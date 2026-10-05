"""Milestone 5.5: the cap-weight book (CW-PIT), the index-tilt book (TILT), and the low-risk book on PIT members.

Card m55-engine (owner decision O-17) builds the engine of the index-tilt design
note, sections 1 and 2. This module reads no data and writes no report; the
tests drive it with synthetic fixtures only.

Timing ``after_close_signal_next_observed_close_v1``: at each month-end
rebalance row ``r``, the cap weights, the scores, the eligibility, and the
tracking-error covariance use rows up to ``r - 1`` only. Both books trade at
the close of row ``r`` and earn from row ``r + 1``.

Card m55-lowrisk (owner decision O-20) adds the optional book ``lowrisk``, a
power volatility tilt built from risk only, and ``calibrate_lowrisk``, which
picks its one knob ``g`` from second moments only (low-risk design note,
sections 3 and 4).

The books run on the long-only engine of ``backtest.portfolio`` with
``weighting_scheme="proportional"`` and ``top_pct=1.0``, so the target weights
pass through unchanged. Costs (R8), terminal events (R4), point-in-time
membership (R2), and halts (``halt_gap_return_v1``) use the Milestone 5
accounting. One event set serves every book.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from backtest.portfolio import (
    BacktestValidationError,
    capture_backtest_source_provenance,
    run_long_only_backtest,
)
from research import m4_7_sp500_pit_rerun as runner
from research.m4_7_family_a import FAMILY_A_IDS, simple_returns


TIMING_CONTRACT = "after_close_signal_next_observed_close_v1"
HALT_POLICY = "halt_gap_return_v1"
SIGNAL_IDS = FAMILY_A_IDS            # the six M5 price signals; Family A orients each so higher is better
TILT_STRENGTH = 0.5                  # w = b x (1 + 0.5 x c)
STOCK_CAP = 0.01                     # |w - b| at most 1 percentage point per stock
TE_TARGET = 0.02                     # ex-ante tracking error against CW-PIT, per year
COV_ROWS = 252                       # daily returns in the covariance window, ending at row r - 1
ANNUAL_ROWS = 252
MIN_VALID_SIGNALS = 4
RENORMALIZE_LOOPS = 100              # cap-and-renormalize passes before the loop refuses
CAP_TOLERANCE = 1e-12                # absolute slack on the stock cap after the last pass
TE_TOLERANCE = 1e-9                  # relative slack on the tracking-error target after scaling
BUDGET_TOLERANCE = 1e-12             # absolute slack on sum w = 1 for each book
ME_REASONS = ("unmapped", "ambiguous", "multi_class", "no_share_fact", "stale_share_fact")
CAUSES = ("cash_merger", "failure", "unknown")
DISAPPEARANCE_FIELDS = ("permanent_id", "effective_date", "known_at", "cause", "delisting_return")
EVENT_RUNS = ("primary", "last_close")
COST_SCALES = {"primary": 1.0, "sensitivity_2x": 2.0}
# One-way bp per traded notional: (first date or None, commission, spread). Design note section 1.
COST_SCHEDULE = ((None, 5.0, 20.0), ("2001-04-01", 2.0, 8.0), ("2007-01-01", 1.0, 4.0))
BOOKS = ("cw", "tilt")
LOWRISK_CAP = 0.02                   # low-risk book: |w - b| at most 2 percentage points per stock
LOWRISK_TE = 0.05                    # low-risk book: ex-ante tracking error against CW-PIT, per year
LOWRISK_GRID = tuple(0.5 * k for k in range(1, 13))     # g = 0.5, 1.0, ..., 6.0 (O-20 calibration)
LOWRISK_TARGET_RATIO = 0.87          # median ex-ante volatility ratio to CW-PIT that the calibration aims at
LOWRISK_RATIO_MIN_ROWS = 126         # complete-case rows the whole-book ratio needs (expert decision, R-d)
LOWRISK_UNDEFINED_MAX = 0.10         # above this share of undefined rebalances, the calibration does not choose


def refuse(reason: str, detail: str = "") -> runner.RunnerStop:
    return runner.RunnerStop(reason, detail)


@dataclass(frozen=True)
class TiltInputs:
    """Aligned panels: rows are the source calendar, columns are permanent IDs.

    ``prices`` is the total-return close the engine accounts with. ``signals``
    holds the six Family A frames (row ``t`` uses data through ``t``).
    ``eligible`` is the boolean M5 eligibility at row ``t``. ``market_equity`` is
    ME at row ``t`` (missing as NaN) and ``me_reason`` its sub-reason where it is
    missing. ``disappearances`` has one row per security with the fields
    ``DISAPPEARANCE_FIELDS``: ``effective_date`` is the settlement row, the row
    after the last observed close; ``known_at`` is the first row at whose close
    the event is known (``known_at <= effective_date``). ``start`` is the
    all-cash anchor row; ``end`` is the last row of its month, and the calendar
    holds a later row in a later month. Every month from ``start`` to ``end``
    has a calendar row, and the window holds at least two rebalances, so at
    least one complete holding month follows the first.
    """

    prices: pd.DataFrame
    signals: Mapping[str, pd.DataFrame]
    eligible: pd.DataFrame
    market_equity: pd.DataFrame
    me_reason: pd.DataFrame
    intervals: pd.DataFrame
    disappearances: pd.DataFrame
    start: pd.Timestamp
    end: pd.Timestamp


def check_inputs(inputs: TiltInputs) -> None:
    prices = inputs.prices
    if set(inputs.signals) != set(SIGNAL_IDS):
        raise refuse("signal_set_invalid", "the six Family A signals are required")
    frames = {"eligible": inputs.eligible, "market_equity": inputs.market_equity, "me_reason": inputs.me_reason,
              **{f"signal {k}": v for k, v in inputs.signals.items()}}
    for name, frame in frames.items():
        if not frame.index.equals(prices.index) or not frame.columns.equals(prices.columns):
            raise refuse("input_misaligned", name)
    if not all(dtype == np.dtype(bool) for dtype in inputs.eligible.dtypes):
        raise refuse("eligible_not_boolean")
    for signal_id, frame in inputs.signals.items():
        values = frame.to_numpy(dtype=float)
        if np.isinf(values).any():
            raise refuse("signal_value_invalid", signal_id)
    # R6: a price is missing (NaN) or a finite positive close; any other present value refuses.
    values = prices.to_numpy(dtype=float)
    if (~np.isnan(values) & ~(np.isfinite(values) & (values > 0.0))).any():
        raise refuse("price_invalid", "a present close is not finite and positive")
    if inputs.start not in prices.index or inputs.end not in prices.index or not inputs.start < inputs.end:
        raise refuse("window_invalid")
    later = prices.index[prices.index > inputs.end]
    if not len(later) or later[0].to_period("M") == inputs.end.to_period("M"):
        raise refuse("window_end_not_month_end", "the calendar must show a later row in a later month")
    months = pd.period_range(inputs.start.to_period("M"), inputs.end.to_period("M"), freq="M")
    if not months.isin(prices.index.to_period("M")).all():
        # A month without rows would give a monthly row without daily rows, or join two holding months.
        raise refuse("calendar_month_missing", "the calendar needs a row in every month from start to end")


# Rebalance schedule, costs, and events --------------------------------------------------

def rebalance_dates(calendar: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """The last calendar row of each month inside ``[start, end]``, without the anchor ``start``."""
    rows = calendar[(calendar >= start) & (calendar <= end)]
    last = pd.Series(rows, index=rows).groupby(rows.to_period("M")).max()
    return pd.DatetimeIndex([d for d in last if d != start])


def dated_cost_frame(dates: pd.DatetimeIndex, schedule: tuple = COST_SCHEDULE, scale: float = 1.0) -> pd.DataFrame:
    """Per-row commission and spread bp from ``schedule``; each entry applies from its first date."""
    starts = [pd.Timestamp(s) for s, _, _ in schedule[1:]]
    if not schedule or schedule[0][0] is not None or starts != sorted(starts) or len(set(starts)) != len(starts):
        raise refuse("cost_schedule_invalid", "the first entry has no date and later dates ascend")
    commission = np.empty(len(dates))
    spread = np.empty(len(dates))
    for first, c, s in schedule:
        on = np.ones(len(dates), dtype=bool) if first is None else np.asarray(dates >= pd.Timestamp(first))
        commission[on], spread[on] = c * scale, s * scale
    return pd.DataFrame({"transaction_cost_bps": commission, "slippage_bps": spread}, index=dates)


def check_disappearances(table: pd.DataFrame, calendar: pd.DatetimeIndex, assets: pd.Index) -> pd.DataFrame:
    if tuple(table.columns) != DISAPPEARANCE_FIELDS:
        raise refuse("disappearances_invalid", "fields")
    clean = table.copy()
    clean["effective_date"] = pd.to_datetime(clean["effective_date"])
    clean["known_at"] = pd.to_datetime(clean["known_at"])
    clean["delisting_return"] = clean["delisting_return"].astype(float)
    if clean["permanent_id"].duplicated().any() or not clean["permanent_id"].isin(assets).all():
        raise refuse("disappearances_invalid", "permanent_id")
    if not clean["cause"].isin(CAUSES).all():
        raise refuse("disappearances_invalid", "cause")
    if not clean["effective_date"].isin(calendar).all() or (clean["effective_date"] <= calendar[0]).any():
        raise refuse("disappearances_invalid", "effective_date")
    if not clean["known_at"].isin(calendar).all() or (clean["known_at"] > clean["effective_date"]).any():
        raise refuse("disappearances_invalid", "known_at must be a calendar row on or before effective_date")
    supplied = clean["delisting_return"].dropna()
    if not np.isfinite(supplied).all() or (supplied < -1.0).any():
        raise refuse("disappearances_invalid", "delisting_return")
    return clean


def terminal_events(table: pd.DataFrame, calendar: pd.DatetimeIndex, run: str) -> pd.DataFrame:
    """R4: one engine event per disappearance, settled at its effective close.

    The reference row is the calendar row before ``effective_date``, which must
    carry the last observed close (the engine refuses otherwise). ``known_at``
    is the caller's availability date. ``primary`` applies the supplied delisting return when present, else the
    declared default: last close (return 0) for a typed cash merger and -100
    percent otherwise. ``last_close`` settles every event at the last close.
    """
    if run not in EVENT_RUNS:
        raise refuse("event_run_invalid", run)
    rows = []
    for record in table.to_dict("records"):
        effective = pd.Timestamp(record["effective_date"])
        prior = calendar[calendar.get_loc(effective) - 1]
        if run == "last_close":
            value = 0.0
        elif math.isfinite(record["delisting_return"]):
            value = float(record["delisting_return"])
        else:
            value = 0.0 if record["cause"] == "cash_merger" else -1.0
        rows.append({"event_id": f"DE-{record['permanent_id']}-{effective.date().isoformat()}",
                     "permanent_id": record["permanent_id"], "effective_date": effective,
                     "known_at": pd.Timestamp(record["known_at"]),
                     "reference_date": prior, "terminal_return": value,
                     "return_basis": "prior_observed_close_to_cash"})
    return pd.DataFrame(rows, columns=["event_id", "permanent_id", "effective_date", "known_at", "reference_date",
                                       "terminal_return", "return_basis"])


# Scores and weights at one rebalance ----------------------------------------------------

def signed_ranks(values: pd.Series) -> pd.Series:
    """2u - 1 with u = (average rank - 1) / (n - 1), as exact fractions; a single value gets 0.

    2u - 1 = (2 rank - n - 1) / (n - 1), and twice an average rank is an
    integer, so each value is an exact fraction. A composite whose true value
    is zero is then exactly zero at any book size.
    """
    n = len(values)
    if n == 1:
        return pd.Series([Fraction(0)], index=values.index, dtype=object)
    twice = (2.0 * values.rank(method="average")).to_numpy()
    return pd.Series([Fraction(int(round(k)) - n - 1, n - 1) for k in twice], index=values.index, dtype=object)


def composite_scores(signal_rows: Mapping[str, pd.Series], full_history: pd.Series,
                     short_history: pd.Series | None = None) -> tuple[pd.Series, dict[str, int]]:
    """c = mean of (2u - 1) over the valid signals; c = 0 under the two rules, which are counted.

    Each ``signal_rows`` series holds row ``r - 1`` values of the book members
    only, so the rank pool is the eligible members with a valid value. A member
    without a complete window is ``short_history`` when its first valid return
    is inside the window and ``window_gap`` otherwise. ``c_zero_natural`` counts
    members whose composite is exactly zero without a rule. The counts can overlap;
    ``c_zero`` counts each member once.
    """
    short_history = ~full_history if short_history is None else short_history
    names = full_history.index
    total = {name: Fraction(0) for name in names}
    count = pd.Series(0, index=names)
    for signal_id in SIGNAL_IDS:
        ranks = signed_ranks(signal_rows[signal_id].dropna())
        for name, value in ranks.items():
            total[name] += value
        count[ranks.index] += 1
    few = count < MIN_VALID_SIGNALS
    incomplete = ~full_history
    # One rounding of the exact mean: raw is zero exactly when the true composite is zero.
    raw = pd.Series([float(total[name] / k) if k else 0.0 for name, k in count.items()], index=names)
    c = raw.where(~(few | incomplete), 0.0)
    natural = ~few & ~incomplete & (raw == 0.0)
    return c, {"c_zero": int((c == 0.0).sum()), "c_zero_few_signals": int(few.sum()),
               "c_zero_short_history": int((incomplete & short_history).sum()),
               "c_zero_window_gap": int((incomplete & ~short_history).sum()),
               "c_zero_natural": int(natural.sum())}


def tracking_error(window: np.ndarray, active: np.ndarray) -> float:
    """Annualized ex-ante TE: the ddof-1 deviation of the window's daily active return, times sqrt(252)."""
    if not active.size or not np.any(active):
        return 0.0
    return float(np.std(window @ active, ddof=1) * math.sqrt(ANNUAL_ROWS))


