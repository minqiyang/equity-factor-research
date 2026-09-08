"""Portfolio construction and accounting helpers.

This module contains a minimal long-only, equal-weight cross-sectional
backtester for research use. It does not place trades, connect to a broker, or
fetch data.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from fractions import Fraction
import hashlib
import math
from numbers import Integral, Real
from typing import Any, Literal, Mapping

import numpy as np
import pandas as pd

from backtest.metrics import calculate_basic_metrics, calculate_holding_episode_metrics
from risk.constraints import apply_long_only_position_cap


_VOLUME_AWARE_SLIPPAGE_MODES = {"diagnostic_only", "apply_precomputed_impact"}
_TIMING_CONTRACT = "after_close_signal_next_observed_close_v1"
_SOURCE_PROVENANCE_POLICY = "tracked_pre_mutation_source_snapshot_v1"
_LEDGER_PHASE_SIGNAL_AVAILABILITY = "strictly_after_feature_row_close"
_LEDGER_PHASE_DECISION = "immediately_after_signal_availability"
_LEDGER_PHASE_EXECUTION = "observed_source_row_close_idealized_reset"
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
_NUMPY_INTEGER_SCALAR_TYPES = frozenset(
    np.dtype(typecode).type for typecode in np.typecodes["AllInteger"]
)
_NUMPY_FLOAT_SCALAR_TYPES = frozenset(
    np.dtype(typecode).type for typecode in np.typecodes["Float"]
)
_NUMPY_COMPLEX_SCALAR_TYPES = frozenset(
    np.dtype(typecode).type for typecode in np.typecodes["Complex"]
)
_MAX_SOURCE_FLOAT_MANTISSA_BITS = np.finfo(np.float64).nmant
_SOURCE_NUMPY_FLOAT_SCALAR_TYPES = frozenset(
    scalar_type
    for scalar_type in _NUMPY_FLOAT_SCALAR_TYPES
    if np.finfo(scalar_type).nmant <= _MAX_SOURCE_FLOAT_MANTISSA_BITS
)
_SOURCE_NUMPY_COMPLEX_SCALAR_TYPES = frozenset(
    scalar_type
    for scalar_type in _NUMPY_COMPLEX_SCALAR_TYPES
    if np.finfo(scalar_type).nmant <= _MAX_SOURCE_FLOAT_MANTISSA_BITS
)
_EXACT_INTEGER_SCALAR_TYPES = frozenset({int, *_NUMPY_INTEGER_SCALAR_TYPES})
_EXACT_REAL_SCALAR_TYPES = frozenset(
    {
        int,
        float,
        Fraction,
        *_NUMPY_INTEGER_SCALAR_TYPES,
        *_NUMPY_FLOAT_SCALAR_TYPES,
    }
)
_EXACT_BOOLEAN_SCALAR_TYPES = frozenset({bool, np.bool_})
_EXACT_SOURCE_COMPLEX_SCALAR_TYPES = frozenset(
    {complex, *_SOURCE_NUMPY_COMPLEX_SCALAR_TYPES}
)


class BacktestValidationError(ValueError):
    """Deterministic validation failure with a machine-readable reason."""

    def __init__(
        self,
        reason: str,
        detail: str,
        *,
        date: pd.Timestamp | None = None,
        asset: object | None = None,
    ) -> None:
        self.reason = reason
        self.date = date
        self.asset = asset
        context = []
        if date is not None:
            context.append(f"date={date.isoformat()}")
        if asset is not None:
            context.append(f"asset={asset!r}")
        suffix = "" if not context else f" ({', '.join(context)})"
        super().__init__(f"{reason}: {detail}{suffix}")


class _SourceLineageToken:
    """Opaque in-process marker for a library-issued provenance lineage."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class SourceCellSnapshot:
    """Immutable semantic representation of one source cell."""

    __experiment_log_private__ = True

    kind: str
    payload: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SourceMutationRecord:
    """One mutation performed through the provenance-controlled API."""

    __experiment_log_private__ = True

    sequence: int
    row_position: int
    column_position: int
    assigned_value: SourceCellSnapshot
    before_state_digest: str
    after_state_digest: str
    record_digest: str


@dataclass(frozen=True, slots=True, repr=False)
class SourceFrameProvenance:
    """Role-bound immutable snapshot and controlled mutation ledger."""

    __experiment_log_private__ = True

    schema_version: str
    role: Literal["prices", "signals"]
    axis_fingerprint: tuple[object, ...]
    original_dtype_names: tuple[str, ...]
    original_dtype_families: tuple[str, ...]
    original_cells: tuple[tuple[SourceCellSnapshot, ...], ...]
    original_state_digest: str
    current_state_digest: str
    mutations: tuple[SourceMutationRecord, ...]
    _source_identity: int = field(repr=False, compare=False)
    _lineage_token: object = field(repr=False, compare=False)


@dataclass(frozen=True, slots=True, repr=False)
class BacktestSourceProvenance:
    """Exact price/signal provenance required by the bounded backtester."""

    __experiment_log_private__ = True

    schema_version: str
    prices: SourceFrameProvenance
    signals: SourceFrameProvenance


@dataclass(frozen=True)
class TimingLedgerRow:
    """One auditable signal/decision/execution timing event."""

    ledger_date: pd.Timestamp
    scheduled_execution_date: pd.Timestamp | None
    is_scheduled_rebalance: bool
    event_status: str
    signal_source_date: pd.Timestamp | None
    feature_observation_end: pd.Timestamp | None
    signal_availability_phase: str | None
    decision_phase: str | None
    execution_phase: str | None
    incoming_return_start: pd.Timestamp | None
    incoming_return_end: pd.Timestamp | None
    first_holding_return_start: pd.Timestamp | None
    first_holding_return_end: pd.Timestamp | None
    is_terminal_scheduled_row: bool


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
    timing_metadata: dict[str, Any]
    timing_ledger: tuple[TimingLedgerRow, ...]
    assumptions: dict[str, Any]


def capture_backtest_source_provenance(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
) -> BacktestSourceProvenance:
    """Capture the caller-declared immutable baseline source state.

    Enforcement begins at this call; the library cannot infer source history
    that was already erased before capture. Callers must invoke it immediately
    after the final price and signal panels are constructed. Any later source
    mutation must use
    :func:`apply_tracked_backtest_source_mutation`; an arbitrary pandas write,
    copy, replacement, or dtype conversion invalidates the handle.
    """

    if not isinstance(prices, pd.DataFrame) or not isinstance(
        signals,
        pd.DataFrame,
    ):
        raise BacktestValidationError(
            "source_axes_invalid",
            "source provenance requires pandas DataFrame price and signal sources",
        )
    return BacktestSourceProvenance(
        schema_version=_SOURCE_PROVENANCE_POLICY,
        prices=_capture_source_frame_provenance(prices, role="prices"),
        signals=_capture_source_frame_provenance(signals, role="signals"),
    )


