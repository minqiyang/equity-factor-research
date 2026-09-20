# Real-Data Blue-Chip Multi-Factor Diagnostic

This report is `DIAGNOSTIC_ONLY`. It uses a static 50-stock liquid blue-chip
cohort from a local EODHD daily Parquet snapshot plus `SPY.US`
as the accounting benchmark. The cohort is survivorship-biased. It is not
point-in-time universe evidence, not a dataset-review decision, and not a
14-trial campaign run. Metrics are workflow diagnostics only and are not
evidence of real-world strategy profitability.

## Evidence ceiling

- Evidence ceiling: `DIAGNOSTIC_ONLY`
- Readiness decision: `diagnostic_ready_with_low_caveats`
- `dataset_manifest_reviewed`: `false`
- `formal_interpretation_eligible`: `false`
- Survivorship bias: `true`
- Not point-in-time universe evidence: `true`
- Protected-sample classification: `historical_evaluation`
- Cohort: static `BLUECHIP_50_COHORT` (50 names in this run)
- Benchmark: `SPY.US` vendor adjusted close

## Pipeline

1. Load local EODHD Parquet files for the requested symbols and
   `SPY.US` through `load_eod_cohort_panels`.
2. Convert vendor bars to research panels: close is `adjusted_close`; OHLC is
   scaled by `adjusted_close / close`; volume is scaled by the inverse ratio so
   dollar volume stays on a matching price/volume basis; VWAP is typical price
   on those scaled bars. Missing cells stay missing.
3. Compute classical price-volume alphas `ALPHA_001`, `ALPHA_002`, `ALPHA_003`, `ALPHA_004`, `ALPHA_005`, `ALPHA_006`, `ALPHA_007`, `ALPHA_008`, `ALPHA_009`, `ALPHA_010`, `ALPHA_012`, `ALPHA_013`, `ALPHA_014`, `ALPHA_015`, `ALPHA_016`, `ALPHA_017`, `ALPHA_018`, `ALPHA_019`, `ALPHA_020`, `ALPHA_021`, `ALPHA_022`, `ALPHA_023`, `ALPHA_024`, `ALPHA_025`, `ALPHA_026`, `ALPHA_028`, `ALPHA_030`, `ALPHA_031`, `ALPHA_032`, `ALPHA_033`, `ALPHA_034`, `ALPHA_035`, `ALPHA_036`, `ALPHA_037`, `ALPHA_038`, `ALPHA_039`, `ALPHA_040`, `ALPHA_041`, `ALPHA_042`, `ALPHA_043`, `ALPHA_044`, `ALPHA_045`, `ALPHA_046`, `ALPHA_049`, `ALPHA_050`, `ALPHA_051`, `ALPHA_052`, `ALPHA_053`, `ALPHA_054`, `ALPHA_055`, `ALPHA_060`, `ALPHA_101`.
4. Build composites `EQUAL_WEIGHTED_COMPOSITE`, `IC_WEIGHTED_COMPOSITE`, `ICIR_WEIGHTED_COMPOSITE`, `CORRELATION_DISCOUNTED_COMPOSITE`, `ALPHA_PRODUCT_INTERACTION`, `CONDITIONAL_RANK_INTERACTION`, `NEUTRALIZED_IC_COMPOSITE`, `SECTOR_NEUTRAL_COMPOSITE`, `MARKET_BETA_NEUTRAL_COMPOSITE`, `REGIME_SWITCHING_COMPOSITE` using the same M01-M11 causal parents as
   the synthetic multifactor diagnostic: closed-window walk-forward IC weights,
   lag-1 execution, frozen decision-time smoothing targets, netted gross
   exposure, and solvency guards.
5. Measure monthly Spearman Rank IC versus 21-source-row forward returns that
   start at the lag-1 execution close.
6. Run the existing long-only monthly backtester with `5.00`
   bps slippage and `5` names, using `SPY.US` as
   the accounting benchmark.
7. Run dollar-neutral long-short quantile spread backtests.
8. Compute DSR with Euler-Mascheroni mix and across-trial Sharpe variance, and
   PBO across the evaluated alphas.

## Configuration

