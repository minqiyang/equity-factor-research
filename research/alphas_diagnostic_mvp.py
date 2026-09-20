"""End-to-end WorldQuant alpha diagnostic pipeline.

This module wires classical price-volume alphas through the committed 50-stock
static diagnostic cohort, a small IC/ICIR/Newey-West/DSR summary, and the
existing equal-weight monthly long-only backtester with 5 bps slippage.

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
from data.diagnostic_cohort import load_diagnostic_cohort_ohlcv
from features.alphas import (
    alpha_001,
    alpha_002,
    alpha_003,
    alpha_004,
    alpha_006,
    alpha_012,
)
from features.diagnostics import (
    deflated_sharpe_ratio,
    factor_rank_information_coefficient,
    information_coefficient_summary,
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
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "alphas_diagnostic_mvp.md"
DEFAULT_EXPERIMENT_LOG_PATH = (
    PROJECT_ROOT / "reports" / "experiment_logs" / "alphas_diagnostic_mvp.json"
)

ALPHA_001 = "ALPHA_001"
ALPHA_002 = "ALPHA_002"
ALPHA_003 = "ALPHA_003"
ALPHA_004 = "ALPHA_004"
ALPHA_006 = "ALPHA_006"
ALPHA_012 = "ALPHA_012"
FACTOR_IDS = (ALPHA_001, ALPHA_002, ALPHA_003, ALPHA_004, ALPHA_006, ALPHA_012)
ALPHA_WARMUP_PERIODS = 25


@dataclass(frozen=True)
class AlphasDiagnosticConfig:
    """Frozen diagnostic settings for the price-volume alpha pipeline."""

    manifest_path: Path = DEFAULT_MANIFEST_PATH
    rebalance_frequency: str = "ME"
    top_n: int = 5
    transaction_cost_bps: float = 0.0
    slippage_bps: float = 5.0
    signal_lag_periods: int = 1
    periods_per_year: int = 252
    n_trials: int = 6
    forward_holding_periods: int = FORWARD_HOLDING_PERIODS
    warmup_periods: int = ALPHA_WARMUP_PERIODS


def calculate_alpha_factor(
    factor_id: str,
    panels: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Compute one classical price-volume alpha on companion OHLCV panels."""

    if factor_id == ALPHA_001:
        return alpha_001(panels["close"], panels["returns"])
    if factor_id == ALPHA_002:
        return alpha_002(panels["open"], panels["close"], panels["volume"])
    if factor_id == ALPHA_003:
        return alpha_003(panels["open"], panels["volume"])
    if factor_id == ALPHA_004:
        return alpha_004(panels["low"])
    if factor_id == ALPHA_006:
        return alpha_006(panels["open"], panels["volume"])
    if factor_id == ALPHA_012:
        return alpha_012(panels["close"], panels["volume"])
    raise ValueError(f"unknown diagnostic alpha: {factor_id}")


