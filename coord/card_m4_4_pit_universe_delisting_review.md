# Milestone 4.4 Independent Code Review Directive

Date: 2026-09-21.
Base: `37437df765155b902566dc41e60e0d314355ec3d` (merged M4.3).
Candidate: `a2d6f3fe97be945a90e2c67f1bd67ab9dc16a38d` on `feat/m4-4-pit-universe-delisting`.
Producer worktree: `/private/tmp/efr-m4-4-pit-universe-delisting` (clean).
Review worktree: `/private/tmp/efr-m4-4-review` (clean detached HEAD).
Reviewer seat: Exactly ONE independent session: **GPT-6 Astra High Fast** (`-m gpt-6-astra -c model_reasoning_effort="high"` under global `service_tier = "fast"`).
Outcome report: `coord/reports/m4_4_pit_universe_delisting_review.md`.

## Governing Rules and Invariants

Follow repository rules from `AGENTS.md`:
1. Direct affirmative style. Definition by negation and strawmen are banned.
2. Read-only review: Do not modify candidate implementation files or producer worktree. Author only the review report `coord/reports/m4_4_pit_universe_delisting_review.md`.
3. Priority: Research-validity and accounting correctness over style. Any P1 requires concrete reproduction evidence.

## Review Scope and Verification Tasks

1. **PIT-005 (Identity and Causal Membership Mask)**:
   - Inspect `src/data/constituent_table.py` (`build_pit_membership_mask`, `load_constituent_intervals_csv`).
   - Verify strict permanent-ID column mapping; confirm ticker reuse without IDs is refused.
   - Verify conservative knowledge cutoff $a[j - \text{lag}]$; confirm future announcements never modify earlier decisions.
   - Verify raw effective-date timestamp precision validation (rejects intraday / timezone-bearing labels).

2. **PIT-006 (Terminal Cash Settlement Accounting)**:
   - Inspect `src/backtest/portfolio.py` and `src/backtest/long_short.py`.
   - Verify complete prior-observed-close-to-cash return ($r \ge -1$). Confirm event return replaces quote return once.
   - Verify signed terminal cash calculation: $E \cdot w \cdot (1 + r)$. Long proceeds credit cash, short liabilities debit cash.
   - Verify position is zeroed out before ordinary market trades.
   - Verify zero extra settlement fee; confirm ordinary turnover excludes terminal redemption.
   - Verify unexpected frozen-target collision refusal (`terminal_target_invalid`).
   - Verify cash balance equals $E \cdot (1 - \sum \text{signed closing holdings})$ and cash remains constant while surviving assets drift.

3. **Walking-Skeleton & Pipeline Integration**:
   - Inspect `research/pit_universe_delisting_demo.py` and generated reports.
   - Verify attempt logging in `reports/pit_universe_delisting_demo_attempts.jsonl`.
   - Confirm baseline numerical equality with M4.3 default diagnostic.

4. **Independent Test Execution**:
   - Run focused test suites:
     `.venv/bin/python -m pytest -q tests/test_pit_universe_delisting.py tests/test_pit_universe_delisting_demo.py`
   - Run core suite:
     `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 BLIS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 .venv/bin/python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 tests --ignore=tests/test_multifactor_diagnostic_mvp.py --ignore=tests/test_m3_10_hardening.py`
   - Run diagnostics suite:
     `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 BLIS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 .venv/bin/python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 tests/test_multifactor_diagnostic_mvp.py tests/test_m3_10_hardening.py`
   - Run Ruff: `.venv/bin/python -m ruff check .`
   - Run compileall: `.venv/bin/python -m compileall -q src tests research lean`

5. **Deliver Report**:
   - Deliver clear verdict: **PASS (MATERIAL: 0)** or document material findings with code references and reproduction.
   - Write report to `coord/reports/m4_4_pit_universe_delisting_review.md`.
