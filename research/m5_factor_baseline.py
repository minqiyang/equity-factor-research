"""Milestone 5 step 2: equal weight (R0) against inverse volatility (R1).

Run with ``python -m research.m5_factor_baseline``. The command implements the
step 2 part of ``docs/preregistrations/m5_trial_family_v1.json`` and refuses to
run when that file differs from its committed HEAD version or from the pinned
SHA-256 below.

Timing (``after_month_end_signal_next_month_return``): the set, sigma, and
weights for month t use returns through month t-1 only, plus the declared
availability of each factor's month-t return; the rebalance happens at the end
of month t-1, the return month is t, and the switch cost is charged in month t.
Evidence ceiling ``DIAGNOSTIC_ONLY``: public long-short factor returns, gross of
each factor's internal trading and borrow costs.

Outputs: ``reports/m5_factor_baseline.md``, ``reports/m5_factor_baseline.json``
(aggregates only), ``reports/m5_public_data_manifest.json``, and one start and
one end record per attempt in ``reports/m5_factor_baseline_attempts.jsonl``.
Raw downloads stay in the gitignored ``data/public_cache/`` (R11).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from backtest.metrics import calculate_max_drawdown
from data.public_factors import (
    MISSING_ABSENT,
    PRESENT,
    MonthlyPanel,
    PublicDataRefusal,
    fetch,
    manifest_entry,
    read_cluster_labels,
    read_french_monthly_zip,
    read_fred_csv,
    read_jkp_zip,
    read_publication_years,
    sha256_file,
    write_manifest,
)
from features.multiple_testing import adjust_pvalues, return_test_statistics


REPO_ROOT = Path(__file__).resolve().parents[1]
TRIAL_PATH = "docs/preregistrations/m5_trial_family_v1.json"
TRIAL_SHA256 = "a99a862c651fd4e52e9904e62c8dfc539b85f57f1910d2a17b9bd03a6723417a"
AMENDMENT_PATH = "docs/preregistrations/m5_trial_family_v1_amendment_1.json"
AMENDMENT_SHA256 = "b3992b3282910a5bf056d3d6061e4456e6b4d4a923f4e6d3493898a445b90751"
CACHE_DIR = "data/public_cache"
REPORT_MD = "reports/m5_factor_baseline.md"
REPORT_JSON = "reports/m5_factor_baseline.json"
MANIFEST_JSON = "reports/m5_public_data_manifest.json"
ATTEMPTS_JSONL = "reports/m5_factor_baseline_attempts.jsonl"

LOOKBACK_MONTHS = 36
MIN_OBSERVATIONS = 24
REALIZED_MONTHS = 12
WORST_WINDOW_MONTHS = 12
MONTHS_PER_YEAR = 12
RULES = ("R0", "R1")
UNIVERSES = ("jkp_factors_153", "jkp_themes_13", "french_7")
PRIMARY_UNIVERSE = "jkp_factors_153"
PERIODS = ("full", "first_half", "second_half")
FRENCH_7_FILES = {
    "french_ff5_2x3_monthly": ["SMB", "HML", "RMW", "CMA"],
    "french_momentum_monthly": ["Mom"],
    "french_st_reversal_monthly": ["ST_Rev"],
    "french_lt_reversal_monthly": ["LT_Rev"],
}
STEP3_SOURCES = ("french_ff3_daily", "jkp_accounting_characteristics_list")


# Trial-file integrity -------------------------------------------------------

def verify_trial_file(repo_root: Path, relative: str) -> tuple[bytes, str]:
    """Return the trial-file bytes and SHA-256 if they equal the HEAD version."""

    worktree = (repo_root / relative).read_bytes()
    committed = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"HEAD:{relative}"],
        capture_output=True, check=False,
    )
    if committed.returncode != 0:
        raise PublicDataRefusal(f"trial file {relative} is not committed at HEAD")
    if committed.stdout != worktree:
        raise PublicDataRefusal(f"trial file {relative} differs from its committed HEAD version")
    return worktree, hashlib.sha256(worktree).hexdigest()


def git_state(repo_root: Path) -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True,
                              text=True, check=True).stdout.strip()
    return {"commit": git("rev-parse", "HEAD"),
            "tracked_changes": bool(git("status", "--porcelain", "--untracked-files=no"))}


# Membership, weights, and costs --------------------------------------------

@dataclass(frozen=True)
class Membership:
    """Per evaluated month and factor: the set, sigma, and each set condition."""

    in_set: pd.DataFrame
    sigma: pd.DataFrame
    has_return: pd.DataFrame
    enough_history: pd.DataFrame


def membership(returns: pd.DataFrame, months: pd.PeriodIndex) -> Membership:
    """Apply the membership rule and R1's sigma month by month.

    Factor i is in month t's set when its month-t return exists and it has at
    least 24 non-missing returns in months t-36 to t-1. sigma_i,t is the ddof-1
    standard deviation of those returns and stays NaN with fewer than 24.
    ``returns`` must carry every calendar month from t-36 to t.
    """

    sigma_rows, history_rows, return_rows = [], [], []
    for month in months:
        window = returns.loc[month - LOOKBACK_MONTHS: month - 1]
        count = window.notna().sum()
        enough = count >= MIN_OBSERVATIONS
        sigma_rows.append(window.std(ddof=1).where(enough))
        history_rows.append(enough)
        return_rows.append(returns.loc[month].notna())

    def frame(rows: list[pd.Series]) -> pd.DataFrame:
        return pd.DataFrame(rows, index=months, columns=returns.columns)

    has_return = frame(return_rows).astype(bool)
    enough_history = frame(history_rows).astype(bool)
    return Membership(has_return & enough_history, frame(sigma_rows).astype(float),
                      has_return, enough_history)


def rule_weights(rule: str, in_set: pd.DataFrame, sigma: pd.DataFrame) -> pd.DataFrame:
    """Target weights for R0 (1/N) or R1 (1/sigma, normalized, no cap).

    A factor outside the set carries weight 0. An evaluated month with an
    empty set refuses, and so does a zero or non-finite sigma for a member.
    """

    counts = in_set.sum(axis=1)
    empty = counts.index[counts == 0]
    if len(empty):
        raise PublicDataRefusal(
            f"{len(empty)} evaluated months have an empty set (first {empty[0]}, last {empty[-1]})"
        )
    if rule == "R0":
        raw = in_set.astype(float)
    elif rule == "R1":
        member_sigma = sigma.where(in_set)
        degenerate = in_set & ~(np.isfinite(member_sigma) & (member_sigma > 0))
        if degenerate.to_numpy().any():
            month = degenerate.any(axis=1).idxmax()
            raise PublicDataRefusal(
                f"{int(degenerate.to_numpy().sum())} member-months have a zero or non-finite sigma "
                f"(first {month})"
            )
        raw = (1.0 / member_sigma).where(in_set, 0.0)
    else:
        raise ValueError(f"unknown rule {rule}")
    return raw.div(raw.sum(axis=1), axis=0)


def portfolio(weights: pd.DataFrame, returns: pd.DataFrame, cost_bps: float) -> pd.DataFrame:
    """Monthly gross return, turnover, and net return of target weights.

    turnover_t = sum_i |w_i,t - w_i,t-1| with weight 0 outside the set; the
    first evaluated month starts from no holdings. r_net = r_gross -
    cost_bps / 10000 * turnover.
    """

    held = returns.loc[weights.index, weights.columns]
    exposed = weights > 0
    if (held.isna() & exposed).to_numpy().any():
        raise PublicDataRefusal("a held factor has a missing return in its holding month")
    gross = (weights * held).where(exposed).sum(axis=1)
    turnover = (weights - weights.shift(1, fill_value=0.0)).abs().sum(axis=1)
    net = gross - cost_bps / 10_000.0 * turnover
    return pd.DataFrame({"gross": gross, "turnover": turnover, "net": net})


# Metrics --------------------------------------------------------------------

def period_bounds(trial: dict[str, Any], last_month: pd.Period) -> dict[str, tuple[pd.Period, pd.Period]]:
    window = trial["evaluation_window"]
    first = pd.Period(window["first_evaluated_month"], freq="M")
    first_half = [pd.Period(value, freq="M") for value in window["halves"]["first"]]
    second_start = pd.Period(window["halves"]["second"][0], freq="M")
    return {"full": (first, last_month), "first_half": (first_half[0], first_half[1]),
            "second_half": (second_start, last_month)}


def worst_window_return(net: pd.Series) -> float | None:
    """Lowest compounded return over any 12 consecutive months of ``net``."""

    growth = (1.0 + net).to_numpy()
    span = WORST_WINDOW_MONTHS
    compounded = [float(np.prod(growth[i:i + span]) - 1.0) for i in range(len(growth) - span + 1)]
    return min(compounded) if compounded else None


def performance(net: pd.Series, turnover: pd.Series | None = None) -> dict[str, Any]:
    """Declared step 2 metrics on one period of monthly net returns."""

    mean = float(net.mean()) * MONTHS_PER_YEAR
    volatility = float(net.std(ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    path = (1.0 + net).cumprod()
    path.index = net.index.to_timestamp()
    return {
        "months": int(len(net)),
        "annualized_mean": mean,
        "volatility": volatility,
        "sharpe": mean / volatility if volatility > 0 else None,
        "max_drawdown": calculate_max_drawdown(path, initial_capital=1.0),
        "worst_12_month_return": worst_window_return(net),
        "average_monthly_turnover": None if turnover is None else float(turnover.mean()),
    }


def realized_volatility(returns: pd.DataFrame, months: pd.PeriodIndex) -> pd.DataFrame:
    """ddof-1 standard deviation over months t to t+11; NaN unless all 12 exist."""

    rows = []
    for month in months:
        window = returns.loc[month: month + REALIZED_MONTHS - 1]
        rows.append(window.std(ddof=1).where(window.notna().sum() == REALIZED_MONTHS))
    return pd.DataFrame(rows, index=months, columns=returns.columns).astype(float)


def volatility_accuracy(sigma: pd.DataFrame, realized: pd.DataFrame, in_set: pd.DataFrame,
                        bounds: dict[str, tuple[pd.Period, pd.Period]]) -> dict[str, Any]:
    """Pooled Spearman correlation of sigma_i,t with realized volatility over t..t+11."""

    last_usable = in_set.index[-1] - (REALIZED_MONTHS - 1)
    result = {}
    for period, (start, end) in bounds.items():
        inside = (in_set.index >= start) & (in_set.index <= end)
        members = in_set[inside]
        pair = members & sigma[inside].notna() & realized[inside].notna()
        past_end = members.copy()
        past_end.loc[members.index <= last_usable] = False
        forecast = sigma[inside].to_numpy()[pair.to_numpy()]
        outcome = realized[inside].to_numpy()[pair.to_numpy()]
        rho = float(spearmanr(forecast, outcome).statistic) if len(forecast) > 2 else None
        result[period] = {
            "spearman": rho,
            "pairs": int(pair.to_numpy().sum()),
            "excluded_window_past_last_month": int(past_end.to_numpy().sum()),
            "excluded_incomplete_realized_window": int((members & ~pair & ~past_end).to_numpy().sum()),
        }
    return result


def typed_missing_counts(missing: pd.DataFrame) -> dict[str, int]:
    reasons = missing.to_numpy().ravel()
    return {str(reason): int(count) for reason, count in
            zip(*np.unique(reasons[reasons != PRESENT], return_counts=True))}


def membership_counts(member: Membership, missing: pd.DataFrame,
                      bounds: dict[str, tuple[pd.Period, pd.Period]]) -> dict[str, Any]:
    result = {}
    for period, (start, end) in bounds.items():
        inside = (member.in_set.index >= start) & (member.in_set.index <= end)
        no_return = ~member.has_return[inside]
        short = ~member.enough_history[inside]
        result[period] = {
            "factor_months_declared": int(no_return.size),
            "factor_months_in_set": int(member.in_set[inside].to_numpy().sum()),
            "excluded_no_return_in_month": int(no_return.to_numpy().sum()),
            "excluded_fewer_than_24_prior_returns": int(short.to_numpy().sum()),
            "excluded_both_conditions": int((no_return & short).to_numpy().sum()),
            "typed_missing_by_reason": typed_missing_counts(missing.loc[start:end]),
        }
    return result


def missing_by_month(missing: pd.DataFrame) -> dict[str, dict[str, int]]:
    result = {}
    for month, row in missing.iterrows():
        counts = row[row != PRESENT].value_counts()
        if len(counts):
            result[str(month)] = {str(reason): int(count) for reason, count in counts.items()}
    return result


def rule_grid(member_set: pd.DataFrame, sigma: pd.DataFrame, returns: pd.DataFrame,
              costs: list[int], bounds: dict[str, tuple[pd.Period, pd.Period]]) -> tuple[dict, dict]:
    """Metrics for every rule, cost level, and period, plus the net series."""

    grid: dict[str, Any] = {}
    series: dict[tuple[str, int], pd.Series] = {}
    for rule in RULES:
        weights = rule_weights(rule, member_set, sigma)
        grid[rule] = {"members_per_month": _range(member_set.sum(axis=1))}
        for cost in costs:
            book = portfolio(weights, returns, cost)
            series[(rule, cost)] = book["net"]
            grid[rule][f"{cost}bp"] = {
                period: performance(book["net"].loc[start:end], book["turnover"].loc[start:end])
                for period, (start, end) in bounds.items()
            }
    return grid, series


def _range(counts: pd.Series) -> dict[str, int]:
    return {"min": int(counts.min()), "median": int(counts.median()), "max": int(counts.max())}


# Tests and decision -----------------------------------------------------------

def s2_tests(differences: dict[str, pd.Series | None], family_size: int) -> dict[str, Any]:
    """HAC test of mean(R1 net - R0 net) at 20 bp per universe, BY-adjusted."""

    statistics = {test_id: (return_test_statistics(values, periods_per_year=MONTHS_PER_YEAR)
                            if values is not None else {"status": "universe_refused", "hac_pvalue": None})
                  for test_id, values in differences.items()}
    pvalues = pd.Series({test_id: np.nan if stat["hac_pvalue"] is None else stat["hac_pvalue"]
                         for test_id, stat in statistics.items()}, dtype=float)
    qvalues = adjust_pvalues(pvalues, method="by", family_size=family_size)
    return {test_id: {**stat, "by_qvalue": None if math.isnan(qvalues[test_id]) else float(qvalues[test_id])}
            for test_id, stat in statistics.items()}


def decide(grid: dict[str, Any] | None, costs: list[int]) -> dict[str, Any]:
    """Step 2 decision rule on the primary universe's rule grid."""

    if grid is None:
        return {"outcome": "refused", "conditions": [], "conditions_held": 0}
    conditions = []
    for period in ("first_half", "second_half"):
        for cost in costs:
            r0, r1 = grid["R0"][f"{cost}bp"][period], grid["R1"][f"{cost}bp"][period]
            conditions.append({"period": period, "cost_bps": cost, "metric": "max_drawdown",
                               "R0": r0["max_drawdown"], "R1": r1["max_drawdown"],
                               "holds": abs(r1["max_drawdown"]) <= abs(r0["max_drawdown"])})
            holds = r0["sharpe"] is not None and r1["sharpe"] is not None and r1["sharpe"] >= r0["sharpe"]
            conditions.append({"period": period, "cost_bps": cost, "metric": "sharpe",
                               "R0": r0["sharpe"], "R1": r1["sharpe"], "holds": bool(holds)})
    held = sum(condition["holds"] for condition in conditions)
    return {"outcome": "R1" if held == len(conditions) else "R0", "conditions": conditions,
            "conditions_held": int(held)}


