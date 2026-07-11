# Risk And Evaluation Metrics Design

Status: Stage 1 implemented; Stage 2 design complete; Stage 2 implementation
is next.

This document defines the next metric work after the PR #144 release baseline.
It covers simulated research diagnostics only. It does not define investment,
execution, production risk, or trading-readiness claims.

## Decision

Implement metrics in four separate stages:

1. Holdings-state metrics.
2. Benchmark-relative tracking error.
3. Constraint design before constraint code.
4. Holding-episode metrics only after position episodes can be attributed.

The Stage 1 code PR implemented only holdings-state metrics and did not modify
portfolio selection, target weights, trades, costs, or returns. The Stage 2 code
PR must implement only the tracking-error contract below.

## Stage 1: Holdings-State Metrics

Input: `BacktestResult.holdings` at each close.

On rebalance dates, holdings are post-trade closing weights. On other dates,
they are drifted closing weights. These metrics describe closing portfolio
state snapshots; they are not intraday, pre-trade, or return-attribution
metrics.

Every active closing row is included, including the terminal row. The final
row may not earn a later observed return, but it is still a portfolio state
constructed by the simulation. A terminal rebalance can therefore change the
average holding count and concentration metrics. Return-exposure metrics, if
added later, must use a separately aligned prior-holdings contract.

For date `t` and asset `i`:

```text
gross_exposure[t] = sum(weight[i, t])
active[t] = gross_exposure[t] > 0
holding_count[t] = sum(weight[i, t] > 0)
normalized_weight[i, t] = weight[i, t] / gross_exposure[t]
concentration_hhi[t] = sum(normalized_weight[i, t] ** 2)
```

Required outputs:

| Metric | Definition |
| --- | --- |
| `average_holding_count` | Mean `holding_count` over active dates. |
| `average_position_concentration_hhi` | Mean normalized HHI over active dates. |
| `max_position_concentration_hhi` | Maximum normalized HHI over active dates. |

All-zero warm-up dates are excluded. If no active date exists, all three
metrics return `NaN` rather than zero. A zero would incorrectly claim a
measured unconcentrated portfolio.

Strictly positive weights count as holdings. The metric layer must not hide
floating-point dust with an undocumented threshold; upstream portfolio code is
responsible for producing explicit zero weights.

HHI is normalized by gross exposure so concentration is comparable if a later
research path holds cash. For an equal-weight portfolio with `n` positions,
HHI is `1 / n`; a single-position portfolio has HHI `1`.

### Validation

Holdings must be a non-empty numeric DataFrame with:

- a unique, increasing DatetimeIndex;
- unique asset columns;
- finite, non-missing, non-negative weights;
- gross exposure no greater than `1` within a documented numerical tolerance.

Invalid holdings raise before metrics are returned. Existing callers that do
not supply holdings remain backward-compatible and do not receive the new
keys.

### Required Tests

- Hand-calculated equal-weight and concentrated rows.
- A partial-cash row such as `[0.25, 0.25, 0.0]` proves gross normalization:
  normalized HHI is `0.5`, not raw squared-weight sum `0.125`.
- Warm-up rows excluded from active-date averages.
- Drifted non-rebalance holdings included.
- A terminal rebalance row is included as a closing state snapshot even though
  it has no subsequent observed return row.
- All-zero holdings return `NaN` for the three metrics.
- Missing, infinite, negative, duplicate, unsorted, non-numeric, and leveraged
  holdings fail explicitly.
- Optional-input compatibility preserves the existing metric dictionary.
- Backtester integration passes its closing holdings without changing returns,
  equity, turnover, or costs.
- Generated synthetic logs are refreshed only if their serialized metric
  dictionaries change.

## Stage 2: Tracking Error

Tracking error requires an exact benchmark-return contract. This section is the
approved Stage 2 design; it does not add a metric implementation or generated
evidence.

### Contract Decision

The future implementation will expose the metric as `tracking_error` in the
existing simulated-metrics dictionary only when an explicit benchmark-return
series is supplied. It will not reconstruct tracking error from
`benchmark_equity_curve` alone, because an equity curve does not preserve the
return-window and cost-basis decision required by this contract.

For the full aligned return series, including the synthetic first row:

```text
active_return[t] = strategy_net_return[t] - benchmark_return[t]
measured_active_return = active_return.iloc[1:]
tracking_error = std(measured_active_return, ddof=0) * sqrt(252)
```

