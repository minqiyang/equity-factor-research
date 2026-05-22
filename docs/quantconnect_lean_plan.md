# QuantConnect / LEAN Implementation Plan

This document plans a first QuantConnect/LEAN version of the local equity factor research workflow. It is a plan only. Do not implement the LEAN strategy in this step.

The goal is to translate the local, auditable research logic into a platform-grade LEAN backtest while preserving the same research standards: no live trading, no brokerage connection, no look-ahead bias, explicit costs, explicit slippage, and clear date alignment.

## 1. Local Logic to LEAN Mapping

| Local component | Current local role | LEAN mapping |
| --- | --- | --- |
| `features.momentum.calculate_12_1_momentum` | Computes 12-1 momentum as `price[t - skip] / price[t - lookback] - 1` with explicit shifting. | Maintain a per-symbol rolling adjusted close history or use `History` / warm-up data. Compute the same score only from completed daily bars. |
| `backtest.portfolio.run_long_only_backtest` | Selects top-ranked assets, equal-weights them, applies fixed transaction cost to turnover, and records holdings/metrics. | Scheduled rebalance handler ranks current universe, calls `SetHoldings` / portfolio targets for selected symbols, liquidates removed names, and relies on LEAN fill, fee, and slippage models. |
| Local price `DataFrame` | Aligned wide table of adjusted prices. | LEAN `Symbol` subscriptions and daily bars from the data feed. Use adjusted data normalization for comparability with local adjusted-price calculations. |
| Local signal `DataFrame` | Precomputed cross-sectional scores by date. | Signals computed inside the algorithm from per-symbol rolling windows after daily bars are available. |
| Local benchmark price `Series` | Synthetic or external benchmark equity curve. | `SetBenchmark("SPY")` or a subscribed benchmark ETF / index proxy. |
| Local reports | Markdown and later plots. | LEAN statistics plus custom logs/charts. Export key diagnostics separately if needed. |

## 2. Universe Selection Assumptions

First version universe should be simple and liquid:

- Asset class: US equities only.
- Data resolution: daily.
- Initial selection: top liquid equities by dollar volume from a coarse or fundamental universe.
- Candidate filter:
  - price above a minimum threshold, such as `$5`.
  - positive dollar volume.
  - sufficient daily history for 252-day lookback plus 21-day skip.
  - exclude symbols with missing or stale data at rebalance.
- Universe size: start with 100-500 most liquid names to keep the first LEAN run debuggable.
- Survivorship bias: prefer LEAN universe selection over a static modern ticker list. A fixed ticker list can be used only as a debugging mode and must be labeled survivorship-biased.
- Corporate actions: use adjusted prices for signal calculation to match the local momentum implementation.

The first LEAN version should not add fundamentals, value, quality, shorting, leverage, or live trading.

## 3. Rebalance Schedule

Recommended first implementation:

- Rebalance monthly.
- Use a scheduled event tied to a liquid reference symbol such as `SPY`.
- Trigger after market open on the first trading day of each month, for example 10-30 minutes after open.
- Rank the current eligible universe using signals computed from completed daily bars through the prior close.

This schedule is intentionally conservative. It avoids using same-day close data for same-day trades and gives LEAN a clear event to test.

Alternative parity mode:

- To match the current local backtester more closely, use month-end rebalance dates with a one-row signal lag and let target holdings affect the next daily return.
- If this parity mode is used, document the exact mapping between local month-end close assumptions and LEAN fill timing.

## 4. Signal Generation Timing

Signal rule:

```text
momentum[t] = adjusted_close[t - 21 trading days] / adjusted_close[t - 252 trading days] - 1
```

Timing rules:

- Only completed daily bars may enter the rolling window.
- At a monthly rebalance event, compute scores from history available before the order event.
- Do not use the current trading day's close if orders are submitted before that close.
- Symbols without enough history receive no score and are excluded from selection.
- Missing or non-positive anchor prices should produce no score, matching the local `NaN` behavior.

Implementation options:

- Maintain `RollingWindow[TradeBar]` or a custom rolling close buffer per symbol.
- Or request history at each rebalance for the active universe, then compute scores in one pass.
- For the first version, history requests are simpler and easier to audit; rolling windows are more efficient later.

## 5. Order Execution Timing

First version execution assumption:

- Orders are submitted only inside the scheduled monthly rebalance handler.
- Trades are market orders or `SetHoldings`-generated market orders after market open.
- Selected assets receive equal target weights.
- Removed assets are liquidated.
- No leverage: total target weight must be less than or equal to 1.0.
- No shorting: all target weights must be non-negative.
- Cash buffer: reserve a small cash buffer, for example 1-2%, to reduce rejected orders from fees, gaps, or rounding.

Important mismatch with local backtest:

- The local engine uses close-to-close returns and simplified target-weight turnover.
- LEAN simulates orders, fills, buying power, fees, and portfolio accounting through its engine. A LEAN market order after the open will not exactly equal a local close-to-close rebalance.

## 6. Transaction Fee and Slippage Assumptions

First version should make fees and slippage explicit:

- Fee model:
  - Use LEAN's brokerage model defaults only if they are documented in the experiment.
  - Prefer a simple custom fee model or supported constant/percentage-style equivalent that approximates the local basis-point cost assumption.
- Slippage model:
  - Use a simple constant slippage assumption first, or explicitly document if using zero slippage for a diagnostic run.
  - Do not present zero-slippage results as realistic.
- Local comparison:
  - Local engine currently uses `transaction_cost_bps` applied to target-weight turnover.
  - LEAN costs are order-based, so cost totals may differ because order size, price, fills, and cash constraints are modeled differently.

Each LEAN run should record:

- fee model name and parameters.
- slippage model name and parameters.
- brokerage model.
- whether orders are market, limit, or portfolio-target generated.
- rejected or partially filled orders, if any.

## 7. Risk Controls

First version risk controls:

- Long-only.
- No leverage.
- Equal-weight positions.
- Maximum number of holdings, such as top 20 or top 50.
- Minimum price filter.
- Minimum dollar-volume filter.
- Minimum history requirement.
- Exclude assets with stale or missing data at rebalance.
- Cash buffer.
- Optional single-name cap equal to the equal-weight target.

Not in first version:

- Long-short portfolio construction.
- Sector neutrality.
- Volatility targeting.
- Stop losses.
- Intraday trading.
- Machine learning model selection.
- Broker integration or live deployment.

## 8. Benchmark Choice

Recommended benchmark:

- `SPY` for a broad US large-cap equity proxy.

Alternatives:

- `VTI` for broader US market exposure.
- Equal-weight synthetic universe benchmark for closer comparison to the selected universe, if implemented explicitly.
- `QQQ` only if the universe is technology-heavy and the choice is documented.

The first LEAN version should call `SetBenchmark` with the selected benchmark and also record the benchmark ticker in the experiment log.

## 9. Differences Between Local Backtest and LEAN Backtest

| Area | Local backtest | LEAN backtest |
| --- | --- | --- |
| Data source | User-provided `DataFrame` or synthetic data. | LEAN data subscriptions and universe data. |
| Price normalization | Assumed adjusted prices if supplied. | Configurable data normalization; must be set/documented. |
| Signal timing | Explicit shifted features and `signal_lag_periods`. | Depends on scheduled event time, daily bar availability, warm-up/history, and algorithm time zone. |
| Rebalance | Derived pandas rebalance dates. | Scheduled events in engine time. |
| Execution | Simplified target-weight change; holdings affect next row. | Orders, fills, cash, buying power, fees, slippage, and brokerage models. |
| Turnover | Target-weight turnover. | Must be calculated from actual orders/fills or portfolio holdings if needed. |
| Fees | Basis points applied to turnover. | Fee model applied to orders/fills. |
| Slippage | Currently not separate from transaction cost unless added later. | Slippage model per security. |
| Metrics | Local deterministic metric helpers. | LEAN statistics plus any custom metrics logged/exported. |

## 10. Potential Sources of Mismatch

### Data Vendor Differences

Different vendors can report different prices, volumes, corporate action adjustments, delisting behavior, and symbol mappings. Local CSV/vendor data may not match QuantConnect datasets.