def budget_weights(b: np.ndarray, m: np.ndarray, free: np.ndarray, returns: np.ndarray, cap: float,
                   te_limit: float, book: str) -> tuple[np.ndarray, dict, int]:
    """Multiply, cap, renormalize, and scale, in that order; the engine step that TILT and ``lowrisk`` share.

    ``w = b m``. Members outside ``free`` must have ``m = 1``; they keep
    ``w = b`` exactly, and only the free members absorb the active budget. Each
    pass caps ``|w - b|`` at ``cap`` and rescales the free weights so their sum
    equals the free cap weight, so active weights sum to zero and ``w >= 0``.
    The loop ends when the cap holds within ``CAP_TOLERANCE`` and refuses after
    ``RENORMALIZE_LOOPS`` passes. The last step scales the active weights
    ``w - b`` until their ex-ante TE on ``returns`` (the free columns of the
    window) is at most ``te_limit``. The third value is the number of free
    members at the cap (within ``CAP_TOLERANCE``) at the start of the last pass.
    """
    w = b * m
    for loops in range(1, RENORMALIZE_LOOPS + 1):
        binding = np.abs(w - b) >= cap - CAP_TOLERANCE
        w = b + np.clip(w - b, -cap, cap)
        if free.any():
            w[free] = w[free] * (math.fsum(b[free]) / math.fsum(w[free]))
        if np.max(np.abs(w - b)) <= cap + CAP_TOLERANCE:
            break
    else:
        raise refuse(f"{book}_loop_not_converged", f"{RENORMALIZE_LOOPS} passes")
    te_before = tracking_error(returns, (w - b)[free])
    scale = 1.0 if te_before <= te_limit else te_limit / te_before
    final = b + scale * (w - b)
    te_after = tracking_error(returns, (final - b)[free])
    if te_after > te_limit * (1.0 + TE_TOLERANCE):
        raise refuse("tracking_error_above_target", f"{te_after}")
    info = {"loops": loops, "ex_ante_te_before_scale": te_before, "te_scale": scale, "ex_ante_te": te_after,
            "max_abs_active": float(np.max(np.abs(final - b)))}
    check_target(b, final, info, cap, te_limit, book)
    return final, info, int(binding[free].sum())


