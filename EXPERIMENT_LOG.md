# Experiment Log

Use this file to record every meaningful experiment, including failed or inconclusive runs. Do not delete weak results to make the project look better.

## Automated Synthetic Demo Logs

Synthetic demo scripts also write deterministic JSON sidecar logs under
`reports/experiment_logs/`. These logs capture configuration, synthetic-only
data assumptions, caveats, outputs, and diagnostics from reproducible smoke
demos.

They are not substitutes for full experiment records when real data, real
universe definitions, validation splits, or parameter studies are introduced.
Synthetic demo metrics remain workflow diagnostics only and are not financial
advice, strategy validation, or profitability evidence.

`reports/experiment_registry.md` summarizes the JSON logs in a deterministic
table for review. The registry is a reporting view over existing logs; it does
not run experiments, recalculate metrics, or replace full experiment records.

`reports/synthetic_multifactor_parameter_sweep.md` is a synthetic-only
parameter sensitivity smoke test. It reports every configured case and should
not be used as parameter selection, strategy validation, financial advice, or
profitability evidence.

## Template

### Experiment ID

`YYYYMMDD-NNN-short-name`

### Date

`YYYY-MM-DD`

### Hypothesis

What should be true if this experiment is useful?

### Data Source

Dataset name, vendor, file path, version, and any known limitations.

### Universe

Universe definition, liquidity screen, exclusions, and survivorship-bias notes.

### Date Range

Start date, end date, and any excluded dates.

### Features / Factors

Feature names, formulas, lookback windows, lags, and data availability assumptions.

### Parameters

All strategy, backtest, ranking, selection, and risk-control parameters.

### Benchmark

Benchmark symbol or dataset and benchmark return calculation assumptions.

### Transaction Costs

Cost model, basis points, minimum commissions, and any simplifications.

### Slippage Model

Slippage model, basis points or volume-aware rule, and limitations.

### Rebalance Frequency

Daily, weekly, monthly, or custom schedule. State exact execution timing.

### Performance Metrics

Total return, annualized return, annualized volatility, Sharpe ratio, benchmark-relative return, or other relevant metrics.

### Turnover

Average turnover, rebalance turnover distribution, and cost impact.

### Max Drawdown

Maximum drawdown, drawdown dates, and comparison with benchmark drawdown.

### Sample Split

In-sample, validation, and test period definitions.

### Result Summary

Concise summary of what happened. Include weak, failed, or ambiguous results.

### Failure Modes

Known problems, possible leakage risks, sensitivity issues, data quality concerns, overfitting risks, or execution assumptions that may be unrealistic.

### Next Action

Keep, reject, revise, test further, add data, improve validation, or stop.
