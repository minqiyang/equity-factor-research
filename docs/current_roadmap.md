# Current Roadmap

Updated: 2026-07-11 for the holding-episode metric implementation stage.

Baseline stage: holding-episode metric implementation.

This is the canonical roadmap. Older checkpoint, gap-refresh, and conformance
documents are historical evidence, not active task queues.

## Objective

Maintain a deterministic, auditable equity-factor research toolkit. Preserve
strict timing, data, accounting, and private-output boundaries. Do not present
synthetic or private diagnostics as investment, profitability, or trading
evidence.

## Implemented Baseline

| Area | Current contract |
| --- | --- |
| Features | Momentum, reversal, volatility, liquidity, Alpha #009/#012, normalization, combination, and reusable panel operators. |
| Diagnostics | Correlation, IC, Rank IC, quantile spread, coverage, and train/validation/test splits. |
| Data | Strict local wide, long, benchmark, and OHLCV CSV validation; no downloader. |
| Portfolio | Drift-aware long-only simulation with explicit signal lag, signed trades, turnover, fixed costs, fixed slippage, optional position caps, benchmark accounting, holdings-state metrics, tracking error, and completed holding-episode metrics. |
| Volume slippage | Explicit drift-aware trade weights, lagged liquidity diagnostics, and reviewed precomputed-impact application with return-basis metadata. |
| Reporting | Deterministic experiment logs and registry. Plotting remains a placeholder. |
| Private diagnostics | Local-only EODHD validation and neutral diagnostics runners; raw inputs and outputs stay outside the repository. |
| LEAN | Non-executing metadata and signal scaffold only. No brokerage, orders, paper trading, or live trading. |

The executable baseline is protected by the full test suite and CI. Historical
claims must be checked against source and tests before reuse.

## Open Gaps

1. Real-data interpretation is blocked by point-in-time universe,
   survivorship, adjustment, benchmark, split, cost, and interpretation policy.
2. Broader portfolio risk constraints and exposure controls are not
   implemented; only the optional long-only position cap is available.
3. Reporting plots are not implemented.
4. Volume-aware impact is a deterministic research estimate, not a calibrated
   fill or market-impact model.
5. LEAN execution remains out of scope.

## Delivery Sequence

| Stage | Status | Scope | Completion gate |
| --- | --- | --- | --- |
| Documentation and release baseline | Complete | Canonical roadmap, current handoff, concise README, code-accurate workflow SVG, package metadata, and CI build gates. | Public claims match code; tests, lint, compilation, package build, and wheel smoke pass. |
| Public interface cleanup | Controlled follow-up | Remove duplicated presentation helpers only when output fixtures prove byte-stable; keep research logic unchanged. | Focused and full tests, generated-output stability, CI, and current-head review. |
| Risk/evaluation design | Complete | Holdings-state formulas, timing, missing-data behavior, deferred metrics, and staged tests are defined in `docs/risk_evaluation_metrics_design.md`. | Design PR accepted before code. |
| Holdings-state metrics | Complete | Average active-date holding count and normalized average/maximum HHI are integrated into simulated backtest metrics and generated synthetic evidence. | Focused and full tests, generated-output review, CI, and current-head review. |
| Tracking error design | Complete | Daily close-to-close benchmark alignment, first-row treatment, missing-data behavior, net-versus-gross return semantics, annualization, errors, metadata, and focused test requirements are defined in `docs/risk_evaluation_metrics_design.md`. | Design contract accepted before implementation. |
| Tracking error implementation | Complete | Annualized population volatility of exact-date aligned daily net strategy returns versus cost-free benchmark returns is integrated with audit metadata and deterministic synthetic evidence. | Focused tests, full tests, generated-output review, CI, and current-head review. |
| Constraint design | Complete | Define an optional long-only position cap after selection and before trade calculation, with clipping, no renormalization, residual cash, validation, audit fields, and accounting interactions. | Design contract accepted before implementation. |
| Position-cap implementation | Complete | Optional long-only target weights are clipped after selection and before trade calculation without renormalization; residual exposure remains cash. | Focused tests, full tests, generated-output review if affected, CI, and current-head review. |
| Episode metric design | Complete | Define continuous positive-weight episodes, signed-trade evidence, deployed-weight return basis, applied-cost allocation, terminal-open handling, audit fields, and tests. | Design contract accepted before implementation. |
| Episode metric implementation | Complete | Signed trades support completed-episode hit rate and average holding-period return with reconciled applied costs and explicit terminal-open counts. | Focused tests, full tests, generated-output review, CI, and current-head review. |
| Full repository conformance audit | Next | Read-only audit of roadmap, handoff, README, code, tests, generated evidence, CI, privacy boundaries, and LEAN scope. | Publish findings separately; remediate every actionable P1/P2 before final verification. |
| Real-data methodology | Blocked | Proceed only after an explicit, complete local-data methodology package is accepted. | Provenance, point-in-time universe, adjustment, benchmark, split, cost, and interpretation gates all pass. |
| LEAN | Blocked | Remain at non-executing scaffold unless separately authorized and reviewed. | No implicit expansion into orders or brokerage behavior. |

## Change Policy

- Use one small PR at a time.
- Treat source and deterministic tests as implementation evidence.
- Update this file when a merge changes roadmap status.
- Keep historical checkpoint documents immutable except for a short successor
  pointer.
- Require CI and current-head Codex review before merge.
