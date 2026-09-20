"""End-to-end WorldQuant alpha and multi-factor diagnostic pipeline.

This module wires the 52 implemented classical price-volume alphas plus
equal-weighted, in-sample IC-weighted, and causal walk-forward ICIR-weighted
and correlation-discounted composites through the committed 50-stock static
diagnostic cohort, a small IC/ICIR/Newey-West/DSR summary, and the existing
equal-weight monthly long-only backtester with 5 bps slippage.

It is DIAGNOSTIC_ONLY. The static cohort is not point-in-time universe
evidence. Outputs are not profitability, strategy validation, or a 14-trial
campaign run.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest.long_short import (
    run_long_short_backtest,
)
from backtest.portfolio import (
    BacktestResult,
    capture_backtest_source_provenance,
    run_long_only_backtest,
)
from data.diagnostic_cohort import load_diagnostic_cohort_ohlcv
from features.alphas import (
    alpha_001,
    alpha_002,
    alpha_003,
    alpha_004,
    alpha_005,
    alpha_006,
    alpha_007,
    alpha_008,
    alpha_009,
    alpha_010,
    alpha_012,
    alpha_013,
    alpha_014,
    alpha_015,
    alpha_016,
    alpha_017,
    alpha_018,
    alpha_019,
    alpha_020,
    alpha_021,
    alpha_022,
    alpha_023,
    alpha_024,
    alpha_025,
    alpha_026,
    alpha_028,
    alpha_030,
    alpha_031,
    alpha_032,
    alpha_033,
    alpha_034,
    alpha_035,
    alpha_036,
    alpha_037,
    alpha_038,
    alpha_039,
    alpha_040,
    alpha_041,
    alpha_042,
    alpha_043,
    alpha_044,
    alpha_045,
    alpha_046,
    alpha_049,
    alpha_050,
    alpha_051,
    alpha_052,
    alpha_053,
    alpha_054,
    alpha_055,
    alpha_060,
    alpha_101,
)
from features.combination import (
    equal_weighted_composite,
    ic_weighted_composite,
    walk_forward_correlation_discounted_composite,
    walk_forward_icir_weighted_composite,
)
from features.diagnostics import (
    deflated_sharpe_ratio,
    factor_rank_information_coefficient,
    information_coefficient_summary,
    probability_of_backtest_overfitting,
)
from features.interaction import (
    conditional_factor_rank,
    factor_product_interaction,
)
from features.neutralize import (
    cross_sectional_group_neutralize,
    cross_sectional_neutralize,
)
from reporting.experiment_log import (
    SYNTHETIC_RESEARCH_CAVEATS,
    resolve_experiment_log_path,
    write_experiment_log,
)
from reporting.experiment_registry import write_experiment_registry_report
from research.walking_skeleton_mvp import (
    FORWARD_HOLDING_PERIODS,
    build_equal_weight_benchmark,
    execution_aligned_forward_returns,
    month_end_dates,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "walking_skeleton" / "diagnostic_cohort_v1.json"
)
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "multifactor_diagnostic_mvp.md"
DEFAULT_EXPERIMENT_LOG_PATH = (
    PROJECT_ROOT / "reports" / "experiment_logs" / "multifactor_diagnostic_mvp.json"
)

ALPHA_001 = "ALPHA_001"
ALPHA_002 = "ALPHA_002"
ALPHA_003 = "ALPHA_003"
ALPHA_004 = "ALPHA_004"
ALPHA_005 = "ALPHA_005"
ALPHA_006 = "ALPHA_006"
ALPHA_007 = "ALPHA_007"
ALPHA_008 = "ALPHA_008"
ALPHA_009 = "ALPHA_009"
ALPHA_010 = "ALPHA_010"
ALPHA_012 = "ALPHA_012"
ALPHA_013 = "ALPHA_013"
ALPHA_014 = "ALPHA_014"
ALPHA_015 = "ALPHA_015"
ALPHA_016 = "ALPHA_016"
ALPHA_017 = "ALPHA_017"
ALPHA_018 = "ALPHA_018"
ALPHA_019 = "ALPHA_019"
ALPHA_020 = "ALPHA_020"
ALPHA_021 = "ALPHA_021"
ALPHA_022 = "ALPHA_022"
ALPHA_023 = "ALPHA_023"
ALPHA_024 = "ALPHA_024"
ALPHA_025 = "ALPHA_025"
ALPHA_026 = "ALPHA_026"
ALPHA_028 = "ALPHA_028"
ALPHA_030 = "ALPHA_030"
ALPHA_031 = "ALPHA_031"
ALPHA_032 = "ALPHA_032"
ALPHA_033 = "ALPHA_033"
ALPHA_034 = "ALPHA_034"
ALPHA_035 = "ALPHA_035"
ALPHA_036 = "ALPHA_036"
ALPHA_037 = "ALPHA_037"
ALPHA_038 = "ALPHA_038"
ALPHA_039 = "ALPHA_039"
ALPHA_040 = "ALPHA_040"
ALPHA_041 = "ALPHA_041"
ALPHA_042 = "ALPHA_042"
ALPHA_043 = "ALPHA_043"
ALPHA_044 = "ALPHA_044"
ALPHA_045 = "ALPHA_045"
ALPHA_046 = "ALPHA_046"
ALPHA_049 = "ALPHA_049"
ALPHA_050 = "ALPHA_050"
ALPHA_051 = "ALPHA_051"
ALPHA_052 = "ALPHA_052"
ALPHA_053 = "ALPHA_053"
ALPHA_054 = "ALPHA_054"
ALPHA_055 = "ALPHA_055"
ALPHA_060 = "ALPHA_060"
ALPHA_101 = "ALPHA_101"
EQUAL_WEIGHTED_COMPOSITE = "EQUAL_WEIGHTED_COMPOSITE"
IC_WEIGHTED_COMPOSITE = "IC_WEIGHTED_COMPOSITE"
ICIR_WEIGHTED_COMPOSITE = "ICIR_WEIGHTED_COMPOSITE"
CORRELATION_DISCOUNTED_COMPOSITE = "CORRELATION_DISCOUNTED_COMPOSITE"
ALPHA_PRODUCT_INTERACTION = "ALPHA_PRODUCT_INTERACTION"
CONDITIONAL_RANK_INTERACTION = "CONDITIONAL_RANK_INTERACTION"
NEUTRALIZED_IC_COMPOSITE = "NEUTRALIZED_IC_COMPOSITE"
SECTOR_NEUTRAL_COMPOSITE = "SECTOR_NEUTRAL_COMPOSITE"
MARKET_BETA_NEUTRAL_COMPOSITE = "MARKET_BETA_NEUTRAL_COMPOSITE"
ALPHA_IDS = (
    ALPHA_001,
    ALPHA_002,
    ALPHA_003,
    ALPHA_004,
    ALPHA_005,
    ALPHA_006,
    ALPHA_007,
    ALPHA_008,
    ALPHA_009,
    ALPHA_010,
    ALPHA_012,
    ALPHA_013,
    ALPHA_014,
    ALPHA_015,
    ALPHA_016,
    ALPHA_017,
    ALPHA_018,
    ALPHA_019,
    ALPHA_020,
    ALPHA_021,
    ALPHA_022,
    ALPHA_023,
    ALPHA_024,
    ALPHA_025,
    ALPHA_026,
    ALPHA_028,
    ALPHA_030,
    ALPHA_031,
    ALPHA_032,
    ALPHA_033,
    ALPHA_034,
    ALPHA_035,
    ALPHA_036,
    ALPHA_037,
    ALPHA_038,
    ALPHA_039,
    ALPHA_040,
    ALPHA_041,
    ALPHA_042,
    ALPHA_043,
    ALPHA_044,
    ALPHA_045,
    ALPHA_046,
    ALPHA_049,
    ALPHA_050,
    ALPHA_051,
    ALPHA_052,
    ALPHA_053,
    ALPHA_054,
    ALPHA_055,
    ALPHA_060,
    ALPHA_101,
)
FACTOR_IDS = (
    *ALPHA_IDS,
    EQUAL_WEIGHTED_COMPOSITE,
    IC_WEIGHTED_COMPOSITE,
    ICIR_WEIGHTED_COMPOSITE,
    CORRELATION_DISCOUNTED_COMPOSITE,
    ALPHA_PRODUCT_INTERACTION,
    CONDITIONAL_RANK_INTERACTION,
    NEUTRALIZED_IC_COMPOSITE,
    SECTOR_NEUTRAL_COMPOSITE,
    MARKET_BETA_NEUTRAL_COMPOSITE,
)
ALPHA_WARMUP_PERIODS = 25
IMPLEMENTED_ALPHA_COUNT = len(ALPHA_IDS)


WEIGHTING_COMPARISON_FACTORS = (
    IC_WEIGHTED_COMPOSITE,
    MARKET_BETA_NEUTRAL_COMPOSITE,
    SECTOR_NEUTRAL_COMPOSITE,
    EQUAL_WEIGHTED_COMPOSITE,
)

WEIGHTING_COMPARISON_SCHEMES = (
    {"name": "Equal (λ=0.0)", "weighting_scheme": "equal", "turnover_penalty_lambda": 0.0},
    {"name": "Inverse-Vol (λ=0.0)", "weighting_scheme": "inverse_volatility", "turnover_penalty_lambda": 0.0},
    {"name": "Equal (λ=0.5)", "weighting_scheme": "equal", "turnover_penalty_lambda": 0.5},
    {"name": "Inverse-Vol (λ=0.5)", "weighting_scheme": "inverse_volatility", "turnover_penalty_lambda": 0.5},
)


@dataclass(frozen=True)
class MultifactorDiagnosticConfig:
    """Frozen diagnostic settings for the implemented-alpha pipeline."""

    manifest_path: Path = DEFAULT_MANIFEST_PATH
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
    n_trials: int = 61
    forward_holding_periods: int = FORWARD_HOLDING_PERIODS
    warmup_periods: int = ALPHA_WARMUP_PERIODS
    pbo_n_splits: int = 8
    quantiles: int = 10
    ridge_alpha: float = 0.1


def calculate_diagnostic_alpha(
    factor_id: str,
    panels: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Compute one implemented price-volume alpha on companion OHLCV panels."""

    if factor_id == ALPHA_001:
        return alpha_001(panels["close"], panels["returns"])
    if factor_id == ALPHA_002:
        return alpha_002(panels["open"], panels["close"], panels["volume"])
    if factor_id == ALPHA_003:
        return alpha_003(panels["open"], panels["volume"])
    if factor_id == ALPHA_004:
        return alpha_004(panels["low"])
    if factor_id == ALPHA_005:
        return alpha_005(panels["open"], panels["close"], panels["vwap"])
    if factor_id == ALPHA_006:
        return alpha_006(panels["open"], panels["volume"])
    if factor_id == ALPHA_007:
        return alpha_007(panels["close"], panels["volume"])
    if factor_id == ALPHA_008:
        return alpha_008(panels["open"], panels["returns"])
    if factor_id == ALPHA_009:
        return alpha_009(panels["close"])
    if factor_id == ALPHA_010:
        return alpha_010(panels["close"])
    if factor_id == ALPHA_012:
        return alpha_012(panels["close"], panels["volume"])
    if factor_id == ALPHA_013:
        return alpha_013(panels["close"], panels["volume"])
    if factor_id == ALPHA_014:
        return alpha_014(panels["open"], panels["volume"], panels["returns"])
    if factor_id == ALPHA_015:
        return alpha_015(panels["high"], panels["volume"])
    if factor_id == ALPHA_016:
        return alpha_016(panels["high"], panels["volume"])
    if factor_id == ALPHA_017:
        return alpha_017(panels["close"], panels["volume"])
    if factor_id == ALPHA_018:
        return alpha_018(panels["open"], panels["close"])
    if factor_id == ALPHA_019:
        return alpha_019(panels["close"], panels["returns"])
    if factor_id == ALPHA_020:
        return alpha_020(panels["open"], panels["high"], panels["low"], panels["close"])
    if factor_id == ALPHA_021:
        return alpha_021(panels["close"], panels["volume"])
    if factor_id == ALPHA_022:
        return alpha_022(panels["high"], panels["volume"], panels["close"])
    if factor_id == ALPHA_023:
        return alpha_023(panels["high"])
    if factor_id == ALPHA_024:
        return alpha_024(panels["close"])
    if factor_id == ALPHA_025:
        return alpha_025(
            panels["high"],
            panels["close"],
            panels["returns"],
            panels["volume"],
            panels["vwap"],
        )
    if factor_id == ALPHA_026:
        return alpha_026(panels["high"], panels["volume"])
    if factor_id == ALPHA_028:
        return alpha_028(
            panels["close"],
            panels["high"],
            panels["low"],
            panels["volume"],
        )
    if factor_id == ALPHA_030:
        return alpha_030(panels["close"], panels["volume"])
    if factor_id == ALPHA_031:
        return alpha_031(panels["close"], panels["volume"])
    if factor_id == ALPHA_032:
        return alpha_032(panels["close"], panels["vwap"])
    if factor_id == ALPHA_033:
        return alpha_033(panels["open"], panels["close"])
    if factor_id == ALPHA_034:
        return alpha_034(panels["close"], panels["returns"])
    if factor_id == ALPHA_035:
        return alpha_035(
            panels["high"],
            panels["low"],
            panels["close"],
            panels["volume"],
            panels["returns"],
        )
    if factor_id == ALPHA_036:
        return alpha_036(
            panels["open"],
            panels["close"],
            panels["volume"],
            panels["returns"],
            panels["vwap"],
        )
    if factor_id == ALPHA_037:
        return alpha_037(panels["open"], panels["close"])
    if factor_id == ALPHA_038:
        return alpha_038(panels["open"], panels["close"])
    if factor_id == ALPHA_039:
        return alpha_039(panels["close"], panels["volume"], panels["returns"])
    if factor_id == ALPHA_040:
        return alpha_040(panels["high"], panels["volume"])
    if factor_id == ALPHA_041:
        return alpha_041(panels["high"], panels["low"], panels["vwap"])
    if factor_id == ALPHA_042:
        return alpha_042(panels["close"], panels["vwap"])
    if factor_id == ALPHA_043:
        return alpha_043(panels["close"], panels["volume"])
    if factor_id == ALPHA_044:
        return alpha_044(panels["high"], panels["volume"])
    if factor_id == ALPHA_045:
        return alpha_045(panels["close"], panels["volume"])
    if factor_id == ALPHA_046:
        return alpha_046(panels["close"])
    if factor_id == ALPHA_049:
        return alpha_049(panels["close"])
    if factor_id == ALPHA_050:
        return alpha_050(panels["volume"], panels["vwap"])
    if factor_id == ALPHA_051:
        return alpha_051(panels["close"])
    if factor_id == ALPHA_052:
        return alpha_052(panels["low"], panels["returns"], panels["volume"])
    if factor_id == ALPHA_053:
        return alpha_053(panels["high"], panels["low"], panels["close"])
    if factor_id == ALPHA_054:
        return alpha_054(panels["open"], panels["high"], panels["low"], panels["close"])
    if factor_id == ALPHA_055:
        return alpha_055(
            panels["high"],
            panels["low"],
            panels["close"],
            panels["volume"],
        )
    if factor_id == ALPHA_060:
        return alpha_060(
            panels["high"],
            panels["low"],
            panels["close"],
            panels["volume"],
        )
    if factor_id == ALPHA_101:
        return alpha_101(panels["open"], panels["high"], panels["low"], panels["close"])
    raise ValueError(f"unknown diagnostic alpha: {factor_id}")


