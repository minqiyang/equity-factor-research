# Review Directive: Milestone 4.5 Remediation Re-Review (M45-R1)

## Identity and Scope

- **Candidate Commit**: `34af01417b6507725e4210e7d14de01d38b1e99a`
- **Base Commit**: `fe851ba0a69be1416db265bee4375433ab45d52d`
- **Branch**: `feat/m4-5-market-impact-capacity`
- **Clean Review Worktree**: `/private/tmp/efr-m4-5-rereview-clean-34af014`
- **Reviewer Seat**: Single independent seat running under **GPT-6 Astra High Fast** (`-m gpt-6-astra -c model_reasoning_effort="high"`, fast mode active).
- **Target Report**: `coord/reports/m4_5_market_impact_capacity_review.md`

## Verification Requirements

1. **Verify Resolution of M45-R1 (P1 MATERIAL)**:
   - Inspect `src/backtest/market_impact.py:418-445` and `:479-490`.
   - Confirm `buy_values = executed.loc[buys].to_numpy(dtype=float, copy=True)` prevents buffer aliasing under pandas 3.0.6 all-True selections.
   - Confirm post-trade balance guard enforces `abs((cash_after + positions_after.sum()) - equity_after) <= 1e-6`, raising `MarketImpactValidationError("impact_accounting_invalid", ...)` if violated.
   - Run the 8 reviewer regression cases (`test_review_cash_alias.py`) against this candidate and verify all 8 pass.

2. **Ablation & QA Verification**:
   - Verify negative ablations in `coord/reports/m4_5_evidence/ablate.py` (all 17 negative ablations must fail when injected).
   - Verify disjoint test lanes:
     - Core lane: 4,136+ passed, 2 inherited skips.
     - Diagnostics lane: 125 passed.
     - Disjoint total: 4,261 passed.
   - Verify 124-book baseline byte equality via `coord/reports/m4_5_evidence/capture_baseline.py` (SHA-256 `5a885b96e7379a83658047d4720d701f504f92838ffae10a76fa267580b61ed4`).
   - Verify capacity demo replay and attempt logs.
   - Verify `ruff check .` and `python -m compileall -q src tests research lean`.

3. **Deliverable**:
   - Write authoritative review report to `coord/reports/m4_5_market_impact_capacity_review.md`.
   - If M45-R1 is resolved with zero new material issues, record verdict:
     `Verdict: PASS (MATERIAL: 0)`.
