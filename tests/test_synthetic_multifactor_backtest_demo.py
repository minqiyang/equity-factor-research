import ast
import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

import research.synthetic_multifactor_backtest_demo as demo
from features.combine import combine_factors
from research.demo_v0 import DEMO_V0_CONFIG
from research.synthetic_momentum_demo import generate_synthetic_prices
from research.synthetic_multifactor_backtest_demo import (
    COMMAND_NAME,
    FROZEN_CONFIG,
    TIMING_CONTRACT,
    SyntheticMultifactorBacktestConfig,
    load_attempt_records,
    main,
    run_synthetic_multifactor_backtest_demo,
)
from research.synthetic_multifactor_workflow_demo import FACTOR_NAMES


def _short_config() -> SyntheticMultifactorBacktestConfig:
    return SyntheticMultifactorBacktestConfig(
        price_seed=123,
        factor_seed=456,
        asset_count=8,
        periods=80,
        start_date="2021-01-01",
        top_n=3,
        transaction_cost_bps=10.0,
        slippage_bps=0.0,
        periods_per_year=252,
    )


def test_frozen_config_matches_demo_v0_price_fixture_and_workflow_weights() -> None:
    assert FROZEN_CONFIG.price_seed == DEMO_V0_CONFIG.seed
    assert FROZEN_CONFIG.asset_count == DEMO_V0_CONFIG.asset_count
    assert FROZEN_CONFIG.periods == DEMO_V0_CONFIG.periods
    assert FROZEN_CONFIG.start_date == DEMO_V0_CONFIG.start_date
    assert FROZEN_CONFIG.starting_price == DEMO_V0_CONFIG.starting_price
    assert FROZEN_CONFIG.rebalance_frequency == DEMO_V0_CONFIG.rebalance_frequency == "ME"
    assert FROZEN_CONFIG.top_n == DEMO_V0_CONFIG.top_n == 5
    assert FROZEN_CONFIG.transaction_cost_bps == DEMO_V0_CONFIG.transaction_cost_bps == 10.0
    assert FROZEN_CONFIG.slippage_bps == DEMO_V0_CONFIG.slippage_bps == 0.0
    assert FROZEN_CONFIG.periods_per_year == DEMO_V0_CONFIG.periods_per_year == 252
    assert FROZEN_CONFIG.factor_seed == 20260528
    assert FROZEN_CONFIG.weights == {
        "synthetic_momentum": 0.50,
        "synthetic_quality": 0.30,
        "synthetic_reversal": 0.20,
    }
    assert tuple(FROZEN_CONFIG.weights) == FACTOR_NAMES


def test_frozen_price_fixture_matches_demo_v0_synthetic_prices() -> None:
    expected = generate_synthetic_prices(DEMO_V0_CONFIG)
    observed = generate_synthetic_prices(demo._price_config(FROZEN_CONFIG))

    assert_frame_equal(observed, expected)
    assert list(observed.columns) == [f"ASSET_{index:02d}" for index in range(1, 21)]


def test_module_command_uses_frozen_config() -> None:
    source = inspect.getsource(main)
    tree = ast.parse(source)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", None) == "run_synthetic_multifactor_backtest_demo"
    ]
    assert len(calls) == 1
    assert calls[0].args == []
    assert calls[0].keywords == []
    assert COMMAND_NAME == "python -m research.synthetic_multifactor_backtest_demo"


def test_scores_holdings_metrics_and_report_are_deterministic(tmp_path: Path) -> None:
    config = _short_config()
    attempt_log_path = tmp_path / "attempts.jsonl"
    first = run_synthetic_multifactor_backtest_demo(
        config=config,
        report_path=tmp_path / "first.md",
        attempt_log_path=attempt_log_path,
    )
    second = run_synthetic_multifactor_backtest_demo(
        config=config,
        report_path=tmp_path / "second.md",
        attempt_log_path=attempt_log_path,
    )

    assert_frame_equal(first.prices, second.prices)
    assert_frame_equal(first.combined_score, second.combined_score)
    assert_frame_equal(first.backtest_result.holdings, second.backtest_result.holdings)
    assert_series_equal(
        first.backtest_result.equity_curve,
        second.backtest_result.equity_curve,
    )
    assert first.backtest_result.metrics == second.backtest_result.metrics
    assert (tmp_path / "first.md").read_text(encoding="utf-8") == (
        tmp_path / "second.md"
    ).read_text(encoding="utf-8")


