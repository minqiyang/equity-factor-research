"""Deterministic experiment-log helpers for research demos.

The helpers in this module serialize already-computed metadata. They do not
fetch data, calculate features, run backtests, place orders, or make
profitability claims.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from datetime import date, datetime
import json
import math
from pathlib import Path
from typing import Any


SYNTHETIC_RESEARCH_CAVEATS = (
    "synthetic data only",
    "not financial advice",
    "not a profitability claim",
    "no real data fetching",
    "no live trading or brokerage integration",
)

DIAGNOSTIC_REAL_DATA_CAVEATS = (
    "DIAGNOSTIC_ONLY",
    "not financial advice",
    "not a profitability claim",
    "local user-provided files only; no remote data fetch",
    "no live trading or brokerage integration",
    "static survivor cohort is not point-in-time universe evidence",
    "survivorship-biased diagnostic",
)

REAL_DATA_MULTIFACTOR_EXPERIMENT_TYPE = "real_data_multifactor_diagnostic"


def resolve_experiment_log_path(
    report_path: Path,
    *,
    default_report_path: Path,
    default_log_path: Path,
) -> Path:
    """Resolve the JSON sidecar path for a synthetic demo report.

    The default committed Markdown reports write logs under
    ``reports/experiment_logs``. Custom report paths receive an adjacent JSON
    sidecar so tests and ad hoc runs stay self-contained.
    """

    report_path = Path(report_path)
    if report_path.resolve() == Path(default_report_path).resolve():
        return default_log_path
    return report_path.with_suffix(".json")


def write_experiment_log(
    *,
    log_path: Path,
    experiment_id: str,
    title: str,
    experiment_type: str,
    summary: str,
    config: Any,
    assumptions: Mapping[str, Any],
    outputs: Mapping[str, Any],
    metrics: Mapping[str, Any] | None = None,
    diagnostics: Mapping[str, Any] | None = None,
    caveats: Sequence[str] = SYNTHETIC_RESEARCH_CAVEATS,
    required_caveats: Sequence[str] | None = None,
    next_action: str,
) -> dict[str, Any]:
    """Write a deterministic JSON experiment log and return its payload."""

    _validate_required_text(experiment_id, field_name="experiment_id")
    _validate_required_text(title, field_name="title")
    _validate_required_text(experiment_type, field_name="experiment_type")
    _validate_required_text(summary, field_name="summary")
    _validate_required_text(next_action, field_name="next_action")
    required = (
        SYNTHETIC_RESEARCH_CAVEATS
        if required_caveats is None
        else tuple(required_caveats)
    )
    _validate_caveats(caveats, required=required)

    payload = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "title": title,
        "experiment_type": experiment_type,
        "summary": summary,
        "config": _to_json_value(config),
        "assumptions": _to_json_value(assumptions),
        "outputs": _to_json_value(outputs),
        "metrics": _to_json_value(metrics or {}),
        "diagnostics": _to_json_value(diagnostics or {}),
        "caveats": list(caveats),
        "next_action": next_action,
    }

    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return payload


def _to_json_value(value: Any) -> Any:
    if getattr(value, "__experiment_log_private__", False):
        raise TypeError(
            "private backtest source provenance must not be serialized",
        )
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _to_json_value(getattr(value, field.name))
            for field in fields(value)
        }

    if isinstance(value, Mapping):
        return {str(key): _to_json_value(nested) for key, nested in value.items()}

    if isinstance(value, tuple | list):
        return [_to_json_value(nested) for nested in value]

    if isinstance(value, set | frozenset):
        return sorted(_to_json_value(nested) for nested in value)

    if isinstance(value, Path):
        return value.as_posix()

    if isinstance(value, datetime | date):
        return value.isoformat()

    if hasattr(value, "item") and callable(value.item):
        return _to_json_value(value.item())

    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return value

    if isinstance(value, int | str | bool) or value is None:
        return value

    raise TypeError(f"unsupported experiment log value type: {type(value).__name__}")


def _validate_required_text(value: str, *, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _validate_caveats(
    caveats: Sequence[str],
    *,
    required: Sequence[str] = SYNTHETIC_RESEARCH_CAVEATS,
) -> None:
    caveat_set = set(caveats)
    missing = [caveat for caveat in required if caveat not in caveat_set]
    if missing:
        family = (
            "synthetic experiment logs"
            if tuple(required) == SYNTHETIC_RESEARCH_CAVEATS
            else "experiment logs"
        )
        raise ValueError(f"{family} must include caveats: {missing}")


__all__ = [
    "DIAGNOSTIC_REAL_DATA_CAVEATS",
    "REAL_DATA_MULTIFACTOR_EXPERIMENT_TYPE",
    "SYNTHETIC_RESEARCH_CAVEATS",
    "resolve_experiment_log_path",
    "write_experiment_log",
]
