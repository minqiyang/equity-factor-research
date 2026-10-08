import ast
import inspect
import types

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

import backtest.portfolio as portfolio
from backtest.portfolio import (
    capture_backtest_source_provenance,
    run_long_only_backtest as _run_long_only_backtest,
)
from backtest.slippage import (
    calculate_volume_aware_slippage_diagnostics,
    calculate_volume_aware_slippage_from_trade_weights,
)
from m55_bytes_support import BASE_COMMIT, assert_same_bytes, module_at


def _volume_aware_metadata(**overrides: object) -> dict[str, object]:
    metadata: dict[str, object] = {
        "name": "unit_test_volume_aware_slippage",
        "slippage_model": "candidate_linear_participation_slippage",
        "trade_weight_source": "explicit_per_asset_trade_weights",
        "return_impact_basis": "beginning_period_portfolio_value",
        "portfolio_notional": 100_000.0,
        "price_field": "adjusted_close",
        "volume_policy": "synthetic_share_volume",
        "window": 1,
        "volume_lag": 1,
        "base_slippage_bps": 0.0,
        "participation_slope_bps": 100.0,
        "max_participation": 0.1,
        "missing_or_zero_liquidity_policy": "raise",
        "stale_volume_policy": "raise",
        "participation_above_cap_policy": "raise",
    }
    metadata.update(overrides)
    return metadata


def _full_evaluation_bounds(prices: pd.DataFrame) -> dict[str, pd.Timestamp]:
    return {
        "evaluation_start": prices.index[0],
        "evaluation_end": prices.index[-1],
    }


def run_long_only_backtest(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    **kwargs: object,
):
    """Run ordinary fixtures with provenance captured at construction."""

    return _run_long_only_backtest(
        prices,
        signals,
        source_provenance=capture_backtest_source_provenance(prices, signals),
        **kwargs,
    )


def test_backtest_does_not_use_future_signals_for_current_rebalance() -> None:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 100.0, 110.0, 120.0],
            "BBB": [100.0, 100.0, 100.0, 100.0],
        },
        index=dates,
    )
    signals = pd.DataFrame(
        {
            "AAA": [10.0, -10.0, -10.0, -10.0],
            "BBB": [0.0, 20.0, 20.0, 20.0],
        },
        index=dates,
    )

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
    )

    assert result.holdings.loc[dates[1], "AAA"] == pytest.approx(1.0)
    assert result.holdings.loc[dates[1], "BBB"] == pytest.approx(0.0)


def test_equal_weighting_for_selected_assets() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 101.0, 102.0],
            "BBB": [100.0, 101.0, 102.0],
            "CCC": [100.0, 101.0, 102.0],
        },
        index=dates,
    )
    signals = pd.DataFrame(
        {
            "AAA": [3.0, 3.0, 3.0],
            "BBB": [2.0, 2.0, 2.0],
            "CCC": [1.0, 1.0, 1.0],
        },
        index=dates,
    )

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=2,
    )

    assert result.holdings.loc[dates[1], "AAA"] == pytest.approx(0.5)
    assert result.holdings.loc[dates[1], "BBB"] == pytest.approx(0.5)
    assert result.holdings.loc[dates[1], "CCC"] == pytest.approx(0.0)
    assert result.holdings.loc[dates[1]].sum() == pytest.approx(1.0)
    assert result.assumptions["aligned_signal_coverage"] == pytest.approx(1.0)
    assert result.metrics["average_holding_count"] == pytest.approx(2.0)
    assert result.metrics["average_position_concentration_hhi"] == pytest.approx(0.5)
    assert result.metrics["max_position_concentration_hhi"] == pytest.approx(0.5)


def test_position_cap_holds_residual_cash_and_drives_accounting() -> None:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = pd.DataFrame(
        {"AAA": [100.0, 100.0, 110.0, 110.0], "BBB": [100.0] * 4},
        index=dates,
    )
    signals = pd.DataFrame(
        {"AAA": [2.0] * 4, "BBB": [1.0] * 4},
        index=dates,
    )

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=2,
        max_position_weight=0.3,
        transaction_cost_bps=100.0,
    )

    assert result.holdings.loc[dates[1]].tolist() == pytest.approx([0.3, 0.3])
    assert result.turnover.loc[dates[1]] == pytest.approx(0.6)
    assert result.transaction_costs.loc[dates[1]] == pytest.approx(0.006)
    assert result.gross_returns.loc[dates[2]] == pytest.approx(0.03)
    assert result.holdings.loc[dates[2]].tolist() == pytest.approx([0.3, 0.3])
    assert result.assumptions["max_position_weight"] == pytest.approx(0.3)
    assert result.assumptions["position_constraint_breach_policy"] == "clip"
    assert result.assumptions["position_constraint_renormalization"] == "none"
    assert result.assumptions["position_constraint_infeasible_target_policy"] == (
        "clip_and_hold_cash"
    )
    assert result.assumptions["holding_episode_terminal_open_count"] == 2


def test_position_cap_is_optional_and_does_not_emit_metadata_when_absent() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
    )

    assert "position_constraint_contract" not in result.assumptions


def test_holding_episode_metrics_include_only_applied_volume_impact() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame(
        {"AAA": [100.0] * 3, "BBB": [100.0] * 3},
        index=dates,
    )
    signals = pd.DataFrame(
        {"AAA": [2.0, 0.0, 0.0], "BBB": [0.0, 2.0, 2.0]},
        index=dates,
    )
    impact = pd.Series([0.0, 0.01, 0.02], index=dates)

    diagnostic = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        volume_aware_slippage_impact=impact,
    )
    applied = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        volume_aware_slippage_mode="apply_precomputed_impact",
        volume_aware_slippage_impact=impact,
        volume_aware_slippage_metadata=_volume_aware_metadata(),
    )

    assert diagnostic.metrics["average_holding_period_return"] == pytest.approx(0.0)
    assert applied.metrics["average_holding_period_return"] == pytest.approx(-0.02)


