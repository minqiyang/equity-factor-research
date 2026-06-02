"""Synthetic-only multi-factor parameter sweep.

This script runs a small deterministic grid of synthetic combined-score
backtest configurations. It is a sensitivity-reporting smoke test only: no real
market data is fetched, no brokerage or live-trading functionality is added,
and no profitability claim is made.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from research.synthetic_combined_score_backtest_demo import (
    SyntheticCombinedScoreBacktestConfig,
    run_synthetic_combined_score_backtest_demo,
)
from research.synthetic_multifactor_workflow_demo import FACTOR_NAMES
from reporting.experiment_log import (
    SYNTHETIC_RESEARCH_CAVEATS,
    resolve_experiment_log_path,
    write_experiment_log,
)
from reporting.experiment_registry import write_experiment_registry_report


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "synthetic_multifactor_parameter_sweep.md"
DEFAULT_EXPERIMENT_LOG_PATH = (
    PROJECT_ROOT / "reports" / "experiment_logs" / "synthetic_multifactor_parameter_sweep.json"
)

WEIGHT_SETS: dict[str, dict[str, float]] = {
    "balanced": {
        "synthetic_momentum": 1.0 / 3.0,
        "synthetic_quality": 1.0 / 3.0,
        "synthetic_reversal": 1.0 / 3.0,
    },
    "momentum_tilt": {
        "synthetic_momentum": 0.60,
        "synthetic_quality": 0.25,
        "synthetic_reversal": 0.15,
    },
    "quality_tilt": {
        "synthetic_momentum": 0.25,
        "synthetic_quality": 0.60,
        "synthetic_reversal": 0.15,
    },
    "reversal_tilt": {
        "synthetic_momentum": 0.25,
        "synthetic_quality": 0.15,
        "synthetic_reversal": 0.60,
    },
}


@dataclass(frozen=True)
class SyntheticParameterSweepConfig:
    """Configuration for the deterministic synthetic parameter sweep."""

    factor_seed: int = 20260528
    price_seed: int = 20260529
    asset_count: int = 12
    periods: int = 160
    start_date: str = "2024-01-02"
    starting_price: float = 100.0
    weight_sets: dict[str, dict[str, float]] = field(
        default_factory=lambda: {name: dict(weights) for name, weights in WEIGHT_SETS.items()}
    )
    top_n_values: tuple[int, ...] = (3, 4)
    winsor_lower_quantile: float = 0.05
    winsor_upper_quantile: float = 0.95
    rebalance_frequency: str = "ME"
    transaction_cost_bps: float = 10.0
    signal_lag_periods: int = 1
    periods_per_year: int = 252


@dataclass(frozen=True)
class SyntheticParameterSweepResult:
    """Container for synthetic parameter sweep outputs."""

    results: pd.DataFrame
    report_path: Path
    experiment_log_path: Path


def run_synthetic_multifactor_parameter_sweep(
    *,
    config: SyntheticParameterSweepConfig = SyntheticParameterSweepConfig(),
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
    update_registry: bool = True,
) -> SyntheticParameterSweepResult:
    """Run the synthetic parameter sweep and write report/log outputs."""

    _validate_config(config)
    experiment_log_path = resolve_experiment_log_path(
        report_path,
        default_report_path=DEFAULT_REPORT_PATH,
        default_log_path=DEFAULT_EXPERIMENT_LOG_PATH,
    ) if experiment_log_path is None else experiment_log_path

    rows = []
    for weight_set_name in sorted(config.weight_sets):
        weights = config.weight_sets[weight_set_name]
        for top_n in sorted(config.top_n_values):
            case_id = f"{weight_set_name}__top_{top_n}"
            case_result = run_synthetic_combined_score_backtest_demo(
                config=_combined_config(config, weights=weights, top_n=top_n),
                report_path=report_path.with_name(f"{report_path.stem}__{case_id}.md"),
                experiment_log_path=experiment_log_path.with_name(
                    f"{experiment_log_path.stem}__{case_id}.json"
                ),
                write_outputs=False,
            )
            metrics = case_result.backtest_result.metrics
            rows.append(
                {
                    "case_id": case_id,
                    "weight_set": weight_set_name,
                    "top_n": top_n,
                    "momentum_weight": weights["synthetic_momentum"],
                    "quality_weight": weights["synthetic_quality"],
                    "reversal_weight": weights["synthetic_reversal"],
                    "total_return": metrics["total_return"],
                    "annualized_return": metrics["annualized_return"],
                    "annualized_volatility": metrics["annualized_volatility"],
                    "sharpe_ratio": metrics["sharpe_ratio"],
                    "max_drawdown": metrics["max_drawdown"],
                    "average_turnover": metrics["average_turnover"],
                    "total_turnover": metrics["total_turnover"],
                    "total_transaction_cost_impact": metrics[
                        "total_transaction_cost_impact"
                    ],
                    "benchmark_total_return": metrics["benchmark_total_return"],
                    "excess_total_return": metrics["excess_total_return"],
                }
            )

    results = pd.DataFrame(rows).sort_values(["weight_set", "top_n"]).reset_index(drop=True)
    sweep_result = SyntheticParameterSweepResult(
        results=results,
        report_path=report_path,
        experiment_log_path=experiment_log_path,
    )
    write_report(config=config, result=sweep_result)
    write_sweep_experiment_log(config=config, result=sweep_result)
    if update_registry:
        write_experiment_registry_report()
    return sweep_result


def write_report(
    *,
    config: SyntheticParameterSweepConfig,
    result: SyntheticParameterSweepResult,
) -> None:
    """Write a Markdown report containing every synthetic sweep case."""

    result.report_path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# Synthetic Multi-Factor Parameter Sweep

This report uses synthetic data only. It is not real-market evidence, not financial advice, and not a profitability claim. All parameter cases are shown to avoid cherry-picking.

The sweep does not fetch real data, connect to a broker, place orders, support live trading, or provide order-execution logic.

## Purpose

Run a small deterministic sensitivity check over synthetic combined-score configurations:

1. Keep the same synthetic price and factor generators across every case.
2. Vary only explicit factor weights and selected-asset counts.
3. Run the existing long-only backtester with signal lag and transaction costs.
4. Report every case, including weak or negative diagnostics.

## Fixed Assumptions

| Item | Value |
| --- | --- |
| Factor seed | `{config.factor_seed}` |
| Price seed | `{config.price_seed}` |
| Asset count | `{config.asset_count}` |
| Price rows | `{config.periods}` |
| Date range | `{config.start_date}` plus `{config.periods}` business rows |
| Factor names | `{", ".join(FACTOR_NAMES)}` |
| Rebalance frequency | `{config.rebalance_frequency}` |
| Transaction cost | `{config.transaction_cost_bps:.2f}` bps per unit of target-weight turnover |
| Slippage model | `not separately modeled; diagnostic synthetic sweep only` |
| Signal lag periods | `{config.signal_lag_periods}` |
| Benchmark | `synthetic equal-weight universe benchmark` |

## Sweep Grid

| Weight set | Weights |
| --- | --- |
{_format_weight_set_rows(config.weight_sets)}

Selected-asset counts: `{", ".join(str(value) for value in sorted(config.top_n_values))}`

## Sweep Results

These metrics are deterministic diagnostics from synthetic data. They are not evidence of real-world performance or strategy validation.

{_format_results_table(result.results)}

## Limitations

- Synthetic prices and factors are not calibrated to actual equities.
- This is a parameter sensitivity smoke test, not model selection.
- The report does not identify a best parameter set or recommend a strategy.
- There is no real data source, universe construction, liquidity model, market-impact model, or validation split.
- Slippage is not separately modeled beyond the simplified transaction-cost assumption.
- Results should not be used as investment evidence or a strategy-quality claim.
"""
    result.report_path.write_text(content, encoding="utf-8")


