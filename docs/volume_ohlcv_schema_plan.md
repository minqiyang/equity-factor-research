# Volume And OHLCV Schema Plan

Date: 2026-06-06

This document plans future local CSV schema support for volume and OHLCV data
before any volume-dependent factor, OHLC-dependent alpha, or liquidity universe
filter is implemented.

It is documentation only. It does not implement a loader, modify the existing
CSV loader, add fixtures, fetch data, download data, choose a vendor, add
credentials, connect to a broker, place orders, support live trading, modify
backtester behavior, or make profitability claims.

## Purpose

The project currently supports strict local CSV loading for adjusted close
panels, long adjusted-close rows, and benchmark price series. The next data
prerequisite is a reviewed local schema for volume and OHLCV files so future
liquidity, volatility, reversal, and WorldQuant-style alpha stages can be
scoped without guessing data shape or adjustment policy.

This plan defines the expected local file shapes, validation rules, alignment
requirements, and staged implementation boundary. It keeps the project in the
same research-only posture: local files only, no automatic downloads, no
brokerage integration, and no performance interpretation.

## Non-Goals

- No loader implementation in this stage.
- No changes to `src/data/csv_loader.py`.
- No new fixtures or generated reports.
- No vendor, API, `requests`, `yfinance`, Alpaca, CCXT, or credential logic.
- No live trading, paper trading, brokerage integration, order execution, or
  account handling.
- No new alpha formula, factor calculation, universe filter, backtest behavior,
  metric, LEAN runtime code, or strategy interpretation.
- No automatic missing-data repair, forward-fill, backward-fill, zero-fill,
  corporate-action adjustment, benchmark substitution, or universe repair.
- No profitability, investment-performance, robustness, or trading-readiness
  claim.

## Current State

Current local CSV support is intentionally narrow and local-file-only:

| Current loader | Input shape | Current role |
| --- | --- | --- |
| `load_wide_price_csv()` | `date` plus one adjusted-close column per asset | Wide adjusted-close research panel |
| `load_long_price_csv()` | `date`, `symbol`, `adjusted_close` | Long adjusted-close rows pivoted to a wide panel |
| `load_benchmark_price_csv()` | `date`, `benchmark_price` | Date-indexed benchmark price series |
| `load_ohlcv_csv()` | `date`, `symbol`, `open`, `high`, `low`, `close`, `volume`, optional `adjusted_close` | Long OHLCV validation frame for fixture diagnostics and future data-dependent planning |

The current loader rejects remote URL-like paths, duplicate headers, bad dates,
duplicate dates or duplicate `(date, symbol)` rows where applicable,
non-positive price fields, negative volume, invalid numeric strings, default
missing values, silent string-to-`NaN` coercion, and invalid OHLC
relationships. These strict defaults should carry forward into any future
volume-only loader, liquidity filter, dollar-volume workflow, or OHLC-dependent
alpha stage.

## Proposed Future Schemas

### Volume Long Format

Use this for local volume-only panels or liquidity screening inputs when price
data is already loaded from a separate adjusted-close file.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `date` | date-like string | yes | Observation date |
| `symbol` | string | yes | Asset identifier |
| `volume` | numeric | yes | Non-negative share volume |

Validation should reject duplicate `(date, symbol)` rows and preserve symbol
labels exactly after trimming only the minimum whitespace needed to identify
missing symbols.

### OHLCV Long Format

Use this for future open, high, low, close, and volume research. This should be
the first implementation target if a future PR adds OHLCV loading.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `date` | date-like string | yes | Observation date |
| `symbol` | string | yes | Asset identifier |
| `open` | numeric | yes | Raw or adjusted convention must be documented |
| `high` | numeric | yes | Same adjustment convention as `open`, `low`, and `close` |
| `low` | numeric | yes | Same adjustment convention as `open`, `high`, and `close` |
| `close` | numeric | yes | Raw close unless explicitly documented otherwise |
| `volume` | numeric | yes | Non-negative share volume |
| `adjusted_close` | numeric | optional | Required when close-to-close adjusted-return research is needed |

The future loader should not infer whether OHLC values are raw, split-adjusted,
dividend-adjusted, or total-return adjusted. If the adjustment policy is
unknown, the validated output may be used only for loader diagnostics, not for
feature interpretation.

### Optional Metadata Sidecar

Future real-data readiness can use a separate metadata file or documented
experiment-log fields. It should not be required for the first synthetic
fixture loader stage, but real user-provided local CSV research should record:

| Field | Purpose |
| --- | --- |
| `source_name` | User-provided source or vendor label |
| `file_version` | Timestamp, hash, or version identifier |
| `price_adjustment_policy` | Raw, split-adjusted, dividend-adjusted, total-return adjusted, or unknown |
| `volume_policy` | Raw share volume, adjusted volume, or unknown |
| `currency` | Price currency if known |
| `calendar` | Market calendar or known calendar limitations |

