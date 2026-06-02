import ast
import inspect
import json
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

import research.synthetic_multifactor_workflow_demo as workflow
from research.synthetic_multifactor_workflow_demo import (
    FACTOR_NAMES,
    SyntheticMultifactorWorkflowConfig,
    generate_synthetic_factor_panels,
    main,
    run_synthetic_multifactor_workflow_demo,
)


def test_synthetic_factor_generation_is_reproducible() -> None:
    config = SyntheticMultifactorWorkflowConfig(seed=123, asset_count=6, periods=10)

    first = generate_synthetic_factor_panels(config)
    second = generate_synthetic_factor_panels(config)

    assert list(first) == list(FACTOR_NAMES)
    for factor_name in FACTOR_NAMES:
        assert_frame_equal(first[factor_name], second[factor_name])


def test_generated_synthetic_factor_panels_have_expected_shape_and_labels() -> None:
    config = SyntheticMultifactorWorkflowConfig(seed=123, asset_count=5, periods=7)

    factors = generate_synthetic_factor_panels(config)

    for panel in factors.values():
        assert panel.shape == (7, 5)
        assert isinstance(panel.index, pd.DatetimeIndex)
        assert panel.index.is_monotonic_increasing
        assert list(panel.columns) == [
            "ASSET_01",
            "ASSET_02",
            "ASSET_03",
            "ASSET_04",
            "ASSET_05",
        ]
        assert not panel.isna().to_numpy().any()


def test_synthetic_multifactor_workflow_is_reproducible(tmp_path: Path) -> None:
    config = SyntheticMultifactorWorkflowConfig(seed=321, asset_count=8, periods=12)
    first_report = tmp_path / "first.md"
    second_report = tmp_path / "second.md"

    first = run_synthetic_multifactor_workflow_demo(
        config=config,
        report_path=first_report,
    )
    second = run_synthetic_multifactor_workflow_demo(
        config=config,
        report_path=second_report,
    )

    assert_frame_equal(first.combined_score, second.combined_score)
    assert_frame_equal(first.correlation_matrix, second.correlation_matrix)
    assert first_report.read_text(encoding="utf-8") == second_report.read_text(encoding="utf-8")


def test_workflow_report_is_created_with_required_warnings(tmp_path: Path) -> None:
    report_path = tmp_path / "synthetic_multifactor_workflow_demo.md"

    result = run_synthetic_multifactor_workflow_demo(report_path=report_path)

    report_text = report_path.read_text(encoding="utf-8")
    assert result.report_path == report_path
    assert report_path.is_file()
    assert "synthetic data only" in report_text
    assert "not real-market evidence" in report_text
    assert "not financial advice" in report_text
    assert "not a profitability claim" in report_text
    assert "does not run a backtest" in report_text
    assert "No backtest integration or portfolio construction is included." in report_text
    assert "| Total return |" not in report_text
    assert "Sharpe" not in report_text


def test_workflow_writes_experiment_log(tmp_path: Path) -> None:
    report_path = tmp_path / "synthetic_multifactor_workflow_demo.md"
    log_path = tmp_path / "synthetic_multifactor_workflow_demo.json"

    result = run_synthetic_multifactor_workflow_demo(
        report_path=report_path,
        experiment_log_path=log_path,
    )

    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert result.experiment_log_path == log_path
    assert payload["experiment_id"] == "synthetic-multifactor-workflow-demo"
    assert payload["experiment_type"] == "synthetic_feature_workflow"
    assert payload["metrics"] == {}
    assert payload["assumptions"]["data_scope"] == "synthetic only"
    assert payload["assumptions"]["portfolio_construction"] == "not included"
    assert payload["assumptions"]["backtest_integration"] == "not included"
    assert payload["assumptions"]["transaction_cost_model"] == "not applicable; no portfolio or trades"
    assert payload["diagnostics"]["factor_names"] == list(FACTOR_NAMES)
    assert "not a strategy signal or portfolio" in payload["caveats"]


def test_combined_score_preserves_index_and_columns(tmp_path: Path) -> None:
    config = SyntheticMultifactorWorkflowConfig(seed=123, asset_count=7, periods=9)

    result = run_synthetic_multifactor_workflow_demo(
        config=config,
        report_path=tmp_path / "report.md",
    )
    reference = result.raw_factors["synthetic_momentum"]

    assert result.combined_score.index.equals(reference.index)
    assert result.combined_score.columns.equals(reference.columns)
    assert not result.combined_score.isna().to_numpy().any()


