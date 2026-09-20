from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backtest.portfolio import capture_backtest_source_provenance
from reporting.experiment_log import (
    DIAGNOSTIC_REAL_DATA_CAVEATS,
    REAL_DATA_MULTIFACTOR_EXPERIMENT_TYPE,
    SYNTHETIC_RESEARCH_CAVEATS,
    resolve_experiment_log_path,
    write_experiment_log,
)


@dataclass(frozen=True)
class ExampleConfig:
    seed: int
    run_date: date


@dataclass(frozen=True)
class NestedConfig:
    payload: object


def test_write_experiment_log_is_deterministic_json(tmp_path: Path) -> None:
    log_path = tmp_path / "experiment.json"

    payload = write_experiment_log(
        log_path=log_path,
        experiment_id="example",
        title="Example Synthetic Experiment",
        experiment_type="synthetic_diagnostic",
        summary="Records already-computed synthetic metadata.",
        config=ExampleConfig(seed=123, run_date=date(2026, 6, 2)),
        assumptions={"data_scope": "synthetic only"},
        outputs={"report": Path("reports/example.md")},
        metrics={"total_return": 0.12, "nan_metric": float("nan")},
        caveats=SYNTHETIC_RESEARCH_CAVEATS,
        next_action="Keep as a synthetic diagnostic log.",
    )

    expected_text = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    assert log_path.read_text(encoding="utf-8") == expected_text

    parsed = json.loads(expected_text)
    assert parsed["schema_version"] == 1
    assert parsed["config"] == {"run_date": "2026-06-02", "seed": 123}
    assert parsed["metrics"]["nan_metric"] is None
    assert parsed["outputs"]["report"] == "reports/example.md"


def test_write_experiment_log_requires_synthetic_caveats(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="synthetic experiment logs must include caveats"):
        write_experiment_log(
            log_path=tmp_path / "experiment.json",
            experiment_id="example",
            title="Example",
            experiment_type="synthetic_diagnostic",
            summary="Missing required caveats.",
            config={},
            assumptions={},
            outputs={},
            caveats=("synthetic data only",),
            next_action="Stop.",
        )


def test_write_experiment_log_accepts_diagnostic_real_data_caveats(tmp_path: Path) -> None:
    log_path = tmp_path / "real.json"
    payload = write_experiment_log(
        log_path=log_path,
        experiment_id="real-data-multifactor-diagnostic",
        title="Real Data",
        experiment_type=REAL_DATA_MULTIFACTOR_EXPERIMENT_TYPE,
        summary="Diagnostic real-data sidecar.",
        config={"top_n": 5},
        assumptions={"data_scope": "local EODHD Parquet diagnostic"},
        outputs={"markdown_report": "reports/real.md"},
        caveats=DIAGNOSTIC_REAL_DATA_CAVEATS,
        required_caveats=DIAGNOSTIC_REAL_DATA_CAVEATS,
        next_action="Keep diagnostic.",
    )
    assert payload["experiment_type"] == REAL_DATA_MULTIFACTOR_EXPERIMENT_TYPE
    assert "synthetic data only" not in payload["caveats"]
    assert "DIAGNOSTIC_ONLY" in payload["caveats"]


def test_write_experiment_log_rejects_private_source_provenance(
    tmp_path: Path,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=3)
    prices = pd.DataFrame({"AAA": np.full(3, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": np.ones(3)}, index=dates)
    source_provenance = capture_backtest_source_provenance(prices, signals)
    log_path = tmp_path / "private_provenance.json"

    with pytest.raises(
        TypeError,
        match="private backtest source provenance must not be serialized",
    ):
        write_experiment_log(
            log_path=log_path,
            experiment_id="private-provenance",
            title="Private Provenance Guard",
            experiment_type="synthetic_diagnostic",
            summary="Exercise the non-serialization boundary.",
            config={},
            assumptions={"source_provenance": source_provenance},
            outputs={},
            caveats=SYNTHETIC_RESEARCH_CAVEATS,
            next_action="Retain only allowlisted provenance status metadata.",
        )

    assert not log_path.exists()

    nested_log_path = tmp_path / "nested_private_provenance.json"
    nested_private_value = NestedConfig(
        payload=source_provenance.signals.original_cells[0][0],
    )
    with pytest.raises(
        TypeError,
        match="private backtest source provenance must not be serialized",
    ):
        write_experiment_log(
            log_path=nested_log_path,
            experiment_id="nested-private-provenance",
            title="Nested Private Provenance Guard",
            experiment_type="synthetic_diagnostic",
            summary="Exercise the recursive non-serialization boundary.",
            config=nested_private_value,
            assumptions={},
            outputs={},
            caveats=SYNTHETIC_RESEARCH_CAVEATS,
            next_action="Reject nested private provenance before dataclass conversion.",
        )

    assert not nested_log_path.exists()


def test_resolve_experiment_log_path_uses_default_log_dir_for_default_report() -> None:
    default_report_path = Path("reports/default.md")
    default_log_path = Path("reports/experiment_logs/default.json")

    assert (
        resolve_experiment_log_path(
            default_report_path,
            default_report_path=default_report_path,
            default_log_path=default_log_path,
        )
        == default_log_path
    )
    assert (
        resolve_experiment_log_path(
            default_report_path.resolve(),
            default_report_path=default_report_path,
            default_log_path=default_log_path,
        )
        == default_log_path
    )
    assert (
        resolve_experiment_log_path(
            Path("tmp/custom.md"),
            default_report_path=default_report_path,
            default_log_path=default_log_path,
        )
        == Path("tmp/custom.json")
    )
