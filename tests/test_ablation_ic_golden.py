"""Retained baseline stress oracle: exact Pearson, bounded Rank IC only."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from features.diagnostics import factor_information_coefficient


GOLDEN_PATH = Path(__file__).parent / "fixtures/ablation/ic_baseline.json"
GOLDEN = json.loads(GOLDEN_PATH.read_text())


def _is_finite_binary64_dyadic(value):
    if type(value) is not float or value != value:
        return False
    _numerator, denominator = value.as_integer_ratio()
    return denominator > 0 and (denominator & (denominator - 1)) == 0


def _walk_numeric(node):
    if isinstance(node, list):
        for item in node:
            yield from _walk_numeric(item)
        return
    yield node


@pytest.mark.parametrize("case", GOLDEN["cases"], ids=lambda case: case["id"])
def test_baseline_ic_stress(case):
    dates = pd.date_range("2020-01-01", periods=8)
    left = pd.DataFrame(case["left"], index=dates, dtype=float)
    right = pd.DataFrame(case["right"], index=dates, dtype=float)
    actual = factor_information_coefficient(left, right, method=case["method"], min_periods=2)
    expected = pd.Series(case["expected"], index=dates, name=case["name"], dtype=case["dtype"])
    pd.testing.assert_index_equal(actual.index, expected.index, exact=True)
    assert actual.dtype == expected.dtype and actual.name == expected.name
    assert actual.isna().equals(expected.isna())
    if case["method"] == "pearson":
        pd.testing.assert_series_equal(actual, expected, check_exact=True)
    else:
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-12, equal_nan=True)


@pytest.mark.parametrize("method", ["pearson", "spearman"])
def test_one_asset_all_missing_and_pair_mask_before_ranking(method):
    dates = pd.date_range("2020-01-01", periods=3)
    left = pd.DataFrame([[1.0], [np.nan], [2.0]], index=dates)
    right = pd.DataFrame([[2.0], [1.0], [np.nan]], index=dates)
    assert factor_information_coefficient(left, right, method=method, min_periods=2).isna().all()
    left = pd.DataFrame([[1.0, 2.0, 100.0, 4.0]], index=dates[:1])
    right = pd.DataFrame([[4.0, 3.0, np.nan, 1.0]], index=dates[:1])
    result = factor_information_coefficient(left, right, method=method, min_periods=3)
    assert result.iloc[0] == pytest.approx(-1.0, abs=1e-12)


def test_pearson_fixture_values_are_binary64_portable():
    fixture_text = GOLDEN_PATH.read_text(encoding="utf-8")
    pearson_cases = [case for case in GOLDEN["cases"] if case["method"] == "pearson"]
    spearman_cases = [case for case in GOLDEN["cases"] if case["method"] == "spearman"]
    assert len(GOLDEN["cases"]) == 48
    assert len(pearson_cases) == 24
    assert len(spearman_cases) == 24
    for case in pearson_cases:
        n_columns = len(case["left"][0])
        assert len(set(case["left"][0])) == 1
        assert case["left"][1][0] != case["left"][1][0]
        assert case["right"][2][n_columns - 1] != case["right"][2][n_columns - 1]
        for value in _walk_numeric([case["left"], case["right"], case["expected"]]):
            if value != value:
                continue
            assert _is_finite_binary64_dyadic(value)
            assert float.fromhex(value.hex()) == value
            dumped = json.dumps(value)
            assert json.loads(dumped) == value
            assert dumped in fixture_text
    unit = next(
        case for case in pearson_cases if case["id"] == "scale_1.0_offset_0.0_3_pearson"
    )
    assert unit["expected"][3] == 0.5
    assert float(unit["expected"][3]).hex() == "0x1.0000000000000p-1"
    assert "1.0000009536743164" in fixture_text
    assert "1099511627776.0" in fixture_text
    assert "8.183476519740355e+149" in fixture_text
    assert "6.696928794914171e+299" in fixture_text
