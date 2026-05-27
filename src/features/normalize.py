"""Factor normalization helpers for research feature panels.

This module contains normalization utilities for cross-sectional factor
research. The helpers transform feature outputs; they do not define strategy
logic, portfolio construction, backtests, or profitability claims.
"""

from __future__ import annotations

import pandas as pd

from features.operators import cross_sectional_zscore


def cross_sectional_zscore_factor(factor: pd.DataFrame, ddof: int = 0) -> pd.DataFrame:
    """Normalize each factor cross-section with a row-wise z-score.

    For each date, the function subtracts the cross-sectional mean across
    assets and divides by the cross-sectional standard deviation. Missing factor
    values are ignored in the row statistics and remain ``NaN`` in the output.
    Rows with zero or unavailable cross-sectional standard deviation return
    ``NaN`` for valid entries rather than zero or infinite values.

    The result preserves the input index and columns. No forward-fill,
    backward-fill, sorting, lagging, or real data fetching is performed. The
    normalized output is a research feature, not a combined score or trading
    strategy.

    Args:
        factor: Factor DataFrame indexed by increasing dates with assets as
            columns. Values must already be numeric; strings and boolean columns
            are rejected by the shared panel validator.
        ddof: Delta degrees of freedom used in the row-wise standard deviation.
            Defaults to 0 for population-style cross-sectional z-scores.

    Returns:
        A DataFrame of cross-sectional z-scores with the same index and columns
        as ``factor``.

    Raises:
        TypeError: If ``factor`` is not a valid numeric panel or ``ddof`` is not
            an integer.
        ValueError: If ``factor`` has invalid date alignment or ``ddof`` is
            negative.
    """

    return cross_sectional_zscore(factor, ddof=ddof)


__all__ = ["cross_sectional_zscore_factor"]
