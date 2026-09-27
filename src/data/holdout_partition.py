"""Prospective holdout seal from raw S&P 500 membership counts (M4.7 plan 1.4).

The seal is derived from membership metadata only: the raw components table
``membership/historical_components_raw.parquet`` and the scalar
``snapshot.components_retrieved_utc_date`` from ``manifest.json``. No price,
split, dividend, or index-level file is read, and the window is derived
without the wall clock, so unchanged inputs yield the same window.

This module also holds the network-free half of the snapshot contract (plan
1.3, S7): strict ``YYYY-MM-DD`` parsing, the partition rules, and
manifest-authorized, hash-verified reads. It opens no network connection.

Partition rule v1 (``real_v1``) makes every row before ``holdout_end``
holdout. Partition rule v2 (M4.8 plan 2.2, ``sealed_window_only_partition_v2``)
makes only ``[holdout_start, holdout_end)`` holdout and writes discovery rows to
two side files, ``discovery_pre`` and ``discovery_post``. A v2 snapshot carries
the seal v1 window through ``holdout_seal_v2.json``
(``carried_forward_sealed_window_v1``); the carried window comes from the seal
v1 bytes only, so no count-based derivation may run on such a snapshot
(``seal_window_recompute_forbidden``).
"""

from __future__ import annotations

import calendar
import hashlib
import io
import json
import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


SEAL_FILE = "holdout_seal_v1.json"
SEAL_CARRY_FILE = "holdout_seal_v2.json"
SEAL_CARRY_SCHEMA_VERSION = "m4_8_holdout_seal_carry_v2"
SEAL_CARRY_RULE = "carried_forward_sealed_window_v1"
# Plan 2.2: the carry record binds these three hashes. The first two docs files
# are committed; the prospective file lives in the private real_v1 snapshot.
SEAL_V1_DOCS_PATH = "docs/preregistrations/m4_7_holdout_seal_v1.json"
SEAL_V1_DOCS_SHA256 = "b7f9380fa5f128c65966a2984f2a81b635b3f3777f32878270fc977a93bff506"
SEAL_V1_PROSPECTIVE_SHA256 = "93ce6e5ad003927dbf7f1521c26aca6a17844cb3061a44f7885a5584612e9882"
SEAL_V1_CONFIRMATION_V2_PATH = "docs/preregistrations/m4_7_holdout_seal_v1_confirmation_v2.json"
SEAL_V1_CONFIRMATION_V2_SHA256 = "8e9e7b0267d689d9bef22ef681aac3b18230373724fe3f0f6cf4e6fa209388ae"
# The window those bytes hold; every carry record read must restate it (a forged window refuses).
SEAL_V1_WINDOW = {"holdout_start": "2019-07-31", "holdout_end_exclusive": "2020-07-31",
                  "calendar_source": "SPY.US_eod_dates_v1"}
