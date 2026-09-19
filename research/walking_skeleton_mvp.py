"""End-to-end walking-skeleton diagnostic pipeline.

This module wires the committed 50-stock static diagnostic cohort through the
three frozen diagnostic factors, a small IC/ICIR/Newey-West/DSR summary, and
the existing equal-weight monthly long-only backtester with 5 bps slippage.

It is DIAGNOSTIC_ONLY. The static cohort is not point-in-time universe
evidence. Outputs are not profitability, strategy validation, or a 14-trial
campaign run.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest.portfolio import (
    BacktestResult,
    capture_backtest_source_provenance,
    run_long_only_backtest,
)
from data.diagnostic_cohort import load_diagnostic_cohort
from features.diagnostics import (
    deflated_sharpe_ratio,
    factor_rank_information_coefficient,
    information_coefficient_summary,
)
from features.momentum import calculate_12_1_momentum
from features.reversal import calculate_short_term_reversal
from features.volatility import calculate_realized_volatility
from reporting.experiment_log import (
    SYNTHETIC_RESEARCH_CAVEATS,
    resolve_experiment_log_path,
    write_experiment_log,
)
from reporting.experiment_registry import write_experiment_registry_report


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "walking_skeleton" / "diagnostic_cohort_v1.json"
)
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "walking_skeleton_mvp.md"
DEFAULT_EXPERIMENT_LOG_PATH = (
    PROJECT_ROOT / "reports" / "experiment_logs" / "walking_skeleton_mvp.json"
)

MOM_12_1 = "MOM_12_1"
REV_1M = "REV_1M"
LOW_VOL_3M = "LOW_VOL_3M"
FACTOR_IDS = (MOM_12_1, REV_1M, LOW_VOL_3M)
MOMENTUM_LOOKBACK_PERIODS = 252
MOMENTUM_SKIP_PERIODS = 21
REVERSAL_LOOKBACK_PERIODS = 21
LOW_VOL_RETURN_WINDOW = 63
FORWARD_HOLDING_PERIODS = 21
EXECUTION_LAG_PERIODS = 1


@dataclass(frozen=True)
class WalkingSkeletonConfig:
    """Frozen diagnostic settings for the walking-skeleton pipeline."""

    manifest_path: Path = DEFAULT_MANIFEST_PATH
    rebalance_frequency: str = "ME"
    top_n: int = 5
    transaction_cost_bps: float = 0.0
    slippage_bps: float = 5.0
    signal_lag_periods: int = 1
    periods_per_year: int = 252
    n_trials: int = 3
    forward_holding_periods: int = FORWARD_HOLDING_PERIODS


def calculate_diagnostic_factor(factor_id: str, prices: pd.DataFrame) -> pd.DataFrame:
    """Compute one frozen diagnostic factor on a price panel."""

    if factor_id == MOM_12_1:
        return calculate_12_1_momentum(
            prices,
            lookback_periods=MOMENTUM_LOOKBACK_PERIODS,
            skip_periods=MOMENTUM_SKIP_PERIODS,
        )
    if factor_id == REV_1M:
        return calculate_short_term_reversal(
            prices,
            lookback_periods=REVERSAL_LOOKBACK_PERIODS,
        )
    if factor_id == LOW_VOL_3M:
        return -calculate_realized_volatility(
            prices,
            window_periods=LOW_VOL_RETURN_WINDOW,
            ddof=1,
        )
    raise ValueError(f"unknown diagnostic factor: {factor_id}")


def execution_aligned_forward_returns(
    prices: pd.DataFrame,
    *,
    holding_periods: int = FORWARD_HOLDING_PERIODS,
    execution_lag: int = EXECUTION_LAG_PERIODS,
) -> pd.DataFrame:
    """Align holding-period returns to the signal date.

    The factor at date ``t`` is evaluated on the return from the execution
    close ``t + execution_lag`` through ``t + execution_lag + holding_periods``.
    These returns are evaluation targets, not signal inputs.
    """

    if (
        isinstance(holding_periods, bool)
        or not isinstance(holding_periods, int)
        or holding_periods < 1
    ):
        raise ValueError("holding_periods must be a positive integer")
    if (
        isinstance(execution_lag, bool)
        or not isinstance(execution_lag, int)
        or execution_lag < 1
    ):
        raise ValueError("execution_lag must be a positive integer")

    numeric_prices = prices.astype(float)
    start_prices = numeric_prices.shift(-execution_lag)
    end_prices = numeric_prices.shift(-(execution_lag + holding_periods))
    valid = start_prices.gt(0.0) & end_prices.gt(0.0)
    return (end_prices / start_prices - 1.0).where(valid)


def month_end_dates(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Return last observed source-row dates in each calendar month."""

    date_series = pd.Series(index=index, data=index)
    return pd.DatetimeIndex(date_series.resample("ME").last().dropna().to_list())