def test_outputs_align_to_price_axes_and_use_combine_factors(tmp_path: Path) -> None:
    result = run_synthetic_multifactor_backtest_demo(
        config=_short_config(),
        report_path=tmp_path / "report.md",
        attempt_log_path=tmp_path / "attempts.jsonl",
    )

    assert result.prices.shape == (80, 8)
    assert list(result.raw_factors) == list(FACTOR_NAMES)
    for panel in (
        *result.raw_factors.values(),
        *result.winsorized_factors.values(),
        *result.zscore_factors.values(),
        result.combined_score,
        result.backtest_result.holdings,
    ):
        assert panel.index.equals(result.prices.index)
        assert panel.columns.equals(result.prices.columns)
        assert np.isfinite(panel.to_numpy()).all()

    expected = combine_factors(result.zscore_factors, _short_config().weights)
    assert_frame_equal(result.combined_score, expected)
    weighted_sum = (
        0.50 * result.zscore_factors["synthetic_momentum"]
        + 0.30 * result.zscore_factors["synthetic_quality"]
        + 0.20 * result.zscore_factors["synthetic_reversal"]
    )
    assert_frame_equal(result.combined_score, weighted_sum)


def test_pipeline_calls_existing_normalize_and_combine_helpers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls = {"winsorize": 0, "zscore": 0, "combine": 0}
    original_winsorize = demo.cross_sectional_winsorize_factor
    original_zscore = demo.cross_sectional_zscore_factor
    original_combine = demo.combine_factors

    def count_winsorize(*args: object, **kwargs: object):
        calls["winsorize"] += 1
        return original_winsorize(*args, **kwargs)

    def count_zscore(*args: object, **kwargs: object):
        calls["zscore"] += 1
        return original_zscore(*args, **kwargs)

    def count_combine(*args: object, **kwargs: object):
        calls["combine"] += 1
        return original_combine(*args, **kwargs)

    monkeypatch.setattr(demo, "cross_sectional_winsorize_factor", count_winsorize)
    monkeypatch.setattr(demo, "cross_sectional_zscore_factor", count_zscore)
    monkeypatch.setattr(demo, "combine_factors", count_combine)

    run_synthetic_multifactor_backtest_demo(
        config=_short_config(),
        report_path=tmp_path / "report.md",
        attempt_log_path=tmp_path / "attempts.jsonl",
    )

    assert calls == {
        "winsorize": len(FACTOR_NAMES),
        "zscore": len(FACTOR_NAMES),
        "combine": 1,
    }


def test_report_records_timing_cost_and_required_claims(tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    result = run_synthetic_multifactor_backtest_demo(
        config=_short_config(),
        report_path=report_path,
        attempt_log_path=tmp_path / "attempts.jsonl",
    )

    report_text = report_path.read_text(encoding="utf-8")
    assert "Synthetic Multifactor Backtest Comparison Report" in report_text
    assert "synthetic data only" in report_text
    assert "not a profitability claim" in report_text
    assert "artificial quality, reversal, and momentum" in report_text
    assert "distinct from Demo v0 12-1 momentum" in report_text
    assert "python -m research.demo_v0" in report_text
    assert "python -m research.synthetic_multifactor_workflow_demo" in report_text
    assert "feature-only" in report_text
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
    assert "zero volume is refused" in report_text
    assert result.backtest_result.assumptions["execution_timing"] == TIMING_CONTRACT
    assert result.backtest_result.assumptions["transaction_cost_bps"] == 10.0
    assert result.backtest_result.assumptions["slippage_bps"] == 0.0
    assert result.backtest_result.assumptions["signal_lag_periods"] == 1
    assert result.backtest_result.assumptions["zero_cost_or_slippage_is_diagnostic"] is True
    assert result.backtest_result.slippage_costs.eq(0.0).all()


def test_source_stays_synthetic_only() -> None:
    source = Path(demo.__file__).read_text(encoding="utf-8")
    assert "generate_synthetic_prices" in source
    assert "generate_synthetic_factor_panels" in source
    assert "combine_factors" in source
    assert "run_long_only_backtest" in source
    assert "require_complete_price_bars" in source
    assert "require_positive_volume_bars" in source
    assert "csv_loader" not in source
    assert "local_csv" not in source
    assert "place_order" not in source
    assert "eodhd" not in source.lower()
    assert "brokerage_integration" in source


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (
            lambda panel: panel.set_index(panel.index + pd.Timedelta(days=1)),
            "index must match synthetic price dates",
        ),
        (
            lambda panel: panel.rename(columns={panel.columns[0]: "OTHER_01"}),
            "columns must match synthetic price assets",
        ),
    ],
)
def test_mismatched_factor_axes_are_refused_without_silent_repair(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutate,
    match: str,
) -> None:
    original = demo.generate_synthetic_factor_panels

    def misaligned(config):
        factors = original(config)
        name = "synthetic_quality"
        factors[name] = mutate(factors[name].copy())
        return factors

    monkeypatch.setattr(demo, "generate_synthetic_factor_panels", misaligned)
    report_path = tmp_path / "report.md"
    attempt_log_path = tmp_path / "attempts.jsonl"

    with pytest.raises(ValueError, match=match):
        run_synthetic_multifactor_backtest_demo(
            config=_short_config(),
            report_path=report_path,
            attempt_log_path=attempt_log_path,
        )

    assert not report_path.exists()
    records = load_attempt_records(attempt_log_path)
    assert [record["status"] for record in records] == ["started", "failure"]
    assert match in records[1]["error_message"]


