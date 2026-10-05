"""Synthetic tests for the Milestone 5.5 screen, shortlist, success, and stop decisions (card m55-criteria).

Every series is generated here; no test reads data or opens a network connection.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

import research.m55_criteria as crit
from features.diagnostics import newey_west_mean_tstat
from features.multiple_testing import adjust_pvalues
from research.m4_7_sp500_pit_rerun import RunnerStop
from research.m55_index_tilt import COST_SCALES, dated_cost_frame


SCREEN = pd.period_range("1963-07", "1992-12", freq="M")
CONFIRM = pd.period_range("1993-02", "2014-03", freq="M")
CHECK = pd.period_range("2014-04", "2025-12", freq="M")


def noise(months: pd.PeriodIndex, seed: int, mean: float = 0.0, scale: float = 0.01) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series(mean + scale * rng.standard_normal(len(months)), index=months)


def stops(reason: str):
    return pytest.raises(RunnerStop, match=f"^{reason}")


def record(ir: float, t: float) -> dict:
    return {"information_ratio": ir, "hac_t": t, "annual_active_mean": 0.01, "annual_te": 0.02}


# Periods and input checks ---------------------------------------------------------------

def test_confirm_window_has_254_months():
    assert len(pd.period_range(crit.CONFIRM_START, crit.CONFIRM_END, freq="M")) == crit.CONFIRM_MONTHS == 254
    assert crit.SCREEN_END + 2 == crit.CONFIRM_START and crit.CONFIRM_END + 1 == crit.CHECK_START


def test_screen_refuses_one_confirm_month():
    months = pd.period_range("1980-01", "1993-02", freq="M")
    with stops("period_violation"):
        crit.screen_record(noise(months, 1), noise(months, 2))
    early = pd.period_range("1963-06", "1970-01", freq="M")
    with stops("period_violation"):
        crit.check_series(noise(early, 1), "x", "screen")
    late_start = pd.period_range("1975-01", "1992-12", freq="M")      # a signal may start after 1963-07
    assert len(crit.check_series(noise(late_start, 1), "x", "screen")) == len(late_start)
    early_end = pd.period_range("1975-01", "1992-11", freq="M")       # the screen must end at 1992-12
    with stops("period_violation"):
        crit.check_series(noise(early_end, 1), "x", "screen")
    with stops("period_violation"):
        crit.screen_record(noise(early_end, 1), noise(early_end, 2))


def test_confirm_and_check_guards():
    for months in (pd.period_range("1993-01", "2014-03", freq="M"), pd.period_range("1993-02", "2014-04", freq="M"),
                   CONFIRM[1:], CONFIRM[:-1]):
        with stops("period_violation"):
            crit.composite_test(noise(months, 1), noise(months, 2), noise(months, 3))
    with stops("period_violation"):
        crit.low_risk_check(noise(CHECK.insert(0, pd.Period("2014-03", "M")), 1),
                            noise(CHECK.insert(0, pd.Period("2014-03", "M")), 2))
    with stops("period_violation"):
        crit.check_series(noise(CHECK[1:], 1), "x", "check")
    with stops("period_invalid"):
        crit.check_series(noise(CHECK, 1), "x", "holdout")


def test_missing_values_and_months_refuse_without_fill():
    series = noise(CONFIRM, 1)
    for bad in (np.nan, np.inf, -np.inf):
        broken = series.copy()
        broken.iloc[10] = bad
        with stops("missing_return"):
            crit.composite_test(broken, noise(CONFIRM, 2), noise(CONFIRM, 3))
    assert np.isfinite(series).all()                         # the input was not filled in place
    with stops("month_missing"):
        crit.check_series(series.drop(series.index[5]), "x", "confirm")
    with stops("months_misaligned"):
        crit.check_paired({"a": noise(SCREEN[-100:], 1), "b": noise(SCREEN[-101:], 2)}, "screen")
    with stops("series_invalid"):
        crit.check_series(series.iloc[::-1], "x", "confirm")
    with stops("series_invalid"):
        crit.check_series(pd.concat([series, series.iloc[-1:]]), "x", "confirm")
    with stops("series_invalid"):
        crit.check_series(series.set_axis(series.index.to_timestamp()), "x", "confirm")
    with stops("series_invalid"):
        crit.check_series(pd.Series(True, index=CONFIRM), "x", "confirm")


# Annual figures and the screen record ---------------------------------------------------

def test_hand_computed_screen_record():
    months = pd.period_range("1992-07", "1992-12", freq="M")
    cw = pd.Series([0.01, -0.02, 0.03, 0.00, 0.01, 0.02], index=months)
    active = [0.004, -0.001, 0.003, 0.002, -0.002, 0.006]
    net = cw + pd.Series(active, index=months)
    out = crit.screen_record(net, cw, annual_turnover=0.4)
    mean = sum(active) / 6
    sd = math.sqrt(sum((a - mean) ** 2 for a in active) / 5)
    assert out["annual_active_mean"] == pytest.approx(12 * mean, abs=1e-15)
    assert out["annual_te"] == pytest.approx(sd * math.sqrt(12), rel=1e-12)
    assert out["information_ratio"] == pytest.approx(12 * mean / (sd * math.sqrt(12)), rel=1e-12)
    assert out["hac_t"] == pytest.approx(newey_west_mean_tstat(net - cw), rel=1e-12)
    assert out["p_one_sided"] == pytest.approx(norm.sf(out["hac_t"]), rel=1e-12)
    assert (out["months"], out["first_month"], out["last_month"], out["annual_turnover"]) == (6, "1992-07",
                                                                                             "1992-12", 0.4)
    assert crit.screen_record(net, cw)["annual_turnover"] is None
    with stops("turnover_invalid"):
        crit.screen_record(net, cw, annual_turnover=-0.1)


def test_constant_active_refuses():
    cw = pd.Series(0.0, index=SCREEN[-60:])
    with stops("statistic_undefined"):
        crit.screen_record(cw + 0.001, cw)


# Shortlist ------------------------------------------------------------------------------

def test_shortlist_boundary():
    records = {"S1": record(0.2, 1.0), "S2": record(np.nextafter(0.2, 0.0), 2.0),
               "S3": record(0.5, np.nextafter(1.0, 0.0)), "S4": record(0.3, 1.5)}
    out = crit.freeze_shortlist(records)
    assert out["shortlist"] == ["S1", "S4"] and out["decision"] == "shortlist_frozen"
    assert set(out["candidates"]) == {"S1", "S2", "S3", "S4"}            # failed candidates stay visible
    assert [out["candidates"][c]["shortlisted"] for c in ("S1", "S2", "S3", "S4")] == [True, False, False, True]
    assert out["rule"] == {"ir_min": 0.2, "t_min": 1.0, "shortlist_cap": 10}


def test_shortlist_cap_and_empty():
    with stops("shortlist_over_cap"):
        crit.freeze_shortlist({f"S{k:02d}": record(0.5, 2.0) for k in range(11)})
    assert len(crit.freeze_shortlist({f"S{k:02d}": record(0.5, 2.0) for k in range(10)})["shortlist"]) == 10
    empty = crit.freeze_shortlist({"S1": record(0.1, 2.0), "S2": record(0.3, 0.5)})
    assert empty["shortlist"] == [] and empty["decision"] == "screen_empty" and len(empty["digest_sha256"]) == 64


def test_digest_stable_and_sensitive():
    records = {"S1": record(0.25, 1.2), "S2": record(0.1, 0.4)}
    first = crit.freeze_shortlist(records)["digest_sha256"]
    assert crit.freeze_shortlist(dict(reversed(list(records.items()))))["digest_sha256"] == first
    for candidate, key in (("S1", "annual_te"), ("S2", "information_ratio"), ("S2", "annual_active_mean")):
        changed = {c: dict(r) for c, r in records.items()}
        changed[candidate][key] = np.nextafter(changed[candidate][key], 1.0)
        assert crit.freeze_shortlist(changed)["digest_sha256"] != first
    assert crit.canonical_json({"b": 0.1, "a": [1, None, True]}) == '{"a":[1,null,true],"b":"0.10000000000000001"}'
    with stops("digest_value_invalid"):
        crit.canonical_json({"a": math.nan})


def test_screen_from_series():
    cw = noise(SCREEN, 10)
    candidates = {"S1": {"net": cw + noise(SCREEN, 11, mean=0.002, scale=0.004), "cw_net": cw},
                  "S2": {"net": cw + noise(SCREEN, 12, mean=-0.001, scale=0.004), "cw_net": cw,
                         "annual_turnover": 0.3}}
    out = crit.screen(candidates)
    assert out["shortlist"] == ["S1"] and out["candidates"]["S2"]["annual_turnover"] == 0.3
    assert crit.screen(candidates)["digest_sha256"] == out["digest_sha256"]


# Test A and the primary family ----------------------------------------------------------

def test_intersection_union_picks_larger_p():
    spy, cw = noise(CONFIRM, 1), noise(CONFIRM, 2)
    composite = spy + noise(CONFIRM, 3, mean=0.002, scale=0.005)
    out = crit.composite_test(composite, spy, cw)
    assert out["vs_spy"]["hac_t"] == pytest.approx(newey_west_mean_tstat(composite - spy), rel=1e-12)
    assert out["vs_cw"]["p_one_sided"] == pytest.approx(norm.sf(newey_west_mean_tstat(composite - cw)), rel=1e-12)
    assert out["p_a"] == max(out["vs_spy"]["p_one_sided"], out["vs_cw"]["p_one_sided"])
    assert out["vs_spy"]["p_one_sided"] < out["vs_cw"]["p_one_sided"] == out["p_a"]


def test_holm_primary_cases():
    alone = crit.holm_primary(0.02, 0.5)
    assert alone["A"] == pytest.approx(0.04) and alone["A"] <= crit.ALPHA < alone["B"]
    both = crit.holm_primary(0.01, 0.04)
    assert both == pytest.approx({"A": 0.02, "B": 0.04}) and max(both.values()) <= crit.ALPHA
    fails = crit.holm_primary(0.04, 0.30)
    assert fails["A"] == pytest.approx(0.08) and fails["A"] > crit.ALPHA


POSITIVE = {"vs_spy": 0.01, "vs_cw": 0.008}


def test_decide_a_rules():
    assert crit.decide_a(0.03, POSITIVE, POSITIVE, POSITIVE)["label"] == "met"
    assert crit.decide_a(0.08, POSITIVE, POSITIVE, POSITIVE)["label"] == "positive_not_shown"
    cost = crit.decide_a(0.03, POSITIVE, {"vs_spy": 0.001, "vs_cw": 0.0}, POSITIVE)      # 2x sign must stay > 0
    assert not cost["passed"] and not cost["conditions"]["cost_2x_means_positive"]
    assert cost["label"] == "positive_not_shown"
    zero_check = crit.decide_a(0.03, POSITIVE, POSITIVE, {"vs_spy": 0.0, "vs_cw": 0.0})   # zero is not negative
    assert zero_check["passed"]
    negative_check = crit.decide_a(0.03, POSITIVE, POSITIVE, {"vs_spy": -1e-9, "vs_cw": 0.01})
    assert not negative_check["passed"] and not negative_check["conditions"]["check_means_not_negative"]
    assert crit.decide_a(0.03, {"vs_spy": 0.01, "vs_cw": -0.001}, POSITIVE, POSITIVE)["label"] == "not_met"


def test_decide_b_rules():
    good = {"annual_gap": -0.004, "vol_ratio": 0.95}
    assert crit.decide_b(0.05, 0.90, 0.95, good)["passed"]
    assert not crit.decide_b(0.05, np.nextafter(0.90, 1.0), 0.95, good)["passed"]
    assert not crit.decide_b(0.0500001, 0.85, 0.95, good)["passed"]
    assert not crit.decide_b(0.01, 0.85, 0.95, {"annual_gap": -0.005, "vol_ratio": 0.95})["passed"]
    assert not crit.decide_b(0.01, 0.85, 0.95, {"annual_gap": 0.0, "vol_ratio": 1.0})["passed"]


def test_decide_b_bootstrap_upper_bound_boundary():
    good = {"annual_gap": 0.0, "vol_ratio": 0.9}
    assert crit.decide_b(0.01, 0.85, np.nextafter(1.0, 0.0), good)["passed"]
    at_one = crit.decide_b(0.01, 0.85, 1.0, good)                     # O-21: the bound must be below 1.0
    assert not at_one["passed"] and not at_one["conditions"]["bootstrap_upper_below_one"]
    assert all(v for k, v in at_one["conditions"].items() if k != "bootstrap_upper_below_one")


def test_stop_floor_boundary():
    assert crit.stop_after_confirm(0.003) is None
    assert crit.stop_after_confirm(np.nextafter(0.003, 0.0)) == "confirm_below_floor"
    assert crit.stop_after_confirm(-0.01) == "confirm_below_floor"


# Test B ---------------------------------------------------------------------------------

def test_non_inferiority_at_margin_and_above():
    spy = noise(CONFIRM, 4)
    swing = pd.Series(np.tile([0.01, -0.01], len(CONFIRM) // 2), index=CONFIRM)
    at_margin = crit.low_risk_test(spy - crit.NI_MARGIN / 12 + swing, spy)
    assert at_margin["t_ni"] == pytest.approx(0.0, abs=1e-9) and at_margin["p_ni"] == pytest.approx(0.5)
    above = crit.low_risk_test(spy + 0.001 + 0.002 * swing, spy)
    assert above["t_ni"] > 3.0 and above["p_ni"] < 0.01


def test_bootstrap_ratio_cases():
    spy = noise(CONFIRM, 5, scale=0.04)
    scaled = crit.low_risk_test(0.8 * spy, spy)
    assert scaled["vol_ratio"] == pytest.approx(0.8, rel=1e-12)
    assert scaled["bootstrap"]["p_vol"] == 0.0 and scaled["bootstrap"]["upper_95"] == pytest.approx(0.8, rel=1e-12)
    assert scaled["p_b"] == max(scaled["p_ni"], 0.0)
    same = crit.bootstrap_vol_ratio(spy.to_numpy(), spy.to_numpy())
    assert same["p_vol"] == 1.0 and same["upper_95"] == 1.0
    ratio = crit.annual_vol(spy) / crit.annual_vol(spy.copy())
    p_b = max(0.0, same["p_vol"])                    # even a perfect non-inferiority p cannot rescue it
    assert ratio == 1.0 and not crit.decide_b(crit.holm_primary(0.0, p_b)["B"], ratio, same["upper_95"],
                                              {"annual_gap": 0.0, "vol_ratio": 0.5})["passed"]
    with stops("statistic_undefined"):                # a gap of exactly zero has no HAC t
        crit.low_risk_test(spy.copy(), spy)


def test_bootstrap_fixed_seed_and_same_blocks():
    spy = noise(CONFIRM, 6, scale=0.04)
    low = 0.7 * spy + noise(CONFIRM, 7, scale=0.02)
    first, second = crit.low_risk_test(low, spy), crit.low_risk_test(low, spy)
    assert first["bootstrap"] == second["bootstrap"]
    assert first["bootstrap"]["draws"] == 10_000 and first["bootstrap"]["block_months"] == 12
    assert 0.0 < first["bootstrap"]["upper_95"] < 1.0 and first["bootstrap"]["p_vol"] == 0.0
    shifted = noise(CONFIRM, 9, scale=0.04)
    assert crit.low_risk_test(0.7 * shifted + noise(CONFIRM, 7, scale=0.02), shifted)["bootstrap"] != first["bootstrap"]
    with stops("bootstrap_too_short"):
        crit.bootstrap_vol_ratio(np.arange(11.0), np.arange(11.0))


# Drawdowns ------------------------------------------------------------------------------

def test_drawdown_episodes_hand_built():
    months = pd.period_range("2000-01", "2000-09", freq="M")
    # wealth: 1.1, 0.99, 1.12, 1.232, 0.9856, 1.08416, 1.3, 1.235, 1.1115
    returns = pd.Series([0.1, -0.1, 1.12 / 0.99 - 1, 0.1, -0.2, 0.1, 1.3 / 1.08416 - 1, -0.05, -0.1], index=months)
    episodes = crit.drawdown_episodes(returns)
    assert [(e["peak_month"], e["trough_month"], e["recovery_month"]) for e in episodes] == [
        ("2000-04", "2000-05", "2000-07"), ("2000-07", "2000-09", None), ("2000-01", "2000-02", "2000-03")]
    assert [e["depth"] for e in episodes] == pytest.approx([-0.2, 0.95 * 0.9 - 1, -0.1])
    start = crit.drawdown_episodes(pd.Series([-0.1, 0.05], index=months[:2]))
    assert start == [{"peak_month": "1999-12", "trough_month": "2000-01", "recovery_month": None,
                      "depth": pytest.approx(-0.1)}]
    assert crit.drawdown_episodes(pd.Series([0.01, 0.0, 0.02], index=months[:3])) == []


def test_low_risk_reports_drawdowns():
    spy = noise(CONFIRM, 8, scale=0.04)
    out = crit.low_risk_test(0.8 * spy, spy)
    assert len(out["largest_drawdowns"]["spy"]) == 3 and len(out["largest_drawdowns"]["low_risk"]) == 3
    deepest = crit.drawdown_episodes(spy)[0]["depth"]
    assert out["drawdown_ratio"] == pytest.approx(crit.drawdown_episodes(0.8 * spy)[0]["depth"] / deepest)


# Full primary decision and the secondary family -----------------------------------------

def primary_inputs(edge: float) -> tuple[dict, dict, dict]:
    spy = noise(CONFIRM, 20, scale=0.04)
    cw = spy + noise(CONFIRM, 21, scale=0.002)
    composite = cw + noise(CONFIRM, 22, mean=edge, scale=0.002)
    low = 0.8 * spy + 0.2 * spy.mean() + noise(CONFIRM, 23, mean=0.0015, scale=0.002)
    check_spy = noise(CHECK, 24, scale=0.04)
    check_cw = check_spy + noise(CHECK, 25, scale=0.002)
    check = {"composite": check_spy + 0.001, "spy": check_spy, "cw": check_cw,
             "low_risk": 0.8 * check_spy + 0.2 * check_spy.mean() + noise(CHECK, 26, mean=0.001, scale=0.002)}
    confirm = {"composite": composite, "spy": spy, "cw": cw, "low_risk": low}
    return confirm, {"composite": composite - 0.0002, "cw": cw - 0.00005}, check


FROZEN = crit.freeze_shortlist({"S1": record(0.5, 2.0), "S2": record(0.1, 0.5)})


def test_primary_decision_end_to_end():
    confirm, confirm_2x, check = primary_inputs(edge=0.004)
    out = crit.primary_decision(FROZEN, confirm, confirm_2x, check)
    a, b = out["test_a"], out["test_b"]
    assert (a["holm_p"], b["holm_p"]) == pytest.approx(tuple(crit.holm_primary(a["p_a"], b["p_b"]).values()))
    assert a["passed"] and a["label"] == "met" and b["passed"] and out["stop"] is None
    weak_confirm, weak_2x, weak_check = primary_inputs(edge=-0.001)
    weak = crit.primary_decision(FROZEN, weak_confirm, weak_2x, weak_check)
    assert weak["stop"] == "confirm_below_floor"
    with stops("period_violation"):
        crit.primary_decision(FROZEN, confirm, confirm_2x, {**check, "spy": confirm["spy"]})


def test_primary_decision_checks_the_frozen_screen():
    confirm, confirm_2x, check = primary_inputs(edge=0.004)
    tampered = {**FROZEN, "candidates": {c: dict(r) for c, r in FROZEN["candidates"].items()}}
    tampered["candidates"]["S2"]["hac_t"] = 0.6                        # a failed candidate's value changed
    with stops("shortlist_digest_mismatch"):
        crit.primary_decision(tampered, confirm, confirm_2x, check)
    with stops("shortlist_digest_mismatch"):
        crit.primary_decision({**FROZEN, "shortlist": ["S1", "S2"]}, confirm, confirm_2x, check)
    with stops("shortlist_digest_mismatch"):
        crit.primary_decision({**FROZEN, "digest_sha256": "0" * 64}, confirm, confirm_2x, check)
    empty = crit.freeze_shortlist({"S1": record(0.1, 2.0)})
    assert empty["decision"] == "screen_empty"
    with stops("screen_empty_confirm"):
        crit.primary_decision(empty, confirm, confirm_2x, check)
    with stops("screen_empty_confirm"):                                 # refused before any confirm series is read
        crit.primary_decision(empty, {}, {}, {})
    with stops("screen_empty_confirm"):                                 # a relabeled empty screen still refuses
        crit.primary_decision({**empty, "decision": "shortlist_frozen"}, confirm, confirm_2x, check)
    assert crit.shortlist_digest(FROZEN) == FROZEN["digest_sha256"]


def test_secondary_family_by_q_values():
    confirm, _, _ = primary_inputs(edge=0.004)
    entries = {f"S{k}": {"composite": confirm["composite"] + noise(CONFIRM, 30 + k, scale=0.002),
                         "spy": confirm["spy"], "cw": confirm["cw"]} for k in range(3)}
    out = crit.secondary_family(entries)
    p = pd.Series({k: v["p_a"] for k, v in out["members"].items()})
    q = adjust_pvalues(p, method="by")
    assert [out["members"][k]["q_by"] for k in p.index] == q.tolist()
    assert out["decides_nothing"] is True and "decides nothing" in out["note"]


# Screen costs ---------------------------------------------------------------------------

def test_screen_cost_schedule_switches():
    dates = pd.DatetimeIndex(["1963-07-31", "1975-04-30", "1975-05-01", "1992-12-31", "1993-01-01", "2001-03-30",
                              "2001-04-02", "2006-12-29", "2007-01-02"])
    for case, scale in COST_SCALES.items():
        frame = dated_cost_frame(dates, crit.SCREEN_COST_SCHEDULE, scale)
        expected = np.array([[30, 30], [30, 30], [10, 30], [10, 30], [5, 20], [5, 20], [2, 8], [2, 8], [1, 4]])
        assert frame.to_numpy() == pytest.approx(expected * scale), case