- Data directory: `<redacted-local-eodhd-snapshot>`
- Inventory: `<redacted-local-per-stock-coverage-inventory>`
- Requested source window: `2016-08-08` to `2026-08-07`
- Asset count: `50`
- Source date range: `2016-08-08` to `2026-08-07`
- Source rows: `2514`
- Evaluation date range: `2016-09-13` to `2026-08-07`
- Rebalance frequency: `ME`
- Selected assets per rebalance: `5`
- Signal lag: `1` source row
- Execution timing: `after_close_signal_next_observed_close_v1`
- Transaction cost: `0.00` bps
- Slippage: `5.00` bps
- Zero cost or slippage diagnostic: `True`
- Benchmark: `SPY.US` vendor adjusted close
- Timing contract: `after_close_signal_next_observed_close_v1`
- DSR expected-maximum mix: Euler-Mascheroni constant `np.euler_gamma`
- PBO splits: `8`
- VWAP: typical price `(high + low + close) / 3` on split-adjusted bars
- Composite IC weights: causal expanding mean monthly Rank IC of the 52 evaluated alphas
- Walk-forward ICIR and correlation weights: expanding window at each monthly rebalance; monthly ICs labeled strictly before t whose execution-aligned forward-return windows have closed by t (`source_row(s) + 1 + 21 <= source_row(t)`)
- Volatility proxy: 20-day rolling return standard deviation, min_periods=5, no backfill
- Sector map: 5 balanced diagnostic cohorts across the loaded assets
- Market beta proxy: 60-day rolling return beta against equal-weighted market return, min_periods=20, no backfill
- Volatility regime proxy: 60-day rolling return volatility against expanding historical median, min_periods=20, no lookahead
- Long-short quantiles: `10`
- Long-only weighting scheme: `equal`
- Long-short weighting scheme: `equal`
- Turnover penalty lambda: `0.00`
- Volatility window: `20`
- Cash-dividend overlay: refused (PIT-007); vendor adjusted close is the return basis

## In-sample IC summaries (descriptive only)

| factor | mean monthly Rank IC |
| --- | --- |
| ALPHA_001 | -0.0075 |
| ALPHA_002 | 0.0162 |
| ALPHA_003 | -0.0249 |
| ALPHA_004 | 0.0050 |
| ALPHA_005 | -0.0053 |
| ALPHA_006 | -0.0024 |
| ALPHA_007 | -0.0073 |
| ALPHA_008 | -0.0052 |
| ALPHA_009 | 0.0111 |
| ALPHA_010 | 0.0054 |
| ALPHA_012 | 0.0165 |
| ALPHA_013 | 0.0095 |
| ALPHA_014 | -0.0075 |
| ALPHA_015 | -0.0262 |
| ALPHA_016 | 0.0047 |
| ALPHA_017 | 0.0139 |
| ALPHA_018 | -0.0051 |
| ALPHA_019 | -0.0196 |
| ALPHA_020 | 0.0250 |
| ALPHA_021 | -0.0062 |
| ALPHA_022 | -0.0090 |
| ALPHA_023 | 0.0193 |
| ALPHA_024 | 0.0252 |
| ALPHA_025 | -0.0022 |
| ALPHA_026 | 0.0091 |
| ALPHA_028 | -0.0102 |
| ALPHA_030 | 0.0055 |
| ALPHA_031 | 0.0119 |
| ALPHA_032 | 0.0012 |
| ALPHA_033 | 0.0014 |
| ALPHA_034 | 0.0004 |
| ALPHA_035 | 0.0111 |
| ALPHA_036 | 0.0164 |
| ALPHA_037 | 0.0034 |
| ALPHA_038 | 0.0056 |
| ALPHA_039 | 0.0034 |
| ALPHA_040 | 0.0027 |
| ALPHA_041 | -0.0047 |
| ALPHA_042 | 0.0106 |
| ALPHA_043 | 0.0125 |
| ALPHA_044 | -0.0072 |
| ALPHA_045 | -0.0160 |
| ALPHA_046 | 0.0016 |
| ALPHA_049 | 0.0168 |
| ALPHA_050 | -0.0096 |
| ALPHA_051 | 0.0163 |
| ALPHA_052 | -0.0132 |
| ALPHA_053 | 0.0072 |
| ALPHA_054 | 0.0068 |
| ALPHA_055 | -0.0132 |
| ALPHA_060 | -0.0136 |
| ALPHA_101 | -0.0008 |

This table retains full-sample descriptive IC summaries. Executable IC,
ICIR, correlation, neutralized, and regime composites use causal walk-forward
parents. An IC labeled at s enters the information set at t when its
execution-aligned forward-return window has closed by t.

