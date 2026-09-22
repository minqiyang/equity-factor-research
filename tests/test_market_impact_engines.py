"""Both-engine accounting, participation, timing, and terminal integration."""

import numpy as np
import pandas as pd
import pytest

from backtest.market_impact import SquareRootImpactModel, MarketImpactValidationError
from backtest.portfolio import (
    capture_backtest_source_provenance,
    run_long_only_backtest,
)
from backtest.long_short import run_long_short_backtest


def panels():
    dates = pd.bdate_range("2024-01-01", periods=16, name="date")
    prices = pd.DataFrame({"SEC_A": 10.0, "SEC_B": 10.0}, index=dates)
    signals = pd.DataFrame({"SEC_A": 2.0, "SEC_B": 1.0}, index=dates)
    volumes = pd.DataFrame(100.0, index=dates, columns=prices.columns)
    return prices, signals, volumes


def run(kind, prices=None, signals=None, volumes=None, **kwargs):
    if prices is None:
        prices, signals, volumes = panels()
    settings = dict(
        evaluation_start=prices.index[3],
        evaluation_end=prices.index[-1],
        rebalance_frequency="W-FRI",
        initial_capital=100.0,
        impact_model=SquareRootImpactModel(
            lookback=2, min_adv=1, max_participation_rate=1
        ),
        impact_volumes=volumes,
        impact_price_basis="raw",
        impact_volume_basis="raw",
    )
    settings.update(kwargs)
    if kind == "lo":
        return run_long_only_backtest(
            prices,
            signals,
            top_n=1,
            source_provenance=capture_backtest_source_provenance(prices, signals),
            **settings,
        )
    return run_long_short_backtest(prices, signals, quantiles=2, **settings)


def holdings(kind, book):
    return book.holdings if kind == "lo" else book.net_holdings


def reconcile(kind, book, prices):
    weights = holdings(kind, book)
    positions = weights.mul(book.equity_curve, axis=0)
    np.testing.assert_allclose(
        positions.sum(axis=1) + book.cash_balance, book.equity_curve, rtol=1e-13
    )
    previous_eq = book.equity_curve.shift(1).fillna(book.equity_curve.iloc[0])
    fees = book.transaction_costs * previous_eq
    slip = book.slippage_cost_series
    cash_delta = (
        -book.executed_trade_values.sum(axis=1)
        - fees
        - slip
        + book.terminal_cashflows.sum(axis=1)
    )
    np.testing.assert_allclose(
        book.cash_balance.diff().iloc[1:], cash_delta.iloc[1:], atol=2e-12, rtol=1e-12
    )
    for i in range(1, len(positions)):
        day, prev = positions.index[i], positions.index[i - 1]
        valued = (positions.loc[prev] * (prices.loc[day] / prices.loc[prev])).where(
            positions.loc[prev].ne(0), 0.0
        )
        for event in book.terminal_event_log:
            if pd.Timestamp(event["effective_date"]) == day:
                valued.loc[event["permanent_id"]] = 0.0
        np.testing.assert_allclose(
            positions.loc[day],
            valued + book.executed_trade_values.loc[day],
            atol=2e-12,
            rtol=1e-12,
        )
    pretrade_eq = previous_eq * (1 + book.gross_returns)
    np.testing.assert_allclose(
        book.turnover,
        book.executed_trade_values.abs().sum(axis=1) / pretrade_eq,
        atol=1e-14,
    )
    np.testing.assert_allclose(
        book.equity_curve,
        previous_eq + previous_eq * book.gross_returns - fees - slip,
        atol=2e-12,
    )
    assert book.cash_balance.ge(0).all()


