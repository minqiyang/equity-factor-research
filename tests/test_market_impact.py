"""Independent cost, causal liquidity, and self-financing execution oracles."""

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import brentq

from backtest.market_impact import (
    MarketImpactValidationError,
    MarketLiquidity,
    SquareRootImpactModel,
    calculate_market_impact,
    execute_impact_step,
    prepare_market_liquidity,
)


def quote(q, *, adv=1000.0, sigma=0.02, **kwargs):
    return calculate_market_impact(
        pd.Series(q, dtype=float),
        pd.Series(adv, index=range(len(q))),
        pd.Series(sigma, index=range(len(q))),
        model=SquareRootImpactModel(min_adv=1, **kwargs),
    )


@pytest.mark.parametrize("q", [0.0, 1e-12, 10.0, 100.0, -100.0])
def test_scalar_square_root_oracle(q):
    row = quote([q], eta=0.5, fixed_bps=3).iloc[0]
    expected = abs(q) * (0.0003 + 0.5 * 0.02 * np.sqrt(abs(q) / 1000))
    assert row.slippage_cost == pytest.approx(expected, rel=1e-14, abs=1e-25)
    assert row.executed_trade_value == q


def test_modes_and_quadratic_total_penalty():
    with pytest.raises(
        MarketImpactValidationError, match="impact_participation_exceeded"
    ):
        quote([200.0])
    throttled = quote([200.0, -200.0], mode="throttle", eta=0.5)
    np.testing.assert_array_equal(throttled.executed_trade_value, [100.0, -100.0])
    np.testing.assert_array_equal(throttled.remaining_trade_value, [100.0, -100.0])
    penalized = quote(
        [200.0, -200.0], mode="penalize", eta=0.5, fixed_bps=3, penalty_bps=7
    )
    expected = (
        200 * (0.0003 + 0.5 * 0.02 * np.sqrt(0.2))
        + 1000 * 0.0007 * (0.2 / 0.1 - 1) ** 2
    )
    np.testing.assert_allclose(penalized.slippage_cost, expected, rtol=1e-14)
    # Doubling excess participation quadruples the total dollar penalty.
    zero = dict(mode="penalize", eta=0, penalty_bps=7)
    assert quote([300.0], **zero).slippage_cost.iloc[0] == pytest.approx(
        4 * quote([200.0], **zero).slippage_cost.iloc[0]
    )


@pytest.mark.parametrize(
    "name,value",
    [
        ("eta", -1),
        ("eta", True),
        ("eta", np.inf),
        ("eta", 10**1000),
        ("fixed_bps", "1"),
        ("penalty_bps", np.nan),
        ("min_adv", 0),
        ("max_participation_rate", 0),
        ("max_participation_rate", 1.01),
        ("lookback", 1),
        ("lookback", True),
        ("lookback", 2.0),
        ("mode", "silent"),
    ],
)
def test_model_refuses_invalid_parameters(name, value):
    with pytest.raises(MarketImpactValidationError, match="impact_model_invalid"):
        SquareRootImpactModel(**{name: value})


@pytest.mark.parametrize("adv", [0, -1, np.nan, np.inf, True, "1000", 0.5])
def test_active_trade_adv_guard_and_zero_trade_skip(adv):
    with pytest.raises(MarketImpactValidationError, match="impact_adv_invalid"):
        calculate_market_impact(
            pd.Series([1.0]),
            pd.Series([adv]),
            pd.Series([0.02]),
            model=SquareRootImpactModel(min_adv=1),
        )
    assert (
        calculate_market_impact(
            pd.Series([0.0]),
            pd.Series([adv]),
            pd.Series([np.nan]),
            model=SquareRootImpactModel(min_adv=1),
        ).slippage_cost.iloc[0]
        == 0
    )


@pytest.mark.parametrize("sigma", [-1, np.nan, np.inf, True, ".02"])
def test_active_trade_volatility_guard(sigma):
    with pytest.raises(MarketImpactValidationError, match="impact_volatility_invalid"):
        calculate_market_impact(
            pd.Series([1.0]),
            pd.Series([1000.0]),
            pd.Series([sigma]),
            model=SquareRootImpactModel(min_adv=1),
        )


