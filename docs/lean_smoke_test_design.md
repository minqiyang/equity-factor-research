# LEAN Smoke-Test Design

Date: 2026-06-04

This document designs a future QuantConnect/LEAN smoke test for the local
equity factor research workflow. It is documentation only. It does not add a
LEAN algorithm, project scaffold, data access path, credentials, brokerage
connection, order-execution path, live trading, paper trading, or
profitability claim.

The design translates the LEAN parity checklist into a first reviewable smoke
test shape. A later implementation PR must still define its exact files,
tests, and scope before adding code.

## 1. Purpose

The smoke test should answer one narrow question:

```text
Can a future LEAN backtest reproduce the local research workflow shape with
auditable timing, assumptions, diagnostics, and caveats?
```

It should not answer whether any factor is profitable, robust, tradable, or
ready for deployment.

## 2. Non-Goals

This design does not authorize:

- a LEAN algorithm file.
- a QuantConnect project scaffold.
- real data fetching or downloading from this repository.
- credentials, tokens, account IDs, secrets, or external platform access.
- live trading, paper trading, brokerage integration, or a real order path.
- parameter search, alpha mining, or best-run selection.
- a profitability, performance, or investment recommendation claim.
- bulk WorldQuant 101 implementation.

## 3. Future Smoke-Test Preconditions

A future implementation stage should start only if these preconditions are
true:

| Preconditions | Evidence before implementation |
| --- | --- |
| Repository state is clean and synced. | `git status -sb`, latest `main`, no open PR gate. |
| Baseline validation passes. | `python -m pytest -q` and `python -m compileall src tests research`. |
| Scope is explicitly limited. | Branch name, intended file list, and out-of-scope list before editing. |
| No external access is required for local development. | The implementation does not need credentials or local data downloads. |
| The smoke test is simulated research only. | PR description and experiment note preserve caveats. |

If any future stage needs credentials, external platform access, real data
downloads, live or paper trading, broker connectivity, or result
interpretation as investment evidence, stop before implementation.

## 4. Minimal Future Scenario

The first LEAN smoke test should be intentionally narrow:

| Area | Initial design |
| --- | --- |
| Asset class | US equities only. |
| Resolution | Daily bars. |
| Universe | Small, liquid, platform-defined universe for debuggability. |
| Benchmark | `SPY` or another documented broad US equity proxy. |
| Primary factor | 12-1 momentum from completed adjusted close history. |
| Optional feature-parity check | `alpha_009` as a logged research feature only, not order logic. |
| Portfolio shape | Simulated long-only equal-weight targets with a cash buffer. |
| Rebalance | Monthly scheduled event after market open. |
| Costs | Explicit fee and slippage assumptions recorded before reviewing output. |
| Diagnostics | Eligibility, skipped-symbol counts, selected symbols, latest completed bar date, and diagnostic export metadata. |

The smoke test should prefer one simple factor as the actual portfolio signal.
`alpha_009` should remain a feature-parity candidate unless a separate reviewed
stage explicitly makes it part of portfolio construction.

## 5. Timing Contract

The future implementation should make these dates distinguishable:

| Date concept | Required meaning |
| --- | --- |
| Algorithm time | The LEAN event timestamp when the rebalance handler runs. |
| Latest completed data date | The most recent daily bar allowed in the factor calculation. |
| Feature date | The date attached to the factor score. |
| Simulated order date | The date simulated portfolio targets are submitted in the engine. |
| Evaluation date | The later period used only for diagnostic return evaluation. |

Required timing assertions:

- no same-day close may be used for an after-open rebalance.
- no future returns may enter signal calculation.
- no future universe membership may enter symbol selection.
- no target weights may be computed before required history exists.
- any mismatch between local pandas dates and LEAN event times must be logged.

## 6. Smoke-Test Assertions

| Assertion group | Required assertion |
| --- | --- |
| Warm-up | No simulated trades or targets before required lookback history exists. |
| Rebalance schedule | Portfolio changes occur only during the documented monthly schedule. |
| Signal cutoff | Factor scores use completed daily bars only. |
| Missing history | Symbols with insufficient, stale, missing, or non-positive history are skipped and counted. |
| Long-only exposure | Target weights are non-negative. |
| Leverage | Total target exposure is less than or equal to one after the cash buffer. |
| Benchmark | Benchmark symbol and data normalization are recorded. |
| Costs | Fee and slippage model names and parameters are recorded. |
| Diagnostics | Eligibility, skip counts, selected symbols, factor metadata, and coverage counts are preserved. |
| Caveats | Output is labeled simulated research output only. |

## 7. Diagnostics To Preserve

A future smoke run should preserve enough diagnostic information to compare
against the local workflow before reviewing summary metrics:

- parameter set and factor formula.
- start date, end date, universe rule, benchmark, and cash buffer.
- latest completed bar date used at each rebalance.
- eligible, skipped, selected, and missing-history counts.
- selected symbols and target weights at each rebalance.
- fee and slippage assumptions.
- rejected or constrained simulated orders, if any.
- diagnostic panel coverage for IC, Rank IC, and quantile-spread review.
- known local-vs-LEAN mismatches.

Forward-return panels should be treated as evaluation targets only. They must
not be used for signal generation, ranking, universe selection, or rebalance
decisions.

## 8. Local Comparison Design

The first comparison should prioritize behavior over metrics:

| Comparison area | Review question |
| --- | --- |
| Rebalance dates | Are differences explained by calendar and scheduling assumptions? |
| Signal dates | Is the data cutoff before simulated portfolio formation? |
| Universe coverage | Are skipped and selected symbols explainable from history and eligibility logs? |
| Weights | Do targets remain long-only and respect the cash buffer? |
| Costs | Are local turnover costs and LEAN simulated cost assumptions clearly different when they differ? |
| Diagnostics | Are IC, Rank IC, and quantile spread coverage counts visible before summary metrics are reviewed? |

The review should document mismatches instead of tuning assumptions merely to
make outputs look closer.

## 9. Experiment Record Shape

A future LEAN smoke-test record should include:

- hypothesis: workflow-shape smoke test, not performance validation.
- non-goals and guardrails.
- factor formula and parameters.
- universe, benchmark, date range, and sample split.
- fee, slippage, cash buffer, schedule, and simulated execution assumptions.
- diagnostic coverage and skip-count summary.
- local-vs-LEAN mismatch notes.
- failures, weak evidence, and caveats.
- statement that the output is not investment advice and not a profitability
  claim.

The experiment record should not hide failed runs or promote a best run.

## 10. Stop Conditions

Stop a future implementation stage if it requires:

- credentials, tokens, account IDs, or secrets.
- external data download code in this repository.
- live trading, paper trading, brokerage connection, or real order routing.
- changing source, tests, research scripts, or reports outside the stated
  scope.
- weakening tests or silently filling missing data.
- interpreting simulated output as evidence of profitability.
- a broad LEAN implementation instead of a smoke-test-sized stage.

## 11. Recommended Next Stage

After this design note is reviewed and merged, the next safe stage should be a
minimal implementation planning checkpoint for the first LEAN code PR. That
checkpoint should choose the exact file layout, local validation strategy, and
review gates before any algorithm or project scaffold is added.

If that checkpoint would require external access, credentials, real data
downloads, live or paper trading, brokerage integration, or performance
interpretation, stop instead of proceeding.
