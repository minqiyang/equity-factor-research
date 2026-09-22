"""Real-data 50-stock multi-factor diagnostic runner.

This module loads the static blue-chip cohort and SPY.US benchmark from local
EODHD Parquet files, then reuses the committed 62-trial multi-factor diagnostic
path (52 classical price-volume alphas plus 12 composites and interactions).

It is DIAGNOSTIC_ONLY. The static cohort is survivorship-biased and is not
point-in-time universe evidence. Outputs are not profitability, strategy
validation, or a 14-trial campaign run. The runner reads local files only.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any
import uuid

import numpy as np
import pandas as pd

from backtest.portfolio import BacktestResult
from data.bluechip_cohort import BENCHMARK_SYMBOL, BLUECHIP_50_COHORT
from data.parquet_loader import DataIntegrityError, load_eod_cohort_panels
from features.combination import (
    equal_weighted_composite,
    walk_forward_correlation_discounted_composite,
    walk_forward_ic_weighted_composite,
    walk_forward_icir_weighted_composite,
)
from features.diagnostics import deflated_sharpe_ratio, probability_of_backtest_overfitting
from features.interaction import conditional_factor_rank, factor_product_interaction
from features.neutralize import (
    cross_sectional_group_neutralize,
    cross_sectional_neutralize,
)
from features.regime import (
    detect_market_volatility_regime,
    regime_switching_factor_composite,
)
from reporting.experiment_log import (
    DIAGNOSTIC_REAL_DATA_CAVEATS,
    REAL_DATA_MULTIFACTOR_EXPERIMENT_TYPE,
    resolve_experiment_log_path,
    write_experiment_log,
)
from research.multifactor_diagnostic_mvp import (
    ALPHA_016,
    ALPHA_022,
    ALPHA_IDS,
    ALPHA_PRODUCT_INTERACTION,
    ALPHA_WARMUP_PERIODS,
    CONDITIONAL_RANK_INTERACTION,
    CORRELATION_DISCOUNTED_COMPOSITE,
    EQUAL_WEIGHTED_COMPOSITE,
    FORWARD_HOLDING_PERIODS,
    IC_WEIGHTED_COMPOSITE,
    ICIR_WEIGHTED_COMPOSITE,
    MARKET_BETA_NEUTRAL_COMPOSITE,
    MultifactorDiagnosticConfig,
    NEUTRALIZED_IC_COMPOSITE,
    REGIME_SWITCHING_COMPOSITE,
    SECTOR_NEUTRAL_COMPOSITE,
    WEIGHTING_COMPARISON_FACTORS,
    _evaluate_factor,
    _format_number,
    _format_percent,
    _trial_family_summary,
    build_default_sector_mapping,
    calculate_diagnostic_alpha,
    compute_rolling_market_beta,
    evaluate_portfolio_weighting_comparisons,
)
from research.multiple_testing_diagnostics import render_multiple_testing, summarize_multiple_testing
from features.cross_validation import combinatorial_purged_cross_validation_pbo
from features.ml_combination import walk_forward_ml_factor_composite
from research.walking_skeleton_mvp import (
    execution_aligned_forward_returns,
    month_end_dates,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "real_data_multifactor_diagnostic.md"
DEFAULT_EXPERIMENT_LOG_PATH = (
    PROJECT_ROOT / "reports" / "experiment_logs" / "real_data_multifactor_diagnostic.json"
)
DEFAULT_DATA_DIR_ENV = "EFR_EODHD_DATA_DIR"
DEFAULT_INVENTORY_PATH_ENV = "EFR_EODHD_INVENTORY_PATH"
DEFAULT_SNAPSHOT_DIR_NAME = "snapshot_20260808T005805Z"
DEFAULT_INVENTORY_FILE_NAME = "per_stock_coverage.json"
DEFAULT_START_DATE = "2016-08-08"
DEFAULT_END_DATE = "2026-08-07"
REDACTED_LOCAL_PATH = "<redacted-local-path>"
REDACTED_DATA_DIR = "<redacted-local-eodhd-snapshot>"
REDACTED_INVENTORY_PATH = "<redacted-local-per-stock-coverage-inventory>"

RANDOM_FOREST_COMPOSITE = "RANDOM_FOREST_COMPOSITE"
GRADIENT_BOOSTING_COMPOSITE = "GRADIENT_BOOSTING_COMPOSITE"

COMPOSITE_IDS = (
    EQUAL_WEIGHTED_COMPOSITE,
    IC_WEIGHTED_COMPOSITE,
    ICIR_WEIGHTED_COMPOSITE,
    CORRELATION_DISCOUNTED_COMPOSITE,
    ALPHA_PRODUCT_INTERACTION,
    CONDITIONAL_RANK_INTERACTION,
    NEUTRALIZED_IC_COMPOSITE,
    SECTOR_NEUTRAL_COMPOSITE,
    MARKET_BETA_NEUTRAL_COMPOSITE,
    REGIME_SWITCHING_COMPOSITE,
    RANDOM_FOREST_COMPOSITE,
    GRADIENT_BOOSTING_COMPOSITE,
)
ESTIMATOR_VERSION = "m4_2_purged_cpcv_v1"


def default_data_dir() -> Path:
    """Return the local EODHD snapshot directory, honoring ``EFR_EODHD_DATA_DIR``."""

    raw = os.environ.get(DEFAULT_DATA_DIR_ENV)
    if raw:
        return Path(raw).expanduser().resolve()
    for parent in PROJECT_ROOT.parents:
        candidate = parent / "private_data" / "eodhd_eod_acquisition" / DEFAULT_SNAPSHOT_DIR_NAME
        if candidate.exists():
            return candidate.resolve()
    return Path("/private_data/eodhd_eod_acquisition") / DEFAULT_SNAPSHOT_DIR_NAME


def default_inventory_path() -> Path:
    """Return the local coverage inventory path, honoring ``EFR_EODHD_INVENTORY_PATH``."""

    raw = os.environ.get(DEFAULT_INVENTORY_PATH_ENV)
    if raw:
        return Path(raw).expanduser().resolve()
    for parent in PROJECT_ROOT.parents:
        candidate = (
            parent / "private_data" / "efr_exploration_inventory_20260913" / DEFAULT_INVENTORY_FILE_NAME
        )
        if candidate.exists():
            return candidate.resolve()
    return Path("/private_data/efr_exploration_inventory_20260913") / DEFAULT_INVENTORY_FILE_NAME


@dataclass(frozen=True)
class RealDataMultifactorDiagnosticConfig:
    """Diagnostic settings for the local EODHD 50-stock runner."""

    data_dir: Path = field(default_factory=default_data_dir)
    inventory_path: Path = field(default_factory=default_inventory_path)
    start_date: str = DEFAULT_START_DATE
    end_date: str = DEFAULT_END_DATE
    symbols: tuple[str, ...] = tuple(BLUECHIP_50_COHORT)
    benchmark_symbol: str = BENCHMARK_SYMBOL
    rebalance_frequency: str = "ME"
    top_n: int = 5
    weighting_scheme: str = "equal"
    long_short_weighting_scheme: str = "equal"
    turnover_penalty_lambda: float = 0.0
    volatility_window: int = 20
    transaction_cost_bps: float = 0.0
    slippage_bps: float = 5.0
    signal_lag_periods: int = 1
    periods_per_year: int = 252
    n_trials: int | None = None
    forward_holding_periods: int = FORWARD_HOLDING_PERIODS
    warmup_periods: int = ALPHA_WARMUP_PERIODS
    pbo_n_splits: int = 8
    pbo_holding_periods: int = FORWARD_HOLDING_PERIODS
    pbo_embargo_periods: int = 5
    quantiles: int = 10
    ridge_alpha: float = 0.1
    alpha_ids: tuple[str, ...] = ALPHA_IDS
    composite_ids: tuple[str, ...] = COMPOSITE_IDS
    include_weighting_comparisons: bool = True


def to_mvp_config(config: RealDataMultifactorDiagnosticConfig) -> MultifactorDiagnosticConfig:
    """Copy shared backtest fields onto the synthetic-runner config object."""

    return MultifactorDiagnosticConfig(
        rebalance_frequency=config.rebalance_frequency,
        top_n=config.top_n,
        weighting_scheme=config.weighting_scheme,
        long_short_weighting_scheme=config.long_short_weighting_scheme,
        turnover_penalty_lambda=config.turnover_penalty_lambda,
        volatility_window=config.volatility_window,
        transaction_cost_bps=config.transaction_cost_bps,
        slippage_bps=config.slippage_bps,
        signal_lag_periods=config.signal_lag_periods,
        periods_per_year=config.periods_per_year,
        n_trials=config.n_trials,
        forward_holding_periods=config.forward_holding_periods,
        warmup_periods=config.warmup_periods,
        pbo_n_splits=config.pbo_n_splits,
        quantiles=config.quantiles,
        ridge_alpha=config.ridge_alpha,
    )


def redact_local_path(path: Path | str | None) -> str:
    """Replace machine-local paths with redacted placeholders in tracked outputs."""

    if path is None:
        return REDACTED_LOCAL_PATH
    resolved = Path(path).expanduser()
    try:
        resolved = resolved.resolve()
    except OSError:
        resolved = Path(path)
    text = resolved.as_posix()
    if DEFAULT_SNAPSHOT_DIR_NAME in text or "eodhd_eod_acquisition" in text:
        return REDACTED_DATA_DIR
    if DEFAULT_INVENTORY_FILE_NAME in text or "efr_exploration_inventory" in text:
        return REDACTED_INVENTORY_PATH
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return REDACTED_LOCAL_PATH


def evaluate_diagnostic_readiness(
    panels: dict[str, pd.DataFrame],
    benchmark: pd.Series,
    config: RealDataMultifactorDiagnosticConfig | None = None,
) -> str:
    """Evaluate diagnostic readiness dynamically based on data validation and alignment."""

    if any(panel.empty for panel in panels.values() if isinstance(panel, pd.DataFrame)):
        return "refused_empty_panels"
    if benchmark.empty or not benchmark.index.equals(panels["close"].index):
        return "refused_benchmark_misaligned"
    for name, panel in panels.items():
        if not isinstance(panel, pd.DataFrame):
            continue
        arr = panel.to_numpy(dtype=float, na_value=0.0)
        if np.isinf(arr).any():
            return f"refused_infinite_values_in_{name}"
    for price_col in ("open", "high", "low", "close"):
        if (panels[price_col] <= 0).any().any():
            return f"refused_non_positive_{price_col}"
    if (panels["volume"] < 0).any().any():
        return "refused_negative_volume"
    has_missing = False
    for name, panel in panels.items():
        if not isinstance(panel, pd.DataFrame):
            continue
        if name == "returns":
            if panel.iloc[1:].isna().any().any():
                has_missing = True
                break
        else:
            if panel.isna().any().any():
                has_missing = True
                break
    if has_missing:
        return "diagnostic_ready_with_typed_missingness"
    return "diagnostic_ready_with_low_caveats"


def build_adjusted_research_panels(
    field_panels: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Build split-consistent OHLCV research panels from vendor fields.

    Research OHLC prices are split-adjusted (divided by cumulative split factor).
    Vendor volume in EODHD is already split-adjusted; keeping volume unscaled
    ensures ``research_close * research_volume`` identically matches true
    unadjusted dollar volume ``close * raw_volume`` without distortion from dividends.
    Vendor ``adjusted_close`` is retained for total-return calculations
    (including dividend distributions) and drives forward return labels,
    portfolio backtest pricing, and the accounting benchmark.
    VWAP is typical price on the split-adjusted bars. Missing cells stay missing.
    """

    close = field_panels["close"].astype(float)
    adjusted_close = field_panels["adjusted_close"].astype(float)
    volume = field_panels["volume"].astype(float)

    if "split_factor" in field_panels:
        cum_split = field_panels["split_factor"].astype(float)
    else:
        scale = close / adjusted_close
        scale_pct = scale.pct_change(fill_method=None).dropna()
        if (scale_pct.abs() > 0.15).any().any():
            raise DataIntegrityError(
                "Price / adjusted_close exhibits discontinuities (>15%) without verified split factor evidence. "
                "Cannot safely reconstruct split-adjusted turnover."
            )
        cum_split = pd.DataFrame(1.0, index=close.index, columns=close.columns, dtype=float)

    split_close = close / cum_split
    split_open = field_panels["open"].astype(float) / cum_split
    split_high = field_panels["high"].astype(float) / cum_split
    split_low = field_panels["low"].astype(float) / cum_split
    raw_volume = volume / cum_split
    dollar_volume = split_close * volume
    vwap = (split_high + split_low + split_close) / 3.0
    returns = adjusted_close.pct_change(fill_method=None)
    result = {
        "open": split_open,
        "high": split_high,
        "low": split_low,
        "close": split_close,
        "adjusted_close": adjusted_close,
        "vwap": vwap,
        "volume": volume,
        "raw_volume": raw_volume,
        "dollar_volume": dollar_volume,
        "returns": returns,
        "split_factor": cum_split,
    }
    if "permanent_id" in field_panels:
        result["permanent_id"] = field_panels["permanent_id"]
    return result


