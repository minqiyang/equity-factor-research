# WorldQuant Alphas Batch 5 Multifactor Diagnostic MVP Evidence

This report is `DIAGNOSTIC_ONLY`. It uses a committed synthetic 50-stock static
survivor cohort. That cohort is not point-in-time universe evidence, not a
dataset-review decision, and not a 14-trial campaign run. Metrics are
workflow diagnostics only and are not evidence of real-world strategy
profitability.

## Evidence ceiling

- Evidence ceiling: `DIAGNOSTIC_ONLY`
- Review decision: `diagnostic_only`
- `dataset_manifest_reviewed`: `False`
- `formal_interpretation_eligible`: `False`
- Survivorship bias: `True`
- Not point-in-time universe evidence: `True`
- Cohort id: `walking_skeleton_diagnostic_cohort_v1`

## Pipeline

1. Load the 50-stock diagnostic cohort fixture and generate synthetic close
   prices plus companion open, high, low, typical-price VWAP, volume, and
   close-to-close returns.
2. Compute classical price-volume alphas `ALPHA_001`, `ALPHA_002`, `ALPHA_003`, `ALPHA_004`, `ALPHA_005`, `ALPHA_006`, `ALPHA_007`, `ALPHA_008`, `ALPHA_009`, `ALPHA_010`, `ALPHA_012`, `ALPHA_013`, `ALPHA_014`, `ALPHA_015`, `ALPHA_016`, `ALPHA_017`, `ALPHA_018`, `ALPHA_019`, `ALPHA_020`, `ALPHA_021`, `ALPHA_022`, `ALPHA_023`, `ALPHA_024`, `ALPHA_025`, `ALPHA_026`, `ALPHA_028`, `ALPHA_030`, `ALPHA_031`, `ALPHA_032`, `ALPHA_033`, `ALPHA_034`, `ALPHA_035`, `ALPHA_036`, `ALPHA_037`, `ALPHA_038`, `ALPHA_039`, `ALPHA_040`, `ALPHA_041`, `ALPHA_042`, `ALPHA_043`, `ALPHA_044`, `ALPHA_045`, `ALPHA_046`, `ALPHA_049`, `ALPHA_050`, `ALPHA_051`, `ALPHA_052`, `ALPHA_053`, `ALPHA_054`, `ALPHA_055`, `ALPHA_060`, `ALPHA_101`.
3. Build `EQUAL_WEIGHTED_COMPOSITE` as the equal-weight average of
   cross-sectional z-scores of those 52 alphas.
4. Build `IC_WEIGHTED_COMPOSITE` with the same z-scores and in-sample mean
   monthly Rank IC as static supplied weights.
5. Build `ICIR_WEIGHTED_COMPOSITE` weighted by historical monthly Information Ratio.
6. Build `CORRELATION_DISCOUNTED_COMPOSITE` solving for collinearity-discounted weights.
7. Build `ALPHA_PRODUCT_INTERACTION` and `CONDITIONAL_RANK_INTERACTION` cross-factor models.
8. Build `NEUTRALIZED_IC_COMPOSITE` orthogonalized against rolling return volatility.
9. Measure monthly Spearman Rank IC versus 21-source-row forward returns that
   start at the lag-1 execution close.
10. Summarize mean IC, ICIR (`mean / sample std`), and the Newey-West t-stat of
    the mean IC.
11. Run the existing long-only equal-weight monthly backtester with
    `5.00` bps slippage and `5` names.
12. Run dollar-neutral long-short decile spread backtests with `10` quantiles
    and `5.00` bps slippage.
13. Compute the Deflated Sharpe Ratio of daily measured strategy returns with
    `n_trials=59` and the Euler-Mascheroni expected-maximum mix.
14. Compute the Probability of Backtest Overfitting (PBO) across all 52
    alphas using Combinatorially Symmetric Cross-Validation (CSCV).

## Configuration

