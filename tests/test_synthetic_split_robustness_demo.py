import ast
import inspect

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import research.synthetic_split_robustness_demo as demo
from research.synthetic_split_robustness_demo import (
    SyntheticRobustnessCase,
    SyntheticSplitRobustnessConfig,
    build_synthetic_robustness_cases,
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

    assert "make profitability claims" in source_text
    assert "is profitable" not in source_text
    assert "profitable strategy" not in source_text
    assert "write generated reports" in source_text
