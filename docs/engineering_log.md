# Engineering Log

This is a living engineering log for review notes, correctness audits, bug fixes, and implementation decisions that are useful for future PR summaries, interviews, retrospectives, and performance-review material.

## How To Update This Log

- Add a new dated entry after meaningful engineering work, especially after correctness reviews, bug fixes, test design changes, architecture decisions, or non-obvious tradeoffs.
- Do not use this log to claim profitability or investment performance.
- Separate observed facts from assumptions. Use `Assumption:` or `Needs follow-up:` when evidence is incomplete.
- Prefer specific engineering reasoning over generic status updates.
- Link or name the relevant files, functions, tests, and checks when possible.

---

## 2026-05-22 - Backtester Correctness Review: Silent Data Failures, Leakage Tests, and Return Semantics

### Context

This work was part of a correctness audit for a local equity factor research pipeline. The system already had a 12-1 month momentum feature, a minimal long-only cross-sectional backtester, basic metrics, a synthetic-data demo, and a QuantConnect/LEAN implementation plan.

The goal was not to add new strategy features. The goal was to run a strict read-only review first, identify subtle correctness risks, then make targeted fixes with tests. The review focused on failure modes that are especially dangerous in quantitative research: silent data fallbacks, hidden future leakage, ambiguous return semantics, benchmark alignment problems, and weak tests that pass on happy-path examples but fail to protect core invariants.

### What I Was Looking For

The review strategy was to look for places where the system could appear to work while producing misleading research output.

The main checks were:

- Where missing data could be silently converted into plausible market behavior.
- Where default values could make metrics look normal while hiding data-quality issues.
- Where signal and return alignment could allow same-day or future information leakage.
- Where tests asserted surface behavior but not the underlying correctness invariant.
- Whether benchmark handling had the same data-quality discipline as strategy returns.
- Whether momentum window tests covered nontrivial skip windows, not only the simplest case.
- Whether the backtest output exposed enough diagnostics to evaluate whether the result was trustworthy.

This was a correctness audit, not a performance optimization pass.

### Issues Found And Fixed

#### 1. Missing Held-Asset Prices Were Silently Treated As 0% Return

The issue:

The backtester computed asset returns and then filled missing returns with zero. That meant if an asset was already held and its next price was missing, the system treated the missing return as a real 0% return.

Why it was subtle:

This does not crash. The equity curve remains smooth, metrics still compute, and tests using complete synthetic data all pass. The failure only appears when real data has gaps, stale symbols, delistings, vendor issues, or incomplete histories.

Risk:

A missing price is not the same as a flat price. Treating missing data as 0% return can silently contaminate the equity curve, drawdown, volatility, turnover-adjusted performance, and benchmark-relative metrics.

Correct behavior:

For a first-phase research engine, the safest default is to fail loudly when a held asset has missing return data.

Fix:

Added an explicit missing held-price policy in `src/backtest/portfolio.py`:

- default: `missing_price_policy="raise"`
- diagnostic fallback: `missing_price_policy="zero_return"`

The default now raises `ValueError` when a held asset has a missing return. The zero-return behavior still exists only as an explicit, documented fallback.

Verification:

Added tests in `tests/test_backtest_portfolio.py` that confirm:

- default behavior raises when a held asset has missing return data.
- explicit `zero_return` policy allows the fallback and records the assumption.

#### 2. Future-Signal Leakage Test Was Too Weak

The issue:

The original future-signal test did not force a disagreement between the lagged signal and the same-day signal on the checked rebalance date. As a result, the test could still pass even if the backtester accidentally used same-day signals.

Why it was subtle:

The implementation was correct, but the test was not strong enough to protect the invariant. A test can give false confidence when it checks a scenario where both the correct and incorrect implementations produce the same output.

Risk:

In a backtest, using same-day or future signals can create inflated performance that looks legitimate. This is one of the most dangerous classes of research bugs because it often improves results instead of causing failures.

