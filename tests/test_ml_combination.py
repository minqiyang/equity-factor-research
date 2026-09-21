"""Unit tests for walk_forward_ml_factor_composite."""

import numpy as np
import pandas as pd
import pytest

from features.ml_combination import (
    _SUPPORTED_MODELS,
    walk_forward_ml_factor_composite,
)


@pytest.fixture
def sample_ml_data():
    dates = pd.bdate_range("2020-01-02", periods=200)
    assets = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    rng = np.random.default_rng(42)

    # 3 distinct factor panels
    f1 = pd.DataFrame(rng.normal(size=(len(dates), len(assets))), index=dates, columns=assets)
    f2 = pd.DataFrame(rng.normal(size=(len(dates), len(assets))), index=dates, columns=assets)
    f3 = pd.DataFrame(rng.normal(size=(len(dates), len(assets))), index=dates, columns=assets)

    # Forward returns correlated with f1 + f2
    noise = rng.normal(scale=0.1, size=(len(dates), len(assets)))
    fwd_ret = (f1 * 0.05 + f2 * 0.03 + noise) * 0.1

    # Month-end rebalance dates
    rebalance_dates = dates[dates.is_month_end]
    if len(rebalance_dates) < 8:
        rebalance_dates = dates[::20]

    return [f1, f2, f3], fwd_ret, rebalance_dates


def test_walk_forward_ml_composite_deterministic(sample_ml_data):
    factors, fwd_ret, rebalance_dates = sample_ml_data
    comp1, imp1, meta1 = walk_forward_ml_factor_composite(
        factors,
        fwd_ret,
        rebalance_dates,
        model_type="random_forest",
        min_train_periods=3,
        forward_holding_periods=10,
        random_state=42,
    )
    comp2, imp2, meta2 = walk_forward_ml_factor_composite(
        factors,
        fwd_ret,
        rebalance_dates,
        model_type="random_forest",
        min_train_periods=3,
        forward_holding_periods=10,
        random_state=42,
    )

    pd.testing.assert_frame_equal(comp1, comp2)
    pd.testing.assert_frame_equal(imp1, imp2)
    assert meta1["evaluated_rebalance_count"] == meta2["evaluated_rebalance_count"]
    assert meta1["evaluated_rebalance_count"] > 0


def test_walk_forward_ml_composite_zero_lookahead(sample_ml_data):
    factors, fwd_ret, rebalance_dates = sample_ml_data
    comp_base, _, _ = walk_forward_ml_factor_composite(
        factors,
        fwd_ret,
        rebalance_dates,
        model_type="ridge",
        min_train_periods=3,
        forward_holding_periods=10,
        random_state=42,
    )

    # Pick a rebalance date t where composite is non-NaN
    valid_dates = comp_base.dropna().index
    assert len(valid_dates) > 0
    t = valid_dates[0]
    t_pos = fwd_ret.index.get_loc(t)
    horizon_rows = 1 + 10  # execution_lag=1, forward_holding=10

    # 1. Mutate forward returns in future (>= t) and at unclosed historical dates
    fwd_ret_mutated = fwd_ret.copy()
    fwd_ret_mutated.loc[t:] = 999.0

    # Mutate all dates strictly after past_dates[-1] + horizon_rows
    past_closed = [
        d for d in rebalance_dates
        if d < t and fwd_ret.index.get_loc(pd.Timestamp(d)) + horizon_rows <= t_pos
    ]
    assert len(past_closed) >= 3
    last_closed_date = past_closed[-1]

    # Mutate any unclosed dates between last_closed_date and t
    unclosed_dates = [d for d in fwd_ret.index if d > last_closed_date]
    fwd_ret_mutated.loc[unclosed_dates] = 888.0

    comp_mutated, _, _ = walk_forward_ml_factor_composite(
        factors,
        fwd_ret_mutated,
        rebalance_dates,
        model_type="ridge",
        min_train_periods=3,
        forward_holding_periods=10,
        random_state=42,
    )

    # Composite at date t MUST be completely unchanged by open or future labels!
    pd.testing.assert_series_equal(comp_base.loc[t], comp_mutated.loc[t])

    # 2. Positive control: mutating the last admitted closed date MUST change predictions
    fwd_ret_closed_mutated = fwd_ret.copy()
    fwd_ret_closed_mutated.loc[last_closed_date] = 555.0
    comp_closed_mutated, _, _ = walk_forward_ml_factor_composite(
        factors,
        fwd_ret_closed_mutated,
        rebalance_dates,
        model_type="ridge",
        min_train_periods=3,
        forward_holding_periods=10,
        random_state=42,
    )
    assert not comp_base.loc[t].equals(comp_closed_mutated.loc[t])


@pytest.mark.parametrize("model_type", sorted(_SUPPORTED_MODELS))
def test_walk_forward_ml_composite_all_supported_models(sample_ml_data, model_type):
    factors, fwd_ret, rebalance_dates = sample_ml_data
    comp, imp, meta = walk_forward_ml_factor_composite(
        factors,
        fwd_ret,
        rebalance_dates,
        model_type=model_type,
        min_train_periods=3,
        forward_holding_periods=10,
        random_state=42,
    )

    assert comp.shape == factors[0].shape
    assert not imp.empty
    assert meta["model_type"] == model_type
    assert meta["evaluated_rebalance_count"] > 0


def test_walk_forward_ml_composite_rolling_window(sample_ml_data):
    factors, fwd_ret, rebalance_dates = sample_ml_data
    _, _, meta_exp = walk_forward_ml_factor_composite(
        factors,
        fwd_ret,
        rebalance_dates,
        model_type="ridge",
        min_train_periods=3,
        training_window=None,
        forward_holding_periods=10,
    )
    _, _, meta_roll = walk_forward_ml_factor_composite(
        factors,
        fwd_ret,
        rebalance_dates,
        model_type="ridge",
        min_train_periods=3,
        training_window=3,
        forward_holding_periods=10,
    )

    assert meta_roll["mean_training_samples"] <= meta_exp["mean_training_samples"]


def test_walk_forward_ml_composite_invalid_inputs(sample_ml_data):
    factors, fwd_ret, rebalance_dates = sample_ml_data

    # Unsupported model
    with pytest.raises(ValueError, match="Unsupported model_type"):
        walk_forward_ml_factor_composite(
            factors, fwd_ret, rebalance_dates, model_type="deep_neural_net"
        )

    # Mismatched factor_names
    with pytest.raises(ValueError, match="factor_names length"):
        walk_forward_ml_factor_composite(
            factors, fwd_ret, rebalance_dates, factor_names=["f1", "f2"]
        )

    # Empty factors
    with pytest.raises(ValueError):
        walk_forward_ml_factor_composite([], fwd_ret, rebalance_dates)
