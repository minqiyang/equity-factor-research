"""Milestone 5 step 4: the price-class bridge on point-in-time S&P 500 books.

Run with ``PYTHONPATH=src .venv/bin/python -m research.m5_step4 --snapshot-dir <dir> --reason "<why>"``.
The command implements ``docs/preregistrations/m5_trial_family_v1_amendment_4.json``
revision 2 on top of v1 and amendments 1 to 3. It refuses unless the five trial
files equal HEAD and their pins, the public cache matches the committed public
manifest, and the ``real_v2`` snapshot matches its pins.

Chain: six Family A sleeves per segment (top quintile, equal weight, month-end
rebalance on the engine's after-close contract, ``halt_gap_return_v1``), every
residual held stop settled at the R4 adverse default (-100 percent) with a
last-close rerun, and a class layer that holds the six sleeves under R0, rule
R1 (1/sigma of each sleeve's own daily net return over the 126 rows ending at
month t-2), and R2 (rule R1 tilted by the step 3 multipliers). The class layer
executes at the month t-1 close and earns month t (invariant R1).

Outputs: ``reports/m5_step4.md``, ``reports/m5_step4.json`` (aggregates only, R11),
and one start and one end record per attempt in ``reports/m5_step4_attempts.jsonl``.
Nothing is written inside the snapshot, and nothing under its ``terminal/``
directory is read. Evidence ceiling ``DIAGNOSTIC_ONLY``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from data.holdout_partition import PARTITION_RULE_V2, SnapshotRefusal, read_seal_carry, sha256_bytes
from data.public_factors import MonthlyPanel, PublicDataRefusal, read_fred_csv, sha256_file
from features.multiple_testing import adjust_pvalues
from research import m5_factor_baseline as base
from research import m5_step3 as step3
from research import m4_7_sp500_pit_rerun as runner
from research.m4_7_common_support import SupportSchedule, residual_bound_events
from research.m4_7_family_a import FAMILY_A_IDS, family_a_signals
from research.m4_7_terminal_evidence import snapshot_segments
from research.m4_7_universe_build import (
    BUILD_MANIFEST,
    INTERVAL_CSV,
    INTERVAL_RESULTS,
    INVENTORY,
    SECURITY_MASTER,
    Snapshot,
    discovery_inputs_sha256,
    read_derived_json,
    require_current,
)


REPO_ROOT = base.REPO_ROOT
AMENDMENT_4_PATH = "docs/preregistrations/m5_trial_family_v1_amendment_4.json"
AMENDMENT_4_SHA256 = "c2b1f8dea064ef1852d55bfda365faef8bd1c658897877037aae2fc0714ac617"
TRIAL_PINS = {**step3.TRIAL_PINS, AMENDMENT_4_PATH: AMENDMENT_4_SHA256}
PUBLIC_MANIFEST_SHA256 = "ba025b1a67af175dfff892c3dcefe96b573f7542b6d365dcdc783353c2af998f"
REPORT_MD = "reports/m5_step4.md"
REPORT_JSON = "reports/m5_step4.json"
ATTEMPTS_JSONL = "reports/m5_step4_attempts.jsonl"

SNAPSHOT_ID = "real_v2"
SEAL_CARRY_FILE = "holdout_seal_v2.json"
SNAPSHOT_PINS = {
    "manifest.json": "b8e5bf478dbeb7e2c69d4167ba77cf2dd74d0b19230ebe16e7d7df20bbf5fbee",
    INVENTORY: "125fb53b14d05c19704b725b55598750b14f7660e16d2210cf2e1dac58d43d3b",
    SEAL_CARRY_FILE: "4047106596a06aad4ff3cd0da2a6a30bc202ac0ae0c78b33a9fb1b7cb4fcb741",
    BUILD_MANIFEST: "f2fdb938eaa032d17ec887acba7274141bf261af01bd9375eef2c78570ad7253",
    INTERVAL_CSV: "64faa0b5752c63ad195c249b22065eb136451df4852aa7a4990a3fb38fb60ba9",
    INTERVAL_RESULTS: "1cf096b30189a3073aa4d6097cfaa35c8e19545510f49152138276a6b66df05f",
    SECURITY_MASTER: "a54d98c36ee66ee41b7becc694341fc7244c46c4fcd9a216f4b21f00fd80d6c6",
}
DISCOVERY_INPUTS_SHA256 = "0583ba8c6d3466fab8a76e7229d9aacff92046af57598b5f7659e8a439f7bc52"
DECLARED = {"partition_rule": PARTITION_RULE_V2, "discovery_layout": "side_partitioned_discovery_v1",
            "calendar_source": "SPY.US_eod_dates_v1", "d0_pre": "2014-04-30"}
SEAL_WINDOW = ("2019-07-31", "2020-07-31")
SEGMENT_DATES = {
    "pre": {"side": "discovery_pre", "anchor_row": "2014-04-29", "first_reset": "2014-04-30",
            "last_ic_reset": "2019-05-31", "last_book_row": "2019-06-28"},
    "post": {"side": "discovery_post", "anchor_row": "2021-08-30", "first_reset": "2021-08-31",
             "last_ic_reset": "2026-07-31", "last_book_row": "2026-08-07"},
}
SEGMENTS = ("pre", "post")
HALF_KEY = {"pre": "first_half", "post": "second_half"}

SLEEVES = {  # signal -> (matched JKP characteristic, JKP theme)
    "MOM_12_1": ("ret_12_1", "Momentum"),
    "HIGH_52W": ("prc_highprc_252d", "Momentum"),
    "REV_1M": ("ret_1_0", "Short-Term Reversal"),
    "LOW_VOL_252": ("rvol_21d", "Low Risk"),
    "LOW_BETA_252": ("beta_60m", "Low Risk"),
    "AMIHUD_ILLIQ_63": ("ami_126d", "Size"),
}
THEMES = ("Momentum", "Short-Term Reversal", "Low Risk", "Size")
TOP_PCT = 0.20
SIGMA_ROWS = 126
CASES = ("primary", "sensitivity")
STOCK_COSTS = {"primary": runner.REGISTERED["costs"]["primary"],
               "sensitivity": runner.REGISTERED["costs"]["sensitivity_2x"]}
ZERO_COST = runner.REGISTERED["costs"]["zero_cost_diagnostic_only"]
SWITCH_BPS = {"primary": 20, "sensitivity": 50}
EVENT_RUNS = {"primary": -1.0, "last_close": 0.0}
RULES = ("R0", "R1", "R2")
OBSERVED_TESTS = 2
FAMILY_SIZE = 480
TOLERANCE = step3.TOLERANCE
HALT_POLICY = "halt_gap_return_v1"
EXIT_CLASSES = ("index_removal_still_trading", "delisting_candidate", "disappearance_outside_membership",
                "seal_gap_identity_split")
UNRESOLVED = "unresolved_no_permanent_id"
UNKNOWN = "unknown"
STAGE_D_PRE_UNPRICED = "111 of 448 members at D0_pre have no pre-side panel (Stage D count)"
VP2 = ("Premise VP-2 (the vendor's adjusted close applies each declared distribution) holds under owner decision "
       "O-9 for step 4 only; the M4.8 census measured S_D > 0.05 on 22.5 percent of eligible member-days.")


def refuse(reason: str, detail: str = "") -> runner.RunnerStop:
    return runner.RunnerStop(reason, detail)


# Snapshot binding and loading ------------------------------------------------------------

def bind_step4(snapshot_dir: Path, pins: dict[str, str] = SNAPSHOT_PINS, snapshot_id: str = SNAPSHOT_ID,
               discovery_inputs: str = DISCOVERY_INPUTS_SHA256, declared: dict[str, str] = DECLARED,
               seal_window: tuple[str, str] = SEAL_WINDOW) -> dict[str, Any]:
    """Every pre-load check of ``bind_snapshot_v3`` against amendment 4's pins, without census or terminal checks."""

    try:
        snapshot = Snapshot.open(snapshot_dir)
    except SnapshotRefusal as exc:
        raise refuse(exc.code, str(exc)) from exc
    root = snapshot.root
    if snapshot.partition_rule != declared["partition_rule"]:
        raise refuse("registration_invalid", f"snapshot partition rule {snapshot.partition_rule}")
    if snapshot.manifest.get("snapshot", {}).get("id") != snapshot_id:
        raise refuse("registration_invalid", "snapshot id")
    if snapshot.manifest.get("snapshot", {}).get("discovery_layout") != declared["discovery_layout"]:
        raise refuse("registration_invalid", "discovery layout")
    verified = {}
    for relative, pinned in pins.items():
        path = root / relative
        verified[relative] = path.read_bytes() if path.is_file() else b""
        if not path.is_file() or sha256_bytes(verified[relative]) != pinned:
            raise refuse("derived_artifact_stale", relative)
    inputs = discovery_inputs_sha256(snapshot)
    if inputs != discovery_inputs:
        raise refuse("derived_artifact_stale", "discovery_inputs")
    inventory = json.loads(verified[INVENTORY])
    try:
        require_current(snapshot, inventory.get("discovery_inputs_sha256"), INVENTORY)
        build = read_derived_json(root, BUILD_MANIFEST)
        require_current(snapshot, build.get("discovery_inputs_sha256"), BUILD_MANIFEST)
        carry = read_seal_carry(root)
        calendar = snapshot.calendar()
        segments = snapshot_segments(snapshot, calendar)
    except SnapshotRefusal as exc:
        raise refuse(exc.code, str(exc)) from exc
    if build.get("d0_pre") != declared["d0_pre"]:
        raise refuse("registration_invalid", "d0_pre")
    for record in inventory["files"]:
        path = root / "panel" / record["file"]
        if not path.is_file() or sha256_bytes(path.read_bytes()) != record["sha256"]:
            raise refuse("derived_artifact_stale", "panel file")
    runner._refuse_split_sources(root, inventory["files"])
    if (carry["holdout_start"], carry["holdout_end_exclusive"]) != seal_window:
        raise refuse("holdout_overlap_refused", "seal carry window differs from amendment 4")
    if snapshot.calendar_source != declared["calendar_source"]:
        raise refuse("registration_invalid", "calendar source")
    return {"snapshot": snapshot, "inputs": inputs, "inventory": inventory, "calendar": calendar,
            "segments": segments}


