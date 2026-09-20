# GROK_REVIEW: Milestone 4.0 Steps 1–2 candidate `4485873`

**Verdict: PASS (MATERIAL: 0)**

- Reviewer seat: `GROK_REVIEW` (Grok Build, STANDARD lane)
- Exact candidate: `4485873b3be1d74433a6cc5d277b1521d59d0990` (`4485873`, `feat/m4-0-real-data-parquet-adapter`)
- Baseline: `24592d5fd3ba21b7f53562c8c735900de7fb8441` (`main` after PR #244)
- Review root: `/private/tmp/efr-m4-0-review-4485873` (detached HEAD at the exact candidate)
- Producer worktree was not used as the review root
- Producer report: `coord/reports/m4_0_parquet_adapter_impl.md`
- Coordination standard read from `/Users/rhapsoul/Documents/Codex/Standards/herdr_pi_coordinator_v7_two_file/` (`coordinator.md`, `routing_table.json`; table status `TEMPLATE_NOT_ACTIVE`; STANDARD lane seat `GROK_REVIEW`)
- Date: 2026-09-20
- Review posture: read-only on this clean root; this report is the only authored deliverable

This body reviews the exact candidate bytes named above. Coverage is the Parquet EOD adapter, the static blue-chip cohort, public exports, the `pyarrow>=14.0` pin, synthetic loader tests, and independent QA on `.venv/bin/python` with `PYTHONPATH=src`.

## Scope

Commit `4485873` adds a local-file EODHD Parquet loader and a static 50-name diagnostic cohort. Delta versus `24592d5`: 12 files, `+993 / −3`.

| Path | Role |
| --- | --- |
| `src/data/parquet_loader.py` | Local Parquet EOD loaders and integrity checks |
| `src/data/bluechip_cohort.py` | Static 50-stock cohort and `SPY.US` benchmark identifier |
| `src/data/__init__.py` | Public exports |
| `pyproject.toml` | `pyarrow>=14.0` |
| `tests/test_parquet_loader.py` | Synthetic `tmp_path` unit tests (33 collected) |
| `tests/test_project_structure.py` | Dependency pin match |
| `scripts/repo_map.py` / `docs/repo_map.md` | Map purpose string and counts (`src/data` 7 files, `tests` 232 files) |
| `CHANGELOG.md` / `docs/engineering_log.md` | Unreleased notes and process record |
| `.gitignore` | `uv.lock` |
| `coord/reports/m4_0_parquet_adapter_impl.md` | Producer implementation report |

The loader is unused by `research/` runners on this candidate. Evidence ceiling remains `DIAGNOSTIC_ONLY`. Tests use synthetic temporary Parquet files.

## Coverage

| Check | Result on `4485873` |
| --- | --- |
| Exact-head identity | HEAD `4485873b3be1d74433a6cc5d277b1521d59d0990`. Source tree matches that commit. Untracked `.venv` is the QA interpreter only. |
| `load_eod_parquet` schema | Requires `date`, `open`, `high`, `low`, `close`, `adjusted_close`, `volume`. Extra columns are dropped. Empty tables raise `DataIntegrityError`. |
| Price / volume integrity | Price columns must be strictly positive finite floats. Volume must be a non-negative finite number. Zero volume is accepted. Independent probe: `inf` volume raises `DataIntegrityError`. |
| Boolean rejection | `is_bool_dtype` columns and object-stored bools are refused before `pd.to_numeric`. Bool-dtype `close` is tested. Independent probe: bool `volume` and parquet-roundtripped object bools raise `DataIntegrityError`. |
| Date order / uniqueness | Duplicate and unordered dates raise `DataIntegrityError`. Unique plus `is_monotonic_increasing` yields a strictly increasing index. |
| DatetimeIndex handling | A `DatetimeIndex` is accepted as the date axis when the `date` column is absent. Timezone-aware values keep wall-clock time and become tz-naive. UTC fixture is tested. Independent probe: `America/New_York` wall-clock strip keeps the calendar date. |
| Inventory mapping | JSON list, envelope keys `stocks` / `coverage` / `symbols` / `files` / `inventory` / `items`, and a flat `symbol: file` object are parsed. Duplicate inventory symbols raise `DataIntegrityError`. Missing mapping or missing file raises `FileNotFoundError`. The `stocks` envelope is tested. |
| `data_dir` confinement | Relative inventory paths are resolved under `data_dir`. Absolute paths and `../` escape raise `ValueError`. Tested. Independent probe: absolute file strings are refused. |
| Wide panel union / PIT-009 | Field panels share the union of remaining dates and the requested symbol order. Missing symbol-date cells stay `NaN`. Alignment does not fill, interpolate, or drop observed rows. Tested for overlapping AAA/BBB calendars. Independent probe: a symbol whose dates fall outside the slice remains all-`NaN` on the union index. |
| `BLUECHIP_50_COHORT` | 50 unique `*.US` identifiers. `BENCHMARK_SYMBOL == "SPY.US"` and is outside the cohort. `get_bluechip_50_symbols()` returns a new list. Module docstring states `DIAGNOSTIC_ONLY` and survivorship from static membership. |
| Public exports | `src/data/__init__.py` re-exports `DataIntegrityError`, `load_eod_parquet`, `load_eod_cohort_panels`, `BLUECHIP_50_COHORT`, `BENCHMARK_SYMBOL`, `get_bluechip_50_symbols`. Independent import identity matches the implementing modules. |
| `pyarrow>=14.0` | `pyproject.toml` dependencies and `tests/test_project_structure.py` pin the same string. Review interpreter: pyarrow 25.0.1, pandas 3.0.6, CPython 3.12.13. |
| Remote / trading imports | Loader imports `json`, `pathlib`, `numpy`, `pandas` only. AST test refuses `requests`, `urllib`, `yfinance`, broker/order modules. Remote URL prefixes are refused at the path boundary. |
| Deterministic QA | See QA section. Producer counts reproduced. |

## Research-safety

### Local adapter boundary

`load_eod_parquet` and `load_eod_cohort_panels` read local filesystem paths through PyArrow. Remote prefixes `http://`, `https://`, `ftp://`, `s3://`, and `gs://` raise `ValueError`. Symbol identifiers must be bare names. Inventory file strings must stay under `data_dir` after `Path.resolve()`. The module is a schema and integrity adapter. Loader success is file-level evidence. It does not stamp a dataset-review decision, interpret returns, or claim profitability.

### Timing and missingness

Each Parquet file is validated in full, then sliced with `start_date` / `end_date` when provided. The slice uses label `loc` on the already-validated index. Full-file validation is fail-closed: a bad historical row refuses the file even when the requested window would have excluded it.

Union alignment preserves observed dates and leaves absent symbol-date cells as `NaN` (PIT-009 silent-repair prohibition at this boundary). File-level NaN prices and NaT dates are refused (`finite` / `missing dates`). Typed missingness reasons (`NOT_YET_LISTED`, `PROVIDER_GAP`, and related codes) remain a later Milestone 4 gate. This slice records undifferentiated `NaN` at the panel join.

### Cohort ceiling

`BLUECHIP_50_COHORT` is a static current-membership snapshot. The module states survivorship bias and `DIAGNOSTIC_ONLY`. Formal point-in-time universe construction remains a later Milestone 4 gate. `SPY.US` is a separate benchmark identifier.

PIT-005 ticker-reuse stitching, PIT-006 terminal payoff, PIT-007 dividend double counting, and price/volume dollar-turnover mixing are outside this slice: the adapter returns OHLCV panels and does not compute returns, turnover, or identity joins.

### Integrity list versus `csv_loader`

`load_ohlcv_csv` still checks high/low/open/close relationships. This Parquet adapter omits those checks by recorded ablation. Independent probe: `high=90`, `low=110` loads. That omission is accepted for this adapter slice and remains a real-data-readiness blocker before interpretation of OHLC-dependent features.

## Deterministic QA

Commands run on exact `4485873b3be1d74433a6cc5d277b1521d59d0990` with `/private/tmp/efr-m4-0-review-4485873/.venv/bin/python` and `PYTHONPATH=src`:

```
python -m pytest tests/test_parquet_loader.py -q
python -m pytest tests/ -q --basetemp=/tmp/efr-pytest-review-m40
python -m ruff check .
python -m compileall -q src tests research lean
```

| Command | Result |
| --- | --- |
| `pytest tests/test_parquet_loader.py -q` | 33 passed in 0.27s |
| `pytest tests/ -q --basetemp=/tmp/efr-pytest-review-m40` | 3759 passed, 2 skipped, 23 warnings in 521.34s |
| `ruff check .` | All checks passed |
| `compileall -q src tests research lean` | passed (exit 0) |
| `git diff --check 24592d5..HEAD` | passed (empty) |

The two skipped tests are the existing platform `longdouble` skips in `tests/test_backtest_timing_contract.py`. The 23 warnings are pre-existing `ConstantInputWarning` from Spearman calls in ablation and long-short tests.

## Findings

MATERIAL: none.

### ADV-M40-1 — Inclusive `end_date` is a midnight timestamp bound

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `4485873b3be1d74433a6cc5d277b1521d59d0990`
- Claim: `load_eod_cohort_panels` documents an inclusive `start_date` / `end_date` slice (`src/data/parquet_loader.py` docstring; producer report). `_slice_date_index` uses `frame.loc[start:end]` after `_optional_timestamp` builds midnight `Timestamp` values. `_parse_dates` keeps wall-clock time-of-day when the Parquet date axis is datetime or timezone-aware.
- Evidence: Independent probe wrote three rows at `16:00` on 2024-01-02/03/04 and requested `end_date="2024-01-04"`. The panel kept 2024-01-02 16:00 and 2024-01-03 16:00 and dropped 2024-01-04 16:00. `test_load_eod_cohort_panels_filters_inclusive_start_and_end_dates` uses midnight dates only, so the calendar-day contract is untested for accepted datetime inputs.
- Impact: Date-typed EOD rows at midnight keep the documented inclusive window. Datetime-stamped daily bars silently lose the last calendar day of the requested window. This truncates the sample. It does not inject future information.
- Resolution: Floor parsed dates to calendar day in `_parse_dates`, or treat `end_date` as inclusive of the whole calendar day. Add a fixture with a non-midnight time on `end_date`.

### ADV-M40-2 — Panel union order depends on deprecated pandas DatetimeIndex concat sorting

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `4485873b3be1d74433a6cc5d277b1521d59d0990`
- Claim: `_align_symbol_panels` does `pd.concat(pieces, axis=1)` without `sort=True`, then relabels the index with `freq=None`. Current pandas 3.0.6 sorts DatetimeIndex unions by default. Pandas emits `Pandas4Warning`: future concat will respect `sort=False`.
- Evidence: Independent probe requested `["BBB.US", "AAA.US"]` where BBB starts one day later than AAA. On this interpreter the close panel index was `2024-01-02` through `2024-01-05` and monotonic. The committed alignment test requests AAA first, so it does not lock later-first symbol order.
- Impact: Today the union index is chronological. A future pandas default would emit an unsorted panel when the first requested symbol lacks the globally earliest date. Downstream rolling and `loc` windows assume increasing dates.
- Resolution: Pass `sort=True` (or sort the union index explicitly) and add a later-first symbol-order test.

### ADV-M40-3 — `docs/engineering_log.md` overstates cohort verification

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `4485873b3be1d74433a6cc5d277b1521d59d0990`
- Claim: The engineering log records `BLUECHIP_50_COHORT` as "50 verified liquid blue-chip symbols from S&P 500". `src/data/bluechip_cohort.py` and the producer report describe a static current-membership snapshot of 50 liquid U.S. large-cap EODHD symbols under `DIAGNOSTIC_ONLY`, with survivorship from static membership.
- Evidence: The commit contains the literal list and uniqueness tests. It contains no S&P 500 membership extract, effective dates, or verification artifact.
- Impact: A later reader could treat the list as a verified index universe. Runtime docstring and CHANGELOG keep the diagnostic ceiling.
- Resolution: Align the engineering-log sentence with the module wording (static diagnostic snapshot; survivorship-biased; not a point-in-time S&P 500 membership record).

### ADV-M40-4 — Several implemented integrity branches lack dedicated tests

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `4485873b3be1d74433a6cc5d277b1521d59d0990`
- Claim: `tests/test_parquet_loader.py` has 33 tests covering valid loads, inventory `stocks` mapping, midnight date filters, path escape, and the main price/date/boolean refusals. Implemented branches independently confirmed on this candidate include: empty table refusal, non-finite volume refusal, boolean volume refusal, `start_date > end_date`, NaT dates, absolute inventory paths, duplicate inventory symbols, and path-like symbols.
- Evidence: Those branches exist in `src/data/parquet_loader.py` and raised the documented exception classes in independent probes. None of them appear as named tests in `tests/test_parquet_loader.py`.
- Impact: A later edit can drop an implemented guard without a red test. Current behavior matches the producer integrity list.
- Resolution: Add targeted `tmp_path` tests for empty tables, non-finite volume, later-first union order, and a non-midnight `end_date` (with ADV-M40-1).

## Verdict

**PASS (MATERIAL: 0)**

`4485873` adds a local EODHD Parquet adapter and a static 50-name `DIAGNOSTIC_ONLY` blue-chip cohort with `SPY.US` as a separate benchmark identifier. File-level schema, strictly positive finite prices, non-negative finite volume, boolean rejection, unique increasing dates, inventory path confinement, and union-`NaN` panel alignment match the assigned contract. Public exports and `pyarrow>=14.0` are pinned. Independent QA on this exact head: 33/33 loader tests, 3759 passed / 2 skipped full suite, ruff clean, compileall clean.

OPEN advisories: ADV-M40-1, ADV-M40-2, ADV-M40-3, ADV-M40-4. MATERIAL count is 0.

This report records the STANDARD-lane `GROK_REVIEW` body for candidate `4485873b3be1d74433a6cc5d277b1521d59d0990`.
