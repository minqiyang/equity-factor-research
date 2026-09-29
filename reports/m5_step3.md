# Milestone 5 Step 3: State Tilt, Factor Momentum Tilt, and Pooled Ridge Against R1

**Evidence ceiling: DIAGNOSTIC_ONLY.** Public long-short factor series on jkp_factors_153, gross of each factor's internal trading and borrow costs, small caps included. Nothing here supports a profitability, ranking, or promotion claim. Every S3 test re-examines comparisons already seen in the prior exposures and supports no confirmatory claim.

Run 2026-09-29T06:28:24Z from code commit `f522a2342d71e561188d9ac50e7e64724319bb65` (tracked changes at run time: False); runtime 6.5 seconds.

## Conclusion

**The return-timing line stays open.** R2 meets all 8 closure conditions and goes to step 4 beside R1, labeled 'no evidence of state timing'.

S3.R2 (R2 net minus R1 net at 20 bp, 648 months): mean -0.23 bp per month, 95% interval [-0.0076%, 0.0029%] per month, HAC p 0.3794, BY q 1, random-date p 0.318.

R2 timing claim: **does not qualify** (failed conditions: 2, 3, 4, 5, 6).

| Condition | Text | Holds |
| --- | --- | --- |
| 1 | R2 meets all 8 closure conditions | yes |
| 2 | full-window mean of the S3.R2 difference is positive | no |
| 3 | S3.R2 BY q-value <= 0.05 | no |
| 4 | S3.R2 random-date p-value is defined and <= 0.05 | no |
| 5 | post-publication R2-sub is not worse than R1-sub at 20 and 50 bp and its mean difference is positive | no |
| 6 | each of R2's three states is eligible under the episode rule | no |

Surviving descriptive state-effect cells: none. Even a qualifying timing claim would credit no single state. R3 or R4 owner items (all 8 conditions and q <= 0.05): none.

## Closure Conditions (R2 against R1, jkp_factors_153)

Differences below 1e-12 in magnitude count as equal, and equal is not a loss. Margin: rule minus R1 Sharpe, and R1 minus rule drawdown magnitude.

| Rule | Period | Cost | Metric | Rule value | R1 value | Margin | Holds |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| R0 | 1972-1999 | 20 bp | max_drawdown | -8.57% | -3.69% | -4.8793 pp | no |
| R0 | 1972-1999 | 20 bp | sharpe | 1.224 | 1.653 | -0.4293 | no |
| R0 | 1972-1999 | 50 bp | max_drawdown | -8.57% | -3.81% | -4.7562 pp | no |
| R0 | 1972-1999 | 50 bp | sharpe | 1.216 | 1.592 | -0.3760 | no |
| R0 | 2000-end | 20 bp | max_drawdown | -9.27% | -7.27% | -1.9992 pp | no |
| R0 | 2000-end | 20 bp | sharpe | 0.610 | 0.736 | -0.1268 | no |
| R0 | 2000-end | 50 bp | max_drawdown | -9.27% | -7.42% | -1.8574 pp | no |
| R0 | 2000-end | 50 bp | sharpe | 0.610 | 0.704 | -0.0942 | no |
| R0 | all | | | | | | **0 of 8 hold** |
| R2 | 1972-1999 | 20 bp | max_drawdown | -3.22% | -3.69% | 0.4707 pp | yes |
| R2 | 1972-1999 | 20 bp | sharpe | 1.771 | 1.653 | 0.1180 | yes |
| R2 | 1972-1999 | 50 bp | max_drawdown | -3.30% | -3.81% | 0.5126 pp | yes |
| R2 | 1972-1999 | 50 bp | sharpe | 1.682 | 1.592 | 0.0902 | yes |
| R2 | 2000-end | 20 bp | max_drawdown | -7.08% | -7.27% | 0.1915 pp | yes |
| R2 | 2000-end | 20 bp | sharpe | 0.756 | 0.736 | 0.0201 | yes |
| R2 | 2000-end | 50 bp | max_drawdown | -7.25% | -7.42% | 0.1625 pp | yes |
| R2 | 2000-end | 50 bp | sharpe | 0.711 | 0.704 | 0.0076 | yes |
| R2 | all | | | | | | **8 of 8 hold** |
| R3 | 1972-1999 | 20 bp | max_drawdown | -2.78% | -3.69% | 0.9083 pp | yes |
| R3 | 1972-1999 | 20 bp | sharpe | 1.673 | 1.653 | 0.0201 | yes |
| R3 | 1972-1999 | 50 bp | max_drawdown | -3.07% | -3.81% | 0.7410 pp | yes |
| R3 | 1972-1999 | 50 bp | sharpe | 1.452 | 1.592 | -0.1398 | no |
| R3 | 2000-end | 20 bp | max_drawdown | -5.46% | -7.27% | 1.8129 pp | yes |
| R3 | 2000-end | 20 bp | sharpe | 0.646 | 0.736 | -0.0903 | no |
| R3 | 2000-end | 50 bp | max_drawdown | -7.60% | -7.42% | -0.1839 pp | no |
| R3 | 2000-end | 50 bp | sharpe | 0.470 | 0.704 | -0.2340 | no |
| R3 | all | | | | | | **4 of 8 hold** |
| R4 | 1972-1999 | 20 bp | max_drawdown | -3.93% | -3.69% | -0.2437 pp | no |
| R4 | 1972-1999 | 20 bp | sharpe | 1.627 | 1.653 | -0.0264 | no |
| R4 | 1972-1999 | 50 bp | max_drawdown | -4.07% | -3.81% | -0.2609 pp | no |
| R4 | 1972-1999 | 50 bp | sharpe | 1.564 | 1.592 | -0.0284 | no |
| R4 | 2000-end | 20 bp | max_drawdown | -6.81% | -7.27% | 0.4598 pp | yes |
| R4 | 2000-end | 20 bp | sharpe | 0.680 | 0.736 | -0.0562 | no |
| R4 | 2000-end | 50 bp | max_drawdown | -7.63% | -7.42% | -0.2136 pp | no |
| R4 | 2000-end | 50 bp | sharpe | 0.594 | 0.704 | -0.1095 | no |
| R4 | all | | | | | | **1 of 8 hold** |

