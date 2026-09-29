# Milestone 5 Step 2: Public Factor Baseline (Equal Weight vs Inverse Volatility)

Run 2026-09-29T00:39:22Z from code commit `272109f7c80985ed722450f68953ce263bc97e29` (tracked changes at run time: False).

## Read This First

- **Evidence ceiling: DIAGNOSTIC_ONLY.** These are diagnostics on public long-short factor series. They support no profitability, ranking, or promotion claim.
- **Long-short and gross of internal costs.** Each factor return is a published zero-investment long-minus-short return. It excludes the factor's own trading costs and short-leg borrow costs. Only the allocator's switch cost (20 bp primary, 50 bp sensitivity, on monthly weight turnover) is charged.
- **Small caps included.** JKP capped value-weight factors and the French factors hold small and micro caps, which a long-only large-cap book cannot trade at these returns.
- **Hindsight in the factor list.** The JKP list was assembled after the underlying papers; months before each publication were in the original authors' samples. The post-publication split below is the declared check.
- **Prior exposures (R9).** Before this declaration the coordinator saw two diagnostics on overlapping months: the 2026-09-28 audit scratch run on 7 French factors (equal weight Sharpe 0.83, inverse volatility 0.83) and the 2026-09-28 vision probe on JKP 153 factors (inverse volatility Sharpe 0.94 vs 0.72 for equal weight). Every result of the earlier step 2 runs under the v1 timing (commit `58f398c`) and both round 1 review diagnostics were also seen before amendment 2; they stay visible. This run re-examines comparisons already seen and supports no confirmatory claim.
- **Trial family.** `docs/preregistrations/m5_trial_family_v1.json`, SHA-256 `a99a862c651fd4e52e9904e62c8dfc539b85f57f1910d2a17b9bd03a6723417a`, verified equal to its committed HEAD version before any data was read; amendments `docs/preregistrations/m5_trial_family_v1_amendment_1.json` (SHA-256 `b3992b3282910a5bf056d3d6061e4456e6b4d4a923f4e6d3493898a445b90751`); `docs/preregistrations/m5_trial_family_v1_amendment_2.json` (SHA-256 `59461b150a957959f0fc9ac36aef9889168d6924f17bc33c3f15dab25eae72f1`), verified the same way.
- **Timing.** `after_month_end_signal_next_month_end_execution` (amendment 2): signal month t-2 (feature observation end: the close of the last trading day of month t-2); execution at the close of the last trading day of month t-1; return month t (close of month t-1 to close of month t); switch cost recorded at the execution close and deducted from the month-t return. A missing return for a held factor refuses the run.

## Result

**Baseline product: R1** (inverse volatility). 8 of 8 declared conditions hold on jkp_factors_153 (R1 drawdown magnitude at most R0's and R1 Sharpe at least R0's, in both halves, at 20 and 50 bp). The S2 q-values are reported beside the decision and do not change it.

Full window at 20 bp on jkp_factors_153: annualized mean net return R0 2.57% and R1 2.27%; volatility R0 3.28% and R1 2.15%; maximum drawdown R0 -13.97% and R1 -7.27%. The S2 test of the mean monthly difference R1 minus R0 has HAC p 0.1179 and BY q 0.3242.

## Data Manifest

| Source | Rows | First | Last | SHA-256 (prefix) | Retrieved (UTC) |
| --- | ---: | --- | --- | --- | --- |
| jkp_cluster_labels | 153 | - | - | `22c7fdd214218d12` | 2026-09-28T23:39:11Z |
| jkp_factor_details | 153 | - | - | `4c579e4dcb93eed0` | 2026-09-28T23:39:11Z |
| jkp_usa_all_factors_monthly_vw_cap | 146457 | 1926-01 | 2025-12 | `f766aa2c7db1f975` | 2026-09-28T23:39:12Z |
| jkp_usa_all_themes_monthly_vw_cap | 14945 | 1926-01 | 2025-12 | `9cf3bfa2a2941846` | 2026-09-28T23:39:13Z |
| french_ff5_2x3_monthly | 758 | 1963-07 | 2026-08 | `36756c5c25596485` | 2026-09-28T23:39:14Z |
| french_momentum_monthly | 1196 | 1927-01 | 2026-08 | `c06d1c2e9a5e4f69` | 2026-09-28T23:39:14Z |
| french_st_reversal_monthly | 1207 | 1926-02 | 2026-08 | `06c0d46d819f51f0` | 2026-09-28T23:39:14Z |
| french_lt_reversal_monthly | 1148 | 1931-01 | 2026-08 | `f4432f4c1dfc32ad` | 2026-09-28T23:39:15Z |
| french_ff3_monthly | 1202 | 1926-07 | 2026-08 | `593f4fbef03181bc` | 2026-09-28T23:39:15Z |
| fred_baa_aaa_monthly | 1292 | 1919-01 | 2026-08 | `7cf737a14461f9e0` | 2026-09-28T23:39:16Z |