Correct behavior:

A rebalance on date `t` with `signal_lag_periods=1` must use the signal from the previous available date, not the signal stamped at `t`.

Fix:

Strengthened the test setup:

- date 0 signal ranks asset A highest.
- date 1 signal ranks asset B highest.
- date 1 rebalance must still hold asset A.
- if signal shifting is removed, the test fails because date 1 would hold asset B.

Verification:

The updated test directly protects the signal-lag invariant.

#### 3. `total_return` Used `equity_curve.iloc[0]` Instead Of Explicit Initial Capital

The issue:

The metrics function calculated total return as:

```text
final_equity / equity_curve.iloc[0] - 1
```

This assumes the first equity curve value is always the starting capital.

Why it was subtle:

With the default signal lag, first-row equity often remains equal to initial capital, so the issue is hidden. But if first-row trading costs or other initial adjustments exist, `equity_curve.iloc[0]` is no longer the true capital base.

Risk:

Return metrics can understate or hide first-period costs. The meaning of total return becomes dependent on how the equity curve is indexed rather than on an explicit capital convention.

Correct behavior:

Total return should be measured against the known initial capital base.

Fix:

Updated `src/backtest/metrics.py` so `calculate_basic_metrics` accepts and uses explicit `initial_capital`:

```text
total_return = final_equity / initial_capital - 1
```

Benchmark total return now uses the same explicit base.

While adding the test, I also found that first-row turnover was not being counted correctly when `signal_lag_periods=0`. That was fixed so first-row entry costs can be represented.

Verification:

Added a test where first-row trading costs exist. The test verifies that total return includes those costs instead of using the already-cost-adjusted first equity value as the denominator.

#### 4. Missing Benchmark Prices Were Silently Filled As Zero Returns

The issue:

Benchmark prices were reindexed to strategy dates. Missing benchmark returns were then filled with zero.

Why it was subtle:

This makes benchmark series look complete even when benchmark data is missing. The benchmark equity curve remains usable, so the problem is easy to miss.

Risk:

A missing benchmark return is not neutral. Filling it with zero makes a concrete assumption that the benchmark was flat. That can distort benchmark total return, excess return, alpha-like diagnostics, and performance interpretation.

Correct behavior:

Benchmark data gaps should be explicit.

Fix:

Added a benchmark missing-data policy in `src/backtest/portfolio.py`:

- default: `benchmark_missing_policy="raise"`
- diagnostic fallback: `benchmark_missing_policy="zero_return"`

The default raises `ValueError` if benchmark prices are missing on strategy dates.

Verification:

Added tests for both default raise behavior and explicit zero-return fallback.

#### 5. Momentum Skip-Window Tests Did Not Cover Wider Skipped Windows

The issue:

Momentum tests covered a simple skip case, but not `skip_periods > 1`.

Why it was subtle:

The implementation used explicit shifts correctly, but off-by-one errors in momentum features often appear only when the skipped window is wider than one period.

Risk:

A wrong implementation could accidentally use prices inside the skipped recent window, or use the wrong boundary price, while still passing simple tests.

Correct behavior:

For a signal date `t`, the formula should be:

```text
momentum[t] = price[t - skip_periods] / price[t - lookback_periods] - 1
```

Interior prices between `t - skip_periods + 1` and `t` should not affect the signal.

Fix:

Added a test with `skip_periods=3` in `tests/test_momentum.py`:

- changing an interior skipped-window price does not change momentum.
- changing the boundary price at `t - skip_periods` does change momentum.

Verification:

The test protects both sides of the invariant: ignored interior prices and included boundary price.

#### 6. Signal Coverage Was Not Exposed

The issue:

After aligning signals to the price index and columns, the caller had no quick way to see how much signal data remained non-null.

Why it was subtle:

The backtester can still run with sparse signals. It may simply hold fewer names, skip assets, or produce plausible results. Without signal coverage diagnostics, a user may not realize the backtest is running on weak or incomplete signal data.

