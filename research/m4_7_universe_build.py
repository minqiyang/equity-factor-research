"""Point-in-time S&P 500 universe build for M4.7 (plan sections 1.5, 1.6, 2).

Reads a private snapshot in the Appendix A layout through manifest roles with
SHA-256 verification (S7) and writes the security master, the per-entry
interval results, the M4.4 interval CSV, one discovery panel per permanent ID
with a ``split_factor`` column, the panel inventory, and the build manifest.

Bar dates come only from ``dates/<CODE>.US.parquet`` through
``read_bar_dates``; price values, split rows, and dividend rows come only from
discovery partitions. No holdout partition, quarantine file, or raw vendor
response is opened. Every refusal is typed and counted; nothing is filled,
clipped, or repaired (R6).

A rule v2 snapshot (M4.8 plan 2.2, 2.5, 2.7) has two discovery sides around the
carried seal. Every value-reading check runs on one side (SL-1): the pre side
anchors seal-touching codes at their last pre-side bar (SL-2, SL-3), seal gaps
split identity (SL-4, SL-5), the benchmark follows the same rules (SL-6), and
per-ID panels are written per side. The curated membership supplement joins
the vendor table (M-1..M-7), and the build takes ``D0_pre`` from the membership
census to fix the two discovery segments.

Run as ``python -m research.m4_7_universe_build --snapshot-id <ID> [--d0-pre YYYY-MM-DD]``.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import shutil
import sys
import urllib.parse
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from data.constituent_table import build_pit_membership_mask, load_constituent_intervals_csv
from data.holdout_partition import (
    PARTITION_RULE_V1,
    PARTITION_RULE_V2,
    SEAL_FILE,
    SIDES,
    SnapshotRefusal,
    classify_membership_entries,
    declared_partition_rule,
    parse_strict_date,
    read_authorized_bytes,
    read_manifest,
    read_partition_window,
    sha256_bytes,
)
from data.parquet_loader import compute_cumulative_split_factor, load_symbol_splits
from research import m4_8_membership
from research.m4_7_common_support import scheduled_reset_rows


DATA_DIR_ENV = "EFR_EODHD_DATA_DIR"
BENCHMARK = "SPY.US"
TABLES = ("splits", "eod", "dividends")
E1_GAP_ROWS = 20
E5_LOG_THRESHOLD = math.log(2.0)
E5_SPLIT_WINDOW_ROWS = 5
WARMUP_ROWS = 252
EXACT_TOLERANCE = 1e-6
PAIR_TOLERANCE = 1e-3
CUMULATIVE_TOLERANCE = 2e-3
REKEY_STATUSES = frozenset({"unavailable:empty_payload", "unavailable:missing_symbol"})
CORPORATE_SUFFIXES = frozenset({"inc", "incorporated", "corp", "corporation", "co", "company", "ltd", "limited", "plc", "llc"})

SECURITY_MASTER = "identity/security_master.csv"
INTERVAL_RESULTS = "identity/interval_results.csv"
INTERVAL_CSV = "membership/constituent_intervals.csv"
BUILD_MANIFEST = "membership/membership_build_manifest.json"
DISTRIBUTION_SUPPORT = "identity/distribution_support.parquet"
PANEL_DIR = "panel"
INVENTORY = "panel/inventory_discovery.json"

MASTER_COLUMNS = (
    "permanent_id", "vendor_code", "episode", "vendor_name", "isin", "role", "first_bar", "last_bar",
    "bar_count", "resolution", "resolution_evidence", "eod_status", "eod_discovery_status",
    "episode_panel_refusal", "interval_count", "has_delisting_candidate_interval",
)
INTERVAL_COLUMNS = (
    "interval_id", "raw_row", "vendor_code", "start_date", "end_date", "permanent_id", "resolution",
    "resolution_evidence", "duplicate_of", "bars_in_span", "m_in", "m_out", "R_entry", "R_exit",
    "exit_class", "member_days_disc", "census_cap", "eod_status", "eod_discovery_status",
)
NO_BARS_CAPPED = ("no_containing_episode:no_vendor_bars:", "no_containing_episode:rekeyed_rename_candidate",
                  "no_containing_episode:no_bars_in_interval")


# ---------------------------------------------------------------- snapshot access


@dataclass
class Snapshot:
    """A snapshot directory, its manifest, its partition rule, and the sealed window and ``calendar_source``.

    ``access_log`` records the table, code, side, and path of every discovery
    partition opened through ``read_discovery`` (plan 2.2).
    """

    root: Path
    manifest: dict[str, Any]
    holdout_end: date
    calendar_source: str
    holdout_start: date | None = None
    partition_rule: str = PARTITION_RULE_V1
    seal_file: str = SEAL_FILE
    access_log: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def open(cls, root: Path | str) -> "Snapshot":
        root = Path(root)
        window = read_partition_window(root)
        manifest = read_manifest(root)
        if declared_partition_rule(manifest) != window.rule:
            raise SnapshotRefusal("partition_rule_mismatch",
                                  f"manifest declares {declared_partition_rule(manifest)}, seal selects {window.rule}")
        return cls(root=root, manifest=manifest, holdout_end=window.holdout_end, calendar_source=window.calendar_source,
                   holdout_start=window.holdout_start, partition_rule=window.rule, seal_file=window.seal_file)

    @property
    def sides(self) -> tuple[str, ...]:
        """Discovery partition roles: ``discovery`` under rule v1, the two side files under rule v2."""
        return ("discovery",) if self.partition_rule == PARTITION_RULE_V1 else SIDES

    def entry(self, table: str, code: str) -> dict[str, Any] | None:
        return self.manifest.get("entries", {}).get(f"{table}/{code}")

    def status(self, table: str, code: str) -> str:
        entry = self.entry(table, code)
        return "absent" if entry is None else str(entry["status"])

    def discovery_status(self, table: str, code: str, side: str = "discovery") -> str:
        entry = self.entry(table, code)
        return "" if entry is None else str(entry.get("partition_statuses", {}).get(side, ""))

    def evidence_valid(self, table: str, code: str, side: str = "discovery") -> bool:
        """``retrieved`` with a valid discovery partition: readable corporate-action evidence."""
        return self.status(table, code) == "retrieved" and self.discovery_status(table, code, side) == "valid"

    def read_discovery(self, table: str, code: str, side: str = "discovery") -> pd.DataFrame | None:
        """The discovery partition of ``table`` for ``code`` on ``side``, or ``None`` when it has no valid file.

        A side the snapshot's rule does not define refuses ``partition_side_invalid``,
        so a rule v2 consumer names the side it opens.
        """
        if side not in self.sides:
            raise SnapshotRefusal("partition_side_invalid", f"{side} under {self.partition_rule}")
        entry = self.entry(table, code)
        if entry is None or side not in entry.get("authorized_files", {}):
            return None
        record = entry["authorized_files"][side]
        self.access_log.append({"table": table, "code": code, "side": side, "path": record["path"]})
        return _parquet(read_authorized_bytes(self.root, record["path"], self.manifest), record["path"])

    def has_later_row(self, code: str) -> bool:
        """R3-A4: any split or dividend row of ``code`` dated on or after ``holdout_start`` (a date-only flag)."""
        return any((self.entry(table, code) or {}).get("has_row_on_or_after_holdout_start", False)
                   for table in ("splits", "dividends"))

    def read_file(self, key: str) -> pd.DataFrame:
        record = self.manifest["files"][key]
        return _parquet(read_authorized_bytes(self.root, record["path"], self.manifest), record["path"])

    def calendar(self) -> pd.DatetimeIndex:
        return pd.DatetimeIndex(self.read_file("calendar")["date"], name="date")

    def components_retrieved(self) -> date:
        value = parse_strict_date(self.manifest["snapshot"].get("components_retrieved_utc_date"))
        if value is None:
            raise SnapshotRefusal("components_retrieved_utc_date_missing")
        return value


def _parquet(payload: bytes, name: str, columns: list[str] | None = None) -> pd.DataFrame:
    source = io.BytesIO(payload)
    source.name = name
    return pd.read_parquet(source, columns=columns, engine="pyarrow")


def read_bar_dates(snapshot: Snapshot, code: str) -> pd.DatetimeIndex | None:
    """Bar dates of ``code`` from its ``dates/`` sidecar only, hash-verified (plan 5.4 step 4)."""
    entry = snapshot.entry("eod", code)
    if entry is None or "dates" not in entry.get("authorized_files", {}):
        return None
    record = entry["authorized_files"]["dates"]
    payload = read_authorized_bytes(snapshot.root, record["path"], snapshot.manifest)
    return pd.DatetimeIndex(_parquet(payload, record["path"], columns=["date"])["date"])


def membership_codes(frame: pd.DataFrame) -> list[str]:
    codes: list[str] = []
    for code in frame["Code"]:
        if isinstance(code, str) and code and f"{code}.US" not in codes:
            codes.append(f"{code}.US")
    return codes


def request_list(snapshot: Snapshot, membership: pd.DataFrame | None = None) -> list[str]:
    membership = snapshot.read_file("membership") if membership is None else membership
    codes = membership_codes(membership)
    for code in [BENCHMARK, *snapshot.manifest.get("requested_codes", [])]:
        if code not in codes:
            codes.append(code)
    return codes


def discovery_inputs_sha256(snapshot: Snapshot, membership: pd.DataFrame | None = None) -> str:
    """SHA-256 over the discovery-scope inputs every derived artifact depends on (S7)."""
    files = snapshot.manifest.get("files", {})
    head = [files.get(key, {}).get("sha256") for key in ("calendar", "membership", "symbols_listed", "symbols_delisted")]
    head.append(snapshot.manifest["snapshot"].get("components_retrieved_utc_date"))
    rows = []
    for code in request_list(snapshot, membership):
        for table in TABLES:
            entry = snapshot.entry(table, code) or {}
            roles = entry.get("authorized_files", {})
            rows.append([code, table, entry.get("status", "absent"), roles.get("dates", {}).get("sha256"),
                         *[roles.get(side, {}).get("sha256") for side in snapshot.sides]])
    if snapshot.partition_rule == PARTITION_RULE_V2:
        head.append(m4_8_membership.read_curated(snapshot.root / "membership").sha256)
    return sha256_bytes(canonical_json({"inputs": head, "entries": sorted(rows)}))


def read_derived_json(root: Path | str, relative: str) -> dict[str, Any]:
    """A derived JSON artifact of an earlier stage; a missing file is the typed ``derived_artifact_missing``."""
    path = Path(root) / relative
    if not path.is_file():
        raise SnapshotRefusal("derived_artifact_missing", relative)
    return json.loads(path.read_bytes())


def require_current(snapshot: Snapshot, recorded: str | None, artifact: str) -> str:
    current = discovery_inputs_sha256(snapshot)
    if recorded != current:
        raise SnapshotRefusal("derived_artifact_stale", artifact)
    return current


def canonical_json(payload: Any) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def write_bytes(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)
    return sha256_bytes(payload)


def csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False, lineterminator="\n").encode("utf-8")


def parquet_bytes(frame: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    frame.to_parquet(buffer, engine="pyarrow", index=False)
    return buffer.getvalue()


def discovery_window(calendar: pd.DatetimeIndex, holdout_end: date) -> tuple[int, int, int]:
    """Rule v1: ``(i_H, D0, D_last)`` as rows of the full calendar (M4.7 plan 4.1)."""
    i_h = int(calendar.searchsorted(pd.Timestamp(holdout_end)))
    resets = scheduled_reset_rows(calendar)
    d_last = int(resets[-1]) if len(resets) else len(calendar) - 1
    later = resets[resets >= i_h + WARMUP_ROWS + 1]
    d0 = int(later[0]) if len(later) else d_last + 1
    return i_h, d0, d_last


@dataclass(frozen=True)
class Segment:
    """One discovery segment as calendar rows (plan 2.5 and the section 7 interface).

    ``side`` is the discovery side file the segment opens; ``anchor_row`` is its
    first accounting row (all cash, no trade); features may read rows
    ``[feature_floor_row, feature_ceiling_row]`` only.
    """

    segment_id: str
    side: str
    anchor_row: int
    first_reset_row: int
    last_ic_reset_row: int
    last_book_row: int
    feature_floor_row: int
    feature_ceiling_row: int


def reset_in_month(calendar: pd.DatetimeIndex, day: date) -> int:
    """The scheduled reset row in the calendar month of ``day`` (plan 2.4 rule 6)."""
    resets = scheduled_reset_rows(calendar)
    month = pd.Timestamp(day).to_period("M")
    inside = [int(r) for r in resets if calendar[r].to_period("M") == month]
    if not inside:
        raise SnapshotRefusal("reset_missing_in_month", str(month))
    return inside[0]


def segment_ic_resets(calendar: pd.DatetimeIndex, segment: Segment) -> np.ndarray:
    """The scheduled resets in ``[first_reset_row, last_ic_reset_row]``: the segment's IC months (T-SEG-3)."""
    resets = scheduled_reset_rows(calendar)
    return resets[(resets >= segment.first_reset_row) & (resets <= segment.last_ic_reset_row)]


