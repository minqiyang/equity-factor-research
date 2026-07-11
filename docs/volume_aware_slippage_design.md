# Volume-Aware Slippage Design

Date: 2026-06-09

## Status: Historical / Superseded In Part

The original design remains useful for liquidity, lag, participation, and
missing-volume policy. Current code now exposes drift-aware per-asset trade
weights from `BacktestResult` and accepts them through
`calculate_volume_aware_slippage_from_trade_weights()`. The older
`calculate_volume_aware_slippage_diagnostics()` target-weight interface remains
as a compatibility path and records that its trades were derived from
consecutive targets. Volume-aware impact is still external and precomputed;
the backtester default remains diagnostic-only.

This is a documentation-only design gate for a possible future
volume-aware slippage model in the local Python research pipeline.

It does not modify source code, tests, research scripts, generated reports,
CSV loaders, factor formulas, diagnostics, metrics, portfolio construction,
LEAN code, data access, execution behavior, or strategy behavior. It does not
fetch data, download data, add vendor APIs, add credentials, add live trading,
add paper trading, add brokerage integration, add order execution, or claim
profitability.

## 1. Purpose

The current local backtester supports explicit transaction costs and
fixed-basis-point slippage on target-weight turnover. That is useful for
synthetic diagnostics, but it does not use volume, dollar volume, liquidity
capacity, or participation-rate assumptions.

The purpose of this design is to define the policy that must exist before any
future volume-aware slippage helper, backtester extension, generated-output
refresh, or local CSV interpretation uses volume data for cost assumptions.

The goal is not realistic execution modeling. The goal is to make any future
volume-based assumption:

- point-in-time safe.
- deterministic and testable.
- explicit about data, capital, lag, and missing-value assumptions.
- clearly caveated as simulated research accounting, not market evidence.

## 2. Current Evidence

| Area | Evidence | Current status |
| --- | --- | --- |
| Project requirement | `PROJECT_SPEC.md` | Costs, slippage, turnover, and execution assumptions must be explicit. |
| Fixed-bps slippage | `src/backtest/portfolio.py`, `src/backtest/metrics.py`, `tests/test_backtest_portfolio.py` | Implemented and tested as fixed basis points on target-weight turnover. |
| Fixed-bps design record | `docs/simulated_slippage_cost_assumption_design.md` | States that volume-aware slippage requires a separate design. |
| Latest checkpoint | `docs/post_slippage_cost_checkpoint.md` | Recommends a documentation-only volume-aware slippage design before implementation. |
| OHLCV policy | `docs/volume_ohlcv_schema_plan.md` | Defines local-only OHLCV validation and volume adjustment risks. |
| Liquidity planning | `docs/liquidity_dollar_volume_universe_plan.md` | Defines rolling ADV and rolling dollar-volume timing, missing-value, and zero-volume risks. |
| Real-data gate | `docs/real_data_readiness_audit.md` | Requires data provenance, adjustment policy, costs, slippage, benchmark, and sample-split evidence before interpretation. |
| LEAN planning | `docs/quantconnect_lean_plan.md` | Distinguishes local target-weight turnover friction from LEAN order/fill-level fees and slippage. |

## 3. Non-Goals

- No implementation in this stage.
- No changes to `src/backtest/portfolio.py`, `src/backtest/metrics.py`,
  `src/features/`, `src/data/`, `research/`, `reports/`, `tests/`, or
  `lean/`.
- No user-provided or real-market data.
- No vendor, API, `requests`, `yfinance`, Alpaca, CCXT, credential, token,
  `.env`, account, or private-key logic.
- No live trading, paper trading, brokerage integration, order execution,
  account handling, fill simulation, or production deployment.
- No claim that a volume-aware rule is realistic, calibrated, tradeable,
  robust, profitable, or suitable for execution.
- No automatic forward-fill, backward-fill, zero-fill, interpolation,
  benchmark substitution, corporate-action repair, or liquidity repair.
- No market-impact model unless a later separate design justifies it.

## 4. Definitions

| Term | Design meaning |
| --- | --- |
| Observation date | Date attached to a local OHLCV row. |
| Rebalance date | Date on which the local backtester sets target weights. |
| Liquidity reference date | Last observation date whose volume may be used for a rebalance-date cost estimate. |
| Target-weight turnover | Current local turnover convention: `sum(abs(target_weight - drifted_pretrade_weight))`. |
| Trade weight | Per-asset absolute change from drifted pre-trade weight to target weight on a rebalance date. |
| Portfolio notional | Explicit assumed portfolio dollar value used only to scale trade weights into dollar notional for volume-aware diagnostics. |
| Dollar volume | Price times share volume under an explicitly documented price and volume adjustment policy. |
| Participation rate | Estimated trade notional divided by lagged dollar-volume capacity. |
| Volume-aware slippage | A deterministic simulated friction estimate that uses lagged liquidity information. |
| Market impact | A broader execution model involving order size, spread, fills, timing, and price response; still deferred. |

