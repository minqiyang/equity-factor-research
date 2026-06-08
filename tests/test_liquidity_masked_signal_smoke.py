import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from features.liquidity import (
    apply_universe_mask_to_signals,
    average_daily_volume_eligibility,
    average_dollar_volume_eligibility,
    construct_liquidity_universe,
)


def _synthetic_panel(values: dict[str, list[float]]) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=len(next(iter(values.values()))), freq="D")
    return pd.DataFrame(values, index=dates)


def test_synthetic_liquidity_universe_masks_raw_signals_without_backtest() -> None:
    price = _synthetic_panel(
        {
            "AAA": [10.0, 10.0, 10.0, 10.0, 10.0],
            "BBB": [5.0, 5.0, 5.0, 5.0, 5.0],
            "CCC": [20.0, 20.0, 20.0, 20.0, 20.0],
        },
    )
    volume = _synthetic_panel(
        {
            "AAA": [100.0, 100.0, 100.0, 100.0, 100.0],
            "BBB": [10.0, 10.0, 10.0, 10.0, 10.0],
            "CCC": [100.0, 100.0, 0.0, 100.0, 100.0],
        },
    )
    raw_signals = _synthetic_panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0, 5.0],
            "BBB": [10.0, 11.0, 12.0, 13.0, 14.0],
            "CCC": [7.0, 8.0, np.nan, 9.0, 10.0],
        },
    )

    adv_eligible = average_daily_volume_eligibility(
        volume,
        window=2,
        min_average_volume=50.0,
    )
    dollar_eligible = average_dollar_volume_eligibility(
        price,
        volume,
        window=2,
        min_average_dollar_volume=1000.0,
    )
    universe = construct_liquidity_universe(
        adv_eligible & dollar_eligible,
        min_assets_per_date=1,
        name="synthetic_smoke_universe",
    )
    masked = apply_universe_mask_to_signals(
        raw_signals,
        universe.universe_mask,
        name="synthetic_smoke_masked_signals",
    )

    expected_universe = pd.DataFrame(
        {
            "AAA": [False, False, True, True, True],
            "BBB": [False, False, False, False, False],
            "CCC": [False, False, True, False, False],
        },
        index=raw_signals.index,
    )
    expected_signals = pd.DataFrame(
        {
            "AAA": [np.nan, np.nan, 3.0, 4.0, 5.0],
            "BBB": [np.nan, np.nan, np.nan, np.nan, np.nan],
            "CCC": [np.nan, np.nan, np.nan, np.nan, np.nan],
        },
        index=raw_signals.index,
    )
    expected_summary = pd.DataFrame(
        {
            "raw_valid_signal_count": [3, 3, 2, 3, 3],
            "universe_eligible_count": [0, 0, 2, 1, 1],
            "valid_masked_signal_count": [0, 0, 1, 1, 1],
            "excluded_by_universe_count": [3, 3, 1, 2, 2],
            "missing_signal_count": [0, 0, 1, 0, 0],
            "low_coverage": [True, True, False, False, False],
        },
        index=raw_signals.index,
    )

    assert_frame_equal(universe.universe_mask, expected_universe)
    assert_frame_equal(masked.signals, expected_signals)
    assert_frame_equal(masked.summary, expected_summary)
    assert masked.caveats == universe.caveats
    assert masked.parameters["name"] == "synthetic_smoke_masked_signals"
    assert universe.parameters["name"] == "synthetic_smoke_universe"


def test_future_liquidity_change_does_not_change_current_masked_signals() -> None:
    price = _synthetic_panel(
        {
            "AAA": [10.0, 10.0, 10.0, 10.0],
            "BBB": [20.0, 20.0, 20.0, 20.0],
        },
    )
    volume = _synthetic_panel(
        {
            "AAA": [100.0, 100.0, 100.0, 100.0],
            "BBB": [10.0, 10.0, 10.0, 10.0],
        },
    )
    changed_future_volume = volume.copy()
    changed_future_volume.loc[changed_future_volume.index[-1], "BBB"] = 10_000.0
    raw_signals = _synthetic_panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0],
            "BBB": [5.0, 6.0, 7.0, 8.0],
        },
    )

    def masked_from(volume_panel: pd.DataFrame) -> pd.DataFrame:
        eligible = average_dollar_volume_eligibility(
            price,
            volume_panel,
            window=2,
            min_average_dollar_volume=1000.0,
        )
        universe = construct_liquidity_universe(eligible)
        return apply_universe_mask_to_signals(raw_signals, universe.universe_mask).signals

    baseline = masked_from(volume)
    changed = masked_from(changed_future_volume)

    assert_frame_equal(baseline.iloc[:3], changed.iloc[:3])
    assert pd.isna(baseline.loc[baseline.index[2], "BBB"])
