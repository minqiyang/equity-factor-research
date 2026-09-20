# Experiment Log

Use this file to record every meaningful experiment, including failed or
inconclusive runs. Do not delete weak results to make the project look better.

## Current Authority And Limitation

This file is the repository's diagnostic/legacy experiment record. It preserves
the current synthetic and local-CSV documentation workflow, but it is not the
immutable all-trial ledger required by Stage 4 of `docs/research_program_charter.md`
and `docs/experiment_trial_ledger_contract.md`.

`docs/point_in_time_data_methodology_contract.md` defines the Stage 3
provider-agnostic data and holdout-evidence requirements. Accepting that
contract does not review a dataset manifest or make a run eligible for formal
interpretation.

Until that ledger allocates experiment, campaign, trial-family, and trial
identifiers before execution and retains every attempt, failure, invalid or
aborted run, full configuration, code/data lineage, output hash, review
outcome, and protected-sample access, entries here may support only
appropriately caveated diagnostics. They must not support formal historical
interpretation, factor promotion, a `RESEARCH_PASS`, or a holdout-independence
claim. "Every configured case" is not evidence of complete trial accounting.

Under the demo-first engineering discipline, All-Attempt Case Logging applies
to Demo v0 runs and to the M3-01 exploratory three-factor backtest:
`python -m research.demo_v0` appends every attempted case, including failures,
to `reports/demo_v0_attempts.jsonl` and writes the synthetic comparison report
to `reports/demo_v0.md`. `python -m research.synthetic_multifactor_backtest_demo`
appends every attempted case, including failures and catchable interruptions,
to `reports/synthetic_multifactor_backtest_demo_attempts.jsonl` and writes the
synthetic comparison report to `reports/synthetic_multifactor_backtest_demo.md`.
A start record is written before computation so incomplete attempts remain
visible. M3-02 requires complete finite strictly positive price bars in those
two demos and refuses a supplied missing or zero-volume panel without silent
fill, clip, drop, or repair. M3-03 proves signal lag on those commands counts
observed source rows; a missing source row remains an omitted observation.
Those demos keep the supplied observed index. M3-07 reports adjacent
calendar-day spans and refuses panel timestamps absent from the declared
source index. Official demos declare the generated price index as source.
Session and holiday status remains unverified. M3-04 proves those commands
compute held returns from the supplied price series only and refuse a separate
cash-dividend overlay (PIT-007). Event-level dividend and split reconciliation
remains later Milestone 3/4 work. M3-05 proves those commands run on a longer
synthetic panel of length `2 * DEMO_V0_CONFIG.periods` (1512) through
`dataclasses.replace`; official frozen Demo v0 config remains 756 rows. M3-06
counts unchanging-price segments on those commands and keeps every supplied
bar. Remaining Milestone 3 work is event-level dividend/split reconciliation.
This lightweight diagnostic run logging is explicitly distinguished from the
formal experiment/trial-ledger accounting required by charter Stage 4 /
`docs/experiment_trial_ledger_contract.md` and by Milestone 4 formal research.
Existing synthetic sidecar logs under `reports/experiment_logs/` remain legacy
diagnostics and are not accepted Demo v0 evidence. `python -m research.synthetic_multifactor_workflow_demo`
remains the feature-only workflow. All-Attempt records support reproducible
demo evidence and track non-blocking imperfections in the lightweight backlog;
formal factor promotion remains reserved for Milestone 4.

## Automated Synthetic Demo Logs

Synthetic demo scripts also write deterministic JSON sidecar logs under
`reports/experiment_logs/`. These logs capture configuration, synthetic-only
data assumptions, caveats, outputs, and diagnostics from reproducible smoke
demos.

They are not substitutes for full experiment records when real data, real
universe definitions, validation splits, or parameter studies are introduced.
Synthetic demo metrics remain workflow diagnostics only and are not financial
advice, strategy validation, or profitability evidence.

`reports/experiment_registry.md` summarizes the JSON logs in a deterministic
table for review. The registry is a reporting view over existing logs; it does
not run experiments, recalculate metrics, or replace full experiment records.

`reports/synthetic_multifactor_parameter_sweep.md` is a synthetic-only
parameter sensitivity smoke test. It reports every configured case and should
not be used as parameter selection, strategy validation, financial advice, or
profitability evidence.

## 20260918-001-walking-skeleton-mvp

### Experiment ID

`20260918-001-walking-skeleton-mvp`

### Date

`2026-09-18`

### Hypothesis

A committed 50-stock static diagnostic cohort can close a synthetic
data-to-evidence loop through the three frozen diagnostic factors without
claiming point-in-time universe evidence.

### Data Source

Synthetic local generator from
`tests/fixtures/walking_skeleton/diagnostic_cohort_v1.json`. Seed
`20260919`. No vendor, private path, or real market data.

### Dataset Review Decision

`dataset_manifest_reviewed = false`. `formal_interpretation_eligible = false`.
Evidence ceiling `DIAGNOSTIC_ONLY`. No dataset-review decision ID.

### Universe

Static 50-name diagnostic slots `D50_01` through `D50_50`. Survivorship-biased
by construction. Not point-in-time membership evidence.

### Date Range

Source `2021-01-04` through `2023-11-27`. Evaluation `2021-12-22` through
`2023-11-27` after 252-row momentum warm-up.

### Features / Factors

- `MOM_12_1`: `price[t-21] / price[t-252] - 1`
- `REV_1M`: `-(price[t] / price[t-21] - 1)`
- `LOW_VOL_3M`: negative sample standard deviation of 63 trailing simple
  returns (`ddof=1`)
- Signal lag: 1 observed source row. Forward IC labels start at the execution
  close.

### Parameters

Monthly last-row rebalance (`ME`), long-only top 5 equal-weight names,
`signal_lag_periods=1`, `n_trials=3` for DSR.

### Benchmark

Synthetic equal-weight 50-name diagnostic-cohort price path. Cost-free.

### Transaction Costs

`0.00` bps. Zero-cost remainder is diagnostic.

### Slippage Model

Fixed `5.00` bps on drift-adjusted target-weight turnover.

### Metrics

Recorded in `reports/walking_skeleton_mvp.md` and
`reports/experiment_logs/walking_skeleton_mvp.json`. All three factors are
retained, including negative mean IC and negative Sharpe. These are
`DIAGNOSTIC_ONLY` synthetic values, not profitability evidence.

### Limitations

Static membership, synthetic prices, idealized close-reset execution, and no
dataset review. This is not a 14-trial run.

### Next Action

Keep as a walking-skeleton wiring check. Do not reopen identity, D8, A2, or
formal interpretation from this result.

## 20260919-001-alphas-diagnostic-mvp

### Experiment ID

`20260919-001-alphas-diagnostic-mvp`

### Date

`2026-09-19`

### Hypothesis

Classical WorldQuant price-volume alphas can be wired through the committed
50-stock diagnostic cohort with the same Rank IC, ICIR, Newey-West, DSR, and
5 bps monthly backtest path as the walking skeleton.

