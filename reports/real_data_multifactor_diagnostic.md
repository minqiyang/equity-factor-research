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
2. Convert vendor bars to research panels: OHLC and volume are split-adjusted
   so dollar volume stays on an exact matching price/volume basis (identically
   matching unadjusted close * raw volume); vendor adjusted_close is retained
   for total-return calculations; VWAP is typical price on the split-adjusted bars.
   Missing cells stay missing.
3. Compute classical price-volume alphas `ALPHA_001`, `ALPHA_002`, `ALPHA_003`, `ALPHA_004`, `ALPHA_005`, `ALPHA_006`, `ALPHA_007`, `ALPHA_008`, `ALPHA_009`, `ALPHA_010`, `ALPHA_012`, `ALPHA_013`, `ALPHA_014`, `ALPHA_015`, `ALPHA_016`, `ALPHA_017`, `ALPHA_018`, `ALPHA_019`, `ALPHA_020`, `ALPHA_021`, `ALPHA_022`, `ALPHA_023`, `ALPHA_024`, `ALPHA_025`, `ALPHA_026`, `ALPHA_028`, `ALPHA_030`, `ALPHA_031`, `ALPHA_032`, `ALPHA_033`, `ALPHA_034`, `ALPHA_035`, `ALPHA_036`, `ALPHA_037`, `ALPHA_038`, `ALPHA_039`, `ALPHA_040`, `ALPHA_041`, `ALPHA_042`, `ALPHA_043`, `ALPHA_044`, `ALPHA_045`, `ALPHA_046`, `ALPHA_049`, `ALPHA_050`, `ALPHA_051`, `ALPHA_052`, `ALPHA_053`, `ALPHA_054`, `ALPHA_055`, `ALPHA_060`, `ALPHA_101`.
4. Build composites `EQUAL_WEIGHTED_COMPOSITE`, `IC_WEIGHTED_COMPOSITE`, `ICIR_WEIGHTED_COMPOSITE`, `CORRELATION_DISCOUNTED_COMPOSITE`, `ALPHA_PRODUCT_INTERACTION`, `CONDITIONAL_RANK_INTERACTION`, `NEUTRALIZED_IC_COMPOSITE`, `SECTOR_NEUTRAL_COMPOSITE`, `MARKET_BETA_NEUTRAL_COMPOSITE`, `REGIME_SWITCHING_COMPOSITE`, `RANDOM_FOREST_COMPOSITE`, `GRADIENT_BOOSTING_COMPOSITE` using the same M01-M11 causal parents as
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
| ALPHA_001 | -0.0056 |
| ALPHA_002 | 0.0167 |
| ALPHA_003 | 0.0349 |
| ALPHA_004 | 0.0019 |
| ALPHA_005 | -0.0071 |
| ALPHA_006 | -0.0028 |
| ALPHA_007 | -0.0075 |
| ALPHA_008 | -0.0069 |
| ALPHA_009 | 0.0119 |
| ALPHA_010 | 0.0064 |
| ALPHA_012 | 0.0155 |
| ALPHA_013 | -0.0121 |
| ALPHA_014 | -0.0072 |
| ALPHA_015 | 0.0210 |
| ALPHA_016 | -0.0085 |
| ALPHA_017 | 0.0117 |
| ALPHA_018 | -0.0009 |
| ALPHA_019 | -0.0182 |
| ALPHA_020 | 0.0230 |
| ALPHA_021 | -0.0064 |
| ALPHA_022 | -0.0083 |
| ALPHA_023 | 0.0203 |
| ALPHA_024 | 0.0301 |
| ALPHA_025 | -0.0035 |
| ALPHA_026 | 0.0064 |
| ALPHA_028 | -0.0089 |
| ALPHA_030 | 0.0052 |
| ALPHA_031 | 0.0114 |
| ALPHA_032 | 0.0029 |
| ALPHA_033 | 0.0014 |
| ALPHA_034 | 0.0011 |
| ALPHA_035 | 0.0102 |
| ALPHA_036 | 0.0165 |
| ALPHA_037 | 0.0041 |
| ALPHA_038 | 0.0046 |
| ALPHA_039 | 0.0026 |
| ALPHA_040 | 0.0045 |
| ALPHA_041 | -0.0024 |
| ALPHA_042 | 0.0174 |
| ALPHA_043 | 0.0118 |
| ALPHA_044 | -0.0023 |
| ALPHA_045 | -0.0157 |
| ALPHA_046 | 0.0130 |
| ALPHA_049 | 0.0156 |
| ALPHA_050 | 0.0174 |
| ALPHA_051 | 0.0176 |
| ALPHA_052 | -0.0134 |
| ALPHA_053 | 0.0073 |
| ALPHA_054 | 0.0068 |
| ALPHA_055 | -0.0079 |
| ALPHA_060 | -0.0150 |
| ALPHA_101 | -0.0008 |

