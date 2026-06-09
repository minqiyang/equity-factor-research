# Synthetic Multi-Factor Parameter Sweep

This report uses synthetic data only. It is not real-market evidence, not financial advice, and not a profitability claim. All parameter cases are shown to avoid cherry-picking.

The sweep does not fetch real data, connect to a broker, place orders, support live trading, or provide order-execution logic.

## Purpose

Run a small deterministic sensitivity check over synthetic combined-score configurations:

1. Keep the same synthetic price and factor generators across every case.
2. Vary only explicit factor weights and selected-asset counts.
3. Run the existing long-only backtester with signal lag, transaction costs, and fixed-bps slippage assumptions.
4. Report every case, including weak or negative diagnostics.

## Fixed Assumptions

| Item | Value |
| --- | --- |
| Factor seed | `20260528` |
| Price seed | `20260529` |
| Asset count | `12` |
| Price rows | `160` |
| Date range | `2024-01-02` plus `160` business rows |
| Factor names | `synthetic_momentum, synthetic_quality, synthetic_reversal` |
| Rebalance frequency | `ME` |
| Transaction cost | `10.00` bps per unit of target-weight turnover |
| Slippage | `0.00` bps per unit of target-weight turnover |
| Zero cost or slippage diagnostic | `True` |
| Signal lag periods | `1` |
| Benchmark | `synthetic equal-weight universe benchmark` |

## Sweep Grid

| Weight set | Weights |
| --- | --- |
| balanced | `synthetic_momentum=0.33, synthetic_quality=0.33, synthetic_reversal=0.33` |
| momentum_tilt | `synthetic_momentum=0.60, synthetic_quality=0.25, synthetic_reversal=0.15` |
| quality_tilt | `synthetic_momentum=0.25, synthetic_quality=0.60, synthetic_reversal=0.15` |
| reversal_tilt | `synthetic_momentum=0.25, synthetic_quality=0.15, synthetic_reversal=0.60` |

Selected-asset counts: `3, 4`

## Sweep Results

These metrics are deterministic diagnostics from synthetic data. They are not evidence of real-world performance or strategy validation.

| Case | Weight set | Top N | Total return | Annualized return | Annualized volatility | Sharpe ratio | Max drawdown | Average turnover | Transaction cost impact | Slippage impact | Total trading impact | Benchmark total return | Excess total return |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| balanced__top_3 | balanced | 3 | 16.65% | 27.65% | 10.26% | 2.4156 | -5.47% | 2.71% | 0.43% | 0.00% | 0.43% | 15.96% | 0.69% |
| balanced__top_4 | balanced | 4 | 21.43% | 36.04% | 9.52% | 3.2638 | -4.27% | 1.56% | 0.25% | 0.00% | 0.25% | 15.96% | 5.47% |
| momentum_tilt__top_3 | momentum_tilt | 3 | 11.37% | 18.62% | 11.95% | 1.4805 | -4.34% | 1.46% | 0.23% | 0.00% | 0.23% | 15.96% | -4.59% |
| momentum_tilt__top_4 | momentum_tilt | 4 | 12.41% | 20.36% | 10.64% | 1.7843 | -4.25% | 2.50% | 0.40% | 0.00% | 0.40% | 15.96% | -3.56% |
| quality_tilt__top_3 | quality_tilt | 3 | 20.42% | 34.24% | 10.07% | 2.9569 | -4.72% | 0.62% | 0.10% | 0.00% | 0.10% | 15.96% | 4.45% |
| quality_tilt__top_4 | quality_tilt | 4 | 20.90% | 35.10% | 9.68% | 3.1376 | -4.27% | 1.25% | 0.20% | 0.00% | 0.20% | 15.96% | 4.94% |
| reversal_tilt__top_3 | reversal_tilt | 3 | 15.81% | 26.19% | 10.21% | 2.3168 | -6.95% | 2.71% | 0.43% | 0.00% | 0.43% | 15.96% | -0.15% |
| reversal_tilt__top_4 | reversal_tilt | 4 | 21.43% | 36.04% | 9.52% | 3.2638 | -4.27% | 1.56% | 0.25% | 0.00% | 0.25% | 15.96% | 5.47% |

## Limitations

- Synthetic prices and factors are not calibrated to actual equities.
- This is a parameter sensitivity smoke test, not model selection.
- The report does not identify a best parameter set or recommend a strategy.
- There is no real data source, universe construction, liquidity model, market-impact model, or validation split.
- The zero-slippage setting is a diagnostic simplification, not an execution-realism claim.
- Results should not be used as investment evidence or a strategy-quality claim.