def apply_tracked_backtest_source_mutation(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    source_provenance: BacktestSourceProvenance,
    *,
    source_role: Literal["prices", "signals"],
    row_position: int,
    column_position: int,
    value: object,
) -> tuple[pd.DataFrame, pd.DataFrame, BacktestSourceProvenance]:
    """Return copied sources plus provenance after one controlled mutation."""

    if source_role not in {"prices", "signals"}:
        raise BacktestValidationError(
            "source_provenance_invalid",
            "source_role must be either 'prices' or 'signals'",
        )
    _validate_backtest_source_provenance(
        prices=prices,
        signals=signals,
        source_provenance=source_provenance,
    )
    row = _read_exact_integral_scalar(row_position)
    column = _read_exact_integral_scalar(column_position)
    if row is None or column is None:
        raise BacktestValidationError(
            "source_provenance_invalid",
            "tracked mutation coordinates must be non-boolean integer positions",
        )

    selected = prices if source_role == "prices" else signals
    if row < 0:
        row += len(selected.index)
    if column < 0:
        column += len(selected.columns)
    if (
        row < 0
        or row >= len(selected.index)
        or column < 0
        or column >= len(selected.columns)
    ):
        raise BacktestValidationError(
            "source_provenance_invalid",
            "tracked mutation coordinates must resolve inside the source axes",
        )

    mutated_prices = prices
    mutated_signals = signals
    selected_copy = selected.copy(deep=True)
    _prepare_tracked_mutation_column(
        selected_copy,
        column_position=column,
        value=value,
    )
    selected_copy.iat[row, column] = value
    selected_provenance = (
        source_provenance.prices
        if source_role == "prices"
        else source_provenance.signals
    )
    before_digest = selected_provenance.current_state_digest
    after_digest = _source_state_digest(selected_copy, role=source_role)
    assigned_value = _snapshot_source_cell(value)
    sequence = len(selected_provenance.mutations)
    record = SourceMutationRecord(
        sequence=sequence,
        row_position=row,
        column_position=column,
        assigned_value=assigned_value,
        before_state_digest=before_digest,
        after_state_digest=after_digest,
        record_digest=_mutation_record_digest(
            lineage_digest=selected_provenance.original_state_digest,
            sequence=sequence,
            row_position=row,
            column_position=column,
            assigned_value=assigned_value,
            before_state_digest=before_digest,
            after_state_digest=after_digest,
        ),
    )
    updated_frame_provenance = replace(
        selected_provenance,
        current_state_digest=after_digest,
        mutations=(*selected_provenance.mutations, record),
        _source_identity=id(selected_copy),
    )
    if source_role == "prices":
        mutated_prices = selected_copy
        updated_provenance = replace(
            source_provenance,
            prices=updated_frame_provenance,
        )
    else:
        mutated_signals = selected_copy
        updated_provenance = replace(
            source_provenance,
            signals=updated_frame_provenance,
        )
    return mutated_prices, mutated_signals, updated_provenance


def _prepare_tracked_mutation_column(
    source: pd.DataFrame,
    *,
    column_position: int,
    value: object,
) -> None:
    """Promote a copied column explicitly before an incompatible test write."""

    dtype = source.dtypes.iloc[column_position]
    if isinstance(value, complex | np.complexfloating):
        if not (
            pd.api.types.is_complex_dtype(dtype)
            or pd.api.types.is_object_dtype(dtype)
        ):
            target_dtype = (
                complex
                if isinstance(dtype, np.dtype)
                and pd.api.types.is_numeric_dtype(dtype)
                and not pd.api.types.is_bool_dtype(dtype)
                else object
            )
            source.isetitem(
                column_position,
                source.iloc[:, column_position].astype(target_dtype),
            )
        return
    if isinstance(value, bool | np.bool_) or not isinstance(value, Real):
        if not pd.api.types.is_object_dtype(dtype):
            source.isetitem(
                column_position,
                source.iloc[:, column_position].astype(object),
            )


