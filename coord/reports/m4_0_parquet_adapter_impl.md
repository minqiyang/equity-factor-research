# Milestone 4.0 Steps 1–2: Parquet Adapter and Blue-Chip Cohort

Date: 2026-09-20.
Assigned branch: `feat/m4-0-real-data-parquet-adapter`.
Baseline: `24592d5fd3ba21b7f53562c8c735900de7fb8441` (`main` after PR #244).
Evidence ceiling: `DIAGNOSTIC_ONLY`.
Push / PR: not performed from this producer worktree.

This report records producer implementation of the local EODHD Parquet loader
and the static 50-stock blue-chip cohort specification. Independent acceptance
remains a Coordinator gate. The slice uses synthetic `tmp_path` Parquet
fixtures only. It does not read private data directories, interpret market
results, or claim profitability.

## Objective completed

1. `src/data/parquet_loader.py` loads a single EODHD daily Parquet file into a
   date-indexed OHLCV frame and loads a symbol list into aligned wide panels.
2. `src/data/bluechip_cohort.py` pins `BLUECHIP_50_COHORT` (50 unique EODHD
   symbols) and `BENCHMARK_SYMBOL = "SPY.US"`.
3. `pyproject.toml` declares `pyarrow>=14.0`.
4. `tests/test_parquet_loader.py` covers valid loads, inventory mapping, date
   filters, and integrity refusals on temporary synthetic Parquet files.

## Design

`load_eod_parquet` reads a local `.parquet` file with PyArrow and requires
columns `date`, `open`, `high`, `low`, `close`, `adjusted_close`, and
`volume`. Extra columns are dropped. A DatetimeIndex named `date` is accepted
when the date column is stored as the table index. Timezone-aware timestamps
keep wall-clock calendar dates and become timezone-naive. Dates must be unique
and strictly increasing; unordered or duplicate rows raise
`DataIntegrityError` (`ValueError`). Price columns must be strictly positive
finite floats. Volume must be a non-negative finite number; zero volume is
valid at this loader boundary. Boolean dtypes and boolean values stored as
object columns are refused before numeric coercion.

`load_eod_cohort_panels` resolves each requested symbol to a file:

- With `inventory_path`, JSON records supply `symbol` -> relative `file`
  under `data_dir`. Supported envelopes are a top-level list, a list under
  `stocks` / `coverage` / `symbols` / `files` / `inventory` / `items`, or a
  flat `symbol: file` object.
- Without inventory, the loader tries `data_dir / f"{symbol}.parquet"` and
  then `data_dir / f"{symbol.lower()}.parquet"`.
- A missing mapping or missing file raises `FileNotFoundError`.
- Inventory paths must stay under `data_dir`.

Each file is validated in full, then sliced with inclusive `start_date` /
`end_date` when provided. Field panels share the union of remaining dates and
the requested symbol order. Missing symbol-date cells remain `NaN`. Alignment
does not fill, interpolate, or drop observed rows.

`BLUECHIP_50_COHORT` is a static current-membership snapshot of 50 liquid
U.S. large-cap EODHD symbols. `get_bluechip_50_symbols()` returns a copy.
`SPY.US` is the separate benchmark identifier. The cohort is
`DIAGNOSTIC_ONLY` and carries survivorship bias from static membership.
Formal point-in-time universe construction remains a later Milestone 4 gate.

## Files

| Path | Role |
| --- | --- |
| `src/data/parquet_loader.py` | Local Parquet EOD loaders and integrity checks |
| `src/data/bluechip_cohort.py` | Static 50-stock cohort and SPY benchmark identifier |
| `src/data/__init__.py` | Public exports for the new loaders and cohort |
| `pyproject.toml` | `pyarrow>=14.0` runtime dependency |
| `tests/test_parquet_loader.py` | Synthetic `tmp_path` unit tests |
| `tests/test_project_structure.py` | Dependency pin match for `pyarrow>=14.0` |
| `scripts/repo_map.py` | `src/data` purpose string |
| `docs/repo_map.md` | Regenerated map counts (`src/data` 7 files, `tests` 232 files) |
| `CHANGELOG.md` | Unreleased notes for the loader and cohort |

## Verification

Commands run from the producer worktree with
`/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/.venv/bin/python`
and `PYTHONPATH=src`.

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_parquet_loader.py -q` | 33 passed |
| `python -m pytest tests/ -q --basetemp=/tmp/efr-pytest-m40` | 3759 passed, 2 skipped |
| `python -m ruff check .` | All checks passed |
| `python -m compileall -q src tests research lean` | passed |

The two skipped tests are the existing platform `longdouble` skips in
`tests/test_backtest_timing_contract.py`. Full pytest used an outside-repo
`--basetemp` so ledger/EODHD path guards stay quiet.

## Ablation

A `ValidatedParquetPanel` dataclass mirroring the CSV loader was considered
and omitted: the assigned contract returns a DataFrame and a dict of
DataFrames. Inner-join date alignment was considered and omitted: union
alignment preserves observed dates and leaves missing symbol-date cells as
`NaN` (PIT-009). OHLC high/low/open/close relationship checks from
`csv_loader.load_ohlcv_csv` were considered and omitted: this slice's
integrity list is dates, finite strictly positive prices, non-negative
volume, and boolean rejection. Inventory path confinement under `data_dir`
was retained as a one-check traversal guard.

## Caveats and next gate

The loader is a local-file adapter. It does not download data, call vendor
APIs, or stamp a dataset-review decision. The blue-chip list is a static
diagnostic cohort. Loader success is schema and integrity evidence for a
file, not universe completeness, adjustment-policy proof, or a research
result.

Next authorized slice: wire the loader to an owner-approved local Parquet
inventory under the real-data readiness audit, with explicit survivorship
and adjustment caveats, before any diagnostic interpretation of real EODHD
panels.
