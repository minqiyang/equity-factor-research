# Local CSV Study Checklist

Date: 2026-06-08

This is a documentation-only checklist for a future user-provided local CSV
research run. It is meant to be completed before any user file is loaded,
validated, diagnosed, or interpreted.

It does not load files, fetch data, download data, call vendor APIs, add
credentials, add live trading, add paper trading, connect to a broker, place
orders, run a backtest, generate a real-data report, or claim profitability.

## 1. Use

Copy this checklist into a future issue, PR description, research note, or
experiment draft before a local CSV run starts. Keep incomplete answers visible.
If a required answer is unknown, stop before interpreting results.

This checklist complements:

- `docs/user_provided_local_csv_research_plan.md`
- `docs/real_data_readiness_audit.md`
- `EXPERIMENT_LOG.md`

It does not replace the real-data readiness audit or the experiment log.

## 2. Scope Statement

Complete this block first.

```text
Run label:

Run type:
  [ ] loader smoke test
  [ ] feature audit
  [ ] diagnostic-only backtest
  [ ] full experiment candidate

Intended interpretation level:
  [ ] ingestion-only
  [ ] feature-calculation-only
  [ ] diagnostic-only simulated workflow
  [ ] reviewable research candidate after audit

What question is this run allowed to answer?

What question is this run not allowed to answer?

Stop if this run needs downloads, vendor APIs, credentials, live trading,
paper trading, brokerage integration, order execution, or profitability
language.
```

## 3. File Inventory

Do not include secrets, account identifiers, API keys, credential paths, or
private account metadata in the repository.

| Input | Local path or placeholder | Source name supplied by user | Timestamp/version | Hash needed? | Notes |
| --- | --- | --- | --- | --- | --- |
| Adjusted close prices |  |  |  |  |  |
| OHLCV prices and volume |  |  |  |  |  |
| Benchmark |  |  |  |  |  |
| Universe membership |  |  |  |  |  |
| Optional factor panel |  |  |  |  |  |
| Metadata sidecar |  |  |  |  |  |

Stop if a mutable file has no timestamp, version identifier, or hash plan.

## 4. Schema Map

| Input | Selected schema | Required columns present? | Duplicate-date policy | Duplicate date-symbol policy | Status |
| --- | --- | --- | --- | --- | --- |
| Prices | wide price / long price / other |  |  |  |  |
| OHLCV | OHLCV long / other |  |  |  |  |
| Benchmark | benchmark price / benchmark return / other |  |  |  |  |
| Universe | membership / eligibility / other |  |  |  |  |
| Factor panel | wide factor / long factor / other |  |  |  |  |

Stop if the schema must be guessed.

## 5. Provenance And Adjustment Policy

```text
Asset price convention:
  [ ] adjusted close
  [ ] raw close
  [ ] split-adjusted
  [ ] dividend-adjusted
  [ ] total-return adjusted
  [ ] unknown

OHLC convention:

Volume convention:
  [ ] raw share volume
  [ ] adjusted volume
  [ ] unknown

Benchmark convention:

Corporate-action handling:

Delisting, merger, stale-row, and symbol-change handling:

Known manual edits:

Known excluded rows or symbols:
```

Stop if the adjustment policy is unknown for any return, feature, benchmark, or
backtest-like interpretation.

## 6. Validation Evidence

Record validation outcomes. Do not repair failures silently.

| Check | Evidence | Issue level | Decision |
| --- | --- | --- | --- |
| Dates parse consistently |  | high / medium / low / none |  |
| Dates are sorted after validation |  | high / medium / low / none |  |
| Duplicate dates absent or rejected |  | high / medium / low / none |  |
| Duplicate `(date, symbol)` rows absent or rejected |  | high / medium / low / none |  |
| Numeric fields reject blanks and missing sentinels before conversion |  | high / medium / low / none |  |
| Missing values counted by file, field, date, and symbol where possible |  | high / medium / low / none |  |
| Non-positive prices absent or rejected |  | high / medium / low / none |  |
| Negative volume absent or rejected |  | high / medium / low / none |  |
| Zero volume counted separately from missing volume |  | high / medium / low / none |  |
| OHLC relationships are valid |  | high / medium / low / none |  |
| Benchmark dates align to intended strategy dates |  | high / medium / low / none |  |
| No forward-fill, backward-fill, interpolation, or zero default was used |  | high / medium / low / none |  |

