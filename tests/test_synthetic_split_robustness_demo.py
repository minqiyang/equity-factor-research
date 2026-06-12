import ast
import inspect
import json
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import research.synthetic_split_robustness_demo as demo
from research.synthetic_split_robustness_demo import (
    SyntheticRobustnessCase,
    SyntheticSplitRobustnessConfig,
    build_synthetic_robustness_cases,
    main,
    run_synthetic_split_robustness_demo,
)


def test_synthetic_split_robustness_reports_all_cases_and_splits() -> None:
    result = run_synthetic_split_robustness_demo()

    assert result.reported_case_count == 3
    assert list(result.summary.index) == [
        ("base_signal", "train"),
        ("base_signal", "validation"),
        ("base_signal", "test"),
        ("inverse_signal", "train"),
        ("inverse_signal", "validation"),
        ("inverse_signal", "test"),
        ("constant_signal", "train"),
        ("constant_signal", "validation"),
        ("constant_signal", "test"),
    ]
    assert result.summary["date_count"].to_dict() == {
        ("base_signal", "train"): 4,
        ("base_signal", "validation"): 4,
        ("base_signal", "test"): 4,
        ("inverse_signal", "train"): 4,
        ("inverse_signal", "validation"): 4,
        ("inverse_signal", "test"): 4,
        ("constant_signal", "train"): 4,
        ("constant_signal", "validation"): 4,
        ("constant_signal", "test"): 4,
    }


def test_synthetic_split_robustness_metrics_are_hand_checked() -> None:
    result = run_synthetic_split_robustness_demo()

    assert result.summary.loc[("base_signal", "train"), "mean_ic"] == pytest.approx(
        1.0,
    )
    assert result.summary.loc[
        ("base_signal", "validation"),
        "mean_ic",
    ] == pytest.approx(-1.0)
    assert result.summary.loc[("base_signal", "test"), "mean_ic"] == pytest.approx(
        1.0,
    )
    assert result.summary.loc[
        ("inverse_signal", "train"),
        "mean_ic",
    ] == pytest.approx(-1.0)
    assert result.summary.loc[
        ("inverse_signal", "validation"),
        "mean_ic",
    ] == pytest.approx(1.0)
    assert result.summary.loc[
        ("inverse_signal", "test"),
        "mean_ic",
    ] == pytest.approx(-1.0)
    assert result.summary.loc[
        ("constant_signal", "train"),
        "invalid_reason",
    ] == "no_valid_ic_or_rank_ic_dates"
    assert pd.isna(result.summary.loc[("constant_signal", "train"), "mean_ic"])


def test_synthetic_split_robustness_preserves_missing_values() -> None:
    result = run_synthetic_split_robustness_demo()

    assert pd.isna(result.base_factor.loc[pd.Timestamp("2024-01-09"), "ASSET_02"])
    assert pd.isna(
        result.forward_returns.loc[pd.Timestamp("2024-01-16"), "ASSET_04"],
    )
    assert result.summary.loc[
        ("base_signal", "validation"),
        "factor_valid_observations",
    ] == 23
    assert result.summary.loc[
        ("base_signal", "test"),
        "forward_return_valid_observations",
    ] == 23
    assert result.summary.loc[
        ("constant_signal", "validation"),
        "factor_valid_observations",
    ] == 23


def test_synthetic_split_robustness_is_deterministic() -> None:
    first = run_synthetic_split_robustness_demo()
    second = run_synthetic_split_robustness_demo()

    assert_frame_equal(first.base_factor, second.base_factor)
    assert_frame_equal(first.forward_returns, second.forward_returns)
    assert_frame_equal(first.summary, second.summary)
    for case_id in first.factor_cases:
        assert_frame_equal(first.factor_cases[case_id], second.factor_cases[case_id])


def test_synthetic_split_robustness_assumptions_keep_costs_separate() -> None:
    result = run_synthetic_split_robustness_demo()

    assert result.assumptions["data_scope"] == "synthetic only"
    assert result.assumptions["benchmark_assumption"] == "not included"
    assert result.assumptions["transaction_cost_bps"] == 0.0
    assert result.assumptions["slippage_bps"] == 0.0
    assert result.assumptions["volume_aware_slippage_mode"] == "absent"
    assert result.assumptions["backtest_integration"] == "not included"
    assert result.assumptions["live_trading"] is False
    assert result.assumptions["paper_trading"] is False
    assert result.assumptions["brokerage_integration"] is False
    assert result.assumptions["order_execution"] is False
    assert result.assumptions["profitability_claim"] is False


