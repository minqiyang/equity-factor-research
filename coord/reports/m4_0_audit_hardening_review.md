# GROK_REVIEW: Milestone 4.0 Audit Hardening remediation candidate `c7f9d94`

**Verdict: PASS (MATERIAL: 0)**

- Reviewer seat: `GROK_REVIEW` (Grok Build / Grok 4.6, CRITICAL lane, `GROK_LATEST` / `XHIGH`)
- Exact candidate: `c7f9d94c4a311b4c2400e5d05c33d4347f691169` (tree `46f53d65818ee43800e540d10fc56e25315d2a6d`)
- Prior candidates: `97db0ddc2990364e34ffe0a6f51c381e585e1019` (FAIL, MATERIAL: 2), `93f5fdb3ebced3f6457c9093c39dbd1035f6efbc`
- Baseline: `cf55af944efd3112e581823a4fd9ee0d726ed2d3` (`main`)
- Review root: `/private/tmp/efr-m4-hardening-review-93f5fdb` (detached HEAD at the exact candidate)
- Producer worktree was not used as the review root
- Findings under re-evaluation: MAT-M40H-1, MAT-M40H-2, ADV-M40H-1, ADV-M40H-2, ADV-M40H-5 (plus residual ADV-M40H-4)
- Review card: `coord/card_m4_0_audit_hardening_remediation_review.md`
- Coordination standard read from `/Users/rhapsoul/Documents/Codex/Standards/herdr_pi_coordinator_v7_two_file/` (`coordinator.md`, `routing_table.json`; table status `TEMPLATE_NOT_ACTIVE`)
- Date: 2026-09-20
- Review posture: read-only on this clean root; this report overwrites the prior `97db0dd` review body

This body reviews the exact candidate bytes named above. Coverage is the round-2 remediations for MAT-M40H-1 and MAT-M40H-2, the advisory items named on the card, the `97db0dd..c7f9d94` delta, independent replay of the numbered witnesses, and focused QA of 69 tests.

## Scope

Commit `c7f9d94` remediates Grok MATERIAL findings on `97db0dd`. Delta versus `97db0dd`: 6 files, `+2852 / −2366` (report/JSON regeneration dominates).

| Path | Role |
| --- | --- |
| `research/real_data_multifactor_diagnostic.py` | Fail-closed unverified splits; `adjusted_close` prices/benchmark; readiness row-0 exclusion; failure dedup |
| `src/data/parquet_loader.py` | Per-symbol discontinuity refusal; ledger errors; `permanent_id` series on cohort panels |
| `tests/test_real_data_multifactor_diagnostic.py` | Unverified-split, adjusted-close runner, dedup, and readiness cases |
| `reports/real_data_multifactor_diagnostic.md` | Regenerated 50-stock report |
| `reports/experiment_logs/real_data_multifactor_diagnostic.json` | Regenerated sidecar |
| `reports/experiment_logs/real_data_multifactor_diagnostic.trials.jsonl` | Appended current-run events |

## Coverage of prior findings

| Finding | Result on `c7f9d94` |
| --- | --- |
| Exact-head identity | HEAD `c7f9d94c4a311b4c2400e5d05c33d4347f691169`. Tree clean after QA. |
| MAT-M40H-1 4:1 jump without split evidence | **Closed.** `build_adjusted_research_panels` and `load_eod_cohort_panels` raise `DataIntegrityError` on the original vendor-volume witness. With `split_factor` `[4, 1]`, dollar volume stays `[400000, 400000]`. |
| MAT-M40H-2 backtest/benchmark basis | **Closed.** `prices = panels["adjusted_close"]`. SPY benchmark is `research_panels["adjusted_close"]`. Runner test with `close != adjusted_close` pins both. Writers name vendor `adjusted_close` as the return basis. |
| ADV-M40H-1 identity retention | **Closed.** Cohort alignment emits a `permanent_id` Series keyed by symbol. Independent two-file probe: `{'AAA.US': 'SEC_A', 'BBB.US': 'SEC_B'}`. |
| ADV-M40H-2 typed missingness | **Closed.** Leading `returns` NA is excluded. Complete OHLCV plus `pct_change` returns yield `diagnostic_ready_with_low_caveats`. Union-NaN close still yields typed missingness. Official report/JSON use `diagnostic_ready_with_low_caveats`. |
| ADV-M40H-5 duplicate failed JSONL | **Closed.** `_record_failure` returns when inventory already has `status=failed` for that `factor_id`. Unit test records one ALPHA_001 failure. |
| ADV-M40H-4 inverse-ratio strings | Remains closed in runner and official reports. Parent-walk `private_data/...` layout tokens remain (residual advisory). |
| Deterministic QA | 69 passed in 4.17s. Ruff, `compileall`, `git diff --check` passed. |

