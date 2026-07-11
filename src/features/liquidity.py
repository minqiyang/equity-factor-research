"""Synthetic-first liquidity eligibility helpers.

This module creates date-asset eligibility masks from already-validated local
or synthetic panels. It does not fetch data, select a portfolio, run a
backtest, connect to brokerage or execution systems, or make profitability
claims.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype

from features.operators import validate_panel_data


@dataclass(frozen=True)
class LiquidityUniverseResult:
    """Liquidity universe mask plus audit metadata.

    The result is a research infrastructure artifact only. It does not contain
    target weights, trades, returns, benchmark comparisons, or performance
    interpretation.
    """

    name: str
    universe_mask: pd.DataFrame
    summary: pd.DataFrame
    parameters: dict[str, object]
    caveats: tuple[str, ...]
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    asset_count: int
    low_coverage_dates: tuple[pd.Timestamp, ...]


@dataclass(frozen=True)
class UniverseMaskedSignalsResult:
    """Universe-masked signal panel plus audit metadata.

    The result is a research infrastructure artifact only. It does not contain
    target weights, trades, returns, benchmark comparisons, or performance
    interpretation.
    """

    name: str
    signals: pd.DataFrame
    summary: pd.DataFrame
    parameters: dict[str, object]
    caveats: tuple[str, ...]
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    asset_count: int
    low_coverage_dates: tuple[pd.Timestamp, ...]


def rolling_average_daily_volume(
    volume: pd.DataFrame,
    *,
    window: int,
) -> pd.DataFrame:
    """Calculate trailing average daily volume with full windows only.

    Missing values are not filled. A window containing any missing volume value
    produces ``NaN`` for that asset/date.
    """

    _validate_positive_integer(window, "window")
    volume_panel = _validate_volume_panel(volume)
    return volume_panel.rolling(window=window, min_periods=window).mean()


def rolling_average_dollar_volume(
    price: pd.DataFrame,
    volume: pd.DataFrame,
    *,
    window: int,
) -> pd.DataFrame:
    """Calculate trailing average dollar volume with full windows only."""

    _validate_positive_integer(window, "window")
    price_panel, volume_panel = _validate_price_volume_panels(price, volume)
    dollar_volume = price_panel * volume_panel
    return dollar_volume.rolling(window=window, min_periods=window).mean()


def average_daily_volume_eligibility(
    volume: pd.DataFrame,
    *,
    window: int,
    min_average_volume: float,
    eligibility_lag: int = 1,
    require_positive_volume_window: bool = True,
) -> pd.DataFrame:
    """Return a lagged eligibility mask from rolling average volume.

    The threshold is evaluated on observation date ``t`` and becomes eligible
    only after ``eligibility_lag`` rows. The default lag of one row means
    liquidity observed through date ``t`` can first affect eligibility on date
    ``t+1``. Warm-up periods, missing rolling values, and windows containing
    zero volume are ineligible by default.
    """

    _validate_positive_integer(eligibility_lag, "eligibility_lag")
    _validate_positive_threshold(min_average_volume, "min_average_volume")
    _validate_bool(require_positive_volume_window, "require_positive_volume_window")

    volume_panel = _validate_volume_panel(volume)
    metric = rolling_average_daily_volume(volume_panel, window=window)
    return _lagged_threshold_eligibility(
        metric,
        volume_panel=volume_panel,
        window=window,
        threshold=float(min_average_volume),
        eligibility_lag=eligibility_lag,
        require_positive_volume_window=require_positive_volume_window,
    )


def average_dollar_volume_eligibility(
    price: pd.DataFrame,
    volume: pd.DataFrame,
    *,
    window: int,
    min_average_dollar_volume: float,
    eligibility_lag: int = 1,
    require_positive_volume_window: bool = True,
) -> pd.DataFrame:
    """Return a lagged eligibility mask from rolling average dollar volume."""

    _validate_positive_integer(eligibility_lag, "eligibility_lag")
    _validate_positive_threshold(
        min_average_dollar_volume,
        "min_average_dollar_volume",
    )
    _validate_bool(require_positive_volume_window, "require_positive_volume_window")

    price_panel, volume_panel = _validate_price_volume_panels(price, volume)
    metric = rolling_average_dollar_volume(price_panel, volume_panel, window=window)
    return _lagged_threshold_eligibility(
        metric,
        volume_panel=volume_panel,
        window=window,
        threshold=float(min_average_dollar_volume),
        eligibility_lag=eligibility_lag,
        require_positive_volume_window=require_positive_volume_window,
    )


def construct_liquidity_universe(
    eligibility_mask: pd.DataFrame,
    *,
    ranking_metric: pd.DataFrame | None = None,
    max_assets_per_date: int | None = None,
    min_assets_per_date: int = 1,
    name: str = "liquidity_universe",
) -> LiquidityUniverseResult:
    """Construct a synthetic/local liquidity universe mask and audit summary.

    Missing eligibility values are counted first, then treated as ineligible.
    When ``max_assets_per_date`` is supplied, eligible assets are selected by
    descending ``ranking_metric``; ties retain the input column order. Missing
    ranking values are counted and excluded from capped selection.
    """

    _validate_non_empty_name(name)
    _validate_positive_integer(min_assets_per_date, "min_assets_per_date")
    if max_assets_per_date is not None:
        _validate_positive_integer(max_assets_per_date, "max_assets_per_date")

    eligible_mask, missing_eligibility = _validate_eligibility_mask(
        eligibility_mask,
    )
    ranking_panel = None
    if ranking_metric is not None:
        ranking_panel = _validate_ranking_metric(ranking_metric, eligible_mask)

    universe_mask, missing_ranking_count, capped_count = _apply_universe_cap(
        eligible_mask,
        ranking_metric=ranking_panel,
        max_assets_per_date=max_assets_per_date,
    )

    previous_mask = universe_mask.shift(1, fill_value=False).astype(bool)
    added_count = (universe_mask & ~previous_mask).sum(axis=1).astype(int)
    removed_count = (~universe_mask & previous_mask).sum(axis=1).astype(int)
    universe_count = universe_mask.sum(axis=1).astype(int)
    raw_eligible_count = eligible_mask.sum(axis=1).astype(int)
    low_coverage = universe_count < min_assets_per_date

    summary = pd.DataFrame(
        {
            "raw_eligible_count": raw_eligible_count,
            "universe_count": universe_count,
            "missing_eligibility_count": missing_eligibility.sum(axis=1).astype(int),
            "missing_ranking_count": missing_ranking_count,
            "capped_count": capped_count,
            "added_count": added_count,
            "removed_count": removed_count,
            "low_coverage": low_coverage.astype(bool),
        },
        index=eligible_mask.index,
    )

    parameters: dict[str, object] = {
        "name": name,
        "max_assets_per_date": max_assets_per_date,
        "min_assets_per_date": min_assets_per_date,
        "ranking_metric_supplied": ranking_panel is not None,
        "tie_break": "input_column_order",
    }
    caveats = (
        "synthetic_or_local_panel_only",
        "not_real_data_evidence",
        "not_backtest_or_portfolio_construction",
        "no_trading_or_order_execution",
        "no_profitability_claim",
    )
    low_coverage_dates = tuple(summary.index[summary["low_coverage"]])

    return LiquidityUniverseResult(
        name=name,
        universe_mask=universe_mask,
        summary=summary,
        parameters=parameters,
        caveats=caveats,
        start_date=pd.Timestamp(eligible_mask.index[0]),
        end_date=pd.Timestamp(eligible_mask.index[-1]),
        asset_count=len(eligible_mask.columns),
        low_coverage_dates=low_coverage_dates,
    )


def apply_universe_mask_to_signals(
    signals: pd.DataFrame,
    universe_mask: pd.DataFrame,
    *,
    name: str = "universe_masked_signals",
    min_valid_signals_per_date: int = 1,
) -> UniverseMaskedSignalsResult:
    """Apply an already-constructed universe mask to a signal panel.

    ``True`` universe-mask cells preserve the original signal. ``False`` cells
    become missing values, not zero scores. Existing signal missing values are
    preserved. Inputs must already be strictly aligned; this helper never
    reindexes, forward-fills, backward-fills, or repairs missing universe
    values.
    """

    _validate_non_empty_name(name)
    _validate_positive_integer(
        min_valid_signals_per_date,
        "min_valid_signals_per_date",
    )

    if isinstance(signals, pd.DataFrame):
        _validate_unique_columns(signals, "signals")
    signal_panel = validate_panel_data(signals, name="signals")
    mask_panel = _validate_universe_mask(universe_mask, signal_panel)

    masked_signals = signal_panel.where(mask_panel)

    raw_valid_signal_count = signal_panel.notna().sum(axis=1).astype(int)
    universe_eligible_count = mask_panel.sum(axis=1).astype(int)
    valid_masked_signal_count = masked_signals.notna().sum(axis=1).astype(int)
    missing_signal_count = signal_panel.isna().sum(axis=1).astype(int)
    excluded_by_universe_count = (
        signal_panel.notna() & ~mask_panel
    ).sum(axis=1).astype(int)
    low_coverage = valid_masked_signal_count < min_valid_signals_per_date

    summary = pd.DataFrame(
        {
            "raw_valid_signal_count": raw_valid_signal_count,
            "universe_eligible_count": universe_eligible_count,
            "valid_masked_signal_count": valid_masked_signal_count,
            "excluded_by_universe_count": excluded_by_universe_count,
            "missing_signal_count": missing_signal_count,
            "low_coverage": low_coverage.astype(bool),
        },
        index=signal_panel.index,
    )

    parameters: dict[str, object] = {
        "name": name,
        "min_valid_signals_per_date": min_valid_signals_per_date,
    }
    caveats = (
        "synthetic_or_local_panel_only",
        "not_real_data_evidence",
        "not_backtest_or_portfolio_construction",
        "no_trading_or_order_execution",
        "no_profitability_claim",
    )
    low_coverage_dates = tuple(summary.index[summary["low_coverage"]])

    return UniverseMaskedSignalsResult(
        name=name,
        signals=masked_signals,
        summary=summary,
        parameters=parameters,
        caveats=caveats,
        start_date=pd.Timestamp(signal_panel.index[0]),
        end_date=pd.Timestamp(signal_panel.index[-1]),
        asset_count=len(signal_panel.columns),
        low_coverage_dates=low_coverage_dates,
    )


def _apply_universe_cap(
    eligible_mask: pd.DataFrame,
    *,
    ranking_metric: pd.DataFrame | None,
    max_assets_per_date: int | None,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    missing_ranking_count = pd.Series(0, index=eligible_mask.index, dtype=int)
    capped_count = pd.Series(0, index=eligible_mask.index, dtype=int)

    if max_assets_per_date is None:
        if ranking_metric is not None:
            missing_ranking_count = (
                eligible_mask & ranking_metric.isna()
            ).sum(axis=1).astype(int)
        return eligible_mask.copy(), missing_ranking_count, capped_count

    if ranking_metric is None:
        raise ValueError("ranking_metric is required when max_assets_per_date is set")

    eligible_ranking = ranking_metric.where(eligible_mask)
    missing_ranking_count = (
        eligible_mask & ranking_metric.isna()
    ).sum(axis=1).astype(int)
    ranks = eligible_ranking.rank(
        axis=1,
        method="first",
        ascending=False,
        na_option="keep",
    )
    selected = eligible_mask & ranks.le(max_assets_per_date)
    valid_ranking_count = eligible_ranking.notna().sum(axis=1)
    capped_count = (valid_ranking_count - selected.sum(axis=1)).clip(
        lower=0,
    ).astype(int)

    return selected.astype(bool), missing_ranking_count, capped_count


def _lagged_threshold_eligibility(
    metric: pd.DataFrame,
    *,
    volume_panel: pd.DataFrame,
    window: int,
    threshold: float,
    eligibility_lag: int,
    require_positive_volume_window: bool,
) -> pd.DataFrame:
    eligible_on_observation_date = metric >= threshold
    if require_positive_volume_window:
        eligible_on_observation_date = (
            eligible_on_observation_date
            & _full_positive_volume_window(volume_panel, window=window)
        )

    return eligible_on_observation_date.shift(
        eligibility_lag,
        fill_value=False,
    ).astype(bool)


def _validate_eligibility_mask(
    eligibility_mask: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not isinstance(eligibility_mask, pd.DataFrame):
        raise TypeError("eligibility_mask must be a pandas DataFrame")

    if not isinstance(eligibility_mask.index, pd.DatetimeIndex):
        raise TypeError("eligibility_mask must be indexed by a pandas DatetimeIndex")

    if eligibility_mask.empty:
        raise ValueError("eligibility_mask must not be empty")

    if eligibility_mask.index.has_duplicates:
        raise ValueError("eligibility_mask index must not contain duplicate dates")

    if not eligibility_mask.index.is_monotonic_increasing:
        raise ValueError("eligibility_mask index must be sorted in increasing date order")

    invalid_columns: list[object] = []
    for column in eligibility_mask.columns:
        non_missing = eligibility_mask[column].dropna()
        if not non_missing.map(lambda value: isinstance(value, (bool, np.bool_))).all():
            invalid_columns.append(column)

    if invalid_columns:
        raise TypeError(
            "eligibility_mask must contain boolean values or missing values only; "
            f"invalid columns: {invalid_columns}"
        )

    missing_eligibility = eligibility_mask.isna()
    clean_mask = eligibility_mask.eq(True).fillna(False).astype(bool)
    return clean_mask, missing_eligibility


def _validate_universe_mask(
    universe_mask: pd.DataFrame,
    signals: pd.DataFrame,
) -> pd.DataFrame:
    if not isinstance(universe_mask, pd.DataFrame):
        raise TypeError("universe_mask must be a pandas DataFrame")

    if not isinstance(universe_mask.index, pd.DatetimeIndex):
        raise TypeError("universe_mask must be indexed by a pandas DatetimeIndex")

    if universe_mask.empty:
        raise ValueError("universe_mask must not be empty")

    if universe_mask.index.has_duplicates:
        raise ValueError("universe_mask index must not contain duplicate dates")

    if not universe_mask.index.is_monotonic_increasing:
        raise ValueError("universe_mask index must be sorted in increasing date order")

    _validate_unique_columns(universe_mask, "universe_mask")

    if not universe_mask.index.equals(signals.index):
        raise ValueError("signals and universe_mask must have identical indexes")

    if not universe_mask.columns.equals(signals.columns):
        raise ValueError("signals and universe_mask must have identical columns")

    invalid_columns = [
        column
        for column in universe_mask.columns
        if not is_bool_dtype(universe_mask[column].dtype)
    ]
    if invalid_columns:
        raise TypeError(
            "universe_mask must contain boolean or nullable boolean dtypes only; "
            f"invalid columns: {invalid_columns}"
        )

    if universe_mask.isna().any().any():
        raise ValueError(
            "universe_mask must not contain missing values; construct or audit "
            "the universe mask before applying it to signals"
        )

    return universe_mask.astype(bool)


def _validate_ranking_metric(
    ranking_metric: pd.DataFrame,
    eligibility_mask: pd.DataFrame,
) -> pd.DataFrame:
    ranking_panel = validate_panel_data(ranking_metric, name="ranking_metric")

    if not ranking_panel.index.equals(eligibility_mask.index):
        raise ValueError("ranking_metric and eligibility_mask must have identical indexes")

    if not ranking_panel.columns.equals(eligibility_mask.columns):
        raise ValueError("ranking_metric and eligibility_mask must have identical columns")

    return ranking_panel


def _full_positive_volume_window(volume_panel: pd.DataFrame, *, window: int) -> pd.DataFrame:
    positive_volume = volume_panel > 0.0
    positive_count = positive_volume.rolling(window=window, min_periods=window).sum()
    return positive_count == float(window)


def _validate_price_volume_panels(
    price: pd.DataFrame,
    volume: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    price_panel = validate_panel_data(price, name="price")
    volume_panel = _validate_volume_panel(volume)

    if not price_panel.index.equals(volume_panel.index):
        raise ValueError("price and volume must have identical indexes")

    if not price_panel.columns.equals(volume_panel.columns):
        raise ValueError("price and volume must have identical columns")

    if (price_panel <= 0.0).any().any():
        raise ValueError("price must contain positive values when present")

    return price_panel, volume_panel


def _validate_volume_panel(volume: pd.DataFrame) -> pd.DataFrame:
    volume_panel = validate_panel_data(volume, name="volume")
    if (volume_panel < 0.0).any().any():
        raise ValueError("volume must contain non-negative values when present")
    return volume_panel


def _validate_positive_integer(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")

    if value < 1:
        raise ValueError(f"{name} must be at least 1")


def _validate_positive_threshold(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")

    if not math.isfinite(float(value)) or float(value) <= 0.0:
        raise ValueError(f"{name} must be a positive finite value")


def _validate_bool(value: bool, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a bool")


def _validate_non_empty_name(value: str) -> None:
    if not isinstance(value, str):
        raise TypeError("name must be a string")

    if not value.strip():
        raise ValueError("name must not be empty")


def _validate_unique_columns(data: pd.DataFrame, name: str) -> None:
    if data.columns.has_duplicates:
        raise ValueError(f"{name} columns must not contain duplicates")


__all__ = [
    "LiquidityUniverseResult",
    "UniverseMaskedSignalsResult",
    "apply_universe_mask_to_signals",
    "average_daily_volume_eligibility",
    "average_dollar_volume_eligibility",
    "construct_liquidity_universe",
    "rolling_average_daily_volume",
    "rolling_average_dollar_volume",
]
