from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path

import pytest

from reporting.experiment_log import (
    SYNTHETIC_RESEARCH_CAVEATS,
    resolve_experiment_log_path,
    write_experiment_log,
)


@dataclass(frozen=True)
class ExampleConfig:
    seed: int
    run_date: date


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
