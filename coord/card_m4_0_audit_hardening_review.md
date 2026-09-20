# Review Card: Milestone 4.0 Audit Hardening (M4-01–M4-04, M09-R)

## Objective
Independent formal code review of commit `93f5fdb` resolving Milestone 4.0 audit findings M4-01 through M4-04 and M09-R.

## Scope & Target
- Candidate commit: `93f5fdb`
- Working root: `/private/tmp/efr-m4-hardening-review-93f5fdb` (detached worktree, clean)
- Output report: `/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/coord/reports/m4_0_audit_hardening_review.md`
- Lane: CRITICAL (Hardening / Remediation)
- Reviewer route: `GROK_REVIEW` (`GROK_LATEST`, `XHIGH`)

## Key Review Checkpoints
1. **M4-01 Volume Basis**:
   - Verify `build_adjusted_research_panels` in `research/real_data_multifactor_diagnostic.py` preserves vendor split-adjusted volume without dividing by `scale = adjusted_close / close`.
   - Verify `research_close * research_volume == adjusted_close * volume` preserves true historical split-adjusted dollar turnover.
2. **M4-02 Parquet Identity & Duplicate Mapping**:
   - Verify `_standardize_eod_frame` in `src/data/parquet_loader.py` inspects `permanent_id` and rejects multi-ID files.
   - Verify `load_eod_cohort_panels` detects and rejects duplicate file mappings across symbols.
3. **M4-03 OHLC Sanity & Dynamic Readiness**:
   - Verify `_validate_ohlc_relationships` in `src/data/parquet_loader.py` validates `high >= low`, `high >= open/close`, `low <= open/close`.
   - Verify `_parse_dates` rejects numeric date payloads.
   - Verify `evaluate_diagnostic_readiness` in `research/real_data_multifactor_diagnostic.py` dynamically evaluates panel/benchmark validity.
4. **M4-04 Privacy & Path Literals**:
   - Verify no machine-local path constants (`/Users/rhapsoul/...`) remain in `research/real_data_multifactor_diagnostic.py`.
   - Verify `redact_local_path` properly redacts snapshot/inventory directory tokens.
5. **M09-R Trial Identity & Failure Retention**:
   - Verify `alpha_ids` and `composite_ids` are included in `trial_context`.
   - Verify feature calculation and composite evaluation failures are recorded in `trials.jsonl`.
6. **Tests & Invariants**:
   - Verify all unit and hardening tests pass without regression.