Risk:

A strategy can appear valid while most of its intended universe has missing signals.

Correct behavior:

Signal coverage should be visible as part of backtest assumptions or diagnostics.

Fix:

Added aligned signal coverage to the backtest result assumptions:

```text
result.assumptions["aligned_signal_coverage"]
```

Verification:

Added a test asserting full coverage in a complete signal example.

### Deep Reasoning

These issues share a common pattern: the system was mostly correct on clean synthetic data, but several defaults could hide problems once the data became messy.

The biggest engineering risk in a backtester is not always a crash. Often the bigger risk is a plausible number produced from bad assumptions.

Examples:

- A missing held-asset return filled with `0.0` is not neutral. It converts a data-quality issue into a fake market observation.
- `equity_curve.iloc[0]` looks like a convenient base, but it conflates starting capital with first recorded portfolio value.
- A missing benchmark return filled with zero does not mean unknown; it means the benchmark was flat.
- A future-leakage test must use inputs where the correct and incorrect implementations diverge. Otherwise the test only verifies that code runs.
- Signal coverage is part of backtest credibility. It is not just debugging metadata.

The broader lesson is that a research pipeline needs explicit semantics at the boundaries: data availability, signal timing, return calculation, benchmark alignment, and missing-data behavior.

### Tests Added Or Strengthened

The test suite was strengthened around specific invariants.

- Held asset missing price: verifies default behavior raises when a held asset has missing return data.
- Explicit zero-return fallback: verifies the fallback is opt-in and visible in assumptions.
- Future-signal leakage: verifies date `t` rebalance uses date `t-1` signal when `signal_lag_periods=1`.
- Total return base: verifies first-row costs are included when measuring return against `initial_capital`.
- Benchmark missing data: verifies missing benchmark dates raise by default.
- Benchmark zero-return fallback: verifies benchmark zero-return behavior is opt-in and documented through assumptions.
- Momentum `skip_periods > 1`: verifies skipped-window interior prices do not affect the signal, while the boundary price does.
- Signal coverage: verifies aligned signal coverage is exposed in backtest assumptions.

These tests are not just coverage additions. Each one protects a correctness invariant that could otherwise silently fail.

### Outcome

The system moved from "runs correctly on clean examples" toward "fails loudly on dangerous data assumptions."

Key improvements:

- Missing held-asset prices no longer silently freeze P&L.
- Benchmark data gaps no longer silently become flat benchmark returns.
- Total return now has an explicit capital base.
- Signal lag behavior is protected by a stronger leakage test.
- Momentum window behavior is tested for wider skip periods.
- Signal coverage is exposed as a first-pass observability diagnostic.

No real market data was fetched. No live trading was added. No profitability claims were made.

Validation at the time of this entry:

```text
python -m pytest -q
24 passed

python -m compileall src tests research
passed

python -m research.synthetic_momentum_demo
passed
```

### Interview Story Version

Situation:

I was building a local quantitative research pipeline with a 12-1 momentum feature, a long-only cross-sectional backtester, basic metrics, and a synthetic-data demo. Before adding more features, I wanted to audit the implementation for correctness risks that could invalidate future research.

Task:

The goal was to perform a strict read-only review first, identify subtle bugs, then make targeted fixes without changing project scope. I focused on look-ahead bias, missing data behavior, return semantics, benchmark alignment, and whether the tests actually protected the intended invariants.

Action:

I inspected the momentum calculation, portfolio return path, benchmark handling, metrics calculation, and tests. The code was mostly correct on the happy path, but I found several silent failure modes. Held-asset missing returns were being filled as 0%, benchmark gaps were also effectively frozen, and total return inferred its base from the first equity curve value. I also found that the future-signal leakage test would not necessarily fail if signal lagging were removed.

I fixed these with explicit policies and stronger tests. Missing held-asset prices now raise by default. Benchmark gaps raise by default. Total return uses explicit initial capital. The future-leakage test now constructs a case where same-day and lagged signals choose different assets. I also added a wider momentum skip-window test and exposed signal coverage in the backtest assumptions.