## 5. Required Future Inputs

Any future volume-aware slippage stage must start from validated local or
synthetic panels. It must not fetch or infer missing market data.

Required inputs:

- explicit per-asset trade weights from the drift-aware portfolio path, or
  target weights only for the compatibility diagnostic path.
- price panel used by the backtester.
- local OHLCV or volume panel validated by reviewed loaders.
- explicit price field for dollar volume, such as `close` or
  `adjusted_close`.
- explicit volume policy: raw share volume, adjusted volume, or unknown.
- explicit rolling window and minimum-period policy.
- explicit portfolio notional in the same currency as dollar volume.
- explicit rebalance dates and signal lag.

The current normalized backtester default `initial_capital=1.0` is not by
itself a market-dollar capital assumption. A future volume-aware helper must
not treat that default as a real tradable notional. If dollar-volume capacity
is used, the helper must require an explicit `portfolio_notional` or equivalent
documented scale.

## 6. Date Alignment And Lag Policy

Default rule:

```text
Volume observations through date t may affect a slippage estimate only for a
rebalance on a later date.
```

For the current backtester convention, the default future policy should be:

```text
liquidity_reference_date(rebalance_date) =
    previous available OHLCV observation date before the rebalance date
```

Same-day volume is not allowed for pre-trade slippage estimates by default.
Using same-day volume would usually mean using information that was not known
before the trade. A later stage may allow same-day volume only if it records a
reviewed execution assumption proving that the volume information would have
been available before the simulated execution time.

Rolling dollar-volume features must be computed using only observations at or
before the liquidity reference date:

```text
rolling_dollar_volume[i, t] =
    rolling_mean(price[i, s] * volume[i, s], window=N)
    for s <= liquidity_reference_date(t)
```

No future volume, future price, future universe membership, future returns, or
same-period target returns may be used.

## 7. Candidate Future Accounting Semantics

The candidate formula below is now implemented as a standalone diagnostic
contract. It is still not an order-fill or calibrated market-impact model.

For each rebalance date `t` and asset `i`:

```text
trade_weight[i, t] = abs(target_weight[i, t] - drifted_pretrade_weight[i, t])
trade_notional[i, t] = portfolio_notional[t] * trade_weight[i, t]
participation[i, t] = trade_notional[i, t] / lagged_rolling_dollar_volume[i, t]
```

A future deterministic slippage estimate could then use a simple documented
function, for example:

```text
asset_slippage_bps[i, t] =
    base_slippage_bps + participation_slope_bps * participation[i, t]

asset_slippage_impact[i, t] =
    trade_weight[i, t] * asset_slippage_bps[i, t] / 10000

portfolio_slippage_impact[t] =
    sum(asset_slippage_impact[i, t])
```

The diagnostic impact is a fraction of post-return portfolio value because the
trade weights are measured immediately before the close-time rebalance. Its
metadata therefore records
`return_impact_basis="post_return_portfolio_value"`. When applied to a period
return, the backtester converts it to beginning-period basis by multiplying by
`1 + gross_return[t]`.

The function and parameter names make clear that this is a simulated
liquidity-friction estimate, not a calibrated market-impact model.

## 8. Missing, Zero, And Stale Volume Policy

Default future behavior must be strict:

- Missing price or volume values are not filled.
- Missing rolling dollar volume blocks a volume-aware slippage estimate by
  default.
- Zero volume is a valid loader value but not valid liquidity capacity.
- Zero lagged rolling dollar volume must not be used as a denominator.
- Stale volume and low coverage should be reported before any estimate is
  interpreted.
- Any optional fallback policy must be explicit, non-default, documented, and
  tested.

Recommended future default for code:

```text
missing_or_zero_liquidity_policy = "raise"
```

Optional future diagnostic modes, if ever added, should be named explicitly,
such as `"mark_unestimated"` or `"exclude_trade"`. They must not silently turn
missing or zero liquidity into zero slippage, average liquidity, or filled
volume.

## 9. Participation Caps And Thresholds

Participation caps are risk controls and should not be hidden inside the
slippage formula.

Future code should separately record:

- maximum allowed participation rate.
- count of trades above the cap.
- symbols and dates affected by the cap.
- whether capped trades are rejected, marked unestimated, or clipped.

Default future behavior should be conservative:

```text
participation_above_cap_policy = "raise"
```

Silent clipping is not acceptable. If a later reviewed stage allows clipping,
the output must report the clipped count, affected symbols/dates, and the cap
used.

Thresholds and caps must not be tuned after reviewing simulated performance
without being recorded as a parameter-sensitivity or validation issue.

## 10. Price And Volume Adjustment Policy

Dollar volume is only meaningful when price and volume conventions are
compatible.