def test_turnover_uses_target_weight_changes_on_rebalance_dates() -> None:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 100.0, 100.0, 100.0],
            "BBB": [100.0, 100.0, 100.0, 100.0],
        },
        index=dates,
    )
    signals = pd.DataFrame(
        {
            "AAA": [1.0, 0.0, 0.0, 0.0],
            "BBB": [0.0, 1.0, 1.0, 1.0],
        },
        index=dates,
    )

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
    )

    assert result.turnover.loc[dates[0]] == pytest.approx(0.0)
    assert result.turnover.loc[dates[1]] == pytest.approx(1.0)
    assert result.turnover.loc[dates[2]] == pytest.approx(2.0)
    assert result.turnover.loc[dates[3]] == pytest.approx(0.0)


def test_holdings_drift_between_rebalances_and_turnover_uses_pretrade_weights() -> None:
    dates = pd.date_range("2024-01-01", periods=12, freq="D")
    prices = pd.DataFrame(
        {
            "AAA": [100.0] * 5 + [200.0, 400.0] + [400.0] * 5,
            "BBB": [100.0] * len(dates),
        },
        index=dates,
    )
    signals = pd.DataFrame(
        {"AAA": [1.0] * len(dates), "BBB": [1.0] * len(dates)},
        index=dates,
    )

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="W-FRI",
        top_n=2,
    )

    first_rebalance = pd.Timestamp("2024-01-05")
    second_rebalance = pd.Timestamp("2024-01-12")

    assert result.holdings.loc[first_rebalance, "AAA"] == pytest.approx(0.5)
    assert result.holdings.loc[first_rebalance, "BBB"] == pytest.approx(0.5)
    assert result.holdings.loc[pd.Timestamp("2024-01-06"), "AAA"] == pytest.approx(2.0 / 3.0)
    assert result.holdings.loc[pd.Timestamp("2024-01-06"), "BBB"] == pytest.approx(1.0 / 3.0)
    assert result.holdings.loc[pd.Timestamp("2024-01-07"), "AAA"] == pytest.approx(0.8)
    assert result.holdings.loc[pd.Timestamp("2024-01-07"), "BBB"] == pytest.approx(0.2)
    assert result.equity_curve.loc[pd.Timestamp("2024-01-07")] == pytest.approx(2.5)
    assert result.turnover.loc[pd.Timestamp("2024-01-06")] == pytest.approx(0.0)
    assert result.turnover.loc[pd.Timestamp("2024-01-07")] == pytest.approx(0.0)
    assert result.turnover.loc[second_rebalance] == pytest.approx(0.6)
    assert result.trade_weights.loc[first_rebalance, "AAA"] == pytest.approx(0.5)
    assert result.trade_weights.loc[first_rebalance, "BBB"] == pytest.approx(0.5)
    assert result.trade_weights.loc[pd.Timestamp("2024-01-06")].eq(0.0).all()
    assert result.trade_weights.loc[pd.Timestamp("2024-01-07")].eq(0.0).all()
    assert result.trade_weights.loc[second_rebalance, "AAA"] == pytest.approx(0.3)
    assert result.trade_weights.loc[second_rebalance, "BBB"] == pytest.approx(0.3)
    assert_series_equal(
        result.trade_weights.sum(axis=1).rename("turnover"),
        result.turnover,
    )

    volume = pd.DataFrame(100_000.0, index=dates, columns=prices.columns)
    diagnostics = calculate_volume_aware_slippage_from_trade_weights(
        result.trade_weights,
        prices,
        volume,
        window=1,
        portfolio_notional=100.0,
        max_participation=1.0,
    )
    assert_frame_equal(diagnostics.trade_weights, result.trade_weights)
    assert diagnostics.summary.loc[second_rebalance, "total_trade_weight"] == pytest.approx(
        0.6
    )
    assert diagnostics.parameters["trade_weight_source"] == (
        "explicit_per_asset_trade_weights"
    )

    assert result.holdings.loc[second_rebalance, "AAA"] == pytest.approx(0.5)
    assert result.holdings.loc[second_rebalance, "BBB"] == pytest.approx(0.5)
    assert result.assumptions["holdings_model"] == "drifted_between_rebalances"
    assert result.assumptions["turnover_reference"] == "drifted_pretrade_weights"


def test_drifted_holdings_survive_near_total_but_positive_loss() -> None:
    dates = pd.date_range("2024-01-01", periods=7, freq="D")
    prices = pd.DataFrame(
        {
            "AAA": [100.0] * 5 + [1e-10, 1e-10],
            "BBB": [100.0] * 5 + [2e-10, 2e-10],
        },
        index=dates,
    )
    signals = pd.DataFrame(1.0, index=dates, columns=prices.columns)

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="W-FRI",
        top_n=2,
    )

    crash_date = pd.Timestamp("2024-01-06")
    assert result.equity_curve.loc[crash_date] > 0.0
    assert result.equity_curve.loc[crash_date] == pytest.approx(1.5e-12)
    assert result.holdings.loc[crash_date].sum() == pytest.approx(1.0)


def test_transaction_cost_is_deducted_from_equity_curve() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        transaction_cost_bps=100.0,
    )

    assert result.transaction_costs.loc[dates[1]] == pytest.approx(0.01)
    assert result.slippage_costs.loc[dates[1]] == pytest.approx(0.0)
    assert result.total_trading_costs.loc[dates[1]] == pytest.approx(0.01)
    assert result.returns.loc[dates[1]] == pytest.approx(-0.01)
    assert result.equity_curve.loc[dates[1]] == pytest.approx(0.99)
    assert result.equity_curve.loc[dates[2]] == pytest.approx(0.99)
    assert result.metrics["total_transaction_cost_impact"] == pytest.approx(0.01)
    assert result.metrics["total_slippage_cost_impact"] == pytest.approx(0.0)
    assert result.metrics["total_trading_cost_impact"] == pytest.approx(0.01)