### Data Source

Synthetic local generator from
`tests/fixtures/walking_skeleton/diagnostic_cohort_v1.json`. Close prices use
seed `20260919`. Companion open, low, and volume use `seed + 1`. No vendor,
private path, or real market data.

### Dataset Review Decision

`dataset_manifest_reviewed = false`. `formal_interpretation_eligible = false`.
Evidence ceiling `DIAGNOSTIC_ONLY`. No dataset-review decision ID.

### Universe

Static 50-name diagnostic slots `D50_01` through `D50_50`. Survivorship-biased
by construction. Not point-in-time membership evidence.

### Date Range

Source `2021-01-04` through `2023-11-27`. Evaluation `2021-02-08` through
`2023-11-27` after 25-row alpha warm-up.

### Features / Factors

- `ALPHA_001`: `rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2), 5)) - 0.5`
- `ALPHA_002`: `-correlation(rank(delta(log(volume), 2)), rank((close-open)/open), 6)`
- `ALPHA_003`: `-correlation(rank(open), rank(volume), 10)`
- `ALPHA_004`: `-Ts_Rank(rank(low), 9)`
- `ALPHA_006`: `-correlation(open, volume, 10)`
- `ALPHA_012`: `sign(delta(volume, 1)) * (-delta(close, 1))`
- Signal lag: 1 observed source row. Forward IC labels start at the execution
  close.

### Parameters

Monthly last-row rebalance (`ME`), long-only top 5 equal-weight names,
`signal_lag_periods=1`, `n_trials=6` for DSR with Euler-Mascheroni mix.

### Benchmark

Synthetic equal-weight 50-name diagnostic-cohort price path. Cost-free.

### Transaction Costs

`0.00` bps. Zero-cost remainder is diagnostic.

### Slippage Model

Fixed `5.00` bps on drift-adjusted target-weight turnover.

### Metrics

Recorded in `reports/alphas_diagnostic_mvp.md` and
`reports/experiment_logs/alphas_diagnostic_mvp.json`. All six factors are
retained, including negative mean IC. Official 4-decimal rows:

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | -0.0083 | -0.0541 | -0.3019 | 0.1123 | -0.40% | 0.0505 | -23.34% |
| ALPHA_002 | -0.0028 | -0.0189 | -0.1163 | 0.0235 | -15.29% | -0.4035 | -27.88% |
| ALPHA_003 | -0.0383 | -0.2358 | -1.1060 | 0.5251 | 31.28% | 0.8040 | -16.56% |
| ALPHA_004 | -0.0181 | -0.1301 | -1.0225 | 0.2068 | 8.41% | 0.2839 | -23.66% |
| ALPHA_006 | -0.0036 | -0.0292 | -0.1833 | 0.1514 | 3.59% | 0.1589 | -14.41% |
| ALPHA_012 | -0.0069 | -0.0548 | -0.3888 | 0.3865 | 21.76% | 0.5961 | -18.88% |

These are `DIAGNOSTIC_ONLY` synthetic values, not profitability evidence.

### Limitations

Static membership, synthetic prices, companion synthetic OHLCV, idealized
close-reset execution, and no dataset review. This is not a 14-trial run.

### Next Action

Keep as a DIAGNOSTIC_ONLY price-volume alpha wiring check. Do not reopen
identity, D8, A2, or formal interpretation from this result.

## 20260919-002-multifactor-diagnostic-mvp

### Experiment ID

`20260919-002-multifactor-diagnostic-mvp`

### Date

`2026-09-19`

### Hypothesis

WorldQuant price-volume alphas 5, 8, 10, 13, 14, 18, and 20, plus equal-weighted
and in-sample IC-weighted z-score composites, can be wired through the committed
50-stock diagnostic cohort with the same Rank IC, ICIR, Newey-West, DSR, and
5 bps monthly backtest path as batch 1.

### Data Source

Synthetic local generator from
`tests/fixtures/walking_skeleton/diagnostic_cohort_v1.json`. Close prices use
seed `20260919`. Companion open, low, and volume use `seed + 1`. High is an
additional `seed + 1` draw after those panels. VWAP is typical price
`(high + low + close) / 3`. No vendor, private path, or real market data.

### Dataset Review Decision

`dataset_manifest_reviewed = false`. `formal_interpretation_eligible = false`.
Evidence ceiling `DIAGNOSTIC_ONLY`. No dataset-review decision ID.

### Universe

Static 50-name diagnostic slots `D50_01` through `D50_50`. Survivorship-biased
by construction. Not point-in-time membership evidence.

### Date Range

Source `2021-01-04` through `2023-11-27`. Evaluation `2021-02-08` through
`2023-11-27` after 25-row alpha warm-up.

### Features / Factors

- `ALPHA_005`: `rank(open - ts_mean(vwap, 10)) * (-abs(rank(close - vwap)))`
- `ALPHA_008`: `-rank((ts_sum(open, 5) * ts_sum(returns, 5)) - ts_delay(that product, 10))`
- `ALPHA_010`: `rank(delta if ts_min(delta, 4) > 0 or ts_max(delta, 4) < 0 else -delta)`
- `ALPHA_013`: `-rank(ts_cov(rank(close), rank(volume), 5))`
- `ALPHA_014`: `-rank(ts_delta(returns, 3)) * ts_corr(open, volume, 10)`
- `ALPHA_018`: `-rank(ts_std(abs(close-open), 5) + (close-open) + ts_corr(close, open, 10))`
- `ALPHA_020`: `-rank(open - delay(high, 1)) * rank(open - delay(close, 1)) * rank(open - delay(low, 1))`
- `EQUAL_WEIGHTED_COMPOSITE`: equal-weight average of cross-sectional z-scores
- `IC_WEIGHTED_COMPOSITE`: same z-scores with in-sample mean monthly Rank IC weights
- Signal lag: 1 observed source row. Forward IC labels start at the execution
  close.

### Parameters

Monthly last-row rebalance (`ME`), long-only top 5 equal-weight names,
`signal_lag_periods=1`, `n_trials=9` for DSR with Euler-Mascheroni mix.

### Benchmark

Synthetic equal-weight 50-name diagnostic-cohort price path. Cost-free.

### Transaction Costs

`0.00` bps. Zero-cost remainder is diagnostic.

### Slippage Model

Fixed `5.00` bps on drift-adjusted target-weight turnover.

### Metrics

