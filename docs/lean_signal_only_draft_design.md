# LEAN Signal-Only Draft Design

Date: 2026-06-04

This document defines the safe boundary for a future LEAN-adjacent
signal-only draft.

It is documentation only. It does not add runnable LEAN code,
`AlgorithmImports`, `QCAlgorithm`, `config.json`, local or cloud LEAN
execution, real data access, data downloads, credentials, live trading, paper
trading, brokerage integration, order execution, or profitability claims.

## 1. Purpose

The purpose of the next LEAN-adjacent code stage is to make the signal
translation boundary reviewable without making the repository runnable on
QuantConnect/LEAN yet.

The future draft should describe what the research signal would need to know
at a point in time:

- the signal name and research feature being represented.
- the required lookback and skip-window assumptions.
- the date-alignment contract for completed data.
- the input field names required for validation.
- the signal ranking and eligibility metadata expected by a later LEAN
  translation.
- the caveats that keep the artifact research-only and non-executable.

The future draft should not evaluate factor performance or claim that any
stock-selection signal is useful, profitable, robust, or trading-ready.

## 2. Decision

The first future LEAN-adjacent code stage should be signal-only and
metadata-only.

It should not import LEAN runtime symbols. In particular, it should not use
`AlgorithmImports`, subclass `QCAlgorithm`, create a `config.json`, run LEAN,
subscribe to platform data, call history APIs, create portfolio targets, place
orders, model fills, model brokerage, or produce backtest results.

The approved future code boundary, if this design is reviewed and merged, is:

| Future file | Role |
| --- | --- |
| `lean/signal_only_momentum_draft.py` | Pure-Python signal metadata and review helpers for a 12-1 momentum-style signal boundary. |
| `tests/test_lean_signal_only_draft_scope.py` | Static tests proving the draft remains signal-only, data-free, credential-free, order-free, and non-runnable. |

The future code stage may also update `lean/README.md`, `docs/engineering_log.md`,
`docs/decision_log.md`, and `CHANGELOG.md` if the PR documents the exact scope.

## 3. Signal Boundary

The future signal-only draft should be allowed to define metadata such as:

- `SIGNAL_DRAFT_STATUS`, with a value that states the draft is non-runnable.
- `IS_EXECUTABLE_LEAN_ALGORITHM = False`.
- `SIGNAL_NAME`, such as `momentum_12_1_signal_only_draft`.
- lookback metadata for 12-month trailing return with a 1-month skip window.
- required input fields, such as completed adjusted-close history.
- a timing contract that distinguishes algorithm evaluation time, latest
  completed data date, feature date, and downstream review date.
- diagnostic field names for eligibility, skipped symbols, ranked symbols,
  benchmark metadata, caveats, and missing-input reasons.

The future draft should avoid portfolio and order semantics. It should not
name target weights, submitted orders, filled orders, brokerage model, fill
model, live mode, paper mode, or order execution behavior as implemented
fields. If downstream portfolio construction needs a placeholder, it should be
described as a future review boundary, not an implemented signal output.

## 4. Timing Contract

The future signal-only draft should preserve the repository's date-alignment
discipline.

Required timing fields:

| Field | Meaning |
| --- | --- |
| `algorithm_time` | The hypothetical time at which a future LEAN algorithm would evaluate the signal. |
| `latest_completed_data_date` | The latest date whose input data is assumed complete before evaluation. |
| `feature_date` | The date associated with the computed signal feature. |
| `signal_review_date` | The date on which the signal metadata would be reviewed before any downstream portfolio decision. |

The future draft should not define an order date or rebalance execution date as
an implemented behavior. Those concepts belong to a later simulated portfolio
or runnable LEAN backtest design, not the signal-only draft.

## 5. Static Validation Plan

The future code PR should include static tests that fail if the signal-only
draft drifts into runtime, data, credential, or trading behavior.

Required checks:

- expected files exist and no `lean/config.json` exists.
- `IS_EXECUTABLE_LEAN_ALGORITHM` remains false.
- no `AlgorithmImports`, `QCAlgorithm`, or LEAN runtime inheritance.
- no `requests`, `yfinance`, Alpaca, CCXT, vendor download helpers, or API
  download logic.
- no credential reads, account IDs, tokens, environment variable reads, or
  local secret paths.
- no live trading, paper trading, brokerage setup, order calls, liquidation
  calls, target-holding calls, fill modeling, or order-routing semantics.
- required timing fields and caveat fields are present.
- no profitability, robustness, investment-advice, or trading-readiness claims.

Recommended validation commands for the future code PR:

```powershell
python -m pytest -q tests/test_lean_signal_only_draft_scope.py
python -m pytest -q
python -m compileall src tests research
python -m compileall lean
git diff --check
```

These commands should not require a local LEAN installation, a QuantConnect
account, credentials, network access, real market data, or cloud execution.

## 6. Out Of Scope

The signal-only draft must not add:

- runnable LEAN algorithm code.
- `AlgorithmImports`, `QCAlgorithm`, `config.json`, or local/cloud LEAN run
  instructions.
- real market data fetching, downloads, API clients, vendor libraries, or
  request-based data access.
- credentials, tokens, account IDs, environment variables, or secret handling.
- live trading, paper trading, brokerage integration, order routing, portfolio
  target calls, liquidation calls, or fill semantics.
- backtest output, report output, or experiment output.
- changes to `src/`, research scripts, reports, backtester, metrics, CSV
  loader, diagnostics, normalization, combination, or alpha modules.
- profitability, robustness, investment-advice, or trading-readiness claims.

## 7. Stop Conditions

Stop before creating a future signal-only code PR if the stage requires:

- LEAN runtime imports to express the signal boundary.
- local or cloud LEAN execution.
- real data fetching, downloads, platform subscriptions, or history calls.
- credentials, account access, cloud configuration, or environment secrets.
- live or paper trading semantics.
- brokerage, order, fill, slippage, fee, or portfolio implementation.
- interpreting simulated output as evidence that a strategy works.
- weakening existing static guardrail tests.

If any stop condition is triggered, the correct next action is a blocker report
or another documentation-only decision, not implementation.

## 8. Recommended Next Stage

After this design is reviewed and merged, the next safe stage is:

```text
Implement pure-Python LEAN signal-only momentum draft with static guardrail tests
```

That stage should be a small code PR limited to the approved future files and
durable logs. It should pause after opening a ready-for-review PR and must not
merge itself.
