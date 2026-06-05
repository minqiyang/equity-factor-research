"""Synthetic split-aware IC / Rank IC diagnostic demo.

This script applies the train/validation/test split helper to deterministic
synthetic factor and forward-return panels. It does not use real market data,
fetch data, select factors, train models, run a backtest, place orders, support
live trading, or make a profitability claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from features.diagnostics import (
    factor_information_coefficient,
    factor_rank_information_coefficient,
)
from features.validation import (
    TrainValidationTestSplit,
    make_train_validation_test_split,
    split_panel_by_train_validation_test,
)
from reporting.experiment_log import (
    SYNTHETIC_RESEARCH_CAVEATS,
    resolve_experiment_log_path,
    write_experiment_log,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "synthetic_split_ic_rank_ic_demo.md"
DEFAULT_EXPERIMENT_LOG_PATH = (
    PROJECT_ROOT / "reports" / "experiment_logs" / "synthetic_split_ic_rank_ic_demo.json"
)
SPLIT_NAMES = ("train", "validation", "test")


@dataclass(frozen=True)
class SyntheticSplitICRankICConfig:
    """Configuration for the deterministic split-aware diagnostic demo."""

    asset_count: int = 6
    periods: int = 12
    start_date: str = "2024-01-02"
    train_end: str = "2024-01-05"
    validation_end: str = "2024-01-11"
    test_end: str | None = None
    ic_min_periods: int = 3


@dataclass(frozen=True)
class SyntheticSplitICRankICResult:
    """Container for synthetic split-aware diagnostic outputs."""

    factor: pd.DataFrame
    forward_returns: pd.DataFrame
    split: TrainValidationTestSplit
    factor_by_split: dict[str, pd.DataFrame]
    forward_returns_by_split: dict[str, pd.DataFrame]
    information_coefficient_by_split: dict[str, pd.Series]
    rank_information_coefficient_by_split: dict[str, pd.Series]
    summary: pd.DataFrame
    report_path: Path
    experiment_log_path: Path


def run_synthetic_split_ic_rank_ic_demo(
    *,
    config: SyntheticSplitICRankICConfig = SyntheticSplitICRankICConfig(),
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
    write_outputs: bool = True,
) -> SyntheticSplitICRankICResult:
    """Run a deterministic split-aware IC / Rank IC diagnostic demo."""

    _validate_config(config)
    experiment_log_path = (
        resolve_experiment_log_path(
            report_path,
            default_report_path=DEFAULT_REPORT_PATH,
            default_log_path=DEFAULT_EXPERIMENT_LOG_PATH,
        )
        if experiment_log_path is None
        else experiment_log_path
    )

    factor = generate_synthetic_factor_panel(config)
    split = make_train_validation_test_split(
        factor.index,
        train_end=config.train_end,
        validation_end=config.validation_end,
        test_end=config.test_end,
    )
    forward_returns = generate_synthetic_forward_returns(factor, split)

    factor_by_split = split_panel_by_train_validation_test(
        factor,
        split,
        name="synthetic_factor",
    )
    forward_returns_by_split = split_panel_by_train_validation_test(
        forward_returns,
        split,
        name="synthetic_forward_returns",
    )
    information_coefficient_by_split = {
        split_name: factor_information_coefficient(
            factor_by_split[split_name],
            forward_returns_by_split[split_name],
            min_periods=config.ic_min_periods,
        )
        for split_name in SPLIT_NAMES
    }
    rank_information_coefficient_by_split = {
        split_name: factor_rank_information_coefficient(
            factor_by_split[split_name],
            forward_returns_by_split[split_name],
            min_periods=config.ic_min_periods,
        )
        for split_name in SPLIT_NAMES
    }
    summary = summarize_split_diagnostics(
        factor_by_split=factor_by_split,
        forward_returns_by_split=forward_returns_by_split,
        information_coefficient_by_split=information_coefficient_by_split,
        rank_information_coefficient_by_split=rank_information_coefficient_by_split,
    )

    result = SyntheticSplitICRankICResult(
        factor=factor,
        forward_returns=forward_returns,
        split=split,
        factor_by_split=factor_by_split,
        forward_returns_by_split=forward_returns_by_split,
        information_coefficient_by_split=information_coefficient_by_split,
        rank_information_coefficient_by_split=rank_information_coefficient_by_split,
        summary=summary,
        report_path=Path(report_path),
        experiment_log_path=Path(experiment_log_path),
    )

    if write_outputs:
        write_report(config=config, result=result)
        write_demo_experiment_log(config=config, result=result)

    return result


def generate_synthetic_factor_panel(
    config: SyntheticSplitICRankICConfig = SyntheticSplitICRankICConfig(),
) -> pd.DataFrame:
    """Generate a deterministic synthetic factor panel."""

    _validate_config(config)
    dates = pd.bdate_range(config.start_date, periods=config.periods)
    assets = [f"ASSET_{asset_id:02d}" for asset_id in range(1, config.asset_count + 1)]
    asset_gradient = np.linspace(-1.0, 1.0, config.asset_count).reshape(1, -1)
    time_gradient = np.linspace(-0.20, 0.20, config.periods).reshape(-1, 1)
    values = asset_gradient + time_gradient
    factor = pd.DataFrame(values, index=dates, columns=assets)

    if config.asset_count >= 4 and config.periods >= 8:
        factor.iloc[5, 1] = np.nan

    return factor


def generate_synthetic_forward_returns(
    factor: pd.DataFrame,
    split: TrainValidationTestSplit,
) -> pd.DataFrame:
    """Create deterministic synthetic forward-return targets by split."""

    coefficients = {
        "train": 0.010,
        "validation": -0.010,
        "test": 0.006,
    }
    forward_returns = factor.copy()
    for split_name, dates in split.as_dict().items():
        forward_returns.loc[dates] = factor.loc[dates] * coefficients[split_name]

    if forward_returns.shape[0] >= 11 and forward_returns.shape[1] >= 4:
        forward_returns.iloc[-2, 3] = np.nan

    return forward_returns


def summarize_split_diagnostics(
    *,
    factor_by_split: dict[str, pd.DataFrame],
    forward_returns_by_split: dict[str, pd.DataFrame],
    information_coefficient_by_split: dict[str, pd.Series],
    rank_information_coefficient_by_split: dict[str, pd.Series],
) -> pd.DataFrame:
    """Build a compact per-split diagnostic coverage summary."""

    rows = []
    for split_name in SPLIT_NAMES:
        factor = factor_by_split[split_name]
        forward_returns = forward_returns_by_split[split_name]
        information_coefficient = information_coefficient_by_split[split_name]
        rank_information_coefficient = rank_information_coefficient_by_split[
            split_name
        ]
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
                "mean_ic": float(information_coefficient.mean()),
                "mean_rank_ic": float(rank_information_coefficient.mean()),
            }
        )

    return pd.DataFrame.from_records(rows).set_index("split")


def write_demo_experiment_log(
    *,
    config: SyntheticSplitICRankICConfig,
    result: SyntheticSplitICRankICResult,
) -> dict[str, object]:
    """Write a deterministic JSON log for the split-aware diagnostic demo."""

    return write_experiment_log(
        log_path=result.experiment_log_path,
        experiment_id="synthetic-split-ic-rank-ic-demo",
        title="Synthetic Split-Aware IC / Rank IC Demo",
        experiment_type="synthetic_split_diagnostic_demo",
        summary=(
            "Deterministic synthetic demo that applies train/validation/test "
            "splits to factor and forward-return panels before computing IC "
            "and Rank IC diagnostics."
        ),
        config=config,
        assumptions={
            "data_scope": "synthetic only",
            "data_source": "local deterministic panels; no external data fetch",
            "universe": f"{config.asset_count} synthetic assets",
            "date_range": {
                "start": result.factor.index.min().date(),
                "end": result.factor.index.max().date(),
            },
            "split_policy": (
                "chronological train/validation/test date windows with no "
                "overlap and no reindexing"
            ),
            "forward_return_timing": (
                "forward returns are synthetic evaluation targets only and "
                "are not feature inputs"
            ),
            "missing_value_policy": (
                "missing values are preserved; no fill, forward-fill, "
                "backward-fill, or zero defaults"
            ),
            "portfolio_construction": "not included",
            "backtest_integration": "not included",
            "live_trading": False,
            "brokerage_integration": False,
        },
        outputs={
            "markdown_report": _project_relative_path(result.report_path),
            "experiment_log": _project_relative_path(result.experiment_log_path),
            "split_names": list(SPLIT_NAMES),
            "factor_rows": int(result.factor.shape[0]),
            "asset_count": int(result.factor.shape[1]),
        },
        metrics={},
        diagnostics={
            "summary": result.summary.to_dict(orient="index"),
            "information_coefficient_by_split": {
                split_name: _series_to_date_dict(series)
                for split_name, series in result.information_coefficient_by_split.items()
            },
            "rank_information_coefficient_by_split": {
                split_name: _series_to_date_dict(series)
                for split_name, series in result.rank_information_coefficient_by_split.items()
            },
        },
        caveats=(
            *SYNTHETIC_RESEARCH_CAVEATS,
            "diagnostics only",
            "not strategy validation",
            "not model selection",
        ),
        next_action=(
            "Use this as a split-aware diagnostic wiring check only; real "
            "user-provided local CSV research still requires readiness-audit "
            "approval, benchmark and universe rules, costs, slippage "
            "assumptions, and full experiment records."
        ),
    )


def write_report(
    *,
    config: SyntheticSplitICRankICConfig,
    result: SyntheticSplitICRankICResult,
) -> None:
    """Write a deterministic Markdown report for the split-aware demo."""

    result.report_path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# Synthetic Split-Aware IC / Rank IC Demo

This report uses deterministic synthetic panels only. It is not real-market evidence, not financial advice, and not a profitability claim. It does not fetch real data, run a backtest, construct a portfolio, connect to a broker, place orders, or support live trading.

## Purpose

Apply the train/validation/test split helper to already-prepared synthetic factor and forward-return panels before running diagnostic IC and Rank IC calculations.

## Configuration

| Item | Value |
| --- | --- |
| Asset count | `{config.asset_count}` |
| Periods | `{config.periods}` |
| Date range | `{result.factor.index.min().date()}` to `{result.factor.index.max().date()}` |
| Train end | `{result.split.train_end.date()}` |
| Validation end | `{result.split.validation_end.date()}` |
| Test end | `{result.split.test_end.date()}` |
| IC min periods | `{config.ic_min_periods}` |

## Split Coverage

{_format_markdown_table(result.summary)}

## Information Coefficient By Split

{_format_split_series(result.information_coefficient_by_split)}

## Rank Information Coefficient By Split

{_format_split_series(result.rank_information_coefficient_by_split)}

## Limitations

- The factor and forward-return panels are synthetic and deterministic.
- Forward returns are evaluation targets only; they are never used as feature inputs.
- The split summary is a diagnostic wiring check, not model selection.
- No portfolio construction, transaction costs, slippage, benchmark, or backtest is included.
- This report is not evidence that any factor works on real market data.
"""
    result.report_path.write_text(content, encoding="utf-8")