## Factor diagnostics

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown | average turnover | slippage cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | -0.0075 | -0.0365 | -0.4077 | 0.1212 | 685.74% | 1.0311 | -40.19% | 0.0713 | 0.0887 |
| ALPHA_002 | 0.0162 | 0.1129 | 1.2646 | 0.2014 | 651.94% | 1.1410 | -30.85% | 0.0841 | 0.1046 |
| ALPHA_003 | -0.0249 | -0.1283 | -1.3193 | 0.0188 | 252.20% | 0.7499 | -31.33% | 0.0833 | 0.1037 |
| ALPHA_004 | 0.0050 | 0.0309 | 0.3449 | 0.0038 | 152.93% | 0.5655 | -29.47% | 0.0839 | 0.1043 |
| ALPHA_005 | -0.0053 | -0.0332 | -0.3821 | 0.0211 | 289.96% | 0.7658 | -28.29% | 0.0775 | 0.0966 |
| ALPHA_006 | -0.0024 | -0.0141 | -0.1558 | 0.0672 | 502.29% | 0.9361 | -40.73% | 0.0851 | 0.1058 |
| ALPHA_007 | -0.0073 | -0.0468 | -0.5328 | 0.0958 | 543.30% | 0.9957 | -27.05% | 0.0869 | 0.1082 |
| ALPHA_008 | -0.0052 | -0.0289 | -0.3499 | 0.0382 | 384.46% | 0.8455 | -27.39% | 0.0791 | 0.0986 |
| ALPHA_009 | 0.0111 | 0.0609 | 0.6376 | 0.1094 | 631.24% | 1.0217 | -25.75% | 0.0802 | 0.1000 |
| ALPHA_010 | 0.0054 | 0.0291 | 0.2885 | 0.0695 | 517.35% | 0.9421 | -28.42% | 0.0793 | 0.0988 |
| ALPHA_012 | 0.0165 | 0.0953 | 1.2383 | 0.0063 | 192.80% | 0.6158 | -31.77% | 0.0763 | 0.0951 |
| ALPHA_013 | 0.0095 | 0.0757 | 0.9290 | 0.0104 | 210.94% | 0.6778 | -31.01% | 0.0788 | 0.0981 |
| ALPHA_014 | -0.0075 | -0.0424 | -0.4081 | 0.1558 | 722.72% | 1.0867 | -33.15% | 0.0859 | 0.1070 |
| ALPHA_015 | -0.0262 | -0.0478 | -0.4984 | 0.0519 | 402.73% | 0.8871 | -25.93% | 0.0805 | 0.1002 |
| ALPHA_016 | 0.0047 | 0.0337 | 0.4080 | 0.0030 | 133.93% | 0.5377 | -34.58% | 0.0828 | 0.1030 |
| ALPHA_017 | 0.0139 | 0.0771 | 0.9347 | 0.0780 | 485.51% | 0.9589 | -28.75% | 0.0866 | 0.1079 |
| ALPHA_018 | -0.0051 | -0.0262 | -0.3317 | 0.1167 | 606.88% | 1.0333 | -31.68% | 0.0836 | 0.1041 |
| ALPHA_019 | -0.0196 | -0.0997 | -0.9220 | 0.1434 | 858.46% | 1.0711 | -31.17% | 0.0677 | 0.0843 |
| ALPHA_020 | 0.0250 | 0.1309 | 1.4995 | 0.0460 | 411.60% | 0.8766 | -28.68% | 0.0852 | 0.1062 |
| ALPHA_021 | -0.0062 | -0.0359 | -0.3796 | 0.0184 | 321.01% | 0.7439 | -44.54% | 0.0725 | 0.0903 |
| ALPHA_022 | -0.0090 | -0.0524 | -0.5631 | 0.0108 | 220.30% | 0.6764 | -33.19% | 0.0827 | 0.1031 |
| ALPHA_023 | 0.0193 | 0.1020 | 1.1271 | 0.0039 | 166.90% | 0.5615 | -31.16% | 0.0834 | 0.1038 |
| ALPHA_024 | 0.0252 | 0.1319 | 1.3883 | 0.0251 | 343.44% | 0.7916 | -26.52% | 0.0714 | 0.0888 |
| ALPHA_025 | -0.0022 | -0.0110 | -0.1283 | 0.1250 | 859.49% | 1.0441 | -41.57% | 0.0784 | 0.0976 |
| ALPHA_026 | 0.0091 | 0.0540 | 0.5340 | 0.0253 | 311.56% | 0.7879 | -33.29% | 0.0857 | 0.1066 |
| ALPHA_028 | -0.0102 | -0.0570 | -0.6512 | 0.0237 | 318.55% | 0.7828 | -39.99% | 0.0830 | 0.1033 |
| ALPHA_030 | 0.0055 | 0.0301 | 0.3430 | 0.0324 | 380.78% | 0.8282 | -36.61% | 0.0860 | 0.1070 |
| ALPHA_031 | 0.0119 | 0.0625 | 0.7056 | 0.0193 | 303.67% | 0.7559 | -29.95% | 0.0865 | 0.1076 |
| ALPHA_032 | 0.0012 | 0.0060 | 0.0680 | 0.0035 | 155.78% | 0.5550 | -27.10% | 0.0738 | 0.0920 |
| ALPHA_033 | 0.0014 | 0.0060 | 0.0712 | 0.0523 | 540.57% | 0.8914 | -41.39% | 0.0834 | 0.1038 |
| ALPHA_034 | 0.0004 | 0.0022 | 0.0245 | 0.0187 | 315.43% | 0.7566 | -32.76% | 0.0853 | 0.1061 |
| ALPHA_035 | 0.0111 | 0.0546 | 0.5584 | 0.0309 | 359.14% | 0.8208 | -27.53% | 0.0863 | 0.1074 |
| ALPHA_036 | 0.0164 | 0.0861 | 1.1298 | 0.0120 | 227.96% | 0.6916 | -30.81% | 0.0799 | 0.0995 |
| ALPHA_037 | 0.0034 | 0.0164 | 0.1660 | 0.0749 | 535.35% | 0.9528 | -39.41% | 0.0664 | 0.0827 |
| ALPHA_038 | 0.0056 | 0.0257 | 0.3023 | 0.0859 | 602.59% | 0.9753 | -30.80% | 0.0853 | 0.1062 |
| ALPHA_039 | 0.0034 | 0.0173 | 0.1875 | 0.0097 | 215.00% | 0.6655 | -29.78% | 0.0744 | 0.0927 |
| ALPHA_040 | 0.0027 | 0.0163 | 0.1930 | 0.0538 | 470.90% | 0.8988 | -34.49% | 0.0786 | 0.0978 |
| ALPHA_041 | -0.0047 | -0.0259 | -0.2546 | 0.0196 | 291.39% | 0.7550 | -33.53% | 0.0803 | 0.1000 |
| ALPHA_042 | 0.0106 | 0.0574 | 0.5595 | 0.2869 | 1211.42% | 1.2312 | -38.43% | 0.0261 | 0.0325 |
| ALPHA_043 | 0.0125 | 0.0659 | 0.6580 | 0.1684 | 706.93% | 1.1079 | -27.32% | 0.0878 | 0.1094 |
| ALPHA_044 | -0.0072 | -0.0489 | -0.6099 | 0.0021 | 123.77% | 0.5022 | -37.84% | 0.0858 | 0.1067 |
| ALPHA_045 | -0.0160 | -0.0951 | -0.9770 | 0.0131 | 225.57% | 0.6979 | -38.87% | 0.0803 | 0.1000 |
| ALPHA_046 | 0.0016 | 0.0097 | 0.1121 | 0.1973 | 982.14% | 1.1389 | -32.31% | 0.0622 | 0.0774 |
| ALPHA_049 | 0.0168 | 0.1003 | 1.0770 | 0.1388 | 739.11% | 1.0661 | -28.75% | 0.0793 | 0.0989 |
| ALPHA_050 | -0.0096 | -0.0269 | -0.2906 | 0.0256 | 283.66% | 0.7848 | -34.53% | 0.0821 | 0.1023 |
| ALPHA_051 | 0.0163 | 0.0970 | 1.0125 | 0.1433 | 755.43% | 1.0724 | -25.30% | 0.0765 | 0.0953 |
| ALPHA_052 | -0.0132 | -0.0628 | -0.7003 | 0.0316 | 358.54% | 0.8195 | -27.36% | 0.0755 | 0.0940 |
| ALPHA_053 | 0.0072 | 0.0358 | 0.3222 | 0.0774 | 453.71% | 0.9567 | -36.38% | 0.0868 | 0.1081 |
| ALPHA_054 | 0.0068 | 0.0349 | 0.3139 | 0.0409 | 352.58% | 0.8534 | -33.92% | 0.0864 | 0.1076 |
| ALPHA_055 | -0.0132 | -0.0854 | -0.9271 | 0.0630 | 401.98% | 0.9268 | -27.43% | 0.0865 | 0.1077 |
| ALPHA_060 | -0.0136 | -0.0727 | -0.6834 | 0.0638 | 534.69% | 0.9242 | -41.57% | 0.0815 | 0.1014 |
| ALPHA_101 | -0.0008 | -0.0036 | -0.0452 | 0.0088 | 208.50% | 0.6483 | -31.99% | 0.0878 | 0.1094 |
| EQUAL_WEIGHTED_COMPOSITE | 0.0062 | 0.0329 | 0.3857 | 0.0574 | 472.60% | 0.9103 | -27.14% | 0.0853 | 0.1063 |
| IC_WEIGHTED_COMPOSITE | -0.0266 | -0.1364 | -1.3985 | 0.0017 | 118.10% | 0.4759 | -33.76% | 0.0838 | 0.1043 |
| ICIR_WEIGHTED_COMPOSITE | -0.0344 | -0.1796 | -1.8355 | 0.0011 | 102.18% | 0.4385 | -34.19% | 0.0804 | 0.1001 |
| CORRELATION_DISCOUNTED_COMPOSITE | -0.0090 | -0.0575 | -0.6561 | 0.0175 | 259.80% | 0.7408 | -28.95% | 0.0814 | 0.1014 |
| ALPHA_PRODUCT_INTERACTION | -0.0086 | -0.0575 | -0.6437 | 0.0558 | 448.68% | 0.9017 | -30.74% | 0.0829 | 0.1032 |
| CONDITIONAL_RANK_INTERACTION | -0.0157 | -0.0888 | -0.9863 | 0.0216 | 286.84% | 0.7628 | -31.76% | 0.0832 | 0.1036 |
| NEUTRALIZED_IC_COMPOSITE | -0.0260 | -0.1446 | -1.4799 | 0.0081 | 205.70% | 0.6461 | -25.53% | 0.0835 | 0.1039 |
| SECTOR_NEUTRAL_COMPOSITE | -0.0218 | -0.1141 | -1.1279 | 0.0164 | 277.41% | 0.7310 | -32.89% | 0.0833 | 0.1037 |
| MARKET_BETA_NEUTRAL_COMPOSITE | -0.0292 | -0.1689 | -1.8591 | 0.0071 | 193.02% | 0.6307 | -23.18% | 0.0822 | 0.1024 |
| REGIME_SWITCHING_COMPOSITE | -0.0242 | -0.1310 | -1.3629 | 0.0066 | 192.35% | 0.6216 | -29.30% | 0.0830 | 0.1033 |