def discovery_segments(
    calendar: pd.DatetimeIndex,
    holdout_start: date,
    holdout_end: date,
    d0_pre: date,
) -> tuple[Segment, ...]:
    """Rule v2: the pre-holdout and post-holdout segments (plan 2.4 rules 6-8, 2.5).

    The pre segment starts at the reset in the calendar month of ``d0_pre``; its
    last IC reset is the last reset whose horizon (the next reset) lies strictly
    before ``holdout_start``, and its last book row is that horizon. The post
    segment keeps the M4.7 window: first reset at least 252 rows after
    ``holdout_end``, last IC reset the last reset with a horizon. A segment
    without an IC reset refuses ``discovery_segment_empty``.
    """
    resets = scheduled_reset_rows(calendar)
    hs_row = int(calendar.searchsorted(pd.Timestamp(holdout_start)))
    he_row = int(calendar.searchsorted(pd.Timestamp(holdout_end)))
    horizons = dict(zip(resets[:-1].tolist(), resets[1:].tolist()))
    first_pre = reset_in_month(calendar, d0_pre)
    pre_ic = [r for r, h in horizons.items() if first_pre <= r and h < hs_row]
    later = resets[resets >= he_row + WARMUP_ROWS + 1]
    first_post = int(later[0]) if len(later) else None
    post_ic = [r for r in horizons if first_post is not None and r >= first_post]
    if first_pre < 1 or not pre_ic or not post_ic:
        raise SnapshotRefusal("discovery_segment_empty", "a segment holds no IC reset")
    pre = Segment("pre", "discovery_pre", first_pre - 1, first_pre, pre_ic[-1], horizons[pre_ic[-1]], 0,
                  horizons[pre_ic[-1]])
    post = Segment("post", "discovery_post", first_post - 1, first_post, post_ic[-1], horizons[post_ic[-1]], he_row,
                   horizons[post_ic[-1]])
    return pre, post


def normalize_name(value: Any) -> str:
    """``name_normalization_v1``: casefold, strip punctuation and corporate suffixes, drop a leading ``the``."""
    if not isinstance(value, str):
        return ""
    tokens = re.sub(r"[^\w\s]", " ", value.casefold()).split()
    while tokens and tokens[-1] in CORPORATE_SUFFIXES:
        tokens.pop()
    if tokens and tokens[0] == "the":
        tokens = tokens[1:]
    return " ".join(tokens)


def normalized_eod_subreason(status: str) -> str:
    """C57: drop ``unavailable:``, replace ``:`` with ``_``; a retrieved code without calendar bars is typed."""
    if status == "retrieved":
        return "retrieved_no_calendar_bars"
    return status.removeprefix("unavailable:").replace(":", "_")


def _truthy(value: Any) -> bool:
    return str(value).strip().casefold() in {"1", "true", "yes"}


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, float) and value != value) or value == ""


# ---------------------------------------------------------------- episode checks (plan 2.2)


@dataclass
class EpisodeCheck:
    """Outcome of the last-bar, in-span, cumulative, and gap checks for one episode."""

    split_basis: str
    outcome: str
    refusal: str | None
    g: float
    rho: float
    later_distribution: bool
    in_span: str
    pairs: int = 0
    dividend_pairs: int = 0
    failing: list[dict[str, Any]] = field(default_factory=list)
    max_residual: float = 0.0
    max_cumulative_drift: float = 0.0
    drift_date: str | None = None
    factor: pd.Series | None = None
    b_d: np.ndarray | None = None
    s_d: np.ndarray | None = None
    undefined_amounts: int = 0


