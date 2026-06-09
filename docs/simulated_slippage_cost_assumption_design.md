# Simulated Slippage And Cost Assumption Design

Date: 2026-06-09

This is a documentation-only design for future simulated transaction-cost and
slippage handling in the local Python backtester.

It does not modify source code, tests, research scripts, generated reports,
CSV loaders, factor formulas, diagnostics, metrics, portfolio construction,
data access, execution assumptions, or performance claims. It does not fetch
data, download data, add vendor APIs, add credentials, add live trading, add
paper trading, add brokerage integration, add order execution, or claim
profitability.

## 1. Purpose

The project specification requires transaction costs, slippage, turnover, and
execution assumptions to be explicit before simulated results are interpreted.

The current local backtester already applies a simple fixed basis-point cost to
target-weight turnover. That is useful for first-pass synthetic diagnostics,
but it does not separately model slippage or market impact. This design defines
the next reviewed boundary before any future source-code change expands cost
handling.

The goal is not to make execution realistic. The goal is to make assumptions
visible, testable, and hard to over-interpret.

## 2. Current Evidence

| Area | Current evidence | Current status |
| --- | --- | --- |
| Backtester cost path | `src/backtest/portfolio.py` | `transaction_cost_bps` is applied to target-weight turnover and deducted from portfolio return. |
| Turnover semantics | `tests/test_backtest_portfolio.py` | Tests cover target-weight turnover and cost deduction. |
| Project requirement | `PROJECT_SPEC.md` | Costs, slippage, turnover, and execution assumptions must be explicit. |
| Readiness gate | `docs/real_data_readiness_audit.md` | Backtest-like runs must state transaction cost model, slippage model, turnover model, rebalance frequency, execution timing, and benchmark choice. |
| LEAN planning | `docs/quantconnect_lean_plan.md` | Local turnover costs and LEAN order-level fees/slippage are different artifacts. |
| Latest checkpoint | `docs/post_local_csv_fixture_audit_rehearsal_checkpoint.md` | Recommends this documentation-only design before any cost/slippage implementation. |

## 3. Current Local Backtester Semantics

Current simplified assumptions:

- Signals are lagged before rebalance use.
- Target holdings set on date `t` affect returns starting on the next
  available price row.
- Turnover is target-weight turnover:

```text
sum(abs(target_weight[t] - previous_target_weight[t]))
```

- Transaction cost impact is:

```text
turnover[t] * transaction_cost_bps / 10000
```

- The cost impact is deducted from the simulated return on the rebalance date.
- Slippage is not separately represented.
- Market impact is not represented.

This is a deterministic research accounting convention, not an order-fill
model and not execution evidence.

## 4. Non-Goals

- No source-code implementation in this stage.
- No changes to `src/backtest/portfolio.py`, `src/backtest/metrics.py`,
  `src/features/`, `src/data/`, `research/`, `reports/`, or `tests/`.
- No user-provided or real-market data.
- No downloads, vendor APIs, `requests`, `yfinance`, Alpaca, CCXT, or
  credential logic.
- No live trading, paper trading, brokerage integration, order execution,
  account handling, fill simulation, or production deployment.
- No LEAN runtime implementation.
- No claims that a cost or slippage setting is realistic.
- No performance, robustness, tradeability, or profitability claim.

## 5. Definitions

| Term | Design meaning |
| --- | --- |
| Transaction cost | Explicit fee-like cost applied by a deterministic simulated rule. |
| Slippage | Extra simulated price-impact or execution-friction assumption, separate from transaction cost. |
| Market impact | More complex relationship between order size, liquidity, spread, volume, and price movement; deferred until separately justified. |
| Turnover | Current local target-weight turnover unless a later reviewed stage defines drift-adjusted or order-notional turnover. |
| Cost impact | Fractional return reduction from simulated transaction cost. |
| Slippage impact | Fractional return reduction from simulated slippage. |
| Total trading impact | Future combined cost impact plus slippage impact, if implemented. |
| Zero-cost diagnostic | A run with transaction cost set to zero, allowed only when labeled diagnostic. |
| No-slippage diagnostic | A run with separate slippage absent or set to zero, allowed only when labeled diagnostic. |

## 6. Design Principles

Future implementation should follow these principles:

1. Keep costs and slippage explicit in assumptions.
2. Preserve existing date alignment: signals are known before rebalance use,
   and target holdings affect later returns under the current backtester
   convention.
3. Do not change factor calculations, signal ranking, or universe selection as
   part of the first cost/slippage implementation.
4. Do not hide zero-cost or no-slippage settings. They are diagnostics only.
5. Keep transaction cost and slippage as separate reported series if slippage
   is implemented.
6. Do not infer realistic market impact from synthetic fixtures.
7. Do not use future volume, future returns, future universe membership, or
   future benchmark data in any cost or slippage estimate.
8. Treat volume-aware models as a later stage requiring additional policy and
   tests.

## 7. Proposed First Implementation Boundary

The first code stage, if approved later, should be narrower than a full
execution model.

Likely future API addition:

```text
run_long_only_backtest(
    ...,
    transaction_cost_bps: float = 0.0,
    slippage_bps: float = 0.0,
)
```

Possible future output additions:

- `transaction_costs`: existing fee-like cost impact series.
- `slippage_costs`: separate slippage impact series.
- `total_trading_costs`: combined impact series, if useful.
- `assumptions["slippage_bps"]`.
- `assumptions["slippage_model"] = "fixed_bps_on_target_weight_turnover"`.
- `assumptions["cost_model"] = "fixed_bps_on_target_weight_turnover"`.
- `assumptions["zero_cost_or_slippage_is_diagnostic"] = True` when either
  component is zero.

The first implementation should not require OHLCV data, spreads, order books,
intraday data, broker fills, or external data.

## 8. First Implementation Semantics

Recommended first semantics:

```text
transaction_cost_impact[t] = turnover[t] * transaction_cost_bps / 10000
slippage_impact[t] = turnover[t] * slippage_bps / 10000
net_return[t] = gross_return[t] - transaction_cost_impact[t] - slippage_impact[t]
```

Rationale:

- It is deterministic and easy to test by hand.
- It preserves the current target-weight turnover model.
- It makes slippage visible without claiming realistic execution.
- It avoids introducing real-data or broker-fill dependencies.

This model is still simplified. It should be described as fixed-basis-point
turnover friction, not a real order-book or market-impact model.

## 9. Deferred Volume-Aware Slippage

Volume-aware or liquidity-aware cost modeling should remain deferred until a
separate design stage defines:

- required OHLCV inputs.
- whether volume is raw, adjusted, or user-reviewed.
- participation-rate assumptions.
- how dollar volume is aligned and lagged.
- what happens on zero-volume, missing-volume, stale-volume, and low-coverage
  dates.
- whether liquidity caps are used and how they avoid parameter mining.
- how the model avoids using future volume or future returns.
- how outputs are caveated as simulated research, not execution evidence.

No current synthetic fixture can prove a volume-aware slippage model is
realistic.

## 10. Market-Impact Boundary

Market impact is not part of the first implementation.

A future market-impact design would need to address:

- spread or liquidity proxy availability.
- order size relative to daily volume.
- execution timing.
- partial fills or unfilled orders, if modeled.
- caps or rejected trades.
- benchmark mismatch.
- sensitivity to assumptions.
- whether the model is calibrated or purely hypothetical.

Without those inputs, market-impact language should remain caveated as a risk
or limitation.

## 11. Experiment Logging Requirements

Any future backtest-like report or experiment log should record:

- transaction cost model name.
- transaction cost parameters.
- slippage model name.
- slippage parameters.
- whether either component is zero.
- turnover model.
- rebalance frequency.
- execution timing.
- benchmark choice.
- whether the run is synthetic, committed fixture, or user-provided local CSV.
- caveat that zero-cost or no-slippage settings are diagnostics only.
- known limitations of fixed-basis-point turnover friction.

For user-provided local CSV work, these fields supplement the existing
readiness audit and `EXPERIMENT_LOG.md` requirements. They do not replace the
data-provenance, adjustment-policy, universe, benchmark, and sample-split gates.

## 12. Required Future Tests

If this design is implemented later, tests should cover:

- non-negative `slippage_bps` validation.
- hand-calculated one-period cost and slippage deduction.
- zero transaction cost with positive slippage.
- positive transaction cost with zero slippage.
- both components positive.
- first-row cost and slippage when `signal_lag_periods=0`.
- metric total return uses `initial_capital`, including first-row impacts.
- assumptions record both cost and slippage model names.
- existing `transaction_cost_bps` behavior remains backward-compatible.
- no source imports from data download libraries, credential paths, broker
  modules, order systems, or LEAN runtime modules.

## 13. Alignment With Current Modules

| Module or artifact | Future interaction |
| --- | --- |
| `src/backtest/portfolio.py` | First implementation can extend existing turnover-cost accounting without changing factor or selection logic. |
| `src/backtest/metrics.py` | Metrics should receive total trading impact or both components only after a reviewed code stage defines the data shape. |
| `research/` synthetic demos | Should label zero-cost or no-slippage runs as diagnostics and record assumptions if reports/logs are regenerated. |
| `reports/experiment_logs/` | JSON sidecars should include explicit cost and slippage fields for future generated outputs. |
| `docs/real_data_readiness_audit.md` | Remains the gate before user-provided local CSV interpretation. |
| `docs/quantconnect_lean_plan.md` | LEAN order-level fees and slippage remain separate from local target-weight turnover friction. |

## 14. Risks

- Treating fixed-basis-point friction as realistic execution evidence.
- Hiding zero-slippage assumptions inside a generic cost field.
- Adding volume-aware logic before volume policy and lag rules are reviewed.
- Double-counting costs if transaction cost and slippage are not reported
  separately.
- Changing existing synthetic reports without a deliberate generated-output
  review.
- Comparing local and LEAN results without acknowledging order-level fill,
  fee, cash, and slippage differences.
- Over-interpreting cost-adjusted synthetic results as market evidence.

## 15. Recommended Next Stages

1. Implement a narrow fixed-bps slippage extension in the local backtester with
   deterministic tests only.
2. Add or update synthetic report/log fields only in a separate stage if the
   implementation changes generated outputs.
3. Consider a volume-aware slippage design only after fixed-bps behavior is
   reviewed and if the required OHLCV policies are explicit.
4. Keep user-provided local CSV interpretation blocked until readiness gates
   are completed for a specific dataset.

Stop any future stage if it requires real data, downloads, vendor credentials,
live or paper trading, brokerage integration, order execution, or profitability
claims.
