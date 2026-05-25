import ast
import inspect

import numpy as np
import pandas as pd
import pytest

import features.worldquant_alphas as worldquant_alphas
from features.worldquant_alphas import alpha_009


def _close_panel(values: dict[str, list[float]], *, start: str = "2024-01-01") -> pd.DataFrame:
    first_column = next(iter(values.values()))
    dates = pd.date_range(start, periods=len(first_column), freq="D")
    return pd.DataFrame(values, index=dates)


def test_alpha_009_preserves_shape_index_and_columns() -> None:
    close = _close_panel(
        {
            "AAA": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0],
            "BBB": [20.0, 19.0, 18.0, 17.0, 16.0, 15.0, 14.0],
        }
    )

    alpha = alpha_009(close)

    assert alpha.index.equals(close.index)
    assert alpha.columns.equals(close.columns)
    assert alpha.shape == close.shape
    assert alpha.dtypes.tolist() == [np.dtype("float64"), np.dtype("float64")]


def test_alpha_009_positive_trend_returns_current_delta() -> None:
    close = _close_panel({"AAA": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]})

    alpha = alpha_009(close)

    assert alpha.iloc[:5, 0].isna().all()
    assert alpha.loc[close.index[5], "AAA"] == pytest.approx(1.0)


def test_alpha_009_negative_trend_returns_current_delta() -> None:
    close = _close_panel({"AAA": [15.0, 14.0, 13.0, 12.0, 11.0, 10.0]})

    alpha = alpha_009(close)

    assert alpha.iloc[:5, 0].isna().all()
    assert alpha.loc[close.index[5], "AAA"] == pytest.approx(-1.0)


def test_alpha_009_mixed_window_returns_negative_current_delta() -> None:
    close = _close_panel({"AAA": [10.0, 11.0, 10.0, 12.0, 11.0, 13.0]})

    alpha = alpha_009(close)

    assert alpha.loc[close.index[5], "AAA"] == pytest.approx(-2.0)


def test_alpha_009_zero_delta_uses_mixed_branch() -> None:
    close = _close_panel({"AAA": [10.0, 11.0, 12.0, 12.0, 13.0, 14.0]})

    alpha = alpha_009(close)

    assert alpha.loc[close.index[5], "AAA"] == pytest.approx(-1.0)


def test_alpha_009_does_not_use_future_close_values() -> None:
    close = _close_panel({"AAA": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0]})
    changed_future = close.copy()
    changed_future.loc[close.index[6], "AAA"] = 10_000.0

    base_alpha = alpha_009(close)
    changed_alpha = alpha_009(changed_future)

    signal_date = close.index[5]
    assert changed_alpha.loc[signal_date, "AAA"] == pytest.approx(base_alpha.loc[signal_date, "AAA"])


def test_alpha_009_missing_close_requires_full_valid_delta_window() -> None:
    close = _close_panel({"AAA": [10.0, 11.0, np.nan, 13.0, 14.0, 15.0, 16.0]})

    alpha = alpha_009(close)

    assert np.isnan(alpha.loc[close.index[5], "AAA"])
    assert np.isnan(alpha.loc[close.index[6], "AAA"])


def test_alpha_009_rejects_invalid_close_inputs() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")

    invalid_inputs = [
        pd.Series([1.0, 2.0, 3.0], index=dates),
        pd.DataFrame({"AAA": [1.0, 2.0, 3.0]}, index=[0, 1, 2]),
        pd.DataFrame({"AAA": [1.0, 2.0]}, index=[dates[0], dates[0]]),
        pd.DataFrame({"AAA": [1.0, 2.0]}, index=[dates[1], dates[0]]),
        pd.DataFrame(index=dates),
        pd.DataFrame({"AAA": [True, False, True]}, index=dates),
        pd.DataFrame({"AAA": [1.0, "bad", 3.0]}, index=dates),
        pd.DataFrame({"AAA": [1.0, "nan", 3.0]}, index=dates),
        pd.DataFrame({"AAA": [1.0, "NaN", 3.0]}, index=dates),
        pd.DataFrame({"AAA": ["1.0", "2.0", "3.0"]}, index=dates),
    ]

    for invalid_close in invalid_inputs:
        with pytest.raises((TypeError, ValueError)):
            alpha_009(invalid_close)


@pytest.mark.parametrize("invalid_window", [0, -1, False, 1.5])
def test_alpha_009_rejects_invalid_window(invalid_window) -> None:
    close = _close_panel({"AAA": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]})

    with pytest.raises((TypeError, ValueError)):
        alpha_009(close, window=invalid_window)


def test_alpha_009_custom_window_uses_full_trailing_delta_window() -> None:
    close = _close_panel({"AAA": [10.0, 11.0, 12.0, 13.0]})

    alpha = alpha_009(close, window=2)

    assert np.isnan(alpha.loc[close.index[1], "AAA"])
    assert alpha.loc[close.index[2], "AAA"] == pytest.approx(1.0)
    assert alpha.loc[close.index[3], "AAA"] == pytest.approx(1.0)


def test_alpha_009_module_has_no_backtest_integration_imports() -> None:
    source = inspect.getsource(worldquant_alphas)
    tree = ast.parse(source)

    forbidden_terms = [
        "backtest",
        "portfolio",
        "metrics",
        "strategies",
        "reporting",
    ]
    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    for module_name in imported_modules:
        assert not any(term in module_name for term in forbidden_terms)
