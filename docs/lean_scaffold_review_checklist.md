# LEAN Scaffold Review Checklist

Date: 2026-06-04

This checklist reviews the merged non-executing LEAN scaffold before any
future stage turns it into a runnable QuantConnect/LEAN draft.

It is documentation only. It does not add a runnable LEAN project, `config.json`,
local or cloud LEAN run, real data path, data download, credential path,
brokerage connection, order-execution path, live trading, paper trading, or
profitability claim.

## 1. Purpose

The checklist answers one narrow question:

```text
Is the current LEAN scaffold sufficiently bounded and auditable to be expanded
in a later PR without changing project guardrails?
```

It does not evaluate strategy quality, factor performance, or trading
readiness.

## 2. Scope Under Review

The current scaffold consists of:

| File | Review role |
| --- | --- |
| `lean/README.md` | Human-facing scaffold scope, caveats, validation commands, and stop conditions. |
| `lean/smoke_test_algorithm.py` | Metadata-only scaffold constants and review metadata. |
| `tests/test_lean_smoke_test_scope.py` | Static guardrail and structure tests. |

The checklist does not approve changes to `src/`, research scripts, generated
reports, backtester, metrics, CSV loader, diagnostics, normalization,
combination, alpha modules, or experiment outputs.

## 3. Required Review Questions

| Area | Question | Required evidence |
| --- | --- | --- |
| Non-execution | Does the scaffold avoid runnable LEAN inheritance, runtime imports, and local/cloud run configuration? | No `QCAlgorithm`, no `AlgorithmImports`, no `config.json`, and `IS_EXECUTABLE_LEAN_ALGORITHM` remains false. |
| Data access | Does the scaffold avoid real data fetching, downloads, vendor APIs, and request libraries? | No `requests`, `yfinance`, Alpaca, CCXT, or download helper imports. |
| Credentials | Does the scaffold avoid secrets, account IDs, environment variables, and token reads? | No `os.environ`, `getenv`, API key, access token, secret key, account ID, or credential helper. |
| Trading mode | Does the scaffold avoid live trading, paper trading, brokerage setup, and order-routing semantics? | No live/paper mode, no brokerage model, no `SetHoldings`, order call, or liquidation call. |
| Timing contract | Are algorithm time, latest completed data date, feature date, simulated order date, and evaluation date still explicit? | The timing field list is present and reviewed before any runnable translation. |
| Diagnostics | Are eligibility, skipped-symbol, selected-symbol, target-weight, benchmark, cost, slippage, and caveat diagnostics still explicit? | The diagnostic field list is present and reviewed before any runnable translation. |
| Caveats | Are synthetic/simulated and non-profitability caveats visible to a human reviewer? | README and PR description use explicit caveat language. |
| File boundary | Are changes limited to the planned LEAN scaffold surface and related logs? | Branch diff contains only the approved files for the stage. |

## 4. Required Static Checks

Before any future runnable LEAN draft PR, run:

```powershell
python -m pytest -q tests/test_lean_smoke_test_scope.py
python -m pytest -q
python -m compileall src tests research
python -m compileall lean
git diff --check
```

The future PR should also run a guardrail grep over changed files and interpret
matches. Acceptable matches are prohibitions, caveats, log entries, or tests.
Unacceptable matches are active data fetching, credential reads, live or paper
mode setup, brokerage integration, order execution, or unsupported performance
claims.

## 5. Safe Expansion Criteria

A later PR may move from metadata-only scaffold toward a runnable draft only if
all of these are true:

- no prior PR merge gate is open.
- latest `main` is synced and clean.
- baseline tests and compile checks pass.
- static scaffold tests pass.
- the intended future file list is stated before editing.
- the stage does not need QuantConnect account access, local LEAN installation,
  cloud execution, credentials, or real data.
- the draft remains simulated research only.
- the PR can be reviewed without interpreting strategy performance.

If any item is false, keep the next stage documentation-only or stop with a
blocker report.

## 6. Stop Conditions

Stop immediately if the next stage requires:

- real market data fetching or downloads.
- `requests`, `yfinance`, Alpaca, CCXT, or another vendor download path.
- credentials, tokens, account IDs, local secrets, or environment variables.
- live trading, paper trading, brokerage connection, or real order routing.
- a local or cloud LEAN run before the runnable draft is reviewed.
- changing source, research, report, backtester, metrics, CSV loader,
  diagnostics, normalization, combination, or alpha modules outside a stated
  reviewed scope.
- weakening tests or removing guardrail checks.
- interpreting simulated output as investment evidence.
- claiming profitability, robustness, or trading readiness.

## 7. Recommended Next Stage After Merge

After this checklist is reviewed and merged, the next safe stage is a narrow
implementation-readiness decision:

```text
Decide whether to add a runnable LEAN draft or keep another planning stage.
```

If the runnable draft can be created without account access, credentials, data
downloads, live or paper trading, brokerage integration, order execution, or
performance interpretation, it may be planned as a small PR. Otherwise, stop
and document the blocker before implementation.
