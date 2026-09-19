import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from features.momentum import calculate_12_1_momentum
from features.operators import decay_linear
from features.reversal import calculate_short_term_reversal
from features.volatility import calculate_realized_volatility
from research.walking_skeleton_mvp import (
    FACTOR_IDS,
    LOW_VOL_3M,
    MOM_12_1,
    MOMENTUM_LOOKBACK_PERIODS,
    REV_1M,
    WalkingSkeletonConfig,
    _format_number,
    _format_percent,
    calculate_diagnostic_factor,
    run_walking_skeleton_mvp,
)

OFFICIAL_FOUR_DECIMAL_ROWS = {
    MOM_12_1: (
        "-0.0145",
        "-0.0919",
        "-0.5047",
        "0.1532",
        "-4.61%",
        "-0.1206",
        "-18.66%",
    ),
    REV_1M: (
        "-0.0202",
        "-0.1678",
        "-0.7473",
        "0.1644",
        "-3.66%",
        "-0.0878",
        "-18.16%",
    ),
    LOW_VOL_3M: (
        "-0.0138",
        "-0.0984",
        "-0.5056",
        "0.1394",
        "-5.91%",
        "-0.1632",
        "-18.18%",
    ),
}


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "walking_skeleton" / "diagnostic_cohort_v1.json"
)
PIPELINE_SOURCE = PROJECT_ROOT / "research" / "walking_skeleton_mvp.py"


def _short_manifest(tmp_path: Path, *, periods: int = 400) -> Path:
    payload = json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))
    payload["generation"]["periods"] = periods
    path = tmp_path / "diagnostic_cohort_short.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_diagnostic_factors_match_existing_feature_functions_without_wrappers() -> None:
    dates = pd.bdate_range("2021-01-04", periods=300)
    prices = pd.DataFrame(
        100.0 + np.linspace(0.0, 1.0, 300).reshape(-1, 1) + np.arange(3),
        index=dates,
        columns=["D50_01", "D50_02", "D50_03"],
    )

    pd.testing.assert_frame_equal(
        calculate_diagnostic_factor(MOM_12_1, prices),
        calculate_12_1_momentum(prices, lookback_periods=252, skip_periods=21),
    )
    pd.testing.assert_frame_equal(
        calculate_diagnostic_factor(REV_1M, prices),
        calculate_short_term_reversal(prices, lookback_periods=21),
    )
    pd.testing.assert_frame_equal(
        calculate_diagnostic_factor(LOW_VOL_3M, prices),
        -calculate_realized_volatility(prices, window_periods=63, ddof=1),
    )


def test_decay_linear_ablation_matches_explicit_numpy_weights() -> None:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    data = pd.DataFrame({"AAA": [1.0, 2.0, 3.0, 6.0]}, index=dates)
    weights = np.array([1.0, 2.0, 3.0])

    observed = decay_linear(data, 3)
    expected_last = float(np.dot(np.array([2.0, 3.0, 6.0]), weights) / weights.sum())

    assert observed.iloc[3, 0] == pytest.approx(expected_last)


def test_walking_skeleton_pipeline_has_no_abstract_class_hierarchy() -> None:
    tree = ast.parse(PIPELINE_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            assert node.name == "WalkingSkeletonConfig"
            assert node.keywords == []
            assert all(
                not (isinstance(base, ast.Name) and base.id in {"ABC", "ABCMeta"})
                for base in node.bases
            )
        if isinstance(node, ast.ClassDef) and node.name != "WalkingSkeletonConfig":
            raise AssertionError(f"unexpected class {node.name}")


def test_walking_skeleton_mvp_runs_fifty_stock_equal_weight_monthly_backtest(
    tmp_path: Path,
) -> None:
    manifest_path = _short_manifest(tmp_path)
    report_path = tmp_path / "walking_skeleton_mvp.md"
    config = WalkingSkeletonConfig(manifest_path=manifest_path, slippage_bps=5.0, top_n=5)

    result = run_walking_skeleton_mvp(
        config=config,
        report_path=report_path,
        write_outputs=True,
    )

    assert result["evidence_ceiling"] == "DIAGNOSTIC_ONLY"
    assert result["prices"].shape[1] == 50
    assert result["evaluation_start"] == result["prices"].index[MOMENTUM_LOOKBACK_PERIODS]
    assert list(result["factors"]) == list(FACTOR_IDS)

    report_text = report_path.read_text(encoding="utf-8")
    assert "DIAGNOSTIC_ONLY" in report_text
    assert "not point-in-time universe evidence" in report_text
    assert "5.00" in report_text
    for factor_id in FACTOR_IDS:
        assert factor_id in report_text
        payload = result["factors"][factor_id]
        backtest = payload["backtest"]
        assert payload["ic_summary"]["count"] >= 1.0
        assert set(payload["ic_summary"]) == {
            "count",
            "mean_ic",
            "ic_std",
            "icir",
            "newey_west_tstat",
        }
        np.testing.assert_allclose(
            backtest.trade_weights.sum(axis=1).to_numpy(),
            backtest.turnover.to_numpy(),
            atol=1e-12,
            rtol=0.0,
        )
        assert backtest.assumptions["slippage_bps"] == pytest.approx(5.0)
        measured = backtest.returns.iloc[1:]
        assert len(measured) >= 2
        assert (backtest.holdings.sum(axis=1) <= 1.0 + 1e-12).all()


def test_walking_skeleton_official_report_table_matches_default_fixture() -> None:
    result = run_walking_skeleton_mvp(write_outputs=False)

    assert result["prices"].shape == (756, 50)
    report_text = (PROJECT_ROOT / "reports" / "walking_skeleton_mvp.md").read_text(
        encoding="utf-8"
    )
    for factor_id, expected in OFFICIAL_FOUR_DECIMAL_ROWS.items():
        payload = result["factors"][factor_id]
        ic_summary = payload["ic_summary"]
        metrics = payload["backtest"].metrics
        observed = (
            _format_number(ic_summary["mean_ic"]),
            _format_number(ic_summary["icir"]),
            _format_number(ic_summary["newey_west_tstat"]),
            _format_number(payload["dsr"]),
            _format_percent(metrics["total_return"]),
            _format_number(metrics["sharpe_ratio"]),
            _format_percent(metrics["max_drawdown"]),
        )
        assert observed == expected
        row = "| " + " | ".join((factor_id, *expected)) + " |"
        assert row in report_text
