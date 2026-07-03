# CSV Data Interface Plan

Date: 2026-06-02

## Status: Historical / Superseded In Part

This plan is retained as design history. Strict local CSV loaders and metadata
review helpers have since been implemented and tested in
`src/data/csv_loader.py`, `src/data/local_csv_inventory.py`,
`tests/test_csv_loader.py`, and `tests/test_local_csv_inventory.py`.

The remaining live guidance is the boundary around user-provided data:
validated local ingestion is not broader real-data interpretation. Provenance,
adjustment policy, point-in-time universe status, benchmark methodology, sample
splits, cost/slippage assumptions, and experiment-log records are still
required before any local CSV or EODHD results are interpreted.

This document is a design plan for a future local CSV research interface. It
does not implement a loader, fetch data, define a data vendor, modify feature
or backtest logic, connect to a broker, place orders, or make profitability
claims.

## Purpose

The future CSV interface should let the project ingest user-provided local CSV
files into the existing pandas-based research pipeline while preserving the
project's auditability and date-alignment standards.

The interface should support reproducible local research inputs before any
real-data experiment is treated as evidence. Its first responsibility is to make
data assumptions explicit: schema, date coverage, missing values, adjustment
conventions, benchmark choice, universe membership, and validation failures.

## Non-Goals

- No downloads or remote data access.
- No real data fetching.
- No `requests`, `yfinance`, Alpaca, CCXT, vendor API, or credential logic.
- No live trading, brokerage integration, order execution, or account handling.
- No change to backtester behavior, metrics, alpha formulas, normalization,
  combination, diagnostics, synthetic demos, or generated reports.
- No automatic forward-fill, backward-fill, survivorship-bias repair, corporate
  action adjustment, benchmark substitution, or missing-data repair.
- No profitability, strategy-validation, or investment-performance claim.

## Supported Future Data Types

The first design target is local files already present on disk. The future
loader should reject unsupported schemas rather than guessing.

| Data type | Purpose | Initial requirement |
| --- | --- | --- |
| Adjusted close | Close-to-close feature and backtest inputs | Date plus one or more numeric asset columns, or long rows with `date`, `symbol`, `adjusted_close` |
| OHLCV | Future open/high/low/close/volume research and OHLC alphas | Long rows with `date`, `symbol`, `open`, `high`, `low`, `close`, `volume` and optional `adjusted_close` |
| Benchmark | Benchmark comparison in backtests | Date plus numeric benchmark price or return column |
| Universe membership | Point-in-time universe eligibility | `date`, `symbol`, and explicit membership or eligibility fields |
| Factor panels | Optional precomputed local factor research inputs | Wide date-indexed factor panel or long `date`, `symbol`, `factor_name`, `value` rows |
| Metadata | Audit context such as source name and adjustment policy | Separate metadata file or sidecar fields, never credentials |

## Proposed Schemas

### Wide Price Panel

Use for adjusted close prices when each asset has one column.

| Column | Type | Notes |
| --- | --- | --- |
| `date` | date-like string | Parsed to a timezone-naive pandas `DatetimeIndex` |
| asset columns | numeric | One column per symbol, usually adjusted close |

Example shape:

```text
date,AAPL,MSFT,SPY
2024-01-02,184.73,370.87,472.65
2024-01-03,183.35,370.60,468.79
```

Validation should preserve the file's symbol labels and require strictly
increasing, duplicate-free dates after parsing.

### Long Price Format

Use when price observations arrive one row per asset/date.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `date` | date-like string | yes | Observation date |
| `symbol` | string | yes | Asset identifier |
| `adjusted_close` | numeric | yes | Adjusted close price |

The future loader may pivot this into a wide adjusted-close panel only after
checking duplicate `(date, symbol)` rows and numeric price validity.

### OHLCV Long Format

Use for future volume-aware or OHLC-dependent research. This schema is
documentation-only in this stage.

