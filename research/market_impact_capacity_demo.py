"""Generated capacity scenarios with causal liquidity and retained attempt evidence."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import math
from typing import Any

import numpy as np
import pandas as pd

from backtest.long_short import run_long_short_backtest
from backtest.market_impact import MarketImpactValidationError, SquareRootImpactModel
from backtest.portfolio import (
    BacktestValidationError,
    capture_backtest_source_provenance,
    run_long_only_backtest,
)
from reporting.experiment_log import write_experiment_log
from research.demo_v0 import append_attempt_record

DEFAULT_REPORT_PATH = (
    Path(__file__).resolve().parents[1] / "reports/market_impact_capacity_demo.md"
)
COMMAND = "PYTHONPATH=src:. python -m research.market_impact_capacity_demo"
AUM_TIERS = (1e6, 1e7, 5e7, 1e8, 5e8, 1e9)
MODES = ("fixed_control", "raise", "throttle", "penalize")
ENGINES = ("long_only", "long_short")
# Annualized Sharpe needs at least one trading month of measured daily returns.
MIN_SHARPE_OBSERVATIONS = 21


def synthetic_inputs(scope: str):
    """Generate a predeclared roster and score panel independently of realized returns."""
    if scope not in ("hand_panel", "synthetic_cohort"):
        raise ValueError("unknown generated scope")
    small = scope == "hand_panel"
    rows, assets = (14, 4) if small else (65, 20)
    dates = pd.bdate_range("2024-01-01", periods=rows, name="source_close")
    columns = pd.Index([f"SEC_{i:03d}" for i in range(assets)], name="permanent_id")
    day = np.arange(rows)[:, None]
    identity = np.arange(assets)[None, :]
    # Scores alternate on a known calendar; price paths are explicit scenarios.
    scores = np.broadcast_to(identity + 1.0, (rows, assets)).copy()
    scores[(np.arange(rows) // 20) % 2 == 1] *= -1
    if small:
        prices = (10.0 + 10 * identity) * (1.0005 + identity * 0.0005) ** day
        volumes = np.full((rows, assets), 10000.0)
    else:
        returns = (
            0.0001 + identity * 0.00005 + 0.012 * np.sin(day * 0.71 + identity * 0.27)
        )
        prices = (50.0 + 2 * identity) * np.cumprod(1.0 + returns, axis=0)
        volumes = np.broadcast_to(20000.0 + 3000 * identity, (rows, assets)).copy()
    return (
        pd.DataFrame(prices, index=dates, columns=columns),
        pd.DataFrame(scores, index=dates, columns=columns),
        pd.DataFrame(volumes, index=dates, columns=columns),
    )


def _finite_or_none(value):
    return float(value) if math.isfinite(float(value)) else None


def capacity_brackets(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Retain adjacent tested sign crossings and unavailable intervals per scenario."""
    result = []
    groups = sorted({(c["scope"], c["engine"], c["mode"]) for c in cases})
    for scope, engine, mode in groups:
        rows = sorted(
            (
                c
                for c in cases
                if (c["scope"], c["engine"], c["mode"]) == (scope, engine, mode)
            ),
            key=lambda c: c["aum"],
        )
        for lower, upper in zip(rows, rows[1:]):
            left, right = (
                lower.get("benchmark_excess_return"),
                upper.get("benchmark_excess_return"),
            )
            if left is None or right is None:
                status = "unavailable"
            elif left > 0 and right <= 0:
                status = "positive_to_nonpositive"
            elif left <= 0 and right > 0:
                status = "nonpositive_to_positive"
            else:
                status = "no_observed_crossing"
            result.append(
                dict(
                    scope=scope,
                    engine=engine,
                    mode=mode,
                    lower_aum=lower["aum"],
                    upper_aum=upper["aum"],
                    status=status,
                )
            )
    return result


