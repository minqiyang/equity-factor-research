"""Cross-sectional factor neutralization and risk factor orthogonalization.

This module provides cross-sectional neutralization utilities for research factor
panels. It removes unwanted market, sector, industry, or style risk exposures
(such as market beta, size, or volatility) via cross-sectional OLS regression or
group-demeaning per date:

    y_t = X_t * beta_t + epsilon_t

where the residual epsilon_t represents the pure, risk-neutralized factor.

The functions transform feature panels; they do not place trades, connect to a
broker, execute orders, or make profitability claims.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from features.operators import validate_panel_data


def cross_sectional_demean(factor: pd.DataFrame) -> pd.DataFrame:
    """Subtract the cross-sectional mean across assets for each date.

    For each date, the cross-sectional mean of non-missing factor values is
    subtracted from each valid asset, producing a dollar-neutral factor panel
    where the cross-sectional sum equals 0.0. Missing values remain ``NaN``.

    Args:
        factor: Factor DataFrame indexed by increasing dates with assets as columns.

    Returns:
        DataFrame of cross-sectional demeaned factor scores with the same shape,
        index, and columns as ``factor``.
    """

    panel = validate_panel_data(factor, name="factor")
    row_mean = panel.mean(axis=1)
    return panel.sub(row_mean, axis=0)


def cross_sectional_neutralize(
    factor: pd.DataFrame,
    risk_factors: pd.DataFrame | Sequence[pd.DataFrame] | Mapping[str, pd.DataFrame],
    *,
    add_intercept: bool = True,
    min_assets: int = 2,
) -> pd.DataFrame:
    """Orthogonalize a factor panel against one or more risk factor panels.

    For each date t, performs a cross-sectional Ordinary Least Squares (OLS)
    regression of the factor y_t on the risk factors X_t:

        y_t = X_t * beta_t + epsilon_t

    The residual epsilon_t is strictly orthogonal to all columns in X_t (and
    demeaned if add_intercept=True).

    Assets with missing values in either the target factor or any risk factor
    are excluded from that date's regression and remain ``NaN`` in the output.
    Dates with fewer valid assets than required return ``NaN`` for all assets.

    Args:
        factor: Target factor DataFrame (T dates x N assets).
        risk_factors: Single DataFrame, sequence of DataFrames, or mapping of
            names to DataFrames representing risk factor exposures (e.g. Size,
            Beta, Volatility). Must share identical index and columns with ``factor``.
        add_intercept: If True (default), includes an intercept term in the
            regression, which guarantees the residual is cross-sectionally
            demeaned (mean = 0.0).
        min_assets: Minimum number of valid assets required on a date to run
            the regression. Must be at least 2.

    Returns:
        DataFrame of risk-neutralized residuals with the same shape, index, and
        columns as ``factor``.

    Raises:
        TypeError: If inputs fail DataFrame or panel validation.
        ValueError: If risk factor panels do not match ``factor`` shape or index.
    """

    if isinstance(min_assets, bool) or not isinstance(min_assets, int) or min_assets < 2:
        raise ValueError("min_assets must be an integer of at least 2")

    target_panel = validate_panel_data(factor, name="factor")

    # Normalize risk_factors to a list of DataFrames
    rf_list: list[pd.DataFrame] = []
    if isinstance(risk_factors, pd.DataFrame):
        rf_list = [risk_factors]
    elif isinstance(risk_factors, Mapping):
        rf_list = list(risk_factors.values())
    elif isinstance(risk_factors, Sequence):
        rf_list = list(risk_factors)
    else:
        raise TypeError("risk_factors must be a DataFrame, sequence of DataFrames, or mapping")

    if not rf_list:
        raise ValueError("risk_factors must not be empty")

    validated_rfs: list[pd.DataFrame] = []
    for i, rf in enumerate(rf_list):
        rf_panel = validate_panel_data(rf, name=f"risk_factors[{i}]")
        if not rf_panel.index.equals(target_panel.index):
            raise ValueError(f"risk_factors[{i}] index must match factor index exactly")
        if not rf_panel.columns.equals(target_panel.columns):
            raise ValueError(f"risk_factors[{i}] columns must match factor columns exactly")
        validated_rfs.append(rf_panel)

    num_rf = len(validated_rfs)
    min_required = num_rf + (1 if add_intercept else 0)
    effective_min = max(min_assets, min_required)

    residual_panel = pd.DataFrame(
        np.nan,
        index=target_panel.index,
        columns=target_panel.columns,
        dtype=float,
    )

    y_values = target_panel.to_numpy(dtype=float)
    rf_values = [rf.to_numpy(dtype=float) for rf in validated_rfs]
    n_rows, n_cols = y_values.shape

    for row_idx in range(n_rows):
        y_row = y_values[row_idx]
        rf_rows = [rf[row_idx] for rf in rf_values]

        # Valid mask across y and all risk factors
        valid = np.isfinite(y_row)
        for rf_row in rf_rows:
            valid &= np.isfinite(rf_row)

        valid_count = int(np.sum(valid))
        if valid_count < effective_min:
            continue

        y_valid = y_row[valid]
        x_cols = [rf_row[valid] for rf_row in rf_rows]

        if add_intercept:
            ones = np.ones(valid_count, dtype=float)
            x_mat = np.column_stack([ones, *x_cols])
        else:
            x_mat = np.column_stack(x_cols)

        # Solve OLS via SVD / least squares
        try:
            beta, residuals, rank, s = np.linalg.lstsq(x_mat, y_valid, rcond=None)
            predicted = np.dot(x_mat, beta)
            residual = y_valid - predicted
            residual_panel.iloc[row_idx, valid] = residual
        except np.linalg.LinAlgError:
            continue

    return residual_panel


def cross_sectional_group_neutralize(
    factor: pd.DataFrame,
    groups: pd.DataFrame | pd.Series | Mapping[str, object],
) -> pd.DataFrame:
    """Demean factor values within discrete industry, sector, or cluster groups.

    For each date and each group, subtracts the group's cross-sectional mean
    from each constituent asset. The resulting factor has a mean of 0.0 within
    every group on every date.

    Args:
        factor: Factor DataFrame indexed by increasing dates with assets as columns.
        groups: Discrete group identifiers. May be:
            - A static Mapping / Series of asset -> group label.
            - A dynamic DataFrame of shape (dates x assets) where each cell is a group label.

    Returns:
        DataFrame of group-neutralized factor values with the same shape, index,
        and columns as ``factor``.
    """

    panel = validate_panel_data(factor, name="factor")
    output = pd.DataFrame(np.nan, index=panel.index, columns=panel.columns, dtype=float)

    if isinstance(groups, (Mapping, pd.Series)):
        group_series = pd.Series(groups)
        unique_groups = group_series.dropna().unique()

        for group_id in unique_groups:
            group_assets = group_series[group_series == group_id].index
            common_assets = panel.columns.intersection(group_assets)
            if len(common_assets) > 0:
                sub_panel = panel[common_assets]
                sub_mean = sub_panel.mean(axis=1)
                output[common_assets] = sub_panel.sub(sub_mean, axis=0)

    elif isinstance(groups, pd.DataFrame):
        if not groups.index.equals(panel.index) or not groups.columns.equals(panel.columns):
            raise ValueError("dynamic groups DataFrame must have identical index and columns to factor")

        for date in panel.index:
            y_row = panel.loc[date]
            g_row = groups.loc[date]
            valid = y_row.notna() & g_row.notna()

            if not valid.any():
                continue

            y_valid = y_row[valid]
            g_valid = g_row[valid]

            for group_id in g_valid.unique():
                g_mask = g_valid == group_id
                group_assets = g_valid.index[g_mask]
                vals = y_valid[group_assets]
                m = float(vals.mean())
                output.loc[date, group_assets] = vals - m
    else:
        raise TypeError("groups must be a Series, Mapping, or DataFrame")

    return output


__all__ = [
    "cross_sectional_demean",
    "cross_sectional_group_neutralize",
    "cross_sectional_neutralize",
]