def test_fixed_bps_slippage_is_deducted_separately_from_transaction_cost() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        transaction_cost_bps=100.0,
        slippage_bps=50.0,
    )

    assert result.transaction_costs.loc[dates[1]] == pytest.approx(0.01)
    assert result.slippage_costs.loc[dates[1]] == pytest.approx(0.005)
    assert result.total_trading_costs.loc[dates[1]] == pytest.approx(0.015)
    assert result.returns.loc[dates[1]] == pytest.approx(-0.015)
    assert result.equity_curve.loc[dates[1]] == pytest.approx(0.985)
    assert result.metrics["total_transaction_cost_impact"] == pytest.approx(0.01)
    assert result.metrics["total_slippage_cost_impact"] == pytest.approx(0.005)
    assert result.metrics["total_trading_cost_impact"] == pytest.approx(0.015)
    assert result.assumptions["transaction_cost_bps"] == pytest.approx(100.0)
    assert result.assumptions["slippage_bps"] == pytest.approx(50.0)
    assert result.assumptions["cost_model"] == "fixed_bps_on_target_weight_turnover"
    assert result.assumptions["slippage_model"] == "fixed_bps_on_target_weight_turnover"


def test_close_time_fixed_costs_scale_with_post_return_portfolio_value() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 100.0, 200.0],
            "BBB": [100.0, 100.0, 100.0],
        },
        index=dates,
    )
    signals = pd.DataFrame(
        {
            "AAA": [1.0, 0.0, 0.0],
            "BBB": [0.0, 1.0, 1.0],
        },
        index=dates,
    )

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        transaction_cost_bps=100.0,
        slippage_bps=50.0,
    )

    assert result.gross_returns.loc[dates[2]] == pytest.approx(1.0)
    assert result.turnover.loc[dates[2]] == pytest.approx(2.0)
    assert result.transaction_costs.loc[dates[2]] == pytest.approx(0.04)
    assert result.slippage_costs.loc[dates[2]] == pytest.approx(0.02)
    assert result.total_trading_costs.loc[dates[2]] == pytest.approx(0.06)
    assert result.returns.loc[dates[2]] == pytest.approx(0.94)
    assert result.equity_curve.loc[dates[2]] == pytest.approx(1.9109)


def test_volume_aware_slippage_default_is_diagnostic_only() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)
    candidate_impact = pd.Series(
        [0.0, 0.01, 0.0],
        index=dates,
        name="portfolio_slippage_impact",
    )

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        volume_aware_slippage_impact=candidate_impact,
        volume_aware_slippage_metadata=_volume_aware_metadata(),
    )

    assert result.returns.loc[dates[1]] == pytest.approx(0.0)
    assert result.equity_curve.loc[dates[2]] == pytest.approx(1.0)
    assert result.volume_aware_slippage_costs.eq(0.0).all()
    assert result.total_trading_costs.loc[dates[1]] == pytest.approx(0.0)
    assert result.metrics["total_volume_aware_slippage_cost_impact"] == pytest.approx(0.0)
    assert result.assumptions["volume_aware_slippage_mode"] == "diagnostic_only"
    assert result.assumptions["volume_aware_slippage_applied_to_returns"] is False
    assert result.assumptions["zero_cost_or_slippage_is_diagnostic"] is True


def test_precomputed_volume_aware_slippage_is_deducted_separately() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)
    impact = pd.Series([0.0, 0.003, 0.0], index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        transaction_cost_bps=100.0,
        volume_aware_slippage_mode="apply_precomputed_impact",
        volume_aware_slippage_impact=impact,
        volume_aware_slippage_metadata=_volume_aware_metadata(),
    )

    assert result.gross_returns.loc[dates[1]] == pytest.approx(0.0)
    assert result.holdings.loc[dates[1], "AAA"] == pytest.approx(1.0)
    assert result.turnover.loc[dates[1]] == pytest.approx(1.0)
    assert result.transaction_costs.loc[dates[1]] == pytest.approx(0.01)
    assert result.slippage_costs.loc[dates[1]] == pytest.approx(0.0)
    assert result.volume_aware_slippage_costs.loc[dates[1]] == pytest.approx(0.003)
    assert result.total_trading_costs.loc[dates[1]] == pytest.approx(0.013)
    assert result.returns.loc[dates[1]] == pytest.approx(-0.013)
    assert result.equity_curve.loc[dates[1]] == pytest.approx(0.987)
    assert result.metrics["total_transaction_cost_impact"] == pytest.approx(0.01)
    assert result.metrics["total_slippage_cost_impact"] == pytest.approx(0.0)
    assert result.metrics["total_volume_aware_slippage_cost_impact"] == pytest.approx(0.003)
    assert result.metrics["total_trading_cost_impact"] == pytest.approx(0.013)
    assert result.assumptions["volume_aware_slippage_mode"] == "apply_precomputed_impact"
    assert result.assumptions["volume_aware_slippage_applied_to_returns"] is True
    assert result.assumptions["volume_aware_slippage_model"] == "candidate_linear_participation_slippage"
    assert result.assumptions["volume_aware_slippage_source"] == "unit_test_volume_aware_slippage"
    assert result.assumptions["volume_aware_trade_weight_source"] == (
        "explicit_per_asset_trade_weights"
    )
    assert result.assumptions["volume_aware_input_return_impact_basis"] == (
        "beginning_period_portfolio_value"
    )
    assert result.assumptions["volume_aware_applied_return_impact_basis"] == (
        "beginning_period_portfolio_value"
    )
    assert result.assumptions["portfolio_notional"] == pytest.approx(100_000.0)
    assert result.assumptions["volume_aware_price_field"] == "adjusted_close"
    assert result.assumptions["volume_policy"] == "synthetic_share_volume"
    assert result.assumptions["volume_lag"] == 1
    assert result.assumptions["rolling_dollar_volume_window"] == 1
    assert result.assumptions["stale_volume_policy"] == "raise"
    assert result.assumptions["max_participation"] == pytest.approx(0.1)
    assert result.assumptions["participation_above_cap_policy"] == "raise"
    assert result.assumptions["missing_or_zero_liquidity_policy"] == "raise"
    assert result.assumptions["zero_cost_or_slippage_is_diagnostic"] is False


