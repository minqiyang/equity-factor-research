"""M4.8 Stage A: partition rule v2, per-side discovery files, and the seal carry (plan 2.2; T-PART, T-SEAL3).

Every rule v2 snapshot is written by the real retrieval path from the fake
vendor on the 2018-2021 calendar (``tests/m4_8_snapshot_support.py``).
"""

from __future__ import annotations

import json
from datetime import date

import pandas as pd
import pytest

from data.holdout_partition import (
    PARTITION_RULE_V1,
    PARTITION_RULE_V2,
    SEAL_CARRY_FILE,
    SEAL_FILE,
    SEAL_V1_CONFIRMATION_V2_PATH,
    SEAL_V1_CONFIRMATION_V2_SHA256,
    SEAL_V1_DOCS_PATH,
    SEAL_V1_DOCS_SHA256,
    SEAL_V1_PROSPECTIVE_SHA256,
    SEAL_V1_WINDOW,
    PartitionWindow,
    SnapshotRefusal,
    build_seal_carry_record,
    partition_of,
    read_partition_window,
    read_seal_carry,
    side_of,
    write_prospective_seal,
)
from m4_7_snapshot_support import CAL, Harness, bars, entry, rows
from m4_8_snapshot_support import (
    ALL_ROWS,
    CAL2,
    HE_ROW,
    HOLDOUT_END,
    HOLDOUT_START,
    HS_ROW,
    N_ROWS,
    REPOSITORY_ROOT,
    HarnessV2,
    bars2,
    day2,
    dividend_row,
    manifest_entry,
    side_file,
    snapshot_v2,
    split_row,
    write_curated,
)
from research.m4_7_coverage_census import membership_census, run_census, run_census_v3
from research.m4_7_holdout_seal import seal_snapshot
from research.m4_7_universe_build import Snapshot
from research import m4_8_membership


def _dates(frame: pd.DataFrame | None) -> list[str]:
    return [] if frame is None else [d.date().isoformat() for d in pd.DatetimeIndex(frame["date"])]


def _docs(name: str) -> bytes:
    return (REPOSITORY_ROOT / name).read_bytes()


def _v2_harness(tmp_path, monkeypatch, codes, name="V2", entries=None):
    harness = HarnessV2(tmp_path, monkeypatch, snapshot_id=name)
    harness.vendor.entries = entries if entries is not None else [entry("AAA", "2018-01-02")]
    harness.vendor.code("SPY.US", bars2(ALL_ROWS))
    for code, spec in codes.items():
        harness.vendor.code(code, *spec) if isinstance(spec, tuple) else harness.vendor.code(code, spec)
    harness.retrieve()
    return harness


# ---------------------------------------------------------------- T-PART


def test_t_part_1_boundary_rows_classify_for_price_split_and_dividend_rows(tmp_path, monkeypatch):
    before, first, last, after = HS_ROW - 1, HS_ROW, HE_ROW - 1, HE_ROW
    assert [side_of(CAL2[r].date(), HOLDOUT_START, HOLDOUT_END) for r in (before, first, last, after)] == [
        "discovery_pre", "holdout", "holdout", "discovery_post"]
    boundary = (before, first, last, after)
    harness = _v2_harness(tmp_path, monkeypatch, {"AAA.US": (
        bars2(ALL_ROWS), [split_row(r, "1/1") for r in boundary], [dividend_row(r, 0.0) for r in boundary])})
    snap = harness.snapshot_dir
    for table in ("eod", "splits", "dividends"):
        pre, hold, post = (side_file(snap, table, "AAA.US", p) for p in ("discovery_pre", "holdout", "discovery_post"))
        assert day2(before) in _dates(pre) and day2(first) not in _dates(pre)
        assert {day2(first), day2(last)} <= set(_dates(hold)) and day2(before) not in _dates(hold)
        assert day2(after) not in _dates(hold) and day2(after) in _dates(post) and day2(last) not in _dates(post)


