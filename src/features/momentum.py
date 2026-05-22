"""Momentum feature definitions.

This module contains point-in-time-safe momentum calculations, starting with
12-1 month momentum. Feature values are aligned so that all inputs are known before
the portfolio formation or execution date.
"""

from __future__ import annotations

import pandas as pd


DEFAULT_LOOKBACK_PERIODS = 252
DEFAULT_SKIP_PERIODS = 21


def calculate_12_1_momentum(
    prices: pd.DataFrame,
    *,
    lookback_periods: int = DEFAULT_LOOKBACK_PERIODS,
    skip_periods: int = DEFAULT_SKIP_PERIODS,
) -> pd.DataFrame:
    """Calculate trailing 12-1 momentum scores from adjusted prices.

    For each asset and signal date ``t``, the score is:

    ``price[t - skip_periods] / price[t - lookback_periods] - 1``

    With the defaults, ``lookback_periods=252`` and ``skip_periods=21`` use
    approximately one trading year of history while skipping the most recent
    trading month. The feature at date ``t`` uses only prices dated on or before
    ``t`` and explicitly shifts both price anchors backward to avoid look-ahead
    bias. The resulting value is suitable for cross-sectional ranking on the
    signal date, with execution timing handled by a later strategy or backtest
    layer.

    Missing prices are not forward-filled. If either required anchor price is
    missing or non-positive, the corresponding momentum score is ``NaN``.

    Args:
        prices: Price DataFrame indexed by increasing dates with asset tickers
            as columns. Prices should be adjusted for splits and dividends if
            total-return momentum is desired.
        lookback_periods: Number of rows back from the signal date to the start
            price anchor. Defaults to 252 trading days.
        skip_periods: Number of recent rows to skip before the end price anchor.
            Defaults to 21 trading days.

    Returns:
        A DataFrame of momentum scores with the same index and columns as
        ``prices``.

    Raises:
        TypeError: If ``prices`` is not a pandas DataFrame or does not use a
            DatetimeIndex.
        ValueError: If dates are duplicated or not sorted, or if the lookback
            and skip windows are invalid.
    """

    _validate_inputs(prices, lookback_periods, skip_periods)

    numeric_prices = prices.astype(float)
    start_prices = numeric_prices.shift(lookback_periods)
    end_prices = numeric_prices.shift(skip_periods)

    valid_anchors = start_prices.gt(0.0) & end_prices.gt(0.0)
    momentum = end_prices / start_prices - 1.0

    return momentum.where(valid_anchors)


def _validate_inputs(
    prices: pd.DataFrame,
    lookback_periods: int,
    skip_periods: int,
) -> None:
    if not isinstance(prices, pd.DataFrame):
        raise TypeError("prices must be a pandas DataFrame")

    if not isinstance(prices.index, pd.DatetimeIndex):
        raise TypeError("prices must be indexed by a pandas DatetimeIndex")

    if prices.index.has_duplicates:
        raise ValueError("prices index must not contain duplicate dates")

    if not prices.index.is_monotonic_increasing:
        raise ValueError("prices index must be sorted in increasing date order")

    if lookback_periods <= 0:
        raise ValueError("lookback_periods must be positive")

    if skip_periods < 0:
        raise ValueError("skip_periods must be non-negative")

    if lookback_periods <= skip_periods:
        raise ValueError("lookback_periods must be greater than skip_periods")
