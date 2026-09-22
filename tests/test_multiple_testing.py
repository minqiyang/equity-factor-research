"""Numerical and boundary oracles for observed-family inference."""

import json
import math

import numpy as np
import pandas as pd
import pytest
from scipy.stats import false_discovery_control, norm, t, ttest_1samp

from features.multiple_testing import (
    METHODS, P_VALUE_FLOOR, adjust_pvalues, return_test_statistics, sharpe_haircut,
)


def test_published_benjamini_hochberg_1995_table() -> None:
    # Published 15-hypothesis example reproduced in SciPy's FDR documentation.
    p = pd.Series([.0001, .0004, .0019, .0095, .0201, .0278, .0298, .0344,
                   .0459, .3240, .4262, .5719, .6528, .7590, 1.0])
    expected = [.0015, .003, .0095, .035625, .0603, .0298*15/7,
                .0298*15/7, .0645, .0765, .486, .4262*15/11,
                .714875, .6528*15/13, .7590*15/14, 1.0]
    np.testing.assert_allclose(adjust_pvalues(p, method="bh"), expected, rtol=1e-14)
    assert (adjust_pvalues(p, method="bh") <= .05).sum() == 4
    assert (adjust_pvalues(p, method="bonferroni") <= .05).sum() == 3


@pytest.mark.parametrize(("method", "expected"), [
    ("bonferroni", [.04, .04, .16, .8]),
    ("holm", [.04, .04, .08, .2]),
    ("bh", [.02, .02, .16/3, .2]),
    ("by", [.02*25/12, .02*25/12, .16/3*25/12, .2*25/12]),
])
def test_hand_computed_ties_and_permutation(method, expected) -> None:
    order = [3, 1, 0, 2]
    p = pd.Series(np.array([.01, .01, .04, .2])[order],
                  index=pd.Index(["z", "a", "a", "b"], name="trials"), name="raw")
    result = adjust_pvalues(p, method=method)
    np.testing.assert_allclose(result, np.array(expected)[order], rtol=1e-14)
    assert result.index.equals(p.index) and result.index.name == "trials"
    assert result.name == "raw"


@pytest.mark.parametrize("method", METHODS)
def test_single_empty_and_endpoint_families(method) -> None:
    for value in (0.0, .023, 1.0, np.nan):
        p = pd.Series([value], name="trial")
        pd.testing.assert_series_equal(adjust_pvalues(p, method=method), p)
    empty = pd.Series([], index=pd.Index([], name="trial"), dtype=float)
    pd.testing.assert_series_equal(adjust_pvalues(empty, method=method), empty)
    all_missing = pd.Series([np.nan, np.nan])
    assert adjust_pvalues(all_missing, method=method).isna().all()


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("extra", [0, 1, 20])
def test_missing_and_declared_slots_equal_explicit_p_one_family(method, extra) -> None:
    p = pd.Series([.001, np.nan, .07, 0, 1, .04])
    actual = adjust_pvalues(p, method=method, family_size=len(p)+extra)
    explicit = pd.Series([.001, 1, .07, 0, 1, .04] + [1.0]*extra)
    expected = adjust_pvalues(explicit, method=method).iloc[:len(p)]
    expected.iloc[1] = np.nan
    pd.testing.assert_series_equal(actual, expected)


@pytest.mark.parametrize("method", ["bh", "by"])
def test_correlated_null_family_matches_scipy(method) -> None:
    rng = np.random.default_rng(731)
    shared = rng.normal(size=200)
    trials = shared[:, None] + .2*rng.normal(size=(200, 30))
    p = pd.Series([return_test_statistics(pd.Series(x))["hac_pvalue"] for x in trials.T])
    np.testing.assert_allclose(adjust_pvalues(p, method=method),
                               false_discovery_control(p, method=method), rtol=1e-14)
    assert (adjust_pvalues(p, method="by") >= adjust_pvalues(p, method="bh")).all()


@pytest.mark.parametrize("values", [[-.1], [1.1], [np.inf], [-np.inf]])
def test_invalid_pvalue_range(values) -> None:
    with pytest.raises(ValueError):
        adjust_pvalues(pd.Series(values))


@pytest.mark.parametrize("values", [[True], [".1"], [1j]])
@pytest.mark.parametrize("operation", [adjust_pvalues, return_test_statistics])
def test_invalid_value_types(values, operation) -> None:
    with pytest.raises(TypeError):
        operation(pd.Series(values))


@pytest.mark.parametrize("operation", [adjust_pvalues, return_test_statistics])
def test_series_boundary(operation) -> None:
    with pytest.raises(TypeError):
        operation(np.array([.1, .2]))
    with pytest.raises(TypeError):
        operation(pd.DataFrame([[.1, .2]]))


@pytest.mark.parametrize("size", [0, 1, True, np.bool_(True), 2.0, -1, 2**53, None])
def test_family_count_validation(size) -> None:
    p = pd.Series([.01, .02])
    if size is None:
        assert adjust_pvalues(p).notna().all()
    else:
        with pytest.raises(ValueError):
            adjust_pvalues(p, family_size=size)


def test_nullable_numeric_and_invalid_method() -> None:
    p = pd.Series([.01, pd.NA], dtype="Float64")
    result = adjust_pvalues(p, method="bonferroni")
    assert result.iloc[0] == .02 and np.isnan(result.iloc[1])
    with pytest.raises(ValueError):
        adjust_pvalues(p, method="invented")


