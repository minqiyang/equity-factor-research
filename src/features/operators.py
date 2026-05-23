"""Reusable point-in-time-safe feature operators.

The functions in this module operate on date-indexed asset panels represented
as pandas DataFrames. Time-series operators use only the current row and
trailing historical rows. They do not sort data, forward-fill missing values,
or convert missing data into synthetic observations.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype


def validate_panel_data(data: pd.DataFrame, *, name: str = "data") -> pd.DataFrame:
    """Validate and return a float copy of a date-indexed asset panel.

    Args:
        data: DataFrame indexed by increasing dates with asset identifiers as
            columns.
        name: Human-readable input name used in error messages.

    Returns:
        A float-typed DataFrame with the same index and columns.

    Raises:
        TypeError: If ``data`` is not a DataFrame, does not use a DatetimeIndex,
            or contains non-numeric or boolean columns.
        ValueError: If the index is unsorted, duplicated, or the panel is empty.

    Notes:
        Missing values in numeric columns are allowed and preserved as ``NaN``.
        Object, string, category, and boolean columns are rejected instead of
        being coerced to numeric values.
    """

    if not isinstance(data, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas DataFrame")

    if not isinstance(data.index, pd.DatetimeIndex):
        raise TypeError(f"{name} must be indexed by a pandas DatetimeIndex")

    if data.empty:
        raise ValueError(f"{name} must not be empty")

    if data.index.has_duplicates:
        raise ValueError(f"{name} index must not contain duplicate dates")

    if not data.index.is_monotonic_increasing:
        raise ValueError(f"{name} index must be sorted in increasing date order")

    invalid_columns = [
        column for column in data.columns if is_bool_dtype(data[column].dtype) or not is_numeric_dtype(data[column].dtype)
    ]
    if invalid_columns:
        raise TypeError(
            f"{name} must contain numeric non-boolean dtypes only; "
            f"invalid columns: {invalid_columns}"
        )

    return data.astype(float)


def delay(data: pd.DataFrame, periods: int = 1) -> pd.DataFrame:
    """Lag panel values by ``periods`` rows.

    Negative periods are rejected because they would expose future values.
    """

    _validate_non_negative_integer(periods, "periods")
    panel = validate_panel_data(data)
    return panel.shift(periods)


def delta(data: pd.DataFrame, periods: int = 1) -> pd.DataFrame:
    """Calculate current value minus the trailing value ``periods`` rows ago."""

    _validate_positive_integer(periods, "periods")
    panel = validate_panel_data(data)
    return panel - panel.shift(periods)


def rolling_mean(data: pd.DataFrame, window: int) -> pd.DataFrame:
    """Calculate trailing rolling mean with full windows only."""

    _validate_positive_integer(window, "window")
    panel = validate_panel_data(data)
    return panel.rolling(window=window, min_periods=window).mean()


def rolling_std(data: pd.DataFrame, window: int, *, ddof: int = 0) -> pd.DataFrame:
    """Calculate trailing rolling standard deviation with full windows only."""

    _validate_positive_integer(window, "window")
    _validate_non_negative_integer(ddof, "ddof")
    panel = validate_panel_data(data)
    return panel.rolling(window=window, min_periods=window).std(ddof=ddof)


def rolling_min(data: pd.DataFrame, window: int) -> pd.DataFrame:
    """Calculate trailing rolling minimum with full windows only."""

    _validate_positive_integer(window, "window")
    panel = validate_panel_data(data)
    return panel.rolling(window=window, min_periods=window).min()


def rolling_max(data: pd.DataFrame, window: int) -> pd.DataFrame:
    """Calculate trailing rolling maximum with full windows only."""

    _validate_positive_integer(window, "window")
    panel = validate_panel_data(data)
    return panel.rolling(window=window, min_periods=window).max()


def rolling_corr(left: pd.DataFrame, right: pd.DataFrame, window: int) -> pd.DataFrame:
    """Calculate asset-wise trailing rolling correlation between matching panels.

    Both inputs must have exactly matching dates and columns. Results require a
    full trailing window of valid paired observations.
    """

    _validate_minimum_integer(window, "window", minimum=2)
    left_panel, right_panel = _validate_matching_panel_data(left, right)
    return left_panel.rolling(window=window, min_periods=window).corr(right_panel)


def rolling_cov(
    left: pd.DataFrame,
    right: pd.DataFrame,
    window: int,
    *,
    ddof: int = 0,
) -> pd.DataFrame:
    """Calculate asset-wise trailing rolling covariance between matching panels.

    Both inputs must have exactly matching dates and columns. Results require a
    full trailing window of valid paired observations.
    """

    _validate_minimum_integer(window, "window", minimum=2)
    _validate_non_negative_integer(ddof, "ddof")
    left_panel, right_panel = _validate_matching_panel_data(left, right)
    return left_panel.rolling(window=window, min_periods=window).cov(right_panel, ddof=ddof)


def cross_sectional_rank(
    data: pd.DataFrame,
    *,
    method: str = "average",
    ascending: bool = True,
) -> pd.DataFrame:
    """Calculate row-wise percentile ranks across assets."""

    panel = validate_panel_data(data)
    return panel.rank(axis=1, method=method, ascending=ascending, pct=True)


def cross_sectional_zscore(data: pd.DataFrame, *, ddof: int = 0) -> pd.DataFrame:
    """Calculate row-wise z-scores across assets.

    Rows with zero cross-sectional standard deviation return ``NaN`` for valid
    entries because zero dispersion cannot support a meaningful z-score.
    """

    _validate_non_negative_integer(ddof, "ddof")
    panel = validate_panel_data(data)
    mean = panel.mean(axis=1, skipna=True)
    std = panel.std(axis=1, skipna=True, ddof=ddof).replace(0.0, np.nan)
    return panel.sub(mean, axis=0).div(std, axis=0)


def winsorize_cross_sectional(
    data: pd.DataFrame,
    *,
    lower_quantile: float = 0.01,
    upper_quantile: float = 0.99,
) -> pd.DataFrame:
    """Clip each cross-section to row-wise lower and upper quantiles."""

    _validate_quantiles(lower_quantile, upper_quantile)
    panel = validate_panel_data(data)
    lower = panel.quantile(lower_quantile, axis=1)
    upper = panel.quantile(upper_quantile, axis=1)
    return panel.clip(lower=lower, upper=upper, axis=0)


def ts_rank(
    data: pd.DataFrame,
    window: int,
    *,
    method: str = "average",
    ascending: bool = True,
) -> pd.DataFrame:
    """Rank the current value inside each asset's full trailing window.

    The percentile rank at date ``t`` uses only values in the trailing window
    ending at ``t``. Missing values inside the required window produce ``NaN``.
    Ties are handled by the pandas rank ``method`` argument, with ``"average"``
    as the default. Ranks use ``pct=True``, so the output is a percentile rank.
    """

    _validate_positive_integer(window, "window")
    panel = validate_panel_data(data)

    def rank_current(window_values: pd.Series) -> float:
        ranks = window_values.rank(method=method, ascending=ascending, pct=True)
        return float(ranks.iloc[-1])

    return panel.rolling(window=window, min_periods=window).apply(rank_current, raw=False)


def signed_power(data: pd.DataFrame, exponent: float) -> pd.DataFrame:
    """Raise absolute values to ``exponent`` while preserving original signs."""

    if exponent <= 0:
        raise ValueError("exponent must be positive")

    panel = validate_panel_data(data)
    return np.sign(panel) * panel.abs().pow(exponent)


def scale(data: pd.DataFrame, *, target_abs_sum: float = 1.0) -> pd.DataFrame:
    """Scale each row so absolute non-missing values sum to ``target_abs_sum``."""

    if target_abs_sum <= 0:
        raise ValueError("target_abs_sum must be positive")

    panel = validate_panel_data(data)
    abs_sum = panel.abs().sum(axis=1, skipna=True).replace(0.0, np.nan)
    return panel.div(abs_sum, axis=0) * target_abs_sum


def safe_divide(numerator: pd.DataFrame, denominator: pd.DataFrame) -> pd.DataFrame:
    """Divide matching panels while returning ``NaN`` for invalid divisions."""

    numerator_panel, denominator_panel = _validate_matching_panel_data(numerator, denominator)
    denominator_panel = denominator_panel.mask(denominator_panel == 0.0)

    with np.errstate(divide="ignore", invalid="ignore"):
        result = numerator_panel / denominator_panel

    return result.replace([np.inf, -np.inf], np.nan)


def _validate_matching_panel_data(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    left_name: str = "left",
    right_name: str = "right",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    left_panel = validate_panel_data(left, name=left_name)
    right_panel = validate_panel_data(right, name=right_name)

    if not left_panel.index.equals(right_panel.index):
        raise ValueError(f"{left_name} and {right_name} must have identical indexes")

    if not left_panel.columns.equals(right_panel.columns):
        raise ValueError(f"{left_name} and {right_name} must have identical columns")

    return left_panel, right_panel


def _validate_positive_integer(value: int, name: str) -> None:
    _validate_minimum_integer(value, name, minimum=1)


def _validate_non_negative_integer(value: int, name: str) -> None:
    _validate_minimum_integer(value, name, minimum=0)


def _validate_minimum_integer(value: int, name: str, *, minimum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")

    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")


def _validate_quantiles(lower_quantile: float, upper_quantile: float) -> None:
    if not 0.0 <= lower_quantile < upper_quantile <= 1.0:
        raise ValueError("quantiles must satisfy 0 <= lower_quantile < upper_quantile <= 1")


__all__ = [
    "cross_sectional_rank",
    "cross_sectional_zscore",
    "delay",
    "delta",
    "rolling_corr",
    "rolling_cov",
    "rolling_max",
    "rolling_mean",
    "rolling_min",
    "rolling_std",
    "safe_divide",
    "scale",
    "signed_power",
    "ts_rank",
    "validate_panel_data",
    "winsorize_cross_sectional",
]
