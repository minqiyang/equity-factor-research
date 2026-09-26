"""Pure decision-layer functions for the M4.7 S&P 500 PIT rerun (plan sections 6.8 and 6.9).

Stage a-0 delivers the halves split, sign stability, the minimum detectable
effect of an IC series, and the decision gate. The runner (stage b-1) feeds
them realized per-factor values.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.stats import norm

from features.diagnostics import mde_from_long_run_variance, newey_west_long_run_variance
from research.m4_7_family_a import FAMILY_A_SIZE


MIN_IC_MONTHS = 60
MIN_HALF_MONTHS = 24
ADEQUATE_MDE = 0.02
ALPHA = 0.05
POWER = 0.80
ALPHA_EFF = ALPHA / (FAMILY_A_SIZE * sum(1.0 / k for k in range(1, FAMILY_A_SIZE + 1)))
Z_EFF = float(norm.ppf(1.0 - ALPHA_EFF / 2.0) + norm.ppf(POWER))
Z_SINGLE = float(norm.ppf(1.0 - ALPHA / 2.0) + norm.ppf(POWER))


@dataclass(frozen=True)
class FactorGateInput:
    factor_id: str
    status: str
    reject: bool
    mean_ic: float
    sign_stable: bool | None
    net_ls: float | None
    mde: float | None


def split_halves(values: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Two contiguous halves by count; the earlier half takes the extra observation."""
    cut = (len(values) + 1) // 2
    return values.iloc[:cut], values.iloc[cut:]


def sign_stability(ic: pd.Series) -> bool | None:
    """True when both halves have a positive mean; ``None`` when a half has fewer than 24 months."""
    first, second = split_halves(ic)
    if len(second) < MIN_HALF_MONTHS:
        return None
    return bool(first.mean() > 0.0 and second.mean() > 0.0)


def ic_minimum_detectable_effect(ic: pd.Series) -> tuple[float | None, float | None]:
    """``(MDE_f, MDE_single)`` from the automatic-lag Bartlett LRV; ``None`` when undefined."""
    count = len(ic)
    if count < MIN_IC_MONTHS:
        return None, None
    lags = int(np.floor(4.0 * (count / 100.0) ** (2.0 / 9.0)))
    lrv = newey_west_long_run_variance(ic, lags)
    mde_f = mde_from_long_run_variance(lrv, count, Z_EFF)
    if math.isnan(mde_f):
        return None, None
    return mde_f, mde_from_long_run_variance(lrv, count, Z_SINGLE)


def decide_gate(factors: Sequence[FactorGateInput], *, kill_reachable_projection: bool) -> dict[str, object]:
    """Return the first matching outcome of plan section 6.9 with its flags."""
    if len(factors) != FAMILY_A_SIZE:
        raise ValueError(f"family_size_mismatch: decide_gate needs {FAMILY_A_SIZE} Family A factors")
    survivors = [f for f in factors if f.reject and f.mean_ic > 0.0]
    if any(f.status != "evaluated" or f.mde is None or f.sign_stable is None or f.net_ls is None
           for f in factors):
        outcome = "evaluation_incomplete"
    elif any(f.sign_stable and f.net_ls is not None and f.net_ls > 0.0 for f in survivors):
        outcome = "proceed"
    elif survivors:
        outcome = "survivor_without_confirmation"
    elif all(f.mde is not None and f.mde <= ADEQUATE_MDE for f in factors):
        outcome = "review_thesis"
    else:
        outcome = "extend_first"
    mdes = [f.mde for f in factors]
    if any(value is None for value in mdes):
        power_status = "undefined"
    elif all(value <= ADEQUATE_MDE for value in mdes if value is not None):
        power_status = "adequate"
    else:
        power_status = "inadequate"
    return {
        "outcome": outcome,
        "contrary_rejections": tuple(f.factor_id for f in factors if f.reject and f.mean_ic < 0.0),
        "kill_reachable_projection": bool(kill_reachable_projection),
        "power_status": power_status,
    }
