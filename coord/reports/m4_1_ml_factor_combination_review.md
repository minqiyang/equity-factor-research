# GROK_REVIEW: Milestone 4.1 candidate `d38220d`

**Verdict: PASS (MATERIAL: 0)**

- Reviewer seat: `GROK_REVIEW` (Grok Build, STANDARD lane, effort `XHIGH`)
- Exact candidate: `d38220d1aea23b254a42e5c749ffb6a27b05b956` (`d38220d`, `feat(ml): implement Milestone 4.1 walk-forward non-linear ML factor combinations`)
- Baseline: `a43e522983076f3841e049a80a001d0859aeb15f` (`HEAD^`)
- Review root: `/private/tmp/efr-m4-1-review-d38220d` (detached HEAD at the exact candidate, clean root)
- Producer worktree was not used as the review root
- Review card: `coord/card_m4_1_ml_factor_combination_review.md`
- Producer report: `coord/reports/m4_1_ml_factor_combination_report.md`
- Coordination standard read from `/Users/rhapsoul/Documents/Codex/Standards/herdr_pi_coordinator_v7_two_file/` (`coordinator.md`, `routing_table.json`; table status `TEMPLATE_NOT_ACTIVE`; STANDARD lane seat `GROK_REVIEW`)
- Date: 2026-09-20
- Review posture: read-only on this clean root; this report is the only authored deliverable

This body reviews the exact candidate bytes named above. Coverage is `walk_forward_ml_factor_composite`, diagnostic-runner integration of `RANDOM_FOREST_COMPOSITE` and `GRADIENT_BOOSTING_COMPOSITE`, committed official diagnostic artifacts, and the card-specified deterministic tests.

## Scope

Commit `d38220d` adds walk-forward non-linear ML factor combination and wires two composites into the local EODHD 50-stock diagnostic runner. Delta versus `a43e522`: 14 files, `+1955 / −457`.

| Path | Role |
| --- | --- |
| `src/features/ml_combination.py` | Walk-forward ML composite (RF, GB, HistGB, Ridge) |
| `src/features/__init__.py` | Public export of `walk_forward_ml_factor_composite` |
| `research/real_data_multifactor_diagnostic.py` | `COMPOSITE_IDS` +12, closed-window ML wiring, ML report section |
| `tests/test_ml_combination.py` | 8 unit tests (determinism, lookahead mutation, rolling window, models, validation) |
| `tests/test_real_data_multifactor_diagnostic.py` | Composite-count pin and synthetic ML runner test |
| `tests/test_project_structure.py` | `scikit-learn>=1.4` pin |
| `pyproject.toml` | `scikit-learn>=1.4` |
| `reports/real_data_multifactor_diagnostic.md` | Official diagnostic markdown including ML rows |
| `reports/experiment_logs/real_data_multifactor_diagnostic.json` | JSON sidecar; `n_trials_for_dsr=152` |
| `reports/experiment_logs/real_data_multifactor_diagnostic.trials.jsonl` | Append-only events; +320 `m4_1_ml_combination_v1` lines |
| `docs/repo_map.md` | Map counts |
| `coord/card_m4_1_ml_factor_combination.md` | Implementation card |
| `coord/card_m4_1_ml_factor_combination_review.md` | Review card |
| `coord/reports/m4_1_ml_factor_combination_report.md` | Producer implementation report |

Evidence ceiling remains `DIAGNOSTIC_ONLY`. Unit tests use synthetic panels and temporary Parquet fixtures. This review did not execute the official private-snapshot command.

## Coverage

