import math

import numpy as np
import pandas as pd
import pytest

from backtest.metrics import (
    calculate_basic_metrics,
    calculate_holdings_state_metrics,
    calculate_tracking_error,
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


def test_holdings_state_hhi_is_rounded_for_stable_serialization() -> None:
    holdings = pd.DataFrame(
        [[0.1, 0.2, 0.3]],
        index=pd.date_range("2024-01-01", periods=1),
        columns=["A", "B", "C"],
    )

    metrics = calculate_holdings_state_metrics(holdings)

    assert metrics["average_position_concentration_hhi"] == 0.388888888888889
    assert metrics["max_position_concentration_hhi"] == 0.388888888888889


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
        (_holdings({"AAA": [0.5 + 99j]}), TypeError, "numeric, non-boolean"),
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


def test_tracking_error_is_hand_calculated_and_excludes_only_anchor() -> None:
    index = pd.date_range("2024-01-01", periods=4, freq="D")
    strategy_returns = pd.Series([99.0, 0.01, 0.03, -0.02], index=index)
    benchmark_returns = pd.Series([0.0, 0.0, 0.01, 0.0], index=index)

    result = calculate_tracking_error(
        strategy_returns,
        benchmark_returns,
        return_frequency="daily_close_to_close",
    )

    assert result == pytest.approx(np.std([0.01, 0.02, -0.02], ddof=0) * np.sqrt(252))
    changed_terminal = strategy_returns.copy()
    changed_terminal.iloc[-1] = 0.02
    assert calculate_tracking_error(
        changed_terminal,
        benchmark_returns,
        return_frequency="daily_close_to_close",
    ) != pytest.approx(result)


def test_tracking_error_rejects_invalid_return_values() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    valid = pd.Series([0.0, 0.01, 0.02], index=index)

    for invalid in [
        pd.Series([0.0, np.nan, 0.02], index=index),
        pd.Series([0.0, np.inf, 0.02], index=index),
        pd.Series([False, True, False], index=index),
        pd.Series([0.0 + 0.0j, 0.01 + 1.0j, 0.02 + 0.0j], index=index),
        pd.Series(["0.0", "0.01", "0.02"], index=index),
    ]:
        with pytest.raises((TypeError, ValueError)):
            calculate_tracking_error(
                invalid,
                valid,
                return_frequency="daily_close_to_close",
            )


def test_tracking_error_requires_exact_index_timezone_and_frequency() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    strategy_returns = pd.Series([0.0, 0.01, 0.02], index=index)
    benchmark_returns = pd.Series([0.0, 0.00, 0.01], index=index)

    with pytest.raises(ValueError, match="identical indexes"):
        calculate_tracking_error(
            strategy_returns,
            benchmark_returns.shift(freq="D"),
            return_frequency="daily_close_to_close",
        )
    with pytest.raises(ValueError, match="matching timezones"):
        calculate_tracking_error(
            strategy_returns,
            benchmark_returns.tz_localize("UTC"),
            return_frequency="daily_close_to_close",
        )
    with pytest.raises(ValueError, match="matching timezones"):
        calculate_tracking_error(
            strategy_returns.tz_localize("UTC"),
            benchmark_returns.tz_localize("America/New_York"),
            return_frequency="daily_close_to_close",
        )
    with pytest.raises(ValueError, match="daily_close_to_close only"):
        calculate_tracking_error(
            strategy_returns,
            benchmark_returns,
            return_frequency="weekly_close_to_close",
        )


def test_tracking_error_rejects_bad_axes_anchor_and_short_sample() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    valid = pd.Series([0.0, 0.01, 0.02], index=index)

    duplicate = valid.copy()
    duplicate.index = pd.DatetimeIndex([index[0], index[0], index[2]])
    with pytest.raises(ValueError, match="duplicate dates"):
        calculate_tracking_error(
            duplicate,
            valid,
            return_frequency="daily_close_to_close",
        )

    with pytest.raises(ValueError, match="sorted"):
        calculate_tracking_error(
            valid.sort_index(ascending=False),
            valid.sort_index(ascending=False),
            return_frequency="daily_close_to_close",
        )

    nonzero_anchor = valid.copy()
    nonzero_anchor.iloc[0] = 0.01
    with pytest.raises(ValueError, match="synthetic zero-return anchor"):
        calculate_tracking_error(
            valid,
            nonzero_anchor,
            return_frequency="daily_close_to_close",
        )

    short_index = index[:2]
    with pytest.raises(ValueError, match="at least 2 measured return periods"):
        calculate_tracking_error(
            pd.Series([0.0, 0.01], index=short_index),
            pd.Series([0.0, 0.00], index=short_index),
            return_frequency="daily_close_to_close",
        )


def test_tracking_error_rejects_wrong_types_empty_and_non_datetime_indexes() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    valid = pd.Series([0.0, 0.01, 0.02], index=index)

    with pytest.raises(TypeError, match="strategy_returns must be a pandas Series"):
        calculate_tracking_error(
            [0.0, 0.01, 0.02],
            valid,
            return_frequency="daily_close_to_close",
        )
    with pytest.raises(TypeError, match="DatetimeIndex"):
        calculate_tracking_error(
            pd.Series([0.0, 0.01, 0.02]),
            valid,
            return_frequency="daily_close_to_close",
        )
    with pytest.raises(ValueError, match="must not be empty"):
        calculate_tracking_error(
            pd.Series(dtype=float, index=pd.DatetimeIndex([])),
            pd.Series(dtype=float, index=pd.DatetimeIndex([])),
            return_frequency="daily_close_to_close",
        )


def test_basic_metrics_add_tracking_error_only_with_explicit_benchmark_returns() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    returns = pd.Series([0.0, 0.01, 0.02], index=index)
    benchmark_returns = pd.Series([0.0, 0.00, 0.01], index=index)
    equity = (1.0 + returns).cumprod()

    without_benchmark_returns = calculate_basic_metrics(equity, returns)
    with_benchmark_returns = calculate_basic_metrics(
        equity,
        returns,
        benchmark_returns=benchmark_returns,
    )

    assert "tracking_error" not in without_benchmark_returns
    assert with_benchmark_returns["tracking_error"] == pytest.approx(
        np.std([0.01, 0.01], ddof=0) * np.sqrt(252)
    )

    with pytest.raises(ValueError, match="daily_close_to_close only"):
        calculate_basic_metrics(
            equity,
            returns,
            benchmark_returns=benchmark_returns,
            periods_per_year=12,
        )
