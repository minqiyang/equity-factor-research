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
from pandas.api.types import is_bool_dtype, is_complex_dtype, is_numeric_dtype
from scipy.stats import norm

from features.diagnostics import newey_west_mean_tstat
from features.multiple_testing import adjust_pvalues
from research.m55_index_tilt import COST_SCHEDULE, refuse


MONTHS_PER_YEAR = 12
SCREEN_START, SCREEN_END = pd.Period("1963-07", "M"), pd.Period("1992-12", "M")
CONFIRM_START, CONFIRM_END = pd.Period("1993-02", "M"), pd.Period("2014-03", "M")
CHECK_START = pd.Period("2014-04", "M")
CONFIRM_MONTHS = 254
SCREEN_MIN_MONTHS = 36
# Monthly returns that touch the seal window [2019-07-31, 2020-07-31) (O-11, O-12, O-18); a check series skips them.
SEAL_MONTHS = pd.period_range("2019-07", "2020-07", freq="M")
PERIODS = ("screen", "confirm", "check")
IR_MIN = 0.2                         # screen net information ratio against CW-PIT
T_MIN = 1.0                          # screen HAC t against CW-PIT
SHORTLIST_CAP = 10                   # R9
SHORTLIST_RULE = {"ir_min": IR_MIN, "t_min": T_MIN, "shortlist_cap": SHORTLIST_CAP}
RECORD_STATUSES = ("ok", "undefined")
ALPHA = 0.05                         # primary family, Holm
NI_MARGIN = 0.005                    # test B: annual return at most 0.5 point below SPY
VOL_RATIO_MAX = 0.90                 # test B: point estimate of the volatility ratio
BOOTSTRAP_UPPER_MAX = 1.0            # test B: the one-sided 95 percent upper bound must be below this
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
    """Refuse unless ``series`` is a complete monthly series of finite real values inside ``period``.

    Screen: every month is in 1963-07 to 1992-12, the last month is 1992-12 (a
    signal may start later), and there are at least 36 months. Confirm: the
    months are exactly 1993-02 to 2014-03. Check: the first month is 2014-04,
    no month is in ``SEAL_MONTHS``, and the seal months are the only gap; the
    statistics join the months on both sides with no fill. Complex and boolean
    dtypes refuse before any cast. The input is not changed.
    """
    if period not in PERIODS:
        raise refuse("period_invalid", period)
    if not isinstance(series, pd.Series) or not isinstance(series.index, pd.PeriodIndex) \
            or series.index.freqstr != "M" or not len(series):
        raise refuse("series_invalid", f"{name}: a non-empty Series with a monthly PeriodIndex is required")
    dtype = series.dtype
    if is_bool_dtype(dtype) or is_complex_dtype(dtype) or not is_numeric_dtype(dtype):
        raise refuse("series_invalid", f"{name}: values must be real numbers, not {dtype}")
    index = series.index
    if not index.is_unique or not index.is_monotonic_increasing:
        raise refuse("series_invalid", f"{name}: months must be sorted and unique")
    if period == "check" and index.isin(SEAL_MONTHS).any():
        raise refuse("seal_month", f"{name}: a month from {SEAL_MONTHS[0]} to {SEAL_MONTHS[-1]} is sealed")
    expected = pd.period_range(index[0], index[-1], freq="M")
    if period == "check":
        expected = expected[~expected.isin(SEAL_MONTHS)]
    if not index.equals(expected):
        raise refuse("month_missing", f"{name}: a month between {index[0]} and {index[-1]} has no row")
    values = series.to_numpy(dtype=float, na_value=np.nan)
    if not np.isfinite(values).all():
        raise refuse("missing_return", f"{name}: a value is NaN or infinite")
    first, last = index[0], index[-1]
    if period == "screen" and (first < SCREEN_START or last != SCREEN_END):
        raise refuse("period_violation", f"{name}: {first} to {last} must lie in the screen {SCREEN_START} to "
                                         f"{SCREEN_END} and end at {SCREEN_END}")
    if period == "screen" and len(index) < SCREEN_MIN_MONTHS:
        raise refuse("screen_too_short", f"{name}: {len(index)} < {SCREEN_MIN_MONTHS} months")
    if period == "confirm" and (first != CONFIRM_START or last != CONFIRM_END):
        raise refuse("period_violation", f"{name}: {first} to {last} is not the confirm {CONFIRM_START} to "
                                         f"{CONFIRM_END}")
    if period == "check" and first != CHECK_START:
        raise refuse("period_violation", f"{name}: the check period starts at {CHECK_START}, not {first}")
    return pd.Series(values, index=index, name=series.name)


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
    """One candidate: its net minus the CW-PIT net of the same run, screen months only.

    A zero or undefined TE or an undefined HAC t gives a typed failed record
    (``status = "undefined"``, the undefined values as ``None``); the screen
    goes on and the record stays visible and hashed.
    """
    clean = check_paired({"candidate": net, "cw": cw_net}, "screen")
    active = clean["candidate"] - clean["cw"]
    if annual_turnover is not None and not (math.isfinite(annual_turnover) and annual_turnover >= 0.0):
        raise refuse("turnover_invalid", f"{annual_turnover}")
    mean = annual_mean(active)
    te = float(active.std(ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    t = newey_west_mean_tstat(active)
    defined = math.isfinite(te) and te > 0.0 and math.isfinite(t)
    return {"status": "ok" if defined else "undefined", "first_month": str(active.index[0]),
            "last_month": str(active.index[-1]), "months": len(active), "annual_active_mean": mean,
            "annual_te": te if math.isfinite(te) else None,
            "information_ratio": mean / te if defined else None, "hac_t": t if defined else None,
            "p_one_sided": float(norm.sf(t)) if defined else None,
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


def shortlist_digest(record: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical JSON of the record's rule, candidates, shortlist, and decision."""
    payload = {key: record.get(key) for key in ("rule", "candidates", "shortlist", "decision")}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def verify_frozen_screen(record: Mapping[str, Any], expected_digest: str) -> bool:
    """Refuse unless the record is the one frozen before any confirm month; True when the shortlist is not empty.

    ``expected_digest`` is the digest saved at the original freeze. The
    recomputed digest, the record's own digest, and ``expected_digest`` must be
    equal, so a replacement record with its own new digest refuses. The rule
    values must equal the module constants.
    """
    recomputed = shortlist_digest(record)
    if not isinstance(expected_digest, str) or not recomputed == record.get("digest_sha256") == expected_digest:
        raise refuse("shortlist_digest_mismatch", "the screen record is not the frozen record")
    if record.get("rule") != SHORTLIST_RULE:
        raise refuse("shortlist_rule_mismatch", f"{record.get('rule')} differs from {SHORTLIST_RULE}")
    decision = record.get("decision")
    if decision not in ("shortlist_frozen", "screen_empty") or (decision == "shortlist_frozen") != bool(
            record.get("shortlist")):
        raise refuse("screen_record_invalid", f"decision {decision} does not match the shortlist")
    return decision == "shortlist_frozen"


def freeze_shortlist(records: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Apply the O-21 rule (IR >= 0.2 and HAC t >= 1.0) and hash the full record.

    Every candidate stays in the record with its values and pass flag; a
    record with ``status = "undefined"`` fails. The digest covers every
    candidate record, the shortlist, the rule values, and the decision.
    More than ``SHORTLIST_CAP`` shortlisted candidates refuses; an empty
    shortlist gives the stop decision ``screen_empty`` (no confirm month is
    opened).
    """
    if not records:
        raise refuse("screen_empty_input", "no candidate record")
    candidates = {}
    for candidate_id in sorted(records):
        record = dict(records[candidate_id])
        if record.get("status") not in RECORD_STATUSES:
            raise refuse("record_invalid", f"{candidate_id}: status {record.get('status')}")
        if record["status"] == "undefined":
            record["shortlisted"] = False            # a typed failed record; it stays visible and hashed
        else:
            ir, t = float(record["information_ratio"]), float(record["hac_t"])
            if not (math.isfinite(ir) and math.isfinite(t)):
                raise refuse("statistic_undefined", candidate_id)
            record["shortlisted"] = ir >= IR_MIN and t >= T_MIN
        candidates[candidate_id] = record
    shortlist = [c for c, record in candidates.items() if record["shortlisted"]]
    if len(shortlist) > SHORTLIST_CAP:
        raise refuse("shortlist_over_cap", f"{len(shortlist)} > {SHORTLIST_CAP}")
    payload = {"rule": dict(SHORTLIST_RULE), "candidates": candidates, "shortlist": shortlist,
               "decision": "shortlist_frozen" if shortlist else "screen_empty"}
    return {**payload, "digest_sha256": shortlist_digest(payload)}


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

def bootstrap_rows(n: int) -> np.ndarray:
    """The row matrix of the moving-block bootstrap: one row of ``n`` month positions per draw.

    Each draw takes ``ceil(n / 12)`` blocks of 12 consecutive months with
    starts drawn uniformly from ``0`` to ``n - 12`` (no wrap) and cuts the
    joined path to ``n`` months. The seed is fixed.
    """
    if n < BLOCK_MONTHS:
        raise refuse("bootstrap_too_short", f"{n} < {BLOCK_MONTHS}")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    blocks = -(-n // BLOCK_MONTHS)
    starts = rng.integers(0, n - BLOCK_MONTHS + 1, size=(BOOTSTRAP_DRAWS, blocks))
    return (starts[:, :, None] + np.arange(BLOCK_MONTHS)).reshape(BOOTSTRAP_DRAWS, -1)[:, :n]


def bootstrap_vol_ratio(low: np.ndarray, spy: np.ndarray) -> dict[str, Any]:
    """Paired moving-block bootstrap of vol(low) / vol(spy): both series use the same rows in each draw."""
    rows = bootstrap_rows(len(low))
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
    """A is ``met`` when every condition holds.

    When the Holm condition fails, A is ``positive_not_shown`` if both confirm
    means are above zero. When Holm passes but the 2x or check rule fails, A is
    ``not_met_robustness``. Anything else is ``not_met``.
    """
    conditions = {"holm_p_at_most_alpha": adjusted_p_a <= ALPHA,
                  "confirm_means_positive": confirm["vs_spy"] > 0.0 and confirm["vs_cw"] > 0.0,
                  "cost_2x_means_positive": confirm_2x["vs_spy"] > 0.0 and confirm_2x["vs_cw"] > 0.0,
                  "check_means_not_negative": check["vs_spy"] >= 0.0 and check["vs_cw"] >= 0.0}
    met = all(conditions.values())
    if met:
        label = "met"
    elif not conditions["confirm_means_positive"]:
        label = "not_met"
    else:
        label = "not_met_robustness" if conditions["holm_p_at_most_alpha"] else "positive_not_shown"
    return {"passed": met, "label": label, "conditions": conditions}


def decide_b(adjusted_p_b: float, vol_ratio: float, upper_95: float, check: Mapping[str, float]) -> dict[str, Any]:
    conditions = {"holm_p_at_most_alpha": adjusted_p_b <= ALPHA,
                  "vol_ratio_at_most_max": vol_ratio <= VOL_RATIO_MAX,
                  "bootstrap_upper_below_one": upper_95 < BOOTSTRAP_UPPER_MAX,
                  "check_gap_above_margin": check["annual_gap"] > -NI_MARGIN,
                  "check_vol_ratio_below_one": check["vol_ratio"] < CHECK_VOL_RATIO_MAX}
    met = all(conditions.values())
    return {"passed": met, "label": "met" if met else "not_met", "conditions": conditions}


def stop_after_confirm(annual_mean_vs_spy: float) -> str | None:
    """The line stops as a declared negative result below 0.3 percent a year, whatever A's outcome."""
    return "confirm_below_floor" if annual_mean_vs_spy < CONFIRM_FLOOR else None


def primary_decision(screen_record: Mapping[str, Any], expected_digest: str, confirm: Mapping[str, pd.Series],
                     confirm_2x: Mapping[str, pd.Series], check: Mapping[str, pd.Series]) -> dict[str, Any]:
    """The O-21 primary family from net series, after the frozen screen record is checked.

    ``screen_record`` is the ``freeze_shortlist`` output and ``expected_digest``
    the digest saved at the original freeze; ``verify_frozen_screen`` runs
    before any confirm or check input is used.

    ``confirm`` holds ``composite``, ``cw``, ``spy``, and ``low_risk`` (confirm
    months, dated costs). ``confirm_2x`` holds ``composite`` and ``cw`` at 2x
    costs (SPY is the same series). ``check`` holds ``composite``, ``cw``,
    ``spy``, and ``low_risk`` from 2014-04, seal months left out.

    After ``screen_empty``, test A and the composite stop rule are refused and
    their inputs are not read. Test B still runs (it uses no screened signal,
    O-20); the Holm family keeps size 2 with p_A = 1.0 (R9).
    """
    opened = verify_frozen_screen(screen_record, expected_digest)
    if opened:
        a = composite_test(confirm["composite"], confirm["spy"], confirm["cw"])
        a_2x = composite_means(confirm_2x["composite"], confirm["spy"], confirm_2x["cw"], "confirm")
        a_check = composite_means(check["composite"], check["spy"], check["cw"], "check")
    b = low_risk_test(confirm["low_risk"], confirm["spy"])
    b_check = low_risk_check(check["low_risk"], check["spy"])
    adjusted = holm_primary(a["p_a"] if opened else 1.0, b["p_b"])
    test_b = {**b, "check": b_check, "holm_p": adjusted["B"],
              **decide_b(adjusted["B"], b["vol_ratio"], b["bootstrap"]["upper_95"], b_check)}
    if not opened:
        return {"test_a": {"run": False, "refused": "screen_empty_confirm", "passed": False, "label": "not_run"},
                "test_b": test_b, "stop": "screen_empty"}
    a_means = {"vs_spy": a["vs_spy"]["annual_mean"], "vs_cw": a["vs_cw"]["annual_mean"]}
    return {"test_a": {"run": True, **a, "cost_2x": a_2x, "check": a_check, "holm_p": adjusted["A"],
                       **decide_a(adjusted["A"], a_means, a_2x, a_check)},
            "test_b": test_b, "stop": stop_after_confirm(a_means["vs_spy"])}


def secondary_family(screen_record: Mapping[str, Any], expected_digest: str,
                     entries: Mapping[str, Mapping[str, pd.Series]], family_size: int) -> dict[str, Any]:
    """Test A statistics for each single signal and the baseline composite, with BY q-values of p_A.

    The same frozen-screen gate as ``primary_decision`` runs before any series
    is read; after ``screen_empty`` it refuses. Each entry holds ``composite``,
    ``spy``, and ``cw`` confirm series. ``family_size`` is the declared size of
    the secondary family; fewer members keep it. The family decides nothing.
    """
    if not verify_frozen_screen(screen_record, expected_digest):
        raise refuse("screen_empty_confirm", "screen_empty: no confirm month is opened for a tilt")
    if isinstance(family_size, bool) or not isinstance(family_size, int) or family_size < max(len(entries), 1):
        raise refuse("family_size_invalid", f"{family_size} for {len(entries)} members")
    stats = {name: composite_test(e["composite"], e["spy"], e["cw"]) for name, e in sorted(entries.items())}
    q = adjust_pvalues(pd.Series({name: s["p_a"] for name, s in stats.items()}, dtype=float), method="by",
                       family_size=family_size)
    return {"members": {name: {**s, "q_by": float(q[name])} for name, s in stats.items()},
            "family_size": family_size, "decides_nothing": True, "note": SECONDARY_NOTE}
