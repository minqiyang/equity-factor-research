import ast
import inspect
import json
import math
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
import pytest

from data.bluechip_cohort import BENCHMARK_SYMBOL, BLUECHIP_50_COHORT
from data.parquet_loader import DataIntegrityError
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
    assert len(COMPOSITE_IDS) == 12
    assert len(FACTOR_IDS) == 62
    assert config.pbo_holding_periods == 21
    assert config.pbo_embargo_periods == 5
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
    # 1. Split-only action (4:1 split)
    close_split = pd.DataFrame({"AAA.US": [400.0, 100.0]}, index=dates)
    split_factor = pd.DataFrame({"AAA.US": [4.0, 1.0]}, index=dates)
    adjusted_split = pd.DataFrame({"AAA.US": [100.0, 100.0]}, index=dates)
    volume_split = pd.DataFrame({"AAA.US": [4_000.0, 4_000.0]}, index=dates)
    panels_split = build_adjusted_research_panels(
        {
            "open": close_split * 0.99,
            "high": close_split * 1.01,
            "low": close_split * 0.98,
            "close": close_split,
            "adjusted_close": adjusted_split,
            "volume": volume_split,
            "split_factor": split_factor,
        }
    )
    # Research close is split-adjusted close (100.0 on both days)
    pd.testing.assert_frame_equal(panels_split["close"], pd.DataFrame({"AAA.US": [100.0, 100.0]}, index=dates))
    # Dollar volume is split_close * volume = 400,000 on both days (matches unadjusted close * raw_volume)
    expected_dollar = pd.DataFrame({"AAA.US": [400_000.0, 400_000.0]}, index=dates)
    pd.testing.assert_frame_equal(panels_split["dollar_volume"], expected_dollar)
    raw_vol = panels_split["raw_volume"]
    pd.testing.assert_frame_equal(close_split * raw_vol, expected_dollar)
    assert pd.isna(panels_split["returns"].iloc[0, 0])
    assert panels_split["returns"].iloc[1, 0] == pytest.approx(0.0)

    # 2. Dividend-only action (10% dividend back-adjustment, no split)
    close_div = pd.DataFrame({"AAA.US": [100.0, 100.0]}, index=dates)
    adjusted_div = pd.DataFrame({"AAA.US": [90.0, 100.0]}, index=dates)
    volume_div = pd.DataFrame({"AAA.US": [1_000.0, 1_000.0]}, index=dates)
    panels_div = build_adjusted_research_panels(
        {
            "open": close_div,
            "high": close_div,
            "low": close_div,
            "close": close_div,
            "adjusted_close": adjusted_div,
            "volume": volume_div,
        }
    )
    # Dollar volume remains 100,000 on both days (not deflated to 90,000 by dividend)
    expected_dollar_div = pd.DataFrame({"AAA.US": [100_000.0, 100_000.0]}, index=dates)
    pd.testing.assert_frame_equal(panels_div["dollar_volume"], expected_dollar_div)
    pd.testing.assert_frame_equal(panels_div["close"] * panels_div["volume"], expected_dollar_div)
    # Returns reflect the total return from adjusted_close (100 / 90 - 1 = +11.11%)
    assert panels_div["returns"].iloc[1, 0] == pytest.approx(100.0 / 90.0 - 1.0)

    # 3. Combined 4:1 split + 10% dividend action
    close_comb = pd.DataFrame({"AAA.US": [400.0, 100.0]}, index=dates)
    split_factor_comb = pd.DataFrame({"AAA.US": [4.0, 1.0]}, index=dates)
    adjusted_comb = pd.DataFrame({"AAA.US": [90.0, 100.0]}, index=dates)
    volume_comb = pd.DataFrame({"AAA.US": [4_000.0, 4_000.0]}, index=dates)
    panels_comb = build_adjusted_research_panels(
        {
            "open": close_comb,
            "high": close_comb,
            "low": close_comb,
            "close": close_comb,
            "adjusted_close": adjusted_comb,
            "volume": volume_comb,
            "split_factor": split_factor_comb,
        }
    )
    # Dollar volume is 400,000 on both days (matches true split-adjusted turnover, not 360,000)
    pd.testing.assert_frame_equal(panels_comb["dollar_volume"], expected_dollar)
    pd.testing.assert_frame_equal(panels_comb["close"] * panels_comb["volume"], expected_dollar)
    pd.testing.assert_frame_equal(close_comb * panels_comb["raw_volume"], expected_dollar)
    assert panels_comb["returns"].iloc[1, 0] == pytest.approx(100.0 / 90.0 - 1.0)


