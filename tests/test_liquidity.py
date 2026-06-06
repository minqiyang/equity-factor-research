import ast
import inspect

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import features.liquidity as liquidity
from features.liquidity import (
    average_daily_volume_eligibility,
    average_dollar_volume_eligibility,
    rolling_average_daily_volume,
    rolling_average_dollar_volume,
)


def _panel(values: dict[str, list[object]], *, start: str = "2024-01-01") -> pd.DataFrame:
    first_column = next(iter(values.values()))
    dates = pd.date_range(start, periods=len(first_column), freq="D")
    return pd.DataFrame(values, index=dates)


def test_rolling_average_daily_volume_is_hand_calculated() -> None:
    volume = _panel({"AAA": [100.0, 200.0, 300.0, 400.0]})

    result = rolling_average_daily_volume(volume, window=2)

    expected = _panel({"AAA": [np.nan, 150.0, 250.0, 350.0]})
    assert_frame_equal(result, expected)


def test_rolling_average_dollar_volume_is_hand_calculated() -> None:
    price = _panel({"AAA": [10.0, 11.0, 12.0]})
    volume = _panel({"AAA": [100.0, 200.0, 300.0]})

    result = rolling_average_dollar_volume(price, volume, window=2)

    expected = _panel({"AAA": [np.nan, 1600.0, 2900.0]})
    assert_frame_equal(result, expected)


def test_average_daily_volume_eligibility_lags_observation_dates() -> None:
    volume = _panel(
        {
            "AAA": [100.0, 200.0, 300.0, 100.0],
            "BBB": [100.0, 100.0, 100.0, 100.0],
        },
    )

    result = average_daily_volume_eligibility(
        volume,
        window=2,
        min_average_volume=150.0,
    )

    expected = pd.DataFrame(
        {
            "AAA": [False, False, True, True],
            "BBB": [False, False, False, False],
        },
        index=volume.index,
    )
    assert_frame_equal(result, expected)


def test_average_dollar_volume_eligibility_lags_observation_dates() -> None:
    price = _panel({"AAA": [10.0, 10.0, 10.0, 10.0]})
    volume = _panel({"AAA": [100.0, 200.0, 300.0, 100.0]})

    result = average_dollar_volume_eligibility(
        price,
        volume,
        window=2,
        min_average_dollar_volume=2000.0,
    )

    expected = pd.DataFrame(
        {"AAA": [False, False, False, True]},
        index=volume.index,
    )
    assert_frame_equal(result, expected)


def test_average_daily_volume_eligibility_treats_warmup_as_ineligible() -> None:
    volume = _panel({"AAA": [300.0, 300.0, 300.0]})

    result = average_daily_volume_eligibility(
        volume,
        window=3,
        min_average_volume=100.0,
    )

    expected = pd.DataFrame({"AAA": [False, False, False]}, index=volume.index)
    assert_frame_equal(result, expected)


def test_average_daily_volume_eligibility_does_not_fill_missing_values() -> None:
    volume = _panel({"AAA": [100.0, np.nan, 300.0, 300.0, 300.0]})

    result = average_daily_volume_eligibility(
        volume,
        window=2,
        min_average_volume=250.0,
    )

    expected = pd.DataFrame(
        {"AAA": [False, False, False, False, True]},
        index=volume.index,
    )
    assert_frame_equal(result, expected)


def test_average_daily_volume_eligibility_excludes_zero_volume_window_by_default() -> None:
    volume = _panel({"AAA": [200.0, 0.0, 400.0, 400.0, 400.0]})

    result = average_daily_volume_eligibility(
        volume,
        window=2,
        min_average_volume=150.0,
    )

    expected = pd.DataFrame(
        {"AAA": [False, False, False, False, True]},
        index=volume.index,
    )
    assert_frame_equal(result, expected)


def test_zero_volume_window_policy_can_be_made_explicit() -> None:
    volume = _panel({"AAA": [200.0, 0.0, 400.0, 400.0]})

    result = average_daily_volume_eligibility(
        volume,
        window=2,
        min_average_volume=150.0,
        require_positive_volume_window=False,
    )

    expected = pd.DataFrame(
        {"AAA": [False, False, False, True]},
        index=volume.index,
    )
    assert_frame_equal(result, expected)


