"""Synthetic-data 12-1 momentum research demo.

This script demonstrates the local research workflow without fetching or using
real market data. The generated results are synthetic diagnostics only and must
not be interpreted as evidence of real-world strategy profitability.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.portfolio import BacktestResult, run_long_only_backtest
from features.momentum import calculate_12_1_momentum
from reporting.experiment_log import (
    SYNTHETIC_RESEARCH_CAVEATS,
    resolve_experiment_log_path,
    write_experiment_log,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "synthetic_momentum_demo.md"
DEFAULT_EXPERIMENT_LOG_PATH = PROJECT_ROOT / "reports" / "experiment_logs" / "synthetic_momentum_demo.json"


@dataclass(frozen=True)
class SyntheticDemoConfig:
    """Configuration for the deterministic synthetic momentum demo."""

    seed: int = 20260521
    asset_count: int = 20
    periods: int = 756
    start_date: str = "2021-01-01"
    starting_price: float = 100.0
    lookback_periods: int = 252
    skip_periods: int = 21
    rebalance_frequency: str = "ME"
    top_n: int = 5
    transaction_cost_bps: float = 10.0
    slippage_bps: float = 0.0
    periods_per_year: int = 252


def generate_synthetic_prices(config: SyntheticDemoConfig = SyntheticDemoConfig()) -> pd.DataFrame:
    """Generate deterministic synthetic prices for a cross-sectional demo.

    The model combines a shared market component, asset-specific noise, and
    mild asset-level drift differences. It is intentionally simple and is not
    calibrated to real equities.
    """

    rng = np.random.default_rng(config.seed)
    dates = pd.bdate_range(config.start_date, periods=config.periods)
    tickers = [f"ASSET_{asset_id:02d}" for asset_id in range(1, config.asset_count + 1)]

    market_component = rng.normal(loc=0.0002, scale=0.0060, size=(config.periods, 1))
    asset_noise = rng.normal(loc=0.0, scale=0.0120, size=(config.periods, config.asset_count))
    asset_drifts = rng.normal(loc=0.00005, scale=0.00020, size=(1, config.asset_count))

    log_returns = market_component + asset_noise + asset_drifts
    prices = config.starting_price * np.exp(np.cumsum(log_returns, axis=0))

    return pd.DataFrame(prices, index=dates, columns=tickers)


def build_equal_weight_benchmark(prices: pd.DataFrame, *, starting_price: float = 100.0) -> pd.Series:
    """Build a synthetic equal-weight universe benchmark price series."""

    daily_returns = prices.pct_change(fill_method=None).mean(axis=1).fillna(0.0)
    return (starting_price * (1.0 + daily_returns).cumprod()).rename("synthetic_equal_weight_benchmark")


def run_synthetic_momentum_demo(
    *,
    config: SyntheticDemoConfig = SyntheticDemoConfig(),
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
) -> BacktestResult:
    """Run the synthetic 12-1 momentum workflow and write a Markdown report."""

    experiment_log_path = resolve_experiment_log_path(
        report_path,
        default_report_path=DEFAULT_REPORT_PATH,
        default_log_path=DEFAULT_EXPERIMENT_LOG_PATH,
    ) if experiment_log_path is None else experiment_log_path

    prices = generate_synthetic_prices(config)
    momentum = calculate_12_1_momentum(
        prices,
        lookback_periods=config.lookback_periods,
        skip_periods=config.skip_periods,
    )
    benchmark = build_equal_weight_benchmark(prices, starting_price=config.starting_price)

    result = run_long_only_backtest(
        prices,
        momentum,
        rebalance_frequency=config.rebalance_frequency,
        top_n=config.top_n,
        transaction_cost_bps=config.transaction_cost_bps,
        slippage_bps=config.slippage_bps,
        benchmark_prices=benchmark,
        signal_lag_periods=1,
        periods_per_year=config.periods_per_year,
    )

    write_report(
        report_path=report_path,
        config=config,
        prices=prices,
        result=result,
    )
    write_demo_experiment_log(
        log_path=experiment_log_path,
        report_path=report_path,
        config=config,
        prices=prices,
        result=result,
    )
    return result


def write_demo_experiment_log(
    *,
    log_path: Path,
    report_path: Path,
    config: SyntheticDemoConfig,
    prices: pd.DataFrame,
    result: BacktestResult,
) -> dict[str, object]:
    """Write a deterministic JSON log for the synthetic momentum demo."""

    return write_experiment_log(
        log_path=log_path,
        experiment_id="synthetic-momentum-demo",
        title="Synthetic Momentum Demo",
        experiment_type="synthetic_backtest_smoke_test",
        summary=(
            "Deterministic synthetic 12-1 momentum workflow that generates local "
            "synthetic prices, computes a lagged momentum signal, and runs the "
            "existing long-only backtester as a smoke test with explicit fixed-bps "
            "cost and slippage assumptions."
        ),
        config=config,
        assumptions={
            "data_scope": "synthetic only",
            "data_source": "local deterministic generator; no external data fetch",
            "universe": f"{config.asset_count} synthetic assets",
            "date_range": {
                "start": prices.index.min().date(),
                "end": prices.index.max().date(),
            },
            "feature_timing": (
                "12-1 momentum uses shifted historical price anchors; signal lag "
                "keeps portfolio formation after signal availability"
            ),
            "execution_timing": result.assumptions["execution_timing"],
            "rebalance_frequency": config.rebalance_frequency,
            "benchmark": "synthetic equal-weight universe benchmark",
            "transaction_cost_model": (
                f"{result.assumptions['cost_model']}; "
                f"{config.transaction_cost_bps:.2f} bps per unit of target-weight turnover"
            ),
            "transaction_cost_bps": config.transaction_cost_bps,
            "slippage_model": (
                f"{result.assumptions['slippage_model']}; "
                f"{config.slippage_bps:.2f} bps per unit of target-weight turnover"
            ),
            "slippage_bps": config.slippage_bps,
            "zero_cost_or_slippage_is_diagnostic": result.assumptions[
                "zero_cost_or_slippage_is_diagnostic"
            ],
            "turnover_model": result.assumptions["turnover_model"],
            "live_trading": False,
            "brokerage_integration": False,
        },
        outputs={
            "markdown_report": _project_relative_path(report_path),
            "experiment_log": _project_relative_path(log_path),
            "holdings_rows": result.holdings.shape[0],
            "holdings_assets": result.holdings.shape[1],
        },
        metrics=result.metrics,
        caveats=(
            *SYNTHETIC_RESEARCH_CAVEATS,
            "workflow diagnostics only",
            "not evidence of real-world strategy performance",
        ),
        next_action=(
            "Use as a reproducible smoke-test log only; real-data experiments "
            "still require explicit data-source, universe, slippage, benchmark, "
            "and validation-split documentation."
        ),
    )


def write_report(
    *,
    report_path: Path,
    config: SyntheticDemoConfig,
    prices: pd.DataFrame,
    result: BacktestResult,
) -> None:
    """Write a concise synthetic-demo report to disk."""

    report_path.parent.mkdir(parents=True, exist_ok=True)
    metrics = result.metrics

    content = f"""# Synthetic Momentum Demo