def empty_events() -> pd.DataFrame:
    return residual_bound_events((), pd.DatetimeIndex([]))


def load_segment_runs_step4(bound: dict[str, Any]) -> tuple[list[runner.SegmentRun], dict[str, list[str]]]:
    """``load_segment_runs`` without ``read_engine_events``: every segment gets an empty event frame."""
    return runner.load_side_runs(bound, empty_events())


def verify_pins_unchanged(snapshot_dir: Path, pins: dict[str, str] = SNAPSHOT_PINS) -> None:
    for relative, pinned in pins.items():
        if sha256_bytes((Path(snapshot_dir) / relative).read_bytes()) != pinned:
            raise refuse("snapshot_changed_during_run", relative)


# Segment preparation -------------------------------------------------------------------

@dataclass
class SegmentInputs:
    """One segment's prepared inputs on its own calendar (positions are segment-calendar rows)."""

    segment_id: str
    calendar: pd.DatetimeIndex
    full_calendar: pd.DatetimeIndex
    offset: int
    prices: pd.DataFrame
    spy: pd.Series
    signals: dict[str, pd.DataFrame]
    intervals: pd.DataFrame
    schedule: SupportSchedule
    residual: tuple[tuple[str, int, int], ...]
    split_close: pd.DataFrame | None = None   # research close (split-only) and cumulative split factor, for step 4b
    split_factor: pd.DataFrame | None = None

    @property
    def window(self) -> tuple[int, int]:
        return self.schedule.d0 - 1, self.schedule.d_last


def registered_rows(segment_id: str, dates: dict[str, dict[str, str]] = SEGMENT_DATES) -> dict[str, str]:
    return dates[segment_id]


def prepare(run: runner.SegmentRun, registered: dict[str, str],
            seal_window: tuple[str, str] = SEAL_WINDOW) -> SegmentInputs:
    """Segment support without labels or Family B; a Family A signal that raises refuses (OPUS-S4F-R2-A1)."""

    holdout = {"holdout_start": seal_window[0], "holdout_end_exclusive": seal_window[1]}
    support = runner.segment_support(run, registered, holdout, None)
    if len(support["events"]):
        raise refuse("terminal_evidence_refused", "step 4 accepts no terminal event")
    research = support["research"]
    try:
        signals = family_a_signals(support["prices"], support["spy"], research["dollar_volume"],
                                   support["schedule"].s_mask)
    except (ValueError, ArithmeticError) as exc:
        raise refuse("family_a_signal_failed", f"{run.segment.segment_id}: {type(exc).__name__}") from exc
    return SegmentInputs(segment_id=run.segment.segment_id, calendar=support["calendar"],
                         full_calendar=run.full_calendar, offset=run.segment.feature_floor_row,
                         prices=support["prices"], spy=support["spy"], signals=signals,
                         intervals=support["intervals"], schedule=support["schedule"],
                         residual=tuple(support["residual"]), split_close=research["close"],
                         split_factor=research["split_factor"])


def segment_events(seg: SegmentInputs, terminal_return: float) -> pd.DataFrame:
    events = residual_bound_events(seg.residual, seg.calendar)
    events["terminal_return"] = float(terminal_return)
    return events


def book_signal(seg: SegmentInputs, signal_id: str) -> pd.DataFrame:
    """The sleeve signal on the evaluation mask, as registration v3 books read it (segment_book_trial)."""
    return seg.signals[signal_id].where(seg.schedule.evaluation_mask)


def check_sleeve_targets(seg: SegmentInputs) -> None:
    """Refuse an empty sleeve target: a scheduled rebalance with no eligible member holding a finite signal."""

    rows = seg.schedule.evaluation_resets
    for signal_id in seg.signals:
        finite = np.isfinite(book_signal(seg, signal_id).to_numpy(dtype=float))
        empty = [int(r) for r in rows if not finite[int(r) - 1].any()]
        if empty:
            raise refuse("empty_sleeve_target", f"{seg.segment_id} {signal_id}: {len(empty)} rebalances")


def run_books(seg: SegmentInputs, terminal_return: float,
              signal_ids: tuple[str, ...] = FAMILY_A_IDS) -> dict[str, Any]:
    """Every sleeve in ``signal_ids`` at both cost cases and the equal-weight benchmark, for one event run."""

    check_sleeve_targets(seg)
    events = segment_events(seg, terminal_return)
    sleeves = {}
    for signal_id in signal_ids:
        for case in CASES:
            sleeves[(signal_id, case)] = runner.run_book(
                "long_only", seg.prices, book_signal(seg, signal_id), seg.calendar, seg.window, intervals=seg.intervals,
                events=events, cost=dict(STOCK_COSTS[case]), top_pct=TOP_PCT, missing_price_policy=HALT_POLICY)
    ew = runner.run_book("long_only", seg.prices, runner.equal_weight_signal(seg.schedule.evaluation_mask),
                         seg.calendar, seg.window, intervals=seg.intervals, events=events, cost=dict(ZERO_COST),
                         top_pct=1.0, missing_price_policy=HALT_POLICY)
    return {"sleeves": sleeves, "ew": ew, "events": events}


# Monthly series, sigma, and the class layer ------------------------------------------

def month_labels(seg: SegmentInputs) -> pd.Series:
    """Calendar-month label of each book row after the anchor; the first reset row joins the first sleeve month.

    The last month is kept only when the full calendar shows a later row in a
    later month, so a month cut off by the calendar's end enters no figure.
    """

    first = seg.schedule.d0
    rows = seg.calendar[first:seg.schedule.d_last + 1]
    labels = pd.Series(rows.to_period("M"), index=rows)
    labels.iloc[0] = labels.iloc[0] + 1
    last = seg.calendar[seg.schedule.d_last]
    later = seg.full_calendar[seg.full_calendar > last]
    if not len(later) or later[0].to_period("M") == last.to_period("M"):
        labels = labels[labels != last.to_period("M")]
    return labels


def compound_monthly(daily: pd.Series, labels: pd.Series) -> pd.Series:
    rows = daily.reindex(labels.index)
    if rows.isna().any():
        raise refuse("monthly_return_missing", f"{int(rows.isna().sum())} daily returns")
    monthly = (1.0 + rows).groupby(labels.to_numpy()).prod() - 1.0
    monthly.index = pd.PeriodIndex(monthly.index, freq="M")
    return monthly


def sleeve_months(seg: SegmentInputs) -> pd.PeriodIndex:
    return pd.PeriodIndex(sorted(set(month_labels(seg))), freq="M")


def own_sigma(daily: pd.Series, months: pd.PeriodIndex, first_row: pd.Timestamp) -> pd.Series:
    """ddof-1 volatility of the 126 daily net returns ending on the last trading day of month t-2.

    Rows start after ``first_row`` (the segment's first reset row); a month with
    fewer than 126 such rows has no sigma.
    """

    rows = daily[daily.index > first_row]
    periods = rows.index.to_period("M")
    values = rows.to_numpy(dtype=float)
    out = {}
    for month in months:
        eligible = values[periods <= month - 2]
        out[month] = float(np.std(eligible[-SIGMA_ROWS:], ddof=1)) if len(eligible) >= SIGMA_ROWS else np.nan
    return pd.Series(out, dtype=float)


def drift_portfolio(weights: pd.DataFrame, returns: pd.DataFrame, bps: float) -> pd.DataFrame:
    """Class layer with drift-adjusted turnover; the first month starts from cash (turnover 1).

    turnover_t = sum_s |w_s,t - wd_s,t-1|, wd_s,t-1 = w_s,t-1 (1 + r_s,t-1) / (1 + sum_j w_j,t-1 r_j,t-1);
    r_net,t = sum_s w_s,t r_s,t - bps / 10000 * turnover_t.
    """

    held = returns.loc[weights.index, weights.columns]
    if held.isna().to_numpy().any():
        raise refuse("monthly_return_missing", "a sleeve month without a return")
    w, r = weights.to_numpy(dtype=float), held.to_numpy(dtype=float)
    gross = (w * r).sum(axis=1)
    turnover = np.empty(len(w))
    for t in range(len(w)):
        if t == 0:
            turnover[t] = np.abs(w[0]).sum()
        else:
            drifted = w[t - 1] * (1.0 + r[t - 1]) / (1.0 + gross[t - 1])
            turnover[t] = np.abs(w[t] - drifted).sum()
    net = gross - bps / 10_000.0 * turnover
    return pd.DataFrame({"gross": gross, "turnover": turnover, "net": net}, index=weights.index)


