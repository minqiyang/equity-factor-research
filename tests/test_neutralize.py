"""Deterministic tests for cross-sectional factor neutralization."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from features.neutralize import (
    cross_sectional_demean,
    cross_sectional_group_neutralize,
    cross_sectional_neutralize,
)


def _panel(values: dict[str, list[float]], *, start: str = "2025-01-06") -> pd.DataFrame:
    first_col = next(iter(values.values()))
    dates = pd.bdate_range(start, periods=len(first_col))
    return pd.DataFrame(values, index=dates)


def test_cross_sectional_demean_hand_calculated() -> None:
    factor = _panel({"AAA": [1.0, 10.0], "BBB": [2.0, 20.0], "CCC": [3.0, 30.0]})

    result = cross_sectional_demean(factor)

    expected = _panel({"AAA": [-1.0, -10.0], "BBB": [0.0, 0.0], "CCC": [1.0, 10.0]})
    assert_frame_equal(result, expected)


def test_cross_sectional_demean_preserves_nans() -> None:
    factor = _panel({"AAA": [1.0], "BBB": [np.nan], "CCC": [3.0]})

    result = cross_sectional_demean(factor)

    # Mean of 1.0 and 3.0 is 2.0
    expected = _panel({"AAA": [-1.0], "BBB": [np.nan], "CCC": [1.0]})
    assert_frame_equal(result, expected)


def test_cross_sectional_neutralize_single_risk_factor_orthogonality() -> None:
    # 5 assets, 3 dates
    # Let y be strongly correlated with x: y = 2.0 * x + noise
    x = _panel(
        {
            "A": [1.0, 2.0, 3.0],
            "B": [2.0, 3.0, 4.0],
            "C": [3.0, 4.0, 5.0],
            "D": [4.0, 5.0, 6.0],
            "E": [5.0, 6.0, 7.0],
        },
    )
    # y has a linear component from x plus a distinct signal
    y = _panel(
        {
            "A": [2.0 + 0.1, 4.0 + 0.2, 6.0 + 0.3],
            "B": [4.0 - 0.2, 6.0 - 0.1, 8.0 + 0.0],
            "C": [6.0 + 0.5, 8.0 + 0.3, 10.0 - 0.2],
            "D": [8.0 - 0.1, 10.0 + 0.4, 12.0 + 0.1],
            "E": [10.0 + 0.0, 12.0 - 0.3, 14.0 + 0.4],
        },
    )

    residual = cross_sectional_neutralize(y, x, add_intercept=True)

    # For each date:
    # 1. Residual must sum to 0 (demeaned due to intercept)
    # 2. Dot product (orthogonality) between x and residual must be 0
    # 3. Correlation between x and residual must be 0
    for date in y.index:
        res_row = residual.loc[date].to_numpy(dtype=float)
        x_row = x.loc[date].to_numpy(dtype=float)

        assert float(np.sum(res_row)) == pytest.approx(0.0, abs=1e-10)
        assert float(np.dot(x_row, res_row)) == pytest.approx(0.0, abs=1e-10)
        corr = np.corrcoef(x_row, res_row)[0, 1]
        assert float(corr) == pytest.approx(0.0, abs=1e-10)


def test_cross_sectional_neutralize_multiple_risk_factors() -> None:
    # Orthogonalize against two risk factors simultaneously: Size (x1) and Vol (x2)
    x1 = _panel(
        {
            "A": [1.0, 2.0],
            "B": [2.0, 1.0],
            "C": [3.0, 4.0],
            "D": [4.0, 3.0],
            "E": [5.0, 5.0],
        },
    )
    x2 = _panel(
        {
            "A": [0.5, 0.2],
            "B": [0.1, 0.4],
            "C": [0.8, 0.3],
            "D": [0.2, 0.7],
            "E": [0.9, 0.1],
        },
    )
    # y = 3.0 * x1 - 1.5 * x2 + signal
    y = _panel(
        {
            "A": [3.0 * 1.0 - 1.5 * 0.5 + 0.1, 3.0 * 2.0 - 1.5 * 0.2 + 0.2],
            "B": [3.0 * 2.0 - 1.5 * 0.1 - 0.1, 3.0 * 1.0 - 1.5 * 0.4 + 0.0],
            "C": [3.0 * 3.0 - 1.5 * 0.8 + 0.3, 3.0 * 4.0 - 1.5 * 0.3 - 0.2],
            "D": [3.0 * 4.0 - 1.5 * 0.2 - 0.2, 3.0 * 3.0 - 1.5 * 0.7 + 0.1],
            "E": [3.0 * 5.0 - 1.5 * 0.9 + 0.0, 3.0 * 5.0 - 1.5 * 0.1 - 0.1],
        },
    )

    residual = cross_sectional_neutralize(y, [x1, x2], add_intercept=True)

    for date in y.index:
        res = residual.loc[date].to_numpy(dtype=float)
        v1 = x1.loc[date].to_numpy(dtype=float)
        v2 = x2.loc[date].to_numpy(dtype=float)

        assert float(np.sum(res)) == pytest.approx(0.0, abs=1e-10)
        assert float(np.dot(v1, res)) == pytest.approx(0.0, abs=1e-10)
        assert float(np.dot(v2, res)) == pytest.approx(0.0, abs=1e-10)


def test_cross_sectional_neutralize_preserves_nans() -> None:
    x = _panel({"A": [1.0], "B": [np.nan], "C": [3.0], "D": [4.0], "E": [5.0]})
    y = _panel({"A": [2.0], "B": [4.0], "C": [np.nan], "D": [8.0], "E": [10.0]})

    residual = cross_sectional_neutralize(y, x)

    # Assets B (x is NaN) and C (y is NaN) must be NaN in output
    assert pd.isna(residual.loc[y.index[0], "B"])
    assert pd.isna(residual.loc[y.index[0], "C"])

    # Valid assets A, D, E are evaluated
    valid_res = residual.loc[y.index[0], ["A", "D", "E"]].to_numpy(dtype=float)
    assert float(np.sum(valid_res)) == pytest.approx(0.0, abs=1e-10)


def test_cross_sectional_group_neutralize_static_mapping() -> None:
    factor = _panel(
        {
            "AAPL": [10.0, 20.0],
            "MSFT": [20.0, 30.0],
            "XOM": [5.0, 10.0],
            "CVX": [7.0, 14.0],
        },
    )
    groups = {
        "AAPL": "Tech",
        "MSFT": "Tech",
        "XOM": "Energy",
        "CVX": "Energy",
    }

    result = cross_sectional_group_neutralize(factor, groups)

    # Tech: mean of AAPL (10) and MSFT (20) is 15 -> AAPL=-5, MSFT=+5
    # Energy: mean of XOM (5) and CVX (7) is 6 -> XOM=-1, CVX=+1
    expected = _panel(
        {
            "AAPL": [-5.0, -5.0],
            "MSFT": [5.0, 5.0],
            "XOM": [-1.0, -2.0],
            "CVX": [1.0, 2.0],
        },
    )
    assert_frame_equal(result, expected)


def test_cross_sectional_group_neutralize_dynamic_groups() -> None:
    factor = _panel(
        {
            "A": [10.0, 20.0],
            "B": [20.0, 30.0],
            "C": [5.0, 10.0],
        },
    )
    # On day 1: A and B in G1, C in G2
    # On day 2: A in G1, B and C in G2
    groups = pd.DataFrame(
        {
            "A": ["G1", "G1"],
            "B": ["G1", "G2"],
            "C": ["G2", "G2"],
        },
        index=factor.index,
    )

    result = cross_sectional_group_neutralize(factor, groups)

    # Day 1:
    # G1 (A: 10, B: 20) -> mean 15 -> A=-5, B=5
    # G2 (C: 5) -> mean 5 -> C=0
    assert result.loc[factor.index[0], "A"] == pytest.approx(-5.0)
    assert result.loc[factor.index[0], "B"] == pytest.approx(5.0)
    assert result.loc[factor.index[0], "C"] == pytest.approx(0.0)

    # Day 2:
    # G1 (A: 20) -> mean 20 -> A=0
    # G2 (B: 30, C: 10) -> mean 20 -> B=10, C=-10
    assert result.loc[factor.index[1], "A"] == pytest.approx(0.0)
    assert result.loc[factor.index[1], "B"] == pytest.approx(10.0)
    assert result.loc[factor.index[1], "C"] == pytest.approx(-10.0)


def test_neutralize_input_validation_errors() -> None:
    y = _panel({"A": [1.0], "B": [2.0]})
    x = _panel({"A": [1.0], "C": [2.0]})  # mismatched columns

    with pytest.raises(ValueError, match="columns"):
        cross_sectional_neutralize(y, x)

    with pytest.raises(ValueError, match="min_assets"):
        cross_sectional_neutralize(y, y, min_assets=1)
