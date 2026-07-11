# Current Handoff

Updated: 2026-07-11 for the position-cap constraint design stage.

Baseline stage: position-cap constraint design.

## Canonical State

- Active roadmap: `docs/current_roadmap.md`.
- Latest implementation baseline: drift-aware volume-slippage accounting,
  vectorized liquidity-universe caps, canonical public docs, and package build
  QA, with holdings-state metrics and the approved Stage 2 tracking-error
  contract implemented.
- Verified suite at the latest implementation stage: 562 tests.
- Delivery model: one small PR, CI, current-head Codex review, then normal
  merge.

## Completed

- Strict local CSV validation and committed fixture workflows.
- Factor construction, normalization, combination, diagnostics, and split
  helpers.
- Drift-aware simulated portfolio accounting and auditable cost fields.
- Explicit per-asset trade weights and return-basis-aware precomputed volume
  slippage.
- Private-output-only EODHD validation and neutral diagnostics guardrails.
- Non-executing LEAN scaffold guardrails.
- Liquidity-universe cap vectorization with stable tie semantics.
- Daily close-to-close tracking error with exact benchmark alignment, net
  strategy cost basis, cost-free benchmark returns, and audit metadata.

## Active Stage

Implement only the approved optional long-only position cap in
`src/risk/constraints.py` and integrate it after selection but before trade
calculation. Do not combine it with hit rate, holding-period return, plotting,
liquidity filtering, or strategy-selection behavior.

## Do Not Infer

- Private diagnostics are not accepted real-data interpretation.
- Synthetic backtests are not profitability or investment evidence.
- Volume-aware slippage is not a calibrated execution model.
- Placeholder plotting and risk modules are not implemented capabilities.
- LEAN files do not support orders, brokerage, paper trading, or live trading.

## Next Safe Actions

1. Implement the approved clip-without-renormalization position-cap contract,
   including residual non-interest-bearing cash and audit metadata.
2. Consider shared presentation helpers only with byte-stable generated-output
   tests.
3. Pause real-data interpretation until the methodology gates in
   `docs/current_roadmap.md` are accepted.
