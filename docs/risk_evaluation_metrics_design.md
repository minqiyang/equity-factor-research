# Risk And Evaluation Metrics Design

Status: Stages 1 through 3 implemented; Stage 4 episode metrics are designed
for a separate implementation checkpoint.

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
implemented Stage 2 contract and remains the authority for future maintenance.

### Contract Decision

The implementation exposes the metric as `tracking_error` in the
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

The implementation uses two explicit `pandas.Series` inputs with the same return
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

The implementation is limited to daily close-to-close observations:

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

The implementation uses these contextual error messages:

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
invalid. The implementation validates before subtracting the series or
returning a metric.

### Output And Metadata Contract

The metric key is exactly `tracking_error`. It is a non-negative annualized
decimal volatility. When no explicit benchmark-return series is supplied,
existing callers retain their current metric dictionary and do not receive a
placeholder value.

The integration records these audit fields alongside the metric:

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

The implementation refreshes affected reports, JSON experiment logs, and the
experiment registry because their serialized metric dictionaries change, and
records the contract metadata in every affected output. Generated evidence
remains explicitly synthetic or committed-fixture diagnostic evidence.

### Implemented Stage 2 Tests

Focused deterministic tests cover:

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
- no changes to holdings, gross returns, net returns, turnover, or cost
  calculations from adding the metric.

## Deferred Metrics

### Hit Rate

Deferred. "Positive return dates" is not an acceptable substitute for trade or
holding-episode hit rate. The current engine does not identify complete entry,
partial resize, exit, and re-entry episodes.

### Average Holding-Period Return

Implemented only after the Stage 4 contract below. Daily positive-return
frequency is not a substitute.

## Stage 3: Long-Only Position-Cap Constraint

The implemented first constraint is deliberately narrow: an optional
per-position maximum applied to already-selected long-only target weights. It
is a simulated portfolio-construction control, not a production risk system.
Sector, factor, beta, volatility, liquidity, and tracking-error limits remain
out of scope.

### Ordering And Accounting

The cap applies after signal lag, ranking, eligibility, and equal-weight target
construction, but before drift-aware trade and turnover calculation:

```text
lagged signals -> rank/select -> unconstrained targets -> position cap
-> constrained targets -> trades -> turnover -> costs -> returns
```

Liquidity-universe filtering remains an upstream eligibility decision and is
not repeated in the constraint helper. Turnover and every cost component must
be calculated from constrained targets versus drifted pre-trade holdings. The
constraint must not modify signals, asset returns, benchmark returns, or prior
holdings.

### Clip, Renormalization, Cash, And Infeasibility

For each target row and asset:

```text
constrained_weight[i, t] = min(target_weight[i, t], max_position_weight)
cash_weight[t] = 1 - sum(constrained_weight[:, t])
```

Valid targets are clipped, not rejected merely for exceeding the cap. Clipped
weight is not redistributed or renormalized, because renormalization can
silently breach the cap or change the selected portfolio. Residual weight is
explicit non-interest-bearing cash under the existing backtest contract.

An infeasible fully invested target is therefore valid and holds cash. For
example, two 50% targets with a 30% cap become two 30% positions and 40% cash.
The helper must not add unselected assets to manufacture full investment.

Warm-up and no-selection rows remain all-zero targets and therefore 100% cash.
A cap of `1.0` is a behavioral no-op. The cap must satisfy
`0 < max_position_weight <= 1`; there is no disabled sentinel inside the
helper. Backtester integration uses `None` to mean the optional constraint is
not requested, preserving existing behavior and output keys.

### Validation And Errors

Target weights must be a non-empty numeric `DataFrame` with a unique,
increasing `DatetimeIndex`, unique asset columns, finite non-missing
non-negative values, and row sums no greater than `1` within the existing
gross-exposure tolerance. Boolean, complex, and object values are invalid.

Required message fragments:

| Invalid condition | Required message fragment |
| --- | --- |
| Wrong target type | `target_weights must be a pandas DataFrame` |
| Invalid axis | `target_weights must have unique assets and unique, increasing dates` |
| Invalid values | `target_weights must contain finite non-negative real weights` |
| Leveraged row | `target_weights gross exposure must not exceed 1` |
| Invalid cap | `max_position_weight must be greater than 0 and no greater than 1` |

Validation happens before clipping. The helper must return a new DataFrame and
must not mutate caller-owned targets.