def test_zero_volatility_and_extreme_cost_refusal():
    assert quote([100.0], sigma=0, fixed_bps=4).slippage_cost.iloc[0] == pytest.approx(
        0.04
    )
    with pytest.raises(MarketImpactValidationError, match="impact_cost_invalid"):
        quote([100.0], sigma=1e308, eta=1e308)
    with pytest.raises(MarketImpactValidationError, match="impact_trade_invalid"):
        quote([np.inf])


def panels():
    dates = pd.bdate_range("2024-01-01", periods=10, name="close")
    prices = pd.DataFrame(
        {"A": [10.0, 11.0, 9.0, 12.0, 10.0, 13.0, 11.0, 14.0, 12.0, 15.0]}, index=dates
    )
    return prices, pd.DataFrame(100.0, index=dates, columns=prices.columns)


def prepare(prices, volumes, **kwargs):
    settings = dict(
        price_basis="raw",
        volume_basis="raw",
        signal_lag_periods=1,
        model=SquareRootImpactModel(lookback=2, min_adv=1),
    )
    settings.update(kwargs)
    return prepare_market_liquidity(prices, volumes, **settings)


def test_lagged_full_windows_ddof_one_and_future_prefix():
    prices, volumes = panels()
    result = prepare(prices, volumes)
    assert result.adv.iloc[2, 0] == 1050
    assert result.daily_volatility.iloc[2, 0] != result.daily_volatility.iloc[2, 0]
    assert result.daily_volatility.iloc[3, 0] == pytest.approx(
        np.std([0.1, 9 / 11 - 1], ddof=1)
    )
    p2, v2 = prices.copy(), volumes.copy()
    p2.iloc[5:] *= 17
    v2.iloc[5:] *= 500
    changed = prepare(p2, v2)
    pd.testing.assert_frame_equal(result.adv.iloc[:6], changed.adv.iloc[:6])
    pd.testing.assert_frame_equal(
        result.daily_volatility.iloc[:6], changed.daily_volatility.iloc[:6]
    )
    lag2 = prepare(prices, volumes, signal_lag_periods=2)
    pd.testing.assert_frame_equal(lag2.adv, result.adv.shift(1))


@pytest.mark.parametrize(
    "price_basis,volume_basis",
    [("raw", "split_adjusted"), ("total_return", "raw"), (None, None)],
)
def test_basis_guard(price_basis, volume_basis):
    with pytest.raises(MarketImpactValidationError, match="impact_basis_invalid"):
        prepare(*panels(), price_basis=price_basis, volume_basis=volume_basis)


@pytest.mark.parametrize("lag", [0, -1, True, 1.5])
def test_lag_guard(lag):
    with pytest.raises(MarketImpactValidationError, match="impact_lag_invalid"):
        prepare(*panels(), signal_lag_periods=lag)


@pytest.mark.parametrize("shape", [(0, 0), (3, 0), (0, 3)])
def test_panel_empty_axes_refused(shape):
    frame = pd.DataFrame(
        index=pd.date_range("2024-01-01", periods=shape[0]), columns=range(shape[1])
    )
    with pytest.raises(MarketImpactValidationError, match="impact_axes_invalid"):
        prepare(frame, frame)


def test_axes_duplicate_mismatch_and_mixed_identity():
    prices, volumes = panels()
    with pytest.raises(MarketImpactValidationError, match="impact_axes_invalid"):
        prepare(prices, volumes.iloc[::-1])
    for frame in (pd.concat([prices, prices], axis=1), pd.concat([prices, prices])):
        with pytest.raises(MarketImpactValidationError, match="impact_axes_invalid"):
            prepare(frame, frame)
    mixed = pd.Index(["001", 2], name="identity")
    q = pd.Series([10.0, -10.0], index=mixed)
    result = calculate_market_impact(
        q, q.abs() * 100, q.abs() * 0.002, model=SquareRootImpactModel(min_adv=1)
    )
    assert result.index.equals(mixed)
    empty = pd.Series([], dtype=float)
    assert calculate_market_impact(
        empty, empty, empty, model=SquareRootImpactModel()
    ).shape == (0, 5)
    with pytest.raises(MarketImpactValidationError, match="impact_axes_invalid"):
        calculate_market_impact(
            pd.Series([1.0, 2.0], index=["A", "A"]),
            empty,
            empty,
            model=SquareRootImpactModel(),
        )


