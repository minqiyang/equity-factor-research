"""M4.7 stage b-1 runner oracles (plan 7.3): T-TERM-7 (runner part), T-SUP-4..7, 9, 10, T-REG-1, 2, 4b, 6, 8..13.

The module fixture runs the committed fixture universe
(``tests/fixtures/m4_7/runner_scenario.py``) through the merged a-1 and a-2
stages and then through the runner once, recording every engine call. The
remaining oracles use small golden fixtures. No test opens a network
connection or reads private data.
"""

from __future__ import annotations

import copy
import json
import math
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import research.m4_7_sp500_pit_rerun as runner
from backtest.portfolio import BacktestValidationError, capture_backtest_source_provenance, run_long_only_backtest
from data.parquet_loader import load_eod_cohort_panels
from fixtures.m4_7 import runner_scenario as scenario
from m4_7_snapshot_support import Harness
from research.m4_7_universe_build import DATA_DIR_ENV
from research.m4_7_common_support import (
    Segment,
    common_support_schedule,
    ic_month_set,
    max_reset_to_reset_rows,
    monthly_rank_ic,
    reset_to_reset_labels,
    scheduled_reset_rows,
    signal_eligibility,
)
from research.m4_7_coverage_census import post_join_warmup_estimate
from research.m4_7_family_a import FAMILY_A, FAMILY_A_IDS, family_a_signals
from research.multifactor_diagnostic_mvp import SECTOR_NEUTRAL_COMPOSITE
from research.multiple_testing_diagnostics import summarize_multiple_testing
from research.real_data_multifactor_diagnostic import build_adjusted_research_panels


PRIMARY = {"transaction_cost_bps": 1.0, "slippage_bps": 4.0}
ZERO = {"transaction_cost_bps": 0.0, "slippage_bps": 0.0}
BENCHMARK = runner.BENCHMARK_ID
TYPED_RETURN_TEST = {"ok", "zero_variance", "insufficient_observations", "nonfinite_observations",
                     "undefined_variance", "undefined_statistic"}


# ---------------------------------------------------------------- module fixture: one full run


def _record_engine_calls(patch: pytest.MonkeyPatch, calls: list[dict]) -> None:
    """Wrap both engines in the runner module; each call's inputs and boundary holdings are recorded."""

    def wrap(kind, engine):
        def call(prices, signals, **kwargs):
            result = engine(prices, signals, **kwargs)
            held = result.net_holdings if kind == "long_short" else result.holdings
            benchmark, events = kwargs.get("benchmark_prices"), kwargs.get("terminal_events")
            calls.append({
                "kind": kind, "price_columns": list(prices.columns), "signal_columns": list(signals.columns),
                "benchmark": None if benchmark is None else benchmark.name,
                "event_ids": [] if events is None else list(events["permanent_id"]),
                "top_pct": kwargs.get("top_pct"), "cost": kwargs.get("transaction_cost_bps"),
                "measured": result.returns.index[1:], "first_held": held.iloc[1], "terminal_held": held.iloc[-1],
            })
            return result
        return call

    patch.setattr(runner, "run_long_short_backtest", wrap("long_short", runner.run_long_short_backtest))
    patch.setattr(runner, "run_long_only_backtest", wrap("long_only", runner.run_long_only_backtest))


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory):
    """The fixture universe retrieved, built, curated, and censused, with its registration."""
    base = tmp_path_factory.mktemp("runner")
    with pytest.MonkeyPatch.context() as patch:
        result = scenario.run_pipeline(base, patch)
        doc = scenario.registration(result)
        path = base / "registration.json"
        sha = scenario.write_registration(doc, path)
        yield {**result, "registration": doc, "registration_path": path, "sha": sha}


@pytest.fixture(scope="module")
def e2e(pipeline):
    """One full rerun of the fixture universe with every engine call recorded."""
    calls: list[dict] = []
    out = pipeline["base"] / "out"
    with pytest.MonkeyPatch.context() as engines:
        _record_engine_calls(engines, calls)
        sidecar = runner.run_rerun(pipeline["snapshot"], registration_path=pipeline["registration_path"],
                                   registration_sha256=pipeline["sha"], output_dir=out,
                                   census_json=pipeline["census_json"], seal_record=pipeline["seal_record"],
                                   code_commit="fixture")
    return {**pipeline, "sidecar": sidecar, "calls": calls, "out": out}


def rerun(e2e, snapshot, out, sha=None, registration_path=None):
    return runner.run_rerun(snapshot, registration_path=registration_path or e2e["registration_path"],
                            registration_sha256=sha or e2e["sha"], output_dir=out, census_json=e2e["census_json"],
                            seal_record=e2e["seal_record"], code_commit="fixture")


def trial_lines(out):
    text = (Path(out) / runner.TRIALS).read_text()
    return [json.loads(line) for line in text.splitlines() if line]


def copy_snapshot(e2e, tmp_path):
    target = tmp_path / "private" / e2e["snapshot"].name
    shutil.copytree(e2e["snapshot"], target)
    return target


def member_ids(snapshot):
    intervals = pd.read_csv(snapshot / "membership/constituent_intervals.csv", dtype=str, keep_default_na=False)
    inventory = json.loads((snapshot / "panel/inventory_discovery.json").read_text())
    return sorted(set(intervals["permanent_id"]) & {r["symbol"] for r in inventory["files"]}), inventory


def books_of(e2e):
    """Engine calls grouped into books: one call per valid segment, in the runner's order."""
    count = e2e["sidecar"]["assumptions"]["segment_count"]
    calls = e2e["calls"]
    return [calls[i:i + count] for i in range(0, len(calls), count)]


# ---------------------------------------------------------------- acceptance (plan 7.3 b-1)


