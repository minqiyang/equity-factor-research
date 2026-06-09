# Synthetic Experiment Registry

This registry summarizes deterministic JSON logs from synthetic demos only. It is not real-market evidence, not financial advice, and not a profitability claim.

The metrics below are copied from synthetic smoke-test logs when present. They are workflow diagnostics only and should not be interpreted as strategy validation.

## Registry

| experiment_id | title | experiment_type | data_scope | date_start | date_end | universe | benchmark | transaction_cost_model | slippage_model | metrics_available | total_return | annualized_return | max_drawdown | sharpe_ratio | markdown_report | experiment_log | next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| local-csv-fixture-workflow-demo | Local CSV Fixture Workflow Demo | synthetic_local_csv_workflow | synthetic only | 2024-01-02 | 2024-01-05 | 3 synthetic fixture assets | synthetic local CSV benchmark fixture | not applicable; no portfolio or trades | not applicable; no portfolio or trades | false |  |  |  |  | reports/local_csv_fixture_workflow_demo.md | reports/experiment_logs/local_csv_fixture_workflow_demo.json | Use this as a local CSV fixture wiring check only; a real user-provided local CSV study still requires readiness-audit approval, explicit sample splits, universe rules, benchmark selection, costs, slippage assumptions, and full caveats. |
| synthetic-combined-score-backtest-demo | Synthetic Combined-Score Backtest Smoke Test | synthetic_backtest_smoke_test | synthetic only | 2024-01-02 | 2024-08-12 | 12 synthetic assets | synthetic equal-weight universe benchmark | fixed_bps_on_target_weight_turnover; 10.00 bps per unit of target-weight turnover | fixed_bps_on_target_weight_turnover; 0.00 bps per unit of target-weight turnover | true | 0.0860815 | 0.139826 | -0.0513536 | 1.284 | reports/synthetic_combined_score_backtest_demo.md | reports/experiment_logs/synthetic_combined_score_backtest_demo.json | Use as a reproducible synthetic smoke-test log only; real-data readiness still requires explicit data interfaces, validation splits, liquidity assumptions, and slippage modeling. |
| synthetic-momentum-demo | Synthetic Momentum Demo | synthetic_backtest_smoke_test | synthetic only | 2021-01-01 | 2023-11-24 | 20 synthetic assets | synthetic equal-weight universe benchmark | fixed_bps_on_target_weight_turnover; 10.00 bps per unit of target-weight turnover | fixed_bps_on_target_weight_turnover; 0.00 bps per unit of target-weight turnover | true | -0.0794896 | -0.0272669 | -0.225516 | -0.216069 | reports/synthetic_momentum_demo.md | reports/experiment_logs/synthetic_momentum_demo.json | Use as a reproducible smoke-test log only; real-data experiments still require explicit data-source, universe, slippage, benchmark, and validation-split documentation. |
| synthetic-multifactor-parameter-sweep | Synthetic Multi-Factor Parameter Sweep | synthetic_parameter_sweep | synthetic only | 2024-01-02 | 2024-08-12 | 12 synthetic assets | synthetic equal-weight universe benchmark | fixed_bps_on_target_weight_turnover; 10.00 bps per unit of target-weight turnover | fixed_bps_on_target_weight_turnover; 0.00 bps per unit of target-weight turnover | false |  |  |  |  | reports/synthetic_multifactor_parameter_sweep.md | reports/experiment_logs/synthetic_multifactor_parameter_sweep.json | Use as a synthetic sensitivity smoke test only; any real-data parameter study requires explicit sample splits, universe rules, slippage assumptions, and full experiment-log entries. |
| synthetic-multifactor-workflow-demo | Synthetic Multi-Factor Workflow Demo | synthetic_feature_workflow | synthetic only | 2024-01-02 | 2024-04-22 | 12 synthetic assets | not applicable | not applicable; no portfolio or trades | not applicable; no portfolio or trades | false |  |  |  |  | reports/synthetic_multifactor_workflow_demo.md | reports/experiment_logs/synthetic_multifactor_workflow_demo.json | Use as a synthetic feature-workflow audit log only; backtest integration and real-data validation remain separate stages. |

## Caveats

- The registry reads existing JSON logs; it does not run experiments or recalculate metrics.
- No real data is fetched.
- No live trading, brokerage integration, order execution, or credential handling is introduced.
- Missing metric cells mean the source log did not contain that metric, not that the value is zero.
- Full experiment records are still required before any real-data validation or parameter study.
