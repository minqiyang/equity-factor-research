"""M4.7 stage a-0 family-partitioned BY and decision-gate oracles (T-REG-3, T-REG-7)."""

from copy import deepcopy
import json

import numpy as np
import pandas as pd
import pytest

from features.multiple_testing import adjust_pvalues, return_test_statistics
from research.m4_7_sp500_pit_rerun import (
    FactorGateInput,
    decide_gate,
    ic_minimum_detectable_effect,
    sign_stability,
)
from research.multiple_testing_diagnostics import summarize_multiple_testing


def trial(trial_id, family, *, shift, key="return_test", status="completed", seed=0):
    values = pd.Series(shift + np.random.default_rng(seed).normal(0.0, 0.05, 120))
    return {"trial_id": trial_id, "family": family, "status": status,
            "specification": {"factor_id": trial_id}, key: return_test_statistics(values, periods_per_year=12)}


def family_inventory(key="return_test"):
    family_a = [trial(f"A{i}", "A", shift=0.004 * i, key=key, seed=i) for i in range(6)]
    family_b = [trial(f"B{i}", "B", shift=0.03, key=key, seed=10 + i) for i in range(3)]
    return family_a, family_b


def test_t_reg_3_adjusts_within_each_declared_family():
    family_a, family_b = family_inventory()
    summary = summarize_multiple_testing(family_a + family_b, family_sizes={"A": 6, "B": 3})
    rows = {row["trial_id"]: row for row in summary["rows"]}
    for members, size in ((family_a, 6), (family_b, 3)):
        pvalues = pd.Series([m["return_test"]["hac_pvalue"] for m in members])
        expected = adjust_pvalues(pvalues, method="by", family_size=size)
        for member, value in zip(members, expected):
            assert rows[member["trial_id"]]["adjusted_pvalues"]["hac"]["by"] == pytest.approx(value, abs=1e-15)
            assert rows[member["trial_id"]]["family"] == member["family"]
    alone = summarize_multiple_testing(family_a, family_sizes={"A": 6})
    for row in alone["rows"]:
        assert row["adjusted_pvalues"] == rows[row["trial_id"]]["adjusted_pvalues"]
    assert summary["family_sizes"] == {"A": 6, "B": 3} and summary["family_size"] == 9
    json.dumps(summary, allow_nan=False)


def test_t_reg_3_family_b_trial_cannot_enter_family_a():
    family_a, family_b = family_inventory()
    moved = deepcopy(family_b[0])
    moved["family"] = "A"
    with pytest.raises(ValueError, match="family_size_mismatch"):
        summarize_multiple_testing(family_a + [moved] + family_b[1:], family_sizes={"A": 6, "B": 3})
    relabeled = {**deepcopy(family_a[0]), "family": "B"}
    result = summarize_multiple_testing(family_a + [relabeled] + family_b[:2], family_sizes={"A": 6, "B": 2})
    assert next(r for r in result["rows"] if r["trial_id"] == "A0")["return_test"]["status"] == "conflicting_attempts"


def test_t_reg_3_aborted_trial_keeps_its_p_equal_one_slot():
    family_a, family_b = family_inventory()
    family_a[2] = {**family_a[2], "status": "failed"}
    summary = summarize_multiple_testing(family_a + family_b, family_sizes={"A": 6, "B": 3})
    rows = {row["trial_id"]: row for row in summary["rows"]}
    assert rows["A2"]["return_test"]["status"] == "failed_or_incomplete_attempt"
    assert rows["A2"]["adjusted_pvalues"]["hac"]["by"] is None
    valid = [m for m in family_a if m["status"] == "completed"]
    pvalues = pd.Series([m["return_test"]["hac_pvalue"] for m in valid] + [np.nan])
    expected = adjust_pvalues(pvalues, method="by", family_size=6)
    for member, value in zip(valid, expected):
        assert rows[member["trial_id"]]["adjusted_pvalues"]["hac"]["by"] == pytest.approx(value, abs=1e-15)


def test_t_reg_3_count_mismatch_unknown_and_missing_family_refuse():
    family_a, family_b = family_inventory()
    with pytest.raises(ValueError, match="family_size_mismatch"):
        summarize_multiple_testing(family_a[:5] + family_b, family_sizes={"A": 6, "B": 3})
    with pytest.raises(ValueError, match="family_unknown"):
        summarize_multiple_testing(family_a + family_b, family_sizes={"A": 6})
    missing = {k: v for k, v in family_a[0].items() if k != "family"}
    with pytest.raises(ValueError, match="family_unknown"):
        summarize_multiple_testing([missing] + family_a[1:], family_sizes={"A": 6})
    with pytest.raises(ValueError, match="mutually exclusive"):
        summarize_multiple_testing(family_a, family_size=6, family_sizes={"A": 6})