def test_b1_synthetic_end_to_end_rerun_meets_the_acceptance_row(e2e):
    sidecar, validation = e2e["sidecar"], e2e["validation"]
    assert sidecar["run_status"] == "completed" and "stop" not in sidecar
    assert validation["counts"] == {"accepted": 4, "curation_unresolved": 1}
    assert validation["settlement_lag_distribution"] == {"cash": {"0": 1}, "stock": {"-1": 1, "0": 2}}
    kinds = {r["event_kind"] for r in validation["rows"] if r["status"] == "accepted"}
    assert kinds == {"merger_or_acquisition", "rename_or_code_change"}
    master = pd.read_csv(e2e["snapshot"] / "identity/security_master.csv", dtype=str, keep_default_na=False)
    assert {"TICK.US#E1", "TICK.US#E2", "NEWL.US#E1", "PRIOR.US#E1", "JOIN.US#E1", "INDX.US#E1"} <= set(master["permanent_id"])
    window = sidecar["assumptions"]["gap_windows"]
    assert len(window) == 1 and window[0]["reason_types"] == ["missing_bar", "terminal_reset_missing_bar",
                                                              "unresolved_delisting"]
    assert sidecar["header"]["U"] == 1 and sidecar["labels"]["ic_month_supply"] >= runner.MIN_IC_MONTHS
    primary = [r for r in trial_lines(e2e["out"]) if r["family"] == "A" and r["hypothesis"] == "rank_ic_mean"]
    books = [r for r in trial_lines(e2e["out"]) if r["family"] == "A" and r["hypothesis"] == "book_return"]
    assert len(primary) == 6 and {r["status"] for r in primary} == {"evaluated"}
    assert len(books) == 36 and {r["status"] for r in books} == {"evaluated"}
    assert {(r["book"], r["cost_case"]) for r in books} == {(b, c) for b in ("long_short", "long_only")
                                                            for c in runner.COST_CASES}
    for row in sidecar["families"]["A"]["rows"].values():
        assert row["coverage_loss_estimate"] <= row["coverage_loss"]
        assert row["coverage_loss_beyond_estimate"] == row["coverage_loss"] - row["coverage_loss_estimate"]
    assert sidecar["gate"]["outcome"] in runner.PROGRAM_DECISION
    assert len(trial_lines(e2e["out"])) == 69 + 36 + 126
    for family in ("A", "B"):
        for row in sidecar["families"][family]["rows"].values():
            defined = row["status"] == "evaluated" and row["ic_test_status"] == "ok"
            assert (row["union_by_q"] is not None) == defined == (row["by_q"] is not None)
            assert not defined or row["by_q"] <= row["union_by_q"] <= 1.0
    assert set(sidecar["iid_sharpe_haircuts"]) == set(FAMILY_A_IDS) | set(runner.FAMILY_B_IDS)
    labels = json.loads((e2e["snapshot"] / runner.LABEL_RECORDS).read_text())
    assert len(labels) == sidecar["labels"]["ic_month_supply"] and not (e2e["out"] / runner.LABEL_RECORDS).exists()
    assert set(labels[0]) == {"reset_date", "signal_date", "horizon_date", "eligible_count", "terminal_aware_labels",
                              "missing_execution_bar", "missing_horizon_end_bar", "label_exclusion_fraction"}
    assert sum(r["terminal_aware_labels"] for r in labels) == 4 == sidecar["labels"]["terminal_aware_labels"]
    report = (e2e["out"] / runner.REPORT).read_text()
    for heading in ("## Premises", "## Assumptions", "## Segments and gap windows", "## Labels and IC months",
                    "## Family A primary tests", "## Family B primary tests", "## Family A books", "## Benchmarks",
                    "## CPCV and PBO families", "## Excluded event exposure", "## Decision gate"):
        assert heading in report


# ---------------------------------------------------------------- T-REG-1


def test_t_reg_1_registration_matches_the_implemented_protocol(pipeline):
    doc = pipeline["registration"]
    assert runner.check_registration(doc) == runner.REGISTERED["costs"]
    assert runner.FAMILY_SIZES == {"A": 6, "B": 63} and runner.UNION_SIZE == 69
    assert SECTOR_NEUTRAL_COMPOSITE not in runner.FAMILY_B_IDS and len(set(runner.FAMILY_B_IDS)) == 63
    assert doc["families"]["A"]["factors"] == [
        {"id": f.factor_id, "direction": f.direction, "params": dict(f.parameters), "warmup_rows": f.warmup_rows}
        for f in FAMILY_A]
    assert [f["warmup_rows"] for f in doc["families"]["A"]["factors"]] == [252, 251, 21, 252, 252, 63]
    assert doc["timing"]["label_contract"] == "terminal_aware_reset_to_reset_forward_return_v2"
    assert doc["terminal"]["settlement_contract"] == "prior_observed_close_to_consideration_at_completion_date_row_v2"
    assert doc["terminal"]["stock_consideration_lag_rows"] == [-1, 0]
    assert doc["statistics"]["cpcv"]["holding_periods"] == pipeline["census"]["public"]["calendar"]["max_reset_to_reset_rows"]
    assert doc["snapshot"]["retrieval_complete"] is True
    assert isinstance(doc["statistics"]["power_projection"]["kill_reachable_projection"], bool)
    universe = doc["universe"]
    assert universe["corporate_action_attribution"] == (
        "episode_span_attribution_with_split_basis_in_span_step_and_cumulative_drift_checks_v3")
    assert universe["in_span_step_check"]["dividend_factor"] == "one_minus_amount_over_own_basis_reference_price_v3"
    assert universe["in_span_step_check"]["cumulative_drift_tolerance"] == 2e-3
    assert universe["in_span_step_check"]["dividend_factor_formula"] == "prior_close_v1"
    premises = universe["vendor_data_premises"]
    assert {"VP-1", "VP-2"} <= set(premises) and premises["owner_item"] == "O-8"
    assert premises["o8_disposition"] == "ratified" and "b_d" in premises["exposure"] and "s_d" in premises["exposure"]
    for objective in (doc["objective"],):
        assert objective["target_information_ratio"] > 0 and 0 < objective["tracking_error_budget_annualized"] <= 0.25
        assert all(0 < v < 1 for v in objective["max_drawdown_budget"].values())


def _set(path, value):
    def change(doc):
        node = doc
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
    return change


@pytest.mark.parametrize("change, reason", [
    (_set(("families", "A", "family_size"), 5), "family_size_mismatch"),
    (_set(("families", "B", "family_size"), 64), "family_size_mismatch"),
    (lambda d: d["families"]["B"]["composite_ids"].append(SECTOR_NEUTRAL_COMPOSITE), "registration_invalid"),
    (lambda d: d["families"]["A"]["factors"][0]["params"].update(lookback_periods=250), "registration_invalid"),
    (_set(("families", "A", "factors", 1, "warmup_rows"), 252), "registration_invalid"),
    (_set(("timing", "label_contract"), "terminal_aware_reset_to_reset_forward_return_v1"), "registration_invalid"),
    (_set(("terminal", "stock_consideration_lag_rows"), [-1, 0, 1]), "registration_invalid"),
    (_set(("universe", "in_span_step_check", "dividend_factor_formula"), "ex_date_v1"), "registration_invalid"),
    (_set(("universe", "vendor_data_premises", "o8_disposition"), "open"), "registration_invalid"),
    (_set(("statistics", "cpcv", "holding_periods"), 23), "registration_invalid"),
    (_set(("statistics", "power_projection", "kill_reachable_projection"), None), "registration_invalid"),
    (_set(("statistics", "power_projection", "kill_reachable"), True), "registration_invalid"),
    (_set(("statistics", "power_projection", "owner_decision_o3"), "undecided"), "registration_invalid"),
    (_set(("snapshot", "retrieval_complete"), False), "registration_invalid"),
    (_set(("snapshot", "segments_sha256"), "0" * 63), "registration_invalid"),
    (_set(("objective", "tracking_error_budget_annualized"), 0.3), "registration_invalid"),
    (_set(("objective", "target_information_ratio"), 0.0), "registration_invalid"),
    (_set(("objective", "max_drawdown_budget", "long_short"), 1.0), "registration_invalid"),
    (_set(("costs", "sensitivity_2x", "slippage_bps"), 6.0), "registration_invalid"),
    (_set(("costs", "zero_cost_diagnostic_only", "transaction_cost_bps"), 0.5), "registration_invalid"),
    (_set(("common_support", "min_segment_rows"), 21), "registration_invalid"),
])
def test_t_reg_1_departures_from_the_protocol_refuse(pipeline, change, reason):
    doc = copy.deepcopy(pipeline["registration"])
    change(doc)
    with pytest.raises(runner.RunnerStop) as stop:
        runner.check_registration(doc)
    assert stop.value.reason == reason


