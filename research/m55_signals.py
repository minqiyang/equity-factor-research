"""Milestone 5.5: the point-in-time candidate signals S1 to S8 on a normalized input schema.

Card m55-signals (owner decisions O-19, O-21) builds the eight candidates of
the signal-screen design note, section 3; card m55-signals-revision sets the
coordinator definitions of S1, the S2 share basis, the fiscal keys, the IBES
link, the S3 announcement date, and the S3 market return. This module reads no file; a later
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
S1_REVISIONS = 3                     # S1: one-month revisions in the last three statistics months
S1_MIN_VALID = 2
IBES_LINK_STATUS = ("ok", "ambiguous")
COVERAGE_NUMERATOR, COVERAGE_DENOMINATOR = 4, 5   # real start: at least 80 percent of members valid

ANNUAL_ITEMS = ("at", "revt", "cogs", "act", "che", "lct", "dlc", "txp", "dp", "seq", "ceq", "pstk", "pstkrv",
                "pstkl", "txditc", "lt")
SCHEMA = {
    "daily": ("permno", "date", "ret", "prc", "shrout", "cfacpr", "cfacshr"),
    "members": ("permno", "start", "end"),
    "fund_annual": ("gvkey", "datadate", "fyear", "known_date") + ANNUAL_ITEMS,
    "fund_quarterly": ("gvkey", "datadate", "fyearq", "fqtr", "known_date", "epspxq", "ajexq", "rdq"),
    "announcements": ("gvkey", "datadate", "fyearq", "fqtr", "rdq"),
    "link": ("gvkey", "permno", "linkdt", "linkenddt"),
    "ibes_link": ("permno", "ibes_ticker", "linkdt", "linkenddt", "status"),
    "ibes": ("ibes_ticker", "statpers", "fpedats", "fpi", "meanest"),
    "index_daily": ("date", "ret"),
}
KEYS = {"daily": ("permno", "date"), "members": ("permno", "start"),
        "fund_annual": ("gvkey", "datadate", "known_date"), "fund_quarterly": ("gvkey", "datadate", "known_date"),
        "announcements": ("gvkey", "fyearq", "fqtr"), "link": ("gvkey", "permno", "linkdt"),
        "ibes_link": ("permno", "ibes_ticker", "linkdt"), "ibes": ("ibes_ticker", "statpers", "fpi"),
        "index_daily": ("date",)}
NOT_NULL = {**KEYS, "members": ("permno", "start", "end"),
            "fund_annual": ("gvkey", "datadate", "fyear", "known_date"),
            "fund_quarterly": ("gvkey", "datadate", "fyearq", "fqtr", "known_date"),
            "announcements": ("gvkey", "datadate", "fyearq", "fqtr"),
            "ibes_link": ("permno", "ibes_ticker", "linkdt", "status"),
            "ibes": ("ibes_ticker", "statpers", "fpi", "fpedats")}
DATE_COLUMNS = {"daily": ("date",), "members": ("start", "end"), "fund_annual": ("datadate", "known_date"),
                "fund_quarterly": ("datadate", "known_date", "rdq"), "announcements": ("datadate", "rdq"),
                "link": ("linkdt", "linkenddt"), "ibes_link": ("linkdt", "linkenddt"),
                "ibes": ("statpers", "fpedats"), "index_daily": ("date",)}
NUMERIC_COLUMNS = {"daily": ("ret", "prc", "shrout", "cfacpr", "cfacshr"), "members": (),
                   "fund_annual": ("fyear",) + ANNUAL_ITEMS, "fund_quarterly": ("fyearq", "fqtr", "epspxq", "ajexq"),
                   "announcements": ("fyearq", "fqtr"), "link": (), "ibes_link": (), "ibes": ("meanest",),
                   "index_daily": ("ret",)}
# One fiscal key per record and one record per fiscal key (card m55-signals-revision, item 4).
FISCAL_KEYS = {"fund_annual": ("fyear",), "fund_quarterly": ("fyearq", "fqtr"), "announcements": ("fyearq", "fqtr")}
NEVER = np.datetime64("2262-01-01", "ns")   # usable-from date of a value the calendar never reaches
ITEM = {name: k for k, name in enumerate(ANNUAL_ITEMS)}


@dataclass(frozen=True)
class SignalInputs:
    """The normalized point-in-time tables (the loader's contract; ``check_inputs`` enforces it).

    ``daily``: one row per (``permno``, ``date``) on the CRSP trading calendar; ``ret`` is the total return with
    the delisting return included; ``prc`` is a positive close. ``members``: S&P 500 spells, ``end`` inclusive.
    ``fund_annual`` and ``fund_quarterly``: point-in-time rows, one per (``gvkey``, ``datadate``, ``known_date``);
    a later ``known_date`` is a revision; ``fyear`` or (``fyearq``, ``fqtr``) is the fiscal key of the record.
    ``announcements``: one ``rdq`` per fiscal quarter, which may come from the standard quarterly file; the
    announcement is public on ``rdq``. ``link``: primary CRSP-Compustat links, ``linkenddt`` NaT when open.
    ``ibes_link``: IBES ticker to PERMNO links with ``status`` ``ok`` or ``ambiguous``. ``ibes``: unadjusted
    summary rows by IBES ticker. ``index_daily``: the CRSP value-weighted S&P 500 universe total return.
    Missing values are NaN or NaT.
    """

    daily: pd.DataFrame
    members: pd.DataFrame
    fund_annual: pd.DataFrame
    fund_quarterly: pd.DataFrame
    announcements: pd.DataFrame
    link: pd.DataFrame
    ibes_link: pd.DataFrame
    ibes: pd.DataFrame
    index_daily: pd.DataFrame


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
    for table in ("link", "ibes_link"):
        link = getattr(inputs, table)
        if (link["linkenddt"] < link["linkdt"]).any():
            raise refuse("link_invalid", f"{table}: linkenddt before linkdt")
    if not inputs.ibes_link["status"].isin(IBES_LINK_STATUS).all():
        raise refuse("link_invalid", "ibes_link.status is not ok or ambiguous")
    for table, fiscal in FISCAL_KEYS.items():
        frame = getattr(inputs, table)
        keys = frame[list(fiscal)].to_numpy(dtype=float)
        if (keys != np.round(keys)).any() or ("fqtr" in fiscal and not frame["fqtr"].isin([1, 2, 3, 4]).all()):
            raise refuse("fiscal_key_invalid", f"{table}: fiscal keys must be integers, fqtr 1 to 4")
        pairs = frame[["gvkey", "datadate", *fiscal]].drop_duplicates()
        if pairs.duplicated(["gvkey", "datadate"]).any() or pairs.duplicated(["gvkey", *fiscal]).any():
            raise refuse("fiscal_key_invalid", f"{table}: a fiscal key and a datadate must match one to one")
    fy1 = inputs.ibes[inputs.ibes["fpi"].astype(str) == "1"]
    if pd.DataFrame({"ticker": fy1["ibes_ticker"], "month": fy1["statpers"].dt.to_period("M")}).duplicated().any():
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


def _quarter_index(frame: pd.DataFrame) -> np.ndarray:
    """Fiscal quarters as consecutive integers: 4 x fyearq + fqtr - 1."""
    return 4 * frame["fyearq"].to_numpy(dtype=np.int64) + frame["fqtr"].to_numpy(dtype=np.int64) - 1


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
        # The S3 market return on each calendar row; NaN where the index row is absent or missing.
        index = inputs.index_daily
        self.index_ret = np.full(len(cal), np.nan)
        pos = np.searchsorted(cal, _ns(index["date"]))
        on_calendar = (pos < len(cal)) & (cal[np.minimum(pos, len(cal) - 1)] == _ns(index["date"]))
        self.index_ret[pos[on_calendar]] = index["ret"].to_numpy(dtype=float)[on_calendar]

        spells = inputs.members
        self.spell_permno = spells["permno"].to_numpy()
        self.spell_start, self.spell_end = _ns(spells["start"]), _ns(spells["end"])

        link = inputs.link
        self.link_gvkey, self.link_permno = link["gvkey"].to_numpy(), link["permno"].to_numpy()
        self.link_start = _ns(link["linkdt"])
        end = _ns(link["linkenddt"])
        self.link_end = np.where(np.isnat(end), NEVER, end)
        ibes_link = inputs.ibes_link
        self.ibes_permno, self.ibes_ticker = ibes_link["permno"].to_numpy(), ibes_link["ibes_ticker"].to_numpy()
        self.ibes_status = ibes_link["status"].to_numpy()
        self.ibes_start = _ns(ibes_link["linkdt"])
        end = _ns(ibes_link["linkenddt"])
        self.ibes_end = np.where(np.isnat(end), NEVER, end)

        self.annual = self._annual(inputs.fund_annual)
        self.quarterly = self._quarterly(inputs.fund_quarterly)
        self.announcements = self._announcements(inputs.announcements)
        self.ibes = self._ibes(inputs.ibes)

    def _annual(self, frame: pd.DataFrame) -> dict[Any, dict[str, Any]]:
        frame = frame.sort_values(["gvkey", "fyear", "known_date"])
        gvkey, datadate = frame["gvkey"].to_numpy(), _ns(frame["datadate"])
        usable = _rows_after(self.calendar, _ns(frame["known_date"]), 1)
        items = frame[list(ANNUAL_ITEMS)].to_numpy(dtype=float)
        records = {}
        for g, rows in _split(gvkey, {"datadate": datadate, "fyear": frame["fyear"].to_numpy(dtype=np.int64),
                                      "usable": usable, "row": np.arange(len(frame))}).items():
            # One record per fiscal year; its rows (revisions) are rows start:stop, sorted by known date.
            start = np.flatnonzero(np.r_[True, rows["fyear"][1:] != rows["fyear"][:-1]])
            dd = rows["datadate"][start]
            records[g] = {"datadate": dd, "fyear": rows["fyear"][start], "first": rows["usable"][start],
                          "ready": _shift_months(dd, ANNUAL_READY_MONTHS), "old": _shift_months(dd, MAX_AGE_MONTHS["S4"]),
                          "start": start, "stop": np.r_[start[1:], len(rows["datadate"])],
                          "usable": rows["usable"], "items": items[rows["row"]]}
        return records

    def _quarterly(self, frame: pd.DataFrame) -> dict[Any, dict[str, np.ndarray]]:
        # S2 uses first-known values only: the earliest row of each fiscal quarter.
        frame = frame.assign(quarter=_quarter_index(frame))
        frame = frame.sort_values(["gvkey", "quarter", "known_date"]).drop_duplicates(["gvkey", "quarter"])
        rdq = _ns(frame["rdq"])
        return _split(frame["gvkey"].to_numpy(), {
            "quarter": frame["quarter"].to_numpy(), "first": _rows_after(self.calendar, _ns(frame["known_date"]), 1),
            "eps": frame["epspxq"].to_numpy(dtype=float), "ajexq": frame["ajexq"].to_numpy(dtype=float),
            "rdq": rdq, "rdq1": _rows_after(self.calendar, rdq, 1), "old": _shift_months(rdq, MAX_AGE_MONTHS["S2"])})

    def _announcements(self, frame: pd.DataFrame) -> dict[Any, dict[str, np.ndarray]]:
        # S3: an announcement is public on rdq, so rdq is its known date; it is usable from rdq + 2 rows.
        frame = frame.assign(quarter=_quarter_index(frame)).sort_values(["gvkey", "quarter"])
        rdq = _ns(frame["rdq"])
        return _split(frame["gvkey"].to_numpy(), {
            "quarter": frame["quarter"].to_numpy(), "rdq": rdq, "rdq1": _rows_after(self.calendar, rdq, 1),
            "rdq2": _rows_after(self.calendar, rdq, 2), "old": _shift_months(rdq, MAX_AGE_MONTHS["S3"])})

    def _ibes(self, frame: pd.DataFrame) -> dict[Any, dict[str, np.ndarray]]:
        frame = frame[frame["fpi"].astype(str) == "1"].sort_values(["ibes_ticker", "statpers"])
        statpers = _ns(frame["statpers"])
        month = _month(statpers)
        # Usable from the first month-end row after the statistics date.
        pos = np.searchsorted(self.month_ends, statpers, side="right")
        usable = np.where(pos < len(self.month_ends), self.month_ends[np.minimum(pos, len(self.month_ends) - 1)],
                          NEVER)
        # The month-end row of the statistics month (for the S1 price), NaT when the calendar lacks that month.
        k = np.minimum(np.searchsorted(self.month_end_month, month), len(self.month_ends) - 1)
        month_end = np.where(self.month_end_month[k] == month, self.month_ends[k], np.datetime64("NaT", "ns"))
        return _split(frame["ibes_ticker"].to_numpy(), {
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

    def ibes_links_at(self, t: np.datetime64) -> dict[Any, Any]:
        """permno -> IBES ticker for one ``ok`` link valid at t; ``ambiguous_link`` for an ambiguous status,
        overlapping rows, or a ticker on two PERMNOs (R3)."""
        mask = (self.ibes_start <= t) & (t <= self.ibes_end)
        rows, permnos = defaultdict(list), defaultdict(set)
        for p, ticker, status in zip(self.ibes_permno[mask].tolist(), self.ibes_ticker[mask].tolist(),
                                     self.ibes_status[mask].tolist()):
            rows[p].append((ticker, status))
            permnos[ticker].add(p)
        out = {}
        for p, found in rows.items():
            ticker, status = found[0]
            out[p] = ticker if len(found) == 1 and status == "ok" and len(permnos[ticker]) == 1 else "ambiguous_link"
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
        i = int(np.searchsorted(rec["fyear"], rec["fyear"][j] - 1))
        if i < j and rec["fyear"][i] == rec["fyear"][j] - 1 and known[i]:
            lag = self._revision(rec, i, t)
        return self._revision(rec, j, t), lag

    @staticmethod
    def _revision(rec: dict[str, Any], j: int, t: np.datetime64) -> np.ndarray:
        start, stop = rec["start"][j], rec["stop"][j]
        k = int(np.searchsorted(rec["usable"][start:stop], t, side="right")) - 1
        return rec["items"][start + k]

    # Signals --------------------------------------------------------------------------

    def s1(self, p: Any, ticker: Any, t: np.datetime64) -> float | str:
        """3 x the mean of the valid one-month FY1 revisions of the last three statistics months (at least 2)."""
        if ticker in ("no_link", "ambiguous_link"):
            return ticker
        rec = self.ibes.get(ticker)
        if rec is None:
            return "no_record"
        usable = rec["usable"] <= t
        if not usable.any():
            return "not_yet_known"
        late = int(np.flatnonzero(usable)[-1])
        if t > rec["old"][late]:
            return "stale"
        revisions = [self._revision_s1(p, rec, rec["month"][late] - k) for k in range(S1_REVISIONS)]
        valid = [r for r in revisions if not isinstance(r, str)]
        if len(valid) >= S1_MIN_VALID:
            return S1_REVISIONS * float(np.mean(valid))
        if "fpe_changed" in revisions:
            return "fpe_changed"
        return next(r for r in revisions if isinstance(r, str))   # the most recent failed revision

    def _revision_s1(self, p: Any, rec: dict[str, np.ndarray], month: int) -> float | str:
        """(FY1 mean at month m - FY1 mean at m - 1) / price at the m - 1 month end, on one share basis."""
        late = int(np.searchsorted(rec["month"], month))
        early = late - 1
        if late >= len(rec["month"]) or rec["month"][late] != month or early < 0 or rec["month"][early] != month - 1:
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
        return float(f_price * (rec["meanest"][late] / f_late - rec["meanest"][early] / f_early) / price)

    def s2(self, g: Any, t: np.datetime64) -> float | str:
        if g in ("no_link", "ambiguous_link"):
            return g
        rec = self.quarterly.get(g)
        if rec is None:
            return "no_record"
        known = rec["first"] <= t
        if not known.any():
            return "not_yet_known"
        j = int(np.flatnonzero(known)[-1])
        if np.isnat(rec["rdq"][j]):
            return "missing_item"
        if rec["rdq1"][j] > t:
            return "not_yet_known"
        if t > rec["old"][j]:
            return "stale"
        if known[: j + 1].sum() < MIN_QUARTER_RECORDS:
            return "short_history"

        def eps(quarter: int) -> float | str:
            # First-known EPS over its own ajexq: one share basis across splits.
            i = int(np.searchsorted(rec["quarter"], quarter))
            if i >= len(rec["quarter"]) or rec["quarter"][i] != quarter or not known[i]:
                return "short_history"
            value, factor = rec["eps"][i], rec["ajexq"][i]
            if np.isnan(value) or np.isnan(factor):
                return "missing_item"
            return value / factor if factor > 0.0 else "invalid_value"

        quarter = rec["quarter"][j]
        now, before = eps(quarter), eps(quarter - 4)
        for value in (now, before):
            if isinstance(value, str):
                return value
        diffs = []
        for q in range(1, SUE_QUARTERS + 1):
            a, b = eps(quarter - q), eps(quarter - q - 4)
            if not isinstance(a, str) and not isinstance(b, str):
                diffs.append(a - b)
        if len(diffs) < SUE_MIN_VALID:
            return "short_history"
        sd = float(np.std(diffs, ddof=1))
        if sd == 0.0:
            return "zero_denominator"
        return (now - before) / sd

    def s3(self, p: Any, g: Any, t: np.datetime64) -> float | str:
        """Stock minus index compound return over rows -1 to +1 around the latest announcement usable at t."""
        if g in ("no_link", "ambiguous_link"):
            return g
        rec = self.announcements.get(g)
        if rec is None:
            return "no_record"
        if np.isnat(rec["rdq"]).all():
            return "missing_item"
        usable = rec["rdq2"] <= t          # NaT compares False: an announcement without a date is never usable
        if not usable.any():
            return "not_yet_known"
        j = int(np.flatnonzero(usable)[-1])
        if t > rec["old"][j]:
            return "stale"
        if (rec["rdq1"][: j + 1] <= t).sum() < MIN_QUARTER_RECORDS:
            return "short_history"
        day0 = int(np.searchsorted(self.calendar, rec["rdq"][j]))   # the first calendar row on or after rdq
        if day0 < 1:
            return "no_market_data"
        days = self.calendar[day0 - 1: day0 + 2]
        rows = self.market.get(p)
        if rows is None:
            return "no_market_data"
        k = np.searchsorted(rows["date"], days)
        if (k >= len(rows["date"])).any() or (rows["date"][np.minimum(k, len(rows["date"]) - 1)] != days).any():
            return "no_market_data"
        stock, index = rows["ret"][k], self.index_ret[day0 - 1: day0 + 2]
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
        links, ibes_links = data.links_at(t), data.ibes_links_at(t)
        anchors = data.anchors(t)
        for p in current:
            c = column[p]
            members[i, c] = True
            g = links.get(p, "no_link")
            annual = g if g in ("no_link", "ambiguous_link") else data.annual_view(g, t)
            cells = {"S1": data.s1(p, ibes_links.get(p, "no_link"), t), "S2": data.s2(g, t), "S3": data.s3(p, g, t),
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
            "timing_contract": TIMING_CONTRACT}


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


def reason_share(result: dict[str, Any], signal: str, reason: str) -> pd.Series:
    """Share of member cells per calendar year that carry ``reason`` for ``signal`` (for example S5 missing_item)."""
    counts = reason_counts(result)
    counts = counts[counts["signal"] == signal]
    total = counts.groupby("year")["count"].sum()
    hit = counts[counts["reason"] == reason].groupby("year")["count"].sum()
    return (hit.reindex(total.index, fill_value=0) / total).rename(f"{signal} {reason} share")


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
