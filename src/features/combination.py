"""Multi-factor combination helpers for research feature panels.

This module standardizes already-computed factor panels cross-sectionally and
combines them with equal weights or supplied IC weights. It does not estimate
IC, select portfolios, connect to a backtest, fetch data, or make
profitability claims.
"""

from __future__ import annotations

from numbers import Real

import numpy as np
import pandas as pd

from features.operators import cross_sectional_zscore, validate_panel_data


def equal_weighted_composite(factors: list[pd.DataFrame]) -> pd.DataFrame:
    """Average cross-sectional z-scores of aligned factor panels.

    Each factor is standardized row-wise. The composite at date ``t`` is the
    equal-weight average of those z-scores across factors, using only assets
    and factors that are non-missing at ``t``. The average at a cell uses the
    count of finite factor z-scores at that cell.

    Args:
        factors: Non-empty list of numeric date-indexed asset panels with
            identical indexes and columns.

    Returns:
        A DataFrame of equal-weighted z-score composites with the same index
        and columns as the input panels.
    """

    validated = _validate_factor_list(factors)
    standardized = [cross_sectional_zscore(panel) for panel in validated]
    weights = np.ones(len(standardized), dtype=float)
    return _weighted_average(standardized, weights)


def ic_weighted_composite(
    factors: list[pd.DataFrame],
    weights: list[float] | pd.Series,
) -> pd.DataFrame:
    """Average cross-sectional z-scores with supplied IC weights.

    ``weights`` is a historical or trailing IC vector supplied by the caller,
    one value per factor, in the same order as ``factors``. Negative weights
    invert the corresponding z-score. Missing factor cells are omitted from
    that date-asset average and the remaining absolute weights are
    renormalized.

    Args:
        factors: Non-empty list of numeric date-indexed asset panels with
            identical indexes and columns.
        weights: Finite numeric IC weights, either a list or a one-dimensional
            Series whose length matches ``factors``.

    Returns:
        A DataFrame of IC-weighted z-score composites with the same index and
        columns as the input panels.
    """

    validated = _validate_factor_list(factors)
    weight_values = _coerce_weights(weights, n_factors=len(validated))
    standardized = [cross_sectional_zscore(panel) for panel in validated]
    return _weighted_average(standardized, weight_values)


def _validate_factor_list(factors: list[pd.DataFrame]) -> list[pd.DataFrame]:
    if not isinstance(factors, list):
        raise TypeError("factors must be a list of DataFrames")

    if not factors:
        raise ValueError("factors must not be empty")

    validated: list[pd.DataFrame] = []
    reference_index: pd.DatetimeIndex | None = None
    reference_columns: pd.Index | None = None

    for position, factor in enumerate(factors):
        panel = validate_panel_data(factor, name=f"factors[{position}]")
        if reference_index is None:
            reference_index = panel.index
            reference_columns = panel.columns
        else:
            if not panel.index.equals(reference_index):
                raise ValueError("all factor panels must have identical indexes")
            if not panel.columns.equals(reference_columns):
                raise ValueError("all factor panels must have identical columns")
        validated.append(panel)

    return validated


def _coerce_weights(weights: list[float] | pd.Series, *, n_factors: int) -> np.ndarray:
    if isinstance(weights, pd.Series):
        if weights.ndim != 1:
            raise ValueError("weights Series must be one-dimensional")
        raw_values = weights.to_list()
    elif isinstance(weights, list):
        raw_values = weights
    else:
        raise TypeError("weights must be a list of floats or a pandas Series")

    if len(raw_values) != n_factors:
        raise ValueError("weights must have one value per factor")

    values = np.array(
        [
            _validate_weight(weight, position=position)
            for position, weight in enumerate(raw_values)
        ],
        dtype=float,
    )
    if not np.any(values != 0.0):
        raise ValueError("at least one factor weight must be nonzero")
    return values


def _validate_weight(weight: float, *, position: int) -> float:
    if isinstance(weight, bool) or not isinstance(weight, Real):
        raise TypeError(f"weight at position {position} must be numeric and non-boolean")

    weight_value = float(weight)
    if not np.isfinite(weight_value):
        raise ValueError(f"weight at position {position} must be finite")
    return weight_value


def _weighted_average(panels: list[pd.DataFrame], weights: np.ndarray) -> pd.DataFrame:
    stacked = np.stack([panel.to_numpy(dtype=float) for panel in panels], axis=0)
    weight = weights.reshape(-1, 1, 1)
    valid = np.isfinite(stacked)
    numerator = np.nansum(np.where(valid, stacked * weight, 0.0), axis=0)
    denominator = np.sum(np.where(valid, np.abs(weight), 0.0), axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        values = numerator / np.where(denominator == 0.0, np.nan, denominator)
    return pd.DataFrame(values, index=panels[0].index, columns=panels[0].columns)


__all__ = ["equal_weighted_composite", "ic_weighted_composite"]
