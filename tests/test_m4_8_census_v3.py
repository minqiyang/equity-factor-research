"""M4.8 Stage A: census v3 readiness, membership census, and public outputs (plan 5; T-CEN3, T-PUB-1)."""

from __future__ import annotations

import json

import pytest

from data.holdout_partition import SnapshotRefusal
from m4_7_snapshot_support import entry
from m4_8_snapshot_support import ALL_ROWS, HS_ROW, bars2, snapshot_v2, split_row, supplement_row
from research.m4_7_coverage_census import (
    derive_readiness_v3,
    halt_counts,
    main as census_main,
    potentially_held,
    run_census_v3,
    run_membership_census,
)

import numpy as np


def clean():
    return {"pre_ic_months": 70, "unresolved_change_fraction": 0.0, "failing_anchors": [],
            "unpriced_absent_fraction": {"pre": 0.0, "post": 0.0}, "unpriced_eligible_fraction": {"pre": 0.0, "post": 0.0},
            "residual_count": 0, "untradeable_fraction": 0.0, "identity_refusal_fraction": 0.0,
            "off_calendar_fraction": 0.0, "calendar_covers_coverage_start": True, "benchmark_complete": True,
            "snapshot_integrity": True, "holdout_band_after_identity": True, "retrieval_complete": True,
            "total_ic_months": 130, "vp2_revisit_required": False, "seal_carry_passed": True, "discrepancy_fraction": 0.0}


SINGLE_FAILURES = [
    ("R3-1", {"pre_ic_months": 33}, "blocked:insufficient_pre_segment"),
    ("R3-2a", {"unresolved_change_fraction": 0.021}, "blocked:unresolved_membership_changes"),
    ("R3-2b", {"failing_anchors": [{"month_end": "2019-06-30"}]}, "blocked:anchor_count_delta"),
    ("R3-2c", {"unpriced_absent_fraction": {"pre": 0.011, "post": 0.0}}, "blocked:unpriced_absent_members"),
    ("R3-3", {"unpriced_eligible_fraction": {"pre": 0.0, "post": 0.051}}, "blocked:unpriced_eligible_member_days"),
    ("R3-4", {"residual_count": 1}, "blocked:residual_unevidenced_disappearance"),
    ("R3-5", {"untradeable_fraction": 0.0011}, "ready_with_caveats:halt_frequency"),
    ("R3-6/R-CENSUS-3", {"identity_refusal_fraction": 0.06}, "blocked:identity_refusal_fraction"),
    ("R3-7", {"total_ic_months": 59}, "blocked:insufficient_ic_months"),
    ("R3-8", {"vp2_revisit_required": True}, "ready_with_caveats:vp2_revisit"),
    ("R3-9", {"seal_carry_passed": False}, "blocked:seal_carry_mismatch"),
    ("R3-10", {"discrepancy_fraction": 0.051}, "ready_with_caveats:membership_discrepancies"),
]


def test_t_cen3_clean_inputs_are_ready():
    readiness = derive_readiness_v3(clean())
    assert readiness["status"] == "ready" and readiness["failures"] == []
    assert list(readiness["rules"]) == ["R3-1", "R3-2a", "R3-2b", "R3-2c", "R3-3", "R3-4", "R3-5", "R3-6", "R3-7",
                                        "R3-8", "R3-9", "R3-10"]


@pytest.mark.parametrize("rule, change, code", SINGLE_FAILURES, ids=[case[0] for case in SINGLE_FAILURES])
def test_t_cen3_1_to_12_each_rule_fails_alone_with_its_code(rule, change, code):
    readiness = derive_readiness_v3({**clean(), **change})
    assert readiness["failures"] == [{"rule": rule, "result": code}]
    expected = code if code.startswith("blocked:") else "ready_with_caveats:" + code.split(":", 1)[1]
    assert readiness["status"] == expected


def test_t_cen3_r3_6_carries_the_m47_codes():
    readiness = derive_readiness_v3({**clean(), "benchmark_complete": False})
    assert readiness["failures"] == [{"rule": "R3-6/R-CENSUS-5", "result": "blocked:benchmark_gap"}]
    readiness = derive_readiness_v3({**clean(), "holdout_band_after_identity": False})
    assert readiness["status"] == "ready_with_caveats:holdout_breadth_after_identity"


