import ast
import inspect
from pathlib import Path

import pytest

from research.demo_v0 import (
    COMMAND_NAME,
    DEMO_V0_CONFIG,
    TIMING_CONTRACT,
    load_attempt_records,
    main,
    run_demo_v0,
)
from research.synthetic_momentum_demo import SyntheticDemoConfig


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
    assert result.holdings.shape[1] == 8
    assert result.assumptions["execution_timing"] == TIMING_CONTRACT
    assert result.assumptions["zero_cost_or_slippage_is_diagnostic"] is True


def test_demo_v0_source_stays_synthetic_only() -> None:
    source = Path(__import__("research.demo_v0", fromlist=["demo_v0"]).__file__).read_text(
        encoding="utf-8"
    )
    assert "generate_synthetic_prices" in source
    assert "calculate_12_1_momentum" in source
    assert "run_long_only_backtest" in source
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
    assert len(records) == 1
    record = records[0]
    assert record["attempt_id"] == 1
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
    assert [record["status"] for record in records] == ["success", "failure"]
    assert records[0]["attempt_id"] == 1
    assert records[1]["attempt_id"] == 2
    assert records[1]["error_type"] == "ValueError"
    assert "warm-up anchor" in records[1]["error_message"]
    assert records[1]["timing_contract"] == TIMING_CONTRACT
    assert records[1]["data_scope"] == "synthetic only"
    assert records[1]["metrics"] == {}
    serialized = attempt_log_path.read_text(encoding="utf-8")
    assert serialized.count("\n") == 2
    assert '"status": "failure"' in serialized
    assert '"status": "success"' in serialized
