"""Portfolio construction and accounting helpers.

This module contains a minimal long-only, equal-weight cross-sectional
backtester for research use. It does not place trades, connect to a broker, or
fetch data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from backtest.metrics import calculate_basic_metrics


@dataclass(frozen=True)
class BacktestResult:
    """Container for minimal long-only backtest outputs.

    ``holdings`` are target weights at each date after any rebalance on that
    date. Period returns use prior-date holdings, so a target set on date ``t``
    affects returns starting on the next available price row.
    """

    equity_curve: pd.Series
    returns: pd.Series
    gross_returns: pd.Series
    holdings: pd.DataFrame
    turnover: pd.Series
    transaction_costs: pd.Series
    slippage_costs: pd.Series
    total_trading_costs: pd.Series
    metrics: dict[str, float]
    benchmark_equity_curve: pd.Series | None
    assumptions: dict[str, Any]


def run_long_only_backtest(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    *,
    rebalance_frequency: str = "ME",
    top_n: int | None = None,
    top_pct: float | None = None,
    transaction_cost_bps: float = 0.0,
    slippage_bps: float = 0.0,
    benchmark_prices: pd.Series | None = None,
    initial_capital: float = 1.0,
    signal_lag_periods: int = 1,
    missing_price_policy: str = "raise",
    benchmark_missing_policy: str = "raise",
    periods_per_year: int = 252,
) -> BacktestResult:
    """Run a minimal long-only, equal-weight cross-sectional backtest.

    Execution alignment:
    - Signals are treated as values known after the close of their timestamp.
    - By default, ``signal_lag_periods=1`` means a rebalance on date ``t`` uses
      the previous available signal row, not the signal stamped at ``t``.
    - Target holdings set on date ``t`` earn returns starting on the next
      available price row.
    - Signals are aligned to the price index and price columns; the aligned
      non-null signal coverage ratio is reported in ``result.assumptions``.

    Portfolio rules:
    - Long-only only.
    - No leverage; selected assets receive equal weights summing to 1.0.
    - No shorting and no cash interest.
    - Trades occur only on rebalance dates.
    - Transaction costs are a fixed basis-point cost applied to target-weight
      turnover on rebalance dates and deducted from that date's portfolio
      return.
    - Slippage is a separate fixed basis-point impact applied to the same
      target-weight turnover model. This is a deterministic research
      assumption, not an order-fill or market-impact model.
    - Missing held-asset returns raise by default. Passing
      ``missing_price_policy="zero_return"`` is an explicit diagnostic fallback
      that treats missing held returns as 0.0.
    - Missing benchmark prices raise by default. Passing
      ``benchmark_missing_policy="zero_return"`` freezes benchmark returns on
      missing dates and should be documented as a simplifying assumption.

    The turnover model is target-weight turnover, not drift-adjusted turnover:
    ``sum(abs(target_weights - previous_target_weights))``. This is a simple
    first-pass research assumption that should be revisited before using the
    engine for more realistic cost modeling.
    """

    _validate_backtest_inputs(
        prices=prices,
        signals=signals,
        top_n=top_n,
        top_pct=top_pct,
        transaction_cost_bps=transaction_cost_bps,
        slippage_bps=slippage_bps,
        initial_capital=initial_capital,
        signal_lag_periods=signal_lag_periods,
        missing_price_policy=missing_price_policy,
        benchmark_missing_policy=benchmark_missing_policy,
        periods_per_year=periods_per_year,
    )

    price_data = prices.astype(float)
    signal_data = signals.reindex(index=price_data.index, columns=price_data.columns).astype(float)
    rebalance_dates = _get_rebalance_dates(price_data.index, rebalance_frequency)
    lagged_signals = signal_data.shift(signal_lag_periods)

    target_weights = _build_target_weights(
        prices=price_data,
        lagged_signals=lagged_signals,
        rebalance_dates=rebalance_dates,
        top_n=top_n,
        top_pct=top_pct,
    )

    holdings = target_weights.ffill().fillna(0.0)
    previous_holdings = holdings.shift(1).fillna(0.0)

    asset_returns = price_data.pct_change(fill_method=None)
    asset_returns = asset_returns.replace([np.inf, -np.inf], np.nan)
    asset_returns = _handle_missing_held_returns(
        asset_returns=asset_returns,
        previous_holdings=previous_holdings,
        missing_price_policy=missing_price_policy,
    )

    gross_returns = (previous_holdings * asset_returns).sum(axis=1)
    turnover_weights = holdings.diff().abs()
    turnover_weights.iloc[0] = holdings.iloc[0].abs()
    turnover = turnover_weights.sum(axis=1)
    transaction_costs = turnover * (transaction_cost_bps / 10_000.0)
    slippage_costs = turnover * (slippage_bps / 10_000.0)
    total_trading_costs = transaction_costs + slippage_costs
    net_returns = gross_returns - total_trading_costs
    equity_curve = initial_capital * (1.0 + net_returns).cumprod()

    benchmark_equity_curve = _calculate_benchmark_equity_curve(
        benchmark_prices=benchmark_prices,
        price_index=price_data.index,
        initial_capital=initial_capital,
        benchmark_missing_policy=benchmark_missing_policy,
    )

    metrics = calculate_basic_metrics(
        equity_curve,
        net_returns,
        turnover=turnover,
        transaction_costs=transaction_costs,
        slippage_costs=slippage_costs,
        benchmark_equity_curve=benchmark_equity_curve,
        initial_capital=initial_capital,
        periods_per_year=periods_per_year,
    )

    return BacktestResult(
        equity_curve=equity_curve.rename("equity"),
        returns=net_returns.rename("return"),
        gross_returns=gross_returns.rename("gross_return"),
        holdings=holdings,
        turnover=turnover.rename("turnover"),
        transaction_costs=transaction_costs.rename("transaction_cost_impact"),
        slippage_costs=slippage_costs.rename("slippage_impact"),
        total_trading_costs=total_trading_costs.rename("total_trading_cost_impact"),
        metrics=metrics,
        benchmark_equity_curve=benchmark_equity_curve,
        assumptions={
            "rebalance_frequency": rebalance_frequency,
            "top_n": top_n,
            "top_pct": top_pct,
            "transaction_cost_bps": transaction_cost_bps,
            "slippage_bps": slippage_bps,
            "signal_lag_periods": signal_lag_periods,
            "missing_price_policy": missing_price_policy,
            "benchmark_missing_policy": benchmark_missing_policy,
            "aligned_signal_coverage": _calculate_signal_coverage(signal_data),
            "execution_timing": "signals known after close; trades on rebalance dates using lagged signals; holdings affect next price row",
            "turnover_model": "target_weight_turnover",
            "cost_model": "fixed_bps_on_target_weight_turnover",
            "slippage_model": "fixed_bps_on_target_weight_turnover",
            "zero_cost_or_slippage_is_diagnostic": transaction_cost_bps == 0.0 or slippage_bps == 0.0,
            "long_only": True,
            "leverage": "none",
        },
    )


def _build_target_weights(
    *,
    prices: pd.DataFrame,
    lagged_signals: pd.DataFrame,
    rebalance_dates: pd.DatetimeIndex,
    top_n: int | None,
    top_pct: float | None,
) -> pd.DataFrame:
    target_weights = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    rebalance_date_set = set(rebalance_dates)

    for date in prices.index:
        if date not in rebalance_date_set:
            target_weights.loc[date] = np.nan
            continue

        scores = lagged_signals.loc[date]
        tradable = prices.loc[date].notna() & prices.loc[date].gt(0.0)
        valid_scores = scores[tradable & scores.notna()]

        selected_assets = _select_top_assets(valid_scores, top_n=top_n, top_pct=top_pct)
        if not selected_assets:
            continue

        equal_weight = 1.0 / len(selected_assets)
        target_weights.loc[date, selected_assets] = equal_weight

    return target_weights


def _select_top_assets(scores: pd.Series, *, top_n: int | None, top_pct: float | None) -> list[str]:
    if scores.empty:
        return []

    sorted_scores = scores.sort_values(ascending=False, kind="mergesort")
    if top_n is not None:
        selection_count = min(top_n, len(sorted_scores))
    else:
        selection_count = max(1, int(np.ceil(len(sorted_scores) * top_pct)))

    return list(sorted_scores.iloc[:selection_count].index)


def _get_rebalance_dates(index: pd.DatetimeIndex, rebalance_frequency: str) -> pd.DatetimeIndex:
    if rebalance_frequency.strip().lower() in {"d", "daily"}:
        return index

    date_series = pd.Series(index=index, data=index)
    return pd.DatetimeIndex(date_series.resample(rebalance_frequency).last().dropna().to_list())


def _handle_missing_held_returns(
    *,
    asset_returns: pd.DataFrame,
    previous_holdings: pd.DataFrame,
    missing_price_policy: str,
) -> pd.DataFrame:
    held_missing_returns = previous_holdings.gt(0.0) & asset_returns.isna()

    if held_missing_returns.to_numpy().any() and missing_price_policy == "raise":
        missing_by_date = held_missing_returns.stack()
        first_date, first_asset = missing_by_date[missing_by_date].index[0]
        raise ValueError(
            "Missing return for held asset "
            f"{first_asset} on {first_date.date()}; set missing_price_policy='zero_return' "
            "only for an explicit diagnostic fallback."
        )

    return asset_returns.fillna(0.0)


def _calculate_benchmark_equity_curve(
    *,
    benchmark_prices: pd.Series | None,
    price_index: pd.DatetimeIndex,
    initial_capital: float,
    benchmark_missing_policy: str,
) -> pd.Series | None:
    if benchmark_prices is None:
        return None

    if not isinstance(benchmark_prices, pd.Series):
        raise TypeError("benchmark_prices must be a pandas Series")
    if not isinstance(benchmark_prices.index, pd.DatetimeIndex):
        raise TypeError("benchmark_prices must be indexed by a pandas DatetimeIndex")

    if benchmark_prices.index.has_duplicates:
        raise ValueError("benchmark_prices index must not contain duplicate dates")
    if not benchmark_prices.index.is_monotonic_increasing:
        raise ValueError("benchmark_prices index must be sorted in increasing date order")

    aligned_prices = benchmark_prices.reindex(price_index).astype(float)
    if aligned_prices.isna().any() and benchmark_missing_policy == "raise":
        first_missing_date = aligned_prices[aligned_prices.isna()].index[0]
        raise ValueError(
            "benchmark_prices are missing on strategy date "
            f"{first_missing_date.date()}; set benchmark_missing_policy='zero_return' "
            "only for an explicit diagnostic fallback."
        )

    benchmark_returns = aligned_prices.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return (initial_capital * (1.0 + benchmark_returns).cumprod()).rename("benchmark_equity")


def _calculate_signal_coverage(signal_data: pd.DataFrame) -> float:
    if signal_data.empty or signal_data.size == 0:
        return float("nan")

    return float(signal_data.notna().sum().sum() / signal_data.size)


def _validate_backtest_inputs(
    *,
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    top_n: int | None,
    top_pct: float | None,
    transaction_cost_bps: float,
    slippage_bps: float,
    initial_capital: float,
    signal_lag_periods: int,
    missing_price_policy: str,
    benchmark_missing_policy: str,
    periods_per_year: int,
) -> None:
    if not isinstance(prices, pd.DataFrame):
        raise TypeError("prices must be a pandas DataFrame")
    if not isinstance(signals, pd.DataFrame):
        raise TypeError("signals must be a pandas DataFrame")
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise TypeError("prices must be indexed by a pandas DatetimeIndex")
    if not isinstance(signals.index, pd.DatetimeIndex):
        raise TypeError("signals must be indexed by a pandas DatetimeIndex")
    if prices.empty:
        raise ValueError("prices must not be empty")
    if prices.index.has_duplicates or signals.index.has_duplicates:
        raise ValueError("prices and signals must not contain duplicate dates")
    if not prices.index.is_monotonic_increasing:
        raise ValueError("prices index must be sorted in increasing date order")
    if not signals.index.is_monotonic_increasing:
        raise ValueError("signals index must be sorted in increasing date order")
    if top_n is None and top_pct is None:
        raise ValueError("either top_n or top_pct must be provided")
    if top_n is not None and top_pct is not None:
        raise ValueError("provide only one of top_n or top_pct")
    if top_n is not None and top_n <= 0:
        raise ValueError("top_n must be positive")
    if top_pct is not None and not 0.0 < top_pct <= 1.0:
        raise ValueError("top_pct must be greater than 0 and no more than 1")
    if transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps must be non-negative")
    if slippage_bps < 0:
        raise ValueError("slippage_bps must be non-negative")
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")
    if signal_lag_periods < 0:
        raise ValueError("signal_lag_periods must be non-negative")
    if missing_price_policy not in {"raise", "zero_return"}:
        raise ValueError("missing_price_policy must be 'raise' or 'zero_return'")
    if benchmark_missing_policy not in {"raise", "zero_return"}:
        raise ValueError("benchmark_missing_policy must be 'raise' or 'zero_return'")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
