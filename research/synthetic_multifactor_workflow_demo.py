"""Synthetic-only multi-factor workflow demo.

This script demonstrates how the existing factor preprocessing, normalization,
diagnostic, and combination helpers can fit together on deterministic synthetic
factor panels. It does not use real market data, define portfolio construction,
run a backtest, fetch data, or make a profitability claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from features.combine import combine_factors
from features.diagnostics import factor_correlation_matrix
from features.normalize import (
    cross_sectional_percentile_rank_factor,
    cross_sectional_rank_factor,
    cross_sectional_winsorize_factor,
    cross_sectional_zscore_factor,
)
from reporting.experiment_log import (
    SYNTHETIC_RESEARCH_CAVEATS,
    resolve_experiment_log_path,
    write_experiment_log,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "synthetic_multifactor_workflow_demo.md"
DEFAULT_EXPERIMENT_LOG_PATH = (
    PROJECT_ROOT / "reports" / "experiment_logs" / "synthetic_multifactor_workflow_demo.json"
)

FACTOR_NAMES = (
    "synthetic_momentum",
    "synthetic_quality",
    "synthetic_reversal",
)


@dataclass(frozen=True)
class SyntheticMultifactorWorkflowConfig:
    """Configuration for the deterministic synthetic multi-factor workflow."""

    seed: int = 20260528
    asset_count: int = 12
    periods: int = 80
    start_date: str = "2024-01-02"
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "synthetic_momentum": 0.50,
            "synthetic_quality": 0.30,
            "synthetic_reversal": 0.20,
        }
    )
    winsor_lower_quantile: float = 0.05
    winsor_upper_quantile: float = 0.95


@dataclass(frozen=True)
class SyntheticMultifactorWorkflowResult:
    """Container for synthetic workflow outputs."""

    raw_factors: dict[str, pd.DataFrame]
    winsorized_factors: dict[str, pd.DataFrame]
    zscore_factors: dict[str, pd.DataFrame]
    rank_factors: dict[str, pd.DataFrame]
    percentile_rank_factors: dict[str, pd.DataFrame]
    correlation_matrix: pd.DataFrame
    combined_score: pd.DataFrame
    weights: dict[str, float]
    report_path: Path
    experiment_log_path: Path


def generate_synthetic_factor_panels(
    config: SyntheticMultifactorWorkflowConfig = SyntheticMultifactorWorkflowConfig(),
) -> dict[str, pd.DataFrame]:
    """Generate deterministic synthetic factor panels.

    The generated factors are simple numeric panels indexed by business dates
    with assets as columns. They are intentionally synthetic and are not
    calibrated to real equities or any live data source.
    """

    _validate_config(config)

    rng = np.random.default_rng(config.seed)
    dates = pd.bdate_range(config.start_date, periods=config.periods)
    assets = [f"ASSET_{asset_id:02d}" for asset_id in range(1, config.asset_count + 1)]

    time_trend = np.linspace(-1.0, 1.0, config.periods).reshape(-1, 1)
    cyclical_time = np.sin(np.linspace(0.0, 4.0 * np.pi, config.periods)).reshape(-1, 1)
    asset_loading = np.linspace(-1.0, 1.0, config.asset_count).reshape(1, -1)
    asset_quality = np.cos(np.linspace(0.0, np.pi, config.asset_count)).reshape(1, -1)

    momentum_noise = rng.normal(loc=0.0, scale=0.04, size=(config.periods, config.asset_count))
    quality_noise = rng.normal(loc=0.0, scale=0.03, size=(config.periods, config.asset_count))
    reversal_noise = rng.normal(loc=0.0, scale=0.05, size=(config.periods, config.asset_count))

    synthetic_momentum = 0.70 * time_trend + 0.45 * asset_loading + momentum_noise
    synthetic_quality = 0.60 * asset_quality + 0.10 * cyclical_time + quality_noise
    synthetic_reversal = -0.35 * time_trend - 0.40 * asset_loading + 0.20 * cyclical_time + reversal_noise

    return {
        "synthetic_momentum": pd.DataFrame(synthetic_momentum, index=dates, columns=assets),
        "synthetic_quality": pd.DataFrame(synthetic_quality, index=dates, columns=assets),
        "synthetic_reversal": pd.DataFrame(synthetic_reversal, index=dates, columns=assets),
    }


def run_synthetic_multifactor_workflow_demo(
    *,
    config: SyntheticMultifactorWorkflowConfig = SyntheticMultifactorWorkflowConfig(),
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
) -> SyntheticMultifactorWorkflowResult:
    """Run the synthetic factor workflow and write a Markdown report."""

    experiment_log_path = resolve_experiment_log_path(
        report_path,
        default_report_path=DEFAULT_REPORT_PATH,
        default_log_path=DEFAULT_EXPERIMENT_LOG_PATH,
    ) if experiment_log_path is None else experiment_log_path

    raw_factors = generate_synthetic_factor_panels(config)
    winsorized_factors = {
        name: cross_sectional_winsorize_factor(
            factor,
            lower_quantile=config.winsor_lower_quantile,
            upper_quantile=config.winsor_upper_quantile,
        )
        for name, factor in raw_factors.items()
    }
    zscore_factors = {
        name: cross_sectional_zscore_factor(factor)
        for name, factor in winsorized_factors.items()
    }
    rank_factors = {
        name: cross_sectional_rank_factor(factor)
        for name, factor in winsorized_factors.items()
    }
    percentile_rank_factors = {
        name: cross_sectional_percentile_rank_factor(factor)
        for name, factor in winsorized_factors.items()
    }

    correlation_matrix = factor_correlation_matrix(zscore_factors)
    combined_score = combine_factors(zscore_factors, config.weights)

    result = SyntheticMultifactorWorkflowResult(
        raw_factors=raw_factors,
        winsorized_factors=winsorized_factors,
        zscore_factors=zscore_factors,
        rank_factors=rank_factors,
        percentile_rank_factors=percentile_rank_factors,
        correlation_matrix=correlation_matrix,
        combined_score=combined_score,
        weights=dict(config.weights),
        report_path=report_path,
        experiment_log_path=experiment_log_path,
    )
    write_report(config=config, result=result)
    write_workflow_experiment_log(config=config, result=result)
    return result


def write_workflow_experiment_log(
    *,
    config: SyntheticMultifactorWorkflowConfig,
    result: SyntheticMultifactorWorkflowResult,
) -> dict[str, object]:
    """Write a deterministic JSON log for the synthetic factor workflow."""

    score_values = result.combined_score.stack(future_stack=True)
    return write_experiment_log(
        log_path=result.experiment_log_path,
        experiment_id="synthetic-multifactor-workflow-demo",
        title="Synthetic Multi-Factor Workflow Demo",
        experiment_type="synthetic_feature_workflow",
        summary=(
            "Deterministic synthetic workflow for factor preprocessing, "
            "normalization, diagnostics, and explicit weighted score combination."
        ),
        config=config,
        assumptions={
            "data_scope": "synthetic only",
            "data_source": "local deterministic factor generator; no external data fetch",
            "universe": f"{config.asset_count} synthetic assets",
            "date_range": {
                "start": result.combined_score.index.min().date(),
                "end": result.combined_score.index.max().date(),
            },
            "missing_value_policy": "no filling, reindexing, forward-fill, or zero defaults",
            "portfolio_construction": "not included",
            "backtest_integration": "not included",
            "benchmark": "not applicable",
            "transaction_cost_model": "not applicable; no portfolio or trades",
            "slippage_model": "not applicable; no portfolio or trades",
            "live_trading": False,
            "brokerage_integration": False,
        },
        outputs={
            "markdown_report": _project_relative_path(result.report_path),
            "experiment_log": _project_relative_path(result.experiment_log_path),
            "factor_rows": result.combined_score.shape[0],
            "asset_count": result.combined_score.shape[1],
        },
        diagnostics={
            "factor_names": list(FACTOR_NAMES),
            "combined_score_mean": float(score_values.mean()),
            "combined_score_standard_deviation": float(score_values.std(ddof=0)),
            "combined_score_minimum": float(score_values.min()),
            "combined_score_maximum": float(score_values.max()),
            "correlation_method": "pearson",
        },
        caveats=(
            *SYNTHETIC_RESEARCH_CAVEATS,
            "workflow diagnostics only",
            "not a strategy signal or portfolio",
        ),
        next_action=(
            "Use as a synthetic feature-workflow audit log only; backtest "
            "integration and real-data validation remain separate stages."
        ),
    )


def write_report(
    *,
    config: SyntheticMultifactorWorkflowConfig,
    result: SyntheticMultifactorWorkflowResult,
) -> None:
    """Write a deterministic synthetic workflow report."""

    result.report_path.parent.mkdir(parents=True, exist_ok=True)
    date_index = result.combined_score.index

    content = f"""# Synthetic Multi-Factor Workflow Demo

