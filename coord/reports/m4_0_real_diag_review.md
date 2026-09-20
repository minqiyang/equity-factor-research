# GROK_REVIEW: Milestone 4.0 Step 4 candidate `330dc11`

**Verdict: PASS (MATERIAL: 0)**

- Reviewer seat: `GROK_REVIEW` (Grok Build, STANDARD lane)
- Exact candidate: `330dc11cf294c858e772198641fea4d638d803c0` (`330dc11`, `feat/m4-0-real-data-diagnostic-runner`)
- Baseline: `01a2607299c8d6117c91d6734adfe4ede1b756fb` (`main` after PR #245)
- Review root: `/private/tmp/efr-m4-0-real-review-330dc11` (detached HEAD at the exact candidate)
- Producer worktree was not used as the review root
- Producer report: `coord/reports/m4_0_real_diag_impl.md`
- Coordination standard read from `/Users/rhapsoul/Documents/Codex/Standards/herdr_pi_coordinator_v7_two_file/` (`coordinator.md`, `routing_table.json`; table status `TEMPLATE_NOT_ACTIVE`; STANDARD lane seat `GROK_REVIEW`)
- Date: 2026-09-20
- Review posture: read-only on this clean root; this report is the only authored deliverable

This body reviews the exact candidate bytes named above. Coverage is the local EODHD 62-trial diagnostic runner, price/volume research scaling, `SPY.US` accounting benchmark wiring, M01-M11 parent reuse, official diagnostic artifacts and redaction, experiment-log caveat family plus synthetic-registry isolation, and independent QA on `.venv/bin/python` with `PYTHONPATH=src`.

## Scope

Commit `330dc11` adds a local-file real-data multi-factor diagnostic runner on the static 50-name blue-chip cohort plus `SPY.US`. Delta versus `01a2607`: 16 files, `+9601 / −9`.

| Path | Role |
| --- | --- |
| `research/real_data_multifactor_diagnostic.py` | Local EODHD 62-trial diagnostic runner |
| `tests/test_real_data_multifactor_diagnostic.py` | Synthetic `tmp_path` Parquet unit tests (10 collected) |
| `research/multifactor_diagnostic_mvp.py` | Skip missing weighting-comparison factor keys |
| `src/reporting/experiment_log.py` | `DIAGNOSTIC_REAL_DATA_CAVEATS` and `required_caveats` |
| `src/reporting/experiment_registry.py` | Skip `real_data_multifactor_diagnostic` in the synthetic registry |
| `tests/test_experiment_log.py` | Diagnostic real-data caveat-family test |
| `reports/real_data_multifactor_diagnostic.md` | Official diagnostic markdown |
| `reports/experiment_logs/real_data_multifactor_diagnostic.json` | JSON sidecar |
| `reports/experiment_logs/real_data_multifactor_diagnostic.trials.jsonl` | Append-only trial events |
| `reports/real_data_readiness_audit_bluechip50.md` | Diagnostic-scope readiness record |
| `EXPERIMENT_LOG.md` | `20260920-001-real-data-multifactor-diagnostic` |
| `CHANGELOG.md` / `docs/engineering_log.md` / `docs/repo_map.md` / `scripts/repo_map.py` | Unreleased notes, process record, map purpose string |
| `coord/reports/m4_0_real_diag_impl.md` | Producer implementation report |

Evidence ceiling remains `DIAGNOSTIC_ONLY`. Unit tests use synthetic temporary Parquet files. This review did not execute the official private-snapshot command.

## Coverage

| Check | Result on `330dc11` |
| --- | --- |
| Exact-head identity | HEAD `330dc11cf294c858e772198641fea4d638d803c0`. Source tree matches that commit. Untracked `.venv` is the QA interpreter only. |
| Data loading | `load_real_data_research_panels` calls `load_eod_cohort_panels` with `BLUECHIP_50_COHORT` plus `BENCHMARK_SYMBOL` (`SPY.US`). Default window `2016-08-08` through `2026-08-07`. |
| Factor universe | Default `symbols == tuple(BLUECHIP_50_COHORT)` (50 unique). `SPY.US` is outside the cohort. Loader appends the benchmark, then drops it from factor panels. Independent probe: official JSON `symbols` length 50 and equals `BLUECHIP_50_COHORT`; `SPY.US` absent. |
| Price / volume scaling | Research close is vendor `adjusted_close`. Open/high/low scale by `adjusted_close / close`. Volume scales by the inverse ratio. VWAP is typical price on those scaled bars. `pct_change(fill_method=None)` leaves the first return missing. Unit test plus independent 4:1 split probe: dollar volume identity holds; raw-close return is `-0.75`; adjusted return is `0.0`. |
| PIT-007 cash overlay | Runner and reports refuse a separate cash-dividend overlay. Return basis is vendor adjusted close. |
| 62 factor trials | `len(ALPHA_IDS)==52`, `len(COMPOSITE_IDS)==10`, `len(FACTOR_IDS)==62`. Official factor-diagnostics table has 62 unique `FACTOR_IDS` rows; long-short table matches. JSON metrics contain the same 62 keys. |
| Lag-1 execution | Default `signal_lag_periods=1`. Forward IC labels use `execution_aligned_forward_returns(..., execution_lag=1, holding_periods=21)`. Backtests pass `signal_lag_periods` into `run_long_only_backtest` / `run_long_short_backtest` (`signals.shift(1)`). Timing contract recorded as `after_close_signal_next_observed_close_v1`. |
| Closed-window IC weights | `walk_forward_ic_weighted_composite`, `walk_forward_icir_weighted_composite`, and `walk_forward_correlation_discounted_composite` receive `execution_lag_periods=1` and `forward_holding_periods=21`. `_realized_ic_history` admits label `s` only when `source_row(s) + 22 <= source_row(t)` and `s < t`. Full-sample mean IC is written to a descriptive table and JSON `config.ic_weights`; executable composites use the walk-forward parents. |
| Frozen smoothing / netted gross / solvency | Reused backtest parents. `target_freeze_policy` is `decision_information_only_no_execution_close_rerank`. Long-short books are dollar-neutral with unit gross. Solvency guards raise before pretrade division and before a successful insolvent result. Inverse-vol uses lagged 20-day volatility. Turnover `λ=0.5` comparison books blend frozen prior targets with decision-time targets. |
| DSR trial inventory | `_evaluate_factor` and weighting comparisons go through `_run_recorded_trial`. Official JSONL: 312 lines = 156 `started` + 156 `completed`; 148 distinct `trial_id`s; 0 `failed`. `156 - 8 = 148` matches the 4 default Equal/`λ=0` books reproduced in the 4×4 grid (2 directions). DSR uses across-trial Sharpe sample variance `0.0011133023721743276` and `n_trials_for_dsr=148`. |
| Benchmark | Long-only books receive `SPY.US` research close (vendor `adjusted_close`). Missing benchmark cells raise. Synthetic fixture test equals the Parquet `adjusted_close` series and keeps `SPY.US` out of `result["prices"]`. Official report/JSON: `SPY.US vendor adjusted close`. |
| Weighting comparisons | 4 composites × 4 schemes = 16 rows in the official markdown and JSON. Equal/`λ=0` Sharpe for `EQUAL_WEIGHTED_COMPOSITE` is `0.9103` in the factor table, comparison grid, and JSON metrics. Reduced tests skip missing comparison keys; official `composite_ids` include all four comparison factors. |
| PBO | `probability_of_backtest_overfitting` on alpha-only long-only return columns, `pbo_n_splits=8`. Official sidecar: `pbo=0.442857…`, 70 combinations. Report labels this as the alpha-only family. |
| Redaction | Official markdown and JSON use `<redacted-local-eodhd-snapshot>` and `<redacted-local-per-stock-coverage-inventory>`. Independent grep of the three official artifacts: no `/Users/` and no `private_data`. JSON `outputs` are repo-relative. `EXPERIMENT_LOG.md` entry uses the same placeholders. |
| Experiment log / registry | `write_experiment_log(..., required_caveats=DIAGNOSTIC_REAL_DATA_CAVEATS)`. Official payload includes every required diagnostic caveat; `dataset_manifest_reviewed=false`; `formal_interpretation_eligible=false`; `survivorship_bias=true`; `evidence_ceiling=DIAGNOSTIC_ONLY`. Default `load_experiment_logs()` / `build_experiment_registry()` skip this experiment type: 9 synthetic rows remain; `real-data-multifactor-diagnostic` is absent. |
| `EXPERIMENT_LOG.md` | Entry `20260920-001-real-data-multifactor-diagnostic` records diagnostic ceiling, survivorship, lag-1 / closed-window contract, zero-cost remainder, 5 bps slippage, and `historical_evaluation` for 2025-05-01 through 2026-05-31. |
| Remote / trading imports | AST test refuses `requests`, `urllib`, `yfinance`, broker modules. Runner imports `data.parquet_loader` and `data.bluechip_cohort`. |
| Deterministic QA | See QA section. Producer counts reproduced. |

## Research-safety

### Local diagnostic boundary

The runner reads local Parquet files through `load_eod_cohort_panels`. Remote fetch, brokerage, and order placement are outside this module. Default source locations may be overridden with `EFR_EODHD_DATA_DIR` and `EFR_EODHD_INVENTORY_PATH`. Tracked markdown/JSON/JSONL outputs redact machine-local paths. Evidence ceiling is `DIAGNOSTIC_ONLY`. `dataset_manifest_reviewed` remains false. Formal interpretation remains ineligible.

The committed `reports/real_data_readiness_audit_bluechip50.md` records `diagnostic_ready_with_low_caveats` under that same ceiling. It is a diagnostic-scope producer audit. It does not stamp a dataset-review decision.

### Timing, labels, and composites

Feature panels use research OHLCV on or before the signal date. Portfolio formation uses `signal_lag_periods=1`. IC evaluation labels are execution-aligned 21-row forward returns starting at the lag-1 close. Those labels are targets. Walk-forward combination weights admit a monthly IC only after its forward window has closed. Regime switching lags the regime indicator by one source row. Neutralization proxies leave leading rolling NaNs in place.

### Accounting and sample honesty

Research returns use vendor `adjusted_close` for the cohort and for `SPY.US`. Scaled OHLC plus inverse-scaled volume keeps dollar volume on one price/volume basis. A separate cash-dividend overlay is refused. Official books use 0 bps transaction cost and 5 bps slippage; `zero_cost_or_slippage_is_diagnostic` is true. The static 50-name list is a current-membership diagnostic cohort; survivorship bias is explicit in the runner docstring, report, JSON, and `EXPERIMENT_LOG.md`. Weak and negative diagnostics are retained in the official tables (example: `ICIR_WEIGHTED_COMPOSITE` mean IC `-0.0344`, long-only Sharpe `0.4385`).

PIT-005 identity stitching, PIT-006 terminal payoff on disappearance, event-level corporate-action reconciliation, GICS point-in-time sectors, and a Stage 4 all-trial ledger remain later Milestone 4 gates. This snapshot's official audit records a complete 2,514 × 51 aligned window with zero missing cells, so disappearance exits are outside the observed official sample. Typed missingness reasons remain a later gate; this runner preserves NaN through scaling (`fill_method=None`).

### M01-M11 parent reuse

This slice does not re-implement the hardened backtest or combination parents. It calls `_evaluate_factor`, `evaluate_portfolio_weighting_comparisons`, `_run_recorded_trial`, `_trial_family_summary`, and the walk-forward combination helpers with the same lag/horizon arguments as the synthetic multifactor runner. Independent confirmation on this candidate is the call graph plus official inventory arithmetic (156 attempts, 148 distinct, 0 failed). Causality mutation tests for those parents live in the existing suite and passed in full QA.

## Deterministic QA

Commands run on exact `330dc11cf294c858e772198641fea4d638d803c0` with `/private/tmp/efr-m4-0-real-review-330dc11/.venv/bin/python` and `PYTHONPATH=src`. Review interpreter: CPython 3.12.13, pandas 3.0.6, pyarrow 25.0.1.

```
python -m pytest tests/test_real_data_multifactor_diagnostic.py -q
python -m pytest tests/ -q --basetemp=/tmp/efr-pytest-review-m40-real
python -m ruff check .
python -m compileall -q src tests research lean
```

| Command | Result |
| --- | --- |
| `pytest tests/test_real_data_multifactor_diagnostic.py -q` | 10 passed in 2.31s |
| `pytest tests/ -q --basetemp=/tmp/efr-pytest-review-m40-real` | 3779 passed, 2 skipped, 23 warnings in 511.84s |
| `ruff check .` | All checks passed |
| `compileall -q src tests research lean` | passed (exit 0) |
| `git diff --check 01a2607..HEAD` | passed (empty) |

The two skipped tests are the existing platform `longdouble` skips in `tests/test_backtest_timing_contract.py`. The 23 warnings are pre-existing `ConstantInputWarning` from Spearman calls in ablation, long-short, and M3.10 hardening tests.

## Findings

MATERIAL: none.

### ADV-M40R-1 — Tracked source encodes machine-local private fallback paths

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `330dc11cf294c858e772198641fea4d638d803c0`
- Claim: Tracked markdown and JSON outputs redact private absolute paths. `research/real_data_multifactor_diagnostic.py` still stores default filesystem locations as `FALLBACK_DATA_DIR` and `FALLBACK_INVENTORY_PATH`.
- Evidence: Those constants are `/Users/rhapsoul/Documents/Codex/private_data/eodhd_eod_acquisition/snapshot_20260808T005805Z` and `/Users/rhapsoul/Documents/Codex/private_data/efr_exploration_inventory_20260913/per_stock_coverage.json`. `EFR_EODHD_DATA_DIR` / `EFR_EODHD_INVENTORY_PATH` override them. Official report/JSON/JSONL and `EXPERIMENT_LOG.md` use `<redacted-local-eodhd-snapshot>` and `<redacted-local-per-stock-coverage-inventory>`. Independent grep of those artifacts found no `/Users/` and no `private_data`.
- Impact: A tracked source file names a machine-local private directory. Outputs remain redacted. Panel values, credentials, and inventory rows stay out of the public projection.
- Resolution: Keep defaults behind environment variables or a repo-external config file. Commit only the redaction tokens and the snapshot logical identifier already used in `EXPERIMENT_LOG.md`.

### ADV-M40R-2 — Synthetic registry load validates the real-data sidecar before skipping it

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `330dc11cf294c858e772198641fea4d638d803c0`
- Claim: `build_experiment_registry` keeps the synthetic registry synthetic-only by skipping `experiment_type=real_data_multifactor_diagnostic`.
- Evidence: `load_experiment_logs` calls `load_experiment_log` on every `*.json` under `reports/experiment_logs`, then filters by experiment type (`src/reporting/experiment_registry.py`). Independent probe on this candidate: default load returns 9 synthetic payloads; `real-data-multifactor-diagnostic` is absent; the official sidecar validates under `DIAGNOSTIC_REAL_DATA_CAVEATS`.
- Impact: A later invalid real-data sidecar in the shared log directory would fail synthetic registry generation even though that experiment is excluded from the table. Current official JSON is valid.
- Resolution: Read `experiment_type` before full validation, or skip this filename/type before `load_experiment_log`.

### ADV-M40R-3 — Official 62-trial artifact rows are unpinned; CI covers a reduced path

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `330dc11cf294c858e772198641fea4d638d803c0`
- Claim: `tests/test_real_data_multifactor_diagnostic.py` covers configuration, scaling, `SPY.US` benchmark wiring, trial recording, redaction, and registry skip on synthetic fixtures. Official runs still evaluate all 62 factors and the 4×4 weighting grid.
- Evidence: The 10 unit tests use two alphas plus `EQUAL_WEIGHTED_COMPOSITE` (4 comparison rows). The synthetic multifactor runner pins `OFFICIAL_COMPARISON_ROWS`. This slice has no equivalent pin of the committed 62-row / 16-row official tables. Untested implemented branches include `EFR_EODHD_*` overrides and dropping `SPY.US` when it is passed inside `symbols`. Independent read of the committed artifacts still shows 62/62/16 rows, 156/148/0 trial arithmetic, and Equal/`λ=0` Sharpe parity for `EQUAL_WEIGHTED_COMPOSITE` at `0.9103`.
- Impact: CI cannot regenerate the official private-snapshot run. A later edit can change committed official tables or drop an env/default branch without a red test. Current committed artifacts match the producer report.
- Resolution: Snapshot-assert the committed markdown factor and comparison row identifiers (no private data required). Add `tmp_path` tests for env overrides and benchmark-in-`symbols` exclusion.

### ADV-M40R-4 — Caveat family is caller-supplied rather than bound to experiment type

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `330dc11cf294c858e772198641fea4d638d803c0`
- Claim: Real-data sidecars use `DIAGNOSTIC_REAL_DATA_CAVEATS` through `required_caveats`.
- Evidence: `write_experiment_log` still defaults `required_caveats` to `SYNTHETIC_RESEARCH_CAVEATS` (`src/reporting/experiment_log.py`). The real-data writer passes `required_caveats=DIAGNOSTIC_REAL_DATA_CAVEATS`. `test_write_experiment_log_accepts_diagnostic_real_data_caveats` covers that call. A writer that sets `experiment_type=real_data_multifactor_diagnostic` and omits `required_caveats` would still be required to include `synthetic data only`.
- Impact: Official runner output includes the diagnostic family and omits `synthetic data only`. A later caller can mis-label a real-data sidecar.
- Resolution: When `experiment_type == REAL_DATA_MULTIFACTOR_EXPERIMENT_TYPE`, select `DIAGNOSTIC_REAL_DATA_CAVEATS` unless `required_caveats` is passed.

## Verdict

**PASS (MATERIAL: 0)**

`330dc11` wires `BLUECHIP_50_COHORT` plus `SPY.US` through `load_eod_cohort_panels` into the committed 62-trial diagnostic path. Research close is vendor `adjusted_close`; scaled OHLC and inverse-scaled volume preserve dollar volume; lag-1 execution, closed-window walk-forward IC weights, frozen smoothing, netted gross, solvency, across-trial DSR variance, and append-only trial inventory are reused from the hardened parents. Official artifacts are `DIAGNOSTIC_ONLY`, redact private paths, retain weak/negative diagnostics, and match 62 factors, 16 weighting rows, 156 attempts, 148 distinct trials, and 0 failures. Independent QA on this exact head: 10/10 focused tests, 3779 passed / 2 skipped full suite, ruff clean, compileall clean.

OPEN advisories: ADV-M40R-1, ADV-M40R-2, ADV-M40R-3, ADV-M40R-4. MATERIAL count is 0.

This report records the STANDARD-lane `GROK_REVIEW` body for candidate `330dc11cf294c858e772198641fea4d638d803c0`.
