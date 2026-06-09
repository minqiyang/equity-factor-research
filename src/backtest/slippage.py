"""Synthetic-only slippage diagnostics.

The helpers in this module calculate auditable volume-aware slippage
diagnostics from already-validated synthetic or local panels. They do not run a
backtest, place orders, connect to a broker, fetch data, or make profitability
claims.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd

from features.operators import validate_panel_data


@dataclass(frozen=True)
class VolumeAwareSlippageDiagnostics:
    """Candidate volume-aware slippage diagnostics and audit metadata.

    The result is an input-review artifact only. It is not a filled-order
    model, not a market-impact model, and not a backtest result.
    """

    name: str
    trade_weights: pd.DataFrame
    lagged_rolling_dollar_volume: pd.DataFrame
    trade_notional: pd.DataFrame
    participation: pd.DataFrame
    asset_slippage_bps: pd.DataFrame
    asset_slippage_impact: pd.DataFrame
    portfolio_slippage_impact: pd.Series
    summary: pd.DataFrame
    parameters: dict[str, object]
    caveats: tuple[str, ...]
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    asset_count: int


def calculate_volume_aware_slippage_diagnostics(
    target_weights: pd.DataFrame,
    price: pd.DataFrame,
    volume: pd.DataFrame,
    *,
    window: int,
    portfolio_notional: float,
    base_slippage_bps: float = 0.0,
    participation_slope_bps: float = 0.0,
    volume_lag: int = 1,
    max_participation: float = 1.0,
    name: str = "volume_aware_slippage_diagnostics",
) -> VolumeAwareSlippageDiagnostics:
    """Calculate lagged participation and candidate slippage diagnostics.

    Rolling dollar volume is calculated from ``price * volume`` using full
    trailing windows, then lagged by ``volume_lag`` rows before it is used for a
    rebalance-date trade. Missing, zero, or zero-volume-window liquidity raises
    by default when a non-zero trade weight needs that liquidity. Participation
    above ``max_participation`` also raises by default.
    """

    _validate_non_empty_name(name)
    _validate_positive_integer(window, "window")
    _validate_positive_integer(volume_lag, "volume_lag")
    _validate_positive_finite(portfolio_notional, "portfolio_notional")
    _validate_non_negative_finite(base_slippage_bps, "base_slippage_bps")
    _validate_non_negative_finite(
        participation_slope_bps,
        "participation_slope_bps",
    )
    _validate_positive_finite(max_participation, "max_participation")

    target_panel = _validate_target_weights(target_weights)
    price_panel, volume_panel = _validate_price_volume_panels(price, volume)
    _validate_identical_axes(target_panel, price_panel, "target_weights", "price")

    trade_weights = target_panel.diff().abs()
    trade_weights.iloc[0] = target_panel.iloc[0].abs()
    traded = trade_weights > 0.0

    rolling_dollar_volume = (price_panel * volume_panel).rolling(
        window=window,
        min_periods=window,
    ).mean()
    lagged_rolling_dollar_volume = rolling_dollar_volume.shift(volume_lag)

    positive_volume_window = (
        (volume_panel > 0.0)
        .rolling(window=window, min_periods=window)
        .sum()
        .eq(float(window))
        .shift(volume_lag)
    )

    _raise_for_unusable_liquidity(
        lagged_rolling_dollar_volume=lagged_rolling_dollar_volume,
        positive_volume_window=positive_volume_window,
        traded=traded,
    )

    trade_notional = trade_weights * float(portfolio_notional)
    participation = trade_notional / lagged_rolling_dollar_volume
    participation = participation.where(traded, 0.0)

    over_cap = traded & participation.gt(float(max_participation))
    if over_cap.to_numpy().any():
        first_date, first_asset = _first_true_cell(over_cap)
        raise ValueError(
            "Participation exceeds max_participation for "
            f"{first_asset} on {first_date.date()}; lower portfolio_notional, "
            "raise max_participation only with a reviewed assumption, or "
            "exclude the trade explicitly."
        )

    asset_slippage_bps = (
        float(base_slippage_bps)
        + float(participation_slope_bps) * participation
    ).where(traded, 0.0)
    asset_slippage_impact = (
        trade_weights * asset_slippage_bps / 10_000.0
    ).where(traded, 0.0)
    portfolio_slippage_impact = asset_slippage_impact.sum(axis=1).rename(
        "portfolio_slippage_impact",
    )

    missing_capacity_count = (
        traded & lagged_rolling_dollar_volume.isna()
    ).sum(axis=1).astype(int)
    zero_capacity_count = (
        traded & lagged_rolling_dollar_volume.le(0.0)
    ).sum(axis=1).astype(int)
    zero_volume_window_count = (
        traded & ~positive_volume_window.eq(True)
    ).sum(axis=1).astype(int)

    summary = pd.DataFrame(
        {
            "trade_count": traded.sum(axis=1).astype(int),
            "total_trade_weight": trade_weights.sum(axis=1),
            "total_trade_notional": trade_notional.sum(axis=1),
            "max_participation": participation.max(axis=1),
            "portfolio_slippage_impact": portfolio_slippage_impact,
            "missing_capacity_count": missing_capacity_count,
            "zero_capacity_count": zero_capacity_count,
            "zero_volume_window_count": zero_volume_window_count,
        },
        index=target_panel.index,
    )

    parameters: dict[str, object] = {
        "name": name,
        "window": window,
        "volume_lag": volume_lag,
        "portfolio_notional": float(portfolio_notional),
        "base_slippage_bps": float(base_slippage_bps),
        "participation_slope_bps": float(participation_slope_bps),
        "max_participation": float(max_participation),
        "liquidity_reference": "rolling_dollar_volume_shifted_by_volume_lag",
        "missing_or_zero_liquidity_policy": "raise",
        "participation_above_cap_policy": "raise",
        "slippage_model": "candidate_linear_participation_slippage",
    }
    caveats = (
        "synthetic_or_local_panel_only",
        "not_backtest_integration",
        "not_order_fill_or_market_impact_model",
        "not_real_data_evidence",
        "no_trading_or_order_execution",
        "no_profitability_claim",
    )

    return VolumeAwareSlippageDiagnostics(
        name=name,
        trade_weights=trade_weights,
        lagged_rolling_dollar_volume=lagged_rolling_dollar_volume,
        trade_notional=trade_notional,
        participation=participation,
        asset_slippage_bps=asset_slippage_bps,
        asset_slippage_impact=asset_slippage_impact,
        portfolio_slippage_impact=portfolio_slippage_impact,
        summary=summary,
        parameters=parameters,
        caveats=caveats,
        start_date=pd.Timestamp(target_panel.index[0]),
        end_date=pd.Timestamp(target_panel.index[-1]),
        asset_count=len(target_panel.columns),
    )


def _validate_target_weights(target_weights: pd.DataFrame) -> pd.DataFrame:
    target_panel = validate_panel_data(target_weights, name="target_weights")

    if target_panel.isna().any().any():
        raise ValueError("target_weights must not contain missing values")

    if (target_panel < 0.0).any().any():
        raise ValueError("target_weights must be non-negative")

    row_sums = target_panel.sum(axis=1)
    if row_sums.gt(1.0 + 1e-12).any():
        first_date = row_sums[row_sums.gt(1.0 + 1e-12)].index[0]
        raise ValueError(
            "target_weights row sum exceeds 1.0 on "
            f"{first_date.date()}; leveraged or short portfolios are outside "
            "this diagnostic helper."
        )

    return target_panel


def _validate_price_volume_panels(
    price: pd.DataFrame,
    volume: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    price_panel = validate_panel_data(price, name="price")
    volume_panel = validate_panel_data(volume, name="volume")
    _validate_identical_axes(price_panel, volume_panel, "price", "volume")

    if price_panel.isna().any().any():
        raise ValueError("price must not contain missing values")

    if volume_panel.isna().any().any():
        raise ValueError("volume must not contain missing values")

    if (price_panel <= 0.0).any().any():
        raise ValueError("price must contain positive values")

    if (volume_panel < 0.0).any().any():
        raise ValueError("volume must contain non-negative values")

    return price_panel, volume_panel


def _validate_identical_axes(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_name: str,
    right_name: str,
) -> None:
    if not left.index.equals(right.index):
        raise ValueError(f"{left_name} and {right_name} must have identical indexes")

    if not left.columns.equals(right.columns):
        raise ValueError(f"{left_name} and {right_name} must have identical columns")


def _raise_for_unusable_liquidity(
    *,
    lagged_rolling_dollar_volume: pd.DataFrame,
    positive_volume_window: pd.DataFrame,
    traded: pd.DataFrame,
) -> None:
    missing_capacity = traded & lagged_rolling_dollar_volume.isna()
    if missing_capacity.to_numpy().any():
        first_date, first_asset = _first_true_cell(missing_capacity)
        raise ValueError(
            "Missing lagged rolling dollar volume for traded asset "
            f"{first_asset} on {first_date.date()}; warm-up or missing "
            "liquidity cannot be filled silently."
        )

    zero_or_negative_capacity = traded & lagged_rolling_dollar_volume.le(0.0)
    if zero_or_negative_capacity.to_numpy().any():
        first_date, first_asset = _first_true_cell(zero_or_negative_capacity)
        raise ValueError(
            "Non-positive lagged rolling dollar volume for traded asset "
            f"{first_asset} on {first_date.date()}"
        )

    zero_volume_window = traded & ~positive_volume_window.eq(True)
    if zero_volume_window.to_numpy().any():
        first_date, first_asset = _first_true_cell(zero_volume_window)
        raise ValueError(
            "Zero or incomplete volume window for traded asset "
            f"{first_asset} on {first_date.date()}; zero volume is not valid "
            "liquidity capacity."
        )


def _first_true_cell(mask: pd.DataFrame) -> tuple[pd.Timestamp, object]:
    stacked = mask.stack()
    first_date, first_asset = stacked[stacked].index[0]
    return pd.Timestamp(first_date), first_asset


def _validate_positive_integer(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")

    if value < 1:
        raise ValueError(f"{name} must be at least 1")


def _validate_positive_finite(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")

    if not math.isfinite(float(value)) or float(value) <= 0.0:
        raise ValueError(f"{name} must be a positive finite value")


def _validate_non_negative_finite(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")

    if not math.isfinite(float(value)) or float(value) < 0.0:
        raise ValueError(f"{name} must be a non-negative finite value")


def _validate_non_empty_name(value: str) -> None:
    if not isinstance(value, str):
        raise TypeError("name must be a string")

    if not value.strip():
        raise ValueError("name must not be empty")


__all__ = [
    "VolumeAwareSlippageDiagnostics",
    "calculate_volume_aware_slippage_diagnostics",
]