Share of evaluated months in which any R2 weight differs from R1 by more than 1e-12: full 0.847, 1972-1999 1.000, 2000-end 0.683. The same share for R3: full 1.000, 1972-1999 1.000, 2000-end 1.000; for R4: full 0.849, 1972-1999 0.708, 2000-end 1.000.

## Rule Metrics (step 2 metrics, R0 to R4)

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
| R2 | 20 bp | full | 648 | 2.24% | 2.02% | 1.113 | -7.08% | -6.22% | 0.033 |
| R2 | 20 bp | 1972-1999 | 336 | 2.59% | 1.46% | 1.771 | -3.22% | -3.22% | 0.035 |
| R2 | 20 bp | 2000-end | 312 | 1.87% | 2.48% | 0.756 | -7.08% | -5.91% | 0.031 |
| R2 | 50 bp | full | 648 | 2.12% | 2.02% | 1.053 | -7.25% | -6.32% | 0.033 |
| R2 | 50 bp | 1972-1999 | 336 | 2.46% | 1.46% | 1.682 | -3.30% | -3.30% | 0.035 |
| R2 | 50 bp | 2000-end | 312 | 1.76% | 2.48% | 0.711 | -7.25% | -6.05% | 0.031 |
| R3 | 20 bp | full | 648 | 2.52% | 2.41% | 1.046 | -5.46% | -4.87% | 0.127 |
| R3 | 20 bp | 1972-1999 | 336 | 3.14% | 1.88% | 1.673 | -2.78% | -0.89% | 0.115 |
| R3 | 20 bp | 2000-end | 312 | 1.85% | 2.87% | 0.646 | -5.46% | -4.87% | 0.140 |
| R3 | 50 bp | full | 648 | 2.06% | 2.42% | 0.855 | -7.60% | -5.34% | 0.127 |
| R3 | 50 bp | 1972-1999 | 336 | 2.73% | 1.88% | 1.452 | -3.07% | -1.32% | 0.115 |
| R3 | 50 bp | 2000-end | 312 | 1.35% | 2.87% | 0.470 | -7.60% | -5.34% | 0.140 |
| R4 | 20 bp | full | 648 | 2.21% | 2.18% | 1.015 | -6.83% | -6.30% | 0.043 |
| R4 | 20 bp | 1972-1999 | 336 | 2.57% | 1.58% | 1.627 | -3.93% | -3.70% | 0.026 |
| R4 | 20 bp | 2000-end | 312 | 1.82% | 2.67% | 0.680 | -6.81% | -5.61% | 0.062 |
| R4 | 50 bp | full | 648 | 2.05% | 2.18% | 0.940 | -7.63% | -6.42% | 0.043 |
| R4 | 50 bp | 1972-1999 | 336 | 2.48% | 1.58% | 1.564 | -4.07% | -3.79% | 0.026 |
| R4 | 50 bp | 2000-end | 312 | 1.59% | 2.68% | 0.594 | -7.63% | -5.90% | 0.062 |