This table retains full-sample descriptive IC summaries. Executable IC,
ICIR, correlation, neutralized, and regime composites use causal walk-forward
parents. An IC labeled at s enters the information set at t when its
execution-aligned forward-return window has closed by t.

## Factor diagnostics

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown | average turnover | slippage cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | -0.0056 | -0.0273 | -0.3087 | 0.1725 | 700.89% | 1.0392 | -40.19% | 0.0713 | 0.0887 |
| ALPHA_002 | 0.0167 | 0.1164 | 1.3089 | 0.2623 | 652.15% | 1.1409 | -30.85% | 0.0842 | 0.1048 |
| ALPHA_003 | 0.0349 | 0.1819 | 2.0643 | 0.2050 | 541.17% | 1.0815 | -32.60% | 0.0854 | 0.1064 |
| ALPHA_004 | 0.0019 | 0.0117 | 0.1210 | 0.0134 | 212.11% | 0.6398 | -36.22% | 0.0849 | 0.1056 |
| ALPHA_005 | -0.0071 | -0.0444 | -0.5103 | 0.0239 | 248.17% | 0.7181 | -26.64% | 0.0768 | 0.0957 |
| ALPHA_006 | -0.0028 | -0.0164 | -0.1809 | 0.1246 | 543.97% | 0.9821 | -38.26% | 0.0843 | 0.1048 |
| ALPHA_007 | -0.0075 | -0.0474 | -0.5364 | 0.1483 | 565.68% | 1.0140 | -27.05% | 0.0866 | 0.1078 |
| ALPHA_008 | -0.0069 | -0.0375 | -0.4526 | 0.0384 | 314.47% | 0.7817 | -27.33% | 0.0804 | 0.1002 |
| ALPHA_009 | 0.0119 | 0.0661 | 0.6801 | 0.1121 | 529.47% | 0.9592 | -25.75% | 0.0804 | 0.1002 |
| ALPHA_010 | 0.0064 | 0.0349 | 0.3430 | 0.0603 | 404.95% | 0.8538 | -28.42% | 0.0793 | 0.0988 |
| ALPHA_012 | 0.0155 | 0.0909 | 1.2252 | 0.0113 | 193.43% | 0.6190 | -31.77% | 0.0773 | 0.0962 |
| ALPHA_013 | -0.0121 | -0.0815 | -0.9423 | 0.0211 | 218.07% | 0.6986 | -30.56% | 0.0802 | 0.0998 |
| ALPHA_014 | -0.0072 | -0.0410 | -0.3918 | 0.2445 | 785.03% | 1.1245 | -33.15% | 0.0859 | 0.1070 |
| ALPHA_015 | 0.0210 | 0.0390 | 0.4087 | 0.0134 | 188.68% | 0.6345 | -32.03% | 0.0831 | 0.1036 |
| ALPHA_016 | -0.0085 | -0.0570 | -0.6576 | 0.0183 | 207.37% | 0.6771 | -37.49% | 0.0830 | 0.1032 |
| ALPHA_017 | 0.0117 | 0.0665 | 0.7917 | 0.1176 | 500.03% | 0.9679 | -28.75% | 0.0866 | 0.1079 |
| ALPHA_018 | -0.0009 | -0.0045 | -0.0576 | 0.1747 | 630.05% | 1.0485 | -33.05% | 0.0836 | 0.1041 |
| ALPHA_019 | -0.0182 | -0.0927 | -0.8551 | 0.2040 | 881.93% | 1.0821 | -31.17% | 0.0679 | 0.0845 |
| ALPHA_020 | 0.0230 | 0.1219 | 1.3584 | 0.1056 | 488.32% | 0.9501 | -29.39% | 0.0849 | 0.1058 |
| ALPHA_021 | -0.0064 | -0.0373 | -0.3877 | 0.0292 | 318.72% | 0.7413 | -44.54% | 0.0722 | 0.0899 |
| ALPHA_022 | -0.0083 | -0.0482 | -0.5220 | 0.0100 | 173.23% | 0.6024 | -33.09% | 0.0837 | 0.1043 |
| ALPHA_023 | 0.0203 | 0.1078 | 1.1642 | 0.0076 | 171.70% | 0.5711 | -28.86% | 0.0833 | 0.1036 |
| ALPHA_024 | 0.0301 | 0.1553 | 1.5713 | 0.0426 | 351.78% | 0.8006 | -26.52% | 0.0710 | 0.0884 |
| ALPHA_025 | -0.0035 | -0.0185 | -0.2088 | 0.0747 | 537.08% | 0.8869 | -37.70% | 0.0788 | 0.0982 |
| ALPHA_026 | 0.0064 | 0.0385 | 0.3855 | 0.0340 | 291.94% | 0.7645 | -34.70% | 0.0855 | 0.1064 |
| ALPHA_028 | -0.0089 | -0.0492 | -0.5569 | 0.0426 | 336.85% | 0.7996 | -42.23% | 0.0839 | 0.1044 |
| ALPHA_030 | 0.0052 | 0.0287 | 0.3244 | 0.0489 | 376.05% | 0.8235 | -36.61% | 0.0857 | 0.1066 |
| ALPHA_031 | 0.0114 | 0.0599 | 0.6893 | 0.0253 | 270.28% | 0.7273 | -31.55% | 0.0870 | 0.1082 |
| ALPHA_032 | 0.0029 | 0.0146 | 0.1649 | 0.0088 | 173.11% | 0.5913 | -27.10% | 0.0745 | 0.0928 |
| ALPHA_033 | 0.0014 | 0.0060 | 0.0712 | 0.0778 | 540.57% | 0.8914 | -41.39% | 0.0834 | 0.1038 |
| ALPHA_034 | 0.0011 | 0.0062 | 0.0669 | 0.0432 | 358.80% | 0.8078 | -32.76% | 0.0851 | 0.1058 |
| ALPHA_035 | 0.0102 | 0.0498 | 0.5108 | 0.0605 | 391.67% | 0.8567 | -28.34% | 0.0859 | 0.1069 |
| ALPHA_036 | 0.0165 | 0.0857 | 1.1403 | 0.0172 | 210.59% | 0.6729 | -26.19% | 0.0802 | 0.0999 |
| ALPHA_037 | 0.0041 | 0.0201 | 0.2079 | 0.0925 | 495.53% | 0.9242 | -39.43% | 0.0657 | 0.0817 |
| ALPHA_038 | 0.0046 | 0.0215 | 0.2527 | 0.1218 | 598.74% | 0.9743 | -30.80% | 0.0850 | 0.1058 |
| ALPHA_039 | 0.0026 | 0.0133 | 0.1413 | 0.0087 | 169.20% | 0.5888 | -34.06% | 0.0742 | 0.0925 |
| ALPHA_040 | 0.0045 | 0.0273 | 0.3224 | 0.0829 | 471.30% | 0.9046 | -34.49% | 0.0786 | 0.0978 |
| ALPHA_041 | -0.0024 | -0.0134 | -0.1304 | 0.0227 | 251.96% | 0.7102 | -33.53% | 0.0809 | 0.1007 |
| ALPHA_042 | 0.0174 | 0.0941 | 0.9254 | 0.2719 | 1098.60% | 1.1515 | -43.17% | 0.0255 | 0.0317 |
| ALPHA_043 | 0.0118 | 0.0628 | 0.6277 | 0.1951 | 659.23% | 1.0748 | -27.32% | 0.0881 | 0.1098 |
| ALPHA_044 | -0.0023 | -0.0160 | -0.1955 | 0.0051 | 134.44% | 0.5270 | -37.37% | 0.0858 | 0.1068 |
| ALPHA_045 | -0.0157 | -0.0962 | -1.0324 | 0.0321 | 246.87% | 0.7487 | -35.56% | 0.0817 | 0.1018 |
| ALPHA_046 | 0.0130 | 0.0740 | 0.8095 | 0.2535 | 979.55% | 1.1340 | -33.92% | 0.0611 | 0.0761 |
| ALPHA_049 | 0.0156 | 0.0918 | 1.0116 | 0.1929 | 727.38% | 1.0708 | -28.16% | 0.0801 | 0.0999 |
| ALPHA_050 | 0.0174 | 0.0518 | 0.6156 | 0.0267 | 233.81% | 0.7285 | -32.12% | 0.0831 | 0.1034 |
| ALPHA_051 | 0.0176 | 0.1094 | 1.1855 | 0.1839 | 712.95% | 1.0597 | -25.30% | 0.0771 | 0.0961 |
| ALPHA_052 | -0.0134 | -0.0637 | -0.7188 | 0.0402 | 329.22% | 0.7898 | -27.37% | 0.0756 | 0.0942 |
| ALPHA_053 | 0.0073 | 0.0360 | 0.3235 | 0.1171 | 463.49% | 0.9662 | -36.38% | 0.0868 | 0.1081 |
| ALPHA_054 | 0.0068 | 0.0352 | 0.3160 | 0.0615 | 352.11% | 0.8517 | -33.92% | 0.0864 | 0.1076 |
| ALPHA_055 | -0.0079 | -0.0499 | -0.5510 | 0.0740 | 344.39% | 0.8849 | -27.55% | 0.0867 | 0.1080 |
| ALPHA_060 | -0.0150 | -0.0796 | -0.7484 | 0.0660 | 471.61% | 0.8648 | -47.95% | 0.0821 | 0.1021 |
| ALPHA_101 | -0.0008 | -0.0037 | -0.0460 | 0.0136 | 201.21% | 0.6366 | -31.99% | 0.0880 | 0.1096 |
| EQUAL_WEIGHTED_COMPOSITE | 0.0092 | 0.0494 | 0.5649 | 0.0853 | 454.91% | 0.9114 | -27.14% | 0.0848 | 0.1056 |
| IC_WEIGHTED_COMPOSITE | -0.0234 | -0.1154 | -1.2900 | 0.0491 | 384.92% | 0.8205 | -31.64% | 0.0830 | 0.1034 |
| ICIR_WEIGHTED_COMPOSITE | -0.0299 | -0.1524 | -1.7190 | 0.0348 | 324.22% | 0.7694 | -29.17% | 0.0799 | 0.0995 |
| CORRELATION_DISCOUNTED_COMPOSITE | -0.0178 | -0.1060 | -1.2927 | 0.0281 | 272.01% | 0.7363 | -31.94% | 0.0812 | 0.1011 |
| ALPHA_PRODUCT_INTERACTION | -0.0080 | -0.0544 | -0.5501 | 0.1174 | 513.01% | 0.9639 | -34.64% | 0.0831 | 0.1035 |
| CONDITIONAL_RANK_INTERACTION | -0.0164 | -0.0958 | -1.0550 | 0.0021 | 96.13% | 0.4322 | -34.86% | 0.0835 | 0.1040 |
| NEUTRALIZED_IC_COMPOSITE | -0.0246 | -0.1325 | -1.5085 | 0.0480 | 356.55% | 0.8166 | -29.02% | 0.0821 | 0.1022 |
| SECTOR_NEUTRAL_COMPOSITE | -0.0247 | -0.1245 | -1.3597 | 0.0232 | 267.64% | 0.7128 | -28.20% | 0.0815 | 0.1014 |
| MARKET_BETA_NEUTRAL_COMPOSITE | -0.0233 | -0.1312 | -1.6508 | 0.0769 | 441.38% | 0.8929 | -29.02% | 0.0827 | 0.1030 |
| REGIME_SWITCHING_COMPOSITE | -0.0192 | -0.1010 | -1.1912 | 0.1112 | 552.82% | 0.9594 | -29.02% | 0.0824 | 0.1026 |
| RANDOM_FOREST_COMPOSITE | -0.0610 | -0.0919 | -0.8579 | 0.0012 | 72.19% | 0.3701 | -40.16% | 0.0640 | 0.0797 |
| GRADIENT_BOOSTING_COMPOSITE | -0.0378 | -0.0580 | -0.5580 | 0.0012 | 73.16% | 0.3717 | -40.16% | 0.0645 | 0.0804 |

