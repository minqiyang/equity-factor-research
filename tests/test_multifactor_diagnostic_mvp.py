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
    alpha_005,
    alpha_006,
    alpha_007,
    alpha_008,
    alpha_009,
    alpha_010,
    alpha_012,
    alpha_013,
    alpha_014,
    alpha_017,
    alpha_018,
    alpha_019,
    alpha_020,
    alpha_023,
    alpha_028,
    alpha_033,
    alpha_038,
    alpha_054,
    alpha_101,
)
from features.combination import equal_weighted_composite, ic_weighted_composite
from research.multifactor_diagnostic_mvp import (
    ALPHA_001,
    ALPHA_002,
    ALPHA_003,
    ALPHA_004,
    ALPHA_005,
    ALPHA_006,
    ALPHA_007,
    ALPHA_008,
    ALPHA_009,
    ALPHA_010,
    ALPHA_012,
    ALPHA_013,
    ALPHA_014,
    ALPHA_017,
    ALPHA_018,
    ALPHA_019,
    ALPHA_020,
    ALPHA_023,
    ALPHA_028,
    ALPHA_033,
    ALPHA_038,
    ALPHA_054,
    ALPHA_101,
    ALPHA_IDS,
    ALPHA_WARMUP_PERIODS,
    EQUAL_WEIGHTED_COMPOSITE,
    FACTOR_IDS,
    IC_WEIGHTED_COMPOSITE,
    IMPLEMENTED_ALPHA_COUNT,
    MultifactorDiagnosticConfig,
    _format_number,
    _format_percent,
    calculate_diagnostic_alpha,
    run_multifactor_diagnostic_mvp,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "walking_skeleton" / "diagnostic_cohort_v1.json"
)
PIPELINE_SOURCE = PROJECT_ROOT / "research" / "multifactor_diagnostic_mvp.py"
OFFICIAL_REPORT_PATH = PROJECT_ROOT / "reports" / "multifactor_diagnostic_mvp.md"
OFFICIAL_FOUR_DECIMAL_ROWS = {
    ALPHA_001: ("-0.0083", "-0.0541", "-0.3019", "0.0280", "-0.40%", "0.0505", "-23.34%"),
    ALPHA_002: ("-0.0028", "-0.0189", "-0.1163", "0.0036", "-15.29%", "-0.4035", "-27.88%"),
    ALPHA_003: ("-0.0383", "-0.2358", "-1.1060", "0.2630", "31.28%", "0.8040", "-16.56%"),
    ALPHA_004: ("-0.0181", "-0.1301", "-1.0225", "0.0650", "8.41%", "0.2839", "-23.66%"),
    ALPHA_005: ("-0.0254", "-0.1645", "-0.8436", "0.1092", "15.55%", "0.4512", "-23.13%"),
    ALPHA_006: ("-0.0036", "-0.0292", "-0.1833", "0.0420", "3.59%", "0.1589", "-14.41%"),
    ALPHA_007: ("0.0106", "0.0984", "0.5324", "0.0028", "-17.35%", "-0.4558", "-25.97%"),
    ALPHA_008: ("-0.0291", "-0.2172", "-1.3083", "0.0666", "8.87%", "0.2920", "-23.31%"),
    ALPHA_009: ("-0.0194", "-0.1182", "-0.7920", "0.0998", "13.74%", "0.4208", "-24.30%"),
    ALPHA_010: ("-0.0182", "-0.1064", "-0.7266", "0.1457", "19.43%", "0.5551", "-23.54%"),
    ALPHA_012: ("-0.0069", "-0.0548", "-0.3888", "0.1622", "21.76%", "0.5961", "-18.88%"),
    ALPHA_013: ("0.0345", "0.2377", "1.6730", "0.0428", "3.69%", "0.1639", "-24.01%"),
    ALPHA_014: ("-0.0063", "-0.0432", "-0.2736", "0.0240", "-2.02%", "0.0119", "-23.78%"),
    ALPHA_017: ("-0.0478", "-0.4175", "-2.9894", "0.3084", "34.36%", "0.8826", "-14.41%"),
    ALPHA_018: ("-0.0324", "-0.2301", "-2.2995", "0.0232", "-2.16%", "0.0032", "-20.67%"),
    ALPHA_019: ("-0.0974", "-0.6117", "-2.9056", "0.0105", "-6.88%", "-0.1828", "-14.82%"),
    ALPHA_020: ("-0.0315", "-0.2621", "-1.6914", "0.0809", "11.10%", "0.3520", "-20.93%"),
    ALPHA_023: ("-0.0152", "-0.0973", "-0.6273", "0.2295", "28.34%", "0.7390", "-17.50%"),
    ALPHA_028: ("0.0097", "0.0693", "0.3415", "0.0597", "7.55%", "0.2593", "-30.66%"),
    ALPHA_033: ("-0.0308", "-0.2051", "-2.0262", "0.1666", "22.10%", "0.6057", "-17.06%"),
    ALPHA_038: ("-0.0174", "-0.1119", "-0.7676", "0.0429", "3.77%", "0.1647", "-20.58%"),
    ALPHA_054: ("0.0048", "0.0346", "0.3353", "0.0359", "1.93%", "0.1156", "-25.60%"),
    ALPHA_101: ("0.0181", "0.1150", "1.0473", "0.0303", "0.28%", "0.0709", "-29.74%"),
    EQUAL_WEIGHTED_COMPOSITE: (
        "-0.0456",
        "-0.3165",
        "-2.4460",
        "0.0059",
        "-12.20%",
        "-0.3078",
        "-29.44%",
    ),
    IC_WEIGHTED_COMPOSITE: (
        "0.0670",
        "0.4900",
        "2.8880",
        "0.0387",
        "2.70%",
        "0.1364",
        "-26.49%",
    ),
}
ALPHA_FEATURE_HELPERS = {
    ALPHA_001: lambda panels: alpha_001(panels["close"], panels["returns"]),
    ALPHA_002: lambda panels: alpha_002(panels["open"], panels["close"], panels["volume"]),
    ALPHA_003: lambda panels: alpha_003(panels["open"], panels["volume"]),
    ALPHA_004: lambda panels: alpha_004(panels["low"]),
    ALPHA_005: lambda panels: alpha_005(panels["open"], panels["close"], panels["vwap"]),
    ALPHA_006: lambda panels: alpha_006(panels["open"], panels["volume"]),
    ALPHA_007: lambda panels: alpha_007(panels["close"], panels["volume"]),
    ALPHA_008: lambda panels: alpha_008(panels["open"], panels["returns"]),
    ALPHA_009: lambda panels: alpha_009(panels["close"]),
    ALPHA_010: lambda panels: alpha_010(panels["close"]),
    ALPHA_012: lambda panels: alpha_012(panels["close"], panels["volume"]),
    ALPHA_013: lambda panels: alpha_013(panels["close"], panels["volume"]),
    ALPHA_014: lambda panels: alpha_014(panels["open"], panels["volume"], panels["returns"]),
    ALPHA_017: lambda panels: alpha_017(panels["close"], panels["volume"]),
    ALPHA_018: lambda panels: alpha_018(panels["open"], panels["close"]),
    ALPHA_019: lambda panels: alpha_019(panels["close"], panels["returns"]),
    ALPHA_020: lambda panels: alpha_020(
        panels["open"],
        panels["high"],
        panels["low"],
        panels["close"],
    ),
    ALPHA_023: lambda panels: alpha_023(panels["high"]),
    ALPHA_028: lambda panels: alpha_028(
        panels["close"],
        panels["high"],
        panels["low"],
        panels["volume"],
    ),
    ALPHA_033: lambda panels: alpha_033(panels["open"], panels["close"]),
    ALPHA_038: lambda panels: alpha_038(panels["open"], panels["close"]),
    ALPHA_054: lambda panels: alpha_054(
        panels["open"],
        panels["high"],
        panels["low"],
        panels["close"],
    ),
    ALPHA_101: lambda panels: alpha_101(
        panels["open"],
        panels["high"],
        panels["low"],
        panels["close"],
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
            assert float(obs_val) == pytest.approx(float(exp_val), abs=0.05)


def test_diagnostic_alpha_helpers_match_feature_functions_without_wrappers() -> None:
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

    assert IMPLEMENTED_ALPHA_COUNT == 23
    assert len(ALPHA_IDS) == 23
    assert len(FACTOR_IDS) == 25
    assert set(ALPHA_FEATURE_HELPERS) == set(ALPHA_IDS)
    for factor_id, helper in ALPHA_FEATURE_HELPERS.items():
        pd.testing.assert_frame_equal(
            calculate_diagnostic_alpha(factor_id, panels),
            helper(panels),
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
    assert result["config"].n_trials == 25
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