Recorded in `reports/multifactor_diagnostic_mvp.md` and
`reports/experiment_logs/multifactor_diagnostic_mvp.json`. All seven alphas and
both composites are retained, including negative mean IC. Official 4-decimal
rows:

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_005 | -0.0254 | -0.1645 | -0.8436 | 0.2252 | 15.55% | 0.4512 | -23.13% |
| ALPHA_008 | -0.0291 | -0.2172 | -1.3083 | 0.1527 | 8.87% | 0.2920 | -23.31% |
| ALPHA_010 | -0.0182 | -0.1064 | -0.7266 | 0.2813 | 19.43% | 0.5551 | -23.54% |
| ALPHA_013 | 0.0345 | 0.2377 | 1.6730 | 0.1071 | 3.69% | 0.1639 | -24.01% |
| ALPHA_014 | -0.0063 | -0.0432 | -0.2736 | 0.0667 | -2.02% | 0.0119 | -23.78% |
| ALPHA_018 | -0.0324 | -0.2301 | -2.2995 | 0.0648 | -2.16% | 0.0032 | -20.67% |
| ALPHA_020 | -0.0315 | -0.2621 | -1.6914 | 0.1781 | 11.10% | 0.3520 | -20.93% |
| EQUAL_WEIGHTED_COMPOSITE | -0.0320 | -0.2186 | -1.5392 | 0.0073 | -19.77% | -0.5429 | -34.25% |
| IC_WEIGHTED_COMPOSITE | 0.0420 | 0.2742 | 1.6372 | 0.2277 | 15.84% | 0.4563 | -21.13% |

These are `DIAGNOSTIC_ONLY` synthetic values, not profitability evidence.

### Limitations

Static membership, synthetic prices, companion synthetic OHLCV, typical-price
VWAP proxy, in-sample IC weights, idealized close-reset execution, and no
dataset review. This is not a 14-trial run.

### Next Action

Keep as a DIAGNOSTIC_ONLY batch-2 alpha and composite wiring check. Do not
reopen identity, D8, A2, or formal interpretation from this result.

## 20260919-003-multifactor-diagnostic-mvp

### Experiment ID

`20260919-003-multifactor-diagnostic-mvp`

### Date

`2026-09-19`

### Hypothesis

The 23 implemented WorldQuant price-volume alphas, plus equal-weighted and
in-sample IC-weighted z-score composites, can be wired through the committed
50-stock diagnostic cohort with monthly Rank IC, ICIR, Newey-West, DSR
(`n_trials=25`), and 5 bps monthly backtests.

### Data Source

Synthetic local generator from
`tests/fixtures/walking_skeleton/diagnostic_cohort_v1.json`. Close prices use
seed `20260919`. Companion open, low, and volume use `seed + 1`. High is an
additional `seed + 1` draw after those panels. VWAP is typical price
`(high + low + close) / 3`. No vendor, private path, or real market data.

### Dataset Review Decision

`dataset_manifest_reviewed = false`. `formal_interpretation_eligible = false`.
Evidence ceiling `DIAGNOSTIC_ONLY`. No dataset-review decision ID.

### Universe

Static 50-name diagnostic slots `D50_01` through `D50_50`. Survivorship-biased
by construction. Not point-in-time membership evidence.

### Date Range

Source `2021-01-04` through `2023-11-27`. Evaluation `2021-02-08` through
`2023-11-27` after 25-row alpha warm-up. `alpha_019` uses a 250-row return
sum, so its early monthly IC cells stay missing until that window is full.

### Features / Factors

Implemented alphas `ALPHA_001` through `ALPHA_101` listed in
`research/multifactor_diagnostic_mvp.py` `ALPHA_IDS`, plus
`EQUAL_WEIGHTED_COMPOSITE` and `IC_WEIGHTED_COMPOSITE`. Signal lag: 1 observed
source row. Forward IC labels start at the execution close. IC-weighted
composite uses in-sample mean monthly Rank IC of the 23 alphas.

### Parameters

Monthly last-row rebalance (`ME`), long-only top 5 equal-weight names,
`signal_lag_periods=1`, `n_trials=25` for DSR with Euler-Mascheroni mix.

### Benchmark

Synthetic equal-weight 50-name diagnostic-cohort price path. Cost-free.

### Transaction Costs

`0.00` bps. Zero-cost remainder is diagnostic.

### Slippage Model

Fixed `5.00` bps on drift-adjusted target-weight turnover.

### Metrics

Recorded in `reports/multifactor_diagnostic_mvp.md` and
`reports/experiment_logs/multifactor_diagnostic_mvp.json`. All 23 alphas and
both composites are retained, including negative mean IC. Official 4-decimal
rows:

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | -0.0083 | -0.0541 | -0.3019 | 0.0280 | -0.40% | 0.0505 | -23.34% |
| ALPHA_002 | -0.0028 | -0.0189 | -0.1163 | 0.0036 | -15.29% | -0.4035 | -27.88% |
| ALPHA_003 | -0.0383 | -0.2358 | -1.1060 | 0.2630 | 31.28% | 0.8040 | -16.56% |
| ALPHA_004 | -0.0181 | -0.1301 | -1.0225 | 0.0650 | 8.41% | 0.2839 | -23.66% |
| ALPHA_005 | -0.0254 | -0.1645 | -0.8436 | 0.1092 | 15.55% | 0.4512 | -23.13% |
| ALPHA_006 | -0.0036 | -0.0292 | -0.1833 | 0.0420 | 3.59% | 0.1589 | -14.41% |
| ALPHA_007 | 0.0106 | 0.0984 | 0.5324 | 0.0028 | -17.35% | -0.4558 | -25.97% |
| ALPHA_008 | -0.0291 | -0.2172 | -1.3083 | 0.0666 | 8.87% | 0.2920 | -23.31% |
| ALPHA_009 | -0.0194 | -0.1182 | -0.7920 | 0.0998 | 13.74% | 0.4208 | -24.30% |
| ALPHA_010 | -0.0182 | -0.1064 | -0.7266 | 0.1457 | 19.43% | 0.5551 | -23.54% |
| ALPHA_012 | -0.0069 | -0.0548 | -0.3888 | 0.1622 | 21.76% | 0.5961 | -18.88% |
| ALPHA_013 | 0.0345 | 0.2377 | 1.6730 | 0.0428 | 3.69% | 0.1639 | -24.01% |
| ALPHA_014 | -0.0063 | -0.0432 | -0.2736 | 0.0240 | -2.02% | 0.0119 | -23.78% |
| ALPHA_017 | -0.0478 | -0.4175 | -2.9894 | 0.3084 | 34.36% | 0.8826 | -14.41% |
| ALPHA_018 | -0.0324 | -0.2301 | -2.2995 | 0.0232 | -2.16% | 0.0032 | -20.67% |
| ALPHA_019 | -0.0974 | -0.6117 | -2.9056 | 0.0105 | -6.88% | -0.1828 | -14.82% |
| ALPHA_020 | -0.0315 | -0.2621 | -1.6914 | 0.0809 | 11.10% | 0.3520 | -20.93% |
| ALPHA_023 | -0.0152 | -0.0973 | -0.6273 | 0.2295 | 28.34% | 0.7390 | -17.50% |
| ALPHA_028 | 0.0097 | 0.0693 | 0.3415 | 0.0597 | 7.55% | 0.2593 | -30.66% |
| ALPHA_033 | -0.0308 | -0.2051 | -2.0262 | 0.1666 | 22.10% | 0.6057 | -17.06% |
| ALPHA_038 | -0.0174 | -0.1119 | -0.7676 | 0.0429 | 3.77% | 0.1647 | -20.58% |
| ALPHA_054 | 0.0048 | 0.0346 | 0.3353 | 0.0359 | 1.93% | 0.1156 | -25.60% |
| ALPHA_101 | 0.0181 | 0.1150 | 1.0473 | 0.0303 | 0.28% | 0.0709 | -29.74% |
| EQUAL_WEIGHTED_COMPOSITE | -0.0456 | -0.3165 | -2.4460 | 0.0059 | -12.20% | -0.3078 | -29.44% |
| IC_WEIGHTED_COMPOSITE | 0.0670 | 0.4900 | 2.8880 | 0.0387 | 2.70% | 0.1364 | -26.49% |

