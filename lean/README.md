# LEAN Smoke-Test Scaffold

This directory holds a minimal, non-executing scaffold for a future
QuantConnect/LEAN smoke test of the local equity factor research workflow.

It is not a runnable LEAN project yet. It does not include a `config.json`,
local LEAN runner setup, cloud-run instructions, credentials, or account IDs.
It explicitly has no real market data path. It also does not include real data
downloads, live trading, paper trading, brokerage integration, order
execution, or profitability claims.

## Purpose

The scaffold gives future review a small file boundary before any executable
LEAN backtest is added. It records the timing contract, diagnostic fields, and
guardrails expected by the existing LEAN planning documents.

The future smoke test should remain focused on workflow shape:

- daily US equity simulated research context.
- one simple 12-1 momentum signal path.
- explicit benchmark, cash buffer, fee, and slippage assumptions.
- completed-bar timing before simulated portfolio formation.
- eligibility, skipped-symbol, selected-symbol, target-weight, and caveat
  diagnostics.

The scaffold does not evaluate whether any factor is useful on real market
data.

## Current Files

- `smoke_test_algorithm.py` contains metadata and constants for review only.
- `../tests/test_lean_smoke_test_scope.py` validates the scaffold statically.

## Local Validation

Use repository-level validation from the project root:

```powershell
python -m pytest -q tests/test_lean_smoke_test_scope.py
python -m pytest -q
python -m compileall src tests research
python -m compileall lean
git diff --check
```

These checks do not run LEAN and do not require external platform access.

## Explicit Guardrail Phrases

For static review, this scaffold is governed by these exact phrases:

- no real market data.
- no live trading.
- no brokerage.
- no profitability claims.
- do not run LEAN.

## Stop Conditions

Stop before expanding this scaffold if the next step would require:

- real market data fetching or downloads.
- `requests`, `yfinance`, Alpaca, CCXT, or another vendor download path.
- credentials, tokens, account IDs, local secrets, or environment variables.
- live trading, paper trading, brokerage connection, or real order routing.
- a local or cloud LEAN run before the scaffold is reviewed.
- interpreting any simulated output as investment evidence.
- changing source, research, reports, backtester, metrics, CSV loader,
  diagnostics, normalization, combination, or alpha modules outside a reviewed
  scope.
