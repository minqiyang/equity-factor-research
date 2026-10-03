"""Milestone 5.5: the cap-weight book (CW-PIT) and the index-tilt book (TILT) on point-in-time members.

Card m55-engine (owner decision O-17) builds the engine of the index-tilt design
note, sections 1 and 2. This module reads no data and writes no report; the
tests drive it with synthetic fixtures only.

Timing ``after_close_signal_next_observed_close_v1``: at each month-end
rebalance row ``r``, the cap weights, the scores, the eligibility, and the
tracking-error covariance use rows up to ``r - 1`` only. Both books trade at
the close of row ``r`` and earn from row ``r + 1``.

Both books run on the long-only engine of ``backtest.portfolio`` with
``weighting_scheme="proportional"`` and ``top_pct=1.0``, so the target weights
pass through unchanged. Costs (R8), terminal events (R4), point-in-time
membership (R2), and halts (``halt_gap_return_v1``) use the Milestone 5
accounting. One event set serves both books.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

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
    holds a later row in a later month.
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
    if not all(dtype == bool for dtype in inputs.eligible.dtypes):
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
    """2u - 1 with u = (average rank - 1) / (n - 1); a single value gets 0.

    The form (2 rank - n - 1) / (n - 1) has an exact numerator, so mirror ranks
    give exactly opposite values and a balanced composite is exactly zero.
    """
    if len(values) == 1:
        return pd.Series(0.0, index=values.index)
    n = float(len(values))
    return (2.0 * values.rank(method="average") - n - 1.0) / (n - 1.0)


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
    parts = []
    for signal_id in SIGNAL_IDS:
        valid = signal_rows[signal_id].dropna()
        parts.append(signed_ranks(valid).reindex(full_history.index))
    frame = pd.concat(parts, axis=1)
    count = frame.notna().sum(axis=1)
    few = count < MIN_VALID_SIGNALS
    incomplete = ~full_history
    # fsum is exactly rounded, so the mean is exactly zero when the signed ranks cancel.
    raw = pd.Series([math.fsum(row[~np.isnan(row)].tolist()) for row in frame.to_numpy(dtype=float)],
                    index=frame.index) / count.where(count > 0, 1)
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


def tilt_weights(b: pd.Series, c: pd.Series, window: pd.DataFrame, pinned: pd.Series) -> tuple[pd.Series, dict]:
    """Tilt, cap, renormalize, and scale, in that order.

    Pinned members (c = 0 for any cause, or no complete covariance window) keep
    ``w = b`` exactly; only the other members absorb the active budget. Each pass
    caps ``|w - b|`` at ``STOCK_CAP`` and rescales the free weights so their sum
    equals the free cap weight, so active weights sum to zero and ``w >= 0``.
    The loop ends when the cap holds within ``CAP_TOLERANCE`` and refuses after
    ``RENORMALIZE_LOOPS`` passes. The last step mixes ``w`` with ``b`` until the
    ex-ante TE of the active weights is at most ``TE_TARGET``.
    """
    bv, cv = b.to_numpy(dtype=float), c.to_numpy(dtype=float)
    if np.any(cv[pinned.to_numpy(dtype=bool)] != 0.0):
        raise refuse("pinned_member_scored")
    free = cv != 0.0          # c = 0 for any cause, natural zeros included, keeps w = b
    w = bv * (1.0 + TILT_STRENGTH * cv)
    for loops in range(1, RENORMALIZE_LOOPS + 1):
        w = bv + np.clip(w - bv, -STOCK_CAP, STOCK_CAP)
        if free.any():
            w[free] = w[free] * (math.fsum(bv[free]) / math.fsum(w[free]))
        if np.max(np.abs(w - bv)) <= STOCK_CAP + CAP_TOLERANCE:
            break
    else:
        raise refuse("tilt_loop_not_converged", f"{RENORMALIZE_LOOPS} passes")
    returns = window.to_numpy(dtype=float)[:, free]
    te_before = tracking_error(returns, (w - bv)[free])
    scale = 1.0 if te_before <= TE_TARGET else TE_TARGET / te_before
    final = (1.0 - scale) * bv + scale * w
    te_after = tracking_error(returns, (final - bv)[free])
    if te_after > TE_TARGET * (1.0 + TE_TOLERANCE):
        raise refuse("tracking_error_above_target", f"{te_after}")
    info = {"loops": loops, "ex_ante_te_before_scale": te_before, "te_scale": scale, "ex_ante_te": te_after,
            "max_abs_active": float(np.max(np.abs(final - bv)))}
    check_target(bv, final, info)
    return pd.Series(final, index=b.index), info


def check_target(b: np.ndarray, w: np.ndarray, info: Mapping[str, float]) -> None:
    """Refuse unless both books are finite, sum to 1, are non-negative, meet the cap, and meet the TE limit."""
    for name, weights in (("cw", b), ("tilt", w)):
        if not np.isfinite(weights).all() or (weights < 0.0).any():
            raise refuse("target_invalid", f"{name} weights not finite and non-negative")
        if abs(math.fsum(weights.tolist()) - 1.0) > BUDGET_TOLERANCE:
            raise refuse("target_invalid", f"{name} weights do not sum to 1")
    if not all(math.isfinite(float(v)) for v in info.values()):
        raise refuse("target_invalid", "non-finite tracking-error record")
    if np.max(np.abs(w - b)) > STOCK_CAP + CAP_TOLERANCE or info["ex_ante_te"] > TE_TARGET * (1.0 + TE_TOLERANCE):
        raise refuse("target_invalid", "cap or tracking-error limit")


def rebalance_targets(inputs: TiltInputs, date: pd.Timestamp, returns: pd.DataFrame, disappearances: pd.DataFrame,
                      first_return: pd.Series) -> tuple[pd.Series, pd.Series, dict[str, Any]]:
    """CW-PIT and TILT targets for the rebalance at ``date``, from row ``r - 1`` and earlier only.

    ``first_return`` is each member's first row with a valid return (the row
    count when it has none). It is compared only with rows up to ``r - 1``.
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
    if surprise & set(names):
        # Declared execution rule: a target member that settles at r on an event unknown at r - 1 refuses.
        raise refuse("event_unknown_at_cutoff", f"{str(date.date())}: {sorted(surprise & set(names))[0]}")
    me_members = me[names]
    b = me_members / math.fsum(me_members.to_list())
    first = t - COV_ROWS + 1
    window = returns.iloc[max(first, 0):t + 1][names]
    full = window.notna().sum() == COV_ROWS
    short = first_return[names] > first      # no valid return before the window: a short history, not a gap
    c, zero_counts = composite_scores({s: inputs.signals[s].iloc[t][names] for s in SIGNAL_IDS}, full, short)
    w, info = tilt_weights(b, c, window, ~full)
    record = {"date": date, "members": len(names), "settled_excluded": int((inputs.eligible.iloc[t] & ~pool).sum()),
              "me_missing": int(len(reasons)),
              **{f"me_missing_{r}": int((reasons == r).sum()) for r in ME_REASONS}, **zero_counts, **info}
    return b, w, record


