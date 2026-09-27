"""Terminal evidence tooling for M4.7 delisting candidates (plan section 3, Decision D7).

``template`` writes one row per permanent ID whose resolved intervals include a
``delisting_candidate``; people curate ``terminal/terminal_evidence.csv`` from
public documents; ``validate`` applies the section 3.6 refusal codes and
computes each accepted row's terminal return; ``project`` writes exactly the
seven engine fields for the accepted rows. Rows that fail stay ``unresolved``
and enter the unresolved set ``U`` of the common support; nothing is filled
(R4, R6). Values are read from discovery partitions only; a candidate whose
settlement row lies at or before the first discovery row is
``deferred_holdout`` and no value of it is read.

Registration v3 (M4.8 plan 3.1-3.6) passes the discovery segments: a candidate
is in scope when its settlement row ``s`` satisfies
``first_reset_row < s <= last_book_row`` for a segment, ``deferred_holdout``
narrows to the seal window, and every other row is
``outside_discovery_holding_windows``. Schema v3 adds the accession, terms
availability, payment timing, and second-check columns, and ``validate`` runs a
terms pass and a projection pass with the four timing bounds.

Run as ``python -m research.m4_7_terminal_evidence {template,validate,project} --snapshot-id <ID>``.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import sys
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from data.holdout_partition import PARTITION_RULE_V2, SnapshotRefusal, parse_strict_date, sha256_bytes
from research.m4_7_universe_build import (
    BUILD_MANIFEST,
    INTERVAL_RESULTS,
    SECURITY_MASTER,
    Snapshot,
    canonical_json,
    csv_bytes,
    discovery_segments,
    discovery_window,
    read_bar_dates,
    read_derived_json,
    require_current,
    snapshot_dir_from_args,
    write_bytes,
)


TEMPLATE = "terminal/terminal_evidence_template.csv"
CURATED = "terminal/terminal_evidence.csv"
VALIDATION = "terminal/terminal_validation.json"
ENGINE_EVENTS = "terminal/terminal_events_engine.csv"
EVIDENCE_COLUMNS = (
    "event_id", "permanent_id", "curation_status", "event_kind", "consideration_type", "announcement_date",
    "completion_date", "cash_per_share", "exchange_ratio", "acquirer_permanent_id", "cash_currency",
    "source_evidence", "curator", "notes",
)
TERM_COLUMNS = EVIDENCE_COLUMNS[3:12] + ("notes",)
ENGINE_FIELDS = ("event_id", "permanent_id", "effective_date", "known_at", "reference_date", "terminal_return", "return_basis")
EVENT_KINDS = frozenset({"merger_or_acquisition", "rename_or_code_change", "exchange_delisting",
                         "bankruptcy_or_liquidation", "other"})
CASH_BASIS = "prior_observed_close_to_cash"
BASIS = {
    "cash": CASH_BASIS,
    "evidenced_worthless": CASH_BASIS,
    "stock": "prior_observed_close_to_stock_consideration_valued_at_completion_date_close",
    "mixed": "prior_observed_close_to_mixed_consideration_valued_at_completion_date_close",
}
EVENTS_HEADER = "# validation_report_sha256: "
CONTRADICTORY_FIELDS = "evidence_incomplete:contradictory_consideration_fields"
EVENTS_MISMATCH = "derived_artifact_stale:terminal_events_engine_mismatch"
EVIDENCE_MISMATCH = "derived_artifact_stale:terminal_validation_evidence_mismatch"
CASH_LAG_MAX = 3
STOCK_LAGS = (-1, 0)
BASIS_TOLERANCE = 1e-6
UNJUSTIFIED_RETURN = 1.5
V3_COLUMNS = ("source_accession", "source_form", "terms_known_at", "payment_timing", "payment_date",
              "payment_source_accession", "second_check")
EVIDENCE_COLUMNS_V3 = EVIDENCE_COLUMNS + V3_COLUMNS
TERM_COLUMNS_V3 = TERM_COLUMNS + V3_COLUMNS[:-1]
PAYMENT_TIMINGS = frozenset({"at_completion_evidenced", "delayed_evidenced", "unknown"})
PAYMENT_LAG_MAX = 3
SECOND_CHECK_FRACTION = 0.2
SECOND_CHECK_SEED = 20260927
IN_SCOPE, DEFERRED, OUTSIDE = "in_scope", "deferred_holdout", "outside_discovery_holding_windows"
TERMS_LATE, PAYMENT_UNKNOWN, PAYMENT_LATE, SECOND_CHECK_DISAGREE = (
    "unresolved:terms_known_after_reference", "unresolved:payment_timing_unknown",
    "unresolved:payment_lag_exceeds_bound", "unresolved:second_check_disagree")
V3_LABELS = ("stock_consideration_converted_at_completion_close_v1", "terms_known_at_bound_v1", "payment_timing_v1")


def snapshot_segments(snapshot: Snapshot, calendar: pd.DatetimeIndex) -> tuple[Any, ...] | None:
    """Rule v2: ``discovery_segments`` from the build manifest's ``d0_pre``; rule v1: ``None`` (one discovery side)."""
    if snapshot.partition_rule != PARTITION_RULE_V2:
        return None
    d0_pre = read_derived_json(snapshot.root, BUILD_MANIFEST).get("d0_pre")
    if not d0_pre:
        raise SnapshotRefusal("discovery_segments_undefined", "the rule v2 build manifest records no d0_pre")
    return discovery_segments(calendar, snapshot.holdout_start, snapshot.holdout_end, date.fromisoformat(d0_pre))


