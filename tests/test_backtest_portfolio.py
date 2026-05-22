import pandas as pd
import pytest

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
    assert result.returns.loc[dates[1]] == pytest.approx(-0.01)
    assert result.equity_curve.loc[dates[1]] == pytest.approx(0.99)
    assert result.equity_curve.loc[dates[2]] == pytest.approx(0.99)


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