def test_average_daily_volume_eligibility_uses_configurable_positive_lag() -> None:
    volume = _panel({"AAA": [300.0, 300.0, 300.0, 300.0]})

    result = average_daily_volume_eligibility(
        volume,
        window=2,
        min_average_volume=100.0,
        eligibility_lag=2,
    )

    expected = pd.DataFrame(
        {"AAA": [False, False, False, True]},
        index=volume.index,
    )
    assert_frame_equal(result, expected)


def test_liquidity_helpers_reject_mismatched_price_and_volume_panels() -> None:
    price = _panel({"AAA": [10.0, 10.0]})
    volume = _panel({"BBB": [100.0, 100.0]})

    with pytest.raises(ValueError, match="identical columns"):
        rolling_average_dollar_volume(price, volume, window=2)


def test_liquidity_helpers_reject_negative_volume() -> None:
    volume = _panel({"AAA": [100.0, -1.0]})

    with pytest.raises(ValueError, match="non-negative"):
        rolling_average_daily_volume(volume, window=2)


def test_liquidity_helpers_reject_non_positive_price() -> None:
    price = _panel({"AAA": [10.0, 0.0]})
    volume = _panel({"AAA": [100.0, 100.0]})

    with pytest.raises(ValueError, match="positive"):
        rolling_average_dollar_volume(price, volume, window=2)


@pytest.mark.parametrize("bad_value", ["100", True])
def test_liquidity_helpers_reject_non_numeric_inputs(bad_value: object) -> None:
    volume = _panel({"AAA": [100.0, bad_value]})

    with pytest.raises(TypeError, match="numeric non-boolean"):
        rolling_average_daily_volume(volume, window=2)


@pytest.mark.parametrize("bad_window", [0, -1])
def test_liquidity_helpers_reject_too_small_window(bad_window: int) -> None:
    volume = _panel({"AAA": [100.0, 200.0]})

    with pytest.raises(ValueError, match="at least 1"):
        rolling_average_daily_volume(volume, window=bad_window)


@pytest.mark.parametrize("bad_window", [True, 1.5, "2"])
def test_liquidity_helpers_reject_non_integer_window(bad_window: object) -> None:
    volume = _panel({"AAA": [100.0, 200.0]})

    with pytest.raises(TypeError, match="integer"):
        rolling_average_daily_volume(volume, window=bad_window)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_lag", [0, -1])
def test_liquidity_helpers_reject_too_small_lag(bad_lag: int) -> None:
    volume = _panel({"AAA": [100.0, 200.0]})

    with pytest.raises(ValueError, match="at least 1"):
        average_daily_volume_eligibility(
            volume,
            window=2,
            min_average_volume=100.0,
            eligibility_lag=bad_lag,
        )


@pytest.mark.parametrize("bad_lag", [True, 1.5, "1"])
def test_liquidity_helpers_reject_non_integer_lag(bad_lag: object) -> None:
    volume = _panel({"AAA": [100.0, 200.0]})

    with pytest.raises(TypeError, match="integer"):
        average_daily_volume_eligibility(
            volume,
            window=2,
            min_average_volume=100.0,
            eligibility_lag=bad_lag,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("bad_threshold", [0.0, -1.0, np.inf])
def test_liquidity_helpers_reject_non_positive_or_infinite_threshold(
    bad_threshold: float,
) -> None:
    volume = _panel({"AAA": [100.0, 200.0]})

    with pytest.raises(ValueError, match="positive finite"):
        average_daily_volume_eligibility(
            volume,
            window=2,
            min_average_volume=bad_threshold,
        )


@pytest.mark.parametrize("bad_threshold", [True, "100"])
def test_liquidity_helpers_reject_non_numeric_threshold(bad_threshold: object) -> None:
    volume = _panel({"AAA": [100.0, 200.0]})

    with pytest.raises(TypeError, match="numeric"):
        average_daily_volume_eligibility(
            volume,
            window=2,
            min_average_volume=bad_threshold,  # type: ignore[arg-type]
        )


def test_liquidity_module_has_no_data_trading_or_backtest_imports() -> None:
    source = inspect.getsource(liquidity)
    tree = ast.parse(source)
    forbidden_terms = {
        "backtest",
        "broker",
        "requests",
        "urllib",
        "yfinance",
        "alpaca",
        "ccxt",
        "reporting",
        "strategies",
    }
    imported_modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    for module_name in imported_modules:
        assert not any(term in module_name.lower() for term in forbidden_terms)
