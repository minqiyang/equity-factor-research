import ast
import inspect

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

import features.diagnostics as diagnostics
from features.diagnostics import (
    factor_correlation_matrix,
    factor_information_coefficient,
    factor_rank_information_coefficient,
)


def _panel(values: dict[str, list[object]], *, start: str = "2024-01-01") -> pd.DataFrame:
    first_column = next(iter(values.values()))
    dates = pd.date_range(start, periods=len(first_column), freq="D")
    return pd.DataFrame(values, index=dates)


def test_factor_correlation_matrix_is_hand_calculated_pearson() -> None:
    factor_a = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]})
    factor_b = _panel({"AAA": [1.0, 2.0], "BBB": [1.0, 2.0]})

    result = factor_correlation_matrix({"a": factor_a, "b": factor_b})

    expected_value = pd.Series([1.0, 3.0, 2.0, 4.0]).corr(
        pd.Series([1.0, 1.0, 2.0, 2.0]),
        method="pearson",
    )
    expected = pd.DataFrame(
        [[1.0, expected_value], [expected_value, 1.0]],
        index=["a", "b"],
        columns=["a", "b"],
    )
    assert_frame_equal(result, expected)


def test_factor_correlation_matrix_is_hand_calculated_spearman() -> None:
    factor_a = _panel({"AAA": [1.0, 4.0], "BBB": [2.0, 3.0]})
    factor_b = _panel({"AAA": [10.0, 30.0], "BBB": [40.0, 20.0]})

    result = factor_correlation_matrix(
        {"a": factor_a, "b": factor_b},
        method="spearman",
    )

    expected_value = pd.Series([1.0, 2.0, 4.0, 3.0]).corr(
        pd.Series([10.0, 40.0, 30.0, 20.0]),
        method="spearman",
    )
    expected = pd.DataFrame(
        [[1.0, expected_value], [expected_value, 1.0]],
        index=["a", "b"],
        columns=["a", "b"],
    )
    assert_frame_equal(result, expected)


def test_factor_correlation_matrix_identical_factors_return_one() -> None:
    factor = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]})

    result = factor_correlation_matrix({"a": factor, "copy": factor.copy()})

    assert result.loc["a", "copy"] == pytest.approx(1.0)


def test_factor_correlation_matrix_inverse_factors_return_negative_one() -> None:
    factor = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]})
    inverse = -factor

    result = factor_correlation_matrix({"a": factor, "inverse": inverse})

    assert result.loc["a", "inverse"] == pytest.approx(-1.0)


def test_factor_correlation_matrix_preserves_factor_name_order() -> None:
    first = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]})
    second = _panel({"AAA": [4.0, 3.0], "BBB": [2.0, 1.0]})
    third = _panel({"AAA": [1.0, 3.0], "BBB": [2.0, 4.0]})

    result = factor_correlation_matrix({"first": first, "second": second, "third": third})

    expected_names = ["first", "second", "third"]
    assert list(result.index) == expected_names
    assert list(result.columns) == expected_names


def test_factor_correlation_matrix_uses_pairwise_overlap_without_filling() -> None:
    factor_a = _panel({"AAA": [1.0, np.nan, 3.0], "BBB": [4.0, 5.0, 6.0]})
    factor_b = _panel({"AAA": [1.0, 2.0, np.nan], "BBB": [4.0, 10.0, 6.0]})

    result = factor_correlation_matrix({"a": factor_a, "b": factor_b}, min_periods=3)

    left = pd.Series([1.0, 4.0, np.nan, 5.0, 3.0, 6.0])
    right = pd.Series([1.0, 4.0, 2.0, 10.0, np.nan, 6.0])
    valid = left.notna() & right.notna()
    expected_value = left[valid].corr(right[valid], method="pearson")
    assert result.loc["a", "b"] == pytest.approx(expected_value)


