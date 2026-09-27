"""Evaluation support for the S&P 500 PIT reruns: support v2 (M4.7) and the causal mask v3 (M4.8).

Pure functions over a discovery calendar, its scheduled reset rows, a bar
presence matrix ``B``, the engine-resolved universe ``M``
(``backtest.portfolio.resolve_pit_universe_mask``), and the settled terminal
rows. Rows are integer positions on the calendar. A missing bar or an
unevidenced disappearance excludes only the affected asset from the reset whose
holding period needs that bar; every other asset, row, and month stays in the
single evaluation window ``[d0, d_last]``. Nothing here reads vendor files or
depends on a holding, signal, price value, or outcome, except the labels of
section 4.6, which read adjusted closes and signals by definition.

Registration v3 (M4.8 plan 4.1, 4.2, 4.6, 4.8) retires the exclusion cells:
``causal_support_schedule`` sets ``E(r - 1) = S_mask(r - 1)`` and reads no bar
after the signal row. Missing labels are typed, ``potentially_held`` builds the
factor-independent superset ``P_r``, and ``residual_disappearances`` lists the
held-possible stops without an accepted settlement. ``support_exclusions``
serves registration v2 only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd

from backtest.portfolio import _prepare_terminal_events, resolve_pit_universe_mask
from features.diagnostics import factor_rank_information_coefficient


SUPPORT_CONTRACT = "asset_level_holding_period_support_exclusion_v1"
CAUSAL_SUPPORT_CONTRACT = "causal_signal_eligibility_mask_v3"
RESIDUAL_BOUND_CASE = "residual_disappearance_minus_100pct_bound_v1"
MIN_IC_PAIRS = 100
MISSING_EXECUTION_HALT = "missing_execution_bar:halt"
MISSING_HORIZON_HALT = "missing_horizon_end_bar:halt"
MISSING_HORIZON_DISAPPEARANCE = "missing_horizon_end_bar:unresolved_disappearance"
TYPED_LABEL_REASONS = (MISSING_EXECUTION_HALT, MISSING_HORIZON_HALT, MISSING_HORIZON_DISAPPEARANCE)


@dataclass(frozen=True)
class SupportSchedule:
    """The evaluation window, ``S_mask``, and the asset-level exclusion cells ``X`` at signal rows ``r - 1``."""

    reset_rows: np.ndarray
    d0: int
    d_last: int
    s_mask: pd.DataFrame
    exclusions: pd.DataFrame
    reasons: tuple[tuple[str, int, str], ...]
    max_reset_to_reset_rows: int

    @property
    def evaluation_resets(self) -> np.ndarray:
        return self.reset_rows[(self.reset_rows >= self.d0) & (self.reset_rows <= self.d_last)]

    @property
    def evaluation_mask(self) -> pd.DataFrame:
        """``E = S_mask & ~X``: the cells that IC pairs, labels, books, and benchmarks read."""
        return self.s_mask & ~self.exclusions

    def breadth(self) -> pd.DataFrame:
        """Per evaluation reset: signal-eligible, support-excluded, and evaluated asset counts."""
        rows = self.evaluation_resets - 1
        eligible = self.s_mask.to_numpy(dtype=bool)[rows].sum(axis=1)
        excluded = self.exclusions.to_numpy(dtype=bool)[rows].sum(axis=1)
        return pd.DataFrame({"signal_eligible": eligible, "support_excluded": excluded,
                             "evaluated": eligible - excluded},
                            index=pd.Index(self.s_mask.index[self.evaluation_resets], name="reset_date"))

    @property
    def excluded_fraction(self) -> float:
        breadth = self.breadth()
        eligible = int(breadth["signal_eligible"].sum())
        return int(breadth["support_excluded"].sum()) / eligible if eligible else 0.0


def scheduled_reset_rows(calendar: pd.DatetimeIndex) -> np.ndarray:
    """Rows of ``R``: the last calendar row of each month (the engine's ``ME`` resets)."""
    months = pd.Series(calendar.to_period("M"))
    return np.flatnonzero(~months.duplicated(keep="last").to_numpy())


def signal_eligibility(mask: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    """``S_mask = E_sig & B`` with ``E_sig[t] = M[t + 1]`` and ``E_sig[N - 1] = False``."""
    _require_aligned(mask, bars)
    return mask.astype(bool).shift(-1, fill_value=False) & bars.astype(bool)


def support_exclusions(
    s_mask: pd.DataFrame, bars: pd.DataFrame, reset_rows: np.ndarray, d0: int, d_last: int,
    settled_rows: Mapping[str, int], unresolved_rows: Mapping[str, int],
) -> tuple[pd.DataFrame, tuple[tuple[str, int, str], ...]]:
    """``X``: signal-eligible cells ``(r - 1, i)`` whose holding period lacks a bar of ``i``.

    The holding period of reset ``r`` runs from its execution row ``r`` through
    the next scheduled reset ``h`` (``r`` itself at the last reset), where the
    engine sells. It ends at ``e - 1`` when ``i`` settles a terminal event at a
    row ``e`` in ``(r, h]``, because the engine pays the terminal return at
    ``e``. The reason is ``unresolved_delisting`` when ``i``'s disappearance
    row in ``U`` falls inside the period and ``missing_bar`` otherwise.
    """
    _require_aligned(s_mask, bars)
    eligible = s_mask.to_numpy(dtype=bool)
    present = bars.to_numpy(dtype=bool)
    assets = list(bars.columns)
    settled = np.array([settled_rows.get(asset, -1) for asset in assets], dtype=int)
    lost = np.array([unresolved_rows.get(asset, -1) for asset in assets], dtype=int)
    excluded = np.zeros_like(present)
    reasons: list[tuple[str, int, str]] = []
    resets = reset_rows[(reset_rows >= d0) & (reset_rows <= d_last)]
    for position, r in enumerate(resets.tolist()):
        h = int(resets[position + 1]) if position + 1 < len(resets) else r
        end = np.where((settled > r) & (settled <= h), settled - 1, h)
        missing = ~present[r:h + 1] & (np.arange(r, h + 1)[:, None] <= end[None, :])
        for column in np.flatnonzero(eligible[r - 1] & missing.any(axis=0)):
            excluded[r - 1, column] = True
            reason = "unresolved_delisting" if r <= lost[column] <= end[column] else "missing_bar"
            reasons.append((assets[column], r, reason))
    return pd.DataFrame(excluded, index=bars.index, columns=bars.columns), tuple(reasons)


def max_reset_to_reset_rows(reset_rows: np.ndarray, d0: int, d_last: int) -> int:
    inside = reset_rows[(reset_rows >= d0) & (reset_rows <= d_last)]
    if inside.size < 2:
        raise ValueError("max_reset_to_reset_rows requires two scheduled resets in [d0, d_last]")
    return int(np.diff(inside).max())


def common_support_schedule(
    calendar: pd.DatetimeIndex, bars: pd.DataFrame, mask: pd.DataFrame,
    unresolved_rows: Mapping[str, int], d0: int, settled_rows: Mapping[str, int] | None = None,
) -> SupportSchedule:
    """Sections 4.1-4.2 under support v2: one window ``[d0, d_last]`` and the asset-level cells ``X``."""
    if not bars.index.equals(calendar):
        raise ValueError("bars must be indexed by the calendar")
    reset_rows = scheduled_reset_rows(calendar)
    if d0 < 1 or d0 not in set(reset_rows.tolist()):
        raise ValueError("d0 must be a scheduled reset row after the first calendar row")
    d_last = int(reset_rows[-1])
    s_mask = signal_eligibility(mask, bars)
    exclusions, reasons = support_exclusions(s_mask, bars, reset_rows, d0, d_last, settled_rows or {},
                                             unresolved_rows)
    return SupportSchedule(
        reset_rows=reset_rows, d0=d0, d_last=d_last, s_mask=s_mask, exclusions=exclusions, reasons=reasons,
        max_reset_to_reset_rows=max_reset_to_reset_rows(reset_rows, d0, d_last),
    )


def causal_support_schedule(
    calendar: pd.DatetimeIndex, bars: pd.DataFrame, mask: pd.DataFrame, d0: int,
) -> SupportSchedule:
    """``causal_signal_eligibility_mask_v3``: ``E(r - 1) = S_mask(r - 1)`` over ``[d0, d_last]`` (M4.8 plan 4.1).

    ``d_last`` is the calendar's last scheduled reset, so a segment calendar
    ending at its last book row gives that row. No cell reads a bar dated after
    its signal row; ``exclusions`` is empty.
    """
    if not bars.index.equals(calendar):
        raise ValueError("bars must be indexed by the calendar")
    reset_rows = scheduled_reset_rows(calendar)
    if d0 < 1 or d0 not in set(reset_rows.tolist()):
        raise ValueError("d0 must be a scheduled reset row after the first calendar row")
    d_last = int(reset_rows[-1])
    s_mask = signal_eligibility(mask, bars)
    return SupportSchedule(
        reset_rows=reset_rows, d0=d0, d_last=d_last, s_mask=s_mask,
        exclusions=pd.DataFrame(False, index=bars.index, columns=bars.columns), reasons=(),
        max_reset_to_reset_rows=max_reset_to_reset_rows(reset_rows, d0, d_last),
    )


def potentially_held(schedule: SupportSchedule, bars: pd.DataFrame) -> dict[int, np.ndarray]:
    """``P_r = S_mask(r - 1) | {a in P_prev(r) : no close at r}`` per evaluation reset (M4.8 plan 4.6).

    ``P_prev`` is empty at the first reset. The set depends on no factor, so it
    covers every book and the equal-weight benchmark, including locks carried
    under H-3.
    """
    _require_aligned(schedule.s_mask, bars)
    eligible, present = schedule.s_mask.to_numpy(dtype=bool), bars.to_numpy(dtype=bool)
    sets: dict[int, np.ndarray] = {}
    previous = np.zeros(len(bars.columns), dtype=bool)
    for r in schedule.evaluation_resets.tolist():
        previous = eligible[r - 1] | (previous & ~present[r])
        sets[int(r)] = previous
    return sets


def residual_disappearances(
    schedule: SupportSchedule, bars: pd.DataFrame, accepted: set[str] | frozenset[str],
    candidates: Mapping[str, int],
) -> tuple[tuple[str, int, int], ...]:
    """``census_zero_residual_v2`` parts 1 and 2: ``(permanent_id, stop_row, reset_row)`` sorted (M4.8 plan 4.6).

    A stop at row ``s`` belongs to the window ``(r, h(r)]`` of consecutive
    evaluation resets. Part 1 takes each candidate settlement row in
    ``(d0, d_last]``; part 2 takes each asset whose last bar ``l < d_last``
    leaves it without a bar through the last book row (``s = l + 1``). A stop
    is residual when its asset lies in ``P_r`` of that window and has no
    accepted settlement.
    """
    held = potentially_held(schedule, bars)
    resets = schedule.evaluation_resets.tolist()
    present = bars.to_numpy(dtype=bool)[: schedule.d_last + 1]
    stops: set[tuple[str, int]] = {(pid, int(row)) for pid, row in candidates.items()
                                   if pid in bars.columns and schedule.d0 < row <= schedule.d_last}
    for column, pid in enumerate(bars.columns):
        rows = np.flatnonzero(present[:, column])
        if rows.size and rows[-1] < schedule.d_last:
            stops.add((pid, int(rows[-1]) + 1))
    residual = []
    for pid, stop in sorted(stops):
        window = [r for r, h in zip(resets, resets[1:]) if r < stop <= h]
        if window and pid not in accepted and held[window[0]][bars.columns.get_loc(pid)]:
            residual.append((pid, stop, window[0]))
    return tuple(residual)


def claim_demand(validation_rows: list[dict], residual: tuple[tuple[str, int, int], ...]) -> dict[str, object]:
    """Claim demand (M4.8 plan 3.6): residual candidates whose only failures are projection-pass timing bounds."""
    timing_only = {row["permanent_id"] for row in validation_rows
                   if row.get("terms_pass") == "terms_valid" and row.get("timing_failures")}
    demand = len({pid for pid, _, _ in residual} & timing_only)
    return {"claim_demand": demand,
            "claim_contract": "claim_not_built:no_consumer" if demand == 0 else "stage_e2_required"}


def residual_bound_events(residual: tuple[tuple[str, int, int], ...], calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """``residual_disappearance_minus_100pct_bound_v1``: each residual stop settles at ``rho = -1`` at its row (4.8)."""
    rows = [{"event_id": f"RB-{pid}-{calendar[stop].date().isoformat()}", "permanent_id": pid,
             "effective_date": calendar[stop], "known_at": calendar[stop - 1], "reference_date": calendar[stop - 1],
             "terminal_return": -1.0, "return_basis": "prior_observed_close_to_cash"} for pid, stop, _ in residual]
    return pd.DataFrame(rows, columns=["event_id", "permanent_id", "effective_date", "known_at", "reference_date",
                                       "terminal_return", "return_basis"])


def ic_month_set(schedule: SupportSchedule) -> tuple[tuple[int, ...], dict[str, tuple[int, ...]]]:
    """``T_IC``: every evaluation reset with a following reset; the last reset's horizon is unmeasured."""
    resets = [int(r) for r in schedule.evaluation_resets]
    return tuple(resets[:-1]), {"ic_month_horizon_unmeasured": tuple(resets[-1:])}


def reset_to_reset_labels(
    adjusted_close: pd.DataFrame, s_mask: pd.DataFrame, reset_rows: np.ndarray,
    label_resets: tuple[int, ...], engine_events: pd.DataFrame | None, *, typed: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Terminal-aware labels keyed by the signal row ``t = r - 1`` (section 4.6).

    Returns the label frame (missing off label rows and outside ``Elig(r)``)
    and one record per reset date with ``eligible_count``, the terminal-aware
    label count, and the counts of the two typed guard reasons. With ``typed``
    (registration v3, M4.8 plan 4.2) a missing execution bar is checked first
    and the counts are ``TYPED_LABEL_REASONS``: a missing horizon bar is a halt
    when the asset has a later bar in the panel and an unresolved
    disappearance otherwise.
    """
    _require_aligned(s_mask, adjusted_close)
    calendar = pd.DatetimeIndex(adjusted_close.index)
    prices = adjusted_close.to_numpy(dtype=float)
    eligible = s_mask.to_numpy(dtype=bool)
    events = {
        record["permanent_id"]: (
            int(calendar.get_loc(effective)), int(calendar.get_loc(record["reference_date"])),
            record["terminal_return"],
        )
        for effective, records in _prepare_terminal_events(engine_events, calendar, adjusted_close.columns).items()
        for record in records
    }
    labels = np.full(prices.shape, np.nan)
    records = []
    for r in label_resets:
        following = reset_rows[reset_rows > r]
        if following.size == 0:
            raise ValueError("every label reset needs a following scheduled reset")
        t, e, h = r - 1, r, int(following[0])
        counts = {"eligible_count": 0, "terminal_aware_labels": 0,
                  **dict.fromkeys(TYPED_LABEL_REASONS if typed else ("missing_execution_bar",
                                                                     "missing_horizon_end_bar"), 0)}
        for column in np.flatnonzero(eligible[t]):
            counts["eligible_count"] += 1
            event = events.get(adjusted_close.columns[column])
            if typed and not np.isfinite(prices[e, column]):
                counts[MISSING_EXECUTION_HALT] += 1
            elif typed and not (event is not None and e < event[0] <= h) and not np.isfinite(prices[h, column]):
                later = np.isfinite(prices[h + 1:, column]).any()
                counts[MISSING_HORIZON_HALT if later else MISSING_HORIZON_DISAPPEARANCE] += 1
            elif event is not None and e < event[0] <= h:
                labels[t, column] = prices[event[1], column] / prices[e, column] * (1.0 + event[2]) - 1.0
                counts["terminal_aware_labels"] += 1
            elif np.isfinite(prices[e, column]) and np.isfinite(prices[h, column]):
                labels[t, column] = prices[h, column] / prices[e, column] - 1.0
            elif not np.isfinite(prices[e, column]):
                counts["missing_execution_bar"] += 1
            else:
                counts["missing_horizon_end_bar"] += 1
        records.append({"reset_date": calendar[r], "signal_date": calendar[t], **counts})
    return (
        pd.DataFrame(labels, index=calendar, columns=adjusted_close.columns),
        pd.DataFrame(records).set_index("reset_date"),
    )


def monthly_rank_ic(
    signal: pd.DataFrame, labels: pd.DataFrame, label_resets: tuple[int, ...],
    *, min_pairs: int = MIN_IC_PAIRS,
) -> pd.DataFrame:
    """Rank IC at each reset from the signal and label rows ``t = r - 1``, with typed validity."""
    _require_aligned(signal, labels)
    rows = [r - 1 for r in label_resets]
    pairs = (signal.notna() & labels.notna()).iloc[rows].sum(axis=1)
    ic = factor_rank_information_coefficient(
        signal.iloc[rows], labels.iloc[rows], min_periods=min_pairs,
    )
    status = np.where(
        pairs < min_pairs, "ic_month_invalid:insufficient_pairs",
        np.where(ic.notna(), "valid", "ic_month_invalid:undefined_rank_ic"),
    )
    return pd.DataFrame({
        "reset_date": signal.index[list(label_resets)],
        "finite_pair_count": pairs.to_numpy(dtype=int),
        "rank_ic": ic.to_numpy(dtype=float),
        "status": status,
    }, index=pd.Index(signal.index[rows], name="signal_date"))


def _require_aligned(left: pd.DataFrame, right: pd.DataFrame) -> None:
    if not left.index.equals(right.index) or not left.columns.equals(right.columns):
        raise ValueError("panels must share index and columns")


# ---------------------------------------------------------------- snapshot wiring (stage a-2)
#
# The functions below read a snapshot in the Appendix A layout. They import the
# universe-build helpers lazily because that module imports the pure core above.


SUPPORT_FILE = "census/asset_support.json"


@dataclass(frozen=True)
class SnapshotSupport:
    """The support inputs read from a snapshot and the schedule derived from them."""

    calendar: pd.DatetimeIndex
    holdout_end: str
    calendar_source: str
    intervals: pd.DataFrame
    events: pd.DataFrame
    bars: pd.DataFrame
    mask: pd.DataFrame
    unresolved: dict[str, int]
    schedule: SupportSchedule
    discovery_inputs_sha256: str

    def record(self) -> dict:
        """The private ``census/asset_support.json`` body without its digests.

        ``exclusions`` lists ``[permanent_id, reset date, reason]`` per cell of
        ``X``; the file stays inside the snapshot (R11). Every other field is a
        count or a date.
        """
        schedule, iso = self.schedule, [day.date().isoformat() for day in self.calendar]
        included, _ = ic_month_set(schedule)
        breadth = schedule.breadth()
        reasons = pd.Series([reason for _, _, reason in schedule.reasons], dtype=object)
        return {
            "support_contract": SUPPORT_CONTRACT, "calendar_source": self.calendar_source,
            "holdout_end": self.holdout_end, "D0": iso[schedule.d0], "D_last": iso[schedule.d_last],
            "D_end": iso[max(included)] if included else None,
            "max_reset_to_reset_rows": schedule.max_reset_to_reset_rows,
            "reset_rows_sha256": hashlib.sha256(_canonical([iso[r] for r in schedule.reset_rows])).hexdigest(),
            "evaluation_resets": len(schedule.evaluation_resets), "ic_month_supply": len(included),
            "signal_eligible_cells": int(breadth["signal_eligible"].sum()),
            "excluded_cells": int(breadth["support_excluded"].sum()),
            "excluded_fraction": schedule.excluded_fraction,
            "excluded_cells_by_reason": {str(k): int(v) for k, v in sorted(reasons.value_counts().items())},
            "unresolved_in_window": len(self.unresolved_in_window()),
            "breadth": [{"reset_date": day.date().isoformat(), **{k: int(v) for k, v in row.items()}}
                        for day, row in breadth.iterrows()],
            "exclusions": [[pid, iso[row], reason] for pid, row, reason in sorted(schedule.reasons)],
        }

    @property
    def support_sha256(self) -> str:
        return hashlib.sha256(_canonical(self.record())).hexdigest()

    def unresolved_in_window(self) -> dict[str, int]:
        return {pid: row for pid, row in sorted(self.unresolved.items())
                if self.schedule.d0 <= row <= self.schedule.d_last}


def write_support_files(snapshot_dir) -> SnapshotSupport:
    """Wire the pure core to a snapshot and emit the private support file (plan 4.1, 4.2, support v2).

    Bar presence comes from the panel files, the mask from
    ``resolve_pit_universe_mask``, and ``U`` from the delisting candidates
    without an engine event; the frame columns are the member permanent IDs
    with a discovery panel. Refuses ``derived_artifact_stale`` when the
    inventory, a panel file, or the terminal validation report no longer
    matches the current manifest (S7), and refuses
    ``derived_artifact_stale:terminal_events_engine_mismatch`` unless the
    engine event table is the projection of the current validation report.
    Writes ``census/asset_support.json``. A rule v2 snapshot goes to
    ``write_support_files_v3``.
    """
    from data.constituent_table import load_constituent_intervals_csv
    from data.holdout_partition import PARTITION_RULE_V1, SnapshotRefusal, sha256_bytes
    from research.m4_7_terminal_evidence import read_engine_events, require_current_terminal
    from research.m4_7_universe_build import (
        INTERVAL_CSV, INVENTORY, SECURITY_MASTER, Snapshot, _parquet, discovery_window, read_derived_json,
        require_current, write_bytes,
    )

    snapshot = Snapshot.open(snapshot_dir)
    if snapshot.partition_rule != PARTITION_RULE_V1:
        return write_support_files_v3(snapshot)
    root = snapshot.root
    inventory = read_derived_json(root, INVENTORY)
    inputs = require_current(snapshot, inventory.get("discovery_inputs_sha256"), INVENTORY)
    require_current_terminal(snapshot)
    full = snapshot.calendar()
    i_h, d0, d_last = discovery_window(full, snapshot.holdout_end)
    if d0 > d_last:
        raise SnapshotRefusal("discovery_window_undefined", "no scheduled reset after the warm-up rows")
    calendar = full[i_h:]
    intervals = load_constituent_intervals_csv(root / INTERVAL_CSV).data
    files = {record["symbol"]: record for record in inventory["files"]}
    assets = sorted(set(intervals["permanent_id"]) & set(files))
    bars = pd.DataFrame(False, index=calendar, columns=pd.Index(assets, dtype=object))
    for pid in assets:
        payload = (root / "panel" / files[pid]["file"]).read_bytes()
        if sha256_bytes(payload) != files[pid]["sha256"]:
            raise SnapshotRefusal("derived_artifact_stale", f"panel {pid}")
        frame = _parquet(payload, files[pid]["file"], columns=["date", "adjusted_close"])
        present = pd.DatetimeIndex(frame.loc[np.isfinite(frame["adjusted_close"]), "date"])
        bars.loc[present.intersection(calendar), pid] = True
    master = pd.read_csv(root / SECURITY_MASTER, dtype=str, keep_default_na=False)
    support = snapshot_support(calendar, snapshot.holdout_end.isoformat(), snapshot.calendar_source, intervals,
                               read_engine_events(root), bars, master, inputs, d0 - i_h)
    write_bytes(root / SUPPORT_FILE, _canonical({**support.record(), "discovery_inputs_sha256": inputs,
                                                 "support_sha256": support.support_sha256}))
    return support


SUPPORT_FILE_V3 = "census/asset_support_v3.json"


def segment_bars(root, inventory: dict, side: str, pids: list[str], calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """Bar presence on one segment's calendar from that side's panel files only, hash-checked (SL-1, S7)."""
    from data.holdout_partition import SnapshotRefusal, sha256_bytes
    from research.m4_7_universe_build import _parquet

    files = {record["symbol"]: record for record in inventory["files"] if record.get("side") == side}
    bars = pd.DataFrame(False, index=calendar, columns=pd.Index(pids, dtype=object))
    for pid in pids:
        payload = (root / "panel" / files[pid]["file"]).read_bytes()
        if sha256_bytes(payload) != files[pid]["sha256"]:
            raise SnapshotRefusal("derived_artifact_stale", f"panel {files[pid]['file']}")
        frame = _parquet(payload, files[pid]["file"], columns=["date", "adjusted_close"])
        present = pd.DatetimeIndex(frame.loc[np.isfinite(frame["adjusted_close"]), "date"])
        bars.loc[present.intersection(calendar), pid] = True
    return bars


def write_support_files_v3(snapshot) -> dict:
    """Rule v2 support per segment (M4.8 plan 4.1, 4.6, 3.6); writes the private ``census/asset_support_v3.json``.

    Each segment reads only its side's panel files on rows
    ``[feature_floor_row, last_book_row]``: the causal schedule, ``P_r`` cell
    counts, and the residual over ``P_r``. Claim demand comes from the current
    validation report, and ``terminal_summary`` is the census v3 input in the
    approved public vocabulary.
    """
    from data.constituent_table import load_constituent_intervals_csv
    from data.holdout_partition import SnapshotRefusal
    from research.m4_7_terminal_evidence import read_engine_events, require_current_terminal, snapshot_segments, \
        terminal_summary
    from research.m4_7_universe_build import INTERVAL_CSV, INVENTORY, SECURITY_MASTER, read_derived_json, \
        require_current, write_bytes

    root = snapshot.root
    inventory = read_derived_json(root, INVENTORY)
    inputs = require_current(snapshot, inventory.get("discovery_inputs_sha256"), INVENTORY)
    report, _ = require_current_terminal(snapshot)
    if report.get("schema_version") != "m4_8_terminal_validation_v3":
        raise SnapshotRefusal("terminal_validation_schema_mismatch", "rule v2 support needs the schema v3 report")
    full = snapshot.calendar()
    intervals = load_constituent_intervals_csv(root / INTERVAL_CSV).data
    master = pd.read_csv(root / SECURITY_MASTER, dtype=str, keep_default_na=False)
    events = read_engine_events(root)
    segments, residual_all, record = snapshot_segments(snapshot, full), [], {}
    for segment in segments:
        calendar = full[segment.feature_floor_row:segment.last_book_row + 1]
        side_pids = {r["symbol"] for r in inventory["files"] if r.get("side") == segment.side}
        pids = sorted(set(intervals["permanent_id"]) & side_pids)
        bars = segment_bars(root, inventory, segment.side, pids, calendar)
        own = events[events["permanent_id"].isin(pids) & events["effective_date"].isin(calendar)].reset_index(drop=True)
        mask = (resolve_pit_universe_mask(intervals[intervals["permanent_id"].isin(pids)], own if len(own) else None,
                                          calendar, pids) if pids else bars.copy())
        schedule = causal_support_schedule(calendar, bars, mask, segment.first_reset_row - segment.feature_floor_row)
        last_bars = {row["permanent_id"]: pd.Timestamp(row["last_bar"]) for row in master.to_dict(orient="records")
                     if row["permanent_id"] in pids and row["has_delisting_candidate_interval"] == "True"}
        candidates = {pid: int(calendar.get_loc(day)) + 1 for pid, day in last_bars.items() if day in calendar}
        residual = residual_disappearances(schedule, bars, set(own["permanent_id"]), candidates)
        residual_all.extend(residual)
        iso = [day.date().isoformat() for day in calendar]
        included, _ = ic_month_set(schedule)
        record[segment.segment_id] = {
            "side": segment.side, "D0": iso[schedule.d0], "D_last": iso[schedule.d_last],
            "ic_month_supply": len(included), "max_reset_to_reset_rows": schedule.max_reset_to_reset_rows,
            "member_columns": len(pids),
            "potentially_held_cells": int(sum(int(v.sum()) for v in potentially_held(schedule, bars).values())),
            "residual_count": len(residual),
            "residual": [[pid, iso[stop], iso[reset]] for pid, stop, reset in residual],
            "panel_sides_opened": [segment.side] if pids else [],
        }
    claim = claim_demand(report["rows"], tuple(residual_all))
    body = {"support_contract": CAUSAL_SUPPORT_CONTRACT, "partition_rule": snapshot.partition_rule,
            "segments": record, "claim": claim,
            "terminal_summary": terminal_summary(report, len(residual_all), claim)}
    digest = hashlib.sha256(_canonical(body)).hexdigest()
    write_bytes(root / SUPPORT_FILE_V3, _canonical({**body, "discovery_inputs_sha256": inputs, "support_sha256": digest}))
    return {**body, "support_sha256": digest}


def snapshot_support(
    calendar: pd.DatetimeIndex, holdout_end: str, calendar_source: str, intervals: pd.DataFrame,
    events: pd.DataFrame, bars: pd.DataFrame, master: pd.DataFrame, inputs: str, d0: int,
) -> SnapshotSupport:
    """The support schedule from a bar-presence matrix whose columns are the member permanent IDs.

    The mask comes from ``resolve_pit_universe_mask`` over the member events,
    the settled rows from the engine events, and ``U`` from the delisting
    candidates without an engine event. The census passes bars read from the
    panel files; the runner passes the loaded panel's missing-value pattern
    (plan 4.5).
    """
    assets = list(bars.columns)
    events = events[events["permanent_id"].isin(assets)].reset_index(drop=True)
    if assets:
        mask = resolve_pit_universe_mask(intervals[intervals["permanent_id"].isin(assets)],
                                         events if len(events) else None, calendar, assets)
    else:
        mask = bars.copy()
    settled = {row["permanent_id"]: int(calendar.get_loc(pd.Timestamp(row["effective_date"])))
               for row in events.to_dict(orient="records")}
    unresolved = {
        row["permanent_id"]: int(calendar.get_loc(pd.Timestamp(row["last_bar"]))) + 1
        for row in master.to_dict(orient="records")
        if row["permanent_id"] in assets and row["has_delisting_candidate_interval"] == "True"
        and row["permanent_id"] not in settled
    }
    schedule = common_support_schedule(calendar, bars, mask, unresolved, d0, settled)
    return SnapshotSupport(calendar, holdout_end, calendar_source, intervals, events, bars, mask, unresolved, schedule,
                           inputs)


def _canonical(payload) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