def tilt_weights(b: pd.Series, c: pd.Series, window: pd.DataFrame, pinned: pd.Series) -> tuple[pd.Series, dict]:
    """TILT: the shared engine step with ``m = 1 + 0.5 c``, cap ``STOCK_CAP``, and TE limit ``TE_TARGET``.

    Pinned members (c = 0 for any cause, or no complete covariance window) keep
    ``w = b`` exactly; a member with c = 0 has ``m = 1`` and is not free.
    """
    bv, cv = b.to_numpy(dtype=float), c.to_numpy(dtype=float)
    if np.any(cv[pinned.to_numpy(dtype=bool)] != 0.0):
        raise refuse("pinned_member_scored")
    free = cv != 0.0          # c = 0 for any cause, natural zeros included, keeps w = b
    w, info, _ = budget_weights(bv, 1.0 + TILT_STRENGTH * cv, free, window.to_numpy(dtype=float)[:, free],
                                STOCK_CAP, TE_TARGET, "tilt")
    return pd.Series(w, index=b.index), info


def member_vols(window: pd.DataFrame, full: pd.Series) -> pd.Series:
    """``s_i``: the ddof-1 deviation of the 252 daily returns ending at ``r - 1``, for members with a full window.

    A zero or non-finite ``s_i`` refuses (``lowrisk_vol_invalid``); it is never repaired.
    """
    names = full.index[full.to_numpy(dtype=bool)]
    vol = pd.Series(window[names].to_numpy(dtype=float).std(axis=0, ddof=1), index=names)
    bad = ~(np.isfinite(vol) & (vol > 0.0))
    if bad.any():
        raise refuse("lowrisk_vol_invalid", ", ".join(map(str, vol.index[bad.to_numpy()])))
    return vol