PARTITION_RULE_V1 = "holdout_before_holdout_end_partition_v1"
PARTITION_RULE_V2 = "sealed_window_only_partition_v2"
DISCOVERY_LAYOUT_V2 = "side_partitioned_discovery_v1"
PRE_SIDE_VOLUME_BASIS = "pre_seal_volume_share_basis_v1"
SIDES = ("discovery_pre", "discovery_post")
MANIFEST_FILE = "manifest.json"
MEMBERSHIP_FILE = "membership/historical_components_raw.parquet"
SEAL_SCHEMA_VERSION = "m4_7_holdout_seal_v1"
SEAL_RULE_VERSION = "earliest_available_decade_from_raw_membership_counts_v1"
SEAL_RULE_OPTION_A = "earliest_available_year_from_raw_membership_counts_option_a_v1"
COVERAGE_START_RULE = "coverage_start_tolerant_3_isolated_v1"
BAND = (470, 530)
HARD_BAND = (450, 560)
TOLERANCE_EXCEPTIONS = 3
# Parameters per seal rule. The v1 decade rule is the plan 1.4 default. Option A
# (owner decision O-3, 2026-09-26) fits the 2019-2026 in-band history of the local
# EODHD components response: a one-year holdout, no prior-exposure cap (the overlap
# is stated in the seal record), and census minima of 7 in-band years (1 holdout,
# 1 warm-up, 5 discovery) and 48 IC months. ``accepted_shortfall`` holds the bounds
# the owner accepted under O-7 (2026-09-26) after the first Option A census: a
# census value that misses its registered threshold but stays inside these bounds
# reads ``ready_with_caveats:coverage_shortfall_accepted`` instead of ``blocked``.
SEAL_RULES: dict[str, dict[str, Any]] = {
    SEAL_RULE_VERSION: {"holdout_years": 10, "latest_holdout_end": date(2014, 1, 1),
                        "min_in_band_years": 16, "min_ic_months": 60, "accepted_shortfall": None},
    SEAL_RULE_OPTION_A: {"holdout_years": 1, "latest_holdout_end": None,
                         "min_in_band_years": 7, "min_ic_months": 48,
                         "accepted_shortfall": {"owner_decision": "O-7 2026-09-26", "min_in_band_years": 6.9,
                                                "min_ic_months": 32, "max_gap_windows": 25,
                                                "max_excluded_fraction": 0.45, "max_unpriced_fraction": 0.40}},
}
DEFAULT_CALENDAR_SOURCE = "GSPC.INDX_eod_dates_v1"
RETRIEVAL_ORDER = (
    "components",
    "symbols",
    "seal",
    "calendar",
    "splits",
    "eod",
    "dividends",
    "verify",
)

_STRICT_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ENTRY_FIELDS = ("Code", "Name", "StartDate", "EndDate", "IsActiveNow", "IsDelisted")


class SnapshotRefusal(RuntimeError):
    """A typed refusal of a snapshot operation; ``code`` is the typed reason."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def parse_strict_date(value: Any) -> date | None:
    """Return the date for a strict ``YYYY-MM-DD`` string, else ``None``."""

    if not isinstance(value, str) or not _STRICT_DATE.match(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def partition_of(day: date, holdout_end: date) -> str:
    """Rule v1: rows dated before ``holdout_end`` are holdout; the rest are discovery."""

    return "holdout" if day < holdout_end else "discovery"


def side_of(day: date, holdout_start: date, holdout_end: date) -> str:
    """Rule v2 (plan 2.2): ``holdout`` inside the seal window, else the discovery side file."""

    if day < holdout_start:
        return "discovery_pre"
    return "holdout" if day < holdout_end else "discovery_post"


@dataclass(frozen=True)
class PartitionWindow:
    """The seal window a snapshot partitions on, and the rule that reads it."""

    rule: str
    holdout_start: date
    holdout_end: date
    calendar_source: str
    seal_file: str

    @property
    def partitions(self) -> tuple[str, ...]:
        return rule_partitions(self.rule)

    def partition(self, day: date) -> str:
        if self.rule == PARTITION_RULE_V1:
            return partition_of(day, self.holdout_end)
        return side_of(day, self.holdout_start, self.holdout_end)


def rule_partitions(rule: str) -> tuple[str, ...]:
    """Partition file roles per rule: one discovery file under v1, two side files under v2."""

    return ("discovery", "holdout") if rule == PARTITION_RULE_V1 else (*SIDES, "holdout")


def declared_partition_rule(manifest: dict[str, Any]) -> str:
    """The manifest's declared rule; a snapshot that declares none uses rule v1 (plan 2.2)."""

    rule = manifest.get("snapshot", {}).get("partition_rule", PARTITION_RULE_V1)
    if rule not in (PARTITION_RULE_V1, PARTITION_RULE_V2):
        raise SnapshotRefusal("partition_rule_unknown", str(rule))
    return rule


