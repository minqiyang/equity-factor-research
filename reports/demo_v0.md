# Demo v0 Comparison Report

This report is the official Demo v0 synthetic vertical slice. It uses existing 12-1 momentum, frozen `SyntheticDemoConfig` values, and the existing long-only backtester. `python -m research.synthetic_momentum_demo` remains a legacy diagnostic.

This report was generated from synthetic data only. It does not use private data, does not support live trading, and is not a profitability claim.

## Purpose

1. Run one local command: `python -m research.demo_v0`.
2. Generate synthetic prices for `20` assets.
3. Compute existing 12-1 momentum.
4. Form simulated long-only top-`5` equal-weight selection with drift-aware holdings.
5. Compare the strategy with a synthetic equal-weight universe benchmark.
6. Record explicit fixed-bps cost, explicit slippage, the accepted timing contract, risk metrics, and limitations.
7. Persist an All-Attempt start record before computation, then append the success, failure, or catchable interruption outcome. Incomplete attempts remain visible.

## Configuration

- Command: `python -m research.demo_v0`
- Data scope: synthetic only
- Random seed: `20260521`
- Asset count: `20`
- Price rows: `756`
- Unchanging-price segments: `0`
- Assets with unchanging-price segments: `0`
- Max unchanging-price run length: `0`
- Adjacent timestamp pairs with calendar-day span > 1: `151`
- Max adjacent calendar-day span: `3` days
- Source date range: `2021-01-01` to `2023-11-24`
- Evaluation date range: `2021-12-21` to `2023-11-24`
- Momentum lookback periods: `252`
- Momentum skipped recent periods: `21`
- Rebalance frequency: `ME`
- Selected assets per rebalance: `5`
- Timing contract: `after_close_signal_next_observed_close_v1`
- Signal lag: `1` observed source rows (`observed_source_rows_within_bounded_accounting_slice`)
- Turnover model: `target_weight_turnover` under the existing undivided absolute-trade convention (`absolute_target_minus_drifted_pretrade_by_asset`)
- Transaction cost: `10.00` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value
- Slippage: `0.00` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value
- Zero cost or slippage diagnostic: `True`
- Benchmark: synthetic equal-weight universe benchmark
- Holdings model: `drifted_between_rebalances`
- Holdings shape: `504` rows by `20` assets
- Tracking-error contract: `daily_close_to_close_v1`
- Tracking-error return basis: `strategy_net_after_applied_costs_vs_cost_free_benchmark`
- Sharpe convention: `net_after_applied_costs`, risk-free `zero`, `ddof=0`, `252` periods/year, `exclude_initialization_anchor`
- Holding-episode contract: `continuous_positive_weight_v1`
- All-Attempt Case Logging: `reports/demo_v0_attempts.jsonl` (lightweight demo logging; not charter Stage 4 ledger accounting)

## Metrics

| Metric | Value |
| --- | ---: |
| Total return | -7.91% |
| Annualized return | -4.04% |
| Annualized volatility | 12.64% |
| Tracking error vs synthetic benchmark | 7.74% |
| Episode hit rate | 34.48% |
| Average holding-period return | -2.14% |
| Sharpe ratio | -0.2631 |
| Max drawdown | -22.64% |
| Average holding count | 5.0000 |
| Average position concentration HHI | 0.2003 |
| Max position concentration HHI | 0.2017 |
| Average turnover | 2.62% |
| Total turnover | 13.1962 |
| Total transaction cost impact | 1.32% |
| Total slippage cost impact | 0.00% |
| Total trading cost impact | 1.32% |
| Benchmark total return | 9.85% |
| Excess total return vs synthetic benchmark | -17.75% |

## Limitations

- Synthetic prices are workflow fixtures. They are not calibrated to actual equities.
- Zero slippage is labeled diagnostic: `True`.
- Holdings drift with asset returns between scheduled rebalances; turnover is the undivided sum of absolute signed trades against drifted pre-trade weights. Fixed-bps costs are charged on post-return portfolio value and expressed as beginning-period return impacts. This is weight-level accounting, not an order-fill model.
- There is no survivorship-bias, delisting, borrow, tax, liquidity, or market-impact model in this slice.
- Price bars must be complete, finite, and strictly positive. A supplied volume panel must be complete, finite, and strictly positive; zero volume is refused. Silent fill, clip, drop, or repair is not applied.
- Consecutive equal prices stay in the panel. Unchanging-price segment count, assets affected, and max run length are recorded. The backtest uses every supplied bar.
- Held returns use the supplied price series only (`current / previous - 1`). A separate cash-dividend overlay on that series is refused. Event-level dividend and split reconciliation remains later Milestone 3/4 work.
- Signal lag counts observed source rows in the bounded accounting slice. A missing source row remains an omitted observation. These demos keep the supplied observed index. M3-07 calendar-alignment checks refuse invented sessions: panel timestamps absent from the declared source index. Official demos declare the generated price index as source. Adjacent calendar-day spans measure `(next.normalize() - current.normalize()).days` and disclose omitted-observation gaps in wall time. Session and holiday status remains unverified. Every supplied observed bar stays in the panel, including Friday-Monday bars.
- All-Attempt Case Logging records every Demo v0 invocation, including failures and catchable interruptions. A start record is written before computation so incomplete attempts stay visible. This is lightweight demo logging, not charter Stage 4 experiment/trial-ledger accounting.
- Results depend on the frozen synthetic seed and remain workflow diagnostics only.
- No claim of strategy profitability is made.

## Next Action

Use `python -m research.demo_v0` as the official synthetic Demo v0 command. Keep `python -m research.synthetic_momentum_demo` as a legacy diagnostic. Formal promotion, private data, and execution remain outside this slice.
