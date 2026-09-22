# Review Directive: Milestone 4.6 Remediation Re-Review (M46-R1)

## Identity and Scope

- **Candidate Commit**: `be177ce57036e48bccc5425950995f044bddf794`
- **Base Commit**: `b60e109c6959e059dea6c19c3573dd5e861a2ac2`
- **Branch**: `feat/m4-6-risk-attribution`
- **Clean Review Worktree**: `/private/tmp/efr-m4-6-rereview-clean-be177ce`
- **Reviewer Seat**: Single independent seat under **GPT-6 Astra High Fast** (`-m gpt-6-astra -c model_reasoning_effort="high"`, with `service_tier = "fast"` actively confirmed).
- **Target Report**: `coord/reports/m4_6_risk_attribution_review.md`

## Verification Requirements

1. **Verify Resolution of M46-R1 (P2 MATERIAL)**:
   - Inspect `src/backtest/risk_attribution.py:200-210` in `decompose_active_risk`.
   - Confirm tolerance alignment: accepts numerical cancellation down to `-1e-14` matching the covariance PSD check (`variance >= -1e-14 and factor_variance >= -1e-14`).
   - Confirm non-material cancellation clamping: `factor_variance = max(factor_variance, 0.0)` and `variance = max(variance, 0.0)`.
   - Confirm `RiskAttributionError("risk_numerical", ...)` is preserved if variances are materially negative ($< -10^{-14}$) or non-finite.
   - Run the reviewer's regression test `test_valid_rank_one_covariance_with_hedged_factor_exposure` in `tests/test_risk_attribution.py` and verify it passes with active variance $\approx 6.25 \times 10^{-7}$.

2. **Ablation & QA Verification**:
   - Verify negative ablations in `coord/reports/m4_6_evidence/ablate.py` (all 55 negative ablations must fail when injected).
   - Verify disjoint test lanes:
     - Core lane: 4,215+ passed, 2 inherited platform skips.
     - Diagnostics lane: 125 passed.
     - Disjoint total: 4,340 passed.
   - Verify 124-book baseline byte equality via `coord/reports/m4_6_evidence/capture_baseline.py` (legacy SHA-256 `5a885b96...` and all-fields SHA-256 `878cfc03...`).
   - Verify demo reproduction (`research/risk_attribution_demo.py`) with attempt logs and markdown report.
   - Verify `ruff check .` and `python -m compileall -q src tests research lean`.

3. **Deliverable**:
   - Write authoritative re-review report to `coord/reports/m4_6_risk_attribution_review.md`.
   - If M46-R1 is resolved with zero new material findings, record:
     `Verdict: PASS (MATERIAL: 0)`.