def write_sweep_experiment_log(
    *,
    config: SyntheticParameterSweepConfig,
    result: SyntheticParameterSweepResult,
) -> dict[str, object]:
    """Write a deterministic JSON log for the full synthetic sweep."""

    return write_experiment_log(
        log_path=result.experiment_log_path,
        experiment_id="synthetic-multifactor-parameter-sweep",
        title="Synthetic Multi-Factor Parameter Sweep",
        experiment_type="synthetic_parameter_sweep",
        summary=(
            "Deterministic synthetic sensitivity check over explicit factor "
            "weight sets and selected-asset counts. Every case is reported; "
            "the sweep is not a parameter-selection claim."
        ),
        config={
            "factor_seed": config.factor_seed,
            "price_seed": config.price_seed,
            "asset_count": config.asset_count,
            "periods": config.periods,
            "start_date": config.start_date,
            "weight_sets": config.weight_sets,
            "top_n_values": list(config.top_n_values),
            "winsor_lower_quantile": config.winsor_lower_quantile,
            "winsor_upper_quantile": config.winsor_upper_quantile,
            "rebalance_frequency": config.rebalance_frequency,
            "transaction_cost_bps": config.transaction_cost_bps,
            "signal_lag_periods": config.signal_lag_periods,
            "periods_per_year": config.periods_per_year,
        },
        assumptions={
            "data_scope": "synthetic only",
            "data_source": "local deterministic price and factor generators; no external data fetch",
            "universe": f"{config.asset_count} synthetic assets",
            "date_range": {
                "start": config.start_date,
                "end": pd.bdate_range(config.start_date, periods=config.periods).max().date(),
            },
            "parameter_policy": "all configured cases are reported; no best-only filtering",
            "feature_timing": "synthetic factor values are aligned to price dates before lagged backtest use",
            "execution_timing": "signals known after close; trades on rebalance dates using lagged signals; holdings affect next price row",
            "rebalance_frequency": config.rebalance_frequency,
            "benchmark": "synthetic equal-weight universe benchmark",
            "transaction_cost_model": (
                f"{config.transaction_cost_bps:.2f} bps per unit of target-weight turnover"
            ),
            "slippage_model": "not separately modeled; diagnostic synthetic sweep only",
            "turnover_model": "target_weight_turnover",
            "long_only": True,
            "live_trading": False,
            "brokerage_integration": False,
        },
        outputs={
            "markdown_report": _project_relative_path(result.report_path),
            "experiment_log": _project_relative_path(result.experiment_log_path),
            "case_count": int(len(result.results)),
            "registry_report": "reports/experiment_registry.md",
        },
        metrics={},
        diagnostics={
            "cases": result.results.to_dict(orient="records"),
            "weakest_total_return_case": _case_id_at_extreme(result.results, "total_return", "min"),
            "strongest_total_return_case": _case_id_at_extreme(result.results, "total_return", "max"),
        },
        caveats=(
            *SYNTHETIC_RESEARCH_CAVEATS,
            "all parameter cases reported",
            "not parameter optimization",
            "not strategy validation",
        ),
        next_action=(
            "Use as a synthetic sensitivity smoke test only; any real-data "
            "parameter study requires explicit sample splits, universe rules, "
            "slippage assumptions, and full experiment-log entries."
        ),
    )