def ex_ante_vol(returns: np.ndarray, weights: np.ndarray) -> float:
    """Annualized ex-ante volatility: the ddof-1 deviation of the window's daily return of ``weights``."""
    return float(np.std(returns @ weights, ddof=1) * math.sqrt(ANNUAL_ROWS))


def whole_book_ratio(window: pd.DataFrame, b: np.ndarray, w: np.ndarray) -> dict[str, Any]:
    """The ex-ante volatility ratio of the whole traded book on its complete-case rows (expert decision, R-b to R-e).

    ``window`` is the traded set's return window that ends at ``r - 1``. The
    rows are the rows where every traded member has a return. A missing price
    blanks two returns, so it removes two rows; no value is filled, clipped, or
    repaired (R6). With at least ``LOWRISK_RATIO_MIN_ROWS`` rows, the status is
    ``defined_full`` (``COV_ROWS`` rows) or ``defined_partial``; with fewer, the
    volatilities and the ratio are NaN (``ratio_window_short``). The status and
    the row counts depend on ``window`` only, never on ``g``. A row is
    ``leading`` when only NaNs before a member's first return in the window
    remove it, and ``gap`` when a NaN after a member's first return does.
    """
    values = window.to_numpy(dtype=float)
    missing = np.isnan(values)
    seen = np.logical_or.accumulate(~missing, axis=0)
    gap = (missing & seen).any(axis=1)
    complete = ~missing.any(axis=1)
    limiting = missing.any(axis=0)
    rows = int(complete.sum())
    record = {"ratio_rows": rows, "ratio_rows_leading": int((~complete & ~gap).sum()),
              "ratio_rows_gap": int(gap.sum()), "ratio_limiting_members": int(limiting.sum()),
              "ratio_limiting_cw_share": math.fsum(b[limiting].tolist())}
    if rows < LOWRISK_RATIO_MIN_ROWS:
        return {"ex_ante_vol": math.nan, "cw_ex_ante_vol": math.nan, "vol_ratio": math.nan,
                "ratio_status": "ratio_window_short", **record}
    rows_used = window[complete].to_numpy(dtype=float)
    vol_w, vol_b = ex_ante_vol(rows_used, w), ex_ante_vol(rows_used, b)
    ratio = vol_w / vol_b if vol_b > 0.0 else math.nan
    if not (math.isfinite(ratio) and ratio > 0.0):
        raise refuse("lowrisk_vol_ratio_invalid", f"ex-ante volatilities {vol_w} and {vol_b}")
    return {"ex_ante_vol": vol_w, "cw_ex_ante_vol": vol_b, "vol_ratio": ratio,
            "ratio_status": "defined_full" if rows == COV_ROWS else "defined_partial", **record}


def lowrisk_weights(b: pd.Series, vol: pd.Series, window: pd.DataFrame, g: float) -> tuple[pd.Series, dict]:
    """``lowrisk``: the shared engine step with ``m = (s / s_med)^(-g)``, cap ``LOWRISK_CAP``, TE ``LOWRISK_TE``.

    ``vol`` holds ``s_i`` of every target member with a full window, the B2
    excluded names included; ``s_med`` is its median. ``b`` and ``window`` cover
    the traded set. A traded member without a full window is pinned at
    ``w = b``. The free multipliers are renormalized so that ``b m`` sums to
    the free cap weight before the cap loop; a multiplier that is not finite
    and positive refuses (``lowrisk_multiplier_invalid``).

    The TE uses the free columns, where the pinned active weights are 0. The
    ex-ante volatilities and their ratio measure the whole traded book on its
    complete-case rows (``whole_book_ratio``). The weights do not depend on
    the ratio status.
    """
    bv = b.to_numpy(dtype=float)
    free = b.index.isin(vol.index)
    if not free.any():
        raise refuse("lowrisk_window_empty", "no traded member has a full window")
    vol_median = float(np.median(vol.to_numpy(dtype=float)))
    m = np.ones(len(bv))
    invalid = refuse("lowrisk_multiplier_invalid", f"g = {g}: a multiplier is not finite and positive")
    with np.errstate(over="ignore", under="ignore"):
        m[free] = (vol[b.index[free]].to_numpy(dtype=float) / vol_median) ** -g
        product = bv[free] * m[free]
    if not (np.isfinite(product) & (product > 0.0)).all():
        raise invalid
    try:
        m[free] = m[free] * (math.fsum(bv[free]) / math.fsum(product.tolist()))
    except OverflowError:
        raise invalid from None
    if not (np.isfinite(m) & (m > 0.0)).all():
        raise invalid
    returns = window.to_numpy(dtype=float)[:, free]
    w, info, capped = budget_weights(bv, m, free, returns, LOWRISK_CAP, LOWRISK_TE, "lowrisk")
    ratio = whole_book_ratio(window, bv, w)
    info = {"g": float(g), "vol_median": vol_median, **ratio, **info, "capped": capped,
            "pinned": int((~free).sum()), "pinned_cw_share": math.fsum(bv[~free].tolist())}
    return pd.Series(w, index=b.index), info


