import ast
import inspect
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data.bluechip_cohort import BENCHMARK_SYMBOL, BLUECHIP_50_COHORT
from reporting.experiment_log import (
    DIAGNOSTIC_REAL_DATA_CAVEATS,
    REAL_DATA_MULTIFACTOR_EXPERIMENT_TYPE,
)
from reporting.experiment_registry import build_experiment_registry
from research.multifactor_diagnostic_mvp import (
    ALPHA_001,
    ALPHA_101,
    ALPHA_IDS,
    ALPHA_PRODUCT_INTERACTION,
    EQUAL_WEIGHTED_COMPOSITE,
    FACTOR_IDS,
)
from research.real_data_multifactor_diagnostic import (
    COMPOSITE_IDS,
    DEFAULT_END_DATE,
    DEFAULT_INVENTORY_FILE_NAME,
    DEFAULT_SNAPSHOT_DIR_NAME,
    DEFAULT_START_DATE,
    REDACTED_DATA_DIR,
    REDACTED_INVENTORY_PATH,
    REDACTED_LOCAL_PATH,
    RealDataMultifactorDiagnosticConfig,
    build_adjusted_research_panels,
    default_data_dir,
    default_inventory_path,
    evaluate_diagnostic_readiness,
    redact_local_path,
    run_real_data_multifactor_diagnostic,
    to_mvp_config,
)
import research.real_data_multifactor_diagnostic as real_data_module