- Manifest: `tests/fixtures/walking_skeleton/diagnostic_cohort_v1.json`
- Asset count: `50`
- Source date range: `2021-01-04` to `2023-11-27`
- Evaluation date range: `2021-02-08` to `2023-11-27`
- Rebalance frequency: `ME`
- Selected assets per rebalance: `5`
- Signal lag: `1` source row
- Execution timing: `after_close_signal_next_observed_close_v1`
- Transaction cost: `0.00` bps
- Slippage: `5.00` bps
- Zero cost or slippage diagnostic: `True`
- Benchmark: synthetic equal-weight diagnostic-cohort benchmark
- Timing contract: `after_close_signal_next_observed_close_v1`
- DSR expected-maximum mix: Euler-Mascheroni constant `np.euler_gamma`
- PBO splits: `8`
- VWAP: typical price `(high + low + close) / 3` on companion synthetic bars
- Composite IC weights: in-sample mean monthly Rank IC of the 52 implemented alphas
- Long-short quantiles: `10`

## In-sample IC weights

| factor | mean monthly Rank IC |
| --- | --- |
| ALPHA_001 | -0.0083 |
| ALPHA_002 | -0.0028 |
| ALPHA_003 | -0.0383 |
| ALPHA_004 | -0.0181 |
| ALPHA_005 | -0.0254 |
| ALPHA_006 | -0.0036 |
| ALPHA_007 | 0.0106 |
| ALPHA_008 | -0.0291 |
| ALPHA_009 | -0.0194 |
| ALPHA_010 | -0.0182 |
| ALPHA_012 | -0.0069 |
| ALPHA_013 | 0.0345 |
| ALPHA_014 | -0.0063 |
| ALPHA_015 | 0.0076 |
| ALPHA_016 | 0.0483 |
| ALPHA_017 | -0.0478 |
| ALPHA_018 | -0.0324 |
| ALPHA_019 | -0.0974 |
| ALPHA_020 | -0.0315 |
| ALPHA_021 | -0.0007 |
| ALPHA_022 | 0.0377 |
| ALPHA_023 | -0.0152 |
| ALPHA_024 | -0.0023 |
| ALPHA_025 | -0.0343 |
| ALPHA_026 | 0.0420 |
| ALPHA_028 | 0.0097 |
| ALPHA_030 | -0.0112 |
| ALPHA_031 | -0.0105 |
| ALPHA_032 | -0.0260 |
| ALPHA_033 | -0.0308 |
| ALPHA_034 | 0.0010 |
| ALPHA_035 | -0.0028 |
| ALPHA_036 | -0.0415 |
| ALPHA_037 | -0.0212 |
| ALPHA_038 | -0.0174 |
| ALPHA_039 | -0.0661 |
| ALPHA_040 | 0.0107 |
| ALPHA_041 | -0.0137 |
| ALPHA_042 | 0.0067 |
| ALPHA_043 | 0.0338 |
| ALPHA_044 | 0.0456 |
| ALPHA_045 | -0.0006 |
| ALPHA_046 | -0.0187 |
| ALPHA_049 | -0.0232 |
| ALPHA_050 | -0.0171 |
| ALPHA_051 | 0.0025 |
| ALPHA_052 | -0.0430 |
| ALPHA_053 | -0.0096 |
| ALPHA_054 | 0.0048 |
| ALPHA_055 | -0.0017 |
| ALPHA_060 | 0.0103 |
| ALPHA_101 | 0.0181 |

These weights are in-sample diagnostics. They are not an out-of-sample
combination rule.

