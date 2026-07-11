"""Backtest metric calculations for simulated research output."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype


_GROSS_EXPOSURE_TOLERANCE = 1e-12


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
    holdings: pd.DataFrame | None = None,
    turnover: pd.Series | None = None,
    transaction_costs: pd.Series | None = None,
    slippage_costs: pd.Series | None = None,
    volume_aware_slippage_costs: pd.Series | None = None,
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

    return metrics


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
        "average_position_concentration_hhi": float(concentration_hhi.mean()),
        "max_position_concentration_hhi": float(concentration_hhi.max()),
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
        or not is_numeric_dtype(holdings[column].dtype)
    ]
    if invalid_columns:
        raise TypeError(
            "holdings must contain numeric, non-boolean columns; "
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