def test_t_part_2_snapshot_without_partition_rule_keeps_rule_v1(tmp_path, monkeypatch):
    harness = Harness(tmp_path, monkeypatch)
    harness.vendor.entries = [entry("AAA", "2003-06-02")]
    harness.vendor.code("SPY.US", bars(rows(0, len(CAL))))
    harness.vendor.code("AAA.US", bars(rows(0, len(CAL))), [{"date": CAL[400].date().isoformat(), "split": "1/1"}])
    snap = harness.retrieve()
    manifest = harness.manifest()
    assert "partition_rule" not in manifest["snapshot"]
    for key, value in manifest["entries"].items():
        assert set(value["partition_statuses"]) <= {"discovery", "holdout"}, key
        assert "has_row_on_or_after_holdout_start" not in value and "pre_side_volume_basis" not in value
    assert not [key for key in manifest["counters"] if "discovery_pre" in key or "discovery_post" in key]
    assert isinstance(manifest["entries"]["eod/AAA.US"]["split_evidence_basis"], str)
    window = read_partition_window(snap)
    assert window.rule == PARTITION_RULE_V1 and window.partitions == ("discovery", "holdout")
    for row in (0, 150, len(CAL) - 1):
        assert window.partition(CAL[row].date()) == partition_of(CAL[row].date(), window.holdout_end)
    assert Snapshot.open(snap).sides == ("discovery",)


def test_t_part_3_pre_holdout_rows_are_discovery_and_holdout_files_hold_the_window(tmp_path, monkeypatch):
    harness = _v2_harness(tmp_path, monkeypatch, {"AAA.US": bars2(ALL_ROWS)})
    snap = harness.snapshot_dir
    assert harness.manifest()["snapshot"]["partition_rule"] == PARTITION_RULE_V2
    assert _dates(side_file(snap, "eod", "AAA.US", "discovery_pre")) == [day2(r) for r in range(0, HS_ROW)]
    assert _dates(side_file(snap, "eod", "AAA.US", "holdout")) == [day2(r) for r in range(HS_ROW, HE_ROW)]
    assert _dates(side_file(snap, "eod", "AAA.US", "discovery_post")) == [day2(r) for r in range(HE_ROW, N_ROWS)]


def test_t_part_5_scale_check_skips_the_seal_pair_and_flags_a_one_side_step(tmp_path, monkeypatch):
    across = bars2(ALL_ROWS, close=100.0, adjusted=lambda r: 50.0 if r < HE_ROW else 100.0)
    inside_pre = bars2(ALL_ROWS, close=100.0, adjusted=lambda r: 50.0 if r < 100 else 100.0)
    harness = _v2_harness(tmp_path, monkeypatch, {"AAA.US": across, "BBB.US": inside_pre},
                          entries=[entry("AAA", "2018-01-02"), entry("BBB", "2018-01-02")])
    statuses = {code: manifest_entry(harness.snapshot_dir, "eod", code)["partition_statuses"] for code in ("AAA.US", "BBB.US")}
    assert statuses["AAA.US"] == {"discovery_pre": "valid", "discovery_post": "valid", "holdout": "valid"}
    assert statuses["BBB.US"]["discovery_pre"] == "quarantined:unverified_split"


def test_t_part_6_every_discovery_row_lands_in_exactly_one_side_file(tmp_path, monkeypatch):
    harness = _v2_harness(tmp_path, monkeypatch, {"AAA.US": (
        bars2(ALL_ROWS), [split_row(50, "1/1"), split_row(HS_ROW + 3, "1/1"), split_row(HE_ROW + 9, "1/1")],
        [dividend_row(r, 0.0) for r in (10, HS_ROW + 10, HE_ROW + 10)])})
    snap = harness.snapshot_dir
    for table in ("eod", "splits", "dividends"):
        entry_record = manifest_entry(snap, table, "AAA.US")
        assert "discovery" not in entry_record["authorized_files"]
        pre, post = (set(_dates(side_file(snap, table, "AAA.US", side))) for side in ("discovery_pre", "discovery_post"))
        assert not pre & post
        assert all(d < HOLDOUT_START.isoformat() for d in pre) and all(d >= HOLDOUT_END.isoformat() for d in post)
    served = {day2(r) for r in ALL_ROWS if not HS_ROW <= r < HE_ROW}
    eod = set(_dates(side_file(snap, "eod", "AAA.US", "discovery_pre"))) | set(_dates(side_file(snap, "eod", "AAA.US", "discovery_post")))
    assert eod == served


