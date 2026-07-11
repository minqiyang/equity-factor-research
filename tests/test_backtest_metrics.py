import math

import numpy as np
import pandas as pd
import pytest

from backtest.metrics import (
    calculate_basic_metrics,
    calculate_holdings_state_metrics,
)


def _holdings(values: dict[str, list[object]]) -> pd.DataFrame:
    first_column = next(iter(values.values()))
    index = pd.date_range("2024-01-01", periods=len(first_column), freq="D")
    return pd.DataFrame(values, index=index)


def test_holdings_state_metrics_are_hand_calculated_and_gross_normalized() -> None:
    holdings = _holdings(
        {
            "AAA": [0.0, 0.5, 0.25, 0.8, 1.0],
            "BBB": [0.0, 0.5, 0.25, 0.2, 0.0],
            "CCC": [0.0, 0.0, 0.0, 0.0, 0.0],
        }
    )

    metrics = calculate_holdings_state_metrics(holdings)

    assert metrics["average_holding_count"] == pytest.approx(1.75)
    assert metrics["average_position_concentration_hhi"] == pytest.approx(0.67)
    assert metrics["max_position_concentration_hhi"] == pytest.approx(1.0)

    partial_cash = calculate_holdings_state_metrics(
        holdings.loc[[holdings.index[2]]]
    )
    assert partial_cash["average_position_concentration_hhi"] == pytest.approx(0.5)
    assert partial_cash["average_position_concentration_hhi"] != pytest.approx(0.125)


def test_holdings_state_metrics_include_terminal_closing_snapshot() -> None:
    holdings = _holdings(
        {
            "AAA": [0.5, 0.5, 1.0],
            "BBB": [0.5, 0.5, 0.0],
        }
    )

    metrics = calculate_holdings_state_metrics(holdings)

    assert metrics["average_holding_count"] == pytest.approx(5.0 / 3.0)
    assert metrics["average_position_concentration_hhi"] == pytest.approx(2.0 / 3.0)
    assert metrics["max_position_concentration_hhi"] == pytest.approx(1.0)


def test_holdings_state_metrics_return_nan_without_active_dates() -> None:
    metrics = calculate_holdings_state_metrics(
        _holdings({"AAA": [0.0, 0.0], "BBB": [0.0, 0.0]})
    )

    assert all(math.isnan(value) for value in metrics.values())


@pytest.mark.parametrize(
    ("holdings", "error_type", "match"),
    [
        (pd.DataFrame({"AAA": [0.5]}), TypeError, "DatetimeIndex"),
        (_holdings({"AAA": [np.nan]}), ValueError, "missing"),
        (_holdings({"AAA": [np.inf]}), ValueError, "finite"),
        (_holdings({"AAA": [-0.1]}), ValueError, "non-negative"),
        (_holdings({"AAA": [0.6], "BBB": [0.5]}), ValueError, "gross exposure"),
        (_holdings({"AAA": ["0.5"]}), TypeError, "numeric, non-boolean"),
        (_holdings({"AAA": [True]}), TypeError, "numeric, non-boolean"),
    ],
)
def test_holdings_state_metrics_reject_invalid_values(
    holdings: pd.DataFrame,
    error_type: type[Exception],
    match: str,
) -> None:
    with pytest.raises(error_type, match=match):
        calculate_holdings_state_metrics(holdings)


def test_holdings_state_metrics_reject_duplicate_and_unsorted_axes() -> None:
    duplicate_dates = _holdings({"AAA": [0.5, 0.5]})
    duplicate_dates.index = pd.DatetimeIndex(
        [duplicate_dates.index[0], duplicate_dates.index[0]]
    )
    with pytest.raises(ValueError, match="duplicate dates"):
        calculate_holdings_state_metrics(duplicate_dates)

    unsorted = _holdings({"AAA": [0.5, 0.5]}).sort_index(ascending=False)
    with pytest.raises(ValueError, match="sorted"):
        calculate_holdings_state_metrics(unsorted)

    duplicate_assets = _holdings({"AAA": [0.5]})
    duplicate_assets["BBB"] = 0.5
    duplicate_assets.columns = ["AAA", "AAA"]
    with pytest.raises(ValueError, match="duplicate assets"):
        calculate_holdings_state_metrics(duplicate_assets)


def test_basic_metrics_remain_backward_compatible_without_holdings() -> None:
    index = pd.date_range("2024-01-01", periods=2, freq="D")
    returns = pd.Series([0.0, 0.01], index=index)
    equity = (1.0 + returns).cumprod()

    metrics = calculate_basic_metrics(equity, returns)

    assert "average_holding_count" not in metrics
    assert "average_position_concentration_hhi" not in metrics
    assert "max_position_concentration_hhi" not in metrics


def test_basic_metrics_require_holdings_to_match_return_dates() -> None:
    index = pd.date_range("2024-01-01", periods=2, freq="D")
    returns = pd.Series([0.0, 0.01], index=index)
    equity = (1.0 + returns).cumprod()
    holdings = _holdings({"AAA": [0.0, 1.0]}).shift(freq="D")

    with pytest.raises(ValueError, match="holdings index must exactly match"):
        calculate_basic_metrics(equity, returns, holdings=holdings)
