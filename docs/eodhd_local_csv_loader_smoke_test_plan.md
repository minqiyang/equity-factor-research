# EODHD Local CSV Loader Smoke Test Plan

Date: 2026-06-28

This documentation-only plan scopes the next validation-only loader smoke test
for the private EODHD local CSV bundle. It does not fetch data, call vendor
APIs, copy private market data into the repository, run a strategy, compute
factor performance, run a backtest, interpret returns, or make profitability,
alpha, investment, or trading-readiness claims.

## Private Bundle

Private bundle path:

```text
/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run
```

Planned loader inputs:

- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/normalized/eodhd_ohlcv_long.csv`
- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/normalized/eodhd_benchmark_spy.csv`
- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/metadata/selected_universe.csv`

Planned private output:

```text
/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/VALIDATION_ONLY_LOADER_SMOKE_TEST_SUMMARY.md
```

No output from this smoke test should be written under the repository.

## Current Evidence To Reuse

The previous private validation-only dry run reported:

| Item | Result |
| --- | --- |
| Symbol coverage | 11/11, including SPY.US benchmark |
| Universe symbols | AAPL.US, MSFT.US, NVDA.US, AMZN.US, GOOGL.US, META.US, JPM.US, XOM.US, JNJ.US, PG.US |
| Benchmark | SPY.US |
| Date range | 2018-01-02 to 2026-06-26 |
| Universe rows | 21320 |
| Benchmark rows | 2132 |
| Schema validation | pass |
| Benchmark alignment | pass |
| Missing required values | 0 |
| Duplicate date-symbol rows | 0 |
| Bad date rows | 0 |
| Bad price rows | 0 |
| Bad volume rows | 0 |
| Credential-marker scan hits | 0 |

These counts support only loader/schema readiness planning. They are not
strategy, factor, portfolio, benchmark-relative, or performance evidence.

## Smoke Test Scope

The next stage may use the existing strict local CSV loaders only. It should:

- load the OHLCV long CSV with `load_ohlcv_csv()` and
  `require_adjusted_close=True`.
- load the benchmark CSV with the existing benchmark loader or the narrowest
  existing validation path that preserves strict local-file behavior.
- inspect only headers, row counts, date ranges, symbol coverage, duplicate
  counts, missing-value counts, invalid-value counts, and benchmark alignment.
- write only a private summary under the private bundle path.
- leave `src/`, `tests/`, `research/`, `reports/`, loaders, backtester,
  metrics, factor logic, generated reports, and committed fixtures unchanged
  unless a later PR explicitly scopes a separate implementation change.

## Required Checks

The smoke test should record:

- required columns present.
- date parsing succeeds and dates are timezone-naive.
- per-symbol date ranges and row counts.
- expected universe coverage for 10 assets plus SPY.US benchmark.
- no duplicate `(date, symbol)` rows.
- positive `open`, `high`, `low`, `close`, and `adjusted_close`.
- non-negative `volume`.
- valid OHLC relationships.
- zero-volume row count, if any.
- benchmark SPY.US present.
- benchmark date range and benchmark alignment against asset dates.
- missing-value counts by required field.
- confirmation the private inputs and private summary are outside the repo and
  not git-tracked.
- credential-marker scan result for created private summary files.

## Stop Conditions

Stop before continuing if any of these occur:

- source, tests, research scripts, reports, generated outputs, loaders,
  backtester, metrics, or factor logic would need changes.
- private CSV/JSON data would enter the repository.
- the loader path would need a vendor API, remote fetch, credential, or
  download.
- required columns are missing or schema mapping becomes ambiguous.
- duplicate rows, bad dates, non-positive prices, negative volumes, invalid
  OHLC relationships, or benchmark-alignment failures remain unresolved.
- EODHD raw OHLC versus `adjusted_close` semantics would need interpretation.
- static-universe survivorship risk would need to be treated as resolved.
- sample splits, cost/slippage assumptions, execution timing, or parameter
  policy would need to be inferred.
- anyone asks to run a strategy, compute factor performance, run a backtest, or
  interpret returns, profitability, alpha, robustness, or trading readiness.

## Caveats To Keep Visible

- The universe is a static selected list, not point-in-time membership.
- Raw OHLC fields and `adjusted_close` can have different adjustment semantics.
- The benchmark is SPY.US, selected for validation alignment only.
- Sample splits, cost/slippage assumptions, execution timing, and full
  experiment-log handoff remain incomplete.

## Next Safe Prompt

```text
Run a validation-only local CSV loader smoke test against:
/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run

Use existing strict loaders only. Write the summary only under that private
bundle. Do not fetch data, use vendor APIs, copy private data into the repo,
modify source/tests/research/reports, run a strategy, run a backtest, compute
factor performance, or interpret returns.
```
