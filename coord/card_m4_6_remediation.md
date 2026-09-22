# Directive Card: Milestone 4.6 Remediation (M46-R1)

## Context and Authority

- Independent review of candidate `a79d4bd69ff82c354fc5f993bf8758ab6e826c83` returned:
  **`CHANGES REQUIRED — MATERIAL: 1 (P2)`**.
- Full review report is available at:
  - `coord/reports/m4_6_risk_attribution_review.md`
- Owner directions authorize immediate autonomous remediation and single-seat **GPT-6 Astra High Fast** re-review.

## Finding Details: M46-R1 (P2 MATERIAL)

- **Affected Code**: `src/backtest/risk_attribution.py:195-202` in `decompose_active_risk`.
- **Root Cause**:
  Line 191 validates positive semi-definiteness with numerical tolerance:
  `np.linalg.eigvalsh(covariance).min() >= -1e-14`.
  However, line 201 enforces strict non-negativity:
  `factor_variance >= 0 and variance >= 0` with zero tolerance.
  When portfolio factor exposure $\beta$ lies in the null space of a valid singular PSD covariance matrix, floating-point cancellation produces tiny negative roundoff (e.g. $-1.69 \times 10^{-22}$), aborting valid risk attribution calls.
- **Reviewer Repro**:
  See section `M46-R1` in `coord/reports/m4_6_risk_attribution_review.md` and `/private/tmp/efr-m46-review-evidence/test_singular_covariance.py`.

## Required Remediation Actions

1. **Numerical Roundoff Alignment in `decompose_active_risk`**:
   - Align tolerance with the PSD eigenvalue check:
     Require `factor_variance >= -1e-14` and `variance >= -1e-14` (raising `RiskAttributionError("risk_numerical", ...)` if materially negative).
   - Clamp non-material numerical roundoff:
     `factor_variance = max(factor_variance, 0.0)`
     `variance = max(variance, 0.0)`
   - Preserve signed Euler factor contributions `factor_terms` and exact reconciliation.

2. **Deterministic Regression Tests**:
   - Integrate the reviewer's exact test fixture (`test_singular_covariance.py`) into `tests/test_risk_attribution.py`.
   - Verify that hedged factor exposures in the null space of singular covariance matrices produce finite active variance and tracking error.

3. **QA & Baseline Verification**:
   - Verify all existing tests and new regression tests pass (disjoint core + diagnostics lanes: 4,332+ tests).
   - Verify all 52 negative ablations in `coord/reports/m4_6_evidence/ablate.py` continue to detect regressions.
   - Verify exact byte-for-byte baseline equality across 124 books (`capture_baseline.py`).
   - Run `ruff check .` and `python -m compileall -q src tests research lean`.

4. **Deliverables**:
   - Commit the remediation on branch `feat/m4-6-risk-attribution`.
   - Update `coord/reports/m4_6_risk_attribution_impl.md` with remediation details and new commit SHA.
   - Hand off candidate commit for independent re-review.