IC is monthly Spearman Rank IC. ICIR is not annualized. DSR is computed on
non-annualized daily measured returns using the Bailey-Lopez de Prado formula
with the Euler-Mascheroni mix and across-trial Sharpe variance
`0.0011133023721743276`. This run evaluated
156 books and
148 distinct configurations across
factors, weighting, penalties, and both directions. Reproductions share a
semantic trial ID; append-only attempt events retain failures and repeated runs.
DSR uses the raw distinct count as an independent-trial upper-bound sensitivity.
Effective independence and total historical search remain unestimated. Missing
trial Sharpe dispersion withholds DSR. PBO covers the alpha-only long-only
family. Weak or negative diagnostics are retained.

## Long-short quantile spread diagnostics

Long-short quantile spread backtests construct a dollar-neutral portfolio long the top quantile
and short the bottom quantile at monthly rebalance frequency with 5.00 bps slippage.

Column groups in the table below:

- Sequential holding-period book metrics: `LS Sharpe`, `LS Ann Return`, `Max DD`, `Win Rate`. These use the lag-1 dollar-neutral long-short book return on every accounting date after the first bar.
- Rebalance-date one-day bucket diagnostics: `Decile Spread Mean`, `Monotonicity`. These use equal-weight quantile returns on month-end rebalance dates only.
- `Total Turnover` is the sequential book's cumulative absolute trade-weight change.

