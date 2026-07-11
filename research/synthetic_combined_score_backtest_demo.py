"""Synthetic combined-score backtest smoke demo.

This script connects deterministic synthetic factor panels to the existing
long-only backtester as a workflow smoke test. It does not use real market
data, connect to a broker, place orders, support live trading, or make a
profitability claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.portfolio import BacktestResult, run_long_only_backtest
from features.combine import combine_factors
from features.diagnostics import factor_correlation_matrix
from features.normalize import (
    cross_sectional_rank_factor,
    cross_sectional_winsorize_factor,
    cross_sectional_zscore_factor,
)
from research.synthetic_multifactor_workflow_demo import (
    FACTOR_NAMES,
    SyntheticMultifactorWorkflowConfig,
    generate_synthetic_factor_panels,
)
from reporting.experiment_log import (
    SYNTHETIC_RESEARCH_CAVEATS,
    resolve_experiment_log_path,
    write_experiment_log,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "synthetic_combined_score_backtest_demo.md"
DEFAULT_EXPERIMENT_LOG_PATH = (
    PROJECT_ROOT / "reports" / "experiment_logs" / "synthetic_combined_score_backtest_demo.json"
)


@dataclass(frozen=True)
class SyntheticCombinedScoreBacktestConfig:
    """Configuration for the synthetic combined-score backtest smoke test."""

    factor_seed: int = 20260528
    price_seed: int = 20260529
    asset_count: int = 12
    periods: int = 160
    start_date: str = "2024-01-02"
    starting_price: float = 100.0
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "synthetic_momentum": 0.50,
            "synthetic_quality": 0.30,
            "synthetic_reversal": 0.20,
        }
    )
    winsor_lower_quantile: float = 0.05
    winsor_upper_quantile: float = 0.95
    rebalance_frequency: str = "ME"
    top_n: int = 4
    transaction_cost_bps: float = 10.0
    slippage_bps: float = 0.0
    signal_lag_periods: int = 1
    periods_per_year: int = 252


@dataclass(frozen=True)
class SyntheticCombinedScoreBacktestResult:
    """Container for synthetic combined-score smoke-test outputs."""

    prices: pd.DataFrame
    raw_factors: dict[str, pd.DataFrame]
    winsorized_factors: dict[str, pd.DataFrame]
    zscore_factors: dict[str, pd.DataFrame]
    rank_factors: dict[str, pd.DataFrame]
    correlation_matrix: pd.DataFrame
    combined_score: pd.DataFrame
    benchmark_prices: pd.Series
    backtest_result: BacktestResult
    report_path: Path
    experiment_log_path: Path


def generate_synthetic_prices(
    config: SyntheticCombinedScoreBacktestConfig = SyntheticCombinedScoreBacktestConfig(),
) -> pd.DataFrame:
    """Generate deterministic synthetic prices with date/asset factor alignment."""

    _validate_config(config)

    rng = np.random.default_rng(config.price_seed)
    dates = pd.bdate_range(config.start_date, periods=config.periods)
    assets = [f"ASSET_{asset_id:02d}" for asset_id in range(1, config.asset_count + 1)]

    market_component = rng.normal(loc=0.00015, scale=0.0050, size=(config.periods, 1))
    asset_noise = rng.normal(loc=0.0, scale=0.0100, size=(config.periods, config.asset_count))
    asset_drifts = np.linspace(-0.00008, 0.00018, config.asset_count).reshape(1, -1)
    cyclical_component = 0.0005 * np.sin(np.linspace(0.0, 6.0 * np.pi, config.periods)).reshape(-1, 1)

    log_returns = market_component + asset_noise + asset_drifts + cyclical_component
    prices = config.starting_price * np.exp(np.cumsum(log_returns, axis=0))

    return pd.DataFrame(prices, index=dates, columns=assets)


def build_synthetic_equal_weight_benchmark(
    prices: pd.DataFrame,
    *,
    starting_price: float,
) -> pd.Series:
    """Build a synthetic equal-weight benchmark from synthetic prices."""

    daily_returns = prices.pct_change(fill_method=None).mean(axis=1).fillna(0.0)
    return (starting_price * (1.0 + daily_returns).cumprod()).rename(
        "synthetic_equal_weight_benchmark"
    )


def run_synthetic_combined_score_backtest_demo(
    *,
    config: SyntheticCombinedScoreBacktestConfig = SyntheticCombinedScoreBacktestConfig(),
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
    write_outputs: bool = True,
) -> SyntheticCombinedScoreBacktestResult:
    """Run the synthetic combined-score backtest smoke test and write a report."""

    experiment_log_path = resolve_experiment_log_path(
        report_path,
        default_report_path=DEFAULT_REPORT_PATH,
        default_log_path=DEFAULT_EXPERIMENT_LOG_PATH,
    ) if experiment_log_path is None else experiment_log_path

    prices = generate_synthetic_prices(config)
    raw_factors = generate_synthetic_factor_panels(_factor_config(config))
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
    correlation_matrix = factor_correlation_matrix(zscore_factors)
    combined_score = combine_factors(zscore_factors, config.weights)
    benchmark_prices = build_synthetic_equal_weight_benchmark(
        prices,
        starting_price=config.starting_price,
    )

    backtest_result = run_long_only_backtest(
        prices,
        combined_score,
        rebalance_frequency=config.rebalance_frequency,
        top_n=config.top_n,
        transaction_cost_bps=config.transaction_cost_bps,
        slippage_bps=config.slippage_bps,
        benchmark_prices=benchmark_prices,
        signal_lag_periods=config.signal_lag_periods,
        periods_per_year=config.periods_per_year,
    )

    result = SyntheticCombinedScoreBacktestResult(
        prices=prices,
        raw_factors=raw_factors,
        winsorized_factors=winsorized_factors,
        zscore_factors=zscore_factors,
        rank_factors=rank_factors,
        correlation_matrix=correlation_matrix,
        combined_score=combined_score,
        benchmark_prices=benchmark_prices,
        backtest_result=backtest_result,
        report_path=report_path,
        experiment_log_path=experiment_log_path,
    )
    if write_outputs:
        write_report(config=config, result=result)
        write_demo_experiment_log(config=config, result=result)
    return result


def write_demo_experiment_log(
    *,
    config: SyntheticCombinedScoreBacktestConfig,
    result: SyntheticCombinedScoreBacktestResult,
) -> dict[str, object]:
    """Write a deterministic JSON log for the combined-score smoke test."""

    metrics = result.backtest_result.metrics
    return write_experiment_log(
        log_path=result.experiment_log_path,
        experiment_id="synthetic-combined-score-backtest-demo",
        title="Synthetic Combined-Score Backtest Smoke Test",
        experiment_type="synthetic_backtest_smoke_test",
        summary=(
            "Deterministic synthetic smoke test that connects existing factor "
            "preprocessing and combination helpers to the existing long-only "
            "backtester with explicit signal lag, transaction costs, and "
            "fixed-bps slippage assumptions."
        ),
        config=config,
        assumptions={
            "data_scope": "synthetic only",
            "data_source": "local deterministic price and factor generators; no external data fetch",
            "universe": f"{config.asset_count} synthetic assets",
            "date_range": {
                "start": result.prices.index.min().date(),
                "end": result.prices.index.max().date(),
            },
            "factor_names": list(FACTOR_NAMES),
            "feature_timing": "synthetic factor values are aligned to price dates before lagged backtest use",
            "execution_timing": result.backtest_result.assumptions["execution_timing"],
            "rebalance_frequency": config.rebalance_frequency,
            "selected_assets_per_rebalance": config.top_n,
            "signal_lag_periods": config.signal_lag_periods,
            "benchmark": "synthetic equal-weight universe benchmark",
            "transaction_cost_model": (
                f"{result.backtest_result.assumptions['cost_model']}; "
                f"{config.transaction_cost_bps:.2f} bps per unit of drift-adjusted "
                "target-weight turnover on post-return portfolio value"
            ),
            "transaction_cost_bps": config.transaction_cost_bps,
            "slippage_model": (
                f"{result.backtest_result.assumptions['slippage_model']}; "
                f"{config.slippage_bps:.2f} bps per unit of drift-adjusted "
                "target-weight turnover on post-return portfolio value"
            ),
            "slippage_bps": config.slippage_bps,
            "zero_cost_or_slippage_is_diagnostic": result.backtest_result.assumptions[
                "zero_cost_or_slippage_is_diagnostic"
            ],
            "turnover_model": result.backtest_result.assumptions["turnover_model"],
            "turnover_reference": result.backtest_result.assumptions["turnover_reference"],
            "holdings_model": result.backtest_result.assumptions["holdings_model"],
            "fixed_cost_application_timing": result.backtest_result.assumptions[
                "fixed_cost_application_timing"
            ],
            "fixed_cost_return_impact_basis": result.backtest_result.assumptions[
                "fixed_cost_return_impact_basis"
            ],
            "tracking_error_contract": result.backtest_result.assumptions[
                "tracking_error_contract"
            ],
            "tracking_error_return_basis": result.backtest_result.assumptions[
                "tracking_error_return_basis"
            ],
            "tracking_error_frequency": result.backtest_result.assumptions[
                "tracking_error_frequency"
            ],
            "tracking_error_periods_per_year": result.backtest_result.assumptions[
                "tracking_error_periods_per_year"
            ],
            "tracking_error_ddof": result.backtest_result.assumptions[
                "tracking_error_ddof"
            ],
            "tracking_error_first_row_policy": result.backtest_result.assumptions[
                "tracking_error_first_row_policy"
            ],
            "tracking_error_missing_policy": result.backtest_result.assumptions[
                "tracking_error_missing_policy"
            ],
            "tracking_error_terminal_row_policy": result.backtest_result.assumptions[
                "tracking_error_terminal_row_policy"
            ],
            "benchmark_cost_basis": result.backtest_result.assumptions[
                "benchmark_cost_basis"
            ],
            **{
                key: result.backtest_result.assumptions[key]
                for key in result.backtest_result.assumptions
                if key.startswith("holding_episode_")
            },
            "long_only": result.backtest_result.assumptions["long_only"],
            "live_trading": False,
            "brokerage_integration": False,
        },
        outputs={
            "markdown_report": _project_relative_path(result.report_path),
            "experiment_log": _project_relative_path(result.experiment_log_path),
            "price_rows": result.prices.shape[0],
            "asset_count": result.prices.shape[1],
        },
        metrics=metrics,
        diagnostics={
            "aligned_signal_coverage": result.backtest_result.assumptions[
                "aligned_signal_coverage"
            ],
            "correlation_method": "pearson",
            "total_turnover": metrics["total_turnover"],
        },
        caveats=(
            *SYNTHETIC_RESEARCH_CAVEATS,
            "workflow smoke test only",
            "not evidence of real-world strategy performance",
            "not strategy validation",
        ),
        next_action=(
            "Use as a reproducible synthetic smoke-test log only; real-data "
            "readiness still requires explicit data interfaces, validation "
            "splits, liquidity assumptions, and slippage modeling."
        ),
    )


def write_report(
    *,
    config: SyntheticCombinedScoreBacktestConfig,
    result: SyntheticCombinedScoreBacktestResult,
) -> None:
    """Write a synthetic-only smoke-test report."""

    result.report_path.parent.mkdir(parents=True, exist_ok=True)
    metrics = result.backtest_result.metrics

    content = f"""# Synthetic Combined-Score Backtest Smoke Test

