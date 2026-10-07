"""Private EODHD local CSV factor diagnostics dry run.

This module uses already-local CSV files and existing strict loaders. It writes
diagnostic summaries only; it does not fetch data, run a strategy, run a
backtest, build a portfolio, or make performance claims.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from data.csv_loader import load_benchmark_price_csv, load_ohlcv_csv
from features.diagnostics import (
    factor_information_coefficient,
    factor_quantile_spread,
    factor_rank_information_coefficient,
)
from features.validation import (
    TrainValidationTestSplit,
    make_price_forward_return_labels,
    make_train_validation_test_split,
    resolve_diagnostic_classification,
    split_label_panel_by_train_validation_test,
    split_panel_by_train_validation_test,
    summarize_label_availability,
)
from features.worldquant_alphas import alpha_009, alpha_012


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_NAME = "FACTOR_DIAGNOSTICS_DRY_RUN_SUMMARY.md"
SPLIT_NAMES = ("train", "validation", "test")


@dataclass(frozen=True)
class EODHDFactorDiagnosticsConfig:
    """Configuration for the private EODHD factor diagnostics dry run."""

    ohlcv_path: Path
    benchmark_path: Path
    output_path: Path
    alpha_window: int = 5
    forward_return_horizon_rows: int = 1
    ic_min_periods: int = 2
    quantiles: int = 5
    min_assets_per_quantile: int = 1
    train_start: str = "2020-01-09"
    train_end: str = "2021-12-31"
    validation_start: str = "2022-01-03"
    validation_end: str = "2023-12-29"
    test_start: str = "2024-01-02"
    test_end: str = "2025-04-30"
    embargo_rows: int = 0
    feature_warm_up_rows: int = 5


@dataclass(frozen=True)
class EODHDFactorDiagnosticsResult:
    """Dry-run diagnostics returned for tests and final summaries."""

    output_path: Path
    asset_row_count: int
    benchmark_row_count: int
    symbol_count: int
    factor_summary: pd.DataFrame
    split: TrainValidationTestSplit
    forward_returns: pd.DataFrame
    benchmark_forward_returns: pd.Series
    forward_returns_by_split: dict[str, pd.DataFrame]
    benchmark_forward_returns_by_split: dict[str, pd.Series]
    label_availability: pd.DataFrame
    benchmark_label_availability: pd.DataFrame
    split_summary: pd.DataFrame


def run_eodhd_factor_diagnostics_dry_run(
    config: EODHDFactorDiagnosticsConfig,
) -> EODHDFactorDiagnosticsResult:
    """Run the no-strategy private EODHD factor diagnostics dry run."""

    _validate_config(config)
    asset_result = load_ohlcv_csv(config.ohlcv_path, require_adjusted_close=True)
    benchmark_ohlcv = load_ohlcv_csv(config.benchmark_path, require_adjusted_close=True)
    benchmark_prices = load_benchmark_price_csv(
        config.benchmark_path,
        value_column="adjusted_close",
    ).data

    ohlcv = asset_result.data
    close = _pivot_ohlcv_panel(ohlcv, "adjusted_close")
    volume = _pivot_ohlcv_panel(ohlcv, "volume").reindex(index=close.index, columns=close.columns)
    _validate_benchmark_alignment(close, benchmark_prices)

    split = make_train_validation_test_split(
        close.index,
        train_start=config.train_start,
        train_end=config.train_end,
        validation_start=config.validation_start,
        validation_end=config.validation_end,
        test_start=config.test_start,
        test_end=config.test_end,
        label_kind="price_forward_return",
        label_derivation="adjusted_close_row_forward_return_v1",
        label_horizon_rows=config.forward_return_horizon_rows,
        embargo_rows=config.embargo_rows,
        feature_warm_up_rows=config.feature_warm_up_rows,
    )
    forward_returns = make_price_forward_return_labels(
        close,
        split,
        name="adjusted_close",
    )
    benchmark_forward_returns = make_price_forward_return_labels(
        benchmark_prices,
        split,
        name="benchmark_adjusted_close",
    )
    assert isinstance(forward_returns, pd.DataFrame)
    assert isinstance(benchmark_forward_returns, pd.Series)
    forward_returns_by_split = split_label_panel_by_train_validation_test(
        forward_returns,
        split,
        name="forward_returns",
    )
    benchmark_forward_returns_by_split = (
        split_label_panel_by_train_validation_test(
            benchmark_forward_returns,
            split,
            name="benchmark_forward_returns",
        )
    )

    factors = {
        "alpha_009": alpha_009(close, window=config.alpha_window),
        "alpha_012": alpha_012(close, volume),
    }
    factor_summary = _summarize_factors(factors)
    label_availability = summarize_label_availability(
        forward_returns,
        split,
        factors=factors,
        name="forward_returns",
    )
    benchmark_label_availability = _summarize_benchmark_label_availability(
        benchmark_forward_returns,
        split,
    )
    split_summary = _summarize_split_diagnostics(
        factors=factors,
        forward_returns_by_split=forward_returns_by_split,
        label_availability=label_availability,
        split=split,
        config=config,
    )

    result = EODHDFactorDiagnosticsResult(
        output_path=config.output_path,
        asset_row_count=int(len(ohlcv)),
        benchmark_row_count=int(len(benchmark_ohlcv.data)),
        symbol_count=int(len(set(ohlcv["symbol"]) | set(benchmark_ohlcv.data["symbol"]))),
        factor_summary=factor_summary,
        split=split,
        forward_returns=forward_returns,
        benchmark_forward_returns=benchmark_forward_returns,
        forward_returns_by_split=forward_returns_by_split,
        benchmark_forward_returns_by_split=benchmark_forward_returns_by_split,
        label_availability=label_availability,
        benchmark_label_availability=benchmark_label_availability,
        split_summary=split_summary,
    )
    _write_summary(result, config)
    return result


def _validate_config(config: EODHDFactorDiagnosticsConfig) -> None:
    if PROJECT_ROOT in config.output_path.resolve().parents:
        raise ValueError("output_path must be outside the repository")
    if config.forward_return_horizon_rows < 1:
        raise ValueError("forward_return_horizon_rows must be at least 1")
    if config.feature_warm_up_rows < max(config.alpha_window, 1):
        raise ValueError(
            "feature_warm_up_rows must cover the maximum factor history"
        )


def _pivot_ohlcv_panel(frame: pd.DataFrame, value_column: str) -> pd.DataFrame:
    panel = frame.pivot(index="date", columns="symbol", values=value_column)
    panel = panel.sort_index()
    panel.columns.name = None
    panel.index.name = "date"
    return panel.astype(float)


def _validate_benchmark_alignment(prices: pd.DataFrame, benchmark: pd.Series) -> None:
    if not benchmark.index.equals(prices.index):
        raise ValueError("benchmark dates must match asset price dates")


def _summarize_factors(factors: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, factor in factors.items():
        total = int(factor.size)
        valid = int(factor.notna().sum().sum())
        rows.append(
            {
                "factor": name,
                "date_count": int(len(factor.index)),
                "asset_count": int(factor.shape[1]),
                "valid_observations": valid,
                "missing_observations": total - valid,
            }
        )
    return pd.DataFrame.from_records(rows).set_index("factor")


def _summarize_split_diagnostics(
    *,
    factors: dict[str, pd.DataFrame],
    forward_returns_by_split: dict[str, pd.DataFrame],
    label_availability: pd.DataFrame,
    split,
    config: EODHDFactorDiagnosticsConfig,
) -> pd.DataFrame:
    rows = []
    for factor_name, factor in factors.items():
        factor_by_split = split_panel_by_train_validation_test(
            factor,
            split,
            panel_role="feature",
            name=factor_name,
        )
        ic_by_split = {
            name: factor_information_coefficient(
                factor_by_split[name],
                forward_returns_by_split[name],
                min_periods=config.ic_min_periods,
            )
            for name in SPLIT_NAMES
        }
        rank_ic_by_split = {
            name: factor_rank_information_coefficient(
                factor_by_split[name],
                forward_returns_by_split[name],
                min_periods=config.ic_min_periods,
            )
            for name in SPLIT_NAMES
        }
        spread_by_split = {
            name: factor_quantile_spread(
                factor_by_split[name],
                forward_returns_by_split[name],
                quantiles=config.quantiles,
                min_assets_per_quantile=config.min_assets_per_quantile,
            )
            for name in SPLIT_NAMES
        }
        for split_name in SPLIT_NAMES:
            split_factor = factor_by_split[split_name]
            availability = label_availability.loc[split_name]
            if isinstance(availability, pd.DataFrame):
                availability = availability.loc[
                    availability["factor"].eq(factor_name)
                ].iloc[0]
            ic_valid_dates = int(ic_by_split[split_name].notna().sum())
            rank_ic_valid_dates = int(
                rank_ic_by_split[split_name].notna().sum()
            )
            quantile_spread_valid_dates = int(
                spread_by_split[split_name][
                    "top_minus_bottom_spread"
                ].notna().sum()
            )
            invalid_reason, status = resolve_diagnostic_classification(
                availability_invalid_reason=availability["invalid_reason"],
                metric_valid_date_counts={
                    "ic": ic_valid_dates,
                    "rank_ic": rank_ic_valid_dates,
                    "quantile_spread": quantile_spread_valid_dates,
                },
            )
            rows.append(
                {
                    "factor": factor_name,
                    "split": split_name,
                    "date_count": int(len(split_factor.index)),
                    "factor_valid_observations": int(split_factor.notna().sum().sum()),
                    "forward_return_valid_observations": int(
                        forward_returns_by_split[split_name].notna().sum().sum()
                    ),
                    "eligible_date_count": int(
                        availability["eligible_date_count"]
                    ),
                    "valid_eligible_target_cells": int(
                        availability["valid_eligible_target_cells"]
                    ),
                    "missing_eligible_target_cells": int(
                        availability["missing_eligible_target_cells"]
                    ),
                    "usable_factor_label_pairs": int(
                        availability["usable_factor_label_pairs"]
                    ),
                    "has_usable_label_pairs": bool(
                        availability["has_usable_label_pairs"]
                    ),
                    "ic_valid_dates": ic_valid_dates,
                    "rank_ic_valid_dates": rank_ic_valid_dates,
                    "quantile_spread_valid_dates": (
                        quantile_spread_valid_dates
                    ),
                    "mean_ic": float(ic_by_split[split_name].mean()),
                    "mean_rank_ic": float(rank_ic_by_split[split_name].mean()),
                    "mean_quantile_spread": float(
                        spread_by_split[split_name]["top_minus_bottom_spread"].mean()
                    ),
                    "invalid_reason": invalid_reason,
                    "status": status,
                }
            )

    return pd.DataFrame.from_records(rows)


def _summarize_benchmark_label_availability(
    benchmark_forward_returns: pd.Series,
    split: TrainValidationTestSplit,
) -> pd.DataFrame:
    records = []
    for split_name in SPLIT_NAMES:
        metadata = split.window_metadata[split_name]
        eligible = benchmark_forward_returns.loc[metadata.eligible_dates]
        valid_count = int(eligible.notna().sum())
        if not metadata.has_eligible_labels:
            invalid_reason = "no_eligible_labels"
        elif valid_count == 0:
            invalid_reason = "no_valid_eligible_targets"
        else:
            invalid_reason = None
        records.append(
            {
                "split": split_name,
                "eligible_date_count": metadata.eligible_date_count,
                "total_eligible_target_cells": int(len(eligible)),
                "valid_eligible_target_cells": valid_count,
                "missing_eligible_target_cells": int(
                    len(eligible) - valid_count
                ),
                "invalid_reason": invalid_reason,
                "status": (
                    "INVALID"
                    if invalid_reason is not None
                    else "DIAGNOSTIC_ONLY"
                ),
            }
        )
    return pd.DataFrame.from_records(records).set_index("split")


def _write_summary(
    result: EODHDFactorDiagnosticsResult,
    config: EODHDFactorDiagnosticsConfig,
) -> None:
    output = config.output_path
    output.parent.mkdir(parents=True, exist_ok=True)
    contract_summary = result.split.window_summary()[
        [
            "configured_start",
            "configured_end",
            "realized_start",
            "realized_end",
            "candidate_date_count",
            "eligible_date_count",
            "purged_date_count",
            "embargoed_date_count",
            "invalid_reason",
            "status",
        ]
    ].reset_index()
    content = "\n".join(
        [
            "# EODHD Factor Diagnostics Dry Run Summary",
            "",
            "Scope: no-strategy local CSV factor diagnostics using existing strict loaders.",
            "No strategy, backtest, portfolio construction, PnL, Sharpe, drawdown, trade simulation, or trading-readiness interpretation was performed.",
            "",
            "## Private Inputs",
            "",
            f"- OHLCV: `{config.ohlcv_path}`",
            f"- Benchmark: `{config.benchmark_path}`",
            f"- Output: `{config.output_path}`",
            "",
            "## Row Counts",
            "",
            f"- Asset rows: {result.asset_row_count}",
            f"- Benchmark rows: {result.benchmark_row_count}",
            f"- Symbol coverage: {result.symbol_count}",
            "",
            "## Factor Coverage",
            "",
            _markdown_table(result.factor_summary.reset_index()),
            "",
            "## Label Contract",
            "",
            f"- Label kind: `{result.split.label_kind}`",
            f"- Label derivation: `{result.split.label_derivation}`",
            f"- Label horizon rows: `{result.split.label_horizon_rows}`",
            f"- Embargo rows: `{result.split.embargo_rows}`",
            "",
            _markdown_table(contract_summary),
            "",
            "## Benchmark Label Availability",
            "",
            _markdown_table(
                result.benchmark_label_availability.reset_index()
            ),
            "",
            "## Split Diagnostics",
            "",
            _markdown_table(result.split_summary),
            "",
            "## Caveats",
            "",
            "- Diagnostics are research checks only, not strategy validation.",
            "- The selected universe is static and not point-in-time membership.",
            "- Raw OHLC fields and adjusted_close may have different adjustment semantics.",
            "- IC, Rank IC, and quantile spread are diagnostic calculations only.",
            "",
        ]
    )
    output.write_text(content, encoding="utf-8")


def _markdown_table(frame: pd.DataFrame) -> str:
    columns = [str(column) for column in frame.columns]
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in frame.itertuples(index=False):
        rows.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_path", type=Path, help="Private EODHD bundle directory.")
    bundle = parser.parse_args(argv).bundle_path
    result = run_eodhd_factor_diagnostics_dry_run(
        EODHDFactorDiagnosticsConfig(
            ohlcv_path=bundle / "normalized" / "eodhd_ohlcv_long.csv",
            benchmark_path=bundle / "normalized" / "eodhd_benchmark_spy.csv",
            output_path=bundle / OUTPUT_NAME,
        )
    )
    print(f"SUMMARY_PATH={result.output_path}")
    print(f"ASSET_ROWS={result.asset_row_count}")
    print(f"BENCHMARK_ROWS={result.benchmark_row_count}")
    print(f"SYMBOL_COVERAGE={result.symbol_count}")


if __name__ == "__main__":
    main()
