# Real-Data Blue-Chip Multi-Factor Diagnostic

This report is `DIAGNOSTIC_ONLY`. It uses a static 50-stock liquid blue-chip
cohort from a local EODHD daily Parquet snapshot plus `SPY.US`
as the accounting benchmark. The cohort is survivorship-biased. It is not
point-in-time universe evidence, not a dataset-review decision, and not a
14-trial campaign run. Metrics are workflow diagnostics only and are not
evidence of real-world strategy profitability.

## Evidence ceiling

- Evidence ceiling: `DIAGNOSTIC_ONLY`
- Readiness decision: `diagnostic_ready_with_typed_missingness`
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
| ALPHA_001 | -0.0060 |
| ALPHA_002 | 0.0156 |
| ALPHA_003 | 0.0353 |
| ALPHA_004 | 0.0015 |
| ALPHA_005 | -0.0080 |
| ALPHA_006 | -0.0041 |
| ALPHA_007 | -0.0097 |
| ALPHA_008 | -0.0066 |
| ALPHA_009 | 0.0112 |
| ALPHA_010 | 0.0063 |
| ALPHA_012 | 0.0139 |
| ALPHA_013 | -0.0130 |
| ALPHA_014 | -0.0084 |
| ALPHA_015 | 0.0214 |
| ALPHA_016 | -0.0087 |
| ALPHA_017 | 0.0130 |
| ALPHA_018 | -0.0029 |
| ALPHA_019 | -0.0182 |
| ALPHA_020 | 0.0225 |
| ALPHA_021 | -0.0069 |
| ALPHA_022 | -0.0087 |
| ALPHA_023 | 0.0201 |
| ALPHA_024 | 0.0292 |
| ALPHA_025 | -0.0034 |
| ALPHA_026 | 0.0056 |
| ALPHA_028 | -0.0103 |
| ALPHA_030 | 0.0054 |
| ALPHA_031 | 0.0101 |
| ALPHA_032 | 0.0013 |
| ALPHA_033 | 0.0012 |
| ALPHA_034 | 0.0010 |
| ALPHA_035 | 0.0083 |
| ALPHA_036 | 0.0165 |
| ALPHA_037 | 0.0074 |
| ALPHA_038 | 0.0049 |
| ALPHA_039 | 0.0006 |
| ALPHA_040 | 0.0029 |
| ALPHA_041 | -0.0039 |
| ALPHA_042 | 0.0115 |
| ALPHA_043 | 0.0116 |
| ALPHA_044 | -0.0023 |
| ALPHA_045 | -0.0158 |
| ALPHA_046 | 0.0116 |
| ALPHA_049 | 0.0170 |
| ALPHA_050 | 0.0127 |
| ALPHA_051 | 0.0188 |
| ALPHA_052 | -0.0160 |
| ALPHA_053 | 0.0053 |
| ALPHA_054 | 0.0047 |
| ALPHA_055 | -0.0070 |
| ALPHA_060 | -0.0162 |
| ALPHA_101 | -0.0007 |

This table retains full-sample descriptive IC summaries. Executable IC,
ICIR, correlation, neutralized, and regime composites use causal walk-forward
parents. An IC labeled at s enters the information set at t when its
execution-aligned forward-return window has closed by t.