@pytest.mark.parametrize("bad_value", [np.nan, np.inf, -np.inf])
def test_nonfinite_factors_are_refused_without_silent_repair(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    bad_value: float,
) -> None:
    original = demo.generate_synthetic_factor_panels

    def dirty(config):
        factors = original(config)
        panel = factors["synthetic_reversal"].copy()
        panel.iloc[0, 0] = bad_value
        factors["synthetic_reversal"] = panel
        return factors

    monkeypatch.setattr(demo, "generate_synthetic_factor_panels", dirty)
    report_path = tmp_path / "report.md"
    attempt_log_path = tmp_path / "attempts.jsonl"

    with pytest.raises(ValueError, match="finite"):
        run_synthetic_multifactor_backtest_demo(
            config=_short_config(),
            report_path=report_path,
            attempt_log_path=attempt_log_path,
        )

    assert not report_path.exists()
    records = load_attempt_records(attempt_log_path)
    assert [record["status"] for record in records] == ["started", "failure"]
    assert records[1]["metrics"] == {}


def test_successful_attempt_is_logged(tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    attempt_log_path = tmp_path / "attempts.jsonl"

    result = run_synthetic_multifactor_backtest_demo(
        config=_short_config(),
        report_path=report_path,
        attempt_log_path=attempt_log_path,
    )

    records = load_attempt_records(attempt_log_path)
    assert [record["status"] for record in records] == ["started", "success"]
    assert records[0]["attempt_id"] == 1
    assert records[1]["attempt_id"] == 1
    record = records[1]
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
    assert record["metrics"]["total_return"] == result.backtest_result.metrics[
        "total_return"
    ]
    assert "artificial quality, reversal, and momentum panels" in record["caveats"]
    assert record["weights"]["synthetic_momentum"] == 0.50


def test_failed_attempt_is_logged_and_previous_records_remain(tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    attempt_log_path = tmp_path / "attempts.jsonl"

    run_synthetic_multifactor_backtest_demo(
        config=_short_config(),
        report_path=report_path,
        attempt_log_path=attempt_log_path,
    )
    prior_report = report_path.read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="periods must be at least 2"):
        run_synthetic_multifactor_backtest_demo(
            config=SyntheticMultifactorBacktestConfig(periods=1),
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
    assert records[2]["attempt_id"] == 2
    assert records[3]["attempt_id"] == 2
    assert records[3]["error_type"] == "ValueError"
    assert "periods must be at least 2" in records[3]["error_message"]
    assert records[3]["metrics"] == {}
    assert report_path.read_text(encoding="utf-8") == prior_report


@pytest.mark.parametrize(
    ("interrupt", "error_type"),
    [
        (KeyboardInterrupt("multifactor backtest interrupted"), "KeyboardInterrupt"),
        (SystemExit("multifactor backtest interrupted"), "SystemExit"),
    ],
)
def test_catchable_interruption_is_logged_and_preserves_prior_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    interrupt: BaseException,
    error_type: str,
) -> None:
    report_path = tmp_path / "report.md"
    attempt_log_path = tmp_path / "attempts.jsonl"

    run_synthetic_multifactor_backtest_demo(
        config=_short_config(),
        report_path=report_path,
        attempt_log_path=attempt_log_path,
    )
    prior_report = report_path.read_text(encoding="utf-8")
    prior_records = load_attempt_records(attempt_log_path)

    def raise_interrupt(*args: object, **kwargs: object) -> None:
        raise interrupt

    monkeypatch.setattr(demo, "_run_pipeline", raise_interrupt)

    with pytest.raises(type(interrupt)):
        run_synthetic_multifactor_backtest_demo(
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
    assert records[3]["error_message"] == "multifactor backtest interrupted"
    assert report_path.read_text(encoding="utf-8") == prior_report


def test_logging_not_ready_stops_before_report_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report_path = tmp_path / "report.md"
    prior_report = "PRIOR COMPARISON REPORT\n"
    report_path.write_text(prior_report, encoding="utf-8")
    attempt_log_path = tmp_path / "attempts.jsonl"
    pipeline_calls = {"count": 0}

    def cannot_begin(*args: object, **kwargs: object) -> None:
        raise OSError("attempt log unavailable")

    def pipeline_must_not_run(*args: object, **kwargs: object) -> None:
        pipeline_calls["count"] += 1
        raise AssertionError("pipeline must not run when logging cannot begin")

    monkeypatch.setattr(demo, "append_attempt_record", cannot_begin)
    monkeypatch.setattr(demo, "_run_pipeline", pipeline_must_not_run)

    with pytest.raises(RuntimeError, match="attempt log cannot begin"):
        run_synthetic_multifactor_backtest_demo(
            config=_short_config(),
            report_path=report_path,
            attempt_log_path=attempt_log_path,
        )

    assert report_path.read_text(encoding="utf-8") == prior_report
    assert pipeline_calls["count"] == 0
    assert not attempt_log_path.exists()


def test_start_record_is_written_before_compute(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempt_log_path = tmp_path / "attempts.jsonl"
    seen_statuses: list[str] = []

    original_pipeline = demo._run_pipeline

    def pipeline_after_start(*args: object, **kwargs: object):
        seen_statuses.extend(
            record["status"] for record in load_attempt_records(attempt_log_path)
        )
        return original_pipeline(*args, **kwargs)

    monkeypatch.setattr(demo, "_run_pipeline", pipeline_after_start)

    run_synthetic_multifactor_backtest_demo(
        config=_short_config(),
        report_path=tmp_path / "report.md",
        attempt_log_path=attempt_log_path,
    )

    assert seen_statuses == ["started"]
    records = load_attempt_records(attempt_log_path)
    assert [record["status"] for record in records] == ["started", "success"]


def _dirty_prices(mutate):
    original = demo.generate_synthetic_prices

    def dirty(config):
        return mutate(original(config).copy())

    return dirty


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (
            lambda panel: panel.copy().assign(**{panel.columns[0]: np.nan}),
            "missing bars is refused",
        ),
        (
            lambda panel: panel.drop(index=panel.index[-1]),
            "source rows",
        ),
        (
            lambda panel: panel.copy().assign(**{panel.columns[0]: 0.0}),
            "strictly positive",
        ),
    ],
)
def test_multifactor_demo_refuses_missing_or_dropped_price_bars_without_silent_repair(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutate,
    match: str,
) -> None:
    monkeypatch.setattr(demo, "generate_synthetic_prices", _dirty_prices(mutate))
    report_path = tmp_path / "report.md"
    attempt_log_path = tmp_path / "attempts.jsonl"

    with pytest.raises(ValueError, match=match):
        run_synthetic_multifactor_backtest_demo(
            config=_short_config(),
            report_path=report_path,
            attempt_log_path=attempt_log_path,
        )

    assert not report_path.exists()
    records = load_attempt_records(attempt_log_path)
    assert [record["status"] for record in records] == ["started", "failure"]
    assert match in records[1]["error_message"]
    assert records[1]["metrics"] == {}


def test_multifactor_demo_refuses_zero_volume_without_silent_repair(
    tmp_path: Path,
) -> None:
    config = _short_config()
    prices = generate_synthetic_prices(demo._price_config(config))
    volume = pd.DataFrame(1.0, index=prices.index, columns=prices.columns)
    volume.iloc[5, 0] = 0.0
    report_path = tmp_path / "report.md"
    attempt_log_path = tmp_path / "attempts.jsonl"

    with pytest.raises(ValueError, match="zero volume is refused"):
        run_synthetic_multifactor_backtest_demo(
            config=config,
            report_path=report_path,
            attempt_log_path=attempt_log_path,
            volume=volume,
        )

    assert not report_path.exists()
    records = load_attempt_records(attempt_log_path)
    assert [record["status"] for record in records] == ["started", "failure"]
    assert "zero volume is refused" in records[1]["error_message"]
