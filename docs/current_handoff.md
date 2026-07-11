# Current Handoff

Updated: 2026-07-10 after PR #142.

## Canonical State

- Active roadmap: `docs/current_roadmap.md`.
- Latest implementation baseline: drift-aware volume-slippage accounting,
  vectorized liquidity-universe caps, canonical public docs, and package build
  QA.
- Verified suite at the latest implementation stage: 536 tests.
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

## Active Stage

Design the missing risk and evaluation metrics before implementation. Keep the
stage documentation-only until formulas, timing, missing-data behavior, and
deterministic synthetic tests are reviewed.

## Do Not Infer

- Private diagnostics are not accepted real-data interpretation.
- Synthetic backtests are not profitability or investment evidence.
- Volume-aware slippage is not a calibrated execution model.
- Placeholder plotting and risk modules are not implemented capabilities.
- LEAN files do not support orders, brokerage, paper trading, or live trading.

## Next Safe Actions

1. Design risk/evaluation metrics before implementing them.
2. Consider shared presentation helpers only with byte-stable generated-output
   tests.
3. Pause real-data interpretation until the methodology gates in
   `docs/current_roadmap.md` are accepted.