def run_alphas_diagnostic_mvp(
    *,
    config: AlphasDiagnosticConfig = AlphasDiagnosticConfig(),
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Run the 50-stock price-volume alpha diagnostic and optionally write reports."""

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

    factor_results: dict[str, dict[str, Any]] = {}
    for factor_id in FACTOR_IDS:
        factor = calculate_alpha_factor(factor_id, panels)
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
        factor_results[factor_id] = {
            "factor": factor,
            "daily_ic": daily_ic,
            "monthly_ic": monthly_ic,
            "ic_summary": ic_summary,
            "backtest": backtest,
            "dsr": float("nan"),
        }

    family_sharpes = [
        payload["backtest"].returns.iloc[1:].mean() / payload["backtest"].returns.iloc[1:].std(ddof=1)
        for payload in factor_results.values()
    ]
    trial_variance = float(np.var(family_sharpes, ddof=1))
    for payload in factor_results.values():
        if np.isfinite(trial_variance):
            payload["dsr"] = deflated_sharpe_ratio(
                payload["backtest"].returns.iloc[1:], n_trials=config.n_trials,
                trial_sharpe_variance=trial_variance,
            )

    result = {
        "manifest": manifest,
        "panels": panels,
        "prices": prices,
        "config": config,
        "trial_sharpe_variance": trial_variance,
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
        write_alphas_experiment_log(result=result)
        if Path(report_path).resolve() == DEFAULT_REPORT_PATH.resolve():
            write_experiment_registry_report()
    return result


def write_alphas_experiment_log(*, result: dict[str, Any]) -> dict[str, object]:
    """Write a deterministic JSON log for the price-volume alpha diagnostic."""

    config: AlphasDiagnosticConfig = result["config"]
    first_backtest: BacktestResult = result["factors"][ALPHA_001]["backtest"]
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
        experiment_id="alphas-diagnostic-mvp",
        title="WorldQuant Alphas Diagnostic MVP",
        experiment_type="synthetic_alphas_diagnostic",
        summary=(
            "DIAGNOSTIC_ONLY static 50-stock synthetic cohort wired through "
            "ALPHA_001, ALPHA_002, ALPHA_003, ALPHA_004, ALPHA_006, and "
            "ALPHA_012 with monthly Rank IC, ICIR, Newey-West t-stat, DSR "
            "with Euler-Mascheroni mix, and equal-weight monthly rebalance "
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
            "warmup_periods": config.warmup_periods,
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
                "price-volume alphas use only open, low, close, volume, and "
                "returns on or before the signal date; signal_lag_periods=1 "
                "delays portfolio formation"
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
            "trial_sharpe_variance": result["trial_sharpe_variance"],
            "dsr_trial_scope": "current evaluated factor family; raw-count independence sensitivity",
            "dsr_expected_max_mix": "euler_mascheroni",
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
            "Keep this as a DIAGNOSTIC_ONLY price-volume alpha wiring check. "
            "It does not reopen identity, D8, A2, or formal interpretation."
        ),
    )


def write_report(*, result: dict[str, Any]) -> None:
    """Write the consolidated diagnostic evidence summary."""

    report_path = Path(result["report_path"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    config: AlphasDiagnosticConfig = result["config"]
    manifest = result["manifest"]
    first_backtest: BacktestResult = result["factors"][ALPHA_001]["backtest"]
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

    content = f"""# WorldQuant Alphas Diagnostic MVP Evidence

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
   prices plus companion open, low, volume, and close-to-close returns.
2. Compute classical price-volume alphas `ALPHA_001`, `ALPHA_002`,
   `ALPHA_003`, `ALPHA_004`, `ALPHA_006`, and `ALPHA_012`.
3. Measure monthly Spearman Rank IC versus 21-source-row forward returns that
   start at the lag-1 execution close.
4. Summarize mean IC, ICIR (`mean / sample std`), and the Newey-West t-stat of
   the mean IC.
5. Run the existing long-only equal-weight monthly backtester with
   `{config.slippage_bps:.2f}` bps slippage and `{config.top_n}` names.
6. Compute the Deflated Sharpe Ratio of daily measured strategy returns with
   `n_trials={config.n_trials}` and the Euler-Mascheroni expected-maximum mix.

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

DSR uses across-trial sample variance of non-annualized Sharpes:
`{result["trial_sharpe_variance"]}`. The raw family count supplies an
independent-trial sensitivity calculation for this diagnostic run.

## Factor diagnostics

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown | average turnover | slippage cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

IC is monthly Spearman Rank IC. ICIR is not annualized. DSR is computed on
non-annualized daily measured returns using the Bailey-Lopez de Prado formula
with the Euler-Mascheroni mix. All six factors are reported; weak or
negative diagnostics are retained.

## Limitations

- Synthetic prices only; no vendor, private, or real market data.
- Companion open, low, and volume are additional synthetic draws from
  `seed + 1`; they are not observed market prints.
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
    """Run the price-volume alpha diagnostic with default settings."""

    run_alphas_diagnostic_mvp(
        report_path=report_path,
        experiment_log_path=experiment_log_path,
    )


if __name__ == "__main__":
    main()