def load_real_data_research_panels(
    config: RealDataMultifactorDiagnosticConfig,
) -> tuple[dict[str, pd.DataFrame], pd.Series, tuple[str, ...]]:
    """Load cohort plus benchmark Parquet files into research OHLCV panels."""

    factor_symbols = _unique_symbols(config.symbols, field_name="symbols")
    if config.benchmark_symbol in factor_symbols:
        factor_symbols = tuple(
            symbol for symbol in factor_symbols if symbol != config.benchmark_symbol
        )
    if not factor_symbols:
        raise ValueError("symbols must include at least one non-benchmark asset")
    load_symbols = [*factor_symbols, config.benchmark_symbol]
    field_panels = load_eod_cohort_panels(
        config.data_dir,
        load_symbols,
        inventory_path=config.inventory_path,
        start_date=config.start_date,
        end_date=config.end_date,
    )
    research_panels = build_adjusted_research_panels(field_panels)
    factor_panels = {
        name: (
            panel.loc[:, list(factor_symbols)]
            if isinstance(panel, pd.DataFrame)
            else panel.reindex(list(factor_symbols))
        )
        for name, panel in research_panels.items()
    }
    benchmark = research_panels["adjusted_close"][config.benchmark_symbol].rename(
        config.benchmark_symbol
    )
    if benchmark.isna().any():
        raise ValueError("benchmark series contains missing values on the aligned panel")
    return factor_panels, benchmark, factor_symbols


