# Engineering Log

This is a living engineering log for review notes, correctness audits, bug fixes, and implementation decisions that are useful for future PR summaries, interviews, retrospectives, and performance-review material.

## How To Update This Log

- Add a new dated entry after meaningful engineering work, especially after correctness reviews, bug fixes, test design changes, architecture decisions, or non-obvious tradeoffs.
- Do not use this log to claim profitability or investment performance.
- Separate observed facts from assumptions. Use `Assumption:` or `Needs follow-up:` when evidence is incomplete.
- Prefer specific engineering reasoning over generic status updates.
- Link or name the relevant files, functions, tests, and checks when possible.

---

## 2026-06-02 - CSV Loader Missing-Value Debug And Fix

This bugfix corrected strict missing-value validation in the local CSV loader
after a WSL-only test failure exposed a pandas version difference.

Initial mistake:

- The first fix assumed that `pd.read_csv(..., keep_default_na=False,
  dtype=str)` was sufficient to preserve raw CSV values through validation.
- The missing-value detector still checked sentinel strings only when
  `values.dtype == object`.
- That assumption held in the Windows validation environment, where the focused
  CSV loader tests and full test suite passed, but it did not cover WSL with
  pandas 3.0.3.

Consequence:

- In WSL, `pd.read_csv(..., dtype=str)` produced a pandas string dtype rather
  than an `object` dtype.
- `_missing_value_mask` therefore skipped the string-sentinel branch for an
  empty wide-price value.
- The empty string was then passed to `pd.to_numeric`, which converted it to
  `NaN` instead of raising before the loader's strict default policy could
  reject it.
- As a result, `load_wide_price_csv(..., allow_missing=False)` accepted a blank
  numeric field that should have failed.

Failing evidence:

```text
tests/test_csv_loader.py::test_load_wide_price_csv_rejects_invalid_or_missing_numeric_values_by_default[]
bad_value = ""
Failed: DID NOT RAISE any of (<class 'TypeError'>, <class 'ValueError'>)
```

The WSL run also showed large apparent diffs across docs, reports, research
scripts, source modules, and tests. Review showed those broad diffs were
line-ending noise from the Windows/WSL working tree, not intended source
changes.

Investigation:

- Confirmed WSL imported the expected module:
  `src/data/csv_loader.py`.
- Confirmed WSL was using pandas 3.0.3.
- Printed `_read_local_csv` and verified it already used
  `keep_default_na=False, dtype=str`.
- Probed a temporary CSV containing a blank `AAPL` field. WSL read the column
  with dtype `str`, represented the blank as `""`, and returned
  `_missing_value_mask == [False, False]`.
- Confirmed `_parse_numeric_column` then returned `[100.0, NaN]` and the loader
  accepted the file instead of raising.

Correction attempts:

- The first Windows-side correction added `dtype=str` and expanded tests for
  `NA` and whitespace-only values. That made Windows tests pass, but it did not
  address pandas string dtype in WSL.
- Applying the saved WSL patch directly on the independent bugfix branch worked
  functionally but introduced whole-file CRLF/LF whitespace noise. That patch
  was restored before commit.

Final fix:

- `_read_local_csv` now reads local CSV files with
  `pd.read_csv(path, keep_default_na=False, dtype=str)` so raw string values are
  preserved before validation.
- `_missing_value_mask` now checks both `object` dtype and pandas string dtype
  via `pd.api.types.is_string_dtype(values.dtype)` before applying the sentinel
  set.
- `tests/test_csv_loader.py` now covers `""`, whitespace-only strings, `nan`,
  `NaN`, `NA`, `null`, and a nonnumeric `bad` value for strict default
  validation.

Verification:

```text
WSL python -m pytest -q tests/test_csv_loader.py
19 passed

WSL python -m pytest -q
209 passed

WSL python -m compileall src tests research
passed

git diff --check origin/main..HEAD
passed
```

Scope review:

