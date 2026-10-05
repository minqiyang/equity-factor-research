"""Milestone 5.5: screen, shortlist, success, and stop decisions of the signal-screen design note.

Card m55-criteria (owner decisions O-19, O-20, O-21) turns monthly net return
series into the locked decisions of the design note, sections 2, 4, 5, and 6.
This module reads no data and builds no weights. Its inputs are the monthly
net returns that ``m55_index_tilt.book_summary(...)["monthly_net"]`` gives: a
``PeriodIndex`` of freq ``M``.

Each period function refuses a series that holds a month outside its period,
so a screen call cannot read a confirm month (R9). A NaN or infinite value
refuses; nothing is filled or dropped (R6).
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

import numpy as np
import pandas as pd
from scipy.stats import norm

from features.diagnostics import newey_west_mean_tstat
from features.multiple_testing import adjust_pvalues
from research.m55_index_tilt import COST_SCHEDULE, refuse


MONTHS_PER_YEAR = 12
SCREEN_START, SCREEN_END = pd.Period("1963-07", "M"), pd.Period("1992-12", "M")
CONFIRM_START, CONFIRM_END = pd.Period("1993-02", "M"), pd.Period("2014-03", "M")
CHECK_START = pd.Period("2014-04", "M")
CONFIRM_MONTHS = 254
PERIODS = ("screen", "confirm", "check")
IR_MIN = 0.2                         # screen net information ratio against CW-PIT
T_MIN = 1.0                          # screen HAC t against CW-PIT
SHORTLIST_CAP = 10                   # R9
ALPHA = 0.05                         # primary family, Holm
NI_MARGIN = 0.005                    # test B: annual return at most 0.5 point below SPY
VOL_RATIO_MAX = 0.90                 # test B: point estimate of the volatility ratio
CHECK_VOL_RATIO_MAX = 1.0            # test B check period: the ratio must be below this
CONFIRM_FLOOR = 0.003                # stop rule: composite annual mean against SPY
BLOCK_MONTHS = 12
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20261003            # fixed before any result (O-21 date)
BOOTSTRAP_QUANTILE = 95.0
DRAWDOWN_EPISODES = 3
FLOAT_FORMAT = ".17g"                # canonical JSON: round-trip exact
# One-way bp per traded notional, in the COST_SCHEDULE format. Design note section 4, item 4:
# fixed commissions before 1975-05, the one-eighth tick to 1992-12, then the engine schedule (R8).
SCREEN_COST_SCHEDULE = ((None, 30.0, 30.0), ("1975-05-01", 10.0, 30.0), ("1993-01-01", 5.0, 20.0)) + COST_SCHEDULE[1:]
SECONDARY_NOTE = "secondary family: reported with BY q-values; it decides nothing"


# Input checks ---------------------------------------------------------------------------

def check_series(series: pd.Series, name: str, period: str) -> pd.Series:
    """Refuse unless ``series`` is a complete monthly series of finite values inside ``period``.

    Screen: every month is in 1963-07 to 1992-12 (a signal may start later).
    Confirm: the months are exactly 1993-02 to 2014-03. Check: the first month
    is 2014-04.
    """
    if period not in PERIODS:
        raise refuse("period_invalid", period)
    if not isinstance(series, pd.Series) or not isinstance(series.index, pd.PeriodIndex) \
            or series.index.freqstr != "M" or not len(series):
        raise refuse("series_invalid", f"{name}: a non-empty Series with a monthly PeriodIndex is required")
    if series.dtype == bool or not pd.api.types.is_numeric_dtype(series.dtype):
        raise refuse("series_invalid", f"{name}: values must be real numbers")
    index = series.index
    if not index.is_unique or not index.is_monotonic_increasing:
        raise refuse("series_invalid", f"{name}: months must be sorted and unique")
    if len(index) != len(pd.period_range(index[0], index[-1], freq="M")):
        raise refuse("month_missing", f"{name}: a month between {index[0]} and {index[-1]} has no row")
    if not np.isfinite(series.to_numpy(dtype=float)).all():
        raise refuse("missing_return", f"{name}: a value is NaN or infinite")
    first, last = index[0], index[-1]
    if period == "screen" and (first < SCREEN_START or last > SCREEN_END):
        raise refuse("period_violation", f"{name}: {first} to {last} is outside the screen {SCREEN_START} to "
                                         f"{SCREEN_END}")
    if period == "confirm" and (first != CONFIRM_START or last != CONFIRM_END):
        raise refuse("period_violation", f"{name}: {first} to {last} is not the confirm {CONFIRM_START} to "
                                         f"{CONFIRM_END}")
    if period == "check" and first != CHECK_START:
        raise refuse("period_violation", f"{name}: the check period starts at {CHECK_START}, not {first}")
    return series.astype(float)


def check_paired(series: Mapping[str, pd.Series], period: str) -> dict[str, pd.Series]:
    """Check each series, then refuse unless all hold the same months."""
    clean = {name: check_series(values, name, period) for name, values in series.items()}
    months = [values.index for values in clean.values()]
    if any(not m.equals(months[0]) for m in months[1:]):
        raise refuse("months_misaligned", ", ".join(clean))
    return clean


# Annual figures -------------------------------------------------------------------------

def annual_mean(monthly: pd.Series) -> float:
    return MONTHS_PER_YEAR * float(monthly.mean())


def annual_vol(monthly: pd.Series) -> float:
    """The ddof-1 monthly standard deviation times sqrt(12); zero or undefined refuses."""
    vol = float(monthly.std(ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    if not math.isfinite(vol) or vol <= 0.0:
        raise refuse("statistic_undefined", "volatility is zero or undefined")
    return vol


def hac_t(monthly: pd.Series) -> float:
    """Newey-West t of the mean with the automatic lag ``floor(4 (n / 100)^(2/9))``; undefined refuses."""
    t = newey_west_mean_tstat(monthly)
    if not math.isfinite(t):
        raise refuse("statistic_undefined", "HAC t is undefined")
    return t


def mean_test(monthly: pd.Series) -> dict[str, Any]:
    """Annual mean, HAC t, and the one-sided p of a monthly active series."""
    t = hac_t(monthly)
    return {"months": len(monthly), "annual_mean": annual_mean(monthly), "hac_t": t,
            "p_one_sided": float(norm.sf(t))}


# Screen and shortlist -------------------------------------------------------------------

def screen_record(net: pd.Series, cw_net: pd.Series, annual_turnover: float | None = None) -> dict[str, Any]:
    """One candidate: its net minus the CW-PIT net of the same run, screen months only."""
    clean = check_paired({"candidate": net, "cw": cw_net}, "screen")
    active = clean["candidate"] - clean["cw"]
    if annual_turnover is not None and not (math.isfinite(annual_turnover) and annual_turnover >= 0.0):
        raise refuse("turnover_invalid", f"{annual_turnover}")
    test = mean_test(active)
    te = annual_vol(active)
    return {"first_month": str(active.index[0]), "last_month": str(active.index[-1]), "months": test["months"],
            "annual_active_mean": test["annual_mean"], "annual_te": te,
            "information_ratio": test["annual_mean"] / te, "hac_t": test["hac_t"],
            "p_one_sided": test["p_one_sided"],
            "annual_turnover": None if annual_turnover is None else float(annual_turnover)}


def canonical_json(value: Any) -> str:
    """Sorted keys, no spaces, and each float as a ``FLOAT_FORMAT`` string; a non-finite float refuses."""
    def encode(item: Any) -> Any:
        if isinstance(item, (bool, np.bool_)) or item is None or isinstance(item, str):
            return bool(item) if isinstance(item, np.bool_) else item
        if isinstance(item, (int, np.integer)):
            return int(item)
        if isinstance(item, (float, np.floating)):
            if not math.isfinite(item):
                raise refuse("digest_value_invalid", f"{item}")
            return format(float(item), FLOAT_FORMAT)
        if isinstance(item, Mapping):
            return {str(k): encode(v) for k, v in item.items()}
        if isinstance(item, (list, tuple)):
            return [encode(v) for v in item]
        raise refuse("digest_value_invalid", type(item).__name__)
    return json.dumps(encode(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


def freeze_shortlist(records: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Apply the O-21 rule (IR >= 0.2 and HAC t >= 1.0) and hash the full record.

    Every candidate stays in the record with its values and pass flag. The
    digest covers every candidate record, the shortlist, and the rule values.
    More than ``SHORTLIST_CAP`` shortlisted candidates refuses; an empty
    shortlist gives the stop decision ``screen_empty`` (no confirm month is
    opened).
    """
    if not records:
        raise refuse("screen_empty_input", "no candidate record")
    candidates = {}
    for candidate_id in sorted(records):
        record = dict(records[candidate_id])
        ir, t = float(record["information_ratio"]), float(record["hac_t"])
        if not (math.isfinite(ir) and math.isfinite(t)):
            raise refuse("statistic_undefined", candidate_id)
        record["shortlisted"] = ir >= IR_MIN and t >= T_MIN
        candidates[candidate_id] = record
    shortlist = [c for c, record in candidates.items() if record["shortlisted"]]
    if len(shortlist) > SHORTLIST_CAP:
        raise refuse("shortlist_over_cap", f"{len(shortlist)} > {SHORTLIST_CAP}")
    rule = {"ir_min": IR_MIN, "t_min": T_MIN, "shortlist_cap": SHORTLIST_CAP}
    payload = {"rule": rule, "candidates": candidates, "shortlist": shortlist}
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return {**payload, "digest_sha256": digest, "decision": "shortlist_frozen" if shortlist else "screen_empty"}


