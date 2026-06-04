# LEAN Runnable Draft Readiness Decision

Date: 2026-06-04

This document decides whether the repository is ready to move from the merged
non-executing LEAN scaffold to a runnable QuantConnect/LEAN draft.

It is documentation only. It does not add a runnable LEAN algorithm,
`AlgorithmImports`, `QCAlgorithm`, `config.json`, local or cloud LEAN run, real
data path, data download, credential path, brokerage connection,
order-execution path, live trading, paper trading, or profitability claim.

## 1. Decision

The repository is not yet ready for a runnable LEAN draft under the current
guardrails.

Reason:

- A normal runnable LEAN algorithm would introduce runtime dependencies such
  as `AlgorithmImports` and `QCAlgorithm`.
- A normal LEAN backtest draft usually introduces platform data subscriptions,
  history access, benchmark subscriptions, scheduled events, portfolio target
  calls, order simulation, fee models, slippage models, and fill semantics.
- The active workflow guardrails still prohibit real market data fetching,
  downloads, credentials, live trading, paper trading, brokerage integration,
  order execution, and profitability claims.
- The merged scaffold tests intentionally confirm that the current LEAN file is
  metadata-only, non-executing, and free of runtime, credential, data-access,
  brokerage, and order-call dependencies.

Therefore the next safe stage should remain pre-runtime and should design a
signal-only LEAN draft boundary before any runnable code is added.

## 2. Evidence Reviewed

| Evidence | Finding |
| --- | --- |
| `AGENTS.md` | Requires small PRs, no live trading, no credentials, no future leakage, no test weakening, and durable logs for meaningful changes. |
| `PROJECT_SPEC.md` | Envisions a future QuantConnect/LEAN path but explicitly keeps live trading, brokerage integration, and unsupported profitability claims out of scope. |
| `docs/lean_scaffold_review_checklist.md` | Allows movement toward a runnable draft only if no account access, credentials, real data, live or paper trading, brokerage integration, order execution, or performance interpretation is required. |
| `lean/README.md` | States the current scaffold is not a runnable LEAN project and has no real market data path. |
| `lean/smoke_test_algorithm.py` | Keeps `IS_EXECUTABLE_LEAN_ALGORITHM` false and returns review metadata only. |
| `tests/test_lean_smoke_test_scope.py` | Guards against runtime LEAN imports, credential/data imports, brokerage calls, and order calls in the scaffold. |
| `docs/quantconnect_lean_plan.md` | Describes eventual LEAN concepts, but several concepts would require platform data, runtime semantics, and simulated order handling that are not yet approved for implementation. |

## 3. Current Blockers To Runnable Code

| Blocker | Why it blocks implementation now | Required resolution |
| --- | --- | --- |
| Runtime dependency boundary | A runnable LEAN file normally imports LEAN runtime symbols that are intentionally absent from the scaffold. | Define whether a future draft may import LEAN symbols and how local validation works when LEAN is not installed. |
| Data-source semantics | A runnable LEAN draft normally depends on platform subscriptions or history calls. | Define a signal-only draft that records data assumptions without fetching local or vendor data from this repository. |
| Order semantics | A complete LEAN backtest normally uses portfolio targets, liquidations, orders, fills, fees, and slippage. | Keep the next stage signal-only, or obtain an explicit reviewed scope that separates simulated LEAN order semantics from prohibited live or brokerage execution. |
| Credential and account boundary | A runnable LEAN project can easily drift toward account, cloud, or local runtime configuration. | Keep `config.json`, credentials, tokens, account IDs, environment reads, and cloud-run instructions out of the repository. |
| Result interpretation | A runnable backtest can create outputs that look like performance evidence. | Require experiment-log caveats and review gates before any simulated result is produced or interpreted. |

## 4. Approved Next Safe Stage

The next safe stage is:

```text
LEAN signal-only draft design
```

That stage should be documentation-only and should define:

- whether a future draft may import LEAN runtime symbols.
- whether the first draft is signal-only rather than portfolio/order-capable.
- exact future files if code is later approved.
- local validation when LEAN is not installed.
- static tests that distinguish signal metadata from order execution.
- stop conditions for data access, credentials, live or paper trading,
  brokerage, order routing, and performance interpretation.

The next stage should not add runnable code.

## 5. Stop Conditions For Any Future Code Stage

Stop before a future code stage if it requires:

- `AlgorithmImports`, `QCAlgorithm`, or LEAN runtime imports without an
  approved validation plan.
- real market data fetching or downloads.
- `requests`, `yfinance`, Alpaca, CCXT, or another vendor download path.
- credentials, tokens, account IDs, local secrets, or environment variables.
- live trading, paper trading, brokerage connection, or real order routing.
- `SetHoldings`, order calls, liquidation calls, brokerage models, or fill
  semantics before the project explicitly scopes simulated order handling.
- changing source, research, report, backtester, metrics, CSV loader,
  diagnostics, normalization, combination, or alpha modules outside a stated
  reviewed scope.
- weakening tests or removing guardrail checks.
- interpreting simulated output as investment evidence.
- claiming profitability, robustness, or trading readiness.

## 6. Next Review Gate

After this decision is reviewed and merged, continue with a documentation-only
LEAN signal-only draft design. That design should either approve a tightly
scoped future signal-only code PR or identify the exact blocker that prevents
code implementation.
