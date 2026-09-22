"""Independent golden identities, timing counterexamples, and engine controls."""

from dataclasses import fields, replace
import json

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal
from scipy.linalg import hadamard

from backtest.long_short import run_long_short_backtest
from backtest.market_impact import SquareRootImpactModel
from backtest.portfolio import capture_backtest_source_provenance, run_long_only_backtest
from backtest.risk_attribution import (
    STYLE_FACTORS, CrossSectionalRiskModel, RiskAttributionError,
    StyleFactorExposures, attribute_backtest, decompose_active_risk,
)


def fixture(periods=8):
    dates = pd.bdate_range("2024-01-01", periods=periods + 1, name="close")
    assets = pd.Index([f"S{i}" for i in range(8)], name="asset")
    x = hadamard(8).astype(float)[:, :6]
    exposures = StyleFactorExposures.from_descriptors({
        name: pd.DataFrame(np.tile(x[:, k + 1], (periods + 1, 1)), index=dates, columns=assets)
        for k, name in enumerate(STYLE_FACTORS)
    }, winsor_quantile=0)
    f = np.arange(1, periods * 6 + 1).reshape(periods, 6) * 0.0001
    residuals = np.arange(1, periods + 1)[:, None] * hadamard(8)[None, :, 6] * 0.0003
    returns = pd.DataFrame(f @ x.T + residuals, index=dates[1:], columns=assets)
    starts = pd.Series(dates[:-1], index=dates[1:])
    model = CrossSectionalRiskModel(exposures, covariance_window=4, min_covariance_observations=2)
    weights = pd.DataFrame(np.arange(-4, 4)[None, :] / 10 + np.zeros((periods, 8)), index=dates[:-1], columns=assets)
    return model, returns, starts, weights, f, residuals


def market_inputs(periods=40, assets=12):
    rng = np.random.default_rng(460)
    dates = pd.bdate_range("2024-01-01", periods=periods)
    columns = pd.Index([f"A{i}" for i in range(assets)])
    def panel(values):
        return pd.DataFrame(values, index=dates, columns=columns)
    prices = panel(100 * np.cumprod(1 + rng.normal(0.001, 0.02, (periods, assets)), axis=0))
    volumes = panel(rng.uniform(1e5, 2e5, (periods, assets)))
    caps = panel(rng.uniform(1e8, 1e9, (periods, assets)))
    value = panel(rng.uniform(0.1, 2, (periods, assets)))
    return prices, volumes, caps, value


def market_exposures(inputs):
    return StyleFactorExposures.from_market_data(
        *inputs, price_basis="raw", volume_basis="raw", momentum_window=6,
        momentum_skip=2, volatility_window=4, liquidity_window=3,
    )


def test_orthogonal_ols_golden():
    model, returns, starts, _, f, residual = fixture()
    fit = model.fit(returns, interval_starts=starts)
    np.testing.assert_allclose(fit.factor_returns, f, atol=1e-16)
    np.testing.assert_allclose(fit.residual_returns, residual, atol=1e-16)
    for i, start in enumerate(starts):
        x = model.exposures.at(start).to_numpy()
        np.testing.assert_allclose(x.T @ fit.residual_returns.iloc[i], 0, atol=1e-16)
    assert fit.diagnostics['rank'].eq(6).all()
    assert fit.diagnostics['method'].eq('OLS').all()


def test_wls_normal_equations_and_prior_weights():
    model, returns, starts, _, _, _ = fixture()
    rw = pd.DataFrame(np.arange(1, 9)[None, :] + np.zeros((9, 8)),
                      index=model.exposures.panels['Size'].index, columns=returns.columns)
    model = replace(model, regression_weights=rw)
    fit = model.fit(returns, interval_starts=starts)
    for i, start in enumerate(starts):
        x = model.exposures.at(start).to_numpy()
        w = np.diag(rw.loc[start])
        expected = np.linalg.solve(x.T @ w @ x, x.T @ w @ returns.iloc[i].to_numpy())
        np.testing.assert_allclose(fit.factor_returns.iloc[i], expected, atol=1e-16)
        np.testing.assert_allclose(x.T @ w @ fit.residual_returns.iloc[i], 0, atol=1e-15)
    rw2 = rw.copy()
    rw2.iloc[-1] *= np.arange(1, 9)
    assert_frame_equal(fit.factor_returns, replace(model, regression_weights=rw2).fit(returns, interval_starts=starts).factor_returns)
    assert fit.diagnostics['method'].eq('WLS').all()


