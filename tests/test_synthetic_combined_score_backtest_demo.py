import ast
import inspect
import json
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal

import research.synthetic_combined_score_backtest_demo as demo
from backtest.portfolio import BacktestResult
from research.synthetic_combined_score_backtest_demo import (
    SyntheticCombinedScoreBacktestConfig,
    generate_synthetic_prices,
    main,
    run_synthetic_combined_score_backtest_demo,
)


def test_synthetic_price_generation_is_deterministic() -> None:
    config = SyntheticCombinedScoreBacktestConfig(price_seed=123, asset_count=6, periods=10)

    first = generate_synthetic_prices(config)
    second = generate_synthetic_prices(config)

    assert_frame_equal(first, second)
    assert first.shape == (10, 6)
    assert isinstance(first.index, pd.DatetimeIndex)
    assert first.index.is_monotonic_increasing
    assert list(first.columns[:3]) == ["ASSET_01", "ASSET_02", "ASSET_03"]
    assert first.gt(0.0).to_numpy().all()


def test_combined_score_backtest_demo_is_deterministic(tmp_path: Path) -> None:
    config = SyntheticCombinedScoreBacktestConfig(
        factor_seed=123,
        price_seed=456,
        asset_count=8,
        periods=80,
        top_n=3,
    )

    first = run_synthetic_combined_score_backtest_demo(
        config=config,
        report_path=tmp_path / "first.md",
    )
    second = run_synthetic_combined_score_backtest_demo(
        config=config,
        report_path=tmp_path / "second.md",
    )

    assert_frame_equal(first.prices, second.prices)
    assert_frame_equal(first.combined_score, second.combined_score)
    assert_frame_equal(first.correlation_matrix, second.correlation_matrix)
    assert_series_equal(first.backtest_result.equity_curve, second.backtest_result.equity_curve)
    assert (tmp_path / "first.md").read_text(encoding="utf-8") == (
        tmp_path / "second.md"
    ).read_text(encoding="utf-8")


def test_outputs_have_expected_shapes_and_alignment(tmp_path: Path) -> None:
    config = SyntheticCombinedScoreBacktestConfig(asset_count=7, periods=70, top_n=3)

    result = run_synthetic_combined_score_backtest_demo(
        config=config,
        report_path=tmp_path / "report.md",
    )

    assert result.prices.shape == (70, 7)
    for panel in result.raw_factors.values():
        assert panel.shape == result.prices.shape
        assert panel.index.equals(result.prices.index)
        assert panel.columns.equals(result.prices.columns)

    assert result.combined_score.index.equals(result.prices.index)
    assert result.combined_score.columns.equals(result.prices.columns)
    assert result.backtest_result.holdings.shape == result.prices.shape
    assert len(result.backtest_result.returns) == len(result.prices)
    assert len(result.backtest_result.equity_curve) == len(result.prices)


def test_backtest_result_exists_and_records_transaction_costs(tmp_path: Path) -> None:
    config = SyntheticCombinedScoreBacktestConfig(transaction_cost_bps=12.5)

    result = run_synthetic_combined_score_backtest_demo(
        config=config,
        report_path=tmp_path / "report.md",
    )

    assert isinstance(result.backtest_result, BacktestResult)
    assert result.backtest_result.assumptions["transaction_cost_bps"] == 12.5
    assert result.backtest_result.assumptions["signal_lag_periods"] == 1
    assert result.backtest_result.assumptions["long_only"] is True
    assert "total_transaction_cost_impact" in result.backtest_result.metrics
    assert result.backtest_result.transaction_costs.ge(0.0).all()


def test_report_is_created_with_required_warning_language(tmp_path: Path) -> None:
    report_path = tmp_path / "synthetic_combined_score_backtest_demo.md"

    run_synthetic_combined_score_backtest_demo(report_path=report_path)

    report_text = report_path.read_text(encoding="utf-8")
    assert report_path.is_file()
    assert "synthetic data only" in report_text
    assert "not real-market evidence" in report_text
    assert "not financial advice" in report_text
    assert "not a profitability claim" in report_text
    assert "synthetic diagnostics only" in report_text
    assert "should not be interpreted as strategy validation" in report_text
    assert "does not fetch real data" in report_text
    assert "connect to a broker" in report_text
    assert "support live trading" in report_text
    assert "place orders" in report_text


