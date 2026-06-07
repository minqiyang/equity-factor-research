# LEAN Parity Checklist

Date: 2026-06-04

This document is a planning and smoke-test checklist for a future
QuantConnect/LEAN research implementation. It is documentation only. It does
not add a LEAN algorithm, fetch data, download data, add credentials, connect
to a broker, place orders, enable live trading, or claim profitability.

The purpose is to map the current local research pipeline to concrete parity
and smoke-test assertions before any LEAN code is written.

## 1. Purpose

The future LEAN stage should preserve the research discipline already present
in the local project:

- transparent factor formulas.
- explicit feature, rebalance, execution, and evaluation timing.
- strict data and missing-value assumptions.
- documented universe, benchmark, fee, slippage, and cash-buffer choices.
- auditable diagnostics and experiment logs.
- clear caveats that simulated research output is not investment advice or a
  performance guarantee.

The checklist should be completed before a future LEAN implementation is
treated as comparable to the local workflow.

## 2. Non-Goals

This checklist does not authorize:

- a LEAN algorithm file.
- QuantConnect project scaffolding.
- real data fetching or downloading.
- vendor API access.
- credentials, tokens, account IDs, or secrets.
- live trading, paper trading, brokerage integration, or order execution.
- performance marketing, profitability claims, or strategy promotion.
- bulk WorldQuant 101 implementation.

## 3. Current Local Evidence To Preserve

| Local evidence | What must be preserved in LEAN planning |
| --- | --- |
| `src/features/momentum.py` | 12-1 momentum formula and lagged close-price timing. |
| `src/features/worldquant_alphas.py` | `alpha_009` as a close-only research feature, not a strategy. |
| `src/features/worldquant_alphas.py` | `alpha_012` as a volume + close research feature, not a strategy, universe filter, or order rule. |
| `src/data/csv_loader.py` | Strict validation mindset: schema, dates, numeric fields, missing values, and provenance. |
| `src/features/diagnostics.py` | IC, Rank IC, and quantile spread as evaluation diagnostics only. |
| `src/backtest/portfolio.py` | Long-only equal-weight target concepts, simplified turnover cost caveats, and signal lag. |
| `src/reporting/experiment_log.py` | Deterministic run metadata, caveats, parameters, and validation summaries. |
| `research/local_csv_fixture_workflow_demo.py` | Workflow shape for synthetic local fixtures only; not market evidence. |
| `EXPERIMENT_LOG.md` | Durable record of hypotheses, assumptions, sample splits, costs, slippage, and caveats. |

## 4. Startup And Scope Gates

| Gate | Assertion | Required evidence | Stop if |
| --- | --- | --- | --- |
| Repository state | LEAN work starts from clean, synced `main`. | `git status -sb`, recent git log, open PR list. | Any prior PR is open or working tree is dirty. |
| Scope | The stage is explicitly limited before editing. | Branch name, intended file list, PR scope. | Source, tests, reports, or research scripts would change outside the planned stage. |
| Data access | No external data path is required. | No vendor import, API call, download command, or credential. | A real data source, download, credential, or platform account is required. |
| Guardrails | Prohibited behavior remains absent. | Guardrail grep and read-only scope review. | Live trading, broker access, order execution, credential, or profitability logic appears. |

## 5. Data, Universe, And Benchmark Checks

| Area | LEAN smoke-test assertion | Local comparison |
| --- | --- | --- |
| Universe | Record universe rule, date range, minimum price, dollar-volume filter, and minimum history requirement. | Local CSV fixtures use explicit asset columns; future real local CSV work must record point-in-time universe assumptions separately. |
| History coverage | Log eligible, skipped, stale, missing-history, and selected symbol counts at every rebalance. | Local loaders reject invalid panels and diagnostics preserve valid asset counts. |
| Corporate actions | Record LEAN equity data normalization mode before signal calculation. | Local momentum assumes the supplied prices are adjusted when the panel is labeled adjusted close. |
| Benchmark | Record benchmark symbol, normalization, subscription, and missing benchmark observations. | Local benchmark CSV validation is separate from asset price validation. |
| Calendar | Record rebalance timestamps, market calendar, time zone, and latest completed bar date used for each signal. | Local pandas dates are not automatically equivalent to LEAN engine event times. |

## 6. Feature-Timing Checks

### 12-1 Momentum

| Assertion | Expected smoke-test evidence |
| --- | --- |
| The score uses the same formula shape: `adjusted_close[t - 21] / adjusted_close[t - 252] - 1`. | A logged sample calculation for at least one symbol at the first eligible rebalance. |
| Orders or portfolio targets do not use same-day close when the event runs after the open. | Rebalance log records latest completed daily bar date used for each signal. |
| Symbols without enough history are excluded, not filled. | Skip counts and skipped-symbol reasons are logged. |
| Non-positive anchor prices produce no score. | A missing or invalid anchor reason is logged when observed. |

### `alpha_009`

| Assertion | Expected smoke-test evidence |
| --- | --- |
| `alpha_009` remains a research feature unless a separate reviewed strategy stage explicitly changes that. | PR scope and experiment notes say it is not order logic. |
| Formula parity is checked against completed close data only. | Sample input/output rows or an offline parity check are preserved. |
| Missing values are not filled into scores. | Diagnostics record valid and missing score counts. |

