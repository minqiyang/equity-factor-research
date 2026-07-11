"""Portfolio construction and accounting helpers.

This module contains a minimal long-only, equal-weight cross-sectional
backtester for research use. It does not place trades, connect to a broker, or
fetch data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_complex_dtype, is_numeric_dtype

from backtest.metrics import calculate_basic_metrics, calculate_holding_episode_metrics
from risk.constraints import apply_long_only_position_cap


_VOLUME_AWARE_SLIPPAGE_MODES = {"diagnostic_only", "apply_precomputed_impact"}
_PORTFOLIO_GROWTH_STABILITY_THRESHOLD = 1e-8
_TRACKING_ERROR_ASSUMPTIONS = {
    "tracking_error_contract": "daily_close_to_close_v1",
    "tracking_error_return_basis": "strategy_net_after_applied_costs_vs_cost_free_benchmark",
    "tracking_error_frequency": "daily_close_to_close",
    "tracking_error_periods_per_year": 252,
    "tracking_error_ddof": 0,
    "tracking_error_first_row_policy": "exclude_synthetic_anchor",
    "tracking_error_missing_policy": "raise",
    "tracking_error_terminal_row_policy": "include_terminal_close_to_close_window",
    "benchmark_cost_basis": "cost_free_price_return",
}
_POSITION_CAP_ASSUMPTIONS = {
    "position_constraint_contract": "long_only_position_cap_v1",
    "position_constraint_order": "after_selection_before_trade_calculation",
    "position_constraint_breach_policy": "clip",
    "position_constraint_renormalization": "none",
    "position_constraint_residual_weight": "non_interest_bearing_cash",
    "position_constraint_infeasible_target_policy": "clip_and_hold_cash",
}
_HOLDING_EPISODE_ASSUMPTIONS = {
    "holding_episode_contract": "continuous_positive_weight_v1",
    "holding_episode_return_basis": "net_contribution_over_cumulative_deployed_weight",
    "holding_episode_cost_allocation": "pro_rata_absolute_signed_trade_weight",
    "holding_episode_resize_policy": "continue_episode",
    "holding_episode_reentry_policy": "new_after_zero_close",
    "holding_episode_terminal_policy": "exclude_open",
    "holding_episode_zero_return_hit_policy": "not_a_hit",
    "holding_episode_aggregation": "equal_weight_completed_episodes",
}
_REQUIRED_VOLUME_AWARE_METADATA_KEYS = {
    "base_slippage_bps",
    "max_participation",
    "missing_or_zero_liquidity_policy",
    "participation_above_cap_policy",
    "participation_slope_bps",
    "portfolio_notional",
    "price_field",
    "return_impact_basis",
    "slippage_model",
    "stale_volume_policy",
    "trade_weight_source",
    "volume_lag",
    "volume_policy",
    "window",
}


@dataclass(frozen=True)
class BacktestResult:
    """Container for minimal long-only backtest outputs.

    ``holdings`` are post-trade weights on rebalance dates and drifted closing
    weights on other dates. Period returns use prior-date holdings, so a target
    set on date ``t`` affects returns starting on the next available price row.
    ``trade_weights`` are absolute per-asset changes from drifted pre-trade
    weights to targets on rebalance dates and zero on other dates; their row sum
    equals ``turnover`` under the undivided convention.
    ``signed_trade_weights`` preserve the corresponding buy-positive,
    sell-negative direction for episode attribution.
    """

    equity_curve: pd.Series
    returns: pd.Series
    gross_returns: pd.Series
    holdings: pd.DataFrame
    signed_trade_weights: pd.DataFrame
    trade_weights: pd.DataFrame
    turnover: pd.Series
    transaction_costs: pd.Series
    slippage_costs: pd.Series
    volume_aware_slippage_costs: pd.Series
    total_trading_costs: pd.Series
    metrics: dict[str, float]
    benchmark_equity_curve: pd.Series | None
    benchmark_returns: pd.Series | None
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
    volume_aware_slippage_mode: str = "diagnostic_only",
    volume_aware_slippage_impact: pd.Series | None = None,
    volume_aware_slippage_metadata: Mapping[str, Any] | None = None,
    benchmark_prices: pd.Series | None = None,
    initial_capital: float = 1.0,
    signal_lag_periods: int = 1,
    missing_price_policy: str = "raise",
    benchmark_missing_policy: str = "raise",
    periods_per_year: int = 252,
    max_position_weight: float | None = None,
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
    - Trades occur only on rebalance dates. Between rebalances, weights drift
      with asset returns; the engine does not silently rebalance them each day.
    - Transaction costs are a fixed basis-point cost applied to target-weight
      turnover on rebalance dates. Because trades occur after that date's asset
      returns, the cost is charged against post-return portfolio value and then
      expressed as an impact on beginning-period return.
    - Slippage is a separate fixed basis-point impact applied to the same
      target-weight turnover model. This is a deterministic research
      assumption, not an order-fill or market-impact model.
    - Volume-aware slippage remains diagnostic-only by default. The first
      supported integration path accepts an explicit precomputed impact series
      and metadata; the backtester does not calculate rolling dollar volume.
    - Missing held-asset returns raise by default. Passing
      ``missing_price_policy="zero_return"`` is an explicit diagnostic fallback
      that treats missing held returns as 0.0.
    - Missing benchmark prices raise by default. Passing
      ``benchmark_missing_policy="zero_return"`` freezes benchmark returns on
      missing dates and should be documented as a simplifying assumption.

    Turnover is the sum of absolute changes from drifted pre-trade weights to
    target weights on each rebalance date:
    ``sum(abs(target_weights - drifted_pretrade_weights))``. The convention is
    not divided by two, so a full switch between two assets has turnover 2.0.
    """

    _validate_backtest_inputs(
        prices=prices,
        signals=signals,
        top_n=top_n,
        top_pct=top_pct,
        transaction_cost_bps=transaction_cost_bps,
        slippage_bps=slippage_bps,
        volume_aware_slippage_mode=volume_aware_slippage_mode,
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
    if max_position_weight is not None:
        target_weights = apply_long_only_position_cap(
            target_weights.fillna(0.0),
            max_position_weight=max_position_weight,
        ).where(target_weights.notna())

    asset_returns = price_data.pct_change(fill_method=None)
    asset_returns = asset_returns.replace([np.inf, -np.inf], np.nan)
    (
        holdings,
        gross_returns,
        signed_trade_weights,
        trade_weights,
        resolved_asset_returns,
    ) = _calculate_drift_aware_portfolio_path(
        asset_returns=asset_returns,
        target_weights=target_weights,
        missing_price_policy=missing_price_policy,
    )
    turnover = trade_weights.sum(axis=1).rename("turnover")
    post_return_growth = 1.0 + gross_returns
    transaction_costs = (
        turnover * (transaction_cost_bps / 10_000.0) * post_return_growth
    )
    slippage_costs = turnover * (slippage_bps / 10_000.0) * post_return_growth
    volume_aware_slippage_costs = _prepare_volume_aware_slippage_costs(
        price_index=price_data.index,
        mode=volume_aware_slippage_mode,
        impact=volume_aware_slippage_impact,
        metadata=volume_aware_slippage_metadata,
        fixed_slippage_bps=slippage_bps,
        post_return_growth=post_return_growth,
    )
    total_trading_costs = (
        transaction_costs + slippage_costs + volume_aware_slippage_costs
    )
    net_returns = gross_returns - total_trading_costs
    net_growth = 1.0 + net_returns
    exhausted = net_growth.le(0.0)
    if exhausted.any():
        first_exhausted_date = exhausted[exhausted].index[0]
        raise ValueError(
            "Asset returns and trading costs exhausted the portfolio on "
            f"{first_exhausted_date.date()}"
        )
    equity_curve = initial_capital * (1.0 + net_returns).cumprod()

    benchmark_equity_curve, benchmark_returns = _calculate_benchmark_path(
        benchmark_prices=benchmark_prices,
        price_index=price_data.index,
        initial_capital=initial_capital,
        benchmark_missing_policy=benchmark_missing_policy,
    )
    benchmark_returns_for_tracking_error = None
    if benchmark_returns is not None and benchmark_missing_policy == "raise":
        if periods_per_year != 252:
            raise ValueError("tracking error supports daily_close_to_close only")
        benchmark_returns_for_tracking_error = benchmark_returns

    metrics = calculate_basic_metrics(
        equity_curve,
        net_returns,
        holdings=holdings,
        turnover=turnover,
        transaction_costs=transaction_costs,
        slippage_costs=slippage_costs,
        volume_aware_slippage_costs=volume_aware_slippage_costs,
        benchmark_equity_curve=benchmark_equity_curve,
        benchmark_returns=benchmark_returns_for_tracking_error,
        initial_capital=initial_capital,
        periods_per_year=periods_per_year,
    )
    episode_metrics, closed_episode_count, open_episode_count = (
        calculate_holding_episode_metrics(
            holdings,
            resolved_asset_returns,
            signed_trade_weights,
            trade_weights,
            turnover,
            total_trading_costs,
        )
    )
    metrics.update(episode_metrics)

    volume_aware_assumptions = _build_volume_aware_slippage_assumptions(
        mode=volume_aware_slippage_mode,
        metadata=volume_aware_slippage_metadata,
    )
    volume_aware_slippage_applied = (
        volume_aware_slippage_mode == "apply_precomputed_impact"
        and volume_aware_slippage_costs.gt(0.0).any()
    )
    zero_cost_or_slippage_is_diagnostic = transaction_cost_bps == 0.0 or (
        slippage_bps == 0.0 and not volume_aware_slippage_applied
    )

    return BacktestResult(
        equity_curve=equity_curve.rename("equity"),
        returns=net_returns.rename("return"),
        gross_returns=gross_returns.rename("gross_return"),
        holdings=holdings,
        signed_trade_weights=signed_trade_weights,
        trade_weights=trade_weights,
        turnover=turnover.rename("turnover"),
        transaction_costs=transaction_costs.rename("transaction_cost_impact"),
        slippage_costs=slippage_costs.rename("slippage_impact"),
        volume_aware_slippage_costs=volume_aware_slippage_costs.rename(
            "volume_aware_slippage_impact",
        ),
        total_trading_costs=total_trading_costs.rename("total_trading_cost_impact"),
        metrics=metrics,
        benchmark_equity_curve=benchmark_equity_curve,
        benchmark_returns=benchmark_returns,
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
            "turnover_reference": "drifted_pretrade_weights",
            "trade_weight_model": "absolute_target_minus_drifted_pretrade_by_asset",
            "signed_trade_weight_model": "target_minus_drifted_pretrade_by_asset",
            "holdings_model": "drifted_between_rebalances",
            "cost_model": "fixed_bps_on_target_weight_turnover",
            "slippage_model": "fixed_bps_on_target_weight_turnover",
            "fixed_cost_application_timing": "close_after_asset_returns",
            "fixed_cost_return_impact_basis": "beginning_period_portfolio_value",
            "zero_cost_or_slippage_is_diagnostic": zero_cost_or_slippage_is_diagnostic,
            "long_only": True,
            "leverage": "none",
            **_HOLDING_EPISODE_ASSUMPTIONS,
            "holding_episode_closed_count": closed_episode_count,
            "holding_episode_terminal_open_count": open_episode_count,
            **(
                {**_POSITION_CAP_ASSUMPTIONS, "max_position_weight": max_position_weight}
                if max_position_weight is not None
                else {}
            ),
            **(
                _TRACKING_ERROR_ASSUMPTIONS
                if benchmark_returns_for_tracking_error is not None
                else {}
            ),
            **volume_aware_assumptions,
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
    target_weights = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)

    for date in rebalance_dates:
        target_weights.loc[date] = 0.0

        scores = lagged_signals.loc[date]
        tradable = prices.loc[date].notna() & prices.loc[date].gt(0.0)
        valid_scores = scores[tradable & scores.notna()]

        selected_assets = _select_top_assets(valid_scores, top_n=top_n, top_pct=top_pct)
        if not selected_assets:
            continue

        equal_weight = 1.0 / len(selected_assets)
        target_weights.loc[date, selected_assets] = equal_weight

    return target_weights


def _calculate_drift_aware_portfolio_path(
    *,
    asset_returns: pd.DataFrame,
    target_weights: pd.DataFrame,
    missing_price_policy: str,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Propagate holdings and record per-asset trades only on target rows."""

    holdings = pd.DataFrame(0.0, index=asset_returns.index, columns=asset_returns.columns)
    gross_returns = pd.Series(0.0, index=asset_returns.index, name="gross_return")
    trade_weights = pd.DataFrame(
        0.0,
        index=asset_returns.index,
        columns=asset_returns.columns,
    )
    signed_trade_weights = trade_weights.copy()
    resolved_asset_returns = trade_weights.copy()
    post_trade_weights = pd.Series(0.0, index=asset_returns.columns, dtype=float)

    for date in asset_returns.index:
        period_returns = _resolve_period_asset_returns(
            asset_returns=asset_returns.loc[date],
            previous_holdings=post_trade_weights,
            date=date,
            missing_price_policy=missing_price_policy,
        )
        resolved_asset_returns.loc[date] = period_returns
        grown_weights = post_trade_weights * (1.0 + period_returns)
        gross_return = float((post_trade_weights * period_returns).sum())
        portfolio_growth = 1.0 + gross_return
        if (
            post_trade_weights.gt(0.0).any()
            and portfolio_growth <= _PORTFOLIO_GROWTH_STABILITY_THRESHOLD
        ):
            portfolio_growth = float(grown_weights.sum())
            gross_return = portfolio_growth - 1.0
        gross_returns.loc[date] = gross_return

        if portfolio_growth <= 0.0 and post_trade_weights.gt(0.0).any():
            raise ValueError(
                "Portfolio value was exhausted before weights could be propagated "
                f"on {date.date()}"
            )
        if post_trade_weights.gt(0.0).any():
            pretrade_weights = grown_weights / portfolio_growth
        else:
            pretrade_weights = post_trade_weights.copy()

        target = target_weights.loc[date]
        if target.notna().any():
            target = target.fillna(0.0)
            signed_trade_weights.loc[date] = target - pretrade_weights
            trade_weights.loc[date] = signed_trade_weights.loc[date].abs()
            post_trade_weights = target
        else:
            post_trade_weights = pretrade_weights

        holdings.loc[date] = post_trade_weights

    return (
        holdings,
        gross_returns,
        signed_trade_weights,
        trade_weights,
        resolved_asset_returns,
    )


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


def _resolve_period_asset_returns(
    *,
    asset_returns: pd.Series,
    previous_holdings: pd.Series,
    date: pd.Timestamp,
    missing_price_policy: str,
) -> pd.Series:
    held_missing_returns = previous_holdings.gt(0.0) & asset_returns.isna()

    if held_missing_returns.any() and missing_price_policy == "raise":
        first_asset = held_missing_returns[held_missing_returns].index[0]
        raise ValueError(
            "Missing return for held asset "
            f"{first_asset} on {date.date()}; set missing_price_policy='zero_return' "
            "only for an explicit diagnostic fallback."
        )

    return asset_returns.fillna(0.0)


def _calculate_benchmark_path(
    *,
    benchmark_prices: pd.Series | None,
    price_index: pd.DatetimeIndex,
    initial_capital: float,
    benchmark_missing_policy: str,
) -> tuple[pd.Series | None, pd.Series | None]:
    if benchmark_prices is None:
        return None, None

    if not isinstance(benchmark_prices, pd.Series):
        raise TypeError("benchmark_prices must be a pandas Series")
    if not isinstance(benchmark_prices.index, pd.DatetimeIndex):
        raise TypeError("benchmark_prices must be indexed by a pandas DatetimeIndex")
    if benchmark_prices.index.tz != price_index.tz:
        raise ValueError("benchmark_prices and strategy prices must have matching timezones")

    if benchmark_prices.index.has_duplicates:
        raise ValueError("benchmark_prices index must not contain duplicate dates")
    if not benchmark_prices.index.is_monotonic_increasing:
        raise ValueError("benchmark_prices index must be sorted in increasing date order")
    if (
        is_bool_dtype(benchmark_prices.dtype)
        or is_complex_dtype(benchmark_prices.dtype)
        or not is_numeric_dtype(benchmark_prices.dtype)
    ):
        raise TypeError(
            "benchmark_prices must contain real numeric, non-boolean values"
        )

    observed_prices = benchmark_prices.dropna().astype(float)
    if (
        not np.isfinite(observed_prices.to_numpy()).all()
        or observed_prices.le(0.0).any()
    ):
        raise ValueError("benchmark_prices must contain finite positive values")

    aligned_prices = benchmark_prices.reindex(price_index).astype(float)
    if aligned_prices.isna().any() and benchmark_missing_policy == "raise":
        first_missing_date = aligned_prices[aligned_prices.isna()].index[0]
        raise ValueError(
            "benchmark_prices are missing on strategy date "
            f"{first_missing_date.date()}; set benchmark_missing_policy='zero_return' "
            "only for an explicit diagnostic fallback."
        )
    if benchmark_missing_policy == "zero_return":
        combined_index = benchmark_prices.index.union(price_index).sort_values()
        aligned_prices = (
            benchmark_prices.astype(float)
            .reindex(combined_index)
            .ffill()
            .reindex(price_index)
        )

    benchmark_returns = aligned_prices.pct_change(fill_method=None)
    if benchmark_missing_policy == "raise":
        benchmark_returns.iloc[0] = 0.0
        invalid_returns = benchmark_returns.isna() | ~np.isfinite(benchmark_returns)
        if invalid_returns.any():
            first_invalid_date = invalid_returns[invalid_returns].index[0]
            raise ValueError(
                "benchmark_prices produce missing or non-finite returns on "
                f"{first_invalid_date.date()}"
            )
    else:
        benchmark_returns = benchmark_returns.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    benchmark_returns = benchmark_returns.rename("benchmark_return")
    benchmark_equity_curve = (
        initial_capital * (1.0 + benchmark_returns).cumprod()
    ).rename("benchmark_equity")
    return benchmark_equity_curve, benchmark_returns


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
    volume_aware_slippage_mode: str,
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
    if volume_aware_slippage_mode not in _VOLUME_AWARE_SLIPPAGE_MODES:
        raise ValueError(
            "volume_aware_slippage_mode must be 'diagnostic_only' or "
            "'apply_precomputed_impact'"
        )
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


def _prepare_volume_aware_slippage_costs(
    *,
    price_index: pd.DatetimeIndex,
    mode: str,
    impact: pd.Series | None,
    metadata: Mapping[str, Any] | None,
    fixed_slippage_bps: float,
    post_return_growth: pd.Series,
) -> pd.Series:
    zero_costs = pd.Series(0.0, index=price_index, name="volume_aware_slippage_impact")

    if mode == "diagnostic_only":
        if impact is not None:
            _validate_precomputed_volume_aware_slippage_impact(
                impact=impact,
                price_index=price_index,
            )
        return zero_costs

    if impact is None:
        raise ValueError(
            "volume_aware_slippage_impact is required when "
            "volume_aware_slippage_mode='apply_precomputed_impact'"
        )

    _validate_volume_aware_slippage_metadata(metadata)
    costs = _validate_precomputed_volume_aware_slippage_impact(
        impact=impact,
        price_index=price_index,
    )

    return_impact_basis = metadata["return_impact_basis"]
    if return_impact_basis == "post_return_portfolio_value":
        costs = costs * post_return_growth

    if fixed_slippage_bps > 0.0 and costs.gt(0.0).any():
        raise ValueError(
            "positive slippage_bps cannot be combined with positive "
            "volume_aware_slippage_impact without a reviewed combined-model policy"
        )

    return costs


def _validate_precomputed_volume_aware_slippage_impact(
    *,
    impact: pd.Series,
    price_index: pd.DatetimeIndex,
) -> pd.Series:
    if not isinstance(impact, pd.Series):
        raise TypeError("volume_aware_slippage_impact must be a pandas Series")
    if not isinstance(impact.index, pd.DatetimeIndex):
        raise TypeError(
            "volume_aware_slippage_impact must be indexed by a pandas DatetimeIndex"
        )
    if impact.index.has_duplicates:
        raise ValueError("volume_aware_slippage_impact index must not contain duplicate dates")
    if not impact.index.is_monotonic_increasing:
        raise ValueError(
            "volume_aware_slippage_impact index must be sorted in increasing date order"
        )
    if not impact.index.equals(price_index):
        raise ValueError(
            "volume_aware_slippage_impact index must exactly match backtest dates"
        )

    try:
        costs = impact.astype(float)
    except (TypeError, ValueError) as exc:
        raise TypeError("volume_aware_slippage_impact must contain numeric values") from exc

    if costs.isna().any():
        first_missing_date = costs[costs.isna()].index[0]
        raise ValueError(
            "volume_aware_slippage_impact must not contain missing values; "
            f"first missing date is {first_missing_date.date()}"
        )
    if not np.isfinite(costs.to_numpy()).all():
        raise ValueError("volume_aware_slippage_impact must contain finite values")
    if costs.lt(0.0).any():
        first_negative_date = costs[costs.lt(0.0)].index[0]
        raise ValueError(
            "volume_aware_slippage_impact must be non-negative; "
            f"first negative date is {first_negative_date.date()}"
        )

    return costs.rename("volume_aware_slippage_impact")


def _validate_volume_aware_slippage_metadata(
    metadata: Mapping[str, Any] | None,
) -> None:
    if metadata is None:
        raise ValueError(
            "volume_aware_slippage_metadata is required when applying "
            "precomputed volume-aware slippage impact"
        )
    if not isinstance(metadata, Mapping):
        raise TypeError("volume_aware_slippage_metadata must be a mapping")

    missing_keys = sorted(_REQUIRED_VOLUME_AWARE_METADATA_KEYS.difference(metadata))
    if missing_keys:
        raise ValueError(
            "volume_aware_slippage_metadata missing required keys: "
            + ", ".join(missing_keys)
        )

    trade_weight_source = metadata["trade_weight_source"]
    if not isinstance(trade_weight_source, str) or not trade_weight_source.strip():
        raise ValueError(
            "volume_aware_slippage_metadata trade_weight_source must be a "
            "non-empty string"
        )

    return_impact_basis = metadata["return_impact_basis"]
    allowed_return_impact_bases = {
        "beginning_period_portfolio_value",
        "post_return_portfolio_value",
    }
    if (
        not isinstance(return_impact_basis, str)
        or return_impact_basis not in allowed_return_impact_bases
    ):
        raise ValueError(
            "volume_aware_slippage_metadata return_impact_basis must be "
            "'beginning_period_portfolio_value' or "
            "'post_return_portfolio_value'"
        )


def _build_volume_aware_slippage_assumptions(
    *,
    mode: str,
    metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    metadata_values: Mapping[str, Any] = {} if metadata is None else metadata

    return {
        "volume_aware_slippage_mode": mode,
        "volume_aware_slippage_applied_to_returns": mode == "apply_precomputed_impact",
        "volume_aware_slippage_model": metadata_values.get("slippage_model"),
        "volume_aware_slippage_source": metadata_values.get("name"),
        "volume_aware_trade_weight_source": metadata_values.get(
            "trade_weight_source"
        ),
        "volume_aware_input_return_impact_basis": metadata_values.get(
            "return_impact_basis"
        ),
        "volume_aware_applied_return_impact_basis": (
            "beginning_period_portfolio_value"
            if mode == "apply_precomputed_impact"
            else None
        ),
        "portfolio_notional": metadata_values.get("portfolio_notional"),
        "volume_aware_price_field": metadata_values.get("price_field"),
        "volume_policy": metadata_values.get("volume_policy"),
        "volume_lag": metadata_values.get("volume_lag"),
        "rolling_dollar_volume_window": metadata_values.get("window"),
        "stale_volume_policy": metadata_values.get("stale_volume_policy"),
        "max_volume_age": metadata_values.get("max_volume_age"),
        "max_participation": metadata_values.get("max_participation"),
        "participation_above_cap_policy": metadata_values.get(
            "participation_above_cap_policy",
        ),
        "missing_or_zero_liquidity_policy": metadata_values.get(
            "missing_or_zero_liquidity_policy",
        ),
    }
