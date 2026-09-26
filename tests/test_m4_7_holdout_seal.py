"""Holdout seal derivation from raw membership counts (M4.7 plan 1.4, T-SEAL-1).

Synthetic membership fixtures only; no vendor file or network access.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from data.holdout_partition import (
    MEMBERSHIP_FILE,
    RETRIEVAL_ORDER,
    SEAL_RULE_OPTION_A,
    SEAL_RULES,
    SnapshotRefusal,
    coverage_start,
    derive_holdout_window,
    monthly_raw_counts,
    parse_membership_entries,
    read_holdout_end,
    sha256_bytes,
    write_prospective_seal,
)


RETRIEVED = date(2026, 9, 25)


def entry(code: str | None, start: str | None, end: str | None = None) -> dict:
    return {"Code": code, "Name": f"{code} Inc", "StartDate": start, "EndDate": end, "IsActiveNow": "1", "IsDelisted": "0"}


def gap(codes: range, leave: str, rejoin: str) -> list[dict]:
    """Each code leaves before a month-end and rejoins after it (two raw entries)."""

    return [row for i in codes for row in (entry(f"C{i:03d}", "1989-01-10", leave), entry(f"C{i:03d}", rejoin))]


def membership(*, adjacent: bool = False, deep: bool = False, shift_years: int = 0) -> pd.DataFrame:
    """300 members from 1989, 500 from 1990-01, and isolated 465-member month-ends.

    Codes C000..C034 leave around 1995-03-31 and C035..C069 around 1997-07-31;
    ``adjacent`` adds three consecutive 465-member month-ends (1992-05..07);
    ``deep`` adds one 440-member month-end at 1996-01-31.
    """

    gapped = set(range(70))
    rows = gap(range(0, 35), "1995-03-15", "1995-04-10") + gap(range(35, 70), "1997-07-15", "1997-08-05")
    if adjacent:
        gapped |= set(range(70, 105))
        rows += gap(range(70, 105), "1992-05-10", "1992-08-05")
    if deep:
        gapped |= set(range(105, 165))
        rows += gap(range(105, 165), "1996-01-10", "1996-02-05")
    rows += [entry(f"C{i:03d}", "1989-01-10") for i in range(300) if i not in gapped]
    rows += [entry(f"C{i:03d}", "1990-01-15") for i in range(300, 500)]
    frame = pd.DataFrame(rows)
    if shift_years:
        for column in ("StartDate", "EndDate"):
            frame[column] = [
                f"{int(value[:4]) + shift_years}{value[4:]}" if isinstance(value, str) else None
                for value in frame[column]
            ]
    return frame


def counts_of(frame: pd.DataFrame, retrieved: date = RETRIEVED) -> dict[date, int]:
    entries, _ = parse_membership_entries(frame, retrieved)
    return dict(monthly_raw_counts(entries, retrieved))


def write_snapshot(snapshot_dir: Path, frame: pd.DataFrame, retrieved: date = RETRIEVED) -> str:
    path = snapshot_dir / MEMBERSHIP_FILE
    path.parent.mkdir(parents=True)
    frame.to_parquet(path, index=False)
    payload = path.read_bytes()
    manifest = {
        "snapshot": {"components_retrieved_utc_date": retrieved.isoformat()},
        "files": {"membership": {"path": MEMBERSHIP_FILE, "sha256": sha256_bytes(payload), "bytes": len(payload), "rows": len(frame)}},
        "entries": {},
    }
    (snapshot_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return sha256_bytes(payload)


def test_t_seal_1_raw_counts_and_tolerant_coverage_start() -> None:
    counts = counts_of(membership())
    assert counts[date(1989, 1, 31)] == 300
    assert counts[date(1989, 12, 31)] == 300
    assert counts[date(1990, 1, 31)] == 500
    assert counts[date(1995, 3, 31)] == 465
    assert counts[date(1995, 4, 30)] == 500
    assert counts[date(1997, 7, 31)] == 465
    assert max(counts) == date(2026, 8, 31)

    window = derive_holdout_window(membership(), RETRIEVED)
    assert window["holdout_start"] == "1990-01-31"
    assert window["coverage_start_strict"] == "1997-08-31"
    assert window["holdout_end_exclusive"] == "2000-01-31"


def test_t_seal_1_three_adjacent_exceptions_move_the_tolerant_start_forward() -> None:
    counts = counts_of(membership(adjacent=True))
    assert [counts[date(1992, month, day)] for month, day in ((5, 31), (6, 30), (7, 31))] == [465] * 3
    window = derive_holdout_window(membership(adjacent=True), RETRIEVED)
    assert window["holdout_start"] == "1992-08-31"
    assert window["coverage_start_strict"] == "1997-08-31"
    assert window["holdout_end_exclusive"] == "2002-08-31"


def test_t_seal_1_exception_outside_the_hard_band_is_not_tolerated() -> None:
    counts = counts_of(membership(deep=True))
    assert counts[date(1996, 1, 31)] == 440
    assert derive_holdout_window(membership(deep=True), RETRIEVED)["holdout_start"] == "1996-02-29"


def test_t_seal_1_coverage_start_rule_on_hand_counts() -> None:
    months = [date(2000, month, 28) for month in range(1, 13)]
    series = lambda values: list(zip(months, values))  # noqa: E731
    base = [400, 500, 469, 500, 531, 500, 500, 469, 500, 500, 500, 500]
    assert coverage_start(series(base), 3) == months[1]
    assert coverage_start(series(base), 0) == months[8]
    four = [500, 469, 500, 469, 500, 469, 500, 469, 500, 500, 500, 500]
    assert coverage_start(series(four), 3) == months[2]
    adjacent = [500, 469, 469, 500, 500, 500, 500, 500, 500, 500, 500, 500]
    assert coverage_start(series(adjacent), 3) == months[3]
    assert coverage_start(series([400] * 12), 3) is None
    # m* itself is in band: a tolerated exception never opens the window.
    assert coverage_start(series([460] + [500] * 11), 3) == months[1]


def test_t_seal_1_entry_rule_counts_shared_with_the_build() -> None:
    frame = pd.DataFrame(
        [
            entry("OPEN", "2000-01-03", "2026-09-26"),
            entry("SHUT", "2000-01-03", "2026-09-25"),
            entry("DUP", "2000-01-03", "2001-01-03"),
            entry("DUP", "2000-01-03", "2001-01-03"),
            entry("OVR", "2000-01-03", "2002-01-03"),
            entry("OVR", "2001-06-01", None),
            entry("ADJ", "2000-01-03", "2001-01-03"),
            entry("ADJ", "2001-01-03", None),
            entry(None, "2000-01-03"),
            entry("NOSTART", ""),
            entry("BAD", "2000/01/03"),
            entry("BADEND", "2000-01-03", "20010103"),
            entry("DEG", "2000-01-03", "2000-01-03"),
        ]
    )
    retained, counts = parse_membership_entries(frame, RETRIEVED)
    assert retained == [
        ("OPEN", date(2000, 1, 3), None),
        ("SHUT", date(2000, 1, 3), date(2026, 9, 25)),
        ("DUP", date(2000, 1, 3), date(2001, 1, 3)),
        ("ADJ", date(2000, 1, 3), date(2001, 1, 3)),
        ("ADJ", date(2001, 1, 3), None),
    ]
    assert counts == {
        "raw_entries": 13,
        "entry_missing_field": 2,
        "entry_unparseable_date": 2,
        "degenerate_interval": 1,
        "exact_duplicate_collapsed": 1,
        "raw_overlap": 2,
        "retained": 5,
    }


def test_t_seal_1_prospective_seal_bytes_hash_and_rerun_stability(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    membership_sha = write_snapshot(first, membership())
    write_snapshot(second, membership())
    record, prospective = write_prospective_seal(
        first, sealed_at="2026-09-25T12:00:00Z", sealing_actor="coordinator", authorization_reference="log-1"
    )
    seal_bytes = (first / "holdout_seal_v1.json").read_bytes()
    assert prospective == sha256_bytes(seal_bytes)
    assert json.loads(seal_bytes) == record
    assert record["schema_version"] == "m4_7_holdout_seal_v1"
    assert record["coverage_start_rule"] == "coverage_start_tolerant_3_isolated_v1"
    assert (record["holdout_start"], record["holdout_end_exclusive"]) == ("1990-01-31", "2000-01-31")
    assert record["band"] == [470, 530] and record["tolerance_exceptions"] == 3
    assert record["inputs"] == {"components_raw_sha256": membership_sha, "components_retrieved_utc_date": "2026-09-25"}
    assert record["value_fields_accessed"] == []
    assert record["confirmation"]["status"] == "pending"
    assert record["retrieval_order"] == list(RETRIEVAL_ORDER)
    assert read_holdout_end(first) == date(2000, 1, 31)

    rerun, _ = write_prospective_seal(
        second, sealed_at="2027-09-25T12:00:00Z", sealing_actor="owner", authorization_reference="log-2"
    )
    volatile = {"sealed_at", "sealing_actor", "authorization_reference"}
    assert {k: v for k, v in rerun.items() if k not in volatile} == {k: v for k, v in record.items() if k not in volatile}
    with pytest.raises(SnapshotRefusal) as refused:
        write_prospective_seal(first, sealed_at="x", sealing_actor="x", authorization_reference="x")
    assert refused.value.code == "snapshot_file_exists"


def test_t_seal_1_refusals(tmp_path: Path) -> None:
    with pytest.raises(SnapshotRefusal) as refused:
        derive_holdout_window(membership(shift_years=15), RETRIEVED)
    assert refused.value.code == "holdout_overlaps_prior_exposure"
    with pytest.raises(SnapshotRefusal) as refused:
        read_holdout_end(tmp_path)
    assert refused.value.code == "holdout_seal_missing"

    snapshot = tmp_path / "tampered"
    write_snapshot(snapshot, membership())
    (snapshot / MEMBERSHIP_FILE).write_bytes((snapshot / MEMBERSHIP_FILE).read_bytes() + b"x")
    with pytest.raises(SnapshotRefusal) as refused:
        write_prospective_seal(snapshot, sealed_at="x", sealing_actor="x", authorization_reference="x")
    assert refused.value.code == "artifact_hash_mismatch"
    assert not (snapshot / "holdout_seal_v1.json").exists()


def test_option_a_seal_rule_seals_one_year_without_the_prior_exposure_cap(tmp_path: Path) -> None:
    """Owner decision O-3: the v1 rule refuses a 2019 coverage start; Option A seals one year."""
    late = membership(shift_years=29)
    with pytest.raises(SnapshotRefusal) as refused:
        derive_holdout_window(late, RETRIEVED)
    assert refused.value.code == "holdout_overlaps_prior_exposure"
    window = derive_holdout_window(late, RETRIEVED, SEAL_RULE_OPTION_A)
    assert (window["holdout_start"], window["holdout_end_exclusive"]) == ("2019-01-31", "2020-01-31")

    snapshot = tmp_path / "option_a"
    write_snapshot(snapshot, late)
    record, _ = write_prospective_seal(snapshot, sealed_at="x", sealing_actor="x", authorization_reference="x",
                                       rule_version=SEAL_RULE_OPTION_A, calendar_source="SPY.US_eod_dates_v1")
    assert (record["rule_version"], record["calendar_source"]) == (SEAL_RULE_OPTION_A, "SPY.US_eod_dates_v1")
    assert read_holdout_end(snapshot) == date(2020, 1, 31)
    assert Snapshot.open(snapshot).calendar_source == "SPY.US_eod_dates_v1"
    assert {key: SEAL_RULES[SEAL_RULE_OPTION_A][key] for key in ("holdout_years", "min_in_band_years", "min_ic_months")} == {
        "holdout_years": 1, "min_in_band_years": 7, "min_ic_months": 48}
    assert SEAL_RULES[SEAL_RULE_OPTION_A]["accepted_shortfall"]["min_ic_months"] == 32
    assert SEAL_RULES["earliest_available_decade_from_raw_membership_counts_v1"]["accepted_shortfall"] is None

    default = tmp_path / "default"
    write_snapshot(default, membership())
    record, _ = write_prospective_seal(default, sealed_at="x", sealing_actor="x", authorization_reference="x")
    assert record["calendar_source"] == "GSPC.INDX_eod_dates_v1"
    assert record["rule_version"] == "earliest_available_decade_from_raw_membership_counts_v1"


def test_a_seal_with_an_unknown_rule_version_is_refused(tmp_path: Path) -> None:
    write_snapshot(tmp_path, membership())
    write_prospective_seal(tmp_path, sealed_at="x", sealing_actor="x", authorization_reference="x")
    seal = json.loads((tmp_path / "holdout_seal_v1.json").read_text())
    (tmp_path / "holdout_seal_v1.json").write_text(json.dumps({**seal, "rule_version": "unregistered"}))
    with pytest.raises(SnapshotRefusal) as refused:
        read_holdout_end(tmp_path)
    assert refused.value.code == "holdout_seal_missing"


# ---------------------------------------------------------------- stage a-2: seal script, read recorder, perturbation, hashes


import copy  # noqa: E402

from fixtures.m4_7.e2e_scenario import (  # noqa: E402
    BAND as E2E_BAND,
    HARD_BAND as E2E_HARD_BAND,
    CONSIDERATION,
    build_vendor,
    downstream,
    run_pipeline,
)
from m4_7_snapshot_support import CAL, Harness, record_reads  # noqa: E402
from research.m4_7_holdout_seal import confirmed_seal_bytes, seal_snapshot  # noqa: E402
from research.m4_7_universe_build import Snapshot  # noqa: E402
from data import holdout_partition  # noqa: E402


def e2e_harness(tmp_path: Path, monkeypatch, name: str = "run", **perturb) -> Harness:
    monkeypatch.setattr(holdout_partition, "BAND", E2E_BAND)
    monkeypatch.setattr(holdout_partition, "HARD_BAND", E2E_HARD_BAND)
    base = tmp_path / name
    base.mkdir(parents=True, exist_ok=True)
    return Harness(base, monkeypatch, snapshot_id="E2E", vendor=build_vendor(**perturb))


class YearLater:
    def __init__(self, harness: Harness) -> None:
        self.harness = harness

    def __call__(self):
        return self.harness.clock.value.replace(year=self.harness.clock.value.year + 1)


def test_t_seal_2_seal_script_inputs_order_and_rerun(tmp_path, monkeypatch):
    harness = e2e_harness(tmp_path, monkeypatch)
    assert harness.run("components") == 0 and harness.run("symbols") == 0
    assert harness.run("calendar") == 1
    assert not (harness.snapshot_dir / "calendar").exists()
    record, prospective = seal_snapshot(harness.snapshot_dir, sealing_actor="coordinator",
                                        authorization_reference="log-a2", clock=harness.clock)
    manifest = json.loads((harness.snapshot_dir / "manifest.json").read_bytes())
    assert record["inputs"] == {"components_raw_sha256": manifest["files"]["membership"]["sha256"],
                                "components_retrieved_utc_date": manifest["snapshot"]["components_retrieved_utc_date"]}
    assert prospective == sha256_bytes((harness.snapshot_dir / "holdout_seal_v1.json").read_bytes())
    assert record["confirmation"]["status"] == "pending" and record["retrieval_order"] == list(RETRIEVAL_ORDER)
    assert (record["holdout_start"], record["holdout_end_exclusive"]) == ("1993-12-31", "2003-12-31")
    for later in ("calendar", "dates", "eod", "splits", "dividends", "raw/index/GSPC.INDX.eod.json"):
        assert not (harness.snapshot_dir / later).exists()
    assert record["entry_counts"]["exact_duplicate_collapsed"] == 1 and record["entry_counts"]["raw_overlap"] == 2

    rerun = tmp_path / "rerun" / "private" / "sp500_pit_E2E"
    rerun.mkdir(parents=True)
    for name in ("manifest.json", MEMBERSHIP_FILE):
        (rerun / name).parent.mkdir(parents=True, exist_ok=True)
        (rerun / name).write_bytes((harness.snapshot_dir / name).read_bytes())
    later, _ = seal_snapshot(rerun, sealing_actor="owner", authorization_reference="log-b", clock=YearLater(harness))
    volatile = {"sealed_at", "sealing_actor", "authorization_reference"}
    assert later["sealed_at"][:4] == str(harness.clock.value.year + 1)
    assert {k: v for k, v in later.items() if k not in volatile} == {k: v for k, v in record.items() if k not in volatile}


def test_t_seal_2_closed_and_open_end_dates_and_prior_exposure_refusal(tmp_path, monkeypatch):
    monkeypatch.setattr(holdout_partition, "BAND", (1, 10))
    monkeypatch.setattr(holdout_partition, "HARD_BAND", (1, 10))
    harness = Harness(tmp_path, monkeypatch, snapshot_id="ends")
    retrieved = harness.clock.value.date().isoformat()
    harness.vendor.entries = [
        {"Code": "OPEN", "Name": "Open Inc", "StartDate": "1993-12-15", "EndDate": "2099-12-31", "IsActiveNow": 1, "IsDelisted": 0},
        {"Code": "CLS", "Name": "Cls Inc", "StartDate": "1993-12-15", "EndDate": retrieved, "IsActiveNow": 0, "IsDelisted": 0},
        {"Code": "CLS", "Name": "Cls Inc", "StartDate": "1993-12-15", "EndDate": None, "IsActiveNow": 1, "IsDelisted": 0},
    ]
    assert harness.run("components") == 0 and harness.run("symbols") == 0
    record, _ = seal_snapshot(harness.snapshot_dir, sealing_actor="x", authorization_reference="x", clock=harness.clock)
    assert record["entry_counts"]["raw_overlap"] == 2 and record["entry_counts"]["retained"] == 1

    monkeypatch.setattr(holdout_partition, "BAND", (470, 530))
    monkeypatch.setattr(holdout_partition, "HARD_BAND", (450, 560))
    shifted = tmp_path / "shifted"
    write_snapshot(shifted, membership(shift_years=15))
    with pytest.raises(SnapshotRefusal) as refused:
        seal_snapshot(shifted, sealing_actor="x", authorization_reference="x")
    assert refused.value.code == "holdout_overlaps_prior_exposure"


def test_t_seal_3_read_recorder_across_every_downstream_stage(tmp_path, monkeypatch):
    harness = e2e_harness(tmp_path, monkeypatch)
    assert harness.run("components") == 0 and harness.run("symbols") == 0
    with record_reads(harness.snapshot_dir) as recorder:
        seal_snapshot(harness.snapshot_dir, sealing_actor="coordinator", authorization_reference="log", clock=harness.clock)
    assert set(recorder.paths()) == {"manifest.json", MEMBERSHIP_FILE}
    consideration = tmp_path / "codes.txt"
    consideration.write_text("".join(f"{code}\n" for code in CONSIDERATION))
    assert harness.run("calendar") == 0 and harness.run("splits", "--codes", str(consideration)) == 0
    for _ in range(3):
        assert harness.run("splits") == 0
        harness.clock.advance(days=1)
    assert harness.run("eod") == 0 and harness.run("dividends") == 0
    harness.run("verify")
    with record_reads(harness.snapshot_dir) as recorder:
        result = downstream(harness.snapshot_dir, tmp_path / "out")
    assert recorder.forbidden() == []
    date_reads = [(reader, columns) for reader, path, columns in recorder.reads if path.startswith("dates/")]
    assert date_reads and all(columns == ["date"] for reader, columns in date_reads if reader == "read_parquet")
    assert {reader for reader, _ in date_reads} == {"read_bytes", "read_parquet"}
    checks = {c["permanent_id"]: c for c in result["build"]["episode_checks"]}
    master = pd.read_csv(harness.snapshot_dir / "identity/security_master.csv", dtype=str, keep_default_na=False)
    hend = master[master["vendor_code"] == "HEND.US"].iloc[0]
    assert "split_basis:not_evaluated:no_discovery_bar" in hend["resolution_evidence"]
    assert not (harness.snapshot_dir / "panel/discovery/HEND.US#E1.parquet").exists()
    assert result["build"]["split_rows_after_final_bar"]["not_evaluated_no_discovery_bar"] == 1
    discovery_bars = int((CAL >= pd.Timestamp("2003-12-31")).sum())
    assert checks["CROSS.US#E1"]["pairs"] == discovery_bars - 1


def discovery_projection(base: Path) -> tuple[dict[str, bytes], dict[str, bytes]]:
    """Split every artifact of a run into discovery-scope content and holdout-scoped extras (plan 5.4, S6)."""
    files, holdout = {}, {}
    for path in sorted(p for p in base.rglob("*") if p.is_file()):
        relative = path.relative_to(base).as_posix()
        inner = relative.split("sp500_pit_E2E/", 1)[-1]
        if inner.startswith(("raw/", "eod/holdout/", "splits/holdout/", "dividends/holdout/")) or (
                inner.startswith("quarantine/") and "_holdout/" in inner):
            holdout[relative] = path.read_bytes()
            continue
        payload = path.read_bytes()
        if inner == "manifest.json":
            manifest = json.loads(payload)
            for entry in manifest["entries"].values():
                for role in ("raw", "holdout", "quarantine_holdout"):
                    entry["authorized_files"].pop(role, None)
                entry["partition_statuses"].pop("holdout", None)
            manifest["files"] = {k: v for k, v in manifest["files"].items() if not v["path"].startswith("raw/")}
            manifest["counters"] = {k: v for k, v in manifest["counters"].items() if "holdout" not in k}
            payload = json.dumps(manifest, sort_keys=True).encode()
        elif inner == "retrieval_log.jsonl":
            lines = [json.loads(line) for line in payload.decode().splitlines()]
            payload = json.dumps([r for r in lines if r.get("partition") != "holdout"], sort_keys=True).encode()
        elif relative.endswith("seal/m4_7_holdout_seal_v1.json"):
            record = json.loads(payload)
            record.pop("automated_integrity_checks_over_holdout_rows")
            record["confirmation"].pop("census_json_sha256")
            payload = json.dumps(record, sort_keys=True).encode()
        elif relative.endswith("reports/m4_7_coverage_census.json"):
            record = json.loads(payload)
            record["snapshot_identity"].pop("manifest_sha256")
            quarantined = record["corporate_actions"]["corporate_action_partitions_quarantined"]
            record["corporate_actions"]["corporate_action_partitions_quarantined"] = {
                k: v for k, v in quarantined.items() if "holdout" not in k}
            payload = json.dumps(record, sort_keys=True).encode()
        elif relative.endswith("reports/m4_7_coverage_census.md"):
            payload = "\n".join(line for line in payload.decode().splitlines()
                                if "manifest_sha256" not in line and "_holdout_quarantined" not in line).encode()
        files[relative] = payload
    return files, holdout


def test_t_seal_4_holdout_perturbation_changes_only_holdout_scoped_paths(tmp_path, monkeypatch):
    baseline = run_pipeline(tmp_path / "baseline", monkeypatch)
    perturbed = run_pipeline(tmp_path / "perturbed", monkeypatch, perturb_holdout=True)
    base_files, base_holdout = discovery_projection(tmp_path / "baseline")
    pert_files, pert_holdout = discovery_projection(tmp_path / "perturbed")
    assert base_files.keys() == pert_files.keys()
    differing = [path for path in base_files if base_files[path] != pert_files[path]]
    assert differing == []

    base_manifest = json.loads((baseline["snapshot"] / "manifest.json").read_bytes())
    pert_manifest = json.loads((perturbed["snapshot"] / "manifest.json").read_bytes())
    assert {t: base_manifest["counters"][f"{t}_holdout_quarantined"] for t in ("eod", "splits", "dividends")} == \
        {"eod": 0, "splits": 0, "dividends": 0}
    assert {t: pert_manifest["counters"][f"{t}_holdout_quarantined"] for t in ("eod", "splits", "dividends")} == \
        {"eod": 1, "splits": 1, "dividends": 1}
    for key, entry in base_manifest["entries"].items():
        if "holdout" in entry["authorized_files"] and entry["authorized_files"]["holdout"]["rows"]:
            other = pert_manifest["entries"][key]["authorized_files"]
            assert entry["authorized_files"]["raw"]["sha256"] != other["raw"]["sha256"], key
            assert other.get("holdout", {}).get("sha256") != entry["authorized_files"]["holdout"]["sha256"], key
    split_entry = pert_manifest["entries"]["splits/TWO.US"]
    assert split_entry["status"] == "retrieved" and split_entry["partition_statuses"] == {
        "discovery": "valid", "holdout": "quarantined:invalid_split_ratio"}
    assert pert_manifest["entries"]["eod/TWO.US"]["split_table_sha256_at_eod_validation"] == \
        base_manifest["entries"]["eod/TWO.US"]["split_table_sha256_at_eod_validation"]
    assert pert_manifest["verify"]["split_evidence_stale"] == []
    cross = pd.read_csv(perturbed["snapshot"] / "identity/interval_results.csv", dtype=str, keep_default_na=False)
    assert cross.loc[cross["vendor_code"] == "CROSS.US", "resolution"].tolist() == ["resolved"]
    quarantined = sorted(path.split("/quarantine/")[1].split("/")[0] for path in pert_holdout if "/quarantine/" in path)
    assert quarantined == ["dividends_holdout", "eod_holdout", "splits_holdout"]
    assert not any("/quarantine/" in path for path in base_holdout)

    run_pipeline(tmp_path / "control", monkeypatch, perturb_discovery=True)
    control_files, _ = discovery_projection(tmp_path / "control")
    assert [path for path in base_files if base_files[path] != control_files.get(path)]


def test_t_seal_5_hash_identities_are_acyclic(tmp_path, monkeypatch):
    result = run_pipeline(tmp_path / "hashes", monkeypatch)
    snapshot_seal = (result["snapshot"] / "holdout_seal_v1.json").read_bytes()
    census_path = tmp_path / "hashes" / "reports" / "m4_7_coverage_census.json"
    committed = (tmp_path / "hashes" / "seal" / "m4_7_holdout_seal_v1.json").read_bytes()
    census = json.loads(census_path.read_bytes())
    prospective = sha256_bytes(snapshot_seal)
    assert json.loads(snapshot_seal)["confirmation"]["status"] == "pending"
    assert census["snapshot_identity"]["seal_prospective_sha256"] == prospective == result["census"]["seal_prospective_sha256"]
    assert "seal_confirmed_sha256" not in census_path.read_text()
    confirmation = json.loads(committed)["confirmation"]
    assert confirmation == {"status": "confirmed", "identity_adjusted_min_month_end_count": confirmation["identity_adjusted_min_month_end_count"],
                            "census_json_sha256": sha256_bytes(census_path.read_bytes()), "seal_prospective_sha256": prospective}
    assert sha256_bytes(committed) == result["census"]["seal_confirmed_sha256"]
    assert confirmed_seal_bytes(snapshot_seal, census_json_sha256=confirmation["census_json_sha256"], status="confirmed",
                                identity_adjusted_min_month_end_count=confirmation["identity_adjusted_min_month_end_count"],
                                integrity=copy.deepcopy(json.loads(committed)["automated_integrity_checks_over_holdout_rows"])) == committed
    prospective_fields = {k: v for k, v in json.loads(snapshot_seal).items()
                          if k not in ("confirmation", "automated_integrity_checks_over_holdout_rows")}
    assert {k: v for k, v in json.loads(committed).items() if k in prospective_fields} == prospective_fields
