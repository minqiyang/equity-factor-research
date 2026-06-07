# Liquidity Universe Construction Design

Date: 2026-06-07

This is a documentation-only design for a future liquidity-based universe
construction boundary.

It does not modify source code, tests, research scripts, generated reports,
loaders, backtester behavior, metrics, strategy logic, data access, execution
assumptions, or performance claims. It does not fetch data, download data, add
vendor APIs, add credentials, add live trading, add paper trading, add
brokerage integration, add order execution, or claim profitability.

## 1. Purpose

The repository already has synthetic-only rolling ADV and rolling dollar-volume
eligibility helpers. Those helpers answer whether an asset is liquid enough on
a date under a reviewed lag rule.

They do not yet define the first actual research universe mask API, the audit
summary that should accompany that mask, or the boundary between liquidity
eligibility, factor scoring, portfolio construction, and backtesting.

This design fills that gap before any backtest or workflow uses liquidity
eligibility as a tradable universe.

## 2. Current Evidence

| Area | Evidence | Current status |
| --- | --- | --- |
| Strict OHLCV validation | `src/data/csv_loader.py`, `tests/test_csv_loader.py` | Implemented for local files and committed synthetic fixtures. |
| Liquidity metrics | `rolling_average_daily_volume()` and `rolling_average_dollar_volume()` | Implemented with full rolling windows and no missing-value fill. |
| Liquidity eligibility | `average_daily_volume_eligibility()` and `average_dollar_volume_eligibility()` | Implemented as lagged boolean masks with strict default zero-volume behavior. |
| Fixture smoke coverage | `research/local_csv_fixture_workflow_demo.py`, reports and tests | Counts liquidity eligibility on committed synthetic fixtures only. |
| Backtester | `src/backtest/portfolio.py` | Does not yet consume liquidity universe masks. |

The current state is useful infrastructure. It does not prove market
tradability, strategy performance, or real-data readiness.

## 3. Non-Goals

- No source-code implementation.
- No changes to `src/features/liquidity.py`.
- No changes to `src/backtest/portfolio.py`, metrics, normalization,
  combination, diagnostics, alpha files, CSV loaders, research scripts, tests,
  or reports.
- No user-provided or real-market data.
- No downloads, vendor APIs, `requests`, `yfinance`, Alpaca, CCXT, or
  credential logic.
- No live trading, paper trading, brokerage integration, order execution, or
  account handling.
- No portfolio construction, signal weighting, position sizing, slippage
  model, benchmark interpretation, LEAN runtime behavior, or strategy result.
- No automatic forward-fill, backward-fill, zero-fill, interpolation, or
  liquidity repair.
- No profitability, investment-performance, robustness, or trading-readiness
  claim.

## 4. Timing Definitions

Future code should keep the following dates distinct:

| Date | Meaning |
| --- | --- |
| Observation date | Date of OHLCV rows used to compute liquidity metrics. |
| Eligibility date | Date when a lagged liquidity rule says a symbol is eligible. |
| Universe date | Date attached to the final universe mask after all universe gates are applied. |
| Signal date | Date a factor score is computed after universe membership is known. |
| Rebalance date | Date a simulated portfolio would form target holdings after signals are known. |
| Execution date | Date simulated trades are assumed to execute under an explicit backtest assumption. |

Default design assumption:

```text
Liquidity observed through date t may first affect universe membership on
date t + eligibility_lag.
```

Any future same-day universe assumption must be separately documented and
tested. The default should remain a positive lag.

## 5. Proposed Future API Boundary

A future implementation PR should add one narrow helper rather than wiring
liquidity directly into a backtest.

Possible shape:

```text
construct_liquidity_universe(
    eligibility_mask: pandas.DataFrame,
    *,
    ranking_metric: pandas.DataFrame | None = None,
    max_assets_per_date: int | None = None,
    min_assets_per_date: int = 1,
    name: str = "liquidity_universe",
) -> LiquidityUniverseResult
```

Where:

- `eligibility_mask` is a boolean date-asset panel produced by reviewed
  eligibility helpers.
- `ranking_metric` is optional and must already be aligned to
  `eligibility_mask`; if supplied, it may be used only to cap the universe by
  liquidity rank, not by future returns or factor outcomes.
- `max_assets_per_date` limits the number of eligible names for research
  tractability, using deterministic tie handling.
- `min_assets_per_date` controls whether low-coverage dates are marked in the
  summary, not whether evidence can be hidden.
- The result includes both the final boolean universe mask and an audit
  summary.

The helper should not import the backtester, metrics, reporting writers,
strategy modules, LEAN files, data loaders, API clients, credential readers, or
execution systems.