Full URLs and hashes: `reports/m5_public_data_manifest.json`. Raw files stay in the gitignored `data/public_cache/`.

Attribution: JKP data by Jensen, Kelly, and Pedersen, jkpfactors.com, CC BY-NC 4.0 (Jensen, Kelly, and Pedersen (2023), Is There a Replication Crisis in Finance?, Journal of Finance, doi 10.1111/jofi.13249). French factors: Kenneth R. French Data Library, copyright Eugene F. Fama and Kenneth R. French. Moody's BAA and AAA yields retrieved from FRED, Federal Reserve Bank of St. Louis (retrieved and hashed for step 3; unused here).

## Decision Conditions (jkp_factors_153)

| Period | Cost | Metric | R0 | R1 | Holds |
| --- | ---: | --- | ---: | ---: | --- |
| 1972-1999 | 20 bp | max_drawdown | -8.57% | -3.69% | yes |
| 1972-1999 | 20 bp | sharpe | 1.224 | 1.653 | yes |
| 1972-1999 | 50 bp | max_drawdown | -8.57% | -3.81% | yes |
| 1972-1999 | 50 bp | sharpe | 1.216 | 1.592 | yes |
| 2000-end | 20 bp | max_drawdown | -9.27% | -7.27% | yes |
| 2000-end | 20 bp | sharpe | 0.610 | 0.736 | yes |
| 2000-end | 50 bp | max_drawdown | -9.27% | -7.42% | yes |
| 2000-end | 50 bp | sharpe | 0.610 | 0.704 | yes |

## S2 Tests (R1 net minus R0 net at 20 bp, full window)

Family S2 has 3 tests; Benjamini-Yekutieli adjustment with family size 3; two-sided Newey-West HAC p-values.

| Test | Status | Months | Mean monthly difference (bp) | HAC t | HAC lags | p | BY q |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| S2.jkp_factors_153 | ok | 648 | -2.51 | -1.56 | 6 | 0.1179 | 0.3242 |
| S2.jkp_themes_13 | ok | 648 | -2.60 | -1.87 | 6 | 0.06196 | 0.3242 |
| S2.french_7 | ok | 656 | -1.00 | -0.75 | 6 | 0.4558 | 0.8356 |

## Universe jkp_factors_153

Evaluated 1972-01 to 2025-12; 153 declared factors; status `completed`.

| Rule | Cost | Period | Months | Ann. mean | Volatility | Sharpe | Max drawdown | Worst 12 months | Avg turnover |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R0 | 20 bp | full | 648 | 2.57% | 3.28% | 0.785 | -13.97% | -11.83% | 0.002 |
| R0 | 20 bp | 1972-1999 | 336 | 2.59% | 2.12% | 1.224 | -8.57% | -6.90% | 0.003 |
| R0 | 20 bp | 2000-end | 312 | 2.55% | 4.18% | 0.610 | -9.27% | -7.74% | 0.000 |
| R0 | 50 bp | full | 648 | 2.57% | 3.28% | 0.783 | -13.97% | -11.83% | 0.002 |
| R0 | 50 bp | 1972-1999 | 336 | 2.58% | 2.12% | 1.216 | -8.57% | -6.90% | 0.003 |
| R0 | 50 bp | 2000-end | 312 | 2.55% | 4.18% | 0.610 | -9.27% | -7.74% | 0.000 |
| R1 | 20 bp | full | 648 | 2.27% | 2.15% | 1.056 | -7.27% | -6.82% | 0.024 |
| R1 | 20 bp | 1972-1999 | 336 | 2.57% | 1.56% | 1.653 | -3.69% | -3.53% | 0.025 |
| R1 | 20 bp | 2000-end | 312 | 1.95% | 2.65% | 0.736 | -7.27% | -6.11% | 0.024 |
| R1 | 50 bp | full | 648 | 2.18% | 2.15% | 1.015 | -7.42% | -6.92% | 0.024 |
| R1 | 50 bp | 1972-1999 | 336 | 2.48% | 1.56% | 1.592 | -3.81% | -3.60% | 0.025 |
| R1 | 50 bp | 2000-end | 312 | 1.86% | 2.65% | 0.704 | -7.42% | -6.21% | 0.024 |