# ---------------------------------------------------------------- T-REG-2


def test_t_reg_2_hash_is_written_into_report_sidecar_and_every_trial(e2e):
    sha = e2e["sha"]
    assert e2e["sidecar"]["header"]["registration_sha256"] == sha
    assert sha in (e2e["out"] / runner.REPORT).read_text()
    assert json.loads((e2e["out"] / runner.SIDECAR).read_text())["header"]["registration_sha256"] == sha
    lines = trial_lines(e2e["out"])
    assert lines and all(r["registration_sha256"] == sha for r in lines)
    assert all(r["segments_sha256"] == e2e["registration"]["snapshot"]["segments_sha256"] for r in lines)


def test_t_reg_2_hash_mismatch_is_class_one_before_any_trial(pipeline, tmp_path):
    sidecar = rerun(pipeline, pipeline["snapshot"], tmp_path, sha="f" * 64)
    assert sidecar["run_status"] == "stopped_before_inference"
    assert sidecar["stop"]["reason"] == "registration_hash_mismatch" and sidecar["stop"]["trial_records_retained"] == 0
    assert sidecar["header"]["registration_sha256"] == pipeline["sha"]
    assert trial_lines(tmp_path) == [] and pipeline["sha"] in (tmp_path / runner.REPORT).read_text()


def test_cli_exit_codes(pipeline, tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "CENSUS_JSON", pipeline["census_json"])
    args = ["--snapshot-id", "RUN", "--data-dir", str(pipeline["snapshot"].parent), "--registration",
            str(pipeline["registration_path"]), "--output-dir", str(tmp_path), "--census-json", str(pipeline["census_json"]),
            "--seal-record", str(pipeline["seal_record"])]
    assert runner.main([*args, "--registration-sha256", "0" * 64]) == 3
    assert json.loads((tmp_path / runner.SIDECAR).read_text())["stop"]["reason"] == "registration_hash_mismatch"
    monkeypatch.delenv(DATA_DIR_ENV, raising=False)
    assert runner.main(["--snapshot-id", "RUN", "--registration-sha256", "0" * 64]) == 2


# ---------------------------------------------------------------- T-REG-8, 9, 10; T-TERM-7


def test_t_reg_8_cpcv_families_are_aligned_on_mrows(e2e):
    cpcv, sidecar = e2e["sidecar"]["cpcv"], e2e["sidecar"]
    rows = sum(s["measured_rows"] for s in sidecar["books"]["MOM_12_1|long_short|primary"]["segments"])
    horizon = e2e["registration"]["discovery"]["max_reset_to_reset_rows"]
    assert set(cpcv) == {"A_long_short", "A_excess", "B_long_short", "B_excess"}
    for name, family in cpcv.items():
        assert family["status"] in ("available", "unavailable") and family["holding_periods"] == horizon
        assert family["rows"] == rows and family["pbo_columns_missing_failed"] == 0
        assert family["columns_completed"] == (6 if name.startswith("A") else 63)
        assert family["status"] == "available" and 0.0 <= family["pbo"] <= 1.0


def test_t_reg_9_typed_statistics_and_the_header(e2e):
    sidecar_text = (e2e["out"] / runner.SIDECAR).read_text()
    report = (e2e["out"] / runner.REPORT).read_text()
    trials_text = (e2e["out"] / runner.TRIALS).read_text()
    for text in (sidecar_text, trials_text):
        assert '"sharpe":' not in text and "monotonicity_spearman" not in text
    assert "sharpe = 0.0" not in report and "monotonicity_spearman" not in report
    for record in trial_lines(e2e["out"]):
        assert record["status"] in ("evaluated", "failed", "invalid_insufficient_ic_months")
        if record["book"] == "long_short" and record["status"] == "evaluated":
            assert record["return_test"]["status"] in TYPED_RETURN_TEST
            assert (record["return_test"]["status"] == "ok") == (record["return_test"]["hac_pvalue"] is not None)
    family_a = [r for r in trial_lines(e2e["out"]) if r["family"] == "A" and r["book"] == "long_short"]
    assert {r["return_test"]["status"] for r in family_a} == {"ok"}
    header = e2e["sidecar"]["header"]
    for key in ("registration_sha256", "code_commit", "manifest_sha256", "discovery_window",
                "prior_exposure_overlap_fraction", "U", "G", "W", "excluded_fraction",
                "eligible_unpriced_member_day_fraction"):
        assert header[key] is not None
    premises = header["premises"]
    assert set(premises) >= {"VP-1", "VP-2", "a1_volume_half", "in_span_distribution_support_fraction", "b_d", "s_d",
                             "vp2_revisit_required", "o8_disposition", "rounding_statement"}
    assert premises["rounding_statement"] == "rounding refusals at low adjusted levels select on later splits"
    assert "rounding refusals at low adjusted levels select on later splits" in report


def test_t_reg_10_engine_frames_hold_member_permanent_ids_only(e2e):
    members, inventory = member_ids(e2e["snapshot"])
    listed = {r["symbol"] for r in inventory["files"]}
    assert {BENCHMARK, "ACQ.US#E1"} <= listed and not {BENCHMARK, "ACQ.US#E1"} & set(members)
    calls = e2e["calls"]
    assert len(calls) == (1 + 36 + 126) * e2e["sidecar"]["assumptions"]["segment_count"]
    for call in calls:
        assert call["price_columns"] == members and call["signal_columns"] == members
        assert set(call["event_ids"]) <= set(members) and len(call["event_ids"]) == 4
        assert call["benchmark"] in (None, BENCHMARK)
        assert (call["benchmark"] == BENCHMARK) == (call["kind"] == "long_only" and call["top_pct"] == runner.TOP_PCT)
    evaluated = [r for r in trial_lines(e2e["out"]) if r["family"] == "A"]
    assert len(evaluated) == 42 and {r["status"] for r in evaluated} == {"evaluated"}


def test_t_term_7_runner_assumptions_list_the_lag_distribution(e2e):
    assumptions = e2e["sidecar"]["assumptions"]
    assert assumptions["settlement_lag_distribution"] == e2e["validation"]["settlement_lag_distribution"]
    assert assumptions["cash_availability_idealization_rows_max"] == 3
    assert assumptions["consideration_valuation_rule"] == "acquirer_close_at_completion_date_row_v1"


# ---------------------------------------------------------------- T-SUP-4, 5 on the fixture universe


def test_t_sup_4_books_and_benchmark_share_measured_rows_and_exposure_is_typed(e2e):
    books = books_of(e2e)
    rows = [pd.DatetimeIndex(np.concatenate([c["measured"] for c in book])) for book in books]
    assert all(r.equals(rows[0]) for r in rows)
    ew, momentum_ls, momentum_lo = books[0], books[1], books[2]
    assert ew[0]["top_pct"] == 1.0 and momentum_ls[0]["kind"] == "long_short" and momentum_lo[0]["kind"] == "long_only"
    assert not momentum_ls[0]["terminal_held"].equals(momentum_lo[0]["terminal_held"])
    exposure = e2e["sidecar"]["excluded_event_exposure"]
    ew_rows = [e for e in exposure if e["trial"] == "equal_weight_pit"]
    assert {e["reason_type"] for e in ew_rows} == {"missing_bar", "unresolved_delisting"}
    assert all(e["side"] == "long" and e["signed_weight"] > 0 for e in ew_rows)
    assert {e["side"] for e in exposure if e["trial"].endswith("long_short")} <= {"long", "short"}
    assert "permanent_id" not in json.dumps(exposure) and ".US#" not in json.dumps(exposure)


