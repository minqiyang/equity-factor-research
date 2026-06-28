"""Private EODHD local CSV factor diagnostics dry run.

This module uses already-local CSV files and existing strict loaders. It writes
diagnostic summaries only; it does not fetch data, run a strategy, run a
backtest, build a portfolio, or make performance claims.
"""

from __future__ import annotations

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
    make_train_validation_test_split,
    split_panel_by_train_validation_test,
)
from features.worldquant_alphas import alpha_009, alpha_012


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = Path("/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run")
DEFAULT_OUTPUT = DEFAULT_BUNDLE / "FACTOR_DIAGNOSTICS_DRY_RUN_SUMMARY.md"
SPLIT_NAMES = ("train", "validation", "test")


@dataclass(frozen=True)
class EODHDFactorDiagnosticsConfig:
    """Configuration for the private EODHD factor diagnostics dry run."""

    ohlcv_path: Path = DEFAULT_BUNDLE / "normalized" / "eodhd_ohlcv_long.csv"
    benchmark_path: Path = DEFAULT_BUNDLE / "normalized" / "eodhd_benchmark_spy.csv"
    output_path: Path = DEFAULT_OUTPUT
    alpha_window: int = 5
    forward_return_horizon_rows: int = 1
    ic_min_periods: int = 2
    quantiles: int = 5
    min_assets_per_quantile: int = 1
    train_end: str = "2021-12-31"
    validation_end: str = "2023-12-29"
    test_end: str | None = None


@dataclass(frozen=True)
class EODHDFactorDiagnosticsResult:
    """Dry-run diagnostics returned for tests and final summaries."""

    output_path: Path
    asset_row_count: int
    benchmark_row_count: int
    symbol_count: int
    factor_summary: pd.DataFrame
    split_summary: pd.DataFrame


def run_eodhd_factor_diagnostics_dry_run(
    config: EODHDFactorDiagnosticsConfig = EODHDFactorDiagnosticsConfig(),
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

    forward_returns = _future_returns(close, periods=config.forward_return_horizon_rows)
    split = make_train_validation_test_split(
        close.index,
        train_end=config.train_end,
        validation_end=config.validation_end,
        test_end=config.test_end,
    )
    forward_returns_by_split = split_panel_by_train_validation_test(
        forward_returns,
        split,
        name="forward_returns",
    )

    factors = {
        "alpha_009": alpha_009(close, window=config.alpha_window),
        "alpha_012": alpha_012(close, volume),
    }
    factor_summary = _summarize_factors(factors)
    split_summary = _summarize_split_diagnostics(
        factors=factors,
        forward_returns=forward_returns,
        forward_returns_by_split=forward_returns_by_split,
        split=split,
        config=config,
    )

    result = EODHDFactorDiagnosticsResult(
        output_path=config.output_path,
        asset_row_count=int(len(ohlcv)),
        benchmark_row_count=int(len(benchmark_ohlcv.data)),
        symbol_count=int(len(set(ohlcv["symbol"]) | set(benchmark_ohlcv.data["symbol"]))),
        factor_summary=factor_summary,
        split_summary=split_summary,
    )
    _write_summary(result, config)
    return result


def _validate_config(config: EODHDFactorDiagnosticsConfig) -> None:
    if PROJECT_ROOT in config.output_path.resolve().parents:
        raise ValueError("output_path must be outside the repository")
    if config.forward_return_horizon_rows < 1:
        raise ValueError("forward_return_horizon_rows must be at least 1")


def _pivot_ohlcv_panel(frame: pd.DataFrame, value_column: str) -> pd.DataFrame:
    panel = frame.pivot(index="date", columns="symbol", values=value_column)
    panel = panel.sort_index()
    panel.columns.name = None
    panel.index.name = "date"
    return panel.astype(float)


def _validate_benchmark_alignment(prices: pd.DataFrame, benchmark: pd.Series) -> None:
    if not benchmark.index.equals(prices.index):
        raise ValueError("benchmark dates must match asset price dates")


def _future_returns(values: pd.DataFrame, *, periods: int) -> pd.DataFrame:
    return values.pct_change(periods=periods, fill_method=None).shift(-periods)


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
    forward_returns: pd.DataFrame,
    forward_returns_by_split: dict[str, pd.DataFrame],
    split,
    config: EODHDFactorDiagnosticsConfig,
) -> pd.DataFrame:
    rows = []
    for factor_name, factor in factors.items():
        factor_by_split = split_panel_by_train_validation_test(
            factor,
            split,
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
            rows.append(
                {
                    "factor": factor_name,
                    "split": split_name,
                    "date_count": int(len(split_factor.index)),
                    "factor_valid_observations": int(split_factor.notna().sum().sum()),
                    "forward_return_valid_observations": int(
                        forward_returns_by_split[split_name].notna().sum().sum()
                    ),
                    "ic_valid_dates": int(ic_by_split[split_name].notna().sum()),
                    "rank_ic_valid_dates": int(rank_ic_by_split[split_name].notna().sum()),
                    "quantile_spread_valid_dates": int(
                        spread_by_split[split_name]["top_minus_bottom_spread"].notna().sum()
                    ),
                    "mean_ic": float(ic_by_split[split_name].mean()),
                    "mean_rank_ic": float(rank_ic_by_split[split_name].mean()),
                    "mean_quantile_spread": float(
                        spread_by_split[split_name]["top_minus_bottom_spread"].mean()
                    ),
                }
            )

    return pd.DataFrame.from_records(rows)


def _write_summary(
    result: EODHDFactorDiagnosticsResult,
    config: EODHDFactorDiagnosticsConfig,
) -> None:
    output = config.output_path
    output.parent.mkdir(parents=True, exist_ok=True)
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


def main() -> None:
    result = run_eodhd_factor_diagnostics_dry_run()
    print(f"SUMMARY_PATH={result.output_path}")
    print(f"ASSET_ROWS={result.asset_row_count}")
    print(f"BENCHMARK_ROWS={result.benchmark_row_count}")
    print(f"SYMBOL_COVERAGE={result.symbol_count}")


if __name__ == "__main__":
    main()