@pytest.mark.parametrize('weight_scale', [0.0, 1.0, -1.0, 10000.0])
def test_exact_return_decomposition(weight_scale):
    model, returns, starts, weights, _, _ = fixture()
    weights *= weight_scale
    costs = pd.Series(0.0007, index=returns.index)
    result = model.attribute(returns, weights, interval_starts=starts, trading_costs=costs)
    expected = (weights.to_numpy() * returns.to_numpy()).sum(axis=1)
    np.testing.assert_allclose(result.gross_return, expected, atol=1e-12, rtol=0)
    np.testing.assert_allclose(result.factor_contributions.sum(axis=1) + result.specific_return,
                               expected, atol=1e-12, rtol=0)
    np.testing.assert_allclose(result.net_return, expected - costs, atol=1e-12, rtol=0)
    np.testing.assert_allclose(result.specific_return, np.sum(weights.to_numpy() * result.fit.residual_returns.to_numpy(), axis=1), atol=1e-12)


def test_standardization_winsorization_and_constant():
    model, _, _, _, _, _ = fixture()
    descriptors = {name: panel.copy() for name, panel in model.exposures.panels.items()}
    descriptors['Size'].iloc[:, -1] = 1000
    result = StyleFactorExposures.from_descriptors(descriptors, winsor_quantile=0.2)
    raw = descriptors['Size'].iloc[0].to_numpy()
    clipped = np.clip(raw, *np.quantile(raw, [0.2, 0.8]))
    expected = (clipped - clipped.mean()) / clipped.std(ddof=0)
    np.testing.assert_allclose(result.panels['Size'].iloc[0], expected)
    for panel in result.panels.values():
        np.testing.assert_allclose(panel.mean(axis=1), 0, atol=1e-15)
        np.testing.assert_allclose(panel.std(axis=1, ddof=0), 1, atol=1e-15)
    descriptors['Value'][:] = 2.0
    constant = StyleFactorExposures.from_descriptors(descriptors)
    assert constant.panels['Value'].eq(0).all().all()


def test_market_descriptor_oracles_and_prefix():
    inputs = market_inputs()
    exposures = market_exposures(inputs)
    p, v, cap, value = inputs
    date = p.index[10]
    raw = {
        'Size': np.log(cap.loc[date]), 'Value': value.loc[date],
        'Momentum': p.iloc[8] / p.iloc[4] - 1,
        'Volatility': (p.iloc[7:11].to_numpy() / p.iloc[6:10].to_numpy() - 1).std(axis=0, ddof=1),
        'Liquidity': np.log((p.iloc[8:11] * v.iloc[8:11]).mean()),
    }
    for name, row in raw.items():
        row = np.asarray(row)
        clipped = np.clip(row, *np.quantile(row, [0.01, 0.99]))
        expected = (clipped - clipped.mean()) / clipped.std(ddof=0)
        np.testing.assert_allclose(exposures.panels[name].loc[date], expected, atol=1e-12)
    prefix = market_exposures(tuple(panel.iloc[:20] for panel in inputs))
    mutated = tuple(panel.copy() for panel in inputs)
    for panel in mutated:
        panel.iloc[20:] *= 5
    after = market_exposures(mutated)
    for name in STYLE_FACTORS:
        assert_frame_equal(prefix.panels[name], exposures.panels[name].iloc[:20])
        assert_frame_equal(after.panels[name].iloc[:20], prefix.panels[name])
    assert exposures.panels['Momentum'].iloc[:6].isna().all().all()
    assert exposures.panels['Volatility'].iloc[:4].isna().all().all()
    assert exposures.panels['Liquidity'].iloc[:2].isna().all().all()


def test_basis_guard():
    with pytest.raises(RiskAttributionError, match='basis'):
        StyleFactorExposures.from_market_data(*market_inputs(), price_basis='raw', volume_basis='split_adjusted')


