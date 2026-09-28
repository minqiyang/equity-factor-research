"""M4.8 Stage A: census v3 readiness, membership census, and public outputs (plan 5; T-CEN3, T-PUB-1)."""

from __future__ import annotations

import json

import pytest

from data.holdout_partition import SnapshotRefusal
from m4_7_snapshot_support import entry
from m4_8_snapshot_support import ALL_ROWS, HS_ROW, bars2, change_row, snapshot_v2, split_row, supplement_row
from research.m4_7_universe_build import Snapshot
from research.m4_7_coverage_census import (
    aggregate_terminal_summary,
    derive_readiness_v3,
    halt_counts,
    main as census_main,
    potentially_held,
    public_leak_scan,
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


def _census_fixture(tmp_path, monkeypatch, name="CEN", changes=()):
    codes = {"AAA.US": bars2(ALL_ROWS), "MIS.US": (bars2(ALL_ROWS), 404),
             "INV.US": (bars2(ALL_ROWS), [split_row(HS_ROW + 10, "0/1")])}
    entries = [entry("AAA", "2018-01-02", name="Alpha Holdings"), entry("MIS", "2018-01-02", name="Missing Evidence Co"),
               entry("INV", "2018-01-02", name="Invalid Split Co")]
    curated = {"supplement": [supplement_row("MS-1", "absent_member_add", "UNP.US", "2018-03-01")], "changes": list(changes)}
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


def test_t_cen3_r3_10_counts_vendor_only_entries_active_in_the_pre_segment(tmp_path, monkeypatch):
    def r3_10(result):
        return {"rule": "R3-10", "result": "ready_with_caveats:membership_discrepancies"} in \
            result["public"]["census_readiness"]["failures"]

    vendor_only = run_census_v3(_census_fixture(tmp_path / "a", monkeypatch, name="VO").snapshot_dir,
                                terminal_summary={"residual_count": 0}, segment_access_logs=LOGS,
                                reports_dir=tmp_path / "a" / "reports")
    assert r3_10(vendor_only)
    changes = [change_row(f"RC-{i}", "2018-01-02", "add", code) for i, code in enumerate(("AAA.US", "MIS.US", "INV.US"))]
    matched = run_census_v3(_census_fixture(tmp_path / "b", monkeypatch, name="VM", changes=changes).snapshot_dir,
                            terminal_summary={"residual_count": 0}, segment_access_logs=LOGS,
                            reports_dir=tmp_path / "b" / "reports")
    assert not r3_10(matched)


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
    for note in ("AAA.US", str(harness.snapshot_dir)):
        with pytest.raises(SnapshotRefusal) as refused:
            run_census_v3(harness.snapshot_dir, terminal_summary={"residual_count": 0, "note": note},
                          segment_access_logs=LOGS, reports_dir=tmp_path / "leak")
        assert refused.value.code == "terminal_summary_not_aggregate"
        assert not (tmp_path / "leak" / "m4_8_coverage_census_v3.json").exists()
    snapshot = Snapshot.open(harness.snapshot_dir)
    assert public_leak_scan('{"x": "AAA.US"}', snapshot) == ["code"]
    assert public_leak_scan(f'{{"x": "{harness.snapshot_dir}"}}', snapshot) == ["path:absolute", "path:sp500_pit_PUB"]


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


PRIVATE_EVIDENCE = "/private/vendor-evidence/terminal.csv"
DETAIL_SUMMARIES = [
    {"residual_count": 1, "unresolved": [{"permanent_id": "UNP.US#E1", "source_file": PRIVATE_EVIDENCE}]},
    {"residual_count": 1, "unresolved_by_permanent_id": {"UNP.US#E1": 1}},
    {"residual_count": 1, "evidence_file": PRIVATE_EVIDENCE},
    {"residual_count": 0, "by_code": {"unp": 1}},
    {"residual_count": 0, "unresolved:unp": 1},
    {"residual_count": 0, "claims": {"pending": {"cash": 1}}},
    {"residual_count": True},
    {"residual_count": -1},
]


@pytest.mark.parametrize("summary", DETAIL_SUMMARIES, ids=[f"detail_{i}" for i in range(len(DETAIL_SUMMARIES))])
def test_t_pub_1_census_v3_refuses_a_terminal_summary_with_per_asset_detail_or_paths(tmp_path, monkeypatch, summary):
    # M48A-A1-M02: UNP.US is a curated-only absent member outside the vendor and requested code lists.
    harness = _census_fixture(tmp_path, monkeypatch, name="DET")
    with pytest.raises(SnapshotRefusal) as refused:
        run_census_v3(harness.snapshot_dir, terminal_summary=summary, segment_access_logs=LOGS,
                      reports_dir=tmp_path / "reports")
    assert refused.value.code == "terminal_summary_not_aggregate"
    assert not (tmp_path / "reports").exists()
    assert not (harness.snapshot_dir / "census/census_detail_v3.json").exists()


def test_t_pub_1_census_v3_publishes_only_the_aggregate_projection(tmp_path, monkeypatch, capsys):
    harness = _census_fixture(tmp_path, monkeypatch, name="AGG")
    summary = {"unresolved_by_reason": {"unresolved:payment_timing_unknown": 2, "evidence_incomplete:terms_known_at_missing": 1},
               "settlement_lag_distribution": {"cash": {"-1": 1, "0": 4, "3": 1}}, "residual_count": 0, "claim_demand": 0}
    result = run_census_v3(harness.snapshot_dir, terminal_summary=summary, segment_access_logs=LOGS,
                           reports_dir=tmp_path / "reports")
    assert result["public"]["terminal_evidence"] == aggregate_terminal_summary(summary)
    assert list(result["public"]["terminal_evidence"]) == ["claim_demand", "residual_count", "settlement_lag_distribution",
                                                          "unresolved_by_reason"]
    snapshot = Snapshot.open(harness.snapshot_dir)
    assert public_leak_scan('{"id": "UNP.US#E1"}', snapshot) == ["code"]
    assert public_leak_scan(f'{{"file": "{PRIVATE_EVIDENCE}"}}', snapshot) == ["path:absolute"]
    text = (tmp_path / "reports" / "m4_8_coverage_census_v3.json").read_text()
    assert "UNP" not in text and "/private" not in text
    detail = tmp_path / "detail.json"
    detail.write_text(json.dumps(DETAIL_SUMMARIES[0]))
    assert census_main(["census-v3", "--snapshot-id", "AGG", "--data-dir", str(harness.data_dir), "--terminal-summary",
                        str(detail), "--reports-dir", str(tmp_path / "cli")]) == 1
    assert "terminal_summary_not_aggregate" in capsys.readouterr().err


def _split_volume_fixture(tmp_path, monkeypatch, name, adjusted_volume):
    """Ten codes with a 2:1 pre-side split; raw volume doubles at the split, so dollar turnover is continuous."""
    split = 150
    codes, entries = {}, []
    for i in range(10):
        base = (lambda k: (lambda r: (100.0 + k) / (2.0 if r >= split else 1.0)))(i)
        raw = (lambda k: (lambda r: (1000.0 + 10.0 * k) * (2.0 if r >= split else 1.0)))(i)
        served = (lambda f: (lambda r: f(r) * (2.0 if r < split else 1.0)))(raw) if adjusted_volume else raw
        eod = bars2(ALL_ROWS, close=base, adjusted=lambda r, f=base: f(r) / (2.0 if r < split else 1.0), volume=served)
        codes[f"S{i:02d}.US"] = (eod, [split_row(split, "2/1")])
        entries.append(entry(f"S{i:02d}", "2018-01-02"))
    return snapshot_v2(tmp_path, monkeypatch, name, entries, codes)


@pytest.mark.parametrize("adjusted_volume, verdict", [(True, "consistent"), (False, "contradicted")])
def test_census_v3_reports_the_vp1_volume_half_per_segment(tmp_path, monkeypatch, adjusted_volume, verdict):
    # M48A-A1-A01: VP-1 on the pre side's attributed splits; the post side holds no split.
    harness = _split_volume_fixture(tmp_path, monkeypatch, f"VP{int(adjusted_volume)}", adjusted_volume)
    result = run_census_v3(harness.snapshot_dir, terminal_summary={"residual_count": 0}, segment_access_logs=LOGS,
                           reports_dir=tmp_path / "reports")
    pre = result["public"]["per_segment"]["pre"]["volume_basis_split_diagnostic"]
    post = result["public"]["per_segment"]["post"]["volume_basis_split_diagnostic"]
    assert (pre["rows"], pre["a1_volume_half"]) == (10, verdict)
    assert pre["median_ell"] == pytest.approx(0.0 if adjusted_volume else 1.0, abs=1e-9)
    assert (post["rows"], post["a1_volume_half"]) == (0, "insufficient")
    assert "VP-1 volume half `pre`" in (tmp_path / "reports" / "m4_8_coverage_census_v3.md").read_text()


def test_t_pub_1_the_public_writer_refuses_a_payload_that_holds_a_code_or_path(tmp_path, monkeypatch):
    from research.m4_7_coverage_census import _write_public

    harness = _census_fixture(tmp_path, monkeypatch, name="WRT")
    snapshot = Snapshot.open(harness.snapshot_dir)
    for payload in ({"note": "UNP.US"}, {"note": "Alpha Holdings"}, {"note": PRIVATE_EVIDENCE}):
        with pytest.raises(SnapshotRefusal) as refused:
            _write_public(tmp_path / "reports", "probe", payload, "", snapshot, ())
        assert refused.value.code == "public_output_leak"
    assert not (tmp_path / "reports").exists()


SEAT1_REPRODUCTIONS = [
    {"residual_count": 0, "raw_vendor_row": {"open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000}},
    {"residual_count": 0, "terminal_row": {"cash_per_share": 25, "exchange_ratio": 1}},
]
UNAPPROVED_SUMMARIES = [
    {"residual_count": 1, "by_asset": {"unp_us_e1": 1}},
    {"residual_count": 1, "residual_unp": 1},
    {"residual_count": 1, "unp1": 1},
    {"residual_count": 1, "aaa_us_e1": 1},
    {"residual_count": 1, "unresolved_by_reason": {"unp_us_e1": 1}},
    {"residual_count": 1, "unresolved_by_reason": {"unresolved:unp": 1}},
    {"residual_count": 1, "settlement_lag_distribution": {"cash": {"100": 1}}},
    {"residual_count": 1, "settlement_lag_distribution": {"unp": {"0": 1}}},
    {"residual_count": 1, "by_segment": {"pre": 1.5}},
    {"residual_count": 1, "accepted": 2.0},
    ["residual_count", 0],
]


@pytest.mark.parametrize("summary", SEAT1_REPRODUCTIONS + UNAPPROVED_SUMMARIES,
                         ids=["raw_vendor_row", "terminal_row"] + [f"unapproved_{i}" for i in range(len(UNAPPROVED_SUMMARIES))])
def test_t_pub_1_fields_outside_the_approved_schema_refuse_before_any_write(tmp_path, monkeypatch, summary):
    # M48A-A1-M02 round 2 (Seat 1 reproductions) and A2-R2-ADV-1 (Seat 2 key channel).
    harness = _census_fixture(tmp_path, monkeypatch, name="SCH")
    with pytest.raises(SnapshotRefusal) as refused:
        run_census_v3(harness.snapshot_dir, terminal_summary=summary, segment_access_logs=LOGS,
                      reports_dir=tmp_path / "reports")
    assert refused.value.code == "terminal_summary_not_aggregate"
    assert not (tmp_path / "reports").exists()
    assert not (harness.snapshot_dir / "census/census_detail_v3.json").exists()


@pytest.mark.parametrize("summary", SEAT1_REPRODUCTIONS, ids=["raw_vendor_row", "terminal_row"])
def test_t_pub_1_the_cli_refuses_seat1_reproductions_before_any_write(tmp_path, monkeypatch, capsys, summary):
    harness = _census_fixture(tmp_path, monkeypatch, name="SCLI")
    path = tmp_path / "summary.json"
    path.write_text(json.dumps(summary))
    logs = tmp_path / "logs.json"
    logs.write_text(json.dumps(LOGS))
    assert census_main(["census-v3", "--snapshot-id", "SCLI", "--data-dir", str(harness.data_dir), "--terminal-summary",
                        str(path), "--segment-access-log", str(logs), "--reports-dir", str(tmp_path / "reports")]) == 1
    assert "terminal_summary_not_aggregate" in capsys.readouterr().err
    assert not (tmp_path / "reports").exists()
    assert not (harness.snapshot_dir / "census/census_detail_v3.json").exists()


def test_the_approved_schema_accepts_every_declared_field_and_nothing_else():
    full = {
        "residual_count": 0, "in_scope_candidates": 30, "curated": 28, "accepted": 25, "unresolved": 3,
        "deferred_holdout": 2, "outside_discovery_holding_windows": 7, "claim_demand": 0,
        "contingent_component_excluded": 1,
        "by_status": {"accepted": 25, "unresolved": 3, "deferred_holdout": 2, "outside_discovery_holding_windows": 7},
        "unresolved_by_reason": {"curation_unresolved": 1, "unresolved:payment_timing_unknown": 1,
                                 "evidence_incomplete:source_accession_missing": 1},
        "by_event_kind": {"merger_or_acquisition": 20, "bankruptcy_or_liquidation": 2, "unresolved": 3},
        "by_consideration_type": {"cash": 15, "stock": 5, "mixed": 4, "evidenced_worthless": 1},
        "by_payment_timing": {"at_completion_evidenced": 19, "delayed_evidenced": 1, "not_applicable": 5},
        "by_segment": {"pre": 18, "post": 12},
        "valuation_row_offsets": {"L": 2, "S": 7},
        "terms_availability_lag_distribution": {"0": 3, "2-5": 10, ">60": 1},
        "claim_realization_lag_distribution": {},
        "settlement_lag_distribution": {"cash": {"-1": 1, "0": 14}, "stock": {"0": 5}},
    }
    assert aggregate_terminal_summary(full) == json.loads(json.dumps(full, sort_keys=True))
    for field in full:
        if field != "residual_count":
            assert aggregate_terminal_summary({"residual_count": 0, field: full[field]})[field] == full[field]
    with pytest.raises(SnapshotRefusal) as refused:
        aggregate_terminal_summary({"accepted": 1})
    assert refused.value.code == "terminal_summary_incomplete"
