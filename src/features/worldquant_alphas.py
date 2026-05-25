"""Selected WorldQuant-style alpha feature definitions.

This module contains educational research references only. The functions here
define feature calculations, not trading strategies, backtests, portfolio
construction rules, or profitability claims.
"""

from __future__ import annotations

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


def _validate_window(window: int) -> None:
    if isinstance(window, bool) or not isinstance(window, int):
        raise TypeError("window must be an integer")

    if window < 1:
        raise ValueError("window must be at least 1")


__all__ = ["alpha_009"]