def test_build_adjusted_research_panels_refuses_unverified_split() -> None:
    dates = pd.DatetimeIndex(["2020-08-28", "2020-08-31"], name="date")
    close_split = pd.DataFrame({"AAA.US": [400.0, 100.0]}, index=dates)
    adjusted_split = pd.DataFrame({"AAA.US": [100.0, 100.0]}, index=dates)
    volume_split = pd.DataFrame({"AAA.US": [4_000.0, 4_000.0]}, index=dates)
    with pytest.raises(DataIntegrityError, match="discontinuities"):
        build_adjusted_research_panels(
            {
                "open": close_split,
                "high": close_split,
                "low": close_split,
                "close": close_split,
                "adjusted_close": adjusted_split,
                "volume": volume_split,
            }
        )


def test_runner_uses_adjusted_close_for_prices_forward_returns_and_benchmark(tmp_path: Path) -> None:
    dates = pd.bdate_range("2020-01-02", periods=160)
    data_dir = tmp_path / "snapshot"
    # Write cohort with close != adjusted_close (e.g. 10% dividend discount on adjusted_close)
    for index, symbol in enumerate(("AAA.US", "BBB.US", "CCC.US")):
        _write_symbol_parquet(
            data_dir / "normalized" / f"{symbol}.parquet",
            dates,
            seed=20260920 + index,
            close_scale=1.0,
            adjusted_scale=0.9,
        )
    _write_symbol_parquet(
        data_dir / "normalized" / f"{BENCHMARK_SYMBOL}.parquet",
        dates,
        seed=42,
        close_scale=1.0,
        adjusted_scale=0.85,
    )
    inventory_path = tmp_path / "per_stock_coverage.json"
    files = [
        {"symbol": s, "file": f"normalized/{s}.parquet"}
        for s in ("AAA.US", "BBB.US", "CCC.US", BENCHMARK_SYMBOL)
    ]
    inventory_path.write_text(json.dumps(files), encoding="utf-8")
    config = RealDataMultifactorDiagnosticConfig(
        data_dir=data_dir,
        inventory_path=inventory_path,
        symbols=("AAA.US", "BBB.US", "CCC.US"),
        benchmark_symbol=BENCHMARK_SYMBOL,
        alpha_ids=(ALPHA_001, ALPHA_101),
        composite_ids=(EQUAL_WEIGHTED_COMPOSITE,),
        include_weighting_comparisons=False,
    )
    result = run_real_data_multifactor_diagnostic(
        config=config,
        report_path=tmp_path / "report.md",
        write_outputs=False,
    )
    panels, benchmark, symbols = real_data_module.load_real_data_research_panels(config)
    pd.testing.assert_frame_equal(result["prices"], panels["adjusted_close"])
    assert not result["prices"].equals(panels["close"])
    pd.testing.assert_series_equal(result["accounting_benchmark"], benchmark)
    assert not result["accounting_benchmark"].equals(panels["close"].get(BENCHMARK_SYMBOL, pd.Series(dtype=float)))


def test_runner_uses_spy_benchmark_and_writes_report_structure(tmp_path: Path) -> None:
    config = _reduced_config(tmp_path)
    report_path = tmp_path / "real_data_multifactor_diagnostic.md"
    result = run_real_data_multifactor_diagnostic(
        config=config,
        report_path=report_path,
        write_outputs=True,
    )

    assert result["evidence_ceiling"] == "DIAGNOSTIC_ONLY"
    assert result["readiness_decision"] in (
        "diagnostic_ready_with_low_caveats",
        "diagnostic_ready_with_typed_missingness",
    )
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
    summary = result["multiple_testing"]
    assert summary["distinct_trial_count"] == result["trial_family"]["distinct_trial_count"]
    assert summary["attempt_count"] == result["trial_family"]["attempt_count"]
    assert payload["metrics"]["multiple_testing"] == summary
    assert "## Multiple-testing diagnostics" in report_text
    assert {row["specification"]["direction"] for row in summary["rows"]} == {"long_only", "long_short"}
    assert all("return_test" in record for record in completed)
    json.dumps(summary, allow_nan=False)
    assert "pbo" in result["pbo_summary"]
    assert result["cpcv_summary"] is not None
    assert result["cpcv_summary"]["holding_periods"] == 21
    assert result["cpcv_summary"]["embargo_periods"] == 5
    assert 0.0 <= result["cpcv_summary"]["pbo"] <= 1.0
    assert len(result["weighting_comparisons"]) == 4