This report uses synthetic data only. It is not real-market evidence, not financial advice, and not a profitability claim. The smoke-test metrics below are synthetic diagnostics only and should not be interpreted as strategy validation.

The demo does not fetch real data, connect to a broker, place orders, support live trading, or provide order-execution logic.

## Purpose

Exercise the integration path from existing factor research helpers into the existing long-only backtester:

1. Generate deterministic synthetic prices and synthetic factor panels.
2. Winsorize factor cross-sections.
3. Normalize factors with z-scores and rank diagnostics.
4. Compute factor correlation diagnostics.
5. Combine z-scored factors with explicit weights.
6. Run the existing long-only backtester as a synthetic smoke test.
7. Record caveated diagnostic metrics and limitations.

## Configuration

| Item | Value |
| --- | --- |
| Factor seed | `{config.factor_seed}` |
| Price seed | `{config.price_seed}` |
| Asset count | `{config.asset_count}` |
| Price rows | `{len(result.prices)}` |
| Date range | `{result.prices.index.min().date()}` to `{result.prices.index.max().date()}` |
| Factor names | `{", ".join(FACTOR_NAMES)}` |
| Combination weights | `{_format_weights(config.weights)}` |
| Rebalance frequency | `{config.rebalance_frequency}` |
| Selected assets per rebalance | `{config.top_n}` |
| Transaction cost | `{config.transaction_cost_bps:.2f}` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value |
| Slippage | `{config.slippage_bps:.2f}` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value |
| Zero cost or slippage diagnostic | `{result.backtest_result.assumptions["zero_cost_or_slippage_is_diagnostic"]}` |
| Signal lag periods | `{config.signal_lag_periods}` |
| Benchmark | `synthetic equal-weight universe benchmark` |
| Tracking-error contract | `{result.backtest_result.assumptions["tracking_error_contract"]}` |
| Tracking-error return basis | `{result.backtest_result.assumptions["tracking_error_return_basis"]}` |
| Tracking-error frequency | `{result.backtest_result.assumptions["tracking_error_frequency"]}` |
| Tracking-error periods/year | `{result.backtest_result.assumptions["tracking_error_periods_per_year"]}` |
| Tracking-error ddof | `{result.backtest_result.assumptions["tracking_error_ddof"]}` |
| Tracking-error first-row policy | `{result.backtest_result.assumptions["tracking_error_first_row_policy"]}` |
| Tracking-error missing policy | `{result.backtest_result.assumptions["tracking_error_missing_policy"]}` |
| Tracking-error terminal-row policy | `{result.backtest_result.assumptions["tracking_error_terminal_row_policy"]}` |
| Benchmark cost basis | `{result.backtest_result.assumptions["benchmark_cost_basis"]}` |
| Holding-episode contract | `{result.backtest_result.assumptions["holding_episode_contract"]}` |
| Holding-episode return basis | `{result.backtest_result.assumptions["holding_episode_return_basis"]}` |
| Holding-episode cost allocation | `{result.backtest_result.assumptions["holding_episode_cost_allocation"]}` |
| Closed / terminal-open episodes | `{result.backtest_result.assumptions["holding_episode_closed_count"]}` / `{result.backtest_result.assumptions["holding_episode_terminal_open_count"]}` |

