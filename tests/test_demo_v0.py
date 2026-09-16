import ast
from dataclasses import replace
import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import research.demo_v0 as demo
from research.demo_v0 import (
    COMMAND_NAME,
    DEMO_V0_CONFIG,
    TIMING_CONTRACT,
    load_attempt_records,
    main,
    run_demo_v0,
)
from research.source_row_lag import DEMO_SIGNAL_LAG_PERIODS, SIGNAL_LAG_UNIT
from research.synthetic_momentum_demo import (
    SyntheticDemoConfig,
    generate_synthetic_prices,
)


def _short_config() -> SyntheticDemoConfig:
    return SyntheticDemoConfig(
        seed=123,
        asset_count=8,
        periods=320,
        lookback_periods=60,
        skip_periods=5,
        rebalance_frequency="ME",
        top_n=3,
        transaction_cost_bps=10.0,
        slippage_bps=0.0,
        periods_per_year=252,
    )


def test_frozen_demo_v0_config_copies_synthetic_demo_values() -> None:
    assert DEMO_V0_CONFIG.seed == 20260521
    assert DEMO_V0_CONFIG.asset_count == 20
    assert DEMO_V0_CONFIG.periods == 756
    assert DEMO_V0_CONFIG.lookback_periods == 252
    assert DEMO_V0_CONFIG.skip_periods == 21
    assert DEMO_V0_CONFIG.rebalance_frequency == "ME"
    assert DEMO_V0_CONFIG.top_n == 5
    assert DEMO_V0_CONFIG.transaction_cost_bps == 10.0
    assert DEMO_V0_CONFIG.slippage_bps == 0.0
    assert DEMO_V0_CONFIG.periods_per_year == 252
    assert DEMO_V0_CONFIG == SyntheticDemoConfig()


def test_demo_v0_module_command_uses_frozen_config() -> None:
    source = inspect.getsource(main)
    tree = ast.parse(source)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "run_demo_v0"
    ]
    assert len(calls) == 1
    assert calls[0].args == []
    assert calls[0].keywords == []
    assert COMMAND_NAME == "python -m research.demo_v0"


def test_demo_v0_writes_comparison_report_claims(tmp_path: Path) -> None:
    report_path = tmp_path / "demo_v0.md"
    attempt_log_path = tmp_path / "demo_v0_attempts.jsonl"

    result = run_demo_v0(
        config=_short_config(),
        report_path=report_path,
        attempt_log_path=attempt_log_path,
    )

    report_text = report_path.read_text(encoding="utf-8")
    assert "Demo v0 Comparison Report" in report_text
    assert "synthetic data only" in report_text
    assert "not a profitability claim" in report_text
    assert TIMING_CONTRACT in report_text
    assert "Timing contract: `after_close_signal_next_observed_close_v1`" in report_text
    assert "10.00` bps" in report_text
    assert "0.00` bps" in report_text
    assert "Zero cost or slippage diagnostic: `True`" in report_text
    assert "synthetic equal-weight universe benchmark" in report_text
    assert "| Tracking error vs synthetic benchmark |" in report_text
    assert "| Max drawdown |" in report_text
    assert "| Sharpe ratio |" in report_text
    assert "undivided" in report_text
    assert "All-Attempt Case Logging" in report_text
    assert "legacy diagnostic" in report_text
    assert "zero volume is refused" in report_text
    assert "supplied price series only" in report_text
    assert "cash-dividend overlay" in report_text
    assert "observed source rows" in report_text
    assert "omitted observation" in report_text
    assert "supplied observed index" in report_text
    assert "calendar-alignment" in report_text
    assert result.holdings.shape[1] == 8
    assert result.assumptions["execution_timing"] == TIMING_CONTRACT
    assert result.assumptions["signal_lag_periods"] == DEMO_SIGNAL_LAG_PERIODS
    assert result.assumptions["signal_lag_unit"] == SIGNAL_LAG_UNIT
    assert result.assumptions["zero_cost_or_slippage_is_diagnostic"] is True


