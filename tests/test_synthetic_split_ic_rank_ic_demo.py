import ast
import inspect
import json
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

import research.synthetic_split_ic_rank_ic_demo as demo
from research.synthetic_split_ic_rank_ic_demo import (
    SyntheticSplitICRankICConfig,
    main,
    run_synthetic_split_ic_rank_ic_demo,
)


def test_split_ic_rank_ic_demo_builds_expected_split_windows() -> None:
    result = run_synthetic_split_ic_rank_ic_demo(write_outputs=False)

    assert list(result.factor.columns) == [
        "ASSET_01",
        "ASSET_02",
        "ASSET_03",
        "ASSET_04",
        "ASSET_05",
        "ASSET_06",
    ]
    assert result.factor.index.equals(
        pd.bdate_range("2024-01-02", periods=12),
    )
    assert list(result.factor_by_split) == ["train", "validation", "test"]
    assert list(result.summary.index) == ["train", "validation", "test"]
    assert result.summary["date_count"].to_dict() == {
        "train": 4,
        "validation": 4,
        "test": 4,
    }
    assert result.split.train_end == pd.Timestamp("2024-01-05")
    assert result.split.validation_end == pd.Timestamp("2024-01-11")
    assert result.split.test_end == pd.Timestamp("2024-01-17")


def test_split_ic_rank_ic_demo_outputs_are_aligned_and_preserve_missing_values() -> None:
    result = run_synthetic_split_ic_rank_ic_demo(write_outputs=False)

    assert result.factor.index.equals(result.forward_returns.index)
    assert result.factor.columns.equals(result.forward_returns.columns)

    for split_name in ("train", "validation", "test"):
        assert result.factor_by_split[split_name].index.equals(
            result.forward_returns_by_split[split_name].index,
        )
        assert result.factor_by_split[split_name].columns.equals(
            result.forward_returns_by_split[split_name].columns,
        )
        assert result.information_coefficient_by_split[split_name].index.equals(
            result.factor_by_split[split_name].index,
        )
        assert result.rank_information_coefficient_by_split[split_name].index.equals(
            result.factor_by_split[split_name].index,
        )

    assert pd.isna(result.factor.loc[pd.Timestamp("2024-01-09"), "ASSET_02"])
    assert pd.isna(
        result.forward_returns.loc[pd.Timestamp("2024-01-16"), "ASSET_04"],
    )
    assert result.summary.loc["validation", "factor_valid_observations"] == 23
    assert result.summary.loc["test", "forward_return_valid_observations"] == 23


def test_split_ic_rank_ic_demo_is_deterministic() -> None:
    first = run_synthetic_split_ic_rank_ic_demo(write_outputs=False)
    second = run_synthetic_split_ic_rank_ic_demo(write_outputs=False)

    assert_frame_equal(first.factor, second.factor)
    assert_frame_equal(first.forward_returns, second.forward_returns)
    assert_frame_equal(first.summary, second.summary)
    for split_name in ("train", "validation", "test"):
        assert_series_equal(
            first.information_coefficient_by_split[split_name],
            second.information_coefficient_by_split[split_name],
        )
        assert_series_equal(
            first.rank_information_coefficient_by_split[split_name],
            second.rank_information_coefficient_by_split[split_name],
        )


def test_split_ic_rank_ic_demo_summary_is_hand_checked() -> None:
    result = run_synthetic_split_ic_rank_ic_demo(write_outputs=False)

    assert result.summary.loc["train", "mean_ic"] == pytest.approx(1.0)
    assert result.summary.loc["validation", "mean_ic"] == pytest.approx(-1.0)
    assert result.summary.loc["test", "mean_ic"] == pytest.approx(1.0)
    assert result.summary.loc["train", "mean_rank_ic"] == pytest.approx(1.0)
    assert result.summary.loc["validation", "mean_rank_ic"] == pytest.approx(-1.0)
    assert result.summary.loc["test", "mean_rank_ic"] == pytest.approx(1.0)
    assert result.summary["ic_valid_dates"].to_dict() == {
        "train": 4,
        "validation": 4,
        "test": 4,
    }


def test_split_ic_rank_ic_demo_can_skip_outputs(tmp_path: Path) -> None:
    report_path = tmp_path / "skipped.md"
    log_path = tmp_path / "skipped.json"

    result = run_synthetic_split_ic_rank_ic_demo(
        report_path=report_path,
        experiment_log_path=log_path,
        write_outputs=False,
    )

    assert result.report_path == report_path
    assert result.experiment_log_path == log_path
    assert not report_path.exists()
    assert not log_path.exists()