def sharpe_long_only(net: pd.Series, rf: pd.Series) -> float | None:
    """12 * mean(r_net - RF) / (sqrt(12) * sd(r_net)), ddof 1; a month without RF refuses."""

    free = rf.reindex(net.index)
    if free.isna().any():
        raise refuse("risk_free_missing", f"{int(free.isna().sum())} months")
    volatility = float(net.std(ddof=1)) * math.sqrt(12)
    if not volatility > 0:
        return None
    return float((net - free).mean()) * 12 / volatility


def metrics(net: pd.Series, rf: pd.Series, turnover: pd.Series | None = None) -> dict[str, Any]:
    out = base.performance(net, turnover)
    out["sharpe"] = sharpe_long_only(net, rf)
    return out


def theme_multipliers(r2_multipliers: pd.DataFrame, months: pd.PeriodIndex) -> pd.DataFrame:
    """The step 3 R2 multipliers of the four themes, one column per sleeve; a missing month refuses."""

    missing = [str(m) for m in months if m not in r2_multipliers.index]
    frame = r2_multipliers.reindex(months)[[SLEEVES[s][1] for s in FAMILY_A_IDS]]
    if missing or frame.isna().to_numpy().any():
        raise refuse("r2_multiplier_missing", f"{len(missing) or int(frame.isna().to_numpy().sum())} months")
    frame.columns = list(FAMILY_A_IDS)
    return frame


def rule_weights(sigma: pd.DataFrame, multipliers: pd.DataFrame | None) -> dict[str, pd.DataFrame]:
    """R0 and rule R1 weights, and R2 unless ``multipliers`` is ``None`` (step 4b runs no R2)."""

    in_set = pd.DataFrame(True, index=sigma.index, columns=sigma.columns)
    try:
        w0 = base.rule_weights("R0", in_set, sigma)
        w1 = base.rule_weights("R1", in_set, sigma)
    except PublicDataRefusal as exc:
        raise refuse("sigma_degenerate", str(exc)) from exc
    if multipliers is None:
        return {"R0": w0, "R1": w1}
    w2 = step3.tilt(w1, multipliers.reindex_like(w1), in_set)
    return {"R0": w0, "R1": w1, "R2": w2}


def class_layer(monthly: dict[str, pd.DataFrame], sigma: dict[str, pd.DataFrame], multipliers: pd.DataFrame | None,
                last_month: pd.Period) -> dict[str, Any]:
    """Comparison months, weights, and rule books for one segment and event run, per cost case.

    ``multipliers`` ``None`` builds R0 and rule R1 only, over whatever sleeves ``monthly`` holds (step 4b).
    """

    out: dict[str, Any] = {}
    for case in CASES:
        sig = sigma[case]
        defined = sig.notna().all(axis=1)
        months = sig.index[defined.to_numpy() & (sig.index <= last_month)]
        if not len(months):
            raise refuse("comparison_window_empty", case)
        months = pd.period_range(months[0], months[-1], freq="M")
        if not defined.reindex(months).fillna(False).all():
            raise refuse("sigma_gap", case)
        weights = rule_weights(sig.loc[months], None if multipliers is None else theme_multipliers(multipliers, months))
        books = {rule: drift_portfolio(weights[rule], monthly[case], SWITCH_BPS[case]) for rule in weights}
        out[case] = {"months": months, "weights": weights, "books": books}
    return out


def class_returns(monthly: pd.DataFrame, sigma: pd.DataFrame, months: pd.PeriodIndex,
                  sleeves: dict[str, tuple[str, str]] = SLEEVES, themes: tuple[str, ...] = THEMES) -> pd.DataFrame:
    """Rule R1 within each theme on the sleeves (descriptive)."""

    inverse = 1.0 / sigma.loc[months]
    values = {}
    for theme in themes:
        members = [s for s in sleeves if sleeves[s][1] == theme]
        values[theme] = (inverse[members] * monthly.loc[months, members]).sum(axis=1) / inverse[members].sum(axis=1)
    return pd.DataFrame(values)


# Decision predicates ------------------------------------------------------------------

def conditions(candidate: dict[str, dict[str, dict]], comparator: dict[str, dict[str, dict]]) -> list[dict]:
    """The 8 step 2 conditions through ``closure_conditions``: segments as halves, cost cases as 20 and 50 bp."""

    grid = {name: {f"{SWITCH_BPS[case]}bp": {HALF_KEY[s]: books[case][s] for s in SEGMENTS} for case in CASES}
            for name, books in (("R1", comparator), ("candidate", candidate))}
    rows = step3.closure_conditions(grid, "candidate", [SWITCH_BPS[c] for c in CASES])
    case_of = {SWITCH_BPS[c]: c for c in CASES}
    segment_of = {v: k for k, v in HALF_KEY.items()}
    return [{"segment": segment_of[row["period"]], "cost_case": case_of[row["cost_bps"]], "metric": row["metric"],
             "candidate": row["rule"], "comparator": row["R1"], "margin": row["margin"], "holds": row["holds"]}
            for row in rows]


def holds_all(rows: list[dict]) -> bool:
    return step3.closure_decision([{"holds": r["holds"]} for r in rows]) == "open"


def decide(cond: dict[str, list[dict]]) -> dict[str, Any]:
    baseline = "R1" if holds_all(cond["R1_vs_R0"]) else "R0"
    r2_ok = holds_all(cond["R2_vs_R1"]) and (baseline == "R1" or holds_all(cond["R2_vs_R0"]))
    return {"baseline": baseline, "r2": "continues" if r2_ok else "closed",
            "r2_label": "no evidence of state timing" if r2_ok else None,
            "counts": {key: sum(r["holds"] for r in rows) for key, rows in cond.items()}}


def sign(value: float | None) -> int | None:
    if value is None or not math.isfinite(value):
        return None
    return 0 if abs(value) < TOLERANCE else (1 if value > 0 else -1)


def fragility(primary: dict[str, Any], other: dict[str, Any]) -> dict[str, Any]:
    """Fragile when any S4 mean sign, closure margin sign, or decision outcome differs between the runs."""

    flips = []
    for test_id in primary["s4_means"]:
        if sign(primary["s4_means"][test_id]) != sign(other["s4_means"][test_id]):
            flips.append(test_id)
    keys = ["R1_vs_R0", "R2_vs_R1"]
    if "R0" in (primary["decision"]["baseline"], other["decision"]["baseline"]):
        keys.append("R2_vs_R0")
    for key in keys:
        for a, b in zip(primary["conditions"][key], other["conditions"][key]):
            if sign(a["margin"]) != sign(b["margin"]):
                flips.append(f"{key}:{a['segment']}:{a['cost_case']}:{a['metric']}")
    outcome = [k for k in ("baseline", "r2") if primary["decision"][k] != other["decision"][k]]
    return {"fragile": bool(flips or outcome), "sign_changes": flips, "outcome_changes": outcome}


def s4_family(pvalues: pd.Series, family_size: int = FAMILY_SIZE) -> pd.Series:
    if len(pvalues) != OBSERVED_TESTS or family_size != FAMILY_SIZE:
        raise refuse("s4_family_invalid", f"{len(pvalues)} observed, family size {family_size}")
    return adjust_pvalues(pvalues, method="by", family_size=family_size)


def ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or not denominator > 0:
        return None
    return numerator / denominator


def correlation(a: pd.Series, b: pd.Series) -> float | None:
    if len(a) < 2 or a.std(ddof=1) == 0 or b.std(ddof=1) == 0:
        return None
    return float(np.corrcoef(a.to_numpy(dtype=float), b.to_numpy(dtype=float))[0, 1])


# Affected events ------------------------------------------------------------------------

def held_events(result: Any) -> list[dict[str, Any]]:
    return [{"pid": r["permanent_id"], "date": pd.Timestamp(r["effective_date"]), "weight": float(r["incoming_weight"])}
            for r in result.terminal_event_log if float(r["incoming_weight"]) > 0]


def book_event_summary(events: list[dict[str, Any]], seal_gap_ids: set[str], window: set[pd.Period]) -> dict:
    def summary(rows):
        weights = [r["weight"] for r in rows]
        return {"count": len(rows), "weight_sum": float(sum(weights)), "weight_max": float(max(weights, default=0.0))}
    inside = [r for r in events if r["date"].to_period("M") in window]
    return {"all": summary(events),
            "seal_gap": summary([r for r in events if r["pid"] in seal_gap_ids]),
            "other": summary([r for r in events if r["pid"] not in seal_gap_ids]),
            "outside_comparison_months": summary([r for r in events if r not in inside])}


