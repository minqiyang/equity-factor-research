# M4.7a-1 Repair Attempt 2: Implementation Report

- Task/attempt: `m4_7a1-repair-a2`
- Card: `coord/v8_review_20260923/card_m4_7a1_repair_a2.md`
- Prior candidate: `ed08d6c0cd9425e9d13995596de6820bc12f1006`; base
  `2c07ee4db70bc90cd449382c69b63765de2eab7d` (main after PR #262).
- Audits remediated: `coord/reports/v8_review_20260923/m47a1/audit1_m47a1_gpt6astra_a1.md`
  (M47A1-A1-M1, M47A1-A1-A2) and `audit2_m47a1_opus_a1.md` (A-1, A-2, A-3, A-5).
- Branch: `claude/m4_7a1-retrieval-and-partition`; the repair is one commit on
  top of `ed08d6c`, pushed to `origin` under the owner's instruction for this
  task.
- Evidence ceiling: offline fake transport and synthetic fixtures. No live
  network call, vendor token, or private data was used.

## Result

Every finding named by the card is resolved and covered by a regression test.
Out of scope for this card and still open: audit 1's M47A1-A1-A3 (partial
symbol pair) and audit 2's A-4 (February month-end addition) and A-6 (bundled
process rules).

| Check | Result |
| --- | --- |
| `pytest tests/test_eodhd_retrieval.py tests/test_m4_7_holdout_seal.py tests/test_project_structure.py -q` | 142 passed |
| `pytest tests/test_governance_constitution.py -v` | 21 passed |
| Full suite `pytest -q -n 8` | 2,890 passed, 2 skipped, 0 failed |
| `ruff check . --exclude .venv` | All checks passed |
| `git diff --check` | clean |

## Findings And Fixes

### M47A1-A1-M1 (MATERIAL / P1): `all --refresh` kept the earlier window

- `cmd_all` passes `session.args.refresh` to `_run_table`
  (`src/data/eodhd_retrieval.py:896`).
- `_is_open` returns true when the entry's recorded `request_window` differs
  from `{"from": --from, "to": --to}` (`_request_window`, `_is_open` at
  lines 522–541). A plain resumed command therefore retrieves an extended
  window.
- `verify` lists a terminal entry with a different window as
  `<status>:request_window_mismatch`, so `retrieval_complete` stays false
  until the requested window is retrieved.
- Consequential guard: the calendar records its `request_window`, and `eod`
  refuses `calendar_window_insufficient` before any request when the calendar
  window does not cover the requested window (`_window_covers`). Without it,
  bars beyond the calendar would be off-calendar and skip the scale check of
  plan 1.3 step 5 silently. The calendar stays write-once per snapshot (S7);
  a wider calendar needs a new snapshot id.
- Tests:
  - `test_m47a1_a1_m1_all_refresh_retrieves_the_extended_window` reproduces
    the audit capsule with date-honoring EOD endpoints. `all --to 2004-06-30
    --refresh` after a retrieval through 2004-03-01 makes 12 requests in
    canonical order. Every entry records the new window, every sidecar ends on
    2004-06-30, the dates hash changes, and `retrieval_complete` is true. An
    unchanged-window `all` then makes zero requests, and an unchanged-window
    `all --refresh` refetches all 12.
  - `test_m47a1_a1_m1_changed_window_reopens_entries_without_refresh`
  - `test_m47a1_a1_m1_eod_refuses_a_window_the_calendar_does_not_cover`

### A-1 / M47A1-A1-A2: token in a dataclass field

`Session` no longer has `token` or `transport` fields. `main` builds two
closures in `_token_closures`: `request(url, timeout)`, which calls `_request`
with the token, and `contains_token(bytes)` for the leak scan. The plan's
wording ("travels only as a function argument") holds.
`test_a1_session_holds_no_token` captures the live session, asserts no
`token` field, checks that `repr(session)` and every attribute's `repr`
contain none of the four token forms, and exercises `contains_token`.

### A-2: non-`OSError` transport failures escaped unconverted

