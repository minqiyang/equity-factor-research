"""Milestone 5 step 3: state tilt (R2), factor momentum tilt (R3), and pooled ridge (R4) against R1.

Run with ``PYTHONPATH=src python -m research.m5_step3``. The command implements
``docs/preregistrations/m5_trial_family_v1_amendment_3.json`` (revision 2) on
top of v1 and amendments 1 and 2, plus the step 3 reporting conventions in
``docs/decision_log.md``. It refuses to run unless all four trial files equal
their committed HEAD version and their pinned SHA-256.

Timing (amendment 2): for return month t the signal month is t-2, so every
input to month t's set, weights, labels, cell histories, and R4 forecasts uses
factor returns and market data through month t-2 (the credit spread through
month t-3); the target executes at the month t-1 close and earns the month-t
return. Evidence ceiling ``DIAGNOSTIC_ONLY``: public long-short factor
returns, gross of each factor's internal trading and borrow costs.

Outputs: ``reports/m5_step3.md``, ``reports/m5_step3.json`` (aggregates only),
two new entries in ``reports/m5_public_data_manifest.json``, and one start and
one end record per attempt in ``reports/m5_step3_attempts.jsonl``. Raw
downloads stay in the gitignored ``data/public_cache/`` (R11).
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.linear_model import Ridge

from data.public_factors import (
    MISSING_CODE,
    PRESENT,
    MonthlyPanel,
    PublicDataRefusal,
    _fields,
    read_fred_csv,
    _zip_member_text,
    fetch,
    manifest_entry,
    sha256_file,
    write_manifest,
)
from features.diagnostics import newey_west_long_run_variance
from features.multiple_testing import P_VALUE_FLOOR, adjust_pvalues, return_test_statistics
from research import m5_factor_baseline as base


REPO_ROOT = base.REPO_ROOT
AMENDMENT_3_PATH = "docs/preregistrations/m5_trial_family_v1_amendment_3.json"
AMENDMENT_3_SHA256 = "c59f69c8262190ad7a1807d42a02e572667dcffa03c11a11c4d2e17a2bb5bfbb"
TRIAL_PINS = {base.TRIAL_PATH: base.TRIAL_SHA256, **base.AMENDMENTS, AMENDMENT_3_PATH: AMENDMENT_3_SHA256}
REPORT_MD = "reports/m5_step3.md"
REPORT_JSON = "reports/m5_step3.json"
ATTEMPTS_JSONL = "reports/m5_step3_attempts.jsonl"

UNIVERSE = "jkp_factors_153"
STATES = ("market_trend", "market_volatility", "credit_spread")
CELLS = {"market_trend": ("up", "down"), "market_volatility": ("high", "normal"),
         "credit_spread": ("wide", "normal")}  # label 1.0 is the first cell, 0.0 the second
HIGH_TURNOVER_CLASSES = ("Short-Term Reversal", "Seasonality", "Momentum")
DATA_SOURCES = ("accounting", "composite", "market")
PRE_SEEN = {("Momentum", "market_trend"), ("Low Risk", "market_volatility"), ("Quality", "market_volatility"),
            ("Value", "market_volatility"), ("Size", "market_volatility"), ("Momentum", "market_volatility")}
RULES = ("R0", "R1", "R2", "R3", "R4")
TILTED_RULES = ("R2", "R3", "R4")

LAG = base.SIGNAL_LAG_MONTHS
TREND_MONTHS = 12
VOL_DAYS = 63
VOL_MIN_MONTHS = 60
CREDIT_LAG = 3
CREDIT_WINDOW = 120
TRAILING_MONTHS = 12
TILT = 0.5
SHRINKAGE_EPISODES = 10
EPISODE_MINIMUM = 10
R4_MIN_TRAINING_MONTHS = 36
R4_MIN_COVERED = 2
OBSERVED_TESTS = 42
FAMILY_SIZE = 1047
NULL_DRAWS = 999
NULL_SEED = 20260928
NULL_MIN_OFFSET = 60
TOLERANCE = 1e-12
SURVIVAL_LEVEL = 0.05
Z95 = 1.959964
ACC_CHARS_COUNT = 315
HIGH_TURNOVER_COUNT = 26
HALVES = ("first_half", "second_half")


def slug(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


# Trial files -------------------------------------------------------------------

def verify_trial_files(repo_root: Path, pins: dict[str, str] = TRIAL_PINS) -> dict[str, bytes]:
    """Return each trial file's bytes after checking HEAD equality and the pinned SHA-256."""

    contents = {}
    for path, pinned in pins.items():
        content, digest = base.verify_trial_file(repo_root, path)
        if digest != pinned:
            raise PublicDataRefusal(f"trial file {path} SHA-256 {digest} differs from the pinned {pinned}")
        contents[path] = content
    return contents


# New public sources --------------------------------------------------------------

def read_french_daily_zip(path: Path, member: str, *, column: str) -> tuple[pd.Series, pd.Series, int]:
    """Parse one column of the daily block of a Ken French CSV inside a zip file.

    Rows whose first field is an eight-digit YYYYMMDD are read; values are
    percent per day and become decimals. The codes -99.99 and -999 become NaN
    typed ``provider_missing_code`` in the returned reason series; nothing is
    filled. A repeated or non-calendar date refuses the load.
    """

    lines = _zip_member_text(path, member).splitlines()
    rows = [i for i, line in enumerate(lines) if re.fullmatch(r"\d{8}", _fields(line)[0])]
    if not rows:
        raise PublicDataRefusal(f"{member}: no eight-digit YYYYMMDD rows")
    header_rows = [i for i in range(rows[0]) if _fields(lines[i])[0] == "" and len(_fields(lines[i])) > 1]
    if not header_rows:
        raise PublicDataRefusal(f"{member}: no header line before the first daily row")
    header = _fields(lines[header_rows[-1]])[1:]
    if column not in header:
        raise PublicDataRefusal(f"{member}: header {header} lacks {column}")
    position = header.index(column) + 1
    dates, values, reasons = [], [], []
    for i in rows:
        fields = _fields(lines[i])
        if len(fields) != len(header) + 1:
            raise PublicDataRefusal(f"{member}: line {i + 1} has {len(fields)} fields, expected {len(header) + 1}")
        date = pd.to_datetime(fields[0], format="%Y%m%d", errors="coerce")
        if pd.isna(date):
            raise PublicDataRefusal(f"{member}: line {i + 1} date is not a calendar date")
        try:
            raw = float(fields[position])
        except ValueError:
            raise PublicDataRefusal(f"{member}: non-numeric {column} on line {i + 1}") from None
        if raw in (-99.99, -999.0):
            values.append(np.nan)
            reasons.append(MISSING_CODE)
        elif not math.isfinite(raw):
            raise PublicDataRefusal(f"{member}: non-finite {column} on line {i + 1}")
        else:
            values.append(raw / 100.0)
            reasons.append(PRESENT)
        dates.append(date)
    index = pd.DatetimeIndex(dates)
    if index.has_duplicates or not index.is_monotonic_increasing:
        raise PublicDataRefusal(f"{member}: dates repeat or are out of order")
    return pd.Series(values, index=index, dtype=float), pd.Series(reasons, index=index, dtype=object), len(rows)


def read_accounting_characteristics(path: Path) -> list[str]:
    """The list literal assigned to ``acc_chars`` inside ``acc_chars_list()`` of jkp-data aux_functions.py.

    The file is parsed, never executed. Anything other than exactly one such
    assignment of a list of strings refuses.
    """

    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "acc_chars_list"]
    if len(functions) != 1:
        raise PublicDataRefusal(f"{path.name}: expected one function acc_chars_list, found {len(functions)}")
    assigns = [node for node in ast.walk(functions[0]) if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id == "acc_chars" for target in node.targets)]
    if len(assigns) != 1:
        raise PublicDataRefusal(f"{path.name}: expected one assignment to acc_chars, found {len(assigns)}")
    try:
        names = ast.literal_eval(assigns[0].value)
    except ValueError:
        raise PublicDataRefusal(f"{path.name}: acc_chars is not a literal list") from None
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise PublicDataRefusal(f"{path.name}: acc_chars is not a list of strings")
    return names


def data_source_map(factors: list[str], accounting_list: list[str], trial: dict[str, Any]) -> pd.Series:
    """v1 data_source trait: accounting, composite, or market for each factor; any overlap or gap refuses."""

    declared = trial["traits"]["data_source"]
    accounting = {name for name in factors if name in set(accounting_list)}
    composite, market = set(declared["composite"]), set(declared["market"])
    groups = (accounting, composite, market)
    overlap = (accounting & composite) | (accounting & market) | (composite & market)
    if overlap or set().union(*groups) != set(factors):
        raise PublicDataRefusal(
            f"data_source groups do not partition the factors (overlap {sorted(overlap)}, "
            f"gap {sorted(set(factors) - set().union(*groups))}, extra {sorted(set().union(*groups) - set(factors))})")
    return pd.Series({name: next(label for label, group in zip(DATA_SOURCES, groups) if name in group)
                      for name in factors})


# Inputs ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Step3Data:
    """In-memory inputs; the real run and the synthetic tests build the same object."""

    returns: pd.DataFrame           # factor returns on a complete monthly index, NaN where missing
    missing: pd.DataFrame           # the typed reason for each NaN
    classes: pd.Series              # factor -> JKP cluster
    data_source: pd.Series          # factor -> accounting | composite | market
    publication_years: dict[str, int | None]
    market_monthly: pd.DataFrame    # French Mkt-RF and RF, decimals, monthly
    market_daily: pd.Series         # French daily Mkt-RF, decimals, NaN for a missing code
    credit: pd.DataFrame            # FRED BAA and AAA, percent per year, monthly
    first: pd.Period
    last: pd.Period

    @property
    def class_order(self) -> list[str]:
        return sorted(set(self.classes))


# State labels ---------------------------------------------------------------------

def market_trend_labels(total: pd.Series, months: pd.PeriodIndex) -> pd.Series:
    """1 (up) when prod(1 + r) - 1 over months t-13..t-2 is above 0, 0 (down) otherwise; NaN if any month is missing."""

    labels = []
    for month in months:
        window = total.loc[month - (TREND_MONTHS + LAG - 1): month - LAG]
        if len(window) != TREND_MONTHS or window.isna().any():
            labels.append(np.nan)
            continue
        labels.append(1.0 if float(np.prod(1.0 + window.to_numpy())) - 1.0 > 0 else 0.0)
    return pd.Series(labels, index=months, dtype=float)


