# Synthetic Multifactor Backtest Comparison Report

This report is the M3-01 exploratory synthetic three-factor backtest. It reuses Demo v0 synthetic price dates and assets, the existing factor generator and `synthetic_momentum=0.50, synthetic_quality=0.30, synthetic_reversal=0.20` weights, existing winsorize/z-score/`combine_factors` helpers, and the existing long-only backtester. `python -m research.demo_v0` remains the official Demo v0 command. `python -m research.synthetic_multifactor_workflow_demo` remains the feature-only workflow.

The three synthetic panels are artificial quality, reversal, and momentum fixtures. They are distinct from Demo v0 12-1 momentum and from fundamentals.

This report was generated from synthetic data only. It does not use private data, does not support live trading, and is not a profitability claim.

## Purpose

1. Run one local command: `python -m research.synthetic_multifactor_backtest_demo`.
2. Generate Demo v0-aligned synthetic prices for `20` assets.
3. Generate three aligned artificial factor panels from the existing factor generator.
4. Winsorize and z-score each panel, then combine with explicit weights through `combine_factors`.
5. Form simulated long-only top-`5` equal-weight selection with drift-aware holdings.
6. Compare the strategy with a synthetic equal-weight universe benchmark.
7. Record explicit fixed-bps cost, explicit slippage, the accepted timing contract, risk metrics, and limitations.
8. Persist an All-Attempt start record before computation, then append the success, failure, or catchable interruption outcome. Incomplete attempts remain visible.

## Configuration

- Command: `python -m research.synthetic_multifactor_backtest_demo`
- Data scope: synthetic only
- Price random seed: `20260521`
- Factor random seed: `20260528`
- Asset count: `20`
- Price rows: `756`
- Source date range: `2021-01-01` to `2023-11-24`
- Evaluation date range: `2021-01-01` to `2023-11-24`
- Factor names: `synthetic_momentum, synthetic_quality, synthetic_reversal`
- Combination weights: `synthetic_momentum=0.50, synthetic_quality=0.30, synthetic_reversal=0.20`
- Winsorization quantiles: `0.05` / `0.95`
- Rebalance frequency: `ME`
- Selected assets per rebalance: `5`
- Timing contract: `after_close_signal_next_observed_close_v1`
- Signal lag periods: `1`
- Turnover model: `target_weight_turnover` under the existing undivided absolute-trade convention (`absolute_target_minus_drifted_pretrade_by_asset`)
- Transaction cost: `10.00` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value
- Slippage: `0.00` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value
- Zero cost or slippage diagnostic: `True`
- Benchmark: synthetic equal-weight universe benchmark
- Holdings model: `drifted_between_rebalances`
- Holdings shape: `756` rows by `20` assets
- Tracking-error contract: `daily_close_to_close_v1`
- Tracking-error return basis: `strategy_net_after_applied_costs_vs_cost_free_benchmark`
- Sharpe convention: `net_after_applied_costs`, risk-free `zero`, `ddof=0`, `252` periods/year, `exclude_initialization_anchor`
- Holding-episode contract: `continuous_positive_weight_v1`
- All-Attempt Case Logging: `reports/synthetic_multifactor_backtest_demo_attempts.jsonl` (lightweight demo logging; not charter Stage 4 ledger accounting)

## Metrics

| Metric | Value |
| --- | ---: |
| Total return | 24.03% |
| Annualized return | 7.45% |
| Annualized volatility | 13.31% |
| Tracking error vs synthetic benchmark | 7.94% |
| Episode hit rate | 57.63% |
| Average holding-period return | 1.09% |
| Sharpe ratio | 0.6065 |
| Max drawdown | -11.78% |
| Average holding count | 5.0000 |
| Average position concentration HHI | 0.2003 |
| Max position concentration HHI | 0.2014 |
| Average turnover | 6.44% |
| Total turnover | 48.6316 |
| Total transaction cost impact | 4.86% |
| Total slippage cost impact | 0.00% |
| Total trading cost impact | 4.86% |
| Benchmark total return | 28.16% |
| Excess total return vs synthetic benchmark | -4.14% |

## Limitations

- Synthetic prices are workflow fixtures. They are not calibrated to actual equities.
- The three synthetic panels are artificial quality, reversal, and momentum fixtures. They are distinct from Demo v0 12-1 momentum and from fundamentals.
- Zero slippage is labeled diagnostic: `True`.
- Holdings drift with asset returns between scheduled rebalances; turnover is the undivided sum of absolute signed trades against drifted pre-trade weights. Fixed-bps costs are charged on post-return portfolio value and expressed as beginning-period return impacts. This is weight-level accounting, not an order-fill model.
- There is no survivorship-bias, delisting, borrow, tax, liquidity, or market-impact model in this slice.
- Price bars must be complete, finite, and strictly positive. A supplied volume panel must be complete, finite, and strictly positive; zero volume is refused. Mismatched price/factor axes and nonfinite factor values are refused. Silent fill, reindex, clip, drop, or repair is not applied.
- All-Attempt Case Logging records every invocation, including failures and catchable interruptions. A start record is written before computation so incomplete attempts stay visible. This is lightweight demo logging, not charter Stage 4 experiment/trial-ledger accounting.
- Results depend on the frozen synthetic seeds and remain workflow diagnostics only.
- No claim of strategy profitability is made.

## Next Action

Use `python -m research.synthetic_multifactor_backtest_demo` as the M3-01 exploratory synthetic three-factor backtest. Keep `python -m research.demo_v0` as the official Demo v0 command. Keep `python -m research.synthetic_multifactor_workflow_demo` as the feature-only workflow. Formal promotion, private data, and execution remain outside this slice.
