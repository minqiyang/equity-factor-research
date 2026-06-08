# Local CSV Readiness Audit Report Template

Date: 2026-06-08

This is a documentation-only report format for a future user-provided local CSV
readiness audit. It is meant to be filled manually before any local CSV result
is interpreted as research evidence.

It does not load files, fetch data, download data, call vendor APIs, add
credentials, add live trading, add paper trading, connect to a broker, place
orders, run a backtest, generate a real-data report, or claim profitability.

Passing this report does not validate a strategy. It only records whether the
local files, schema choices, validation evidence, timing assumptions, and
interpretation boundary are documented enough for a reviewable next step.

## 1. Use

Copy this report format into a future issue, PR description, research note, or
experiment draft after the local CSV study checklist has been completed and
before any result is interpreted.

This report complements:

- `docs/user_provided_local_csv_research_plan.md`
- `docs/local_csv_study_checklist.md`
- `docs/real_data_readiness_audit.md`
- `EXPERIMENT_LOG.md`

It does not replace the study checklist or the experiment log. Unknown answers
must remain visible. Do not commit private source files, credential-like paths,
account identifiers, API keys, tokens, or private account metadata.

## 2. Audit Identity

```text
Audit ID:
Audit date:
Reviewer:
Run label:
Related branch or PR:
Related checklist:
Related experiment-log entry:

Run type:
  [ ] loader smoke test
  [ ] feature audit
  [ ] diagnostic-only backtest
  [ ] full experiment candidate

Allowed interpretation level:
  [ ] ingestion-only
  [ ] feature-calculation-only
  [ ] diagnostic-only simulated workflow
  [ ] reviewable research candidate after audit
  [ ] stop before interpretation
```

## 3. Input Inventory Reviewed

Record only the minimum review metadata needed for auditability. Redact local
paths if they reveal private directory structure or account information.

| Input | Present? | Schema | Source supplied by user | Timestamp/version | Hash or hash plan | Path redacted? | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Adjusted close prices |  |  |  |  |  |  |  |
| OHLCV prices and volume |  |  |  |  |  |  |  |
| Benchmark |  |  |  |  |  |  |  |
| Universe membership |  |  |  |  |  |  |  |
| Optional factor panel |  |  |  |  |  |  |  |
| Metadata sidecar |  |  |  |  |  |  |  |

Stop interpretation if provenance, timestamp or version evidence, source name,
or revision history is missing for a mutable file.

## 4. Schema And Loader Validation Evidence

This section records validation evidence. It is not a place to repair data
silently.

| Check | Evidence reviewed | Issue level | Decision |
| --- | --- | --- | --- |
| Required columns match selected schema |  | high / medium / low / none |  |
| Dates parse consistently |  | high / medium / low / none |  |
| Dates are sorted after validation |  | high / medium / low / none |  |
| Duplicate dates are absent or rejected |  | high / medium / low / none |  |
| Duplicate `(date, symbol)` rows are absent or rejected |  | high / medium / low / none |  |
| Numeric fields reject blanks and missing sentinels before conversion |  | high / medium / low / none |  |
| Missing values are counted by file, field, date, and symbol where possible |  | high / medium / low / none |  |
| Non-positive prices are absent or separately justified |  | high / medium / low / none |  |
| Negative volume is absent or rejected |  | high / medium / low / none |  |
| Zero volume is counted separately from missing volume |  | high / medium / low / none |  |
| OHLC relationships are valid |  | high / medium / low / none |  |
| Benchmark dates align to intended strategy dates |  | high / medium / low / none |  |
| No forward-fill, backward-fill, interpolation, or zero default was used |  | high / medium / low / none |  |

Stop interpretation if any high or medium validation issue remains unresolved.

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

Split, dividend, merger, delisting, stale-row, and symbol-change handling:

Known manual edits:

Known excluded rows or symbols:
```

Stop interpretation if any return, feature, benchmark, or backtest-like output
depends on an unknown or incompatible adjustment policy.

## 6. Universe And Benchmark Review

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

Stop interpretation if universe membership is not date-aware and survivorship
bias is not documented.

## 7. Date Alignment And Timing Review

Keep feature dates, universe dates, rebalance dates, execution dates, and return
measurement dates separate.

| Item | Evidence reviewed | Issue level | Decision |
| --- | --- | --- | --- |
| Latest data timestamp is known for each signal date |  | high / medium / low / none |  |
| Feature lookbacks do not use future rows |  | high / medium / low / none |  |
| Universe membership is known before the signal date |  | high / medium / low / none |  |
| Liquidity eligibility lag is explicit |  | high / medium / low / none |  |
| Rebalance timing is explicit |  | high / medium / low / none |  |
| Execution timing is explicit |  | high / medium / low / none |  |
| Forward-return measurement starts after signal formation |  | high / medium / low / none |  |
| Off-by-one checks were reviewed |  | high / medium / low / none |  |

Stop interpretation if future prices, future universe membership, future
benchmark values, or same-period target returns could enter a feature.

## 8. Sample Split, Parameters, Costs, And Slippage

```text
Warm-up exclusion:

In-sample period:

Validation period:

Test or holdout period:

Fixed parameters:

Parameter grid, if any:

When parameters were chosen:

Transaction cost model:

Slippage model:

Turnover model:

Rebalance frequency:

Execution timing:

Benchmark comparison:

How weak, failed, ambiguous, or stopped cases will be recorded:
```

Stop interpretation if parameter choices are compared before sample splits and
parameter policy are recorded. Zero-cost or no-slippage output may be used only
as a diagnostic caveat, not as execution evidence.

## 9. Issue Register

Use high for blockers that can change interpretation or violate guardrails. Use
medium for unresolved evidence gaps that can materially affect conclusions. Use
low for caveats that are documented and do not affect date alignment, data
availability, or interpretation.

| ID | Area | Issue | Evidence | Level | Resolution or limitation | Status |
| --- | --- | --- | --- | --- | --- | --- |
|  | provenance |  |  | high / medium / low |  | open / accepted / resolved |
|  | schema |  |  | high / medium / low |  | open / accepted / resolved |
|  | validation |  |  | high / medium / low |  | open / accepted / resolved |
|  | adjustment policy |  |  | high / medium / low |  | open / accepted / resolved |
|  | universe |  |  | high / medium / low |  | open / accepted / resolved |
|  | benchmark |  |  | high / medium / low |  | open / accepted / resolved |
|  | date alignment |  |  | high / medium / low |  | open / accepted / resolved |
|  | missing data |  |  | high / medium / low |  | open / accepted / resolved |
|  | interpretation |  |  | high / medium / low |  | open / accepted / resolved |

Any unresolved high or medium issue stops interpretation.

## 10. Gate Decision

```text
High issues open:

Medium issues open:

Low issues accepted as limitations:

Stop conditions triggered:

Decision:
  [ ] stop before loading files
  [ ] load only for schema smoke test
  [ ] run feature audit only
  [ ] run diagnostic-only workflow
  [ ] prepare full experiment candidate after audit

Decision rationale:
```

Local CSV diagnostics are not profitability evidence. A passed readiness audit
only permits the next reviewed research step under the recorded limitations.

## 11. Experiment Log Handoff

Before any real-data output is committed or interpreted, prepare an
`EXPERIMENT_LOG.md` entry that records:

- experiment ID and date.
- data source and local file references, with redaction where needed.
- universe and survivorship-bias caveats.
- date range and sample splits.
- feature formulas, lookbacks, lags, and timing assumptions.
- parameters and parameter-selection policy.
- benchmark.
- transaction costs and slippage.
- rebalance and execution timing.
- metrics and limitations.
- missing-data summary.
- high, medium, and low audit issues.
- failure modes and next action.

Synthetic JSON sidecar logs are not substitutes for this record.

## 12. Final Stop Statements

Do not interpret or publish results unless every statement below is true.

- [ ] Local files were supplied by the user and no data was fetched.
- [ ] No vendor API, `requests`, `yfinance`, Alpaca, CCXT, credential, token,
      or `.env` path was used.
- [ ] No live trading, paper trading, brokerage integration, order execution,
      or account access was added.
- [ ] No source data was committed unless it is an approved tiny synthetic or
      public fixture.
- [ ] No missing values were silently coerced, forward-filled, backward-filled,
      interpolated, or replaced with zero.
- [ ] Feature dates, universe dates, rebalance dates, execution dates, and
      return measurement dates are distinct.
- [ ] Sample splits, parameter policy, costs, slippage, benchmark, and
      execution timing are recorded before interpretation.
- [ ] No unresolved high or medium audit issue remains.
- [ ] The output language is caveated as simulated research or diagnostics.
- [ ] The output does not claim profitability, robustness, tradeability,
      deployment readiness, investment advice, or future performance.

If any box cannot be checked, stop before interpretation.