def _load(snapshot_dir: Path | str) -> tuple[Snapshot, pd.DatetimeIndex, int, pd.DataFrame, str]:
    snapshot = Snapshot.open(snapshot_dir)
    manifest = read_derived_json(snapshot.root, BUILD_MANIFEST)
    inputs = require_current(snapshot, manifest.get("discovery_inputs_sha256"), BUILD_MANIFEST)
    calendar = snapshot.calendar()
    i_h, _, _ = discovery_window(calendar, snapshot.holdout_end)
    master = _read_csv(snapshot.root / SECURITY_MASTER)
    return snapshot, calendar, i_h, master, inputs


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def event_scope(settlement: int, segments: tuple[Any, ...], seal_rows: tuple[int, int]) -> tuple[str, Any]:
    """M4.8 plan 3.1: ``(scope, segment)`` of a settlement row on the full calendar.

    ``segments`` carry ``first_reset_row`` and ``last_book_row``; ``seal_rows``
    is ``(row(holdout_start), row(holdout_end))``.
    """
    for segment in segments:
        if segment.first_reset_row < settlement <= segment.last_book_row:
            return IN_SCOPE, segment
    if seal_rows[0] <= settlement < seal_rows[1]:
        return DEFERRED, None
    return OUTSIDE, None


def _seal_rows(calendar: pd.DatetimeIndex, holdout_start: date, i_h: int) -> tuple[int, int]:
    return int(calendar.searchsorted(pd.Timestamp(holdout_start))), i_h


def write_template(
    snapshot_dir: Path | str, *, segments: tuple[Any, ...] | None = None, holdout_start: date | None = None,
) -> pd.DataFrame:
    """One template row per candidate permanent ID (plan 3.1).

    Without ``segments`` a row is ``deferred_holdout`` when ``S <= i_H``; with
    them (schema v3) it carries its M4.8 scope class and the v3 columns. A rule
    v2 snapshot supplies its own segments and ``holdout_start``.
    """
    snapshot, calendar, i_h, master, inputs = _load(snapshot_dir)
    if segments is None:
        segments, holdout_start = snapshot_segments(snapshot, calendar), snapshot.holdout_start
    columns = EVIDENCE_COLUMNS if segments is None else EVIDENCE_COLUMNS_V3
    seal_rows = None if segments is None else _seal_rows(calendar, holdout_start, i_h)
    rows = []
    for record in master.to_dict(orient="records"):
        if record["permanent_id"] and record["has_delisting_candidate_interval"] == "True":
            settlement = calendar.get_loc(pd.Timestamp(record["last_bar"])) + 1
            if segments is None:
                status = "deferred_holdout" if settlement <= i_h else "unresolved"
            else:
                scope = event_scope(settlement, segments, seal_rows)[0]
                status = "unresolved" if scope == IN_SCOPE else scope
            rows.append({
                **dict.fromkeys(columns, ""),
                "event_id": f"TE-{record['permanent_id']}-{calendar[settlement].date().isoformat()}",
                "permanent_id": record["permanent_id"],
                "curation_status": status,
                "discovery_inputs_sha256": inputs,
            })
    frame = pd.DataFrame(rows, columns=[*columns, "discovery_inputs_sha256"])
    write_bytes(snapshot.root / TEMPLATE, csv_bytes(frame))
    return frame