def check_target(b: np.ndarray, w: np.ndarray, info: Mapping[str, float], cap: float = STOCK_CAP,
                 te_limit: float = TE_TARGET, book: str = "tilt") -> None:
    """Refuse unless both books are finite, sum to 1, are non-negative, meet the cap, and meet the TE limit."""
    for name, weights in (("cw", b), (book, w)):
        if not np.isfinite(weights).all() or (weights < 0.0).any():
            raise refuse("target_invalid", f"{name} weights not finite and non-negative")
        if abs(math.fsum(weights.tolist()) - 1.0) > BUDGET_TOLERANCE:
            raise refuse("target_invalid", f"{name} weights do not sum to 1")
    if not all(math.isfinite(float(v)) for v in info.values()):
        raise refuse("target_invalid", "non-finite tracking-error record")
    if np.max(np.abs(w - b)) > cap + CAP_TOLERANCE or info["ex_ante_te"] > te_limit * (1.0 + TE_TOLERANCE):
        raise refuse("target_invalid", "cap or tracking-error limit")


def rebalance_members(inputs: TiltInputs, date: pd.Timestamp, returns: pd.DataFrame, disappearances: pd.DataFrame,
                      first_return: pd.Series) -> dict[str, Any]:
    """The target members, the traded set, CW-PIT, and the return window at ``date``, from row ``r - 1`` only.

    ``first_return`` is each member's first row with a valid return (the row
    count when it has none). It is compared only with rows up to ``r - 1``.

    Declared execution rule (B2): a target member that settles at ``r`` on an
    event first known at ``r`` has no close at ``r``, so it cannot trade. Its
    held position settles under R4 in every book. The traded set is the target
    members without these names. Scores, ranks, volatilities, and the
    covariance stay at ``r - 1``, and the ranks and the volatility median keep
    the excluded names. CW-PIT renormalizes the cap weights pro rata over the
    traded set; TILT and ``lowrisk`` run their tilt, cap, and TE step on the
    traded set.
    """
    calendar = inputs.prices.index
    t = calendar.get_loc(date) - 1
    cutoff = calendar[t]
    # R1 and R2: only events known at the cutoff change the pool; the engine masks the same cells.
    by_r = disappearances["effective_date"] <= date
    known = disappearances["known_at"] <= cutoff
    settled = set(disappearances.loc[by_r & known, "permanent_id"])
    surprise = set(disappearances.loc[by_r & ~known, "permanent_id"])     # effective = known_at = r
    pool = inputs.eligible.iloc[t] & ~inputs.prices.columns.isin(sorted(settled))
    me, reason = inputs.market_equity.iloc[t].astype(float), inputs.me_reason.iloc[t]
    missing = me.isna()
    if (pool & ~missing & ~(np.isfinite(me) & (me > 0.0))).any():
        raise refuse("me_invalid", str(date.date()))
    if (pool & ~missing & reason.notna()).any():
        raise refuse("me_reason_conflict", str(date.date()))
    reasons = reason[pool & missing]
    if not reasons.isin(ME_REASONS).all():
        raise refuse("me_reason_invalid", str(date.date()))
    members = pool & ~missing
    if not members.any():
        raise refuse("empty_book", str(date.date()))
    names = members.index[members.to_numpy()]
    unknown = names.isin(sorted(surprise))
    traded = names[~unknown]
    if not len(traded):
        raise refuse("traded_set_empty", f"{str(date.date())}: every target member settles at r on an event "
                                         "first known at r")
    me_members = me[names]
    me_total = math.fsum(me_members.to_list())
    b = me[traded] / math.fsum(me[traded].to_list())
    first = t - COV_ROWS + 1
    window = returns.iloc[max(first, 0):t + 1][names]
    full = window.notna().sum() == COV_ROWS
    short = first_return[names] > first      # no valid return before the window: a short history, not a gap
    record = {"date": date, "members": len(names), "settled_excluded": int((inputs.eligible.iloc[t] & ~pool).sum()),
              "unknown_event_excluded": int(unknown.sum()),
              "unknown_event_cw_share": math.fsum(me_members[unknown].to_list()) / me_total,
              "me_missing": int(len(reasons)),
              **{f"me_missing_{r}": int((reasons == r).sum()) for r in ME_REASONS}}
    return {"t": t, "names": names, "traded": traded, "b": b, "window": window, "full": full, "short": short,
            "record": record}


def rebalance_targets(inputs: TiltInputs, date: pd.Timestamp, returns: pd.DataFrame, disappearances: pd.DataFrame,
                      first_return: pd.Series, g: float | None = None) -> tuple[dict[str, pd.Series], dict[str, Any]]:
    """CW-PIT, TILT, and (when ``g`` is given) ``lowrisk`` targets at ``date``, from row ``r - 1`` and earlier only."""
    setup = rebalance_members(inputs, date, returns, disappearances, first_return)
    t, names, traded, b = setup["t"], setup["names"], setup["traded"], setup["b"]
    window, full = setup["window"], setup["full"]
    # The ranks use every target member, the excluded names included; only the traded set gets weights.
    c, zero_counts = composite_scores({s: inputs.signals[s].iloc[t][names] for s in SIGNAL_IDS}, full,
                                      setup["short"])
    w, info = tilt_weights(b, c[traded], window[traded], ~full[traded])
    record = {**setup["record"], **zero_counts, **info}
    weights = {"cw": b, "tilt": w}
    if g is not None:
        weights["lowrisk"], low = lowrisk_weights(b, member_vols(window, full), window[traded], g)
        record.update({f"lowrisk_{key}": value for key, value in low.items()})
    return weights, record


def prepare(inputs: TiltInputs) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Check the inputs; return the checked events, the daily returns, and each member's first valid return row."""
    check_inputs(inputs)
    disappearances = check_disappearances(inputs.disappearances, inputs.prices.index, inputs.prices.columns)
    returns = simple_returns(inputs.prices)
    valid = returns.notna().to_numpy()
    first_return = pd.Series(np.where(valid.any(axis=0), valid.argmax(axis=0), len(returns)), index=returns.columns)
    return disappearances, returns, first_return