def test_t_sup_4_cpcv_family_omits_failed_columns():
    rows = pd.bdate_range("2020-01-01", periods=300)
    rng = np.random.default_rng(4)
    series = {k: pd.Series(rng.normal(0, 0.01, 300), index=rows) for k in ("a", "b")}
    family = runner.cpcv_family({**series, "c": None}, rows, 5)
    assert family["status"] == "available" and family["pbo_columns_missing_failed"] == 1
    assert family["columns_completed"] == 2
    single = runner.cpcv_family({"a": series["a"], "b": None}, rows, 5)
    assert single["unavailable_reason"] == "pbo_unavailable:insufficient_completed_strategies"
    with pytest.raises(ValueError, match="cpcv_matrix_misaligned"):
        runner.cpcv_family({"a": series["a"], "b": series["b"].iloc[1:]}, rows, 5)
    short = runner.cpcv_family({k: v.iloc[:10] for k, v in series.items()}, rows[:10], 5)
    assert short["unavailable_reason"] == "insufficient_rows_for_split_count"


def test_t_sup_5_every_book_completes_and_a_one_row_gap_member_is_held_around_the_window(e2e):
    trials = trial_lines(e2e["out"])
    assert all(r["status"] == "evaluated" for r in trials if r["family"] == "A")
    assert e2e["sidecar"]["benchmarks"]["equal_weight_pit"]["status"] == "evaluated"
    ew = books_of(e2e)[0]
    assert ew[0]["terminal_held"]["RSTM.US#E1"] > 0 and ew[1]["first_held"]["RSTM.US#E1"] > 0
    assert ew[0]["terminal_held"]["HALT.US#E1"] > 0 and ew[1]["first_held"]["HALT.US#E1"] > 0
    assert ew[0]["terminal_held"]["JOIN.US#E1"] == 0 and ew[1]["first_held"]["JOIN.US#E1"] > 0


# ---------------------------------------------------------------- T-SUP-6, T-SUP-9 stops on the fixture universe


def test_t_sup_6_a_missing_value_the_census_did_not_record_stops_the_run(pipeline, tmp_path, monkeypatch):
    real = runner.load_eod_cohort_panels

    def inject(*args, **kwargs):
        fields = real(*args, **kwargs)
        day = fields["adjusted_close"].index[350]
        for field in ("open", "high", "low", "close", "adjusted_close", "volume"):
            fields[field].loc[day, "N050.US#E1"] = np.nan
        return fields

    monkeypatch.setattr(runner, "load_eod_cohort_panels", inject)
    sidecar = rerun(pipeline, pipeline["snapshot"], tmp_path)
    assert sidecar["run_status"] == "stopped_before_inference"
    assert sidecar["stop"]["reason"] == "census_runner_inconsistency:schedule_digest"
    assert (tmp_path / runner.TRIALS).is_file() and trial_lines(tmp_path) == []
    assert "census_runner_inconsistency:schedule_digest" in (tmp_path / runner.REPORT).read_text()


def test_t_sup_9_class_one_inside_a_segment_stops_and_keeps_written_trials(pipeline, tmp_path, monkeypatch):
    def failing_composites(*args, **kwargs):
        raise ValueError("composite construction unavailable in this oracle")

    def execution_failure(prices, signals, **kwargs):
        raise BacktestValidationError("execution_price_invalid", "injected inside a segment")

    monkeypatch.setattr(runner, "family_b_composites", failing_composites)
    monkeypatch.setattr(runner, "run_long_short_backtest", execution_failure)
    sidecar = rerun(pipeline, pipeline["snapshot"], tmp_path)
    assert sidecar["run_status"] == "stopped_before_inference"
    assert sidecar["stop"]["reason"] == "execution_price_invalid"
    assert sidecar["stop"]["trial"] == "A:MOM_12_1:long_short:primary"
    lines = trial_lines(tmp_path)
    assert len(lines) == 69 == sidecar["stop"]["trial_records_retained"]
    assert {r["hypothesis"] for r in lines} == {"rank_ic_mean"}
    composites = [r for r in lines if r["factor_id"] in runner.FAMILY_B_COMPOSITES]
    assert len(composites) == 11 and {r["status"] for r in composites} == {"failed"}


# ---------------------------------------------------------------- T-REG-12, T-REG-13 on copies of the snapshot


def _spy_on_loads(monkeypatch):
    calls = []
    real = runner.load_eod_cohort_panels
    monkeypatch.setattr(runner, "load_eod_cohort_panels", lambda *a, **k: calls.append(a) or real(*a, **k))
    return calls


def test_t_reg_12_a_panel_split_table_refuses_before_loading(pipeline, tmp_path, monkeypatch):
    snapshot = copy_snapshot(pipeline, tmp_path)
    pid = "N001.US#E1"
    (snapshot / "panel/splits").mkdir(parents=True)
    pd.DataFrame({"date": [pd.Timestamp("2010-06-04")], "split": ["2/1"]}).to_parquet(
        snapshot / "panel/splits" / f"{pid}.parquet")
    loads = _spy_on_loads(monkeypatch)
    sidecar = rerun(pipeline, snapshot, tmp_path / "out")
    assert sidecar["stop"]["reason"] == "panel_split_table_present" and sidecar["stop"]["detail"] == pid
    assert loads == [] and trial_lines(tmp_path / "out") == []
    inventory = json.loads((pipeline["snapshot"] / "panel/inventory_discovery.json").read_text())
    record = next(r for r in inventory["files"] if r["symbol"] == pid)
    panels = load_eod_cohort_panels(pipeline["snapshot"] / "panel", [pid],
                                    inventory_path=pipeline["snapshot"] / "panel/inventory_discovery.json")
    written = pd.read_parquet(pipeline["snapshot"] / "panel" / record["file"])
    assert np.array_equal(panels["split_factor"][pid].to_numpy(), written["split_factor"].to_numpy())


