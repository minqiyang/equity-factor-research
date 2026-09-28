# Milestone 5 Step 2: Public Factor Baseline (Equal Weight vs Inverse Volatility)

Run 2026-09-28T23:41:00Z from code commit `2fd16a86475c634aaf1aab15b1afb448fcb0602f` (tracked changes at run time: False).

## Read This First

- **Evidence ceiling: DIAGNOSTIC_ONLY.** These are diagnostics on public long-short factor series. They support no profitability, ranking, or promotion claim.
- **Long-short and gross of internal costs.** Each factor return is a published zero-investment long-minus-short return. It excludes the factor's own trading costs and short-leg borrow costs. Only the allocator's switch cost (20 bp primary, 50 bp sensitivity, on monthly weight turnover) is charged.
- **Small caps included.** JKP capped value-weight factors and the French factors hold small and micro caps, which a long-only large-cap book cannot trade at these returns.
- **Hindsight in the factor list.** The JKP list was assembled after the underlying papers; months before each publication were in the original authors' samples. The post-publication split below is the declared check.
- **Prior exposures (R9).** Before this declaration the coordinator saw two diagnostics on overlapping months: the 2026-09-28 audit scratch run on 7 French factors (equal weight Sharpe 0.83, inverse volatility 0.83) and the 2026-09-28 vision probe on JKP 153 factors (inverse volatility Sharpe 0.94 vs 0.72 for equal weight). This run re-examines a comparison already seen and supports no confirmatory claim.
- **Trial family.** `docs/preregistrations/m5_trial_family_v1.json`, SHA-256 `a99a862c651fd4e52e9904e62c8dfc539b85f57f1910d2a17b9bd03a6723417a`, verified equal to its committed HEAD version before any data was read.
- **Timing.** `after_month_end_signal_next_month_return`: weights for month t use returns through month t-1 and the declared availability of each factor's month-t return; the switch cost is charged in month t.

## Result

**Baseline product: R1** (inverse volatility). 8 of 8 declared conditions hold on jkp_factors_153 (R1 drawdown magnitude at most R0's and R1 Sharpe at least R0's, in both halves, at 20 and 50 bp). The S2 q-values are reported beside the decision and do not change it.

Full window at 20 bp on jkp_factors_153: annualized mean net return R0 2.57% and R1 2.26%; volatility R0 3.28% and R1 2.13%; maximum drawdown R0 -13.97% and R1 -7.23%. The S2 test of the mean monthly difference R1 minus R0 has HAC p 0.107 and BY q 0.2943.

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
| 1972-1999 | 20 bp | max_drawdown | -8.57% | -3.67% | yes |
| 1972-1999 | 20 bp | sharpe | 1.224 | 1.659 | yes |
| 1972-1999 | 50 bp | max_drawdown | -8.57% | -3.80% | yes |
| 1972-1999 | 50 bp | sharpe | 1.217 | 1.597 | yes |
| 2000-end | 20 bp | max_drawdown | -9.27% | -7.23% | yes |
| 2000-end | 20 bp | sharpe | 0.610 | 0.735 | yes |
| 2000-end | 50 bp | max_drawdown | -9.27% | -7.36% | yes |
| 2000-end | 50 bp | sharpe | 0.610 | 0.703 | yes |

## S2 Tests (R1 net minus R0 net at 20 bp, full window)

Family S2 has 3 tests; Benjamini-Yekutieli adjustment with family size 3; two-sided Newey-West HAC p-values.

| Test | Status | Months | Mean monthly difference (bp) | HAC t | HAC lags | p | BY q |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| S2.jkp_factors_153 | ok | 648 | -2.63 | -1.61 | 6 | 0.107 | 0.2943 |
| S2.jkp_themes_13 | ok | 648 | -2.67 | -1.89 | 6 | 0.05839 | 0.2943 |
| S2.french_7 | ok | 656 | -1.18 | -0.85 | 6 | 0.3927 | 0.72 |

## Universe jkp_factors_153

Evaluated 1972-01 to 2025-12; 153 declared factors; status `completed`.

| Rule | Cost | Period | Months | Ann. mean | Volatility | Sharpe | Max drawdown | Worst 12 months | Avg turnover |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R0 | 20 bp | full | 648 | 2.57% | 3.28% | 0.785 | -13.97% | -11.83% | 0.002 |
| R0 | 20 bp | 1972-1999 | 336 | 2.59% | 2.12% | 1.224 | -8.57% | -6.90% | 0.003 |
| R0 | 20 bp | 2000-end | 312 | 2.55% | 4.18% | 0.610 | -9.27% | -7.74% | 0.000 |
| R0 | 50 bp | full | 648 | 2.57% | 3.28% | 0.783 | -13.97% | -11.83% | 0.002 |
| R0 | 50 bp | 1972-1999 | 336 | 2.58% | 2.12% | 1.217 | -8.57% | -6.90% | 0.003 |
| R0 | 50 bp | 2000-end | 312 | 2.55% | 4.18% | 0.610 | -9.27% | -7.74% | 0.000 |
| R1 | 20 bp | full | 648 | 2.26% | 2.13% | 1.060 | -7.23% | -6.68% | 0.024 |
| R1 | 20 bp | 1972-1999 | 336 | 2.57% | 1.55% | 1.659 | -3.67% | -3.47% | 0.025 |
| R1 | 20 bp | 2000-end | 312 | 1.92% | 2.61% | 0.735 | -7.23% | -6.07% | 0.024 |
| R1 | 50 bp | full | 648 | 2.17% | 2.13% | 1.019 | -7.36% | -6.77% | 0.024 |
| R1 | 50 bp | 1972-1999 | 336 | 2.48% | 1.55% | 1.597 | -3.80% | -3.56% | 0.025 |
| R1 | 50 bp | 2000-end | 312 | 1.84% | 2.61% | 0.703 | -7.36% | -6.18% | 0.024 |

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
| full | 0.607 | 97373 | 1683 | 0 |
| 1972-1999 | 0.600 | 51320 | 0 | 0 |
| 2000-end | 0.619 | 46053 | 1683 | 0 |