Members per month: min 149, median 153, max 153.

Market excess return (French Mkt-RF, context only, no switch cost):

| Period | Ann. mean | Volatility | Sharpe | Max drawdown | Worst 12 months |
| --- | ---: | ---: | ---: | ---: | ---: |
| full | 7.57% | 15.77% | 0.480 | -54.16% | -45.84% |
| 1972-1999 | 7.77% | 15.84% | 0.491 | -53.10% | -45.84% |
| 2000-end | 7.35% | 15.71% | 0.468 | -54.16% | -43.30% |

Volatility-forecast accuracy (Spearman of sigma_i,t with realized volatility over t..t+11, pooled across factor-months):

| Period | Spearman | Pairs | Excluded: window past last month | Excluded: incomplete window |
| --- | ---: | ---: | ---: | ---: |
| full | 0.595 | 97369 | 1683 | 0 |
| 1972-1999 | 0.592 | 51316 | 0 | 0 |
| 2000-end | 0.604 | 46053 | 1683 | 0 |

Membership and missingness counts (factor-months):

| Period | Declared | In set | Fewer than 24 in t-37..t-2 | Bad data in t-37..t-2 | Both | Typed missing |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| full | 99144 | 99052 | 92 | 0 | 0 | none |
| 1972-1999 | 51408 | 51316 | 92 | 0 | 0 | none |
| 2000-end | 47736 | 47736 | 0 | 0 | 0 | none |

Typed missing factor-months in the lookback-only months 1968-12 to 1971-12: absent 144. An absent month counts against the 24-return condition; a bad-data code excludes every window that contains it. Nothing is filled.

## Universe jkp_themes_13

Evaluated 1972-01 to 2025-12; 13 declared factors; status `completed`.

| Rule | Cost | Period | Months | Ann. mean | Volatility | Sharpe | Max drawdown | Worst 12 months | Avg turnover |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R0 | 20 bp | full | 648 | 2.37% | 2.08% | 1.141 | -5.06% | -4.22% | 0.002 |
| R0 | 20 bp | 1972-1999 | 336 | 2.63% | 1.43% | 1.842 | -2.05% | -1.47% | 0.003 |
| R0 | 20 bp | 2000-end | 312 | 2.09% | 2.60% | 0.804 | -5.06% | -4.22% | 0.000 |
| R0 | 50 bp | full | 648 | 2.36% | 2.08% | 1.138 | -5.06% | -4.22% | 0.002 |
| R0 | 50 bp | 1972-1999 | 336 | 2.62% | 1.43% | 1.832 | -2.05% | -1.47% | 0.003 |
| R0 | 50 bp | 2000-end | 312 | 2.09% | 2.60% | 0.804 | -5.06% | -4.22% | 0.000 |
| R1 | 20 bp | full | 648 | 2.06% | 1.27% | 1.623 | -3.48% | -2.83% | 0.024 |
| R1 | 20 bp | 1972-1999 | 336 | 2.54% | 1.08% | 2.343 | -1.22% | 0.14% | 0.024 |
| R1 | 20 bp | 2000-end | 312 | 1.54% | 1.43% | 1.080 | -3.48% | -2.83% | 0.024 |
| R1 | 50 bp | full | 648 | 1.97% | 1.27% | 1.554 | -3.63% | -2.94% | 0.024 |
| R1 | 50 bp | 1972-1999 | 336 | 2.45% | 1.08% | 2.260 | -1.24% | 0.03% | 0.024 |
| R1 | 50 bp | 2000-end | 312 | 1.46% | 1.43% | 1.020 | -3.63% | -2.94% | 0.024 |

Members per month: min 13, median 13, max 13.

Market excess return (French Mkt-RF, context only, no switch cost):

