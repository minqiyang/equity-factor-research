import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from features.operators import (
    cross_sectional_rank,
    cross_sectional_zscore,
    delay,
    delta,
    rolling_corr,
    rolling_cov,
    rolling_max,
    rolling_mean,
    rolling_min,
    rolling_std,
    safe_divide,
    scale,
    signed_power,
    ts_rank,
    validate_panel_data,
    winsorize_cross_sectional,
)


def _panel(values: dict[str, list[float]], *, start: str = "2024-01-01") -> pd.DataFrame:
    first_column = next(iter(values.values()))
    dates = pd.date_range(start, periods=len(first_column), freq="D")
    return pd.DataFrame(values, index=dates)


def test_validate_panel_data_returns_float_copy_and_preserves_missing_values() -> None:
    data = _panel({"AAA": [1, 2, np.nan], "BBB": [4, 5, 6]})

    result = validate_panel_data(data)

    assert result.index.equals(data.index)
    assert result.columns.equals(data.columns)
    assert result.dtypes.tolist() == [np.dtype("float64"), np.dtype("float64")]
    assert np.isnan(result.loc[data.index[2], "AAA"])
    assert result is not data


def test_validate_panel_data_accepts_numeric_int_float_and_real_nan() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    data = pd.DataFrame(
        {
            "INTS": pd.Series([1, 2, 3], index=dates, dtype="int64"),
            "FLOATS": pd.Series([1.5, np.nan, 3.5], index=dates, dtype="float64"),
        },
        index=dates,
    )

    result = validate_panel_data(data)

    assert result.index.equals(data.index)
    assert result.columns.equals(data.columns)
    assert result.dtypes.tolist() == [np.dtype("float64"), np.dtype("float64")]
    assert result.loc[dates[0], "INTS"] == pytest.approx(1.0)
    assert np.isnan(result.loc[dates[1], "FLOATS"])


def test_validate_panel_data_rejects_duplicate_asset_columns_clearly() -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    data = pd.DataFrame(
        [[1.0, 2.0], [3.0, 4.0]],
        index=dates,
        columns=["AAA", "AAA"],
    )

    with pytest.raises(ValueError, match="duplicate asset columns.*AAA"):
        validate_panel_data(data, name="prices")


@pytest.mark.parametrize("infinite_value", [np.inf, -np.inf])
def test_validate_panel_data_rejects_infinite_values(infinite_value: float) -> None:
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    data = pd.DataFrame(
        {"AAA": [1.0, infinite_value], "BBB": [np.nan, 2.0]},
        index=dates,
    )

    with pytest.raises(ValueError, match="finite numeric values or NaN"):
        validate_panel_data(data, name="prices")


def test_validate_panel_data_rejects_invalid_inputs() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")

    with pytest.raises(TypeError, match="DataFrame"):
        validate_panel_data(pd.Series([1.0, 2.0, 3.0], index=dates))

    with pytest.raises(TypeError, match="DatetimeIndex"):
        validate_panel_data(pd.DataFrame({"AAA": [1.0, 2.0, 3.0]}, index=[0, 1, 2]))

    with pytest.raises(ValueError, match="duplicate"):
        validate_panel_data(pd.DataFrame({"AAA": [1.0, 2.0]}, index=[dates[0], dates[0]]))

    with pytest.raises(ValueError, match="sorted"):
        validate_panel_data(pd.DataFrame({"AAA": [1.0, 2.0]}, index=[dates[1], dates[0]]))

    with pytest.raises(ValueError, match="empty"):
        validate_panel_data(pd.DataFrame(index=dates))

    with pytest.raises(TypeError, match="numeric"):
        validate_panel_data(pd.DataFrame({"AAA": [1.0, "bad", 3.0]}, index=dates))

    with pytest.raises(TypeError, match="numeric non-boolean"):
        validate_panel_data(pd.DataFrame({"AAA": [1.0, "nan", 3.0]}, index=dates))

    with pytest.raises(TypeError, match="numeric non-boolean"):
        validate_panel_data(pd.DataFrame({"AAA": [1.0, "NaN", 3.0]}, index=dates))

    with pytest.raises(TypeError, match="numeric non-boolean"):
        validate_panel_data(pd.DataFrame({"AAA": ["1.0", "2.0", "3.0"]}, index=dates))

    with pytest.raises(TypeError, match="numeric non-boolean"):
        validate_panel_data(pd.DataFrame({"AAA": pd.Categorical([1.0, 2.0, 3.0])}, index=dates))

    with pytest.raises(TypeError, match="numeric non-boolean"):
        validate_panel_data(pd.DataFrame({"AAA": [True, False, True]}, index=dates))