def month_end_volatility(daily: pd.Series) -> pd.Series:
    """ddof-1 std of the last 63 daily returns ending on each month's last trading day, times sqrt(252).

    NaN when fewer than 63 trading days exist or any of them is missing.
    """

    values = daily.to_numpy(dtype=float)
    month_of = daily.index.to_period("M")
    last_position = pd.Series(np.arange(len(values)), index=month_of).groupby(level=0).max()
    result = {}
    for month, position in last_position.items():
        window = values[position - VOL_DAYS + 1: position + 1] if position >= VOL_DAYS - 1 else np.array([])
        result[month] = (float(np.std(window, ddof=1)) * math.sqrt(252)
                         if len(window) == VOL_DAYS and np.isfinite(window).all() else np.nan)
    series = pd.Series(result, dtype=float)
    return series.reindex(pd.period_range(series.index[0], series.index[-1], freq="M"))


def market_volatility_labels(daily: pd.Series, months: pd.PeriodIndex) -> pd.Series:
    """1 (high) when the month t-2 value exceeds the expanding median through t-2 (at least 60 values)."""

    volatility = month_end_volatility(daily)
    values = volatility.to_numpy()
    medians, counts = np.full(len(values), np.nan), np.zeros(len(values), dtype=int)
    for i in range(len(values)):
        past = values[: i + 1]
        past = past[np.isfinite(past)]
        counts[i] = len(past)
        if len(past):
            medians[i] = float(np.median(past))
    median = pd.Series(medians, index=volatility.index)
    count = pd.Series(counts, index=volatility.index)
    labels = []
    for month in months:
        signal = month - LAG
        value = volatility.get(signal, np.nan)
        if not np.isfinite(value) or count.get(signal, 0) < VOL_MIN_MONTHS:
            labels.append(np.nan)
        else:
            labels.append(1.0 if value > median[signal] else 0.0)
    return pd.Series(labels, index=months, dtype=float)


def credit_spread_labels(credit: pd.DataFrame, months: pd.PeriodIndex) -> pd.Series:
    """1 (wide) when BAA - AAA at month t-3 exceeds the median of months t-122..t-3 (all 120 present)."""

    spread = credit["BAA"] - credit["AAA"]
    labels = []
    for month in months:
        signal = month - CREDIT_LAG
        window = spread.loc[signal - (CREDIT_WINDOW - 1): signal]
        if len(window) != CREDIT_WINDOW or window.isna().any():
            labels.append(np.nan)
        else:
            labels.append(1.0 if float(window.iloc[-1]) > float(np.median(window.to_numpy())) else 0.0)
    return pd.Series(labels, index=months, dtype=float)


def state_labels(data: Step3Data, months: pd.PeriodIndex) -> pd.DataFrame:
    total = data.market_monthly["Mkt-RF"] + data.market_monthly["RF"]
    return pd.DataFrame({
        "market_trend": market_trend_labels(total, months),
        "market_volatility": market_volatility_labels(data.market_daily, months),
        "credit_spread": credit_spread_labels(data.credit, months),
    })


# Classes and the label span ------------------------------------------------------