### `alpha_012`

| Assertion | Expected smoke-test evidence |
| --- | --- |
| `alpha_012` remains a research feature unless a separate reviewed strategy stage explicitly changes that. | PR scope and experiment notes say it is not order logic, universe construction, or portfolio construction. |
| The formula uses completed close and volume bars only: `sign(delta(volume, 1)) * (-1 * delta(close, 1))`. | Sample close, volume, delta, sign, and output rows are preserved for at least one reviewed symbol/date. |
| Close and volume dates match before a score is produced. | Rebalance or diagnostic logs record latest completed close and volume dates. |
| Missing close, missing volume, incomplete one-period anchors, and stale bars are not filled into scores. | Skip counts and skipped-symbol reasons are logged. |
| Negative volume is invalid and zero volume remains visible. | Diagnostics distinguish negative-volume invalid input from zero-volume observations. |

## 7. Diagnostic Export Checks

Diagnostics are evaluation tools, not signal inputs.

| Diagnostic | Required assertion | Required evidence |
| --- | --- | --- |
| IC | Forward returns are exported or computed only after the evaluation period is known. | Exported panel metadata distinguishes factor dates from forward-return target dates. |
| Rank IC | Missing factor/return pairs are dropped pairwise without filling. | Valid count per date is recorded. |
| Quantile spread | Top-minus-bottom spread is labeled diagnostic and includes bucket counts. | Edge-bucket counts, valid asset counts, and caveats are preserved. |
| Coverage | Dates with insufficient assets remain visible. | `NaN` diagnostics or explicit insufficient-coverage records are retained. |
| Alpha#012 coverage | Close/volume score coverage is visible before any diagnostic is interpreted. | Valid score counts and skip reasons for missing close, missing volume, mismatched dates, negative volume, stale volume, and incomplete anchors are preserved. |

Forward returns must never be used as features, selection inputs, or rebalance
inputs.

## 8. Execution And Accounting Checks

These checks are for future simulated LEAN backtests only. They are not live
trading instructions.

| Area | Smoke-test assertion |
| --- | --- |
| Warm-up | No trades occur before required history is available. |
| Schedule | Rebalance occurs monthly only, at the documented scheduled event. |
| Positioning | Targets are long-only and non-negative. |
| Leverage | Total target exposure is less than or equal to 1.0 after the cash buffer. |
| Holdings | Removed names are liquidated only during the scheduled rebalance. |
| Fees | Fee model and parameters are recorded before interpreting any result. |
| Slippage | Slippage model and parameters are recorded; zero-slippage diagnostics are labeled unrealistic. |
| Cash buffer | Cash buffer is explicit and rejected orders are logged. |
| Orders | Rejected or partially filled orders remain visible in logs. |

## 9. Experiment-Log Requirements

A future LEAN smoke run should create or update a research record only after
its scope is reviewed. The record should include:

- hypothesis and non-goals.
- start date, end date, universe rule, benchmark, and sample split.
- factor formulas and parameter values.
- latest completed data date used at each rebalance.
- fee model, slippage model, cash buffer, brokerage model, and order type.
- eligible, skipped, selected, and missing-history counts.
- rejected orders or buying-power issues.
- diagnostic export locations and coverage summaries.
- known mismatches versus the local workflow.
- caveats that the run is simulated research output only.

## 10. Local-Vs-LEAN Parity Review

| Review area | Pass condition | Expected mismatch to document |
| --- | --- | --- |
| Rebalance dates | Dates are explainable from the selected market calendar and schedule. | Month-end pandas dates may differ from first-trading-day LEAN events. |
| Signal timing | Signals use only data available before simulated order submission. | Local close-to-close lag may not match after-open LEAN order timing exactly. |
| Selected symbols | Differences are explained by universe, history, or data availability. | LEAN universe membership can differ from local fixtures or static panels. |
| Weights | Long-only equal weights respect the cash buffer. | LEAN share rounding and cash constraints can alter final holdings. |
| Costs | Fee/slippage assumptions are visible before metrics are reviewed. | Local turnover cost is simplified; LEAN is order/fill based. |
| Diagnostics | IC, Rank IC, and quantile-spread coverage is compared before summary metrics. | Similar headline metrics can hide different coverage or missing-data behavior. |

Parity review should document mismatches. It should not tune assumptions merely
to make outputs look similar.

## 11. Stop Conditions

Stop a future LEAN stage if any of the following is required:

- external data download or vendor API access.
- QuantConnect account credentials, secrets, or tokens.
- live trading, paper trading, brokerage connection, or real order path.
- source changes outside the reviewed stage scope.
- interpreting simulated output as profitability evidence.
- unexplained local-vs-LEAN mismatch after reasonable log review.
- weakening existing tests or hiding missing data.

## 12. Recommended Next Step After This Checklist

After this checklist is reviewed and merged, the next safe LEAN-related stage
should still be small. A reasonable next stage would be a documentation-only
LEAN smoke-test design note or, if explicitly approved later, a minimal
non-executing LEAN project scaffold with no credentials, no external data
download code, no live-trading path, and no performance claims.