## Factor Correlation Diagnostics

The matrix below is computed from flattened z-scored synthetic factor panels.

{_format_markdown_table(result.correlation_matrix)}

## Smoke-Test Metrics

These values are deterministic diagnostics from synthetic data. They are not evidence of real-world performance.

| Metric | Value |
| --- | ---: |
| Total return | `{_format_percent(metrics["total_return"])}` |
| Annualized return | `{_format_percent(metrics["annualized_return"])}` |
| Annualized volatility | `{_format_percent(metrics["annualized_volatility"])}` |
| Tracking error vs synthetic benchmark | `{_format_percent(metrics["tracking_error"])}` |
| Episode hit rate | `{_format_percent(metrics["episode_hit_rate"])}` |
| Average holding-period return | `{_format_percent(metrics["average_holding_period_return"])}` |
| Sharpe ratio | `{_format_number(metrics["sharpe_ratio"])}` |
| Max drawdown | `{_format_percent(metrics["max_drawdown"])}` |
| Average holding count | `{_format_number(metrics["average_holding_count"])}` |
| Average position concentration HHI | `{_format_number(metrics["average_position_concentration_hhi"])}` |
| Max position concentration HHI | `{_format_number(metrics["max_position_concentration_hhi"])}` |
| Average turnover | `{_format_percent(metrics["average_turnover"])}` |
| Total turnover | `{_format_number(metrics["total_turnover"])}` |
| Total transaction cost impact | `{_format_percent(metrics["total_transaction_cost_impact"])}` |
| Total slippage cost impact | `{_format_percent(metrics["total_slippage_cost_impact"])}` |
| Total trading cost impact | `{_format_percent(metrics["total_trading_cost_impact"])}` |
| Benchmark total return | `{_format_percent(metrics["benchmark_total_return"])}` |
| Excess total return vs synthetic benchmark | `{_format_percent(metrics["excess_total_return"])}` |

