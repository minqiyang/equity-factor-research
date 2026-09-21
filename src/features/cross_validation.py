"""Purged and Embargoed Combinatorial Cross-Validation (CPCV).

This module implements financial cross-validation methods designed to prevent
leakage in time-series data with overlapping labels (e.g. forward-return holding
periods) and autoregressive serial correlation.

Key components:
- PurgedGroupTimeSeriesSplit: Scikit-learn compatible cross-validator with
  label purging and post-test embargo.
- combinatorial_purged_cross_validation_pbo: Combinatorial Purged Cross-Validation
  (CPCV) Probability of Backtest Overfitting (PBO) evaluator.
"""

from __future__ import annotations

import itertools
import math
from typing import Any, Iterator, Mapping

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype
from sklearn.model_selection import BaseCrossValidator


class PurgedGroupTimeSeriesSplit(BaseCrossValidator):
    """Purged and embargoed cross-validation splitter for financial time series.

    When financial samples have forward-looking return labels (e.g. holding
    period of H bars), adjacent training and test samples share underlying price
    information. PurgedGroupTimeSeriesSplit divides time-ordered observations
    into N contiguous groups, evaluates combinations of k test groups (CPCV),
    and purges all training samples whose label intervals overlap with the test
    groups. It additionally applies an embargo window after test groups to
    prevent autoregressive momentum/volatility leakage.

    Parameters:
        n_splits: Total number of contiguous time groups (N >= 2). Default 5.
        n_test_groups: Number of groups selected for testing per split (k >= 1).
            When n_test_groups = 1, produces standard K-fold purged CV.
            When n_test_groups > 1, produces Combinatorial Purged CV (C(N, k) splits).
            Default is 1.
        holding_periods: Number of periods forward that each sample's label spans.
            Used to determine label end times when samples_info is not provided.
            Default is 0 (point-in-time instantaneous labels).
        embargo_periods: Fixed number of observations after each test group to
            embargo (drop from training). Default is 0.
        embargo_pct: Percentage of total observations to embargo after each test
            group. If both embargo_periods and embargo_pct are given, the larger
            count is used. Default is 0.0.
        samples_info: Optional pandas Series or DataFrame mapping sample index to
            its label end timestamp or integer index. If provided, overrides
            holding_periods for determining exact label horizons.
    """

    def __init__(
        self,
        n_splits: int = 5,
        *,
        n_test_groups: int = 1,
        holding_periods: int = 0,
        embargo_periods: int = 0,
        embargo_pct: float = 0.0,
        samples_info: pd.Series | pd.DataFrame | Mapping[Any, Any] | None = None,
    ) -> None:
        if isinstance(n_splits, bool) or not isinstance(n_splits, int) or n_splits < 2:
            raise ValueError(f"n_splits must be an integer >= 2, got {n_splits}")
        if (
            isinstance(n_test_groups, bool)
            or not isinstance(n_test_groups, int)
            or n_test_groups < 1
            or n_test_groups >= n_splits
        ):
            raise ValueError(
                f"n_test_groups must be an integer in [1, n_splits - 1], got {n_test_groups} with n_splits={n_splits}"
            )
        if isinstance(holding_periods, bool) or not isinstance(holding_periods, int) or holding_periods < 0:
            raise ValueError(f"holding_periods must be a non-negative integer, got {holding_periods}")
        if isinstance(embargo_periods, bool) or not isinstance(embargo_periods, int) or embargo_periods < 0:
            raise ValueError(f"embargo_periods must be a non-negative integer, got {embargo_periods}")
        if (
            isinstance(embargo_pct, bool)
            or not isinstance(embargo_pct, (int, float))
            or embargo_pct < 0.0
            or embargo_pct >= 1.0
        ):
            raise ValueError(f"embargo_pct must be a float in [0.0, 1.0), got {embargo_pct}")

        self.n_splits = n_splits
        self.n_test_groups = n_test_groups
        self.holding_periods = holding_periods
        self.embargo_periods = embargo_periods
        self.embargo_pct = float(embargo_pct)
        self.samples_info = samples_info

    def get_n_splits(
        self,
        X: Any = None,
        y: Any = None,
        groups: Any = None,
    ) -> int:
        """Return the number of splitting iterations C(n_splits, n_test_groups)."""
        if groups is not None:
            unique_groups = len(np.unique(groups))
            if unique_groups != self.n_splits:
                raise ValueError(
                    f"Number of unique groups ({unique_groups}) does not match n_splits ({self.n_splits})"
                )
        return math.comb(self.n_splits, self.n_test_groups)

    def split_details(
        self,
        X: Any,
        y: Any = None,
        groups: Any = None,
    ) -> Iterator[tuple[np.ndarray, np.ndarray, int, int]]:
        """Yield (train_indices, test_indices, purge_count, embargo_count)."""
        X_arr = np.asarray(X)
        n_samples = len(X_arr)
        if n_samples < self.n_splits:
            raise ValueError(f"n_samples ({n_samples}) must be >= n_splits ({self.n_splits})")

        indices = np.arange(n_samples)
        sample_starts = np.arange(n_samples, dtype=int)
        sample_ends = sample_starts + self.holding_periods

        if self.samples_info is not None:
            if isinstance(self.samples_info, (pd.Series, pd.DataFrame)):
                info_values = self.samples_info.to_numpy()
            elif isinstance(self.samples_info, Mapping):
                info_values = np.array([self.samples_info.get(i, i) for i in range(n_samples)])
            else:
                info_values = np.asarray(self.samples_info)

            if np.issubdtype(info_values.dtype, np.integer):
                sample_ends = info_values.astype(int)

        # Partition indices into n_splits groups
        if groups is None:
            group_splits = np.array_split(indices, self.n_splits)
        else:
            unique_groups = np.unique(groups)
            if len(unique_groups) < self.n_splits:
                raise ValueError(
                    f"Number of unique groups ({len(unique_groups)}) is less than n_splits ({self.n_splits})"
                )
            group_splits = [indices[groups == g] for g in unique_groups]

        embargo_count = max(self.embargo_periods, int(math.ceil(self.embargo_pct * n_samples)))

        all_group_indices = list(range(len(group_splits)))
        for test_group_comb in itertools.combinations(all_group_indices, self.n_test_groups):
            test_indices_list = [group_splits[g] for g in test_group_comb]
            test_indices = np.sort(np.concatenate(test_indices_list))

            test_intervals: list[tuple[int, int]] = []
            for g in test_group_comb:
                g_idx = group_splits[g]
                if len(g_idx) == 0:
                    continue
                g_start = int(sample_starts[g_idx[0]])
                g_end = int(sample_ends[g_idx[-1]])
                test_intervals.append((g_start, g_end))

            non_test_mask = np.ones(n_samples, dtype=bool)
            non_test_mask[test_indices] = False

            # 1. Purge: remove training samples whose label window overlaps with any test group
            overlap_mask = np.zeros(n_samples, dtype=bool)
            for t_start, t_end in test_intervals:
                overlap = (sample_starts <= t_end) & (sample_ends >= t_start)
                overlap_mask |= overlap

            purged_mask = non_test_mask & overlap_mask

            # 2. Embargo: remove training samples immediately following each test group
            embargo_mask = np.zeros(n_samples, dtype=bool)
            if embargo_count > 0:
                for _, t_end in test_intervals:
                    in_embargo = (sample_starts > t_end) & (sample_starts <= t_end + embargo_count)
                    embargo_mask |= in_embargo

            # Non-test rows that were not already purged, but fall in post-test embargo
            effective_embargo_mask = (non_test_mask & ~purged_mask) & embargo_mask

            train_mask = non_test_mask & ~purged_mask & ~effective_embargo_mask
            train_indices = indices[train_mask]

            purge_count = int(np.sum(purged_mask))
            embargo_count_val = int(np.sum(effective_embargo_mask))

            yield train_indices, test_indices, purge_count, embargo_count_val

    def split(
        self,
        X: Any,
        y: Any = None,
        groups: Any = None,
    ) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        """Generate indices to split data into training and test set."""
        for train_indices, test_indices, _, _ in self.split_details(X, y=y, groups=groups):
            yield train_indices, test_indices