@pytest.mark.parametrize("kind", ["lo", "ls"])
@pytest.mark.parametrize("mode", ["raise", "throttle", "penalize"])
def test_daily_rebalance_cash_and_quantity_accounting(kind, mode):
    prices, signals, volumes = panels()
    prices["SEC_A"] *= np.array(
        [
            1.0,
            1.01,
            0.98,
            1.03,
            1.0,
            1.08,
            0.99,
            1.1,
            1.08,
            1.2,
            1.19,
            1.15,
            1.21,
            1.17,
            1.1,
            1.15,
        ]
    )
    signals.iloc[8:] = [0.0, 3.0]
    model = SquareRootImpactModel(
        lookback=2,
        min_adv=1,
        max_participation_rate=1.0 if mode == "raise" else 0.1,
        mode=mode,
        eta=0.5,
        fixed_bps=4,
    )
    book = run(
        kind,
        prices,
        signals,
        volumes,
        impact_model=model,
        transaction_cost_bps=10,
        rebalance_frequency="D",
    )
    reconcile(kind, book, prices)
    assert book.slippage_cost_series.sum() > 0
    trade = book.executed_trade_values.abs().sum(axis=1)
    expected_bps = (10000 * book.slippage_cost_series / trade).fillna(0)
    np.testing.assert_allclose(book.realized_slippage_bps, expected_bps)
    assert book.assumptions["cash_model"].startswith("self_financing")
    assert book.assumptions["formal_market_impact_evidence_eligible"] is False


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_throttle_retries_shares_at_changed_prices_and_retains_final_queue(kind):
    prices, signals, volumes = panels()
    prices.iloc[5:, 0] = 20.0
    model = SquareRootImpactModel(
        lookback=2, min_adv=1, max_participation_rate=0.01, mode="throttle", eta=0
    )
    book = run(
        kind,
        prices,
        signals,
        volumes,
        impact_model=model,
        evaluation_end=prices.index[7],
    )
    day4, day5 = prices.index[4:6]
    assert book.executed_trade_values.loc[day4, "SEC_A"] == 10
    assert book.pending_trade_shares.loc[day4, "SEC_A"] == (9 if kind == "lo" else 4)
    assert book.executed_trade_values.loc[day5, "SEC_A"] == 10
    assert book.pending_trade_shares.loc[day5, "SEC_A"] == (
        8.5 if kind == "lo" else 3.5
    )
    assert book.pending_trade_shares.iloc[-1].abs().sum() > 0
    assert book.trade_participation_rates.max().max() <= 0.01 + 1e-15
    reconcile(kind, book, prices)


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_new_frozen_target_cancels_previous_deferred_shares(kind):
    prices, signals, volumes = panels()
    signals.iloc[8:] = [0.0, 3.0]
    model = SquareRootImpactModel(
        lookback=2, min_adv=1, max_participation_rate=0.01, mode="throttle", eta=0
    )
    book = run(kind, prices, signals, volumes, impact_model=model, initial_capital=1000)
    date = prices.index[9]
    np.testing.assert_allclose(
        book.cancelled_trade_shares.loc[date],
        book.pending_trade_shares.loc[prices.index[8]],
    )
    assert book.executed_trade_values.loc[date, "SEC_A"] < 0
    assert book.executed_trade_values.loc[date, "SEC_B"] > 0


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_known_ineligible_pending_increase_is_cancelled(kind):
    prices, signals, volumes = panels()
    mask = pd.DataFrame(True, index=prices.index, columns=prices.columns)
    mask.loc[prices.index[5] :, "SEC_A"] = False
    model = SquareRootImpactModel(
        lookback=2, min_adv=1, max_participation_rate=0.01, mode="throttle", eta=0
    )
    book = run(kind, prices, signals, volumes, impact_model=model, universe_mask=mask)
    assert book.cancelled_trade_shares.loc[prices.index[5], "SEC_A"] > 0
    assert book.pending_trade_shares.loc[prices.index[5], "SEC_A"] == 0
    assert book.executed_trade_values.loc[prices.index[5], "SEC_A"] == 0


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_sparse_universe_row_cancels_pending_increases(kind):
    prices, signals, volumes = panels()
    mask = pd.DataFrame(True, index=[prices.index[4]], columns=prices.columns)
    model = SquareRootImpactModel(
        lookback=2, min_adv=1, max_participation_rate=0.01, mode="throttle", eta=0
    )
    book = run(kind, prices, signals, volumes, impact_model=model, universe_mask=mask)
    assert book.pending_trade_shares.loc[prices.index[5]].eq(0).all()


