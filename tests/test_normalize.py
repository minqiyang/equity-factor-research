import ast
import inspect

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

import features.normalize as normalize
from features.normalize import (
    cross_sectional_percentile_rank_factor,
    cross_sectional_rank_factor,
    cross_sectional_winsorize_factor,
    cross_sectional_zscore_factor,
)


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


def test_rank_helpers_preserve_index_and_columns() -> None:
    factor = _panel({"AAA": [3.0, 2.0], "BBB": [1.0, 4.0]}, start="2024-03-01")

    ordinal = cross_sectional_rank_factor(factor)
    percentile = cross_sectional_percentile_rank_factor(factor)

    for result in [ordinal, percentile]:
        assert result.index.equals(factor.index)
        assert result.columns.equals(factor.columns)


def test_cross_sectional_rank_factor_is_hand_calculated_with_average_ties() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0], "CCC": [2.0], "DDD": [np.nan]})

    result = cross_sectional_rank_factor(factor)

    expected = _panel({"AAA": [1.0], "BBB": [2.5], "CCC": [2.5], "DDD": [np.nan]})
    assert_frame_equal(result, expected)


def test_cross_sectional_percentile_rank_factor_uses_pandas_pct_convention() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0], "CCC": [2.0], "DDD": [np.nan]})

    result = cross_sectional_percentile_rank_factor(factor)

    expected = _panel({"AAA": [1.0 / 3.0], "BBB": [2.5 / 3.0], "CCC": [2.5 / 3.0], "DDD": [np.nan]})
    assert_frame_equal(result, expected)


def test_rank_helpers_support_ascending_false() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0], "CCC": [3.0]})

    ordinal = cross_sectional_rank_factor(factor, ascending=False)
    percentile = cross_sectional_percentile_rank_factor(factor, ascending=False)

    expected_ordinal = _panel({"AAA": [3.0], "BBB": [2.0], "CCC": [1.0]})
    expected_percentile = _panel({"AAA": [1.0], "BBB": [2.0 / 3.0], "CCC": [1.0 / 3.0]})
    assert_frame_equal(ordinal, expected_ordinal)
    assert_frame_equal(percentile, expected_percentile)


def test_rank_helpers_preserve_nan_and_exclude_missing_values() -> None:
    factor = _panel({"AAA": [10.0], "BBB": [np.nan], "CCC": [20.0], "DDD": [30.0]})

    ordinal = cross_sectional_rank_factor(factor)
    percentile = cross_sectional_percentile_rank_factor(factor)

    expected_ordinal = _panel({"AAA": [1.0], "BBB": [np.nan], "CCC": [2.0], "DDD": [3.0]})
    expected_percentile = _panel({"AAA": [1.0 / 3.0], "BBB": [np.nan], "CCC": [2.0 / 3.0], "DDD": [1.0]})
    assert_frame_equal(ordinal, expected_ordinal)
    assert_frame_equal(percentile, expected_percentile)


def test_rank_helpers_all_nan_row_remains_nan() -> None:
    factor = _panel({"AAA": [np.nan], "BBB": [np.nan], "CCC": [np.nan]})

    ordinal = cross_sectional_rank_factor(factor)
    percentile = cross_sectional_percentile_rank_factor(factor)

    assert ordinal.loc[factor.index[0]].isna().all()
    assert percentile.loc[factor.index[0]].isna().all()


def test_rank_helpers_single_valid_value_row_returns_one() -> None:
    factor = _panel({"AAA": [np.nan], "BBB": [5.0], "CCC": [np.nan]})

    ordinal = cross_sectional_rank_factor(factor)
    percentile = cross_sectional_percentile_rank_factor(factor)

    expected = _panel({"AAA": [np.nan], "BBB": [1.0], "CCC": [np.nan]})
    assert_frame_equal(ordinal, expected)
    assert_frame_equal(percentile, expected)


def test_rank_helpers_reject_non_dataframe_input() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")

    with pytest.raises(TypeError, match="DataFrame"):
        cross_sectional_rank_factor(pd.Series([1.0, 2.0, 3.0], index=dates))

    with pytest.raises(TypeError, match="DataFrame"):
        cross_sectional_percentile_rank_factor(pd.Series([1.0, 2.0, 3.0], index=dates))


def test_rank_helpers_reject_unsorted_index() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-01"])
    factor = pd.DataFrame({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]}, index=dates)

    with pytest.raises(ValueError, match="sorted"):
        cross_sectional_rank_factor(factor)

    with pytest.raises(ValueError, match="sorted"):
        cross_sectional_percentile_rank_factor(factor)


