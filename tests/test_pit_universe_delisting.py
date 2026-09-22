"""Synthetic PIT identity, availability, and terminal cash accounting oracles."""

import json

import numpy as np
import pandas as pd
import pytest

from backtest.long_short import run_long_short_backtest
from backtest.portfolio import (
    BacktestValidationError,
    capture_backtest_source_provenance,
    run_long_only_backtest,
)
from data.constituent_table import (
    build_pit_membership_mask,
    load_constituent_intervals_csv,
)


def panels():
    dates = pd.bdate_range("2024-01-01", periods=12, name="date")
    prices = pd.DataFrame({"SEC_A": 10.0, "SEC_B": 20.0}, index=dates)
    signals = pd.DataFrame({"SEC_A": 2.0, "SEC_B": 1.0}, index=dates)
    return dates, prices, signals


def intervals(dates):
    return pd.DataFrame(
        {
            "symbol": ["AAA", "BBB"],
            "permanent_id": ["SEC_A", "SEC_B"],
            "start_date": [dates[0]] * 2,
            "end_date": [pd.NaT] * 2,
            "start_known_at": [dates[0]] * 2,
            "end_known_at": [pd.NaT] * 2,
        }
    )


def event(dates, *, asset="SEC_A", position=5, value=-0.5, known_position=4):
    return pd.DataFrame(
        [
            {
                "event_id": "synthetic-final-cash",
                "permanent_id": asset,
                "effective_date": dates[position],
                "known_at": dates[known_position],
                "reference_date": dates[position - 1],
                "terminal_return": value,
                "return_basis": "prior_observed_close_to_cash",
            }
        ]
    )


def run(kind, prices, signals, **kwargs):
    settings = dict(
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="W-FRI",
        initial_capital=100.0,
    )
    settings.update(kwargs)
    if kind == "lo":
        settings.setdefault("top_n", 1)
        return run_long_only_backtest(
            prices,
            signals,
            source_provenance=capture_backtest_source_provenance(prices, signals),
            **settings,
        )
    return run_long_short_backtest(prices, signals, quantiles=2, **settings)


def holdings(kind, book):
    return book.holdings if kind == "lo" else book.net_holdings


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_event_free_results_expose_zero_flows_and_residual_cash(kind):
    _, prices, signals = panels()
    book = run(kind, prices, signals)
    assert book.terminal_event_log == ()
    assert book.terminal_cashflows.eq(0).all().all()
    assert "membership_contract" not in book.assumptions
    assert "terminal_settlement_contract" not in book.assumptions
    assert book.cash_balance.iloc[0] == 100
    np.testing.assert_allclose(
        book.cash_balance + holdings(kind, book).sum(axis=1) * book.equity_curve,
        book.equity_curve,
        rtol=0,
        atol=1e-12,
    )


@pytest.mark.parametrize("kind", ["lo", "ls"])
@pytest.mark.parametrize("value", [-0.5, 0.2, 0.0])
def test_long_terminal_cash_and_surviving_book_hand_oracle(kind, value):
    dates, prices, signals = panels()
    prices.loc[dates[5] :, "SEC_A"] = np.nan
    book = run(kind, prices, signals, terminal_events=event(dates, value=value))
    weight = 1.0 if kind == "lo" else 0.5
    expected_equity = 100 * (1 + weight * value)
    expected_proceeds = 100 * weight * (1 + value)
    assert book.equity_curve.loc[dates[5]] == pytest.approx(expected_equity)
    assert book.terminal_cashflows.loc[dates[5], "SEC_A"] == pytest.approx(
        expected_proceeds
    )
    expected_cash = expected_equity if kind == "lo" else expected_equity + 50
    assert book.cash_balance.loc[dates[5]] == pytest.approx(expected_cash)
    assert holdings(kind, book).loc[dates[5] :, "SEC_A"].eq(0).all()
    assert book.turnover.loc[dates[5]] == 0
    assert book.total_trading_costs.loc[dates[5]] == 0
    np.testing.assert_allclose(
        book.cash_balance.loc[dates[5] : dates[8]], expected_cash, rtol=0, atol=1e-12
    )
    if kind == "ls":
        assert holdings(kind, book).loc[dates[5], "SEC_B"] == pytest.approx(
            -50 / expected_equity
        )
    assert len(book.terminal_event_log) == 1
    assert book.terminal_event_log[0]["incoming_weight"] == weight
    assert book.terminal_event_log[0]["cashflow"] == pytest.approx(expected_proceeds)
    json.dumps(book.terminal_event_log, allow_nan=False)
    np.testing.assert_allclose(
        book.cash_balance + holdings(kind, book).sum(axis=1) * book.equity_curve,
        book.equity_curve,
        rtol=1e-14,
        atol=1e-12,
    )


