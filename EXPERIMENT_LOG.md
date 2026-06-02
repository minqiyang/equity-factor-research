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

## Local CSV Experiment Records

Any future run that uses user-provided local CSV data must add or prepare a full
entry in this file before results are interpreted. The entry is required for
loader smoke tests, feature audits, backtest diagnostics, parameter studies, and
full experiment candidates.

This requirement does not authorize data downloads, remote data access, vendor
APIs, credentials, live trading, brokerage integration, order execution, or
profitability claims. Local CSV runs remain research-only and must pass the
real-data readiness audit before being treated as evidence.

At minimum, a local CSV experiment record must include:

- Local source path for each input file, plus file timestamp, file hash, or
  version identifier when the file may be revised.
- Schema for each file: wide price, long price, benchmark, universe membership,
  factor panel, metadata, or another reviewed schema.
- Validation summary: date parsing, sorted dates, duplicate checks, numeric
  parsing, missing-value counts, non-positive price handling, and whether any
  forward-fill or backward-fill was used.
- Data provenance: source name as provided by the user, export type, known
  manual edits, and known missing, stale, revised, or excluded observations.
- Price adjustment policy: adjusted close, raw close, split-adjusted,
  dividend-adjusted, total-return adjusted, or unknown, including benchmark
  adjustment compatibility.
- Universe rules: starting universe, point-in-time membership status, liquidity
  filters, price filters, minimum history, exclusions, delistings, symbol
  changes, and survivorship-bias caveats.
- Feature and signal timing: formulas, lookbacks, skipped windows, latest data
  timestamp available for each signal date, signal lag, and execution timing.
- Sample splits and parameter policy: in-sample, validation, test or holdout
  periods, warm-up exclusion, fixed parameters or grid, and whether choices were
  made before seeing results.
- Benchmark: symbol or local benchmark file, date range, price or return field,
  missing dates, adjustment convention, and alignment to strategy dates.
- Costs, slippage, turnover, rebalance frequency, and execution assumptions,
  including whether zero-cost or zero-slippage settings are diagnostic only.
- Metrics and limitations, including missing-data limitations, benchmark
  mismatch, corporate-action uncertainty, vendor differences, stale prices,
  delisting risk, and any unresolved low issues from the readiness audit.
- Failure modes and next action, including weak, failed, ambiguous, or stopped
  cases. Do not report only the best parameter result.

If required provenance, adjustment policy, date alignment, benchmark coverage,
sample splits, cost/slippage assumptions, or missing-data evidence is absent,
stop before interpreting metrics. Synthetic JSON sidecar logs are not
substitutes for local CSV experiment records.

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
