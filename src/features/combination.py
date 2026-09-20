"""Multi-factor combination helpers for research feature panels.

This module standardizes already-computed factor panels cross-sectionally and
combines them with equal weights, supplied IC weights, ICIR weights, or
correlation-discounted weights. It does not select portfolios, connect to a
backtest, fetch data, or make profitability claims.
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


def icir_weighted_composite(
    factors: list[pd.DataFrame],
    ic_history: pd.DataFrame | list[pd.Series],
    *,
    min_ic_periods: int = 5,
) -> pd.DataFrame:
    """Average cross-sectional z-scores weighted by Information Ratio (ICIR).

    ICIR is defined as mean(IC) / std(IC) over the supplied IC history.
    Factors with higher stability relative to volatility receive higher weight.

    Args:
        factors: Non-empty list of numeric date-indexed asset panels with identical
            indexes and columns.
        ic_history: A DataFrame of historical ICs (rows=dates, columns=factors) or
            a list of IC Series, one per factor.
        min_ic_periods: Minimum number of finite historical IC observations required
            per factor (default 5).

    Returns:
        A DataFrame of ICIR-weighted z-score composites.
    """
    validated = _validate_factor_list(factors)
    n_factors = len(validated)

    ic_matrix = _coerce_ic_history(ic_history, n_factors=n_factors, min_periods=min_ic_periods)
    ic_mean = np.nanmean(ic_matrix, axis=0)
    ic_std = np.nanstd(ic_matrix, axis=0, ddof=1)

    invalid_std = (ic_std <= 1e-12) | np.isnan(ic_std)
    if np.any(invalid_std):
        bad_idx = np.where(invalid_std)[0].tolist()
        raise ValueError(f"factors at indices {bad_idx} have zero or undefined IC standard deviation")

    icir = ic_mean / ic_std
    if not np.any(icir != 0.0):
        raise ValueError("at least one factor must have a nonzero ICIR")

    standardized = [cross_sectional_zscore(panel) for panel in validated]
    return _weighted_average(standardized, icir)


def correlation_discounted_composite(
    factors: list[pd.DataFrame],
    ic_weights: list[float] | pd.Series,
    *,
    factor_correlation: pd.DataFrame | np.ndarray | None = None,
    ridge_alpha: float = 0.1,
) -> pd.DataFrame:
    """Combine factors adjusting for pairwise cross-factor correlation.

    Solves for collinearity-adjusted weights: w* = (C + alpha * I)^{-1} * ic_weights,
    where C is the factor correlation matrix. This discounts redundant or highly
    correlated factors, preventing duplicate signals from dominating the composite.

    Args:
        factors: Non-empty list of numeric date-indexed asset panels with identical
            indexes and columns.
        ic_weights: Historical or trailing IC weights (one per factor).
        factor_correlation: Optional pairwise correlation matrix among factors.
            If None, computes the pairwise correlation of factor values across all
            aligned dates and assets.
        ridge_alpha: Non-negative ridge shrinkage parameter to ensure numerical
            stability and positive definiteness (default 0.1).

    Returns:
        A DataFrame of correlation-discounted z-score composites.
    """
    validated = _validate_factor_list(factors)
    n_factors = len(validated)
    weights = _coerce_weights(ic_weights, n_factors=n_factors)

    if not isinstance(ridge_alpha, Real) or isinstance(ridge_alpha, bool) or ridge_alpha < 0.0:
        raise ValueError("ridge_alpha must be a non-negative float")

    if factor_correlation is None:
        corr_matrix = _compute_factor_correlation(validated)
    else:
        corr_matrix = _coerce_correlation_matrix(factor_correlation, n_factors=n_factors)

    reg_corr = corr_matrix + float(ridge_alpha) * np.eye(n_factors)

    try:
        adjusted_weights = np.linalg.solve(reg_corr, weights)
    except np.linalg.LinAlgError as e:
        raise ValueError(f"factor correlation matrix is singular: {e}") from e

    if not np.any(adjusted_weights != 0.0):
        raise ValueError("adjusted weights are all zero")

    standardized = [cross_sectional_zscore(panel) for panel in validated]
    return _weighted_average(standardized, adjusted_weights)


def walk_forward_icir_weighted_composite(
    factors: list[pd.DataFrame],
    ic_history: pd.DataFrame,
    rebalance_dates: pd.DatetimeIndex,
    *,
    min_ic_periods: int = 5,
) -> pd.DataFrame:
    """Average z-scores with expanding-window ICIR weights at each rebalance.

    On rebalance date ``t``, ICIR weights use monthly ICs with timestamps
    strictly before ``t``. Factors below ``min_ic_periods`` finite ICs, or with
    zero IC standard deviation, receive weight 0.0. Those weights are held on
    every panel date in ``[t, t+1)``. Dates before the first rebalance with at
    least one nonzero ICIR remain ``NaN``.

    Args:
        factors: Non-empty list of numeric date-indexed asset panels with
            identical indexes and columns.
        ic_history: Monthly IC DataFrame (rows=dates, columns=factors in the
            same order as ``factors``).
        rebalance_dates: Month-end (or other) dates at which weights refresh.
        min_ic_periods: Minimum finite IC observations per factor before that
            factor receives a nonzero ICIR weight (default 5).

    Returns:
        A DataFrame of walk-forward ICIR-weighted z-score composites.
    """
    validated = _validate_factor_list(factors)
    n_factors = len(validated)
    _validate_min_ic_periods(min_ic_periods)
    history = _walk_forward_ic_history(ic_history, n_factors=n_factors)
    ordered_rebalances = _ordered_rebalance_dates(rebalance_dates)
    standardized = [cross_sectional_zscore(panel) for panel in validated]

    weights_by_rebalance: dict[pd.Timestamp, np.ndarray] = {}
    for t in ordered_rebalances:
        past = history.loc[history.index < t]
        weights = _expanding_icir_weights(
            past.to_numpy(dtype=float),
            n_factors=n_factors,
            min_ic_periods=min_ic_periods,
        )
        if weights is not None:
            weights_by_rebalance[pd.Timestamp(t)] = weights

    return _weighted_composite_by_rebalance(
        standardized,
        ordered_rebalances,
        weights_by_rebalance,
    )


def walk_forward_correlation_discounted_composite(
    factors: list[pd.DataFrame],
    ic_history: pd.DataFrame,
    rebalance_dates: pd.DatetimeIndex,
    *,
    ridge_alpha: float = 0.1,
    min_ic_periods: int = 1,
) -> pd.DataFrame:
    """Combine z-scores with walk-forward collinearity-discounted weights.

    On rebalance date ``t``, the IC vector is the expanding-window mean of
    monthly ICs with timestamps strictly before ``t``. Pairwise factor-value
    correlation uses the trailing panels through ``t`` inclusive. Adjusted
    weights solve ``(C_t + alpha * I)^{-1} * ic_mean_t`` and are held on every
    panel date in ``[t, t+1)``.

    Args:
        factors: Non-empty list of numeric date-indexed asset panels with
            identical indexes and columns.
        ic_history: Monthly IC DataFrame (rows=dates, columns=factors in the
            same order as ``factors``).
        rebalance_dates: Month-end (or other) dates at which weights refresh.
        ridge_alpha: Non-negative ridge shrinkage parameter (default 0.1).
        min_ic_periods: Minimum finite IC observations per factor before that
            factor contributes a nonzero expanding-window mean IC (default 1).

    Returns:
        A DataFrame of walk-forward correlation-discounted z-score composites.
    """
    validated = _validate_factor_list(factors)
    n_factors = len(validated)
    _validate_min_ic_periods(min_ic_periods)
    if not isinstance(ridge_alpha, Real) or isinstance(ridge_alpha, bool) or ridge_alpha < 0.0:
        raise ValueError("ridge_alpha must be a non-negative float")

    history = _walk_forward_ic_history(ic_history, n_factors=n_factors)
    ordered_rebalances = _ordered_rebalance_dates(rebalance_dates)
    standardized = [cross_sectional_zscore(panel) for panel in validated]
    ridge = float(ridge_alpha) * np.eye(n_factors)

    weights_by_rebalance: dict[pd.Timestamp, np.ndarray] = {}
    for t in ordered_rebalances:
        past = history.loc[history.index < t]
        ic_weights = _expanding_mean_ic_weights(
            past.to_numpy(dtype=float),
            n_factors=n_factors,
            min_ic_periods=min_ic_periods,
        )
        if ic_weights is None:
            continue
        trailing = [panel.loc[panel.index <= t] for panel in validated]
        if trailing[0].empty:
            continue
        corr_matrix = _compute_factor_correlation(trailing)
        try:
            adjusted = np.linalg.solve(corr_matrix + ridge, ic_weights)
        except np.linalg.LinAlgError:
            continue
        if not np.any(adjusted != 0.0):
            continue
        weights_by_rebalance[pd.Timestamp(t)] = adjusted

    return _weighted_composite_by_rebalance(
        standardized,
        ordered_rebalances,
        weights_by_rebalance,
    )


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


def _coerce_ic_history(
    ic_history: pd.DataFrame | list[pd.Series],
    *,
    n_factors: int,
    min_periods: int,
) -> np.ndarray:
    if isinstance(ic_history, pd.DataFrame):
        if ic_history.shape[1] != n_factors:
            raise ValueError(f"ic_history DataFrame must have {n_factors} columns, got {ic_history.shape[1]}")
        matrix = ic_history.to_numpy(dtype=float)
    elif isinstance(ic_history, list):
        if len(ic_history) != n_factors:
            raise ValueError(f"ic_history list must have {n_factors} series, got {len(ic_history)}")
        series_list = []
        for i, s in enumerate(ic_history):
            if not isinstance(s, pd.Series):
                raise TypeError(f"ic_history[{i}] must be a pandas Series")
            series_list.append(s.to_numpy(dtype=float))
        lengths = [len(arr) for arr in series_list]
        if len(set(lengths)) > 1:
            raise ValueError("all ic_history series must have identical length")
        matrix = np.column_stack(series_list)
    else:
        raise TypeError("ic_history must be a pandas DataFrame or list of Series")

    valid_counts = np.sum(np.isfinite(matrix), axis=0)
    for i, count in enumerate(valid_counts):
        if count < min_periods:
            raise ValueError(
                f"factor at position {i} has {count} valid IC periods, requires at least {min_periods}"
            )

    return matrix


def _validate_min_ic_periods(min_ic_periods: int) -> None:
    if (
        isinstance(min_ic_periods, bool)
        or not isinstance(min_ic_periods, int)
        or min_ic_periods < 1
    ):
        raise ValueError("min_ic_periods must be an integer of at least 1")


def _walk_forward_ic_history(ic_history: pd.DataFrame, *, n_factors: int) -> pd.DataFrame:
    if not isinstance(ic_history, pd.DataFrame):
        raise TypeError("ic_history must be a pandas DataFrame")
    if ic_history.shape[1] != n_factors:
        raise ValueError(
            f"ic_history DataFrame must have {n_factors} columns, got {ic_history.shape[1]}"
        )
    history = ic_history.copy()
    history.index = pd.DatetimeIndex(history.index)
    return history.sort_index()


def _ordered_rebalance_dates(rebalance_dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(rebalance_dates).sort_values().unique()


def _expanding_mean_ic_weights(
    ic_matrix: np.ndarray,
    *,
    n_factors: int,
    min_ic_periods: int,
) -> np.ndarray | None:
    if ic_matrix.size == 0:
        return None
    if ic_matrix.ndim != 2 or ic_matrix.shape[1] != n_factors:
        raise ValueError(f"ic_history must have shape (n_periods, {n_factors})")
    weights = np.zeros(n_factors, dtype=float)
    for position in range(n_factors):
        finite = ic_matrix[:, position][np.isfinite(ic_matrix[:, position])]
        if finite.size < min_ic_periods:
            continue
        weights[position] = float(np.mean(finite))
    if not np.any(weights != 0.0):
        return None
    return weights


def _expanding_icir_weights(
    ic_matrix: np.ndarray,
    *,
    n_factors: int,
    min_ic_periods: int,
) -> np.ndarray | None:
    if ic_matrix.size == 0:
        return None
    if ic_matrix.ndim != 2 or ic_matrix.shape[1] != n_factors:
        raise ValueError(f"ic_history must have shape (n_periods, {n_factors})")
    weights = np.zeros(n_factors, dtype=float)
    for position in range(n_factors):
        finite = ic_matrix[:, position][np.isfinite(ic_matrix[:, position])]
        if finite.size < min_ic_periods:
            continue
        ic_std = float(np.std(finite, ddof=1))
        if (not np.isfinite(ic_std)) or ic_std <= 1e-12:
            continue
        weights[position] = float(np.mean(finite)) / ic_std
    if not np.any(weights != 0.0):
        return None
    return weights


def _weighted_composite_by_rebalance(
    standardized: list[pd.DataFrame],
    rebalance_dates: pd.DatetimeIndex,
    weights_by_rebalance: dict[pd.Timestamp, np.ndarray],
) -> pd.DataFrame:
    index = standardized[0].index
    columns = standardized[0].columns
    output = pd.DataFrame(np.nan, index=index, columns=columns, dtype=float)
    ordered = pd.DatetimeIndex(rebalance_dates).sort_values().unique()
    for position, t in enumerate(ordered):
        weights = weights_by_rebalance.get(pd.Timestamp(t))
        if weights is None:
            continue
        next_t = ordered[position + 1] if position + 1 < len(ordered) else None
        if next_t is None:
            members = index[index >= t]
        else:
            members = index[(index >= t) & (index < next_t)]
        if len(members) == 0:
            continue
        sliced = [panel.loc[members] for panel in standardized]
        combined = _weighted_average(sliced, weights)
        output.loc[members] = combined.to_numpy()
    return output


def _compute_factor_correlation(factors: list[pd.DataFrame]) -> np.ndarray:
    n_factors = len(factors)
    corr = np.eye(n_factors, dtype=float)
    flat_factors = [f.to_numpy(dtype=float).flatten() for f in factors]

    for i in range(n_factors):
        for j in range(i + 1, n_factors):
            valid = np.isfinite(flat_factors[i]) & np.isfinite(flat_factors[j])
            if np.sum(valid) < 3:
                r = 0.0
            else:
                with np.errstate(invalid="ignore", divide="ignore"):
                    r = float(np.corrcoef(flat_factors[i][valid], flat_factors[j][valid])[0, 1])
                if np.isnan(r):
                    r = 0.0
            corr[i, j] = r
            corr[j, i] = r
    return corr


def _coerce_correlation_matrix(
    corr: pd.DataFrame | np.ndarray,
    *,
    n_factors: int,
) -> np.ndarray:
    if isinstance(corr, pd.DataFrame):
        if corr.shape != (n_factors, n_factors):
            raise ValueError(f"factor_correlation must have shape ({n_factors}, {n_factors})")
        arr = corr.to_numpy(dtype=float)
    elif isinstance(corr, np.ndarray):
        if corr.shape != (n_factors, n_factors):
            raise ValueError(f"factor_correlation must have shape ({n_factors}, {n_factors})")
        arr = corr.astype(float)
    else:
        raise TypeError("factor_correlation must be a DataFrame or ndarray")

    if not np.all(np.isfinite(arr)):
        raise ValueError("factor_correlation matrix must contain only finite values")
    return arr


def _weighted_average(panels: list[pd.DataFrame], weights: np.ndarray) -> pd.DataFrame:
    stacked = np.stack([panel.to_numpy(dtype=float) for panel in panels], axis=0)
    weight = weights.reshape(-1, 1, 1)
    valid = np.isfinite(stacked)
    numerator = np.nansum(np.where(valid, stacked * weight, 0.0), axis=0)
    denominator = np.sum(np.where(valid, np.abs(weight), 0.0), axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        values = numerator / np.where(denominator == 0.0, np.nan, denominator)
    return pd.DataFrame(values, index=panels[0].index, columns=panels[0].columns)


__all__ = [
    "correlation_discounted_composite",
    "equal_weighted_composite",
    "ic_weighted_composite",
    "icir_weighted_composite",
    "walk_forward_correlation_discounted_composite",
    "walk_forward_icir_weighted_composite",
]