def validate(
    snapshot_dir: Path | str, *, segments: tuple[Any, ...] | None = None, holdout_start: date | None = None,
    second_check_seed: int = SECOND_CHECK_SEED,
) -> dict[str, Any]:
    """Apply the section 3.6 codes to the curated table and write the validation report.

    With ``segments``, or on a rule v2 snapshot, the schema v3 two-pass
    validation of M4.8 plan 3.6 runs instead (``validate_v3``).
    """
    if segments is None:
        opened = Snapshot.open(snapshot_dir)
        if opened.partition_rule == PARTITION_RULE_V2:
            segments, holdout_start = snapshot_segments(opened, opened.calendar()), opened.holdout_start
    if segments is not None:
        return validate_v3(snapshot_dir, segments=segments, holdout_start=holdout_start,
                           second_check_seed=second_check_seed)
    snapshot, calendar, i_h, master, inputs = _load(snapshot_dir)
    path = snapshot.root / CURATED
    if not path.is_file():
        raise SnapshotRefusal("terminal_evidence_missing", CURATED)
    evidence_bytes = path.read_bytes()
    curated = pd.read_csv(io.BytesIO(evidence_bytes), dtype=str, keep_default_na=False)
    missing = [column for column in EVIDENCE_COLUMNS if column not in curated.columns]
    if missing or curated["event_id"].duplicated().any():
        raise SnapshotRefusal("terminal_evidence_invalid", f"columns {missing} or duplicate event_id")
    masters = {r["permanent_id"]: r for r in master.to_dict(orient="records") if r["permanent_id"]}
    candidates = _candidates(snapshot)
    results = []
    for row in curated.to_dict(orient="records"):
        pid = row["permanent_id"]
        if pid not in masters or pid not in candidates:
            raise SnapshotRefusal("terminal_evidence_invalid", f"{row['event_id']}: not a resolved delisting candidate")
        last_bar = calendar.get_loc(pd.Timestamp(masters[pid]["last_bar"]))
        settlement = last_bar + 1
        implied = _implied_settlement(row["event_id"], pid)
        has_terms = any(row[column].strip() for column in TERM_COLUMNS)
        if settlement <= i_h:
            if has_terms:
                raise SnapshotRefusal("holdout_terms_forbidden", row["event_id"])
            results.append(_result(row, "deferred_holdout", None))
            continue
        if row["curation_status"] != "curated":
            results.append(_result(row, "unresolved", "curation_unresolved"))
            continue
        if implied is None or implied != calendar[settlement].date():
            results.append(_result(row, "unresolved", "reference_not_last_bar"))
            continue
        results.append(_validate_row(snapshot, calendar, masters, row, last_bar))
    counts: dict[str, int] = {}
    for result in results:
        key = result["validation_reason"] or result["status"]
        counts[key] = counts.get(key, 0) + 1
    report = {
        "schema_version": "m4_7_terminal_validation_v1",
        "discovery_inputs_sha256": inputs,
        "curated_evidence_sha256": sha256_bytes(evidence_bytes),
        "counts": dict(sorted(counts.items())),
        "settlement_lag_distribution": _lag_distribution(results),
        "valuation_row_offsets": {
            "L": sum(1 for r in results if r["status"] == "accepted" and r["settlement_lag_rows"] == -1
                     and r["consideration_type"] in ("stock", "mixed")),
            "S": sum(1 for r in results if r["status"] == "accepted" and r["settlement_lag_rows"] == 0
                     and r["consideration_type"] in ("stock", "mixed")),
        },
        "rows": results,
    }
    write_bytes(snapshot.root / VALIDATION, canonical_json(report))
    return report


def _candidates(snapshot: Snapshot) -> set[str]:
    intervals = _read_csv(snapshot.root / INTERVAL_RESULTS)
    return set(intervals.loc[intervals["exit_class"] == "delisting_candidate", "permanent_id"])


def _implied_settlement(event_id: str, pid: str) -> date | None:
    prefix = f"TE-{pid}-"
    return parse_strict_date(event_id[len(prefix):]) if event_id.startswith(prefix) else None


def _result(row: dict[str, Any], status: str, reason: str | None, **fields: Any) -> dict[str, Any]:
    return {
        "event_id": row["event_id"], "permanent_id": row["permanent_id"], "status": status,
        "validation_reason": reason, "event_kind": row.get("event_kind", ""),
        "consideration_type": row.get("consideration_type", ""), "settlement_lag_rows": None, "valuation_row": None,
        "corporate_action_evidence_status": None, "terminal_return": None, "return_basis": None,
        "reference_date": None, "effective_date": None, "known_at": None, **fields,
    }


def _number(text: str) -> float | None:
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _blank_or_zero(text: str) -> bool:
    return not text.strip() or _number(text) == 0.0


def _consideration_fault(kind: str, row: dict[str, Any], cash: float | None, ratio: float | None, acquirer: str) -> str | None:
    """Required and forbidden term fields by consideration type (plan 3.2, 3.3).

    A missing required component is ``evidence_incomplete``; a populated field
    that the type's registered formula does not use is
    ``evidence_incomplete:contradictory_consideration_fields``, so an unused
    field can never change a payoff or disagree with its basis label.
    """
    stock_terms = ratio is not None and ratio > 0 and bool(acquirer)
    if kind == "cash":
        if cash is None or cash < 0:
            return "evidence_incomplete"
        if row["exchange_ratio"].strip() or acquirer:
            return CONTRADICTORY_FIELDS
    elif kind == "stock":
        if not stock_terms:
            return "evidence_incomplete"
        if not _blank_or_zero(row["cash_per_share"]):
            return CONTRADICTORY_FIELDS
    elif kind == "mixed":
        if not stock_terms or cash is None or cash <= 0:
            return "evidence_incomplete"
    elif kind == "evidenced_worthless":
        if not _blank_or_zero(row["cash_per_share"]) or row["exchange_ratio"].strip() or acquirer:
            return CONTRADICTORY_FIELDS
    return None


