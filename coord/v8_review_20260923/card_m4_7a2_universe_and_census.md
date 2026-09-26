# Task Card: M4.7a-2 PIT Universe Build, Terminal Evidence, Support Wiring, and Coverage Census

- **Task/attempt**: `m4_7a2-universe-and-census-a1`
- **Objective**: Implement Stage `a-2` of Milestone 4.7 Binding Implementation Plan Revision 11 (`coord/plans/m4_7_binding_plan.md` §7.2, stage `a-2`):
  1. `research/m4_7_holdout_seal.py`: Seal script wrapper and confirmation tooling.
  2. `research/m4_7_universe_build.py`: Point-in-time universe construction (Rules E1–E6, corporate action attribution, split-basis and in-span step checks, cumulative drift check, panel and inventory emission with hashes, `identity/interval_results.csv`, `read_bar_dates`).
  3. `research/m4_7_terminal_evidence.py`: Terminal evidence curation and validation tooling (`template`, `validate`, `project`, valuation row `V`, corporate-action evidence check).
  4. Snapshot wiring in `research/m4_7_common_support.py`: Wire a-0 pure support core to snapshot panel files, masks through `resolve_pit_universe_mask`, and emit `census/exclusion_set.json`, `census/gap_windows.json`, `census/segments.json`.
  5. `research/m4_7_coverage_census.py`: Coverage census calculations, readiness checks (R-CENSUS-1..10), volume-basis diagnostic, power projection (§5.5), and seal confirmation.
  6. Synthetic snapshot fixtures under `tests/fixtures/m4_7/` in the Appendix A layout flowing end-to-end.
  7. Dedicated test suites: `tests/test_m4_7_universe_build.py` (T-UNI-1..17), `tests/test_m4_7_terminal_evidence.py` (T-TERM-1..11), `tests/test_m4_7_coverage_census.py` (T-CENSUS-1..10), and seal tests in `tests/test_m4_7_holdout_seal.py` (T-SEAL-2..5).
- **Core Directives (Owner Priorities)**:
  - **No Over-Engineering**: Prefer lightweight pure functions, standard Pandas DataFrames, NumPy arrays, and simple Dataclasses. No speculative abstraction layers or recursive state machines.
  - **Pragmatic Data Engineering**: Follow Plan §1.5 and Appendix A synthetic golden fixtures without blocking on edge-case vendor lineage.
  - **Decoupled Architecture**: All modules developed and tested against deterministic synthetic snapshot fixtures without network calls.
- **Route**: `GENERAL_EXEC` (Coordination Standard V8.6).
- **Binding**: `OPUS_LATEST` (`claude-opus-5-5`), Claude Code, effort: `medium`, normal service tier, `--dangerously-skip-permissions`.
- **Lane**: CRITICAL. **Structural**: true (`ARCHITECTURE`, `SCHEMA_PROTOCOL_CONTRACT`, `SECURITY_AUTHORITY`).
- **Ablation applicability**: Major implementation candidate; requires ABLATION pass before final merge.
- **Base commit**: `76a0e43` (`main` after PR #264 and PR #262).
- **Candidate branch**: `claude/m4_7a2-universe-and-census`.
- **Working root**: `/private/tmp/efr-m47a2-universe-20260925`.
- **Operative Plan Reference**: `coord/plans/m4_7_binding_plan.md` (Revision 11, SHA-256 `6541db93336e9181ebf3ad2f066b7b17f4550a17565036c2db5a5d82872a6407` §1.5, §1.6, §2, §3, §4.1, §4.2, §5.1, §5.2, §5.3, §5.4, §5.5, §7.2 a-2, Appendices A, B, D, E).
- **Report destination**: `/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/coord/reports/m4_7a2_universe_and_census_impl.md`.

---

## Deliverables & Acceptance Criteria (§7.2, stage a-2)

1. **Seal Script (`research/m4_7_holdout_seal.py`)**:
   - Calls `src/data/holdout_partition.py::write_prospective_seal` with verification.
   - Embeds prospective SHA-256 and writes confirmation block upon census.
2. **Universe Builder (`research/m4_7_universe_build.py`)**:
   - Implements Rules E1–E6 with ISIN continuity and interval-level resolution before code-level rules (C60).
   - Calendar-row boundary rule (`m_in = row(start) + 1`, `m_out = row(end) + 1`).
   - Exclusive exit classes (`delisting_candidate`, `disappearance_outside_membership`, `index_removal_still_trading`).
   - Episode attribution of split and dividend rows; split-basis check at last bar; in-span step check with own-basis reference prices (C73, C74, C81); cumulative drift check under prior-close formula (C82, S3).
   - Generates `identity/interval_results.csv`, panel Parquet files under `panel/discovery/`, inventory Parquet with `discovery_inputs_sha256` and hashes.
   - `read_bar_dates` reads dates only through `dates/<CODE>.US.parquet` with hash verification.
3. **Terminal Evidence Tooling (`research/m4_7_terminal_evidence.py`)**:
   - `template`: Generates curation template for delisting candidates.
   - `validate`: Strict validation of delisting evidence (dates, consideration types, corporate action evidence).
   - `project`: Maps terminal evidence to engine-compatible settlement events with accepted consideration lags.
4. **Common Support Wiring (`research/m4_7_common_support.py`)**:
   - Wires pure evaluation core delivered in a-0 to snapshot panels: builds bar-presence matrix, evaluates masks via `resolve_pit_universe_mask`, computes peeled segments and gap windows, emits `census/exclusion_set.json`, `census/gap_windows.json`, and `census/segments.json`.
5. **Coverage Census (`research/m4_7_coverage_census.py`)**:
   - Evaluates census metrics: `eligible_unpriced_member_days`, warm-up estimates, readiness R-CENSUS-1..10, volume-basis diagnostic (VP-1), power projection (§5.5), and writes `reports/m4_7_coverage_census.json` and markdown report.
   - Writes seal confirmation block with acyclic hashes (`seal_prospective_sha256`, `seal_confirmed_sha256`, `census_json_sha256`).
6. **Deterministic Verification**:
   - All tests in `tests/test_m4_7_universe_build.py`, `tests/test_m4_7_terminal_evidence.py`, `tests/test_m4_7_common_support.py`, `tests/test_m4_7_coverage_census.py`, and `tests/test_m4_7_holdout_seal.py` (T-SEAL-2..5 including read recorder and perturbation oracle) pass.
   - `tests/test_governance_constitution.py` passes.
   - `ruff check . --exclude .venv` passes cleanly.
   - Full test suite passes without regressions.