def step(
    *,
    model=None,
    position=(0.0, 0.0),
    target=(1.0, 0.0),
    cash=100.0,
    equity=100.0,
    pending=(0.0, 0.0),
    price=(10.0, 10.0),
    adv=(1000.0, 1000.0),
    sigma=(0.02, 0.02),
    observed=(100.0, 100.0),
    eligible=None,
    settled=None,
    fee=0.0,
):
    assets = pd.Index(["A", "B"])
    date = pd.Timestamp("2024-01-10")

    def vector(x):
        return pd.Series(x, index=assets, dtype=float)

    def frame(x):
        return pd.DataFrame([x], index=[date], columns=assets)

    return execute_impact_step(
        model=model or SquareRootImpactModel(min_adv=1, max_participation_rate=1),
        liquidity=MarketLiquidity(frame(adv), frame(sigma), frame(observed)),
        date=date,
        execution_prices=vector(price),
        position_values=vector(position),
        cash=cash,
        equity_before=equity,
        target_weights=None if target is None else vector(target),
        pending_shares=vector(pending),
        eligible=eligible,
        settled=settled or set(),
        transaction_cost_bps=fee,
    )


def test_initial_cash_funding_independent_root_and_cost_accounting():
    model = SquareRootImpactModel(
        eta=0.5, fixed_bps=10, min_adv=1, max_participation_rate=1
    )
    result = step(model=model, fee=20)

    def scalar_cost(q):
        return q * (0.001 + 0.5 * 0.02 * np.sqrt(q / 1000))

    expected_q = brentq(
        lambda q: q + q * 0.002 + scalar_cost(q) - 100, 0, 100, xtol=1e-12
    )
    assert result.executed_trade_values.A == pytest.approx(expected_q, abs=1e-12)
    assert result.cash >= 0
    assert result.cash < 1e-12
    assert result.slippage_cost == pytest.approx(scalar_cost(expected_q))
    assert result.commission == pytest.approx(expected_q * 0.002)
    assert result.cancelled_trade_shares.A == pytest.approx((100 - expected_q) / 10)
    assert result.pending_trade_shares.eq(0).all()
    assert result.position_values.sum() + result.cash == pytest.approx(
        100 - result.commission - result.slippage_cost
    )


def test_sells_fund_common_buy_scale_and_sign_symmetry():
    result = step(
        target=(-0.5, 1.5),
        model=SquareRootImpactModel(min_adv=1, max_participation_rate=1),
        fee=10,
    )
    assert result.executed_trade_values.A == -50
    assert result.executed_trade_values.B < 150
    assert result.position_values.sum() + result.cash == pytest.approx(
        100 - result.commission - result.slippage_cost
    )


def test_throttle_share_carry_price_change_replacement_and_terminal_cancel():
    model = SquareRootImpactModel(
        min_adv=1, max_participation_rate=0.01, mode="throttle", eta=0
    )
    first = step(model=model)
    assert first.executed_trade_values.A == 10
    assert first.pending_trade_shares.A == 9
    retry = step(
        model=model,
        position=(20.0, 0.0),
        cash=90,
        equity=110,
        target=None,
        pending=(9.0, 0.0),
        price=(20.0, 10.0),
    )
    assert retry.executed_trade_values.A == 10
    assert retry.pending_trade_shares.A == 8.5
    replaced = step(model=model, target=(0.0, 1.0), pending=(9.0, 0.0))
    assert replaced.cancelled_trade_shares.A == 9
    terminal = step(
        model=model,
        target=None,
        pending=(9.0, 0.0),
        price=(np.nan, 10.0),
        settled={"A"},
    )
    assert terminal.cancelled_trade_shares.A == 9
    assert terminal.executed_trade_values.eq(0).all()
    assert terminal.pending_trade_shares.eq(0).all()


