# Walking Skeleton MVP Diagnostic Evidence

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

1. Load the 50-stock diagnostic cohort fixture and generate synthetic prices.
2. Compute frozen diagnostic factors `MOM_12_1`, `REV_1M`, and `LOW_VOL_3M`.
3. Measure monthly Spearman Rank IC versus 21-source-row forward returns that
   start at the lag-1 execution close.
4. Summarize mean IC, ICIR (`mean / sample std`), and the Newey-West t-stat of
   the mean IC.
5. Run the existing long-only equal-weight monthly backtester with
   `5.00` bps slippage and `5` names.
6. Compute the Deflated Sharpe Ratio of daily measured strategy returns with
   `n_trials=3`.

## Configuration

- Manifest: `tests/fixtures/walking_skeleton/diagnostic_cohort_v1.json`
- Asset count: `50`
- Source date range: `2021-01-04` to `2023-11-27`
- Evaluation date range: `2021-12-22` to `2023-11-27`
- Rebalance frequency: `ME`
- Selected assets per rebalance: `5`
- Signal lag: `1` source row
- Execution timing: `after_close_signal_next_observed_close_v1`
- Transaction cost: `0.00` bps
- Slippage: `5.00` bps
- Zero cost or slippage diagnostic: `True`
- Benchmark: synthetic equal-weight diagnostic-cohort benchmark
- Timing contract: `after_close_signal_next_observed_close_v1`

## Factor diagnostics

| factor | mean IC | ICIR | Newey-West t | DSR | total return | Sharpe | max drawdown | average turnover | slippage cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MOM_12_1 | -0.0145 | -0.0919 | -0.5047 | 0.1532 | -4.61% | -0.1206 | -18.66% | 0.0287 | 0.0072 |
| REV_1M | -0.0202 | -0.1678 | -0.7473 | 0.1644 | -3.66% | -0.0878 | -18.16% | 0.0809 | 0.0203 |
| LOW_VOL_3M | -0.0138 | -0.0984 | -0.5056 | 0.1394 | -5.91% | -0.1632 | -18.18% | 0.0631 | 0.0159 |

IC is monthly Spearman Rank IC. ICIR is not annualized. DSR is computed on
non-annualized daily measured returns. All three factors are reported; weak or
negative diagnostics are retained.

## Limitations

- Synthetic prices only; no vendor, private, or real market data.
- Static 50-name membership is survivorship-biased by construction.
- Close-only lag-1 execution is idealized research accounting, not brokerage.
- 5 bps slippage is a fixed diagnostic assumption, not a market-impact model.
- This does not execute, replace, or reopen the refused 14-trial run.
- This does not grant `RESEARCH_PASS`, formal interpretation, or profitability.