def run_real_data_multifactor_diagnostic(
    *,
    config: RealDataMultifactorDiagnosticConfig | None = None,
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Run the local EODHD 50-stock diagnostic and optionally write reports."""

    config = RealDataMultifactorDiagnosticConfig() if config is None else config
    mvp_config = to_mvp_config(config)
    alpha_ids = _validate_id_subset(config.alpha_ids, ALPHA_IDS, field_name="alpha_ids")
    composite_ids = _validate_id_subset(
        config.composite_ids, COMPOSITE_IDS, field_name="composite_ids"
    )
    experiment_log_path = (
        resolve_experiment_log_path(
            report_path,
            default_report_path=DEFAULT_REPORT_PATH,
            default_log_path=DEFAULT_EXPERIMENT_LOG_PATH,
        )
        if experiment_log_path is None
        else experiment_log_path
    )

    panels, accounting_benchmark_full, factor_symbols = load_real_data_research_panels(
        config
    )
    readiness = evaluate_diagnostic_readiness(panels, accounting_benchmark_full, config)
    if readiness.startswith("refused_"):
        raise DataIntegrityError(f"Diagnostic dataset refused: {readiness}")

    inventory: list[dict[str, Any]] = []
    inventory_path = (
        Path(experiment_log_path).with_suffix(".trials.jsonl") if write_outputs else None
    )
    sample_digest = hashlib.sha256()
    for name, panel in sorted(panels.items()):
        if not isinstance(panel, pd.DataFrame):
            continue
        sample_digest.update(name.encode())
        sample_digest.update(pd.util.hash_pandas_object(panel, index=True).values.tobytes())
        sample_digest.update(repr(tuple(panel.columns)).encode())

    alpha_trial_context = {
        "estimator_version": ESTIMATOR_VERSION,
        "sample_sha256": sample_digest.hexdigest(),
        "estimator_parameters": {
            "warmup_periods": config.warmup_periods,
            "forward_holding_periods": config.forward_holding_periods,
        },
    }
    composite_trial_context = {
        "estimator_version": ESTIMATOR_VERSION,
        "sample_sha256": sample_digest.hexdigest(),
        "estimator_parameters": {
            "warmup_periods": config.warmup_periods,
            "forward_holding_periods": config.forward_holding_periods,
            "ridge_alpha": config.ridge_alpha,
            "parent_alpha_ids": list(sorted(config.alpha_ids)),
            "composite_ids": list(sorted(config.composite_ids)),
        },
    }

    def _record_failure(
        *,
        factor_id: str,
        stage: str,
        exc: Exception,
        context: dict[str, Any],
    ) -> None:
        if any(
            r.get("specification", {}).get("factor_id") == factor_id
            and r.get("status") == "failed"
            for r in inventory
        ):
            return
        spec = {**context, "factor_id": factor_id, "stage": stage}
        fail_record = {
            "trial_id": hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest(),
            "attempt_id": uuid.uuid4().hex,
            "specification": spec,
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        inventory.append(fail_record)
        if inventory_path is not None:
            inventory_path.parent.mkdir(parents=True, exist_ok=True)
            with inventory_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(fail_record, sort_keys=True, allow_nan=False) + "\n")

    prices = panels["adjusted_close"]
    if len(prices.index) <= config.warmup_periods + config.forward_holding_periods:
        raise ValueError("real-data panel is too short for alpha warm-up and labels")

    evaluation_start = prices.index[config.warmup_periods]
    evaluation_end = prices.index[-1]
    accounting_benchmark = accounting_benchmark_full.loc[evaluation_start:evaluation_end]
    if accounting_benchmark.isna().any():
        raise ValueError("benchmark is missing on the evaluation window")
    forward_returns = execution_aligned_forward_returns(
        prices,
        holding_periods=config.forward_holding_periods,
        execution_lag=config.signal_lag_periods,
    )
    monthly_dates = month_end_dates(prices.index)
    monthly_eval_dates = monthly_dates[
        (monthly_dates >= evaluation_start) & (monthly_dates <= evaluation_end)
    ]

    alpha_panels: dict[str, pd.DataFrame] = {}
    factor_results: dict[str, dict[str, Any]] = {}
    for factor_id in alpha_ids:
        try:
            factor = calculate_diagnostic_alpha(factor_id, panels)
        except Exception as exc:
            _record_failure(
                factor_id=factor_id,
                stage="feature_calculation",
                exc=exc,
                context=alpha_trial_context,
            )
            raise
        alpha_panels[factor_id] = factor
        try:
            factor_results[factor_id] = _evaluate_factor(
                factor_id=factor_id,
                inventory=inventory,
                inventory_path=inventory_path,
                trial_context=alpha_trial_context,
                factor=factor,
                prices=prices,
                forward_returns=forward_returns,
                monthly_eval_dates=monthly_eval_dates,
                accounting_benchmark=accounting_benchmark,
                evaluation_start=evaluation_start,
                evaluation_end=evaluation_end,
                config=mvp_config,
            )
        except Exception as exc:
            _record_failure(
                factor_id=factor_id,
                stage="alpha_evaluation",
                exc=exc,
                context=alpha_trial_context,
            )
            raise

    ordered_alphas = [alpha_panels[factor_id] for factor_id in alpha_ids]
    ic_weights = {
        factor_id: float(factor_results[factor_id]["ic_summary"]["mean_ic"])
        for factor_id in alpha_ids
    }
    ic_history = pd.DataFrame(
        {factor_id: factor_results[factor_id]["monthly_ic"] for factor_id in alpha_ids}
    )
    try:
        composites, ml_feature_importances = _build_composites(
            composite_ids=composite_ids,
            alpha_ids=alpha_ids,
            alpha_panels=alpha_panels,
            ordered_alphas=ordered_alphas,
            ic_history=ic_history,
            monthly_eval_dates=monthly_eval_dates,
            panels=panels,
            prices=prices,
            forward_returns=forward_returns,
            config=config,
        )
    except Exception as exc:
        _record_failure(
            factor_id="COMPOSITE_CONSTRUCTION",
            stage="composite_construction",
            exc=exc,
            context=composite_trial_context,
        )
        raise

    for factor_id, factor in composites.items():
        try:
            factor_results[factor_id] = _evaluate_factor(
                factor_id=factor_id,
                inventory=inventory,
                inventory_path=inventory_path,
                trial_context=composite_trial_context,
                factor=factor,
                prices=prices,
                forward_returns=forward_returns,
                monthly_eval_dates=monthly_eval_dates,
                accounting_benchmark=accounting_benchmark,
                evaluation_start=evaluation_start,
                evaluation_end=evaluation_end,
                config=mvp_config,
            )
        except Exception as exc:
            _record_failure(
                factor_id=factor_id,
                stage="composite_evaluation",
                exc=exc,
                context=composite_trial_context,
            )
            raise

    alpha_returns = pd.DataFrame(
        {
            factor_id: factor_results[factor_id]["backtest"].returns.iloc[1:]
            for factor_id in alpha_ids
        }
    )
    pbo_summary = probability_of_backtest_overfitting(
        alpha_returns,
        n_splits=config.pbo_n_splits,
    )
    cpcv_summary: dict[str, Any] | None = None
    try:
        cpcv_summary = combinatorial_purged_cross_validation_pbo(
            alpha_returns,
            n_splits=config.pbo_n_splits,
            holding_periods=config.pbo_holding_periods,
            embargo_periods=config.pbo_embargo_periods,
        )
    except ValueError:
        # Sample size or split geometry insufficient for purged and embargoed evaluation
        cpcv_summary = None

    weighting_comparisons: list[dict[str, Any]] = []
    if config.include_weighting_comparisons:
        comparison_factors = {
            factor_id: factor_results[factor_id]["factor"]
            for factor_id in WEIGHTING_COMPARISON_FACTORS
            if factor_id in factor_results
        }
        if comparison_factors:
            weighting_comparisons = evaluate_portfolio_weighting_comparisons(
                inventory=inventory,
                inventory_path=inventory_path,
                trial_context=composite_trial_context,
                factors=comparison_factors,
                prices=prices,
                accounting_benchmark=accounting_benchmark,
                evaluation_start=evaluation_start,
                evaluation_end=evaluation_end,
                config=mvp_config,
            )

    trial_family = _trial_family_summary(inventory, n_trials=config.n_trials)
    multiple_testing = summarize_multiple_testing(inventory, family_size=config.n_trials)
    for payload in factor_results.values():
        variance = trial_family["trial_sharpe_variance"]
        payload["dsr"] = (
            deflated_sharpe_ratio(
                payload["backtest"].returns.iloc[1:],
                n_trials=trial_family["n_trials_for_dsr"],
                trial_sharpe_variance=variance,
            )
            if variance is not None
            else math.nan
        )

    evaluated_ids = tuple(alpha_ids) + tuple(composite_ids)
    result = {
        "config": config,
        "mvp_config": mvp_config,
        "panels": panels,
        "prices": prices,
        "factor_symbols": factor_symbols,
        "accounting_benchmark": accounting_benchmark_full,
        "evaluation_start": evaluation_start,
        "evaluation_end": evaluation_end,
        "factors": factor_results,
        "ic_weights": ic_weights,
        "sector_map": build_default_sector_mapping(prices.columns),
        "pbo_summary": pbo_summary,
        "cpcv_summary": cpcv_summary,
        "weighting_comparisons": weighting_comparisons,
        "trial_inventory": tuple(inventory),
        "trial_family": trial_family,
        "multiple_testing": multiple_testing,
        "trial_inventory_path": inventory_path,
        "report_path": report_path,
        "experiment_log_path": experiment_log_path,
        "evidence_ceiling": "DIAGNOSTIC_ONLY",
        "readiness_decision": readiness,
        "evaluated_factor_ids": evaluated_ids,
        "alpha_ids": alpha_ids,
        "composite_ids": composite_ids,
        "ml_feature_importances": ml_feature_importances,
    }
    if write_outputs:
        write_real_data_report(result=result)
        write_real_data_experiment_log(result=result)
    return result


def _build_composites(
    *,
    composite_ids: tuple[str, ...],
    alpha_ids: tuple[str, ...],
    alpha_panels: dict[str, pd.DataFrame],
    ordered_alphas: list[pd.DataFrame],
    ic_history: pd.DataFrame,
    monthly_eval_dates: pd.DatetimeIndex,
    panels: dict[str, pd.DataFrame],
    prices: pd.DataFrame,
    forward_returns: pd.DataFrame,
    config: RealDataMultifactorDiagnosticConfig,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    if not composite_ids:
        return {}, {}
    if not ordered_alphas:
        raise ValueError("composites require at least one evaluated alpha")

    requested = set(composite_ids)
    need_interaction_parents = bool(
        requested & {ALPHA_PRODUCT_INTERACTION, CONDITIONAL_RANK_INTERACTION}
    )
    if need_interaction_parents and (
        ALPHA_016 not in alpha_ids or ALPHA_022 not in alpha_ids
    ):
        raise ValueError(
            "ALPHA_PRODUCT_INTERACTION and CONDITIONAL_RANK_INTERACTION require "
            "ALPHA_016 and ALPHA_022 in alpha_ids"
        )

    ic_comp = walk_forward_ic_weighted_composite(
        ordered_alphas,
        ic_history,
        monthly_eval_dates,
        execution_lag_periods=config.signal_lag_periods,
        forward_holding_periods=config.forward_holding_periods,
    )
    volatility_proxy = panels["returns"].rolling(20, min_periods=5).std()
    sector_map = build_default_sector_mapping(prices.columns)
    market_beta = compute_rolling_market_beta(panels["returns"], window=60, min_periods=20)
    beta_neutral_comp = cross_sectional_neutralize(ic_comp, market_beta)
    market_returns = panels["returns"].mean(axis=1)
    volatility_regime = detect_market_volatility_regime(
        market_returns, window=60, min_periods=20
    )
    regime_comp = regime_switching_factor_composite(
        ic_comp,
        beta_neutral_comp,
        volatility_regime,
        signal_lag_periods=config.signal_lag_periods,
    )

    available = {
        EQUAL_WEIGHTED_COMPOSITE: equal_weighted_composite(ordered_alphas),
        IC_WEIGHTED_COMPOSITE: ic_comp,
        ICIR_WEIGHTED_COMPOSITE: walk_forward_icir_weighted_composite(
            ordered_alphas,
            ic_history,
            monthly_eval_dates,
            execution_lag_periods=config.signal_lag_periods,
            forward_holding_periods=config.forward_holding_periods,
        ),
        CORRELATION_DISCOUNTED_COMPOSITE: walk_forward_correlation_discounted_composite(
            ordered_alphas,
            ic_history,
            monthly_eval_dates,
            ridge_alpha=config.ridge_alpha,
            execution_lag_periods=config.signal_lag_periods,
            forward_holding_periods=config.forward_holding_periods,
        ),
        NEUTRALIZED_IC_COMPOSITE: cross_sectional_neutralize(ic_comp, volatility_proxy),
        SECTOR_NEUTRAL_COMPOSITE: cross_sectional_group_neutralize(ic_comp, sector_map),
        MARKET_BETA_NEUTRAL_COMPOSITE: beta_neutral_comp,
        REGIME_SWITCHING_COMPOSITE: regime_comp,
    }
    if ALPHA_016 in alpha_panels and ALPHA_022 in alpha_panels:
        available[ALPHA_PRODUCT_INTERACTION] = factor_product_interaction(
            alpha_panels[ALPHA_016],
            alpha_panels[ALPHA_022],
        )
        available[CONDITIONAL_RANK_INTERACTION] = conditional_factor_rank(
            conditioning_factor=alpha_panels[ALPHA_016],
            target_factor=alpha_panels[ALPHA_022],
            n_bins=5,
        )

    ml_importances: dict[str, pd.DataFrame] = {}
    if RANDOM_FOREST_COMPOSITE in requested:
        rf_comp, rf_imp, _ = walk_forward_ml_factor_composite(
            ordered_alphas,
            forward_returns,
            monthly_eval_dates,
            factor_names=list(alpha_ids),
            model_type="random_forest",
            execution_lag_periods=config.signal_lag_periods,
            forward_holding_periods=config.forward_holding_periods,
            random_state=42,
        )
        available[RANDOM_FOREST_COMPOSITE] = rf_comp
        ml_importances[RANDOM_FOREST_COMPOSITE] = rf_imp

    if GRADIENT_BOOSTING_COMPOSITE in requested:
        gb_comp, gb_imp, _ = walk_forward_ml_factor_composite(
            ordered_alphas,
            forward_returns,
            monthly_eval_dates,
            factor_names=list(alpha_ids),
            model_type="gradient_boosting",
            execution_lag_periods=config.signal_lag_periods,
            forward_holding_periods=config.forward_holding_periods,
            random_state=42,
        )
        available[GRADIENT_BOOSTING_COMPOSITE] = gb_comp
        ml_importances[GRADIENT_BOOSTING_COMPOSITE] = gb_imp

    selected = {factor_id: available[factor_id] for factor_id in composite_ids}
    return selected, ml_importances


def write_real_data_experiment_log(*, result: dict[str, Any]) -> dict[str, object]:
    """Write a deterministic JSON log for the local EODHD diagnostic."""

    config: RealDataMultifactorDiagnosticConfig = result["config"]
    first_factor_id = result["alpha_ids"][0]
    first_backtest: BacktestResult = result["factors"][first_factor_id]["backtest"]
    factor_metrics = {
        factor_id: {
            **payload["ic_summary"],
            "dsr": payload["dsr"],
            **payload["backtest"].metrics,
            "long_short_metrics": payload["long_short_backtest"].metrics,
        }
        for factor_id, payload in result["factors"].items()
    }
    return write_experiment_log(
        log_path=result["experiment_log_path"],
        experiment_id="real-data-multifactor-diagnostic",
        title="Real-Data Blue-Chip Multi-Factor Diagnostic",
        experiment_type=REAL_DATA_MULTIFACTOR_EXPERIMENT_TYPE,
        summary=(
            "DIAGNOSTIC_ONLY static 50-stock blue-chip EODHD cohort plus SPY.US "
            "wired through the 52 implemented classical price-volume alphas and "
            "12 composites/interactions, with lag-1 execution, closed-window "
            "walk-forward IC and ML weights, frozen smoothing targets, netted gross "
            "exposure, solvency guards, across-trial Sharpe variance for DSR, "
            "trial inventory logging, portfolio-weighting comparisons, and PBO."
        ),
        config={
            "data_dir": redact_local_path(config.data_dir),
            "inventory_path": redact_local_path(config.inventory_path),
            "start_date": config.start_date,
            "end_date": config.end_date,
            "symbols": list(result["factor_symbols"]),
            "benchmark_symbol": config.benchmark_symbol,
            "rebalance_frequency": config.rebalance_frequency,
            "top_n": config.top_n,
            "transaction_cost_bps": config.transaction_cost_bps,
            "slippage_bps": config.slippage_bps,
            "signal_lag_periods": config.signal_lag_periods,
            "periods_per_year": config.periods_per_year,
            "n_trials": result["trial_family"]["n_trials_for_dsr"],
            "forward_holding_periods": config.forward_holding_periods,
            "warmup_periods": config.warmup_periods,
            "ic_weights": result["ic_weights"],
            "quantiles": config.quantiles,
            "ridge_alpha": config.ridge_alpha,
            "alpha_ids": list(result["alpha_ids"]),
            "composite_ids": list(result["composite_ids"]),
            "include_weighting_comparisons": config.include_weighting_comparisons,
            "pbo_n_splits": config.pbo_n_splits,
            "pbo_holding_periods": config.pbo_holding_periods,
            "pbo_embargo_periods": config.pbo_embargo_periods,
        },
        assumptions={
            "data_scope": "local EODHD Parquet diagnostic",
            "data_source": (
                "user-provided local EODHD daily Parquet snapshot; no remote fetch"
            ),
            "evidence_ceiling": result["evidence_ceiling"],
            "readiness_decision": result["readiness_decision"],
            "dataset_manifest_reviewed": False,
            "formal_interpretation_eligible": False,
            "universe": "static 50-stock liquid blue-chip diagnostic cohort",
            "survivorship_bias": True,
            "not_point_in_time_universe_evidence": True,
            "protected_sample_classification": "historical_evaluation",
            "date_range": {
                "start": result["evaluation_start"].date(),
                "end": result["evaluation_end"].date(),
            },
            "source_date_range": {
                "start": result["prices"].index.min().date(),
                "end": result["prices"].index.max().date(),
            },
            "price_basis": (
                "split-adjusted OHLC and volume matching true dollar volume; "
                "vendor adjusted_close for total return"
            ),
            "feature_timing": (
                "implemented alphas use only open, high, low, close, vwap, "
                "volume, and returns on or before the signal date; "
                "signal_lag_periods=1 delays portfolio formation"
            ),
            "execution_timing": first_backtest.assumptions["execution_timing"],
            "rebalance_frequency": config.rebalance_frequency,
            "selected_assets_per_rebalance": config.top_n,
            "benchmark": f"{config.benchmark_symbol} vendor adjusted close",
            "transaction_cost_model": (
                f"{first_backtest.assumptions['cost_model']}; "
                f"{config.transaction_cost_bps:.2f} bps per unit of drift-adjusted "
                "target-weight turnover on post-return portfolio value"
            ),
            "transaction_cost_bps": config.transaction_cost_bps,
            "slippage_model": (
                f"{first_backtest.assumptions['slippage_model']}; "
                f"{config.slippage_bps:.2f} bps per unit of drift-adjusted "
                "target-weight turnover on post-return portfolio value"
            ),
            "slippage_bps": config.slippage_bps,
            "zero_cost_or_slippage_is_diagnostic": first_backtest.assumptions[
                "zero_cost_or_slippage_is_diagnostic"
            ],
            "n_trials_for_dsr": result["trial_family"]["n_trials_for_dsr"],
            "trial_family": result["trial_family"],
            "dsr_expected_max_mix": "euler_mascheroni",
            "cash_dividend_overlay": "refused; vendor adjusted_close is the return basis",
            "composite_ic_weights": (
                "expanding mean monthly Rank IC from fully realized windows of the "
                "evaluated alphas"
            ),
            "composite_walk_forward_weights": (
                "ICIR-weighted and correlation-discounted composites refresh "
                "weights on each monthly rebalance date t using monthly Rank "
                "ICs labeled strictly before t whose execution-aligned "
                "forward-return windows have closed by t "
                "(source_row(s) + signal_lag_periods + forward_holding_periods "
                "<= source_row(t)); correlation-discounted also uses trailing "
                "factor-value correlation through t"
            ),
            "volatility_proxy": (
                "20-day rolling return standard deviation with min_periods=5; "
                "leading dates without a full minimum window remain NaN"
            ),
            "sector_map": "5 balanced cohorts across the loaded assets",
            "market_beta_proxy": (
                "60-day rolling return beta against equal-weighted market return "
                "with min_periods=20; leading dates without a full minimum window remain NaN"
            ),
            "volatility_regime_proxy": (
                "60-day rolling return volatility against expanding historical median "
                "with min_periods=20; zero lookahead; composite applies signal_lag_periods=1 "
                "(regime.shift(1))"
            ),
            "vwap_definition": (
                "typical price (high + low + close) / 3 on split-adjusted bars"
            ),
            "live_trading": False,
            "brokerage_integration": False,
            "long_short_dollar_neutral": True,
            "long_short_quantiles": config.quantiles,
            "weighting_scheme": config.weighting_scheme,
            "long_short_weighting_scheme": config.long_short_weighting_scheme,
            "turnover_penalty_lambda": config.turnover_penalty_lambda,
            "volatility_window": config.volatility_window,
        },
        outputs={
            "markdown_report": _tracked_output_path(result["report_path"]),
            "experiment_log": _tracked_output_path(result["experiment_log_path"]),
            "trial_attempt_events": _tracked_output_path(result["trial_inventory_path"]),
        },
        metrics={
            **factor_metrics,
            "multiple_testing": result["multiple_testing"],
            "pbo_summary": result["pbo_summary"],
            "cpcv_summary": result.get("cpcv_summary"),
            "weighting_comparisons": result.get("weighting_comparisons", []),
            "trial_inventory": [
                {key: value for key, value in record.items() if key != "attempt_id"}
                for record in result["trial_inventory"]
            ],
        },
        caveats=(
            *DIAGNOSTIC_REAL_DATA_CAVEATS,
            "not a 14-trial campaign run",
            "not evidence of real-world strategy performance",
            "IC-weighted composite uses causal expanding mean monthly Rank IC weights",
            "ICIR-weighted and correlation-discounted composites use causal "
            "walk-forward weights at monthly rebalance dates, admitting an IC "
            "labeled at s only when its execution-aligned forward-return "
            "window has closed by t",
            "random-forest and gradient-boosting ML composites use causal "
            "walk-forward training windows at monthly rebalance dates, admitting an "
            "observation labeled at s only when its execution-aligned forward-return "
            "window has closed by t; predictions are held on [t, next_t)",
            "CPCV cross-validation on one-period strategy P&L purges training samples overlapping with the 21-bar forward-return window and applies a 5-bar post-test embargo",
            "volatility proxy does not backfill leading rolling-standard-deviation NaNs",
            "sector map uses static balanced cohorts, not GICS point-in-time sectors",
            "market beta proxy does not backfill leading rolling-beta NaNs",
            "regime-switching composite switches between IC-weighted and market-beta-neutral composites based on causal trailing 60-day volatility regime with signal_lag_periods=1 execution (regime.shift(1)); leading NaN regime defaults to IC-weighted composite",
            "inverse-volatility weighting applies lagged 20-day return volatility (shift 1 source row)",
            "turnover penalization (lambda=0.5) blends previous frozen targets with fresh decision-time targets; final eligibility and net exposure constraints apply",
            "the 2025-05-01 through 2026-05-31 interval remains historical_evaluation",
        ),
        required_caveats=DIAGNOSTIC_REAL_DATA_CAVEATS,
        next_action=(
            "Keep this as a DIAGNOSTIC_ONLY real-data pipeline check. It does not "
            "grant RESEARCH_PASS, formal interpretation, or profitability."
        ),
    )


def write_real_data_report(*, result: dict[str, Any]) -> None:
    """Write human-readable markdown for the local EODHD diagnostic."""

    config: RealDataMultifactorDiagnosticConfig = result["config"]
    report_path = Path(result["report_path"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    first_factor_id = result["alpha_ids"][0]
    first_backtest: BacktestResult = result["factors"][first_factor_id]["backtest"]
    pbo_summary = result["pbo_summary"]
    cpcv_summary = result.get("cpcv_summary")
    horizon_contract = (
        f"source_row(s) + {config.signal_lag_periods} + "
        f"{config.forward_holding_periods} <= source_row(t)"
    )
    evaluated_ids = result["evaluated_factor_ids"]
    rows = []
    ls_rows = []
    for factor_id in evaluated_ids:
        payload = result["factors"][factor_id]
        ic_summary = payload["ic_summary"]
        metrics = payload["backtest"].metrics
        ls_metrics = payload["long_short_backtest"].metrics
        rows.append(
            "| "
            + " | ".join(
                [
                    factor_id,
                    _format_number(ic_summary["mean_ic"]),
                    _format_number(
                        ic_summary["icIR"]
                        if "icIR" in ic_summary
                        else ic_summary["icir"]
                    ),
                    _format_number(ic_summary["newey_west_tstat"]),
                    _format_number(payload["dsr"]),
                    _format_percent(metrics["total_return"]),
                    _format_number(metrics["sharpe_ratio"]),
                    _format_percent(metrics["max_drawdown"]),
                    _format_number(metrics.get("average_turnover", np.nan)),
                    _format_number(metrics.get("total_slippage_cost_impact", np.nan)),
                ]
            )
            + " |"
        )
        ls_rows.append(
            "| "
            + " | ".join(
                [
                    factor_id,
                    _format_number(ls_metrics["sharpe"]),
                    _format_percent(ls_metrics["annualized_return"]),
                    _format_percent(ls_metrics["max_drawdown"]),
                    _format_percent(ls_metrics["win_rate"]),
                    _format_number(ls_metrics["decile_spread_mean"]),
                    _format_number(ls_metrics["monotonicity_spearman"]),
                    _format_number(ls_metrics["total_turnover"]),
                ]
            )
            + " |"
        )
    weight_rows = [
        f"| {factor_id} | {_format_number(result['ic_weights'][factor_id])} |"
        for factor_id in result["alpha_ids"]
    ]
    comp_rows = []
    for record in result.get("weighting_comparisons", []):
        comp_rows.append(
            "| "
            + " | ".join(
                [
                    str(record["factor_id"]),
                    str(record["scheme"]),
                    _format_number(record["lo_sharpe"]),
                    _format_number(record["lo_turnover"]),
                    _format_percent(record["lo_total_return"]),
                    _format_percent(record["lo_max_drawdown"]),
                    _format_number(record["ls_sharpe"]),
                    _format_number(record["ls_turnover"]),
                    _format_percent(record["ls_annualized_return"]),
                    _format_percent(record["ls_max_drawdown"]),
                ]
            )
            + " |"
        )
    if not comp_rows:
        comp_rows = ["| (none) |  |  |  |  |  |  |  |  |  |"]

    ml_section = ""
    ml_importances = result.get("ml_feature_importances", {})
    if ml_importances:
        ml_table_rows = []
        for comp_name, imp_frame in ml_importances.items():
            if imp_frame is not None and not imp_frame.empty:
                mean_s = imp_frame.mean(axis=0).sort_values(ascending=False)
                top_3 = [f"`{idx}` ({val:.1%})" for idx, val in mean_s.head(3).items()]
                ml_table_rows.append(f"| `{comp_name}` | {', '.join(top_3)} | {len(imp_frame)} |")
        if ml_table_rows:
            ml_section = f"""
## Machine learning factor combinations and feature importances

Walk-forward non-linear factor combinations (Random Forest, Gradient Boosting)
learn empirical mappings from the classical alphas to forward returns using
expanding training windows with strictly closed forward-return labels (zero lookahead).

| composite | top features (mean importance) | evaluated rebalance count |
| --- | --- | --- |
{chr(10).join(ml_table_rows)}
"""

    cpcv_section = ""
    if cpcv_summary:
        cpcv_section = f"""
### Combinatorial Purged Cross-Validation (CPCV)

CPCV evaluates backtest overfitting on the one-period strategy return series with a declared 21-bar forward-dependence horizon and 5-bar post-test embargo window.

- Purged & Embargoed PBO: `{_format_number(cpcv_summary["pbo"])}`
- Out-of-Sample Probability of Loss: `{_format_number(cpcv_summary["prob_loss"])}`
- Combinations: `{cpcv_summary["n_combinations"]}` (from `{cpcv_summary["n_splits"]}` splits)
- Forward Holding Horizon: `{cpcv_summary["holding_periods"]}` bars
- Post-Test Embargo Window: `{cpcv_summary["embargo_periods"]}` bars
- Mean Purged Samples per Split: `{_format_number(cpcv_summary["mean_purged_samples"])}`
- Mean Embargoed Samples per Split: `{_format_number(cpcv_summary["mean_embargoed_samples"])}`
- Mean OOS Relative Rank: `{_format_number(cpcv_summary["mean_relative_rank"])}`
- Median OOS Relative Rank: `{_format_number(cpcv_summary["median_relative_rank"])}`
- Mean IS Sharpe: `{_format_number(cpcv_summary["mean_is_sharpe"])}`
- Mean OOS Sharpe: `{_format_number(cpcv_summary["mean_oos_sharpe"])}`
"""

    alpha_names = ", ".join(f"`{factor_id}`" for factor_id in result["alpha_ids"])
    composite_names = ", ".join(f"`{factor_id}`" for factor_id in result["composite_ids"])
    n_alphas = len(result["alpha_ids"])
    n_assets = len(result["factor_symbols"])
    content = f"""# Real-Data Blue-Chip Multi-Factor Diagnostic

This report is `DIAGNOSTIC_ONLY`. It uses a static 50-stock liquid blue-chip
cohort from a local EODHD daily Parquet snapshot plus `{config.benchmark_symbol}`
as the accounting benchmark. The cohort is survivorship-biased. It is not
point-in-time universe evidence, not a dataset-review decision, and not a
14-trial campaign run. Metrics are workflow diagnostics only and are not
evidence of real-world strategy profitability.

## Evidence ceiling

- Evidence ceiling: `{result["evidence_ceiling"]}`
- Readiness decision: `{result["readiness_decision"]}`
- `dataset_manifest_reviewed`: `false`
- `formal_interpretation_eligible`: `false`
- Survivorship bias: `true`
- Not point-in-time universe evidence: `true`
- Protected-sample classification: `historical_evaluation`
- Cohort: static `BLUECHIP_50_COHORT` ({n_assets} names in this run)
- Benchmark: `{config.benchmark_symbol}` vendor adjusted close

## Pipeline

1. Load local EODHD Parquet files for the requested symbols and
   `{config.benchmark_symbol}` through `load_eod_cohort_panels`.
2. Convert vendor bars to research panels: OHLC and volume are split-adjusted
   so dollar volume stays on an exact matching price/volume basis (identically
   matching unadjusted close * raw volume); vendor adjusted_close is retained
   for total-return calculations; VWAP is typical price on the split-adjusted bars.
   Missing cells stay missing.
3. Compute classical price-volume alphas {alpha_names}.
4. Build composites {composite_names} using the same M01-M11 causal parents as
   the synthetic multifactor diagnostic: closed-window walk-forward IC weights,
   lag-1 execution, frozen decision-time smoothing targets, netted gross
   exposure, and solvency guards.
5. Measure monthly Spearman Rank IC versus 21-source-row forward returns that
   start at the lag-1 execution close.
6. Run the existing long-only monthly backtester with `{config.slippage_bps:.2f}`
   bps slippage and `{config.top_n}` names, using `{config.benchmark_symbol}` as
   the accounting benchmark.
7. Run dollar-neutral long-short quantile spread backtests.
8. Compute DSR with Euler-Mascheroni mix and across-trial Sharpe variance, and
   PBO across the evaluated alphas.

## Configuration

- Data directory: `{redact_local_path(config.data_dir)}`
- Inventory: `{redact_local_path(config.inventory_path)}`
- Requested source window: `{config.start_date}` to `{config.end_date}`
- Asset count: `{n_assets}`
- Source date range: `{result["prices"].index.min().date()}` to `{result["prices"].index.max().date()}`
- Source rows: `{len(result["prices"].index)}`
- Evaluation date range: `{result["evaluation_start"].date()}` to `{result["evaluation_end"].date()}`
- Rebalance frequency: `{config.rebalance_frequency}`
- Selected assets per rebalance: `{config.top_n}`
- Signal lag: `{config.signal_lag_periods}` source row
- Execution timing: `{first_backtest.assumptions["execution_timing"]}`
- Transaction cost: `{config.transaction_cost_bps:.2f}` bps
- Slippage: `{config.slippage_bps:.2f}` bps
- Zero cost or slippage diagnostic: `{first_backtest.assumptions["zero_cost_or_slippage_is_diagnostic"]}`
- Benchmark: `{config.benchmark_symbol}` vendor adjusted close
- Timing contract: `{first_backtest.timing_metadata["timing_contract"]}`
- DSR expected-maximum mix: Euler-Mascheroni constant `np.euler_gamma`
- PBO splits: `{config.pbo_n_splits}`
- VWAP: typical price `(high + low + close) / 3` on split-adjusted bars
- Composite IC weights: causal expanding mean monthly Rank IC of the {n_alphas} evaluated alphas
- Walk-forward ICIR and correlation weights: expanding window at each monthly rebalance; monthly ICs labeled strictly before t whose execution-aligned forward-return windows have closed by t (`{horizon_contract}`)
- Volatility proxy: 20-day rolling return standard deviation, min_periods=5, no backfill
- Sector map: 5 balanced diagnostic cohorts across the loaded assets
- Market beta proxy: 60-day rolling return beta against equal-weighted market return, min_periods=20, no backfill
- Volatility regime proxy: 60-day rolling return volatility against expanding historical median, min_periods=20, no lookahead
- Long-short quantiles: `{config.quantiles}`
- Long-only weighting scheme: `{config.weighting_scheme}`
- Long-short weighting scheme: `{config.long_short_weighting_scheme}`
- Turnover penalty lambda: `{config.turnover_penalty_lambda:.2f}`
- Volatility window: `{config.volatility_window}`
- Cash-dividend overlay: refused (PIT-007); vendor adjusted close is the return basis

## In-sample IC summaries (descriptive only)

| factor | mean monthly Rank IC |
| --- | --- |
{chr(10).join(weight_rows)}

This table retains full-sample descriptive IC summaries. Executable IC,
ICIR, correlation, neutralized, and regime composites use causal walk-forward
parents. An IC labeled at s enters the information set at t when its
execution-aligned forward-return window has closed by t.

## Factor diagnostics

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown | average turnover | slippage cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

IC is monthly Spearman Rank IC. ICIR is not annualized. DSR is computed on
non-annualized daily measured returns using the Bailey-Lopez de Prado formula
with the Euler-Mascheroni mix and across-trial Sharpe variance
`{result["trial_family"]["trial_sharpe_variance"]}`. This run evaluated
{result["trial_family"]["attempt_count"]} books and
{result["trial_family"]["distinct_trial_count"]} distinct configurations across
factors, weighting, penalties, and both directions. Reproductions share a
semantic trial ID; append-only attempt events retain failures and repeated runs.
DSR uses the raw distinct count as an independent-trial upper-bound sensitivity.
Effective independence and total historical search remain unestimated. Missing
trial Sharpe dispersion withholds DSR. PBO covers the alpha-only long-only
family. Weak or negative diagnostics are retained.

{render_multiple_testing(result["multiple_testing"])}

## Long-short quantile spread diagnostics

Long-short quantile spread backtests construct a dollar-neutral portfolio long the top quantile
and short the bottom quantile at monthly rebalance frequency with {config.slippage_bps:.2f} bps slippage.

Column groups in the table below:

- Sequential holding-period book metrics: `LS Sharpe`, `LS Ann Return`, `Max DD`, `Win Rate`. These use the lag-1 dollar-neutral long-short book return on every accounting date after the first bar.
- Rebalance-date one-day bucket diagnostics: `Decile Spread Mean`, `Monotonicity`. These use equal-weight quantile returns on month-end rebalance dates only.
- `Total Turnover` is the sequential book's cumulative absolute trade-weight change.

| factor | LS Sharpe | LS Ann Return | Max DD | Win Rate | Decile Spread Mean | Monotonicity | Total Turnover |
| --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(ls_rows)}