def test_t_reg_13_stale_inputs_refuse_and_the_rebuilt_state_loads(pipeline, tmp_path, monkeypatch):
    snapshot = copy_snapshot(pipeline, tmp_path)
    harness = Harness(tmp_path, monkeypatch, snapshot_id="RUN", vendor=scenario.build_vendor())
    assert harness.snapshot_dir == snapshot
    harness.clock.advance(days=30)
    body = json.loads(harness.vendor.routes["eod/N001.US"])
    body[400] = {**body[400], **{f: body[400][f] * 1.001 for f in ("open", "high", "low", "close", "adjusted_close")}}
    harness.vendor.routes["eod/N001.US"] = json.dumps(body).encode("utf-8")
    codes = tmp_path / "refresh.txt"
    codes.write_text("N001.US\n")
    assert harness.run("eod", "--codes", str(codes), "--refresh") == 0
    loads = _spy_on_loads(monkeypatch)
    sidecar = rerun(pipeline, snapshot, tmp_path / "stale")
    assert sidecar["stop"]["reason"] == "derived_artifact_stale" and loads == []
    assert trial_lines(tmp_path / "stale") == []

    altered = tmp_path / "altered"
    target = altered / "private" / pipeline["snapshot"].name
    shutil.copytree(pipeline["snapshot"], target)
    inventory = json.loads((target / "panel/inventory_discovery.json").read_text())
    record = next(r for r in inventory["files"] if r["symbol"] == "N002.US#E1")
    frame = pd.read_parquet(target / "panel" / record["file"])
    frame.loc[5, "volume"] = frame.loc[5, "volume"] + 1.0
    frame.to_parquet(target / "panel" / record["file"], index=False)
    sidecar = rerun(pipeline, target, altered / "out")
    assert sidecar["stop"] == {"reason": "derived_artifact_stale", "detail": "panel N002.US#E1", "trial": None,
                               "trial_records_retained": 0}
    assert loads == []

    rebuilt = scenario.downstream(snapshot, tmp_path / "rebuilt")
    doc = scenario.registration({"census": rebuilt["census"], "snapshot": snapshot,
                                 "seal_record": rebuilt["seal_record"]})
    assert doc["snapshot"]["manifest_sha256"] != pipeline["registration"]["snapshot"]["manifest_sha256"]
    bound = runner.bind_snapshot(snapshot, doc, rebuilt["census_json"], rebuilt["seal_record"])
    loaded = runner.load_member_panels(bound)
    support = runner.recompute_support(bound, loaded, doc)
    assert support.segments_sha256 == doc["snapshot"]["segments_sha256"] and len(loads) == 1


# ---------------------------------------------------------------- small golden fixtures


SMALL = pd.bdate_range("2020-01-01", periods=520, name="date")


def intervals(dates, starts, ends=None):
    ends = ends or {}
    return pd.DataFrame({
        "symbol": list(starts), "permanent_id": list(starts),
        "start_date": [dates[starts[a]] for a in starts], "start_known_at": [dates[starts[a]] for a in starts],
        "end_date": [dates[ends[a]] if a in ends else pd.NaT for a in starts],
        "end_known_at": [dates[ends[a]] if a in ends else pd.NaT for a in starts],
    })


def cash_event(dates, asset, settle, known, value):
    return pd.DataFrame([{"event_id": f"e-{asset}", "permanent_id": asset, "effective_date": dates[settle],
                          "known_at": dates[known], "reference_date": dates[settle - 1], "terminal_return": value,
                          "return_basis": "prior_observed_close_to_cash"}])


def walks(dates, assets, seed):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(50.0 * np.exp(np.cumsum(rng.normal(0.0003, 0.012, (len(dates), len(assets))), axis=0)),
                        index=dates, columns=assets)


def _mask(table, dates, assets, events=None):
    from backtest.portfolio import resolve_pit_universe_mask
    return resolve_pit_universe_mask(table, events, dates, assets)


def test_t_sup_7_two_segment_hand_oracle():
    R = scheduled_reset_rows(SMALL)
    d0 = int(R[R >= 253][0])
    gap = int(R[R > d0 + 120][0]) + 8
    assets = [f"A{i:02d}" for i in range(20)]
    prices = walks(SMALL, assets, 7)
    prices.iloc[gap, 0] = np.nan
    table = intervals(SMALL, {a: 0 for a in assets})
    mask = _mask(table, SMALL, assets)
    bars = prices.notna()
    schedule = common_support_schedule(SMALL, bars, mask, {}, d0)
    valid = [s for s in schedule.segments if s.valid]
    assert len(valid) == 2 and len(schedule.windows) == 1
    window = schedule.windows[0]
    assert schedule.excluded_rows == window.end - window.start + 1
    s_mask = signal_eligibility(mask, bars)
    signal = pd.DataFrame(np.random.default_rng(8).normal(size=prices.shape), index=SMALL, columns=assets).where(s_mask)
    for book in ("long_only", "long_short"):
        results = runner.run_segmented_book(book, prices, signal, SMALL, valid, intervals=table, events=pd.DataFrame(),
                                            cost=PRIMARY, top_pct=0.25)
        stats, net = runner.book_statistics(results, book)
        assert len(net) == sum(s.rows for s in valid) and net.index.equals(SMALL[np.r_[valid[0].first:valid[0].last + 1,
                                                                                       valid[1].first:valid[1].last + 1]])
        for result, segment, record in zip(results, valid, stats["segments"]):
            assert result.equity_curve.index[0] == SMALL[segment.anchor] and result.equity_curve.iloc[0] == 1.0
            assert result.returns.iloc[0] == 0.0 and result.total_trading_costs.iloc[0] == 0.0
            assert record["first_row_net_return"] == pytest.approx(-result.total_trading_costs.iloc[1], abs=1e-15)
            assert record["terminal_open_positions"] > 0 and record["terminal_row_trading_cost"] > 0
            assert result.returns.iloc[-1] == pytest.approx(
                result.gross_returns.iloc[-1] - result.total_trading_costs.iloc[-1], abs=1e-15)
        assert stats["pooled_trading_costs"] == pytest.approx(sum(r["trading_costs"] for r in stats["segments"]))
        assert stats["hac_boundary_adjacency_pairs"] == stats["return_test"]["hac_lags"]


def test_t_sup_9_book_failures_are_trial_level_or_class_one(monkeypatch):
    assets = [f"A{i:02d}" for i in range(20)]
    prices = walks(SMALL, assets, 9)
    table = intervals(SMALL, {a: 0 for a in assets})
    s_mask = signal_eligibility(_mask(table, SMALL, assets), prices.notna())
    signal = prices.pct_change(21).where(s_mask)
    segment = [Segment(300, 400, True)]
    spy = prices.mean(axis=1).rename(BENCHMARK)
    kwargs = dict(cost=PRIMARY, intervals=table, events=pd.DataFrame(), spy=spy,
                  spy_daily=spy.pct_change().iloc[300:401], equal_weight=None,
                  objective=runner.REGISTERED["objective"])

    def exposure_failure(*args, **kw):
        raise BacktestValidationError("target_exposure_invalid", "injected")

    monkeypatch.setattr(runner, "run_long_short_backtest", exposure_failure)
    fields, net, results = runner.book_trial("long_short", prices, signal, SMALL, segment, **kwargs)
    assert fields["status"] == "failed" and fields["error_type"] == "BacktestValidationError" and net is None
    assert fields["error"].startswith("target_exposure_invalid")
    fields_lo, net_lo, _ = runner.book_trial("long_only", prices, signal, SMALL, segment, **kwargs)
    assert fields_lo["status"] == "evaluated" and fields_lo["excess_vs_equal_weight"] == {"status": "benchmark_failed"}
    records = [{"trial_id": "failed", "family": "A", "status": "failed", "specification": {"factor_id": "F0"}},
               *({"trial_id": f"ok{i}", "family": "A", "status": "completed", "specification": {"factor_id": f"F{i}"},
                  "return_test": {**fields_lo["return_test"]}} for i in range(1, 6))]
    summary = summarize_multiple_testing(records, family_sizes={"A": 6})
    failed = next(row for row in summary["rows"] if row["trial_id"] == "failed")
    assert failed["adjusted_pvalues"]["hac"]["by"] is None and failed["rejections"]["hac"]["by"] is False

    def execution_failure(*args, **kw):
        raise BacktestValidationError("execution_price_invalid", "injected")

    monkeypatch.setattr(runner, "run_long_short_backtest", execution_failure)
    with pytest.raises(runner.RunnerStop) as stop:
        runner.book_trial("long_short", prices, signal, SMALL, segment, **kwargs)
    assert stop.value.reason == "execution_price_invalid"