def run_long_only_backtest(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    *,
    source_provenance: BacktestSourceProvenance,
    evaluation_start: pd.Timestamp,
    evaluation_end: pd.Timestamp,
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
    """Run the bounded after-close/next-observed-close research contract.

    The inclusive evaluation bounds are exact source-row labels. The first
    bounded row is an all-cash initialization anchor. A scheduled row ``a[j]``
    uses only ``signals[a[j - signal_lag_periods]]`` and a target established at
    its close first earns the return ending on the next observed row.

    This is idealized close-reset accounting, not order, fill, auction,
    brokerage, LEAN-parity, or live-trading behavior.
    """

    _validate_backtest_inputs(
        prices=prices,
        signals=signals,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
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

    start_pos, end_pos, accounting_dates = _resolve_accounting_window(
        prices.index,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
    )
    price_provenance, signal_provenance = _validate_backtest_source_provenance(
        prices=prices,
        signals=signals,
        source_provenance=source_provenance,
    )
    price_data, recovered_price_columns = _extract_bounded_source_values(
        prices,
        provenance=price_provenance,
        start_pos=start_pos,
        end_pos=end_pos,
    )
    bounded_signal_values, recovered_signal_columns = (
        _extract_bounded_source_values(
            signals,
            provenance=signal_provenance,
            start_pos=start_pos,
            end_pos=end_pos,
        )
    )
    signal_data = _validate_bounded_signal_values(bounded_signal_values)
    rebalance_dates = _get_rebalance_dates(accounting_dates, rebalance_frequency)
    lagged_signals = signal_data.shift(signal_lag_periods)

    target_weights = _build_target_weights(
        lagged_signals=lagged_signals,
        rebalance_dates=rebalance_dates,
        initialization_anchor=accounting_dates[0],
        signal_lag_periods=signal_lag_periods,
        top_n=top_n,
        top_pct=top_pct,
    )
    if max_position_weight is not None:
        target_weights = apply_long_only_position_cap(
            target_weights.fillna(0.0),
            max_position_weight=max_position_weight,
        ).where(target_weights.notna())

    raw_volume_impact, volume_impact_basis = _prepare_volume_aware_slippage_input(
        accounting_dates=accounting_dates,
        mode=volume_aware_slippage_mode,
        impact=volume_aware_slippage_impact,
        metadata=volume_aware_slippage_metadata,
        fixed_slippage_bps=slippage_bps,
    )
    (
        holdings,
        gross_returns,
        signed_trade_weights,
        trade_weights,
        resolved_asset_returns,
        turnover,
        transaction_costs,
        slippage_costs,
        volume_aware_slippage_costs,
        total_trading_costs,
        net_returns,
        equity_curve,
    ) = _calculate_bounded_portfolio_path(
        prices=price_data,
        target_weights=target_weights,
        initial_capital=float(initial_capital),
        transaction_cost_bps=float(transaction_cost_bps),
        slippage_bps=float(slippage_bps),
        raw_volume_impact=raw_volume_impact,
        volume_impact_basis=volume_impact_basis,
        missing_price_policy=missing_price_policy,
    )

    benchmark_equity_curve, benchmark_returns = _calculate_benchmark_path(
        benchmark_prices=benchmark_prices,
        accounting_dates=accounting_dates,
        initial_capital=float(initial_capital),
        benchmark_missing_policy=benchmark_missing_policy,
    )
    formal_benchmark_equity = (
        benchmark_equity_curve if benchmark_missing_policy == "raise" else None
    )
    formal_benchmark_returns = (
        benchmark_returns if benchmark_missing_policy == "raise" else None
    )

    metrics = calculate_basic_metrics(
        equity_curve,
        net_returns,
        holdings=holdings,
        turnover=turnover,
        transaction_costs=transaction_costs,
        slippage_costs=slippage_costs,
        volume_aware_slippage_costs=volume_aware_slippage_costs,
        benchmark_equity_curve=formal_benchmark_equity,
        benchmark_returns=formal_benchmark_returns,
        initial_capital=float(initial_capital),
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
    timing_metadata = _build_timing_metadata(
        accounting_dates=accounting_dates,
        rebalance_dates=rebalance_dates,
        signal_lag_periods=signal_lag_periods,
        missing_price_policy=missing_price_policy,
        benchmark_missing_policy=benchmark_missing_policy,
        provenance_recovery_applied=bool(
            recovered_price_columns or recovered_signal_columns
        ),
    )
    timing_ledger = _build_timing_ledger(
        accounting_dates=accounting_dates,
        rebalance_dates=rebalance_dates,
        target_weights=target_weights,
        signal_lag_periods=signal_lag_periods,
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
        timing_metadata=timing_metadata,
        timing_ledger=timing_ledger,
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
            "execution_timing": _TIMING_CONTRACT,
            "turnover_model": "target_weight_turnover",
            "turnover_reference": "drifted_pretrade_weights",
            "trade_weight_model": "absolute_target_minus_drifted_pretrade_by_asset",
            "signed_trade_weight_model": "target_minus_drifted_pretrade_by_asset",
            "holdings_model": "drifted_between_rebalances",
            "cost_model": "fixed_bps_on_target_weight_turnover",
            "slippage_model": "fixed_bps_on_target_weight_turnover",
            "fixed_cost_application_timing": "close_after_asset_returns",
            "fixed_cost_return_impact_basis": "beginning_period_portfolio_value",
            "sharpe_return_basis": "net_after_applied_costs",
            "sharpe_risk_free_policy": "zero",
            "sharpe_ddof": 0,
            "sharpe_periods_per_year": 252,
            "sharpe_measured_row_policy": "exclude_initialization_anchor",
            "zero_cost_or_slippage_is_diagnostic": zero_cost_or_slippage_is_diagnostic,
            "formal_timing_evidence_eligible": (
                missing_price_policy == "raise"
                and benchmark_missing_policy == "raise"
            ),
            "long_only": True,
            "leverage": "none",
            **timing_metadata,
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
                if formal_benchmark_returns is not None
                else {}
            ),
            **volume_aware_assumptions,
        },
    )


def _build_target_weights(
    *,
    lagged_signals: pd.DataFrame,
    rebalance_dates: pd.DatetimeIndex,
    initialization_anchor: pd.Timestamp,
    signal_lag_periods: int,
    top_n: int | None,
    top_pct: float | None,
) -> pd.DataFrame:
    target_weights = pd.DataFrame(
        np.nan,
        index=lagged_signals.index,
        columns=lagged_signals.columns,
    )

    for date in rebalance_dates:
        position = lagged_signals.index.get_loc(date)
        if date == initialization_anchor or position < signal_lag_periods:
            continue

        target_weights.loc[date] = 0.0
        scores = lagged_signals.loc[date]
        valid_scores = scores[scores.notna()]

        selected_assets = _select_top_assets(valid_scores, top_n=top_n, top_pct=top_pct)
        if not selected_assets:
            continue

        equal_weight = 1.0 / len(selected_assets)
        target_weights.loc[date, selected_assets] = equal_weight

    return target_weights


def _calculate_bounded_portfolio_path(
    *,
    prices: pd.DataFrame,
    target_weights: pd.DataFrame,
    initial_capital: float,
    transaction_cost_bps: float,
    slippage_bps: float,
    raw_volume_impact: pd.Series,
    volume_impact_basis: str | None,
    missing_price_policy: str,
) -> tuple[
    pd.DataFrame,
    pd.Series,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.Series,
    pd.Series,
    pd.Series,
    pd.Series,
    pd.Series,
    pd.Series,
    pd.Series,
]:
    """Advance bounded accounting rows in the contract's normative order."""

    index = prices.index
    columns = prices.columns
    holdings = pd.DataFrame(0.0, index=index, columns=columns)
    gross_returns = pd.Series(0.0, index=index, name="gross_return")
    signed_trade_weights = pd.DataFrame(0.0, index=index, columns=columns)
    trade_weights = pd.DataFrame(0.0, index=index, columns=columns)
    resolved_asset_returns = pd.DataFrame(0.0, index=index, columns=columns)
    turnover = pd.Series(0.0, index=index, name="turnover")
    transaction_costs = pd.Series(
        0.0,
        index=index,
        name="transaction_cost_impact",
    )
    slippage_costs = pd.Series(0.0, index=index, name="slippage_impact")
    volume_aware_costs = pd.Series(
        0.0,
        index=index,
        name="volume_aware_slippage_impact",
    )
    total_costs = pd.Series(0.0, index=index, name="total_trading_cost_impact")
    net_returns = pd.Series(0.0, index=index, name="return")
    equity_curve = pd.Series(np.nan, index=index, name="equity")
    equity_curve.iloc[0] = initial_capital
    post_trade_weights = pd.Series(0.0, index=columns, dtype=float)

    if raw_volume_impact.iloc[0] != 0.0:
        raise BacktestValidationError(
            "volume_aware_slippage_invalid",
            "the initialization anchor must have zero applied impact",
            date=index[0],
        )

    for position in range(1, len(index)):
        date = index[position]
        previous_date = index[position - 1]
        period_returns = _calculate_held_asset_returns(
            previous_prices=prices.iloc[position - 1],
            current_prices=prices.iloc[position],
            previous_holdings=post_trade_weights,
            previous_date=previous_date,
            current_date=date,
            missing_price_policy=missing_price_policy,
        )
        resolved_asset_returns.loc[date] = period_returns

        with np.errstate(over="ignore", invalid="ignore"):
            weighted_asset_returns = post_trade_weights * period_returns
            weighted_return_values = (
                weighted_asset_returns.to_numpy(dtype=float).tolist()
            )
            gross_return = math.fsum(weighted_return_values)
            gross_multiplier = math.fsum([1.0, *weighted_return_values])
        _validate_pretrade_gross(
            gross_return=gross_return,
            gross_multiplier=gross_multiplier,
            date=date,
        )
        gross_returns.loc[date] = gross_return

        with np.errstate(over="ignore", invalid="ignore"):
            grown_weights = post_trade_weights * (1.0 + period_returns)
        pretrade_weights = (
            grown_weights / gross_multiplier
            if post_trade_weights.ne(0.0).any()
            else post_trade_weights.copy()
        )

        target = target_weights.loc[date]
        if target.notna().any():
            frozen_target = target.fillna(0.0)
            signed_trades = frozen_target - pretrade_weights
            _validate_execution_price_legs(
                execution_prices=prices.iloc[position],
                signed_trade_weights=signed_trades,
                date=date,
            )
            signed_trade_weights.loc[date] = signed_trades
            trade_weights.loc[date] = signed_trades.abs()
            next_holdings = frozen_target
        else:
            next_holdings = pretrade_weights

        row_turnover = float(trade_weights.loc[date].sum())
        turnover.loc[date] = row_turnover
        with np.errstate(over="ignore", invalid="ignore"):
            fixed_transaction_cost = (
                row_turnover * (transaction_cost_bps / 10_000.0) * gross_multiplier
            )
            fixed_slippage_cost = (
                row_turnover * (slippage_bps / 10_000.0) * gross_multiplier
            )
            volume_cost = float(raw_volume_impact.loc[date])
            if volume_impact_basis == "post_return_portfolio_value":
                volume_cost *= gross_multiplier

        if row_turnover == 0.0 and volume_cost != 0.0:
            raise BacktestValidationError(
                "volume_aware_slippage_invalid",
                "applied impact must be zero when turnover is zero",
                date=date,
            )
        transaction_costs.loc[date] = fixed_transaction_cost
        slippage_costs.loc[date] = fixed_slippage_cost
        volume_aware_costs.loc[date] = volume_cost
        row_total_cost = (
            fixed_transaction_cost + fixed_slippage_cost + volume_cost
        )
        total_costs.loc[date] = row_total_cost

        with np.errstate(over="ignore", invalid="ignore"):
            net_return = gross_return - row_total_cost
            net_multiplier = 1.0 + net_return
            equity_candidate = float(equity_curve.iloc[position - 1]) * net_multiplier
        _validate_postcost_net_equity(
            net_return=net_return,
            net_multiplier=net_multiplier,
            equity_candidate=equity_candidate,
            date=date,
        )
        net_returns.loc[date] = net_return
        equity_curve.loc[date] = equity_candidate
        holdings.loc[date] = next_holdings
        post_trade_weights = next_holdings

    return (
        holdings,
        gross_returns,
        signed_trade_weights,
        trade_weights,
        resolved_asset_returns,
        turnover,
        transaction_costs,
        slippage_costs,
        volume_aware_costs,
        total_costs,
        net_returns,
        equity_curve,
    )


def _calculate_held_asset_returns(
    *,
    previous_prices: pd.Series,
    current_prices: pd.Series,
    previous_holdings: pd.Series,
    previous_date: pd.Timestamp,
    current_date: pd.Timestamp,
    missing_price_policy: str,
) -> pd.Series:
    """Calculate only economically relevant held-asset returns."""

    period_returns = pd.Series(0.0, index=previous_holdings.index, dtype=float)
    for asset in previous_holdings.index[previous_holdings.ne(0.0)]:
        previous_price = _read_positive_price(previous_prices.loc[asset])
        current_price = _read_positive_price(current_prices.loc[asset])
        if previous_price is None or current_price is None:
            if missing_price_policy == "zero_return":
                period_returns.loc[asset] = 0.0
                continue
            invalid_endpoint = (
                previous_date if previous_price is None else current_date
            )
            raise BacktestValidationError(
                "incoming_price_invalid",
                "held prior/current close endpoints must be finite positive real values",
                date=invalid_endpoint,
                asset=asset,
            )
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            period_returns.loc[asset] = current_price / previous_price - 1.0
    return period_returns


def _validate_execution_price_legs(
    *,
    execution_prices: pd.Series,
    signed_trade_weights: pd.Series,
    date: pd.Timestamp,
) -> None:
    """Validate every frozen nonzero buy, sell, or liquidation leg."""

    for asset in signed_trade_weights.index[signed_trade_weights.ne(0.0)]:
        if _read_positive_price(execution_prices.loc[asset]) is None:
            raise BacktestValidationError(
                "execution_price_invalid",
                "every nonzero frozen trade leg requires a finite positive real close",
                date=date,
                asset=asset,
            )


def _validate_pretrade_gross(
    *,
    gross_return: float,
    gross_multiplier: float,
    date: pd.Timestamp,
) -> None:
    if (
        not np.isfinite(gross_return)
        or not np.isfinite(gross_multiplier)
        or gross_multiplier <= 0.0
    ):
        raise BacktestValidationError(
            "portfolio_insolvent_or_non_finite_before_trade",
            "gross return and multiplier must be finite with positive multiplier",
            date=date,
        )


def _validate_postcost_net_equity(
    *,
    net_return: float,
    net_multiplier: float,
    equity_candidate: float,
    date: pd.Timestamp,
) -> None:
    if (
        not np.isfinite(net_return)
        or not np.isfinite(net_multiplier)
        or net_multiplier <= 0.0
        or not np.isfinite(equity_candidate)
        or equity_candidate <= 0.0
    ):
        raise BacktestValidationError(
            "portfolio_insolvent_or_non_finite_after_costs",
            "net return, multiplier, and resulting equity must remain finite and positive",
            date=date,
        )


def _read_positive_price(value: object) -> float | None:
    numeric = _read_finite_real_scalar(value)
    if numeric is None or numeric <= 0.0:
        return None
    return numeric


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


def _calculate_benchmark_path(
    *,
    benchmark_prices: pd.Series | None,
    accounting_dates: pd.DatetimeIndex,
    initial_capital: float,
    benchmark_missing_policy: str,
) -> tuple[pd.Series | None, pd.Series | None]:
    if benchmark_prices is None:
        return None, None

    _validate_benchmark_structure(
        benchmark_prices,
        accounting_dates=accounting_dates,
        require_exact_axis=benchmark_missing_policy == "raise",
    )

    if benchmark_missing_policy == "raise":
        clean_values = []
        for date, value in benchmark_prices.items():
            price = _read_positive_price(value)
            if price is None:
                raise BacktestValidationError(
                    "benchmark_prices_invalid",
                    "formal benchmark prices must be finite positive real values",
                    date=date,
                )
            clean_values.append(price)
        aligned_prices = pd.Series(
            clean_values,
            index=accounting_dates,
            name=benchmark_prices.name,
        )
    else:
        observed_values: list[float] = []
        observed_dates: list[pd.Timestamp] = []
        for date, value in benchmark_prices.items():
            price = _read_positive_price(value)
            if price is None:
                if pd.isna(value):
                    continue
                raise BacktestValidationError(
                    "benchmark_prices_invalid",
                    "diagnostic benchmark observations must be finite positive real values",
                    date=date,
                )
            observed_dates.append(date)
            observed_values.append(price)
        observed = pd.Series(observed_values, index=observed_dates, dtype=float)
        combined_index = observed.index.union(accounting_dates).sort_values()
        aligned_prices = observed.reindex(combined_index).ffill().reindex(
            accounting_dates
        )
        if aligned_prices.iloc[0] != aligned_prices.iloc[0]:
            aligned_prices.iloc[0] = 1.0
        aligned_prices = aligned_prices.ffill()

    benchmark_returns = aligned_prices.pct_change(fill_method=None)
    if benchmark_missing_policy == "zero_return":
        benchmark_returns = benchmark_returns.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    else:
        benchmark_returns.iloc[0] = 0.0
        if not np.isfinite(benchmark_returns.to_numpy()).all():
            raise BacktestValidationError(
                "benchmark_prices_invalid",
                "benchmark price ratios must produce finite returns",
            )

    benchmark_returns = benchmark_returns.rename("benchmark_return")
    benchmark_equity_curve = (
        initial_capital * (1.0 + benchmark_returns).cumprod()
    ).rename("benchmark_equity")
    return benchmark_equity_curve, benchmark_returns


def _validate_benchmark_structure(
    benchmark_prices: pd.Series,
    *,
    accounting_dates: pd.DatetimeIndex,
    require_exact_axis: bool,
) -> None:
    if not isinstance(benchmark_prices, pd.Series):
        raise BacktestValidationError(
            "benchmark_prices_invalid",
            "benchmark_prices must be a pandas Series",
        )
    if not isinstance(benchmark_prices.index, pd.DatetimeIndex):
        raise BacktestValidationError(
            "benchmark_prices_invalid",
            "benchmark_prices must use a DatetimeIndex",
        )
    if (
        benchmark_prices.index.has_duplicates
        or not benchmark_prices.index.is_monotonic_increasing
    ):
        raise BacktestValidationError(
            "benchmark_prices_invalid",
            "benchmark dates must be unique and strictly increasing",
        )
    if benchmark_prices.index.tz != accounting_dates.tz:
        raise BacktestValidationError(
            "benchmark_prices_invalid",
            "benchmark and accounting dates must use the same timezone",
        )
    if require_exact_axis and not benchmark_prices.index.equals(accounting_dates):
        raise BacktestValidationError(
            "benchmark_prices_invalid",
            "formal benchmark index must exactly match accounting dates",
        )


def _calculate_signal_coverage(signal_data: pd.DataFrame) -> float:
    if signal_data.empty or signal_data.size == 0:
        return float("nan")

    return float(signal_data.notna().sum().sum() / signal_data.size)


def _build_timing_metadata(
    *,
    accounting_dates: pd.DatetimeIndex,
    rebalance_dates: pd.DatetimeIndex,
    signal_lag_periods: int,
    missing_price_policy: str,
    benchmark_missing_policy: str,
    provenance_recovery_applied: bool,
) -> dict[str, Any]:
    measured_dates = accounting_dates[1:]
    return {
        "timing_contract": _TIMING_CONTRACT,
        "feature_time": "source_row_close_conservative",
        "signal_availability_time": "strictly_after_feature_row_close",
        "decision_time": "immediately_after_signal_availability_on_signal_source_row",
        "execution_time": "observed_source_row_close_idealized_reset",
        "signal_lag_rows": signal_lag_periods,
        "signal_lag_unit": "observed_source_rows_within_bounded_accounting_slice",
        "return_frequency": "daily_close_to_close",
        "periods_per_year": 252,
        "return_interval": "previous_close_to_current_close",
        "holding_effective_interval": "execution_close_to_next_observed_close",
        "cost_application_time": "execution_close_after_row_gross_return",
        "cost_return_basis": "beginning_period_portfolio_value",
        "evaluation_start": accounting_dates[0],
        "evaluation_end": accounting_dates[-1],
        "metric_anchor_policy": "exclude_initialization_anchor_use_common_measured_rows",
        "measured_return_start": measured_dates[0],
        "measured_return_end": measured_dates[-1],
        "measured_return_count": len(measured_dates),
        "rebalance_resolution": "last_observed_row_in_resample_bucket",
        "resolved_rebalance_dates": tuple(rebalance_dates),
        "backtest_source_provenance_policy": _SOURCE_PROVENANCE_POLICY,
        "backtest_source_provenance_status": (
            "validated_with_tracked_complex_recovery"
            if provenance_recovery_applied
            else "validated_without_recovery"
        ),
        "signal_value_failure_policy": (
            "validate_bounded_scores_after_exact_slice_raise_on_invalid_available_score"
        ),
        "target_freeze_policy": "decision_information_only_no_execution_close_rerank",
        "target_input_scope": "final_masked_signal_matrix_only",
        "incoming_price_failure_policy": (
            "raise_before_asset_return_on_invalid_held_endpoint"
        ),
        "execution_price_failure_policy": (
            "raise_execution_price_invalid_without_redistribution"
        ),
        "gross_insolvency_failure_policy": (
            "raise_before_pretrade_division_or_costs"
        ),
        "insolvency_failure_policy": (
            "raise_before_successful_result_on_invalid_or_insolvent_capital"
        ),
        "equity_curve_failure_policy": "reject_invalid_equity_before_metrics",
        "returns_failure_policy": "reject_invalid_returns_before_basic_metrics",
        "terminal_row_policy": (
            "include_return_trade_cost_open_holdings_no_future_return"
        ),
        "benchmark_return_window": "same_measured_rows_cost_free_close_to_close",
        "initialization_anchor_policy": (
            "zero_return_trade_turnover_cost_and_holdings"
        ),
        "missing_price_policy_classification": (
            "formal_raise"
            if missing_price_policy == "raise"
            else "diagnostic_zero_return_not_promotion_evidence"
        ),
        "benchmark_missing_policy_classification": (
            "formal_raise"
            if benchmark_missing_policy == "raise"
            else "diagnostic_zero_return_no_formal_relative_metrics"
        ),
    }


def _build_timing_ledger(
    *,
    accounting_dates: pd.DatetimeIndex,
    rebalance_dates: pd.DatetimeIndex,
    target_weights: pd.DataFrame,
    signal_lag_periods: int,
) -> tuple[TimingLedgerRow, ...]:
    ledger_dates = pd.DatetimeIndex(
        [accounting_dates[0], *rebalance_dates.to_list()]
    ).unique().sort_values()
    scheduled_dates = set(rebalance_dates)
    rows: list[TimingLedgerRow] = []

    for date in ledger_dates:
        position = int(accounting_dates.get_loc(date))
        is_scheduled = date in scheduled_dates
        is_anchor = position == 0
        insufficient_lag = is_scheduled and position < signal_lag_periods
        if is_anchor:
            status = "initialization_anchor_no_execution"
        elif insufficient_lag:
            status = "insufficient_lag_no_execution"
        else:
            target = target_weights.loc[date]
            status = (
                "executed_invested_target"
                if float(target.fillna(0.0).sum()) > 0.0
                else "executed_cash_target"
            )

        executed = status in {
            "executed_invested_target",
            "executed_cash_target",
        }
        source_date = (
            accounting_dates[position - signal_lag_periods] if executed else None
        )
        incoming_start = accounting_dates[position - 1] if position > 0 else None
        incoming_end = date if position > 0 else None
        first_holding_start = date if executed else None
        first_holding_end = (
            accounting_dates[position + 1]
            if executed and position + 1 < len(accounting_dates)
            else None
        )
        rows.append(
            TimingLedgerRow(
                ledger_date=date,
                scheduled_execution_date=date if is_scheduled else None,
                is_scheduled_rebalance=is_scheduled,
                event_status=status,
                signal_source_date=source_date,
                feature_observation_end=source_date,
                signal_availability_phase=(
                    _LEDGER_PHASE_SIGNAL_AVAILABILITY if executed else None
                ),
                decision_phase=_LEDGER_PHASE_DECISION if executed else None,
                execution_phase=_LEDGER_PHASE_EXECUTION if executed else None,
                incoming_return_start=incoming_start,
                incoming_return_end=incoming_end,
                first_holding_return_start=first_holding_start,
                first_holding_return_end=first_holding_end,
                is_terminal_scheduled_row=(
                    is_scheduled and position == len(accounting_dates) - 1
                ),
            )
        )
    return tuple(rows)


def _validate_backtest_inputs(
    *,
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    evaluation_start: pd.Timestamp,
    evaluation_end: pd.Timestamp,
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
    signal_lag_value = _read_exact_integral_scalar(signal_lag_periods)
    if signal_lag_value is None or signal_lag_value < 1:
        raise BacktestValidationError(
            "signal_lag_invalid",
            "signal_lag_periods must be a non-boolean integer of at least one",
        )
    _validate_initial_capital(initial_capital)

    if not isinstance(prices, pd.DataFrame):
        raise BacktestValidationError(
            "source_axes_invalid",
            "prices must be a pandas DataFrame",
        )
    if not isinstance(signals, pd.DataFrame):
        raise BacktestValidationError(
            "source_axes_invalid",
            "signals must be a pandas DataFrame",
        )
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise BacktestValidationError(
            "source_axes_invalid",
            "prices must use a DatetimeIndex",
        )
    if not isinstance(signals.index, pd.DatetimeIndex):
        raise BacktestValidationError(
            "source_axes_invalid",
            "signals must use a DatetimeIndex",
        )
    if prices.empty:
        raise BacktestValidationError(
            "source_axes_invalid",
            "prices and signals must contain dates and assets",
        )
    if (
        prices.index.has_duplicates
        or signals.index.has_duplicates
        or prices.columns.has_duplicates
        or signals.columns.has_duplicates
    ):
        raise BacktestValidationError(
            "source_axes_invalid",
            "source dates and asset identifiers must be unique",
        )
    if (
        not prices.index.is_monotonic_increasing
        or not signals.index.is_monotonic_increasing
    ):
        raise BacktestValidationError(
            "source_axes_invalid",
            "source dates must be strictly increasing",
        )
    if prices.index.tz != signals.index.tz:
        raise BacktestValidationError(
            "source_axes_invalid",
            "price and signal indexes must use the same timezone",
        )
    if not prices.index.equals(signals.index):
        raise BacktestValidationError(
            "source_axes_invalid",
            "price and signal dates must match exactly in order",
        )
    if not prices.columns.equals(signals.columns):
        raise BacktestValidationError(
            "source_axes_invalid",
            "price and signal asset columns must match exactly in order",
        )

    _resolve_accounting_window(
        prices.index,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
    )

    if top_n is None and top_pct is None:
        raise ValueError("either top_n or top_pct must be provided")
    if top_n is not None and top_pct is not None:
        raise ValueError("provide only one of top_n or top_pct")
    if top_n is not None:
        top_n_value = _read_exact_integral_scalar(top_n)
        if top_n_value is None or top_n_value <= 0:
            raise ValueError("top_n must be positive")
    if top_pct is not None:
        top_pct_value = _read_finite_real_scalar(top_pct)
        if top_pct_value is None or not 0.0 < top_pct_value <= 1.0:
            raise ValueError("top_pct must be greater than 0 and no more than 1")
    transaction_cost_value = _read_finite_real_scalar(transaction_cost_bps)
    if transaction_cost_value is None or transaction_cost_value < 0.0:
        raise ValueError("transaction_cost_bps must be non-negative")
    slippage_value = _read_finite_real_scalar(slippage_bps)
    if slippage_value is None or slippage_value < 0.0:
        raise ValueError("slippage_bps must be non-negative")
    if volume_aware_slippage_mode not in _VOLUME_AWARE_SLIPPAGE_MODES:
        raise ValueError(
            "volume_aware_slippage_mode must be 'diagnostic_only' or "
            "'apply_precomputed_impact'"
        )
    if missing_price_policy not in {"raise", "zero_return"}:
        raise ValueError("missing_price_policy must be 'raise' or 'zero_return'")
    if benchmark_missing_policy not in {"raise", "zero_return"}:
        raise ValueError("benchmark_missing_policy must be 'raise' or 'zero_return'")
    periods_per_year_value = _read_exact_integral_scalar(periods_per_year)
    if periods_per_year_value != 252:
        raise BacktestValidationError(
            "periods_per_year_invalid",
            "daily close-to-close accounting requires integer periods_per_year=252",
        )


def _validate_initial_capital(initial_capital: object) -> None:
    numeric = _read_finite_real_scalar(initial_capital)
    if numeric is None or numeric <= 0.0:
        raise BacktestValidationError(
            "initial_capital_invalid",
            "initial_capital must be a finite positive real non-boolean scalar",
        )


def _is_finite_real_scalar(value: object) -> bool:
    return _read_finite_real_scalar(value) is not None


def _read_finite_real_scalar(value: object) -> float | None:
    if type(value) not in _EXACT_REAL_SCALAR_TYPES:
        return None
    try:
        numeric = float(value)
    except (OverflowError, TypeError, ValueError):
        return None
    return numeric if np.isfinite(numeric) else None


def _read_exact_integral_scalar(value: object) -> int | None:
    if type(value) not in _EXACT_INTEGER_SCALAR_TYPES:
        return None
    return int(value)


def _capture_source_frame_provenance(
    source: pd.DataFrame,
    *,
    role: Literal["prices", "signals"],
) -> SourceFrameProvenance:
    axis_fingerprint = _source_axis_fingerprint(source)
    dtype_names = tuple(str(dtype) for dtype in source.dtypes)
    dtype_families = tuple(_source_dtype_family(dtype) for dtype in source.dtypes)
    cells = _snapshot_source_cells(source)
    _reject_unsupported_source_cells(cells)
    state_digest = _snapshot_state_digest(
        role=role,
        axis_fingerprint=axis_fingerprint,
        dtype_names=dtype_names,
        cells=cells,
    )
    return SourceFrameProvenance(
        schema_version=_SOURCE_PROVENANCE_POLICY,
        role=role,
        axis_fingerprint=axis_fingerprint,
        original_dtype_names=dtype_names,
        original_dtype_families=dtype_families,
        original_cells=cells,
        original_state_digest=state_digest,
        current_state_digest=state_digest,
        mutations=(),
        _source_identity=id(source),
        _lineage_token=_SourceLineageToken(),
    )


def _validate_backtest_source_provenance(
    *,
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    source_provenance: BacktestSourceProvenance,
) -> tuple[SourceFrameProvenance, SourceFrameProvenance]:
    if (
        not isinstance(source_provenance, BacktestSourceProvenance)
        or source_provenance.schema_version != _SOURCE_PROVENANCE_POLICY
    ):
        raise BacktestValidationError(
            "source_provenance_invalid",
            "a current library-issued backtest source provenance handle is required",
        )
    _validate_source_frame_provenance(
        source=prices,
        provenance=source_provenance.prices,
        expected_role="prices",
    )
    _validate_source_frame_provenance(
        source=signals,
        provenance=source_provenance.signals,
        expected_role="signals",
    )
    return source_provenance.prices, source_provenance.signals


def _validate_source_frame_provenance(
    *,
    source: pd.DataFrame,
    provenance: SourceFrameProvenance,
    expected_role: Literal["prices", "signals"],
) -> None:
    if (
        not isinstance(provenance, SourceFrameProvenance)
        or provenance.schema_version != _SOURCE_PROVENANCE_POLICY
        or provenance.role != expected_role
        or type(provenance._lineage_token) is not _SourceLineageToken
        or provenance._source_identity != id(source)
    ):
        raise BacktestValidationError(
            "source_provenance_invalid",
            "source provenance is stale, copied, malformed, or bound to another role",
        )

    axis_fingerprint = _source_axis_fingerprint(source)
    if provenance.axis_fingerprint != axis_fingerprint:
        raise BacktestValidationError(
            "source_provenance_invalid",
            "source axes no longer match the captured provenance",
        )
    row_count = len(source.index)
    column_count = len(source.columns)
    if (
        len(provenance.original_dtype_names) != column_count
        or len(provenance.original_dtype_families) != column_count
        or len(provenance.original_cells) != row_count
        or any(len(row) != column_count for row in provenance.original_cells)
    ):
        raise BacktestValidationError(
            "source_provenance_invalid",
            "source provenance shape does not match the runtime source",
        )

    expected_original_digest = _snapshot_state_digest(
        role=expected_role,
        axis_fingerprint=provenance.axis_fingerprint,
        dtype_names=provenance.original_dtype_names,
        cells=provenance.original_cells,
    )
    if expected_original_digest != provenance.original_state_digest:
        raise BacktestValidationError(
            "source_provenance_invalid",
            "source provenance lineage is internally inconsistent",
        )

    previous_digest = provenance.original_state_digest
    for sequence, record in enumerate(provenance.mutations):
        if (
            not isinstance(record, SourceMutationRecord)
            or record.sequence != sequence
            or record.before_state_digest != previous_digest
            or record.row_position < 0
            or record.row_position >= row_count
            or record.column_position < 0
            or record.column_position >= column_count
            or record.record_digest
            != _mutation_record_digest(
                lineage_digest=provenance.original_state_digest,
                sequence=record.sequence,
                row_position=record.row_position,
                column_position=record.column_position,
                assigned_value=record.assigned_value,
                before_state_digest=record.before_state_digest,
                after_state_digest=record.after_state_digest,
            )
        ):
            raise BacktestValidationError(
                "source_provenance_invalid",
                "source mutation ledger is malformed or replay-inconsistent",
            )
        previous_digest = record.after_state_digest
    if (
        previous_digest != provenance.current_state_digest
        or _source_state_digest(source, role=expected_role)
        != provenance.current_state_digest
    ):
        raise BacktestValidationError(
            "source_provenance_invalid",
            "runtime source state does not match the controlled mutation ledger",
        )


def _source_axis_fingerprint(source: pd.DataFrame) -> tuple[object, ...]:
    return (
        "source_axis_v1",
        _qualified_type_name(source.index),
        tuple(_typed_value_token(name) for name in source.index.names),
        tuple(_typed_value_token(label) for label in source.index),
        _qualified_type_name(source.columns),
        tuple(_typed_value_token(name) for name in source.columns.names),
        tuple(_typed_value_token(label) for label in source.columns),
    )


def _typed_value_token(value: object) -> str:
    return f"{_qualified_type_name(value)}:{value!r}"


def _qualified_type_name(value: object) -> str:
    value_type = type(value)
    return f"{value_type.__module__}.{value_type.__qualname__}"


def _source_dtype_family(dtype: object) -> str:
    if pd.api.types.is_complex_dtype(dtype):
        return "complex"
    if pd.api.types.is_bool_dtype(dtype):
        return "boolean"
    if pd.api.types.is_numeric_dtype(dtype):
        return "real_numeric"
    if pd.api.types.is_object_dtype(dtype):
        return "object"
    return "other"


def _snapshot_source_cells(
    source: pd.DataFrame,
) -> tuple[tuple[SourceCellSnapshot, ...], ...]:
    if len(source.columns) == 0:
        return tuple(() for _ in range(len(source.index)))
    return tuple(
        tuple(_snapshot_source_cell(value) for value in row)
        for row in zip(
            *(source.iloc[:, column].array for column in range(len(source.columns))),
            strict=True,
        )
    )


def _snapshot_source_cell(value: object) -> SourceCellSnapshot:
    value_type = type(value)
    if value_type in _EXACT_BOOLEAN_SCALAR_TYPES:
        return SourceCellSnapshot("boolean", ("true" if bool(value) else "false",))
    if value_type in _EXACT_SOURCE_COMPLEX_SCALAR_TYPES:
        return SourceCellSnapshot(
            "complex",
            (
                _float_semantic_token(float(np.real(value))),
                _float_semantic_token(float(np.imag(value))),
            ),
        )
    if value_type in _EXACT_INTEGER_SCALAR_TYPES:
        return SourceCellSnapshot("integer", (str(int(value)),))
    if value_type in _SOURCE_NUMPY_FLOAT_SCALAR_TYPES or value_type is float:
        numeric = float(value)
        if np.isnan(numeric):
            return SourceCellSnapshot("ieee_nan", ())
        return SourceCellSnapshot("real_float", (_float_semantic_token(numeric),))
    if value_type is Fraction:
        return SourceCellSnapshot(
            "fraction",
            (str(value.numerator), str(value.denominator)),
        )
    if isinstance(value, complex | Integral | Real | np.number):
        return SourceCellSnapshot(
            "unsupported_numeric",
            (_qualified_type_name(value),),
        )
    if value is None or value is pd.NA or value is pd.NaT:
        return SourceCellSnapshot("missing_other", (_qualified_type_name(value),))
    return SourceCellSnapshot(
        "other",
        (_qualified_type_name(value), repr(value)),
    )


def _float_semantic_token(value: float) -> str:
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0.0 else "-inf"
    return value.hex()


def _snapshot_state_digest(
    *,
    role: str,
    axis_fingerprint: tuple[object, ...],
    dtype_names: tuple[str, ...],
    cells: tuple[tuple[SourceCellSnapshot, ...], ...],
) -> str:
    payload = (
        _SOURCE_PROVENANCE_POLICY,
        role,
        axis_fingerprint,
        dtype_names,
        cells,
    )
    return hashlib.sha256(
        repr(payload).encode("utf-8", errors="backslashreplace"),
    ).hexdigest()


def _source_state_digest(
    source: pd.DataFrame,
    *,
    role: Literal["prices", "signals"],
) -> str:
    cells = _snapshot_source_cells(source)
    _reject_unsupported_source_cells(cells)
    return _snapshot_state_digest(
        role=role,
        axis_fingerprint=_source_axis_fingerprint(source),
        dtype_names=tuple(str(dtype) for dtype in source.dtypes),
        cells=cells,
    )


def _reject_unsupported_source_cells(
    cells: tuple[tuple[SourceCellSnapshot, ...], ...],
) -> None:
    if any(
        cell.kind == "unsupported_numeric"
        for row in cells
        for cell in row
    ):
        raise BacktestValidationError(
            "source_provenance_invalid",
            "custom numeric source cells are not supported",
        )


def _mutation_record_digest(
    *,
    lineage_digest: str,
    sequence: int,
    row_position: int,
    column_position: int,
    assigned_value: SourceCellSnapshot,
    before_state_digest: str,
    after_state_digest: str,
) -> str:
    payload = (
        _SOURCE_PROVENANCE_POLICY,
        lineage_digest,
        sequence,
        row_position,
        column_position,
        assigned_value,
        before_state_digest,
        after_state_digest,
    )
    return hashlib.sha256(
        repr(payload).encode("utf-8", errors="backslashreplace"),
    ).hexdigest()


def _resolve_accounting_window(
    price_index: pd.DatetimeIndex,
    *,
    evaluation_start: pd.Timestamp,
    evaluation_end: pd.Timestamp,
) -> tuple[int, int, pd.DatetimeIndex]:
    if type(evaluation_start) is not pd.Timestamp or type(
        evaluation_end
    ) is not pd.Timestamp:
        raise BacktestValidationError(
            "evaluation_bounds_invalid",
            "evaluation bounds must be exact scalar pandas Timestamps",
        )
    if pd.isna(evaluation_start) or pd.isna(evaluation_end):
        raise BacktestValidationError(
            "evaluation_bounds_invalid",
            "evaluation bounds must not be missing",
        )
    if (
        evaluation_start.tz != price_index.tz
        or evaluation_end.tz != price_index.tz
    ):
        raise BacktestValidationError(
            "evaluation_bounds_invalid",
            "evaluation bounds must exactly match the source timezone",
        )
    try:
        start_pos = price_index.get_loc(evaluation_start)
        end_pos = price_index.get_loc(evaluation_end)
    except KeyError as exc:
        raise BacktestValidationError(
            "evaluation_bounds_invalid",
            "evaluation bounds must be exact source-index members",
        ) from exc
    if (
        not isinstance(start_pos, Integral)
        or isinstance(start_pos, bool | np.bool_)
        or not isinstance(end_pos, Integral)
        or isinstance(end_pos, bool | np.bool_)
        or start_pos >= end_pos
    ):
        raise BacktestValidationError(
            "evaluation_bounds_invalid",
            "evaluation bounds must resolve to increasing scalar positions",
        )
    accounting_dates = price_index[int(start_pos) : int(end_pos) + 1]
    return int(start_pos), int(end_pos), accounting_dates


def _extract_bounded_source_values(
    source: pd.DataFrame,
    *,
    provenance: SourceFrameProvenance,
    start_pos: int,
    end_pos: int,
) -> tuple[pd.DataFrame, tuple[int, ...]]:
    """Extract bounded cells using only mutation-time provenance.

    A real column promoted by a tracked complex write outside the accounting
    window may recover bounded real semantics losslessly, including when a
    later outside non-real write promotes the current column to object. Native
    complex inputs, latest bounded complex writes, stale handles, and arbitrary
    pandas writes never receive that recovery.
    """

    bounded_index = source.index[start_pos : end_pos + 1]
    extracted_columns: list[pd.Series] = []
    recovered_column_positions: list[int] = []
    for column_position, asset in enumerate(source.columns):
        bounded_column = source.iloc[start_pos : end_pos + 1, column_position]
        outside_complex_write = any(
            record.column_position == column_position
            and record.assigned_value.kind == "complex"
            and (
                record.row_position < start_pos
                or record.row_position > end_pos
            )
            for record in provenance.mutations
        )
        latest_bounded_assignments: dict[int, SourceCellSnapshot] = {
            record.row_position: record.assigned_value
            for record in provenance.mutations
            if record.column_position == column_position
            and start_pos <= record.row_position <= end_pos
        }
        current_dtype = source.dtypes.iloc[column_position]
        recover_tracked_upcast = (
            (
                pd.api.types.is_complex_dtype(current_dtype)
                or pd.api.types.is_object_dtype(current_dtype)
            )
            and provenance.original_dtype_families[column_position]
            == "real_numeric"
            and outside_complex_write
        )
        if recover_tracked_upcast:
            recovered: list[object] = []
            contains_nonreal = False
            recovered_any = False
            for offset, value in enumerate(bounded_column.tolist()):
                source_row_position = start_pos + offset
                expected = latest_bounded_assignments.get(
                    source_row_position,
                    provenance.original_cells[source_row_position][
                        column_position
                    ],
                )
                if expected.kind == "complex":
                    recovered.append(value)
                    contains_nonreal = True
                    continue
                recovered_value = _losslessly_recover_expected_real(
                    value,
                    expected=expected,
                )
                if recovered_value is not None:
                    recovered.append(recovered_value)
                    recovered_any = True
                else:
                    recovered.append(value)
                    contains_nonreal = True
            extracted = pd.Series(
                recovered,
                index=bounded_index,
                dtype=object if contains_nonreal else float,
                name=asset,
            )
            if recovered_any:
                recovered_column_positions.append(column_position)
        elif pd.api.types.is_object_dtype(source.dtypes.iloc[column_position]):
            extracted = pd.Series(
                bounded_column.tolist(),
                index=bounded_index,
                dtype=object,
                name=asset,
            )
        else:
            extracted = bounded_column.copy()
            extracted.name = asset
        extracted_columns.append(extracted)

    extracted_frame = pd.concat(extracted_columns, axis=1)
    extracted_frame.columns = source.columns.copy()
    return extracted_frame, tuple(recovered_column_positions)


def _losslessly_recover_expected_real(
    value: object,
    *,
    expected: SourceCellSnapshot,
) -> float | None:
    if not isinstance(value, complex | np.complexfloating):
        return None
    real_value = float(np.real(value))
    imaginary_value = float(np.imag(value))
    if not imaginary_value == 0.0:
        return None
    if expected.kind == "ieee_nan":
        return float("nan") if math.isnan(real_value) else None
    if expected.kind == "integer":
        if not math.isfinite(real_value) or not real_value.is_integer():
            return None
        expected_integer = int(expected.payload[0])
        if int(real_value) != expected_integer:
            return None
        return real_value
    if expected.kind == "real_float":
        if _float_semantic_token(real_value) != expected.payload[0]:
            return None
        return real_value
    return None


def _validate_bounded_signal_values(
    bounded_signals: pd.DataFrame,
) -> pd.DataFrame:
    clean = pd.DataFrame(
        np.nan,
        index=bounded_signals.index,
        columns=bounded_signals.columns,
        dtype=float,
    )
    for row_position, date in enumerate(bounded_signals.index):
        for column_position, asset in enumerate(bounded_signals.columns):
            value = bounded_signals.iat[row_position, column_position]
            if isinstance(value, float | np.floating) and np.isnan(value):
                continue
            if not _is_finite_real_scalar(value):
                raise BacktestValidationError(
                    "signal_value_invalid",
                    "bounded scores must be finite real values or IEEE NaN",
                    date=date,
                    asset=asset,
                )
            clean.iat[row_position, column_position] = float(value)
    return clean


def _prepare_volume_aware_slippage_input(
    *,
    accounting_dates: pd.DatetimeIndex,
    mode: str,
    impact: pd.Series | None,
    metadata: Mapping[str, Any] | None,
    fixed_slippage_bps: float,
) -> tuple[pd.Series, str | None]:
    zero_costs = pd.Series(
        0.0,
        index=accounting_dates,
        name="volume_aware_slippage_impact",
    )

    if mode == "diagnostic_only":
        if impact is not None:
            _validate_precomputed_volume_aware_slippage_impact(
                impact=impact,
                accounting_dates=accounting_dates,
            )
        return zero_costs, None

    if impact is None:
        raise ValueError(
            "volume_aware_slippage_impact is required when "
            "volume_aware_slippage_mode='apply_precomputed_impact'"
        )

    _validate_volume_aware_slippage_metadata(metadata)
    costs = _validate_precomputed_volume_aware_slippage_impact(
        impact=impact,
        accounting_dates=accounting_dates,
    )

    return_impact_basis = metadata["return_impact_basis"]

    if fixed_slippage_bps > 0.0 and costs.gt(0.0).any():
        raise ValueError(
            "positive slippage_bps cannot be combined with positive "
            "volume_aware_slippage_impact without a reviewed combined-model policy"
        )

    return costs, return_impact_basis


def _validate_precomputed_volume_aware_slippage_impact(
    *,
    impact: pd.Series,
    accounting_dates: pd.DatetimeIndex,
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
    if impact.index.tz != accounting_dates.tz or not impact.index.equals(
        accounting_dates
    ):
        raise ValueError(
            "volume_aware_slippage_impact index must exactly match accounting dates"
        )

    if impact.isna().any():
        first_missing_date = impact[impact.isna()].index[0]
        raise ValueError(
            "volume_aware_slippage_impact must not contain missing values; "
            f"first missing date is {first_missing_date.date()}"
        )
    if any(not _is_finite_real_scalar(value) for value in impact.to_numpy(dtype=object)):
        raise TypeError(
            "volume_aware_slippage_impact must contain finite real non-boolean values"
        )
    costs = impact.astype(float)

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
