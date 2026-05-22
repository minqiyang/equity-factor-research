import numpy as np
import pandas as pd
import pytest

from features.momentum import calculate_12_1_momentum


def test_small_hand_calculated_example_skips_recent_period() -> None:
    dates = pd.date_range("2024-01-31", periods=6, freq="ME")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 110.0, 120.0, 130.0, 10_000.0, 150.0],
            "BBB": [50.0, 55.0, 60.0, 70.0, 80.0, 90.0],
        },
        index=dates,
    )

    momentum = calculate_12_1_momentum(prices, lookback_periods=4, skip_periods=1)

    signal_date = dates[4]
    assert momentum.loc[signal_date, "AAA"] == pytest.approx(130.0 / 100.0 - 1.0)
    assert momentum.loc[signal_date, "BBB"] == pytest.approx(70.0 / 50.0 - 1.0)


def test_output_does_not_use_future_prices() -> None:
    dates = pd.date_range("2024-01-31", periods=8, freq="ME")
    base_prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0, 110.0, 120.0, 130.0, 140.0, 150.0]}, index=dates)
    changed_future_prices = base_prices.copy()
    changed_future_prices.loc[dates[6]:, "AAA"] = [10_000.0, 20_000.0]

    base_momentum = calculate_12_1_momentum(base_prices, lookback_periods=4, skip_periods=1)
    changed_momentum = calculate_12_1_momentum(changed_future_prices, lookback_periods=4, skip_periods=1)

    signal_date = dates[5]
    assert changed_momentum.loc[signal_date, "AAA"] == pytest.approx(base_momentum.loc[signal_date, "AAA"])


def test_most_recent_one_month_window_is_skipped() -> None:
    dates = pd.date_range("2024-01-31", periods=5, freq="ME")
    prices = pd.DataFrame({"AAA": [100.0, 100.0, 100.0, 100.0, 1_000.0]}, index=dates)

    momentum = calculate_12_1_momentum(prices, lookback_periods=4, skip_periods=1)

    assert momentum.loc[dates[4], "AAA"] == pytest.approx(0.0)
    assert prices.loc[dates[4], "AAA"] == 1_000.0


def test_wider_skipped_window_ignores_interior_prices_but_uses_boundary() -> None:
    dates = pd.date_range("2024-01-31", periods=8, freq="ME")
    prices = pd.DataFrame(
        {"AAA": [100.0, 105.0, 110.0, 130.0, 140.0, 150.0, 160.0, 170.0]},
        index=dates,
    )

    base = calculate_12_1_momentum(prices, lookback_periods=6, skip_periods=3)

    changed_interior = prices.copy()
    changed_interior.loc[dates[5], "AAA"] = 10_000.0
    interior = calculate_12_1_momentum(changed_interior, lookback_periods=6, skip_periods=3)

    changed_boundary = prices.copy()
    changed_boundary.loc[dates[3], "AAA"] = 1_000.0
    boundary = calculate_12_1_momentum(changed_boundary, lookback_periods=6, skip_periods=3)

    signal_date = dates[6]
    assert base.loc[signal_date, "AAA"] == pytest.approx(130.0 / 100.0 - 1.0)
    assert interior.loc[signal_date, "AAA"] == pytest.approx(base.loc[signal_date, "AAA"])
    assert boundary.loc[signal_date, "AAA"] == pytest.approx(1_000.0 / 100.0 - 1.0)


def test_missing_data_does_not_crash_and_returns_nan_for_missing_anchor() -> None:
    dates = pd.date_range("2024-01-31", periods=6, freq="ME")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, np.nan, 120.0, 130.0, 140.0, 150.0],
            "BBB": [50.0, 55.0, 60.0, np.nan, 80.0, 90.0],
        },
        index=dates,
    )

    momentum = calculate_12_1_momentum(prices, lookback_periods=4, skip_periods=1)

    assert np.isnan(momentum.loc[dates[5], "AAA"])
    assert np.isnan(momentum.loc[dates[4], "BBB"])
    assert momentum.loc[dates[5], "BBB"] == pytest.approx(80.0 / 55.0 - 1.0)


def test_returns_aligned_dates_and_columns() -> None:
    dates = pd.date_range("2024-01-31", periods=6, freq="ME")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 105.0, 110.0, 115.0, 120.0, 125.0],
            "BBB": [200.0, 198.0, 202.0, 205.0, 210.0, 215.0],
        },
        index=dates,
    )

    momentum = calculate_12_1_momentum(prices, lookback_periods=4, skip_periods=1)

    assert momentum.index.equals(prices.index)
    assert momentum.columns.equals(prices.columns)


def test_requires_sorted_dates_to_preserve_alignment() -> None:
    dates = pd.to_datetime(["2024-02-29", "2024-01-31", "2024-03-31"])
    prices = pd.DataFrame({"AAA": [100.0, 99.0, 101.0]}, index=dates)

    with pytest.raises(ValueError, match="sorted"):
        calculate_12_1_momentum(prices, lookback_periods=2, skip_periods=1)