def test_t_sup_9_a_label_bar_missing_past_the_census_is_class_one():
    assets = [f"A{i:02d}" for i in range(5)]
    prices = walks(SMALL, assets, 10)
    table = intervals(SMALL, {a: 0 for a in assets})
    mask = _mask(table, SMALL, assets)
    schedule = common_support_schedule(SMALL, prices.notna(), mask, {}, int(scheduled_reset_rows(SMALL)[12]))
    resets, _ = ic_month_set(schedule)
    s_mask = signal_eligibility(mask, prices.notna())
    labels, records = runner.ic_labels(prices, s_mask, schedule, resets, pd.DataFrame())
    assert (records["label_exclusion_fraction"] == 0.0).all()
    for row_of in (lambda r: r, lambda r: int(schedule.reset_rows[schedule.reset_rows > r][0])):
        broken = prices.copy()
        broken.iloc[row_of(resets[3]), 2] = np.nan
        with pytest.raises(runner.RunnerStop) as stop:
            runner.ic_labels(broken, s_mask, schedule, resets, pd.DataFrame())
        assert stop.value.reason == "census_runner_inconsistency:label_bar_missing"


def test_t_sup_10_ic_rows_and_book_holdings_align():
    dates = SMALL
    R = scheduled_reset_rows(dates)
    d0 = int(R[R >= 253][0])
    r_join = int(R[R > d0 + 60][0])
    assets = [f"A{i:02d}" for i in range(10)] + ["JOIN", "GAPM"]
    prices = walks(dates, assets, 11)
    prices.iloc[r_join - 1, assets.index("GAPM")] = np.nan
    starts = {a: 0 for a in assets} | {"JOIN": r_join - 3}
    table = intervals(dates, starts)
    mask = _mask(table, dates, assets)
    bars = prices.notna()
    schedule = common_support_schedule(dates, bars, mask, {}, d0)
    valid = [s for s in schedule.segments if s.valid]
    resets, _ = ic_month_set(schedule)
    assert r_join in resets and not mask.iloc[r_join - 3]["JOIN"] and mask.iloc[r_join - 2]["JOIN"]
    s_mask = signal_eligibility(mask, bars)
    assert s_mask.iloc[r_join - 1]["JOIN"] and not s_mask.iloc[r_join - 1]["GAPM"]
    rng = np.random.default_rng(12)
    raw = pd.DataFrame(rng.normal(size=prices.shape), index=dates, columns=assets)
    for r in resets:
        raw.iloc[r] = -raw.iloc[r - 1]
    signal = raw.where(s_mask)
    labels, _ = reset_to_reset_labels(prices, s_mask, schedule.reset_rows, resets, None)

    def run(book, sig, **extra):
        results = runner.run_segmented_book(book, prices, sig, dates, valid, intervals=table, events=pd.DataFrame(),
                                            cost=ZERO, **extra)
        held = pd.concat([(r.net_holdings if book == "long_short" else r.holdings) for r in results])
        return results, held

    _, ew = run("long_only", runner.equal_weight_signal(s_mask), top_pct=1.0)
    _, top = run("long_only", signal)
    _, spread = run("long_short", signal)
    ic = monthly_rank_ic(signal, labels, resets, min_pairs=3)
    for r in resets:
        t, day = r - 1, dates[r]
        eligible = set(s_mask.columns[s_mask.iloc[t].to_numpy()])
        scores = signal.iloc[t].dropna()
        assert set(ew.columns[ew.loc[day] > 0]) == eligible and set(scores.index) == eligible
        assert set(top.columns[top.loc[day] > 0]) == set(scores.nlargest(math.ceil(0.1 * len(scores))).index)
        longs, shorts = set(spread.columns[spread.loc[day] > 0]), set(spread.columns[spread.loc[day] < 0])
        unselected = scores.drop(list(longs | shorts))
        assert longs and shorts and (longs | shorts) <= eligible
        assert scores[list(longs)].min() > unselected.max() and scores[list(shorts)].max() < unselected.min()
    for segment in valid:
        start, end = dates[segment.anchor], dates[segment.last]
        single = run_long_only_backtest(prices, signal, source_provenance=capture_backtest_source_provenance(prices, signal),
                                        evaluation_start=start, evaluation_end=end, top_n=1, constituent_intervals=table)
        resolved = pd.DatetimeIndex(single.timing_metadata["resolved_rebalance_dates"])
        for r in [r for r in resets if segment.first <= r <= segment.last]:
            chosen = signal.iloc[r - 1].idxmax()
            increment = prices.iloc[r + 1][chosen] / prices.iloc[r][chosen] - 1.0
            assert single.gross_returns.loc[dates[r + 1]] == pytest.approx(increment, abs=1e-14)
            h = int(schedule.reset_rows[schedule.reset_rows > r][0])
            assert resolved[resolved > dates[r]][0] == dates[h]
    moved = raw.copy()
    moved.iloc[list(resets)] = rng.normal(size=(len(resets), len(assets)))
    _, top_moved = run("long_only", moved.where(s_mask))
    ic_moved = monthly_rank_ic(moved.where(s_mask), labels, resets, min_pairs=3)
    pd.testing.assert_series_equal(ic_moved["rank_ic"], ic["rank_ic"])
    assert top_moved.loc[dates[list(resets)]].equals(top.loc[dates[list(resets)]])
    r = resets[4]
    flipped = raw.copy()
    flipped.iloc[r - 1] = -raw.iloc[r - 1]
    _, top_flipped = run("long_only", flipped.where(s_mask))
    ic_flipped = monthly_rank_ic(flipped.where(s_mask), labels, resets, min_pairs=3)
    assert ic_flipped["rank_ic"].iloc[4] == pytest.approx(-ic["rank_ic"].iloc[4])
    assert not top_flipped.loc[dates[r]].equals(top.loc[dates[r]])


