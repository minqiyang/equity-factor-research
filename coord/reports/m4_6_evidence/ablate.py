"""Isolated negative removals with exact source hashes and retained failures."""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
MODEL = "risk_attribution.py"
TEST_UNIT = "tests/test_risk_attribution.py"


def mutation(name, test, before, after):
    return name, TEST_UNIT + "::" + test, [(MODEL, before, after)]


GUARDS = {
    **{reason: 'test_public_guard_counterexamples[' + reason + ']' for reason in (
        'axes', 'dates', 'numeric', 'nonfinite', 'styles', 'configuration', 'alignment',
        'positive_inputs', 'availability', 'exposure_unavailable', 'causality',
        'regression_weights', 'partial_missing', 'costs', 'return_identity', 'risk_numerical')},
    'fit_numerical': 'test_solver_output_guard',
    'basis': 'test_basis_guard',
    'rank_deficient': 'test_collinearity_refused[duplicate]',
    'sample_size': 'test_descriptor_missing_and_sparse_guards',
    'specific_variance': 'test_invalid_covariance_refused[negative_specific]',
    'covariance_psd': 'test_invalid_covariance_refused[indefinite]',
    'covariance_symmetry': 'test_invalid_covariance_refused[asymmetric]',
    'integration_scope': 'test_integration_scope_and_identity_guard',
    'engine_identity': 'test_integration_scope_and_identity_guard',
}
VARIANTS = [mutation('guard_' + reason, test, 'if not condition:',
                     f'if not condition and reason != "{reason}":') for reason, test in GUARDS.items()]
