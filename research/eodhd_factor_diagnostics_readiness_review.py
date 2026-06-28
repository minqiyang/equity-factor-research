"""Private EODHD factor-diagnostics readiness review.

This module checks metadata from the private factor-diagnostics handoff. It
does not fetch data, calculate factors, run a strategy, or interpret results.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = Path("/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run")
DEFAULT_EXPERIMENT_LOG = DEFAULT_BUNDLE / "FACTOR_DIAGNOSTICS_EXPERIMENT_LOG.json"
DEFAULT_DRY_RUN_SUMMARY = DEFAULT_BUNDLE / "FACTOR_DIAGNOSTICS_DRY_RUN_SUMMARY.md"
DEFAULT_REVIEW_JSON = DEFAULT_BUNDLE / "FACTOR_DIAGNOSTICS_READINESS_REVIEW.json"
DEFAULT_REVIEW_MARKDOWN = DEFAULT_BUNDLE / "FACTOR_DIAGNOSTICS_READINESS_REVIEW.md"

EXPECTED_DATA_SOURCE = "EODHD local CSV private bundle"
REQUIRED_ALLOWED_DIAGNOSTICS = {
    "factor coverage",
    "factor missingness",
    "IC",
    "Rank IC",
    "quantile spread",
    "split labels",
}
REQUIRED_FORBIDDEN_OUTPUTS = {
    "strategy run",
    "backtest",
    "portfolio construction",
    "trade simulation",
    "PnL",
    "Sharpe",
    "drawdown",
    "performance interpretation",
    "profitability claim",
    "alpha claim",
    "trading-readiness claim",
}
REQUIRED_EXPERIMENT_LOG_FIELDS = {
    "data_source",
    "input_file_paths",
    "output_file_paths",
    "symbol_coverage",
    "row_counts",
    "date_range",
    "allowed_diagnostics",
    "forbidden_interpretations",
    "adjusted_close_policy",
    "static_universe_survivorship_caveat",
    "no_strategy_no_backtest_statement",
}


@dataclass(frozen=True)
class EODHDFactorDiagnosticsReadinessReviewConfig:
    bundle_path: Path = DEFAULT_BUNDLE
    experiment_log_path: Path = DEFAULT_EXPERIMENT_LOG
    dry_run_summary_path: Path = DEFAULT_DRY_RUN_SUMMARY
    review_json_path: Path = DEFAULT_REVIEW_JSON
    review_markdown_path: Path = DEFAULT_REVIEW_MARKDOWN


def run_eodhd_factor_diagnostics_readiness_review(
    config: EODHDFactorDiagnosticsReadinessReviewConfig = (
        EODHDFactorDiagnosticsReadinessReviewConfig()
    ),
) -> dict[str, Any]:
    """Write a private readiness review for limited diagnostics review."""

    _validate_config(config)
    experiment_log = _read_json(config.experiment_log_path)
    dry_run_summary = _read_text(config.dry_run_summary_path)
    _validate_required_fields(experiment_log)

    row_counts = _required_mapping(experiment_log["row_counts"], "row_counts")
    checks = {
        "required_private_artifacts_exist": _check_required_artifacts(config, experiment_log),
        "expected_data_source": _check(
            experiment_log["data_source"] == EXPECTED_DATA_SOURCE,
            f"data_source={experiment_log['data_source']}",
        ),
        "symbol_coverage_recorded": _check_positive_int(
            experiment_log["symbol_coverage"],
            "symbol_coverage",
        ),
        "row_counts_recorded": _check(
            _is_positive_int(row_counts.get("asset_rows"))
            and _is_positive_int(row_counts.get("benchmark_rows")),
            "asset_rows and benchmark_rows are present",
        ),
        "date_range_recorded": _check_date_range(experiment_log["date_range"]),
        "allowed_diagnostics_recorded": _check_required_items(
            experiment_log["allowed_diagnostics"],
            REQUIRED_ALLOWED_DIAGNOSTICS,
            "allowed_diagnostics",
        ),
        "forbidden_outputs_recorded": _check_required_items(
            experiment_log["forbidden_interpretations"],
            REQUIRED_FORBIDDEN_OUTPUTS,
            "forbidden_interpretations",
        ),
        "adjusted_close_policy_recorded": _check_contains(
            experiment_log["adjusted_close_policy"],
            "adjusted_close",
            "adjusted_close_policy",
        ),
        "static_universe_survivorship_caveat_recorded": _check_contains(
            experiment_log["static_universe_survivorship_caveat"],
            "static",
            "static_universe_survivorship_caveat",
        ),
        "no_strategy_no_backtest_statement_recorded": _check_no_strategy_statement(
            experiment_log["no_strategy_no_backtest_statement"],
        ),
        "dry_run_summary_links_metadata": _check_summary_metadata(
            dry_run_summary,
            experiment_log,
        ),
    }
    ready = all(check["passed"] for check in checks.values())
    payload: dict[str, Any] = {
        "schema_version": 1,
        "review_name": "EODHD factor diagnostics readiness review",
        "ready_for_limited_factor_diagnostics_review": ready,
        "checks": checks,
        "input_file_paths": {
            "experiment_log": str(config.experiment_log_path),
            "dry_run_summary": str(config.dry_run_summary_path),
        },
        "output_file_paths": {
            "readiness_review_json": str(config.review_json_path),
            "readiness_review_markdown": str(config.review_markdown_path),
        },
        "summary_counts": {
            "asset_rows": row_counts["asset_rows"],
            "benchmark_rows": row_counts["benchmark_rows"],
            "symbol_coverage": experiment_log["symbol_coverage"],
        },
        "date_range": experiment_log["date_range"],
        "next_checkpoint": (
            "Future limited factor-diagnostics review may inspect diagnostics "
            "only after this readiness review remains passing."
        ),
        "no_interpretation_statement": (
            "This readiness review does not interpret IC, Rank IC, quantile spread, "
            "returns, alpha, profitability, or trading readiness."
        ),
    }
    config.review_json_path.parent.mkdir(parents=True, exist_ok=True)
    config.review_json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    config.review_markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
    return payload


def _validate_config(config: EODHDFactorDiagnosticsReadinessReviewConfig) -> None:
    bundle = config.bundle_path.resolve()
    for field_name, path in (
        ("experiment_log_path", config.experiment_log_path),
        ("dry_run_summary_path", config.dry_run_summary_path),
        ("review_json_path", config.review_json_path),
        ("review_markdown_path", config.review_markdown_path),
    ):
        resolved = path.resolve()
        if not _is_under(resolved, bundle):
            raise ValueError(f"{field_name} must be under bundle_path")
        if field_name.startswith("review_") and PROJECT_ROOT in resolved.parents:
            raise ValueError(f"{field_name} must be outside the repository")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"{path} is empty")
    return text


def _validate_required_fields(payload: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_EXPERIMENT_LOG_FIELDS - payload.keys())
    if missing:
        raise ValueError(f"missing experiment log fields: {missing}")


def _check_required_artifacts(
    config: EODHDFactorDiagnosticsReadinessReviewConfig,
    experiment_log: dict[str, Any],
) -> dict[str, Any]:
    input_paths = _required_mapping(experiment_log["input_file_paths"], "input_file_paths")
    output_paths = _required_mapping(experiment_log["output_file_paths"], "output_file_paths")
    required_paths = {
        "experiment_log": config.experiment_log_path,
        "dry_run_summary": config.dry_run_summary_path,
        "experiment_log_markdown": Path(str(output_paths["experiment_log_markdown"])),
        "factor_diagnostics_summary": Path(str(input_paths["factor_diagnostics_summary"])),
    }
    missing = [name for name, path in required_paths.items() if not path.exists()]
    return _check(not missing, f"missing={missing}")


def _check_positive_int(value: Any, field_name: str) -> dict[str, Any]:
    return _check(_is_positive_int(value), f"{field_name}={value}")


def _check_date_range(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return _check(False, "date_range is not an object")
    return _check(
        bool(value.get("start")) and bool(value.get("end")),
        f"start={value.get('start')}, end={value.get('end')}",
    )


def _check_required_items(value: Any, required: set[str], field_name: str) -> dict[str, Any]:
    if not isinstance(value, list):
        return _check(False, f"{field_name} is not a list")
    missing = sorted(required - set(value))
    return _check(not missing, f"missing={missing}")


def _check_contains(value: Any, needle: str, field_name: str) -> dict[str, Any]:
    return _check(isinstance(value, str) and needle in value, f"{field_name} includes {needle}")


def _check_no_strategy_statement(value: Any) -> dict[str, Any]:
    required = {"No strategy", "backtest", "performance interpretation"}
    return _check(
        isinstance(value, str) and all(item in value for item in required),
        "no-strategy/no-backtest/no-performance statement recorded",
    )


def _check_summary_metadata(summary: str, experiment_log: dict[str, Any]) -> dict[str, Any]:
    row_counts = _required_mapping(experiment_log["row_counts"], "row_counts")
    required_fragments = [
        f"- Asset rows: {row_counts['asset_rows']}",
        f"- Benchmark rows: {row_counts['benchmark_rows']}",
        f"- Symbol coverage: {experiment_log['symbol_coverage']}",
    ]
    missing = [fragment for fragment in required_fragments if fragment not in summary]
    return _check(not missing, f"missing={missing}")


def _required_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and value > 0


def _check(passed: bool, detail: str) -> dict[str, Any]:
    return {"passed": bool(passed), "detail": detail}


def _render_markdown(payload: dict[str, Any]) -> str:
    checks = payload["checks"]
    row_counts = payload["summary_counts"]
    date_range = payload["date_range"]
    return "\n".join(
        [
            "# EODHD Factor Diagnostics Readiness Review",
            "",
            f"- Ready for limited factor diagnostics review: {payload['ready_for_limited_factor_diagnostics_review']}",
            f"- Asset rows: {row_counts['asset_rows']}",
            f"- Benchmark rows: {row_counts['benchmark_rows']}",
            f"- Symbol coverage: {row_counts['symbol_coverage']}",
            f"- Date range: {date_range['start']} to {date_range['end']}",
            "",
            "## Checks",
            "",
            "| Check | Passed |",
            "| --- | --- |",
            *[f"| {name} | {check['passed']} |" for name, check in checks.items()],
            "",
            payload["no_interpretation_statement"],
            "",
            f"Next checkpoint: {payload['next_checkpoint']}",
            "",
        ]
    )


def _is_under(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def main() -> None:
    payload = run_eodhd_factor_diagnostics_readiness_review()
    counts = payload["summary_counts"]
    date_range = payload["date_range"]
    print(f"REVIEW_JSON_PATH={payload['output_file_paths']['readiness_review_json']}")
    print(f"REVIEW_MARKDOWN_PATH={payload['output_file_paths']['readiness_review_markdown']}")
    print(
        "READY_FOR_LIMITED_FACTOR_DIAGNOSTICS_REVIEW="
        f"{payload['ready_for_limited_factor_diagnostics_review']}"
    )
    print(f"ASSET_ROWS={counts['asset_rows']}")
    print(f"BENCHMARK_ROWS={counts['benchmark_rows']}")
    print(f"SYMBOL_COVERAGE={counts['symbol_coverage']}")
    print(f"DATE_RANGE={date_range['start']}..{date_range['end']}")


if __name__ == "__main__":
    main()
