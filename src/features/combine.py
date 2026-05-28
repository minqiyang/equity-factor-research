"""Factor combination helpers for research feature panels.

This module combines already-preprocessed factor panels with explicit weights.
It does not normalize raw factors, define portfolio construction, connect to a
backtest, fetch data, or make profitability claims.
"""

from __future__ import annotations

from numbers import Real

import numpy as np
import pandas as pd

from features.operators import validate_panel_data


def combine_factors(
    factors: dict[str, pd.DataFrame],
    weights: dict[str, float],
) -> pd.DataFrame:
    """Combine aligned factor panels with explicit weights.

    Each supplied factor must be a numeric date-indexed asset panel with the
    same dates and columns as every other factor. Missing values are rejected
    under the default strict policy so the caller must make missing-data
    decisions before combination.

    The output is a research feature panel. It is not a trading signal,
    strategy, backtest integration, or profitability claim.

    Args:
        factors: Non-empty mapping of factor names to DataFrames indexed by
            increasing dates with assets as columns.
        weights: Mapping of factor names to finite numeric weights. Keys must
            exactly match ``factors``.

    Returns:
        A DataFrame containing ``sum(weight[name] * factors[name])`` with the
        same index and columns as the input panels.

    Raises:
        TypeError: If inputs have invalid types or weights are non-numeric.
        ValueError: If mappings are empty or mismatched, panels are misaligned,
            factor values contain ``NaN``, or all weights are zero.
    """

    if not isinstance(factors, dict):
        raise TypeError("factors must be a dict of factor name to DataFrame")

    if not factors:
        raise ValueError("factors must not be empty")

    if not isinstance(weights, dict):
        raise TypeError("weights must be a dict of factor name to numeric weight")

    factor_names = set(factors)
    weight_names = set(weights)
    if factor_names != weight_names:
        missing = sorted(repr(name) for name in factor_names - weight_names)
        extra = sorted(repr(name) for name in weight_names - factor_names)
        raise ValueError(
            "weights must exactly match factor names; "
            f"missing weights: {missing}; extra weights: {extra}"
        )

    validated_weights = {
        name: _validate_weight(weight, name=name)
        for name, weight in weights.items()
    }
    if not any(weight != 0.0 for weight in validated_weights.values()):
        raise ValueError("at least one factor weight must be nonzero")

    validated_factors: dict[str, pd.DataFrame] = {}
    reference_index: pd.DatetimeIndex | None = None
    reference_columns: pd.Index | None = None

    for name, factor in factors.items():
        panel = validate_panel_data(factor, name=f"factors[{name!r}]")

        if panel.isna().to_numpy().any():
            raise ValueError(
                f"factors[{name!r}] must not contain NaN values under strict combination policy"
            )

        if reference_index is None:
            reference_index = panel.index
            reference_columns = panel.columns
        else:
            if not panel.index.equals(reference_index):
                raise ValueError("all factor panels must have identical indexes")
            if not panel.columns.equals(reference_columns):
                raise ValueError("all factor panels must have identical columns")

        validated_factors[name] = panel

    result = pd.DataFrame(0.0, index=reference_index, columns=reference_columns)
    for name, panel in validated_factors.items():
        result = result + panel * validated_weights[name]

    return result


def _validate_weight(weight: float, *, name: str) -> float:
    if isinstance(weight, bool) or not isinstance(weight, Real):
        raise TypeError(f"weight for factor {name!r} must be numeric and non-boolean")

    weight_value = float(weight)
    if not np.isfinite(weight_value):
        raise ValueError(f"weight for factor {name!r} must be finite")

    return weight_value


__all__ = ["combine_factors"]