# Data loading ---------------------------------------------------------------

def _cache_path(cache_dir: Path, source: dict[str, Any]) -> Path:
    return cache_dir / f"{source['id']}{Path(urlparse(source['url']).path).suffix}"


def _dates(panel: MonthlyPanel) -> tuple[str, str]:
    present = panel.values.notna().any(axis=1) | (panel.missing != MISSING_ABSENT).any(axis=1)
    months = panel.values.index[present.to_numpy()]
    return str(months[0]), str(months[-1])


def load_inputs(trial: dict[str, Any], cache_dir: Path) -> dict[str, Any]:
    """Fetch and parse every step 2 source; fail closed on any declared check."""

    sources = {source["id"]: source for source in trial["data_sources"]}
    entries, loaded = [], {}

    def get(source_id: str):
        source = sources[source_id]
        cached = fetch(source["url"], _cache_path(cache_dir, source))
        if "sha256" in source and cached.sha256 != source["sha256"]:
            raise PublicDataRefusal(f"{source_id}: SHA-256 differs from the pinned value")
        return source, cached

    source, cached = get("jkp_cluster_labels")
    labels = read_cluster_labels(cached.path)
    if len(labels) != source["row_count"] or sorted(set(labels.values())) != sorted(source["clusters"]):
        raise PublicDataRefusal("jkp_cluster_labels: rows or clusters differ from the declaration")
    entries.append(manifest_entry(source["id"], cached, rows=len(labels), first=None, last=None))

    source, cached = get("jkp_factor_details")
    years = read_publication_years(cached.path, sheet=source["sheet"])
    entries.append(manifest_entry(source["id"], cached, rows=len(years), first=None, last=None))

    theme_names = {label.lower().replace(" ", "_").replace("-", "_") for label in labels.values()}
    if theme_names != set(trial["universes"]["jkp_themes_13"]["members"]):
        raise PublicDataRefusal("normalized cluster labels differ from the declared theme members")
    expected = {"jkp_usa_all_factors_monthly_vw_cap": set(labels),
                "jkp_usa_all_themes_monthly_vw_cap": theme_names}
    for source_id, names in expected.items():
        source, cached = get(source_id)
        panel = read_jkp_zip(cached.path, source["zip_member"], columns=source["columns"],
                             expected_names=names)
        loaded[source_id] = panel
        entries.append(manifest_entry(source_id, cached, rows=panel.n_rows, first=_dates(panel)[0],
                                      last=_dates(panel)[1]))

    for source_id, columns in {**FRENCH_7_FILES, "french_ff3_monthly": ["Mkt-RF", "RF"]}.items():
        source, cached = get(source_id)
        panel = read_french_monthly_zip(cached.path, source["zip_member"], columns=columns)
        loaded[source_id] = panel
        entries.append(manifest_entry(source_id, cached, rows=panel.n_rows, first=_dates(panel)[0],
                                      last=_dates(panel)[1]))

    source, cached = get("fred_baa_aaa_monthly")
    fred = read_fred_csv(cached.path, series=list(source["series"]))
    entries.append(manifest_entry(source["id"], cached, rows=fred.n_rows, first=_dates(fred)[0],
                                  last=_dates(fred)[1]))
    return {"labels": labels, "years": years, "panels": loaded, "manifest": entries}