@pytest.mark.parametrize('kind', ['duplicate', 'zero', 'near_collinear'])
def test_collinearity_refused(kind):
    model, returns, starts, _, _, _ = fixture()
    panels = {k: v.copy() for k, v in model.exposures.panels.items()}
    panels['Value'] = panels['Size'].copy() if kind != 'zero' else panels['Size'] * 0
    if kind == 'near_collinear':
        panels['Value'] += panels['Momentum'] * 1e-14
    with pytest.raises(RiskAttributionError, match='rank_deficient'):
        replace(model, exposures=StyleFactorExposures(panels)).fit(returns, interval_starts=starts)


def test_prior_exposures_and_risk_causality():
    model, returns, starts, weights, _, _ = fixture()
    result = model.attribute(returns, weights, interval_starts=starts)
    i = 4
    mutated_returns = returns.copy()
    mutated_returns.iloc[i:] *= 7
    changed = model.attribute(mutated_returns, weights, interval_starts=starts)
    assert_frame_equal(result.fit.factor_returns.iloc[:i], changed.fit.factor_returns.iloc[:i])
    assert_frame_equal(result.risk.iloc[:i + 1], changed.risk.iloc[:i + 1])
    panels = {k: v.copy() for k, v in model.exposures.panels.items()}
    for v in panels.values():
        v.loc[returns.index[i]:] *= -1
    changed_model = replace(model, exposures=StyleFactorExposures(panels))
    changed_fit = changed_model.fit(returns, interval_starts=starts)
    assert_frame_equal(result.fit.factor_returns.iloc[:i + 1], changed_fit.factor_returns.iloc[:i + 1])
    prefix = model.attribute(returns.iloc[:i], weights.iloc[:i], interval_starts=starts.iloc[:i])
    assert_frame_equal(result.risk.iloc[:i], prefix.risk)
    assert_frame_equal(result.factor_contributions.iloc[:i], prefix.factor_contributions)
    for i in range(2, len(returns)):
        hist = result.fit.factor_returns.iloc[max(0, i - 4):i]
        resid = result.fit.residual_returns.iloc[max(0, i - 4):i]
        beta = result.exposures.iloc[i].to_numpy()
        expected = beta @ np.cov(hist.to_numpy(), rowvar=False, ddof=1) @ beta
        expected += np.sum(weights.iloc[i].to_numpy()**2 * np.var(resid.to_numpy(), axis=0, ddof=1))
        assert result.risk.iloc[i].active_variance == pytest.approx(expected, abs=1e-18)
    assert result.risk.iloc[:2].status.eq('insufficient_history').all()
    assert result.risk.iloc[:2].active_variance.isna().all()
    assert result.risk.observations.tolist() == [0, 1, 2, 3, 4, 4, 4, 4]


def test_risk_covariance_golden_and_signed_euler():
    x = pd.DataFrame([[1, 2], [-1, 1], [0, -1]], index=['a', 'b', 'c'], columns=['f1', 'f2'])
    p = pd.Series([0.5, -0.25, 0.1], index=x.index)
    b = pd.Series([0.2, 0.2, 0.6], index=x.index)
    covariance = pd.DataFrame([[0.04, 0.018], [0.018, 0.01]], index=x.columns, columns=x.columns)
    specific = pd.Series([0.01, 0.02, 0.03], index=x.index)
    result = decompose_active_risk(x, p, b, covariance, specific, periods_per_year=12)
    active = (p - b).to_numpy()
    beta = active @ x.to_numpy()
    factor = beta * (covariance.to_numpy() @ beta)
    specific_terms = active**2 * specific.to_numpy()
    np.testing.assert_allclose(result.factor_contributions, factor)
    np.testing.assert_allclose(result.specific_contributions, specific_terms)
    assert result.factor_variance == pytest.approx(factor.sum())
    assert result.specific_variance == pytest.approx(specific_terms.sum())
    assert result.active_variance == pytest.approx(factor.sum() + specific_terms.sum())
    assert result.annualized_tracking_error == pytest.approx(np.sqrt(result.active_variance * 12))
    assert result.tracking_error == pytest.approx(np.sqrt(result.active_variance))
    zero = decompose_active_risk(x, p, p, covariance, specific)
    assert zero.active_variance == 0
    # Correlated factors can supply a negative individual Euler contribution.
    signed = decompose_active_risk(pd.DataFrame(np.eye(2), columns=x.columns),
                                  pd.Series([1., -1.]), pd.Series([0., 0.]), covariance,
                                  pd.Series([0., 0.]))
    assert signed.factor_contributions.iloc[1] < 0
    assert signed.active_variance > 0