def test_factor_correlation_matrix_raises_for_insufficient_overlap() -> None:
    factor_a = _panel({"AAA": [1.0, np.nan], "BBB": [np.nan, np.nan]})
    factor_b = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]})

    with pytest.raises(ValueError, match="overlapping observations"):
        factor_correlation_matrix({"a": factor_a, "b": factor_b}, min_periods=2)


def test_factor_correlation_matrix_rejects_mismatched_indexes() -> None:
    factor_a = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]}, start="2024-01-01")
    factor_b = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]}, start="2024-01-02")

    with pytest.raises(ValueError, match="identical indexes"):
        factor_correlation_matrix({"a": factor_a, "b": factor_b})


def test_factor_correlation_matrix_rejects_mismatched_columns() -> None:
    factor_a = _panel({"AAA": [1.0], "BBB": [2.0]})
    factor_b = _panel({"AAA": [3.0], "CCC": [4.0]})

    with pytest.raises(ValueError, match="identical columns"):
        factor_correlation_matrix({"a": factor_a, "b": factor_b})


def test_factor_correlation_matrix_rejects_empty_factors() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        factor_correlation_matrix({})


def test_factor_correlation_matrix_rejects_non_dict_factors() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})

    with pytest.raises(TypeError, match="factors must be a dict"):
        factor_correlation_matrix(factor)  # type: ignore[arg-type]


def test_factor_correlation_matrix_rejects_non_dataframe_factor() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})

    with pytest.raises(TypeError, match="DataFrame"):
        factor_correlation_matrix({"valid": factor, "bad": [1.0, 2.0]})  # type: ignore[dict-item]


@pytest.mark.parametrize("bad_value", ["nan", "NaN", "1.0"])
def test_factor_correlation_matrix_rejects_invalid_string_values(bad_value: str) -> None:
    factor = _panel({"AAA": [1.0, bad_value], "BBB": [2.0, 3.0]})

    with pytest.raises(TypeError, match="numeric non-boolean"):
        factor_correlation_matrix({"factor": factor})


def test_factor_correlation_matrix_rejects_invalid_method() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})

    with pytest.raises(ValueError, match="method"):
        factor_correlation_matrix({"factor": factor}, method="kendall")


@pytest.mark.parametrize("bad_min_periods", [0, -1])
def test_factor_correlation_matrix_rejects_too_small_min_periods(
    bad_min_periods: int,
) -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})

    with pytest.raises(ValueError, match="at least 1"):
        factor_correlation_matrix({"factor": factor}, min_periods=bad_min_periods)


@pytest.mark.parametrize("bad_min_periods", [True, 1.5, "1"])
def test_factor_correlation_matrix_rejects_non_integer_min_periods(
    bad_min_periods: object,
) -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})

    with pytest.raises(TypeError, match="integer"):
        factor_correlation_matrix({"factor": factor}, min_periods=bad_min_periods)  # type: ignore[arg-type]


def test_factor_correlation_matrix_returns_nan_for_undefined_constant_pair() -> None:
    constant = _panel({"AAA": [1.0, 1.0], "BBB": [1.0, 1.0]})
    varying = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]})

    result = factor_correlation_matrix(
        {"constant": constant, "varying": varying},
        min_periods=4,
    )

    assert np.isnan(result.loc["constant", "varying"])


def test_factor_information_coefficient_is_hand_calculated_pearson_by_date() -> None:
    factor = _panel(
        {
            "AAA": [1.0, 1.0, 1.0],
            "BBB": [2.0, 2.0, np.nan],
            "CCC": [3.0, 3.0, 3.0],
        },
    )
    forward_returns = _panel(
        {
            "AAA": [0.01, 0.03, 0.01],
            "BBB": [0.02, 0.02, 0.04],
            "CCC": [0.03, 0.01, np.nan],
        },
    )

    result = factor_information_coefficient(factor, forward_returns)

    expected = pd.Series(
        [1.0, -1.0, np.nan],
        index=factor.index,
        name="information_coefficient",
    )
    assert_series_equal(result, expected)