def _combined_config(
    sweep_config: SyntheticParameterSweepConfig,
    *,
    weights: dict[str, float],
    top_n: int,
) -> SyntheticCombinedScoreBacktestConfig:
    return SyntheticCombinedScoreBacktestConfig(
        factor_seed=sweep_config.factor_seed,
        price_seed=sweep_config.price_seed,
        asset_count=sweep_config.asset_count,
        periods=sweep_config.periods,
        start_date=sweep_config.start_date,
        starting_price=sweep_config.starting_price,
        weights=dict(weights),
        winsor_lower_quantile=sweep_config.winsor_lower_quantile,
        winsor_upper_quantile=sweep_config.winsor_upper_quantile,
        rebalance_frequency=sweep_config.rebalance_frequency,
        top_n=top_n,
        transaction_cost_bps=sweep_config.transaction_cost_bps,
        signal_lag_periods=sweep_config.signal_lag_periods,
        periods_per_year=sweep_config.periods_per_year,
    )


def _validate_config(config: SyntheticParameterSweepConfig) -> None:
    if not config.weight_sets:
        raise ValueError("weight_sets must not be empty")
    if not config.top_n_values:
        raise ValueError("top_n_values must not be empty")

    for name, weights in config.weight_sets.items():
        if set(weights) != set(FACTOR_NAMES):
            raise ValueError(f"weight set {name!r} must exactly match synthetic factor names")
        if not all(
            not isinstance(weight, bool) and isinstance(weight, int | float)
            for weight in weights.values()
        ):
            raise TypeError(f"weight set {name!r} contains non-numeric weights")
        if sum(abs(float(weight)) for weight in weights.values()) == 0.0:
            raise ValueError(f"weight set {name!r} must contain at least one nonzero weight")

    for top_n in config.top_n_values:
        if isinstance(top_n, bool) or not isinstance(top_n, int):
            raise TypeError("top_n_values must contain integers")
        if top_n <= 0:
            raise ValueError("top_n_values must be positive")
        if top_n > config.asset_count:
            raise ValueError("top_n_values must be no larger than asset_count")