VARIANTS += [
    mutation('winsorization', 'test_standardization_winsorization_and_constant',
             'clipped = raw.clip(lower=bounds.iloc[0], upper=bounds.iloc[1], axis=0)', 'clipped = raw'),
    mutation('demean', 'test_standardization_winsorization_and_constant',
             'centered = clipped.sub(clipped.mean(axis=1), axis=0)', 'centered = clipped'),
    mutation('population_standardization', 'test_standardization_winsorization_and_constant',
             'scale = clipped.std(axis=1, ddof=0)', 'scale = clipped.std(axis=1, ddof=1)'),
    mutation('size_log', 'test_market_descriptor_oracles_and_prefix',
             '"Size": np.log(market_caps)', '"Size": market_caps'),
    mutation('value_descriptor', 'test_market_descriptor_oracles_and_prefix',
             '"Value": book_to_price', '"Value": book_to_price * 0'),
    mutation('momentum_skip', 'test_market_descriptor_oracles_and_prefix',
             'prices.shift(momentum_skip)', 'prices.shift(0)'),
    mutation('volatility_ddof_equivalence', 'test_market_descriptor_oracles_and_prefix',
             '.std(ddof=1)', '.std(ddof=0)'),
    mutation('volatility_calculation', 'test_market_descriptor_oracles_and_prefix',
             'returns.rolling(volatility_window, min_periods=volatility_window).std(ddof=1)',
             'returns.rolling(volatility_window, min_periods=volatility_window).mean()'),
    mutation('liquidity_dollar_basis', 'test_market_descriptor_oracles_and_prefix',
             '(prices * volumes).rolling', 'volumes.rolling'),
    mutation('prior_exposure_lag', 'test_prior_exposures_and_risk_causality',
             'self.exposures.at(start)', 'self.exposures.at(asset_returns.index[i])'),
    mutation('wls_weighting', 'test_wls_normal_equations_and_prior_weights',
             'np.sqrt(weights.iloc[i].to_numpy(dtype=float))', 'np.ones(len(y))'),
    mutation('residual_subtraction', 'test_orthogonal_ols_golden',
             'residual = y - x @ coefficients', 'residual = y'),
    mutation('signed_portfolio_exposure', 'test_exact_return_decomposition[1.0]',
             'beta = p.iloc[i].to_numpy() @ x.to_numpy()', 'beta = np.abs(p.iloc[i].to_numpy()) @ x.to_numpy()'),
    mutation('signed_specific_return', 'test_exact_return_decomposition[1.0]',
             'p.iloc[i].to_numpy() @ fit.residual_returns.iloc[i].to_numpy()',
             'np.abs(p.iloc[i].to_numpy()) @ fit.residual_returns.iloc[i].to_numpy()'),
    mutation('current_return_in_risk', 'test_prior_exposures_and_risk_causality',
             '.iloc[history_start:i]', '.iloc[history_start:i + 1]'),
    mutation('bounded_risk_window', 'test_prior_exposures_and_risk_causality',
             'history_start = max(0, i - self.covariance_window)', 'history_start = 0'),
    mutation('risk_warmup', 'test_prior_exposures_and_risk_causality',
             'if len(factor_history) >= self.min_covariance_observations:', 'if len(factor_history) >= 1:'),
    mutation('factor_covariance_sample', 'test_prior_exposures_and_risk_causality',
             'factor_history.cov(ddof=1)', 'factor_history.cov(ddof=0)'),
    mutation('specific_variance_sample', 'test_prior_exposures_and_risk_causality',
             'residual_history.var(ddof=1)', 'residual_history.var(ddof=0)'),
    mutation('factor_cross_covariance', 'test_risk_covariance_golden_and_signed_euler',
             'beta * (covariance @ beta)', 'beta**2 * np.diag(covariance)'),
    mutation('squared_active_weights', 'test_risk_covariance_golden_and_signed_euler',
             'active_weights**2 * specific', 'np.abs(active_weights) * specific'),
    mutation('benchmark_subtraction', 'test_benchmark_weights_and_future_benchmark',
             'active_weights = p - b', 'active_weights = p'),
    mutation('total_active_variance', 'test_risk_covariance_golden_and_signed_euler',
             'variance = factor_variance + specific_variance', 'variance = factor_variance'),
    mutation('tracking_error_root', 'test_risk_covariance_golden_and_signed_euler',
             'tracking_error = float(np.sqrt(variance))', 'tracking_error = float(variance)'),
    mutation('annualization', 'test_risk_covariance_golden_and_signed_euler',
             'tracking_error * float(np.sqrt(periods_per_year))', 'tracking_error'),
    mutation('net_costs', 'test_exact_return_decomposition[1.0]',
             '(gross_series - costs).rename', 'gross_series.rename'),
    mutation('actual_prior_holdings', 'test_engine_integration_and_baseline',
             'model.attribute(asset_returns, holdings.iloc[:-1]', 'model.attribute(asset_returns, holdings.iloc[1:]'),
    mutation('full_cross_section_returns', 'test_engine_integration_and_baseline',
             'prices.pct_change(fill_method=None).iloc[1:]', 'prices.pct_change(fill_method=None).iloc[1:] * 0'),
    mutation('variance_roundoff_tolerance', 'test_valid_rank_one_covariance_with_hedged_factor_exposure',
             'variance >= -1e-14 and factor_variance >= -1e-14',
             'variance >= 0 and factor_variance >= 0'),
    mutation('factor_variance_roundoff_clamp', 'test_variance_roundoff_boundary',
             'factor_variance = max(factor_variance, 0.0)', 'factor_variance = factor_variance'),
    mutation('active_variance_roundoff_clamp', 'test_variance_roundoff_boundary',
             'variance = max(variance, 0.0)', 'variance = variance'),
]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    originals = {
        name: digest(ROOT / "src/backtest" / name)
        for name in (MODEL, "portfolio.py", "long_short.py")
    }
    cases = [("baseline", TEST_UNIT, [])] + VARIANTS
    records = []
    for name, selection, edits in cases:
        isolated = output / name
        if isolated.exists():
            raise ValueError(f"preserve existing ablation evidence: {isolated}")
        package = isolated / "src/backtest"
        shutil.copytree(
            ROOT / "src/backtest", package, ignore=shutil.ignore_patterns("__pycache__")
        )
        for filename, old, new in edits:
            path = package / filename
            content = path.read_text()
            if old not in content:
                raise ValueError(f"missing mutation anchor: {name}/{filename}")
            path.write_text(content.replace(old, new))
        environment = dict(
            os.environ,
            PYTHONPATH=os.pathsep.join(
                (str(isolated / "src"), str(ROOT / "src"), str(ROOT))
            ),
        )
        environment.update(
            {
                key: "1"
                for key in (
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "BLIS_NUM_THREADS",
                    "VECLIB_MAXIMUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                )
            }
        )
        imported = subprocess.check_output(
            [
                sys.executable,
                "-c",
                "import backtest.risk_attribution as m;print(m.__file__)",
            ],
            cwd=isolated,
            env=environment,
            text=True,
        ).strip()
        if Path(imported) != package / MODEL:
            raise RuntimeError("ablation import escaped its isolated copy")
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-o",
            "pythonpath=",
            *selection.split(),
        ]
        start = time.monotonic()
        process = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        log = isolated / "pytest.txt"
        log.write_text(process.stdout)
        records.append(
            dict(
                name=name,
                expected_exit=0 if name in ("baseline", "volatility_ddof_equivalence") else 1,
                observed_exit=process.returncode,
                seconds=time.monotonic() - start,
                selected_tests=selection,
                log_sha256=digest(log),
                source_sha256={file: digest(package / file) for file in originals},
                edits=[
                    dict(file=file, before=old, after=new) for file, old, new in edits
                ],
            )
        )
        print(name, process.returncode, flush=True)
    preserved = originals == {
        name: digest(ROOT / "src/backtest" / name) for name in originals
    }
    result = dict(
        production_sources_preserved=preserved,
        baseline_sources=originals,
        cases=records,
    )
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    if not preserved or any(
        case["expected_exit"] != case["observed_exit"] for case in records
    ):
        raise RuntimeError("ablation has an unexpected outcome; inspect retained logs")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
