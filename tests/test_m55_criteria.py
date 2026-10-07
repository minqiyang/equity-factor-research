"""Synthetic tests for the Milestone 5.5 screen, shortlist, success, and stop decisions (card m55-criteria).

Every series is generated here; no test reads data or opens a network connection.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_series_equal
from scipy.stats import norm

import research.m55_criteria as crit
from features.diagnostics import newey_west_long_run_variance, newey_west_mean_tstat
from features.multiple_testing import adjust_pvalues
from research.m4_7_sp500_pit_rerun import RunnerStop
from research.m55_index_tilt import COST_SCALES, dated_cost_frame


SCREEN = pd.period_range("1963-07", "1992-12", freq="M")
CONFIRM = pd.period_range("1993-02", "2014-03", freq="M")
CHECK = pd.period_range("2014-04", "2019-06", freq="M").append(pd.period_range("2021-09", "2025-12", freq="M"))


def noise(months: pd.PeriodIndex, seed: int, mean: float = 0.0, scale: float = 0.01) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series(mean + scale * rng.standard_normal(len(months)), index=months)


def stops(reason: str):
    return pytest.raises(RunnerStop, match=f"^{reason}")


def record(ir: float, t: float) -> dict:
    return {"status": "ok", "information_ratio": ir, "hac_t": t, "annual_active_mean": 0.01, "annual_te": 0.02}


# Periods and input checks ---------------------------------------------------------------

def test_confirm_window_has_254_months():
    assert len(pd.period_range(crit.CONFIRM_START, crit.CONFIRM_END, freq="M")) == crit.CONFIRM_MONTHS == 254
    assert crit.SCREEN_END + 2 == crit.CONFIRM_START and crit.CONFIRM_END + 1 == crit.CHECK_START
    assert list(crit.CHECK_GAP_MONTHS.astype(str)) == [str(m) for m in pd.period_range("2019-07", "2021-08", freq="M")]
    assert len(crit.CHECK_GAP_MONTHS) == 26


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


def test_screen_minimum_length():
    assert len(crit.check_series(noise(SCREEN[-36:], 1), "x", "screen")) == 36
    with stops("screen_too_short"):
        crit.check_series(noise(SCREEN[-35:], 1), "x", "screen")
    with stops("screen_too_short"):
        crit.screen_record(noise(SCREEN[-35:], 1), noise(SCREEN[-35:], 2))


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


def test_check_period_skips_the_check_gap():
    full = pd.period_range("2014-04", "2025-12", freq="M")
    with stops("seal_month"):
        crit.check_series(noise(full, 1), "x", "check")
    for month in ("2019-07", "2020-07", "2020-08", "2021-08"):        # seal months and post-seal warm-up
        with stops("seal_month"):
            crit.check_series(noise(CHECK.insert(63, pd.Period(month, "M")).sort_values(), 1), "x", "check")
    warm = pd.period_range("2020-08", "2021-08", freq="M")
    with stops("seal_month"):                        # the old seal-only gap: rows for 2020-08 to 2021-08 after the seal
        crit.check_series(noise(CHECK.append(warm).sort_values(), 1), "x", "check")
    with stops("seal_month"):                        # warm-up rows with no row after them
        crit.check_series(noise(pd.period_range("2014-04", "2019-06", freq="M").append(warm), 1), "x", "check")
    assert len(crit.check_series(noise(CHECK, 1), "x", "check")) == len(CHECK)    # exactly 2019-07 to 2021-08 skipped
    before = pd.period_range("2014-04", "2019-06", freq="M")
    assert len(crit.check_series(noise(before, 1), "x", "check")) == len(before)
    with stops("month_missing"):                     # the check gap is the only allowed gap
        crit.check_series(noise(CHECK.delete(70), 1), "x", "check")
    with stops("month_missing"):
        crit.check_series(noise(CHECK.delete(63), 1), "x", "check")       # 2021-09 missing after the gap
    spy, low = noise(CHECK, 2, scale=0.04), noise(CHECK, 3, scale=0.03)
    out = crit.low_risk_check(low, spy)              # the joined months, no fill
    assert out["annual_gap"] == pytest.approx(12 * float(np.mean(low.to_numpy() - spy.to_numpy())), rel=1e-12)
    assert CHECK[62] == pd.Period("2019-06", "M") and CHECK[63] == pd.Period("2021-09", "M")


def test_missing_values_and_months_refuse_without_fill():
    series = noise(CONFIRM, 1)
    for bad in (np.nan, np.inf, -np.inf):
        broken = series.copy()
        broken.iloc[10] = bad
        saved = broken.copy()
        with stops("missing_return"):
            crit.composite_test(broken, noise(CONFIRM, 2), noise(CONFIRM, 3))
        assert_series_equal(broken, saved)           # the object passed in was not filled in place
    nullable = series.astype("Float64")
    nullable.iloc[10] = pd.NA
    with stops("missing_return"):
        crit.check_series(nullable, "x", "confirm")
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


def non_real_inputs() -> dict[str, pd.Series]:
    base = noise(CONFIRM, 1)
    finite = base.astype(complex)
    bad_imaginary = base.astype(complex)
    bad_imaginary.iloc[3] = complex(base.iloc[3], float("nan"))
    return {"complex": finite, "complex_nan_imaginary": bad_imaginary,
            "nullable_boolean": pd.Series(True, index=CONFIRM, dtype="boolean"),
            "numpy_boolean": pd.Series(True, index=CONFIRM, dtype=bool)}


def test_complex_and_boolean_dtypes_refuse_before_any_cast():
    confirm, confirm_2x, check = wired_inputs()
    for name, bad in non_real_inputs().items():
        saved = bad.copy()
        with stops("series_invalid"):
            crit.check_series(bad, name, "confirm")
        with stops("series_invalid"):
            crit.primary_decision(FROZEN, EXPECTED, {**confirm, "composite": bad}, confirm_2x, check)
        with stops("series_invalid"):
            crit.primary_decision(FROZEN, EXPECTED, {**confirm, "low_risk": bad}, confirm_2x, check)
        assert_series_equal(bad, saved), name
        assert bad.dtype == saved.dtype


# Annual figures and the screen record ---------------------------------------------------

def test_hand_computed_screen_record():
    months = SCREEN[-36:]
    cw = pd.Series(np.tile([0.01, -0.02, 0.03, 0.00, 0.01, 0.02], 6), index=months)
    active = [round(0.001 * k, 3) for k in np.random.default_rng(3).integers(-4, 7, size=36)]
    net = cw + pd.Series(active, index=months)
    out = crit.screen_record(net, cw, annual_turnover=0.4)
    realized = (net - cw).to_list()
    mean = sum(realized) / 36
    sd = math.sqrt(sum((a - mean) ** 2 for a in realized) / 35)
    assert out["annual_active_mean"] == pytest.approx(12 * mean, abs=1e-15)
    assert out["annual_te"] == pytest.approx(sd * math.sqrt(12), rel=1e-12)
    assert out["information_ratio"] == pytest.approx(12 * mean / (sd * math.sqrt(12)), rel=1e-12)
    assert out["hac_t"] == pytest.approx(newey_west_mean_tstat(net - cw), rel=1e-12)
    assert out["p_one_sided"] == pytest.approx(norm.sf(out["hac_t"]), rel=1e-12)
    assert (out["status"], out["months"], out["first_month"], out["last_month"], out["annual_turnover"]) == (
        "ok", 36, "1990-01", "1992-12", 0.4)
    assert crit.screen_record(net, cw)["annual_turnover"] is None
    with stops("turnover_invalid"):
        crit.screen_record(net, cw, annual_turnover=-0.1)


def test_undefined_candidate_gets_a_typed_failed_record():
    cw = pd.Series(0.0, index=SCREEN[-60:])
    undefined = crit.screen_record(cw + 0.001, cw)          # constant active: zero TE, no HAC t
    assert undefined["status"] == "undefined" and undefined["annual_te"] == 0.0
    assert undefined["information_ratio"] is None and undefined["hac_t"] is None and undefined["p_one_sided"] is None
    assert undefined["annual_active_mean"] == pytest.approx(0.012)
    good = cw + noise(SCREEN[-60:], 5, mean=0.003, scale=0.004)
    out = crit.screen({"S1": {"net": cw + 0.001, "cw_net": cw}, "S2": {"net": good, "cw_net": cw}})
    assert out["shortlist"] == ["S2"] and out["candidates"]["S1"]["shortlisted"] is False
    assert out["candidates"]["S1"]["status"] == "undefined"
    changed = crit.screen({"S1": {"net": cw + 0.002, "cw_net": cw}, "S2": {"net": good, "cw_net": cw}})
    assert changed["digest_sha256"] != out["digest_sha256"]    # the failed record is hashed
    with stops("record_invalid"):
        crit.freeze_shortlist({"S1": {"information_ratio": 0.5, "hac_t": 2.0}})


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
    frozen = crit.freeze_shortlist(records)
    assert crit.shortlist_digest({**frozen, "decision": "screen_empty"}) != frozen["digest_sha256"]
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
    assert cost["label"] == "not_met_robustness"
    zero_check = crit.decide_a(0.03, POSITIVE, POSITIVE, {"vs_spy": 0.0, "vs_cw": 0.0})   # zero is not negative
    assert zero_check["passed"]
    negative_check = crit.decide_a(0.03, POSITIVE, POSITIVE, {"vs_spy": -1e-9, "vs_cw": 0.01})
    assert not negative_check["passed"] and not negative_check["conditions"]["check_means_not_negative"]
    assert negative_check["label"] == "not_met_robustness"
    assert crit.decide_a(0.08, POSITIVE, {"vs_spy": -0.01, "vs_cw": -0.01}, POSITIVE)["label"] == "positive_not_shown"
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


def gpt_bootstrap_fixture() -> tuple[pd.Series, pd.Series]:
    rng = np.random.default_rng(44)
    spy = rng.normal(0.004, 0.04, size=len(CONFIRM))
    low = 0.91 * spy + rng.normal(0.0, 0.014, size=len(CONFIRM))
    return pd.Series(low, index=CONFIRM), pd.Series(spy, index=CONFIRM)


def oracle_ratios(low: np.ndarray, spy: np.ndarray, scheme: str = "blocks") -> np.ndarray:
    """An independent loop: 12-month blocks, starts 0 to n - 12, cut to n; or the i.i.d. or wrapped variants."""
    n, draws, block = len(low), 10_000, 12
    rng = np.random.default_rng(crit.BOOTSTRAP_SEED)
    blocks = math.ceil(n / block)
    if scheme == "iid":
        all_rows = rng.integers(0, n, size=(draws, n))
    else:
        top = n if scheme == "wrapped" else n - block + 1
        starts = rng.integers(0, top, size=(draws, blocks))
        all_rows = [[(s + k) % n for s in row for k in range(block)][:n] for row in starts]
    ratios = np.empty(draws)
    for d, rows in enumerate(all_rows):
        ratios[d] = np.std(low[rows], ddof=1) / np.std(spy[rows], ddof=1)
    return ratios


def test_bootstrap_matches_independent_oracle():
    low, spy = gpt_bootstrap_fixture()
    boot = crit.low_risk_test(low, spy)["bootstrap"]
    ratios = oracle_ratios(low.to_numpy(), spy.to_numpy())
    assert boot["p_vol"] == float(np.mean(ratios >= 1.0)) == 0.0099
    assert boot["upper_95"] == float(np.percentile(ratios, 95.0)) == 0.9882666976280164
    assert boot["upper_95"] != float(np.percentile(ratios, 90.0))           # not the 90th percentile
    for scheme in ("iid", "wrapped"):
        other = oracle_ratios(low.to_numpy(), spy.to_numpy(), scheme)
        assert (float(np.mean(other >= 1.0)), float(np.percentile(other, 95.0))) != (boot["p_vol"], boot["upper_95"])


def test_bootstrap_rows_are_unwrapped_blocks():
    n = 30
    rows = crit.bootstrap_rows(n)
    assert rows.shape == (10_000, n)
    starts = rows[:, ::12]
    assert starts.min() == 0 and starts.max() == n - 12            # starts 0 to n - 12, both ends reached
    for k in range(0, n, 12):
        block = rows[:, k:k + 12]
        assert (np.diff(block, axis=1) == 1).all()                  # consecutive months, no wrap
    assert rows.max() <= n - 1


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

LAG = int(np.floor(4.0 * (len(CONFIRM) / 100.0) ** (2.0 / 9.0)))


def centered(seed: int, scale: float, months: pd.PeriodIndex = CONFIRM) -> pd.Series:
    e = noise(months, seed, scale=scale)
    return e - e.mean()


def with_t(e: pd.Series, t: float) -> pd.Series:
    """Shift a centered series so its HAC t is ``t`` (the long-run variance ignores the shift)."""
    return e + t * math.sqrt(newey_west_long_run_variance(e.to_numpy(), LAG) / len(e))


def wired_inputs(t_spy: float = 4.0, t_cw: float = 4.5, t_ni: float = 4.0, a_spy: pd.Series | None = None,
                 a_cw: pd.Series | None = None, cost_2x_cw: float = 0.0, check_offset: float = 0.001,
                 check_low_scale: float = 0.8) -> tuple[dict, dict, dict]:
    """Primary inputs whose HAC t values (A against SPY and CW-PIT, B non-inferiority) are set exactly."""
    spy = noise(CONFIRM, 40, mean=0.006, scale=0.04)
    a_spy = with_t(centered(41, 0.005), t_spy) if a_spy is None else a_spy
    a_cw = with_t(centered(42, 0.005), t_cw) if a_cw is None else a_cw
    composite = spy + a_spy
    cw = composite - a_cw
    e = -0.2 * (spy - spy.mean()) + noise(CONFIRM, 43, scale=0.002)
    low = spy + with_t(e - e.mean(), t_ni) - crit.NI_MARGIN / 12
    confirm = {"composite": composite, "spy": spy, "cw": cw, "low_risk": low}
    confirm_2x = {"composite": composite - 0.0001 - cost_2x_cw, "cw": cw - 0.00002}
    check_spy = noise(CHECK, 50, mean=0.005, scale=0.04)
    check = {"composite": check_spy + check_offset, "spy": check_spy, "cw": check_spy - 0.0005,
             "low_risk": check_low_scale * check_spy + (1.0 - check_low_scale) * check_spy.mean() + 0.0005}
    return confirm, confirm_2x, check


FROZEN = crit.freeze_shortlist({"S1": record(0.5, 2.0), "S2": record(0.1, 0.5)})
EXPECTED = FROZEN["digest_sha256"]                   # saved at the original freeze
EMPTY = crit.freeze_shortlist({"S1": record(0.1, 2.0)})
EMPTY_DIGEST = EMPTY["digest_sha256"]


def failed(conditions: dict) -> list[str]:
    return sorted(k for k, v in conditions.items() if not v)


def decide(**kwargs) -> dict:
    return crit.primary_decision(FROZEN, EXPECTED, *wired_inputs(**kwargs))


def test_wired_inputs_set_the_hac_t():
    confirm, _, _ = wired_inputs(t_spy=1.75, t_cw=3.0, t_ni=0.5)
    a = crit.composite_test(confirm["composite"], confirm["spy"], confirm["cw"])
    b = crit.low_risk_test(confirm["low_risk"], confirm["spy"])
    assert (a["vs_spy"]["hac_t"], a["vs_cw"]["hac_t"], b["t_ni"]) == pytest.approx((1.75, 3.0, 0.5), abs=1e-9)
    assert b["bootstrap"]["p_vol"] == 0.0 and b["vol_ratio"] < 0.85


def test_primary_decision_all_conditions_pass():
    out = decide()
    a, b = out["test_a"], out["test_b"]
    assert a["run"] and a["passed"] and a["label"] == "met" and failed(a["conditions"]) == []
    assert b["passed"] and failed(b["conditions"]) == [] and out["stop"] is None
    assert (a["holm_p"], b["holm_p"]) == pytest.approx(tuple(crit.holm_primary(a["p_a"], b["p_b"]).values()))


def test_primary_decision_a_fails_only_after_holm():
    out = decide(t_spy=float(norm.isf(0.04)), t_cw=3.0, t_ni=float(norm.isf(0.31)))
    a = out["test_a"]
    assert a["p_a"] == pytest.approx(0.04) and a["p_a"] <= crit.ALPHA < a["holm_p"]
    assert failed(a["conditions"]) == ["holm_p_at_most_alpha"] and a["label"] == "positive_not_shown"
    assert out["stop"] is None


def test_primary_decision_b_fails_only_after_holm():
    out = decide(t_spy=float(norm.isf(0.31)), t_cw=3.0, t_ni=float(norm.isf(0.04)))
    b = out["test_b"]
    assert b["p_b"] == pytest.approx(0.04) and b["p_b"] <= crit.ALPHA < b["holm_p"]
    assert failed(b["conditions"]) == ["holm_p_at_most_alpha"]


def test_primary_decision_uses_the_2x_input():
    a = decide(cost_2x_cw=0.01)["test_a"]
    assert a["cost_2x"]["vs_cw"] < 0.0 < a["vs_cw"]["annual_mean"]
    assert failed(a["conditions"]) == ["cost_2x_means_positive"] and a["label"] == "not_met_robustness"


def test_primary_decision_uses_the_check_composite():
    a = decide(check_offset=-0.001)["test_a"]
    assert failed(a["conditions"]) == ["check_means_not_negative"] and a["label"] == "not_met_robustness"


def test_primary_decision_uses_the_b_check():
    out = decide(check_low_scale=1.05)
    assert out["test_b"]["check"]["vol_ratio"] == pytest.approx(1.05)
    assert failed(out["test_b"]["conditions"]) == ["check_vol_ratio_below_one"] and out["test_a"]["passed"]


def test_primary_decision_stop_uses_the_spy_mean():
    def means(seed: int, annual: float) -> pd.Series:
        return centered(seed, 0.0005) + annual / 12
    low_spy = decide(a_spy=means(41, 0.002), a_cw=means(42, 0.01))
    assert low_spy["test_a"]["vs_spy"]["annual_mean"] == pytest.approx(0.002)
    assert low_spy["stop"] == "confirm_below_floor"
    low_cw = decide(a_spy=means(41, 0.01), a_cw=means(42, 0.002))
    assert low_cw["test_a"]["vs_cw"]["annual_mean"] == pytest.approx(0.002) and low_cw["stop"] is None


def test_primary_decision_refuses_a_check_series_in_confirm_months():
    confirm, confirm_2x, check = wired_inputs()
    with stops("period_violation"):
        crit.primary_decision(FROZEN, EXPECTED, confirm, confirm_2x, {**check, "spy": confirm["spy"]})


def test_frozen_screen_binds_to_the_original_digest():
    confirm, confirm_2x, check = wired_inputs()
    # GPT regression: a changed shortlist with a correctly recomputed replacement digest.
    replaced = crit.freeze_shortlist({"S1": record(0.5, 2.0), "S2": record(0.5, 2.0)})
    assert replaced["shortlist"] == ["S1", "S2"] and crit.shortlist_digest(replaced) == replaced["digest_sha256"]
    with stops("shortlist_digest_mismatch"):
        crit.primary_decision(replaced, EXPECTED, confirm, confirm_2x, check)
    tampered = {**FROZEN, "candidates": {c: dict(r) for c, r in FROZEN["candidates"].items()}}
    tampered["candidates"]["S2"]["hac_t"] = 0.6
    for record_in, expected in ((tampered, EXPECTED), ({**FROZEN, "digest_sha256": "0" * 64}, EXPECTED),
                                (FROZEN, "0" * 64), (FROZEN, None), ({**EMPTY, "decision": "shortlist_frozen"},
                                                                     EMPTY_DIGEST)):
        with stops("shortlist_digest_mismatch"):
            crit.primary_decision(record_in, expected, confirm, confirm_2x, check)
    with stops("shortlist_digest_mismatch"):          # the gate runs before any input is read
        crit.primary_decision(tampered, EXPECTED, {}, {}, {})


def test_frozen_screen_rule_and_decision_checks():
    confirm, confirm_2x, check = wired_inputs()
    loose = {**FROZEN, "rule": {"ir_min": 0.0, "t_min": 0.0, "shortlist_cap": 99}}
    loose["digest_sha256"] = crit.shortlist_digest(loose)
    with stops("shortlist_rule_mismatch"):
        crit.primary_decision(loose, loose["digest_sha256"], confirm, confirm_2x, check)
    relabeled = {**EMPTY, "decision": "shortlist_frozen"}
    relabeled["digest_sha256"] = crit.shortlist_digest(relabeled)
    with stops("screen_record_invalid"):
        crit.primary_decision(relabeled, relabeled["digest_sha256"], confirm, confirm_2x, check)


def test_screen_empty_runs_b_only():
    confirm, _, check = wired_inputs(t_ni=float(norm.isf(0.02)))
    b_only = {"low_risk": confirm["low_risk"], "spy": confirm["spy"]}
    out = crit.primary_decision(EMPTY, EMPTY_DIGEST, b_only, {}, {"low_risk": check["low_risk"], "spy": check["spy"]})
    assert out["test_a"] == {"run": False, "refused": "screen_empty_confirm", "passed": False, "label": "not_run"}
    assert out["stop"] == "screen_empty"
    b = out["test_b"]
    assert b["p_b"] == pytest.approx(0.02) and b["holm_p"] == pytest.approx(min(1.0, 2.0 * b["p_b"]))
    assert b["holm_p"] == crit.holm_primary(1.0, b["p_b"])["B"] and b["passed"]


def secondary_entries(count: int = 3) -> dict:
    confirm, _, _ = wired_inputs()
    return {f"S{k}": {"composite": confirm["composite"] + noise(CONFIRM, 30 + k, scale=0.002),
                      "spy": confirm["spy"], "cw": confirm["cw"]} for k in range(count)}


def test_secondary_family_by_q_values_and_family_size():
    entries = secondary_entries()
    out = crit.secondary_family(FROZEN, EXPECTED, entries, family_size=3)
    p = pd.Series({k: v["p_a"] for k, v in out["members"].items()})
    assert [out["members"][k]["q_by"] for k in p.index] == adjust_pvalues(p, method="by").tolist()
    assert out["decides_nothing"] is True and "decides nothing" in out["note"] and out["family_size"] == 3
    wider = crit.secondary_family(FROZEN, EXPECTED, entries, family_size=9)    # a refused member keeps its slot
    q9 = adjust_pvalues(p, method="by", family_size=9)
    assert [wider["members"][k]["q_by"] for k in p.index] == q9.tolist()
    assert all(wider["members"][k]["q_by"] >= out["members"][k]["q_by"] for k in p.index)
    assert any(wider["members"][k]["q_by"] > out["members"][k]["q_by"] for k in p.index)
    with stops("family_size_invalid"):
        crit.secondary_family(FROZEN, EXPECTED, entries, family_size=2)


def test_secondary_family_gate():
    entries = secondary_entries(1)
    with stops("screen_empty_confirm"):               # no entry is read after screen_empty
        crit.secondary_family(EMPTY, EMPTY_DIGEST, {}, family_size=3)
    with stops("screen_empty_confirm"):
        crit.secondary_family(EMPTY, EMPTY_DIGEST, entries, family_size=3)
    replaced = crit.freeze_shortlist({"S1": record(0.5, 2.0), "S2": record(0.5, 2.0)})
    with stops("shortlist_digest_mismatch"):
        crit.secondary_family(replaced, EXPECTED, entries, family_size=3)


# Screen costs ---------------------------------------------------------------------------

def test_screen_cost_schedule_switches():
    dates = pd.DatetimeIndex(["1963-07-31", "1975-04-30", "1975-05-01", "1992-12-31", "1993-01-01", "2001-03-30",
                              "2001-04-02", "2006-12-29", "2007-01-02"])
    for case, scale in COST_SCALES.items():
        frame = dated_cost_frame(dates, crit.SCREEN_COST_SCHEDULE, scale)
        expected = np.array([[30, 30], [30, 30], [10, 30], [10, 30], [5, 20], [5, 20], [2, 8], [2, 8], [1, 4]])
        assert frame.to_numpy() == pytest.approx(expected * scale), case


# Declared blank months (R6, card m55-critmask) ------------------------------------------

def blank(*months: str) -> dict:
    return {pd.Period(m, "M"): "path_break_held" for m in months}


def without(series: pd.Series, months: dict) -> pd.Series:
    return series.drop(list(months))


def screen_pair(seed: int = 60, months: pd.PeriodIndex = SCREEN) -> tuple[pd.Series, pd.Series]:
    cw = noise(months, seed)
    return cw + noise(months, seed + 1, mean=0.002, scale=0.004), cw


def test_blank_reasons_and_declaration_checks():
    assert crit.BLANK_REASONS == ("path_break_held",)
    net, cw = screen_pair()
    for bad in ({pd.Period("1975-03", "M"): "halt"}, {pd.Period("1975-03", "M"): None}, {"1975-03": "path_break_held"},
                {pd.Period("1975-03-02", "D"): "path_break_held"}, [pd.Period("1975-03", "M")]):
        with stops("blank_invalid"):
            crit.check_series(net, "x", "screen", bad)
        with stops("blank_invalid"):
            crit.screen_record(net, cw, blank_months=bad)
    assert crit.check_blank(None) == {} and list(crit.check_blank(blank("1980-01", "1975-03"))) == [
        pd.Period("1975-03", "M"), pd.Period("1980-01", "M")]


def test_no_blank_month_gives_the_same_outputs():
    """Card criterion 4: with no declared month the records have the e8135bc keys and values.

    The keys and values below were computed with the e8135bc module. The HAC t uses ``np.dot``, whose last bit can
    differ between BLAS builds, so values are pinned at 1e-12; an omitted, ``None``, or empty declaration agree exactly.
    """
    net, cw = screen_pair()
    base = crit.screen_record(net, cw, 0.4)
    assert sorted(base) == ["annual_active_mean", "annual_te", "annual_turnover", "first_month", "hac_t",
                            "information_ratio", "last_month", "months", "p_one_sided", "status"]
    assert (base["status"], base["months"], base["first_month"], base["last_month"]) == (
        "ok", 354, "1963-07", "1992-12")
    assert [base[k] for k in ("annual_active_mean", "annual_te", "information_ratio", "hac_t")] == pytest.approx(
        [0.02303763161890473, 0.014154880397759695, 1.6275398287753047, 10.001342216649235], rel=1e-12)
    for empty in (None, {}):
        assert crit.screen_record(net, cw, 0.4, empty) == base
        assert_series_equal(crit.check_series(net, "x", "screen", empty), crit.check_series(net, "x", "screen"))
    candidates = {"S1": {"net": net, "cw_net": cw}, "S2": {"net": cw + noise(SCREEN, 62, scale=0.004), "cw_net": cw}}
    digest = crit.screen(candidates)["digest_sha256"]
    assert crit.screen({c: {**v, "blank_months": {}} for c, v in candidates.items()})["digest_sha256"] == digest
    confirm, confirm_2x, check = wired_inputs()
    out = crit.primary_decision(FROZEN, EXPECTED, confirm, confirm_2x, check)
    assert crit.primary_decision(FROZEN, EXPECTED, confirm, confirm_2x, check, {}, {}) == out
    assert [sorted(out), sorted(out["test_a"]["check"]), sorted(out["test_b"]["check"])] == [
        ["stop", "test_a", "test_b"], ["vs_cw", "vs_spy"], ["annual_gap", "vol_ratio"]]
    assert sorted(out["test_a"]) == ["check", "conditions", "cost_2x", "holm_p", "label", "p_a", "passed", "run",
                                     "vs_cw", "vs_spy"]
    assert sorted(out["test_b"]) == ["annual_gap", "bootstrap", "check", "conditions", "drawdown_ratio", "holm_p",
                                     "label", "largest_drawdowns", "p_b", "p_ni", "passed", "t_ni", "vol_ratio"]
    assert (out["test_a"]["p_a"], out["test_b"]["vol_ratio"]) == pytest.approx((3.167124183311986e-05,
                                                                                0.8007754135286231), rel=1e-12)
    assert "blank_months" not in crit.canonical_json(out)
    entries = secondary_entries()
    family = crit.secondary_family(FROZEN, EXPECTED, entries, 3)
    assert crit.secondary_family(FROZEN, EXPECTED, entries, 3, {}) == family


def test_blank_month_is_left_out_of_the_screen_statistics():
    net, cw = screen_pair()
    months = blank("1975-03", "1992-12")              # an inner month and the last screen month
    out = crit.screen_record(without(net, months), without(cw, months), 0.4, months)
    active = without(net - cw, months)
    joined = SCREEN[-len(active):]                    # the same values on months with no gap
    reference = crit.screen_record(net.drop(list(months)).set_axis(joined), cw.drop(list(months)).set_axis(joined), 0.4)
    moved = ("first_month", "last_month", "blank_months", "blank_reason_counts")
    assert {k: v for k, v in out.items() if k not in moved} == {k: v for k, v in reference.items() if k not in moved}
    assert (out["months"], out["first_month"], out["last_month"]) == (len(SCREEN) - 2, "1963-07", "1992-11")
    assert out["blank_months"] == {"1975-03": "path_break_held", "1992-12": "path_break_held"}
    assert out["blank_reason_counts"] == {"path_break_held": 2}
    assert out["annual_active_mean"] == pytest.approx(12 * float(active.mean()), rel=1e-12)
    assert out["hac_t"] == newey_west_mean_tstat(active)          # the months on each side are adjacent
    zero_filled = (net - cw).where(~(net - cw).index.isin(list(months)), 0.0)
    assert out["hac_t"] != newey_west_mean_tstat(zero_filled)    # not a zero fill


def test_minimum_month_rules_count_months_with_values():
    net, cw = screen_pair(months=SCREEN[-37:])
    inner = blank(str(SCREEN[-20]))
    assert crit.screen_record(without(net, inner), without(cw, inner), blank_months=inner)["months"] == 36
    for months in (blank(str(SCREEN[-20])), blank(str(SCREEN[-36]))):     # an inner and a first month
        short_net, short_cw = net.iloc[1:], cw.iloc[1:]
        with stops("screen_too_short"):
            crit.screen_record(without(short_net, months), without(short_cw, months), blank_months=months)
    spy = noise(CONFIRM, 70, scale=0.04)
    low = 0.8 * spy + noise(CONFIRM, 71, scale=0.01)
    for kept, reason in ((11, "bootstrap_too_short"), (12, None)):
        months = {m: "path_break_held" for m in CONFIRM[kept:]}
        if reason:
            with stops(reason):
                crit.low_risk_test(low.iloc[:kept], spy.iloc[:kept], months)
        else:
            assert crit.low_risk_test(low.iloc[:kept], spy.iloc[:kept], months)["bootstrap"]["draws"] == 10_000


def test_blank_month_is_left_out_of_the_confirm_statistics():
    spy = noise(CONFIRM, 72, scale=0.04)
    low = 0.8 * spy + noise(CONFIRM, 73, mean=0.0005, scale=0.01)
    months = blank("1993-02", "2001-06")              # the first confirm month and an inner month
    out = crit.low_risk_test(without(low, months), without(spy, months), months)
    lo, sp = without(low, months), without(spy, months)
    assert out["annual_gap"] == crit.annual_mean(lo - sp)
    assert out["t_ni"] == newey_west_mean_tstat(lo - sp + crit.NI_MARGIN / 12)
    assert out["vol_ratio"] == crit.annual_vol(lo) / crit.annual_vol(sp)
    assert out["bootstrap"] == crit.bootstrap_vol_ratio(lo.to_numpy(), sp.to_numpy())    # 252 months, joined blocks
    assert out["bootstrap"] != crit.bootstrap_vol_ratio(low.to_numpy(), spy.to_numpy())
    assert out["largest_drawdowns"] == {"low_risk": crit.drawdown_episodes(lo)[:3],
                                        "spy": crit.drawdown_episodes(sp)[:3]}
    assert out["blank_months"] == {"1993-02": "path_break_held", "2001-06": "path_break_held"}
    composite, cw = spy + noise(CONFIRM, 74, mean=0.001, scale=0.004), spy + noise(CONFIRM, 75, scale=0.003)
    a = crit.composite_test(without(composite, months), sp, without(cw, months), months)
    assert a["vs_cw"]["months"] == 252
    assert a["vs_spy"]["hac_t"] == newey_west_mean_tstat(without(composite, months) - sp)
    assert a["blank_reason_counts"] == {"path_break_held": 2}


def test_drawdown_path_joins_a_blank_month():
    months = pd.period_range("2000-01", "2000-04", freq="M")
    returns = pd.Series([0.1, np.nan, -0.1, 0.2], index=months)         # 2000-02 is blank
    episodes = crit.drawdown_episodes(returns.drop(months[1]))
    assert [(e["peak_month"], e["trough_month"], e["recovery_month"]) for e in episodes] == [
        ("2000-01", "2000-03", "2000-04")]                              # no point falls on 2000-02
    assert episodes[0]["depth"] == pytest.approx(-0.1)
    zero_filled = crit.drawdown_episodes(returns.fillna(0.0))
    assert zero_filled[0]["peak_month"] == "2000-02"                    # a zero fill would put a peak on it


def test_undeclared_gap_refuses():
    net, cw = screen_pair()
    months = blank("1975-03")
    for declared in (None, {}):
        with stops("month_missing"):
            crit.screen_record(without(net, months), without(cw, months), blank_months=declared)
    two = blank("1975-03", "1975-04")
    for declared in (months, blank("1975-04")):                         # only one of the two left-out months declared
        with stops("month_missing"):
            crit.screen_record(without(net, two), without(cw, two), blank_months=declared)
    with stops("month_missing"):                                        # a declared month away from the rows
        crit.check_series(net.iloc[-100:], "x", "screen", blank("1970-01"))


def test_declared_month_with_a_row_refuses():
    net, cw = screen_pair()
    months = blank("1975-03")
    for value in (0.01, np.nan, np.inf):                                # a value, or a NaN row: no fill, no drop
        with_row = net.copy()
        with_row[pd.Period("1975-03", "M")] = value
        saved = with_row.copy()
        with stops("blank_month_has_row"):
            crit.screen_record(with_row, without(cw, months), blank_months=months)
        assert_series_equal(with_row, saved)
    spy = noise(CONFIRM, 76)
    with stops("blank_month_has_row"):
        crit.low_risk_test(without(spy, blank("2000-01")), spy, blank("2000-01"))
    for month in ("2014-04", "2015-06", "2025-12"):                     # check period, a row at each declared month
        with stops("blank_month_has_row"):
            crit.low_risk_check(noise(CHECK, 79), noise(CHECK, 80), blank(month))


def test_pair_must_blank_the_same_months():
    net, cw = screen_pair()
    a, b = blank("1975-03"), blank("1975-04")
    with stops("blank_month_has_row"):                                  # the CW book keeps a row the candidate blanks
        crit.screen_record(without(net, a), cw, blank_months=a)
    with stops("month_missing"):
        crit.screen_record(without(net, a), cw)
    with stops("blank_month_has_row"):                                  # each book blanks a different month
        crit.screen_record(without(net, a), without(cw, b), blank_months={**a, **b})
    with stops("blank_month_has_row"):
        crit.screen({"S1": {"net": without(net, a), "cw_net": cw, "blank_months": a}})
    confirm, confirm_2x, check = wired_inputs()
    m = blank("2000-01")
    with stops("blank_month_has_row"):                                  # SPY keeps the row
        crit.composite_test(without(confirm["composite"], m), confirm["spy"], without(confirm["cw"], m), m)


def test_period_rules_with_blank_months():
    net, cw = screen_pair()
    with stops("period_violation"):                                     # a declared month after the screen
        crit.check_series(net, "x", "screen", blank("1993-01"))
    with stops("period_violation"):
        crit.check_series(net, "x", "screen", blank("1963-06"))
    confirm = noise(CONFIRM, 77)
    with stops("period_violation"):
        crit.check_series(confirm, "x", "confirm", blank("1993-01"))
    assert len(crit.check_series(without(confirm, blank("2014-03")), "x", "confirm", blank("2014-03"))) == 253
    check = noise(CHECK, 78)
    for month in ("2019-07", "2021-08"):                                # the check gap stays the only gap
        with stops("seal_month"):
            crit.check_series(check, "x", "check", blank(month))
    for month in ("2014-04", "2019-06", "2021-09", "2025-12"):
        assert len(crit.check_series(without(check, blank(month)), "x", "check", blank(month))) == len(CHECK) - 1


def test_digest_covers_the_blank_months():
    net, cw = screen_pair()
    def frozen(months: dict) -> dict:
        return crit.screen({"S1": {"net": without(net, months), "cw_net": without(cw, months), "blank_months": months}})
    first, moved, more = frozen(blank("1975-03")), frozen(blank("1975-04")), frozen(blank("1975-03", "1980-01"))
    assert len({first["digest_sha256"], moved["digest_sha256"], more["digest_sha256"],
                crit.screen({"S1": {"net": net, "cw_net": cw}})["digest_sha256"]}) == 4
    s1 = first["candidates"]["S1"]
    tampered = {**first, "candidates": {"S1": {**s1, "blank_months": {"1975-04": "path_break_held"}}}}
    assert crit.shortlist_digest(tampered) != first["digest_sha256"]   # only the listed blank month changed
    recount = {**first, "candidates": {"S1": {**s1, "blank_reason_counts": {"path_break_held": 2}}}}
    assert crit.shortlist_digest(recount) != first["digest_sha256"]
    assert crit.verify_frozen_screen(first, first["digest_sha256"]) == bool(first["shortlist"])
    with stops("shortlist_digest_mismatch"):
        crit.verify_frozen_screen({**tampered, "digest_sha256": crit.shortlist_digest(tampered)},
                                  first["digest_sha256"])


def test_primary_decision_with_blank_months():
    confirm, confirm_2x, check = wired_inputs()
    cm, km = blank("2000-01"), blank("2015-06")
    c, c2, k = ({name: without(s, months) for name, s in group.items()}
                for group, months in ((confirm, cm), (confirm_2x, cm), (check, km)))
    out = crit.primary_decision(FROZEN, EXPECTED, c, c2, k, cm, km)
    a, b = out["test_a"], out["test_b"]
    direct = crit.composite_test(c["composite"], c["spy"], c["cw"], cm)
    assert a["p_a"] == direct["p_a"] and a["vs_spy"] == direct["vs_spy"] and a["vs_spy"]["months"] == 253
    assert a["blank_months"] == b["blank_months"] == a["cost_2x"]["blank_months"] == {"2000-01": "path_break_held"}
    assert a["check"]["blank_months"] == b["check"]["blank_months"] == {"2015-06": "path_break_held"}
    assert b["bootstrap"] == crit.low_risk_test(c["low_risk"], c["spy"], cm)["bootstrap"]
    assert b["check"]["vol_ratio"] == crit.low_risk_check(k["low_risk"], k["spy"], km)["vol_ratio"]
    with stops("month_missing"):                                        # the confirm months are declared, not the check
        crit.primary_decision(FROZEN, EXPECTED, c, c2, k, cm)
    with stops("blank_month_has_row"):                                  # the 2x books share SPY and the declaration
        crit.primary_decision(FROZEN, EXPECTED, c, confirm_2x, k, cm, km)
    entries = {name: {key: without(s, cm) for key, s in e.items()} for name, e in secondary_entries(2).items()}
    family = crit.secondary_family(FROZEN, EXPECTED, entries, 2, cm)
    assert all(member["blank_months"] == {"2000-01": "path_break_held"} for member in family["members"].values())
