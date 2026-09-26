"""M4.7 stage a-0 Family A factor and long-run variance oracles (T-REG-4, T-REG-5)."""

import math

import numpy as np
import pandas as pd
import pytest

from features.diagnostics import (
    mde_from_long_run_variance,
    newey_west_long_run_variance,
    newey_west_mean_tstat,
)
from features.liquidity import calculate_amihud_illiquidity
from features.momentum import calculate_52_week_high_proximity
from features.volatility import calculate_rolling_market_beta
from research.m4_7_family_a import FAMILY_A, FAMILY_A_IDS, FAMILY_A_SIZE, family_a_signals, simple_returns
from research.m4_7_sp500_pit_rerun import Z_EFF, Z_SINGLE, ic_minimum_detectable_effect, split_halves


ROWS = 600


def calendar(rows=ROWS):
    return pd.bdate_range("2020-01-01", periods=rows, name="date")


def growth_panel(columns=("FULL",)):
    index = calendar()
    base = 100.0 * np.exp(0.001 * np.arange(ROWS))
    return pd.DataFrame({column: base for column in columns}, index=index)


def market_series(index):
    rng = np.random.default_rng(20260925)
    return pd.Series(100.0 * np.cumprod(1.0 + rng.normal(0.0, 0.01, len(index))), index=index)


def test_family_a_definitions_are_frozen():
    assert FAMILY_A_IDS == ("MOM_12_1", "HIGH_52W", "REV_1M", "LOW_VOL_252", "LOW_BETA_252", "AMIHUD_ILLIQ_63")
    assert tuple(f.warmup_rows for f in FAMILY_A) == (252, 251, 21, 252, 252, 63)
    assert {f.direction for f in FAMILY_A} == {"higher_is_better"}
    assert FAMILY_A_SIZE == 6
    with pytest.raises(TypeError):
        FAMILY_A[0].parameters["lookback_periods"] = 1


def test_t_reg_4_first_finite_row_equals_first_bar_plus_warmup():
    prices = growth_panel(("FULL", "NEW"))
    prices.iloc[:300, 1] = np.nan
    dollar_volume = pd.DataFrame(1e6, index=prices.index, columns=prices.columns).where(prices.notna())
    s_mask = pd.DataFrame(True, index=prices.index, columns=prices.columns)
    signals = family_a_signals(prices, market_series(prices.index), dollar_volume, s_mask)
    first_finite = {factor_id: signals[factor_id]["NEW"].first_valid_index() for factor_id in FAMILY_A_IDS}
    assert {k: prices.index.get_loc(v) for k, v in first_finite.items()} == {
        f.factor_id: 300 + f.warmup_rows for f in FAMILY_A
    }
    assert signals["MOM_12_1"]["FULL"].iloc[300] == pytest.approx(0.2598592394492314, abs=1e-15)
    assert signals["REV_1M"]["FULL"].iloc[300] == pytest.approx(-0.02122205163752855, abs=1e-15)
    for factor_id in FAMILY_A_IDS:
        assert signals[factor_id]["FULL"].iloc[300:].notna().all(), factor_id


def test_t_reg_4_every_signal_is_missing_where_s_mask_is_false():
    prices = growth_panel(("A", "B"))
    s_mask = pd.DataFrame(True, index=prices.index, columns=prices.columns)
    s_mask.iloc[400:450, 0] = False
    s_mask.iloc[::7, 1] = False
    dollar_volume = pd.DataFrame(1e6, index=prices.index, columns=prices.columns)
    signals = family_a_signals(prices, market_series(prices.index), dollar_volume, s_mask)
    for factor_id, signal in signals.items():
        assert signal.where(~s_mask).isna().all().all(), factor_id
        assert signal.iloc[500:].notna().where(s_mask.iloc[500:], True).all().all(), factor_id