## Factor diagnostics

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown | average turnover | slippage cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | -0.0060 | -0.0292 | -0.3315 | 0.1834 | 593.22% | 0.9751 | -40.33% | 0.0713 | 0.0887 |
| ALPHA_002 | 0.0156 | 0.1089 | 1.1936 | 0.2259 | 501.76% | 1.0256 | -31.14% | 0.0842 | 0.1048 |
| ALPHA_003 | 0.0353 | 0.1836 | 2.0652 | 0.1652 | 405.82% | 0.9555 | -33.82% | 0.0854 | 0.1064 |
| ALPHA_004 | 0.0015 | 0.0092 | 0.0971 | 0.0103 | 146.64% | 0.5298 | -36.34% | 0.0849 | 0.1056 |
| ALPHA_005 | -0.0080 | -0.0504 | -0.5801 | 0.0200 | 183.03% | 0.6157 | -26.88% | 0.0768 | 0.0957 |
| ALPHA_006 | -0.0041 | -0.0243 | -0.2675 | 0.1001 | 400.03% | 0.8629 | -41.01% | 0.0843 | 0.1048 |
| ALPHA_007 | -0.0097 | -0.0621 | -0.7034 | 0.1247 | 426.98% | 0.9017 | -27.23% | 0.0866 | 0.1078 |
| ALPHA_008 | -0.0066 | -0.0366 | -0.4435 | 0.0374 | 248.80% | 0.6998 | -28.90% | 0.0804 | 0.1001 |
| ALPHA_009 | 0.0112 | 0.0624 | 0.6430 | 0.1106 | 428.81% | 0.8785 | -26.10% | 0.0804 | 0.1002 |
| ALPHA_010 | 0.0063 | 0.0345 | 0.3367 | 0.0618 | 329.41% | 0.7792 | -28.94% | 0.0793 | 0.0988 |
| ALPHA_012 | 0.0139 | 0.0804 | 1.1130 | 0.0125 | 156.20% | 0.5542 | -32.42% | 0.0773 | 0.0962 |
| ALPHA_013 | -0.0130 | -0.0876 | -1.0149 | 0.0142 | 148.42% | 0.5698 | -30.69% | 0.0802 | 0.0998 |
| ALPHA_014 | -0.0084 | -0.0480 | -0.4581 | 0.2227 | 612.99% | 1.0235 | -33.29% | 0.0859 | 0.1070 |
| ALPHA_015 | 0.0214 | 0.0399 | 0.4459 | 0.0110 | 136.02% | 0.5332 | -32.20% | 0.0831 | 0.1036 |
| ALPHA_016 | -0.0087 | -0.0579 | -0.6729 | 0.0141 | 147.84% | 0.5660 | -38.84% | 0.0830 | 0.1032 |
| ALPHA_017 | 0.0130 | 0.0741 | 0.8885 | 0.1120 | 400.74% | 0.8805 | -29.42% | 0.0866 | 0.1078 |
| ALPHA_018 | -0.0029 | -0.0145 | -0.1838 | 0.1619 | 499.11% | 0.9541 | -34.95% | 0.0836 | 0.1041 |
| ALPHA_019 | -0.0182 | -0.0930 | -0.8603 | 0.2271 | 766.73% | 1.0292 | -31.29% | 0.0679 | 0.0845 |
| ALPHA_020 | 0.0225 | 0.1191 | 1.3103 | 0.0991 | 387.44% | 0.8603 | -29.53% | 0.0849 | 0.1058 |
| ALPHA_021 | -0.0069 | -0.0406 | -0.4193 | 0.0292 | 250.54% | 0.6635 | -45.18% | 0.0722 | 0.0899 |
| ALPHA_022 | -0.0087 | -0.0502 | -0.5387 | 0.0097 | 132.31% | 0.5215 | -33.47% | 0.0837 | 0.1043 |
| ALPHA_023 | 0.0201 | 0.1066 | 1.1550 | 0.0075 | 128.98% | 0.4925 | -29.42% | 0.0833 | 0.1036 |
| ALPHA_024 | 0.0292 | 0.1503 | 1.5119 | 0.0444 | 285.94% | 0.7284 | -26.76% | 0.0710 | 0.0884 |
| ALPHA_025 | -0.0034 | -0.0179 | -0.2053 | 0.0817 | 447.59% | 0.8242 | -38.49% | 0.0788 | 0.0981 |
| ALPHA_026 | 0.0056 | 0.0334 | 0.3382 | 0.0298 | 221.17% | 0.6680 | -36.58% | 0.0855 | 0.1064 |
| ALPHA_028 | -0.0103 | -0.0569 | -0.6321 | 0.0410 | 265.59% | 0.7159 | -43.86% | 0.0839 | 0.1044 |
| ALPHA_030 | 0.0054 | 0.0299 | 0.3383 | 0.0374 | 268.07% | 0.7052 | -36.71% | 0.0857 | 0.1066 |
| ALPHA_031 | 0.0101 | 0.0525 | 0.6122 | 0.0211 | 198.40% | 0.6247 | -31.73% | 0.0870 | 0.1081 |
| ALPHA_032 | 0.0013 | 0.0065 | 0.0738 | 0.0080 | 127.56% | 0.5027 | -27.30% | 0.0745 | 0.0928 |
| ALPHA_033 | 0.0012 | 0.0052 | 0.0617 | 0.0751 | 423.56% | 0.8077 | -43.15% | 0.0834 | 0.1038 |
| ALPHA_034 | 0.0010 | 0.0057 | 0.0630 | 0.0396 | 275.76% | 0.7161 | -32.83% | 0.0851 | 0.1058 |
| ALPHA_035 | 0.0083 | 0.0402 | 0.4145 | 0.0432 | 273.12% | 0.7262 | -30.22% | 0.0859 | 0.1069 |
| ALPHA_036 | 0.0165 | 0.0861 | 1.1516 | 0.0146 | 155.39% | 0.5736 | -27.82% | 0.0802 | 0.0999 |
| ALPHA_037 | 0.0074 | 0.0363 | 0.3768 | 0.1008 | 419.44% | 0.8615 | -39.83% | 0.0657 | 0.0817 |
| ALPHA_038 | 0.0049 | 0.0225 | 0.2665 | 0.1121 | 465.89% | 0.8805 | -31.07% | 0.0850 | 0.1058 |
| ALPHA_039 | 0.0006 | 0.0033 | 0.0356 | 0.0089 | 130.87% | 0.5136 | -34.15% | 0.0742 | 0.0925 |
| ALPHA_040 | 0.0029 | 0.0176 | 0.2029 | 0.0753 | 364.22% | 0.8102 | -34.67% | 0.0786 | 0.0978 |
| ALPHA_041 | -0.0039 | -0.0214 | -0.2081 | 0.0208 | 191.99% | 0.6201 | -33.89% | 0.0809 | 0.1007 |
| ALPHA_042 | 0.0115 | 0.0617 | 0.6048 | 0.2428 | 826.57% | 1.0444 | -44.18% | 0.0255 | 0.0317 |
| ALPHA_043 | 0.0116 | 0.0616 | 0.6184 | 0.1639 | 496.15% | 0.9586 | -27.50% | 0.0881 | 0.1098 |
| ALPHA_044 | -0.0023 | -0.0161 | -0.1912 | 0.0037 | 87.68% | 0.4158 | -37.52% | 0.0858 | 0.1068 |
| ALPHA_045 | -0.0158 | -0.0975 | -1.0686 | 0.0298 | 193.06% | 0.6606 | -35.74% | 0.0817 | 0.1018 |
| ALPHA_046 | 0.0116 | 0.0661 | 0.7251 | 0.2927 | 882.81% | 1.0936 | -34.35% | 0.0611 | 0.0761 |
| ALPHA_049 | 0.0170 | 0.0997 | 1.1028 | 0.1911 | 594.44% | 0.9905 | -29.64% | 0.0801 | 0.0999 |
| ALPHA_050 | 0.0127 | 0.0386 | 0.4530 | 0.0220 | 174.15% | 0.6250 | -32.29% | 0.0831 | 0.1034 |
| ALPHA_051 | 0.0188 | 0.1172 | 1.2773 | 0.1916 | 598.11% | 0.9905 | -25.49% | 0.0771 | 0.0961 |
| ALPHA_052 | -0.0160 | -0.0758 | -0.8482 | 0.0431 | 271.42% | 0.7221 | -27.37% | 0.0756 | 0.0942 |
| ALPHA_053 | 0.0053 | 0.0261 | 0.2356 | 0.0980 | 351.68% | 0.8553 | -36.71% | 0.0868 | 0.1081 |
| ALPHA_054 | 0.0047 | 0.0241 | 0.2175 | 0.0470 | 255.81% | 0.7319 | -34.51% | 0.0864 | 0.1076 |
| ALPHA_055 | -0.0070 | -0.0442 | -0.4884 | 0.0597 | 258.88% | 0.7716 | -27.85% | 0.0867 | 0.1080 |
| ALPHA_060 | -0.0162 | -0.0858 | -0.8117 | 0.0713 | 391.01% | 0.7996 | -48.88% | 0.0821 | 0.1021 |
| ALPHA_101 | -0.0007 | -0.0033 | -0.0405 | 0.0116 | 146.27% | 0.5395 | -33.32% | 0.0880 | 0.1096 |
| EQUAL_WEIGHTED_COMPOSITE | 0.0079 | 0.0424 | 0.4872 | 0.0703 | 338.74% | 0.8006 | -27.38% | 0.0848 | 0.1055 |
| IC_WEIGHTED_COMPOSITE | -0.0246 | -0.1231 | -1.4241 | 0.0764 | 363.10% | 0.8146 | -26.67% | 0.0825 | 0.1027 |
| ICIR_WEIGHTED_COMPOSITE | -0.0326 | -0.1690 | -1.9948 | 0.0443 | 277.76% | 0.7253 | -28.22% | 0.0792 | 0.0987 |
| CORRELATION_DISCOUNTED_COMPOSITE | -0.0183 | -0.1116 | -1.3347 | 0.0554 | 296.50% | 0.7621 | -27.97% | 0.0816 | 0.1017 |
| ALPHA_PRODUCT_INTERACTION | -0.0075 | -0.0523 | -0.5227 | 0.1092 | 405.11% | 0.8724 | -34.80% | 0.0831 | 0.1036 |
| CONDITIONAL_RANK_INTERACTION | -0.0171 | -0.1004 | -1.0972 | 0.0021 | 67.29% | 0.3548 | -35.09% | 0.0835 | 0.1040 |
| NEUTRALIZED_IC_COMPOSITE | -0.0246 | -0.1350 | -1.5585 | 0.0359 | 254.67% | 0.6959 | -26.67% | 0.0824 | 0.1026 |
| SECTOR_NEUTRAL_COMPOSITE | -0.0257 | -0.1310 | -1.4933 | 0.0753 | 347.75% | 0.8116 | -27.67% | 0.0812 | 0.1011 |
| MARKET_BETA_NEUTRAL_COMPOSITE | -0.0261 | -0.1464 | -1.8516 | 0.0208 | 195.64% | 0.6194 | -28.50% | 0.0822 | 0.1023 |
| REGIME_SWITCHING_COMPOSITE | -0.0226 | -0.1201 | -1.4434 | 0.0892 | 385.63% | 0.8417 | -28.50% | 0.0823 | 0.1024 |