def test_t_part_7_a_post_side_unverified_split_quarantines_only_the_post_side(tmp_path, monkeypatch):
    step_post = bars2(ALL_ROWS, close=100.0, adjusted=lambda r: 50.0 if r < HE_ROW + 40 else 100.0)
    harness = _v2_harness(tmp_path, monkeypatch, {"AAA.US": step_post})
    statuses = manifest_entry(harness.snapshot_dir, "eod", "AAA.US")["partition_statuses"]
    assert statuses == {"discovery_pre": "valid", "discovery_post": "quarantined:unverified_split", "holdout": "valid"}
    harness2 = _v2_harness(tmp_path / "b", monkeypatch, {"AAA.US": (bars2(ALL_ROWS), [split_row(HE_ROW + 5, "x/1")])},
                           name="V2B")
    entry_record = manifest_entry(harness2.snapshot_dir, "eod", "AAA.US")
    assert entry_record["split_evidence_basis"] == {"discovery_pre": "discovery_split_table",
                                                    "discovery_post": "split_evidence_quarantined"}
    assert entry_record["partition_statuses"]["discovery_pre"] == "valid"
    assert entry_record["partition_statuses"]["discovery_post"] == "quarantined:split_evidence_quarantined"


def test_partition_rule_dispatch_refuses_ambiguous_or_mismatched_seals(tmp_path, monkeypatch):
    harness = _v2_harness(tmp_path, monkeypatch, {"AAA.US": bars2(ALL_ROWS)})
    snap = harness.snapshot_dir
    (snap / SEAL_FILE).write_bytes((snap / SEAL_CARRY_FILE).read_bytes())
    with pytest.raises(SnapshotRefusal) as refused:
        Snapshot.open(snap)
    assert refused.value.code == "holdout_seal_ambiguous"
    (snap / SEAL_FILE).unlink()
    harness.edit_manifest(lambda m: m["snapshot"].pop("partition_rule"))
    with pytest.raises(SnapshotRefusal) as refused:
        Snapshot.open(snap)
    assert refused.value.code == "partition_rule_mismatch"

    v1 = HarnessV2(tmp_path / "v1", monkeypatch, snapshot_id="V1")
    v1.vendor.entries = [entry("AAA", "2018-01-02")]
    v1.vendor.code("SPY.US", bars2(ALL_ROWS))
    v1.vendor.code("AAA.US", bars2(ALL_ROWS))
    assert v1.run("components") == 0 and v1.run("symbols") == 0
    v1.seal("2019-07-31", "2020-07-31")
    assert v1.run("calendar") == 0 and v1.run("splits") == 0
    (v1.snapshot_dir / SEAL_FILE).unlink()
    v1.carry()
    assert v1.run("eod") == 1
    assert "partition_rule" not in v1.manifest()["snapshot"]


# ---------------------------------------------------------------- T-SEAL3


def test_t_seal3_1_carry_record_comes_from_seal_v1_bytes_and_verifies_the_bound_hashes(tmp_path, monkeypatch):
    seal_v1 = json.loads(_docs(SEAL_V1_DOCS_PATH))
    assert {key: seal_v1[key] for key in SEAL_V1_WINDOW} == SEAL_V1_WINDOW
    harness = _v2_harness(tmp_path, monkeypatch, {"AAA.US": bars2(ALL_ROWS)})
    record = read_seal_carry(harness.snapshot_dir)
    assert {key: record[key] for key in SEAL_V1_WINDOW} == SEAL_V1_WINDOW
    assert record["carried_from"] == {
        "seal_v1_docs_path": SEAL_V1_DOCS_PATH, "seal_v1_docs_sha256": SEAL_V1_DOCS_SHA256,
        "seal_v1_prospective_sha256": SEAL_V1_PROSPECTIVE_SHA256,
        "seal_v1_confirmation_v2_path": SEAL_V1_CONFIRMATION_V2_PATH,
        "seal_v1_confirmation_v2_sha256": SEAL_V1_CONFIRMATION_V2_SHA256, "private_prospective_verified": False}
    assert record["prior_exposures"] == seal_v1["prior_exposures"] and record["prior_exposure_status"] == "carried_stated_v1"
    assert record["seal_bracket_computation_forbidden"] is True
    assert record["partitioner_value_access"][0]["rows"] == "dated_on_or_after_holdout_start"
    kwargs = {"written_at": "t", "writing_actor": "t", "authorization_reference": "t"}
    tampered = _docs(SEAL_V1_DOCS_PATH).replace(b"2020-07-31", b"2020-08-31", 1)
    with pytest.raises(SnapshotRefusal) as refused:
        build_seal_carry_record(tampered, _docs(SEAL_V1_CONFIRMATION_V2_PATH), **kwargs)
    assert refused.value.code == "seal_carry_source_mismatch"
    with pytest.raises(SnapshotRefusal) as refused:
        build_seal_carry_record(_docs(SEAL_V1_DOCS_PATH), _docs(SEAL_V1_CONFIRMATION_V2_PATH),
                                private_prospective_bytes=b"{}", **kwargs)
    assert refused.value.code == "seal_carry_source_mismatch"
    forged = {**record, "holdout_start": "2018-07-31"}
    (harness.snapshot_dir / SEAL_CARRY_FILE).write_bytes(json.dumps(forged).encode())
    with pytest.raises(SnapshotRefusal) as refused:
        read_seal_carry(harness.snapshot_dir)
    assert refused.value.code == "holdout_seal_missing"


