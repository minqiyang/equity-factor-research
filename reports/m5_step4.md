# Milestone 5 Step 4: Price-Class Bridge on Point-in-Time S&P 500 Books

**Evidence ceiling: `DIAGNOSTIC_ONLY`.** Simulated research on the local `real_v2` snapshot; no profitability claim. Aggregates only.

- **VP-2.** Premise VP-2 (the vendor's adjusted close applies each declared distribution) holds under owner decision O-9 for step 4 only; the M4.8 census measured S_D > 0.05 on 22.5 percent of eligible member-days.
- **R4.** No terminal evidence is accepted. Every residual held stop settles at -100 percent in every sleeve and in the equal-weight benchmark; a last-close rerun is reported beside it.
- **Fragility: FRAGILE** (3 sign changes between the -100 percent run and the last-close rerun; outcome changes: none).
- **Unpriced members** are never held. Unpriced member-day share: pre 27.83% (upper bound 27.97%); post 15.72% (upper bound 15.89%). 111 of 448 members at D0_pre have no pre-side panel (Stage D count).
- **Missing crash.** The seal window and its buffers exclude 2019-07 to 2021-08, including the 2020 crash, so drawdowns are understated.
- **Prior exposure.** The post segment re-examines M4.7 factors and months; only 2014-05 to 2016-07 is unexposed. No result is confirmatory.

## Decision Outcomes (primary run)

- Point-in-time baseline product: **R0**. Rule R1 against R0: 4 of 8 on point-in-time books, 6 of 8 on public books over the same months.
- R2: **closed**. R2 against rule R1: 6 of 8 on point-in-time books, 4 of 8 on public books over the same months; R2 against R0: 3 of 8 on point-in-time books, 6 of 8 on public books over the same months.
- Fragility: **FRAGILE**. Sign changes: R2_vs_R1:pre:primary:sharpe, R2_vs_R1:pre:sensitivity:sharpe, R2_vs_R1:post:sensitivity:sharpe.
- Last-close rerun: baseline R0, R2 closed.
- S4 q-values and the fragility label are reported beside the outcomes and do not change them.

## Survival: Point-in-Time Conditions Beside the Public Margins

### Rule R1 against R0: 4 of 8 hold on point-in-time books (6 of 8 on public books over the same months)

| Segment | Cost case | Metric | PIT margin | PIT holds | Public margin | Public holds | Ratio | Last-close margin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre | primary | max_drawdown | 0.0062 | yes | 0.0039 | yes | 1.603 | 0.0065 |
| pre | primary | sharpe | -0.0248 | no | -0.0948 | no | n/a | -0.0045 |
| pre | sensitivity | max_drawdown | 0.0059 | yes | 0.0035 | yes | 1.698 | 0.0061 |
| pre | sensitivity | sharpe | -0.0305 | no | -0.1537 | no | n/a | -0.0109 |
| post | primary | max_drawdown | 0.0014 | yes | 0.0200 | yes | 0.070 | 0.0024 |
| post | primary | sharpe | -0.0103 | no | 0.1770 | yes | -0.058 | -0.0013 |
| post | sensitivity | max_drawdown | 0.0015 | yes | 0.0195 | yes | 0.076 | 0.0025 |
| post | sensitivity | sharpe | -0.0139 | no | 0.1452 | yes | -0.096 | -0.0048 |

### R2 against rule R1: 6 of 8 hold on point-in-time books (4 of 8 on public books over the same months)

| Segment | Cost case | Metric | PIT margin | PIT holds | Public margin | Public holds | Ratio | Last-close margin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre | primary | max_drawdown | -0.0000 | yes | -0.0010 | no | n/a | -0.0000 |
| pre | primary | sharpe | 0.0042 | yes | -0.0163 | no | n/a | -0.0011 |
| pre | sensitivity | max_drawdown | -0.0000 | yes | -0.0014 | no | n/a | 0.0000 |
| pre | sensitivity | sharpe | 0.0009 | yes | -0.0397 | no | n/a | -0.0043 |
| post | primary | max_drawdown | -0.0024 | no | 0.0006 | yes | -4.066 | -0.0032 |
| post | primary | sharpe | 0.0121 | yes | 0.0336 | yes | 0.359 | 0.0079 |
| post | sensitivity | max_drawdown | -0.0040 | no | 0.0005 | yes | -7.542 | -0.0048 |
| post | sensitivity | sharpe | 0.0020 | yes | 0.0138 | yes | 0.145 | -0.0023 |

### R2 against R0: 3 of 8 hold on point-in-time books (6 of 8 on public books over the same months)

| Segment | Cost case | Metric | PIT margin | PIT holds | Public margin | Public holds | Ratio | Last-close margin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre | primary | max_drawdown | 0.0062 | yes | 0.0029 | yes | 2.143 | 0.0065 |
| pre | primary | sharpe | -0.0206 | no | -0.1111 | no | n/a | -0.0056 |
| pre | sensitivity | max_drawdown | 0.0059 | yes | 0.0021 | yes | 2.812 | 0.0061 |
| pre | sensitivity | sharpe | -0.0296 | no | -0.1934 | no | n/a | -0.0152 |
| post | primary | max_drawdown | -0.0010 | no | 0.0206 | yes | -0.048 | -0.0007 |
| post | primary | sharpe | 0.0018 | yes | 0.2106 | yes | 0.008 | 0.0066 |
| post | sensitivity | max_drawdown | -0.0025 | no | 0.0201 | yes | -0.124 | -0.0023 |
| post | sensitivity | sharpe | -0.0119 | no | 0.1590 | yes | -0.075 | -0.0072 |

Sharpe on point-in-time books is 12 x mean(r_net - RF) / (sqrt(12) x sd(r_net)); the public long-short books keep the v1 Sharpe without RF. Drawdown margins are R1 magnitude minus candidate magnitude.

## S4 Tests (primary run, primary cost case, pooled comparison months)

| Test | Months | Mean monthly | 95% interval (monthly) | HAC p | BY q (family 480) | Last-close mean |
| --- | --- | --- | --- | --- | --- | --- |
| S4.R1 | 99 | -0.03% | -0.07% to 0.01% | 0.193 | 1.000 | -0.02% |
| S4.R2 | 99 | 0.01% | -0.01% to 0.04% | 0.352 | 1.000 | 0.01% |

The BY family counts 2 observed tests and 478 prior slots at p = 1. The last-close rerun reports means and signs only. With 480 slots the smallest p-value needs about 1.5e-5 to reach q 0.05.

## Rule Metrics (primary run)

| Segment | Cost case | Rule | Months | Ann. mean | Volatility | Sharpe (RF) | Max drawdown | Avg switch turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre | primary | R0 | 55 | 5.80% | 10.98% | 0.449 | -11.99% | 0.032 |
| pre | primary | R1 | 55 | 5.39% | 10.65% | 0.424 | -11.37% | 0.052 |
| pre | primary | R2 | 55 | 5.44% | 10.66% | 0.428 | -11.37% | 0.062 |
| pre | sensitivity | R0 | 55 | 5.31% | 10.97% | 0.405 | -12.11% | 0.032 |
| pre | sensitivity | R1 | 55 | 4.85% | 10.65% | 0.374 | -11.52% | 0.052 |
| pre | sensitivity | R2 | 55 | 4.87% | 10.66% | 0.375 | -11.52% | 0.062 |
| post | primary | R0 | 44 | 6.68% | 14.43% | 0.169 | -13.04% | 0.038 |
| post | primary | R1 | 44 | 6.42% | 13.74% | 0.159 | -12.90% | 0.055 |
| post | primary | R2 | 44 | 6.68% | 14.29% | 0.171 | -13.14% | 0.092 |
| post | sensitivity | R0 | 44 | 6.19% | 14.43% | 0.135 | -13.15% | 0.038 |
| post | sensitivity | R1 | 44 | 5.90% | 13.74% | 0.122 | -13.00% | 0.055 |
| post | sensitivity | R2 | 44 | 6.00% | 14.29% | 0.124 | -13.40% | 0.092 |

## Excess Over the Benchmarks (primary run)

| Segment | Book | Ann. excess vs SPY | Total excess vs SPY | Ann. excess vs EW | Total excess vs EW | Unpriced share |
| --- | --- | --- | --- | --- | --- | --- |
| pre | R0 (primary) | -4.61% | -28.55% | -1.55% | -7.90% | 27.83% |
| pre | R1 (primary) | -5.02% | -30.71% | -1.97% | -10.06% | 27.83% |
| pre | R2 (primary) | -4.97% | -30.43% | -1.91% | -9.78% | 27.83% |
| pre | MOM_12_1 (primary) | -6.63% | -50.40% | -3.76% | -26.08% | 27.83% |
| pre | HIGH_52W (primary) | -6.98% | -51.43% | -4.12% | -27.12% | 27.83% |
| pre | REV_1M (primary) | -3.05% | -28.92% | -0.18% | -4.61% | 27.83% |
| pre | LOW_VOL_252 (primary) | -0.48% | -2.22% | 2.39% | 22.10% | 27.83% |
| pre | LOW_BETA_252 (primary) | -6.93% | -50.32% | -4.06% | -26.01% | 27.83% |
| pre | AMIHUD_ILLIQ_63 (primary) | -2.39% | -23.15% | 0.47% | 1.16% | 27.83% |
| pre | R0 (sensitivity) | -5.10% | -31.34% | -2.04% | -10.69% | 27.83% |
| pre | R1 (sensitivity) | -5.55% | -33.71% | -2.50% | -13.06% | 27.83% |
| pre | R2 (sensitivity) | -5.54% | -33.63% | -2.48% | -12.98% | 27.83% |
| pre | MOM_12_1 (sensitivity) | -6.95% | -52.44% | -4.09% | -28.13% | 27.83% |
| pre | HIGH_52W (sensitivity) | -7.63% | -55.45% | -4.77% | -31.14% | 27.83% |
| pre | REV_1M (sensitivity) | -4.00% | -35.83% | -1.14% | -11.52% | 27.83% |
| pre | LOW_VOL_252 (sensitivity) | -0.59% | -3.16% | 2.28% | 21.16% | 27.83% |
| pre | LOW_BETA_252 (sensitivity) | -7.04% | -51.01% | -4.17% | -26.70% | 27.83% |
| pre | AMIHUD_ILLIQ_63 (sensitivity) | -2.55% | -24.36% | 0.32% | -0.05% | 27.83% |
| post | R0 (primary) | -9.73% | -51.45% | -2.86% | -11.70% | 15.72% |
| post | R1 (primary) | -9.99% | -52.18% | -3.11% | -12.43% | 15.72% |
| post | R2 (primary) | -9.73% | -51.35% | -2.86% | -11.60% | 15.72% |
| post | MOM_12_1 (primary) | -1.27% | -13.19% | 3.38% | 23.00% | 15.72% |
| post | HIGH_52W (primary) | -5.63% | -40.72% | -0.98% | -4.54% | 15.72% |
| post | REV_1M (primary) | -9.35% | -67.20% | -4.70% | -31.02% | 15.72% |
| post | LOW_VOL_252 (primary) | -6.51% | -45.44% | -1.86% | -9.25% | 15.72% |
| post | LOW_BETA_252 (primary) | -6.57% | -45.85% | -1.92% | -9.66% | 15.72% |
| post | AMIHUD_ILLIQ_63 (primary) | -6.82% | -52.96% | -2.18% | -16.78% | 15.72% |
| post | R0 (sensitivity) | -10.22% | -53.62% | -3.34% | -13.87% | 15.72% |
| post | R1 (sensitivity) | -10.50% | -54.45% | -3.63% | -14.71% | 15.72% |
| post | R2 (sensitivity) | -10.41% | -54.36% | -3.53% | -14.62% | 15.72% |
| post | MOM_12_1 (sensitivity) | -1.59% | -15.72% | 3.06% | 20.46% | 15.72% |
| post | HIGH_52W (sensitivity) | -6.22% | -44.58% | -1.57% | -8.40% | 15.72% |
| post | REV_1M (sensitivity) | -10.30% | -72.20% | -5.65% | -36.02% | 15.72% |
| post | LOW_VOL_252 (sensitivity) | -6.62% | -46.16% | -1.97% | -9.98% | 15.72% |
| post | LOW_BETA_252 (sensitivity) | -6.67% | -46.51% | -2.02% | -10.32% | 15.72% |
| post | AMIHUD_ILLIQ_63 (sensitivity) | -6.97% | -53.85% | -2.32% | -17.67% | 15.72% |

## Benchmarks (primary run)

| Segment | Benchmark | Window | Months | Ann. mean | Sharpe (RF) | Max drawdown |
| --- | --- | --- | --- | --- | --- | --- |
| pre | spy | sleeve_months | 62 | 11.36% | 0.895 | -13.53% |
| pre | spy | comparison_months | 55 | 10.41% | 0.775 | -13.53% |
| pre | equal_weight_pit | sleeve_months | 62 | 8.50% | 0.616 | -13.79% |
| pre | equal_weight_pit | comparison_months | 55 | 7.35% | 0.501 | -13.79% |
| post | spy | sleeve_months | 59 | 12.90% | 0.582 | -23.93% |
| post | spy | comparison_months | 44 | 16.41% | 0.798 | -12.95% |
| post | equal_weight_pit | sleeve_months | 59 | 8.25% | 0.286 | -21.97% |
| post | equal_weight_pit | comparison_months | 44 | 9.53% | 0.314 | -13.57% |

## Sleeves (primary run, sleeve months)

| Segment | Sleeve | Cost case | Months | Ann. mean | Sharpe (RF) | Max drawdown | Avg monthly stock turnover | Avg monthly stock cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre | MOM_12_1 | primary | 62 | 4.74% | 0.320 | -18.08% | 0.541 | 0.03% |
| pre | MOM_12_1 | sensitivity | 62 | 4.41% | 0.294 | -18.15% | 0.541 | 0.05% |
| pre | HIGH_52W | primary | 62 | 4.38% | 0.337 | -14.95% | 1.082 | 0.05% |
| pre | HIGH_52W | sensitivity | 62 | 3.73% | 0.276 | -15.40% | 1.082 | 0.11% |
| pre | REV_1M | primary | 62 | 8.32% | 0.478 | -18.16% | 1.581 | 0.08% |
| pre | REV_1M | sensitivity | 62 | 7.36% | 0.418 | -18.64% | 1.581 | 0.16% |
| pre | LOW_VOL_252 | primary | 62 | 10.88% | 1.040 | -7.48% | 0.178 | 0.01% |
| pre | LOW_VOL_252 | sensitivity | 62 | 10.78% | 1.029 | -7.49% | 0.178 | 0.02% |
| pre | LOW_BETA_252 | primary | 62 | 4.43% | 0.384 | -9.84% | 0.181 | 0.01% |
| pre | LOW_BETA_252 | sensitivity | 62 | 4.32% | 0.373 | -9.90% | 0.181 | 0.02% |
| pre | AMIHUD_ILLIQ_63 | primary | 62 | 8.97% | 0.549 | -15.49% | 0.261 | 0.01% |
| pre | AMIHUD_ILLIQ_63 | sensitivity | 62 | 8.81% | 0.538 | -15.52% | 0.261 | 0.03% |
| post | MOM_12_1 | primary | 59 | 11.63% | 0.446 | -21.60% | 0.530 | 0.03% |
| post | MOM_12_1 | sensitivity | 59 | 11.31% | 0.428 | -21.85% | 0.530 | 0.05% |
| post | HIGH_52W | primary | 59 | 7.26% | 0.259 | -18.37% | 0.975 | 0.05% |
| post | HIGH_52W | sensitivity | 59 | 6.67% | 0.218 | -18.64% | 0.975 | 0.10% |
| post | REV_1M | primary | 59 | 3.55% | -0.002 | -24.71% | 1.581 | 0.08% |
| post | REV_1M | sensitivity | 59 | 2.60% | -0.053 | -25.24% | 1.581 | 0.16% |
| post | LOW_VOL_252 | primary | 59 | 6.39% | 0.215 | -14.22% | 0.188 | 0.01% |
| post | LOW_VOL_252 | sensitivity | 59 | 6.28% | 0.206 | -14.29% | 0.188 | 0.02% |
| post | LOW_BETA_252 | primary | 59 | 6.33% | 0.210 | -11.83% | 0.171 | 0.01% |
| post | LOW_BETA_252 | sensitivity | 59 | 6.23% | 0.202 | -11.85% | 0.171 | 0.02% |
| post | AMIHUD_ILLIQ_63 | primary | 59 | 6.07% | 0.132 | -25.25% | 0.244 | 0.01% |
| post | AMIHUD_ILLIQ_63 | sensitivity | 59 | 5.92% | 0.125 | -25.33% | 0.244 | 0.02% |

## Mean Class-Layer Weights (primary run, primary cost case)

| Segment | Rule | MOM_12_1 | HIGH_52W | REV_1M | LOW_VOL_252 | LOW_BETA_252 | AMIHUD_ILLIQ_63 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pre | R0 | 0.167 | 0.167 | 0.167 | 0.167 | 0.167 | 0.167 |
| pre | R1 | 0.145 | 0.169 | 0.139 | 0.204 | 0.195 | 0.148 |
| pre | R2 | 0.142 | 0.166 | 0.142 | 0.204 | 0.194 | 0.151 |
| post | R0 | 0.167 | 0.167 | 0.167 | 0.167 | 0.167 | 0.167 |
| post | R1 | 0.143 | 0.187 | 0.122 | 0.207 | 0.211 | 0.130 |
| post | R2 | 0.157 | 0.205 | 0.142 | 0.171 | 0.173 | 0.152 |

## Transmission (descriptive; primary run, primary cost case)

| Segment | Sleeve or class | Months | PIT mean active | Public mean | Ratio | Correlation |
| --- | --- | --- | --- | --- | --- | --- |
| pre | MOM_12_1 | 62 | -0.31% | 0.26% | -1.199 | 0.828 |
| pre | HIGH_52W | 62 | -0.34% | 0.42% | -0.818 | 0.824 |
| pre | REV_1M | 62 | -0.02% | 0.39% | -0.038 | 0.859 |
| pre | LOW_VOL_252 | 62 | 0.20% | 0.54% | 0.369 | 0.734 |
| pre | LOW_BETA_252 | 62 | -0.34% | 0.42% | -0.802 | 0.906 |
| pre | AMIHUD_ILLIQ_63 | 62 | 0.04% | -0.28% | -0.143 | 0.511 |
| post | MOM_12_1 | 52 | 0.19% | 0.69% | 0.275 | 0.788 |
| post | HIGH_52W | 52 | -0.09% | 0.97% | -0.090 | 0.742 |
| post | REV_1M | 52 | -0.39% | -0.60% | 0.653 | 0.735 |
| post | LOW_VOL_252 | 52 | -0.15% | 0.58% | -0.251 | 0.771 |
| post | LOW_BETA_252 | 52 | -0.08% | -0.38% | 0.209 | 0.886 |
| post | AMIHUD_ILLIQ_63 | 52 | -0.22% | -0.60% | 0.365 | 0.437 |
| pooled | MOM_12_1 | 114 | -0.08% | 0.46% | -0.183 | 0.808 |
| pooled | HIGH_52W | 114 | -0.23% | 0.67% | -0.337 | 0.781 |
| pooled | REV_1M | 114 | -0.19% | -0.06% | 3.125 | 0.787 |
| pooled | LOW_VOL_252 | 114 | 0.04% | 0.56% | 0.075 | 0.745 |
| pooled | LOW_BETA_252 | 114 | -0.22% | 0.05% | -4.058 | 0.882 |
| pooled | AMIHUD_ILLIQ_63 | 114 | -0.08% | -0.42% | 0.185 | 0.474 |
| pre | class Momentum | 55 | -0.40% | 0.19% | -2.063 | 0.849 |
| pre | class Short-Term Reversal | 55 | 0.07% | 0.17% | 0.404 | 0.415 |
| pre | class Low Risk | 55 | -0.08% | 0.28% | -0.266 | 0.825 |
| pre | class Size | 55 | 0.12% | -0.03% | -3.952 | 0.547 |
| post | class Momentum | 44 | -0.03% | 0.29% | -0.102 | 0.853 |
| post | class Short-Term Reversal | 44 | -0.36% | -0.16% | 2.223 | 0.389 |
| post | class Low Risk | 44 | -0.41% | -0.26% | 1.547 | 0.839 |
| post | class Size | 44 | -0.22% | -0.20% | 1.111 | 0.474 |

## R4 Affected Events

| Run | Segment | Book | Events (count) | Incoming weight sum | Max | Seal-gap events | Outside comparison months |
| --- | --- | --- | --- | --- | --- | --- | --- |
| primary | pre | MOM_12_1 (primary) | 16 | 0.2195 | 0.0144 | 0 | 0 |
| primary | pre | MOM_12_1 (sensitivity) | 16 | 0.2195 | 0.0144 | 0 | 0 |
| primary | pre | HIGH_52W (primary) | 18 | 0.2470 | 0.0145 | 0 | 0 |
| primary | pre | HIGH_52W (sensitivity) | 18 | 0.2470 | 0.0145 | 0 | 0 |
| primary | pre | REV_1M (primary) | 2 | 0.0263 | 0.0136 | 0 | 0 |
| primary | pre | REV_1M (sensitivity) | 2 | 0.0263 | 0.0136 | 0 | 0 |
| primary | pre | LOW_VOL_252 (primary) | 5 | 0.0674 | 0.0143 | 0 | 0 |
| primary | pre | LOW_VOL_252 (sensitivity) | 5 | 0.0674 | 0.0143 | 0 | 0 |
| primary | pre | LOW_BETA_252 (primary) | 16 | 0.2164 | 0.0146 | 0 | 0 |
| primary | pre | LOW_BETA_252 (sensitivity) | 16 | 0.2164 | 0.0146 | 0 | 0 |
| primary | pre | AMIHUD_ILLIQ_63 (primary) | 4 | 0.0511 | 0.0134 | 0 | 0 |
| primary | pre | AMIHUD_ILLIQ_63 (sensitivity) | 4 | 0.0511 | 0.0134 | 0 | 0 |
| primary | pre | equal_weight_pit | 30 | 0.0821 | 0.0030 | 0 | 0 |
| primary | pre | R0 (primary) | 26 unique, 61 incidences | 0.1384 | 0.0093 | 0 | rule level: comparison months only |
| primary | pre | R1 (primary) | 26 unique, 61 incidences | 0.1444 | 0.0107 | 0 | rule level: comparison months only |
| primary | pre | R2 (primary) | 26 unique, 61 incidences | 0.1420 | 0.0102 | 0 | rule level: comparison months only |
| primary | pre | R0 (sensitivity) | 26 unique, 61 incidences | 0.1384 | 0.0093 | 0 | rule level: comparison months only |
| primary | pre | R1 (sensitivity) | 26 unique, 61 incidences | 0.1444 | 0.0107 | 0 | rule level: comparison months only |
| primary | pre | R2 (sensitivity) | 26 unique, 61 incidences | 0.1420 | 0.0102 | 0 | rule level: comparison months only |
| primary | post | MOM_12_1 (primary) | 9 | 0.1039 | 0.0126 | 0 | 4 |
| primary | post | MOM_12_1 (sensitivity) | 9 | 0.1039 | 0.0126 | 0 | 4 |
| primary | post | HIGH_52W (primary) | 9 | 0.1053 | 0.0120 | 0 | 3 |
| primary | post | HIGH_52W (sensitivity) | 9 | 0.1053 | 0.0120 | 0 | 3 |
| primary | post | REV_1M (primary) | 5 | 0.0587 | 0.0121 | 0 | 2 |
| primary | post | REV_1M (sensitivity) | 5 | 0.0587 | 0.0121 | 0 | 2 |
| primary | post | LOW_VOL_252 (primary) | 4 | 0.0478 | 0.0123 | 0 | 1 |
| primary | post | LOW_VOL_252 (sensitivity) | 4 | 0.0478 | 0.0123 | 0 | 1 |
| primary | post | LOW_BETA_252 (primary) | 9 | 0.1059 | 0.0122 | 0 | 2 |
| primary | post | LOW_BETA_252 (sensitivity) | 9 | 0.1059 | 0.0122 | 0 | 2 |
| primary | post | AMIHUD_ILLIQ_63 (primary) | 3 | 0.0329 | 0.0113 | 0 | 2 |
| primary | post | AMIHUD_ILLIQ_63 (sensitivity) | 3 | 0.0329 | 0.0113 | 0 | 2 |
| primary | post | equal_weight_pit | 27 | 0.0623 | 0.0027 | 0 | 9 |
| primary | post | R0 (primary) | 14 unique, 25 incidences | 0.0492 | 0.0078 | 0 | rule level: comparison months only |
| primary | post | R1 (primary) | 14 unique, 25 incidences | 0.0517 | 0.0088 | 0 | rule level: comparison months only |
| primary | post | R2 (primary) | 14 unique, 25 incidences | 0.0517 | 0.0079 | 0 | rule level: comparison months only |
| primary | post | R0 (sensitivity) | 14 unique, 25 incidences | 0.0492 | 0.0078 | 0 | rule level: comparison months only |
| primary | post | R1 (sensitivity) | 14 unique, 25 incidences | 0.0517 | 0.0088 | 0 | rule level: comparison months only |
| primary | post | R2 (sensitivity) | 14 unique, 25 incidences | 0.0517 | 0.0079 | 0 | rule level: comparison months only |
| last_close | pre | MOM_12_1 (primary) | 16 | 0.2193 | 0.0144 | 0 | 0 |
| last_close | pre | MOM_12_1 (sensitivity) | 16 | 0.2193 | 0.0144 | 0 | 0 |
| last_close | pre | HIGH_52W (primary) | 18 | 0.2464 | 0.0144 | 0 | 0 |
| last_close | pre | HIGH_52W (sensitivity) | 18 | 0.2464 | 0.0144 | 0 | 0 |
| last_close | pre | REV_1M (primary) | 2 | 0.0263 | 0.0136 | 0 | 0 |
| last_close | pre | REV_1M (sensitivity) | 2 | 0.0263 | 0.0136 | 0 | 0 |
| last_close | pre | LOW_VOL_252 (primary) | 5 | 0.0674 | 0.0143 | 0 | 0 |
| last_close | pre | LOW_VOL_252 (sensitivity) | 5 | 0.0674 | 0.0143 | 0 | 0 |
| last_close | pre | LOW_BETA_252 (primary) | 16 | 0.2160 | 0.0146 | 0 | 0 |
| last_close | pre | LOW_BETA_252 (sensitivity) | 16 | 0.2160 | 0.0146 | 0 | 0 |
| last_close | pre | AMIHUD_ILLIQ_63 (primary) | 4 | 0.0511 | 0.0134 | 0 | 0 |
| last_close | pre | AMIHUD_ILLIQ_63 (sensitivity) | 4 | 0.0511 | 0.0134 | 0 | 0 |
| last_close | pre | equal_weight_pit | 30 | 0.0820 | 0.0030 | 0 | 0 |
| last_close | pre | R0 (primary) | 26 unique, 61 incidences | 0.1382 | 0.0093 | 0 | rule level: comparison months only |
| last_close | pre | R1 (primary) | 26 unique, 61 incidences | 0.1454 | 0.0107 | 0 | rule level: comparison months only |
| last_close | pre | R2 (primary) | 26 unique, 61 incidences | 0.1431 | 0.0102 | 0 | rule level: comparison months only |
| last_close | pre | R0 (sensitivity) | 26 unique, 61 incidences | 0.1382 | 0.0093 | 0 | rule level: comparison months only |
| last_close | pre | R1 (sensitivity) | 26 unique, 61 incidences | 0.1454 | 0.0107 | 0 | rule level: comparison months only |
| last_close | pre | R2 (sensitivity) | 26 unique, 61 incidences | 0.1430 | 0.0102 | 0 | rule level: comparison months only |
| last_close | post | MOM_12_1 (primary) | 9 | 0.1036 | 0.0126 | 0 | 4 |
| last_close | post | MOM_12_1 (sensitivity) | 9 | 0.1036 | 0.0126 | 0 | 4 |
| last_close | post | HIGH_52W (primary) | 9 | 0.1053 | 0.0120 | 0 | 3 |
| last_close | post | HIGH_52W (sensitivity) | 9 | 0.1053 | 0.0120 | 0 | 3 |
| last_close | post | REV_1M (primary) | 5 | 0.0587 | 0.0121 | 0 | 2 |
| last_close | post | REV_1M (sensitivity) | 5 | 0.0587 | 0.0121 | 0 | 2 |
| last_close | post | LOW_VOL_252 (primary) | 4 | 0.0478 | 0.0123 | 0 | 1 |
| last_close | post | LOW_VOL_252 (sensitivity) | 4 | 0.0478 | 0.0123 | 0 | 1 |
| last_close | post | LOW_BETA_252 (primary) | 9 | 0.1059 | 0.0122 | 0 | 2 |
| last_close | post | LOW_BETA_252 (sensitivity) | 9 | 0.1059 | 0.0122 | 0 | 2 |
| last_close | post | AMIHUD_ILLIQ_63 (primary) | 3 | 0.0329 | 0.0113 | 0 | 2 |
| last_close | post | AMIHUD_ILLIQ_63 (sensitivity) | 3 | 0.0329 | 0.0113 | 0 | 2 |
| last_close | post | equal_weight_pit | 27 | 0.0622 | 0.0027 | 0 | 9 |
| last_close | post | R0 (primary) | 14 unique, 25 incidences | 0.0491 | 0.0078 | 0 | rule level: comparison months only |
| last_close | post | R1 (primary) | 14 unique, 25 incidences | 0.0516 | 0.0088 | 0 | rule level: comparison months only |
| last_close | post | R2 (primary) | 14 unique, 25 incidences | 0.0516 | 0.0079 | 0 | rule level: comparison months only |
| last_close | post | R0 (sensitivity) | 14 unique, 25 incidences | 0.0491 | 0.0078 | 0 | rule level: comparison months only |
| last_close | post | R1 (sensitivity) | 14 unique, 25 incidences | 0.0516 | 0.0088 | 0 | rule level: comparison months only |
| last_close | post | R2 (sensitivity) | 14 unique, 25 incidences | 0.0516 | 0.0079 | 0 | rule level: comparison months only |

Residual stops per segment: pre 30 (seal-gap 0); post 27 (seal-gap 0).

## Missingness

- pre: 181055 of 650629 member-days unpriced (27.83%); undated intervals 1 (upper bound 27.97%); by exit class index_removal_still_trading 130078, delisting_candidate 13212, disappearance_outside_membership 2806, seal_gap_identity_split 0, unresolved_no_permanent_id 34959, unknown 0; by reason eod_quarantine 34342, episode_panel_refusal 111754, identity_refusal 5348, no_bars_in_interval 9188, no_vendor_bars 6347, other 14076.
- post: 98244 of 624854 member-days unpriced (15.72%); undated intervals 1 (upper bound 15.89%); by exit class index_removal_still_trading 83718, delisting_candidate 1239, disappearance_outside_membership 0, seal_gap_identity_split 0, unresolved_no_permanent_id 13287, unknown 0; by reason eod_quarantine 1239, episode_panel_refusal 82479, identity_refusal 9802, no_bars_in_interval 2, no_vendor_bars 730, other 3992.
- pre signal exclusions (eligible, no finite signal): MOM_12_1 131, HIGH_52W 131, REV_1M 7, LOW_VOL_252 131, LOW_BETA_252 131, AMIHUD_ILLIQ_63 75.
- post signal exclusions (eligible, no finite signal): MOM_12_1 67, HIGH_52W 78, REV_1M 2, LOW_VOL_252 79, LOW_BETA_252 79, AMIHUD_ILLIQ_63 24.
- pre unmarked halt rows and locked execution rows (primary cost case): MOM_12_1 0 and 0, HIGH_52W 0 and 0, REV_1M 0 and 0, LOW_VOL_252 0 and 0, LOW_BETA_252 0 and 0, AMIHUD_ILLIQ_63 0 and 0.
- post unmarked halt rows and locked execution rows (primary cost case): MOM_12_1 0 and 0, HIGH_52W 0 and 0, REV_1M 1 and 0, LOW_VOL_252 0 and 0, LOW_BETA_252 0 and 0, AMIHUD_ILLIQ_63 0 and 0.

## Windows

- pre: comparison months primary 2014-12 to 2019-06 (55); sensitivity 2014-12 to 2019-06 (55); sleeve months 2014-05 to 2019-06 (62).
- post: comparison months primary 2022-05 to 2025-12 (44); sensitivity 2022-05 to 2025-12 (44); sleeve months 2021-09 to 2026-07 (59).

## Method and Provenance

- Specification: `docs/preregistrations/m5_trial_family_v1_amendment_4.json` revision 2 (SHA-256 `c2b1f8dea064ef1852d55bfda365faef8bd1c658897877037aae2fc0714ac617`) with v1 and amendments 1 to 3; the runner refuses unless all five match HEAD and their pins.
- Code commit `d0f05dbc01a14c656008b94ed9795d857db8c9f2`; tracked changes at run time: False.
- Data: the local `real_v2` snapshot, bound by the SHA-256 pins in `reports/m5_step4.json` (snapshot.pins) and the recomputed discovery inputs; public inputs from `reports/m5_public_data_manifest.json` (SHA-256 `ba025b1a67af175dfff892c3dcefe96b573f7542b6d365dcdc783353c2af998f`). Nothing under the snapshot's terminal directory is read, and the seal window stays unaccessed.
- Timing: `after_close_signal_next_observed_close_v1`. A sleeve signal uses row r - 1, executes at the close of month-end row r, and first earns row r + 1. Class weights for month t use inputs through month t-2, execute at the month t-1 close, and earn month t.
- Costs: stock 1 + 4 bp (primary) or 2 + 8 bp (sensitivity) on traded notional inside each sleeve; a class switch cost of 20 or 50 bp on drift-adjusted class turnover; no borrow (long only); the equal-weight benchmark and SPY are cost-free.
- Sample reuse: every comparison re-examines months or factors seen in M4.7 or in steps 2 and 3; the S4 family counts 478 prior slots.


## Limitations

- Costs do not net across sleeves and include no market-impact model; the switch cost is a proxy.
- Rule R1 uses a 126-day sigma, not the v1 36-month window.
- About 99 comparison months give little power; the pooled HAC treats the segment boundary as adjacent.
- R2's multipliers come from public long-short data and are not re-estimated on stock-level books.
- Four of 13 themes are covered; the public counterpart is the 153-factor book.
- All six source papers predate 2014, so every month is post-publication.