def test_demo_v0_source_stays_synthetic_only() -> None:
    source = Path(__import__("research.demo_v0", fromlist=["demo_v0"]).__file__).read_text(
        encoding="utf-8"
    )
    assert "generate_synthetic_prices" in source
    assert "calculate_12_1_momentum" in source
    assert "run_long_only_backtest" in source
    assert "require_complete_price_bars" in source
    assert "require_positive_volume_bars" in source
    assert "require_observed_source_index" in source
    assert "refuse_cash_dividend_overlay" in source
    assert "DEMO_SIGNAL_LAG_PERIODS" in source
    assert "csv_loader" not in source
    assert "local_csv" not in source
    assert "place_order" not in source
    assert "eodhd" not in source.lower()
    assert '"brokerage_integration": False' in source or "brokerage_integration" in source


def test_successful_attempt_is_logged(tmp_path: Path) -> None:
    report_path = tmp_path / "demo_v0.md"
    attempt_log_path = tmp_path / "demo_v0_attempts.jsonl"

    result = run_demo_v0(
        config=_short_config(),
        report_path=report_path,
        attempt_log_path=attempt_log_path,
    )

    records = load_attempt_records(attempt_log_path)
    assert [record["status"] for record in records] == ["started", "success"]
    assert records[0]["attempt_id"] == 1
    assert records[1]["attempt_id"] == 1
    record = records[1]
    assert record["status"] == "success"
    assert record["command"] == COMMAND_NAME
    assert record["logging_kind"] == "all_attempt_case_logging"
    assert record["logging_ceiling"] == "lightweight_demo_diagnostic"
    assert record["data_scope"] == "synthetic only"
    assert record["timing_contract"] == TIMING_CONTRACT
    assert record["transaction_cost_bps"] == 10.0
    assert record["slippage_bps"] == 0.0
    assert record["zero_cost_or_slippage_is_diagnostic"] is True
    assert record["live_trading"] is False
    assert record["brokerage_integration"] is False
    assert record["not_a_profitability_claim"] is True
    assert record["error_type"] is None
    assert record["metrics"]["total_return"] == result.metrics["total_return"]
    assert "not a profitability claim" in record["caveats"]


def test_failed_attempt_is_logged_and_previous_records_remain(tmp_path: Path) -> None:
    report_path = tmp_path / "demo_v0.md"
    attempt_log_path = tmp_path / "demo_v0_attempts.jsonl"

    run_demo_v0(
        config=_short_config(),
        report_path=report_path,
        attempt_log_path=attempt_log_path,
    )

    failing_config = SyntheticDemoConfig(periods=10, lookback_periods=252)
    with pytest.raises(ValueError, match="warm-up anchor"):
        run_demo_v0(
            config=failing_config,
            report_path=report_path,
            attempt_log_path=attempt_log_path,
        )

    records = load_attempt_records(attempt_log_path)
    assert [record["status"] for record in records] == [
        "started",
        "success",
        "started",
        "failure",
    ]
    assert records[0]["attempt_id"] == 1
    assert records[1]["attempt_id"] == 1
    assert records[2]["attempt_id"] == 2
    assert records[3]["attempt_id"] == 2
    assert records[3]["error_type"] == "ValueError"
    assert "warm-up anchor" in records[3]["error_message"]
    assert records[3]["timing_contract"] == TIMING_CONTRACT
    assert records[3]["data_scope"] == "synthetic only"
    assert records[3]["metrics"] == {}
    serialized = attempt_log_path.read_text(encoding="utf-8")
    assert serialized.count("\n") == 4
    assert '"status": "failure"' in serialized
    assert '"status": "success"' in serialized
    assert '"status": "started"' in serialized