def _write_symbol_parquet(
    path: Path,
    dates: pd.DatetimeIndex,
    *,
    seed: int,
    start_price: float = 100.0,
    close_scale: float = 1.0,
    adjusted_scale: float = 1.0,
) -> Path:
    rng = np.random.default_rng(seed)
    returns = rng.normal(loc=0.0004, scale=0.012, size=len(dates))
    close = start_price * np.exp(np.cumsum(returns))
    open_ = np.maximum(close * (1.0 + rng.normal(0.0, 0.001, size=len(dates))), 0.1)
    high = np.maximum(open_, close) * 1.004
    low = np.minimum(open_, close) * 0.996
    volume = rng.uniform(80_000.0, 180_000.0, size=len(dates))
    frame = pd.DataFrame(
        {
            "date": dates,
            "open": open_ * close_scale,
            "high": high * close_scale,
            "low": low * close_scale,
            "close": close * close_scale,
            "adjusted_close": close * adjusted_scale,
            "volume": volume,
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False, engine="pyarrow")
    return path


def _write_cohort_fixture(
    tmp_path: Path,
    *,
    periods: int = 160,
    symbols: tuple[str, ...] = ("AAA.US", "BBB.US", "CCC.US"),
) -> tuple[Path, Path, pd.DatetimeIndex, tuple[str, ...]]:
    dates = pd.bdate_range("2020-01-02", periods=periods)
    data_dir = tmp_path / "snapshot"
    files: list[dict[str, str]] = []
    for index, symbol in enumerate(symbols):
        relative = f"normalized/{symbol}.parquet"
        _write_symbol_parquet(
            data_dir / relative,
            dates,
            seed=20260920 + index,
            start_price=80.0 + 10.0 * index,
        )
        files.append({"symbol": symbol, "file": relative})
    spy_relative = f"normalized/{BENCHMARK_SYMBOL}.parquet"
    _write_symbol_parquet(
        data_dir / spy_relative,
        dates,
        seed=42,
        start_price=300.0,
    )
    files.append({"symbol": BENCHMARK_SYMBOL, "file": spy_relative})
    inventory_path = tmp_path / "per_stock_coverage.json"
    inventory_path.write_text(json.dumps(files), encoding="utf-8")
    return data_dir, inventory_path, dates, symbols


def _reduced_config(
    tmp_path: Path,
    *,
    symbols: tuple[str, ...] | None = None,
    **overrides: object,
) -> RealDataMultifactorDiagnosticConfig:
    data_dir, inventory_path, dates, default_symbols = _write_cohort_fixture(
        tmp_path,
        symbols=symbols or ("AAA.US", "BBB.US", "CCC.US"),
    )
    payload = {
        "data_dir": data_dir,
        "inventory_path": inventory_path,
        "start_date": dates[0].strftime("%Y-%m-%d"),
        "end_date": dates[-1].strftime("%Y-%m-%d"),
        "symbols": default_symbols,
        "benchmark_symbol": BENCHMARK_SYMBOL,
        "top_n": 2,
        "quantiles": 2,
        "pbo_n_splits": 4,
        "alpha_ids": (ALPHA_001, ALPHA_101),
        "composite_ids": (EQUAL_WEIGHTED_COMPOSITE,),
        "include_weighting_comparisons": True,
        "slippage_bps": 5.0,
        "signal_lag_periods": 1,
    }
    payload.update(overrides)
    return RealDataMultifactorDiagnosticConfig(**payload)


def test_real_data_config_defaults() -> None:
    config = RealDataMultifactorDiagnosticConfig()
    assert config.symbols == tuple(BLUECHIP_50_COHORT)
    assert config.benchmark_symbol == BENCHMARK_SYMBOL
    assert config.rebalance_frequency == "ME"
    assert config.top_n == 5
    assert config.weighting_scheme == "equal"
    assert config.long_short_weighting_scheme == "equal"
    assert config.turnover_penalty_lambda == 0.0
    assert config.volatility_window == 20
    assert config.transaction_cost_bps == 0.0
    assert config.slippage_bps == 5.0
    assert config.signal_lag_periods == 1
    assert config.periods_per_year == 252
    assert config.start_date == DEFAULT_START_DATE
    assert config.end_date == DEFAULT_END_DATE
    assert config.alpha_ids == ALPHA_IDS
    assert config.composite_ids == COMPOSITE_IDS
    assert config.data_dir == default_data_dir()
    assert len(ALPHA_IDS) == 52
    assert len(COMPOSITE_IDS) == 10
    assert len(FACTOR_IDS) == 62
    assert default_data_dir().name == DEFAULT_SNAPSHOT_DIR_NAME
    assert default_inventory_path().name == DEFAULT_INVENTORY_FILE_NAME


def test_to_mvp_config_propagates_shared_backtest_fields() -> None:
    config = RealDataMultifactorDiagnosticConfig(
        data_dir=Path("/tmp/unused-data"),
        inventory_path=Path("/tmp/unused-inventory.json"),
        top_n=3,
        slippage_bps=7.5,
        signal_lag_periods=1,
        turnover_penalty_lambda=0.5,
        weighting_scheme="inverse_volatility",
        pbo_n_splits=4,
        quantiles=2,
        warmup_periods=25,
    )
    mvp = to_mvp_config(config)
    assert mvp.top_n == 3
    assert mvp.slippage_bps == 7.5
    assert mvp.signal_lag_periods == 1
    assert mvp.turnover_penalty_lambda == 0.5
    assert mvp.weighting_scheme == "inverse_volatility"
    assert mvp.pbo_n_splits == 4
    assert mvp.quantiles == 2
    assert mvp.warmup_periods == 25


def test_redact_local_path_hides_private_defaults_and_tmp_paths() -> None:
    assert redact_local_path(default_data_dir()) == REDACTED_DATA_DIR
    assert redact_local_path(default_inventory_path()) == REDACTED_INVENTORY_PATH
    assert redact_local_path(Path("/tmp/efr-pytest-m40-real")) == REDACTED_LOCAL_PATH


def test_build_adjusted_research_panels_keeps_dollar_volume_basis() -> None:
    dates = pd.DatetimeIndex(["2020-08-28", "2020-08-31"], name="date")
    close = pd.DataFrame({"AAA.US": [400.0, 100.0]}, index=dates)
    adjusted = pd.DataFrame({"AAA.US": [100.0, 100.0]}, index=dates)
    # Vendor volume in EODHD is already split-adjusted (e.g. 4000.0 on both days)
    volume = pd.DataFrame({"AAA.US": [4_000.0, 4_000.0]}, index=dates)
    open_ = close * 0.99
    high = close * 1.01
    low = close * 0.98
    panels = build_adjusted_research_panels(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "adjusted_close": adjusted,
            "volume": volume,
        }
    )
    # Research volume remains identical to vendor split-adjusted volume
    pd.testing.assert_frame_equal(panels["volume"], volume)
    pd.testing.assert_frame_equal(panels["close"], adjusted)
    # Dollar volume is adjusted_close * volume = 400,000 on both days (stable across split)
    expected_dollar = pd.DataFrame({"AAA.US": [400_000.0, 400_000.0]}, index=dates)
    dollar_adj = panels["close"] * panels["volume"]
    pd.testing.assert_frame_equal(dollar_adj, expected_dollar)
    assert pd.isna(panels["returns"].iloc[0, 0])
    assert panels["returns"].iloc[1, 0] == pytest.approx(0.0)
    raw_close_return = close.iloc[1, 0] / close.iloc[0, 0] - 1.0
    assert raw_close_return == pytest.approx(-0.75)