These are `DIAGNOSTIC_ONLY` synthetic values, not profitability evidence.

### Limitations

Static membership, synthetic prices, companion synthetic OHLCV, typical-price
VWAP proxy, in-sample IC weights, idealized close-reset execution, and no
dataset review. `alpha_019` has a longer effective warm-up than the shared
25-row evaluation start. This is not a 14-trial run.

### Next Action

Keep as a DIAGNOSTIC_ONLY implemented-alpha and composite wiring check. Do not
reopen identity, D8, A2, or formal interpretation from this result.

## 20260919-004-multifactor-diagnostic-mvp

### Experiment ID

`20260919-004-multifactor-diagnostic-mvp`

### Date

`2026-09-19`

### Hypothesis

The 38 implemented WorldQuant price-volume alphas, plus equal-weighted and
in-sample IC-weighted z-score composites, can be wired through the committed
50-stock diagnostic cohort with monthly Rank IC, ICIR, Newey-West, DSR
(`n_trials=40`), and 5 bps monthly backtests.

### Data Source

Synthetic local generator from
`tests/fixtures/walking_skeleton/diagnostic_cohort_v1.json`. Close prices use
seed `20260919`. Companion open, low, and volume use `seed + 1`. High is an
additional `seed + 1` draw after those panels. VWAP is typical price
`(high + low + close) / 3`. No vendor, private path, or real market data.

### Dataset Review Decision

`dataset_manifest_reviewed = false`. `formal_interpretation_eligible = false`.
Evidence ceiling `DIAGNOSTIC_ONLY`. No dataset-review decision ID.

### Universe

Static 50-name diagnostic slots `D50_01` through `D50_50`. Survivorship-biased
by construction. Not point-in-time membership evidence.

### Date Range

Source `2021-01-04` through `2023-11-27`. Evaluation `2021-02-08` through
`2023-11-27` after 25-row alpha warm-up. `alpha_019` and `alpha_039` use a
250-row return sum, `alpha_024` uses a 200-row mean-drift window, and
`alpha_032` uses a 230-row VWAP correlation, so their early monthly IC cells
stay missing until those windows are full.

### Features / Factors

Implemented alphas `ALPHA_001` through `ALPHA_101` listed in
`research/multifactor_diagnostic_mvp.py` `ALPHA_IDS`, plus
`EQUAL_WEIGHTED_COMPOSITE` and `IC_WEIGHTED_COMPOSITE`. Signal lag: 1 observed
source row. Forward IC labels start at the execution close. IC-weighted
composite uses in-sample mean monthly Rank IC of the 38 alphas.

### Parameters

Monthly last-row rebalance (`ME`), long-only top 5 equal-weight names,
`signal_lag_periods=1`, `n_trials=40` for DSR with Euler-Mascheroni mix.

### Benchmark

Synthetic equal-weight 50-name diagnostic-cohort price path. Cost-free.

### Transaction Costs

`0.00` bps. Zero-cost remainder is diagnostic.

### Slippage Model

Fixed `5.00` bps on drift-adjusted target-weight turnover.

### Metrics

