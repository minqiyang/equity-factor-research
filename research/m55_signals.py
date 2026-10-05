"""Milestone 5.5: the point-in-time candidate signals S1 to S8 on a normalized input schema.

Card m55-signals (owner decisions O-19, O-21) builds the eight candidates of
the signal-screen design note, section 3. This module reads no file; a later
loader card maps the WRDS files into ``SCHEMA``. The tests drive it with
synthetic fixtures only.

Timing ``after_close_signal_next_observed_close_v1``: at rebalance row ``r``
every value uses information usable at the close of the decision row
``t = r - 1``. A value known on day ``k`` is usable from the first calendar row
after ``k``. Members are the S&P 500 spells that cover ``t``.

Each member cell holds a finite value or exactly one typed reason from
``REASONS`` (R6). Nothing is filled, clipped, winsorized, or dropped. The
engine ranks the values with the sign in ``SIGNS``; this module does not rank.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from research.m55_index_tilt import TIMING_CONTRACT, refuse


SIGNAL_IDS = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")
SIGNS = {"S1": 1, "S2": 1, "S3": 1, "S4": 1, "S5": -1, "S6": -1, "S7": -1, "S8": 1}  # +1: higher is better
REASONS = ("no_link", "ambiguous_link", "no_record", "not_yet_known", "stale", "short_history", "missing_item",
           "no_market_data", "fpe_changed", "be_nonpositive", "zero_denominator", "invalid_value")
# A value is stale when t is later than its event date plus this many months (design note, section 3).
# Events: S1 the statistics date, S2 and S3 the report date, S4 to S6 and S8 the fiscal period end,
# S7 the share row against its month-end anchor.
MAX_AGE_MONTHS = {"S1": 2, "S2": 6, "S3": 6, "S4": 18, "S5": 18, "S6": 18, "S7": 1, "S8": 18}
MARKET_AGE_MONTHS = 1                # a daily row read "at" a date is at most this old (the S7 rule)
ANNUAL_READY_MONTHS = 6              # fiscal period end + 6 months before an annual value is used
MIN_ANNUAL_RECORDS = 2               # backfill: two fiscal years known at t, the current one included
MIN_QUARTER_RECORDS = 8              # backfill for S2 and S3: two fiscal years of quarters known at t
SUE_QUARTERS = 8                     # S2: differences of the eight quarters before the current one
SUE_MIN_VALID = 6
REVISION_MONTHS = 3                  # S1: the earlier estimate is three statistics months before the latest
COVERAGE_NUMERATOR, COVERAGE_DENOMINATOR = 4, 5   # real start: at least 80 percent of members valid

ANNUAL_ITEMS = ("at", "revt", "cogs", "act", "che", "lct", "dlc", "txp", "dp", "seq", "ceq", "pstk", "pstkrv",
                "pstkl", "txditc", "lt")
SCHEMA = {
    "daily": ("permno", "date", "ret", "prc", "shrout", "cfacpr", "cfacshr"),
    "members": ("permno", "start", "end"),
    "fund_annual": ("gvkey", "datadate", "known_date") + ANNUAL_ITEMS,
    "fund_quarterly": ("gvkey", "datadate", "known_date", "epspxq", "rdq"),
    "link": ("gvkey", "permno", "linkdt", "linkenddt"),
    "ibes": ("permno", "statpers", "fpedats", "fpi", "meanest"),
}
KEYS = {"daily": ("permno", "date"), "members": ("permno", "start"),
        "fund_annual": ("gvkey", "datadate", "known_date"), "fund_quarterly": ("gvkey", "datadate", "known_date"),
        "link": ("gvkey", "permno", "linkdt"), "ibes": ("permno", "statpers", "fpi")}
NOT_NULL = {**KEYS, "members": ("permno", "start", "end"), "ibes": ("permno", "statpers", "fpi", "fpedats")}
DATE_COLUMNS = {"daily": ("date",), "members": ("start", "end"), "fund_annual": ("datadate", "known_date"),
                "fund_quarterly": ("datadate", "known_date", "rdq"), "link": ("linkdt", "linkenddt"),
                "ibes": ("statpers", "fpedats")}
NUMERIC_COLUMNS = {"daily": ("ret", "prc", "shrout", "cfacpr", "cfacshr"), "members": (), "fund_annual": ANNUAL_ITEMS,
                   "fund_quarterly": ("epspxq",), "link": (), "ibes": ("meanest",)}
NEVER = np.datetime64("2262-01-01", "ns")   # usable-from date of a value the calendar never reaches
ITEM = {name: k for k, name in enumerate(ANNUAL_ITEMS)}


@dataclass(frozen=True)
class SignalInputs:
    """The normalized point-in-time tables (the loader's contract; ``check_inputs`` enforces it).

    ``daily``: one row per (``permno``, ``date``) on the CRSP trading calendar; ``ret`` is the total return with
    the delisting return included; ``prc`` is a positive close. ``members``: S&P 500 spells, ``end`` inclusive.
    ``fund_annual`` and ``fund_quarterly``: one row per (``gvkey``, ``datadate``, ``known_date``); a later
    ``known_date`` is a revision. ``link``: primary CRSP-Compustat links, ``linkenddt`` NaT when open. ``ibes``:
    unadjusted summary rows already linked to ``permno``. Missing values are NaN or NaT.
    """

    daily: pd.DataFrame
    members: pd.DataFrame
    fund_annual: pd.DataFrame
    fund_quarterly: pd.DataFrame
    link: pd.DataFrame
    ibes: pd.DataFrame


def _ns(values: Any) -> np.ndarray:
    return np.asarray(values).astype("datetime64[ns]")


def check_inputs(inputs: SignalInputs) -> None:
    for table, columns in SCHEMA.items():
        frame = getattr(inputs, table)
        for column in columns:
            if column not in frame.columns:
                raise refuse("schema_column_missing", f"{table}.{column}")
        for column in DATE_COLUMNS[table]:
            if not pd.api.types.is_datetime64_dtype(frame[column]):
                raise refuse("schema_date_invalid", f"{table}.{column}")
        for column in NOT_NULL[table]:
            if frame[column].isna().any():
                raise refuse("schema_key_missing", f"{table}.{column}")
        for column in NUMERIC_COLUMNS[table]:
            series = frame[column]
            if not pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
                raise refuse("schema_value_invalid", f"{table}.{column}")
            if np.isinf(series.to_numpy(dtype=float)).any():
                raise refuse("schema_value_invalid", f"{table}.{column} is infinite")
        if frame.duplicated(list(KEYS[table])).any():
            raise refuse("duplicate_key", table)
    prc = inputs.daily["prc"].to_numpy(dtype=float)
    if (prc[~np.isnan(prc)] <= 0.0).any():
        raise refuse("schema_value_invalid", "daily.prc is not positive")
    for table in ("fund_annual", "fund_quarterly"):
        frame = getattr(inputs, table)
        if (frame["known_date"] < frame["datadate"]).any():
            raise refuse("known_before_datadate", table)
    members = inputs.members.sort_values(["permno", "start"])
    if (members["start"] > members["end"]).any():
        raise refuse("spell_invalid", "start after end")
    same = members["permno"].to_numpy()[1:] == members["permno"].to_numpy()[:-1]
    if (same & (members["start"].to_numpy()[1:] <= members["end"].to_numpy()[:-1])).any():
        raise refuse("spell_invalid", "overlapping spells")
    link = inputs.link
    if (link["linkenddt"] < link["linkdt"]).any():
        raise refuse("link_invalid", "linkenddt before linkdt")
    fy1 = inputs.ibes[inputs.ibes["fpi"].astype(str) == "1"]
    if pd.DataFrame({"permno": fy1["permno"], "month": fy1["statpers"].dt.to_period("M")}).duplicated().any():
        raise refuse("duplicate_key", "ibes: two FY1 statistics dates in one month")


# Date helpers ---------------------------------------------------------------------------

def _month(dates: np.ndarray) -> np.ndarray:
    return dates.astype("datetime64[M]").astype(np.int64)


def _rows_after(calendar: np.ndarray, dates: np.ndarray, k: int) -> np.ndarray:
    """The k-th calendar row strictly after each date; NEVER past the calendar end; NaT stays NaT."""
    out = np.full(len(dates), NEVER)
    missing = np.isnat(dates)
    pos = np.searchsorted(calendar, dates, side="right") + (k - 1)
    ok = ~missing & (pos < len(calendar))
    out[ok] = calendar[pos[ok]]
    out[missing] = np.datetime64("NaT", "ns")
    return out


def _shift_months(dates: np.ndarray, k: int) -> np.ndarray:
    return (pd.DatetimeIndex(dates) + pd.DateOffset(months=k)).to_numpy().astype("datetime64[ns]")


def _split(key: np.ndarray, arrays: dict[str, np.ndarray]) -> dict[Any, dict[str, np.ndarray]]:
    """Group sorted arrays by a sorted key: key -> {name: slice}."""
    if not len(key):
        return {}
    cut = np.flatnonzero(key[1:] != key[:-1]) + 1
    starts, stops = np.r_[0, cut], np.r_[cut, len(key)]
    return {key[s]: {name: a[s:e] for name, a in arrays.items()} for s, e in zip(starts, stops)}


# The member-universe return for S3 --------------------------------------------------------

def universe_returns(inputs: SignalInputs, calendar: np.ndarray) -> np.ndarray:
    """Cap-weighted daily return of the member universe on each calendar row; NaN where it is blank.

    The weight of a member on row d is ``prc x shrout`` on its row d - 1. R6: a member without a finite return
    on row d, or without a weight from row d - 1, blanks row d; no member is dropped from the mean.
    """
    frame = inputs.daily.sort_values(["permno", "date"])
    permno = frame["permno"].to_numpy()
    dates = _ns(frame["date"])
    pos = np.searchsorted(calendar, dates)
    ret = frame["ret"].to_numpy(dtype=float)
    cap = (frame["prc"] * frame["shrout"]).to_numpy(dtype=float)
    follows = np.r_[False, (permno[1:] == permno[:-1]) & (pos[1:] == pos[:-1] + 1)]
    weight = np.where(follows, np.r_[np.nan, cap[:-1]], np.nan)
    member = np.zeros(len(frame), dtype=bool)
    rows = _split(permno, {"index": np.arange(len(frame))})
    count = np.zeros(len(calendar) + 1, dtype=np.int64)
    for p, start, end in inputs.members[["permno", "start", "end"]].itertuples(index=False):
        start, end = np.datetime64(start, "ns"), np.datetime64(end, "ns")
        np.add.at(count, [np.searchsorted(calendar, start), np.searchsorted(calendar, end, side="right")], [1, -1])
        if p in rows:
            index = rows[p]["index"]
            lo = np.searchsorted(dates[index], start)
            hi = np.searchsorted(dates[index], end, side="right")
            member[index[lo:hi]] = True
    count = np.cumsum(count)[:-1]
    ok = member & np.isfinite(ret) & np.isfinite(weight)
    valid = np.bincount(pos[ok], minlength=len(calendar))
    num = np.bincount(pos[ok], weights=weight[ok] * ret[ok], minlength=len(calendar))
    den = np.bincount(pos[ok], weights=weight[ok], minlength=len(calendar))
    blank = (count == 0) | (valid != count) | (den <= 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(blank, np.nan, num / den)


# Prepared data --------------------------------------------------------------------------

class _Signals:
    """The inputs, sorted and grouped once, and one function per signal."""

    def __init__(self, inputs: SignalInputs) -> None:
        self.calendar = cal = np.unique(_ns(inputs.daily["date"]))
        cal_month = _month(cal)
        last = np.r_[cal_month[1:] != cal_month[:-1], True]
        self.month_ends, self.month_end_month = cal[last], cal_month[last]

        daily = inputs.daily.sort_values(["permno", "date"])
        self.market = _split(daily["permno"].to_numpy(), {
            "date": _ns(daily["date"]), **{c: daily[c].to_numpy(dtype=float) for c in ("ret", "prc", "shrout",
                                                                                       "cfacshr")}})
        self.universe = universe_returns(inputs, cal)
        self.universe_blank_rows = int(np.isnan(self.universe).sum())

        spells = inputs.members
        self.spell_permno = spells["permno"].to_numpy()
        self.spell_start, self.spell_end = _ns(spells["start"]), _ns(spells["end"])

        link = inputs.link
        self.link_gvkey, self.link_permno = link["gvkey"].to_numpy(), link["permno"].to_numpy()
        self.link_start = _ns(link["linkdt"])
        end = _ns(link["linkenddt"])
        self.link_end = np.where(np.isnat(end), NEVER, end)

        self.annual = self._annual(inputs.fund_annual)
        self.quarterly = self._quarterly(inputs.fund_quarterly)
        self.ibes = self._ibes(inputs.ibes)

    def _annual(self, frame: pd.DataFrame) -> dict[Any, dict[str, Any]]:
        frame = frame.sort_values(["gvkey", "datadate", "known_date"])
        gvkey, datadate = frame["gvkey"].to_numpy(), _ns(frame["datadate"])
        usable = _rows_after(self.calendar, _ns(frame["known_date"]), 1)
        items = frame[list(ANNUAL_ITEMS)].to_numpy(dtype=float)
        records = {}
        for g, rows in _split(gvkey, {"datadate": datadate, "usable": usable, "row": np.arange(len(frame))}).items():
            # One record per fiscal period; its rows (revisions) are rows start:stop, sorted by known date.
            start = np.flatnonzero(np.r_[True, rows["datadate"][1:] != rows["datadate"][:-1]])
            dd = rows["datadate"][start]
            records[g] = {"datadate": dd, "month": _month(dd), "first": rows["usable"][start],
                          "ready": _shift_months(dd, ANNUAL_READY_MONTHS), "old": _shift_months(dd, MAX_AGE_MONTHS["S4"]),
                          "start": start, "stop": np.r_[start[1:], len(rows["datadate"])],
                          "usable": rows["usable"], "items": items[rows["row"]]}
        return records

    def _quarterly(self, frame: pd.DataFrame) -> dict[Any, dict[str, np.ndarray]]:
        # S2 and S3 use first-known values only: the earliest row of each fiscal quarter.
        frame = frame.sort_values(["gvkey", "datadate", "known_date"]).drop_duplicates(["gvkey", "datadate"])
        known, rdq = _ns(frame["known_date"]), _ns(frame["rdq"])
        return _split(frame["gvkey"].to_numpy(), {
            "month": _month(_ns(frame["datadate"])), "first": _rows_after(self.calendar, known, 1),
            "known": known, "floor": _shift_months(known, -MARKET_AGE_MONTHS),
            "eps": frame["epspxq"].to_numpy(dtype=float), "rdq": rdq, "rdq1": _rows_after(self.calendar, rdq, 1),
            "rdq2": _rows_after(self.calendar, rdq, 2), "old": _shift_months(rdq, MAX_AGE_MONTHS["S2"])})

    def _ibes(self, frame: pd.DataFrame) -> dict[Any, dict[str, np.ndarray]]:
        frame = frame[frame["fpi"].astype(str) == "1"].sort_values(["permno", "statpers"])
        statpers = _ns(frame["statpers"])
        month = _month(statpers)
        # Usable from the first month-end row after the statistics date.
        pos = np.searchsorted(self.month_ends, statpers, side="right")
        usable = np.where(pos < len(self.month_ends), self.month_ends[np.minimum(pos, len(self.month_ends) - 1)],
                          NEVER)
        # The month-end row of the statistics month (for the S1 price), NaT when the calendar lacks that month.
        k = np.minimum(np.searchsorted(self.month_end_month, month), len(self.month_ends) - 1)
        month_end = np.where(self.month_end_month[k] == month, self.month_ends[k], np.datetime64("NaT", "ns"))
        return _split(frame["permno"].to_numpy(), {
            "statpers": statpers, "month": month, "usable": usable, "old": _shift_months(statpers, MAX_AGE_MONTHS["S1"]),
            "floor": _shift_months(statpers, -MARKET_AGE_MONTHS), "fpedats": _ns(frame["fpedats"]),
            "meanest": frame["meanest"].to_numpy(dtype=float), "month_end": month_end,
            "month_end_floor": _shift_months(month_end, -MARKET_AGE_MONTHS)})

    # Rebalance state ------------------------------------------------------------------

    def members_at(self, t: np.datetime64) -> list[Any]:
        mask = (self.spell_start <= t) & (t <= self.spell_end)
        return sorted(set(self.spell_permno[mask].tolist()))

    def links_at(self, t: np.datetime64) -> dict[Any, Any]:
        """permno -> gvkey for one-to-one links valid at t; ``ambiguous_link`` otherwise (R3)."""
        mask = (self.link_start <= t) & (t <= self.link_end)
        gvkeys, permnos = defaultdict(set), defaultdict(set)
        for g, p in zip(self.link_gvkey[mask].tolist(), self.link_permno[mask].tolist()):
            gvkeys[p].add(g)
            permnos[g].add(p)
        out = {}
        for p, gs in gvkeys.items():
            g = next(iter(gs))
            out[p] = g if len(gs) == 1 and len(permnos[g]) == 1 else "ambiguous_link"
        return out

    def anchors(self, t: np.datetime64) -> dict[str, np.datetime64 | None]:
        """S7 and S8 read shares at the month-end row before t's month, and S7 also 12 months earlier."""
        t_month = _month(np.array([t]))[0]
        k = int(np.searchsorted(self.month_end_month, t_month)) - 1
        if k < 0:
            return {"a": None, "a_floor": None, "a12": None, "a12_floor": None}
        a, month = self.month_ends[k], self.month_end_month[k] - 12
        j = int(np.searchsorted(self.month_end_month, month))
        a12 = self.month_ends[j] if self.month_end_month[j] == month else None   # j <= k, so it is in range
        floor = _shift_months(np.array([a, a12 if a12 is not None else np.datetime64("NaT", "ns")]), -MARKET_AGE_MONTHS)
        return {"a": a, "a_floor": floor[0], "a12": a12, "a12_floor": floor[1]}

    # Lookups --------------------------------------------------------------------------

    def market_row(self, p: Any, date: np.datetime64, floor: np.datetime64) -> tuple[dict, int] | str:
        """The latest daily row of ``p`` at or before ``date``, at most one month old."""
        rows = self.market.get(p)
        if rows is None:
            return "no_market_data"
        k = int(np.searchsorted(rows["date"], date, side="right")) - 1
        if k < 0:
            return "no_market_data"
        if rows["date"][k] < floor:
            return "stale"
        return rows, k

    def share_factor(self, p: Any, date: np.datetime64, floor: np.datetime64) -> float | str:
        found = self.market_row(p, date, floor)
        if isinstance(found, str):
            return found
        rows, k = found
        f = rows["cfacshr"][k]
        if np.isnan(f):
            return "missing_item"
        return float(f) if f > 0.0 else "invalid_value"

    def annual_view(self, g: Any, t: np.datetime64) -> tuple[np.ndarray, np.ndarray | None] | str:
        """The current fiscal year and the prior one, each as the latest revision usable at t."""
        rec = self.annual.get(g)
        if rec is None:
            return "no_record"
        known = rec["first"] <= t
        ready = known & (rec["ready"] <= t)
        if not ready.any():
            return "not_yet_known"
        j = int(np.flatnonzero(ready)[-1])
        if t > rec["old"][j]:
            return "stale"
        if known[: j + 1].sum() < MIN_ANNUAL_RECORDS:
            return "short_history"
        lag = None
        i = int(np.searchsorted(rec["month"], rec["month"][j] - 12))
        if i < j and rec["month"][i] == rec["month"][j] - 12 and known[i]:
            lag = self._revision(rec, i, t)
        return self._revision(rec, j, t), lag

    @staticmethod
    def _revision(rec: dict[str, Any], j: int, t: np.datetime64) -> np.ndarray:
        start, stop = rec["start"][j], rec["stop"][j]
        k = int(np.searchsorted(rec["usable"][start:stop], t, side="right")) - 1
        return rec["items"][start + k]

    def quarter_view(self, g: Any, t: np.datetime64) -> tuple[dict, np.ndarray, int] | str:
        rec = self.quarterly.get(g)
        if rec is None:
            return "no_record"
        known = rec["first"] <= t
        if not known.any():
            return "not_yet_known"
        return rec, known, int(np.flatnonzero(known)[-1])

    # Signals --------------------------------------------------------------------------

    def s1(self, p: Any, t: np.datetime64) -> float | str:
        rec = self.ibes.get(p)
        if rec is None:
            return "no_record"
        usable = rec["usable"] <= t
        if not usable.any():
            return "not_yet_known"
        late = int(np.flatnonzero(usable)[-1])
        if t > rec["old"][late]:
            return "stale"
        early = int(np.searchsorted(rec["month"], rec["month"][late] - REVISION_MONTHS))
        if early >= late or rec["month"][early] != rec["month"][late] - REVISION_MONTHS:
            return "short_history"
        if rec["fpedats"][early] != rec["fpedats"][late]:
            return "fpe_changed"
        if np.isnan(rec["meanest"][late]) or np.isnan(rec["meanest"][early]):
            return "missing_item"
        f_late = self.share_factor(p, rec["statpers"][late], rec["floor"][late])
        if isinstance(f_late, str):
            return f_late
        f_early = self.share_factor(p, rec["statpers"][early], rec["floor"][early])
        if isinstance(f_early, str):
            return f_early
        if np.isnat(rec["month_end"][early]):
            return "no_market_data"
        found = self.market_row(p, rec["month_end"][early], rec["month_end_floor"][early])
        if isinstance(found, str):
            return found
        rows, k = found
        price, f_price = rows["prc"][k], rows["cfacshr"][k]
        if np.isnan(price) or np.isnan(f_price):
            return "missing_item"
        if f_price <= 0.0:
            return "invalid_value"
        # Put both estimates on the share basis of the price row: EPS on date d over cfacshr(d) is basis-free.
        return f_price * (rec["meanest"][late] / f_late - rec["meanest"][early] / f_early) / price

    def s2(self, p: Any, t: np.datetime64, view: tuple | str) -> float | str:
        if isinstance(view, str):
            return view
        rec, known, j = view
        if np.isnat(rec["rdq"][j]):
            return "missing_item"
        if rec["rdq1"][j] > t:
            return "not_yet_known"
        if t > rec["old"][j]:
            return "stale"
        if known[: j + 1].sum() < MIN_QUARTER_RECORDS:
            return "short_history"

        def eps(month: int) -> float | str:
            # First-known EPS over cfacshr at its known date: one share basis across splits.
            i = int(np.searchsorted(rec["month"], month))
            if i >= len(rec["month"]) or rec["month"][i] != month or not known[i]:
                return "short_history"
            if np.isnan(rec["eps"][i]):
                return "missing_item"
            f = self.share_factor(p, rec["known"][i], rec["floor"][i])
            return f if isinstance(f, str) else rec["eps"][i] / f

        month = rec["month"][j]
        now, before = eps(month), eps(month - 12)
        for value in (now, before):
            if isinstance(value, str):
                return value
        diffs = []
        for q in range(1, SUE_QUARTERS + 1):
            a, b = eps(month - 3 * q), eps(month - 3 * q - 12)
            if not isinstance(a, str) and not isinstance(b, str):
                diffs.append(a - b)
        if len(diffs) < SUE_MIN_VALID:
            return "short_history"
        sd = float(np.std(diffs, ddof=1))
        if sd == 0.0:
            return "zero_denominator"
        return (now - before) / sd

    def s3(self, p: Any, t: np.datetime64, view: tuple | str) -> float | str:
        if isinstance(view, str):
            return view
        rec, known, j = view
        rdq = rec["rdq"][j]
        if np.isnat(rdq):
            return "missing_item"
        if rec["rdq2"][j] > t:
            return "not_yet_known"
        if t > rec["old"][j]:
            return "stale"
        if known[: j + 1].sum() < MIN_QUARTER_RECORDS:
            return "short_history"
        day0 = int(np.searchsorted(self.calendar, rdq))   # the first calendar row at or after the report date
        if day0 < 1:
            return "no_market_data"
        days = self.calendar[day0 - 1: day0 + 2]
        rows = self.market.get(p)
        if rows is None:
            return "no_market_data"
        k = np.searchsorted(rows["date"], days)
        if (k >= len(rows["date"])).any() or (rows["date"][np.minimum(k, len(rows["date"]) - 1)] != days).any():
            return "no_market_data"
        stock, index = rows["ret"][k], self.universe[day0 - 1: day0 + 2]
        if np.isnan(stock).any() or np.isnan(index).any():
            return "no_market_data"
        return float(np.prod(1.0 + stock) - np.prod(1.0 + index))

    @staticmethod
    def s4(view: tuple | str) -> float | str:
        if isinstance(view, str):
            return view
        cur = view[0]
        revt, cogs, at = cur[ITEM["revt"]], cur[ITEM["cogs"]], cur[ITEM["at"]]
        if np.isnan([revt, cogs, at]).any():
            return "missing_item"
        if at < 0.0:
            return "invalid_value"
        return "zero_denominator" if at == 0.0 else (revt - cogs) / at

    @staticmethod
    def s5(view: tuple | str) -> float | str:
        if isinstance(view, str):
            return view
        cur, lag = view
        if lag is None:
            return "short_history"
        names = ("act", "che", "lct", "dlc", "txp", "at")
        now = {n: cur[ITEM[n]] for n in names + ("dp",)}
        old = {n: lag[ITEM[n]] for n in names}
        if np.isnan(list(now.values()) + list(old.values())).any():
            return "missing_item"
        if now["at"] < 0.0 or old["at"] < 0.0:
            return "invalid_value"
        mean_at = (now["at"] + old["at"]) / 2.0
        if mean_at == 0.0:
            return "zero_denominator"
        d = {n: now[n] - old[n] for n in names}
        accruals = (d["act"] - d["che"]) - (d["lct"] - d["dlc"] - d["txp"]) - now["dp"]
        return accruals / mean_at

    @staticmethod
    def s6(view: tuple | str) -> float | str:
        if isinstance(view, str):
            return view
        cur, lag = view
        if lag is None:
            return "short_history"
        at, at_lag = cur[ITEM["at"]], lag[ITEM["at"]]
        if np.isnan([at, at_lag]).any():
            return "missing_item"
        if at < 0.0 or at_lag < 0.0:
            return "invalid_value"
        return "zero_denominator" if at_lag == 0.0 else at / at_lag - 1.0

    def s7(self, p: Any, anchors: dict[str, Any]) -> float | str:
        if anchors["a"] is None:
            return "no_market_data"
        now = self._shares(p, anchors["a"], anchors["a_floor"])
        if isinstance(now, str):
            return now
        if anchors["a12"] is None:
            return "short_history"
        before = self._shares(p, anchors["a12"], anchors["a12_floor"])
        if isinstance(before, str):
            return "short_history" if before == "no_market_data" else before
        return float(np.log(now) - np.log(before))

    def _shares(self, p: Any, date: np.datetime64, floor: np.datetime64) -> float | str:
        found = self.market_row(p, date, floor)
        if isinstance(found, str):
            return found
        rows, k = found
        shares = rows["shrout"][k] * rows["cfacshr"][k]
        if np.isnan(shares):
            return "missing_item"
        return float(shares) if shares > 0.0 else "invalid_value"

    def s8(self, p: Any, view: tuple | str, anchors: dict[str, Any]) -> float | str:
        if isinstance(view, str):
            return view
        be = book_equity(view[0])
        if isinstance(be, str):
            return be
        if be <= 0.0:
            return "be_nonpositive"
        if anchors["a"] is None:
            return "no_market_data"
        found = self.market_row(p, anchors["a"], anchors["a_floor"])
        if isinstance(found, str):
            return found
        rows, k = found
        price, shares = rows["prc"][k], rows["shrout"][k]
        if np.isnan(price) or np.isnan(shares):
            return "missing_item"
        if shares < 0.0:
            return "invalid_value"
        return "zero_denominator" if shares == 0.0 else be / (price * shares)


def book_equity(row: np.ndarray) -> float | str:
    """Fama-French book equity: stockholders' equity - preferred + deferred taxes (``txditc`` 0 when missing)."""
    seq, ceq, pstk, at, lt = (row[ITEM[n]] for n in ("seq", "ceq", "pstk", "at", "lt"))
    if not np.isnan(seq):
        equity = seq
    elif not np.isnan(ceq) and not np.isnan(pstk):
        equity = ceq + pstk
    elif not np.isnan(at) and not np.isnan(lt):
        equity = at - lt
    else:
        return "missing_item"
    preferred = next((row[ITEM[n]] for n in ("pstkrv", "pstkl", "pstk") if not np.isnan(row[ITEM[n]])), None)
    if preferred is None:
        return "missing_item"
    txditc = row[ITEM["txditc"]]
    return float(equity - preferred + (0.0 if np.isnan(txditc) else txditc))


# Panels ---------------------------------------------------------------------------------

def build_signals(inputs: SignalInputs, rebalances: pd.DatetimeIndex) -> dict[str, Any]:
    """Value and reason panels (rebalance rows x PERMNO) for S1 to S8 at each rebalance row ``r``.

    Columns are every PERMNO that is a member at some rebalance; a non-member cell is NaN with no reason.
    """
    check_inputs(inputs)
    data = _Signals(inputs)
    cal = data.calendar
    rows = _ns(rebalances)
    pos = np.searchsorted(cal, rows)
    if (pos >= len(cal)).any() or (cal[np.minimum(pos, len(cal) - 1)] != rows).any() or (pos < 1).any():
        raise refuse("rebalance_invalid", "every rebalance must be a calendar row after the first")
    if len(rows) and (np.diff(rows) <= np.timedelta64(0, "ns")).any():
        raise refuse("rebalance_invalid", "rebalances must increase")
    decision = cal[pos - 1]
    member_sets = [data.members_at(t) for t in decision]
    permnos = sorted(set().union(*member_sets)) if member_sets else []
    column = {p: k for k, p in enumerate(permnos)}
    values = {s: np.full((len(rows), len(permnos)), np.nan) for s in SIGNAL_IDS}
    reasons = {s: np.full((len(rows), len(permnos)), None, dtype=object) for s in SIGNAL_IDS}
    members = np.zeros((len(rows), len(permnos)), dtype=bool)
    for i, (t, current) in enumerate(zip(decision, member_sets)):
        links = data.links_at(t)
        anchors = data.anchors(t)
        for p in current:
            c = column[p]
            members[i, c] = True
            g = links.get(p, "no_link")
            linked = g not in ("no_link", "ambiguous_link")
            annual = data.annual_view(g, t) if linked else g
            quarter = data.quarter_view(g, t) if linked else g
            cells = {"S1": data.s1(p, t), "S2": data.s2(p, t, quarter), "S3": data.s3(p, t, quarter),
                     "S4": data.s4(annual), "S5": data.s5(annual), "S6": data.s6(annual), "S7": data.s7(p, anchors),
                     "S8": data.s8(p, annual, anchors)}
            for s, cell in cells.items():
                if isinstance(cell, str):
                    reasons[s][i, c] = cell
                elif np.isfinite(cell):
                    values[s][i, c] = float(cell)
                else:
                    reasons[s][i, c] = "invalid_value"
    index = pd.DatetimeIndex(rebalances, name="date")
    columns = pd.Index(permnos, name="permno")
    return {"values": {s: pd.DataFrame(values[s], index=index, columns=columns) for s in SIGNAL_IDS},
            "reasons": {s: pd.DataFrame(reasons[s], index=index, columns=columns, dtype=object) for s in SIGNAL_IDS},
            "members": pd.DataFrame(members, index=index, columns=columns), "signs": dict(SIGNS),
            "timing_contract": TIMING_CONTRACT, "universe_blank_rows": data.universe_blank_rows}


def reason_counts(result: dict[str, Any]) -> pd.DataFrame:
    """Member cells by signal, calendar year, and reason (``valid`` for a value); from reason panels only."""
    members = result["members"].to_numpy()
    years = result["members"].index.year
    counts: dict[tuple[str, int, str], int] = defaultdict(int)
    for s in SIGNAL_IDS:
        reasons = result["reasons"][s].to_numpy()
        for year, member, row in zip(years, members, reasons):
            for reason in row[member]:
                counts[(s, int(year), reason or "valid")] += 1
    rows = [(s, y, r, n) for (s, y, r), n in sorted(counts.items())]
    return pd.DataFrame(rows, columns=["signal", "year", "reason", "count"])


def real_start(reasons: pd.DataFrame, members: pd.DataFrame) -> int | None:
    """First year from which every rebalance month has at least 80 percent of members valid, to the panel end.

    The years are the calendar years of the panel rows. A month with no member fails. Reason panels only.
    """
    valid = (members & reasons.isna()).sum(axis=1)
    total = members.sum(axis=1)
    month_ok = (total > 0) & (COVERAGE_DENOMINATOR * valid >= COVERAGE_NUMERATOR * total)
    year_ok = month_ok.groupby(month_ok.index.year).all()
    start = None
    for year, ok in sorted(year_ok.items(), reverse=True):
        if not ok:
            break
        start = int(year)
    return start