def universe_panel(values: pd.DataFrame, missing: pd.DataFrame, first: pd.Period,
                   last: pd.Period) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Restrict to months through ``last`` on a complete calendar-month index.

    Months added before a file starts are typed ``absent``; no value is filled.
    """

    index = pd.period_range(min(values.index[0], first - LOOKBACK_MONTHS), last, freq="M")
    return values.reindex(index), missing.reindex(index).fillna(MISSING_ABSENT)


def build_universes(inputs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    panels = inputs["panels"]
    french_values = pd.concat([panels[s].values[c] for s, c in FRENCH_7_FILES.items()], axis=1)
    french_missing = pd.concat([panels[s].missing[c] for s, c in FRENCH_7_FILES.items()], axis=1)
    return {
        "jkp_factors_153": {"panel": panels["jkp_usa_all_factors_monthly_vw_cap"],
                            "last": panels["jkp_usa_all_factors_monthly_vw_cap"].values.index[-1]},
        "jkp_themes_13": {"panel": panels["jkp_usa_all_themes_monthly_vw_cap"],
                          "last": panels["jkp_usa_all_themes_monthly_vw_cap"].values.index[-1]},
        "french_7": {"panel": MonthlyPanel(french_values, french_missing.fillna(MISSING_ABSENT), 0),
                     "last": min(panels[s].values.index[-1] for s in FRENCH_7_FILES)},
    }


# Run ------------------------------------------------------------------------

def run_universe(panel: MonthlyPanel, first: pd.Period, last: pd.Period, trial: dict[str, Any],
                 market: pd.Series, costs: list[int]) -> dict[str, Any]:
    returns, missing = universe_panel(panel.values, panel.missing, first, last)
    months = pd.period_range(first, last, freq="M")
    bounds = period_bounds(trial, last)
    member = membership(returns, months)
    result: dict[str, Any] = {
        "first_evaluated_month": str(first), "last_evaluated_month": str(last),
        "declared_factors": int(returns.shape[1]),
        "counts": membership_counts(member, missing, bounds),
        "lookback_typed_missing": {
            "months": f"{first - LOOKBACK_MONTHS} to {first - 1}",
            "by_reason": typed_missing_counts(missing.loc[first - LOOKBACK_MONTHS: first - 1]),
        },
        "missing_by_month": missing_by_month(missing.loc[first:last]),
        "volatility_forecast_accuracy": volatility_accuracy(
            member.sigma, realized_volatility(returns, months), member.in_set, bounds),
    }
    market_months = market.reindex(months)
    if market_months.isna().any():
        result["market_excess"] = {"status": "missing_months", "missing": int(market_months.isna().sum())}
    else:
        result["market_excess"] = {period: performance(market_months.loc[start:end])
                                   for period, (start, end) in bounds.items()}
    try:
        grid, series = rule_grid(member.in_set, member.sigma, returns, costs, bounds)
    except PublicDataRefusal as refusal:
        result.update(status="refused", reason=str(refusal))
        return result
    result.update(status="completed", rules=grid)
    result["_series"] = series
    result["_member"] = member
    result["_returns"] = returns
    return result


def post_publication(universe: dict[str, Any], years: dict[str, int | None], trial: dict[str, Any],
                     costs: list[int]) -> dict[str, Any]:
    """R0 and R1 on the set restricted to factors published before year(t).

    Amendment 1: the run starts at the first evaluated month with a non-empty
    subset; earlier months are counted as empty, and a later empty month
    still refuses.
    """

    member: Membership = universe["_member"]
    declared = set(trial["traits"]["years_since_publication"]["missing_publication_year"])
    no_year = {name for name in member.in_set.columns if years.get(name) is None}
    if no_year != declared:
        return {"status": "refused",
                "reason": f"factors without a publication year {sorted(no_year)} differ from the declared list"}
    calendar_year = pd.Series(member.in_set.index.year, index=member.in_set.index)
    published = pd.DataFrame(
        {name: (calendar_year > years[name]) if name not in no_year else False
         for name in member.in_set.columns}, index=member.in_set.index,
    ).astype(bool)
    subset = member.in_set & published
    last = member.in_set.index[-1]
    bounds = period_bounds(trial, last)
    counts = {}
    for period, (start, end) in bounds.items():
        inside = (subset.index >= start) & (subset.index <= end)
        in_set = member.in_set[inside]
        counts[period] = {
            "factor_months_in_set": int(in_set.to_numpy().sum()),
            "factor_months_in_subset": int(subset[inside].to_numpy().sum()),
            "excluded_missing_publication_year": int(in_set[sorted(no_year)].to_numpy().sum()),
            "excluded_published_in_or_after_year": int(
                (in_set & ~published[inside]).drop(columns=sorted(no_year)).to_numpy().sum()),
            "months_with_empty_subset": int((subset[inside].sum(axis=1) == 0).sum()),
        }
    non_empty = subset.sum(axis=1) > 0
    start = subset.index[non_empty.to_numpy().argmax()] if non_empty.any() else None
    leading = subset.index[~non_empty & (subset.index < start)] if start is not None else subset.index
    result: dict[str, Any] = {
        "counts": counts,
        "start_month": str(start) if start is not None else None,
        "empty_subset_months": {"count": int(len(leading)),
                                "first": str(leading[0]) if len(leading) else None,
                                "last": str(leading[-1]) if len(leading) else None},
    }
    if start is None:
        result.update(status="refused", reason="no evaluated month has a non-empty subset")
        return result
    run_bounds = {period: (max(first, start), end) for period, (first, end) in bounds.items()
                  if max(first, start) <= end}
    run_subset, run_sigma = subset.loc[start:], member.sigma.loc[start:]
    try:
        grid, _ = rule_grid(run_subset, run_sigma, universe["_returns"], costs, run_bounds)
    except PublicDataRefusal as refusal:
        result.update(status="refused", reason=str(refusal))
        return result
    result["volatility_forecast_accuracy"] = volatility_accuracy(
        run_sigma, realized_volatility(universe["_returns"], run_subset.index), run_subset, run_bounds)
    result.update(status="completed", rules=grid)
    return result


def run(repo_root: Path) -> dict[str, Any]:
    trial_bytes, trial_sha = verify_trial_file(repo_root, TRIAL_PATH)
    if trial_sha != TRIAL_SHA256:
        raise PublicDataRefusal(f"trial file SHA-256 {trial_sha} differs from the pinned {TRIAL_SHA256}")
    _, amendment_sha = verify_trial_file(repo_root, AMENDMENT_PATH)
    if amendment_sha != AMENDMENT_SHA256:
        raise PublicDataRefusal(f"amendment SHA-256 {amendment_sha} differs from the pinned {AMENDMENT_SHA256}")
    trial = json.loads(trial_bytes)
    git = git_state(repo_root)
    costs = [trial["costs"]["switch_cost_bps"]["primary"], trial["costs"]["switch_cost_bps"]["sensitivity"]]
    first = pd.Period(trial["evaluation_window"]["first_evaluated_month"], freq="M")

    inputs = load_inputs(trial, repo_root / CACHE_DIR)
    write_manifest(repo_root / MANIFEST_JSON, inputs["manifest"], notes={
        "trial_file": TRIAL_PATH, "trial_file_sha256": trial_sha, "code_commit": git["commit"],
        "cache_dir": CACHE_DIR + "/ (gitignored; raw files are never committed)",
        "not_retrieved_in_step2": {source: "consumed in step 3" for source in STEP3_SOURCES},
    })
    market_panel = inputs["panels"]["french_ff3_monthly"]
    market = market_panel.values["Mkt-RF"]

    universes = {}
    for universe_id, spec in build_universes(inputs).items():
        universes[universe_id] = run_universe(spec["panel"], first, spec["last"], trial, market, costs)

    tests = trial["step2_tests"]
    differences = {}
    for test in tests["tests"]:
        universe = universes[test["universe"]]
        differences[test["id"]] = (universe["_series"][("R1", costs[0])] - universe["_series"][("R0", costs[0])]
                                   if universe["status"] == "completed" else None)
    s2 = s2_tests(differences, tests["family_size"])
    primary = universes[PRIMARY_UNIVERSE]
    decision = decide(primary.get("rules") if primary["status"] == "completed" else None, costs)
    post = (post_publication(primary, inputs["years"], trial, costs)
            if primary["status"] == "completed" else {"status": "universe_refused"})

    for universe in universes.values():
        for key in ("_series", "_member", "_returns"):
            universe.pop(key, None)
    return {
        "schema_version": "m5_factor_baseline_v1",
        "evidence_ceiling": trial["evidence_ceiling"],
        "run_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trial_file": TRIAL_PATH, "trial_file_sha256": trial_sha,
        "amendment_file": AMENDMENT_PATH, "amendment_file_sha256": amendment_sha, "git": git,
        "timing": trial["timing"]["label"], "switch_cost_bps": costs,
        "manifest": inputs["manifest"],
        "universes": universes, "s2_tests": s2, "decision": decision, "post_publication": post,
    }


# Report -----------------------------------------------------------------------

def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.2f}%"


def _num(value: float | None, digits: int = 3) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def _bp(value: float | None) -> str:
    return "n/a" if value is None else f"{10_000 * value:.2f}"


def _pvalue(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4g}"


PERIOD_LABEL = {"full": "full", "first_half": "1972-1999", "second_half": "2000-end"}


def render_report(result: dict[str, Any]) -> str:
    decision = result["decision"]
    lines = [
        "# Milestone 5 Step 2: Public Factor Baseline (Equal Weight vs Inverse Volatility)",
        "",
        f"Run {result['run_utc']} from code commit `{result['git']['commit']}` "
        f"(tracked changes at run time: {result['git']['tracked_changes']}).",
        "",
        "## Read This First",
        "",
        f"- **Evidence ceiling: {result['evidence_ceiling']}.** These are diagnostics on public long-short factor "
        "series. They support no profitability, ranking, or promotion claim.",
        "- **Long-short and gross of internal costs.** Each factor return is a published zero-investment "
        "long-minus-short return. It excludes the factor's own trading costs and short-leg borrow costs. Only the "
        "allocator's switch cost (20 bp primary, 50 bp sensitivity, on monthly weight turnover) is charged.",
        "- **Small caps included.** JKP capped value-weight factors and the French factors hold small and micro "
        "caps, which a long-only large-cap book cannot trade at these returns.",
        "- **Hindsight in the factor list.** The JKP list was assembled after the underlying papers; months before "
        "each publication were in the original authors' samples. The post-publication split below is the declared "
        "check.",
        "- **Prior exposures (R9).** Before this declaration the coordinator saw two diagnostics on overlapping "
        "months: the 2026-09-28 audit scratch run on 7 French factors (equal weight Sharpe 0.83, inverse volatility "
        "0.83) and the 2026-09-28 vision probe on JKP 153 factors (inverse volatility Sharpe 0.94 vs 0.72 for equal "
        "weight). This run re-examines a comparison already seen and supports no confirmatory claim.",
        f"- **Trial family.** `{result['trial_file']}`, SHA-256 `{result['trial_file_sha256']}`, verified equal "
        "to its committed HEAD version before any data was read"
        + (f"; amendment `{result['amendment_file']}`, SHA-256 `{result['amendment_file_sha256']}`, verified the "
           "same way." if result.get("amendment_file") else "."),
        f"- **Timing.** `{result['timing']}`: weights for month t use returns through month t-1 and the declared "
        "availability of each factor's month-t return; the switch cost is charged in month t.",
        "",
        "## Result",
        "",
    ]
    if decision["outcome"] == "refused":
        lines.append("The primary universe refused, so the decision rule has no outcome.")
    else:
        lines.append(
            f"**Baseline product: {decision['outcome']}** "
            f"({'inverse volatility' if decision['outcome'] == 'R1' else 'equal weight'}). "
            f"{decision['conditions_held']} of {len(decision['conditions'])} declared conditions hold on "
            "jkp_factors_153 (R1 drawdown magnitude at most R0's and R1 Sharpe at least R0's, in both halves, at "
            "20 and 50 bp). The S2 q-values are reported beside the decision and do not change it.")
        full = {rule: result["universes"][PRIMARY_UNIVERSE]["rules"][rule][f"{result['switch_cost_bps'][0]}bp"]["full"]
                for rule in RULES}
        s2 = result["s2_tests"].get(f"S2.{PRIMARY_UNIVERSE}", {})
        lines += ["", f"Full window at {result['switch_cost_bps'][0]} bp on {PRIMARY_UNIVERSE}: annualized mean net "
                  f"return R0 {_pct(full['R0']['annualized_mean'])} and R1 {_pct(full['R1']['annualized_mean'])}; "
                  f"volatility R0 {_pct(full['R0']['volatility'])} and R1 {_pct(full['R1']['volatility'])}; "
                  f"maximum drawdown R0 {_pct(full['R0']['max_drawdown'])} and R1 "
                  f"{_pct(full['R1']['max_drawdown'])}. The S2 test of the mean monthly difference R1 minus R0 has "
                  f"HAC p {_pvalue(s2.get('hac_pvalue'))} and BY q {_pvalue(s2.get('by_qvalue'))}."]
    lines += ["", "## Data Manifest", "",
              "| Source | Rows | First | Last | SHA-256 (prefix) | Retrieved (UTC) |",
              "| --- | ---: | --- | --- | --- | --- |"]
    for entry in result["manifest"]:
        lines.append(f"| {entry['id']} | {entry['rows']} | {entry['first_date'] or '-'} | "
                     f"{entry['last_date'] or '-'} | `{entry['sha256'][:16]}` | {entry['retrieved_utc']} |")
    lines += ["", "Full URLs and hashes: `reports/m5_public_data_manifest.json`. Raw files stay in the gitignored "
              "`data/public_cache/`.", "",
              "Attribution: JKP data by Jensen, Kelly, and Pedersen, jkpfactors.com, CC BY-NC 4.0 (Jensen, Kelly, "
              "and Pedersen (2023), Is There a Replication Crisis in Finance?, Journal of Finance, doi "
              "10.1111/jofi.13249). French factors: Kenneth R. French Data Library, copyright Eugene F. Fama and "
              "Kenneth R. French. Moody's BAA and AAA yields retrieved from FRED, Federal Reserve Bank of St. Louis "
              "(retrieved and hashed for step 3; unused here).", ""]

    lines += ["## Decision Conditions (jkp_factors_153)", "",
              "| Period | Cost | Metric | R0 | R1 | Holds |", "| --- | ---: | --- | ---: | ---: | --- |"]
    for c in decision["conditions"]:
        fmt = _pct if c["metric"] == "max_drawdown" else _num
        lines.append(f"| {PERIOD_LABEL[c['period']]} | {c['cost_bps']} bp | {c['metric']} | {fmt(c['R0'])} | "
                     f"{fmt(c['R1'])} | {'yes' if c['holds'] else 'no'} |")

    lines += ["", "## S2 Tests (R1 net minus R0 net at 20 bp, full window)", "",
              "Family S2 has 3 tests; Benjamini-Yekutieli adjustment with family size 3; two-sided Newey-West "
              "HAC p-values.", "",
              "| Test | Status | Months | Mean monthly difference (bp) | HAC t | HAC lags | p | BY q |",
              "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for test_id, stat in result["s2_tests"].items():
        lines.append(f"| {test_id} | {stat['status']} | {stat.get('n_observations', 'n/a')} | "
                     f"{_bp(stat.get('mean_return'))} | {_num(stat.get('hac_statistic'), 2)} | "
                     f"{stat.get('hac_lags', 'n/a')} | {_pvalue(stat.get('hac_pvalue'))} | "
                     f"{_pvalue(stat.get('by_qvalue'))} |")

    for universe_id, universe in result["universes"].items():
        lines += ["", f"## Universe {universe_id}", "",
                  f"Evaluated {universe['first_evaluated_month']} to {universe['last_evaluated_month']}; "
                  f"{universe['declared_factors']} declared factors; status `{universe['status']}`."]
        if universe["status"] != "completed":
            lines += ["", f"Refusal: {universe['reason']}"]
        else:
            lines += ["", "| Rule | Cost | Period | Months | Ann. mean | Volatility | Sharpe | Max drawdown | "
                      "Worst 12 months | Avg turnover |",
                      "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
            lines += _grid_rows(universe["rules"], result["switch_cost_bps"])
            members = universe["rules"]["R0"]["members_per_month"]
            lines += ["", f"Members per month: min {members['min']}, median {members['median']}, "
                      f"max {members['max']}."]
        market = universe["market_excess"]
        lines += ["", "Market excess return (French Mkt-RF, context only, no switch cost):", ""]
        if "status" in market:
            lines.append(f"Unavailable: {market['missing']} months missing.")
        else:
            lines += ["| Period | Ann. mean | Volatility | Sharpe | Max drawdown | Worst 12 months |",
                      "| --- | ---: | ---: | ---: | ---: | ---: |"]
            for period, m in market.items():
                lines.append(f"| {PERIOD_LABEL[period]} | {_pct(m['annualized_mean'])} | {_pct(m['volatility'])} | "
                             f"{_num(m['sharpe'])} | {_pct(m['max_drawdown'])} | "
                             f"{_pct(m['worst_12_month_return'])} |")
        lines += ["", "Volatility-forecast accuracy (Spearman of sigma_i,t with realized volatility over t..t+11, "
                  "pooled across factor-months):", "",
                  "| Period | Spearman | Pairs | Excluded: window past last month | Excluded: incomplete window |",
                  "| --- | ---: | ---: | ---: | ---: |"]
        for period, v in universe["volatility_forecast_accuracy"].items():
            lines.append(f"| {PERIOD_LABEL[period]} | {_num(v['spearman'])} | {v['pairs']} | "
                         f"{v['excluded_window_past_last_month']} | {v['excluded_incomplete_realized_window']} |")
        lines += ["", "Membership and missingness counts (factor-months):", "",
                  "| Period | Declared | In set | No month-t return | Fewer than 24 prior | Both | Typed missing |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
        for period, c in universe["counts"].items():
            typed = ", ".join(f"{k} {v}" for k, v in c["typed_missing_by_reason"].items()) or "none"
            lines.append(f"| {PERIOD_LABEL[period]} | {c['factor_months_declared']} | {c['factor_months_in_set']} | "
                         f"{c['excluded_no_return_in_month']} | {c['excluded_fewer_than_24_prior_returns']} | "
                         f"{c['excluded_both_conditions']} | {typed} |")
        lookback = universe["lookback_typed_missing"]
        typed = ", ".join(f"{k} {v}" for k, v in lookback["by_reason"].items()) or "none"
        lines += ["", f"Typed missing factor-months in the lookback-only months {lookback['months']}: {typed}. "
                  "They count against the 24-return condition and are never filled."]

    post = result["post_publication"]
    lines += ["", "## Post-Publication Split (jkp_factors_153, descriptive)", "",
              "For month t the set is restricted to factors whose publication year is before the calendar year of "
              "t; R0 and R1 use the same rules and costs in one continuous run from the first month with a non-empty "
              "subset (trial amendment 1).", "",
              f"Status `{post['status']}`; start month {post.get('start_month') or 'none'}."]
    if "empty_subset_months" in post:
        empty = post["empty_subset_months"]
        lines += ["", f"Evaluated months with an empty subset: {empty['count']}"
                  + (f" ({empty['first']} to {empty['last']})." if empty["count"] else ".")]
    if post["status"] == "refused":
        lines += ["", f"Refusal: {post['reason']}. An empty subset after the start month refuses the split, so "
                  "it has no metrics."]
    elif post["status"] == "completed":
        lines += ["", "| Rule | Cost | Period | Months | Ann. mean | Volatility | Sharpe | Max drawdown | "
                  "Worst 12 months | Avg turnover |",
                  "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        lines += _grid_rows(post["rules"], result["switch_cost_bps"])
    if "counts" in post:
        lines += ["", "| Period | In set | In subset | Missing publication year | Published in or after year | "
                  "Empty-subset months |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for period, c in post["counts"].items():
            lines.append(f"| {PERIOD_LABEL[period]} | {c['factor_months_in_set']} | {c['factor_months_in_subset']} | "
                         f"{c['excluded_missing_publication_year']} | "
                         f"{c['excluded_published_in_or_after_year']} | {c['months_with_empty_subset']} |")

    lines += ["", "## Limitations", "",
              "- Diagnostic ceiling: public long-short series, gross of each factor's internal trading and borrow "
              "costs, including small caps. The implementable check on the repository's point-in-time S&P 500 "
              "books after costs is step 4.",
              "- The comparison of R0 and R1 was already seen in two prior diagnostics on overlapping months; the "
              "halves reuse the same history and are not out-of-sample confirmation.",
              "- Month-t availability of a factor return enters the month-t set by declaration: a JKP return exists "
              "only when both extreme portfolios met the minimum stock count at formation at the end of month t-1.",
              "- The JKP and French files are revised by their providers; a later download can change results. The "
              "manifest pins the SHA-256 of the files used here.",
              "- Target weights are compared without drift adjustment, as declared; the switch cost is a flat rate "
              "on weight turnover.",
              "- Only the S2 comparison is tested; halves, the 50 bp level, the market, volatility-forecast "
              "accuracy, and the post-publication split are descriptive.",
              ""]
    return "\n".join(lines)


def _grid_rows(grid: dict[str, Any], costs: list[int]) -> list[str]:
    rows = []
    for rule in RULES:
        for cost in costs:
            for period, m in grid[rule][f"{cost}bp"].items():
                rows.append(f"| {rule} | {cost} bp | {PERIOD_LABEL[period]} | {m['months']} | "
                            f"{_pct(m['annualized_mean'])} | {_pct(m['volatility'])} | {_num(m['sharpe'])} | "
                            f"{_pct(m['max_drawdown'])} | {_pct(m['worst_12_month_return'])} | "
                            f"{_num(m['average_monthly_turnover'])} |")
    return rows


def _append_attempt(repo_root: Path, record: dict[str, Any]) -> None:
    path = repo_root / ATTEMPTS_JSONL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    attempt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    try:
        commit = git_state(REPO_ROOT)
    except subprocess.CalledProcessError:
        commit = {"commit": None, "tracked_changes": None}
    _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "start", **commit})
    try:
        result = run(REPO_ROOT)
        (REPO_ROOT / REPORT_JSON).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        (REPO_ROOT / REPORT_MD).write_text(render_report(result), encoding="utf-8")
    except Exception as error:
        _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "end", "status": "failed",
                                    "error": f"{type(error).__name__}: {error}"[:500]})
        raise
    outputs = {path: sha256_file(REPO_ROOT / path) for path in (REPORT_MD, REPORT_JSON, MANIFEST_JSON)}
    _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "end", "status": "completed",
                                "decision": result["decision"]["outcome"],
                                "trial_file_sha256": result["trial_file_sha256"], "outputs": outputs})
    print(f"decision: {result['decision']['outcome']}; report: {REPORT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