### Audit Contract

When the optional cap is active, `BacktestResult.assumptions` records:

```text
position_constraint_contract = "long_only_position_cap_v1"
max_position_weight = <configured decimal>
position_constraint_order = "after_selection_before_trade_calculation"
position_constraint_breach_policy = "clip"
position_constraint_renormalization = "none"
position_constraint_residual_weight = "non_interest_bearing_cash"
position_constraint_infeasible_target_policy = "clip_and_hold_cash"
```

No constraint audit fields are emitted when the option is `None`. Descriptive
holdings metrics remain in `src/backtest/metrics.py`; implementation behavior
belongs in `src/risk/constraints.py` and integration in the backtester.

### Required Stage 3 Implementation Tests

- hand-calculated clipping and residual cash;
- no redistribution to uncapped or unselected assets;
- all-zero warm-up and no-selection rows remain zero;
- cap `1.0` is a no-op and input targets are not mutated;
- invalid types, axes, values, leverage, and cap values fail explicitly;
- constrained targets drive trades, turnover, costs, holdings, and returns;
- a partial-cash portfolio drifts correctly without earning cash interest;
- optional-input compatibility preserves exact existing behavior and metadata;
- constraint metadata is emitted only when active;
- liquidity filtering remains upstream and benchmark/tracking-error accounting
  is unchanged except through the constrained strategy return path.

## Stage 4: Holding-Episode Metrics

The first episode implementation adds only `episode_hit_rate` and
`average_holding_period_return`. It uses completed long-only asset episodes
from the simulated backtest. It does not infer trades, fills, tax lots, or
round trips from daily portfolio returns.

### Required Attribution Inputs

Episode attribution requires exact-date inputs. Matrix inputs have identical
indexes and asset columns; series inputs share that index:

| Input | Meaning |
| --- | --- |
| `holdings` | Post-trade closing weights. |
| `asset_returns` | Close-to-close asset returns; row `t` is earned by holdings from the prior close. |
| `signed_trade_weights` | Constrained target weight minus drifted pre-trade weight. Positive values deploy capital; negative values withdraw capital. |
| `trade_weights` | Absolute signed trade weights, retained as an accounting cross-check. |
| `turnover` | Row sum of absolute signed trade weights. |
| `total_trading_costs` | Applied portfolio-return impact from transaction costs, fixed slippage, and applied volume-aware impact. |

The implementation must expose `signed_trade_weights` from the existing
drift-aware path rather than reconstructing trade direction from closing
holdings. For every date and asset,
`abs(signed_trade_weights) == trade_weights`; row sums of absolute signed trades
must equal turnover. This is accounting evidence, not a new trading model.

### Episode Boundaries

An episode is one uninterrupted run of strictly positive post-trade closing
weight for one asset:

- entry: weight changes from zero at the prior close to positive after the
  current close's trade;
- continuation: post-trade weight remains positive, including drift and any
  increase or partial reduction;
- exit: prior-close weight is positive and post-trade closing weight is zero,
  whether from a full sale or a total asset loss during the return window;
- re-entry: a later zero-to-positive transition starts a new episode;
- a same-close sell and buy cannot be observed separately in daily aggregate
  targets and therefore remains one episode when closing weight stays positive.

The entry row contributes its entry cost but no asset return because the new
holding starts after that row's close-to-close window. The exit row contributes
the final asset return earned by the prior-close holding and the exit cost.

An episode still positive on the terminal row is open and excluded from both
metrics. It is never forced closed at an invented price. The assumptions
record closed and terminal-open episode counts so omitted observations remain
visible. If there are no completed episodes, both metrics are `NaN`.

### Return And Hit Definitions

For each completed episode `e`:

```text
gross_contribution[e] = sum(prior_close_weight[i, t] * asset_return[i, t])
deployed_weight[e] = sum(max(signed_trade_weight[i, t], 0))
net_contribution[e] = gross_contribution[e] - allocated_trading_cost[e]
episode_return[e] = net_contribution[e] / deployed_weight[e]
```

`deployed_weight` includes entry and later increases, but not drift or partial
sales. It must be positive for every completed episode. This definition is a
net simulated return on cumulatively deployed portfolio weight; it is not an
asset buy-and-hold return, IRR, tax-lot return, or compounded portfolio return.

Required aggregate metrics:

