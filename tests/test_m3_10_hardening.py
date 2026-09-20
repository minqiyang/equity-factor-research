"""Synthetic regression oracles for audit M01--M11 and Appendices A/B."""
import json

import numpy as np
import pandas as pd
import pytest

from backtest.long_short import run_long_short_backtest
from backtest.portfolio import capture_backtest_source_provenance, run_long_only_backtest
from data.constituent_table import build_membership_mask, load_constituent_intervals_csv
from features.diagnostics import deflated_sharpe_ratio
from features.regime import regime_switching_factor_composite
import research.multifactor_diagnostic_mvp as m


def panels(n=8, assets=4):
    dates = pd.bdate_range('2025-01-06', periods=n)
    prices = pd.DataFrame(100., index=dates, columns=list('ABCD')[:assets])
    signals = pd.DataFrame(np.tile(np.arange(assets, 0, -1, dtype=float), (n, 1)),
                           index=dates, columns=prices.columns)
    return prices, signals


def run_book(kind, prices, signals, **kwargs):
    if kind == 'ls':
        return run_long_short_backtest(prices, signals, quantiles=2, **kwargs)
    return run_long_only_backtest(
        prices, signals, source_provenance=capture_backtest_source_provenance(prices, signals),
        evaluation_start=prices.index[0], evaluation_end=prices.index[-1], top_n=2, **kwargs)


def holdings(kind, book):
    return book.net_holdings if kind == 'ls' else book.holdings


@pytest.mark.parametrize('kind', ['lo', 'ls'])
@pytest.mark.parametrize('lag', [1, 2, 3])
@pytest.mark.parametrize('frequency,execution', [('D', 5), ('W-FRI', 9)])
def test_m02_frozen_smoothing_execution_and_future_price_invariance(kind, lag, frequency, execution):
    prices, signals = panels(n=20)
    signals.iloc[4::2] = signals.iloc[0].to_numpy()[::-1]
    changed = prices.copy()
    changed.iloc[execution:, 0] = 200.
    kwargs = dict(rebalance_frequency=frequency, signal_lag_periods=lag, turnover_penalty_lambda=.5)
    before = run_book(kind, prices, signals, **kwargs)
    after = run_book(kind, changed, signals, **kwargs)
    pd.testing.assert_frame_equal(holdings(kind, before).iloc[:execution + 1],
                                  holdings(kind, after).iloc[:execution + 1])


@pytest.mark.parametrize('penalty', [0., .25, .5, .75, .999999])
@pytest.mark.parametrize('partial', [False, True])
def test_m03_netted_exposure_full_and_partial_reversal(penalty, partial):
    prices, signals = panels()
    signals.iloc[1::2] = [4., 1., 3., 2.] if partial else [1., 2., 3., 4.]
    result = run_book('ls', prices, signals, rebalance_frequency='D', turnover_penalty_lambda=penalty)
    np.testing.assert_allclose(result.net_holdings.abs().sum(axis=1).iloc[1:], 1., atol=1e-5)
    np.testing.assert_allclose(result.net_holdings.sum(axis=1), 0., atol=1e-5)
    assert (result.long_holdings * result.short_holdings).eq(0.).all().all()
    pd.testing.assert_frame_equal(result.long_holdings - result.short_holdings, result.net_holdings)


@pytest.mark.parametrize('bad', [np.nan, 0., -1., np.inf, -np.inf, True, 'bad', 1j])
@pytest.mark.parametrize('frequency', ['D', '2B'])
@pytest.mark.parametrize('liquidate', [False, True])
def test_m04_held_price_disappearance_refuses(bad, frequency, liquidate):
    prices, signals = panels(n=8, assets=2)
    # Both schedules execute at row 1; row 2 intervenes between 2B rebalances.
    prices = prices.astype(object)
    prices.iloc[2, 0] = bad
    if liquidate:
        signals.iloc[1:] = np.nan
    with pytest.raises(ValueError, match='incoming_price_invalid'):
        run_book('ls', prices, signals, rebalance_frequency=frequency)


@pytest.mark.parametrize('bad', [np.nan, 0., -1., np.inf, True, 'bad', 1j])
def test_m04_invalid_initial_execution_price_refuses(bad):
    prices, signals = panels(assets=2)
    prices = prices.astype(object)
    prices.iloc[1, 0] = bad
    with pytest.raises(ValueError, match='execution_price_invalid'):
        run_book('ls', prices, signals, rebalance_frequency='D')


@pytest.mark.parametrize('price', [300., 400.])
def test_m04_pretrade_insolvency_refuses(price):
    prices, signals = panels(assets=2)
    prices.iloc[2:, 1] = price
    with pytest.raises(ValueError, match='portfolio_insolvent_or_non_finite_before_trade'):
        run_book('ls', prices, signals, rebalance_frequency='D')