def combinatorial_purged_cross_validation_pbo(
    returns_matrix: pd.DataFrame,
    *,
    n_splits: int = 8,
    n_test_splits: int | None = None,
    holding_periods: int = 0,
    embargo_periods: int = 0,
    risk_free_rate: float = 0.0,
) -> dict[str, Any]:
    """Combinatorial Purged Cross-Validation (CPCV) Probability of Backtest Overfitting (PBO).

    Computes PBO under purged and embargoed combinatorial cross-validation.
    When holding_periods > 0, training samples near test block boundaries whose
    forward-return labels overlap with the test set are purged. An embargo window
    is additionally applied to drop post-test training observations.

    When holding_periods = 0 and embargo_periods = 0, this identically reproduces
    standard Combinatorially Symmetric Cross-Validation (CSCV).

    Args:
        returns_matrix: 2D DataFrame of shape (T, N) where T >= 2 * n_splits and N >= 2.
            Must contain finite numeric values.
        n_splits: Number of contiguous temporal blocks (S >= 4). Default is 8.
        n_test_splits: Number of out-of-sample test blocks per combination (k).
            Defaults to n_splits // 2.
        holding_periods: Forward return label holding horizon (H >= 0). Default is 0.
        embargo_periods: Observations to embargo after each test block (E >= 0). Default is 0.
        risk_free_rate: Benchmark or risk-free return subtracted in Sharpe calculation.

    Returns:
        Dictionary containing:
            - 'pbo': Probability of Backtest Overfitting (float in [0, 1]).
            - 'prob_loss': Probability of out-of-sample loss for the IS optimal strategy.
            - 'n_splits': Total time blocks S.
            - 'n_test_splits': Test blocks k.
            - 'n_combinations': Number of combinations C(S, k).
            - 'holding_periods': Applied forward holding horizon H.
            - 'embargo_periods': Applied post-test embargo horizon E.
            - 'mean_purged_samples': Average number of training samples purged per split.
            - 'mean_embargoed_samples': Average number of training samples embargoed per split.
            - 'mean_relative_rank': Average OOS relative rank percentile (omega).
            - 'median_relative_rank': Median OOS relative rank percentile.
            - 'mean_is_sharpe': Average IS Sharpe ratio of the selected strategies.
            - 'mean_oos_sharpe': Average OOS Sharpe ratio of the selected strategies.
            - 'oos_sharpe_distribution': List of OOS Sharpe ratios of chosen strategies.
    """
    if not isinstance(returns_matrix, pd.DataFrame):
        raise TypeError("returns_matrix must be a pandas DataFrame")

    if any(
        is_bool_dtype(dtype) or not is_numeric_dtype(dtype)
        for dtype in returns_matrix.dtypes
    ):
        raise TypeError("returns_matrix must contain numeric non-boolean values")

    values = returns_matrix.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("returns_matrix must contain finite values without NaN or Inf")

    n_rows, n_cols = values.shape
    if n_cols < 2:
        raise ValueError("returns_matrix must contain at least 2 strategy columns")

    if isinstance(n_splits, bool) or not isinstance(n_splits, int) or n_splits < 4:
        raise ValueError("n_splits must be an integer >= 4")

    if n_test_splits is None:
        if n_splits % 2 != 0:
            raise ValueError("n_splits must be even when n_test_splits is not specified")
        n_test = n_splits // 2
    else:
        if not isinstance(n_test_splits, int) or n_test_splits < 1 or n_test_splits >= n_splits:
            raise ValueError(f"n_test_splits must be an integer in [1, n_splits - 1], got {n_test_splits}")
        n_test = n_test_splits

    if n_rows < 2 * n_splits:
        raise ValueError(
            f"returns_matrix has {n_rows} rows; requires at least 2 * n_splits = {2 * n_splits} rows"
        )

    if isinstance(holding_periods, bool) or not isinstance(holding_periods, int) or holding_periods < 0:
        raise ValueError(f"holding_periods must be an integer >= 0, got {holding_periods}")

    if isinstance(embargo_periods, bool) or not isinstance(embargo_periods, int) or embargo_periods < 0:
        raise ValueError(f"embargo_periods must be an integer >= 0, got {embargo_periods}")

    rf = float(risk_free_rate)
    if not math.isfinite(rf):
        raise ValueError("risk_free_rate must be a finite float")

    # Fast path for classical unpurged symmetric CSCV
    if holding_periods == 0 and embargo_periods == 0 and n_test == n_splits // 2:
        return _fast_symmetric_cscv(
            values=values,
            n_rows=n_rows,
            n_cols=n_cols,
            n_splits=n_splits,
            rf=rf,
        )

    # General CPCV with PurgedGroupTimeSeriesSplit
    cv = PurgedGroupTimeSeriesSplit(
        n_splits=n_splits,
        n_test_groups=n_test,
        holding_periods=holding_periods,
        embargo_periods=embargo_periods,
    )

    omegas: list[float] = []
    oos_losses: list[bool] = []
    is_sharpes: list[float] = []
    oos_sharpes: list[float] = []
    purged_counts: list[int] = []
    embargoed_counts: list[int] = []

    for train_idx, test_idx, n_purged, n_embargoed in cv.split_details(values):
        purged_counts.append(n_purged)
        embargoed_counts.append(n_embargoed)

        if len(train_idx) < 2:
            raise ValueError(
                "Purging and embargo removed too many training samples; reduce holding_periods or embargo_periods"
            )

        # In-sample statistics
        is_data = values[train_idx]
        is_mean = is_data.mean(axis=0)
        is_var = is_data.var(axis=0, ddof=1)
        is_std = np.sqrt(np.maximum(is_var, 0.0))
        with np.errstate(divide="ignore", invalid="ignore"):
            is_sr = np.where(is_std > 0.0, (is_mean - rf) / is_std, 0.0)

        best_strategy = int(np.argmax(is_sr))
        is_sharpes.append(float(is_sr[best_strategy]))

        # Out-of-sample statistics
        oos_data = values[test_idx]
        oos_mean = oos_data.mean(axis=0)
        oos_var = oos_data.var(axis=0, ddof=1)
        oos_std = np.sqrt(np.maximum(oos_var, 0.0))
        with np.errstate(divide="ignore", invalid="ignore"):
            oos_sr = np.where(oos_std > 0.0, (oos_mean - rf) / oos_std, 0.0)

        best_oos_sr = float(oos_sr[best_strategy])
        oos_sharpes.append(best_oos_sr)
        oos_losses.append(best_oos_sr <= 0.0)

        # Relative rank of best_strategy in OOS Sharpe distribution
        strictly_worse = (oos_sr < best_oos_sr).sum()
        equal = (oos_sr == best_oos_sr).sum() - 1
        rank = 1.0 + strictly_worse + 0.5 * equal
        omega = rank / (n_cols + 1.0)
        omegas.append(float(omega))

    omegas_arr = np.array(omegas)
    pbo = float((omegas_arr <= 0.5).mean())
    prob_loss = float(np.mean(oos_losses))

    return {
        "pbo": pbo,
        "prob_loss": prob_loss,
        "n_splits": n_splits,
        "n_test_splits": n_test,
        "n_combinations": len(omegas),
        "holding_periods": holding_periods,
        "embargo_periods": embargo_periods,
        "mean_purged_samples": float(np.mean(purged_counts)),
        "mean_embargoed_samples": float(np.mean(embargoed_counts)),
        "mean_relative_rank": float(np.mean(omegas_arr)),
        "median_relative_rank": float(np.median(omegas_arr)),
        "mean_is_sharpe": float(np.mean(is_sharpes)),
        "mean_oos_sharpe": float(np.mean(oos_sharpes)),
        "oos_sharpe_distribution": oos_sharpes,
    }


