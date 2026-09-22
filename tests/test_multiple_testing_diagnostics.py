"""Run-family retention and integration boundary checks using synthetic books."""

from copy import deepcopy
import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from features.multiple_testing import METHODS, return_test_statistics
from research.multiple_testing_diagnostics import render_multiple_testing, summarize_multiple_testing


def record(trial_id, *, sign=1, direction="long_only", weighting="equal", penalty=0.0):
    values = pd.Series(sign*(.05 + np.random.default_rng(4).normal(0, .01, 60)))
    return {
        "trial_id": trial_id, "attempt_id": trial_id+"-attempt", "status": "completed",
        "specification": {"factor_id": "synthetic_alpha", "direction": direction,
                          "parameters": {"weighting_scheme": weighting, "turnover_penalty_lambda": penalty}},
        "return_test": return_test_statistics(values),
    }


def test_complete_family_retains_directions_variants_and_negative_findings() -> None:
    attempts = [record("a"), record("b", direction="long_short", sign=-1),
                record("c", weighting="inverse_volatility"), record("d", penalty=.5)]
    summary = summarize_multiple_testing(attempts)
    assert summary["family_size"] == 4
    assert summary["hac_by_rejections"] == 4
    assert summary["positive_hac_by_rejections"] == 3
    assert [row["trial_id"] for row in summary["rows"]] == list("abcd")
    for row in summary["rows"]:
        assert set(row["iid_haircuts"]) == set(METHODS)
        assert set(row["adjusted_pvalues"]) == {"hac", "iid"}
        assert row["iid_bonferroni_t_hurdle"] > 2
    assert summary["rows"][1]["iid_haircuts"]["bonferroni"]["adjusted_sharpe"] < 0
    json.dumps(summary, allow_nan=False)
    text = render_multiple_testing(summary)
    for trial in "abcd":
        assert f"| {trial} |" in text
    for label in ("HAC BY", "IID", "PRDS", "DIAGNOSTIC_ONLY", "historical", "negative rejection"):
        assert label in text


def test_identical_repeats_deduplicate_and_conflicts_are_order_invariant() -> None:
    a = record("a")
    repeated = deepcopy(a)
    repeated["attempt_id"] = "another-attempt"
    same = summarize_multiple_testing([a, repeated])
    assert same["attempt_count"] == 2 and same["family_size"] == 1
    assert same["valid_trial_count"] == 1
    conflicting = record("a", sign=-1)
    for attempts in ([a, conflicting], [conflicting, a]):
        result = summarize_multiple_testing(attempts)
        assert result["family_size"] == 1 and result["valid_trial_count"] == 0
        row = result["rows"][0]
        assert row["return_test"]["status"] == "conflicting_attempts"
        assert row["adjusted_pvalues"]["hac"]["by"] is None
        assert row["rejections"]["hac"]["by"] is False
    assert summarize_multiple_testing([a, conflicting]) == summarize_multiple_testing([conflicting, a])


def test_failed_incomplete_unavailable_and_degenerate_trials_keep_slots() -> None:
    valid = record("a")
    failed = {**record("b"), "status": "failed", "error": "synthetic failure"}
    incomplete = {**record("c"), "status": "started"}
    unavailable = record("d")
    del unavailable["return_test"]
    constant = {**record("e"), "return_test": return_test_statistics(pd.Series([0.0]*60))}
    missing = {**record("f"), "return_test": return_test_statistics(pd.Series([0.0, np.nan, .1]))}
    result = summarize_multiple_testing([valid, failed, incomplete, unavailable, constant, missing])
    assert result["family_size"] == 6 and result["valid_trial_count"] == 1
    assert result["rows"][0]["adjusted_pvalues"]["hac"]["bonferroni"] == pytest.approx(6*valid["return_test"]["hac_pvalue"])
    for row in result["rows"][1:]:
        assert row["iid_haircuts"] == {}
        assert row["positive_mean"] is False
        assert all(value is None for value in row["adjusted_pvalues"]["hac"].values())
        assert row["iid_bonferroni_t_hurdle"] is None
    json.dumps(result, allow_nan=False)


def test_failed_repeat_withholds_successful_sibling() -> None:
    success = record("a")
    failure = {**success, "status": "failed"}
    assert summarize_multiple_testing([success, failure])["valid_trial_count"] == 0


def test_declared_family_sensitivity_and_empty_family() -> None:
    baseline = summarize_multiple_testing([record("a"), record("b")])
    larger = summarize_multiple_testing([record("a"), record("b")], family_size=20)
    assert larger["additional_unavailable_hypotheses"] == 18
    for first, second in zip(baseline["rows"], larger["rows"], strict=True):
        for basis in ("hac", "iid"):
            for method in METHODS:
                assert second["adjusted_pvalues"][basis][method] >= first["adjusted_pvalues"][basis][method]
        assert second["iid_bonferroni_t_hurdle"] > first["iid_bonferroni_t_hurdle"]
    with pytest.raises(ValueError):
        summarize_multiple_testing([record("a"), record("b")], family_size=1)
    empty = summarize_multiple_testing([])
    assert empty["family_size"] == 0 and empty["rows"] == []
    assert "0 distinct trials" in render_multiple_testing(empty)
    json.dumps(empty, allow_nan=False)


def test_completed_attempt_records_exact_measured_sample(tmp_path, monkeypatch) -> None:
    from research import multifactor_diagnostic_mvp as m
    values = pd.Series([0.0, .01, -.02, .03, .005])
    book = SimpleNamespace(returns=values)
    monkeypatch.setattr(m, "run_long_only_backtest", lambda **kwargs: book)
    attempts = []
    path = tmp_path / "attempts.jsonl"
    result = m._run_recorded_trial(
        factor_id="synthetic", direction="long_only", inventory=attempts,
        inventory_path=path, trial_context={}, periods_per_year=12,
    )
    assert result is book
    expected = return_test_statistics(values.iloc[1:], periods_per_year=12)
    assert attempts[0]["return_test"] == expected
    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert [event["status"] for event in events] == ["started", "completed"]
    assert events[1]["return_test"] == expected
    assert len(values) == 5


def test_inference_failure_keeps_failed_book_event(tmp_path, monkeypatch) -> None:
    from research import multifactor_diagnostic_mvp as m
    monkeypatch.setattr(m, "run_long_only_backtest", lambda **kwargs: SimpleNamespace(returns=pd.Series([0, .1, -.1, .2])))
    attempts = []
    path = tmp_path / "attempts.jsonl"
    with pytest.raises(ValueError):
        m._run_recorded_trial(factor_id="synthetic", direction="long_only", inventory=attempts,
                              inventory_path=path, trial_context={}, periods_per_year=True)
    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert events[-1]["status"] == "failed"
    assert summarize_multiple_testing(attempts)["valid_trial_count"] == 0