def test_volume_aware_slippage_helper_output_can_feed_precomputed_boundary() -> None:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = pd.DataFrame(
        {"AAA": [100.0, 100.0, 100.0, 100.0], "BBB": [100.0, 100.0, 100.0, 100.0]},
        index=dates,
    )
    signals = pd.DataFrame(
        {"AAA": [1.0, 1.0, 1.0, 1.0], "BBB": [0.0, 0.0, 0.0, 0.0]},
        index=dates,
    )
    target_weights = pd.DataFrame(
        {"AAA": [0.0, 1.0, 1.0, 1.0], "BBB": [0.0, 0.0, 0.0, 0.0]},
        index=dates,
    )
    volume = pd.DataFrame(
        {"AAA": [100.0, 100.0, 100.0, 100.0], "BBB": [100.0, 100.0, 100.0, 100.0]},
        index=dates,
    )

    diagnostics = calculate_volume_aware_slippage_diagnostics(
        target_weights,
        prices,
        volume,
        window=1,
        portfolio_notional=100.0,
        participation_slope_bps=100.0,
        volume_lag=1,
        max_participation=1.0,
        name="helper_integration_test",
    )
    metadata = {
        **diagnostics.parameters,
        "price_field": "adjusted_close",
        "volume_policy": "synthetic_share_volume",
        "stale_volume_policy": "raise",
    }

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        volume_aware_slippage_mode="apply_precomputed_impact",
        volume_aware_slippage_impact=diagnostics.portfolio_slippage_impact,
        volume_aware_slippage_metadata=metadata,
    )

    assert diagnostics.portfolio_slippage_impact.loc[dates[1]] == pytest.approx(0.0001)
    assert result.volume_aware_slippage_costs.loc[dates[1]] == pytest.approx(0.0001)
    assert result.returns.loc[dates[1]] == pytest.approx(-0.0001)
    assert result.assumptions["volume_aware_slippage_source"] == "helper_integration_test"
    assert result.assumptions["volume_aware_trade_weight_source"] == (
        "derived_from_target_weight_difference"
    )


def test_post_return_volume_impact_is_scaled_to_beginning_return_basis() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 100.0, 200.0],
            "BBB": [100.0, 100.0, 100.0],
        },
        index=dates,
    )
    signals = pd.DataFrame(
        {
            "AAA": [1.0, 0.0, 0.0],
            "BBB": [0.0, 1.0, 1.0],
        },
        index=dates,
    )
    baseline = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
    )
    volume = pd.DataFrame(1_000_000.0, index=dates, columns=prices.columns)
    diagnostics = calculate_volume_aware_slippage_from_trade_weights(
        baseline.trade_weights,
        prices,
        volume,
        window=1,
        portfolio_notional=100.0,
        base_slippage_bps=100.0,
        max_participation=1.0,
    )
    metadata = {
        **diagnostics.parameters,
        "price_field": "adjusted_close",
        "volume_policy": "synthetic_share_volume",
        "stale_volume_policy": "raise",
    }

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        volume_aware_slippage_mode="apply_precomputed_impact",
        volume_aware_slippage_impact=diagnostics.portfolio_slippage_impact,
        volume_aware_slippage_metadata=metadata,
    )

    assert diagnostics.portfolio_slippage_impact.loc[dates[2]] == pytest.approx(0.02)
    assert result.gross_returns.loc[dates[2]] == pytest.approx(1.0)
    assert result.volume_aware_slippage_costs.loc[dates[2]] == pytest.approx(0.04)
    assert result.returns.loc[dates[2]] == pytest.approx(0.96)
    assert result.equity_curve.loc[dates[2]] == pytest.approx(1.9404)
    assert result.assumptions["volume_aware_input_return_impact_basis"] == (
        "post_return_portfolio_value"
    )
    assert result.assumptions["volume_aware_applied_return_impact_basis"] == (
        "beginning_period_portfolio_value"
    )


@pytest.mark.parametrize(
    ("impact", "match"),
    [
        (
            pd.Series([0.0, 0.001], index=pd.date_range("2024-01-01", periods=2, freq="D")),
            "index must exactly match",
        ),
        (
            pd.Series([0.0, None, 0.0], index=pd.date_range("2024-01-01", periods=3, freq="D")),
            "must not contain missing values",
        ),
        (
            pd.Series([0.0, -0.001, 0.0], index=pd.date_range("2024-01-01", periods=3, freq="D")),
            "must be non-negative",
        ),
    ],
)
def test_precomputed_volume_aware_slippage_rejects_invalid_impact_series(
    impact: pd.Series,
    match: str,
) -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    with pytest.raises(ValueError, match=match):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            rebalance_frequency="D",
            top_n=1,
            volume_aware_slippage_mode="apply_precomputed_impact",
            volume_aware_slippage_impact=impact,
            volume_aware_slippage_metadata=_volume_aware_metadata(),
        )


def test_precomputed_volume_aware_slippage_requires_metadata() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)
    impact = pd.Series([0.0, 0.001, 0.0], index=dates)

    with pytest.raises(ValueError, match="volume_aware_slippage_metadata is required"):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            rebalance_frequency="D",
            top_n=1,
            volume_aware_slippage_mode="apply_precomputed_impact",
            volume_aware_slippage_impact=impact,
        )


@pytest.mark.parametrize(
    "missing_key",
    ["portfolio_notional", "trade_weight_source", "return_impact_basis"],
)
def test_precomputed_volume_aware_slippage_rejects_missing_metadata_keys(
    missing_key: str,
) -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)
    impact = pd.Series([0.0, 0.001, 0.0], index=dates)
    metadata = _volume_aware_metadata()
    metadata.pop(missing_key)

    with pytest.raises(ValueError, match=missing_key):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            rebalance_frequency="D",
            top_n=1,
            volume_aware_slippage_mode="apply_precomputed_impact",
            volume_aware_slippage_impact=impact,
            volume_aware_slippage_metadata=metadata,
        )


def test_precomputed_volume_aware_slippage_rejects_blank_trade_weight_source() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)
    impact = pd.Series([0.0, 0.001, 0.0], index=dates)

    with pytest.raises(ValueError, match="trade_weight_source must be a non-empty"):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            rebalance_frequency="D",
            top_n=1,
            volume_aware_slippage_mode="apply_precomputed_impact",
            volume_aware_slippage_impact=impact,
            volume_aware_slippage_metadata=_volume_aware_metadata(
                trade_weight_source=" ",
            ),
        )


def test_precomputed_volume_aware_slippage_rejects_unknown_return_basis() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)
    impact = pd.Series(0.0, index=prices.index)

    with pytest.raises(ValueError, match="return_impact_basis must be"):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            top_n=1,
            volume_aware_slippage_mode="apply_precomputed_impact",
            volume_aware_slippage_impact=impact,
            volume_aware_slippage_metadata=_volume_aware_metadata(
                return_impact_basis="unknown_basis",
            ),
        )