This report uses synthetic data only. It is not real-market evidence, not financial advice, and not a profitability claim. It does not run a backtest, construct a portfolio, support live trading, connect to a broker, or fetch real data.

## Purpose

Demonstrate the research feature workflow on deterministic synthetic factor panels:

1. Generate synthetic factor panels.
2. Apply row-wise factor winsorization.
3. Apply cross-sectional z-score normalization.
4. Apply ordinal rank and pandas percentile-rank normalization.
5. Compute factor correlation diagnostics.
6. Combine z-scored factors with explicit weights.
7. Write a synthetic-only workflow report.

## Configuration

| Item | Value |
| --- | --- |
| Random seed | `{config.seed}` |
| Asset count | `{config.asset_count}` |
| Factor rows | `{config.periods}` |
| Date range | `{date_index.min().date()}` to `{date_index.max().date()}` |
| Factor names | `{", ".join(FACTOR_NAMES)}` |
| Winsorization quantiles | `{config.winsor_lower_quantile:.2f}` / `{config.winsor_upper_quantile:.2f}` |
| Combination weights | `{_format_weights(result.weights)}` |

## Processing Summary

The workflow generated synthetic factors, clipped each date's cross-section with explicit quantile bounds, transformed the clipped panels with z-score and rank-based normalization helpers, measured pairwise factor relationships, and combined the z-scored factors with explicit weights.

