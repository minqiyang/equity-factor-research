import numpy as np
import pandas as pd
import pytest

from features.regime import (
    detect_market_trend_regime,
    detect_market_volatility_regime,
    regime_switching_factor_composite,
)


def test_detect_market_volatility_regime_causality() -> None:
    dates = pd.bdate_range("2021-01-04", periods=100)
    rng = np.random.default_rng(42)
    returns = pd.Series(rng.normal(0.0, 0.01, size=100), index=dates)

    regime_base = detect_market_volatility_regime(returns, window=20, min_periods=10)

    # Mutate future returns from index 50 onwards
    mutated_returns = returns.copy()
    mutated_returns.iloc[50:] = 0.5

    regime_mutated = detect_market_volatility_regime(
        mutated_returns, window=20, min_periods=10
    )

    # Regimes strictly before index 50 must be identical
    pd.testing.assert_series_equal(regime_base.iloc[:50], regime_mutated.iloc[:50])


def test_detect_market_trend_regime_causality() -> None:
    dates = pd.bdate_range("2021-01-04", periods=100)
    rng = np.random.default_rng(42)
    returns = pd.Series(rng.normal(0.001, 0.01, size=100), index=dates)

    trend_base = detect_market_trend_regime(returns, window=20, min_periods=10)

    mutated_returns = returns.copy()
    mutated_returns.iloc[50:] = -0.1

    trend_mutated = detect_market_trend_regime(
        mutated_returns, window=20, min_periods=10
    )

    pd.testing.assert_series_equal(trend_base.iloc[:50], trend_mutated.iloc[:50])


def test_detect_market_volatility_regime_synthetic_dynamics() -> None:
    dates = pd.bdate_range("2021-01-04", periods=100)
    # First 50 days low volatility, next 50 days high volatility
    low_vol = np.full(50, 0.001)
    # Alternating slight move for non-zero variance
    low_vol[::2] = -0.001
    high_vol = np.full(50, 0.05)
    high_vol[::2] = -0.05

    returns = pd.Series(np.concatenate([low_vol, high_vol]), index=dates)
    regime = detect_market_volatility_regime(returns, window=10, min_periods=5)

    assert regime.iloc[:4].isna().all()
    # During low vol, expanding median catches up, so it stays mostly 0
    assert (regime.iloc[5:45] == 0.0).all()
    # Once high vol kicks in, rolling vol jumps well above historical expanding median
    assert (regime.iloc[55:] == 1.0).all()


def test_detect_market_trend_regime_synthetic_dynamics() -> None:
    dates = pd.bdate_range("2021-01-04", periods=40)
    bull_returns = pd.Series(0.01, index=dates)
    bear_returns = pd.Series(-0.01, index=dates)

    bull_regime = detect_market_trend_regime(bull_returns, window=10, min_periods=5)
    bear_regime = detect_market_trend_regime(bear_returns, window=10, min_periods=5)

    assert bull_regime.iloc[:4].isna().all()
    assert (bull_regime.iloc[4:] == 1.0).all()
    assert bear_regime.iloc[:4].isna().all()
    assert (bear_regime.iloc[4:] == 0.0).all()


def test_regime_switching_factor_composite_convex_blending() -> None:
    dates = pd.bdate_range("2021-01-04", periods=10)
    assets = ["A", "B", "C"]
    # Low factor: [1, 2, 3] across assets
    f_low = pd.DataFrame(
        np.tile([1.0, 2.0, 3.0], (10, 1)),
        index=dates,
        columns=assets,
    )
    # High factor: [3, 2, 1] across assets
    f_high = pd.DataFrame(
        np.tile([3.0, 2.0, 1.0], (10, 1)),
        index=dates,
        columns=assets,
    )

    # Regime series: 0.0 for first 5 dates, 1.0 for last 5 dates
    regime = pd.Series([0.0] * 5 + [1.0] * 5, index=dates)

    # With signal_lag_periods=1, date 0 has no lagged regime -> default 0.0
    # date 1..5 have lagged regime 0.0
    # date 6..9 have lagged regime 1.0
    composite = regime_switching_factor_composite(
        f_low, f_high, regime, signal_lag_periods=1
    )

    # Verify z-scoring: for [1, 2, 3], mean 2, std 1 -> [-1, 0, 1]
    # for [3, 2, 1], mean 2, std 1 -> [1, 0, -1]
    np.testing.assert_allclose(
        composite.iloc[0:6].to_numpy(), np.tile([-1.0, 0.0, 1.0], (6, 1)), atol=1e-10
    )
    np.testing.assert_allclose(
        composite.iloc[6:].to_numpy(), np.tile([1.0, 0.0, -1.0], (4, 1)), atol=1e-10
    )


def test_regime_switching_factor_composite_causality_mutation() -> None:
    dates = pd.bdate_range("2021-01-04", periods=20)
    assets = ["A", "B", "C"]
    rng = np.random.default_rng(123)
    f_low = pd.DataFrame(rng.normal(size=(20, 3)), index=dates, columns=assets)
    f_high = pd.DataFrame(rng.normal(size=(20, 3)), index=dates, columns=assets)
    regime = pd.Series([0.0] * 10 + [1.0] * 10, index=dates)

    base_comp = regime_switching_factor_composite(
        f_low, f_high, regime, signal_lag_periods=1
    )

    # Mutate f_high, f_low, and regime from index 10 onwards
    f_low_mut = f_low.copy()
    f_high_mut = f_high.copy()
    regime_mut = regime.copy()
    f_low_mut.iloc[10:] *= 10.0
    f_high_mut.iloc[10:] *= 10.0
    regime_mut.iloc[10:] = 0.5

    mut_comp = regime_switching_factor_composite(
        f_low_mut, f_high_mut, regime_mut, signal_lag_periods=1
    )

    # Rows 0..9 must be strictly identical
    pd.testing.assert_frame_equal(base_comp.iloc[:10], mut_comp.iloc[:10])


def test_regime_invalid_inputs() -> None:
    with pytest.raises(TypeError):
        detect_market_volatility_regime([1.0, 2.0])  # type: ignore

    with pytest.raises(ValueError):
        detect_market_volatility_regime(pd.Series([1.0, 2.0]), window=0)

    with pytest.raises(ValueError):
        detect_market_volatility_regime(pd.Series([1.0, 2.0]), window=5, min_periods=10)

    with pytest.raises(TypeError):
        detect_market_trend_regime([1.0, 2.0])  # type: ignore

    with pytest.raises(ValueError):
        detect_market_trend_regime(pd.Series([1.0, 2.0]), window=0)

    with pytest.raises(TypeError):
        regime_switching_factor_composite(pd.DataFrame(), "invalid", pd.Series())  # type: ignore