def check_g(g: float) -> None:
    if not math.isfinite(g) or g < 0.0:
        raise refuse("lowrisk_g_invalid", f"{g}: g is a finite number at or above 0")


def build_targets(inputs: TiltInputs, g: float | None = None) -> dict[str, Any]:
    """Every rebalance target; ``g`` adds the ``lowrisk`` book (no default: the trial file fixes ``g``)."""
    if g is not None:
        check_g(g)
    disappearances, returns, first_return = prepare(inputs)
    dates = rebalance_dates(inputs.prices.index, inputs.start, inputs.end)
    if len(dates) < 2:
        # The first rebalance earns from the next month. With one rebalance (at ``end``), the only monthly row
        # would fall after ``end``, so the window refuses (GPT-R2-01).
        raise refuse("window_too_short", "no complete holding month after the first rebalance")
    books = BOOKS if g is None else BOOKS + ("lowrisk",)
    targets = {book: pd.DataFrame(np.nan, index=dates, columns=inputs.prices.columns) for book in books}
    records = []
    for date in dates:
        weights, record = rebalance_targets(inputs, date, returns, disappearances, first_return, g)
        for book, w in weights.items():
            targets[book].loc[date, w.index] = w.to_numpy()
        records.append(record)
    table = pd.DataFrame(records).set_index("date")
    counts = {key: int(table[key].sum()) for key in table.columns
              if key.startswith("me_missing") or key.startswith("c_zero")
              or key in ("settled_excluded", "unknown_event_excluded", "lowrisk_pinned")}
    return {"targets": targets, "rebalances": table, "counts": counts, "disappearances": disappearances}


RATIO_DEFINED = ("defined_full", "defined_partial")
RATIO_FIELDS = ("vol_ratio", "ratio_status", "ratio_rows", "ratio_rows_leading", "ratio_rows_gap",
                "ratio_limiting_members", "ratio_limiting_cw_share", "ex_ante_vol", "cw_ex_ante_vol", "ex_ante_te",
                "te_scale", "capped", "pinned", "pinned_cw_share")


def lowrisk_bracket(ratios: Sequence[np.ndarray | None], rebalances: int, target: float,
                    stops: bool = True) -> dict[str, Any]:
    """Classify each grid value with a two-sided median bracket, then decide (expert decision, R-g and R-h).

    ``ratios[k]`` holds the defined ratios of grid value ``k`` over
    ``rebalances`` rebalances, or None when that value refused. Its ``u``
    undefined rebalances enter the median once at +inf (``median_hi``) and once
    at -inf (``median_lo``). A value *meets* when ``median_hi <= target``,
    *fails* when ``median_lo > target``, and is *ambiguous* otherwise: the
    missing ratios could move it to either side. Decisions, in this order:

    - ``refused``: a refused value below the first value that meets, or any
      refused value when none meets; ``index`` names the first one, and the
      caller stops with its refusal.
    - ``ratio_coverage_low``: ``u / rebalances > LOWRISK_UNDEFINED_MAX``.
    - ``ratio_coverage_ambiguous``: an ambiguous value below the first value
      that meets, or any ambiguous value when none meets. The owner decides.
    - ``chosen``: the first value that meets; every smaller value fails.
    - ``no_g_reaches_target``.

    With ``stops=False`` (the window diagnostic, R-i), the first two steps are
    skipped: a refused value is passed over, and the coverage stop does not
    apply; ``undefined_share`` is still returned.
    """
    classes, hi, lo, undefined = [], [], [], []
    for values in ratios:
        if values is None:
            classes.append(None)
            hi.append(math.nan)
            lo.append(math.nan)
            continue
        values = np.asarray(values, dtype=float)
        u = rebalances - len(values)
        undefined.append(u)
        hi.append(float(np.median(np.concatenate([values, np.full(u, np.inf)]))))
        lo.append(float(np.median(np.concatenate([values, np.full(u, -np.inf)]))))
        classes.append("meets" if hi[-1] <= target else "fails" if lo[-1] > target else "ambiguous")
    first = classes.index("meets") if "meets" in classes else len(classes)
    record = {"classes": classes, "median_hi": hi, "median_lo": lo,
              "undefined_share": max(undefined) / rebalances if undefined else math.nan}
    if stops and None in classes[:first]:
        return {**record, "decision": "refused", "index": classes.index(None)}
    if stops and record["undefined_share"] > LOWRISK_UNDEFINED_MAX:
        return {**record, "decision": "ratio_coverage_low", "index": None}
    if "ambiguous" in classes[:first]:
        return {**record, "decision": "ratio_coverage_ambiguous", "index": None}
    if first < len(classes):
        return {**record, "decision": "chosen", "index": first}
    return {**record, "decision": "no_g_reaches_target", "index": None}