def test_correlation_matrix_preserves_factor_names(tmp_path: Path) -> None:
    result = run_synthetic_multifactor_workflow_demo(report_path=tmp_path / "report.md")

    expected_names = list(FACTOR_NAMES)
    assert list(result.correlation_matrix.index) == expected_names
    assert list(result.correlation_matrix.columns) == expected_names


def test_workflow_uses_existing_feature_helpers(monkeypatch, tmp_path: Path) -> None:
    calls = {
        "winsorize": 0,
        "zscore": 0,
        "rank": 0,
        "percentile_rank": 0,
        "correlation": 0,
        "combine": 0,
    }
    original_winsorize = workflow.cross_sectional_winsorize_factor
    original_zscore = workflow.cross_sectional_zscore_factor
    original_rank = workflow.cross_sectional_rank_factor
    original_percentile_rank = workflow.cross_sectional_percentile_rank_factor
    original_correlation = workflow.factor_correlation_matrix
    original_combine = workflow.combine_factors

    def count_winsorize(*args, **kwargs):
        calls["winsorize"] += 1
        return original_winsorize(*args, **kwargs)

    def count_zscore(*args, **kwargs):
        calls["zscore"] += 1
        return original_zscore(*args, **kwargs)

    def count_rank(*args, **kwargs):
        calls["rank"] += 1
        return original_rank(*args, **kwargs)

    def count_percentile_rank(*args, **kwargs):
        calls["percentile_rank"] += 1
        return original_percentile_rank(*args, **kwargs)

    def count_correlation(*args, **kwargs):
        calls["correlation"] += 1
        return original_correlation(*args, **kwargs)

    def count_combine(*args, **kwargs):
        calls["combine"] += 1
        return original_combine(*args, **kwargs)

    monkeypatch.setattr(workflow, "cross_sectional_winsorize_factor", count_winsorize)
    monkeypatch.setattr(workflow, "cross_sectional_zscore_factor", count_zscore)
    monkeypatch.setattr(workflow, "cross_sectional_rank_factor", count_rank)
    monkeypatch.setattr(
        workflow,
        "cross_sectional_percentile_rank_factor",
        count_percentile_rank,
    )
    monkeypatch.setattr(workflow, "factor_correlation_matrix", count_correlation)
    monkeypatch.setattr(workflow, "combine_factors", count_combine)

    run_synthetic_multifactor_workflow_demo(report_path=tmp_path / "report.md")

    assert calls == {
        "winsorize": len(FACTOR_NAMES),
        "zscore": len(FACTOR_NAMES),
        "rank": len(FACTOR_NAMES),
        "percentile_rank": len(FACTOR_NAMES),
        "correlation": 1,
        "combine": 1,
    }


def test_main_writes_report_to_requested_path(tmp_path: Path) -> None:
    report_path = tmp_path / "module_report.md"

    main(report_path=report_path)

    report_text = report_path.read_text(encoding="utf-8")
    assert report_path.is_file()
    assert "# Synthetic Multi-Factor Workflow Demo" in report_text


def test_workflow_module_has_no_forbidden_imports() -> None:
    source = inspect.getsource(workflow)
    tree = ast.parse(source)
    forbidden_terms = [
        "backtest",
        "portfolio",
        "metrics",
        "strategies",
        "reporting",
        "worldquant_alphas",
        "requests",
        "urllib",
        "yfinance",
        "alpaca",
        "ccxt",
        "broker",
        "order",
        "live_trading",
    ]

    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    allowed_modules = {"reporting.experiment_log"}
    for module_name in imported_modules:
        if module_name in allowed_modules:
            continue
        assert not any(term in module_name for term in forbidden_terms)


def test_workflow_text_contains_only_caveated_profitability_language(tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    run_synthetic_multifactor_workflow_demo(report_path=report_path)

    source_text = inspect.getsource(workflow).lower()
    report_text = report_path.read_text(encoding="utf-8").lower()
    combined_text = source_text + "\n" + report_text

    assert "not a profitability claim" in combined_text
    assert "is profitable" not in combined_text
    assert "profitable strategy" not in combined_text
