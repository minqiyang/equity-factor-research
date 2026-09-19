import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from features.alphas import (
    alpha_001,
    alpha_002,
    alpha_003,
    alpha_004,
    alpha_006,
    alpha_012,
)
from research.alphas_diagnostic_mvp import (
    ALPHA_001,
    ALPHA_002,
    ALPHA_003,
    ALPHA_004,
    ALPHA_006,
    ALPHA_012,
    ALPHA_WARMUP_PERIODS,
    FACTOR_IDS,
    AlphasDiagnosticConfig,
    _format_number,
    _format_percent,
    calculate_alpha_factor,
    run_alphas_diagnostic_mvp,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "walking_skeleton" / "diagnostic_cohort_v1.json"
)
PIPELINE_SOURCE = PROJECT_ROOT / "research" / "alphas_diagnostic_mvp.py"
OFFICIAL_REPORT_PATH = PROJECT_ROOT / "reports" / "alphas_diagnostic_mvp.md"
OFFICIAL_FOUR_DECIMAL_ROWS = {
    ALPHA_001: (
        "-0.0083",
        "-0.0541",
        "-0.3019",
        "0.1123",
        "-0.40%",
        "0.0505",
        "-23.34%",
    ),
    ALPHA_002: (
        "-0.0028",
        "-0.0189",
        "-0.1163",
        "0.0235",
        "-15.29%",
        "-0.4035",
        "-27.88%",
    ),
    ALPHA_003: (
        "-0.0383",
        "-0.2358",
        "-1.1060",
        "0.5251",
        "31.28%",
        "0.8040",
        "-16.56%",
    ),
    ALPHA_004: (
        "-0.0181",
        "-0.1301",
        "-1.0225",
        "0.2068",
        "8.41%",
        "0.2839",
        "-23.66%",
    ),
    ALPHA_006: (
        "-0.0036",
        "-0.0292",
        "-0.1833",
        "0.1514",
        "3.59%",
        "0.1589",
        "-14.41%",
    ),
    ALPHA_012: (
        "-0.0069",
        "-0.0548",
        "-0.3888",
        "0.3865",
        "21.76%",
        "0.5961",
        "-18.88%",
    ),
}


def _short_manifest(tmp_path: Path, *, periods: int = 400) -> Path:
    payload = json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))
    payload["generation"]["periods"] = periods
    path = tmp_path / "diagnostic_cohort_short.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_alpha_factor_helpers_match_feature_functions_without_wrappers() -> None:
    dates = pd.bdate_range("2021-01-04", periods=80)
    close = pd.DataFrame(
        100.0 + np.linspace(0.0, 1.0, 80).reshape(-1, 1) + np.arange(3),
        index=dates,
        columns=["D50_01", "D50_02", "D50_03"],
    )
    panels = {
        "close": close,
        "returns": close.pct_change(fill_method=None),
        "open": close * 0.99,
        "low": close * 0.98,
        "volume": close * 10.0,
    }

    pd.testing.assert_frame_equal(
        calculate_alpha_factor(ALPHA_001, panels),
        alpha_001(panels["close"], panels["returns"]),
    )
    pd.testing.assert_frame_equal(
        calculate_alpha_factor(ALPHA_002, panels),
        alpha_002(panels["open"], panels["close"], panels["volume"]),
    )
    pd.testing.assert_frame_equal(
        calculate_alpha_factor(ALPHA_003, panels),
        alpha_003(panels["open"], panels["volume"]),
    )
    pd.testing.assert_frame_equal(
        calculate_alpha_factor(ALPHA_004, panels),
        alpha_004(panels["low"]),
    )
    pd.testing.assert_frame_equal(
        calculate_alpha_factor(ALPHA_006, panels),
        alpha_006(panels["open"], panels["volume"]),
    )
    pd.testing.assert_frame_equal(
        calculate_alpha_factor(ALPHA_012, panels),
        alpha_012(panels["close"], panels["volume"]),
    )


def test_alphas_pipeline_has_no_abstract_class_hierarchy() -> None:
    tree = ast.parse(PIPELINE_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            assert node.name == "AlphasDiagnosticConfig"
            assert node.keywords == []
            assert all(
                not (isinstance(base, ast.Name) and base.id in {"ABC", "ABCMeta"})
                for base in node.bases
            )


def test_alphas_diagnostic_mvp_runs_fifty_stock_equal_weight_monthly_backtest(
    tmp_path: Path,
) -> None:
    manifest_path = _short_manifest(tmp_path)
    report_path = tmp_path / "alphas_diagnostic_mvp.md"
    config = AlphasDiagnosticConfig(manifest_path=manifest_path, slippage_bps=5.0, top_n=5)

    result = run_alphas_diagnostic_mvp(
        config=config,
        report_path=report_path,
        write_outputs=True,
    )

    assert result["evidence_ceiling"] == "DIAGNOSTIC_ONLY"
    assert result["prices"].shape[1] == 50
    assert result["evaluation_start"] == result["prices"].index[ALPHA_WARMUP_PERIODS]
    assert list(result["factors"]) == list(FACTOR_IDS)
    assert result["config"].n_trials == 6

    report_text = report_path.read_text(encoding="utf-8")
    assert "DIAGNOSTIC_ONLY" in report_text
    assert "not point-in-time universe evidence" in report_text
    assert "Euler-Mascheroni" in report_text
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


def test_alphas_diagnostic_official_report_table_matches_default_fixture() -> None:
    result = run_alphas_diagnostic_mvp(write_outputs=False)

    assert result["prices"].shape == (756, 50)
    report_text = OFFICIAL_REPORT_PATH.read_text(encoding="utf-8")
    assert "DIAGNOSTIC_ONLY" in report_text
    assert "Euler-Mascheroni" in report_text
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
