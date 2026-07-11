# Current Handoff

Updated: 2026-07-11 for the holding-episode metric implementation stage.

Baseline stage: holding-episode metric implementation.

## Canonical State

- Active roadmap: `docs/current_roadmap.md`.
- Latest implementation baseline: drift-aware volume-slippage accounting,
  vectorized liquidity-universe caps, canonical public docs, and package build
  QA, with holdings-state metrics and the approved Stage 2 tracking-error
  contract implemented.
- Verified suite at the latest implementation stage: 591 tests.
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
- Optional long-only position caps applied after selection and before trade
  calculation, with no renormalization and residual non-interest-bearing cash.
- Signed trade weights plus completed holding-episode hit rate and average
  holding-period return with reconciled applied costs and terminal-open counts.

## Active Stage

Run a fresh read-only full repository conformance audit from the merged episode
implementation baseline. Keep audit findings separate from remediation code.

## Do Not Infer

- Private diagnostics are not accepted real-data interpretation.
- Synthetic backtests are not profitability or investment evidence.
- Volume-aware slippage is not a calibrated execution model.
- Plotting and broader portfolio-risk controls are not implemented
  capabilities; the position cap is the only active constraint.
- LEAN files do not support orders, brokerage, paper trading, or live trading.

## Next Safe Actions

1. Audit roadmap, handoff, README, code, tests, generated evidence, metadata,
   private-output policy, CI, and LEAN boundaries against current main.
2. Consider shared presentation helpers only with byte-stable generated-output
   tests.
3. Pause real-data interpretation until the methodology gates in
   `docs/current_roadmap.md` are accepted.