def _validate_row(
    snapshot: Snapshot, calendar: pd.DatetimeIndex, masters: dict[str, dict[str, Any]],
    row: dict[str, Any], last_bar: int,
) -> dict[str, Any]:
    kind = row["consideration_type"]
    code = masters[row["permanent_id"]]["vendor_code"]
    announced, completed = parse_strict_date(row["announcement_date"]), parse_strict_date(row["completion_date"])
    cash, ratio = _number(row["cash_per_share"]), _number(row["exchange_ratio"])
    acquirer = row["acquirer_permanent_id"].strip()
    settlement = last_bar + 1
    timing = {"reference_date": calendar[last_bar].date().isoformat(),
              "effective_date": calendar[settlement].date().isoformat()}
    if kind == "unresolved":
        return _result(row, "unresolved", "curation_unresolved", **timing)
    complete = (row["event_kind"] in EVENT_KINDS and kind in BASIS and announced is not None
                and completed is not None and row["source_evidence"].strip())
    fault = "evidence_incomplete" if not complete else _consideration_fault(kind, row, cash, ratio, acquirer)
    if fault is not None:
        return _result(row, "unresolved", fault, **timing)
    if kind in ("cash", "mixed") and row["cash_currency"].strip() != "USD":
        return _result(row, "unresolved", "terminal_currency_unsupported", **timing)
    if pd.Timestamp(announced) > calendar[last_bar]:
        return _result(row, "unresolved", "known_at_after_reference", **timing)
    lag = int(calendar.searchsorted(pd.Timestamp(completed))) - settlement
    timing["settlement_lag_rows"] = lag
    if lag < -1:
        return _result(row, "unresolved", "settlement_lag_negative", **timing)
    if kind in ("cash", "evidenced_worthless") and lag > CASH_LAG_MAX:
        return _result(row, "unresolved", "settlement_lag_exceeds_3_rows", **timing)
    if kind in ("stock", "mixed") and lag not in STOCK_LAGS:
        return _result(row, "unresolved", "stock_consideration_lag_positive", **timing)
    valuation = settlement + lag  # V <= S for stock and mixed, so it indexes the calendar; cash never reads it
    acquirer_code = None
    if kind in ("stock", "mixed"):
        timing["valuation_row"] = calendar[valuation].date().isoformat()
        record = masters.get(acquirer)
        dates = None if record is None else read_bar_dates(snapshot, record["vendor_code"])
        if record is None or record["resolution"] != "resolved" or dates is None or calendar[valuation] not in dates \
                or not record["first_bar"] <= timing["valuation_row"] <= record["last_bar"]:
            return _result(row, "unresolved", "acquirer_bar_missing", **timing)
        acquirer_code = record["vendor_code"]
    tables = [("splits", code), ("dividends", code)] + ([("splits", acquirer_code)] if acquirer_code else [])
    if not all(snapshot.evidence_valid(table, table_code) for table, table_code in tables):
        return _result(row, "unresolved", "terminal_basis_ambiguous:corporate_action_evidence_missing",
                       corporate_action_evidence_status="missing", **timing)
    timing["corporate_action_evidence_status"] = "valid"
    target = _discovery_eod(snapshot, code)
    reference = calendar[last_bar]
    p_ref, adjusted = float(target.loc[reference, "close"]), float(target.loc[reference, "adjusted_close"])
    settle_day = calendar[settlement]
    target_actions = _dates(snapshot, "splits", code) | _dates(snapshot, "dividends", code)
    acquirer_splits = _dates(snapshot, "splits", acquirer_code) if acquirer_code else set()
    acquirer_split_on_v = acquirer_code is not None and calendar[valuation] in acquirer_splits
    if abs(adjusted / p_ref - 1.0) > BASIS_TOLERANCE or settle_day in target_actions or acquirer_split_on_v:
        return _result(row, "unresolved", "terminal_basis_ambiguous", **timing)
    acquirer_close = None
    if acquirer_code is not None:
        frame = _discovery_eod(snapshot, acquirer_code)
        if frame is None or calendar[valuation] not in frame.index:
            return _result(row, "unresolved", "acquirer_bar_missing", **timing)
        acquirer_close = float(frame.loc[calendar[valuation], "close"])
    if kind == "evidenced_worthless":
        rho = -1.0
    elif kind == "cash":
        rho = cash / p_ref - 1.0
    elif kind == "stock":
        rho = ratio * acquirer_close / p_ref - 1.0
    else:
        rho = (cash + ratio * acquirer_close) / p_ref - 1.0
    if rho < -1.0:
        raise SnapshotRefusal("terminal_return_below_minus_one", row["event_id"])
    if rho > UNJUSTIFIED_RETURN and not row["notes"].strip():
        return _result(row, "unresolved", "terminal_return_unjustified", terminal_return=rho, **timing)
    return _result(row, "accepted", None, terminal_return=rho, return_basis=BASIS[kind],
                   known_at=announced.isoformat(), **timing)