Market excess return (French Mkt-RF, context only, no switch cost): full ann. mean 7.57%, Sharpe 0.480; 1972-1999 ann. mean 7.77%, Sharpe 0.491; 2000-end ann. mean 7.35%, Sharpe 0.468.

## S3 Rule Tests (rule net minus R1 net at 20 bp, full window)

BY family: 42 observed p-values plus 1005 prior-exposure slots at p = 1 (family size 1047). The 95% interval is pointwise, mean +/- 1.959964 x sqrt(LRV / n), not adjusted for selection or multiplicity.

| Test | Status | Months | Mean (bp/month) | 95% interval (%/month) | 95% interval (%/year) | HAC t | HAC p | BY q | Random-date p |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |
| S3.R2 | ok | 648 | -0.23 | [-0.0076%, 0.0029%] | [-0.0909%, 0.0346%] | -0.88 | 0.3794 | 1 | 0.318 |
| S3.R3 | ok | 648 | 2.08 | [-0.0126%, 0.0542%] | [-0.1511%, 0.6507%] | 1.22 | 0.222 | 1 | not run |
| S3.R4 | ok | 648 | -0.53 | [-0.0108%, 0.0002%] | [-0.1299%, 0.0024%] | -1.89 | 0.05905 | 1 | not run |

Random-date null: 999 circular shifts of the three label series inside the label span (1131 months), seed 20260928, offsets 60 to 1071. S3.R2: 317 exceedances, 0 undefined draws (counted as exceedances). R3 and R4 have no random-date null.

## State Episodes and Eligibility

Episodes are maximal runs of consecutive evaluated months in one cell, counted per half; a run crossing 1999-12 to 2000-01 counts once in each half. A state is eligible when each cell has at least 10 episodes in each half.

| State | Cell | Episodes 1972-1999 | Episodes 2000-end | Eligible |
| --- | --- | ---: | ---: | --- |
| market_trend | up | 11 | 10 | no |
| market_trend | down | 10 | 9 | no |
| market_volatility | high | 23 | 26 | yes |
| market_volatility | normal | 22 | 26 | yes |
| credit_spread | wide | 14 | 14 | yes |
| credit_spread | normal | 13 | 14 | yes |

R2 mean lambda = E / (E + 10) per state: full market_trend 0.737, market_volatility 0.820, credit_spread 0.730; 1972-1999 market_trend 0.708, market_volatility 0.786, credit_spread 0.689; 2000-end market_trend 0.768, market_volatility 0.858, credit_spread 0.774.

## State-Effect Tests (39, gross class returns)

b is the mean gross class return in the first cell (up, high, wide) minus the second, in percent per month. `*` marks a pre-seen cell. Months/episodes are per cell (first cell / second cell). A test on a state that is not eligible is description only; its p-value still counts in the family.