@pytest.mark.parametrize("value", [-1.0, -0.6, 0.5])
def test_short_terminal_liability_payment(value):
    dates, prices, signals = panels()
    prices.loc[dates[5] :, "SEC_B"] = np.nan
    book = run(
        "ls", prices, signals, terminal_events=event(dates, asset="SEC_B", value=value)
    )
    assert book.equity_curve.loc[dates[5]] == pytest.approx(100 - 50 * value)
    assert book.terminal_cashflows.loc[dates[5], "SEC_B"] == pytest.approx(
        -50 * (1 + value)
    )
    assert book.cash_balance.loc[dates[5]] == pytest.approx(100 - 50 * (1 + value))
    assert book.net_holdings.loc[dates[5], "SEC_A"] == pytest.approx(
        50 / (100 - 50 * value)
    )
    assert book.net_holdings.loc[dates[5] :, "SEC_B"].eq(0).all()


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_settlement_cash_persists_as_surviving_asset_changes_value(kind):
    dates, prices, signals = panels()
    prices.loc[dates[5] :, "SEC_A"] = np.nan
    prices.loc[dates[5:9], "SEC_B"] = [22.0, 24.0, 18.0, 26.0]
    settings = {"top_n": 2} if kind == "lo" else {}
    book = run(kind, prices, signals, terminal_events=event(dates), **settings)
    expected_cash = 25.0 if kind == "lo" else 125.0
    surviving_shares = 2.5 if kind == "lo" else -2.5
    np.testing.assert_allclose(
        book.cash_balance.loc[dates[5:9]], expected_cash, rtol=0, atol=1e-12
    )
    np.testing.assert_allclose(
        book.equity_curve.loc[dates[5:9]],
        expected_cash + surviving_shares * prices.loc[dates[5:9], "SEC_B"],
        rtol=0,
        atol=1e-12,
    )


def test_explicit_zero_payoff_and_portfolio_insolvency_refusal():
    dates, prices, signals = panels()
    prices.loc[dates[5] :, "SEC_A"] = np.nan
    events = event(dates, value=-1)
    with pytest.raises(BacktestValidationError, match="portfolio_insolvent"):
        run("lo", prices, signals, terminal_events=events)
    book = run("lo", prices, signals, terminal_events=events, max_position_weight=0.5)
    assert book.equity_curve.loc[dates[5]] == 50
    assert book.cash_balance.loc[dates[5]] == 50
    assert book.terminal_cashflows.to_numpy().sum() == 0
    assert book.terminal_event_log[0]["terminal_return"] == -1
    assert book.assumptions["holding_episode_closed_count"] == 1
    assert book.metrics["average_holding_period_return"] == -1


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_event_return_replaces_quote_and_is_applied_once(kind):
    dates, prices, signals = panels()
    prices.loc[dates[5] :, "SEC_A"] = 500.0
    book = run(kind, prices, signals, terminal_events=event(dates))
    expected = 50 if kind == "lo" else 75
    assert book.equity_curve.loc[dates[5]] == expected
    assert book.equity_curve.loc[dates[6]] == expected
    assert book.terminal_cashflows["SEC_A"].ne(0).sum() == 1