IC is monthly Spearman Rank IC. ICIR is not annualized. DSR is computed on
non-annualized daily measured returns using the Bailey-Lopez de Prado formula
with the Euler-Mascheroni mix and across-trial Sharpe variance
`0.0010062222498294483`. This run evaluated
160 books and
152 distinct configurations across
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
| ALPHA_001 | 0.3102 | 3.07% | 19.28% | 51.37% | 0.0006 | -0.2606 | 195.0105 |
| ALPHA_002 | 0.4361 | 3.35% | 19.41% | 50.69% | -0.0001 | 0.4788 | 213.1217 |
| ALPHA_003 | 0.5002 | 4.54% | 13.08% | 49.96% | 0.0012 | 0.2606 | 221.3030 |
| ALPHA_004 | -0.1808 | -1.76% | 37.89% | 48.18% | 0.0025 | 0.8424 | 215.2845 |
| ALPHA_005 | -0.0382 | -0.36% | 30.56% | 48.91% | 0.0029 | 0.5758 | 201.2103 |
| ALPHA_006 | -0.1754 | -1.74% | 36.65% | 48.26% | 0.0023 | 0.5758 | 215.5393 |
| ALPHA_007 | -0.6942 | -6.93% | 59.76% | 46.77% | 0.0012 | 0.7455 | 179.4073 |
| ALPHA_008 | -0.0745 | -0.72% | 21.26% | 49.31% | 0.0017 | 0.4788 | 201.1215 |
| ALPHA_009 | 0.3119 | 2.89% | 28.47% | 49.39% | 0.0003 | -0.2727 | 200.4173 |
| ALPHA_010 | 0.1776 | 1.63% | 39.05% | 49.27% | -0.0001 | -0.4667 | 198.4953 |
| ALPHA_012 | -0.2082 | -1.67% | 31.98% | 49.72% | 0.0013 | 0.4182 | 198.2801 |
| ALPHA_013 | -0.2858 | -2.21% | 34.85% | 48.51% | 0.0012 | 0.2606 | 206.5072 |
| ALPHA_014 | 0.2928 | 2.55% | 29.35% | 50.97% | 0.0023 | 0.8424 | 214.3212 |
| ALPHA_015 | -0.1504 | -0.94% | 26.54% | 46.93% | 0.0053 | 0.1152 | 47.0600 |
| ALPHA_016 | -0.1599 | -1.21% | 38.13% | 49.76% | 0.0005 | 0.3212 | 205.0825 |
| ALPHA_017 | -0.0713 | -0.65% | 43.25% | 50.61% | 0.0013 | 0.4303 | 218.1797 |
| ALPHA_018 | 0.4889 | 4.78% | 20.77% | 49.31% | 0.0003 | 0.0667 | 191.7627 |
| ALPHA_019 | 0.4786 | 5.36% | 18.24% | 50.38% | 0.0040 | 0.7333 | 155.3558 |
| ALPHA_020 | -0.0824 | -0.82% | 34.60% | 50.57% | 0.0010 | 0.4788 | 212.4411 |
| ALPHA_021 | -0.5795 | -6.23% | 62.24% | 48.02% | 0.0022 | 0.7333 | 149.1994 |
| ALPHA_022 | -0.6933 | -5.73% | 47.30% | 47.78% | -0.0004 | -0.0424 | 207.0531 |
| ALPHA_023 | -0.5085 | -4.69% | 47.63% | 47.94% | 0.0024 | 0.5515 | 209.4101 |
| ALPHA_024 | 0.1563 | 1.45% | 30.73% | 50.95% | 0.0021 | 0.7818 | 146.2334 |
| ALPHA_025 | -0.0697 | -0.76% | 49.97% | 48.83% | 0.0001 | 0.1152 | 192.4908 |
| ALPHA_026 | -0.2609 | -2.36% | 36.60% | 50.12% | 0.0019 | 0.8182 | 216.9062 |
| ALPHA_028 | 0.0175 | 0.18% | 47.12% | 48.51% | -0.0010 | -0.5515 | 203.9150 |
| ALPHA_030 | 0.1979 | 1.95% | 24.84% | 49.19% | 0.0022 | 0.7455 | 215.3316 |
| ALPHA_031 | -0.0421 | -0.39% | 27.33% | 49.11% | 0.0000 | 0.4909 | 215.7423 |
| ALPHA_032 | -0.1667 | -1.57% | 28.62% | 48.41% | 0.0038 | 0.6000 | 185.6508 |
| ALPHA_033 | 0.0533 | 0.66% | 44.71% | 49.23% | -0.0007 | -0.4545 | 209.4504 |
| ALPHA_034 | 0.0042 | 0.04% | 34.96% | 48.83% | 0.0016 | 0.4061 | 212.7921 |
| ALPHA_035 | -0.0824 | -0.78% | 37.00% | 47.46% | 0.0026 | 0.7697 | 215.1663 |
| ALPHA_036 | -0.1624 | -1.44% | 38.47% | 50.69% | 0.0025 | 0.7091 | 202.0819 |
| ALPHA_037 | 0.3256 | 3.00% | 24.68% | 50.22% | 0.0004 | 0.3212 | 161.2890 |
| ALPHA_038 | -0.1017 | -1.12% | 43.86% | 49.15% | -0.0001 | 0.2000 | 214.4649 |
| ALPHA_039 | -0.2099 | -2.03% | 31.71% | 49.09% | 0.0031 | 0.5636 | 175.1725 |
| ALPHA_040 | 0.0124 | 0.12% | 24.22% | 49.03% | 0.0020 | 0.6121 | 202.6475 |
| ALPHA_041 | -0.0755 | -0.71% | 34.14% | 48.18% | -0.0003 | -0.3091 | 198.5092 |
| ALPHA_042 | 0.7159 | 7.01% | 18.33% | 50.69% | -0.0002 | -0.2848 | 123.1063 |
| ALPHA_043 | 0.1210 | 1.15% | 23.30% | 50.39% | 0.0009 | 0.6727 | 219.6438 |
| ALPHA_044 | -0.4835 | -3.93% | 44.68% | 48.67% | 0.0020 | 0.7091 | 215.3407 |
| ALPHA_045 | -0.0824 | -0.65% | 22.39% | 50.61% | -0.0007 | -0.2848 | 197.7389 |
| ALPHA_046 | -0.1393 | -1.37% | 30.63% | 47.70% | -0.0000 | 0.1273 | 175.1515 |
| ALPHA_049 | 0.2341 | 2.13% | 23.17% | 49.60% | -0.0005 | -0.6606 | 205.9873 |
| ALPHA_050 | 0.0106 | 0.13% | 34.48% | 49.83% | 0.0040 | 0.2485 | 167.0726 |
| ALPHA_051 | 0.1111 | 1.02% | 34.96% | 48.83% | -0.0007 | -0.1152 | 203.6437 |
| ALPHA_052 | 0.0910 | 0.85% | 17.53% | 48.72% | 0.0033 | 0.5273 | 182.2849 |
| ALPHA_053 | 0.1572 | 1.46% | 23.58% | 50.48% | 0.0003 | -0.1152 | 219.4098 |
| ALPHA_054 | -0.0596 | -0.56% | 35.39% | 49.27% | -0.0003 | -0.2000 | 214.6821 |
| ALPHA_055 | -0.2499 | -1.89% | 28.05% | 49.11% | 0.0005 | 0.3455 | 216.0214 |
| ALPHA_060 | -0.0172 | -0.20% | 33.31% | 49.60% | -0.0014 | -0.6000 | 205.4650 |
| ALPHA_101 | -0.4634 | -4.71% | 44.76% | 48.75% | -0.0006 | 0.1636 | 220.2076 |
| EQUAL_WEIGHTED_COMPOSITE | 0.0543 | 0.55% | 38.44% | 49.84% | 0.0027 | 0.8182 | 208.5257 |
| IC_WEIGHTED_COMPOSITE | 0.0436 | 0.42% | 39.57% | 49.73% | -0.0002 | 0.0909 | 205.1510 |
| ICIR_WEIGHTED_COMPOSITE | -0.0178 | -0.17% | 41.35% | 50.43% | -0.0007 | -0.1030 | 198.1400 |
| CORRELATION_DISCOUNTED_COMPOSITE | -0.5496 | -4.57% | 48.94% | 48.74% | -0.0007 | -0.0788 | 204.0947 |
| ALPHA_PRODUCT_INTERACTION | 0.4110 | 3.29% | 16.59% | 51.21% | 0.0002 | -0.3697 | 209.2009 |
| CONDITIONAL_RANK_INTERACTION | -1.0792 | -9.16% | 61.05% | 46.81% | 0.0007 | 0.0424 | 209.2089 |
| NEUTRALIZED_IC_COMPOSITE | -0.0878 | -0.78% | 34.95% | 49.32% | 0.0006 | -0.0061 | 202.3089 |
| SECTOR_NEUTRAL_COMPOSITE | -0.3090 | -2.88% | 52.68% | 48.86% | 0.0004 | 0.2606 | 204.8513 |
| MARKET_BETA_NEUTRAL_COMPOSITE | 0.0603 | 0.53% | 24.94% | 49.61% | 0.0005 | 0.0667 | 203.2673 |
| REGIME_SWITCHING_COMPOSITE | 0.2476 | 2.24% | 24.60% | 50.35% | 0.0004 | 0.1030 | 202.3973 |
| RANDOM_FOREST_COMPOSITE | 0.1380 | 0.59% | 10.29% | 47.77% | 0.0097 | 0.6242 | 14.0111 |
| GRADIENT_BOOSTING_COMPOSITE | -0.0566 | -0.22% | 15.85% | 46.50% | 0.0130 | 0.2727 | 14.0854 |

