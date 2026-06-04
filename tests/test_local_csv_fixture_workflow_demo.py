import ast
import inspect
import json
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

import research.local_csv_fixture_workflow_demo as demo
from research.local_csv_fixture_workflow_demo import (
    DEFAULT_BENCHMARK_FIXTURE,
    DEFAULT_PRICE_FIXTURE,
    LocalCSVFixtureWorkflowConfig,
    main,
    run_local_csv_fixture_workflow_demo,
)


def test_local_csv_fixture_workflow_loads_committed_fixtures() -> None:
    result = run_local_csv_fixture_workflow_demo(write_outputs=False)

    assert list(result.prices.columns) == ["AAA", "BBB", "CCC"]
    assert result.prices.index.equals(
        pd.DatetimeIndex(
            ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            name="date",
        )
    )
    assert result.benchmark_prices.index.equals(result.prices.index)
    assert result.price_summary.schema == "wide_price"
    assert result.benchmark_summary.schema == "benchmark_price"
    assert result.price_summary.missing_value_count == 0
    assert result.benchmark_summary.missing_value_count == 0


def test_local_csv_fixture_workflow_outputs_are_aligned() -> None:
    result = run_local_csv_fixture_workflow_demo(write_outputs=False)

    assert result.alpha_009_factor.index.equals(result.prices.index)
    assert result.alpha_009_factor.columns.equals(result.prices.columns)
    assert result.forward_returns.index.equals(result.prices.index)
    assert result.forward_returns.columns.equals(result.prices.columns)
    assert result.benchmark_forward_returns.index.equals(result.prices.index)
    assert result.information_coefficient.index.equals(result.prices.index)
    assert result.rank_information_coefficient.index.equals(result.prices.index)
    assert result.quantile_spread.index.equals(result.prices.index)

    assert result.alpha_009_factor.notna().sum().sum() == 9
    assert result.forward_returns.notna().sum().sum() == 9
    assert result.benchmark_forward_returns.notna().sum() == 3


def test_local_csv_fixture_workflow_is_deterministic() -> None:
    first = run_local_csv_fixture_workflow_demo(write_outputs=False)
    second = run_local_csv_fixture_workflow_demo(write_outputs=False)

    assert_frame_equal(first.prices, second.prices)
    assert_series_equal(first.benchmark_prices, second.benchmark_prices)
    assert_frame_equal(first.alpha_009_factor, second.alpha_009_factor)
    assert_frame_equal(first.forward_returns, second.forward_returns)
    assert_series_equal(first.information_coefficient, second.information_coefficient)
    assert_series_equal(first.rank_information_coefficient, second.rank_information_coefficient)
    assert_frame_equal(first.quantile_spread, second.quantile_spread)


def test_workflow_report_and_experiment_log_are_created_with_caveats(tmp_path: Path) -> None:
    report_path = tmp_path / "local_csv_fixture_workflow_demo.md"
    log_path = tmp_path / "local_csv_fixture_workflow_demo.json"

    result = run_local_csv_fixture_workflow_demo(
        report_path=report_path,
        experiment_log_path=log_path,
        update_registry=False,
    )

    report_text = report_path.read_text(encoding="utf-8")
    payload = json.loads(log_path.read_text(encoding="utf-8"))

    assert result.report_path == report_path
    assert result.experiment_log_path == log_path
    assert "committed synthetic local CSV fixtures only" in report_text
    assert "not real-market evidence" in report_text
    assert "not financial advice" in report_text
    assert "not a profitability claim" in report_text
    assert "does not run a backtest" in report_text
    assert "No portfolio construction" in report_text
    assert "| Total return |" not in report_text
    assert "Sharpe" not in report_text

    assert payload["experiment_id"] == "local-csv-fixture-workflow-demo"
    assert payload["experiment_type"] == "synthetic_local_csv_workflow"
    assert payload["metrics"] == {}
    assert payload["assumptions"]["data_scope"] == "synthetic only"
    assert payload["assumptions"]["price_fixture"] == DEFAULT_PRICE_FIXTURE
    assert payload["assumptions"]["benchmark_fixture"] == DEFAULT_BENCHMARK_FIXTURE
    assert payload["assumptions"]["portfolio_construction"] == "not included"
    assert payload["assumptions"]["backtest_integration"] == "not included"
    assert payload["assumptions"]["live_trading"] is False
    assert payload["diagnostics"]["factor_valid_observations"] == 9
    assert "not strategy validation" in payload["caveats"]