def test_positive_fixed_and_volume_aware_slippage_cannot_be_combined_by_default() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)
    impact = pd.Series([0.0, 0.001, 0.0], index=dates)

    with pytest.raises(ValueError, match="combined-model policy"):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            rebalance_frequency="D",
            top_n=1,
            slippage_bps=1.0,
            volume_aware_slippage_mode="apply_precomputed_impact",
            volume_aware_slippage_impact=impact,
            volume_aware_slippage_metadata=_volume_aware_metadata(),
        )


def test_invalid_volume_aware_slippage_mode_raises() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)

    with pytest.raises(ValueError, match="volume_aware_slippage_mode"):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            rebalance_frequency="D",
            top_n=1,
            volume_aware_slippage_mode="apply_internal_volume_model",
        )


def test_slippage_without_transaction_cost_is_explicit_diagnostic() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        transaction_cost_bps=0.0,
        slippage_bps=25.0,
    )

    assert result.transaction_costs.loc[dates[1]] == pytest.approx(0.0)
    assert result.slippage_costs.loc[dates[1]] == pytest.approx(0.0025)
    assert result.total_trading_costs.loc[dates[1]] == pytest.approx(0.0025)
    assert result.returns.loc[dates[1]] == pytest.approx(-0.0025)
    assert result.assumptions["zero_cost_or_slippage_is_diagnostic"] is True


def test_transaction_cost_without_slippage_is_explicit_diagnostic() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        transaction_cost_bps=25.0,
        slippage_bps=0.0,
    )

    assert result.transaction_costs.loc[dates[1]] == pytest.approx(0.0025)
    assert result.slippage_costs.loc[dates[1]] == pytest.approx(0.0)
    assert result.total_trading_costs.loc[dates[1]] == pytest.approx(0.0025)
    assert result.returns.loc[dates[1]] == pytest.approx(-0.0025)
    assert result.assumptions["zero_cost_or_slippage_is_diagnostic"] is True


def test_total_return_uses_initial_capital_base_with_zero_cost_anchor() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        slippage_bps=100.0,
    )

    assert result.slippage_costs.loc[dates[0]] == pytest.approx(0.0)
    assert result.total_trading_costs.loc[dates[0]] == pytest.approx(0.0)
    assert result.equity_curve.loc[dates[0]] == pytest.approx(1.0)
    assert result.slippage_costs.loc[dates[1]] == pytest.approx(0.01)
    assert result.metrics["total_return"] == pytest.approx(-0.01)


def test_positive_transaction_cost_and_slippage_are_not_zero_diagnostic() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        transaction_cost_bps=10.0,
        slippage_bps=10.0,
    )

    assert result.assumptions["zero_cost_or_slippage_is_diagnostic"] is False


def test_negative_slippage_bps_raises() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)

    with pytest.raises(ValueError, match="slippage_bps must be non-negative"):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            rebalance_frequency="D",
            top_n=1,
            slippage_bps=-1.0,
        )


def test_transaction_cost_uses_initial_capital_base_after_zero_cost_anchor() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        transaction_cost_bps=100.0,
    )

    assert result.equity_curve.loc[dates[0]] == pytest.approx(1.0)
    assert result.transaction_costs.loc[dates[0]] == pytest.approx(0.0)
    assert result.equity_curve.loc[dates[1]] == pytest.approx(0.99)
    assert result.metrics["total_return"] == pytest.approx(-0.01)


def test_fixed_cost_that_exhausts_portfolio_raises() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)

    with pytest.raises(
        ValueError,
        match="portfolio_insolvent_or_non_finite_after_costs",
    ):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            rebalance_frequency="D",
            top_n=1,
            transaction_cost_bps=10_000.0,
        )


def test_precomputed_impact_that_exhausts_portfolio_raises() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)
    impact = pd.Series([0.0, 1.0], index=dates)

    with pytest.raises(
        ValueError,
        match="portfolio_insolvent_or_non_finite_after_costs",
    ):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            rebalance_frequency="D",
            top_n=1,
            volume_aware_slippage_mode="apply_precomputed_impact",
            volume_aware_slippage_impact=impact,
            volume_aware_slippage_metadata=_volume_aware_metadata(),
        )


def test_missing_held_asset_return_raises_by_default() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, None]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    with pytest.raises(ValueError, match="incoming_price_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            rebalance_frequency="D",
            top_n=1,
        )


def test_missing_held_asset_zero_return_policy_is_explicit() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, None]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        missing_price_policy="zero_return",
    )

    assert result.returns.loc[dates[2]] == pytest.approx(0.0)
    assert result.assumptions["missing_price_policy"] == "zero_return"


def test_missing_benchmark_price_raises_by_default() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)
    benchmark = pd.Series([100.0, 102.0], index=[dates[0], dates[2]])

    with pytest.raises(ValueError, match="benchmark_prices_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            rebalance_frequency="D",
            top_n=1,
            benchmark_prices=benchmark,
        )


def test_missing_benchmark_zero_return_policy_is_explicit() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)
    benchmark = pd.Series([100.0, 102.0], index=[dates[0], dates[2]])

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        benchmark_prices=benchmark,
        benchmark_missing_policy="zero_return",
    )

    assert result.benchmark_equity_curve is not None
    assert result.benchmark_equity_curve.loc[dates[1]] == pytest.approx(1.0)
    assert result.benchmark_equity_curve.loc[dates[2]] == pytest.approx(1.02)
    assert result.assumptions["benchmark_missing_policy"] == "zero_return"
    assert "tracking_error" not in result.metrics
    assert "tracking_error_contract" not in result.assumptions


def test_benchmark_zero_return_policy_preserves_prior_price_anchor() -> None:
    strategy_dates = pd.date_range("2024-01-02", periods=2, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=strategy_dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=strategy_dates)
    benchmark = pd.Series(
        [100.0, 102.0],
        index=pd.to_datetime(["2024-01-01", "2024-01-03"]),
    )

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        benchmark_prices=benchmark,
        benchmark_missing_policy="zero_return",
    )

    assert result.benchmark_equity_curve is not None
    assert result.benchmark_equity_curve.loc[strategy_dates[0]] == pytest.approx(1.0)
    assert result.benchmark_equity_curve.loc[strategy_dates[1]] == pytest.approx(1.02)


