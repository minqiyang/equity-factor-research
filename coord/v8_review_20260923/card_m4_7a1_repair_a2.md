# Task Card: M4.7a-1 Repair Attempt 2 (M47A1-A1-M1 & Key Advisories)

- **Task/attempt**: `m4_7a1-repair-a2`
- **Objective**: Remediate findings from the Dual Audit of candidate `ed08d6c0cd9425e9d13995596de6820bc12f1006`:
  1. **M47A1-A1-M1 (MATERIAL / P1)**: `all --refresh` silently retains earlier request window. In `src/data/eodhd_retrieval.py`, `cmd_all` passed literal `False` to `_run_table`; also `_is_open` failed to compare `request_window`. Fix both so `--refresh` and extended request windows trigger proper retrieval. Add regression test covering `all --refresh` with window comparison.
  2. **A-1 / M47A1-A1-A2 (ADVISORY)**: `Session` dataclass field `token` exposes credential in `repr(session)`. Remove `token` from `Session` dataclass; pass token as explicit function argument or through request closure per plan §1.3.
  3. **A-2 (ADVISORY)**: Non-`OSError` transport exceptions (such as `http.client.InvalidURL` or `IncompleteRead`) escape `_request` unconverted. Catch all unexpected exceptions, sanitize, and raise `RetrievalTransportError` without `__cause__` or `__context__`.
  4. **A-3 (ADVISORY)**: Vendor / curator codes reach URL and file paths unvalidated. Add strict regex validation (`^[A-Za-z0-9][A-Za-z0-9._-]*$`) before URL construction and filesystem writes; fail closed on path traversal (`../`) or invalid characters.
  5. **A-5 (ADVISORY)**: Update `coord/reports/v8_review_20260923/m47a1/claims_m47a1.md` Claim 1 wording to match T-STRUCT-1 scope precisely.
- **Route**: `GENERAL_EXEC` (Coordination Standard V8.6).
- **Binding**: `OPUS_LATEST` (`claude-opus-5-5`), Claude Code (reusing existing session `de2f6871-3b7b-45c2-94c4-30e122de8751` in tab `w3:tFF`, pane `w3:pHE`).
- **Lane**: CRITICAL. **Structural**: true (`ARCHITECTURE`, `SCHEMA_PROTOCOL_CONTRACT`, `SECURITY_AUTHORITY`).
- **Base commit**: `2c07ee4db70bc90cd449382c69b63765de2eab7d` (`main`).
- **Prior candidate**: `ed08d6c0cd9425e9d13995596de6820bc12f1006` on branch `claude/m4_7a1-retrieval-and-partition`.
- **Working tree**: `/private/tmp/efr-m47a1-retrieval-20260925`.
- **Report destination**: `/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/coord/reports/m4_7a1_repair_a2_impl.md`.

---

## Acceptance Criteria

1. **M47A1-A1-M1 Resolved**:
   - `cmd_all` in `src/data/eodhd_retrieval.py` passes `session.args.refresh` to `_run_table`.
   - `_is_open` detects when an existing entry's recorded `request_window` does not match the currently requested `{"from": args.date_from, "to": args.date_to}`, returning `True` (open for retrieval).
   - Deterministic test reproduces Astra's capsule: running `all --to <date2> --refresh` after an initial window retrieves the delta bars and updates the manifest window and dates.
2. **A-1 Resolved**:
   - `Session` is no longer holding `token: str | None` as a dataclass field.
   - `repr(session)` does not contain any credential. Test added asserting this property.
3. **A-2 Resolved**:
   - `_request` catches any unhandled exception, sanitizes the message, and raises `RetrievalTransportError` without cause or context.
   - Tests verify `IncompleteRead` and `InvalidURL` do not leak tokens.
4. **A-3 Resolved**:
   - Strict code validation pattern enforced. Path traversal attempts (`../`) are rejected with typed error before filesystem access or network calls.
5. **QA Verification**:
   - `PYTHONPATH=. .venv/bin/python -m pytest tests/test_eodhd_retrieval.py tests/test_m4_7_holdout_seal.py tests/test_project_structure.py -q` passes (all existing + new tests).
   - `PYTHONPATH=. .venv/bin/python -m pytest tests/test_governance_constitution.py -v` passes.
   - `.venv/bin/ruff check . --exclude .venv` passes cleanly.
   - `git diff --check` clean.
   - Candidate committed to branch `claude/m4_7a1-retrieval-and-partition` and pushed to `origin`.
