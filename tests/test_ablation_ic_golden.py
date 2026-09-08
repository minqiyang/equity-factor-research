"""Retained baseline stress oracle: exact Pearson, bounded Rank IC only."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from features.diagnostics import factor_information_coefficient


GOLDEN = json.loads((Path(__file__).parent / "fixtures/ablation/ic_baseline.json").read_text())


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