Recorded in `reports/multifactor_diagnostic_mvp.md` and
`reports/experiment_logs/multifactor_diagnostic_mvp.json`. All 38 alphas and
both composites are retained, including negative mean IC. Official 4-decimal
rows:

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | -0.0083 | -0.0541 | -0.3019 | 0.0177 | -0.40% | 0.0505 | -23.34% |
| ALPHA_002 | -0.0028 | -0.0189 | -0.1163 | 0.0020 | -15.29% | -0.4035 | -27.88% |
| ALPHA_003 | -0.0383 | -0.2358 | -1.1060 | 0.2043 | 31.28% | 0.8040 | -16.56% |
| ALPHA_004 | -0.0181 | -0.1301 | -1.0225 | 0.0439 | 8.41% | 0.2839 | -23.66% |
| ALPHA_005 | -0.0254 | -0.1645 | -0.8436 | 0.0773 | 15.55% | 0.4512 | -23.13% |
| ALPHA_006 | -0.0036 | -0.0292 | -0.1833 | 0.0274 | 3.59% | 0.1589 | -14.41% |
| ALPHA_007 | 0.0106 | 0.0984 | 0.5324 | 0.0015 | -17.35% | -0.4558 | -25.97% |
| ALPHA_008 | -0.0291 | -0.2172 | -1.3083 | 0.0452 | 8.87% | 0.2920 | -23.31% |
| ALPHA_009 | -0.0194 | -0.1182 | -0.7920 | 0.0701 | 13.74% | 0.4208 | -24.30% |
| ALPHA_010 | -0.0182 | -0.1064 | -0.7266 | 0.1061 | 19.43% | 0.5551 | -23.54% |
| ALPHA_012 | -0.0069 | -0.0548 | -0.3888 | 0.1195 | 21.76% | 0.5961 | -18.88% |
| ALPHA_013 | 0.0345 | 0.2377 | 1.6730 | 0.0280 | 3.69% | 0.1639 | -24.01% |
| ALPHA_014 | -0.0063 | -0.0432 | -0.2736 | 0.0150 | -2.02% | 0.0119 | -23.78% |
| ALPHA_017 | -0.0478 | -0.4175 | -2.9894 | 0.2443 | 34.36% | 0.8826 | -14.41% |
| ALPHA_018 | -0.0324 | -0.2301 | -2.2995 | 0.0145 | -2.16% | 0.0032 | -20.67% |
| ALPHA_019 | -0.0974 | -0.6117 | -2.9056 | 0.0062 | -6.88% | -0.1828 | -14.82% |
| ALPHA_020 | -0.0315 | -0.2621 | -1.6914 | 0.0557 | 11.10% | 0.3520 | -20.93% |
| ALPHA_021 | -0.0007 | -0.0049 | -0.0286 | 0.0299 | 4.43% | 0.1810 | -22.81% |
| ALPHA_023 | -0.0152 | -0.0973 | -0.6273 | 0.1754 | 28.34% | 0.7390 | -17.50% |
| ALPHA_024 | -0.0023 | -0.0137 | -0.0780 | 0.0030 | -11.63% | -0.3295 | -24.82% |
| ALPHA_026 | 0.0420 | 0.2824 | 1.6224 | 0.1027 | 19.19% | 0.5438 | -19.93% |
| ALPHA_028 | 0.0097 | 0.0693 | 0.3415 | 0.0401 | 7.55% | 0.2593 | -30.66% |
| ALPHA_030 | -0.0112 | -0.0723 | -0.4867 | 0.0687 | 13.78% | 0.4145 | -19.70% |
| ALPHA_032 | -0.0260 | -0.1733 | -0.8504 | 0.0084 | -4.97% | -0.1185 | -22.85% |
| ALPHA_033 | -0.0308 | -0.2051 | -2.0262 | 0.1230 | 22.10% | 0.6057 | -17.06% |
| ALPHA_034 | 0.0010 | 0.0068 | 0.0458 | 0.0990 | 19.40% | 0.5305 | -13.73% |
| ALPHA_035 | -0.0028 | -0.0186 | -0.1299 | 0.0063 | -8.62% | -0.1802 | -19.08% |
| ALPHA_038 | -0.0174 | -0.1119 | -0.7676 | 0.0281 | 3.77% | 0.1647 | -20.58% |
| ALPHA_039 | -0.0661 | -0.4513 | -1.9483 | 0.0078 | -5.51% | -0.1338 | -17.86% |
| ALPHA_043 | 0.0338 | 0.2310 | 1.6466 | 0.0004 | -24.62% | -0.7007 | -32.69% |
| ALPHA_045 | -0.0006 | -0.0044 | -0.0261 | 0.1768 | 27.64% | 0.7443 | -15.48% |
| ALPHA_049 | -0.0232 | -0.1703 | -1.3605 | 0.0602 | 12.17% | 0.3746 | -24.35% |
| ALPHA_051 | 0.0025 | 0.0198 | 0.1748 | 0.1011 | 18.95% | 0.5392 | -20.51% |
| ALPHA_053 | -0.0096 | -0.0809 | -0.6399 | 0.0119 | -3.94% | -0.0416 | -26.81% |
| ALPHA_054 | 0.0048 | 0.0346 | 0.3353 | 0.0231 | 1.93% | 0.1156 | -25.60% |
| ALPHA_055 | -0.0017 | -0.0114 | -0.0662 | 0.0134 | -2.63% | -0.0151 | -24.90% |
| ALPHA_060 | 0.0103 | 0.0727 | 0.6986 | 0.0145 | -1.97% | 0.0042 | -23.44% |
| ALPHA_101 | 0.0181 | 0.1150 | 1.0473 | 0.0193 | 0.28% | 0.0709 | -29.74% |
| EQUAL_WEIGHTED_COMPOSITE | -0.0216 | -0.1387 | -1.0344 | 0.0070 | -7.98% | -0.1587 | -25.20% |
| IC_WEIGHTED_COMPOSITE | 0.0718 | 0.5086 | 3.0392 | 0.1003 | 18.39% | 0.5368 | -23.22% |

These are `DIAGNOSTIC_ONLY` synthetic values, not profitability evidence.

### Limitations

Static membership, synthetic prices, companion synthetic OHLCV, typical-price
VWAP proxy, in-sample IC weights, idealized close-reset execution, and no
dataset review. `alpha_019`, `alpha_024`, `alpha_032`, and `alpha_039` have a
longer effective warm-up than the shared 25-row evaluation start. This is not
a 14-trial run.

### Next Action

Keep as a DIAGNOSTIC_ONLY implemented-alpha and composite wiring check. Do not
reopen identity, D8, A2, or formal interpretation from this result.

## 20260919-005-multifactor-diagnostic-mvp

### Experiment ID

`20260919-005-multifactor-diagnostic-mvp`

### Date

`2026-09-19`

### Hypothesis

The 52 implemented WorldQuant price-volume alphas, plus equal-weighted and
in-sample IC-weighted z-score composites, can be wired through the committed
50-stock diagnostic cohort with monthly Rank IC, ICIR, Newey-West, DSR
(`n_trials=54`), and 5 bps monthly backtests.

### Data Source

Synthetic local generator from
`tests/fixtures/walking_skeleton/diagnostic_cohort_v1.json`. Close prices use
seed `20260919`. Companion open, low, and volume use `seed + 1`. High is an
additional `seed + 1` draw after those panels. VWAP is typical price
`(high + low + close) / 3`. No vendor, private path, or real market data.

### Dataset Review Decision

`dataset_manifest_reviewed = false`. `formal_interpretation_eligible = false`.
Evidence ceiling `DIAGNOSTIC_ONLY`. No dataset-review decision ID.

### Universe

Static 50-name diagnostic slots `D50_01` through `D50_50`. Survivorship-biased
by construction. Not point-in-time membership evidence.

### Date Range

Source `2021-01-04` through `2023-11-27`. Evaluation `2021-02-08` through
`2023-11-27` after 25-row alpha warm-up. `alpha_019` and `alpha_039` use a
250-row return sum, `alpha_024` uses a 200-row mean-drift window, `alpha_032`
uses a 230-row VWAP correlation, `alpha_036` uses a 200-row close mean,
`alpha_037` uses a 200-row delayed-spread correlation, and `alpha_052` uses a
240-row return sum, so their early monthly IC cells stay missing until those
windows are full.

### Features / Factors

Implemented alphas `ALPHA_001` through `ALPHA_101` listed in
`research/multifactor_diagnostic_mvp.py` `ALPHA_IDS`, plus
`EQUAL_WEIGHTED_COMPOSITE` and `IC_WEIGHTED_COMPOSITE`. Signal lag: 1 observed
source row. Forward IC labels start at the execution close. IC-weighted
composite uses in-sample mean monthly Rank IC of the 52 alphas.

### Parameters

Monthly last-row rebalance (`ME`), long-only top 5 equal-weight names,
`signal_lag_periods=1`, `n_trials=54` for DSR with Euler-Mascheroni mix.

### Benchmark

Synthetic equal-weight 50-name diagnostic-cohort price path. Cost-free.

### Transaction Costs

`0.00` bps. Zero-cost remainder is diagnostic.

### Slippage Model

Fixed `5.00` bps on drift-adjusted target-weight turnover.

### Metrics

