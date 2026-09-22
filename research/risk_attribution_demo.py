"""Reproduce a synthetic five-style attribution with every attempt retained."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest.long_short import run_long_short_backtest
from backtest.portfolio import capture_backtest_source_provenance, run_long_only_backtest
from backtest.risk_attribution import CrossSectionalRiskModel, RiskAttributionError, StyleFactorExposures
from research.demo_v0 import append_attempt_record

DEFAULT_REPORT_PATH = Path(__file__).resolve().parents[1] / "reports/risk_attribution_demo.md"
COMMAND = "PYTHONPATH=src:. python -m research.risk_attribution_demo"


def synthetic_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate independent, declared-available synthetic prices and descriptors."""
    rng = np.random.default_rng(4606)
    dates = pd.bdate_range("2024-01-01", periods=100, name="observed_close")
    assets = pd.Index([f"SYNTH_{i:02d}" for i in range(24)], name="permanent_id")
    shape = (len(dates), len(assets))
    def panel(values):
        return pd.DataFrame(values, index=dates, columns=assets)
    prices = panel(100 * np.cumprod(1 + rng.normal(0, 0.015, shape), axis=0))
    volumes = panel(rng.uniform(1e5, 1e6, shape))
    market_caps = panel(prices.to_numpy() * rng.uniform(1e6, 1e8, shape))
    book_to_price = panel(rng.uniform(0.1, 2.0, shape))
    return prices, volumes, market_caps, book_to_price


