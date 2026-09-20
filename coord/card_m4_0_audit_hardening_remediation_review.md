# Review Task Card: Milestone 4.0 Audit Hardening Remediation Round 2 Candidate `c7f9d94`

## Review Metadata
- Reviewer: `GROK_REVIEW` (Grok Build / Grok 4.6, CRITICAL lane, `GROK_LATEST` / `XHIGH`)
- Candidate: `c7f9d94c4a311b4c2400e5d05c33d4347f691169`
- Prior Candidates: `97db0ddc2990364e34ffe0a6f51c381e585e1019` (FAIL: MATERIAL: 2), `93f5fdb3ebced3f6457c9093c39dbd1035f6efbc`
- Baseline: `cf55af944efd3112e581823a4fd9ee0d726ed2d3` (`main`)
- Worktree: `/private/tmp/efr-m4-hardening-review-93f5fdb` (detached HEAD at `c7f9d94`)
- Deliverable: `/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/coord/reports/m4_0_audit_hardening_review.md`

## Round 2 Remediation Scope (Addressing Grok Findings)
1. **MAT-M40H-1 (Residual) — Fail Closed on Missing Split Evidence**:
   - `research/real_data_multifactor_diagnostic.py` (`build_adjusted_research_panels`): If `split_factor` is not provided in `field_panels`, verifies `(close / adjusted_close).pct_change().abs() <= 0.15`. If discontinuities (>15%) exist without split factor evidence, raises `DataIntegrityError` instead of failing open with `cum_split = 1.0`.
   - `src/data/parquet_loader.py` (`load_eod_cohort_panels`): Verifies `(close / adjusted_close).pct_change().abs() <= 0.15` when no split files exist. Raises `DataIntegrityError` on unverified discontinuities.
   - `src/data/parquet_loader.py` (`load_symbol_splits`): Removed bare `except Exception: pass`. Raises `DataIntegrityError` on SQLite errors and `FileNotFoundError` if a split file referenced in the ledger is missing.
   - `tests/test_real_data_multifactor_diagnostic.py`: Added `test_build_adjusted_research_panels_refuses_unverified_split` verifying the 4:1 split witness without `split_factor` raises `DataIntegrityError`.

2. **MAT-M40H-2 — Total-Return Basis for Backtest, Labels, and Benchmark**:
   - `research/real_data_multifactor_diagnostic.py`:
     - `benchmark = research_panels["adjusted_close"][config.benchmark_symbol]`: SPY benchmark is strictly driven by vendor `adjusted_close`.
     - `prices = panels["adjusted_close"]`: Portfolio backtest pricing and forward return labels are driven by `panels["adjusted_close"]` (total-return basis, including cash dividends and splits).
     - `panels["close"]` and `panels["volume"]`: Retained strictly as the split-only dollar-turnover pair (`split_close * volume`) and for price-volume alpha feature calculation.
   - `tests/test_real_data_multifactor_diagnostic.py`: Added `test_runner_uses_adjusted_close_for_prices_forward_returns_and_benchmark` verifying that when `close != adjusted_close`, `result["prices"]` and `result["accounting_benchmark"]` strictly track `adjusted_close`.

3. **ADV-M40H-1 — Identity Retention**:
   - `src/data/parquet_loader.py` (`_align_symbol_panels`): Attaches validated `permanent_id` series on cohort panels if present.

4. **ADV-M40H-2 — Readiness Gating and Typed Missingness**:
   - `research/real_data_multifactor_diagnostic.py` (`evaluate_diagnostic_readiness`): Excludes row 0 NA of `returns` from missingness check so complete datasets receive `diagnostic_ready_with_low_caveats`. Handles `pd.Series` (e.g. `permanent_id`) gracefully.
   - `tests/test_real_data_multifactor_diagnostic.py`: Verified in `test_evaluate_diagnostic_readiness_valid_and_invalid`.

5. **ADV-M40H-5 — Failure Logging Deduplication**:
   - `research/real_data_multifactor_diagnostic.py` (`_record_failure`): Deduplicates against records already appended with `status == "failed"` by `_run_recorded_trial`.
   - `tests/test_real_data_multifactor_diagnostic.py`: Added `test_record_failure_deduplication`.

6. **Regenerated Published Reports & Experiment Logs**:
   - `reports/real_data_multifactor_diagnostic.md` and `reports/experiment_logs/real_data_multifactor_diagnostic.json` / `.trials.jsonl` regenerated with the updated total-return backtest and benchmark engine.

## Instructions for Reviewer
1. Verify detached HEAD at `c7f9d94` in `/private/tmp/efr-m4-hardening-review-93f5fdb`.
2. Inspect diff `git diff 97db0dd..c7f9d94` (and `git diff cf55af9..c7f9d94`).
3. Run pytest: `PYTHONPATH=src:. .venv/bin/pytest tests/test_parquet_loader.py tests/test_real_data_multifactor_diagnostic.py` (69 tests).
4. Re-evaluate MAT-M40H-1, MAT-M40H-2, and ADV-M40H-1..5.
5. Overwrite `/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/coord/reports/m4_0_audit_hardening_review.md` with your updated formal review report and verdict.