Result:

The backtester became more auditable and less likely to produce misleading results from bad data or ambiguous accounting. The final checks passed: the full pytest suite, compile check, and synthetic demo all ran successfully. More importantly, the tests now protect the correctness assumptions that matter most for a financial research pipeline.

### Resume / Performance Review Bullets

- Performed a correctness audit of a Python quantitative backtesting pipeline, identifying silent data-quality failures in held-asset returns, benchmark alignment, and return-base semantics.
- Strengthened backtest invariants by adding explicit missing-data policies, signal-lag validation, initial-capital-based return calculation, and signal coverage diagnostics.
- Improved unit tests to catch future-signal leakage, momentum window off-by-one errors, benchmark data gaps, and missing held-price behavior.
- Converted ambiguous silent fallbacks into explicit default failures with opt-in diagnostic policies for synthetic or controlled research scenarios.
- Preserved project scope by fixing correctness issues without adding live trading, external data fetching, or unsupported profitability claims.

### PR Summary Draft

This change tightens correctness guarantees in the research backtester and momentum tests. Missing held-asset returns and missing benchmark prices now raise by default instead of being silently treated as zero-return observations. Total return is now calculated against explicit `initial_capital`, avoiding ambiguity when the first equity-curve row already includes costs. The signal-lag test was strengthened so it fails if same-day signals are accidentally used. Momentum tests now cover wider skipped windows, and the backtest result exposes aligned signal coverage for basic observability.

Tests added or strengthened cover held-asset missing prices, explicit zero-return fallback policies, future-signal leakage, total-return base semantics, benchmark missing-data handling, `skip_periods > 1` momentum behavior, and signal coverage exposure.

---

## 2026-05-22 - WorldQuant Alpha Catalog Stage 1

This was a documentation-only, catalog-first milestone for adding WorldQuant-style alpha research to the project. The work created `docs/worldquant_alpha_catalog.md` to classify the 101 Formulaic Alpha references by data requirement and priority before any implementation work.

No alpha code, operator layer, real market data, or backtest integration was added. The catalog explicitly treats the formulas as educational research references, not trading recommendations or guaranteed profitable strategies.

The next milestone is operator-layer implementation and tests, not alpha backtesting.

Validation:

```text
python -m pytest -q
24 passed
```

---

## 2026-05-23 - WorldQuant Operator Layer Stage 2

This milestone added a reusable pandas operator layer for future WorldQuant-style alpha research. The work is infrastructure only: no alpha formulas, backtest integration, real data fetching, live trading, or profitability claims were added.

The key correctness decisions were to require sorted date-indexed DataFrames, preserve index and columns, use full trailing windows for rolling operators, reject invalid non-numeric panel values instead of silently coercing them to missing data, and require exact index/column matches for pairwise operators such as rolling correlation, rolling covariance, and safe division.

Tests were added for hand-calculated examples, missing-data propagation, invalid input handling, tie behavior in ranks, zero-denominator division, zero cross-sectional standard deviation, full-window rolling behavior, and future-row isolation for time-series operators.

Follow-up review note:

The read-only review found one subtle validation gap: `astype(float)` correctly rejects values such as `"bad"`, but can silently convert string sentinel values such as `"nan"` into real missing values. That behavior would blur the difference between an intentional missing value and an invalid non-numeric data error. The validator was tightened to require numeric, non-boolean dtypes before conversion to a float copy, rejecting object, string, category, boolean, and numeric-looking string columns. Regression tests were added for `"nan"`, `"NaN"`, and `"1.0"` string inputs while preserving support for real numeric `NaN` values in numeric columns. The `ts_rank` docstring was also clarified to state that ties use average rank by default and that `pct=True` returns percentile ranks.

Validation at the time of this entry:

```text
python -m pytest -q
46 passed
```