| Check | Result on `d38220d` |
| --- | --- |
| Exact-head identity | HEAD `d38220d1aea23b254a42e5c749ffb6a27b05b956`. Working tree clean at review. |
| Causal training filter | On rebalance `t`, training dates are `s < t` and `source_row(s) + execution_lag_periods + forward_holding_periods <= source_row(t)`. Matches `_realized_ic_history` / `_horizon_rows` in `src/features/combination.py`. |
| Label construction | Diagnostic `forward_returns` come from `execution_aligned_forward_returns(..., execution_lag=signal_lag_periods, holding_periods=forward_holding_periods)`. Last price of the label at `s` is at `s_pos + lag + holding`. The filter admits that label only after that price is on or before `t`. |
| Same-day / open labels | Independent probe: mutating the label at `t`, all still-open historical rebalance labels, and the just-open source row `t_pos - horizon + 1` leaves the composite at `t` unchanged. Mutating the last closed admitted label moves Ridge scores at `t` (positive control). |
| Feature standardization | `cross_sectional_zscore` is row-wise (`mean`/`std` on `axis=1`). Independent probe: mutating another date's factor row leaves the z-score at `t` unchanged. |
| Prediction z-scoring | Finite cross-section at `t` is standardized with `ddof=1`. Independent probe: mean `~0`, std `1.0`. |
| Feature importances | Trees log `feature_importances_`; Ridge logs `abs(coef_)`; HistGradientBoosting (no native importances on sklearn 1.9.1) uses permutation importance on the training matrix only. Importances are logged; they are not features. |
| Seeds / model construction | `_instantiate_model` passes `random_state` into RF, GB, HistGB, and Ridge. Diagnostic calls use `random_state=42`. Same-process RF replay matched. |
| Diagnostic integration | `RANDOM_FOREST_COMPOSITE` and `GRADIENT_BOOSTING_COMPOSITE` are in `COMPOSITE_IDS` (length 12). `_build_composites` passes the same `forward_returns` panel and `signal_lag_periods` / `forward_holding_periods` as IC evaluation. `ESTIMATOR_VERSION` is `m4_1_ml_combination_v1`. |
| Official artifacts | Factor and LS tables include both ML composites. ML section reports 105 evaluated rebalances. JSON `composite_ids` has 12 names. `n_trials_for_dsr=152` (= parent 148 + 2 composites × 2 directions). PBO remains parent `0.5286` (alpha-only). Weak/negative ML mean ICs are retained (`RF -0.0610`, `GB -0.0378`). Paths redacted. |
| Deterministic QA | Card-specified pytest: 92 passed. Ruff clean on touched sources. See QA. |

## Research-safety

### Causal horizon

`execution_aligned_forward_returns` stores at date `s` the return from close `s + execution_lag` through close `s + execution_lag + holding_periods` (`shift(-lag)` and `shift(-(lag + holding))`). Those cells are evaluation targets.

`walk_forward_ml_factor_composite` sets `horizon_rows = execution_lag_periods + forward_holding_periods`. For each ordered rebalance `t` it computes `t_pos` on the factor panel index and admits past rebalances `s` only when `s < t` and `get_loc(s) + horizon_rows <= t_pos`. Training features are the (optionally z-scored) factor row at `s`. Training targets are `forward_returns.loc[s]`. Prediction uses the factor row at `t`.

That filter matches the last price used by the label. When `s_pos + lag + holding == t_pos`, the label uses close `t`, which is known under `after_close_signal_next_observed_close_v1`. A label whose end price is after `t` stays out of the training set.

The diagnostic runner builds `forward_returns` once with `execution_lag=config.signal_lag_periods` (default 1) and `holding_periods=config.forward_holding_periods` (default 21), then passes those same arguments into the ML helper. IC-weighted parents use the same horizon contract.

Independent Ridge probe on an 80-row panel, lag 1, holding 5, rebalance every 5 rows:

- Rebalance `t = 2020-03-05` (`t_pos=45`): 8 admitted dates, 1 still-open historical rebalance (`2020-02-27`, `s_pos=40 = t_pos - horizon + 1`).
- Mutating open labels, future labels, the same-day label at `t`, and the just-open source row leaves `composite.loc[t]` unchanged.
- Mutating the last closed admitted label (`2020-02-20`, end price `2020-02-28`) changes the z-scored Ridge row at `t` (max abs delta `0.3707`).
- Mutating factor values strictly after `t` leaves `composite.loc[t]` unchanged.

The unit test `test_walk_forward_ml_composite_zero_lookahead` mutates calendar `t - 5 days` and `t:` under holding 10 / default lag 1. That mutation is inside the open window and is a valid lock against a missing horizon. It is a weaker pin than the source-row boundary `t_pos - horizon + 1` (see ADV-M41-3). The implementation matches the card contract.

### Features, predictions, and importances

Feature panels are z-scored once, row-wise, before the rebalance loop. Row `s` does not use row `t`. Predictions at `t` are z-scored across assets with sample standard deviation (`ddof=1`). Constant finite predictions are set to `0.0`. The score vector is held on panel dates in `[t, next_t)` (or through the panel end after the last rebalance). That hold freezes the ML score, which is a monthly-rebalance contract. Linear walk-forward composites freeze weights and re-apply them to later daily z-scores. The ML hold is causal. It is a different staleness choice (see ADV-M41-4).

