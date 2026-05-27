import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from features.normalize import cross_sectional_zscore_factor


def _panel(values: dict[str, list[float]], *, start: str = "2024-01-01") -> pd.DataFrame:
    first_column = next(iter(values.values()))
    dates = pd.date_range(start, periods=len(first_column), freq="D")
    return pd.DataFrame(values, index=dates)


def test_cross_sectional_zscore_factor_is_hand_calculated() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0], "CCC": [3.0]})

    result = cross_sectional_zscore_factor(factor)

    expected_std = np.sqrt(2.0 / 3.0)
    expected = _panel({"AAA": [-1.0 / expected_std], "BBB": [0.0], "CCC": [1.0 / expected_std]})
    assert_frame_equal(result, expected)


def test_cross_sectional_zscore_factor_preserves_index_and_columns() -> None:
    factor = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]}, start="2024-02-01")

    result = cross_sectional_zscore_factor(factor)

    assert result.index.equals(factor.index)
    assert result.columns.equals(factor.columns)


def test_cross_sectional_zscore_factor_preserves_nan_and_skips_missing_values() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [np.nan], "CCC": [3.0]})

    result = cross_sectional_zscore_factor(factor)

    expected = _panel({"AAA": [-1.0], "BBB": [np.nan], "CCC": [1.0]})
    assert_frame_equal(result, expected)


def test_cross_sectional_zscore_factor_zero_std_returns_nan_for_valid_entries() -> None:
    factor = _panel({"AAA": [5.0], "BBB": [5.0], "CCC": [5.0]})

    result = cross_sectional_zscore_factor(factor)

    assert result.loc[factor.index[0]].isna().all()


def test_cross_sectional_zscore_factor_all_nan_row_returns_nan() -> None:
    factor = _panel({"AAA": [np.nan], "BBB": [np.nan], "CCC": [np.nan]})

    result = cross_sectional_zscore_factor(factor)

    assert result.loc[factor.index[0]].isna().all()


def test_cross_sectional_zscore_factor_rejects_unsorted_index() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-01"])
    factor = pd.DataFrame({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]}, index=dates)

    with pytest.raises(ValueError, match="sorted"):
        cross_sectional_zscore_factor(factor)


def test_cross_sectional_zscore_factor_rejects_non_dataframe_input() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")

    with pytest.raises(TypeError, match="DataFrame"):
        cross_sectional_zscore_factor(pd.Series([1.0, 2.0, 3.0], index=dates))


@pytest.mark.parametrize("bad_value", ["nan", "NaN", "1.0"])
def test_cross_sectional_zscore_factor_rejects_invalid_string_values(bad_value: str) -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    factor = pd.DataFrame({"AAA": [1.0, bad_value, 3.0], "BBB": [2.0, 3.0, 4.0]}, index=dates)

    with pytest.raises(TypeError, match="numeric non-boolean"):
        cross_sectional_zscore_factor(factor)


def test_cross_sectional_zscore_factor_rejects_boolean_columns() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    factor = pd.DataFrame({"AAA": [True, False, True], "BBB": [1.0, 2.0, 3.0]}, index=dates)

    with pytest.raises(TypeError, match="numeric non-boolean"):
        cross_sectional_zscore_factor(factor)


def test_cross_sectional_zscore_factor_does_not_use_future_rows() -> None:
    factor = _panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0],
            "BBB": [2.0, 3.0, 4.0, 5.0],
            "CCC": [3.0, 4.0, 5.0, 6.0],
        }
    )
    changed_future = factor.copy()
    changed_future.loc[factor.index[3], :] = [10_000.0, -10_000.0, 0.0]

    signal_date = factor.index[2]
    base_result = cross_sectional_zscore_factor(factor)
    changed_result = cross_sectional_zscore_factor(changed_future)

    assert_series_equal(changed_result.loc[signal_date], base_result.loc[signal_date], check_names=False)


def test_cross_sectional_zscore_factor_produces_no_infinite_values() -> None:
    factor = _panel({"AAA": [1.0, 5.0], "BBB": [2.0, 5.0], "CCC": [3.0, 5.0]})

    result = cross_sectional_zscore_factor(factor)

    assert not np.isinf(result.to_numpy()).any()


def test_cross_sectional_zscore_factor_supports_ddof_one() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0], "CCC": [3.0]})

    result = cross_sectional_zscore_factor(factor, ddof=1)

    expected = _panel({"AAA": [-1.0], "BBB": [0.0], "CCC": [1.0]})
    assert_frame_equal(result, expected)


def test_cross_sectional_zscore_factor_ddof_equal_to_valid_count_returns_nan() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [3.0], "CCC": [np.nan]})

    result = cross_sectional_zscore_factor(factor, ddof=2)

    assert result.loc[factor.index[0]].isna().all()