def gross_growth_path(result: Any) -> pd.Series:
    """Cumulative gross growth of a sleeve: the path G_j of amendment 4 disappearances.affected_events.rule."""
    return (1.0 + result.gross_returns).cumprod()


def rule_event_summary(sleeve_events: dict[str, list[dict[str, Any]]], equity: dict[str, pd.Series],
                       weights: pd.DataFrame, calendar: pd.DatetimeIndex, seal_gap_ids: set[str]) -> dict:
    """Rule-level incoming weight: sum over holding sleeves of the drifted sleeve share times its incoming weight.

    Share_s = w_s,t G_s / sum_j w_j,t G_j with G_j the growth from the month-(t-1) close to the close of row s - 1.
    Each event (permanent ID, stop row) counts once; sleeve-event incidences are reported beside it.
    Events outside the class-layer months are out of scope here.
    """

    months = set(weights.index)
    unique: dict[tuple[str, pd.Timestamp], list[tuple[str, float]]] = {}
    for sleeve, rows in sleeve_events.items():
        for r in rows:
            if r["date"].to_period("M") in months:
                unique.setdefault((r["pid"], r["date"]), []).append((sleeve, r["weight"]))
    values, seal = [], []
    for (pid, day), holders in unique.items():
        month = day.to_period("M")
        prior = calendar[calendar.get_loc(day) - 1]
        month_start = calendar[calendar.to_period("M") < month][-1]
        growth = {s: float(equity[s].loc[prior] / equity[s].loc[month_start]) for s in weights.columns}
        total = sum(weights.loc[month, s] * growth[s] for s in weights.columns)
        value = sum(weights.loc[month, s] * growth[s] / total * w for s, w in holders)
        values.append(value)
        seal.append(pid in seal_gap_ids)
    incidences = sum(len(h) for h in unique.values())
    return {"unique_events": len(values), "incidences": incidences, "weight_sum": float(sum(values)),
            "weight_max": float(max(values, default=0.0)),
            "seal_gap_events": int(sum(seal)), "seal_gap_weight_sum": float(sum(v for v, s in zip(values, seal) if s))}


# Unpriced member-day accounting ------------------------------------------------------------

UNRESOLVED_REASONS = (("ambiguous_reuse", "identity_refusal"), ("no_containing_episode:no_vendor_bars", "no_vendor_bars"),
                      ("no_containing_episode:no_bars_in_interval", "no_bars_in_interval"),
                      ("entry_missing_field", "entry_missing_field"))


def _interval_key(value: str) -> tuple[int, int | str]:
    return (0, int(value)) if str(value).isdigit() else (1, str(value))


def member_rows(row: dict[str, Any], calendar: pd.DatetimeIndex) -> tuple[int, int] | None:
    """The build's member window [m_in, m_out) as full-calendar rows; ``None`` for an undated interval.

    The interval results store both bounds as calendar dates; a blank m_out is an
    open interval (the build's ``None``, read as the calendar length).
    """

    m_in, m_out = str(row.get("m_in", "")).strip(), str(row.get("m_out", "")).strip()
    if not m_in:
        return None
    start = int(calendar.get_loc(pd.Timestamp(m_in)))
    return start, len(calendar) if not m_out else int(calendar.get_loc(pd.Timestamp(m_out)))


def unpriced_share(intervals: pd.DataFrame, calendar: pd.DatetimeIndex, spans: dict[str, tuple[int, int, str]],
                   panels: dict[str, set[str]], quarantined: dict[str, set[str]],
                   refusals: dict[str, set[str]]) -> dict[str, Any]:
    """Member-days over each segment's [first reset, last book] rows against every interval (amendment 4).

    ``intervals`` holds interval_id, vendor_code, permanent_id, resolution, exit_class, m_in, m_out (dates on
    the full calendar, m_out blank for an open interval). ``spans`` maps segment -> (first_row, last_row, side);
    ``panels`` side -> permanent IDs with a side panel; ``quarantined`` side -> vendor codes whose EOD partition is
    quarantined; ``refusals`` side -> permanent IDs with an episode panel refusal on that side. A member-day is a
    row in [m_in, m_out) (the build's member window); overlapping intervals of one code count once, under the
    lowest interval_id. An undated interval is counted by interval with zero observed member-days, and an upper
    bound charges it the whole span as unpriced.
    """

    ordered = intervals.assign(_k=intervals["interval_id"].map(_interval_key)).sort_values("_k")
    out = {}
    for segment, (first, last, side) in spans.items():
        span = last - first + 1
        claimed: dict[str, np.ndarray] = {}
        priced = unpriced = 0
        by_class: dict[str, int] = {c: 0 for c in (*EXIT_CLASSES, UNRESOLVED, UNKNOWN)}
        by_reason: dict[str, int] = {}
        undated = 0
        for row in ordered.to_dict(orient="records"):
            window = member_rows(row, calendar)
            if window is None:
                undated += 1
                continue
            m_in, m_out = window
            lo, hi = max(m_in, first), min(m_out, last + 1)
            if hi <= lo:
                continue
            key = row["vendor_code"] or f"interval:{row['interval_id']}"
            taken = claimed.setdefault(key, np.zeros(span, dtype=bool))
            fresh = ~taken[lo - first:hi - first]
            days = int(fresh.sum())
            taken[lo - first:hi - first] = True
            if not days:
                continue
            pid, resolved = row["permanent_id"], row["resolution"] == "resolved"
            if resolved and pid in panels.get(side, set()):
                priced += days
                continue
            unpriced += days
            if resolved:
                klass = row["exit_class"] if row["exit_class"] in EXIT_CLASSES else UNKNOWN
                reason = ("eod_quarantine" if row["vendor_code"] in quarantined.get(side, set()) else
                          "episode_panel_refusal" if pid in refusals.get(side, set()) else "other")
            else:
                klass = UNRESOLVED
                reason = next((name for prefix, name in UNRESOLVED_REASONS if row["resolution"].startswith(prefix)),
                              "other")
            by_class[klass] += days
            by_reason[reason] = by_reason.get(reason, 0) + days
        denominator = int(sum(taken.sum() for taken in claimed.values()))
        reconcile(segment, denominator, priced, unpriced, by_class, by_reason)
        upper_unpriced, upper_denominator = unpriced + undated * span, denominator + undated * span
        out[segment] = {
            "span_rows": span, "denominator": denominator, "priced": priced, "unpriced": unpriced,
            "unpriced_share": unpriced / denominator if denominator else None,
            "by_exit_class": by_class, "by_reason": dict(sorted(by_reason.items())),
            "undated_intervals": undated,
            "unpriced_share_upper_bound": upper_unpriced / upper_denominator if upper_denominator else None,
        }
    return out


def reconcile(segment: str, denominator: int, priced: int, unpriced: int, by_class: dict[str, int],
              by_reason: dict[str, int]) -> None:
    """Priced plus unpriced equals the member-day count, and each split sums to the unpriced total."""
    if priced + unpriced != denominator or sum(by_class.values()) != unpriced or sum(by_reason.values()) != unpriced:
        raise refuse("unpriced_accounting_unreconciled", segment)


def exit_class_lookup(intervals: pd.DataFrame, calendar: pd.DatetimeIndex) -> dict[str, list[tuple[int, int, str]]]:
    """Permanent ID -> its resolved member windows and exit classes, for the exposure splits."""
    lookup: dict[str, list[tuple[int, int, str]]] = {}
    for row in intervals.to_dict(orient="records"):
        window = member_rows(row, calendar)
        if row["resolution"] != "resolved" or window is None:
            continue
        klass = row["exit_class"] if row["exit_class"] in EXIT_CLASSES else UNKNOWN
        lookup.setdefault(row["permanent_id"], []).append((*window, klass))
    return lookup


def classify(lookup: dict[str, list[tuple[int, int, str]]], pid: str, full_row: int) -> str:
    for m_in, m_out, klass in lookup.get(pid, []):
        if m_in <= full_row < m_out:
            return klass
    return UNKNOWN


def signal_exclusions(seg: SegmentInputs, lookup: dict | None) -> dict[str, Any]:
    """Eligible members without a finite signal at each rebalance's signal row, per sleeve, by exit class."""

    rows = [int(r) - 1 for r in seg.schedule.evaluation_resets]
    eligible = seg.schedule.evaluation_mask.to_numpy(dtype=bool)
    out = {}
    for signal_id in seg.signals:
        missing = eligible & ~np.isfinite(book_signal(seg, signal_id).to_numpy(dtype=float))
        per_rebalance = [int(missing[r].sum()) for r in rows]
        by_class: dict[str, int] = {}
        if lookup is not None:
            for r in rows:
                for column in np.flatnonzero(missing[r]):
                    klass = classify(lookup, seg.prices.columns[column], r + seg.offset)
                    by_class[klass] = by_class.get(klass, 0) + 1
        out[signal_id] = {"total": int(sum(per_rebalance)), "per_rebalance": per_rebalance,
                          "by_exit_class": dict(sorted(by_class.items()))}
    return out


