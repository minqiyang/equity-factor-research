# EODHD Loader Smoke Checkpoint And Diagnostics Dry Run Plan

Date: 2026-06-28

This documentation-only checkpoint records the completed private EODHD
validation-only loader smoke test and scopes the next diagnostics dry-run
boundary. It does not copy private market data into the repository, fetch data,
call vendor APIs, use credentials, run a strategy, run a backtest, compute
factor performance, interpret returns, or make profitability, alpha,
investment, robustness, or trading-readiness claims.

## Private Loader Smoke Test Evidence

Private bundle:

```text
/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run
```

Private summary:

```text
/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/LOADER_SMOKE_TEST_SUMMARY.md
```

The summary remains outside the repository and is not git-tracked.

Existing strict loaders used:

- `load_ohlcv_csv(..., require_adjusted_close=True)`
- `load_benchmark_price_csv(..., value_column="adjusted_close")`

Aggregate result:

| Check | Result |
| --- | --- |
| Symbol coverage | 11/11 |
| Benchmark | SPY.US |
| Asset date range | 2018-01-02 to 2026-06-26 |
| Benchmark date range | 2018-01-02 to 2026-06-26 |
| Asset rows | 21320 |
| Benchmark rows | 2132 |
| Required columns present | true |
| Duplicate asset date-symbol rows | 0 |
| Duplicate benchmark date-symbol rows | 0 |
| Missing required values | 0 |
| Non-positive asset price values | 0 |
| Non-positive benchmark price values | 0 |
| Negative asset volume rows | 0 |
| Negative benchmark volume rows | 0 |
| Asset zero-volume rows | 0 |
| Benchmark zero-volume rows | 0 |
| Invalid asset OHLC rows | 0 |
| Invalid benchmark OHLC rows | 0 |
| Missing benchmark dates from asset calendar | 0 |
| Extra benchmark dates outside asset calendar | 0 |
| Sensitive-marker hits in private summary | 0 |

This evidence supports only local loader/schema readiness and benchmark-date
alignment. It does not validate a factor, strategy, portfolio, return series,
execution model, or research conclusion.

## Diagnostics Dry Run Boundary

The next diagnostics dry run may inspect only data-quality and readiness
properties from already-local private files. It may summarize:

- per-symbol coverage and date ranges.
- trading-date overlap between assets and SPY.US.
- missing-value counts by required field.
- duplicate-date and duplicate `(date, symbol)` counts.
- non-positive price, negative-volume, zero-volume, stale-row, and invalid
  OHLC counts.
- calendar gaps and partial-coverage dates.
- raw OHLC versus `adjusted_close` adjustment-policy caveats.
- static-universe survivorship caveats.

The dry run must write any private output only under:

```text
/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run
```

## Stop Conditions

Stop before the diagnostics dry run if it would require:

- source, test, research-script, report, loader, backtester, metric, factor, or
  generated-output changes.
- fetching or downloading data.
- vendor APIs, credentials, tokens, account data, or `.env` files.
- copying private CSV/JSON files into the repository.
- printing full CSV contents.
- forward-filling, backward-filling, zero-filling, interpolating, repairing, or
  inferring missing data or corporate actions.
- computing factors, signals, portfolio weights, returns, IC, Rank IC,
  quantile spreads, backtests, benchmark-relative performance, alpha, or
  trading-readiness evidence.
- interpreting any output beyond diagnostics and readiness limitations.

## Open Caveats

- The universe is a static selected list, not point-in-time membership.
- Raw OHLC fields and `adjusted_close` may have different adjustment
  semantics.
- SPY.US is validated only as a benchmark series for date alignment.
- Sample splits, cost/slippage assumptions, execution timing, parameter policy,
  and a full experiment-log handoff remain unresolved.

## Next Safe Checkpoint

Run or document a no-performance diagnostics dry run that stays inside the
private-output boundary above. If that dry run would need source-code,
research-script, report, or loader changes, stop and create a separate reviewed
PR plan before implementation.