def test_t_reg_6_equal_weight_pit_benchmark_hand_oracle():
    dates = pd.bdate_range("2021-01-01", periods=140, name="date")
    R = scheduled_reset_rows(dates)
    p, q = int(R[0]), len(dates) - 1
    assets = ["ENT", "EXT", "SET"]
    rng = np.random.default_rng(13)
    prices = pd.DataFrame(40.0 * np.exp(np.cumsum(rng.normal(0, 0.01, (len(dates), 3)), axis=0)),
                          index=dates, columns=assets)
    r_settle, r_entry_first = int(R[3]), int(R[1])
    prices.iloc[r_settle:, 2] = np.nan
    prices.iloc[r_entry_first - 1, 0] = np.nan
    table = intervals(dates, {"ENT": r_entry_first - 5, "EXT": 0, "SET": 0}, {"EXT": int(R[2]) + 3})
    events = cash_event(dates, "SET", r_settle, r_settle - 10, -0.2)
    mask = _mask(table, dates, assets, events)
    s_mask = signal_eligibility(mask, prices.notna())
    [result] = runner.run_segmented_book("long_only", prices, runner.equal_weight_signal(s_mask), dates,
                                         [Segment(p, q, True)], intervals=table, events=events, cost=ZERO, top_pct=1.0)
    resets = [int(r) for r in R if p <= r <= q] + ([q] if q not in R else [])
    for r in resets:
        support = set(result.holdings.columns[result.holdings.loc[dates[r]] > 0])
        assert support == set(s_mask.columns[s_mask.iloc[r - 1].to_numpy()])
    assert not s_mask.iloc[r_settle - 1]["SET"] and not s_mask.iloc[r_entry_first - 1]["ENT"]
    assert s_mask.iloc[int(R[2]) - 1]["ENT"] and not s_mask.iloc[int(R[3]) - 1]["EXT"]
    value, sleeves, equity = 1.0, {}, [1.0]
    for row in range(p, q + 1):
        if row > p:
            for asset in list(sleeves):
                if asset == "SET" and row == r_settle:
                    sleeves[asset] = ("cash", sleeves[asset][1] * 0.8)
                elif sleeves[asset][0] == "held":
                    sleeves[asset] = ("held", sleeves[asset][1] * prices.iloc[row][asset] / prices.iloc[row - 1][asset])
            value = sum(v for _, v in sleeves.values())
        equity.append(value)
        if row in resets:
            chosen = [a for a in assets if s_mask.iloc[row - 1][a]]
            sleeves = {a: ("held", value / len(chosen)) for a in chosen}
    np.testing.assert_allclose(result.equity_curve.to_numpy(), np.array(equity), rtol=0, atol=1e-12)
    assert result.equity_curve.index[0] == dates[p - 1]


def test_t_reg_4b_family_b_masking_and_composite_inputs(monkeypatch):
    dates = pd.bdate_range("2021-01-01", periods=320, name="date")
    assets = [f"B{i:02d}" for i in range(30)]
    close = walks(dates, assets, 14)
    join = 200
    table = intervals(dates, {a: 0 for a in assets} | {"B29": join})
    mask = _mask(table, dates, assets)
    s_mask = signal_eligibility(mask, close.notna())

    def research(frame):
        fields = {"open": frame, "high": frame * 1.01, "low": frame * 0.99, "close": frame, "adjusted_close": frame,
                  "volume": frame * 0 + 1e6, "split_factor": frame * 0 + 1.0}
        return build_adjusted_research_panels(fields)

    baseline = runner.family_b_alphas(research(close), s_mask)
    perturbed_close = close.copy()
    perturbed_close.iloc[:join, -1] *= np.linspace(0.5, 2.0, join)
    perturbed = runner.family_b_alphas(research(perturbed_close), s_mask)
    before = slice(0, join)
    for alpha_id, frame in baseline.items():
        assert not isinstance(frame, Exception), alpha_id
        assert np.array_equal(frame.iloc[before, :-1].to_numpy(), perturbed[alpha_id].iloc[before, :-1].to_numpy(),
                              equal_nan=True), alpha_id
        assert frame.iloc[before, -1].isna().all() and perturbed[alpha_id].iloc[before, -1].isna().all()
    R = scheduled_reset_rows(dates)
    d0 = int(R[3])
    resets = tuple(int(r) for r in R if d0 <= r < R[-1])
    horizon = max_reset_to_reset_rows(R, d0, int(R[-1]))
    labels, _ = reset_to_reset_labels(close, s_mask, R, resets, None)
    rebalances = dates[[int(r) - 1 for r in R if r >= d0]]
    seen = {}

    def capture(**kwargs):
        seen.update(kwargs)
        return {c: pd.DataFrame(1.0, index=dates, columns=assets) for c in kwargs["composite_ids"]}, {}

    monkeypatch.setattr(runner, "_build_composites", capture)
    composites = runner.family_b_composites(research(close), s_mask, baseline, labels, resets, rebalances, horizon)
    assert seen["forward_returns"] is labels and seen["config"].forward_holding_periods == horizon
    assert seen["config"].signal_lag_periods == 1 and seen["monthly_eval_dates"].equals(rebalances)
    labelled = labels.index[labels.notna().any(axis=1)]
    assert set(labelled) <= set(dates[[r - 1 for r in resets]])
    assert seen["ic_history"].index.equals(dates[[r - 1 for r in resets]])
    assert tuple(seen["composite_ids"]) == runner.FAMILY_B_COMPOSITES
    assert all(c.where(~s_mask).isna().all().all() for c in composites.values())


def test_t_reg_11_coverage_loss_and_the_census_warmup_bound():
    dates = pd.bdate_range("2019-01-18", periods=600, name="date")
    R = scheduled_reset_rows(dates)
    assert 550 in set(R.tolist())
    resets = tuple(int(r) for r in R[:-1])
    growth = pd.Series(100.0 * np.exp(0.001 * np.arange(600)), index=dates)
    prices = pd.DataFrame({"FULL": growth, "NEW": growth, "GAP": growth})
    prices.iloc[:300, 1] = np.nan
    prices.iloc[400, 2] = np.nan
    table = intervals(dates, {"FULL": 300, "NEW": 300, "GAP": 0})
    mask = _mask(table, dates, list(prices.columns))
    bars = prices.notna()
    s_mask = signal_eligibility(mask, bars)
    assert s_mask.iloc[300]["FULL"] and not s_mask.iloc[299]["FULL"] and not s_mask.iloc[400]["GAP"]
    market = pd.Series(100.0 * np.exp(0.001 * np.arange(600) + 0.01 * np.sin(np.arange(600) / 7.0)), index=dates)
    signals = family_a_signals(prices, market, prices * 1000.0, s_mask)
    assert signals["MOM_12_1"].iloc[300]["FULL"] == pytest.approx(0.2598592394492314, abs=1e-12)
    assert signals["REV_1M"].iloc[300]["FULL"] == pytest.approx(-0.02122205163752855, abs=1e-12)
    estimate = {asset: post_join_warmup_estimate(s_mask[[asset]], bars[[asset]], resets) for asset in prices.columns}
    for factor in FAMILY_A:
        loss = {asset: runner.coverage_loss(signals[factor.factor_id][[asset]], s_mask[[asset]], resets)["total"]
                for asset in prices.columns}
        assert loss["FULL"] == 0 and estimate["FULL"][factor.factor_id] == 0
        expected_new = sum(1 for r in resets if 300 <= r - 1 < 300 + factor.warmup_rows)
        assert loss["NEW"] == expected_new == estimate["NEW"][factor.factor_id]
        assert estimate["GAP"][factor.factor_id] <= loss["GAP"]
    gap_loss = runner.coverage_loss(signals["LOW_VOL_252"][["GAP"]], s_mask[["GAP"]], resets)["total"]
    assert gap_loss - estimate["GAP"]["LOW_VOL_252"] == sum(1 for r in resets if 401 <= r - 1 <= 652) > 0
    research = build_adjusted_research_panels({
        "open": prices, "high": prices, "low": prices, "close": prices, "adjusted_close": prices,
        "volume": prices * 0 + 1e6, "split_factor": prices * 0 + 1.0})
    alpha = runner.family_b_alphas(research, s_mask)["ALPHA_019"]
    assert alpha["FULL"].first_valid_index() == dates[549] and alpha["NEW"].first_valid_index() == dates[550]
    full = runner.coverage_loss(alpha[["FULL"]], s_mask[["FULL"]], resets)["total"]
    new = runner.coverage_loss(alpha[["NEW"]], s_mask[["NEW"]], resets)["total"]
    assert full == sum(1 for r in resets if 300 <= r - 1 <= 548)
    assert new == sum(1 for r in resets if 300 <= r - 1 <= 549) == full + 1
    assert FAMILY_A_IDS == tuple(signals)