def build_targets(inputs: TiltInputs) -> dict[str, Any]:
    check_inputs(inputs)
    disappearances = check_disappearances(inputs.disappearances, inputs.prices.index, inputs.prices.columns)
    returns = simple_returns(inputs.prices)
    valid = returns.notna().to_numpy()
    first_return = pd.Series(np.where(valid.any(axis=0), valid.argmax(axis=0), len(returns)), index=returns.columns)
    dates = rebalance_dates(inputs.prices.index, inputs.start, inputs.end)
    if not len(dates):
        raise refuse("window_invalid", "no rebalance inside the window")
    targets = {book: pd.DataFrame(np.nan, index=dates, columns=inputs.prices.columns) for book in BOOKS}
    records = []
    for date in dates:
        b, w, record = rebalance_targets(inputs, date, returns, disappearances, first_return)
        targets["cw"].loc[date, b.index] = b.to_numpy()
        targets["tilt"].loc[date, w.index] = w.to_numpy()
        records.append(record)
    table = pd.DataFrame(records).set_index("date")
    counts = {key: int(table[key].sum()) for key in table.columns
              if key.startswith("me_missing") or key.startswith("c_zero") or key == "settled_excluded"}
    return {"targets": targets, "rebalances": table, "counts": counts, "disappearances": disappearances}


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
    """Measured rows run from the first rebalance row to ``end``; the all-cash rows before it are left out."""
    first, last = target.index[0], target.index[-1]
    measured = result.returns.index >= first
    daily = result.returns[measured]
    turnover, cost = result.turnover[measured], result.total_trading_costs[measured]
    held = [r for r in result.terminal_event_log if float(r["incoming_weight"]) > 0.0]
    weights = [float(r["incoming_weight"]) for r in held]
    return {"daily_net": daily, "daily_gross": result.gross_returns[measured],
            "monthly_net": monthly_returns(daily), "turnover": turnover, "cost": cost,
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


def run_index_tilt(inputs: TiltInputs, schedule: tuple = COST_SCHEDULE) -> dict[str, Any]:
    """Both books at both cost scales and both event runs, from one set of targets."""
    built = build_targets(inputs)
    calendar = inputs.prices.index
    runs = {}
    for case, scale in COST_SCALES.items():
        costs = dated_cost_frame(calendar, schedule, scale)
        for event_run in EVENT_RUNS:
            events = terminal_events(built["disappearances"], calendar, event_run)
            books = {book: book_summary(run_book(inputs, built["targets"][book], events, costs), built["targets"][book])
                     for book in BOOKS}
            runs[(case, event_run)] = {**books, "active": active_summary(books["cw"], books["tilt"])}
    fragility = {case: sign(runs[(case, "primary")]["active"]["mean_monthly"])
                 != sign(runs[(case, "last_close")]["active"]["mean_monthly"]) for case in COST_SCALES}
    return {"timing": TIMING_CONTRACT, "targets": built["targets"], "rebalances": built["rebalances"],
            "counts": built["counts"], "runs": runs, "fragile_active_sign": fragility}
