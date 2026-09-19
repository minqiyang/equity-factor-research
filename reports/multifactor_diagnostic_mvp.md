# WorldQuant Alphas Batch 3 Multifactor Diagnostic MVP Evidence

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
2. Compute classical price-volume alphas `ALPHA_001`, `ALPHA_002`, `ALPHA_003`, `ALPHA_004`, `ALPHA_005`, `ALPHA_006`, `ALPHA_007`, `ALPHA_008`, `ALPHA_009`, `ALPHA_010`, `ALPHA_012`, `ALPHA_013`, `ALPHA_014`, `ALPHA_017`, `ALPHA_018`, `ALPHA_019`, `ALPHA_020`, `ALPHA_023`, `ALPHA_028`, `ALPHA_033`, `ALPHA_038`, `ALPHA_054`, `ALPHA_101`.
3. Build `EQUAL_WEIGHTED_COMPOSITE` as the equal-weight average of
   cross-sectional z-scores of those 23 alphas.
4. Build `IC_WEIGHTED_COMPOSITE` with the same z-scores and in-sample mean
   monthly Rank IC as static supplied weights.
5. Measure monthly Spearman Rank IC versus 21-source-row forward returns that
   start at the lag-1 execution close.
6. Summarize mean IC, ICIR (`mean / sample std`), and the Newey-West t-stat of
   the mean IC.
7. Run the existing long-only equal-weight monthly backtester with
   `5.00` bps slippage and `5` names.
8. Compute the Deflated Sharpe Ratio of daily measured strategy returns with
   `n_trials=25` and the Euler-Mascheroni expected-maximum mix.

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
- VWAP: typical price `(high + low + close) / 3` on companion synthetic bars
- Composite IC weights: in-sample mean monthly Rank IC of the 23 implemented alphas

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
| ALPHA_017 | -0.0478 |
| ALPHA_018 | -0.0324 |
| ALPHA_019 | -0.0974 |
| ALPHA_020 | -0.0315 |
| ALPHA_023 | -0.0152 |
| ALPHA_028 | 0.0097 |
| ALPHA_033 | -0.0308 |
| ALPHA_038 | -0.0174 |
| ALPHA_054 | 0.0048 |
| ALPHA_101 | 0.0181 |

These weights are in-sample diagnostics. They are not an out-of-sample
combination rule.

## Factor diagnostics

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown | average turnover | slippage cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | -0.0083 | -0.0541 | -0.3019 | 0.0280 | -0.40% | 0.0505 | -23.34% | 0.0724 | 0.0264 |
| ALPHA_002 | -0.0028 | -0.0189 | -0.1163 | 0.0036 | -15.29% | -0.4035 | -27.88% | 0.0838 | 0.0306 |
| ALPHA_003 | -0.0383 | -0.2358 | -1.1060 | 0.2630 | 31.28% | 0.8040 | -16.56% | 0.0832 | 0.0304 |
| ALPHA_004 | -0.0181 | -0.1301 | -1.0225 | 0.0650 | 8.41% | 0.2839 | -23.66% | 0.0871 | 0.0318 |
| ALPHA_005 | -0.0254 | -0.1645 | -0.8436 | 0.1092 | 15.55% | 0.4512 | -23.13% | 0.0781 | 0.0285 |
| ALPHA_006 | -0.0036 | -0.0292 | -0.1833 | 0.0420 | 3.59% | 0.1589 | -14.41% | 0.0826 | 0.0302 |
| ALPHA_007 | 0.0106 | 0.0984 | 0.5324 | 0.0028 | -17.35% | -0.4558 | -25.97% | 0.0799 | 0.0292 |
| ALPHA_008 | -0.0291 | -0.2172 | -1.3083 | 0.0666 | 8.87% | 0.2920 | -23.31% | 0.0804 | 0.0294 |
| ALPHA_009 | -0.0194 | -0.1182 | -0.7920 | 0.0998 | 13.74% | 0.4208 | -24.30% | 0.0804 | 0.0294 |
| ALPHA_010 | -0.0182 | -0.1064 | -0.7266 | 0.1457 | 19.43% | 0.5551 | -23.54% | 0.0815 | 0.0298 |
| ALPHA_012 | -0.0069 | -0.0548 | -0.3888 | 0.1622 | 21.76% | 0.5961 | -18.88% | 0.0821 | 0.0300 |
| ALPHA_013 | 0.0345 | 0.2377 | 1.6730 | 0.0428 | 3.69% | 0.1639 | -24.01% | 0.0814 | 0.0298 |
| ALPHA_014 | -0.0063 | -0.0432 | -0.2736 | 0.0240 | -2.02% | 0.0119 | -23.78% | 0.0832 | 0.0304 |
| ALPHA_017 | -0.0478 | -0.4175 | -2.9894 | 0.3084 | 34.36% | 0.8826 | -14.41% | 0.0839 | 0.0307 |
| ALPHA_018 | -0.0324 | -0.2301 | -2.2995 | 0.0232 | -2.16% | 0.0032 | -20.67% | 0.0859 | 0.0314 |
| ALPHA_019 | -0.0974 | -0.6117 | -2.9056 | 0.0105 | -6.88% | -0.1828 | -14.82% | 0.0414 | 0.0151 |
| ALPHA_020 | -0.0315 | -0.2621 | -1.6914 | 0.0809 | 11.10% | 0.3520 | -20.93% | 0.0855 | 0.0312 |
| ALPHA_023 | -0.0152 | -0.0973 | -0.6273 | 0.2295 | 28.34% | 0.7390 | -17.50% | 0.0788 | 0.0288 |
| ALPHA_028 | 0.0097 | 0.0693 | 0.3415 | 0.0597 | 7.55% | 0.2593 | -30.66% | 0.0827 | 0.0302 |
| ALPHA_033 | -0.0308 | -0.2051 | -2.0262 | 0.1666 | 22.10% | 0.6057 | -17.06% | 0.0859 | 0.0314 |
| ALPHA_038 | -0.0174 | -0.1119 | -0.7676 | 0.0429 | 3.77% | 0.1647 | -20.58% | 0.0838 | 0.0307 |
| ALPHA_054 | 0.0048 | 0.0346 | 0.3353 | 0.0359 | 1.93% | 0.1156 | -25.60% | 0.0860 | 0.0314 |
| ALPHA_101 | 0.0181 | 0.1150 | 1.0473 | 0.0303 | 0.28% | 0.0709 | -29.74% | 0.0816 | 0.0298 |
| EQUAL_WEIGHTED_COMPOSITE | -0.0456 | -0.3165 | -2.4460 | 0.0059 | -12.20% | -0.3078 | -29.44% | 0.0881 | 0.0321 |
| IC_WEIGHTED_COMPOSITE | 0.0670 | 0.4900 | 2.8880 | 0.0387 | 2.70% | 0.1364 | -26.49% | 0.0803 | 0.0294 |

IC is monthly Spearman Rank IC. ICIR is not annualized. DSR is computed on
non-annualized daily measured returns using the Bailey-Lopez de Prado formula
with the Euler-Mascheroni mix. All 23 alphas and both composites are
reported; weak or negative diagnostics are retained.

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