@pytest.mark.parametrize('invalid', ['negative_specific', 'indefinite', 'asymmetric', 'nan', 'order'])
def test_invalid_covariance_refused(invalid):
    x = pd.DataFrame(np.eye(2), columns=['a', 'b'])
    cov = pd.DataFrame(np.eye(2), index=x.columns, columns=x.columns)
    specific = pd.Series([1., 1.])
    reason = {'negative_specific': 'specific_variance', 'indefinite': 'covariance_psd',
              'asymmetric': 'covariance_symmetry', 'nan': 'nonfinite', 'order': 'alignment'}[invalid]
    if invalid == 'negative_specific':
        specific.iloc[0] = -0.1
    elif invalid == 'indefinite':
        cov.iloc[0, 1] = cov.iloc[1, 0] = 2
    elif invalid == 'asymmetric':
        cov.iloc[0, 1] = 0.1
    elif invalid == 'nan':
        cov.iloc[0, 0] = np.nan
    else:
        cov = cov.iloc[::-1]
    with pytest.raises(RiskAttributionError, match=reason):
        decompose_active_risk(x, pd.Series([1., 0.]), pd.Series([0., 0.]), cov, specific)


def test_benchmark_weights_and_future_benchmark():
    model, returns, starts, weights, _, _ = fixture()
    model = replace(model, benchmark_weights=weights.copy())
    result = model.attribute(returns, weights, interval_starts=starts)
    assert result.active_exposures.eq(0).all().all()
    assert result.risk.active_variance.iloc[2:].eq(0).all()
    assert result.risk.benchmark.eq('supplied_weights').all()
    benchmark = weights.copy()
    benchmark.iloc[5:] = 10
    changed = replace(model, benchmark_weights=benchmark).attribute(returns, weights, interval_starts=starts)
    assert_frame_equal(result.risk.iloc[:5], changed.risk.iloc[:5])


@pytest.mark.parametrize('invalid', ['same_date', 'stale', 'order', 'missing', 'nan', 'bool', 'empty_rows', 'empty_cols', 'duplicate_assets', 'duplicate_dates'])
def test_input_refusals(invalid):
    model, returns, starts, _, _, _ = fixture()
    if invalid == 'same_date':
        starts[:] = returns.index
    elif invalid == 'stale':
        starts.iloc[-1] = starts.iloc[-1] - pd.Timedelta(days=1)
    elif invalid == 'order':
        returns = returns.iloc[:, ::-1]
    elif invalid == 'missing':
        model.exposures.panels['Value'].iloc[0, 0] = np.nan
    elif invalid == 'nan':
        returns.iloc[0, 0] = np.nan
    elif invalid == 'bool':
        returns = returns.astype(bool)
    elif invalid == 'empty_rows':
        returns, starts = returns.iloc[:0], starts.iloc[:0]
    elif invalid == 'empty_cols':
        returns = returns.iloc[:, :0]
    elif invalid == 'duplicate_assets':
        returns.columns = ['x'] * 8
    else:
        returns.index = [returns.index[0]] * len(returns)
    with pytest.raises(RiskAttributionError):
        model.fit(returns, interval_starts=starts)


@pytest.mark.parametrize('invalid', ['nan', 'zero', 'negative', 'order'])
def test_wls_invalid_weights(invalid):
    model, returns, starts, weights, _, _ = fixture()
    weights[:] = 1.0
    if invalid == 'order':
        weights = weights.iloc[:, ::-1]
    else:
        weights.iloc[0, 0] = {'nan': np.nan, 'zero': 0, 'negative': -1}[invalid]
    with pytest.raises(RiskAttributionError):
        replace(model, regression_weights=weights).fit(returns, interval_starts=starts)


