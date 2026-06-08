import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from backtest.portfolio import run_long_only_backtest
from features.liquidity import (
    apply_universe_mask_to_signals,
    average_daily_volume_eligibility,
    average_dollar_volume_eligibility,
    construct_liquidity_universe,
)


def _synthetic_panel(values: dict[str, list[float]]) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=len(next(iter(values.values()))), freq="D")
    return pd.DataFrame(values, index=dates)


def test_synthetic_masked_signals_feed_existing_backtester_with_lag() -> None:
    prices = _synthetic_panel(
        {
            "AAA": [10.0, 10.0, 10.0, 11.0, 12.0],
            "BBB": [5.0, 5.0, 5.0, 5.0, 5.0],
            "CCC": [20.0, 20.0, 20.0, 20.0, 20.0],
        },
    )
    volume = _synthetic_panel(
        {
            "AAA": [100.0, 100.0, 100.0, 100.0, 100.0],
            "BBB": [10.0, 10.0, 10.0, 10.0, 10.0],
            "CCC": [100.0, 100.0, 0.0, 100.0, 100.0],
        },
    )
    raw_signals = _synthetic_panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0, 5.0],
            "BBB": [100.0, 100.0, 100.0, 100.0, 100.0],
            "CCC": [7.0, 8.0, np.nan, 9.0, 10.0],
        },
    )

    adv_eligible = average_daily_volume_eligibility(
        volume,
        window=2,
        min_average_volume=50.0,
    )
    dollar_eligible = average_dollar_volume_eligibility(
        prices,
        volume,
        window=2,
        min_average_dollar_volume=1000.0,
    )
    universe = construct_liquidity_universe(
        adv_eligible & dollar_eligible,
        name="synthetic_backtest_smoke_universe",
    )
    masked = apply_universe_mask_to_signals(
        raw_signals,
        universe.universe_mask,
        name="synthetic_backtest_smoke_masked_signals",
    )

    result = run_long_only_backtest(
        prices,
        masked.signals,
        rebalance_frequency="D",
        top_n=2,
        transaction_cost_bps=10.0,
        signal_lag_periods=1,
    )

    expected_masked_signals = pd.DataFrame(
        {
            "AAA": [np.nan, np.nan, 3.0, 4.0, 5.0],
            "BBB": [np.nan, np.nan, np.nan, np.nan, np.nan],
            "CCC": [np.nan, np.nan, np.nan, np.nan, np.nan],
        },
        index=prices.index,
    )
    expected_holdings = pd.DataFrame(
        {
            "AAA": [0.0, 0.0, 0.0, 1.0, 1.0],
            "BBB": [0.0, 0.0, 0.0, 0.0, 0.0],
            "CCC": [0.0, 0.0, 0.0, 0.0, 0.0],
        },
        index=prices.index,
    )

    assert_frame_equal(masked.signals, expected_masked_signals)
    assert_frame_equal(result.holdings, expected_holdings)
    assert result.assumptions["signal_lag_periods"] == 1
    assert result.assumptions["top_n"] == 2
    assert result.assumptions["transaction_cost_bps"] == 10.0
    assert result.assumptions["aligned_signal_coverage"] == pytest.approx(3 / 15)
    assert result.transaction_costs.loc[prices.index[3]] == pytest.approx(0.001)
    assert result.returns.loc[prices.index[3]] == pytest.approx(-0.001)
    assert result.returns.loc[prices.index[4]] == pytest.approx((12.0 / 11.0) - 1.0)
    assert result.metrics["total_transaction_cost_impact"] == pytest.approx(0.001)


def test_synthetic_masked_backtest_uses_prior_masked_signal_row() -> None:
    prices = _synthetic_panel(
        {
            "AAA": [10.0, 10.0, 10.0, 10.0],
            "BBB": [10.0, 10.0, 10.0, 10.0],
        },
    )
    raw_signals = _synthetic_panel(
        {
            "AAA": [1.0, 1.0, -100.0, -100.0],
            "BBB": [0.0, 0.0, 100.0, 100.0],
        },
    )
    universe_mask = pd.DataFrame(
        {
            "AAA": [True, True, False, False],
            "BBB": [False, False, True, True],
        },
        index=prices.index,
    )
    masked = apply_universe_mask_to_signals(raw_signals, universe_mask)

    result = run_long_only_backtest(
        prices,
        masked.signals,
        rebalance_frequency="D",
        top_n=1,
        signal_lag_periods=1,
    )

    assert result.holdings.loc[prices.index[1], "AAA"] == pytest.approx(1.0)
    assert result.holdings.loc[prices.index[2], "AAA"] == pytest.approx(1.0)
    assert result.holdings.loc[prices.index[2], "BBB"] == pytest.approx(0.0)
    assert result.holdings.loc[prices.index[3], "AAA"] == pytest.approx(0.0)
    assert result.holdings.loc[prices.index[3], "BBB"] == pytest.approx(1.0)