Membership and missingness counts (factor-months):

| Period | Declared | In set | No month-t return | Fewer than 24 prior | Both | Typed missing |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| full | 99144 | 99056 | 0 | 88 | 0 | none |
| 1972-1999 | 51408 | 51320 | 0 | 88 | 0 | none |
| 2000-end | 47736 | 47736 | 0 | 0 | 0 | none |

Typed missing factor-months in the lookback-only months 1969-01 to 1971-12: absent 140. They count against the 24-return condition and are never filled.

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
| R1 | 20 bp | full | 648 | 2.05% | 1.26% | 1.629 | -3.43% | -2.83% | 0.024 |
| R1 | 20 bp | 1972-1999 | 336 | 2.53% | 1.08% | 2.338 | -1.22% | 0.15% | 0.024 |
| R1 | 20 bp | 2000-end | 312 | 1.53% | 1.41% | 1.086 | -3.43% | -2.83% | 0.024 |
| R1 | 50 bp | full | 648 | 1.96% | 1.26% | 1.559 | -3.60% | -2.95% | 0.024 |
| R1 | 50 bp | 1972-1999 | 336 | 2.44% | 1.08% | 2.252 | -1.24% | 0.03% | 0.024 |
| R1 | 50 bp | 2000-end | 312 | 1.44% | 1.41% | 1.026 | -3.60% | -2.95% | 0.024 |

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
| full | 0.698 | 8281 | 143 | 0 |
| 1972-1999 | 0.676 | 4368 | 0 | 0 |
| 2000-end | 0.716 | 3913 | 143 | 0 |

Membership and missingness counts (factor-months):

| Period | Declared | In set | No month-t return | Fewer than 24 prior | Both | Typed missing |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| full | 8424 | 8424 | 0 | 0 | 0 | none |
| 1972-1999 | 4368 | 4368 | 0 | 0 | 0 | none |
| 2000-end | 4056 | 4056 | 0 | 0 | 0 | none |

Typed missing factor-months in the lookback-only months 1969-01 to 1971-12: none. They count against the 24-return condition and are never filled.

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
| R1 | 20 bp | full | 656 | 3.42% | 4.10% | 0.835 | -16.58% | -9.39% | 0.023 |
| R1 | 20 bp | 1972-1999 | 336 | 4.21% | 3.13% | 1.343 | -6.97% | -4.89% | 0.024 |
| R1 | 20 bp | 2000-end | 320 | 2.60% | 4.91% | 0.529 | -16.58% | -9.39% | 0.023 |
| R1 | 50 bp | full | 656 | 3.34% | 4.10% | 0.815 | -16.74% | -9.46% | 0.023 |
| R1 | 50 bp | 1972-1999 | 336 | 4.13% | 3.13% | 1.317 | -7.08% | -4.97% | 0.024 |
| R1 | 50 bp | 2000-end | 320 | 2.52% | 4.91% | 0.512 | -16.74% | -9.46% | 0.023 |

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
| full | 0.426 | 4515 | 77 | 0 |
| 1972-1999 | 0.349 | 2352 | 0 | 0 |
| 2000-end | 0.474 | 2163 | 77 | 0 |

Membership and missingness counts (factor-months):

| Period | Declared | In set | No month-t return | Fewer than 24 prior | Both | Typed missing |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| full | 4592 | 4592 | 0 | 0 | 0 | none |
| 1972-1999 | 2352 | 2352 | 0 | 0 | 0 | none |
| 2000-end | 2240 | 2240 | 0 | 0 | 0 | none |

Typed missing factor-months in the lookback-only months 1969-01 to 1971-12: none. They count against the 24-return condition and are never filled.

## Post-Publication Split (jkp_factors_153, descriptive)

For month t the set is restricted to factors whose publication year is before the calendar year of t; R0 and R1 use the same rules and costs in one continuous run from 1972-01.

Status `refused`.

Evaluated months with an empty subset: 24 (1972-01 to 1973-12).

Refusal: 24 evaluated months have an empty set (first 1972-01, last 1973-12). The trial family refuses any evaluated month with an empty set, and it declares no other handling for this split, so the split has no metrics.

| Period | In set | In subset | Missing publication year | Published in or after year | Empty-subset months |
| --- | ---: | ---: | ---: | ---: | ---: |
| full | 99056 | 35292 | 7128 | 56636 | 24 |
| 1972-1999 | 51320 | 3060 | 3696 | 44564 | 24 |
| 2000-end | 47736 | 32232 | 3432 | 12072 | 0 |

## Limitations

- Diagnostic ceiling: public long-short series, gross of each factor's internal trading and borrow costs, including small caps. The implementable check on the repository's point-in-time S&P 500 books after costs is step 4.
- The comparison of R0 and R1 was already seen in two prior diagnostics on overlapping months; the halves reuse the same history and are not out-of-sample confirmation.
- Month-t availability of a factor return enters the month-t set by declaration: a JKP return exists only when both extreme portfolios met the minimum stock count at formation at the end of month t-1.
- The JKP and French files are revised by their providers; a later download can change results. The manifest pins the SHA-256 of the files used here.
- Target weights are compared without drift adjustment, as declared; the switch cost is a flat rate on weight turnover.
- Only the S2 comparison is tested; halves, the 50 bp level, the market, volatility-forecast accuracy, and the post-publication split are descriptive.