@pytest.mark.parametrize('bps', [10000., 20000., 1e308])
def test_m04_postcost_insolvency_refuses(bps):
    prices, signals = panels(assets=2)
    with pytest.raises(ValueError, match='portfolio_insolvent_or_non_finite_after_costs'):
        run_book('ls', prices, signals, rebalance_frequency='D', transaction_cost_bps=bps)


@pytest.mark.parametrize('kind', ['lo', 'ls'])
@pytest.mark.parametrize('asset_price,gross', [(120., .1), (80., -.1)])
def test_m05_rebalance_cost_hand_oracle(kind, asset_price, gross):
    prices, signals = panels(assets=2)
    prices.iloc[2:, 0] = asset_price
    result = run_book(kind, prices, signals, rebalance_frequency='D', transaction_cost_bps=100., slippage_bps=50.)
    # Equal .5 positions drift to .6/1.1 and .5/1.1 (short sign for LS).
    expected_turnover = .1 / (1. + gross)
    assert result.gross_returns.iloc[2] == pytest.approx(gross)
    assert result.turnover.iloc[2] == pytest.approx(expected_turnover)
    assert result.transaction_costs.iloc[2] == pytest.approx(.001)
    assert result.slippage_costs.iloc[2] == pytest.approx(.0005)
    assert result.returns.iloc[2] == pytest.approx(gross - .0015)


@pytest.mark.parametrize('kind,gross,turnover,cost', [('lo', 1., 1., .02), ('ls', 0., 2., .02)])
def test_m05_liquidation_uses_drifted_weights(kind, gross, turnover, cost):
    prices, signals = panels(assets=2)
    prices.iloc[2:] = 200.
    signals.iloc[1] = np.nan
    result = run_book(kind, prices, signals, rebalance_frequency='D', transaction_cost_bps=100., turnover_penalty_lambda=.5)
    assert result.gross_returns.iloc[2] == pytest.approx(gross)
    assert result.turnover.iloc[2] == pytest.approx(turnover)
    assert result.transaction_costs.iloc[2] == pytest.approx(cost)
    assert holdings(kind, result).iloc[2].eq(0.).all()


@pytest.mark.parametrize('kind', ['lo', 'ls'])
@pytest.mark.parametrize('mask_mode', ['gap', 'exclude', 'all_excluded'])
def test_m06_final_eligibility_after_smoothing(kind, mask_mode):
    prices, signals = panels()
    mask = pd.DataFrame(True, index=prices.index, columns=prices.columns)
    if mask_mode == 'gap':
        mask = mask.iloc[:1]
    elif mask_mode == 'exclude':
        mask.loc[prices.index[3]:, 'A'] = False
    else:
        mask.iloc[3:] = False
    result = run_book(kind, prices, signals, rebalance_frequency='D', universe_mask=mask, turnover_penalty_lambda=.5)
    final = holdings(kind, result).iloc[3:]
    if mask_mode == 'exclude':
        assert final.A.eq(0.).all()
    else:
        assert final.eq(0.).all().all()


def test_m06_long_only_cap_after_smoothing():
    prices, signals = panels()
    prices.iloc[3:, 0] = 200.
    result = run_book('lo', prices, signals, rebalance_frequency='D', turnover_penalty_lambda=.5, max_position_weight=.4)
    assert result.holdings.le(.4 + 1e-12).all().all()


def test_m06_long_short_final_cap_feasible_or_refused():
    prices, signals = panels()
    feasible = run_book('ls', prices, signals, rebalance_frequency='D', turnover_penalty_lambda=.5, max_position_weight=.25)
    assert feasible.net_holdings.abs().le(.25 + 1e-12).all().all()
    # Removing one long asset leaves a net target with a .5 position.
    mask = pd.DataFrame(True, index=prices.index, columns=prices.columns)
    mask.iloc[3:, 0] = False
    with pytest.raises(ValueError, match='position_cap_infeasible'):
        run_book('ls', prices, signals, rebalance_frequency='D', turnover_penalty_lambda=.5, max_position_weight=.25, universe_mask=mask)


@pytest.mark.parametrize('kind', ['lo', 'ls'])
@pytest.mark.parametrize('bad', [np.nan, np.inf, True, -.1, 1.])
def test_penalty_finite_domain(kind, bad):
    prices, signals = panels()
    with pytest.raises(ValueError, match='turnover_penalty_lambda'):
        run_book(kind, prices, signals, turnover_penalty_lambda=bad)


