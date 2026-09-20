# Implementation Report: Milestone 4.0 Audit Hardening (M4-01–M4-04, M09-R)

**Candidate**: `codex/m4-0-audit-hardening`  
**Base**: `cf55af944efd3112e581823a4fd9ee0d726ed2d3` (`main`)  
**Lane**: CRITICAL (Hardening / Remediation)  
**Author**: Antigravity Coordinator (Gemini)  
**Date**: 2026-09-20  

---

## 1. Summary of Changes

This change set resolves all 5 material findings identified in the Milestone 4.0 independent audit (`coord/reports/antigravity_acceleration_and_drift_audit_m4_gpt6.md`):

1. **M4-01 (Volume & Dollar Turnover Basis in EODHD Data)**:
   - Vendor volume in EODHD data is documented as split-adjusted. In `research/real_data_multifactor_diagnostic.py`, `build_adjusted_research_panels` previously divided vendor volume by `adjusted_close / close`, resulting in a double-split adjustment and 4× inflation of pre-split dollar volume.
   - Fixed by keeping vendor volume unscaled: `research_volume = vendor_volume`. Since `research_close = adjusted_close`, `research_close * research_volume == adjusted_close * vendor_volume` preserves the exact true dollar turnover without split-ratio distortion.
   - Added unit test `test_build_adjusted_research_panels_keeps_dollar_volume_basis` verifying dollar volume stability across a 4:1 split.

2. **M4-02 (Parquet Loader Identity Integrity & Duplicate Alias Rejection)**:
   - In `src/data/parquet_loader.py`, `_standardize_eod_frame` now inspects `permanent_id` if present in the Parquet schema. If multiple distinct permanent IDs are detected in a single file, it raises `DataIntegrityError`, preventing artificial economic continuity across distinct securities (PIT-005).
   - In `load_eod_cohort_panels`, duplicate underlying file mappings across requested cohort symbols are now detected and rejected with `DataIntegrityError`.
   - Added tests `test_parquet_with_multiple_permanent_ids_is_refused`, `test_parquet_with_single_permanent_id_is_accepted`, and `test_duplicate_file_mapping_across_symbols_is_refused`.

3. **M4-03 (OHLC Bar Sanity Checks & Dynamic Readiness Evaluation)**:
   - In `src/data/parquet_loader.py`, added `_validate_ohlc_relationships` enforcing `high >= low`, `high >= open`, `high >= close`, `low <= open`, `low <= close`.
   - In `_parse_dates`, added strict rejection of numeric date payloads (e.g. integer YYYYMMDD).
   - In `research/real_data_multifactor_diagnostic.py`, replaced the static constant `READINESS_DECISION` with dynamic function `evaluate_diagnostic_readiness(panels, benchmark, config)` validating non-empty panels, aligned benchmark, finite values, positive prices, and non-negative volume.
   - Added tests `test_invalid_ohlc_relationships_are_refused`, `test_numeric_date_payload_is_refused`, and `test_evaluate_diagnostic_readiness_valid_and_invalid`.

4. **M4-04 (Purge Private Path Literals & Sensitive Directory Strings)**:
   - Removed `FALLBACK_DATA_DIR` and `FALLBACK_INVENTORY_PATH` constants from `research/real_data_multifactor_diagnostic.py`.
   - Replaced with dynamic resolution via environment variables (`EFR_EODHD_DATA_DIR`, `EFR_EODHD_INVENTORY_PATH`) or repo-external search without hardcoding user home paths (`/Users/rhapsoul/...`).
   - Updated `redact_local_path` to match on snapshot/inventory directory tokens.
   - Redacted machine-specific path strings in `coord/reports/m4_0_real_diag_review.md`.

5. **M09-R (Semantic Trial ID Distinctness & Pre-Registration Failure Retention)**:
   - Included `alpha_ids` and `composite_ids` in `trial_context` inside `research/real_data_multifactor_diagnostic.py`. Altering constituent alpha parents for composites now produces distinct trial IDs.
   - Wrapped feature calculation (`calculate_diagnostic_alpha`) and composite evaluation in try-except blocks: if an exception occurs, a failed trial event (`status="failed"`, `error_type`, `error`) is appended to `inventory` and persisted to `*.trials.jsonl` before re-raising.
   - Added unit tests `test_distinct_composite_trial_ids_when_parents_change` and `test_feature_calculation_failure_is_recorded_in_trials_jsonl`.

---

## 2. Verification Evidence

- `uv run ruff check .`: Passed (0 errors).
- `git diff --check`: Passed (0 whitespace/formatting issues).
- `PYTHONPATH=. uv run pytest -v tests/test_parquet_loader.py tests/test_real_data_multifactor_diagnostic.py`: 60 passed in 3.41s.
- `PYTHONPATH=. uv run pytest -q tests/test_m3_10_hardening.py`: 117 passed in 76.50s.