- Meaningful branch diff was limited to `src/data/csv_loader.py` and
  `tests/test_csv_loader.py`.
- The direct WSL patch application was rejected as a commit candidate because
  it carried line-ending noise.
- The committed branch used only the minimal semantic patch.

Remaining caveats:

- Windows and WSL can still display noisy diffs if line endings are touched
  broadly.
- Future CSV loader changes should inspect both normal diffs and
  `git diff --ignore-space-at-eol` before staging.
- Environment-specific behavior should be checked when pandas dtype handling is
  part of the bug.

Prevention:

- Treat pandas dtype assumptions as version-sensitive.
- Keep missing-value checks independent of only one dtype spelling.
- When fixing validation behavior, probe the raw value, dtype, missing mask,
  conversion result, and final loader behavior in the environment that reported
  the failure.
- Do not consider a technical fix complete until this type of full debug chain
  is recorded in the relevant engineering log.

This fix did not fetch real data, add vendor access, add live trading, add
brokerage or order-execution logic, store credentials, modify backtester or
metrics behavior, modify synthetic reports, or make profitability claims.

---

## 2026-06-02 - QuantConnect/LEAN CSV Validation Mapping

This documentation-only milestone updated `docs/quantconnect_lean_plan.md` to
map the future local CSV validation checklist to QuantConnect/LEAN data,
calendar, universe, benchmark, fee, slippage, and execution assumptions.

The new mapping treats local CSV validation and LEAN backtests as separate
research artifacts. Local CSV checks improve auditability of user-provided
files, but LEAN runs must still document platform datasets, data normalization,
scheduled event timing, skipped symbols, benchmark configuration, brokerage
model, fee model, slippage model, order type, cash buffer, and diagnostics.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, or synthetic demos. It does
not fetch data, download data, add vendor access, introduce live trading, add
brokerage or order-execution logic, store credentials, or make profitability
claims.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Real-Data Readiness Audit Checklist

This documentation-only milestone added `docs/real_data_readiness_audit.md` as a pre-experiment checklist for using user-provided local CSV data.

The checklist covers scope statements, data provenance, schema and loader checks, price adjustment policy, universe construction, benchmark choice, feature and signal timing, sample splits, costs, slippage, experiment-log fields, stop conditions, and an approval gate before any local CSV run is interpreted.

It does not fetch data, download data, choose a vendor, implement a loader, change feature calculations, modify backtester behavior, alter reports, introduce live trading, add brokerage or order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Local CSV Loader

This milestone added a strict local CSV loader module for user-provided files under `src/data/csv_loader.py`.

The loader supports wide adjusted-close price panels, long adjusted-close price rows that are pivoted to a date-asset panel, and benchmark price series. It reads local `.csv` files only, rejects remote URL-like paths, validates parseable dates, rejects duplicate or unsorted dates where order matters, rejects duplicate long `(date, symbol)` rows, parses numeric fields with explicit errors, preserves missing values only when requested, and rejects non-positive prices.

This does not fetch real data, choose a vendor, add downloads, change feature calculations, modify backtester behavior, alter reports, introduce live trading, add brokerage or order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - CSV Data Interface Design Plan

This documentation-only milestone added `docs/csv_data_interface_plan.md` as a design plan for a future local CSV research interface.

The plan defines intended local CSV data types, proposed wide and long schemas, validation rules, alignment expectations for existing feature/backtest modules, and risks around survivorship bias, corporate actions, delistings, adjusted versus raw prices, vendor differences, and benchmark mismatch.

It does not implement a loader, fetch real data, add remote downloads, change feature calculations, modify backtester behavior, alter reports, introduce live trading, add brokerage or order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Synthetic Multi-Factor Parameter Sweep

This research-process milestone added a deterministic synthetic-only parameter sweep for the combined-score backtest workflow.

The sweep varies only explicit factor weight sets and selected-asset counts while holding synthetic seeds, date range, transaction cost, signal lag, benchmark, and execution assumptions fixed. It reports every configured case in `reports/synthetic_multifactor_parameter_sweep.md`, writes a JSON log under `reports/experiment_logs/`, and refreshes the synthetic experiment registry.

