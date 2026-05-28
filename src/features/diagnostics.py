"""Diagnostic helpers for research factor panels.

This module measures relationships among already-prepared factor panels. It
does not select factors, train models, define strategy logic, connect to a
backtest, fetch data, or make profitability claims.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from features.operators import validate_panel_data


def factor_correlation_matrix(
    factors: dict[str, pd.DataFrame],
    *,
    method: str = "pearson",
    min_periods: int = 1,
) -> pd.DataFrame:
    """Compute pairwise correlations between aligned factor panels.

    Each factor panel is flattened into an aligned date-asset vector. Pairwise
    correlations use only overlapping non-missing observations for each factor
    pair. Missing values are not filled, and panels are not sorted, reindexed,
    normalized, or otherwise transformed.

    The output is diagnostic research infrastructure. It is not a trading
    strategy, backtest integration, factor-selection rule, or profitability
    claim.

    Args:
        factors: Non-empty mapping of factor names to numeric date-indexed
            asset panels.
        method: Correlation method. Supported values are ``"pearson"`` and
            ``"spearman"``.
        min_periods: Minimum number of overlapping valid observations required
            for each factor pair.

    Returns:
        Square DataFrame indexed and columned by factor names in insertion
        order.

    Raises:
        TypeError: If ``factors`` or ``min_periods`` have invalid types, or a
            factor panel fails shared validation.
        ValueError: If ``factors`` is empty, panels are misaligned, ``method``
            is unsupported, ``min_periods`` is less than 1, or any factor pair
            has too few overlapping valid observations.
    """

    if not isinstance(factors, dict):
        raise TypeError("factors must be a dict of factor name to DataFrame")

    if not factors:
        raise ValueError("factors must not be empty")

    if method not in {"pearson", "spearman"}:
        raise ValueError("method must be either 'pearson' or 'spearman'")

    _validate_min_periods(min_periods)

    validated = _validate_factor_panels(factors)
    factor_names = list(validated)
    flattened = {
        name: panel.stack(future_stack=True)
        for name, panel in validated.items()
    }

    result = pd.DataFrame(index=factor_names, columns=factor_names, dtype=float)
    for left_name in factor_names:
        for right_name in factor_names:
            left = flattened[left_name]
            right = flattened[right_name]
            valid_pair = left.notna() & right.notna()
            overlap_count = int(valid_pair.sum())
            if overlap_count < min_periods:
                raise ValueError(
                    f"factor pair {left_name!r}, {right_name!r} has "
                    f"{overlap_count} overlapping observations; "
                    f"min_periods={min_periods}"
                )

            with np.errstate(divide="ignore", invalid="ignore"):
                result.loc[left_name, right_name] = left[valid_pair].corr(
                    right[valid_pair],
                    method=method,
                )

    return result


def _validate_factor_panels(
    factors: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    validated: dict[str, pd.DataFrame] = {}
    reference_index: pd.DatetimeIndex | None = None
    reference_columns: pd.Index | None = None

    for name, factor in factors.items():
        panel = validate_panel_data(factor, name=f"factors[{name!r}]")

        if reference_index is None:
            reference_index = panel.index
            reference_columns = panel.columns
        else:
            if not panel.index.equals(reference_index):
                raise ValueError("all factor panels must have identical indexes")
            if not panel.columns.equals(reference_columns):
                raise ValueError("all factor panels must have identical columns")

        validated[name] = panel

    return validated


def _validate_min_periods(min_periods: int) -> None:
    if isinstance(min_periods, bool) or not isinstance(min_periods, int):
        raise TypeError("min_periods must be an integer")

    if min_periods < 1:
        raise ValueError("min_periods must be at least 1")


__all__ = ["factor_correlation_matrix"]
