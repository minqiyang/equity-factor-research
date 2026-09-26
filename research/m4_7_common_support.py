"""Common evaluation support for the M4.7 S&P 500 PIT rerun (plan section 4).

Pure functions over a discovery calendar, its scheduled reset rows, a bar
presence matrix ``B``, the engine-resolved universe ``M``
(``backtest.portfolio.resolve_pit_universe_mask``), and the engine event
table. Rows are integer positions on the calendar. Nothing here reads vendor
files or depends on a holding, signal, price value, or outcome, except the
labels of section 4.6, which read adjusted closes and signals by definition.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Mapping

import numpy as np
import pandas as pd

from backtest.portfolio import _prepare_terminal_events, resolve_pit_universe_mask
from features.diagnostics import factor_rank_information_coefficient


MIN_SEGMENT_ROWS = 42
MIN_IC_PAIRS = 100


@dataclass
class GapWindow:
    start: int
    end: int
    reasons: set[str] = field(default_factory=set)
    peeled_rows: int = 0


@dataclass(frozen=True)
class Segment:
    first: int
    last: int
    valid: bool

    @property
    def anchor(self) -> int:
        return self.first - 1

    @property
    def rows(self) -> int:
        return self.last - self.first + 1


@dataclass(frozen=True)
class SupportSchedule:
    reset_rows: np.ndarray
    d0: int
    d_last: int
    g_base: pd.DataFrame
    g_term: tuple[tuple[str, int], ...]
    windows: tuple[GapWindow, ...]
    segments: tuple[Segment, ...]
    excluded_rows: int
    excluded_fraction: float
    max_reset_to_reset_rows: int


def scheduled_reset_rows(calendar: pd.DatetimeIndex) -> np.ndarray:
    """Rows of ``R``: the last calendar row of each month (the engine's ``ME`` resets)."""
    months = pd.Series(calendar.to_period("M"))
    return np.flatnonzero(~months.duplicated(keep="last").to_numpy())


def signal_eligibility(mask: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    """``S_mask = E_sig & B`` with ``E_sig[t] = M[t + 1]`` and ``E_sig[N - 1] = False``."""
    _require_aligned(mask, bars)
    return mask.astype(bool).shift(-1, fill_value=False) & bars.astype(bool)


def holding_cells(mask: pd.DataFrame, reset_rows: np.ndarray, d_last: int) -> pd.DataFrame:
    """``H(a)``: ``[R_entry, R_exit]`` over each membership run of ``M`` with ``R_entry < R_exit``."""
    values = mask.to_numpy(dtype=bool)
    held = np.zeros_like(values)
    rows = len(values)
    for column in range(values.shape[1]):
        present = np.concatenate(([False], values[:, column], [False]))
        edges = np.flatnonzero(present[1:] != present[:-1])
        for m_in, m_out in zip(edges[::2], edges[1::2]):
            entry = _first_reset_at_or_after(reset_rows, m_in)
            exit_ = _first_reset_at_or_after(reset_rows, m_out) if m_out < rows else None
            exit_ = d_last if exit_ is None else exit_
            if entry is not None and entry < exit_:
                held[entry:exit_ + 1, column] = True
    return pd.DataFrame(held, index=mask.index, columns=mask.columns)


def base_exclusion_cells(
    bars: pd.DataFrame, mask: pd.DataFrame, reset_rows: np.ndarray, d_last: int,
) -> pd.DataFrame:
    """``G_base``: held cells between an asset's first and last bar whose bar is missing."""
    _require_aligned(mask, bars)
    present = bars.to_numpy(dtype=bool)
    seen = np.maximum.accumulate(present, axis=0)
    seen_later = np.maximum.accumulate(present[::-1], axis=0)[::-1]
    inside = seen & seen_later
    cells = holding_cells(mask, reset_rows, d_last).to_numpy(dtype=bool) & inside & ~present
    return pd.DataFrame(cells, index=bars.index, columns=bars.columns)


def gap_windows(
    g_base: pd.DataFrame, unresolved_rows: Mapping[str, int], reset_rows: np.ndarray,
    d0: int, d_last: int,
) -> list[GapWindow]:
    """Steps 1-2: one ``Gamma(m) = [m, R2(m) - 1]`` per missing run and ``U`` entry, merged."""
    starts: list[tuple[int, str]] = []
    values = g_base.to_numpy(dtype=bool)
    for column in range(values.shape[1]):
        present = np.concatenate(([False], values[:, column]))
        starts.extend((int(m), "missing_bar") for m in np.flatnonzero(present[1:] & ~present[:-1]))
    starts.extend(
        (int(row), "unresolved_delisting") for row in unresolved_rows.values() if d0 <= row <= d_last
    )
    windows = []
    for m, reason in starts:
        r2 = _first_reset_at_or_after(reset_rows, m + 1)
        windows.append(GapWindow(m, d_last if r2 is None else r2 - 1, {reason}))
    return [
        GapWindow(max(w.start, d0), min(w.end, d_last), w.reasons)
        for w in _merge(windows) if w.end >= d0 and w.start <= d_last
    ]


def peel_terminal_resets(
    windows: list[GapWindow], mask: pd.DataFrame, bars: pd.DataFrame, d0: int,
) -> tuple[list[GapWindow], tuple[tuple[str, int], ...]]:
    """Step 4: move a window's start to ``q`` while an asset is selectable at ``q`` without a bar.

    A peel changes only the segment that precedes its own window, so one pass
    in date order reaches the fixed point, and the ``q > p`` stop leaves at
    least one segment row, so no two windows become adjacent.
    """
    _require_aligned(mask, bars)
    selectable = mask.to_numpy(dtype=bool)
    present = bars.to_numpy(dtype=bool)
    assets = list(mask.columns)
    peeled = [GapWindow(w.start, w.end, set(w.reasons), w.peeled_rows) for w in windows]
    cells: list[tuple[str, int]] = []
    for position, window in enumerate(peeled):
        p = d0 if position == 0 else peeled[position - 1].end + 1
        q = window.start - 1
        while q > p:
            hits = np.flatnonzero(selectable[q] & present[q - 1] & ~present[q])
            if hits.size == 0:
                break
            cells.extend((assets[column], q) for column in hits)
            window.reasons.add("terminal_reset_missing_bar")
            window.peeled_rows += 1
            window.start = q
            q -= 1
    return peeled, tuple(cells)


def support_segments(
    windows: list[GapWindow], d0: int, d_last: int, *, min_rows: int = MIN_SEGMENT_ROWS,
) -> tuple[Segment, ...]:
    """Steps 3 and 5: maximal runs of ``[d0, d_last]`` outside ``W``; valid when ``q - p + 1 >= min_rows``."""
    segments = []
    cursor = d0
    for window in windows:
        if window.start > cursor:
            segments.append(Segment(cursor, window.start - 1, window.start - cursor >= min_rows))
        cursor = max(cursor, window.end + 1)
    if cursor <= d_last:
        segments.append(Segment(cursor, d_last, d_last - cursor + 1 >= min_rows))
    return tuple(segments)


def max_reset_to_reset_rows(reset_rows: np.ndarray, d0: int, d_last: int) -> int:
    inside = reset_rows[(reset_rows >= d0) & (reset_rows <= d_last)]
    if inside.size < 2:
        raise ValueError("max_reset_to_reset_rows requires two scheduled resets in [d0, d_last]")
    return int(np.diff(inside).max())


def common_support_schedule(
    calendar: pd.DatetimeIndex, bars: pd.DataFrame, mask: pd.DataFrame,
    unresolved_rows: Mapping[str, int], d0: int,
) -> SupportSchedule:
    """Sections 4.1-4.2 end to end: ``X``, ``W``, peeling, segments, and exclusions."""
    if not bars.index.equals(calendar):
        raise ValueError("bars must be indexed by the calendar")
    reset_rows = scheduled_reset_rows(calendar)
    if d0 not in set(reset_rows.tolist()):
        raise ValueError("d0 must be a scheduled reset row")
    d_last = int(reset_rows[-1])
    g_base = base_exclusion_cells(bars, mask, reset_rows, d_last)
    windows, g_term = peel_terminal_resets(
        gap_windows(g_base, unresolved_rows, reset_rows, d0, d_last), mask, bars, d0,
    )
    segments = support_segments(windows, d0, d_last)
    span = d_last - d0 + 1
    excluded = span - sum(segment.rows for segment in segments if segment.valid)
    return SupportSchedule(
        reset_rows=reset_rows, d0=d0, d_last=d_last, g_base=g_base, g_term=g_term,
        windows=tuple(windows), segments=segments, excluded_rows=excluded,
        excluded_fraction=excluded / span,
        max_reset_to_reset_rows=max_reset_to_reset_rows(reset_rows, d0, d_last),
    )


def ic_month_set(schedule: SupportSchedule) -> tuple[tuple[int, ...], dict[str, tuple[int, ...]]]:
    """``T_IC`` (fully measured holding periods) and the typed month-end exclusions."""
    included: list[int] = []
    excluded: dict[str, list[int]] = {
        "ic_month_in_gap": [], "ic_month_in_dropped_segment": [], "ic_month_horizon_unmeasured": [],
    }
    resets = schedule.reset_rows
    for position, r in enumerate(resets):
        if not schedule.d0 <= r <= schedule.d_last:
            continue
        following = int(resets[position + 1]) if position + 1 < len(resets) else None
        segment = next((s for s in schedule.segments if s.first <= r <= s.last), None)
        if segment is None:
            excluded["ic_month_in_gap"].append(int(r))
        elif not segment.valid:
            excluded["ic_month_in_dropped_segment"].append(int(r))
        elif r < segment.last and following is not None and following <= segment.last:
            included.append(int(r))
        else:
            excluded["ic_month_horizon_unmeasured"].append(int(r))
    return tuple(included), {reason: tuple(rows) for reason, rows in excluded.items()}


def reset_to_reset_labels(
    adjusted_close: pd.DataFrame, s_mask: pd.DataFrame, reset_rows: np.ndarray,
    label_resets: tuple[int, ...], engine_events: pd.DataFrame | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Terminal-aware labels keyed by the signal row ``t = r - 1`` (section 4.6).

    Returns the label frame (missing off label rows and outside ``Elig(r)``)
    and one record per reset date with ``eligible_count``, the terminal-aware
    label count, and the counts of the two typed guard reasons.
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
                  "missing_execution_bar": 0, "missing_horizon_end_bar": 0}
        for column in np.flatnonzero(eligible[t]):
            counts["eligible_count"] += 1
            event = events.get(adjusted_close.columns[column])
            if event is not None and e < event[0] <= h:
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


def _first_reset_at_or_after(reset_rows: np.ndarray, row: int) -> int | None:
    position = int(np.searchsorted(reset_rows, row, side="left"))
    return int(reset_rows[position]) if position < len(reset_rows) else None


def _merge(windows: list[GapWindow]) -> list[GapWindow]:
    merged: list[GapWindow] = []
    for window in sorted(windows, key=lambda w: (w.start, w.end)):
        if merged and window.start <= merged[-1].end + 1:
            last = merged[-1]
            last.end = max(last.end, window.end)
            last.reasons |= window.reasons
            last.peeled_rows += window.peeled_rows
        else:
            merged.append(GapWindow(window.start, window.end, set(window.reasons), window.peeled_rows))
    return merged


def _require_aligned(left: pd.DataFrame, right: pd.DataFrame) -> None:
    if not left.index.equals(right.index) or not left.columns.equals(right.columns):
        raise ValueError("panels must share index and columns")


# ---------------------------------------------------------------- snapshot wiring (stage a-2)
#
# The functions below read a snapshot in the Appendix A layout. They import the
# universe-build helpers lazily because that module imports the pure core above.


EXCLUSION_SET = "census/exclusion_set.json"
GAP_WINDOWS = "census/gap_windows.json"
SEGMENTS = "census/segments.json"


@dataclass(frozen=True)
class SnapshotSupport:
    """The support inputs read from a snapshot and the schedule derived from them."""

    calendar: pd.DatetimeIndex
    holdout_end: str
    intervals: pd.DataFrame
    events: pd.DataFrame
    bars: pd.DataFrame
    mask: pd.DataFrame
    unresolved: dict[str, int]
    schedule: SupportSchedule
    discovery_inputs_sha256: str

    def record(self) -> dict:
        """The ``census/segments.json`` body of Appendix A without its digests."""
        schedule, iso = self.schedule, [day.date().isoformat() for day in self.calendar]
        included, _ = ic_month_set(schedule)
        cell_rows = ([int(row) for row, _ in np.argwhere(schedule.g_base.to_numpy(dtype=bool))]
                     + [row for _, row in schedule.g_term] + list(self.unresolved_in_window().values()))
        windows = [{
            "start": iso[w.start], "end": iso[w.end], "reasons": sorted(w.reasons),
            "cell_count": sum(w.start <= row <= w.end for row in cell_rows), "peeled_rows": w.peeled_rows,
        } for w in schedule.windows]
        segments = [{
            "anchor": iso[s.anchor], "first_row": iso[s.first], "last_row": iso[s.last], "measured_rows": s.rows,
            "valid": s.valid, "drop_reason": None if s.valid else "segment_too_short",
        } for s in schedule.segments]
        return {
            "calendar_source": "GSPC.INDX_eod_dates_v1", "holdout_end": self.holdout_end,
            "D0": iso[schedule.d0], "D_last": iso[schedule.d_last], "D_end": iso[max(included)] if included else None,
            "max_reset_to_reset_rows": schedule.max_reset_to_reset_rows,
            "reset_rows_sha256": hashlib.sha256(_canonical([iso[r] for r in schedule.reset_rows])).hexdigest(),
            "gap_windows": windows, "segments": segments,
            "excluded_rows": schedule.excluded_rows, "excluded_fraction": schedule.excluded_fraction,
        }

    @property
    def segments_sha256(self) -> str:
        return hashlib.sha256(_canonical(self.record())).hexdigest()

    def unresolved_in_window(self) -> dict[str, int]:
        return {pid: row for pid, row in sorted(self.unresolved.items())
                if self.schedule.d0 <= row <= self.schedule.d_last}


def write_support_files(snapshot_dir) -> SnapshotSupport:
    """Wire the pure core to a snapshot and emit the three private support files (plan 4.1, 4.2).

    Bar presence comes from the panel files, the mask from
    ``resolve_pit_universe_mask``, and ``U`` from the delisting candidates
    without an engine event; the frame columns are the member permanent IDs
    with a discovery panel. Refuses ``derived_artifact_stale`` when the
    inventory, a panel file, or the terminal validation report no longer
    matches the current manifest (S7), and refuses
    ``derived_artifact_stale:terminal_events_engine_mismatch`` unless the
    engine event table is the projection of the current validation report. Writes ``census/exclusion_set.json``,
    ``census/gap_windows.json``, and ``census/segments.json``.
    """
    from data.constituent_table import load_constituent_intervals_csv
    from data.holdout_partition import SnapshotRefusal, sha256_bytes
    from research.m4_7_terminal_evidence import read_engine_events, require_current_terminal
    from research.m4_7_universe_build import (
        INTERVAL_CSV, INVENTORY, SECURITY_MASTER, Snapshot, _parquet, discovery_window, read_derived_json,
        require_current, write_bytes,
    )

    snapshot = Snapshot.open(snapshot_dir)
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
    support = snapshot_support(calendar, snapshot.holdout_end.isoformat(), intervals, read_engine_events(root), bars,
                               master, inputs, d0 - i_h)
    schedule = support.schedule
    iso = [day.date().isoformat() for day in support.calendar]
    columns = list(schedule.g_base.columns)
    base = sorted(np.argwhere(schedule.g_base.to_numpy(dtype=bool)).tolist(), key=lambda rc: (columns[rc[1]], rc[0]))
    record = support.record()
    exclusion = {
        "discovery_inputs_sha256": support.discovery_inputs_sha256,
        "g_base": [[columns[column], iso[row]] for row, column in base],
        "g_term": [[pid, iso[row]] for pid, row in schedule.g_term],
        "unresolved": [[pid, iso[row]] for pid, row in support.unresolved_in_window().items()],
    }
    write_bytes(root / EXCLUSION_SET, _canonical(exclusion))
    write_bytes(root / GAP_WINDOWS, _canonical({"discovery_inputs_sha256": support.discovery_inputs_sha256,
                                                "gap_windows": record["gap_windows"]}))
    write_bytes(root / SEGMENTS, _canonical({**record, "discovery_inputs_sha256": support.discovery_inputs_sha256,
                                             "segments_sha256": support.segments_sha256}))
    return support


def snapshot_support(
    calendar: pd.DatetimeIndex, holdout_end: str, intervals: pd.DataFrame, events: pd.DataFrame,
    bars: pd.DataFrame, master: pd.DataFrame, inputs: str, d0: int,
) -> SnapshotSupport:
    """The schedule of sections 4.1-4.2 from a bar-presence matrix whose columns are the member permanent IDs.

    The mask comes from ``resolve_pit_universe_mask`` over the member events
    and ``U`` from the delisting candidates without an engine event. The
    census passes bars read from the panel files; the runner passes the
    loaded panel's missing-value pattern (plan 4.5).
    """
    assets = list(bars.columns)
    events = events[events["permanent_id"].isin(assets)].reset_index(drop=True)
    if assets:
        mask = resolve_pit_universe_mask(intervals[intervals["permanent_id"].isin(assets)],
                                         events if len(events) else None, calendar, assets)
    else:
        mask = bars.copy()
    settled = set(events["permanent_id"])
    unresolved = {
        row["permanent_id"]: int(calendar.get_loc(pd.Timestamp(row["last_bar"]))) + 1
        for row in master.to_dict(orient="records")
        if row["permanent_id"] in assets and row["has_delisting_candidate_interval"] == "True"
        and row["permanent_id"] not in settled
    }
    schedule = common_support_schedule(calendar, bars, mask, unresolved, d0)
    return SnapshotSupport(calendar, holdout_end, intervals, events, bars, mask, unresolved, schedule, inputs)


def _canonical(payload) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