This is a sensitivity smoke test, not parameter selection or strategy validation. It does not change feature calculations, backtester behavior, strategy logic, real-data access, live trading functionality, brokerage integration, order execution, or profitability claims.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Structured Synthetic Experiment Registry

This research-process milestone added a structured registry helper for the synthetic JSON experiment logs.

The helper validates required log fields and synthetic-research caveats, rejects duplicate experiment IDs, builds a deterministic registry table, and writes `reports/experiment_registry.md` as a caveated review report. The report summarizes existing synthetic logs only; it does not run experiments, recalculate metrics, choose parameters, fetch real data, or make profitability claims.

This does not change feature calculations, strategy logic, backtester behavior, report metrics, data access, live trading functionality, brokerage integration, order execution, or credential handling.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Synthetic Demo Experiment Logging Automation

This research-process milestone added deterministic JSON experiment-log sidecars for the existing synthetic demos.

The logs capture each demo's configuration, synthetic-only data assumptions, caveats, output paths, and diagnostics or metrics. Backtest smoke-test logs also record benchmark choice, transaction-cost assumptions, signal lag, execution-timing assumptions, and the explicit caveat that slippage is not separately modeled.

This does not change feature calculations, strategy logic, backtester behavior, portfolio construction, report metrics, real-data access, brokerage integration, live trading functionality, or profitability claims. The logs are reproducibility and auditability metadata for synthetic workflows only.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Post-4H Checkpoint Review

This documentation-only checkpoint reviewed the repository after the synthetic combined-score backtest smoke test was merged to `main`.

The review synced `main`, confirmed the latest reviewed commit was `6811b58`, reran the full test suite and compile check, and interpreted guardrail grep matches for live trading, brokerage, real-data fetching, and profitability language. The matches were governance warnings, synthetic caveats, LEAN planning caveats, module docstrings, or tests that enforce forbidden-import and warning-language rules.

No source code, tests, strategy logic, backtester behavior, feature calculations, report-generation code, data access, live trading functionality, or profitability claims were changed.

Validation:

```text
python -m pytest -q
171 passed

python -m compileall src tests research
passed
```

---

## 2026-05-28 - Repository Checkpoint Audit And Phase Report

This documentation-only checkpoint captured the project state before moving from individual factor normalization helpers toward factor combination work.

The audit reviewed tracked files, stage traceability, test status, scope guardrails, and current limitations. It did not change source code, tests, strategy logic, reports, real data access, backtester behavior, metrics, or profitability claims.

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

---

## 2026-05-25 - Stage 3 Planning Rationale: Start With alpha_009 Only

Stage 3 intentionally starts with a single WorldQuant-style alpha candidate: `alpha_009`. This is a scope-control decision, not a rejection of `alpha_012`, `alpha_101`, or the broader WorldQuant 101 set as future research candidates. The project is deliberately avoiding a bulk implementation milestone because formulaic alpha work is only useful if each formula has clear data requirements, date alignment, missing-data behavior, and tests.

`alpha_009` is the safest first candidate because it is close-only. The repository already has close-price-based feature work, and the Stage 2 reusable operator layer now provides the primitives needed for this formula: strict panel validation, one-period deltas, and full trailing rolling minimum and maximum operators. It does not require volume, OHLC, VWAP, market cap, or industry classification schemas. That makes it a good first formulaic alpha for testing operator reuse, date alignment, missing-data propagation, strict input validation, and no-look-ahead behavior without expanding the data model.

Other candidates remain staged. `alpha_012` requires volume + close data, so it should wait until the project defines a volume schema and adds volume-specific validation tests. `alpha_101` requires OHLC inputs, so it should wait until the project has explicit open, high, low, and close schemas plus safe denominator handling and OHLC alignment tests. VWAP, market cap, and industry-neutral alphas remain deferred until the project has explicit data support and validation rules for those inputs.

