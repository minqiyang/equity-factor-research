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

from backtest.risk_attribution import (
    CrossSectionalRiskModel, PortfolioRiskAttribution, attribute_backtest,
)
from backtest.market_impact import (
    SquareRootImpactModel, execute_impact_step,
    resolve_impact_liquidity, impact_assumptions, impact_result_fields,
)
from backtest.portfolio import (
    BacktestValidationError,
    _get_rebalance_dates,
    _read_positive_price,
    _calculate_held_asset_returns,
    _validate_execution_price_legs,
    _validate_pretrade_gross,
    _validate_postcost_net_equity,
    _validate_bounded_signal_values,
    _read_exact_integral_scalar,
    _read_finite_real_scalar,
    _prepare_terminal_events,
    _resolve_pit_universe,
    _terminal_settlement,
    _validate_terminal_target,
)
from data.constituent_table import ValidatedConstituentIntervals


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
    cash_balance: pd.Series
    terminal_cashflows: pd.DataFrame
    terminal_event_log: tuple[dict[str, Any], ...]
    slippage_cost_series: pd.Series
    realized_slippage_bps: pd.Series
    trade_participation_rates: pd.DataFrame
    executed_trade_values: pd.DataFrame
    pending_trade_shares: pd.DataFrame
    cancelled_trade_shares: pd.DataFrame
    risk_attribution: PortfolioRiskAttribution | None = None


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
    constituent_intervals: ValidatedConstituentIntervals | pd.DataFrame | None = None,
    terminal_events: pd.DataFrame | None = None,
    transaction_cost_bps: float = 0.0,
    slippage_bps: float = 0.0,
    risk_model: CrossSectionalRiskModel | None = None,
    impact_model: SquareRootImpactModel | None = None,
    impact_volumes: pd.DataFrame | None = None,
    impact_price_basis: str | None = None,
    impact_volume_basis: str | None = None,
    initial_capital: float = 1.0,
    signal_lag_periods: int = 1,
    gross_leverage: float = 1.0,
    max_position_weight: float | None = None,
    periods_per_year: int = 252,
) -> LongShortBacktestResult:
    """Run a dollar-neutral long-short quantile spread backtest.

    Constructs long positions in top quantile (highest factor scores) and short
    positions in bottom quantile (lowest factor scores). Frozen targets have
    zero net exposure and gross exposure equal to gross_leverage (default 1.0).
    Impact-model fills preserve cash-funded positions; partial fills and drift
    can produce different realized exposures.

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

    if max_position_weight is not None:
        cap = _read_finite_real_scalar(max_position_weight)
        if cap is None or cap <= 0.0 or cap > 1.0:
            raise ValueError("max_position_weight must be in (0, 1]")

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
    sub_signals = _validate_bounded_signal_values(signals.loc[accounting_dates])
    prepared_events = _prepare_terminal_events(terminal_events, prices.index, prices.columns)
    universe_mask = _resolve_pit_universe(
        constituent_intervals=constituent_intervals, universe_mask=universe_mask,
        dates=accounting_dates, assets=prices.columns, signal_lag_periods=signal_lag_periods,
        terminal_events=prepared_events,
    )
    impact_liquidity = resolve_impact_liquidity(
        prices, model=impact_model, volumes=impact_volumes,
        price_basis=impact_price_basis, volume_basis=impact_volume_basis,
        evaluation_end=eval_end, signal_lag_periods=signal_lag_periods,
        slippage_bps=slippage_bps,
    )
    lagged_signals = sub_signals.shift(signal_lag_periods)
    rebalance_dates = _get_rebalance_dates(accounting_dates, rebalance_frequency)

    n_dates = len(accounting_dates)
    columns = sub_prices.columns

    # Allocate output containers
    long_values = np.zeros((n_dates, len(columns)), dtype=float)
    short_values = np.zeros((n_dates, len(columns)), dtype=float)
    net_values = np.zeros((n_dates, len(columns)), dtype=float)

    q_labels = [f"D{i+1}" for i in range(quantiles)]
    decile_returns = pd.DataFrame(np.nan, index=accounting_dates, columns=q_labels)
    spread_returns = pd.Series(0.0, index=accounting_dates, name="spread_return")
    gross_returns = np.full(n_dates, 0.0, dtype=float)
    net_returns = np.full(n_dates, 0.0, dtype=float)
    turnover = np.full(n_dates, 0.0, dtype=float)
    tx_costs = np.full(n_dates, 0.0, dtype=float)
    slip_costs = np.full(n_dates, 0.0, dtype=float)
    total_costs = np.full(n_dates, 0.0, dtype=float)
    equity = np.full(n_dates, np.nan, dtype=float)
    equity[0] = float(initial_capital)

    executed_values = np.zeros(sub_prices.shape)
    participation = np.zeros(sub_prices.shape)
    pending_values = np.zeros(sub_prices.shape)
    cancelled_values = np.zeros(sub_prices.shape)
    cash_values = np.full(n_dates, float(initial_capital))
    impact_dollars = np.zeros(len(accounting_dates))
    pending = pd.Series(0.0, index=columns)
    half_leverage = 0.5 * float(gross_leverage)

    lagged_volatility: pd.DataFrame | None = None
    if weighting_scheme == "inverse_volatility":
        rolling_vol = (
            sub_prices.pct_change(fill_method=None)
            .rolling(volatility_window, min_periods=min_volatility_periods)
            .std()
        )
        lagged_volatility = rolling_vol.shift(signal_lag_periods)

    previous_target = pd.Series(0.0, index=columns)
    current_net = pd.Series(0.0, index=columns)
    terminal_cashflows = np.zeros(sub_prices.shape, dtype=float)
    terminal_event_log: list[dict[str, Any]] = []
    anchor_events = prepared_events.get(accounting_dates[0], ())
    if anchor_events:
        _, anchor_log = _terminal_settlement(
            records=anchor_events, previous_holdings=current_net,
            previous_equity=float(initial_capital),
        )
        terminal_event_log.extend(anchor_log)
    settled = {record["permanent_id"] for event_date, records in prepared_events.items()
               if event_date <= accounting_dates[0] for record in records}

    for i in range(1, n_dates):
        date = accounting_dates[i]
        prev_date = accounting_dates[i - 1]

        previous_prices = sub_prices.iloc[i - 1]
        current_prices = sub_prices.iloc[i]
        events_today = prepared_events.get(date, ())
        terminal_returns = {record["permanent_id"]: record["terminal_return"] for record in events_today}

        # Validate held endpoints before valuation, drift, or any liquidation.
        held_returns = _calculate_held_asset_returns(
            previous_prices=previous_prices,
            current_prices=current_prices,
            previous_holdings=current_net,
            previous_date=prev_date,
            current_date=date,
            missing_price_policy="raise",
            terminal_returns=terminal_returns or None,
        )
        with np.errstate(over="ignore", invalid="ignore"):
            weighted = (current_net * held_returns).to_numpy(dtype=float)
            period_gross = float(np.sum(weighted))
            gross_multiplier = 1.0 + period_gross
        _validate_pretrade_gross(
            gross_return=period_gross, gross_multiplier=gross_multiplier, date=date
        )
        gross_returns[i] = period_gross
        pretrade_net = current_net * (1.0 + held_returns) / gross_multiplier
        if events_today:
            flows, event_log = _terminal_settlement(
                records=events_today, previous_holdings=current_net,
                previous_equity=float(equity[i - 1]),
            )
            terminal_cashflows[i] = flows.to_numpy(dtype=float)
            terminal_event_log.extend(event_log)
            pretrade_net.loc[list(terminal_returns)] = 0.0
            settled.update(terminal_returns)
        actual_target = None
        # Calculate decile returns for diagnostic tracking
        if date in rebalance_dates:
            # These quantile returns describe the incoming interval diagnostically.
            # Executable P&L above uses exclusively previously held positions.
            diagnostic_previous = pd.Series(
                [_read_positive_price(value) for value in previous_prices], index=columns, dtype=float
            )
            diagnostic_current = pd.Series(
                [_read_positive_price(value) for value in current_prices], index=columns, dtype=float
            )
            asset_returns = diagnostic_current / diagnostic_previous - 1.0
            for asset, value in terminal_returns.items():
                if _read_positive_price(previous_prices.loc[asset]) is not None:
                    asset_returns.loc[asset] = value

            scores = lagged_signals.loc[date]
            valid_scores = scores[scores.notna()]
            if universe_mask is not None:
                if date in universe_mask.index:
                    mask_row = universe_mask.loc[date]
                    valid_scores = valid_scores[valid_scores.index.isin(mask_row[mask_row.eq(True)].index)]
                else:
                    valid_scores = valid_scores.iloc[0:0]

            if len(valid_scores) >= quantiles:
                ranks = valid_scores.rank(ascending=True, method="first")
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

                fresh_target = target_long - target_short
                target_net = fresh_target.copy()
                if turnover_penalty_lambda > 0.0 and previous_target.ne(0.0).any():
                    target_net = (
                        (1.0 - turnover_penalty_lambda) * fresh_target
                        + turnover_penalty_lambda * previous_target
                    )
                target_net.loc[~target_net.index.isin(valid_scores.index)] = 0.0
                # Net opposing positions first, then normalize the disjoint legs.
                # A degenerate blend uses the feasible fresh decision-time target.
                positive = target_net.clip(lower=0.0)
                negative = -target_net.clip(upper=0.0)
                if positive.sum() <= 1e-12 or negative.sum() <= 1e-12:
                    target_net = fresh_target
                    positive = target_net.clip(lower=0.0)
                    negative = -target_net.clip(upper=0.0)
                target_net = (
                    half_leverage * positive / positive.sum()
                    - half_leverage * negative / negative.sum()
                )
                if (
                    not np.isfinite(target_net).all()
                    or abs(float(target_net.sum())) > 1e-5
                    or abs(float(target_net.abs().sum()) - gross_leverage) > 1e-5
                ):
                    raise BacktestValidationError(
                        "target_exposure_invalid", "invested target must be net zero with configured gross", date=date
                    )
                if max_position_weight is not None and (target_net.abs() > max_position_weight + 1e-12).any():
                    raise BacktestValidationError(
                        "position_cap_infeasible", "final signed target exceeds max_position_weight", date=date
                    )
            else:
                target_net = pd.Series(0.0, index=columns)

            # The frozen target reference stays independent of execution prices.
            previous_target = target_net.copy()
            _validate_terminal_target(target_net, settled, date=date)
            actual_target = target_net
        current_net = pretrade_net
        row_turnover = row_tx_cost = row_slip_cost = row_total_cost = 0.0
        if impact_model is not None:
            previous_equity = float(equity[i - 1])
            equity_before = previous_equity * gross_multiplier
            step = execute_impact_step(
                model=impact_model, liquidity=impact_liquidity, date=date,
                execution_prices=current_prices,
                position_values=pretrade_net * equity_before,
                cash=cash_values[i - 1] + float(terminal_cashflows[i].sum()),
                equity_before=equity_before, target_weights=actual_target,
                pending_shares=pending,
                eligible=universe_mask.reindex(index=[date], columns=columns).iloc[0] if universe_mask is not None else None,
                settled=settled, transaction_cost_bps=transaction_cost_bps,
            )
            pending = step.pending_trade_shares
            executed_values[i] = step.executed_trade_values.to_numpy()
            participation[i] = step.participation_rates.to_numpy()
            pending_values[i] = pending.to_numpy()
            cancelled_values[i] = step.cancelled_trade_shares.to_numpy()
            cash_values[i] = step.cash
            impact_dollars[i] = step.slippage_cost
            row_turnover = float(step.executed_trade_values.abs().sum()) / equity_before
            row_tx_cost = step.commission / previous_equity
            row_slip_cost = step.slippage_cost / previous_equity
            row_total_cost = row_tx_cost + row_slip_cost
            impact_equity = equity_before - step.commission - step.slippage_cost
            current_net = step.position_values / impact_equity
        elif actual_target is not None:
            signed_trades = target_net - pretrade_net
            _validate_execution_price_legs(
                execution_prices=current_prices,
                signed_trade_weights=signed_trades,
                date=date,
            )
            row_turnover = float(signed_trades.abs().sum())
            row_tx_cost = row_turnover * (float(transaction_cost_bps) / 10_000.0) * gross_multiplier
            row_slip_cost = row_turnover * (float(slippage_bps) / 10_000.0) * gross_multiplier
            row_total_cost = row_tx_cost + row_slip_cost
            current_net = target_net
            executed_values[i] = signed_trades.to_numpy() * equity[i - 1] * gross_multiplier
            participation[i, executed_values[i] != 0] = np.nan

        period_net = period_gross - row_total_cost
        if impact_model is not None:
            period_net = impact_equity / equity[i - 1] - 1.0
        net_returns[i] = period_net
        turnover[i] = row_turnover
        tx_costs[i] = row_tx_cost
        slip_costs[i] = row_slip_cost
        total_costs[i] = row_total_cost

        equity_candidate = float(equity[i - 1]) * (1.0 + period_net)
        if impact_model is not None:
            equity_candidate = impact_equity
        _validate_postcost_net_equity(
            net_return=period_net, net_multiplier=1.0 + period_net,
            equity_candidate=equity_candidate, date=date,
        )
        equity[i] = equity_candidate
        net_values[i] = current_net.to_numpy(dtype=float)
        long_values[i] = np.where(net_values[i] < 0.0, 0.0, net_values[i])
        short_values[i] = -np.where(net_values[i] > 0.0, 0.0, net_values[i])

    long_holdings = pd.DataFrame(long_values, index=accounting_dates, columns=columns)
    short_holdings = pd.DataFrame(short_values, index=accounting_dates, columns=columns)
    net_holdings = pd.DataFrame(net_values, index=accounting_dates, columns=columns)
    gross_returns = pd.Series(gross_returns, index=accounting_dates, name="gross_return")
    net_returns = pd.Series(net_returns, index=accounting_dates, name="return")
    turnover = pd.Series(turnover, index=accounting_dates, name="turnover")
    tx_costs = pd.Series(tx_costs, index=accounting_dates, name="transaction_cost_impact")
    slip_costs = pd.Series(slip_costs, index=accounting_dates, name="slippage_impact")
    total_costs = pd.Series(total_costs, index=accounting_dates, name="total_trading_cost_impact")
    equity = pd.Series(equity, index=accounting_dates, name="equity")

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
        "max_position_weight": max_position_weight,
        "smoothing_reference": "previous_frozen_target",
        "degenerate_blend_policy": "fresh_target",
        "missing_universe_row_policy": "empty",
        "cost_basis": "turnover_on_post_return_value_scaled_to_beginning_period",
        "decile_return_scope": "incoming_interval_diagnostic_only",
        "periods_per_year": periods_per_year,
        "dollar_neutral": True,
        **({
            "membership_contract": "known_schedule_at_lagged_source_close_v1",
            "formal_universe_evidence_eligible": False,
        } if constituent_intervals is not None else {}),
        **({
            "terminal_settlement_contract": "prior_observed_close_to_cash_v1",
            "formal_terminal_evidence_eligible": False,
            "terminal_settlement_fee": 0.0,
            "terminal_redemption_turnover": "excluded_from_ordinary_market_turnover",
            "cash_model": "residual_of_postcost_target_weight_accounting",
            "terminal_exposure_policy": "surviving_positions_drift_until_next_scheduled_reset",
        } if terminal_events is not None else {}),
        "timing_contract": "after_close_signal_next_observed_close_v1",
        **impact_assumptions(impact_model, price_basis=impact_price_basis,
                             volume_basis=impact_volume_basis),
        **({"dollar_neutral": False, "target_dollar_neutral": True}
           if impact_model is not None else {}),
    }

    return LongShortBacktestResult(
        risk_attribution=attribute_backtest(
            risk_model, prices=sub_prices, holdings=net_holdings,
            gross_returns=gross_returns, net_returns=net_returns,
            trading_costs=total_costs, periods_per_year=periods_per_year,
            terminal_events=terminal_events, missing_price_policy="raise",
        ),
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
        cash_balance=(pd.Series(cash_values, index=accounting_dates) if impact_model is not None else equity * (1.0 - net_holdings.sum(axis=1))).rename("cash_balance"),
        **impact_result_fields(index=accounting_dates, columns=columns, equity=equity.to_numpy(),
                               slippage_returns=slip_costs, executed=executed_values,
                               participation=participation, pending=pending_values,
                               cancelled=cancelled_values,
                               slippage_dollars=impact_dollars if impact_model is not None else None),
        terminal_cashflows=pd.DataFrame(terminal_cashflows, index=accounting_dates, columns=columns),
        terminal_event_log=tuple(terminal_event_log),
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

    if prices.index.has_duplicates or prices.columns.has_duplicates or not prices.index.is_monotonic_increasing:
        raise BacktestValidationError("source_axes_invalid", "source axes must be unique and dates increasing")

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
        _read_finite_real_scalar(turnover_penalty_lambda) is None
        or turnover_penalty_lambda < 0.0
        or turnover_penalty_lambda >= 1.0
    ):
        raise ValueError("turnover_penalty_lambda must be in [0.0, 1.0)")

    if universe_mask is not None:
        if not isinstance(universe_mask, pd.DataFrame):
            raise TypeError("universe_mask must be a DataFrame")
        if not isinstance(universe_mask.index, pd.DatetimeIndex):
            raise TypeError("universe_mask must use a DatetimeIndex")
        if universe_mask.index.has_duplicates or universe_mask.columns.has_duplicates or not universe_mask.index.is_monotonic_increasing:
            raise ValueError("universe_mask axes must be unique and dates increasing")

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
