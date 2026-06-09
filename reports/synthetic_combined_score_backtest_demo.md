# Synthetic Combined-Score Backtest Smoke Test

This report uses synthetic data only. It is not real-market evidence, not financial advice, and not a profitability claim. The smoke-test metrics below are synthetic diagnostics only and should not be interpreted as strategy validation.

The demo does not fetch real data, connect to a broker, place orders, support live trading, or provide order-execution logic.

## Purpose

Exercise the integration path from existing factor research helpers into the existing long-only backtester:

1. Generate deterministic synthetic prices and synthetic factor panels.
2. Winsorize factor cross-sections.
3. Normalize factors with z-scores and rank diagnostics.
4. Compute factor correlation diagnostics.
5. Combine z-scored factors with explicit weights.
6. Run the existing long-only backtester as a synthetic smoke test.
7. Record caveated diagnostic metrics and limitations.

## Configuration

| Item | Value |
| --- | --- |
| Factor seed | `20260528` |
| Price seed | `20260529` |
| Asset count | `12` |
| Price rows | `160` |
| Date range | `2024-01-02` to `2024-08-12` |
| Factor names | `synthetic_momentum, synthetic_quality, synthetic_reversal` |
| Combination weights | `synthetic_momentum=0.50, synthetic_quality=0.30, synthetic_reversal=0.20` |
| Rebalance frequency | `ME` |
| Selected assets per rebalance | `4` |
| Transaction cost | `10.00` bps per unit of target-weight turnover |
| Slippage | `0.00` bps per unit of target-weight turnover |
| Zero cost or slippage diagnostic | `True` |
| Signal lag periods | `1` |
| Benchmark | `synthetic equal-weight universe benchmark` |

## Factor Correlation Diagnostics

The matrix below is computed from flattened z-scored synthetic factor panels.

| Factor | synthetic_momentum | synthetic_quality | synthetic_reversal |
| --- | ---: | ---: | ---: |
| synthetic_momentum | 1.0000 | -0.9841 | -0.9766 |
| synthetic_quality | -0.9841 | 1.0000 | 0.9769 |
| synthetic_reversal | -0.9766 | 0.9769 | 1.0000 |

## Smoke-Test Metrics

These values are deterministic diagnostics from synthetic data. They are not evidence of real-world performance.

| Metric | Value |
| --- | ---: |
| Total return | `8.61%` |
| Annualized return | `13.98%` |
| Annualized volatility | `10.57%` |
| Sharpe ratio | `1.2840` |
| Max drawdown | `-5.14%` |
| Average turnover | `5.31%` |
| Total turnover | `8.5000` |
| Total transaction cost impact | `0.85%` |
| Total slippage cost impact | `0.00%` |
| Total trading cost impact | `0.85%` |
| Benchmark total return | `15.96%` |
| Excess total return vs synthetic benchmark | `-7.35%` |

## Limitations

- Synthetic prices and factors are not calibrated to actual equities.
- The combined score is a synthetic research feature, not a production signal.
- The backtest is a smoke test of workflow wiring only.
- There is no real data source, universe construction, liquidity model, market-impact model, or validation split.
- The existing backtester uses simplified target-weight turnover.
- The zero-slippage setting is a diagnostic simplification, not an execution-realism claim.
- Results should not be used as investment evidence or a strategy-quality claim.
