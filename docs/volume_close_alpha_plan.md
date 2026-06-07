# Volume + Close Alpha Planning Gate

Date: 2026-06-06

This document defines the next planning boundary before any volume + close
WorldQuant-style alpha is implemented.

It is documentation only. It does not modify source code, tests, research
scripts, generated reports, loaders, backtester behavior, metrics, data access,
execution assumptions, or performance claims. It does not fetch data, download
data, add vendor APIs, add credentials, add live trading, add paper trading,
add brokerage integration, add order execution, or claim profitability.

## Purpose

The repository now has strict local OHLCV CSV validation, synthetic OHLCV
fixture smoke coverage, synthetic liquidity eligibility helpers, short-term
reversal, and realized volatility. The next data-dependent factor gap is a
reviewed boundary for formulas that require both volume and close data.

This planning gate keeps formula work separate from data access, universe
construction, portfolio construction, and performance interpretation. It
defines what must be true before a future PR implements a small volume + close
research feature such as `alpha_012`.

## Non-Goals

- No source-code implementation.
- No changes to `src/features/worldquant_alphas.py`.
- No changes to `src/data/csv_loader.py`.
- No changes to tests, research scripts, generated reports, backtester,
  metrics, normalization, combination, diagnostics, or synthetic demos.
- No user-provided or real-market data.
- No downloads, vendor APIs, `requests`, `yfinance`, Alpaca, CCXT, or
  credential logic.
- No live trading, paper trading, brokerage integration, order execution, or
  account handling.
- No portfolio construction, signal weighting, universe selection, slippage
  model, benchmark interpretation, LEAN runtime behavior, or strategy result.
- No automatic forward-fill, backward-fill, zero-fill, interpolation, or
  missing-data repair.
- No profitability, investment-performance, robustness, or trading-readiness
  claim.

## Current Prerequisites

| Prerequisite | Current evidence | Status |
| --- | --- | --- |
| Strict OHLCV local validation | `load_ohlcv_csv()` in `src/data/csv_loader.py` | Implemented and tested. |
| Synthetic OHLCV fixture smoke coverage | `tests/test_local_csv_loader_smoke_demo.py` and committed fixture CSVs | Implemented with synthetic fixtures only. |
| Volume and dollar-volume helper behavior | `src/features/liquidity.py`, `tests/test_liquidity.py` | Implemented for synthetic panels. |
| Close-only alpha precedent | `alpha_009()` in `src/features/worldquant_alphas.py` | Implemented as a research feature only. |
| Close-price factor precedent | Momentum, reversal, and volatility helpers | Implemented as research features only. |
| Diagnostics and split helpers | `src/features/diagnostics.py`, `src/features/validation.py` | Implemented for synthetic/local-fixture panels. |

These prerequisites make the next formula review possible. They do not approve
real-data interpretation, backtest integration, or formula profitability
claims.

## Candidate Formula Boundary

The first volume + close candidate should be a single small formula, likely
`alpha_012`, because the WorldQuant catalog already classifies it as requiring
only volume and close inputs.

Before implementation, the future PR must record the exact formula source and
notation in the PR description or engineering log. This planning document does
not lock the formula text because formula transcription is a code-stage
correctness risk and should be checked immediately before implementation.

The future implementation should answer these questions before code is added:

| Question | Required answer before code |
| --- | --- |
| Formula provenance | Which public formula text is being implemented, and how are its symbols mapped to local panels? |
| Input close policy | Is the formula using raw close, adjusted close, or a caller-provided close panel? |
| Volume policy | Is volume raw share volume, adjusted volume, or caller-provided already-reviewed volume? |
| Output meaning | Is higher output intended to be ranked as a stronger feature value, or should ranking direction be documented separately? |
| Date availability | When are close and volume known, and what later layer handles execution lag? |
| Missing behavior | Which missing close or volume observations produce `NaN`? |
| Zero-volume behavior | Does zero volume remain a valid input to the formula, or does it force `NaN`? |
| Panel alignment | Must close and volume indexes and columns match exactly before calculation? |

## Alpha#012 Implementation Status

`alpha_012()` is now implemented as the first volume + close research feature
in `src/features/worldquant_alphas.py`.

The implementation maps the public formula:

```text
sign(delta(volume, 1)) * (-1 * delta(close, 1))
```

to exactly aligned caller-provided close and volume panels. It keeps the
function as a feature calculation only: no loader, universe, backtest,
portfolio, execution, reporting, real-data, or profitability behavior is added.

Remaining volume + close alphas still require their own formula provenance,
input policy, missing-data policy, zero-volume policy, and tests before code is
added.

## Alpha#012 Synthetic Fixture Smoke Status

The committed synthetic OHLCV fixture now has feature-only smoke coverage for
`alpha_012()`.

`tests/test_local_csv_loader_smoke_demo.py` loads
`tests/fixtures/local_csv_loader_smoke/synthetic_ohlcv.csv`, pivots
`adjusted_close` and `volume` into aligned panels, and computes the feature
without running diagnostics, reports, backtests, portfolio construction, data
downloads, broker logic, order execution, or performance interpretation.

