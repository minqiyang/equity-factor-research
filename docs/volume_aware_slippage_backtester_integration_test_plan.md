# Volume-Aware Slippage Backtester Integration Test Plan

Date: 2026-06-11

## Status: Historical / Superseded In Part

This test plan is retained as provenance for the reviewed precomputed-impact
implementation. The required first-path accounting, validation, metadata, and
guardrail checks have since been implemented in `src/backtest/portfolio.py` and
covered by `tests/test_backtest_portfolio.py` and
`tests/test_volume_aware_slippage.py`.

The remaining live guidance applies only to future changes beyond the current
precomputed-impact boundary, such as any internal OHLCV/rolling-volume model,
generated-output refresh, or broader real-data interpretation. Those changes
still need a separate scoped PR and explicit no-trading/no-performance caveats.

This is a documentation-only test plan for any future implementation that
would integrate the existing diagnostic-only volume-aware slippage helper into
the simulated local backtester.

This stage does not modify source code, tests, research scripts, generated
reports, loaders, backtester behavior, metrics behavior, factor logic,
diagnostics behavior, LEAN code, data access, execution behavior, or strategy
behavior. It does not fetch data, download data, add vendor APIs, add
credentials, add live trading, add paper trading, add brokerage integration,
add order execution, or claim profitability.

## 1. Purpose

The merged integration design recommends keeping volume-aware slippage
diagnostic-only by default and, if later approved, applying only a reviewed
precomputed `portfolio_slippage_impact` series to simulated net returns.

This test plan defines the test coverage that must exist before any future
implementation changes `run_long_only_backtest()`, metrics, report helpers, or
experiment-log writers for volume-aware slippage.

The goal is not to prove execution realism. The goal is to make any future
accounting change deterministic, date-aligned, separately inspectable, and hard
to over-interpret.

## 2. Current Evidence

| Artifact | Existing coverage or boundary |
| --- | --- |
| `docs/volume_aware_slippage_backtester_integration_design.md` | Recommends `diagnostic_only` as default and `apply_precomputed_impact` as the only acceptable first integration shape. |
| `src/backtest/portfolio.py` | Current `BacktestResult` includes `returns`, `gross_returns`, `holdings`, `turnover`, `transaction_costs`, `slippage_costs`, `total_trading_costs`, `metrics`, and `assumptions`. |
| `src/backtest/metrics.py` | Current metrics can report total transaction-cost impact, total slippage impact, and total trading-cost impact. |
| `src/backtest/slippage.py` | Current helper returns `VolumeAwareSlippageDiagnostics` with trade weights, lagged rolling dollar volume, trade notional, participation, asset and portfolio candidate slippage impact, summary counts, parameters, and caveats. |
| `tests/test_backtest_portfolio.py` | Existing tests cover target-weight turnover, fixed transaction costs, fixed-bps slippage, zero-cost or zero-slippage diagnostics, missing held returns, benchmark missing-policy behavior, and forbidden imports. |
| `tests/test_volume_aware_slippage.py` | Existing tests cover hand-calculated candidate impact, lagged capacity, explicit notional, warm-up capacity, missing/zero liquidity, participation caps, invalid targets, invalid parameters, and forbidden imports. |

This plan does not replace the existing helper tests. It defines the additional
tests required before the helper's candidate impact can affect backtester
returns.

## 3. Required Unit Tests Before Implementation

A future code-changing PR must add or update deterministic unit tests before
or with implementation. The tests must use small synthetic panels with
hand-computable values.

Required unit tests for backtester accounting:

- `diagnostic_only` is the default mode and leaves `returns`, `equity_curve`,
  `slippage_costs`, and `total_trading_costs` unchanged from the current
  fixed-bps behavior.
- `apply_precomputed_impact` deducts an explicitly supplied aligned
  `volume_aware_slippage_impact` series from net returns by hand calculation.
- Applied volume-aware impact does not change `gross_returns`, `holdings`, or
  `turnover`.
- Applied volume-aware impact is separately inspectable from fixed transaction
  costs and fixed-bps slippage.
- Total trading impact equals fixed transaction-cost impact plus fixed-bps
  slippage impact plus applied volume-aware impact.