@pytest.mark.parametrize("kind", ["lo", "ls"])
@pytest.mark.parametrize("missing_position", [4, 5])
def test_missing_terminal_evidence_and_missing_reference_refuse(kind, missing_position):
    dates, prices, signals = panels()
    prices.loc[dates[missing_position], "SEC_A"] = np.nan
    with pytest.raises(BacktestValidationError):
        run(kind, prices, signals)
    if missing_position == 4:
        with pytest.raises(BacktestValidationError):
            run(kind, prices, signals, terminal_events=event(dates))


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_late_terminal_information_refuses_frozen_target_collision(kind):
    dates, prices, signals = panels()
    events = event(dates, position=5, known_position=5)
    prices.loc[dates[5] :, "SEC_A"] = np.nan
    with pytest.raises(BacktestValidationError, match="terminal_target_invalid"):
        run(kind, prices, signals, terminal_events=events, rebalance_frequency="D")


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_preannounced_terminal_schedule_preserves_frozen_targets(kind):
    dates, prices, signals = panels()
    events = event(dates)
    prices.loc[dates[5] :, "SEC_A"] = np.nan
    book = run(kind, prices, signals, terminal_events=events, rebalance_frequency="D")
    assert holdings(kind, book).loc[dates[5] :, "SEC_A"].eq(0).all()
    changed = events.copy()
    changed["terminal_return"] = 0.75
    alternate = run(
        kind, prices, signals, terminal_events=changed, rebalance_frequency="D"
    )
    pd.testing.assert_series_equal(
        book.equity_curve.loc[: dates[4]], alternate.equity_curve.loc[: dates[4]]
    )
    pd.testing.assert_frame_equal(
        holdings(kind, book).loc[: dates[4]], holdings(kind, alternate).loc[: dates[4]]
    )


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_terminal_costs_and_residual_cash_follow_existing_convention(kind):
    dates, prices, signals = panels()
    prices.loc[dates[5] :, "SEC_A"] = np.nan
    book = run(
        kind,
        prices,
        signals,
        terminal_events=event(dates),
        transaction_cost_bps=10,
        slippage_bps=20,
    )
    # First scheduled position establishes gross exposure 1 and pays 30 bps.
    assert book.equity_curve.loc[dates[4]] == pytest.approx(99.7)
    weight = 1 if kind == "lo" else 0.5
    assert book.terminal_cashflows.loc[dates[5], "SEC_A"] == pytest.approx(
        99.7 * weight * 0.5
    )
    assert book.total_trading_costs.loc[dates[5]] == 0
    assert book.equity_curve.loc[dates[5]] == pytest.approx(99.7 * (1 - 0.5 * weight))


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_final_row_and_simultaneous_settlement(kind):
    dates, prices, signals = panels()
    events = event(dates, position=11, known_position=10)
    second = event(dates, asset="SEC_B", position=11, known_position=10, value=0.2)
    second["event_id"] = "other-final-cash"
    prices.loc[dates[11]] = np.nan
    book = run(kind, prices, signals, terminal_events=pd.concat([events, second]))
    assert holdings(kind, book).iloc[-1].eq(0).all()
    assert book.cash_balance.iloc[-1] == pytest.approx(book.equity_curve.iloc[-1])
    assert len(book.terminal_event_log) == 2


