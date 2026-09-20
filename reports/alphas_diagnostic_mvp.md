# WorldQuant Alphas Diagnostic MVP Evidence

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
   prices plus companion open, low, volume, and close-to-close returns.
2. Compute classical price-volume alphas `ALPHA_001`, `ALPHA_002`,
   `ALPHA_003`, `ALPHA_004`, `ALPHA_006`, and `ALPHA_012`.
3. Measure monthly Spearman Rank IC versus 21-source-row forward returns that
   start at the lag-1 execution close.
4. Summarize mean IC, ICIR (`mean / sample std`), and the Newey-West t-stat of
   the mean IC.
5. Run the existing long-only equal-weight monthly backtester with
   `5.00` bps slippage and `5` names.
6. Compute the Deflated Sharpe Ratio of daily measured strategy returns with
   `n_trials=6` and the Euler-Mascheroni expected-maximum mix.

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

DSR uses across-trial sample variance of non-annualized Sharpes:
`0.000715723872638918`. The raw family count supplies an
independent-trial sensitivity calculation for this diagnostic run.

## Factor diagnostics

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown | average turnover | slippage cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | -0.0083 | -0.0541 | -0.3019 | 0.1968 | -0.40% | 0.0505 | -23.34% | 0.0724 | 0.0264 |
| ALPHA_002 | -0.0028 | -0.0189 | -0.1163 | 0.0519 | -15.29% | -0.4035 | -27.88% | 0.0838 | 0.0306 |
| ALPHA_003 | -0.0383 | -0.2358 | -1.1060 | 0.6651 | 31.28% | 0.8040 | -16.56% | 0.0832 | 0.0304 |
| ALPHA_004 | -0.0181 | -0.1301 | -1.0225 | 0.3240 | 8.41% | 0.2839 | -23.66% | 0.0871 | 0.0318 |
| ALPHA_006 | -0.0036 | -0.0292 | -0.1833 | 0.2519 | 3.59% | 0.1589 | -14.41% | 0.0826 | 0.0302 |
| ALPHA_012 | -0.0069 | -0.0548 | -0.3888 | 0.5295 | 21.76% | 0.5961 | -18.88% | 0.0821 | 0.0300 |

IC is monthly Spearman Rank IC. ICIR is not annualized. DSR is computed on
non-annualized daily measured returns using the Bailey-Lopez de Prado formula
with the Euler-Mascheroni mix. All six factors are reported; weak or
negative diagnostics are retained.

## Limitations

- Synthetic prices only; no vendor, private, or real market data.
- Companion open, low, and volume are additional synthetic draws from
  `seed + 1`; they are not observed market prints.
- Static 50-name membership is survivorship-biased by construction.
- Close-only lag-1 execution is idealized research accounting, not brokerage.
- 5 bps slippage is a fixed diagnostic assumption, not a market-impact model.
- This does not execute, replace, or reopen the refused 14-trial run.
- This does not grant `RESEARCH_PASS`, formal interpretation, or profitability.