## 6. Mask Semantics

Future universe masks should follow these rules:

1. The mask is boolean and aligned by date and asset.
2. Missing eligibility is treated as `False` only after being recorded in the
   audit summary.
3. A symbol can be in the universe on a date only if it is eligible on that
   same universe date after the configured lag.
4. If `ranking_metric` is used, missing ranking values cannot be filled.
5. If `max_assets_per_date` is used, selection must be deterministic and must
   not depend on future returns, realized performance, or later availability.
6. Dates with too few eligible symbols must remain visible in the audit
   summary.
7. Universe construction does not create target weights, trades, positions,
   orders, returns, or benchmark comparisons.

## 7. Audit Summary Contract

A future `LiquidityUniverseResult` should preserve at least:

| Field | Purpose |
| --- | --- |
| `name` | Stable identifier for the universe rule. |
| `start_date` and `end_date` | Date span covered by the mask. |
| `asset_count` | Number of unique symbols considered. |
| `universe_count_by_date` | Final eligible count per date. |
| `raw_eligible_count_by_date` | Count before any optional cap. |
| `missing_eligibility_count_by_date` | Missing or unavailable eligibility observations. |
| `missing_ranking_count_by_date` | Missing liquidity rank inputs, if a ranking metric is used. |
| `capped_count_by_date` | Number removed by `max_assets_per_date`, if used. |
| `added_count_by_date` and `removed_count_by_date` | Turnover-like universe membership changes, not portfolio turnover. |
| `low_coverage_dates` | Dates below `min_assets_per_date`. |
| `parameters` | Window, thresholds, lag, price field, volume policy, and zero-volume policy inherited from eligibility inputs. |
| `caveats` | Explicit no-real-data, no-backtest, no-trading, no-profitability caveats. |

The summary should be inspectable in tests without writing a report.

## 8. Alignment With Current Modules

| Module | Future interaction |
| --- | --- |
| `src/features/liquidity.py` | Produces eligibility masks and possibly ranking metrics; remains synthetic/local-panel only. |
| `src/features/worldquant_alphas.py` | May receive factor panels that are later masked, but alpha helpers should not construct universes. |
| `src/features/diagnostics.py` | May use universe-masked factor/return panels in a later diagnostics stage; diagnostics remain evaluation-only. |
| `src/backtest/portfolio.py` | Should not consume liquidity masks until a separate reviewed stage defines signal, universe, and execution timing together. |
| `research/local_csv_fixture_workflow_demo.py` | May later report universe-mask counts on committed synthetic fixtures, still without backtesting or interpretation. |
| `docs/real_data_readiness_audit.md` | Must remain the gate before any user-provided local CSV universe result is interpreted. |

## 9. Required Future Tests

Future implementation tests should cover:

- exact index and column preservation.
- boolean mask output.
- rejection of non-boolean eligibility input.
- rejection of mismatched ranking-metric indexes or columns.
- no look-ahead from future eligibility or ranking values.
- missing eligibility recorded and excluded by default.
- missing ranking values recorded and excluded when a rank cap is used.
- deterministic cap behavior and tie handling.
- warm-up dates and low-coverage dates remaining visible.
- `max_assets_per_date` and `min_assets_per_date` validation.
- no forward-fill, backward-fill, zero-fill, interpolation, or silent coercion.
- no imports from backtester, reporting writers, data download libraries,
  credential paths, broker modules, order systems, or LEAN runtime modules.

## 10. Risks

- Survivorship bias from static modern symbol lists.
- Universe membership accidentally using future liquidity observations.
- Vendor differences in volume, adjusted volume, corporate actions, and stale
  rows.
- Liquidity rank caps turning into hidden parameter tuning.
- Low-coverage dates being silently dropped.
- Treating universe count stability as evidence that a strategy works.
- Connecting liquidity eligibility directly to portfolio construction before
  signal, rebalance, and execution timing are reviewed together.

## 11. Recommended Next Stages

1. Implement a small `LiquidityUniverseResult` and
   `construct_liquidity_universe()` helper using synthetic panels only.
2. Add deterministic tests for mask semantics, summary fields, cap behavior,
   missing values, low coverage, and no-lookahead.
3. Add a local synthetic fixture workflow smoke update that reports universe
   mask counts only, without backtesting or performance interpretation.
4. Only after those stages, consider a separate backtester integration design
   that defines how a universe mask, factor score, rebalance schedule, costs,
   slippage, benchmark, and execution lag interact.

Stop any future stage if it requires real data, downloads, vendor credentials,
live or paper trading, brokerage integration, order execution, or
profitability claims.