- Existing fixed-bps transaction-cost and fixed-bps slippage tests remain
  backward-compatible when no volume-aware impact is supplied.
- Positive fixed-bps slippage plus positive applied volume-aware impact raises
  by default until a combined-model policy is reviewed.
- Zero fixed-bps slippage plus applied volume-aware impact is not labeled as a
  no-slippage run; it is labeled as volume-aware candidate slippage applied.
- No applied volume-aware impact, or diagnostic-only volume-aware output, keeps
  the zero-slippage diagnostic flag visible.

Required unit tests for impact-series validation:

- Impact series index must exactly match the backtester return index.
- Missing dates, extra dates, duplicate dates, unsorted dates, or timezone
  mismatches raise before returns are calculated.
- Missing impact values raise by default on dates with non-zero turnover.
- Missing impact values on no-trade dates either raise by default or are
  accepted only under an explicit, tested `allow_no_trade_missing_impact`
  policy.
- Negative impact values raise unless a later reviewed design explicitly
  permits rebates or price improvement.
- Non-numeric, infinite, or non-finite impact values raise.
- Applied impact series name is normalized to a stable output field name.

Required unit tests for assumptions and audit metadata:

- Assumptions record `volume_aware_slippage_mode`.
- Assumptions record whether volume-aware impact was applied to returns.
- Assumptions record the volume-aware slippage model name and source.
- Assumptions record `portfolio_notional`, `window`, `volume_lag`,
  `base_slippage_bps`, `participation_slope_bps`, `max_participation`, price
  field, volume policy, missing-liquidity policy, stale-volume policy, and cap
  policy.
- Missing required diagnostic metadata raises when applying impact.
- Diagnostic-only metadata can be reported without affecting returns.

## 4. Required Integration Tests Before Implementation

Integration tests must prove that the helper output and the backtester
accounting boundary work together without making the backtester own OHLCV
semantics.

Required integration tests:

- Build a tiny synthetic target-weight panel, price panel, and volume panel.
- Call `calculate_volume_aware_slippage_diagnostics()` outside the backtester.
- Pass only the resulting aligned `portfolio_slippage_impact` series and audit
  metadata into the future backtester or wrapper.
- Verify hand-calculated net returns after deducting fixed transaction costs,
  fixed-bps slippage when allowed, and applied volume-aware impact.
- Verify the full `VolumeAwareSlippageDiagnostics` object remains available for
  audit reporting.
- Verify no internal backtester code path computes rolling dollar volume from
  price and volume panels in the first implementation.
- Verify generated report or experiment-log helpers can consume the audit
  fields without changing generated reports in the implementation PR unless
  explicitly scoped.
- Verify local-fixture smoke workflow behavior remains diagnostic-only unless
  a later generated-output refresh explicitly opts into the new mode.

Integration tests must be synthetic or committed-fixture only. They must not
load user-provided CSV files, fetch real data, call vendor APIs, use
credentials, connect to a broker, place orders, run LEAN, or imply live or
paper trading readiness.

## 5. Required Failure-Mode Tests

Failure-mode tests must be explicit and should assert error messages with the
invalid field or policy name.

Required failures:

- missing volume raises.
- zero volume in a required rolling window raises.
- non-positive lagged rolling dollar volume raises.
- incomplete rolling dollar-volume warm-up raises when a trade needs capacity.
- stale volume raises by default when liquidity reference age exceeds the
  configured maximum.
- invalid or missing `portfolio_notional` raises.
- target weights with missing values raise.
- target weights with negative weights raise.
- target weights with row sums above 1.0 raise unless a later design explicitly
  supports leverage.
- target weights, price, volume, and applied impact with mismatched indexes or
  columns raise.
- excessive participation above `max_participation` raises.
- positive fixed-bps slippage plus positive applied volume-aware impact raises
  by default.
- applied impact without required audit metadata raises.
- use of same-day or future volume in the helper remains blocked by tests.
- imports or configuration for data downloads, vendor APIs, credentials,
  brokerage, order systems, live/paper trading, or LEAN runtime execution are
  rejected by static import checks.

## 6. Expected Behavior By Edge Case