`_request` ends with `except Exception`, reached after the `urllib` handlers.
It maps `http.client.IncompleteRead`, `http.client.InvalidURL`, `ValueError`,
and similar failures to `provider_error` with status `None`, and still raises
`RetrievalTransportError` after the handlers close. `__cause__` and
`__context__` are both `None`. `BaseException` (interruption) still
propagates. The module adds no `http.client` import, so T-STRUCT-1's pinned
set stays `{urllib.request, urllib.error}`. Tests:
`test_a2_non_oserror_transport_failures_are_sanitized_without_chaining`
(three failure types) and `test_a2_incomplete_read_is_retried_then_provider_error`
(retried to `provider_error`; the run continues with the next code).

### A-3: unvalidated codes in URLs and paths

`CODE_PATTERN = ^[A-Za-z0-9][A-Za-z0-9._-]*$`, applied to the full code with
`.US` appended:

- A vendor membership code that fails becomes the terminal, counted status
  `unavailable:invalid_code` for each table, with no request and no file.
  `plan` omits it.
- A curated `--codes` or `--consideration-securities` line that fails refuses
  the invocation with `invalid_code` before any request or manifest change.
- `--index` and `--benchmark` are validated with the other arguments.

Tests: `test_a3_invalid_vendor_codes_are_counted_and_never_reach_a_path_or_url`
(`../../../../ESCAPE`, `A B`, `A/B`, `.HIDDEN`; no file anywhere under the
test directory matches `*ESCAPE*`) and
`test_a3_invalid_curated_or_option_codes_refuse_before_any_request` (`../x`,
`A B`, `A/B`, `-X`, and a NUL byte). A validated code has no character that
needs URL encoding, so the path segment needs no percent-encoding.

### A-5: Claim 1 wording

Claim 1 of `coord/reports/v8_review_20260923/m47a1/claims_m47a1.md` now reads
"the only module under `src/`, `research/`, and `scripts/` that imports a
listed network module (T-STRUCT-1)". It states the scan's exact scope and the
cases outside its evidence: bare `import urllib` attribute access,
`importlib`, and network IO inside permitted libraries. It also cites the
test's real name. The rest of that directory (the two audits) remains
untracked and unmodified; only the claims file enters this commit.

## New Typed Codes

`unavailable:invalid_code` (table status, terminal), `invalid_code`
(invocation refusal), `calendar_window_insufficient` (eod refusal), and the
verify listing `<status>:request_window_mismatch`.

## Ablation

Each new guard was removed in isolation against the preserved file (restored
by SHA-256), running `tests/test_eodhd_retrieval.py`:

| ID | Guard removed | Result |
| --- | --- | --- |
| R1 | `all` passes `refresh=False` | First run: 75 passed. The window check masked it, so an unchanged-window `all --refresh` assertion was added. Rerun: `test_m47a1_a1_m1_all_refresh_…` fails |
| R2 | Window check in `_is_open` | `…changed_window_reopens_entries_without_refresh` fails |
| R3 | Window mismatch in `verify` | same test fails |
| R4 | Calendar coverage refusal | `…eod_refuses_a_window_the_calendar_does_not_cover` fails |
| R5 | `except Exception` in `_request` | four A-2 tests fail |
| R6 | Vendor code validation | `test_a3_invalid_vendor_codes_…` fails |
| R7 | Curated code validation | five parametrized A-3 cases fail |
| R8 | `--index`/`--benchmark` validation | five parametrized A-3 cases fail |

Simplification attempt: an equality check before rewriting an
`unavailable:invalid_code` entry passed every test when removed, because
`_set_entry` already logs only status changes. It was removed along with its
duplicate log line.

## Limitations

- `verify` compares entries with its own `--from`/`--to`, so a bounded
  retrieval must be verified with the same window. `all` does this by
  construction.
- A calendar fetched with an open `--to` covers any later open-ended request
  by the window rule, while its dates end at the calendar's retrieval date;
  bars after that date are off-calendar. Snapshots are retrieved in one
  session under plan 5.4, so this stays a documented boundary.
- M47A1-A1-A3, A-4, and A-6 remain open for their own dispositions.

## Next Gate

Re-audit of the repaired head by the CRITICAL-lane reviewers, then the
independent ABLATION pass and coordinator acceptance of the exact head.
