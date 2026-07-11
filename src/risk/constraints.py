"""Portfolio target-weight constraints for simulated research."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_complex_dtype, is_numeric_dtype


_GROSS_EXPOSURE_TOLERANCE = 1e-12


def apply_long_only_position_cap(
    target_weights: pd.DataFrame,
    *,
    max_position_weight: float,
) -> pd.DataFrame:
    """Clip long-only targets at a per-position maximum without renormalizing."""

    _validate_target_weights(target_weights)
    if (
        isinstance(max_position_weight, (bool, np.bool_))
        or not isinstance(max_position_weight, (int, float, np.integer, np.floating))
        or not np.isfinite(max_position_weight)
        or not 0.0 < float(max_position_weight) <= 1.0
    ):
        raise ValueError(
            "max_position_weight must be greater than 0 and no greater than 1"
        )

    return target_weights.astype(float).clip(upper=float(max_position_weight))


def _validate_target_weights(target_weights: pd.DataFrame) -> None:
    if not isinstance(target_weights, pd.DataFrame):
        raise TypeError("target_weights must be a pandas DataFrame")
    if target_weights.empty:
        raise ValueError("target_weights must not be empty")
    if (
        not isinstance(target_weights.index, pd.DatetimeIndex)
        or target_weights.index.has_duplicates
        or not target_weights.index.is_monotonic_increasing
        or target_weights.columns.has_duplicates
    ):
        raise ValueError(
            "target_weights must have unique assets and unique, increasing dates"
        )
    if any(
        is_bool_dtype(dtype)
        or is_complex_dtype(dtype)
        or not is_numeric_dtype(dtype)
        for dtype in target_weights.dtypes
    ):
        raise TypeError(
            "target_weights must contain finite non-negative real weights"
        )

    values = target_weights.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0.0).any():
        raise ValueError(
            "target_weights must contain finite non-negative real weights"
        )
    if target_weights.sum(axis=1).gt(1.0 + _GROSS_EXPOSURE_TOLERANCE).any():
        raise ValueError("target_weights gross exposure must not exceed 1")
