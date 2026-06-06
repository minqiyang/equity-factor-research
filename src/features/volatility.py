"""Realized volatility feature definitions.

This module contains point-in-time-safe trailing volatility calculations from
adjusted price panels. Feature values are aligned to the signal date and use
only current and historical prices; execution timing remains the responsibility
of a later strategy or backtest layer.
"""

from __future__ import annotations

import pandas as pd

from features.operators import validate_panel_data


DEFAULT_WINDOW_PERIODS = 21
DEFAULT_DDOF = 0


def calculate_realized_volatility(
    prices: pd.DataFrame,
    *,
    window_periods: int = DEFAULT_WINDOW_PERIODS,
    ddof: int = DEFAULT_DDOF,
) -> pd.DataFrame:
    """Calculate trailing realized volatility from adjusted prices.

    For each asset and signal date ``t``, this helper first computes simple
    one-period returns using adjacent prices:

    ``price[t] / price[t - 1] - 1``

    It then calculates the rolling standard deviation of those returns over a
    full trailing window ending at ``t``. The result is not annualized; a later
    research or reporting layer must apply any explicit scaling convention.

    Missing prices are not filled. A return is treated as missing when either
    adjacent price anchor is missing or non-positive, and any missing return
    inside the required trailing window produces ``NaN`` for that date.

    Args:
        prices: Price DataFrame indexed by increasing dates with asset
            identifiers as columns. Prices should be adjusted for splits and
            dividends if total-return volatility is desired.
        window_periods: Number of trailing one-period returns required for
            each volatility estimate. Defaults to 21 rows.
        ddof: Delta degrees of freedom passed to the rolling standard
            deviation calculation. Defaults to 0 for population volatility.

    Returns:
        A DataFrame of trailing realized volatility values with the same index
        and columns as ``prices``.

    Raises:
        TypeError: If ``prices`` is not a pandas DataFrame, does not use a
            DatetimeIndex, contains non-numeric columns, or if window/ddof
            settings are not integers.
        ValueError: If dates are duplicated or not sorted, the panel is empty,
            or if the window/ddof settings are invalid.
    """

    _validate_window_periods(window_periods)
    _validate_ddof(ddof, window_periods=window_periods)
    price_panel = validate_panel_data(prices, name="prices")

    previous_prices = price_panel.shift(1)
    valid_return_anchors = price_panel.gt(0.0) & previous_prices.gt(0.0)
    returns = (price_panel / previous_prices - 1.0).where(valid_return_anchors)

    return returns.rolling(window=window_periods, min_periods=window_periods).std(
        ddof=ddof,
    )


def _validate_window_periods(window_periods: int) -> None:
    if isinstance(window_periods, bool) or not isinstance(window_periods, int):
        raise TypeError("window_periods must be an integer")

    if window_periods < 1:
        raise ValueError("window_periods must be at least 1")


def _validate_ddof(ddof: int, *, window_periods: int) -> None:
    if isinstance(ddof, bool) or not isinstance(ddof, int):
        raise TypeError("ddof must be an integer")

    if ddof < 0:
        raise ValueError("ddof must be at least 0")

    if ddof >= window_periods:
        raise ValueError("ddof must be less than window_periods")


__all__ = [
    "DEFAULT_DDOF",
    "DEFAULT_WINDOW_PERIODS",
    "calculate_realized_volatility",
]