```text
episode_hit_rate = mean(episode_return > 0)
average_holding_period_return = mean(episode_return)
```

Zero-return episodes are not hits. Every completed episode receives equal
weight in both aggregates; there is no capital-weighting or duration-weighting.

### Cost Attribution

Applied cost on date `t` is allocated across assets in proportion to absolute
signed trade weight:

```text
asset_cost[i, t] = total_trading_costs[t] * (
    abs(signed_trade_weight[i, t]) / turnover[t]
)
```

When turnover is zero, total applied cost must also be zero and every asset
cost is zero. Entry, increase, reduction, and exit costs belong to the episode
active immediately before or after that trade. The allocation exactly
reconciles to `total_trading_costs` on every date. For nonlinear precomputed
volume impact this is an explicit accounting allocation, not a claim that each
asset caused a proportional amount of market impact.

Diagnostic-only slippage is excluded because it is not in
`total_trading_costs`. Benchmark costs are never attributed to strategy
episodes. Results with zero transaction costs or slippage remain diagnostics
under the existing project policy.

### Validation, Output, And Audit Fields

All inputs must be non-empty real numeric data with unique increasing
`DatetimeIndex` values, finite values, and exact date alignment. Matrices also
require unique, exactly aligned asset columns. Holdings and absolute trades are
non-negative; holdings gross exposure cannot exceed one. Signed trades may be
negative. Returns may be negative but must not be below `-1` for any
prior-close held asset.

The implementation rejects accounting mismatches before attribution, including
absolute/signed trade disagreement, turnover disagreement, nonzero cost with
zero turnover, or daily allocated costs that do not reconcile. It does not
fill, intersect, reorder, threshold, or infer missing data.

Metrics are optional: callers without the complete attribution inputs retain
their existing metric dictionary. When active, assumptions record:

```text
holding_episode_contract = "continuous_positive_weight_v1"
holding_episode_return_basis = "net_contribution_over_cumulative_deployed_weight"
holding_episode_cost_allocation = "pro_rata_absolute_signed_trade_weight"
holding_episode_resize_policy = "continue_episode"
holding_episode_reentry_policy = "new_after_zero_close"
holding_episode_terminal_policy = "exclude_open"
holding_episode_zero_return_hit_policy = "not_a_hit"
holding_episode_aggregation = "equal_weight_completed_episodes"
holding_episode_closed_count = <integer>
holding_episode_terminal_open_count = <integer>
```

### Required Stage 4 Implementation Tests

- one hand-calculated entry, return, and exit episode with entry/exit costs;
- multiple assets proving equal episode weighting and exact daily cost
  reconciliation;
- partial increase and reduction continue the episode while positive increases
  add to deployed weight;
- a zero close followed by re-entry creates two episodes;
- a total asset loss closes an episode without inventing an exit trade;
- zero-return completed episodes are not hits;
- terminal-open episodes are counted but excluded from both metrics;
- no completed episodes return `NaN` metrics;
- position-cap cash does not create an episode and earns no return;
- applied volume-aware cost is included while diagnostic-only impact is not;
- malformed axes, values, return windows, and accounting identities fail;
- optional-input compatibility preserves all existing metrics and backtest
  paths when episode attribution is not requested.

## PR Sequence

| PR | Scope | Stop condition |
| --- | --- | --- |
| A | Completed: risk/evaluation design, including the holdings-state and tracking-error contracts. | Stop if a metric remains semantically ambiguous. |
| B | Completed: implement holdings-state helpers and backtester integration. | Stop on accounting changes or unstable generated outputs. |
| C | Completed: implement tracking error under the approved daily close-to-close contract with benchmark-alignment tests. | Stop if benchmark returns cannot be reconstructed unambiguously. |
| D | Completed: long-only position-cap constraint design. | Stop before code until the design PR is accepted. |
| D2 | Completed: implement the approved optional position cap. | Stop on implicit renormalization, altered selection, or accounting drift. |
| E | Completed: holding-episode boundaries, return basis, cost allocation, terminal policy, audit fields, and tests. | Stop before presenting daily win rate as trade hit rate. |
| E2 | Next: expose signed trades and implement only the approved episode metrics. | Stop on cost non-reconciliation or invented terminal exits. |

Every code PR requires focused tests, full tests, Ruff, compilation, package
build, current-head Codex review, and normal merge.
