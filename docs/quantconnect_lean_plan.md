# QuantConnect / LEAN Implementation Plan

This document plans a first QuantConnect/LEAN version of the local equity factor research workflow. It is a plan only. Do not implement the LEAN strategy in this step.

The goal is to translate the local, auditable research logic into a platform-grade LEAN backtest while preserving the same research standards: no live trading, no brokerage connection, no look-ahead bias, explicit costs, explicit slippage, and clear date alignment.

Current local status before any LEAN code:

- strict local CSV loaders exist for wide prices, long prices, and benchmark prices.
- committed synthetic local CSV fixtures and a local CSV fixture workflow demo exercise the loader path without real data.
- `alpha_009` exists as a close-only research feature, not a strategy.
- `alpha_012` exists as a volume + close research feature and is covered by
  formula tests, synthetic OHLCV fixture smoke coverage, and local-fixture
  diagnostics. It is not a strategy, not order logic, and not performance
  evidence.
- IC, Rank IC, and quantile spread diagnostics exist for already-aligned factor and forward-return panels.
- synthetic reports, JSON experiment logs, and the experiment registry exist for auditable workflow outputs.
- no real-data local CSV study, LEAN implementation, paper trading, live trading, broker integration, order execution, or profitability claim exists.

## 1. Local Logic to LEAN Mapping

| Local component | Current local role | LEAN mapping |
| --- | --- | --- |
| `features.momentum.calculate_12_1_momentum` | Computes 12-1 momentum as `price[t - skip] / price[t - lookback] - 1` with explicit shifting. | Maintain a per-symbol rolling adjusted close history or use `History` / warm-up data. Compute the same score only from completed daily bars. |
| `features.worldquant_alphas.alpha_009` | Computes one close-only WorldQuant-style research feature from current and prior closes. It is not a strategy or performance claim. | Optional later feature-parity candidate only after local formula behavior and LEAN bar timing are mapped. Do not connect it to orders without a separate reviewed strategy stage. |
| `features.worldquant_alphas.alpha_012` | Computes `sign(delta(volume, 1)) * (-1 * delta(close, 1))` from exactly aligned close and volume panels. It rejects negative volume, preserves missing values, and is not a strategy or performance claim. | Optional later feature-parity candidate only after completed daily close and volume timing are mapped. The first LEAN-adjacent treatment should be signal-export or metadata-only, not order logic. |
| `data.csv_loader` | Reads user-provided local CSV files only, with strict schema, date, missing-value, and numeric validation. | No direct LEAN equivalent because LEAN uses subscriptions, history, and universe data. Map validation concepts to LEAN dataset, universe, calendar, normalization, and missing-history diagnostics. |
| `research/local_csv_fixture_workflow_demo.py` | Demonstrates the local CSV path on committed synthetic fixtures, computes `alpha_009` and `alpha_012`, and runs caveated diagnostics. | Use as a workflow-shape reference only: load or subscribe data, compute a feature, align evaluation targets, log diagnostics, and preserve caveats. It is not a real-data or LEAN parity result. |
| `features.diagnostics.factor_information_coefficient` and `factor_rank_information_coefficient` | Compute per-date cross-sectional IC / Rank IC from already-aligned factor and forward-return panels without filling missing values. | Export or log factor and realized forward-return panels from LEAN after a smoke run, then compute comparable diagnostics offline or in a research notebook. Avoid using future returns as live signal inputs. |
| `features.diagnostics.factor_quantile_spread` | Computes top-minus-bottom quantile return diagnostics with explicit coverage counts from aligned panels. | Record selected quantile membership and subsequent returns for LEAN analysis. Treat quantile spread as diagnostic evidence only, not as order logic or a profitability claim. |
| `backtest.portfolio.run_long_only_backtest` | Selects top-ranked assets, equal-weights them, applies fixed transaction cost and fixed-bps slippage assumptions to target-weight turnover, and records holdings, metrics, and separate cost/slippage impact series. | Scheduled rebalance handler ranks current universe, calls `SetHoldings` / portfolio targets for selected symbols, liquidates removed names, and relies on LEAN fill, fee, and slippage models. |
| Local price `DataFrame` | Aligned wide table of adjusted prices. | LEAN `Symbol` subscriptions and daily bars from the data feed. Use adjusted data normalization for comparability with local adjusted-price calculations. |
| Local signal `DataFrame` | Precomputed cross-sectional scores by date. | Signals computed inside the algorithm from per-symbol rolling windows after daily bars are available. |
| Local benchmark price `Series` | Synthetic or external benchmark equity curve. | `SetBenchmark("SPY")` or a subscribed benchmark ETF / index proxy. |
| `reporting.experiment_log` and `reporting.experiment_registry` | Write deterministic JSON logs and a registry for synthetic/local workflow outputs. | Record LEAN run metadata, parameters, data assumptions, diagnostics, and caveats in a separate experiment-log entry. Do not mix LEAN results into synthetic-only records. |
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
  - if an Alpha#012-style signal is reviewed later, sufficient completed
    close and volume history for the one-period deltas and a logged policy for
    missing, zero, or stale volume.
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

