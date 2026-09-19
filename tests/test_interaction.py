import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from features.interaction import (
    conditional_factor_rank,
    factor_product_interaction,
    factor_quadrant_interaction,
)
from features.operators import cross_sectional_zscore

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTERACTION_SOURCE = PROJECT_ROOT / "src" / "features" / "interaction.py"


def _panel(values: dict[str, list[float]], *, start: str = "2024-01-01") -> pd.DataFrame:
    first_column = next(iter(values.values()))
    dates = pd.date_range(start, periods=len(first_column), freq="D")
    return pd.DataFrame(values, index=dates)


def test_factor_product_interaction_hand_calculated() -> None:
    # 2 dates, 3 assets
    factor_a = _panel({"AAA": [1.0, 10.0], "BBB": [2.0, 20.0], "CCC": [3.0, 30.0]})
    factor_b = _panel({"AAA": [3.0, 30.0], "BBB": [2.0, 20.0], "CCC": [1.0, 10.0]})

    # za: AAA=-1/sqrt(2/3), BBB=0, CCC=1/sqrt(2/3)
    # zb: AAA=1/sqrt(2/3), BBB=0, CCC=-1/sqrt(2/3)
    # product: AAA=-1.5, BBB=0.0, CCC=-1.5
    result_raw = factor_product_interaction(factor_a, factor_b, standardize_output=False)
    expected_raw = _panel({"AAA": [-1.5, -1.5], "BBB": [0.0, 0.0], "CCC": [-1.5, -1.5]})
    assert_frame_equal(result_raw, expected_raw)

    result_std = factor_product_interaction(factor_a, factor_b, standardize_output=True)
    expected_std = cross_sectional_zscore(expected_raw)
    assert_frame_equal(result_std, expected_std)


def test_factor_product_interaction_preserves_nans() -> None:
    factor_a = _panel({"AAA": [1.0, np.nan], "BBB": [2.0, 20.0], "CCC": [3.0, 30.0]})
    factor_b = _panel({"AAA": [3.0, 30.0], "BBB": [np.nan, 20.0], "CCC": [1.0, 10.0]})

    result = factor_product_interaction(factor_a, factor_b, standardize_output=False)
    assert np.isnan(result.loc[result.index[0], "BBB"])
    assert np.isnan(result.loc[result.index[1], "AAA"])
    assert not np.isnan(result.loc[result.index[0], "AAA"])
    assert not np.isnan(result.loc[result.index[1], "CCC"])


def test_conditional_factor_rank_hand_calculated() -> None:
    # 1 date, 6 assets, 2 bins of 3 assets each
    dates = pd.date_range("2024-01-01", periods=1)
    # Conditioning factor separates into 2 bins:
    # Bin 0: A1, A2, A3 (values 1, 2, 3)
    # Bin 1: B1, B2, B3 (values 10, 20, 30)
    cond = pd.DataFrame(
        {"A1": [1.0], "A2": [2.0], "A3": [3.0], "B1": [10.0], "B2": [20.0], "B3": [30.0]},
        index=dates,
    )
    # Target factor within Bin 0 has values 30, 10, 20 -> ranks: A2=0.0, A3=0.5, A1=1.0
    # Target factor within Bin 1 has values 200, 300, 100 -> ranks: B3=0.0, B1=0.5, B2=1.0
    target = pd.DataFrame(
        {"A1": [30.0], "A2": [10.0], "A3": [20.0], "B1": [200.0], "B2": [300.0], "B3": [100.0]},
        index=dates,
    )

    result = conditional_factor_rank(cond, target, n_bins=2)

    assert result.loc[dates[0], "A2"] == pytest.approx(0.0)
    assert result.loc[dates[0], "A3"] == pytest.approx(0.5)
    assert result.loc[dates[0], "A1"] == pytest.approx(1.0)
    assert result.loc[dates[0], "B3"] == pytest.approx(0.0)
    assert result.loc[dates[0], "B1"] == pytest.approx(0.5)
    assert result.loc[dates[0], "B2"] == pytest.approx(1.0)


def test_factor_quadrant_interaction_hand_calculated() -> None:
    dates = pd.date_range("2024-01-01", periods=1)
    fa = pd.DataFrame({"Q1": [1.0], "Q2": [-1.0], "Q3": [1.0], "Q4": [-1.0]}, index=dates)
    fb = pd.DataFrame({"Q1": [1.0], "Q2": [-1.0], "Q3": [-1.0], "Q4": [1.0]}, index=dates)

    result = factor_quadrant_interaction(fa, fb, threshold_a=0.0, threshold_b=0.0)

    assert result.loc[dates[0], "Q1"] == 1.0   # Concordant High
    assert result.loc[dates[0], "Q2"] == -1.0  # Concordant Low
    assert result.loc[dates[0], "Q3"] == 0.5   # Discordant A-High / B-Low
    assert result.loc[dates[0], "Q4"] == -0.5  # Discordant A-Low / B-High


def test_interaction_lookahead_free() -> None:
    factor_a = _panel({"AAA": [1.0, 2.0, 3.0], "BBB": [3.0, 2.0, 1.0]})
    factor_b = _panel({"AAA": [10.0, 20.0, 30.0], "BBB": [30.0, 20.0, 10.0]})

    changed_a = factor_a.copy()
    changed_b = factor_b.copy()
    changed_a.iloc[-1] = 9999.0
    changed_b.iloc[-1] = 9999.0

    signal_date = factor_a.index[0]

    assert_series_equal(
        factor_product_interaction(factor_a, factor_b).loc[signal_date],
        factor_product_interaction(changed_a, changed_b).loc[signal_date],
        check_names=False,
    )
    assert_series_equal(
        factor_quadrant_interaction(factor_a, factor_b).loc[signal_date],
        factor_quadrant_interaction(changed_a, changed_b).loc[signal_date],
        check_names=False,
    )


def test_interaction_rejects_mismatched_panels() -> None:
    factor_a = _panel({"AAA": [1.0], "BBB": [2.0]})
    factor_b = _panel({"AAA": [1.0], "CCC": [2.0]})

    with pytest.raises(ValueError, match="identical asset columns"):
        factor_product_interaction(factor_a, factor_b)
    with pytest.raises(ValueError, match="identical asset columns"):
        conditional_factor_rank(factor_a, factor_b)
    with pytest.raises(ValueError, match="identical asset columns"):
        factor_quadrant_interaction(factor_a, factor_b)
    with pytest.raises(ValueError, match="n_bins"):
        conditional_factor_rank(factor_a, factor_a, n_bins=1)


def test_interaction_module_has_no_abstract_class_hierarchy() -> None:
    tree = ast.parse(INTERACTION_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        assert not isinstance(node, ast.ClassDef)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert "backtest" not in node.module
            assert "portfolio" not in node.module
            assert "alphas" not in node.module
