"""Factor normalization helpers for research feature panels.

This module contains normalization utilities for cross-sectional factor
research. The helpers transform feature outputs; they do not define strategy
logic, portfolio construction, backtests, or profitability claims.
"""

from __future__ import annotations

import pandas as pd

from features.operators import cross_sectional_rank, cross_sectional_zscore, validate_panel_data


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


def cross_sectional_rank_factor(
    factor: pd.DataFrame,
    method: str = "average",
    ascending: bool = True,
) -> pd.DataFrame:
    """Normalize each factor cross-section with ordinal row-wise ranks.

    For each date, assets are ranked across that date's factor values using
    pandas ordinal rank semantics with ``pct=False``. Missing factor values are
    excluded from the row ranking and remain ``NaN`` in the output. Ties are
    handled by pandas according to ``method``, with ``"average"`` as the
    default.

    The result preserves the input index and columns. The output is a
    normalized research feature, not a combined score or trading strategy.

    Args:
        factor: Factor DataFrame indexed by increasing dates with assets as
            columns. Values must already be numeric; strings and boolean columns
            are rejected by the shared panel validator.
        method: Tie-handling method passed to ``DataFrame.rank``.
        ascending: If ``True``, lower raw values receive lower rank numbers. If
            ``False``, higher raw values receive lower rank numbers.

    Returns:
        A DataFrame of ordinal ranks with the same index and columns as
        ``factor``.
    """

    panel = validate_panel_data(factor, name="factor")
    return panel.rank(axis=1, method=method, ascending=ascending, pct=False)


def cross_sectional_percentile_rank_factor(
    factor: pd.DataFrame,
    method: str = "average",
    ascending: bool = True,
) -> pd.DataFrame:
    """Normalize each factor cross-section with pandas percentile ranks.

    For each date, assets are ranked across that date's factor values using
    pandas ``pct=True`` rank semantics. The percentile rank is the ordinal rank
    divided by the number of valid non-missing observations in that row; it is
    not a min-max percentile transformation. Missing values are excluded from
    the row ranking and remain ``NaN`` in the output.

    The result preserves the input index and columns. The output is a
    normalized research feature, not a combined score or trading strategy.

    Args:
        factor: Factor DataFrame indexed by increasing dates with assets as
            columns. Values must already be numeric; strings and boolean columns
            are rejected by the shared panel validator.
        method: Tie-handling method passed to ``DataFrame.rank``.
        ascending: If ``True``, lower raw values receive lower percentile ranks.
            If ``False``, higher raw values receive lower percentile ranks.

    Returns:
        A DataFrame of pandas percentile ranks with the same index and columns
        as ``factor``.
    """

    return cross_sectional_rank(factor, method=method, ascending=ascending)


__all__ = [
    "cross_sectional_percentile_rank_factor",
    "cross_sectional_rank_factor",
    "cross_sectional_zscore_factor",
]