| Test | Pre-seen | b full | HAC t | HAC p | BY q | Random-date p (undef.) | b 1972-1999 | b 2000-end | b post-pub | Months 1972-1999 | Episodes 1972-1999 | Months 2000-end | Episodes 2000-end | Description only | Survives |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |
| S3.effect.accruals.market_trend |  | -0.082% | -0.51 | 0.6124 | 1 | 0.617 (0) | -0.297% | 0.041% | 0.035% | 276/60 | 11/10 | 239/73 | 10/9 | yes | no |
| S3.effect.accruals.market_volatility |  | 0.062% | 0.63 | 0.5296 | 1 | 0.773 (0) | 0.041% | 0.248% | 0.426% | 194/142 | 23/22 | 226/86 | 26/26 | no | no |
| S3.effect.accruals.credit_spread |  | 0.066% | 0.72 | 0.4729 | 1 | 0.571 (0) | 0.153% | 0.115% | 0.213% | 147/189 | 14/13 | 187/125 | 14/14 | no | no |
| S3.effect.debt_issuance.market_trend |  | -0.158% | -2.10 | 0.0358 | 1 | 0.049 (0) | -0.169% | -0.179% | 0.009% | 276/60 | 11/10 | 239/73 | 10/9 | yes | no |
| S3.effect.debt_issuance.market_volatility |  | 0.090% | 1.43 | 0.1533 | 1 | 0.376 (0) | 0.142% | 0.097% | -0.097% | 194/142 | 23/22 | 226/86 | 26/26 | no | no |
| S3.effect.debt_issuance.credit_spread |  | 0.040% | 0.61 | 0.5438 | 1 | 0.731 (0) | -0.030% | 0.183% | 0.016% | 147/189 | 14/13 | 187/125 | 14/14 | no | no |
| S3.effect.investment.market_trend |  | -0.324% | -1.49 | 0.1353 | 1 | 0.174 (0) | -0.322% | -0.335% | -0.243% | 276/60 | 11/10 | 239/73 | 10/9 | yes | no |
| S3.effect.investment.market_volatility |  | 0.164% | 1.09 | 0.2762 | 1 | 0.254 (0) | -0.042% | 0.460% | 0.337% | 194/142 | 23/22 | 226/86 | 26/26 | no | no |
| S3.effect.investment.credit_spread |  | 0.115% | 0.63 | 0.5269 | 1 | 0.524 (0) | -0.044% | 0.311% | 0.113% | 147/189 | 14/13 | 187/125 | 14/14 | no | no |
| S3.effect.low_leverage.market_trend |  | -0.000% | -0.00 | 0.9998 | 1 | 1 (0) | 0.258% | -0.265% | -0.291% | 276/60 | 11/10 | 239/73 | 10/9 | yes | no |
| S3.effect.low_leverage.market_volatility |  | 0.147% | 0.73 | 0.4655 | 1 | 0.462 (0) | 0.346% | -0.018% | 0.075% | 194/142 | 23/22 | 226/86 | 26/26 | no | no |
| S3.effect.low_leverage.credit_spread |  | 0.162% | 0.52 | 0.6001 | 1 | 0.554 (0) | 0.193% | 0.218% | 0.404% | 147/189 | 14/13 | 187/125 | 14/14 | no | no |
| S3.effect.low_risk.market_trend |  | -0.013% | -0.03 | 0.9726 | 1 | 0.977 (0) | 0.049% | -0.026% | -0.202% | 276/60 | 11/10 | 239/73 | 10/9 | yes | no |
| S3.effect.low_risk.market_volatility | * | -0.522% | -2.15 | 0.03177 | 1 | 0.02 (0) | -0.674% | -0.449% | -0.424% | 194/142 | 23/22 | 226/86 | 26/26 | no | no |
| S3.effect.low_risk.credit_spread |  | -0.209% | -0.65 | 0.5171 | 1 | 0.449 (0) | -0.031% | -0.506% | -0.236% | 147/189 | 14/13 | 187/125 | 14/14 | no | no |
| S3.effect.momentum.market_trend | * | 0.531% | 1.43 | 0.1523 | 1 | 0.167 (0) | 0.615% | 0.429% | 0.794% | 276/60 | 11/10 | 239/73 | 10/9 | yes | no |
| S3.effect.momentum.market_volatility | * | -0.178% | -0.95 | 0.3435 | 1 | 0.344 (0) | -0.110% | -0.198% | -0.068% | 194/142 | 23/22 | 226/86 | 26/26 | no | no |
| S3.effect.momentum.credit_spread |  | 0.203% | 0.78 | 0.4325 | 1 | 0.457 (0) | 0.380% | 0.090% | 0.241% | 147/189 | 14/13 | 187/125 | 14/14 | no | no |
| S3.effect.profit_growth.market_trend |  | 0.136% | 1.21 | 0.2244 | 1 | 0.213 (0) | 0.013% | 0.210% | 0.276% | 276/60 | 11/10 | 239/73 | 10/9 | yes | no |
| S3.effect.profit_growth.market_volatility |  | -0.095% | -1.34 | 0.1799 | 1 | 0.307 (0) | 0.059% | -0.217% | -0.211% | 194/142 | 23/22 | 226/86 | 26/26 | no | no |
| S3.effect.profit_growth.credit_spread |  | -0.121% | -1.41 | 0.16 | 1 | 0.177 (0) | 0.043% | -0.233% | -0.208% | 147/189 | 14/13 | 187/125 | 14/14 | no | no |
| S3.effect.profitability.market_trend |  | 0.174% | 0.80 | 0.4264 | 1 | 0.531 (0) | 0.075% | 0.284% | 0.254% | 276/60 | 11/10 | 239/73 | 10/9 | yes | no |
| S3.effect.profitability.market_volatility |  | -0.164% | -1.11 | 0.2668 | 1 | 0.282 (0) | -0.110% | -0.294% | -0.320% | 194/142 | 23/22 | 226/86 | 26/26 | no | no |
| S3.effect.profitability.credit_spread |  | -0.407% | -1.70 | 0.08932 | 1 | 0.076 (0) | -0.362% | -0.526% | -0.585% | 147/189 | 14/13 | 187/125 | 14/14 | no | no |
| S3.effect.quality.market_trend |  | -0.173% | -0.99 | 0.3235 | 1 | 0.309 (0) | -0.137% | -0.200% | -0.146% | 276/60 | 11/10 | 239/73 | 10/9 | yes | no |
| S3.effect.quality.market_volatility | * | 0.072% | 0.62 | 0.5364 | 1 | 0.568 (0) | 0.218% | -0.129% | -0.322% | 194/142 | 23/22 | 226/86 | 26/26 | no | no |
| S3.effect.quality.credit_spread |  | -0.061% | -0.48 | 0.6341 | 1 | 0.611 (0) | -0.056% | -0.082% | -0.139% | 147/189 | 14/13 | 187/125 | 14/14 | no | no |
| S3.effect.seasonality.market_trend |  | -0.087% | -1.48 | 0.1398 | 1 | 0.23 (0) | -0.033% | -0.137% | 0.064% | 276/60 | 11/10 | 239/73 | 10/9 | yes | no |
| S3.effect.seasonality.market_volatility |  | 0.045% | 1.05 | 0.2918 | 1 | 0.387 (0) | 0.033% | 0.065% | -0.012% | 194/142 | 23/22 | 226/86 | 26/26 | no | no |
| S3.effect.seasonality.credit_spread |  | 0.062% | 1.49 | 0.1351 | 1 | 0.324 (0) | 0.028% | 0.105% | 0.044% | 147/189 | 14/13 | 187/125 | 14/14 | no | no |
| S3.effect.short_term_reversal.market_trend |  | -0.069% | -0.76 | 0.446 | 1 | 0.502 (0) | -0.136% | -0.002% | -0.434% | 276/60 | 11/10 | 239/73 | 10/9 | yes | no |
| S3.effect.short_term_reversal.market_volatility |  | 0.028% | 0.38 | 0.706 | 1 | 0.716 (0) | -0.058% | 0.121% | 0.072% | 194/142 | 23/22 | 226/86 | 26/26 | no | no |
| S3.effect.short_term_reversal.credit_spread |  | 0.002% | 0.02 | 0.9873 | 1 | 0.988 (0) | 0.045% | -0.066% | -0.206% | 147/189 | 14/13 | 187/125 | 14/14 | no | no |
| S3.effect.size.market_trend |  | -0.606% | -2.48 | 0.01309 | 1 | 0.027 (0) | -0.278% | -0.885% | -0.749% | 276/60 | 11/10 | 239/73 | 10/9 | yes | no |
| S3.effect.size.market_volatility | * | 0.350% | 2.03 | 0.04247 | 1 | 0.042 (0) | 0.037% | 0.743% | 0.380% | 194/142 | 23/22 | 226/86 | 26/26 | no | no |
| S3.effect.size.credit_spread |  | 0.509% | 2.80 | 0.0051 | 1 | 0.003 (0) | 0.434% | 0.587% | 0.571% | 147/189 | 14/13 | 187/125 | 14/14 | no | no |
| S3.effect.value.market_trend |  | -0.337% | -1.18 | 0.239 | 1 | 0.324 (0) | -0.494% | -0.174% | -0.565% | 276/60 | 11/10 | 239/73 | 10/9 | yes | no |
| S3.effect.value.market_volatility | * | -0.006% | -0.02 | 0.9802 | 1 | 0.99 (0) | -0.260% | 0.263% | -0.107% | 194/142 | 23/22 | 226/86 | 26/26 | no | no |
| S3.effect.value.credit_spread |  | -0.080% | -0.22 | 0.8277 | 1 | 0.794 (0) | -0.135% | -0.084% | -0.095% | 147/189 | 14/13 | 187/125 | 14/14 | no | no |

