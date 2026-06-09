import ast
import inspect

import pandas as pd
import pytest

import backtest.portfolio as portfolio
from backtest.portfolio import run_long_only_backtest


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
    assert result.assumptions["benchmark_missing_policy"] == "zero_return"


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
