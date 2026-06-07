"""Synthetic local CSV fixture workflow demo.

This script exercises the committed local CSV fixture path end to end. It does
not use real market data, fetch data, connect to a broker, place orders,
support live trading, run a backtest, or make a profitability claim.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

import pandas as pd

from data.csv_loader import (
    CSVValidationSummary,
    load_benchmark_price_csv,
    load_ohlcv_csv,
    load_wide_price_csv,
)
from features.diagnostics import (
    factor_information_coefficient,
    factor_quantile_spread,
    factor_rank_information_coefficient,
)
from features.validation import (
    TrainValidationTestSplit,
    make_train_validation_test_split,
    split_panel_by_train_validation_test,
)
from features.liquidity import (
    average_daily_volume_eligibility,
    average_dollar_volume_eligibility,
    construct_liquidity_universe,
    LiquidityUniverseResult,
)
from features.worldquant_alphas import alpha_009, alpha_012
from reporting.experiment_log import (
    SYNTHETIC_RESEARCH_CAVEATS,
    resolve_experiment_log_path,
    write_experiment_log,
)
from reporting.experiment_registry import write_experiment_registry_report


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRICE_FIXTURE = "tests/fixtures/local_csv_loader_smoke/synthetic_adjusted_close.csv"
DEFAULT_BENCHMARK_FIXTURE = "tests/fixtures/local_csv_loader_smoke/synthetic_benchmark.csv"
DEFAULT_OHLCV_FIXTURE = "tests/fixtures/local_csv_loader_smoke/synthetic_ohlcv.csv"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "local_csv_fixture_workflow_demo.md"
DEFAULT_EXPERIMENT_LOG_PATH = (
    PROJECT_ROOT / "reports" / "experiment_logs" / "local_csv_fixture_workflow_demo.json"
)
SPLIT_NAMES = ("train", "validation", "test")


@dataclass(frozen=True)
class LocalCSVFixtureWorkflowConfig:
    """Configuration for the committed synthetic local CSV fixture workflow."""

    price_fixture: str = DEFAULT_PRICE_FIXTURE
    benchmark_fixture: str = DEFAULT_BENCHMARK_FIXTURE
    ohlcv_fixture: str = DEFAULT_OHLCV_FIXTURE
    alpha_window: int = 1
    forward_return_horizon_rows: int = 1
    ic_min_periods: int = 2
    quantiles: int = 3
    min_assets_per_quantile: int = 1
    train_end: str = "2024-01-02"
    validation_end: str = "2024-01-03"
    test_end: str | None = None
    liquidity_window: int = 2
    min_average_volume: float = 100_000.0
    min_average_dollar_volume: float = 11_000_000.0
    liquidity_eligibility_lag: int = 1
    liquidity_price_column: str = "adjusted_close"
    liquidity_universe_min_assets_per_date: int = 1


@dataclass(frozen=True)
class LocalCSVFixtureWorkflowResult:
    """Container for local CSV fixture workflow outputs."""

    prices: pd.DataFrame
    benchmark_prices: pd.Series
    ohlcv: pd.DataFrame
    price_summary: CSVValidationSummary
    benchmark_summary: CSVValidationSummary
    ohlcv_summary: CSVValidationSummary
    liquidity_price_panel: pd.DataFrame
    liquidity_volume_panel: pd.DataFrame
    average_daily_volume_eligibility: pd.DataFrame
    average_dollar_volume_eligibility: pd.DataFrame
    liquidity_eligibility_summary: pd.DataFrame
    liquidity_universe_result: LiquidityUniverseResult
    alpha_009_factor: pd.DataFrame
    alpha_012_factor: pd.DataFrame
    forward_returns: pd.DataFrame
    benchmark_forward_returns: pd.Series
    split: TrainValidationTestSplit
    alpha_009_factor_by_split: dict[str, pd.DataFrame]
    alpha_012_factor_by_split: dict[str, pd.DataFrame]
    forward_returns_by_split: dict[str, pd.DataFrame]
    information_coefficient: pd.Series
    rank_information_coefficient: pd.Series
    quantile_spread: pd.DataFrame
    alpha_012_information_coefficient: pd.Series
    alpha_012_rank_information_coefficient: pd.Series
    alpha_012_quantile_spread: pd.DataFrame
    information_coefficient_by_split: dict[str, pd.Series]
    rank_information_coefficient_by_split: dict[str, pd.Series]
    quantile_spread_by_split: dict[str, pd.DataFrame]
    alpha_012_information_coefficient_by_split: dict[str, pd.Series]
    alpha_012_rank_information_coefficient_by_split: dict[str, pd.Series]
    alpha_012_quantile_spread_by_split: dict[str, pd.DataFrame]
    split_summary: pd.DataFrame
    report_path: Path
    experiment_log_path: Path


def run_local_csv_fixture_workflow_demo(
    *,
    config: LocalCSVFixtureWorkflowConfig = LocalCSVFixtureWorkflowConfig(),
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
    write_outputs: bool = True,
    update_registry: bool = True,
) -> LocalCSVFixtureWorkflowResult:
    """Run the synthetic local CSV fixture workflow and optionally write outputs."""

    _validate_config(config)
    experiment_log_path = resolve_experiment_log_path(
        report_path,
        default_report_path=DEFAULT_REPORT_PATH,
        default_log_path=DEFAULT_EXPERIMENT_LOG_PATH,
    ) if experiment_log_path is None else experiment_log_path

    price_result = load_wide_price_csv(_resolve_project_fixture(config.price_fixture))
    benchmark_result = load_benchmark_price_csv(
        _resolve_project_fixture(config.benchmark_fixture),
    )
    ohlcv_result = load_ohlcv_csv(
        _resolve_project_fixture(config.ohlcv_fixture),
        require_adjusted_close=True,
    )
    prices = price_result.data
    benchmark_prices = benchmark_result.data
    ohlcv = ohlcv_result.data
    _validate_benchmark_alignment(prices, benchmark_prices)

    liquidity_price_panel = _pivot_ohlcv_panel(
        ohlcv,
        value_column=config.liquidity_price_column,
        index=prices.index,
        columns=prices.columns,
    )
    liquidity_volume_panel = _pivot_ohlcv_panel(
        ohlcv,
        value_column="volume",
        index=prices.index,
        columns=prices.columns,
    )
    adv_eligibility = average_daily_volume_eligibility(
        liquidity_volume_panel,
        window=config.liquidity_window,
        min_average_volume=config.min_average_volume,
        eligibility_lag=config.liquidity_eligibility_lag,
    )
    dollar_volume_eligibility = average_dollar_volume_eligibility(
        liquidity_price_panel,
        liquidity_volume_panel,
        window=config.liquidity_window,
        min_average_dollar_volume=config.min_average_dollar_volume,
        eligibility_lag=config.liquidity_eligibility_lag,
    )
    liquidity_eligibility_summary = summarize_liquidity_eligibility(
        volume_panel=liquidity_volume_panel,
        adv_eligibility=adv_eligibility,
        dollar_volume_eligibility=dollar_volume_eligibility,
    )
    liquidity_universe_result = construct_liquidity_universe(
        adv_eligibility & dollar_volume_eligibility,
        min_assets_per_date=config.liquidity_universe_min_assets_per_date,
        name="synthetic_fixture_liquidity_universe",
    )

    alpha_factor = alpha_009(prices, window=config.alpha_window)
    alpha_012_factor = alpha_012(liquidity_price_panel, liquidity_volume_panel)
    forward_returns = _future_returns(prices, periods=config.forward_return_horizon_rows)
    benchmark_forward_returns = _future_returns(
        benchmark_prices,
        periods=config.forward_return_horizon_rows,
    )
    split = make_train_validation_test_split(
        prices.index,
        train_end=config.train_end,
        validation_end=config.validation_end,
        test_end=config.test_end,
    )
    alpha_factor_by_split = split_panel_by_train_validation_test(
        alpha_factor,
        split,
        name="alpha_009_factor",
    )
    alpha_012_factor_by_split = split_panel_by_train_validation_test(
        alpha_012_factor,
        split,
        name="alpha_012_factor",
    )
    forward_returns_by_split = split_panel_by_train_validation_test(
        forward_returns,
        split,
        name="forward_returns",
    )

    information_coefficient = factor_information_coefficient(
        alpha_factor,
        forward_returns,
        min_periods=config.ic_min_periods,
    )
    rank_information_coefficient = factor_rank_information_coefficient(
        alpha_factor,
        forward_returns,
        min_periods=config.ic_min_periods,
    )
    quantile_spread = factor_quantile_spread(
        alpha_factor,
        forward_returns,
        quantiles=config.quantiles,
        min_assets_per_quantile=config.min_assets_per_quantile,
    )
    alpha_012_information_coefficient = factor_information_coefficient(
        alpha_012_factor,
        forward_returns,
        min_periods=config.ic_min_periods,
    )
    alpha_012_rank_information_coefficient = factor_rank_information_coefficient(
        alpha_012_factor,
        forward_returns,
        min_periods=config.ic_min_periods,
    )
    alpha_012_quantile_spread = factor_quantile_spread(
        alpha_012_factor,
        forward_returns,
        quantiles=config.quantiles,
        min_assets_per_quantile=config.min_assets_per_quantile,
    )
    information_coefficient_by_split = {
        split_name: factor_information_coefficient(
            alpha_factor_by_split[split_name],
            forward_returns_by_split[split_name],
            min_periods=config.ic_min_periods,
        )
        for split_name in SPLIT_NAMES
    }
    rank_information_coefficient_by_split = {
        split_name: factor_rank_information_coefficient(
            alpha_factor_by_split[split_name],
            forward_returns_by_split[split_name],
            min_periods=config.ic_min_periods,
        )
        for split_name in SPLIT_NAMES
    }
    quantile_spread_by_split = {
        split_name: factor_quantile_spread(
            alpha_factor_by_split[split_name],
            forward_returns_by_split[split_name],
            quantiles=config.quantiles,
            min_assets_per_quantile=config.min_assets_per_quantile,
        )
        for split_name in SPLIT_NAMES
    }
    alpha_012_information_coefficient_by_split = {
        split_name: factor_information_coefficient(
            alpha_012_factor_by_split[split_name],
            forward_returns_by_split[split_name],
            min_periods=config.ic_min_periods,
        )
        for split_name in SPLIT_NAMES
    }
    alpha_012_rank_information_coefficient_by_split = {
        split_name: factor_rank_information_coefficient(
            alpha_012_factor_by_split[split_name],
            forward_returns_by_split[split_name],
            min_periods=config.ic_min_periods,
        )
        for split_name in SPLIT_NAMES
    }
    alpha_012_quantile_spread_by_split = {
        split_name: factor_quantile_spread(
            alpha_012_factor_by_split[split_name],
            forward_returns_by_split[split_name],
            quantiles=config.quantiles,
            min_assets_per_quantile=config.min_assets_per_quantile,
        )
        for split_name in SPLIT_NAMES
    }
    split_summary = summarize_split_diagnostics(
        factor_by_split=alpha_factor_by_split,
        forward_returns_by_split=forward_returns_by_split,
        information_coefficient_by_split=information_coefficient_by_split,
        rank_information_coefficient_by_split=rank_information_coefficient_by_split,
        quantile_spread_by_split=quantile_spread_by_split,
    )

    result = LocalCSVFixtureWorkflowResult(
        prices=prices,
        benchmark_prices=benchmark_prices,
        ohlcv=ohlcv,
        price_summary=price_result.summary,
        benchmark_summary=benchmark_result.summary,
        ohlcv_summary=ohlcv_result.summary,
        liquidity_price_panel=liquidity_price_panel,
        liquidity_volume_panel=liquidity_volume_panel,
        average_daily_volume_eligibility=adv_eligibility,
        average_dollar_volume_eligibility=dollar_volume_eligibility,
        liquidity_eligibility_summary=liquidity_eligibility_summary,
        liquidity_universe_result=liquidity_universe_result,
        alpha_009_factor=alpha_factor,
        alpha_012_factor=alpha_012_factor,
        forward_returns=forward_returns,
        benchmark_forward_returns=benchmark_forward_returns,
        split=split,
        alpha_009_factor_by_split=alpha_factor_by_split,
        alpha_012_factor_by_split=alpha_012_factor_by_split,
        forward_returns_by_split=forward_returns_by_split,
        information_coefficient=information_coefficient,
        rank_information_coefficient=rank_information_coefficient,
        quantile_spread=quantile_spread,
        alpha_012_information_coefficient=alpha_012_information_coefficient,
        alpha_012_rank_information_coefficient=alpha_012_rank_information_coefficient,
        alpha_012_quantile_spread=alpha_012_quantile_spread,
        information_coefficient_by_split=information_coefficient_by_split,
        rank_information_coefficient_by_split=rank_information_coefficient_by_split,
        quantile_spread_by_split=quantile_spread_by_split,
        alpha_012_information_coefficient_by_split=(
            alpha_012_information_coefficient_by_split
        ),
        alpha_012_rank_information_coefficient_by_split=(
            alpha_012_rank_information_coefficient_by_split
        ),
        alpha_012_quantile_spread_by_split=alpha_012_quantile_spread_by_split,
        split_summary=split_summary,
        report_path=Path(report_path),
        experiment_log_path=Path(experiment_log_path),
    )

    if write_outputs:
        write_report(config=config, result=result)
        write_workflow_experiment_log(config=config, result=result)
        if _is_default_experiment_log_path(result.experiment_log_path) and update_registry:
            write_experiment_registry_report()

    return result


def summarize_liquidity_eligibility(
    *,
    volume_panel: pd.DataFrame,
    adv_eligibility: pd.DataFrame,
    dollar_volume_eligibility: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize synthetic liquidity eligibility counts by decision date."""

    if not adv_eligibility.index.equals(dollar_volume_eligibility.index):
        raise ValueError("liquidity eligibility masks must have identical indexes")
    if not adv_eligibility.columns.equals(dollar_volume_eligibility.columns):
        raise ValueError("liquidity eligibility masks must have identical columns")
    if not volume_panel.index.equals(adv_eligibility.index):
        raise ValueError("volume panel and eligibility masks must have identical indexes")
    if not volume_panel.columns.equals(adv_eligibility.columns):
        raise ValueError("volume panel and eligibility masks must have identical columns")

    both_eligible = adv_eligibility & dollar_volume_eligibility
    summary = pd.DataFrame(
        {
            "asset_count": len(volume_panel.columns),
            "volume_observed_asset_count": volume_panel.notna().sum(axis=1),
            "missing_volume_count": volume_panel.isna().sum(axis=1),
            "zero_volume_count": volume_panel.eq(0.0).sum(axis=1),
            "adv_eligible_count": adv_eligibility.sum(axis=1),
            "dollar_volume_eligible_count": dollar_volume_eligibility.sum(axis=1),
            "both_eligible_count": both_eligible.sum(axis=1),
        },
        index=volume_panel.index,
    )
    return summary.astype(int)