def test_workflow_can_skip_report_log_and_registry_outputs(tmp_path: Path) -> None:
    report_path = tmp_path / "skipped.md"
    log_path = tmp_path / "skipped.json"

    result = run_local_csv_fixture_workflow_demo(
        report_path=report_path,
        experiment_log_path=log_path,
        write_outputs=False,
        update_registry=False,
    )

    assert result.report_path == report_path
    assert result.experiment_log_path == log_path
    assert not report_path.exists()
    assert not log_path.exists()


def test_workflow_uses_existing_loader_feature_and_diagnostic_helpers(
    monkeypatch,
) -> None:
    calls = {
        "price_loader": 0,
        "benchmark_loader": 0,
        "alpha_009": 0,
        "ic": 0,
        "rank_ic": 0,
        "quantile_spread": 0,
    }
    original_price_loader = demo.load_wide_price_csv
    original_benchmark_loader = demo.load_benchmark_price_csv
    original_alpha_009 = demo.alpha_009
    original_ic = demo.factor_information_coefficient
    original_rank_ic = demo.factor_rank_information_coefficient
    original_quantile_spread = demo.factor_quantile_spread

    def count_price_loader(*args, **kwargs):
        calls["price_loader"] += 1
        return original_price_loader(*args, **kwargs)

    def count_benchmark_loader(*args, **kwargs):
        calls["benchmark_loader"] += 1
        return original_benchmark_loader(*args, **kwargs)

    def count_alpha_009(*args, **kwargs):
        calls["alpha_009"] += 1
        return original_alpha_009(*args, **kwargs)

    def count_ic(*args, **kwargs):
        calls["ic"] += 1
        return original_ic(*args, **kwargs)

    def count_rank_ic(*args, **kwargs):
        calls["rank_ic"] += 1
        return original_rank_ic(*args, **kwargs)

    def count_quantile_spread(*args, **kwargs):
        calls["quantile_spread"] += 1
        return original_quantile_spread(*args, **kwargs)

    monkeypatch.setattr(demo, "load_wide_price_csv", count_price_loader)
    monkeypatch.setattr(demo, "load_benchmark_price_csv", count_benchmark_loader)
    monkeypatch.setattr(demo, "alpha_009", count_alpha_009)
    monkeypatch.setattr(demo, "factor_information_coefficient", count_ic)
    monkeypatch.setattr(demo, "factor_rank_information_coefficient", count_rank_ic)
    monkeypatch.setattr(demo, "factor_quantile_spread", count_quantile_spread)

    run_local_csv_fixture_workflow_demo(write_outputs=False)

    assert calls == {
        "price_loader": 1,
        "benchmark_loader": 1,
        "alpha_009": 1,
        "ic": 1,
        "rank_ic": 1,
        "quantile_spread": 1,
    }


def test_workflow_rejects_absolute_fixture_paths(tmp_path: Path) -> None:
    config = LocalCSVFixtureWorkflowConfig(price_fixture=str(tmp_path / "prices.csv"))

    with pytest.raises(ValueError, match="project-relative"):
        run_local_csv_fixture_workflow_demo(config=config, write_outputs=False)


def test_workflow_rejects_invalid_config_values() -> None:
    config = LocalCSVFixtureWorkflowConfig(forward_return_horizon_rows=0)

    with pytest.raises(ValueError, match="forward_return_horizon_rows"):
        run_local_csv_fixture_workflow_demo(config=config, write_outputs=False)


def test_main_writes_report_to_requested_path(tmp_path: Path) -> None:
    report_path = tmp_path / "module_report.md"

    main(report_path=report_path, update_registry=False)

    report_text = report_path.read_text(encoding="utf-8")
    assert report_path.is_file()
    assert "# Local CSV Fixture Workflow Demo" in report_text


def test_workflow_module_has_no_real_data_broker_or_live_trading_imports() -> None:
    source = inspect.getsource(demo)
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


def test_workflow_text_contains_only_caveated_profitability_language(tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    run_local_csv_fixture_workflow_demo(report_path=report_path, update_registry=False)

    source_text = inspect.getsource(demo).lower()
    report_text = report_path.read_text(encoding="utf-8").lower()
    combined_text = source_text + "\n" + report_text

    assert "not a profitability claim" in combined_text
    assert "is profitable" not in combined_text
    assert "profitable strategy" not in combined_text
    assert "not strategy validation" in combined_text