def test_runner_uses_spy_benchmark_and_writes_report_structure(tmp_path: Path) -> None:
    config = _reduced_config(tmp_path)
    report_path = tmp_path / "real_data_multifactor_diagnostic.md"
    result = run_real_data_multifactor_diagnostic(
        config=config,
        report_path=report_path,
        write_outputs=True,
    )

    assert result["evidence_ceiling"] == "DIAGNOSTIC_ONLY"
    assert result["readiness_decision"] == "diagnostic_ready_with_low_caveats"
    assert result["config"].top_n == 2
    assert result["config"].slippage_bps == 5.0
    assert result["config"].signal_lag_periods == 1
    assert list(result["prices"].columns) == ["AAA.US", "BBB.US", "CCC.US"]
    assert BENCHMARK_SYMBOL not in result["prices"].columns
    assert result["accounting_benchmark"].name == BENCHMARK_SYMBOL
    assert result["accounting_benchmark"].index.equals(result["prices"].index)
    assert list(result["evaluated_factor_ids"]) == [
        ALPHA_001,
        ALPHA_101,
        EQUAL_WEIGHTED_COMPOSITE,
    ]
    first_backtest = result["factors"][ALPHA_001]["backtest"]
    assert first_backtest.benchmark_equity_curve is not None
    assert first_backtest.benchmark_returns is not None
    spy_path = config.data_dir / "normalized" / f"{BENCHMARK_SYMBOL}.parquet"
    spy_frame = pd.read_parquet(spy_path, engine="pyarrow")
    spy_close = spy_frame.set_index(pd.to_datetime(spy_frame["date"]))["adjusted_close"]
    spy_close.index.name = "date"
    pd.testing.assert_series_equal(
        result["accounting_benchmark"],
        spy_close.rename(BENCHMARK_SYMBOL),
        check_freq=False,
    )

    report_text = report_path.read_text(encoding="utf-8")
    assert report_text.startswith("# Real-Data Blue-Chip Multi-Factor Diagnostic")
    assert "`DIAGNOSTIC_ONLY`" in report_text
    assert "Survivorship bias: `true`" in report_text
    assert f"Benchmark: `{BENCHMARK_SYMBOL}` vendor adjusted close" in report_text
    assert "## Factor diagnostics" in report_text
    assert "## Overfitting diagnostics (CSCV / PBO)" in report_text
    assert ALPHA_001 in report_text
    assert EQUAL_WEIGHTED_COMPOSITE in report_text
    assert "/Users/" not in report_text
    assert "private_data" not in report_text
    assert str(config.data_dir) not in report_text

    log_path = Path(result["experiment_log_path"])
    trials_path = Path(result["trial_inventory_path"])
    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert payload["experiment_type"] == REAL_DATA_MULTIFACTOR_EXPERIMENT_TYPE
    assert payload["assumptions"]["dataset_manifest_reviewed"] is False
    assert payload["assumptions"]["formal_interpretation_eligible"] is False
    assert payload["assumptions"]["survivorship_bias"] is True
    assert payload["assumptions"]["benchmark"] == f"{BENCHMARK_SYMBOL} vendor adjusted close"
    assert payload["config"]["top_n"] == 2
    assert payload["config"]["slippage_bps"] == 5.0
    assert payload["config"]["signal_lag_periods"] == 1
    assert payload["config"]["inventory_path"] in (
        REDACTED_LOCAL_PATH,
        REDACTED_INVENTORY_PATH,
    )
    for caveat in DIAGNOSTIC_REAL_DATA_CAVEATS:
        assert caveat in payload["caveats"]
    assert "/Users/" not in json.dumps(payload)

    assert trials_path.is_file()
    records = [
        json.loads(line)
        for line in trials_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    completed = [record for record in records if record["status"] == "completed"]
    assert completed
    assert all("trial_id" in record for record in completed)
    assert result["trial_family"]["attempt_count"] >= 6
    assert result["trial_family"]["distinct_trial_count"] >= 6
    assert "pbo" in result["pbo_summary"]
    assert len(result["weighting_comparisons"]) == 4


def test_runner_records_trials_without_writing_when_requested(tmp_path: Path) -> None:
    config = _reduced_config(tmp_path, include_weighting_comparisons=False)
    result = run_real_data_multifactor_diagnostic(
        config=config,
        report_path=tmp_path / "unused.md",
        write_outputs=False,
    )
    assert result["trial_inventory_path"] is None
    assert not (tmp_path / "unused.md").exists()
    assert result["trial_family"]["attempt_count"] == 6
    statuses = {record["status"] for record in result["trial_inventory"]}
    assert statuses == {"completed"}


def test_unknown_alpha_id_is_refused(tmp_path: Path) -> None:
    config = _reduced_config(tmp_path, alpha_ids=(ALPHA_001, "NOT_AN_ALPHA"))
    with pytest.raises(ValueError, match="unknown"):
        run_real_data_multifactor_diagnostic(
            config=config,
            report_path=tmp_path / "unused.md",
            write_outputs=False,
        )


def test_product_interaction_requires_parent_alphas(tmp_path: Path) -> None:
    config = _reduced_config(
        tmp_path,
        alpha_ids=(ALPHA_001, ALPHA_101),
        composite_ids=(ALPHA_PRODUCT_INTERACTION,),
    )
    with pytest.raises(ValueError, match="ALPHA_016"):
        run_real_data_multifactor_diagnostic(
            config=config,
            report_path=tmp_path / "unused.md",
            write_outputs=False,
        )


def test_module_has_no_broker_or_remote_fetch_imports() -> None:
    source = inspect.getsource(real_data_module)
    tree = ast.parse(source)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    forbidden = (
        "requests",
        "urllib",
        "yfinance",
        "alpaca",
        "ccxt",
        "broker",
        "brokerage",
    )
    for module_name in imported:
        assert not any(term in module_name for term in forbidden)
    assert "data.parquet_loader" in imported
    assert "data.bluechip_cohort" in imported


def test_registry_skips_real_data_experiment_logs(tmp_path: Path) -> None:
    from reporting.experiment_log import SYNTHETIC_RESEARCH_CAVEATS, write_experiment_log

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    write_experiment_log(
        log_path=log_dir / "synthetic.json",
        experiment_id="synthetic-demo",
        title="Synthetic Demo",
        experiment_type="synthetic_diagnostic",
        summary="Synthetic sidecar.",
        config={"seed": 1},
        assumptions={
            "data_scope": "synthetic only",
            "date_range": {"start": "2024-01-02", "end": "2024-02-01"},
            "universe": "synthetic",
            "benchmark": "synthetic",
            "transaction_cost_model": "none",
            "slippage_model": "none",
        },
        outputs={"markdown_report": "reports/synthetic.md", "experiment_log": "a.json"},
        caveats=SYNTHETIC_RESEARCH_CAVEATS,
        next_action="Keep synthetic.",
    )
    write_experiment_log(
        log_path=log_dir / "real.json",
        experiment_id="real-data-multifactor-diagnostic",
        title="Real Data",
        experiment_type=REAL_DATA_MULTIFACTOR_EXPERIMENT_TYPE,
        summary="Real-data sidecar.",
        config={"top_n": 5},
        assumptions={
            "data_scope": "local EODHD Parquet diagnostic",
            "date_range": {"start": "2016-08-08", "end": "2026-08-07"},
            "universe": "blue-chip",
            "benchmark": "SPY.US vendor adjusted close",
            "transaction_cost_model": "none",
            "slippage_model": "none",
        },
        outputs={"markdown_report": "reports/real.md", "experiment_log": "b.json"},
        caveats=DIAGNOSTIC_REAL_DATA_CAVEATS,
        required_caveats=DIAGNOSTIC_REAL_DATA_CAVEATS,
        next_action="Keep diagnostic.",
    )

    registry = build_experiment_registry(log_dir)
    assert list(registry["experiment_id"]) == ["synthetic-demo"]


def test_distinct_composite_trial_ids_when_parents_change(tmp_path: Path) -> None:
    from research.multifactor_diagnostic_mvp import ALPHA_016

    cfg_a = _reduced_config(
        tmp_path / "run_a",
        alpha_ids=(ALPHA_001, ALPHA_101),
        composite_ids=(EQUAL_WEIGHTED_COMPOSITE,),
        include_weighting_comparisons=False,
    )
    res_a = run_real_data_multifactor_diagnostic(
        config=cfg_a,
        report_path=tmp_path / "run_a" / "report.md",
        write_outputs=False,
    )

    cfg_b = _reduced_config(
        tmp_path / "run_b",
        alpha_ids=(ALPHA_001, ALPHA_016),
        composite_ids=(EQUAL_WEIGHTED_COMPOSITE,),
        include_weighting_comparisons=False,
    )
    res_b = run_real_data_multifactor_diagnostic(
        config=cfg_b,
        report_path=tmp_path / "run_b" / "report.md",
        write_outputs=False,
    )

    trial_a = next(
        t for t in res_a["trial_inventory"]
        if t["specification"]["factor_id"] == EQUAL_WEIGHTED_COMPOSITE
        and t["specification"]["direction"] == "long_only"
    )
    trial_b = next(
        t for t in res_b["trial_inventory"]
        if t["specification"]["factor_id"] == EQUAL_WEIGHTED_COMPOSITE
        and t["specification"]["direction"] == "long_only"
    )
    assert trial_a["trial_id"] != trial_b["trial_id"]


def test_feature_calculation_failure_is_recorded_in_trials_jsonl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _reduced_config(
        tmp_path,
        alpha_ids=(ALPHA_001, ALPHA_101),
        include_weighting_comparisons=False,
    )
    report_path = tmp_path / "report.md"
    orig_calc = real_data_module.calculate_diagnostic_alpha

    def mock_calc(factor_id: str, panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
        if factor_id == ALPHA_101:
            raise ValueError("simulated feature failure for ALPHA_101")
        return orig_calc(factor_id, panels)

    monkeypatch.setattr(real_data_module, "calculate_diagnostic_alpha", mock_calc)

    with pytest.raises(ValueError, match="simulated feature failure"):
        run_real_data_multifactor_diagnostic(
            config=config,
            report_path=report_path,
            write_outputs=True,
        )

    jsonl_path = tmp_path / "report.trials.jsonl"
    assert jsonl_path.exists()
    events = [json.loads(line) for line in jsonl_path.read_text().splitlines()]
    failed_events = [e for e in events if e.get("status") == "failed"]
    assert len(failed_events) == 1
    assert failed_events[0]["specification"]["factor_id"] == ALPHA_101
    assert failed_events[0]["error"] == "simulated feature failure for ALPHA_101"


def test_evaluate_diagnostic_readiness_valid_and_invalid() -> None:
    dates = pd.date_range("2024-01-02", periods=5)
    df = pd.DataFrame({"A": [1.0, 2.0, 3.0, 4.0, 5.0]}, index=dates)
    panels = {
        "open": df, "high": df, "low": df, "close": df, "volume": df * 100
    }
    benchmark = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0], index=dates)
    config = RealDataMultifactorDiagnosticConfig()

    assert evaluate_diagnostic_readiness(panels, benchmark, config) == "diagnostic_ready_with_low_caveats"

    # Misaligned benchmark
    bad_bm = pd.Series([100.0], index=pd.date_range("2024-01-02", periods=1))
    assert evaluate_diagnostic_readiness(panels, bad_bm, config) == "refused_benchmark_misaligned"

    # Non-positive price
    bad_panels = dict(panels)
    bad_panels["close"] = pd.DataFrame({"A": [1.0, 0.0, 3.0, 4.0, 5.0]}, index=dates)
    assert evaluate_diagnostic_readiness(bad_panels, benchmark, config) == "refused_non_positive_close"