def build_equal_weight_benchmark(
    prices: pd.DataFrame,
    *,
    starting_price: float,
) -> pd.Series:
    """Build a synthetic equal-weight cohort benchmark price series."""

    daily_returns = prices.pct_change(fill_method=None).mean(axis=1).fillna(0.0)
    return (starting_price * (1.0 + daily_returns).cumprod()).rename(
        "diagnostic_cohort_equal_weight_benchmark"
    )


def run_walking_skeleton_mvp(
    *,
    config: WalkingSkeletonConfig = WalkingSkeletonConfig(),
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Run the 50-stock diagnostic walking skeleton and optionally write reports."""

    experiment_log_path = (
        resolve_experiment_log_path(
            report_path,
            default_report_path=DEFAULT_REPORT_PATH,
            default_log_path=DEFAULT_EXPERIMENT_LOG_PATH,
        )
        if experiment_log_path is None
        else experiment_log_path
    )

    manifest, prices = load_diagnostic_cohort(config.manifest_path)
    starting_price = float(manifest["generation"]["starting_price"])
    if len(prices.index) <= MOMENTUM_LOOKBACK_PERIODS + config.forward_holding_periods:
        raise ValueError("diagnostic cohort is too short for momentum warm-up and labels")

    evaluation_start = prices.index[MOMENTUM_LOOKBACK_PERIODS]
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

    factor_results: dict[str, dict[str, Any]] = {}
    for factor_id in FACTOR_IDS:
        factor = calculate_diagnostic_factor(factor_id, prices)
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
            transaction_cost_bps=config.transaction_cost_bps,
            slippage_bps=config.slippage_bps,
            benchmark_prices=accounting_benchmark,
            signal_lag_periods=config.signal_lag_periods,
            periods_per_year=config.periods_per_year,
        )
        measured_returns = backtest.returns.iloc[1:]
        factor_results[factor_id] = {
            "factor": factor,
            "daily_ic": daily_ic,
            "monthly_ic": monthly_ic,
            "ic_summary": ic_summary,
            "backtest": backtest,
            "dsr": deflated_sharpe_ratio(
                measured_returns,
                n_trials=config.n_trials,
            ),
        }

    result = {
        "manifest": manifest,
        "prices": prices,
        "config": config,
        "evaluation_start": evaluation_start,
        "evaluation_end": evaluation_end,
        "benchmark": benchmark,
        "factors": factor_results,
        "report_path": report_path,
        "experiment_log_path": experiment_log_path,
        "evidence_ceiling": manifest["evidence_ceiling"],
    }
    if write_outputs:
        write_report(result=result)
        write_skeleton_experiment_log(result=result)
        if Path(report_path).resolve() == DEFAULT_REPORT_PATH.resolve():
            write_experiment_registry_report()
    return result


def write_skeleton_experiment_log(*, result: dict[str, Any]) -> dict[str, object]:
    """Write a deterministic JSON log for the walking-skeleton diagnostic."""

    config: WalkingSkeletonConfig = result["config"]
    first_backtest: BacktestResult = result["factors"][MOM_12_1]["backtest"]
    factor_metrics = {
        factor_id: {
            **payload["ic_summary"],
            "dsr": payload["dsr"],
            **payload["backtest"].metrics,
        }
        for factor_id, payload in result["factors"].items()
    }
    return write_experiment_log(
        log_path=result["experiment_log_path"],
        experiment_id="walking-skeleton-mvp",
        title="Walking Skeleton MVP Diagnostic",
        experiment_type="synthetic_walking_skeleton_diagnostic",
        summary=(
            "DIAGNOSTIC_ONLY static 50-stock synthetic cohort wired through "
            "MOM_12_1, REV_1M, and LOW_VOL_3M with monthly Rank IC, ICIR, "
            "Newey-West t-stat, DSR, and equal-weight monthly rebalance "
            "backtests at 5 bps slippage."
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
                "close-derived factors use only prices on or before the signal "
                "date; signal_lag_periods=1 delays portfolio formation"
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
            "live_trading": False,
            "brokerage_integration": False,
        },
        outputs={
            "markdown_report": _project_relative_path(result["report_path"]),
            "experiment_log": _project_relative_path(result["experiment_log_path"]),
        },
        metrics=factor_metrics,
        caveats=(
            *SYNTHETIC_RESEARCH_CAVEATS,
            "DIAGNOSTIC_ONLY",
            "static survivor cohort is not point-in-time universe evidence",
            "not a 14-trial campaign run",
            "not evidence of real-world strategy performance",
        ),
        next_action=(
            "Keep this as a DIAGNOSTIC_ONLY walking-skeleton wiring check. "
            "It does not reopen identity, D8, A2, or formal interpretation."
        ),
    )


def write_report(*, result: dict[str, Any]) -> None:
    """Write the consolidated diagnostic evidence summary."""

    report_path = Path(result["report_path"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    config: WalkingSkeletonConfig = result["config"]
    manifest = result["manifest"]
    first_backtest: BacktestResult = result["factors"][MOM_12_1]["backtest"]
    rows = []
    for factor_id in FACTOR_IDS:
        payload = result["factors"][factor_id]
        ic_summary = payload["ic_summary"]
        metrics = payload["backtest"].metrics
        rows.append(
            "| "
            + " | ".join(
                [
                    factor_id,
                    _format_number(ic_summary["mean_ic"]),
                    _format_number(ic_summary["icir"]),
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

    content = f"""# Walking Skeleton MVP Diagnostic Evidence

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

1. Load the 50-stock diagnostic cohort fixture and generate synthetic prices.
2. Compute frozen diagnostic factors `MOM_12_1`, `REV_1M`, and `LOW_VOL_3M`.
3. Measure monthly Spearman Rank IC versus 21-source-row forward returns that
   start at the lag-1 execution close.
4. Summarize mean IC, ICIR (`mean / sample std`), and the Newey-West t-stat of
   the mean IC.
5. Run the existing long-only equal-weight monthly backtester with
   `{config.slippage_bps:.2f}` bps slippage and `{config.top_n}` names.
6. Compute the Deflated Sharpe Ratio of daily measured strategy returns with
   `n_trials={config.n_trials}`.

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

## Factor diagnostics

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown | average turnover | slippage cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

IC is monthly Spearman Rank IC. ICIR is not annualized. DSR is computed on
non-annualized daily measured returns. All three factors are reported; weak or
negative diagnostics are retained.

## Limitations

- Synthetic prices only; no vendor, private, or real market data.
- Static 50-name membership is survivorship-biased by construction.
- Close-only lag-1 execution is idealized research accounting, not brokerage.
- 5 bps slippage is a fixed diagnostic assumption, not a market-impact model.
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
    """Run the walking-skeleton diagnostic with default settings."""

    run_walking_skeleton_mvp(
        report_path=report_path,
        experiment_log_path=experiment_log_path,
    )


if __name__ == "__main__":
    main()