def test_t_reg_4_high_52w_golden_at_known_maximum():
    prices = pd.DataFrame({"A": 100.0}, index=calendar())
    prices.iloc[350, 0] = 150.0
    high = calculate_52_week_high_proximity(prices)
    assert high["A"].iloc[:251].isna().all()
    assert high["A"].iloc[251] == 1.0
    assert high["A"].iloc[350] == 1.0
    assert high["A"].iloc[400] == pytest.approx(100.0 / 150.0, abs=1e-15)
    assert high["A"].iloc[599] == pytest.approx(100.0 / 150.0, abs=1e-15)
    gapped = prices.copy()
    gapped.iloc[400, 0] = np.nan
    assert calculate_52_week_high_proximity(gapped)["A"].iloc[400:].isna().all()


def test_t_reg_4_low_beta_golden_on_constructed_beta_two_series():
    index = calendar()
    market = market_series(index)
    market_returns = simple_returns(market)
    asset = pd.Series(100.0 * np.cumprod(1.0 + 2.0 * market_returns.fillna(0.0)), index=index)
    returns = simple_returns(pd.DataFrame({"A": asset}))
    beta = calculate_rolling_market_beta(returns, market_returns)
    assert beta["A"].iloc[:252].isna().all()
    np.testing.assert_allclose(beta["A"].iloc[252:], 2.0, rtol=0, atol=1e-10)
    s_mask = pd.DataFrame(True, index=index, columns=["A"])
    signals = family_a_signals(pd.DataFrame({"A": asset}), market, pd.DataFrame({"A": 1e6}, index=index), s_mask)
    np.testing.assert_allclose(signals["LOW_BETA_252"]["A"].iloc[252:], -2.0, rtol=0, atol=1e-10)


def test_rolling_beta_matches_numpy_reference_and_refuses_bad_market():
    index = calendar(300)
    rng = np.random.default_rng(7)
    market_returns = pd.Series(rng.normal(0, 0.01, 300), index=index)
    returns = pd.DataFrame({"A": 0.5 * market_returns + rng.normal(0, 0.01, 300)}, index=index)
    beta = calculate_rolling_market_beta(returns, market_returns, window=252)
    t = 280
    window = slice(t - 251, t + 1)
    x, y = market_returns.iloc[window].to_numpy(), returns["A"].iloc[window].to_numpy()
    expected = np.cov(y, x, ddof=1)[0, 1] / np.var(x, ddof=1)
    assert beta["A"].iloc[t] == pytest.approx(expected, abs=1e-12)
    for level in (0.0, 0.001):
        flat = pd.Series(level, index=index)
        assert calculate_rolling_market_beta(returns, flat, window=252).isna().all().all()
    with pytest.raises(ValueError):
        calculate_rolling_market_beta(returns, market_returns.iloc[1:], window=252)
    with pytest.raises(ValueError):
        calculate_rolling_market_beta(returns, market_returns, window=1)


def test_t_reg_4_amihud_golden_on_constant_returns_and_volume():
    index = calendar()
    prices = pd.DataFrame({"A": 100.0 * 1.01 ** np.arange(ROWS)}, index=index)
    dollar_volume = pd.DataFrame({"A": 2e6}, index=index)
    amihud = calculate_amihud_illiquidity(simple_returns(prices), dollar_volume)
    assert amihud["A"].iloc[:63].isna().all()
    np.testing.assert_allclose(amihud["A"].iloc[63:], 0.01 / 2e6, rtol=1e-12, atol=0)
    zero = dollar_volume.copy()
    zero.iloc[200, 0] = 0.0
    missing = calculate_amihud_illiquidity(simple_returns(prices), zero)["A"]
    assert missing.iloc[200:263].isna().all() and missing.iloc[263:].notna().all()
    with pytest.raises(ValueError):
        calculate_amihud_illiquidity(simple_returns(prices), dollar_volume.iloc[1:])
    with pytest.raises(ValueError):
        calculate_amihud_illiquidity(simple_returns(prices), -dollar_volume)