def _format_weight_set_rows(weight_sets: dict[str, dict[str, float]]) -> str:
    return "\n".join(
        f"| {name} | `{_format_weights(weight_sets[name])}` |"
        for name in sorted(weight_sets)
    )


def _format_weights(weights: dict[str, float]) -> str:
    return ", ".join(f"{name}={weights[name]:.2f}" for name in FACTOR_NAMES)


def _format_results_table(results: pd.DataFrame) -> str:
    columns = [
        "case_id",
        "weight_set",
        "top_n",
        "total_return",
        "annualized_return",
        "annualized_volatility",
        "sharpe_ratio",
        "max_drawdown",
        "average_turnover",
        "total_transaction_cost_impact",
        "benchmark_total_return",
        "excess_total_return",
    ]
    headers = [
        "Case",
        "Weight set",
        "Top N",
        "Total return",
        "Annualized return",
        "Annualized volatility",
        "Sharpe ratio",
        "Max drawdown",
        "Average turnover",
        "Cost impact",
        "Benchmark total return",
        "Excess total return",
    ]
    separator = ["---", "---", "---:"] + ["---:" for _ in headers[3:]]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for _, row in results[columns].iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["case_id"]),
                    str(row["weight_set"]),
                    str(int(row["top_n"])),
                    _format_percent(row["total_return"]),
                    _format_percent(row["annualized_return"]),
                    _format_percent(row["annualized_volatility"]),
                    _format_float(row["sharpe_ratio"]),
                    _format_percent(row["max_drawdown"]),
                    _format_percent(row["average_turnover"]),
                    _format_percent(row["total_transaction_cost_impact"]),
                    _format_percent(row["benchmark_total_return"]),
                    _format_percent(row["excess_total_return"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _case_id_at_extreme(results: pd.DataFrame, column: str, direction: str) -> str:
    index = results[column].idxmin() if direction == "min" else results[column].idxmax()
    return str(results.loc[index, "case_id"])


def _format_percent(value: float) -> str:
    if pd.isna(value):
        return "NaN"
    return f"{value:.2%}"


def _format_float(value: float) -> str:
    if pd.isna(value):
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
    update_registry: bool = True,
) -> None:
    """Run the default synthetic parameter sweep."""

    run_synthetic_multifactor_parameter_sweep(
        report_path=report_path,
        experiment_log_path=experiment_log_path,
        update_registry=update_registry,
    )


if __name__ == "__main__":
    main()
