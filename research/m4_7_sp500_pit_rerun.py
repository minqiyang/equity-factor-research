"""M4.7 S&P 500 point-in-time rerun: decision layer (stage a-0) and runner (stage b-1).

Stage a-0 delivers the halves split, sign stability, the minimum detectable
effect of an IC series, and the decision gate (plan sections 6.8 and 6.9).
Stage b-1 binds a frozen registration to a snapshot, recomputes the common
support from the loaded panels, runs both factor families on member-only
engine frames over the valid segments, and writes the report, the JSON
sidecar, and the trials JSONL (plan sections 4, 6, 7.3, Appendix E).

Every Class I reason of plan section 4.5 stops the run before inference with
``stopped_before_inference``; the trial records written so far stay in the
JSONL. Every figure is ``DIAGNOSTIC_ONLY``.

Run as ``python -m research.m4_7_sp500_pit_rerun --snapshot-id <ID>
--registration-sha256 <hash> [--registration <path>] [--output-dir <dir>]``.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Sequence

import numpy as np
import pandas as pd
from scipy.stats import norm

from backtest.long_short import run_long_short_backtest
from backtest.portfolio import BacktestValidationError, capture_backtest_source_provenance, run_long_only_backtest
from data.constituent_table import load_constituent_intervals_csv
from data.holdout_partition import SEAL_FILE, SnapshotRefusal, sha256_bytes
from data.parquet_loader import load_eod_cohort_panels, load_symbol_splits
from features.cross_validation import combinatorial_purged_cross_validation_pbo, cpcv_geometry_unavailable_reason
from features.diagnostics import deflated_sharpe_ratio, mde_from_long_run_variance, newey_west_long_run_variance
from features.multiple_testing import return_test_statistics
from research.m4_7_common_support import (
    GAP_WINDOWS,
    SEGMENTS,
    SupportSchedule,
    _canonical,
    ic_month_set,
    monthly_rank_ic,
    reset_to_reset_labels,
    signal_eligibility,
    snapshot_support,
)
from research.m4_7_coverage_census import _code_commit
from research.m4_7_family_a import FAMILY_A, FAMILY_A_IDS, FAMILY_A_SIZE, family_a_signals
from research.m4_7_terminal_evidence import ENGINE_EVENTS, read_engine_events, require_current_terminal
from research.m4_7_universe_build import (
    INTERVAL_CSV,
    INTERVAL_RESULTS,
    INVENTORY,
    SECURITY_MASTER,
    Snapshot,
    discovery_inputs_sha256,
    discovery_window,
    read_derived_json,
    require_current,
    snapshot_dir_from_args,
    write_bytes,
)
from research.multifactor_diagnostic_mvp import ALPHA_IDS, SECTOR_NEUTRAL_COMPOSITE, calculate_diagnostic_alpha
from research.multiple_testing_diagnostics import summarize_multiple_testing
from research.real_data_multifactor_diagnostic import COMPOSITE_IDS, _build_composites, build_adjusted_research_panels


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


# ---------------------------------------------------------------- registered protocol (plan 6.1, Appendix C)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_PATH = REPOSITORY_ROOT / "docs/preregistrations/m4_7_sp500_pit_rerun_v1.json"
CENSUS_JSON = REPOSITORY_ROOT / "reports/m4_7_coverage_census.json"
SEAL_RECORD = REPOSITORY_ROOT / "docs/preregistrations/m4_7_holdout_seal_v1.json"
REPORT = "reports/m4_7_sp500_pit_rerun.md"
SIDECAR = "reports/experiment_logs/m4_7_sp500_pit_rerun.json"
TRIALS = "reports/experiment_logs/m4_7_sp500_pit_rerun_trials.jsonl"
LABEL_RECORDS = "rerun/label_records.json"
BENCHMARK_ID = "SPY.US#E1"
FAMILY_B_COMPOSITES = tuple(c for c in COMPOSITE_IDS if c != SECTOR_NEUTRAL_COMPOSITE)
FAMILY_B_IDS = tuple(ALPHA_IDS) + FAMILY_B_COMPOSITES
FAMILY_SIZES = {"A": FAMILY_A_SIZE, "B": len(FAMILY_B_IDS)}
UNION_SIZE = FAMILY_SIZES["A"] + FAMILY_SIZES["B"]
FAMILY_B_FIELDS = ("open", "high", "low", "close", "adjusted_close", "vwap", "volume", "dollar_volume", "returns")
CLASS_I_ENGINE = frozenset({"incoming_price_invalid", "execution_price_invalid", "terminal_target_invalid",
                            "terminal_events_invalid"})
COST_CASES = ("primary", "sensitivity_2x", "zero_cost_diagnostic_only")
QUANTILES, TOP_PCT, CPCV_SPLITS, CPCV_EMBARGO = 10, 0.10, 8, 5
O3_CHOICES = ("proceed_as_registered", "north_star_power_definition_changed", "extended_before_rerun")
PROGRAM_DECISION = {
    "evaluation_incomplete": "No kill decision is possible; the owner chooses repair and rerun under a new registration "
                             "version, or accepts the incomplete evaluation as a recorded null result",
    "proceed": "M4.8: fundamentals, style risk on the PIT universe, costs at the owner's scale",
    "survivor_without_confirmation": "The owner reviews implementation and costs in an M4.8 scoping decision",
    "review_thesis": "North Star kill criterion: engine feature work stops; the owner reviews the thesis",
    "extend_first": "Extend breadth or history under a new registration; the holdout stays sealed",
}
ROUNDING_STATEMENT = "rounding refusals at low adjusted levels select on later splits"
VP_STATEMENTS = {
    "VP-1": "volume_carries_the_split_adjustment_of_prices_tested_by_volume_basis_split_diagnostic",
    "VP-2": "declared_distributions_applied_as_non_split_adjustments_by_the_registered_formula_and_no_other",
}
REGISTERED: dict[str, Any] = {
    "schema_version": "m4_7_sp500_pit_rerun_v1",
    "evidence_class": "DIAGNOSTIC_ONLY",
    "universe": {
        "index": "GSPC.INDX",
        "calendar_source": "GSPC.INDX_eod_dates_v1",
        "bar_date_source": "dates_sidecar_v1",
        "membership_availability_basis": "vendor_effective_date_as_known_at_v1",
        "interval_boundary_rule": "calendar_row_semantics_v1",
        "identity_rules": ["E1_gap_20_rows", "E2_containment", "E3_name_conflict", "E4_isin_conflict",
                           "E5_discontinuity_ln2_discovery_rows", "E6_delisted_and_listed_reuse_isin_continuity"],
        "signal_row_eligibility": "resolved_universe_at_next_execution_row_and_cutoff_bar_present_v2",
        "family_b_input_masking": "all_field_panels_masked_before_cross_sectional_operators_v1",
        "engine_frame_columns": "member_permanent_ids_only",
        "corporate_action_tables": "date_first_partitioned_per_partition_validated_v1",
        "split_evidence_scope": "discovery_partition_only_with_discontinuity_fallback",
        "corporate_action_attribution":
            "episode_span_attribution_with_split_basis_in_span_step_and_cumulative_drift_checks_v3",
        "split_basis_check": {"exact_tolerance": 1e-6, "last_bar_support": "exact_declared_split_pattern_only_v2",
                              "non_split_factor_bound": "(0, 1]"},
        "in_span_step_check": {
            "tolerance": 1e-3, "pairs": "consecutive_on_calendar_discovery_bars_of_the_episode",
            "dividend_factor": "one_minus_amount_over_own_basis_reference_price_v3",
            "event_order": "date_then_split_before_distribution", "dividend_factor_formula": "prior_close_v1",
            "cumulative_drift_tolerance": 2e-3, "cumulative_drift": "telescoped_sum_of_log_pair_ratios_to_last_bar_v1",
            "dividend_evidence_unavailable": "every_pair_flat"},
        "vendor_data_premises": {
            **VP_STATEMENTS, "exposure": "in_span_distribution_support_with_b_d_and_s_d_quantiles",
            "revisit_trigger": "s_d_above_0.05_on_more_than_1_percent_of_eligible_member_days",
            "owner_item": "O-8", "o8_disposition": "ratified"},
        "membership_entries":
            "exact_duplicates_collapsed_overlaps_refused_union_under_r_census_9_unparseable_charged_worst_case_v2",
        "membership_open_end_date": "empty_null_absent_or_strictly_after_components_retrieved_utc_date_v2",
    },
    "holdout": {
        "seal_record": "docs/preregistrations/m4_7_holdout_seal_v1.json",
        "buffer_rows": 252,
        "retrieval_order": ["components", "symbols", "seal", "calendar", "splits", "eod", "dividends", "verify"],
    },
    "discovery": {"halves": "contiguous_by_valid_ic_month_count_earlier_half_takes_remainder"},
    "timing": {
        "contract": "after_close_signal_next_observed_close_v1", "rebalance": "ME", "signal_lag_periods": 1,
        "ic_signal_row": "reset_row_minus_one", "ic_execution_row": "reset_row",
        "label_horizon": "next_scheduled_reset_row", "label_contract": "terminal_aware_reset_to_reset_forward_return_v2",
    },
    "common_support": {
        "contract": "common_support_segments_open_terminal_holdings_v3", "terminal_reset_peeling": True,
        "exclusion_cells_from_first_bar": True, "max_gap_windows": 6, "max_excluded_fraction": 0.05,
        "min_segment_rows": 42,
    },
    "terminal": {
        "settlement_contract": "prior_observed_close_to_consideration_at_completion_date_row_v2",
        "consideration_valuation_rule": "acquirer_close_at_completion_date_row_v1",
        "cash_settlement_lag_rows": [-1, 3], "stock_consideration_lag_rows": [-1, 0],
        "cash_availability_idealization_rows_max": 3,
        "known_at_rule": "announcement_date_at_or_before_reference_row",
        "rename_rule": "stock_consideration_into_successor_permanent_id",
        "corporate_action_evidence_rule":
            "target_split_and_dividend_and_acquirer_split_discovery_partitions_required_else_unresolved",
    },
    "families": {
        "A": {"family_size": FAMILY_A_SIZE, "factors": [
            {"id": f.factor_id, "direction": f.direction, "params": dict(f.parameters), "warmup_rows": f.warmup_rows}
            for f in FAMILY_A]},
        "B": {"family_size": FAMILY_SIZES["B"], "alpha_ids": list(ALPHA_IDS), "composite_ids": list(FAMILY_B_COMPOSITES),
              "composite_fitting_labels": "terminal_aware_reset_to_reset_forward_return_v2_keyed_by_signal_row"},
        "union_sensitivity_size": UNION_SIZE,
    },
    "books": {
        "long_short": {"quantiles": QUANTILES, "weighting": "equal", "gross_leverage": 1.0},
        "long_only": {"top_pct": TOP_PCT, "weighting": "equal", "benchmark": BENCHMARK_ID},
    },
    "costs": {
        "primary": {"transaction_cost_bps": 1.0, "slippage_bps": 4.0},
        "sensitivity_2x": {"transaction_cost_bps": 2.0, "slippage_bps": 8.0},
        "zero_cost_diagnostic_only": {"transaction_cost_bps": 0.0, "slippage_bps": 0.0},
    },
    "benchmarks": {
        "primary": "SPY.US#E1_adjusted_close_cost_free",
        "secondary": "equal_weight_pit_universe_engine_constant_signal_zero_cost_same_segments",
    },
    "objective": {
        "target_information_ratio": 0.30, "tracking_error_budget_annualized": 0.08,
        "max_drawdown_budget": {"long_only": 0.60, "long_short": 0.30}, "role_in_m4_7": "descriptive",
    },
    "statistics": {
        "primary_test": "monthly_rank_ic_mean_two_sided_hac_bartlett_automatic_lag",
        "family_control": "benjamini_yekutieli_0.05_within_family",
        "survivor": "by_reject_and_positive_mean_ic",
        "economic_confirmation": "long_short_mean_daily_net_return_positive_at_primary_costs",
        "sign_stability": "positive_mean_ic_in_both_halves_min_24_months_each",
        "min_ic_months": MIN_IC_MONTHS, "min_ic_pairs_per_month": 100,
        "mde": {"power": POWER, "alpha_eff_formula": "0.05 / (6 * H_6)", "variance": "bartlett_long_run_variance",
                "floor": ADEQUATE_MDE, "single_test_reported": True},
        "power_projection": {"prior_band": [0.08, 0.10, 0.12]},
        "cpcv": {"n_splits": CPCV_SPLITS, "embargo_periods": CPCV_EMBARGO},
    },
    "decision_gate": {
        "order": ["evaluation_incomplete", "proceed", "survivor_without_confirmation", "review_thesis", "extend_first"],
        "review_thesis_requires": "no_positive_survivor_and_every_realized_mde_at_or_below_0.02",
        "contrary_rejection_disposition": "non_survivor_confirmed_by_owner_o3",
    },
}
SNAPSHOT_DIGESTS = ("manifest_sha256", "discovery_inputs_sha256", "interval_csv_sha256", "security_master_sha256",
                    "interval_results_sha256", "engine_events_sha256", "segments_sha256", "seal_prospective_sha256",
                    "seal_confirmed_sha256", "census_json_sha256")


class RunnerStop(Exception):
    """A Class I reason of plan section 4.5: the run stops before inference."""

    def __init__(self, reason: str, detail: str = "", trial: str | None = None) -> None:
        self.reason, self.detail, self.trial = reason, detail, trial
        super().__init__(f"{reason}: {detail}" if detail else reason)


def check_registration(doc: dict[str, Any]) -> dict[str, dict[str, float]]:
    """T-REG-1: refuse a registration that departs from the implemented protocol; return its cost cases.

    Fixed sections must equal ``REGISTERED``; run-specific values (snapshot
    digests, the holdout and discovery dates, the O-3 choice, and the owner
    values under O-1 and O-6) are checked for type and range.
    """
    def refuse(field: str) -> None:
        raise RunnerStop("registration_invalid", field)

    families = doc.get("families", {})
    if (families.get("A", {}).get("family_size") != FAMILY_A_SIZE or families.get("B", {}).get("family_size") != 63
            or families.get("union_sensitivity_size") != 69 or FAMILY_SIZES["B"] != 63):
        raise RunnerStop("family_size_mismatch", "registered family sizes must be A 6, B 63, union 69")
    if SECTOR_NEUTRAL_COMPOSITE in families.get("B", {}).get("composite_ids", []):
        refuse("families.B.composite_ids")
    for section in ("schema_version", "evidence_class", "universe", "timing", "terminal", "families", "books",
                    "benchmarks", "decision_gate"):
        if doc.get(section) != REGISTERED[section]:
            refuse(section)
    for section in ("holdout", "discovery", "common_support"):
        if any(doc.get(section, {}).get(key) != value for key, value in REGISTERED[section].items()):
            refuse(section)
    if '"kill_reachable":' in json.dumps(doc):
        refuse("kill_reachable")
    statistics = copy.deepcopy(doc.get("statistics", {}))
    projection = statistics.get("power_projection", {})
    if not isinstance(projection.pop("kill_reachable_projection", None), bool):
        refuse("statistics.power_projection.kill_reachable_projection")
    if projection.pop("owner_decision_o3", None) not in O3_CHOICES:
        refuse("statistics.power_projection.owner_decision_o3")
    holding = statistics.get("cpcv", {}).pop("holding_periods", None)
    if statistics != REGISTERED["statistics"]:
        refuse("statistics")
    discovery = doc["discovery"]
    if not isinstance(holding, int) or holding != discovery.get("max_reset_to_reset_rows"):
        refuse("statistics.cpcv.holding_periods")
    snapshot = doc.get("snapshot", {})
    if snapshot.get("retrieval_complete") is not True:
        refuse("snapshot.retrieval_complete")
    for key in SNAPSHOT_DIGESTS:
        value = snapshot.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            refuse(f"snapshot.{key}")
    costs = doc.get("costs", {})
    if set(costs) != set(COST_CASES) or any(set(case) != {"transaction_cost_bps", "slippage_bps"}
                                            for case in costs.values()):
        refuse("costs")
    values = {name: {k: float(v) for k, v in case.items()} for name, case in costs.items()}
    if (any(not math.isfinite(v) or v < 0.0 for case in values.values() for v in case.values())
            or any(v != 0.0 for v in values["zero_cost_diagnostic_only"].values())
            or any(values["sensitivity_2x"][k] != 2.0 * values["primary"][k] for k in values["primary"])):
        refuse("costs")
    objective = doc.get("objective", {})
    drawdown = objective.get("max_drawdown_budget", {})
    if not (objective.get("target_information_ratio", 0) > 0
            and 0 < objective.get("tracking_error_budget_annualized", 0) <= 0.25
            and set(drawdown) == {"long_only", "long_short"} and all(0 < v < 1 for v in drawdown.values())
            and objective.get("role_in_m4_7") == "descriptive"):
        refuse("objective")
    return values


# ---------------------------------------------------------------- snapshot binding (C64, S7, plan 2.4 and 4.5)


def _stale(artifact: str) -> RunnerStop:
    return RunnerStop("derived_artifact_stale", artifact)


def bind_snapshot(snapshot_dir: Path, registration: dict[str, Any], census_json: Path,
                  seal_record: Path) -> dict[str, Any]:
    """Every check that precedes ``load_eod_cohort_panels``; returns the bound inputs.

    Hash bindings to the registration, the discovery-input and panel-hash
    check, the terminal binding, the peeled schedule files, the holdout seal,
    and the ``panel_split_table_present`` re-check (C64).
    """
    try:
        snapshot = Snapshot.open(snapshot_dir)
    except SnapshotRefusal as exc:
        raise RunnerStop(exc.code, str(exc)) from exc
    root, pinned = snapshot.root, registration["snapshot"]
    if pinned.get("snapshot_id") != snapshot.manifest["snapshot"].get("id"):
        raise RunnerStop("registration_invalid", "snapshot.snapshot_id")
    files = {"manifest_sha256": root / "manifest.json", "interval_csv_sha256": root / INTERVAL_CSV,
             "security_master_sha256": root / SECURITY_MASTER, "interval_results_sha256": root / INTERVAL_RESULTS,
             "engine_events_sha256": root / ENGINE_EVENTS, "seal_prospective_sha256": root / SEAL_FILE,
             "seal_confirmed_sha256": Path(seal_record), "census_json_sha256": Path(census_json)}
    for key, path in files.items():
        if not path.is_file() or sha256_bytes(path.read_bytes()) != pinned[key]:
            raise _stale(key.removesuffix("_sha256"))
    inputs = discovery_inputs_sha256(snapshot)
    if inputs != pinned["discovery_inputs_sha256"]:
        raise _stale("discovery_inputs")
    try:
        validation, _ = require_current_terminal(snapshot)
        inventory = read_derived_json(root, INVENTORY)
        require_current(snapshot, inventory.get("discovery_inputs_sha256"), INVENTORY)
        segments = read_derived_json(root, SEGMENTS)
        windows = read_derived_json(root, GAP_WINDOWS)
    except SnapshotRefusal as exc:
        raise RunnerStop(exc.code, str(exc)) from exc
    for record in inventory["files"]:
        path = root / "panel" / record["file"]
        if not path.is_file() or sha256_bytes(path.read_bytes()) != record["sha256"]:
            raise _stale(f"panel {record['symbol']}")
    body = {k: v for k, v in segments.items() if k not in ("segments_sha256", "discovery_inputs_sha256")}
    if (segments.get("discovery_inputs_sha256") != inputs or windows.get("discovery_inputs_sha256") != inputs
            or segments.get("segments_sha256") != pinned["segments_sha256"]
            or hashlib.sha256(_canonical(body)).hexdigest() != pinned["segments_sha256"]
            or windows.get("gap_windows") != segments["gap_windows"]):
        raise _stale(SEGMENTS)
    max_reset = registration["discovery"]["max_reset_to_reset_rows"]
    if segments["max_reset_to_reset_rows"] != max_reset:
        raise RunnerStop("census_runner_inconsistency:max_reset_span", "census/segments.json")
    discovery = registration["discovery"]
    if (discovery.get("first_reset"), discovery.get("last_reset"), discovery.get("last_ic_month")) != (
            segments["D0"], segments["D_last"], segments["D_end"]):
        raise RunnerStop("registration_invalid", "discovery window")
    seal = json.loads(Path(seal_record).read_bytes())
    holdout = registration["holdout"]
    sealed = (seal.get("holdout_start"), seal.get("holdout_end_exclusive"))
    if sealed != (holdout.get("holdout_start"), holdout.get("holdout_end_exclusive")) or \
            sealed[1] != snapshot.holdout_end.isoformat():
        raise RunnerStop("holdout_overlap_refused", "registration, seal record, and snapshot seal disagree")
    census = json.loads(Path(census_json).read_bytes())
    for record in inventory["files"]:
        if load_symbol_splits(root / "panel", record["symbol"]) is not None:
            raise RunnerStop("panel_split_table_present", record["symbol"])
    return {"snapshot": snapshot, "inputs": inputs, "inventory": inventory, "validation": validation,
            "census": census}


def load_member_panels(bound: dict[str, Any]) -> dict[str, Any]:
    """Load the member panels plus ``SPY.US#E1`` and build the research panels on ``C_disc``."""
    snapshot, root = bound["snapshot"], bound["snapshot"].root
    full = snapshot.calendar()
    i_h, d0, _ = discovery_window(full, snapshot.holdout_end)
    calendar = full[i_h:]
    intervals = load_constituent_intervals_csv(root / INTERVAL_CSV).data
    listed = {record["symbol"] for record in bound["inventory"]["files"]}
    if BENCHMARK_ID not in listed:
        raise RunnerStop("calendar_mismatch", f"{BENCHMARK_ID} has no discovery panel")
    assets = sorted(set(intervals["permanent_id"]) & listed)
    fields = load_eod_cohort_panels(root / "panel", assets + [BENCHMARK_ID], inventory_path=root / INVENTORY)
    if not pd.DatetimeIndex(fields["adjusted_close"].index).equals(calendar):
        raise RunnerStop("calendar_mismatch", "loaded panel index differs from C_disc")
    research = build_adjusted_research_panels(fields)
    spy = research["adjusted_close"][BENCHMARK_ID]
    if not np.isfinite(spy.to_numpy(dtype=float)).all():
        raise RunnerStop("calendar_mismatch", f"{BENCHMARK_ID} incomplete on C_disc")
    return {"calendar": calendar, "d0": d0 - i_h, "intervals": intervals, "assets": assets,
            "research": {k: v[assets] for k, v in research.items() if isinstance(v, pd.DataFrame)}, "spy": spy,
            "events": read_engine_events(root), "master": pd.read_csv(root / SECURITY_MASTER, dtype=str,
                                                                        keep_default_na=False)}