| factor | LS Sharpe | LS Ann Return | Max DD | Win Rate | Decile Spread Mean | Monotonicity | Total Turnover |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | 0.3059 | 3.03% | 19.49% | 51.09% | 0.0006 | -0.2848 | 194.5150 |
| ALPHA_002 | 0.4191 | 3.20% | 20.51% | 50.65% | -0.0001 | 0.4424 | 213.5467 |
| ALPHA_003 | -0.0182 | -0.18% | 41.78% | 49.19% | 0.0024 | 0.2606 | 221.0142 |
| ALPHA_004 | -0.4352 | -4.10% | 39.26% | 49.07% | 0.0011 | 0.7212 | 209.7798 |
| ALPHA_005 | -0.0569 | -0.54% | 32.49% | 49.72% | 0.0027 | 0.7333 | 201.5332 |
| ALPHA_006 | -0.2045 | -2.04% | 37.87% | 48.34% | 0.0024 | 0.4667 | 216.5095 |
| ALPHA_007 | -0.6953 | -6.94% | 59.82% | 47.09% | 0.0009 | 0.7212 | 180.3833 |
| ALPHA_008 | -0.0415 | -0.40% | 20.37% | 49.88% | 0.0021 | 0.3939 | 198.6471 |
| ALPHA_009 | 0.3611 | 3.39% | 26.51% | 50.44% | 0.0003 | -0.1515 | 199.3476 |
| ALPHA_010 | 0.2824 | 2.59% | 35.65% | 50.04% | -0.0002 | -0.4061 | 196.6251 |
| ALPHA_012 | -0.2315 | -1.84% | 31.81% | 48.87% | 0.0011 | 0.3576 | 198.1477 |
| ALPHA_013 | -0.1508 | -1.19% | 28.31% | 50.00% | 0.0014 | 0.3939 | 203.1654 |
| ALPHA_014 | 0.1856 | 1.61% | 30.53% | 50.44% | 0.0022 | 0.7333 | 214.2362 |
| ALPHA_015 | -0.6720 | -3.82% | 35.16% | 46.37% | 0.0049 | 0.2242 | 42.9917 |
| ALPHA_016 | -0.4920 | -3.89% | 38.93% | 48.10% | 0.0005 | 0.0545 | 207.4751 |
| ALPHA_017 | -0.1138 | -1.04% | 42.99% | 50.16% | 0.0015 | 0.6000 | 218.2615 |
| ALPHA_018 | 0.4168 | 4.07% | 20.39% | 49.52% | 0.0002 | -0.0303 | 190.5695 |
| ALPHA_019 | 0.4600 | 5.15% | 19.26% | 50.11% | 0.0038 | 0.7455 | 154.7751 |
| ALPHA_020 | -0.2446 | -2.45% | 37.54% | 50.40% | 0.0012 | 0.5879 | 212.9837 |
| ALPHA_021 | -0.5477 | -5.89% | 61.00% | 48.06% | 0.0021 | 0.7333 | 149.4042 |
| ALPHA_022 | -0.6810 | -5.64% | 45.12% | 47.98% | -0.0005 | -0.0788 | 206.6037 |
| ALPHA_023 | -0.5950 | -5.51% | 52.05% | 48.18% | 0.0021 | 0.5515 | 210.0605 |
| ALPHA_024 | 0.1056 | 1.00% | 34.63% | 50.65% | 0.0020 | 0.7455 | 146.3574 |
| ALPHA_025 | -0.0712 | -0.80% | 48.50% | 49.80% | 0.0005 | 0.2606 | 187.5129 |
| ALPHA_026 | -0.1682 | -1.52% | 36.36% | 50.16% | 0.0020 | 0.7333 | 217.6123 |
| ALPHA_028 | -0.0795 | -0.82% | 46.83% | 48.10% | -0.0009 | -0.5394 | 203.0654 |
| ALPHA_030 | 0.2007 | 1.99% | 25.06% | 49.15% | 0.0022 | 0.6970 | 215.7353 |
| ALPHA_031 | 0.0146 | 0.13% | 20.60% | 48.67% | 0.0001 | 0.5152 | 215.2139 |
| ALPHA_032 | -0.2217 | -2.10% | 32.78% | 48.24% | 0.0035 | 0.4667 | 183.9205 |
| ALPHA_033 | 0.0533 | 0.66% | 44.71% | 49.23% | -0.0007 | -0.4545 | 209.4504 |
| ALPHA_034 | -0.0528 | -0.49% | 38.31% | 48.99% | 0.0016 | 0.3818 | 213.2643 |
| ALPHA_035 | -0.1526 | -1.45% | 38.18% | 47.54% | 0.0026 | 0.8061 | 216.0568 |
| ALPHA_036 | -0.0923 | -0.82% | 34.77% | 50.95% | 0.0027 | 0.7091 | 202.4382 |
| ALPHA_037 | 0.4012 | 3.67% | 22.39% | 50.74% | 0.0004 | 0.4545 | 163.1144 |
| ALPHA_038 | -0.1026 | -1.13% | 44.48% | 49.03% | -0.0001 | 0.2121 | 215.6991 |
| ALPHA_039 | -0.1168 | -1.13% | 31.74% | 49.09% | 0.0036 | 0.6727 | 175.1486 |
| ALPHA_040 | -0.1029 | -0.97% | 30.73% | 47.78% | 0.0024 | 0.5636 | 202.2254 |
| ALPHA_041 | -0.0983 | -0.93% | 36.38% | 48.75% | -0.0005 | -0.2970 | 197.1095 |
| ALPHA_042 | 0.6877 | 6.55% | 19.98% | 49.80% | -0.0000 | -0.2727 | 122.9842 |
| ALPHA_043 | 0.1536 | 1.49% | 23.08% | 50.71% | 0.0015 | 0.7576 | 219.4075 |
| ALPHA_044 | -0.6362 | -5.12% | 49.06% | 47.29% | 0.0019 | 0.6364 | 214.3103 |
| ALPHA_045 | -0.1523 | -1.24% | 23.77% | 49.84% | -0.0005 | -0.4667 | 190.9366 |
| ALPHA_046 | -0.1362 | -1.33% | 31.44% | 47.78% | -0.0001 | 0.2485 | 177.0723 |
| ALPHA_049 | 0.4163 | 3.79% | 22.27% | 49.64% | -0.0002 | -0.5515 | 205.0601 |
| ALPHA_050 | -0.2779 | -2.97% | 43.96% | 47.11% | 0.0069 | 0.4061 | 130.4544 |
| ALPHA_051 | 0.1888 | 1.74% | 29.76% | 48.71% | -0.0003 | -0.1030 | 201.9723 |
| ALPHA_052 | 0.1041 | 0.98% | 16.43% | 48.85% | 0.0033 | 0.5879 | 182.9101 |
| ALPHA_053 | 0.1446 | 1.34% | 24.12% | 50.61% | 0.0003 | -0.1879 | 219.6214 |
| ALPHA_054 | -0.0596 | -0.56% | 35.39% | 49.27% | -0.0003 | -0.2000 | 214.6821 |
| ALPHA_055 | 0.0285 | 0.22% | 20.29% | 49.03% | -0.0001 | 0.2000 | 214.6559 |
| ALPHA_060 | -0.0593 | -0.65% | 34.91% | 49.47% | -0.0011 | -0.6242 | 205.1938 |
| ALPHA_101 | -0.4516 | -4.59% | 44.09% | 48.87% | -0.0006 | 0.1636 | 220.0075 |
| EQUAL_WEIGHTED_COMPOSITE | 0.1719 | 1.74% | 35.46% | 50.32% | 0.0027 | 0.6970 | 211.1575 |
| IC_WEIGHTED_COMPOSITE | -0.5075 | -4.81% | 54.22% | 49.36% | 0.0008 | 0.2364 | 207.3842 |
| ICIR_WEIGHTED_COMPOSITE | -0.4997 | -4.77% | 54.41% | 49.19% | 0.0001 | 0.3091 | 198.9892 |
| CORRELATION_DISCOUNTED_COMPOSITE | 0.1264 | 1.04% | 17.97% | 49.19% | 0.0007 | 0.4424 | 203.8358 |
| ALPHA_PRODUCT_INTERACTION | 0.2707 | 2.13% | 22.98% | 49.19% | -0.0001 | 0.2727 | 208.4088 |
| CONDITIONAL_RANK_INTERACTION | -0.4426 | -3.81% | 36.31% | 47.98% | -0.0008 | -0.0061 | 210.3138 |
| NEUTRALIZED_IC_COMPOSITE | -0.2988 | -2.60% | 38.85% | 49.15% | 0.0014 | 0.2364 | 206.1734 |
| SECTOR_NEUTRAL_COMPOSITE | -0.2279 | -2.19% | 49.74% | 49.19% | 0.0001 | 0.2606 | 206.7329 |
| MARKET_BETA_NEUTRAL_COMPOSITE | -0.3853 | -3.35% | 37.83% | 48.82% | 0.0004 | 0.4061 | 204.6337 |
| REGIME_SWITCHING_COMPOSITE | -0.3661 | -3.22% | 41.99% | 48.94% | 0.0006 | 0.0667 | 205.2119 |

