"""Long-short decile spread and quantile portfolio backtesting.

This module provides decile and quantile spread portfolio backtesting for
cross-sectional research factor panels. It constructs dollar-neutral (or
configurable gross leverage) long-short portfolios, evaluates per-decile
returns (D1..D10), computes long-minus-short spreads, tracks turnover, and
applies explicit frictional costs (transaction costs and slippage).

It does not place trades, connect to a broker, or fetch remote data. All
calculations are strictly simulated, reproducible, and explainable.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Literal

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from backtest.portfolio import (
    BacktestValidationError,
    _get_rebalance_dates,
    _read_exact_integral_scalar,
    _read_finite_real_scalar,
)


@dataclass(frozen=True)
class LongShortBacktestResult:
    """Container for long-short decile spread backtest outputs.

    equity_curve: Cumulative portfolio equity series (starts at initial_capital).
    returns: Net portfolio returns after transaction costs and slippage.
    gross_returns: Gross portfolio returns before costs.
    decile_returns: DataFrame with columns D1..D{quantiles} containing period returns for each decile.
    spread_returns: Top-minus-bottom quantile return spread series (D{quantiles} - D1).
    long_holdings: Post-rebalance target holdings DataFrame for the long leg.
    short_holdings: Post-rebalance target holdings DataFrame for the short leg (absolute positive weights).
    net_holdings: Net target holdings DataFrame (long_holdings - short_holdings).
    turnover: Period turnover series (sum of absolute trade weight changes).
    transaction_costs: Transaction cost impact series.
    slippage_costs: Slippage impact series.
    total_trading_costs: Combined transaction cost and slippage series.
    metrics: Summary dictionary with Sharpe, annualized return/volatility, drawdown, win rate, and decile monotonicity.
    assumptions: Dictionary of configuration parameters and model assumptions.
    """

    equity_curve: pd.Series
    returns: pd.Series
    gross_returns: pd.Series
    decile_returns: pd.DataFrame
    spread_returns: pd.Series
    long_holdings: pd.DataFrame
    short_holdings: pd.DataFrame
    net_holdings: pd.DataFrame
    turnover: pd.Series
    transaction_costs: pd.Series
    slippage_costs: pd.Series
    total_trading_costs: pd.Series
    metrics: dict[str, float]
    assumptions: dict[str, Any]


def run_long_short_backtest(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    *,
    evaluation_start: pd.Timestamp | None = None,
    evaluation_end: pd.Timestamp | None = None,
    rebalance_frequency: str = "ME",
    quantiles: int = 10,
    weighting_scheme: Literal["equal", "rank", "inverse_volatility"] = "equal",
    volatility_window: int = 20,
    min_volatility_periods: int = 5,
    turnover_penalty_lambda: float = 0.0,
    universe_mask: pd.DataFrame | None = None,
    transaction_cost_bps: float = 0.0,
    slippage_bps: float = 0.0,
    initial_capital: float = 1.0,
    signal_lag_periods: int = 1,
    gross_leverage: float = 1.0,
    periods_per_year: int = 252,
) -> LongShortBacktestResult:
    """Run a dollar-neutral long-short quantile spread backtest.

    Constructs long positions in top quantile (highest factor scores) and short
    positions in bottom quantile (lowest factor scores). Net exposure is zero
    (dollar neutral) and gross exposure sums to gross_leverage (default 1.0).

    Signals are lagged by signal_lag_periods (default 1), enforcing the
    after-close/next-observed-close lookahead-free research contract.
    """

    _validate_long_short_inputs(
        prices=prices,
        signals=signals,
        quantiles=quantiles,
        weighting_scheme=weighting_scheme,
        volatility_window=volatility_window,
        min_volatility_periods=min_volatility_periods,
        turnover_penalty_lambda=turnover_penalty_lambda,
        universe_mask=universe_mask,
        transaction_cost_bps=transaction_cost_bps,
        slippage_bps=slippage_bps,
        initial_capital=initial_capital,
        signal_lag_periods=signal_lag_periods,
        gross_leverage=gross_leverage,
        periods_per_year=periods_per_year,
    )

    eval_start = prices.index[0] if evaluation_start is None else pd.Timestamp(evaluation_start)
    eval_end = prices.index[-1] if evaluation_end is None else pd.Timestamp(evaluation_end)

    if eval_start not in prices.index or eval_end not in prices.index:
        raise BacktestValidationError(
            "evaluation_dates_invalid",
            "evaluation_start and evaluation_end must be exact source-row labels",
        )
    if eval_start >= eval_end:
        raise BacktestValidationError(
            "evaluation_window_invalid",
            "evaluation_start must precede evaluation_end",
        )

    start_pos = prices.index.get_loc(eval_start)
    end_pos = prices.index.get_loc(eval_end)
    accounting_dates = prices.index[start_pos : end_pos + 1]

    sub_prices = prices.loc[accounting_dates]
    sub_signals = signals.loc[accounting_dates]
    lagged_signals = sub_signals.shift(signal_lag_periods)
    rebalance_dates = _get_rebalance_dates(accounting_dates, rebalance_frequency)

    n_dates = len(accounting_dates)
    columns = sub_prices.columns

    # Allocate output containers
    long_holdings = pd.DataFrame(0.0, index=accounting_dates, columns=columns)
    short_holdings = pd.DataFrame(0.0, index=accounting_dates, columns=columns)
    net_holdings = pd.DataFrame(0.0, index=accounting_dates, columns=columns)

    q_labels = [f"D{i+1}" for i in range(quantiles)]
    decile_returns = pd.DataFrame(np.nan, index=accounting_dates, columns=q_labels)
    spread_returns = pd.Series(0.0, index=accounting_dates, name="spread_return")
    gross_returns = pd.Series(0.0, index=accounting_dates, name="gross_return")
    net_returns = pd.Series(0.0, index=accounting_dates, name="return")
    turnover = pd.Series(0.0, index=accounting_dates, name="turnover")
    tx_costs = pd.Series(0.0, index=accounting_dates, name="transaction_cost_impact")
    slip_costs = pd.Series(0.0, index=accounting_dates, name="slippage_impact")
    total_costs = pd.Series(0.0, index=accounting_dates, name="total_trading_cost_impact")
    equity = pd.Series(np.nan, index=accounting_dates, name="equity")
    equity.iloc[0] = float(initial_capital)

    half_leverage = 0.5 * float(gross_leverage)

    lagged_volatility: pd.DataFrame | None = None
    if weighting_scheme == "inverse_volatility":
        rolling_vol = (
            sub_prices.pct_change()
            .rolling(volatility_window, min_periods=min_volatility_periods)
            .std()
        )
        lagged_volatility = rolling_vol.shift(signal_lag_periods)

    current_long = pd.Series(0.0, index=columns)
    current_short = pd.Series(0.0, index=columns)
    current_net = pd.Series(0.0, index=columns)

    for i in range(1, n_dates):
        date = accounting_dates[i]
        prev_date = accounting_dates[i - 1]

        # Asset returns from prev_date to date
        p_prev = sub_prices.loc[prev_date].to_numpy(dtype=float)
        p_curr = sub_prices.loc[date].to_numpy(dtype=float)
        asset_returns = pd.Series(p_curr / p_prev - 1.0, index=columns)

        # Portfolio return earned on held positions
        period_gross = float((current_net * asset_returns).sum())
        gross_returns.loc[date] = period_gross

        # Calculate decile returns for diagnostic tracking
        if date in rebalance_dates:
            scores = lagged_signals.loc[date]
            valid_scores = scores[scores.notna()]
            if universe_mask is not None and date in universe_mask.index:
                mask_row = universe_mask.loc[date]
                valid_scores = valid_scores[valid_scores.index.isin(mask_row[mask_row.eq(True)].index)]

            if len(valid_scores) >= quantiles:
                ranks = valid_scores.rank(ascending=True, method="first")
                try:
                    quantile_bins = pd.qcut(ranks, q=quantiles, labels=q_labels)
                    for q_lbl in q_labels:
                        q_assets = valid_scores.index[quantile_bins == q_lbl]
                        if len(q_assets) > 0:
                            decile_returns.loc[date, q_lbl] = float(asset_returns[q_assets].mean())

                    d_top = q_labels[-1]
                    d_bottom = q_labels[0]
                    if pd.notna(decile_returns.loc[date, d_top]) and pd.notna(decile_returns.loc[date, d_bottom]):
                        spread_returns.loc[date] = (
                            decile_returns.loc[date, d_top] - decile_returns.loc[date, d_bottom]
                        )
                except ValueError:
                    pass

                # Build target long and short weights
                top_assets = valid_scores.index[quantile_bins == q_labels[-1]]
                bottom_assets = valid_scores.index[quantile_bins == q_labels[0]]

                target_long = pd.Series(0.0, index=columns)
                target_short = pd.Series(0.0, index=columns)

                if weighting_scheme == "equal":
                    target_long[top_assets] = half_leverage / len(top_assets)
                    target_short[bottom_assets] = half_leverage / len(bottom_assets)
                elif weighting_scheme == "rank":
                    # Top decile: higher score -> higher weight
                    top_ranks = valid_scores[top_assets].rank(ascending=True, method="average")
                    target_long[top_assets] = half_leverage * (top_ranks / top_ranks.sum())
                    # Bottom decile: lower score -> higher short weight (rank descending)
                    bottom_ranks = valid_scores[bottom_assets].rank(ascending=False, method="average")
                    target_short[bottom_assets] = half_leverage * (bottom_ranks / bottom_ranks.sum())
                elif weighting_scheme == "inverse_volatility":
                    assert lagged_volatility is not None
                    top_vols = lagged_volatility.loc[date, top_assets]
                    valid_top_mask = (top_vols > 0.0) & np.isfinite(top_vols)
                    valid_top_vols = top_vols[valid_top_mask]
                    if len(valid_top_vols) == 0:
                        target_long[top_assets] = half_leverage / len(top_assets)
                    else:
                        fallback_top = float(valid_top_vols.median())
                        filled_top = top_vols.where(valid_top_mask, fallback_top)
                        inv_top = 1.0 / filled_top
                        inv_top_sum = float(inv_top.sum())
                        if inv_top_sum > 0.0:
                            target_long[top_assets] = half_leverage * (inv_top / inv_top_sum)
                        else:
                            target_long[top_assets] = half_leverage / len(top_assets)

                    bot_vols = lagged_volatility.loc[date, bottom_assets]
                    valid_bot_mask = (bot_vols > 0.0) & np.isfinite(bot_vols)
                    valid_bot_vols = bot_vols[valid_bot_mask]
                    if len(valid_bot_vols) == 0:
                        target_short[bottom_assets] = half_leverage / len(bottom_assets)
                    else:
                        fallback_bot = float(valid_bot_vols.median())
                        filled_bot = bot_vols.where(valid_bot_mask, fallback_bot)
                        inv_bot = 1.0 / filled_bot
                        inv_bot_sum = float(inv_bot.sum())
                        if inv_bot_sum > 0.0:
                            target_short[bottom_assets] = half_leverage * (inv_bot / inv_bot_sum)
                        else:
                            target_short[bottom_assets] = half_leverage / len(bottom_assets)

                if turnover_penalty_lambda > 0.0 and (current_long.ne(0.0).any() or current_short.ne(0.0).any()):
                    drifted_long = current_long * (1.0 + asset_returns)
                    drifted_short = current_short * (1.0 + asset_returns)
                    sum_long = float(drifted_long.sum())
                    sum_short = float(drifted_short.sum())
                    drifted_long_norm = (
                        half_leverage * (drifted_long / sum_long)
                        if sum_long > 1e-8
                        else drifted_long
                    )
                    drifted_short_norm = (
                        half_leverage * (drifted_short / sum_short)
                        if sum_short > 1e-8
                        else drifted_short
                    )
                    target_long = (
                        (1.0 - turnover_penalty_lambda) * target_long
                        + turnover_penalty_lambda * drifted_long_norm
                    )
                    target_short = (
                        (1.0 - turnover_penalty_lambda) * target_short
                        + turnover_penalty_lambda * drifted_short_norm
                    )

                target_net = target_long - target_short

                # Turnover: absolute changes from drifted pretrade net weights
                drifted_net = current_net * (1.0 + asset_returns)
                net_mult = 1.0 + period_gross
                if abs(net_mult) > 1e-8:
                    drifted_net /= net_mult

                trades = (target_net - drifted_net).abs()
                row_turnover = float(trades.sum())

                row_tx_cost = row_turnover * (float(transaction_cost_bps) / 10_000.0)
                row_slip_cost = row_turnover * (float(slippage_bps) / 10_000.0)
                row_total_cost = row_tx_cost + row_slip_cost

                current_long = target_long
                current_short = target_short
                current_net = target_net
            else:
                # Ineligible: liquidate to cash
                row_turnover = float(current_net.abs().sum())
                row_tx_cost = row_turnover * (float(transaction_cost_bps) / 10_000.0)
                row_slip_cost = row_turnover * (float(slippage_bps) / 10_000.0)
                row_total_cost = row_tx_cost + row_slip_cost

                current_long = pd.Series(0.0, index=columns)
                current_short = pd.Series(0.0, index=columns)
                current_net = pd.Series(0.0, index=columns)
        else:
            # Non-rebalance date: drift weights
            drifted_net = current_net * (1.0 + asset_returns)
            net_mult = 1.0 + period_gross
            if abs(net_mult) > 1e-8:
                drifted_net /= net_mult
            current_net = drifted_net
            if turnover_penalty_lambda > 0.0:
                drifted_long = current_long * (1.0 + asset_returns)
                drifted_short = current_short * (1.0 + asset_returns)
                if abs(net_mult) > 1e-8:
                    drifted_long /= net_mult
                    drifted_short /= net_mult
                current_long = drifted_long
                current_short = drifted_short
            row_turnover = 0.0
            row_tx_cost = 0.0
            row_slip_cost = 0.0
            row_total_cost = 0.0

        period_net = period_gross - row_total_cost
        net_returns.loc[date] = period_net
        turnover.loc[date] = row_turnover
        tx_costs.loc[date] = row_tx_cost
        slip_costs.loc[date] = row_slip_cost
        total_costs.loc[date] = row_total_cost

        equity.loc[date] = float(equity.iloc[i - 1]) * (1.0 + period_net)
        long_holdings.loc[date] = current_long
        short_holdings.loc[date] = current_short
        net_holdings.loc[date] = current_net

    # Summary metrics
    metrics = _calculate_long_short_metrics(
        equity=equity,
        returns=net_returns.iloc[1:],
        decile_returns=decile_returns.dropna(how="all"),
        spread_returns=spread_returns[spread_returns.ne(0.0)],
        turnover=turnover,
        periods_per_year=periods_per_year,
    )

    assumptions = {
        "rebalance_frequency": rebalance_frequency,
        "quantiles": quantiles,
        "weighting_scheme": weighting_scheme,
        "volatility_window": volatility_window,
        "min_volatility_periods": min_volatility_periods,
        "turnover_penalty_lambda": turnover_penalty_lambda,
        "universe_mask_applied": universe_mask is not None,
        "transaction_cost_bps": transaction_cost_bps,
        "slippage_bps": slippage_bps,
        "signal_lag_periods": signal_lag_periods,
        "gross_leverage": gross_leverage,
        "periods_per_year": periods_per_year,
        "dollar_neutral": True,
        "timing_contract": "after_close_signal_next_observed_close_v1",
    }

    return LongShortBacktestResult(
        equity_curve=equity,
        returns=net_returns,
        gross_returns=gross_returns,
        decile_returns=decile_returns,
        spread_returns=spread_returns,
        long_holdings=long_holdings,
        short_holdings=short_holdings,
        net_holdings=net_holdings,
        turnover=turnover,
        transaction_costs=tx_costs,
        slippage_costs=slip_costs,
        total_trading_costs=total_costs,
        metrics=metrics,
        assumptions=assumptions,
    )


def _validate_long_short_inputs(
    *,
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    quantiles: int,
    weighting_scheme: str,
    volatility_window: int = 20,
    min_volatility_periods: int = 5,
    turnover_penalty_lambda: float = 0.0,
    universe_mask: pd.DataFrame | None,
    transaction_cost_bps: float,
    slippage_bps: float,
    initial_capital: float,
    signal_lag_periods: int,
    gross_leverage: float,
    periods_per_year: int,
) -> None:
    if not isinstance(prices, pd.DataFrame) or not isinstance(signals, pd.DataFrame):
        raise BacktestValidationError("source_axes_invalid", "prices and signals must be DataFrames")
    if not isinstance(prices.index, pd.DatetimeIndex) or not isinstance(signals.index, pd.DatetimeIndex):
        raise BacktestValidationError("source_axes_invalid", "prices and signals must use DatetimeIndex")
    if prices.empty or signals.empty:
        raise BacktestValidationError("source_axes_invalid", "prices and signals must not be empty")
    if not prices.index.equals(signals.index) or not prices.columns.equals(signals.columns):
        raise BacktestValidationError("source_axes_invalid", "price and signal axes must match exactly")

    if isinstance(quantiles, bool) or not isinstance(quantiles, int) or quantiles < 2:
        raise ValueError("quantiles must be an integer of at least 2")
    if weighting_scheme not in {"equal", "rank", "inverse_volatility"}:
        raise ValueError("weighting_scheme must be 'equal', 'rank', or 'inverse_volatility'")
    if not isinstance(volatility_window, int) or volatility_window <= 0:
        raise ValueError("volatility_window must be a positive integer")
    if (
        not isinstance(min_volatility_periods, int)
        or min_volatility_periods <= 0
        or min_volatility_periods > volatility_window
    ):
        raise ValueError("min_volatility_periods must be positive and <= volatility_window")
    if (
        not isinstance(turnover_penalty_lambda, (int, float))
        or turnover_penalty_lambda < 0.0
        or turnover_penalty_lambda >= 1.0
    ):
        raise ValueError("turnover_penalty_lambda must be in [0.0, 1.0)")

    if universe_mask is not None:
        if not isinstance(universe_mask, pd.DataFrame):
            raise TypeError("universe_mask must be a DataFrame")
        if not isinstance(universe_mask.index, pd.DatetimeIndex):
            raise TypeError("universe_mask must use a DatetimeIndex")

    tc = _read_finite_real_scalar(transaction_cost_bps)
    if tc is None or tc < 0.0:
        raise ValueError("transaction_cost_bps must be non-negative")
    slip = _read_finite_real_scalar(slippage_bps)
    if slip is None or slip < 0.0:
        raise ValueError("slippage_bps must be non-negative")
    init_cap = _read_finite_real_scalar(initial_capital)
    if init_cap is None or init_cap <= 0.0:
        raise ValueError("initial_capital must be positive")
    lag = _read_exact_integral_scalar(signal_lag_periods)
    if lag is None or lag < 1:
        raise ValueError("signal_lag_periods must be at least 1")
    lev = _read_finite_real_scalar(gross_leverage)
    if lev is None or lev <= 0.0:
        raise ValueError("gross_leverage must be positive")
    ppy = _read_exact_integral_scalar(periods_per_year)
    if ppy is None or ppy <= 0:
        raise ValueError("periods_per_year must be positive")


def _calculate_long_short_metrics(
    *,
    equity: pd.Series,
    returns: pd.Series,
    decile_returns: pd.DataFrame,
    spread_returns: pd.Series,
    turnover: pd.Series,
    periods_per_year: int,
) -> dict[str, float]:
    clean_returns = returns.dropna()
    n_periods = len(clean_returns)
    if n_periods == 0:
        return {
            "sharpe": 0.0,
            "annualized_return": 0.0,
            "annualized_volatility": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "total_turnover": 0.0,
            "decile_spread_mean": 0.0,
            "monotonicity_spearman": 0.0,
        }

    mean_ret = float(clean_returns.mean())
    std_ret = float(clean_returns.std(ddof=1)) if n_periods >= 2 else 0.0
    sharpe = float(mean_ret / std_ret * math.sqrt(periods_per_year)) if std_ret > 0.0 else 0.0
    ann_ret = float(mean_ret * periods_per_year)
    ann_vol = float(std_ret * math.sqrt(periods_per_year))

    peak = equity.cummax()
    drawdown = (peak - equity) / peak
    max_dd = float(drawdown.max())

    non_zero = clean_returns[clean_returns.ne(0.0)]
    win_rate = float((non_zero > 0.0).mean()) if len(non_zero) > 0 else 0.0
    tot_turnover = float(turnover.sum())

    spread_mean = float(spread_returns.mean()) if len(spread_returns) > 0 else 0.0

    # Decile monotonicity: correlation between decile index (1..Q) and mean return
    decile_means = decile_returns.mean(axis=0)
    if len(decile_means.dropna()) >= 2:
        indices = np.arange(1, len(decile_means) + 1)
        sr, _ = spearmanr(indices, decile_means.to_numpy(dtype=float))
        monotonicity = float(sr) if math.isfinite(sr) else 0.0
    else:
        monotonicity = 0.0

    return {
        "sharpe": sharpe,
        "annualized_return": ann_ret,
        "annualized_volatility": ann_vol,
        "max_drawdown": max_dd,
        "win_rate": win_rate,
        "total_turnover": tot_turnover,
        "decile_spread_mean": spread_mean,
        "monotonicity_spearman": monotonicity,
    }


__all__ = [
    "LongShortBacktestResult",
    "run_long_short_backtest",
]