Per-half cell mean gross returns are in `reports/m5_step3.json` under `state_effects`.

## R3 and R4 Coverage

R3 members without a trailing 12-month return (keep their R1 weight): full 0, 1972-1999 0, 2000-end 0.

| Period | Set factor-months | Covered rows | Forecast factor-months | Share of set | Forecast share of R1 weight | Months with < 2 forecasts | No publication year | Not yet published | Missing trailing return | No fit yet |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full | 99052 | 35008 | 34962 | 0.353 | 0.341 | 98 | 7128 | 56916 | 0 | 46 |
| 1972-1999 | 51316 | 2992 | 2946 | 0.057 | 0.043 | 98 | 3696 | 44628 | 0 | 46 |
| 2000-end | 47736 | 32016 | 32016 | 0.671 | 0.661 | 0 | 3432 | 12288 | 0 | 0 |

Reasons are assigned in the order listed (no publication year, not yet published, missing trailing return, no fit yet), so each uncovered factor-month has one reason.

| Fit year | Status | Training rows | Training months | Forecast rows | Intercept |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1972 | too_few_training_months | 0 | 0 | 0 | n/a |
| 1973 | too_few_training_months | 0 | 0 | 0 | n/a |
| 1974 | too_few_training_months | 0 | 0 | 0 | n/a |
| 1975 | too_few_training_months | 9 | 9 | 0 | n/a |
| 1976 | too_few_training_months | 21 | 21 | 0 | n/a |
| 1977 | too_few_training_months | 33 | 33 | 0 | n/a |
| 1978 | fit | 45 | 45 | 12 | -0.001951 |
| 1979 | fit | 57 | 57 | 12 | -0.004562 |
| 1980 | fit | 69 | 69 | 32 | -0.005140 |
| 1981 | fit | 99 | 81 | 36 | -0.009406 |
| 1982 | fit | 135 | 93 | 46 | -0.000962 |
| 1983 | fit | 180 | 105 | 58 | 0.001765 |
| 1984 | fit | 237 | 117 | 70 | 0.002874 |
| 1985 | fit | 306 | 129 | 82 | 0.004472 |
| 1986 | fit | 387 | 141 | 104 | 0.003607 |
| 1987 | fit | 489 | 153 | 108 | 0.003233 |
| 1988 | fit | 597 | 165 | 108 | 0.002672 |
| 1989 | fit | 705 | 177 | 118 | 0.002754 |
| 1990 | fit | 822 | 189 | 120 | 0.001915 |
| 1991 | fit | 942 | 201 | 130 | 0.001168 |
| 1992 | fit | 1071 | 213 | 132 | 0.001093 |
| 1993 | fit | 1203 | 225 | 152 | 0.001093 |
| 1994 | fit | 1353 | 237 | 196 | 0.001353 |
| 1995 | fit | 1545 | 249 | 234 | 0.001302 |
| 1996 | fit | 1776 | 261 | 240 | 0.001044 |
| 1997 | fit | 2016 | 273 | 280 | 0.001131 |
| 1998 | fit | 2292 | 285 | 288 | 0.001523 |
| 1999 | fit | 2580 | 297 | 388 | 0.001566 |
| 2000 | fit | 2958 | 309 | 418 | 0.000359 |
| 2001 | fit | 3375 | 321 | 440 | 0.001154 |
| 2002 | fit | 3813 | 333 | 504 | 0.002788 |
| 2003 | fit | 4311 | 345 | 536 | 0.003308 |
| 2004 | fit | 4845 | 357 | 560 | 0.003025 |
| 2005 | fit | 5403 | 369 | 664 | 0.002881 |
| 2006 | fit | 6057 | 381 | 814 | 0.002701 |
| 2007 | fit | 6858 | 393 | 970 | 0.002474 |
| 2008 | fit | 7815 | 405 | 1036 | 0.002184 |
| 2009 | fit | 8847 | 417 | 1214 | 0.002587 |
| 2010 | fit | 10044 | 429 | 1268 | 0.001820 |
| 2011 | fit | 11310 | 441 | 1282 | 0.001685 |
| 2012 | fit | 12591 | 453 | 1384 | 0.001677 |
| 2013 | fit | 13965 | 465 | 1434 | 0.001725 |
| 2014 | fit | 15396 | 477 | 1450 | 0.001658 |
| 2015 | fit | 16845 | 489 | 1492 | 0.001634 |
| 2016 | fit | 18333 | 501 | 1520 | 0.001667 |
| 2017 | fit | 19851 | 513 | 1584 | 0.001627 |
| 2018 | fit | 21429 | 525 | 1606 | 0.001540 |
| 2019 | fit | 23034 | 537 | 1648 | 0.001464 |
| 2020 | fit | 24678 | 549 | 1676 | 0.001359 |
| 2021 | fit | 26352 | 561 | 1700 | 0.000891 |
| 2022 | fit | 28050 | 573 | 1704 | 0.001019 |
| 2023 | fit | 29754 | 585 | 1704 | 0.001469 |
| 2024 | fit | 31458 | 597 | 1704 | 0.001375 |
| 2025 | fit | 33162 | 609 | 1704 | 0.001287 |

