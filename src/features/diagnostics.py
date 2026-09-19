"""Diagnostic helpers for research factor panels.

This module measures relationships among already-prepared factor panels. It
does not select factors, train models, define strategy logic, connect to a
backtest, fetch data, or make profitability claims.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype
from scipy.stats import kurtosis, norm, skew

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

    if method == "pearson":
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

    valid = factor_panel.notna() & returns_panel.notna()
    eligible = valid.sum(axis=1) >= min_periods
    if not bool(eligible.any()):
        return pd.Series(
            np.nan,
            index=factor_panel.index,
            dtype="float64",
            name="information_coefficient",
        )

    left = factor_panel.loc[eligible].where(valid.loc[eligible])
    right = returns_panel.loc[eligible].where(valid.loc[eligible])
    left = left.rank(axis=1, method="average")
    right = right.rank(axis=1, method="average")
    with np.errstate(divide="ignore", invalid="ignore"):
        result = left.corrwith(right, axis=1)
    return result.reindex(factor_panel.index).rename("information_coefficient")


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


def newey_west_mean_tstat(
    values: pd.Series,
    *,
    lags: int | None = None,
) -> float:
    """Newey-West t-statistic for the mean of a one-dimensional series.

    Automatic lag selection uses the Newey-West 1994 rule
    ``floor(4 * (n / 100) ** (2 / 9))``. The series is not filled. Fewer than
    two finite observations return ``NaN``.
    """

    clean = _finite_series(values, name="values")
    count = int(clean.size)
    if count < 2:
        return math.nan

    if lags is None:
        lags = int(np.floor(4.0 * (count / 100.0) ** (2.0 / 9.0)))
    elif isinstance(lags, bool) or not isinstance(lags, int) or lags < 0:
        raise ValueError("lags must be a non-negative integer")

    mean = float(clean.mean())
    residual = clean - mean
    gamma0 = float(np.dot(residual, residual) / count)
    hac = gamma0
    for lag in range(1, lags + 1):
        gamma = float(np.dot(residual[lag:], residual[:-lag]) / count)
        weight = 1.0 - lag / (lags + 1.0)
        hac += 2.0 * weight * gamma
    if not math.isfinite(hac) or hac <= 0.0:
        return math.nan
    standard_error = math.sqrt(hac / count)
    if standard_error == 0.0:
        return math.nan
    return float(mean / standard_error)


def information_coefficient_summary(
    ic: pd.Series,
    *,
    lags: int | None = None,
) -> dict[str, float]:
    """Mean IC, sample ICIR, and Newey-West t-statistic of a date-indexed IC series.

    ICIR is ``mean / sample_std`` with ``ddof=1`` and is not annualized. Missing
    IC dates are dropped rather than filled.
    """

    clean = pd.Series(ic, copy=True).dropna().astype(float)
    count = int(clean.size)
    if count == 0:
        return {
            "count": 0.0,
            "mean_ic": math.nan,
            "ic_std": math.nan,
            "icir": math.nan,
            "newey_west_tstat": math.nan,
        }

    mean_ic = float(clean.mean())
    ic_std = float(clean.std(ddof=1)) if count >= 2 else math.nan
    icir = math.nan
    if math.isfinite(ic_std) and ic_std > 0.0:
        icir = float(mean_ic / ic_std)
    return {
        "count": float(count),
        "mean_ic": mean_ic,
        "ic_std": ic_std,
        "icir": icir,
        "newey_west_tstat": newey_west_mean_tstat(clean, lags=lags),
    }


def deflated_sharpe_ratio(
    returns: pd.Series,
    *,
    n_trials: int,
) -> float:
    """Bailey and Lopez de Prado Deflated Sharpe Ratio of a return series.

    The statistic is computed on the non-annualized Sharpe of the supplied
    series. ``n_trials`` is the number of independent trials used to form the
    expected-maximum Sharpe. The result is a probability in ``[0, 1]``, not a
    profitability claim. Fewer than three observations, zero volatility, or a
    non-positive Sharpe variance term return ``NaN``.
    """

    if isinstance(n_trials, bool) or not isinstance(n_trials, int) or n_trials < 2:
        raise ValueError("n_trials must be an integer of at least 2")

    clean = _finite_series(returns, name="returns")
    count = int(clean.size)
    if count < 3:
        return math.nan

    mean = float(clean.mean())
    std = float(clean.std(ddof=1))
    if not math.isfinite(std) or std <= 0.0:
        return math.nan

    sharpe = mean / std
    skewness = float(skew(clean, bias=False))
    raw_kurtosis = float(kurtosis(clean, fisher=False, bias=False))
    inner = 1.0 - skewness * sharpe + ((raw_kurtosis - 1.0) / 4.0) * sharpe * sharpe
    if not math.isfinite(inner) or inner <= 0.0:
        return math.nan

    z_one = float(norm.ppf(1.0 - 1.0 / n_trials))
    z_two = float(norm.ppf(1.0 - 1.0 / (n_trials * math.e)))
    expected_max = math.sqrt(inner / (count - 1)) * (
        (1.0 - skewness) * z_one + skewness * z_two
    )
    statistic = (sharpe - expected_max) * math.sqrt(count - 1) / math.sqrt(inner)
    if not math.isfinite(statistic):
        return math.nan
    return float(norm.cdf(statistic))


def _finite_series(values: pd.Series, *, name: str) -> np.ndarray:
    if not isinstance(values, pd.Series):
        raise TypeError(f"{name} must be a pandas Series")
    if is_bool_dtype(values.dtype) or not is_numeric_dtype(values.dtype):
        raise TypeError(f"{name} must contain numeric non-boolean values")
    clean = values.astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    return clean.to_numpy(dtype=float)


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
    "deflated_sharpe_ratio",
    "factor_correlation_matrix",
    "factor_information_coefficient",
    "factor_quantile_spread",
    "factor_rank_information_coefficient",
    "information_coefficient_summary",
    "newey_west_mean_tstat",
]
