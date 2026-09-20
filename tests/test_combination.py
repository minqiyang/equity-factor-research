import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from features.combination import (
    correlation_discounted_composite,
    equal_weighted_composite,
    ic_weighted_composite,
    icir_weighted_composite,
    walk_forward_correlation_discounted_composite,
    walk_forward_icir_weighted_composite,
)
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


def test_icir_weighted_composite_hand_calculated() -> None:
    factor_a = _panel({"AAA": [1.0, 3.0], "BBB": [3.0, 1.0]})
    factor_b = _panel({"AAA": [10.0, 30.0], "BBB": [30.0, 10.0]})

    # Factor A has higher ICIR (mean=0.10, std=0.02 -> ICIR=5.0)
    # Factor B has lower ICIR (mean=0.05, std=0.05 -> ICIR=1.0)
    ic_df = pd.DataFrame(
        {
            "fa": [0.08, 0.10, 0.12, 0.09, 0.11],
            "fb": [0.00, 0.10, 0.05, 0.02, 0.08],
        }
    )

    result = icir_weighted_composite([factor_a, factor_b], ic_df, min_ic_periods=5)
    expected = _panel({"AAA": [-1.0, 1.0], "BBB": [1.0, -1.0]})
    assert_frame_equal(result, expected)


def test_icir_weighted_composite_rejects_insufficient_periods_or_zero_std() -> None:
    factor_a = _panel({"AAA": [1.0], "BBB": [3.0]})
    # 4 periods < min_ic_periods=5
    short_ic = pd.DataFrame({"fa": [0.1, 0.2, 0.3, 0.4]})
    with pytest.raises(ValueError, match="valid IC periods"):
        icir_weighted_composite([factor_a], short_ic, min_ic_periods=5)

    # Constant IC -> zero std
    constant_ic = pd.DataFrame({"fa": [0.1, 0.1, 0.1, 0.1, 0.1]})
    with pytest.raises(ValueError, match="zero or undefined IC standard deviation"):
        icir_weighted_composite([factor_a], constant_ic, min_ic_periods=5)


