"""Tests for Purged and Embargoed Combinatorial Cross-Validation (CPCV)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score

from features.cross_validation import (
    PurgedGroupTimeSeriesSplit,
    combinatorial_purged_cross_validation_pbo,
)
from features.diagnostics import probability_of_backtest_overfitting


def test_purged_split_validates_constructor_arguments() -> None:
    # n_splits must be >= 2
    with pytest.raises(ValueError, match="n_splits must be an integer >= 2"):
        PurgedGroupTimeSeriesSplit(n_splits=1)
    with pytest.raises(ValueError, match="n_splits must be an integer >= 2"):
        PurgedGroupTimeSeriesSplit(n_splits="five")  # type: ignore[arg-type]

    # n_test_groups must be in [1, n_splits - 1]
    with pytest.raises(ValueError, match="n_test_groups must be an integer in"):
        PurgedGroupTimeSeriesSplit(n_splits=5, n_test_groups=0)
    with pytest.raises(ValueError, match="n_test_groups must be an integer in"):
        PurgedGroupTimeSeriesSplit(n_splits=5, n_test_groups=5)

    # holding_periods must be >= 0
    with pytest.raises(ValueError, match="holding_periods must be a non-negative integer"):
        PurgedGroupTimeSeriesSplit(n_splits=5, holding_periods=-1)

    # embargo_periods must be >= 0
    with pytest.raises(ValueError, match="embargo_periods must be a non-negative integer"):
        PurgedGroupTimeSeriesSplit(n_splits=5, embargo_periods=-2)

    # embargo_pct must be in [0.0, 1.0)
    with pytest.raises(ValueError, match="embargo_pct must be a float in"):
        PurgedGroupTimeSeriesSplit(n_splits=5, embargo_pct=1.0)
    with pytest.raises(ValueError, match="embargo_pct must be a float in"):
        PurgedGroupTimeSeriesSplit(n_splits=5, embargo_pct=-0.1)


def test_purged_split_combinatorial_split_counts() -> None:
    X = np.zeros((100, 2))
    cv_1 = PurgedGroupTimeSeriesSplit(n_splits=5, n_test_groups=1)
    assert cv_1.get_n_splits(X) == 5
    assert len(list(cv_1.split(X))) == 5

    cv_2 = PurgedGroupTimeSeriesSplit(n_splits=5, n_test_groups=2)
    assert cv_2.get_n_splits(X) == math.comb(5, 2)  # 10
    assert len(list(cv_2.split(X))) == 10

    cv_3 = PurgedGroupTimeSeriesSplit(n_splits=6, n_test_groups=3)
    assert cv_3.get_n_splits(X) == math.comb(6, 3)  # 20
    assert len(list(cv_3.split(X))) == 20


def test_purged_split_purging_boundary_exact_exclusion() -> None:
    # 100 samples, 5 equal groups: [0..19], [20..39], [40..59], [60..79], [80..99]
    n_samples = 100
    X = np.arange(n_samples).reshape(-1, 1)
    holding_periods = 5

    cv = PurgedGroupTimeSeriesSplit(
        n_splits=5,
        n_test_groups=1,
        holding_periods=holding_periods,
        embargo_periods=0,
    )

    splits = list(cv.split(X))

    # Test fold 1: test group is group 1 -> indices [20..39]
    train_idx, test_idx = splits[1]
    np.testing.assert_array_equal(test_idx, np.arange(20, 40))

    # In group 0 ([0..19]), samples with start + holding >= 20 overlap with test group 1!
    # For start in [15..19], start + 5 in [20..24] >= 20.
    # Therefore, samples 15, 16, 17, 18, 19 MUST be purged from training set!
    for p in range(15, 20):
        assert p not in train_idx, f"Sample {p} should have been purged due to holding overlap"

    # Samples 0..14 do not overlap: 14 + 5 = 19 < 20.
    for p in range(0, 15):
        assert p in train_idx, f"Sample {p} should be retained in train set"


def test_purged_split_embargo_boundary_exact_exclusion() -> None:
    # 100 samples, 5 groups: [0..19], [20..39], [40..59], [60..79], [80..99]
    n_samples = 100
    X = np.arange(n_samples).reshape(-1, 1)
    embargo_periods = 4

    cv = PurgedGroupTimeSeriesSplit(
        n_splits=5,
        n_test_groups=1,
        holding_periods=0,
        embargo_periods=embargo_periods,
    )

    splits = list(cv.split(X))

    # Test fold 1: test group is [20..39]
    train_idx, test_idx = splits[1]
    np.testing.assert_array_equal(test_idx, np.arange(20, 40))

    # Samples immediately following test group [20..39] within embargo 4:
    # 40, 41, 42, 43 MUST be embargoed (excluded)!
    for e in range(40, 44):
        assert e not in train_idx, f"Sample {e} should have been embargoed"

    # Sample 44 is outside embargo window and should be retained
    assert 44 in train_idx


def test_purged_split_sklearn_cross_val_score_compatibility() -> None:
    rng = np.random.default_rng(42)
    n_samples = 120
    X = rng.normal(size=(n_samples, 5))
    y = X[:, 0] * 2.0 + rng.normal(size=n_samples)

    cv = PurgedGroupTimeSeriesSplit(
        n_splits=4,
        n_test_groups=1,
        holding_periods=5,
        embargo_periods=2,
    )

    scores = cross_val_score(Ridge(alpha=1.0), X, y, cv=cv)
    assert len(scores) == 4
    assert all(np.isfinite(scores))


def test_cpcv_pbo_matches_cscv_when_holding_and_embargo_zero() -> None:
    rng = np.random.default_rng(77)
    df = pd.DataFrame(rng.normal(loc=0.01, scale=0.05, size=(120, 6)), columns=[f"s_{i}" for i in range(6)])

    cpcv_res = combinatorial_purged_cross_validation_pbo(
        df,
        n_splits=6,
        holding_periods=0,
        embargo_periods=0,
    )
    cscv_res = probability_of_backtest_overfitting(
        df,
        n_splits=6,
    )

    assert cpcv_res["pbo"] == pytest.approx(cscv_res["pbo"])
    assert cpcv_res["prob_loss"] == pytest.approx(cscv_res["prob_loss"])
    assert cpcv_res["n_splits"] == cscv_res["n_splits"]
    assert cpcv_res["n_combinations"] == cscv_res["n_combinations"]
    assert cpcv_res["mean_relative_rank"] == pytest.approx(cscv_res["mean_relative_rank"])
    assert cpcv_res["median_relative_rank"] == pytest.approx(cscv_res["median_relative_rank"])
    assert cpcv_res["mean_is_sharpe"] == pytest.approx(cscv_res["mean_is_sharpe"])
    assert cpcv_res["mean_oos_sharpe"] == pytest.approx(cscv_res["mean_oos_sharpe"])
    assert cpcv_res["mean_purged_samples"] == 0.0
    assert cpcv_res["mean_embargoed_samples"] == 0.0


def test_cpcv_pbo_purging_and_embargo_reduces_training_samples() -> None:
    rng = np.random.default_rng(99)
    df = pd.DataFrame(rng.normal(loc=0.02, scale=0.05, size=(160, 4)), columns=[f"strat_{i}" for i in range(4)])

    result = combinatorial_purged_cross_validation_pbo(
        df,
        n_splits=4,
        holding_periods=10,
        embargo_periods=5,
    )

    assert result["holding_periods"] == 10
    assert result["embargo_periods"] == 5
    assert result["mean_purged_samples"] > 0.0
    assert 0.0 <= result["pbo"] <= 1.0
    assert 0.0 <= result["prob_loss"] <= 1.0
    assert result["n_combinations"] == 6  # C(4, 2) = 6
    assert len(result["oos_sharpe_distribution"]) == 6


def test_cpcv_pbo_validates_inputs() -> None:
    valid_df = pd.DataFrame(np.ones((80, 3)), columns=["a", "b", "c"])

    with pytest.raises(TypeError, match="must be a pandas DataFrame"):
        combinatorial_purged_cross_validation_pbo(np.ones((80, 3)))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="n_splits must be an integer >= 4"):
        combinatorial_purged_cross_validation_pbo(valid_df, n_splits=2)

    with pytest.raises(ValueError, match="holding_periods must be an integer >= 0"):
        combinatorial_purged_cross_validation_pbo(valid_df, holding_periods=-1)

    with pytest.raises(ValueError, match="embargo_periods must be an integer >= 0"):
        combinatorial_purged_cross_validation_pbo(valid_df, embargo_periods=-1)
