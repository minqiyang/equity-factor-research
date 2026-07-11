import ast
import inspect
import json
from pathlib import Path

import pandas as pd
import pytest

import reporting.experiment_registry as registry_module
from reporting.experiment_log import SYNTHETIC_RESEARCH_CAVEATS, write_experiment_log
from reporting.experiment_registry import (
    REGISTRY_COLUMNS,
    build_experiment_registry,
    load_experiment_log,
    render_experiment_registry_markdown,
    write_experiment_registry_report,
)


def _write_log(
    log_path: Path,
    *,
    experiment_id: str,
    title: str,
    metrics: dict[str, float] | None = None,
) -> None:
    write_experiment_log(
        log_path=log_path,
        experiment_id=experiment_id,
        title=title,
        experiment_type="synthetic_backtest_smoke_test",
        summary=f"Synthetic summary for {title}.",
        config={"seed": 123},
        assumptions={
            "data_scope": "synthetic only",
            "date_range": {"start": "2024-01-02", "end": "2024-02-01"},
            "universe": "3 synthetic assets",
            "benchmark": "synthetic benchmark",
            "transaction_cost_model": (
                "fixed_bps_on_target_weight_turnover; "
                "10.00 bps per unit of target-weight turnover"
            ),
            "slippage_model": (
                "fixed_bps_on_target_weight_turnover; "
                "0.00 bps per unit of target-weight turnover"
            ),
        },
        outputs={
            "markdown_report": f"reports/{experiment_id}.md",
            "experiment_log": f"reports/experiment_logs/{experiment_id}.json",
        },
        metrics=metrics or {},
        caveats=(*SYNTHETIC_RESEARCH_CAVEATS, "workflow diagnostics only"),
        next_action="Keep this as a synthetic diagnostic.",
    )


def test_build_experiment_registry_is_structured_and_sorted(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    _write_log(
        log_dir / "z_demo.json",
        experiment_id="z-demo",
        title="Z Demo",
        metrics={
            "total_return": -0.01,
            "annualized_return": -0.02,
            "tracking_error": 0.03,
        },
    )
    _write_log(
        log_dir / "a_demo.json",
        experiment_id="a-demo",
        title="A Demo",
    )

    registry = build_experiment_registry(log_dir)

    assert list(registry.columns) == list(REGISTRY_COLUMNS)
    assert list(registry["experiment_id"]) == ["a-demo", "z-demo"]
    assert bool(registry.loc[0, "metrics_available"]) is False
    assert bool(registry.loc[1, "metrics_available"]) is True
    assert registry.loc[1, "total_return"] == -0.01
    assert registry.loc[1, "tracking_error"] == 0.03
    assert registry.loc[1, "data_scope"] == "synthetic only"
    assert registry.loc[1, "slippage_model"].startswith("fixed_bps_on_target_weight_turnover")


def test_write_experiment_registry_report_contains_caveats_and_metrics(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    report_path = tmp_path / "registry.md"
    _write_log(
        log_dir / "demo.json",
        experiment_id="demo",
        title="Demo",
        metrics={
            "total_return": 0.12345678,
            "tracking_error": 0.07654321,
            "sharpe_ratio": -0.5,
        },
    )

    registry = write_experiment_registry_report(log_dir=log_dir, report_path=report_path)

    report_text = report_path.read_text(encoding="utf-8")
    assert isinstance(registry, pd.DataFrame)
    assert "# Synthetic Experiment Registry" in report_text
    assert "synthetic demos only" in report_text
    assert "not financial advice" in report_text
    assert "not a profitability claim" in report_text
    assert "workflow diagnostics only" in report_text
    assert "0.123457" in report_text
    assert "0.0765432" in report_text
    assert "Missing metric cells mean" in report_text


def test_load_experiment_log_rejects_missing_required_caveat(tmp_path: Path) -> None:
    log_path = tmp_path / "bad.json"
    _write_log(log_path, experiment_id="bad", title="Bad")
    payload = json.loads(log_path.read_text(encoding="utf-8"))
    payload["caveats"] = ["synthetic data only"]
    log_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="missing required caveats"):
        load_experiment_log(log_path)


def test_build_experiment_registry_rejects_duplicate_experiment_ids(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    _write_log(log_dir / "first.json", experiment_id="duplicate", title="First")
    _write_log(log_dir / "second.json", experiment_id="duplicate", title="Second")

    with pytest.raises(ValueError, match="duplicate experiment_id"):
        build_experiment_registry(log_dir)


def test_render_experiment_registry_markdown_requires_registry_columns() -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        render_experiment_registry_markdown(pd.DataFrame({"experiment_id": ["demo"]}))


def test_experiment_registry_module_has_no_forbidden_imports() -> None:
    source = inspect.getsource(registry_module)
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