def test_tracking_error_uses_net_returns_and_records_contract_metadata() -> None:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 110.0, 121.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0, 1.0]}, index=dates)
    benchmark = pd.Series([100.0, 100.0, 102.0, 102.0], index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
        transaction_cost_bps=100.0,
        benchmark_prices=benchmark,
    )

    assert result.benchmark_returns is not None
    expected_active_returns = (
        result.returns.iloc[1:] - result.benchmark_returns.iloc[1:]
    )
    assert result.metrics["tracking_error"] == pytest.approx(
        expected_active_returns.std(ddof=0) * np.sqrt(252)
    )
    assert result.assumptions["tracking_error_contract"] == (
        "daily_close_to_close_v1"
    )
    assert result.assumptions["tracking_error_return_basis"] == (
        "strategy_net_after_applied_costs_vs_cost_free_benchmark"
    )
    assert result.assumptions["tracking_error_first_row_policy"] == (
        "exclude_synthetic_anchor"
    )
    assert result.assumptions["tracking_error_terminal_row_policy"] == (
        "include_terminal_close_to_close_window"
    )
    assert result.assumptions["benchmark_cost_basis"] == "cost_free_price_return"


def test_tracking_error_integration_rejects_timezone_and_frequency_mismatch() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 101.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)
    benchmark = pd.Series([100.0, 100.0, 101.0], index=dates)

    with pytest.raises(ValueError, match="benchmark_prices_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            rebalance_frequency="D",
            top_n=1,
            benchmark_prices=benchmark.tz_localize("UTC"),
        )

    with pytest.raises(ValueError, match="periods_per_year_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            **_full_evaluation_bounds(prices),
            rebalance_frequency="D",
            top_n=1,
            benchmark_prices=benchmark,
            periods_per_year=12,
        )


def test_simple_synthetic_price_example() -> None:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 100.0, 110.0, 121.0],
            "BBB": [100.0, 100.0, 100.0, 100.0],
        },
        index=dates,
    )
    signals = pd.DataFrame(
        {
            "AAA": [1.0, 1.0, 1.0, 1.0],
            "BBB": [0.0, 0.0, 0.0, 0.0],
        },
        index=dates,
    )

    result = run_long_only_backtest(
        prices,
        signals,
        **_full_evaluation_bounds(prices),
        rebalance_frequency="D",
        top_n=1,
    )

    assert result.holdings.loc[dates[1], "AAA"] == pytest.approx(1.0)
    assert result.returns.loc[dates[2]] == pytest.approx(0.10)
    assert result.returns.loc[dates[3]] == pytest.approx(0.10)
    assert result.equity_curve.loc[dates[3]] == pytest.approx(1.21)
    assert result.metrics["total_return"] == pytest.approx(0.21)
    assert_frame_equal(result.signed_trade_weights.abs(), result.trade_weights)
    assert result.assumptions["holding_episode_contract"] == (
        "continuous_positive_weight_v1"
    )
    assert result.assumptions["holding_episode_terminal_open_count"] == 1
    assert result.assumptions["holding_episode_closed_count"] == 0
    assert np.isnan(result.metrics["episode_hit_rate"])


def test_backtester_has_no_data_vendor_credential_or_execution_imports() -> None:
    source = inspect.getsource(portfolio)
    tree = ast.parse(source)
    forbidden_terms = {
        "requests",
        "urllib",
        "yfinance",
        "alpaca",
        "ccxt",
        "broker",
        "brokerage",
        "order",
        "credential",
        "dotenv",
        "subprocess",
        "AlgorithmImports",
    }
    imported_modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    for module_name in imported_modules:
        assert not any(term.lower() in module_name.lower() for term in forbidden_terms)


def _dated_cost_fixture() -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0, 100.0], "BBB": [100.0, 100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 0.0, 1.0, 1.0], "BBB": [0.0, 1.0, 0.0, 0.0]}, index=dates)
    return prices, signals


def test_dated_costs_apply_the_rate_of_each_row() -> None:
    prices, signals = _dated_cost_fixture()
    dates = prices.index
    rates = pd.DataFrame({"transaction_cost_bps": [9.0, 10.0, 20.0, 30.0], "slippage_bps": [9.0, 40.0, 30.0, 0.5]},
                         index=dates)

    result = run_long_only_backtest(
        prices, signals, **_full_evaluation_bounds(prices), rebalance_frequency="D", top_n=1, dated_costs=rates,
    )

    # Row 1 buys AAA from cash (turnover 1); row 2 switches to BBB (2); row 3 switches back (2).
    assert result.turnover.tolist() == pytest.approx([0.0, 1.0, 2.0, 2.0])
    assert result.transaction_costs.tolist() == pytest.approx([0.0, 0.0010, 0.0040, 0.0060])
    assert result.slippage_costs.tolist() == pytest.approx([0.0, 0.0040, 0.0060, 0.0001])
    assert result.assumptions["dated_costs"] == "per_row_transaction_and_slippage_bps"
    assert result.assumptions["zero_cost_or_slippage_is_diagnostic"] is False


def test_dated_costs_equal_fixed_costs_when_the_rate_is_constant() -> None:
    prices, signals = _dated_cost_fixture()
    rates = pd.DataFrame({"transaction_cost_bps": 7.0, "slippage_bps": 11.0}, index=prices.index)

    dated = run_long_only_backtest(
        prices, signals, **_full_evaluation_bounds(prices), rebalance_frequency="D", top_n=1, dated_costs=rates,
    )
    fixed = run_long_only_backtest(
        prices, signals, **_full_evaluation_bounds(prices), rebalance_frequency="D", top_n=1,
        transaction_cost_bps=7.0, slippage_bps=11.0,
    )

    assert_series_equal(dated.returns, fixed.returns)
    assert_series_equal(dated.total_trading_costs, fixed.total_trading_costs)
    assert "dated_costs" not in fixed.assumptions