@pytest.mark.parametrize('field,value', [('covariance_window', 1), ('min_covariance_observations', 1), ('min_covariance_observations', 5), ('covariance_window', True)])
def test_covariance_configuration(field, value):
    model, returns, starts, weights, _, _ = fixture()
    with pytest.raises(RiskAttributionError, match='configuration'):
        replace(model, **{field: value}).attribute(returns, weights, interval_starts=starts)


def test_cost_and_weight_alignment_guards():
    model, returns, starts, weights, _, _ = fixture()
    with pytest.raises(RiskAttributionError, match='alignment'):
        model.attribute(returns, weights.set_axis(returns.index), interval_starts=starts)
    with pytest.raises(RiskAttributionError, match='costs'):
        model.attribute(returns, weights, interval_starts=starts, trading_costs=pd.Series(-1., index=returns.index))
    with pytest.raises(RiskAttributionError, match='alignment'):
        model.attribute(returns, weights, interval_starts=starts, trading_costs=pd.Series(0., index=returns.index[::-1]))


def test_descriptor_missing_and_sparse_guards():
    model, returns, starts, _, _, _ = fixture()
    panels = {k: v.copy() for k, v in model.exposures.panels.items()}
    panels['Value'].iloc[0, 0] = np.nan
    with pytest.raises(RiskAttributionError, match='partial_missing'):
        StyleFactorExposures.from_descriptors(panels)
    panels = {k: v.iloc[:, :6].copy() for k, v in model.exposures.panels.items()}
    with pytest.raises(RiskAttributionError, match='sample_size'):
        replace(model, exposures=StyleFactorExposures(panels)).fit(returns.iloc[:, :6], interval_starts=starts)
    panels = {k: v.copy() for k, v in model.exposures.panels.items()}
    panels['Value'].iloc[0] = np.nan
    exposures = StyleFactorExposures.from_descriptors(panels)
    with pytest.raises(RiskAttributionError, match='exposure_unavailable'):
        exposures.at(starts.iloc[0])


def engine_book(engine, prices, signals, model=None, impact=False, **overrides):
    kwargs = dict(evaluation_start=prices.index[8], evaluation_end=prices.index[-1],
                  rebalance_frequency='W-FRI', transaction_cost_bps=10., slippage_bps=5.,
                  initial_capital=10000., risk_model=model)
    if impact:
        kwargs.update(impact_model=SquareRootImpactModel(lookback=3, mode='throttle', max_participation_rate=0.00001),
                      impact_volumes=pd.DataFrame(1e6, index=prices.index, columns=prices.columns),
                      impact_price_basis='raw', impact_volume_basis='raw', slippage_bps=0.)
    kwargs.update(overrides)
    if engine == 'long_only':
        return run_long_only_backtest(prices, signals, source_provenance=capture_backtest_source_provenance(prices, signals), top_n=4, **kwargs)
    return run_long_short_backtest(prices, signals, quantiles=3, **kwargs)


@pytest.mark.parametrize('engine', ['long_only', 'long_short'])
@pytest.mark.parametrize('impact', [False, True])
def test_engine_integration_and_baseline(engine, impact):
    inputs = market_inputs()
    prices = inputs[0]
    signals = inputs[3]
    model = CrossSectionalRiskModel(market_exposures(inputs), covariance_window=5, min_covariance_observations=2)
    baseline = engine_book(engine, prices, signals, impact=impact)
    attributed = engine_book(engine, prices, signals, model, impact)
    assert baseline.risk_attribution is None
    for field in fields(baseline):
        if field.name == 'risk_attribution':
            continue
        a, b = getattr(baseline, field.name), getattr(attributed, field.name)
        if isinstance(a, pd.DataFrame):
            assert_frame_equal(a, b, check_exact=True)
        elif isinstance(a, pd.Series):
            assert_series_equal(a, b, check_exact=True)
        else:
            assert a == b
    attr = attributed.risk_attribution
    np.testing.assert_allclose(attr.gross_return, attributed.gross_returns.iloc[1:], atol=1e-12)
    np.testing.assert_allclose(attr.net_return, attributed.returns.iloc[1:], atol=1e-12)
    assert attr.trading_costs.gt(0).any()
    holdings = attributed.holdings if engine == 'long_only' else attributed.net_holdings
    for date, start in attr.fit.diagnostics.exposure_date.items():
        np.testing.assert_allclose(attr.exposures.loc[date], holdings.loc[start] @ model.exposures.at(start), atol=1e-14)
    assert attr.gross_return.iloc[0] == 0


