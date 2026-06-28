"""Private limited EODHD factor-diagnostics review.

This module summarizes already-computed diagnostics from a private dry-run
summary. It does not fetch data, calculate factors, run a strategy, or
interpret performance.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from research.eodhd_factor_diagnostics_experiment_log import _parse_markdown_table


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = Path("/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run")
DEFAULT_DRY_RUN_SUMMARY = DEFAULT_BUNDLE / "FACTOR_DIAGNOSTICS_DRY_RUN_SUMMARY.md"
DEFAULT_EXPERIMENT_LOG = DEFAULT_BUNDLE / "FACTOR_DIAGNOSTICS_EXPERIMENT_LOG.json"
DEFAULT_READINESS_REVIEW = DEFAULT_BUNDLE / "FACTOR_DIAGNOSTICS_READINESS_REVIEW.json"
DEFAULT_OUTPUT_JSON = DEFAULT_BUNDLE / "LIMITED_FACTOR_DIAGNOSTICS_REVIEW.json"
DEFAULT_OUTPUT_MARKDOWN = DEFAULT_BUNDLE / "LIMITED_FACTOR_DIAGNOSTICS_REVIEW.md"

ALLOWED_DIAGNOSTICS = [
    "factor coverage",
    "factor missingness",
    "IC",
    "Rank IC",
    "quantile spread",
    "split labels",
]
FORBIDDEN_INTERPRETATIONS = [
    "strategy run",
    "backtest",
    "portfolio construction",
    "trade simulation",
    "PnL",
    "Sharpe",
    "drawdown",
    "performance interpretation",
    "investment recommendation",
    "profitability claim",
    "alpha claim",
    "trading-readiness claim",
]
REQUIRED_INPUT_FORBIDDEN_INTERPRETATIONS = [
    item for item in FORBIDDEN_INTERPRETATIONS if item != "investment recommendation"
]


@dataclass(frozen=True)
class EODHDLimitedFactorDiagnosticsReviewConfig:
    bundle_path: Path = DEFAULT_BUNDLE
    dry_run_summary_path: Path = DEFAULT_DRY_RUN_SUMMARY
    readiness_review_path: Path = DEFAULT_READINESS_REVIEW
    experiment_log_path: Path = DEFAULT_EXPERIMENT_LOG
    output_json_path: Path = DEFAULT_OUTPUT_JSON
    output_markdown_path: Path = DEFAULT_OUTPUT_MARKDOWN


def run_eodhd_limited_factor_diagnostics_review(
    config: EODHDLimitedFactorDiagnosticsReviewConfig = (
        EODHDLimitedFactorDiagnosticsReviewConfig()
    ),
) -> dict[str, Any]:
    """Write a private limited review of already-computed diagnostics."""

    _validate_config(config)
    dry_run_summary = _read_text(config.dry_run_summary_path)
    readiness_review = _read_json(config.readiness_review_path)
    experiment_log = _read_json(config.experiment_log_path)
    _validate_ready(readiness_review)
    _validate_experiment_log_scope(experiment_log)

    factor_coverage = _factor_coverage_by_name(dry_run_summary)
    split_diagnostics = _split_diagnostic_rows(dry_run_summary)
    split_labels = sorted({row["split"] for row in split_diagnostics})
    payload: dict[str, Any] = {
        "schema_version": 1,
        "review_scope": "limited_factor_diagnostics_review",
        "diagnostics_are_research_only": True,
        "input_file_paths": {
            "dry_run_summary": str(config.dry_run_summary_path),
            "readiness_review": str(config.readiness_review_path),
            "experiment_log": str(config.experiment_log_path),
        },
        "output_file_paths": {
            "limited_review_json": str(config.output_json_path),
            "limited_review_markdown": str(config.output_markdown_path),
        },
        "input_readiness": {
            "ready_for_limited_factor_diagnostics_review": readiness_review[
                "ready_for_limited_factor_diagnostics_review"
            ],
        },
        "summary_counts": readiness_review["summary_counts"],
        "date_range": readiness_review["date_range"],
        "allowed_diagnostics_reviewed": ALLOWED_DIAGNOSTICS,
        "forbidden_interpretations": FORBIDDEN_INTERPRETATIONS,
        "factor_coverage": factor_coverage,
        "factor_missingness": {
            factor: {
                "missing_observations": values["missing_observations"],
                "total_observations": values["total_observations"],
                "missing_fraction": values["missing_fraction"],
            }
            for factor, values in factor_coverage.items()
        },
        "split_labels": split_labels,
        "split_diagnostics": split_diagnostics,
        "neutral_diagnostics_statement": (
            "Diagnostics are summarized as research diagnostics only and are not "
            "strategy, portfolio, trading, investment, alpha, or profitability evidence."
        ),
        "no_strategy_no_performance_statement": (
            "No strategy, backtest, portfolio construction, PnL, Sharpe, drawdown, "
            "investment recommendation, profitability claim, alpha claim, or "
            "trading-readiness claim was made."
        ),
        "next_checkpoint": (
            "Preserve the no-strategy/no-performance boundary before any future "
            "methodology or data-readiness decision."
        ),
    }
    config.output_json_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    config.output_markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
    return payload


def _validate_config(config: EODHDLimitedFactorDiagnosticsReviewConfig) -> None:
    bundle = config.bundle_path.resolve()
    for field_name, path in (
        ("dry_run_summary_path", config.dry_run_summary_path),
        ("readiness_review_path", config.readiness_review_path),
        ("experiment_log_path", config.experiment_log_path),
        ("output_json_path", config.output_json_path),
        ("output_markdown_path", config.output_markdown_path),
    ):
        resolved = path.resolve()
        if not _is_under(resolved, bundle):
            raise ValueError(f"{field_name} must be under bundle_path")
        if field_name.startswith("output_") and PROJECT_ROOT in resolved.parents:
            raise ValueError(f"{field_name} must be outside the repository")


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"{path} is empty")
    return text


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _validate_ready(readiness_review: dict[str, Any]) -> None:
    if readiness_review.get("ready_for_limited_factor_diagnostics_review") is not True:
        raise ValueError("readiness review is not ready for limited diagnostics review")
    for field in ("summary_counts", "date_range"):
        if field not in readiness_review:
            raise ValueError(f"readiness review missing field: {field}")


def _validate_experiment_log_scope(experiment_log: dict[str, Any]) -> None:
    allowed = set(_required_list(experiment_log, "allowed_diagnostics"))
    forbidden = set(_required_list(experiment_log, "forbidden_interpretations"))
    missing_allowed = sorted(set(ALLOWED_DIAGNOSTICS) - allowed)
    missing_forbidden = sorted(set(REQUIRED_INPUT_FORBIDDEN_INTERPRETATIONS) - forbidden)
    if missing_allowed:
        raise ValueError(f"missing allowed diagnostics: {missing_allowed}")
    if missing_forbidden:
        raise ValueError(f"missing forbidden interpretations: {missing_forbidden}")


def _factor_coverage_by_name(summary: str) -> dict[str, dict[str, Any]]:
    rows = _parse_markdown_table(summary, "Factor Coverage", key="factor")
    assert isinstance(rows, dict)
    result: dict[str, dict[str, Any]] = {}
    for factor, values in rows.items():
        date_count = _int(values["date_count"])
        asset_count = _int(values["asset_count"])
        valid = _int(values["valid_observations"])
        missing = _int(values["missing_observations"])
        total = valid + missing
        result[factor] = {
            "date_count": date_count,
            "asset_count": asset_count,
            "valid_observations": valid,
            "missing_observations": missing,
            "total_observations": total,
            "missing_fraction": missing / total if total else 0.0,
        }
    return result


def _split_diagnostic_rows(summary: str) -> list[dict[str, Any]]:
    rows = _parse_markdown_table(summary, "Split Diagnostics")
    assert isinstance(rows, list)
    return [
        {
            "factor": row["factor"],
            "split": row["split"],
            "date_count": _int(row["date_count"]),
            "factor_valid_observations": _int(row["factor_valid_observations"]),
            "forward_return_valid_observations": _int(
                row["forward_return_valid_observations"]
            ),
            "ic_valid_dates": _int(row["ic_valid_dates"]),
            "rank_ic_valid_dates": _int(row["rank_ic_valid_dates"]),
            "quantile_spread_valid_dates": _int(row["quantile_spread_valid_dates"]),
            "mean_ic": _float(row["mean_ic"]),
            "mean_rank_ic": _float(row["mean_rank_ic"]),
            "mean_quantile_spread": _float(row["mean_quantile_spread"]),
        }
        for row in rows
    ]


def _required_list(payload: dict[str, Any], field_name: str) -> list[str]:
    value = payload.get(field_name)
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return [str(item) for item in value]


def _int(value: str) -> int:
    return int(value)


def _float(value: str) -> float:
    return float(value)


def _render_markdown(payload: dict[str, Any]) -> str:
    counts = payload["summary_counts"]
    date_range = payload["date_range"]
    return "\n".join(
        [
            "# EODHD Limited Factor Diagnostics Review",
            "",
            "Diagnostics are research diagnostics only.",
            f"- Asset rows: {counts['asset_rows']}",
            f"- Benchmark rows: {counts['benchmark_rows']}",
            f"- Symbol coverage: {counts['symbol_coverage']}",
            f"- Date range: {date_range['start']} to {date_range['end']}",
            f"- Factors reviewed: {len(payload['factor_coverage'])}",
            f"- Split labels: {', '.join(payload['split_labels'])}",
            "",
            payload["no_strategy_no_performance_statement"],
            "",
            f"Next checkpoint: {payload['next_checkpoint']}",
            "",
        ]
    )


def _is_under(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def main() -> None:
    payload = run_eodhd_limited_factor_diagnostics_review()
    counts = payload["summary_counts"]
    date_range = payload["date_range"]
    print(f"REVIEW_JSON_PATH={payload['output_file_paths']['limited_review_json']}")
    print(f"REVIEW_MARKDOWN_PATH={payload['output_file_paths']['limited_review_markdown']}")
    print(f"FACTOR_COUNT={len(payload['factor_coverage'])}")
    print(f"SPLIT_LABELS={','.join(payload['split_labels'])}")
    print(f"ASSET_ROWS={counts['asset_rows']}")
    print(f"BENCHMARK_ROWS={counts['benchmark_rows']}")
    print(f"SYMBOL_COVERAGE={counts['symbol_coverage']}")
    print(f"DATE_RANGE={date_range['start']}..{date_range['end']}")


if __name__ == "__main__":
    main()
