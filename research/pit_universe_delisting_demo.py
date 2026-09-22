"""Synthetic PIT membership and immediate terminal-cash walking skeleton."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest.long_short import run_long_short_backtest
from backtest.portfolio import BacktestValidationError, capture_backtest_source_provenance, run_long_only_backtest
from data.constituent_table import build_pit_membership_mask
from reporting.experiment_log import write_experiment_log
from research.demo_v0 import append_attempt_record


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "pit_universe_delisting_demo.md"
COMMAND = "python -m research.pit_universe_delisting_demo"


def synthetic_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return a predeclared synthetic roster with separate permanent identities."""
    dates = pd.bdate_range("2024-01-01", periods=12, name="date")
    prices = pd.DataFrame({
        "SEC_OLD": [10.0]*5+[np.nan]*7,
        "SEC_NEW": 1000.0*1.01**np.arange(12),
        "SEC_REF": 20.0,
    }, index=dates)
    signals = pd.DataFrame({"SEC_OLD": 3.0, "SEC_NEW": 4.0, "SEC_REF": 1.0}, index=dates)
    membership = pd.DataFrame({
        "symbol": ["REUSED", "REUSED", "REFERENCE"],
        "permanent_id": ["SEC_OLD", "SEC_NEW", "SEC_REF"],
        "start_date": [dates[0], dates[5], dates[0]],
        "end_date": [dates[5], pd.NaT, pd.NaT],
        "start_known_at": [dates[0], dates[3], dates[0]],
        "end_known_at": [dates[3], pd.NaT, pd.NaT],
    })
    events = pd.DataFrame([{
        "event_id": "synthetic-old-final-cash", "permanent_id": "SEC_OLD",
        "effective_date": dates[5], "reference_date": dates[4], "known_at": dates[3],
        "terminal_return": -.6, "return_basis": "prior_observed_close_to_cash",
    }])
    return prices, signals, membership, events


