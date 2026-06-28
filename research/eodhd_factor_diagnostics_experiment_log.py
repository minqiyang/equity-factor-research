"""Private EODHD factor-diagnostics experiment-log handoff.

This module records metadata from an already-generated private diagnostics
summary. It does not fetch data, calculate factors, run a strategy, or
interpret performance.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = Path("/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run")
DEFAULT_SUMMARY = DEFAULT_BUNDLE / "FACTOR_DIAGNOSTICS_DRY_RUN_SUMMARY.md"
DEFAULT_LOG = DEFAULT_BUNDLE / "FACTOR_DIAGNOSTICS_EXPERIMENT_LOG.json"
DEFAULT_MARKDOWN = DEFAULT_BUNDLE / "FACTOR_DIAGNOSTICS_EXPERIMENT_LOG.md"

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
    "profitability claim",
    "alpha claim",
    "trading-readiness claim",
]


@dataclass(frozen=True)
class EODHDFactorDiagnosticsExperimentLogConfig:
    bundle_path: Path = DEFAULT_BUNDLE
    summary_path: Path = DEFAULT_SUMMARY
    log_path: Path = DEFAULT_LOG
    markdown_path: Path = DEFAULT_MARKDOWN
    run_label: str = "eodhd-factor-diagnostics-readiness-handoff"


def run_eodhd_factor_diagnostics_experiment_log(
    config: EODHDFactorDiagnosticsExperimentLogConfig = (
        EODHDFactorDiagnosticsExperimentLogConfig()
    ),
) -> dict[str, object]:
    """Write a private structured experiment-log handoff from the summary."""

    _validate_config(config)
    summary_text = _read_required_text(config.summary_path)
    private_inputs = _parse_private_inputs(summary_text)
    row_counts = _parse_row_counts(summary_text)
    factor_coverage = _parse_markdown_table(summary_text, "Factor Coverage", key="factor")
    split_rows = _parse_markdown_table(summary_text, "Split Diagnostics")
    split_labels = sorted({row["split"] for row in split_rows if row.get("split")})
    date_range = _read_aligned_date_range(
        Path(private_inputs["OHLCV"]),
        Path(private_inputs["Benchmark"]),
    )

    payload: dict[str, object] = {
        "schema_version": 1,
        "run_label": _required_text(config.run_label, "run_label"),
        "data_source": "EODHD local CSV private bundle",
        "local_private_bundle_path": str(config.bundle_path),
        "input_file_paths": {
            "factor_diagnostics_summary": str(config.summary_path),
            "ohlcv": private_inputs["OHLCV"],
            "benchmark": private_inputs["Benchmark"],
            "dry_run_summary_output": private_inputs["Output"],
        },
        "output_file_paths": {
            "experiment_log_json": str(config.log_path),
            "experiment_log_markdown": str(config.markdown_path),
        },
        "symbol_coverage": row_counts["symbol_coverage"],
        "row_counts": {
            "asset_rows": row_counts["asset_rows"],
            "benchmark_rows": row_counts["benchmark_rows"],
        },
        "date_range": date_range,
        "factor_diagnostics_stage_name": "EODHD factor diagnostics dry run",
        "allowed_diagnostics": ALLOWED_DIAGNOSTICS,
        "forbidden_interpretations": FORBIDDEN_INTERPRETATIONS,
        "adjusted_close_policy": (
            "Diagnostics use adjusted_close from the validated local EODHD CSV bundle; "
            "raw OHLC fields may have different adjustment semantics and remain unresolved "
            "for interpretation."
        ),
        "static_universe_survivorship_caveat": (
            "The selected universe is static and is not point-in-time membership, so "
            "survivorship bias remains unresolved for interpretation."
        ),
        "no_strategy_no_backtest_statement": (
            "No strategy, backtest, portfolio construction, PnL, Sharpe, drawdown, "
            "trade simulation, performance interpretation, profitability claim, alpha "
            "claim, or trading-readiness claim was performed."
        ),
        "factor_coverage": factor_coverage,
        "split_labels": split_labels,
        "next_checkpoint": (
            "Complete a real-data readiness review before interpreting factor diagnostics."
        ),
    }

    config.log_path.parent.mkdir(parents=True, exist_ok=True)
    config.log_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    config.markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
    return payload


def _validate_config(config: EODHDFactorDiagnosticsExperimentLogConfig) -> None:
    bundle = config.bundle_path.resolve()
    for field_name, path in (
        ("summary_path", config.summary_path),
        ("log_path", config.log_path),
        ("markdown_path", config.markdown_path),
    ):
        resolved = path.resolve()
        if not _is_under(resolved, bundle):
            raise ValueError(f"{field_name} must be under bundle_path")
        if field_name != "summary_path" and PROJECT_ROOT in resolved.parents:
            raise ValueError(f"{field_name} must be outside the repository")


def _read_required_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"{path} is empty")
    return text


def _parse_private_inputs(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("- ") or ": `" not in line or not line.endswith("`"):
            continue
        label, value = line[2:-1].split(": `", 1)
        if label in {"OHLCV", "Benchmark", "Output"}:
            values[label] = value
    missing = [label for label in ("OHLCV", "Benchmark", "Output") if label not in values]
    if missing:
        raise ValueError(f"missing private input fields: {missing}")
    return values


def _parse_row_counts(text: str) -> dict[str, int]:
    labels = {
        "Asset rows": "asset_rows",
        "Benchmark rows": "benchmark_rows",
        "Symbol coverage": "symbol_coverage",
    }
    values: dict[str, int] = {}
    for line in text.splitlines():
        if not line.startswith("- ") or ": " not in line:
            continue
        label, value = line[2:].split(": ", 1)
        if label in labels:
            values[labels[label]] = int(value)
    missing = [field for field in labels.values() if field not in values]
    if missing:
        raise ValueError(f"missing row count fields: {missing}")
    return values


def _parse_markdown_table(
    text: str,
    heading: str,
    *,
    key: str | None = None,
) -> list[dict[str, str]] | dict[str, dict[str, str]]:
    lines = text.splitlines()
    marker = f"## {heading}"
    try:
        start = lines.index(marker) + 1
    except ValueError as exc:
        raise ValueError(f"missing section: {heading}") from exc

    table_lines = []
    for line in lines[start:]:
        if line.startswith("## ") and table_lines:
            break
        if line.startswith("| "):
            table_lines.append(line)
        elif table_lines:
            break
    if len(table_lines) < 2:
        raise ValueError(f"missing markdown table: {heading}")
    columns = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(columns):
            raise ValueError(f"malformed markdown table row in {heading}: {line}")
        rows.append(dict(zip(columns, cells, strict=True)))
    if key is None:
        return rows
    return {row[key]: {column: value for column, value in row.items() if column != key} for row in rows}


def _read_aligned_date_range(ohlcv_path: Path, benchmark_path: Path) -> dict[str, str]:
    ohlcv_range = _read_date_range(ohlcv_path)
    benchmark_range = _read_date_range(benchmark_path)
    if ohlcv_range != benchmark_range:
        raise ValueError("OHLCV and benchmark date ranges must match")
    return {"start": ohlcv_range[0].isoformat(), "end": ohlcv_range[1].isoformat()}


def _read_date_range(path: Path) -> tuple[date, date]:
    if not path.exists():
        raise FileNotFoundError(path)
    seen: list[date] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "date" not in reader.fieldnames:
            raise ValueError(f"{path} must include a date column")
        for row in reader:
            seen.append(date.fromisoformat(row["date"]))
    if not seen:
        raise ValueError(f"{path} has no date rows")
    return min(seen), max(seen)


def _render_markdown(payload: dict[str, object]) -> str:
    date_range = payload["date_range"]
    assert isinstance(date_range, dict)
    row_counts = payload["row_counts"]
    assert isinstance(row_counts, dict)
    return "\n".join(
        [
            "# EODHD Factor Diagnostics Experiment Log",
            "",
            f"- Run label: {payload['run_label']}",
            f"- Data source: {payload['data_source']}",
            f"- Private bundle: `{payload['local_private_bundle_path']}`",
            f"- JSON output: `{payload['output_file_paths']['experiment_log_json']}`",
            f"- Asset rows: {row_counts['asset_rows']}",
            f"- Benchmark rows: {row_counts['benchmark_rows']}",
            f"- Symbol coverage: {payload['symbol_coverage']}",
            f"- Date range: {date_range['start']} to {date_range['end']}",
            "",
            payload["no_strategy_no_backtest_statement"],
            "",
            f"Next checkpoint: {payload['next_checkpoint']}",
            "",
        ]
    )


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _is_under(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def main() -> None:
    payload = run_eodhd_factor_diagnostics_experiment_log()
    date_range = payload["date_range"]
    row_counts = payload["row_counts"]
    assert isinstance(date_range, dict)
    assert isinstance(row_counts, dict)
    print(f"LOG_PATH={payload['output_file_paths']['experiment_log_json']}")
    print(f"MARKDOWN_PATH={payload['output_file_paths']['experiment_log_markdown']}")
    print(f"ASSET_ROWS={row_counts['asset_rows']}")
    print(f"BENCHMARK_ROWS={row_counts['benchmark_rows']}")
    print(f"SYMBOL_COVERAGE={payload['symbol_coverage']}")
    print(f"DATE_RANGE={date_range['start']}..{date_range['end']}")


if __name__ == "__main__":
    main()