def halt_counts(result: Any, seg: SegmentInputs, lookup: dict | None) -> dict[str, Any]:
    ledger = result.halt_ledger or {}
    rows = ledger.get("unmarked_halt_rows", [])
    by_class: dict[str, int] = {}
    if lookup is not None:
        for day, pid in rows:
            klass = classify(lookup, pid, int(seg.calendar.get_loc(pd.Timestamp(day))) + seg.offset)
            by_class[klass] = by_class.get(klass, 0) + 1
    return {"unmarked_halt_rows": len(rows), "locked_execution_rows": len(ledger.get("locked_execution_rows", [])),
            "by_exit_class": dict(sorted(by_class.items()))}


# Public inputs --------------------------------------------------------------------------

@dataclass
class PublicInputs:
    rf: pd.Series
    multipliers: pd.DataFrame
    class_values: pd.DataFrame
    jkp: pd.DataFrame
    nets: dict[str, dict[str, pd.Series]]
    last_month: pd.Period
    manifest: list[dict[str, Any]]


def load_public(repo_root: Path, sleeves: dict[str, tuple[str, str]] = SLEEVES,
                themes: tuple[str, ...] = THEMES) -> PublicInputs:
    """Step 2 and step 3 public inputs from the cache; any source missing or unlike the committed manifest refuses.

    ``jkp`` holds the matched characteristic of each sleeve in ``sleeves`` and ``class_values`` each theme in
    ``themes`` (step 4b passes its nine sleeves and adds Value and Quality).
    """

    manifest_path = repo_root / base.MANIFEST_JSON
    if sha256_file(manifest_path) != PUBLIC_MANIFEST_SHA256:
        raise refuse("public_manifest_changed", base.MANIFEST_JSON)
    committed = {e["id"]: e for e in json.loads(manifest_path.read_text(encoding="utf-8"))["sources"]}
    trial = json.loads((repo_root / base.TRIAL_PATH).read_bytes())
    cache_dir = repo_root / base.CACHE_DIR
    for source in trial["data_sources"]:
        path = base._cache_path(cache_dir, source)
        if not path.is_file() or not path.with_name(path.name + ".retrieval.json").is_file():
            raise refuse("public_cache_missing", source["id"])
    inputs = base.load_inputs(trial, cache_dir)
    fred_source = next(s for s in trial["data_sources"] if s["id"] == "fred_baa_aaa_monthly")
    fred = read_fred_csv(base._cache_path(cache_dir, fred_source), series=list(fred_source["series"]))
    extra = step3.load_step3_sources(trial, cache_dir)
    entries = inputs["manifest"] + extra["entries"]
    for entry in entries:
        if committed.get(entry["id"], {}).get("sha256") != entry["sha256"]:
            raise refuse("public_cache_changed", entry["id"])
    data = step3.assemble_data(inputs, fred, extra, trial)
    built = step3.build_rules(data, trial)
    costs = [SWITCH_BPS[c] for c in CASES]
    step2 = base.run_universe(MonthlyPanel(built["returns"], built["missing"], 0), data.first, data.last, trial,
                              data.market_monthly["Mkt-RF"], costs)
    if step2["status"] != "completed" or not step2["_member"].in_set.equals(built["in_set"].loc[built["months"]]):
        raise refuse("public_rules_refused", str(step2.get("reason", "set mismatch")))
    nets = {rule: {} for rule in RULES}
    for case in CASES:
        cost = SWITCH_BPS[case]
        nets["R0"][case] = step2["_series"][("R0", cost)]
        nets["R1"][case] = step2["_series"][("R1", cost)]
        nets["R2"][case] = base.portfolio(built["weights"]["R2"], built["returns"], cost)["net"]
    jkp = inputs["panels"]["jkp_usa_all_factors_monthly_vw_cap"].values[[sleeves[s][0] for s in sleeves]]
    return PublicInputs(rf=inputs["panels"]["french_ff3_monthly"].values["RF"],
                        multipliers=built["r2"]["multipliers"], class_values=built["class_values"][list(themes)],
                        jkp=jkp, nets=nets, last_month=data.last, manifest=entries)


# Evaluation ------------------------------------------------------------------------------

def excess(net: pd.Series, reference: pd.Series) -> dict[str, float]:
    ref = reference.reindex(net.index)
    return {"annualized_mean_excess": float((net - ref).mean() * 12),
            "excess_total_return": float((1 + net).prod() - (1 + ref).prod())}


def segment_series(seg: SegmentInputs, books: dict[str, Any], public: PublicInputs) -> dict[str, Any]:
    """Monthly sleeve, benchmark, and sigma series of one segment and event run, and its class layer.

    Every series compounds over the same rows: the first sleeve month includes the
    first reset row, and the benchmarks compound the same way (amendment 4
    sleeves.monthly_return).
    """

    labels_first = month_labels(seg)
    first_row = seg.calendar[seg.schedule.d0]
    months = sleeve_months(seg)
    monthly, daily_sigma = {}, {}
    for case in CASES:
        frame, sig = {}, {}
        for signal_id in FAMILY_A_IDS:
            result = books["sleeves"][(signal_id, case)]
            frame[signal_id] = compound_monthly(result.returns, labels_first)
            sig[signal_id] = own_sigma(result.returns, months, first_row)
        monthly[case], daily_sigma[case] = pd.DataFrame(frame), pd.DataFrame(sig)
    ew = compound_monthly(books["ew"].returns, labels_first)
    spy = compound_monthly(seg.spy.pct_change(fill_method=None), labels_first)
    layer = class_layer(monthly, daily_sigma, public.multipliers, public.last_month)
    return {"books": books, "monthly": monthly, "sigma": daily_sigma, "ew": ew, "spy": spy, "layer": layer,
            "sleeve_months": months, "sleeve_rows": labels_first.index}


def evaluate_run(segments: dict[str, SegmentInputs], public: PublicInputs, terminal_return: float,
                 seal_gap_ids: set[str], lookup: dict | None) -> dict[str, Any]:
    """One event run: sleeves, benchmarks, class layer, conditions, and descriptive tables."""

    seg_out = {sid: segment_series(seg, run_books(seg, terminal_return), public) for sid, seg in segments.items()}

    grid = {rule: {case: {sid: metrics(seg_out[sid]["layer"][case]["books"][rule]["net"], public.rf,
                                       seg_out[sid]["layer"][case]["books"][rule]["turnover"])
                          for sid in segments} for case in CASES} for rule in RULES}
    cond = {"R1_vs_R0": conditions(grid["R1"], grid["R0"]), "R2_vs_R1": conditions(grid["R2"], grid["R1"]),
            "R2_vs_R0": conditions(grid["R2"], grid["R0"])}
    decision = decide(cond)

    public_grid = {rule: {case: {sid: base.performance(public.nets[rule][case].loc[
        seg_out[sid]["layer"][case]["months"][0]:seg_out[sid]["layer"][case]["months"][-1]]) for sid in segments}
        for case in CASES} for rule in RULES}
    public_cond = {"R1_vs_R0": conditions(public_grid["R1"], public_grid["R0"]),
                   "R2_vs_R1": conditions(public_grid["R2"], public_grid["R1"]),
                   "R2_vs_R0": conditions(public_grid["R2"], public_grid["R0"])}
    survival = {key: [{**row, "public_margin": pub["margin"], "public_holds": pub["holds"],
                       "margin_ratio": ratio(row["margin"], pub["margin"])} for row, pub in zip(rows, public_cond[key])]
                for key, rows in cond.items()}

    diffs = {}
    for test_id, (a, b) in {"S4.R1": ("R1", "R0"), "S4.R2": ("R2", "R1")}.items():
        parts = [seg_out[sid]["layer"]["primary"]["books"][a]["net"] - seg_out[sid]["layer"]["primary"]["books"][b]["net"]
                 for sid in SEGMENTS if sid in segments]
        diffs[test_id] = pd.concat(parts)
    s4_means = {k: float(v.mean()) for k, v in diffs.items()}

    tables = describe(segments, seg_out, public, seal_gap_ids, lookup, grid)
    return {"seg": seg_out, "grid": grid, "conditions": cond, "survival": survival, "decision": decision,
            "public_grid": public_grid, "diffs": diffs, "s4_means": s4_means, "tables": tables}