## Factor diagnostics

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown | average turnover | slippage cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | -0.0083 | -0.0541 | -0.3019 | 0.0121 | -0.40% | 0.0505 | -23.34% | 0.0724 | 0.0264 |
| ALPHA_002 | -0.0028 | -0.0189 | -0.1163 | 0.0012 | -15.29% | -0.4035 | -27.88% | 0.0838 | 0.0306 |
| ALPHA_003 | -0.0383 | -0.2358 | -1.1060 | 0.1645 | 31.28% | 0.8040 | -16.56% | 0.0832 | 0.0304 |
| ALPHA_004 | -0.0181 | -0.1301 | -1.0225 | 0.0317 | 8.41% | 0.2839 | -23.66% | 0.0871 | 0.0318 |
| ALPHA_005 | -0.0254 | -0.1645 | -0.8436 | 0.0579 | 15.55% | 0.4512 | -23.13% | 0.0781 | 0.0285 |
| ALPHA_006 | -0.0036 | -0.0292 | -0.1833 | 0.0193 | 3.59% | 0.1589 | -14.41% | 0.0826 | 0.0302 |
| ALPHA_007 | 0.0106 | 0.0984 | 0.5324 | 0.0009 | -17.35% | -0.4558 | -25.97% | 0.0799 | 0.0292 |
| ALPHA_008 | -0.0291 | -0.2172 | -1.3083 | 0.0326 | 8.87% | 0.2920 | -23.31% | 0.0804 | 0.0294 |
| ALPHA_009 | -0.0194 | -0.1182 | -0.7920 | 0.0521 | 13.74% | 0.4208 | -24.30% | 0.0804 | 0.0294 |
| ALPHA_010 | -0.0182 | -0.1064 | -0.7266 | 0.0812 | 19.43% | 0.5551 | -23.54% | 0.0815 | 0.0298 |
| ALPHA_012 | -0.0069 | -0.0548 | -0.3888 | 0.0922 | 21.76% | 0.5961 | -18.88% | 0.0821 | 0.0300 |
| ALPHA_013 | 0.0345 | 0.2377 | 1.6730 | 0.0197 | 3.69% | 0.1639 | -24.01% | 0.0814 | 0.0298 |
| ALPHA_014 | -0.0063 | -0.0432 | -0.2736 | 0.0102 | -2.02% | 0.0119 | -23.78% | 0.0832 | 0.0304 |
| ALPHA_015 | 0.0076 | 0.0388 | 0.2525 | 0.0294 | 7.65% | 0.2641 | -24.26% | 0.0805 | 0.0294 |
| ALPHA_016 | 0.0483 | 0.3418 | 2.4570 | 0.0087 | -3.09% | -0.0222 | -22.16% | 0.0811 | 0.0297 |
| ALPHA_017 | -0.0478 | -0.4175 | -2.9894 | 0.1998 | 34.36% | 0.8826 | -14.41% | 0.0839 | 0.0307 |
| ALPHA_018 | -0.0324 | -0.2301 | -2.2995 | 0.0098 | -2.16% | 0.0032 | -20.67% | 0.0859 | 0.0314 |
| ALPHA_019 | -0.0974 | -0.6117 | -2.9056 | 0.0040 | -6.88% | -0.1828 | -14.82% | 0.0414 | 0.0151 |
| ALPHA_020 | -0.0315 | -0.2621 | -1.6914 | 0.0408 | 11.10% | 0.3520 | -20.93% | 0.0855 | 0.0312 |
| ALPHA_021 | -0.0007 | -0.0049 | -0.0286 | 0.0211 | 4.43% | 0.1810 | -22.81% | 0.0581 | 0.0212 |
| ALPHA_022 | 0.0377 | 0.2971 | 1.9156 | 0.2526 | 40.80% | 0.9852 | -12.59% | 0.0832 | 0.0304 |
| ALPHA_023 | -0.0152 | -0.0973 | -0.6273 | 0.1395 | 28.34% | 0.7390 | -17.50% | 0.0788 | 0.0288 |
| ALPHA_024 | -0.0023 | -0.0137 | -0.0780 | 0.0019 | -11.63% | -0.3295 | -24.82% | 0.0529 | 0.0193 |
| ALPHA_025 | -0.0343 | -0.2524 | -2.1566 | 0.0265 | 6.50% | 0.2379 | -22.81% | 0.0832 | 0.0304 |
| ALPHA_026 | 0.0420 | 0.2824 | 1.6224 | 0.0784 | 19.19% | 0.5438 | -19.93% | 0.0828 | 0.0302 |
| ALPHA_028 | 0.0097 | 0.0693 | 0.3415 | 0.0288 | 7.55% | 0.2593 | -30.66% | 0.0827 | 0.0302 |
| ALPHA_030 | -0.0112 | -0.0723 | -0.4867 | 0.0511 | 13.78% | 0.4145 | -19.70% | 0.0827 | 0.0302 |
| ALPHA_031 | -0.0105 | -0.0736 | -0.4883 | 0.0490 | 13.34% | 0.4025 | -14.94% | 0.0810 | 0.0296 |
| ALPHA_032 | -0.0260 | -0.1733 | -0.8504 | 0.0055 | -4.97% | -0.1185 | -22.85% | 0.0586 | 0.0214 |
| ALPHA_033 | -0.0308 | -0.2051 | -2.0262 | 0.0952 | 22.10% | 0.6057 | -17.06% | 0.0859 | 0.0314 |
| ALPHA_034 | 0.0010 | 0.0068 | 0.0458 | 0.0753 | 19.40% | 0.5305 | -13.73% | 0.0789 | 0.0288 |
| ALPHA_035 | -0.0028 | -0.0186 | -0.1299 | 0.0041 | -8.62% | -0.1802 | -19.08% | 0.0844 | 0.0308 |
| ALPHA_036 | -0.0415 | -0.3506 | -1.6099 | 0.0054 | -5.68% | -0.1249 | -20.28% | 0.0634 | 0.0231 |
| ALPHA_037 | -0.0212 | -0.1205 | -0.8161 | 0.0096 | -1.80% | -0.0005 | -19.20% | 0.0570 | 0.0208 |
| ALPHA_038 | -0.0174 | -0.1119 | -0.7676 | 0.0197 | 3.77% | 0.1647 | -20.58% | 0.0838 | 0.0307 |
| ALPHA_039 | -0.0661 | -0.4513 | -1.9483 | 0.0051 | -5.51% | -0.1338 | -17.86% | 0.0580 | 0.0212 |
| ALPHA_040 | 0.0107 | 0.0731 | 0.4754 | 0.0309 | 8.01% | 0.2775 | -16.59% | 0.0854 | 0.0312 |
| ALPHA_041 | -0.0137 | -0.0933 | -0.9037 | 0.0177 | 2.80% | 0.1387 | -23.42% | 0.0831 | 0.0303 |
| ALPHA_042 | 0.0067 | 0.0418 | 0.3450 | 0.0347 | 9.44% | 0.3074 | -20.44% | 0.0405 | 0.0148 |
| ALPHA_043 | 0.0338 | 0.2310 | 1.6466 | 0.0002 | -24.62% | -0.7007 | -32.69% | 0.0811 | 0.0296 |
| ALPHA_044 | 0.0456 | 0.2998 | 1.7685 | 0.0092 | -2.68% | -0.0112 | -20.08% | 0.0826 | 0.0301 |
| ALPHA_045 | -0.0006 | -0.0044 | -0.0261 | 0.1407 | 27.64% | 0.7443 | -15.48% | 0.0751 | 0.0274 |
| ALPHA_046 | -0.0187 | -0.1143 | -0.6428 | 0.0118 | -0.58% | 0.0449 | -19.16% | 0.0681 | 0.0249 |
| ALPHA_049 | -0.0232 | -0.1703 | -1.3605 | 0.0443 | 12.17% | 0.3746 | -24.35% | 0.0789 | 0.0288 |
| ALPHA_050 | -0.0171 | -0.1065 | -0.5499 | 0.0098 | -2.13% | 0.0030 | -21.84% | 0.0804 | 0.0293 |
| ALPHA_051 | 0.0025 | 0.0198 | 0.1748 | 0.0771 | 18.95% | 0.5392 | -20.51% | 0.0828 | 0.0302 |
| ALPHA_052 | -0.0430 | -0.2931 | -1.4077 | 0.0105 | -1.11% | 0.0181 | -21.46% | 0.0550 | 0.0201 |
| ALPHA_053 | -0.0096 | -0.0809 | -0.6399 | 0.0080 | -3.94% | -0.0416 | -26.81% | 0.0832 | 0.0304 |
| ALPHA_054 | 0.0048 | 0.0346 | 0.3353 | 0.0161 | 1.93% | 0.1156 | -25.60% | 0.0860 | 0.0314 |
| ALPHA_055 | -0.0017 | -0.0114 | -0.0662 | 0.0090 | -2.63% | -0.0151 | -24.90% | 0.0795 | 0.0290 |
| ALPHA_060 | 0.0103 | 0.0727 | 0.6986 | 0.0099 | -1.97% | 0.0042 | -23.44% | 0.0804 | 0.0293 |
| ALPHA_101 | 0.0181 | 0.1150 | 1.0473 | 0.0133 | 0.28% | 0.0709 | -29.74% | 0.0816 | 0.0298 |
| EQUAL_WEIGHTED_COMPOSITE | -0.0138 | -0.0890 | -0.7149 | 0.0081 | -3.65% | -0.0388 | -23.39% | 0.0844 | 0.0308 |
| IC_WEIGHTED_COMPOSITE | 0.0826 | 0.6074 | 3.5590 | 0.0741 | 18.26% | 0.5280 | -23.03% | 0.0787 | 0.0287 |
| ICIR_WEIGHTED_COMPOSITE | 0.0819 | 0.6063 | 3.5552 | 0.0533 | 14.26% | 0.4283 | -26.32% | 0.0798 | 0.0291 |
| CORRELATION_DISCOUNTED_COMPOSITE | 0.1693 | 1.0880 | 6.2728 | 0.0268 | 6.74% | 0.2404 | -21.99% | 0.0821 | 0.0300 |
| ALPHA_PRODUCT_INTERACTION | 0.0253 | 0.1600 | 1.0433 | 0.1530 | 28.91% | 0.7745 | -12.31% | 0.0859 | 0.0314 |
| CONDITIONAL_RANK_INTERACTION | 0.0079 | 0.0618 | 0.3589 | 0.3153 | 44.83% | 1.0942 | -11.25% | 0.0816 | 0.0298 |
| NEUTRALIZED_IC_COMPOSITE | 0.0810 | 0.5614 | 3.5598 | 0.0405 | 10.93% | 0.3507 | -22.73% | 0.0825 | 0.0302 |