`LS Sharpe`, `LS Ann Return`, `Max DD`, and `Win Rate` summarize the sequential holding-period book. `Decile Spread Mean` is the mean top-minus-bottom quantile return on rebalance dates. Monotonicity is the Spearman rank correlation of mean rebalance-date returns across quantiles.

## Portfolio weighting and turnover penalization diagnostics

Comparison of weighting schemes and turnover penalty (λ) across key multi-factor composites:

| factor | scheme | LO Sharpe | LO Turnover | LO Return | LO Max DD | LS Sharpe | LS Turnover | LS Ann Return | LS Max DD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IC_WEIGHTED_COMPOSITE | Equal (λ=0.0) | 0.4759 | 0.0838 | 118.10% | -33.76% | -0.5075 | 207.3842 | -4.81% | 54.22% |
| IC_WEIGHTED_COMPOSITE | Inverse-Vol (λ=0.0) | 0.5710 | 0.0844 | 150.80% | -27.52% | -0.5100 | 209.3053 | -4.42% | 49.61% |
| IC_WEIGHTED_COMPOSITE | Equal (λ=0.5) | 0.8393 | 0.0420 | 291.75% | -26.01% | -0.3084 | 105.7786 | -1.94% | 31.63% |
| IC_WEIGHTED_COMPOSITE | Inverse-Vol (λ=0.5) | 0.8652 | 0.0421 | 278.61% | -25.86% | -0.3954 | 105.9497 | -2.28% | 31.10% |
| MARKET_BETA_NEUTRAL_COMPOSITE | Equal (λ=0.0) | 0.6307 | 0.0822 | 193.02% | -23.18% | -0.3853 | 204.6337 | -3.35% | 37.83% |
| MARKET_BETA_NEUTRAL_COMPOSITE | Inverse-Vol (λ=0.0) | 0.7278 | 0.0832 | 226.23% | -22.35% | -0.3512 | 207.0571 | -2.83% | 36.82% |
| MARKET_BETA_NEUTRAL_COMPOSITE | Equal (λ=0.5) | 0.9265 | 0.0415 | 348.07% | -26.15% | -0.0569 | 104.9619 | -0.33% | 19.05% |
| MARKET_BETA_NEUTRAL_COMPOSITE | Inverse-Vol (λ=0.5) | 0.9521 | 0.0416 | 323.17% | -25.98% | -0.1406 | 105.0986 | -0.76% | 18.82% |
| SECTOR_NEUTRAL_COMPOSITE | Equal (λ=0.0) | 0.7310 | 0.0833 | 277.41% | -32.89% | -0.2279 | 206.7329 | -2.19% | 49.74% |
| SECTOR_NEUTRAL_COMPOSITE | Inverse-Vol (λ=0.0) | 0.7587 | 0.0845 | 262.25% | -29.32% | -0.3163 | 209.8631 | -2.77% | 49.50% |
| SECTOR_NEUTRAL_COMPOSITE | Equal (λ=0.5) | 0.9917 | 0.0416 | 423.10% | -25.77% | 0.0536 | 104.9647 | 0.34% | 24.78% |
| SECTOR_NEUTRAL_COMPOSITE | Inverse-Vol (λ=0.5) | 0.9703 | 0.0419 | 351.78% | -26.00% | -0.1513 | 105.6723 | -0.87% | 29.68% |
| EQUAL_WEIGHTED_COMPOSITE | Equal (λ=0.0) | 0.9103 | 0.0853 | 472.60% | -27.14% | 0.1719 | 211.1575 | 1.74% | 35.46% |
| EQUAL_WEIGHTED_COMPOSITE | Inverse-Vol (λ=0.0) | 0.9588 | 0.0869 | 471.32% | -25.67% | 0.1189 | 215.1239 | 1.10% | 32.78% |
| EQUAL_WEIGHTED_COMPOSITE | Equal (λ=0.5) | 0.9960 | 0.0430 | 470.08% | -28.34% | 0.2617 | 107.2272 | 1.85% | 16.55% |
| EQUAL_WEIGHTED_COMPOSITE | Inverse-Vol (λ=0.5) | 0.9823 | 0.0432 | 406.37% | -28.00% | 0.1140 | 107.5726 | 0.73% | 17.56% |

