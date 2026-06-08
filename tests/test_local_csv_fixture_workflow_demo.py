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
    DEFAULT_OHLCV_FIXTURE,
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
    assert result.ohlcv["symbol"].tolist() == ["AAA", "BBB", "AAA", "BBB"]
    assert result.price_summary.schema == "wide_price"
    assert result.benchmark_summary.schema == "benchmark_price"
    assert result.ohlcv_summary.schema == "ohlcv_long"
    assert result.price_summary.missing_value_count == 0
    assert result.benchmark_summary.missing_value_count == 0
    assert result.ohlcv_summary.missing_value_count == 0
    assert result.split.train.equals(pd.DatetimeIndex(["2024-01-02"], name="date"))
    assert result.split.validation.equals(pd.DatetimeIndex(["2024-01-03"], name="date"))
    assert result.split.test.equals(
        pd.DatetimeIndex(["2024-01-04", "2024-01-05"], name="date")
    )
    assert result.split.train_end == pd.Timestamp("2024-01-02")
    assert result.split.validation_end == pd.Timestamp("2024-01-03")
    assert result.split.test_end == pd.Timestamp("2024-01-05")


def test_local_csv_fixture_workflow_outputs_are_aligned() -> None:
    result = run_local_csv_fixture_workflow_demo(write_outputs=False)

    assert result.alpha_009_factor.index.equals(result.prices.index)
    assert result.alpha_009_factor.columns.equals(result.prices.columns)
    assert result.forward_returns.index.equals(result.prices.index)
    assert result.forward_returns.columns.equals(result.prices.columns)
    assert result.benchmark_forward_returns.index.equals(result.prices.index)
    assert result.liquidity_price_panel.index.equals(result.prices.index)
    assert result.liquidity_price_panel.columns.equals(result.prices.columns)
    assert result.liquidity_volume_panel.index.equals(result.prices.index)
    assert result.liquidity_volume_panel.columns.equals(result.prices.columns)
    assert result.average_daily_volume_eligibility.index.equals(result.prices.index)
    assert result.average_daily_volume_eligibility.columns.equals(result.prices.columns)
    assert result.average_dollar_volume_eligibility.index.equals(result.prices.index)
    assert result.average_dollar_volume_eligibility.columns.equals(result.prices.columns)
    assert result.liquidity_eligibility_summary.index.equals(result.prices.index)
    assert result.liquidity_universe_result.universe_mask.index.equals(
        result.prices.index,
    )
    assert result.liquidity_universe_result.universe_mask.columns.equals(
        result.prices.columns,
    )
    assert result.liquidity_universe_result.summary.index.equals(result.prices.index)
    assert result.masked_alpha_009_signals.signals.index.equals(result.prices.index)
    assert result.masked_alpha_009_signals.signals.columns.equals(result.prices.columns)
    assert result.masked_alpha_009_signals.summary.index.equals(result.prices.index)
    assert result.alpha_012_factor.index.equals(result.prices.index)
    assert result.alpha_012_factor.columns.equals(result.prices.columns)
    assert result.information_coefficient.index.equals(result.prices.index)
    assert result.rank_information_coefficient.index.equals(result.prices.index)
    assert result.quantile_spread.index.equals(result.prices.index)
    assert result.alpha_012_information_coefficient.index.equals(result.prices.index)
    assert result.alpha_012_rank_information_coefficient.index.equals(result.prices.index)
    assert result.alpha_012_quantile_spread.index.equals(result.prices.index)
    assert list(result.alpha_009_factor_by_split) == ["train", "validation", "test"]
    assert list(result.alpha_012_factor_by_split) == ["train", "validation", "test"]
    assert list(result.forward_returns_by_split) == ["train", "validation", "test"]
    assert list(result.split_summary.index) == ["train", "validation", "test"]

    for split_name in ("train", "validation", "test"):
        assert result.alpha_009_factor_by_split[split_name].index.equals(
            result.forward_returns_by_split[split_name].index,
        )
        assert result.alpha_009_factor_by_split[split_name].columns.equals(
            result.forward_returns_by_split[split_name].columns,
        )
        assert result.alpha_012_factor_by_split[split_name].index.equals(
            result.forward_returns_by_split[split_name].index,
        )
        assert result.alpha_012_factor_by_split[split_name].columns.equals(
            result.forward_returns_by_split[split_name].columns,
        )
        assert result.information_coefficient_by_split[split_name].index.equals(
            result.alpha_009_factor_by_split[split_name].index,
        )
        assert result.rank_information_coefficient_by_split[split_name].index.equals(
            result.alpha_009_factor_by_split[split_name].index,
        )
        assert result.quantile_spread_by_split[split_name].index.equals(
            result.alpha_009_factor_by_split[split_name].index,
        )
        assert result.alpha_012_information_coefficient_by_split[split_name].index.equals(
            result.alpha_012_factor_by_split[split_name].index,
        )
        assert result.alpha_012_rank_information_coefficient_by_split[split_name].index.equals(
            result.alpha_012_factor_by_split[split_name].index,
        )
        assert result.alpha_012_quantile_spread_by_split[split_name].index.equals(
            result.alpha_012_factor_by_split[split_name].index,
        )

    assert result.alpha_009_factor.notna().sum().sum() == 9
    assert result.alpha_012_factor.notna().sum().sum() == 2
    assert result.alpha_012_factor.loc[pd.Timestamp("2024-01-03"), "AAA"] == pytest.approx(-0.75)
    assert result.alpha_012_factor.loc[pd.Timestamp("2024-01-03"), "BBB"] == pytest.approx(-0.50)
    assert result.alpha_012_information_coefficient.notna().sum() == 1
    assert result.alpha_012_rank_information_coefficient.notna().sum() == 1
    assert result.alpha_012_quantile_spread["top_minus_bottom_spread"].notna().sum() == 0
    assert result.forward_returns.notna().sum().sum() == 9
    assert result.benchmark_forward_returns.notna().sum() == 3
    assert result.liquidity_volume_panel.notna().sum(axis=1).to_dict() == {
        pd.Timestamp("2024-01-02"): 2,
        pd.Timestamp("2024-01-03"): 2,
        pd.Timestamp("2024-01-04"): 0,
        pd.Timestamp("2024-01-05"): 0,
    }
    assert result.average_daily_volume_eligibility.sum(axis=1).to_dict() == {
        pd.Timestamp("2024-01-02"): 0,
        pd.Timestamp("2024-01-03"): 0,
        pd.Timestamp("2024-01-04"): 2,
        pd.Timestamp("2024-01-05"): 0,
    }
    assert result.average_dollar_volume_eligibility.sum(axis=1).to_dict() == {
        pd.Timestamp("2024-01-02"): 0,
        pd.Timestamp("2024-01-03"): 0,
        pd.Timestamp("2024-01-04"): 1,
        pd.Timestamp("2024-01-05"): 0,
    }
    assert result.liquidity_eligibility_summary["missing_volume_count"].to_dict() == {
        pd.Timestamp("2024-01-02"): 1,
        pd.Timestamp("2024-01-03"): 1,
        pd.Timestamp("2024-01-04"): 3,
        pd.Timestamp("2024-01-05"): 3,
    }
    assert result.liquidity_eligibility_summary["zero_volume_count"].to_dict() == {
        pd.Timestamp("2024-01-02"): 0,
        pd.Timestamp("2024-01-03"): 0,
        pd.Timestamp("2024-01-04"): 0,
        pd.Timestamp("2024-01-05"): 0,
    }
    assert result.liquidity_universe_result.universe_mask.sum(axis=1).to_dict() == {
        pd.Timestamp("2024-01-02"): 0,
        pd.Timestamp("2024-01-03"): 0,
        pd.Timestamp("2024-01-04"): 1,
        pd.Timestamp("2024-01-05"): 0,
    }
    assert result.liquidity_universe_result.summary["raw_eligible_count"].to_dict() == {
        pd.Timestamp("2024-01-02"): 0,
        pd.Timestamp("2024-01-03"): 0,
        pd.Timestamp("2024-01-04"): 1,
        pd.Timestamp("2024-01-05"): 0,
    }
    assert result.liquidity_universe_result.summary["low_coverage"].to_dict() == {
        pd.Timestamp("2024-01-02"): True,
        pd.Timestamp("2024-01-03"): True,
        pd.Timestamp("2024-01-04"): False,
        pd.Timestamp("2024-01-05"): True,
    }
    assert result.liquidity_universe_result.low_coverage_dates == (
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-05"),
    )
    expected_masked_alpha_009_signals = pd.DataFrame(
        {
            "AAA": [float("nan"), float("nan"), float("nan"), float("nan")],
            "BBB": [float("nan"), float("nan"), 0.75, float("nan")],
            "CCC": [float("nan"), float("nan"), float("nan"), float("nan")],
        },
        index=result.prices.index,
    )
    assert_frame_equal(
        result.masked_alpha_009_signals.signals,
        expected_masked_alpha_009_signals,
    )
    assert result.masked_alpha_009_signals.summary[
        "valid_masked_signal_count"
    ].to_dict() == {
        pd.Timestamp("2024-01-02"): 0,
        pd.Timestamp("2024-01-03"): 0,
        pd.Timestamp("2024-01-04"): 1,
        pd.Timestamp("2024-01-05"): 0,
    }
    assert result.masked_alpha_009_signals.summary[
        "excluded_by_universe_count"
    ].to_dict() == {
        pd.Timestamp("2024-01-02"): 0,
        pd.Timestamp("2024-01-03"): 3,
        pd.Timestamp("2024-01-04"): 2,
        pd.Timestamp("2024-01-05"): 3,
    }
    assert result.masked_alpha_009_signals.low_coverage_dates == (
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-05"),
    )
    assert result.split_summary["date_count"].to_dict() == {
        "train": 1,
        "validation": 1,
        "test": 2,
    }
    assert result.split_summary.loc["train", "factor_valid_observations"] == 0
    assert result.split_summary.loc["validation", "factor_valid_observations"] == 3
    assert result.split_summary.loc["test", "forward_return_valid_observations"] == 3


