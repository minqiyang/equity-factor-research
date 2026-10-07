"""Milestone 5.5: build the engine and signal inputs from the WRDS files (card m55-loader).

The loader reads only the main files of the WRDS folder that
``coord/reports/m6_prep/wrds_pull.py`` writes (vintage 2025-12-31). It checks
each file's SHA-256 against ``MANIFEST_local.json`` and refuses a mismatch, a
missing file, or any path under ``sealed/``. It never opens a sealed file; only
``write_manifest`` hashes the bytes of the sealed files (O-12, O-18, O-22).

Outputs: the engine frames of ``research/m55_index_tilt.py`` (``tilt_frames``;
the driver adds the signals), the ``SignalInputs`` of ``research/m55_signals.py``
(``signal_inputs``), the three benchmark total returns (``benchmarks``), the
intake aggregates (``intake_report``), and the tracked manifest
(``write_manifest``). Coordinator defaults D1 to D9 of the card apply; the
decision log records them. The module prints and writes aggregates only: never a
row, a PERMNO, a ticker, a CUSIP, a GVKEY, a name, or a private path.

Units: CRSP ``shrout`` is in thousands of shares, so market equity is in
thousands of USD. Compustat items are in millions of USD.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from research import m55_signals as sig
from research.m55_index_tilt import CAUSES, DISAPPEARANCE_FIELDS, ME_REASONS, refuse


MANIFEST = "MANIFEST_local.json"
SEALED = "sealed"
REQUIRED = ("crsp_dsf_v2", "crsp_stkshares", "crsp_stkdelists", "crsp_stksecurityinfohist", "crsp_dsp500list_v2",
            "crsp_index_daily", "crsp_dsp500_legacy", "ccm_lnkhist", "comp_fundq", "comp_snapshot_csa_pit",
            "comp_urq", "ibes_statsumu_epsus", "ibes_crsp_link")
SEAL_START, SEAL_END = pd.Timestamp("2019-07-31"), pd.Timestamp("2020-07-31")
MARKET_INDNO = sig.MARKET_INDNO                  # 1000200: CRSP value-weighted market, total return
SHARE_LAG_DAYS = 136                             # D5: a share count is used from its date plus 136 calendar days
SPY_TICKER, SPY_FIRST, SPY_LAST = "SPY", pd.Timestamp("1993-01-01"), pd.Timestamp("1993-02-28")
SPY_RETURNS_FROM = pd.Timestamp("1993-02-01")
SPY_MAX_GAP_ROWS = 5                             # calendar rows between two SPY returns
LEGACY_END = pd.Timestamp("2024-12-31")
FAILURE_REASONS = ("BKPY", "LP", "SHLD", "INSC", "DELQ", "FING", "INSF", "MVOT", "MTMK", "MVCHI", "MVMF")
FAILURE_ACTIONS = ("GLI",)
SPLIT_FACTOR = 2.0                               # D7: rows with dlyfacprc = 2
SPLIT_EXACT_SHARE = 0.99                         # D7: share of split rows where both factors halve exactly
SPLIT_MEDIAN_BOUNDS = (1.8, 2.2)                 # D7: median price ratio and share ratio across the split
AJEXQ_WINDOW_DAYS = 365                          # P-9 aggregate: quarters reported up to a year before a split
SUPPLIED_AJEXQ = 1.0                             # P-9 option (a): S2 uses the cfacshr basis of the first known date
FY1, IBES_CURRENCY = "1", "USD"                  # S1 divides by a USD price: FY1 rows in other currencies drop
EXIT_CLASSES = ("current", "left_index", *CAUSES)
EVENT_RUN_COLUMNS = {"primary": ("level", "chain_mismatch"),            # R4: the switch for the driver
                     "last_close": ("level_last_close", "chain_mismatch_last_close")}
BID_ASK_FLAG = "BA"                              # dlyprcflg: a bid-ask average, not a trade (trial OI-11)
UNITS = {"shrout": "thousands of shares", "market_equity": "thousands of USD", "compustat_items": "millions of USD"}


@dataclass
class WrdsData:
    """The main files as Arrow tables by stem, the manifest, and a cache of derived frames."""

    tables: dict[str, pa.Table]
    manifest: dict[str, Any]
    root: Path | None = None
    cache: dict[str, Any] = field(default_factory=dict)


# Loading ----------------------------------------------------------------------------------

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stem_of(relative: str) -> str:
    return relative.split("/")[0].removesuffix(".parquet")


def load(root: str | Path) -> WrdsData:
    """D9: read the main files listed in the manifest after a SHA-256 check; refuse any path under ``sealed/``."""
    root = Path(root).expanduser().resolve()
    if SEALED in root.parts:
        raise refuse("sealed_path", "the data root is inside a sealed folder")
    manifest = json.loads((root / MANIFEST).read_text())
    sealed = root / SEALED
    parts: dict[str, list[pa.Table]] = {}
    for relative, record in sorted(manifest["files"].items()):
        path = (root / relative).resolve()
        if relative.split("/")[0] == SEALED or path == sealed or sealed in path.parents:
            raise refuse("sealed_path", "the manifest lists a sealed path")
        if root not in path.parents:
            raise refuse("path_outside_root", relative)
        if record["rows"] == 0:          # an empty part writes no data file
            if path.exists():
                raise refuse("file_unexpected", relative)
            continue
        if not path.is_file():
            raise refuse("file_missing", relative)
        if sha256(path) != record["sha256"]:
            raise refuse("hash_mismatch", relative)
        table = pq.read_table(path)
        if table.num_rows != record["rows"]:
            raise refuse("row_count_mismatch", relative)
        parts.setdefault(stem_of(relative), []).append(table)
    missing = [stem for stem in REQUIRED if stem not in parts]
    if missing:
        raise refuse("file_missing", ", ".join(missing))
    return WrdsData({stem: pa.concat_tables(tables) for stem, tables in parts.items()}, manifest, root)


def frame(data: WrdsData, stem: str, columns: list[str]) -> pd.DataFrame:
    """Selected columns as pandas; Arrow dates become datetime64[ns] (a date past 2262 refuses)."""
    table = data.tables[stem].select(columns)
    out = table.to_pandas(date_as_object=False)
    for name in columns:
        if pa.types.is_date(table.schema.field(name).type):
            out[name] = out[name].astype("datetime64[ns]")
    return out


def _cached(data: WrdsData, key: str, build) -> Any:
    if key not in data.cache:
        data.cache[key] = build()
    return data.cache[key]


# Calendar, membership, and the daily file (D1 to D4, D7) ----------------------------------

def in_seal(dates: pd.Series | pd.DatetimeIndex) -> np.ndarray:
    return np.asarray((dates >= SEAL_START) & (dates < SEAL_END))


def calendar(data: WrdsData) -> pd.DatetimeIndex:
    """D2: the trading days of INDNO 1000200 in the main file; no seal day."""
    def build() -> pd.DatetimeIndex:
        index = frame(data, "crsp_index_daily", ["indno", "dlycaldt"])
        dates = index.loc[index["indno"] == MARKET_INDNO, "dlycaldt"]
        if dates.isna().any() or dates.duplicated().any():
            raise refuse("calendar_invalid", "the market index has a missing or repeated date")
        if in_seal(dates).any():
            raise refuse("seal_row_present", "index daily")
        return pd.DatetimeIndex(sorted(dates), name="date")
    return _cached(data, "calendar", build)


def spells(data: WrdsData) -> pd.DataFrame:
    """D4: S&P 500 spells (``permno``, ``start``, ``end``), ``end`` inclusive."""
    def build() -> pd.DataFrame:
        raw = frame(data, "crsp_dsp500list_v2", ["permno", "indno", "mbrstartdt", "mbrenddt"])
        if raw["indno"].nunique() != 1:
            raise refuse("membership_invalid", "more than one index number")
        table = raw.rename(columns={"mbrstartdt": "start", "mbrenddt": "end"})[["permno", "start", "end"]]
        if table.isna().any().any() or (table["start"] > table["end"]).any():
            raise refuse("membership_invalid", "a spell without dates or with start after end")
        table = table.sort_values(["permno", "start"], kind="mergesort").reset_index(drop=True)
        same = table["permno"].to_numpy()[1:] == table["permno"].to_numpy()[:-1]
        if (same & (table["start"].to_numpy()[1:] <= table["end"].to_numpy()[:-1])).any():
            raise refuse("membership_invalid", "overlapping spells")
        return table
    return _cached(data, "spells", build)


def member_mask(rows: pd.DataFrame, table: pd.DataFrame) -> np.ndarray:
    """True for (``permno``, ``date``) rows inside an inclusive spell."""
    out = np.zeros(len(rows), dtype=bool)
    if not len(rows):
        return out
    joined = rows[["permno", "date"]].reset_index(drop=True).reset_index().merge(table, on="permno")
    hit = joined.loc[(joined["start"] <= joined["date"]) & (joined["date"] <= joined["end"]), "index"]
    out[hit.to_numpy()] = True
    return out


def price_path(daily: pd.DataFrame) -> pd.DataFrame:
    """D3: a total-return close index per PERMNO and seal segment, built from ``dlyret`` only.

    The anchor is the segment's first row with a positive price (index 1.0). Each later row with a finite
    ``dlyret`` is the last valid value times (1 + ``dlyret``); a missing ``dlyret`` is NaN. CIZ includes the
    delisting return on the ``dlydelflg = 'Y'`` row; ``delret`` is never added. A return of -100 percent or
    less (only on a delisting row) leaves that row NaN; D6 carries it as the delisting return.
    ``chain_mismatch`` flags a valid row whose ``dlyprevdt`` is not the date of the previous valid row: the
    return of the rows between is not in the path (R6). ``tilt_frames`` exposes these rows as ``path_break``.
    Input rows are sorted by permno and date.
    """
    dates = daily["date"].to_numpy()
    group = daily["permno"].to_numpy(dtype=np.int64) * 2 + (dates >= SEAL_END.to_datetime64())
    gid = np.cumsum(np.r_[True, group[1:] != group[:-1]]) - 1
    priced = daily["prc"].notna().to_numpy()
    ret = daily["dlyret"].to_numpy(dtype=float)
    ok = np.isfinite(ret)
    count = pd.Series(priced.astype(np.int64)).groupby(gid).cumsum().to_numpy()
    anchor = priced & (count == 1)
    after = (count > 0) & ~anchor
    terminal = ok & (ret <= -1.0)
    if (terminal & (daily["dlydelflg"].to_numpy() != "Y")).any():
        raise refuse("return_invalid", "a return of -100 percent or less outside a delisting row")
    step = after & ok & ~terminal
    growth = pd.Series(np.where(step, 1.0 + ret, 1.0)).groupby(gid).cumprod().to_numpy()
    valid = anchor | step
    level = np.where(valid, growth, np.nan)
    valid_dates = pd.Series(np.where(valid, dates, np.datetime64("NaT", "ns")), dtype="datetime64[ns]")
    previous = valid_dates.groupby(gid).ffill().groupby(gid).shift(1).to_numpy()
    prevdt = daily["dlyprevdt"].to_numpy(dtype="datetime64[ns]")
    mismatch = step & (prevdt != previous)
    return pd.DataFrame({"level": level, "terminal": terminal, "chain_mismatch": mismatch,
                         "unanchored": ok & (count == 0)}, index=daily.index)


def split_check(daily: pd.DataFrame) -> dict[str, Any]:
    """D7: at ``dlyfacprc = 2`` both cumulative factors halve, the price halves, and shares double; else refuse."""
    previous = daily.shift(1)
    rows = (daily["dlyfacprc"] == SPLIT_FACTOR) & (daily["permno"] == previous["permno"])
    rows &= daily[["dlycumfacpr", "dlycumfacshr"]].notna().all(axis=1)
    rows &= previous[["dlycumfacpr", "dlycumfacshr"]].notna().all(axis=1)
    if not rows.any():
        raise refuse("split_factor_invalid", "no split row to check")
    pr = previous.loc[rows, "dlycumfacpr"] / daily.loc[rows, "dlycumfacpr"]
    shr = previous.loc[rows, "dlycumfacshr"] / daily.loc[rows, "dlycumfacshr"]
    exact = np.isclose(pr, SPLIT_FACTOR, rtol=1e-9) & np.isclose(shr, SPLIT_FACTOR, rtol=1e-9)
    price = float((previous.loc[rows, "prc"] / daily.loc[rows, "prc"]).median())
    shares = float((daily.loc[rows, "shrout"] / previous.loc[rows, "shrout"]).median())
    result = {"split_rows": int(rows.sum()), "both_factors_halve": int(exact.sum()),
              "factor_rises": int(((pr < 1.0) | (shr < 1.0)).sum()), "median_price_ratio": price,
              "median_share_ratio": shares}
    low, high = SPLIT_MEDIAN_BOUNDS
    if (result["factor_rises"] or exact.mean() < SPLIT_EXACT_SHARE
            or not (low <= price <= high) or not (low <= shares <= high)):
        raise refuse("split_factor_invalid", "the cumulative factors do not fall at a split (D7)")
    return result


def daily(data: WrdsData) -> pd.DataFrame:
    """The main daily rows on the calendar with ``prc`` = |``dlyprc``| (0 is no price) and the D3 path."""
    def build() -> pd.DataFrame:
        table = frame(data, "crsp_dsf_v2", ["permno", "dlycaldt", "dlyret", "dlyprc", "dlyprevdt", "dlydelflg",
                                            "dlycumfacpr", "dlycumfacshr", "dlyfacprc", "shrout", "dlyvol",
                                            "primaryexch", "dlyprcflg"])
        table = table.rename(columns={"dlycaldt": "date"})
        if table["date"].isna().any() or table.duplicated(["permno", "date"]).any():
            raise refuse("daily_invalid", "a row without a date or a repeated PERMNO date")
        if in_seal(table["date"]).any():
            raise refuse("seal_row_present", "daily")
        on_calendar = table["date"].isin(calendar(data)).to_numpy()
        if member_mask(table[~on_calendar], spells(data)).any():
            raise refuse("calendar_invalid", "a member's daily date is not a market index trading day (D2)")
        data.cache["daily_off_calendar"] = int((~on_calendar).sum())
        table = table[on_calendar].sort_values(["permno", "date"], kind="mergesort").reset_index(drop=True)
        price = table["dlyprc"].abs()
        table["prc"] = price.where(price > 0.0)
        table["shrout"] = table["shrout"].astype(float)
        table = pd.concat([table, price_path(table)], axis=1)
        # R4 last-close run: the Y row's return leaves the path, so the path ends at the last trade close.
        last_close = price_path(table.assign(dlyret=table["dlyret"].where(table["dlydelflg"] != "Y")))
        table["level_last_close"] = last_close["level"]
        table["chain_mismatch_last_close"] = last_close["chain_mismatch"]
        data.cache["split_check"] = split_check(table)
        return table
    return _cached(data, "daily", build)


# Market equity (D5) and disappearances (D6) -----------------------------------------------

def market_equity(rows: pd.DataFrame, shares: pd.DataFrame, history: pd.DataFrame | None = None,
                  cal: pd.DatetimeIndex | None = None) -> pd.DataFrame:
    """D5: ME at each daily row t, its reason where it is missing, and the share count at t.

    Share count = the ``shrout`` of the share row with the latest ``shrstartdt`` on or before t - 136 calendar
    days x ``cfacshr`` at that count's basis / ``cfacshr`` at t; ME = |``dlyprc``| at t x the share count. The
    basis is the first row of ``history`` (the PERMNO's full main daily rows; default ``rows``) on or after
    ``shrstartdt`` with a factor, and it must be on or before t. When a gap lies between ``shrstartdt`` and the
    basis row (a calendar row of ``cal`` without a factor row, or the seal) and the factor of the last row before
    ``shrstartdt`` differs from the basis factor, the basis is unknown: ``unmapped`` (card m55-loader-fix-r1,
    item 1). Reasons: no share row, ``no_share_fact``; its ``shrenddt`` before the cutoff, ``stale_share_fact``;
    no basis factor by t, an unknown basis, or no factor at t, ``unmapped``. The share count is NaN under these
    reasons; ME is also ``unmapped`` without a valid close at t or a positive value.
    """
    history = rows if history is None else history
    cal = pd.DatetimeIndex(np.unique(history["date"])) if cal is None else cal
    left = pd.DataFrame({"row": np.arange(len(rows)), "permno": rows["permno"].to_numpy(),
                         "date": rows["date"].to_numpy(),
                         "cutoff": rows["date"].to_numpy() - np.timedelta64(SHARE_LAG_DAYS, "D")})
    facts = shares[["permno", "shrstartdt", "shrenddt", "shrout"]].rename(columns={"shrout": "fact"})
    found = pd.merge_asof(left.sort_values("cutoff"), facts.sort_values("shrstartdt"), left_on="cutoff",
                          right_on="shrstartdt", by="permno", direction="backward")
    factors = history.loc[history["dlycumfacshr"].gt(0.0), ["permno", "date", "dlycumfacshr"]].sort_values("date")
    has_fact = found["shrstartdt"].notna()
    with_basis = pd.merge_asof(found[has_fact].sort_values("shrstartdt"),
                               factors.rename(columns={"date": "basis_date", "dlycumfacshr": "basis_factor"}),
                               left_on="shrstartdt", right_on="basis_date", by="permno", direction="forward")
    with_basis = pd.merge_asof(with_basis.sort_values("shrstartdt"),
                               factors.rename(columns={"date": "prior_date", "dlycumfacshr": "prior_factor"}),
                               left_on="shrstartdt", right_on="prior_date", by="permno", direction="backward",
                               allow_exact_matches=False)
    found = pd.concat([with_basis, found[~has_fact]]).set_index("row").sort_index()
    start = found["shrstartdt"].to_numpy(dtype="datetime64[ns]")
    position = cal.searchsorted(start)
    first_row = np.where(position < len(cal), cal.to_numpy()[np.minimum(position, len(cal) - 1)],
                         np.datetime64("NaT", "ns"))
    basis_date = found["basis_date"].to_numpy(dtype="datetime64[ns]")
    gap = (first_row != basis_date) | in_seal(pd.DatetimeIndex(start))
    prior, basis_factor = found["prior_factor"].to_numpy(dtype=float), found["basis_factor"].to_numpy(dtype=float)
    changed = gap & np.isfinite(prior) & ~np.isclose(prior, basis_factor, rtol=1e-9, atol=0.0)
    price, factor = rows["prc"].to_numpy(), rows["dlycumfacshr"].to_numpy(dtype=float)
    count = found["fact"].to_numpy(dtype=float) * basis_factor / factor
    no_fact = found["shrstartdt"].isna().to_numpy()
    stale = (found["shrenddt"] < found["cutoff"]).to_numpy()
    no_basis = ~(found["basis_date"] <= found["date"]).to_numpy() | changed | ~(factor > 0.0)
    share_reason = np.full(len(rows), None, dtype=object)
    for mask, label in ((no_basis, "unmapped"), (stale, "stale_share_fact"), (no_fact, "no_share_fact")):
        share_reason[mask] = label    # later assignments win: the order is the reason priority
    count = np.where(pd.isna(share_reason), count, np.nan)
    value = price * count
    reason = share_reason.copy()
    reason[pd.isna(reason) & ~(value > 0.0)] = "unmapped"
    reason[~np.isfinite(rows["level"].to_numpy()) | ~np.isfinite(price) | ~(factor > 0.0)] = "unmapped"
    me = np.where(pd.isna(reason), value, np.nan)
    return pd.DataFrame({"market_equity": me, "me_reason": reason, "share_count": count,
                         "basis_changed_across_gap": changed & ~no_fact & ~stale}, index=rows.index)


def member_market_equity(data: WrdsData) -> pd.DataFrame:
    """D5 on every daily row of a member PERMNO, with the basis looked up in the full main rows (cached)."""
    def build() -> pd.DataFrame:
        rows = daily(data)
        rows = rows[rows["permno"].isin(spells(data)["permno"])]
        shares = frame(data, "crsp_stkshares", ["permno", "shrstartdt", "shrenddt", "shrout"])
        return market_equity(rows, shares, rows, calendar(data))
    return _cached(data, "member_market_equity", build)


def cause_of(action: Any, reason: Any, payment: Any) -> str:
    """D6: ``cash_merger`` only for MER paid in CASH; ``failure`` for the listed reasons or GLI; else ``unknown``."""
    if action == "MER" and payment == "CASH":
        return "cash_merger"
    if reason in FAILURE_REASONS or action in FAILURE_ACTIONS:
        return "failure"
    return "unknown"


def disappearances(data: WrdsData, run: str = "primary") -> pd.DataFrame:
    """D6: member PERMNOs with a delisting record whose price path ends before the last calendar row.

    ``effective_date`` is the later of the calendar row after the last row with a value in the price path and
    the date of the ``dlydelflg = 'Y'`` row: no settlement happens before its source row (card
    m55-loader-fix-r1, item 3). ``known_at = effective_date``. In the ``primary`` run, ``delisting_return`` is
    0.0 when the delisting row is the last valued row (CIZ already put the delisting return in the path), the
    delisting row's return when it is -100 percent or less (not representable in a positive path), and NaN
    otherwise, so the engine default applies. In the ``last_close`` run (R4 sensitivity), the path ends at the
    last trade close and every event settles there (0.0). ``last_valid`` (the last valued row) is kept for the
    window filter; ``reference_valued`` is False when rows without a value lie between it and the effective row.
    """
    if run not in EVENT_RUN_COLUMNS:
        raise refuse("event_run_invalid", run)

    def build() -> pd.DataFrame:
        cal = calendar(data)
        rows = daily(data)
        level = EVENT_RUN_COLUMNS[run][0]
        last = rows[rows[level].notna()].groupby("permno").tail(1).set_index("permno")
        record = frame(data, "crsp_stkdelists", ["permno", "delactiontype", "delreasontype", "delpaymenttype"])
        if record["permno"].duplicated().any():
            raise refuse("disappearances_invalid", "two delisting records for one PERMNO")
        record = record[record["permno"].isin(spells(data)["permno"]) & record["permno"].isin(last.index)]
        flagged = rows[(rows["dlydelflg"] == "Y") & rows["permno"].isin(record["permno"])]
        if flagged["permno"].duplicated().any():
            raise refuse("disappearances_invalid", "two delisting rows for one PERMNO")
        flagged = flagged.set_index("permno")
        out = []
        for item in record.itertuples(index=False):
            end = last.loc[item.permno]
            position = cal.get_loc(end["date"]) + 1
            effective = position
            if item.permno in flagged.index:
                effective = max(position, cal.get_loc(flagged.loc[item.permno, "date"]))
            if effective >= len(cal):
                continue
            if run == "last_close" or end["dlydelflg"] == "Y":
                value = 0.0
            elif item.permno in flagged.index and flagged.loc[item.permno, "terminal"]:
                value = float(flagged.loc[item.permno, "dlyret"])
            else:
                value = np.nan
            out.append({"permanent_id": str(item.permno), "effective_date": cal[effective],
                        "known_at": cal[effective],
                        "cause": cause_of(item.delactiontype, item.delreasontype, item.delpaymenttype),
                        "delisting_return": value, "last_valid": end["date"],
                        "reference_valued": effective == position})
        columns = [*DISAPPEARANCE_FIELDS, "last_valid", "reference_valued"]
        table = pd.DataFrame(out, columns=columns)
        for name in ("effective_date", "known_at", "last_valid"):
            table[name] = pd.to_datetime(table[name])
        table["delisting_return"] = table["delisting_return"].astype(float)
        table["reference_valued"] = table["reference_valued"].astype(bool)
        return table
    return _cached(data, f"disappearances_{run}", build)


# Engine frames ----------------------------------------------------------------------------

def segment_rows(cal: pd.DatetimeIndex, date: pd.Timestamp) -> pd.DatetimeIndex:
    return cal[(cal >= SEAL_END) == (date >= SEAL_END)]


def intervals(table: pd.DataFrame) -> pd.DataFrame:
    """D4: engine intervals; ``end_date`` is the first calendar day after ``mbrenddt``."""
    ids = table["permno"].astype(str)
    return pd.DataFrame({"symbol": ids, "permanent_id": ids, "start_date": table["start"],
                         "end_date": table["end"] + pd.Timedelta(days=1), "start_known_at": table["start"],
                         "end_known_at": table["end"]}).reset_index(drop=True)


def eligibility(table: pd.DataFrame, rows: pd.DatetimeIndex, columns: pd.Index) -> pd.DataFrame:
    """D4: eligibility at the decision row t = r - 1 from intervals in force at t, as the engine resolves them.

    The engine admits a member at row r when ``start <= t`` and drops it once ``t >= mbrenddt`` (its
    ``end_known_at``), so a spell is eligible on rows ``start <= t < mbrenddt``: a member on its last index
    day is not bought for the next row (the M5 rule resolved_universe_at_next_execution_row).
    """
    out = np.zeros((len(rows), len(columns)), dtype=bool)
    position = columns.get_indexer(table["permno"].astype(str))
    for column, start, end in zip(position, table["start"], table["end"]):
        if column >= 0:
            out[rows.searchsorted(start, "left"):rows.searchsorted(end, "left"), column] = True
    return pd.DataFrame(out, index=rows, columns=columns)


def panel(values: pd.Series, rows_frame: pd.DataFrame, rows: pd.DatetimeIndex, columns: pd.Index,
          fill: Any = np.nan, dtype: Any = float) -> pd.DataFrame:
    out = np.full((len(rows), len(columns)), fill, dtype=dtype)
    out[rows.get_indexer(rows_frame["date"]), columns.get_indexer(rows_frame["permno"].astype(str))] = values
    return pd.DataFrame(out, index=rows, columns=columns)


def tilt_frames(data: WrdsData, start: str | pd.Timestamp, end: str | pd.Timestamp,
                run: str = "primary") -> dict[str, Any]:
    """The engine inputs for a window inside one seal segment (the driver adds the six signals).

    Rows run from the segment's first calendar row to the first row of the month after ``end``. Columns are
    the PERMNOs (as strings, D1) with a spell that touches these rows. A cell without a daily row has no price
    and ME reason ``unmapped``. ``path_break`` is True on a row whose return starts after a return that is not
    in the path (decision log P-1): the driver blanks every level window (a price ratio or a maximum) that holds
    a True row and its previous valid row (R6), and reports each held position across one. Disappearances keep
    events whose last valued row and effective row are inside the rows. ``run`` is the R4 switch: ``primary``,
    or ``last_close`` (the path ends at the last trade close and every event settles there; the engine run
    must be ``last_close`` too). A window that crosses the seal refuses (D9: the driver runs separate
    segments). An event whose effective row follows rows without a value refuses: the engine settles from a
    close on the row before the effective row (item 3).
    """
    if run not in EVENT_RUN_COLUMNS:
        raise refuse("event_run_invalid", run)
    level, chain = EVENT_RUN_COLUMNS[run]
    cal = calendar(data)
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if start not in cal or end not in cal or not start < end:
        raise refuse("window_invalid", "start and end must be calendar rows with start before end")
    if (start >= SEAL_END) != (end >= SEAL_END):
        raise refuse("window_crosses_seal", "run each seal segment separately (D9)")
    segment = segment_rows(cal, start)
    later = segment[segment.to_period("M") > end.to_period("M")]
    if not len(later):
        raise refuse("window_invalid", "the segment has no row in a month after end")
    rows = segment[segment <= later[0]]
    table = spells(data)
    touching = table[(table["start"] <= rows[-1]) & (table["end"] >= rows[0])]
    permnos = np.sort(touching["permno"].unique())
    columns = pd.Index([str(p) for p in permnos], name="permanent_id")
    member_spells = table[table["permno"].isin(permnos)]
    source = daily(data)
    history = source[source["permno"].isin(permnos)]
    window = history[history["date"].between(rows[0], rows[-1])]
    me = market_equity(window.assign(level=window[level]),       # ME needs a close of the same run's path
                       frame(data, "crsp_stkshares", ["permno", "shrstartdt", "shrenddt", "shrout"]), history, cal)
    prices = panel(window[level].to_numpy(), window, rows, columns)
    market = panel(me["market_equity"].to_numpy(), window, rows, columns)
    reason = panel(me["me_reason"].to_numpy(), window, rows, columns, fill="unmapped", dtype=object)
    reason = reason.where(market.isna(), None)
    events = disappearances(data, run)
    events = events[events["permanent_id"].isin(columns) & events["last_valid"].between(rows[0], rows[-1])
                    & events["effective_date"].between(rows[0], rows[-1])]
    if not events["reference_valued"].all():
        raise refuse("terminal_gap_unsupported", "rows without a value lie before a delisting row in the window")
    breaks = panel(window[chain].to_numpy(), window, rows, columns, fill=False, dtype=bool)
    return {"calendar": rows, "prices": prices, "path_break": breaks,
            "eligible": eligibility(member_spells, rows, columns),
            "market_equity": market, "me_reason": reason, "intervals": intervals(member_spells),
            "disappearances": events[list(DISAPPEARANCE_FIELDS)].reset_index(drop=True)}


# Signal inputs (D8) -----------------------------------------------------------------------

def _fiscal_conflicts(table: pd.DataFrame, fiscal: list[str], known: str) -> np.ndarray:
    """P-5 after card m55-loader-fix-r1, item 2: the rows that lose a fiscal-key conflict, first known wins.

    A record is a (``gvkey``, ``datadate``, fiscal key) pair, first known at the earliest ``known`` of its rows
    (a missing date is never known). In each gvkey, records are taken in order of first known date. A record whose
    fiscal key or ``datadate`` an earlier record holds loses. Records first known on the same date that share a
    fiscal key or a ``datadate`` all lose and hold both. So a later row never removes an earlier known row.
    """
    keys = ["gvkey", "datadate", *fiscal]
    never = pd.Timestamp.max.floor("D")
    pairs = table[keys].assign(_first=table[known].fillna(never)).groupby(keys, sort=False)["_first"].min()
    pairs = pairs.reset_index()
    clash = pairs.duplicated(["gvkey", *fiscal], keep=False) | pairs.duplicated(["gvkey", "datadate"], keep=False)
    losers = []
    for gvkey, group in pairs[pairs["gvkey"].isin(pairs.loc[clash, "gvkey"])].groupby("gvkey", sort=False):
        held_dates: set = set()
        held_keys: set = set()
        for _, same in group.groupby("_first", sort=True):
            records = [(row[1], row[2:]) for row in same[keys].itertuples(index=False, name=None)]
            fresh = [r for r in records if r[0] not in held_dates and r[1] not in held_keys]
            dates, fiscal_keys = Counter(r[0] for r in fresh), Counter(r[1] for r in fresh)
            losers += [(gvkey, d, *k) for d, k in records
                       if (d, k) not in fresh or dates[d] > 1 or fiscal_keys[k] > 1]
            held_dates.update(dates)
            held_keys.update(fiscal_keys)
    if not losers:
        return np.zeros(len(table), dtype=bool)
    lost = pd.DataFrame(losers, columns=keys).assign(_x=True)
    return table[keys].merge(lost, how="left", on=keys)["_x"].notna().to_numpy()


def _drop(table: pd.DataFrame, rules: list[tuple[str, Any]]) -> tuple[pd.DataFrame, dict[str, int]]:
    """Apply the drop rules in order; each rule is a label and a function of the remaining rows."""
    counts = {}
    for label, rule in rules:
        mask = np.asarray(rule(table), dtype=bool)
        counts[label] = int(mask.sum())
        table = table[~mask].reset_index(drop=True)
    return table, counts


def _integral(series: pd.Series) -> pd.Series:
    values = series.to_numpy(dtype=float)
    return pd.Series(np.isfinite(values) & (values == np.round(values)), index=series.index)


def signal_tables(data: WrdsData) -> tuple[sig.SignalInputs, dict[str, dict[str, int]]]:
    """D8: ``SignalInputs`` and the dropped rows by table and reason; ``check_inputs`` must pass."""
    def build() -> tuple[sig.SignalInputs, dict[str, dict[str, int]]]:
        members = spells(data)
        rows = daily(data)
        rows = rows[rows["permno"].isin(members["permno"])]
        # D8 amendment (card m55-loader-fix-r1, item 7): shrout is the D5 share count on the row's basis, NaN
        # under the D5 reasons; the raw daily shrout is not an input (R1). primaryexch and dlyprcflg serve the
        # driver (trial OI-11, OI-12).
        daily_table = pd.DataFrame({"permno": rows["permno"].to_numpy(), "date": rows["date"].to_numpy(),
                                    "ret": rows["dlyret"].to_numpy(), "prc": rows["prc"].to_numpy(),
                                    "shrout": member_market_equity(data).loc[rows.index, "share_count"].to_numpy(),
                                    "cfacpr": rows["dlycumfacpr"].to_numpy(),
                                    "cfacshr": rows["dlycumfacshr"].to_numpy(),
                                    "primaryexch": rows["primaryexch"].to_numpy(),
                                    "dlyprcflg": rows["dlyprcflg"].to_numpy()})
        drops: dict[str, dict[str, int]] = {"daily": {"off_calendar": data.cache["daily_off_calendar"]},
                                            "members": {}}

        annual = frame(data, "comp_snapshot_csa_pit", ["gvkey", "datadate", "fyear", "pitdate1",
                                                       *sig.ANNUAL_ITEMS]).rename(columns={"pitdate1": "known_date"})
        annual, drops["fund_annual"] = _drop(annual, [
            ("no_fiscal_key", lambda t: t["gvkey"].isna() | t["datadate"].isna() | ~_integral(t["fyear"])),
            ("no_known_date", lambda t: t["known_date"].isna()),
            ("known_before_datadate", lambda t: t["known_date"] < t["datadate"]),
            ("fiscal_key_conflict", lambda t: _fiscal_conflicts(t, ["fyear"], "known_date"))])
        annual["fyear"] = annual["fyear"].astype(np.int64)

        urq = frame(data, "comp_urq", ["gvkey", "datadate", "fqtr", "rdq", "prelimqprd", "finalqprd", "epspxq"])
        # P-9 option (a): URQ ajexq is not first-reported, so it is never read. First-reported EPS is on the share
        # basis of its report date (ASC 260), the basis of CRSP cfacshr at that date; S2 applies the cfacshr ratio.
        urq["ajexq"] = SUPPLIED_AJEXQ
        keys = frame(data, "comp_fundq", ["gvkey", "datadate", "fyearq"]).dropna().drop_duplicates()
        keys = keys[~keys.duplicated(["gvkey", "datadate"], keep=False)]    # two fiscal years: no fiscal key
        urq = urq.merge(keys, on=["gvkey", "datadate"], how="left")
        period = urq["prelimqprd"].fillna(urq["finalqprd"])
        urq["known_date"] = period.where(urq["rdq"].isna() | (period >= urq["rdq"]), urq["rdq"])
        urq["known_date"] = urq["known_date"].where(period.notna())
        keyed, key_drops = _drop(urq, [
            ("no_fiscal_key", lambda t: t["gvkey"].isna() | t["datadate"].isna() | ~_integral(t["fyearq"])
             | ~t["fqtr"].isin([1, 2, 3, 4]))])
        keyed[["fyearq", "fqtr"]] = keyed[["fyearq", "fqtr"]].astype(np.int64)
        # Item 2: each table resolves fiscal-key conflicts on its own clock; an announcement is known on rdq.
        announcements, conflicts = _drop(keyed, [
            ("fiscal_key_conflict", lambda t: _fiscal_conflicts(t, ["fyearq", "fqtr"], "rdq"))])
        drops["announcements"] = {**key_drops, **conflicts}
        announcements = announcements[["gvkey", "datadate", "fyearq", "fqtr", "rdq"]]
        quarterly, quarter_drops = _drop(keyed, [
            ("no_known_date", lambda t: t["known_date"].isna()),
            ("known_before_datadate", lambda t: t["known_date"] < t["datadate"]),
            ("fiscal_key_conflict", lambda t: _fiscal_conflicts(t, ["fyearq", "fqtr"], "known_date"))])
        drops["fund_quarterly"] = {**key_drops, **quarter_drops}
        quarterly = quarterly[["gvkey", "datadate", "fyearq", "fqtr", "known_date", *sig.QUARTER_ITEMS]]

        link = frame(data, "ccm_lnkhist", ["gvkey", "lpermno", "linkdt", "linkenddt"])
        link, drops["link"] = _drop(link, [("no_key", lambda t: t[["gvkey", "linkdt"]].isna().any(axis=1)
                                            | ~_integral(t["lpermno"]))])
        link = link.assign(permno=link["lpermno"].astype(np.int64))[list(sig.SCHEMA["link"])]
        ibes_link = frame(data, "ibes_crsp_link", ["ticker", "permno", "sdate", "edate", "score"])
        ibes_link, drops["ibes_link"] = _drop(ibes_link, [
            ("no_key", lambda t: t[["ticker", "permno", "sdate", "score"]].isna().any(axis=1))])
        ibes = frame(data, "ibes_statsumu_epsus", ["ticker", "statpers", "fpedats", "fpi", "meanest", "curcode"])
        ibes, drops["ibes"] = _drop(ibes, [
            ("no_key", lambda t: t[["ticker", "statpers", "fpi", "fpedats"]].isna().any(axis=1))])
        other = (ibes["fpi"] == FY1) & (ibes["curcode"] != IBES_CURRENCY)     # a missing currency is not USD
        drops["ibes_non_usd_fy1_by_year"] = {str(y): int(n) for y, n in
                                             ibes.loc[other, "statpers"].dt.year.value_counts().sort_index().items()}
        drops["ibes"]["non_usd_fy1"] = int(other.sum())
        ibes = ibes[~other].reset_index(drop=True)[list(sig.SCHEMA["ibes"])]
        index = frame(data, "crsp_index_daily", ["indno", "dlycaldt", "dlytotret"])
        index = index[index["indno"] == MARKET_INDNO].rename(columns={"dlycaldt": "date", "dlytotret": "ret"})
        drops["index_daily"] = {}
        inputs = sig.SignalInputs(
            daily=daily_table, members=members.reset_index(drop=True), fund_annual=annual[
                list(sig.SCHEMA["fund_annual"])], fund_quarterly=quarterly, announcements=announcements,
            link=link, ibes_link=ibes_link, ibes=ibes, index_daily=index[["date", "indno", "ret"]].reset_index(
                drop=True))
        sig.check_inputs(inputs)
        return inputs, drops
    return _cached(data, "signal_tables", build)


def urq_ajexq_aggregate(data: WrdsData) -> dict[str, Any]:
    """P-9 aggregate (never an input): URQ ``ajexq`` of quarters reported before a CRSP 2-for-1 split.

    Quarters whose ``rdq`` falls up to a year before a split of the linked PERMNO (CCM link valid at ``rdq``) were
    reported before the split, so a first-reported ``ajexq`` would be 1. The count shows that URQ ``ajexq`` is a
    current-vintage value; the loader supplies ``ajexq`` 1.0 instead.
    """
    rows = daily(data)
    splits = rows.loc[rows["dlyfacprc"] == SPLIT_FACTOR, ["permno", "date"]].rename(columns={"date": "split"})
    link = frame(data, "ccm_lnkhist", ["gvkey", "lpermno", "linkdt", "linkenddt"]).dropna(subset=["lpermno"])
    link["permno"] = link["lpermno"].astype(np.int64)
    urq = frame(data, "comp_urq", ["gvkey", "datadate", "rdq", "ajexq"]).dropna(subset=["rdq"])
    hit = urq.merge(link[["gvkey", "permno", "linkdt", "linkenddt"]], on="gvkey")
    hit = hit[(hit["linkdt"] <= hit["rdq"]) & (hit["linkenddt"].isna() | (hit["rdq"] <= hit["linkenddt"]))]
    hit = hit.merge(splits, on="permno")
    hit = hit[(hit["split"] > hit["rdq"]) & (hit["split"] <= hit["rdq"] + pd.Timedelta(days=AJEXQ_WINDOW_DAYS))]
    hit = hit.drop_duplicates(["gvkey", "datadate"])
    return {"quarters_before_split": int(len(hit)), "ajexq_one": int((hit["ajexq"] == 1.0).sum())}


def signal_inputs(data: WrdsData) -> sig.SignalInputs:
    """The signal inputs (D8, P-9 option (a), FY1 rows in USD only)."""
    return signal_tables(data)[0]


# Benchmarks -------------------------------------------------------------------------------

def spy_permno(data: WrdsData) -> int:
    """The one PERMNO with ticker SPY in early 1993 (the pull's preflight rule); never printed."""
    info = frame(data, "crsp_stksecurityinfohist", ["permno", "ticker", "secinfostartdt", "secinfoenddt"])
    hit = info[(info["ticker"] == SPY_TICKER) & (info["secinfostartdt"] <= pd.Timestamp("1993-03-31"))
               & (info["secinfoenddt"] >= pd.Timestamp("1993-02-01"))]
    if hit["permno"].nunique() != 1:
        raise refuse("spy_invalid", "SPY does not resolve to one PERMNO")
    return int(hit["permno"].iloc[0])


def spy_check(data: WrdsData) -> dict[str, Any]:
    """SPY: one PERMNO, first return in 1993-01 or 1993-02, at most five calendar rows between two returns."""
    cal = calendar(data)
    rows = daily(data)
    returns = rows.loc[(rows["permno"] == spy_permno(data)) & rows["dlyret"].notna(), "date"]
    if not len(returns) or not SPY_FIRST <= returns.iloc[0] <= SPY_LAST:
        raise refuse("spy_invalid", "the first SPY return is not in 1993-01 or 1993-02")
    gap = int(np.diff(cal.get_indexer(returns)).max(initial=1)) - 1
    if gap > SPY_MAX_GAP_ROWS:
        raise refuse("spy_invalid", f"{gap} calendar rows between two SPY returns")
    return {"permnos": 1, "first_return_month": returns.iloc[0].strftime("%Y-%m"), "max_gap_rows": gap}


def benchmarks(data: WrdsData) -> pd.DataFrame:
    """Daily total returns on the calendar: SPY ``dlyret`` from 1993-02, INDNO 1000200 ``dlytotret``, and the
    legacy S&P 500 value-weighted ``vwretd`` to 2024-12-31. Never ``sprtrn`` or the 1000502 price return."""
    cal = calendar(data)
    rows = daily(data)
    spy = rows[(rows["permno"] == spy_permno(data)) & (rows["date"] >= SPY_RETURNS_FROM)].set_index("date")["dlyret"]
    index = frame(data, "crsp_index_daily", ["indno", "dlycaldt", "dlytotret"])
    market = index[index["indno"] == MARKET_INDNO].set_index("dlycaldt")["dlytotret"]
    legacy = frame(data, "crsp_dsp500_legacy", ["caldt", "vwretd"])
    legacy = legacy[legacy["caldt"] <= LEGACY_END].set_index("caldt")["vwretd"]
    if not legacy.index.isin(cal).all() or legacy.index.duplicated().any():
        raise refuse("calendar_invalid", "a legacy S&P 500 date is not a calendar row")
    return pd.DataFrame({"spy": spy.reindex(cal), "crsp_vw_market": market.reindex(cal),
                         "sp500_vw_legacy": legacy.reindex(cal)}, index=cal)


# Intake report ----------------------------------------------------------------------------

def member_days(data: WrdsData) -> pd.DataFrame:
    """Every (PERMNO, calendar row) inside an inclusive spell, with its daily row values when it has one."""
    cal = calendar(data)
    parts = []
    for item in spells(data).itertuples(index=False):
        dates = cal[(cal >= item.start) & (cal <= item.end)]
        parts.append(pd.DataFrame({"permno": item.permno, "date": dates}))
    days = pd.concat(parts, ignore_index=True)
    rows = daily(data)
    rows = rows[rows["permno"].isin(spells(data)["permno"])]
    values = pd.concat([rows[["permno", "date", "dlyret", "prc", "dlyvol", "level", "shrout", "dlyprcflg"]],
                        member_market_equity(data)], axis=1)
    days = days.merge(values, on=["permno", "date"], how="left", indicator="row")
    days["has_row"] = days.pop("row").eq("both")
    days["me_reason"] = days["me_reason"].where(days["has_row"], "unmapped")
    days["dollar_volume"] = (days["prc"] * days["dlyvol"]).fillna(0.0)
    return days


def exit_class(data: WrdsData) -> pd.Series:
    """Later exit class per PERMNO: the D6 cause of a disappearance, else ``current`` at the vintage end, else
    ``left_index``."""
    table = spells(data)
    vintage = pd.Timestamp(data.manifest["vintage"])
    out = pd.Series("left_index", index=table["permno"].unique())
    out[table.loc[table["end"] >= vintage, "permno"].unique()] = "current"
    events = disappearances(data)
    out[events["permanent_id"].astype(np.int64).to_numpy()] = events["cause"].to_numpy()
    return out


def _shares(days: pd.DataFrame, by: str) -> dict[str, dict[str, float]]:
    out = {}
    for key, group in days.groupby(by):
        total = float(group["dollar_volume"].sum())
        reasons = group["me_reason"].fillna("present")
        out[str(key)] = {"member_days": int(len(group)),
                         **{f"days_{r}": int((reasons == r).sum()) for r in ("present", *ME_REASONS)},
                         **{f"dv_share_{r}": (float(group.loc[reasons == r, "dollar_volume"].sum()) / total
                                              if total else float("nan")) for r in ("present", *ME_REASONS)}}
    return out


def intake_report(data: WrdsData) -> dict[str, Any]:
    """The intake aggregates; a hard check that fails refuses (fail closed)."""
    rows = daily(data)
    days = member_days(data)
    days["year"] = days["date"].dt.year
    days["exit"] = days["permno"].map(exit_class(data))
    per_day = days.groupby("date").size()
    by_year = per_day.groupby(per_day.index.year)
    members = {str(y): {"days": int(len(v)), "mean": float(v.mean()), "min": int(v.min()), "max": int(v.max()),
                        "days_500": int((v == 500).sum())} for y, v in by_year}
    coverage = {"member_days": int(len(days)), "with_daily_row": int(days["has_row"].sum()),
                "with_price": int(days["prc"].notna().sum()), "with_return": int(days["dlyret"].notna().sum()),
                "with_path_value": int(days["level"].notna().sum())}
    events = disappearances(data)
    causes = {c: int((events["cause"] == c).sum()) for c in CAUSES}
    in_path = int((events["delisting_return"] == 0.0).sum())
    terminal = int((events["delisting_return"].notna() & (events["delisting_return"] != 0.0)).sum())
    member_rows = rows[rows["permno"].isin(spells(data)["permno"])]
    breaks = member_rows[member_rows["chain_mismatch"]]
    break_days = member_mask(breaks, spells(data))
    break_decades = (breaks.loc[break_days, "date"].dt.year // 10 * 10).value_counts().sort_index()
    last_rows = member_rows[member_rows["level"].notna()].groupby("permno")["date"].max()
    early_end = last_rows[(last_rows < calendar(data)[-1])].index
    no_record = last_rows[early_end.difference(events["permanent_id"].astype(np.int64))]
    end_months = no_record.dt.to_period("M").astype(str).value_counts().sort_index()
    inputs, drops = signal_tables(data)
    fy1 = inputs.ibes[inputs.ibes["fpi"] == "1"]
    duplicate_fy1 = int(pd.DataFrame({"t": fy1["ticker"], "m": fy1["statpers"].dt.to_period("M")}).duplicated().sum())
    if duplicate_fy1:
        raise refuse("duplicate_key", "ibes: two FY1 rows in one ticker-month")
    tables = {name: {"rows": int(len(getattr(inputs, name))), "dropped": drops[name]} for name in sig.SCHEMA}
    with_row = days[days["has_row"]]
    shares_by_year = {str(y): {"rows": int(len(g)), "raw": int((g["shrout"] > 0.0).sum()),
                               "d5": int(g["share_count"].notna().sum()),
                               "basis_changed_across_gap": int(g["basis_changed_across_gap"].eq(True).sum())}
                      for y, g in with_row.groupby("year")}
    terminal_gaps = {run: int((~disappearances(data, run)["reference_valued"]).sum()) for run in EVENT_RUN_COLUMNS}
    supplied = inputs.fund_quarterly["ajexq"]
    raw = frame(data, "ibes_statsumu_epsus", ["ticker", "statpers", "fpedats", "fpi", "curcode"])
    raw = raw[raw[["ticker", "statpers", "fpi", "fpedats"]].notna().all(axis=1) & (raw["fpi"] == FY1)]
    usd_fy1 = {"file_usd": int((raw["curcode"] == IBES_CURRENCY).sum()), "inputs": int((inputs.ibes["fpi"] == FY1).sum())}
    return {
        "vintage": data.manifest["vintage"],
        "calendar": {"rows": int(len(calendar(data))), "first": str(calendar(data)[0].date()),
                     "last": str(calendar(data)[-1].date()), "seal_rows": 0,
                     "daily_off_calendar_non_member_rows": data.cache["daily_off_calendar"]},
        "members_per_day": members, "coverage": coverage,
        "me_by_year": _shares(days, "year"), "me_by_exit": _shares(days, "exit"),
        "disappearances": {"total": int(len(events)), **causes, "delisting_return_in_path": in_path,
                           "delisting_return_supplied_minus_100": terminal,
                           "delisting_return_missing": int(events["delisting_return"].isna().sum())},
        "price_path": {"chain_mismatch_rows": int(member_rows["chain_mismatch"].sum()),
                       "chain_mismatch_permnos": int(breaks["permno"].nunique()),
                       "chain_mismatch_in_member_spell": int(break_days.sum()),
                       "chain_mismatch_in_member_spell_by_decade": {str(k): int(v) for k, v in break_decades.items()},
                       "unanchored_return_rows": int(member_rows["unanchored"].sum()),
                       "zero_price_rows": int((member_rows["dlyprc"] == 0.0).sum()),
                       "path_ends_early_without_delisting_record": len(no_record),
                       "path_ends_early_by_month": {k: int(v) for k, v in end_months.items()}},
        "spy": spy_check(data), "split_check": data.cache["split_check"],
        "signal_tables": tables, "duplicate_fy1_ticker_month": duplicate_fy1,
        "ajexq": {"supplied_rows": int(len(supplied)), "supplied_one": int((supplied == SUPPLIED_AJEXQ).sum()),
                  "urq": urq_ajexq_aggregate(data)},
        "ibes_non_usd_fy1_by_year": drops["ibes_non_usd_fy1_by_year"], "ibes_fy1_rows": usd_fy1,
        "share_counts_by_year": shares_by_year, "terminal_gap_events": terminal_gaps,
        "last_close_events": int(len(disappearances(data, "last_close"))),
        "bid_ask_member_days": {"member_days": int(len(days)),
                                "bid_ask": int((days["dlyprcflg"] == BID_ASK_FLAG).sum())},
    }


def _fmt(value: float) -> str:
    return "n/a" if value != value else f"{value:.4f}"


def intake_markdown(report: dict[str, Any]) -> str:
    """The intake report as Markdown: aggregates only."""
    lines = ["# M5.5 WRDS Loader Intake Report", "",
             f"Vintage {report['vintage']}. Main files only; the sealed files were not opened. Aggregates only.",
             "", "## Checks", ""]
    checks = [
        ("D2 calendar: every member daily date is a market index trading day; no seal row", True),
        ("SPY: one PERMNO, first return in 1993-01 or 1993-02, at most 5 calendar rows between returns",
         report["spy"]["max_gap_rows"] <= SPY_MAX_GAP_ROWS),
        ("D7 split check: both cumulative factors fall at a split; price halves; shares double",
         report["split_check"]["factor_rises"] == 0),
        ("Duplicate FY1 row per ticker-month is zero", report["duplicate_fy1_ticker_month"] == 0),
        ("Signal inputs pass `check_inputs`", True),
        ("P-9: `fund_quarterly` `ajexq` is 1.0 on every supplied row (URQ `ajexq` is not read)",
         report["ajexq"]["supplied_one"] == report["ajexq"]["supplied_rows"]),
        ("IBES: the FY1 rows of the signal inputs are exactly the keyed USD FY1 rows of the file",
         report["ibes_fy1_rows"]["inputs"] == report["ibes_fy1_rows"]["file_usd"]),
        ("D6: no event settles after rows without a value (the engine needs a close on the row before), in both "
         "R4 runs", not any(report["terminal_gap_events"].values())),
    ]
    lines += [f"- {'PASS' if ok else 'FAIL'}: {text}" for text, ok in checks]
    spy, split, cal = report["spy"], report["split_check"], report["calendar"]
    lines += ["", f"Calendar: {cal['rows']} rows, {cal['first']} to {cal['last']}; seal rows {cal['seal_rows']}; "
              f"non-member daily rows off the calendar dropped: {cal['daily_off_calendar_non_member_rows']}.",
              f"SPY: first return {spy['first_return_month']}; largest gap {spy['max_gap_rows']} calendar rows.",
              f"Split rows {split['split_rows']}; both factors halve exactly on {split['both_factors_halve']}; "
              f"factor rises {split['factor_rises']}; median price ratio {split['median_price_ratio']:.4f}; "
              f"median share ratio {split['median_share_ratio']:.4f}.",
              f"URQ `ajexq` (aggregate only, not read for S2): {report['ajexq']['urq']['ajexq_one']} of "
              f"{report['ajexq']['urq']['quarters_before_split']} quarters reported up to a year before a split have "
              f"`ajexq` 1; the loader supplies 1.0 on all {report['ajexq']['supplied_rows']} `fund_quarterly` rows "
              "(P-9 option (a)).", "",
              "## Members Per Day By Year", "", "| Year | Days | Mean | Min | Max | Days with 500 |",
              "| --- | --- | --- | --- | --- | --- |"]
    lines += [f"| {y} | {v['days']} | {v['mean']:.1f} | {v['min']} | {v['max']} | {v['days_500']} |"
              for y, v in report["members_per_day"].items()]
    c = report["coverage"]
    lines += ["", "## Member-Day Coverage", "", f"Member-days {c['member_days']}; with a daily row "
              f"{c['with_daily_row']}; with a price {c['with_price']}; with a return {c['with_return']}; with a "
              f"total-return path value {c['with_path_value']}.", ""]
    for title, key in (("Market Equity By Year", "me_by_year"), ("Market Equity By Later Exit Class", "me_by_exit")):
        reasons = ("present", *ME_REASONS)
        lines += [f"## {title}", "", "Member-days by ME reason, then the share of member dollar volume "
                  "(split-only close x split-adjusted volume) in each reason.", "",
                  "| Key | Member-days | " + " | ".join(reasons) + " | " + " | ".join(f"DV {r}" for r in reasons)
                  + " |", "| --- " * (2 + 2 * len(reasons)) + "|"]
        for key, v in report[key].items():
            lines.append(f"| {key} | {v['member_days']} | " + " | ".join(str(v[f'days_{r}']) for r in reasons)
                         + " | " + " | ".join(_fmt(v[f'dv_share_{r}']) for r in reasons) + " |")
        lines.append("")
    d = report["disappearances"]
    lines += ["## Disappearances (D6)", "", f"Total {d['total']}: cash_merger {d['cash_merger']}, failure "
              f"{d['failure']}, unknown {d['unknown']}. Delisting return in the price path {d['delisting_return_in_path']}"
              f" ({_fmt(d['delisting_return_in_path'] / d['total']) if d['total'] else 'n/a'} of all); supplied "
              f"-100 percent {d['delisting_return_supplied_minus_100']}; missing (engine default) "
              f"{d['delisting_return_missing']}.", ""]
    p = report["price_path"]
    decades = ", ".join(f"{k}s {v}" for k, v in p["chain_mismatch_in_member_spell_by_decade"].items())
    lines += ["## Price Path (D3, R6)", "", f"- Rows whose `dlyprevdt` is not the previous valid row (a row with a "
              f"price but no return lies between; that return is not in the path): {p['chain_mismatch_rows']} rows, "
              f"{p['chain_mismatch_permnos']} PERMNOs, {p['chain_mismatch_in_member_spell']} inside a member spell (by "
              f"decade: {decades or 'none'}). `tilt_frames` marks these rows in `path_break`; the driver blanks each level window that "
              "holds one and reports each held position across one.",
              f"- Returns before the first priced row (not used): {p['unanchored_return_rows']}.",
              f"- Zero prices read as no price: {p['zero_price_rows']}.",
              f"- Member PERMNOs whose path ends before the vintage end without a delisting record: "
              f"{p['path_ends_early_without_delisting_record']} (last valued row by month: "
              f"{', '.join(f'{k} {v}' for k, v in p['path_ends_early_by_month'].items()) or 'none'}).", "",
              "## Signal Input Tables (D8)", "",
              "| Table | Rows | Dropped by reason |", "| --- | --- | --- |"]
    for name, v in report["signal_tables"].items():
        dropped = ", ".join(f"{k} {n}" for k, n in v["dropped"].items()) or "none"
        lines.append(f"| {name} | {v['rows']} | {dropped} |")
    by_year = ", ".join(f"{y} {n}" for y, n in report["ibes_non_usd_fy1_by_year"].items()) or "none"
    lines += ["", f"IBES FY1 rows with a currency other than USD, dropped before `signal_inputs` returns: "
              f"{report['signal_tables']['ibes']['dropped']['non_usd_fy1']} (by year: {by_year}).", ""]
    ba = report["bid_ask_member_days"]
    gaps = report["terminal_gap_events"]
    lines += ["## R4 Runs And Driver Columns", "",
              f"- Events in the `last_close` run: {report['last_close_events']} (primary {d['total']}). Events whose "
              f"effective row follows rows without a value: primary {gaps['primary']}, last_close "
              f"{gaps['last_close']}.",
              f"- Member-days with `dlyprcflg = '{BID_ASK_FLAG}'`: {ba['bid_ask']} of {ba['member_days']} "
              f"({_fmt(ba['bid_ask'] / ba['member_days']) if ba['member_days'] else 'n/a'}).", "",
              "## Share Counts For S7 And S8 (D5 On The Daily Signal Table)", "",
              "Member-days with a daily row; a positive raw daily `shrout` (the old input); a D5 share count (the new "
              "input); and the rows where ME and the share count are `unmapped` because the basis factor changed "
              "across a gap.", "", "| Year | Rows | Raw | D5 | Basis changed across a gap |", "| --- | --- | --- | --- | --- |"]
    lines += [f"| {y} | {v['rows']} | {v['raw']} | {v['d5']} | {v['basis_changed_across_gap']} |"
              for y, v in report["share_counts_by_year"].items()]
    total = {k: sum(v[k] for v in report["share_counts_by_year"].values())
             for k in ("rows", "raw", "d5", "basis_changed_across_gap")}
    lines += [f"| All | {total['rows']} | {total['raw']} | {total['d5']} | {total['basis_changed_across_gap']} |", ""]
    return "\n".join(lines)


# Tracked manifest -------------------------------------------------------------------------

def sealed_digest(root: Path) -> dict[str, Any]:
    """One SHA-256 over the bytes of every file under ``sealed/`` in path order; the files are not parsed."""
    folder = root / SEALED
    paths = sorted(p for p in folder.rglob("*") if p.is_file() and not p.name.startswith("."))
    digest = hashlib.sha256()
    for path in paths:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                digest.update(block)
    return {"files": len(paths), "sha256": digest.hexdigest()}


def write_manifest(data: WrdsData, path: str | Path) -> dict[str, Any]:
    """``reports/wrds_manifest_2025.json``: names, rows, and hashes only (no identifier, query text, or path)."""
    files = {name: {"rows": int(record["rows"]), "sha256": record["sha256"],
                    "query_sha256": hashlib.sha256(record["query"].encode()).hexdigest()}
             for name, record in sorted(data.manifest["files"].items())}
    out = {"vintage": data.manifest["vintage"], "script_code_sha256": data.manifest["code"], "files": files,
           "sealed": sealed_digest(data.root), "units": UNITS}
    Path(path).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the M5.5 WRDS intake checks and write the tracked manifest.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    data = load(args.root)
    args.report.write_text(intake_markdown(intake_report(data)))
    write_manifest(data, args.manifest)
    print("intake report and manifest written")


if __name__ == "__main__":
    main()
