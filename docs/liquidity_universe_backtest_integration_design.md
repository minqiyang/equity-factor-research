# Liquidity Universe Backtest Integration Design

Date: 2026-06-07

This is a documentation-only design for a future, reviewed boundary between
liquidity universe masks and the existing simulated long-only backtester.

It does not modify source code, tests, research scripts, generated reports,
loaders, backtester behavior, metrics, strategy logic, data access, execution
assumptions, or performance claims. It does not fetch data, download data, add
vendor APIs, add credentials, add live trading, add paper trading, add
brokerage integration, add order execution, or claim profitability.

## 1. Purpose

The repository now has three reviewed liquidity-universe prerequisites:

1. Synthetic rolling ADV and rolling dollar-volume eligibility helpers.
2. A synthetic/local-panel `construct_liquidity_universe()` helper that returns
   a boolean mask and audit summary.
3. A committed local CSV fixture workflow that reports universe-mask counts
   without backtesting or performance interpretation.

The next risk is accidentally feeding the universe mask into the backtester
without a complete signal, rebalance, execution, cost, slippage, benchmark, and
audit contract.

This design defines that contract before any source code consumes a liquidity
universe mask in a backtest.

## 2. Current Evidence

| Area | Evidence | Current status |
| --- | --- | --- |
| Liquidity eligibility | `average_daily_volume_eligibility()` and `average_dollar_volume_eligibility()` in `src/features/liquidity.py` | Implemented with explicit positive lag and strict missing/zero-volume behavior. |
| Universe mask | `construct_liquidity_universe()` and `LiquidityUniverseResult` in `src/features/liquidity.py` | Implemented for synthetic/local panels with audit summary and caveats. |
| Fixture smoke check | `research/local_csv_fixture_workflow_demo.py` and its tests/report/log | Reports universe-mask counts only on committed synthetic fixtures. |
| Backtester | `run_long_only_backtest()` in `src/backtest/portfolio.py` | Consumes prices and signals only; it does not accept a universe mask. |
| Backtest timing | `BacktestResult` and tests | Target weights set on date `t` affect returns starting on the next price row; signals are lagged by `signal_lag_periods`. |

This evidence supports a design stage. It does not support a real-data study or
a performance interpretation.

## 3. Non-Goals

- No source-code implementation.
- No changes to `src/backtest/portfolio.py`, `src/backtest/metrics.py`,
  `src/features/liquidity.py`, alpha modules, diagnostics, normalization,
  combination, CSV loaders, research scripts, tests, or reports.
- No user-provided or real-market data.
- No downloads, vendor APIs, `requests`, `yfinance`, Alpaca, CCXT, or
  credential logic.
- No live trading, paper trading, brokerage integration, order execution, or
  account handling.
- No new portfolio-construction rule, position sizing rule, slippage model,
  transaction-cost model, benchmark result, LEAN runtime behavior, or strategy
  result.
- No automatic forward-fill, backward-fill, zero-fill, interpolation, or
  universe repair.
- No profitability, investment-performance, robustness, or trading-readiness
  claim.

## 4. Integration Principle

A liquidity universe mask should filter eligible signal scores before the
existing selection logic ranks assets.

The mask should not directly create target weights. The future integration
should preserve the current separation:

```text
prices + raw factor scores + universe mask
  -> validated universe-masked signal panel
  -> existing long-only ranking/selection backtester
  -> simulated research diagnostics
```

The first implementation should probably be a narrow adapter that prepares
masked signals, rather than a broad rewrite of the backtester.

Possible future helper shape:

```text
apply_universe_mask_to_signals(
    signals: pandas.DataFrame,
    universe_mask: pandas.DataFrame,
    *,
    name: str = "universe_masked_signals",
) -> UniverseMaskedSignalsResult
```

The helper would return:

- `signals`: original signal values where the mask is `True`, missing
  elsewhere.
- `summary`: per-date counts of raw valid signals, universe-eligible assets,
  valid masked signals, excluded-by-universe signals, missing signal values,
  and low-coverage dates.
- `parameters` and `caveats`: inherited universe name, no-real-data,
  no-trading, no-order, no-profitability caveats.

The existing `run_long_only_backtest()` can then consume this masked signal
panel without knowing how the universe was produced.

## 5. Required Alignment Contract

Future code should require strict alignment before masking:

1. `signals.index` and `universe_mask.index` must be identical.
2. `signals.columns` and `universe_mask.columns` must be identical.
3. Both indexes must be sorted, unique `DatetimeIndex` values.
4. Both column sets must be unique.
5. `universe_mask` must be boolean or an audited result from
   `construct_liquidity_universe()`.
6. Missing universe eligibility must not be silently repaired at this layer.
   Missing eligibility should be recorded by the universe-construction helper
   before any masking helper sees the final boolean mask.
