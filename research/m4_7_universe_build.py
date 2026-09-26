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

Run as ``python -m research.m4_7_universe_build --snapshot-id <ID>``.
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
    SEAL_FILE,
    SnapshotRefusal,
    classify_membership_entries,
    parse_strict_date,
    read_authorized_bytes,
    read_manifest,
    read_seal,
    sha256_bytes,
)
from data.parquet_loader import compute_cumulative_split_factor, load_symbol_splits
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
    """A snapshot directory, its manifest, and the sealed ``holdout_end`` and ``calendar_source``."""

    root: Path
    manifest: dict[str, Any]
    holdout_end: date
    calendar_source: str

    @classmethod
    def open(cls, root: Path | str) -> "Snapshot":
        root = Path(root)
        seal = read_seal(root)
        return cls(root=root, manifest=read_manifest(root), holdout_end=date.fromisoformat(seal["holdout_end_exclusive"]),
                   calendar_source=seal["calendar_source"])

    def entry(self, table: str, code: str) -> dict[str, Any] | None:
        return self.manifest.get("entries", {}).get(f"{table}/{code}")

    def status(self, table: str, code: str) -> str:
        entry = self.entry(table, code)
        return "absent" if entry is None else str(entry["status"])

    def discovery_status(self, table: str, code: str) -> str:
        entry = self.entry(table, code)
        return "" if entry is None else str(entry.get("partition_statuses", {}).get("discovery", ""))

    def evidence_valid(self, table: str, code: str) -> bool:
        """``retrieved`` with a valid discovery partition: readable corporate-action evidence."""
        return self.status(table, code) == "retrieved" and self.discovery_status(table, code) == "valid"

    def read_discovery(self, table: str, code: str) -> pd.DataFrame | None:
        """The discovery partition of ``table`` for ``code``, or ``None`` when it has no valid file."""
        entry = self.entry(table, code)
        if entry is None or "discovery" not in entry.get("authorized_files", {}):
            return None
        record = entry["authorized_files"]["discovery"]
        return _parquet(read_authorized_bytes(self.root, record["path"], self.manifest), record["path"])

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
            rows.append([code, table, entry.get("status", "absent"),
                         roles.get("dates", {}).get("sha256"), roles.get("discovery", {}).get("sha256")])
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
    """``(i_H, D0, D_last)`` as rows of the full calendar (plan 4.1)."""
    i_h = int(calendar.searchsorted(pd.Timestamp(holdout_end)))
    resets = scheduled_reset_rows(calendar)
    d_last = int(resets[-1]) if len(resets) else len(calendar) - 1
    later = resets[resets >= i_h + WARMUP_ROWS + 1]
    d0 = int(later[0]) if len(later) else d_last + 1
    return i_h, d0, d_last


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


