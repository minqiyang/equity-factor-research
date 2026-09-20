"""Walk-forward non-linear machine learning factor combination models.

This module provides strictly causal, zero-lookahead machine learning factor
combinations (Random Forest, Gradient Boosting, HistGradientBoosting, Ridge)
that learn non-linear mappings from classical alpha features to forward returns.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import Ridge

from features.combination import _ordered_rebalance_dates, _validate_factor_list
from features.operators import cross_sectional_zscore


_SUPPORTED_MODELS = {
    "random_forest",
    "gradient_boosting",
    "hist_gradient_boosting",
    "ridge",
}


def _instantiate_model(
    model_type: str,
    *,
    random_state: int,
    hyperparameters: dict[str, Any] | None = None,
) -> Any:
    params = dict(hyperparameters or {})
    if model_type == "random_forest":
        return RandomForestRegressor(
            n_estimators=params.get("n_estimators", 50),
            max_depth=params.get("max_depth", 4),
            min_samples_leaf=params.get("min_samples_leaf", 2),
            random_state=random_state,
            n_jobs=-1,
        )
    if model_type == "gradient_boosting":
        return GradientBoostingRegressor(
            n_estimators=params.get("n_estimators", 50),
            max_depth=params.get("max_depth", 3),
            learning_rate=params.get("learning_rate", 0.05),
            min_samples_leaf=params.get("min_samples_leaf", 2),
            random_state=random_state,
        )
    if model_type == "hist_gradient_boosting":
        return HistGradientBoostingRegressor(
            max_iter=params.get("max_iter", 50),
            max_depth=params.get("max_depth", 3),
            learning_rate=params.get("learning_rate", 0.05),
            min_samples_leaf=params.get("min_samples_leaf", 2),
            random_state=random_state,
        )
    if model_type == "ridge":
        return Ridge(
            alpha=params.get("alpha", 1.0),
            random_state=random_state,
        )
    raise ValueError(
        f"Unsupported model_type '{model_type}'. Supported models: {sorted(_SUPPORTED_MODELS)}"
    )


def walk_forward_ml_factor_composite(
    factors: list[pd.DataFrame],
    forward_returns: pd.DataFrame,
    rebalance_dates: pd.DatetimeIndex,
    *,
    factor_names: list[str] | None = None,
    model_type: str = "random_forest",
    min_train_periods: int = 5,
    min_train_samples: int = 6,
    training_window: int | None = None,
    execution_lag_periods: int = 1,
    forward_holding_periods: int = 21,
    random_state: int = 42,
    hyperparameters: dict[str, Any] | None = None,
    standardize_features: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Generate a walk-forward machine learning composite factor panel.

    On each rebalance date `t`, the model trains strictly on historical dates `s`
    whose execution-aligned forward-return labels have completely closed by `t`:
    `source_row(s) + execution_lag_periods + forward_holding_periods <= source_row(t)`.

    Args:
        factors: Non-empty list of date-indexed asset panels with identical shape.
        forward_returns: Date-indexed panel of forward return targets.
        rebalance_dates: Rebalance dates at which the model retrains and predicts.
        factor_names: Optional names for the input factors (used in importance tracking).
        model_type: Model algorithm ('random_forest', 'gradient_boosting',
            'hist_gradient_boosting', 'ridge'). Default is 'random_forest'.
        min_train_periods: Minimum number of closed rebalance dates required before
            generating predictions. Dates before receive NaN.
        training_window: If set, limits training to the most recent N closed dates
            (rolling window); otherwise uses all available closed dates (expanding window).
        execution_lag_periods: Lag periods between signal date and trade execution (default 1).
        forward_holding_periods: Number of periods held for return calculation (default 21).
        random_state: Integer seed for deterministic reproduction (default 42).
        hyperparameters: Optional dictionary of regressor hyperparameters.
        standardize_features: Whether to cross-sectionally z-score factors before ML (default True).

    Returns:
        tuple of:
            - composite: Date-indexed panel of composite cross-sectional z-score predictions.
            - feature_importances: DataFrame of feature importances across rebalance dates.
            - metadata: Dictionary containing run summary, sample counts, and parameters.
    """
    validated = _validate_factor_list(factors)
    n_factors = len(validated)
    if factor_names is None:
        names = [f"factor_{i}" for i in range(n_factors)]
    else:
        if len(factor_names) != n_factors:
            raise ValueError(
                f"factor_names length ({len(factor_names)}) must match factors count ({n_factors})"
            )
        names = list(factor_names)

    panel_index = validated[0].index
    columns = validated[0].columns
    if not forward_returns.index.equals(panel_index) or not forward_returns.columns.equals(columns):
        raise ValueError("forward_returns must have identical index and columns to factor panels")

    if standardize_features:
        feature_panels = [cross_sectional_zscore(p) for p in validated]
    else:
        feature_panels = validated

    ordered_rebalances = _ordered_rebalance_dates(rebalance_dates)
    horizon_rows = execution_lag_periods + forward_holding_periods

    composite_output = pd.DataFrame(np.nan, index=panel_index, columns=columns, dtype=float)
    importance_records: dict[pd.Timestamp, np.ndarray] = {}
    train_sample_counts: dict[pd.Timestamp, int] = {}

    for pos, t in enumerate(ordered_rebalances):
        t_ts = pd.Timestamp(t)
        if t_ts not in panel_index:
            t_pos = int(panel_index.searchsorted(t_ts, side="right")) - 1
        else:
            t_pos = int(panel_index.get_loc(t_ts))

        if t_pos < horizon_rows:
            continue

        # Find historical rebalance dates whose forward return window closed by t
        past_dates = [
            d for d in ordered_rebalances
            if d < t_ts and panel_index.get_loc(pd.Timestamp(d)) + horizon_rows <= t_pos
        ]

        if len(past_dates) < min_train_periods:
            continue

        if training_window is not None and training_window > 0:
            past_dates = past_dates[-training_window:]

        # Build training set (X_train, y_train) from past closed dates
        x_train_list: list[np.ndarray] = []
        y_train_list: list[float] = []

        for past_date in past_dates:
            p_ts = pd.Timestamp(past_date)
            # Stack factor values for all assets on past_date: shape (n_assets, n_factors)
            feat_matrix = np.column_stack([p.loc[p_ts].to_numpy(dtype=float) for p in feature_panels])
            targets = forward_returns.loc[p_ts].to_numpy(dtype=float)

            valid_mask = np.isfinite(targets) & np.all(np.isfinite(feat_matrix), axis=1)
            if np.any(valid_mask):
                x_train_list.append(feat_matrix[valid_mask])
                y_train_list.extend(targets[valid_mask].tolist())

        if not x_train_list:
            continue

        x_train = np.vstack(x_train_list)
        y_train = np.array(y_train_list, dtype=float)

        if len(y_train) < min_train_samples:
            continue

        train_sample_counts[t_ts] = len(y_train)
        model = _instantiate_model(
            model_type,
            random_state=random_state,
            hyperparameters=hyperparameters,
        )
        model.fit(x_train, y_train)

        # Extract feature importances
        if hasattr(model, "feature_importances_"):
            importance_records[t_ts] = np.array(model.feature_importances_, dtype=float)
        elif hasattr(model, "coef_"):
            importance_records[t_ts] = np.abs(np.array(model.coef_, dtype=float))
        else:
            from sklearn.inspection import permutation_importance

            perm = permutation_importance(
                model, x_train, y_train, n_repeats=2, random_state=random_state
            )
            importance_records[t_ts] = np.maximum(perm.importances_mean, 0.0)

        # Predict on current date t
        feat_t = np.column_stack([p.loc[t_ts].to_numpy(dtype=float) for p in feature_panels])
        valid_t = np.all(np.isfinite(feat_t), axis=1)

        pred_t = np.full(len(columns), np.nan, dtype=float)
        if np.any(valid_t):
            raw_pred = model.predict(feat_t[valid_t])
            pred_t[valid_t] = raw_pred

        # Cross-sectionally standardize predictions to z-scores
        finite_mask = np.isfinite(pred_t)
        if np.sum(finite_mask) >= 2:
            vals = pred_t[finite_mask]
            std = float(np.std(vals, ddof=1))
            if std > 1e-12:
                pred_t[finite_mask] = (vals - np.mean(vals)) / std
            else:
                pred_t[finite_mask] = 0.0

        # Assign and hold on [t, next_t)
        next_t = ordered_rebalances[pos + 1] if pos + 1 < len(ordered_rebalances) else None
        if next_t is None:
            active_dates = panel_index[panel_index >= t_ts]
        else:
            next_ts = pd.Timestamp(next_t)
            active_dates = panel_index[(panel_index >= t_ts) & (panel_index < next_ts)]

        for d in active_dates:
            composite_output.loc[d] = pred_t

    importance_df = (
        pd.DataFrame.from_dict(importance_records, orient="index", columns=names)
        if importance_records
        else pd.DataFrame(columns=names)
    )
    importance_df.index.name = "rebalance_date"

    metadata = {
        "model_type": model_type,
        "n_factors": n_factors,
        "factor_names": names,
        "min_train_periods": min_train_periods,
        "training_window": training_window,
        "execution_lag_periods": execution_lag_periods,
        "forward_holding_periods": forward_holding_periods,
        "random_state": random_state,
        "evaluated_rebalance_count": len(importance_records),
        "total_rebalances": len(ordered_rebalances),
        "mean_training_samples": float(np.mean(list(train_sample_counts.values()))) if train_sample_counts else 0.0,
    }

    return composite_output, importance_df, metadata