| Edge case | Expected default behavior |
| --- | --- |
| Missing volume | Raise before diagnostics are applied to returns; no fill, forward-fill, interpolation, or zero default. |
| Zero volume | Raise for traded cells when the required rolling window contains zero volume or lagged rolling dollar volume is non-positive. |
| Stale volume | Raise by default when liquidity reference age exceeds an explicit `max_volume_age`; optional `mark_unestimated` must be separately designed and tested. |
| Invalid notional | Raise when `portfolio_notional` is missing, non-numeric, non-finite, non-positive, or inferred from normalized `initial_capital=1.0`. |
| Invalid target weights | Raise for missing values, negative weights, leverage above 1.0, unaligned axes, or incompatible rebalance dates. |
| Excessive participation | Raise when participation exceeds `max_participation`; silent clipping is not allowed. |
| Incomplete rolling dollar-volume window | Raise when a non-zero trade needs warm-up capacity that is unavailable after lagging. |
| Missing impact value | Raise on trade dates by default; no silent zero-slippage fallback. |
| Extra or missing impact date | Raise before return calculation. |
| Positive fixed-bps plus positive volume-aware slippage | Raise by default to prevent hidden double counting. |

Optional future policies such as `mark_unestimated`, `exclude_trade`, or
`clip_to_cap` are out of scope for the first implementation unless a separate
design records their semantics and tests.

## 7. Zero-Slippage Diagnostic Mode

Tests must preserve the current diagnostic semantics while adding a future
volume-aware mode.

Expected behavior:

- `transaction_cost_bps=0.0` or `slippage_bps=0.0` remains visible in
  assumptions as a diagnostic simplification.
- `volume_aware_slippage_mode="diagnostic_only"` does not change net returns,
  `slippage_costs`, or `total_trading_costs`.
- Diagnostic-only candidate impact may be reported in audit fields but must not
  be included in `returns`, `equity_curve`, or total trading impact.
- `volume_aware_slippage_mode="apply_precomputed_impact"` with positive impact
  is not a no-slippage run even when fixed `slippage_bps=0.0`.
- Reports and experiment logs must distinguish "no applied slippage" from
  "applied volume-aware candidate slippage".

## 8. Separately Inspectable Cost And Slippage Components

Future tests must require separate inspection of:

- fixed transaction-cost impact.
- fixed-bps slippage impact.
- volume-aware candidate slippage impact.
- total trading-cost impact.
- diagnostic-only candidate volume-aware impact, when not applied.

The future implementation should not overload the existing `slippage_costs`
field in a way that hides whether impact came from fixed-bps slippage or
volume-aware slippage.

Recommended future field shape:

- keep `transaction_costs` for fixed transaction-cost impact.
- keep `slippage_costs` for backward-compatible fixed-bps slippage impact, or
  clearly document any rename before implementation.
- add `volume_aware_slippage_costs` for applied candidate volume-aware impact.
- keep `total_trading_costs` as the sum of all applied cost/slippage impact
  components.
- add metrics for each total component.

## 9. Future Backtester Result And Audit Fields

If a later implementation applies precomputed volume-aware impact, future
`BacktestResult` or wrapper outputs should provide:

- `volume_aware_slippage_costs`: applied volume-aware impact by date.
- `volume_aware_slippage_diagnostics`: optional preserved diagnostic object or
  a stable audit summary reference.
- `total_trading_costs`: total applied transaction-cost plus slippage impact.
- `metrics["total_volume_aware_slippage_cost_impact"]`.
- `metrics["total_trading_cost_impact"]` including the applied volume-aware
  component.
- `assumptions["volume_aware_slippage_mode"]`.
- `assumptions["volume_aware_slippage_applied_to_returns"]`.
- `assumptions["volume_aware_slippage_model"]`.
- `assumptions["volume_aware_slippage_source"]`.
- `assumptions["portfolio_notional"]`.
- `assumptions["volume_aware_price_field"]`.
- `assumptions["volume_policy"]`.
- `assumptions["volume_lag"]`.
- `assumptions["rolling_dollar_volume_window"]`.
- `assumptions["stale_volume_policy"]`.
- `assumptions["max_volume_age"]`, if used.
- `assumptions["max_participation"]`.
- `assumptions["participation_above_cap_policy"]`.
- `assumptions["missing_or_zero_liquidity_policy"]`.
- `assumptions["zero_cost_or_slippage_is_diagnostic"]`.