def test_split_ic_rank_ic_demo_writes_caveated_report_and_log(tmp_path: Path) -> None:
    report_path = tmp_path / "synthetic_split_ic_rank_ic_demo.md"
    log_path = tmp_path / "synthetic_split_ic_rank_ic_demo.json"

    result = run_synthetic_split_ic_rank_ic_demo(
        report_path=report_path,
        experiment_log_path=log_path,
    )

    report_text = report_path.read_text(encoding="utf-8")
    payload = json.loads(log_path.read_text(encoding="utf-8"))

    assert result.report_path == report_path
    assert result.experiment_log_path == log_path
    assert "# Synthetic Split-Aware IC / Rank IC Demo" in report_text
    assert "deterministic synthetic panels only" in report_text
    assert "not real-market evidence" in report_text
    assert "not a profitability claim" in report_text
    assert "does not fetch real data" in report_text
    assert "No portfolio construction" in report_text
    assert "not model selection" in payload["caveats"]

    assert payload["experiment_id"] == "synthetic-split-ic-rank-ic-demo"
    assert payload["experiment_type"] == "synthetic_split_diagnostic_demo"
    assert payload["metrics"] == {}
    assert payload["assumptions"]["data_scope"] == "synthetic only"
    assert payload["assumptions"]["portfolio_construction"] == "not included"
    assert payload["assumptions"]["backtest_integration"] == "not included"
    assert payload["assumptions"]["live_trading"] is False
    assert payload["diagnostics"]["summary"]["train"]["date_count"] == 4


def test_split_ic_rank_ic_demo_uses_split_and_diagnostic_helpers(monkeypatch) -> None:
    calls = {
        "make_split": 0,
        "split_panel": 0,
        "ic": 0,
        "rank_ic": 0,
    }
    original_make_split = demo.make_train_validation_test_split
    original_split_panel = demo.split_panel_by_train_validation_test
    original_ic = demo.factor_information_coefficient
    original_rank_ic = demo.factor_rank_information_coefficient

    def count_make_split(*args, **kwargs):
        calls["make_split"] += 1
        return original_make_split(*args, **kwargs)

    def count_split_panel(*args, **kwargs):
        calls["split_panel"] += 1
        return original_split_panel(*args, **kwargs)

    def count_ic(*args, **kwargs):
        calls["ic"] += 1
        return original_ic(*args, **kwargs)

    def count_rank_ic(*args, **kwargs):
        calls["rank_ic"] += 1
        return original_rank_ic(*args, **kwargs)

    monkeypatch.setattr(demo, "make_train_validation_test_split", count_make_split)
    monkeypatch.setattr(demo, "split_panel_by_train_validation_test", count_split_panel)
    monkeypatch.setattr(demo, "factor_information_coefficient", count_ic)
    monkeypatch.setattr(demo, "factor_rank_information_coefficient", count_rank_ic)

    run_synthetic_split_ic_rank_ic_demo(write_outputs=False)

    assert calls == {
        "make_split": 1,
        "split_panel": 2,
        "ic": 3,
        "rank_ic": 3,
    }


def test_split_ic_rank_ic_demo_rejects_invalid_config_values() -> None:
    config = SyntheticSplitICRankICConfig(ic_min_periods=7)

    with pytest.raises(ValueError, match="ic_min_periods"):
        run_synthetic_split_ic_rank_ic_demo(config=config, write_outputs=False)


def test_split_ic_rank_ic_demo_main_writes_requested_report(tmp_path: Path) -> None:
    report_path = tmp_path / "module_report.md"
    log_path = tmp_path / "module_log.json"

    main(report_path=report_path, experiment_log_path=log_path)

    assert report_path.is_file()
    assert log_path.is_file()
    assert "# Synthetic Split-Aware IC / Rank IC Demo" in report_path.read_text(
        encoding="utf-8",
    )


def test_split_ic_rank_ic_module_has_no_real_data_broker_or_live_trading_imports() -> None:
    source = inspect.getsource(demo)
    tree = ast.parse(source)
    forbidden_terms = [
        "requests",
        "urllib",
        "yfinance",
        "alpaca",
        "ccxt",
        "broker",
        "order",
        "execution",
        "live_trading",
        "real_data",
        "backtest",
    ]

    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    for module_name in imported_modules:
        assert not any(term in module_name for term in forbidden_terms)


def test_split_ic_rank_ic_text_contains_only_caveated_profitability_language(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "report.md"
    run_synthetic_split_ic_rank_ic_demo(report_path=report_path)

    source_text = inspect.getsource(demo).lower()
    report_text = report_path.read_text(encoding="utf-8").lower()
    combined_text = source_text + "\n" + report_text

    assert "not a profitability claim" in combined_text
    assert "is profitable" not in combined_text
    assert "profitable strategy" not in combined_text
    assert "not strategy validation" in combined_text