The WorldQuant 101 Formulaic Alphas are treated here as educational formulaic alpha references, not guaranteed profitable trading strategies. A formulaic alpha is not a complete strategy. It still requires universe selection, data cleaning, date alignment, signal lag, ranking or normalization, portfolio construction, transaction costs, slippage assumptions, risk controls, benchmark comparison, and out-of-sample validation before it can be evaluated as part of a research workflow.

The implementation philosophy for this project is to keep milestones small and reviewable. Reusable operators are tested before formulas. Formulas are implemented one at a time. Alpha outputs are not connected to the backtester until formula correctness has been reviewed. Real market data is deferred until synthetic and unit-test behavior is stable. No profitability claim is made from implementing a formula alone.

Codex is being used as an engineering agent, not as a strategy oracle. Stage 3 prompts use hard preflight checks, strict allowed-file lists, no-go conditions, self-checks after implementation, read-only review before commit, and separate commit and PR steps. When subagents are used, their role is read-only review or scoped analysis; they are not used to modify the same files concurrently.

The prompt workflow is also designed to be queue-safe. Each prompt checks the active branch, working-tree cleanliness, test status, and allowed file set before proceeding. If a prerequisite fails, the prompt must stop instead of continuing. This prevents later queued tasks from blindly building on a broken, stale, or dirty state.

Explicit Stage 3 non-goals:

- no `alpha_012`
- no `alpha_101`
- no full WQ101 implementation
- no backtester integration
- no performance report
- no real data fetching
- no live trading
- no profitability claim

---

## 2026-05-25 - WorldQuant Alpha#009 Stage 3

This milestone implemented `alpha_009` as the first close-only WorldQuant-style alpha candidate. The function is a research feature only: it calculates a point-in-time-safe signal from close prices and does not define portfolio construction, execution timing, backtest integration, or expected profitability.

The implementation uses the reusable operator layer from Stage 2. It computes one-period close deltas, evaluates full trailing rolling windows over those deltas, and applies the Alpha#009 rule: continue the current delta when the trailing delta window is strictly all positive or strictly all negative; otherwise use the negative current delta. A zero delta falls into the mixed-window branch because the conditions are strict.

Date alignment is explicit: the feature at date `t` may use `close[t]` and earlier closes only, so it is known after the close at `t`. Trading lag remains the responsibility of a later strategy or backtest layer.

Tests were added for hand-calculated positive, negative, mixed, and zero-delta cases; output shape preservation; future-row isolation; missing close behavior; strict input validation; window validation; and absence of backtest integration imports.

No real market data was fetched. No reports were modified. No profitability claim or strategy performance result was added.

Validation at the time of this entry:

```text
python -m pytest -q
60 passed
```

---

## 2026-05-25 - Pull Request and Commit Hygiene Rules

This documentation-only governance update added explicit pull request and commit discipline to `AGENTS.md`.

The project is adopting small, meaningful PR and commit practices to improve reviewability and traceability. The goal is not artificial PR or commit inflation. Trivial edits should not be split just to increase counts, and unrelated changes should not be combined into one PR.

Future alpha work should continue to be split by clear milestones, such as planning, tests or documentation, implementation, read-only review, and PR review.

No source code, tests, strategy logic, backtester behavior, metrics, reports, real data fetching, or profitability claims were changed.

---

## 2026-05-28 - Factor Correlation Diagnostics

This milestone added diagnostic-only factor correlation infrastructure for aligned factor panels.

The helper measures pairwise Pearson or Spearman relationships across flattened factor panels using overlapping non-missing observations only. It preserves factor names, validates panel alignment, and does not fill missing values.

Factor selection, model training, backtest integration, performance reporting, real data fetching, new alpha formulas, and profitability claims remain deferred.

---

## 2026-05-28 - Factor Combination Helper

This milestone added a narrow helper for combining already-preprocessed factor panels with explicit weights.

