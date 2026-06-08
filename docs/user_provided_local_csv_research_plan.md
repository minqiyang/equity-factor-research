# User-Provided Local CSV Research Plan

Date: 2026-06-08

This is a documentation-only plan for a future research workflow that uses
CSV files already present on the user's local machine.

It does not load user files, fetch data, download data, choose a vendor, add
credentials, add API access, add live trading, add paper trading, connect to a
broker, place orders, modify strategy logic, run a real-data study, or claim
profitability.

## 1. Purpose

The project now has strict local CSV loaders, synthetic fixtures, factor
helpers, diagnostics, local-fixture workflow demos, liquidity eligibility,
liquidity universe masks, universe-masked signals, and synthetic backtest smoke
coverage.

The next requirement is not more factor implementation. The next requirement is
a repeatable plan for how a future user-provided local CSV study should be
scoped, audited, logged, and stopped when the evidence is not strong enough to
interpret.

This plan defines the required inputs, audit artifacts, workflow gates, and
stop conditions before any future result from local user CSV files can be
reported as research evidence.

## 2. Non-Goals

- No real data fetching or remote data access.
- No `requests`, `yfinance`, Alpaca, CCXT, vendor API, credential, token, or
  `.env` handling.
- No live trading, paper trading, brokerage integration, account access, order
  execution, fill model, or production deployment.
- No source-code implementation in this stage.
- No changes to loaders, factor helpers, diagnostics, backtester, metrics,
  research scripts, generated reports, tests, or synthetic fixtures.
- No automatic forward-fill, backward-fill, zero-fill, interpolation, calendar
  repair, symbol repair, survivorship-bias repair, or corporate-action repair.
- No profitability, investment-performance, robustness, tradeability, or
  strategy-validation claim.

## 3. Intended Future Workflow

Future user-provided local CSV work should proceed through these gates in
order.

| Gate | Required artifact | Stop condition |
| --- | --- | --- |
| Scope statement | A short description of local files, schema, date range, universe, benchmark, features, run type, and intended interpretation level. | Stop if the run objective is unclear or requires downloads, credentials, trading, or performance claims. |
| File inventory | Local paths, timestamps or versions, hashes when files can change, source names supplied by the user, and known manual edits. | Stop if provenance, revision history, or private/credential content cannot be separated from research metadata. |
| Schema map | Explicit schema for each file: wide price, long price, OHLCV, benchmark, universe membership, factor panel, or metadata. | Stop if the schema must be guessed or required columns are missing. |
| Loader validation | Date parsing, duplicate checks, numeric validation, missing-value summary, non-positive price checks, OHLC consistency, and benchmark coverage. | Stop if invalid values are silently coerced, filled, or repaired. |
| Readiness audit | Completed real-data readiness audit with no unresolved high or medium issues. | Stop interpretation if provenance, adjustment policy, universe, benchmark, date alignment, or missing-data policy is unresolved. |
| Experiment record | Prepared `EXPERIMENT_LOG.md` entry with data source, universe, splits, features, costs, slippage, metrics, limitations, failure modes, and next action. | Stop if synthetic JSON logs are being used as a substitute for a real local CSV experiment record. |
| Reviewable output | Caveated report or diagnostic output that states the run type and limitations. | Stop if the result would need to be described as profitable, robust, tradeable, or investment evidence. |

## 4. Required Local Input Bundle

A future local CSV study should declare exactly which files are used before any
results are interpreted.

| Input | Required for | Minimum metadata |
| --- | --- | --- |
| Adjusted close price panel | Close-based factors, forward returns, and simulated backtests. | Local path, source name, adjustment convention, date range, symbol count, missing-value summary, non-positive price check. |
| OHLCV panel | Volume-aware factors, liquidity eligibility, and OHLC-dependent research features. | Local path, source name, raw versus adjusted field policy, volume convention, zero-volume count, stale-row caveats. |
| Benchmark series | Benchmark-relative diagnostics or backtests. | Local path, benchmark identity, adjustment policy, date coverage, missing dates, and compatibility with the asset panel. |
| Universe membership | Point-in-time universe studies. | Local path, membership rule, date stamp, point-in-time status, exclusions, symbol changes, delistings, and survivorship-bias statement. |
| Optional factor panel | User-supplied factor diagnostics. | Local path, formula or source, timing assumption, missing-value summary, and whether values are known before the signal date. |
| Metadata sidecar | Provenance and audit context. | Source notes, export settings, revision notes, corporate-action policy, calendar notes, and limitation notes. |

User data files themselves should not be committed unless a later reviewed stage
explicitly approves a tiny synthetic or public fixture. Private, proprietary,
credential-like, account-specific, or personally identifying files should remain
outside the repository.

## 5. Scope Statement Template

Each future local CSV run should start with a plain-language scope statement.

