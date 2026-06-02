import ast
import inspect
import json
from pathlib import Path

from pandas.testing import assert_frame_equal
import pytest

import research.synthetic_multifactor_parameter_sweep as sweep
from research.synthetic_multifactor_parameter_sweep import (
    SyntheticParameterSweepConfig,
    main,
    run_synthetic_multifactor_parameter_sweep,
)


def test_parameter_sweep_runs_all_configured_cases(tmp_path: Path) -> None:
    config = SyntheticParameterSweepConfig(top_n_values=(3, 4))

    result = run_synthetic_multifactor_parameter_sweep(
        config=config,
        report_path=tmp_path / "sweep.md",
        experiment_log_path=tmp_path / "sweep.json",
        update_registry=False,
    )

    expected_case_count = len(config.weight_sets) * len(config.top_n_values)
    assert len(result.results) == expected_case_count
    assert result.results["case_id"].is_unique
    assert set(result.results["weight_set"]) == set(config.weight_sets)
    assert set(result.results["top_n"]) == set(config.top_n_values)
    assert result.results["total_return"].notna().all()


def test_parameter_sweep_is_deterministic(tmp_path: Path) -> None:
    config = SyntheticParameterSweepConfig(top_n_values=(3, 4))

    first = run_synthetic_multifactor_parameter_sweep(
        config=config,
        report_path=tmp_path / "first.md",
        experiment_log_path=tmp_path / "first.json",
        update_registry=False,
    )
    second = run_synthetic_multifactor_parameter_sweep(
        config=config,
        report_path=tmp_path / "second.md",
        experiment_log_path=tmp_path / "second.json",
        update_registry=False,
    )

    assert_frame_equal(first.results, second.results)
    assert (tmp_path / "first.md").read_text(encoding="utf-8") == (
        tmp_path / "second.md"
    ).read_text(encoding="utf-8")


def test_parameter_sweep_report_and_log_are_caveated(tmp_path: Path) -> None:
    report_path = tmp_path / "synthetic_multifactor_parameter_sweep.md"
    log_path = tmp_path / "synthetic_multifactor_parameter_sweep.json"

    result = run_synthetic_multifactor_parameter_sweep(
        report_path=report_path,
        experiment_log_path=log_path,
        update_registry=False,
    )

    report_text = report_path.read_text(encoding="utf-8")
    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert result.report_path == report_path
    assert result.experiment_log_path == log_path
    assert "synthetic data only" in report_text
    assert "not real-market evidence" in report_text
    assert "not financial advice" in report_text
    assert "not a profitability claim" in report_text
    assert "All parameter cases are shown" in report_text
    assert "weak or negative diagnostics" in report_text
    assert "not evidence of real-world performance or strategy validation" in report_text
    assert "does not identify a best parameter set" in report_text
    assert payload["experiment_id"] == "synthetic-multifactor-parameter-sweep"
    assert payload["experiment_type"] == "synthetic_parameter_sweep"
    assert payload["metrics"] == {}
    assert payload["outputs"]["case_count"] == len(result.results)
    assert len(payload["diagnostics"]["cases"]) == len(result.results)
    assert "all parameter cases reported" in payload["caveats"]
    assert "not parameter optimization" in payload["caveats"]
    assert payload["assumptions"]["parameter_policy"] == "all configured cases are reported; no best-only filtering"


def test_main_writes_requested_report_and_log(tmp_path: Path) -> None:
    report_path = tmp_path / "module_report.md"
    log_path = tmp_path / "module_log.json"

    main(report_path=report_path, experiment_log_path=log_path, update_registry=False)

    assert report_path.is_file()
    assert log_path.is_file()
    assert "# Synthetic Multi-Factor Parameter Sweep" in report_path.read_text(encoding="utf-8")


def test_parameter_sweep_validates_weight_sets_and_top_n_values(tmp_path: Path) -> None:
    invalid_weight_config = SyntheticParameterSweepConfig(
        weight_sets={"bad": {"synthetic_momentum": 1.0}},
    )
    with pytest.raises(ValueError, match="must exactly match synthetic factor names"):
        run_synthetic_multifactor_parameter_sweep(
            config=invalid_weight_config,
            report_path=tmp_path / "bad.md",
            experiment_log_path=tmp_path / "bad.json",
            update_registry=False,
        )

    invalid_top_n_config = SyntheticParameterSweepConfig(top_n_values=(0,))
    with pytest.raises(ValueError, match="top_n_values must be positive"):
        run_synthetic_multifactor_parameter_sweep(
            config=invalid_top_n_config,
            report_path=tmp_path / "bad_top_n.md",
            experiment_log_path=tmp_path / "bad_top_n.json",
            update_registry=False,
        )


def test_parameter_sweep_module_has_no_forbidden_imports() -> None:
    source = inspect.getsource(sweep)
    tree = ast.parse(source)
    forbidden_terms = [
        "requests",
        "urllib",
        "yfinance",
        "alpaca",
        "ccxt",
        "broker",
        "brokerage",
        "order",
        "execution",
        "live_trading",
        "real_data",
    ]

    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    for module_name in imported_modules:
        assert not any(term in module_name for term in forbidden_terms)
