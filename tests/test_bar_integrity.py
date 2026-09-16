import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from research.bar_integrity import (
    require_complete_price_bars,
    require_positive_volume_bars,
)


def _panel() -> pd.DataFrame:
    dates = pd.bdate_range("2021-01-01", periods=4)
    return pd.DataFrame(
        [[10.0, 11.0], [10.5, 11.2], [10.7, 11.4], [11.0, 11.8]],
        index=dates,
        columns=["ASSET_01", "ASSET_02"],
    )


def test_complete_price_bars_return_a_float_copy() -> None:
    prices = _panel()
    validated = require_complete_price_bars(
        prices,
        expected_rows=4,
        expected_assets=2,
    )

    assert_frame_equal(validated, prices.astype(float))
    assert validated is not prices


def test_missing_price_bar_is_refused_without_mutating_input() -> None:
    prices = _panel()
    prices.iloc[1, 0] = np.nan
    original = prices.copy()

    with pytest.raises(ValueError, match="missing bars is refused"):
        require_complete_price_bars(prices, expected_rows=4, expected_assets=2)

    assert_frame_equal(prices, original)


@pytest.mark.parametrize(
    ("bad_value", "match"),
    [
        (0.0, "strictly positive"),
        (-1.0, "strictly positive"),
        (np.inf, "finite numeric values"),
        (-np.inf, "finite numeric values"),
    ],
)
def test_non_positive_or_infinite_price_bar_is_refused(
    bad_value: float,
    match: str,
) -> None:
    prices = _panel()
    prices.iloc[2, 1] = bad_value

    with pytest.raises(ValueError, match=match):
        require_complete_price_bars(prices, expected_rows=4, expected_assets=2)


def test_dropped_price_row_is_refused() -> None:
    prices = _panel().iloc[:-1]

    with pytest.raises(ValueError, match="keep 4 source rows"):
        require_complete_price_bars(prices, expected_rows=4, expected_assets=2)


def test_dropped_price_asset_is_refused() -> None:
    prices = _panel().drop(columns=["ASSET_02"])

    with pytest.raises(ValueError, match="keep 2 assets"):
        require_complete_price_bars(prices, expected_rows=4, expected_assets=2)


def test_positive_volume_bars_match_price_axes() -> None:
    prices = _panel()
    volume = pd.DataFrame(1.0, index=prices.index, columns=prices.columns)

    validated = require_positive_volume_bars(volume, prices=prices)
    assert_frame_equal(validated, volume)


def test_zero_volume_bar_is_refused_without_mutating_input() -> None:
    prices = _panel()
    volume = pd.DataFrame(5.0, index=prices.index, columns=prices.columns)
    volume.iloc[0, 1] = 0.0
    original = volume.copy()

    with pytest.raises(ValueError, match="zero volume is refused"):
        require_positive_volume_bars(volume, prices=prices)

    assert_frame_equal(volume, original)


def test_missing_volume_bar_is_refused() -> None:
    prices = _panel()
    volume = pd.DataFrame(5.0, index=prices.index, columns=prices.columns)
    volume.iloc[-1, 0] = np.nan

    with pytest.raises(ValueError, match="missing bars is refused"):
        require_positive_volume_bars(volume, prices=prices)


def test_misaligned_volume_axes_are_refused() -> None:
    prices = _panel()
    volume = pd.DataFrame(5.0, index=prices.index, columns=prices.columns)
    shifted = volume.set_index(volume.index + pd.Timedelta(days=1))

    with pytest.raises(ValueError, match="index must match price dates"):
        require_positive_volume_bars(shifted, prices=prices)