def screen(candidates: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """``candidates`` maps an ID to ``{"net", "cw_net", "annual_turnover" (optional)}``."""
    return freeze_shortlist({c: screen_record(v["net"], v["cw_net"], v.get("annual_turnover"))
                             for c, v in candidates.items()})


# Test A: the composite ------------------------------------------------------------------

def composite_test(composite: pd.Series, spy: pd.Series, cw: pd.Series) -> dict[str, Any]:
    """Confirm period: composite minus SPY and composite minus CW-PIT; p_A is the larger one-sided p."""
    clean = check_paired({"composite": composite, "spy": spy, "cw": cw}, "confirm")
    vs_spy = mean_test(clean["composite"] - clean["spy"])
    vs_cw = mean_test(clean["composite"] - clean["cw"])
    return {"vs_spy": vs_spy, "vs_cw": vs_cw, "p_a": max(vs_spy["p_one_sided"], vs_cw["p_one_sided"])}


def composite_means(composite: pd.Series, spy: pd.Series, cw: pd.Series, period: str) -> dict[str, float]:
    """Annual active means against SPY and CW-PIT (the 2x-cost or check-period sign rules)."""
    clean = check_paired({"composite": composite, "spy": spy, "cw": cw}, period)
    return {"vs_spy": annual_mean(clean["composite"] - clean["spy"]),
            "vs_cw": annual_mean(clean["composite"] - clean["cw"])}


# Test B: the low-risk version -----------------------------------------------------------

def bootstrap_vol_ratio(low: np.ndarray, spy: np.ndarray) -> dict[str, Any]:
    """Paired moving-block bootstrap of vol(low) / vol(spy).

    Each draw takes ``ceil(n / 12)`` blocks of 12 consecutive months with
    starts drawn uniformly from ``0`` to ``n - 12`` (no wrap), cuts the joined
    path to ``n`` months, and uses the same months for both series.
    """
    n = len(low)
    if n < BLOCK_MONTHS:
        raise refuse("bootstrap_too_short", f"{n} < {BLOCK_MONTHS}")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    blocks = -(-n // BLOCK_MONTHS)
    starts = rng.integers(0, n - BLOCK_MONTHS + 1, size=(BOOTSTRAP_DRAWS, blocks))
    rows = (starts[:, :, None] + np.arange(BLOCK_MONTHS)).reshape(BOOTSTRAP_DRAWS, -1)[:, :n]
    ratios = low[rows].std(axis=1, ddof=1) / spy[rows].std(axis=1, ddof=1)
    if not np.isfinite(ratios).all():
        raise refuse("statistic_undefined", "a bootstrap draw has an undefined volatility ratio")
    return {"p_vol": float(np.mean(ratios >= 1.0)), "upper_95": float(np.percentile(ratios, BOOTSTRAP_QUANTILE)),
            "draws": BOOTSTRAP_DRAWS, "block_months": BLOCK_MONTHS, "seed": BOOTSTRAP_SEED}


def drawdown_episodes(monthly: pd.Series) -> list[dict[str, Any]]:
    """Non-overlapping drawdown episodes of the compounded path, deepest first.

    Wealth starts at 1 at the month before the first return. An episode starts
    after a peak, has its trough at the lowest wealth before recovery, and ends
    at the first month whose wealth is at least the peak again (``None`` when
    the path does not recover). Depth is trough wealth / peak wealth - 1.
    """
    months = [monthly.index[0] - 1, *monthly.index]
    wealth = np.concatenate([[1.0], np.cumprod(1.0 + monthly.to_numpy(dtype=float))])
    episodes, peak, current = [], 0, None
    for k in range(1, len(wealth)):
        if wealth[k] >= wealth[peak]:
            if current is not None:
                current["recovery_month"] = str(months[k])
                episodes.append(current)
                current = None
            peak = k
        elif current is None or wealth[k] < wealth[current["trough"]]:
            current = {"peak": peak, "trough": k} if current is None else {**current, "trough": k}
    if current is not None:
        current["recovery_month"] = None
        episodes.append(current)
    out = [{"peak_month": str(months[e["peak"]]), "trough_month": str(months[e["trough"]]),
            "recovery_month": e["recovery_month"], "depth": float(wealth[e["trough"]] / wealth[e["peak"]] - 1.0)}
           for e in episodes]
    return sorted(out, key=lambda e: (e["depth"], e["peak_month"]))


def low_risk_test(low: pd.Series, spy: pd.Series) -> dict[str, Any]:
    """Confirm period: non-inferiority with the 0.5-point margin, the volatility ratio, and the bootstrap.

    p_B is the larger of p_NI and p_vol. Drawdowns are reported, not tested.
    """
    clean = check_paired({"low_risk": low, "spy": spy}, "confirm")
    gap = clean["low_risk"] - clean["spy"]
    t_ni = hac_t(gap + NI_MARGIN / MONTHS_PER_YEAR)
    p_ni = float(norm.sf(t_ni))
    ratio = annual_vol(clean["low_risk"]) / annual_vol(clean["spy"])
    boot = bootstrap_vol_ratio(clean["low_risk"].to_numpy(), clean["spy"].to_numpy())
    episodes = {name: drawdown_episodes(clean[name]) for name in ("low_risk", "spy")}
    deepest = {name: min((e["depth"] for e in found), default=0.0) for name, found in episodes.items()}
    return {"annual_gap": annual_mean(gap), "t_ni": t_ni, "p_ni": p_ni, "vol_ratio": ratio, "bootstrap": boot,
            "p_b": max(p_ni, boot["p_vol"]),
            "drawdown_ratio": deepest["low_risk"] / deepest["spy"] if deepest["spy"] < 0.0 else None,
            "largest_drawdowns": {name: found[:DRAWDOWN_EPISODES] for name, found in episodes.items()}}


def low_risk_check(low: pd.Series, spy: pd.Series) -> dict[str, float]:
    clean = check_paired({"low_risk": low, "spy": spy}, "check")
    return {"annual_gap": annual_mean(clean["low_risk"] - clean["spy"]),
            "vol_ratio": annual_vol(clean["low_risk"]) / annual_vol(clean["spy"])}


# Primary family, stop rule, and secondary family ----------------------------------------

def holm_primary(p_a: float, p_b: float) -> dict[str, float]:
    adjusted = adjust_pvalues(pd.Series({"A": p_a, "B": p_b}), method="holm")
    return {"A": float(adjusted["A"]), "B": float(adjusted["B"])}


def decide_a(adjusted_p_a: float, confirm: Mapping[str, float], confirm_2x: Mapping[str, float],
             check: Mapping[str, float]) -> dict[str, Any]:
    """A is ``met`` when every condition holds; a failed A with both confirm means positive is
    ``positive_not_shown``; anything else is ``not_met``."""
    conditions = {"holm_p_at_most_alpha": adjusted_p_a <= ALPHA,
                  "confirm_means_positive": confirm["vs_spy"] > 0.0 and confirm["vs_cw"] > 0.0,
                  "cost_2x_means_positive": confirm_2x["vs_spy"] > 0.0 and confirm_2x["vs_cw"] > 0.0,
                  "check_means_not_negative": check["vs_spy"] >= 0.0 and check["vs_cw"] >= 0.0}
    met = all(conditions.values())
    label = "met" if met else ("positive_not_shown" if conditions["confirm_means_positive"] else "not_met")
    return {"passed": met, "label": label, "conditions": conditions}


def decide_b(adjusted_p_b: float, vol_ratio: float, check: Mapping[str, float]) -> dict[str, Any]:
    conditions = {"holm_p_at_most_alpha": adjusted_p_b <= ALPHA,
                  "vol_ratio_at_most_max": vol_ratio <= VOL_RATIO_MAX,
                  "check_gap_above_margin": check["annual_gap"] > -NI_MARGIN,
                  "check_vol_ratio_below_one": check["vol_ratio"] < CHECK_VOL_RATIO_MAX}
    met = all(conditions.values())
    return {"passed": met, "label": "met" if met else "not_met", "conditions": conditions}


def stop_after_confirm(annual_mean_vs_spy: float) -> str | None:
    """The line stops as a declared negative result below 0.3 percent a year, whatever A's outcome."""
    return "confirm_below_floor" if annual_mean_vs_spy < CONFIRM_FLOOR else None


def primary_decision(confirm: Mapping[str, pd.Series], confirm_2x: Mapping[str, pd.Series],
                     check: Mapping[str, pd.Series]) -> dict[str, Any]:
    """The O-21 primary family from net series.

    ``confirm`` holds ``composite``, ``cw``, ``spy``, and ``low_risk`` (confirm
    months, dated costs). ``confirm_2x`` holds ``composite`` and ``cw`` at 2x
    costs (SPY is the same series). ``check`` holds ``composite``, ``cw``,
    ``spy``, and ``low_risk`` from 2014-04.
    """
    a = composite_test(confirm["composite"], confirm["spy"], confirm["cw"])
    b = low_risk_test(confirm["low_risk"], confirm["spy"])
    a_2x = composite_means(confirm_2x["composite"], confirm["spy"], confirm_2x["cw"], "confirm")
    a_check = composite_means(check["composite"], check["spy"], check["cw"], "check")
    b_check = low_risk_check(check["low_risk"], check["spy"])
    adjusted = holm_primary(a["p_a"], b["p_b"])
    a_means = {"vs_spy": a["vs_spy"]["annual_mean"], "vs_cw": a["vs_cw"]["annual_mean"]}
    return {"test_a": {**a, "cost_2x": a_2x, "check": a_check, "holm_p": adjusted["A"],
                       **decide_a(adjusted["A"], a_means, a_2x, a_check)},
            "test_b": {**b, "check": b_check, "holm_p": adjusted["B"],
                       **decide_b(adjusted["B"], b["vol_ratio"], b_check)},
            "stop": stop_after_confirm(a_means["vs_spy"])}


def secondary_family(entries: Mapping[str, Mapping[str, pd.Series]]) -> dict[str, Any]:
    """Test A statistics for each single signal and the baseline composite, with BY q-values of p_A.

    Each entry holds ``composite``, ``spy``, and ``cw`` confirm series. The
    family decides nothing.
    """
    stats = {name: composite_test(e["composite"], e["spy"], e["cw"]) for name, e in sorted(entries.items())}
    q = adjust_pvalues(pd.Series({name: s["p_a"] for name, s in stats.items()}, dtype=float), method="by")
    return {"members": {name: {**s, "q_by": float(q[name])} for name, s in stats.items()},
            "decides_nothing": True, "note": SECONDARY_NOTE}