def test_t_seal3_2_count_based_window_derivation_on_a_carried_seal_refuses(tmp_path, monkeypatch):
    entries = [entry(f"M{i:03d}", "2011-01-03") for i in range(3)]
    harness = _v2_harness(tmp_path, monkeypatch, {"M000.US": bars2(ALL_ROWS)}, entries=entries)
    snap = harness.snapshot_dir
    carried = (snap / SEAL_CARRY_FILE).read_bytes()
    for call in (lambda: write_prospective_seal(snap, sealed_at="t", sealing_actor="t", authorization_reference="t"),
                 lambda: seal_snapshot(snap, sealing_actor="t", authorization_reference="t"),
                 lambda: run_census(snap, reports_dir=tmp_path / "r", seal_out=tmp_path / "s.json")):
        with pytest.raises(SnapshotRefusal) as refused:
            call()
        assert refused.value.code == "seal_window_recompute_forbidden"
    # Curated counts that would move a count-derived start earlier leave the carried window untouched.
    write_curated(snap / "membership", supplement=[
        {"supplement_id": f"MS-{i}", "action": "absent_member_add", "code": f"Z{i:03d}.US", "start_date": "2011-01-03",
         "source_kind": "sec_filing", "source_locator": "x"} for i in range(5)])
    result = membership_census(Snapshot.open(snap), m4_8_membership.read_curated(snap / "membership"))
    assert result["public"]["absent_members"]["unpriced"] == 5
    assert (snap / SEAL_CARRY_FILE).read_bytes() == carried and not (snap / SEAL_FILE).exists()
    window = read_partition_window(snap)
    assert (window.holdout_start, window.holdout_end) == (HOLDOUT_START, HOLDOUT_END)


def test_partition_window_rule_v2_partitions():
    window = PartitionWindow(PARTITION_RULE_V2, HOLDOUT_START, HOLDOUT_END, "SPY.US_eod_dates_v1", SEAL_CARRY_FILE)
    assert window.partitions == ("discovery_pre", "discovery_post", "holdout")
    assert window.partition(date(2019, 7, 30)) == "discovery_pre"
    assert window.partition(date(2020, 7, 30)) == "holdout"
    assert window.partition(date(2020, 7, 31)) == "discovery_post"


