from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import research.demo_v0 as demo_v0_module
import research.synthetic_multifactor_backtest_demo as multifactor_module
from research.demo_v0 import DEMO_V0_CONFIG, run_demo_v0
from research.synthetic_momentum_demo import (
    SyntheticDemoConfig,
    generate_synthetic_prices,
)
from research.synthetic_multifactor_backtest_demo import (
    FROZEN_CONFIG,
    SyntheticMultifactorBacktestConfig,
    run_synthetic_multifactor_backtest_demo,
)
from research.unchanging_price import report_unchanging_price_segments


def _bytes(panel: pd.DataFrame) -> bytes:
    return panel.to_csv().encode("utf-8")


def _known_flat_fixture() -> pd.DataFrame:
    dates = pd.bdate_range("2021-01-01", periods=6)
    return pd.DataFrame(
        {
            "ASSET_01": [10.0, 10.0, 10.0, 11.0, 11.0, 12.0],
            "ASSET_02": [20.0, 21.0, 22.0, 23.0, 24.0, 25.0],
            "ASSET_03": [30.0, 30.0, 31.0, 32.0, 32.0, 32.0],
        },
        index=dates,
    )


def _strictly_moving_panel() -> pd.DataFrame:
    dates = pd.bdate_range("2021-01-01", periods=5)
    return pd.DataFrame(
        {
            "ASSET_01": [10.0, 10.5, 11.0, 11.5, 12.0],
            "ASSET_02": [20.0, 19.0, 21.0, 18.0, 22.0],
        },
        index=dates,
    )


def _short_demo_config() -> SyntheticDemoConfig:
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


def _short_multifactor_config() -> SyntheticMultifactorBacktestConfig:
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


def _plant_known_flat_runs(base: pd.DataFrame) -> pd.DataFrame:
    panel = base.copy()
    panel.iloc[20:24, 0] = 1_000_000.0
    panel.iloc[30:32, 1] = 1_000_001.0
    return panel


def test_known_flat_run_is_counted_and_prices_keep_input_bytes() -> None:
    prices = _known_flat_fixture()
    before = _bytes(prices)

    report = report_unchanging_price_segments(prices)

    assert report.segment_count == 4
    assert report.assets_affected == 2
    assert report.max_run_length == 3
    assert _bytes(prices) == before


def test_strictly_moving_panel_reports_zero_segments() -> None:
    prices = _strictly_moving_panel()
    before = _bytes(prices)

    report = report_unchanging_price_segments(prices)

    assert report.segment_count == 0
    assert report.assets_affected == 0
    assert report.max_run_length == 0
    assert _bytes(prices) == before


def test_official_demo_v0_config_is_unchanged() -> None:
    assert DEMO_V0_CONFIG.seed == 20260521
    assert DEMO_V0_CONFIG.asset_count == 20
    assert DEMO_V0_CONFIG.periods == 756
    assert DEMO_V0_CONFIG.start_date == "2021-01-01"
    assert DEMO_V0_CONFIG.starting_price == 100.0
    assert DEMO_V0_CONFIG.lookback_periods == 252
    assert DEMO_V0_CONFIG.skip_periods == 21
    assert DEMO_V0_CONFIG.rebalance_frequency == "ME"
    assert DEMO_V0_CONFIG.top_n == 5
    assert DEMO_V0_CONFIG.transaction_cost_bps == 10.0
    assert DEMO_V0_CONFIG.slippage_bps == 0.0
    assert DEMO_V0_CONFIG.periods_per_year == 252
    assert FROZEN_CONFIG.periods == DEMO_V0_CONFIG.periods
    assert FROZEN_CONFIG.price_seed == DEMO_V0_CONFIG.seed
    assert FROZEN_CONFIG.asset_count == DEMO_V0_CONFIG.asset_count


@pytest.mark.parametrize(
    "shape",
    [(4, 0), (0, 3), (0, 0)],
)
def test_empty_axis_panels_report_zero_segments(shape: tuple[int, int]) -> None:
    rows, cols = shape
    index = pd.bdate_range("2021-01-01", periods=rows)
    columns = [f"ASSET_{i:02d}" for i in range(1, cols + 1)]
    prices = pd.DataFrame(
        np.empty(shape),
        index=index,
        columns=columns,
    )
    before = _bytes(prices)

    report = report_unchanging_price_segments(prices)

    assert report.segment_count == 0
    assert report.assets_affected == 0
    assert report.max_run_length == 0
    assert _bytes(prices) == before


def test_non_dataframe_prices_are_refused() -> None:
    with pytest.raises(TypeError, match="pandas DataFrame"):
        report_unchanging_price_segments([1.0, 1.0])


def test_demo_v0_reports_known_flat_run_and_keeps_every_bar(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = _short_demo_config()
    fixture = _plant_known_flat_runs(generate_synthetic_prices(config))
    before = _bytes(fixture)
    monkeypatch.setattr(
        demo_v0_module,
        "generate_synthetic_prices",
        lambda current: fixture,
    )

    result = run_demo_v0(
        config=config,
        report_path=tmp_path / "demo_v0.md",
        attempt_log_path=tmp_path / "demo_v0_attempts.jsonl",
    )
    report_text = (tmp_path / "demo_v0.md").read_text(encoding="utf-8")

    assert _bytes(fixture) == before
    assert f"Price rows: `{config.periods}`" in report_text
    assert "Unchanging-price segments: `2`" in report_text
    assert "Assets with unchanging-price segments: `2`" in report_text
    assert "Max unchanging-price run length: `4`" in report_text
    assert "every supplied bar" in report_text
    assert result.holdings.shape[1] == config.asset_count


def test_multifactor_demo_reports_known_flat_run_and_keeps_every_bar(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = _short_multifactor_config()
    price_config = replace(
        SyntheticDemoConfig(),
        seed=config.price_seed,
        asset_count=config.asset_count,
        periods=config.periods,
        start_date=config.start_date,
        starting_price=config.starting_price,
    )
    fixture = _plant_known_flat_runs(generate_synthetic_prices(price_config))
    before = _bytes(fixture)
    monkeypatch.setattr(
        multifactor_module,
        "generate_synthetic_prices",
        lambda current: fixture,
    )

    result = run_synthetic_multifactor_backtest_demo(
        config=config,
        report_path=tmp_path / "multifactor.md",
        attempt_log_path=tmp_path / "multifactor_attempts.jsonl",
    )
    report_text = (tmp_path / "multifactor.md").read_text(encoding="utf-8")

    assert _bytes(fixture) == before
    assert result.prices.shape == (config.periods, config.asset_count)
    assert f"Price rows: `{config.periods}`" in report_text
    assert "Unchanging-price segments: `2`" in report_text
    assert "Assets with unchanging-price segments: `2`" in report_text
    assert "Max unchanging-price run length: `4`" in report_text
    assert "every supplied bar" in report_text
    assert result.backtest_result.holdings.shape[1] == config.asset_count