@pytest.mark.parametrize("lag", [1, 2])
def test_membership_knowledge_cutoffs_and_late_closure(lag):
    dates, _, _ = panels()
    table = intervals(dates)
    table.loc[0, ["start_date", "start_known_at"]] = [dates[3], dates[1]]
    table.loc[1, ["end_date", "end_known_at"]] = [dates[4], dates[6]]
    mask = build_pit_membership_mask(
        table, dates, ["SEC_A", "SEC_B"], signal_lag_periods=lag
    )
    for j, date in enumerate(dates):
        if j < lag:
            assert not mask.loc[date].any()
        else:
            assert mask.loc[date, "SEC_A"] == (
                date >= dates[3] and dates[j - lag] >= dates[1]
            )
            assert mask.loc[date, "SEC_B"] == (
                not (date >= dates[4] and dates[j - lag] >= dates[6])
            )
    changed = table.copy()
    changed.loc[1, "end_date"] = dates[2]
    alternate = build_pit_membership_mask(
        changed, dates, ["SEC_A", "SEC_B"], signal_lag_periods=lag
    )
    pd.testing.assert_frame_equal(mask.iloc[: 6 + lag], alternate.iloc[: 6 + lag])


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_membership_engine_integration_and_empty_universe(kind):
    dates, prices, signals = panels()
    table = intervals(dates)
    table["start_date"] = dates[2]
    table["end_date"] = dates[6]
    table["end_known_at"] = dates[4]
    book = run(
        kind, prices, signals, constituent_intervals=table, rebalance_frequency="D"
    )
    assert holdings(kind, book).iloc[:2].eq(0).all().all()
    assert holdings(kind, book).iloc[2:6].abs().to_numpy().sum() > 0
    assert holdings(kind, book).iloc[6:].eq(0).all().all()
    assert book.cash_balance.iloc[-1] == pytest.approx(book.equity_curve.iloc[-1])


def test_ticker_reassignment_uses_separate_price_id_axes(tmp_path):
    dates, _, _ = panels()
    table = intervals(dates)
    table["symbol"] = "REUSED"
    table.loc[0, ["end_date", "end_known_at"]] = [dates[5], dates[3]]
    table.loc[1, ["start_date", "start_known_at"]] = [dates[5], dates[3]]
    path = tmp_path / "identity.csv"
    table.to_csv(path, index=False)
    loaded = load_constituent_intervals_csv(path)
    mask = build_pit_membership_mask(loaded, dates, ["SEC_A", "SEC_B"])
    assert mask.loc[dates[4]].tolist() == [True, False]
    assert mask.loc[dates[5]].tolist() == [False, True]
    with pytest.raises(ValueError, match="PIT-005"):
        build_pit_membership_mask(loaded, dates, ["REUSED"])
    with pytest.raises(ValueError):
        build_pit_membership_mask(table.drop(columns="permanent_id"), dates, ["REUSED"])
    reused_prices = pd.DataFrame(
        {"SEC_A": [10] * 5 + [np.nan] * 7, "SEC_B": [np.nan] * 5 + [1000] * 7},
        index=dates,
    )
    signals = pd.DataFrame(1.0, index=dates, columns=reused_prices.columns)
    events = event(dates, value=-0.4, known_position=3)
    book = run(
        "lo",
        reused_prices,
        signals,
        constituent_intervals=table,
        terminal_events=events,
        rebalance_frequency="D",
    )
    assert book.equity_curve.loc[dates[5]] == 60
    assert book.holdings.loc[dates[5]].tolist() == [0.0, 1.0]
    assert book.equity_curve.iloc[-1] == 60


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_event",
        "duplicate_asset",
        "unknown_asset",
        "late_known",
        "bad_reference",
        "off_calendar",
        "wrong_basis",
        "null_basis",
        "below_minus_one",
        "nonfinite",
        "boolean",
        "missing_field",
        "extra_field",
    ],
)
@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_terminal_input_refusals(kind, mutation):
    dates, prices, signals = panels()
    events = event(dates)
    if mutation in ("duplicate_event", "duplicate_asset"):
        extra = events.copy()
        extra["permanent_id" if mutation == "duplicate_event" else "event_id"] = (
            "SEC_B" if mutation == "duplicate_event" else "other"
        )
        events = pd.concat([events, extra])
    else:
        changes = {
            "unknown_asset": ("permanent_id", "ALIAS"),
            "late_known": ("known_at", dates[6]),
            "bad_reference": ("reference_date", dates[3]),
            "off_calendar": ("effective_date", pd.Timestamp("2024-01-07")),
            "wrong_basis": ("return_basis", "additional_delisting_leg"),
            "null_basis": ("return_basis", pd.NA),
            "below_minus_one": ("terminal_return", -1.1),
            "nonfinite": ("terminal_return", np.inf),
            "boolean": ("terminal_return", True),
        }
        if mutation == "missing_field":
            events = events.drop(columns="reference_date")
        elif mutation == "extra_field":
            events["payment_date"] = dates[8]
        else:
            column, value = changes[mutation]
            events[column] = value
    with pytest.raises(ValueError):
        run(kind, prices, signals, terminal_events=events)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_availability",
        "late_time",
        "timezone",
        "bad_date",
        "inverted",
        "zero_interval",
        "missing_end_known",
        "open_with_end_known",
        "missing_id",
        "mixed_id",
        "overlap",
        "duplicate_column",
    ],
)
def test_pit_membership_invalid_evidence(mutation):
    dates, _, _ = panels()
    table = intervals(dates)
    if mutation == "missing_availability":
        table = table.drop(columns="start_known_at")
    elif mutation == "late_time":
        table["start_known_at"] = dates[0] + pd.Timedelta(hours=16)
    elif mutation == "timezone":
        table["start_known_at"] = dates[0].tz_localize("UTC")
    elif mutation == "bad_date":
        table["start_known_at"] = "unparseable"
    elif mutation in ("inverted", "zero_interval"):
        table["start_date"] = dates[2]
        table["end_date"] = dates[1] if mutation == "inverted" else dates[2]
        table["end_known_at"] = dates[1]
    elif mutation == "missing_end_known":
        table["end_date"] = dates[5]
    elif mutation == "open_with_end_known":
        table["end_known_at"] = dates[5]
    elif mutation == "missing_id":
        table.loc[0, "permanent_id"] = pd.NA
    elif mutation == "mixed_id":
        table["permanent_id"] = ["SEC_A", 1]
    elif mutation == "overlap":
        table["symbol"] = "SAME"
    elif mutation == "duplicate_column":
        table = pd.concat([table, table[["symbol"]]], axis=1)
    with pytest.raises(ValueError):
        build_pit_membership_mask(table, dates, ["SEC_A", "SEC_B"])