The helper enforces exact date and asset alignment, finite non-boolean weights, at least one nonzero weight, and strict missing-value behavior before producing a weighted combined score.

Normalization, factor correlation diagnostics, synthetic alpha smoke demos, backtest integration, real data fetching, new alpha formulas, reports, and profitability claims remain deferred.

---

## 2026-05-27 - Cross-Sectional Z-Score Normalization Helper

This milestone added the first factor normalization helper: cross-sectional z-score normalization for date-indexed asset factor panels.

The helper is intentionally narrow. It reuses the existing strict operator-layer validation and row-wise z-score behavior so missing factor values remain visible, zero-dispersion cross-sections produce `NaN`, and index and asset alignment are preserved.

Rank normalization, factor combination, factor diagnostics, synthetic alpha smoke demos, and backtest integration remain deferred to later PRs.

No backtester behavior, metrics, WorldQuant alpha formulas, reports, real data fetching, or profitability claims were changed.

---

## 2026-05-28 - Cross-Sectional Factor Winsorization Helper

This milestone added a row-wise winsorization helper for date-indexed asset factor panels.

The helper is intentionally limited to factor preprocessing. It preserves missing values, reuses strict panel validation, and clips each date's cross-section independently using explicit lower and upper quantile bounds.

Factor combination, factor correlation diagnostics, synthetic alpha smoke demos, and backtest integration remain deferred to later PRs.

No backtester behavior, metrics, WorldQuant alpha formulas, reports, real data fetching, or profitability claims were changed.

---

## 2026-05-27 - Rank-Based Factor Normalization Helpers

This milestone added rank-based factor normalization helpers for date-indexed asset factor panels: ordinal cross-sectional ranks and pandas-style percentile ranks.

The helpers are intentionally limited to row-wise ranking across assets. They preserve missing values, reuse strict panel validation, and document that pandas percentile ranks use `pct=True` semantics rather than min-max percentile scaling.

Winsorization, factor combination, factor correlation diagnostics, synthetic alpha smoke demos, and backtest integration remain deferred to later PRs.

No backtester behavior, metrics, WorldQuant alpha formulas, reports, real data fetching, or profitability claims were changed.

---

## 2026-05-25 - Factor Normalization And Combination Roadmap

This documentation-only roadmap defines the next research infrastructure step before combining factor outputs or connecting WorldQuant-style alphas to the backtester.

The roadmap explains why raw factor values should not be combined directly, distinguishes raw factors from normalized factors, combined scores, and full strategies, and records expected policies for cross-sectional normalization, ranking, winsorization, missing values, factor alignment, and correlation diagnostics.

The intended future sequence is normalization helpers first, factor combination helpers second, factor correlation diagnostics third, an `alpha_009` synthetic feature smoke demo fourth, and backtest integration only after those pieces are tested.

No source code, tests, strategy logic, backtester behavior, metrics, reports, real data fetching, or profitability claims were changed.

---

## 2026-05-28 - Synthetic Multi-Factor Workflow Demo

This milestone added a synthetic-only workflow demo showing how existing factor preprocessing, normalization, diagnostics, and combination helpers can be used together on deterministic factor panels.

The demo applies row-wise winsorization, z-score normalization, rank-based normalization, factor correlation diagnostics, and explicit weighted factor combination before writing a synthetic workflow report.

It does not add backtest integration, portfolio construction, real market data, new alpha formulas, reports beyond the synthetic demo report, live trading functionality, or profitability claims.

---

## 2026-05-28 - Synthetic Combined-Score Backtest Smoke Test

This milestone added a synthetic-only smoke test that passes a deterministic combined factor score into the existing long-only backtester.

The workflow generates synthetic prices and synthetic factor panels, applies existing factor preprocessing and normalization helpers, combines z-scored factors with explicit weights, and runs the existing backtester with transaction costs and signal lag.

The output is a workflow diagnostic only. It does not modify backtester or feature helper behavior, fetch real market data, add broker or live trading logic, introduce order execution, or make profitability claims.