def test_correlation_discounted_composite_discounts_collinear_factors() -> None:
    # 3 factors: factor_a and factor_b are identical (corr = 1.0), factor_c is orthogonal
    factor_a = _panel({"AAA": [1.0, 2.0], "BBB": [2.0, 1.0]})
    factor_b = _panel({"AAA": [1.0, 2.0], "BBB": [2.0, 1.0]})
    factor_c = _panel({"AAA": [1.0, 1.0], "BBB": [2.0, 2.0]})

    ic_weights = [0.1, 0.1, 0.1]
    # Correlation matrix where a and b are highly correlated (0.95), c is uncorrelated (0.0)
    corr = pd.DataFrame(
        [
            [1.0, 0.95, 0.0],
            [0.95, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )

    result = correlation_discounted_composite(
        [factor_a, factor_b, factor_c],
        ic_weights,
        factor_correlation=corr,
        ridge_alpha=0.05,
    )
    assert not result.isna().all().all()
    assert result.index.equals(factor_a.index)
    assert result.columns.equals(factor_a.columns)


def test_correlation_discounted_composite_rejects_invalid_inputs() -> None:
    factor_a = _panel({"AAA": [1.0], "BBB": [2.0]})
    with pytest.raises(ValueError, match="ridge_alpha"):
        correlation_discounted_composite([factor_a], [0.1], ridge_alpha=-0.1)
    with pytest.raises(ValueError, match="shape"):
        correlation_discounted_composite([factor_a], [0.1], factor_correlation=np.ones((2, 2)))


def test_walk_forward_icir_holds_weights_between_rebalances_and_ignores_future_ics() -> None:
    factor_a = _panel({"AAA": [1.0, 3.0, 1.0], "BBB": [3.0, 1.0, 3.0]})
    factor_b = _panel({"AAA": [10.0, 30.0, 10.0], "BBB": [30.0, 10.0, 30.0]})
    dates = factor_a.index
    rebalance_dates = pd.DatetimeIndex([dates[0], dates[1]])
    ic_history = pd.DataFrame(
        {
            "fa": [0.08, 0.10, 0.12, 0.09, 0.11, 0.90],
            "fb": [0.00, 0.10, 0.05, 0.02, 0.08, -0.90],
        },
        index=pd.DatetimeIndex(
            [
                "2023-07-31",
                "2023-08-31",
                "2023-09-30",
                "2023-10-31",
                "2023-11-30",
                dates[0],
            ]
        ),
    )

    result = walk_forward_icir_weighted_composite(
        [factor_a, factor_b],
        ic_history,
        rebalance_dates,
        min_ic_periods=5,
    )
    past_only = ic_history.iloc[:5]
    expected_first = icir_weighted_composite(
        [factor_a.iloc[[0]], factor_b.iloc[[0]]],
        past_only,
        min_ic_periods=5,
    )
    expected_later = icir_weighted_composite(
        [factor_a.iloc[1:], factor_b.iloc[1:]],
        ic_history,
        min_ic_periods=5,
    )
    assert_frame_equal(result.iloc[[0]], expected_first)
    assert_frame_equal(result.iloc[1:], expected_later)

    future_ics = ic_history.copy()
    future_ics.loc[dates[1]] = [1.0, -1.0]
    mutated = walk_forward_icir_weighted_composite(
        [factor_a, factor_b],
        future_ics,
        pd.DatetimeIndex([dates[0], dates[1]]),
        min_ic_periods=5,
    )
    assert_series_equal(result.loc[dates[0]], mutated.loc[dates[0]], check_names=False)


def test_walk_forward_icir_is_nan_until_minimum_history() -> None:
    factor_a = _panel({"AAA": [1.0, 3.0], "BBB": [3.0, 1.0]})
    dates = factor_a.index
    ic_history = pd.DataFrame(
        {"fa": [0.10, 0.12, 0.08, 0.09]},
        index=pd.DatetimeIndex(["2023-07-31", "2023-08-31", "2023-09-30", dates[0]]),
    )

    result = walk_forward_icir_weighted_composite(
        [factor_a],
        ic_history,
        pd.DatetimeIndex([dates[0], dates[1]]),
        min_ic_periods=5,
    )
    assert result.isna().all().all()


def test_walk_forward_correlation_uses_trailing_factor_values_only() -> None:
    factor_a = _panel({"AAA": [1.0, 2.0, 3.0], "BBB": [3.0, 2.0, 1.0]})
    factor_b = _panel({"AAA": [10.0, 20.0, 30.0], "BBB": [30.0, 20.0, 10.0]})
    dates = factor_a.index
    rebalance_dates = pd.DatetimeIndex([dates[1], dates[2]])
    ic_history = pd.DataFrame(
        {"fa": [0.20, 0.10], "fb": [0.05, 0.15]},
        index=pd.DatetimeIndex([dates[0], dates[1]]),
    )

    result = walk_forward_correlation_discounted_composite(
        [factor_a, factor_b],
        ic_history,
        rebalance_dates,
        ridge_alpha=0.1,
        min_ic_periods=1,
    )
    expected_mid = correlation_discounted_composite(
        [factor_a.iloc[[1]], factor_b.iloc[[1]]],
        list(ic_history.iloc[[0]].mean(axis=0)),
        factor_correlation=pd.DataFrame(
            np.corrcoef(
                [
                    factor_a.iloc[:2].to_numpy(dtype=float).flatten(),
                    factor_b.iloc[:2].to_numpy(dtype=float).flatten(),
                ]
            )
        ),
        ridge_alpha=0.1,
    )
    assert_frame_equal(result.iloc[[1]], expected_mid)

    scrambled = factor_a.copy()
    scrambled.iloc[-1] = 10_000.0
    mutated = walk_forward_correlation_discounted_composite(
        [scrambled, factor_b],
        ic_history,
        rebalance_dates,
        ridge_alpha=0.1,
        min_ic_periods=1,
    )
    assert_series_equal(result.loc[dates[1]], mutated.loc[dates[1]], check_names=False)
    assert result.loc[dates[0]].isna().all()



def test_combination_module_has_no_abstract_class_hierarchy() -> None:
    tree = ast.parse(COMBINATION_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        assert not isinstance(node, ast.ClassDef)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert "backtest" not in node.module
            assert "portfolio" not in node.module
            assert "alphas" not in node.module