```text
Run type:
  loader smoke test | feature audit | diagnostic-only backtest | full experiment candidate

Local files:
  prices:
  ohlcv:
  benchmark:
  universe:
  metadata:

Schema choices:
  prices:
  ohlcv:
  benchmark:
  universe:

Date range:
  intended start:
  intended end:
  warm-up exclusion:

Universe:
  starting universe:
  liquidity rule:
  point-in-time status:
  survivorship-bias caveat:

Features and signals:
  formulas:
  lookbacks:
  signal lag:
  latest available data timestamp:

Evaluation:
  sample splits:
  benchmark:
  costs:
  slippage:
  rebalance timing:
  interpretation level:
```

If the scope statement cannot be completed, the run should stop before metrics
are interpreted.

## 6. Validation Requirements

Validation should fail loudly and leave an audit trail.

- Dates must parse and normalize consistently.
- Wide date-indexed files must reject duplicate dates.
- Long files must reject duplicate `(date, symbol)` observations.
- Numeric fields must reject blank strings, missing sentinels, booleans, and
  invalid numeric-looking text before conversion.
- Missing values must be counted by file, field, date, and symbol when
  possible.
- Non-positive prices must be rejected or separately justified before use.
- OHLCV files must reject negative volume and impossible OHLC relationships.
- Benchmark dates must be aligned explicitly to strategy dates.
- Calendar gaps must be reported, not automatically filled.
- No forward-fill, backward-fill, interpolation, or zero default may be added
  unless a later reviewed policy documents and tests it.

## 7. Research Design Requirements

Before any diagnostic output is interpreted, the future run must record:

- price adjustment policy for assets and benchmark.
- volume policy, including raw versus adjusted volume if relevant.
- universe membership rule, point-in-time status, and survivorship-bias caveat.
- feature formulas, input fields, lookbacks, skipped windows, and signal lag.
- sample split boundaries and warm-up exclusions.
- fixed parameter policy or pre-declared parameter grid.
- benchmark choice and why it matches the intended universe.
- transaction cost, slippage, turnover, rebalance frequency, and execution
  timing assumptions.
- low-coverage dates, missing-signal counts, missing-return counts, and any
  stopped or weak cases.

No run should report only the best parameter result.

## 8. Interpretation Levels

Future local CSV work should label output by interpretation level.

| Level | Meaning | Allowed interpretation |
| --- | --- | --- |
| Loader smoke test | Proves a local file can pass schema and validation checks. | Data ingestion is reviewable; no factor or performance evidence. |
| Feature audit | Computes a feature panel and timing checks. | Feature calculation is inspectable; no strategy evidence. |
| Diagnostic-only backtest | Exercises the simulated backtester with declared assumptions. | Workflow diagnostic under explicit assumptions; not tradeability or profitability evidence. |
| Full experiment candidate | Has complete provenance, readiness audit, experiment log, splits, costs, benchmark, and limitations. | Reviewable research evidence only if no high or medium audit issue remains. |

Even the highest level remains simulated research. It is not investment advice,
not a live-trading system, and not a profitability claim.

## 9. Stop Conditions

Stop before interpretation if any of these are true:

- data source, file version, timestamp, or hash is missing for a mutable file.
- adjustment policy is unknown or incompatible between asset and benchmark
  data.
- universe membership is not date-aware and survivorship bias is not documented.
- benchmark coverage, benchmark adjustment policy, or benchmark date alignment
  is unresolved.
- duplicate dates, duplicate date-symbol rows, or invalid numeric fields remain
  unresolved.
- missing data is silently coerced, filled, interpolated, forward-filled,
  backward-filled, or converted to zero.
- feature dates, universe dates, rebalance dates, execution dates, and return
  measurement dates are blurred.
- sample splits or parameter policy are absent before parameter comparison.
- costs, slippage, turnover, rebalance frequency, or execution timing are
  missing for a backtest-like run.
- any unresolved high or medium issue remains in the real-data readiness audit.
- the output would need to be described as profitable, robust, tradeable,
  deployment-ready, or investment evidence.

## 10. Expected Future PR-Sized Stages

1. Add a local CSV study checklist or template that can be completed before
   reading any user-provided data.
2. Add a dry-run validator that checks a declared local-file inventory without
   storing private paths or data in generated reports.
3. Add a synthetic fixture rehearsal of the user-provided CSV research plan
   using committed synthetic fixtures only.
4. Add a real-data readiness audit report format that can be filled manually
   before interpretation.
5. Only after those stages are reviewed, consider a local-file-only smoke run
   on user-provided data with no downloads, no committed private data, no
   trading behavior, and no profitability interpretation.

Each stage should remain a separate reviewed PR.

## 11. Final Recommendation

The next implementation after this plan should still avoid user data. A safe
follow-up would be a template/checklist stage that prepares the artifacts a
future user-provided local CSV run must complete before any file is loaded or
any result is interpreted.
