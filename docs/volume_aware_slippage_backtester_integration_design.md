# Volume-Aware Slippage Backtester Integration Design

Date: 2026-06-11

## Status: Historical / Superseded In Part

This design is retained as provenance for the reviewed precomputed-impact
boundary. The first integration path has since been implemented and tested in
`src/backtest/portfolio.py`, `tests/test_backtest_portfolio.py`, and
`tests/test_volume_aware_slippage.py`, with
`volume_aware_slippage_mode="diagnostic_only"` still the default and
`apply_precomputed_impact` requiring an explicit aligned impact series plus
audit metadata.

The remaining live guidance is the boundary: the backtester still does not
compute rolling dollar volume from raw volume data, fetch data, infer OHLCV
semantics, connect to brokers, place orders, or claim execution realism.

Current code also exposes drift-aware per-asset trade weights on
`BacktestResult`. The standalone slippage helper accepts those weights through
`calculate_volume_aware_slippage_from_trade_weights()` and records their source.
Candidate impact still enters net-return accounting only through the explicit
precomputed-impact boundary; no rolling volume calculation was moved inside the
backtester.

This is a documentation-only design for deciding whether and how the existing
synthetic-only volume-aware slippage diagnostic helper could later be connected
to the simulated local backtester.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loaders, factor logic, diagnostics behavior, metrics, LEAN code,
data access, execution behavior, or strategy behavior. It does not fetch data,
download data, add vendor APIs, add credentials, add live trading, add paper
trading, add brokerage integration, add order execution, or claim
profitability.

## 1. Problem To Solve

The current local backtester can deduct transaction costs and fixed-basis-point
slippage from simulated returns. The repository also has a standalone
volume-aware slippage diagnostic helper that calculates lagged dollar-volume
capacity, trade notional, participation, candidate slippage impact, and audit
counts.

Those two paths are intentionally separate. The separation leaves a reviewed
question before any implementation:

```text
Should candidate volume-aware slippage ever affect simulated net returns, and
if so, what exact inputs, defaults, stop conditions, reporting fields, and tests
are required?
```

The problem this integration would solve is not execution realism. The problem
is auditability: if a future simulated report wants to compare gross returns,
fixed transaction costs, fixed-bps slippage, and candidate liquidity-aware
friction, the accounting and caveats must be explicit before behavior changes.

## 2. Current State

| Artifact | Current role |
| --- | --- |
| `src/backtest/portfolio.py` | Exposes drift-aware per-asset trade weights and applies their summed turnover to transaction-cost, fixed-bps slippage, and net-return accounting. |
| `src/backtest/metrics.py` | Reports total transaction-cost, slippage, and total trading-cost impact when supplied. |
| `src/backtest/slippage.py` | Provides a compatibility target-difference helper and an explicit drift-aware trade-weight diagnostic entrypoint. |
| `tests/test_volume_aware_slippage.py` | Covers lagged capacity, explicit notional, missing/zero liquidity, participation caps, and forbidden imports for the helper. |
| `research/local_csv_fixture_workflow_demo.py` | Calls the helper on committed synthetic fixture inputs and reports participation plus rejected/cap counts without applying candidate slippage to returns. |
| `docs/volume_aware_slippage_design.md` | Defines the original design boundary for the helper and diagnostic smoke path. |

The helper returns candidate `portfolio_slippage_impact`, but that series is
not consumed by the backtester. Current generated local-fixture artifacts use
the helper for diagnostics only.

## 3. Why It Remains Diagnostic-Only

Volume-aware slippage remains diagnostic-only because applying it to simulated
returns would change research accounting and interpretation.

The unresolved issues are:

- explicit portfolio-dollar notional is required before target weights can be
  converted to dollar trade size.
- lagged dollar volume must be aligned to a pre-trade liquidity reference date.
- missing, zero, stale, or incomplete volume can make the estimate invalid.
- participation caps can reject or mark trades, and that policy changes
  interpretation.
- fixed-bps slippage and volume-aware slippage can be double-counted if both
  are applied without a reviewed rule.
- synthetic and committed-fixture diagnostics do not calibrate market impact or
  prove execution realism.
- user-provided local CSV interpretation remains blocked until readiness-audit,
  provenance, adjustment-policy, benchmark, and experiment-handoff gates are
  complete.

The safe current default is therefore:

```text
volume_aware_slippage_mode = "diagnostic_only"
```

## 4. Required Inputs For Any Future Integration

Any future implementation that lets volume-aware slippage affect backtester net
returns must require validated local or synthetic inputs. It must not fetch or
infer missing data.

Required inputs:

- target weights on the same rebalance dates and asset columns used by the
  backtester.
- previous target weights or an equivalent deterministic turnover convention.
- price panel used to compute dollar volume.
- volume panel or local OHLCV-derived volume panel with reviewed adjustment
  policy.
- explicit price field for dollar volume, such as `close` or `adjusted_close`.
- explicit volume policy, such as raw share volume, adjusted volume, or
  reviewed source-specific policy.
- `portfolio_notional` as a positive finite dollar scale. The normalized
  `initial_capital=1.0` default is not a market notional.
