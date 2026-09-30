# Milestone 5 Step 4b: SEC Value and Quality Sleeves on Point-in-Time S&P 500 Books

**Evidence ceiling: `DIAGNOSTIC_ONLY`.** Simulated research on the local `real_v2` snapshot and the pinned SEC companyfacts cache; no profitability claim. Aggregates only.

- **VP-2.** Premise VP-2 (the vendor's adjusted close applies each declared distribution) holds under owner decision O-9 for step 4 only; the M4.8 census measured S_D > 0.05 on 22.5 percent of eligible member-days. Owner decision O-9 extends it to step 4b.
- **R4.** No terminal evidence is accepted. Every residual held stop settles at -100 percent in every price and SEC sleeve and in the equal-weight benchmark; a last-close rerun is reported beside it.
- **Unpriced members** are never held. Unpriced member-day share: pre 27.83% (upper bound 27.97%); post 15.72% (upper bound 15.89%). 111 of 448 members at D0_pre have no pre-side panel (Stage D count).
- **Missing crash.** The seal window and its buffers exclude 2019-07 to 2021-08, including the 2020 crash, so drawdowns are understated.
- **Prior exposure.** Every step 4 number is seen on the same 99 comparison months; be_me, ni_me, and gp_at are in the public books of steps 2 and 3. No step 4b result is confirmatory.

## Decision Outcome (primary run)

- **Outcome: not_join.** The SEC Value and Quality classes do not join the baseline class set: R0_9 meets 2 of 8 conditions against R0_6.
- **S4b.ADD:** mean monthly difference 0.00051 over 99 months, HAC p 0.4177, BY q 1.0000 (family of 481, 1 observed), 95% interval (monthly) [-0.00072, 0.00175].
- **Fragility: not fragile** (0 sign changes between the -100 percent run and the last-close rerun; outcome changes: none).
- **Coverage tilt: not coverage-tilted** (0 margin signs differ against R0_6_mapped; R0_9 meets 2 of 8 against it).
- **Last-close outcome: not_join** (2 of 8; S4b.ADD mean 0.00032, no p-value).
- The labels, the q-value, and the last-close outcome are reported beside the outcome and do not change it.

## Conditions: R0_9 Against R0_6 Beside the Public Margins (primary run)

| Segment | Cost case | Metric | R0_9 | Comparator | Margin | Holds | Public margin | Public holds | Ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre | primary | max_drawdown | -0.1350 | -0.1199 | -0.0151 | no | 0.0326 | yes | -0.46 |
| pre | primary | sharpe | 0.4259 | 0.4491 | -0.0232 | no | 0.0151 | yes | -1.54 |
| pre | sensitivity | max_drawdown | -0.1359 | -0.1211 | -0.0148 | no | 0.0326 | yes | -0.45 |
| pre | sensitivity | sharpe | 0.3924 | 0.4049 | -0.0124 | no | 0.0151 | yes | -0.83 |
| post | primary | max_drawdown | -0.1412 | -0.1304 | -0.0108 | no | 0.0099 | yes | -1.10 |
| post | primary | sharpe | 0.2301 | 0.1692 | 0.0609 | yes | 0.0414 | yes | 1.47 |
| post | sensitivity | max_drawdown | -0.1421 | -0.1315 | -0.0106 | no | 0.0099 | yes | -1.08 |
| post | sensitivity | sharpe | 0.2043 | 0.1355 | 0.0689 | yes | 0.0414 | yes | 1.66 |

## Coverage Tilt: R0_9 Against R0_6_mapped (primary run)

| Segment | Cost case | Metric | R0_9 | Comparator | Margin | Holds |
| --- | --- | --- | --- | --- | --- | --- |
| pre | primary | max_drawdown | -0.1350 | -0.1205 | -0.0145 | no |
| pre | primary | sharpe | 0.4259 | 0.5093 | -0.0834 | no |
| pre | sensitivity | max_drawdown | -0.1359 | -0.1217 | -0.0142 | no |
| pre | sensitivity | sharpe | 0.3924 | 0.4654 | -0.0730 | no |
| post | primary | max_drawdown | -0.1412 | -0.1319 | -0.0093 | no |
| post | primary | sharpe | 0.2301 | 0.1512 | 0.0789 | yes |
| post | sensitivity | max_drawdown | -0.1421 | -0.1330 | -0.0091 | no |
| post | sensitivity | sharpe | 0.2043 | 0.1171 | 0.0872 | yes |

## Conditions in the Last-Close Rerun

| Segment | Cost case | Metric | R0_9 | Comparator | Margin | Holds |
| --- | --- | --- | --- | --- | --- | --- |
| pre | primary | max_drawdown | -0.1291 | -0.1137 | -0.0153 | no |
| pre | primary | sharpe | 0.6423 | 0.7218 | -0.0795 | no |
| pre | sensitivity | max_drawdown | -0.1300 | -0.1149 | -0.0151 | no |
| pre | sensitivity | sharpe | 0.6091 | 0.6779 | -0.0688 | no |
| post | primary | max_drawdown | -0.1342 | -0.1231 | -0.0111 | no |
| post | primary | sharpe | 0.3174 | 0.2633 | 0.0540 | yes |
| post | sensitivity | max_drawdown | -0.1351 | -0.1241 | -0.0109 | no |
| post | sensitivity | sharpe | 0.2915 | 0.2294 | 0.0621 | yes |

## Rule Books

| Run | Book | Cost case | Segment | Months | Ann. mean | Volatility | Sharpe | Max drawdown | Turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | R0_9 | primary | pre | 55 | 5.98% | 12.00% | 0.426 | -13.50% | 0.033 |
| primary | R0_9 | primary | post | 44 | 7.83% | 15.61% | 0.230 | -14.12% | 0.038 |
| primary | R0_9 | sensitivity | pre | 55 | 5.58% | 12.00% | 0.392 | -13.59% | 0.033 |
| primary | R0_9 | sensitivity | post | 44 | 7.42% | 15.61% | 0.204 | -14.21% | 0.038 |
| primary | R0_6 | primary | pre | 55 | 5.80% | 10.98% | 0.449 | -11.99% | 0.032 |
| primary | R0_6 | primary | post | 44 | 6.68% | 14.43% | 0.169 | -13.04% | 0.038 |
| primary | R0_6 | sensitivity | pre | 55 | 5.31% | 10.97% | 0.405 | -12.11% | 0.032 |
| primary | R0_6 | sensitivity | post | 44 | 6.19% | 14.43% | 0.135 | -13.15% | 0.038 |
| primary | R0_6_mapped | primary | pre | 55 | 6.51% | 11.08% | 0.509 | -12.05% | 0.032 |
| primary | R0_6_mapped | primary | post | 44 | 6.40% | 14.34% | 0.151 | -13.19% | 0.038 |
| primary | R0_6_mapped | sensitivity | pre | 55 | 6.02% | 11.07% | 0.465 | -12.17% | 0.032 |
| primary | R0_6_mapped | sensitivity | post | 44 | 5.91% | 14.33% | 0.117 | -13.30% | 0.038 |
| primary | R1_9 | primary | pre | 55 | 5.39% | 11.59% | 0.390 | -12.94% | 0.053 |
| primary | R1_9 | primary | post | 44 | 7.40% | 14.89% | 0.212 | -13.95% | 0.055 |
| primary | R1_9 | sensitivity | pre | 55 | 4.92% | 11.59% | 0.350 | -13.07% | 0.053 |
| primary | R1_9 | sensitivity | post | 44 | 6.94% | 14.89% | 0.182 | -14.04% | 0.055 |
| last_close | R0_9 | primary | pre | 55 | 8.57% | 11.98% | 0.642 | -12.91% | 0.033 |
| last_close | R0_9 | primary | post | 44 | 9.19% | 15.60% | 0.317 | -13.42% | 0.038 |
| last_close | R0_9 | sensitivity | pre | 55 | 8.16% | 11.98% | 0.609 | -13.00% | 0.033 |
| last_close | R0_9 | sensitivity | post | 44 | 8.78% | 15.60% | 0.292 | -13.51% | 0.038 |
| last_close | R0_6 | primary | pre | 55 | 8.81% | 11.00% | 0.722 | -11.37% | 0.031 |
| last_close | R0_6 | primary | post | 44 | 8.02% | 14.38% | 0.263 | -12.31% | 0.038 |
| last_close | R0_6 | sensitivity | pre | 55 | 8.32% | 11.00% | 0.678 | -11.49% | 0.031 |
| last_close | R0_6 | sensitivity | post | 44 | 7.53% | 14.38% | 0.229 | -12.41% | 0.038 |
| last_close | R0_6_mapped | primary | pre | 55 | 9.07% | 11.01% | 0.745 | -11.39% | 0.032 |
| last_close | R0_6_mapped | primary | post | 44 | 7.71% | 14.33% | 0.243 | -12.41% | 0.038 |
| last_close | R0_6_mapped | sensitivity | pre | 55 | 8.59% | 11.00% | 0.701 | -11.51% | 0.032 |
| last_close | R0_6_mapped | sensitivity | post | 44 | 7.22% | 14.32% | 0.208 | -12.52% | 0.038 |
| last_close | R1_9 | primary | pre | 55 | 8.09% | 11.55% | 0.625 | -12.34% | 0.053 |
| last_close | R1_9 | primary | post | 44 | 8.78% | 14.87% | 0.306 | -13.18% | 0.055 |
| last_close | R1_9 | sensitivity | pre | 55 | 7.62% | 11.55% | 0.585 | -12.47% | 0.053 |
| last_close | R1_9 | sensitivity | post | 44 | 8.33% | 14.86% | 0.276 | -13.27% | 0.055 |

Rule R1 over nine sleeves (R1_9) is descriptive: no test and no decision. R2 is not run.

## SEC Sleeves (primary run)

| Segment | Sleeve | Months | Ann. mean | Sharpe | Max drawdown | Stock turnover / month | Stock cost / month |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pre | BM_AF (primary) | 62 | 7.79% | 0.439 | -18.95% | 0.193 | 0.00010 |
| pre | BM_AF (sensitivity) | 62 | 7.67% | 0.431 | -19.07% | 0.193 | 0.00019 |
| pre | EP_AF (primary) | 62 | 7.17% | 0.383 | -19.59% | 0.261 | 0.00013 |
| pre | EP_AF (sensitivity) | 62 | 7.01% | 0.374 | -19.73% | 0.261 | 0.00026 |
| pre | GP_AT_AF (primary) | 62 | 6.62% | 0.437 | -16.22% | 0.108 | 0.00005 |
| pre | GP_AT_AF (sensitivity) | 62 | 6.55% | 0.433 | -16.23% | 0.108 | 0.00011 |
| post | BM_AF (primary) | 59 | 12.46% | 0.482 | -20.53% | 0.202 | 0.00010 |
| post | BM_AF (sensitivity) | 59 | 12.34% | 0.475 | -20.58% | 0.202 | 0.00020 |
| post | EP_AF (primary) | 59 | 10.61% | 0.380 | -21.57% | 0.247 | 0.00012 |
| post | EP_AF (sensitivity) | 59 | 10.46% | 0.372 | -21.65% | 0.247 | 0.00025 |
| post | GP_AT_AF (primary) | 59 | 5.66% | 0.117 | -27.42% | 0.121 | 0.00006 |
| post | GP_AT_AF (sensitivity) | 59 | 5.59% | 0.113 | -27.46% | 0.121 | 0.00012 |

## Benchmarks: Net Excess (primary run, comparison months for books)

| Segment | Book | Ann. excess vs SPY | Compounded vs SPY | Ann. excess vs EW | Compounded vs EW | Unpriced share |
| --- | --- | --- | --- | --- | --- | --- |
| pre | R0_9 (primary) | -4.43% | -28.16% | -1.37% | -7.51% | 27.83% |
| pre | R0_6 (primary) | -4.61% | -28.55% | -1.55% | -7.90% | 27.83% |
| pre | R0_6_mapped (primary) | -3.90% | -24.43% | -0.84% | -3.78% | 27.83% |
| pre | R1_9 (primary) | -5.02% | -31.30% | -1.96% | -10.65% | 27.83% |
| pre | BM_AF (primary) | -3.57% | -33.18% | -0.71% | -8.87% | 27.83% |
| pre | EP_AF (primary) | -4.19% | -38.32% | -1.33% | -14.01% | 27.83% |
| pre | GP_AT_AF (primary) | -4.74% | -38.72% | -1.88% | -14.40% | 27.83% |
| pre | R0_9 (sensitivity) | -4.83% | -30.48% | -1.77% | -9.83% | 27.83% |
| pre | R0_6 (sensitivity) | -5.10% | -31.34% | -2.04% | -10.69% | 27.83% |
| pre | R0_6_mapped (sensitivity) | -4.39% | -27.32% | -1.33% | -6.67% | 27.83% |
| pre | R1_9 (sensitivity) | -5.49% | -33.91% | -2.43% | -13.26% | 27.83% |
| pre | BM_AF (sensitivity) | -3.69% | -34.02% | -0.83% | -9.71% | 27.83% |
| pre | EP_AF (sensitivity) | -4.35% | -39.41% | -1.48% | -15.09% | 27.83% |
| pre | GP_AT_AF (sensitivity) | -4.81% | -39.16% | -1.94% | -14.85% | 27.83% |
| post | R0_9 (primary) | -8.58% | -46.98% | -1.71% | -7.23% | 15.72% |
| post | R0_6 (primary) | -9.73% | -51.45% | -2.86% | -11.70% | 15.72% |
| post | R0_6_mapped (primary) | -10.01% | -52.61% | -3.13% | -12.87% | 15.72% |
| post | R1_9 (primary) | -9.01% | -48.48% | -2.14% | -8.73% | 15.72% |
| post | BM_AF (primary) | -0.43% | -7.13% | 4.22% | 29.06% | 15.72% |
| post | EP_AF (primary) | -2.29% | -21.83% | 2.36% | 14.35% | 15.72% |
| post | GP_AT_AF (primary) | -7.24% | -54.36% | -2.59% | -18.18% | 15.72% |
| post | R0_9 (sensitivity) | -8.99% | -48.84% | -2.11% | -9.09% | 15.72% |
| post | R0_6 (sensitivity) | -10.22% | -53.62% | -3.34% | -13.87% | 15.72% |
| post | R0_6_mapped (sensitivity) | -10.49% | -54.77% | -3.62% | -15.02% | 15.72% |
| post | R1_9 (sensitivity) | -9.47% | -50.54% | -2.59% | -10.79% | 15.72% |
| post | BM_AF (sensitivity) | -0.55% | -8.14% | 4.09% | 28.05% | 15.72% |
| post | EP_AF (sensitivity) | -2.44% | -22.96% | 2.21% | 13.23% | 15.72% |
| post | GP_AT_AF (sensitivity) | -7.31% | -54.80% | -2.66% | -18.61% | 15.72% |

## SEC Missingness by Reason and Later Exit Class (member-days)

Every evaluation-mask member-day over [first reset, last book row] carries exactly one status per SEC sleeve; a ranking-set member carries its rebalance status, any other member-day is not_ranked_at_rebalance. A not_ranked_at_rebalance member-day means the member cannot be newly selected at that rebalance. The engine's halt_gap_return_v1 accounting is unchanged: a previously held position locked by a missing execution price stays held, so status counts and holdings are distinct (coordinator ruling on GPT-S4BF-R2-A1 and OPUS-S4BF-R2-A3).

pre, BM_AF: 469213 member-days. preferred_zero_by_absence: 186428 ranked member-days.

| Status | Days | Share | index_removal_still_trading | delisting_candidate | disappearance_outside_membership | seal_gap_identity_split | unknown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ranked | 351844 | 74.99% | 297520 | 41240 | 13084 | 0 | 0 |
| not_ranked_at_rebalance | 1367 | 0.29% | 983 | 197 | 57 | 0 | 130 |
| identity_unmapped | 20630 | 4.40% | 20630 | 0 | 0 | 0 | 0 |
| identity_ambiguous | 3081 | 0.66% | 0 | 2840 | 241 | 0 | 0 |
| identity_multi_class | 6043 | 1.29% | 3941 | 2102 | 0 | 0 | 0 |
| facts_absent | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| non_usd | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| no_annual_fact | 34046 | 7.26% | 32670 | 1335 | 41 | 0 | 0 |
| amendment_first | 1300 | 0.28% | 1300 | 0 | 0 | 0 | 0 |
| stale | 14206 | 3.03% | 10879 | 2672 | 655 | 0 | 0 |
| concept_missing | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| be_nonpositive | 13492 | 2.88% | 13080 | 327 | 85 | 0 | 0 |
| assets_nonpositive | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| shares_ambiguous | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| shares_missing | 23121 | 4.93% | 21093 | 1464 | 564 | 0 | 0 |
| price_missing | 83 | 0.02% | 83 | 0 | 0 | 0 | 0 |

pre, EP_AF: 469213 member-days.

| Status | Days | Share | index_removal_still_trading | delisting_candidate | disappearance_outside_membership | seal_gap_identity_split | unknown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ranked | 354764 | 75.61% | 300028 | 42028 | 12708 | 0 | 0 |
| not_ranked_at_rebalance | 1367 | 0.29% | 983 | 197 | 57 | 0 | 130 |
| identity_unmapped | 20630 | 4.40% | 20630 | 0 | 0 | 0 | 0 |
| identity_ambiguous | 3081 | 0.66% | 0 | 2840 | 241 | 0 | 0 |
| identity_multi_class | 6043 | 1.29% | 3941 | 2102 | 0 | 0 | 0 |
| facts_absent | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| non_usd | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| no_annual_fact | 32637 | 6.96% | 30435 | 1700 | 502 | 0 | 0 |
| amendment_first | 1300 | 0.28% | 1300 | 0 | 0 | 0 | 0 |
| stale | 26979 | 5.75% | 23914 | 1846 | 1219 | 0 | 0 |
| concept_missing | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| be_nonpositive | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| assets_nonpositive | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| shares_ambiguous | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| shares_missing | 22329 | 4.76% | 20865 | 1464 | 0 | 0 | 0 |
| price_missing | 83 | 0.02% | 83 | 0 | 0 | 0 | 0 |

pre, GP_AT_AF: 469213 member-days.

| Status | Days | Share | index_removal_still_trading | delisting_candidate | disappearance_outside_membership | seal_gap_identity_split | unknown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ranked | 250499 | 53.39% | 212527 | 27248 | 10724 | 0 | 0 |
| not_ranked_at_rebalance | 1367 | 0.29% | 983 | 197 | 57 | 0 | 130 |
| identity_unmapped | 20630 | 4.40% | 20630 | 0 | 0 | 0 | 0 |
| identity_ambiguous | 3081 | 0.66% | 0 | 2840 | 241 | 0 | 0 |
| identity_multi_class | 6043 | 1.29% | 3941 | 2102 | 0 | 0 | 0 |
| facts_absent | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| non_usd | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| no_annual_fact | 9761 | 2.08% | 8385 | 1335 | 41 | 0 | 0 |
| amendment_first | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| stale | 1463 | 0.31% | 808 | 0 | 655 | 0 | 0 |
| concept_missing | 176369 | 37.59% | 154905 | 18455 | 3009 | 0 | 0 |
| be_nonpositive | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| assets_nonpositive | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| shares_ambiguous | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| shares_missing | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| price_missing | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |

post, BM_AF: 526151 member-days. preferred_zero_by_absence: 192065 ranked member-days.

| Status | Days | Share | index_removal_still_trading | delisting_candidate | disappearance_outside_membership | seal_gap_identity_split | unknown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ranked | 399957 | 76.02% | 383976 | 15218 | 763 | 0 | 0 |
| not_ranked_at_rebalance | 673 | 0.13% | 589 | 7 | 0 | 0 | 77 |
| identity_unmapped | 22520 | 4.28% | 22100 | 420 | 0 | 0 | 0 |
| identity_ambiguous | 1238 | 0.24% | 1238 | 0 | 0 | 0 | 0 |
| identity_multi_class | 3868 | 0.74% | 3714 | 154 | 0 | 0 | 0 |
| facts_absent | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| non_usd | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| no_annual_fact | 21332 | 4.05% | 20626 | 0 | 706 | 0 | 0 |
| amendment_first | 126 | 0.02% | 0 | 126 | 0 | 0 | 0 |
| stale | 19147 | 3.64% | 17782 | 1365 | 0 | 0 | 0 |
| concept_missing | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| be_nonpositive | 29088 | 5.53% | 29088 | 0 | 0 | 0 | 0 |
| assets_nonpositive | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| shares_ambiguous | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| shares_missing | 28202 | 5.36% | 27750 | 0 | 452 | 0 | 0 |
| price_missing | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |

post, EP_AF: 526151 member-days.

| Status | Days | Share | index_removal_still_trading | delisting_candidate | disappearance_outside_membership | seal_gap_identity_split | unknown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ranked | 420898 | 80.00% | 404230 | 15905 | 763 | 0 | 0 |
| not_ranked_at_rebalance | 673 | 0.13% | 589 | 7 | 0 | 0 | 77 |
| identity_unmapped | 22520 | 4.28% | 22100 | 420 | 0 | 0 | 0 |
| identity_ambiguous | 1238 | 0.24% | 1238 | 0 | 0 | 0 | 0 |
| identity_multi_class | 3868 | 0.74% | 3714 | 154 | 0 | 0 | 0 |
| facts_absent | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| non_usd | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| no_annual_fact | 20371 | 3.87% | 19391 | 274 | 706 | 0 | 0 |
| amendment_first | 1238 | 0.24% | 1238 | 0 | 0 | 0 | 0 |
| stale | 29570 | 5.62% | 28588 | 530 | 452 | 0 | 0 |
| concept_missing | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| be_nonpositive | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| assets_nonpositive | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| shares_ambiguous | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| shares_missing | 25775 | 4.90% | 25775 | 0 | 0 | 0 | 0 |
| price_missing | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |

post, GP_AT_AF: 526151 member-days.

| Status | Days | Share | index_removal_still_trading | delisting_candidate | disappearance_outside_membership | seal_gap_identity_split | unknown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ranked | 299024 | 56.83% | 287532 | 10729 | 763 | 0 | 0 |
| not_ranked_at_rebalance | 673 | 0.13% | 589 | 7 | 0 | 0 | 77 |
| identity_unmapped | 22520 | 4.28% | 22100 | 420 | 0 | 0 | 0 |
| identity_ambiguous | 1238 | 0.24% | 1238 | 0 | 0 | 0 | 0 |
| identity_multi_class | 3868 | 0.74% | 3714 | 154 | 0 | 0 | 0 |
| facts_absent | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| non_usd | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| no_annual_fact | 2269 | 0.43% | 2269 | 0 | 0 | 0 | 0 |
| amendment_first | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| stale | 164 | 0.03% | 164 | 0 | 0 | 0 | 0 |
| concept_missing | 196395 | 37.33% | 189257 | 5980 | 1158 | 0 | 0 |
| be_nonpositive | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| assets_nonpositive | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| shares_ambiguous | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| shares_missing | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |
| price_missing | 0 | 0.00% | 0 | 0 | 0 | 0 | 0 |

## Identity Exposure (member-days of the eligible pool)

| Scope | Exit class | Member-days | Not mapped | Share |
| --- | --- | --- | --- | --- |
| post | all | 526610 | 27665 | 5.25% |
| post | index_removal_still_trading | 507341 | 27087 | 5.34% |
| post | delisting_candidate | 17342 | 577 | 3.33% |
| post | disappearance_outside_membership | 1927 | 1 | 0.05% |
| post | seal_gap_identity_split | 0 | 0 | n/a |
| post | unknown | 0 | 0 | n/a |
| pre | all | 469574 | 29903 | 6.37% |
| pre | index_removal_still_trading | 402561 | 24693 | 6.13% |
| pre | delisting_candidate | 52257 | 4958 | 9.49% |
| pre | disappearance_outside_membership | 14756 | 252 | 1.71% |
| pre | seal_gap_identity_split | 0 | 0 | n/a |
| pre | unknown | 0 | 0 | n/a |
| pooled | all | 996184 | 57568 | 5.78% |
| pooled | index_removal_still_trading | 909902 | 51780 | 5.69% |
| pooled | delisting_candidate | 69599 | 5535 | 7.95% |
| pooled | disappearance_outside_membership | 16683 | 253 | 1.52% |
| pooled | seal_gap_identity_split | 0 | 0 | n/a |
| pooled | unknown | 0 | 0 | n/a |

| Scope | Status: reason | Member-days | Share of all |
| --- | --- | --- | --- |
| post | ambiguous: ticker_cik_disagrees | 1239 | 0.24% |
| post | multi_class: shared_cik_overlapping | 3872 | 0.74% |
| post | unmapped: name_mismatch | 16513 | 3.14% |
| post | unmapped: no_periodic_filing_in_window | 6041 | 1.15% |
| pre | ambiguous: several_survivors | 1544 | 0.33% |
| pre | ambiguous: ticker_cik_disagrees | 1547 | 0.33% |
| pre | multi_class: shared_cik_overlapping | 6085 | 1.30% |
| pre | unmapped: name_mismatch | 15503 | 3.30% |
| pre | unmapped: no_periodic_filing_in_window | 5224 | 1.11% |
| pooled | ambiguous: several_survivors | 1544 | 0.15% |
| pooled | ambiguous: ticker_cik_disagrees | 2786 | 0.28% |
| pooled | multi_class: shared_cik_overlapping | 9957 | 1.00% |
| pooled | unmapped: name_mismatch | 32016 | 3.21% |
| pooled | unmapped: no_periodic_filing_in_window | 11265 | 1.13% |

## Affected Events (primary run, R4 default)

| Segment | Book | Events | Weight sum | Weight max |
| --- | --- | --- | --- | --- |
| pre | BM_AF (primary) | 4 | 0.0740 | 0.0209 |
| pre | BM_AF (sensitivity) | 4 | 0.0740 | 0.0209 |
| pre | EP_AF (primary) | 2 | 0.0360 | 0.0207 |
| pre | EP_AF (sensitivity) | 2 | 0.0360 | 0.0207 |
| pre | GP_AT_AF (primary) | 5 | 0.1295 | 0.0272 |
| pre | GP_AT_AF (sensitivity) | 5 | 0.1295 | 0.0272 |
| pre | R0_9 (primary) | 28 | 0.1190 | 0.0107 |
| pre | R0_9 (sensitivity) | 28 | 0.1190 | 0.0107 |
| post | BM_AF (primary) | 5 | 0.0651 | 0.0152 |
| post | BM_AF (sensitivity) | 5 | 0.0651 | 0.0152 |
| post | EP_AF (primary) | 6 | 0.0846 | 0.0146 |
| post | EP_AF (sensitivity) | 6 | 0.0846 | 0.0146 |
| post | GP_AT_AF (primary) | 3 | 0.0627 | 0.0214 |
| post | GP_AT_AF (sensitivity) | 3 | 0.0627 | 0.0214 |
| post | R0_9 (primary) | 15 | 0.0495 | 0.0075 |
| post | R0_9 (sensitivity) | 15 | 0.0495 | 0.0075 |

## Transmission (descriptive, primary cost case)

| Segment | Sleeve or class | Months | PIT mean active | Public mean | Ratio | Correlation |
| --- | --- | --- | --- | --- | --- | --- |
| pre | BM_AF | 62 | -0.00059 | -0.00519 | 0.11 | 0.78 |
| pre | EP_AF | 62 | -0.00111 | -0.00050 | 2.21 | 0.52 |
| pre | GP_AT_AF | 62 | -0.00157 | 0.00546 | -0.29 | 0.47 |
| post | BM_AF | 52 | 0.00221 | 0.00508 | 0.44 | 0.87 |
| post | EP_AF | 52 | 0.00194 | 0.00692 | 0.28 | 0.50 |
| post | GP_AT_AF | 52 | -0.00134 | -0.00183 | 0.73 | 0.77 |
| pooled | BM_AF | 114 | 0.00069 | -0.00050 | -1.36 | 0.82 |
| pooled | EP_AF | 114 | 0.00028 | 0.00289 | 0.10 | 0.48 |
| pooled | GP_AT_AF | 114 | -0.00146 | 0.00213 | -0.68 | 0.58 |
| pre (class) | Value | 55 | 0.00003 | -0.00114 | -0.03 | 0.62 |
| pre (class) | Quality | 55 | -0.00235 | 0.00235 | -1.00 | 0.38 |
| post (class) | Value | 44 | 0.00111 | 0.00099 | 1.12 | 0.63 |
| post (class) | Quality | 44 | -0.00055 | 0.00153 | -0.36 | 0.54 |

## Halts in the SEC Sleeves (primary run)

| Segment | Sleeve | Unmarked halt rows | Locked execution rows |
| --- | --- | --- | --- |
| pre | BM_AF (primary) | 0 | 0 |
| pre | BM_AF (sensitivity) | 0 | 0 |
| pre | EP_AF (primary) | 0 | 0 |
| pre | EP_AF (sensitivity) | 0 | 0 |
| pre | GP_AT_AF (primary) | 0 | 0 |
| pre | GP_AT_AF (sensitivity) | 0 | 0 |
| post | BM_AF (primary) | 1 | 0 |
| post | BM_AF (sensitivity) | 1 | 0 |
| post | EP_AF (primary) | 1 | 0 |
| post | EP_AF (sensitivity) | 1 | 0 |
| post | GP_AT_AF (primary) | 0 | 0 |
| post | GP_AT_AF (sensitivity) | 0 | 0 |

## Data Quality

- First-filed value ties with distinct values inside one accession: 0 keys; the lowest accession's first fact in file order is used.
- Rebalance statuses (member-rebalances, each ranking-set member exactly once): pre BM_AF ranked 17096; pre EP_AF ranked 17251; pre GP_AT_AF ranked 12183; post BM_AF ranked 19723; post EP_AF ranked 20765; post GP_AT_AF ranked 14741.

## Limitations

- Companyfacts carries no dimensional facts, so unlisted share classes are not detected.
- Concept chains are frozen; a filer whose tag is outside a chain is concept_missing, not repaired.
- The mapped universe keeps 563 of 632 eligible IDs; the not-mapped share differs by later exit class (identity exposure above), which the coverage-tilt label addresses descriptively.
- SEC facts filed inside the seal window may enter an early post-segment signal; no seal-window price is read.