def test_delay_and_delta_are_hand_calculated_and_reject_invalid_lags() -> None:
    data = _panel({"AAA": [1.0, 3.0, 6.0, 10.0], "BBB": [10.0, 9.0, 7.0, 4.0]})

    expected_delay = _panel({"AAA": [np.nan, 1.0, 3.0, 6.0], "BBB": [np.nan, 10.0, 9.0, 7.0]})
    expected_delta = _panel({"AAA": [np.nan, np.nan, 5.0, 7.0], "BBB": [np.nan, np.nan, -3.0, -5.0]})

    assert_frame_equal(delay(data, periods=1), expected_delay)
    assert_frame_equal(delta(data, periods=2), expected_delta)

    with pytest.raises(ValueError, match="at least 0"):
        delay(data, periods=-1)

    with pytest.raises(ValueError, match="at least 1"):
        delta(data, periods=0)


def test_rolling_summary_operators_use_full_trailing_windows() -> None:
    data = _panel({"AAA": [1.0, 2.0, 3.0, 4.0], "BBB": [4.0, np.nan, 8.0, 10.0]})

    expected_mean = _panel({"AAA": [np.nan, 1.5, 2.5, 3.5], "BBB": [np.nan, np.nan, np.nan, 9.0]})
    expected_std = _panel({"AAA": [np.nan, 0.5, 0.5, 0.5], "BBB": [np.nan, np.nan, np.nan, 1.0]})
    expected_min = _panel({"AAA": [np.nan, 1.0, 2.0, 3.0], "BBB": [np.nan, np.nan, np.nan, 8.0]})
    expected_max = _panel({"AAA": [np.nan, 2.0, 3.0, 4.0], "BBB": [np.nan, np.nan, np.nan, 10.0]})

    assert_frame_equal(rolling_mean(data, 2), expected_mean)
    assert_frame_equal(rolling_std(data, 2), expected_std)
    assert_frame_equal(rolling_min(data, 2), expected_min)
    assert_frame_equal(rolling_max(data, 2), expected_max)

    with pytest.raises(ValueError, match="at least 1"):
        rolling_mean(data, 0)


def test_rolling_corr_and_cov_require_matching_panels_and_full_windows() -> None:
    left = _panel({"AAA": [1.0, 2.0, 3.0, 4.0], "BBB": [1.0, 2.0, np.nan, 4.0]})
    right = _panel({"AAA": [2.0, 4.0, 6.0, 8.0], "BBB": [4.0, 3.0, 2.0, 1.0]})

    corr = rolling_corr(left, right, 3)
    cov = rolling_cov(left, right, 3)

    assert np.isnan(corr.loc[left.index[1], "AAA"])
    assert corr.loc[left.index[2], "AAA"] == pytest.approx(1.0)
    assert corr.loc[left.index[3], "AAA"] == pytest.approx(1.0)
    assert np.isnan(corr.loc[left.index[3], "BBB"])

    assert cov.loc[left.index[2], "AAA"] == pytest.approx(4.0 / 3.0)
    assert cov.loc[left.index[3], "AAA"] == pytest.approx(4.0 / 3.0)
    assert np.isnan(cov.loc[left.index[3], "BBB"])

    mismatched_columns = right.rename(columns={"BBB": "CCC"})
    with pytest.raises(ValueError, match="columns"):
        rolling_corr(left, mismatched_columns, 3)

    mismatched_index = right.copy()
    mismatched_index.index = pd.date_range("2024-02-01", periods=4, freq="D")
    with pytest.raises(ValueError, match="indexes"):
        rolling_cov(left, mismatched_index, 3)

    with pytest.raises(ValueError, match="at least 2"):
        rolling_corr(left, right, 1)


