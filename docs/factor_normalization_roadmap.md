# Factor Normalization And Combination Roadmap

## Status: Historical / Superseded In Part

This roadmap is retained as design history. Normalization, winsorization,
factor combination, factor diagnostics, and Alpha#009 smoke coverage have since
been implemented and tested in `src/features/normalize.py`,
`src/features/combine.py`, `src/features/diagnostics.py`,
`src/features/worldquant_alphas.py`, `tests/test_normalize.py`,
`tests/test_combine.py`, `tests/test_diagnostics.py`, and
`tests/test_worldquant_alphas.py`.

The remaining live guidance is the research boundary: combined scores still
are not strategies, and any future backtest use must keep signal lag,
execution timing, costs, slippage, benchmark alignment, validation splits, and
no-performance-claim caveats explicit.

## Purpose

This document is a roadmap for factor normalization and factor-combination research infrastructure. It is documentation-only: it does not add helper code, connect factors to the backtester, fetch real market data, or claim profitability.

The goal is to define the policies that should exist before raw feature outputs such as momentum or `alpha_009` are combined into a cross-sectional score.

## Why Raw Factors Should Not Be Combined Directly

Raw factor values can differ in units, magnitude, sign convention, outlier behavior, and missing-value patterns. A direct sum of raw momentum, reversal, volatility, and WorldQuant-style alpha outputs can cause one factor to dominate only because its numerical scale is larger, not because it has stronger research support.

Raw factor combination can also hide data-quality problems. Missing values, stale values, or extreme outliers may affect a combined score in ways that are difficult to audit unless normalization and missing-value behavior are explicit.

## Terminology

- Raw factor: a direct feature output, such as 12-1 momentum or `alpha_009`.
- Normalized factor: a row-wise transformed factor, such as a cross-sectional z-score or percentile rank.
- Combined score: a weighted blend of normalized factors with documented sign conventions and missing-value behavior.
- Strategy: a complete research workflow including universe selection, signal lag, ranking, portfolio construction, costs, slippage, risk controls, benchmark comparison, and validation.

A combined score is not a strategy by itself. It becomes part of a strategy only after execution timing, portfolio construction, transaction costs, risk controls, and benchmark evaluation are specified.

## Normalization Methods

Cross-sectional z-score normalization should operate row-wise across assets for each date. It subtracts the cross-sectional mean and divides by the cross-sectional standard deviation, preserving the original date and asset labels. Rows with zero dispersion need explicit behavior in tested helper code.

Cross-sectional rank or percentile-rank normalization should also operate row-wise across assets for each date. It converts raw factor values into ordinal or percentile information, which can be more robust to extreme magnitudes than raw values.

Both approaches must use only values available at the feature timestamp. They must not sort, fill, lag, or align data implicitly in ways that change date availability.

## Winsorization And Outlier Control

Outlier control should be an explicit, tested policy. Winsorization can be useful before or during normalization, but it should not be hidden cleanup.

Future helper code should document quantile choices, row-wise behavior, and how missing values interact with clipping. Outlier treatment should be visible in experiment notes because it can materially change rankings and combined scores.

## Missing-Value Policy

Missing factor values should propagate by default. The project should not silently forward-fill, backward-fill, or zero-fill factor values.

Any future imputation, neutral fallback, or asset exclusion behavior must be explicit, opt-in, documented, and covered by tests. A missing factor value is a data-availability fact, not a neutral score unless a later research decision explicitly defines it that way.

## Factor Alignment Requirements

Factors must have aligned dates and assets before combination. A helper should not silently combine mismatched panels because that can create cross-asset or cross-date contamination.

Feature timestamps and execution timestamps must remain separate. A factor known after the close at date `t` is not automatically tradable at the same close. Signal lag and execution timing remain strategy-layer responsibilities.

## Deferred Factor Combination

Factor combination should be a later, separate PR after normalization helpers are implemented and tested.

Future combination helpers should define:

- input factor panel requirements.
- factor weights.
- sign conventions.
- missing-value behavior.
- output shape and alignment.

This roadmap does not choose factor weights or connect combined scores to any portfolio construction logic.

## Diagnostics Before Backtesting

Factor correlation diagnostics should come before backtest integration. They can help identify redundant factors, unstable factor relationships, accidental duplicate signals, and factor outputs that mostly measure the same effect.

Diagnostics should be treated as research visibility, not proof of profitability. They should support auditability before a combined score is evaluated in a backtest.

## Deferred Backtest Integration

`alpha_009` and future combined scores should not be connected to the backtester until normalization helpers, combination helpers, and diagnostics have tests.

Formula output is a research feature, not a trading strategy. Backtest integration should remain a separate milestone with explicit signal lag, execution timing, costs, slippage, turnover, benchmark comparison, and validation assumptions.

## Proposed Future PR Sequence

1. Add normalization helpers and tests.
2. Add factor combination helpers and tests.
3. Add factor correlation report.
4. Add `alpha_009` synthetic feature smoke demo.
5. Only later connect normalized or combined scores to the long-only backtest.