def test_local_csv_fixture_workflow_is_deterministic() -> None:
    first = run_local_csv_fixture_workflow_demo(write_outputs=False)
    second = run_local_csv_fixture_workflow_demo(write_outputs=False)

    assert_frame_equal(first.prices, second.prices)
    assert_series_equal(first.benchmark_prices, second.benchmark_prices)
    assert_frame_equal(first.alpha_009_factor, second.alpha_009_factor)
    assert_frame_equal(first.alpha_012_factor, second.alpha_012_factor)
    assert_frame_equal(first.forward_returns, second.forward_returns)
    assert_frame_equal(first.liquidity_price_panel, second.liquidity_price_panel)
    assert_frame_equal(first.liquidity_volume_panel, second.liquidity_volume_panel)
    assert_frame_equal(
        first.average_daily_volume_eligibility,
        second.average_daily_volume_eligibility,
    )
    assert_frame_equal(
        first.average_dollar_volume_eligibility,
        second.average_dollar_volume_eligibility,
    )
    assert_frame_equal(first.liquidity_eligibility_summary, second.liquidity_eligibility_summary)
    assert_frame_equal(
        first.liquidity_universe_result.universe_mask,
        second.liquidity_universe_result.universe_mask,
    )
    assert_frame_equal(
        first.liquidity_universe_result.summary,
        second.liquidity_universe_result.summary,
    )
    assert_frame_equal(
        first.masked_alpha_009_signals.signals,
        second.masked_alpha_009_signals.signals,
    )
    assert_frame_equal(
        first.masked_alpha_009_signals.summary,
        second.masked_alpha_009_signals.summary,
    )
    assert_series_equal(first.information_coefficient, second.information_coefficient)
    assert_series_equal(first.rank_information_coefficient, second.rank_information_coefficient)
    assert_frame_equal(first.quantile_spread, second.quantile_spread)
    assert_series_equal(
        first.alpha_012_information_coefficient,
        second.alpha_012_information_coefficient,
    )
    assert_series_equal(
        first.alpha_012_rank_information_coefficient,
        second.alpha_012_rank_information_coefficient,
    )
    assert_frame_equal(first.alpha_012_quantile_spread, second.alpha_012_quantile_spread)
    assert_frame_equal(first.split_summary, second.split_summary)
    for split_name in ("train", "validation", "test"):
        assert_frame_equal(
            first.alpha_009_factor_by_split[split_name],
            second.alpha_009_factor_by_split[split_name],
        )
        assert_frame_equal(
            first.forward_returns_by_split[split_name],
            second.forward_returns_by_split[split_name],
        )
        assert_series_equal(
            first.information_coefficient_by_split[split_name],
            second.information_coefficient_by_split[split_name],
        )
        assert_frame_equal(
            first.alpha_012_factor_by_split[split_name],
            second.alpha_012_factor_by_split[split_name],
        )
        assert_series_equal(
            first.alpha_012_information_coefficient_by_split[split_name],
            second.alpha_012_information_coefficient_by_split[split_name],
        )


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
    assert "## Liquidity Eligibility Smoke Check" in report_text
    assert "## Liquidity Universe Mask Smoke Check" in report_text
    assert "## Universe-Masked Alpha#009 Signal Smoke Check" in report_text
    assert "signal-panel wiring check only" in report_text
    assert "not tradeability evidence or backtest universe integration" in report_text
    assert "| 2024-01-04 | 3 | 0 | 3 | 0 | 2 | 1 | 1 |" in report_text
    assert "| 2024-01-04 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | false |" in report_text
    assert "| 2024-01-04 | 3 | 1 | 1 | 2 | 0 | false |" in report_text
    assert "## Split Coverage" in report_text
    assert "## Alpha#012 Diagnostic Coverage" in report_text
    assert "## Alpha#012 Information Coefficient Diagnostics" in report_text
    assert "| 2024-01-03 | 1.0000 |" in report_text
    assert "| train | 1 | 3 | 0 | 3 | 0 | 0 | 0 | NaN | NaN |" in report_text
    assert "| Total return |" not in report_text
    assert "Sharpe" not in report_text

    assert payload["experiment_id"] == "local-csv-fixture-workflow-demo"
    assert payload["experiment_type"] == "synthetic_local_csv_workflow"
    assert payload["metrics"] == {}
    assert payload["assumptions"]["data_scope"] == "synthetic only"
    assert payload["assumptions"]["price_fixture"] == DEFAULT_PRICE_FIXTURE
    assert payload["assumptions"]["benchmark_fixture"] == DEFAULT_BENCHMARK_FIXTURE
    assert payload["assumptions"]["ohlcv_fixture"] == DEFAULT_OHLCV_FIXTURE
    assert payload["assumptions"]["liquidity_check"].startswith("synthetic")
    assert payload["assumptions"]["liquidity_universe_check"].startswith(
        "synthetic universe-mask",
    )
    assert payload["assumptions"]["liquidity_masked_signal_check"].startswith(
        "synthetic universe-masked alpha_009",
    )
    assert payload["assumptions"]["liquidity_eligibility_lag"] == 1
    assert payload["assumptions"]["liquidity_price_column"] == "adjusted_close"
    assert payload["assumptions"]["liquidity_universe_min_assets_per_date"] == 1
    assert payload["assumptions"]["masked_signal_min_valid_signals_per_date"] == 1
    assert payload["assumptions"]["alpha_012_feature"] == (
        "alpha_012 from adjusted_close and volume OHLCV panels"
    )
    assert payload["assumptions"]["portfolio_construction"] == "not included"
    assert payload["assumptions"]["backtest_integration"] == "not included"
    assert payload["assumptions"]["live_trading"] is False
    assert payload["assumptions"]["split_policy"].startswith("chronological")
    assert payload["assumptions"]["split_timing"].startswith("split labels")
    assert payload["assumptions"]["split_boundaries"] == {
        "train_end": "2024-01-02",
        "validation_end": "2024-01-03",
        "test_end": "2024-01-05",
    }
    assert payload["outputs"]["split_names"] == ["train", "validation", "test"]
    assert payload["outputs"]["ohlcv_rows"] == 4
    assert payload["diagnostics"]["adv_eligible_counts_by_date"] == {
        "2024-01-02": 0.0,
        "2024-01-03": 0.0,
        "2024-01-04": 2.0,
        "2024-01-05": 0.0,
    }
    assert payload["diagnostics"]["dollar_volume_eligible_counts_by_date"] == {
        "2024-01-02": 0.0,
        "2024-01-03": 0.0,
        "2024-01-04": 1.0,
        "2024-01-05": 0.0,
    }
    assert payload["diagnostics"]["liquidity_eligibility_summary"]["2024-01-04"] == {
        "adv_eligible_count": 2.0,
        "asset_count": 3.0,
        "both_eligible_count": 1.0,
        "dollar_volume_eligible_count": 1.0,
        "missing_volume_count": 3.0,
        "volume_observed_asset_count": 0.0,
        "zero_volume_count": 0.0,
    }
    assert payload["diagnostics"]["liquidity_universe_counts_by_date"] == {
        "2024-01-02": 0.0,
        "2024-01-03": 0.0,
        "2024-01-04": 1.0,
        "2024-01-05": 0.0,
    }
    assert payload["diagnostics"]["liquidity_universe_low_coverage_dates"] == [
        "2024-01-02",
        "2024-01-03",
        "2024-01-05",
    ]
    assert payload["diagnostics"]["liquidity_universe_summary"]["2024-01-04"] == {
        "added_count": 1.0,
        "capped_count": 0.0,
        "low_coverage": False,
        "missing_eligibility_count": 0.0,
        "missing_ranking_count": 0.0,
        "raw_eligible_count": 1.0,
        "removed_count": 0.0,
        "universe_count": 1.0,
    }
    assert payload["diagnostics"]["masked_alpha_009_signal_counts_by_date"] == {
        "2024-01-02": 0.0,
        "2024-01-03": 0.0,
        "2024-01-04": 1.0,
        "2024-01-05": 0.0,
    }
    assert payload["diagnostics"]["masked_alpha_009_signal_low_coverage_dates"] == [
        "2024-01-02",
        "2024-01-03",
        "2024-01-05",
    ]
    assert payload["diagnostics"]["masked_alpha_009_signal_summary"]["2024-01-04"] == {
        "excluded_by_universe_count": 2.0,
        "low_coverage": False,
        "missing_signal_count": 0.0,
        "raw_valid_signal_count": 3.0,
        "universe_eligible_count": 1.0,
        "valid_masked_signal_count": 1.0,
    }
    assert payload["diagnostics"]["factor_valid_observations"] == 9
    assert payload["diagnostics"]["alpha_009_factor_valid_observations"] == 9
    assert payload["diagnostics"]["masked_alpha_009_signal_valid_observations"] == 1
    assert payload["diagnostics"]["alpha_012_factor_valid_observations"] == 2
    alpha_012_ic_by_date = payload["diagnostics"][
        "alpha_012_information_coefficient_by_date"
    ]
    alpha_012_rank_ic_by_date = payload["diagnostics"][
        "alpha_012_rank_information_coefficient_by_date"
    ]
    assert alpha_012_ic_by_date == {
        "2024-01-02": None,
        "2024-01-03": 1.0,
        "2024-01-04": None,
        "2024-01-05": None,
    }
    assert alpha_012_rank_ic_by_date["2024-01-02"] is None
    assert alpha_012_rank_ic_by_date["2024-01-03"] == pytest.approx(1.0)
    assert alpha_012_rank_ic_by_date["2024-01-04"] is None
    assert alpha_012_rank_ic_by_date["2024-01-05"] is None
    assert payload["diagnostics"]["alpha_012_quantile_spread_valid_dates"] == 0
    assert payload["diagnostics"]["alpha_012_quantile_spread_valid_dates_by_split"] == {
        "train": 0,
        "validation": 0,
        "test": 0,
    }
    assert payload["diagnostics"]["split_summary"]["train"]["date_count"] == 1
    assert payload["diagnostics"]["split_summary"]["validation"]["ic_valid_dates"] == 1
    assert payload["diagnostics"]["quantile_spread_valid_dates_by_split"] == {
        "train": 0,
        "validation": 1,
        "test": 0,
    }
    assert "split-aware wiring check only" in payload["caveats"]
    assert "liquidity eligibility count smoke check only" in payload["caveats"]
    assert "liquidity universe mask count smoke check only" in payload["caveats"]
    assert "liquidity universe-masked signal smoke check only" in payload["caveats"]
    assert "not backtest universe integration" in payload["caveats"]
    assert "not tradeability evidence" in payload["caveats"]
    assert "not model selection" in payload["caveats"]
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
        "ohlcv_loader": 0,
        "adv_eligibility": 0,
        "dollar_volume_eligibility": 0,
        "liquidity_universe": 0,
        "mask_signals": 0,
        "alpha_009": 0,
        "alpha_012": 0,
        "make_split": 0,
        "split_panel": 0,
        "ic": 0,
        "rank_ic": 0,
        "quantile_spread": 0,
    }
    original_price_loader = demo.load_wide_price_csv
    original_benchmark_loader = demo.load_benchmark_price_csv
    original_ohlcv_loader = demo.load_ohlcv_csv
    original_adv_eligibility = demo.average_daily_volume_eligibility
    original_dollar_volume_eligibility = demo.average_dollar_volume_eligibility
    original_liquidity_universe = demo.construct_liquidity_universe
    original_mask_signals = demo.apply_universe_mask_to_signals
    original_alpha_009 = demo.alpha_009
    original_alpha_012 = demo.alpha_012
    original_make_split = demo.make_train_validation_test_split
    original_split_panel = demo.split_panel_by_train_validation_test
    original_ic = demo.factor_information_coefficient
    original_rank_ic = demo.factor_rank_information_coefficient
    original_quantile_spread = demo.factor_quantile_spread

    def count_price_loader(*args, **kwargs):
        calls["price_loader"] += 1
        return original_price_loader(*args, **kwargs)

    def count_benchmark_loader(*args, **kwargs):
        calls["benchmark_loader"] += 1
        return original_benchmark_loader(*args, **kwargs)

    def count_ohlcv_loader(*args, **kwargs):
        calls["ohlcv_loader"] += 1
        return original_ohlcv_loader(*args, **kwargs)

    def count_adv_eligibility(*args, **kwargs):
        calls["adv_eligibility"] += 1
        return original_adv_eligibility(*args, **kwargs)

    def count_dollar_volume_eligibility(*args, **kwargs):
        calls["dollar_volume_eligibility"] += 1
        return original_dollar_volume_eligibility(*args, **kwargs)

    def count_liquidity_universe(*args, **kwargs):
        calls["liquidity_universe"] += 1
        return original_liquidity_universe(*args, **kwargs)

    def count_mask_signals(*args, **kwargs):
        calls["mask_signals"] += 1
        return original_mask_signals(*args, **kwargs)

    def count_alpha_009(*args, **kwargs):
        calls["alpha_009"] += 1
        return original_alpha_009(*args, **kwargs)

    def count_alpha_012(*args, **kwargs):
        calls["alpha_012"] += 1
        return original_alpha_012(*args, **kwargs)

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

    def count_quantile_spread(*args, **kwargs):
        calls["quantile_spread"] += 1
        return original_quantile_spread(*args, **kwargs)

    monkeypatch.setattr(demo, "load_wide_price_csv", count_price_loader)
    monkeypatch.setattr(demo, "load_benchmark_price_csv", count_benchmark_loader)
    monkeypatch.setattr(demo, "load_ohlcv_csv", count_ohlcv_loader)
    monkeypatch.setattr(demo, "average_daily_volume_eligibility", count_adv_eligibility)
    monkeypatch.setattr(
        demo,
        "average_dollar_volume_eligibility",
        count_dollar_volume_eligibility,
    )
    monkeypatch.setattr(demo, "construct_liquidity_universe", count_liquidity_universe)
    monkeypatch.setattr(demo, "apply_universe_mask_to_signals", count_mask_signals)
    monkeypatch.setattr(demo, "alpha_009", count_alpha_009)
    monkeypatch.setattr(demo, "alpha_012", count_alpha_012)
    monkeypatch.setattr(demo, "make_train_validation_test_split", count_make_split)
    monkeypatch.setattr(demo, "split_panel_by_train_validation_test", count_split_panel)
    monkeypatch.setattr(demo, "factor_information_coefficient", count_ic)
    monkeypatch.setattr(demo, "factor_rank_information_coefficient", count_rank_ic)
    monkeypatch.setattr(demo, "factor_quantile_spread", count_quantile_spread)

    run_local_csv_fixture_workflow_demo(write_outputs=False)

    assert calls == {
        "price_loader": 1,
        "benchmark_loader": 1,
        "ohlcv_loader": 1,
        "adv_eligibility": 1,
        "dollar_volume_eligibility": 1,
        "liquidity_universe": 1,
        "mask_signals": 1,
        "alpha_009": 1,
        "alpha_012": 1,
        "make_split": 1,
        "split_panel": 3,
        "ic": 8,
        "rank_ic": 8,
        "quantile_spread": 8,
    }