def recompute_support(bound: dict[str, Any], loaded: dict[str, Any], registration: dict[str, Any]):
    """Recompute ``X``, ``W``, and the segments from the loaded panel's missing-value pattern (plan 4.5).

    The digest covers ``max_reset_to_reset_rows``, so one comparison checks both.
    """
    prices = loaded["research"]["adjusted_close"]
    bars = pd.DataFrame(np.isfinite(prices.to_numpy(dtype=float)), index=loaded["calendar"], columns=prices.columns)
    support = snapshot_support(loaded["calendar"], bound["snapshot"].holdout_end.isoformat(),
                               bound["snapshot"].calendar_source, loaded["intervals"], loaded["events"], bars,
                               loaded["master"], bound["inputs"], loaded["d0"])
    if support.segments_sha256 != registration["snapshot"]["segments_sha256"]:
        raise RunnerStop("census_runner_inconsistency:schedule_digest", "recomputed schedule differs from the census")
    return support


# ---------------------------------------------------------------- signals, labels, and IC trials (plan 2.5, 4.6)


def equal_weight_signal(s_mask: pd.DataFrame) -> pd.DataFrame:
    """The equal-weight PIT benchmark signal: 1.0 where eligible with a bar, missing elsewhere (plan 2.5)."""
    return s_mask.astype(float).where(s_mask)


