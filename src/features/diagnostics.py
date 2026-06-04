"""Diagnostic helpers for research factor panels.

This module measures relationships among already-prepared factor panels. It
does not select factors, train models, define strategy logic, connect to a
backtest, fetch data, or make profitability claims.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from features.operators import validate_panel_data

_SUPPORTED_CORRELATION_METHODS = {"pearson", "spearman"}
_QUANTILE_SPREAD_COLUMNS = [
    "bottom_quantile_mean_return",
    "top_quantile_mean_return",
    "top_minus_bottom_spread",
    "valid_asset_count",
    "bottom_quantile_count",
    "top_quantile_count",
]


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

    _validate_correlation_method(method)

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


def factor_information_coefficient(
    factor: pd.DataFrame,
    forward_returns: pd.DataFrame,
    *,
    method: str = "pearson",
    min_periods: int = 2,
) -> pd.Series:
    """Compute per-date cross-sectional IC between a factor and returns.

    ``forward_returns`` must already be aligned so each row contains the
    holding-period return used to evaluate the factor value at that same date.
    This helper does not calculate returns, shift dates, fill missing values,
    select assets, connect to a backtest, or interpret the result as evidence
    of future performance.

    Args:
        factor: Numeric date-indexed asset factor panel.
        forward_returns: Numeric date-indexed asset return panel aligned to
            ``factor``. These returns are evaluation targets, not signal inputs.
        method: Correlation method. Supported values are ``"pearson"`` and
            ``"spearman"``.
        min_periods: Minimum number of overlapping valid assets required on a
            date. Dates with fewer valid pairs return ``NaN``.

    Returns:
        Series indexed by date, where each value is that date's cross-sectional
        information coefficient.

    Raises:
        TypeError: If either panel fails shared validation or ``min_periods`` is
            not an integer.
        ValueError: If panels are misaligned, ``method`` is unsupported, or
            ``min_periods`` is less than 2.
    """

    _validate_correlation_method(method)
    _validate_min_periods(min_periods, minimum=2)
    factor_panel, returns_panel = _validate_matching_evaluation_panels(
        factor,
        forward_returns,
    )

    values: list[float] = []
    for date in factor_panel.index:
        factor_row = factor_panel.loc[date]
        returns_row = returns_panel.loc[date]
        valid_pair = factor_row.notna() & returns_row.notna()

        if int(valid_pair.sum()) < min_periods:
            values.append(np.nan)
            continue

        with np.errstate(divide="ignore", invalid="ignore"):
            correlation = factor_row[valid_pair].corr(
                returns_row[valid_pair],
                method=method,
            )
            values.append(float(correlation))

    return pd.Series(values, index=factor_panel.index, name="information_coefficient")


def factor_rank_information_coefficient(
    factor: pd.DataFrame,
    forward_returns: pd.DataFrame,
    *,
    min_periods: int = 2,
) -> pd.Series:
    """Compute per-date cross-sectional Rank IC using Spearman correlation."""

    result = factor_information_coefficient(
        factor,
        forward_returns,
        method="spearman",
        min_periods=min_periods,
    )
    return result.rename("rank_information_coefficient")


def factor_quantile_spread(
    factor: pd.DataFrame,
    forward_returns: pd.DataFrame,
    *,
    quantiles: int = 5,
    min_assets_per_quantile: int = 1,
) -> pd.DataFrame:
    """Compute per-date top-minus-bottom quantile return diagnostics.

    ``forward_returns`` must already be aligned so each row contains the
    holding-period return used to evaluate the factor value at that same date.
    This helper does not calculate returns, shift dates, fill missing values,
    select a portfolio, connect to a backtest, or interpret the spread as
    evidence of future performance.

    For each date, assets with overlapping non-missing factor and return values
    are assigned to factor quantiles. The output reports the average return in
    the bottom and top quantiles, the top-minus-bottom spread, and simple
    coverage counts. Dates with too few valid assets, too few distinct factor
    values, or too few assets in either edge quantile return ``NaN`` for the
    return and spread columns.
    """

    _validate_minimum_integer(quantiles, "quantiles", minimum=2)
    _validate_minimum_integer(
        min_assets_per_quantile,
        "min_assets_per_quantile",
        minimum=1,
    )
    factor_panel, returns_panel = _validate_matching_evaluation_panels(
        factor,
        forward_returns,
    )

    records: list[dict[str, float | int]] = []
    for date in factor_panel.index:
        factor_row = factor_panel.loc[date]
        returns_row = returns_panel.loc[date]
        valid_pair = factor_row.notna() & returns_row.notna()
        factor_values = factor_row[valid_pair]
        returns_values = returns_row[valid_pair]
        valid_count = int(valid_pair.sum())
        record = _empty_quantile_spread_record(valid_count)

        if valid_count < quantiles or factor_values.nunique(dropna=True) < quantiles:
            records.append(record)
            continue

        try:
            quantile_codes = pd.qcut(
                factor_values,
                q=quantiles,
                labels=False,
                duplicates="drop",
            )
        except ValueError:
            records.append(record)
            continue

        quantile_codes = pd.Series(quantile_codes, index=factor_values.index)
        if (
            quantile_codes.isna().any()
            or int(quantile_codes.nunique(dropna=True)) != quantiles
        ):
            records.append(record)
            continue

        bottom_mask = quantile_codes == 0
        top_mask = quantile_codes == quantiles - 1
        bottom_count = int(bottom_mask.sum())
        top_count = int(top_mask.sum())
        record["bottom_quantile_count"] = bottom_count
        record["top_quantile_count"] = top_count

        if (
            bottom_count < min_assets_per_quantile
            or top_count < min_assets_per_quantile
        ):
            records.append(record)
            continue

        bottom_mean = float(returns_values[bottom_mask].mean())
        top_mean = float(returns_values[top_mask].mean())
        record["bottom_quantile_mean_return"] = bottom_mean
        record["top_quantile_mean_return"] = top_mean
        record["top_minus_bottom_spread"] = top_mean - bottom_mean
        records.append(record)

    return pd.DataFrame.from_records(
        records,
        index=factor_panel.index,
        columns=_QUANTILE_SPREAD_COLUMNS,
    )


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


def _validate_matching_evaluation_panels(
    factor: pd.DataFrame,
    forward_returns: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    factor_panel = validate_panel_data(factor, name="factor")
    returns_panel = validate_panel_data(forward_returns, name="forward_returns")

    if not factor_panel.index.equals(returns_panel.index):
        raise ValueError("factor and forward_returns must have identical indexes")

    if not factor_panel.columns.equals(returns_panel.columns):
        raise ValueError("factor and forward_returns must have identical columns")

    return factor_panel, returns_panel


def _validate_correlation_method(method: str) -> None:
    if method not in _SUPPORTED_CORRELATION_METHODS:
        raise ValueError("method must be either 'pearson' or 'spearman'")


def _empty_quantile_spread_record(valid_asset_count: int) -> dict[str, float | int]:
    return {
        "bottom_quantile_mean_return": np.nan,
        "top_quantile_mean_return": np.nan,
        "top_minus_bottom_spread": np.nan,
        "valid_asset_count": valid_asset_count,
        "bottom_quantile_count": 0,
        "top_quantile_count": 0,
    }


def _validate_minimum_integer(value: int, name: str, *, minimum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")

    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")


def _validate_min_periods(min_periods: int, *, minimum: int = 1) -> None:
    _validate_minimum_integer(min_periods, "min_periods", minimum=minimum)


__all__ = [
    "factor_correlation_matrix",
    "factor_information_coefficient",
    "factor_quantile_spread",
    "factor_rank_information_coefficient",
]
