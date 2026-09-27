"""M4.8 Stage B integration oracles on a rule v2 snapshot (integration seams I-1..I-4).

The module fixture retrieves a rule v2 snapshot through Stage A's harness and
runs the whole chain once: terminal template and schema v3 validation with
segments from the build manifest, projection, the v3 support file, the
membership census and census v3, a registration v3 document bound to the
snapshot files, and ``run_rerun`` on it. No test opens a network connection or
reads private data.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pandas as pd
import pytest

import m4_8_integration_support as it
import m4_8_segment_support as sup
import research.m4_7_sp500_pit_rerun as runner
import research.m4_7_terminal_evidence as terminal
from research.m4_7_common_support import SUPPORT_FILE_V3
from research.m4_7_coverage_census import aggregate_terminal_summary
from research.m4_7_universe_build import Snapshot, discovery_segments


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    base = tmp_path_factory.mktemp("integration")
    reads: list[tuple[str, str, str]] = []
    loads: list[str] = []
    with pytest.MonkeyPatch.context() as patch:
        original_read = Snapshot.read_discovery

        def read(self, table, code, side="discovery"):
            reads.append((table, code, side))
            return original_read(self, table, code, side)

        original_load = runner.load_eod_cohort_panels

        def load(directory, symbols, **kwargs):
            mapped = json.loads(Path(kwargs["inventory_path"]).read_text())["files"]
            loads.append(sorted({Path(record["file"]).parts[0] for record in mapped}))
            return original_load(directory, symbols, **kwargs)

        patch.setattr(Snapshot, "read_discovery", read)
        patch.setattr(runner, "load_eod_cohort_panels", load)
        snap = it.retrieve(base, patch)
        reads.clear()
        it.curate_and_validate(snap)
        validation_reads = list(reads)
        support, census = it.census(snap, base / "reports")
        census_json = base / "reports" / "m4_8_coverage_census_v3.json"
        doc = it.registration(snap, census_json, support)
        path = base / "registration.json"
        sha = it.write_registration(doc, path)
        sidecar = runner.run_rerun(snap, registration_path=path, registration_sha256=sha, output_dir=base / "out",
                                   census_json=census_json, code_commit="fixture")
    return {"base": base, "snap": snap, "support": support, "census": census, "census_json": census_json,
            "doc": doc, "sidecar": sidecar, "validation_reads": validation_reads, "loads": loads}


def _rerun(chain, tmp_path, change):
    doc = copy.deepcopy(chain["doc"])
    change(doc)
    path = tmp_path / "registration.json"
    sha = it.write_registration(doc, path)
    return runner.run_rerun(chain["snap"], registration_path=path, registration_sha256=sha, output_dir=tmp_path / "out",
                            census_json=chain["census_json"], code_commit="fixture")


# ---------------------------------------------------------------- I-1 binding and per-side loaders


def test_i1_run_rerun_binds_a_rule_v2_snapshot_and_runs_each_segment_on_its_side(chain):
    sidecar = chain["sidecar"]
    assert sidecar["schema_version"] == "m4_8_sp500_pit_rerun_result_v3" and sidecar["run_status"] == "completed"
    assert sidecar["header"]["segment_access_logs"] == {"pre": ["discovery_pre"], "post": ["discovery_post"]}
    assert chain["loads"] == [["discovery_pre"], ["discovery_post"]]  # the files the verified inventory names
    snapshot = Snapshot.open(chain["snap"])
    calendar = snapshot.calendar()
    build = json.loads((chain["snap"] / "membership/membership_build_manifest.json").read_text())
    segments = discovery_segments(calendar, snapshot.holdout_start, snapshot.holdout_end,
                                  pd.Timestamp(build["d0_pre"]).date())
    for segment in segments:
        header = sidecar["header"]["segments"][segment.segment_id]
        assert header["first_reset"] == calendar[segment.first_reset_row].date().isoformat()
        assert header["last_book_row"] == calendar[segment.last_book_row].date().isoformat()
    assert sidecar["header"]["segments"]["pre"]["last_loaded_date"] < snapshot.holdout_start.isoformat()
    assert sidecar["header"]["segments"]["post"]["first_loaded_date"] >= snapshot.holdout_end.isoformat()
    assert sidecar["header"]["residual"] == {"pre": 0, "post": 0}
    assert (chain["base"] / "out" / runner.TRIALS_V3).is_file()


@pytest.mark.parametrize("change, reason, detail", [
    (lambda d: d["snapshot"].update(seal_carry_sha256="0" * 64), "derived_artifact_stale", "seal_carry"),
    (lambda d: d["snapshot"].update(terminal_evidence_sha256="1" * 64), "derived_artifact_stale", "terminal_evidence"),
    (lambda d: d["snapshot"].update(census_json_sha256="2" * 64), "derived_artifact_stale", "census_json"),
    (lambda d: d["snapshot"].update(discovery_inputs_sha256="3" * 64), "derived_artifact_stale", "discovery_inputs"),
    (lambda d: d["snapshot"].update(snapshot_id="OTHER"), "registration_invalid", "snapshot.snapshot_id"),
    (lambda d: d["holdout"].update(holdout_start="2019-07-30"), "holdout_overlap_refused",
     "registration and seal carry record disagree"),
])
def test_i1_the_v3_binder_refuses_before_any_load(chain, tmp_path, change, reason, detail):
    sidecar = _rerun(chain, tmp_path, change)
    assert (sidecar["stop"]["reason"], sidecar["stop"]["detail"]) == (reason, detail)
    assert sidecar["outputs_written"] is False and not (tmp_path / "out").exists()


def test_i1_a_segment_row_the_snapshot_does_not_produce_is_a_census_runner_inconsistency(chain, tmp_path):
    sidecar = _rerun(chain, tmp_path, lambda d: d["discovery"]["segments"][1].update(first_reset="2021-08-31"))
    assert sidecar["stop"]["reason"] == "census_runner_inconsistency:segment_rows"


# ---------------------------------------------------------------- I-2 terminal scoping on rule v2


def test_i2_rule_v2_validation_derives_segments_and_reads_one_side(chain):
    report = json.loads((chain["snap"] / terminal.VALIDATION).read_text())
    assert report["schema_version"] == "m4_8_terminal_validation_v3"
    row = next(r for r in report["rows"] if r["permanent_id"] == it.CASH_PID)
    assert (row["status"], row["scope"], row["segment_id"]) == ("accepted", "in_scope", "pre")
    code_reads = [(table, side) for table, code, side in chain["validation_reads"] if code == "CSH.US"]
    assert code_reads and {side for _, side in code_reads} == {"discovery_pre"}
    assert all(side in ("discovery_pre", "discovery_post") for _, _, side in chain["validation_reads"])


def test_i2_the_terminal_cli_runs_schema_v3_on_a_rule_v2_snapshot(chain, capsys):
    snap = chain["snap"]
    args = ["--snapshot-id", snap.name.removeprefix("sp500_pit_"), "--data-dir", str(snap.parent)]
    before = (snap / terminal.VALIDATION).read_bytes()
    assert terminal.main(["validate", *args]) == 0
    assert json.loads(capsys.readouterr().out) == {"accepted": 1}
    assert (snap / terminal.VALIDATION).read_bytes() == before
    template = pd.read_csv(snap / terminal.TEMPLATE, dtype=str, keep_default_na=False)
    assert list(template.columns)[:len(terminal.EVIDENCE_COLUMNS_V3)] == list(terminal.EVIDENCE_COLUMNS_V3)


# ---------------------------------------------------------------- I-3 support per segment


def test_i3_rule_v2_support_is_per_segment_and_feeds_census_v3(chain):
    support = chain["support"]
    assert set(support["segments"]) == {"pre", "post"}
    for segment_id, record in support["segments"].items():
        assert record["panel_sides_opened"] == [f"discovery_{segment_id}"] and record["residual_count"] == 0
        assert record["ic_month_supply"] == chain["doc"]["discovery"]["segments"][
            ["pre", "post"].index(segment_id)]["ic_months"]
    assert support["claim"] == {"claim_demand": 0, "claim_contract": "claim_not_built:no_consumer"}
    public = aggregate_terminal_summary(support["terminal_summary"])
    assert public["residual_count"] == 0 and public["accepted"] == 1 and public["by_segment"] == {"pre": 1}
    assert chain["census"]["public"]["terminal_evidence"] == public
    assert chain["census"]["public"]["seal"]["carry_check"]["checks"]["segment_logs_open_own_side_only"] is True
    stored = json.loads((chain["snap"] / SUPPORT_FILE_V3).read_text())
    assert stored["support_sha256"] == support["support_sha256"]


# ---------------------------------------------------------------- I-4 runtime bracket refusal, both directions


@pytest.mark.parametrize("segment_id, borrow", [("pre", "post"), ("post", "pre")])
def test_i4_a_segment_input_with_a_row_from_the_other_side_refuses(segment_id, borrow):
    runs = dict(zip(("pre", "post"), sup.runs()))
    registered = {s["segment_id"]: s for s in sup.registration()["discovery"]["segments"]}
    run, other = runs[segment_id], runs[borrow]
    rows = other.fields["close"].index[:1] if borrow == "post" else other.fields["close"].index[-1:]
    mixed = {k: pd.concat([v, other.fields[k].loc[rows]]).sort_index() for k, v in run.fields.items()}
    bad = runner.SegmentRun(run.segment, run.full_calendar, mixed, run.intervals, run.events, run.master)
    with pytest.raises(runner.RunnerStop) as stop:
        runner.prepare_segment(bad, registered[segment_id], sup.registration()["holdout"], sup.horizon())
    assert stop.value.reason == "seal_bracket_computation_forbidden"


# ---------------------------------------------------------------- M48B-A1-M02: the registered inventory binds the universe


def _copy(chain, tmp_path):
    import shutil

    target = tmp_path / "private" / chain["snap"].name
    shutil.copytree(chain["snap"], target)
    return target


def _rerun_on(chain, snap, tmp_path, monkeypatch):
    loads: list[str] = []
    original = runner.load_eod_cohort_panels
    monkeypatch.setattr(runner, "load_eod_cohort_panels",
                        lambda directory, symbols, **kw: loads.append(str(directory)) or original(directory, symbols, **kw))
    path = tmp_path / "registration.json"
    sha = it.write_registration(chain["doc"], path)
    sidecar = runner.run_rerun(snap, registration_path=path, registration_sha256=sha, output_dir=tmp_path / "out",
                               census_json=chain["census_json"], code_commit="fixture")
    return sidecar, loads


def test_m02_the_registration_binds_the_inventory_and_the_build_manifest(chain):
    snapshot = chain["doc"]["snapshot"]
    assert snapshot["inventory_sha256"] == runner.sha256_bytes((chain["snap"] / "panel/inventory_discovery.json").read_bytes())
    assert snapshot["build_manifest_sha256"] == runner.sha256_bytes(
        (chain["snap"] / "membership/membership_build_manifest.json").read_bytes())
    assert chain["sidecar"]["header"]["segments"]["post"]["member_columns"] == 12  # the restored baseline run


def test_m02_a_removed_inventory_member_refuses_before_any_panel_load(chain, tmp_path, monkeypatch):
    snap = _copy(chain, tmp_path)
    path = snap / "panel/inventory_discovery.json"
    inventory = json.loads(path.read_bytes())
    inventory["files"] = [r for r in inventory["files"]
                          if not (r["symbol"] == "W00.US#E1" and r["side"] == "discovery_post")]
    path.write_text(json.dumps(inventory, sort_keys=True))
    sidecar, loads = _rerun_on(chain, snap, tmp_path, monkeypatch)
    assert (sidecar["stop"]["reason"], sidecar["stop"]["detail"]) == ("derived_artifact_stale", "inventory")
    assert sidecar["outputs_written"] is False and loads == [] and not (tmp_path / "out").exists()


def test_m02_an_edited_build_manifest_refuses_before_any_panel_load(chain, tmp_path, monkeypatch):
    snap = _copy(chain, tmp_path)
    path = snap / "membership/membership_build_manifest.json"
    path.write_bytes(path.read_bytes() + b"\n")
    sidecar, loads = _rerun_on(chain, snap, tmp_path, monkeypatch)
    assert (sidecar["stop"]["reason"], sidecar["stop"]["detail"]) == ("derived_artifact_stale", "build_manifest")
    assert loads == []


# ---------------------------------------------------------------- A2-B-ADV-1: access logs come from the opened paths


def _redirected_inventory(chain):
    """The post-side record of ``W00`` pointed at its pre-side file (with that file's digest)."""
    inventory = json.loads((chain["snap"] / "panel/inventory_discovery.json").read_bytes())
    pre = next(r for r in inventory["files"] if r["symbol"] == "W00.US#E1" and r["side"] == "discovery_pre")
    for record in inventory["files"]:
        if record["symbol"] == "W00.US#E1" and record["side"] == "discovery_post":
            record.update(file=pre["file"], sha256=pre["sha256"])
    return inventory


def test_adv1_the_runner_access_log_reports_a_wrong_side_open_and_the_segment_refuses(chain):
    bound = runner.bind_snapshot_v3(chain["snap"], chain["doc"], chain["census_json"])
    runs, access = runner.load_segment_runs(bound)
    assert access == {"pre": ["discovery_pre"], "post": ["discovery_post"]}
    runs, access = runner.load_segment_runs({**bound, "inventory": _redirected_inventory(chain)})
    assert access["post"] == ["discovery_post", "discovery_pre"]
    registered = {s["segment_id"]: s for s in chain["doc"]["discovery"]["segments"]}
    with pytest.raises(runner.RunnerStop) as stop:
        runner.prepare_segment(runs[1], registered["post"], chain["doc"]["holdout"], chain["doc"]["discovery"][
            "max_reset_to_reset_rows"])
    assert stop.value.reason == "seal_bracket_computation_forbidden"


def test_adv1_the_support_access_log_reports_a_wrong_side_open(chain):
    from research.m4_7_common_support import segment_bars

    snapshot = Snapshot.open(chain["snap"])
    calendar = snapshot.calendar()
    segment = runner.snapshot_segments(snapshot, calendar)[1]
    rows = calendar[segment.feature_floor_row:segment.last_book_row + 1]
    _, opened = segment_bars(chain["snap"], _redirected_inventory(chain), segment.side, ["W00.US#E1"], rows)
    assert opened == ["discovery_pre"]