@pytest.mark.parametrize("bad_value", ["nan", "NaN", "1.0"])
def test_rank_helpers_reject_invalid_string_values(bad_value: str) -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    factor = pd.DataFrame({"AAA": [1.0, bad_value, 3.0], "BBB": [2.0, 3.0, 4.0]}, index=dates)

    with pytest.raises(TypeError, match="numeric non-boolean"):
        cross_sectional_rank_factor(factor)

    with pytest.raises(TypeError, match="numeric non-boolean"):
        cross_sectional_percentile_rank_factor(factor)


def test_cross_sectional_winsorize_factor_preserves_index_and_columns() -> None:
    factor = _panel({"AAA": [1.0, 10.0], "BBB": [2.0, 20.0], "CCC": [100.0, 30.0]})

    result = cross_sectional_winsorize_factor(factor)

    assert result.index.equals(factor.index)
    assert result.columns.equals(factor.columns)


def test_cross_sectional_winsorize_factor_is_hand_calculated() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0], "CCC": [100.0]})

    result = cross_sectional_winsorize_factor(factor, lower_quantile=0.0, upper_quantile=0.5)

    expected = _panel({"AAA": [1.0], "BBB": [2.0], "CCC": [2.0]})
    assert_frame_equal(result, expected)


def test_cross_sectional_winsorize_factor_clips_row_wise_not_globally() -> None:
    factor = _panel({"AAA": [1.0, 10.0], "BBB": [2.0, 20.0], "CCC": [100.0, 30.0]})

    result = cross_sectional_winsorize_factor(factor, lower_quantile=0.0, upper_quantile=0.5)

    expected = _panel({"AAA": [1.0, 10.0], "BBB": [2.0, 20.0], "CCC": [2.0, 20.0]})
    assert_frame_equal(result, expected)


def test_cross_sectional_winsorize_factor_preserves_nan_and_excludes_missing_values() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [np.nan], "CCC": [100.0]})

    result = cross_sectional_winsorize_factor(factor, lower_quantile=0.0, upper_quantile=0.5)

    expected = _panel({"AAA": [1.0], "BBB": [np.nan], "CCC": [50.5]})
    assert_frame_equal(result, expected)


def test_cross_sectional_winsorize_factor_all_nan_row_remains_nan() -> None:
    factor = _panel({"AAA": [np.nan], "BBB": [np.nan], "CCC": [np.nan]})

    result = cross_sectional_winsorize_factor(factor)

    assert result.loc[factor.index[0]].isna().all()


def test_cross_sectional_winsorize_factor_single_valid_value_row_is_unchanged() -> None:
    factor = _panel({"AAA": [np.nan], "BBB": [5.0], "CCC": [np.nan]})

    result = cross_sectional_winsorize_factor(factor)

    expected = _panel({"AAA": [np.nan], "BBB": [5.0], "CCC": [np.nan]})
    assert_frame_equal(result, expected)


@pytest.mark.parametrize(
    ("lower_quantile", "upper_quantile"),
    [(-0.1, 0.9), (0.1, 1.1), (0.5, 0.5), (0.9, 0.1)],
)
def test_cross_sectional_winsorize_factor_rejects_invalid_quantile_bounds(
    lower_quantile: float,
    upper_quantile: float,
) -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0], "CCC": [3.0]})

    with pytest.raises(ValueError, match="quantiles"):
        cross_sectional_winsorize_factor(
            factor,
            lower_quantile=lower_quantile,
            upper_quantile=upper_quantile,
        )


def test_cross_sectional_winsorize_factor_rejects_non_dataframe_input() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")

    with pytest.raises(TypeError, match="DataFrame"):
        cross_sectional_winsorize_factor(pd.Series([1.0, 2.0, 3.0], index=dates))


def test_cross_sectional_winsorize_factor_rejects_unsorted_index() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-01"])
    factor = pd.DataFrame({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]}, index=dates)

    with pytest.raises(ValueError, match="sorted"):
        cross_sectional_winsorize_factor(factor)


@pytest.mark.parametrize("bad_value", ["nan", "NaN", "1.0"])
def test_cross_sectional_winsorize_factor_rejects_invalid_string_values(bad_value: str) -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    factor = pd.DataFrame({"AAA": [1.0, bad_value, 3.0], "BBB": [2.0, 3.0, 4.0]}, index=dates)

    with pytest.raises(TypeError, match="numeric non-boolean"):
        cross_sectional_winsorize_factor(factor)


def test_normalize_module_has_no_backtest_or_real_data_imports() -> None:
    source = inspect.getsource(normalize)
    tree = ast.parse(source)
    forbidden_terms = [
        "backtest",
        "portfolio",
        "metrics",
        "strategies",
        "reporting",
        "requests",
        "urllib",
        "yfinance",
    ]

    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    for module_name in imported_modules:
        assert not any(term in module_name for term in forbidden_terms)