def read_partition_window(snapshot_dir: Path, manifest: dict[str, Any] | None = None) -> PartitionWindow:
    """Dispatch on the seal file: the carry record selects rule v2, the v1 seal rule v1.

    With ``manifest``, the manifest's declared rule must agree with the seal
    (``partition_rule_mismatch``); downstream readers pass it, the partitioner
    records the declaration before it partitions.
    """

    root = Path(snapshot_dir)
    if (root / SEAL_CARRY_FILE).is_file() and (root / SEAL_FILE).is_file():
        raise SnapshotRefusal("holdout_seal_ambiguous", f"{SEAL_FILE} and {SEAL_CARRY_FILE}")
    if (root / SEAL_CARRY_FILE).is_file():
        record = read_seal_carry(root)
        window = PartitionWindow(PARTITION_RULE_V2, date.fromisoformat(record["holdout_start"]),
                                 date.fromisoformat(record["holdout_end_exclusive"]), record["calendar_source"],
                                 SEAL_CARRY_FILE)
    else:
        record = read_seal(root)
        window = PartitionWindow(PARTITION_RULE_V1, date.fromisoformat(record["holdout_start"]),
                                 date.fromisoformat(record["holdout_end_exclusive"]), record["calendar_source"],
                                 SEAL_FILE)
    if manifest is not None and declared_partition_rule(manifest) != window.rule:
        raise SnapshotRefusal("partition_rule_mismatch",
                              f"manifest declares {declared_partition_rule(manifest)}, seal selects {window.rule}")
    return window


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_manifest(snapshot_dir: Path) -> dict[str, Any]:
    path = Path(snapshot_dir) / MANIFEST_FILE
    if not path.is_file():
        raise SnapshotRefusal("manifest_missing", str(MANIFEST_FILE))
    return json.loads(path.read_bytes())