Recorded in `reports/multifactor_diagnostic_mvp.md` and
`reports/experiment_logs/multifactor_diagnostic_mvp.json`. All 52 alphas and
both composites are retained, including negative mean IC. Official 4-decimal
rows:

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | -0.0083 | -0.0541 | -0.3019 | 0.0132 | -0.40% | 0.0505 | -23.34% |
| ALPHA_002 | -0.0028 | -0.0189 | -0.1163 | 0.0014 | -15.29% | -0.4035 | -27.88% |
| ALPHA_003 | -0.0383 | -0.2358 | -1.1060 | 0.1729 | 31.28% | 0.8040 | -16.56% |
| ALPHA_004 | -0.0181 | -0.1301 | -1.0225 | 0.0342 | 8.41% | 0.2839 | -23.66% |
| ALPHA_005 | -0.0254 | -0.1645 | -0.8436 | 0.0618 | 15.55% | 0.4512 | -23.13% |
| ALPHA_006 | -0.0036 | -0.0292 | -0.1833 | 0.0209 | 3.59% | 0.1589 | -14.41% |
| ALPHA_007 | 0.0106 | 0.0984 | 0.5324 | 0.0010 | -17.35% | -0.4558 | -25.97% |
| ALPHA_008 | -0.0291 | -0.2172 | -1.3083 | 0.0352 | 8.87% | 0.2920 | -23.31% |
| ALPHA_009 | -0.0194 | -0.1182 | -0.7920 | 0.0558 | 13.74% | 0.4208 | -24.30% |
| ALPHA_010 | -0.0182 | -0.1064 | -0.7266 | 0.0863 | 19.43% | 0.5551 | -23.54% |
| ALPHA_012 | -0.0069 | -0.0548 | -0.3888 | 0.0979 | 21.76% | 0.5961 | -18.88% |
| ALPHA_013 | 0.0345 | 0.2377 | 1.6730 | 0.0213 | 3.69% | 0.1639 | -24.01% |
| ALPHA_014 | -0.0063 | -0.0432 | -0.2736 | 0.0111 | -2.02% | 0.0119 | -23.78% |
| ALPHA_015 | 0.0076 | 0.0388 | 0.2525 | 0.0317 | 7.65% | 0.2641 | -24.26% |
| ALPHA_016 | 0.0483 | 0.3418 | 2.4570 | 0.0096 | -3.09% | -0.0222 | -22.16% |
| ALPHA_017 | -0.0478 | -0.4175 | -2.9894 | 0.2093 | 34.36% | 0.8826 | -14.41% |
| ALPHA_018 | -0.0324 | -0.2301 | -2.2995 | 0.0107 | -2.16% | 0.0032 | -20.67% |
| ALPHA_019 | -0.0974 | -0.6117 | -2.9056 | 0.0044 | -6.88% | -0.1828 | -14.82% |
| ALPHA_020 | -0.0315 | -0.2621 | -1.6914 | 0.0438 | 11.10% | 0.3520 | -20.93% |
| ALPHA_021 | -0.0007 | -0.0049 | -0.0286 | 0.0229 | 4.43% | 0.1810 | -22.81% |
| ALPHA_022 | 0.0377 | 0.2971 | 1.9156 | 0.2634 | 40.80% | 0.9852 | -12.59% |
| ALPHA_023 | -0.0152 | -0.0973 | -0.6273 | 0.1471 | 28.34% | 0.7390 | -17.50% |
| ALPHA_024 | -0.0023 | -0.0137 | -0.0780 | 0.0021 | -11.63% | -0.3295 | -24.82% |
| ALPHA_025 | -0.0343 | -0.2524 | -2.1566 | 0.0286 | 6.50% | 0.2379 | -22.81% |
| ALPHA_026 | 0.0420 | 0.2824 | 1.6224 | 0.0834 | 19.19% | 0.5438 | -19.93% |
| ALPHA_028 | 0.0097 | 0.0693 | 0.3415 | 0.0310 | 7.55% | 0.2593 | -30.66% |
| ALPHA_030 | -0.0112 | -0.0723 | -0.4867 | 0.0547 | 13.78% | 0.4145 | -19.70% |
| ALPHA_031 | -0.0105 | -0.0736 | -0.4883 | 0.0524 | 13.34% | 0.4025 | -14.94% |
| ALPHA_032 | -0.0260 | -0.1733 | -0.8504 | 0.0061 | -4.97% | -0.1185 | -22.85% |
| ALPHA_033 | -0.0308 | -0.2051 | -2.0262 | 0.1010 | 22.10% | 0.6057 | -17.06% |
| ALPHA_034 | 0.0010 | 0.0068 | 0.0458 | 0.0802 | 19.40% | 0.5305 | -13.73% |
| ALPHA_035 | -0.0028 | -0.0186 | -0.1299 | 0.0045 | -8.62% | -0.1802 | -19.08% |
| ALPHA_036 | -0.0415 | -0.3506 | -1.6099 | 0.0059 | -5.68% | -0.1249 | -20.28% |
| ALPHA_037 | -0.0212 | -0.1205 | -0.8161 | 0.0105 | -1.80% | -0.0005 | -19.20% |
| ALPHA_038 | -0.0174 | -0.1119 | -0.7676 | 0.0214 | 3.77% | 0.1647 | -20.58% |
| ALPHA_039 | -0.0661 | -0.4513 | -1.9483 | 0.0057 | -5.51% | -0.1338 | -17.86% |
| ALPHA_040 | 0.0107 | 0.0731 | 0.4754 | 0.0333 | 8.01% | 0.2775 | -16.59% |
| ALPHA_041 | -0.0137 | -0.0933 | -0.9037 | 0.0192 | 2.80% | 0.1387 | -23.42% |
| ALPHA_042 | 0.0067 | 0.0418 | 0.3450 | 0.0373 | 9.44% | 0.3074 | -20.44% |
| ALPHA_043 | 0.0338 | 0.2310 | 1.6466 | 0.0002 | -24.62% | -0.7007 | -32.69% |
| ALPHA_044 | 0.0456 | 0.2998 | 1.7685 | 0.0100 | -2.68% | -0.0112 | -20.08% |
| ALPHA_045 | -0.0006 | -0.0044 | -0.0261 | 0.1483 | 27.64% | 0.7443 | -15.48% |
| ALPHA_046 | -0.0187 | -0.1143 | -0.6428 | 0.0129 | -0.58% | 0.0449 | -19.16% |
| ALPHA_049 | -0.0232 | -0.1703 | -1.3605 | 0.0476 | 12.17% | 0.3746 | -24.35% |
| ALPHA_050 | -0.0171 | -0.1065 | -0.5499 | 0.0107 | -2.13% | 0.0030 | -21.84% |
| ALPHA_051 | 0.0025 | 0.0198 | 0.1748 | 0.0821 | 18.95% | 0.5392 | -20.51% |
| ALPHA_052 | -0.0430 | -0.2931 | -1.4077 | 0.0115 | -1.11% | 0.0181 | -21.46% |
| ALPHA_053 | -0.0096 | -0.0809 | -0.6399 | 0.0087 | -3.94% | -0.0416 | -26.81% |
| ALPHA_054 | 0.0048 | 0.0346 | 0.3353 | 0.0175 | 1.93% | 0.1156 | -25.60% |
| ALPHA_055 | -0.0017 | -0.0114 | -0.0662 | 0.0099 | -2.63% | -0.0151 | -24.90% |
| ALPHA_060 | 0.0103 | 0.0727 | 0.6986 | 0.0108 | -1.97% | 0.0042 | -23.44% |
| ALPHA_101 | 0.0181 | 0.1150 | 1.0473 | 0.0144 | 0.28% | 0.0709 | -29.74% |
| EQUAL_WEIGHTED_COMPOSITE | -0.0138 | -0.0890 | -0.7149 | 0.0089 | -3.65% | -0.0388 | -23.39% |
| IC_WEIGHTED_COMPOSITE | 0.0826 | 0.6074 | 3.5590 | 0.0789 | 18.26% | 0.5280 | -23.03% |