Signal timing must be documented separately for each reviewed feature. The
first runnable LEAN path should not treat feature parity as strategy approval.

### 12-1 Momentum

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

### Alpha#012

Reviewed local formula:

```text
alpha_012[t] = sign(volume[t] - volume[t - 1]) * (-(close[t] - close[t - 1]))
```

LEAN mapping assumptions before any future code:

- Use only completed daily bars for both close and volume.
- Record whether `close` means adjusted close, raw close, or another reviewed
  normalization mode before comparing with local outputs.
- Treat share volume as caller-reviewed volume; do not infer split-adjusted
  volume behavior without documenting the data source and normalization.
- Require the latest completed close and volume date to be the same for each
  scored symbol.
- Missing close, missing volume, incomplete one-period anchors, stale bars, or
  non-positive close observations should produce no score and should be logged
  as skipped-symbol reasons.
- Negative volume should be treated as invalid input. Zero volume should remain
  visible and should not be silently converted to missing or positive volume.
- The first LEAN-adjacent Alpha#012 artifact should be signal metadata,
  feature export, or parity diagnostics only. It should not create portfolio
  targets, submit orders, select a universe by factor value, or interpret
  results as performance evidence.

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
  - Local engine currently uses `transaction_cost_bps` and `slippage_bps` applied to target-weight turnover.
  - Local output records transaction cost impact, slippage impact, and combined total trading impact separately.
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
| Slippage | Separate fixed-bps `slippage_bps` impact applied to target-weight turnover; zero slippage is labeled diagnostic. | Slippage model per security. |
| Metrics | Local deterministic metric helpers. | LEAN statistics plus any custom metrics logged/exported. |

### Local CSV Validation Mapping

The local CSV interface and a future LEAN backtest solve different data
problems. The local path validates user-provided files already present on disk.
The LEAN path uses platform subscriptions, history, universe selection, and
engine accounting. A successful local CSV validation therefore improves
auditability, but it does not prove that a LEAN run has identical data,
calendar, symbol, fill, fee, or slippage assumptions.

Local CSV validation should map into LEAN planning as follows:

| Local CSV check | LEAN planning equivalent | Divergence risk |
| --- | --- | --- |
| File provenance, schema, and local path are recorded before use. | Record LEAN project, dataset, universe selection rules, start/end dates, benchmark, and algorithm parameters before the backtest. | Local file identity and LEAN dataset configuration are not interchangeable evidence. |
| Dates parse, sort, and remain duplicate-free. | Log scheduled rebalance timestamps, algorithm time zone, exchange calendar, and latest completed bar date used for each signal. | Pandas date indexes can differ from LEAN event times, market holidays, half days, and data emission timing. |
| Wide or long adjusted-close panels declare their adjustment convention. | Configure and record LEAN equity data normalization for signal calculation and benchmark comparison. | Local adjusted prices may not match LEAN corporate-action processing or normalization mode. |
| Duplicate `(date, symbol)` rows, non-positive prices, and silent numeric coercion are rejected. | Skip securities with missing, stale, non-positive, or incomplete history at rebalance and log skip counts. | LEAN data can be absent because of subscriptions, IPO dates, delistings, symbol changes, or universe membership timing. |
| Missing values are reported and are not forward-filled by default. | Record missing history responses, inactive securities, fill-forward settings, and symbols excluded for incomplete anchors. | Platform fill-forward behavior or warm-up gaps can hide a mismatch if it is not logged. |
| Universe membership must be date-stamped and not use future membership. | Prefer LEAN universe selection over static modern ticker lists and record the exact filters used. | LEAN universe logic reduces survivorship bias risk, but filter timing and dataset coverage still need review. |
| Benchmark files are validated separately and aligned explicitly. | Record `SetBenchmark` choice, benchmark subscription, normalization, date range, and missing benchmark observations. | A local benchmark series and LEAN benchmark security can differ in coverage, adjustment, and trading calendar. |
| Experiment setup records costs, slippage, rebalance timing, and signal lag. | Record brokerage model, fee model, slippage model, cash buffer, order type, and scheduled execution timing. | Local turnover costs are target-weight approximations; LEAN applies order-level fills, fees, buying power, and cash constraints. |
| Validation summary is preserved before interpreting results. | Preserve LEAN diagnostics: eligible count, selected symbols, skipped symbols, rejected orders, actual holdings, and benchmark state. | Similar headline metrics can mask different data coverage, fills, costs, or symbol mappings. |

