# WorldQuant Alphas Batch 2 Multifactor Diagnostic MVP Evidence

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
2. Compute classical price-volume alphas `ALPHA_005`, `ALPHA_008`,
   `ALPHA_010`, `ALPHA_013`, `ALPHA_014`, `ALPHA_018`, and `ALPHA_020`.
3. Build `EQUAL_WEIGHTED_COMPOSITE` as the equal-weight average of
   cross-sectional z-scores of those seven alphas.
4. Build `IC_WEIGHTED_COMPOSITE` with the same z-scores and in-sample mean
   monthly Rank IC as static supplied weights.
5. Measure monthly Spearman Rank IC versus 21-source-row forward returns that
   start at the lag-1 execution close.
6. Summarize mean IC, ICIR (`mean / sample std`), and the Newey-West t-stat of
   the mean IC.
7. Run the existing long-only equal-weight monthly backtester with
   `5.00` bps slippage and `5` names.
8. Compute the Deflated Sharpe Ratio of daily measured strategy returns with
   `n_trials=9` and the Euler-Mascheroni expected-maximum mix.

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
- Composite IC weights: in-sample mean monthly Rank IC of the seven batch-2 alphas

## In-sample IC weights

| factor | mean monthly Rank IC |
| --- | --- |
| ALPHA_005 | -0.0254 |
| ALPHA_008 | -0.0291 |
| ALPHA_010 | -0.0182 |
| ALPHA_013 | 0.0345 |
| ALPHA_014 | -0.0063 |
| ALPHA_018 | -0.0324 |
| ALPHA_020 | -0.0315 |

These weights are in-sample diagnostics. They are not an out-of-sample
combination rule.

## Factor diagnostics

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown | average turnover | slippage cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_005 | -0.0254 | -0.1645 | -0.8436 | 0.2252 | 15.55% | 0.4512 | -23.13% | 0.0781 | 0.0285 |
| ALPHA_008 | -0.0291 | -0.2172 | -1.3083 | 0.1527 | 8.87% | 0.2920 | -23.31% | 0.0804 | 0.0294 |
| ALPHA_010 | -0.0182 | -0.1064 | -0.7266 | 0.2813 | 19.43% | 0.5551 | -23.54% | 0.0815 | 0.0298 |
| ALPHA_013 | 0.0345 | 0.2377 | 1.6730 | 0.1071 | 3.69% | 0.1639 | -24.01% | 0.0814 | 0.0298 |
| ALPHA_014 | -0.0063 | -0.0432 | -0.2736 | 0.0667 | -2.02% | 0.0119 | -23.78% | 0.0832 | 0.0304 |
| ALPHA_018 | -0.0324 | -0.2301 | -2.2995 | 0.0648 | -2.16% | 0.0032 | -20.67% | 0.0859 | 0.0314 |
| ALPHA_020 | -0.0315 | -0.2621 | -1.6914 | 0.1781 | 11.10% | 0.3520 | -20.93% | 0.0855 | 0.0312 |
| EQUAL_WEIGHTED_COMPOSITE | -0.0320 | -0.2186 | -1.5392 | 0.0073 | -19.77% | -0.5429 | -34.25% | 0.0820 | 0.0300 |
| IC_WEIGHTED_COMPOSITE | 0.0420 | 0.2742 | 1.6372 | 0.2277 | 15.84% | 0.4563 | -21.13% | 0.0836 | 0.0306 |

IC is monthly Spearman Rank IC. ICIR is not annualized. DSR is computed on
non-annualized daily measured returns using the Bailey-Lopez de Prado formula
with the Euler-Mascheroni mix. All seven alphas and both composites are
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