def test_t_reg_3_statistic_key_reads_ic_statistics():
    family_a, _ = family_inventory(key="ic_test")
    summary = summarize_multiple_testing(family_a, family_sizes={"A": 6}, statistic_key="ic_test")
    assert summary["valid_trial_count"] == 6
    assert summary["statistic_key"] == "ic_test"
    assert summary["null_hypothesis"].startswith("mean monthly Rank IC")
    assert all("return_test" not in row and row["ic_test"]["status"] == "ok" for row in summary["rows"])


def test_t_reg_3_default_path_is_unchanged():
    family_a, _ = family_inventory()
    plain = [{k: v for k, v in m.items() if k != "family"} for m in family_a]
    default = summarize_multiple_testing(plain)
    assert default == summarize_multiple_testing(plain, family_size=None)
    assert "family_sizes" not in default and "statistic_key" not in default
    assert all("family" not in row for row in default["rows"])
    assert default["null_hypothesis"].startswith("mean daily net book return")


def gate(overrides=None):
    overrides = overrides or {}
    base = dict(status="evaluated", reject=False, mean_ic=0.01, sign_stable=True, net_ls=0.0001, mde=0.015)
    return [FactorGateInput(factor_id=f"F{i}", **{**base, **overrides.get(i, {})}) for i in range(6)]


@pytest.mark.parametrize(("overrides", "outcome"), [
    ({0: {"status": "failed"}}, "evaluation_incomplete"),
    ({3: {"mde": None}}, "evaluation_incomplete"),
    ({1: {"sign_stable": None}}, "evaluation_incomplete"),
    ({2: {"net_ls": None}}, "evaluation_incomplete"),
    ({0: {"reject": True, "mean_ic": 0.03}}, "proceed"),
    ({0: {"reject": True, "mean_ic": 0.03, "sign_stable": False}}, "survivor_without_confirmation"),
    ({0: {"reject": True, "mean_ic": 0.03, "net_ls": -0.0001}}, "survivor_without_confirmation"),
    ({}, "review_thesis"),
    ({4: {"mde": 0.025}}, "extend_first"),
])
def test_t_reg_7_truth_table(overrides, outcome):
    for projection in (True, False):
        assert decide_gate(gate(overrides), kill_reachable_projection=projection)["outcome"] == outcome


def test_t_reg_7_contrary_rejection_flags_and_routes_by_power():
    contrary = {0: {"reject": True, "mean_ic": -0.03}}
    result = decide_gate(gate(contrary), kill_reachable_projection=False)
    assert result["outcome"] == "review_thesis"
    assert result["contrary_rejections"] == ("F0",)
    assert result["power_status"] == "adequate"
    underpowered = decide_gate(gate({**contrary, 5: {"mde": 0.025}}), kill_reachable_projection=True)
    assert underpowered["outcome"] == "extend_first"
    assert underpowered["contrary_rejections"] == ("F0",)
    assert underpowered["power_status"] == "inadequate"
    assert underpowered["kill_reachable_projection"] is True


def test_t_reg_7_negative_first_half_routes_to_survivor_without_confirmation():
    ic = pd.Series(np.r_[np.full(60, -0.01), np.full(60, 0.09)] + np.random.default_rng(1).normal(0, 0.01, 120))
    assert ic.mean() > 0 and sign_stability(ic) is False
    mde, _ = ic_minimum_detectable_effect(ic)
    factors = gate({0: {"reject": True, "mean_ic": float(ic.mean()), "sign_stable": sign_stability(ic),
                          "mde": mde}})
    assert decide_gate(factors, kill_reachable_projection=False)["outcome"] == "survivor_without_confirmation"


@pytest.mark.parametrize("ic", [pd.Series([0.05]), pd.Series(np.full(120, 0.02))])
def test_t_reg_7_one_month_and_zero_variance_series_are_incomplete(ic):
    mde, mde_single = ic_minimum_detectable_effect(ic)
    assert (mde, mde_single) == (None, None)
    result = decide_gate(gate({0: {"mde": mde}}), kill_reachable_projection=True)
    assert result["outcome"] == "evaluation_incomplete"
    assert result["power_status"] == "undefined"


def test_t_reg_7_realized_power_decides_regardless_of_projection():
    for projection in (True, False):
        assert decide_gate(gate(), kill_reachable_projection=projection)["outcome"] == "review_thesis"
        assert decide_gate(gate({2: {"mde": 0.025}}), kill_reachable_projection=projection)["outcome"] == (
            "extend_first")


def test_sign_stability_needs_twenty_four_months_per_half():
    assert sign_stability(pd.Series(np.full(47, 0.01))) is None
    assert sign_stability(pd.Series(np.full(48, 0.01))) is True
    assert sign_stability(pd.Series(np.r_[np.full(24, 0.01), np.full(24, -0.01)])) is False


def test_decide_gate_requires_six_factors():
    with pytest.raises(ValueError, match="family_size_mismatch"):
        decide_gate(gate()[:5], kill_reachable_projection=False)