def test_dated_costs_with_a_zero_rate_row_are_diagnostic() -> None:
    prices, signals = _dated_cost_fixture()
    rates = pd.DataFrame({"transaction_cost_bps": [5.0, 5.0, 0.0, 5.0], "slippage_bps": 5.0}, index=prices.index)

    result = run_long_only_backtest(
        prices, signals, **_full_evaluation_bounds(prices), rebalance_frequency="D", top_n=1, dated_costs=rates,
    )

    assert result.assumptions["zero_cost_or_slippage_is_diagnostic"] is True


@pytest.mark.parametrize(
    ("change", "extra"),
    [
        ("missing_row", {}),
        ("negative", {}),
        ("columns", {}),
        ("fixed_rate", {"transaction_cost_bps": 1.0}),
    ],
)
def test_dated_costs_refuse_invalid_schedules(change: str, extra: dict[str, float]) -> None:
    prices, signals = _dated_cost_fixture()
    rates = pd.DataFrame({"transaction_cost_bps": 5.0, "slippage_bps": 5.0}, index=prices.index)
    if change == "missing_row":
        rates = rates.iloc[:-1]
    elif change == "negative":
        rates.iloc[2, 0] = -1.0
    elif change == "columns":
        rates = rates[["slippage_bps", "transaction_cost_bps"]]

    with pytest.raises(portfolio.BacktestValidationError, match="dated_costs_invalid"):
        run_long_only_backtest(
            prices, signals, **_full_evaluation_bounds(prices), rebalance_frequency="D", top_n=1,
            dated_costs=rates, **extra,
        )


def test_dated_costs_record_the_applied_schedule() -> None:
    prices, signals = _dated_cost_fixture()
    rates = pd.DataFrame({"transaction_cost_bps": [5.0, 5.0, 2.0, 2.0], "slippage_bps": [20.0, 20.0, 8.0, 8.0]},
                         index=prices.index)

    result = run_long_only_backtest(
        prices, signals, **_full_evaluation_bounds(prices), rebalance_frequency="D", top_n=1, dated_costs=rates,
    )

    assert result.assumptions["dated_cost_segments"] == [
        {"first_date": "2024-01-01", "transaction_cost_bps": 5.0, "slippage_bps": 20.0},
        {"first_date": "2024-01-03", "transaction_cost_bps": 2.0, "slippage_bps": 8.0},
    ]


@pytest.mark.parametrize("change", ["duplicate_index", "text", "volume_aware", "impact_model"])
def test_dated_costs_refuse_more_invalid_inputs(change: str) -> None:
    prices, signals = _dated_cost_fixture()
    rates = pd.DataFrame({"transaction_cost_bps": 5.0, "slippage_bps": 5.0}, index=prices.index)
    extra: dict[str, object] = {}
    if change == "duplicate_index":
        rates = pd.concat([rates, rates.iloc[:1]])
    elif change == "text":
        rates = rates.astype(object)
        rates.iloc[1, 0] = "five"
    elif change == "impact_model":
        extra = {"impact_model": portfolio.SquareRootImpactModel()}
    else:
        extra = {"volume_aware_slippage_mode": "apply_precomputed_impact",
                 "volume_aware_slippage_impact": pd.Series(0.0, index=prices.index),
                 "volume_aware_slippage_metadata": _volume_aware_metadata()}

    with pytest.raises(portfolio.BacktestValidationError, match="dated_costs_invalid"):
        run_long_only_backtest(
            prices, signals, **_full_evaluation_bounds(prices), rebalance_frequency="D", top_n=1,
            dated_costs=rates, **extra,
        )


def test_dated_costs_apply_on_a_halt_locked_row() -> None:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, np.nan, 100.0], "BBB": 100.0, "CCC": 100.0}, index=dates)
    rates = pd.DataFrame({"transaction_cost_bps": [0.0, 10.0, 30.0, 0.0], "slippage_bps": [0.0, 10.0, 30.0, 0.0]},
                         index=dates)
    flat = pd.DataFrame(1.0, index=dates, columns=prices.columns)
    flat.iloc[1, 1] = 3.0           # row 2 targets (0.2, 0.6, 0.2), but AAA has no close: the row is locked

    result = run_long_only_backtest(
        prices, flat, **_full_evaluation_bounds(prices), rebalance_frequency="D", top_pct=1.0,
        weighting_scheme="proportional", dated_costs=rates, missing_price_policy="halt_gap_return_v1",
    )

    assert len(result.halt_ledger["locked_execution_rows"]) == 1
    assert result.turnover.loc[dates[2]] > 0.0
    assert result.total_trading_costs.loc[dates[2]] == pytest.approx(
        result.turnover.loc[dates[2]] * 60.0 / 10_000.0 * (1.0 + result.gross_returns.loc[dates[2]]))


# Per-asset slippage rates (card m55-confirm, trial family v1 amendment 3) -------------------------

def _locked_fixture() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, np.nan, 100.0], "BBB": [100.0, 101.0, 99.0, 100.0],
                           "CCC": [100.0, 99.5, 100.5, 101.0]}, index=dates)
    rates = pd.DataFrame({"transaction_cost_bps": [0.0, 10.0, 30.0, 5.0], "slippage_bps": [0.0, 10.0, 30.0, 5.0]},
                         index=dates)
    flat = pd.DataFrame(1.0, index=dates, columns=prices.columns)
    flat.iloc[1, 1] = 3.0           # row 2 targets (0.2, 0.6, 0.2), but AAA has no close: the row is locked
    return prices, flat, rates


def _runs(module: types.ModuleType) -> list:
    """The existing dated-cost, fixed-cost, and halt-locked fixtures, run on ``module``."""
    def run(prices, signals, **kwargs):
        return module.run_long_only_backtest(
            prices, signals, source_provenance=module.capture_backtest_source_provenance(prices, signals),
            **_full_evaluation_bounds(prices), **kwargs)
    prices, signals = _dated_cost_fixture()
    dated = pd.DataFrame({"transaction_cost_bps": [9.0, 10.0, 20.0, 30.0], "slippage_bps": [9.0, 40.0, 30.0, 0.5]},
                         index=prices.index)
    locked_prices, flat, locked_rates = _locked_fixture()
    return [run(prices, signals, rebalance_frequency="D", top_n=1, dated_costs=dated),
            run(prices, signals, rebalance_frequency="D", top_n=1, transaction_cost_bps=7.0, slippage_bps=11.0),
            run(locked_prices, flat, rebalance_frequency="D", top_pct=1.0, weighting_scheme="proportional",
                dated_costs=locked_rates, missing_price_policy="halt_gap_return_v1")]