Tracking error is the annualized population standard deviation of active
close-to-close returns. It is never the difference between strategy and
benchmark annualized returns.

### Return Series And Cost Basis

The code PR must use two explicit `pandas.Series` inputs with the same return
index:

| Input | Contract |
| --- | --- |
| `strategy_returns` | The backtest's net close-to-close return series, equivalent to `BacktestResult.returns`; it is not `gross_returns`. Each measured return is after every trading-cost component actually applied to the strategy, including transaction costs, fixed slippage, and applied precomputed volume-aware impact. Diagnostic-only costs are not included. |
| `benchmark_returns` | A cost-free close-to-close price return series for the selected benchmark over the same return windows. It is not a total-return comparison derived by subtracting two equity-curve totals. |

The return construction is explicit:

```text
strategy_net_return[t] = gross_return[t] - applied_trading_cost_impact[t]
benchmark_return[t] = benchmark_price[t] / benchmark_price[t - 1] - 1
```

The benchmark series may contain only its one synthetic first-row anchor at
zero; no other missing or non-finite price-to-return conversion is filled.

Benchmark transaction costs, benchmark slippage, and benchmark impact are zero
under this Stage 2 contract. They must not be inferred from strategy costs or
silently copied from the strategy. A future explicit benchmark-cost model is a
separate design and cannot be introduced in the implementation PR.

The return basis is recorded as
`strategy_net_after_applied_costs_vs_cost_free_benchmark`. The strategy and
benchmark series are return observations, not holdings snapshots. The
`initial_capital` and normalized portfolio notional do not change tracking
error.

### Index, Timezone, And Frequency Alignment

The first implementation is limited to daily close-to-close observations:

- both inputs are non-empty real numeric `Series` objects;
- both use unique, increasing `DatetimeIndex` values;
- both indexes have the same timezone metadata; naive and timezone-aware
  indexes do not mix, and no implicit timezone conversion is performed;
- indexes must be exactly equal in values and order, including the terminal
  date; extra, missing, reordered, or intersected dates are rejected;
- `return_frequency` is a required explicit input/metadata value and must be
  `daily_close_to_close`; `periods_per_year` is fixed at `252`. Frequency is
  not inferred from `DatetimeIndex.freq` and no resampling, union,
  intersection, forward-fill, or calendar conversion is allowed.

Weekly, monthly, intraday, irregular-observation, and mixed-frequency tracking
error require a separate reviewed contract. Weekend and holiday gaps are
allowed as ordinary gaps in a daily trading-session index when both series
share the exact same dates.

### First-Row And Terminal-Window Semantics

The first aligned row is the synthetic price-return anchor: it has no prior
observed close and is not a realized close-to-close window. It is excluded from
`measured_active_return` for both series. This prevents the conventional
zero-return anchor from diluting volatility and makes the measured sample a
set of actual return windows. The anchor row is not silently redistributed;
any cost recorded on an initial execution remains visible in the backtest's
total-return and cost metrics but is outside this close-to-close volatility
window by definition.

The final aligned row is included because it is the endpoint of the last
observed close-to-close window. A terminal rebalance does not create a future
return, but any cost applied on that terminal row is part of the strategy net
return for the preceding-to-terminal window. No holdings snapshot after the
terminal row is manufactured.

At least two measured return windows are required. A one-window sample would
produce a mechanically zero population standard deviation without providing a
meaningful volatility diagnostic.

### Missing Values, Validation, And Errors

Missing-data policy is `raise` only. The metric must reject missing or
non-finite strategy or benchmark returns; it must not fill, freeze, or convert
missing values to zero. A backtest that used
`benchmark_missing_policy="zero_return"` is not eligible for this metric
unless a future design explicitly records and approves the imputation policy.

The implementation must use these contextual error messages:

| Invalid condition | Required message or message fragment |
| --- | --- |
| Wrong input type | ``strategy_returns must be a pandas Series`` or ``benchmark_returns must be a pandas Series`` |
| Non-datetime index | ``<name> must be indexed by a pandas DatetimeIndex`` |
| Duplicate dates | ``<name> index must not contain duplicate dates`` |
| Unsorted dates | ``<name> index must be sorted in increasing date order`` |
| Timezone mismatch | ``strategy_returns and benchmark_returns must have matching timezones`` |
| Date/index mismatch | ``strategy_returns and benchmark_returns must have identical indexes`` |
| Missing or infinite values | ``tracking error does not support missing or non-finite returns`` |
| Unsupported frequency | ``tracking error supports daily_close_to_close only`` |
| Too few measured windows | ``tracking error requires at least 2 measured return periods`` |