def test_t_part_4_poisoned_holdout_files_leave_stage_a_outputs_byte_identical(tmp_path, monkeypatch):
    harness = snapshot_v2(tmp_path, monkeypatch, "P4", [entry("AAA", "2018-01-02")], {"AAA.US": (
        bars2(ALL_ROWS, volume=lambda r: 1000.0 + r), [split_row(HS_ROW + 20, "2/1")],
        [dividend_row(HS_ROW + 30, 0.5, 0.5)])})
    snap = harness.snapshot_dir
    derived = ("identity/security_master.csv", "identity/interval_results.csv", "membership/constituent_intervals.csv",
               "membership/membership_build_manifest.json", "panel/inventory_discovery.json",
               "identity/distribution_support.parquet")

    def outputs():
        files = {name: (snap / name).read_bytes() for name in derived}
        files.update({p.relative_to(snap).as_posix(): p.read_bytes() for p in sorted((snap / "panel").rglob("*.parquet"))})
        census = membership_census(Snapshot.open(snap), m4_8_membership.read_curated(snap / "membership"))
        files["membership_census"] = json.dumps(census["public"], sort_keys=True).encode()
        # A2-ADV-4: census v3 is outcome-blind to holdout files as well.
        v3 = run_census_v3(snap, terminal_summary={"residual_count": 0}, reports_dir=tmp_path / "reports",
                           segment_access_logs={"pre": ["discovery_pre"], "post": ["discovery_post"]})
        files["census_v3_public"] = (tmp_path / "reports" / "m4_8_coverage_census_v3.json").read_bytes()
        files["census_v3_detail"] = (snap / "census/census_detail_v3.json").read_bytes()
        assert v3["public"]["seal"]["carry_check"]["passed"] is True
        return files

    before = outputs()
    manifest = harness.manifest()
    poisoned = 0
    for record in manifest["entries"].values():
        for role, file_record in record["authorized_files"].items():
            if role == "holdout" or role.startswith("quarantine"):
                (snap / file_record["path"]).write_bytes(b"poison")
                poisoned += 1
    assert poisoned >= 3
    from research.m4_7_universe_build import build_universe

    build_universe(snap, date(2018, 6, 29))
    assert outputs() == before


# ---------------------------------------------------------------- T-RET3-1

M47_ARTIFACT_SHA256 = {
    "docs/preregistrations/m4_7_holdout_seal_v1.json": "b7f9380fa5f128c65966a2984f2a81b635b3f3777f32878270fc977a93bff506",
    "docs/preregistrations/m4_7_holdout_seal_v1_confirmation_v2.json": "8e9e7b0267d689d9bef22ef681aac3b18230373724fe3f0f6cf4e6fa209388ae",
    "docs/preregistrations/m4_7_sp500_pit_rerun_v1.json": "6ea218a638dd2cba760ea22ebd4009bb184d4137233762f72a844454a10f1c9f",
    "docs/preregistrations/m4_7_sp500_pit_rerun_v2.json": "4a6f8b5a0478bd70e90cd84e440a389898630f2e156eb0488c96ca0e8923e7dc",
    "reports/m4_7_coverage_census.json": "608fd1b1dd633e8985ea07537f6a944777cb38d684e86e7c75ada11ddc2d1c40",
    "reports/m4_7_coverage_census.md": "ca242e428ec4601f0b85b771ca5c8868b191af0033a969b10d67d55ff36a64ae",
    "reports/m4_7_coverage_census_v2.json": "8308828f3b8c2e2850bd95da9227cc21d82fee0e99133dbc58e533705039967e",
    "reports/m4_7_coverage_census_v2.md": "af7a3f9b7d02e2e877f63ba6f4fb9a71c10a22ac913099db8984ba800a9f3d59",
    "reports/m4_7_sp500_pit_rerun.md": "2de61b35422ed5c99992da9a58717444ab804b7c0a8f25a7088a7a1e86349ca6",
    "reports/m4_7_sp500_pit_rerun_v2.md": "59b0611d1ae9399874301ffeed7f68c989dce1f5e327c5d1e3c61008e16af2b4",
}


def test_t_ret3_1_committed_m47_registrations_seals_census_and_rerun_reports_keep_their_bytes():
    import hashlib

    for relative, digest in M47_ARTIFACT_SHA256.items():
        assert hashlib.sha256((REPOSITORY_ROOT / relative).read_bytes()).hexdigest() == digest, relative


def test_write_seal_carry_refuses_a_snapshot_that_holds_a_v1_seal(tmp_path):
    from data.holdout_partition import write_seal_carry

    (tmp_path / SEAL_FILE).write_bytes(b"{}")
    with pytest.raises(SnapshotRefusal) as refused:
        write_seal_carry(tmp_path, seal_v1_path=REPOSITORY_ROOT / SEAL_V1_DOCS_PATH,
                         confirmation_v2_path=REPOSITORY_ROOT / SEAL_V1_CONFIRMATION_V2_PATH,
                         written_at="t", writing_actor="t", authorization_reference="t")
    assert refused.value.code == "holdout_seal_ambiguous" and not (tmp_path / SEAL_CARRY_FILE).exists()