def test_factor_rank_information_coefficient_is_hand_calculated_spearman() -> None:
    factor = _panel({"AAA": [1.0, 3.0], "BBB": [2.0, 2.0], "CCC": [3.0, 1.0]})
    forward_returns = _panel(
        {"AAA": [0.01, 0.30], "BBB": [0.02, 0.20], "CCC": [0.03, 0.10]},
    )

    result = factor_rank_information_coefficient(factor, forward_returns)

    expected = pd.Series(
        [1.0, 1.0],
        index=factor.index,
        name="rank_information_coefficient",
    )
    assert_series_equal(result, expected)


def test_factor_information_coefficient_uses_pairwise_overlap_without_filling() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [np.nan], "CCC": [3.0]})
    forward_returns = _panel({"AAA": [0.01], "BBB": [0.99], "CCC": [0.03]})

    result = factor_information_coefficient(factor, forward_returns, min_periods=2)

    expected = pd.Series([1.0], index=factor.index, name="information_coefficient")
    assert_series_equal(result, expected)


def test_factor_information_coefficient_preserves_dates_and_returns_nan_for_low_coverage() -> None:
    factor = _panel({"AAA": [1.0, 1.0], "BBB": [2.0, np.nan], "CCC": [3.0, np.nan]})
    forward_returns = _panel({"AAA": [0.01, 0.01], "BBB": [0.02, 0.02], "CCC": [0.03, 0.03]})

    result = factor_information_coefficient(factor, forward_returns, min_periods=3)

    expected = pd.Series(
        [1.0, np.nan],
        index=factor.index,
        name="information_coefficient",
    )
    assert_series_equal(result, expected)


def test_factor_information_coefficient_rejects_mismatched_indexes() -> None:
    factor = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]}, start="2024-01-01")
    forward_returns = _panel({"AAA": [0.01, 0.02], "BBB": [0.03, 0.04]}, start="2024-01-02")

    with pytest.raises(ValueError, match="identical indexes"):
        factor_information_coefficient(factor, forward_returns)


def test_factor_information_coefficient_rejects_mismatched_columns() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})
    forward_returns = _panel({"AAA": [0.01], "CCC": [0.02]})

    with pytest.raises(ValueError, match="identical columns"):
        factor_information_coefficient(factor, forward_returns)


@pytest.mark.parametrize("bad_value", ["nan", "NaN", "1.0"])
def test_factor_information_coefficient_rejects_invalid_string_values(
    bad_value: str,
) -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})
    forward_returns = _panel({"AAA": [0.01], "BBB": [bad_value]})

    with pytest.raises(TypeError, match="numeric non-boolean"):
        factor_information_coefficient(factor, forward_returns)


def test_factor_information_coefficient_rejects_invalid_method() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})
    forward_returns = _panel({"AAA": [0.01], "BBB": [0.02]})

    with pytest.raises(ValueError, match="method"):
        factor_information_coefficient(factor, forward_returns, method="kendall")


@pytest.mark.parametrize("bad_min_periods", [0, 1])
def test_factor_information_coefficient_rejects_too_small_min_periods(
    bad_min_periods: int,
) -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})
    forward_returns = _panel({"AAA": [0.01], "BBB": [0.02]})

    with pytest.raises(ValueError, match="at least 2"):
        factor_information_coefficient(
            factor,
            forward_returns,
            min_periods=bad_min_periods,
        )


@pytest.mark.parametrize("bad_min_periods", [True, 2.5, "2"])
def test_factor_information_coefficient_rejects_non_integer_min_periods(
    bad_min_periods: object,
) -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})
    forward_returns = _panel({"AAA": [0.01], "BBB": [0.02]})

    with pytest.raises(TypeError, match="integer"):
        factor_information_coefficient(
            factor,
            forward_returns,
            min_periods=bad_min_periods,  # type: ignore[arg-type]
        )


def test_diagnostics_module_has_no_backtest_alpha_reporting_or_real_data_imports() -> None:
    source = inspect.getsource(diagnostics)
    tree = ast.parse(source)
    forbidden_terms = [
        "backtest",
        "portfolio",
        "metrics",
        "worldquant_alphas",
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
