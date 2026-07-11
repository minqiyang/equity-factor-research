# Current Handoff

Updated: 2026-07-10 for the risk/evaluation design stage.

Baseline stage: risk/evaluation design.

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

Implement the approved holdings-state metrics in
`docs/risk_evaluation_metrics_design.md`. Do not add tracking error, hit rate,
holding-period return, or portfolio constraints in the same PR.

## Do Not Infer

- Private diagnostics are not accepted real-data interpretation.
- Synthetic backtests are not profitability or investment evidence.
- Volume-aware slippage is not a calibrated execution model.
- Placeholder plotting and risk modules are not implemented capabilities.
- LEAN files do not support orders, brokerage, paper trading, or live trading.

## Next Safe Actions

1. Implement and test average holding count plus normalized average/maximum
   concentration HHI.
2. Design tracking error as a separate benchmark-alignment stage.
3. Consider shared presentation helpers only with byte-stable generated-output
   tests.
4. Pause real-data interpretation until the methodology gates in
   `docs/current_roadmap.md` are accepted.