def test_runner_reports_benchmark_excess_code_identity_and_long_short_pbo(
    tmp_path: Path,
) -> None:
    config = _reduced_config(tmp_path, include_weighting_comparisons=False)
    report_path = tmp_path / "real_data_multifactor_diagnostic.md"
    result = run_real_data_multifactor_diagnostic(
        config=config, report_path=report_path, write_outputs=True
    )

    window = result["prices"].loc[result["evaluation_start"] : result["evaluation_end"]]
    daily = window.pct_change(fill_method=None).iloc[1:].mean(axis=1)
    expected_equal_weight = float((1.0 + daily).prod() - 1.0)
    assert result["equal_weight_cohort_total_return"] == pytest.approx(
        expected_equal_weight, rel=1e-12
    )

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(real_data_module.__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert result["code_identity"]["git_commit"] == head
    assert isinstance(result["code_identity"]["tracked_changes"], bool)
    assert 0.0 <= result["pbo_long_short_summary"]["pbo"] <= 1.0

    report_text = report_path.read_text(encoding="utf-8")
    assert (
        "| excess vs benchmark | excess vs equal-weight cohort | tracking error |"
        in report_text
    )
    assert f"Code commit: `{head}`" in report_text
    assert "### Long-short alpha family" in report_text
    metrics = result["factors"][ALPHA_001]["backtest"].metrics
    diagnostics = report_text.split("## Factor diagnostics", 1)[1].split("\n## ", 1)[0]
    alpha_row = next(
        line for line in diagnostics.splitlines() if line.startswith(f"| {ALPHA_001} |")
    )
    assert f"{metrics['excess_total_return']:.2%}" in alpha_row
    assert f"{metrics['total_return'] - expected_equal_weight:.2%}" in alpha_row

    payload = json.loads(Path(result["experiment_log_path"]).read_text(encoding="utf-8"))
    assert payload["config"]["code_identity"]["git_commit"] == head
    assert payload["metrics"]["pbo_long_short_summary"]["pbo"] == pytest.approx(
        result["pbo_long_short_summary"]["pbo"]
    )
    assert payload["metrics"]["equal_weight_cohort_total_return"] == pytest.approx(
        expected_equal_weight
    )


def test_equal_weight_total_return_refuses_gaps() -> None:
    dates = pd.bdate_range("2021-01-04", periods=4)
    gapped = pd.DataFrame(
        {"A": [100.0, 101.0, np.nan, 103.0], "B": [50.0, 50.5, 51.0, 51.5]},
        index=dates,
    )
    assert math.isnan(real_data_module.equal_weight_total_return(gapped))
    complete = gapped.assign(A=[100.0, 101.0, 102.0, 103.0])
    daily = complete.pct_change(fill_method=None).iloc[1:].mean(axis=1)
    assert real_data_module.equal_weight_total_return(complete) == pytest.approx(
        float((1.0 + daily).prod() - 1.0), rel=1e-12
    )


def test_code_identity_without_git(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(*args, **kwargs):
        raise OSError("git unavailable")

    monkeypatch.setattr(real_data_module.subprocess, "run", unavailable)
    assert real_data_module.code_identity() == {
        "git_commit": None,
        "tracked_changes": None,
    }


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

    alpha_001_a = next(
        t for t in res_a["trial_inventory"]
        if t["specification"]["factor_id"] == ALPHA_001
        and t["specification"]["direction"] == "long_only"
    )
    alpha_001_b = next(
        t for t in res_b["trial_inventory"]
        if t["specification"]["factor_id"] == ALPHA_001
        and t["specification"]["direction"] == "long_only"
    )
    assert alpha_001_a["trial_id"] == alpha_001_b["trial_id"]


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
        "open": df, "high": df, "low": df, "close": df, "volume": df * 100,
        "returns": df.pct_change(),
        "permanent_id": pd.Series({"A": "PERM_A"}),
    }
    benchmark = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0], index=dates)
    config = RealDataMultifactorDiagnosticConfig()

    assert evaluate_diagnostic_readiness(panels, benchmark, config) == "diagnostic_ready_with_low_caveats"

    # Typed missingness (NaN in panel)
    nan_panels = dict(panels)
    nan_panels["close"] = pd.DataFrame({"A": [1.0, np.nan, 3.0, 4.0, 5.0]}, index=dates)
    assert (
        evaluate_diagnostic_readiness(nan_panels, benchmark, config)
        == "diagnostic_ready_with_typed_missingness"
    )

    # Missingness in returns at row 2
    nan_ret_panels = dict(panels)
    nan_ret = df.pct_change()
    nan_ret.iloc[2, 0] = np.nan
    nan_ret_panels["returns"] = nan_ret
    assert (
        evaluate_diagnostic_readiness(nan_ret_panels, benchmark, config)
        == "diagnostic_ready_with_typed_missingness"
    )

    # Misaligned benchmark
    bad_bm = pd.Series([100.0], index=pd.date_range("2024-01-02", periods=1))
    assert evaluate_diagnostic_readiness(panels, bad_bm, config) == "refused_benchmark_misaligned"

    # Non-positive price
    bad_panels = dict(panels)
    bad_panels["close"] = pd.DataFrame({"A": [1.0, 0.0, 3.0, 4.0, 5.0]}, index=dates)
    assert evaluate_diagnostic_readiness(bad_panels, benchmark, config) == "refused_non_positive_close"


