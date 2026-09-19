import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from features.combination import equal_weighted_composite, ic_weighted_composite
from features.operators import cross_sectional_zscore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMBINATION_SOURCE = PROJECT_ROOT / "src" / "features" / "combination.py"


def _panel(values: dict[str, list[float]], *, start: str = "2024-01-01") -> pd.DataFrame:
    first_column = next(iter(values.values()))
    dates = pd.date_range(start, periods=len(first_column), freq="D")
    return pd.DataFrame(values, index=dates)


def test_equal_weighted_composite_is_mean_of_cross_sectional_zscores() -> None:
    factor_a = _panel({"AAA": [1.0, 3.0], "BBB": [3.0, 1.0]})
    factor_b = _panel({"AAA": [10.0, 30.0], "BBB": [30.0, 10.0]})

    result = equal_weighted_composite([factor_a, factor_b])

    expected = _panel({"AAA": [-1.0, 1.0], "BBB": [1.0, -1.0]})
    assert_frame_equal(result, expected)


def test_ic_weighted_composite_hand_calculated_positive_weights() -> None:
    factor_a = _panel({"AAA": [1.0, 3.0], "BBB": [3.0, 1.0]})
    factor_b = _panel({"AAA": [10.0, 30.0], "BBB": [30.0, 10.0]})

    result = ic_weighted_composite([factor_a, factor_b], [0.25, 0.75])

    expected = _panel({"AAA": [-1.0, 1.0], "BBB": [1.0, -1.0]})
    assert_frame_equal(result, expected)


def test_ic_weighted_composite_negative_weight_inverts_factor() -> None:
    factor_a = _panel({"AAA": [1.0, 3.0], "BBB": [3.0, 1.0]})
    factor_b = _panel({"AAA": [10.0, 30.0], "BBB": [30.0, 10.0]})

    result = ic_weighted_composite([factor_a, factor_b], [1.0, -1.0])

    expected = _panel({"AAA": [0.0, 0.0], "BBB": [0.0, 0.0]})
    assert_frame_equal(result, expected)


def test_ic_weighted_composite_accepts_series_weights() -> None:
    factor_a = _panel({"AAA": [1.0], "BBB": [3.0]})
    factor_b = _panel({"AAA": [10.0], "BBB": [30.0]})
    weights = pd.Series([0.0, 1.0])

    result = ic_weighted_composite([factor_a, factor_b], weights)

    assert_frame_equal(result, cross_sectional_zscore(factor_b))


def test_equal_weighted_composite_skips_missing_factor_cells() -> None:
    factor_a = _panel({"AAA": [1.0, np.nan], "BBB": [3.0, 1.0]})
    factor_b = _panel({"AAA": [10.0, 30.0], "BBB": [30.0, 10.0]})

    result = equal_weighted_composite([factor_a, factor_b])

    assert result.loc[result.index[0], "AAA"] == pytest.approx(-1.0)
    assert result.loc[result.index[1], "AAA"] == pytest.approx(1.0)
    assert result.loc[result.index[1], "BBB"] == pytest.approx(-1.0)


def test_combination_does_not_use_future_rows() -> None:
    factor_a = _panel({"AAA": [1.0, 2.0, 3.0], "BBB": [3.0, 2.0, 1.0]})
    factor_b = _panel({"AAA": [10.0, 20.0, 30.0], "BBB": [30.0, 20.0, 10.0]})
    changed_a = factor_a.copy()
    changed_b = factor_b.copy()
    changed_a.iloc[-1] = 10_000.0
    changed_b.iloc[-1] = 10_000.0
    signal_date = factor_a.index[-2]

    assert_series_equal(
        equal_weighted_composite([changed_a, changed_b]).loc[signal_date],
        equal_weighted_composite([factor_a, factor_b]).loc[signal_date],
        check_names=False,
    )
    assert_series_equal(
        ic_weighted_composite([changed_a, changed_b], [0.4, 0.6]).loc[signal_date],
        ic_weighted_composite([factor_a, factor_b], [0.4, 0.6]).loc[signal_date],
        check_names=False,
    )


def test_combination_preserves_index_and_columns() -> None:
    factor_a = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]}, start="2024-02-01")
    factor_b = _panel({"AAA": [5.0, 6.0], "BBB": [7.0, 8.0]}, start="2024-02-01")

    result = equal_weighted_composite([factor_a, factor_b])

    assert result.index.equals(factor_a.index)
    assert result.columns.equals(factor_a.columns)


def test_combination_rejects_empty_and_mismatched_panels() -> None:
    factor_a = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]})
    shifted = _panel({"AAA": [1.0, 2.0], "BBB": [3.0, 4.0]}, start="2024-01-02")
    other_assets = _panel({"AAA": [1.0, 2.0], "CCC": [3.0, 4.0]})

    with pytest.raises(ValueError, match="empty"):
        equal_weighted_composite([])
    with pytest.raises(TypeError, match="list of DataFrames"):
        equal_weighted_composite(factor_a)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="identical indexes"):
        equal_weighted_composite([factor_a, shifted])
    with pytest.raises(ValueError, match="identical columns"):
        equal_weighted_composite([factor_a, other_assets])
    with pytest.raises(ValueError, match="one value per factor"):
        ic_weighted_composite([factor_a, factor_a], [1.0])
    with pytest.raises(ValueError, match="nonzero"):
        ic_weighted_composite([factor_a, factor_a], [0.0, 0.0])
    with pytest.raises(ValueError, match="finite"):
        ic_weighted_composite([factor_a], [np.nan])
    with pytest.raises(TypeError, match="numeric and non-boolean"):
        ic_weighted_composite([factor_a], [True])  # type: ignore[list-item]


def test_combination_module_has_no_abstract_class_hierarchy() -> None:
    tree = ast.parse(COMBINATION_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        assert not isinstance(node, ast.ClassDef)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert "backtest" not in node.module
            assert "portfolio" not in node.module
            assert "alphas" not in node.module