@pytest.mark.parametrize("kind", ["lo", "ls"])
@pytest.mark.parametrize("asset", ["SEC_A", "SEC_B"])
def test_terminal_cash_exemption_and_pending_cancellation(kind, asset):
    prices, signals, volumes = panels()
    date = prices.index[5]
    prices.loc[date:, asset] = np.nan
    volumes.loc[date:, asset] = np.nan
    events = pd.DataFrame(
        [
            dict(
                event_id="final",
                permanent_id=asset,
                effective_date=date,
                reference_date=prices.index[4],
                known_at=prices.index[4],
                terminal_return=-0.5,
                return_basis="prior_observed_close_to_cash",
            )
        ]
    )
    model = SquareRootImpactModel(
        lookback=2,
        min_adv=1,
        max_participation_rate=0.01,
        mode="throttle",
        eta=0,
        fixed_bps=10,
    )
    book = run(
        kind, prices, signals, volumes, impact_model=model, terminal_events=events
    )
    previous_pending = book.pending_trade_shares.loc[prices.index[4], asset]
    assert book.cancelled_trade_shares.loc[date, asset] == previous_pending
    assert book.executed_trade_values.loc[date:, asset].eq(0).all()
    assert book.pending_trade_shares.loc[date:, asset].eq(0).all()
    assert book.terminal_cashflows.loc[date, asset] == pytest.approx(
        book.executed_trade_values.loc[prices.index[4], asset] * 0.5
    )
    assert book.slippage_cost_series.loc[date] == pytest.approx(
        book.executed_trade_values.loc[date].abs().sum() * 0.001
    )
    reconcile(kind, book, prices)


def test_asymmetric_long_short_throttle_exposes_actual_net_exposure():
    prices, signals, volumes = panels()
    volumes["SEC_B"] = 200
    model = SquareRootImpactModel(
        lookback=2, min_adv=1, max_participation_rate=0.01, mode="throttle", eta=0
    )
    book = run("ls", prices, signals, volumes, impact_model=model)
    assert book.net_holdings.loc[prices.index[4]].sum() == pytest.approx(-0.1)
    assert book.assumptions["dollar_neutral"] is False
    assert book.assumptions["target_dollar_neutral"] is True


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_participation_raise_occurs_before_cash_funding(kind):
    with pytest.raises(
        MarketImpactValidationError, match="impact_participation_exceeded"
    ):
        run(
            kind,
            impact_model=SquareRootImpactModel(
                lookback=2, min_adv=1, max_participation_rate=0.001
            ),
        )


@pytest.mark.parametrize("kind", ["lo", "ls"])
@pytest.mark.parametrize(
    "kwargs,reason",
    [
        ({"slippage_bps": 1}, "impact_input_ambiguous"),
        ({"impact_model": None}, "impact_input_ambiguous"),
        ({"impact_volume_basis": "split_adjusted"}, "impact_basis_invalid"),
        ({"impact_volumes": None}, "impact_axes_invalid"),
    ],
)
def test_explicit_optional_input_contract(kind, kwargs, reason):
    with pytest.raises(MarketImpactValidationError, match=reason):
        run(kind, **kwargs)


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_warmup_required_and_zero_current_volume_refused(kind):
    prices, signals, volumes = panels()
    with pytest.raises(MarketImpactValidationError, match="impact_adv_invalid"):
        run(
            kind,
            prices,
            signals,
            volumes,
            evaluation_start=prices.index[0],
            rebalance_frequency="D",
        )
    volumes.loc[prices.index[4], "SEC_A"] = 0
    with pytest.raises(
        MarketImpactValidationError, match="impact_execution_volume_invalid"
    ):
        run(kind, prices, signals, volumes)


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_future_liquidity_values_outside_window_are_irrelevant(kind):
    prices, signals, volumes = panels()
    end = prices.index[7]
    book = run(kind, prices, signals, volumes, evaluation_end=end)
    prices = prices.astype(object)
    volumes = volumes.astype(object)
    prices.iloc[8:] = "future invalid"
    volumes.iloc[8:] = "future invalid"
    changed = run(kind, prices, signals, volumes, evaluation_end=end)
    for field in ["equity_curve", "returns", "slippage_cost_series", "cash_balance"]:
        pd.testing.assert_series_equal(getattr(book, field), getattr(changed, field))
    pd.testing.assert_frame_equal(
        book.executed_trade_values, changed.executed_trade_values
    )


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_legacy_additive_diagnostics_and_zero_pending(kind):
    book = run(
        kind,
        impact_model=None,
        impact_volumes=None,
        impact_price_basis=None,
        impact_volume_basis=None,
        transaction_cost_bps=10,
        slippage_bps=5,
    )
    previous_eq = book.equity_curve.shift(1).fillna(100)
    np.testing.assert_allclose(
        book.slippage_cost_series, book.slippage_costs * previous_eq
    )
    assert book.pending_trade_shares.eq(0).all().all()
    assert book.cancelled_trade_shares.eq(0).all().all()
    assert (
        book.trade_participation_rates.where(book.executed_trade_values.ne(0))
        .isna()
        .all()
        .all()
    )
    assert book.realized_slippage_bps.loc[book.turnover.gt(0)].eq(5).all()


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_anchor_terminal_retains_zero_evidence_with_active_impact(kind):
    prices, signals, volumes = panels()
    day = prices.index[3]
    prices.loc[day:, "SEC_A"] = np.nan
    volumes.loc[day:, "SEC_A"] = np.nan
    events = pd.DataFrame(
        [
            dict(
                event_id="anchor",
                permanent_id="SEC_A",
                effective_date=day,
                reference_date=prices.index[2],
                known_at=prices.index[2],
                terminal_return=-0.5,
                return_basis="prior_observed_close_to_cash",
            )
        ]
    )
    book = run(kind, prices, signals, volumes, terminal_events=events)
    assert len(book.terminal_event_log) == 1
    assert book.terminal_event_log[0]["incoming_weight"] == 0
    assert book.terminal_event_log[0]["cashflow"] == 0
    assert book.executed_trade_values["SEC_A"].eq(0).all()


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_single_row_impact_retains_existing_evaluation_refusal(kind):
    prices, signals, volumes = panels()
    with pytest.raises(ValueError, match="evaluation_"):
        run(kind, prices, signals, volumes, evaluation_end=prices.index[3])


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(missing_price_policy="zero_return"),
        dict(volume_aware_slippage_mode="apply_precomputed_impact"),
    ],
)
def test_long_only_ambiguous_impact_paths_refused(kwargs):
    with pytest.raises(MarketImpactValidationError, match="impact_input_ambiguous"):
        run("lo", **kwargs)


