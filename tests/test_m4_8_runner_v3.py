"""M4.8 Stage B runner oracles on synthetic segments (plan 4.1, 4.9, 6, 8.1).

T-REG3-1..6, T-RET3-2, T-GATE3, T-CAUSAL-5, T-SEG-4..7, T-SEAL-BR-2..3, T-EXP-1..2.
The module fixtures run ``run_segments`` twice on the committed synthetic
segments (``tests/m4_8_segment_support.py``): once as built and once with every
post-side value replaced. No test opens a network connection or reads private
data.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import m4_8_segment_support as sup
import research.m4_7_common_support as common_support
import research.m4_7_sp500_pit_rerun as runner
from research.m4_7_coverage_census import power_projection, prior_exposure_overlap


def write_registration(doc: dict, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(doc, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _record(patch: pytest.MonkeyPatch, log: dict) -> None:
    """Record every engine, research-panel, and composite-builder call of the runner."""

    def engine(kind, function):
        def call(prices, signals, **kwargs):
            log["engine"].append({"kind": kind, "index": pd.DatetimeIndex(prices.index),
                                  "start": pd.Timestamp(kwargs["evaluation_start"]),
                                  "end": pd.Timestamp(kwargs["evaluation_end"]),
                                  "policy": kwargs.get("missing_price_policy")})
            return function(prices, signals, **kwargs)
        return call

    def panels(fields):
        result = build(fields)
        log["panels"].append(result)
        return result

    def composites(**kwargs):
        log["composites"].append({"labels_index": pd.DatetimeIndex(kwargs["forward_returns"].index),
                                  "dates": pd.DatetimeIndex(kwargs["monthly_eval_dates"]),
                                  "prices_index": pd.DatetimeIndex(kwargs["prices"].index)})
        return builder(**kwargs)

    def forbidden(*args, **kwargs):
        raise AssertionError("support_exclusions called under registration v3")

    build, builder = runner.build_adjusted_research_panels, runner._build_composites
    patch.setattr(runner, "run_long_short_backtest", engine("long_short", runner.run_long_short_backtest))
    patch.setattr(runner, "run_long_only_backtest", engine("long_only", runner.run_long_only_backtest))
    patch.setattr(runner, "build_adjusted_research_panels", panels)
    patch.setattr(runner, "_build_composites", composites)
    patch.setattr(common_support, "support_exclusions", forbidden)


def _run(base: Path, paths: dict[str, pd.DataFrame] | None) -> dict:
    doc = sup.registration()
    path = base / "registration.json"
    sha = write_registration(doc, path)
    log = {"engine": [], "panels": [], "composites": []}
    with pytest.MonkeyPatch.context() as patch:
        _record(patch, log)
        sidecar = runner.run_segments(sup.runs(paths), registration_path=path, registration_sha256=sha,
                                      output_dir=base / "out", code_commit="fixture")
    trials = [json.loads(line) for line in (base / "out" / runner.TRIALS_V3).read_text().splitlines() if line]
    return {"sidecar": sidecar, "trials": trials, "log": log, "doc": doc, "path": path, "sha": sha,
            "report": (base / "out" / runner.REPORT_V3).read_text()}


@pytest.fixture(scope="module")
def e2e(tmp_path_factory):
    return _run(tmp_path_factory.mktemp("v3_clean"), None)


@pytest.fixture(scope="module")
def poisoned(tmp_path_factory):
    """Every post-side value replaced by another valid path; the pre side is unchanged."""
    paths = sup.vendor_paths()
    other = sup.vendor_paths(seed=99)
    post = slice(sup.ROW_END, None)
    for field in paths:
        paths[field].iloc[post] = other[field].iloc[post].to_numpy()
    return _run(tmp_path_factory.mktemp("v3_poisoned"), paths)


# ---------------------------------------------------------------- end to end


def test_v3_synthetic_run_completes_with_the_registered_segments(e2e):
    sidecar = e2e["sidecar"]
    assert sidecar["run_status"] == "completed" and sidecar["outputs_written"] is True
    assert sidecar["schema_version"] == "m4_8_sp500_pit_rerun_result_v3"
    segments = sidecar["header"]["segments"]
    assert [segments[s]["ic_months"] for s in ("pre", "post")] == [37, 37]
    assert sidecar["header"]["ic_month_supply"] == 74
    assert sidecar["gate"]["outcome"] in runner.PROGRAM_DECISION
    assert all(row["status"] == "evaluated" for row in sidecar["families"]["A"]["rows"].values())
    assert sidecar["labels"]["post"]["missing_execution_bar:halt"] == 1
    assert sidecar["labels"]["post"]["missing_horizon_end_bar:halt"] == 2
    assert sidecar["labels"]["pre"]["terminal_aware_labels"] == 1
    ew = sidecar["benchmarks"]["equal_weight_pit"]["segments"]
    assert ew["pre"]["halt"]["unmarked_halt_row_count"] == 2 and ew["post"]["halt"]["locked_execution_row_count"] >= 1
    assert len(e2e["trials"]) == runner.UNION_SIZE + 6 * 3 * 2 + 63 * 2


def test_t_causal_5_the_v3_runner_never_calls_support_exclusions(e2e):
    assert e2e["sidecar"]["run_status"] == "completed"  # the fixture ran with support_exclusions raising
    assert all(t.get("support_contract") == runner.CAUSAL_SUPPORT_CONTRACT for t in e2e["trials"])


def test_t_seg_4_one_engine_call_per_segment_over_anchor_to_last_book_row(e2e):
    calls = e2e["log"]["engine"]
    book_trials = [t for t in e2e["trials"] if t["hypothesis"] == "book_return"]
    assert len(calls) == 2 * (len(book_trials) + 1)  # every book trial and the equal-weight benchmark
    windows = {(sup.CAL[s.anchor_row], sup.CAL[s.last_book_row]) for s in (sup.PRE, sup.POST)}
    for position, call in enumerate(calls):
        segment = (sup.PRE, sup.POST)[position % 2]
        assert (call["start"], call["end"]) == (sup.CAL[segment.anchor_row], sup.CAL[segment.last_book_row])
        assert call["policy"] == runner.HALT_POLICY and (call["start"], call["end"]) in windows
    for trial in book_trials:
        pre = trial["segments"]["pre"]
        assert pre["first_month"] == sup.CAL[sup.PRE.first_reset_row].strftime("%Y-%m")


def test_t_seg_5_concatenated_series_carry_segment_ids_and_no_return_spans_the_gap(e2e):
    trial = next(t for t in e2e["trials"] if t["factor_id"] == "MOM_12_1" and t["hypothesis"] == "rank_ic_mean")
    by_month = trial["segment_id_by_month"]
    assert list(dict.fromkeys(by_month.values())) == ["pre", "post"]
    assert max(d for d, s in by_month.items() if s == "pre") < min(d for d, s in by_month.items() if s == "post")
    ew = e2e["sidecar"]["benchmarks"]["equal_weight_pit"]
    measured = {s: sup.PRE.last_book_row - sup.PRE.first_reset_row + 1 if s == "pre"
                else sup.POST.last_book_row - sup.POST.first_reset_row + 1 for s in ("pre", "post")}
    assert ew["segment_rows"] == measured and ew["measured_rows"] == sum(measured.values())
    for segment in ("pre", "post"):  # each segment starts in cash at its anchor: its first return earns nothing
        assert ew["segments"][segment]["first_row_net_return"] == 0.0


def test_t_seg_6_one_composite_builder_call_per_segment(e2e):
    calls = e2e["log"]["composites"]
    assert len(calls) == 2
    for call, segment in zip(calls, (sup.PRE, sup.POST)):
        calendar = sup.CAL[segment.feature_floor_row:segment.last_book_row + 1]
        assert call["labels_index"].equals(calendar) and call["prices_index"].equals(calendar)
        assert call["dates"][0] == sup.CAL[segment.first_reset_row - 1] and call["dates"][-1] <= calendar[-1]
    for trial in e2e["trials"]:
        if trial["factor_id"] in runner.FAMILY_B_COMPOSITES and trial["hypothesis"] == "rank_ic_mean":
            months = trial["finite_pair_count_by_month"]
            first_post = sup.CAL[sup.POST.first_reset_row].date().isoformat()
            assert first_post in months  # the post segment's composites restart at its own first reset


def _pre_parts(run: dict) -> dict:
    parts = {"labels": run["sidecar"]["labels"]["pre"]}
    for trial in run["trials"]:
        key = f"{trial['factor_id']}|{trial['hypothesis']}|{trial['book']}|{trial['cost_case']}"
        if trial["hypothesis"] == "rank_ic_mean" and "segment_id_by_month" in trial:  # pooled status spans both
            pre_months = {d for d, s in trial["segment_id_by_month"].items() if s == "pre"}
            parts[key] = ({d: v for d, v in trial["finite_pair_count_by_month"].items() if d in pre_months},
                          trial["descriptive"]["per_segment"]["pre"],
                          {d: v for d, v in trial["coverage_loss"]["by_month"].items() if d in pre_months})
        elif trial["status"] == "evaluated":
            parts[key] = trial["segments"]["pre"]
        else:
            parts[key] = trial["status"]
    parts["ew"] = run["sidecar"]["benchmarks"]["equal_weight_pit"]["segments"]["pre"]
    return parts


def test_t_seg_7_poisoning_one_side_leaves_the_other_segment_byte_identical(e2e, poisoned):
    clean, dirty = _pre_parts(e2e), _pre_parts(poisoned)
    assert json.dumps(clean, sort_keys=True) == json.dumps(dirty, sort_keys=True)
    post_clean = e2e["sidecar"]["benchmarks"]["equal_weight_pit"]["segments"]["post"]
    post_dirty = poisoned["sidecar"]["benchmarks"]["equal_weight_pit"]["segments"]["post"]
    assert post_clean != post_dirty  # the poison reached the post segment


def test_t_seal_br_2_every_panel_stays_on_one_side_and_the_first_post_return_is_missing(e2e):
    start, end = pd.Timestamp(sup.HOLDOUT_START), pd.Timestamp(sup.HOLDOUT_END)
    for result in e2e["log"]["panels"]:
        index = pd.DatetimeIndex(result["returns"].index)
        assert (index < start).all() or (index >= end).all()
        if (index >= end).all():
            assert result["returns"].iloc[0].isna().all()
    for call in e2e["log"]["engine"] + [{"index": c["prices_index"]} for c in e2e["log"]["composites"]]:
        assert (call["index"] < start).all() or (call["index"] >= end).all()


def test_t_seal_br_3_a_segment_input_that_reaches_across_the_seal_refuses():
    registered = {s["segment_id"]: s for s in sup.registration()["discovery"]["segments"]}
    holdout = sup.registration()["holdout"]
    pre, post = sup.runs()
    joined = {k: pd.concat([v, post.fields[k].iloc[:3]]) for k, v in pre.fields.items()}
    bad = runner.SegmentRun(pre.segment, pre.full_calendar, joined, pre.intervals, pre.events, pre.master)
    with pytest.raises(runner.RunnerStop) as stop:
        runner.prepare_segment(bad, registered["pre"], holdout, sup.horizon())
    assert stop.value.reason == "seal_bracket_computation_forbidden"
    sealed = {k: pd.concat([v.iloc[:0], v]) for k, v in post.fields.items()}
    sealed = {k: v.set_axis(v.index.where(v.index != v.index[0], pd.Timestamp("2008-06-06"))) for k, v in sealed.items()}
    bad_post = runner.SegmentRun(post.segment, post.full_calendar, sealed, post.intervals, post.events, post.master)
    with pytest.raises(runner.RunnerStop) as stop:
        runner.prepare_segment(bad_post, registered["post"], holdout, sup.horizon())
    assert stop.value.reason == "seal_bracket_computation_forbidden"


def test_a_registered_segment_row_mismatch_is_a_census_runner_inconsistency():
    doc = sup.registration()
    registered = {s["segment_id"]: s for s in doc["discovery"]["segments"]}
    registered["pre"] = {**registered["pre"], "first_reset": "2004-12-31"}
    with pytest.raises(runner.RunnerStop) as stop:
        runner.prepare_segment(sup.runs()[0], registered["pre"], doc["holdout"], sup.horizon())
    assert stop.value.reason == "census_runner_inconsistency:segment_rows"


def test_an_unevidenced_held_possible_disappearance_stops_before_inference(tmp_path):
    paths = sup.vendor_paths()
    paths["close"].iloc[sup.PRE.first_reset_row + 90:, 5] = np.nan
    paths["adjusted_close"].iloc[sup.PRE.first_reset_row + 90:, 5] = np.nan
    doc = sup.registration()
    sha = write_registration(doc, tmp_path / "registration.json")
    sidecar = runner.run_segments(sup.runs(paths), registration_path=tmp_path / "registration.json",
                                  registration_sha256=sha, output_dir=tmp_path / "out", code_commit="fixture")
    assert sidecar["stop"]["reason"] == "residual_unevidenced_disappearance"
    assert sidecar["outputs_written"] is False and not (tmp_path / "out" / runner.TRIALS_V3).exists()


# ---------------------------------------------------------------- registration v3


def test_t_reg3_3_family_hashes_equal_registration_v2(e2e):
    committed = json.loads(runner.REGISTRATION_PATH.read_bytes())
    assert runner.family_hashes(e2e["doc"]) == runner.family_hashes(committed)
    assert runner.REGISTERED_V3["families"] == runner.REGISTERED["families"]
    for section in ("timing", "books", "benchmarks", "decision_gate"):
        assert runner.REGISTERED_V3[section] == runner.REGISTERED[section], section


def _set(path, value):
    def change(doc):
        node = doc
        for key in path[:-1]:
            node = node[key]
        if value is KeyError:
            del node[path[-1]]
        else:
            node[path[-1]] = value
    return change


@pytest.mark.parametrize("change, reason", [
    (_set(("discovery", "segments"), KeyError), "registration_invalid"),
    (lambda d: d["discovery"]["segments"].pop(), "registration_invalid"),
    (_set(("discovery", "segments", 0, "anchor_row"), KeyError), "registration_invalid"),
    (_set(("discovery", "segments", 1, "anchor_row"), "2008-06-06"), "holdout_overlap_refused"),
    (_set(("discovery", "segments", 1, "anchor_row"), "2017-06-06"), "registration_invalid"),
    (_set(("discovery", "segments", 0, "last_book_row"), "2008-02-29"), "holdout_overlap_refused"),
    (_set(("common_support", "contract"), "asset_level_holding_period_support_exclusion_v1"),
     "support_contract_retired"),
    (lambda d: d["families"]["A"]["factors"][0]["params"].update(lookback_periods=250), "family_hash_mismatch"),
    (_set(("families", "B", "family_size"), 64), "family_size_mismatch"),
    (_set(("engine", "missing_price_policy"), "raise"), "registration_invalid"),
    (_set(("composites", "fitting"), "single_builder_call_v1"), "registration_invalid"),
    (_set(("statistics", "min_ic_months"), 32), "registration_invalid"),
    (_set(("statistics", "hac"), "bartlett_automatic_lag"), "registration_invalid"),
    (_set(("terminal", "claim_contract"), "terminal_claim_v1"), "registration_invalid"),
    (_set(("statistics", "power_projection", "owner_decision_o48_3"), "undecided"), "registration_invalid"),
    (_set(("snapshot", "seal_carry_sha256"), "0" * 63), "registration_invalid"),
    (_set(("holdout", "seal_bracket_computation_forbidden"), False), "registration_invalid"),
    (_set(("costs", "sensitivity_2x", "slippage_bps"), 6.0), "registration_invalid"),
])
def test_t_reg3_1_departures_refuse(change, reason):
    doc = sup.registration()
    assert runner.check_registration(doc) == {k: {kk: float(vv) for kk, vv in v.items()}
                                              for k, v in doc["costs"].items()}
    change(doc)
    with pytest.raises(runner.RunnerStop) as stop:
        runner.check_registration(doc)
    assert stop.value.reason == reason


def test_t_reg3_1_a_stale_bound_hash_refuses(tmp_path):
    doc = sup.registration()
    paths = {}
    for key in runner.SNAPSHOT_DIGESTS_V3:
        path = tmp_path / f"{key}.bin"
        path.write_bytes(key.encode())
        paths[key] = path
    runner.verify_bound_hashes(doc, paths)
    paths["terminal_evidence_sha256"].write_bytes(b"edited after the freeze")
    with pytest.raises(runner.RunnerStop) as stop:
        runner.verify_bound_hashes(doc, paths)
    assert (stop.value.reason, stop.value.detail) == ("derived_artifact_stale", "terminal_evidence")


def test_t_ret3_2_a_registration_other_than_v2_binding_support_v2_refuses():
    v2 = json.loads(runner.REGISTRATION_PATH.read_bytes())
    runner.check_registration(copy.deepcopy(v2))  # registration v2 keeps its contract until the v3 freeze
    for schema in ("m4_8_sp500_pit_rerun_v3", "m4_9_sp500_pit_rerun_v4", "m4_7_sp500_pit_rerun_v1"):
        doc = copy.deepcopy(v2)
        doc["schema_version"] = schema
        with pytest.raises(runner.RunnerStop) as stop:
            runner.check_registration(doc)
        assert stop.value.reason == "support_contract_retired"


def test_t_reg3_2_the_cli_path_refuses_v3_until_per_side_loaders_bind(tmp_path):
    path = tmp_path / "registration.json"
    sha = write_registration(sup.registration(), path)
    sidecar = runner.run_rerun(tmp_path / "missing_snapshot", registration_path=path, registration_sha256=sha,
                               output_dir=tmp_path / "out", code_commit="fixture")
    assert sidecar["stop"]["reason"] == "segment_side_loader_unavailable" and sidecar["outputs_written"] is False


def test_t_reg3_4_minimum_months_route_short_series_to_invalid():
    ic = pd.Series(np.random.default_rng(3).normal(0.01, 0.1, 59),
                   index=pd.date_range("2010-01-31", periods=59, freq="ME"))
    labels = ["pre"] * 29 + ["post"] * 30
    assert runner.ic_minimum_detectable_effect(ic, segments=labels, min_months=runner.MIN_IC_MONTHS_V3) == (None, None)
    assert runner.sign_stability(ic, min_half=runner.MIN_HALF_MONTHS_V3) is None  # halves of 30 and 29
    longer = pd.concat([ic, pd.Series([0.02], index=[pd.Timestamp("2014-12-31")])])
    assert runner.sign_stability(longer, min_half=runner.MIN_HALF_MONTHS_V3) is not None
    assert runner.ic_minimum_detectable_effect(longer, segments=labels + ["post"],
                                               min_months=runner.MIN_IC_MONTHS_V3)[0] is not None


def test_t_reg3_5_power_projection_reproduces_section_5_4():
    projection = power_projection(154)
    band = {row["s"]: row for row in projection["band"]}
    assert band[0.10]["months_for_mde_eff_0_02"] == 356
    assert projection["kill_reachable_projection"] is False
    assert power_projection(356)["kill_reachable_projection"] is True


def test_t_reg3_6_the_report_states_looks_exposure_and_the_unexposed_subsample(e2e):
    report = e2e["report"]
    assert "Sequential looks: 3" in report and "carried seal with stated prior exposures" in report
    assert "## Family A prior-exposure overlap by segment" in report
    assert "reported_descriptive_factor_choices_made_with_knowledge_of_later_data" in report
    assert "## Per-segment Family A IC (descriptive)" in report
    assert "residual_disappearance_minus_100pct_bound_v1` vacuous_no_residual" in report


def test_t_gate3_the_v3_gate_is_the_carried_decide_gate(e2e):
    gate = e2e["sidecar"]["gate"]
    rows = e2e["sidecar"]["families"]["A"]["rows"]
    inputs = [runner.FactorGateInput(f, "evaluated" if r["status"] == "evaluated" else "invalid", bool(r["reject"]),
                                     r["mean_ic"], r["sign_stable"], r["long_short_mean_daily_net_return"], r["mde_f"])
              for f, r in rows.items()]
    expected = runner.decide_gate(inputs, kill_reachable_projection=False)
    assert {k: gate[k] for k in ("outcome", "power_status", "kill_reachable_projection")} == {
        k: expected[k] for k in ("outcome", "power_status", "kill_reachable_projection")}


# ---------------------------------------------------------------- T-EXP


def test_t_exp_1_overlap_reproduces_the_carried_computation():
    windows = runner.prior_exposure_windows()
    assert [kind for kind, _, _ in windows] == ["static_50_name_cohort", "csv_validation", "historical_evaluation"]
    dates = [d.date() for d in pd.date_range("2013-08-31", "2026-07-31", freq="ME")]
    carried = prior_exposure_overlap(dates)
    ours = runner.exposure_overlap(dates, windows)
    for kind in carried:
        assert ours[kind] == carried[kind]["fraction_of_ic_months"]
    valid = pd.DataFrame({"reset_date": pd.date_range("2013-08-30", periods=40, freq="ME"),
                          "horizon_date": pd.date_range("2013-09-30", periods=40, freq="ME"),
                          "segment_id": "pre", "rank_ic": np.linspace(-0.05, 0.1, 40)})
    result = runner.factor_exposure(valid, "MOM_12_1", windows)
    assert result["factor_named_in_prior_exposure"] is True
    assert result["calendar_unexposed_pre_subsample"]["months"] == 35  # horizons before 2016-08-08
    assert result["calendar_unexposed_pre_subsample"]["status"].startswith("reported_descriptive")
    short = runner.factor_exposure(valid.iloc[5:], "LOW_VOL_252", windows)
    assert short["calendar_unexposed_pre_subsample"] == {"months": 30, "horizon_before": "2016-08-08",
                                                         "status": short["calendar_unexposed_pre_subsample"]["status"],
                                                         "mean_ic": pytest.approx(
                                                             float(valid.iloc[5:35]["rank_ic"].mean())),
                                                         "hac_pvalue": short["calendar_unexposed_pre_subsample"][
                                                             "hac_pvalue"]}
    fewer = runner.factor_exposure(valid.iloc[6:], "LOW_VOL_252", windows)
    assert fewer["calendar_unexposed_pre_subsample"]["status"] == "not_reported_below_30_valid_months"


def test_t_exp_2_full_overlap_reports_no_subsample_and_no_statistic_is_fresh(e2e):
    windows = runner.prior_exposure_windows()
    valid = pd.DataFrame({"reset_date": pd.date_range("2016-09-30", periods=40, freq="ME"),
                          "horizon_date": pd.date_range("2016-10-31", periods=40, freq="ME"),
                          "segment_id": "pre", "rank_ic": 0.01})
    result = runner.factor_exposure(valid, "REV_1M", windows)
    assert result["calendar_unexposed_pre_subsample"]["months"] == 0
    assert result["per_segment"]["pre"]["static_50_name_cohort"] == 1.0
    assert "fresh" not in e2e["report"].lower()
    assert date(2016, 8, 8) == min(start for _, start, _ in windows)
