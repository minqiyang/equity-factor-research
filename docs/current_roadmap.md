# Current Roadmap

Updated: 2026-07-11 for the tracking-error implementation stage.

Baseline stage: tracking-error implementation.

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
| Portfolio | Drift-aware long-only simulation with explicit signal lag, turnover, fixed costs, fixed slippage, benchmark accounting, holdings-state metrics, and daily benchmark-relative tracking error. |
| Volume slippage | Explicit drift-aware trade weights, lagged liquidity diagnostics, and reviewed precomputed-impact application with return-basis metadata. |
| Reporting | Deterministic experiment logs and registry. Plotting remains a placeholder. |
| Private diagnostics | Local-only EODHD validation and neutral diagnostics runners; raw inputs and outputs stay outside the repository. |
| LEAN | Non-executing metadata and signal scaffold only. No brokerage, orders, paper trading, or live trading. |

The executable baseline is protected by the full test suite and CI. Historical
claims must be checked against source and tests before reuse.

## Open Gaps

1. Real-data interpretation is blocked by point-in-time universe,
   survivorship, adjustment, benchmark, split, cost, and interpretation policy.
2. Portfolio risk constraints and exposure controls are not implemented;
   `src/risk/constraints.py` is a placeholder.
3. Hit rate and average holding-period return remain unimplemented pending an
   episode-attribution model.
4. Reporting plots are not implemented.
5. Volume-aware impact is a deterministic research estimate, not a calibrated
   fill or market-impact model.
6. LEAN execution remains out of scope.

## Delivery Sequence

| Stage | Status | Scope | Completion gate |
| --- | --- | --- | --- |
| Documentation and release baseline | Complete | Canonical roadmap, current handoff, concise README, code-accurate workflow SVG, package metadata, and CI build gates. | Public claims match code; tests, lint, compilation, package build, and wheel smoke pass. |
| Public interface cleanup | Controlled follow-up | Remove duplicated presentation helpers only when output fixtures prove byte-stable; keep research logic unchanged. | Focused and full tests, generated-output stability, CI, and current-head review. |
| Risk/evaluation design | Complete | Holdings-state formulas, timing, missing-data behavior, deferred metrics, and staged tests are defined in `docs/risk_evaluation_metrics_design.md`. | Design PR accepted before code. |
| Holdings-state metrics | Complete | Average active-date holding count and normalized average/maximum HHI are integrated into simulated backtest metrics and generated synthetic evidence. | Focused and full tests, generated-output review, CI, and current-head review. |
| Tracking error design | Complete | Daily close-to-close benchmark alignment, first-row treatment, missing-data behavior, net-versus-gross return semantics, annualization, errors, metadata, and focused test requirements are defined in `docs/risk_evaluation_metrics_design.md`. | Design contract accepted before implementation. |
| Tracking error implementation | Complete | Annualized population volatility of exact-date aligned daily net strategy returns versus cost-free benchmark returns is integrated with audit metadata and deterministic synthetic evidence. | Focused tests, full tests, generated-output review, CI, and current-head review. |
| Constraint design | Next | Define ordering, reject/clip/renormalize behavior, cash treatment, infeasible-target handling, audit fields, errors, and liquidity/turnover interaction before code. | Design contract accepted before implementation. |
| Real-data methodology | Blocked | Proceed only after an explicit, complete local-data methodology package is accepted. | Provenance, point-in-time universe, adjustment, benchmark, split, cost, and interpretation gates all pass. |
| LEAN | Blocked | Remain at non-executing scaffold unless separately authorized and reviewed. | No implicit expansion into orders or brokerage behavior. |

## Change Policy

- Use one small PR at a time.
- Treat source and deterministic tests as implementation evidence.
- Update this file when a merge changes roadmap status.
- Keep historical checkpoint documents immutable except for a short successor
  pointer.
- Require CI and current-head Codex review before merge.
