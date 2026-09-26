# Task Card: M4.7a-1 Retrieval and Partition

- **Task/attempt**: `m4_7a1-retrieval-and-partition-a1`
- **Objective**: Implement the data retrieval and holdout partitioning modules of Milestone 4.7 Binding Implementation Plan Revision 11 (`coord/plans/m4_7_binding_plan.md` §7.2, stage `a-1`): `src/data/eodhd_retrieval.py` and `src/data/holdout_partition.py` with mockable transport, exception sanitization, token leakage prevention, and full deterministic test suite without live network calls.
- **Target audience**: Project Owner and Coordinator.
- **Route**: `GENERAL_EXEC` (Coordination Standard V8.5).
- **Binding**: `OPUS_LATEST` (`claude-opus-5-5`), Claude Code, effort: `medium`, normal service tier, `--dangerously-skip-permissions`.
- **Lane**: CRITICAL. **Structural**: true (`ARCHITECTURE`, `SCHEMA_PROTOCOL_CONTRACT`, `SECURITY_AUTHORITY`).
- **Ablation applicability**: Major implementation candidate; requires ABLATION pass before final merge.
- **Base commit**: `main` (incorporating PR #262 / M4.7a-0).
- **Candidate branch**: `claude/m4_7a1-retrieval-and-partition`.
- **Operative Plan Reference**: `coord/plans/m4_7_binding_plan.md` (Revision 11, SHA-256 `6541db93336e9181ebf3ad2f066b7b17f4550a17565036c2db5a5d82872a6407` §1.3, §1.4, §1.5, §7.2).
- **Report destination**: `/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/coord/reports/m4_7a1_retrieval_and_partition_impl.md`.

---

## Deliverables & Acceptance Criteria (§7.2, §1.3, §1.4, §1.5)

### 1. Network Module & CLI: `src/data/eodhd_retrieval.py` (§1.3)
- **Placement & Dependencies**:
  - Sole module permitted to make network requests.
  - Standard library only: `urllib.request`, `urllib.error`, `json`, `hashlib`, `os`, `sys`, `pathlib`, `argparse`. No external HTTP libraries (`requests`, `httpx`, etc.).
- **Command-line Interface**:
  - `plan --snapshot-id <ID> [--index GSPC.INDX] [--from 1980-01-01] [--to <date>]`: Offline, prints projected request count and duration.
  - `components --snapshot-id <ID>`: Verbatim raw response under `raw/index/GSPC.INDX.fundamentals.json`; manifest key `snapshot.components_retrieved_utc_date`; validates JSON list/object shape; refuses `components_malformed` or `components_empty`.
  - `symbols --snapshot-id <ID>`: Listed (`delisted=0`) and delisted (`delisted=1`) US equity inventories to `symbols/listed.parquet` and `symbols/delisted.parquet`.
  - `calendar --snapshot-id <ID>`: Requires seal; writes `raw/index/GSPC.INDX.eod.json` (levels, private) and `calendar/GSPC.INDX.dates.parquet` (date column only).
  - `splits --snapshot-id <ID> [--codes <file>] [--refresh]`: Requires seal; runs before `eod`; strict `YYYY-MM-DD` date parsing; splits at `holdout_end`; validates `ratio = N / M > 0`; records `splits_status`, `splits_discovery_status`, `splits_holdout_status`.
  - `eod --snapshot-id <ID> [--codes <file>] [--refresh]`: Requires seal, calendar, and splits status per code; checks `splits_required_before_eod`; writes `dates/<CODE>.US.parquet` before value validation; run-local scale check against calendar on consecutive on-calendar bars (gap <= 20 calendar rows, step > 15% without split -> quarantined as `validation_failed:unverified_split`); partitions at `holdout_end` into `eod/discovery/` and `eod/holdout/`; records `split_evidence_basis` and `split_table_sha256_at_eod_validation`.
  - `dividends --snapshot-id <ID> [--codes <file>] [--refresh]`: Requires seal; runs after `eod`; validates `value >= 0`; partitions at `holdout_end`.
  - `all --snapshot-id <ID> [--consideration-securities <file>]`: Runs `components` and `symbols`, then exits with exit code 3 and `holdout_seal_required` if seal missing; resumes with `calendar`, `splits`, `eod`, `dividends`, `verify`.
  - `verify --snapshot-id <ID>`: Offline; checks manifest integrity, SHA-256 hashes of all authorized files, `split_evidence_stale`, completeness (`retrieval_complete`), and scans every byte for token leaks.
- **Token Hygiene & Transport Seam**:
  - `EFR_EODHD_API_TOKEN` read only from `os.environ.get`; never logged, stored, printed, or chained in exceptions. Absent token exits 2 with fixed message.
  - `_request(url_without_token, token, *, timeout)` appends token; catches `HTTPError`, `URLError`, `OSError`, `TimeoutError` and raises sanitized `RetrievalTransportError` where URL has token replaced with `<redacted>`. Original exception never chained.
  - Injected transport seam (`transport: Callable[[str], bytes] | None = None`) for offline deterministic unit testing.
- **Persistent Provider Errors (§1.3)**:
  - Manifest records `provider_error_history` per code and table.
  - When history contains 3 distinct UTC dates while status is `provider_error`, sets terminal status `unavailable:persistent_provider_error`.
- **Role-Keyed Manifest & Atomic Writes (§1.2, §1.3, Appendix A)**:
  - Atomic file writing via temp file replace.
  - Manifest records authorized files and hashes; unauthorized or tampered files refused.

### 2. Holdout Seal Derivation: `src/data/holdout_partition.py` (§1.4)
- Derives `holdout_seal_v1.json` from `membership/historical_components_raw.parquet` and `snapshot.components_retrieved_utc_date` from manifest.
- Parsing rules: entry collapse, raw overlap handling, exclusion of invalid dates.
- Monthly raw counts $n_{\text{raw}}(m)$ on calendar month-ends.
- Band check: $470 \le n \le 530$.
- Rule `coverage_start_tolerant_3_isolated_v1`: earliest month-end $m^*$ where later month-ends have at most 3 isolated exceptions, none $<450$ or $>560$.
- Sensitivity: `coverage_start_strict` (zero exceptions).
- `holdout_start = coverage_start`; `holdout_end = holdout_start + 10 calendar years`. Check `holdout_end <= 2014-01-01` (refuse `holdout_overlaps_prior_exposure` if later).
- Writes prospective seal with `status: pending`.

### 3. Structural & Security Assertions (§1.3, Appendix D)
- **T-STRUCT-1**: Structural test in `tests/test_project_structure.py` verifying that ONLY `src/data/eodhd_retrieval.py` imports network-capable modules (`urllib.request`, `urllib.error`, `http.client`, `requests`, `httpx`, `socket`, `ssl`, etc.). All other modules under `src`, `research`, and `scripts` are strictly network-free.

---

## Deterministic Test Oracles (§7.2, Appendix D)

Dedicated tests in `tests/test_eodhd_retrieval.py`, `tests/test_m4_7_holdout_seal.py`, and `tests/test_project_structure.py`:
1. **T-RET-1**: Token absent exits 2 with fixed message.
2. **T-RET-2**: Injected fake transport records URLs; verifies no byte, log line, stderr line, or traceback contains raw or percent-encoded token, including on simulated `HTTPError`.
3. **T-RET-3**: HTTP status handling (401 stops without retry, 402 stops, 404 typed and continues, 429 backs off then typed stop, 5xx retries then continues).
4. **T-RET-4**: Resume skips hashed files; `--refresh` refetches.
5. **T-RET-5**: Storage directory inside repository root refuses with `data_dir_inside_repository`.
6. **T-RET-6**: Split string `"2.000000/1.000000"` parses to `2.0`. Invalid ratios (`"0/1"`, `"1:2"`, empty) quarantine affected partition.
7. **T-RET-7**: Rows split at `holdout_end` into discovery/holdout. Value defect in holdout quarantines only holdout partition, leaving discovery partition and date sidecar intact.
8. **T-RET-8**: Components response parsing, `components_retrieved_utc_date` recording, malformed/empty detection with typed refusals (`components_malformed`, `components_empty`).
9. **T-RET-9**: `calendar`, `splits`, `eod`, or `dividends` without seal refuses with `holdout_seal_missing`.
10. **T-RET-10**: Canonical snapshot sequence: `components`, `symbols`, seal pause, `calendar`, `splits`, `eod`, `dividends`, `verify` on fake transport, covering all sub-cases (a)–(h).
11. **T-RET-11**: Date structure validation (unparseable, duplicate, unsorted refuse whole code with typed reason; sidecar not written).
12. **T-RET-12**: Splits and dividends parsed date-first; partition at `holdout_end`.
13. **T-RET-13**: Scope of `malformed_response`: missing `date` key refuses code; non-numeric values quarantine partition only.
14. **T-RET-14**: Resume and completeness: `verify` reports `retrieval_complete = true` only when all requested codes hold terminal statuses.
15. **T-RET-15**: Run-local scale check on consecutive on-calendar bars: gap <= 20 rows with step > 15% and no split table row -> `validation_failed:unverified_split`.
16. **T-RET-16**: Persistent provider errors: 5xx on 3 distinct UTC dates -> `unavailable:persistent_provider_error`.
17. **T-RET-17**: Refresh and authorized reads: manifest role authorization, hash verification, tamper detection (`artifact_hash_mismatch`).
18. **T-SEAL-1**: Holdout seal derivation from components fixture: calculates $n_{\text{raw}}(m)$, tolerance rule, 10-year holdout window, SHA-256 seal prospective hash.
19. **T-STRUCT-1**: Network import allowlist enforcement across repository.