`LS Sharpe`, `LS Ann Return`, `Max DD`, and `Win Rate` summarize the sequential holding-period book. `Decile Spread Mean` is the mean top-minus-bottom quantile return on rebalance dates. Monotonicity is the Spearman rank correlation of mean rebalance-date returns across quantiles.

## Portfolio weighting and turnover penalization diagnostics

Comparison of weighting schemes and turnover penalty (λ) across key multi-factor composites:

| factor | scheme | LO Sharpe | LO Turnover | LO Return | LO Max DD | LS Sharpe | LS Turnover | LS Ann Return | LS Max DD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(comp_rows)}

Inverse-volatility weighting applies lagged 20-day return volatility (shift 1 source row). Turnover penalization (λ=0.5) blends previous frozen targets with fresh decision-time targets; final eligibility and net exposure constraints apply.

## Overfitting diagnostics (CSCV / PBO)

### Classical CSCV (unpurged)

- Probability of Backtest Overfitting (PBO): `{_format_number(pbo_summary["pbo"])}`
- Out-of-Sample Probability of Loss: `{_format_number(pbo_summary["prob_loss"])}`
- Combinations: `{pbo_summary["n_combinations"]}` (from `{pbo_summary["n_splits"]}` splits)
- Mean OOS Relative Rank: `{_format_number(pbo_summary["mean_relative_rank"])}`
- Median OOS Relative Rank: `{_format_number(pbo_summary["median_relative_rank"])}`
- Mean IS Sharpe: `{_format_number(pbo_summary["mean_is_sharpe"])}`
- Mean OOS Sharpe: `{_format_number(pbo_summary["mean_oos_sharpe"])}`
{cpcv_section}
{ml_section}
## Limitations

