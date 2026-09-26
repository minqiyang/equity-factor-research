"""Frozen Family A definitions for the M4.7 S&P 500 PIT rerun (plan section 6.2).

Six price-only edge-thesis factors. Each value at signal row ``t`` uses only
rows on or before ``t`` (R1), missing anchors stay missing (R6), and the
signal is the factor masked by ``S_mask`` (plan section 2.5).
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, TypeVar

import pandas as pd

from features.liquidity import calculate_amihud_illiquidity
from features.momentum import calculate_12_1_momentum, calculate_52_week_high_proximity
from features.reversal import calculate_short_term_reversal
from features.volatility import calculate_realized_volatility, calculate_rolling_market_beta


@dataclass(frozen=True)
class FamilyAFactor:
    factor_id: str
    parameters: Mapping[str, Any]
    warmup_rows: int
    direction: str = "higher_is_better"


FAMILY_A: tuple[FamilyAFactor, ...] = (
    FamilyAFactor("MOM_12_1", MappingProxyType({"lookback_periods": 252, "skip_periods": 21}), 252),
    FamilyAFactor("HIGH_52W", MappingProxyType({"window": 252}), 251),
    FamilyAFactor("REV_1M", MappingProxyType({"lookback_periods": 21}), 21),
    FamilyAFactor("LOW_VOL_252", MappingProxyType({"window_periods": 252, "ddof": 1}), 252),
    FamilyAFactor("LOW_BETA_252", MappingProxyType({"window": 252}), 252),
    FamilyAFactor("AMIHUD_ILLIQ_63", MappingProxyType({"window": 63}), 63),
)
FAMILY_A_IDS = tuple(factor.factor_id for factor in FAMILY_A)
FAMILY_A_SIZE = len(FAMILY_A)


PanelT = TypeVar("PanelT", pd.DataFrame, pd.Series)


def simple_returns(prices: PanelT) -> PanelT:
    """One-row simple returns; missing when either close is missing or non-positive."""
    previous = prices.shift(1)
    return (prices / previous - 1.0).where(prices.gt(0.0) & previous.gt(0.0))


def family_a_signals(
    adjusted_close: pd.DataFrame,
    market_adjusted_close: pd.Series,
    dollar_volume: pd.DataFrame,
    s_mask: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Compute every Family A factor on unmasked panels, then mask with ``S_mask``.

    ``LOW_VOL_252`` and ``LOW_BETA_252`` are negated so every factor reads
    higher is better. ``LOW_BETA_252`` uses ``ddof=1`` against the market
    series (``SPY.US#E1`` in the rerun).
    """
    if not s_mask.index.equals(adjusted_close.index) or not s_mask.columns.equals(adjusted_close.columns):
        raise ValueError("s_mask must share the adjusted_close index and columns")
    p = {factor.factor_id: dict(factor.parameters) for factor in FAMILY_A}
    returns = simple_returns(adjusted_close)
    market_returns = simple_returns(market_adjusted_close)
    raw = {
        "MOM_12_1": calculate_12_1_momentum(adjusted_close, **p["MOM_12_1"]),
        "HIGH_52W": calculate_52_week_high_proximity(adjusted_close, **p["HIGH_52W"]),
        "REV_1M": calculate_short_term_reversal(adjusted_close, **p["REV_1M"]),
        "LOW_VOL_252": -calculate_realized_volatility(adjusted_close, **p["LOW_VOL_252"]),
        "LOW_BETA_252": -calculate_rolling_market_beta(returns, market_returns, **p["LOW_BETA_252"]),
        "AMIHUD_ILLIQ_63": calculate_amihud_illiquidity(returns, dollar_volume, **p["AMIHUD_ILLIQ_63"]),
    }
    eligible = s_mask.astype(bool)
    return {factor_id: raw[factor_id].where(eligible) for factor_id in FAMILY_A_IDS}