The 83 coefficients of every fit are in `reports/m5_step3.json` under `r4.fits`.

## Post-Publication Comparison (condition 5; no test)

R2 re-estimated on post-publication factor-months only, with history from the subset label span start. Status `completed`; start month 1974-03; subset label span start 1974-03. R3 and R4 are not formed on the subset.

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
| R2 | 20 bp | full | 622 | 0.83% | 5.32% | 0.156 | -50.75% | -21.93% | 0.055 |
| R2 | 20 bp | 1972-1999 | 310 | 0.07% | 7.12% | 0.009 | -50.75% | -21.93% | 0.056 |
| R2 | 20 bp | 2000-end | 312 | 1.59% | 2.46% | 0.645 | -8.16% | -6.70% | 0.054 |
| R2 | 50 bp | full | 622 | 0.63% | 5.31% | 0.119 | -50.96% | -22.26% | 0.055 |
| R2 | 50 bp | 1972-1999 | 310 | -0.13% | 7.10% | -0.019 | -50.96% | -22.26% | 0.056 |
| R2 | 50 bp | 2000-end | 312 | 1.39% | 2.46% | 0.565 | -8.77% | -6.88% | 0.054 |

Subset periods: full 1974-03 to 2025-12; 1972-1999 1974-03 to 1999-12; 2000-end 2000-01 to 2025-12. Subset members per month: min 1, median 34, max 142; the early subset holds very few factors, so its first-half figures describe a thin and changing set.