def validate_v3(
    snapshot_dir: Path | str, *, segments: tuple[Any, ...], holdout_start: date,
    second_check_seed: int = SECOND_CHECK_SEED,
) -> dict[str, Any]:
    """Schema v3 two-pass validation (M4.8 plan 3.1-3.6); writes the validation report.

    Every in-scope curated row runs the terms pass (the carried checks and the
    v3 schema rules, without the four timing bounds) and, when terms-valid, the
    projection pass with the timing bounds, since ``terminal_claim_v1`` is not
    built. Rows whose only failures are timing bounds keep ``terms_pass =
    terms_valid`` and list ``timing_failures``; ``common_support.claim_demand``
    counts those that are residual. Values are read from the side of the
    settlement row's segment only.
    """
    snapshot, calendar, i_h, master, inputs = _load(snapshot_dir)
    if holdout_start is None:
        raise SnapshotRefusal("terminal_evidence_invalid", "schema v3 validation needs holdout_start")
    seal_rows = _seal_rows(calendar, holdout_start, i_h)
    path = snapshot.root / CURATED
    if not path.is_file():
        raise SnapshotRefusal("terminal_evidence_missing", CURATED)
    evidence_bytes = path.read_bytes()
    curated = pd.read_csv(io.BytesIO(evidence_bytes), dtype=str, keep_default_na=False)
    missing = [column for column in EVIDENCE_COLUMNS_V3 if column not in curated.columns]
    if missing or curated["event_id"].duplicated().any():
        raise SnapshotRefusal("terminal_evidence_invalid", f"columns {missing} or duplicate event_id")
    masters = {r["permanent_id"]: r for r in master.to_dict(orient="records") if r["permanent_id"]}
    candidates = _candidates(snapshot)
    results = []
    for row in curated.to_dict(orient="records"):
        pid = row["permanent_id"]
        if pid not in masters or pid not in candidates:
            raise SnapshotRefusal("terminal_evidence_invalid", f"{row['event_id']}: not a resolved delisting candidate")
        last_bar = calendar.get_loc(pd.Timestamp(masters[pid]["last_bar"]))
        settlement = last_bar + 1
        scope, segment = event_scope(settlement, segments, seal_rows)
        if scope != IN_SCOPE:
            if scope == DEFERRED and any(row[column].strip() for column in TERM_COLUMNS_V3):
                raise SnapshotRefusal("holdout_terms_forbidden", row["event_id"])
            results.append(_result_v3(row, scope, None, None))
            continue
        if row["curation_status"] != "curated":
            results.append(_result_v3(row, "unresolved", "curation_unresolved", segment))
        elif _implied_settlement(row["event_id"], pid) != calendar[settlement].date():
            results.append(_result_v3(row, "unresolved", "reference_not_last_bar", segment))
        else:
            results.append(_validate_row_v3(snapshot, calendar, masters, row, last_bar, segment))
    second_check = _second_check_sample(results, second_check_seed)
    report = {
        "schema_version": "m4_8_terminal_validation_v3",
        "discovery_inputs_sha256": inputs,
        "curated_evidence_sha256": sha256_bytes(evidence_bytes),
        "claim_contract": "timing_bounds_v1",
        "labels": list(V3_LABELS),
        "counts": _count(results, lambda r: r["validation_reason"] or r["status"]),
        "counts_by": {key: _count(results, lambda r, key=key: str(r[key] or "")) for key in (
            "event_kind", "consideration_type", "payment_timing", "segment_id", "scope")},
        "timing_only_failures": sum(1 for r in results if r["terms_pass"] == "terms_valid" and r["timing_failures"]),
        "settlement_lag_distribution": _lag_distribution(results),
        "terms_availability_lag_distribution": _count([r for r in results if r["terms_availability_lag_days"] is not None],
                                              lambda r: _lag_bucket(r["terms_availability_lag_days"])),
        "second_check": second_check,
        "rows": results,
    }
    write_bytes(snapshot.root / VALIDATION, canonical_json(report))
    return report


def _count(rows: list[dict[str, Any]], key) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[key(row)] = counts.get(key(row), 0) + 1
    return dict(sorted(counts.items()))


def _lag_bucket(days: int) -> str:
    """The approved public day-lag buckets (``research/m4_7_coverage_census.DAY_LAG_BUCKETS``)."""
    return next(label for bound, label in ((0, "0"), (1, "1"), (5, "2-5"), (20, "6-20"), (60, "21-60")) if days <= bound) \
        if days <= 60 else ">60"


def _result_v3(row: dict[str, Any], status: str, reason: str | None, segment: Any, **fields: Any) -> dict[str, Any]:
    scope = status if status in (DEFERRED, OUTSIDE) else IN_SCOPE
    return _result(row, status, reason, **{
        "scope": scope, "segment_id": None if segment is None else segment.segment_id, "terms_pass": None,
        "timing_failures": [], "payment_timing": row.get("payment_timing", "") or None, "terms_known_at": None,
        "terms_availability_lag_days": None, "payment_lag_rows": None, "second_check": row.get("second_check", ""),
        "validation_detail": None,
        **fields})


def _second_check_sample(results: list[dict[str, Any]], seed: int) -> dict[str, Any]:
    """Plan 3.5: a seeded 20 percent sample of in-scope curated rows plus the mandatory re-derivations."""
    curated = sorted(r["event_id"] for r in results if r["scope"] == IN_SCOPE and r["validation_reason"] not in (
        "curation_unresolved", "reference_not_last_bar"))
    count = math.ceil(SECOND_CHECK_FRACTION * len(curated))
    sampled = sorted(np.random.default_rng(seed).choice(curated, size=count, replace=False).tolist()) if count else []
    mandatory = sorted(r["event_id"] for r in results if r["event_id"] in curated and (
        (r["terminal_return"] is not None and abs(r["terminal_return"]) > 0.5)
        or (r["terms_availability_lag_days"] or 0) > 0))
    required = sorted(set(sampled) | set(mandatory))
    by_id = {r["event_id"]: r for r in results}
    return {"seed": seed, "sample_fraction": SECOND_CHECK_FRACTION, "sampled_event_ids": sampled,
            "mandatory_event_ids": mandatory, "required_event_ids": required,
            "pending": sum(1 for event_id in required if not by_id[event_id]["second_check"].strip())}


