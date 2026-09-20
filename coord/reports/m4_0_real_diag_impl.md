# Milestone 4.0 Step 4: Real-Data Multi-Factor Diagnostic Runner

Date: 2026-09-20.
Assigned branch: `feat/m4-0-real-data-diagnostic-runner`.
Baseline: `01a2607299c8d6117c91d6734adfe4ede1b756fb` (`main` after PR #245).
Evidence ceiling: `DIAGNOSTIC_ONLY`.
Readiness decision: `diagnostic_ready_with_low_caveats`.
Survivorship bias: `true`.
Push / PR: not performed from this producer worktree.

This report records producer implementation of the local EODHD 50-stock
multi-factor diagnostic runner. Independent acceptance remains a Coordinator
gate. Unit tests use synthetic `tmp_path` Parquet fixtures. The official
command reads the owner-approved local snapshot and writes caveated diagnostic
artifacts. Outputs are workflow diagnostics. They are not profitability,
`RESEARCH_PASS`, or formal interpretation.

## Objective completed

1. `research/real_data_multifactor_diagnostic.py` loads `BLUECHIP_50_COHORT`
   plus `BENCHMARK_SYMBOL` (`SPY.US`) through `load_eod_cohort_panels`.
2. Default source window is `2016-08-08` through `2026-08-07` (2,514 trading
   days on the official snapshot).
3. The runner evaluates all 62 factor trials: 52 classical price-volume alphas
   plus 10 composites/interactions (`EQUAL_WEIGHTED_COMPOSITE`,
   `IC_WEIGHTED_COMPOSITE`, `ICIR_WEIGHTED_COMPOSITE`,
   `CORRELATION_DISCOUNTED_COMPOSITE`, `ALPHA_PRODUCT_INTERACTION`,
   `CONDITIONAL_RANK_INTERACTION`, `NEUTRALIZED_IC_COMPOSITE`,
   `SECTOR_NEUTRAL_COMPOSITE`, `MARKET_BETA_NEUTRAL_COMPOSITE`,
   `REGIME_SWITCHING_COMPOSITE`).
4. Long-only books use real `SPY.US` vendor adjusted close as the accounting
   benchmark. `SPY.US` is excluded from the factor universe.
5. M01-M11 parents are reused from the hardened multifactor path: lag-1
   execution, closed-window walk-forward IC weights, decision-time frozen
   smoothing targets, netted gross exposure, solvency guards, across-trial
   Sharpe variance for DSR, and append-only trial inventory logging.
6. Official outputs:
   - `reports/real_data_multifactor_diagnostic.md`
   - `reports/experiment_logs/real_data_multifactor_diagnostic.json`
   - `reports/experiment_logs/real_data_multifactor_diagnostic.trials.jsonl`
7. `tests/test_real_data_multifactor_diagnostic.py` covers configuration
   propagation, benchmark handling, trial recording, and report structure on
   temporary synthetic Parquet files.
8. `EXPERIMENT_LOG.md` entry `20260920-001-real-data-multifactor-diagnostic`.

## Design

Research close is vendor `adjusted_close`. Open, high, and low are scaled by
`adjusted_close / close`. Volume is scaled by the inverse ratio so dollar
volume `close * volume` equals `adjusted_close * adjusted_volume`. VWAP is
typical price on those scaled bars. Missing cells stay missing. A separate
cash-dividend overlay is refused (PIT-007).

Raw vendor `close` contains split jumps (AAPL 4:1 on 2020-08-31 moves 499.23
to 129.04). Using that series as the return basis would treat the split as a
price return. Adjusted close is the research return basis for both the cohort
and `SPY.US`.

Default data and inventory locations may be overridden with
`EFR_EODHD_DATA_DIR` and `EFR_EODHD_INVENTORY_PATH`. Tracked markdown and JSON
outputs redact private absolute paths as
`<redacted-local-eodhd-snapshot>` and
`<redacted-local-per-stock-coverage-inventory>`.

`write_experiment_log` accepts `DIAGNOSTIC_REAL_DATA_CAVEATS` through
`required_caveats`. The synthetic experiment registry skips
`experiment_type=real_data_multifactor_diagnostic` so the existing synthetic
registry remains synthetic-only.

Reduced unit-test runs may evaluate a subset of alphas and composites.
`evaluate_portfolio_weighting_comparisons` skips missing comparison-factor
keys. Official runs still supply all four comparison composites.

## Official run

Command: `PYTHONPATH=src python -m research.real_data_multifactor_diagnostic`.

| Item | Value |
| --- | --- |
| Source window | `2016-08-08` to `2026-08-07` |
| Source rows | 2514 |
| Evaluation window | `2016-09-13` to `2026-08-07` (25-row warmup) |
| Factor universe | 50 names; `SPY.US` excluded |
| Evaluated factors | 62 |
| Weighting comparison rows | 16 (4 composites × 4 schemes) |
| Attempted books | 156 |
| Distinct trials for DSR | 148 |
| Failed attempts | 0 |
| Runtime | 515.55 s |

Protected-sample classification for the 2025-05-01 through 2026-05-31 interval
remains `historical_evaluation`.

## Files

| Path | Role |
| --- | --- |
| `research/real_data_multifactor_diagnostic.py` | Local EODHD 62-trial diagnostic runner |
| `tests/test_real_data_multifactor_diagnostic.py` | Synthetic `tmp_path` Parquet unit tests |
| `src/reporting/experiment_log.py` | Diagnostic real-data caveat family |
| `src/reporting/experiment_registry.py` | Skip real-data logs in the synthetic registry |
| `research/multifactor_diagnostic_mvp.py` | Skip missing weighting-comparison factor keys |
| `reports/real_data_multifactor_diagnostic.md` | Official diagnostic markdown |
| `reports/experiment_logs/real_data_multifactor_diagnostic.json` | JSON sidecar |
| `reports/experiment_logs/real_data_multifactor_diagnostic.trials.jsonl` | Append-only trial events |
| `EXPERIMENT_LOG.md` | `20260920-001-real-data-multifactor-diagnostic` |
| `CHANGELOG.md` | Unreleased notes |
| `docs/engineering_log.md` | Producer engineering record |
| `docs/repo_map.md` | Regenerated map (`research` 25, `tests` 233) |

## Verification

Commands run from the producer worktree with
`/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/.venv/bin/python`.
Pytest uses `pythonpath = ["src"]` from `pyproject.toml`. Full pytest used an
outside-repo `--basetemp`.

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_real_data_multifactor_diagnostic.py -q` | 10 passed |
| `python -m pytest tests/ -q --basetemp=/tmp/efr-pytest-m40-real` | 3779 passed, 2 skipped |
| `python -m ruff check .` | All checks passed |
| `python -m compileall -q src tests research lean` | passed |
| `python scripts/repo_map.py` | regenerated `docs/repo_map.md` |

The two skipped tests are the existing platform `longdouble` skips in
`tests/test_backtest_timing_contract.py`.

## Ablation

A shared `evaluate_multifactor_panels` extraction from
`research/multifactor_diagnostic_mvp.py` was considered and omitted: the
synthetic official pins stay on the existing runner, and the real-data module
imports the same `_evaluate_factor`, composite helpers, DSR, PBO, and
weighting-comparison functions.

Using raw vendor `close` as the research return basis was considered and
omitted: split jumps would enter held returns. Scaled OHLC plus inverse-scaled
volume was retained so dollar volume stays on one price/volume basis.

GICS point-in-time sector maps were considered and omitted: this slice reuses
the existing five-block diagnostic `build_default_sector_mapping`.

A recursive schema registry for local Parquet diagnostics was considered and
omitted.

The one-line skip of missing weighting-comparison keys was retained so unit
tests can evaluate `EQUAL_WEIGHTED_COMPOSITE` without requiring the other
three comparison composites.

## Caveats and next gate

The blue-chip list is a static diagnostic cohort. Loader success and this
runner are schema, timing, and pipeline evidence. They do not prove universe
completeness, event-level corporate-action reconciliation, or a survivorship-free
sample. Formal interpretation remains blocked
(`dataset_manifest_reviewed = false`).

Next authorized slice remains Coordinator-owned: independent exact-head review
of this candidate, then any later Milestone 4 lineage or ledger gate.
