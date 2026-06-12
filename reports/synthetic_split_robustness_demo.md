# Synthetic Split-Aware Robustness Demo

This report uses deterministic synthetic panels only. It is not real-market evidence, not financial advice, and not a profitability claim. It does not fetch real data, run a backtest, construct a portfolio, connect to a broker, place orders, or support live trading.

## Purpose

Report every configured synthetic signal case across chronological train, validation, and test windows. The table includes favorable, unfavorable, and invalid diagnostics so the demo cannot hide weak or undefined cases.

## Input Artifacts

| Item | Value |
| --- | --- |
| Data scope | `synthetic only` |
| Source artifacts | `research/synthetic_split_robustness_demo.py` |
| Synthetic seed | `deterministic formula; no random seed` |
| Target return definition | `synthetic forward-return evaluation target` |
| Signal lag | `not applicable; deterministic aligned diagnostic inputs` |

## Split Windows

| split | start | end | date_count |
| --- | ---: | ---: | ---: |
| train | 2024-01-02 | 2024-01-05 | 4 |
| validation | 2024-01-08 | 2024-01-11 | 4 |
| test | 2024-01-12 | 2024-01-17 | 4 |

## Parameter Grid

| case_id | transform |
| --- | ---: |
| base_signal | identity |
| inverse_signal | inverse |
| constant_signal | constant |

## All-Case Split Summary

| case_id | split | split_start | split_end | date_count | asset_count | factor_valid_observations | forward_return_valid_observations | ic_valid_dates | rank_ic_valid_dates | mean_ic | mean_rank_ic | invalid_reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| base_signal | train | 2024-01-02 | 2024-01-05 | 4 | 6 | 24 | 24 | 4 | 4 | 1.0000 | 1.0000 |  |
| base_signal | validation | 2024-01-08 | 2024-01-11 | 4 | 6 | 23 | 23 | 4 | 4 | -1.0000 | -1.0000 |  |
| base_signal | test | 2024-01-12 | 2024-01-17 | 4 | 6 | 24 | 23 | 4 | 4 | 1.0000 | 1.0000 |  |
| inverse_signal | train | 2024-01-02 | 2024-01-05 | 4 | 6 | 24 | 24 | 4 | 4 | -1.0000 | -1.0000 |  |
| inverse_signal | validation | 2024-01-08 | 2024-01-11 | 4 | 6 | 23 | 23 | 4 | 4 | 1.0000 | 1.0000 |  |
| inverse_signal | test | 2024-01-12 | 2024-01-17 | 4 | 6 | 24 | 23 | 4 | 4 | -1.0000 | -1.0000 |  |
| constant_signal | train | 2024-01-02 | 2024-01-05 | 4 | 6 | 24 | 24 | 0 | 0 | NaN | NaN | no_valid_ic_or_rank_ic_dates |
| constant_signal | validation | 2024-01-08 | 2024-01-11 | 4 | 6 | 23 | 23 | 0 | 0 | NaN | NaN | no_valid_ic_or_rank_ic_dates |
| constant_signal | test | 2024-01-12 | 2024-01-17 | 4 | 6 | 24 | 23 | 0 | 0 | NaN | NaN | no_valid_ic_or_rank_ic_dates |

## Invalid Or Insufficient Cases

| case_id | split | invalid_reason | ic_valid_dates | rank_ic_valid_dates |
| --- | --- | ---: | ---: | ---: |
| constant_signal | train | no_valid_ic_or_rank_ic_dates | 0 | 0 |
| constant_signal | validation | no_valid_ic_or_rank_ic_dates | 0 | 0 |
| constant_signal | test | no_valid_ic_or_rank_ic_dates | 0 | 0 |

## Benchmark, Cost, And Slippage Assumptions

| Assumption | Value |
| --- | --- |
| Benchmark | `not included` |
| Rebalance frequency | `not included` |
| Execution timing | `not included` |
| Transaction cost bps | `0.0` |
| Fixed slippage bps | `0.0` |
| Volume-aware slippage mode | `absent` |
| Portfolio construction | `not included` |
| Backtest integration | `not included` |

## Guardrails

- Synthetic data only.
- Diagnostics only.
- No real data fetching.
- No vendor APIs or credentials.
- No live trading, paper trading, brokerage integration, or order execution.
- No profitability, model-selection, or parameter-selection claim.
- Every configured case is reported.

## Next Step

Only refresh committed generated artifacts in a separate explicitly scoped PR after this report/log support is reviewed.
