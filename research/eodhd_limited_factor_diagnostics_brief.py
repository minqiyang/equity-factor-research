"""Private neutral EODHD limited factor-diagnostics brief."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = Path("/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run")
DEFAULT_LIMITED_REVIEW = DEFAULT_BUNDLE / "LIMITED_FACTOR_DIAGNOSTICS_REVIEW.json"
DEFAULT_READINESS_REVIEW = DEFAULT_BUNDLE / "FACTOR_DIAGNOSTICS_READINESS_REVIEW.json"
DEFAULT_EXPERIMENT_LOG = DEFAULT_BUNDLE / "FACTOR_DIAGNOSTICS_EXPERIMENT_LOG.json"
DEFAULT_OUTPUT_JSON = DEFAULT_BUNDLE / "LIMITED_FACTOR_DIAGNOSTICS_BRIEF.json"
DEFAULT_OUTPUT_MARKDOWN = DEFAULT_BUNDLE / "LIMITED_FACTOR_DIAGNOSTICS_BRIEF.md"

DIAGNOSTIC_METRICS = {
    "mean_ic": "ic_valid_dates",
    "mean_rank_ic": "rank_ic_valid_dates",
    "mean_quantile_spread": "quantile_spread_valid_dates",
}


@dataclass(frozen=True)
class EODHDLimitedFactorDiagnosticsBriefConfig:
    bundle_path: Path = DEFAULT_BUNDLE
    limited_review_path: Path = DEFAULT_LIMITED_REVIEW
    readiness_review_path: Path = DEFAULT_READINESS_REVIEW
    experiment_log_path: Path = DEFAULT_EXPERIMENT_LOG
    output_json_path: Path = DEFAULT_OUTPUT_JSON
    output_markdown_path: Path = DEFAULT_OUTPUT_MARKDOWN


def run_eodhd_limited_factor_diagnostics_brief(
    config: EODHDLimitedFactorDiagnosticsBriefConfig = (
        EODHDLimitedFactorDiagnosticsBriefConfig()
    ),
) -> dict[str, Any]:
    """Write a private neutral diagnostics brief from the limited review."""

    _validate_config(config)
    limited_review = _read_json(config.limited_review_path)
    readiness_review = _read_json(config.readiness_review_path)
    experiment_log = _read_json(config.experiment_log_path)
    _validate_inputs(limited_review, readiness_review, experiment_log)

    factor_coverage = _required_mapping(limited_review["factor_coverage"], "factor_coverage")
    factor_missingness = _required_mapping(
        limited_review["factor_missingness"],
        "factor_missingness",
    )
    split_diagnostics = _as_list(limited_review["split_diagnostics"], "split_diagnostics")
    factor_briefs = _build_factor_briefs(factor_coverage, factor_missingness, split_diagnostics)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "brief_scope": "limited_factor_diagnostics_brief",
        "diagnostics_are_research_only": True,
        "input_file_paths": {
            "limited_review": str(config.limited_review_path),
            "readiness_review": str(config.readiness_review_path),
            "experiment_log": str(config.experiment_log_path),
        },
        "output_file_paths": {
            "brief_json": str(config.output_json_path),
            "brief_markdown": str(config.output_markdown_path),
        },
        "summary_counts": limited_review["summary_counts"],
        "date_range": limited_review["date_range"],
        "factor_count": len(factor_briefs),
        "split_labels": limited_review["split_labels"],
        "factor_briefs": factor_briefs,
        "neutral_brief_statement": (
            "Diagnostic direction, magnitude, and split consistency are described "
            "neutrally as research diagnostics only."
        ),
        "no_strategy_no_performance_statement": (
            "No strategy, backtest, portfolio construction, PnL, Sharpe, drawdown, "
            "investment recommendation, profitability claim, alpha claim, or "
            "trading-readiness claim was made."
        ),
        "next_checkpoint": (
            "Decide whether another methodology/data-readiness checkpoint is needed "
            "before any broader research interpretation."
        ),
    }
    config.output_json_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    config.output_markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
    return payload


def _validate_config(config: EODHDLimitedFactorDiagnosticsBriefConfig) -> None:
    bundle = config.bundle_path.resolve()
    for field_name, path in (
        ("limited_review_path", config.limited_review_path),
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


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _validate_inputs(
    limited_review: dict[str, Any],
    readiness_review: dict[str, Any],
    experiment_log: dict[str, Any],
) -> None:
    if limited_review.get("review_scope") != "limited_factor_diagnostics_review":
        raise ValueError("limited review scope must be limited_factor_diagnostics_review")
    if limited_review.get("diagnostics_are_research_only") is not True:
        raise ValueError("limited review must mark diagnostics as research only")
    if readiness_review.get("ready_for_limited_factor_diagnostics_review") is not True:
        raise ValueError("readiness review is not ready for limited diagnostics review")
    allowed = set(_required_list(experiment_log, "allowed_diagnostics"))
    missing = {
        "factor coverage",
        "factor missingness",
        "IC",
        "Rank IC",
        "quantile spread",
        "split labels",
    } - allowed
    if missing:
        raise ValueError(f"experiment log missing allowed diagnostics: {sorted(missing)}")
    for field in (
        "summary_counts",
        "date_range",
        "factor_coverage",
        "factor_missingness",
        "split_labels",
        "split_diagnostics",
    ):
        if field not in limited_review:
            raise ValueError(f"limited review missing field: {field}")


def _build_factor_briefs(
    factor_coverage: dict[str, Any],
    factor_missingness: dict[str, Any],
    split_diagnostics: list[Any],
) -> dict[str, Any]:
    by_factor: dict[str, list[dict[str, Any]]] = {}
    for row in split_diagnostics:
        row_map = _required_mapping(row, "split_diagnostics row")
        by_factor.setdefault(str(row_map["factor"]), []).append(row_map)
    return {
        factor: {
            "coverage": factor_coverage[factor],
            "missingness": factor_missingness[factor],
            "diagnostics": _diagnostics_for_factor(by_factor.get(factor, [])),
        }
        for factor in sorted(factor_coverage)
    }


def _diagnostics_for_factor(rows: list[dict[str, Any]]) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    for metric, valid_dates_field in DIAGNOSTIC_METRICS.items():
        by_split = [
            {
                "split": str(row["split"]),
                "value": float(row[metric]),
                "direction": _direction(float(row[metric])),
                "magnitude": abs(float(row[metric])),
                "valid_dates": int(row[valid_dates_field]),
            }
            for row in rows
        ]
        diagnostics[metric] = {
            "by_split": by_split,
            "split_consistency": _split_consistency(by_split),
        }
    return diagnostics


def _direction(value: float) -> str:
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "zero"


def _split_consistency(rows: list[dict[str, Any]]) -> str:
    directions = {row["direction"] for row in rows}
    if not directions:
        return "no_split_values"
    if directions == {"positive"}:
        return "positive"
    if directions == {"negative"}:
        return "negative"
    if directions == {"zero"}:
        return "zero"
    return "mixed_sign"


def _required_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def _required_list(payload: dict[str, Any], field_name: str) -> list[Any]:
    value = payload.get(field_name)
    return _as_list(value, field_name)


def _as_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return value


def _render_markdown(payload: dict[str, Any]) -> str:
    counts = payload["summary_counts"]
    date_range = payload["date_range"]
    return "\n".join(
        [
            "# EODHD Limited Factor Diagnostics Brief",
            "",
            "Diagnostics are research diagnostics only.",
            f"- Factor count: {payload['factor_count']}",
            f"- Split labels: {', '.join(payload['split_labels'])}",
            f"- Asset rows: {counts['asset_rows']}",
            f"- Benchmark rows: {counts['benchmark_rows']}",
            f"- Symbol coverage: {counts['symbol_coverage']}",
            f"- Date range: {date_range['start']} to {date_range['end']}",
            "",
            payload["neutral_brief_statement"],
            payload["no_strategy_no_performance_statement"],
            "",
            f"Next checkpoint: {payload['next_checkpoint']}",
            "",
        ]
    )


def _is_under(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def main() -> None:
    payload = run_eodhd_limited_factor_diagnostics_brief()
    counts = payload["summary_counts"]
    date_range = payload["date_range"]
    print(f"BRIEF_JSON_PATH={payload['output_file_paths']['brief_json']}")
    print(f"BRIEF_MARKDOWN_PATH={payload['output_file_paths']['brief_markdown']}")
    print(f"FACTOR_COUNT={payload['factor_count']}")
    print(f"SPLIT_LABELS={','.join(payload['split_labels'])}")
    print(f"ASSET_ROWS={counts['asset_rows']}")
    print(f"BENCHMARK_ROWS={counts['benchmark_rows']}")
    print(f"SYMBOL_COVERAGE={counts['symbol_coverage']}")
    print(f"DATE_RANGE={date_range['start']}..{date_range['end']}")


if __name__ == "__main__":
    main()