IC is monthly Spearman Rank IC. ICIR is not annualized. DSR is computed on
non-annualized daily measured returns using the Bailey-Lopez de Prado formula
with the Euler-Mascheroni mix and across-trial Sharpe variance
`0.0008985785135052004`. This run evaluated
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
| ALPHA_001 | 0.2796 | 2.77% | 19.50% | 50.97% | 0.0006 | -0.2485 | 194.8826 |
| ALPHA_002 | 0.4257 | 3.27% | 19.53% | 50.81% | -0.0001 | 0.4788 | 212.9288 |
| ALPHA_003 | 0.4925 | 4.48% | 13.68% | 50.04% | 0.0012 | 0.1515 | 221.0917 |
| ALPHA_004 | -0.2041 | -1.99% | 39.60% | 47.90% | 0.0025 | 0.8424 | 215.1076 |
| ALPHA_005 | -0.0586 | -0.55% | 31.24% | 48.95% | 0.0029 | 0.5758 | 201.0613 |
| ALPHA_006 | -0.2071 | -2.06% | 38.36% | 48.06% | 0.0023 | 0.5758 | 215.3684 |
| ALPHA_007 | -0.7882 | -7.88% | 63.12% | 46.61% | 0.0011 | 0.6485 | 179.3455 |
| ALPHA_008 | -0.0817 | -0.79% | 21.81% | 49.43% | 0.0017 | 0.5152 | 200.9712 |
| ALPHA_009 | 0.2866 | 2.66% | 29.36% | 49.27% | 0.0003 | -0.2848 | 200.3070 |
| ALPHA_010 | 0.1632 | 1.50% | 39.87% | 49.23% | -0.0000 | -0.5030 | 198.3735 |
| ALPHA_012 | -0.2002 | -1.61% | 32.11% | 49.84% | 0.0013 | 0.3576 | 198.1486 |
| ALPHA_013 | -0.3117 | -2.42% | 36.06% | 48.63% | 0.0012 | 0.2606 | 206.3288 |
| ALPHA_014 | 0.2820 | 2.46% | 29.46% | 51.09% | 0.0023 | 0.8545 | 214.1447 |
| ALPHA_015 | -0.1604 | -1.00% | 26.56% | 46.53% | 0.0053 | 0.1394 | 47.0191 |
| ALPHA_016 | -0.1691 | -1.28% | 38.52% | 49.64% | 0.0005 | 0.3212 | 204.9076 |
| ALPHA_017 | -0.0954 | -0.87% | 44.07% | 50.40% | 0.0013 | 0.4545 | 218.0490 |
| ALPHA_018 | 0.4544 | 4.45% | 22.47% | 49.31% | 0.0003 | -0.0788 | 191.6390 |
| ALPHA_019 | 0.4765 | 5.34% | 18.18% | 50.42% | 0.0039 | 0.7333 | 155.2524 |
| ALPHA_020 | -0.0936 | -0.93% | 34.91% | 50.57% | 0.0011 | 0.4667 | 212.2896 |
| ALPHA_021 | -0.6779 | -7.29% | 65.61% | 47.86% | 0.0021 | 0.7333 | 149.1440 |
| ALPHA_022 | -0.6995 | -5.78% | 47.79% | 47.82% | -0.0004 | -0.0424 | 206.9168 |
| ALPHA_023 | -0.5295 | -4.88% | 48.89% | 47.86% | 0.0023 | 0.5515 | 209.2666 |
| ALPHA_024 | 0.1365 | 1.27% | 31.55% | 51.00% | 0.0020 | 0.7818 | 146.1402 |
| ALPHA_025 | -0.0806 | -0.88% | 50.34% | 48.75% | 0.0000 | 0.1636 | 192.3756 |
| ALPHA_026 | -0.2634 | -2.39% | 36.91% | 50.08% | 0.0019 | 0.8182 | 216.7228 |
| ALPHA_028 | -0.0021 | -0.02% | 47.72% | 48.34% | -0.0011 | -0.5515 | 203.7876 |
| ALPHA_030 | 0.1633 | 1.62% | 25.91% | 48.79% | 0.0022 | 0.6970 | 215.1589 |
| ALPHA_031 | -0.0603 | -0.55% | 28.08% | 49.03% | 0.0000 | 0.4909 | 215.5734 |
| ALPHA_032 | -0.2006 | -1.89% | 30.81% | 48.37% | 0.0037 | 0.6000 | 185.5424 |
| ALPHA_033 | 0.0471 | 0.58% | 44.37% | 49.07% | -0.0007 | -0.4303 | 209.2743 |
| ALPHA_034 | -0.0134 | -0.12% | 36.14% | 48.79% | 0.0017 | 0.4061 | 212.6359 |
| ALPHA_035 | -0.1402 | -1.34% | 39.43% | 47.25% | 0.0025 | 0.7697 | 215.0181 |
| ALPHA_036 | -0.1844 | -1.63% | 39.29% | 50.39% | 0.0024 | 0.7091 | 201.9325 |
| ALPHA_037 | 0.3565 | 3.29% | 24.45% | 50.39% | 0.0003 | 0.4061 | 161.1344 |
| ALPHA_038 | -0.1159 | -1.27% | 44.24% | 49.07% | -0.0002 | 0.2000 | 214.2919 |
| ALPHA_039 | -0.2351 | -2.27% | 32.56% | 48.91% | 0.0031 | 0.5636 | 175.0800 |
| ALPHA_040 | -0.0200 | -0.19% | 25.31% | 49.19% | 0.0021 | 0.6485 | 202.5108 |
| ALPHA_041 | -0.1139 | -1.08% | 35.92% | 48.02% | -0.0003 | -0.3091 | 198.4009 |
| ALPHA_042 | 0.6400 | 6.28% | 18.76% | 50.65% | -0.0002 | -0.2970 | 123.0712 |
| ALPHA_043 | 0.0952 | 0.91% | 23.87% | 50.59% | 0.0009 | 0.6727 | 219.4445 |
| ALPHA_044 | -0.4820 | -3.93% | 44.68% | 48.75% | 0.0019 | 0.7091 | 215.1333 |
| ALPHA_045 | -0.0740 | -0.59% | 22.39% | 50.65% | -0.0007 | -0.3212 | 197.5762 |
| ALPHA_046 | -0.2007 | -1.97% | 34.20% | 47.42% | -0.0000 | 0.1273 | 175.0442 |
| ALPHA_049 | 0.2125 | 1.94% | 23.54% | 49.47% | -0.0005 | -0.6848 | 205.8449 |
| ALPHA_050 | -0.0012 | -0.02% | 34.48% | 49.89% | 0.0039 | 0.2485 | 166.9681 |
| ALPHA_051 | 0.1111 | 1.02% | 35.48% | 48.91% | -0.0007 | -0.1515 | 203.4726 |
| ALPHA_052 | 0.0846 | 0.79% | 17.52% | 48.68% | 0.0033 | 0.5273 | 182.1637 |
| ALPHA_053 | 0.1456 | 1.35% | 23.67% | 50.28% | 0.0004 | -0.2000 | 219.2171 |
| ALPHA_054 | -0.0812 | -0.76% | 36.24% | 49.52% | -0.0003 | -0.2727 | 214.4935 |
| ALPHA_055 | -0.2463 | -1.87% | 27.74% | 49.35% | 0.0005 | 0.3455 | 215.8208 |
| ALPHA_060 | 0.0073 | 0.08% | 32.24% | 49.76% | -0.0014 | -0.6000 | 205.2942 |
| ALPHA_101 | -0.4453 | -4.53% | 43.65% | 48.95% | -0.0005 | 0.1636 | 219.9762 |
| EQUAL_WEIGHTED_COMPOSITE | 0.0118 | 0.12% | 40.49% | 49.47% | 0.0026 | 0.8182 | 208.3964 |
| IC_WEIGHTED_COMPOSITE | 0.1013 | 1.00% | 34.65% | 50.23% | 0.0005 | -0.0182 | 204.0393 |
| ICIR_WEIGHTED_COMPOSITE | -0.0875 | -0.85% | 43.56% | 50.09% | -0.0000 | -0.1030 | 196.7359 |
| CORRELATION_DISCOUNTED_COMPOSITE | -0.3098 | -2.64% | 42.98% | 47.99% | -0.0007 | 0.1273 | 204.7525 |
| ALPHA_PRODUCT_INTERACTION | 0.3876 | 3.11% | 17.47% | 51.37% | 0.0003 | -0.3697 | 209.0629 |
| CONDITIONAL_RANK_INTERACTION | -1.0701 | -9.09% | 60.80% | 46.61% | 0.0007 | 0.0424 | 209.0496 |
| NEUTRALIZED_IC_COMPOSITE | -0.0871 | -0.79% | 32.18% | 49.52% | 0.0006 | 0.1030 | 203.2938 |
| SECTOR_NEUTRAL_COMPOSITE | 0.0186 | 0.18% | 35.98% | 49.77% | 0.0003 | -0.1636 | 203.3337 |
| MARKET_BETA_NEUTRAL_COMPOSITE | -0.2819 | -2.47% | 32.62% | 48.98% | 0.0012 | 0.0182 | 201.6726 |
| REGIME_SWITCHING_COMPOSITE | 0.1188 | 1.08% | 26.75% | 50.27% | 0.0010 | 0.0667 | 202.3237 |

