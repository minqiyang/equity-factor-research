import numpy as np
import pandas as pd
import pytest

from features.volatility import calculate_realized_volatility


def test_realized_volatility_matches_hand_calculated_simple_returns() -> None:
    dates = pd.date_range("2024-01-31", periods=5, freq="ME")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 110.0, 99.0, 118.8, 118.8],
            "BBB": [50.0, 55.0, 60.5, 66.55, 73.205],
        },
        index=dates,
    )

    volatility = calculate_realized_volatility(prices, window_periods=3)

    aaa_returns = pd.Series([0.10, -0.10, 0.20])
    signal_date = dates[3]
    assert volatility.loc[signal_date, "AAA"] == pytest.approx(
        float(aaa_returns.std(ddof=0)),
    )
    assert volatility.loc[signal_date, "BBB"] == pytest.approx(0.0)


def test_realized_volatility_uses_current_and_historical_prices_only() -> None:
    dates = pd.date_range("2024-01-31", periods=6, freq="ME")
    base_prices = pd.DataFrame(
        {"AAA": [100.0, 105.0, 102.0, 108.0, 111.0, 115.0]},
        index=dates,
    )
    changed_future_prices = base_prices.copy()
    changed_future_prices.loc[dates[5], "AAA"] = 10_000.0

    base_volatility = calculate_realized_volatility(base_prices, window_periods=3)
    changed_volatility = calculate_realized_volatility(
        changed_future_prices,
        window_periods=3,
    )

    signal_date = dates[4]
    assert changed_volatility.loc[signal_date, "AAA"] == pytest.approx(
        base_volatility.loc[signal_date, "AAA"],
    )


def test_realized_volatility_preserves_dates_and_columns() -> None:
    dates = pd.date_range("2024-01-31", periods=4, freq="ME")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 101.0, 103.0, 102.0],
            "BBB": [50.0, 49.0, 51.0, 50.0],
        },
        index=dates,
    )

    volatility = calculate_realized_volatility(prices, window_periods=2)

    assert volatility.index.equals(prices.index)
    assert volatility.columns.equals(prices.columns)


def test_realized_volatility_requires_full_return_window() -> None:
    dates = pd.date_range("2024-01-31", periods=4, freq="ME")
    prices = pd.DataFrame({"AAA": [100.0, 110.0, 121.0, 133.1]}, index=dates)

    volatility = calculate_realized_volatility(prices, window_periods=3)

    assert np.isnan(volatility.loc[dates[2], "AAA"])
    assert volatility.loc[dates[3], "AAA"] == pytest.approx(0.0)


def test_realized_volatility_does_not_fill_missing_prices() -> None:
    dates = pd.date_range("2024-01-31", periods=6, freq="ME")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 105.0, np.nan, 110.0, 115.0, 120.0],
            "BBB": [50.0, 55.0, 60.5, 66.55, 73.205, 80.5255],
        },
        index=dates,
    )

    volatility = calculate_realized_volatility(prices, window_periods=3)

    assert np.isnan(volatility.loc[dates[4], "AAA"])
    assert np.isnan(volatility.loc[dates[5], "AAA"])
    assert volatility.loc[dates[3], "BBB"] == pytest.approx(0.0)


def test_realized_volatility_returns_nan_for_non_positive_price_anchors() -> None:
    dates = pd.date_range("2024-01-31", periods=5, freq="ME")
    prices = pd.DataFrame(
        {
            "ZERO_CURRENT": [100.0, 105.0, 0.0, 110.0, 115.0],
            "NEGATIVE_PREVIOUS": [100.0, -1.0, 105.0, 110.0, 115.0],
        },
        index=dates,
    )

    volatility = calculate_realized_volatility(prices, window_periods=2)

    assert np.isnan(volatility.loc[dates[2], "ZERO_CURRENT"])
    assert np.isnan(volatility.loc[dates[3], "ZERO_CURRENT"])
    assert np.isnan(volatility.loc[dates[2], "NEGATIVE_PREVIOUS"])


def test_realized_volatility_supports_sample_ddof() -> None:
    dates = pd.date_range("2024-01-31", periods=4, freq="ME")
    prices = pd.DataFrame({"AAA": [100.0, 110.0, 99.0, 118.8]}, index=dates)

    volatility = calculate_realized_volatility(prices, window_periods=3, ddof=1)

    returns = pd.Series([0.10, -0.10, 0.20])
    assert volatility.loc[dates[3], "AAA"] == pytest.approx(
        float(returns.std(ddof=1)),
    )


def test_realized_volatility_requires_sorted_dates() -> None:
    dates = pd.to_datetime(["2024-02-29", "2024-01-31", "2024-03-31"])
    prices = pd.DataFrame({"AAA": [100.0, 99.0, 101.0]}, index=dates)

    with pytest.raises(ValueError, match="sorted"):
        calculate_realized_volatility(prices, window_periods=2)


def test_realized_volatility_rejects_duplicate_dates() -> None:
    dates = pd.to_datetime(["2024-01-31", "2024-01-31", "2024-02-29"])
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)

    with pytest.raises(ValueError, match="duplicate"):
        calculate_realized_volatility(prices, window_periods=2)


@pytest.mark.parametrize("bad_window", [0, -1])
def test_realized_volatility_rejects_too_small_window(bad_window: int) -> None:
    dates = pd.date_range("2024-01-31", periods=3, freq="ME")
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)

    with pytest.raises(ValueError, match="at least 1"):
        calculate_realized_volatility(prices, window_periods=bad_window)


@pytest.mark.parametrize("bad_window", [True, 1.5, "1"])
def test_realized_volatility_rejects_non_integer_window(
    bad_window: object,
) -> None:
    dates = pd.date_range("2024-01-31", periods=3, freq="ME")
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)

    with pytest.raises(TypeError, match="integer"):
        calculate_realized_volatility(
            prices,
            window_periods=bad_window,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("bad_ddof", [True, 1.5, "1"])
def test_realized_volatility_rejects_non_integer_ddof(bad_ddof: object) -> None:
    dates = pd.date_range("2024-01-31", periods=3, freq="ME")
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)

    with pytest.raises(TypeError, match="integer"):
        calculate_realized_volatility(
            prices,
            window_periods=2,
            ddof=bad_ddof,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("bad_ddof", [-1, 2])
def test_realized_volatility_rejects_invalid_ddof(bad_ddof: int) -> None:
    dates = pd.date_range("2024-01-31", periods=3, freq="ME")
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)

    with pytest.raises(ValueError):
        calculate_realized_volatility(prices, window_periods=2, ddof=bad_ddof)


def test_realized_volatility_rejects_non_numeric_columns() -> None:
    dates = pd.date_range("2024-01-31", periods=3, freq="ME")
    prices = pd.DataFrame({"AAA": [100.0, "101.0", 102.0]}, index=dates)

    with pytest.raises(TypeError, match="numeric"):
        calculate_realized_volatility(prices, window_periods=2)