def test_interior_missing_bar_losses_match_the_registered_counts():
    prices = growth_panel(("GAP",))
    prices.iloc[400, 0] = np.nan
    s_mask = pd.DataFrame(True, index=prices.index, columns=prices.columns)
    signals = family_a_signals(prices, market_series(prices.index), pd.DataFrame(1e6, index=prices.index,
                                                                                 columns=prices.columns), s_mask)
    missing_rows = {k: np.flatnonzero(v["GAP"].iloc[252:].isna().to_numpy()) + 252 for k, v in signals.items()}
    assert missing_rows["MOM_12_1"].tolist() == [421]
    assert missing_rows["REV_1M"].tolist() == [400, 421]
    assert missing_rows["LOW_VOL_252"].tolist() == list(range(400, ROWS))
    assert missing_rows["LOW_BETA_252"].tolist() == list(range(400, ROWS))
    assert missing_rows["HIGH_52W"].tolist() == list(range(400, ROWS))
    assert missing_rows["AMIHUD_ILLIQ_63"].tolist() == list(range(400, 464))


def test_t_reg_5_mde_goldens():
    assert mde_from_long_run_variance(0.136 ** 2, 240, Z_EFF) == pytest.approx(0.033101, abs=1e-6)
    assert mde_from_long_run_variance(0.136 ** 2, 240, Z_SINGLE) == pytest.approx(0.024595, abs=1e-6)
    assert Z_EFF == pytest.approx(3.7705, abs=1e-4)
    assert Z_SINGLE == pytest.approx(2.8016, abs=1e-4)
    for lrv in (0.0, -1.0, math.nan, math.inf):
        assert math.isnan(mde_from_long_run_variance(lrv, 240, Z_EFF))
    assert math.isnan(mde_from_long_run_variance(0.01, 0, Z_EFF))


def test_t_reg_5_long_run_variance_matches_numpy_reference():
    rng = np.random.default_rng(240)
    shocks = rng.normal(0.0, 0.1, 241)
    series = shocks[1:] + 0.4 * shocks[:-1]
    residual = series - series.mean()
    count, lags = len(series), 4
    gammas = [residual[k:] @ residual[:count - k] / count for k in range(lags + 1)]
    reference = gammas[0] + 2.0 * sum((1.0 - k / (lags + 1.0)) * gammas[k] for k in range(1, lags + 1))
    assert newey_west_long_run_variance(series, lags) == pytest.approx(reference, abs=1e-12)
    assert newey_west_long_run_variance(pd.Series(series), lags) == pytest.approx(reference, abs=1e-12)
    tstat = newey_west_mean_tstat(pd.Series(series), lags=lags)
    assert tstat == pytest.approx(series.mean() / math.sqrt(reference / count), abs=1e-12)


def test_t_reg_5_long_run_variance_undefined_and_refusals():
    assert math.isnan(newey_west_long_run_variance(np.full(240, 0.05), 4))
    assert math.isnan(newey_west_long_run_variance(np.array([], dtype=float), 0))
    with pytest.raises(ValueError, match="finite"):
        newey_west_long_run_variance(np.array([0.1, np.nan, 0.2]), 1)
    with pytest.raises(ValueError, match="lags"):
        newey_west_long_run_variance(np.array([0.1, 0.2]), -1)
    with pytest.raises(ValueError, match="lags"):
        newey_west_long_run_variance(np.array([0.1, 0.2]), True)


def test_t_reg_5_halves_and_ic_mde():
    first, second = split_halves(pd.Series(np.arange(241.0)))
    assert (len(first), len(second)) == (121, 120)
    assert first.iloc[-1] == 120.0 and second.iloc[0] == 121.0
    rng = np.random.default_rng(3)
    ic = pd.Series(rng.normal(0.02, 0.1, 240))
    mde_f, mde_single = ic_minimum_detectable_effect(ic)
    lags = int(np.floor(4 * (240 / 100) ** (2 / 9)))
    lrv = newey_west_long_run_variance(ic, lags)
    assert mde_f == pytest.approx(Z_EFF * math.sqrt(lrv / 240), abs=1e-15)
    assert mde_single == pytest.approx(Z_SINGLE * math.sqrt(lrv / 240), abs=1e-15)
    assert ic_minimum_detectable_effect(ic.iloc[:31]) == (None, None)
    assert all(value is not None for value in ic_minimum_detectable_effect(ic.iloc[:32]))
    assert ic_minimum_detectable_effect(pd.Series(np.full(120, 0.03))) == (None, None)