@pytest.mark.parametrize(
    "mutation",
    [
        "empty_dates",
        "duplicate_dates",
        "reverse_dates",
        "missing_date",
        "intraday",
        "timezone",
        "empty_assets",
        "duplicate_assets",
        "mixed_assets",
        "ticker_axis",
    ],
)
def test_pit_membership_axis_refusals(mutation):
    dates, _, _ = panels()
    table = intervals(dates)
    assets = ["SEC_A", "SEC_B"]
    if mutation == "empty_dates":
        dates = dates[:0]
    elif mutation == "duplicate_dates":
        dates = dates.insert(1, dates[0])
    elif mutation == "reverse_dates":
        dates = dates[::-1]
    elif mutation == "missing_date":
        dates = dates.insert(1, pd.NaT)
    elif mutation == "intraday":
        dates = dates + pd.Timedelta(hours=16)
    elif mutation == "timezone":
        dates = dates.tz_localize("UTC")
    elif mutation == "empty_assets":
        assets = []
    elif mutation == "duplicate_assets":
        assets = ["SEC_A", "SEC_A"]
    elif mutation == "mixed_assets":
        assets = ["SEC_A", 1]
    elif mutation == "ticker_axis":
        assets = ["AAA", "BBB"]
    with pytest.raises(ValueError):
        build_pit_membership_mask(table, dates, assets)


