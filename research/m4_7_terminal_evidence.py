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

import pandas as pd

from data.holdout_partition import SnapshotRefusal, parse_strict_date, sha256_bytes
from research.m4_7_universe_build import (
    BUILD_MANIFEST,
    INTERVAL_RESULTS,
    SECURITY_MASTER,
    Snapshot,
    canonical_json,
    csv_bytes,
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


def write_template(snapshot_dir: Path | str) -> pd.DataFrame:
    """One template row per candidate permanent ID; ``deferred_holdout`` when ``S <= i_H`` (plan 3.1)."""
    snapshot, calendar, i_h, master, inputs = _load(snapshot_dir)
    rows = []
    for record in master.to_dict(orient="records"):
        if record["permanent_id"] and record["has_delisting_candidate_interval"] == "True":
            settlement = calendar.get_loc(pd.Timestamp(record["last_bar"])) + 1
            rows.append({
                **dict.fromkeys(EVIDENCE_COLUMNS, ""),
                "event_id": f"TE-{record['permanent_id']}-{calendar[settlement].date().isoformat()}",
                "permanent_id": record["permanent_id"],
                "curation_status": "deferred_holdout" if settlement <= i_h else "unresolved",
                "discovery_inputs_sha256": inputs,
            })
    frame = pd.DataFrame(rows, columns=[*EVIDENCE_COLUMNS, "discovery_inputs_sha256"])
    write_bytes(snapshot.root / TEMPLATE, csv_bytes(frame))
    return frame


def validate(snapshot_dir: Path | str) -> dict[str, Any]:
    """Apply the section 3.6 codes to the curated table and write the validation report."""
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


def _discovery_eod(snapshot: Snapshot, code: str) -> pd.DataFrame | None:
    frame = snapshot.read_discovery("eod", code)
    return None if frame is None else frame.assign(date=pd.DatetimeIndex(frame["date"])).set_index("date")


def _dates(snapshot: Snapshot, table: str, code: str) -> set[pd.Timestamp]:
    frame = snapshot.read_discovery(table, code)
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