This mapping is a documentation-only bridge. It does not implement a CSV loader,
fetch data, download data, add vendor access, connect to a broker, place orders,
enable live trading, or make a profitability claim. Future LEAN results should
be treated as a separate research artifact with their own experiment-log entry
and caveats, not as a direct continuation of a local CSV validation report.

### Local Diagnostic Mapping

The local diagnostics added after the original LEAN plan should shape the first
LEAN research review, but they should not be converted directly into trading
rules.

| Local diagnostic | LEAN planning equivalent | Required caveat |
| --- | --- | --- |
| IC / Rank IC by date | Export factor scores and realized next-period returns after a LEAN backtest, then compute cross-sectional correlations with the same missing-value policy. | Forward returns are evaluation targets only and must never enter signal generation. |
| Quantile spread by date | Record factor buckets and subsequent returns for each rebalance period. Include valid asset counts and bucket counts. | Quantile spread is diagnostic visibility, not proof of future performance. |
| Local CSV fixture workflow report/log | Use as a template for caveated workflow documentation and JSON sidecar metadata. | The fixture is synthetic and tiny; it is not a real-data benchmark or LEAN parity test. |
| Experiment registry | Keep LEAN experiment records discoverable separately from synthetic local logs. | Registry summaries should not hide weak runs or promote best-only results. |

Alpha#012-specific diagnostic exports should additionally record:

- close normalization mode used for the `close[t] - close[t - 1]` term.
- volume field source and whether the value is raw, adjusted, or
  caller-reviewed without adjustment.
- counts of skipped symbols for missing close, missing volume, mismatched close
  and volume dates, negative volume, stale volume, and incomplete one-period
  anchors.
- valid Alpha#012 score counts before IC, Rank IC, or quantile-spread
  diagnostics are computed.
- explicit caveats that Alpha#012 diagnostics are feature diagnostics only,
  not a standalone strategy, portfolio rule, or profitability claim.

The first LEAN smoke run should therefore preserve:

- factor formula and timing metadata.
- latest completed data date used for each rebalance.
- eligible, skipped, selected, and missing-history symbol counts.
- benchmark configuration and normalization.
- fee, slippage, cash buffer, order type, and brokerage model assumptions.
- diagnostics exported in a form that can be audited outside the engine.
- explicit caveats that results are simulated research output only.

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

Local cost and slippage assumptions may be fixed basis points applied to target-weight turnover. LEAN slippage models can be zero, constant, volume-share, or custom and are applied through engine order/fill semantics. Differences can materially change results.

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
   - if Alpha#012 parity is in scope for a later reviewed stage, compute it
     only from completed close and volume bars and export scores as
     diagnostics, not as order or universe-selection logic.
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
    - number of symbols skipped for missing, stale, non-positive, or incomplete history.
    - latest completed bar date used for signal calculation.
    - optional IC, Rank IC, and quantile-spread export fields for offline review.
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
    - compare diagnostic panel coverage before comparing summary metrics.
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

## 12. Recommended Next LEAN-Related Stage

The next LEAN-related stage should still be planning or signal-boundary
documentation, not a full algorithm.

Recommended PR-sized stage:

- create a documentation-only Alpha#012 signal-boundary design or checklist
  addendum that defines metadata fields, timing fields, skipped-symbol reasons,
  and static guardrails before any Alpha#012 LEAN-adjacent code exists.
- keep any future Alpha#012 LEAN-adjacent code signal-only until a separate
  design is reviewed and merged.
- do not fetch data, download data, add credentials, connect to a broker, place
  orders, enable live trading, or claim profitability.

Stop conditions for the next LEAN stage:

- a real data source, QuantConnect account access, credentials, or external
  execution path is required.
- a local-vs-LEAN mismatch cannot be explained from available logs.
- the work would require source-code changes outside the planned scaffold.
- any result would need to be interpreted as performance evidence.

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