| Period | Ann. mean | Volatility | Sharpe | Max drawdown | Worst 12 months |
| --- | ---: | ---: | ---: | ---: | ---: |
| full | 7.57% | 15.77% | 0.480 | -54.16% | -45.84% |
| 1972-1999 | 7.77% | 15.84% | 0.491 | -53.10% | -45.84% |
| 2000-end | 7.35% | 15.71% | 0.468 | -54.16% | -43.30% |

Volatility-forecast accuracy (Spearman of sigma_i,t with realized volatility over t..t+11, pooled across factor-months):

| Period | Spearman | Pairs | Excluded: window past last month | Excluded: incomplete window |
| --- | ---: | ---: | ---: | ---: |
| full | 0.689 | 8281 | 143 | 0 |
| 1972-1999 | 0.669 | 4368 | 0 | 0 |
| 2000-end | 0.704 | 3913 | 143 | 0 |

Membership and missingness counts (factor-months):

| Period | Declared | In set | Fewer than 24 in t-37..t-2 | Bad data in t-37..t-2 | Both | Typed missing |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| full | 8424 | 8424 | 0 | 0 | 0 | none |
| 1972-1999 | 4368 | 4368 | 0 | 0 | 0 | none |
| 2000-end | 4056 | 4056 | 0 | 0 | 0 | none |

Typed missing factor-months in the lookback-only months 1968-12 to 1971-12: none. An absent month counts against the 24-return condition; a bad-data code excludes every window that contains it. Nothing is filled.

## Universe french_7

Evaluated 1972-01 to 2026-08; 7 declared factors; status `completed`.

| Rule | Cost | Period | Months | Ann. mean | Volatility | Sharpe | Max drawdown | Worst 12 months | Avg turnover |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R0 | 20 bp | full | 656 | 3.57% | 4.27% | 0.835 | -16.41% | -10.00% | 0.002 |
| R0 | 20 bp | 1972-1999 | 336 | 4.75% | 3.24% | 1.467 | -5.81% | -3.94% | 0.003 |
| R0 | 20 bp | 2000-end | 320 | 2.33% | 5.12% | 0.455 | -16.41% | -10.00% | 0.000 |
| R0 | 50 bp | full | 656 | 3.56% | 4.27% | 0.834 | -16.41% | -10.00% | 0.002 |
| R0 | 50 bp | 1972-1999 | 336 | 4.73% | 3.23% | 1.464 | -5.81% | -3.94% | 0.003 |
| R0 | 50 bp | 2000-end | 320 | 2.33% | 5.12% | 0.455 | -16.41% | -10.00% | 0.000 |
| R1 | 20 bp | full | 656 | 3.45% | 4.12% | 0.835 | -17.05% | -9.50% | 0.023 |
| R1 | 20 bp | 1972-1999 | 336 | 4.27% | 3.14% | 1.360 | -6.83% | -4.82% | 0.024 |
| R1 | 20 bp | 2000-end | 320 | 2.58% | 4.94% | 0.521 | -17.05% | -9.50% | 0.023 |
| R1 | 50 bp | full | 656 | 3.36% | 4.12% | 0.815 | -17.21% | -9.57% | 0.023 |
| R1 | 50 bp | 1972-1999 | 336 | 4.19% | 3.14% | 1.334 | -6.93% | -4.89% | 0.024 |
| R1 | 50 bp | 2000-end | 320 | 2.50% | 4.94% | 0.505 | -17.21% | -9.57% | 0.023 |

Members per month: min 7, median 7, max 7.

Market excess return (French Mkt-RF, context only, no switch cost):

| Period | Ann. mean | Volatility | Sharpe | Max drawdown | Worst 12 months |
| --- | ---: | ---: | ---: | ---: | ---: |
| full | 7.67% | 15.76% | 0.487 | -54.16% | -45.84% |
| 1972-1999 | 7.77% | 15.84% | 0.491 | -53.10% | -45.84% |
| 2000-end | 7.56% | 15.69% | 0.482 | -54.16% | -43.30% |

Volatility-forecast accuracy (Spearman of sigma_i,t with realized volatility over t..t+11, pooled across factor-months):

| Period | Spearman | Pairs | Excluded: window past last month | Excluded: incomplete window |
| --- | ---: | ---: | ---: | ---: |
| full | 0.406 | 4515 | 77 | 0 |
| 1972-1999 | 0.334 | 2352 | 0 | 0 |
| 2000-end | 0.450 | 2163 | 77 | 0 |