# ---------------------------------------------------------------- binding guards (plan 2.4, 4.5, 5.4, 6.1)


def _registered_copy(e2e, tmp_path, change):
    doc = copy.deepcopy(e2e["registration"])
    change(doc)
    path = tmp_path / "registration.json"
    return path, scenario.write_registration(doc, path)


def test_binding_guards_refuse_before_loading(pipeline, tmp_path, monkeypatch):
    loads = _spy_on_loads(monkeypatch)
    stale = copy_snapshot(pipeline, tmp_path / "inventory")
    inventory = json.loads((stale / "panel/inventory_discovery.json").read_text())
    inventory["discovery_inputs_sha256"] = "0" * 64
    (stale / "panel/inventory_discovery.json").write_text(json.dumps(inventory))
    assert rerun(pipeline, stale, tmp_path / "o1")["stop"]["reason"] == "derived_artifact_stale"

    evidence = copy_snapshot(pipeline, tmp_path / "evidence")
    curated = evidence / "terminal/terminal_evidence.csv"
    curated.write_text(curated.read_text().replace("fixture public notice", "edited notice", 1))
    stop = rerun(pipeline, evidence, tmp_path / "o2")["stop"]
    assert stop["reason"] == "derived_artifact_stale:terminal_validation_evidence_mismatch"

    windows = copy_snapshot(pipeline, tmp_path / "windows")
    record = json.loads((windows / "census/gap_windows.json").read_text())
    record["gap_windows"][0]["peeled_rows"] = 0
    (windows / "census/gap_windows.json").write_text(json.dumps(record))
    assert rerun(pipeline, windows, tmp_path / "o5")["stop"] == {
        "reason": "derived_artifact_stale", "detail": "census/segments.json", "trial": None, "trial_records_retained": 0}

    path, sha = _registered_copy(pipeline, tmp_path, _set(("holdout", "holdout_end_exclusive"), "2004-12-31"))
    assert rerun(pipeline, pipeline["snapshot"], tmp_path / "o3", sha=sha, registration_path=path)["stop"]["reason"] == \
        "holdout_overlap_refused"
    path, sha = _registered_copy(pipeline, tmp_path, lambda d: (
        _set(("discovery", "max_reset_to_reset_rows"), 6)(d), _set(("statistics", "cpcv", "holding_periods"), 6)(d)))
    assert rerun(pipeline, pipeline["snapshot"], tmp_path / "o4", sha=sha, registration_path=path)["stop"]["reason"] == \
        "census_runner_inconsistency:max_reset_span"
    assert loads == []


@pytest.mark.parametrize("edit, reason", [
    (lambda fields: {k: v.drop(v.index[100]) for k, v in fields.items()}, "calendar_mismatch"),
    (lambda fields: {**fields, "adjusted_close": fields["adjusted_close"].assign(
        **{BENCHMARK: fields["adjusted_close"][BENCHMARK].where(fields["adjusted_close"].index != fields[
            "adjusted_close"].index[100])})}, "calendar_mismatch"),
])
def test_loaded_calendar_and_benchmark_guards(pipeline, tmp_path, monkeypatch, edit, reason):
    real = runner.load_eod_cohort_panels
    monkeypatch.setattr(runner, "load_eod_cohort_panels", lambda *a, **k: edit(real(*a, **k)))
    sidecar = rerun(pipeline, pipeline["snapshot"], tmp_path)
    assert sidecar["stop"]["reason"] == reason and trial_lines(tmp_path) == []


def _no_composites(monkeypatch):
    def failing(*args, **kwargs):
        raise ValueError("composite construction unavailable in this oracle")

    monkeypatch.setattr(runner, "family_b_composites", failing)


def test_warmup_bound_violation_is_class_one(pipeline, tmp_path, monkeypatch):
    census = json.loads(Path(pipeline["census_json"]).read_text())
    census["warm_up_estimate"]["post_join_warmup_estimate"]["REV_1M"] += 1000
    inflated = tmp_path / "census.json"
    inflated.write_text(json.dumps(census))
    path, sha = _registered_copy(pipeline, tmp_path, _set(("snapshot", "census_json_sha256"),
                                                     runner.sha256_bytes(inflated.read_bytes())))
    _no_composites(monkeypatch)
    sidecar = runner.run_rerun(pipeline["snapshot"], registration_path=path, registration_sha256=sha, output_dir=tmp_path,
                               census_json=inflated, seal_record=pipeline["seal_record"], code_commit="fixture")
    assert sidecar["stop"]["reason"] == "census_runner_inconsistency:warmup_estimate"
    assert sidecar["stop"]["trial"] == "REV_1M"
    assert [r["factor_id"] for r in trial_lines(tmp_path)] == ["MOM_12_1", "HIGH_52W"]


def test_family_a_trial_count_is_asserted_before_inference(pipeline, tmp_path, monkeypatch):
    _no_composites(monkeypatch)
    monkeypatch.setattr(runner, "FAMILY_A_IDS", FAMILY_A_IDS[:5])
    sidecar = rerun(pipeline, pipeline["snapshot"], tmp_path)
    assert sidecar["stop"]["reason"] == "family_size_mismatch" and len(trial_lines(tmp_path)) == 5 + 63


def test_failed_trials_keep_their_slots_and_the_gate_reads_evaluation_incomplete(pipeline, tmp_path, monkeypatch):
    def failing_family_a(*args, **kwargs):
        raise ValueError("family A unavailable in this oracle")

    _no_composites(monkeypatch)
    monkeypatch.setattr(runner, "family_a_signals", failing_family_a)
    monkeypatch.setattr(runner, "book_trial", lambda *a, **k: (runner._failure(ValueError("book stub")), None, None))
    sidecar = rerun(pipeline, pipeline["snapshot"], tmp_path)
    assert sidecar["run_status"] == "completed" and sidecar["gate"]["outcome"] == "evaluation_incomplete"
    lines = trial_lines(tmp_path)
    assert len(lines) == 69 + 36 + 126
    assert {r["status"] for r in lines if r["family"] == "A"} == {"failed"}
    rows = sidecar["families"]["A"]["rows"]
    assert all(row["by_q"] is None and row["reject"] is False for row in rows.values())
    assert {v["unavailable_reason"] for v in sidecar["cpcv"].values()} == {
        "pbo_unavailable:insufficient_completed_strategies"}
    assert sidecar["cpcv"]["A_long_short"]["pbo_columns_missing_failed"] == 6
