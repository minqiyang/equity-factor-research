"""Backtest metric calculations for simulated research output."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_complex_dtype, is_numeric_dtype


_GROSS_EXPOSURE_TOLERANCE = 1e-12
_HOLDINGS_METRIC_DECIMAL_PLACES = 15
_TRACKING_ERROR_FREQUENCY = "daily_close_to_close"
_TRACKING_ERROR_PERIODS_PER_YEAR = 252
_EPISODE_ACCOUNTING_TOLERANCE = 1e-12


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


def calculate_tracking_error(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    *,
    return_frequency: str,
) -> float:
    """Calculate annualized volatility of aligned active daily returns."""

    clean_strategy = _validate_tracking_error_returns(
        strategy_returns,
        "strategy_returns",
    )
    clean_benchmark = _validate_tracking_error_returns(
        benchmark_returns,
        "benchmark_returns",
    )

    if clean_strategy.index.tz != clean_benchmark.index.tz:
        raise ValueError(
            "strategy_returns and benchmark_returns must have matching timezones"
        )
    if not clean_strategy.index.equals(clean_benchmark.index):
        raise ValueError(
            "strategy_returns and benchmark_returns must have identical indexes"
        )
    if return_frequency != _TRACKING_ERROR_FREQUENCY:
        raise ValueError("tracking error supports daily_close_to_close only")
    if clean_benchmark.iloc[0] != 0.0:
        raise ValueError(
            "benchmark_returns first row must be the synthetic zero-return anchor"
        )

    measured_active_returns = (clean_strategy - clean_benchmark).iloc[1:]
    if len(measured_active_returns) < 2:
        raise ValueError("tracking error requires at least 2 measured return periods")

    return float(
        measured_active_returns.std(ddof=0)
        * math.sqrt(_TRACKING_ERROR_PERIODS_PER_YEAR)
    )


def calculate_holding_episode_metrics(
    holdings: pd.DataFrame,
    asset_returns: pd.DataFrame,
    signed_trade_weights: pd.DataFrame,
    trade_weights: pd.DataFrame,
    turnover: pd.Series,
    total_trading_costs: pd.Series,
) -> tuple[dict[str, float], int, int]:
    """Calculate completed holding-episode diagnostics with applied costs."""

    clean_holdings = _validate_holdings_for_metrics(holdings)
    clean_returns = _validate_episode_matrix(asset_returns, "asset_returns")
    clean_signed = _validate_episode_matrix(
        signed_trade_weights,
        "signed_trade_weights",
    )
    clean_trades = _validate_episode_matrix(trade_weights, "trade_weights")
    clean_turnover = _validate_episode_series(turnover, "turnover")
    clean_costs = _validate_episode_series(
        total_trading_costs,
        "total_trading_costs",
    )

    for name, frame in {
        "asset_returns": clean_returns,
        "signed_trade_weights": clean_signed,
        "trade_weights": clean_trades,
    }.items():
        if not frame.index.equals(clean_holdings.index) or not frame.columns.equals(
            clean_holdings.columns
        ):
            raise ValueError(f"{name} axes must exactly match holdings")
    for name, series in {
        "turnover": clean_turnover,
        "total_trading_costs": clean_costs,
    }.items():
        if not series.index.equals(clean_holdings.index):
            raise ValueError(f"{name} index must exactly match holdings")

    if clean_trades.lt(0.0).any().any():
        raise ValueError("trade_weights must be non-negative")
    if clean_turnover.lt(0.0).any():
        raise ValueError("turnover must be non-negative")
    if clean_costs.lt(0.0).any():
        raise ValueError("total_trading_costs must be non-negative")
    if clean_returns.lt(-1.0).any().any():
        raise ValueError("asset_returns must not be below -1")
    if not np.allclose(
        clean_signed.abs().to_numpy(),
        clean_trades.to_numpy(),
        atol=_EPISODE_ACCOUNTING_TOLERANCE,
        rtol=0.0,
    ):
        raise ValueError("absolute signed trades must exactly match trade_weights")
    calculated_turnover = clean_trades.sum(axis=1)
    if not np.allclose(
        calculated_turnover.to_numpy(),
        clean_turnover.to_numpy(),
        atol=_EPISODE_ACCOUNTING_TOLERANCE,
        rtol=0.0,
    ):
        raise ValueError("trade_weights row sums must exactly match turnover")
    zero_turnover_with_cost = clean_turnover.le(_EPISODE_ACCOUNTING_TOLERANCE) & clean_costs.gt(
        _EPISODE_ACCOUNTING_TOLERANCE
    )
    if zero_turnover_with_cost.any():
        raise ValueError("total_trading_costs must be zero when turnover is zero")

    allocation_weights = clean_trades.div(
        clean_turnover.replace(0.0, np.nan),
        axis=0,
    ).fillna(0.0)
    asset_costs = allocation_weights.mul(clean_costs, axis=0)
    if not np.allclose(
        asset_costs.sum(axis=1).to_numpy(),
        clean_costs.to_numpy(),
        atol=_EPISODE_ACCOUNTING_TOLERANCE,
        rtol=0.0,
    ):
        raise ValueError("allocated episode costs must reconcile to total_trading_costs")

    previous_holdings = clean_holdings.shift(1, fill_value=0.0)
    active: dict[object, list[float]] = {}
    completed_returns: list[float] = []

    for date in clean_holdings.index:
        for asset in clean_holdings.columns:
            held_before = previous_holdings.at[date, asset] > 0.0
            held_after = clean_holdings.at[date, asset] > 0.0
            if not held_before and held_after:
                active[asset] = [0.0, 0.0, 0.0]

            episode = active.get(asset)
            if held_before and episode is None:
                raise ValueError("holdings episode state is inconsistent across dates")
            if episode is None:
                if abs(clean_signed.at[date, asset]) > _EPISODE_ACCOUNTING_TOLERANCE:
                    raise ValueError("signed trade has no active holding episode")
                continue

            episode[0] += previous_holdings.at[date, asset] * clean_returns.at[date, asset]
            episode[1] += max(clean_signed.at[date, asset], 0.0)
            episode[2] += asset_costs.at[date, asset]

            if held_before and not held_after:
                if episode[1] <= _EPISODE_ACCOUNTING_TOLERANCE:
                    raise ValueError("completed episode must have positive deployed weight")
                completed_returns.append((episode[0] - episode[2]) / episode[1])
                del active[asset]

    closed_count = len(completed_returns)
    open_count = len(active)
    if not completed_returns:
        return {
            "episode_hit_rate": math.nan,
            "average_holding_period_return": math.nan,
        }, closed_count, open_count

    episode_returns = np.asarray(completed_returns, dtype=float)
    return {
        "episode_hit_rate": float(np.mean(episode_returns > 0.0)),
        "average_holding_period_return": float(episode_returns.mean()),
    }, closed_count, open_count


def calculate_basic_metrics(
    equity_curve: pd.Series,
    returns: pd.Series,
    *,
    holdings: pd.DataFrame | None = None,
    turnover: pd.Series | None = None,
    transaction_costs: pd.Series | None = None,
    slippage_costs: pd.Series | None = None,
    volume_aware_slippage_costs: pd.Series | None = None,
    benchmark_equity_curve: pd.Series | None = None,
    benchmark_returns: pd.Series | None = None,
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
    if benchmark_returns is not None and periods_per_year != 252:
        raise ValueError("tracking error supports daily_close_to_close only")

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

    if holdings is not None:
        if not holdings.index.equals(returns.index):
            raise ValueError("holdings index must exactly match returns index")
        metrics.update(calculate_holdings_state_metrics(holdings))

    if turnover is not None:
        metrics["average_turnover"] = float(turnover.mean())
        metrics["total_turnover"] = float(turnover.sum())

    if transaction_costs is not None:
        metrics["total_transaction_cost_impact"] = float(transaction_costs.sum())

    if slippage_costs is not None:
        metrics["total_slippage_cost_impact"] = float(slippage_costs.sum())

    if volume_aware_slippage_costs is not None:
        metrics["total_volume_aware_slippage_cost_impact"] = float(
            volume_aware_slippage_costs.sum(),
        )

    if (
        transaction_costs is not None
        or slippage_costs is not None
        or volume_aware_slippage_costs is not None
    ):
        transaction_total = 0.0 if transaction_costs is None else float(transaction_costs.sum())
        slippage_total = 0.0 if slippage_costs is None else float(slippage_costs.sum())
        volume_aware_total = (
            0.0
            if volume_aware_slippage_costs is None
            else float(volume_aware_slippage_costs.sum())
        )
        metrics["total_trading_cost_impact"] = (
            transaction_total + slippage_total + volume_aware_total
        )

    if benchmark_equity_curve is not None:
        benchmark_total_return = float(benchmark_equity_curve.iloc[-1] / initial_capital - 1.0)
        metrics["benchmark_total_return"] = benchmark_total_return
        metrics["excess_total_return"] = total_return - benchmark_total_return

    if benchmark_returns is not None:
        metrics["tracking_error"] = calculate_tracking_error(
            returns,
            benchmark_returns,
            return_frequency=_TRACKING_ERROR_FREQUENCY,
        )

    return metrics


def _validate_tracking_error_returns(
    returns: pd.Series,
    name: str,
) -> pd.Series:
    if not isinstance(returns, pd.Series):
        raise TypeError(f"{name} must be a pandas Series")
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise TypeError(f"{name} must be indexed by a pandas DatetimeIndex")
    if returns.empty:
        raise ValueError(f"{name} must not be empty")
    if returns.index.has_duplicates:
        raise ValueError(f"{name} index must not contain duplicate dates")
    if not returns.index.is_monotonic_increasing:
        raise ValueError(f"{name} index must be sorted in increasing date order")
    if (
        is_bool_dtype(returns.dtype)
        or is_complex_dtype(returns.dtype)
        or not is_numeric_dtype(returns.dtype)
    ):
        raise TypeError(f"{name} must contain real numeric, non-boolean values")

    clean_returns = returns.astype(float)
    if clean_returns.isna().any() or not np.isfinite(clean_returns.to_numpy()).all():
        raise ValueError(
            "tracking error does not support missing or non-finite returns"
        )
    return clean_returns


def _validate_episode_matrix(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas DataFrame")
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError(f"{name} must be indexed by a pandas DatetimeIndex")
    if frame.empty:
        raise ValueError(f"{name} must not be empty")
    if (
        frame.index.has_duplicates
        or not frame.index.is_monotonic_increasing
        or frame.columns.has_duplicates
    ):
        raise ValueError(f"{name} must have unique assets and increasing unique dates")
    if any(
        is_bool_dtype(dtype)
        or is_complex_dtype(dtype)
        or not is_numeric_dtype(dtype)
        for dtype in frame.dtypes
    ):
        raise TypeError(f"{name} must contain real numeric, non-boolean values")
    clean = frame.astype(float)
    if not np.isfinite(clean.to_numpy()).all():
        raise ValueError(f"{name} must contain finite values")
    return clean


def _validate_episode_series(series: pd.Series, name: str) -> pd.Series:
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} must be a pandas Series")
    frame = _validate_episode_matrix(series.to_frame(), name)
    return frame.iloc[:, 0]


def calculate_holdings_state_metrics(holdings: pd.DataFrame) -> dict[str, float]:
    """Calculate closing holdings-count and normalized HHI diagnostics.

    All active closing rows are included, including the terminal row. All-zero
    rows are treated as inactive warm-up states and excluded from averages.
    Concentration is normalized by each row's gross exposure so partial-cash
    rows remain comparable with fully invested rows.
    """

    clean_holdings = _validate_holdings_for_metrics(holdings)
    gross_exposure = clean_holdings.sum(axis=1)
    active = gross_exposure.gt(0.0)

    if not active.any():
        return {
            "average_holding_count": math.nan,
            "average_position_concentration_hhi": math.nan,
            "max_position_concentration_hhi": math.nan,
        }

    active_holdings = clean_holdings.loc[active]
    active_gross_exposure = gross_exposure.loc[active]
    holding_count = active_holdings.gt(0.0).sum(axis=1)
    normalized_holdings = active_holdings.div(active_gross_exposure, axis=0)
    concentration_hhi = normalized_holdings.pow(2).sum(axis=1)

    return {
        "average_holding_count": float(holding_count.mean()),
        "average_position_concentration_hhi": round(
            float(concentration_hhi.mean()),
            _HOLDINGS_METRIC_DECIMAL_PLACES,
        ),
        "max_position_concentration_hhi": round(
            float(concentration_hhi.max()),
            _HOLDINGS_METRIC_DECIMAL_PLACES,
        ),
    }


def _validate_holdings_for_metrics(holdings: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(holdings, pd.DataFrame):
        raise TypeError("holdings must be a pandas DataFrame")
    if not isinstance(holdings.index, pd.DatetimeIndex):
        raise TypeError("holdings must be indexed by a pandas DatetimeIndex")
    if holdings.empty:
        raise ValueError("holdings must not be empty")
    if holdings.index.has_duplicates:
        raise ValueError("holdings index must not contain duplicate dates")
    if not holdings.index.is_monotonic_increasing:
        raise ValueError("holdings index must be sorted in increasing date order")
    if holdings.columns.has_duplicates:
        raise ValueError("holdings columns must not contain duplicate assets")

    invalid_columns = [
        column
        for column in holdings.columns
        if is_bool_dtype(holdings[column].dtype)
        or is_complex_dtype(holdings[column].dtype)
        or not is_numeric_dtype(holdings[column].dtype)
    ]
    if invalid_columns:
        raise TypeError(
            "holdings must contain real numeric, non-boolean columns; "
            f"invalid columns: {invalid_columns}"
        )

    clean_holdings = holdings.astype(float)

    if clean_holdings.isna().any().any():
        raise ValueError("holdings must not contain missing values")
    if not np.isfinite(clean_holdings.to_numpy()).all():
        raise ValueError("holdings must contain finite values")
    if clean_holdings.lt(0.0).any().any():
        raise ValueError("holdings must be non-negative")

    gross_exposure = clean_holdings.sum(axis=1)
    leveraged = gross_exposure.gt(1.0 + _GROSS_EXPOSURE_TOLERANCE)
    if leveraged.any():
        first_date = leveraged[leveraged].index[0]
        raise ValueError(
            "holdings gross exposure must not exceed 1.0; "
            f"first leveraged date is {first_date.date()}"
        )

    return clean_holdings