Feature importances are extracted after `fit` on the closed training matrix. They do not re-enter `X`. HistGradientBoostingRegressor on sklearn 1.9.1 has no `feature_importances_`; the fallback is `permutation_importance(..., n_repeats=2, random_state=random_state)` on `x_train` / `y_train`.

### Diagnostic runner and reporting

`COMPOSITE_IDS` is 12 names. `_build_composites` constructs RF and GB only when requested, using `ordered_alphas`, the shared `forward_returns`, `monthly_eval_dates`, `execution_lag_periods=config.signal_lag_periods`, `forward_holding_periods=config.forward_holding_periods`, and `random_state=42`. Those panels then go through `_evaluate_factor` with the same lag-1 backtest parents as the other composites.

Official markdown lists both ML composites in the factor table, LS table, and a dedicated importance section (105 rebalances; top features match the producer report). Limitations keep the diagnostic ceiling, survivorship, PIT-007 cash-overlay refusal, idealized lag-1 execution, and `historical_evaluation` on 2025-05-01 through 2026-05-31. JSON caveats still describe ICIR/correlation closed-window weights and omit an ML-specific closed-window sentence (see ADV-M41-2). The JSON `summary` string still says "10 composites/interactions" while `config.composite_ids` has 12 entries (see ADV-M41-1).

Trial arithmetic on the committed sidecar: 160 attempts, 152 distinct, 0 failed in the current estimator version. Parent JSON used 148 distinct with 10 composites. Adding two composites × long-only and long-short = 4 distinct trials (`148 + 4 = 152`). Eight Equal/`λ=0` reproductions remain shared with the 4×4 weighting grid (`160 - 8 = 152`). JSONL is append-only: 936 parent `m4_0_real_data_causal_accounting_v1` events plus 320 new `m4_1_ml_combination_v1` events (160 started + 160 completed). DSR uses the current-run distinct count, not the concatenated file.

PBO remains the alpha-only family and equals the parent value `0.5286`. Alpha long-only totals and Sharpes inspected against the parent markdown are unchanged; DSR cells move because the across-trial Sharpe sample now includes the two ML books (`trial_sharpe_variance` `0.0010259…` → `0.0010062…`).

## Deterministic QA

Commands run on exact `d38220d1aea23b254a42e5c749ffb6a27b05b956` with `/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/.venv/bin/python` and `PYTHONPATH=src:.`. Review interpreter: CPython 3.12.13, sklearn 1.9.1, pandas 3.0.6, numpy 2.5.3.

```
PYTHONPATH=src:. .venv/bin/pytest tests/test_ml_combination.py tests/test_real_data_multifactor_diagnostic.py tests/test_project_structure.py -q
PYTHONPATH=src:. .venv/bin/python -m ruff check src/features/ml_combination.py research/real_data_multifactor_diagnostic.py tests/test_ml_combination.py tests/test_real_data_multifactor_diagnostic.py tests/test_project_structure.py
PYTHONPATH=src:. .venv/bin/python -m compileall -q src/features/ml_combination.py research/real_data_multifactor_diagnostic.py tests/test_ml_combination.py
```

| Command | Result |
| --- | --- |
| pytest (card-specified files) | 92 passed in 6.82s |
| ruff check (touched sources) | All checks passed |
| compileall (touched sources) | passed (exit 0) |

`tests/test_ml_combination.py` collects 8 tests: same-seed RF replay, Ridge future/open-label mutation, four supported models, rolling vs expanding `mean_training_samples`, and invalid-input raises. `tests/test_real_data_multifactor_diagnostic.py` pins `len(COMPOSITE_IDS) == 12` and runs `test_runner_evaluates_ml_composites` on a synthetic 3-asset Parquet fixture. This review did not re-run the full `tests/` tree; the producer full-suite count is unverified here.

## Findings

MATERIAL: none.