See `docs/volume_ohlcv_schema_plan.md` for the follow-up planning gate that
details future volume-only, OHLCV, metadata, validation, alignment, and
implementation-stage requirements before any loader support is added.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `date` | date-like string | yes | Observation date |
| `symbol` | string | yes | Asset identifier |
| `open` | numeric | yes | Raw or adjusted convention must be documented |
| `high` | numeric | yes | Must be consistent with `open`, `low`, `close` convention |
| `low` | numeric | yes | Must be consistent with `open`, `high`, `close` convention |
| `close` | numeric | yes | Raw close unless explicitly documented otherwise |
| `volume` | numeric | yes | Non-negative share volume |
| `adjusted_close` | numeric | optional | Required for close-to-close adjusted-price workflows |

The future loader should not infer adjustment policy. If raw and adjusted fields
coexist, downstream code must be told which field it is using.

## Validation Rules

The future loader should fail loudly on ambiguous data. It should return both
validated data and an audit summary, but this stage does not implement either.

- Dates must be parseable and normalized consistently.
- Dates must be sorted in increasing order before they are passed to feature
  helpers.
- Duplicate dates in wide panels must be rejected.
- Duplicate `(date, symbol)` observations in long panels must be rejected.
- Required columns must be present with exact names for each selected schema.
- Numeric fields must already be numeric or be explicitly parsed with error
  reporting.
- Silent string-to-`NaN` coercion must be rejected.
- Boolean columns must not be accepted as numeric market data.
- Non-positive adjusted prices should be reported and rejected for price panels.
- OHLC rows should report impossible relationships such as `high < low`.
- Volume should be numeric and non-negative.
- Missing values must be reported by date, symbol, field, and count.
- Forward-fill and backward-fill must be disabled by default.
- Calendar gaps should be reported, not automatically filled.
- Universe membership must be date-stamped and must not use future membership
  information for earlier dates.
- Benchmark series must be validated separately and aligned explicitly to
  strategy dates.

## Alignment With Current Modules

The current project already expects clean pandas objects. The future CSV
interface should adapt local files to those expectations without changing the
core research functions.

| Module | Expected alignment |
| --- | --- |
| `src/features/operators.py` | Produce sorted, duplicate-free, numeric date-indexed panels that satisfy `validate_panel_data` |
| `src/features/worldquant_alphas.py` | Feed `alpha_009` only close-price panels; the output remains a research feature, not a strategy |
| `src/features/normalize.py` | Pass already validated factor panels; no sorting or filling should be added inside normalization helpers |
| `src/features/combine.py` | Provide exactly aligned factor panels before weighted combination |
| `src/features/diagnostics.py` | Provide aligned panels and preserve missing values for overlap-aware diagnostics |
| `src/backtest/portfolio.py` | Provide adjusted price panels, signal panels, and benchmark series with documented signal lag, rebalance timing, cost, slippage, and benchmark assumptions |

Feature dates, execution dates, and return measurement dates must remain
distinct. A future loader should not decide execution timing; it should only
record data availability and validation results.

## Risks And Research Caveats

- Survivorship bias from static ticker lists.
- Corporate actions, including splits, dividends, mergers, and symbol changes.
- Delistings and stale prices.
- Adjusted versus raw price ambiguity.
- Vendor differences in price history, volume, symbol mapping, and benchmark
  construction.
- Benchmark mismatch between selected universe and benchmark asset.
- Calendar mismatch across assets, markets, and benchmark series.
- Hidden look-ahead through universe membership or revised metadata.
- Missing values that make synthetic-clean tests look stronger than local CSV
  data will support.
- Overfitting risk once parameter studies move from synthetic data to local
  datasets.

These risks must be documented in future experiment records before any
real-data research output is interpreted.

## Future Stages

1. Use `docs/volume_ohlcv_schema_plan.md` as the planning gate before adding
   any volume or OHLCV loader support.
2. Implement a local CSV loader for user-provided local CSV files only, with
   schema selection and strict validation tests.
3. Add a real-data readiness audit that checks data provenance, adjustment
   policy, universe construction, benchmark choice, sample splits, costs, and
   slippage assumptions before any real-data experiment.
4. Update the QuantConnect/LEAN plan to describe how local CSV validation maps
   to platform data assumptions and where the two workflows can diverge.
5. Add experiment-log requirements for local CSV runs, including source path,
   file hash or version identifier, schema, validation summary, universe rules,
   and known data limitations.

Each future stage should remain a separate reviewed PR.