def authorized_records(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map every manifest-authorized relative path to its ``{path, sha256}`` record."""

    records: dict[str, dict[str, Any]] = {}
    for record in manifest.get("files", {}).values():
        records[record["path"]] = record
    for entry in manifest.get("entries", {}).values():
        for record in entry.get("authorized_files", {}).values():
            records[record["path"]] = record
    return records


def read_authorized_bytes(
    snapshot_dir: Path,
    relative_path: str,
    manifest: dict[str, Any] | None = None,
) -> bytes:
    """Read a retrieval artifact only through its manifest role, hash first.

    A path no role names refuses ``artifact_not_authorized``; bytes that differ
    from the recorded SHA-256 refuse ``artifact_hash_mismatch``.
    """

    manifest = read_manifest(snapshot_dir) if manifest is None else manifest
    record = authorized_records(manifest).get(relative_path)
    if record is None:
        raise SnapshotRefusal("artifact_not_authorized", relative_path)
    path = Path(snapshot_dir) / relative_path
    payload = path.read_bytes() if path.is_file() else b""
    if not path.is_file() or sha256_bytes(payload) != record["sha256"]:
        raise SnapshotRefusal("artifact_hash_mismatch", relative_path)
    return payload


def read_authorized_parquet(
    snapshot_dir: Path,
    relative_path: str,
    manifest: dict[str, Any] | None = None,
) -> pd.DataFrame:
    payload = read_authorized_bytes(snapshot_dir, relative_path, manifest)
    return pd.read_parquet(io.BytesIO(payload), engine="pyarrow")


def read_seal(snapshot_dir: Path) -> dict[str, Any]:
    """Return the seal record; refuse when no well-formed seal exists."""

    path = Path(snapshot_dir) / SEAL_FILE
    if not path.is_file():
        raise SnapshotRefusal("holdout_seal_missing", SEAL_FILE)
    record = json.loads(path.read_bytes())
    holdout_end = parse_strict_date(record.get("holdout_end_exclusive"))
    if record.get("schema_version") != SEAL_SCHEMA_VERSION or holdout_end is None:
        raise SnapshotRefusal("holdout_seal_missing", "seal record is not m4_7_holdout_seal_v1")
    if record.get("rule_version") not in SEAL_RULES:
        raise SnapshotRefusal("holdout_seal_missing", f"unknown seal rule {record.get('rule_version')!r}")
    return record


def read_holdout_end(snapshot_dir: Path) -> date:
    """Return the sealed ``holdout_end_exclusive``; refuse when no seal exists."""

    return date.fromisoformat(read_seal(snapshot_dir)["holdout_end_exclusive"])


def build_seal_carry_record(
    seal_v1_bytes: bytes,
    confirmation_v2_bytes: bytes,
    *,
    written_at: str,
    writing_actor: str,
    authorization_reference: str,
    private_prospective_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Plan 2.2: the carry record for a rule v2 snapshot, verified against the three bound hashes.

    The window, calendar source, and prior exposures come from the seal v1
    bytes and from nothing else. A docs file or a present private prospective
    file with another hash refuses ``seal_carry_source_mismatch``.
    """

    checks = (("seal_v1_docs", seal_v1_bytes, SEAL_V1_DOCS_SHA256),
              ("seal_v1_confirmation_v2", confirmation_v2_bytes, SEAL_V1_CONFIRMATION_V2_SHA256))
    if private_prospective_bytes is not None:
        checks += (("seal_v1_prospective", private_prospective_bytes, SEAL_V1_PROSPECTIVE_SHA256),)
    for name, payload, expected in checks:
        if sha256_bytes(payload) != expected:
            raise SnapshotRefusal("seal_carry_source_mismatch", f"{name} SHA-256 differs from the bound hash")
    seal = json.loads(seal_v1_bytes)
    confirmation = json.loads(confirmation_v2_bytes)
    for name, record in (("seal_v1_docs", seal), ("seal_v1_confirmation_v2", confirmation)):
        if record.get("confirmation", {}).get("seal_prospective_sha256") != SEAL_V1_PROSPECTIVE_SHA256:
            raise SnapshotRefusal("seal_carry_source_mismatch", f"{name} embeds another prospective hash")
    if any(record.get(key) != value for record in (seal, confirmation) for key, value in SEAL_V1_WINDOW.items()):
        raise SnapshotRefusal("seal_carry_source_mismatch", "seal v1 bytes and the bound window disagree")
    return {
        "schema_version": SEAL_CARRY_SCHEMA_VERSION,
        "rule_version": SEAL_CARRY_RULE,
        "holdout_start": seal["holdout_start"],
        "holdout_end_exclusive": seal["holdout_end_exclusive"],
        "calendar_source": seal["calendar_source"],
        "carried_from": {
            "seal_v1_docs_path": SEAL_V1_DOCS_PATH,
            "seal_v1_docs_sha256": SEAL_V1_DOCS_SHA256,
            "seal_v1_prospective_sha256": SEAL_V1_PROSPECTIVE_SHA256,
            "seal_v1_confirmation_v2_path": SEAL_V1_CONFIRMATION_V2_PATH,
            "seal_v1_confirmation_v2_sha256": SEAL_V1_CONFIRMATION_V2_SHA256,
            "private_prospective_verified": private_prospective_bytes is not None,
        },
        "prior_exposures": seal["prior_exposures"],
        "prior_exposure_status": "carried_stated_v1",
        "partition_rule": PARTITION_RULE_V2,
        "discovery_layout": DISCOVERY_LAYOUT_V2,
        "pre_side_volume_basis": PRE_SIDE_VOLUME_BASIS,
        "seal_bracket_computation_forbidden": True,
        "seal_bracket_scope": "every_computation_downstream_of_the_partitioner",
        "partitioner_value_access": [{
            "table": "splits", "field": "ratio", "rows": "dated_on_or_after_holdout_start",
            "purpose": PRE_SIDE_VOLUME_BASIS,
            "design_impact": "pre-side volume is divided by the product of these ratios; no ratio, factor, or "
                             "count derived from them is written to a discovery file or a public output",
        }],
        "value_fields_accessed_downstream": [],
        "holdout_value_files_never_opened_downstream": [
            "raw/**", "eod/holdout/*", "splits/holdout/*", "dividends/holdout/*", "quarantine/**",
        ],
        "classification": "carried_seal_with_stated_prior_exposures",
        "written_at": written_at,
        "writing_actor": writing_actor,
        "authorization_reference": authorization_reference,
    }


def write_seal_carry(
    snapshot_dir: Path,
    *,
    seal_v1_path: Path,
    confirmation_v2_path: Path,
    written_at: str,
    writing_actor: str,
    authorization_reference: str,
    private_prospective_path: Path | None = None,
) -> tuple[dict[str, Any], str]:
    """Write ``holdout_seal_v2.json`` into a snapshot; return the record and its SHA-256."""

    snapshot_dir = Path(snapshot_dir)
    target = snapshot_dir / SEAL_CARRY_FILE
    if target.exists():
        raise SnapshotRefusal("snapshot_file_exists", SEAL_CARRY_FILE)
    if (snapshot_dir / SEAL_FILE).exists():
        raise SnapshotRefusal("holdout_seal_ambiguous", f"{SEAL_FILE} exists in a rule v2 snapshot")
    record = build_seal_carry_record(
        Path(seal_v1_path).read_bytes(), Path(confirmation_v2_path).read_bytes(),
        written_at=written_at, writing_actor=writing_actor, authorization_reference=authorization_reference,
        private_prospective_bytes=None if private_prospective_path is None else Path(private_prospective_path).read_bytes(),
    )
    body = seal_bytes(record)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_bytes(body)
    os.replace(temporary, target)
    return record, sha256_bytes(body)


def read_seal_carry(snapshot_dir: Path) -> dict[str, Any]:
    """Return the carry record; refuse a record that is not a well-formed carried seal."""

    path = Path(snapshot_dir) / SEAL_CARRY_FILE
    if not path.is_file():
        raise SnapshotRefusal("holdout_seal_missing", SEAL_CARRY_FILE)
    record = json.loads(path.read_bytes())
    carried = record.get("carried_from", {})
    well_formed = (
        record.get("schema_version") == SEAL_CARRY_SCHEMA_VERSION
        and record.get("rule_version") == SEAL_CARRY_RULE
        and record.get("partition_rule") == PARTITION_RULE_V2
        and all(record.get(key) == value for key, value in SEAL_V1_WINDOW.items())
        and carried.get("seal_v1_docs_sha256") == SEAL_V1_DOCS_SHA256
        and carried.get("seal_v1_prospective_sha256") == SEAL_V1_PROSPECTIVE_SHA256
        and carried.get("seal_v1_confirmation_v2_sha256") == SEAL_V1_CONFIRMATION_V2_SHA256
    )
    if not well_formed:
        raise SnapshotRefusal("holdout_seal_missing", f"{SEAL_CARRY_FILE} is not a carried_forward_sealed_window_v1 record")
    return record


def refuse_carried_window_recompute(snapshot_dir: Path) -> None:
    """Plan 2.2: a count-based window derivation on a carried seal refuses ``seal_window_recompute_forbidden``."""

    if (Path(snapshot_dir) / SEAL_CARRY_FILE).exists():
        raise SnapshotRefusal("seal_window_recompute_forbidden", f"{SEAL_CARRY_FILE} declares {SEAL_CARRY_RULE}")


def classify_membership_entries(
    frame: pd.DataFrame,
    components_retrieved_utc_date: date,
) -> list[dict[str, Any]]:
    """Type every raw membership entry under the shared entry rule (C75, C87).

    One record per raw row in raw-table order with ``code``, ``start``, ``end``
    (``None`` when open), ``outcome`` (``retained``, ``entry_missing_field``,
    ``entry_unparseable_date``, ``degenerate_interval``,
    ``exact_duplicate_collapsed``, or ``raw_overlap``), and ``duplicate_of``
    (the raw position of the retained copy). The seal and the universe build
    both call this function, so they count the same entries.
    """

    records: list[dict[str, Any]] = []
    first_copy: dict[tuple[str, date, date | None], int] = {}
    for position, row in enumerate(frame.to_dict(orient="records")):
        code, start_raw, end_raw = row.get("Code"), row.get("StartDate"), row.get("EndDate")
        record: dict[str, Any] = {"position": position, "code": None, "start": None, "end": None, "duplicate_of": None}
        records.append(record)
        if _is_blank(code) or _is_blank(start_raw):
            record["outcome"] = "entry_missing_field"
            continue
        start = parse_strict_date(start_raw)
        end = None if _is_blank(end_raw) else parse_strict_date(end_raw)
        if start is None or (not _is_blank(end_raw) and end is None):
            record["outcome"] = "entry_unparseable_date"
            continue
        if end is not None and end > components_retrieved_utc_date:
            end = None
        record.update(code=str(code), start=start, end=end)
        if end is not None and end <= start:
            record["outcome"] = "degenerate_interval"
            continue
        triple = (str(code), start, end)
        if triple in first_copy:
            record.update(outcome="exact_duplicate_collapsed", duplicate_of=first_copy[triple])
            continue
        first_copy[triple] = position
        record["outcome"] = "retained"

    kept = [record for record in records if record["outcome"] == "retained"]
    for i, left in enumerate(kept):
        for right in kept[i + 1:]:
            if left["code"] == right["code"] and _intersects(left["start"], left["end"], right["start"], right["end"]):
                left["overlap"] = right["overlap"] = True
    for record in kept:
        if record.pop("overlap", False):
            record["outcome"] = "raw_overlap"
    return records


def parse_membership_entries(
    frame: pd.DataFrame,
    components_retrieved_utc_date: date,
) -> tuple[list[tuple[str, date, date | None]], dict[str, int]]:
    """Apply the shared entry rule (plan 1.4 step 1, 1.6 step 2, C75, C87).

    Returns the retained ``(code, start_date, end_date_or_open)`` triples in
    raw-table order and the count per typed outcome.
    """

    records = classify_membership_entries(frame, components_retrieved_utc_date)
    counts = {"raw_entries": int(len(frame))}
    for outcome in ("entry_missing_field", "entry_unparseable_date", "degenerate_interval",
                    "exact_duplicate_collapsed", "raw_overlap", "retained"):
        counts[outcome] = sum(1 for record in records if record["outcome"] == outcome)
    retained = [(r["code"], r["start"], r["end"]) for r in records if r["outcome"] == "retained"]
    return retained, counts


def monthly_raw_counts(
    entries: list[tuple[str, date, date | None]],
    last_day: date,
) -> list[tuple[date, int]]:
    """``n_raw(m)`` for every calendar month-end from the earliest start to ``last_day``."""

    if not entries:
        return []
    first = min(start for _, start, _ in entries)
    counts: list[tuple[date, int]] = []
    month_end = _month_end(first.year, first.month)
    while month_end <= last_day:
        n = sum(
            1
            for _, start, end in entries
            if start <= month_end and (end is None or end > month_end)
        )
        counts.append((month_end, n))
        month_end = _month_end(
            month_end.year + month_end.month // 12, month_end.month % 12 + 1
        )
    return counts


def coverage_start(counts: list[tuple[date, int]], tolerance: int) -> date | None:
    """Earliest in-band month-end whose tail meets the tolerant band rule.

    Over the month-ends from ``m*`` on, at most ``tolerance`` lie outside
    ``BAND``, no two of them are adjacent, and none lies outside ``HARD_BAND``.
    ``m*`` itself is in band. ``tolerance = 0`` is the strict sensitivity.
    """

    for start in range(len(counts)):
        if not _in_band(counts[start][1]):
            continue
        exceptions = [
            index for index in range(start, len(counts)) if not _in_band(counts[index][1])
        ]
        if len(exceptions) > tolerance:
            continue
        if any(later - earlier == 1 for earlier, later in zip(exceptions, exceptions[1:])):
            continue
        if any(not HARD_BAND[0] <= counts[index][1] <= HARD_BAND[1] for index in exceptions):
            continue
        return counts[start][0]
    return None


def derive_holdout_window(
    frame: pd.DataFrame,
    components_retrieved_utc_date: date,
    rule_version: str = SEAL_RULE_VERSION,
) -> dict[str, Any]:
    """Derive the holdout window under ``rule_version``; refuse a window ending after its cap."""

    entries, entry_counts = parse_membership_entries(frame, components_retrieved_utc_date)
    counts = monthly_raw_counts(entries, components_retrieved_utc_date)
    tolerant = coverage_start(counts, TOLERANCE_EXCEPTIONS)
    strict = coverage_start(counts, 0)
    if tolerant is None:
        raise SnapshotRefusal("coverage_start_undefined", "no month-end meets the band rule")
    rule = SEAL_RULES[rule_version]
    holdout_end = _add_years_to_month_end(tolerant, rule["holdout_years"])
    cap = rule["latest_holdout_end"]
    if cap is not None and holdout_end > cap:
        raise SnapshotRefusal(
            "holdout_overlaps_prior_exposure",
            f"holdout_end {holdout_end.isoformat()} is after {cap.isoformat()}",
        )
    return {
        "holdout_start": tolerant.isoformat(),
        "holdout_end_exclusive": holdout_end.isoformat(),
        "coverage_start_strict": None if strict is None else strict.isoformat(),
        "entry_counts": entry_counts,
    }


def build_prospective_seal(
    window: dict[str, Any],
    *,
    components_raw_sha256: str,
    components_retrieved_utc_date: date,
    sealed_at: str,
    sealing_actor: str,
    authorization_reference: str,
    rule_version: str = SEAL_RULE_VERSION,
    calendar_source: str = DEFAULT_CALENDAR_SOURCE,
) -> dict[str, Any]:
    """Assemble the plan 5.4 seal record with ``confirmation.status = pending``."""

    return {
        "schema_version": SEAL_SCHEMA_VERSION,
        "rule_version": rule_version,
        "coverage_start_rule": COVERAGE_START_RULE,
        "holdout_start": window["holdout_start"],
        "holdout_end_exclusive": window["holdout_end_exclusive"],
        "coverage_start_strict": window["coverage_start_strict"],
        "band": list(BAND),
        "tolerance_exceptions": TOLERANCE_EXCEPTIONS,
        "entry_counts": window["entry_counts"],
        "calendar_source": calendar_source,
        "sealed_at": sealed_at,
        "sealing_actor": sealing_actor,
        "authorization_reference": authorization_reference,
        "inputs": {
            "components_raw_sha256": components_raw_sha256,
            "components_retrieved_utc_date": components_retrieved_utc_date.isoformat(),
        },
        "metadata_fields_accessed": [
            *_ENTRY_FIELDS,
            "manifest.snapshot.components_retrieved_utc_date",
        ],
        "value_fields_accessed": [],
        "bar_date_source": {
            "reader": "read_bar_dates",
            "files": "dates/<CODE>.US.parquet",
            "columns": ["date"],
            "written_before_value_validation": True,
            "purposes": ["E1", "E2", "E6", "exit_class", "first_bar", "last_bar", "bar_presence"],
        },
        "retrieval_order": list(RETRIEVAL_ORDER),
        "automated_integrity_checks_over_holdout_rows": {
            "checks": [
                "date_structure",
                "positive_prices",
                "non_negative_volume",
                "ohlc_relations",
                "split_ratio_positive_finite",
                "dividend_value_non_negative_finite",
            ],
            "files_passed": "pending",
            "files_quarantined": "pending",
            "date_structure_refusals": "pending",
            "design_impact": "none_by_construction",
        },
        "byte_scans": [
            {
                "scan": "token_leak_scan",
                "files": [
                    "raw/**",
                    "eod/**",
                    "splits/**",
                    "dividends/**",
                    "dates/**",
                    "calendar/**",
                    "manifest.json",
                    "retrieval_log.jsonl",
                ],
                "parsing": "none",
                "values_interpreted": "none",
            }
        ],
        "holdout_value_files_never_opened_downstream": [
            "raw/eod/*.json",
            "raw/index/GSPC.INDX.eod.json",
            "raw/splits/*.json",
            "raw/dividends/*.json",
            "eod/holdout/*",
            "splits/holdout/*",
            "dividends/holdout/*",
            "quarantine/**",
        ],
        "prior_exposures": [
            {"window": "2016-08-08..2026-08-07", "kind": "static_50_name_cohort"},
            {"window": "2018-01-02..2026-06-26", "kind": "csv_validation"},
            {"window": "2025-05-01..2026-05-31", "kind": "historical_evaluation"},
        ],
        "classification": "sealed_holdout",
        "confirmation": {
            "status": "pending",
            "identity_adjusted_min_month_end_count": None,
            "census_json_sha256": None,
            "seal_prospective_sha256": None,
        },
    }


def seal_bytes(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_prospective_seal(
    snapshot_dir: Path,
    *,
    sealed_at: str,
    sealing_actor: str,
    authorization_reference: str,
    rule_version: str = SEAL_RULE_VERSION,
    calendar_source: str = DEFAULT_CALENDAR_SOURCE,
) -> tuple[dict[str, Any], str]:
    """Derive and write ``holdout_seal_v1.json``; return the record and its SHA-256.

    Reads exactly ``manifest.json`` and the manifest-authorized membership
    file (S5, S7). The returned hash is ``seal_prospective_sha256``.
    """

    snapshot_dir = Path(snapshot_dir)
    refuse_carried_window_recompute(snapshot_dir)
    target = snapshot_dir / SEAL_FILE
    if target.exists():
        raise SnapshotRefusal("snapshot_file_exists", SEAL_FILE)
    manifest = read_manifest(snapshot_dir)
    retrieved = parse_strict_date(
        manifest.get("snapshot", {}).get("components_retrieved_utc_date")
    )
    if retrieved is None or MEMBERSHIP_FILE not in authorized_records(manifest):
        raise SnapshotRefusal("holdout_seal_missing", "components membership is not retrieved")
    payload = read_authorized_bytes(snapshot_dir, MEMBERSHIP_FILE, manifest)
    frame = pd.read_parquet(io.BytesIO(payload), engine="pyarrow")
    window = derive_holdout_window(frame, retrieved, rule_version)
    record = build_prospective_seal(
        window,
        components_raw_sha256=sha256_bytes(payload),
        components_retrieved_utc_date=retrieved,
        sealed_at=sealed_at,
        sealing_actor=sealing_actor,
        authorization_reference=authorization_reference,
        rule_version=rule_version,
        calendar_source=calendar_source,
    )
    body = seal_bytes(record)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_bytes(body)
    os.replace(temporary, target)
    return record, sha256_bytes(body)


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, float) and value != value) or value == ""


def _intersects(start_a: date, end_a: date | None, start_b: date, end_b: date | None) -> bool:
    return (end_b is None or start_a < end_b) and (end_a is None or start_b < end_a)


def _in_band(count: int) -> bool:
    return BAND[0] <= count <= BAND[1]


def _month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def _add_years_to_month_end(month_end: date, years: int) -> date:
    return _month_end(month_end.year + years, month_end.month)
