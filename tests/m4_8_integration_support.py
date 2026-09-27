"""A populated rule v2 snapshot for the M4.8 Stage B integration oracles (seams I-1..I-4).

Stage A's harness (``tests/m4_8_snapshot_support.py``) retrieves twelve random-walk
members, one cash-deal disappearance on the pre side, and ``SPY.US`` into a rule
v2 snapshot with the carried seal; the terminal tooling, the v3 support
writer, census v3, and a registration v3 document follow from it. No test
opens a network connection or reads private data.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd

import research.m4_7_sp500_pit_rerun as runner
from m4_7_snapshot_support import entry
from m4_8_snapshot_support import ALL_ROWS, CAL2, HS_ROW, bars2, day2, snapshot_v2
from research.m4_7_common_support import write_support_files
from research.m4_7_coverage_census import run_census_v3, run_membership_census
from research.m4_7_terminal_evidence import CURATED, EVIDENCE_COLUMNS_V3, project, snapshot_segments, validate, \
    write_template
from research.m4_7_universe_build import Snapshot, discovery_inputs_sha256, segment_ic_resets


CODES = [f"W{k:02d}" for k in range(12)]
CASH_LAST = HS_ROW - 120            # a pre-side cash deal, settled at CASH_LAST + 1
CASH_PID = "CSH.US#E1"


def _walk(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return 40.0 * np.exp(np.cumsum(rng.normal(0.0005, 0.02, len(CAL2))))


def build(tmp_path: Path, monkeypatch, name: str = "INT") -> Path:
    """Retrieve, build, template, curate, validate, and project a rule v2 snapshot."""
    snap = retrieve(tmp_path, monkeypatch, name)
    curate_and_validate(snap)
    return snap


def retrieve(tmp_path: Path, monkeypatch, name: str = "INT") -> Path:
    """Retrieve and build the rule v2 snapshot (Stage A)."""
    codes = {f"{code}.US": bars2(ALL_ROWS, close=lambda r, p=_walk(k): float(p[r]),
                                 volume=lambda r, k=k: 1e5 * (1 + (r * 7 + k) % 5))
             for k, code in enumerate(CODES)}
    cash = _walk(99)
    codes["CSH.US"] = bars2(range(0, CASH_LAST + 1), close=lambda r: float(cash[r]))
    entries = [entry(code, "2018-01-02") for code in CODES] + [entry("CSH", "2018-01-02")]
    return snapshot_v2(tmp_path, monkeypatch, name, entries, codes).snapshot_dir


def curate_and_validate(snap: Path) -> None:
    """Write the template, curate the cash deal under schema v3, validate, and project."""
    cash = _walk(99)
    template = write_template(snap)
    rows = []
    for row in template.to_dict(orient="records"):
        record = {column: row.get(column, "") for column in EVIDENCE_COLUMNS_V3}
        if row["permanent_id"] == CASH_PID:
            record.update({"curation_status": "curated", "event_kind": "merger_or_acquisition",
                           "consideration_type": "cash", "announcement_date": day2(CASH_LAST - 30),
                           "completion_date": day2(CASH_LAST + 1), "cash_per_share": f"{cash[CASH_LAST] * 1.2:.4f}",
                           "cash_currency": "USD", "source_evidence": "8-K filed at completion",
                           "curator": "research_curator", "source_accession": "0000950123-19-000001",
                           "source_form": "8-K/2.01", "terms_known_at": day2(CASH_LAST - 30),
                           "payment_timing": "at_completion_evidenced", "second_check": "agree"})
        rows.append(record)
    pd.DataFrame(rows, columns=list(EVIDENCE_COLUMNS_V3)).to_csv(snap / CURATED, index=False)
    validate(snap)
    project(snap)


def census(snap: Path, reports: Path) -> tuple[dict, dict]:
    """Stage C membership census (writes the discrepancy file), the v3 support file, and census v3."""
    run_membership_census(snap, snap / "membership", reports_dir=reports)
    support = write_support_files(snap)
    logs = {sid: record["panel_sides_opened"] for sid, record in support["segments"].items()}
    result = run_census_v3(snap, terminal_summary=support["terminal_summary"], segment_access_logs=logs,
                           reports_dir=reports)
    return support, result


def registration(snap: Path, census_json: Path, support: dict) -> dict:
    snapshot = Snapshot.open(snap)
    calendar = snapshot.calendar()
    segments = snapshot_segments(snapshot, calendar)
    doc = copy.deepcopy(runner.REGISTERED_V3)
    doc["holdout"].update(holdout_start=snapshot.holdout_start.isoformat(),
                          holdout_end_exclusive=snapshot.holdout_end.isoformat())
    doc["discovery"]["segments"] = [
        {"segment_id": s.segment_id, "side": s.side, "anchor_row": calendar[s.anchor_row].date().isoformat(),
         "first_reset": calendar[s.first_reset_row].date().isoformat(),
         "last_ic_reset": calendar[s.last_ic_reset_row].date().isoformat(),
         "last_book_row": calendar[s.last_book_row].date().isoformat(),
         "ic_months": int(len(segment_ic_resets(calendar, s))), "prior_exposure_overlap_fraction": {}}
        for s in segments]
    horizon = max(record["max_reset_to_reset_rows"] for record in support["segments"].values())
    doc["discovery"]["max_reset_to_reset_rows"] = horizon
    doc["statistics"]["power_projection"].update(kill_reachable_projection=False,
                                                 owner_decision_o48_3="proceed_as_registered")
    doc["statistics"]["cpcv"]["holding_periods"] = horizon
    digests = {key: runner.sha256_bytes(path.read_bytes())
               for key, path in runner.bound_paths_v3(snapshot.root, census_json).items()}
    doc["snapshot"] = {"snapshot_id": snapshot.manifest["snapshot"]["id"], "retrieval_complete": True,
                       "discovery_inputs_sha256": discovery_inputs_sha256(snapshot), **digests}
    doc["costs"] = copy.deepcopy(runner.REGISTERED["costs"])
    doc["objective"] = copy.deepcopy(runner.REGISTERED["objective"])
    return doc


def write_registration(doc: dict, path: Path) -> str:
    path.write_bytes((json.dumps(doc, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    return runner.sha256_bytes(path.read_bytes())