def describe(segments: dict[str, SegmentInputs], seg_out: dict[str, Any], public: PublicInputs,
             seal_gap_ids: set[str], lookup: dict | None, grid: dict) -> dict[str, Any]:
    out: dict[str, Any] = {"sleeves": {}, "benchmarks": {}, "excess": {}, "events": {}, "transmission": {},
                           "class_transmission": {}, "halts": {}, "residual_stops": {}, "comparison_months": {},
                           "weights_mean": {}, "sigma_start": {}}
    for sid, seg in segments.items():
        s = seg_out[sid]
        months = s["sleeve_months"]
        cmp_months = {case: s["layer"][case]["months"] for case in CASES}
        out["comparison_months"][sid] = {case: [str(m[0]), str(m[-1]), int(len(m))] for case, m in cmp_months.items()}
        out["residual_stops"][sid] = {"count": len(seg.residual),
                                      "seal_gap": sum(1 for pid, _, _ in seg.residual if pid in seal_gap_ids)}
        out["sleeves"][sid] = {
            f"{signal_id}|{case}": {
                **metrics(s["monthly"][case][signal_id], public.rf),
                **stock_trading(s["books"]["sleeves"][(signal_id, case)], s["sleeve_rows"], len(months)),
            } for signal_id in FAMILY_A_IDS for case in CASES}
        out["benchmarks"][sid] = {
            "sleeve_months": [str(months[0]), str(months[-1]), int(len(months))],
            "equal_weight_pit": {"sleeve_months": metrics(s["ew"], public.rf),
                                 "comparison_months": metrics(s["ew"].loc[cmp_months["primary"]], public.rf)},
            "spy": {"sleeve_months": metrics(s["spy"], public.rf),
                    "comparison_months": metrics(s["spy"].loc[cmp_months["primary"]], public.rf)}}
        ex = {}
        for case in CASES:
            m = cmp_months[case]
            for rule in RULES:
                net = s["layer"][case]["books"][rule]["net"]
                ex[f"{rule}|{case}"] = {"vs_spy": excess(net, s["spy"]), "vs_equal_weight": excess(net, s["ew"])}
            for signal_id in FAMILY_A_IDS:
                net = s["monthly"][case][signal_id]
                ex[f"{signal_id}|{case}"] = {"vs_spy": excess(net, s["spy"]), "vs_equal_weight": excess(net, s["ew"])}
            out["weights_mean"].setdefault(sid, {})[case] = {
                rule: {k: float(v) for k, v in s["layer"][case]["weights"][rule].mean().items()} for rule in RULES}
            out["sigma_start"].setdefault(sid, {})[case] = str(m[0])
        out["excess"][sid] = ex
        window = set(cmp_months["primary"])
        ev = {f"{signal_id}|{case}": book_event_summary(held_events(s["books"]["sleeves"][(signal_id, case)]),
                                                        seal_gap_ids, window)
              for signal_id in FAMILY_A_IDS for case in CASES}
        ev["equal_weight_pit"] = book_event_summary(held_events(s["books"]["ew"]), seal_gap_ids, window)
        for case in CASES:
            sleeve_events = {sig: held_events(s["books"]["sleeves"][(sig, case)]) for sig in FAMILY_A_IDS}
            equity = {sig: gross_growth_path(s["books"]["sleeves"][(sig, case)]) for sig in FAMILY_A_IDS}
            for rule in RULES:
                ev[f"{rule}|{case}"] = rule_event_summary(sleeve_events, equity, s["layer"][case]["weights"][rule],
                                                          seg.calendar, seal_gap_ids)
        out["events"][sid] = ev
        out["halts"][sid] = {f"{signal_id}|{case}": halt_counts(s["books"]["sleeves"][(signal_id, case)], seg, lookup)
                             for signal_id in FAMILY_A_IDS for case in CASES}
        # Transmission, primary case, sleeve months through the public last month.
        t_months = months[months <= public.last_month]
        active = s["monthly"]["primary"].loc[t_months].sub(s["ew"].loc[t_months], axis=0)
        out["transmission"][sid] = {signal_id: _transmission(active[signal_id],
                                                              public.jkp[SLEEVES[signal_id][0]].reindex(t_months))
                                    for signal_id in FAMILY_A_IDS}
        cm = cmp_months["primary"]
        klass = class_returns(s["monthly"]["primary"], s["sigma"]["primary"], cm).sub(s["ew"].loc[cm], axis=0)
        out["class_transmission"][sid] = {theme: _transmission(klass[theme], public.class_values[theme].reindex(cm))
                                          for theme in THEMES}
    pooled = {}
    for signal_id in FAMILY_A_IDS:
        a, b = [], []
        for sid in segments:
            months = seg_out[sid]["sleeve_months"]
            months = months[months <= public.last_month]
            a.append(seg_out[sid]["monthly"]["primary"].loc[months, signal_id] - seg_out[sid]["ew"].loc[months])
            b.append(public.jkp[SLEEVES[signal_id][0]].reindex(months))
        pooled[signal_id] = _transmission(pd.concat(a), pd.concat(b))
    out["transmission"]["pooled"] = pooled
    return out


def stock_trading(result: Any, rows: pd.DatetimeIndex, months: int) -> dict[str, float]:
    """Average monthly stock turnover and cost over the sleeve-month rows (the partial month is left out)."""
    return {"stock_turnover_monthly_mean": float(result.turnover.reindex(rows).sum()) / months,
            "stock_cost_monthly_mean": float(result.total_trading_costs.reindex(rows).sum()) / months}


def _transmission(active: pd.Series, public: pd.Series) -> dict[str, Any]:
    if public.isna().any():
        raise refuse("public_return_missing", f"{int(public.isna().sum())} months")
    pit_mean, pub_mean = float(active.mean()), float(public.mean())
    return {"months": int(len(active)), "pit_mean_active": pit_mean, "public_mean": pub_mean,
            "ratio": None if pub_mean == 0 else pit_mean / pub_mean, "correlation": correlation(active, public)}


def evaluate(segments: dict[str, SegmentInputs], public: PublicInputs, seal_gap_ids: set[str] = frozenset(),
             lookup: dict | None = None) -> dict[str, Any]:
    """Both event runs, the S4 tests on the primary run, the BY family, and the fragility label."""

    runs = {name: evaluate_run(segments, public, value, set(seal_gap_ids), lookup)
            for name, value in EVENT_RUNS.items()}
    primary = runs["primary"]
    tests = {test_id: step3.rule_test(diff) for test_id, diff in primary["diffs"].items()}
    pvalues = pd.Series({k: 1.0 if v["hac_pvalue"] is None else float(v["hac_pvalue"]) for k, v in tests.items()})
    qvalues = s4_family(pvalues)
    for test_id, stat in tests.items():
        stat["family_p"], stat["by_qvalue"] = float(pvalues[test_id]), float(qvalues[test_id])
    return {"runs": runs, "s4_tests": tests, "fragility": fragility(primary, runs["last_close"])}


# Output ---------------------------------------------------------------------------------

def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        value = float(value)
        return value if math.isfinite(value) else None
    if isinstance(value, (pd.Period, pd.Timestamp)):
        return str(value)
    return value


def summarize(result: dict[str, Any]) -> dict[str, Any]:
    """The JSON-ready aggregate view: no series, no identifier, no path."""

    runs = {}
    for name, run in result["runs"].items():
        runs[name] = {"decision": run["decision"], "survival": run["survival"], "s4_means": run["s4_means"],
                      "rules": run["grid"], "public_rules": run["public_grid"], **run["tables"]}
    tests = {k: {key: v.get(key) for key in ("status", "n_observations", "mean_return", "hac_statistic", "hac_pvalue",
                                               "hac_lags", "ci95_monthly", "ci95_annual", "family_p", "by_qvalue")}
             for k, v in result["s4_tests"].items()}
    return _clean({"runs": runs, "s4_tests": tests, "fragility": result["fragility"],
                   "family": {"observed_tests": OBSERVED_TESTS, "prior_slots": FAMILY_SIZE - OBSERVED_TESTS,
                              "family_size": FAMILY_SIZE, "method": "by"}})


def _f(value: Any, digits: int = 3, pct: bool = False) -> str:
    if value is None:
        return "n/a"
    return f"{100 * value:.{digits - 1}f}%" if pct else f"{value:.{digits}f}"


def _book(key: str) -> str:
    """A table label for a ``book|case`` key; a pipe inside a Markdown cell would split the cell."""
    return key.replace("|", " (") + ")" if "|" in key else key


def _survival_counts(run: dict[str, Any], key: str) -> str:
    rows = run["survival"][key]
    return (f"{sum(bool(r['holds']) for r in rows)} of 8 on point-in-time books, "
            f"{sum(bool(r['public_holds']) for r in rows)} of 8 on public books over the same months")