def test_synthetic_split_robustness_can_skip_outputs(tmp_path: Path) -> None:
    report_path = tmp_path / "skipped.md"
    log_path = tmp_path / "skipped.json"

    result = run_synthetic_split_robustness_demo(
        report_path=report_path,
        experiment_log_path=log_path,
    )

    assert result.report_path == report_path
    assert result.experiment_log_path == log_path
    assert not report_path.exists()
    assert not log_path.exists()


def test_synthetic_split_robustness_writes_caveated_report_and_log(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "synthetic_split_robustness_demo.md"
    log_path = tmp_path / "synthetic_split_robustness_demo.json"

    result = run_synthetic_split_robustness_demo(
        report_path=report_path,
        experiment_log_path=log_path,
        write_outputs=True,
    )

    report_text = report_path.read_text(encoding="utf-8")
    payload = json.loads(log_path.read_text(encoding="utf-8"))

    assert result.report_path == report_path
    assert result.experiment_log_path == log_path
    assert "# Synthetic Split-Aware Robustness Demo" in report_text
    assert "deterministic synthetic panels only" in report_text
    assert "not real-market evidence" in report_text
    assert "not a profitability claim" in report_text
    assert "No real data fetching" in report_text
    assert "Every configured case is reported" in report_text
    assert "All-Case Split Summary" in report_text
    assert "Invalid Or Insufficient Cases" in report_text

    assert payload["experiment_id"] == "synthetic-split-robustness-demo"
    assert payload["experiment_type"] == "synthetic_split_robustness_diagnostic_demo"
    assert payload["metrics"] == {}
    assert payload["outputs"]["reported_case_count"] == 3
    assert payload["outputs"]["invalid_case_count"] == 3
    assert len(payload["diagnostics"]["all_case_summary"]) == 9
    assert len(payload["diagnostics"]["invalid_case_summary"]) == 3
    assert "all configured cases reported" in payload["caveats"]
    assert "not parameter selection" in payload["caveats"]
    assert payload["assumptions"]["volume_aware_slippage_mode"] == "absent"


def test_synthetic_split_robustness_main_writes_requested_report(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "module_report.md"
    log_path = tmp_path / "module_log.json"

    main(report_path=report_path, experiment_log_path=log_path, write_outputs=True)

    assert report_path.is_file()
    assert log_path.is_file()
    assert "# Synthetic Split-Aware Robustness Demo" in report_path.read_text(
        encoding="utf-8",
    )


def test_build_synthetic_robustness_cases_rejects_duplicate_case_ids() -> None:
    base_factor = run_synthetic_split_robustness_demo().base_factor

    with pytest.raises(ValueError, match="duplicate case_id"):
        build_synthetic_robustness_cases(
            base_factor=base_factor,
            cases=(
                SyntheticRobustnessCase("duplicate", "identity"),
                SyntheticRobustnessCase("duplicate", "inverse"),
            ),
        )


def test_synthetic_split_robustness_rejects_unsupported_transform() -> None:
    config = SyntheticSplitRobustnessConfig(
        cases=(
            SyntheticRobustnessCase(
                "bad_transform",
                "unsupported",  # type: ignore[arg-type]
            ),
        ),
    )

    with pytest.raises(ValueError, match="unsupported transform"):
        run_synthetic_split_robustness_demo(config)


def test_synthetic_split_robustness_rejects_empty_cases() -> None:
    config = SyntheticSplitRobustnessConfig(cases=())

    with pytest.raises(ValueError, match="cases must not be empty"):
        run_synthetic_split_robustness_demo(config)


def test_synthetic_split_robustness_module_has_no_forbidden_imports() -> None:
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
    ]

    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    for module_name in imported_modules:
        assert not any(term in module_name for term in forbidden_terms)


def test_synthetic_split_robustness_text_contains_only_caveated_claim_language() -> None:
    source_text = inspect.getsource(demo).lower()

    assert "profitability claims" in source_text
    assert "is profitable" not in source_text
    assert "profitable strategy" not in source_text
    assert "write generated reports\nunless explicitly requested" in source_text