## Alpha#012 Synthetic Fixture Diagnostics Status

The synthetic local CSV fixture workflow now evaluates `alpha_012()` with the
existing IC, Rank IC, and quantile-spread diagnostics.

`research/local_csv_fixture_workflow_demo.py` computes `alpha_012()` from the
committed synthetic OHLCV fixture's aligned `adjusted_close` and `volume`
panels. The generated report and JSON experiment log keep Alpha#012 diagnostic
coverage separate from Alpha#009 and label the output as synthetic
local-fixture diagnostics only. No backtest, universe construction, portfolio,
execution, real-data, or profitability behavior is added.

## Proposed Future Function Shape

A future code PR can consider a narrow helper in `src/features/worldquant_alphas.py`:

```text
alpha_012(close: pandas.DataFrame, volume: pandas.DataFrame) -> pandas.DataFrame
```

The exact signature may change if the reviewed formula requires a window or
other parameter. The function should remain a research feature only. It should
not import backtest, portfolio, reporting, data-loader, API, credential, or
execution modules.

## Alignment Rules

Future volume + close alpha code should preserve these timing rules:

1. `close[t]` and `volume[t]` may be used only for a feature value dated `t`.
2. The feature value at `t` is known only after both the close and volume for
   `t` are available.
3. Any trade date, execution timing, rebalance schedule, signal lag, and
   slippage assumption must remain outside the alpha helper.
4. A formula must not use future close, future volume, future universe
   membership, or same-period target returns.
5. If the formula uses one-period deltas, tests must prove that changing a
   future row does not change the current signal.

## Missing And Zero-Volume Policy

Default future behavior should be strict:

- Missing close values are not filled.
- Missing volume values are not filled.
- Missing values consumed by the formula produce `NaN` for the affected
  asset/date.
- Close and volume panels must align exactly by date and asset before
  calculation.
- Non-numeric, boolean, unsorted, duplicate-date, or empty panels should be
  rejected through shared panel validation.
- Negative volume should be rejected before formula calculation.
- Zero volume should be handled explicitly in the formula-specific tests. It
  should not be silently converted to missing, positive volume, or a filled
  value.
- No forward-fill, backward-fill, interpolation, or zero default should be
  introduced.

## Required Future Tests

A future implementation PR should include deterministic synthetic tests for:

- hand-calculated formula output on a small close and volume panel.
- index, date, and column preservation.
- exact close/volume alignment requirements.
- no look-ahead from future close rows.
- no look-ahead from future volume rows.
- missing close behavior.
- missing volume behavior.
- zero-volume behavior.
- negative-volume rejection.
- non-positive close handling if the formula uses price deltas or ratios that
  require positive prices.
- sorted and duplicate date validation through shared panel validation.
- non-numeric and boolean input rejection.
- custom parameter validation if the reviewed formula requires parameters.
- no backtester, reporting, data-fetching, credential, broker, or order
  imports.

## Research Risks

Volume + close formulas add risks that close-only formulas do not fully expose:

- raw close versus adjusted close ambiguity.
- raw volume versus adjusted volume ambiguity after splits.
- formula transcription errors from public alpha references.
- symbol, calendar, and adjustment-policy mismatches between close and volume.
- stale, halted, suspended, or zero-volume rows.
- survivorship bias from static symbols.
- liquidity or volume behavior accidentally becoming a universe filter inside
  a factor helper.
- interpreting a formula smoke test as factor validity or profitability.

These risks should stay visible in engineering logs, experiment logs, and
future real-data readiness audits.

## Future PR-Sized Stages

1. Formula provenance and implementation PR for one volume + close alpha only,
   if the exact formula and tests are unambiguous. Completed for `alpha_012()`;
   still required separately for any other volume + close alpha.
2. Synthetic local-fixture smoke check that loads committed OHLCV data and
   computes the new alpha as a feature only, without backtesting or performance
   interpretation. Completed for `alpha_012()`.
3. Diagnostics-only update that evaluates the feature with existing synthetic
   IC / Rank IC / quantile spread helpers, still without strategy claims.
   Completed for `alpha_012()` in the synthetic local CSV fixture workflow.
4. QuantConnect/LEAN plan refresh if the volume + close feature changes the
   local-to-LEAN signal mapping assumptions.
5. Separate planning gate for any OHLC, VWAP, market-cap, or industry-neutral
   formula category.

Each stage should be a separate PR. Stop if a stage requires real data,
external downloads, vendor credentials, live or paper trading, brokerage
integration, order execution, or profitability claims.

## Recommended Next Stage After This Plan

After the Alpha#012 implementation, fixture smoke check, and fixture
diagnostics stages have merged, the next safe stage should be a
documentation-only QuantConnect/LEAN plan refresh if the feature changes
local-to-LEAN signal mapping assumptions.

That future stage should not add runnable LEAN code, data subscriptions,
platform access, credentials, brokerage behavior, orders, portfolio
construction, or performance interpretation. Remaining volume + close alphas
still require separate formula provenance, input-policy, missing-data, and test
review before any code is added.