### Survivorship Bias

A static current ticker list can exclude delisted or failed companies. LEAN universe selection can reduce this risk, but the exact universe construction must still be documented.

### Corporate Actions

Splits, dividends, mergers, and symbol changes can change adjusted-price history and tradability. Momentum calculations must use the same adjustment convention in local and LEAN runs.

### Fills

The local engine assumes target weights are achieved mechanically. LEAN has fill models, order events, buying power checks, open-market timing, and possible rejected orders.

### Slippage

Local cost assumptions may be fixed basis points. LEAN slippage models can be zero, constant, volume-share, or custom. Differences can materially change results.

### Fees

Local fees are turnover-based. LEAN fees are applied at the order/fill level. They may differ because of share rounding, cash buffers, brokerage model defaults, and partial fills.

### Timezone and Date Alignment

Pandas dates are usually date-indexed close observations. LEAN has algorithm time zones, exchange time zones, scheduled event timing, and data emission timing. The first LEAN implementation must log rebalance timestamps and the latest price date used for each signal.

## 11. Step-by-Step First LEAN Version

1. Create a new LEAN research branch or directory, but keep it separate from the local Python pipeline.
2. Define algorithm metadata:
   - start date and end date.
   - initial cash.
   - benchmark ticker.
   - daily resolution.
   - adjusted data normalization.
3. Add a liquid benchmark subscription such as `SPY` and set it as benchmark.
4. Implement a simple US equity universe:
   - filter by price.
   - sort by dollar volume.
   - keep top 100-500 candidates.
   - require enough historical data before ranking.
5. Add warm-up or history handling:
   - ensure 252 + 21 trading days of daily adjusted close data are available.
   - skip symbols without complete required anchors.
6. Implement signal calculation only:
   - compute 12-1 momentum from completed daily bars.
   - log a few symbol-level scores on the first rebalance for audit.
7. Implement monthly scheduled rebalance:
   - schedule after market open on the first trading day of each month.
   - rank eligible symbols by momentum.
   - select top `N`.
8. Implement equal-weight targets:
   - target weight per selected symbol = `(1 - cash_buffer) / N`.
   - liquidate names no longer selected.
   - submit only long targets.
9. Configure and document fee/slippage assumptions:
   - start with a simple explicit model.
   - record all parameters in the experiment log.
10. Add diagnostics:
    - selected symbols at each rebalance.
    - number of eligible symbols.
    - turnover approximation or actual order notional.
    - rejected orders.
    - current benchmark value.
11. Run a short smoke backtest:
    - verify no trades during warm-up.
    - verify monthly-only trading.
    - verify no negative holdings.
    - verify no leverage.
    - verify signals use prior completed data only.
12. Run a longer backtest only after the smoke test passes.
13. Compare local and LEAN behavior:
    - use the same universe if possible for a parity test.
    - compare rebalance dates, selected symbols, weights, turnover, fees, and equity curve.
    - document mismatches rather than tuning them away.
14. Record the run in `EXPERIMENT_LOG.md`:
    - hypothesis.
    - universe.
    - date range.
    - factor formula.
    - parameters.
    - benchmark.
    - fees and slippage.
    - sample split.
    - failure modes.

## References

- QuantConnect docs: [Algorithm Engine](https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/algorithm-engine)
- QuantConnect docs: [Initialization and SetBenchmark](https://www.quantconnect.com/docs/v2/writing-algorithms/initialization)
- QuantConnect docs: [Fundamental Universes](https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/universe-selection/fundamental-universes)
- QuantConnect docs: [US Equity Coarse Universe](https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/quantconnect/us-equity-coarse-universe)
- QuantConnect docs: [Historical Data](https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/getting-started)
- QuantConnect docs: [Warm Up Periods](https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/warm-up-periods)
- QuantConnect docs: [Transaction Fees](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/transaction-fees/key-concepts)
- QuantConnect docs: [Slippage Models](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/slippage/supported-models)
- QuantConnect docs: [Trade Fills](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/trade-fills/key-concepts)