Allowed future policies:

- raw close times raw share volume, when both policies are documented.
- adjusted close times adjusted volume, if a source explicitly provides and
  documents adjusted volume.
- another documented convention only after a readiness audit records why it is
  compatible.

Risky or blocked policies:

- adjusted close times raw volume when split treatment is unknown.
- unknown price adjustment policy.
- unknown volume adjustment policy.
- mixing benchmark currency or asset currency without documentation.

If the adjustment policy is unknown, a future workflow may run loader or
diagnostic checks, but it must not interpret volume-aware slippage estimates.

## 11. Reporting And Experiment Logging

Any future generated output or experiment log that uses volume-aware slippage
must record:

- slippage model name.
- slippage parameters.
- portfolio notional or capital scale.
- price field used for dollar volume.
- volume policy.
- rolling window and minimum periods.
- liquidity lag rule.
- missing and zero-volume policy.
- participation cap and cap policy.
- count of missing, zero, stale, unestimated, rejected, or capped trades.
- whether the run is synthetic, committed fixture, or user-provided local CSV.
- caveat that the estimate is simulated research accounting, not execution
  evidence.

For user-provided local CSV work, these fields supplement the readiness audit
and `EXPERIMENT_LOG.md` gates. They do not replace provenance, adjustment,
universe, benchmark, sample-split, or issue-register requirements.

## 12. Required Future Tests

The first code-changing stage after this design should include deterministic
synthetic tests for:

- no look-ahead from future volume into the current rebalance.
- previous-observation liquidity reference date selection.
- rolling-window warm-up and `min_periods` behavior.
- missing price or volume raising by default.
- zero volume and zero rolling dollar volume raising by default.
- no forward-fill, backward-fill, zero-fill, or interpolation.
- explicit portfolio notional being required for dollar-volume scaling.
- hand-calculated participation rate and slippage impact.
- participation above cap raising by default.
- assumptions recording model name, parameters, lag, notional, field choices,
  and missing-data policies.
- existing fixed-bps slippage behavior remaining backward-compatible.
- no imports from data download libraries, credential paths, broker modules,
  order systems, or LEAN runtime modules.

## 13. Alignment With Current Modules

| Module or artifact | Future interaction |
| --- | --- |
| `src/backtest/portfolio.py` | Should not consume volume-aware slippage until a reviewed implementation defines inputs, notional scale, lag, missing policy, and output fields. |
| `src/backtest/metrics.py` | May receive a total slippage impact series only after the calculation policy is tested. |
| `src/features/liquidity.py` | Rolling ADV and rolling dollar-volume helpers can inform eligibility and diagnostics but should not be treated as execution evidence. |
| `src/data/csv_loader.py` | Loader validation remains separate from slippage interpretation; zero volume is loader-valid but capacity-invalid. |
| `research/` | Synthetic demos may exercise wiring only after implementation, with no performance interpretation. |
| `reports/experiment_logs/` | Must record all volume-aware slippage assumptions if generated outputs are refreshed. |
| `docs/real_data_readiness_audit.md` | Remains mandatory before user-provided local CSV interpretation. |
| `docs/quantconnect_lean_plan.md` | LEAN order/fill-level slippage remains a separate platform semantics problem. |

## 14. Risks

- Using same-day volume and introducing look-ahead bias.
- Treating normalized capital as real tradable notional.
- Mixing adjusted prices with raw volume.
- Dividing by zero or stale liquidity.
- Silently filling missing volume.
- Hiding rejected or capped trades.
- Double-counting fixed-bps slippage and volume-aware slippage.
- Treating synthetic fixtures as execution evidence.
- Tuning participation caps or slopes to improve results.
- Comparing local target-weight friction with LEAN order fills without
  recording semantic differences.

## 15. Recommended Future PR-Sized Stages

1. Add a narrow synthetic-only volume-aware slippage helper with deterministic
   tests, but do not integrate it into the backtester yet if notional and
   policy questions remain.
2. If the helper is reviewed, add a synthetic/local-fixture smoke diagnostic
   that reports participation and unestimated/capped counts only, without
   interpreting performance.
3. Only after the helper and diagnostics are reviewed, decide whether the
   local backtester should accept a volume-aware slippage impact series or
   callback.
4. Refresh generated synthetic reports only in a separate generated-output
   review stage if backtester behavior changes.
5. Keep user-provided local CSV interpretation blocked until readiness gates,
   experiment-log requirements, and data provenance are complete for a
   specific dataset.

## 16. Final Recommendation

The next implementation stage, if this design is reviewed and merged, should
be a synthetic-only helper or diagnostic stage that calculates lagged
participation and candidate slippage impact on deterministic fixtures.

It should not fetch data, load user files, change backtester net returns,
modify generated reports, connect to LEAN runtime systems, add broker/order
logic, or make performance or profitability claims.
