"""Market regime detection and regime-conditional factor allocation.

This module provides causal, lookahead-free market regime detection functions
(e.g., volatility regime, trend/momentum regime) and a dynamic regime-switching
composite builder that dynamically shifts factor allocations between growth/momentum
and defensive/neutralized factor styles.
"""

from __future__ import annotations

from numbers import Integral
import numpy as np
import pandas as pd


def detect_market_volatility_regime(
    market_returns: pd.Series,
    window: int = 60,
    min_periods: int = 20,
) -> pd.Series:
    """Detect market volatility regime using trailing rolling standard deviation.

    For each timestamp t, computes the rolling standard deviation of market_returns
    over the trailing `window` periods (with at least `min_periods` observations).
    Compares the current rolling volatility to its trailing historical expanding median
    (calculated strictly using information through t, avoiding lookahead).

    Returns a float indicator where:
    - 1.0 indicates a HIGH_VOLATILITY regime (current rolling vol > trailing expanding median).
    - 0.0 indicates a LOW_VOLATILITY regime (current rolling vol <= trailing expanding median).
    - NaN where insufficient history exists.
    """
    if not isinstance(market_returns, pd.Series):
        raise TypeError(
            f"market_returns must be a pd.Series, got {type(market_returns)}"
        )
    if window <= 0 or min_periods <= 0:
        raise ValueError("window and min_periods must be strictly positive")
    if min_periods > window:
        raise ValueError("min_periods cannot exceed window")

    rolling_vol = market_returns.rolling(window=window, min_periods=min_periods).std()
    expanding_median = rolling_vol.expanding(min_periods=1).median()

    regime = pd.Series(np.nan, index=market_returns.index, dtype=float)
    valid_mask = rolling_vol.notna() & expanding_median.notna()
    regime[valid_mask] = (
        rolling_vol[valid_mask] > expanding_median[valid_mask]
    ).astype(float)
    return regime


def detect_market_trend_regime(
    market_returns: pd.Series,
    window: int = 60,
    min_periods: int = 20,
) -> pd.Series:
    """Detect market trend/direction regime using trailing cumulative return.

    For each timestamp t, computes cumulative return over the trailing `window`.
    - 1.0 indicates a BULL regime (cumulative return > 0.0).
    - 0.0 indicates a BEAR regime (cumulative return <= 0.0).
    - NaN where insufficient history exists.
    """
    if not isinstance(market_returns, pd.Series):
        raise TypeError(
            f"market_returns must be a pd.Series, got {type(market_returns)}"
        )
    if window <= 0 or min_periods <= 0:
        raise ValueError("window and min_periods must be strictly positive")
    if min_periods > window:
        raise ValueError("min_periods cannot exceed window")

    log_1p = np.log1p(market_returns)
    rolling_log_return = log_1p.rolling(window=window, min_periods=min_periods).sum()
    rolling_cum_return = np.expm1(rolling_log_return)

    regime = pd.Series(np.nan, index=market_returns.index, dtype=float)
    valid_mask = rolling_cum_return.notna()
    regime[valid_mask] = (rolling_cum_return[valid_mask] > 0.0).astype(float)
    return regime


def regime_switching_factor_composite(
    factor_low_regime: pd.DataFrame,
    factor_high_regime: pd.DataFrame,
    regime_indicator: pd.Series,
    signal_lag_periods: int = 1,
) -> pd.DataFrame:
    """Dynamically blend two factor panels based on a lagged regime indicator.

    The caller supplies causal parent panels. The regime_indicator is lagged by `signal_lag_periods`
    (default 1) so the regime state evaluated at close of t - lag governs factor
    weights established at t.

    When lagged regime_indicator is 0.0 (or NaN fallback), factor_low_regime is selected.
    When lagged regime_indicator is 1.0, factor_high_regime is selected.
    For continuous indicators in (0.0, 1.0), convex combination is applied:
    (1 - lambda) * factor_low + lambda * factor_high.
    Binary states require the selected parent. Fractional states require both
    parents. Missing parent cells remain unavailable; observed constant rows
    have zero standardized scores. Missing regime states select the low parent.
    """
    if isinstance(signal_lag_periods, (bool, np.bool_)) or not isinstance(signal_lag_periods, Integral) or signal_lag_periods < 1:
        raise ValueError("signal_lag_periods must be a non-boolean integer of at least 1")
    if not isinstance(factor_low_regime, pd.DataFrame) or not isinstance(
        factor_high_regime, pd.DataFrame
    ):
        raise TypeError("factor panels must be pd.DataFrame")
    if not isinstance(regime_indicator, pd.Series):
        raise TypeError("regime_indicator must be a pd.Series")
    if not factor_low_regime.index.equals(
        factor_high_regime.index
    ) or not factor_low_regime.columns.equals(factor_high_regime.columns):
        raise ValueError(
            "factor_low_regime and factor_high_regime must have identical index and columns"
        )

    if (
        not isinstance(factor_low_regime.index, pd.DatetimeIndex)
        or factor_low_regime.index.has_duplicates
        or not factor_low_regime.index.is_monotonic_increasing
        or factor_low_regime.columns.has_duplicates
        or not regime_indicator.index.equals(factor_low_regime.index)
    ):
        raise ValueError("regime and factor dates must be aligned, unique, and increasing")
    observed_regime = regime_indicator.dropna()
    if not pd.api.types.is_numeric_dtype(observed_regime.dtype) or not np.isfinite(observed_regime).all() or not observed_regime.between(0.0, 1.0).all():
        raise ValueError("observed regime values must be finite and in [0, 1]")

    lagged_regime = regime_indicator.shift(signal_lag_periods)
    aligned_regime = lagged_regime.reindex(factor_low_regime.index)

    def _zscore(df: pd.DataFrame) -> pd.DataFrame:
        mean = df.mean(axis=1)
        std = df.std(axis=1)
        std = std.mask(std.eq(0.0) | df.count(axis=1).eq(1), 1.0)
        z = df.sub(mean, axis=0).div(std, axis=0)
        return z

    z_low = _zscore(factor_low_regime)
    z_high = _zscore(factor_high_regime)

    regime_weights = pd.DataFrame(
        np.repeat(
            aligned_regime.to_numpy()[:, np.newaxis], factor_low_regime.shape[1], axis=1
        ),
        index=factor_low_regime.index,
        columns=factor_low_regime.columns,
    )

    regime_weights = regime_weights.fillna(0.0)
    composite = (1.0 - regime_weights) * z_low + regime_weights * z_high
    composite = composite.where(regime_weights.ne(0.0), z_low)
    composite = composite.where(regime_weights.ne(1.0), z_high)
    return composite