These are `DIAGNOSTIC_ONLY` synthetic values, not profitability evidence.

### Limitations

Static membership, synthetic prices, companion synthetic OHLCV, typical-price
VWAP proxy, in-sample IC weights, idealized close-reset execution, and no
dataset review. `alpha_019`, `alpha_024`, `alpha_032`, `alpha_036`,
`alpha_037`, `alpha_039`, and `alpha_052` have a longer effective warm-up
than the shared 25-row evaluation start. This is not a 14-trial run.

### Next Action

Keep as a DIAGNOSTIC_ONLY implemented-alpha and composite wiring check. Do not
reopen identity, D8, A2, or formal interpretation from this result.

## 20260919-006-walk-forward-composite-weights

### Experiment ID

`20260919-006-walk-forward-composite-weights`

### Date

`2026-09-19`

### Hypothesis

Causal walk-forward ICIR and correlation-discounted weights at monthly
rebalance dates, plus an unfilled trailing volatility proxy, can replace
full-sample static composite weights on the same 50-stock diagnostic cohort
without changing individual-alpha diagnostics.

### Data Source

Synthetic local generator from
`tests/fixtures/walking_skeleton/diagnostic_cohort_v1.json`. Close prices use
seed `20260919`. Companion open, low, and volume use `seed + 1`. High is an
additional `seed + 1` draw after those panels. VWAP is typical price
`(high + low + close) / 3`. No vendor, private path, or real market data.

### Dataset Review Decision

`dataset_manifest_reviewed = false`. `formal_interpretation_eligible = false`.
Evidence ceiling `DIAGNOSTIC_ONLY`. No dataset-review decision ID.

### Universe

Static 50-name diagnostic slots `D50_01` through `D50_50`. Survivorship-biased
by construction. Not point-in-time membership evidence.

### Date Range

Source `2021-01-04` through `2023-11-27`. Evaluation `2021-02-08` through
`2023-11-27` after 25-row alpha warm-up.

### Features / Factors

Same 52 implemented alphas as `20260919-005-multifactor-diagnostic-mvp`, plus
`EQUAL_WEIGHTED_COMPOSITE`, in-sample `IC_WEIGHTED_COMPOSITE`, walk-forward
`ICIR_WEIGHTED_COMPOSITE`, walk-forward `CORRELATION_DISCOUNTED_COMPOSITE`,
`ALPHA_PRODUCT_INTERACTION`, `CONDITIONAL_RANK_INTERACTION`, and
`NEUTRALIZED_IC_COMPOSITE`. On each monthly rebalance date t, ICIR and
expanding-window mean IC use monthly Rank ICs strictly before t. Correlation
uses trailing factor values through t. Volatility proxy is a 20-day rolling
return standard deviation with `min_periods=5` and leading NaNs left in place.

### Parameters

Monthly last-row rebalance (`ME`), long-only top 5 equal-weight names,
`signal_lag_periods=1`, `n_trials=59` for DSR with Euler-Mascheroni mix,
`ridge_alpha=0.1`, ICIR `min_ic_periods=5`.

### Benchmark

Synthetic equal-weight 50-name diagnostic-cohort price path. Cost-free.

### Transaction Costs

`0.00` bps. Zero-cost remainder is diagnostic.

### Slippage Model

Fixed `5.00` bps on drift-adjusted target-weight turnover.

### Metrics

Recorded in `reports/multifactor_diagnostic_mvp.md` and
`reports/experiment_logs/multifactor_diagnostic_mvp.json`. Individual alpha,
equal-weighted, in-sample IC-weighted, interaction, and neutralized-IC rows
match `20260919-005` / the PR #234 official pins. Walk-forward composites:

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ICIR_WEIGHTED_COMPOSITE | -0.0131 | -0.0910 | -0.5403 | 0.0011 | -14.44% | -0.4302 | -25.03% |
| CORRELATION_DISCOUNTED_COMPOSITE | 0.0028 | 0.0190 | 0.1221 | 0.0118 | -0.56% | 0.0435 | -28.79% |

These walk-forward composites are weaker than the previous full-sample static
versions. Weak and negative diagnostics are retained. Values are
`DIAGNOSTIC_ONLY` synthetic diagnostics, not profitability evidence.

### Limitations

Static membership, synthetic prices, companion synthetic OHLCV, typical-price
VWAP proxy, in-sample IC-weighted composite, idealized close-reset execution,
and no dataset review. Walk-forward ICIR requires five prior monthly ICs per
factor before that factor receives nonzero weight. This is not a 14-trial run.

### Next Action

Keep as a DIAGNOSTIC_ONLY implemented-alpha and composite wiring check. Do not
reopen identity, D8, A2, or formal interpretation from this result.

## Local CSV Experiment Records

Any future run that uses user-provided local CSV data must add or prepare a full
entry in this file before results are interpreted. The entry is required for
loader smoke tests, feature audits, backtest diagnostics, parameter studies, and
full experiment candidates.

This requirement does not authorize data downloads, remote data access, vendor
APIs, credentials, live trading, brokerage integration, order execution, or
profitability claims. Local CSV runs remain research-only and must pass the
real-data readiness audit before being treated as diagnostic evidence. A
completed entry does not by itself satisfy the point-in-time methodology,
purged-split, timing, all-trial ledger, statistical, privacy, cost, or holdout
gates required for formal evidence.

At minimum, a local CSV experiment record must include:

- Private-manifest ID and redacted public logical ID for each input. Tracked
  records must not contain private absolute paths.
- Private evidence that records the hash algorithm, actual raw-byte and
  ordered-manifest hashes, immutable dataset version, retrieval timestamp,
  extraction scope, transformation lineage, and any revision/supersession
  relationship, plus `canonicalization_id`, `environment_id`,
  `environment_lock_sha256`, interpreter/platform, locale, process timezone,
  and parsing/calendar/transformation library versions. Actual hashes remain
  in the private manifest; this tracked record contains only a
  publication-approved hash or redacted private-evidence reference and
  verification state.
- Redacted license-decision ID/evidence reference and review state, permitted
  research use, redistribution restriction, and public/private classification.
  License documents, contract/account IDs, and restricted entitlement metadata
  remain private. An asserted license is not an accepted entitlement decision.
- Schema for each file: wide price, long price, benchmark, universe membership,
  factor panel, metadata, or another reviewed schema.