def run_risk_attribution_demo(
    *, report_path: Path = DEFAULT_REPORT_PATH, write_outputs: bool = True,
) -> dict[str, Any]:
    report_path = Path(report_path)
    attempt_path = report_path.with_name(report_path.stem + "_attempts.jsonl")
    cases = []
    unexpected = []
    specifications = [(engine, method, direction, "valid")
                      for engine in ("long_only", "long_short")
                      for method in ("OLS", "WLS") for direction in (1, -1)]
    specifications += [("long_only", "OLS", 1, guard) for guard in ("collinear", "warmup")]
    for engine, method, direction, scope in specifications:
        case_id = f"{engine}_{method}_{direction}_{scope}"
        start = {"case_id": case_id, "command": COMMAND, "status": "started", "data_scope": "synthetic"}
        attempt_id = append_attempt_record(attempt_path, start)["attempt_id"] if write_outputs else None
        case = {"case_id": case_id, "expected_refusal": scope != "valid"}
        try:
            prices, volumes, caps, value = synthetic_inputs()
            exposures = StyleFactorExposures.from_market_data(
                prices, volumes, caps, value, price_basis="raw", volume_basis="raw",
                momentum_window=20, momentum_skip=5, volatility_window=15, liquidity_window=10,
            )
            benchmark = pd.DataFrame(1 / len(prices.columns), index=prices.index, columns=prices.columns) if engine == "long_only" else None
            model = CrossSectionalRiskModel(
                exposures, regression_weights=np.sqrt(caps) if method == "WLS" else None,
                benchmark_weights=benchmark, covariance_window=20, min_covariance_observations=10,
            )
            if scope == "collinear":
                panels = {k: v.copy() for k, v in exposures.panels.items()}
                panels['Value'] = panels['Size'].copy()
                model = replace(model, exposures=StyleFactorExposures(panels))
            signals = direction * value
            kwargs = dict(
                evaluation_start=prices.index[25 if scope != "warmup" else 5],
                evaluation_end=prices.index[-1], rebalance_frequency="W-FRI",
                transaction_cost_bps=10., slippage_bps=5., initial_capital=10000., risk_model=model,
            )
            if engine == "long_only":
                book = run_long_only_backtest(prices, signals, source_provenance=capture_backtest_source_provenance(prices, signals), top_n=6, **kwargs)
            else:
                book = run_long_short_backtest(prices, signals, quantiles=4, **kwargs)
            attr = book.risk_attribution
            reconstruction = attr.factor_contributions.sum(axis=1) + attr.specific_return
            case.update(
                status="unexpected_success" if scope != "valid" else "success",
                gross_arithmetic_sum=float(attr.gross_return.sum()),
                net_arithmetic_sum=float(attr.net_return.sum()),
                compounded_net_return=float(book.equity_curve.iloc[-1] / book.equity_curve.iloc[0] - 1),
                factor_arithmetic_sums={k: float(v) for k, v in attr.factor_contributions.sum().items()},
                specific_arithmetic_sum=float(attr.specific_return.sum()),
                cost_arithmetic_sum=float(attr.trading_costs.sum()),
                max_identity_error=float((reconstruction - attr.gross_return).abs().max()),
                latest_exposures={k: float(v) for k, v in attr.exposures.iloc[-1].items()},
                latest_active_exposures={k: float(v) for k, v in attr.active_exposures.iloc[-1].items()},
                latest_factor_variance=float(attr.risk.factor_variance.iloc[-1]),
                latest_specific_variance=float(attr.risk.specific_variance.iloc[-1]),
                latest_annualized_tracking_error=float(attr.risk.annualized_tracking_error.iloc[-1]),
                risk_estimated_intervals=int(attr.risk.status.eq("estimated").sum()),
                risk_warmup_intervals=int(attr.risk.status.eq("insufficient_history").sum()),
                benchmark="equal_weight_at_prior_close" if benchmark is not None else "cash",
            )
            if scope != "valid":
                unexpected.append(case_id)
        except BaseException as exc:
            expected_reason = {"collinear": "rank_deficient", "warmup": "exposure_unavailable"}.get(scope)
            expected = isinstance(exc, RiskAttributionError) and exc.reason == expected_reason
            case.update(status="refused" if expected else "failure", error_type=type(exc).__name__, reason=getattr(exc, 'reason', type(exc).__name__))
            if not isinstance(exc, Exception):
                if write_outputs:
                    append_attempt_record(attempt_path, {**start, **case, "status": "interrupted"}, attempt_id=attempt_id)
                raise
            if not expected:
                unexpected.append(case_id)
        cases.append(case)
        if write_outputs:
            append_attempt_record(attempt_path, {**start, **case}, attempt_id=attempt_id)
    result = {"evidence_ceiling": "DIAGNOSTIC_ONLY", "seed": 4606, "cases": cases}
    if write_outputs:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_report(result), encoding="utf-8")
    if unexpected:
        raise RuntimeError(f"unexpected outcomes retained in attempt log: {unexpected}")
    return result


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Multi-Factor Risk Attribution Synthetic Diagnostic", "",
        "Evidence ceiling: DIAGNOSTIC_ONLY. Seed 4606 generates 100 observed closes and 24 predeclared synthetic identities.",
        "All inputs, market caps, and book-to-price availability are synthetic. The cohort supplies a software diagnostic; empirical validation and formal promotion remain open.", "",
        "Size uses log capitalization; Value uses supplied book-to-price; Momentum uses a 20-close lookback with a 5-close skip; Volatility uses 15 sample-return observations; Liquidity uses log 10-close mean dollar volume. Price and volume use the declared raw basis. Each style uses 1%/99% winsorization and population-standard-deviation normalization. Market is a unit intercept.", "",
        "Exposures, regression weights, benchmark weights, and actual portfolio weights use the immediately prior observed close. Signals execute at the next observed close under the existing engine contract; incoming returns use previous holdings. Weekly Friday resets pay 10 bps commission and 5 bps slippage under existing turnover conventions. Cash earns zero.", "",
        "OLS and WLS (W = sqrt(market cap)) fit every complete 24-asset cross-section. Long-only active risk uses an equal-weight benchmark re-established at each prior close. Long-short active risk uses cash. The engine's realized benchmark metrics remain separate from this model forecast.", "",
        "Risk uses the latest 20 earlier fits, with 10 observations required, sample covariance and sample residual variance. Forecasts exclude the current realized return. Diagonal specific covariance and zero factor/specific covariance are modeling assumptions. Specific return measures residual return. Economic alpha, covariance calibration, and forecast accuracy require separate evidence.", "",
        "Complete finite static panels define this diagnostic. Warmup exposure gaps and collinearity produce retained refusals. Terminal-event integration and changing regression universes remain open. Every attempted case retains started and terminal records. The full synthetic interval is a diagnostic sample; holdout inference and parameter selection are outside this run.", "",
        "Arithmetic contribution sums describe sums of one-period returns; compounded portfolio return has its own column. Multi-period geometric attribution remains open.", "",
        "## All attempted cases", "",
        "| case | status | compounded net | gross sum | specific sum | cost sum | annualized forecast TE | max identity error |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for case in result['cases']:
        if case['status'] == 'success':
            lines.append(f"| {case['case_id']} | success | {case['compounded_net_return']:.8f} | {case['gross_arithmetic_sum']:.8f} | {case['specific_arithmetic_sum']:.8f} | {case['cost_arithmetic_sum']:.8f} | {case['latest_annualized_tracking_error']:.8f} | {case['max_identity_error']:.3g} |")
        else:
            lines.append(f"| {case['case_id']} | {case['status']}: {case.get('reason', '')} | | | | | | |")
    lines += ["", "## Factor contribution sums", "", "| case | " + " | ".join(("Market", "Size", "Value", "Momentum", "Volatility", "Liquidity")) + " |", "| --- | " + " | ".join(["---:"] * 6) + " |"]
    for case in result['cases']:
        if case['status'] == 'success':
            lines.append("| " + case['case_id'] + " | " + " | ".join(f"{v:.8f}" for v in case['factor_arithmetic_sums'].values()) + " |")
    lines += ["", "## Latest active-risk decomposition", "",
              "| case | factor variance | specific variance | total active variance | estimated intervals | warmup intervals |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for case in result['cases']:
        if case['status'] == 'success':
            factor = case['latest_factor_variance']
            specific = case['latest_specific_variance']
            lines.append(f"| {case['case_id']} | {factor:.10f} | {specific:.10f} | {factor + specific:.10f} | {case['risk_estimated_intervals']} | {case['risk_warmup_intervals']} |")
    lines += ["", "## Latest portfolio factor exposures", "",
              "| case | Market | Size | Value | Momentum | Volatility | Liquidity |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for case in result['cases']:
        if case['status'] == 'success':
            lines.append("| " + case['case_id'] + " | " + " | ".join(f"{v:.8f}" for v in case['latest_exposures'].values()) + " |")
    successes = [case for case in result['cases'] if case['status'] == 'success']
    lines += ["", f"Recorded cases: {len(result['cases'])}; successful books: {len(successes)}; negative compounded net-return books: {sum(c['compounded_net_return'] < 0 for c in successes)}.", "", f"Reproduce: `{COMMAND}`.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    run_risk_attribution_demo()