Stop if any high or medium validation issue remains unresolved.

## 7. Universe And Benchmark

```text
Starting universe:

Universe membership source:

Point-in-time membership status:
  [ ] point-in-time
  [ ] static current list
  [ ] unknown

Liquidity rule:

Minimum history rule:

Price filter:

Exclusions:

Survivorship-bias statement:

Benchmark identity:

Why this benchmark matches the intended universe:

Benchmark missing-date policy:
```

Stop if universe membership is not date-aware and survivorship bias is not
documented.

## 8. Feature, Signal, And Timing

Keep feature dates, universe dates, rebalance dates, execution dates, and return
measurement dates separate.

| Item | Required answer |
| --- | --- |
| Feature formulas |  |
| Input fields |  |
| Lookback windows |  |
| Skipped windows |  |
| Latest data timestamp available for each signal date |  |
| Signal lag before portfolio formation |  |
| Rebalance timing |  |
| Execution timing assumption |  |
| Return measurement window |  |
| Off-by-one checks planned |  |

Stop if same-period target returns, future universe membership, future prices,
or future benchmark values could enter a feature.

## 9. Sample Split And Parameter Policy

```text
Warm-up exclusion:

In-sample period:

Validation period:

Test or holdout period:

Fixed parameters:

Parameter grid, if any:

When parameters were chosen:

How weak, failed, ambiguous, or stopped cases will be recorded:
```

Stop if parameter choices are compared before sample splits and parameter
policy are recorded.

## 10. Costs, Slippage, And Execution Assumptions

Required for any backtest-like diagnostic.

| Assumption | Value | Diagnostic-only caveat |
| --- | --- | --- |
| Transaction cost model |  |  |
| Slippage model |  |  |
| Turnover model |  |  |
| Rebalance frequency |  |  |
| Execution timing |  |  |
| Benchmark comparison |  |  |
| Zero-cost or zero-slippage use |  |  |

Stop if zero-cost or no-slippage output would be presented as realistic
execution evidence.

## 11. Readiness Audit Summary

```text
Real-data readiness audit completed:
  [ ] yes
  [ ] no

High issues:

Medium issues:

Low issues:

Low issues accepted as limitations:

Stop conditions triggered:

Decision:
  [ ] stop before loading files
  [ ] load only for schema smoke test
  [ ] run feature audit only
  [ ] run diagnostic-only workflow
  [ ] prepare full experiment candidate after audit
```

Stop if any unresolved high or medium issue remains.

## 12. Experiment Log Preparation

Before any real-data output is committed or interpreted, prepare an
`EXPERIMENT_LOG.md` entry with:

- experiment ID and date.
- data source and local file references.
- universe and survivorship-bias caveats.
- date range and sample splits.
- feature formulas, lookbacks, lags, and timing assumptions.
- parameters and parameter-selection policy.
- benchmark.
- transaction costs and slippage.
- rebalance and execution timing.
- metrics and limitations.
- missing-data summary.
- failure modes and next action.

Synthetic JSON sidecar logs are not substitutes for this record.

## 13. Final Gate

Do not interpret results unless every statement below is true.

- [ ] Local files were supplied by the user and no data was fetched.
- [ ] No vendor API, `requests`, `yfinance`, Alpaca, CCXT, credential, token,
      or `.env` path was used.
- [ ] No live trading, paper trading, brokerage integration, order execution,
      or account access was added.
- [ ] No source data was committed unless it is an approved tiny synthetic or
      public fixture.
- [ ] No missing values were silently coerced, forward-filled, backward-filled,
      interpolated, or replaced with zero.
- [ ] No unresolved high or medium audit issue remains.
- [ ] The output language is caveated as simulated research or diagnostics.
- [ ] The output does not claim profitability, robustness, tradeability,
      deployment readiness, investment advice, or future performance.

If any box cannot be checked, stop before interpretation.
