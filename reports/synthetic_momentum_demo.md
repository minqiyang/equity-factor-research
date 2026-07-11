# Synthetic Momentum Demo

This report was generated from synthetic data only. It does not use real market data, does not support live trading, and is not evidence of real-world strategy profitability.

## Purpose

Demonstrate the local research workflow:

1. Generate synthetic prices for 20 assets.
2. Compute 12-1 month momentum.
3. Run a long-only, top-ranked, equal-weight backtest.
4. Include fixed transaction costs.
5. Record explicit fixed-bps slippage assumptions.
6. Record basic metrics and limitations.

## Configuration

- Random seed: `20260521`
- Asset count: `20`
- Price rows: `756`
- Date range: `2021-01-01` to `2023-11-24`
- Momentum lookback periods: `252`
- Momentum skipped recent periods: `21`
- Rebalance frequency: `ME`
- Selected assets per rebalance: `5`
- Transaction cost: `10.00` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value
- Slippage: `0.00` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value
- Zero cost or slippage diagnostic: `True`
- Benchmark: synthetic equal-weight universe benchmark
- Tracking-error contract: `daily_close_to_close_v1`
- Tracking-error return basis: `strategy_net_after_applied_costs_vs_cost_free_benchmark`
- Tracking-error frequency/annualization: `daily_close_to_close`, `252` periods/year, `ddof=0`
- Tracking-error first-row policy: `exclude_synthetic_anchor`
- Tracking-error missing policy: `raise`
- Tracking-error terminal-row policy: `include_terminal_close_to_close_window`
- Benchmark cost basis: `cost_free_price_return`
- Holding-episode contract: `continuous_positive_weight_v1`
- Holding-episode return/cost basis: `net_contribution_over_cumulative_deployed_weight`, `pro_rata_absolute_signed_trade_weight`
- Holding-episode terminal policy: `exclude_open`
- Closed/terminal-open episodes: `29` / `5`
- Execution timing: signals known after close; trades on rebalance dates using lagged signals; holdings affect next price row

## Metrics

| Metric | Value |
| --- | ---: |
| Total return | -7.91% |
| Annualized return | -2.71% |
| Annualized volatility | 10.31% |
| Tracking error vs synthetic benchmark | 9.09% |
| Episode hit rate | 34.48% |
| Average holding-period return | -2.14% |
| Sharpe ratio | -0.2146 |
| Max drawdown | -22.64% |
| Average holding count | 5.0000 |
| Average position concentration HHI | 0.2003 |
| Max position concentration HHI | 0.2017 |
| Average turnover | 1.75% |
| Total turnover | 13.1962 |
| Total transaction cost impact | 1.32% |
| Total slippage cost impact | 0.00% |
| Total trading cost impact | 1.32% |
| Benchmark total return | 28.16% |
| Excess total return vs synthetic benchmark | -36.07% |

## Limitations

- Synthetic prices are not calibrated to actual equities.
- There is no survivorship-bias, delisting, borrow, tax, liquidity, or market-impact model.
- Holdings drift with asset returns between scheduled rebalances; turnover is measured against drifted pre-trade weights. Fixed-bps costs are charged on post-return portfolio value and expressed as beginning-period return impacts. This is still weight-level accounting, not an order-fill model.
- The zero-slippage setting is a diagnostic simplification, not an execution-realism claim.
- Results depend on the synthetic random seed and are workflow diagnostics only.
- No claim of strategy profitability is made.

## Next Action

Use this demo as a smoke test for the research pipeline. Before using real data,
add explicit data-source documentation, universe construction rules, benchmark
selection, and train/validation/test split definitions.
