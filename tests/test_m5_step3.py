"""Milestone 5 step 3: R2, R3, R4, the S3 tests, the random-date null, and the closure rule.

Synthetic fixtures only; no network access and no provider file. The names in
the section comments follow amendment 3 ``required_tests`` and the step 3
reporting conventions in ``docs/decision_log.md``.
"""

from __future__ import annotations

import json
import math
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data.public_factors import MISSING_ABSENT, MISSING_BLANK, MISSING_CODE, PRESENT, PublicDataRefusal
from features.multiple_testing import return_test_statistics
from research import m5_factor_baseline as base
from research import m5_step3 as s3


CLASSES = ["Accruals", "Debt Issuance", "Investment", "Low Leverage", "Low Risk", "Momentum", "Profit Growth",
           "Profitability", "Quality", "Seasonality", "Short-Term Reversal", "Size", "Value"]
COSTS = [20, 50]
FEW_DRAWS = 49


def trial_like() -> dict:
    return {"evaluation_window": {"first_evaluated_month": "1975-01",
                                  "halves": {"first": ["1975-01", "1979-12"],
                                             "second": ["1980-01", "last_evaluated_month"]}},
            "traits": {"years_since_publication": {"missing_publication_year": ["size_1"]},
                       "data_source": {"composite": [], "market": []}},
            "costs": {"switch_cost_bps": {"primary": 20, "sensitivity": 50}}}