def _validate_config(config: SyntheticSplitICRankICConfig) -> None:
    if isinstance(config.asset_count, bool) or not isinstance(config.asset_count, int):
        raise TypeError("asset_count must be an integer")
    if config.asset_count < 3:
        raise ValueError("asset_count must be at least 3")
    if isinstance(config.periods, bool) or not isinstance(config.periods, int):
        raise TypeError("periods must be an integer")
    if config.periods < 6:
        raise ValueError("periods must be at least 6")
    if isinstance(config.ic_min_periods, bool) or not isinstance(config.ic_min_periods, int):
        raise TypeError("ic_min_periods must be an integer")
    if config.ic_min_periods < 2:
        raise ValueError("ic_min_periods must be at least 2")
    if config.ic_min_periods > config.asset_count:
        raise ValueError("ic_min_periods must be no larger than asset_count")


def _format_split_series(series_by_split: dict[str, pd.Series]) -> str:
    rows = []
    for split_name in SPLIT_NAMES:
        for date, value in series_by_split[split_name].items():
            rows.append(
                {
                    "split": split_name,
                    "date": pd.Timestamp(date).date().isoformat(),
                    "value": value,
                }
            )
    frame = pd.DataFrame.from_records(rows)
    return _format_markdown_table(frame.set_index(["split", "date"]))