These fields must be stable enough for generated reports and experiment logs
to consume without guessing model semantics.

## 10. Required Experiment-Log And Report Fields

Before generated outputs are refreshed for any implemented integration, tests
or review checks must require these fields:

- slippage model names for fixed-bps and volume-aware components.
- `volume_aware_slippage_mode`.
- whether volume-aware impact was applied to returns.
- `portfolio_notional`.
- price field used for dollar volume.
- volume adjustment policy.
- rolling dollar-volume window and minimum-period rule.
- volume lag and liquidity-reference-date policy.
- stale-volume policy and `max_volume_age`, if used.
- base slippage bps.
- participation slope bps.
- maximum participation cap.
- participation-above-cap policy.
- missing-capacity, zero-capacity, stale-capacity, incomplete-window,
  unestimated, rejected, clipped, and cap-breach counts.
- maximum participation by date and overall.
- total fixed transaction-cost impact.
- total fixed-bps slippage impact.
- total applied volume-aware slippage impact.
- total diagnostic-only candidate volume-aware impact, if not applied.
- total trading-cost impact.
- zero-cost and zero-slippage diagnostic flags.
- data scope: synthetic, committed fixture, or user-provided local CSV.
- caveats that the output is simulated research accounting, not execution
  evidence, not investment advice, and not a profitability claim.

For user-provided local CSV work, these fields supplement the readiness audit
and do not replace provenance, schema, adjustment, universe, benchmark,
sample-split, issue-register, or experiment-handoff requirements.

## 11. Guardrail Tests

Future implementation tests must include guardrails that fail if the
integration introduces:

- real data downloads.
- vendor APIs or request clients.
- credentials, tokens, `.env` readers, account IDs, or private keys.
- broker or brokerage integrations.
- live trading or paper trading modes.
- order routing, order placement, fill models, or execution systems.
- LEAN runtime execution.
- generated report wording that claims profitability, execution realism,
  robustness, tradeability, or investment suitability.

Static import checks should continue to scan the touched backtester, metrics,
helper, and workflow modules for forbidden imports or terms.

## 12. Stop Conditions

Implementation must not proceed if any of these are true:

- PR #98 or this test-plan PR is not merged.
- The future PR would need real data, user-provided CSV interpretation,
  downloads, vendor APIs, credentials, brokerage, live/paper trading, order
  execution, or LEAN runtime execution.
- The impact series cannot be aligned exactly to backtester return dates.
- Missing, zero, stale, or incomplete volume policy is ambiguous.
- `portfolio_notional` would be inferred from normalized `initial_capital`.
- Same-day or future volume would be used for a pre-trade slippage estimate.
- Positive fixed-bps slippage and positive volume-aware slippage would both be
  applied without an explicit combined-model design.
- Reports or experiment logs cannot separately identify fixed transaction
  costs, fixed-bps slippage, volume-aware slippage, and total trading impact.
- Any test would need to be weakened, skipped, or removed to pass.
- Wording would imply profitability, execution realism, live/paper trading
  readiness, or investment advice.

## 13. Recommended Next PR-Sized Stage

After this test plan is reviewed and merged, the next safe stage can be a
narrow code-changing implementation PR for the precomputed-impact boundary,
but only if the implementation includes the required deterministic tests in
the same PR and keeps generated reports unchanged.

Expected scope for that later implementation:

- add a minimal explicit API for `apply_precomputed_impact` or an equivalent
  wrapper.
- add deterministic unit and integration tests from this plan.
- add future result/audit fields needed for separate inspection.
- keep helper calculation outside the backtester.
- keep `diagnostic_only` as default.
- do not refresh generated reports until a later generated-output review PR.

Stop before that stage if the reviewed API shape, audit fields, or
double-counting policy are still ambiguous.

## 14. Final Recommendation

Do not integrate volume-aware slippage into `run_long_only_backtest()` in this
stage.

Use this plan as the acceptance checklist for any future implementation. The
first implementation should remain synthetic-only, precomputed-impact based,
diagnostic-only by default, and fully caveated as simulated research accounting
rather than execution evidence.
