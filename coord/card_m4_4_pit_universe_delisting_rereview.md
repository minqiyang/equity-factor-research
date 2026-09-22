# Milestone 4.4 Independent Code Re-Review Directive

Date: 2026-09-21.
Base: `37437df765155b902566dc41e60e0d314355ec3d` (merged M4.3).
Remediated Candidate: `18f3741f5fa7053fff2132adaff4041a57641a07` on `feat/m4-4-pit-universe-delisting`.
Parent Candidate: `a2d6f3fe97be945a90e2c67f1bd67ab9dc16a38d`.
Initial Review Report: `coord/reports/m4_4_pit_universe_delisting_review.md` (recorded findings M44-R1 and M44-R2).
Implementation Report: `coord/reports/m4_4_pit_universe_delisting_impl.md`.
Review Worktree: `/private/tmp/efr-m4-4-rereview` (clean detached HEAD).
Reviewer Seat: Single independent session: **GPT-6 Astra High Fast** (`-m gpt-6-astra -c model_reasoning_effort="high"` under global `service_tier = "fast"`).
Outcome: Updated or appended review report in `coord/reports/m4_4_pit_universe_delisting_review.md`.

## Governing Rules and Invariants

Follow repository rules from `AGENTS.md`:
1. Direct affirmative construction. Assertive tone.
2. Read-only review: Do not modify candidate implementation files or producer worktree. Author only the review report.
3. Priority: Research-validity and accounting correctness.

## Targeted Re-Review Verification Tasks

1. **Verify M44-R1 Closure (Strict Permanent-ID Validation at PIT CSV Boundary)**:
   - Inspect `src/data/constituent_table.py:load_constituent_intervals_csv`.
   - Verify raw string exactness check on `permanent_id` and `symbol` prior to whitespace stripping or normalization.
   - Verify that strings with leading/trailing whitespace (e.g. `' ID_A'` or `'ID_A '`) or blank strings raise `ValueError("PIT-005: ...")`.
   - Verify that leading zeros, custom column names, and legacy CSV loads behave as specified.
   - Re-run reviewer probe tests that previously failed: confirm they now correctly raise the expected `ValueError`.

2. **Verify M44-R2 Closure (Retention of Zero-Holding Anchor Terminal Evidence)**:
   - Inspect `src/backtest/portfolio.py` and `src/backtest/long_short.py`.
   - Verify that terminal events effective exactly at `evaluation_start` (with valid full-source reference date) are recorded in `terminal_event_log` with zero incoming weight and zero cashflow.
   - Verify that events strictly prior to `evaluation_start` remain excluded from bounded event logs.
   - Re-run reviewer probe tests that previously failed: confirm `assert len(book.terminal_event_log) == 1`.

3. **Independent Test Execution**:
   - Run focused test suites:
     `.venv/bin/python -m pytest -q tests/test_pit_universe_delisting.py tests/test_pit_universe_delisting_demo.py`
   - Run core suite:
     `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 BLIS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 .venv/bin/python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 tests --ignore=tests/test_multifactor_diagnostic_mvp.py --ignore=tests/test_m3_10_hardening.py`
   - Run diagnostics suite:
     `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 BLIS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 .venv/bin/python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 tests/test_multifactor_diagnostic_mvp.py tests/test_m3_10_hardening.py`
   - Run Ruff: `.venv/bin/python -m ruff check .`
   - Run compileall: `.venv/bin/python -m compileall -q src tests research lean`

4. **Deliver Report**:
   - Deliver clear verdict: **PASS (MATERIAL: 0)** upon verifying that M44-R1 and M44-R2 are fully closed and all tests pass with zero new material defects.
   - Update `coord/reports/m4_4_pit_universe_delisting_review.md`.