def build_default_sector_mapping(
    assets: Sequence[str],
    n_sectors: int = 5,
) -> dict[str, str]:
    """Assign assets into deterministic balanced sector cohorts."""
    sorted_assets = sorted(assets)
    block_size = max(1, len(sorted_assets) // n_sectors)
    return {
        asset: f"Sector_{min(i // block_size, n_sectors - 1)}"
        for i, asset in enumerate(sorted_assets)
    }


def compute_rolling_market_beta(
    returns: pd.DataFrame,
    *,
    window: int = 60,
    min_periods: int = 20,
) -> pd.DataFrame:
    """Compute rolling market beta for each asset against equal-weighted market return."""
    market_returns = returns.mean(axis=1)
    market_var = market_returns.rolling(window, min_periods=min_periods).var()
    market_cov = returns.rolling(window, min_periods=min_periods).cov(market_returns)
    return market_cov.div(market_var, axis=0)


def run_multifactor_diagnostic_mvp(
    *,
    config: MultifactorDiagnosticConfig = MultifactorDiagnosticConfig(),
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Run the 50-stock implemented-alpha diagnostic and optionally write reports."""

    experiment_log_path = (
        resolve_experiment_log_path(
            report_path,
            default_report_path=DEFAULT_REPORT_PATH,
            default_log_path=DEFAULT_EXPERIMENT_LOG_PATH,
        )
        if experiment_log_path is None
        else experiment_log_path
    )

    manifest, panels = load_diagnostic_cohort_ohlcv(config.manifest_path)
    prices = panels["close"]
    starting_price = float(manifest["generation"]["starting_price"])
    if len(prices.index) <= config.warmup_periods + config.forward_holding_periods:
        raise ValueError("diagnostic cohort is too short for alpha warm-up and labels")

    evaluation_start = prices.index[config.warmup_periods]
    evaluation_end = prices.index[-1]
    forward_returns = execution_aligned_forward_returns(
        prices,
        holding_periods=config.forward_holding_periods,
        execution_lag=config.signal_lag_periods,
    )
    benchmark = build_equal_weight_benchmark(prices, starting_price=starting_price)
    accounting_benchmark = benchmark.loc[evaluation_start:evaluation_end]
    monthly_dates = month_end_dates(prices.index)
    monthly_eval_dates = monthly_dates[
        (monthly_dates >= evaluation_start) & (monthly_dates <= evaluation_end)
    ]

    alpha_panels: dict[str, pd.DataFrame] = {}
    factor_results: dict[str, dict[str, Any]] = {}
    for factor_id in ALPHA_IDS:
        factor = calculate_diagnostic_alpha(factor_id, panels)
        alpha_panels[factor_id] = factor
        factor_results[factor_id] = _evaluate_factor(
            factor_id=factor_id,
            factor=factor,
            prices=prices,
            forward_returns=forward_returns,
            monthly_eval_dates=monthly_eval_dates,
            accounting_benchmark=accounting_benchmark,
            evaluation_start=evaluation_start,
            evaluation_end=evaluation_end,
            config=config,
        )

    ordered_alphas = [alpha_panels[factor_id] for factor_id in ALPHA_IDS]
    ic_weights = [
        float(factor_results[factor_id]["ic_summary"]["mean_ic"]) for factor_id in ALPHA_IDS
    ]
    ic_history = pd.DataFrame(
        {factor_id: factor_results[factor_id]["monthly_ic"] for factor_id in ALPHA_IDS}
    )

    volatility_proxy = panels["returns"].rolling(20, min_periods=5).std()
    sector_map = build_default_sector_mapping(prices.columns)
    market_beta = compute_rolling_market_beta(panels["returns"], window=60, min_periods=20)
    ic_comp = ic_weighted_composite(ordered_alphas, ic_weights)

    composites = {
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
        ALPHA_PRODUCT_INTERACTION: factor_product_interaction(
            alpha_panels[ALPHA_016],
            alpha_panels[ALPHA_022],
        ),
        CONDITIONAL_RANK_INTERACTION: conditional_factor_rank(
            conditioning_factor=alpha_panels[ALPHA_016],
            target_factor=alpha_panels[ALPHA_022],
            n_bins=5,
        ),
        NEUTRALIZED_IC_COMPOSITE: cross_sectional_neutralize(
            ic_comp,
            volatility_proxy,
        ),
        SECTOR_NEUTRAL_COMPOSITE: cross_sectional_group_neutralize(
            ic_comp,
            sector_map,
        ),
        MARKET_BETA_NEUTRAL_COMPOSITE: cross_sectional_neutralize(
            ic_comp,
            market_beta,
        ),
    }
    for factor_id, factor in composites.items():
        factor_results[factor_id] = _evaluate_factor(
            factor_id=factor_id,
            factor=factor,
            prices=prices,
            forward_returns=forward_returns,
            monthly_eval_dates=monthly_eval_dates,
            accounting_benchmark=accounting_benchmark,
            evaluation_start=evaluation_start,
            evaluation_end=evaluation_end,
            config=config,
        )

    alpha_returns = pd.DataFrame(
        {
            factor_id: factor_results[factor_id]["backtest"].returns.iloc[1:]
            for factor_id in ALPHA_IDS
        }
    )
    pbo_summary = probability_of_backtest_overfitting(
        alpha_returns,
        n_splits=config.pbo_n_splits,
    )

    factor_panels_dict = {
        factor_id: factor_results[factor_id]["factor"]
        for factor_id in WEIGHTING_COMPARISON_FACTORS
    }
    weighting_comparisons = evaluate_portfolio_weighting_comparisons(
        factors=factor_panels_dict,
        prices=prices,
        accounting_benchmark=accounting_benchmark,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
        config=config,
    )

    result = {
        "manifest": manifest,
        "panels": panels,
        "prices": prices,
        "config": config,
        "evaluation_start": evaluation_start,
        "evaluation_end": evaluation_end,
        "benchmark": benchmark,
        "factors": factor_results,
        "ic_weights": dict(zip(ALPHA_IDS, ic_weights, strict=True)),
        "sector_map": sector_map,
        "market_beta": market_beta,
        "pbo_summary": pbo_summary,
        "weighting_comparisons": weighting_comparisons,
        "report_path": report_path,
        "experiment_log_path": experiment_log_path,
        "evidence_ceiling": manifest["evidence_ceiling"],
    }
    if write_outputs:
        write_report(result=result)
        write_multifactor_experiment_log(result=result)
        if Path(report_path).resolve() == DEFAULT_REPORT_PATH.resolve():
            write_experiment_registry_report()
    return result


def evaluate_portfolio_weighting_comparisons(
    *,
    factors: dict[str, pd.DataFrame],
    prices: pd.DataFrame,
    accounting_benchmark: pd.Series,
    evaluation_start: pd.Timestamp,
    evaluation_end: pd.Timestamp,
    config: MultifactorDiagnosticConfig,
) -> list[dict[str, Any]]:
    """Evaluate key composite factors across weighting and turnover penalty schemes."""

    records: list[dict[str, Any]] = []
    for factor_id in WEIGHTING_COMPARISON_FACTORS:
        factor = factors[factor_id]
        source_provenance = capture_backtest_source_provenance(prices, factor)
        for scheme in WEIGHTING_COMPARISON_SCHEMES:
            scheme_name = str(scheme["name"])
            w_scheme = str(scheme["weighting_scheme"])
            penalty_lambda = float(scheme["turnover_penalty_lambda"])

            lo_bt = run_long_only_backtest(
                prices,
                factor,
                source_provenance=source_provenance,
                evaluation_start=evaluation_start,
                evaluation_end=evaluation_end,
                rebalance_frequency=config.rebalance_frequency,
                top_n=config.top_n,
                weighting_scheme=w_scheme,
                turnover_penalty_lambda=penalty_lambda,
                volatility_window=config.volatility_window,
                transaction_cost_bps=config.transaction_cost_bps,
                slippage_bps=config.slippage_bps,
                benchmark_prices=accounting_benchmark,
                signal_lag_periods=config.signal_lag_periods,
                periods_per_year=config.periods_per_year,
            )
            ls_bt = run_long_short_backtest(
                prices,
                factor,
                evaluation_start=evaluation_start,
                evaluation_end=evaluation_end,
                rebalance_frequency=config.rebalance_frequency,
                quantiles=config.quantiles,
                weighting_scheme=w_scheme,
                turnover_penalty_lambda=penalty_lambda,
                volatility_window=config.volatility_window,
                transaction_cost_bps=config.transaction_cost_bps,
                slippage_bps=config.slippage_bps,
                signal_lag_periods=config.signal_lag_periods,
                periods_per_year=config.periods_per_year,
            )
            lo_m = lo_bt.metrics
            ls_m = ls_bt.metrics
            records.append(
                {
                    "factor_id": factor_id,
                    "scheme": scheme_name,
                    "weighting_scheme": w_scheme,
                    "turnover_penalty_lambda": penalty_lambda,
                    "lo_sharpe": lo_m["sharpe_ratio"],
                    "lo_total_return": lo_m["total_return"],
                    "lo_max_drawdown": lo_m["max_drawdown"],
                    "lo_turnover": lo_m.get("average_turnover", np.nan),
                    "ls_sharpe": ls_m["sharpe"],
                    "ls_annualized_return": ls_m["annualized_return"],
                    "ls_max_drawdown": ls_m["max_drawdown"],
                    "ls_turnover": ls_m["total_turnover"],
                }
            )
    return records


def _evaluate_factor(
    *,
    factor_id: str,
    factor: pd.DataFrame,
    prices: pd.DataFrame,
    forward_returns: pd.DataFrame,
    monthly_eval_dates: pd.DatetimeIndex,
    accounting_benchmark: pd.Series,
    evaluation_start: pd.Timestamp,
    evaluation_end: pd.Timestamp,
    config: MultifactorDiagnosticConfig,
) -> dict[str, Any]:
    daily_ic = factor_rank_information_coefficient(factor, forward_returns)
    monthly_ic = daily_ic.reindex(monthly_eval_dates)
    ic_summary = information_coefficient_summary(monthly_ic)
    source_provenance = capture_backtest_source_provenance(prices, factor)
    backtest = run_long_only_backtest(
        prices,
        factor,
        source_provenance=source_provenance,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
        rebalance_frequency=config.rebalance_frequency,
        top_n=config.top_n,
        weighting_scheme=config.weighting_scheme,
        turnover_penalty_lambda=config.turnover_penalty_lambda,
        volatility_window=config.volatility_window,
        transaction_cost_bps=config.transaction_cost_bps,
        slippage_bps=config.slippage_bps,
        benchmark_prices=accounting_benchmark,
        signal_lag_periods=config.signal_lag_periods,
        periods_per_year=config.periods_per_year,
    )
    long_short_backtest = run_long_short_backtest(
        prices,
        factor,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
        rebalance_frequency=config.rebalance_frequency,
        quantiles=config.quantiles,
        weighting_scheme=config.long_short_weighting_scheme,
        turnover_penalty_lambda=config.turnover_penalty_lambda,
        volatility_window=config.volatility_window,
        transaction_cost_bps=config.transaction_cost_bps,
        slippage_bps=config.slippage_bps,
        signal_lag_periods=config.signal_lag_periods,
        periods_per_year=config.periods_per_year,
    )
    measured_returns = backtest.returns.iloc[1:]
    return {
        "factor_id": factor_id,
        "factor": factor,
        "daily_ic": daily_ic,
        "monthly_ic": monthly_ic,
        "ic_summary": ic_summary,
        "backtest": backtest,
        "long_short_backtest": long_short_backtest,
        "dsr": deflated_sharpe_ratio(
            measured_returns,
            n_trials=config.n_trials,
        ),
    }


def write_multifactor_experiment_log(*, result: dict[str, Any]) -> dict[str, object]:
    """Write a deterministic JSON log for the implemented-alpha diagnostic."""

    config: MultifactorDiagnosticConfig = result["config"]
    first_backtest: BacktestResult = result["factors"][ALPHA_IDS[0]]["backtest"]
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
        experiment_id="multifactor-diagnostic-mvp",
        title="WorldQuant Alphas Batch 5 Multifactor Diagnostic MVP",
        experiment_type="synthetic_alphas_diagnostic",
        summary=(
            "DIAGNOSTIC_ONLY static 50-stock synthetic cohort wired through "
            "the 52 implemented classical price-volume alphas, equal-weighted, "
            "in-sample IC-weighted, causal walk-forward ICIR-weighted, and "
            "causal walk-forward correlation-discounted composites, "
            "cross-sectional volatility, sector, and market beta neutralization, and "
            "cross-factor interaction models (product interaction and conditional rank), "
            "with monthly Rank IC, ICIR, Newey-West t-stat, DSR with Euler-Mascheroni mix, "
            "equal-weight monthly rebalance backtests at 5 bps slippage, and "
            "dollar-neutral long-short decile spread backtests."
        ),
        config={
            "manifest_path": _project_relative_path(config.manifest_path),
            "rebalance_frequency": config.rebalance_frequency,
            "top_n": config.top_n,
            "transaction_cost_bps": config.transaction_cost_bps,
            "slippage_bps": config.slippage_bps,
            "signal_lag_periods": config.signal_lag_periods,
            "periods_per_year": config.periods_per_year,
            "n_trials": config.n_trials,
            "forward_holding_periods": config.forward_holding_periods,
            "warmup_periods": config.warmup_periods,
            "ic_weights": result["ic_weights"],
            "quantiles": config.quantiles,
            "ridge_alpha": config.ridge_alpha,
        },
        assumptions={
            "data_scope": "synthetic only",
            "data_source": "local deterministic generator; no external data fetch",
            "evidence_ceiling": result["evidence_ceiling"],
            "dataset_manifest_reviewed": False,
            "formal_interpretation_eligible": False,
            "universe": "50-stock static survivor diagnostic cohort",
            "survivorship_bias": True,
            "not_point_in_time_universe_evidence": True,
            "date_range": {
                "start": result["evaluation_start"].date(),
                "end": result["evaluation_end"].date(),
            },
            "source_date_range": {
                "start": result["prices"].index.min().date(),
                "end": result["prices"].index.max().date(),
            },
            "feature_timing": (
                "implemented alphas use only open, high, low, close, vwap, "
                "volume, and returns on or before the signal date; "
                "signal_lag_periods=1 delays portfolio formation"
            ),
            "execution_timing": first_backtest.assumptions["execution_timing"],
            "rebalance_frequency": config.rebalance_frequency,
            "selected_assets_per_rebalance": config.top_n,
            "benchmark": "synthetic equal-weight diagnostic-cohort benchmark",
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
            "n_trials_for_dsr": config.n_trials,
            "dsr_expected_max_mix": "euler_mascheroni",
            "composite_ic_weights": (
                "in-sample mean monthly Rank IC of the 52 implemented alphas"
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
            "sector_map": (
                "5 balanced cohorts across 50 assets (10 assets per sector)"
            ),
            "market_beta_proxy": (
                "60-day rolling return beta against equal-weighted market return "
                "with min_periods=20; leading dates without a full minimum window remain NaN"
            ),
            "vwap_definition": "typical price (high + low + close) / 3 on companion synthetic bars",
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
            "markdown_report": _project_relative_path(result["report_path"]),
            "experiment_log": _project_relative_path(result["experiment_log_path"]),
        },
        metrics={
            **factor_metrics,
            "pbo_summary": result["pbo_summary"],
            "weighting_comparisons": result.get("weighting_comparisons", []),
        },
        caveats=(
            *SYNTHETIC_RESEARCH_CAVEATS,
            "DIAGNOSTIC_ONLY",
            "static survivor cohort is not point-in-time universe evidence",
            "not a 14-trial campaign run",
            "not evidence of real-world strategy performance",
            "IC-weighted composite uses in-sample mean monthly Rank IC weights",
            "ICIR-weighted and correlation-discounted composites use causal "
            "walk-forward weights at monthly rebalance dates, admitting an IC "
            "labeled at s only when its execution-aligned forward-return "
            "window has closed by t",
            "volatility proxy does not backfill leading rolling-standard-deviation NaNs",
            "sector map uses static balanced cohorts across 50 assets",
            "market beta proxy does not backfill leading rolling-beta NaNs",
        ),
        next_action=(
            "Keep this as a DIAGNOSTIC_ONLY implemented-alpha and composite "
            "wiring check. It does not reopen identity, D8, A2, or formal "
            "interpretation."
        ),
    )


def write_report(*, result: dict[str, Any]) -> None:
    """Write human-readable markdown for the implemented-alpha diagnostic."""

    config: MultifactorDiagnosticConfig = result["config"]
    manifest = result["manifest"]
    report_path = Path(result["report_path"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    first_backtest: BacktestResult = result["factors"][ALPHA_IDS[0]]["backtest"]
    pbo_summary = result["pbo_summary"]
    horizon_contract = (
        f"source_row(s) + {config.signal_lag_periods} + "
        f"{config.forward_holding_periods} <= source_row(t)"
    )

    rows = []
    ls_rows = []
    for factor_id in FACTOR_IDS:
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
                    _format_number(ic_summary["icIR"] if "icIR" in ic_summary else ic_summary["icir"]),
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
    weight_rows = []
    for factor_id in ALPHA_IDS:
        weight_rows.append(
            f"| {factor_id} | {_format_number(result['ic_weights'][factor_id])} |"
        )

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

    alpha_names = ", ".join(f"`{factor_id}`" for factor_id in ALPHA_IDS)
    content = f"""# WorldQuant Alphas Batch 5 Multifactor Diagnostic MVP Evidence

This report is `DIAGNOSTIC_ONLY`. It uses a committed synthetic 50-stock static
survivor cohort. That cohort is not point-in-time universe evidence, not a
dataset-review decision, and not a 14-trial campaign run. Metrics are
workflow diagnostics only and are not evidence of real-world strategy
profitability.

## Evidence ceiling

- Evidence ceiling: `{manifest["evidence_ceiling"]}`
- Review decision: `{manifest["review_decision"]}`
- `dataset_manifest_reviewed`: `{manifest["dataset_manifest_reviewed"]}`
- `formal_interpretation_eligible`: `{manifest["formal_interpretation_eligible"]}`
- Survivorship bias: `{manifest["survivorship_bias"]}`
- Not point-in-time universe evidence: `{manifest["not_point_in_time_universe_evidence"]}`
- Cohort id: `{manifest["cohort_id"]}`

## Pipeline

1. Load the 50-stock diagnostic cohort fixture and generate synthetic close
   prices plus companion open, high, low, typical-price VWAP, volume, and
   close-to-close returns.
2. Compute classical price-volume alphas {alpha_names}.
3. Build `EQUAL_WEIGHTED_COMPOSITE` as the equal-weight average of
   cross-sectional z-scores of those {IMPLEMENTED_ALPHA_COUNT} alphas.
4. Build `IC_WEIGHTED_COMPOSITE` with the same z-scores and in-sample mean
   monthly Rank IC as static supplied weights.
5. Build `ICIR_WEIGHTED_COMPOSITE` with causal walk-forward ICIR weights: on
   each monthly rebalance date t, ICIR is estimated from monthly Rank ICs
   labeled strictly before t whose execution-aligned forward-return windows
   have closed by t (`{horizon_contract}`). Expanding window,
   minimum 5 observations per factor. Those weights are held until the next
   rebalance.
6. Build `CORRELATION_DISCOUNTED_COMPOSITE` with causal walk-forward
   collinearity-discounted weights: expanding-window mean of those same
   horizon-complete monthly Rank ICs, and pairwise factor-value correlation
   through t.
7. Build `ALPHA_PRODUCT_INTERACTION` and `CONDITIONAL_RANK_INTERACTION` cross-factor models.
8. Build `NEUTRALIZED_IC_COMPOSITE` orthogonalized against trailing rolling
   return volatility. Leading dates without five observations remain NaN.
9. Build `SECTOR_NEUTRAL_COMPOSITE` demeaned within discrete sector cohorts
   (5 sectors across the 50 assets).
10. Build `MARKET_BETA_NEUTRAL_COMPOSITE` orthogonalized against trailing 60-day
    rolling market beta against the equal-weighted market portfolio. Leading
    dates without 20 observations remain NaN.
11. Measure monthly Spearman Rank IC versus 21-source-row forward returns that
    start at the lag-1 execution close.
12. Summarize mean IC, ICIR (`mean / sample std`), and the Newey-West t-stat of
    the mean IC.
13. Run the existing long-only equal-weight monthly backtester with
    `{config.slippage_bps:.2f}` bps slippage and `{config.top_n}` names.
14. Run dollar-neutral long-short decile spread backtests with `{config.quantiles}` quantiles
    and `{config.slippage_bps:.2f}` bps slippage.
15. Compute the Deflated Sharpe Ratio of daily measured strategy returns with
    `n_trials={config.n_trials}` and the Euler-Mascheroni expected-maximum mix.
16. Compute the Probability of Backtest Overfitting (PBO) across all {IMPLEMENTED_ALPHA_COUNT}
    alphas using Combinatorially Symmetric Cross-Validation (CSCV).

## Configuration

- Manifest: `{_project_relative_path(config.manifest_path)}`
- Asset count: `{manifest["asset_count"]}`
- Source date range: `{result["prices"].index.min().date()}` to `{result["prices"].index.max().date()}`
- Evaluation date range: `{result["evaluation_start"].date()}` to `{result["evaluation_end"].date()}`
- Rebalance frequency: `{config.rebalance_frequency}`
- Selected assets per rebalance: `{config.top_n}`
- Signal lag: `{config.signal_lag_periods}` source row
- Execution timing: `{first_backtest.assumptions["execution_timing"]}`
- Transaction cost: `{config.transaction_cost_bps:.2f}` bps
- Slippage: `{config.slippage_bps:.2f}` bps
- Zero cost or slippage diagnostic: `{first_backtest.assumptions["zero_cost_or_slippage_is_diagnostic"]}`
- Benchmark: synthetic equal-weight diagnostic-cohort benchmark
- Timing contract: `{first_backtest.timing_metadata["timing_contract"]}`
- DSR expected-maximum mix: Euler-Mascheroni constant `np.euler_gamma`
- PBO splits: `{config.pbo_n_splits}`
- VWAP: typical price `(high + low + close) / 3` on companion synthetic bars
- Composite IC weights: in-sample mean monthly Rank IC of the {IMPLEMENTED_ALPHA_COUNT} implemented alphas
- Walk-forward ICIR and correlation weights: expanding window at each monthly rebalance; monthly ICs labeled strictly before t whose execution-aligned forward-return windows have closed by t (`{horizon_contract}`)
- Volatility proxy: 20-day rolling return standard deviation, min_periods=5, no backfill
- Sector map: 5 balanced cohorts across 50 assets (10 assets per sector)
- Market beta proxy: 60-day rolling return beta against equal-weighted market return, min_periods=20, no backfill
- Long-short quantiles: `{config.quantiles}`
- Long-only weighting scheme: `{config.weighting_scheme}`
- Long-short weighting scheme: `{config.long_short_weighting_scheme}`
- Turnover penalty lambda: `{config.turnover_penalty_lambda:.2f}`
- Volatility window: `{config.volatility_window}`

## In-sample IC weights

| factor | mean monthly Rank IC |
| --- | --- |
{chr(10).join(weight_rows)}

These IC-weighted composite weights are in-sample diagnostics. They are not
an out-of-sample combination rule. `ICIR_WEIGHTED_COMPOSITE` and
`CORRELATION_DISCOUNTED_COMPOSITE` replace full-sample static weights with
causal walk-forward weights at each monthly rebalance. An IC labeled at date
s enters the information set at rebalance date t when its execution-aligned
forward-return window has closed by t.

## Factor diagnostics

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown | average turnover | slippage cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

IC is monthly Spearman Rank IC. ICIR is not annualized. DSR is computed on
non-annualized daily measured returns using the Bailey-Lopez de Prado formula
with the Euler-Mascheroni mix. All {IMPLEMENTED_ALPHA_COUNT} alphas and all composites are
reported; weak or negative diagnostics are retained.

## Long-short decile spread diagnostics

Long-short decile spread backtests construct a dollar-neutral portfolio long the top decile
and short the bottom decile at monthly rebalance frequency with {config.slippage_bps:.2f} bps slippage.

Column groups in the table below:

- Sequential holding-period book metrics: `LS Sharpe`, `LS Ann Return`, `Max DD`, `Win Rate`. These use the lag-1 dollar-neutral long-short book return on every accounting date after the first bar.
- Rebalance-date one-day bucket diagnostics: `Decile Spread Mean`, `Monotonicity`. These use equal-weight quantile returns on month-end rebalance dates only.
- `Total Turnover` is the sequential book's cumulative absolute trade-weight change.

| factor | LS Sharpe | LS Ann Return | Max DD | Win Rate | Decile Spread Mean | Monotonicity | Total Turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(ls_rows)}

`LS Sharpe`, `LS Ann Return`, `Max DD`, and `Win Rate` summarize the sequential holding-period book. `Decile Spread Mean` is the mean top-minus-bottom quantile return on rebalance dates. Monotonicity is the Spearman rank correlation of mean rebalance-date returns across deciles D1..D10.

## Portfolio weighting and turnover penalization diagnostics

Comparison of weighting schemes and turnover penalty (λ) across key multi-factor composites:

| factor | scheme | LO Sharpe | LO Turnover | LO Return | LO Max DD | LS Sharpe | LS Turnover | LS Ann Return | LS Max DD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(comp_rows)}