def _format_markdown_table(frame: pd.DataFrame) -> str:
    index_names = [name if name is not None else "index" for name in frame.index.names]
    headers = [*index_names, *[str(column) for column in frame.columns]]
    separator = ["---" for _ in index_names] + ["---:" for _ in frame.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for index, row in frame.iterrows():
        index_values = index if isinstance(index, tuple) else (index,)
        row_values = [_format_table_value(value) for value in row]
        lines.append(
            "| "
            + " | ".join([*(str(value) for value in index_values), *row_values])
            + " |"
        )
    return "\n".join(lines)


def _format_table_value(value: object) -> str:
    if pd.isna(value):
        return "NaN"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return f"{float(value):.4f}"


def _series_to_date_dict(series: pd.Series) -> dict[str, float | None]:
    return {
        pd.Timestamp(index).date().isoformat(): None if pd.isna(value) else float(value)
        for index, value in series.items()
    }


def _project_relative_path(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def main(
    report_path: Path = DEFAULT_REPORT_PATH,
    experiment_log_path: Path | None = None,
) -> None:
    """Run the default synthetic split-aware IC / Rank IC demo."""

    run_synthetic_split_ic_rank_ic_demo(
        report_path=report_path,
        experiment_log_path=experiment_log_path,
    )


if __name__ == "__main__":
    main()