## Evaluation

### MAT-M40H-1 — Fail-closed missing split evidence

**Status: CLOSED** for the numbered 4:1 jump witness.

Without `split_factor`, `build_adjusted_research_panels` computes `scale = close / adjusted_close` and refuses when `pct_change` exceeds 15% in absolute value (`research/real_data_multifactor_diagnostic.py:275–285`). `load_eod_cohort_panels` applies the same check per symbol when split files are absent (`src/data/parquet_loader.py:120–133`). `load_symbol_splits` raises `FileNotFoundError` for a ledger-referenced missing parquet and `DataIntegrityError` on `sqlite3.Error`; the bare `except Exception: pass` is gone.

Independent replay:

| Fixture | Result |
| --- | --- |
| 4:1, vendor volume `[4000, 4000]`, no `split_factor` | `DataIntegrityError` discontinuities |
| Same with `split_factor` `[4, 1]` | Dollar `[400000, 400000]` |
| 10% dividend, no split | Dollar `[100000, 100000]`; returns `100/90−1` |
| Loader 4:1 file, no splits directory | `DataIntegrityError` on symbol AAA.US |

`test_build_adjusted_research_panels_refuses_unverified_split` pins the jump witness. Dividend-only and combined fixtures in `test_build_adjusted_research_panels_keeps_dollar_volume_basis` still match.

Residual heuristic limits (constant restated split ratio with no in-sample jump; sub-15% splits; large special dividends refused as splits; corrupt ledger blocking parquet fallback) are recorded as ADV-M40H-6. They do not reopen the original 4:1 inflation witness on files that contain the split date.

### MAT-M40H-2 — Total-return prices, labels, and benchmark

**Status: CLOSED.**

`run_real_data_multifactor_diagnostic` sets `prices = panels["adjusted_close"]` (line 442). `load_real_data_research_panels` sets the benchmark from `research_panels["adjusted_close"]` (lines 342–344). Split-adjusted `close` and vendor `volume` remain the dollar-turnover pair (`dollar_volume = split_close * volume`). Feature `returns` remain `adjusted_close.pct_change(fill_method=None)`.

`test_runner_uses_adjusted_close_for_prices_forward_returns_and_benchmark` writes `close_scale=1.0` vs `adjusted_scale=0.9` (SPY 0.85) and asserts `result["prices"]` equals `panels["adjusted_close"]` and differs from `panels["close"]`, and that the accounting benchmark equals the adjusted-close series.

Docstring, experiment-log `price_basis`, `cash_dividend_overlay`, and report configuration now match that wiring: vendor `adjusted_close` is the return basis; split-adjusted OHLC/volume carry dollar volume.

### ADV-M40H-1 — Identity on cohort panels

**Status: CLOSED.**

`_align_symbol_panels` attaches `panels["permanent_id"]` as a symbol-keyed Series of the validated single ID (`src/data/parquet_loader.py:492–500`). `build_adjusted_research_panels` forwards the object when present. `evaluate_diagnostic_readiness` and the sample digest skip non-DataFrame entries. File-level mixed-null and multi-ID refusals remain.

### ADV-M40H-2 — Readiness row-0 return NA

**Status: CLOSED.**

`evaluate_diagnostic_readiness` inspects `returns.iloc[1:]` only. Independent probe: complete panels including `pct_change` returns return `diagnostic_ready_with_low_caveats`; a NaN in `close` returns `diagnostic_ready_with_typed_missingness`. Official regenerated report and JSON record `diagnostic_ready_with_low_caveats`. Early `refused_*` gating from the prior candidate remains.

### ADV-M40H-5 — Failure-record dedup

**Status: CLOSED.**

`_record_failure` returns when inventory already contains a failed record for the same `factor_id` (lines 421–427). `test_record_failure_deduplication` appends a failed book inside `_evaluate_factor` and asserts a single ALPHA_001 failed JSONL event.

## Deterministic QA

Commands run on exact `c7f9d94c4a311b4c2400e5d05c33d4347f691169` with `/private/tmp/efr-m4-hardening-review-93f5fdb/.venv/bin/python` and `PYTHONPATH=src:.`.

Interpreter: CPython 3.12.13, pandas 3.0.6, pyarrow 25.0.1, pytest 9.1.1.

```
.venv/bin/python -m pytest -v tests/test_parquet_loader.py tests/test_real_data_multifactor_diagnostic.py
.venv/bin/ruff check research/real_data_multifactor_diagnostic.py src/data/parquet_loader.py tests/test_parquet_loader.py tests/test_real_data_multifactor_diagnostic.py
.venv/bin/python -m compileall -q src tests research
git diff --check 97db0dd..HEAD
```