Condition 5 over the full subset period: at 20 bp, Sharpe margin +0.0057 (holds) and drawdown margin -0.1273 pp (fails); at 50 bp, Sharpe margin -0.0081 (fails) and drawdown margin -0.1472 pp (fails); mean R2-sub minus R1-sub at 20 bp +0.33 bp per month (holds).

R2-sub mean lambda per state: full market_trend 0.467, market_volatility 0.602, credit_spread 0.519; 1972-1999 market_trend 0.349, market_volatility 0.442, credit_spread 0.395; 2000-end market_trend 0.584, market_volatility 0.760, credit_spread 0.644.

Share of subset months in which R2-sub weights differ from R1-sub weights by more than 1e-12: full 0.868, 1972-1999 0.735, 2000-end 1.000.

Subset class-months with no subset member (typed missing, left out of R2-sub histories and b post-pub): full 2640, 1972-1999 2564, 2000-end 76.

Evaluated months with an empty subset before the start month: 26.

## Label Span, Missingness, and Refusals

Label span 1931-10 to 2025-12 (1131 months, of which 483 are lookback months before 1972-01). Label months before the span start are used by no rule or test; defined labels before it: market_trend 50, market_volatility 0, credit_spread 31; missing labels before it: market_trend 19, market_volatility 69, credit_spread 38. No label is missing inside the span (the run would refuse).

Cell months inside the span: market_trend up 861, down 270; market_volatility high 556, normal 575; credit_spread wide 531, normal 600.