def test_workflow_rejects_absolute_fixture_paths(tmp_path: Path) -> None:
    config = LocalCSVFixtureWorkflowConfig(price_fixture=str(tmp_path / "prices.csv"))

    with pytest.raises(ValueError, match="project-relative"):
        run_local_csv_fixture_workflow_demo(config=config, write_outputs=False)


def test_workflow_rejects_invalid_config_values() -> None:
    config = LocalCSVFixtureWorkflowConfig(forward_return_horizon_rows=0)

    with pytest.raises(ValueError, match="forward_return_horizon_rows"):
        run_local_csv_fixture_workflow_demo(config=config, write_outputs=False)


def test_workflow_rejects_invalid_liquidity_config_values() -> None:
    config = LocalCSVFixtureWorkflowConfig(min_average_dollar_volume=0.0)

    with pytest.raises(ValueError, match="min_average_dollar_volume"):
        run_local_csv_fixture_workflow_demo(config=config, write_outputs=False)

    bad_type_config = LocalCSVFixtureWorkflowConfig(
        liquidity_universe_min_assets_per_date=True,
    )
    with pytest.raises(TypeError, match="liquidity_universe_min_assets_per_date"):
        run_local_csv_fixture_workflow_demo(config=bad_type_config, write_outputs=False)

    bad_value_config = LocalCSVFixtureWorkflowConfig(
        liquidity_universe_min_assets_per_date=0,
    )
    with pytest.raises(ValueError, match="liquidity_universe_min_assets_per_date"):
        run_local_csv_fixture_workflow_demo(config=bad_value_config, write_outputs=False)

    bad_mask_type_config = LocalCSVFixtureWorkflowConfig(
        masked_signal_min_valid_signals_per_date=True,
    )
    with pytest.raises(TypeError, match="masked_signal_min_valid_signals_per_date"):
        run_local_csv_fixture_workflow_demo(
            config=bad_mask_type_config,
            write_outputs=False,
        )

    bad_mask_value_config = LocalCSVFixtureWorkflowConfig(
        masked_signal_min_valid_signals_per_date=0,
    )
    with pytest.raises(ValueError, match="masked_signal_min_valid_signals_per_date"):
        run_local_csv_fixture_workflow_demo(
            config=bad_mask_value_config,
            write_outputs=False,
        )


def test_workflow_rejects_invalid_split_boundaries() -> None:
    config = LocalCSVFixtureWorkflowConfig(
        train_end="2024-01-03",
        validation_end="2024-01-02",
    )

    with pytest.raises(ValueError, match="split boundaries"):
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
