import numpy as np
import pandas as pd
import pytest

from features.reversal import calculate_short_term_reversal


def test_short_term_reversal_is_negative_trailing_return() -> None:
    dates = pd.date_range("2024-01-31", periods=5, freq="ME")
    prices = pd.DataFrame(
        {
            "LOSER": [100.0, 90.0, 80.0, 70.0, 60.0],
            "WINNER": [100.0, 110.0, 120.0, 130.0, 140.0],
        },
        index=dates,
    )

    reversal = calculate_short_term_reversal(prices, lookback_periods=2)

    signal_date = dates[3]
    assert reversal.loc[signal_date, "LOSER"] == pytest.approx(
        -(70.0 / 90.0 - 1.0),
    )
    assert reversal.loc[signal_date, "WINNER"] == pytest.approx(
        -(130.0 / 110.0 - 1.0),
    )
    assert reversal.loc[signal_date, "LOSER"] > reversal.loc[signal_date, "WINNER"]


def test_short_term_reversal_uses_current_and_trailing_prices_only() -> None:
    dates = pd.date_range("2024-01-31", periods=6, freq="ME")
    base_prices = pd.DataFrame(
        {"AAA": [100.0, 105.0, 110.0, 90.0, 95.0, 100.0]},
        index=dates,
    )
    changed_future_prices = base_prices.copy()
    changed_future_prices.loc[dates[5], "AAA"] = 10_000.0

    base_reversal = calculate_short_term_reversal(base_prices, lookback_periods=2)
    changed_reversal = calculate_short_term_reversal(
        changed_future_prices,
        lookback_periods=2,
    )

    signal_date = dates[4]
    assert changed_reversal.loc[signal_date, "AAA"] == pytest.approx(
        base_reversal.loc[signal_date, "AAA"],
    )


def test_short_term_reversal_preserves_dates_and_columns() -> None:
    dates = pd.date_range("2024-01-31", periods=4, freq="ME")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 101.0, 99.0, 98.0],
            "BBB": [50.0, 49.0, 51.0, 50.0],
        },
        index=dates,
    )

    reversal = calculate_short_term_reversal(prices, lookback_periods=1)

    assert reversal.index.equals(prices.index)
    assert reversal.columns.equals(prices.columns)


def test_short_term_reversal_does_not_fill_missing_values() -> None:
    dates = pd.date_range("2024-01-31", periods=5, freq="ME")
    prices = pd.DataFrame(
        {
            "AAA": [100.0, np.nan, 90.0, 95.0, 96.0],
            "BBB": [50.0, 48.0, 47.0, 46.0, np.nan],
        },
        index=dates,
    )

    reversal = calculate_short_term_reversal(prices, lookback_periods=2)

    assert reversal.loc[dates[2], "AAA"] == pytest.approx(-(90.0 / 100.0 - 1.0))
    assert np.isnan(reversal.loc[dates[3], "AAA"])
    assert reversal.loc[dates[4], "AAA"] == pytest.approx(-(96.0 / 90.0 - 1.0))
    assert np.isnan(reversal.loc[dates[4], "BBB"])


def test_short_term_reversal_returns_nan_for_non_positive_price_anchors() -> None:
    dates = pd.date_range("2024-01-31", periods=4, freq="ME")
    prices = pd.DataFrame(
        {
            "ZERO_CURRENT": [100.0, 101.0, 0.0, 103.0],
            "NEGATIVE_TRAILING": [100.0, -1.0, 110.0, 120.0],
        },
        index=dates,
    )

    reversal = calculate_short_term_reversal(prices, lookback_periods=1)

    assert np.isnan(reversal.loc[dates[2], "ZERO_CURRENT"])
    assert np.isnan(reversal.loc[dates[2], "NEGATIVE_TRAILING"])


def test_short_term_reversal_requires_sorted_dates() -> None:
    dates = pd.to_datetime(["2024-02-29", "2024-01-31", "2024-03-31"])
    prices = pd.DataFrame({"AAA": [100.0, 99.0, 101.0]}, index=dates)

    with pytest.raises(ValueError, match="sorted"):
        calculate_short_term_reversal(prices, lookback_periods=1)


def test_short_term_reversal_rejects_duplicate_dates() -> None:
    dates = pd.to_datetime(["2024-01-31", "2024-01-31", "2024-02-29"])
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)

    with pytest.raises(ValueError, match="duplicate"):
        calculate_short_term_reversal(prices, lookback_periods=1)


@pytest.mark.parametrize("bad_lookback", [0, -1])
def test_short_term_reversal_rejects_too_small_lookback(bad_lookback: int) -> None:
    dates = pd.date_range("2024-01-31", periods=3, freq="ME")
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)

    with pytest.raises(ValueError, match="at least 1"):
        calculate_short_term_reversal(prices, lookback_periods=bad_lookback)


@pytest.mark.parametrize("bad_lookback", [True, 1.5, "1"])
def test_short_term_reversal_rejects_non_integer_lookback(
    bad_lookback: object,
) -> None:
    dates = pd.date_range("2024-01-31", periods=3, freq="ME")
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)

    with pytest.raises(TypeError, match="integer"):
        calculate_short_term_reversal(
            prices,
            lookback_periods=bad_lookback,  # type: ignore[arg-type]
        )


def test_short_term_reversal_rejects_non_numeric_columns() -> None:
    dates = pd.date_range("2024-01-31", periods=3, freq="ME")
    prices = pd.DataFrame({"AAA": [100.0, "101.0", 102.0]}, index=dates)

    with pytest.raises(TypeError, match="numeric"):
        calculate_short_term_reversal(prices, lookback_periods=1)