def dividend_amounts(dividends: pd.DataFrame | None, split_dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Per dividend row: ``value`` and the C74/C81 ``amount`` (``unadjustedValue`` basis; NaN when undefined)."""
    if dividends is None or dividends.empty:
        return pd.DataFrame({"date": pd.DatetimeIndex([]), "value": [], "amount": []})
    amounts = []
    for row in dividends.itertuples(index=False):
        vendor = json.loads(row.row_json) if isinstance(getattr(row, "row_json", None), str) else {}
        try:
            unadjusted = float(vendor.get("unadjustedValue"))
        except (TypeError, ValueError):
            unadjusted = math.nan
        if math.isfinite(unadjusted):
            amounts.append(unadjusted)
        elif not (split_dates >= pd.Timestamp(row.date)).any():
            amounts.append(float(row.value))
        else:
            amounts.append(math.nan)
    return pd.DataFrame({"date": pd.DatetimeIndex(dividends["date"]), "value": dividends["value"].astype(float),
                         "amount": amounts})


def evaluate_episode(
    bars: pd.DataFrame,
    in_span_splits: pd.DataFrame,
    post_splits: pd.DataFrame,
    dividends: pd.DataFrame,
    *,
    dividend_evidence: bool,
    final: bool,
    gap_split_after: bool,
) -> EpisodeCheck:
    """Run the plan 2.2 checks on one episode's on-calendar discovery bars.

    ``bars`` holds ``close`` and ``adjusted_close`` indexed by date;
    ``in_span_splits`` and ``post_splits`` hold ``date`` and ``ratio`` (the
    split rows attributed to the episode and every discovery split row of the
    code after its last bar); ``dividends`` holds the code's discovery
    dividend rows with ``value`` and ``amount``.
    """
    close = bars["close"].to_numpy(dtype=float)
    adjusted = bars["adjusted_close"].to_numpy(dtype=float)
    dates = pd.DatetimeIndex(bars.index)
    last = dates[-1]
    after = dividends[dividends["date"] > last]
    later_distribution = bool(dividend_evidence and (after["value"] > 0).any())
    p_k = (not dividend_evidence) or later_distribution
    g = float(adjusted[-1] / close[-1])
    rho = float(np.prod(post_splits["ratio"].to_numpy(dtype=float))) if len(post_splits) else 1.0

    def supported(d: float) -> bool:
        return abs(d - 1.0) <= EXACT_TOLERANCE

    def feasible(d: float) -> bool:
        return supported(d) or (p_k and d <= 1.0 + EXACT_TOLERANCE)

    unapplied, applied = g, g * rho
    two = abs(rho - 1.0) > EXACT_TOLERANCE
    refusal = None
    if two and final:
        if supported(unapplied) and not feasible(applied):
            outcome = "excluded_unapplied"
        elif supported(applied) and not feasible(unapplied):
            outcome = "attributed_applied"
        else:
            outcome, refusal = "refused", "split_attribution_ambiguous"
    elif two:
        if supported(unapplied) and not feasible(applied):
            outcome = "written"
        elif supported(unapplied):
            outcome, refusal = "refused", "split_basis_unverified:explanations_disagree"
        elif supported(applied):
            outcome, refusal = "refused", "cross_episode_adjustment"
        else:
            outcome, refusal = "refused", "split_basis_unverified:unexplained_deviation"
    elif supported(unapplied):
        outcome = "excluded_unapplied" if final and len(post_splits) else "written"
    else:
        outcome, refusal = "refused", "split_basis_unverified:unexplained_deviation"
    split_basis = {"attributed_applied": "applied", "refused": "refused"}.get(outcome, "unapplied")
    check = EpisodeCheck(split_basis, outcome, refusal, g, rho, later_distribution,
                         "not_evaluated_split_basis_refused")
    if refusal is not None:
        return check

    factor_rows = pd.concat([in_span_splits, post_splits]) if outcome == "attributed_applied" else in_span_splits
    factor = compute_cumulative_split_factor(dates, factor_rows if len(factor_rows) else None)
    y = factor.to_numpy() * adjusted / close
    in_span_dividends = dividends[(dividends["date"] >= dates[0]) & (dividends["date"] <= last)]
    in_span_dividends = in_span_dividends[in_span_dividends["amount"].isna() | (in_span_dividends["amount"] > 0)]
    events = sorted(
        [(pd.Timestamp(d), 0, float(r)) for d, r in zip(in_span_splits["date"], in_span_splits["ratio"])]
        + ([(pd.Timestamp(d), 1, float(a)) for d, a in zip(in_span_dividends["date"], in_span_dividends["amount"])]
           if dividend_evidence else []),
        key=lambda event: (event[0], event[1]),
    )
    values = np.zeros(max(len(dates) - 1, 0))
    distribution_logs = np.full(len(values), np.nan)
    for j in range(len(values)):
        pair_events = [event for event in events if dates[j] < event[0] <= dates[j + 1]]
        phi, carried, delta, defined = 1.0, 1.0, 1.0, True
        for _, kind, number in pair_events:
            if kind == 0:
                phi *= number
                continue
            if not math.isfinite(number):
                defined = False
                check.undefined_amounts += 1
                break
            delta_i = 1.0 - number / (close[j] * carried / phi)
            if not 0.0 < delta_i <= 1.0:
                defined = False
                break
            delta *= delta_i
            carried *= delta_i
        has_split = any(kind == 0 for _, kind, _ in pair_events)
        has_dividend = any(kind == 1 for _, kind, _ in pair_events)
        check.dividend_pairs += int(has_dividend)
        residual = abs(y[j + 1] / y[j] * delta - 1.0) if defined else math.inf
        check.max_residual = max(check.max_residual, residual)
        if residual > PAIR_TOLERANCE:
            kind = "declared_split_pair" if has_split else "declared_dividend_pair" if has_dividend else "undeclared_step"
            check.failing.append({"date_a": dates[j].date().isoformat(), "date_b": dates[j + 1].date().isoformat(),
                                  "kind": kind, "residual": residual if defined else None})
        else:
            values[j] = math.log(y[j + 1] / y[j] * delta)
            if has_dividend:
                distribution_logs[j] = -math.log(delta)
    check.pairs = len(values)
    check.factor = factor
    if check.failing:
        check.in_span, check.refusal = "mismatch", "split_basis_unverified:in_span_step_mismatch"
        return check
    cumulative = np.concatenate((np.cumsum(values[::-1])[::-1], [0.0]))
    worst = int(np.argmax(np.abs(cumulative)))
    check.max_cumulative_drift = float(abs(cumulative[worst]))
    check.drift_date = dates[worst].date().isoformat()
    if check.max_cumulative_drift > CUMULATIVE_TOLERANCE:
        check.in_span, check.refusal = "cumulative_drift", "split_basis_unverified:cumulative_basis_drift"
        return check
    check.in_span = "passed"
    if gap_split_after:
        check.refusal = "split_attribution_ambiguous"
        return check
    logs = np.concatenate((np.nan_to_num(distribution_logs, nan=-np.inf), [-np.inf]))
    check.b_d = np.maximum(np.maximum.accumulate(logs[::-1])[::-1], 0.0)
    check.s_d = np.concatenate((np.cumsum(np.nan_to_num(distribution_logs)[::-1])[::-1], [0.0]))
    return check


# ---------------------------------------------------------------- build


@dataclass
class Episode:
    code: str
    k: int
    rows: np.ndarray
    role: str
    permanent_id: str = ""
    resolution: str = "resolved"
    evidence: list[str] = field(default_factory=list)
    panel_refusal: str = ""
    intervals: list[dict[str, Any]] = field(default_factory=list)
    parent: int = 0

    @property
    def first(self) -> int:
        return int(self.rows[0])

    @property
    def last(self) -> int:
        return int(self.rows[-1])


def _episodes(rows: np.ndarray, code: str, role: str) -> list[Episode]:
    if rows.size == 0:
        return []
    breaks = np.flatnonzero(np.diff(rows) - 1 > E1_GAP_ROWS) + 1
    return [Episode(code, k, part, role) for k, part in enumerate(np.split(rows, breaks), start=1)]


def _seal_gaps(a: np.ndarray, b: np.ndarray, hs_row: int, he_row: int) -> np.ndarray:
    """Bar-date gaps ``(a, b)`` with an endpoint inside ``[hs_row, he_row)`` or spanning it (SL-5)."""
    return (b - a > 1) & (((a >= hs_row) & (a < he_row)) | ((b >= hs_row) & (b < he_row)) | ((a < hs_row) & (b >= he_row)))


def seal_gap_split(eps: list[Episode], hs_row: int, he_row: int) -> tuple[list[Episode], int]:
    """``seal_gap_identity_split_v1``: split E1 episodes at seal gaps; return the episodes and the split count.

    E5 cannot evaluate a gap with an endpoint in the seal, so such a gap starts
    a new permanent ID. The count includes E1 breaks whose gap touches the seal
    (a ticker reused inside the seal). Episodes are renumbered in date order and
    keep their E1 episode as ``parent``.
    """
    split: list[Episode] = []
    count = 0
    for position, ep in enumerate(eps):
        if position:
            count += int(_seal_gaps(np.array([eps[position - 1].last]), np.array([ep.first]), hs_row, he_row)[0])
        breaks = np.flatnonzero(_seal_gaps(ep.rows[:-1], ep.rows[1:], hs_row, he_row)) + 1
        count += len(breaks)
        for part in np.split(ep.rows, breaks):
            split.append(Episode(ep.code, len(split) + 1, part, ep.role, parent=ep.k))
    return split, count


def _row(calendar: pd.DatetimeIndex, day: date | pd.Timestamp) -> int:
    return int(calendar.searchsorted(pd.Timestamp(day)))


def _first_reset_at_or_after(resets: np.ndarray, row: int) -> int | None:
    position = int(np.searchsorted(resets, row, side="left"))
    return int(resets[position]) if position < len(resets) else None


def _date(calendar: pd.DatetimeIndex, row: int | None) -> str:
    return "" if row is None or not 0 <= row < len(calendar) else calendar[row].date().isoformat()


def interval_keys(frame: pd.DataFrame, records: list[dict[str, Any]]) -> list[str]:
    """C76 keys: ``<quote(code)>/<StartDate>/<EndDate or open>/<n>`` or ``raw_row/<index>``."""
    keys, seen = [], {}
    raw_rows = frame["raw_row"].tolist() if "raw_row" in frame else list(range(len(frame)))
    for record, row, raw_row in zip(records, frame.to_dict(orient="records"), raw_rows):
        if record["outcome"] in ("entry_missing_field", "entry_unparseable_date"):
            keys.append(f"raw_row/{raw_row}")
            continue
        end = "open" if _blank(row.get("EndDate")) else str(row["EndDate"])
        stem = f"{urllib.parse.quote(str(row['Code']) + '.US', safe='')}/{row['StartDate']}/{end}"
        seen[stem] = seen.get(stem, 0) + 1
        keys.append(f"{stem}/{seen[stem]}")
    return keys


def build_universe(snapshot_dir: Path | str, d0_pre: date | None = None) -> dict[str, Any]:
    """Run plan 1.6 steps 1-7 on the snapshot and write every universe artifact.

    A rule v2 snapshot needs ``d0_pre`` (the membership census output) to fix
    its two segments; a rule v1 snapshot ignores it.
    """
    snapshot = Snapshot.open(snapshot_dir)
    root = snapshot.root
    calendar = snapshot.calendar()
    n_rows = len(calendar)
    v2 = snapshot.partition_rule == PARTITION_RULE_V2
    segments: tuple[Segment, ...] = ()
    if v2:
        if d0_pre is None:
            raise SnapshotRefusal("d0_pre_required", "a rule v2 snapshot needs D0_pre from the membership census")
        segments = discovery_segments(calendar, snapshot.holdout_start, snapshot.holdout_end, d0_pre)
        hs_row, i_h = _row(calendar, snapshot.holdout_start), _row(calendar, snapshot.holdout_end)
        d0, d_last = segments[0].first_reset_row, segments[-1].last_book_row
        spans = [(segment.first_reset_row, segment.last_book_row) for segment in segments]
        side_rows = {"discovery_pre": (0, hs_row), "discovery_post": (i_h, n_rows)}
    else:
        i_h, d0, d_last = discovery_window(calendar, snapshot.holdout_end)
        spans = [(d0, d_last)]
        side_rows = {"discovery": (i_h, n_rows)}
    resets = scheduled_reset_rows(calendar)
    retrieved = snapshot.components_retrieved()
    raw_membership = snapshot.read_file("membership")
    membership = raw_membership
    supplement: list[dict[str, Any]] = []
    if v2:
        curated = m4_8_membership.read_curated(root / "membership")
        supplement = m4_8_membership.validate_supplement(curated.supplement, raw_membership, calendar)
        membership = m4_8_membership.apply_supplement(raw_membership, supplement, retrieved)
    records = classify_membership_entries(membership, retrieved)
    keys = interval_keys(membership, records)
    raw_rows = membership["raw_row"].tolist() if "raw_row" in membership else list(range(len(membership)))
    listed = _symbol_map(snapshot.read_file("symbols_listed"))
    delisted = _symbol_map(snapshot.read_file("symbols_delisted"))
    inputs_sha = discovery_inputs_sha256(snapshot, raw_membership)

    members = membership_codes(membership)
    roles = {code: "member" for code in members}
    for code in [BENCHMARK, *snapshot.manifest.get("requested_codes", [])]:
        roles.setdefault(code, "benchmark" if code == BENCHMARK else "acquirer_only")
    calendar_set = {day: row for row, day in enumerate(calendar)}

    code_rows: dict[str, np.ndarray] = {}
    off_calendar: dict[str, int] = {}
    for code in roles:
        dates = read_bar_dates(snapshot, code)
        dates = pd.DatetimeIndex([]) if dates is None else dates
        rows = np.array(sorted(calendar_set[d] for d in dates if d in calendar_set), dtype=int)
        code_rows[code] = rows
        inside = (dates >= pd.Timestamp(snapshot.holdout_end)) & (dates <= calendar[-1])
        if v2:
            inside |= (dates >= calendar[0]) & (dates < pd.Timestamp(snapshot.holdout_start))
        off_calendar[code] = int(sum(1 for d, keep in zip(dates, inside) if keep and d not in calendar_set))
    e1_episodes = {code: _episodes(code_rows[code], code, roles[code]) for code in roles}
    episodes = e1_episodes
    seal_splits: dict[str, int] = {}
    if v2:
        episodes = {}
        for code, eps in e1_episodes.items():
            episodes[code], seal_splits[code] = seal_gap_split(eps, hs_row, i_h)

    # Entries: typed outcomes, boundary rows, and E2 per interval (C52, C60, C62).
    starts_by_date: dict[date, list[tuple[str, str]]] = {}
    for record, row in zip(records, membership.to_dict(orient="records")):
        if record["start"] is not None:
            starts_by_date.setdefault(record["start"], []).append((f"{record['code']}.US", normalize_name(row.get("Name"))))
    entries: list[dict[str, Any]] = []
    for record, row, key, raw_row in zip(records, membership.to_dict(orient="records"), keys, raw_rows):
        code = f"{record['code']}.US" if record["code"] else ""
        entry = {
            "interval_id": key, "raw_row": raw_row, "vendor_code": code,
            "start_date": "" if _blank(row.get("StartDate")) else str(row["StartDate"]),
            "end_date": "" if _blank(row.get("EndDate")) else str(row["EndDate"]),
            "name": row.get("Name"), "is_delisted": _truthy(row.get("IsDelisted")),
            "start": record["start"], "end": record["end"], "permanent_id": "", "evidence": [],
            "duplicate_of": "" if record["duplicate_of"] is None else keys[record["duplicate_of"]],
            "bars_in_span": "", "m_in": None, "m_out": None, "R_entry": None, "R_exit": None, "exit_class": "",
            "member_days_disc": 0, "eod_status": snapshot.status("eod", code) if code else "",
            "eod_discovery_status": snapshot.discovery_status("eod", code) if code else "",
            "episode": None,
        }
        entries.append(entry)
        outcome = record["outcome"]
        if outcome in ("entry_missing_field", "entry_unparseable_date"):
            entry["resolution"] = outcome
            continue
        rs = _row(calendar, record["start"])
        re_ = n_rows if record["end"] is None else _row(calendar, record["end"])
        entry["rs"], entry["re"] = rs, re_
        entry["m_in"] = rs + 1
        entry["m_out"] = None if record["end"] is None else re_ + 1
        entry["R_entry"] = _first_reset_at_or_after(resets, rs + 1)
        exit_reset = None if record["end"] is None else _first_reset_at_or_after(resets, re_ + 1)
        entry["R_exit"] = d_last if exit_reset is None else exit_reset
        if outcome == "degenerate_interval":
            entry["m_out"] = entry["m_in"]
        if outcome != "retained":
            entry["resolution"] = outcome
            if outcome == "raw_overlap":
                entry["member_days_disc"] = _member_days(entry, spans, n_rows)
            continue
        entry["member_days_disc"] = _member_days(entry, spans, n_rows)
        rows = code_rows[code]
        in_span = rows[(rows >= rs) & (rows < re_)]
        entry["bars_in_span"] = int(in_span.size)
        name = normalize_name(row.get("Name"))
        renamed = record["end"] is not None and any(
            other != code and other_name == name for other, other_name in starts_by_date.get(record["end"], ())
        )
        status = entry["eod_status"]
        if rows.size == 0:
            if renamed and status in REKEY_STATUSES:
                entry["resolution"] = "no_containing_episode:rekeyed_rename_candidate"
            else:
                entry["resolution"] = f"no_containing_episode:no_vendor_bars:{normalized_eod_subreason(status)}"
            continue
        if in_span.size == 0:
            rekeyed = renamed and status == "retrieved"
            entry["resolution"] = ("no_containing_episode:rekeyed_rename_candidate" if rekeyed
                                   else "no_containing_episode:no_bars_in_interval")
            if rekeyed:
                entry["evidence"].append(f"first_bar={_date(calendar, int(rows[0]))}")
            continue
        touched = [ep for ep in episodes[code] if ((ep.rows >= rs) & (ep.rows < re_)).any()]
        siblings = v2 and len({ep.parent for ep in touched}) == 1
        if len(touched) > 1 and not siblings:
            entry["resolution"] = "ambiguous_reuse_gap"
        elif rs < touched[0].first - E1_GAP_ROWS:
            entry["resolution"] = "no_containing_episode"
        else:
            entry["resolution"] = "resolved"
            entry["episode"] = touched[0]
            touched[0].intervals.append(entry)
            # SL-5: an interval over a seal gap attaches to each split ID by date.
            for position, ep in enumerate(touched[1:], start=2):
                piece = {**entry, "interval_id": f"{key}#seal_split_{position}", "evidence": [], "seal_piece": True,
                         "start_date": _date(calendar, ep.first), "start": calendar[ep.first].date()}
                _set_rows(piece, ep.first, re_, record["end"], resets, d_last, n_rows, spans, rows)
                entry.update(end_date=_date(calendar, ep.first), end=calendar[ep.first].date(), seal_split_end=True)
                _set_rows(entry, entry["rs"], ep.first, entry["end"], resets, d_last, n_rows, spans, rows)
                piece["episode"] = ep
                ep.intervals.append(piece)
                entries.append(piece)
                entry = piece

    # Code-level rules E3-E6 (C60); rule E5 reads discovery values and attributed split rows, one side at a time.
    split_frames = {code: {side: (snapshot.read_discovery("splits", code, side)
                                  if snapshot.evidence_valid("splits", code, side) else None)
                           for side in snapshot.sides} for code in roles}
    eod_frames: dict[str, dict[str, pd.DataFrame | None]] = {}
    e5_not_evaluated: dict[str, int] = {}
    name_mismatches = 0
    for code in roles:
        code_entries = [e for e in entries if e["vendor_code"] == code and e["start"] is not None and not e.get("seal_piece")]
        fired: list[tuple[str, str]] = []
        eps = episodes[code]
        continuous = len(e1_episodes[code]) == 1
        if eps:
            if _e3_fires(code_entries, e1_episodes[code]):
                fired.append(("E3", "ambiguous_reuse_continuous_history"))
            isin_l, isin_d = listed.get(code, {}).get("isin"), delisted.get(code, {}).get("isin")
            if isin_l and isin_d and isin_l != isin_d and continuous:
                fired.append(("E4", "ambiguous_reuse_isin_conflict"))
            eod_frames[code] = {side: _discovery_bars(snapshot, code, calendar_set, side) for side in snapshot.sides}
            e5, skipped = _e5_fires(eps, [(*side_rows[side], eod_frames[code][side], split_frames[code][side])
                                          for side in snapshot.sides], calendar)
            e5_not_evaluated[code] = skipped
            if e5:
                fired.append(("E5", "ambiguous_reuse_discontinuity"))
            trigger = (code in listed and code in delisted) or (
                code in listed and any(e["is_delisted"] for e in code_entries))
            if trigger and continuous:
                if isin_l and isin_d and isin_l == isin_d:
                    eps[0].evidence.append("E6:isin_continuity")
                elif not (isin_l and isin_d):
                    missing = "+".join(side for side, value in (("listed_isin", isin_l), ("delisted_isin", isin_d)) if not value)
                    fired.append(("E6", "ambiguous_reuse_delisted_and_listed_continuous_history"))
                    eps[0].evidence.append(f"E6:missing_identifier={missing}")
        for e in code_entries:
            symbol_name = listed.get(code, delisted.get(code, {})).get("name")
            if symbol_name and normalize_name(symbol_name) != normalize_name(e["name"]):
                name_mismatches += 1
        if fired:
            refusal = fired[0][1]
            tags = [f"{rule}:{code_}" for rule, code_ in fired]
            for ep in eps:
                ep.resolution = refusal
                ep.evidence.extend(tags)
                for e in ep.intervals:
                    e["resolution"], e["episode"] = refusal, None
                    e["evidence"].extend(tags)
            for e in code_entries:
                if e["resolution"].startswith(("no_containing_episode:no_bars_in_interval",
                                              "no_containing_episode:rekeyed_rename_candidate")):
                    e["evidence"].extend(tags)
        for ep in eps:
            if ep.resolution == "resolved":
                ep.permanent_id = f"{code}#E{ep.k}"

    for e in entries:
        ep = e.pop("episode")
        if ep is not None and e["resolution"] == "resolved":
            e["permanent_id"] = ep.permanent_id
            # A piece that ends at a seal gap ends by identity split (SL-5), never by a disappearance.
            e["exit_class"] = "seal_gap_identity_split" if e.get("seal_split_end") else exit_class(ep.last, e["R_exit"], d_last)

    # Step 6: split-basis, in-span, cumulative, and gap checks; panel write (C45, C55, C67, C72, C73, C82).
    panel_root = root / PANEL_DIR
    for side in snapshot.sides:
        shutil.rmtree(panel_root / side, ignore_errors=True)
    counters = _new_counters()
    if v2:
        counters.update(segment_anchor_checks=0, pre_side_split_rows_after_anchor=0,
                        seal_gap_identity_split=sum(seal_splits.values()))
    pre_ceiling = segments[0].feature_ceiling_row if v2 else n_rows
    episode_checks: list[dict[str, Any]] = []
    support_frames: list[pd.DataFrame] = []
    written: dict[str, tuple[str, str, str]] = {}
    for code, eps in episodes.items():
        evaluated: set[int] = set()
        for side in snapshot.sides:
            lo, hi = side_rows[side]
            prefix = f"{side}:" if v2 else ""
            side_eps = [ep for ep in eps if ((ep.rows >= lo) & (ep.rows < hi)).any()] if v2 else eps
            if not side_eps:
                continue
            spans_side = ([(int(ep.rows[(ep.rows >= lo) & (ep.rows < hi)][0]), int(ep.rows[(ep.rows >= lo) & (ep.rows < hi)][-1]))
                           for ep in side_eps] if v2 else [(ep.first, ep.last) for ep in eps])
            splits = split_frames[code][side]
            split_dates = pd.DatetimeIndex([]) if splits is None else pd.DatetimeIndex(splits["date"])
            ratios = pd.DataFrame({"date": split_dates, "ratio": [] if splits is None else splits["ratio"].astype(float)})
            dividend_ok = snapshot.evidence_valid("dividends", code, side)
            amount_splits = split_dates
            if side == "discovery_pre" and (snapshot.entry("splits", code) or {}).get("has_row_on_or_after_holdout_start"):
                # A later split makes a missing unadjustedValue undefined, as a later discovery split does under v1.
                amount_splits = split_dates.append(pd.DatetimeIndex([pd.Timestamp(snapshot.holdout_start)]))
            dividends = dividend_amounts(snapshot.read_discovery("dividends", code, side) if dividend_ok else None,
                                         amount_splits)
            anchor = None
            if side == "discovery_pre" and ((code_rows[code] >= hs_row).any() or snapshot.has_later_row(code)):
                # SL-2: anchor at the code's last pre-side bar; later pre-side action rows cannot enter a(t) / a(tau).
                anchor = int(code_rows[code][code_rows[code] < hs_row].max())
                keep = np.asarray(split_dates <= calendar[anchor])
                counters["pre_side_split_rows_after_anchor"] += int((~keep).sum())
                split_dates, ratios = split_dates[keep], ratios[keep].reset_index(drop=True)
                dividends = dividends[dividends["date"] <= calendar[anchor]]
            bar_dates = [(calendar[first], calendar[last]) for first, last in spans_side]
            attributed: dict[int, list[int]] = {ep.k: [] for ep in side_eps}
            gap_rows: dict[int, int] = {}
            post_final = []
            for index, day in enumerate(split_dates):
                spot = next((k for k, (first, last) in enumerate(bar_dates) if first <= day <= last), None)
                if spot is not None:
                    attributed[side_eps[spot].k].append(index)
                elif side_eps and day > bar_dates[-1][1]:
                    post_final.append(index)
                elif side_eps and day < bar_dates[0][0]:
                    counters["split_rows_before_first_bar"][code] = counters["split_rows_before_first_bar"].get(code, 0) + 1
                elif side_eps:
                    preceding = max(k for k, (_, last) in enumerate(bar_dates) if last < day)
                    gap_rows[side_eps[preceding].k] = gap_rows.get(side_eps[preceding].k, 0) + 1
                    counters["split_rows_unattributed"] += 1
            frame = eod_frames.get(code, {}).get(side)
            for ep, (first, last) in zip(side_eps, spans_side):
                if ep.resolution != "resolved":
                    continue
                final = ep is side_eps[-1]
                has_discovery_bar = v2 or ep.last >= i_h
                if not has_discovery_bar:
                    ep.evidence.append("split_basis:not_evaluated:no_discovery_bar")
                    counters["split_basis_check_by_outcome"]["not_evaluated_no_discovery_bar"] += 1
                    counters["in_span_step_check_by_outcome"]["not_evaluated_no_discovery_bar"] += 1
                    if final and post_final:
                        counters["split_rows_after_final_bar"]["not_evaluated_no_discovery_bar"] += len(post_final)
                    continue
                evaluated.add(ep.k)
                if frame is None:
                    ep.evidence.append(f"{prefix}split_basis:not_evaluated:{side}_partition_"
                                       f"{snapshot.discovery_status('eod', code, side) or 'missing'}")
                    continue
                bars = frame[(frame.index >= calendar[max(first, lo)]) & (frame.index <= calendar[last])]
                check_bars = bars
                if anchor is not None:
                    a_tau = frame.loc[calendar[anchor], "adjusted_close"] / frame.loc[calendar[anchor], "close"]
                    check_bars = bars.assign(adjusted_close=bars["adjusted_close"] / a_tau)
                    counters["segment_anchor_checks"] += 1
                after_last = split_dates > calendar[last]
                check = evaluate_episode(
                    check_bars, ratios.iloc[attributed[ep.k]], ratios[after_last], dividends,
                    dividend_evidence=dividend_ok, final=final, gap_split_after=ep.k in gap_rows,
                )
                _record_check(ep, check, counters, final, len(post_final), dividend_ok, prefix)
                episode_checks.append({
                    "permanent_id": ep.permanent_id, "vendor_code": code, "episode": ep.k,
                    "split_basis": check.split_basis, "outcome": check.outcome, "refusal": check.refusal,
                    "in_span": check.in_span, "pairs": check.pairs, "dividend_pairs": check.dividend_pairs,
                    "failing_pairs": check.failing, "max_cumulative_drift": check.max_cumulative_drift,
                    "later_distribution": check.later_distribution, "dividend_evidence": dividend_ok,
                    "min_adjusted_close": float(bars["adjusted_close"].min()),
                    "attributed_splits": [{"date": split_dates[i].date().isoformat(), "ratio": float(ratios["ratio"].iloc[i])}
                                          for i in attributed[ep.k]],
                    "max_b_d": None if check.b_d is None else float(check.b_d[0]),
                    "max_s_d": None if check.s_d is None else float(check.s_d[0]),
                    **({"side": side, "segment_anchor": anchor is not None} if v2 else {}),
                })
                if check.refusal is not None:
                    ep.panel_refusal = ";".join(filter(None, (ep.panel_refusal, f"{prefix}{check.refusal}")))
                    continue
                # SL-3: pre-side panels end at the pre segment's feature ceiling; an anchored panel is normalized
                # to its own last row, so no stored value carries a(tau) or any action dated after that row.
                kept = np.asarray(bars.index <= calendar[min(pre_ceiling, n_rows - 1)]) if side == "discovery_pre" else \
                    np.ones(len(bars), dtype=bool)
                if not kept.any():
                    ep.evidence.append(f"{prefix}panel_not_written:after_feature_ceiling")
                    continue
                panel_rows = frame.loc[bars.index[kept]]
                if anchor is not None:
                    panel_rows = panel_rows.assign(adjusted_close=panel_rows["adjusted_close"]
                                                   / (panel_rows["adjusted_close"].iloc[-1] / panel_rows["close"].iloc[-1]))
                panel = panel_rows.reset_index()
                panel["symbol"] = code
                panel["permanent_id"] = ep.permanent_id
                panel["split_factor"] = check.factor.to_numpy()[kept]
                relative = f"{side}/{ep.permanent_id}.parquet"
                written[relative] = (ep.permanent_id, side, write_bytes(panel_root / relative, parquet_bytes(panel)))
                if check.dividend_pairs:
                    support_frames.append(pd.DataFrame({"permanent_id": ep.permanent_id, "date": bars.index[kept],
                                                        "b_d": check.b_d[kept], "s_d": check.s_d[kept]}))
        for ep in eps:
            if v2 and ep.resolution == "resolved" and ep.k not in evaluated:
                ep.evidence.append("split_basis:not_evaluated:no_discovery_bar")
                counters["split_basis_check_by_outcome"]["not_evaluated_no_discovery_bar"] += 1
                counters["in_span_step_check_by_outcome"]["not_evaluated_no_discovery_bar"] += 1

    for pid in sorted({pid for pid, _, _ in written.values()}):
        if load_symbol_splits(panel_root, pid) is not None:
            raise SnapshotRefusal("panel_split_table_present", pid)

    # Outputs: interval results, interval CSV (round-tripped), security master, inventory, build manifest.
    interval_frame = _interval_frame(entries, calendar)
    interval_csv = _constituent_csv(entries)
    outputs = {
        INTERVAL_RESULTS: write_bytes(root / INTERVAL_RESULTS, csv_bytes(interval_frame)),
        INTERVAL_CSV: write_bytes(root / INTERVAL_CSV, csv_bytes(interval_csv)),
    }
    _round_trip_intervals(root / INTERVAL_CSV, entries, calendar)
    master = _master_frame(episodes, calendar, snapshot, listed, delisted, entries)
    outputs[SECURITY_MASTER] = write_bytes(root / SECURITY_MASTER, csv_bytes(master))
    support = (pd.concat(support_frames, ignore_index=True) if support_frames
               else pd.DataFrame({"permanent_id": pd.Series(dtype=object), "date": pd.DatetimeIndex([]),
                                  "b_d": pd.Series(dtype=float), "s_d": pd.Series(dtype=float)}))
    outputs[DISTRIBUTION_SUPPORT] = write_bytes(root / DISTRIBUTION_SUPPORT, parquet_bytes(support))
    inventory = {
        "discovery_inputs_sha256": inputs_sha,
        "files": [{"symbol": pid, "file": relative, "sha256": sha, **({"side": side} if v2 else {})}
                  for relative, (pid, side, sha) in sorted(written.items())],
    }
    outputs[INVENTORY] = write_bytes(root / INVENTORY, canonical_json(inventory))

    build_manifest = {
        "schema_version": "m4_7_membership_build_manifest_v1",
        "membership_availability_basis": "vendor_effective_date_as_known_at_v1",
        "interval_semantics": "half_open_start_inclusive_end_exclusive_v1",
        "interval_boundary_rule": "calendar_row_semantics_v1",
        "calendar_source": snapshot.calendar_source,
        "bar_date_source": "dates_sidecar_v1",
        "corporate_action_attribution": "episode_span_attribution_with_split_basis_in_span_step_and_cumulative_drift_checks_v3",
        "dividend_factor_formula": "prior_close_v1",
        "rule_versions": {"entry_rule": "c75_exact_duplicate_collapse_overlap_refusal_v1",
                          "identity_rules": "e1_e6_isin_continuity_v1", "name_normalization": "name_normalization_v1"},
        "holdout_end": snapshot.holdout_end.isoformat(),
        "discovery_window": {"first_discovery_row": _date(calendar, i_h), "D0": _date(calendar, d0),
                             "D_last": _date(calendar, d_last)},
        "interval_resolution_counts": _counts(e["resolution"] for e in entries),
        "episode_panel_refusal_counts": _counts(ep.panel_refusal for eps in episodes.values() for ep in eps if ep.panel_refusal),
        "exact_duplicate_entries_collapsed": sum(r["outcome"] == "exact_duplicate_collapsed" for r in records),
        "raw_overlap_entries": sum(r["outcome"] == "raw_overlap" for r in records),
        **counters,
        "off_calendar_bar_rows": {code: count for code, count in sorted(off_calendar.items()) if count},
        "e5_not_evaluated_holdout_rows": {code: count for code, count in sorted(e5_not_evaluated.items()) if count},
        "name_mismatch_recorded": name_mismatches,
        "episode_checks": episode_checks,
        "input_sha256": {key: snapshot.manifest["files"][key]["sha256"]
                         for key in ("calendar", "membership", "symbols_listed", "symbols_delisted")},
        "seal_sha256": sha256_bytes((root / snapshot.seal_file).read_bytes()),
        "output_sha256": dict(sorted(outputs.items())),
        "discovery_inputs_sha256": inputs_sha,
    }
    if v2:
        del build_manifest["discovery_window"]
        build_manifest.update(_v2_build_fields(snapshot, calendar, segments, d0_pre, roles))
    write_bytes(root / BUILD_MANIFEST, canonical_json(build_manifest))
    return build_manifest


def _v2_build_fields(
    snapshot: Snapshot, calendar: pd.DatetimeIndex, segments: tuple[Segment, ...], d0_pre: date | None,
    roles: dict[str, str],
) -> dict[str, Any]:
    """Rule v2 build-manifest fields: segments, validation rules, volume basis, and the access log."""
    volume_basis = {code: str((snapshot.entry("eod", code) or {}).get("pre_side_volume_basis", "absent"))
                    for code in roles}
    opens: dict[str, int] = {}
    for record in snapshot.access_log:
        key = f"{record['table']}/{record['side']}"
        opens[key] = opens.get(key, 0) + 1
    return {
        "schema_version": "m4_8_membership_build_manifest_v2",
        "membership_availability_basis": "effective_date_as_known_at_v1",
        "partition_rule": snapshot.partition_rule,
        "discovery_layout": "side_partitioned_discovery_v1",
        "holdout_start": None if snapshot.holdout_start is None else snapshot.holdout_start.isoformat(),
        "d0_pre": None if d0_pre is None else d0_pre.isoformat(),
        "segments": [{"segment_id": s.segment_id, "side": s.side, "anchor_row": _date(calendar, s.anchor_row),
                      "first_reset_row": _date(calendar, s.first_reset_row),
                      "last_ic_reset_row": _date(calendar, s.last_ic_reset_row),
                      "last_book_row": _date(calendar, s.last_book_row),
                      "feature_floor_row": _date(calendar, s.feature_floor_row),
                      "feature_ceiling_row": _date(calendar, s.feature_ceiling_row),
                      "ic_months": int(len(segment_ic_resets(calendar, s)))} for s in segments],
        "universe_validation": ["segment_anchor_normalized_basis_v1", "seal_gap_identity_split_v1",
                                "pre_seal_volume_share_basis_v1"],
        "pre_side_volume_basis_by_code": dict(sorted(volume_basis.items())),
        "access_log": {"opens_by_table_and_side": dict(sorted(opens.items())),
                       "holdout_partition_opens": sum(1 for r in snapshot.access_log if r["side"] == "holdout")},
    }


def exit_class(last_bar: int, r_exit: int, d_last: int) -> str:
    """C54: exactly one class per resolved interval."""
    if last_bar >= d_last:
        return "index_removal_still_trading"
    if last_bar < r_exit:
        return "delisting_candidate"
    return "disappearance_outside_membership"


def _member_days(entry: dict[str, Any], spans: list[tuple[int, int]], n_rows: int) -> int:
    """Member-days inside the discovery spans ``[first, last]`` (one span under rule v1, one per segment under v2)."""
    m_out = n_rows if entry["m_out"] is None else entry["m_out"]
    return sum(max(0, min(m_out, last + 1) - max(entry["m_in"], first)) for first, last in spans)


def _set_rows(
    entry: dict[str, Any], rs: int, re_: int, end: date | None, resets: np.ndarray, d_last: int, n_rows: int,
    spans: list[tuple[int, int]], bar_rows: np.ndarray,
) -> None:
    """Boundary rows of a seal-split interval piece ``[rs, re_)`` (SL-5), by the rules of the vendor entries."""
    exit_reset = None if end is None else _first_reset_at_or_after(resets, re_ + 1)
    entry.update(rs=rs, re=re_, m_in=rs + 1, m_out=None if end is None else re_ + 1,
                 R_entry=_first_reset_at_or_after(resets, rs + 1), R_exit=d_last if exit_reset is None else exit_reset,
                 bars_in_span=int(((bar_rows >= rs) & (bar_rows < re_)).sum()))
    entry["member_days_disc"] = _member_days(entry, spans, n_rows)


def _symbol_map(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for row in frame.to_dict(orient="records"):
        code = row.get("Code")
        if isinstance(code, str) and code and f"{code}.US" not in mapping:
            isin = row.get("Isin")
            mapping[f"{code}.US"] = {"isin": None if _blank(isin) else str(isin), "name": row.get("Name")}
    return mapping


def _discovery_bars(
    snapshot: Snapshot, code: str, calendar_set: dict[pd.Timestamp, int], side: str = "discovery",
) -> pd.DataFrame | None:
    frame = snapshot.read_discovery("eod", code, side)
    if frame is None:
        return None
    frame = frame.assign(date=pd.DatetimeIndex(frame["date"])).set_index("date")
    return frame[frame.index.isin(list(calendar_set))]


def _e3_fires(code_entries: list[dict[str, Any]], eps: list[Episode]) -> bool:
    """E3: two differently named entries whose own spans hold bars of one E1 episode (C87 for copies)."""
    by_key = {e["interval_id"]: e for e in code_entries}
    for e in code_entries:
        if e["duplicate_of"]:
            kept = by_key.get(e["duplicate_of"])
            if kept is not None and normalize_name(kept["name"]) != normalize_name(e["name"]) and (kept["bars_in_span"] or 0) > 0:
                return True
    touched = []
    for e in code_entries:
        if e["duplicate_of"] or e["resolution"] in ("raw_overlap", "degenerate_interval"):
            continue
        episodes = {ep.k for ep in eps if ((ep.rows >= e["rs"]) & (ep.rows < e["re"])).any()}
        touched.append((normalize_name(e["name"]), episodes))
    return any(
        left[0] != right[0] and left[1] & right[1]
        for i, left in enumerate(touched) for right in touched[i + 1:]
    )


def _e5_fires(
    eps: list[Episode],
    sides: list[tuple[int, int, pd.DataFrame | None, pd.DataFrame | None]],
    calendar: pd.DatetimeIndex,
) -> tuple[bool, int]:
    """E5 over each in-episode gap whose endpoints lie on one discovery side ``[lo, hi)`` (SL-4).

    ``sides`` holds ``(lo, hi, eod_frame, split_frame)`` per side. A gap with an
    endpoint outside every side (a holdout row) is skipped and counted.
    """
    skipped = 0
    for ep in eps:
        gaps = np.flatnonzero(np.diff(ep.rows) > 1)
        for j in gaps:
            a, b = int(ep.rows[j]), int(ep.rows[j + 1])
            side = next(((frame, splits) for lo, hi, frame, splits in sides if lo <= a and b < hi), None)
            if side is None:
                skipped += 1
                continue
            frame, splits = side
            if frame is None:
                continue
            split_rows = [] if splits is None else [_row(calendar, day) for day in pd.DatetimeIndex(splits["date"])]
            ratio = frame.loc[calendar[b], "adjusted_close"] / frame.loc[calendar[a], "adjusted_close"]
            near = any(a - E5_SPLIT_WINDOW_ROWS <= r <= b + E5_SPLIT_WINDOW_ROWS for r in split_rows)
            if abs(math.log(ratio)) > E5_LOG_THRESHOLD and not near:
                return True, skipped
    return False, skipped


def _new_counters() -> dict[str, Any]:
    return {
        "split_basis_check_by_outcome": dict.fromkeys(
            ("unapplied_exact", "applied_exact", "refused", "not_evaluated_no_discovery_bar"), 0),
        "split_basis_refusals_with_later_distribution": 0,
        "in_span_step_check_by_outcome": dict.fromkeys(
            ("passed", "mismatch", "cumulative_drift", "not_evaluated_split_basis_refused",
             "not_evaluated_no_discovery_bar"), 0),
        "written_max_cumulative_drift_by_bucket": dict.fromkeys(("[0,1e-4]", "(1e-4,1e-3]", "(1e-3,2e-3]"), 0),
        "failing_pairs_by_kind": dict.fromkeys(("declared_split_pair", "declared_dividend_pair", "undeclared_step"), 0),
        "failing_pairs_by_residual_bucket": dict.fromkeys(("(1e-3,1e-2]", "(1e-2,0.15]", ">0.15"), 0),
        "split_rows_unattributed": 0,
        "split_rows_after_final_bar": dict.fromkeys(
            ("excluded_unapplied", "attributed_applied", "refused", "not_evaluated_no_discovery_bar"), 0),
        "split_rows_before_first_bar": {},
        "dividend_rows_amount_undefined": 0,
    }


def residual_bucket(residual: float | None) -> str:
    """Failing-pair residual bucket; an undefined residual (undefined amount) counts above 0.15."""
    if residual is None:
        return ">0.15"
    return "(1e-3,1e-2]" if residual <= 1e-2 else "(1e-2,0.15]" if residual <= 0.15 else ">0.15"


def _record_check(ep: Episode, check: EpisodeCheck, counters: dict[str, Any], final: bool, post_rows: int,
                  dividend_ok: bool, prefix: str = "") -> None:
    basis = counters["split_basis_check_by_outcome"]
    if check.split_basis == "refused":
        basis["refused"] += 1
        counters["split_basis_refusals_with_later_distribution"] += int(check.later_distribution)
        counters["in_span_step_check_by_outcome"]["not_evaluated_split_basis_refused"] += 1
    else:
        basis["applied_exact" if check.split_basis == "applied" else "unapplied_exact"] += 1
        counters["in_span_step_check_by_outcome"][check.in_span] += 1
    if final and post_rows:
        disposition = check.outcome if check.outcome in ("excluded_unapplied", "attributed_applied") else "refused"
        if check.split_basis == "refused":
            disposition = "refused"
        counters["split_rows_after_final_bar"][disposition] += post_rows
    for pair in check.failing:
        counters["failing_pairs_by_kind"][pair["kind"]] += 1
        counters["failing_pairs_by_residual_bucket"][residual_bucket(pair["residual"])] += 1
    counters["dividend_rows_amount_undefined"] += check.undefined_amounts
    evidence = (f"split_basis:{check.split_basis}:g={check.g:.9g}:rho={check.rho:.9g}"
                f":later_distribution={str(check.later_distribution).lower()}"
                f":dividend_evidence={'valid' if dividend_ok else 'unavailable'}")
    if final and post_rows:
        evidence += f":post_final_bar={check.outcome}"
    ep.evidence.append(prefix + evidence)
    if check.split_basis == "refused":
        return
    in_span = (f"in_span_steps:{check.in_span}:pairs={check.pairs}:dividend_pairs={check.dividend_pairs}"
               f":failing_pairs={len(check.failing)}:max_residual={min(check.max_residual, 1e9):.6g}"
               f":max_cumulative_drift={check.max_cumulative_drift:.6g}")
    if check.failing:
        first = check.failing[0]
        in_span += f":first_failing={first['date_a']}..{first['date_b']}:{first['kind']}"
    elif check.drift_date:
        in_span += f":largest_drift_row={check.drift_date}"
    ep.evidence.append(prefix + in_span)
    if check.refusal is None:
        drift = check.max_cumulative_drift
        bucket = "[0,1e-4]" if drift <= 1e-4 else "(1e-4,1e-3]" if drift <= 1e-3 else "(1e-3,2e-3]"
        counters["written_max_cumulative_drift_by_bucket"][bucket] += 1
        if check.dividend_pairs:
            ep.evidence.append(f"{prefix}distribution_support:max_b_d={check.b_d[0]:.6f}:max_s_d={check.s_d[0]:.6f}")


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def census_cap(resolution: str) -> str:
    if resolution in ("resolved", "exact_duplicate_collapsed", "degenerate_interval"):
        return "none"
    if resolution in ("raw_overlap", "entry_missing_field", "entry_unparseable_date") or resolution.startswith(NO_BARS_CAPPED):
        return "R-CENSUS-9"
    return "R-CENSUS-3"


def _interval_frame(entries: list[dict[str, Any]], calendar: pd.DatetimeIndex) -> pd.DataFrame:
    rows = []
    for e in entries:
        rows.append({
            **{column: e.get(column, "") for column in INTERVAL_COLUMNS},
            "resolution_evidence": ";".join(e["evidence"]),
            "m_in": _date(calendar, e["m_in"]), "m_out": _date(calendar, e["m_out"]),
            "R_entry": _date(calendar, e["R_entry"]), "R_exit": _date(calendar, e["R_exit"]),
            "census_cap": census_cap(e["resolution"]),
        })
    return pd.DataFrame(rows, columns=list(INTERVAL_COLUMNS))


def _constituent_csv(entries: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for e in entries:
        if e["resolution"] != "resolved":
            continue
        end = "" if e["end"] is None else e["end"].isoformat()
        rows.append({"symbol": e["vendor_code"], "permanent_id": e["permanent_id"],
                     "start_date": e["start"].isoformat(), "end_date": end,
                     "start_known_at": e["start"].isoformat(), "end_known_at": end})
    return pd.DataFrame(rows, columns=["symbol", "permanent_id", "start_date", "end_date", "start_known_at", "end_known_at"])


def _round_trip_intervals(path: Path, entries: list[dict[str, Any]], calendar: pd.DatetimeIndex) -> None:
    """Step 5: the M4.4 loader and mask are the oracle for ``m_in`` and ``m_out`` (T-UNI-12)."""
    resolved = [e for e in entries if e["resolution"] == "resolved"]
    if not resolved:
        return
    table = load_constituent_intervals_csv(path)
    assets = sorted({e["permanent_id"] for e in resolved})
    mask = build_pit_membership_mask(table, calendar, assets, signal_lag_periods=1)
    expected = pd.DataFrame(False, index=calendar, columns=assets)
    for e in resolved:
        m_out = len(calendar) if e["m_out"] is None else e["m_out"]
        expected.iloc[e["m_in"]:m_out, assets.index(e["permanent_id"])] = True
    if not mask.iloc[1:].equals(expected.iloc[1:]):
        raise SnapshotRefusal("interval_boundary_mismatch", "mask rows differ from calendar-row boundaries")


def _master_frame(
    episodes: dict[str, list[Episode]], calendar: pd.DatetimeIndex, snapshot: Snapshot,
    listed: dict[str, dict[str, Any]], delisted: dict[str, dict[str, Any]], entries: list[dict[str, Any]],
) -> pd.DataFrame:
    rows = []
    for code, eps in episodes.items():
        symbol = listed.get(code) or delisted.get(code) or {}
        isin = (listed.get(code, {}).get("isin") or delisted.get(code, {}).get("isin") or "")
        for ep in eps:
            names = [e["name"] for e in ep.intervals if isinstance(e.get("name"), str)]
            rows.append({
                "permanent_id": ep.permanent_id, "vendor_code": code, "episode": ep.k,
                "vendor_name": names[0] if names else (symbol.get("name") or ""), "isin": isin, "role": ep.role,
                "first_bar": _date(calendar, ep.first), "last_bar": _date(calendar, ep.last),
                "bar_count": int(ep.rows.size), "resolution": ep.resolution,
                "resolution_evidence": ";".join(ep.evidence), "eod_status": snapshot.status("eod", code),
                "eod_discovery_status": snapshot.discovery_status("eod", code),
                "episode_panel_refusal": ep.panel_refusal,
                "interval_count": sum(1 for e in entries if ep.permanent_id and e["permanent_id"] == ep.permanent_id),
                "has_delisting_candidate_interval": any(
                    e["exit_class"] == "delisting_candidate" for e in entries
                    if ep.permanent_id and e["permanent_id"] == ep.permanent_id),
            })
    return pd.DataFrame(rows, columns=list(MASTER_COLUMNS))


# ---------------------------------------------------------------- command line


def snapshot_dir_from_args(args: argparse.Namespace) -> Path:
    raw = args.data_dir or os.environ.get(DATA_DIR_ENV, "")
    if not raw.strip():
        raise SnapshotRefusal("data_dir_missing", f"{DATA_DIR_ENV} or --data-dir is required")
    return Path(raw).expanduser().resolve() / f"sp500_pit_{args.snapshot_id}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m research.m4_7_universe_build")
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--d0-pre", type=date.fromisoformat, default=None,
                        help="D0_pre from the membership census; required for a rule v2 snapshot")
    args = parser.parse_args(argv)
    try:
        manifest = build_universe(snapshot_dir_from_args(args), args.d0_pre)
    except SnapshotRefusal as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"interval_resolution_counts": manifest["interval_resolution_counts"],
                      "episode_panel_refusal_counts": manifest["episode_panel_refusal_counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