@pytest.mark.parametrize('second_start', ['2021-01-01', '2022-01-01'])
def test_m07_permanent_identity_and_ambiguous_reuse(tmp_path, second_start):
    path = tmp_path / 'identities.csv'
    text = f'symbol,start_date,end_date,permanent_id\nXYZ,2020-01-01,2021-01-01,SECURITY_A\nXYZ,{second_start},2023-01-01,SECURITY_B\n'
    path.write_text(text)
    table = load_constituent_intervals_csv(path)
    dates = pd.DatetimeIndex(['2020-06-01', '2022-06-01'])
    mask = build_membership_mask(table, dates)
    assert list(mask.columns) == ['SECURITY_A', 'SECURITY_B']
    assert mask.values.tolist() == [[True, False], [False, True]]
    with pytest.raises(ValueError, match='PIT-005'):
        build_membership_mask(table, dates, assets=['XYZ'])
    with pytest.raises(ValueError, match='PIT-005'):
        build_membership_mask(table.data.drop(columns='permanent_id'), dates)
    path.write_text(text.replace(',permanent_id', '').replace(',SECURITY_A', '').replace(',SECURITY_B', ''))
    with pytest.raises(ValueError, match='PIT-005'):
        load_constituent_intervals_csv(path)


def test_m07_same_security_reentry(tmp_path):
    path = tmp_path / 'reentry.csv'
    path.write_text('symbol,start_date,end_date,permanent_id\nXYZ,2020-01-01,2021-01-01,S1\nXYZ,2022-01-01,2023-01-01,S1\n')
    mask = build_membership_mask(load_constituent_intervals_csv(path), pd.DatetimeIndex(['2020-06-01', '2021-06-01', '2022-06-01']))
    assert mask.S1.tolist() == [True, False, True]


@pytest.mark.parametrize('variance,expected', [(.0001, .9999929565), (.01, .3726006190)])
def test_m08_appendix_a_paper_numeric_oracle(variance, expected):
    returns = pd.Series(np.random.default_rng(911).normal(.002, .01, 500))
    assert deflated_sharpe_ratio(returns, n_trials=62, trial_sharpe_variance=variance) == pytest.approx(expected, abs=5e-10)


@pytest.mark.parametrize('variance', [-.1, np.nan, np.inf, True, '0.1'])
def test_m08_variance_domain(variance):
    with pytest.raises(ValueError, match='trial_sharpe_variance'):
        deflated_sharpe_ratio(pd.Series([.1, -.1, .2]), n_trials=2, trial_sharpe_variance=variance)


@pytest.mark.parametrize('lag', [-1, 0, True, False, 1., 1.5, '1', np.nan])
def test_m10_lag_domain(lag):
    _, signals = panels()
    with pytest.raises(ValueError, match='signal_lag_periods'):
        regime_switching_factor_composite(signals, -signals, pd.Series(0., index=signals.index), signal_lag_periods=lag)


@pytest.mark.parametrize('mutation', ['duplicate', 'unsorted', 'misaligned', 'infinite', 'out_of_range'])
def test_m10_regime_axes_and_range(mutation):
    _, low = panels()
    high = -low
    indicator = pd.Series(0., index=low.index)
    if mutation == 'duplicate':
        low.index = high.index = indicator.index = pd.DatetimeIndex([low.index[0]] * len(low))
    elif mutation == 'unsorted':
        low, high, indicator = low.iloc[::-1], high.iloc[::-1], indicator.iloc[::-1]
    elif mutation == 'misaligned':
        indicator = indicator.iloc[:-1]
    else:
        indicator.iloc[2] = np.inf if mutation == 'infinite' else 2.
    with pytest.raises(ValueError):
        regime_switching_factor_composite(low, high, indicator)


def test_m11_missing_and_selected_parent_evidence():
    prices, low = panels()
    absent = low * np.nan
    indicator = pd.Series(0., index=low.index)
    output = regime_switching_factor_composite(absent, absent, indicator)
    assert output.isna().all().all()
    result = run_book('ls', prices, output, rebalance_frequency='D')
    assert result.net_holdings.eq(0.).all().all()
    # Missing unselected evidence has no effect on a binary selection.
    expected = low.sub(low.mean(axis=1), axis=0).div(low.std(axis=1), axis=0)
    pd.testing.assert_frame_equal(regime_switching_factor_composite(low, absent, indicator), expected)
    high_only = regime_switching_factor_composite(absent, low, indicator + 1.)
    pd.testing.assert_frame_equal(high_only.iloc[1:], expected.iloc[1:])
    assert regime_switching_factor_composite(low, absent, indicator + .5).iloc[1:].isna().all().all()
    low.iloc[2, 0] = np.nan
    low.iloc[3] = 7.
    partial = regime_switching_factor_composite(low, absent, indicator)
    assert pd.isna(partial.iloc[2, 0])
    assert partial.iloc[2, 1:].notna().all()
    assert partial.iloc[3].eq(0.).all()


