# Synthetic Momentum Demo

This report was generated from synthetic data only. It does not use real market data, does not support live trading, and is not evidence of real-world strategy profitability.

## Purpose

Demonstrate the local research workflow:

1. Generate synthetic prices for 20 assets.
2. Compute 12-1 month momentum.
3. Run a long-only, top-ranked, equal-weight backtest.
4. Include fixed transaction costs.
5. Record basic metrics and limitations.

## Configuration

- Random seed: `20260521`
- Asset count: `20`
- Price rows: `756`
- Date range: `2021-01-01` to `2023-11-24`
- Momentum lookback periods: `252`
- Momentum skipped recent periods: `21`
- Rebalance frequency: `ME`
- Selected assets per rebalance: `5`
- Transaction cost: `10.00` bps per unit of target-weight turnover
- Benchmark: synthetic equal-weight universe benchmark
- Execution timing: signals known after close; trades on rebalance dates using lagged signals; holdings affect next price row

## Metrics

| Metric | Value |
| --- | ---: |
| Total return | -7.95% |
| Annualized return | -2.73% |
| Annualized volatility | 10.32% |
| Sharpe ratio | -0.2161 |
| Max drawdown | -22.55% |
| Average turnover | 1.67% |
| Total turnover | 12.6000 |
| Total transaction cost impact | 1.26% |
| Benchmark total return | 28.16% |
| Excess total return vs synthetic benchmark | -36.11% |

## Limitations

- Synthetic prices are not calibrated to actual equities.
- There is no survivorship-bias, delisting, borrow, tax, liquidity, or market-impact model.
- The backtester uses simplified target-weight turnover, not drift-adjusted trade accounting.
- Results depend on the synthetic random seed and are workflow diagnostics only.
- No claim of strategy profitability is made.

## Next Action

Use this demo as a smoke test for the research pipeline. Before using real data,
add explicit data-source documentation, universe construction rules, benchmark
selection, and train/validation/test split definitions.
