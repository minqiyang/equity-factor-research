from dataclasses import replace
from pathlib import Path

from research.demo_v0 import (
    DEMO_V0_CONFIG,
    load_attempt_records as load_demo_v0_attempt_records,
    run_demo_v0,
)
from research.synthetic_multifactor_backtest_demo import (
    FROZEN_CONFIG,
    load_attempt_records as load_multifactor_attempt_records,
    run_synthetic_multifactor_backtest_demo,
)


def test_official_demo_v0_periods_remain_756() -> None:
    assert DEMO_V0_CONFIG.periods == 756
    assert FROZEN_CONFIG.periods == DEMO_V0_CONFIG.periods


def test_demo_v0_runs_on_double_official_periods(tmp_path: Path) -> None:
    assert DEMO_V0_CONFIG.periods == 756
    longer = replace(DEMO_V0_CONFIG, periods=2 * DEMO_V0_CONFIG.periods)
    assert longer.periods == 1512
    assert longer.lookback_periods == 252
    assert longer.skip_periods == 21
    assert longer.rebalance_frequency == "ME"
    assert longer.top_n == 5
    assert longer.transaction_cost_bps == 10.0
    assert longer.slippage_bps == 0.0
    assert longer.seed == 20260521
    assert longer.asset_count == 20
    assert DEMO_V0_CONFIG.periods == 756

    report_path = tmp_path / "demo_v0.md"
    attempt_log_path = tmp_path / "demo_v0_attempts.jsonl"
    result = run_demo_v0(
        config=longer,
        report_path=report_path,
        attempt_log_path=attempt_log_path,
    )

    report_text = report_path.read_text(encoding="utf-8")
    records = load_demo_v0_attempt_records(attempt_log_path)
    assert DEMO_V0_CONFIG.periods == 756
    assert DEMO_V0_CONFIG.lookback_periods == 252
    assert DEMO_V0_CONFIG.skip_periods == 21
    assert DEMO_V0_CONFIG.rebalance_frequency == "ME"
    assert DEMO_V0_CONFIG.top_n == 5
    assert DEMO_V0_CONFIG.transaction_cost_bps == 10.0
    assert DEMO_V0_CONFIG.slippage_bps == 0.0
    assert records[1]["source_price_rows"] == 1512
    assert records[1]["config"]["periods"] == 1512
    assert records[1]["config"]["lookback_periods"] == 252
    assert records[1]["config"]["skip_periods"] == 21
    assert records[1]["data_scope"] == "synthetic only"
    assert records[1]["not_a_profitability_claim"] is True
    assert "synthetic data only" in report_text
    assert "not a profitability claim" in report_text
    assert "Price rows: `1512`" in report_text
    assert "Momentum lookback periods: `252`" in report_text
    assert "Momentum skipped recent periods: `21`" in report_text
    assert result.holdings.shape[1] == 20
    assert result.assumptions["transaction_cost_bps"] == 10.0
    assert result.assumptions["slippage_bps"] == 0.0
    assert result.assumptions["zero_cost_or_slippage_is_diagnostic"] is True


def test_multifactor_demo_runs_on_double_official_periods(tmp_path: Path) -> None:
    assert FROZEN_CONFIG.periods == 756
    assert DEMO_V0_CONFIG.lookback_periods == 252
    assert DEMO_V0_CONFIG.skip_periods == 21
    longer = replace(FROZEN_CONFIG, periods=2 * DEMO_V0_CONFIG.periods)
    assert longer.periods == 1512
    assert longer.rebalance_frequency == "ME"
    assert longer.top_n == 5
    assert longer.transaction_cost_bps == 10.0
    assert longer.slippage_bps == 0.0
    assert longer.price_seed == 20260521
    assert longer.asset_count == 20
    assert FROZEN_CONFIG.periods == 756

    report_path = tmp_path / "multifactor.md"
    attempt_log_path = tmp_path / "multifactor_attempts.jsonl"
    result = run_synthetic_multifactor_backtest_demo(
        config=longer,
        report_path=report_path,
        attempt_log_path=attempt_log_path,
    )

    report_text = report_path.read_text(encoding="utf-8")
    records = load_multifactor_attempt_records(attempt_log_path)
    assert FROZEN_CONFIG.periods == 756
    assert DEMO_V0_CONFIG.periods == 756
    assert DEMO_V0_CONFIG.lookback_periods == 252
    assert DEMO_V0_CONFIG.skip_periods == 21
    assert result.prices.shape == (1512, 20)
    assert records[1]["source_price_rows"] == 1512
    assert records[1]["config"]["periods"] == 1512
    assert records[1]["data_scope"] == "synthetic only"
    assert records[1]["not_a_profitability_claim"] is True
    assert "synthetic data only" in report_text
    assert "not a profitability claim" in report_text
    assert "Price rows: `1512`" in report_text
    assert result.backtest_result.holdings.shape[1] == 20
    assert result.backtest_result.assumptions["transaction_cost_bps"] == 10.0
    assert result.backtest_result.assumptions["slippage_bps"] == 0.0
    assert result.backtest_result.assumptions["zero_cost_or_slippage_is_diagnostic"] is True
