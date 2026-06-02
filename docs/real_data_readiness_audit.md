# Real-Data Readiness Audit

Date: 2026-06-02

This checklist is a pre-experiment gate for using user-provided local CSV data
in the research pipeline. It does not fetch data, download data, choose a data
vendor, add credentials, connect to a broker, place orders, support live
trading, or make profitability claims.

Passing this checklist does not make a strategy validated. It only records
that the local data and experiment setup have enough documented context for a
reviewable research run.

## Required Scope Statement

Before running any local CSV experiment, write a short scope statement that
answers:

- What local files will be used?
- Which schema each file follows: wide price, long price, benchmark, universe
  membership, factor panel, metadata, or another documented schema.
- Which date range is intended for the run.
- Which assets or universe rules are intended.
- Which features, if any, will be calculated.
- Whether the run is a loader smoke test, feature calculation audit, backtest
  diagnostic, or full experiment candidate.

If this statement cannot be written clearly, stop before running the
experiment.

## Data Provenance

Record enough information that another reviewer can identify the exact local
inputs without relying on memory.

Required:

- Local file path for each input.
- File timestamp or version identifier.
- File hash, if the file may be revised or replaced.
- Data source name as provided by the user.
- Whether the file is raw export, hand-cleaned, vendor-cleaned, or derived from
  another file.
- Any known manual edits.
- Any known missing symbols, missing dates, stale prices, or excluded rows.

Do not store credentials, account IDs, API keys, or private account metadata in
the repository.

## Schema And Loader Checks

For each CSV file, record:

| Check | Required evidence |
| --- | --- |
| Schema selected | Wide price, long price, benchmark, universe, factor, or metadata |
| Required columns | Present with exact expected names |
| Date parsing | Dates parse successfully and are timezone-naive unless explicitly documented |
| Date order | Dates are sorted after validation |
| Duplicate dates | No duplicates in wide date-indexed files |
| Duplicate date-symbol pairs | No duplicates in long asset files |
| Numeric fields | Parsed explicitly with errors surfaced |
| Missing values | Counted by file, field, date, and symbol where possible |
| Non-positive prices | Rejected or separately justified before use |
| Forward-fill/backward-fill | Disabled unless a later reviewed stage adds explicit policy |

The current local CSV loader is allowed only to read user-provided local files.
It must not download data or call vendor APIs.

## Price Adjustment Policy

Document the adjustment convention before calculating returns or features.

Required:

- Whether prices are adjusted close, raw close, split-adjusted, dividend-adjusted,
  total-return adjusted, or unknown.
- Whether open, high, low, close, and adjusted close fields use the same
  adjustment convention.
- Whether volume is raw share volume or adjusted volume.
- How splits, dividends, mergers, symbol changes, and delistings are represented.
- Whether the benchmark uses the same adjustment convention as the asset panel.

If adjustment policy is unknown, do not treat return metrics as research
evidence.

## Universe Construction

Universe rules must be date-aware and documented before the run.

Required:

- Starting universe definition.
- Liquidity or volume filters, if any.
- Price filters, if any.
- Minimum history requirements.
- Inclusion and exclusion rules.
- How delisted, merged, stale, suspended, or missing symbols are handled.
- Whether universe membership is point-in-time or a static current list.
- Survivorship-bias risk statement.

Future universe membership must not be used for earlier dates.

## Benchmark Choice

Record benchmark assumptions before computing benchmark-relative metrics.

Required:

- Benchmark symbol or local benchmark file.
- Why the benchmark matches the intended universe.
- Benchmark date range.
- Benchmark price or return field.
- Missing benchmark dates.
- Adjustment convention.
- How benchmark dates align to strategy dates.

If benchmark coverage is incomplete, the experiment should stop unless the
missing-data policy is explicitly documented as diagnostic.

## Feature And Signal Timing

Feature dates must remain distinct from execution and return measurement dates.

Required:

- Feature formula and required input fields.
- Lookback windows and skipped windows.
- Latest data timestamp available for each signal date.
- Signal lag before portfolio formation.
- Execution timing assumption: next open, next close, next available row, or
  another explicit rule.
- Tests or manual checks for off-by-one risk in rolling windows and lags.

Same-period target returns must not be used as features.

## Sample Splits And Parameter Policy

Before evaluating parameter choices, define:

- In-sample period.
- Validation period.
- Test or holdout period.
- Any warm-up period excluded from evaluation.
- Parameter grid or fixed parameter policy.
- Whether parameter choices were made before or after looking at results.
- How weak, failed, or ambiguous cases will be recorded.

Do not report only the best parameter result.

## Costs, Slippage, And Execution Assumptions

Every backtest-like run must state:

- Transaction cost model.
- Slippage model.
- Turnover model.
- Rebalance frequency.
- Execution timing.
- Benchmark choice.
- Whether zero-cost or zero-slippage settings are used only as diagnostics.

Zero-cost or no-slippage results must not be presented as realistic execution
evidence.

## Required Experiment-Log Fields

Before committing any real-data experiment output, add or prepare an
`EXPERIMENT_LOG.md` entry that includes:

- Data source and local file references.
- Universe definition and survivorship-bias caveats.
- Date range and sample splits.
- Feature formulas, lookbacks, lags, and data availability assumptions.
- Parameters and parameter-selection policy.
- Benchmark.
- Transaction costs and slippage.
- Rebalance and execution timing.
- Metrics and limitations.
- Missing-data summary.
- Failure modes.
- Next action.

Synthetic demo JSON logs are not substitutes for this real-data experiment
record.

## Stop Conditions

Stop the run before interpreting any result if:

- Required data provenance is missing.
- Price adjustment policy is unknown.
- The universe is a static current list and survivorship bias is not documented.
- Benchmark coverage or adjustment is incompatible with the asset data.
- Missing values are silently filled.
- Dates or date-symbol rows are duplicated without reviewed resolution.
- Feature timing cannot be shown to precede execution timing.
- Sample splits are not defined for parameter selection.
- Costs, slippage, or execution assumptions are absent.
- The result would require a profitability or investment-performance claim.

## Approval Gate

A real-data experiment may proceed only after this audit identifies no
unresolved high or medium issues. Low issues may proceed only when they are
documented as limitations and do not affect date alignment, data availability,
or interpretation of results.

The first use of local CSV data should still be treated as a smoke test unless
a separate reviewed PR adds the full experiment record, validation split, and
result interpretation.
