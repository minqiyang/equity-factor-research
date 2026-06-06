"""Synthetic-first liquidity eligibility helpers.

This module creates date-asset eligibility masks from already-validated local
or synthetic panels. It does not fetch data, select a portfolio, run a
backtest, connect to brokerage or execution systems, or make profitability
claims.
"""

from __future__ import annotations

import math

import pandas as pd

from features.operators import validate_panel_data


def rolling_average_daily_volume(
    volume: pd.DataFrame,
    *,
    window: int,
) -> pd.DataFrame:
    """Calculate trailing average daily volume with full windows only.

    Missing values are not filled. A window containing any missing volume value
    produces ``NaN`` for that asset/date.
    """

    _validate_positive_integer(window, "window")
    volume_panel = _validate_volume_panel(volume)
    return volume_panel.rolling(window=window, min_periods=window).mean()


def rolling_average_dollar_volume(
    price: pd.DataFrame,
    volume: pd.DataFrame,
    *,
    window: int,
) -> pd.DataFrame:
    """Calculate trailing average dollar volume with full windows only."""

    _validate_positive_integer(window, "window")
    price_panel, volume_panel = _validate_price_volume_panels(price, volume)
    dollar_volume = price_panel * volume_panel
    return dollar_volume.rolling(window=window, min_periods=window).mean()


def average_daily_volume_eligibility(
    volume: pd.DataFrame,
    *,
    window: int,
    min_average_volume: float,
    eligibility_lag: int = 1,
    require_positive_volume_window: bool = True,
) -> pd.DataFrame:
    """Return a lagged eligibility mask from rolling average volume.

    The threshold is evaluated on observation date ``t`` and becomes eligible
    only after ``eligibility_lag`` rows. The default lag of one row means
    liquidity observed through date ``t`` can first affect eligibility on date
    ``t+1``. Warm-up periods, missing rolling values, and windows containing
    zero volume are ineligible by default.
    """

    _validate_positive_integer(eligibility_lag, "eligibility_lag")
    _validate_positive_threshold(min_average_volume, "min_average_volume")
    _validate_bool(require_positive_volume_window, "require_positive_volume_window")

    volume_panel = _validate_volume_panel(volume)
    metric = rolling_average_daily_volume(volume_panel, window=window)
    return _lagged_threshold_eligibility(
        metric,
        volume_panel=volume_panel,
        window=window,
        threshold=float(min_average_volume),
        eligibility_lag=eligibility_lag,
        require_positive_volume_window=require_positive_volume_window,
    )


def average_dollar_volume_eligibility(
    price: pd.DataFrame,
    volume: pd.DataFrame,
    *,
    window: int,
    min_average_dollar_volume: float,
    eligibility_lag: int = 1,
    require_positive_volume_window: bool = True,
) -> pd.DataFrame:
    """Return a lagged eligibility mask from rolling average dollar volume."""

    _validate_positive_integer(eligibility_lag, "eligibility_lag")
    _validate_positive_threshold(
        min_average_dollar_volume,
        "min_average_dollar_volume",
    )
    _validate_bool(require_positive_volume_window, "require_positive_volume_window")

    price_panel, volume_panel = _validate_price_volume_panels(price, volume)
    metric = rolling_average_dollar_volume(price_panel, volume_panel, window=window)
    return _lagged_threshold_eligibility(
        metric,
        volume_panel=volume_panel,
        window=window,
        threshold=float(min_average_dollar_volume),
        eligibility_lag=eligibility_lag,
        require_positive_volume_window=require_positive_volume_window,
    )


def _lagged_threshold_eligibility(
    metric: pd.DataFrame,
    *,
    volume_panel: pd.DataFrame,
    window: int,
    threshold: float,
    eligibility_lag: int,
    require_positive_volume_window: bool,
) -> pd.DataFrame:
    eligible_on_observation_date = metric >= threshold
    if require_positive_volume_window:
        eligible_on_observation_date = (
            eligible_on_observation_date
            & _full_positive_volume_window(volume_panel, window=window)
        )

    return eligible_on_observation_date.shift(
        eligibility_lag,
        fill_value=False,
    ).astype(bool)


def _full_positive_volume_window(volume_panel: pd.DataFrame, *, window: int) -> pd.DataFrame:
    positive_volume = volume_panel > 0.0
    positive_count = positive_volume.rolling(window=window, min_periods=window).sum()
    return positive_count == float(window)


def _validate_price_volume_panels(
    price: pd.DataFrame,
    volume: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    price_panel = validate_panel_data(price, name="price")
    volume_panel = _validate_volume_panel(volume)

    if not price_panel.index.equals(volume_panel.index):
        raise ValueError("price and volume must have identical indexes")

    if not price_panel.columns.equals(volume_panel.columns):
        raise ValueError("price and volume must have identical columns")

    if (price_panel <= 0.0).any().any():
        raise ValueError("price must contain positive values when present")

    return price_panel, volume_panel


def _validate_volume_panel(volume: pd.DataFrame) -> pd.DataFrame:
    volume_panel = validate_panel_data(volume, name="volume")
    if (volume_panel < 0.0).any().any():
        raise ValueError("volume must contain non-negative values when present")
    return volume_panel


def _validate_positive_integer(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")

    if value < 1:
        raise ValueError(f"{name} must be at least 1")


def _validate_positive_threshold(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")

    if not math.isfinite(float(value)) or float(value) <= 0.0:
        raise ValueError(f"{name} must be a positive finite value")


def _validate_bool(value: bool, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a bool")


__all__ = [
    "average_daily_volume_eligibility",
    "average_dollar_volume_eligibility",
    "rolling_average_daily_volume",
    "rolling_average_dollar_volume",
]