def make_data(seed: int = 3) -> s3.Step3Data:
    """13 classes x 2 factors, returns 1950-1985 with class means of both signs that move with a volatility regime.

    momentum_1 is absent 1973-12..1974-11, so it is a set member without a
    trailing return in 1975 and its class return is typed missing in those
    lookback months. size_1 has no publication year; value_0 and value_1 are
    published in 1980, so Value has no post-publication member before 1981-03.
    """

    rng = np.random.default_rng(seed)
    index = pd.period_range("1950-01", "1985-12", freq="M")
    names = [f"{s3.slug(name)}_{j}" for name in CLASSES for j in (0, 1)]
    regime = np.asarray([(month.year // 3) % 2 for month in index], dtype=float)
    base_mean = np.array([0.004 if k % 3 else -0.003 for k in range(len(CLASSES))])
    swing = np.array([0.01 if k % 4 == 0 else 0.0 for k in range(len(CLASSES))])
    class_mean = base_mean[None, :] + swing[None, :] * (regime[:, None] - 0.5)
    values = np.repeat(class_mean, 2, axis=1) + rng.normal(0.0, 0.02, size=(len(index), len(names)))
    returns = pd.DataFrame(values, index=index, columns=names)
    returns.loc[:"1956-12", "accruals_1"] = np.nan
    returns.loc["1973-12":"1974-11", "momentum_1"] = np.nan
    missing = pd.DataFrame(PRESENT, index=index, columns=names, dtype=object)
    missing[returns.isna()] = MISSING_ABSENT
    classes = pd.Series({f"{s3.slug(name)}_{j}": name for name in CLASSES for j in (0, 1)})
    sources = pd.Series({name: s3.DATA_SOURCES[i % 3] for i, name in enumerate(names)})
    years: dict[str, int | None] = {name: (1974 if name.endswith("_0") else 1980) for name in names}
    years.update({"size_1": None, "value_0": 1980, "momentum_1": 1973, "quality_1": 1979})
    market_index = pd.period_range("1945-01", "1985-12", freq="M")
    market = pd.DataFrame({"Mkt-RF": rng.normal(0.006, 0.045, len(market_index)), "RF": 0.003}, index=market_index)
    days = pd.bdate_range("1948-01-01", "1985-12-31")
    scale = np.where((days.year // 3) % 2 == 0, 0.008, 0.015)
    daily = pd.Series(rng.normal(0.0003, 1.0, len(days)) * scale, index=days)
    credit_index = pd.period_range("1940-01", "1985-12", freq="M")
    aaa = 4 + np.cumsum(rng.normal(0, 0.05, len(credit_index)))
    credit = pd.DataFrame({"BAA": aaa + 1 + 0.5 * np.sin(np.arange(len(credit_index)) / 9)
                           + rng.normal(0, 0.05, len(credit_index)), "AAA": aaa}, index=credit_index)
    return s3.Step3Data(returns=returns, missing=missing, classes=classes, data_source=sources,
                        publication_years=years, market_monthly=market, market_daily=daily, credit=credit,
                        first=pd.Period("1975-01", freq="M"), last=pd.Period("1985-12", freq="M"))


def replace(data: s3.Step3Data, **changes) -> s3.Step3Data:
    fields = {name: getattr(data, name) for name in data.__dataclass_fields__}
    fields.update(changes)
    return s3.Step3Data(**fields)


@pytest.fixture(scope="module")
def fixture_data() -> s3.Step3Data:
    return make_data()


@pytest.fixture(scope="module")
def built(fixture_data: s3.Step3Data) -> dict:
    return s3.build_rules(fixture_data, trial_like())


@pytest.fixture(scope="module")
def evaluated(fixture_data: s3.Step3Data) -> dict:
    return s3.evaluate(fixture_data, trial_like(), COSTS, draws=FEW_DRAWS)


def month(value: str) -> pd.Period:
    return pd.Period(value, freq="M")


# future_perturbation --------------------------------------------------------------

def _decision_state(built: dict, t: pd.Period) -> dict:
    r2 = built["r2"]
    row = list(built["months"]).index(t)
    fit = built["fits"][t.year]
    return {
        "labels": built["labels"].loc[t],
        "means": r2["means"][row], "lambdas": r2["lambdas"].loc[t], "episodes": r2["episodes"].loc[t],
        "weights": {rule: frame.loc[:t] for rule, frame in built["weights"].items()},
        "fit_status": fit["status"], "coefficients": fit.get("coefficients"),
        "forecast": built["forecast"].loc[t],
    }


def _assert_same_state(before: dict, after: dict) -> None:
    pd.testing.assert_series_equal(before["labels"], after["labels"])
    np.testing.assert_array_equal(before["means"], after["means"])
    pd.testing.assert_series_equal(before["lambdas"], after["lambdas"])
    pd.testing.assert_series_equal(before["episodes"], after["episodes"])
    for rule in before["weights"]:
        pd.testing.assert_frame_equal(before["weights"][rule], after["weights"][rule])
    assert before["fit_status"] == after["fit_status"]
    assert before["coefficients"] == after["coefficients"]
    pd.testing.assert_series_equal(before["forecast"], after["forecast"])


@pytest.mark.parametrize("t", ["1980-01", "1983-06"])
def test_future_perturbation_leaves_month_t_labels_histories_weights_and_r4_unchanged(
        fixture_data: s3.Step3Data, built: dict, t: str) -> None:
    t = month(t)
    assert built["fits"][t.year]["status"] == "fit"
    before = _decision_state(built, t)
    rng = np.random.default_rng(5)
    returns = fixture_data.returns.copy()
    future = returns.index >= t - 1
    returns.loc[future] = returns.loc[future] + rng.normal(0.0, 0.05, size=returns.loc[future].shape)
    returns.loc[t - 1, "quality_0"] = np.nan
    returns.loc[t, "low_risk_1"] = np.nan
    missing = fixture_data.missing.copy()
    missing[returns.isna()] = MISSING_ABSENT
    last_day = fixture_data.market_daily.index[fixture_data.market_daily.index.to_period("M") == t - 2].max()
    daily = fixture_data.market_daily.copy()
    daily[daily.index > last_day] += rng.normal(0.0, 0.02, int((daily.index > last_day).sum()))
    market = fixture_data.market_monthly.copy()
    market.loc[market.index > t - 2, "Mkt-RF"] += 0.3
    credit = fixture_data.credit.copy()
    credit.loc[credit.index > t - 3, "BAA"] += 5.0
    perturbed = replace(fixture_data, returns=returns, missing=missing, market_daily=daily,
                        market_monthly=market, credit=credit)
    _assert_same_state(before, _decision_state(s3.build_rules(perturbed, trial_like()), t))


def test_a_signal_month_return_can_change_month_t(fixture_data: s3.Step3Data, built: dict) -> None:
    t = month("1983-06")
    returns = fixture_data.returns.copy()
    returns.loc[t - 2, "quality_0"] += 0.2
    after = s3.build_rules(replace(fixture_data, returns=returns), trial_like())
    for rule in ("R1", "R3"):
        assert after["weights"][rule].loc[t, "quality_0"] != pytest.approx(built["weights"][rule].loc[t, "quality_0"])
    assert not np.allclose(after["r2"]["means"][list(after["months"]).index(t)],
                           built["r2"]["means"][list(built["months"]).index(t)], equal_nan=True)


# r4_publication_year_weight_level ---------------------------------------------------

def test_r4_publication_year_change_at_or_after_signal_year_leaves_every_r4_quantity_unchanged(
        fixture_data: s3.Step3Data, built: dict) -> None:
    t = month("1980-02")  # signal month 1979-12; quality_1 is published in 1979
    assert fixture_data.publication_years["quality_1"] == 1979
    later = replace(fixture_data, publication_years={**fixture_data.publication_years, "quality_1": 1983})
    after = s3.build_rules(later, trial_like())
    design_before, design_after = built["design"], after["design"]
    rows_before, rows_after = design_before.months <= t, design_after.months <= t
    np.testing.assert_array_equal(design_before.features[np.asarray(rows_before)],
                                  design_after.features[np.asarray(rows_after)])
    np.testing.assert_array_equal(design_before.target[np.asarray(rows_before)],
                                  design_after.target[np.asarray(rows_after)])
    pd.testing.assert_frame_equal(design_before.covered.loc[:t], design_after.covered.loc[:t])
    for year in range(1975, t.year + 1):
        assert built["fits"][year].get("coefficients") == after["fits"][year].get("coefficients")
    pd.testing.assert_frame_equal(built["forecast"].loc[:t], after["forecast"].loc[:t])
    pd.testing.assert_frame_equal(built["weights"]["R4"].loc[:t], after["weights"]["R4"].loc[:t])


# r4_uncovered_keeps_r1 -----------------------------------------------------------------

def test_r4_uncovered_factor_months_keep_their_exact_r1_weight(fixture_data: s3.Step3Data, built: dict) -> None:
    w1, w4 = built["weights"]["R1"], built["weights"]["R4"]
    forecast = built["forecast"].loc[w1.index]
    uncovered = forecast.isna() & built["in_set"].loc[w1.index]
    assert uncovered.to_numpy().sum() > 0
    np.testing.assert_array_equal(w4.to_numpy()[uncovered.to_numpy()], w1.to_numpy()[uncovered.to_numpy()])
    # Each reason appears: no publication year, not yet published, missing trailing return, pre-first-fit.
    assert (w4["size_1"] == w1["size_1"]).all()
    assert (w4.loc["1975-01":"1981-02", "value_0"] == w1.loc["1975-01":"1981-02", "value_0"]).all()
    assert built["trailing"].loc["1975-06", "momentum_1"] != built["trailing"].loc["1975-06", "momentum_1"]
    assert w4.loc["1975-06", "momentum_1"] == w1.loc["1975-06", "momentum_1"]
    assert built["fits"][1978]["status"] == "too_few_training_months"
    pd.testing.assert_frame_equal(w4.loc[:"1978-12"], w1.loc[:"1978-12"])
    block_total = w1.where(forecast.notna(), 0.0).sum(axis=1)
    np.testing.assert_allclose(w4.where(forecast.notna(), 0.0).sum(axis=1), block_total, atol=1e-15)
    np.testing.assert_allclose(w4.sum(axis=1), 1.0, atol=1e-15)


def test_r4_with_fewer_than_two_forecasts_equals_r1() -> None:
    w1 = pd.DataFrame([[0.2, 0.3, 0.5], [0.2, 0.3, 0.5]], index=pd.period_range("1990-01", periods=2, freq="M"),
                      columns=["a", "b", "c"])
    forecast = pd.DataFrame([[0.1, np.nan, np.nan], [0.1, -0.2, 0.3]], index=w1.index, columns=w1.columns)
    w4 = s3.r4_weights(w1, forecast)
    pd.testing.assert_series_equal(w4.iloc[0], w1.iloc[0])
    multipliers = np.array([1.0, 0.5, 1.5])  # z = 0, -1, 1 from ranks 2, 1, 3
    expected = w1.iloc[1].to_numpy() * multipliers / (w1.iloc[1].to_numpy() @ multipliers)
    np.testing.assert_allclose(w4.iloc[1].to_numpy(), expected)


# r4_refit_boundary -----------------------------------------------------------------------

def test_r4_refit_uses_no_pair_after_november_and_ignores_december_changes(
        fixture_data: s3.Step3Data, built: dict) -> None:
    year = 1982
    fit = built["fits"][year]
    design = built["design"]
    train = np.asarray(design.months <= month(f"{year - 1}-11"))
    assert fit["training_rows"] == int(train.sum())
    assert fit["last_training_month"] == f"{year - 1}-11"
    returns = fixture_data.returns.copy()
    returns.loc[month(f"{year - 1}-12"):] += 0.1
    after = s3.build_rules(replace(fixture_data, returns=returns), trial_like())
    assert after["fits"][year]["coefficients"] == fit["coefficients"]
    november = fixture_data.returns.copy()
    november.loc[month(f"{year - 1}-11")] += 0.1
    moved = s3.build_rules(replace(fixture_data, returns=november), trial_like())
    assert moved["fits"][year]["coefficients"] != fit["coefficients"]


# r4_shared_state_column --------------------------------------------------------------------

def test_r4_state_columns_shared_by_every_factor_stay_finite_and_every_covered_pair_reaches_the_fit(
        built: dict) -> None:
    design = built["design"]
    names = design.names
    state_columns = [names.index(f"state={state}") for state in s3.STATES]
    assert np.isfinite(design.features).all()
    assert len(design.target) == int(design.covered.to_numpy().sum())
    for t in pd.unique(design.months):
        rows = np.asarray(design.months == t)
        block = design.features[rows][:, state_columns]
        assert (block == block[0]).all() and set(np.unique(block)) <= {-0.5, 0.5}
    for year, fit in built["fits"].items():
        cutoff = month(f"{year - 1}-11")
        assert fit["training_rows"] == int(design.covered.loc[:cutoff].to_numpy().sum())


# r2_hand_computed -------------------------------------------------------------------------------

def test_r2_multipliers_and_weights_match_a_hand_calculation() -> None:
    labels = np.array([[1, 0, 1], [1, 0, 0], [0, 0, 1], [0, 0, 0], [1, 0, 1], [0, 0, 0], [1, 0, 1], [1, 0, 0]],
                      dtype=float)
    values = np.array([[0.01, -0.01, 0.0], [0.02, -0.02, 0.0], [-0.03, 0.05, 0.0], [np.nan, 0.01, 0.0],
                       [0.04, 0.0, 0.0], [0.01, np.nan, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
    tilt = s3.r2_tilt(values, labels, np.array([0, 1, 2, 6]))
    np.testing.assert_array_equal(tilt["multipliers"][:2], 1.0)  # no history u <= t - 2
    np.testing.assert_array_equal(tilt["lambdas"][:2], 0.0)
    # Position 2: history is position 0 only. State 0 is in cell 0 with no past month of that cell.
    np.testing.assert_allclose(tilt["lambdas"][2], [0.0, 1 / 11, 1 / 11])
    np.testing.assert_allclose(tilt["multipliers"][2], [1 + 0.5 * (2 / 11) / 3, 1 - 0.5 * (2 / 11) / 3, 1.0])
    # Position 6: history positions 0..4; state 0 cell 1 has runs at 0-1 and 4 (E = 2), state 1 one run of
    # cell 0 (E = 1), state 2 cell 1 runs at 0, 2, 4 (E = 3). Class A means: +, +, +; class B: -, +, +;
    # class C has a zero mean everywhere, so sign(0) = 0 and its multiplier is 1.
    lam = np.array([2 / 12, 1 / 11, 3 / 13])
    np.testing.assert_allclose(tilt["lambdas"][3], lam)
    np.testing.assert_array_equal(tilt["episodes"][3], [2, 1, 3])
    np.testing.assert_allclose(tilt["means"][3, 0], [0.07 / 3, 0.01, 0.02 / 3])
    np.testing.assert_allclose(tilt["means"][3, 1], [-0.01, 0.03 / 5, 0.04 / 3])
    expected = np.array([1 + 0.5 * lam.sum() / 3, 1 + 0.5 * (-lam[0] + lam[1] + lam[2]) / 3, 1.0])
    np.testing.assert_allclose(tilt["multipliers"][3], expected)
    assert ((tilt["multipliers"] >= 0.5) & (tilt["multipliers"] <= 1.5)).all()
    index = pd.period_range("1990-01", periods=1, freq="M")
    w1 = pd.DataFrame([[0.1, 0.2, 0.3, 0.4]], index=index, columns=["a1", "a2", "b1", "c1"])
    classes = pd.Series({"a1": "A", "a2": "A", "b1": "B", "c1": "C"})
    multipliers = pd.DataFrame([expected], index=index, columns=["A", "B", "C"])
    w2 = s3.r2_weights(w1, w1 > 0, multipliers, classes)
    raw = w1.to_numpy()[0] * expected[[0, 0, 1, 2]]
    np.testing.assert_allclose(w2.to_numpy()[0], raw / raw.sum())
    assert w2.to_numpy().sum() == pytest.approx(1.0) and (w2.to_numpy() > 0).all()


def test_r2_empty_cell_history_contributes_zero() -> None:
    labels = np.array([[1, 1, 1], [1, 1, 1], [0, 1, 1]], dtype=float)
    values = np.array([[0.01], [0.02], [0.03]])
    tilt = s3.r2_tilt(values, labels, np.array([2]))
    # State 0 is in cell 0, which has no month at position 0: lambda 0 and no contribution.
    np.testing.assert_allclose(tilt["lambdas"][0], [0.0, 1 / 11, 1 / 11])
    np.testing.assert_allclose(tilt["multipliers"][0], [1 + 0.5 * (2 / 11) / 3])


# r3_hand_computed -------------------------------------------------------------------------------

def test_r3_sign_tilt_keeps_r1_weight_without_a_signal_and_preserves_the_block_total() -> None:
    index = pd.period_range("1990-01", periods=1, freq="M")
    w1 = pd.DataFrame([[0.1, 0.2, 0.3, 0.4]], index=index, columns=list("abcd"))
    trailing = pd.DataFrame([[0.05, -0.02, np.nan, 0.0]], index=index, columns=list("abcd"))
    w3 = s3.r3_weights(w1, w1 > 0, trailing)
    scale = 0.7 / 0.65
    np.testing.assert_allclose(w3.to_numpy()[0], [0.15 * scale, 0.1 * scale, 0.3, 0.4 * scale])
    assert w3.loc[index[0], "c"] == 0.3
    assert w3.to_numpy().sum() == pytest.approx(1.0)


def test_trailing_return_uses_months_t13_to_t2_and_needs_all_twelve() -> None:
    index = pd.period_range("1990-01", "1991-06", freq="M")
    returns = pd.DataFrame({"a": 0.01, "b": 0.01}, index=index)
    returns.loc["1990-03", "b"] = np.nan
    t = month("1991-03")  # window 1990-02 .. 1991-01
    trailing = s3.trailing_return(returns, pd.PeriodIndex([t]))
    assert trailing.loc[t, "a"] == pytest.approx(1.01 ** 12 - 1)
    assert math.isnan(trailing.loc[t, "b"])
    later = returns.copy()
    later.loc["1991-02":] = 0.5
    assert s3.trailing_return(later, pd.PeriodIndex([t])).loc[t, "a"] == trailing.loc[t, "a"]


# label_span ---------------------------------------------------------------------------------------

def test_label_span_starts_at_the_first_month_with_all_labels_and_a_class_return() -> None:
    index = pd.period_range("1990-01", periods=6, freq="M")
    labels = pd.DataFrame({"market_trend": [1, 1, 0, 1, 0, 1], "market_volatility": [np.nan, 0, 0, 1, 1, 0],
                           "credit_spread": [1, 1, 1, 0, 0, 1]}, index=index, dtype=float)
    values = pd.DataFrame({"A": [np.nan, np.nan, 0.01, 0.02, np.nan, 0.01]}, index=index)
    assert s3.label_span_start(labels, values, index[-1]) == index[2]
    gap = labels.copy()
    gap.loc[index[4], "credit_spread"] = np.nan
    with pytest.raises(PublicDataRefusal, match="typed-missing labels inside the label span"):
        s3.label_span_start(gap, values, index[-1])


def test_labels_before_the_span_change_neither_observed_nor_shifted_r2(
        fixture_data: s3.Step3Data, built: dict) -> None:
    # Early market months move market_trend labels before the span start (1953-04 in this fixture) only.
    market = fixture_data.market_monthly.copy()
    market.loc[:"1950-12", "Mkt-RF"] = -market.loc[:"1950-12", "Mkt-RF"] - 0.05
    after = s3.build_rules(replace(fixture_data, market_monthly=market), trial_like())
    assert after["span_start"] == built["span_start"]
    before_span = built["labels"].loc[:built["span_start"] - 1, "market_trend"]
    assert not before_span.equals(after["labels"].loc[:built["span_start"] - 1, "market_trend"])
    pd.testing.assert_frame_equal(after["r2"]["multipliers"], built["r2"]["multipliers"])
    np.testing.assert_array_equal(after["r2"]["span_labels"], built["r2"]["span_labels"])
    for offset in s3.null_offsets(len(built["r2"]["span_labels"]), 5):
        shifted = [s3.r2_tilt(r["r2"]["span_values"], s3.shift_labels(r["r2"]["span_labels"], offset),
                              r["r2"]["positions"])["multipliers"] for r in (built, after)]
        np.testing.assert_array_equal(shifted[0], shifted[1])
    counts = s3.label_counts(built["labels"], built["span_start"], fixture_data)
    assert counts["months_before_span_with_defined_label"]["market_trend"] == int(before_span.notna().sum()) > 0


# Label boundaries (decision log) ---------------------------------------------------------------------

def test_market_trend_of_exactly_zero_is_down_and_uses_months_t13_to_t2() -> None:
    index = pd.period_range("1990-01", "1991-12", freq="M")
    total = pd.Series(0.0, index=index)
    t = month("1991-03")
    assert s3.market_trend_labels(total, pd.PeriodIndex([t])).iloc[0] == 0.0
    total.loc["1991-02":] = 0.5  # t-1 and later
    assert s3.market_trend_labels(total, pd.PeriodIndex([t])).iloc[0] == 0.0
    total.loc["1990-02"] = 0.01  # t-13
    assert s3.market_trend_labels(total, pd.PeriodIndex([t])).iloc[0] == 1.0
    total.loc["1990-05"] = np.nan
    assert math.isnan(s3.market_trend_labels(total, pd.PeriodIndex([t])).iloc[0])


def test_market_volatility_median_expands_through_the_signal_month() -> None:
    rng = np.random.default_rng(2)
    days = pd.bdate_range("1990-01-01", "1997-12-31")
    daily = pd.Series(rng.normal(0.0, 0.01, len(days)) * np.where(days.month % 3 == 0, 2.0, 1.0), index=days)
    volatility = s3.month_end_volatility(daily)
    first = volatility.first_valid_index()
    months = pd.period_range("1994-01", "1997-12", freq="M")
    labels = s3.market_volatility_labels(daily, months)
    for t in months:
        past = volatility.loc[:t - 2].dropna()
        expected = (np.nan if len(past) < 60 else float(volatility[t - 2] > np.median(past.to_numpy())))
        assert (math.isnan(expected) and math.isnan(labels[t])) or labels[t] == expected
    sixtieth = first + 59  # the 60th month-end value
    assert math.isnan(labels[sixtieth + 1]) and not math.isnan(labels[sixtieth + 2])
    t = month("1996-06")
    last_day = daily.index[daily.index.to_period("M") == t - 2].max()
    later = daily.copy()
    later[later.index > last_day] *= 10.0
    assert s3.market_volatility_labels(later, pd.PeriodIndex([t])).iloc[0] == labels[t]
    window = daily[daily.index <= last_day].iloc[-63:]
    assert volatility[t - 2] == pytest.approx(float(np.std(window, ddof=1)) * math.sqrt(252))


def test_credit_spread_compares_month_t3_with_the_median_of_months_t122_to_t3() -> None:
    index = pd.period_range("1980-01", "1995-12", freq="M")
    rng = np.random.default_rng(4)
    credit = pd.DataFrame({"BAA": 5 + rng.normal(0, 0.3, len(index)), "AAA": 4.0}, index=index)
    months = pd.period_range("1990-03", "1995-12", freq="M")
    labels = s3.credit_spread_labels(credit, months)
    spread = credit["BAA"] - credit["AAA"]
    for t in months:
        window = spread.loc[t - 122: t - 3]
        assert len(window) == 120
        assert labels[t] == float(spread[t - 3] > np.median(window.to_numpy()))
    assert math.isnan(s3.credit_spread_labels(credit, pd.PeriodIndex([month("1990-02")])).iloc[0])
    t = month("1993-06")
    later = credit.copy()
    later.loc[t - 2:, "BAA"] = 50.0
    assert s3.credit_spread_labels(later, pd.PeriodIndex([t])).iloc[0] == labels[t]
    gap = credit.copy()
    gap.loc[t - 122, "BAA"] = np.nan
    assert math.isnan(s3.credit_spread_labels(gap, pd.PeriodIndex([t])).iloc[0])


# class_return_missing and the class return (decision log) ---------------------------------------------

def test_class_return_is_r1_applied_within_the_class(fixture_data: s3.Step3Data, built: dict) -> None:
    w1 = built["weights"]["R1"]
    returns = built["returns"].loc[w1.index]
    for name in ("Momentum", "Value", "Accruals"):
        columns = [c for c in w1.columns if fixture_data.classes[c] == name]
        within = w1[columns].div(w1[columns].sum(axis=1), axis=0)
        expected = (within * returns[columns]).sum(axis=1)
        np.testing.assert_allclose(built["class_values"].loc[w1.index, name], expected, rtol=1e-12)
    totals = pd.DataFrame({name: w1[[c for c in w1.columns if fixture_data.classes[c] == name]].sum(axis=1)
                           for name in fixture_data.class_order})
    gross = (w1 * returns).sum(axis=1)
    np.testing.assert_allclose((totals * built["class_values"].loc[w1.index]).sum(axis=1), gross, rtol=1e-12)


def test_class_returns_type_missing_members_and_empty_classes() -> None:
    index = pd.period_range("1990-01", periods=3, freq="M")
    returns = pd.DataFrame({"a": [0.01, np.nan, 0.03], "b": [0.02, 0.02, 0.02], "c": [0.0, 0.0, 0.0]}, index=index)
    in_set = pd.DataFrame({"a": [True, True, True], "b": [True, True, True], "c": [False, False, True]}, index=index)
    sigma = pd.DataFrame(1.0, index=index, columns=list("abc")).where(in_set)
    classes = pd.Series({"a": "A", "b": "A", "c": "C"})
    values, reasons = s3.class_returns(returns, in_set, sigma, classes, ["A", "C"])
    assert values.loc[index[0], "A"] == pytest.approx(0.015)
    assert math.isnan(values.loc[index[1], "A"]) and reasons.loc[index[1], "A"] == "member_return_missing"
    assert math.isnan(values.loc[index[0], "C"]) and reasons.loc[index[0], "C"] == "no_member"
    assert values.loc[index[2], "C"] == 0.0 and reasons.loc[index[2], "C"] == PRESENT


def test_lookback_class_months_with_a_missing_member_return_are_left_out_and_counted(
        fixture_data: s3.Step3Data, built: dict, evaluated: dict) -> None:
    reasons = built["class_reasons"]["Momentum"]
    gap = reasons.loc["1973-12":"1974-11"]
    assert (gap == "member_return_missing").all()
    assert evaluated["class_missing"]["lookback_in_span"]["Momentum"]["member_return_missing"] == 12
    values = built["class_values"].copy()
    values.loc["1973-12":"1974-11", "Momentum"] = 123.0  # would dominate every history if it were used
    moved = s3.r2_on_months(values, built["labels"], built["span_start"], fixture_data.last, built["months"])
    changed = s3.r2_on_months(built["class_values"], built["labels"], built["span_start"], fixture_data.last,
                              built["months"])
    assert not np.allclose(moved["means"], changed["means"], equal_nan=True)
    assert np.isfinite(changed["means"][:, fixture_data.class_order.index("Momentum")]).all()


def test_an_evaluated_month_with_an_empty_class_refuses(fixture_data: s3.Step3Data) -> None:
    returns, missing = fixture_data.returns.copy(), fixture_data.missing.copy()
    for name in ("debt_issuance_0", "debt_issuance_1"):  # bad data in a lookback month empties 1975-01..1977-07
        returns.loc["1974-06", name] = np.nan
        missing.loc["1974-06", name] = MISSING_BLANK
    with pytest.raises(PublicDataRefusal, match="no member"):
        s3.evaluate(replace(fixture_data, returns=returns, missing=missing), trial_like(), COSTS, draws=3)


def test_post_publication_class_months_without_a_subset_member_are_typed_missing_and_counted(
        evaluated: dict) -> None:
    post = evaluated["_post"]
    assert post["status"] == "completed"
    counts = post["class_missing"]["full"]["Value"]["no_member"]
    assert counts == len(pd.period_range(post["start_month"], "1981-02", freq="M"))
    assert post["_class_values"].loc[post["start_month"]:"1981-02", "Value"].isna().all()
    assert evaluated["state_effects"]["S3.effect.value.market_trend"]["b_post_publication"] is not None


def test_subset_r2_span_starts_at_the_first_subset_class_return_and_uses_subset_histories_only(
        fixture_data: s3.Step3Data, built: dict, evaluated: dict) -> None:
    post = evaluated["_post"]
    values = post["_class_values"]
    defined = built["labels"].notna().all(axis=1) & values.notna().any(axis=1)
    assert post["span_start"] == str(defined.index[defined.to_numpy().argmax()])
    assert month(post["span_start"]) > built["span_start"]
    # size_1 has no publication year, so it never enters the subset: moving its returns moves the full-set
    # Size class but leaves every R2-sub multiplier and weight unchanged.
    returns = fixture_data.returns.copy()
    returns["size_1"] = returns["size_1"] * -3.0
    moved = s3.evaluate(replace(fixture_data, returns=returns), trial_like(), COSTS, draws=3)
    pd.testing.assert_frame_equal(moved["_post"]["_r2"]["multipliers"], post["_r2"]["multipliers"])
    pd.testing.assert_frame_equal(moved["_post"]["_weights"]["R2"], post["_weights"]["R2"])
    assert not moved["_built"]["class_values"]["Size"].equals(built["class_values"]["Size"])


# state_effect_hac -------------------------------------------------------------------------------------------

def test_state_effect_slope_is_the_cell_mean_difference_and_lag0_matches_white() -> None:
    rng = np.random.default_rng(8)
    d = (rng.random(200) > 0.4).astype(float)
    y = 0.01 * d + rng.normal(0, 0.02, 200) * (1 + d)
    result = s3.state_effect_statistic(y, d, lags=0)
    assert result["b"] == pytest.approx(y[d == 1].mean() - y[d == 0].mean(), rel=1e-12)
    x = np.column_stack([np.ones_like(d), d])
    xtx_inv = np.linalg.inv(x.T @ x)
    residual = y - x @ (xtx_inv @ x.T @ y)
    white = xtx_inv @ (x.T * residual ** 2) @ x @ xtx_inv
    assert result["t"] == pytest.approx(result["b"] / math.sqrt(white[1, 1]), rel=1e-10)
    default = s3.state_effect_statistic(y, d)
    assert default["lags"] == int(np.floor(4 * (200 / 100) ** (2 / 9)))
    assert default["p"] == pytest.approx(2 * (1 - __import__("scipy").stats.norm.cdf(abs(default["t"]))))
    assert s3.state_effect_statistic(y, np.ones_like(d))["status"] == "undefined"


# random_date_null --------------------------------------------------------------------------------------------

def test_random_date_offsets_shift_and_pvalue() -> None:
    n = 648
    offsets = s3.null_offsets(n)
    np.testing.assert_array_equal(
        offsets, np.random.default_rng(20260928).integers(60, n - 60, size=999, endpoint=True))
    assert len(offsets) == 999 and offsets.min() >= 60 and offsets.max() <= n - 60
    labels = np.random.default_rng(1).integers(0, 2, size=(n, 3)).astype(float)
    shifted = s3.shift_labels(labels, 100)
    np.testing.assert_array_equal(shifted[100], labels[0])
    np.testing.assert_array_equal(shifted[0], labels[n - 100])
    np.testing.assert_array_equal(shifted.sum(axis=0), labels.sum(axis=0))
    result = s3.random_date_pvalue(2.0, np.array([1.0, -2.5, 0.3, np.nan]))
    assert result["exceedances"] == 2 and result["undefined_draws"] == 1 and result["p"] == pytest.approx(3 / 5)
    with pytest.raises(PublicDataRefusal, match="too short"):
        s3.null_offsets(119)


def test_undefined_draws_count_as_exceedances_and_an_undefined_observed_statistic_cannot_survive() -> None:
    y = np.random.default_rng(3).normal(0, 0.01, 120)
    constant = s3.state_effect_statistic(y, np.zeros(120))
    zero_variance = s3.state_effect_statistic(np.ones(120), (np.arange(120) % 2).astype(float))
    assert constant["t"] is None and zero_variance["t"] is None
    draws = np.array([np.nan if value is None else value for value in (constant["t"], zero_variance["t"], 0.1)])
    result = s3.random_date_pvalue(1.0, draws)
    assert result["undefined_draws"] == 2 and result["exceedances"] == 2 and result["p"] == pytest.approx(3 / 4)
    undefined = s3.random_date_pvalue(None, np.array([0.1, 0.2]))
    assert undefined["p"] is None
    assert not s3.cell_survives(1e-9, undefined["p"], True, 0.01, [0.01, 0.01, 0.01])


def test_evaluate_reports_the_null_beside_s3_r2_and_every_state_test(evaluated: dict) -> None:
    null = evaluated["null"]
    assert null["draws"] == FEW_DRAWS and null["offset_min"] >= 60 and null["offset_max"] <= null["span_months"] - 60
    r2 = evaluated["rule_tests"]["S3.R2"]["random_date"]
    assert r2["draws"] == FEW_DRAWS and r2["p"] == (1 + r2["exceedances"]) / (FEW_DRAWS + 1)
    assert "random_date" not in evaluated["rule_tests"]["S3.R3"]
    for effect in evaluated["state_effects"].values():
        assert effect["random_date"]["draws"] == FEW_DRAWS


def test_a_zero_offset_draw_reproduces_the_observed_statistics(evaluated: dict) -> None:
    r2_t, effect_t = s3.null_draw(0, evaluated["_null_context"])
    assert r2_t == pytest.approx(evaluated["rule_tests"]["S3.R2"]["hac_statistic"], rel=1e-12)
    observed = [effect["full"]["t"] for effect in evaluated["state_effects"].values()]
    np.testing.assert_allclose(effect_t, observed, rtol=1e-12)
    moved_r2, moved = s3.null_draw(97, evaluated["_null_context"])
    assert not np.allclose(moved, observed)


# s3_family ----------------------------------------------------------------------------------------------------

def test_s3_family_passes_42_observed_pvalues_with_family_size_1047(monkeypatch, fixture_data) -> None:
    calls = []
    original = s3.adjust_pvalues

    def spy(pvalues, **kwargs):
        calls.append((len(pvalues), kwargs))
        return original(pvalues, **kwargs)

    monkeypatch.setattr(s3, "adjust_pvalues", spy)
    result = s3.evaluate(fixture_data, trial_like(), COSTS, draws=3)
    assert calls == [(42, {"method": "by", "family_size": 1047})]
    assert len(result["rule_tests"]) == 3 and len(result["state_effects"]) == 39
    for count in (41, 43):
        with pytest.raises(PublicDataRefusal, match="S3 family"):
            s3.s3_adjust(pd.Series(0.5, index=range(count)))
    with pytest.raises(PublicDataRefusal, match="S3 family"):
        s3.s3_adjust(pd.Series(0.5, index=range(42)), family_size=1046)
    q = s3.s3_adjust(pd.Series([1e-7] + [1.0] * 41))
    assert q.iloc[0] == pytest.approx(min(1.0, 1e-7 * 1047 * sum(1 / k for k in range(1, 1048))))


# episode_rule --------------------------------------------------------------------------------------------------

def _alternating(months: pd.PeriodIndex, run: int) -> pd.Series:
    return pd.Series([float((i // run) % 2 == 0) for i in range(len(months))], index=months)


def test_episode_rule_counts_boundary_runs_in_both_halves_and_needs_ten_per_cell_and_half() -> None:
    bounds = {"first_half": (month("1975-01"), month("1979-12")), "second_half": (month("1980-01"), month("1985-12"))}
    months = pd.period_range("1975-01", "1985-12", freq="M")
    crossing = pd.Series(0.0, index=months)
    crossing.loc["1979-11":"1980-02"] = 1.0
    assert s3.episode_count(crossing.loc["1975-01":"1979-12"], 1.0) == 1
    assert s3.episode_count(crossing.loc["1980-01":"1985-12"], 1.0) == 1
    ten = _alternating(months, 3)  # first half: 20 runs of 3 months, 10 per cell
    labels = pd.DataFrame({state: ten for state in s3.STATES})
    result = s3.eligibility(labels, bounds)
    assert result["market_trend"]["episodes"]["first_half"] == {"up": 10, "down": 10}
    assert all(result[state]["eligible"] for state in s3.STATES)
    nine = ten.copy()
    nine.loc["1975-01":"1975-03"] = 0.0  # the first wide run joins the next normal run: 9 wide, 10 normal
    labels["credit_spread"] = nine
    result = s3.eligibility(labels, bounds)
    assert result["credit_spread"]["episodes"]["first_half"] == {"wide": 9, "normal": 10}
    assert not result["credit_spread"]["eligible"] and result["market_trend"]["eligible"]


def test_state_tests_on_an_ineligible_state_are_description_only_and_cannot_survive(evaluated: dict) -> None:
    for effect in evaluated["state_effects"].values():
        eligible = evaluated["states"][effect["state"]]["eligible"]
        assert effect["description_only"] is (not eligible)
        if not eligible:
            assert effect["survives"] is False


# r2_timing_claim ------------------------------------------------------------------------------------------------

def _grid(r1: tuple[float, float], other: tuple[float, float]) -> dict:
    cell = lambda sharpe, drawdown: {"sharpe": sharpe, "max_drawdown": drawdown}  # noqa: E731
    return {rule: {f"{cost}bp": {half: cell(*values) for half in s3.HALVES} for cost in COSTS}
            for rule, values in (("R1", r1), ("R2", other))}


def _post(r1: tuple, r2: tuple, mean: float | None = 0.0002, months: int = 300) -> dict:
    def metrics(values):
        return {"full": {"months": months, "sharpe": values[0], "max_drawdown": values[1]}}
    return {"status": "completed", "rules": {"R1": {f"{c}bp": metrics(r1) for c in COSTS},
                                             "R2": {f"{c}bp": metrics(r2) for c in COSTS}},
            "mean_difference_20bp": mean}


def _states(episodes: int = 10) -> dict:
    bounds = {"first_half": (month("1975-01"), month("1979-12")), "second_half": (month("1980-01"), month("1985-12"))}
    months = pd.period_range("1975-01", "1985-12", freq="M")
    labels = pd.DataFrame({state: _alternating(months, 3) for state in s3.STATES})
    if episodes == 9:
        labels.loc["1975-01":"1975-03", "market_volatility"] = 0.0
    return s3.eligibility(labels, bounds)


def _claim(post: dict, mean: float | None = 0.001, states: dict | None = None) -> dict:
    conditions = s3.closure_conditions(_grid((1.0, -0.1), (1.1, -0.09)), "R2", COSTS)
    return s3.r2_timing_claim(conditions, mean, 0.01, 0.01, post, states or _states(10), COSTS)


def test_r2_timing_claim_needs_all_six_conditions_including_post_publication() -> None:
    good = _post((1.0, -0.1), (1.2, -0.08))
    assert _claim(good)["qualifies"]
    loses_after_publication = _claim(_post((1.0, -0.1), (0.9, -0.08)))
    assert not loses_after_publication["qualifies"] and loses_after_publication["failed"] == ["5"]
    assert _claim(_post((1.0, -0.1), (None, -0.08)))["failed"] == ["5"]
    assert _claim(_post((1.0, -0.1), (1.2, -0.08), months=0))["failed"] == ["5"]
    assert _claim({"status": "refused"})["failed"] == ["5"]
    assert _claim(_post((1.0, -0.1), (1.2, -0.08), mean=-1e-6))["failed"] == ["5"]
    assert _claim(good, mean=0.0)["failed"] == ["2"]
    assert _claim(good, mean=None)["failed"] == ["2"]
    nine = _states(9)
    assert nine["market_volatility"]["episodes"]["first_half"] == {"high": 9, "normal": 10}
    assert _claim(good, states=nine)["failed"] == ["6"]
    conditions = s3.closure_conditions(_grid((1.0, -0.1), (1.1, -0.09)), "R2", COSTS)
    assert s3.r2_timing_claim(conditions, 0.001, 0.06, 0.01, good, _states(10), COSTS)["failed"] == ["3"]
    assert s3.r2_timing_claim(conditions, 0.001, 0.01, None, good, _states(10), COSTS)["failed"] == ["4"]
    losing = s3.closure_conditions(_grid((1.0, -0.1), (0.9, -0.09)), "R2", COSTS)
    assert s3.r2_timing_claim(losing, 0.001, 0.01, 0.01, good, _states(10), COSTS)["failed"] == ["1"]


# closure_rule -------------------------------------------------------------------------------------------------------

def test_closure_rule_closes_on_any_failed_condition_and_ties_below_tolerance_keep_it_open() -> None:
    passing = _grid((1.0, -0.10), (1.1, -0.09))
    assert s3.closure_decision(s3.closure_conditions(passing, "R2", COSTS)) == "open"
    for half in s3.HALVES:
        for cost in COSTS:
            for metric, value in (("sharpe", 0.99), ("max_drawdown", -0.11)):
                grid = json.loads(json.dumps(passing))
                grid["R2"][f"{cost}bp"][half][metric] = value
                conditions = s3.closure_conditions(grid, "R2", COSTS)
                assert s3.closure_decision(conditions) == "closed"
                assert sum(not c["holds"] for c in conditions) == 1
    tie = _grid((1.0, -0.10), (1.0 - 5e-13, -0.10 - 5e-13))
    assert s3.closure_decision(s3.closure_conditions(tie, "R2", COSTS)) == "open"
    beyond = _grid((1.0, -0.10), (1.0 - 2e-12, -0.10))
    assert s3.closure_decision(s3.closure_conditions(beyond, "R2", COSTS)) == "closed"
    undefined = _grid((1.0, -0.10), (None, -0.10))
    assert s3.closure_decision(s3.closure_conditions(undefined, "R2", COSTS)) == "closed"


def test_evaluate_applies_the_closure_rule_to_r2_and_reports_margins(evaluated: dict) -> None:
    closure = evaluated["closure"]
    assert len(closure["conditions"]) == 8
    expected = "open" if all(c["holds"] for c in closure["conditions"]) else "closed"
    assert closure["decision"] == expected
    assert closure["carried_to_step4"] == (["R1"] if expected == "closed" else ["R1", "R2"])
    for c in closure["conditions"]:
        assert c["margin"] is not None
    assert set(evaluated["rule_conditions"]) == {"R0", "R2", "R3", "R4"}


# costs ----------------------------------------------------------------------------------------------------------------

def test_tilted_rules_and_post_publication_books_come_from_the_step2_portfolio(
        evaluated: dict) -> None:
    built = evaluated["_built"]
    for rule in s3.TILTED_RULES:
        for cost in COSTS:
            book = evaluated["_books"][rule][cost]
            pd.testing.assert_frame_equal(book, base.portfolio(built["weights"][rule], built["returns"], cost))
            assert book["turnover"].iloc[0] == pytest.approx(1.0)
            net = book["gross"] - cost / 10_000 * book["turnover"]
            pd.testing.assert_series_equal(book["net"], net, check_names=False)
    post = evaluated["_post"]
    for rule in ("R1", "R2"):
        for cost in COSTS:
            book = post["_books"][rule][cost]
            pd.testing.assert_frame_equal(book, base.portfolio(post["_weights"][rule], built["returns"], cost))
            assert book.index[0] == month(post["start_month"])
            assert book["turnover"].iloc[0] == pytest.approx(1.0)


def test_rule_metrics_are_the_step2_metrics(evaluated: dict) -> None:
    book = evaluated["_books"]["R3"][20]
    expected = base.performance(book["net"].loc["1980-01":], book["turnover"].loc["1980-01":])
    assert evaluated["rules"]["R3"]["20bp"]["second_half"] == expected
    step2 = evaluated["_step2"]["rules"]
    assert evaluated["rules"]["R1"] == step2["R1"] and evaluated["rules"]["R0"] == step2["R0"]


# Interval (decision log) --------------------------------------------------------------------------------------------

def test_rule_test_interval_uses_the_hac_standard_error() -> None:
    rng = np.random.default_rng(6)
    difference = pd.Series(0.0005 + rng.normal(0, 0.003, 300))
    result = s3.rule_test(difference)
    reference = return_test_statistics(difference, periods_per_year=12)
    assert result["mean_return"] / result["standard_error"] == pytest.approx(reference["hac_statistic"], rel=1e-12)
    low, high = result["ci95_monthly"]
    assert (low + high) / 2 == pytest.approx(result["mean_return"])
    assert (high - low) / 2 == pytest.approx(1.959964 * result["standard_error"])
    assert result["ci95_annual"] == pytest.approx([12 * low, 12 * high])
    constant = s3.rule_test(pd.Series(0.0, index=range(50)))
    assert constant["status"] == "zero_variance" and constant["ci95_monthly"] is None


# R4 rank scaling and layout (decision log) -----------------------------------------------------------------------

def test_r4_rank_scaling_uses_average_ranks_and_zero_for_a_single_row() -> None:
    index = pd.period_range("1990-01", periods=3, freq="M")
    values = pd.DataFrame([[3.0, 1.0, 3.0, 2.0], [5.0, 1.0, 2.0, 3.0], [0.4, 0.1, 0.2, 0.3]], index=index,
                          columns=list("abcd"))
    covered = pd.DataFrame([[True] * 4, [True, False, False, False], [True, True, False, True]], index=index,
                           columns=list("abcd"))
    scaled = s3.rank_scaled(values, covered)
    np.testing.assert_allclose(scaled.iloc[0], [2.5 / 3 - 0.5, -0.5, 2.5 / 3 - 0.5, 1 / 3 - 0.5])
    assert scaled.iloc[1, 0] == 0.0 and scaled.iloc[1, 1:].isna().all()
    np.testing.assert_allclose(scaled.iloc[2, [0, 1, 3]], [0.5, -0.5, 0.0])
    assert math.isnan(scaled.iloc[2, 2])


def test_r4_has_83_columns_in_the_declared_layout(built: dict) -> None:
    names = s3.r4_feature_names(CLASSES)
    assert len(names) == 83 and len(set(names)) == 83
    traits = s3.r4_trait_names(CLASSES)
    assert len(traits) == 20 and names[:20] == traits
    assert names[20:23] == [f"state={state}" for state in s3.STATES]
    assert names[23:] == [f"{trait}*state={state}" for trait in traits for state in s3.STATES]
    design = built["design"]
    assert design.features.shape[1] == 83 and design.names == names
    features = design.features
    for j, trait in enumerate(traits):
        for k, state in enumerate(s3.STATES):
            np.testing.assert_array_equal(features[:, names.index(f"{trait}*state={state}")],
                                          features[:, j] * features[:, 20 + k])
    themes = features[:, :13]
    assert (themes.sum(axis=1) == 1).all() and (features[:, 13:16].sum(axis=1) == 1).all()
    ranks = features[:, 17:20]
    assert (ranks >= -0.5).all() and (ranks <= 0.5).all()
    fit = next(fit for fit in built["fits"].values() if fit["status"] == "fit")
    assert list(fit["coefficients"]) == names


# trial_file_pins --------------------------------------------------------------------------------------------------------

def test_runner_refuses_unless_every_trial_file_matches_head_and_its_pin(tmp_path: Path) -> None:
    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                       check=True, capture_output=True)
    git("init", "-q")
    pins = {}
    for i, name in enumerate(["v1.json", "a1.json", "a2.json", "a3.json"]):
        path = tmp_path / "docs" / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(f'{{"n": {i}}}\n', encoding="utf-8")
        pins[f"docs/{name}"] = __import__("hashlib").sha256(path.read_bytes()).hexdigest()
    git("add", "docs")
    git("commit", "-q", "-m", "trial")
    assert set(s3.verify_trial_files(tmp_path, pins)) == set(pins)
    (tmp_path / "docs" / "a3.json").write_text('{"n": 9}\n', encoding="utf-8")
    with pytest.raises(PublicDataRefusal, match="differs from its committed HEAD"):
        s3.verify_trial_files(tmp_path, pins)
    git("commit", "-q", "-am", "edit")
    with pytest.raises(PublicDataRefusal, match="differs from the pinned"):
        s3.verify_trial_files(tmp_path, pins)


def test_committed_trial_files_match_the_four_pins() -> None:
    assert len(s3.TRIAL_PINS) == 4
    assert s3.TRIAL_PINS[s3.AMENDMENT_3_PATH] == "c59f69c8262190ad7a1807d42a02e572667dcffa03c11a11c4d2e17a2bb5bfbb"
    assert set(s3.verify_trial_files(s3.REPO_ROOT)) == set(s3.TRIAL_PINS)


# New sources and traits ---------------------------------------------------------------------------------------------------

DAILY_TEXT = """This file was created using the 202608 CRSP database.
The Tbill return is the simple daily rate.

,Mkt-RF,SMB,HML,RF
19260701,    0.09,   -0.25,   -0.27,    0.01
19260702,    0.45,   -0.33,   -0.06,    0.01
19260706,  -99.99,    0.30,   -0.39,    0.01

Copyright 2026 Eugene F. Fama and Kenneth R. French
"""


def test_french_daily_parser_reads_yyyymmdd_rows_with_typed_missing(tmp_path: Path) -> None:
    path = tmp_path / "daily.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("F-F_Research_Data_Factors_daily.csv", DAILY_TEXT)
    values, reasons, rows = s3.read_french_daily_zip(path, "F-F_Research_Data_Factors_daily.csv", column="Mkt-RF")
    assert rows == 3 and list(values.index.strftime("%Y%m%d")) == ["19260701", "19260702", "19260706"]
    assert values.iloc[1] == pytest.approx(0.0045) and math.isnan(values.iloc[2])
    assert list(reasons) == [PRESENT, PRESENT, MISSING_CODE]
    repeated = tmp_path / "repeated.zip"
    with zipfile.ZipFile(repeated, "w") as archive:
        archive.writestr("d.csv", DAILY_TEXT.replace("19260706", "19260702"))
    with pytest.raises(PublicDataRefusal, match="repeat"):
        s3.read_french_daily_zip(repeated, "d.csv", column="Mkt-RF")


def test_accounting_list_is_parsed_without_executing_the_file(tmp_path: Path) -> None:
    path = tmp_path / "aux_functions.py"
    path.write_text('raise SystemExit("never executed")\n\n'
                    'def acc_chars_list():\n    acc_chars = ["at_gr1", "be_me"]\n    return acc_chars\n',
                    encoding="utf-8")
    assert s3.read_accounting_characteristics(path) == ["at_gr1", "be_me"]
    path.write_text("def other():\n    return []\n", encoding="utf-8")
    with pytest.raises(PublicDataRefusal, match="acc_chars_list"):
        s3.read_accounting_characteristics(path)


def test_data_source_groups_must_partition_the_factors() -> None:
    trial = {"traits": {"data_source": {"composite": ["qmj"], "market": ["ret_1_0"]}}}
    result = s3.data_source_map(["be_me", "qmj", "ret_1_0"], ["be_me", "at_gr1"], trial)
    assert result.to_dict() == {"be_me": "accounting", "qmj": "composite", "ret_1_0": "market"}
    with pytest.raises(PublicDataRefusal, match="partition"):
        s3.data_source_map(["be_me", "qmj", "ret_1_0", "prc"], ["be_me"], trial)
    with pytest.raises(PublicDataRefusal, match="partition"):
        s3.data_source_map(["be_me", "qmj", "ret_1_0"], ["be_me", "qmj"], trial)


def test_manifest_update_adds_step3_sources_and_refuses_a_changed_step2_file(tmp_path: Path) -> None:
    path = tmp_path / base.MANIFEST_JSON
    path.parent.mkdir(parents=True)
    old = {"id": "jkp_cluster_labels", "sha256": "a" * 64, "rows": 153}
    path.write_text(json.dumps({"schema_version": "m5_public_data_manifest_v1", "code_commit": "abc",
                                "sources": [old]}), encoding="utf-8")
    new = {"id": "french_ff3_daily", "sha256": "b" * 64, "rows": 10}
    note = s3.update_manifest(tmp_path, [old], [new], {"commit": "def"})
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["code_commit"] == "abc" and manifest["step3"] == note
    assert [entry["id"] for entry in manifest["sources"]] == ["jkp_cluster_labels", "french_ff3_daily"]
    with pytest.raises(PublicDataRefusal, match="differs from the manifest"):
        s3.update_manifest(tmp_path, [{**old, "sha256": "c" * 64}], [new], {"commit": "def"})


# End to end on the fixture --------------------------------------------------------------------------------------------------

def test_evaluate_and_report_on_the_synthetic_fixture(evaluated: dict) -> None:
    assert evaluated["labels"]["span_start"] == "1953-04"
    assert evaluated["r4"]["coverage"]["full"]["uncovered_by_reason"]["missing_trailing_return"] > 0
    assert evaluated["r3"]["members_without_trailing_return"]["first_half"] == 12
    assert 0 < evaluated["r2"]["weights_differ_share"]["full"] <= 1
    result = s3.json_ready({
        **{key: value for key, value in evaluated.items() if not key.startswith("_")},
        "evidence_ceiling": "DIAGNOSTIC_ONLY", "run_utc": "2026-09-28T00:00:00Z",
        "git": {"commit": "abc", "tracked_changes": False}, "switch_cost_bps": COSTS, "timing": base.TIMING,
        "trial_files": s3.TRIAL_PINS, "manifest": [],
        "missing_codes": {"french_ff3_daily_mkt_rf": 0, "fred_baa_aaa": {}, "french_ff3_monthly": {}},
        "runtime_seconds": 1.0,
    })
    text = json.dumps(result, allow_nan=False)
    assert "NaN" not in text
    report = s3.render_report(result)
    assert report.isascii()
    assert "**Evidence ceiling: DIAGNOSTIC_ONLY.**" in report.splitlines()[2]
    for heading in ("## Conclusion", "## Closure Conditions", "## S3 Rule Tests", "## State-Effect Tests (39",
                    "## R3 and R4 Coverage", "## Post-Publication Comparison", "## Limitations"):
        assert heading in report
    assert "R2 re-estimated on post-publication factor-months only, with history from the subset label span start" \
        in report
    assert report.count("| S3.effect.") == 39


def test_runner_never_calls_the_ml_combination_path(monkeypatch, fixture_data: s3.Step3Data) -> None:
    # The features package __init__ imports ml_combination, so the module is loaded; the runner must never
    # reach its z-score and row-filter path (v1 known_defect_to_avoid).
    import features
    import features.ml_combination as ml

    def refuse(*args, **kwargs):
        raise AssertionError("ml_combination was called")

    for name in dir(ml):
        if callable(getattr(ml, name)) and getattr(getattr(ml, name), "__module__", None) == ml.__name__:
            monkeypatch.setattr(ml, name, refuse)
    monkeypatch.setattr(features, "walk_forward_ml_factor_composite", refuse)
    assert not any(value is ml for value in vars(s3).values())
    s3.evaluate(fixture_data, trial_like(), COSTS, draws=3)