def terminal_summary(report: dict[str, Any], residual_count: int, claim: dict[str, Any]) -> dict[str, Any]:
    """The census v3 ``terminal_summary`` (plan 3.7, 4.6): counts only, in the approved public vocabulary.

    ``research.m4_7_coverage_census.aggregate_terminal_summary`` validates the
    result; every key below comes from its declared vocabulary.
    """
    rows = report["rows"]
    in_scope = [r for r in rows if r["scope"] == IN_SCOPE]
    curated = [r for r in in_scope if r["validation_reason"] not in ("curation_unresolved", "reference_not_last_bar")]
    unresolved = [r for r in in_scope if r["status"] == "unresolved"]
    return {
        "residual_count": int(residual_count), "claim_demand": int(claim["claim_demand"]),
        "in_scope_candidates": len(in_scope), "curated": len(curated),
        "accepted": sum(1 for r in in_scope if r["status"] == "accepted"), "unresolved": len(unresolved),
        "deferred_holdout": sum(1 for r in rows if r["scope"] == DEFERRED),
        "outside_discovery_holding_windows": sum(1 for r in rows if r["scope"] == OUTSIDE),
        "by_status": _count(rows, lambda r: r["status"]),
        "unresolved_by_reason": _count(unresolved, lambda r: r["validation_reason"]),
        "by_event_kind": _count(in_scope, lambda r: r["event_kind"] or "unresolved"),
        "by_consideration_type": _count(in_scope, lambda r: r["consideration_type"] or "unresolved"),
        "by_payment_timing": _count([r for r in curated if r["payment_timing"]], lambda r: r["payment_timing"]),
        "by_segment": _count(in_scope, lambda r: r["segment_id"]),
        "terms_availability_lag_distribution": report["terms_availability_lag_distribution"],
        "settlement_lag_distribution": report["settlement_lag_distribution"],
    }


def _read(snapshot: Snapshot, table: str, code: str, side: str | None) -> pd.DataFrame | None:
    """A discovery read confined to one side (SL-1); ``side`` is ``None`` for a one-side rule v1 snapshot."""
    return snapshot.read_discovery(table, code, side or "discovery")


def _v3_schema_fault(kind: str, row: dict[str, Any], announced: date) -> tuple[str, str | None] | None:
    """Plan 3.3 required fields: ``(reason, detail)``; a blank field never defaults to another value.

    A missing required field is ``evidence_incomplete:<field>_missing``; a present
    but unusable value is the carried ``evidence_incomplete`` with its detail kept
    in the private report, so every published reason stays in the approved
    vocabulary (``research/m4_7_coverage_census.TERMINAL_REASONS``).
    """
    if not row["source_accession"].strip():
        return "evidence_incomplete:source_accession_missing", None
    if not row["terms_known_at"].strip():
        return "evidence_incomplete:terms_known_at_missing", None
    terms = parse_strict_date(row["terms_known_at"])
    if terms is None:
        return "evidence_incomplete", "terms_known_at_unparseable"
    if terms < announced:
        return "evidence_incomplete", "terms_known_at_before_announcement"
    timing = row["payment_timing"].strip()
    if not timing:
        return "evidence_incomplete:payment_timing_missing", None
    if (timing not in PAYMENT_TIMINGS) if kind in ("cash", "mixed") else timing != "not_applicable":
        return "evidence_incomplete", "payment_timing_invalid"
    if timing == "delayed_evidenced":
        if not row["payment_date"].strip():
            return "evidence_incomplete:payment_date_missing", None
        if parse_strict_date(row["payment_date"]) is None:
            return "evidence_incomplete", "payment_date_unparseable"
        if not row["payment_source_accession"].strip():
            return "evidence_incomplete:payment_source_accession_missing", None
    elif row["payment_date"].strip():
        return "evidence_incomplete", "payment_date_not_applicable"
    if row["second_check"].strip() not in ("", "agree", "disagree"):
        return "evidence_incomplete", "second_check_invalid"
    return None