def test_without_asset_rates_every_output_has_the_bytes_of_the_base_runner(tmp_path) -> None:
    base = module_at(BASE_COMMIT, "src/backtest/portfolio.py", "portfolio_8590b2e", tmp_path)
    for new, old in zip(_runs(portfolio), _runs(base)):
        assert_same_bytes(new, old)
        assert "asset_slippage" not in new.assumptions


def test_equal_asset_rates_give_the_bytes_of_dated_costs() -> None:
    for prices, signals, rates, kwargs in (
            (*_dated_cost_fixture(), None, {"top_n": 1}),
            (*_locked_fixture(), {"top_pct": 1.0, "weighting_scheme": "proportional",
                                  "missing_price_policy": "halt_gap_return_v1"})):
        if rates is None:
            rates = pd.DataFrame({"transaction_cost_bps": [9.0, 10.0, 20.0, 30.0],
                                  "slippage_bps": [9.0, 40.0, 30.0, 0.5]}, index=prices.index)
        equal = pd.DataFrame(np.repeat(rates[["slippage_bps"]].to_numpy(), prices.shape[1], axis=1),
                             index=prices.index, columns=prices.columns)
        common = {**_full_evaluation_bounds(prices), "rebalance_frequency": "D", "dated_costs": rates, **kwargs}
        plain = run_long_only_backtest(prices, signals, **common)
        per_asset = run_long_only_backtest(prices, signals, asset_slippage_bps=equal, **common)
        assert per_asset.assumptions.pop("asset_slippage") == "per_asset_slippage_bps"
        assert_same_bytes(per_asset, plain)


def test_asset_rates_charge_each_trade_at_its_own_rate() -> None:
    prices, signals = _dated_cost_fixture()
    rates = pd.DataFrame({"transaction_cost_bps": 5.0, "slippage_bps": 10.0}, index=prices.index)
    per_asset = pd.DataFrame({"AAA": [10.0, 50.0, 10.0, 70.0], "BBB": [10.0, 10.0, 25.0, 10.0]}, index=prices.index)

    result = run_long_only_backtest(prices, signals, **_full_evaluation_bounds(prices), rebalance_frequency="D",
                                    top_n=1, dated_costs=rates, asset_slippage_bps=per_asset)

    # Row 1 buys AAA (rate 50); row 2 sells AAA and buys BBB (10 and 25); row 3 sells BBB and buys AAA (10, 70).
    gross = 1.0 + result.gross_returns
    expected = [0.0, 1.0 * 50.0, 1.0 * 10.0 + 1.0 * 25.0, 1.0 * 10.0 + 1.0 * 70.0]
    assert result.slippage_costs.tolist() == pytest.approx([e / 10_000.0 * g for e, g in zip(expected, gross)])
    assert result.transaction_costs.tolist() == pytest.approx([0.0, 0.0005, 0.0010, 0.0010])


def test_asset_rates_apply_the_full_cost_on_a_halt_locked_row() -> None:
    """H-3c: the free sleeve pays the whole row cost, the per-asset part too, so a run whose single row rate gives
    the same row cost holds the same weights after the locked row."""
    prices, flat, rates = _locked_fixture()
    per_asset = pd.DataFrame({"AAA": 30.0, "BBB": 90.0, "CCC": 30.0}, index=prices.index)
    per_asset.iloc[1] = 10.0
    per_asset.iloc[3] = 5.0
    common = {**_full_evaluation_bounds(prices), "rebalance_frequency": "D", "top_pct": 1.0,
              "weighting_scheme": "proportional", "missing_price_policy": "halt_gap_return_v1"}

    result = run_long_only_backtest(prices, flat, dated_costs=rates, asset_slippage_bps=per_asset, **common)

    row = prices.index[2]
    assert len(result.halt_ledger["locked_execution_rows"]) == 1
    trades = result.trade_weights.loc[row]
    gross = 1.0 + result.gross_returns.loc[row]
    assert trades["BBB"] > 0.0
    assert result.slippage_costs.loc[row] == pytest.approx(float((trades * per_asset.loc[row]).sum()) / 1e4 * gross)
    same = rates.copy()
    same.loc[row, "slippage_bps"] = float((trades * per_asset.loc[row]).sum() / trades.sum())
    single = run_long_only_backtest(prices, flat, dated_costs=same, **common)
    assert result.total_trading_costs.loc[row] == pytest.approx(single.total_trading_costs.loc[row], rel=1e-12)
    assert_frame_equal(result.holdings, single.holdings, check_exact=False, rtol=1e-12)
    assert_series_equal(result.returns, single.returns, check_exact=False, rtol=1e-12)


@pytest.mark.parametrize("change", ["no_dated_costs", "columns", "missing_row", "negative", "nan", "duplicate_index"])
def test_asset_rates_refuse_invalid_panels(change: str) -> None:
    prices, signals = _dated_cost_fixture()
    rates = pd.DataFrame({"transaction_cost_bps": 5.0, "slippage_bps": 5.0}, index=prices.index)
    panel = pd.DataFrame(5.0, index=prices.index, columns=prices.columns)
    extra: dict[str, object] = {"dated_costs": rates}
    if change == "no_dated_costs":
        extra = {"slippage_bps": 5.0, "transaction_cost_bps": 5.0}
    elif change == "columns":
        panel = panel[["BBB", "AAA"]]
    elif change == "missing_row":
        panel = panel.iloc[:-1]
    elif change == "negative":
        panel.iloc[2, 1] = -1.0
    elif change == "nan":
        panel.iloc[1, 0] = np.nan
    else:
        panel = pd.concat([panel, panel.iloc[:1]])

    with pytest.raises(portfolio.BacktestValidationError, match="asset_slippage_invalid"):
        run_long_only_backtest(prices, signals, **_full_evaluation_bounds(prices), rebalance_frequency="D", top_n=1,
                               asset_slippage_bps=panel, **extra)