- Validation summary: date parsing, sorted dates, duplicate checks, numeric
  parsing, missing-value counts, non-positive price handling, and whether any
  forward-fill or backward-fill was used.
- Data provenance: source name as provided by the user, export type, known
  manual edits, and known missing, stale, revised, or excluded observations.
- Price adjustment policy: adjusted close, raw close, split-adjusted,
  dividend-adjusted, total-return adjusted, or unknown, including benchmark
  adjustment compatibility.
- Universe rules: starting universe, point-in-time membership status, liquidity
  filters, price filters, minimum history, exclusions, permanent/listing/issuer
  identifiers, ticker-alias intervals, membership effective/known times,
  delistings, mergers, corporate actions, and survivorship-bias caveats.
- Field and calendar policy: source field dictionary/version, units/currency,
  field availability and revision timestamps, exchange calendar,
  session/timezone conventions, typed missingness, and stale/zero-volume rules.
- Feature and signal timing: formulas, lookbacks, skipped windows, latest data
  timestamp available for each signal date, conservative `known_at` with
  `known_at <= decision_time`, signal lag, and execution timing.
- Sample splits and parameter policy: in-sample, validation, test or holdout
  periods, warm-up exclusion, fixed parameters or grid, and whether choices were
  made before seeing results.
- Benchmark: symbol or local benchmark file, date range, price or return field,
  version, role, missing dates, adjustment convention, availability, and
  alignment to strategy dates; include risk-free source, version, tenor,
  units, day-count, availability, and missing-date policy when applicable.
- Costs, slippage, turnover, rebalance frequency, and execution assumptions,
  including whether zero-cost or zero-slippage settings are diagnostic only.
- Metric names, computation status, redacted private-evidence references, and
  limitations, including missing-data limitations, benchmark mismatch,
  corporate-action uncertainty, vendor differences, stale prices, delisting
  risk, and any unresolved low issues from the readiness audit. Private
  performance values remain outside tracked records unless a separate
  publication decision explicitly approves named aggregate fields.
- Failure modes and next action, including weak, failed, ambiguous, or stopped
  cases. Do not report only the best parameter result.
- Holdout-exposure classification and append-only access-record identifier.
  The historically examined 2025-05-01 through 2026-05-31 interval is
  `historical_evaluation`, not a pristine holdout.
- When formal interpretation is proposed, the immutable dataset-review
  decision ID, exact reviewed manifest/projection identities,
  reviewer-authority reference, scope, timestamp, and finding dispositions.
  This must be a non-self-issued exact-version dataset-review decision; the
  tracked record cannot grant a gate or self-certify its own manifest.
- For diagnostic scope without a dataset-review decision, do not fabricate a
  decision ID: record `dataset_manifest_reviewed = false`,
  `formal_interpretation_eligible = false`, the diagnostic limitation, and
  omit the formal-only decision identity, reviewer, and finding fields.
  Protected-sample access-record and exposure-decision IDs remain
  scope-applicable and are not formal-only.

If required provenance, adjustment policy, date alignment, benchmark coverage,
sample splits, cost/slippage assumptions, license evidence, verified private
hash evidence,
identifier history, field availability, calendar policy, privacy projection,
canonicalization/environment identity, protected-sample classification, or
missing-data evidence is absent, stop before interpreting even diagnostic
metrics. Synthetic JSON sidecar logs are not substitutes for local CSV
experiment records, and neither record type is the future immutable all-trial
ledger.

## Template

### Experiment ID

`YYYYMMDD-NNN-short-name`

### Date

`YYYY-MM-DD`

### Hypothesis

What should be true if this experiment is useful?

### Data Source

Dataset name, vendor, private-manifest ID, redacted public logical ID, immutable
version, hash-verification state plus a publication-approved hash or redacted
private-evidence reference, retrieval/extraction metadata, lineage, license
state, `canonicalization_id`, `environment_id`, `environment_lock_sha256`,
privacy class, and any known limitations. Do not record a private absolute path
or an unapproved digest.

### Dataset Review Decision

When formal interpretation is proposed, record the immutable decision ID, exact
reviewed manifest/projection identities, safe reviewer-authority reference,
review time, declared scope, decision, finding dispositions, contract identity,
and redacted evidence reference. This must be a non-self-issued exact-version
dataset-review decision. The manifest producer or this template cannot grant
`dataset_manifest_reviewed`.

For diagnostic scope without a dataset-review decision, do not fabricate a
decision ID. Record `dataset_manifest_reviewed = false`,
`formal_interpretation_eligible = false`, the diagnostic limitation, and omit
the formal-only decision identity, reviewer, and finding fields. Continue to
record every scope-applicable protected-sample access-record and
exposure-decision ID under Sample Split.

### Universe

Universe definition, permanent/listing identifiers, point-in-time membership
and known-at times, liquidity screen, exclusions, corporate actions,
delistings, and survivorship-bias notes.

### Date Range

Start date, end date, and any excluded dates.

### Features / Factors

Feature names, formulas, lookback windows, lags, and data availability assumptions.

### Parameters

All strategy, backtest, ranking, selection, and risk-control parameters.

### Benchmark

Benchmark identity/version, role, availability/calendar/alignment, and return
calculation assumptions. Include the risk-free source and convention when
risk-adjusted metrics are claimed.

### Transaction Costs

Cost model, basis points, minimum commissions, and any simplifications.

### Slippage Model

Slippage model, basis points or volume-aware rule, and limitations.

### Rebalance Frequency

Daily, weekly, monthly, or custom schedule. State exact execution timing.

### Performance Metrics

For synthetic or explicitly publication-approved evidence, record the named
total-return, annualized-return, volatility, Sharpe-style,
benchmark-relative, or other approved fields. For private evidence, record
only metric names, computation status, and redacted private-evidence IDs unless
a separate publication decision approves the named aggregate values.

### Turnover

Record the method and approved evidence fields. Private turnover values and
distributions remain external unless separately approved for publication.

### Max Drawdown

Record the method and approved evidence fields. Private drawdown values, dates,
and benchmark comparison remain external unless separately approved for
publication.

### Sample Split

In-sample, validation, and test period definitions, protected-sample
classification, append-only access-record identifier, and exposure-decision
ID. Missing, backfilled, uncertain, outcome-reconstructible, or overlapping
access downgrades the sample monotonically; the 2025-05-01 through 2026-05-31
interval remains `historical_evaluation` and cannot be upgraded.

### Result Summary

Concise summary of what happened. Include weak, failed, or ambiguous results.
For private evidence, do not reveal direction, magnitude, rank, or metric
value; record only status and a redacted private-evidence reference unless
publication is separately approved.

### Failure Modes

Known problems, possible leakage risks, sensitivity issues, data quality concerns, overfitting risks, or execution assumptions that may be unrealistic.

### Next Action

Keep, reject, revise, test further, add data, improve validation, or stop.
