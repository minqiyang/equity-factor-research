"""Short-term reversal feature definitions.

This module contains point-in-time-safe reversal calculations from adjusted
price panels. Feature values are aligned to the signal date and use only the
current and trailing historical prices; execution timing remains the
responsibility of a later strategy or backtest layer.
"""

from __future__ import annotations

import pandas as pd

from features.operators import validate_panel_data


DEFAULT_LOOKBACK_PERIODS = 5


def calculate_short_term_reversal(
    prices: pd.DataFrame,
    *,
    lookback_periods: int = DEFAULT_LOOKBACK_PERIODS,
) -> pd.DataFrame:
    """Calculate short-term reversal scores from adjusted prices.

    For each asset and signal date ``t``, the trailing return is:

    ``price[t] / price[t - lookback_periods] - 1``

    The reversal score is the negative of that trailing return. With this
    convention, assets with lower recent returns receive higher reversal scores
    for cross-sectional ranking. The score uses only prices dated on or before
    the signal date; a later strategy or backtest layer must still decide
    execution timing and signal lag.

    Missing prices are not filled. If either price anchor is missing or
    non-positive, the corresponding reversal score is ``NaN``.

    Args:
        prices: Price DataFrame indexed by increasing dates with asset
            identifiers as columns. Prices should be adjusted for splits and
            dividends if total-return reversal is desired.
        lookback_periods: Number of rows back from the signal date to the
            trailing price anchor. Defaults to five rows.

    Returns:
        A DataFrame of reversal scores with the same index and columns as
        ``prices``.

    Raises:
        TypeError: If ``prices`` is not a pandas DataFrame, does not use a
            DatetimeIndex, or contains non-numeric columns.
        ValueError: If dates are duplicated or not sorted, or if the lookback
            window is invalid.
    """

    _validate_lookback_periods(lookback_periods)
    price_panel = validate_panel_data(prices, name="prices")

    trailing_prices = price_panel.shift(lookback_periods)
    valid_anchors = price_panel.gt(0.0) & trailing_prices.gt(0.0)
    trailing_returns = price_panel / trailing_prices - 1.0
    reversal = -trailing_returns

    return reversal.where(valid_anchors)


def _validate_lookback_periods(lookback_periods: int) -> None:
    if isinstance(lookback_periods, bool) or not isinstance(lookback_periods, int):
        raise TypeError("lookback_periods must be an integer")

    if lookback_periods < 1:
        raise ValueError("lookback_periods must be at least 1")


__all__ = [
    "DEFAULT_LOOKBACK_PERIODS",
    "calculate_short_term_reversal",
]
