"""Deterministic tests for long-short decile spread backtesting."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest.long_short import LongShortBacktestResult, run_long_short_backtest


def _make_long_short_panels(
    n_days: int = 15,
    n_assets: int = 20,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range("2025-01-06", periods=n_days)
    assets = [f"A{i:02d}" for i in range(n_assets)]
    # Prices drift upwards slightly
    np.random.seed(42)
    daily_returns = np.random.normal(0.0005, 0.01, size=(n_days, n_assets))
    price_matrix = 100.0 * np.cumprod(1.0 + daily_returns, axis=0)
    prices = pd.DataFrame(price_matrix, index=dates, columns=assets)

    # Signals: A00 is highest (20), A19 is lowest (1)
    signals = pd.DataFrame(
        {assets[i]: float(n_assets - i) for i in range(n_assets)},
        index=dates,
    )
    return prices, signals


def test_long_short_dollar_neutral_equal_weight() -> None:
    prices, signals = _make_long_short_panels(n_assets=20)

    result = run_long_short_backtest(
        prices,
        signals,
        rebalance_frequency="D",
        quantiles=10,
        weighting_scheme="equal",
        transaction_cost_bps=0.0,
        slippage_bps=0.0,
        gross_leverage=1.0,
    )

    assert isinstance(result, LongShortBacktestResult)
    assert result.assumptions["dollar_neutral"] is True
    assert result.assumptions["gross_leverage"] == 1.0

    # With 20 assets and 10 quantiles, each decile has 2 assets
    # Gross leverage = 1.0 -> long leg sum = +0.5, short leg sum = +0.5
    # Net exposure = sum(net_holdings) = 0.0
    for date in prices.index[2:]:
        net_row = result.net_holdings.loc[date]
        assert net_row.sum() == pytest.approx(0.0, abs=1e-10)
        assert net_row.abs().sum() == pytest.approx(1.0, abs=1e-10)

        # Top decile (A00, A01) long with weight +0.25 each
        assert result.long_holdings.loc[date, "A00"] == pytest.approx(0.25)
        assert result.long_holdings.loc[date, "A01"] == pytest.approx(0.25)

        # Bottom decile (A18, A19) short with weight +0.25 each
        assert result.short_holdings.loc[date, "A18"] == pytest.approx(0.25)
        assert result.short_holdings.loc[date, "A19"] == pytest.approx(0.25)


def test_long_short_rank_weighting() -> None:
    prices, signals = _make_long_short_panels(n_assets=20)

    result = run_long_short_backtest(
        prices,
        signals,
        rebalance_frequency="D",
        quantiles=10,
        weighting_scheme="rank",
        gross_leverage=1.0,
    )

    # In top decile (A00 score 20, A01 score 19):
    # A01 rank=1, A00 rank=2 -> sum=3
    # A00 weight = 0.5 * (2/3) = 1/3, A01 weight = 0.5 * (1/3) = 1/6
    for date in prices.index[2:]:
        assert result.long_holdings.loc[date, "A00"] == pytest.approx(0.5 * (2.0 / 3.0))
        assert result.long_holdings.loc[date, "A01"] == pytest.approx(0.5 * (1.0 / 3.0))


def test_long_short_costs_and_turnover() -> None:
    prices, signals = _make_long_short_panels(n_assets=20)

    result = run_long_short_backtest(
        prices,
        signals,
        rebalance_frequency="D",
        quantiles=10,
        transaction_cost_bps=10.0,
        slippage_bps=5.0,
        gross_leverage=1.0,
    )

    assert result.transaction_costs.sum() > 0.0
    assert result.slippage_costs.sum() > 0.0
    assert result.total_trading_costs.sum() == pytest.approx(
        result.transaction_costs.sum() + result.slippage_costs.sum()
    )

    # Net returns must be strictly less than gross returns on days with turnover
    trade_dates = result.turnover[result.turnover > 0.0].index
    for date in trade_dates:
        assert result.returns.loc[date] < result.gross_returns.loc[date]


def test_long_short_equity_compounding() -> None:
    prices, signals = _make_long_short_panels(n_assets=20)

    result = run_long_short_backtest(
        prices,
        signals,
        initial_capital=10_000.0,
    )

    assert result.equity_curve.iloc[0] == 10_000.0
    for i in range(1, len(result.equity_curve)):
        prev_eq = result.equity_curve.iloc[i - 1]
        ret = result.returns.iloc[i]
        assert result.equity_curve.iloc[i] == pytest.approx(prev_eq * (1.0 + ret))


def test_long_short_decile_returns_and_spread() -> None:
    prices, signals = _make_long_short_panels(n_assets=20)

    result = run_long_short_backtest(
        prices,
        signals,
        rebalance_frequency="D",
        quantiles=10,
    )

    # Check that decile_returns has columns D1..D10
    expected_cols = [f"D{i+1}" for i in range(10)]
    assert list(result.decile_returns.columns) == expected_cols

    # Spread returns should match D10 - D1 on rebalance days
    rebal_dates = result.decile_returns.dropna().index
    for date in rebal_dates:
        d10 = result.decile_returns.loc[date, "D10"]
        d1 = result.decile_returns.loc[date, "D1"]
        assert result.spread_returns.loc[date] == pytest.approx(d10 - d1)


def test_long_short_validation_errors() -> None:
    prices, signals = _make_long_short_panels(n_assets=10)

    # quantiles < 2
    with pytest.raises(ValueError, match="quantiles"):
        run_long_short_backtest(prices, signals, quantiles=1)

    # invalid weighting_scheme
    with pytest.raises(ValueError, match="weighting_scheme"):
        run_long_short_backtest(prices, signals, weighting_scheme="invalid")  # type: ignore[arg-type]

    # negative costs
    with pytest.raises(ValueError, match="transaction_cost_bps"):
        run_long_short_backtest(prices, signals, transaction_cost_bps=-1.0)