def calibrate_lowrisk(inputs: TiltInputs, grid: tuple[float, ...], target_ratio: float, start: pd.Timestamp,
                      end: pd.Timestamp) -> dict[str, Any]:
    """Pick ``g`` from second moments only (low-risk design note, section 4; expert decision of 2026-10-05).

    For each ``g`` in ``grid``, the whole-book ex-ante ratio at each rebalance
    of a run anchored at ``start`` and ending at ``end`` (the engine schedule;
    ``whole_book_ratio``), then the decision of ``lowrisk_bracket``. A refused
    ``g`` keeps its rows from earlier rebalances in the rebalance table with
    ``g_status = "refused"``; it gets no bracket class. The window diagnostic
    (R-i; coordinator ruling of 2026-10-05) repeats the bracket classes and the
    choice with every ``defined_partial`` rebalance treated as undefined, but
    without the refusal and coverage stops. ``window_sensitive`` flags a
    different choice (another ``g``, or a choice against an ambiguous or empty
    result) for the owner and does not stop. The diagnostic undefined share and
    ``window_diag_coverage_high`` (that share above ``LOWRISK_UNDEFINED_MAX``)
    are recorded apart and never set ``window_sensitive``.

    Every grid value is recorded (R9). The function computes no mean return,
    Sharpe ratio, return gap, or realized portfolio return, and it runs no book.
    """
    grid = tuple(float(g) for g in grid)
    if not grid or list(grid) != sorted(set(grid)):
        raise refuse("calibration_grid_invalid", "the grid is not empty and strictly ascends")
    for g in grid:
        check_g(g)
    if not math.isfinite(target_ratio) or target_ratio <= 0.0:
        raise refuse("calibration_target_invalid", f"{target_ratio}")
    window_inputs = replace(inputs, start=pd.Timestamp(start), end=pd.Timestamp(end))
    disappearances, returns, first_return = prepare(window_inputs)
    dates = rebalance_dates(inputs.prices.index, window_inputs.start, window_inputs.end)
    if not len(dates):
        raise refuse("calibration_window_empty")
    rows, refused = [], {}
    for date in dates:
        setup = rebalance_members(window_inputs, date, returns, disappearances, first_return)
        vol = member_vols(setup["window"], setup["full"])
        for g in grid:
            if g in refused:
                continue
            try:
                _, low = lowrisk_weights(setup["b"], vol, setup["window"][setup["traded"]], g)
            except runner.RunnerStop as exc:
                refused[g] = (date, exc)
                continue
            rows.append({"date": date, "g": g, **{key: low[key] for key in RATIO_FIELDS}})
    table = pd.DataFrame(rows, columns=["date", "g", *RATIO_FIELDS])
    table.insert(2, "g_status", np.where(table["g"].isin(list(refused)), "refused", "ok"))

    def defined_ratios(statuses: tuple[str, ...]) -> list[np.ndarray | None]:
        return [None if g in refused else table.loc[(table["g"] == g) & table["ratio_status"].isin(statuses),
                                                    "vol_ratio"].to_numpy(dtype=float) for g in grid]

    bracket = lowrisk_bracket(defined_ratios(RATIO_DEFINED), len(dates), target_ratio)
    if bracket["decision"] == "refused":
        raise refused[grid[bracket["index"]]][1]
    full_only = lowrisk_bracket(defined_ratios(("defined_full",)), len(dates), target_ratio, stops=False)
    summary = []
    for k, g in enumerate(grid):
        if g in refused:
            date, exc = refused[g]
            summary.append({"g": g, "status": "refused", "refusal": str(exc), "refusal_date": date,
                            "rebalances": len(dates)})
            continue
        part = table[table["g"] == g]
        defined = part["ratio_status"].isin(RATIO_DEFINED)
        summary.append({
            "g": g, "status": "ok", "refusal": None, "refusal_date": pd.NaT, "rebalances": len(dates),
            "defined": int(defined.sum()), "undefined": int((~defined).sum()),
            "undefined_share": float((~defined).mean()),
            "defined_partial_share": float((part["ratio_status"] == "defined_partial").mean()),
            "median_vol_ratio": float(np.median(part.loc[defined, "vol_ratio"])) if defined.any() else math.nan,
            "median_hi": bracket["median_hi"][k], "median_lo": bracket["median_lo"][k],
            "bracket": bracket["classes"][k], "bracket_full_windows": full_only["classes"][k],
            "max_pinned_cw_share_defined": float(part.loc[defined, "pinned_cw_share"].max()),
            "share_cap_binds": float((part["capped"] > 0).mean()),
            "share_te_scaled": float((part["te_scale"] < 1.0).mean()),
            "share_pinned": float((part["pinned"] > 0).mean()),
            "mean_pinned_cw_share": float(part["pinned_cw_share"].mean())})

    def chosen(result: dict[str, Any]) -> float | None:
        return grid[result["index"]] if result["decision"] == "chosen" else None

    return {"grid": pd.DataFrame(summary), "rebalances": table, "target_ratio": float(target_ratio),
            "start": window_inputs.start, "end": window_inputs.end, "undefined_share": bracket["undefined_share"],
            "chosen_g": chosen(bracket), "decision": bracket["decision"],
            "window_decision": full_only["decision"], "window_chosen_g": chosen(full_only),
            "window_sensitive": chosen(bracket) != chosen(full_only),      # chosen() is None unless "chosen"
            "window_diag_undefined_share": full_only["undefined_share"],
            "window_diag_coverage_high": full_only["undefined_share"] > LOWRISK_UNDEFINED_MAX}


# Engine runs ----------------------------------------------------------------------------