def test_integration_scope_and_identity_guard():
    model, returns, _, weights, _, _ = fixture()
    dates = model.exposures.panels['Size'].index
    prices = pd.DataFrame(100., index=dates, columns=returns.columns)
    prices.iloc[1:] = 100 * (1 + returns).cumprod().to_numpy()
    holdings = pd.concat([weights, weights.iloc[[-1]].set_axis(dates[-1:])])
    zero = pd.Series(0., index=dates)
    args = dict(prices=prices, holdings=holdings, gross_returns=zero, net_returns=zero,
                trading_costs=zero, periods_per_year=252, terminal_events=None)
    assert attribute_backtest(None, **args) is None
    with pytest.raises(RiskAttributionError, match='integration_scope'):
        attribute_backtest(model, **{**args, 'terminal_events': pd.DataFrame()})
    with pytest.raises(RiskAttributionError, match='integration_scope'):
        attribute_backtest(model, **{**args, 'missing_price_policy': 'zero_return'})
    with pytest.raises(RiskAttributionError, match='engine_identity'):
        attribute_backtest(model, **args)


def test_demo_attempts_and_reproducibility(tmp_path):
    from research.risk_attribution_demo import run_risk_attribution_demo
    path = tmp_path / 'demo.md'
    first = run_risk_attribution_demo(report_path=path)
    second = run_risk_attribution_demo(write_outputs=False)
    assert first == second
    records = [json.loads(line) for line in path.with_name('demo_attempts.jsonl').read_text().splitlines()]
    assert len(records) == 2 * len(first['cases'])
    assert {c['status'] for c in first['cases']} == {'success', 'refused'}
    assert sum(c['status'] == 'refused' for c in first['cases']) == 2
    assert all(records[i]['status'] == 'started' for i in range(0, len(records), 2))
    assert all(records[i]['attempt_id'] == records[i + 1]['attempt_id'] for i in range(0, len(records), 2))
    assert 'DIAGNOSTIC_ONLY' in path.read_text()


@pytest.mark.parametrize('reason', [
    'axes', 'dates', 'numeric', 'nonfinite', 'styles', 'configuration', 'alignment',
    'positive_inputs', 'availability', 'exposure_unavailable', 'causality',
    'regression_weights', 'partial_missing', 'costs', 'return_identity', 'risk_numerical',
])
def test_public_guard_counterexamples(reason, monkeypatch):
    model, returns, starts, weights, _, _ = fixture()
    if reason == 'axes':
        # Duplicate assets with equal labels remain an ambiguous cross-section.
        for panel in model.exposures.panels.values():
            panel.columns = ['a'] * 8
        returns.columns = ['a'] * 8
    elif reason == 'dates':
        for panel in model.exposures.panels.values():
            panel.index = panel.index[::-1]
    elif reason == 'numeric':
        returns = returns.astype(str)
    elif reason == 'nonfinite':
        returns.iloc[0, 0] = np.inf
    elif reason == 'styles':
        model.exposures.panels.pop('Value')
    elif reason == 'configuration':
        model = replace(model, covariance_window=1)
    elif reason == 'alignment':
        returns = returns.iloc[:, ::-1]
    elif reason == 'positive_inputs':
        inputs = market_inputs()
        inputs[1].iloc[0, 0] = 0
    elif reason == 'availability':
        starts.iloc[-1] = starts.iloc[-1] + pd.Timedelta(days=10)
    elif reason == 'exposure_unavailable':
        model.exposures.panels['Value'].iloc[0] = np.nan
    elif reason == 'causality':
        starts[:] = returns.index
    elif reason == 'regression_weights':
        model = replace(model, regression_weights=weights * 0)
    elif reason == 'partial_missing':
        model.exposures.panels['Value'].iloc[0, 0] = np.nan
    elif reason == 'return_identity':
        original = model.fit(returns, interval_starts=starts)
        bad = replace(original, residual_returns=original.residual_returns + 0.1)
        monkeypatch.setattr(CrossSectionalRiskModel, 'fit', lambda *a, **kw: bad)
    elif reason == 'risk_numerical':
        weights[:] = 1e308
    with pytest.raises(RiskAttributionError, match='^' + reason + ':'):
        if reason == 'styles' or reason == 'partial_missing':
            StyleFactorExposures.from_descriptors(model.exposures.panels)
        elif reason == 'positive_inputs':
            market_exposures(inputs)
        elif reason == 'availability':
            model.exposures.at(starts.iloc[-1])
        elif reason == 'risk_numerical':
            with np.errstate(over='ignore', invalid='ignore'):
                decompose_active_risk(model.exposures.at(starts.iloc[0]), weights.iloc[0], weights.iloc[0] * 0,
                                      pd.DataFrame(np.eye(6), index=['Market', *STYLE_FACTORS], columns=['Market', *STYLE_FACTORS]),
                                      pd.Series(1., index=returns.columns))
        else:
            model.attribute(returns, weights, interval_starts=starts,
                            trading_costs=pd.Series(-1. if reason == 'costs' else 0., index=returns.index))