def test_impact_timing_ledger_describes_target_attempts_and_separate_retries():
    model = SquareRootImpactModel(
        lookback=2, min_adv=1, max_participation_rate=0.01, mode="throttle", eta=0
    )
    book = run("lo", impact_model=model)
    assert (
        book.timing_metadata["timing_ledger_scope"]
        == "scheduled_frozen_target_attempts"
    )
    phases = {
        row.execution_phase
        for row in book.timing_ledger
        if row.execution_phase is not None
    }
    assert phases == {"observed_source_row_close_frozen_target_attempt"}
    assert book.executed_trade_values.iloc[2].abs().sum() > 0


@pytest.mark.parametrize("terminal_row_only", [True, False])
@pytest.mark.parametrize("asset_count", [1, 2])
def test_public_long_only_all_assets_cash_reconciliation(
    terminal_row_only, asset_count
):
    """M45-R1: a fully invested all-buy book funds its fees exactly once."""
    dates = pd.bdate_range("2024-01-01", periods=6)
    columns = ["A", "B"][:asset_count]
    prices = pd.DataFrame(10.0, index=dates, columns=columns)
    signals = pd.DataFrame(
        [list(range(asset_count, 0, -1))] * len(dates), index=dates, columns=columns
    )
    book = run_long_only_backtest(
        prices,
        signals,
        source_provenance=capture_backtest_source_provenance(prices, signals),
        top_n=asset_count,
        initial_capital=100.0,
        evaluation_start=dates[3],
        evaluation_end=dates[4] if terminal_row_only else dates[5],
        rebalance_frequency="D",
        impact_model=SquareRootImpactModel(
            min_adv=1, eta=0, fixed_bps=100, max_participation_rate=1, lookback=2
        ),
        impact_volumes=prices * 10,
        impact_price_basis="raw",
        impact_volume_basis="raw",
    )
    expected_equity = 100 / 1.01
    assert book.equity_curve.loc[dates[4]] == pytest.approx(expected_equity, abs=1e-12)
    assert book.cash_balance.loc[dates[4]] == pytest.approx(0, abs=1e-12)
    assert book.slippage_cost_series.loc[dates[4]] == pytest.approx(
        expected_equity * 0.01, rel=1e-13
    )
    np.testing.assert_allclose(
        book.executed_trade_values.loc[dates[4]],
        expected_equity / asset_count,
        rtol=1e-13,
    )
    np.testing.assert_allclose(
        book.cash_balance + book.holdings.mul(book.equity_curve, axis=0).sum(axis=1),
        book.equity_curve,
        rtol=1e-13,
    )
    if not terminal_row_only:
        assert book.equity_curve.loc[dates[5]] == pytest.approx(
            expected_equity, abs=1e-12
        )
        assert book.cash_balance.loc[dates[5]] == pytest.approx(0, abs=1e-12)
        assert book.slippage_cost_series.loc[dates[5]] == pytest.approx(0, abs=1e-12)