def test_t_cen3_13_combined_failures_report_the_first_in_table_order_and_list_every_rule():
    both = derive_readiness_v3({**clean(), "residual_count": 2, "pre_ic_months": 10})
    assert both["status"] == "blocked:insufficient_pre_segment"
    assert [f["rule"] for f in both["failures"]] == ["R3-1", "R3-4"]
    mixed = derive_readiness_v3({**clean(), "untradeable_fraction": 0.5, "total_ic_months": 10})
    assert mixed["status"] == "blocked:insufficient_ic_months"
    assert [f["rule"] for f in mixed["failures"]] == ["R3-5", "R3-7"]
    caveats = derive_readiness_v3({**clean(), "untradeable_fraction": 0.5, "discrepancy_fraction": 0.5})
    assert caveats["status"] == "ready_with_caveats:halt_frequency,membership_discrepancies"


def test_potentially_held_sets_carry_locks_and_halts_count_from_bar_presence():
    bars = np.ones((12, 2), dtype=bool)
    bars[6, 0] = False            # asset 0 halts on the second execution row
    bars[8:10, 1] = False         # asset 1 halts inside a window and resumes
    s_mask = np.zeros((12, 2), dtype=bool)
    s_mask[3, 0] = True           # signal row of the first reset
    s_mask[5, 1] = True
    held = potentially_held(s_mask, bars, [4, 6])
    assert held[4].tolist() == [True, False] and held[6].tolist() == [True, True]
    counts = halt_counts(held, bars, {4: 6, 6: 10})
    assert counts == {"potentially_held_cells": 3, "untradeable_execution_cells": 1, "unmarked_halt_rows": 3}


def _census_fixture(tmp_path, monkeypatch, name="CEN"):
    codes = {"AAA.US": bars2(ALL_ROWS), "MIS.US": (bars2(ALL_ROWS), 404),
             "INV.US": (bars2(ALL_ROWS), [split_row(HS_ROW + 10, "0/1")])}
    entries = [entry("AAA", "2018-01-02", name="Alpha Holdings"), entry("MIS", "2018-01-02", name="Missing Evidence Co"),
               entry("INV", "2018-01-02", name="Invalid Split Co")]
    curated = {"supplement": [supplement_row("MS-1", "absent_member_add", "UNP.US", "2018-03-01")]}
    return snapshot_v2(tmp_path, monkeypatch, name, entries, codes, curated=curated)


LOGS = {"pre": ["discovery_pre"], "post": ["discovery_post"]}


def test_census_v3_end_to_end_on_a_rule_v2_snapshot(tmp_path, monkeypatch):
    harness = _census_fixture(tmp_path, monkeypatch)
    result = run_census_v3(harness.snapshot_dir, terminal_summary={"residual_count": 0}, segment_access_logs=LOGS,
                           reports_dir=tmp_path / "reports")
    public = result["public"]
    pre, post = public["per_segment"]["pre"], public["per_segment"]["post"]
    assert public["seal"]["carry_check"]["passed"] is True
    assert (pre["ic_months"], post["ic_months"]) == (12, 5) and public["ic_supply"]["total_ic_months"] == 17
    assert pre["volume_basis_unverified"]["codes"] == 2 and pre["volume_basis_unverified"]["eligible_member_days"] > 0
    assert post["volume_basis_unverified"] == {"codes": 0, "eligible_member_days": 0}
    assert pre["unpriced_absent_member_days"] > 0 and pre["unpriced_absent_fraction"] > 0
    assert "no_containing_episode:no_vendor_bars:absent" in pre["eligible_unpriced_member_days"]
    assert "volume_basis_unverified_by_reason" not in pre
    readiness = public["census_readiness"]
    assert readiness["status"] == "blocked:insufficient_pre_segment"
    assert {"R3-1", "R3-7"} <= {f["rule"] for f in readiness["failures"]}
    detail = json.loads((harness.snapshot_dir / "census/census_detail_v3.json").read_bytes())
    assert set(detail["volume_basis_unverified_by_reason"]["pre"]) == {
        "volume_basis_unverified:later_split_invalid", "volume_basis_unverified:split_evidence_missing"}
    missing_logs = run_census_v3(harness.snapshot_dir, terminal_summary={"residual_count": 0}, segment_access_logs=None,
                                 reports_dir=tmp_path / "reports")
    assert missing_logs["public"]["seal"]["carry_check"]["checks"]["segment_logs_open_own_side_only"] is False
    assert "R3-9" in {f["rule"] for f in missing_logs["public"]["census_readiness"]["failures"]}
    crossed = run_census_v3(harness.snapshot_dir, terminal_summary={"residual_count": 0}, reports_dir=tmp_path / "r2",
                            segment_access_logs={"pre": ["discovery_pre", "discovery_post"], "post": ["discovery_post"]})
    assert crossed["public"]["seal"]["carry_check"]["passed"] is False
    with pytest.raises(SnapshotRefusal) as refused:
        run_census_v3(harness.snapshot_dir, terminal_summary={}, segment_access_logs=LOGS, reports_dir=tmp_path / "r3")
    assert refused.value.code == "terminal_summary_incomplete"