- rolling dollar-volume `window`, `min_periods`, and `volume_lag`.
- rebalance calendar and liquidity-reference-date rule.
- `base_slippage_bps`, `participation_slope_bps`, and
  `max_participation`.
- stop-condition policies for missing volume, zero volume, stale volume,
  invalid notional, and excessive participation.

The first implementation should not add vendor APIs, broker connections,
request-based downloads, or live/paper trading dependencies to satisfy these
inputs.

## 5. Recommended Integration Shape

The recommended first integration, after a separate test-plan PR, is a
precomputed-impact boundary rather than making `run_long_only_backtest()`
calculate volume-aware slippage internally.

Recommended future flow:

1. Build backtester target weights by the existing deterministic path.
2. Call `calculate_volume_aware_slippage_diagnostics()` outside the backtester
   with explicitly validated price, volume, notional, lag, window, and cap
   parameters.
3. Pass only a reviewed, date-aligned `portfolio_slippage_impact` series plus
   audit metadata into the backtester or a narrow wrapper.
4. Deduct that impact from simulated net returns only when an explicit future
   option says to apply it.
5. Preserve the full diagnostic object for audit reporting.

Rationale:

- It keeps volume, notional, and missing-data policy review outside the core
  portfolio-return path.
- It avoids making the backtester responsible for OHLCV validation or
  liquidity-window construction.
- It makes date alignment and impact-series review testable before net-return
  behavior changes.
- It minimizes the chance of hidden double counting with fixed-bps slippage.

Deferred alternative:

- A later, higher-risk implementation could let `run_long_only_backtest()`
  accept price and volume panels and call the helper internally. That should
  remain deferred until a separate design explains why the backtester should own
  OHLCV semantics.

## 6. Accounting Semantics

Current behavior:

```text
gross_return[t] = return before transaction-cost and slippage deductions
fixed_transaction_cost_impact[t] = turnover[t] * transaction_cost_bps / 10000
fixed_bps_slippage_impact[t] = turnover[t] * slippage_bps / 10000
net_return[t] = gross_return[t]
    - fixed_transaction_cost_impact[t]
    - fixed_bps_slippage_impact[t]
```

Future precomputed-impact behavior, if implemented after review:

```text
volume_aware_slippage_impact[t] =
    diagnostics.portfolio_slippage_impact[t]

net_return[t] = gross_return[t]
    - fixed_transaction_cost_impact[t]
    - fixed_bps_slippage_impact[t]
    - volume_aware_slippage_impact[t]
```

Required boundaries:

- Gross returns must not change.
- Target weights, holdings, and turnover must not change merely because a
  slippage impact is supplied.
- Transaction-cost impact remains separate from slippage impact.
- Volume-aware slippage impact must be separately named and separately
  reportable.
- The first implementation should reject applying both positive fixed-bps
  slippage and positive volume-aware slippage unless a later reviewed design
  explicitly permits combined models.
- Zero fixed-bps slippage with applied volume-aware slippage is not a
  no-slippage run; it must be labeled as volume-aware candidate slippage.
- A run with no applied slippage, or diagnostic-only volume-aware slippage,
  remains a zero-slippage or diagnostic-only run.

## 7. Returns, Costs, Audit Fields, Or Diagnostics

The model can have three distinct future modes:

| Mode | Returns affected? | Cost fields affected? | Audit fields affected? | Intended use |
| --- | --- | --- | --- | --- |
| `diagnostic_only` | No | No | Yes | Current default; report participation, candidate impact, rejected/cap counts, and caveats only. |
| `apply_precomputed_impact` | Yes | Yes, as a separate slippage impact series | Yes | Future explicit implementation after tests; deduct a precomputed aligned impact series from net returns. |
| `internal_backtester_calculation` | Yes | Yes | Yes | Deferred; requires separate design because the backtester would own volume-panel and OHLCV semantics. |

The current stage recommends keeping `diagnostic_only` as the default and using
`apply_precomputed_impact` as the only acceptable first future integration
shape. `internal_backtester_calculation` should not be implemented as the next
stage.

## 8. Required Defaults And Stop Conditions

Defaults for a future implementation should be conservative:

| Area | Default | Stop condition |
| --- | --- | --- |
| Integration mode | `diagnostic_only` | Applying to returns requires an explicit opt-in and reviewed tests. |
| Portfolio notional | No implicit default from `initial_capital` | Missing, non-numeric, non-finite, or non-positive notional raises. |
| Dollar-volume lag | Positive lag, default `volume_lag=1` | Same-day volume use is blocked unless a later design records an execution-time assumption. |
| Missing volume | `raise` for traded cells | Missing price, missing volume, missing lagged rolling dollar volume, or warm-up capacity needed by a trade raises. |
| Zero volume | `raise` for traded cells | Zero volume inside the required rolling window or non-positive lagged rolling dollar volume raises. |
| Stale volume | `raise` or `mark_unestimated`, with `raise` preferred | Liquidity reference older than an explicit `max_volume_age` or outside coverage raises by default. |
| Excessive participation | `raise` | Participation above `max_participation` raises; silent clipping is not allowed. |
| Fixed-bps plus volume-aware slippage | Reject combined positive slippage models by default | Positive `slippage_bps` plus applied positive volume-aware impact raises until a combined-model design exists. |
| Missing diagnostics metadata | `raise` | Applied impact without model name, parameters, lag, notional, cap, and caveats raises. |