def summarize_split_diagnostics(
    *,
    factor_by_split: dict[str, pd.DataFrame],
    forward_returns_by_split: dict[str, pd.DataFrame],
    information_coefficient_by_split: dict[str, pd.Series],
    rank_information_coefficient_by_split: dict[str, pd.Series],
    quantile_spread_by_split: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Build per-split diagnostic coverage for the local CSV fixture workflow."""

    rows = []
    for split_name in SPLIT_NAMES:
        factor = factor_by_split[split_name]
        forward_returns = forward_returns_by_split[split_name]
        information_coefficient = information_coefficient_by_split[split_name]
        rank_information_coefficient = rank_information_coefficient_by_split[
            split_name
        ]
        quantile_spread = quantile_spread_by_split[split_name]
        rows.append(
            {
                "split": split_name,
                "date_count": int(len(factor.index)),
                "asset_count": int(factor.shape[1]),
                "factor_valid_observations": int(factor.notna().sum().sum()),
                "forward_return_valid_observations": int(
                    forward_returns.notna().sum().sum()
                ),
                "ic_valid_dates": int(information_coefficient.notna().sum()),
                "rank_ic_valid_dates": int(
                    rank_information_coefficient.notna().sum()
                ),
                "quantile_spread_valid_dates": int(
                    quantile_spread["top_minus_bottom_spread"].notna().sum()
                ),
                "mean_ic": float(information_coefficient.mean()),
                "mean_rank_ic": float(rank_information_coefficient.mean()),
            }
        )

    return pd.DataFrame.from_records(rows).set_index("split")


def write_workflow_experiment_log(
    *,
    config: LocalCSVFixtureWorkflowConfig,
    result: LocalCSVFixtureWorkflowResult,
) -> dict[str, object]:
    """Write a deterministic JSON log for the local CSV fixture workflow."""

    return write_experiment_log(
        log_path=result.experiment_log_path,
        experiment_id="local-csv-fixture-workflow-demo",
        title="Local CSV Fixture Workflow Demo",
        experiment_type="synthetic_local_csv_workflow",
        summary=(
            "Deterministic smoke demo that loads committed synthetic local CSV "
            "fixtures, computes alpha_009 and alpha_012 as research features, "
            "and evaluates diagnostic liquidity eligibility counts, IC, "
            "Rank IC, and quantile spread against aligned forward-return "
            "targets."
        ),
        config=config,
        assumptions={
            "data_scope": "synthetic only",
            "data_source": (
                "committed local CSV fixtures under tests/fixtures/local_csv_loader_smoke; "
                "no external data fetch"
            ),
            "price_fixture": config.price_fixture,
            "benchmark_fixture": config.benchmark_fixture,
            "ohlcv_fixture": config.ohlcv_fixture,
            "universe": f"{result.prices.shape[1]} synthetic fixture assets",
            "date_range": {
                "start": result.prices.index.min().date(),
                "end": result.prices.index.max().date(),
            },
            "liquidity_check": (
                "synthetic decision-date eligibility count smoke check only; "
                "not a tradeable universe-selection study"
            ),
            "liquidity_universe_check": (
                "synthetic universe-mask count smoke check only; not backtest "
                "integration, portfolio construction, or tradeability evidence"
            ),
            "liquidity_window": config.liquidity_window,
            "liquidity_eligibility_lag": config.liquidity_eligibility_lag,
            "liquidity_price_column": config.liquidity_price_column,
            "liquidity_universe_min_assets_per_date": (
                config.liquidity_universe_min_assets_per_date
            ),
            "min_average_volume": config.min_average_volume,
            "min_average_dollar_volume": config.min_average_dollar_volume,
            "liquidity_timing": (
                "rolling liquidity observations through date t are shifted by "
                "one row before appearing on a decision date; missing and "
                "zero-volume counts are reported separately and are not filled"
            ),
            "feature": f"alpha_009 with window={config.alpha_window}",
            "feature_timing": (
                "alpha_009 at date t uses close[t] and earlier closes only; "
                "no trade timing is defined in this demo"
            ),
            "alpha_012_feature": "alpha_012 from adjusted_close and volume OHLCV panels",
            "alpha_012_feature_timing": (
                "alpha_012 at date t uses adjusted_close[t], volume[t], and "
                "their one-row trailing anchors only; no trade timing is "
                "defined in this demo"
            ),
            "forward_return_timing": (
                "forward returns are computed after loading as evaluation "
                "targets only; they are not feature inputs"
            ),
            "split_policy": (
                "chronological train/validation/test date windows generated "
                "from the committed fixture index with no overlap, no "
                "reindexing, and no parameter selection"
            ),
            "split_timing": (
                "split labels are assigned by factor and evaluation-target "
                "row date; one-row forward-return targets are diagnostics "
                "only and are not used for parameter selection"
            ),
            "split_boundaries": _split_boundary_dict(result.split),
            "benchmark": "synthetic local CSV benchmark fixture",
            "missing_value_policy": (
                "strict loader defaults; no fill, forward-fill, backward-fill, "
                "or zero defaults"
            ),
            "portfolio_construction": "not included",
            "backtest_integration": "not included",
            "transaction_cost_model": "not applicable; no portfolio or trades",
            "slippage_model": "not applicable; no portfolio or trades",
            "live_trading": False,
            "brokerage_integration": False,
        },
        outputs={
            "markdown_report": _project_relative_path(result.report_path),
            "experiment_log": _project_relative_path(result.experiment_log_path),
            "price_rows": result.prices.shape[0],
            "asset_count": result.prices.shape[1],
            "benchmark_rows": int(result.benchmark_prices.shape[0]),
            "ohlcv_rows": int(result.ohlcv.shape[0]),
            "split_names": list(SPLIT_NAMES),
        },
        metrics={},
        diagnostics={
            "liquidity_eligibility_summary": _date_indexed_frame_to_dict(
                result.liquidity_eligibility_summary,
            ),
            "adv_eligible_counts_by_date": _series_to_date_dict(
                result.liquidity_eligibility_summary["adv_eligible_count"],
            ),
            "dollar_volume_eligible_counts_by_date": _series_to_date_dict(
                result.liquidity_eligibility_summary["dollar_volume_eligible_count"],
            ),
            "both_liquidity_rules_eligible_counts_by_date": _series_to_date_dict(
                result.liquidity_eligibility_summary["both_eligible_count"],
            ),
            "liquidity_universe_summary": _date_indexed_frame_to_dict(
                result.liquidity_universe_result.summary,
            ),
            "liquidity_universe_counts_by_date": _series_to_date_dict(
                result.liquidity_universe_result.summary["universe_count"],
            ),
            "liquidity_universe_low_coverage_dates": [
                date.date().isoformat()
                for date in result.liquidity_universe_result.low_coverage_dates
            ],
            "split_summary": result.split_summary.to_dict(orient="index"),
            "information_coefficient_by_date": _series_to_date_dict(
                result.information_coefficient,
            ),
            "rank_information_coefficient_by_date": _series_to_date_dict(
                result.rank_information_coefficient,
            ),
            "information_coefficient_by_split": {
                split_name: _series_to_date_dict(series)
                for split_name, series in result.information_coefficient_by_split.items()
            },
            "rank_information_coefficient_by_split": {
                split_name: _series_to_date_dict(series)
                for split_name, series in result.rank_information_coefficient_by_split.items()
            },
            "quantile_spread_valid_dates_by_split": {
                split_name: int(
                    frame["top_minus_bottom_spread"].notna().sum()
                )
                for split_name, frame in result.quantile_spread_by_split.items()
            },
            "quantile_spread_valid_dates": int(
                result.quantile_spread["top_minus_bottom_spread"].notna().sum()
            ),
            "alpha_012_information_coefficient_by_date": _series_to_date_dict(
                result.alpha_012_information_coefficient,
            ),
            "alpha_012_rank_information_coefficient_by_date": _series_to_date_dict(
                result.alpha_012_rank_information_coefficient,
            ),
            "alpha_012_information_coefficient_by_split": {
                split_name: _series_to_date_dict(series)
                for split_name, series in result.alpha_012_information_coefficient_by_split.items()
            },
            "alpha_012_rank_information_coefficient_by_split": {
                split_name: _series_to_date_dict(series)
                for split_name, series in result.alpha_012_rank_information_coefficient_by_split.items()
            },
            "alpha_012_quantile_spread_valid_dates_by_split": {
                split_name: int(
                    frame["top_minus_bottom_spread"].notna().sum()
                )
                for split_name, frame in result.alpha_012_quantile_spread_by_split.items()
            },
            "alpha_012_quantile_spread_valid_dates": int(
                result.alpha_012_quantile_spread["top_minus_bottom_spread"].notna().sum()
            ),
            "factor_valid_observations": int(result.alpha_009_factor.notna().sum().sum()),
            "alpha_009_factor_valid_observations": int(result.alpha_009_factor.notna().sum().sum()),
            "alpha_012_factor_valid_observations": int(result.alpha_012_factor.notna().sum().sum()),
            "forward_return_valid_observations": int(result.forward_returns.notna().sum().sum()),
            "benchmark_forward_return_valid_observations": int(
                result.benchmark_forward_returns.notna().sum()
            ),
        },
        caveats=(
            *SYNTHETIC_RESEARCH_CAVEATS,
            "local CSV fixture smoke demo only",
            "split-aware wiring check only",
            "liquidity eligibility count smoke check only",
            "liquidity universe mask count smoke check only",
            "not backtest universe integration",
            "not tradeability evidence",
            "not strategy validation",
            "not model selection",
            "not evidence of real-world performance",
        ),
        next_action=(
            "Use this as a local CSV fixture wiring check only; a real "
            "user-provided local CSV study still requires readiness-audit "
            "approval, explicit sample splits, universe rules, benchmark "
            "selection, costs, slippage assumptions, and full caveats."
        ),
    )


def write_report(
    *,
    config: LocalCSVFixtureWorkflowConfig,
    result: LocalCSVFixtureWorkflowResult,
) -> None:
    """Write a deterministic Markdown report for the local CSV fixture workflow."""

    result.report_path.parent.mkdir(parents=True, exist_ok=True)

    content = f"""# Local CSV Fixture Workflow Demo

This report uses committed synthetic local CSV fixtures only. It is not real-market evidence, not financial advice, and not a profitability claim. It does not run a backtest, construct a portfolio, fetch real data, connect to a broker, place orders, or support live trading.

## Purpose

Exercise the local CSV research path with a small committed fixture:

1. Load a wide adjusted-close CSV with the strict local loader.
2. Load a benchmark CSV and verify date alignment.
3. Load a synthetic OHLCV CSV for a liquidity eligibility count smoke check.
4. Compute lagged ADV and dollar-volume eligibility masks without filling missing volume.
5. Construct a synthetic liquidity universe mask count diagnostic from the intersection of both eligibility rules.
6. Compute `alpha_009` as a close-only research feature.
7. Compute `alpha_012` as a volume + close research feature from the OHLCV fixture.
8. Compute next-row forward returns as evaluation targets only.
9. Apply chronological train/validation/test split metadata.
10. Run IC, Rank IC, and quantile spread diagnostics.
11. Write a caveated report and JSON experiment log.

## Inputs

| Item | Value |
| --- | --- |
| Price fixture | `{config.price_fixture}` |
| Benchmark fixture | `{config.benchmark_fixture}` |
| OHLCV fixture | `{config.ohlcv_fixture}` |
| Price schema | `{result.price_summary.schema}` |
| Benchmark schema | `{result.benchmark_summary.schema}` |
| OHLCV schema | `{result.ohlcv_summary.schema}` |
| Price rows | `{result.price_summary.source_row_count}` |
| OHLCV rows | `{result.ohlcv_summary.source_row_count}` |
| Asset columns | `{", ".join(result.price_summary.columns)}` |
| Date range | `{result.prices.index.min().date()}` to `{result.prices.index.max().date()}` |
| Train end | `{result.split.train_end.date()}` |
| Validation end | `{result.split.validation_end.date()}` |
| Test end | `{result.split.test_end.date()}` |
| Missing price values | `{result.price_summary.missing_value_count}` |
| Missing benchmark values | `{result.benchmark_summary.missing_value_count}` |

## Processing Summary

The workflow preserves the loader output date index and asset columns, verifies that the benchmark dates match the price panel dates, computes `alpha_009` with `window={config.alpha_window}`, and computes `alpha_012` from the synthetic OHLCV `adjusted_close` and `volume` panels. Forward returns are aligned to the same date as the factor value for diagnostic evaluation only; they are not used as feature inputs.

The train/validation/test metadata is a chronological fixture split by factor and evaluation-target row date only. The one-row forward returns are diagnostic labels, not feature inputs, and are not used for parameter selection. This tiny fixture split is not model selection, parameter tuning, strategy validation, or real-market evidence.

No missing values were filled. No dates or assets were reindexed. No portfolio construction, execution timing, transaction cost model, slippage model, or backtest is included.

## Liquidity Eligibility Smoke Check

The workflow loads the committed synthetic OHLCV fixture and pivots `{config.liquidity_price_column}` and `volume` into panels aligned to the adjusted-close fixture's dates and assets. Missing OHLCV rows after that alignment remain missing; there is no fill, forward-fill, backward-fill, interpolation, or zero default.

Eligibility counts below are decision-date diagnostics only. They use `window={config.liquidity_window}`, `eligibility_lag={config.liquidity_eligibility_lag}`, `min_average_volume={_format_float(config.min_average_volume)}`, and `min_average_dollar_volume={_format_float(config.min_average_dollar_volume)}`. They do not run a strategy, construct a portfolio, or validate market tradability.

{_format_markdown_table(result.liquidity_eligibility_summary)}

## Liquidity Universe Mask Smoke Check

The synthetic universe mask below is constructed from the intersection of the ADV and dollar-volume eligibility masks. It reports count and audit fields from `construct_liquidity_universe()` only. It does not create target weights, trades, positions, orders, returns, benchmark comparisons, or a tradeable universe claim.

{_format_markdown_table(result.liquidity_universe_result.summary)}

## Split Coverage

{_format_labeled_index_markdown_table(result.split_summary, index_label="split")}

## Alpha#009 Diagnostic Coverage

| Diagnostic | Value |
| --- | ---: |
| Factor valid observations | `{int(result.alpha_009_factor.notna().sum().sum())}` |
| Forward-return valid observations | `{int(result.forward_returns.notna().sum().sum())}` |
| Benchmark forward-return valid observations | `{int(result.benchmark_forward_returns.notna().sum())}` |
| IC valid dates | `{int(result.information_coefficient.notna().sum())}` |
| Rank IC valid dates | `{int(result.rank_information_coefficient.notna().sum())}` |
| Quantile spread valid dates | `{int(result.quantile_spread["top_minus_bottom_spread"].notna().sum())}` |

## Alpha#009 Information Coefficient Diagnostics

{_format_series_table(result.information_coefficient)}

## Alpha#009 Rank Information Coefficient Diagnostics

{_format_series_table(result.rank_information_coefficient)}

## Alpha#009 Quantile Spread Diagnostics

{_format_markdown_table(result.quantile_spread)}

## Alpha#012 Diagnostic Coverage

`alpha_012` uses only the synthetic OHLCV dates and assets with available adjusted close and volume anchors. Missing OHLCV rows remain missing after alignment to the wider adjusted-close fixture. These diagnostics are feature-evaluation wiring checks only, not strategy validation.

| Diagnostic | Value |
| --- | ---: |
| Factor valid observations | `{int(result.alpha_012_factor.notna().sum().sum())}` |
| Forward-return valid observations | `{int(result.forward_returns.notna().sum().sum())}` |
| IC valid dates | `{int(result.alpha_012_information_coefficient.notna().sum())}` |
| Rank IC valid dates | `{int(result.alpha_012_rank_information_coefficient.notna().sum())}` |
| Quantile spread valid dates | `{int(result.alpha_012_quantile_spread["top_minus_bottom_spread"].notna().sum())}` |

## Alpha#012 Information Coefficient Diagnostics

{_format_series_table(result.alpha_012_information_coefficient)}

## Alpha#012 Rank Information Coefficient Diagnostics

{_format_series_table(result.alpha_012_rank_information_coefficient)}

## Alpha#012 Quantile Spread Diagnostics

{_format_markdown_table(result.alpha_012_quantile_spread)}

## Limitations

- The CSV files are tiny synthetic fixtures committed for workflow testing.
- The benchmark is synthetic and used only to verify local CSV date alignment.
- The diagnostic returns are synthetic fixture calculations, not market evidence.
- The liquidity eligibility and universe-mask counts are synthetic decision-date diagnostics, not tradeability evidence or backtest universe integration.
- `alpha_009` is a research feature, not a complete strategy.
- `alpha_012` is a research feature, not a complete strategy.
- The split metadata is a wiring check for the committed fixture, not a train/validation/test study on real data.
- No local CSV result here should be interpreted without the real-data readiness audit and full experiment-log requirements.
- User-provided local CSV research, universe construction, costs, slippage, and QuantConnect/LEAN implementation remain future stages.
"""

    result.report_path.write_text(content, encoding="utf-8")


def _future_returns(values: pd.DataFrame | pd.Series, *, periods: int) -> pd.DataFrame | pd.Series:
    return values.pct_change(periods=periods, fill_method=None).shift(-periods)


def _resolve_project_fixture(relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        raise ValueError("fixture paths must be project-relative")

    resolved = (PROJECT_ROOT / path).resolve()
    if not resolved.is_relative_to(PROJECT_ROOT):
        raise ValueError("fixture paths must stay inside the project")
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return resolved


def _validate_config(config: LocalCSVFixtureWorkflowConfig) -> None:
    if isinstance(config.alpha_window, bool) or not isinstance(config.alpha_window, int):
        raise TypeError("alpha_window must be an integer")
    if config.alpha_window < 1:
        raise ValueError("alpha_window must be at least 1")
    if (
        isinstance(config.forward_return_horizon_rows, bool)
        or not isinstance(config.forward_return_horizon_rows, int)
    ):
        raise TypeError("forward_return_horizon_rows must be an integer")
    if config.forward_return_horizon_rows < 1:
        raise ValueError("forward_return_horizon_rows must be at least 1")
    if isinstance(config.ic_min_periods, bool) or not isinstance(config.ic_min_periods, int):
        raise TypeError("ic_min_periods must be an integer")
    if config.ic_min_periods < 2:
        raise ValueError("ic_min_periods must be at least 2")
    if isinstance(config.quantiles, bool) or not isinstance(config.quantiles, int):
        raise TypeError("quantiles must be an integer")
    if config.quantiles < 2:
        raise ValueError("quantiles must be at least 2")
    if (
        isinstance(config.min_assets_per_quantile, bool)
        or not isinstance(config.min_assets_per_quantile, int)
    ):
        raise TypeError("min_assets_per_quantile must be an integer")
    if config.min_assets_per_quantile < 1:
        raise ValueError("min_assets_per_quantile must be at least 1")
    if (
        isinstance(config.liquidity_window, bool)
        or not isinstance(config.liquidity_window, int)
    ):
        raise TypeError("liquidity_window must be an integer")
    if config.liquidity_window < 1:
        raise ValueError("liquidity_window must be at least 1")
    if (
        isinstance(config.liquidity_eligibility_lag, bool)
        or not isinstance(config.liquidity_eligibility_lag, int)
    ):
        raise TypeError("liquidity_eligibility_lag must be an integer")
    if config.liquidity_eligibility_lag < 1:
        raise ValueError("liquidity_eligibility_lag must be at least 1")
    _validate_positive_finite_float(
        config.min_average_volume,
        "min_average_volume",
    )
    _validate_positive_finite_float(
        config.min_average_dollar_volume,
        "min_average_dollar_volume",
    )
    if config.liquidity_price_column not in {"close", "adjusted_close"}:
        raise ValueError("liquidity_price_column must be 'close' or 'adjusted_close'")
    if (
        isinstance(config.liquidity_universe_min_assets_per_date, bool)
        or not isinstance(config.liquidity_universe_min_assets_per_date, int)
    ):
        raise TypeError("liquidity_universe_min_assets_per_date must be an integer")
    if config.liquidity_universe_min_assets_per_date < 1:
        raise ValueError("liquidity_universe_min_assets_per_date must be at least 1")


def _validate_benchmark_alignment(prices: pd.DataFrame, benchmark: pd.Series) -> None:
    if not benchmark.index.equals(prices.index):
        raise ValueError("benchmark fixture dates must match price fixture dates")


def _validate_positive_finite_float(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    if not math.isfinite(float(value)) or float(value) <= 0.0:
        raise ValueError(f"{name} must be a positive finite value")


def _pivot_ohlcv_panel(
    frame: pd.DataFrame,
    *,
    value_column: str,
    index: pd.DatetimeIndex,
    columns: pd.Index,
) -> pd.DataFrame:
    if value_column not in frame.columns:
        raise ValueError(f"OHLCV fixture is missing {value_column}")

    panel = frame.pivot(index="date", columns="symbol", values=value_column)
    panel = panel.sort_index()
    panel.columns.name = None
    panel = panel.reindex(index=index, columns=columns)
    panel.index.name = index.name
    return panel.astype(float)


def _split_boundary_dict(split: TrainValidationTestSplit) -> dict[str, str]:
    return {
        "train_end": split.train_end.date().isoformat(),
        "validation_end": split.validation_end.date().isoformat(),
        "test_end": split.test_end.date().isoformat(),
    }


def _is_default_experiment_log_path(path: Path) -> bool:
    return Path(path).resolve() == DEFAULT_EXPERIMENT_LOG_PATH.resolve()


def _series_to_date_dict(series: pd.Series) -> dict[str, float]:
    return {
        pd.Timestamp(index).date().isoformat(): float(value)
        for index, value in series.items()
    }


def _date_indexed_frame_to_dict(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    return {
        pd.Timestamp(index).date().isoformat(): {
            str(column): _json_scalar(column, value)
            for column, value in row.items()
        }
        for index, row in frame.iterrows()
    }


def _format_series_table(series: pd.Series) -> str:
    frame = series.to_frame()
    return _format_markdown_table(frame)


def _format_markdown_table(frame: pd.DataFrame) -> str:
    headers = ["Date", *[str(column) for column in frame.columns]]
    separator = ["---", *["---:" for _ in frame.columns]]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for index, row in frame.iterrows():
        values = [
            _format_table_value(column, value)
            for column, value in row.items()
        ]
        lines.append(
            "| "
            + " | ".join([pd.Timestamp(index).date().isoformat(), *values])
            + " |"
        )
    return "\n".join(lines)


def _format_labeled_index_markdown_table(
    frame: pd.DataFrame,
    *,
    index_label: str,
) -> str:
    headers = [index_label, *[str(column) for column in frame.columns]]
    separator = ["---", *["---:" for _ in frame.columns]]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for index, row in frame.iterrows():
        values = [
            _format_table_value(column, value)
            for column, value in row.items()
        ]
        lines.append("| " + " | ".join([str(index), *values]) + " |")
    return "\n".join(lines)


def _format_table_value(column: object, value: object) -> str:
    if pd.isna(value):
        return "NaN"

    column_name = str(column)
    if column_name == "low_coverage":
        return str(bool(value)).lower()
    if (
        column_name.endswith("_count")
        or column_name.endswith("_observations")
        or column_name.endswith("_valid_dates")
        or column_name == "valid_asset_count"
    ):
        return str(int(value))

    return _format_float(float(value))


def _format_float(value: float) -> str:
    if pd.isna(value):
        return "NaN"
    return f"{value:.4f}"


def _json_scalar(column: object, value: object) -> object:
    if str(column) == "low_coverage":
        return bool(value)
    if pd.isna(value):
        return None
    return float(value)


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
    """Run the default synthetic local CSV fixture workflow."""

    run_local_csv_fixture_workflow_demo(
        report_path=report_path,
        experiment_log_path=experiment_log_path,
        update_registry=update_registry,
    )


if __name__ == "__main__":
    main()