def render_report(doc: dict[str, Any]) -> str:
    p, lc = doc["runs"]["primary"], doc["runs"]["last_close"]
    frag = doc["fragility"]
    unpriced = doc.get("unpriced", {})
    label = "FRAGILE" if frag["fragile"] else "not fragile"
    lines = [
        "# Milestone 5 Step 4: Price-Class Bridge on Point-in-Time S&P 500 Books",
        "",
        "**Evidence ceiling: `DIAGNOSTIC_ONLY`.** Simulated research on the local `real_v2` snapshot; no profitability "
        "claim. Aggregates only.",
        "",
        f"- **VP-2.** {VP2}",
        "- **R4.** No terminal evidence is accepted. Every residual held stop settles at -100 percent in every sleeve "
        "and in the equal-weight benchmark; a last-close rerun is reported beside it.",
        f"- **Fragility: {label}** ({len(frag['sign_changes'])} sign changes between the -100 percent run and the "
        f"last-close rerun; outcome changes: {', '.join(frag['outcome_changes']) or 'none'}).",
        "- **Unpriced members** are never held. Unpriced member-day share: "
        + "; ".join(f"{sid} {_f(u.get('unpriced_share'), 3, True)} (upper bound {_f(u.get('unpriced_share_upper_bound'), 3, True)})"
                    for sid, u in unpriced.items()) + f". {STAGE_D_PRE_UNPRICED}.",
        "- **Missing crash.** The seal window and its buffers exclude 2019-07 to 2021-08, including the 2020 crash, "
        "so drawdowns are understated.",
        "- **Prior exposure.** The post segment re-examines M4.7 factors and months; only 2014-05 to 2016-07 is "
        "unexposed. No result is confirmatory.",
        "",
        "## Decision Outcomes (primary run)",
        "",
        f"- Point-in-time baseline product: **{p['decision']['baseline']}**. Rule R1 against R0: "
        f"{_survival_counts(p, 'R1_vs_R0')}.",
        f"- R2: **{p['decision']['r2']}**" + (f", labeled '{p['decision']['r2_label']}'" if p['decision']['r2_label'] else "")
        + f". R2 against rule R1: {_survival_counts(p, 'R2_vs_R1')}; R2 against R0: {_survival_counts(p, 'R2_vs_R0')}.",
        f"- Fragility: **{label}**. Sign changes: {', '.join(frag['sign_changes']) or 'none'}.",
        f"- Last-close rerun: baseline {lc['decision']['baseline']}, R2 {lc['decision']['r2']}.",
        "- S4 q-values and the fragility label are reported beside the outcomes and do not change them.",
        "",
        "## Survival: Point-in-Time Conditions Beside the Public Margins",
        "",
    ]
    for key, title in (("R1_vs_R0", "Rule R1 against R0"), ("R2_vs_R1", "R2 against rule R1"),
                       ("R2_vs_R0", "R2 against R0")):
        rows = p["survival"][key]
        public_holds = sum(bool(r["public_holds"]) for r in rows)
        lines += [f"### {title}: {sum(bool(r['holds']) for r in rows)} of 8 hold on point-in-time books "
                  f"({public_holds} of 8 on public books over the same months)", "",
                  "| Segment | Cost case | Metric | PIT margin | PIT holds | Public margin | Public holds | Ratio | "
                  "Last-close margin |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for row, other in zip(rows, lc["survival"][key]):
            lines.append(f"| {row['segment']} | {row['cost_case']} | {row['metric']} | {_f(row['margin'], 4)} | "
                         f"{'yes' if row['holds'] else 'no'} | {_f(row['public_margin'], 4)} | "
                         f"{'yes' if row['public_holds'] else 'no'} | {_f(row['margin_ratio'], 3)} | "
                         f"{_f(other['margin'], 4)} |")
        lines.append("")
    lines += ["Sharpe on point-in-time books is 12 x mean(r_net - RF) / (sqrt(12) x sd(r_net)); the public long-short "
              "books keep the v1 Sharpe without RF. Drawdown margins are R1 magnitude minus candidate magnitude.", "",
              "## S4 Tests (primary run, primary cost case, pooled comparison months)", "",
              "| Test | Months | Mean monthly | 95% interval (monthly) | HAC p | BY q (family 480) | "
              "Last-close mean |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for test_id, stat in doc["s4_tests"].items():
        ci = stat.get("ci95_monthly")
        lines.append(f"| {test_id} | {stat.get('n_observations')} | {_f(stat.get('mean_return'), 3, True)} | "
                     + (f"{_f(ci[0], 3, True)} to {_f(ci[1], 3, True)}" if ci else "n/a")
                     + f" | {_f(stat.get('hac_pvalue'), 3)} | {_f(stat.get('by_qvalue'), 3)} | "
                     f"{_f(lc['s4_means'][test_id], 3, True)} |")
    lines += ["", "The BY family counts 2 observed tests and 478 prior slots at p = 1. The last-close rerun reports "
              "means and signs only. With 480 slots the smallest p-value needs about 1.5e-5 to reach q 0.05.", ""]
    lines += ["## Rule Metrics (primary run)", "",
              "| Segment | Cost case | Rule | Months | Ann. mean | Volatility | Sharpe (RF) | Max drawdown | "
              "Avg switch turnover |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for sid in p["rules"]["R0"]["primary"]:
        for case in CASES:
            for rule in RULES:
                m = p["rules"][rule][case][sid]
                lines.append(f"| {sid} | {case} | {rule} | {m['months']} | {_f(m['annualized_mean'], 3, True)} | "
                             f"{_f(m['volatility'], 3, True)} | {_f(m['sharpe'])} | {_f(m['max_drawdown'], 3, True)} | "
                             f"{_f(m['average_monthly_turnover'])} |")
    lines += ["", "## Excess Over the Benchmarks (primary run)", "",
              "| Segment | Book | Ann. excess vs SPY | Total excess vs SPY | Ann. excess vs EW | Total excess vs EW | "
              "Unpriced share |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for sid, table in p["excess"].items():
        share = _f(unpriced.get(sid, {}).get("unpriced_share"), 3, True)
        for book, e in table.items():
            lines.append(f"| {sid} | {_book(book)} | {_f(e['vs_spy']['annualized_mean_excess'], 3, True)} | "
                         f"{_f(e['vs_spy']['excess_total_return'], 3, True)} | "
                         f"{_f(e['vs_equal_weight']['annualized_mean_excess'], 3, True)} | "
                         f"{_f(e['vs_equal_weight']['excess_total_return'], 3, True)} | {share} |")
    lines += ["", "## Benchmarks (primary run)", "",
              "| Segment | Benchmark | Window | Months | Ann. mean | Sharpe (RF) | Max drawdown |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for sid, b in p["benchmarks"].items():
        for name in ("spy", "equal_weight_pit"):
            for window in ("sleeve_months", "comparison_months"):
                m = b[name][window]
                lines.append(f"| {sid} | {name} | {window} | {m['months']} | {_f(m['annualized_mean'], 3, True)} | "
                             f"{_f(m['sharpe'])} | {_f(m['max_drawdown'], 3, True)} |")
    lines += ["", "## Sleeves (primary run, sleeve months)", "",
              "| Segment | Sleeve | Cost case | Months | Ann. mean | Sharpe (RF) | Max drawdown | Avg monthly stock "
              "turnover | Avg monthly stock cost |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for sid, table in p["sleeves"].items():
        for key, m in table.items():
            signal_id, case = key.split("|")
            lines.append(f"| {sid} | {signal_id} | {case} | {m['months']} | {_f(m['annualized_mean'], 3, True)} | "
                         f"{_f(m['sharpe'])} | {_f(m['max_drawdown'], 3, True)} | "
                         f"{_f(m['stock_turnover_monthly_mean'])} | {_f(m['stock_cost_monthly_mean'], 3, True)} |")
    lines += ["", "## Mean Class-Layer Weights (primary run, primary cost case)", "",
              "| Segment | Rule | " + " | ".join(FAMILY_A_IDS) + " |", "| --- | --- |" + " --- |" * len(FAMILY_A_IDS)]
    for sid, cases in p["weights_mean"].items():
        for rule in RULES:
            lines.append(f"| {sid} | {rule} | " + " | ".join(_f(cases["primary"][rule][s]) for s in FAMILY_A_IDS) + " |")
    lines += ["", "## Transmission (descriptive; primary run, primary cost case)", "",
              "| Segment | Sleeve or class | Months | PIT mean active | Public mean | Ratio | Correlation |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for sid, table in p["transmission"].items():
        for name, t in table.items():
            lines.append(f"| {sid} | {name} | {t['months']} | {_f(t['pit_mean_active'], 3, True)} | "
                         f"{_f(t['public_mean'], 3, True)} | {_f(t['ratio'])} | {_f(t['correlation'])} |")
    for sid, table in p["class_transmission"].items():
        for name, t in table.items():
            lines.append(f"| {sid} | class {name} | {t['months']} | {_f(t['pit_mean_active'], 3, True)} | "
                         f"{_f(t['public_mean'], 3, True)} | {_f(t['ratio'])} | {_f(t['correlation'])} |")
    lines += ["", "## R4 Affected Events", "",
              "| Run | Segment | Book | Events (count) | Incoming weight sum | Max | Seal-gap events | "
              "Outside comparison months |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for run_name, run in (("primary", p), ("last_close", lc)):
        for sid, table in run["events"].items():
            for book, e in table.items():
                if "all" in e:
                    lines.append(f"| {run_name} | {sid} | {_book(book)} | {e['all']['count']} | {_f(e['all']['weight_sum'], 4)} | "
                                 f"{_f(e['all']['weight_max'], 4)} | {e['seal_gap']['count']} | "
                                 f"{e['outside_comparison_months']['count']} |")
                else:
                    lines.append(f"| {run_name} | {sid} | {_book(book)} | {e['unique_events']} unique, {e['incidences']} "
                                 f"incidences | {_f(e['weight_sum'], 4)} | {_f(e['weight_max'], 4)} | "
                                 f"{e['seal_gap_events']} | rule level: comparison months only |")
    lines += ["", "Residual stops per segment: " + "; ".join(f"{sid} {r['count']} (seal-gap {r['seal_gap']})"
                                                           for sid, r in p["residual_stops"].items()) + ".", ""]
    lines += ["## Missingness", ""]
    for sid, u in unpriced.items():
        lines.append(f"- {sid}: {u['unpriced']} of {u['denominator']} member-days unpriced "
                     f"({_f(u['unpriced_share'], 3, True)}); undated intervals {u['undated_intervals']} (upper bound "
                     f"{_f(u['unpriced_share_upper_bound'], 3, True)}); by exit class "
                     + ", ".join(f"{k} {v}" for k, v in u["by_exit_class"].items()) + "; by reason "
                     + ", ".join(f"{k} {v}" for k, v in u["by_reason"].items()) + ".")
    for sid, table in p.get("signal_exclusions", {}).items():
        lines.append(f"- {sid} signal exclusions (eligible, no finite signal): "
                     + ", ".join(f"{k} {v['total']}" for k, v in table.items()) + ".")
    for sid, table in p["halts"].items():
        primary_rows = {k: v for k, v in table.items() if k.endswith("|primary")}
        lines.append(f"- {sid} unmarked halt rows and locked execution rows (primary cost case): "
                     + ", ".join(f"{k.split('|')[0]} {v['unmarked_halt_rows']} and {v['locked_execution_rows']}"
                                 for k, v in primary_rows.items()) + ".")
    lines += ["", "## Windows", ""]
    for sid, cases in p["comparison_months"].items():
        lines.append(f"- {sid}: comparison months " + "; ".join(f"{c} {v[0]} to {v[1]} ({v[2]})" for c, v in cases.items())
                     + f"; sleeve months {p['benchmarks'][sid]['sleeve_months'][0]} to "
                     f"{p['benchmarks'][sid]['sleeve_months'][1]} ({p['benchmarks'][sid]['sleeve_months'][2]}).")
    snapshot = doc.get("snapshot", {})
    git = doc.get("git", {})
    lines += ["", "## Method and Provenance", "",
              "- Specification: `docs/preregistrations/m5_trial_family_v1_amendment_4.json` revision 2 (SHA-256 "
              f"`{AMENDMENT_4_SHA256}`) with v1 and amendments 1 to 3; the runner refuses unless all five match HEAD "
              "and their pins.",
              f"- Code commit `{git.get('commit', 'n/a')}`; tracked changes at run time: {git.get('tracked_changes')}.",
              f"- Data: the local `{snapshot.get('id', SNAPSHOT_ID)}` snapshot, bound by the SHA-256 pins in "
              f"`{REPORT_JSON}` (snapshot.pins) and the recomputed discovery inputs; public inputs from "
              f"`{base.MANIFEST_JSON}` (SHA-256 `{PUBLIC_MANIFEST_SHA256}`). Nothing under the snapshot's terminal "
              "directory is read, and the seal window stays unaccessed.",
              "- Timing: `after_close_signal_next_observed_close_v1`. A sleeve signal uses row r - 1, executes at the "
              "close of month-end row r, and first earns row r + 1. Class weights for month t use inputs through month "
              "t-2, execute at the month t-1 close, and earn month t.",
              "- Costs: stock 1 + 4 bp (primary) or 2 + 8 bp (sensitivity) on traded notional inside each sleeve; a "
              "class switch cost of 20 or 50 bp on drift-adjusted class turnover; no borrow (long only); the equal-weight "
              "benchmark and SPY are cost-free.",
              "- Sample reuse: every comparison re-examines months or factors seen in M4.7 or in steps 2 and 3; the S4 "
              "family counts 478 prior slots.", ""]
    lines += ["", "## Limitations", "",
              "- Costs do not net across sleeves and include no market-impact model; the switch cost is a proxy.",
              "- Rule R1 uses a 126-day sigma, not the v1 36-month window.",
              "- About 99 comparison months give little power; the pooled HAC treats the segment boundary as adjacent.",
              "- R2's multipliers come from public long-short data and are not re-estimated on stock-level books.",
              "- Four of 13 themes are covered; the public counterpart is the 153-factor book.",
              "- All six source papers predate 2014, so every month is post-publication.", ""]
    return "\n".join(lines) + "\n"


# Run -------------------------------------------------------------------------------------

def snapshot_accounting(bound: dict[str, Any]) -> tuple[dict[str, Any], dict, set[str]]:
    """Unpriced accounting inputs from the pinned snapshot files (aggregated before output)."""

    snapshot, root = bound["snapshot"], bound["snapshot"].root
    intervals = pd.read_csv(root / INTERVAL_RESULTS, dtype=str, keep_default_na=False)
    master = pd.read_csv(root / SECURITY_MASTER, dtype=str, keep_default_na=False)
    calendar = bound["calendar"]
    panels: dict[str, set[str]] = {}
    for record in bound["inventory"]["files"]:
        panels.setdefault(record["side"], set()).add(record["symbol"])
    spans = {seg.segment_id: (seg.first_reset_row, seg.last_book_row, seg.side) for seg in bound["segments"]}
    sides = {side for _, _, side in spans.values()}
    codes = {c for c in intervals["vendor_code"] if c}
    quarantined = {side: {c for c in codes if snapshot.discovery_status("eod", c, side).startswith("quarantined:")}
                   for side in sides}
    refusals = {side: set(master.loc[master["episode_panel_refusal"].str.contains(side), "permanent_id"])
                for side in sides}
    shares = unpriced_share(intervals, calendar, spans, panels, quarantined, refusals)
    seal_gap = set(intervals.loc[intervals["exit_class"] == "seal_gap_identity_split", "permanent_id"])
    return shares, exit_class_lookup(intervals, calendar), seal_gap


def run(repo_root: Path, snapshot_dir: Path, git: dict[str, Any]) -> dict[str, Any]:
    step3.verify_trial_files(repo_root, TRIAL_PINS)
    public = load_public(repo_root)
    bound = bind_step4(snapshot_dir)
    runs, access = load_segment_runs_step4(bound)
    segments = {r.segment.segment_id: prepare(r, registered_rows(r.segment.segment_id)) for r in runs}
    shares, lookup, seal_gap = snapshot_accounting(bound)
    result = evaluate(segments, public, seal_gap, lookup)
    exclusions = {sid: signal_exclusions(seg, lookup) for sid, seg in segments.items()}
    verify_pins_unchanged(snapshot_dir)
    doc = summarize(result)
    doc["runs"]["primary"]["signal_exclusions"] = _clean(exclusions)
    doc.update(_clean({
        "schema_version": "m5_step4_v1", "evidence_ceiling": "DIAGNOSTIC_ONLY",
        "run_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trial_files": TRIAL_PINS, "git": git, "snapshot": {"id": SNAPSHOT_ID, "pins": SNAPSHOT_PINS,
                                                            "discovery_inputs_sha256": DISCOVERY_INPUTS_SHA256,
                                                            "segment_access_sides": access},
        "public_manifest_sha256": PUBLIC_MANIFEST_SHA256, "public_last_month": str(public.last_month),
        "vp2": VP2, "unpriced": shares, "stage_d_note": STAGE_D_PRE_UNPRICED,
        "costs": {"stock": STOCK_COSTS, "switch_bps": SWITCH_BPS}, "sigma_rows": SIGMA_ROWS, "top_pct": TOP_PCT,
    }))
    return doc


def _append_attempt(repo_root: Path, record: dict[str, Any]) -> None:
    path = repo_root / ATTEMPTS_JSONL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def write_outputs(repo_root: Path, doc: dict[str, Any]) -> dict[str, str]:
    (repo_root / REPORT_JSON).write_text(json.dumps(doc, indent=2, sort_keys=True, allow_nan=False) + "\n",
                                         encoding="utf-8")
    (repo_root / REPORT_MD).write_text(render_report(doc), encoding="utf-8")
    return {path: hashlib.sha256((repo_root / path).read_bytes()).hexdigest() for path in (REPORT_MD, REPORT_JSON)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--snapshot-dir", required=True, help="the real_v2 snapshot directory (never recorded)")
    parser.add_argument("--reason", required=True, help="why this attempt runs")
    args = parser.parse_args(argv)
    attempt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    git = base.git_state(REPO_ROOT)
    _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "start", "reason": args.reason,
                                "amendment_4_sha256": AMENDMENT_4_SHA256, "snapshot_id": SNAPSHOT_ID,
                                "snapshot_pins": SNAPSHOT_PINS, **git})
    started = time.perf_counter()
    try:
        doc = run(REPO_ROOT, Path(args.snapshot_dir), git)
        outputs = write_outputs(REPO_ROOT, doc)
    except Exception as error:
        reason = getattr(error, "reason", type(error).__name__)
        _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "end", "status": "refused",
                                    "reason": reason, "seconds": round(time.perf_counter() - started, 1)})
        raise
    decision = doc["runs"]["primary"]["decision"]
    _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "end", "status": "completed",
                                "baseline": decision["baseline"], "r2": decision["r2"],
                                "fragile": doc["fragility"]["fragile"], "outputs": outputs,
                                "seconds": round(time.perf_counter() - started, 1)})
    print(f"baseline {decision['baseline']}; R2 {decision['r2']}; fragile {doc['fragility']['fragile']}; "
          f"report {REPORT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