Inverse-volatility weighting applies lagged 20-day return volatility (shift 1 source row). Turnover penalization (λ=0.5) blends drifted pre-trade holdings with target weights to reduce turnover drag.

## Overfitting diagnostics (CSCV / PBO)

- Probability of Backtest Overfitting (PBO): `{_format_number(pbo_summary["pbo"])}`
- Out-of-Sample Probability of Loss: `{_format_number(pbo_summary["prob_loss"])}`
- Combinations: `{pbo_summary["n_combinations"]}` (from `{pbo_summary["n_splits"]}` splits)
- Mean OOS Relative Rank: `{_format_number(pbo_summary["mean_relative_rank"])}`
- Median OOS Relative Rank: `{_format_number(pbo_summary["median_relative_rank"])}`
- Mean IS Sharpe: `{_format_number(pbo_summary["mean_is_sharpe"])}`
- Mean OOS Sharpe: `{_format_number(pbo_summary["mean_oos_sharpe"])}`

## Limitations

- Synthetic prices only; no vendor, private, or real market data.
- Companion open, high, low, and volume are additional synthetic draws from
  `seed + 1`; they are not observed market prints.
- VWAP is a typical-price proxy, not a traded volume-weighted average price.
- Static 50-name membership is survivorship-biased by construction.
- Close-only lag-1 execution is idealized research accounting, not brokerage.
- 5 bps slippage is a fixed diagnostic assumption, not a market-impact model.
- IC-weighted composite uses in-sample mean monthly Rank IC weights.
- ICIR-weighted and correlation-discounted composites use causal walk-forward
  weights at monthly rebalance dates. An IC labeled at s is admitted at t
  when `{horizon_contract}`. Early rebalances remain missing until the
  minimum realized IC history is available (typed missingness).
- The volatility proxy for `NEUTRALIZED_IC_COMPOSITE` is a trailing rolling
  return standard deviation (min_periods=5); market beta proxy for
  `MARKET_BETA_NEUTRAL_COMPOSITE` is a 60-day rolling covariance over market
  variance (min_periods=20). Leading dates without sufficient observations remain
  NaN; values are not backfilled from later dates.
- `SECTOR_NEUTRAL_COMPOSITE` demeans within 5 static balanced cohorts across the
  50 synthetic assets.
- This does not execute, replace, or reopen the refused 14-trial run.
- This does not grant `RESEARCH_PASS`, formal interpretation, or profitability.
"""
    report_path.write_text(content, encoding="utf-8")


def _format_percent(value: float) -> str:
    if value is None or pd.isna(value):
        return "NaN"
    return f"{value:.2%}"


def _format_number(value: float) -> str:
    if value is None or pd.isna(value):
        return "NaN"
    return f"{value:.4f}"


def _project_relative_path(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def main(
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
) -> None:
    """Run the implemented-alpha diagnostic with default settings."""

    run_multifactor_diagnostic_mvp(
        report_path=report_path,
        experiment_log_path=experiment_log_path,
    )


if __name__ == "__main__":
    main()