def test_known_ineligibility_allows_only_exposure_reduction():
    eligibility = pd.Series(False, index=["A", "B"])
    result = step(
        target=None, position=(20.0, -20.0), pending=(-4.0, 4.0), eligible=eligibility
    )
    np.testing.assert_allclose(result.executed_trade_values, [-20, 20])
    np.testing.assert_allclose(result.cancelled_trade_shares, [-2, 2])
    result = step(target=None, pending=(4.0, -4.0), eligible=eligibility)
    assert result.executed_trade_values.eq(0).all()
    np.testing.assert_allclose(result.cancelled_trade_shares, [4, -4])


@pytest.mark.parametrize("observed", [(0.0, 100.0), (np.nan, 100.0)])
def test_zero_current_volume_refuses_actual_fills(observed):
    with pytest.raises(
        MarketImpactValidationError, match="impact_execution_volume_invalid"
    ):
        step(observed=observed)
    assert step(target=(0.0, 0.0), observed=observed).executed_trade_values.eq(0).all()


def test_insolvent_sell_and_invalid_execution_price_refused():
    with pytest.raises(MarketImpactValidationError, match="impact_cash_insufficient"):
        step(target=(0.0, 0.0), position=(100.0, 0.0), cash=0, fee=20000)
    with pytest.raises(
        MarketImpactValidationError, match="impact_execution_price_invalid"
    ):
        step(price=(np.nan, 10.0))
    with pytest.raises(MarketImpactValidationError, match="impact_portfolio_insolvent"):
        step(
            target=(-1.0, 0.0),
            model=SquareRootImpactModel(
                min_adv=1, max_participation_rate=1, fixed_bps=15000
            ),
        )


def test_common_buy_scale_preserves_proportions():
    result = step(target=(0.25, 0.75), adv=(1000, 2000), sigma=(0.04, 0.01), fee=10)
    assert (
        result.executed_trade_values.B / result.executed_trade_values.A
        == pytest.approx(3)
    )
    assert result.cash >= 0


def test_complete_liquidity_window_rejects_invalid_cells_without_flooring():
    p, v = panels()
    v.iloc[1, 0] = np.nan
    result = prepare(p, v)
    assert np.isnan(result.adv.iloc[3, 0])
    assert np.isfinite(result.adv.iloc[4, 0])
    v[:] = 0
    assert prepare(p, v).adv.iloc[3, 0] == 0
    adjusted = prepare(
        p, v, price_basis="split_adjusted", volume_basis="split_adjusted"
    )
    assert adjusted.adv.iloc[3, 0] == 0
    assert replace(SquareRootImpactModel(), eta=0).eta == 0


def test_cash_and_position_input_balance_refused():
    with pytest.raises(MarketImpactValidationError, match="impact_accounting_invalid"):
        step(position=(50.0, 0.0), cash=100.0, equity=100.0)


def test_penalized_buy_funding_recomputes_cost_at_actual_size():
    model = SquareRootImpactModel(
        min_adv=1,
        max_participation_rate=0.01,
        mode="penalize",
        eta=0.5,
        fixed_bps=3,
        penalty_bps=20,
    )
    result = step(model=model, fee=7)

    def impact(q):
        return (
            q * (0.0003 + 0.5 * 0.02 * np.sqrt(q / 1000))
            + 1000 * 0.002 * max(q / 10 - 1, 0) ** 2
        )

    expected = brentq(lambda q: q + q * 0.0007 + impact(q) - 100, 0, 100)
    assert result.executed_trade_values.A == pytest.approx(expected, rel=1e-13)
    assert result.slippage_cost == pytest.approx(impact(expected), rel=1e-13)
    assert result.pending_trade_shares.eq(0).all()


def test_massive_trade_throttled_and_boolean_trade_refused():
    assert quote([1e250], mode="throttle").executed_trade_value.iloc[0] == 100
    with pytest.raises(MarketImpactValidationError, match="impact_trade_invalid"):
        calculate_market_impact(
            pd.Series([True]),
            pd.Series([1000]),
            pd.Series([0.02]),
            model=SquareRootImpactModel(min_adv=1),
        )
