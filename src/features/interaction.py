"""Cross-factor interaction and non-linear feature models.

This module provides cross-sectional bivariate factor interactions, including
standardized product interactions, conditional quantile-rank interactions
(double-sorts), and quadrant regime indicators.

All calculations are strictly cross-sectional per date, with zero lookahead.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from features.operators import cross_sectional_zscore, validate_panel_data


def factor_product_interaction(
    factor_a: pd.DataFrame,
    factor_b: pd.DataFrame,
    *,
    standardize_inputs: bool = True,
    standardize_output: bool = True,
) -> pd.DataFrame:
    """Compute cross-sectional product interaction of two factor panels.

    Z(f_a) * Z(f_b) captures the non-linear synergy between two factors
    (e.g., Value * Momentum or Quality * Volatility).

    Args:
        factor_a: First date-indexed asset panel.
        factor_b: Second date-indexed asset panel with identical index and columns.
        standardize_inputs: If True (default), standardizes each factor cross-sectionally
            (z-score) before multiplication.
        standardize_output: If True (default), standardizes the resulting interaction
            product cross-sectionally.

    Returns:
        A DataFrame of interaction values with the same shape, index, and columns.
    """
    panel_a = validate_panel_data(factor_a, name="factor_a")
    panel_b = validate_panel_data(factor_b, name="factor_b")

    if not panel_a.index.equals(panel_b.index):
        raise ValueError("factor_a and factor_b must have identical date indexes")
    if not panel_a.columns.equals(panel_b.columns):
        raise ValueError("factor_a and factor_b must have identical asset columns")

    za = cross_sectional_zscore(panel_a) if standardize_inputs else panel_a
    zb = cross_sectional_zscore(panel_b) if standardize_inputs else panel_b

    product = za * zb
    if standardize_output:
        return cross_sectional_zscore(product)
    return product


def conditional_factor_rank(
    conditioning_factor: pd.DataFrame,
    target_factor: pd.DataFrame,
    *,
    n_bins: int = 5,
) -> pd.DataFrame:
    """Compute conditional cross-sectional rank of target_factor within bins of conditioning_factor.

    Implements cross-sectional double-sorting: on each date, assets are partitioned
    into `n_bins` quantile buckets based on `conditioning_factor`. Within each bucket,
    assets are ranked by `target_factor`.

    The resulting conditional rank isolates the incremental predictive power of
    `target_factor` independent of `conditioning_factor`.

    Args:
        conditioning_factor: Primary sorting factor panel (e.g., Size or Volatility).
        target_factor: Secondary factor panel to be conditionally evaluated.
        n_bins: Number of quantile buckets for the conditioning factor (default 5, min 2).

    Returns:
        A DataFrame of conditional ranks normalized to [0, 1] per bucket, or NaN
        where either input is NaN.
    """
    if not isinstance(n_bins, int) or n_bins < 2:
        raise ValueError("n_bins must be an integer >= 2")

    cond = validate_panel_data(conditioning_factor, name="conditioning_factor")
    target = validate_panel_data(target_factor, name="target_factor")

    if not cond.index.equals(target.index):
        raise ValueError("conditioning_factor and target_factor must have identical date indexes")
    if not cond.columns.equals(target.columns):
        raise ValueError("conditioning_factor and target_factor must have identical asset columns")

    result = pd.DataFrame(np.nan, index=cond.index, columns=cond.columns, dtype=float)

    for date in cond.index:
        c_row = cond.loc[date]
        t_row = target.loc[date]

        valid_mask = c_row.notna() & t_row.notna()
        n_valid = int(valid_mask.sum())
        if n_valid < n_bins:
            continue

        c_valid = c_row[valid_mask]
        t_valid = t_row[valid_mask]

        # Use qcut with duplicates='drop' or rank-based binning
        c_ranks = c_valid.rank(method="first", ascending=True)
        # Partition into n_bins [0, ..., n_bins - 1]
        bins = pd.cut(c_ranks, bins=n_bins, labels=False)

        cond_ranks = pd.Series(np.nan, index=c_valid.index, dtype=float)
        for b in range(n_bins):
            in_bin = bins == b
            bin_size = int(in_bin.sum())
            if bin_size == 0:
                continue
            if bin_size == 1:
                cond_ranks[in_bin] = 0.5
            else:
                # Rank within bin normalized to [0, 1]
                t_in_bin = t_valid[in_bin]
                bin_rank = t_in_bin.rank(method="average", ascending=True)
                cond_ranks[in_bin] = (bin_rank - 1.0) / (bin_size - 1.0)

        result.loc[date, valid_mask] = cond_ranks

    return result


def factor_quadrant_interaction(
    factor_a: pd.DataFrame,
    factor_b: pd.DataFrame,
    *,
    threshold_a: float = 0.0,
    threshold_b: float = 0.0,
) -> pd.DataFrame:
    """Classify assets into cross-sectional interaction quadrants based on thresholds.

    Quadrants are scored as:
        +1.0: Concordant High (factor_a >= threshold_a and factor_b >= threshold_b)
        -1.0: Concordant Low (factor_a < threshold_a and factor_b < threshold_b)
        +0.5: Discordant A-High / B-Low (factor_a >= threshold_a and factor_b < threshold_b)
        -0.5: Discordant A-Low / B-High (factor_a < threshold_a and factor_b >= threshold_b)
        NaN: Where either factor is NaN.

    Args:
        factor_a: First date-indexed asset panel (typically standardized).
        factor_b: Second date-indexed asset panel (typically standardized).
        threshold_a: Threshold for factor_a (default 0.0).
        threshold_b: Threshold for factor_b (default 0.0).

    Returns:
        A DataFrame of quadrant classification scores with the same shape.
    """
    panel_a = validate_panel_data(factor_a, name="factor_a")
    panel_b = validate_panel_data(factor_b, name="factor_b")

    if not panel_a.index.equals(panel_b.index):
        raise ValueError("factor_a and factor_b must have identical date indexes")
    if not panel_a.columns.equals(panel_b.columns):
        raise ValueError("factor_a and factor_b must have identical asset columns")

    valid_mask = panel_a.notna() & panel_b.notna()

    a_high = panel_a >= threshold_a
    b_high = panel_b >= threshold_b

    quadrant = pd.DataFrame(np.nan, index=panel_a.index, columns=panel_a.columns, dtype=float)

    # Concordant High (+1.0)
    quadrant[valid_mask & a_high & b_high] = 1.0
    # Concordant Low (-1.0)
    quadrant[valid_mask & (~a_high) & (~b_high)] = -1.0
    # Discordant A-High / B-Low (+0.5)
    quadrant[valid_mask & a_high & (~b_high)] = 0.5
    # Discordant A-Low / B-High (-0.5)
    quadrant[valid_mask & (~a_high) & b_high] = -0.5

    return quadrant


__all__ = [
    "conditional_factor_rank",
    "factor_product_interaction",
    "factor_quadrant_interaction",
]