### ADV-M41-1 — Official JSON summary still says 10 composites

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `d38220d1aea23b254a42e5c749ffb6a27b05b956`
- Claim: The committed experiment-log summary describes "52 implemented classical price-volume alphas and 10 composites/interactions".
- Evidence: `write_real_data_experiment_log` hard-codes that sentence (`research/real_data_multifactor_diagnostic.py`). The same sidecar `config.composite_ids` has 12 names including `RANDOM_FOREST_COMPOSITE` and `GRADIENT_BOOSTING_COMPOSITE`. Module docstring still says "plus 10 composites and interactions". Runner `COMPOSITE_IDS` length 12; synthetic `FACTOR_IDS` remains 62 by design of the MVP module.
- Impact: Prose count is stale. Executable inventory, official tables, and DSR `n_trials_for_dsr=152` follow the 12-composite run.
- Resolution: Update the summary string, module docstring, and any "10 composites" / "62-trial" prose that names this runner. Keep `FACTOR_IDS` as the synthetic MVP inventory if that list stays synthetic-only.

### ADV-M41-2 — JSON caveats omit the ML closed-window contract

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `d38220d1aea23b254a42e5c749ffb6a27b05b956`
- Claim: Official assumptions document closed-window walk-forward for ICIR and correlation-discounted weights.
- Evidence: `assumptions.composite_walk_forward_weights` and the matching caveat name ICIR/correlation only. The markdown ML section states closed forward-return labels. JSON `caveats` has no Random Forest / Gradient Boosting / ML sentence. Pipeline step 4 lists the ML composite names under "the same M01-M11 causal parents" and "closed-window walk-forward IC weights".
- Impact: A reader of the sidecar alone can miss that RF/GB train on execution-aligned forward returns with the `source_row(s) + lag + holding <= source_row(t)` cut. The code path uses that cut. Mean feature importances in the markdown table are full-sample averages of walk-forward train-set importances (descriptive, unused as signals).
- Resolution: Add an ML closed-window assumption and caveat. Split pipeline step 4 so IC-weight parents and ML parents are separate sentences. Label the importance table as descriptive.

### ADV-M41-3 — Unit lookahead test uses a calendar offset inside the open window

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `d38220d1aea23b254a42e5c749ffb6a27b05b956`
- Claim: `tests/test_ml_combination.py` tests zero lookahead under future mutation.
- Evidence: The test mutates `fwd_ret.loc[t:]` and `fwd_ret.loc[t - Timedelta(days=5):]` with `forward_holding_periods=10` and default `execution_lag_periods=1` (`horizon_rows=11`). A 5-calendar-day offset is inside the open window, so a missing horizon would fail, and an off-by-one that still excludes `t-5` would pass. Independent review probe locked the exact just-open source row `t_pos - horizon + 1` and the last closed admitted label.
- Impact: CI will not catch a one-row horizon regression that still excludes `t-5`. Current implementation matches `execution_aligned_forward_returns`.
- Resolution: Mutate the label at `s_pos = t_pos - execution_lag - holding + 1` (must stay unchanged) and at `s_pos = t_pos - execution_lag - holding` (must change for Ridge).

### ADV-M41-4 — Random Forest uses `n_jobs=-1`; scores are held constant between rebalances

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `d38220d1aea23b254a42e5c749ffb6a27b05b956`
- Claim: Results are reproducible under `random_state`.
- Evidence: `RandomForestRegressor(..., random_state=random_state, n_jobs=-1)`. Same-process unit test and independent probe matched on sklearn 1.9.1. Parallel RF still depends on the joblib backend. After prediction, `composite_output.loc[d] = pred_t` for every panel date in `[t, next_t)`, so later days reuse the rebalance-date score instead of applying the frozen model to later factor rows.
- Impact: Cross-process RF bit-identity is weaker than Ridge/GB sequential fits. Frozen scores lower turnover relative to daily frozen-model inference; official LS total turnover is `14.0111` (RF) and `14.0854` (GB). That contract is causal and is visible in the LS table.
- Resolution: Pin `n_jobs=1` for deterministic research fits. State in the ML report section that scores are constant on `[t, next_t)`.

## Verdict

**PASS (MATERIAL: 0)**

`d38220d` implements walk-forward ML factor combination with the closed execution-aligned label cut `source_row(s) + execution_lag + forward_holding <= source_row(t)`, trains on historical rebalance rows only, z-scores features cross-sectionally and predictions at `t`, and wires `RANDOM_FOREST_COMPOSITE` / `GRADIENT_BOOSTING_COMPOSITE` through the real-data diagnostic on the same `forward_returns` panel as IC evaluation. Card-specified tests passed (92). Independent boundary probes passed. Official tables retain negative ML mean ICs. OPEN advisories ADV-M41-1 through ADV-M41-4 do not block acceptance of `d38220d`.