Membership and missingness counts (factor-months):

| Period | Declared | In set | Fewer than 24 in t-37..t-2 | Bad data in t-37..t-2 | Both | Typed missing |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| full | 4592 | 4592 | 0 | 0 | 0 | none |
| 1972-1999 | 2352 | 2352 | 0 | 0 | 0 | none |
| 2000-end | 2240 | 2240 | 0 | 0 | 0 | none |

Typed missing factor-months in the lookback-only months 1968-12 to 1971-12: none. An absent month counts against the 24-return condition; a bad-data code excludes every window that contains it. Nothing is filled.

## Post-Publication Split (jkp_factors_153, descriptive)

For month t the set is restricted to factors whose publication year is before the calendar year of the signal month t-2 (amendment 2); R0 and R1 use the same rules and costs in one continuous run from the first month with a non-empty subset (trial amendment 1).

Status `completed`; start month 1974-03.

Members per month: min 1, median 34, max 142. The first half holds few factors (see the subset counts below), so its figures describe a thin and changing set.

Evaluated months with an empty subset: 26 (1972-01 to 1974-02).

| Rule | Cost | Period | Months | Ann. mean | Volatility | Sharpe | Max drawdown | Worst 12 months | Avg turnover |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R0 | 20 bp | full | 622 | 1.11% | 5.96% | 0.186 | -50.88% | -22.14% | 0.015 |
| R0 | 20 bp | 1972-1999 | 310 | -0.16% | 7.41% | -0.021 | -50.88% | -22.14% | 0.022 |
| R0 | 20 bp | 2000-end | 312 | 2.37% | 4.03% | 0.589 | -9.27% | -7.75% | 0.009 |
| R0 | 50 bp | full | 622 | 1.06% | 5.95% | 0.177 | -51.06% | -22.43% | 0.015 |
| R0 | 50 bp | 1972-1999 | 310 | -0.24% | 7.39% | -0.032 | -51.06% | -22.43% | 0.022 |
| R0 | 50 bp | 2000-end | 312 | 2.34% | 4.03% | 0.581 | -9.28% | -7.76% | 0.009 |
| R1 | 20 bp | full | 622 | 0.79% | 5.26% | 0.150 | -50.62% | -21.73% | 0.034 |
| R1 | 20 bp | 1972-1999 | 310 | -0.08% | 7.05% | -0.011 | -50.62% | -21.73% | 0.038 |
| R1 | 20 bp | 2000-end | 312 | 1.65% | 2.41% | 0.686 | -7.46% | -6.32% | 0.031 |
| R1 | 50 bp | full | 622 | 0.67% | 5.25% | 0.127 | -50.81% | -22.03% | 0.034 |
| R1 | 50 bp | 1972-1999 | 310 | -0.21% | 7.03% | -0.030 | -50.81% | -22.03% | 0.038 |
| R1 | 50 bp | 2000-end | 312 | 1.54% | 2.41% | 0.639 | -7.64% | -6.42% | 0.031 |

| Period | In set | In subset | Missing publication year | Published in or after signal year | Empty-subset months |
| --- | ---: | ---: | ---: | ---: | ---: |
| full | 99052 | 35008 | 7128 | 56916 | 26 |
| 1972-1999 | 51316 | 2992 | 3696 | 44628 | 26 |
| 2000-end | 47736 | 32016 | 3432 | 12288 | 0 |

## Limitations

- Diagnostic ceiling: public long-short series, gross of each factor's internal trading and borrow costs, including small caps. The implementable check on the repository's point-in-time S&P 500 books after costs is step 4.
- The comparison of R0 and R1 was already seen in two prior diagnostics on overlapping months; the halves reuse the same history and are not out-of-sample confirmation.
- Monthly observations only: the target executes at the month-end close after the signal month, so one whole month separates signal and execution. A daily execution would need daily factor returns.
- The JKP and French files are revised by their providers; a later download can change results. The manifest pins the SHA-256 of the files used here.
- Target weights are compared without drift adjustment, as declared; the switch cost is a flat rate on weight turnover.
- Only the S2 comparison is tested; halves, the 50 bp level, the market, volatility-forecast accuracy, and the post-publication split are descriptive.