Inverse-volatility weighting applies lagged 20-day return volatility (shift 1 source row). Turnover penalization (λ=0.5) blends previous frozen targets with fresh decision-time targets; final eligibility and net exposure constraints apply.

## Overfitting diagnostics (CSCV / PBO)

- Probability of Backtest Overfitting (PBO): `0.4429`
- Out-of-Sample Probability of Loss: `0.0000`
- Combinations: `70` (from `8` splits)
- Mean OOS Relative Rank: `0.5084`
- Median OOS Relative Rank: `0.5283`
- Mean IS Sharpe: `0.0879`
- Mean OOS Sharpe: `0.0540`

## Limitations

- Local EODHD files only; no vendor API, credentials, or remote fetch.
- Static 50-name membership is survivorship-biased by construction.
- Vendor adjusted close is the research return basis. Event-level dividend and
  split reconciliation against an independent event table was not performed.
- A separate cash-dividend overlay is refused (PIT-007).
- VWAP is a typical-price proxy, not a traded volume-weighted average price.
- Close-only lag-1 execution is idealized research accounting, not brokerage.
- 5 bps slippage is a fixed diagnostic assumption, not a market-impact model.
- Sector map uses static balanced cohorts, not GICS point-in-time sectors.
- The 2025-05-01 through 2026-05-31 interval remains `historical_evaluation`.
- This does not execute, replace, or reopen the refused 14-trial run.
- This does not grant `RESEARCH_PASS`, formal interpretation, or profitability.
