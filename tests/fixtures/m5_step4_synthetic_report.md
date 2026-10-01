# Milestone 5 Step 4: Price-Class Bridge on Point-in-Time S&P 500 Books

**Evidence ceiling: `DIAGNOSTIC_ONLY`.** Simulated research on the local `real_v2` snapshot; no profitability claim. Aggregates only.

- **VP-2.** Premise VP-2 (the vendor's adjusted close applies each declared distribution) holds under owner decision O-9 for step 4 only; the M4.8 census measured S_D > 0.05 on 22.5 percent of eligible member-days.
- **R4.** No terminal evidence is accepted. Every residual held stop settles at -100 percent in every sleeve and in the equal-weight benchmark; a last-close rerun is reported beside it.
- **Fragility: FRAGILE** (7 sign changes between the -100 percent run and the last-close rerun; outcome changes: baseline).
- **Unpriced members** are never held. Unpriced member-day share: . 111 of 448 members at D0_pre have no pre-side panel (Stage D count).
- **Missing crash.** The seal window and its buffers exclude 2019-07 to 2021-08, including the 2020 crash, so drawdowns are understated.
- **Prior exposure.** The post segment re-examines M4.7 factors and months; only 2014-05 to 2016-07 is unexposed. No result is confirmatory.

## Decision Outcomes (primary run)

- Point-in-time baseline product: **R0**. Rule R1 against R0: 6 of 8 on point-in-time books, 6 of 8 on public books over the same months.
- R2: **closed**. R2 against rule R1: 1 of 8 on point-in-time books, 5 of 8 on public books over the same months; R2 against R0: 5 of 8 on point-in-time books, 5 of 8 on public books over the same months.
- Fragility: **FRAGILE**. Sign changes: S4.R2, R1_vs_R0:pre:primary:max_drawdown, R1_vs_R0:pre:sensitivity:max_drawdown, R2_vs_R1:pre:primary:max_drawdown, R2_vs_R0:pre:primary:max_drawdown, R2_vs_R0:pre:sensitivity:max_drawdown, R2_vs_R0:pre:sensitivity:sharpe.
- Last-close rerun: baseline R1, R2 closed.
- S4 q-values and the fragility label are reported beside the outcomes and do not change them.

## Survival: Point-in-Time Conditions Beside the Public Margins

### Rule R1 against R0: 6 of 8 hold on point-in-time books (6 of 8 on public books over the same months)

| Segment | Cost case | Metric | PIT margin | PIT holds | Public margin | Public holds | Ratio | Last-close margin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre | primary | max_drawdown | -0.0195 | no | 0.0150 | yes | -1.304 | 0.0031 |
| pre | primary | sharpe | 0.0198 | yes | 0.0647 | yes | 0.306 | 0.2936 |
| pre | sensitivity | max_drawdown | -0.0195 | no | 0.0114 | yes | -1.707 | 0.0030 |
| pre | sensitivity | sharpe | 0.0031 | yes | -0.2143 | no | n/a | 0.2853 |
| post | primary | max_drawdown | 0.0125 | yes | 0.0030 | yes | 4.190 | 0.0125 |
| post | primary | sharpe | 0.2472 | yes | 0.5384 | yes | 0.459 | 0.2472 |
| post | sensitivity | max_drawdown | 0.0123 | yes | 0.0092 | yes | 1.336 | 0.0123 |
| post | sensitivity | sharpe | 0.2251 | yes | -0.1800 | no | n/a | 0.2251 |

### R2 against rule R1: 1 of 8 hold on point-in-time books (5 of 8 on public books over the same months)

| Segment | Cost case | Metric | PIT margin | PIT holds | Public margin | Public holds | Ratio | Last-close margin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre | primary | max_drawdown | -0.0037 | no | 0.0478 | yes | -0.078 | 0.0006 |
| pre | primary | sharpe | 0.0236 | yes | 2.1779 | yes | 0.011 | 0.0439 |
| pre | sensitivity | max_drawdown | -0.0039 | no | 0.0099 | yes | -0.392 | -0.0009 |
| pre | sensitivity | sharpe | -0.0330 | no | 0.8390 | yes | -0.039 | -0.0581 |
| post | primary | max_drawdown | -0.0017 | no | -0.0081 | no | n/a | -0.0017 |
| post | primary | sharpe | -0.0188 | no | 0.1070 | yes | -0.176 | -0.0188 |
| post | sensitivity | max_drawdown | -0.0031 | no | -0.0203 | no | n/a | -0.0031 |
| post | sensitivity | sharpe | -0.1056 | no | -0.3192 | no | n/a | -0.1056 |

### R2 against R0: 5 of 8 hold on point-in-time books (5 of 8 on public books over the same months)

| Segment | Cost case | Metric | PIT margin | PIT holds | Public margin | Public holds | Ratio | Last-close margin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre | primary | max_drawdown | -0.0232 | no | 0.0628 | yes | -0.370 | 0.0037 |
| pre | primary | sharpe | 0.0434 | yes | 2.2426 | yes | 0.019 | 0.3375 |
| pre | sensitivity | max_drawdown | -0.0234 | no | 0.0213 | yes | -1.097 | 0.0021 |
| pre | sensitivity | sharpe | -0.0298 | no | 0.6248 | yes | -0.048 | 0.2272 |
| post | primary | max_drawdown | 0.0107 | yes | -0.0051 | no | n/a | 0.0107 |
| post | primary | sharpe | 0.2284 | yes | 0.6454 | yes | 0.354 | 0.2284 |
| post | sensitivity | max_drawdown | 0.0092 | yes | -0.0111 | no | n/a | 0.0092 |
| post | sensitivity | sharpe | 0.1195 | yes | -0.4992 | no | n/a | 0.1195 |

Sharpe on point-in-time books is 12 x mean(r_net - RF) / (sqrt(12) x sd(r_net)); the public long-short books keep the v1 Sharpe without RF. Drawdown margins are R1 magnitude minus candidate magnitude.

## S4 Tests (primary run, primary cost case, pooled comparison months)

| Test | Months | Mean monthly | 95% interval (monthly) | HAC p | BY q (family 480) | Last-close mean |
| --- | --- | --- | --- | --- | --- | --- |
| S4.R1 | 31 | 0.06% | -0.14% to 0.25% | 0.572 | 1.000 | 0.10% |
| S4.R2 | 31 | 0.01% | -0.07% to 0.09% | 0.840 | 1.000 | -0.00% |

The BY family counts 2 observed tests and 478 prior slots at p = 1. The last-close rerun reports means and signs only. With 480 slots the smallest p-value needs about 1.5e-5 to reach q 0.05.

## Rule Metrics (primary run)

| Segment | Cost case | Rule | Months | Ann. mean | Volatility | Sharpe (RF) | Max drawdown | Avg switch turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre | primary | R0 | 17 | 4.48% | 10.51% | 0.312 | -7.69% | 0.083 |
| pre | primary | R1 | 17 | 5.04% | 11.57% | 0.332 | -9.64% | 0.157 |
| pre | primary | R2 | 17 | 5.43% | 11.92% | 0.355 | -10.01% | 0.349 |
| pre | sensitivity | R0 | 17 | 3.78% | 10.51% | 0.245 | -7.73% | 0.083 |
| pre | sensitivity | R1 | 17 | 4.08% | 11.59% | 0.249 | -9.68% | 0.157 |
| pre | sensitivity | R2 | 17 | 3.76% | 11.89% | 0.216 | -10.07% | 0.349 |
| post | primary | R0 | 14 | 6.16% | 6.83% | 0.726 | -4.22% | 0.096 |
| post | primary | R1 | 14 | 6.96% | 5.92% | 0.973 | -2.97% | 0.106 |
| post | primary | R2 | 14 | 6.70% | 5.76% | 0.955 | -3.15% | 0.257 |
| post | sensitivity | R0 | 14 | 5.43% | 6.93% | 0.611 | -4.37% | 0.096 |
| post | sensitivity | R1 | 14 | 6.23% | 6.02% | 0.836 | -3.14% | 0.106 |
| post | sensitivity | R2 | 14 | 5.43% | 5.79% | 0.730 | -3.45% | 0.257 |

## Excess Over the Benchmarks (primary run)

| Segment | Book | Ann. excess vs SPY | Total excess vs SPY | Ann. excess vs EW | Total excess vs EW | Unpriced share |
| --- | --- | --- | --- | --- | --- | --- |
| pre | R0 (primary) | 16.52% | 28.01% | -4.28% | -7.11% | n/a |
| pre | R1 (primary) | 17.08% | 28.66% | -3.72% | -6.46% | n/a |
| pre | R2 (primary) | 17.48% | 29.20% | -3.33% | -5.92% | n/a |
| pre | MOM_12_1 (primary) | 39.72% | 85.44% | 10.01% | 22.90% | n/a |
| pre | HIGH_52W (primary) | 30.93% | 62.86% | 1.21% | 0.31% | n/a |
| pre | REV_1M (primary) | 33.80% | 71.17% | 4.09% | 8.62% | n/a |
| pre | LOW_VOL_252 (primary) | 24.08% | 47.95% | -5.64% | -14.60% | n/a |
| pre | LOW_BETA_252 (primary) | 24.51% | 49.24% | -5.20% | -13.30% | n/a |
| pre | AMIHUD_ILLIQ_63 (primary) | 21.64% | 42.23% | -8.07% | -20.31% | n/a |
| pre | R0 (sensitivity) | 15.82% | 26.97% | -4.98% | -8.15% | n/a |
| pre | R1 (sensitivity) | 16.12% | 27.23% | -4.68% | -7.89% | n/a |
| pre | R2 (sensitivity) | 15.81% | 26.71% | -5.00% | -8.41% | n/a |
| pre | MOM_12_1 (sensitivity) | 39.42% | 84.59% | 9.70% | 22.04% | n/a |
| pre | HIGH_52W (sensitivity) | 30.36% | 61.50% | 0.65% | -1.04% | n/a |
| pre | REV_1M (sensitivity) | 32.80% | 68.64% | 3.08% | 6.10% | n/a |
| pre | LOW_VOL_252 (sensitivity) | 23.93% | 47.63% | -5.79% | -14.92% | n/a |
| pre | LOW_BETA_252 (sensitivity) | 24.17% | 48.53% | -5.54% | -14.02% | n/a |
| pre | AMIHUD_ILLIQ_63 (sensitivity) | 21.43% | 41.81% | -8.29% | -20.74% | n/a |
| post | R0 (primary) | 13.12% | 22.07% | 0.64% | 0.68% | n/a |
| post | R1 (primary) | 13.92% | 23.14% | 1.44% | 1.75% | n/a |
| post | R2 (primary) | 13.66% | 22.82% | 1.18% | 1.43% | n/a |
| post | MOM_12_1 (primary) | 23.26% | 46.61% | -2.81% | -6.67% | n/a |
| post | HIGH_52W (primary) | 26.59% | 53.40% | 0.52% | 0.12% | n/a |
| post | REV_1M (primary) | 38.47% | 80.60% | 12.40% | 27.32% | n/a |
| post | LOW_VOL_252 (primary) | 26.08% | 53.29% | 0.01% | 0.01% | n/a |
| post | LOW_BETA_252 (primary) | 10.41% | 23.54% | -15.65% | -29.75% | n/a |
| post | AMIHUD_ILLIQ_63 (primary) | 31.74% | 62.39% | 5.68% | 9.11% | n/a |
| post | R0 (sensitivity) | 12.39% | 21.16% | -0.09% | -0.23% | n/a |
| post | R1 (sensitivity) | 13.20% | 22.22% | 0.72% | 0.83% | n/a |
| post | R2 (sensitivity) | 12.39% | 21.23% | -0.09% | -0.16% | n/a |
| post | MOM_12_1 (sensitivity) | 22.92% | 45.92% | -3.15% | -7.36% | n/a |
| post | HIGH_52W (sensitivity) | 26.04% | 52.25% | -0.02% | -1.04% | n/a |
| post | REV_1M (sensitivity) | 37.49% | 78.08% | 11.43% | 24.80% | n/a |
| post | LOW_VOL_252 (sensitivity) | 25.98% | 53.09% | -0.08% | -0.20% | n/a |
| post | LOW_BETA_252 (sensitivity) | 10.03% | 22.94% | -16.03% | -30.35% | n/a |
| post | AMIHUD_ILLIQ_63 (sensitivity) | 31.62% | 62.12% | 5.56% | 8.83% | n/a |

## Benchmarks (primary run)

| Segment | Benchmark | Window | Months | Ann. mean | Sharpe (RF) | Max drawdown |
| --- | --- | --- | --- | --- | --- | --- |
| pre | spy | sleeve_months | 24 | -20.13% | -0.586 | -57.13% |
| pre | spy | comparison_months | 17 | -12.04% | -0.391 | -37.39% |
| pre | equal_weight_pit | sleeve_months | 24 | 9.58% | 1.459 | -2.95% |
| pre | equal_weight_pit | comparison_months | 17 | 8.76% | 1.185 | -2.95% |
| post | spy | sleeve_months | 23 | -20.01% | -0.537 | -48.39% |
| post | spy | comparison_months | 14 | -6.96% | -0.211 | -33.56% |
| post | equal_weight_pit | sleeve_months | 23 | 6.06% | 0.867 | -3.13% |
| post | equal_weight_pit | comparison_months | 14 | 5.52% | 0.850 | -2.68% |

## Sleeves (primary run, sleeve months)

| Segment | Sleeve | Cost case | Months | Ann. mean | Sharpe (RF) | Max drawdown | Avg monthly stock turnover | Avg monthly stock cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre | MOM_12_1 | primary | 24 | 19.59% | 1.092 | -14.29% | 0.499 | 0.03% |
| pre | MOM_12_1 | sensitivity | 24 | 19.29% | 1.075 | -14.31% | 0.499 | 0.05% |
| pre | HIGH_52W | primary | 24 | 10.80% | 0.615 | -15.89% | 0.937 | 0.05% |
| pre | HIGH_52W | sensitivity | 24 | 10.24% | 0.578 | -15.95% | 0.937 | 0.09% |
| pre | REV_1M | primary | 24 | 13.67% | 0.984 | -13.43% | 1.644 | 0.08% |
| pre | REV_1M | sensitivity | 24 | 12.67% | 0.909 | -13.79% | 1.644 | 0.16% |
| pre | LOW_VOL_252 | primary | 24 | 3.95% | 0.197 | -17.25% | 0.252 | 0.01% |
| pre | LOW_VOL_252 | sensitivity | 24 | 3.80% | 0.186 | -17.28% | 0.252 | 0.03% |
| pre | LOW_BETA_252 | primary | 24 | 4.38% | 0.242 | -14.55% | 0.558 | 0.03% |
| pre | LOW_BETA_252 | sensitivity | 24 | 4.04% | 0.216 | -14.71% | 0.558 | 0.06% |
| pre | AMIHUD_ILLIQ_63 | primary | 24 | 1.51% | 0.019 | -20.24% | 0.353 | 0.02% |
| pre | AMIHUD_ILLIQ_63 | sensitivity | 24 | 1.30% | 0.006 | -20.43% | 0.353 | 0.04% |
| post | MOM_12_1 | primary | 23 | 3.25% | 0.188 | -11.21% | 0.572 | 0.03% |
| post | MOM_12_1 | sensitivity | 23 | 2.91% | 0.157 | -11.37% | 0.572 | 0.06% |
| post | HIGH_52W | primary | 23 | 6.58% | 0.474 | -10.86% | 0.902 | 0.05% |
| post | HIGH_52W | sensitivity | 23 | 6.04% | 0.425 | -11.02% | 0.902 | 0.09% |
| post | REV_1M | primary | 23 | 18.46% | 1.152 | -6.76% | 1.587 | 0.08% |
| post | REV_1M | sensitivity | 23 | 17.49% | 1.090 | -6.84% | 1.587 | 0.16% |
| post | LOW_VOL_252 | primary | 23 | 6.07% | 0.849 | -3.76% | 0.159 | 0.01% |
| post | LOW_VOL_252 | sensitivity | 23 | 5.97% | 0.832 | -3.87% | 0.159 | 0.02% |
| post | LOW_BETA_252 | primary | 23 | -9.60% | -0.981 | -24.68% | 0.635 | 0.03% |
| post | LOW_BETA_252 | sensitivity | 23 | -9.97% | -1.016 | -25.03% | 0.635 | 0.06% |
| post | AMIHUD_ILLIQ_63 | primary | 23 | 11.74% | 0.552 | -10.34% | 0.199 | 0.01% |
| post | AMIHUD_ILLIQ_63 | sensitivity | 23 | 11.61% | 0.546 | -10.36% | 0.199 | 0.02% |

## Mean Class-Layer Weights (primary run, primary cost case)

| Segment | Rule | MOM_12_1 | HIGH_52W | REV_1M | LOW_VOL_252 | LOW_BETA_252 | AMIHUD_ILLIQ_63 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pre | R0 | 0.167 | 0.167 | 0.167 | 0.167 | 0.167 | 0.167 |
| pre | R1 | 0.131 | 0.156 | 0.167 | 0.244 | 0.160 | 0.143 |
| pre | R2 | 0.128 | 0.153 | 0.192 | 0.239 | 0.159 | 0.129 |
| post | R0 | 0.167 | 0.167 | 0.167 | 0.167 | 0.167 | 0.167 |
| post | R1 | 0.151 | 0.189 | 0.132 | 0.291 | 0.130 | 0.107 |
| post | R2 | 0.154 | 0.193 | 0.129 | 0.298 | 0.133 | 0.092 |

## Transmission (descriptive; primary run, primary cost case)

| Segment | Sleeve or class | Months | PIT mean active | Public mean | Ratio | Correlation |
| --- | --- | --- | --- | --- | --- | --- |
| pre | MOM_12_1 | 24 | 0.83% | 0.04% | 19.663 | 0.009 |
| pre | HIGH_52W | 24 | 0.10% | 0.67% | 0.151 | 0.013 |
| pre | REV_1M | 24 | 0.34% | 0.32% | 1.057 | 0.376 |
| pre | LOW_VOL_252 | 24 | -0.47% | 0.41% | -1.155 | -0.122 |
| pre | LOW_BETA_252 | 24 | -0.43% | 0.39% | -1.101 | 0.059 |
| pre | AMIHUD_ILLIQ_63 | 24 | -0.67% | 0.31% | -2.195 | -0.343 |
| post | MOM_12_1 | 21 | -0.14% | 0.83% | -0.170 | 0.106 |
| post | HIGH_52W | 21 | 0.35% | 0.18% | 1.966 | -0.332 |
| post | REV_1M | 21 | 1.13% | 0.46% | 2.443 | 0.057 |
| post | LOW_VOL_252 | 21 | 0.01% | 0.57% | 0.020 | -0.116 |
| post | LOW_BETA_252 | 21 | -1.21% | 0.30% | -4.089 | -0.053 |
| post | AMIHUD_ILLIQ_63 | 21 | 0.57% | 0.33% | 1.699 | 0.097 |
| pooled | MOM_12_1 | 45 | 0.38% | 0.41% | 0.919 | 0.012 |
| pooled | HIGH_52W | 45 | 0.22% | 0.44% | 0.496 | -0.154 |
| pooled | REV_1M | 45 | 0.71% | 0.39% | 1.828 | 0.237 |
| pooled | LOW_VOL_252 | 45 | -0.25% | 0.48% | -0.507 | -0.105 |
| pooled | LOW_BETA_252 | 45 | -0.79% | 0.35% | -2.284 | 0.013 |
| pooled | AMIHUD_ILLIQ_63 | 45 | -0.09% | 0.32% | -0.295 | -0.086 |
| pre | class Momentum | 17 | 0.14% | 0.30% | 0.476 | -0.159 |
| pre | class Short-Term Reversal | 17 | 0.68% | -0.36% | -1.896 | 0.038 |
| pre | class Low Risk | 17 | -0.68% | 0.10% | -6.857 | -0.020 |
| pre | class Size | 17 | -1.15% | 0.55% | -2.118 | -0.169 |
| post | class Momentum | 14 | 0.23% | 1.35% | 0.174 | -0.063 |
| post | class Short-Term Reversal | 14 | 0.80% | 0.06% | 13.216 | 0.210 |
| post | class Low Risk | 14 | -0.01% | -0.21% | 0.024 | -0.282 |
| post | class Size | 14 | -0.35% | -0.11% | 3.191 | -0.458 |

## R4 Affected Events

| Run | Segment | Book | Events (count) | Incoming weight sum | Max | Seal-gap events | Outside comparison months |
| --- | --- | --- | --- | --- | --- | --- | --- |
| primary | pre | MOM_12_1 (primary) | 1 | 0.1655 | 0.1655 | 1 | 0 |
| primary | pre | MOM_12_1 (sensitivity) | 1 | 0.1655 | 0.1655 | 1 | 0 |
| primary | pre | HIGH_52W (primary) | 1 | 0.1674 | 0.1674 | 1 | 0 |
| primary | pre | HIGH_52W (sensitivity) | 1 | 0.1674 | 0.1674 | 1 | 0 |
| primary | pre | REV_1M (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | pre | REV_1M (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | pre | LOW_VOL_252 (primary) | 1 | 0.1691 | 0.1691 | 1 | 0 |
| primary | pre | LOW_VOL_252 (sensitivity) | 1 | 0.1691 | 0.1691 | 1 | 0 |
| primary | pre | LOW_BETA_252 (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | pre | LOW_BETA_252 (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | pre | AMIHUD_ILLIQ_63 (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | pre | AMIHUD_ILLIQ_63 (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | pre | equal_weight_pit | 1 | 0.0341 | 0.0341 | 1 | 0 |
| primary | pre | R0 (primary) | 1 unique, 3 incidences | 0.0855 | 0.0855 | 1 | rule level: comparison months only |
| primary | pre | R1 (primary) | 1 unique, 3 incidences | 0.1062 | 0.1062 | 1 | rule level: comparison months only |
| primary | pre | R2 (primary) | 1 unique, 3 incidences | 0.1109 | 0.1109 | 1 | rule level: comparison months only |
| primary | pre | R0 (sensitivity) | 1 unique, 3 incidences | 0.0855 | 0.0855 | 1 | rule level: comparison months only |
| primary | pre | R1 (sensitivity) | 1 unique, 3 incidences | 0.1061 | 0.1061 | 1 | rule level: comparison months only |
| primary | pre | R2 (sensitivity) | 1 unique, 3 incidences | 0.1109 | 0.1109 | 1 | rule level: comparison months only |
| primary | post | MOM_12_1 (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | post | MOM_12_1 (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | post | HIGH_52W (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | post | HIGH_52W (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | post | REV_1M (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | post | REV_1M (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | post | LOW_VOL_252 (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | post | LOW_VOL_252 (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | post | LOW_BETA_252 (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | post | LOW_BETA_252 (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | post | AMIHUD_ILLIQ_63 (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | post | AMIHUD_ILLIQ_63 (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | post | equal_weight_pit | 0 | 0.0000 | 0.0000 | 0 | 0 |
| primary | post | R0 (primary) | 0 unique, 0 incidences | 0.0000 | 0.0000 | 0 | rule level: comparison months only |
| primary | post | R1 (primary) | 0 unique, 0 incidences | 0.0000 | 0.0000 | 0 | rule level: comparison months only |
| primary | post | R2 (primary) | 0 unique, 0 incidences | 0.0000 | 0.0000 | 0 | rule level: comparison months only |
| primary | post | R0 (sensitivity) | 0 unique, 0 incidences | 0.0000 | 0.0000 | 0 | rule level: comparison months only |
| primary | post | R1 (sensitivity) | 0 unique, 0 incidences | 0.0000 | 0.0000 | 0 | rule level: comparison months only |
| primary | post | R2 (sensitivity) | 0 unique, 0 incidences | 0.0000 | 0.0000 | 0 | rule level: comparison months only |
| last_close | pre | MOM_12_1 (primary) | 1 | 0.1655 | 0.1655 | 1 | 0 |
| last_close | pre | MOM_12_1 (sensitivity) | 1 | 0.1655 | 0.1655 | 1 | 0 |
| last_close | pre | HIGH_52W (primary) | 1 | 0.1674 | 0.1674 | 1 | 0 |
| last_close | pre | HIGH_52W (sensitivity) | 1 | 0.1674 | 0.1674 | 1 | 0 |
| last_close | pre | REV_1M (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | pre | REV_1M (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | pre | LOW_VOL_252 (primary) | 1 | 0.1691 | 0.1691 | 1 | 0 |
| last_close | pre | LOW_VOL_252 (sensitivity) | 1 | 0.1691 | 0.1691 | 1 | 0 |
| last_close | pre | LOW_BETA_252 (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | pre | LOW_BETA_252 (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | pre | AMIHUD_ILLIQ_63 (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | pre | AMIHUD_ILLIQ_63 (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | pre | equal_weight_pit | 1 | 0.0341 | 0.0341 | 1 | 0 |
| last_close | pre | R0 (primary) | 1 unique, 3 incidences | 0.0855 | 0.0855 | 1 | rule level: comparison months only |
| last_close | pre | R1 (primary) | 1 unique, 3 incidences | 0.1062 | 0.1062 | 1 | rule level: comparison months only |
| last_close | pre | R2 (primary) | 1 unique, 3 incidences | 0.1109 | 0.1109 | 1 | rule level: comparison months only |
| last_close | pre | R0 (sensitivity) | 1 unique, 3 incidences | 0.0855 | 0.0855 | 1 | rule level: comparison months only |
| last_close | pre | R1 (sensitivity) | 1 unique, 3 incidences | 0.1061 | 0.1061 | 1 | rule level: comparison months only |
| last_close | pre | R2 (sensitivity) | 1 unique, 3 incidences | 0.1109 | 0.1109 | 1 | rule level: comparison months only |
| last_close | post | MOM_12_1 (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | post | MOM_12_1 (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | post | HIGH_52W (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | post | HIGH_52W (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | post | REV_1M (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | post | REV_1M (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | post | LOW_VOL_252 (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | post | LOW_VOL_252 (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | post | LOW_BETA_252 (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | post | LOW_BETA_252 (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | post | AMIHUD_ILLIQ_63 (primary) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | post | AMIHUD_ILLIQ_63 (sensitivity) | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | post | equal_weight_pit | 0 | 0.0000 | 0.0000 | 0 | 0 |
| last_close | post | R0 (primary) | 0 unique, 0 incidences | 0.0000 | 0.0000 | 0 | rule level: comparison months only |
| last_close | post | R1 (primary) | 0 unique, 0 incidences | 0.0000 | 0.0000 | 0 | rule level: comparison months only |
| last_close | post | R2 (primary) | 0 unique, 0 incidences | 0.0000 | 0.0000 | 0 | rule level: comparison months only |
| last_close | post | R0 (sensitivity) | 0 unique, 0 incidences | 0.0000 | 0.0000 | 0 | rule level: comparison months only |
| last_close | post | R1 (sensitivity) | 0 unique, 0 incidences | 0.0000 | 0.0000 | 0 | rule level: comparison months only |
| last_close | post | R2 (sensitivity) | 0 unique, 0 incidences | 0.0000 | 0.0000 | 0 | rule level: comparison months only |

Residual stops per segment: pre 1 (seal-gap 1); post 0 (seal-gap 0).

## Missingness

- pre unmarked halt rows and locked execution rows (primary cost case): MOM_12_1 0 and 0, HIGH_52W 0 and 0, REV_1M 0 and 0, LOW_VOL_252 0 and 0, LOW_BETA_252 0 and 0, AMIHUD_ILLIQ_63 0 and 0.
- post unmarked halt rows and locked execution rows (primary cost case): MOM_12_1 0 and 0, HIGH_52W 0 and 0, REV_1M 0 and 0, LOW_VOL_252 0 and 0, LOW_BETA_252 0 and 0, AMIHUD_ILLIQ_63 0 and 0.

## Windows

- pre: comparison months primary 2011-08 to 2012-12 (17); sensitivity 2011-08 to 2012-12 (17); sleeve months 2011-01 to 2012-12 (24).
- post: comparison months primary 2015-08 to 2016-09 (14); sensitivity 2015-08 to 2016-09 (14); sleeve months 2015-01 to 2016-11 (23).

## Method and Provenance

- Specification: `docs/preregistrations/m5_trial_family_v1_amendment_4.json` revision 2 (SHA-256 `c2b1f8dea064ef1852d55bfda365faef8bd1c658897877037aae2fc0714ac617`) with v1 and amendments 1 to 3; the runner refuses unless all five match HEAD and their pins.
- Code commit `n/a`; tracked changes at run time: None.
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

