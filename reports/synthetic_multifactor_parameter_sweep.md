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
| Transaction cost | `10.00` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value |
| Slippage | `0.00` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value |
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
| balanced__top_3 | balanced | 3 | 16.59% | 27.53% | 10.26% | 2.4084 | -5.51% | 2.82% | 0.45% | 0.00% | 0.45% | 15.96% | 0.62% |
| balanced__top_4 | balanced | 4 | 21.33% | 35.86% | 9.52% | 3.2501 | -4.31% | 1.68% | 0.27% | 0.00% | 0.27% | 15.96% | 5.37% |
| momentum_tilt__top_3 | momentum_tilt | 3 | 11.26% | 18.43% | 11.95% | 1.4661 | -4.35% | 1.57% | 0.25% | 0.00% | 0.25% | 15.96% | -4.70% |
| momentum_tilt__top_4 | momentum_tilt | 4 | 12.37% | 20.30% | 10.67% | 1.7743 | -4.32% | 2.58% | 0.41% | 0.00% | 0.41% | 15.96% | -3.60% |
| quality_tilt__top_3 | quality_tilt | 3 | 20.30% | 34.03% | 10.06% | 2.9448 | -4.79% | 0.74% | 0.12% | 0.00% | 0.12% | 15.96% | 4.34% |
| quality_tilt__top_4 | quality_tilt | 4 | 20.80% | 34.91% | 9.68% | 3.1252 | -4.31% | 1.38% | 0.22% | 0.00% | 0.22% | 15.96% | 4.84% |
| reversal_tilt__top_3 | reversal_tilt | 3 | 15.67% | 25.95% | 10.20% | 2.2995 | -7.03% | 2.79% | 0.45% | 0.00% | 0.45% | 15.96% | -0.29% |
| reversal_tilt__top_4 | reversal_tilt | 4 | 21.33% | 35.86% | 9.52% | 3.2501 | -4.31% | 1.68% | 0.27% | 0.00% | 0.27% | 15.96% | 5.37% |

## Limitations

- Synthetic prices and factors are not calibrated to actual equities.
- This is a parameter sensitivity smoke test, not model selection.
- The report does not identify a best parameter set or recommend a strategy.
- There is no real data source, universe construction, liquidity model, market-impact model, or validation split.
- The zero-slippage setting is a diagnostic simplification, not an execution-realism claim.
- Results should not be used as investment evidence or a strategy-quality claim.
