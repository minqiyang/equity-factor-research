# Risk And Evaluation Metrics Design

Status: approved for staged implementation.

This document defines the next metric work after the PR #144 release baseline.
It covers simulated research diagnostics only. It does not define investment,
execution, production risk, or trading-readiness claims.

## Decision

Implement metrics in four separate stages:

1. Holdings-state metrics.
2. Benchmark-relative tracking error.
3. Constraint design before constraint code.
4. Holding-episode metrics only after position episodes can be attributed.

The first code PR must implement only holdings-state metrics. It must not modify
portfolio selection, target weights, trades, costs, or returns.

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

Tracking error requires an exact benchmark-return contract and therefore stays
outside Stage 1.

Candidate definition:

```text
active_return[t] = strategy_net_return[t] - benchmark_return[t]
tracking_error = std(active_return, ddof=0) * sqrt(periods_per_year)
```

Before implementation, the PR must decide whether the synthetic first row is
included, require exact index and timezone alignment, reject missing values,
and record that strategy returns are net of applied research costs while the
benchmark is cost-free unless explicitly modeled.

Do not calculate tracking error from the difference between two annualized
returns. Tracking error is the volatility of the active-return series.

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
| A | This design and test contract. | Stop if a metric remains semantically ambiguous. |
| B | Implement holdings-state helpers and backtester integration. | Stop on accounting changes or unstable generated outputs. |
| C | Design and implement tracking error with benchmark alignment tests. | Stop if benchmark returns cannot be reconstructed unambiguously. |
| D | Constraint design only. | Stop before code until reject/clip/renormalize policy is approved. |
| E | Episode model design, only if hit-rate or holding-period metrics are still needed. | Stop before presenting daily win rate as trade hit rate. |

Every code PR requires focused tests, full tests, Ruff, compilation, package
build, current-head Codex review, and normal merge.
