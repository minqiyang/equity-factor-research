import ast
import inspect

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import features.combine as combine
from features.combine import combine_factors


def _panel(values: dict[str, list[object]], *, start: str = "2024-01-01") -> pd.DataFrame:
    first_column = next(iter(values.values()))
    dates = pd.date_range(start, periods=len(first_column), freq="D")
    return pd.DataFrame(values, index=dates)


def test_combine_factors_is_hand_calculated_weighted_sum() -> None:
    momentum = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]})
    value = _panel({"AAA": [10.0, 20.0], "BBB": [30.0, 40.0]})

    result = combine_factors(
        {"momentum": momentum, "value": value},
        {"momentum": 0.25, "value": 0.75},
    )

    expected = _panel({"AAA": [7.75, 15.5], "BBB": [23.25, 31.0]})
    assert_frame_equal(result, expected)


def test_combine_factors_preserves_index_and_columns() -> None:
    factor_a = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]}, start="2024-02-01")
    factor_b = _panel({"AAA": [5.0, 6.0], "BBB": [7.0, 8.0]}, start="2024-02-01")

    result = combine_factors({"a": factor_a, "b": factor_b}, {"a": 1.0, "b": -0.5})

    assert result.index.equals(factor_a.index)
    assert result.columns.equals(factor_a.columns)


def test_combine_factors_supports_three_factor_combination() -> None:
    factor_a = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]})
    factor_b = _panel({"AAA": [10.0, 20.0], "BBB": [30.0, 40.0]})
    factor_c = _panel({"AAA": [-1.0, 1.0], "BBB": [2.0, -2.0]})

    result = combine_factors(
        {"a": factor_a, "b": factor_b, "c": factor_c},
        {"a": 0.5, "b": 0.25, "c": -1.0},
    )

    expected = _panel({"AAA": [4.0, 5.0], "BBB": [7.0, 14.0]})
    assert_frame_equal(result, expected)


def test_combine_factors_rejects_non_dict_factors() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})

    with pytest.raises(TypeError, match="factors must be a dict"):
        combine_factors(factor, {"factor": 1.0})  # type: ignore[arg-type]


def test_combine_factors_rejects_empty_factors() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        combine_factors({}, {})


def test_combine_factors_rejects_non_dict_weights() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})

    with pytest.raises(TypeError, match="weights must be a dict"):
        combine_factors({"factor": factor}, [1.0])  # type: ignore[arg-type]


def test_combine_factors_rejects_missing_weight_names() -> None:
    factor_a = _panel({"AAA": [1.0], "BBB": [2.0]})
    factor_b = _panel({"AAA": [3.0], "BBB": [4.0]})

    with pytest.raises(ValueError, match="exactly match"):
        combine_factors({"a": factor_a, "b": factor_b}, {"a": 1.0})


def test_combine_factors_rejects_extra_weight_names() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})

    with pytest.raises(ValueError, match="exactly match"):
        combine_factors({"factor": factor}, {"factor": 1.0, "extra": 0.5})


def test_combine_factors_rejects_mismatched_indexes() -> None:
    factor_a = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]}, start="2024-01-01")
    factor_b = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]}, start="2024-01-02")

    with pytest.raises(ValueError, match="identical indexes"):
        combine_factors({"a": factor_a, "b": factor_b}, {"a": 1.0, "b": 1.0})


def test_combine_factors_rejects_mismatched_columns() -> None:
    factor_a = _panel({"AAA": [1.0], "BBB": [2.0]})
    factor_b = _panel({"AAA": [3.0], "CCC": [4.0]})

    with pytest.raises(ValueError, match="identical columns"):
        combine_factors({"a": factor_a, "b": factor_b}, {"a": 1.0, "b": 1.0})


def test_combine_factors_rejects_non_dataframe_factor_value() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})

    with pytest.raises(TypeError, match="DataFrame"):
        combine_factors({"valid": factor, "bad": [1.0, 2.0]}, {"valid": 1.0, "bad": 1.0})  # type: ignore[dict-item]


@pytest.mark.parametrize("bad_value", ["nan", "NaN", "1.0"])
def test_combine_factors_rejects_invalid_string_factor_values(bad_value: str) -> None:
    factor = _panel({"AAA": [1.0, bad_value], "BBB": [2.0, 3.0]})

    with pytest.raises(TypeError, match="numeric non-boolean"):
        combine_factors({"factor": factor}, {"factor": 1.0})


def test_combine_factors_rejects_boolean_factor_columns() -> None:
    factor = _panel({"AAA": [True, False], "BBB": [1.0, 2.0]})

    with pytest.raises(TypeError, match="numeric non-boolean"):
        combine_factors({"factor": factor}, {"factor": 1.0})


def test_combine_factors_rejects_nan_factor_values() -> None:
    factor = _panel({"AAA": [1.0, np.nan], "BBB": [2.0, 3.0]})

    with pytest.raises(ValueError, match="NaN"):
        combine_factors({"factor": factor}, {"factor": 1.0})


def test_combine_factors_rejects_nan_even_for_zero_weight_factor() -> None:
    valid = _panel({"AAA": [1.0], "BBB": [2.0]})
    missing = _panel({"AAA": [np.nan], "BBB": [3.0]})

    with pytest.raises(ValueError, match="NaN"):
        combine_factors({"valid": valid, "missing": missing}, {"valid": 1.0, "missing": 0.0})


def test_combine_factors_rejects_all_zero_weights() -> None:
    factor_a = _panel({"AAA": [1.0], "BBB": [2.0]})
    factor_b = _panel({"AAA": [3.0], "BBB": [4.0]})

    with pytest.raises(ValueError, match="nonzero"):
        combine_factors({"a": factor_a, "b": factor_b}, {"a": 0.0, "b": 0.0})


@pytest.mark.parametrize("bad_weight", [np.nan, np.inf, -np.inf])
def test_combine_factors_rejects_non_finite_weights(bad_weight: float) -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})

    with pytest.raises(ValueError, match="finite"):
        combine_factors({"factor": factor}, {"factor": bad_weight})


@pytest.mark.parametrize("bad_weight", [True, "1.0"])
def test_combine_factors_rejects_non_numeric_or_boolean_weights(bad_weight: object) -> None:
    factor = _panel({"AAA": [1.0], "BBB": [2.0]})

    with pytest.raises(TypeError, match="numeric and non-boolean"):
        combine_factors({"factor": factor}, {"factor": bad_weight})  # type: ignore[dict-item]


def test_combine_factors_allows_zero_weight_factor_with_valid_aligned_data() -> None:
    selected = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]})
    unselected = _panel({"AAA": [100.0, 200.0], "BBB": [300.0, 400.0]})

    result = combine_factors(
        {"selected": selected, "unselected": unselected},
        {"selected": 1.0, "unselected": 0.0},
    )

    assert_frame_equal(result, selected)


def test_combine_module_has_no_backtest_alpha_reporting_or_real_data_imports() -> None:
    source = inspect.getsource(combine)
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