def _validate_row_v3(
    snapshot: Snapshot, calendar: pd.DatetimeIndex, masters: dict[str, dict[str, Any]],
    row: dict[str, Any], last_bar: int, segment: Any,
) -> dict[str, Any]:
    """Terms pass, then the projection pass with the four timing bounds (plan 3.4, 3.6)."""
    kind, side = row["consideration_type"], segment.side
    code = masters[row["permanent_id"]]["vendor_code"]
    announced, completed = parse_strict_date(row["announcement_date"]), parse_strict_date(row["completion_date"])
    cash, ratio = _number(row["cash_per_share"]), _number(row["exchange_ratio"])
    acquirer = row["acquirer_permanent_id"].strip()
    settlement = last_bar + 1
    reference = calendar[last_bar]
    timing: dict[str, Any] = {"reference_date": reference.date().isoformat(),
                              "effective_date": calendar[settlement].date().isoformat()}

    def unresolved(reason: str, **fields: Any) -> dict[str, Any]:
        return _result_v3(row, "unresolved", reason, segment, terms_pass="terms_invalid", **timing, **fields)

    if kind == "unresolved":
        return unresolved("curation_unresolved")
    complete = (row["event_kind"] in EVENT_KINDS and kind in BASIS and announced is not None
                and completed is not None and row["source_evidence"].strip())
    schema = None if not complete else _v3_schema_fault(kind, row, announced)
    if schema is not None:
        return unresolved(schema[0], validation_detail=schema[1])
    fault = "evidence_incomplete" if not complete else _consideration_fault(kind, row, cash, ratio, acquirer)
    if fault is not None:
        return unresolved(fault)
    terms = parse_strict_date(row["terms_known_at"])
    timing.update(terms_known_at=terms.isoformat(), terms_availability_lag_days=(terms - announced).days)
    if kind in ("cash", "mixed") and row["cash_currency"].strip() != "USD":
        return unresolved("terminal_currency_unsupported")
    if row["payment_timing"].strip() == "unknown":
        return unresolved(PAYMENT_UNKNOWN)
    if row["second_check"].strip() == "disagree":
        return unresolved(SECOND_CHECK_DISAGREE)
    if pd.Timestamp(announced) > reference:
        return unresolved("known_at_after_reference")
    completion_row = int(calendar.searchsorted(pd.Timestamp(completed)))
    lag = completion_row - settlement
    timing["settlement_lag_rows"] = lag
    if lag < -1:
        return unresolved("settlement_lag_negative")
    acquirer_code = None
    if kind in ("stock", "mixed"):
        record = masters.get(acquirer)
        valuation = calendar[completion_row] if completion_row < len(calendar) else None
        timing["valuation_row"] = None if valuation is None else valuation.date().isoformat()
        dates = None if record is None else read_bar_dates(snapshot, record["vendor_code"])
        if (valuation is None or record is None or record["resolution"] != "resolved" or dates is None
                or valuation not in dates or not record["first_bar"] <= timing["valuation_row"] <= record["last_bar"]
                or completion_row > segment.feature_ceiling_row):
            return unresolved("acquirer_bar_missing")
        acquirer_code = record["vendor_code"]
    tables = [("splits", code), ("dividends", code)] + ([("splits", acquirer_code)] if acquirer_code else [])
    if not all(snapshot.evidence_valid(table, table_code, side or "discovery") for table, table_code in tables):
        return unresolved("terminal_basis_ambiguous:corporate_action_evidence_missing",
                          corporate_action_evidence_status="missing")
    timing["corporate_action_evidence_status"] = "valid"
    target = _discovery_eod(snapshot, code, side)
    p_ref, adjusted = float(target.loc[reference, "close"]), float(target.loc[reference, "adjusted_close"])
    target_actions = _dates(snapshot, "splits", code, side) | _dates(snapshot, "dividends", code, side)
    acquirer_splits = _dates(snapshot, "splits", acquirer_code, side) if acquirer_code else set()
    valuation_day = calendar[completion_row] if acquirer_code else None
    if (abs(adjusted / p_ref - 1.0) > BASIS_TOLERANCE or calendar[settlement] in target_actions
            or (acquirer_code is not None and valuation_day in acquirer_splits)):
        return unresolved("terminal_basis_ambiguous")
    acquirer_close = None
    if acquirer_code is not None:
        frame = _discovery_eod(snapshot, acquirer_code, side)
        if frame is None or valuation_day not in frame.index:
            return unresolved("acquirer_bar_missing")
        acquirer_close = float(frame.loc[valuation_day, "close"])
    rho = (-1.0 if kind == "evidenced_worthless" else cash / p_ref - 1.0 if kind == "cash"
           else ratio * acquirer_close / p_ref - 1.0 if kind == "stock" else (cash + ratio * acquirer_close) / p_ref - 1.0)
    if rho < -1.0:
        raise SnapshotRefusal("terminal_return_below_minus_one", row["event_id"])
    if rho > UNJUSTIFIED_RETURN and not row["notes"].strip():
        return unresolved("terminal_return_unjustified", terminal_return=rho)
    failures = []
    if kind in ("cash", "evidenced_worthless") and lag > CASH_LAG_MAX:
        failures.append("settlement_lag_exceeds_3_rows")
    if kind in ("stock", "mixed") and lag not in STOCK_LAGS:
        failures.append("stock_consideration_lag_positive")
    if terms > reference.date():
        failures.append(TERMS_LATE)
    if row["payment_timing"].strip() == "delayed_evidenced":
        timing["payment_lag_rows"] = int(calendar.searchsorted(pd.Timestamp(parse_strict_date(row["payment_date"])))) \
            - settlement
        if timing["payment_lag_rows"] > PAYMENT_LAG_MAX:
            failures.append(PAYMENT_LATE)
    if failures:
        return _result_v3(row, "unresolved", failures[0], segment, terms_pass="terms_valid", timing_failures=failures,
                          terminal_return=rho, **timing)
    return _result_v3(row, "accepted", None, segment, terms_pass="terms_valid", terminal_return=rho,
                      return_basis=BASIS[kind], known_at=max(announced, terms).isoformat(), **timing)