Metadata must not contain credentials, account identifiers, access tokens, API
keys, private account information, or broker details.

## Validation Rules

Future volume and OHLCV loaders should preserve the existing strict CSV
behavior:

- Read raw strings first with default missing-value coercion disabled.
- Reject missing sentinels such as blank strings, whitespace-only strings,
  `nan`, `NaN`, `NA`, and `null` by default before numeric conversion.
- Allow missing values only through an explicit non-default policy that is
  documented and tested.
- Reject duplicate CSV headers.
- Require exact required-column names for the selected schema.
- Require parseable, timezone-naive dates.
- Require dates to be sorted in increasing order after validation.
- Reject duplicate `(date, symbol)` rows.
- Reject missing symbols.
- Reject boolean columns as numeric market data.
- Reject non-finite numeric values.
- Reject negative volume.
- Treat zero volume as valid loader input because it is non-negative local
  market data; future liquidity or dollar-volume workflows must explicitly
  report, filter, or reject zero-volume rows in their own scope.
- Require positive `open`, `high`, `low`, `close`, and `adjusted_close` values
  when present.
- Reject impossible OHLC relationships:
  - `high < low`
  - `high < open`
  - `high < close`
  - `low > open`
  - `low > close`
- Report missing values by field and, when possible, by date and symbol.
- Report calendar gaps instead of filling them.
- Do not forward-fill, backward-fill, zero-fill, interpolate, or infer
  corporate-action adjustments by default.

## Alignment Requirements

Future volume and OHLCV outputs should be compatible with the existing pandas
research modules without forcing those modules to sort, fill, or repair data.

| Consumer | Required alignment |
| --- | --- |
| `src/features/operators.py` | Numeric, sorted, duplicate-free date-symbol panels that preserve missing values |
| `src/features/worldquant_alphas.py` | OHLCV or volume columns only when a future alpha explicitly requires them |
| `src/features/diagnostics.py` | Aligned factor and forward-return panels with missing values still visible |
| `src/backtest/portfolio.py` | Liquidity filters and price panels must be date-aligned before portfolio construction |
| `docs/real_data_readiness_audit.md` | Adjustment policy, universe construction, benchmark, sample splits, costs, and slippage must be documented before interpretation |
| `docs/quantconnect_lean_plan.md` | LEAN mapping must distinguish local file validation from platform data subscriptions and fill behavior |

Feature dates, execution dates, and return measurement dates must remain
separate. A loader should validate and summarize data; it should not choose
execution timing, portfolio weights, benchmark substitutions, or factor
interpretation.

## Research Risks

Volume and OHLCV data introduce risks that adjusted-close-only workflows do not
fully expose:

- Raw versus adjusted OHLC ambiguity.
- Raw versus adjusted volume ambiguity after stock splits.
- Stale volume or zero-volume rows.
- Suspensions, halts, delistings, mergers, and symbol changes.
- Vendor-specific high/low/open construction.
- Missing intraday context behind daily OHLC bars.
- Calendar mismatch between assets and benchmark.
- Survivorship bias from static ticker lists.
- Liquidity filters that accidentally use future information.
- Dollar-volume filters that depend on mismatched raw close, adjusted close, or
  volume conventions.
- OHLC relationships that can look valid while still using incompatible
  adjustment policies.

These risks must be visible in future readiness audits and experiment logs
before any local CSV result is interpreted.

## Future PR-Sized Stages

1. Add a synthetic volume/OHLCV loader design review test plan, still
   documentation-only if implementation details remain ambiguous. Completed by
   this planning gate because the implementation boundary was clear enough to
   proceed directly.
2. Implement a strict local OHLCV long-format loader using committed synthetic
   fixtures only. Completed by `load_ohlcv_csv()` and focused loader tests.
3. Add a synthetic OHLCV loader smoke demo that validates schema, missing-value
   policy, OHLC relationships, and summary metadata without computing a
   strategy. Completed by fixture-level smoke tests.
4. Add a liquidity or dollar-volume universe planning note before any code
   filters assets by volume.
5. Plan the next data-dependent alpha stage, such as `alpha_012` or
   `alpha_101`, only after the relevant local schema and validation tests
   exist.
6. Refresh the QuantConnect/LEAN plan if the local OHLCV validation behavior
   changes the LEAN data mapping assumptions.

Each future stage should remain a separate PR and should stop if it requires
real data, external downloads, vendor credentials, live or paper trading,
brokerage integration, order execution, or profitability claims.

## Recommended Next Stage After This Plan

After the strict OHLCV loader and synthetic smoke-demo stages are reviewed and
merged, the next safe stage should be a liquidity or dollar-volume universe
planning note. That planning stage should define local-only inputs,
date-alignment rules, zero-volume handling, dollar-volume formulas, and stop
conditions before any code filters assets by volume.
