import ast
import inspect

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

import backtest.portfolio as portfolio
from backtest.portfolio import run_long_only_backtest
from backtest.slippage import (
    calculate_volume_aware_slippage_diagnostics,
    calculate_volume_aware_slippage_from_trade_weights,
)


def _volume_aware_metadata(**overrides: object) -> dict[str, object]:
    metadata: dict[str, object] = {
        "name": "unit_test_volume_aware_slippage",
        "slippage_model": "candidate_linear_participation_slippage",
        "trade_weight_source": "explicit_per_asset_trade_weights",
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

    result = run_long_only_backtest(prices, signals, rebalance_frequency="D", top_n=1)

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

    result = run_long_only_backtest(prices, signals, rebalance_frequency="D", top_n=2)

    assert result.holdings.loc[dates[1], "AAA"] == pytest.approx(0.5)
    assert result.holdings.loc[dates[1], "BBB"] == pytest.approx(0.5)
    assert result.holdings.loc[dates[1], "CCC"] == pytest.approx(0.0)
    assert result.holdings.loc[dates[1]].sum() == pytest.approx(1.0)
    assert result.assumptions["aligned_signal_coverage"] == pytest.approx(1.0)


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

    result = run_long_only_backtest(prices, signals, rebalance_frequency="D", top_n=1)

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


def test_transaction_cost_is_deducted_from_equity_curve() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
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
            rebalance_frequency="D",
            top_n=1,
            volume_aware_slippage_mode="apply_precomputed_impact",
            volume_aware_slippage_impact=impact,
        )


@pytest.mark.parametrize("missing_key", ["portfolio_notional", "trade_weight_source"])
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
            rebalance_frequency="D",
            top_n=1,
            volume_aware_slippage_mode="apply_precomputed_impact",
            volume_aware_slippage_impact=impact,
            volume_aware_slippage_metadata=_volume_aware_metadata(
                trade_weight_source=" ",
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


def test_total_return_uses_initial_capital_base_when_first_row_has_slippage() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        rebalance_frequency="D",
        top_n=1,
        slippage_bps=100.0,
        signal_lag_periods=0,
    )

    assert result.slippage_costs.loc[dates[0]] == pytest.approx(0.01)
    assert result.total_trading_costs.loc[dates[0]] == pytest.approx(0.01)
    assert result.equity_curve.loc[dates[0]] == pytest.approx(0.99)
    assert result.metrics["total_return"] == pytest.approx(-0.01)


def test_positive_transaction_cost_and_slippage_are_not_zero_diagnostic() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
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
        run_long_only_backtest(prices, signals, rebalance_frequency="D", top_n=1, slippage_bps=-1.0)


def test_total_return_uses_initial_capital_base_when_first_row_has_cost() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        rebalance_frequency="D",
        top_n=1,
        transaction_cost_bps=100.0,
        signal_lag_periods=0,
    )

    assert result.equity_curve.loc[dates[0]] == pytest.approx(0.99)
    assert result.metrics["total_return"] == pytest.approx(-0.01)


def test_fixed_cost_that_exhausts_portfolio_raises() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)

    with pytest.raises(ValueError, match="trading costs exhausted the portfolio"):
        run_long_only_backtest(
            prices,
            signals,
            rebalance_frequency="D",
            top_n=1,
            transaction_cost_bps=10_000.0,
            signal_lag_periods=0,
        )


def test_precomputed_impact_that_exhausts_portfolio_raises() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)
    impact = pd.Series([1.0, 0.0], index=dates)

    with pytest.raises(ValueError, match="trading costs exhausted the portfolio"):
        run_long_only_backtest(
            prices,
            signals,
            rebalance_frequency="D",
            top_n=1,
            volume_aware_slippage_mode="apply_precomputed_impact",
            volume_aware_slippage_impact=impact,
            volume_aware_slippage_metadata=_volume_aware_metadata(),
            signal_lag_periods=0,
        )


def test_missing_held_asset_return_raises_by_default() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, None]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    with pytest.raises(ValueError, match="Missing return for held asset AAA"):
        run_long_only_backtest(prices, signals, rebalance_frequency="D", top_n=1)


def test_missing_held_asset_zero_return_policy_is_explicit() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, None]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
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

    with pytest.raises(ValueError, match="benchmark_prices are missing"):
        run_long_only_backtest(
            prices,
            signals,
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
        rebalance_frequency="D",
        top_n=1,
        benchmark_prices=benchmark,
        benchmark_missing_policy="zero_return",
    )

    assert result.benchmark_equity_curve is not None
    assert result.benchmark_equity_curve.loc[dates[1]] == pytest.approx(1.0)
    assert result.benchmark_equity_curve.loc[dates[2]] == pytest.approx(1.02)
    assert result.assumptions["benchmark_missing_policy"] == "zero_return"


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
        rebalance_frequency="D",
        top_n=1,
        benchmark_prices=benchmark,
        benchmark_missing_policy="zero_return",
    )

    assert result.benchmark_equity_curve is not None
    assert result.benchmark_equity_curve.loc[strategy_dates[0]] == pytest.approx(1.0)
    assert result.benchmark_equity_curve.loc[strategy_dates[1]] == pytest.approx(1.02)


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

    result = run_long_only_backtest(prices, signals, rebalance_frequency="D", top_n=1)

    assert result.holdings.loc[dates[1], "AAA"] == pytest.approx(1.0)
    assert result.returns.loc[dates[2]] == pytest.approx(0.10)
    assert result.returns.loc[dates[3]] == pytest.approx(0.10)
    assert result.equity_curve.loc[dates[3]] == pytest.approx(1.21)
    assert result.metrics["total_return"] == pytest.approx(0.21)


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
