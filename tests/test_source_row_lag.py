import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from backtest.portfolio import (
    capture_backtest_source_provenance,
    run_long_only_backtest,
)
from research.source_row_lag import (
    DEMO_SIGNAL_LAG_PERIODS,
    SIGNAL_LAG_UNIT,
    lag_by_observed_source_rows,
    refuse_inserted_source_rows,
    require_observed_source_index,
)


def _gapped_monday_wednesday_friday() -> pd.DatetimeIndex:
    return pd.DatetimeIndex(["2021-01-04", "2021-01-06", "2021-01-08"])


def _panel() -> pd.DataFrame:
    return pd.DataFrame(
        {"AAA": [100.0, 101.0, 102.0], "BBB": [100.0, 99.0, 98.0]},
        index=_gapped_monday_wednesday_friday(),
    )


def test_require_observed_source_index_keeps_gapped_rows() -> None:
    prices = _panel()
    validated = require_observed_source_index(prices)

    assert_frame_equal(validated, prices.astype(float))
    assert validated is not prices
    assert list(validated.index) == list(_gapped_monday_wednesday_friday())


def test_lag_by_observed_source_rows_uses_previous_observed_row() -> None:
    signals = pd.DataFrame(
        {"AAA": [2.0, 1.0, 3.0], "BBB": [1.0, 4.0, 0.5]},
        index=_gapped_monday_wednesday_friday(),
    )

    lagged = lag_by_observed_source_rows(signals, DEMO_SIGNAL_LAG_PERIODS)

    assert lagged.loc["2021-01-04"].isna().all()
    assert_series_equal(
        lagged.loc["2021-01-06"],
        signals.loc["2021-01-04"],
        check_names=False,
    )
    assert_series_equal(
        lagged.loc["2021-01-08"],
        signals.loc["2021-01-06"],
        check_names=False,
    )


def test_calendar_day_lag_points_at_the_omitted_weekday() -> None:
    dates = _gapped_monday_wednesday_friday()
    wednesday = dates[1]
    calendar_prior = wednesday - pd.Timedelta(days=1)
    source_prior = dates[0]

    assert calendar_prior == pd.Timestamp("2021-01-05")
    assert calendar_prior not in dates
    assert source_prior == pd.Timestamp("2021-01-04")
    assert (wednesday - source_prior) > pd.Timedelta(days=1)


@pytest.mark.parametrize("lag", [0, False, -1, 1.5, "1", None])
def test_invalid_source_row_lag_is_refused(lag: object) -> None:
    with pytest.raises((TypeError, ValueError), match="at least one"):
        lag_by_observed_source_rows(_panel(), lag)  # type: ignore[arg-type]


def test_inserted_source_row_is_refused_without_mutating_input() -> None:
    observed = _panel()
    inserted = observed.reindex(
        observed.index.insert(1, pd.Timestamp("2021-01-05"))
    )
    filled = inserted.ffill()
    original = filled.copy()

    with pytest.raises(ValueError, match="silently inserted"):
        refuse_inserted_source_rows(filled, observed_index=observed.index)

    assert_frame_equal(filled, original)
    assert pd.Timestamp("2021-01-05") in filled.index
    assert pd.Timestamp("2021-01-05") not in observed.index


def test_dropped_observed_source_row_is_refused() -> None:
    observed = _panel()
    dropped = observed.drop(index=observed.index[1])

    with pytest.raises(ValueError, match="dropped"):
        refuse_inserted_source_rows(dropped, observed_index=observed.index)


def test_demo_backtest_lag_advances_to_next_observed_source_row() -> None:
    dates = _gapped_monday_wednesday_friday()
    prices = pd.DataFrame(
        {"AAA": [100.0, 100.0, 100.0], "BBB": [100.0, 100.0, 100.0]},
        index=dates,
    )
    signals = pd.DataFrame(
        {"AAA": [2.0, 1.0, 1.0], "BBB": [1.0, 2.0, 2.0]},
        index=dates,
    )

    result = run_long_only_backtest(
        prices,
        signals,
        source_provenance=capture_backtest_source_provenance(prices, signals),
        evaluation_start=dates[0],
        evaluation_end=dates[-1],
        rebalance_frequency="D",
        top_n=1,
        signal_lag_periods=DEMO_SIGNAL_LAG_PERIODS,
    )

    wednesday = dates[1]
    friday = dates[2]
    assert result.assumptions["signal_lag_periods"] == DEMO_SIGNAL_LAG_PERIODS
    assert result.assumptions["signal_lag_unit"] == SIGNAL_LAG_UNIT
    assert result.holdings.loc[wednesday, "AAA"] == 1.0
    assert result.holdings.loc[friday, "BBB"] == 1.0

    wednesday_row = next(
        row for row in result.timing_ledger if row.ledger_date == wednesday
    )
    friday_row = next(
        row for row in result.timing_ledger if row.ledger_date == friday
    )
    assert wednesday_row.signal_source_date == dates[0]
    assert friday_row.signal_source_date == dates[1]
    assert (wednesday - dates[0]) > pd.Timedelta(days=1)
    assert (friday - dates[1]) > pd.Timedelta(days=1)