def test_large_declared_family_uses_implicit_slots() -> None:
    size = 2**53 - 1
    result = adjust_pvalues(pd.Series([1e-20]), family_size=size)
    assert 1e-20 < result.iloc[0] < 1


def test_iid_and_independent_bartlett_hac_oracle() -> None:
    values = np.array([.02, -.01, .04, .025, -.03, .005, .01, .016, -.004, .009])
    result = return_test_statistics(pd.Series(values), periods_per_year=12)
    expected_iid = ttest_1samp(values, 0)
    assert result["iid_statistic"] == pytest.approx(expected_iid.statistic)
    assert result["iid_pvalue"] == pytest.approx(expected_iid.pvalue)
    assert result["observed_sharpe"] == pytest.approx(values.mean()/values.std(ddof=1)*np.sqrt(12))
    n = len(values)
    residual = values-values.mean()
    lags = math.floor(4*(n/100)**(2/9))
    covariance = sum(residual[i]**2 for i in range(n))/n
    for lag in range(1, lags+1):
        covariance += 2*(1-lag/(lags+1))*sum(residual[i]*residual[i-lag] for i in range(lag,n))/n
    statistic = values.mean()/math.sqrt(covariance/n)
    assert result["hac_statistic"] == pytest.approx(statistic)
    assert result["hac_pvalue"] == pytest.approx(2*norm.sf(abs(statistic)))
    assert result["hac_pvalue"] != pytest.approx(result["iid_pvalue"])
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(("values", "status"), [
    ([], "insufficient_observations"), ([1, 2], "insufficient_observations"),
    ([0, 0, 0], "zero_variance"), ([.1]*3, "zero_variance"),
    ([.1, np.nan, .3], "nonfinite_observations"),
    ([.1, np.inf, .3], "nonfinite_observations"),
    ([1e308, -1e308, 1e308], "undefined_variance"),
])
def test_undefined_returns_are_retained(values, status) -> None:
    result = return_test_statistics(pd.Series(values, dtype=float))
    assert result["status"] == status
    assert result["n_observations"] == len(values)
    assert result["iid_pvalue"] is None and result["hac_pvalue"] is None
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("annualization", [0, -1, True, 1.5, 2**53])
def test_invalid_annualization(annualization) -> None:
    with pytest.raises(ValueError):
        return_test_statistics(pd.Series([.01, -.02, .03]), periods_per_year=annualization)


@pytest.mark.parametrize("sign", [-1, 1])
@pytest.mark.parametrize("annualization", [12, 252])
def test_haircut_t_inverse_and_annualization(sign, annualization) -> None:
    count = 60
    observed = sign*2*math.sqrt(annualization/count)
    p = float(2*t.sf(2, count-1))
    adjusted = min(1, p*4)
    result = sharpe_haircut(observed, n_observations=count,
                           adjusted_pvalue=adjusted, periods_per_year=annualization)
    expected_t = float(t.isf(adjusted/2, count-1))
    assert result["adjusted_sharpe"] == pytest.approx(sign*expected_t*math.sqrt(annualization/count))
    assert result["haircut_fraction"] == pytest.approx(1-expected_t/2)
    assert result["adjusted_t_magnitude"] == pytest.approx(expected_t)


def test_haircut_zero_one_and_tail_resolution() -> None:
    assert sharpe_haircut(0, n_observations=60, adjusted_pvalue=1)["haircut_fraction"] == 0
    assert sharpe_haircut(-1, n_observations=60, adjusted_pvalue=1)["adjusted_sharpe"] == 0
    result = sharpe_haircut(1e10, n_observations=1000, adjusted_pvalue=0)
    assert result["adjusted_sharpe"] == 1e10
    assert result["haircut_fraction"] == 0
    returns = pd.Series(1+np.linspace(-1e-6,1e-6,1000))
    tests = return_test_statistics(returns)
    assert tests["hac_pvalue"] == P_VALUE_FLOOR
    assert tests["iid_pvalue"] == P_VALUE_FLOOR
    for method in METHODS:
        q = adjust_pvalues(pd.Series([tests["iid_pvalue"]]), method=method, family_size=10).iloc[0]
        haircut = sharpe_haircut(tests["observed_sharpe"], n_observations=1000, adjusted_pvalue=q)
        assert 0 <= haircut["haircut_fraction"] <= 1
        json.dumps(haircut, allow_nan=False)


@pytest.mark.parametrize("kwargs", [
    {"adjusted_pvalue": -.1}, {"adjusted_pvalue": 1.1}, {"adjusted_pvalue": np.nan},
    {"adjusted_pvalue": True}, {"adjusted_pvalue": 1e-10},
    {"n_observations": 2}, {"n_observations": True}, {"observed_sharpe": np.inf},
    {"observed_sharpe": True}, {"periods_per_year": 0},
    {"observed_sharpe": 1e308, "n_observations": 1000, "periods_per_year": 1},
])
def test_haircut_invalid_arguments(kwargs) -> None:
    arguments = {"observed_sharpe": 1.0, "n_observations": 60, "adjusted_pvalue": 1.0, **kwargs}
    with pytest.raises(ValueError):
        sharpe_haircut(**arguments)
