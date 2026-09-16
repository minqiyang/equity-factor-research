import inspect

import pandas as pd
import pytest

from backtest.portfolio import (
    capture_backtest_source_provenance,
    run_long_only_backtest,
)
from research.dividend_policy import (
    CASH_DIVIDEND_OVERLAY_POLICY,
    PRICE_RETURN_BASIS,
    price_series_simple_return,
    refuse_cash_dividend_overlay,
)


def _adjusted_close_panel() -> pd.DataFrame:
    dates = pd.DatetimeIndex(["2021-01-04", "2021-01-05", "2021-01-06"])
    return pd.DataFrame(
        {"AAA": [100.0, 100.0, 100.0], "BBB": [100.0, 100.0, 100.0]},
        index=dates,
    )


def test_price_series_simple_return_is_current_over_previous_minus_one() -> None:
    assert price_series_simple_return(100.0, 100.0) == pytest.approx(0.0)
    assert price_series_simple_return(100.0, 102.0) == pytest.approx(0.02)


def test_cash_dividend_on_adjusted_series_would_double_count() -> None:
    previous_price = 100.0
    current_adjusted_price = 100.0
    cash_dividend = 2.0
    price_only = price_series_simple_return(previous_price, current_adjusted_price)
    double_counted = price_only + cash_dividend / previous_price

    assert price_only == pytest.approx(0.0)
    assert double_counted == pytest.approx(0.02)
    assert double_counted > price_only


def test_absent_cash_dividend_overlay_is_allowed() -> None:
    refuse_cash_dividend_overlay(None)


@pytest.mark.parametrize(
    "overlay",
    [
        2.0,
        0,
        pd.Series([2.0]),
        pd.DataFrame({"AAA": [2.0]}),
        pd.DataFrame(),
    ],
)
def test_cash_dividend_overlay_is_refused(overlay: object) -> None:
    with pytest.raises(ValueError, match="cash_dividends overlay"):
        refuse_cash_dividend_overlay(overlay)


def test_long_only_backtest_has_no_cash_dividend_parameter() -> None:
    names = inspect.signature(run_long_only_backtest).parameters
    forbidden = {
        "cash_dividends",
        "dividends",
        "dividend",
        "dividend_yield",
        "cash_flows",
    }

    assert forbidden.isdisjoint(names)
    assert PRICE_RETURN_BASIS == "supplied_price_series_simple_return_v1"
    assert CASH_DIVIDEND_OVERLAY_POLICY == (
        "refuse_separate_cash_dividend_on_supplied_price_series"
    )


def test_held_gross_return_matches_adjusted_price_ratio_without_cash_dividend() -> None:
    prices = _adjusted_close_panel()
    signals = pd.DataFrame(
        {"AAA": [2.0, 2.0, 2.0], "BBB": [1.0, 1.0, 1.0]},
        index=prices.index,
    )
    result = run_long_only_backtest(
        prices,
        signals,
        source_provenance=capture_backtest_source_provenance(prices, signals),
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=1,
        transaction_cost_bps=0.0,
        slippage_bps=0.0,
    )
    holding_date = prices.index[1]
    return_date = prices.index[2]
    previous_price = float(prices.loc[holding_date, "AAA"])
    current_price = float(prices.loc[return_date, "AAA"])
    cash_dividend = 2.0
    price_only = price_series_simple_return(previous_price, current_price)
    double_counted = price_only + cash_dividend / previous_price

    assert result.holdings.loc[holding_date, "AAA"] == pytest.approx(1.0)
    assert result.gross_returns.loc[return_date] == pytest.approx(price_only)
    assert result.gross_returns.loc[return_date] == pytest.approx(0.0)
    assert result.gross_returns.loc[return_date] != pytest.approx(double_counted)