def build_universe(snapshot_dir: Path | str) -> dict[str, Any]:
    """Run plan 1.6 steps 1-7 on the snapshot and write every universe artifact."""
    snapshot = Snapshot.open(snapshot_dir)
    root = snapshot.root
    calendar = snapshot.calendar()
    n_rows = len(calendar)
    i_h, d0, d_last = discovery_window(calendar, snapshot.holdout_end)
    resets = scheduled_reset_rows(calendar)
    retrieved = snapshot.components_retrieved()
    membership = snapshot.read_file("membership")
    records = classify_membership_entries(membership, retrieved)
    keys = interval_keys(membership, records)
    raw_rows = membership["raw_row"].tolist() if "raw_row" in membership else list(range(len(membership)))
    listed = _symbol_map(snapshot.read_file("symbols_listed"))
    delisted = _symbol_map(snapshot.read_file("symbols_delisted"))
    inputs_sha = discovery_inputs_sha256(snapshot, membership)

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
        off_calendar[code] = int(sum(1 for d, keep in zip(dates, inside) if keep and d not in calendar_set))
    episodes = {code: _episodes(code_rows[code], code, roles[code]) for code in roles}

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
                entry["member_days_disc"] = _member_days(entry, d0, d_last, n_rows)
            continue
        entry["member_days_disc"] = _member_days(entry, d0, d_last, n_rows)
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
        if len(touched) > 1:
            entry["resolution"] = "ambiguous_reuse_gap"
        elif rs < touched[0].first - E1_GAP_ROWS:
            entry["resolution"] = "no_containing_episode"
        else:
            entry["resolution"] = "resolved"
            entry["episode"] = touched[0]
            touched[0].intervals.append(entry)

    # Code-level rules E3-E6 (C60); rule E5 reads discovery values and attributed split rows.
    split_frames = {code: (snapshot.read_discovery("splits", code) if snapshot.evidence_valid("splits", code) else None)
                    for code in roles}
    eod_frames: dict[str, pd.DataFrame | None] = {}
    e5_not_evaluated: dict[str, int] = {}
    name_mismatches = 0
    for code in roles:
        code_entries = [e for e in entries if e["vendor_code"] == code and e["start"] is not None]
        fired: list[tuple[str, str]] = []
        eps = episodes[code]
        continuous = len(eps) == 1
        if eps:
            if _e3_fires(code_entries, eps):
                fired.append(("E3", "ambiguous_reuse_continuous_history"))
            isin_l, isin_d = listed.get(code, {}).get("isin"), delisted.get(code, {}).get("isin")
            if isin_l and isin_d and isin_l != isin_d and continuous:
                fired.append(("E4", "ambiguous_reuse_isin_conflict"))
            eod_frames[code] = _discovery_bars(snapshot, code, calendar_set)
            e5, skipped = _e5_fires(eps, eod_frames[code], split_frames[code], calendar, i_h)
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
            e["exit_class"] = exit_class(ep.last, e["R_exit"], d_last)

    # Step 6: split-basis, in-span, cumulative, and gap checks; panel write (C45, C55, C67, C72, C73, C82).
    panel_root = root / PANEL_DIR
    shutil.rmtree(panel_root / "discovery", ignore_errors=True)
    counters = _new_counters()
    episode_checks: list[dict[str, Any]] = []
    support_frames: list[pd.DataFrame] = []
    written: dict[str, str] = {}
    for code, eps in episodes.items():
        splits = split_frames[code]
        split_dates = pd.DatetimeIndex([]) if splits is None else pd.DatetimeIndex(splits["date"])
        ratios = pd.DataFrame({"date": split_dates, "ratio": [] if splits is None else splits["ratio"].astype(float)})
        dividend_ok = snapshot.evidence_valid("dividends", code)
        dividends = dividend_amounts(snapshot.read_discovery("dividends", code) if dividend_ok else None, split_dates)
        bar_dates = [(calendar[ep.first], calendar[ep.last]) for ep in eps]
        attributed: dict[int, list[int]] = {ep.k: [] for ep in eps}
        gap_rows: dict[int, int] = {}
        post_final = []
        for index, day in enumerate(split_dates):
            spot = next((k for k, (first, last) in enumerate(bar_dates) if first <= day <= last), None)
            if spot is not None:
                attributed[eps[spot].k].append(index)
            elif eps and day > bar_dates[-1][1]:
                post_final.append(index)
            elif eps and day < bar_dates[0][0]:
                counters["split_rows_before_first_bar"][code] = counters["split_rows_before_first_bar"].get(code, 0) + 1
            elif eps:
                preceding = max(k for k, (_, last) in enumerate(bar_dates) if last < day)
                gap_rows[eps[preceding].k] = gap_rows.get(eps[preceding].k, 0) + 1
                counters["split_rows_unattributed"] += 1
        frame = eod_frames.get(code)
        for ep in eps:
            if ep.resolution != "resolved":
                continue
            final = ep is eps[-1]
            has_discovery_bar = ep.last >= i_h
            if not has_discovery_bar:
                ep.evidence.append("split_basis:not_evaluated:no_discovery_bar")
                counters["split_basis_check_by_outcome"]["not_evaluated_no_discovery_bar"] += 1
                counters["in_span_step_check_by_outcome"]["not_evaluated_no_discovery_bar"] += 1
                if final and post_final:
                    counters["split_rows_after_final_bar"]["not_evaluated_no_discovery_bar"] += len(post_final)
                continue
            if frame is None:
                ep.evidence.append(f"split_basis:not_evaluated:discovery_partition_{snapshot.discovery_status('eod', code) or 'missing'}")
                continue
            bars = frame[(frame.index >= calendar[max(ep.first, i_h)]) & (frame.index <= calendar[ep.last])]
            after_last = split_dates > calendar[ep.last]
            check = evaluate_episode(
                bars, ratios.iloc[attributed[ep.k]], ratios[after_last], dividends,
                dividend_evidence=dividend_ok, final=final, gap_split_after=ep.k in gap_rows,
            )
            _record_check(ep, check, counters, final, len(post_final), dividend_ok)
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
            })
            if check.refusal is not None:
                ep.panel_refusal = check.refusal
                continue
            panel = frame.loc[bars.index].reset_index()
            panel["symbol"] = code
            panel["permanent_id"] = ep.permanent_id
            panel["split_factor"] = check.factor.to_numpy()
            relative = f"discovery/{ep.permanent_id}.parquet"
            written[ep.permanent_id] = write_bytes(panel_root / relative, parquet_bytes(panel))
            if check.dividend_pairs:
                support_frames.append(pd.DataFrame({"permanent_id": ep.permanent_id, "date": bars.index,
                                                    "b_d": check.b_d, "s_d": check.s_d}))

    for pid in sorted(written):
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
        "files": [{"symbol": pid, "file": f"discovery/{pid}.parquet", "sha256": written[pid]} for pid in sorted(written)],
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
        "seal_sha256": sha256_bytes((root / SEAL_FILE).read_bytes()),
        "output_sha256": dict(sorted(outputs.items())),
        "discovery_inputs_sha256": inputs_sha,
    }
    write_bytes(root / BUILD_MANIFEST, canonical_json(build_manifest))
    return build_manifest