def test_report_contains_metrics_as_caveated_smoke_diagnostics(tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"

    run_synthetic_combined_score_backtest_demo(report_path=report_path)

    report_text = report_path.read_text(encoding="utf-8")
    assert "## Smoke-Test Metrics" in report_text
    assert "| Total return |" in report_text
    assert "These values are deterministic diagnostics from synthetic data" in report_text
    assert "not evidence of real-world performance" in report_text


def test_combined_score_demo_writes_experiment_log(tmp_path: Path) -> None:
    report_path = tmp_path / "synthetic_combined_score_backtest_demo.md"
    log_path = tmp_path / "synthetic_combined_score_backtest_demo.json"

    result = run_synthetic_combined_score_backtest_demo(
        report_path=report_path,
        experiment_log_path=log_path,
    )

    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert result.experiment_log_path == log_path
    assert payload["experiment_id"] == "synthetic-combined-score-backtest-demo"
    assert payload["experiment_type"] == "synthetic_backtest_smoke_test"
    assert payload["assumptions"]["data_scope"] == "synthetic only"
    assert payload["assumptions"]["benchmark"] == "synthetic equal-weight universe benchmark"
    assert payload["assumptions"]["signal_lag_periods"] == 1
    assert payload["assumptions"]["transaction_cost_model"].startswith("10.00 bps")
    assert payload["assumptions"]["slippage_model"].startswith("not separately modeled")
    assert payload["assumptions"]["live_trading"] is False
    assert payload["metrics"]["total_return"] == result.backtest_result.metrics["total_return"]
    assert payload["diagnostics"]["aligned_signal_coverage"] == 1.0
    assert "not strategy validation" in payload["caveats"]


def test_main_writes_report_to_requested_path(tmp_path: Path) -> None:
    report_path = tmp_path / "module_report.md"

    main(report_path=report_path)

    report_text = report_path.read_text(encoding="utf-8")
    assert report_path.is_file()
    assert "# Synthetic Combined-Score Backtest Smoke Test" in report_text


def test_demo_uses_existing_helpers(monkeypatch, tmp_path: Path) -> None:
    calls = {
        "winsorize": 0,
        "zscore": 0,
        "rank": 0,
        "correlation": 0,
        "combine": 0,
        "backtest": 0,
    }
    original_winsorize = demo.cross_sectional_winsorize_factor
    original_zscore = demo.cross_sectional_zscore_factor
    original_rank = demo.cross_sectional_rank_factor
    original_correlation = demo.factor_correlation_matrix
    original_combine = demo.combine_factors
    original_backtest = demo.run_long_only_backtest

    def count_winsorize(*args, **kwargs):
        calls["winsorize"] += 1
        return original_winsorize(*args, **kwargs)

    def count_zscore(*args, **kwargs):
        calls["zscore"] += 1
        return original_zscore(*args, **kwargs)

    def count_rank(*args, **kwargs):
        calls["rank"] += 1
        return original_rank(*args, **kwargs)

    def count_correlation(*args, **kwargs):
        calls["correlation"] += 1
        return original_correlation(*args, **kwargs)

    def count_combine(*args, **kwargs):
        calls["combine"] += 1
        return original_combine(*args, **kwargs)

    def count_backtest(*args, **kwargs):
        calls["backtest"] += 1
        return original_backtest(*args, **kwargs)

    monkeypatch.setattr(demo, "cross_sectional_winsorize_factor", count_winsorize)
    monkeypatch.setattr(demo, "cross_sectional_zscore_factor", count_zscore)
    monkeypatch.setattr(demo, "cross_sectional_rank_factor", count_rank)
    monkeypatch.setattr(demo, "factor_correlation_matrix", count_correlation)
    monkeypatch.setattr(demo, "combine_factors", count_combine)
    monkeypatch.setattr(demo, "run_long_only_backtest", count_backtest)

    run_synthetic_combined_score_backtest_demo(report_path=tmp_path / "report.md")

    assert calls == {
        "winsorize": 3,
        "zscore": 3,
        "rank": 3,
        "correlation": 1,
        "combine": 1,
        "backtest": 1,
    }


def test_demo_module_has_no_real_data_broker_or_live_trading_imports() -> None:
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


def test_demo_text_contains_only_caveated_profitability_language(tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    run_synthetic_combined_score_backtest_demo(report_path=report_path)

    source_text = inspect.getsource(demo).lower()
    report_text = report_path.read_text(encoding="utf-8").lower()
    combined_text = source_text + "\n" + report_text

    assert "not a profitability claim" in combined_text
    assert "is profitable" not in combined_text
    assert "profitable strategy" not in combined_text
    assert "strategy validation" in combined_text