| Command | Result |
| --- | --- |
| `pytest tests/test_parquet_loader.py tests/test_real_data_multifactor_diagnostic.py -v` | 69 passed in 4.17s |
| `ruff check` on the implementation/test delta | All checks passed |
| `compileall -q src tests research` | passed (exit 0) |
| `git diff --check 97db0dd..HEAD` | passed (empty) |

## Findings

MATERIAL: none.

### ADV-M40H-6 — Discontinuity heuristic is jump-only and 15%

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `c7f9d94c4a311b4c2400e5d05c33d4347f691169`
- Claim: Missing split evidence is fail-closed when `close / adjusted_close` jumps more than 15%. The original 4:1 in-sample jump is refused.
- Evidence: Independent constant-scale fixture `close=[400,400,400]`, `adjusted_close=[100,100,100]`, vendor volume `[4000,4000,4000]` (later split already in adj/volume, split date absent) is accepted with dollar volume `[1600000, 1600000, 1600000]`. A 1.1-for-1 jump (~9%) is accepted. A 20% special-dividend scale jump is refused as an unverified split. Loader `pct_change()` omits `fill_method=None` (harmless on pandas 3.0.6). A corrupt `logs/eod_request_ledger.sqlite3` raises `DataIntegrityError` and skips later `splits/{symbol}.parquet` candidates.
- Impact: Files that contain the split date remain fail-closed. Files whose history omits the split date while carrying restated split-adjusted volume can still mix raw close with split-adjusted volume. Large cash specials can refuse a valid dividend-only series.
- Resolution: Require an explicit split event table (empty allowed) per symbol, or refuse when the median `close / adjusted_close` differs from 1 by more than a documented tolerance. On ledger SQLite errors, fall through to parquet split candidates. Add a loader unit test for the 4:1 file without split events.

### ADV-M40H-4 residual — Private snapshot layout tokens remain in defaults

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `c7f9d94c4a311b4c2400e5d05c33d4347f691169`
- Claim: Inverse-ratio documentation is gone from the runner and official reports. `default_data_dir` still walks `private_data/eodhd_eod_acquisition/snapshot_20260808T005805Z`.
- Evidence: `research/real_data_multifactor_diagnostic.py:121–139`. Official `reports/real_data_multifactor_diagnostic.md` contains no `/Users/` and no `inverse ratio`.
- Impact: Owner home directories stay out of source. Tracked code still names the private snapshot directory token.
- Resolution: Require `EFR_EODHD_DATA_DIR` / `EFR_EODHD_INVENTORY_PATH` with no `private_data` parent walk.

### ADV-M40H-7 — Trial JSONL concatenates three regeneration populations

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `c7f9d94c4a311b4c2400e5d05c33d4347f691169`
- Claim: Current-run DSR uses in-memory inventory (`n_trials_for_dsr=148`, `attempt_count=156` in the regenerated JSON).
- Evidence: `reports/experiment_logs/real_data_multifactor_diagnostic.trials.jsonl` has 936 events (468 started, 468 completed), 296 distinct `trial_id`s. Diff versus `97db0dd` adds 312 lines. Sidecar `trial_family` remains 156/148.
- Impact: The append-only file mixes volume-basis regenerations. Inference in the JSON sidecar is bound to the current run.
- Resolution: Start a fresh JSONL for the canonical run, or document the concatenated regenerations next to the sidecar.

## Independent witness replay

| Witness | Result on `c7f9d94` |
| --- | --- |
| 4:1 split, no `split_factor` | `DataIntegrityError` |
| 4:1 split with factor `[4, 1]` | Dollar `[400000, 400000]` |
| 10% dividend, no split | Dollar `[100000, 100000]` |
| Loader 4:1 file, no splits dir | `DataIntegrityError` |
| Constant scale 4.0, no jump | Accepted; dollar 4× (ADV-M40H-6) |
| `prices` / SPY from `adjusted_close` | Code and unit test |
| Cohort `permanent_id` | Series `AAA.US=SEC_A`, `BBB.US=SEC_B` |
| Readiness with `returns` row-0 NA only | `diagnostic_ready_with_low_caveats` |
| Duplicate `_record_failure` | Single failed JSONL event |
| Inverse-ratio in runner / official report | Absent |

## Closing

`c7f9d94` closes MAT-M40H-1’s numbered 4:1 fail-open, drives backtest prices, forward-return labels, and the SPY benchmark from vendor `adjusted_close`, retains cohort `permanent_id`, restores `diagnostic_ready_with_low_caveats` for complete panels, and deduplicates outer failure records. 69 focused tests pass. Remaining items are advisory: the 15% jump heuristic, private snapshot layout tokens, and concatenated trial JSONL.

This report records the exact-head review of `c7f9d94c4a311b4c2400e5d05c33d4347f691169`. MATERIAL: 0.