def run_pit_universe_delisting_demo(
    *, report_path: Path = DEFAULT_REPORT_PATH, write_outputs: bool = True,
) -> dict[str, Any]:
    """Retain four valid comparisons and two explicit missing-evidence refusals."""
    report_path = Path(report_path)
    log_path = report_path.with_suffix(".json")
    attempt_path = report_path.with_name(report_path.stem + "_attempts.jsonl")
    prices, signals, membership, events = synthetic_inputs()
    mask = build_pit_membership_mask(membership, prices.index, list(prices.columns))
    cases = []
    unexpected = []
    for kind in ("long_only", "long_short"):
        for scope in ("static_roster", "pit_membership", "missing_terminal_evidence"):
            case_id = f"{kind}_{scope}"
            expected_refusal = scope == "missing_terminal_evidence"
            start = {"case_id": case_id, "command": COMMAND, "status": "started", "data_scope": "synthetic"}
            attempt_id = None
            if write_outputs:
                attempt_id = append_attempt_record(attempt_path, start)["attempt_id"]
            case: dict[str, Any] = {"case_id": case_id, "expected_refusal": expected_refusal}
            try:
                kwargs = dict(
                    evaluation_start=prices.index[0], evaluation_end=prices.index[-1],
                    rebalance_frequency="D", initial_capital=1000.0,
                    transaction_cost_bps=10.0, slippage_bps=5.0,
                    constituent_intervals=membership if scope != "static_roster" else None,
                    terminal_events=None if expected_refusal else events,
                )
                if kind == "long_only":
                    book = run_long_only_backtest(
                        prices, signals, source_provenance=capture_backtest_source_provenance(prices, signals),
                        top_n=1, **kwargs,
                    )
                    weights = book.holdings
                else:
                    book = run_long_short_backtest(prices, signals, quantiles=2, **kwargs)
                    weights = book.net_holdings
                case.update(
                    status="unexpected_success" if expected_refusal else "success",
                    final_equity=float(book.equity_curve.iloc[-1]),
                    terminal_cashflows=float(book.terminal_cashflows.to_numpy().sum()),
                    terminal_event_log=book.terminal_event_log,
                    path=[{
                        "date": date.isoformat(), "equity": float(book.equity_curve.loc[date]),
                        "cash": float(book.cash_balance.loc[date]),
                        "terminal_cashflow": float(book.terminal_cashflows.loc[date].sum()),
                        "holdings": {asset: float(value) for asset, value in weights.loc[date].items()},
                    } for date in prices.index],
                )
                if expected_refusal:
                    unexpected.append(case_id)
            except BaseException as exc:
                expected = expected_refusal and isinstance(exc, BacktestValidationError) and exc.reason == "incoming_price_invalid"
                case.update(status="refused" if expected else "failure", error_type=type(exc).__name__,
                            reason=getattr(exc, "reason", type(exc).__name__))
                if not isinstance(exc, Exception):
                    if write_outputs:
                        append_attempt_record(attempt_path, {**start, **case, "status": "interrupted"}, attempt_id=attempt_id)
                    raise
                if not expected:
                    unexpected.append(case_id)
            cases.append(case)
            if write_outputs:
                append_attempt_record(attempt_path, {**start, **case}, attempt_id=attempt_id)
    result = {
        "evidence_ceiling": "DIAGNOSTIC_ONLY", "cases": cases,
        "membership": membership.astype(object).where(membership.notna(), None).to_dict("records"),
        "terminal_events": events.to_dict("records"),
        "eligibility": [{"execution_date": date.isoformat(),
                         "decision_cutoff": prices.index[i-1].isoformat() if i else None,
                         "eligible_ids": list(mask.columns[mask.loc[date]])} for i, date in enumerate(prices.index)],
    }
    if write_outputs:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_report(result), encoding="utf-8")
        write_experiment_log(
            log_path=log_path, experiment_id="m4_4_pit_universe_delisting_synthetic",
            title="PIT universe and terminal cash synthetic comparison",
            experiment_type="pit_universe_delisting_synthetic",
            summary="Four complete synthetic books and two retained missing-terminal-evidence refusals.",
            config={"periods": 12, "initial_capital": 1000, "signal_lag_periods": 1,
                    "rebalance_frequency": "D", "transaction_cost_bps": 10, "slippage_bps": 5},
            assumptions={"evidence_ceiling": "DIAGNOSTIC_ONLY", "terminal_settlement_fee": 0,
                         "universe": "predeclared synthetic permanent-ID roster and known membership schedule",
                         "benchmark": "static-roster synthetic control; benchmark-relative alpha unestimated",
                         "availability_basis": "caller-declared daily source-close labels",
                         "cash_basis": "residual of existing postcost target-weight convention"},
            outputs={"markdown_report": report_path.name, "experiment_log": log_path.name, "attempt_log": attempt_path.name},
            metrics={"cases": cases}, diagnostics={key: value for key, value in result.items() if key != "cases"},
            next_action="Review synthetic accounting conformance and retain separate gates for private data and delayed recoveries.",
        )
    if unexpected:
        raise RuntimeError(f"unexpected synthetic case outcomes: {unexpected}")
    return result


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# PIT Universe and Terminal Cash Synthetic Diagnostic", "",
        "Evidence ceiling: DIAGNOSTIC_ONLY. Twelve generated source dates and three predeclared permanent IDs.",
        "The static roster and changing index membership are explicit synthetic controls. "
        "Historical ticker REUSED belongs to SEC_OLD and then SEC_NEW; their price columns remain separate.", "",
        "Targets use lag-1 signals and the membership schedule known at that decision cutoff. "
        "The old security's -60% complete terminal return settles once on 2024-01-08. "
        "Ordinary turnover pays 10 bps commission and 5 bps slippage; terminal redemption has zero extra modeled fee.", "",
        "Cash is the residual of the existing postcost target-weight convention. Signed terminal cash flows "
        "credit long proceeds and debit short liabilities. Same-close cash can fund a frozen eligible target. "
        "Unscheduled surviving long-short exposures drift until the next feasible scheduled reset.", "",
        "Delayed payments, unpriced receivables, stock consideration, full revision histories, and verified "
        "source calendars remain separate work. The declared availability labels and synthetic identities "
        "supply simulation conformance evidence.", "",
        "## All attempted cases", "",
        "| case | status | final equity | signed terminal proceeds | refusal reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for case in result["cases"]:
        equity = f"{case['final_equity']:.6f}" if "final_equity" in case else "undefined"
        proceeds = f"{case['terminal_cashflows']:.6f}" if "terminal_cashflows" in case else "undefined"
        lines.append(f"| {case['case_id']} | {case['status']} | {equity} | {proceeds} | {case.get('reason', '')} |")
    lines.extend(["", "## Knowledge cutoffs and eligibility", "",
                  "| execution close | decision cutoff | eligible permanent IDs |", "| --- | --- | --- |"])
    for row in result["eligibility"]:
        cutoff = row["decision_cutoff"][:10] if row["decision_cutoff"] else "initialization"
        lines.append(f"| {row['execution_date'][:10]} | {cutoff} | {', '.join(row['eligible_ids'])} |")
    for case in result["cases"]:
        if "path" not in case:
            continue
        lines.extend(["", f"## {case['case_id']}", "", "| close | equity | cash | terminal cash flow | signed closing holdings |",
                      "| --- | --- | --- | --- | --- |"])
        for row in case["path"]:
            weights = ", ".join(f"{key}={value:.6f}" for key, value in row["holdings"].items())
            lines.append(f"| {row['date'][:10]} | {row['equity']:.6f} | {row['cash']:.6f} | {row['terminal_cashflow']:.6f} | {weights} |")
    lines.extend(["", f"Reproduce with `{COMMAND}`. Append-only attempt events retain each start and outcome."])
    return "\n".join(lines)+"\n"


if __name__ == "__main__":
    run_pit_universe_delisting_demo()
    print(f"Wrote {DEFAULT_REPORT_PATH}")