@pytest.mark.parametrize("lag", [True, 0, -1, 1.0, np.nan])
def test_pit_membership_lag_refusals(lag):
    dates, _, _ = panels()
    with pytest.raises(ValueError):
        build_pit_membership_mask(
            intervals(dates), dates, ["SEC_A", "SEC_B"], signal_lag_periods=lag
        )


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_bounded_window_lag_and_event_outside_evaluation(kind):
    dates, prices, signals = panels()
    table = intervals(dates)
    book = run(
        kind,
        prices,
        signals,
        constituent_intervals=table,
        terminal_events=event(dates, position=11, known_position=8),
        evaluation_start=dates[2],
        evaluation_end=dates[8],
        signal_lag_periods=2,
        rebalance_frequency="D",
    )
    assert holdings(kind, book).iloc[:2].eq(0).all().all()
    assert book.terminal_event_log == ()
    assert book.terminal_cashflows.eq(0).all().all()
    # An already-settled security remains closed in a later bounded window.
    prices.loc[dates[5] :, "SEC_A"] = np.nan
    later = run(
        kind,
        prices,
        signals,
        terminal_events=event(dates),
        evaluation_start=dates[7],
        rebalance_frequency="D",
    )
    assert holdings(kind, later)["SEC_A"].eq(0).all()


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_late_information_is_invariant_for_prior_book_decisions(kind):
    dates, prices, signals = panels()
    first = intervals(dates)
    first.loc[0, ["end_date", "end_known_at"]] = [dates[4], dates[7]]
    second = first.copy()
    second.loc[0, "end_date"] = dates[2]
    a = run(kind, prices, signals, constituent_intervals=first, rebalance_frequency="D")
    b = run(
        kind, prices, signals, constituent_intervals=second, rebalance_frequency="D"
    )
    pd.testing.assert_frame_equal(
        holdings(kind, a).loc[: dates[7]], holdings(kind, b).loc[: dates[7]]
    )
    pd.testing.assert_series_equal(
        a.equity_curve.loc[: dates[7]], b.equity_curve.loc[: dates[7]]
    )


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_pit_input_ownership_and_missing_price_policy(kind):
    dates, prices, signals = panels()
    with pytest.raises(ValueError, match="universe_input_ambiguous"):
        run(
            kind,
            prices,
            signals,
            constituent_intervals=intervals(dates),
            universe_mask=prices.gt(0),
        )
    if kind == "lo":
        with pytest.raises(ValueError, match="pit_missing_price_policy_invalid"):
            run(
                kind,
                prices,
                signals,
                constituent_intervals=intervals(dates),
                missing_price_policy="zero_return",
            )


def test_csv_preserves_known_at_and_refuses_intraday_truncation(tmp_path):
    dates, _, _ = panels()
    table = intervals(dates)
    path = tmp_path / "intervals.csv"
    table.to_csv(path, index=False)
    loaded = load_constituent_intervals_csv(path)
    pd.testing.assert_series_equal(
        loaded.data["start_known_at"], table["start_known_at"], check_dtype=False
    )
    table["start_known_at"] = dates[0] + pd.Timedelta(hours=16)
    table.to_csv(path, index=False)
    with pytest.raises(ValueError, match="source-close labels"):
        load_constituent_intervals_csv(path)


@pytest.mark.parametrize("column", ["start_date", "end_date"])
@pytest.mark.parametrize("kind", ["intraday", "timezone"])
def test_pit_csv_effective_dates_preserve_precision_boundary(tmp_path, column, kind):
    dates, _, _ = panels()
    table = intervals(dates)
    stamp = dates[0] if column == "start_date" else dates[5]
    table[column] = (
        stamp + pd.Timedelta(hours=16) if kind == "intraday" else stamp.tz_localize("UTC")
    )
    path = tmp_path / "pit_effective_dates.csv"
    table.to_csv(path, index=False)
    reason = "source-close labels" if kind == "intraday" else "timezone-naive"
    with pytest.raises(ValueError, match=reason):
        load_constituent_intervals_csv(path)


def test_same_security_reentry_and_gapped_observed_calendar():
    dates, _, _ = panels()
    table = pd.concat(
        [intervals(dates).iloc[[0]], intervals(dates).iloc[[0]]], ignore_index=True
    )
    table.loc[0, ["end_date", "end_known_at"]] = [dates[3], dates[1]]
    table.loc[1, ["start_date", "start_known_at"]] = [dates[7], dates[6]]
    table.loc[1, "symbol"] = "NEW_ALIAS"
    source = dates[[0, 1, 3, 4, 7, 9]]
    mask = build_pit_membership_mask(table, source, ["SEC_A"])
    assert mask["SEC_A"].tolist() == [False, True, False, False, False, True]
    assert mask.index.name == dates.name
