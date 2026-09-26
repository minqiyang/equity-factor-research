# Signal, Execution, and Metric Timing Contract

Status: accepted Stage 2 design; Stage 2b runtime implementation complete on
protected main via PR #162.

Implementation baseline: protected `main` merge `8a352d3` (PR #162). The
post-merge local baseline has 849 passing tests with two platform-conditional
wide-`longdouble` skips; exact merge-head GitHub CI passed.

This is the normative documentation and methodology target for the current
close-only backtester and deterministic tests. Implementation conformance is
not historical research evidence and does not authorize real-data
interpretation, factor promotion, LEAN execution, paper trading, brokerage
access, orders, or live trading.

## Scope

Stage 2b implementation covers:

- one named after-close signal and next-observed-close execution policy;
- explicit evaluation start and end anchors;
- exact signal, price, benchmark, and metric date alignment;
- required role-bound caller-declared source provenance captured before any
  later mutation;
- a non-boolean integer signal-row lag of at least one;
- decision-time target freezing separated from execution-price feasibility;
- deterministic return, drift, trade, turnover, cost, and holdings ordering;
- one common measured-return window for strategy and benchmark metrics;
- typed global timing metadata and a timing ledger over the initialization
  anchor/resolved-schedule union; and
- deterministic tests for zero lag, warm-up exclusion, terminal handling, and
  mutation invariance.

Stage 2a changed documentation, repo-map index tooling, and
documentation-contract tests only. Stage 2b enforces the contract in runtime
code, direct callers, metrics, serialized synthetic evidence, and behavior
tests, including the homogeneous-complex provenance case stated below.

This contract does not select an exchange calendar, vendor, point-in-time
universe, benchmark security, risk-free series, intraday clock, auction model,
order type, fill model, or empirical promotion threshold.

## Pre-Implementation Baseline and Closed Gaps

The table below records the verified pre-Stage 2b baseline that motivated this
contract. Its line references are historical and do not describe the current
runtime.

| Evidence | Current behavior | Contract consequence |
| --- | --- | --- |
| `src/backtest/portfolio.py:123-129,176-179` | Signals are described as known after their timestamp's close, reindexed to price axes, and shifted by source rows. | The contract must name every event and reject silent axis repair. |
| `src/backtest/portfolio.py:609-610` | Only negative `signal_lag_periods` values are rejected. Zero and Boolean false can reach target construction. | Stage 2b must require a non-boolean integer at least one. |
| `src/backtest/portfolio.py:342-366` | Target membership is ranked after filtering with the execution row's closing-price validity. | Stage 2b must freeze the intended target from decision-time information and treat the execution close only as fill feasibility. |
| `src/backtest/portfolio.py:388-426` | Row return and drift are processed before the row's target, trade, cost, and post-trade holdings. | The current drift-aware accounting order is retained and made explicit. |
| `src/backtest/metrics.py:65-76,238-252` | Tracking error excludes the first row; volatility and Sharpe include it; annualized return assumes one fewer interval. | All period-return metrics must share one explicit measured-date set. |
| `src/backtest/metrics.py:19-35` | Drawdown starts at the first reported equity value rather than the initial-capital base. | Stage 2b must include the initial-capital anchor in drawdown. |
| `research/synthetic_momentum_demo.py:91-109` | Full feature warm-up history is passed into the backtester and its metrics. | Warm-up may feed feature calculation but must not enter the declared evaluation window. |
| `src/backtest/portfolio.py:450-455` | A rebalance period resolves to the last observed row in each pandas bucket, including an incomplete terminal bucket. | The behavior is retained as an observed-row rule and must be disclosed in resolved metadata. |
| `lean/signal_only_momentum_draft.py:39-44` | The LEAN scaffold lacks local decision, execution, return-window, and metric-anchor fields. | Stage 2a and Stage 2b cannot claim LEAN parity. |

Stage 2b closes the untyped same-close loophole, silent alignment,
execution-close target membership, and inconsistent evaluation anchors. It
regenerates only deterministic synthetic implementation evidence; no private
result is opened or reinterpreted.

## Normative Terms

- **Full source index**: the unique, strictly increasing daily-close
  observation index shared by prices and final signals, denoted `s[0..M]`. A
  row denotes one observed session close; it is not automatically a calendar
  day.
- **Feature observation end**: the latest source event used by a feature value.
  Under the generic current API, a final signal stamped at row `t` is
  conservatively treated as depending on `close[t]`, even when a particular
  formula uses older anchors.
- **Signal stamp**: the source row label attached to the final cross-sectional
  score supplied to the backtester.
- **Signal availability**: the first event at which the complete final score is
  knowable. For this contract it is strictly after the signal row's close.
- **Decision time**: the event immediately after signal availability on the
  signal-source row, before any later source-row observation. Ranking,
  selection, constraints, and intended target weights are frozen here and then
  held until a scheduled execution.
- **Execution time**: the close of a later observed source row at which the
  idealized target reset and its costs are recorded.
- **Execution feasibility**: whether a frozen intended target has a finite,
  positive price at the execution close. It is not permission to rerank or
  redistribute the target with information learned at that close.
- **Post-trade holdings**: closing weights immediately after the row's target
  reset. They first earn the next observed close-to-close return.
- **Accounting dates**: the exact contiguous slice of the full source index
  from `evaluation_start` through `evaluation_end`, denoted `a[0..N]`, where
  `a[0]` is the initialization anchor. Feature calculations may read earlier
  full-source history, but signal lag and target generation may use only this
  bounded slice.
- **Initialization anchor**: `evaluation_start`, which establishes initial
  capital and the first price anchor but has no preceding measured return.
- **Measured return dates**: accounting rows after the initialization anchor.
  Each row is the end of one close-to-close return interval.
- **Terminal row**: `evaluation_end`. It includes the return earned into that
  close and any configured closing target reset and cost, but no fabricated
  later return.

Date-only inputs do not justify invented wall-clock precision. Runtime metadata
must pair source timestamps with event phases such as `close` and
`strictly_after_close`. Exchange timezone, session, holiday, and half-day
validation remain part of the later point-in-time data methodology.

## Canonical Daily-Close Timeline

The supported policy identifier is:

```text
after_close_signal_next_observed_close_v1
```

A close-derived signal stamped at row `t` becomes available only after
`close[t]`.

For each resolved scheduled execution accounting row `a[j]` and configured
signal lag `L`, the source signal is `a[j - L]`. When `j < L`, that scheduled
row has insufficient bounded accounting-row history and is a disclosed no-op
rather than an execution. A signal stamped on `s[k] < a[0]` may contribute to
feature computation, but it cannot satisfy execution lag or be consumed as a
trade signal. For `j >= L`:

```text
signal_source_row       = a[j - L]
feature_observation_end = close[a[j - L]]
signal_availability     = strictly_after_close[a[j - L]]
decision_time           = immediately_after_availability[a[j - L]]
execution_time          = close[a[j]]
holding_effective_start = immediately_after_close[a[j]]
first_return_start      = close[a[j]]
if j < N:
    first_return_end    = close[a[j + 1]]
    first_return_row    = a[j + 1]
if j = N:
    first_return_end    = missing
    first_return_row    = missing
```

The terminal scheduled execution at `a[N]` still has a valid
`holding_effective_start` immediately after `close[a[N]]` and a
`first_return_start` at `close[a[N]]`, but it has no return endpoint or return
row inside the bounded evaluation. It must not construct or infer `a[N+1]`.

The earliest supported execution is `close[t+1]`, the next observed source
row, only when that row is a resolved scheduled execution. With daily
rebalancing and the default `L = 1`, the complete mapping is:

```text
close[d0] observation
-> strictly after close[d0] availability and decision
-> close[d1] idealized target reset and execution cost
-> (close[d1], close[d2]] first return earned by that target
```

The ordering is strict where information availability requires it:

```text
close[a[j-L]] = feature_observation_end
feature_observation_end < signal_availability < decision_time
decision_time < close[a[j-L+1]] < ... < close[a[j]] = execution_time
execution_time < holding_effective_start
if j < N:
    holding_effective_start < first_return_end
```

The middle chain contains only the observed source-row closes strictly after
the selected signal-source row and through that scheduled execution row. For
`L = 1`, it reduces to `decision_time < close[a[j]]`.
It does not constrain source rows after execution. For `L > 1`, every
intervening observed close must precede execution and must not replace
`a[j-L]` as the frozen signal source.

A target executed at close `t` does not earn the return stamped `t`; it first
earns `(t,t+1]`.

The Stage 1 `price_forward_return` label stamped `d0` currently measures
`close[d0]` to `close[d1]`. It proved split isolation, but it is not the
strategy return earned by a `d0` after-close signal under this policy. Formal
execution-aligned factor evidence must start at the declared executable price.
The existing Stage 1 label remains diagnostic-only unless a later reviewed
label contract changes it.

Same-row synthetic response diagnostics are not executable strategy returns
and do not relax the lag requirement.

## Signal-Lag and Rebalance Contract

### Lag validation

The supported daily-close model requires:

```text
isinstance(signal_lag_periods, Integral)
and not isinstance(signal_lag_periods, bool)
and signal_lag_periods >= 1
```

`signal_lag_periods=0` is invalid for close-derived signals. Boolean,
fractional, negative, string, or missing values are also invalid and must fail
before alignment, shifting, target construction, or accounting.

Row lag counts observed source rows within the exact bounded accounting slice,
not calendar days and not rebalance periods. Lag one means the immediately
preceding accounting row, not the preceding rebalance. On a bounded
Friday/Monday/Wednesday slice, Monday uses Friday's signal and Wednesday uses
Monday's signal. Rows in the full source index before `a[0]` never satisfy lag,
even when they supplied feature warm-up inputs.

A same-close, next-open, auction, pre-close, or intraday model requires a
separate typed and reviewed execution contract. Integer zero is not implicit
authorization for any of them.

### Exact axes

Full-source prices and final signals must have identical structural axes:

- `DatetimeIndex` values and order;
- timezone awareness and timezone;
- asset columns and column order; and
- unique dates and unique asset identifiers.

No timing-sensitive path may silently reindex, sort, deduplicate, localize,
convert timezones, add assets, drop assets, forward-fill, or backfill. Bounded
IEEE `NaN` signal cells remain explicit unavailable scores under the sequence
below.

Validation order is normative:

```text
1. validate full-source price/signal axes, labels, order, uniqueness, timezone,
   and asset columns structurally
2. validate exact evaluation bounds and derive start_pos, end_pos, and
   accounting_dates
3. bounded_final_signals = final_signals.iloc[start_pos : end_pos + 1]
4. validate bounded final-signal values
5. apply bounded accounting-row lag and construct targets
```

Only after that exact bounded slice exists does value validation apply. Every
available score in `bounded_final_signals` must be real numeric, non-Boolean,
and finite. IEEE `NaN` in the bounded matrix is the sole unavailable-score
sentinel. Boolean, complex, string/object, positive or negative infinity, and
other missing representations inside the bounded matrix raise with stable
reason `signal_value_invalid` before lag application, ranking, or target
construction; they are not coerced to scores or `NaN`.

Signal values strictly before `evaluation_start` or after `evaluation_end` are
outside this validation and execution contract. Mutating only those values to
Boolean, complex, string/object, positive or negative infinity, or another
missing representation must not change the bounded result or its exception,
even if the mutation changes the full signal frame's inferred dtype. Full
structural axes validation still runs and must still pass first.

Pandas can erase per-cell type provenance when a complex assignment promotes
an otherwise real homogeneous column to `complex128`. A pre-start `1+0j` write
and a bounded `1+0j` write can produce identical final frames, so a post-hoc
snapshot alone cannot preserve both strict bounded-complex rejection and
out-of-window mutation invariance.

The selected policy is `tracked_pre_mutation_source_snapshot_v1`:

- `run_long_only_backtest` requires `source_provenance` with no default or
  compatibility bypass;
- capture is the caller-declared baseline after final price/signal panel
  construction; enforcement begins at capture, so the library cannot infer or
  recover type history already erased before that call;
- the immutable handle binds separate price/signal roles, exact axes, original
  dtype/cell semantics, current source identity/state, and a chained mutation
  ledger;
- source-cell semantic hashing supports built-in binary64-or-narrower numeric
  scalars and NumPy floating/complex scalar types whose mantissa is no wider
  than float64. A wider NumPy scalar such as x86 `longdouble` or
  `clongdouble` raises `source_provenance_invalid` at capture before any Python
  `float` conversion; this prevents precision-colliding digests and false
  lossless-recovery claims;
- later writes must use the controlled API, which records source role,
  coordinate, assigned semantic type, and before/after state digests;
- arbitrary pandas writes, copies/replacements, stale axes, role swaps,
  malformed ledgers, and replay-inconsistent state raise
  `source_provenance_invalid`;
- only a tracked complex write outside the current evaluation bounds can
  authorize lossless recovery from an originally real numeric column. An
  untouched bounded coordinate is checked against its original snapshot; a
  coordinate later written through the controlled API is checked against its
  latest tracked assignment. A latest real assignment may recover, while a
  latest complex assignment remains complex and invalid. IEEE `NaN`, signed
  zero, and large integers retain exact semantic checks. Recovery remains
  eligible when a later outside non-real write changes the promoted column
  container from complex to object; and
- native complex sources, tracked bounded complex writes, and lossy bounded
  conversions are not recovered. Signals retain `signal_value_invalid`; prices
  retain the existing incoming/execution economic-boundary reasons.

The trust boundary is library-issued in-process provenance plus controlled
post-capture mutations, not cryptographic proof against a malicious caller or
proof of pre-capture history. Direct and nested provenance objects are rejected
by the experiment-log serializer, and current committed logs include only the
allowlisted policy/status and are scanned for private field names. A caller
that extracts an internal primitive or reconstructs a plain mapping remains
responsible for not logging it.

Feature history may precede `evaluation_start`, but Stage 2b must use only the
bounded accounting-date signal matrix for signal lag and target generation. No
pre-anchor signal may create a trade on the initialization anchor or on a later
accounting row with insufficient local lag.

### Rebalance resolution

The initial policy retains the current observed-bucket behavior:

```text
daily: every accounting row
other pandas frequency: last observed accounting row in each resample bucket
```

The final observed row of an incomplete terminal bucket is therefore a
rebalance date. This is an observed-data convention, not proof of an exchange
calendar period end. Metadata must expose every resolved rebalance date rather
than only the frequency string.

On a scheduled row with no valid decision-time scores, the intended target is
all cash and existing holdings are liquidated under the normal target and cost
rules. An unscheduled row has no target reset and only drifts.

### Target freeze and execution feasibility

Ranking, selection, position constraints, and intended weights must use only:

- the lagged final signal;
- a universe or eligibility mask frozen on the same signal-source row and
  known at the immediately-after-availability decision; and
- configuration frozen before execution.

The exact execution close may be used to calculate a simulated fill price and
test feasibility. It must not change selected membership, rerank survivors, or
redistribute a failed asset's weight. The initial strict feasibility policy
requires the execution-close price for every intended nonzero buy, sell, or
liquidation leg to be real numeric, non-Boolean, finite, and strictly positive.
Missing, Boolean, complex, string/object, `NaN`, positive or negative infinity,
zero, or negative execution prices raise with stable reason
`execution_price_invalid`, without coercion, fill, reranking, redistribution,
or a successful result.

Incoming-return validation is distinct from execution-leg feasibility. For
every asset whose prior post-trade holding is nonzero, both its prior-close and
current-close endpoint prices must be real numeric, non-Boolean, finite, and
strictly positive. Missing, Boolean, complex, string/object, non-finite, zero,
or negative endpoint values raise with stable reason `incoming_price_invalid`
before asset-return calculation, gross solvency, drift, target feasibility,
trade, or cost. No coercion, fill, or zero-return substitution is allowed.
Execution buy/sell price validation remains a separate later check.
When the same held sell has an invalid incoming endpoint, the earlier
`incoming_price_invalid` check takes precedence. The sell-side
`execution_price_invalid` contract must therefore also be tested directly on
the execution-leg validator with an otherwise prevalidated frozen sell leg.

The existing `missing_price_policy="zero_return"` fallback is diagnostic-only
and cannot satisfy this formal timing contract or support promotion evidence.
A hold-cash, synthetic-zero-return, stale-price, or partial-fill execution
fallback requires a separate reviewed policy.

Changing any signal, universe value, or price after the signal-source row must
not alter its frozen intended target. An execution-row price mutation may
change feasibility, fill-price accounting, or later returns, but not ranking or
weight redistribution. Mutations may affect only events whose declared
information sets include the changed value.

## Execution, Holdings, and Cost Timing

For accounting row `t > 0`, with asset `i`:

```text
for each i where posttrade_holdings[i,t-1] != 0:
    require valid_real_nonboolean_positive(price[i,t-1])
    require valid_real_nonboolean_positive(price[i,t])
    otherwise raise incoming_price_invalid

asset_return[i,t] =
    price[i,t] / price[i,t-1] - 1

gross_return[t] =
    sum(posttrade_holdings[i,t-1] * asset_return[i,t])

gross_multiplier[t] =
    1 + gross_return[t]

require isfinite(gross_return[t])
require isfinite(gross_multiplier[t])
require gross_multiplier[t] > 0
otherwise raise portfolio_insolvent_or_non_finite_before_trade

grown_weight[i,t] =
    posttrade_holdings[i,t-1] * (1 + asset_return[i,t])

pretrade_weight[i,t] =
    grown_weight[i,t] / gross_multiplier[t]

signed_trade_weight[i,t] =
    target_weight[i,t] - pretrade_weight[i,t]

trade_weight[i,t] =
    abs(signed_trade_weight[i,t])

turnover[t] =
    sum(trade_weight[i,t])

fixed_cost_impact[t] =
    turnover[t] * fixed_cost_rate * gross_multiplier[t]

net_return[t] =
    gross_return[t] - all_applied_cost_impacts[t]

net_multiplier[t] =
    1 + net_return[t]

equity_candidate[t] =
    equity[t-1] * net_multiplier[t]

posttrade_holdings[i,t] =
    target_weight[i,t] on scheduled target rows
    pretrade_weight[i,t] otherwise
```

The row order is:

```text
prior post-trade holdings
-> held incoming-return endpoint validation
-> close-to-close asset return
-> gross return and multiplier
-> pretrade gross solvency validation
-> drifted pre-trade holdings
-> frozen target feasibility
-> signed trade and turnover
-> cost at the ending close
-> net-return and equity solvency validation
-> new post-trade holdings
```

Fixed transaction cost and fixed slippage are charged against post-return
portfolio value and expressed as beginning-period return impacts. Any
precomputed volume impact must preserve its declared return basis and exact
date alignment. Zero cost or zero slippage remains diagnostic-only.

Before accounting begins:

```text
is_real_numeric_scalar(initial_capital)
not isinstance(initial_capital, bool)
initial_capital is not missing
isfinite(initial_capital)
initial_capital > 0
```

Type, Boolean, and missing-value validation must occur before `isfinite` or
comparison so complex, string/object, `None`, and Boolean inputs fail
deterministically rather than leaking a Python or NumPy type error. Any initial
capital failure raises with stable exception evidence reason
`initial_capital_invalid`.

Before grown weights, pretrade-weight division, trade construction, or cost
calculation, every row's already-computed gross result must satisfy:

```text
isfinite(gross_return[t])
isfinite(gross_multiplier[t])
gross_multiplier[t] > 0
```

Failure, including gross return exactly `-1`, below `-1`, or non-finite, raises
with stable reason `portfolio_insolvent_or_non_finite_before_trade` before any
division by the gross multiplier, drifted pretrade weights, trades, costs,
equity update, metrics, or successful `BacktestResult`.

After all cost impacts are applied, every row must satisfy:

```text
isfinite(net_return[t])
isfinite(net_multiplier[t])
net_multiplier[t] > 0
isfinite(equity_candidate[t])
equity_candidate[t] > 0
```

Failure of any condition, including net return exactly `-1`, below `-1`, or
non-finite, raises deterministically before equity is updated, metrics are
calculated, or a successful `BacktestResult` is constructed. The implementation
must not continue into complex-valued or misleading geometric annualization,
must not serialize the run as successful evidence, and must retain the
stable row-failure evidence reason
`portfolio_insolvent_or_non_finite_after_costs` for the later Stage 4 immutable
trial ledger. It must not emit a successful result labeled `INVALID`.

The model is an idealized full target reset at an observed close. It is not an
order, fill, market-on-close auction, partial-fill, liquidity-capacity, or
brokerage model. Calling it realistic close execution or LEAN parity is
prohibited.

## Return and Metric Measurement Window

### Explicit bounds and anchor

Every backtest must receive explicit inclusive `evaluation_start` and
`evaluation_end` source rows with:

```text
require evaluation_start and evaluation_end to be exact scalar Timestamp labels
require exact timezone compatibility and membership in price_index
start_pos = price_index.get_loc(evaluation_start)
end_pos = price_index.get_loc(evaluation_end)
require start_pos and end_pos to be scalar integer positions
require start_pos < end_pos
accounting_dates = price_index[start_pos : end_pos + 1]
measured_return_dates = accounting_dates[1:]
```

Both bounds must be exact scalar timestamp labels in the validated price index,
with the same timezone awareness and timezone as that index. Strings,
including partial-date strings such as `2024-01`, are invalid rather than
instructions for pandas partial-label resolution. An off-index endpoint, an
aware/naive mismatch, a different timezone, a non-scalar `get_loc` result,
equal bounds, or reversed bounds must raise before target generation or
accounting. Bounds must not be rounded, localized, converted, or resolved by
label slicing. When both labels are valid, positional slicing includes each
boundary exactly once.

`evaluation_start` is frozen from the experiment configuration; it must not be
inferred after seeing the first non-null score, first selection, first trade,
or result. Feature warm-up can precede it and still support the signal stamped
at the anchor.

The first accounting row is a synthetic initialization anchor with zero
strategy return, zero benchmark return, no trade, zero turnover, zero cost,
and all-cash holdings. It is excluded from every period-return statistic.

If the schedule delays the first execution, intervening all-cash strategy rows
inside the preregistered evaluation window remain measured. They are part of
the chosen strategy and are compared with the benchmark. Pre-evaluation
feature warm-up rows are not measured.

### Common metric rows

After Stage 2b, these metrics must use exactly
`measured_return_dates`:

- geometric annualized net return;
- annualized net-return volatility;
- zero-risk-free, unadjusted Sharpe-style ratio;
- benchmark total and excess return over the matching window;
- tracking error from net strategy returns versus cost-free benchmark returns;
  and
- average turnover per observed measured row.

The policy fixes a non-boolean integer `periods_per_year == 252`; any other
value fails before metric calculation. The formulas are:

```text
N = len(measured_return_dates)
total_return = final_equity / initial_capital - 1
annualized_return = (1 + total_return) ** (periods_per_year / N) - 1
annualized_volatility =
    std(net_return[measured_return_dates], ddof=0) * sqrt(periods_per_year)
unadjusted_sharpe =
    mean(net_return[measured_return_dates])
    / std(net_return[measured_return_dates], ddof=0)
    * sqrt(periods_per_year)
tracking_error =
    std(
        net_return.loc[measured_return_dates]
        - benchmark_return.loc[measured_return_dates],
        ddof=0,
    )
    * sqrt(252)
```

`initial_capital`, every measured equity value, and `final_equity` must be
finite and strictly positive before geometric total or annualized return is
calculated. Equivalently, the annualization base
`1 + total_return = final_equity / initial_capital` must be finite and strictly
positive. These metric preconditions are downstream safeguards; the row-level
solvency validation above must fail the run earlier. Exact bounds require
`start_pos < end_pos`, so `N = len(measured_return_dates)` is positive.

Stage 2b changes the standalone public signature to:

```text
calculate_max_drawdown(equity_curve, *, initial_capital)
```

The standalone helper validates `initial_capital` under the scalar contract
above. It independently requires `equity_curve` to be a non-empty
`pandas.Series` with a unique, strictly increasing `DatetimeIndex` and real
numeric non-Boolean values that are all finite and strictly positive.
It has no external index-equality requirement because it receives no returns
or accounting index, and it has no responsibility for validating returns.

`calculate_basic_metrics` separately requires `returns` to be a non-empty
`pandas.Series` with a unique, strictly increasing `DatetimeIndex`, real
numeric non-Boolean finite values, and a formal first-row zero-return anchor.
Wrong container type, empty input, non-`DatetimeIndex`, duplicate or unsorted
dates, Boolean, complex, string/object, `NaN`, positive or negative infinity,
or a nonzero anchor raises with stable reason `returns_invalid` before metrics.

The basic-metrics equity and returns must have exactly identical
`DatetimeIndex` values, timezone, and order. This applies in addition to the
equity type, uniqueness, monotonicity, and value checks. Missing, extra,
reordered, or timezone-mismatched equity dates raise rather than intersecting
or reindexing. After validation, basic metrics passes the validated
`initial_capital` explicitly to `calculate_max_drawdown`.

Both helper paths validate before division, geometric annualization, or
drawdown. Wrong container type, empty series, non-`DatetimeIndex`, duplicate or
unsorted dates, zero, negative, `NaN`, positive or negative infinity, Boolean,
complex, and string/object values raise deterministically with stable reason
`equity_curve_invalid`. No coercion, intersection, sorting, or fill is allowed.
These are downstream helper safeguards; a backtester-produced invalid
intermediate or final equity must have already failed the row-level gross or
post-cost checks. Neither equity nor returns validation produces a partial
metric dictionary or successful result.

The Sharpe-style ratio assumes a zero risk-free return and remains `NaN` when
measured volatility is zero. The current key `sharpe_ratio` may remain for
compatibility only if metadata identifies this exact unadjusted convention.
Tracking error requires at least two measured daily close-to-close intervals.
Formal `BacktestResult` arrays still require a zero initialization-anchor
strategy and benchmark return. To preserve the existing public
`calculate_tracking_error` contract, a direct metric-helper test may use a
nonzero strategy anchor sentinel only to prove that exact
`.loc[measured_return_dates]` indexing excludes it; the benchmark anchor
remains required zero.

`total_return`, total turnover, and total applied costs include every
accounting event, including the terminal row. Maximum drawdown must seed the
running peak with `initial_capital`; a loss cannot disappear merely because it
occurs at the first reported equity value.

Holdings-count and concentration metrics remain closing-state metrics over
active post-trade rows, including the terminal row. Holding-episode metrics
retain their existing completed-episode contract; terminal-open episodes stay
visible in counts and are excluded from completed-episode aggregates.

The daily annualizer is an explicit observed-session assumption with
`periods_per_year=252`. Weekend and holiday gaps are not filled and lag still
counts rows. Intraday, mixed-frequency, multiple-rows-per-session input, or a
different annualization factor is outside this policy. Exchange-calendar
validation is deferred and therefore still blocks formal real-data
interpretation.

## Benchmark Alignment

The benchmark must use:

- the exact accounting-date index and timezone;
- the same initialization anchor;
- the same `measured_return_dates`;
- cost-free close-to-close returns;
- the same terminal return window; and
- no strategy transaction, slippage, or impact costs.

The benchmark price input must have the exact accounting-date axis and be real
numeric, non-Boolean, finite, and strictly positive at every row before return
conversion. Complex, Boolean, string/object, missing, extra-date, reordered, or
otherwise misaligned price input raises without coercion.

The benchmark anchor return is zero in both formal `BacktestResult` data and
the public tracking-error helper contract. Benchmark return row `t > 0`
measures the same `(close[t-1], close[t]]` interval as strategy gross return row
`t`. Tracking error subtracts benchmark returns from strategy net returns only
on the common measured-date set.

Missing benchmark prices raise in the formal path. The existing explicit
zero-return fill policy remains diagnostic-only and cannot produce tracking
error or formal benchmark-relative evidence.

`benchmark_total_return` compounds the benchmark measured returns from the
shared capital base. `excess_total_return` remains the arithmetic difference
between strategy and benchmark cumulative total returns; it must not be
described as a compounded active-return series.

Benchmark selection, investability, normalization, risk-free policy, and
calendar compatibility remain later methodology decisions.

## Required Metadata

Stage 2b must emit stable global metadata rather than only free-text prose:

| Field | Required value or meaning |
| --- | --- |
| `timing_contract` | `after_close_signal_next_observed_close_v1` |
| `feature_time` | `source_row_close_conservative` |
| `signal_availability_time` | `strictly_after_feature_row_close` |
| `decision_time` | `immediately_after_signal_availability_on_signal_source_row` |
| `execution_time` | `observed_source_row_close_idealized_reset` |
| `signal_lag_rows` | Validated non-boolean integer at least one |
| `signal_lag_unit` | `observed_source_rows_within_bounded_accounting_slice` |
| `return_frequency` | `daily_close_to_close` |
| `periods_per_year` | `252` |
| `return_interval` | `previous_close_to_current_close` |
| `holding_effective_interval` | `execution_close_to_next_observed_close` |
| `cost_application_time` | `execution_close_after_row_gross_return` |
| `cost_return_basis` | `beginning_period_portfolio_value` |
| `evaluation_start` | Explicit initialization-anchor timestamp |
| `evaluation_end` | Explicit terminal timestamp |
| `metric_anchor_policy` | `exclude_initialization_anchor_use_common_measured_rows` |
| `measured_return_start` | First timestamp after `evaluation_start` |
| `measured_return_end` | `evaluation_end` |
| `measured_return_count` | Exact number of common measured rows |
| `rebalance_resolution` | `last_observed_row_in_resample_bucket` |
| `backtest_source_provenance_policy` | `tracked_pre_mutation_source_snapshot_v1` |
| `backtest_source_provenance_status` | `validated_without_recovery` or `validated_with_tracked_complex_recovery` |
| `signal_value_failure_policy` | `validate_bounded_scores_after_exact_slice_raise_on_invalid_available_score` |
| `target_freeze_policy` | `decision_information_only_no_execution_close_rerank` |
| `incoming_price_failure_policy` | `raise_before_asset_return_on_invalid_held_endpoint` |
| `execution_price_failure_policy` | `raise_execution_price_invalid_without_redistribution` |
| `gross_insolvency_failure_policy` | `raise_before_pretrade_division_or_costs` |
| `insolvency_failure_policy` | `raise_before_successful_result_on_invalid_or_insolvent_capital` |
| `equity_curve_failure_policy` | `reject_invalid_equity_before_metrics` |
| `returns_failure_policy` | `reject_invalid_returns_before_basic_metrics` |
| `terminal_row_policy` | `include_return_trade_cost_open_holdings_no_future_return` |
| `benchmark_return_window` | `same_measured_rows_cost_free_close_to_close` |
| `initialization_anchor_policy` | `zero_return_trade_turnover_cost_and_holdings` |

The result must also expose one deterministic ledger row for every date in the
sorted, de-duplicated union:

```text
timing_ledger_dates =
    {evaluation_start} union {resolved scheduled rebalance dates}
```

The initialization anchor is therefore always represented even when a
non-daily evaluation window starts mid-bucket and the anchor is not a resolved
scheduled rebalance. When the anchor is also a scheduled date, the union still
contains one row: it retains `initialization_anchor_no_execution` and records
`is_scheduled_rebalance = true`; initialization never executes. A later
scheduled row with insufficient lag uses
`insufficient_lag_no_execution`. Each ledger row contains at least:

```text
ledger_date
scheduled_execution_date
is_scheduled_rebalance
event_status
signal_source_date
feature_observation_end
signal_availability_phase
decision_phase
execution_phase
incoming_return_start
incoming_return_end
first_holding_return_start
first_holding_return_end
is_terminal_scheduled_row
```

`ledger_date` is the union member. `scheduled_execution_date` equals
`ledger_date` only when `is_scheduled_rebalance` is true and is otherwise
missing. For a mid-bucket, non-scheduled initialization anchor,
`is_scheduled_rebalance` is false, `scheduled_execution_date` is missing, and
the initialization status and all no-execution null-field rules apply.

`event_status` is one of:

```text
initialization_anchor_no_execution
insufficient_lag_no_execution
executed_invested_target
executed_cash_target
```

For either no-execution status, signal, decision, execution, and first-holding
fields are missing, and the row has no target, trade, turnover, or cost. The
initialization anchor also has missing `incoming_return_start` and
`incoming_return_end` because no measured interval precedes `a[0]`. A later
`insufficient_lag_no_execution` row at `a[j]`, where `j > 0`, records
`incoming_return_start = a[j-1]` and `incoming_return_end = a[j]` for its
measured all-cash prior-close-to-current-close return; both first-holding
endpoints remain missing. An executed terminal target has a valid incoming
return interval when one exists and records
`first_holding_return_start = a[N]`, but `first_holding_return_end` is missing,
`is_terminal_scheduled_row` is true, and no `a[N+1]` exists in the result.
Missing endpoints must never be filled with an invented future date.

Signal-value, held incoming-price, or strict execution-feasibility failure
raises before a successful `BacktestResult` exists, so none is a
successful-result ledger status. Pretrade gross or post-cost net/equity
insolvency has the same successful-result boundary. Stage 2b tests must retain
the deterministic exception evidence; the later immutable trial ledger will
retain failed-run records.

Timestamp fields use the validated source labels. Phase fields preserve the
within-row ordering without inventing timezone-aware wall-clock instants that
the input does not provide.

## Hand-Calculated Reference Case

Use four observed closes `d0`, `d1`, `d2`, and `d3`, daily rebalancing,
`top_n=1`, lag one, and a 100-basis-point fixed transaction cost:

```text
prices:
       AAA  BBB
d0     100  100
d1     100  100
d2     110  100
d3     110  100

signals:
       AAA  BBB
d0       2    1
d1       1    2
d2       1    2
d3       2    1
```

Expected accounting:

| Row | Signal used | Prior holdings | Gross return | Frozen target | Turnover | Fixed cost impact | Net return | Post-trade holdings |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| `d0` | none | cash | `0.000` | none | `0.000` | `0.000` | `0.000` | cash |
| `d1` | `d0` | cash | `0.000` | AAA | `1.000` | `0.010` | `-0.010` | AAA |
| `d2` | `d1` | AAA | `0.100` | BBB | `2.000` | `0.022` | `0.078` | BBB |
| `d3` | `d2` | BBB | `0.000` | BBB | `0.000` | `0.000` | `0.000` | BBB |

The `d2` fixed cost is:

```text
2.0 turnover * 0.01 cost rate * 1.10 post-return growth = 0.022
```

Starting from capital `1.0`, equity is `1.0` at `d0`, `0.99` at `d1`,
`1.06722` at `d2`, and `1.06722` at `d3`. The common measured return dates are
`[d1, d2, d3]`; the anchor `d0` is excluded from period statistics but remains
the initial-capital base.

The `d0` signal selects AAA. It does not earn the AAA `d0` to `d1` return. It
is executed at `d1` close and first earns AAA's 10% `d1` to `d2` return,
recorded on `d2`. Changing only the `d1` signal may change the `d2` target and
cost, but it cannot change the `d2` gross return already earned by the AAA
holding established at `d1`.

## Deterministic Stage 2b Test Matrix

| ID | Fixture | Required assertion |
| --- | --- | --- |
| `TIMING-001` | The four-row daily-rebalance reference case above, where fixture labels `d0..d3` are bounded accounting rows `a[0..3]`. | Each scheduled row uses bounded `a[j-L]`; exact signal source, execution row, first earned return, drift, trade, turnover, cost, holdings, net return, and equity values match by hand. |
| `TIMING-002` | Lags `0`, `False`, `0.0`, `-1`, `1.5`, and `"1"`. | Every invalid lag fails before alignment or target construction; integer one passes. |
| `TIMING-003` | Full-source signal axes with an extra/missing/reordered date or asset, duplicate labels, or a timezone mismatch; bounded cells with Boolean, complex, string/object, positive infinity, negative infinity, IEEE `NaN`, and other missing values; native homogeneous complex inputs; NumPy float/complex scalars wider than float64 on platforms that provide them; the identical-frame pre-start-versus-bounded `1+0j` counterexample; an outside complex upcast followed at one bounded coordinate by controlled complex, real, and complex assignments; an outside complex write followed by an outside non-real write that leaves the current column as object; controlled pre-start/post-end mutations; and stale, swapped, untracked, tampered, moved-bound, or lossy provenance cases. | Full structural axis validation runs first; exact bounds then select `bounded_final_signals`; every native/bounded complex and other invalid value raises its domain reason while bounded IEEE `NaN` alone remains unavailable. Wider-than-float64 NumPy source scalars fail provenance capture before downcast. Tracked out-of-window signal/price mutations leave bounded results and exceptions unchanged, including complex and later object dtype propagation; the latest controlled bounded assignment determines recovery, so a final real value executes while a final complex value fails; arbitrary or inconsistent state raises `source_provenance_invalid`; the coordinate ledger distinguishes identical final complex frames. |
| `TIMING-004` | A bounded Friday, Monday, and Wednesday accounting slice with lags one and two. | Lag one uses the immediately preceding accounting row, not a calendar-day offset; for Wednesday execution at lag two, Friday is the frozen source, Monday is an intervening close, and the asserted order ends at Wednesday execution without constraining later rows. |
| `TIMING-005` | Monthly rebalancing with daily signal rows. | Each month-end execution uses the immediately preceding source-row signal for lag one, not the previous rebalance signal; unscheduled signals do not execute. |
| `TIMING-006` | For each intended nonzero buy and a directly tested prevalidated frozen sell leg, separately set the execution-close price to missing, Boolean, complex, string/object, `NaN`, positive infinity, negative infinity, zero, and negative values; separately apply the same invalid values to the prior and current incoming-return endpoints of a nonzero prior holding. | Every invalid buy/sell execution leg raises `execution_price_invalid` without coercion, fill, reranking, or redistribution; every invalid held endpoint raises `incoming_price_invalid` earlier than asset return, gross validation, drift, target feasibility, trade, or cost; when an integrated held sell shares the invalid current endpoint, incoming-price failure takes precedence while the direct sell-validator fixture preserves independent sell-leg coverage. |
| `TIMING-007` | Mutate execution-row signal/eligibility values and, separately, a price strictly after the execution row. | Neither mutation changes the frozen intended target or the execution row's incoming gross return; execution-close price mutations are covered separately by feasibility and accounting tests. |
| `TIMING-008` | Explicit full-source history before `evaluation_start`, a first post-anchor scheduled row with insufficient local accounting-row lag, later daily lag-greater-than-one no-op rows, and a non-daily window whose anchor is mid-bucket. | Pre-anchor history supports feature computation but is never consumed as a lagged trade signal; the first post-anchor scheduled row remains all cash when `j < L`; the ledger-date set is exactly the anchor/rebalance union; the mid-bucket anchor appears once with `is_scheduled_rebalance = false`, missing scheduled execution and incoming/first-holding intervals; each later insufficient-lag row records its `a[j-1]` to `a[j]` all-cash incoming interval while both first-holding endpoints remain missing. |
| `TIMING-009` | Explicit bounded evaluation dates after a long feature warm-up, plus partial-date string `2024-01`, off-index endpoints, equal and reversed bounds, aware/naive and different-timezone endpoints, and an exact-boundary fixture. | Strategy return, benchmark return, annualized return, volatility, Sharpe, and tracking error exclude every warm-up row; the partial string and every other invalid endpoint case raise before target generation; scalar `get_loc` positions drive the valid exact positional slice, whose endpoints are each included once and whose rows alone contribute to accounting and metrics. |
| `TIMING-010` | Hand-calculated net and benchmark returns; a direct tracking-error fixture with a deliberately nonzero strategy anchor sentinel and required zero benchmark anchor; an anchor loss check; `periods_per_year` values `False`, `True`, `251`, `252`, and `365`; initial capital inputs `True`, `False`, complex, string, `None`, zero, negative, `NaN`, and infinity; gross returns exactly `-1`, below `-1`, `NaN`, positive infinity, and negative infinity; separate high-cost net returns exactly `-1`, below `-1`, `NaN`, positive infinity, and negative infinity; standalone drawdown equity inputs with wrong container type, empty series, non-`DatetimeIndex`, duplicate or unsorted dates, zero, negative, `NaN`, positive infinity, negative infinity, Boolean, complex, or string/object values; basic-metrics returns with wrong container type, empty series, non-`DatetimeIndex`, duplicate or unsorted dates, Boolean, complex, string/object, `NaN`, positive infinity, negative infinity, or nonzero formal anchor; and basic-metrics equity versus returns with missing, extra, reordered, or timezone-mismatched dates. | All period metrics share `measured_return_dates`; the direct tracking-error helper remains invariant to its permitted strategy anchor sentinel while basic-metrics returns require a zero anchor; standalone drawdown requires keyword `initial_capital`, validates only its own series/index/value contract, and has no returns responsibility; basic metrics rejects every invalid returns case with `returns_invalid`, requires exact equity/returns index/timezone/order equality, and passes validated capital to drawdown; direct equity violations raise `equity_curve_invalid`; invalid initial capital, gross, and high-cost net cases raise their distinct stable reasons before downstream work. |
| `TIMING-011` | Exact benchmark prices and zero benchmark-return anchor, plus Boolean, complex, string/object, missing, non-finite, non-positive, extra-date, missing-date, duplicate-date, reordered-date, and timezone-mismatched benchmark variants. | Strategy and benchmark share anchor, measured rows, and terminal window; tracking error explicitly subtracts only each series' `.loc[measured_return_dates]` values while preserving the helper's zero benchmark anchor; duplicate dates and every other benchmark type, price, axis, or alignment violation fail without coercion. |
| `TIMING-012` | An incomplete terminal resample bucket with a target change at scheduled accounting row `a[N]`. | The last observed row is disclosed as a rebalance; its incoming return, turnover, and cost are included and its post-trade holdings are open; `holding_effective_start` is immediately after `close[a[N]]`, `first_holding_return_start` is `a[N]`, both the first-return endpoint and row are missing, and no `a[N+1]` is constructed or inferred. |
| `TIMING-013` | A Stage 1 same-row synthetic response and a one-row price-forward label. | Both remain diagnostic targets and cannot be serialized as executable strategy P&L under this policy. |
| `TIMING-014` | Every current backtest caller and serialized result. | Every caller declares a capture baseline and passes required provenance at the final-panel boundary. Global typed metadata includes only the allowlisted provenance policy/status, resolved rebalance dates, and one ledger row per date in the initialization-anchor/resolved-schedule union. Direct/nested provenance-object serialization is rejected, and current committed logs are scanned for internal field names. The anchor, insufficient-lag, nonterminal, and terminal intervals reconcile with accounting arrays without inventing `a[N+1]`. |

Implementation tests must assert values, dates, event ordering, error messages,
and mutation invariance. Static wording checks alone do not complete Stage 2b.

## Stage 2b Implementation Boundary

Stage 2b may change:

- `src/backtest/portfolio.py` and `src/backtest/metrics.py`;
- their focused deterministic tests;
- current synthetic callers and configuration surfaces that expose signal lag;
- exact generated synthetic reports, JSON logs, and registry entries only when
  deterministic behavior or metadata changes;
- timing-related documentation and public method summaries; and
- the smallest validation helper surface required for exact axes and bounded
  evaluation metadata.

Stage 2b must:

- start from the matrix above;
- reject zero, Boolean, fractional, and negative lag values;
- add explicit bounded evaluation dates;
- preserve a zero initialization anchor;
- validate full-source axes structurally, select exact bounded accounting
  signals, and only then reject invalid bounded available values before lag or
  target construction;
- require immutable price/signal provenance as a caller-declared baseline,
  state that enforcement begins at capture, reject stale or untracked later
  source state, and permit complex-dtype recovery only through the controlled
  coordinate ledger;
- freeze targets immediately after source-row signal availability;
- validate every held prior/current incoming-price endpoint before asset
  returns or gross accounting;
- validate every nonzero buy/sell execution-close price as real numeric,
  non-Boolean, finite, and positive without coercion or redistribution;
- align every period-return metric to one measured-date set;
- enforce the daily `periods_per_year == 252` annualizer;
- reject non-real, non-scalar, Boolean, missing, non-finite, or non-positive
  initial capital before unsafe numeric operations; reject invalid gross
  multipliers before division, drift, trades, or costs; reject invalid
  net-return multipliers or resulting equity before metrics or a successful
  result;
- change standalone drawdown to
  `calculate_max_drawdown(equity_curve, *, initial_capital)`, migrate every
  caller, and keep its self-contained series/index/value validation distinct
  from basic-metrics equity/returns exact-index alignment;
- validate direct basic-metrics returns as a non-empty, unique, increasing,
  finite real non-Boolean `pandas.Series` with a zero anchor before metrics;
- emit typed timing metadata and one ledger row per date in the
  initialization-anchor/resolved-schedule union;
- migrate all direct callers without hidden compatibility bypasses;
- retain changed and failed deterministic evidence; and
- run focused tests plus the complete repository gates.

Stage 2b must not:

- interpret or regenerate private EODHD performance;
- change factor formulas, directions, or parameters;
- treat Stage 1 diagnostic labels as strategy returns;
- add a provider, exchange-calendar, execution, or heavyweight dependency;
- add next-open, intraday, auction, partial-fill, shorting, or LEAN runtime
  behavior; or
- claim empirical alpha, profitability, robustness, capacity, or readiness.

Any generated-output change remains synthetic implementation evidence and
changes no research trial count.

## Accepted Decisions and Deferred Choices

Accepted here:

- the canonical policy is
  `after_close_signal_next_observed_close_v1`;
- every generic final signal is conservatively available after its stamped
  close;
- signal lag is a non-boolean integer bounded accounting-source-row count of
  at least one; full-source pre-anchor history may support feature computation
  but cannot satisfy execution lag;
- for every scheduled execution `a[j]`, lag `L` uses source signal
  `a[j-L]`; under daily rebalancing, fixture `d0` as `a[0]` maps to `d1` as
  `a[1]` execution and first earned return ending at `d2` as `a[2]`;
- prices and signals require exact axes and timezone compatibility;
- bounded available signal scores are real numeric non-Boolean finite values;
  only bounded IEEE `NaN` denotes an unavailable score, and out-of-window value
  mutations cannot affect bounded results or exceptions;
- source provenance is mandatory; the selected
  `tracked_pre_mutation_source_snapshot_v1` policy distinguishes native,
  bounded, and tracked post-capture out-of-window complex values. It cannot
  prove pre-capture history; direct and nested provenance objects are not
  serializable, while callers remain responsible for extracted primitives;
- targets are frozen immediately after source-row signal availability;
- held incoming-return endpoints are strictly validated before asset returns,
  separately from later execution-leg feasibility;
- execution-price feasibility cannot rerank or redistribute;
- every intended nonzero buy/sell execution leg requires a real numeric,
  non-Boolean, finite, positive execution-close price;
- invalid initial capital raises before accounting; non-finite or non-positive
  gross multiplier raises before pretrade division, drift, trades, or costs;
  non-finite or non-positive net-return multiplier or resulting equity raises
  before metrics or a successful result;
- return, drift, trade, cost, and holdings follow the explicit row order;
- evaluation bounds are explicit and the first row is a zero initialization
  anchor;
- strategy and benchmark period metrics share the same post-anchor rows;
- standalone drawdown validates only its own capital/equity inputs, while basic
  metrics additionally validates formal zero-anchor returns and exact
  equity/returns index alignment;
- the daily annualization factor is exactly 252;
- warm-up remains available to features but outside measured evaluation;
- drawdown includes the initial-capital base;
- observed-bucket rebalance resolution and terminal target/cost behavior are
  retained and disclosed; and
- the model is an idealized close-reset accounting model, not fill evidence.

Deferred:

- same-close, pre-close, next-open, auction, and intraday execution;
- actual order submission, fill, partial-fill, queue, and market-impact models;
- exchange calendars, timezones, holidays, half-days, suspensions, stale
  prices, delistings, and corporate actions;
- a formal risk-free series and non-daily annualization;
- execution-aligned replacement of existing Stage 1 diagnostic labels;
- terminal liquidation or suppression of a terminal rebalance;
- calibrated capacity and borrow/shortability;
- LEAN signal, holdings, trade, cost, and fill parity;
- real-data interpretation and protected-sample access; and
- every empirical promotion threshold.

Those choices cannot be inferred from Stage 2a documentation or current
synthetic results.

## M4.4 Optional PIT Membership and Immediate Terminal Cash

M4.4 extends the daily simulation boundary with optional
`constituent_intervals` and `terminal_events` inputs in both backtest engines.
The preceding Stage 2a decisions describe the original interface. This section
defines the implemented immediate-cash subset of the deferred delisting work.
The detailed input contract is in
[`coord/card_m4_4_pit_universe_delisting.md`](../coord/card_m4_4_pit_universe_delisting.md).

`build_pit_membership_mask` requires permanent-ID price/signal columns and
identity-backed half-open membership intervals. At execution row `a[j]`, the
membership schedule uses information available at bounded source row `a[j-L]`.
An entry requires both its effective start and its known-at cutoff. A closure
applies once its effective end and end-known-at cutoff both hold. The first `L`
rows have empty eligibility. Membership changes act at scheduled target resets;
an explicit terminal event also settles existing holdings between resets.

PIT CSV ingestion validates raw symbol and permanent-ID strings before legacy
normalization, including caller-selected column names. Padded or blank values
raise a `PIT-005` exact-string error. Valid leading-zero string IDs preserve
their bytes through loading and membership construction.

Availability and effective dates use caller-declared, timezone-naive daily
source-close labels. The interface refuses intraday timestamps and preserves
observed source-row lag. Source publication precision, revision histories, and
exchange-calendar certification require separate evidence. Synthetic declarations
establish simulation conformance and carry `DIAGNOSTIC_ONLY` evidence status.

A terminal event declares its permanent ID, unique event ID, effective close,
known-at close, preceding full-source reference close, complete terminal return,
and the literal basis `prior_observed_close_to_cash`. Terms must be available by
the effective close. The complete return replaces the ordinary incoming return
on that row and includes any final market and delisting legs. A held security
still requires a valid positive reference price. Its terminal quote may be
missing because the evidenced cash payoff supplies the final valuation.

After gross P&L and drift, signed cash settlement equals prior equity multiplied
by the prior signed weight and `(1 + terminal_return)`. The settled holding then
becomes zero. Long redemption credits cash; short settlement debits the final
liability. Existing positive-equity guards apply before division and after costs.
An explicit return of -1 represents evidenced zero recovery. Missing evidence
continues to refuse held disappearance under the strict price policy.

Known terminal schedules exclude settled identities from frozen future targets.
A late event that collides with a nonzero frozen target raises
`terminal_target_invalid`. Ordinary execution-price validation, scheduled target
construction, turnover, and costs retain their existing order. The terminal
redemption itself has zero modeled extra fee and a separate cash-flow record;
ordinary market turnover contains only subsequent market trades. Surviving
positions drift until the next scheduled reset, including temporarily unbalanced
long-short exposures.

Both result types expose `cash_balance`, `terminal_cashflows`, and
`terminal_event_log`. Cash is the residual of the existing postcost target-weight
accounting convention: equity times one minus the sum of signed closing weights.
The event log records source evidence and signed proceeds independently of the
ordinary timing ledger. Event-free calls preserve existing output values and
add zero terminal flows plus the residual cash series.

Events effective exactly at the initialization row retain zero-weight,
zero-cashflow log entries when their full-source reference is valid. Events
strictly earlier than the bounded start keep the identity closed and remain
outside the bounded event log. Both public backtest APIs require at least two
bounded source rows; a one-row evaluation retains its existing typed refusal.

The synthetic command `python -m research.pit_universe_delisting_demo` records
static/PIT comparisons, identity reuse, cash settlement, and retained missing-
evidence refusals. Delayed recoveries, unpriced receivables, and formal
real-data lineage promotion remain open evidence gates.

### M4.7 consideration bases

Milestone 4.7 stage a-0 widens the accepted `return_basis` literal to the
frozen set `ACCEPTED_TERMINAL_BASES` in `src/backtest/portfolio.py`, which both
engines use. The engine refuses every other string with
`terminal_events_invalid`.

| Consideration | Terminal return | `return_basis` |
| --- | --- | --- |
| Cash, or evidenced zero recovery (`-1`) | `c / P_ref - 1` | `prior_observed_close_to_cash` |
| Stock | `r * P_acq(V) / P_ref - 1` | `prior_observed_close_to_stock_consideration_valued_at_completion_date_close` |
| Mixed | `(c + r * P_acq(V)) / P_ref - 1` | `prior_observed_close_to_mixed_consideration_valued_at_completion_date_close` |

`L` is the target's last observed bar (the event's `reference_date`), `S = L + 1`
is the settlement row (the event's `effective_date`), and `P_ref` is the target
raw close at `L`. The valuation row `V = row(completion_date)` satisfies
`V in {L, S}`, so every price inside the terminal return is observable at the
close of `V <= S`. The engine receives only the finished `terminal_return`.
Settlement is unchanged: the engine credits cash on `S` with the arithmetic,
turnover exclusion, cost treatment, and refusal codes of this M4.4 section.

Both result types record `terminal_settlement_contract:
prior_observed_close_to_consideration_at_completion_date_row_v2`, which
replaces `prior_observed_close_to_cash_v1`, and `terminal_basis_counts`, the
event count per accepted label with zero for absent labels. Event-free calls
omit both keys. `resolve_pit_universe_mask(constituent_intervals,
terminal_events, dates, assets, *, signal_lag_periods=1)` returns the exact
mask `_resolve_pit_universe` hands the target builder after
`_prepare_terminal_events`, so research code reads the engines' resolved
universe by construction.

## M4.5 Optional Daily Market Impact and Self-Financing Cash

Both engines accept `impact_model`, `impact_volumes`, `impact_price_basis`, and
`impact_volume_basis`. The default `impact_model=None` preserves every existing
result field exactly. An active `SquareRootImpactModel` requires strict held
prices, matching `raw` or matching `split_adjusted` bases, and zero legacy
`slippage_bps`. The long-only precomputed impact overlay remains exclusive of
this model. Commission remains additive. Supplied volume axes must exactly
match the unique, ordered full-source price axes.

At execution row `t`, dollar ADV is the mean of `price * volume` over W complete
source rows ending at `t-L`; daily volatility is the sample standard deviation
of W simple one-row price returns ending at `t-L`. Here W is `lookback >= 2`
and L is the engine's positive `signal_lag_periods`. Full-source warm-up rows
before evaluation supply historical estimates. Values after the bounded end
remain outside estimation. Every nonzero request requires finite ADV at or
above `min_adv` and finite nonnegative volatility. Zero requests consume zero
liquidity and cost. Actual fills additionally require a positive current price
and observed current volume. Current volume supplies a feasibility veto; it
never determines target ranking or quoted size.

For absolute requested dollars Q, lagged ADV A, participation p=Q/A, fixed bps b,
and daily volatility sigma, base slippage dollars are
`C = Q * (b/10000 + eta * sigma * sqrt(p))`. The `raise` policy refuses requests
above `max_participation_rate * A`. The `throttle` policy clips ordinary traded
dollars to that amount and carries the remainder as signed shares. The
`penalize` policy adds total dollar cost
`A * penalty_bps/10000 * max(p/max_participation_rate - 1, 0)^2`.
All coefficients are declared scenarios; the model's costs represent average
execution cost. Empirical calibration remains a separate evidence gate.

The row order is gross held-asset return, evidenced terminal cash settlement,
frozen target or deferred-share request, participation policy, sells, cash-funded
buys, and cost payment. A scheduled target requests `target * E_pre - H`, where
H is the vector of post-return dollar holdings and E_pre is pretrade equity.
A new target cancels the previous queue. On other rows, deferred signed shares
use the current price; settled identities cancel before quote validation.
Known ineligibility allows only exposure reduction. Long-only sells are bounded
by the remaining long position; arithmetic excess shares are cancellations.

Existing cash plus sale proceeds pays sell commission and slippage first. A
shared buy scale in [0,1], determined by 64-step monotone bisection, reserves
cash for buy dollars, commission, and recomputed nonlinear impact. Funding
shortfalls become cancellations. Liquidity shortfalls remain deferred shares.
With actual signed market dollars X, commission F, and slippage C:

```text
E_pre  = E_previous * (1 + gross_return)
E_next = E_pre - F - C
K_next = K_pre - sum(X) - F - C
H_next = H + X
w_next = H_next / E_next
turnover = sum(abs(X)) / E_pre
transaction_costs = F / E_previous
slippage_costs = C / E_previous
```

Funding calculations retain an immutable snapshot of unscaled quoted buys.
Closing cash plus signed holdings must reconcile to post-cost equity within a
relative tolerance of 1e-12 of equity, with a $0.000001 absolute floor; an
excess discrepancy raises `impact_accounting_invalid`. The relative bound
matches the pre-trade check, so floating-point rounding on large books
reconciles while books below $1M keep the absolute limit. Held quantities persist between
market trades. Terminal redemption contributes zero market turnover and zero
impact fee; later ordinary reinvestment follows the impact policy. Target
position caps and long-short neutrality describe frozen targets. Partial fills
and drift can produce different actual exposures. Both engines retain their
existing refusal of a one-row bounded evaluation.

The six additive audit fields are dollar `slippage_cost_series`, dollar-weighted
`realized_slippage_bps`, `trade_participation_rates`, signed
`executed_trade_values`, `pending_trade_shares`, and `cancelled_trade_shares`.
Zero-trade rates are zero. Legacy traded cells have unavailable participation.
Cancellations aggregate signed shares per row and asset; opposing cancellations
can offset in that aggregate. Final deferred shares remain explicit unfinished
simulation state. The long-only timing ledger labels scheduled frozen target
attempts; its separate actual-trade matrix includes all deferred retries.

The generated capacity report retains every engine, AUM, and policy attempt,
including failures and refusals. Its benchmark holds equal initial dollars in
the predeclared cohort at zero benchmark cost. Adjacent positive-to-nonpositive
benchmark-excess brackets are reported without interpolation. Refused endpoints
remain unavailable. Books with fewer than 21 measured daily returns report
Sharpe as unavailable. Borrow fees, recalls, intraday execution, corporate-action
conversion of pending shares, source basis verification, and empirical capacity
remain open research work.

## M4.6 Optional Style Risk Attribution

Both engines accept `risk_model`. The default `risk_model=None` preserves every
existing result field and returns `risk_attribution=None`. An active
`CrossSectionalRiskModel` produces a diagnostic sidecar; engine accounting,
holdings, costs, and metrics are unchanged.

For each measured return row `a[j]`, the interval is `(close[a[j-1]],
close[a[j]]]`. Style exposures, regression weights, and benchmark weights come
from the immediately previous observed close `a[j-1]`, and the model refuses
any other start. Portfolio weights are the engine's actual prior-close
holdings after drift and partial fills. Exposures are winsorized, demeaned,
and population-scaled at that close; warm-up rows stay missing and a selected
row requires complete finite values.

Cross-sectional OLS or WLS with a Market intercept estimates factor returns on
each interval. A fit requires more assets than coefficients (`sample_size`)
and full column rank (`rank_deficient`). Factor plus specific return
reconciles to the engine's gross return within 1e-12, and net return equals
gross return minus engine costs.

Active-risk forecasts use only strictly earlier fitted intervals: at most
`covariance_window` of them, and at least `min_covariance_observations`, or the
row reports `insufficient_history`. The current interval stays outside its own
estimate. Specific variance is diagonal. Aggregate variance roundoff within
1e-14 is clamped to zero after validation; material negative variance refuses.

Enabled attribution requires an absent terminal-event table and the strict
missing-price policy (`integration_scope`), plus complete finite prices for
every regression asset (`nonfinite`); a changing regression universe therefore
refuses. Market capitalization and book-to-price inputs are
caller-declared at their availability close. Empirical calibration, industry
factors, residual correlations, and geometric linking remain open research
work.