def exit_class(last_bar: int, r_exit: int, d_last: int) -> str:
    """C54: exactly one class per resolved interval."""
    if last_bar >= d_last:
        return "index_removal_still_trading"
    if last_bar < r_exit:
        return "delisting_candidate"
    return "disappearance_outside_membership"


def _member_days(entry: dict[str, Any], d0: int, d_last: int, n_rows: int) -> int:
    m_out = n_rows if entry["m_out"] is None else entry["m_out"]
    return max(0, min(m_out, d_last + 1) - max(entry["m_in"], d0))


def _symbol_map(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for row in frame.to_dict(orient="records"):
        code = row.get("Code")
        if isinstance(code, str) and code and f"{code}.US" not in mapping:
            isin = row.get("Isin")
            mapping[f"{code}.US"] = {"isin": None if _blank(isin) else str(isin), "name": row.get("Name")}
    return mapping


def _discovery_bars(snapshot: Snapshot, code: str, calendar_set: dict[pd.Timestamp, int]) -> pd.DataFrame | None:
    frame = snapshot.read_discovery("eod", code)
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
    eps: list[Episode], frame: pd.DataFrame | None, splits: pd.DataFrame | None,
    calendar: pd.DatetimeIndex, i_h: int,
) -> tuple[bool, int]:
    split_rows = [] if splits is None else [_row(calendar, day) for day in pd.DatetimeIndex(splits["date"])]
    skipped = 0
    for ep in eps:
        gaps = np.flatnonzero(np.diff(ep.rows) > 1)
        for j in gaps:
            a, b = int(ep.rows[j]), int(ep.rows[j + 1])
            if a < i_h:
                skipped += 1
                continue
            if frame is None:
                continue
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
                  dividend_ok: bool) -> None:
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
    ep.evidence.append(evidence)
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
    ep.evidence.append(in_span)
    if check.refusal is None:
        drift = check.max_cumulative_drift
        bucket = "[0,1e-4]" if drift <= 1e-4 else "(1e-4,1e-3]" if drift <= 1e-3 else "(1e-3,2e-3]"
        counters["written_max_cumulative_drift_by_bucket"][bucket] += 1
        if check.dividend_pairs:
            ep.evidence.append(f"distribution_support:max_b_d={check.b_d[0]:.6f}:max_s_d={check.s_d[0]:.6f}")


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
    args = parser.parse_args(argv)
    try:
        manifest = build_universe(snapshot_dir_from_args(args))
    except SnapshotRefusal as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"interval_resolution_counts": manifest["interval_resolution_counts"],
                      "episode_panel_refusal_counts": manifest["episode_panel_refusal_counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
