# Review Card: Milestone 4.2 Purged & Embargoed Cross-Validation (CPCV)

## Objective
Independent formal code review of Milestone 4.2 Purged & Embargoed Cross-Validation (`PurgedGroupTimeSeriesSplit` and `combinatorial_purged_cross_validation_pbo`) and diagnostic integration.

## Scope & Target
- Candidate branch: `feat/m4-2-purged-embargoed-cpcv`
- Lane: STANDARD
- Reviewer route: `GROK_REVIEW` (`GROK_LATEST`, `XHIGH`)
- Output report: `coord/reports/m4_2_purged_embargoed_cpcv_review.md`

## Key Review Checkpoints
1. **Purging Logic Correctness**:
   - In `src/features/cross_validation.py` (`PurgedGroupTimeSeriesSplit`), verify that training observations whose forward-holding window $[s, s + H]$ intersects the test window $[T_{\text{start}}, T_{\text{end}}]$ are strictly purged:
     `purge_condition = (sample_starts <= test_end) & (sample_ends >= test_start)`.
   - Verify that samples before test start are purged if $s \in [T_{\text{start}} - H, T_{\text{start}} - 1]$.
2. **Embargo Logic Correctness**:
   - Verify that training observations immediately following a test block are excluded for the post-test embargo window $E$:
     `embargo_condition = (sample_starts > test_end) & (sample_starts <= min(n_samples - 1, test_end + embargo_periods))`.
3. **Scikit-Learn Compatibility**:
   - Verify `PurgedGroupTimeSeriesSplit` conforms to the `BaseCrossValidator` interface (`split`, `get_n_splits`) and works with standard scikit-learn functions like `cross_val_score`.
4. **PBO and CSCV Equivalence**:
   - In `combinatorial_purged_cross_validation_pbo`, verify that when $H=0$ and $E=0$, the results are mathematically identical to standard CSCV in `probability_of_backtest_overfitting`.
5. **Real-Data Diagnostic Integration**:
   - In `research/real_data_multifactor_diagnostic.py`, verify that `cpcv_summary` is computed using appropriate holding and embargo horizons (e.g. 21 bars forward return, 5 bars embargo) without corrupting existing unpurged CSCV baseline metrics.
6. **Edge Cases and Robustness**:
   - Verify handling of small datasets, empty splits, invalid input types, and boundary conditions.
