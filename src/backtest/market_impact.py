"""Causal daily liquidity, symmetric impact costs, and simulated cash-funded trades."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from numbers import Integral, Real
from typing import Literal
import math

import numpy as np
import pandas as pd


class MarketImpactValidationError(ValueError):
    """A typed refusal at the optional market-impact boundary."""

    def __init__(self, reason: str, message: str):
        self.reason = reason
        super().__init__(f"{reason}: {message}")


def _finite_real(value: object) -> bool:
    if not isinstance(value, Real) or isinstance(value, (bool, np.bool_)):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def _post_trade_reconciles(balance: float, equity: float) -> bool:
    """Closing cash plus signed positions must equal post-cost equity.

    The relative bound scales with notional like the pre-trade check, so
    floating-point rounding on large books reconciles; the absolute floor keeps
    books below $1M at the $0.000001 limit.
    """
    return math.isfinite(balance) and math.isclose(
        balance, equity, rel_tol=1e-12, abs_tol=1e-6
    )


@dataclass(frozen=True)
class SquareRootImpactModel:
    eta: float = 0.25
    max_participation_rate: float = 0.10
    fixed_bps: float = 0.0
    min_adv: float = 1e5
    mode: Literal["throttle", "penalize", "raise"] = "raise"
    lookback: int = 20
    penalty_bps: float = 10.0

    def __post_init__(self) -> None:
        for name in (
            "eta",
            "fixed_bps",
            "penalty_bps",
            "min_adv",
            "max_participation_rate",
        ):
            value = getattr(self, name)
            if not _finite_real(value) or value < 0:
                raise MarketImpactValidationError(
                    "impact_model_invalid",
                    f"{name} requires a finite nonnegative real value",
                )
        if self.min_adv <= 0 or not 0 < self.max_participation_rate <= 1:
            raise MarketImpactValidationError(
                "impact_model_invalid",
                "ADV minimum must be positive and participation cap must lie in (0, 1]",
            )
        if (
            isinstance(self.lookback, (bool, np.bool_))
            or not isinstance(self.lookback, Integral)
            or self.lookback < 2
        ):
            raise MarketImpactValidationError(
                "impact_model_invalid", "lookback requires an integer >= 2"
            )
        if self.mode not in ("throttle", "penalize", "raise"):
            raise MarketImpactValidationError(
                "impact_model_invalid", "unknown participation mode"
            )


@dataclass(frozen=True)
class MarketLiquidity:
    adv: pd.DataFrame
    daily_volatility: pd.DataFrame
    observed_volume: pd.DataFrame


@dataclass(frozen=True)
class MarketImpactExecution:
    position_values: pd.Series
    cash: float
    commission: float
    slippage_cost: float
    executed_trade_values: pd.Series
    participation_rates: pd.Series
    pending_trade_shares: pd.Series
    cancelled_trade_shares: pd.Series


def _panel_axes(prices: pd.DataFrame, volumes: pd.DataFrame) -> None:
    if not isinstance(prices, pd.DataFrame) or not isinstance(volumes, pd.DataFrame):
        raise MarketImpactValidationError(
            "impact_axes_invalid", "prices and volumes require DataFrames"
        )
    if (
        not isinstance(prices.index, pd.DatetimeIndex)
        or prices.empty
        or prices.index.hasnans
        or not prices.index.is_unique
        or not prices.index.is_monotonic_increasing
        or not prices.columns.is_unique
        or not prices.index.equals(volumes.index)
        or not prices.columns.equals(volumes.columns)
    ):
        raise MarketImpactValidationError(
            "impact_axes_invalid",
            "price/volume axes require exact unique ordered source rows and columns",
        )


def prepare_market_liquidity(
    prices: pd.DataFrame,
    volumes: pd.DataFrame,
    *,
    price_basis: str,
    volume_basis: str,
    model: SquareRootImpactModel,
    signal_lag_periods: int,
) -> MarketLiquidity:
    """Estimate daily dollar ADV and volatility using only lagged complete windows."""
    _panel_axes(prices, volumes)
    if not isinstance(model, SquareRootImpactModel):
        raise MarketImpactValidationError(
            "impact_model_invalid", "a SquareRootImpactModel is required"
        )
    if price_basis not in ("raw", "split_adjusted") or price_basis != volume_basis:
        raise MarketImpactValidationError(
            "impact_basis_invalid",
            "price and volume require matching raw or split_adjusted bases",
        )
    if (
        isinstance(signal_lag_periods, (bool, np.bool_))
        or not isinstance(signal_lag_periods, Integral)
        or signal_lag_periods < 1
    ):
        raise MarketImpactValidationError(
            "impact_lag_invalid", "lag requires a positive integer"
        )
    clean_prices = prices.map(
        lambda x: float(x) if _finite_real(x) and x > 0 else np.nan
    )
    clean_volume = volumes.map(
        lambda x: float(x) if _finite_real(x) and x >= 0 else np.nan
    )
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        dollar_volume = clean_prices * clean_volume
        returns = clean_prices.pct_change(fill_method=None)
    dollar_volume = dollar_volume.where(np.isfinite(dollar_volume))
    returns = returns.where(np.isfinite(returns))
    adv = (
        dollar_volume.rolling(model.lookback, min_periods=model.lookback)
        .mean()
        .shift(signal_lag_periods)
    )
    volatility = (
        returns.rolling(model.lookback, min_periods=model.lookback)
        .std(ddof=1)
        .shift(signal_lag_periods)
    )
    return MarketLiquidity(adv, volatility, clean_volume)


def resolve_impact_liquidity(
    prices: pd.DataFrame,
    *,
    model: SquareRootImpactModel | None,
    volumes: pd.DataFrame | None,
    price_basis: str | None,
    volume_basis: str | None,
    evaluation_end: pd.Timestamp,
    signal_lag_periods: int,
    slippage_bps: float,
    precomputed_impact: bool = False,
    missing_price_policy: str = "raise",
) -> MarketLiquidity | None:
    """Bind optional engine inputs and keep unused future values outside estimation."""
    if model is None:
        if volumes is not None or price_basis is not None or volume_basis is not None:
            raise MarketImpactValidationError(
                "impact_input_ambiguous", "liquidity inputs require an impact model"
            )
        return None
    if slippage_bps != 0 or precomputed_impact or missing_price_policy != "raise":
        raise MarketImpactValidationError(
            "impact_input_ambiguous",
            "active impact requires strict prices and exclusive modeled slippage",
        )
    _panel_axes(prices, volumes)
    return prepare_market_liquidity(
        prices.loc[:evaluation_end],
        volumes.loc[:evaluation_end],
        price_basis=price_basis,
        volume_basis=volume_basis,
        model=model,
        signal_lag_periods=signal_lag_periods,
    )


def _aligned_series(reference: pd.Series, *others: pd.Series) -> None:
    if not isinstance(reference, pd.Series) or not reference.index.is_unique:
        raise MarketImpactValidationError(
            "impact_axes_invalid", "trade axes require a unique Series index"
        )
    if any(
        not isinstance(other, pd.Series) or not reference.index.equals(other.index)
        for other in others
    ):
        raise MarketImpactValidationError(
            "impact_axes_invalid", "all trade vectors require exact matching axes"
        )


def _costs(
    q: np.ndarray, adv: np.ndarray, sigma: np.ndarray, model: SquareRootImpactModel
) -> np.ndarray:
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        participation = q / adv
        result = q * (
            model.fixed_bps / 10000.0 + model.eta * sigma * np.sqrt(participation)
        )
        if model.mode == "penalize":
            excess = np.maximum(participation / model.max_participation_rate - 1.0, 0.0)
            result += adv * (model.penalty_bps / 10000.0) * excess**2
    if not np.isfinite(result).all():
        raise MarketImpactValidationError(
            "impact_cost_invalid", "modeled costs must remain finite"
        )
    return result


def calculate_market_impact(
    trade_values: pd.Series,
    adv: pd.Series,
    daily_volatility: pd.Series,
    *,
    model: SquareRootImpactModel,
) -> pd.DataFrame:
    """Quote signed dollar requests under one explicit participation policy."""
    if not isinstance(model, SquareRootImpactModel):
        raise MarketImpactValidationError(
            "impact_model_invalid", "a SquareRootImpactModel is required"
        )
    _aligned_series(trade_values, adv, daily_volatility)
    if not all(_finite_real(value) for value in trade_values):
        raise MarketImpactValidationError(
            "impact_trade_invalid",
            "trade values must be finite real non-Boolean dollars",
        )
    requested = trade_values.to_numpy(dtype=float)
    active = requested != 0
    for value in adv.iloc[np.flatnonzero(active)]:
        if not _finite_real(value) or value < model.min_adv:
            raise MarketImpactValidationError(
                "impact_adv_invalid",
                "nonzero trades require finite ADV at or above min_adv",
            )
    for value in daily_volatility.iloc[np.flatnonzero(active)]:
        if not _finite_real(value) or value < 0:
            raise MarketImpactValidationError(
                "impact_volatility_invalid",
                "nonzero trades require finite nonnegative daily volatility",
            )
    executed = requested.copy()
    costs = np.zeros(len(requested))
    rates = np.zeros(len(requested))
    a = adv.iloc[np.flatnonzero(active)].to_numpy(dtype=float)
    sigma = daily_volatility.iloc[np.flatnonzero(active)].to_numpy(dtype=float)
    q = np.abs(requested[active])
    caps = model.max_participation_rate * a
    if model.mode == "raise" and np.any(q > caps):
        raise MarketImpactValidationError(
            "impact_participation_exceeded",
            "requested dollars exceed the declared ADV participation cap",
        )
    if model.mode == "throttle":
        q = np.minimum(q, caps)
        executed[active] = np.sign(requested[active]) * q
    costs[active] = _costs(q, a, sigma, model)
    rates[active] = q / a
    if not np.isfinite(rates).all():
        raise MarketImpactValidationError(
            "impact_cost_invalid", "participation must remain finite"
        )
    return pd.DataFrame(
        {
            "requested_trade_value": requested,
            "executed_trade_value": executed,
            "remaining_trade_value": requested - executed,
            "participation_rate": rates,
            "slippage_cost": costs,
        },
        index=trade_values.index,
    )


def execute_impact_step(
    *,
    model: SquareRootImpactModel,
    liquidity: MarketLiquidity,
    date: pd.Timestamp,
    execution_prices: pd.Series,
    position_values: pd.Series,
    cash: float,
    equity_before: float,
    target_weights: pd.Series | None,
    pending_shares: pd.Series,
    eligible: pd.Series | None,
    settled: set,
    transaction_cost_bps: float,
    allow_short: bool = True,
) -> MarketImpactExecution:
    """Execute a frozen target or deferred shares with explicit self-financing cash."""
    _aligned_series(position_values, execution_prices, pending_shares)
    if (
        not _finite_real(cash)
        or cash < 0
        or not _finite_real(equity_before)
        or equity_before <= 0
        or not _finite_real(transaction_cost_bps)
        or transaction_cost_bps < 0
        or not all(_finite_real(x) for x in position_values)
        or not all(_finite_real(x) for x in pending_shares)
    ):
        raise MarketImpactValidationError(
            "impact_accounting_invalid",
            "positions, pending shares, cash and equity require finite admissible values",
        )
    try:
        balance = math.fsum([cash, *position_values.to_numpy(dtype=float)])
    except OverflowError as exc:
        raise MarketImpactValidationError(
            "impact_accounting_invalid", "cash plus signed positions must be finite"
        ) from exc
    if not math.isclose(balance, equity_before, rel_tol=1e-12, abs_tol=1e-12):
        raise MarketImpactValidationError(
            "impact_accounting_invalid",
            "cash plus signed positions must reconcile to pretrade equity",
        )
    zero = pd.Series(0.0, index=position_values.index)
    cancelled = zero.copy()
    prices = execution_prices.map(
        lambda x: float(x) if _finite_real(x) and x > 0 else np.nan
    )
    if target_weights is not None:
        _aligned_series(position_values, target_weights)
        if not all(_finite_real(x) for x in target_weights):
            raise MarketImpactValidationError(
                "impact_trade_invalid", "target weights must be finite real values"
            )
        cancelled += pending_shares
        requested = target_weights * equity_before - position_values
    else:
        pending = pending_shares.copy()
        ended = pending.index.isin(settled)
        cancelled.loc[ended] += pending.loc[ended]
        pending.loc[ended] = 0.0
        requested = zero.copy()
        active = pending.ne(0)
        requested.loc[active] = pending.loc[active] * prices.loc[active]
        if eligible is not None:
            _aligned_series(position_values, eligible)
            for asset in requested.index[~eligible.eq(True) & requested.ne(0)]:
                request, held = requested.loc[asset], position_values.loc[asset]
                reduction = (request > 0 and held < 0) or (request < 0 and held > 0)
                allowed = (
                    math.copysign(min(abs(request), abs(held)), request)
                    if reduction
                    else 0.0
                )
                cancelled.loc[asset] += (request - allowed) / prices.loc[asset]
                requested.loc[asset] = allowed
    active = requested.ne(0)
    if prices.loc[active].isna().any():
        raise MarketImpactValidationError(
            "impact_execution_price_invalid",
            "every requested market leg requires a positive finite execution price",
        )
    if not allow_short:
        if position_values.lt(0).any() or (
            target_weights is not None and target_weights.lt(0).any()
        ):
            raise MarketImpactValidationError(
                "impact_accounting_invalid",
                "long-only positions and targets require nonnegative values",
            )
        # Retried shares can exceed the remaining long by roundoff after valuation.
        # Bound the actual sell request and record its unused share remainder.
        bounded = requested.clip(lower=-position_values)
        cancelled.loc[active] += (
            requested.loc[active] - bounded.loc[active]
        ) / prices.loc[active]
        requested = bounded
        active = requested.ne(0)
    quote = calculate_market_impact(
        requested,
        liquidity.adv.loc[date],
        liquidity.daily_volatility.loc[date],
        model=model,
    )
    executed = quote["executed_trade_value"].copy()
    a = liquidity.adv.loc[date]
    sigma = liquidity.daily_volatility.loc[date]
    sells = executed.lt(0)
    buys = executed.gt(0)
    commission_rate = transaction_cost_bps / 10000.0
    sell_commission = float((-executed.loc[sells]).sum()) * commission_rate
    sell_slippage = float(quote.loc[sells, "slippage_cost"].sum())
    available = (
        cash - float(executed.loc[sells].sum()) - sell_commission - sell_slippage
    )
    if not math.isfinite(available) or available < 0:
        raise MarketImpactValidationError(
            "impact_cash_insufficient", "cash and sale proceeds must cover sell costs"
        )
    # An all-True pandas selection can share its buffer with executed.
    # Funding quotes retain the unscaled values while actual fills are updated.
    buy_values = executed.loc[buys].to_numpy(dtype=float, copy=True)
    buy_adv = a.loc[buys].to_numpy(dtype=float)
    buy_sigma = sigma.loc[buys].to_numpy(dtype=float)

    def buy_outlay(scale: float) -> tuple[float, float, float]:
        amount = float((buy_values * scale).sum())
        fee = amount * commission_rate
        impact = float(_costs(buy_values * scale, buy_adv, buy_sigma, model).sum())
        return amount + fee + impact, fee, impact

    scale = 1.0
    if buy_outlay(scale)[0] > available:
        lower, upper = 0.0, 1.0
        for _ in range(64):
            middle = (lower + upper) / 2.0
            if buy_outlay(middle)[0] <= available:
                lower = middle
            else:
                upper = middle
        scale = lower
    executed.loc[buys] *= scale
    buy_spend, buy_commission, buy_slippage = buy_outlay(scale)
    commission = sell_commission + buy_commission
    slippage = sell_slippage + buy_slippage
    cash_after = available - buy_spend
    equity_after = equity_before - commission - slippage
    if (
        not all(
            math.isfinite(x) for x in (cash_after, commission, slippage, equity_after)
        )
        or cash_after < 0
        or equity_after <= 0
    ):
        raise MarketImpactValidationError(
            "impact_portfolio_insolvent",
            "cash and postcost equity must remain finite and admissible",
        )
    traded = executed.ne(0)
    observed_volume = liquidity.observed_volume.loc[date, traded]
    if observed_volume.isna().any() or observed_volume.le(0).any():
        raise MarketImpactValidationError(
            "impact_execution_volume_invalid",
            "actual market fills require positive observed execution volume",
        )
    pending_next = zero.copy()
    pending_next.loc[active] = (
        quote.loc[active, "remaining_trade_value"] / prices.loc[active]
    )
    cancelled.loc[active] += (
        quote.loc[active, "executed_trade_value"] - executed.loc[active]
    ) / prices.loc[active]
    rates = zero.copy()
    rates.loc[traded] = executed.loc[traded].abs() / a.loc[traded]
    positions_after = position_values + executed
    if not all(
        np.isfinite(series.to_numpy(dtype=float)).all()
        for series in (positions_after, pending_next, cancelled)
    ):
        raise MarketImpactValidationError(
            "impact_accounting_invalid",
            "position and share arithmetic must remain finite",
        )
    post_trade_balance = cash_after + float(positions_after.sum())
    if not _post_trade_reconciles(post_trade_balance, equity_after):
        raise MarketImpactValidationError(
            "impact_accounting_invalid",
            "cash plus signed positions must reconcile to post-cost equity",
        )
    return MarketImpactExecution(
        positions_after,
        cash_after,
        commission,
        slippage,
        executed,
        rates,
        pending_next,
        cancelled,
    )


def impact_assumptions(
    model: SquareRootImpactModel | None, *, price_basis, volume_basis
):
    """Describe the optional accounting path without altering legacy assumptions."""
    if model is None:
        return {}
    return {
        "impact_model": asdict(model),
        "impact_price_basis": price_basis,
        "impact_volume_basis": volume_basis,
        "slippage_model": "lagged_daily_square_root_scenario_v1",
        "cash_model": "self_financing_dollar_positions_sells_then_cash_funded_buys",
        "cost_model": "commission_plus_impact_on_actual_dollar_trades",
        "holdings_model": "quantity_preserving_with_partial_fills",
        "turnover_model": "absolute_actual_dollar_trades_over_pretrade_equity",
        "signed_trade_weight_model": "actual_signed_dollars_over_pretrade_equity",
        "trade_weight_model": "absolute_actual_dollars_over_pretrade_equity",
        "impact_estimation": "full_source_complete_windows_shifted_by_signal_lag",
        "participation_basis": "actual_dollars_over_lagged_ADV",
        "pending_policy": "liquidity_deferred_shares_replaced_at_next_target",
        "funding_policy": "common_buy_scale_with_cash_unfilled_shares_cancelled",
        "exposure_policy": "constraints_apply_to_targets_actual_exposure_can_drift",
        "terminal_impact_fee": 0.0,
        "formal_market_impact_evidence_eligible": False,
        "zero_cost_or_slippage_is_diagnostic": True,
    }


def impact_result_fields(
    *,
    index,
    columns,
    equity,
    slippage_returns,
    executed,
    participation,
    pending,
    cancelled,
    slippage_dollars=None,
):
    """Build the six additive audit fields from engine accounting arrays."""
    previous_equity = np.r_[float(equity[0]), np.asarray(equity)[:-1]]
    dollars = (
        np.asarray(slippage_returns) * previous_equity
        if slippage_dollars is None
        else np.asarray(slippage_dollars)
    )
    traded = np.abs(executed).sum(axis=1)
    bps = (
        np.divide(dollars, traded, out=np.zeros(len(index)), where=traded != 0)
        * 10000.0
    )
    return {
        "slippage_cost_series": pd.Series(
            dollars, index=index, name="slippage_cost_dollars"
        ),
        "realized_slippage_bps": pd.Series(
            bps, index=index, name="realized_slippage_bps"
        ),
        "trade_participation_rates": pd.DataFrame(
            participation, index=index, columns=columns
        ),
        "executed_trade_values": pd.DataFrame(executed, index=index, columns=columns),
        "pending_trade_shares": pd.DataFrame(pending, index=index, columns=columns),
        "cancelled_trade_shares": pd.DataFrame(cancelled, index=index, columns=columns),
    }