def test_cross_sectional_rank_preserves_nan_and_uses_average_ties() -> None:
    data = _panel({"AAA": [1.0], "BBB": [2.0], "CCC": [2.0], "DDD": [4.0], "EEE": [np.nan]})

    ranked = cross_sectional_rank(data)

    expected = _panel({"AAA": [0.25], "BBB": [0.625], "CCC": [0.625], "DDD": [1.0], "EEE": [np.nan]})
    assert_frame_equal(ranked, expected)


def test_cross_sectional_zscore_uses_row_statistics_and_zero_std_returns_nan() -> None:
    data = _panel(
        {
            "AAA": [1.0, 5.0, 1.0],
            "BBB": [2.0, 5.0, np.nan],
            "CCC": [3.0, 5.0, 3.0],
        }
    )

    zscores = cross_sectional_zscore(data)
    population_std = np.sqrt(2.0 / 3.0)

    assert zscores.loc[data.index[0], "AAA"] == pytest.approx(-1.0 / population_std)
    assert zscores.loc[data.index[0], "BBB"] == pytest.approx(0.0)
    assert zscores.loc[data.index[0], "CCC"] == pytest.approx(1.0 / population_std)
    assert zscores.loc[data.index[1]].isna().all()
    assert zscores.loc[data.index[2], "AAA"] == pytest.approx(-1.0)
    assert np.isnan(zscores.loc[data.index[2], "BBB"])
    assert zscores.loc[data.index[2], "CCC"] == pytest.approx(1.0)


def test_winsorize_cross_sectional_clips_row_outliers() -> None:
    data = _panel({"AAA": [1.0], "BBB": [2.0], "CCC": [100.0]})

    clipped = winsorize_cross_sectional(data, lower_quantile=0.0, upper_quantile=0.5)

    expected = _panel({"AAA": [1.0], "BBB": [2.0], "CCC": [2.0]})
    assert_frame_equal(clipped, expected)

    with pytest.raises(ValueError, match="quantiles"):
        winsorize_cross_sectional(data, lower_quantile=0.9, upper_quantile=0.1)


def test_ts_rank_uses_current_value_in_full_trailing_window_with_average_ties() -> None:
    data = _panel({"AAA": [1.0, 2.0, 2.0, 0.0], "BBB": [3.0, 1.0, 2.0, 4.0]})

    ranked = ts_rank(data, 3)

    assert np.isnan(ranked.loc[data.index[1], "AAA"])
    assert ranked.loc[data.index[2], "AAA"] == pytest.approx(2.5 / 3.0)
    assert ranked.loc[data.index[3], "AAA"] == pytest.approx(1.0 / 3.0)
    assert ranked.loc[data.index[2], "BBB"] == pytest.approx(2.0 / 3.0)
    assert ranked.loc[data.index[3], "BBB"] == pytest.approx(1.0)

    missing = _panel({"AAA": [1.0, np.nan, 2.0]})
    assert np.isnan(ts_rank(missing, 3).loc[missing.index[2], "AAA"])


def test_signed_power_preserves_sign_for_fractional_exponents() -> None:
    data = _panel({"AAA": [-4.0], "BBB": [0.0], "CCC": [9.0], "DDD": [np.nan]})

    result = signed_power(data, 0.5)

    expected = _panel({"AAA": [-2.0], "BBB": [0.0], "CCC": [3.0], "DDD": [np.nan]})
    assert_frame_equal(result, expected)

    with pytest.raises(ValueError, match="positive"):
        signed_power(data, 0.0)


