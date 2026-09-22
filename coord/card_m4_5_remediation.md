# Directive Card: Milestone 4.5 Remediation (M45-R1)

## Context and Authority

- Independent review of candidate `fa63cfae90b6543e94b861df2277ecdfab9b9460` returned:
  **`CHANGES REQUIRED — MATERIAL: 1 (P1)`**.
- Full review report is available at:
  - `coord/reports/m4_5_market_impact_capacity_review.md`
- Owner directions authorize immediate autonomous remediation and re-review under single-seat **GPT-6 Astra High Fast**.

## Finding Details: M45-R1 (P1 MATERIAL)

- **Affected Code**: `src/backtest/market_impact.py:418-443` in `execute_impact_step`.
- **Root Cause**:
  In pandas 3.0.6, when all requested trades are buys (all-True boolean indexer), `buy_values = executed.loc[buys].to_numpy(dtype=float)` does not create a memory copy and shares memory with `executed`.
  When `scale < 1.0`, line 438 performs `executed.loc[buys] *= scale`, mutating `buy_values` in place.
  Line 439 then executes `buy_spend, buy_commission, buy_slippage = buy_outlay(scale)`, which calls `buy_values * scale` on the already-scaled array, effectively applying `scale` twice (`scale**2`) to commissions, slippage, and spend.
  Closing cash and closing equity become mismatched with executed positions.
- **Reviewer Repro**:
  See section `M45-R1` in `coord/reports/m4_5_market_impact_capacity_review.md`. Reviewer verified that copying `buy_values = executed.loc[buys].to_numpy(dtype=float, copy=True)` (or capturing an immutable snapshot) resolves the issue, alongside adding post-trade cash-plus-position reconciliation.

## Required Remediation Actions

1. **Memory Isolation & Outlay Calculation**:
   - Ensure `buy_values` is an explicit copy (`to_numpy(dtype=float, copy=True)` or compute outlay before modifying `executed`).
   - Add explicit post-trade cash-plus-position reconciliation check in `execute_impact_step`:
     Verify that `(cash_after + post_trade_position_value)` reconciles with `(equity_before - commission - slippage)` within numerical tolerance (`<= 1e-6`), raising `MarketImpactValidationError("impact_accounting_invalid", ...)` if violated.

2. **Comprehensive Deterministic Regressions**:
   - Add tests covering all-buy portfolios requiring funding (`scale < 1`):
     - Direct-step tests across all three policies (`raise`, `throttle`, `penalize`).
     - Fixed slippage, square-root slippage, and commission-only variations.
     - Public `run_long_only_backtest` tests with single-security and multi-security all-buy orders, verifying exact closing cash, closing equity, and subsequent accounting row stability.
   - Integrate reviewer's regression cases into `tests/test_market_impact.py` or `tests/test_market_impact_engines.py`.

3. **Ablation & QA Verification**:
   - Update `coord/reports/m4_5_evidence/ablate.py` to include negative ablation for M45-R1 (verifying that omitting the copy or reconciliation guard fails).
   - Re-verify exact 124-book baseline byte equality (`capture_baseline.py`).
   - Re-run full core lane and diagnostics lane.
   - Run `ruff check .` and `python -m compileall -q src tests research lean`.
   - Ensure capacity demo generates cleanly.

4. **Deliverables**:
   - Commit the remediation on branch `feat/m4-5-market-impact-capacity`.
   - Update implementation report `coord/reports/m4_5_market_impact_capacity_impl.md` with remediation details and commit SHA.
   - Hand off clean candidate commit to coordinator for re-review.
