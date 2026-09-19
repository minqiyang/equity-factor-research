import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from features.alphas import (
    alpha_005,
    alpha_008,
    alpha_010,
    alpha_013,
    alpha_014,
    alpha_018,
    alpha_020,
)
from features.combination import equal_weighted_composite, ic_weighted_composite
from research.multifactor_diagnostic_mvp import (
    ALPHA_005,
    ALPHA_008,
    ALPHA_010,
    ALPHA_013,
    ALPHA_014,
    ALPHA_018,
    ALPHA_020,
    ALPHA_IDS,
    ALPHA_WARMUP_PERIODS,
    EQUAL_WEIGHTED_COMPOSITE,
    FACTOR_IDS,
    IC_WEIGHTED_COMPOSITE,
    MultifactorDiagnosticConfig,
    _format_number,
    _format_percent,
    calculate_batch2_alpha,
    run_multifactor_diagnostic_mvp,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "walking_skeleton" / "diagnostic_cohort_v1.json"
)
PIPELINE_SOURCE = PROJECT_ROOT / "research" / "multifactor_diagnostic_mvp.py"
OFFICIAL_REPORT_PATH = PROJECT_ROOT / "reports" / "multifactor_diagnostic_mvp.md"
OFFICIAL_FOUR_DECIMAL_ROWS = {
    ALPHA_005: (
        "-0.0254",
        "-0.1645",
        "-0.8436",
        "0.2252",
        "15.55%",
        "0.4512",
        "-23.13%",
    ),
    ALPHA_008: (
        "-0.0291",
        "-0.2172",
        "-1.3083",
        "0.1527",
        "8.87%",
        "0.2920",
        "-23.31%",
    ),
    ALPHA_010: (
        "-0.0182",
        "-0.1064",
        "-0.7266",
        "0.2813",
        "19.43%",
        "0.5551",
        "-23.54%",
    ),
    ALPHA_013: (
        "0.0345",
        "0.2377",
        "1.6730",
        "0.1071",
        "3.69%",
        "0.1639",
        "-24.01%",
    ),
    ALPHA_014: (
        "-0.0063",
        "-0.0432",
        "-0.2736",
        "0.0667",
        "-2.02%",
        "0.0119",
        "-23.78%",
    ),
    ALPHA_018: (
        "-0.0324",
        "-0.2301",
        "-2.2995",
        "0.0648",
        "-2.16%",
        "0.0032",
        "-20.67%",
    ),
    ALPHA_020: (
        "-0.0315",
        "-0.2621",
        "-1.6914",
        "0.1781",
        "11.10%",
        "0.3520",
        "-20.93%",
    ),
    EQUAL_WEIGHTED_COMPOSITE: (
        "-0.0320",
        "-0.2186",
        "-1.5392",
        "0.0073",
        "-19.77%",
        "-0.5429",
        "-34.25%",
    ),
    IC_WEIGHTED_COMPOSITE: (
        "0.0420",
        "0.2742",
        "1.6372",
        "0.2277",
        "15.84%",
        "0.4563",
        "-21.13%",
    ),
}


def _short_manifest(tmp_path: Path, *, periods: int = 400) -> Path:
    payload = json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))
    payload["generation"]["periods"] = periods
    path = tmp_path / "diagnostic_cohort_short.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _approx_report_values(observed: tuple[str, ...], expected: tuple[str, ...]) -> None:
    for obs_val, exp_val in zip(observed, expected, strict=True):
        if obs_val.endswith("%"):
            assert float(obs_val.rstrip("%")) == pytest.approx(
                float(exp_val.rstrip("%")), abs=0.1
            )
        else:
            assert float(obs_val) == pytest.approx(float(exp_val), abs=0.02)


def test_batch2_alpha_helpers_match_feature_functions_without_wrappers() -> None:
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
        "high": close * 1.01,
        "low": close * 0.98,
        "vwap": close,
        "volume": close * 10.0,
    }

    pd.testing.assert_frame_equal(
        calculate_batch2_alpha(ALPHA_005, panels),
        alpha_005(panels["open"], panels["close"], panels["vwap"]),
    )
    pd.testing.assert_frame_equal(
        calculate_batch2_alpha(ALPHA_008, panels),
        alpha_008(panels["open"], panels["returns"]),
    )
    pd.testing.assert_frame_equal(
        calculate_batch2_alpha(ALPHA_010, panels),
        alpha_010(panels["close"]),
    )
    pd.testing.assert_frame_equal(
        calculate_batch2_alpha(ALPHA_013, panels),
        alpha_013(panels["close"], panels["volume"]),
    )
    pd.testing.assert_frame_equal(
        calculate_batch2_alpha(ALPHA_014, panels),
        alpha_014(panels["open"], panels["volume"], panels["returns"]),
    )
    pd.testing.assert_frame_equal(
        calculate_batch2_alpha(ALPHA_018, panels),
        alpha_018(panels["open"], panels["close"]),
    )
    pd.testing.assert_frame_equal(
        calculate_batch2_alpha(ALPHA_020, panels),
        alpha_020(panels["open"], panels["high"], panels["low"], panels["close"]),
    )


def test_multifactor_pipeline_has_no_abstract_class_hierarchy() -> None:
    tree = ast.parse(PIPELINE_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            assert node.name == "MultifactorDiagnosticConfig"
            assert node.keywords == []
            assert all(
                not (isinstance(base, ast.Name) and base.id in {"ABC", "ABCMeta"})
                for base in node.bases
            )


def test_multifactor_diagnostic_mvp_runs_fifty_stock_equal_weight_monthly_backtest(
    tmp_path: Path,
) -> None:
    manifest_path = _short_manifest(tmp_path)
    report_path = tmp_path / "multifactor_diagnostic_mvp.md"
    config = MultifactorDiagnosticConfig(manifest_path=manifest_path, slippage_bps=5.0, top_n=5)

    result = run_multifactor_diagnostic_mvp(
        config=config,
        report_path=report_path,
        write_outputs=True,
    )

    assert result["evidence_ceiling"] == "DIAGNOSTIC_ONLY"
    assert result["prices"].shape[1] == 50
    assert result["evaluation_start"] == result["prices"].index[ALPHA_WARMUP_PERIODS]
    assert list(result["factors"]) == list(FACTOR_IDS)
    assert result["config"].n_trials == 9
    assert list(result["ic_weights"]) == list(ALPHA_IDS)
    alpha_panels = [result["factors"][factor_id]["factor"] for factor_id in ALPHA_IDS]
    pd.testing.assert_frame_equal(
        result["factors"][EQUAL_WEIGHTED_COMPOSITE]["factor"],
        equal_weighted_composite(alpha_panels),
    )
    pd.testing.assert_frame_equal(
        result["factors"][IC_WEIGHTED_COMPOSITE]["factor"],
        ic_weighted_composite(alpha_panels, list(result["ic_weights"].values())),
    )

    report_text = report_path.read_text(encoding="utf-8")
    assert "DIAGNOSTIC_ONLY" in report_text
    assert "not point-in-time universe evidence" in report_text
    assert "Euler-Mascheroni" in report_text
    assert "in-sample mean monthly Rank IC" in report_text
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


def test_multifactor_diagnostic_official_report_table_matches_default_fixture() -> None:
    result = run_multifactor_diagnostic_mvp(write_outputs=False)

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
        _approx_report_values(observed, expected)
        row = "| " + " | ".join((factor_id, *expected)) + " |"
        assert row in report_text