## Limitations

- Synthetic prices and factors are not calibrated to actual equities.
- The combined score is a synthetic research feature, not a production signal.
- The backtest is a smoke test of workflow wiring only.
- There is no real data source, universe construction, liquidity model, market-impact model, or validation split.
- Holdings drift with asset returns between scheduled rebalances; turnover is measured against drifted pre-trade weights. Fixed-bps costs are charged on post-return portfolio value and expressed as beginning-period return impacts. This remains weight-level accounting, not an order-fill model.
- The zero-slippage setting is a diagnostic simplification, not an execution-realism claim.
- Results should not be used as investment evidence or a strategy-quality claim.
"""

    result.report_path.write_text(content, encoding="utf-8")


def _factor_config(
    config: SyntheticCombinedScoreBacktestConfig,
) -> SyntheticMultifactorWorkflowConfig:
    return SyntheticMultifactorWorkflowConfig(
        seed=config.factor_seed,
        asset_count=config.asset_count,
        periods=config.periods,
        start_date=config.start_date,
        weights=dict(config.weights),
        winsor_lower_quantile=config.winsor_lower_quantile,
        winsor_upper_quantile=config.winsor_upper_quantile,
    )


def _validate_config(config: SyntheticCombinedScoreBacktestConfig) -> None:
    if config.asset_count < 2:
        raise ValueError("asset_count must be at least 2")
    if config.periods < 2:
        raise ValueError("periods must be at least 2")
    if config.starting_price <= 0:
        raise ValueError("starting_price must be positive")
    if set(config.weights) != set(FACTOR_NAMES):
        raise ValueError("weights must exactly match synthetic factor names")


def _format_weights(weights: dict[str, float]) -> str:
    return ", ".join(f"{name}={weight:.2f}" for name, weight in weights.items())


def _format_percent(value: float) -> str:
    if pd.isna(value):
        return "NaN"
    return f"{value:.2%}"


def _format_number(value: float) -> str:
    if pd.isna(value):
        return "NaN"
    return f"{value:.4f}"


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
    """Run the synthetic combined-score smoke demo with default settings."""

    run_synthetic_combined_score_backtest_demo(
        report_path=report_path,
        experiment_log_path=experiment_log_path,
    )


if __name__ == "__main__":
    main()