`LS Sharpe`, `LS Ann Return`, `Max DD`, and `Win Rate` summarize the sequential holding-period book. `Decile Spread Mean` is the mean top-minus-bottom quantile return on rebalance dates. Monotonicity is the Spearman rank correlation of mean rebalance-date returns across quantiles.

## Portfolio weighting and turnover penalization diagnostics

Comparison of weighting schemes and turnover penalty (λ) across key multi-factor composites:

| factor | scheme | LO Sharpe | LO Turnover | LO Return | LO Max DD | LS Sharpe | LS Turnover | LS Ann Return | LS Max DD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IC_WEIGHTED_COMPOSITE | Equal (λ=0.0) | 0.8205 | 0.0830 | 384.92% | -31.64% | 0.0436 | 205.1510 | 0.42% | 39.57% |
| IC_WEIGHTED_COMPOSITE | Inverse-Vol (λ=0.0) | 0.8230 | 0.0848 | 333.81% | -28.60% | -0.0897 | 208.8638 | -0.79% | 34.63% |
| IC_WEIGHTED_COMPOSITE | Equal (λ=0.5) | 0.9854 | 0.0409 | 453.67% | -29.45% | 0.1921 | 103.9998 | 1.27% | 19.12% |
| IC_WEIGHTED_COMPOSITE | Inverse-Vol (λ=0.5) | 0.9672 | 0.0414 | 376.55% | -29.57% | -0.0037 | 104.7094 | -0.02% | 18.92% |
| MARKET_BETA_NEUTRAL_COMPOSITE | Equal (λ=0.0) | 0.8929 | 0.0827 | 441.38% | -29.02% | 0.0603 | 203.2673 | 0.53% | 24.94% |
| MARKET_BETA_NEUTRAL_COMPOSITE | Inverse-Vol (λ=0.0) | 0.8687 | 0.0847 | 357.35% | -28.60% | -0.0536 | 207.4982 | -0.43% | 25.64% |
| MARKET_BETA_NEUTRAL_COMPOSITE | Equal (λ=0.5) | 1.0135 | 0.0408 | 465.44% | -29.53% | 0.2552 | 103.2940 | 1.61% | 20.05% |
| MARKET_BETA_NEUTRAL_COMPOSITE | Inverse-Vol (λ=0.5) | 0.9761 | 0.0413 | 368.04% | -29.63% | 0.0490 | 104.0655 | 0.28% | 19.70% |
| SECTOR_NEUTRAL_COMPOSITE | Equal (λ=0.0) | 0.7128 | 0.0815 | 267.64% | -28.20% | -0.3090 | 204.8513 | -2.88% | 52.68% |
| SECTOR_NEUTRAL_COMPOSITE | Inverse-Vol (λ=0.0) | 0.7031 | 0.0833 | 227.38% | -27.92% | -0.4187 | 208.5697 | -3.53% | 49.33% |
| SECTOR_NEUTRAL_COMPOSITE | Equal (λ=0.5) | 0.8499 | 0.0407 | 316.72% | -28.39% | -0.1725 | 103.6554 | -1.11% | 31.46% |
| SECTOR_NEUTRAL_COMPOSITE | Inverse-Vol (λ=0.5) | 0.8320 | 0.0412 | 266.33% | -28.92% | -0.3341 | 104.5105 | -1.94% | 32.35% |
| EQUAL_WEIGHTED_COMPOSITE | Equal (λ=0.0) | 0.9114 | 0.0848 | 454.91% | -27.14% | 0.0543 | 208.5257 | 0.55% | 38.44% |
| EQUAL_WEIGHTED_COMPOSITE | Inverse-Vol (λ=0.0) | 0.9201 | 0.0864 | 410.76% | -25.67% | 0.0131 | 212.8019 | 0.12% | 36.39% |
| EQUAL_WEIGHTED_COMPOSITE | Equal (λ=0.5) | 0.9806 | 0.0430 | 430.80% | -28.30% | 0.1879 | 106.9430 | 1.33% | 20.89% |
| EQUAL_WEIGHTED_COMPOSITE | Inverse-Vol (λ=0.5) | 0.9594 | 0.0432 | 367.02% | -27.91% | 0.0909 | 107.4124 | 0.58% | 20.93% |