def class_returns(returns: pd.DataFrame, in_set: pd.DataFrame, sigma: pd.DataFrame, classes: pd.Series,
                  class_order: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """r_k,u: R1 (1/sigma) applied within class k over month u's set, gross.

    A class-month with no member (``no_member``) or with a member lacking its
    month-u return (``member_return_missing``) is NaN with that reason; nothing
    is reallocated. A zero or non-finite member sigma refuses, as in R1.
    """

    months = in_set.index
    held = returns.reindex(index=months, columns=in_set.columns)
    member_sigma = sigma.where(in_set)
    degenerate = in_set & ~(np.isfinite(member_sigma) & (member_sigma > 0))
    if degenerate.to_numpy().any():
        raise PublicDataRefusal(f"{int(degenerate.to_numpy().sum())} member-months have a zero or non-finite sigma")
    inverse = (1.0 / member_sigma).where(in_set, 0.0)
    values, reasons = {}, {}
    for name in class_order:
        columns = [column for column in in_set.columns if classes[column] == name]
        members = in_set[columns]
        weighted = (inverse[columns] * held[columns]).where(members, 0.0).sum(axis=1)
        value = weighted / inverse[columns].sum(axis=1)
        no_member = members.sum(axis=1) == 0
        lacking = (members & held[columns].isna()).any(axis=1)
        reason = pd.Series(PRESENT, index=months, dtype=object)
        reason[lacking] = "member_return_missing"
        reason[no_member] = "no_member"
        values[name] = value.where(reason == PRESENT)
        reasons[name] = reason
    return pd.DataFrame(values, index=months), pd.DataFrame(reasons, index=months)


def label_span_start(labels: pd.DataFrame, class_values: pd.DataFrame, last: pd.Period) -> pd.Period:
    """First month with all three labels and at least one class return; a missing label inside the span refuses."""

    defined = labels.notna().all(axis=1) & class_values.reindex(labels.index).notna().any(axis=1)
    if not defined.any():
        raise PublicDataRefusal("no month has all three labels and a class return, so the label span is empty")
    start = defined.index[defined.to_numpy().argmax()]
    inside = labels.loc[start:last]
    if inside.isna().to_numpy().any():
        gaps = inside.isna()
        raise PublicDataRefusal(
            f"{int(gaps.to_numpy().sum())} typed-missing labels inside the label span "
            f"(first {gaps.any(axis=1).idxmax()}, states {[s for s in STATES if gaps[s].any()]})")
    return start


# R2 --------------------------------------------------------------------------------

def r2_tilt(class_values: np.ndarray, labels: np.ndarray, positions: np.ndarray) -> dict[str, np.ndarray]:
    """R2 class multipliers at span positions ``positions`` from span arrays.

    ``class_values`` is span months x classes (NaN = undefined), ``labels`` is
    span months x states (1.0 first cell, 0.0 second). For month t at
    position p the history is span positions u <= p - 2 in the current cell
    with a defined class return; m is their mean, E the number of runs of the
    current cell starting at or before p - 2, lambda = E / (E + 10). The
    score is the mean over states of sign(m) * lambda (0 for an empty
    history), and the multiplier is 1 + 0.5 * score.
    """

    n_states = labels.shape[1]
    defined = ~np.isnan(class_values)
    value = np.where(defined, class_values, 0.0)
    end = positions - LAG
    has_history = end >= 0
    at = np.where(has_history, end, 0)
    score = np.zeros((len(positions), class_values.shape[1]))
    lambdas = np.zeros((len(positions), n_states))
    episodes = np.zeros((len(positions), n_states), dtype=int)
    means = np.full((len(positions), class_values.shape[1], n_states), np.nan)
    for s in range(n_states):
        series = labels[:, s]
        current = series[positions] == 1.0
        run_start = np.r_[True, series[1:] != series[:-1]]
        sums, counts, starts = {}, {}, {}
        for cell in (0.0, 1.0):
            in_cell = series == cell
            sums[cell] = np.cumsum(value * in_cell[:, None], axis=0)
            counts[cell] = np.cumsum(defined & in_cell[:, None], axis=0)
            starts[cell] = np.cumsum(run_start & in_cell)
        cell_sum = np.where(current[:, None], sums[1.0][at], sums[0.0][at])
        cell_count = np.where(current[:, None], counts[1.0][at], counts[0.0][at]) * has_history[:, None]
        count_e = np.where(current, starts[1.0][at], starts[0.0][at]) * has_history
        mean = np.divide(cell_sum, cell_count, out=np.full(cell_sum.shape, np.nan), where=cell_count > 0)
        lam = count_e / (count_e + SHRINKAGE_EPISODES)
        score += np.where(cell_count > 0, np.sign(np.nan_to_num(mean)), 0.0) * lam[:, None]
        lambdas[:, s], episodes[:, s], means[:, :, s] = lam, count_e, mean
    return {"multipliers": 1.0 + TILT * score / n_states, "lambdas": lambdas, "episodes": episodes, "means": means}


def span_positions(months: pd.PeriodIndex, span_start: pd.Period) -> np.ndarray:
    return np.asarray([(month - span_start).n for month in months], dtype=int)


def r2_on_months(class_values: pd.DataFrame, labels: pd.DataFrame, span_start: pd.Period, last: pd.Period,
                 months: pd.PeriodIndex) -> dict[str, Any]:
    """R2 multipliers for ``months``; a month before the span start has no history and multiplier 1."""

    span_values = class_values.loc[span_start:last].to_numpy()
    span_labels = labels.loc[span_start:last, list(STATES)].to_numpy()
    positions = span_positions(months, span_start)
    valid = positions >= 0
    tilt = r2_tilt(span_values, span_labels, positions[valid])
    multipliers = np.ones((len(months), class_values.shape[1]))
    lambdas = np.zeros((len(months), len(STATES)))
    episodes = np.zeros((len(months), len(STATES)), dtype=int)
    means = np.full((len(months), class_values.shape[1], len(STATES)), np.nan)
    multipliers[valid], lambdas[valid], episodes[valid], means[valid] = (
        tilt["multipliers"], tilt["lambdas"], tilt["episodes"], tilt["means"])
    return {"multipliers": pd.DataFrame(multipliers, index=months, columns=class_values.columns),
            "lambdas": pd.DataFrame(lambdas, index=months, columns=list(STATES)),
            "episodes": pd.DataFrame(episodes, index=months, columns=list(STATES)),
            "means": means, "span_values": span_values, "span_labels": span_labels,
            "positions": positions, "valid": valid}


def tilt_array(w1: np.ndarray, multiplier: np.ndarray, block: np.ndarray) -> np.ndarray:
    """w_i = w1_i * M_i * (sum over block of w1) / (sum over block of w1 * M) inside the block; w1 outside."""

    inside = np.where(block, w1, 0.0)
    tilted = inside * np.where(block, multiplier, 0.0)
    total, tilted_total = inside.sum(axis=1), tilted.sum(axis=1)
    scale = np.divide(total, tilted_total, out=np.zeros_like(total), where=tilted_total > 0)
    return np.where(block, tilted * scale[:, None], w1)


def tilt(w1: pd.DataFrame, multiplier: pd.DataFrame, block: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(tilt_array(w1.to_numpy(), multiplier.reindex_like(w1).to_numpy(),
                                   block.reindex_like(w1).fillna(False).to_numpy(dtype=bool)),
                        index=w1.index, columns=w1.columns)


def factor_multipliers(class_multipliers: pd.DataFrame, classes: pd.Series, columns: pd.Index) -> pd.DataFrame:
    return pd.DataFrame(class_multipliers[[classes[column] for column in columns]].to_numpy(),
                        index=class_multipliers.index, columns=columns)


def r2_weights(w1: pd.DataFrame, in_set: pd.DataFrame, class_multipliers: pd.DataFrame,
               classes: pd.Series) -> pd.DataFrame:
    return tilt(w1, factor_multipliers(class_multipliers, classes, w1.columns), in_set.loc[w1.index])


# R3 ----------------------------------------------------------------------------------

def trailing_return(returns: pd.DataFrame, months: pd.PeriodIndex) -> pd.DataFrame:
    """prod(1 + r) - 1 over months t-13..t-2; NaN unless all 12 returns exist."""

    rows = []
    for month in months:
        window = returns.loc[month - (TRAILING_MONTHS + LAG - 1): month - LAG]
        complete = (window.notna().sum() == TRAILING_MONTHS) & (len(window) == TRAILING_MONTHS)
        rows.append((1.0 + window).prod().sub(1.0).where(complete))
    return pd.DataFrame(rows, index=months, columns=returns.columns).astype(float)


def r3_weights(w1: pd.DataFrame, in_set: pd.DataFrame, trailing: pd.DataFrame) -> pd.DataFrame:
    signal = trailing.loc[w1.index, w1.columns]
    multiplier = 1.0 + TILT * np.sign(signal)
    return tilt(w1, multiplier, in_set.loc[w1.index] & signal.notna())


# R4 ----------------------------------------------------------------------------------

def r4_trait_names(class_order: list[str]) -> list[str]:
    return ([f"theme={name}" for name in class_order] + [f"data_source={name}" for name in DATA_SOURCES]
            + ["turnover_class=high", "rank_trailing_12m_return", "rank_trailing_36m_volatility",
               "rank_years_since_publication"])


def r4_feature_names(class_order: list[str]) -> list[str]:
    traits = r4_trait_names(class_order)
    states = [f"state={state}" for state in STATES]
    return traits + states + [f"{trait}*{state}" for trait in traits for state in states]


def rank_scaled(values: pd.DataFrame, covered: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional average rank among covered rows scaled by (rank - 1) / (n - 1) - 0.5; 0 when n = 1."""

    ranks = values.where(covered).rank(axis=1, method="average").to_numpy()
    n = covered.sum(axis=1).to_numpy(dtype=float)[:, None]
    scaled = np.divide(ranks - 1.0, n - 1.0, out=np.zeros_like(ranks), where=n > 1) - 0.5
    scaled = np.where(n > 1, scaled, 0.0)
    return pd.DataFrame(np.where(covered.to_numpy(), scaled, np.nan), index=values.index, columns=values.columns)


@dataclass(frozen=True)
class R4Design:
    months: pd.PeriodIndex           # return month of each row
    factors: np.ndarray              # factor name of each row
    features: np.ndarray             # rows x 83
    target: np.ndarray               # the row's month-t return
    names: list[str]
    covered: pd.DataFrame


def r4_design(months: pd.PeriodIndex, in_set: pd.DataFrame, publication_trait: pd.DataFrame,
              trailing: pd.DataFrame, sigma: pd.DataFrame, data: Step3Data, labels: pd.DataFrame) -> R4Design:
    """Covered factor-months (set member with years_since_publication and trailing return) and their 83 features."""

    columns = in_set.columns
    covered = in_set.loc[months] & publication_trait.loc[months, columns].notna() & trailing.loc[months, columns].notna()
    ranks = [rank_scaled(frame.loc[months, columns], covered)
             for frame in (trailing, sigma, publication_trait)]
    row, col = np.nonzero(covered.to_numpy())
    class_order = data.class_order
    theme = np.array([[data.classes[name] == k for k in class_order] for name in columns], dtype=float)
    source = np.array([[data.data_source[name] == k for k in DATA_SOURCES] for name in columns], dtype=float)
    high = np.array([[data.classes[name] in HIGH_TURNOVER_CLASSES] for name in columns], dtype=float)
    traits = np.hstack([theme[col], source[col], high[col]] + [rank.to_numpy()[row, col][:, None] for rank in ranks])
    states = np.where(labels.loc[months, list(STATES)].to_numpy()[row] == 1.0, 0.5, -0.5)
    interactions = (traits[:, :, None] * states[:, None, :]).reshape(len(row), -1)
    features = np.hstack([traits, states, interactions])
    target = data.returns.loc[months, columns].to_numpy()[row, col]
    return R4Design(months[row], np.asarray(columns)[col], features, target, r4_feature_names(class_order), covered)


def r4_fit(design: R4Design, year: int) -> dict[str, Any]:
    """Ridge (alpha = training rows) on covered pairs whose return month is at most November of year - 1."""

    cutoff = pd.Period(f"{year - 1}-11", freq="M")
    train = np.asarray(design.months <= cutoff)
    months = int(pd.Series(design.months[train]).nunique())
    record: dict[str, Any] = {"year": year, "training_rows": int(train.sum()), "training_months": months,
                              "last_training_month": str(cutoff)}
    if months < R4_MIN_TRAINING_MONTHS:
        return {**record, "status": "too_few_training_months"}
    if np.isnan(design.target[train]).any() or not np.isfinite(design.features[train]).all():
        return {**record, "status": "missing_training_value"}
    model = Ridge(alpha=float(train.sum()), fit_intercept=True).fit(design.features[train], design.target[train])
    return {**record, "status": "fit", "model": model, "intercept": float(model.intercept_),
            "coefficients": dict(zip(design.names, map(float, model.coef_)))}


def r4_forecasts(design: R4Design, years: list[int]) -> tuple[pd.DataFrame, dict[int, dict[str, Any]]]:
    forecast = pd.DataFrame(np.nan, index=design.covered.index, columns=design.covered.columns)
    fits = {}
    row_years = np.asarray(design.months.year)
    for year in years:
        fit = r4_fit(design, year)
        rows = row_years == year
        fit["forecast_rows"] = int(rows.sum()) if fit["status"] == "fit" else 0
        if fit["status"] == "fit" and rows.any():
            predicted = fit["model"].predict(design.features[rows])
            for month, name, value in zip(design.months[rows], design.factors[rows], predicted):
                forecast.at[month, name] = float(value)
        fits[year] = fit
    return forecast, fits


def r4_weights(w1: pd.DataFrame, forecast: pd.DataFrame) -> pd.DataFrame:
    """Forecast ranks tilt R1 by 1 + 0.5 z, z in [-1, 1]; fewer than 2 forecasts leave the month at R1."""

    signal = forecast.loc[w1.index, w1.columns]
    count = signal.notna().sum(axis=1)
    block = signal.notna() & (count >= R4_MIN_COVERED).to_numpy()[:, None]
    ranks = signal.where(block).rank(axis=1, method="average")
    z = 2.0 * (ranks - 1.0).div((count - 1).where(count >= R4_MIN_COVERED), axis=0) - 1.0
    return tilt(w1, 1.0 + TILT * z.fillna(0.0), block)


# Statistics ---------------------------------------------------------------------

def hac_lags(count: int) -> int:
    return int(np.floor(4.0 * (count / 100.0) ** (2.0 / 9.0)))


def state_effect_statistic(y: np.ndarray, d: np.ndarray, lags: int | None = None) -> dict[str, Any]:
    """OLS slope of y on an intercept and D with the amendment 3 HAC variance n * LRV(g) / Sxx^2."""

    y, d = np.asarray(y, dtype=float), np.asarray(d, dtype=float)
    n = len(y)
    lags = hac_lags(n) if lags is None else lags
    result: dict[str, Any] = {"status": "undefined", "n": n, "lags": lags, "b": None, "t": None, "p": None}
    centered = d - d.mean() if n else d
    sxx = float(centered @ centered)
    if n < 3 or sxx <= 0:
        return result
    b = float(centered @ y) / sxx
    residual = y - (y.mean() - b * d.mean()) - b * d
    lrv = newey_west_long_run_variance(centered * residual, lags)
    if not math.isfinite(lrv):
        return {**result, "b": b}
    t_stat = b / math.sqrt(n * lrv / sxx ** 2)
    if not math.isfinite(t_stat):
        return {**result, "b": b}
    return {**result, "status": "ok", "b": b, "t": t_stat, "p": max(P_VALUE_FLOOR, float(2 * norm.sf(abs(t_stat))))}


def rule_test(difference: pd.Series) -> dict[str, Any]:
    """S3 rule test with the decision-log 95% pointwise interval mean +/- 1.959964 * sqrt(LRV / n)."""

    statistic = dict(return_test_statistics(difference, periods_per_year=base.MONTHS_PER_YEAR))
    statistic.update(standard_error=None, ci95_monthly=None, ci95_annual=None)
    if statistic["status"] == "ok":
        n = int(statistic["n_observations"])
        lrv = newey_west_long_run_variance(difference.to_numpy(dtype=float), int(statistic["hac_lags"]))
        se = math.sqrt(lrv / n)
        mean = float(statistic["mean_return"])
        low, high = mean - Z95 * se, mean + Z95 * se
        statistic.update(standard_error=se, ci95_monthly=[low, high],
                         ci95_annual=[base.MONTHS_PER_YEAR * low, base.MONTHS_PER_YEAR * high])
    return statistic


def s3_adjust(pvalues: pd.Series, family_size: int = FAMILY_SIZE) -> pd.Series:
    """BY over the 42 observed S3 p-values with the 1005 prior slots at p = 1; any other count refuses."""

    if len(pvalues) != OBSERVED_TESTS or family_size != FAMILY_SIZE:
        raise PublicDataRefusal(f"S3 family needs {OBSERVED_TESTS} observed p-values and family size {FAMILY_SIZE}, "
                                f"got {len(pvalues)} and {family_size}")
    return adjust_pvalues(pvalues, method="by", family_size=family_size)


def null_offsets(n: int, draws: int = NULL_DRAWS) -> np.ndarray:
    if n - NULL_MIN_OFFSET < NULL_MIN_OFFSET:
        raise PublicDataRefusal(f"label span of {n} months is too short for offsets in [60, n - 60]")
    return np.random.default_rng(NULL_SEED).integers(NULL_MIN_OFFSET, n - NULL_MIN_OFFSET, size=draws,
                                                     endpoint=True)


def shift_labels(span_labels: np.ndarray, offset: int) -> np.ndarray:
    """Circular shift inside the span: the label at position j moves to position (j + offset) mod n."""

    return np.roll(span_labels, int(offset), axis=0)


def random_date_pvalue(observed: float | None, draws: np.ndarray) -> dict[str, Any]:
    """(1 + draws with |t| >= |t_observed| or an undefined t) / (draws + 1); undefined when t_observed is."""

    undefined = ~np.isfinite(draws)
    result = {"draws": int(len(draws)), "undefined_draws": int(undefined.sum()), "exceedances": None, "p": None}
    if observed is None or not math.isfinite(observed):
        return result
    exceed = undefined | (np.abs(np.where(undefined, 0.0, draws)) >= abs(observed))
    return {**result, "exceedances": int(exceed.sum()), "p": (1 + int(exceed.sum())) / (len(draws) + 1)}


def episode_count(labels: pd.Series, cell: float) -> int:
    values = labels.to_numpy()
    in_cell = values == cell
    return int((in_cell & np.r_[True, values[1:] != values[:-1]]).sum())


def eligibility(labels: pd.DataFrame, bounds: dict[str, tuple[pd.Period, pd.Period]]) -> dict[str, Any]:
    """Per state: episodes of each cell in each half on the observed labels; eligible when every count is >= 10."""

    result = {}
    for state in STATES:
        counts = {half: {cell_name: episode_count(labels.loc[bounds[half][0]:bounds[half][1], state], value)
                         for cell_name, value in zip(CELLS[state], (1.0, 0.0))}
                  for half in HALVES}
        result[state] = {"episodes": counts,
                         "eligible": all(count >= EPISODE_MINIMUM for half in counts.values() for count in half.values())}
    return result


# Decision predicates ----------------------------------------------------------

def not_worse(margin: float | None) -> bool:
    return margin is not None and (margin >= 0 or abs(margin) < TOLERANCE)


def closure_conditions(grid: dict[str, Any], rule: str, costs: list[int]) -> list[dict[str, Any]]:
    """The 8 step 2 conditions with ``rule`` in place of R1 and R1 in place of R0, with the 1e-12 tolerance."""

    conditions = []
    for period in HALVES:
        for cost in costs:
            mine, r1 = grid[rule][f"{cost}bp"][period], grid["R1"][f"{cost}bp"][period]
            drawdown = abs(r1["max_drawdown"]) - abs(mine["max_drawdown"])
            conditions.append({"period": period, "cost_bps": cost, "metric": "max_drawdown", "rule": mine["max_drawdown"],
                               "R1": r1["max_drawdown"], "margin": drawdown, "holds": not_worse(drawdown)})
            sharpe = (None if mine["sharpe"] is None or r1["sharpe"] is None else mine["sharpe"] - r1["sharpe"])
            conditions.append({"period": period, "cost_bps": cost, "metric": "sharpe", "rule": mine["sharpe"],
                               "R1": r1["sharpe"], "margin": sharpe, "holds": not_worse(sharpe)})
    return conditions


def closure_decision(conditions: list[dict[str, Any]]) -> str:
    return "open" if len(conditions) == 8 and all(c["holds"] for c in conditions) else "closed"


def post_publication_condition(post: dict[str, Any], costs: list[int]) -> dict[str, Any]:
    """Condition 5: on the subset's full period R2-sub is not worse than R1-sub at both costs, and mean(d) > 0."""

    if post.get("status") != "completed" or "full" not in post.get("rules", {}).get("R2", {}).get(f"{costs[0]}bp", {}):
        return {"holds": False, "detail": "post-publication period is empty or refused"}
    checks = []
    for cost in costs:
        r1, r2 = post["rules"]["R1"][f"{cost}bp"]["full"], post["rules"]["R2"][f"{cost}bp"]["full"]
        if not r1.get("months") or not r2.get("months"):
            return {"holds": False, "detail": "post-publication period is empty"}
        sharpe = None if r1["sharpe"] is None or r2["sharpe"] is None else r2["sharpe"] - r1["sharpe"]
        drawdown = (None if r1["max_drawdown"] is None or r2["max_drawdown"] is None
                    else abs(r1["max_drawdown"]) - abs(r2["max_drawdown"]))
        checks += [not_worse(sharpe), not_worse(drawdown)]
    mean = post.get("mean_difference_20bp")
    holds = all(checks) and mean is not None and math.isfinite(mean) and mean > 0
    return {"holds": bool(holds), "detail": f"Sharpe and drawdown checks {checks}; mean R2-sub minus R1-sub {mean}"}


def r2_timing_claim(conditions: list[dict[str, Any]], mean_difference: float | None, qvalue: float | None,
                    random_p: float | None, post: dict[str, Any], states: dict[str, Any],
                    costs: list[int]) -> dict[str, Any]:
    post_check = post_publication_condition(post, costs)
    checks = [
        ("1", "R2 meets all 8 closure conditions", closure_decision(conditions) == "open"),
        ("2", "full-window mean of the S3.R2 difference is positive",
         mean_difference is not None and mean_difference > 0),
        ("3", "S3.R2 BY q-value <= 0.05", qvalue is not None and qvalue <= SURVIVAL_LEVEL),
        ("4", "S3.R2 random-date p-value is defined and <= 0.05", random_p is not None and random_p <= SURVIVAL_LEVEL),
        ("5", "post-publication R2-sub is not worse than R1-sub at 20 and 50 bp and its mean difference is positive",
         post_check["holds"]),
        ("6", "each of R2's three states is eligible under the episode rule",
         all(states[state]["eligible"] for state in STATES)),
    ]
    listed = [{"condition": number, "text": text, "holds": bool(holds)} for number, text, holds in checks]
    return {"qualifies": all(item["holds"] for item in listed), "conditions": listed,
            "failed": [item["condition"] for item in listed if not item["holds"]],
            "post_publication_detail": post_check["detail"]}


def cell_survives(qvalue: float | None, random_p: float | None, eligible: bool, b_full: float | None,
                  others: list[float | None]) -> bool:
    if qvalue is None or qvalue > SURVIVAL_LEVEL or random_p is None or random_p > SURVIVAL_LEVEL or not eligible:
        return False
    if b_full is None or b_full == 0:
        return False
    return all(b is not None and b != 0 and np.sign(b) == np.sign(b_full) for b in others)


# Portfolios ---------------------------------------------------------------------

def rule_books(weights: pd.DataFrame, returns: pd.DataFrame, costs: list[int],
               bounds: dict[str, tuple[pd.Period, pd.Period]]) -> tuple[dict[str, Any], dict[int, pd.DataFrame]]:
    grid, books = {}, {}
    for cost in costs:
        book = base.portfolio(weights, returns, cost)
        books[cost] = book
        grid[f"{cost}bp"] = {period: base.performance(book["net"].loc[start:end], book["turnover"].loc[start:end])
                             for period, (start, end) in bounds.items()}
    return grid, books


def differs_share(tilted: pd.DataFrame, w1: pd.DataFrame, bounds: dict[str, tuple[pd.Period, pd.Period]]) -> dict:
    differs = (tilted - w1).abs().max(axis=1) > TOLERANCE
    return {period: float(differs.loc[start:end].mean()) for period, (start, end) in bounds.items()}


def mean_by_period(frame: pd.DataFrame, bounds: dict[str, tuple[pd.Period, pd.Period]]) -> dict:
    return {period: {column: float(frame.loc[start:end, column].mean()) for column in frame.columns}
            for period, (start, end) in bounds.items()}


# Evaluation ----------------------------------------------------------------------

def build_rules(data: Step3Data, trial: dict[str, Any]) -> dict[str, Any]:
    """Every decision-time quantity: set, sigma, labels, class returns, span, and R1 to R4 weights.

    Uses no portfolio return, so it runs on inputs whose holding-month
    returns are missing (the future-perturbation tests need that).
    """

    returns, missing = base.universe_panel(data.returns, data.missing, data.first, data.last)
    all_months = returns.index
    months = pd.period_range(data.first, data.last, freq="M")
    member = base.membership(returns, missing, all_months)
    in_set, sigma = member.in_set, member.sigma
    classes, class_order = data.classes, data.class_order
    class_values, class_reasons = class_returns(returns, in_set, sigma, classes, class_order)
    labels = state_labels(data, all_months)
    span_start = label_span_start(labels, class_values, data.last)
    if span_start > data.first:
        raise PublicDataRefusal(f"the label span starts at {span_start}, after the first evaluated month")
    w1 = base.rule_weights("R1", in_set.loc[months], sigma.loc[months])
    r2 = r2_on_months(class_values, labels, span_start, data.last, months)
    w2 = r2_weights(w1, in_set, r2["multipliers"], classes)
    trailing = trailing_return(returns, all_months)
    w3 = r3_weights(w1, in_set, trailing)
    publication_trait = base.years_since_publication(all_months, {name: data.publication_years.get(name)
                                                                  for name in returns.columns})
    lookback = all_months[all_months < data.first]
    covered_lookback = (in_set.loc[lookback] & publication_trait.loc[lookback].notna()
                        & trailing.loc[lookback].notna())
    if covered_lookback.to_numpy().any():
        raise PublicDataRefusal("an R4 covered pair falls before the first evaluated month; step 3 forms R4 pairs "
                                "on evaluated months only")
    design = r4_design(months, in_set, publication_trait, trailing, sigma, data, labels)
    forecast, fits = r4_forecasts(design, sorted(set(months.year)))
    w4 = r4_weights(w1, forecast)
    return {"returns": returns, "missing": missing, "months": months, "all_months": all_months, "member": member,
            "in_set": in_set, "sigma": sigma, "class_values": class_values, "class_reasons": class_reasons,
            "labels": labels, "span_start": span_start, "r2": r2, "trailing": trailing,
            "publication_trait": publication_trait, "design": design, "forecast": forecast, "fits": fits,
            "weights": {"R1": w1, "R2": w2, "R3": w3, "R4": w4}}


def class_missing_counts(reasons: pd.DataFrame, periods: dict[str, tuple[pd.Period, pd.Period]]) -> dict:
    result = {}
    for period, (start, end) in periods.items():
        block = reasons.loc[start:end]
        result[period] = {name: {reason: int((block[name] == reason).sum())
                                 for reason in ("no_member", "member_return_missing")} for name in block.columns}
    return result


def label_counts(labels: pd.DataFrame, span_start: pd.Period, data: Step3Data) -> dict[str, Any]:
    before = labels.loc[: span_start - 1]
    inside = labels.loc[span_start: data.last]
    return {
        "span_start": str(span_start), "span_end": str(data.last), "span_months": int(len(inside)),
        "span_lookback_months": int(len(inside.loc[: data.first - 1])),
        "months_before_span_with_defined_label": {state: int(before[state].notna().sum()) for state in STATES},
        "months_before_span_with_missing_label": {state: int(before[state].isna().sum()) for state in STATES},
        "cell_months_inside_span": {state: {cell: int((inside[state] == value).sum())
                                            for cell, value in zip(CELLS[state], (1.0, 0.0))} for state in STATES},
    }


def r4_coverage(built: dict[str, Any], data: Step3Data, bounds: dict[str, tuple[pd.Period, pd.Period]]) -> dict:
    months = built["months"]
    in_set = built["in_set"].loc[months]
    w1, forecast = built["weights"]["R1"], built["forecast"].loc[months]
    no_year = pd.Series({name: data.publication_years.get(name) is None for name in in_set.columns})
    published = built["publication_trait"].loc[months].notna()
    trailing = built["trailing"].loc[months].notna()
    count = forecast.notna().sum(axis=1)
    block = forecast.notna() & (count >= R4_MIN_COVERED).to_numpy()[:, None]
    reasons = {
        "no_publication_year": in_set & no_year.to_numpy()[None, :],
        "not_yet_published": in_set & ~no_year.to_numpy()[None, :] & ~published,
        "missing_trailing_return": in_set & published & ~trailing,
        "no_fit_yet": built["design"].covered & forecast.isna(),
    }
    result = {}
    for period, (start, end) in bounds.items():
        inside = slice(start, end)
        members = int(in_set.loc[inside].to_numpy().sum())
        forecasted = int(forecast.loc[inside].notna().to_numpy().sum())
        result[period] = {
            "set_factor_months": members,
            "covered_rows": int(built["design"].covered.loc[inside].to_numpy().sum()),
            "forecast_factor_months": forecasted,
            "forecast_share_of_set": forecasted / members if members else None,
            "tilted_factor_months": int(block.loc[inside].to_numpy().sum()),
            "forecast_share_of_r1_weight": float(w1.where(forecast.notna(), 0.0).loc[inside].sum(axis=1).mean()),
            "months_with_fewer_than_2_forecasts": int((count.loc[inside] < R4_MIN_COVERED).sum()),
            "uncovered_by_reason": {reason: int(frame.loc[inside].to_numpy().sum()) for reason, frame in reasons.items()},
        }
    return result


def post_publication_r2(built: dict[str, Any], step2: dict[str, Any], data: Step3Data, trial: dict[str, Any],
                        costs: list[int]) -> dict[str, Any]:
    """R1 and R2 re-estimated on post-publication factor-months only, from the amendment 1 start month."""

    post = base.post_publication(step2, data.publication_years, trial, costs)
    result: dict[str, Any] = {"step2_split": {key: value for key, value in post.items() if key != "rules"},
                              "status": post["status"], "start_month": post.get("start_month")}
    if post["status"] != "completed":
        return result
    start, last = pd.Period(post["start_month"], freq="M"), data.last
    all_months = built["all_months"]
    subset = built["in_set"] & built["publication_trait"].reindex(index=all_months).notna()
    values, reasons = class_returns(built["returns"], subset, built["sigma"], data.classes, data.class_order)
    span_start = label_span_start(built["labels"], values, last)
    months = pd.period_range(start, last, freq="M")
    w1 = base.rule_weights("R1", subset.loc[months], built["sigma"].loc[months])
    r2 = r2_on_months(values, built["labels"], span_start, last, months)
    w2 = r2_weights(w1, subset, r2["multipliers"], data.classes)
    bounds = {period: (max(first, start), end) for period, (first, end) in base.period_bounds(trial, last).items()
              if max(first, start) <= end}
    rules = {}
    books = {}
    for rule, weights in (("R1", w1), ("R2", w2)):
        rules[rule], books[rule] = rule_books(weights, built["returns"], costs, bounds)
    for cost in costs:
        for period in bounds:
            if rules["R1"][f"{cost}bp"][period] != post["rules"]["R1"][f"{cost}bp"][period]:
                raise PublicDataRefusal("post-publication R1 differs from the step 2 split")
    difference = books["R2"][costs[0]]["net"] - books["R1"][costs[0]]["net"]
    result.update(
        rules={"R0": post["rules"]["R0"], **rules}, span_start=str(span_start),
        mean_difference_20bp=float(difference.mean()),
        mean_lambda=mean_by_period(r2["lambdas"], bounds),
        weights_differ_share=differs_share(w2, w1, bounds),
        class_missing=class_missing_counts(reasons.loc[months], bounds),
        _class_values=values, _r2=r2, _weights={"R1": w1, "R2": w2}, _books=books,
    )
    return result


def null_draw(offset: int, context: dict[str, Any]) -> tuple[float, np.ndarray]:
    """S3.R2 and state-effect HAC t-statistics with the three label series shifted by ``offset``.

    R2 is rebuilt from the shifted labels (current cell, histories, E, and
    weights) with R1 and the class returns fixed. NaN marks an undefined draw.
    """

    shifted = shift_labels(context["span_labels"], offset)
    multipliers = r2_tilt(context["span_values"], shifted, context["positions"])["multipliers"]
    tilted = tilt_array(context["w1"], multipliers[:, context["class_index"]], context["in_set"])
    book = base.portfolio(pd.DataFrame(tilted, index=context["months"], columns=context["columns"]),
                          context["returns"], context["cost"])
    statistic = return_test_statistics(book["net"] - context["r1_net"], periods_per_year=base.MONTHS_PER_YEAR)
    r2_t = np.nan if statistic["hac_statistic"] is None else float(statistic["hac_statistic"])
    shifted_eval = shifted[context["positions"]]
    effect_t = [state_effect_statistic(context["y"][:, k], shifted_eval[:, s])["t"] for k, s in context["tests"]]
    return r2_t, np.array([np.nan if t is None else t for t in effect_t], dtype=float)


def evaluate(data: Step3Data, trial: dict[str, Any], costs: list[int], draws: int = NULL_DRAWS) -> dict[str, Any]:
    built = build_rules(data, trial)
    returns, months, labels = built["returns"], built["months"], built["labels"]
    bounds = base.period_bounds(trial, data.last)
    market = data.market_monthly["Mkt-RF"]
    step2 = base.run_universe(MonthlyPanel(returns, built["missing"], 0), data.first, data.last, trial, market, costs)
    if step2["status"] != "completed":
        raise PublicDataRefusal(f"R0 and R1 refused: {step2['reason']}")
    empty = built["class_reasons"].loc[months] == "no_member"
    if empty.to_numpy().any():
        raise PublicDataRefusal(f"{int(empty.to_numpy().sum())} evaluated class-months have no member "
                                f"(first {empty.any(axis=1).idxmax()})")
    weights = built["weights"]
    if not step2["_member"].in_set.equals(built["in_set"].loc[months]):
        raise PublicDataRefusal("step 3 set differs from the step 2 set")

    grid = {rule: step2["rules"][rule] for rule in ("R0", "R1")}
    books = {}
    for rule in TILTED_RULES:
        grid[rule], books[rule] = rule_books(weights[rule], returns, costs, bounds)
    r1_net = step2["_series"][("R1", costs[0])]

    rule_tests = {f"S3.{rule}": rule_test(books[rule][costs[0]]["net"] - r1_net) for rule in TILTED_RULES}

    # State-effect tests on the observed labels.
    y_all = built["class_values"].loc[months]
    d_all = labels.loc[months]
    post = post_publication_r2(built, step2, data, trial, costs)
    effects = {}
    for name in data.class_order:
        for state in STATES:
            y, d = y_all[name].to_numpy(), d_all[state].to_numpy()
            full = state_effect_statistic(y, d)
            halves = {}
            for half in HALVES:
                start, end = bounds[half]
                yh, dh = y_all.loc[start:end, name], d_all.loc[start:end, state]
                cells = {cell: {"months": int((dh == value).sum()),
                                "episodes": episode_count(dh, value),
                                "mean_gross_return": float(yh[dh == value].mean()) if (dh == value).any() else None}
                         for cell, value in zip(CELLS[state], (1.0, 0.0))}
                first_cell, second_cell = (cells[c]["mean_gross_return"] for c in CELLS[state])
                halves[half] = {"cells": cells, "b": (None if first_cell is None or second_cell is None
                                                      else first_cell - second_cell)}
            b_post = None
            if post.get("status") == "completed":
                sub = post["_class_values"].loc[pd.Period(post["start_month"], freq="M"): data.last, name]
                sub_d = labels.loc[sub.index, state]
                defined = sub.notna()
                high, low = sub[defined & (sub_d == 1.0)], sub[defined & (sub_d == 0.0)]
                b_post = float(high.mean() - low.mean()) if len(high) and len(low) else None
            effects[f"S3.effect.{slug(name)}.{state}"] = {
                "class": name, "state": state, "full": full, "halves": halves, "b_post_publication": b_post,
                "pre_seen": (name, state) in PRE_SEEN,
            }

    # Random-date null: one offset set shared by S3.R2 and the 39 state-effect tests.
    r2 = built["r2"]
    n_span = r2["span_labels"].shape[0]
    offsets = null_offsets(n_span, draws)
    test_ids = list(effects)
    context = {
        "span_values": r2["span_values"], "span_labels": r2["span_labels"], "positions": r2["positions"],
        "w1": weights["R1"].to_numpy(), "in_set": built["in_set"].loc[months].to_numpy(),
        "class_index": np.array([data.class_order.index(data.classes[c]) for c in returns.columns]),
        "months": months, "columns": returns.columns, "returns": returns, "cost": costs[0], "r1_net": r1_net,
        "y": y_all.to_numpy(),
        "tests": [(data.class_order.index(effects[t]["class"]), STATES.index(effects[t]["state"])) for t in test_ids],
    }
    r2_draws = np.full(len(offsets), np.nan)
    effect_draws = np.full((len(offsets), len(test_ids)), np.nan)
    for i, offset in enumerate(offsets):
        r2_draws[i], effect_draws[i] = null_draw(int(offset), context)
    effect_draws = {test_id: effect_draws[:, j] for j, test_id in enumerate(test_ids)}

    rule_tests["S3.R2"]["random_date"] = random_date_pvalue(rule_tests["S3.R2"]["hac_statistic"], r2_draws)
    for test_id, effect in effects.items():
        effect["random_date"] = random_date_pvalue(effect["full"]["t"], effect_draws[test_id])

    # S3 family: 3 rule tests and 39 state-effect tests, 1005 prior slots at p = 1.
    family = {test_id: stat["hac_pvalue"] for test_id, stat in rule_tests.items()}
    family.update({test_id: effect["full"]["p"] for test_id, effect in effects.items()})
    pvalues = pd.Series({test_id: 1.0 if p is None else p for test_id, p in family.items()}, dtype=float)
    qvalues = s3_adjust(pvalues)
    for test_id, stat in rule_tests.items():
        stat["family_p"], stat["by_qvalue"] = float(pvalues[test_id]), float(qvalues[test_id])
    states = eligibility(labels.loc[months], bounds)
    for test_id, effect in effects.items():
        effect["family_p"], effect["by_qvalue"] = float(pvalues[test_id]), float(qvalues[test_id])
        effect["eligible_state"] = states[effect["state"]]["eligible"]
        effect["description_only"] = not effect["eligible_state"]
        effect["survives"] = cell_survives(effect["by_qvalue"], effect["random_date"]["p"], effect["eligible_state"],
                                           effect["full"]["b"],
                                           [effect["halves"][h]["b"] for h in HALVES] + [effect["b_post_publication"]])

    conditions = {rule: closure_conditions(grid, rule, costs) for rule in ("R0", *TILTED_RULES)}
    decision = closure_decision(conditions["R2"])
    claim = r2_timing_claim(conditions["R2"], rule_tests["S3.R2"]["mean_return"], rule_tests["S3.R2"]["by_qvalue"],
                            rule_tests["S3.R2"]["random_date"]["p"], post, states, costs)
    owner_items = [rule for rule in ("R3", "R4") if closure_decision(conditions[rule]) == "open"
                   and rule_tests[f"S3.{rule}"]["by_qvalue"] <= SURVIVAL_LEVEL]

    trailing_eval = built["trailing"].loc[months]
    r3_missing = {period: int((built["in_set"].loc[start:end] & trailing_eval.loc[start:end].isna()).to_numpy().sum())
                  for period, (start, end) in bounds.items()}
    lookback_periods = {"lookback_in_span": (built["span_start"], data.first - 1), **bounds}
    fits = {year: {key: value for key, value in fit.items() if key != "model"} for year, fit in built["fits"].items()}
    post_out = {key: value for key, value in post.items() if not key.startswith("_")}
    return {
        "universe": UNIVERSE, "first_evaluated_month": str(data.first), "last_evaluated_month": str(data.last),
        "closure": {"decision": decision, "conditions": conditions["R2"],
                    "carried_to_step4": ["R1"] if decision == "closed" else ["R1", "R2"],
                    "r2_label": None if decision == "closed" or claim["qualifies"] else "no evidence of state timing"},
        "r2_timing_claim": claim,
        "rule_conditions": conditions, "owner_items": owner_items,
        "rules": grid, "rule_tests": rule_tests, "state_effects": effects, "states": states,
        "r2": {"mean_lambda": mean_by_period(r2["lambdas"], bounds),
               "weights_differ_share": differs_share(weights["R2"], weights["R1"], bounds)},
        "r3": {"members_without_trailing_return": r3_missing,
               "weights_differ_share": differs_share(weights["R3"], weights["R1"], bounds)},
        "r4": {"coverage": r4_coverage(built, data, bounds), "fits": fits,
               "weights_differ_share": differs_share(weights["R4"], weights["R1"], bounds)},
        "post_publication": post_out,
        "labels": label_counts(labels, built["span_start"], data),
        "class_missing": class_missing_counts(built["class_reasons"], lookback_periods),
        "null": {"draws": int(len(offsets)), "seed": NULL_SEED, "span_months": int(n_span),
                 "offset_min": int(offsets.min()), "offset_max": int(offsets.max())},
        "step2_counts": step2["counts"], "lookback_typed_missing": step2["lookback_typed_missing"],
        "market_excess": step2["market_excess"],
        "family": {"observed_tests": OBSERVED_TESTS, "prior_slots": FAMILY_SIZE - OBSERVED_TESTS,
                   "family_size": FAMILY_SIZE, "method": "by"},
        "_built": built, "_books": books, "_step2": step2, "_post": post, "_null_context": context,
    }


# Data loading ------------------------------------------------------------------

def load_step3_sources(trial: dict[str, Any], cache_dir: Path) -> dict[str, Any]:
    sources = {source["id"]: source for source in trial["data_sources"]}
    daily_source = sources["french_ff3_daily"]
    cached = fetch(daily_source["url"], base._cache_path(cache_dir, daily_source))
    daily, reasons, rows = read_french_daily_zip(cached.path, daily_source["zip_member"], column="Mkt-RF")
    entries = [manifest_entry(daily_source["id"], cached, rows=rows, first=str(daily.index[0].date()),
                              last=str(daily.index[-1].date()))]
    aux_source = sources["jkp_accounting_characteristics_list"]
    cached = fetch(aux_source["url"], base._cache_path(cache_dir, aux_source))
    if cached.sha256 != aux_source["sha256"]:
        raise PublicDataRefusal("jkp_accounting_characteristics_list: SHA-256 differs from the pinned value")
    accounting = read_accounting_characteristics(cached.path)
    if len(accounting) != ACC_CHARS_COUNT:
        raise PublicDataRefusal(f"acc_chars holds {len(accounting)} names, expected {ACC_CHARS_COUNT}")
    entries.append(manifest_entry(aux_source["id"], cached, rows=len(accounting), first=None, last=None))
    return {"daily": daily, "daily_missing_codes": int((reasons == MISSING_CODE).sum()),
            "accounting": accounting, "entries": entries}


def update_manifest(repo_root: Path, step2_entries: list[dict[str, Any]], new_entries: list[dict[str, Any]],
                    git: dict[str, Any]) -> dict[str, Any]:
    """Add the two step 3 sources to the committed manifest; a step 2 entry that disagrees refuses."""

    path = repo_root / base.MANIFEST_JSON
    manifest = json.loads(path.read_text(encoding="utf-8"))
    recorded = {entry["id"]: entry for entry in manifest["sources"]}
    for entry in step2_entries:
        if entry["id"] in recorded and recorded[entry["id"]]["sha256"] != entry["sha256"]:
            raise PublicDataRefusal(f"cached {entry['id']} differs from the manifest SHA-256")
    for entry in new_entries:
        recorded[entry["id"]] = entry
    notes = {key: value for key, value in manifest.items() if key not in ("schema_version", "sources")}
    notes["step3"] = {
        "code_commit": git["commit"], "amendment_3": AMENDMENT_3_PATH, "amendment_3_sha256": AMENDMENT_3_SHA256,
        "retrieved_in_step3": [entry["id"] for entry in new_entries],
        "rows_note": "rows for jkp_accounting_characteristics_list counts the names in acc_chars_list(); rows "
                     "for french_ff3_daily counts YYYYMMDD data rows",
    }
    write_manifest(path, list(recorded.values()), notes=notes)
    return notes["step3"]


def assemble_data(inputs: dict[str, Any], fred: MonthlyPanel, step3: dict[str, Any],
                  trial: dict[str, Any]) -> Step3Data:
    panel = inputs["panels"]["jkp_usa_all_factors_monthly_vw_cap"]
    factors = list(panel.values.columns)
    classes = pd.Series({name: inputs["labels"][name] for name in factors})
    high = int(classes.isin(HIGH_TURNOVER_CLASSES).sum())
    if high != HIGH_TURNOVER_COUNT:
        raise PublicDataRefusal(f"{high} factors in high-turnover themes, expected {HIGH_TURNOVER_COUNT}")
    return Step3Data(
        returns=panel.values, missing=panel.missing, classes=classes,
        data_source=data_source_map(factors, step3["accounting"], trial),
        publication_years={name: inputs["years"].get(name) for name in factors},
        market_monthly=inputs["panels"]["french_ff3_monthly"].values[["Mkt-RF", "RF"]],
        market_daily=step3["daily"], credit=fred.values,
        first=pd.Period(trial["evaluation_window"]["first_evaluated_month"], freq="M"),
        last=panel.values.index[-1],
    )


def run(repo_root: Path, git: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run step 3. ``git`` is the tree state taken before the attempt log was appended."""

    contents = verify_trial_files(repo_root)
    trial = json.loads(contents[base.TRIAL_PATH])
    git = git if git is not None else base.git_state(repo_root)
    costs = [trial["costs"]["switch_cost_bps"]["primary"], trial["costs"]["switch_cost_bps"]["sensitivity"]]
    cache_dir = repo_root / base.CACHE_DIR
    inputs = base.load_inputs(trial, cache_dir)
    fred_source = next(source for source in trial["data_sources"] if source["id"] == "fred_baa_aaa_monthly")
    fred = read_fred_csv(fetch(fred_source["url"], base._cache_path(cache_dir, fred_source)).path,
                         series=list(fred_source["series"]))
    step3 = load_step3_sources(trial, cache_dir)
    manifest_note = update_manifest(repo_root, inputs["manifest"], step3["entries"], git)
    data = assemble_data(inputs, fred, step3, trial)
    result = evaluate(data, trial, costs)
    for key in [key for key in result if key.startswith("_")]:
        result.pop(key)
    return {
        "schema_version": "m5_step3_v1", "evidence_ceiling": trial["evidence_ceiling"],
        "run_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trial_files": TRIAL_PINS, "git": git, "timing": base.TIMING, "switch_cost_bps": costs,
        "manifest": inputs["manifest"] + step3["entries"], "manifest_step3": manifest_note,
        "missing_codes": {"french_ff3_daily_mkt_rf": step3["daily_missing_codes"],
                          "fred_baa_aaa": base.typed_missing_counts(fred.missing),
                          "french_ff3_monthly": base.typed_missing_counts(
                              inputs["panels"]["french_ff3_monthly"].missing)},
        **result,
    }


# Report -------------------------------------------------------------------------

_pct, _num, _bp, _pvalue = base._pct, base._num, base._bp, base._pvalue
PERIOD_LABEL = {**base.PERIOD_LABEL, "lookback_in_span": "span lookback"}


def _yes(value: bool) -> str:
    return "yes" if value else "no"


def _interval(values: list[float] | None, scale: float) -> str:
    return "n/a" if values is None else f"[{100 * scale * values[0]:.3f}%, {100 * scale * values[1]:.3f}%]"


def render_report(result: dict[str, Any]) -> str:
    costs = result["switch_cost_bps"]
    closure, claim = result["closure"], result["r2_timing_claim"]
    tests = result["rule_tests"]
    lines = [
        "# Milestone 5 Step 3: State Tilt, Factor Momentum Tilt, and Pooled Ridge Against R1",
        "",
        f"**Evidence ceiling: {result['evidence_ceiling']}.** Public long-short factor series on "
        f"{result['universe']}, gross of each factor's internal trading and borrow costs, small caps included. "
        "Nothing here supports a profitability, ranking, or promotion claim. Every S3 test re-examines comparisons "
        "already seen in the prior exposures and supports no confirmatory claim.",
        "",
        f"Run {result['run_utc']} from code commit `{result['git']['commit']}` (tracked changes at run time: "
        f"{result['git']['tracked_changes']}); runtime {result.get('runtime_seconds', 'n/a')} seconds.",
        "",
        "## Conclusion",
        "",
    ]
    if closure["decision"] == "closed":
        lines.append("**The return-timing line is closed.** R2 (state tilt) loses to R1 in at least one half on at "
                     "least one of the 8 declared conditions. R1 stays the baseline product and is the only rule "
                     "carried to step 4. R2, R3, R4, and the null results are reported as a negative result for "
                     "return timing; every trial stays visible.")
    else:
        label = f", labeled '{closure['r2_label']}'" if closure["r2_label"] else ""
        lines.append(f"**The return-timing line stays open.** R2 meets all 8 closure conditions and goes to step 4 "
                     f"beside R1{label}.")
    lines += ["", f"R2 timing claim: **{'qualifies' if claim['qualifies'] else 'does not qualify'}**"
              + ("" if claim["qualifies"] else f" (failed conditions: {', '.join(claim['failed'])})") + ".", "",
              "| Condition | Text | Holds |", "| --- | --- | --- |"]
    lines += [f"| {c['condition']} | {c['text']} | {_yes(c['holds'])} |" for c in claim["conditions"]]
    survivors = [test_id for test_id, effect in result["state_effects"].items() if effect["survives"]]
    lines += ["", f"Surviving descriptive state-effect cells: {', '.join(survivors) if survivors else 'none'}. "
              "Even a qualifying timing claim would credit no single state. "
              f"R3 or R4 owner items (all 8 conditions and q <= 0.05): {', '.join(result['owner_items']) or 'none'}."]

    lines += ["", "## Closure Conditions (R2 against R1, jkp_factors_153)", "",
              "Differences below 1e-12 in magnitude count as equal, and equal is not a loss. Margin: rule minus R1 "
              "Sharpe, and R1 minus rule drawdown magnitude.", ""]
    lines += _condition_table(result["rule_conditions"])
    lines += ["", "Share of evaluated months in which any R2 weight differs from R1 by more than 1e-12: "
              + ", ".join(f"{PERIOD_LABEL[p]} {v:.3f}" for p, v in result["r2"]["weights_differ_share"].items())
              + ". The same share for R3: "
              + ", ".join(f"{PERIOD_LABEL[p]} {v:.3f}" for p, v in result["r3"]["weights_differ_share"].items())
              + "; for R4: "
              + ", ".join(f"{PERIOD_LABEL[p]} {v:.3f}" for p, v in result["r4"]["weights_differ_share"].items())
              + "."]

    lines += ["", "## Rule Metrics (step 2 metrics, R0 to R4)", "",
              "| Rule | Cost | Period | Months | Ann. mean | Volatility | Sharpe | Max drawdown | Worst 12 months | "
              "Avg turnover |", "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    lines += _grid_rows(result["rules"], costs, RULES)
    market = result["market_excess"]
    if "status" not in market:
        lines += ["", "Market excess return (French Mkt-RF, context only, no switch cost): "
                  + "; ".join(f"{PERIOD_LABEL[p]} ann. mean {_pct(m['annualized_mean'])}, Sharpe {_num(m['sharpe'])}"
                              for p, m in market.items()) + "."]

    lines += ["", "## S3 Rule Tests (rule net minus R1 net at 20 bp, full window)", "",
              f"BY family: {result['family']['observed_tests']} observed p-values plus "
              f"{result['family']['prior_slots']} prior-exposure slots at p = 1 (family size "
              f"{result['family']['family_size']}). The 95% interval is pointwise, mean +/- 1.959964 x sqrt(LRV / n), "
              "not adjusted for selection or multiplicity.", "",
              "| Test | Status | Months | Mean (bp/month) | 95% interval (%/month) | 95% interval (%/year) | HAC t | "
              "HAC p | BY q | Random-date p |",
              "| --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |"]
    for test_id, stat in tests.items():
        random_p = stat.get("random_date", {}).get("p") if "random_date" in stat else None
        random_text = _pvalue(random_p) if test_id == "S3.R2" else "not run"
        lines.append(f"| {test_id} | {stat['status']} | {stat['n_observations']} | {_bp(stat['mean_return'])} | "
                     f"{_interval(stat['ci95_monthly'], 1)} | {_interval(stat['ci95_monthly'], 12)} | "
                     f"{_num(stat['hac_statistic'], 2)} | {_pvalue(stat['hac_pvalue'])} | {_pvalue(stat['by_qvalue'])} | "
                     f"{random_text} |")
    r2_null = tests["S3.R2"]["random_date"]
    lines += ["", f"Random-date null: {result['null']['draws']} circular shifts of the three label series inside the "
              f"label span ({result['null']['span_months']} months), seed {result['null']['seed']}, offsets "
              f"{result['null']['offset_min']} to {result['null']['offset_max']}. S3.R2: "
              f"{r2_null['exceedances']} exceedances, {r2_null['undefined_draws']} undefined draws (counted as "
              "exceedances). R3 and R4 have no random-date null."]

    lines += ["", "## State Episodes and Eligibility", "",
              "Episodes are maximal runs of consecutive evaluated months in one cell, counted per half; a run crossing "
              "1999-12 to 2000-01 counts once in each half. A state is eligible when each cell has at least 10 "
              "episodes in each half.", "",
              "| State | Cell | Episodes 1972-1999 | Episodes 2000-end | Eligible |", "| --- | --- | ---: | ---: | --- |"]
    for state, info in result["states"].items():
        for cell in CELLS[state]:
            lines.append(f"| {state} | {cell} | {info['episodes']['first_half'][cell]} | "
                         f"{info['episodes']['second_half'][cell]} | {_yes(info['eligible'])} |")
    lines += ["", "R2 mean lambda = E / (E + 10) per state: "
              + "; ".join(f"{PERIOD_LABEL[p]} " + ", ".join(f"{s} {v:.3f}" for s, v in values.items())
                          for p, values in result["r2"]["mean_lambda"].items()) + "."]

    lines += ["", "## State-Effect Tests (39, gross class returns)", "",
              "b is the mean gross class return in the first cell (up, high, wide) minus the second, in percent per "
              "month. `*` marks a pre-seen cell. Months/episodes are per cell (first cell / second cell). A test on a "
              "state that is not eligible is description only; its p-value still counts in the family.", "",
              "| Test | Pre-seen | b full | HAC t | HAC p | BY q | Random-date p (undef.) | b 1972-1999 | b 2000-end | "
              "b post-pub | Months 1972-1999 | Episodes 1972-1999 | Months 2000-end | Episodes 2000-end | "
              "Description only | Survives |",
              "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |"]
    for test_id, e in result["state_effects"].items():
        cells = {h: e["halves"][h]["cells"] for h in HALVES}
        first, second = CELLS[e["state"]]
        lines.append(
            f"| {test_id} | {'*' if e['pre_seen'] else ''} | {_pct4(e['full']['b'])} | {_num(e['full']['t'], 2)} | "
            f"{_pvalue(e['full']['p'])} | {_pvalue(e['by_qvalue'])} | {_pvalue(e['random_date']['p'])} "
            f"({e['random_date']['undefined_draws']}) | {_pct4(e['halves']['first_half']['b'])} | "
            f"{_pct4(e['halves']['second_half']['b'])} | {_pct4(e['b_post_publication'])} | "
            + " | ".join(f"{cells[h][first]['months']}/{cells[h][second]['months']} | "
                         f"{cells[h][first]['episodes']}/{cells[h][second]['episodes']}" for h in HALVES)
            + f" | {_yes(e['description_only'])} | {_yes(e['survives'])} |")
    lines += ["", "Per-half cell mean gross returns are in `reports/m5_step3.json` under `state_effects`."]

    coverage = result["r4"]["coverage"]
    lines += ["", "## R3 and R4 Coverage", "",
              "R3 members without a trailing 12-month return (keep their R1 weight): "
              + ", ".join(f"{PERIOD_LABEL[p]} {v}" for p, v in result["r3"]["members_without_trailing_return"].items())
              + ".", "",
              "| Period | Set factor-months | Covered rows | Forecast factor-months | Share of set | Forecast share of R1 "
              "weight | Months with < 2 forecasts | No publication year | Not yet published | Missing trailing return | "
              "No fit yet |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for period, c in coverage.items():
        u = c["uncovered_by_reason"]
        lines.append(f"| {PERIOD_LABEL[period]} | {c['set_factor_months']} | {c['covered_rows']} | "
                     f"{c['forecast_factor_months']} | {_num(c['forecast_share_of_set'])} | "
                     f"{_num(c['forecast_share_of_r1_weight'])} | {c['months_with_fewer_than_2_forecasts']} | "
                     f"{u['no_publication_year']} | {u['not_yet_published']} | {u['missing_trailing_return']} | "
                     f"{u['no_fit_yet']} |")
    lines += ["", "Reasons are assigned in the order listed (no publication year, not yet published, missing trailing "
              "return, no fit yet), so each uncovered factor-month has one reason.", "",
              "| Fit year | Status | Training rows | Training months | Forecast rows | Intercept |",
              "| ---: | --- | ---: | ---: | ---: | ---: |"]
    for year, fit in result["r4"]["fits"].items():
        lines.append(f"| {year} | {fit['status']} | {fit['training_rows']} | {fit['training_months']} | "
                     f"{fit['forecast_rows']} | {_num(fit.get('intercept'), 6)} |")
    lines += ["", "The 83 coefficients of every fit are in `reports/m5_step3.json` under `r4.fits`."]

    post = result["post_publication"]
    lines += ["", "## Post-Publication Comparison (condition 5; no test)", "",
              "R2 re-estimated on post-publication factor-months only, with history from the subset label span "
              f"start. Status `{post['status']}`; start month {post.get('start_month') or 'none'}; subset label span "
              f"start {post.get('span_start', 'n/a')}. R3 and R4 are not formed on the subset."]
    if post["status"] == "completed":
        lines += ["", "| Rule | Cost | Period | Months | Ann. mean | Volatility | Sharpe | Max drawdown | "
                  "Worst 12 months | Avg turnover |", "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        lines += _grid_rows(post["rules"], costs, ("R0", "R1", "R2"))
        lines += ["", f"Mean R2-sub net minus R1-sub net at 20 bp over the full subset period: "
                  f"{_bp(post['mean_difference_20bp'])} bp per month. {claim['post_publication_detail']}.", "",
                  "R2-sub mean lambda per state: "
                  + "; ".join(f"{PERIOD_LABEL[p]} " + ", ".join(f"{s} {v:.3f}" for s, v in values.items())
                              for p, values in post["mean_lambda"].items()) + ".", "",
                  "Share of subset months in which R2-sub weights differ from R1-sub weights by more than 1e-12: "
                  + ", ".join(f"{PERIOD_LABEL[p]} {v:.3f}" for p, v in post["weights_differ_share"].items()) + "."]
        missing = {p: sum(v["no_member"] for v in counts.values()) for p, counts in post["class_missing"].items()}
        lines += ["", "Subset class-months with no subset member (typed missing, left out of R2-sub histories and "
                  "b post-pub): " + ", ".join(f"{PERIOD_LABEL[p]} {v}" for p, v in missing.items()) + "."]
    split = post["step2_split"]
    if "empty_subset_months" in split:
        empty = split["empty_subset_months"]
        lines += ["", f"Evaluated months with an empty subset before the start month: {empty['count']}."]

    labels = result["labels"]
    lines += ["", "## Label Span, Missingness, and Refusals", "",
              f"Label span {labels['span_start']} to {labels['span_end']} ({labels['span_months']} months, of which "
              f"{labels['span_lookback_months']} are lookback months before 1972-01). Label months before the span "
              "start are used by no rule or test; defined labels before it: "
              + ", ".join(f"{s} {v}" for s, v in labels["months_before_span_with_defined_label"].items())
              + "; missing labels before it: "
              + ", ".join(f"{s} {v}" for s, v in labels["months_before_span_with_missing_label"].items())
              + ". No label is missing inside the span (the run would refuse).", "",
              "Cell months inside the span: " + "; ".join(
                  f"{s} " + ", ".join(f"{c} {v}" for c, v in cells.items())
                  for s, cells in labels["cell_months_inside_span"].items()) + "."]
    class_missing = result["class_missing"]
    lines += ["", "Full-set class-months typed missing (left out of R2 histories and tests): "
              + "; ".join(f"{PERIOD_LABEL[p]}: no member {sum(v['no_member'] for v in counts.values())}, member return "
                          f"missing {sum(v['member_return_missing'] for v in counts.values())}"
                          for p, counts in class_missing.items())
              + ". Per-class counts are in the JSON. An evaluated month with an empty class would refuse the run."]
    codes = result["missing_codes"]
    lines += ["", f"Provider missing codes: French daily Mkt-RF {codes['french_ff3_daily_mkt_rf']}; FRED BAA/AAA "
              f"{codes['fred_baa_aaa'] or 'none'}; French monthly FF3 {codes['french_ff3_monthly'] or 'none'}.", "",
              "| Period | Declared | In set | Fewer than 24 in t-37..t-2 | Bad data in t-37..t-2 | Typed missing |",
              "| --- | ---: | ---: | ---: | ---: | --- |"]
    for period, c in result["step2_counts"].items():
        typed = ", ".join(f"{k} {v}" for k, v in c["typed_missing_by_reason"].items()) or "none"
        lines.append(f"| {PERIOD_LABEL[period]} | {c['factor_months_declared']} | {c['factor_months_in_set']} | "
                     f"{c['excluded_fewer_than_24_prior_returns']} | {c['excluded_bad_data_in_lookback']} | {typed} |")
    lines += ["", "Refusals in this run: none (a refusal stops the run and is recorded in "
              "`reports/m5_step3_attempts.jsonl`).", "",
              "Descriptive universes: none. Amendment 3 runs step 3 on jkp_factors_153 only; the step 2 results for "
              "jkp_themes_13 and french_7 stand."]

    lines += ["", "## Provenance, Costs, and Timing", "",
              "Trial files, each verified equal to its committed HEAD version and its pinned SHA-256 before any data "
              "was read: " + "; ".join(f"`{p}` (`{d[:16]}...`)" for p, d in result["trial_files"].items()) + ".", "",
              f"- Timing `{result['timing']['label']}`: signal month {result['timing']['signal_month']}; execution at "
              f"{result['timing']['execution']}; return month {result['timing']['return_month']}. Labels use market "
              "data through month t-2 and the credit spread through month t-3; R2 histories use class returns of "
              "months u <= t-2; each R4 fit for year Y trains on return months through November of Y-1.",
              f"- Costs: switch cost {costs[0]} bp primary and {costs[1]} bp sensitivity on monthly weight turnover "
              "from the step 2 portfolio function; each run starts from no holdings (turnover 1 in its first month). "
              "State-effect tests use gross class returns. Factor internal costs and borrow stay inside the published "
              "returns.", "",
              "| Source | Rows | First | Last | SHA-256 (prefix) | Retrieved (UTC) |",
              "| --- | ---: | --- | --- | --- | --- |"]
    for entry in result["manifest"]:
        lines.append(f"| {entry['id']} | {entry['rows']} | {entry['first_date'] or '-'} | {entry['last_date'] or '-'} | "
                     f"`{entry['sha256'][:16]}` | {entry['retrieved_utc']} |")
    lines += ["", "Full URLs and hashes: `reports/m5_public_data_manifest.json`. Raw files stay in the gitignored "
              "`data/public_cache/`. Attribution: JKP data by Jensen, Kelly, and Pedersen, jkpfactors.com, CC BY-NC "
              "4.0; jkp-data code (cluster_labels.csv, factor_details.xlsx, aux_functions.py) MIT. French factors: "
              "Kenneth R. French Data Library, copyright Eugene F. Fama and Kenneth R. French. Moody's BAA and AAA "
              "yields retrieved from FRED, Federal Reserve Bank of St. Louis.",
              "", "## Limitations", "",
              "- DIAGNOSTIC_ONLY: public long-short factor returns, gross of internal trading and borrow costs, "
              "small caps included. The implementable check on point-in-time books after costs is step 4.",
              "- Every S3 test re-examines comparisons the prior exposures already ran on the same months; the "
              "1005 prior slots cover the retained final scripts only, so the historical search is not proven "
              "complete.",
              "- With 1047 family slots the smallest p-value needs about 6.3e-6 (HAC |t| about 4.5) to reach BY q "
              "0.05, so survival is rare by design.",
              "- HAC standard errors with the step 2 lag may understate uncertainty for persistent states; the "
              "random-date null is the guard, and its circular shift joins the span end to its start once per draw.",
              "- R4 has no forecast for most first-half factor-months, so its first-half comparison has little "
              "power; R4 has no random-date null and supports no state-timing claim.",
              "- R2 lookback histories reach back to the early 1930s and include early Compustat years with known "
              "backfill bias; the JKP clusters used as classes come from full-sample correlations (hindsight).",
              "- The post-publication condition uses the subset's full period, which is weighted toward the second "
              "half; the subset halves are reported, not tested.",
              "- On jkp_factors_153, turnover_class is a function of theme and adds nothing to R4 beyond theme.",
              "- The JKP and French files are revised by their providers; the manifest pins the SHA-256 of the files "
              "used here.",
              ""]
    return "\n".join(lines)


def _pct4(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.3f}%"


def _condition_table(conditions: dict[str, list[dict[str, Any]]]) -> list[str]:
    rows = ["| Rule | Period | Cost | Metric | Rule value | R1 value | Margin | Holds |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | --- |"]
    for rule, items in conditions.items():
        for c in items:
            fmt = _pct if c["metric"] == "max_drawdown" else _num
            margin = "n/a" if c["margin"] is None else (f"{100 * c['margin']:.4f} pp" if c["metric"] == "max_drawdown"
                                                          else f"{c['margin']:.4f}")
            rows.append(f"| {rule} | {PERIOD_LABEL[c['period']]} | {c['cost_bps']} bp | {c['metric']} | "
                        f"{fmt(c['rule'])} | {fmt(c['R1'])} | {margin} | {_yes(c['holds'])} |")
        rows.append(f"| {rule} | all | | | | | | **{sum(c['holds'] for c in items)} of 8 hold** |")
    return rows


def _grid_rows(grid: dict[str, Any], costs: list[int], rules: tuple[str, ...]) -> list[str]:
    rows = []
    for rule in rules:
        for cost in costs:
            for period, m in grid[rule][f"{cost}bp"].items():
                rows.append(f"| {rule} | {cost} bp | {PERIOD_LABEL[period]} | {m['months']} | "
                            f"{_pct(m['annualized_mean'])} | {_pct(m['volatility'])} | {_num(m['sharpe'])} | "
                            f"{_pct(m['max_drawdown'])} | {_pct(m['worst_12_month_return'])} | "
                            f"{_num(m['average_monthly_turnover'])} |")
    return rows


def json_ready(value: Any) -> Any:
    """Plain JSON types: NaN and infinities become null; numpy scalars and periods become Python values."""

    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, pd.Period):
        return str(value)
    return value


def _append_attempt(repo_root: Path, record: dict[str, Any]) -> None:
    path = repo_root / ATTEMPTS_JSONL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    attempt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    try:
        commit = base.git_state(REPO_ROOT)
    except subprocess.CalledProcessError:
        commit = {"commit": None, "tracked_changes": None}
    _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "start", **commit})
    started = time.perf_counter()
    try:
        result = json_ready(run(REPO_ROOT, commit))
        result["runtime_seconds"] = round(time.perf_counter() - started, 1)
        (REPO_ROOT / REPORT_JSON).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        (REPO_ROOT / REPORT_MD).write_text(render_report(result), encoding="utf-8")
    except PublicDataRefusal as refusal:
        _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "end", "status": "refused",
                                    "error": f"PublicDataRefusal: {refusal}"[:500]})
        print(f"refused: {refusal}", file=sys.stderr)
        return 1
    except Exception as error:
        _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "end", "status": "failed",
                                    "error": f"{type(error).__name__}: {error}"[:500]})
        raise
    outputs = {path: sha256_file(REPO_ROOT / path) for path in (REPORT_MD, REPORT_JSON, base.MANIFEST_JSON)}
    _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "end", "status": "completed",
                                "closure": result["closure"]["decision"],
                                "r2_timing_claim": result["r2_timing_claim"]["qualifies"],
                                "runtime_seconds": result["runtime_seconds"], "outputs": outputs})
    print(f"closure: {result['closure']['decision']}; timing claim: {result['r2_timing_claim']['qualifies']}; "
          f"runtime {result['runtime_seconds']} s; report: {REPORT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