def _fast_symmetric_cscv(
    values: np.ndarray,
    n_rows: int,
    n_cols: int,
    n_splits: int,
    rf: float,
) -> dict[str, Any]:
    """Optimized block-summary calculation for standard unpurged symmetric CSCV."""
    blocks = np.array_split(np.arange(n_rows), n_splits)
    block_counts = np.array([len(b) for b in blocks], dtype=float)
    block_sums = np.array([values[b].sum(axis=0) for b in blocks], dtype=float)
    block_sum_sqs = np.array([(values[b] ** 2).sum(axis=0) for b in blocks], dtype=float)

    half_s = n_splits // 2
    all_blocks = set(range(n_splits))
    combinations = list(itertools.combinations(range(n_splits), half_s))

    omegas: list[float] = []
    oos_losses: list[bool] = []
    is_sharpes: list[float] = []
    oos_sharpes: list[float] = []

    for is_idx in combinations:
        oos_idx = tuple(all_blocks.difference(is_idx))

        # IS statistics
        is_n = block_counts[list(is_idx)].sum()
        is_sum = block_sums[list(is_idx)].sum(axis=0)
        is_sum_sq = block_sum_sqs[list(is_idx)].sum(axis=0)
        is_mean = is_sum / is_n
        is_var = np.maximum((is_sum_sq - (is_sum ** 2) / is_n) / (is_n - 1.0), 0.0)
        is_std = np.sqrt(is_var)
        with np.errstate(divide="ignore", invalid="ignore"):
            is_sr = np.where(is_std > 0.0, (is_mean - rf) / is_std, 0.0)

        best_strategy = int(np.argmax(is_sr))
        is_sharpes.append(float(is_sr[best_strategy]))

        # OOS statistics
        oos_n = block_counts[list(oos_idx)].sum()
        oos_sum = block_sums[list(oos_idx)].sum(axis=0)
        oos_sum_sq = block_sum_sqs[list(oos_idx)].sum(axis=0)
        oos_mean = oos_sum / oos_n
        oos_var = np.maximum((oos_sum_sq - (oos_sum ** 2) / oos_n) / (oos_n - 1.0), 0.0)
        oos_std = np.sqrt(oos_var)
        with np.errstate(divide="ignore", invalid="ignore"):
            oos_sr = np.where(oos_std > 0.0, (oos_mean - rf) / oos_std, 0.0)

        best_oos_sr = float(oos_sr[best_strategy])
        oos_sharpes.append(best_oos_sr)
        oos_losses.append(bool(best_oos_sr <= 0.0))

        # Relative rank of best_strategy in OOS Sharpe distribution
        strictly_worse = (oos_sr < best_oos_sr).sum()
        equal = (oos_sr == best_oos_sr).sum() - 1
        rank = 1.0 + strictly_worse + 0.5 * equal
        omega = rank / (n_cols + 1.0)
        omegas.append(float(omega))

    omegas_arr = np.array(omegas)
    pbo = float((omegas_arr <= 0.5).mean())
    prob_loss = float(np.mean(oos_losses))

    return {
        "pbo": pbo,
        "prob_loss": prob_loss,
        "n_splits": n_splits,
        "n_test_splits": half_s,
        "n_combinations": len(combinations),
        "holding_periods": 0,
        "embargo_periods": 0,
        "mean_purged_samples": 0.0,
        "mean_embargoed_samples": 0.0,
        "mean_relative_rank": float(np.mean(omegas_arr)),
        "median_relative_rank": float(np.median(omegas_arr)),
        "mean_is_sharpe": float(np.mean(is_sharpes)),
        "mean_oos_sharpe": float(np.mean(oos_sharpes)),
        "oos_sharpe_distribution": oos_sharpes,
    }