Full-set class-months typed missing (left out of R2 histories and tests): span lookback: no member 478, member return missing 0; full: no member 0, member return missing 0; 1972-1999: no member 0, member return missing 0; 2000-end: no member 0, member return missing 0. Per-class counts are in the JSON. An evaluated month with an empty class would refuse the run.

Provider missing codes: French daily Mkt-RF 0; FRED BAA/AAA none; French monthly FF3 none.

| Period | Declared | In set | Fewer than 24 in t-37..t-2 | Bad data in t-37..t-2 | Typed missing |
| --- | ---: | ---: | ---: | ---: | --- |
| full | 99144 | 99052 | 92 | 0 | none |
| 1972-1999 | 51408 | 51316 | 92 | 0 | none |
| 2000-end | 47736 | 47736 | 0 | 0 | none |

Refusals in this run: none (a refusal stops the run and is recorded in `reports/m5_step3_attempts.jsonl`).

Descriptive universes: none. Amendment 3 runs step 3 on jkp_factors_153 only; the step 2 results for jkp_themes_13 and french_7 stand.

## Provenance, Costs, and Timing

Trial files, each verified equal to its committed HEAD version and its pinned SHA-256 before any data was read: `docs/preregistrations/m5_trial_family_v1.json` (`a99a862c651fd4e5...`); `docs/preregistrations/m5_trial_family_v1_amendment_1.json` (`b3992b3282910a5b...`); `docs/preregistrations/m5_trial_family_v1_amendment_2.json` (`59461b150a957959...`); `docs/preregistrations/m5_trial_family_v1_amendment_3.json` (`c59f69c8262190ad...`).

- Timing `after_month_end_signal_next_month_end_execution`: signal month t-2 (feature observation end: the close of the last trading day of month t-2); execution at the close of the last trading day of month t-1; return month t (close of month t-1 to close of month t). Labels use market data through month t-2 and the credit spread through month t-3; R2 histories use class returns of months u <= t-2; each R4 fit for year Y trains on return months through November of Y-1.
- Costs: switch cost 20 bp primary and 50 bp sensitivity on monthly weight turnover from the step 2 portfolio function; each run starts from no holdings (turnover 1 in its first month). State-effect tests use gross class returns. Factor internal costs and borrow stay inside the published returns.

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
| french_ff3_daily | 26317 | 1926-07-01 | 2026-08-31 | `2f29e22546069914` | 2026-09-29T06:25:12Z |
| jkp_accounting_characteristics_list | 315 | - | - | `b3cab651d62bd121` | 2026-09-29T06:25:12Z |

Full URLs and hashes: `reports/m5_public_data_manifest.json`. Raw files stay in the gitignored `data/public_cache/`. Attribution: JKP data by Jensen, Kelly, and Pedersen, jkpfactors.com, CC BY-NC 4.0; jkp-data code (cluster_labels.csv, factor_details.xlsx, aux_functions.py) MIT. French factors: Kenneth R. French Data Library, copyright Eugene F. Fama and Kenneth R. French. Moody's BAA and AAA yields retrieved from FRED, Federal Reserve Bank of St. Louis.

## Limitations

- DIAGNOSTIC_ONLY: public long-short factor returns, gross of internal trading and borrow costs, small caps included. The implementable check on point-in-time books after costs is step 4.
- Every S3 test re-examines comparisons the prior exposures already ran on the same months; the 1005 prior slots cover the retained final scripts only, so the historical search is not proven complete.
- With 1047 family slots the smallest p-value needs about 6.3e-6 (HAC |t| about 4.5) to reach BY q 0.05, so survival is rare by design.
- HAC standard errors with the step 2 lag may understate uncertainty for persistent states; the random-date null is the guard, and its circular shift joins the span end to its start once per draw.
- R4 has no forecast for most first-half factor-months, so its first-half comparison has little power; R4 has no random-date null and supports no state-timing claim.
- R2 lookback histories reach back to the early 1930s and include early Compustat years with known backfill bias; the JKP clusters used as classes come from full-sample correlations (hindsight).
- The post-publication condition uses the subset's full period, which is weighted toward the second half; the subset halves are reported, not tested.
- On jkp_factors_153, turnover_class is a function of theme and adds nothing to R4 beyond theme.
- The JKP and French files are revised by their providers; the manifest pins the SHA-256 of the files used here.