def evaluate_capacity(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    volumes: pd.DataFrame,
    *,
    scope: str,
    evaluation_start: pd.Timestamp,
    evaluation_end: pd.Timestamp,
    price_basis: str,
    volume_basis: str,
    lookback: int = 20,
    aum_tiers=AUM_TIERS,
    modes=MODES,
    engines=ENGINES,
    attempt_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Evaluate supplied compatible panels; callers own data authorization and provenance."""
    tiers = tuple(aum_tiers)
    if (
        not tiers
        or any(
            isinstance(x, (bool, np.bool_))
            or not isinstance(x, (int, float))
            or not math.isfinite(x)
            or x <= 0
            for x in tiers
        )
        or len(set(tiers)) != len(tiers)
    ):
        raise ValueError("AUM tiers require unique finite positive numbers")
    if (
        not modes
        or any(mode not in MODES for mode in modes)
        or not engines
        or any(engine not in ENGINES for engine in engines)
    ):
        raise ValueError(
            "capacity modes and engines require supported nonempty selections"
        )
    cases = []
    for engine in engines:
        for mode in modes:
            for aum in tiers:
                case = dict(
                    case_id=f"{scope}_{engine}_{mode}_{aum:g}",
                    scope=scope,
                    engine=engine,
                    mode=mode,
                    aum=float(aum),
                )
                start = {
                    **case,
                    "command": COMMAND,
                    "status": "started",
                    "data_scope": scope,
                }
                attempt_id = (
                    append_attempt_record(attempt_path, start)["attempt_id"]
                    if attempt_path
                    else None
                )
                try:
                    benchmark = (
                        prices.loc[evaluation_start:evaluation_end]
                        / prices.loc[evaluation_start]
                    ).mean(axis=1, skipna=False)
                    if not np.isfinite(benchmark).all() or benchmark.le(0).any():
                        raise ValueError(
                            "capacity benchmark requires a complete positive supplied cohort"
                        )
                    model = (
                        None
                        if mode == "fixed_control"
                        else SquareRootImpactModel(
                            mode=mode, lookback=lookback, fixed_bps=2
                        )
                    )
                    common = dict(
                        evaluation_start=evaluation_start,
                        evaluation_end=evaluation_end,
                        initial_capital=float(aum),
                        rebalance_frequency="W-FRI",
                        signal_lag_periods=1,
                        transaction_cost_bps=10.0,
                        slippage_bps=5.0 if model is None else 0.0,
                        impact_model=model,
                        impact_volumes=volumes if model else None,
                        impact_price_basis=price_basis if model else None,
                        impact_volume_basis=volume_basis if model else None,
                    )
                    if engine == "long_only":
                        book = run_long_only_backtest(
                            prices,
                            signals,
                            top_n=max(1, len(prices.columns) // 4),
                            source_provenance=capture_backtest_source_provenance(
                                prices, signals
                            ),
                            **common,
                        )
                        weights = book.holdings
                        sharpe = book.metrics["sharpe_ratio"]
                    else:
                        book = run_long_short_backtest(
                            prices, signals, quantiles=4, **common
                        )
                        weights = book.net_holdings
                        sharpe = book.metrics["sharpe"]
                    net_return = float(book.equity_curve.iloc[-1] / aum - 1.0)
                    gross_path_return = float((1 + book.gross_returns).prod() - 1)
                    benchmark_return = float(
                        benchmark.iloc[-1] / benchmark.iloc[0] - 1.0
                    )
                    traded = float(book.executed_trade_values.abs().to_numpy().sum())
                    slippage = float(book.slippage_cost_series.sum())
                    rates = book.trade_participation_rates.to_numpy()
                    finite_rates = rates[np.isfinite(rates)]
                    measured_returns = len(book.equity_curve) - 1
                    case.update(
                        status="success",
                        measured_returns=measured_returns,
                        net_sharpe=(
                            _finite_or_none(sharpe)
                            if measured_returns >= MIN_SHARPE_OBSERVATIONS
                            else None
                        ),
                        net_return=net_return,
                        gross_path_return=gross_path_return,
                        benchmark_return=benchmark_return,
                        benchmark_excess_return=net_return - benchmark_return,
                        slippage_dollars=slippage,
                        traded_notional=traded,
                        weighted_slippage_bps=10000 * slippage / traded
                        if traded
                        else 0.0,
                        summed_turnover=float(book.turnover.sum()),
                        max_participation=None
                        if model is None
                        else float(finite_rates.max()),
                        final_pending_abs_shares=float(
                            book.pending_trade_shares.iloc[-1].abs().sum()
                        ),
                        cancelled_abs_shares=float(
                            book.cancelled_trade_shares.abs().to_numpy().sum()
                        ),
                        final_net_exposure=float(weights.iloc[-1].sum()),
                        final_gross_exposure=float(weights.iloc[-1].abs().sum()),
                        model=None if model is None else asdict(model),
                        path=[
                            dict(
                                date=date.isoformat(),
                                equity=float(book.equity_curve.loc[date]),
                                cash=float(book.cash_balance.loc[date]),
                                slippage_dollars=float(
                                    book.slippage_cost_series.loc[date]
                                ),
                                turnover=float(book.turnover.loc[date]),
                                absolute_traded_dollars=float(
                                    book.executed_trade_values.loc[date].abs().sum()
                                ),
                                pending_abs_shares=float(
                                    book.pending_trade_shares.loc[date].abs().sum()
                                ),
                                cancelled_abs_shares=float(
                                    book.cancelled_trade_shares.loc[date].abs().sum()
                                ),
                            )
                            for date in book.equity_curve.index
                        ],
                    )
                except BaseException as exc:
                    status = (
                        "refused"
                        if isinstance(
                            exc, (MarketImpactValidationError, BacktestValidationError)
                        )
                        else "failure"
                    )
                    if not isinstance(exc, Exception):
                        status = "interrupted"
                    case.update(
                        status=status,
                        reason=getattr(exc, "reason", type(exc).__name__),
                        error_type=type(exc).__name__,
                    )
                    if status == "interrupted":
                        if attempt_path:
                            append_attempt_record(
                                attempt_path, {**start, **case}, attempt_id=attempt_id
                            )
                        raise
                cases.append(case)
                if attempt_path:
                    append_attempt_record(
                        attempt_path, {**start, **case}, attempt_id=attempt_id
                    )
    return cases


def render_report(result):
    lines = [
        "# Market Impact and Capacity Synthetic Diagnostic",
        "",
        "Evidence ceiling: **DIAGNOSTIC_ONLY**. Every source panel is generated from a predeclared roster and calendar.",
        "",
        "The hand panel contains 14 closes and four permanent IDs; the cohort contains 65 closes and 20 permanent IDs. "
        "Evaluation starts after 3 and 21 warm-up rows respectively. Weekly Friday targets use lag-1 scores. "
        "Complete lagged 2-row and 20-row windows estimate dollar ADV and sample daily volatility.",
        "",
        "Each ordinary dollar traded pays 10 bps commission. Fixed controls pay 5 bps slippage under legacy accounting. "
        "The self-financing impact scenarios use eta=0.25, fixed=2 bps, cap=10%, min_ADV=$100,000, and penalty=10 bps. "
        "Price and volume bases are both raw. Sell proceeds and existing cash fund buys and costs. "
        "Liquidity-deferred shares retry; target replacement and funding shortfalls produce cancellations.",
        "",
        "The benchmark holds equal initial dollars of every predeclared security, with zero benchmark costs. "
        "Excess return is the difference of cumulative net strategy and benchmark returns. "
        "Gross path return compounds pre-cost returns on the actual executed holdings; fixed-control comparisons also change the accounting convention. "
        "Sharpe uses measured daily net returns, a zero risk-free rate, population standard deviation, and 252-day annualization. "
        f"Books with fewer than {MIN_SHARPE_OBSERVATIONS} measured daily returns report Sharpe as unavailable.",
        "",
        "## Capacity curves by tested AUM",
        "",
        "| scope | engine | mode | AUM | status | net Sharpe | net return | benchmark excess | weighted slippage bps | max participation | final deferred shares | reason |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]

    def number(case, key):
        value = case.get(key)
        return "unavailable" if value is None else f"{value:.6f}"

    for case in result["cases"]:
        lines.append(
            f"| {case['scope']} | {case['engine']} | {case['mode']} | {case['aum']:,.0f} | {case['status']} | "
            + " | ".join(
                number(case, key)
                for key in (
                    "net_sharpe",
                    "net_return",
                    "benchmark_excess_return",
                    "weighted_slippage_bps",
                    "max_participation",
                    "final_pending_abs_shares",
                )
            )
            + f" | {case.get('reason', '')} |"
        )
    lines += [
        "",
        "## Adjacent AUM crossing evidence",
        "",
        "Every adjacent tested interval remains in JSON. Positive-to-nonpositive brackets follow below. "
        "A refused endpoint makes its interval unavailable. No observed crossing leaves capacity unresolved by this grid. "
        "Repeated or reverse crossings remain visible; no interpolation or unique capacity estimate is applied.",
        "",
    ]
    crossings = [
        row
        for row in result["capacity_brackets"]
        if row["status"] == "positive_to_nonpositive"
    ]
    for row in crossings:
        lines.append(
            f"- {row['scope']} / {row['engine']} / {row['mode']}: ${row['lower_aum']:,.0f} to ${row['upper_aum']:,.0f}."
        )
    if not crossings:
        lines.append("The tested grid contains zero positive-to-nonpositive brackets.")
    lines += [
        "",
        "## Evidence and limitations",
        "",
        "The square-root coefficient and quadratic penalty are declared scenarios. Short-sale borrow fees, recalls, intraday execution, "
        "corporate-action share conversion, and empirical calibration remain open. Partial fills and price drift create actual exposures "
        "that differ from target neutrality and position caps. A final deferred queue remains an unexecuted simulation state. "
        "Actual dollars divided by lagged ADV measure forecast participation. Vendor price/volume declarations require separate verification. "
        "The scenario panel establishes accounting behavior and illustrative AUM sensitivity; empirical strategy capacity remains unmeasured.",
        "",
        "All successes, negative returns, refusals, failures, and interrupted attempts are retained. JSON includes per-row cash, equity, "
        "cost, turnover, pending, and cancellation totals. Append-only start/outcome events preserve reruns.",
        "",
        f"Reproduce with `{COMMAND}`.",
        "",
    ]
    return "\n".join(lines)


def run_market_impact_capacity_demo(
    *, report_path=DEFAULT_REPORT_PATH, write_outputs=True, aum_tiers=AUM_TIERS
):
    report_path = Path(report_path)
    attempts = (
        report_path.with_name(report_path.stem + "_attempts.jsonl")
        if write_outputs
        else None
    )
    cases = []
    for scope in ("hand_panel", "synthetic_cohort"):
        prices, signals, volumes = synthetic_inputs(scope)
        lookback = 2 if scope == "hand_panel" else 20
        cases.extend(
            evaluate_capacity(
                prices,
                signals,
                volumes,
                scope=scope,
                evaluation_start=prices.index[lookback + 1],
                evaluation_end=prices.index[-1],
                price_basis="raw",
                volume_basis="raw",
                lookback=lookback,
                aum_tiers=aum_tiers,
                attempt_path=attempts,
            )
        )
    result = dict(
        evidence_ceiling="DIAGNOSTIC_ONLY",
        cases=cases,
        capacity_brackets=capacity_brackets(cases),
    )
    if write_outputs:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_report(result), encoding="utf-8")
        write_experiment_log(
            log_path=report_path.with_suffix(".json"),
            experiment_id="m4_5_market_impact_capacity_synthetic",
            title="Synthetic market impact and capacity curves",
            experiment_type="market_impact_capacity_synthetic",
            summary="Both engines across all declared AUM and participation modes with every outcome retained.",
            config=dict(aum_tiers=aum_tiers, modes=MODES, engines=ENGINES),
            assumptions=dict(
                evidence_ceiling="DIAGNOSTIC_ONLY",
                data_scope="generated_only",
                benchmark="cost_free_equal_initial_dollar_static_cohort",
            ),
            outputs=dict(
                markdown_report=report_path.name,
                experiment_log=report_path.with_suffix(".json").name,
                attempt_log=attempts.name,
            ),
            metrics=dict(cases=cases),
            diagnostics=dict(capacity_brackets=result["capacity_brackets"]),
            next_action="Independent exact-candidate accounting review; empirical calibration remains open.",
        )
    if any(case["status"] == "failure" for case in cases):
        raise RuntimeError(
            "unexpected capacity failures retained in reports and attempt log"
        )
    return result


if __name__ == "__main__":
    result = run_market_impact_capacity_demo()
    print(
        f"Retained {len(result['cases'])} capacity scenarios in {DEFAULT_REPORT_PATH}"
    )