@pytest.mark.parametrize(
    ("interrupt", "error_type"),
    [
        (KeyboardInterrupt("demo v0 interrupted"), "KeyboardInterrupt"),
        (SystemExit("demo v0 interrupted"), "SystemExit"),
    ],
)
def test_catchable_interruption_is_logged_and_preserves_prior_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    interrupt: BaseException,
    error_type: str,
) -> None:
    report_path = tmp_path / "demo_v0.md"
    attempt_log_path = tmp_path / "demo_v0_attempts.jsonl"

    run_demo_v0(
        config=_short_config(),
        report_path=report_path,
        attempt_log_path=attempt_log_path,
    )
    prior_report = report_path.read_text(encoding="utf-8")
    prior_records = load_attempt_records(attempt_log_path)
    assert [record["status"] for record in prior_records] == ["started", "success"]

    def raise_interrupt(*args: object, **kwargs: object) -> None:
        raise interrupt

    monkeypatch.setattr(demo, "_run_demo_v0_pipeline", raise_interrupt)

    with pytest.raises(type(interrupt)):
        run_demo_v0(
            config=_short_config(),
            report_path=report_path,
            attempt_log_path=attempt_log_path,
        )

    records = load_attempt_records(attempt_log_path)
    assert records[:2] == prior_records
    assert [record["status"] for record in records] == [
        "started",
        "success",
        "started",
        "interrupted",
    ]
    assert records[2]["attempt_id"] == 2
    assert records[3]["attempt_id"] == 2
    assert records[3]["error_type"] == error_type
    assert records[3]["error_message"] == "demo v0 interrupted"
    assert report_path.read_text(encoding="utf-8") == prior_report


def test_logging_not_ready_stops_before_report_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report_path = tmp_path / "demo_v0.md"
    prior_report = "PRIOR COMPARISON REPORT\n"
    report_path.write_text(prior_report, encoding="utf-8")
    attempt_log_path = tmp_path / "demo_v0_attempts.jsonl"
    pipeline_calls = {"count": 0}

    def cannot_begin(*args: object, **kwargs: object) -> None:
        raise OSError("attempt log unavailable")

    def pipeline_must_not_run(*args: object, **kwargs: object) -> None:
        pipeline_calls["count"] += 1
        raise AssertionError("pipeline must not run when logging cannot begin")

    monkeypatch.setattr(demo, "append_attempt_record", cannot_begin)
    monkeypatch.setattr(demo, "_run_demo_v0_pipeline", pipeline_must_not_run)

    with pytest.raises(RuntimeError, match="attempt log cannot begin"):
        run_demo_v0(
            config=_short_config(),
            report_path=report_path,
            attempt_log_path=attempt_log_path,
        )

    assert report_path.read_text(encoding="utf-8") == prior_report
    assert pipeline_calls["count"] == 0
    assert not attempt_log_path.exists()


def _dirty_prices(mutate):
    original = demo.generate_synthetic_prices

    def dirty(config: SyntheticDemoConfig) -> pd.DataFrame:
        return mutate(original(config).copy())

    return dirty


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (
            lambda panel: panel.assign(**{panel.columns[0]: np.nan}),
            "missing bars is refused",
        ),
        (
            lambda panel: panel.drop(index=panel.index[0]),
            "source rows",
        ),
        (
            lambda panel: panel.assign(**{panel.columns[0]: 0.0}),
            "strictly positive",
        ),
    ],
)
def test_demo_v0_refuses_missing_or_dropped_price_bars_without_silent_repair(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutate,
    match: str,
) -> None:
    monkeypatch.setattr(demo, "generate_synthetic_prices", _dirty_prices(mutate))
    report_path = tmp_path / "demo_v0.md"
    attempt_log_path = tmp_path / "demo_v0_attempts.jsonl"

    with pytest.raises(ValueError, match=match):
        run_demo_v0(
            config=_short_config(),
            report_path=report_path,
            attempt_log_path=attempt_log_path,
        )

    assert not report_path.exists()
    records = load_attempt_records(attempt_log_path)
    assert [record["status"] for record in records] == ["started", "failure"]
    assert match in records[1]["error_message"]
    assert records[1]["metrics"] == {}


def test_demo_v0_refuses_zero_volume_without_silent_repair(tmp_path: Path) -> None:
    config = _short_config()
    prices = generate_synthetic_prices(config)
    volume = pd.DataFrame(1.0, index=prices.index, columns=prices.columns)
    volume.iloc[3, 1] = 0.0
    report_path = tmp_path / "demo_v0.md"
    attempt_log_path = tmp_path / "demo_v0_attempts.jsonl"

    with pytest.raises(ValueError, match="zero volume is refused"):
        run_demo_v0(
            config=config,
            report_path=report_path,
            attempt_log_path=attempt_log_path,
            volume=volume,
        )

    assert not report_path.exists()
    records = load_attempt_records(attempt_log_path)
    assert [record["status"] for record in records] == ["started", "failure"]
    assert "zero volume is refused" in records[1]["error_message"]


