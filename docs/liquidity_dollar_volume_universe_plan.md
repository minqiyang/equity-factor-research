# Liquidity And Dollar-Volume Universe Plan

Date: 2026-06-06

This document plans future local liquidity and dollar-volume universe
selection before any code filters assets by volume.

It is documentation only. It does not implement a universe filter, modify
loaders, modify features, modify backtests, add research scripts, generate
reports, fetch data, download data, choose a vendor, add credentials, connect
to a broker, place orders, support live or paper trading, or make
profitability claims.

## Purpose

The project now has strict local OHLCV CSV validation and synthetic fixture
smoke coverage. The next prerequisite for liquidity-aware research is a
reviewed universe-selection plan that states exactly how volume and
dollar-volume inputs may be used without introducing look-ahead bias,
survivorship bias, silent missing-data repair, or performance interpretation.

This plan defines local-only inputs, candidate formulas, date-alignment rules,
zero-volume handling, validation requirements, risks, and future PR-sized
implementation gates.

## Non-Goals

- No source-code implementation.
- No changes to `src/data/csv_loader.py`, `src/features/`, `src/backtest/`,
  `src/reporting/`, `research/`, `reports/`, or tests in this stage.
- No user-provided or real-market data.
- No downloads, vendor APIs, `requests`, `yfinance`, Alpaca, CCXT, or
  credential logic.
- No live trading, paper trading, brokerage integration, order execution, or
  account handling.
- No new alpha formula, strategy, backtest, LEAN runtime behavior, portfolio
  construction, slippage model, or benchmark interpretation.
- No automatic forward-fill, backward-fill, zero-fill, interpolation, or
  liquidity repair.
- No profitability, investment-performance, robustness, or trading-readiness
  claim.

## Current Prerequisites

Current local data support relevant to liquidity planning:

| Prerequisite | Current evidence | Status |
| --- | --- | --- |
| Strict local OHLCV loader | `load_ohlcv_csv()` in `src/data/csv_loader.py` | Implemented and tested. |
| Synthetic OHLCV fixture smoke coverage | `tests/test_local_csv_loader_smoke_demo.py` and `tests/fixtures/local_csv_loader_smoke/synthetic_ohlcv.csv` | Implemented with committed synthetic fixture only. |
| Split-aware diagnostics | `src/features/validation.py`, `src/features/diagnostics.py`, and related tests | Implemented for synthetic/local-fixture workflows. |
| Real-data readiness gate | `docs/real_data_readiness_audit.md` | Documentation gate only; no real-data run approved. |
| Experiment-log requirements | `EXPERIMENT_LOG.md` and reporting helpers | Synthetic logging exists; real-data records remain gated. |

These prerequisites do not prove any universe rule works. They only make the
next planning and synthetic implementation stages reviewable.

## Candidate Inputs

Future liquidity and dollar-volume work should use local files already present
on disk and validated by reviewed loaders.

| Input | Required source | Notes |
| --- | --- | --- |
| `date` | OHLCV long CSV | Observation date; must be timezone-naive and sorted after validation. |
| `symbol` | OHLCV long CSV | Asset identifier; duplicate `(date, symbol)` rows are rejected. |
| `volume` | OHLCV long CSV | Non-negative share volume; zero volume is allowed by the loader but must be reported by liquidity workflows. |
| `close` | OHLCV long CSV | Raw close unless adjustment policy says otherwise. |
| `adjusted_close` | Optional OHLCV field | Preferred for adjusted-return research when available; not automatically interchangeable with raw close. |
| Universe sidecar | Future optional local CSV | Must be date-stamped and point-in-time if used. |
| Metadata | Future optional sidecar or experiment log | Should record source, adjustment policy, volume policy, currency, and calendar limitations. |

No future implementation should infer missing input fields or fetch them from a
remote service.

## Candidate Liquidity Measures

### Average Daily Volume

Candidate formula:

```text
ADV_t = rolling_mean(volume, window=N)
```

Use:

- simple share-volume screening.
- debugging when price adjustment policy is unclear.

Risks:

- share volume is not comparable across price levels.
- adjusted versus raw volume after splits can differ by source.
- zero-volume and stale-volume periods need explicit reporting.

### Dollar Volume

Candidate formula:

```text
dollar_volume_t = close_t * volume_t
```

or, when the adjustment policy is explicitly compatible:

```text
dollar_volume_t = adjusted_close_t * volume_t
```

Use:

- approximate tradeability screening.
- future liquidity-aware universe construction.

Risks:

- raw close times raw volume and adjusted close times raw volume are different
  conventions.
- split-adjusted price with raw volume can distort historical dollar volume.
- adjusted volume, if present in a future source, must be documented before
  use.
- benchmark-relative or portfolio results cannot be interpreted from this
  planning stage.