- Local EODHD files only; no vendor API, credentials, or remote fetch.
- Static 50-name membership is survivorship-biased by construction.
- Vendor adjusted close is the research return basis. Event-level dividend and
  split reconciliation against an independent event table was not performed.
- A separate cash-dividend overlay is refused (PIT-007).
- VWAP is a typical-price proxy, not a traded volume-weighted average price.
- Close-only lag-1 execution is idealized research accounting, not brokerage.
- 5 bps slippage is a fixed diagnostic assumption, not a market-impact model.
- Sector map uses static balanced cohorts, not GICS point-in-time sectors.
- The 2025-05-01 through 2026-05-31 interval remains `historical_evaluation`.
- This does not execute, replace, or reopen the refused 14-trial run.
- This does not grant `RESEARCH_PASS`, formal interpretation, or profitability.
"""
    report_path.write_text(content, encoding="utf-8")


def _unique_symbols(symbols: Sequence[str], *, field_name: str) -> tuple[str, ...]:
    if not symbols:
        raise ValueError(f"{field_name} must be a nonempty sequence")
    cleaned: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError(f"{field_name} must contain nonempty strings")
        name = symbol.strip()
        if name in seen:
            raise ValueError(f"{field_name} must be unique: {name}")
        seen.add(name)
        cleaned.append(name)
    return tuple(cleaned)


def _validate_id_subset(
    values: Sequence[str],
    allowed: Sequence[str],
    *,
    field_name: str,
) -> tuple[str, ...]:
    if not values:
        raise ValueError(f"{field_name} must be a nonempty sequence")
    allowed_set = set(allowed)
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in allowed_set:
            raise ValueError(f"unknown {field_name[:-1]}: {value}")
        if value in seen:
            raise ValueError(f"{field_name} must be unique: {value}")
        seen.add(value)
        cleaned.append(value)
    return tuple(cleaned)


def _tracked_output_path(path: Path | str | None) -> str:
    if path is None:
        return REDACTED_LOCAL_PATH
    try:
        return Path(path).resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return redact_local_path(path)


def main(
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
) -> None:
    """Run the local EODHD diagnostic with default settings."""

    run_real_data_multifactor_diagnostic(
        report_path=report_path,
        experiment_log_path=experiment_log_path,
    )


if __name__ == "__main__":
    main()