IC is monthly Spearman Rank IC. ICIR is not annualized. DSR is computed on
non-annualized daily measured returns using the Bailey-Lopez de Prado formula
with the Euler-Mascheroni mix. All 52 alphas and all composites are
reported; weak or negative diagnostics are retained.

## Long-short decile spread diagnostics

| factor | LS Sharpe | LS Ann Return | LS Max DD | Win Rate | Decile Spread Mean | Monotonicity | Total Turnover |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | 0.7463 | 4.20% | 5.81% | 51.88% | -0.0022 | -0.3818 | 55.1747 |
| ALPHA_002 | -1.2182 | -7.54% | 21.05% | 47.84% | -0.0008 | -0.0788 | 61.2925 |
| ALPHA_003 | 0.2884 | 1.67% | 8.04% | 50.63% | -0.0009 | 0.0424 | 61.2879 |
| ALPHA_004 | -0.6269 | -3.65% | 20.43% | 46.44% | -0.0007 | -0.2000 | 59.4265 |
| ALPHA_005 | -0.2806 | -1.71% | 12.31% | 48.95% | 0.0007 | -0.1879 | 58.8830 |
| ALPHA_006 | -0.4843 | -2.89% | 11.87% | 47.42% | -0.0005 | -0.3697 | 62.4488 |
| ALPHA_007 | -2.1854 | -12.99% | 31.73% | 44.35% | -0.0028 | -0.5273 | 48.2519 |
| ALPHA_008 | -1.0168 | -6.17% | 21.37% | 46.30% | -0.0030 | -0.4424 | 59.7947 |
| ALPHA_009 | 0.7612 | 4.58% | 11.29% | 51.60% | 0.0003 | 0.0303 | 58.1070 |
| ALPHA_010 | 0.7027 | 4.18% | 13.12% | 49.79% | 0.0001 | 0.1758 | 58.7975 |
| ALPHA_012 | 0.6834 | 4.16% | 6.69% | 51.60% | 0.0002 | 0.0182 | 59.0552 |
| ALPHA_013 | -0.2569 | -1.52% | 9.62% | 50.21% | -0.0005 | -0.0182 | 58.2831 |
| ALPHA_014 | -0.3348 | -2.04% | 9.91% | 48.95% | 0.0004 | -0.3576 | 60.4002 |
| ALPHA_015 | 0.3050 | 2.42% | 9.83% | 52.44% | 0.0007 | 0.0788 | 61.2483 |
| ALPHA_016 | -0.1838 | -1.08% | 8.86% | 48.81% | -0.0011 | -0.4424 | 58.4241 |
| ALPHA_017 | 1.1584 | 6.64% | 9.62% | 53.14% | -0.0006 | -0.1515 | 59.7488 |
| ALPHA_018 | 0.1366 | 0.82% | 12.01% | 49.09% | 0.0008 | -0.3939 | 60.6734 |
| ALPHA_019 | -1.8232 | -8.63% | 25.55% | 43.46% | -0.0021 | -0.4667 | 28.1241 |
| ALPHA_020 | -0.1942 | -1.17% | 10.95% | 51.46% | -0.0004 | -0.2364 | 60.5368 |
| ALPHA_021 | -0.6901 | -4.04% | 14.40% | 48.95% | -0.0007 | -0.3212 | 41.8626 |
| ALPHA_022 | 0.5265 | 3.15% | 4.77% | 51.74% | -0.0011 | -0.4909 | 60.5954 |
| ALPHA_023 | 0.0172 | 0.10% | 11.08% | 48.81% | -0.0004 | -0.5636 | 58.8885 |
| ALPHA_024 | -0.9209 | -4.93% | 18.43% | 48.34% | -0.0017 | -0.1152 | 34.4216 |
| ALPHA_025 | 0.1158 | 0.66% | 16.92% | 49.51% | -0.0008 | -0.3091 | 60.6065 |
| ALPHA_026 | -0.4514 | -2.70% | 13.66% | 48.81% | 0.0005 | 0.3333 | 60.6917 |
| ALPHA_028 | 0.6513 | 3.80% | 9.11% | 52.58% | -0.0009 | -0.1758 | 60.5145 |
| ALPHA_030 | 0.3136 | 1.81% | 14.40% | 51.60% | -0.0028 | -0.1758 | 61.2052 |
| ALPHA_031 | -0.3327 | -1.95% | 8.64% | 48.54% | 0.0002 | -0.3333 | 58.1563 |
| ALPHA_032 | -0.5739 | -2.79% | 15.17% | 47.69% | -0.0022 | -0.3455 | 41.6993 |
| ALPHA_033 | 0.8914 | 5.24% | 8.49% | 50.49% | -0.0003 | -0.5636 | 61.6618 |
| ALPHA_034 | 0.9680 | 5.86% | 6.36% | 52.72% | -0.0006 | -0.4788 | 58.2409 |
| ALPHA_035 | -1.0286 | -6.19% | 19.62% | 47.28% | -0.0016 | -0.2970 | 60.3869 |
| ALPHA_036 | 0.0626 | 0.34% | 7.62% | 49.26% | 0.0035 | 0.4182 | 46.2908 |
| ALPHA_037 | 0.0229 | 0.11% | 12.36% | 48.71% | -0.0026 | -0.0667 | 39.8460 |
| ALPHA_038 | -0.8145 | -4.74% | 18.88% | 48.95% | -0.0020 | -0.5152 | 59.6707 |
| ALPHA_039 | -1.4173 | -7.02% | 20.34% | 45.88% | 0.0008 | -0.1273 | 40.0846 |
| ALPHA_040 | -0.8215 | -4.89% | 16.06% | 47.98% | -0.0020 | -0.3939 | 62.2862 |
| ALPHA_041 | -0.1675 | -1.02% | 16.35% | 48.95% | 0.0007 | -0.0909 | 59.0983 |
| ALPHA_042 | 0.1515 | 0.94% | 14.28% | 51.88% | -0.0019 | -0.1879 | 42.5049 |
| ALPHA_043 | -2.3610 | -13.82% | 34.25% | 41.00% | -0.0005 | -0.2242 | 60.0741 |
| ALPHA_044 | -0.2959 | -1.80% | 15.83% | 49.37% | 0.0026 | -0.0909 | 60.0341 |
| ALPHA_045 | 0.2430 | 1.41% | 9.34% | 49.37% | 0.0016 | 0.7212 | 54.6218 |
| ALPHA_046 | -0.4678 | -2.79% | 11.03% | 48.95% | -0.0017 | -0.5758 | 53.8122 |
| ALPHA_049 | 1.2320 | 7.33% | 8.64% | 53.00% | 0.0010 | 0.3939 | 59.1451 |
| ALPHA_050 | -1.2014 | -8.14% | 22.56% | 46.03% | 0.0016 | 0.2970 | 61.4806 |
| ALPHA_051 | 0.7861 | 4.56% | 8.11% | 51.05% | -0.0003 | -0.1394 | 60.3689 |
| ALPHA_052 | -0.3249 | -1.63% | 16.21% | 48.89% | -0.0000 | -0.1030 | 40.0882 |
| ALPHA_053 | 0.0765 | 0.48% | 12.56% | 51.60% | -0.0005 | -0.0545 | 60.9197 |
| ALPHA_054 | -0.5805 | -3.56% | 18.12% | 49.65% | -0.0000 | -0.2364 | 61.7681 |
| ALPHA_055 | -0.8510 | -4.91% | 13.80% | 49.09% | -0.0001 | 0.0545 | 58.6452 |
| ALPHA_060 | 0.2926 | 1.72% | 5.62% | 47.56% | -0.0004 | 0.1636 | 57.9660 |
| ALPHA_101 | -0.4183 | -2.56% | 14.98% | 49.93% | 0.0015 | 0.5394 | 60.3938 |
| EQUAL_WEIGHTED_COMPOSITE | -0.0963 | -0.57% | 11.64% | 51.05% | -0.0025 | -0.1879 | 60.6288 |
| IC_WEIGHTED_COMPOSITE | 0.3693 | 2.14% | 10.10% | 51.74% | -0.0002 | 0.1394 | 58.6652 |
| ICIR_WEIGHTED_COMPOSITE | 0.1548 | 0.91% | 14.58% | 51.19% | -0.0003 | 0.0545 | 58.5144 |
| CORRELATION_DISCOUNTED_COMPOSITE | 0.0607 | 0.37% | 16.60% | 51.46% | -0.0005 | -0.5152 | 59.9242 |
| ALPHA_PRODUCT_INTERACTION | 0.1253 | 0.74% | 10.90% | 50.35% | 0.0000 | 0.5394 | 61.6196 |
| CONDITIONAL_RANK_INTERACTION | 0.6315 | 3.73% | 9.85% | 51.05% | -0.0002 | -0.1879 | 60.1766 |
| NEUTRALIZED_IC_COMPOSITE | -0.2614 | -1.54% | 17.16% | 48.81% | -0.0007 | 0.1152 | 60.1761 |