def test_m09_failed_trials_are_retained(tmp_path, monkeypatch):
    prices, signals = panels()
    inventory = []
    log = tmp_path / 'attempts.jsonl'
    def fail(**kwargs):
        raise ValueError('synthetic refusal')
    monkeypatch.setattr(m, 'run_long_short_backtest', fail)
    with pytest.raises(ValueError, match='synthetic refusal'):
        m._run_recorded_trial(factor_id='F', direction='long_short', inventory=inventory,
                              inventory_path=log, trial_context={'estimator_version': 'test'},
                              prices=prices, signals=signals)
    events = [json.loads(line) for line in log.read_text().splitlines()]
    assert [event['status'] for event in events] == ['started', 'failed']
    assert inventory[0]['status'] == 'failed'
    assert m._trial_family_summary(inventory, n_trials=None)['trial_sharpe_variance'] is None


def test_m09_counts_variance_deduplication_and_override():
    inventory = [{'trial_id': str(i), 'status': 'completed', 'sharpe': sr}
                 for i, sr in enumerate([-.2, .1, .4])]
    summary = m._trial_family_summary(inventory + [inventory[0]], n_trials=None)
    assert summary['distinct_trial_count'] == 3
    assert summary['attempt_count'] == 4
    assert summary['trial_sharpe_variance'] == pytest.approx(.09)
    with pytest.raises(ValueError, match='distinct evaluated'):
        m._trial_family_summary(inventory, n_trials=2)
    assert m._trial_family_summary(inventory, n_trials=8)['n_trials_for_dsr'] == 8


def test_m01_integrated_future_labels_and_prices_prefix_invariance(tmp_path, monkeypatch):
    # A compact synthetic search retains every composite/descendant and both books.
    manifest = json.loads(m.DEFAULT_MANIFEST_PATH.read_text())
    manifest['generation']['periods'] = 420
    manifest_path = tmp_path / 'cohort.json'
    manifest_path.write_text(json.dumps(manifest))
    monkeypatch.setattr(m, 'ALPHA_IDS', (m.ALPHA_016, m.ALPHA_022, m.ALPHA_003))
    config = m.MultifactorDiagnosticConfig(manifest_path=manifest_path, warmup_periods=40, forward_holding_periods=5)
    baseline = m.run_multifactor_diagnostic_mvp(config=config, write_outputs=False)
    original_labels = m.execution_aligned_forward_returns
    def changed_labels(*args, **kwargs):
        labels = original_labels(*args, **kwargs)
        labels.iloc[330:] *= -1.
        return labels
    monkeypatch.setattr(m, 'execution_aligned_forward_returns', changed_labels)
    labels_changed = m.run_multifactor_diagnostic_mvp(config=config, write_outputs=False)
    monkeypatch.setattr(m, 'execution_aligned_forward_returns', original_labels)
    original_loader = m.load_diagnostic_cohort_ohlcv
    def changed_prices(*args, **kwargs):
        metadata, panel = original_loader(*args, **kwargs)
        for key in ['open', 'high', 'low', 'close', 'vwap']:
            panel[key].iloc[330:, 0] *= 1.5
        panel['returns'] = panel['close'].pct_change(fill_method=None)
        return metadata, panel
    monkeypatch.setattr(m, 'load_diagnostic_cohort_ohlcv', changed_prices)
    prices_changed = m.run_multifactor_diagnostic_mvp(config=config, write_outputs=False)
    for factor_id, payload in baseline['factors'].items():
        for changed in [labels_changed, prices_changed]:
            other = changed['factors'][factor_id]
            pd.testing.assert_frame_equal(payload['factor'].iloc[:300], other['factor'].iloc[:300])
            pd.testing.assert_frame_equal(payload['backtest'].holdings.iloc[:250], other['backtest'].holdings.iloc[:250])
            pd.testing.assert_frame_equal(payload['long_short_backtest'].net_holdings.iloc[:250], other['long_short_backtest'].net_holdings.iloc[:250])
    regime = baseline['factors'][m.REGIME_SWITCHING_COMPOSITE]
    assert regime['long_short_backtest'].net_holdings.iloc[:250].abs().sum().sum() > 0.
    assert baseline['trial_family']['attempt_count'] == 2 * len(baseline['factors']) + 32
    assert baseline['trial_family']['distinct_trial_count'] == 2 * len(baseline['factors']) + 24
    # Prove the perturbations changed later evidence and sample identity.
    assert not baseline['factors'][m.ALPHA_016]['daily_ic'].equals(labels_changed['factors'][m.ALPHA_016]['daily_ic'])
    assert baseline['trial_inventory'][0]['trial_id'] != prices_changed['trial_inventory'][0]['trial_id']
