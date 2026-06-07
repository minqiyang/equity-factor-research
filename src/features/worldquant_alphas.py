"""Selected WorldQuant-style alpha feature definitions.

This module contains educational research references only. The functions here
define feature calculations, not trading strategies, backtests, portfolio
construction rules, or profitability claims.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from features.operators import delta, rolling_max, rolling_min, validate_panel_data


def alpha_009(close: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """Calculate WorldQuant-style Alpha#009 from close prices.

    This educational reference computes one-period close deltas and applies the
    Alpha#009 sign rule:

    - if all deltas in the trailing ``window`` are positive, return current delta.
    - if all deltas in the trailing ``window`` are negative, return current delta.
    - otherwise, return negative current delta.

    The feature at date ``t`` may use ``close[t]`` and earlier closes only. It is
    known after ``close[t]`` is available; any trading lag or execution timing
    remains the responsibility of a later strategy or backtest layer. The output
    is a research feature, not a complete strategy or evidence of profitability.

    Missing prices are not filled. A missing close value, missing delta endpoint,
    or incomplete trailing delta window produces ``NaN`` for that asset/date.

    Args:
        close: Close-price DataFrame indexed by increasing dates with assets as
            columns. Values must already be numeric; strings are rejected by the
            shared panel validator.
        window: Number of trailing one-period deltas used for the sign rule.
            Defaults to 5.

    Returns:
        A DataFrame of Alpha#009 feature values with the same index and columns
        as ``close``.

    Raises:
        TypeError: If ``close`` is not a valid numeric price panel or ``window``
            is not an integer.
        ValueError: If ``close`` has invalid date alignment or ``window`` is
            less than 1.
    """

    _validate_window(window)
    close_panel = validate_panel_data(close, name="close")

    delta_close = delta(close_panel, periods=1)
    trailing_min = rolling_min(delta_close, window)
    trailing_max = rolling_max(delta_close, window)

    trend_continuation = trailing_min.gt(0.0) | trailing_max.lt(0.0)
    alpha = delta_close.where(trend_continuation, -delta_close)

    valid_inputs = delta_close.notna() & trailing_min.notna() & trailing_max.notna()
    return alpha.where(valid_inputs)


def alpha_012(close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant-style Alpha#012 from close and volume panels.

    This educational reference implements the public Alpha#012 formula:

    ``sign(delta(volume, 1)) * (-1 * delta(close, 1))``

    The feature at date ``t`` may use ``close[t]``, ``volume[t]``, and their
    one-row trailing anchors only. It is known after both ``close[t]`` and
    ``volume[t]`` are available; any trading lag, ranking direction, universe
    selection, execution timing, or backtest interpretation remains the
    responsibility of a later layer. The output is a research feature, not a
    complete strategy or evidence of profitability.

    Missing close or volume endpoints are not filled and produce ``NaN`` for
    the affected asset/date. Zero volume is allowed as validated local market
    data; a zero one-period volume delta contributes a zero sign and therefore
    a zero feature value when the close delta is valid. Negative volume values
    are rejected before calculation.

    Args:
        close: Close-price DataFrame indexed by increasing dates with assets as
            columns. The caller is responsible for documenting whether this is
            raw close, adjusted close, or another reviewed close panel.
        volume: Volume DataFrame with exactly the same index and columns as
            ``close``. Values must be non-negative.

    Returns:
        A DataFrame of Alpha#012 feature values with the same index and columns
        as ``close`` and ``volume``.

    Raises:
        TypeError: If either input is not a valid numeric panel.
        ValueError: If input panels have invalid date alignment, mismatched
            indexes or columns, or negative volume values.
    """

    close_panel, volume_panel = _validate_close_volume_panels(close, volume)
    close_delta = delta(close_panel, periods=1)
    volume_delta = delta(volume_panel, periods=1)

    alpha = np.sign(volume_delta) * (-1.0 * close_delta)
    valid_inputs = close_delta.notna() & volume_delta.notna()
    return alpha.where(valid_inputs)


def _validate_window(window: int) -> None:
    if isinstance(window, bool) or not isinstance(window, int):
        raise TypeError("window must be an integer")

    if window < 1:
        raise ValueError("window must be at least 1")


def _validate_close_volume_panels(
    close: pd.DataFrame,
    volume: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    close_panel = validate_panel_data(close, name="close")
    volume_panel = validate_panel_data(volume, name="volume")

    if not close_panel.index.equals(volume_panel.index):
        raise ValueError("close and volume must have identical indexes")

    if not close_panel.columns.equals(volume_panel.columns):
        raise ValueError("close and volume must have identical columns")

    if (volume_panel < 0.0).any().any():
        raise ValueError("volume must contain non-negative values when present")

    return close_panel, volume_panel


__all__ = ["alpha_009", "alpha_012"]