Long-short decile spread backtests construct a dollar-neutral portfolio long the top decile
and short the bottom decile at monthly rebalance frequency with 5.00 bps slippage.
Monotonicity reports the Spearman rank correlation of mean returns across deciles D1..D10.

## Overfitting diagnostics (CSCV / PBO)

- Probability of Backtest Overfitting (PBO): `0.6143`
- Out-of-Sample Probability of Loss: `0.5000`
- Combinations: `70` (from `8` splits)
- Mean OOS Relative Rank: `0.4340`
- Median OOS Relative Rank: `0.4057`
- Mean IS Sharpe: `0.0871`
- Mean OOS Sharpe: `0.0059`

## Limitations

- Synthetic prices only; no vendor, private, or real market data.
- Companion open, high, low, and volume are additional synthetic draws from
  `seed + 1`; they are not observed market prints.
- VWAP is a typical-price proxy, not a traded volume-weighted average price.
- Static 50-name membership is survivorship-biased by construction.
- Close-only lag-1 execution is idealized research accounting, not brokerage.
- 5 bps slippage is a fixed diagnostic assumption, not a market-impact model.
- IC-weighted composite uses in-sample mean monthly Rank IC weights.
- This does not execute, replace, or reopen the refused 14-trial run.
- This does not grant `RESEARCH_PASS`, formal interpretation, or profitability.