No missing values were filled. No dates or assets were reindexed. No strategy, return metric, order rule, or execution assumption was produced.

## Correlation Diagnostics

The matrix below is computed from flattened z-scored factor panels using the existing diagnostic helper.

{_format_markdown_table(result.correlation_matrix)}

## Combined Score Diagnostics

The combined score is a weighted synthetic research feature panel. It is not a portfolio, trade list, or strategy signal.

| Diagnostic | Value |
| --- | ---: |
| Rows | `{result.combined_score.shape[0]}` |
| Assets | `{result.combined_score.shape[1]}` |
| Mean | `{_format_float(result.combined_score.stack(future_stack=True).mean())}` |
| Standard deviation | `{_format_float(result.combined_score.stack(future_stack=True).std(ddof=0))}` |
| Minimum | `{_format_float(result.combined_score.stack(future_stack=True).min())}` |
| Maximum | `{_format_float(result.combined_score.stack(future_stack=True).max())}` |

## Limitations

- Synthetic factors are not calibrated to actual equities.
- The report is a workflow smoke demo only.
- No real data source, universe construction, transaction cost model, slippage model, benchmark, or validation split is used.
- No backtest integration or portfolio construction is included.
- Factor-to-backtest integration remains deferred until this synthetic workflow is reviewed.
"""

    result.report_path.write_text(content, encoding="utf-8")


def _validate_config(config: SyntheticMultifactorWorkflowConfig) -> None:
    if isinstance(config.seed, bool) or not isinstance(config.seed, int):
        raise TypeError("seed must be an integer")
    if isinstance(config.asset_count, bool) or not isinstance(config.asset_count, int):
        raise TypeError("asset_count must be an integer")
    if config.asset_count < 2:
        raise ValueError("asset_count must be at least 2")
    if isinstance(config.periods, bool) or not isinstance(config.periods, int):
        raise TypeError("periods must be an integer")
    if config.periods < 1:
        raise ValueError("periods must be at least 1")
    if set(config.weights) != set(FACTOR_NAMES):
        raise ValueError("weights must exactly match synthetic factor names")


def _format_weights(weights: dict[str, float]) -> str:
    return ", ".join(f"{name}={weight:.2f}" for name, weight in weights.items())


def _format_float(value: float) -> str:
    if pd.isna(value):
        return "NaN"
    return f"{value:.4f}"


def _format_markdown_table(frame: pd.DataFrame) -> str:
    headers = ["Factor", *[str(column) for column in frame.columns]]
    separator = ["---", *["---:" for _ in frame.columns]]
    rows = [
        [str(index), *[_format_float(float(value)) for value in frame.loc[index]]]
        for index in frame.index
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _project_relative_path(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def main(
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
) -> None:
    """Run the synthetic multi-factor workflow with default settings."""

    run_synthetic_multifactor_workflow_demo(
        report_path=report_path,
        experiment_log_path=experiment_log_path,
    )


if __name__ == "__main__":
    main()
