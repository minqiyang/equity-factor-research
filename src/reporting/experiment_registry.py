"""Structured registry helpers for synthetic experiment logs.

This module summarizes already-written JSON experiment logs. It does not fetch
data, run experiments, calculate strategy metrics, place orders, or make
profitability claims.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPERIMENT_LOG_DIR = PROJECT_ROOT / "reports" / "experiment_logs"
DEFAULT_REGISTRY_REPORT_PATH = PROJECT_ROOT / "reports" / "experiment_registry.md"

REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "experiment_id",
    "title",
    "experiment_type",
    "summary",
    "config",
    "assumptions",
    "outputs",
    "metrics",
    "diagnostics",
    "caveats",
    "next_action",
)

REQUIRED_CAVEATS = (
    "synthetic data only",
    "not financial advice",
    "not a profitability claim",
    "no real data fetching",
    "no live trading or brokerage integration",
)

REGISTRY_COLUMNS = (
    "experiment_id",
    "title",
    "experiment_type",
    "data_scope",
    "date_start",
    "date_end",
    "universe",
    "benchmark",
    "transaction_cost_model",
    "slippage_model",
    "metrics_available",
    "total_return",
    "annualized_return",
    "tracking_error",
    "episode_hit_rate",
    "average_holding_period_return",
    "max_drawdown",
    "sharpe_ratio",
    "markdown_report",
    "experiment_log",
    "next_action",
)


def load_experiment_log(log_path: Path) -> dict[str, Any]:
    """Load and validate one JSON experiment log."""

    log_path = Path(log_path)
    payload = json.loads(log_path.read_text(encoding="utf-8"))
    _validate_experiment_log(payload, log_path=log_path)
    return payload


def load_experiment_logs(
    log_dir: Path = DEFAULT_EXPERIMENT_LOG_DIR,
    *,
    pattern: str = "*.json",
) -> list[dict[str, Any]]:
    """Load all experiment logs from ``log_dir`` in deterministic path order."""

    log_dir = Path(log_dir)
    log_paths = sorted(log_dir.glob(pattern))
    if not log_paths:
        raise ValueError(f"no experiment log files found in {log_dir}")

    payloads = [load_experiment_log(path) for path in log_paths]
    _validate_unique_experiment_ids(payloads)
    return payloads


def build_experiment_registry(
    log_dir: Path = DEFAULT_EXPERIMENT_LOG_DIR,
    *,
    pattern: str = "*.json",
) -> pd.DataFrame:
    """Build a structured registry DataFrame from JSON experiment logs."""

    payloads = load_experiment_logs(log_dir, pattern=pattern)
    rows = [_registry_row(payload) for payload in payloads]
    registry = pd.DataFrame(rows, columns=REGISTRY_COLUMNS)
    return registry.sort_values("experiment_id", kind="mergesort").reset_index(drop=True)


def write_experiment_registry_report(
    *,
    log_dir: Path = DEFAULT_EXPERIMENT_LOG_DIR,
    report_path: Path = DEFAULT_REGISTRY_REPORT_PATH,
    pattern: str = "*.json",
) -> pd.DataFrame:
    """Write a deterministic Markdown registry report and return the registry."""

    registry = build_experiment_registry(log_dir=log_dir, pattern=pattern)
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_experiment_registry_markdown(registry), encoding="utf-8")
    return registry


def main(
    *,
    log_dir: Path = DEFAULT_EXPERIMENT_LOG_DIR,
    report_path: Path = DEFAULT_REGISTRY_REPORT_PATH,
) -> None:
    """Regenerate the default synthetic experiment registry report."""

    write_experiment_registry_report(log_dir=log_dir, report_path=report_path)


def render_experiment_registry_markdown(registry: pd.DataFrame) -> str:
    """Render a caveated Markdown report from a registry DataFrame."""

    _validate_registry_frame(registry)

    lines = [
        "# Synthetic Experiment Registry",
        "",
        "This registry summarizes deterministic JSON logs from synthetic demos only. It is not real-market evidence, not financial advice, and not a profitability claim.",
        "",
        "The metrics below are copied from synthetic smoke-test logs when present. They are workflow diagnostics only and should not be interpreted as strategy validation.",
        "",
        "## Registry",
        "",
        _format_markdown_table(registry),
        "",
        "## Caveats",
        "",
        "- The registry reads existing JSON logs; it does not run experiments or recalculate metrics.",
        "- No real data is fetched.",
        "- No live trading, brokerage integration, order execution, or credential handling is introduced.",
        "- Missing metric cells mean the source log did not contain that metric, not that the value is zero.",
        "- Full experiment records are still required before any real-data validation or parameter study.",
        "",
    ]
    return "\n".join(lines)


def _registry_row(payload: Mapping[str, Any]) -> dict[str, Any]:
    assumptions = _require_mapping(payload["assumptions"], field_name="assumptions")
    outputs = _require_mapping(payload["outputs"], field_name="outputs")
    metrics = _require_mapping(payload["metrics"], field_name="metrics")
    date_range = assumptions.get("date_range", {})
    if date_range and not isinstance(date_range, Mapping):
        raise ValueError(
            f"experiment {payload['experiment_id']!r} assumptions.date_range must be a mapping"
        )

    return {
        "experiment_id": payload["experiment_id"],
        "title": payload["title"],
        "experiment_type": payload["experiment_type"],
        "data_scope": assumptions.get("data_scope", ""),
        "date_start": date_range.get("start", "") if date_range else "",
        "date_end": date_range.get("end", "") if date_range else "",
        "universe": assumptions.get("universe", ""),
        "benchmark": assumptions.get("benchmark", ""),
        "transaction_cost_model": assumptions.get("transaction_cost_model", ""),
        "slippage_model": assumptions.get("slippage_model", ""),
        "metrics_available": bool(metrics),
        "total_return": metrics.get("total_return"),
        "annualized_return": metrics.get("annualized_return"),
        "tracking_error": metrics.get("tracking_error"),
        "episode_hit_rate": metrics.get("episode_hit_rate"),
        "average_holding_period_return": metrics.get(
            "average_holding_period_return"
        ),
        "max_drawdown": metrics.get("max_drawdown"),
        "sharpe_ratio": metrics.get("sharpe_ratio"),
        "markdown_report": outputs.get("markdown_report", ""),
        "experiment_log": outputs.get("experiment_log", ""),
        "next_action": payload["next_action"],
    }


def _validate_experiment_log(payload: Any, *, log_path: Path) -> None:
    if not isinstance(payload, Mapping):
        raise TypeError(f"{log_path} must contain a JSON object")

    missing = [field for field in REQUIRED_TOP_LEVEL_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"{log_path} is missing required fields: {missing}")

    if payload["schema_version"] != 1:
        raise ValueError(f"{log_path} has unsupported schema_version {payload['schema_version']!r}")

    for field in ("experiment_id", "title", "experiment_type", "summary", "next_action"):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise ValueError(f"{log_path} field {field!r} must be a non-empty string")

    for field in ("config", "assumptions", "outputs", "metrics", "diagnostics"):
        _require_mapping(payload[field], field_name=field)

    caveats = payload["caveats"]
    if not isinstance(caveats, list) or not all(isinstance(item, str) for item in caveats):
        raise ValueError(f"{log_path} field 'caveats' must be a list of strings")

    missing_caveats = [caveat for caveat in REQUIRED_CAVEATS if caveat not in caveats]
    if missing_caveats:
        raise ValueError(f"{log_path} is missing required caveats: {missing_caveats}")


def _validate_unique_experiment_ids(payloads: Iterable[Mapping[str, Any]]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for payload in payloads:
        experiment_id = str(payload["experiment_id"])
        if experiment_id in seen:
            duplicates.add(experiment_id)
        seen.add(experiment_id)

    if duplicates:
        raise ValueError(f"duplicate experiment_id values found: {sorted(duplicates)}")


def _validate_registry_frame(registry: pd.DataFrame) -> None:
    missing = [column for column in REGISTRY_COLUMNS if column not in registry.columns]
    if missing:
        raise ValueError(f"registry is missing required columns: {missing}")


def _require_mapping(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def _format_markdown_table(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    separator = ["---" for _ in headers]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(_format_cell(row[column]) for column in frame.columns) + " |")
    return "\n".join(lines)


def _format_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.6g}"
    text = str(value)
    return text.replace("\n", " ").replace("|", "\\|")


__all__ = [
    "DEFAULT_EXPERIMENT_LOG_DIR",
    "DEFAULT_REGISTRY_REPORT_PATH",
    "REGISTRY_COLUMNS",
    "build_experiment_registry",
    "load_experiment_log",
    "load_experiment_logs",
    "main",
    "render_experiment_registry_markdown",
    "write_experiment_registry_report",
]


if __name__ == "__main__":
    main()