def family_b_alphas(research: dict[str, pd.DataFrame], s_mask: pd.DataFrame) -> dict[str, pd.DataFrame | Exception]:
    """The 52 alphas on field panels masked with ``S_mask``, masked again; a failure is kept as its exception."""
    masked = {field: research[field].where(s_mask) for field in FAMILY_B_FIELDS}
    out: dict[str, pd.DataFrame | Exception] = {}
    for alpha_id in ALPHA_IDS:
        try:
            out[alpha_id] = calculate_diagnostic_alpha(alpha_id, masked).where(s_mask)
        except (ValueError, ArithmeticError, KeyError) as exc:
            out[alpha_id] = exc
    return out


def family_b_composites(
    research: dict[str, pd.DataFrame], s_mask: pd.DataFrame, alphas: dict[str, pd.DataFrame],
    labels: pd.DataFrame, ic_resets: tuple[int, ...], rebalance_dates: pd.DatetimeIndex, horizon: int,
) -> dict[str, pd.DataFrame]:
    """The eleven composites fitted on terminal-aware labels keyed by ``t = r - 1`` (plan 6.3)."""
    masked = {field: research[field].where(s_mask) for field in FAMILY_B_FIELDS}
    history = pd.DataFrame({alpha_id: monthly_rank_ic(alphas[alpha_id], labels, ic_resets)["rank_ic"]
                            for alpha_id in ALPHA_IDS})
    composites, _ = _build_composites(
        composite_ids=FAMILY_B_COMPOSITES, alpha_ids=tuple(ALPHA_IDS), alpha_panels=alphas,
        ordered_alphas=[alphas[a] for a in ALPHA_IDS], ic_history=history, monthly_eval_dates=rebalance_dates,
        panels=masked, prices=research["adjusted_close"], forward_returns=labels,
        config=SimpleNamespace(signal_lag_periods=1, forward_holding_periods=horizon, ridge_alpha=0.1),
    )
    return {composite_id: panel.where(s_mask) for composite_id, panel in composites.items()}