This report was generated from synthetic data only. It does not use real market data, does not support live trading, and is not evidence of real-world strategy profitability.

## Purpose

Demonstrate the local research workflow:

1. Generate synthetic prices for 20 assets.
2. Compute 12-1 month momentum.
3. Run a long-only, top-ranked, equal-weight backtest.
4. Include fixed transaction costs.
5. Record explicit fixed-bps slippage assumptions.
6. Record basic metrics and limitations.

## Configuration

- Random seed: `{config.seed}`
- Asset count: `{config.asset_count}`
- Price rows: `{len(prices)}`
- Date range: `{prices.index.min().date()}` to `{prices.index.max().date()}`
- Momentum lookback periods: `{config.lookback_periods}`
- Momentum skipped recent periods: `{config.skip_periods}`
- Rebalance frequency: `{config.rebalance_frequency}`
- Selected assets per rebalance: `{config.top_n}`
- Transaction cost: `{config.transaction_cost_bps:.2f}` bps per unit of target-weight turnover
- Slippage: `{config.slippage_bps:.2f}` bps per unit of target-weight turnover
- Zero cost or slippage diagnostic: `{result.assumptions["zero_cost_or_slippage_is_diagnostic"]}`
- Benchmark: synthetic equal-weight universe benchmark
- Execution timing: {result.assumptions["execution_timing"]}

## Metrics

| Metric | Value |
| --- | ---: |
| Total return | {_format_percent(metrics["total_return"])} |
| Annualized return | {_format_percent(metrics["annualized_return"])} |
| Annualized volatility | {_format_percent(metrics["annualized_volatility"])} |
| Sharpe ratio | {_format_number(metrics["sharpe_ratio"])} |
| Max drawdown | {_format_percent(metrics["max_drawdown"])} |
| Average turnover | {_format_percent(metrics["average_turnover"])} |
| Total turnover | {_format_number(metrics["total_turnover"])} |
| Total transaction cost impact | {_format_percent(metrics["total_transaction_cost_impact"])} |
| Total slippage cost impact | {_format_percent(metrics["total_slippage_cost_impact"])} |
| Total trading cost impact | {_format_percent(metrics["total_trading_cost_impact"])} |
| Benchmark total return | {_format_percent(metrics["benchmark_total_return"])} |
| Excess total return vs synthetic benchmark | {_format_percent(metrics["excess_total_return"])} |

## Limitations

- Synthetic prices are not calibrated to actual equities.
- There is no survivorship-bias, delisting, borrow, tax, liquidity, or market-impact model.
- The backtester uses simplified target-weight turnover, not drift-adjusted trade accounting.
- The zero-slippage setting is a diagnostic simplification, not an execution-realism claim.
- Results depend on the synthetic random seed and are workflow diagnostics only.
- No claim of strategy profitability is made.

## Next Action

Use this demo as a smoke test for the research pipeline. Before using real data,
add explicit data-source documentation, universe construction rules, benchmark
selection, and train/validation/test split definitions.
"""

    report_path.write_text(content, encoding="utf-8")


def _format_percent(value: float) -> str:
    if pd.isna(value):
        return "NaN"
    return f"{value:.2%}"


def _format_number(value: float) -> str:
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
) -> None:
    """Run the synthetic momentum demo with default settings."""

    run_synthetic_momentum_demo(
        report_path=report_path,
        experiment_log_path=experiment_log_path,
    )


if __name__ == "__main__":
    main()
