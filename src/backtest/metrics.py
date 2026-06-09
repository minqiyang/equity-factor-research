"""Backtest metric calculations for simulated research output."""

from __future__ import annotations

import math

import pandas as pd


def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    """Calculate maximum drawdown from a portfolio equity curve.

    Args:
        equity_curve: Portfolio value indexed by date.

    Returns:
        Maximum drawdown as a negative decimal value. For example, ``-0.25``
        means a 25% peak-to-trough drawdown.
    """

    if equity_curve.empty:
        return math.nan

    running_peak = equity_curve.cummax()
    drawdowns = equity_curve / running_peak - 1.0
    return float(drawdowns.min())


def calculate_basic_metrics(
    equity_curve: pd.Series,
    returns: pd.Series,
    *,
    turnover: pd.Series | None = None,
    transaction_costs: pd.Series | None = None,
    slippage_costs: pd.Series | None = None,
    benchmark_equity_curve: pd.Series | None = None,
    initial_capital: float = 1.0,
    periods_per_year: int = 252,
) -> dict[str, float]:
    """Calculate a small set of deterministic backtest metrics.

    Metrics are intended for research diagnostics only. They are not evidence
    of live profitability or future performance. ``total_return`` is measured
    against the explicit ``initial_capital`` base, so first-row trading costs
    are included when they exist.
    """

    if equity_curve.empty:
        raise ValueError("equity_curve must not be empty")
    if returns.empty:
        raise ValueError("returns must not be empty")
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")

    total_return = float(equity_curve.iloc[-1] / initial_capital - 1.0)
    realized_periods = max(len(returns) - 1, 1)
    annualized_return = float((1.0 + total_return) ** (periods_per_year / realized_periods) - 1.0)

    annualized_volatility = float(returns.std(ddof=0) * math.sqrt(periods_per_year))
    sharpe_ratio = math.nan
    if annualized_volatility > 0:
        sharpe_ratio = float(returns.mean() / returns.std(ddof=0) * math.sqrt(periods_per_year))

    metrics = {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": calculate_max_drawdown(equity_curve),
    }

    if turnover is not None:
        metrics["average_turnover"] = float(turnover.mean())
        metrics["total_turnover"] = float(turnover.sum())

    if transaction_costs is not None:
        metrics["total_transaction_cost_impact"] = float(transaction_costs.sum())

    if slippage_costs is not None:
        metrics["total_slippage_cost_impact"] = float(slippage_costs.sum())

    if transaction_costs is not None or slippage_costs is not None:
        transaction_total = 0.0 if transaction_costs is None else float(transaction_costs.sum())
        slippage_total = 0.0 if slippage_costs is None else float(slippage_costs.sum())
        metrics["total_trading_cost_impact"] = transaction_total + slippage_total

    if benchmark_equity_curve is not None:
        benchmark_total_return = float(benchmark_equity_curve.iloc[-1] / initial_capital - 1.0)
        metrics["benchmark_total_return"] = benchmark_total_return
        metrics["excess_total_return"] = total_return - benchmark_total_return

    return metrics