def ic_labels(prices: pd.DataFrame, s_mask: pd.DataFrame, schedule: SupportSchedule, ic_resets: tuple[int, ...],
              events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Terminal-aware labels with the label-bar guard: any guard reason is Class I (plan 4.6)."""
    labels, records = reset_to_reset_labels(prices, s_mask, schedule.reset_rows, ic_resets,
                                            events if len(events) else None)
    if len(records) and int(records[["missing_execution_bar", "missing_horizon_end_bar"]].to_numpy().sum()):
        raise RunnerStop("census_runner_inconsistency:label_bar_missing",
                         f"{int(records['missing_execution_bar'].sum())} execution, "
                         f"{int(records['missing_horizon_end_bar'].sum())} horizon")
    if len(records):
        typed = records["missing_execution_bar"] + records["missing_horizon_end_bar"]
        horizons = [int(schedule.reset_rows[schedule.reset_rows > r][0]) for r in ic_resets]
        records = records.assign(horizon_date=prices.index[horizons],
                                 label_exclusion_fraction=typed / records["eligible_count"].where(
                                     records["eligible_count"] > 0))
    return labels, records


def coverage_loss(signal: pd.DataFrame, s_mask: pd.DataFrame, ic_resets: tuple[int, ...]) -> dict[str, Any]:
    """``coverage_loss_f``: eligible assets per IC month whose factor value at ``r - 1`` is missing."""
    rows = [r - 1 for r in ic_resets]
    eligible = s_mask.iloc[rows].to_numpy(dtype=bool)
    finite = signal.iloc[rows].notna().to_numpy() & eligible
    by_month = (eligible.sum(axis=1) - finite.sum(axis=1)).astype(int)
    dates = [signal.index[r].date().isoformat() for r in ic_resets]
    return {"total": int(by_month.sum()), "by_month": dict(zip(dates, by_month.tolist()))}


def ic_evaluation(signal: pd.DataFrame, labels: pd.DataFrame, s_mask: pd.DataFrame,
                  ic_resets: tuple[int, ...]) -> dict[str, Any]:
    """The primary Rank IC test of one factor with halves, MDE, and coverage loss (plan 4.6, 6.4, 6.8)."""
    months = monthly_rank_ic(signal, labels, ic_resets)
    valid = months[months["status"] == "valid"]
    ic = pd.Series(valid["rank_ic"].to_numpy(dtype=float), index=pd.DatetimeIndex(valid["reset_date"]))
    first, second = split_halves(ic)
    mde_f, mde_single = ic_minimum_detectable_effect(ic)
    return {
        "status": "evaluated" if len(ic) >= MIN_IC_MONTHS else "invalid_insufficient_ic_months",
        "ic_month_count": len(ic), "ic_month_gap_count": int(len(months) - len(ic)),
        "invalid_months": {k: int(v) for k, v in months["status"].value_counts().items() if k != "valid"},
        "mean_ic": float(ic.mean()) if len(ic) else None,
        "ic_test": return_test_statistics(ic.reset_index(drop=True), periods_per_year=12),
        "halves": {"boundary_reset_date": second.index[0].date().isoformat() if len(second) else None,
                   "first": {"months": len(first), "mean_ic": float(first.mean()) if len(first) else None},
                   "second": {"months": len(second), "mean_ic": float(second.mean()) if len(second) else None}},
        "sign_stable": sign_stability(ic),
        "mde_f": mde_f, "mde_single": mde_single,
        "coverage_loss": coverage_loss(signal, s_mask, ic_resets),
        "finite_pair_count_by_month": dict(zip((d.date().isoformat() for d in months["reset_date"]),
                                               months["finite_pair_count"].tolist())),
    }


# ---------------------------------------------------------------- segmented books (plan 4.3, 4.4)


def run_segmented_book(
    book: str, prices: pd.DataFrame, signal: pd.DataFrame, calendar: pd.DatetimeIndex,
    segments: Sequence[Any], *, intervals: pd.DataFrame, events: pd.DataFrame, cost: dict[str, float],
    benchmark: pd.Series | None = None, top_pct: float = TOP_PCT,
) -> list[Any]:
    """One bounded engine call per valid segment; a Class I engine reason raises ``RunnerStop``.

    ``book`` is ``long_short`` (deciles, equal weight, gross leverage 1) or
    ``long_only`` (``top_pct``, equal weight). Each segment starts from cash
    at its anchor; the terminal row keeps its open holdings (TIMING-012).
    """
    provenance = capture_backtest_source_provenance(prices, signal) if book == "long_only" else None
    results = []
    for segment in segments:
        start, end = calendar[segment.anchor], calendar[segment.last]
        common = dict(evaluation_start=start, evaluation_end=end, rebalance_frequency="ME", weighting_scheme="equal",
                      turnover_penalty_lambda=0.0, constituent_intervals=intervals,
                      terminal_events=events if len(events) else None, **cost)
        try:
            if book == "long_short":
                results.append(run_long_short_backtest(prices, signal, quantiles=QUANTILES, gross_leverage=1.0,
                                                       **common))
            else:
                results.append(run_long_only_backtest(
                    prices, signal, source_provenance=provenance, top_pct=top_pct,
                    benchmark_prices=None if benchmark is None else benchmark.loc[start:end], **common))
        except BacktestValidationError as exc:
            if exc.reason in CLASS_I_ENGINE:
                raise RunnerStop(exc.reason, str(exc)) from exc
            raise
    return results


def _max_drawdown(equity: pd.Series) -> float:
    return float(-(equity / equity.cummax() - 1.0).min())


def book_halves(net: pd.Series, boundary: str | None) -> dict[str, Any]:
    """Descriptive half-sample statistics split at the factor's IC-half boundary (plan 4.4, 6.8).

    ``boundary`` is the reset date of the first IC month of the second half.
    A daily return dated on or before it ends a holding period that began
    before that reset, so it belongs to the first half; later returns belong
    to the second half.
    """
    if boundary is None:
        return {"status": "undefined_no_ic_boundary", "boundary_reset_date": None}
    cut = pd.Timestamp(boundary)

    def describe(part: pd.Series) -> dict[str, Any]:
        return {"rows": len(part), "mean_daily_net_return": float(part.mean()) if len(part) else None,
                "annualized_volatility": float(part.std(ddof=1) * math.sqrt(252)) if len(part) > 1 else None,
                "return_test": return_test_statistics(part, periods_per_year=252)}

    first, second = net[net.index <= cut], net[net.index > cut]
    status = "evaluated" if len(first) and len(second) else "undefined_boundary_outside_measured_rows"
    return {"status": status, "boundary_reset_date": boundary, "first": describe(first), "second": describe(second)}


def book_statistics(results: list[Any], book: str, boundary: str | None = None) -> tuple[dict[str, Any], pd.Series]:
    """Pooled daily statistics over the measured rows, the per-segment record of plan 4.3, and the halves."""
    net = pd.concat([r.returns.iloc[1:] for r in results])
    held = [(r.net_holdings if book == "long_short" else r.holdings).iloc[-1] for r in results]
    segments = [{
        "first_month": r.returns.index[1].strftime("%Y-%m"), "last_month": r.returns.index[-1].strftime("%Y-%m"),
        "measured_rows": len(r.returns) - 1, "turnover": float(r.turnover.iloc[1:].sum()),
        "trading_costs": float(r.total_trading_costs.iloc[1:].sum()), "max_drawdown": _max_drawdown(r.equity_curve),
        "first_row_net_return": float(r.returns.iloc[1]), "terminal_row_trading_cost": float(r.total_trading_costs.iloc[-1]),
        "terminal_open_positions": int((h.abs() > 0).sum()), "terminal_gross_exposure": float(h.abs().sum()),
    } for r, h in zip(results, held)]
    test = return_test_statistics(net, periods_per_year=252)
    return {
        "return_test": test, "measured_rows": len(net), "segments": segments,
        "pooled_turnover": sum(s["turnover"] for s in segments),
        "pooled_trading_costs": sum(s["trading_costs"] for s in segments),
        "pooled_max_drawdown": max(s["max_drawdown"] for s in segments),
        "hac_boundary_adjacency_pairs": (len(results) - 1) * int(test["hac_lags"]),
        "total_lag_products": len(net) * int(test["hac_lags"]),
        "mean_daily_net_return": float(net.mean()), "halves": book_halves(net, boundary),
    }, net


def book_trial(
    book: str, prices: pd.DataFrame, signal: pd.DataFrame, calendar: pd.DatetimeIndex, segments: Sequence[Any], *,
    cost: dict[str, float], intervals: pd.DataFrame, events: pd.DataFrame, spy: pd.Series, spy_daily: pd.Series,
    equal_weight: pd.Series | None, objective: dict[str, Any], boundary: str | None = None,
) -> tuple[dict[str, Any], pd.Series | None, list[Any] | None]:
    """One book trial: a Class II error becomes a ``failed`` record; a Class I reason raises ``RunnerStop`` (plan 4.5).

    Returns the trial fields, the daily net returns on ``Mrows``, and the
    per-segment engine results (both ``None`` when the trial failed).
    """
    try:
        results = run_segmented_book(book, prices, signal, calendar, segments, intervals=intervals, events=events,
                                     cost=cost, benchmark=spy if book == "long_only" else None)
        fields, net = book_statistics(results, book, boundary)
    except (BacktestValidationError, ValueError, ArithmeticError) as exc:
        return _failure(exc), None, None
    fields["status"] = "evaluated"
    fields["max_drawdown_within_budget"] = fields["pooled_max_drawdown"] <= objective["max_drawdown_budget"][book]
    if book == "long_only":
        spy_excess = excess_metrics(net, spy_daily)
        ratio, tracking = spy_excess["information_ratio"], spy_excess["tracking_error"]
        fields.update({
            "excess_vs_spy": spy_excess,
            "excess_vs_equal_weight": ({"status": "benchmark_failed"} if equal_weight is None
                                       else excess_metrics(net, equal_weight)),
            "information_ratio_within_budget": None if ratio is None else ratio >= objective["target_information_ratio"],
            "tracking_error_within_budget": (None if tracking is None
                                             else tracking <= objective["tracking_error_budget_annualized"]),
        })
    return fields, net, results


def excess_metrics(net: pd.Series, reference: pd.Series) -> dict[str, Any]:
    """Excess total return, tracking error, and information ratio over a reference on the measured rows."""
    if not net.index.equals(reference.index):
        raise ValueError("excess_rows_misaligned: book and reference measured rows differ")
    excess = net - reference
    tracking = float(excess.std(ddof=1) * math.sqrt(252)) if len(excess) > 1 else math.nan
    ratio = float(excess.mean() * 252 / tracking) if math.isfinite(tracking) and tracking > 0 else None
    return {"excess_total_return": float((1 + net).prod() - (1 + reference).prod()),
            "tracking_error": tracking if math.isfinite(tracking) else None,
            "information_ratio": ratio, "status": "ok" if ratio is not None else "undefined_tracking_error"}


def cpcv_family(columns: dict[str, pd.Series | None], rows: pd.DatetimeIndex, holding: int) -> dict[str, Any]:
    """One CPCV/PBO family on ``Mrows``: failed columns omitted and counted (plan 4.4, 6.7)."""
    completed = {k: v for k, v in columns.items() if v is not None}
    base = {"columns_completed": len(completed), "pbo_columns_missing_failed": len(columns) - len(completed),
            "n_splits": CPCV_SPLITS, "holding_periods": holding, "embargo_periods": CPCV_EMBARGO,
            "rows": len(rows)}
    if len(completed) < 2:
        return {**base, "status": "unavailable", "unavailable_reason": "pbo_unavailable:insufficient_completed_strategies"}
    if any(not series.index.equals(rows) for series in completed.values()):
        raise ValueError("cpcv_matrix_misaligned: every column must be indexed by Mrows")
    matrix = pd.DataFrame(completed)
    if not np.isfinite(matrix.to_numpy(dtype=float)).all():
        raise ValueError("cpcv_matrix_nonfinite")
    reason = cpcv_geometry_unavailable_reason(len(matrix), n_splits=CPCV_SPLITS, holding_periods=holding,
                                              embargo_periods=CPCV_EMBARGO)
    if reason is not None:
        return {**base, "status": "unavailable", "unavailable_reason": reason}
    summary = combinatorial_purged_cross_validation_pbo(matrix, n_splits=CPCV_SPLITS, holding_periods=holding,
                                                        embargo_periods=CPCV_EMBARGO)
    return {**base, "status": "available", **{k: summary[k] for k in (
        "pbo", "prob_loss", "n_combinations", "mean_purged_samples", "mean_embargoed_samples",
        "mean_is_sharpe", "mean_oos_sharpe")}}


def excluded_event_exposure(schedule: SupportSchedule, unresolved: dict[str, int], calendar: pd.DatetimeIndex,
                            books: dict[str, list[Any]]) -> list[dict[str, Any]]:
    """Per book and gap: each excluded asset held at the preceding segment's terminal row (plan 4.4).

    ``books`` maps a trial label to its per-valid-segment engine results.
    Public rows carry the gap's month, the reason type, the side, and the
    signed weight, and no permanent ID (R11).
    """
    valid = [s for s in schedule.segments if s.valid]
    cells = [(schedule.g_base.columns[c], int(r), "missing_bar")
             for r, c in zip(*np.nonzero(schedule.g_base.to_numpy(dtype=bool)))]
    cells += [(pid, row, "terminal_reset_missing_bar") for pid, row in schedule.g_term]
    cells += [(pid, row, "unresolved_delisting") for pid, row in unresolved.items()]
    out = []
    for position, window in enumerate(schedule.windows):
        preceding = next((k for k, s in enumerate(valid) if s.last == window.start - 1), None)
        if preceding is None:
            continue
        assets = sorted({(pid, reason) for pid, row, reason in cells if window.start <= row <= window.end})
        for trial, results in books.items():
            result = results[preceding]
            held = (result.net_holdings if hasattr(result, "net_holdings") else result.holdings).iloc[-1]
            for pid, reason in assets:
                weight = float(held.get(pid, 0.0))
                if weight != 0.0:
                    out.append({"gap_index": position, "gap_start_month": calendar[window.start].strftime("%Y-%m"),
                                "trial": trial, "reason_type": reason, "side": "long" if weight > 0 else "short",
                                "signed_weight": weight})
    return out


# ---------------------------------------------------------------- run (plan 7.3 b-1)


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    return value


class _Trials:
    """Append-only trials JSONL: every record is written when its trial finishes (R9).

    The file is truncated on the first ``add``; until then ``path`` is untouched,
    so a refusal before any trial leaves a prior run's JSONL byte-identical.
    """

    def __init__(self, path: Path, registration_sha256: str, context: dict[str, Any]) -> None:
        self.path, self.registration_sha256, self.context = path, registration_sha256, context
        self.records: list[dict[str, Any]] = []
        self._initialized = False

    def add(self, family: str, factor_id: str, hypothesis: str, fields: dict[str, Any], *, book: str | None = None,
            cost_case: str | None = None) -> dict[str, Any]:
        specification = {"family": family, "factor_id": factor_id, "hypothesis": hypothesis, "book": book,
                         "cost_case": cost_case}
        trial_id = hashlib.sha256(json.dumps({**specification, "registration_sha256": self.registration_sha256},
                                             sort_keys=True).encode()).hexdigest()
        record = _clean({"trial_id": trial_id, "family": family, "factor_id": factor_id, "hypothesis": hypothesis,
                         "book": book, "cost_case": cost_case, "specification": specification,
                         "registration_sha256": self.registration_sha256, **self.context, **fields})
        if not self._initialized:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_bytes(b"")
            self._initialized = True
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
        self.records.append(record)
        return record


def _failure(exc: Exception) -> dict[str, Any]:
    return {"status": "failed", "error_type": type(exc).__name__, "error": str(exc)}


def _for_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**r, "status": "completed" if r["status"] == "evaluated" else r["status"]} for r in records]


def run_rerun(
    snapshot_dir: Path | str, *, registration_path: Path | str, registration_sha256: str,
    output_dir: Path | str, census_json: Path | str = CENSUS_JSON, seal_record: Path | str = SEAL_RECORD,
    code_commit: str | None = None,
) -> dict[str, Any]:
    """Run the registered rerun and write the report, sidecar, and trials JSONL; return the sidecar.

    A Class I stop before the first trial record writes nothing, so the outputs
    of an earlier run stay byte-identical, and returns the sidecar with
    ``outputs_written = False``. A Class I stop after the first trial record
    writes the sidecar, the report, and the trials recorded so far.
    """
    out = Path(output_dir)
    registration_bytes = Path(registration_path).read_bytes()
    actual = sha256_bytes(registration_bytes)
    state: dict[str, Any] = {"header": {"registration_sha256": actual, "registration_sha256_expected": registration_sha256,
                                        "code_commit": code_commit if code_commit is not None else _code_commit()}}
    trials = _Trials(out / TRIALS, actual, {})
    try:
        if actual != registration_sha256:
            raise RunnerStop("registration_hash_mismatch", "registration bytes differ from --registration-sha256")
        try:
            registration = json.loads(registration_bytes)
            costs = check_registration(registration)
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise RunnerStop("registration_invalid", f"{type(exc).__name__}: {exc}") from exc
        bound = bind_snapshot(Path(snapshot_dir), registration, Path(census_json), Path(seal_record))
        loaded = load_member_panels(bound)
        _execute(state, trials, registration, costs, bound, loaded, Path(snapshot_dir))
        state["run_status"] = "completed"
    except RunnerStop as stop:
        state["run_status"] = "stopped_before_inference"
        state["stop"] = {"reason": stop.reason, "detail": stop.detail, "trial": stop.trial,
                         "trial_records_retained": len(trials.records)}
        if not trials.records:
            return _clean({**_sidecar_head(), **state, "outputs_written": False})
    sidecar = _clean({**_sidecar_head(), **state, "outputs_written": True,
                      "trials_jsonl_sha256": sha256_bytes((out / TRIALS).read_bytes())})
    write_bytes(out / SIDECAR, (json.dumps(sidecar, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    write_bytes(out / REPORT, render_report(sidecar).encode("utf-8"))
    return sidecar


def _sidecar_head() -> dict[str, Any]:
    return {"schema_version": "m4_7_sp500_pit_rerun_result_v1", "evidence_ceiling": "DIAGNOSTIC_ONLY",
            "formal_universe_evidence_eligible": False, "formal_terminal_evidence_eligible": False}


def _execute(state: dict[str, Any], trials: _Trials, registration: dict[str, Any], costs: dict[str, dict[str, float]],
             bound: dict[str, Any], loaded: dict[str, Any], snapshot_dir: Path) -> None:
    calendar, assets, research = loaded["calendar"], loaded["assets"], loaded["research"]
    prices, spy = research["adjusted_close"], loaded["spy"]
    support = recompute_support(bound, loaded, registration)
    schedule, events, bars = support.schedule, support.events, support.bars
    horizon = registration["discovery"]["max_reset_to_reset_rows"]
    census, record = bound["census"], support.record()
    ic_resets, ic_excluded = ic_month_set(schedule)
    valid = [s for s in schedule.segments if s.valid]
    g_count = int(schedule.g_base.to_numpy().sum()) + len(schedule.g_term)
    state["header"].update({
        "snapshot_id": registration["snapshot"]["snapshot_id"],
        "manifest_sha256": registration["snapshot"]["manifest_sha256"],
        "segments_sha256": support.segments_sha256, "census_json_sha256": registration["snapshot"]["census_json_sha256"],
        "discovery_window": {"holdout_end": record["holdout_end"], "D0": record["D0"], "D_last": record["D_last"],
                             "D_end": record["D_end"]},
        "prior_exposure_overlap_fraction": {k: v["fraction_of_ic_months"] for k, v in
                                            census["discovery_overlap_with_prior_exposures"].items()},
        "U": len(support.unresolved_in_window()), "G": g_count, "W": len(schedule.windows),
        "excluded_rows": schedule.excluded_rows, "excluded_fraction": schedule.excluded_fraction,
        "eligible_unpriced_member_day_fraction": census["price_coverage"]["eligible_unpriced_fraction"],
        "census_readiness": census["census_readiness"]["status"],
        "premises": {
            **VP_STATEMENTS, "a1_volume_half": census["volume_basis_split_diagnostic"]["a1_volume_half"],
            "in_span_distribution_support_fraction":
                census["in_span_distribution_support"]["fraction_of_eligible_member_days"],
            "b_d": census["in_span_distribution_support"]["b_d"], "s_d": census["in_span_distribution_support"]["s_d"],
            "vp2_revisit_required": census["vp2_revisit_required"], "o8_disposition": "ratified",
            "rounding_statement": ROUNDING_STATEMENT},
        "holdout_guard": {"holdout_end_exclusive": record["holdout_end"],
                          "first_loaded_date": calendar[0].date().isoformat(),
                          "overlap": bool(calendar[0].date().isoformat() < record["holdout_end"])},
    })
    state["assumptions"] = {
        "timing_contract": registration["timing"]["contract"], "label_contract": registration["timing"]["label_contract"],
        "window_splitting_contract": registration["common_support"]["contract"],
        "initialization_anchor_policy": "zero_return_zero_trade_all_cash_excluded_from_statistics",
        "terminal_row_policy": "include_return_trade_cost_open_holdings_no_future_return",
        "segment_count": len(valid), "segment_terminal_reset_months": [calendar[s.last].strftime("%Y-%m") for s in valid],
        "terminal_reset_cells": len(schedule.g_term), "excluded_rows": schedule.excluded_rows,
        "excluded_fraction": schedule.excluded_fraction,
        "gap_windows": [{"start_month": w["start"][:7], "end_month": w["end"][:7], "reason_types": w["reasons"],
                         "peeled_rows": w["peeled_rows"]} for w in record["gap_windows"]],
        "settlement_lag_distribution": bound["validation"]["settlement_lag_distribution"],
        "cash_availability_idealization_rows_max": registration["terminal"]["cash_availability_idealization_rows_max"],
        "consideration_valuation_rule": registration["terminal"]["consideration_valuation_rule"],
        "settlement_contract": registration["terminal"]["settlement_contract"],
        "costs": costs, "impact_model": "none", "borrow_cost": "absent_from_the_long_short_engine",
        "first_discovery_date": calendar[schedule.d0].date().isoformat(),
        "market_beta_neutral_composite_market": "equal_weight_market_of_eligible_names",
        "cpcv_boundary_conservatism": "segment concatenation purges labels that cannot overlap in calendar time",
        "engine_frame_columns": "member_permanent_ids_only", "member_columns": len(assets),
    }
    context = {"segments_sha256": support.segments_sha256, "segment_count": len(valid),
               "excluded_rows": schedule.excluded_rows}
    trials.context = context
    s_mask = signal_eligibility(support.mask, bars)
    labels, label_records = ic_labels(prices, s_mask, schedule, ic_resets, events)
    write_bytes(snapshot_dir / LABEL_RECORDS, _canonical(_clean(label_records.reset_index().to_dict(orient="records"))))
    eligible = s_mask.iloc[[r - 1 for r in ic_resets]].sum(axis=1)
    state["labels"] = {
        "ic_month_supply": len(ic_resets),
        **{reason.replace("ic_month_", "ic_months_"): len(rows) for reason, rows in ic_excluded.items()},
        "terminal_aware_labels": int(label_records["terminal_aware_labels"].sum()) if len(label_records) else 0,
        "missing_execution_bar": 0, "missing_horizon_end_bar": 0,
        "eligible_count_by_month": dict(zip((calendar[r].date().isoformat() for r in ic_resets),
                                            eligible.astype(int).tolist())),
    }

    signals: dict[str, dict[str, pd.DataFrame | Exception]] = {}
    try:
        signals["A"] = dict(family_a_signals(prices, spy, research["dollar_volume"], s_mask))
    except (ValueError, ArithmeticError) as exc:
        signals["A"] = {factor_id: exc for factor_id in FAMILY_A_IDS}
    alphas = family_b_alphas(research, s_mask)
    signals["B"] = dict(alphas)
    rebalances = calendar[[r - 1 for r in schedule.reset_rows if schedule.d0 <= r <= schedule.d_last]]
    if any(isinstance(v, Exception) for v in alphas.values()):
        failed = ValueError("parent_alpha_failed: every composite needs the 52 alphas")
        signals["B"].update({c: failed for c in FAMILY_B_COMPOSITES})
    else:
        try:
            signals["B"].update(family_b_composites(research, s_mask, alphas, labels, ic_resets, rebalances, horizon))
        except (ValueError, ArithmeticError, KeyError) as exc:
            signals["B"].update({c: exc for c in FAMILY_B_COMPOSITES})

    estimate = census["warm_up_estimate"]["post_join_warmup_estimate"]
    primary: dict[str, dict[str, Any]] = {}
    for family, ids in (("A", FAMILY_A_IDS), ("B", FAMILY_B_IDS)):
        for factor_id in ids:
            signal = signals[family][factor_id]
            if isinstance(signal, Exception):
                fields = _failure(signal)
            else:
                try:
                    fields = ic_evaluation(signal, labels, s_mask, ic_resets)
                except (ValueError, ArithmeticError) as exc:
                    fields = _failure(exc)
            if family == "A" and "coverage_loss" in fields:
                loss = fields["coverage_loss"]["total"]
                if estimate[factor_id] > loss:
                    raise RunnerStop("census_runner_inconsistency:warmup_estimate", factor_id, trial=factor_id)
                fields["coverage_loss_estimate"] = estimate[factor_id]
                fields["coverage_loss_beyond_estimate"] = loss - estimate[factor_id]
            primary[factor_id] = trials.add(family, factor_id, "rank_ic_mean", fields)
    try:  # the family partition refuses unless each family's distinct trials equal its declared size
        by_family = summarize_multiple_testing(_for_summary(list(primary.values())), family_sizes=FAMILY_SIZES,
                                               statistic_key="ic_test")
    except ValueError as exc:
        raise RunnerStop("family_size_mismatch", str(exc)) from exc
    union = summarize_multiple_testing(_for_summary(list(primary.values())), family_size=UNION_SIZE,
                                       statistic_key="ic_test")
    adjusted = {row["specification"]["factor_id"]: row for row in by_family["rows"]}
    union_q = {row["specification"]["factor_id"]: row["adjusted_pvalues"]["hac"]["by"] for row in union["rows"]}

    common = dict(intervals=loaded["intervals"][loaded["intervals"]["permanent_id"].isin(assets)], events=events)
    measured = calendar[np.concatenate([np.arange(s.first, s.last + 1) for s in valid])]
    spy_daily = spy.pct_change(fill_method=None).loc[measured]
    exposure_books: dict[str, list[Any]] = {}
    ew_net: pd.Series | None = None
    try:
        ew_results = run_segmented_book("long_only", prices, equal_weight_signal(s_mask), calendar, valid,
                                        cost=costs["zero_cost_diagnostic_only"], top_pct=1.0, **common)
        ew_stats, ew_net = book_statistics(ew_results, "long_only")
        exposure_books["equal_weight_pit"] = ew_results
        ew_record = {"status": "evaluated", **ew_stats, "excess_vs_spy": excess_metrics(ew_net, spy_daily)}
    except RunnerStop as stop:
        stop.trial = "equal_weight_pit"
        raise
    except (BacktestValidationError, ValueError, ArithmeticError) as exc:
        ew_record = _failure(exc)
    state["benchmarks"] = {"equal_weight_pit": ew_record,
                           "spy": {"status": "evaluated", "return_test": return_test_statistics(spy_daily, periods_per_year=252)}}
    objective = registration["objective"]
    books: dict[str, dict[str, Any]] = {}
    nets: dict[tuple[str, str, str], pd.Series | None] = {}
    for family, ids in (("A", FAMILY_A_IDS), ("B", FAMILY_B_IDS)):
        for factor_id in ids:
            for cost_case in (COST_CASES if family == "A" else ("primary",)):
                for book in ("long_short", "long_only"):
                    signal, key = signals[family][factor_id], (factor_id, book, cost_case)
                    if isinstance(signal, Exception):
                        fields, net, results = _failure(signal), None, None
                    else:
                        try:
                            fields, net, results = book_trial(
                                book, prices, signal, calendar, valid, cost=costs[cost_case], spy=spy,
                                spy_daily=spy_daily, equal_weight=ew_net, objective=objective,
                                boundary=(primary[factor_id].get("halves") or {}).get("boundary_reset_date"), **common)
                        except RunnerStop as stop:
                            stop.trial = f"{family}:{factor_id}:{book}:{cost_case}"
                            raise
                    nets[key] = net
                    if results is not None and cost_case == "primary":
                        exposure_books[f"{family}:{factor_id}:{book}"] = results
                    books["|".join(key)] = trials.add(family, factor_id, "book_return", fields, book=book,
                                                      cost_case=cost_case)

    state["cpcv"] = {
        f"{family}_{kind}": cpcv_family(
            {f: (nets[(f, book, "primary")] if kind == "long_short" or nets[(f, book, "primary")] is None
                 else nets[(f, book, "primary")] - spy_daily) for f in ids}, measured, horizon)
        for family, ids in (("A", FAMILY_A_IDS), ("B", FAMILY_B_IDS))
        for kind, book in (("long_short", "long_short"), ("excess", "long_only"))
    }
    state["dsr"] = {}
    for family, ids in (("A", FAMILY_A_IDS), ("B", FAMILY_B_IDS)):
        series = {f: nets[(f, "long_short", "primary")] for f in ids if nets[(f, "long_short", "primary")] is not None}
        sharpes = [float(s.mean() / s.std(ddof=1)) for s in series.values() if s.std(ddof=1) > 0]
        variance = float(np.var(sharpes, ddof=1)) if len(sharpes) >= 2 else None
        state["dsr"][family] = {"n_trials": FAMILY_SIZES[family], "trial_sharpe_variance": variance, "values": {
            f: (deflated_sharpe_ratio(s, n_trials=FAMILY_SIZES[family], trial_sharpe_variance=variance)
                if variance is not None else None) for f, s in series.items()}}
    ls_primary = [books[f"{f}|long_short|primary"] for f in FAMILY_A_IDS + FAMILY_B_IDS]
    haircuts = summarize_multiple_testing(_for_summary(ls_primary), family_sizes=FAMILY_SIZES,
                                          statistic_key="return_test")
    state["iid_sharpe_haircuts"] = {row["specification"]["factor_id"]: row["iid_haircuts"].get("by")
                                    for row in haircuts["rows"]}
    state["excluded_event_exposure"] = excluded_event_exposure(schedule, support.unresolved_in_window(), calendar,
                                                               exposure_books)

    state["families"] = {}
    for family, ids in (("A", FAMILY_A_IDS), ("B", FAMILY_B_IDS)):
        rows = {}
        for factor_id in ids:
            trial, row = primary[factor_id], adjusted[factor_id]
            ls = books[f"{factor_id}|long_short|primary"]
            rows[factor_id] = {
                "status": trial["status"], "ic_month_count": trial.get("ic_month_count"),
                "mean_ic": trial.get("mean_ic"), "hac_pvalue": (trial.get("ic_test") or {}).get("hac_pvalue"),
                "ic_test_status": (trial.get("ic_test") or {}).get("status"),
                "by_q": row["adjusted_pvalues"]["hac"]["by"], "reject": row["rejections"]["hac"]["by"],
                "union_by_q": union_q[factor_id], "halves": trial.get("halves"), "sign_stable": trial.get("sign_stable"),
                "mde_f": trial.get("mde_f"), "mde_single": trial.get("mde_single"),
                "coverage_loss": (trial.get("coverage_loss") or {}).get("total"),
                "coverage_loss_estimate": trial.get("coverage_loss_estimate"),
                "coverage_loss_beyond_estimate": trial.get("coverage_loss_beyond_estimate"),
                "long_short_status": ls["status"],
                "long_short_mean_daily_net_return": ls.get("mean_daily_net_return"),
                "long_short_hac_pvalue": (ls.get("return_test") or {}).get("hac_pvalue"),
            }
        state["families"][family] = {"family_size": FAMILY_SIZES[family], "rows": rows,
                                     "positive_by_rejections": sum(r["reject"] and (r["mean_ic"] or 0.0) > 0.0
                                                                   for r in rows.values())}
    state["books"] = {key: {k: v for k, v in record.items() if k not in ("specification", "segments_sha256")}
                      for key, record in books.items() if record["family"] == "A"}
    state["family_b_books"] = {
        "status_counts": pd.Series([r["status"] for k, r in books.items() if r["family"] == "B"]).value_counts().to_dict()}

    gate_inputs = []
    for factor_id in FAMILY_A_IDS:
        row = state["families"]["A"]["rows"][factor_id]
        status = {"evaluated": "evaluated", "failed": "failed"}.get(row["status"], "invalid")
        net = row["long_short_mean_daily_net_return"] if row["long_short_status"] == "evaluated" else None
        gate_inputs.append(FactorGateInput(factor_id, status, bool(row["reject"]),
                                           row["mean_ic"] if row["mean_ic"] is not None else math.nan,
                                           row["sign_stable"], net, row["mde_f"]))
    gate = decide_gate(gate_inputs, kill_reachable_projection=registration["statistics"]["power_projection"][
        "kill_reachable_projection"])
    state["gate"] = {**gate, "program_decision": PROGRAM_DECISION[gate["outcome"]],
                     "family_b_context": {"positive_by_rejections": state["families"]["B"]["positive_by_rejections"],
                                          "role": "exploratory; changes no decision"},
                     "owner_decision_o3": registration["statistics"]["power_projection"]["owner_decision_o3"]}


# ---------------------------------------------------------------- report (plan 6.9, 7.3; Appendix E)


def _fmt(value: Any, digits: int = 6) -> str:
    if value is None:
        return "undefined"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.{digits}g}"
    return str(value)


def render_report(sidecar: dict[str, Any]) -> str:
    """The markdown report: header, assumptions, families, segments, labels, books, PBO, and the gate."""
    header = sidecar.get("header", {})
    lines = [
        "# M4.7 S&P 500 PIT Rerun",
        "",
        "Evidence ceiling: `DIAGNOSTIC_ONLY`. No figure below supports a ranking, selection, promotion, or "
        "profitability claim; `formal_universe_evidence_eligible` and `formal_terminal_evidence_eligible` are false.",
        "",
        f"- Run status: `{sidecar['run_status']}`",
        f"- Registration SHA-256: `{header.get('registration_sha256')}`",
        f"- Code commit: `{header.get('code_commit')}`",
    ]
    if sidecar.get("stop"):
        stop = sidecar["stop"]
        lines += [f"- Stop reason (Class I): `{stop['reason']}` ({stop['detail']}); trial: `{stop['trial']}`; "
                  f"trial records retained: {stop['trial_records_retained']}", ""]
    if "discovery_window" not in header:
        return "\n".join(lines) + "\n"
    window, premises = header["discovery_window"], header["premises"]
    lines += [
        f"- Snapshot: `{header['snapshot_id']}`; manifest SHA-256 `{header['manifest_sha256']}`",
        f"- segments_sha256: `{header['segments_sha256']}`; census JSON SHA-256 `{header['census_json_sha256']}`",
        f"- Discovery window: holdout end `{window['holdout_end']}`, D0 `{window['D0']}`, D_last `{window['D_last']}`, "
        f"D_end `{window['D_end']}`",
        "- Prior-exposure overlap fractions: " + ", ".join(
            f"{k} {_fmt(v)}" for k, v in header["prior_exposure_overlap_fraction"].items()),
        f"- |U| = {header['U']}, |G| = {header['G']}, |W| = {header['W']}; excluded rows {header['excluded_rows']}, "
        f"excluded fraction {_fmt(header['excluded_fraction'])}",
        f"- Eligible unpriced member-day fraction: {_fmt(header['eligible_unpriced_member_day_fraction'])}",
        f"- Census readiness: `{header['census_readiness']}`",
        f"- Holdout guard: first loaded date `{header['holdout_guard']['first_loaded_date']}`, "
        f"overlap {_fmt(header['holdout_guard']['overlap'])}",
        "",
        "## Premises",
        "",
        f"- VP-1: {premises['VP-1']}; `a1_volume_half = {premises['a1_volume_half']}`",
        f"- VP-2: {premises['VP-2']}; in_span_distribution_support fraction "
        f"{_fmt(premises['in_span_distribution_support_fraction'])}; B_D quantiles {premises['b_d']}; "
        f"S_D quantiles {premises['s_d']}; vp2_revisit_required {_fmt(premises['vp2_revisit_required'])}",
        f"- O-8 disposition: {premises['o8_disposition']}",
        f"- Rounding: {premises['rounding_statement']}",
        "",
        "## Assumptions",
        "",
        *[f"- {key}: {_fmt(value)}" for key, value in sidecar["assumptions"].items() if key != "gap_windows"],
        "",
        "## Segments and gap windows (month granularity)",
        "",
        "| Start month | End month | Reason types | Peeled rows |",
        "| --- | --- | --- | --- |",
        *[f"| {w['start_month']} | {w['end_month']} | {', '.join(w['reason_types'])} | {w['peeled_rows']} |"
          for w in sidecar["assumptions"]["gap_windows"]],
        "",
    ]
    if "labels" in sidecar:
        labels = sidecar["labels"]
        lines += ["## Labels and IC months", "",
                  *[f"- {k}: {v}" for k, v in labels.items() if k != "eligible_count_by_month"], ""]
    if sidecar["run_status"] != "completed":
        return "\n".join(lines) + "\n"
    for family in ("A", "B"):
        rows = sidecar["families"][family]["rows"]
        lines += [
            f"## Family {family} primary tests (monthly Rank IC, BY within family of {sidecar['families'][family]['family_size']})",
            "",
            "| Factor | Status | T_f | Mean IC | HAC p | BY q | Union BY q | Half 1 mean | Half 2 mean | Sign stable | "
            "MDE_f | MDE_single | Coverage loss | Estimate | Beyond estimate | LS status | LS mean net | LS HAC p |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for factor_id, row in rows.items():
            halves = row["halves"] or {"first": {}, "second": {}}
            lines.append("| " + " | ".join(_fmt(v) for v in (
                factor_id, row["status"], row["ic_month_count"], row["mean_ic"], row["hac_pvalue"], row["by_q"],
                row["union_by_q"], halves["first"].get("mean_ic"), halves["second"].get("mean_ic"), row["sign_stable"],
                row["mde_f"], row["mde_single"], row["coverage_loss"], row["coverage_loss_estimate"],
                row["coverage_loss_beyond_estimate"], row["long_short_status"],
                row["long_short_mean_daily_net_return"], row["long_short_hac_pvalue"])) + " |")
        lines.append("")
    lines += ["## Family A books", "",
              "| Factor | Book | Cost case | Status | Mean daily net | HAC p | Turnover | Costs | Max drawdown | "
              "Within DD budget | Excess vs SPY | Excess vs EW | Tracking error | IR | IR within | TE within | Halves | "
              "Half 1 mean net | Half 2 mean net |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- "
              "| --- |"]
    for record in sidecar["books"].values():
        spy_x, ew_x = record.get("excess_vs_spy") or {}, record.get("excess_vs_equal_weight") or {}
        lines.append("| " + " | ".join(_fmt(v) for v in (
            record["factor_id"], record["book"], record["cost_case"], record["status"],
            record.get("mean_daily_net_return"), (record.get("return_test") or {}).get("hac_pvalue"),
            record.get("pooled_turnover"), record.get("pooled_trading_costs"), record.get("pooled_max_drawdown"),
            record.get("max_drawdown_within_budget"), spy_x.get("excess_total_return"), ew_x.get("excess_total_return"),
            spy_x.get("tracking_error"), spy_x.get("information_ratio"), record.get("information_ratio_within_budget"),
            record.get("tracking_error_within_budget"), (record.get("halves") or {}).get("status"),
            ((record.get("halves") or {}).get("first") or {}).get("mean_daily_net_return"),
            ((record.get("halves") or {}).get("second") or {}).get("mean_daily_net_return"))) + " |")
    lines += ["", f"- The zero-cost case is diagnostic only (R8). Family B books by status: "
                  f"{sidecar['family_b_books']['status_counts']}", "",
              "## Benchmarks", ""]
    ew = sidecar["benchmarks"]["equal_weight_pit"]
    ew_excess = (ew.get("excess_vs_spy") or {}) if ew.get("status") == "evaluated" else {}
    lines += [f"- Equal-weight PIT benchmark: status `{ew.get('status', 'missing')}`"
              + (f" ({ew.get('error_type')}: {ew.get('error')})" if ew.get("status") == "failed" else "")
              + f", mean daily net {_fmt(ew.get('mean_daily_net_return'))}, excess total return over SPY "
              f"{_fmt(ew_excess.get('excess_total_return'))}",
              f"- SPY.US#E1: status `{sidecar['benchmarks']['spy']['status']}`, mean daily return "
              f"{_fmt(sidecar['benchmarks']['spy']['return_test']['mean_return'])}", "",
              "## CPCV and PBO families", "",
              "| Family | Status | Reason | PBO | Completed columns | Failed columns omitted | Holding periods |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for name, value in sidecar["cpcv"].items():
        lines.append("| " + " | ".join(_fmt(v) for v in (
            name, value["status"], value.get("unavailable_reason"), value.get("pbo"), value["columns_completed"],
            value["pbo_columns_missing_failed"], value["holding_periods"])) + " |")
    lines += ["", "## Deflated Sharpe (long-short, primary costs)", ""]
    for family, value in sidecar["dsr"].items():
        lines.append(f"- Family {family}: n_trials {value['n_trials']}, trial Sharpe variance "
                     f"{_fmt(value['trial_sharpe_variance'])}; values " + ", ".join(
                         f"{k} {_fmt(v)}" for k, v in value["values"].items()))
    lines += ["- IID Sharpe haircuts (BY, disclosed as IID) are in the sidecar.", "",
              "## Excluded event exposure", "",
              "| Gap | Start month | Trial | Reason type | Side | Signed weight |", "| --- | --- | --- | --- | --- | --- |",
              *[f"| {e['gap_index']} | {e['gap_start_month']} | {e['trial']} | {e['reason_type']} | {e['side']} | "
                f"{_fmt(e['signed_weight'])} |" for e in sidecar["excluded_event_exposure"]],
              "",
              "Gap windows condition on the fact that an asset disappeared, halted, or joined with a missing bar; they "
              "apply to every book and benchmark alike.", ""]
    gate = sidecar["gate"]
    lines += ["## Decision gate", "",
              f"- Outcome: `{gate['outcome']}`",
              f"- Program decision: {gate['program_decision']}",
              f"- contrary_rejections: {gate['contrary_rejections']}",
              f"- power_status: `{gate['power_status']}`",
              f"- kill_reachable_projection: {_fmt(gate['kill_reachable_projection'])}",
              f"- family_b_context: {gate['family_b_context']}",
              f"- owner_decision_o3: `{gate['owner_decision_o3']}`", "",
              "## Limitations", "",
              "- Borrow cost is absent from the long-short engine; the constant spread understates costs before 2001.",
              "- Terminal rows pay a cost for holdings that are never measured, which is conservative for the strategy.",
              "- Family B carries no primary claim; short-horizon price-volume alphas lie outside the edge thesis.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m research.m4_7_sp500_pit_rerun")
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--registration", default=str(REGISTRATION_PATH))
    parser.add_argument("--registration-sha256", required=True)
    parser.add_argument("--output-dir", default=str(REPOSITORY_ROOT))
    parser.add_argument("--census-json", default=str(CENSUS_JSON))
    parser.add_argument("--seal-record", default=str(SEAL_RECORD))
    args = parser.parse_args(argv)
    try:
        snapshot_dir = snapshot_dir_from_args(args)
    except SnapshotRefusal as exc:
        print(str(exc), file=sys.stderr)
        return 2
    sidecar = run_rerun(snapshot_dir, registration_path=args.registration, registration_sha256=args.registration_sha256,
                        output_dir=args.output_dir, census_json=args.census_json, seal_record=args.seal_record)
    print(json.dumps({"run_status": sidecar["run_status"], "stop": sidecar.get("stop"),
                      "outputs_written": sidecar["outputs_written"],
                      "outcome": sidecar.get("gate", {}).get("outcome")}, sort_keys=True))
    return 0 if sidecar["run_status"] == "completed" else 3


if __name__ == "__main__":
    sys.exit(main())