### Rolling Dollar Volume

Candidate formula:

```text
rolling_dollar_volume_t = rolling_mean(price_t * volume_t, window=N)
```

Use:

- reducing single-day liquidity spikes.
- future minimum-history and universe membership checks.

Risks:

- rolling windows introduce warm-up periods.
- missing volume or price values should make the rolling value missing unless
  an explicit, reviewed policy says otherwise.
- rolling values must be based only on data known before the selection date.

## Date Alignment Rules

Future universe filters must maintain explicit timing:

1. Observation date: the date for OHLCV rows used to compute liquidity.
2. Universe decision date: the date on which a symbol becomes eligible or
   ineligible.
3. Signal date: the date a factor value is calculated after universe
   eligibility is known.
4. Execution date: the date a simulated rebalance would trade after signals
   are known.

Default planning assumption:

```text
liquidity inputs through date t may only affect eligibility on date t+1 or
later unless a reviewed execution assumption proves same-day availability.
```

Future tests should include off-by-one cases for rolling windows and universe
membership dates.

## Missing And Zero-Volume Policy

Default future behavior should be strict:

- Missing price or volume values should not be filled.
- Missing liquidity values should make the symbol ineligible for the affected
  decision date unless a later reviewed stage defines a different policy.
- Zero volume should be reported separately from missing volume.
- Zero volume should not be silently converted to missing or accepted as
  liquid.
- Negative volume is invalid and already rejected by the OHLCV loader.
- Non-positive prices are invalid for dollar-volume calculations and already
  rejected by the OHLCV loader for OHLC and adjusted-close fields.

The loader's zero-volume acceptance is a validation choice, not a liquidity
eligibility choice.

## Proposed Universe Rules

Future implementation stages can consider one small rule at a time.

| Rule | Description | Planning status |
| --- | --- | --- |
| Minimum ADV | Eligible when rolling average volume is at least a configured threshold. | Future synthetic implementation only. |
| Minimum dollar volume | Eligible when rolling average dollar volume is at least a configured threshold. | Future synthetic implementation only. |
| Minimum history | Eligible only after enough observed rows exist for the rolling window. | Required for rolling rules. |
| Stale or zero-volume exclusion | Eligible only when recent zero-volume count is below a configured limit. | Future design needed. |
| Static universe sidecar | Use a date-stamped local eligibility file. | Future planning needed before code. |

No rule should use future universe membership, future liquidity observations,
future prices, or same-period target returns as features.

## Validation Requirements For Future Code

Future code-changing PRs should include deterministic synthetic tests for:

- sorted date-symbol input handling.
- duplicate date-symbol rejection or reliance on validated loader output.
- rolling-window warm-up behavior.
- no look-ahead from date `t+1` into eligibility at date `t`.
- missing price or volume values making eligibility false by default.
- zero volume being reported and treated as not liquid by default when a
  threshold requires positive volume.
- raw close versus adjusted close field selection being explicit.
- all thresholds and windows being recorded in an audit summary.
- stable behavior when some symbols have shorter histories than others.
- no forward-fill, backward-fill, zero-fill, or interpolation.

## Research Risks

- Survivorship bias from static ticker lists.
- Liquidity filters that use future data by accident.
- Split and dividend adjustment mismatches between price and volume.
- Vendor differences in volume and corporate-action handling.
- Zero-volume rows caused by halted, stale, suspended, or illiquid securities.
- Calendar mismatch between assets.
- Thin trading that makes close-to-close returns misleading.
- Threshold overfitting if parameters are tuned after seeing results.
- Excluding difficult symbols in a way that hides failure modes.

These risks must be visible in future engineering logs, experiment logs, and
real-data readiness audits before any result is interpreted.

## Future PR-Sized Stages

1. Add a synthetic liquidity eligibility helper design or implementation
   decision if the exact function boundary is still ambiguous.
2. Implement a small synthetic-only liquidity eligibility helper with tests for
   rolling ADV or rolling dollar volume, missing values, zero volume, and
   date lag.
3. Add a synthetic local-fixture workflow check that reports liquidity
   eligibility counts without running a strategy.
4. Add experiment-log fields for liquidity threshold, rolling window, price
   field, volume policy, zero-volume count, and eligibility lag.
5. Revisit `alpha_012` or other volume-dependent factor planning only after
   liquidity eligibility and volume input handling are tested.

Each stage should stop if it requires real data, external downloads, vendor
credentials, live or paper trading, brokerage integration, order execution, or
profitability claims.

## Recommended Next Stage

After this plan is reviewed and merged, the next safe stage should be a
synthetic-only liquidity eligibility helper design or implementation decision.

If scope is clear, implement a small helper that produces date-symbol
eligibility from validated synthetic panels using an explicit lag. If scope is
still ambiguous, add a narrower checklist first.