@pytest.mark.parametrize('shape', [(0, 8), (8, 0), (0, 0)])
def test_empty_public_exposure_axes(shape):
    raw = pd.DataFrame(np.empty(shape), index=pd.bdate_range('2024-01-01', periods=shape[0]))
    with pytest.raises(RiskAttributionError, match='axes'):
        StyleFactorExposures.from_descriptors({k: raw for k in STYLE_FACTORS})


def test_named_mixed_asset_identities_and_zero_covariance():
    model, returns, starts, weights, _, _ = fixture()
    labels = pd.Index(['A', 1, '1', 2.5, 'Z', 9, 'X', 42], name='mixed_id')
    for panel in model.exposures.panels.values():
        panel.columns = labels
    returns.columns = weights.columns = labels
    attr = model.attribute(returns, weights, interval_starts=starts)
    assert attr.fit.residual_returns.columns.equals(labels)
    x = model.exposures.at(starts.iloc[0])
    risk = decompose_active_risk(x, weights.iloc[0], weights.iloc[0] * 0,
                                 pd.DataFrame(0., index=x.columns, columns=x.columns),
                                 pd.Series(0., index=labels))
    assert risk.tracking_error == 0


@pytest.mark.parametrize('engine', ['long_only', 'long_short'])
def test_engine_future_prefix_and_missing_unheld_refusal(engine):
    inputs = market_inputs()
    prices, _, _, signals = inputs
    model = CrossSectionalRiskModel(market_exposures(inputs), covariance_window=5, min_covariance_observations=2)
    full = engine_book(engine, prices, signals, model)
    prefix = engine_book(engine, prices, signals, model, evaluation_end=prices.index[24])
    attr = full.risk_attribution
    before = prefix.risk_attribution
    assert_frame_equal(attr.factor_contributions.loc[before.factor_contributions.index], before.factor_contributions)
    assert_frame_equal(attr.risk.loc[before.risk.index], before.risk)
    broken = prices.copy()
    # The initialization interval holds cash, while the full regression needs every endpoint.
    broken.iloc[8, 0] = np.nan
    with pytest.raises(RiskAttributionError, match='nonfinite'):
        engine_book(engine, broken, signals, model)


def test_demo_unexpected_failure_logged(tmp_path, monkeypatch):
    import research.risk_attribution_demo as demo
    def fail():
        raise RuntimeError('synthetic injected failure')
    monkeypatch.setattr(demo, 'synthetic_inputs', fail)
    path = tmp_path / 'bad.md'
    with pytest.raises(RuntimeError, match='unexpected outcomes'):
        demo.run_risk_attribution_demo(report_path=path)
    records = [json.loads(line) for line in path.with_name('bad_attempts.jsonl').read_text().splitlines()]
    assert len(records) == 20
    assert all(r['status'] == 'failure' for r in records[1::2])
    assert 'failure' in path.read_text()


def test_solver_output_guard(monkeypatch):
    model, returns, starts, _, _, _ = fixture()
    monkeypatch.setattr(np.linalg, 'lstsq', lambda *a, **kw: (np.full(6, np.nan), [], 6, np.ones(6)))
    with pytest.raises(RiskAttributionError, match='fit_numerical'):
        model.fit(returns, interval_starts=starts)