def test_scale_targets_row_absolute_sum_and_handles_zero_rows() -> None:
    data = _panel({"AAA": [1.0, 0.0, 2.0], "BBB": [-3.0, 0.0, -2.0], "CCC": [np.nan, np.nan, 4.0]})

    result = scale(data, target_abs_sum=2.0)

    expected = _panel({"AAA": [0.5, np.nan, 0.5], "BBB": [-1.5, np.nan, -0.5], "CCC": [np.nan, np.nan, 1.0]})
    assert_frame_equal(result, expected)

    with pytest.raises(ValueError, match="positive"):
        scale(data, target_abs_sum=0.0)


def test_safe_divide_returns_nan_for_zero_denominators_and_missing_inputs() -> None:
    numerator = _panel({"AAA": [2.0, 0.0, np.nan, 5.0], "BBB": [6.0, 8.0, 10.0, 12.0]})
    denominator = _panel({"AAA": [1.0, 0.0, 2.0, np.nan], "BBB": [3.0, 4.0, 0.0, 6.0]})

    result = safe_divide(numerator, denominator)

    expected = _panel({"AAA": [2.0, np.nan, np.nan, np.nan], "BBB": [2.0, 2.0, np.nan, 2.0]})
    assert_frame_equal(result, expected)
    assert not np.isinf(result.to_numpy()).any()

    mismatched = denominator.rename(columns={"BBB": "CCC"})
    with pytest.raises(ValueError, match="columns"):
        safe_divide(numerator, mismatched)


def test_operators_preserve_index_and_columns() -> None:
    data = _panel({"AAA": [1.0, 2.0, 3.0, 4.0], "BBB": [4.0, 3.0, 2.0, 1.0]})
    other = _panel({"AAA": [2.0, 4.0, 6.0, 8.0], "BBB": [1.0, 2.0, 3.0, 4.0]})

    operator_results = [
        validate_panel_data(data),
        delay(data),
        delta(data),
        rolling_mean(data, 2),
        rolling_std(data, 2),
        rolling_min(data, 2),
        rolling_max(data, 2),
        rolling_corr(data, other, 2),
        rolling_cov(data, other, 2),
        cross_sectional_rank(data),
        cross_sectional_zscore(data),
        winsorize_cross_sectional(data),
        ts_rank(data, 2),
        signed_power(data, 2.0),
        scale(data),
        safe_divide(data, other),
    ]

    for result in operator_results:
        assert result.index.equals(data.index)
        assert result.columns.equals(data.columns)


@pytest.mark.parametrize(
    "operator",
    [
        lambda data: delay(data, 1),
        lambda data: delta(data, 1),
        lambda data: rolling_mean(data, 3),
        lambda data: rolling_std(data, 3),
        lambda data: rolling_min(data, 3),
        lambda data: rolling_max(data, 3),
        lambda data: ts_rank(data, 3),
    ],
)
def test_time_series_operators_do_not_use_future_rows(operator) -> None:
    data = _panel({"AAA": [1.0, 2.0, 3.0, 4.0, 5.0], "BBB": [5.0, 4.0, 3.0, 2.0, 1.0]})
    changed_future = data.copy()
    changed_future.loc[data.index[4], :] = [10_000.0, -10_000.0]

    base_result = operator(data)
    changed_result = operator(changed_future)

    signal_date = data.index[3]
    assert_series_equal(changed_result.loc[signal_date], base_result.loc[signal_date], check_names=False)


def test_rolling_pair_operators_do_not_use_future_rows() -> None:
    left = _panel({"AAA": [1.0, 2.0, 3.0, 4.0, 5.0], "BBB": [2.0, 3.0, 4.0, 5.0, 6.0]})
    right = _panel({"AAA": [2.0, 4.0, 6.0, 8.0, 10.0], "BBB": [1.0, 3.0, 5.0, 7.0, 9.0]})
    changed_future = right.copy()
    changed_future.loc[right.index[4], :] = [10_000.0, -10_000.0]

    signal_date = left.index[3]
    assert_series_equal(
        rolling_corr(left, changed_future, 3).loc[signal_date],
        rolling_corr(left, right, 3).loc[signal_date],
        check_names=False,
    )
    assert_series_equal(
        rolling_cov(left, changed_future, 3).loc[signal_date],
        rolling_cov(left, right, 3).loc[signal_date],
        check_names=False,
    )