7. Missing signal values should remain missing and should be counted, not
   filled.

The future adapter should not rely on the current backtester's internal signal
reindexing as a universe-alignment mechanism. Reindexing can hide schema
mistakes that should be visible before a simulated backtest starts.

## 6. Timing Contract

The future integration must keep these dates distinct:

| Date | Meaning |
| --- | --- |
| Liquidity observation date | Date of OHLCV rows used to compute liquidity metrics. |
| Eligibility date | Date when a lagged liquidity rule first says a symbol is eligible. |
| Universe date | Date attached to the final universe mask after all universe gates. |
| Signal date | Date a factor score is computed and optionally masked by the universe. |
| Rebalance date | Date the simulated backtester forms target weights using lagged signals. |
| Return measurement date | Date of returns earned by previous holdings. |

Default future contract:

```text
masked_signal[t] = raw_signal[t] if universe_mask[t] is True, else missing
```

Then the existing backtester lag applies:

```text
rebalance on date t uses masked_signal[t - signal_lag_periods]
```

With the current default `signal_lag_periods=1`, a factor score and universe
mask stamped at date `t` can first affect a rebalance on the next available
price row. Target holdings set on that rebalance date affect returns starting
on the following price row, consistent with the existing backtester contract.

Any same-day use of a universe mask or signal would require a separate
reviewed execution assumption and tests.

## 7. Selection And Coverage Semantics

Future backtest consumption should follow these rules:

- Ineligible assets have missing masked signals, not zero scores.
- The existing long-only selector ranks only non-missing masked signals.
- If no eligible assets with valid signals exist on a rebalance date, target
  weights should remain all zero for that rebalance, and the event should be
  visible in the audit summary.
- If fewer eligible assets exist than `top_n`, the selector should choose the
  available eligible assets and record the low-coverage condition.
- Universe additions and removals are not portfolio turnover. They are
  universe membership changes that may later cause portfolio turnover after
  the signal and rebalance rules are applied.
- `top_n` and `top_pct` remain ranking/selection parameters, not liquidity
  thresholds.

## 8. Backtest Assumption Additions

Any future synthetic backtest that consumes a liquidity universe mask should
record at least:

| Field | Purpose |
| --- | --- |
| `universe_name` | Stable universe-mask identifier. |
| `universe_mask_source` | Function or workflow that produced the mask. |
| `universe_mask_parameters` | Window, thresholds, lag, cap, and low-coverage parameters. |
| `universe_mask_coverage` | Fraction of date-asset cells eligible after the mask. |
| `masked_signal_coverage` | Fraction of date-asset cells with non-missing masked signals. |
| `low_coverage_dates` | Dates below the configured minimum universe count. |
| `empty_rebalance_dates` | Rebalance dates with no eligible scored assets. |
| `universe_signal_timing` | Statement that mask and signal timestamps are lagged before rebalance use. |
| `not_real_data_evidence` | Explicit caveat when synthetic or fixture data is used. |

These fields should supplement, not replace, existing backtest assumptions such
as transaction costs, signal lag, missing-price policy, benchmark policy,
execution timing, turnover model, long-only constraint, and leverage policy.

## 9. Required Future Tests

Future implementation tests should cover:

- strict index and column alignment between signals and universe mask.
- rejection of unsorted or duplicate dates.
- rejection of non-boolean universe masks.
- missing signal values remaining missing after masking.
- ineligible signal values becoming missing, not zero.
- no forward-fill, backward-fill, zero-fill, interpolation, or silent
  coercion.
- no look-ahead: changing a future universe-mask row cannot alter current
  masked signals or current rebalance selection.
- `signal_lag_periods=1` using the prior masked signal row for a current
  rebalance.
- low-coverage and empty-rebalance dates remaining visible.
- `top_n` behavior when fewer eligible scored assets are available than
  requested.
- no imports from data download libraries, credential paths, broker modules,
  order systems, or LEAN runtime modules.

## 10. Suggested Next Stages

1. Implement a small `apply_universe_mask_to_signals()` adapter with
   deterministic synthetic tests only.
2. Add a synthetic adapter smoke test that proves masked signals are what the
   existing backtester would consume, without running a backtest if that keeps
   the PR narrower.
3. Add a separate synthetic backtest smoke PR that passes masked signals into
   `run_long_only_backtest()` with explicit caveats and generated outputs.
4. Only after synthetic stages are reviewed, consider a local CSV fixture
   workflow update that remains committed-fixture-only and still avoids real
   data interpretation.
5. Keep user-provided local CSV interpretation gated by the real-data
   readiness audit and experiment-log requirements.

Stop any future stage if it requires real data, downloads, vendor credentials,
live or paper trading, brokerage integration, order execution, or
profitability claims.