def _discovery_eod(snapshot: Snapshot, code: str, side: str | None = None) -> pd.DataFrame | None:
    frame = _read(snapshot, "eod", code, side)
    return None if frame is None else frame.assign(date=pd.DatetimeIndex(frame["date"])).set_index("date")


def _dates(snapshot: Snapshot, table: str, code: str, side: str | None = None) -> set[pd.Timestamp]:
    frame = _read(snapshot, table, code, side)
    if frame is None:
        return set()
    if table == "dividends":
        frame = frame[frame["value"] > 0]
    return set(pd.DatetimeIndex(frame["date"]))


def _lag_distribution(results: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    distribution: dict[str, dict[str, int]] = {}
    for result in results:
        lag = result["settlement_lag_rows"]
        if lag is None:
            continue
        key = str(lag) if -1 <= lag <= CASH_LAG_MAX else ("<-1" if lag < -1 else ">3")
        bucket = distribution.setdefault(result["consideration_type"], {})
        bucket[key] = bucket.get(key, 0) + 1
    return {kind: dict(sorted(values.items())) for kind, values in sorted(distribution.items())}


def engine_events_bytes(report_bytes: bytes) -> bytes:
    """The projection of a validation report: a digest header line, then the seven engine fields of accepted rows."""
    report = json.loads(report_bytes)
    rows = [{field: r[field] for field in ENGINE_FIELDS} for r in report["rows"] if r["status"] == "accepted"]
    header = f"{EVENTS_HEADER}{sha256_bytes(report_bytes)}\n".encode("utf-8")
    return header + csv_bytes(pd.DataFrame(rows, columns=list(ENGINE_FIELDS)))


def current_validation(snapshot: Snapshot) -> tuple[bytes, str]:
    """The validation report's bytes, refused unless it matches the current manifest and curated evidence (S7)."""
    path = snapshot.root / VALIDATION
    if not path.is_file():
        raise SnapshotRefusal("derived_artifact_missing", VALIDATION)
    report_bytes = path.read_bytes()
    report = json.loads(report_bytes)
    inputs = require_current(snapshot, report.get("discovery_inputs_sha256"), VALIDATION)
    evidence = snapshot.root / CURATED
    if not evidence.is_file() or sha256_bytes(evidence.read_bytes()) != report.get("curated_evidence_sha256"):
        raise SnapshotRefusal(EVIDENCE_MISMATCH, CURATED)
    return report_bytes, inputs


def require_current_terminal(snapshot: Snapshot) -> tuple[dict[str, Any], str]:
    """Refuse unless the engine event table is exactly the projection of the current validation report.

    Consumers call this before building masks, support, or census metrics, so
    an event the current validation no longer accepts can never settle an asset.
    """
    report_bytes, inputs = current_validation(snapshot)
    events = snapshot.root / ENGINE_EVENTS
    if not events.is_file():
        raise SnapshotRefusal("derived_artifact_missing", ENGINE_EVENTS)
    if events.read_bytes() != engine_events_bytes(report_bytes):
        raise SnapshotRefusal(EVENTS_MISMATCH, ENGINE_EVENTS)
    return json.loads(report_bytes), inputs


def project(snapshot_dir: Path | str) -> pd.DataFrame:
    """Write the seven engine fields for every accepted row of the current validation report (plan 3.5)."""
    snapshot = Snapshot.open(snapshot_dir)
    report_bytes, _ = current_validation(snapshot)
    payload = engine_events_bytes(report_bytes)
    write_bytes(snapshot.root / ENGINE_EVENTS, payload)
    return pd.read_csv(io.BytesIO(payload), skiprows=1, dtype=str, keep_default_na=False)


def read_engine_events(snapshot_dir: Path | str) -> pd.DataFrame:
    """Parse the engine event table below its digest header line."""
    path = Path(snapshot_dir) / ENGINE_EVENTS
    if not path.is_file():
        raise SnapshotRefusal("derived_artifact_missing", ENGINE_EVENTS)
    payload = path.read_bytes()
    if not payload.startswith(EVENTS_HEADER.encode("utf-8")):
        raise SnapshotRefusal(EVENTS_MISMATCH, ENGINE_EVENTS)
    frame = pd.read_csv(io.BytesIO(payload), skiprows=1, dtype={"event_id": str, "permanent_id": str,
                                                                 "return_basis": str})
    for column in ("effective_date", "known_at", "reference_date"):
        frame[column] = pd.to_datetime(frame[column])
    frame["terminal_return"] = frame["terminal_return"].astype(float)
    return frame


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m research.m4_7_terminal_evidence")
    parser.add_argument("command", choices=("template", "validate", "project"))
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--data-dir", default=None)
    args = parser.parse_args(argv)
    snapshot_dir = snapshot_dir_from_args(args)
    try:
        if args.command == "template":
            print(json.dumps({"template_rows": len(write_template(snapshot_dir))}))
        elif args.command == "validate":
            print(json.dumps(validate(snapshot_dir)["counts"], sort_keys=True))
        else:
            print(json.dumps({"engine_events": len(project(snapshot_dir))}))
    except SnapshotRefusal as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