`LS Sharpe`, `LS Ann Return`, `Max DD`, and `Win Rate` summarize the sequential holding-period book. `Decile Spread Mean` is the mean top-minus-bottom quantile return on rebalance dates. Monotonicity is the Spearman rank correlation of mean rebalance-date returns across quantiles.

## Portfolio weighting and turnover penalization diagnostics

Comparison of weighting schemes and turnover penalty (λ) across key multi-factor composites:

| factor | scheme | LO Sharpe | LO Turnover | LO Return | LO Max DD | LS Sharpe | LS Turnover | LS Ann Return | LS Max DD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IC_WEIGHTED_COMPOSITE | Equal (λ=0.0) | 0.8146 | 0.0825 | 363.10% | -26.67% | 0.1013 | 204.0393 | 1.00% | 34.65% |
| IC_WEIGHTED_COMPOSITE | Inverse-Vol (λ=0.0) | 0.7659 | 0.0836 | 279.94% | -26.39% | -0.0852 | 206.7832 | -0.77% | 33.65% |
| IC_WEIGHTED_COMPOSITE | Equal (λ=0.5) | 0.8985 | 0.0411 | 349.00% | -28.41% | 0.0841 | 104.0808 | 0.57% | 20.84% |
| IC_WEIGHTED_COMPOSITE | Inverse-Vol (λ=0.5) | 0.8458 | 0.0413 | 273.06% | -28.60% | -0.1524 | 104.5196 | -0.93% | 24.66% |
| MARKET_BETA_NEUTRAL_COMPOSITE | Equal (λ=0.0) | 0.6194 | 0.0822 | 195.64% | -28.50% | -0.2819 | 201.6726 | -2.47% | 32.62% |
| MARKET_BETA_NEUTRAL_COMPOSITE | Inverse-Vol (λ=0.0) | 0.5665 | 0.0834 | 148.95% | -28.13% | -0.4184 | 204.4603 | -3.36% | 35.27% |
| MARKET_BETA_NEUTRAL_COMPOSITE | Equal (λ=0.5) | 0.7925 | 0.0408 | 262.58% | -29.35% | -0.1383 | 103.1920 | -0.86% | 24.32% |
| MARKET_BETA_NEUTRAL_COMPOSITE | Inverse-Vol (λ=0.5) | 0.7393 | 0.0410 | 204.15% | -29.49% | -0.3516 | 103.5000 | -1.97% | 24.15% |
| SECTOR_NEUTRAL_COMPOSITE | Equal (λ=0.0) | 0.8116 | 0.0812 | 347.75% | -27.67% | 0.0186 | 203.3337 | 0.18% | 35.98% |
| SECTOR_NEUTRAL_COMPOSITE | Inverse-Vol (λ=0.0) | 0.7750 | 0.0833 | 272.66% | -27.45% | -0.0807 | 207.7931 | -0.68% | 34.26% |
| SECTOR_NEUTRAL_COMPOSITE | Equal (λ=0.5) | 0.8599 | 0.0407 | 310.88% | -28.19% | 0.0569 | 103.6335 | 0.37% | 18.98% |
| SECTOR_NEUTRAL_COMPOSITE | Inverse-Vol (λ=0.5) | 0.8154 | 0.0412 | 245.62% | -28.77% | -0.1088 | 104.6652 | -0.64% | 22.85% |
| EQUAL_WEIGHTED_COMPOSITE | Equal (λ=0.0) | 0.8006 | 0.0848 | 338.74% | -27.38% | 0.0118 | 208.3964 | 0.12% | 40.49% |
| EQUAL_WEIGHTED_COMPOSITE | Inverse-Vol (λ=0.0) | 0.8041 | 0.0864 | 306.20% | -25.89% | -0.0332 | 212.7335 | -0.31% | 38.33% |
| EQUAL_WEIGHTED_COMPOSITE | Equal (λ=0.5) | 0.8681 | 0.0430 | 329.53% | -28.52% | 0.1331 | 106.8292 | 0.94% | 23.03% |
| EQUAL_WEIGHTED_COMPOSITE | Inverse-Vol (λ=0.5) | 0.8388 | 0.0432 | 277.30% | -28.11% | 0.0301 | 107.3051 | 0.19% | 22.90% |

Inverse-volatility weighting applies lagged 20-day return volatility (shift 1 source row). Turnover penalization (λ=0.5) blends previous frozen targets with fresh decision-time targets; final eligibility and net exposure constraints apply.

## Overfitting diagnostics (CSCV / PBO)

- Probability of Backtest Overfitting (PBO): `0.5286`
- Out-of-Sample Probability of Loss: `0.0000`
- Combinations: `70` (from `8` splits)
- Mean OOS Relative Rank: `0.4671`
- Median OOS Relative Rank: `0.4906`
- Mean IS Sharpe: `0.0825`
- Mean OOS Sharpe: `0.0458`

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