def test_record_failure_deduplication(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _reduced_config(
        tmp_path,
        alpha_ids=(ALPHA_001,),
        composite_ids=(EQUAL_WEIGHTED_COMPOSITE,),
        include_weighting_comparisons=False,
    )
    report_path = tmp_path / "report.md"
    jsonl_path = tmp_path / "report.trials.jsonl"

    def mock_eval(**kwargs):
        fail_rec = {
            "trial_id": "simulated_trial",
            "attempt_id": "attempt1",
            "specification": {"factor_id": kwargs["factor_id"]},
            "status": "failed",
        }
        kwargs["inventory"].append(fail_rec)
        if kwargs.get("inventory_path") is not None:
            kwargs["inventory_path"].parent.mkdir(parents=True, exist_ok=True)
            with kwargs["inventory_path"].open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(fail_rec) + "\n")
        raise RuntimeError("simulated evaluation failure")

    monkeypatch.setattr(real_data_module, "_evaluate_factor", mock_eval)

    with pytest.raises(RuntimeError, match="simulated evaluation failure"):
        run_real_data_multifactor_diagnostic(
            config=config,
            report_path=report_path,
            write_outputs=True,
        )

    assert jsonl_path.exists()
    events = [json.loads(line) for line in jsonl_path.read_text().splitlines()]
    failed_events = [e for e in events if e.get("specification", {}).get("factor_id") == ALPHA_001 and e.get("status") == "failed"]
    assert len(failed_events) == 1


def test_runner_refuses_early_on_invalid_panels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _reduced_config(tmp_path)
    orig_load = real_data_module.load_real_data_research_panels

    def mock_load(cfg):
        panels, bm, syms = orig_load(cfg)
        panels["close"].iloc[0, 0] = -1.0
        return panels, bm, syms

    monkeypatch.setattr(real_data_module, "load_real_data_research_panels", mock_load)

    with pytest.raises(DataIntegrityError, match="Diagnostic dataset refused: refused_non_positive_close"):
        run_real_data_multifactor_diagnostic(
            config=config,
            report_path=tmp_path / "report.md",
            write_outputs=False,
        )


def test_runner_evaluates_ml_composites(tmp_path: Path) -> None:
    from research.real_data_multifactor_diagnostic import (
        GRADIENT_BOOSTING_COMPOSITE,
        RANDOM_FOREST_COMPOSITE,
    )

    config = _reduced_config(
        tmp_path,
        alpha_ids=(ALPHA_001, ALPHA_101),
        composite_ids=(RANDOM_FOREST_COMPOSITE, GRADIENT_BOOSTING_COMPOSITE),
        include_weighting_comparisons=False,
    )
    report_path = tmp_path / "ml_report.md"
    result = run_real_data_multifactor_diagnostic(
        config=config,
        report_path=report_path,
        write_outputs=True,
    )

    assert RANDOM_FOREST_COMPOSITE in result["factors"]
    assert GRADIENT_BOOSTING_COMPOSITE in result["factors"]
    assert RANDOM_FOREST_COMPOSITE in result["ml_feature_importances"]
    assert GRADIENT_BOOSTING_COMPOSITE in result["ml_feature_importances"]

    rf_backtest = result["factors"][RANDOM_FOREST_COMPOSITE]["backtest"]
    assert rf_backtest.metrics["sharpe_ratio"] is not None
    gb_backtest = result["factors"][GRADIENT_BOOSTING_COMPOSITE]["backtest"]
    assert gb_backtest.metrics["sharpe_ratio"] is not None

    report_text = report_path.read_text(encoding="utf-8")
    assert "## Machine learning factor combinations and feature importances" in report_text
    assert RANDOM_FOREST_COMPOSITE in report_text
    assert GRADIENT_BOOSTING_COMPOSITE in report_text