def test_t_pub_1_public_outputs_hold_no_code_name_or_private_path(tmp_path, monkeypatch):
    harness = _census_fixture(tmp_path, monkeypatch, name="PUB")
    reports = tmp_path / "reports"
    run_census_v3(harness.snapshot_dir, terminal_summary={"residual_count": 0}, segment_access_logs=LOGS,
                  reports_dir=reports)
    run_membership_census(harness.snapshot_dir, harness.snapshot_dir / "membership", reports_dir=reports)
    forbidden = ["AAA", "MIS.US", "INV", "UNP.US", "Alpha Holdings", "Missing Evidence", str(tmp_path), "private"]
    for path in sorted(reports.iterdir()):
        text = path.read_text(encoding="utf-8")
        assert not [token for token in forbidden if token in text], path.name
    with pytest.raises(SnapshotRefusal) as refused:
        run_census_v3(harness.snapshot_dir, terminal_summary={"residual_count": 0, "note": "AAA.US"},
                      segment_access_logs=LOGS, reports_dir=tmp_path / "leak")
    assert refused.value.code == "public_output_leak" and not (tmp_path / "leak" / "m4_8_coverage_census_v3.json").exists()
    with pytest.raises(SnapshotRefusal) as refused:
        run_census_v3(harness.snapshot_dir, terminal_summary={"residual_count": 0, "note": str(harness.snapshot_dir)},
                      segment_access_logs=LOGS, reports_dir=tmp_path / "leak")
    assert refused.value.code == "public_output_leak"


def test_membership_census_command_writes_private_detail_and_public_counts(tmp_path, monkeypatch, capsys):
    harness = _census_fixture(tmp_path, monkeypatch, name="MCLI")
    curated = harness.snapshot_dir / "membership"
    code = census_main(["membership-census", "--snapshot-id", "MCLI", "--data-dir", str(harness.data_dir),
                        "--curated-dir", str(curated), "--reports-dir", str(tmp_path / "reports")])
    assert code == 0
    summary = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert summary["gate_g1"].startswith("blocked:")
    public = json.loads((tmp_path / "reports" / "m4_8_membership_census.json").read_bytes())
    assert public["absent_members"] == {"priced": 0, "unpriced": 1, "identity_refused": 0}
    assert (curated / "membership_census_detail.json").is_file() and (curated / "membership_discrepancies.csv").is_file()
    terminal = tmp_path / "terminal.json"
    terminal.write_text(json.dumps({"residual_count": 0}))
    logs = tmp_path / "logs.json"
    logs.write_text(json.dumps(LOGS))
    assert census_main(["census-v3", "--snapshot-id", "MCLI", "--data-dir", str(harness.data_dir), "--terminal-summary",
                        str(terminal), "--segment-access-log", str(logs), "--reports-dir", str(tmp_path / "reports")]) == 0
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1])["census_readiness"] == "blocked:insufficient_pre_segment"