def test_demo_v0_lag_uses_previous_observed_source_row(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    full_config = SyntheticDemoConfig(
        seed=123,
        asset_count=8,
        periods=40,
        lookback_periods=10,
        skip_periods=2,
        rebalance_frequency="D",
        top_n=3,
        transaction_cost_bps=10.0,
        slippage_bps=0.0,
        periods_per_year=252,
    )
    full_prices = generate_synthetic_prices(full_config)
    hole = next(
        date
        for date in full_prices.index[15:-1]
        if full_prices.index[full_prices.index.get_loc(date) + 1]
        == date + pd.Timedelta(days=1)
    )
    gapped_prices = full_prices.drop(index=hole)
    run_config = replace(full_config, periods=len(gapped_prices))
    after = gapped_prices.index[gapped_prices.index.searchsorted(hole)]
    before = gapped_prices.index[gapped_prices.index.get_loc(after) - 1]

    monkeypatch.setattr(demo, "generate_synthetic_prices", lambda config: gapped_prices)

    result = run_demo_v0(
        config=run_config,
        report_path=tmp_path / "demo_v0.md",
        attempt_log_path=tmp_path / "demo_v0_attempts.jsonl",
    )

    ledger_row = next(row for row in result.timing_ledger if row.ledger_date == after)
    assert hole not in gapped_prices.index
    assert (after - before) > pd.Timedelta(days=1)
    assert after - pd.Timedelta(days=1) == hole
    assert ledger_row.signal_source_date == before
    assert result.assumptions["signal_lag_unit"] == SIGNAL_LAG_UNIT
    assert result.assumptions["signal_lag_periods"] == DEMO_SIGNAL_LAG_PERIODS


def test_demo_v0_refuses_extra_price_rows_versus_configured_periods(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = _short_config()
    prices = generate_synthetic_prices(config)
    extra = prices.reindex(
        prices.index.append(pd.DatetimeIndex([prices.index[-1] + pd.Timedelta(days=1)]))
    )
    run_config = replace(config, periods=len(prices))

    monkeypatch.setattr(demo, "generate_synthetic_prices", lambda current: extra)
    report_path = tmp_path / "demo_v0.md"
    attempt_log_path = tmp_path / "demo_v0_attempts.jsonl"

    with pytest.raises(ValueError, match="must keep .* source rows"):
        run_demo_v0(
            config=run_config,
            report_path=report_path,
            attempt_log_path=attempt_log_path,
        )

    assert not report_path.exists()
    records = load_attempt_records(attempt_log_path)
    assert [record["status"] for record in records] == ["started", "failure"]
    assert "must keep" in records[1]["error_message"]
    assert "source rows" in records[1]["error_message"]


def test_demo_v0_refuses_cash_dividend_overlay(tmp_path: Path) -> None:
    config = _short_config()
    prices = generate_synthetic_prices(config)
    cash_dividends = pd.DataFrame(2.0, index=prices.index, columns=prices.columns)
    report_path = tmp_path / "demo_v0.md"
    attempt_log_path = tmp_path / "demo_v0_attempts.jsonl"

    with pytest.raises(ValueError, match="cash_dividends overlay"):
        run_demo_v0(
            config=config,
            report_path=report_path,
            attempt_log_path=attempt_log_path,
            cash_dividends=cash_dividends,
        )

    assert not report_path.exists()
    records = load_attempt_records(attempt_log_path)
    assert [record["status"] for record in records] == ["started", "failure"]
    assert "cash_dividends overlay" in records[1]["error_message"]
    assert "PIT-007" in records[1]["error_message"]


def test_demo_v0_accepts_strictly_positive_volume(tmp_path: Path) -> None:
    config = _short_config()
    prices = generate_synthetic_prices(config)
    volume = pd.DataFrame(1.0, index=prices.index, columns=prices.columns)

    result = run_demo_v0(
        config=config,
        report_path=tmp_path / "demo_v0.md",
        attempt_log_path=tmp_path / "demo_v0_attempts.jsonl",
        volume=volume,
    )

    assert result.holdings.shape[1] == config.asset_count