Boolean, complex, object, and otherwise non-real numeric return columns are
invalid. The implementation must validate before subtracting the series or
returning a metric.

### Output And Metadata Contract

The metric key is exactly `tracking_error`. It is a non-negative annualized
decimal volatility. When no explicit benchmark-return series is supplied,
existing callers retain their current metric dictionary and do not receive a
placeholder value.

The future integration must record these audit fields alongside the metric:

```text
tracking_error_contract = "daily_close_to_close_v1"
tracking_error_return_basis = "strategy_net_after_applied_costs_vs_cost_free_benchmark"
tracking_error_frequency = "daily_close_to_close"
tracking_error_periods_per_year = 252
tracking_error_ddof = 0
tracking_error_first_row_policy = "exclude_synthetic_anchor"
tracking_error_missing_policy = "raise"
tracking_error_terminal_row_policy = "include_terminal_close_to_close_window"
benchmark_cost_basis = "cost_free_price_return"
```

This design PR does not refresh reports, JSON experiment logs, registries, or
hashes because no metric output exists yet. The later implementation PR must
add deterministic synthetic tests first, refresh generated artifacts only if
the serialized metric dictionaries change, and record the contract metadata in
every affected output. Generated evidence must remain explicitly synthetic or
committed-fixture diagnostic evidence.

### Required Stage 2 Tests Before Implementation

The implementation PR must add focused deterministic tests for:

- a hand-calculated active-return series proving population `ddof=0`, annual
  multiplication by `sqrt(252)`, and the exact `tracking_error` name;
- a changed synthetic first-row value not changing the result, proving the
  anchor is excluded;
- a changed terminal return changing the result, proving the last observed
  close-to-close window is included;
- strategy and benchmark net-return basis, including applied strategy cost
  impact and a cost-free benchmark that is not charged strategy costs;
- exact matching daily indexes, including the terminal date and allowed
  weekend/holiday gaps;
- duplicate, unsorted, missing, extra, reordered, naive-versus-aware, and
  different-timezone indexes failing explicitly;
- `NaN`, positive/negative infinity, boolean, complex, object, and empty input
  failures;
- missing benchmark data failing rather than using the backtest's diagnostic
  zero-return fallback;
- fewer than two measured windows failing;
- rejection of weekly, monthly, intraday, or mixed-frequency inputs;
- a regression proving tracking error is not computed from the difference of
  two annualized returns;
- no changes to holdings, gross returns, net returns, turnover, costs, or
  generated artifacts in the design-only stage.

## Deferred Metrics

### Hit Rate

Deferred. "Positive return dates" is not an acceptable substitute for trade or
holding-episode hit rate. The current engine does not identify complete entry,
partial resize, exit, and re-entry episodes.

### Average Holding-Period Return

Deferred for the same reason. Partial rebalances and drift require an explicit
lot or episode attribution policy and a reviewed allocation of costs.

### Portfolio Constraints

Deferred to a design PR. `src/risk/constraints.py` must remain a placeholder
until the project defines:

- whether constraints apply before or after ranking;
- reject, clip, or renormalize behavior;
- cash treatment;
- infeasible-target behavior;
- audit fields and failure messages;
- interaction with liquidity and turnover.

Descriptive holdings metrics belong in `src/backtest/metrics.py`, not in the
constraint placeholder.

## PR Sequence

| PR | Scope | Stop condition |
| --- | --- | --- |
| A | Completed: risk/evaluation design, including the holdings-state and tracking-error contracts. | Stop if a metric remains semantically ambiguous. |
| B | Completed: implement holdings-state helpers and backtester integration. | Stop on accounting changes or unstable generated outputs. |
| C | Next: implement tracking error under the approved daily close-to-close contract with benchmark-alignment tests. | Stop if benchmark returns cannot be reconstructed unambiguously. |
| D | Constraint design only. | Stop before code until reject/clip/renormalize policy is approved. |
| E | Episode model design, only if hit-rate or holding-period metrics are still needed. | Stop before presenting daily win rate as trade hit rate. |

Every code PR requires focused tests, full tests, Ruff, compilation, package
build, current-head Codex review, and normal merge.