def engine_scores(target: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """Place each rebalance target on row ``r - 1``: the engine trades row ``r`` on the row ``r - 1`` score."""
    scores = pd.DataFrame(np.nan, index=calendar, columns=target.columns)
    for date in target.index:
        scores.iloc[calendar.get_loc(date) - 1] = target.loc[date].to_numpy()
    return scores


def check_engine_targets(result: Any, target: pd.DataFrame, calendar: pd.DatetimeIndex) -> None:
    """Fail closed unless the engine executed exactly these rebalances on the row ``r - 1`` source.

    Holdings after each rebalance equal the target unless the halt policy
    locked capital at that row.
    """
    executed = {row.ledger_date: row for row in result.timing_ledger if row.event_status.startswith("executed")}
    if set(executed) != set(target.index):
        raise refuse("engine_rebalance_mismatch")
    for date, row in executed.items():
        if row.event_status != "executed_invested_target" or row.signal_source_date != calendar[calendar.get_loc(date) - 1]:
            raise refuse("engine_rebalance_mismatch", str(date.date()))
    locked = {pd.Timestamp(r["date"]) for r in (result.halt_ledger or {}).get("locked_execution_rows", [])}
    for date in target.index.difference(pd.DatetimeIndex(sorted(locked))):
        gap = np.abs(result.holdings.loc[date].to_numpy() - target.loc[date].fillna(0.0).to_numpy())
        if gap.max() > 1e-12:
            raise refuse("engine_target_mismatch", str(date.date()))


def run_book(inputs: TiltInputs, target: pd.DataFrame, events: pd.DataFrame, costs: pd.DataFrame) -> Any:
    calendar = inputs.prices.index
    scores = engine_scores(target, calendar)
    try:
        result = run_long_only_backtest(
            inputs.prices, scores, source_provenance=capture_backtest_source_provenance(inputs.prices, scores),
            evaluation_start=inputs.start, evaluation_end=inputs.end, rebalance_frequency="ME", top_pct=1.0,
            weighting_scheme="proportional", constituent_intervals=inputs.intervals,
            terminal_events=events if len(events) else None, dated_costs=costs, missing_price_policy=HALT_POLICY)
    except BacktestValidationError as exc:
        if exc.reason in runner.CLASS_I_ENGINE:
            raise refuse(exc.reason, str(exc)) from exc
        raise
    check_engine_targets(result, target, calendar)
    return result


def monthly_returns(daily: pd.Series) -> pd.Series:
    """Compound measured daily returns by calendar month; the first row (the first rebalance) joins the next month.

    The first rebalance is the last row of its month, so its purchase cost
    falls in the first measured month (the M5 ``month_labels`` convention), and
    the product of monthly growth equals the product of daily growth.
    """
    labels = daily.index.to_period("M").to_numpy().copy()
    labels[0] = labels[0] + 1
    monthly = (1.0 + daily).groupby(labels).prod() - 1.0
    monthly.index = pd.PeriodIndex(monthly.index, freq="M")
    return monthly


def book_summary(result: Any, target: pd.DataFrame) -> dict[str, Any]:
    """Measured rows run from the first rebalance row to ``end``; the all-cash rows before it are left out.

    The monthly rows are exactly the months from the one after the first
    rebalance to the month of the last rebalance (``end``): one row per
    holding month, none outside the evaluation span.
    """
    first, last = target.index[0], target.index[-1]
    measured = result.returns.index >= first
    daily = result.returns[measured]
    monthly = monthly_returns(daily)
    months = pd.period_range(first.to_period("M") + 1, last.to_period("M"), freq="M")
    if daily.index[-1] != last or not monthly.index.equals(months):
        raise refuse("monthly_period_invalid", f"{list(monthly.index.astype(str))} for {first.date()} to {last.date()}")
    turnover, cost = result.turnover[measured], result.total_trading_costs[measured]
    held = [r for r in result.terminal_event_log if float(r["incoming_weight"]) > 0.0]
    weights = [float(r["incoming_weight"]) for r in held]
    return {"daily_net": daily, "daily_gross": result.gross_returns[measured],
            "monthly_net": monthly, "turnover": turnover, "cost": cost,
            "weights": result.holdings.loc[target.index],
            "annual_turnover": float(turnover.mean() * ANNUAL_ROWS),
            "annual_cost_drag": float(cost.mean() * ANNUAL_ROWS),
            "initial_purchase_cost": float(cost.loc[first]),
            "terminal_rebalance_cost": float(cost.loc[last]),     # TIMING-012: the reset at end earns nothing
            "held_events": {"count": len(held), "weight_sum": float(sum(weights)),
                            "weight_max": float(max(weights, default=0.0))}}


def active_summary(cw: dict[str, Any], tilt: dict[str, Any]) -> dict[str, Any]:
    daily = tilt["daily_net"] - cw["daily_net"]
    monthly = tilt["monthly_net"] - cw["monthly_net"]
    return {"daily": daily, "monthly": monthly, "mean_monthly": float(monthly.mean()),
            "realized_te_daily": float(daily.std(ddof=1) * math.sqrt(ANNUAL_ROWS)),
            "realized_te_monthly": float(monthly.std(ddof=1) * math.sqrt(12)) if len(monthly) > 1 else None}


def sign(value: float) -> int:
    return 0 if value == 0.0 else (1 if value > 0.0 else -1)


def run_index_tilt(inputs: TiltInputs, schedule: tuple = COST_SCHEDULE, g: float | None = None) -> dict[str, Any]:
    """Every book at both cost scales and both event runs, from one set of targets; ``g`` adds ``lowrisk``."""
    built = build_targets(inputs, g)
    calendar = inputs.prices.index
    runs = {}
    for case, scale in COST_SCALES.items():
        costs = dated_cost_frame(calendar, schedule, scale)
        for event_run in EVENT_RUNS:
            events = terminal_events(built["disappearances"], calendar, event_run)
            books = {book: book_summary(run_book(inputs, target, events, costs), target)
                     for book, target in built["targets"].items()}
            runs[(case, event_run)] = {**books, "active": active_summary(books["cw"], books["tilt"])}
            if g is not None:
                runs[(case, event_run)]["lowrisk_active"] = active_summary(books["cw"], books["lowrisk"])
    actives = ("active",) if g is None else ("active", "lowrisk_active")
    fragility = {active: {case: sign(runs[(case, "primary")][active]["mean_monthly"])
                          != sign(runs[(case, "last_close")][active]["mean_monthly"]) for case in COST_SCALES}
                 for active in actives}
    out = {"timing": TIMING_CONTRACT, "targets": built["targets"], "rebalances": built["rebalances"],
           "counts": built["counts"], "runs": runs, "fragile_active_sign": fragility["active"]}
    if g is not None:
        out["fragile_lowrisk_active_sign"] = fragility["lowrisk_active"]
    return out