Inverse-volatility weighting applies lagged 20-day return volatility (shift 1 source row). Turnover penalization (λ=0.5) blends previous frozen targets with fresh decision-time targets; final eligibility and net exposure constraints apply.

## Overfitting diagnostics (CSCV / PBO)

- Probability of Backtest Overfitting (PBO): `0.5286`
- Out-of-Sample Probability of Loss: `0.0000`
- Combinations: `70` (from `8` splits)
- Mean OOS Relative Rank: `0.4412`
- Median OOS Relative Rank: `0.4906`
- Mean IS Sharpe: `0.0878`
- Mean OOS Sharpe: `0.0506`

## Machine learning factor combinations and feature importances

Walk-forward non-linear factor combinations (Random Forest, Gradient Boosting)
learn empirical mappings from the classical alphas to forward returns using
expanding training windows with strictly closed forward-return labels (zero lookahead).

| composite | top features (mean importance) | evaluated rebalance count |
| --- | --- | --- |
| `RANDOM_FOREST_COMPOSITE` | `ALPHA_053` (6.4%), `ALPHA_040` (6.2%), `ALPHA_007` (4.1%) | 105 |
| `GRADIENT_BOOSTING_COMPOSITE` | `ALPHA_040` (6.8%), `ALPHA_053` (6.1%), `ALPHA_006` (4.8%) | 105 |

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