Optional future policies such as `mark_unestimated`, `exclude_trade`, or
`clip_to_cap` must be explicit, non-default, documented, and tested before use.
They must report affected dates and symbols. They must not silently transform
missing or zero liquidity into zero slippage.

## 9. Required Tests Before Implementation

Before any code-changing PR applies volume-aware slippage to backtester
returns, deterministic tests must cover:

- existing fixed-bps backtester behavior remains backward-compatible.
- volume-aware slippage is diagnostic-only by default and does not affect net
  returns.
- applied precomputed impact deducts from net returns by hand calculation.
- gross returns, holdings, and turnover remain unchanged when only slippage
  impact is applied.
- impact series must align exactly to the backtester return index.
- missing, duplicate, unsorted, or extra dates in the impact series raise.
- missing impact values on dates with trades raise by default.
- `portfolio_notional` is required and cannot be derived from normalized
  `initial_capital`.
- lagged rolling dollar volume cannot use same-day or future volume.
- missing volume, zero volume, stale volume, warm-up capacity, and non-positive
  lagged dollar volume raise by default.
- participation above cap raises by default.
- applying volume-aware slippage with positive fixed-bps slippage raises until
  a combined-model policy exists.
- assumptions record model names, parameters, lag, notional, price/volume
  policy, missing/stale policy, cap policy, and whether impact was applied to
  returns.
- metrics and report helpers can distinguish transaction costs, fixed-bps
  slippage, volume-aware candidate slippage, and total trading impact.
- generated-output wording remains synthetic or local-fixture diagnostic and
  does not claim profitability, execution realism, or trading readiness.
- no imports or configuration are added for downloads, vendor APIs,
  credentials, broker modules, order systems, live/paper trading, or LEAN
  runtime execution.

## 10. Required Experiment-Log And Report Fields

Any future generated output or experiment log that includes volume-aware
slippage must record:

- `slippage_model`.
- `volume_aware_slippage_mode`.
- whether candidate impact was applied to returns.
- `portfolio_notional`.
- price field used for dollar volume.
- volume adjustment policy.
- rolling dollar-volume window and minimum-period rule.
- liquidity lag rule and liquidity reference date policy.
- stale-volume policy and `max_volume_age`, if used.
- base slippage bps and participation slope bps.
- maximum participation cap.
- participation-above-cap policy.
- missing, zero, stale, unestimated, rejected, clipped, and capped trade
  counts.
- maximum participation by date and overall.
- total fixed transaction-cost impact.
- total fixed-bps slippage impact.
- total volume-aware candidate slippage impact.
- total trading-cost impact.
- zero-cost or zero-slippage diagnostic flags.
- data scope: synthetic, committed fixture, or user-provided local CSV.
- caveats that the estimate is simulated research accounting, not execution
  evidence, not trading advice, and not a profitability claim.

For user-provided local CSV work, these fields supplement the readiness audit.
They do not replace provenance, schema, adjustment, universe, benchmark,
sample-split, issue-register, or experiment-handoff requirements.

## 11. Non-Goals

- No source-code implementation in this stage.
- No tests, research scripts, generated reports, loaders, backtester, metrics,
  factor logic, diagnostics behavior, or LEAN code changes in this stage.
- No integration of volume-aware slippage into `run_long_only_backtest()` in
  this stage.
- No real data, user-provided CSV loading, data downloads, vendor APIs,
  credentials, request clients, or brokerage/account integration.
- No live trading, paper trading, order routing, order execution, fill model,
  account handling, or production deployment.
- No market-impact calibration or claim that participation-based slippage is
  realistic.
- No performance, robustness, tradeability, or profitability claim.
- No silent fill, forward-fill, backward-fill, interpolation, clipping, or
  zero-slippage fallback for missing or invalid liquidity.

## 12. Recommended Next PR-Sized Stage

After this design is reviewed and merged, the next safe stage should be a
documentation-only backtester integration test plan.

Expected scope:

- define the exact deterministic test cases for an eventual
  `apply_precomputed_impact` implementation.
- specify the minimal API shape for passing a precomputed volume-aware slippage
  impact series and audit metadata.
- keep source code, tests, research scripts, generated reports, loaders,
  backtester behavior, metrics behavior, and diagnostics behavior unchanged.

Stop conditions for that next stage:

- any ambiguity about date alignment, missing/stale volume, double-counting
  fixed-bps slippage, or report fields.
- any need for real data, vendor APIs, credentials, brokerage, live/paper
  trading, order execution, or profitability language.

## 13. Final Recommendation

Do not integrate volume-aware slippage into `run_long_only_backtest()` yet.

If this design is accepted, the first future implementation should use an
explicit precomputed-impact boundary, keep diagnostic-only mode as the default,
reject unsafe missing/zero/stale liquidity and excessive participation by
default, and update reports and experiment logs only after deterministic tests
prove the accounting and audit fields.
