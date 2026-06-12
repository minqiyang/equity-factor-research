# Engineering Log

This is a living engineering log for review notes, correctness audits, bug fixes, and implementation decisions that are useful for future PR summaries, interviews, retrospectives, and performance-review material.

## How To Update This Log

- Add a new dated entry after meaningful engineering work, especially after correctness reviews, bug fixes, test design changes, architecture decisions, or non-obvious tradeoffs.
- Do not use this log to claim profitability or investment performance.
- Separate observed facts from assumptions. Use `Assumption:` or `Needs follow-up:` when evidence is incomplete.
- Prefer specific engineering reasoning over generic status updates.
- Link or name the relevant files, functions, tests, and checks when possible.

---

## 2026-06-12 - Post Synthetic Robustness Generated-Output Checkpoint

This documentation-only checkpoint records the state after PR #108 merged the
synthetic split-aware robustness Markdown report, JSON experiment log, and
refreshed experiment registry.

The checkpoint preserves the reviewed sequence from plan, deterministic
all-case implementation, opt-in report/log support, PR-gate governance, and
committed generated artifacts. It also records remaining gaps before any
local-fixture robustness refresh or user-provided local CSV interpretation:
the all-case split summary format has not yet been mapped to committed local
fixtures, no real-data IC/Rank IC or benchmark-relative study exists, and
readiness/provenance gates still block user-data interpretation.

Validation before this checkpoint branch:

- `python -m pytest -q` passed with 501 tests after syncing `main` at PR #108.
- `python -m compileall src tests research` passed after syncing `main` at
  PR #108.

Checkpoint branch validation:

- Markdown fence checks passed for the checkpoint and updated workflow docs.
- Guardrail text checks confirmed no-real-data, no-vendor-API,
  no-live-trading, no-order-execution, and no-profitability boundaries.
- Scope review found no `src/`, `tests/`, `research/`, `reports/`, or `lean/`
  changes.
- `python -m pytest -q` passed with 501 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` ran.
- `git diff --check` passed before commit.

This stage is documentation-only. It does not modify source code, tests,
research scripts, generated reports/logs, data loaders, backtester behavior,
metrics behavior, factor logic, diagnostics helpers, LEAN code, real-data
access, vendor APIs, credentials, live/paper trading, brokerage/order logic,
or profitability language.

---

## 2026-06-12 - Synthetic Robustness Generated Output Refresh

This generated-output stage commits the default Markdown report, JSON
experiment log, and refreshed experiment registry for the synthetic
split-aware robustness demo after the report/log support path was reviewed and
merged.

The refresh calls the explicit `write_outputs=True` path for
`research.synthetic_split_robustness_demo` and then regenerates the synthetic
experiment registry from committed JSON logs. The committed report preserves
the all-case split summary, invalid/insufficient-case table, synthetic-only
caveats, no-real-data/no-trading guardrails, and separately inspectable
cost/slippage assumptions. The JSON log records three configured cases, nine
all-case rows, three invalid-case rows, empty metrics, and
`volume_aware_slippage_mode` as `absent`.

Validation:

- `python -m pytest tests/test_synthetic_split_robustness_demo.py -q` passed
  with 13 tests.
- Direct JSON/report content checks confirmed the expected experiment id,
  experiment type, reported/invalid case counts, nine all-case rows, three
  invalid-case rows, empty metrics, `volume_aware_slippage_mode=absent`, and
  required caveat strings.
- `python -m pytest -q` passed with 501 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` ran.
- `.\scripts\audit-skills.ps1` passed.
- `git diff --check origin/main..HEAD` passed.

This stage does not modify source code, tests, research scripts, data loaders,
backtester behavior, metrics behavior, factor logic, diagnostics helpers, LEAN
code, real-data access, vendor APIs, credentials, live/paper trading,
brokerage/order logic, or profitability language.

---

## 2026-06-12 - PR Gate Pause Rule Refresh

This workflow-control stage updates the project PR-gate rules so future
continuations pause after one current-state check when a previous-stage PR is
not verified merged.

The rule prevents repeated PR polling, protection checks, review checks,
auto-merge reclassification, baseline validation, or next-stage startup while
the same PR gate remains open, closed-unmerged, unknown, or otherwise unproven
merged. A merged PR still requires the normal `main` fast-forward and baseline
validation before any next stage begins.

This stage changes only workflow documentation and the project staged workflow
Skill. It does not modify source code, tests, research scripts, generated
reports/logs, data access, strategy logic, backtester behavior, metrics, real
data fetching, vendor APIs, credentials, live/paper trading, brokerage/order
logic, or profitability language.

---

## 2026-06-12 - Synthetic Robustness Report/Log Support

This implementation stage adds opt-in Markdown report and JSON experiment-log
support to `research/synthetic_split_robustness_demo.py` after PR #105 added
the deterministic all-case summary.

The report/log support keeps output writing explicit through `write_outputs`.
Default module execution still runs the synthetic demo without creating
committed generated artifacts. The Markdown report includes input artifacts,
split windows, parameter grid, all-case split summary, invalid/insufficient
cases, benchmark/cost/slippage assumptions, and guardrails. The JSON log uses
the existing deterministic experiment-log helper and records empty metrics,
all-case diagnostics, invalid-case diagnostics, caveats, and separately
inspectable cost, fixed-slippage, and volume-aware-slippage assumptions.

Validation:

- `python -m pytest tests/test_synthetic_split_robustness_demo.py -q` passed
  with 13 tests after updating one wording assertion to match the revised
  opt-in output caveat.
- `python -m research.synthetic_split_robustness_demo` passed without creating
  default report/log files.
- `python -m pytest -q` passed with 501 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` ran and produced no `docs/repo_map.md` diff.
- `git diff --check` passed.
- `.\scripts\audit-skills.ps1` passed.

This stage does not refresh committed generated reports/logs, modify source
package modules, change CSV loader behavior, change factor formulas, change
existing diagnostics helpers, change backtester behavior, change metrics
logic, access private data, fetch real data, add vendor APIs, add credentials,
add live or paper trading scope, add brokerage integration, add order
execution, change LEAN runtime behavior, calibrate market impact, or add
profitability language.

---

## 2026-06-12 - Synthetic Split-Aware Robustness Demo

This implementation stage adds `research/synthetic_split_robustness_demo.py`
and focused tests after the reviewed synthetic robustness validation plan.

The demo reuses the existing deterministic split-aware synthetic factor and
forward-return panels, then reports every configured signal case across train,
validation, and test windows. The default cases are an identity signal, inverse
signal, and constant invalid signal. The summary is sorted by stable case and
split order, includes every case/split row, preserves missing values, records
invalid reasons for undefined IC/Rank IC diagnostics, and keeps assumptions for
benchmark, costs, fixed-bps slippage, volume-aware slippage, portfolio
construction, and backtest integration separately inspectable.

Assumption: this PR deliberately avoids generated report/log changes so the
review can focus on deterministic all-case implementation and tests. A later
stage can add report/log output or committed generated artifacts if explicitly
scoped.

Validation:

- `python -m pytest tests/test_synthetic_split_robustness_demo.py -q` passed
  with 10 tests.
- `python -m research.synthetic_split_robustness_demo` passed without writing
  outputs.
- `python -m pytest -q` passed with 498 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` refreshed `docs/repo_map.md`.
- `git diff --check` passed.
- `.\scripts\audit-skills.ps1` passed.
- Guardrail grep found only prohibition, caveat, and test assertion wording.

This stage does not modify source package modules, generated reports/logs, CSV
loader behavior, factor formulas, existing diagnostics helpers, backtester
behavior, metrics logic, private data, real-data access, vendor APIs,
credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact calibration, or profitability
language.

---

## 2026-06-12 - Synthetic Robustness And Split-Aware Validation Plan

This documentation-only stage adds
`docs/synthetic_robustness_validation_plan.md` after the roadmap refresh
identified robustness and split-aware validation policy as the next blocker.

Assumption: after PR #103 merged and synced `main` passed baseline validation,
the next safe stage was a plan for robustness reporting, not implementation,
generated-output refresh, real-data interpretation, or LEAN/runtime work.

The plan defines required inputs, chronological split policy, all-case
robustness reporting behavior, missing-data and insufficient-window stop
conditions, future deterministic test coverage, future experiment-log fields,
and future Markdown report fields. It keeps fixed-bps transaction costs,
fixed-bps slippage, and volume-aware diagnostics or precomputed impacts
separately inspectable.

Validation:

- `python -m pytest -q` passed with 488 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` refreshed `docs/repo_map.md` for the new plan.
- `git diff --check` passed.
- `.\scripts\audit-skills.ps1` passed.
- Guardrail grep found only existing prohibition, caveat, and policy wording.

This stage does not modify source code, tests, research scripts, generated
reports/logs, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics logic, private data, real-data access, vendor
APIs, credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact calibration, or profitability
language.

---

## 2026-06-12 - Post-Volume-Aware Roadmap Gap Refresh

This documentation-only stage refreshes `docs/current_roadmap_gap_refresh.md`
after the split, liquidity, fixed-bps slippage, volume-aware diagnostic,
precomputed-impact, generated-log, and checkpoint stages.

Assumption: after PR #102 merged, no open PR gate remained, and synced `main`
passed baseline validation, the next safe stage was the checkpoint-recommended
roadmap refresh, not source code, tests, research-script changes,
generated-output changes, real-data workflows, or LEAN/runtime work.

The refreshed roadmap records the current implementation traceability,
remaining original-goal gaps, guardrail state, and recommended next roadmap.
The next recommended PR-sized stage is a documentation-only synthetic
robustness and split-aware validation plan before any implementation or
generated-output refresh.

Validation:

- `python -m pytest -q` passed with 488 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` ran and produced no `docs/repo_map.md` diff.
- `git diff --check` passed.
- `.\scripts\audit-skills.ps1` passed.

This stage does not modify source code, tests, research scripts, generated
reports/logs, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics logic, private data, real-data access, vendor
APIs, credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact calibration, or profitability
language.

---

## 2026-06-11 - Post Precomputed Volume-Aware Slippage Checkpoint

This documentation-only checkpoint records the completed PR #98 through
PR #101 sequence for volume-aware slippage backtester integration:
documentation-only design, documentation-only test plan, precomputed-impact
implementation, and synthetic generated-log refresh.

Assumption: after PR #101 merged and synced `main` passed baseline validation,
the next safe stage was the handoff-recommended checkpoint, not new code,
research-script changes, generated-output changes, real-data workflows, or
LEAN/runtime work.

`docs/post_precomputed_volume_aware_slippage_checkpoint.md` records the
baseline, completed implementation and generated-log state, guardrail review,
remaining gaps, and recommended next roadmap. The recommendation is a
documentation-only post-volume-aware roadmap gap refresh because
`docs/current_roadmap_gap_refresh.md` predates several completed split,
liquidity, fixed-bps slippage, volume-aware diagnostic, precomputed-impact, and
generated-log stages.

This stage does not modify source code, tests, research scripts, generated
reports/logs, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics logic, private data, real-data access, vendor
APIs, credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact calibration, or profitability
language.

Validation:

- `python -m pytest -q` passed with 488 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` refreshed `docs/repo_map.md` for the new
  checkpoint document.
- `git diff --check origin/main..HEAD` passed.
- `.\scripts\audit-skills.ps1` passed.

---

## 2026-06-11 - Synthetic Volume-Aware Slippage Generated-Log Refresh

This generated-output stage refreshes the committed synthetic experiment logs
after PR #100 added the default `total_volume_aware_slippage_cost_impact`
metric to the local backtester result metrics.

Assumption: after PR #100 merged and synced `main` passed baseline validation,
the next safe stage was the handoff-recommended generated-output review or
refresh for synthetic/local-fixture artifacts, not source code, tests, research
script behavior, real-data workflows, or LEAN/runtime work.

`python research\synthetic_momentum_demo.py` completed and refreshed the
synthetic momentum experiment log. Direct file invocation of
`research\synthetic_combined_score_backtest_demo.py` and
`research\synthetic_multifactor_parameter_sweep.py` failed with
`ModuleNotFoundError: No module named 'research'` because those scripts import
package-qualified `research.*` modules. Rerunning them as
`python -m research.synthetic_combined_score_backtest_demo` and
`python -m research.synthetic_multifactor_parameter_sweep` completed
successfully. No source or research-script changes were needed.

Only these committed synthetic JSON experiment logs changed:

- `reports/experiment_logs/synthetic_momentum_demo.json`
- `reports/experiment_logs/synthetic_combined_score_backtest_demo.json`

Both now include `total_volume_aware_slippage_cost_impact: 0.0` in the metrics
payload. The synthetic parameter sweep produced no committed diff, and no
Markdown report or experiment-registry file changed.

This stage does not modify source code, tests, research scripts, CSV loader
behavior, factor formulas, diagnostics semantics, backtester behavior, metrics
logic, private data, real-data access, vendor APIs, credentials, live or paper
trading scope, brokerage integration, order execution, LEAN runtime behavior,
market-impact calibration, or profitability language.

Validation:

- `python -m pytest -q` passed with 488 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` ran and produced no `docs/repo_map.md` diff.
- `git diff --check origin/main..HEAD` passed.
- `.\scripts\audit-skills.ps1` passed.

---

## 2026-06-11 - Precomputed Volume-Aware Slippage Backtester Integration

This code-changing stage implements the reviewed precomputed-impact boundary
for volume-aware slippage without moving OHLCV or rolling dollar-volume
calculation into the backtester.

Assumption: after PR #99 merged and synced `main` passed baseline validation,
the next safe stage was the narrow implementation described by
`docs/volume_aware_slippage_backtester_integration_test_plan.md`, with
deterministic tests in the same PR and no generated-output refresh.

`run_long_only_backtest()` now keeps `volume_aware_slippage_mode` at
`diagnostic_only` by default. A caller may explicitly use
`apply_precomputed_impact` with an aligned precomputed impact series and
required audit metadata. Applied impact is recorded in a separate
`volume_aware_slippage_costs` series, included in total trading impact, and
reported through a separate metric while fixed transaction costs and fixed-bps
slippage remain separately inspectable.

The implementation rejects invalid impact indexes, missing or negative impact
values, missing required metadata, invalid modes, and positive fixed-bps
slippage combined with positive applied volume-aware impact. Tests also cover
the integration path where `calculate_volume_aware_slippage_diagnostics()`
feeds the precomputed boundary from outside the backtester.

This stage does not modify data loaders, feature logic, diagnostics helper
behavior, research scripts, generated reports, real-data access, vendor APIs,
credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact calibration, or profitability
language.

---

## 2026-06-11 - Volume-Aware Slippage Backtester Integration Test Plan

This documentation-only stage defines the test coverage required before any
future implementation applies volume-aware slippage to simulated local
backtester returns.

Assumption: after PR #98 merged and `main` was synced, the next safe stage is a
test plan, not source code changes, test file changes, research script changes,
generated report changes, backtester integration, or metrics changes.

`docs/volume_aware_slippage_backtester_integration_test_plan.md` records the
required unit tests, integration tests, failure-mode tests, edge-case expected
behavior, zero-slippage diagnostic behavior, separate inspection requirements,
future result/audit fields, experiment-log/report fields, guardrail tests,
stop conditions, and the recommended next PR-sized stage.

The plan keeps helper calculation outside the backtester for the first future
implementation, keeps `diagnostic_only` as default, and requires deterministic
tests in the same PR as any later precomputed-impact implementation.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, vendor APIs,
credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact modeling, or profitability
language.

---

## 2026-06-11 - Volume-Aware Slippage Backtester Integration Design

This documentation-only stage defines whether and how the existing
volume-aware slippage diagnostic helper could later affect simulated local
backtester net returns.

Assumption: after PR #97 merged and `main` was synced, the next safe stage is a
design boundary, not source code changes, test changes, research script
changes, generated report changes, or backtester integration.

`docs/volume_aware_slippage_backtester_integration_design.md` records the
problem statement, diagnostic-only rationale, required inputs, recommended
future precomputed-impact integration shape, return/cost/audit semantics,
strict defaults and stop conditions, required tests, experiment-log/report
fields, non-goals, and the recommended next PR-sized stage.

The design recommends keeping `diagnostic_only` as the default and deferring
any `run_long_only_backtest()` integration until a separate test-plan stage is
reviewed. If implemented later, the first integration should pass a validated,
date-aligned `portfolio_slippage_impact` series and audit metadata into the
backtester or wrapper rather than making the backtester own OHLCV validation.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, vendor APIs,
credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact modeling, or profitability
language.

---

## 2026-06-11 - Post Local Fixture Slippage Output Refresh Checkpoint

This documentation-only checkpoint records the repository state after PR #94
refreshed the synthetic local CSV fixture generated outputs and PRs #95/#96
added and refined the context-budget retrieval policy.

Assumption: after syncing `main` to PR #96, verifying no open PR gates, and
passing baseline validation, the next safe stage is a checkpoint before any
backtester net-return integration design. It is not source code changes, CSV
loader changes, research script changes, generated report changes,
user-provided local CSV interpretation, or LEAN/runtime work.

`docs/post_local_fixture_slippage_output_refresh_checkpoint.md` records the
reviewed baseline, completed volume-aware slippage design/helper/smoke/output
refresh sequence, diagnostic-only boundary, remaining gaps, guardrail review,
and recommended next roadmap. The recommendation is a documentation-only
volume-aware slippage backtester integration design after this checkpoint is
reviewed and merged.

`docs/current_handoff.md` now routes future continuations through this
checkpoint PR, and `docs/repo_map.md` is refreshed because a docs file was
added.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, vendor APIs,
credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact modeling, or profitability
language.

---

## 2026-06-11 - Context Budget Policy For Staged Workflow

This workflow-control update adds a context-budget and retrieval policy to the
long-running controller and staged workflow Skill after a continuation
encountered tool-output truncation while reading too much context at once.

The policy limits first-pass context to the handoff, repo map, governing agent
rules, project spec, controller, and staged workflow Skill; defines a
retrieval ladder from git/PR state through targeted log searches; discourages
parallel broad reads of long logs, reports, experiment JSON, and checkpoint
documents; and requires targeted rereads after truncation.

Follow-up refinement: the short-entry files are now explicitly maintained as
retrieval controls. `docs/current_handoff.md` should stay around 100-200 lines,
`docs/repo_map.md` should remain an index rather than history, and long logs
plus `CHANGELOG.md` should be accessed by tail, keyword search, stats, or small
line ranges by default.

This stage changes workflow documentation and logs only. It does not modify
source code, tests, research scripts, generated reports, CSV loader behavior,
backtester behavior, metrics, alpha files, normalization, combination,
diagnostics, `PROJECT_SPEC.md`, real-data access, vendor APIs, credentials,
trading scope, order execution, or profitability language.

---

## 2026-06-10 - Local Fixture Slippage Generated-Output Refresh

This generated-output refresh syncs the committed synthetic local CSV fixture
report, JSON experiment log, and experiment registry after PR #92 added the
volume-aware slippage smoke diagnostic and PR #93 recorded the checkpoint.

Assumption: after PR #93 merged and no open PR gate remained, the next safe
stage was the checkpoint-recommended generated-output refresh, not source code
changes, backtester net-return integration, user-provided local CSV
interpretation, or LEAN/runtime work.

`python research/local_csv_fixture_workflow_demo.py` was run from the project
root. It uses committed synthetic fixtures under
`tests/fixtures/local_csv_loader_smoke` and updates:

- `reports/local_csv_fixture_workflow_demo.md`
- `reports/experiment_logs/local_csv_fixture_workflow_demo.json`
- `reports/experiment_registry.md`

The refreshed artifacts now include the volume-aware slippage smoke diagnostic
assumptions, participation and rejected/cap counts, and caveats that the
diagnostic is not applied to returns and is not a trading-cost conclusion.

This stage does not modify source code, tests, research scripts, CSV loader
behavior, factor formulas, diagnostics semantics, backtester behavior, metrics,
private data, real-data access, vendor APIs, credentials, live or paper trading
scope, brokerage integration, order execution, LEAN runtime behavior,
market-impact modeling, or profitability language.

Validation before PR creation:

- `python -m pytest -q` - 478 passed before the refresh branch.
- `python -m compileall src tests research` - passed before the refresh branch.
- Full final validation is recorded in the PR summary after the final gate.

---

## 2026-06-09 - Post Volume-Aware Slippage Smoke Checkpoint

This documentation-only checkpoint records the repository state after PR #92
merged the committed synthetic local CSV fixture smoke diagnostic for
volume-aware slippage.

Assumption: after syncing `main` to PR #92 and verifying no open PR gates,
the next safe stage is a checkpoint, not generated-output refresh,
backtester net-return integration, user-provided local CSV interpretation,
or LEAN/runtime work. The checkpoint should make the next step explicit before
any committed reports/logs are regenerated.

`docs/post_volume_aware_slippage_smoke_checkpoint.md` now records the reviewed
baseline, completed design/helper/smoke sequence, diagnostic-only boundary,
remaining gaps, guardrail review, and recommended next roadmap. The
recommendation is a narrow synthetic local CSV fixture generated-output
refresh so committed report/log artifacts reflect the new smoke diagnostic.

`docs/decision_log.md` records the durable decision to refresh local fixture
generated outputs before considering any backtester slippage integration.
`docs/current_handoff.md` is updated so future continuations pause at this
checkpoint PR and, after merge, route to the generated-output refresh stage.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, vendor APIs,
credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact modeling, or profitability
language.

Validation before PR creation:

- `python -m pytest -q` - 478 passed.
- `python -m compileall src tests research` - passed.
- Full final validation is recorded in the PR summary after the final gate.

---

## 2026-06-09 - Local Fixture Volume-Aware Slippage Smoke Diagnostic

This code milestone wires the reviewed volume-aware slippage diagnostic helper
into the committed synthetic local CSV fixture workflow as a smoke diagnostic
only.

Assumption: after PR #91 merged and no open PR gate remained, the next safe
stage was the handoff-recommended synthetic/local-fixture smoke diagnostic
that reports participation and rejected/cap counts only. It should not
integrate volume-aware slippage into backtester net returns, generated
performance interpretation, real-data workflows, LEAN runtime behavior, or
trading/execution code.

`research/local_csv_fixture_workflow_demo.py` now builds a tiny deterministic
two-date target-weight panel from complete synthetic OHLCV fixture rows, calls
`calculate_volume_aware_slippage_diagnostics()`, and stores a reduced smoke
summary containing trade count, trade weight/notional, max participation,
missing/zero/zero-window rejection counts, total rejected-capacity count, and
participation-cap breach count. The workflow intentionally does not report or
apply candidate slippage impact to returns.

`tests/test_local_csv_fixture_workflow_demo.py` now verifies the fixed target
weights, date/asset alignment, helper invocation, deterministic participation
summary, Markdown report caveats, JSON experiment-log diagnostics, and
invalid slippage-smoke config rejection.

This stage does not modify `src/backtest/portfolio.py`,
`src/backtest/metrics.py`, the CSV loader, alpha formulas, normalization,
combination, diagnostics helpers, generated reports, user data, real-data
access, vendor APIs, credentials, live or paper trading scope, brokerage
integration, order execution, or profitability language.

Validation before PR creation:

- `python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py` - 14
  passed.
- `python -m pytest -q tests/test_volume_aware_slippage.py` - 17 passed.
- Full validation recorded in the PR summary after the final gate.

Troubleshooting note: this stage also recorded an output-truncation and patch
context recovery chain in `docs/troubleshooting_log.md`. The final
implementation used capped reads and smaller patches.

---

## 2026-06-09 - Volume-Aware Slippage Diagnostic Helper

This code milestone adds a standalone synthetic-only diagnostic helper for
volume-aware slippage assumptions after PR #90's design gate merged.

Assumption: the next safe stage is a narrow helper and deterministic tests, not
backtester net-return integration, generated-output refresh, local CSV
interpretation, or LEAN/runtime work. The helper should make notional,
liquidity lag, participation, missing-data, zero-volume, and cap assumptions
explicit before any later stage decides whether those diagnostics should
affect simulated returns.

`src/backtest/slippage.py` now exposes
`calculate_volume_aware_slippage_diagnostics()` and
`VolumeAwareSlippageDiagnostics`. The helper calculates target-weight trade
changes, lagged rolling dollar volume, trade notional, participation,
candidate asset-level slippage basis points, asset-level slippage impact, and
portfolio-level slippage impact. It requires explicit `portfolio_notional`,
uses rolling dollar volume shifted by `volume_lag`, and raises by default for
missing capacity, non-positive capacity, incomplete or zero-volume windows,
participation above cap, invalid target weights, and invalid parameters.

`tests/test_volume_aware_slippage.py` adds hand-calculated deterministic
coverage for the diagnostic calculation, lagged capacity rather than same-day
volume, required notional, warm-up capacity failures, missing price/volume,
zero-volume windows, zero lagged dollar volume, participation caps, panel
alignment, target-weight validation, invalid parameters, and forbidden import
guardrails.

This stage does not modify `src/backtest/portfolio.py`,
`src/backtest/metrics.py`, research scripts, generated reports, CSV loader
behavior, factor formulas, diagnostics semantics, private data, real-data
access, execution behavior, live or paper trading scope, brokerage
integration, order execution, LEAN runtime behavior, market-impact modeling,
or profitability language.

Validation:

- `python -m pytest -q tests/test_volume_aware_slippage.py` - 17 passed.
- `python -m pytest -q` - 478 passed.
- `python -m compileall src tests research` - passed.
- `python scripts/repo_map.py` - wrote `docs/repo_map.md`.
- `git diff --check` - passed with only Windows LF/CRLF notices.

Warning recovery:

- Original implementation used `.fillna(False)` on the shifted
  `positive_volume_window` boolean mask.
- Consequence: focused tests passed, but pandas emitted a `FutureWarning`
  about silent downcasting on `.fillna`, which could become brittle in a
  future pandas release.
- Evidence: `python -m pytest -q tests/test_volume_aware_slippage.py` reported
  17 passed with warnings from `src/backtest/slippage.py`.
- Investigation: the shifted rolling-window mask can carry missing values and
  object dtype after lagging. The helper only needs to treat literal `True` as
  valid capacity.
- Final fix: replace `.fillna(False)` with `.eq(True)`, avoiding silent
  downcasting while keeping missing values ineligible.
- Verification: focused helper tests were rerun and passed without warnings;
  full pytest also passed with 478 tests.
- Prevention: prefer explicit boolean comparisons for lagged nullable masks
  instead of relying on pandas fill/downcast behavior.

---

## 2026-06-09 - Volume-Aware Slippage Design Gate

This documentation-only design stage defines the boundary for any future
volume-aware slippage work after the fixed-bps slippage sequence and
token-efficient workflow controls merged.

Assumption: after PR #89 merged and the open-PR gate was clear, the current
handoff and checkpoint documents still identify volume-aware slippage design
as the next safe repository-internal stage. The correct next step is not a
helper implementation, generated-output refresh, local CSV interpretation, or
LEAN/runtime integration.

`docs/volume_aware_slippage_design.md` now records the required future input
contract, lagged liquidity-reference policy, candidate participation and
slippage-impact semantics, portfolio-notional requirement, zero/missing/stale
volume policy, participation-cap policy, adjustment-policy constraints,
future reporting fields, required tests, module alignment, and risks.

`docs/decision_log.md` records the durable decision that volume-aware slippage
requires explicit lagged dollar-volume, notional, missing-data, cap, and
adjustment-policy semantics before code. `docs/current_handoff.md` is updated
so the next continuation starts from the current post-PR #89 state.
`CHANGELOG.md` records the user-visible design document addition.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
behavior, live or paper trading scope, brokerage integration, order execution,
LEAN runtime behavior, market-impact modeling, or profitability language.

Validation:

- `python -m pytest -q` - 461 passed.
- `python -m compileall src tests research` - passed.
- `python -m compileall lean` - passed.
- `.\scripts\audit-skills.ps1` - passed for 2 Skill files.
- `python scripts/repo_map.py` - wrote `docs/repo_map.md`.
- `git diff --check` - passed with only Windows LF/CRLF notices.

---

## 2026-06-09 - Token-Efficient Codex Workflow Controls

This documentation and workflow-tooling milestone adds a short durable handoff
and capped-output rules so future staged Codex runs can spend less context on
stable repository state while preserving review quality.

Assumption: after PR #88 merged, the next safe stage is workflow-control only.
The current open-PR gate was clear at branch creation, and no research source,
tests, research scripts, generated reports, CSV loader, backtester, metrics,
alpha files, normalization, combination, diagnostics, LEAN code, real-data
access, broker/order behavior, credentials, or `PROJECT_SPEC.md` changes are
needed to improve Codex context discipline.

`docs/current_handoff.md` now provides the first-read project state summary.
`scripts/repo_map.py` reads repository paths and writes only
`docs/repo_map.md`, skipping cache/build directories, generated reports, and
large artifacts by default. `AGENTS.md`, the long-running controller, and the
staged workflow Skill now require handoff-first startup, capped output for
unknown large commands, targeted inspection of temp-file captures when full
output is needed, and no full generated-report or large-log printing by
default.

Validation before commit:

- `python -m pytest -q` - 461 passed.
- `python -m compileall src tests research` - passed.
- `.\scripts\audit-skills.ps1` - passed for 2 Skill files.
- `python scripts/repo_map.py` - wrote `docs/repo_map.md`.
- `git diff --check` - passed before commit.

Workflow recovery:

- Original assumption: the GitHub connector could create the PR after the
  branch was pushed.
- Consequence: PR creation stopped on the connector path.
- Evidence: the connector returned `403 Resource not accessible by
  integration`.
- Investigation: `gh repo view` confirmed the canonical repository is
  `minqiyang/equity-factor-research` with base branch `main`, and the branch
  had already pushed successfully.
- Correction attempt and final fix: used the documented GitHub CLI fallback
  with a temp Markdown body file, and `gh pr create` opened ready-for-review
  PR #89.
- Verification: the PR URL was returned by `gh`; future runs should continue
  to fall back to `gh pr create` when the connector returns this 403.

---

## 2026-06-09 - Post Slippage And Cost Checkpoint

This documentation checkpoint records the repository state after the fixed-bps
slippage design, implementation, and synthetic report/log refresh merged.

Assumption: after PR #87 merged, the previous checkpoint's recommended
slippage/cost sequence is complete. The safest next stage is not a direct
volume-aware implementation and not a user-provided local CSV run. The safe
repository-internal stage is a checkpoint that marks fixed-bps slippage as
reflected in code and generated synthetic outputs, then routes any broader
slippage work through a new design gate.

`docs/post_slippage_cost_checkpoint.md` now records the current review
baseline, completed slippage/cost state, remaining original-goal gaps,
guardrail review, and recommended next roadmap. It recommends a
documentation-only volume-aware slippage design before any helper,
backtester-extension, generated-output, or local CSV interpretation stage.

`docs/decision_log.md` records the durable decision to require a
volume-aware slippage design before implementation. `CHANGELOG.md` records the
user-visible checkpoint addition.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
assumptions, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, volume-aware slippage implementation,
market-impact modeling, or profitability language.

Validation:

- `python -m pytest -q` - 461 passed.
- `python -m compileall src tests research` - passed.
- `git diff --check` - passed with only Windows LF/CRLF notices.

---

## 2026-06-09 - Synthetic Backtest Slippage Report/Log Refresh

This generated-output milestone refreshes the synthetic backtest demos after
the fixed-bps slippage backtester extension merged.

Assumption: after `run_long_only_backtest()` began exposing separate
transaction cost, slippage, and total trading impact fields, generated
synthetic backtest reports and JSON logs should no longer say slippage is "not
separately modeled." The safest next stage is to update synthetic outputs only,
preserving the existing default `slippage_bps=0.0` as an explicit diagnostic
simplification rather than changing synthetic return paths.

Updated synthetic backtest generators now carry `slippage_bps` in their config,
pass it into the local backtester, record the fixed-bps cost and slippage model
names, record `zero_cost_or_slippage_is_diagnostic`, and include total
slippage cost impact and total trading cost impact in reports/logs. The
experiment registry was regenerated from the updated JSON logs so the registry
shows current fixed-bps cost/slippage assumptions.

`docs/simulated_slippage_cost_assumption_design.md` and
`docs/quantconnect_lean_plan.md` were narrowly refreshed so current roadmap and
planning documents no longer say local slippage is unimplemented. The LEAN plan
still distinguishes local target-weight turnover friction from LEAN
order/fill-level fee and slippage models.

This stage does not change backtester logic, factor formulas, CSV loaders,
local user-data handling, generated private data, real-data access, live or
paper trading scope, brokerage integration, order execution, LEAN runtime
behavior, volume-aware slippage, market-impact modeling, or profitability
language.

Validation:

- `python -m pytest -q tests/test_synthetic_momentum_demo.py tests/test_synthetic_combined_score_backtest_demo.py tests/test_synthetic_multifactor_parameter_sweep.py tests/test_experiment_registry.py` - 27 passed.
- `python -m pytest -q` - 461 passed.
- `python -m compileall src tests research` - passed.
- `git diff --check` - passed with only Windows LF/CRLF notices.

---

## 2026-06-09 - Fixed-Bps Slippage Backtester Extension

This code milestone implements the narrow fixed-basis-point slippage extension
designed in `docs/simulated_slippage_cost_assumption_design.md`.

Assumption: after the slippage and cost assumption design merged, the next safe
code stage is the first fixed-bps implementation only. The implementation
should preserve the existing target-weight turnover model, keep transaction
cost and slippage as separate impact series, keep total trading impact
inspectable, and avoid volume-aware slippage, market impact, generated report
updates, real data, broker fills, order execution, or performance
interpretation.

`run_long_only_backtest()` now accepts `slippage_bps` with default `0.0`.
Slippage impact is calculated as target-weight turnover times
`slippage_bps / 10000`, separately from `transaction_cost_bps`, and both are
deducted from simulated net returns. `BacktestResult` now exposes
`slippage_costs` and `total_trading_costs` in addition to the existing
`transaction_costs`. Backtest assumptions now record the cost model, slippage
model, `slippage_bps`, and whether a zero cost or zero slippage setting is a
diagnostic simplification.

`calculate_basic_metrics()` now records total transaction cost impact, total
slippage cost impact, and total trading cost impact when the relevant series
are supplied. Focused tests cover separate transaction cost and slippage
deduction, zero-cost or zero-slippage diagnostic labeling, first-row slippage
impact with `signal_lag_periods=0`, positive combined impact, and validation
that negative `slippage_bps` raises.

This stage does not modify research scripts, generated reports, CSV loader
behavior, factor formulas, diagnostics semantics, private data, real-data
access, live or paper trading scope, brokerage integration, order execution,
LEAN runtime behavior, volume-aware slippage, market-impact modeling, or
profitability language.

Validation:

- `python -m pytest -q tests/test_backtest_portfolio.py` - 17 passed.
- `python -m pytest -q` - 461 passed.
- `python -m compileall src tests research` - passed.
- `git diff --check` - passed with only Windows LF/CRLF notices.

---

## 2026-06-09 - Simulated Slippage And Cost Assumption Design

This documentation milestone defines the reviewed boundary for future local
backtester cost and slippage expansion.

Assumption: after the post-local-CSV-fixture audit rehearsal checkpoint merged,
the safest repository-internal next stage is not a code change. The current
backtester has deterministic target-weight turnover costs through
`transaction_cost_bps`, but it does not separately represent slippage or market
impact. A design gate keeps transaction cost, slippage, zero-slippage
diagnostics, market-impact caveats, experiment-log fields, and future tests
reviewable before source code changes.

`docs/simulated_slippage_cost_assumption_design.md` now records current
backtester semantics, non-goals, definitions, design principles, a proposed
fixed-basis-point slippage boundary, deferred volume-aware slippage and market
impact scope, future experiment-log fields, required tests, module alignment,
risks, and recommended next stages.

`docs/decision_log.md` records the durable decision to require this design
before cost/slippage implementation. `CHANGELOG.md` records the user-visible
documentation addition.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
assumptions, live or paper trading scope, brokerage integration, order
execution, or profitability language.

Validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Post Local CSV Fixture Audit Rehearsal Checkpoint

This documentation milestone records the repository state after the committed
synthetic local CSV fixture readiness audit rehearsal merged.

Assumption: no user-provided local CSV bundle, completed user-data checklist,
completed inventory review, completed readiness audit report, or prepared
user-data `EXPERIMENT_LOG.md` entry is available in the current repository
context. The next safe stage is therefore not a real local CSV smoke run. The
safe repository-internal stage is a checkpoint that closes the local CSV
readiness-artifact sequence for now and selects the next non-user-data
roadmap item.

`docs/post_local_csv_fixture_audit_rehearsal_checkpoint.md` now records the
post-PR #83 review baseline, completed local CSV readiness artifacts, remaining
user-data gates, original-goal gaps, guardrail review, and recommended next
stage. It recommends a documentation-only simulated slippage and cost
assumption design before any backtester cost/slippage code changes.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
assumptions, live or paper trading scope, brokerage integration, order
execution, or profitability language.

Validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Local CSV Fixture Readiness Audit Rehearsal

This documentation milestone fills the manual local CSV readiness audit report
format using the already-committed synthetic local CSV fixture workflow.

Assumption: after the post-readiness-gates checkpoint merged, no user-provided
local CSV bundle, completed user-data checklist, or completed user-data audit
is available. The next safe repository-internal stage is therefore not a real
local CSV smoke run. A synthetic-only audit rehearsal can still move the
project forward by proving that the new audit report format can represent
known fixture evidence, issue levels, limitations, and gate decisions without
crossing into user-data interpretation.

`docs/local_csv_fixture_readiness_audit_rehearsal.md` now records the audit
identity, fixture input inventory, schema and loader evidence, provenance and
adjustment policy, universe and benchmark review, date-alignment review,
sample split and execution assumptions, low issue register, gate decision, and
experiment-log handoff for the committed synthetic fixture workflow.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
assumptions, live or paper trading scope, brokerage integration, order
execution, or profitability language.

Validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Post Local CSV Readiness Gates Checkpoint

This documentation milestone records the repository state after the local CSV
study checklist, metadata-only inventory dry-run validator, committed synthetic
fixture rehearsal, and manual readiness audit report template merged.

Assumption: after PR #81 merged, the next safe stage is not an actual
user-provided local CSV smoke run because no user-supplied local CSV bundle,
completed scope statement, completed checklist, completed readiness audit
report, or local CSV `EXPERIMENT_LOG.md` entry exists in the repository
context. The safest PR-sized stage is a checkpoint that distinguishes
"readiness gates are available" from "a user-provided dataset is ready for
interpretation."

`docs/post_local_csv_readiness_gates_checkpoint.md` now records the current
review baseline, completed local CSV readiness artifacts, readiness assessment,
remaining stop conditions, guardrail review, and recommended next stage under
two conditions: no user data available, or a future user-supplied local CSV
bundle available outside the repository.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
assumptions, live or paper trading scope, brokerage integration, order
execution, or profitability language.

Validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Local CSV Readiness Audit Report Template

This documentation milestone adds the next manual gate after the committed
synthetic fixture inventory rehearsal.

Assumption: the safest PR-sized next stage is still documentation-only. The
project already has a study checklist, metadata-only inventory dry-run
validator, and synthetic fixture rehearsal. The remaining stage named in the
user-provided local CSV plan is a manually fillable real-data readiness audit
report format that records evidence, high/medium/low issues, stop conditions,
and the final gate decision before any user-provided local CSV result is
interpreted.

`docs/local_csv_readiness_audit_report_template.md` now provides that report
format. It covers audit identity, redacted input inventory, schema and loader
validation evidence, provenance and adjustment policy, universe and benchmark
review, date alignment and timing, sample splits, parameter policy, costs,
slippage, issue register, gate decision, experiment-log handoff, and final stop
statements. The template explicitly states that local CSV diagnostics are not
profitability evidence and that unresolved high or medium issues stop
interpretation.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
assumptions, live or paper trading scope, brokerage integration, order
execution, or profitability language.

Validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Local CSV Fixture Inventory Dry-Run Rehearsal

This code-and-report milestone connects the local CSV inventory dry-run
validator to the committed synthetic fixture workflow.

Assumption: after the metadata-only inventory validator merged, the safest
PR-sized next stage is a synthetic fixture rehearsal of the user-provided
local CSV research plan. The rehearsal should prove that declared local CSV
inventory metadata can be reviewed and reported before loader output is
interpreted, while still avoiding user-provided files, downloads, vendor APIs,
credentials, trading behavior, and profitability language.

`research/local_csv_fixture_workflow_demo.py` now builds a metadata-only
inventory declaration for the committed synthetic adjusted-close, benchmark,
and OHLCV fixtures and runs `validate_local_csv_inventory()` before loading
those fixtures. The workflow result, Markdown report, and JSON sidecar log now
include redacted inventory review summaries and issue counts. The review
records metadata flags only; it does not store raw local paths in its result,
read files, check path existence, compute hashes, fetch data, or authorize
real-data interpretation.

`tests/test_local_csv_fixture_workflow_demo.py` now verifies the inventory
review has three declared inputs, no high/medium/low issues for the committed
synthetic fixture metadata, no raw-path field on review summaries, deterministic
review output, report/log inventory sections, helper reuse, and caveats.

The generated report and JSON experiment log were regenerated from committed
synthetic fixtures only. This stage does not modify CSV loader behavior, factor
formulas, diagnostics semantics, backtester behavior, metrics, private data,
real-data access, execution assumptions, live or paper trading scope,
brokerage integration, order execution, or profitability language.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
14 passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Local CSV Inventory Dry-Run Validator

This code milestone adds the next local CSV planning gate after the study
checklist template merged.

Assumption: the safest PR-sized next stage is a metadata-only dry-run
validator for a declared local CSV inventory. The helper should review the
declared file labels, schema labels, provenance fields, version/hash evidence,
known-manual-edit disclosure, remote path markers, and credential-like path
markers before any user file is loaded. It should not read files, check path
existence, compute file hashes, write reports, store raw paths in its review
result, fetch data, or interpret research output.

`src/data/local_csv_inventory.py` now exposes
`validate_local_csv_inventory()` plus redacted review, summary, and issue
dataclasses. The result deliberately stores per-input metadata flags rather
than raw local paths so later reports can cite inventory readiness without
leaking private filesystem details. High or medium issues keep the future
local CSV workflow stopped before loading or interpreting data.

`tests/test_local_csv_inventory.py` covers valid inventory metadata, raw-path
redaction, missing required fields, hash or hash-plan version evidence,
unknown schemas, remote paths, credential-like path markers, non-CSV path
warnings, redacted CSV placeholders, duplicate input names, invalid inventory
shape, and absence of file I/O, remote-data, vendor, broker, order, or live
trading imports.

This stage does not modify CSV loaders, factor helpers, diagnostics,
backtester behavior, metrics, research scripts, generated reports, strategy
logic, real data access, execution assumptions, live or paper trading scope,
brokerage integration, order execution, or profitability language.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_inventory.py
19 passed

python -m pytest -q
453 passed

python -m compileall src tests research
passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Local CSV Study Checklist Template

This documentation milestone adds the first concrete checklist template after
the user-provided local CSV research plan merged.

Assumption: the safest PR-sized next stage is still documentation-only. The
project should prepare a reusable pre-run checklist before any stage loads,
validates, diagnoses, reports, or interprets user-provided local CSV files.

`docs/local_csv_study_checklist.md` now provides a copyable checklist for
scope, file inventory, schema mapping, provenance, adjustment policy,
validation evidence, universe and benchmark assumptions, feature timing,
sample splits, costs, slippage, readiness-audit summary, experiment-log
preparation, and final stop conditions. It is designed to be completed before
any user file is loaded, and it explicitly keeps downloads, vendor APIs,
credentials, live or paper trading, brokerage integration, order execution,
silent missing-data repair, and profitability language out of scope.

This stage does not modify source code, tests, research scripts, generated
reports, strategy logic, data access, execution assumptions, live or paper
trading scope, brokerage integration, order execution, or profitability
language.

Validation at the time of this entry:

```text
python -m pytest -q
434 passed

python -m compileall src tests research
passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - User-Provided Local CSV Research Plan

This documentation milestone defines the Stage 77 plan for future
user-provided local CSV research without loading user files or interpreting
real-data results.

Assumption: after the local CSV readiness checkpoint merged, the safest
PR-sized next stage is a documentation-only planning artifact. The project has
strict local loaders, committed synthetic fixtures, factor diagnostics,
liquidity eligibility, universe masks, universe-masked signals, and synthetic
backtest smoke coverage, but it still needs a clear local-file study plan
before any user-provided CSV result can be interpreted.

`docs/user_provided_local_csv_research_plan.md` now defines the intended
future workflow gates, local input bundle, scope statement template,
validation requirements, research design requirements, interpretation levels,
stop conditions, and next PR-sized stages. It keeps user-provided local CSV
work gated by provenance, schema validation, adjustment policy, universe
documentation, benchmark compatibility, sample splits, cost/slippage
assumptions, experiment logging, and the real-data readiness audit.

This stage does not modify source code, tests, research scripts, generated
reports, strategy logic, data access, execution assumptions, live or paper
trading scope, brokerage integration, order execution, or profitability
language.

Validation at the time of this entry:

```text
python -m pytest -q
434 passed

python -m compileall src tests research
passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Local CSV Readiness Checkpoint

This documentation milestone records the local CSV readiness state after the
fixture workflow was updated with liquidity universe masks and
universe-masked signal audit counts.

Assumption: the safest PR-sized Stage 76 is a checkpoint before planning any
user-provided local CSV research. The project has enough synthetic and
committed-fixture infrastructure to define a future plan, but not enough
provenance, adjustment-policy, universe, benchmark, cost, slippage, or sample
split evidence to interpret real user-provided local CSV results.

`docs/local_csv_readiness_checkpoint.md` summarizes the current implemented
state, readiness assessment, guardrail review, stop conditions before
user-provided local CSV interpretation, and the recommended next stage:
documentation-only user-provided local CSV research planning.

This stage does not modify source code, tests, research scripts, generated
reports, strategy logic, data access, execution assumptions, live or paper
trading scope, brokerage integration, order execution, or profitability
language.

Validation at the time of this entry:

```text
python -m pytest -q
434 passed

python -m compileall src tests research
passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Synthetic Masked-Signal Backtest Smoke Test

This test milestone added the first synthetic smoke check that passes
universe-masked signals into the existing long-only backtester after the
synthetic masked-signal adapter smoke test merged.

Assumption: the safest PR-sized Stage 74 is a focused test-only backtest smoke
check, not a new research script, report, experiment log, backtester rewrite,
portfolio-construction change, parameter study, or real-data workflow.

`tests/test_liquidity_masked_signal_backtest_smoke.py` now builds
deterministic synthetic price, volume, and raw-signal panels, computes lagged
ADV and dollar-volume eligibility, constructs a liquidity universe mask,
applies that mask to raw signals, and passes the masked signal panel to
`run_long_only_backtest()`. The test verifies the exact masked signals,
resulting holdings, aligned signal coverage, transaction-cost impact, and the
existing `signal_lag_periods=1` timing. A second test confirms that a current
rebalance uses the prior masked-signal row, so a same-date universe/signal
change does not affect the current rebalance.

This stage does not modify source helpers, backtester behavior, metrics,
loaders, research scripts, generated reports, real-data handling, vendor
access, credentials, live or paper trading, brokerage integration, order
execution, strategy parameters, reusable report outputs, or profitability
claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_liquidity_masked_signal_backtest_smoke.py
2 passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Local CSV Fixture Universe-Masked Signal Smoke Check

This code-and-report milestone updated the committed synthetic local CSV
fixture workflow after the synthetic masked-signal backtest smoke PR merged.

Assumption: the safest PR-sized Stage 75 is not another backtest, not a
portfolio-construction change, not a real-data workflow, and not a parameter
study. It is a narrow local-fixture wiring check that applies the reviewed
liquidity universe mask to an already-computed `alpha_009` signal panel and
records the resulting masked-signal audit counts.

`research/local_csv_fixture_workflow_demo.py` now calls
`apply_universe_mask_to_signals()` after constructing the synthetic fixture
liquidity universe. The resulting `masked_alpha_009_signals` panel keeps the
original signal only where the universe mask is `True`, turns ineligible cells
into missing values rather than zero scores, preserves existing signal missing
values, and records per-date raw valid signal counts, eligible universe
counts, valid masked signal counts, excluded-by-universe counts, missing signal
counts, and low-coverage dates.

The generated fixture report and JSON sidecar log now include a
universe-masked `alpha_009` signal smoke-check section. The output is a
signal-panel wiring diagnostic only. It does not rank assets, create weights,
run a backtest, create trades, compare benchmark returns, fetch real data,
connect to a broker, support live or paper trading, or make profitability
claims.

`tests/test_local_csv_fixture_workflow_demo.py` now verifies the masked signal
alignment, deterministic output, exact fixture masked-signal values, report
section, JSON diagnostics, helper reuse, caveats, and configuration
validation.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
13 passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Synthetic Masked-Signal Smoke Test

This test milestone added the first synthetic smoke check after the
universe-masked signal adapter merged.

Assumption: the safest PR-sized Stage 73 is an integration-style test that
proves the reviewed liquidity eligibility helpers, liquidity universe
constructor, and `apply_universe_mask_to_signals()` adapter compose into the
masked signal panel a future backtest would consume. It is not yet a backtest
stage, research-script update, generated-report stage, parameter study, or
real-data workflow.

`tests/test_liquidity_masked_signal_smoke.py` now builds deterministic
synthetic price, volume, and raw-signal panels. The smoke test computes lagged
ADV and dollar-volume eligibility masks, constructs a liquidity universe mask,
applies that mask to raw signals, and checks the exact universe mask, masked
signals, and audit summary. Ineligible signals become `NaN`, not zero, and an
existing raw signal `NaN` remains visible in the summary. A second test changes
a future liquidity observation and confirms earlier masked-signal rows do not
change.

This stage does not modify source helpers, backtester behavior, metrics,
loaders, research scripts, generated reports, real-data handling, vendor
access, credentials, live or paper trading, brokerage integration, order
execution, target weights, portfolio construction, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_liquidity_masked_signal_smoke.py
2 passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Universe-Masked Signal Adapter

This code milestone implemented the first narrow helper from the liquidity
universe backtest-integration design after PR #71 merged.

Assumption: the safest PR-sized Stage 72 is a synthetic/local-panel signal
masking adapter only, not a backtest integration, ranking rule, target-weight
constructor, research-script update, generated report, or real-data workflow.

`src/features/liquidity.py` now exposes `UniverseMaskedSignalsResult` and
`apply_universe_mask_to_signals()`. The helper accepts an already-computed
numeric signal panel and an already-constructed boolean universe mask with
identical dates and assets. `True` mask cells preserve the original signal,
`False` mask cells become missing values rather than zero scores, and existing
signal missing values remain missing. The helper rejects mismatched indexes,
mismatched columns, non-boolean masks, duplicate labels, unsorted dates, and
missing universe-mask values by default. It does not reindex, forward-fill,
backward-fill, zero-fill, rank assets, create weights, run a backtest, write
reports, fetch data, or interpret performance.

Focused tests in `tests/test_liquidity.py` cover a hand-calculated masking
example, index and column preservation, ineligible signals becoming `NaN` and
not zero, preservation of existing signal `NaN` values, nullable boolean mask
acceptance, mismatched index rejection, mismatched column rejection,
unsorted and duplicate date rejection, duplicate-column rejection, non-boolean
mask rejection, missing mask rejection by default, and invalid parameter
rejection.

During the stage, a new duplicate-column test initially exposed a validation
order issue: duplicate signal columns reached the shared numeric panel
validator before the adapter's duplicate-column check, producing a pandas
`AttributeError` instead of the intended `ValueError`. The adapter now checks
duplicate signal columns before numeric validation. The full failure-to-fix
chain is recorded in `docs/troubleshooting_log.md`.

This stage remains synthetic/local-panel research infrastructure only. It does
not fetch real data, add vendor access, add credentials, modify loaders,
modify research scripts, generate reports, connect to a broker, place orders,
support live or paper trading, modify the backtester or metrics, tune
thresholds, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_liquidity.py
58 passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Liquidity Universe Backtest Integration Design

This documentation milestone defined the next reviewed boundary after the
synthetic liquidity universe helper and fixture universe-mask smoke check
merged.

Assumption: the next safest PR-sized stage is not source-code integration into
`run_long_only_backtest()`. It is a design gate that specifies how liquidity
universe masks, factor signals, rebalance schedules, costs, slippage,
benchmarks, and execution lag should interact before any backtest consumes a
universe mask.

`docs/liquidity_universe_backtest_integration_design.md` now defines the
purpose, current evidence, non-goals, proposed future signal-masking adapter,
strict signal/mask alignment contract, timing contract, selection and coverage
semantics, required future backtest assumptions, required future tests, and
suggested next stages.

`docs/liquidity_universe_construction_design.md` now marks the first three
recommended follow-up stages as complete and points the next step to the new
backtest-integration design. `docs/liquidity_dollar_volume_universe_plan.md`
also now reflects the completed universe-mask helper and fixture smoke stages.
`docs/decision_log.md` records the decision to require this design before code
consumes liquidity universe masks.

This stage does not modify source code, tests, research scripts, generated
reports, data loaders, backtester behavior, metrics, strategy logic, real-data
handling, vendor access, credentials, live or paper trading, brokerage
integration, order execution, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
417 passed

python -m compileall src tests research
passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Liquidity Universe Fixture Smoke Check

This stage connected the reviewed synthetic liquidity universe helper to the
committed local CSV fixture workflow as a count-only smoke check.

Assumption: after the standalone helper merged, the next safest PR-sized stage
was not backtest consumption, ranking/capping research, threshold tuning, or a
real-data workflow. It was a narrow fixture workflow update that proves the
existing ADV and dollar-volume eligibility masks can be combined into
`construct_liquidity_universe()` and reported as audit counts only.

`research/local_csv_fixture_workflow_demo.py` now constructs a
`synthetic_fixture_liquidity_universe` result from the intersection of the
lagged ADV and dollar-volume eligibility masks. The generated Markdown report
and JSON experiment log include universe-mask counts, low-coverage dates, and
caveats that keep the output separate from portfolio construction, backtest
universe integration, tradeability evidence, trading behavior, or performance
interpretation.

`tests/test_local_csv_fixture_workflow_demo.py` now verifies the universe mask
alignment, deterministic summary, low-coverage dates, JSON diagnostics,
Markdown report section, helper reuse, and invalid `min_assets_per_date`
configuration. The default synthetic report and experiment-log sidecar were
regenerated from the committed fixture only.

During implementation, the first full test run failed because the test suite
still expected the pre-helper caveat text `not universe construction` while
the workflow had intentionally changed to a universe-mask count diagnostic.
The full failure-to-fix chain is recorded in `docs/troubleshooting_log.md`.

This stage does not fetch real data, add vendor access, add credentials,
modify loaders, modify backtester or metrics, create target weights, place
orders, support live or paper trading, tune liquidity thresholds, or make
profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
13 passed

python -m pytest -q
417 passed

python -m compileall src tests research
passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Synthetic Liquidity Universe Helper

This code milestone implemented the first reviewed liquidity universe-mask
boundary after the documentation-only construction design merged.

Assumption: the next safest PR-sized stage after
`docs/liquidity_universe_construction_design.md` is a narrow synthetic/local
panel helper, not a research workflow update, backtest integration, report
generation, threshold-tuning step, or real-data study.

`src/features/liquidity.py` now exposes `LiquidityUniverseResult` and
`construct_liquidity_universe()`. The helper accepts an already-reviewed
boolean eligibility panel, records missing eligibility before treating it as
ineligible, optionally caps eligible assets by an aligned ranking metric with
stable input-column tie handling, and returns both the final boolean universe
mask and an inspectable per-date audit summary. The summary keeps raw eligible
counts, final universe counts, missing eligibility counts, missing ranking
counts, capped counts, additions, removals, and low-coverage flags visible.

Focused tests in `tests/test_liquidity.py` cover summary fields, missing
eligibility exclusion for object and nullable boolean panels, rejection of
non-boolean eligibility values, capped selection, missing ranking exclusion,
deterministic tie handling, mismatched ranking panels, no-lookahead behavior
for ranking values, parameter validation, and continued absence of data,
trading, or backtest imports.

During the stage, the first missing-eligibility implementation passed tests
but emitted a pandas `FutureWarning` because object boolean panels were cleaned
with `fillna(False).astype(bool)`. The conversion was replaced with
`eq(True).fillna(False).astype(bool)`, preserving explicit missing-value
exclusion for both object and nullable boolean panels while avoiding future
silent-downcasting behavior. The full warning-to-fix chain is recorded in
`docs/troubleshooting_log.md`.

This stage does not fetch real data, add vendor access, add credentials,
modify loaders, modify research scripts, generate reports, connect to a
broker, place orders, support live or paper trading, modify the backtester or
metrics, create portfolio weights, tune thresholds, or make profitability
claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_liquidity.py
44 passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Liquidity Universe Construction Design

This documentation milestone defined the next liquidity-related boundary after
the Alpha#012 LEAN planning refresh merged.

Assumption: after synthetic rolling ADV and rolling dollar-volume eligibility
helpers, local-fixture eligibility count smoke coverage, and Alpha#012
planning are complete, the next safest PR-sized stage is not code and not a
backtest. It is a design that specifies how a future universe mask and audit
summary should behave before any liquidity eligibility is consumed by
portfolio construction.

`docs/liquidity_universe_construction_design.md` now defines the purpose,
non-goals, timing definitions, proposed future API boundary, mask semantics,
audit-summary contract, module alignment, required future tests, risks, and
next stages for a synthetic-only liquidity universe construction helper.

`docs/liquidity_dollar_volume_universe_plan.md` now marks the eligibility
helper, local-fixture count smoke, and experiment-log field work as completed
for synthetic fixtures, then routes future work through the new universe-mask
design. `docs/decision_log.md` records the decision to keep liquidity
eligibility, universe-mask construction, and backtest consumption as separate
reviewed stages.

This stage does not modify source code, tests, research scripts, generated
reports, data access, backtester behavior, metrics, strategy logic, real-data
handling, vendor access, credentials, live or paper trading, brokerage
integration, order execution, runnable LEAN behavior, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
402 passed

python -m compileall src tests research
passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-07 - Alpha#012 QuantConnect/LEAN Plan Refresh

This documentation milestone refreshed the QuantConnect/LEAN planning path
after the post-Alpha#012 roadmap checkpoint merged.

Assumption: the next safest PR-sized stage after the Alpha#012 local feature,
fixture smoke, diagnostics, and checkpoint sequence is a planning refresh, not
runnable LEAN code. The local Alpha#012 feature changes the local-to-LEAN
signal mapping assumptions because it requires both completed close and volume
bars, an explicit close normalization policy, a reviewed volume policy, and
visible skip reasons for missing, stale, mismatched, or invalid inputs.

`docs/quantconnect_lean_plan.md` now records Alpha#012 as an implemented
local research feature and maps it to future LEAN planning requirements:
completed close and volume timing, close normalization, volume-source policy,
date matching, missing and stale data handling, negative-volume rejection,
zero-volume visibility, feature export, and diagnostic-only treatment.

`docs/lean_parity_checklist.md` now includes Alpha#012 parity assertions and
diagnostic coverage requirements. These checklist entries keep Alpha#012 out
of order logic, universe construction, portfolio construction, performance
interpretation, and strategy claims unless a later reviewed stage explicitly
changes that boundary.

This stage does not modify source code, tests, research scripts, generated
reports, data access, backtester behavior, metrics, strategy logic, real-data
handling, vendor access, credentials, live or paper trading, brokerage
integration, order execution, runnable LEAN behavior, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
402 passed

python -m compileall src tests research
passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-07 - Post-Alpha#012 Roadmap Checkpoint

This documentation checkpoint refreshed the staged roadmap after PR #65 merged
the Alpha#012 synthetic local-fixture diagnostics.

Assumption: after Alpha#012 implementation, synthetic OHLCV fixture smoke
coverage, and local-fixture diagnostics all merged, the next safest PR-sized
stage is not another formula or a backtest. It is a checkpoint that reconciles
the now-completed Alpha#012 sequence and chooses the next stage from current
evidence.

`docs/post_alpha012_checkpoint_report.md` now records the current
implementation state, completed Alpha#012 stages, remaining original-goal
gaps, guardrail status, and a recommended next roadmap.
`docs/volume_close_alpha_plan.md` now marks the synthetic fixture diagnostics
stage as complete and updates the recommended next stage.
`docs/worldquant_alpha_catalog.md` now reflects that Alpha#012 has fixture
smoke and diagnostics coverage, while keeping all remaining WorldQuant-style
formulas separate and PR-sized.

The checkpoint recommends a documentation-only QuantConnect/LEAN plan refresh
for Alpha#012 signal mapping as the next safe stage. That recommendation is
limited to planning: no runnable LEAN code, data subscriptions, credentials,
brokerage behavior, orders, portfolio construction, or performance
interpretation should be added.

This stage does not modify source code, tests, research scripts, generated
reports, data access, backtester behavior, metrics, strategy logic, real-data
handling, vendor access, credentials, live or paper trading, brokerage
integration, order execution, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
402 passed

python -m compileall src tests research
passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-07 - Alpha#012 Local Fixture Diagnostics

This workflow milestone extended the committed synthetic local CSV fixture
workflow after the Alpha#012 OHLCV fixture smoke check merged.

Assumption: the next smallest safe stage is a diagnostics-only workflow update
for `alpha_012()`, not a backtest, strategy rule, report interpretation,
additional formula, or real-data study. The existing local fixture workflow
already loads the committed synthetic OHLCV fixture, aligns adjusted close and
volume panels, computes forward-return evaluation targets, applies
train/validation/test split metadata, and runs IC, Rank IC, and quantile-spread
diagnostics for `alpha_009()`.

`research/local_csv_fixture_workflow_demo.py` now computes `alpha_012()` from
the aligned synthetic OHLCV `adjusted_close` and `volume` panels and evaluates
it with the same existing diagnostic helpers against already-aligned
forward-return targets. The generated Markdown report and JSON experiment log
record Alpha#012 diagnostic coverage separately from Alpha#009. The tiny
fixture produces two valid Alpha#012 observations on the validation date, one
valid IC date, one valid Rank IC date, and no valid Alpha#012 quantile-spread
dates because the configured three-quantile diagnostic requires more valid
assets than the fixture supplies.

During the stage, a new JSON-log test initially asserted exact equality for a
computed Rank IC value that serialized as `0.9999999999999999` instead of
`1.0`. The assertion was corrected to use approximate equality for the finite
computed float while preserving exact structural checks; the full
failure-to-fix chain is recorded in `docs/troubleshooting_log.md`.

This stage remains synthetic/local-fixture only. It does not fetch real data,
add vendor access, add credentials, connect to a broker, place orders, support
live or paper trading, modify feature formulas, modify loaders, modify the
backtester, create a portfolio, tune parameters, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
13 passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-07 - Alpha#012 Synthetic OHLCV Fixture Smoke Check

This test milestone added a narrow local-fixture smoke check after PR #63
merged `alpha_012()`.

Assumption: the next safest stage after the Alpha#012 implementation is not
diagnostics, report generation, backtesting, or another alpha formula. It is a
small wiring check from the existing strict OHLCV loader to the new feature
using the committed synthetic OHLCV fixture only.

`tests/test_local_csv_loader_smoke_demo.py` now loads
`tests/fixtures/local_csv_loader_smoke/synthetic_ohlcv.csv` with
`load_ohlcv_csv(require_adjusted_close=True)`, pivots `adjusted_close` and
`volume` into aligned date-asset panels, and computes `alpha_012(close,
volume)`. The test verifies the fixture dates and assets, the first-row `NaN`
delta behavior, and hand-calculated second-row outputs of `-0.75` for `AAA`
and `-0.50` for `BBB`.

This stage is feature-only smoke coverage. It does not modify source feature
logic, loaders, diagnostics, research scripts, reports, generated experiment
logs, backtester behavior, metrics, normalization, factor combination,
QuantConnect/LEAN artifacts, data access, vendor access, credentials, live or
paper trading, brokerage integration, order execution, or profitability
claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_loader_smoke_demo.py
7 passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-07 - Alpha#012 Volume + Close Research Feature

This code milestone implemented `alpha_012` as one reviewed volume + close
WorldQuant-style research feature after the planning gate in
`docs/volume_close_alpha_plan.md` merged.

Formula provenance: the public arXiv version of Zura Kakushadze's
`101 Formulaic Alphas` lists Alpha#012 as:

```text
sign(delta(volume, 1)) * (-1 * delta(close, 1))
```

`alpha_012()` maps that formula to caller-provided close and volume panels. It
requires exactly matching dates and asset columns, rejects negative volume,
does not fill missing close or volume values, preserves zero-volume behavior
explicitly, and returns `NaN` when either one-period delta endpoint is missing.
The feature at date `t` uses only `close[t]`, `volume[t]`, and their one-row
trailing anchors. Execution lag, ranking direction, universe selection,
portfolio construction, costs, slippage, backtesting, and interpretation
remain separate later-stage responsibilities.

Focused tests in `tests/test_worldquant_alphas.py` cover hand-calculated
formula output, shape preservation, no-lookahead behavior for both close and
volume, missing endpoints, zero-volume and zero-volume-delta behavior,
negative-volume rejection, panel alignment, invalid close and volume inputs,
and continued absence of backtest integration imports.

During the stage, the first hand-calculated test had an incorrect expected
sign for one row. The implementation matched the reviewed formula; the test
expectation was corrected and the full failure-to-fix chain is recorded in
`docs/troubleshooting_log.md`.

This stage does not fetch real data, add vendor access, add credentials,
connect to a broker, place orders, support live or paper trading, implement
bulk WorldQuant 101, modify loaders, modify the backtester, generate reports,
or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_worldquant_alphas.py
24 passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-06 - Volume + Close Alpha Planning Gate

This documentation milestone added `docs/volume_close_alpha_plan.md` before
any volume-dependent WorldQuant-style alpha implementation.

Assumption: after PR #61 merged the realized volatility feature, the older
`docs/original_goal_gap_analysis.md` recommendation for a synthetic IC /
Rank IC helper is stale because `factor_information_coefficient()` and
`factor_rank_information_coefficient()` already exist in
`src/features/diagnostics.py` and are covered by tests. The current
post-liquidity roadmap points to volume-dependent alpha planning as the next
small safe stage after reversal and realized volatility are settled.

The new plan keeps the next formula stage separate from data access, loader
changes, universe construction, portfolio construction, backtesting,
QuantConnect/LEAN runtime work, and interpretation. It records prerequisites,
non-goals, formula provenance requirements, close and volume policy questions,
date-alignment rules, missing and zero-volume behavior, required future tests,
research risks, and PR-sized next steps for a single future volume + close
alpha candidate such as `alpha_012`.

No source code, tests, research scripts, generated reports, data loaders,
backtester behavior, metrics, normalization, combination, diagnostics,
synthetic demos, real data fetching, vendor access, credentials, live or paper
trading, brokerage integration, order execution, or profitability claims were
changed.

Validation at the time of this entry:

```text
python -m pytest -q
391 passed

python -m compileall src tests research
passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-06 - Realized Volatility Feature

This code milestone implemented the next safe stage after the short-term
reversal feature: a small adjusted-price realized volatility research feature.

Assumption: the first volatility helper should compute unannualized trailing
realized volatility from simple one-period returns, leaving any annualization,
risk scaling, filtering threshold, portfolio construction, execution timing,
costs, slippage, backtesting, and interpretation to later explicit stages.
`calculate_realized_volatility()` therefore computes adjacent-price returns:

```text
price[t] / price[t - 1] - 1
```

and then calculates a full-window trailing standard deviation ending at the
signal date. The default window is 21 return observations and the default
degrees-of-freedom setting is `ddof=0`.

The feature uses only current and historical prices. It preserves the input
dates and asset columns, does not sort or reindex input data, does not fill
missing values, and treats returns as missing when either adjacent price anchor
is missing or non-positive. Any missing return inside the required trailing
window keeps the volatility value as `NaN`.

Focused tests in `tests/test_volatility.py` cover hand-calculated simple-return
volatility, no-lookahead behavior, date/column alignment, full-window
requirements, missing-price behavior without fills, non-positive anchor
handling, `ddof` behavior, sorted and duplicate date validation, window and
`ddof` validation, and non-numeric input rejection.

This stage does not fetch real data, add vendor access, add credentials,
connect to a broker, place orders, support live or paper trading, modify the
backtester, generate reports, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_volatility.py
20 passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-06 - Short-Term Reversal Feature

This code milestone implemented the next safe stage recommended by
`docs/post_liquidity_checkpoint_report.md`: a small close-price
short-term reversal research feature.

Assumption: the reversal score convention should make higher values represent
stronger contrarian candidates. `calculate_short_term_reversal()` therefore
computes the negative trailing return over a configurable lookback window:

```text
-(price[t] / price[t - lookback_periods] - 1)
```

The feature uses explicit current and trailing price anchors only. It preserves
the input dates and asset columns, does not sort or reindex input data, does
not fill missing values, and returns `NaN` when either required anchor is
missing or non-positive. Execution timing, signal lag, portfolio construction,
costs, slippage, backtesting, and interpretation remain separate later-stage
responsibilities.

Focused tests in `tests/test_reversal.py` cover hand-calculated sign
convention, no-lookahead behavior, date/column alignment, missing anchor
handling without fills, non-positive anchor handling, sorted and duplicate date
validation, lookback validation, and non-numeric input rejection.

This stage does not fetch real data, add vendor access, add credentials,
connect to a broker, place orders, support live or paper trading, modify the
backtester, generate reports, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_reversal.py
13 passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-06 - Post-Liquidity Roadmap Checkpoint

This documentation checkpoint refreshed the roadmap after PR #58 merged the
synthetic local-fixture liquidity eligibility count smoke check.

Assumption: after the OHLCV and liquidity sequence, the next safest PR-sized
stage is to reconcile stale roadmap recommendations before starting another
feature implementation. `docs/original_goal_gap_analysis.md` and
`docs/current_roadmap_gap_refresh.md` still contain useful original-goal
context, but they predate several completed stages: IC / Rank IC diagnostics,
quantile spread diagnostics, validation split helpers, local CSV fixture
workflow, strict OHLCV loading, synthetic liquidity eligibility helpers, and
the local fixture liquidity count smoke check.

`docs/post_liquidity_checkpoint_report.md` now records the current
implementation state, completed roadmap items, remaining gaps, guardrail
review, and a next-stage recommendation. The report identifies
`src/features/reversal.py` and `src/features/volatility.py` as placeholder
modules only and recommends short-term reversal feature design or
implementation as the next safe stage, subject to explicit score-sign and
missing-value tests.

This stage is documentation-only. It does not modify source code, tests,
research scripts, generated reports, strategy logic, backtester behavior,
metrics, data access, execution assumptions, real data handling, vendor
access, credentials, live or paper trading, brokerage integration, order
execution, or profitability claims.

Validation before this checkpoint:

```text
python -m pytest -q
358 passed

python -m compileall src tests research
passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-06 - Synthetic Liquidity Eligibility Fixture Smoke Check

This code milestone extended the committed synthetic local CSV fixture workflow
with a narrow liquidity eligibility count smoke check after the synthetic-only
liquidity helper merged.

Assumption: the next safe PR-sized stage is not universe construction,
strategy validation, backtesting, or real-data interpretation. It is a wiring
check that proves the existing strict local CSV workflow can load the committed
synthetic OHLCV fixture, pivot `adjusted_close` and `volume`, align those panels
to the synthetic adjusted-close fixture, and report lagged ADV and
dollar-volume eligibility counts without filling missing volume.

`research/local_csv_fixture_workflow_demo.py` now loads the synthetic OHLCV
fixture with `load_ohlcv_csv()`, computes lagged eligibility masks with
`average_daily_volume_eligibility()` and
`average_dollar_volume_eligibility()`, and writes decision-date count
diagnostics to the synthetic report and JSON experiment log. The default smoke
parameters use a two-row window, one-row eligibility lag, a minimum average
volume threshold, and a minimum average dollar-volume threshold. Missing and
zero-volume counts remain visible in the report; no forward-fill,
backward-fill, interpolation, zero default, universe construction, portfolio,
backtest, external data access, broker connection, order execution, or
profitability claim is added.

Focused tests in `tests/test_local_csv_fixture_workflow_demo.py` assert the
aligned liquidity panels, expected lagged eligibility counts, missing-volume
counts, zero-volume counts, report caveats, JSON diagnostics, and integration
with the existing loader and liquidity helpers.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
13 passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-06 - Synthetic Liquidity Eligibility Helper

This code milestone implemented the next safe stage after
`docs/liquidity_dollar_volume_universe_plan.md`: a narrow synthetic-only
liquidity eligibility helper with deterministic tests.

Assumption: the reviewed liquidity and dollar-volume planning gate made the
function boundary clear enough to implement a small helper rather than adding
another design-only checkpoint. The implementation is limited to already
prepared numeric panels and does not connect to the CSV loader, fetch data,
select a portfolio, run a backtest, modify alpha formulas, alter diagnostics,
generate reports, add vendor access, add credentials, connect to a broker,
place orders, support live or paper trading, or make profitability claims.

`src/features/liquidity.py` now provides rolling average daily volume and
rolling average dollar-volume helpers plus lagged eligibility masks. The
eligibility helpers use full rolling windows only, preserve missing values as
ineligible observations, reject negative volume and non-positive prices,
require positive finite thresholds, default to a one-row eligibility lag, and
require each rolling volume window to contain strictly positive volume by
default. That default keeps zero-volume rows from being silently accepted as
liquid while still allowing an explicit non-default policy for synthetic tests.

Focused tests in `tests/test_liquidity.py` cover hand-calculated ADV and
dollar-volume calculations, date-lag semantics, warm-up ineligibility, missing
values without filling, default zero-volume exclusion, explicit zero-volume
policy override, configurable positive lags, invalid thresholds, invalid
windows, mismatched panels, negative volume, non-positive prices, non-numeric
inputs, and forbidden import boundaries.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_liquidity.py
30 passed

python -m pytest -q
357 passed

python -m compileall src tests research
passed

.\scripts\audit-skills.ps1
passed for 2 Skill files
```

---

## 2026-06-06 - Liquidity And Dollar-Volume Universe Planning Gate

This documentation-only milestone added
`docs/liquidity_dollar_volume_universe_plan.md` after the strict OHLCV loader
and synthetic OHLCV loader smoke coverage merged.

Assumption: the next safe stage after OHLCV validation and smoke coverage is
not volume-based filtering code or a volume-dependent alpha. The safer
PR-sized step is to define local-only liquidity and dollar-volume universe
rules, date-alignment requirements, zero-volume handling, missing-data
behavior, and future implementation gates before any code filters assets by
volume.

The plan defines candidate inputs, average daily volume, dollar-volume, and
rolling dollar-volume formulas, explicit observation/decision/signal/execution
date boundaries, strict missing-value and zero-volume policy, candidate
universe rules, future deterministic test requirements, research risks, and
future PR-sized stages. It preserves the existing research-only boundary and
does not implement a universe filter, modify loaders, modify features, modify
backtests, add research scripts, generate reports, fetch data, add vendor
access, add credentials, connect to a broker, place orders, support live or
paper trading, or make profitability claims.

`docs/volume_ohlcv_schema_plan.md` now records the liquidity planning note as
the completed planning gate before volume-based filtering. The WorldQuant
alpha catalog now points future liquidity or dollar-volume universe work to
this plan before implementation.

Validation at the time of this entry:

```text
python -m pytest -q
327 passed

python -m compileall src tests research
passed
```

---

## 2026-06-06 - Synthetic OHLCV Loader Smoke Demo

This test milestone added fixture-level smoke coverage for the strict local
OHLCV CSV loader after the loader implementation merged.

Assumption: after the strict `load_ohlcv_csv()` stage, the next safe
PR-sized step is Stage 3 from `docs/volume_ohlcv_schema_plan.md`: validate the
committed synthetic OHLCV fixture at the smoke-demo level before any
liquidity filter, dollar-volume workflow, OHLC-dependent alpha, strategy
logic, or generated report is added.

The stage extends `tests/test_local_csv_loader_smoke_demo.py` rather than
creating a research script. That keeps the work focused on loader wiring and
audit metadata: the committed synthetic OHLCV fixture loads with the expected
schema, sorted dates, duplicate-free date-symbol pairs, float numeric fields,
positive OHLC relationships, summary metadata, and required adjusted-close
policy. Additional synthetic temporary files test that missing values remain
strict by default and invalid OHLC relationships are rejected.

`docs/volume_ohlcv_schema_plan.md` now reflects the completed loader and smoke
coverage and recommends a future liquidity or dollar-volume universe planning
note before any code filters assets by volume. This change remains local and
synthetic only. It does not modify source code, research scripts, reports,
feature formulas, alpha modules, diagnostics, backtester behavior, metrics,
real-data access, vendor downloads, credentials, live or paper trading,
brokerage or order execution, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_loader_smoke_demo.py
6 passed

python -m pytest -q
327 passed

python -m compileall src tests research
passed
```

---

## 2026-06-06 - Strict Local OHLCV CSV Loader

This code milestone implemented the next stage recommended by
`docs/volume_ohlcv_schema_plan.md`: a strict local OHLCV long-format CSV
loader using committed synthetic fixtures only.

Assumption: the reviewed OHLCV schema plan made the implementation scope clear
enough to proceed without an additional documentation-only checklist. The
stage is limited to local CSV validation and does not compute a strategy,
generate reports, modify alpha formulas, modify diagnostics, modify the
backtester, fetch data, add vendor APIs, add credentials, connect to a broker,
place orders, support live or paper trading, or make profitability claims.

`src/data/csv_loader.py` now exposes `load_ohlcv_csv()` and
`ValidatedCSVFrame`. The loader preserves raw CSV strings through validation,
requires local `.csv` paths, rejects duplicate headers, validates required
`date`, `symbol`, `open`, `high`, `low`, `close`, and `volume` columns,
supports optional or required `adjusted_close`, rejects duplicate
`(date, symbol)` rows, rejects missing symbols, rejects missing or invalid
numeric sentinels by default, preserves missing values only when
`allow_missing=True`, requires positive OHLC and `adjusted_close` values when
present, allows zero volume but rejects negative volume, and rejects impossible
OHLC relationships.

The zero-volume decision is intentionally narrow: zero volume is accepted as a
non-negative local loader value so the loader does not impose liquidity-policy
assumptions. Future liquidity or dollar-volume stages must explicitly report,
filter, or reject zero-volume rows in their own tests and documentation.

Test coverage in `tests/test_csv_loader.py` and
`tests/fixtures/local_csv_loader_smoke/synthetic_ohlcv.csv` covers valid
synthetic OHLCV loading, summary metadata, strict missing-value rejection,
explicit missing preservation, duplicate date-symbol pairs, missing symbols,
required adjusted close, negative and zero volume behavior, non-positive
prices, and invalid OHLC relationships.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_csv_loader.py
34 passed

python -m pytest -q
324 passed

python -m compileall src tests research
passed
```

---

## 2026-06-06 - Volume And OHLCV Schema Planning Gate

This documentation-only milestone added
`docs/volume_ohlcv_schema_plan.md` after the local CSV fixture split metadata
workflow merged.

Assumption: after Stage C in `docs/current_roadmap_gap_refresh.md` was
completed by the local CSV fixture split metadata workflow, the next safe
roadmap stage is Stage D: volume/OHLCV schema planning. The planning gate is
needed before implementing volume-dependent factors, OHLC-dependent
WorldQuant-style alphas, or liquidity-based universe filters.

The plan defines future local volume-only and OHLCV long-format schemas,
optional metadata sidecar expectations, strict validation rules, alignment
requirements with existing feature and backtest modules, research risks, and
future PR-sized stages. It preserves the existing local-file-only boundary and
does not implement a loader, add fixtures, modify `src/`, modify tests,
generate reports, fetch data, add vendor access, add credentials, connect to a
broker, place orders, support live or paper trading, or make profitability
claims.

`docs/csv_data_interface_plan.md` now points to this plan as the schema gate
before volume or OHLCV loader support. `docs/worldquant_alpha_catalog.md` now
points future volume or OHLC-dependent alpha work to the plan before code is
added.

Validation at the time of this entry:

```text
python -m pytest -q
309 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-05 - Local CSV Fixture Split Metadata Workflow Update

This code milestone updated the committed synthetic local CSV fixture workflow
after the split helper and split-aware IC / Rank IC demo had merged.

Assumption: after the split-aware diagnostic demo, the next safe roadmap stage
is the local fixture split-aware workflow update recommended by
`docs/current_roadmap_gap_refresh.md`. The stage applies existing
train/validation/test metadata to the already-committed synthetic local CSV
fixture workflow. It remains a fixture wiring and diagnostic coverage check,
not a real-data study, model-selection result, backtest, strategy validation,
or performance claim.

The workflow now configures chronological fixture split boundaries, creates a
`TrainValidationTestSplit` from the loaded price index, slices the `alpha_009`
factor panel and forward-return target panel with
`split_panel_by_train_validation_test()`, and computes IC, Rank IC, and
quantile-spread diagnostics both overall and by split. The generated Markdown
report and JSON experiment log now include split boundaries, split coverage,
per-split diagnostic metadata, explicit signal-date split timing caveats, and
caveats that the output is synthetic, fixture-only, not model selection, and
not strategy validation.

Test coverage was expanded to check the expected train, validation, and test
fixture windows; alignment of split factor and target panels; deterministic
split outputs; caveated report/log fields; helper-use monkeypatch counts;
invalid split-boundary rejection; forbidden-import checks; and caveated
profitability language.

This change does not modify CSV loader behavior, alpha formulas, diagnostic
helper behavior, validation helper behavior, backtester behavior, metrics,
LEAN code, normalization, combination, real-data access, vendor downloads,
credentials, live or paper trading, brokerage or order execution, or
profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
12 passed

python -m pytest -q
309 passed

python -m compileall src tests research
passed
```

---

## 2026-06-05 - Synthetic Split-Aware IC / Rank IC Demo

This code milestone added `research/synthetic_split_ic_rank_ic_demo.py` and
`tests/test_synthetic_split_ic_rank_ic_demo.py` after the
train/validation/test split helper merged.

Assumption: after PR #48 merged, the next safe roadmap stage is the
split-aware diagnostic demo recommended by
`docs/current_roadmap_gap_refresh.md`. The stage applies the existing
chronological split helper to deterministic synthetic factor and
forward-return panels before computing IC and Rank IC diagnostics. It is a
wiring and coverage demonstration only, not model selection, strategy
validation, a backtest, or evidence of factor performance.

The demo builds a small synthetic factor panel, derives synthetic
forward-return evaluation targets by split, preserves missing values, slices
both panels through `split_panel_by_train_validation_test()`, computes
`factor_information_coefficient()` and
`factor_rank_information_coefficient()` separately for train, validation, and
test windows, and summarizes date counts, valid observations, valid diagnostic
dates, mean IC, and mean Rank IC. Optional report and JSON log outputs are
caveated and can be redirected to temporary paths in tests.

The test coverage includes expected split windows, alignment checks,
missing-value preservation, deterministic reruns, hand-checked split summary
diagnostics, skipped output mode, caveated report and log creation, helper-use
monkeypatch checks, invalid configuration rejection, `main()` output writing,
forbidden import checks, and caveated profitability-language checks.

This change does not modify source feature formulas, diagnostics helper
behavior, validation helper behavior, CSV loader behavior, generated reports,
backtester behavior, metrics, LEAN code, alpha modules, normalization,
combination, or strategy logic. It does not fetch real data, download data,
add vendor APIs, add credentials, add live or paper trading, add brokerage or
order execution, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_synthetic_split_ic_rank_ic_demo.py
11 passed

python -m pytest -q
308 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-05 - Public Repository Metadata And License Polish

This documentation-stage checkpoint records the owner decision to publish the
repository under Apache-2.0 and updates the public GitHub shell around the
already-polished README landing page.

The file changes add the official Apache-2.0 root `LICENSE`, add a concise
`CITATION.cff` using only the repository URL, SPDX license identifier, GitHub
owner login, and observed git author name, and add
`docs/assets/social_preview.svg` as an original source asset for a possible
future GitHub social-preview upload. The README license badge now links to the
root license file, and the current-status language now states the Apache-2.0
license selection.

Assumption: this stage is public-presentation metadata work only. It does not
change `src/`, `tests/`, `research/`, `reports/`, data loading, factor formulas,
diagnostics, backtester behavior, generated result numbers, private-data
protections, LEAN behavior, live or paper trading scope, brokerage integration,
order execution, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
297 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only

gh api licenses/apache-2.0 --jq .spdx_id
Apache-2.0
```

---

## 2026-06-05 - Synthetic Train/Validation/Test Split Helper

This code milestone added `src/features/validation.py` and
`tests/test_validation.py` after the current roadmap gap refresh merged.

Assumption: the next safe implementation stage is the deterministic
train/validation/test split helper recommended by
`docs/current_roadmap_gap_refresh.md`. The helper is deliberately limited to
already-prepared date indexes and numeric factor panels. It does not fetch
data, calculate returns, choose parameters, run a backtest, modify reports, or
interpret performance.

The new `make_train_validation_test_split()` helper validates a
`DatetimeIndex`, preserves chronological order, rejects duplicate or unsorted
dates, applies inclusive train, validation, and test boundaries, requires
non-empty windows, and returns a `TrainValidationTestSplit` dataclass. The new
`split_panel_by_train_validation_test()` helper slices an already-prepared
numeric panel by those dates and preserves missing values instead of filling
or coercing them into synthetic observations.

The test coverage includes hand-calculated date windows, timestamp boundary
handling, split ordering, panel slicing, missing-value preservation, invalid
date indexes, invalid boundary order, empty windows, non-date boundaries,
invalid timestamp strings, non-numeric panels, mismatched indexes, and an
import guardrail check.

This change does not modify research scripts, generated reports, CSV loader
behavior, diagnostics behavior, backtester behavior, metrics, factor formulas,
normalization, combination, LEAN code, or strategy logic. It does not add real
data fetching, downloads, credentials, live or paper trading, brokerage,
order execution, a LEAN run, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_validation.py
25 passed

python -m pytest -q
297 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-05 - Current Roadmap Gap Refresh

This documentation-only checkpoint added
`docs/current_roadmap_gap_refresh.md` after PR #46 merged.

Assumption: after the LEAN signal-only momentum draft merged, the safest next
stage is to refresh the roadmap before adding more code. The older
`docs/original_goal_gap_analysis.md` still captures the original objective,
but several of its recommended next stages are now complete: local CSV fixture
smoke/demo work, IC and Rank IC helpers, quantile spread diagnostics, LEAN
planning, the non-executing LEAN scaffold, and the LEAN signal-only metadata
draft.

The checkpoint records current implementation traceability, remaining gaps,
guardrail status, and a refreshed roadmap. It recommends the next
implementation stage as a synthetic train/validation/test split helper because
validation-discipline support is now a larger gap than adding another factor
or duplicating already-implemented diagnostics.

This change does not modify `src/`, tests, research scripts, generated
reports, CSV loader behavior, diagnostics behavior, backtester behavior,
metrics, factor formulas, normalization, combination, LEAN code, or strategy
logic. It does not add real data fetching, downloads, credentials, live or
paper trading, brokerage, order execution, a LEAN run, or profitability
claims.

Validation at the time of this entry:

```text
python -m pytest -q
272 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-05 - LEAN Signal-Only Momentum Draft

This code milestone added a pure-Python LEAN-adjacent signal-only draft after
the signal-only design merged and later public-facing README/CI stages were
also merged.

Assumption: the current next safe stage is the implementation recommended by
`docs/lean_signal_only_draft_design.md`: a metadata-only
`lean/signal_only_momentum_draft.py` plus static guardrail tests. The stage is
code-changing, but it remains pre-runtime and signal-only. It does not import
LEAN runtime symbols, create a runnable QuantConnect algorithm, create
`config.json`, run LEAN, fetch data, read credentials, configure brokerage,
define orders, calculate returns, produce reports, or claim profitability.

The new draft records the signal name, 12-1 momentum lookback and skip-window
metadata, required input fields, timing contract fields, diagnostic field
names, guardrails, and caveats. It exposes
`describe_signal_only_momentum_draft()` so reviewers can inspect the metadata
without calculating a signal or touching data.

The new `tests/test_lean_signal_only_draft_scope.py` statically checks that
the draft exists, remains non-runnable, avoids banned runtime/data/credential
imports, avoids LEAN runtime and order/brokerage calls, declares the required
timing and diagnostic metadata, returns no performance or order outputs, and
keeps README guardrail language visible. `lean/README.md` now documents the
signal-only draft and its focused validation command.

This change does not modify `src/`, research scripts, generated reports, CSV
loader behavior, diagnostics behavior, backtester behavior, metrics, factor
formulas, normalization, combination, or strategy logic. It does not add real
data fetching, downloads, credentials, live or paper trading, brokerage,
order execution, runnable LEAN code, a LEAN run, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_lean_signal_only_draft_scope.py
8 passed

python -m pytest -q tests/test_lean_smoke_test_scope.py tests/test_lean_signal_only_draft_scope.py
14 passed

python -m pytest -q
272 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - GitHub Actions CI Badge

This CI/documentation milestone adds the first repository GitHub Actions
workflow after the public landing-page polish merged.

Assumption: the next safe public-facing stage is a minimal CI workflow that
uses the repository's existing Python packaging and validation commands. The
workflow installs dependencies with `python -m pip install -e ".[dev]"`, which
matches the existing `pyproject.toml` optional dev dependency setup, and uses
Python 3.11 to satisfy the documented `requires-python >=3.11` boundary.

The new `.github/workflows/ci.yml` workflow is named `CI` and runs on pull
requests targeting `main` and pushes to `main`. It checks out the repository,
sets up Python 3.11, installs project and dev dependencies, runs
`python -m pytest -q`, runs `python -m compileall src tests research`, and
runs `python -m compileall lean`. The README replaces the static local-test
status label with a live badge for the new workflow file.

This change does not modify `src/`, tests, research scripts, generated reports,
CSV loader behavior, diagnostics behavior, backtester behavior, metrics, factor
formulas, normalization, combination, LEAN scaffold behavior, strategy logic,
private-data protections, result numbers, repository visibility, or license
state. It does not add real data fetching, credentials, live trading,
brokerage integration, order execution, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
264 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only

README badge/workflow target check
passed
```

---

## 2026-06-04 - Public GitHub Landing Page Polish

This documentation-only milestone improves the public README as a newcomer
landing page after the LEAN signal-only draft design merged.

Assumption: the next safe public-facing stage is presentation polish rather
than additional research logic. The update keeps the current research scope
unchanged and makes the repository easier to evaluate from the GitHub first
screen.

The README now has a concise tagline, truthful static status labels, a short
description of what the repository is, runnable synthetic/local-fixture demo
commands, a beginner-friendly PowerShell Quick Start, a local CSV fixture demo
walkthrough, a project map, links to key reports and demo files, and an
explicit safety/scope section. The new `docs/assets/research_workflow.svg`
diagram is an original workflow visual that explains the research process
without implying live trading, brokerage integration, order execution, or
profitability.

This change does not modify `src/`, tests, research scripts, generated reports,
CSV loader behavior, diagnostics behavior, backtester behavior, metrics, factor
formulas, normalization, combination, LEAN scaffold behavior, strategy logic,
private-data protections, or result numbers. It does not add a license file,
GitHub Actions workflow, real data fetching, credentials, live trading,
brokerage integration, order execution, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
264 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

README relative-link sanity check
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - LEAN Signal-Only Draft Design

This documentation-only milestone added
`docs/lean_signal_only_draft_design.md` after the runnable draft readiness
decision merged.

Assumption: after PR #42 merged, the next unblocked safe stage is the
signal-only draft design that PR #42 explicitly recommended. The design keeps
the next LEAN-adjacent code boundary pure Python and metadata-only, without
LEAN runtime imports, local or cloud LEAN execution, real data access,
credentials, live trading, paper trading, brokerage integration, order
execution, or profitability claims.

The design defines the purpose, decision, future file boundary, timing
contract, static validation plan, out-of-scope items, stop conditions, and the
recommended next stage. It narrows the next possible code PR to
`lean/signal_only_momentum_draft.py` and
`tests/test_lean_signal_only_draft_scope.py`, with optional updates to
`lean/README.md`, durable logs, and `CHANGELOG.md` if that future PR documents
the scope.

This change does not modify `src/`, tests, research scripts, generated
reports, LEAN code, CSV loader behavior, diagnostics behavior, backtester
behavior, metrics, factor formulas, normalization, combination, or strategy
logic. It does not add `AlgorithmImports`, `QCAlgorithm`, `config.json`, data
fetching, downloads, credentials, live or paper trading, brokerage, order
execution, a LEAN run, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
264 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - LEAN Runnable Draft Readiness Decision

This documentation-only milestone added
`docs/lean_runnable_draft_readiness_decision.md` after the LEAN scaffold review
checklist merged.

Assumption: after PR #41 merged, the next safe stage is an
implementation-readiness decision rather than a runnable LEAN algorithm draft.
The current guardrails still prohibit real market data fetching, downloads,
credentials, live trading, paper trading, brokerage integration, order
execution, and profitability claims. A normal runnable LEAN draft would likely
introduce runtime imports, platform data semantics, portfolio target calls,
orders, fills, fee models, slippage models, and backtest outputs before those
boundaries are explicitly approved.

The decision records that the repository is not yet ready for runnable LEAN
code under current guardrails. It identifies blockers around runtime imports,
data-source semantics, order semantics, credential/account boundaries, and
result interpretation. It recommends the next stage as a documentation-only
LEAN signal-only draft design that can define whether any future code PR may
import LEAN runtime symbols and how static validation should separate signal
metadata from order execution.

This change does not modify `src/`, tests, research scripts, generated
reports, the LEAN scaffold code, CSV loader behavior, diagnostics behavior,
backtester behavior, metrics, factor formulas, normalization, combination, or
strategy logic. It does not add `AlgorithmImports`, `QCAlgorithm`,
`config.json`, data access, credentials, live or paper trading, brokerage,
order execution, a LEAN run, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
264 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - LEAN Scaffold Review Checklist

This documentation-only milestone added `docs/lean_scaffold_review_checklist.md`
after the minimal non-executing LEAN scaffold merged.

Assumption: after PR #40 merged, the next unblocked safe stage is a scaffold
review checklist before deciding whether a future PR can safely create a
runnable LEAN draft. This keeps the workflow moving while avoiding a premature
runtime implementation that could require platform access, credentials, real
data, brokerage integration, order execution, live trading, paper trading, or
performance interpretation.

The checklist defines the current scaffold files under review, required review
questions, static checks, safe expansion criteria, stop conditions, and the
recommended next stage: a narrow implementation-readiness decision. It does
not approve a runnable LEAN algorithm, `config.json`, local or cloud LEAN run,
data download, credential path, order path, or profitability claim.

This change does not modify `src/`, tests, research scripts, generated
reports, the LEAN scaffold code, CSV loader behavior, diagnostics behavior,
backtester behavior, metrics, factor formulas, normalization, combination, or
strategy logic.

Validation at the time of this entry:

```text
python -m pytest -q
264 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - Minimal Non-Executing LEAN Smoke-Test Scaffold

This scaffold milestone added a first `lean/` directory after the LEAN
implementation planning checkpoint merged.

Assumption: after PR #39 merged, the next unblocked safe stage is the planned
minimal non-executing LEAN scaffold with static guardrail tests. The scaffold
is deliberately metadata-only and does not import the LEAN runtime, create a
`config.json`, run a local or cloud backtest, fetch data, read credentials,
connect to a broker, enable live trading or paper trading, submit orders, or
interpret performance.

The new `lean/README.md` records the scaffold purpose, current files, local
validation commands, and stop conditions. The new
`lean/smoke_test_algorithm.py` defines review metadata, configuration fields,
the timing contract, diagnostic field names, and guardrail constants without
creating a runnable QuantConnect algorithm. The new
`tests/test_lean_smoke_test_scope.py` statically validates the scaffold file
boundary, rejects external data and credential imports, rejects order and
brokerage calls, and checks for timing, diagnostic, and caveat coverage.

This change does not modify `src/`, research scripts, generated reports, CSV
loader behavior, diagnostics behavior, backtester behavior, metrics, factor
formulas, normalization, combination, or strategy logic. It does not fetch
data, download data, connect to a broker, place orders, add credentials,
enable live trading, add paper trading, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_lean_smoke_test_scope.py
6 passed

python -m pytest -q
264 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - LEAN Implementation Planning Checkpoint

This documentation-only milestone added
`docs/lean_implementation_planning_checkpoint.md` after PR #38 merged.

Assumption: after the LEAN smoke-test design note merged, the next unblocked
safe LEAN-related stage is an implementation planning checkpoint before any
LEAN algorithm file or project scaffold. This keeps the workflow moving while
preserving the merge gate and avoiding external platform access, credentials,
real data downloads, brokerage integration, order execution, live trading,
paper trading, and performance interpretation.

The checkpoint chooses the intended boundary for the first future LEAN code
PR: `lean/README.md`, `lean/smoke_test_algorithm.py`,
`tests/test_lean_smoke_test_scope.py`, `docs/engineering_log.md`, and
`CHANGELOG.md`. It also defines the future algorithm draft scope, static local
validation strategy, review gates, stop conditions, and the recommended next
stage: a minimal non-executing LEAN scaffold with static guardrail tests.

This change does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, diagnostics behavior, backtester behavior,
metrics, data access, or strategy logic. It does not fetch data, download data,
connect to a broker, place orders, add credentials, enable live trading, add
paper trading, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
258 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - LEAN Smoke-Test Design Note

This documentation-only milestone added `docs/lean_smoke_test_design.md` after
the LEAN parity checklist merged.

Assumption: after PR #37 merged, the next unblocked safe LEAN-related stage is
a smoke-test design note, not LEAN algorithm code or a project scaffold. This
keeps the stage aligned with the checklist recommendation while avoiding
external platform access, credentials, real data downloads, brokerage
integration, order execution, live trading, paper trading, or performance
interpretation.

The design note defines future smoke-test preconditions, a minimal future
scenario, a timing contract, smoke-test assertions, diagnostics to preserve,
local-vs-LEAN comparison priorities, experiment-record shape, stop conditions,
and the next planning checkpoint before any future LEAN code PR.

This change does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, diagnostics behavior, backtester behavior,
metrics, data access, or strategy logic. It does not fetch data, download data,
connect to a broker, place orders, add credentials, enable live trading, add
paper trading, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
258 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - LEAN Parity Checklist Planning

This documentation-only milestone added `docs/lean_parity_checklist.md` after
the refreshed QuantConnect/LEAN plan merged.

Assumption: after PR #36 merged and baseline validation passed, the next
unblocked safe stage from `docs/quantconnect_lean_plan.md` is a LEAN parity
checklist or smoke-test plan. The stage is kept documentation-only because the
repository still needs explicit parity gates before any LEAN algorithm,
platform scaffold, real data, credentials, brokerage integration, order
execution, live trading, or performance interpretation.

The checklist maps current local evidence to future LEAN smoke-test
assertions: 12-1 momentum timing, `alpha_009` feature-only status, strict data
validation mindset, IC / Rank IC / quantile spread diagnostics, benchmark
configuration, fees, slippage, cash buffer, simulated order-accounting caveats,
experiment-log requirements, local-vs-LEAN parity review, and stop conditions.

This change does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, diagnostics behavior, backtester behavior,
metrics, data access, or strategy logic. It does not fetch data, download data,
connect to a broker, place orders, add credentials, enable live trading, or
make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
258 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - QuantConnect/LEAN Plan Refresh After CSV Diagnostics

This documentation-only milestone refreshed `docs/quantconnect_lean_plan.md`
after the local CSV fixture workflow demo merged.

Assumption: after PR #35 merged and baseline validation passed, the next
unblocked safe stage from `docs/original_goal_gap_analysis.md` is Stage F:
refresh the QuantConnect/LEAN plan from the current local modules. The stage is
kept plan-only because the repository is not ready for LEAN algorithm code,
real data, platform access, credentials, brokerage integration, order
execution, or performance interpretation.

The updated plan now records the current local status before any LEAN code:
strict local CSV loaders, committed synthetic CSV fixtures, the local CSV
fixture workflow demo, `alpha_009`, IC / Rank IC diagnostics, quantile spread
diagnostics, experiment logs, and the experiment registry. It maps those local
components to future LEAN planning concepts while preserving the distinction
between local synthetic fixtures, user-provided local CSV work, and platform
subscriptions/history.

The plan also adds diagnostic mapping guidance for IC, Rank IC, and quantile
spread exports from a future LEAN smoke run. Forward returns remain evaluation
targets only and must not become signal inputs. Quantile spread remains a
diagnostic, not a strategy-validation or profitability claim. The recommended
next LEAN-related stage is a parity checklist or smoke-test plan, not an
algorithm implementation.

This change does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, diagnostics behavior, backtester behavior,
metrics, data access, or strategy logic. It does not fetch data, download data,
connect to a broker, place orders, add credentials, enable live trading, or
make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
258 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - Local CSV Fixture Research Workflow Demo

This code-and-report milestone added a synthetic local CSV fixture workflow
demo after the local CSV loader smoke tests, synthetic IC / Rank IC
diagnostics, and synthetic quantile spread diagnostics had merged.

Assumption: after PR #34 merged, the next unblocked safe stage from
`docs/original_goal_gap_analysis.md` is Stage E: run a complete local-file
workflow on committed synthetic CSV fixtures only. The stage is intentionally
small and uses the already-reviewed local CSV loader, `alpha_009`, IC, Rank IC,
and quantile spread helpers instead of introducing new source-layer behavior.

The new `research/local_csv_fixture_workflow_demo.py` script loads the
committed synthetic adjusted-close and benchmark fixtures under
`tests/fixtures/local_csv_loader_smoke/`, verifies benchmark date alignment,
computes `alpha_009` as a close-only research feature with a one-row diagnostic
window, computes next-row forward returns as evaluation targets only, and runs
IC, Rank IC, and quantile spread diagnostics. The forward returns are not
feature inputs, not a portfolio rule, and not an execution assumption.

The generated report and JSON sidecar log are synthetic fixture diagnostics
only. They are included to prove that the local CSV path can participate in a
caveated, auditable workflow without using real data, downloads, vendor APIs,
credentials, live trading, brokerage integration, order execution, or
profitability claims. The experiment registry is refreshed so the new
synthetic local CSV workflow log is discoverable alongside earlier synthetic
demos.

Focused tests in `tests/test_local_csv_fixture_workflow_demo.py` cover fixture
loading, date and asset alignment, deterministic outputs, report and log
caveats, output-suppression behavior for tests, use of existing loader/feature
and diagnostic helpers, rejection of absolute fixture paths, config
validation, import guardrails, and caveated profitability language.

This change does not modify CSV loader behavior, feature formulas,
normalization, factor combination, diagnostics, backtester behavior, metrics,
or external data access. It does not run a backtest or claim that `alpha_009`
is useful on real market data.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
11 passed

python -m pytest -q
258 passed

python -m compileall src tests research
passed
```

---

## 2026-06-04 - Synthetic Quantile Spread Diagnostics

This code milestone added synthetic-first quantile spread diagnostics to
`src/features/diagnostics.py`.

Assumption: after the synthetic IC / Rank IC diagnostics PR merged, the next
unblocked safe stage from `docs/original_goal_gap_analysis.md` is Stage D: add
a quantile-bucket diagnostic helper using synthetic panels first. The helper is
kept in the existing diagnostics module because it is research visibility
infrastructure, not a strategy, backtest integration, report generator, or data
loader.

The new `factor_quantile_spread` helper computes per-date cross-sectional
factor quantile diagnostics against an already-aligned forward-return
evaluation panel. The helper reports bottom-quantile mean return,
top-quantile mean return, top-minus-bottom spread, valid asset count, and edge
quantile counts. `forward_returns` is treated as an evaluation target supplied
by the caller, not as a feature input.

Missing values are handled conservatively: each date uses only overlapping
non-missing factor and return pairs; missing values are not filled,
forward-filled, backward-filled, or converted to zeros. Dates with too few
valid assets, too few distinct factor values to form the requested quantiles,
or too few assets in either edge quantile return `NaN` for the return and
spread columns while preserving coverage counts.

Focused tests in `tests/test_diagnostics.py` cover hand-calculated
top-minus-bottom spreads, pairwise missing-value overlap without filling,
low-coverage dates, insufficient distinct factor values, minimum edge-bucket
size checks, date and asset alignment validation, invalid string-value
rejection, and quantile-parameter validation.

This change does not modify CSV loader behavior, local CSV fixtures, synthetic
reports, research scripts, feature formulas, normalization, factor combination,
backtester behavior, metrics, data access, execution assumptions, or
performance claims. It does not fetch data, download data, add vendor access,
introduce live trading, add brokerage or order-execution logic, store
credentials, or make profitability claims.

Validation:

```text
python -m pytest -q tests/test_diagnostics.py
58 passed

python -m pytest -q
247 passed

python -m compileall src tests research
passed
```

---

## 2026-06-04 - Synthetic IC And Rank IC Diagnostics

This code milestone added synthetic-first information coefficient diagnostics
to `src/features/diagnostics.py`.

Assumption: after the local CSV loader smoke demo merged, the next unblocked
safe stage from `docs/original_goal_gap_analysis.md` is Stage C: add IC and
Rank IC helpers using synthetic panels first. The implementation is kept in the
existing diagnostics module because the helper is diagnostic research
infrastructure, not a strategy, backtest integration, report generator, or data
loader.

The new `factor_information_coefficient` helper computes a per-date
cross-sectional correlation between an already-prepared factor panel and an
already-aligned forward-return evaluation panel. The helper does not compute
returns, shift dates, select assets, fill missing values, connect to the
backtester, or interpret results. `forward_returns` is explicitly treated as an
evaluation target supplied by the caller, not as a feature input.

The new `factor_rank_information_coefficient` helper wraps the same alignment
and missing-data behavior with Spearman correlation for Rank IC. Dates with
fewer than `min_periods` overlapping valid assets return `NaN`; missing values
are not filled, forward-filled, backward-filled, or converted to zeros.

Focused tests in `tests/test_diagnostics.py` cover hand-calculated Pearson IC,
hand-calculated Spearman Rank IC, pairwise missing-value overlap without
filling, low-coverage dates returning `NaN`, date and asset alignment
validation, invalid string-value rejection, method validation, and
`min_periods` validation. The existing diagnostics import-boundary test still
guards against adding backtest, alpha, reporting, vendor download, or real-data
imports to the diagnostics module.

This change does not modify CSV loader behavior, local CSV fixtures, synthetic
reports, research scripts, feature formulas, normalization, factor combination,
backtester behavior, metrics, data access, execution assumptions, or
performance claims. It does not fetch data, download data, add vendor access,
introduce live trading, add brokerage or order-execution logic, store
credentials, or make profitability claims.

Validation:

```text
python -m pytest -q tests/test_diagnostics.py
38 passed

python -m pytest -q
227 passed

python -m compileall src tests research
passed
```

---

## 2026-06-03 - Local CSV Loader Synthetic Fixture Smoke Demo

This test-focused milestone added a committed synthetic local CSV fixture set
and smoke tests for the existing strict local CSV loader.

Assumption: the next stage recommended by
`docs/original_goal_gap_analysis.md` should be implemented as a focused test
and fixture stage, not as a research script or generated report. This keeps the
stage deterministic and avoids interpreting any result as market evidence.

The new fixtures under `tests/fixtures/local_csv_loader_smoke/` are synthetic,
small, local-only CSV files:

- `synthetic_adjusted_close.csv`
- `synthetic_adjusted_close_with_missing.csv`
- `synthetic_benchmark.csv`

The new smoke tests in `tests/test_local_csv_loader_smoke_demo.py` verify that
the existing loader can read a local wide adjusted-close panel, preserve
expected date indexes and asset columns, produce float-valued panels, align a
benchmark series to the same dates, expose audit summary metadata, and enforce
the missing-value policy. Missing values are rejected by default and preserved
only through explicit `allow_missing=True`; no fill, forward-fill,
backward-fill, or zero default is introduced.

This change does not modify CSV loader source code, feature calculations,
backtester behavior, metrics, research scripts, generated reports,
normalization, factor combination, diagnostics, data access, execution
assumptions, or performance claims. It does not fetch data, download data, add
vendor access, introduce live trading, add brokerage or order-execution logic,
store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q tests/test_local_csv_loader_smoke_demo.py tests/test_csv_loader.py
22 passed

python -m pytest -q
212 passed

python -m compileall src tests research
passed
```

---

## 2026-06-03 - Original Goal Gap Analysis Checkpoint

This documentation-only checkpoint added
`docs/original_goal_gap_analysis.md` before starting any new feature stage.

The analysis compares the original project objective from `PROJECT_SPEC.md`,
`README.md`, and `docs/project_overview.md` against the current implemented
state recorded in checkpoint reports, `docs/engineering_log.md`,
`CHANGELOG.md`, `EXPERIMENT_LOG.md`, `docs/worldquant_alpha_catalog.md`, and
`docs/quantconnect_lean_plan.md`.

The current repository has progressed from governance and skeleton work to a
tested simulated research pipeline with 12-1 momentum, a long-only backtester,
synthetic demos, synthetic experiment logs and registry, WorldQuant catalog and
`alpha_009`, reusable operators, normalization, winsorization, factor
combination, diagnostics, local CSV interface planning, a strict local CSV
loader, real-data readiness documentation, and QuantConnect/LEAN planning.

The main remaining gap is that the project has not yet completed a full
local-CSV-based research study. No real-data IC, Rank IC, quantile spread,
train/validation/test split, benchmark/universe study, or LEAN implementation
exists yet. Paper and live trading remain intentionally out of scope.

The recommended next stage after this checkpoint PR is a local CSV loader smoke
demo using a committed synthetic local fixture only. That stage should verify
local-file workflow wiring without fetching data, interpreting market evidence,
or adding trading functionality.

During the startup checks for this checkpoint, a low-risk workflow command
issue occurred:

- Original mistake: a GitHub PR state command used Bash-style `|| true` inside
  PowerShell.
- Consequence: PowerShell rejected the command before `gh pr view 30` could
  run.
- Evidence: `The token '||' is not a valid statement separator in this
  version.`
- Investigation: the command was written with a Bash fallback despite the
  repository running in a Windows PowerShell shell.
- Correction attempt: reran PR checks as separate PowerShell-compatible
  commands.
- Final fix: `gh pr list --state open` returned no open PRs, and
  `gh pr view 30` confirmed PR #30 was merged.
- Verification: baseline validation passed before the documentation was
  created: `python -m pytest -q` reported 209 passed and
  `python -m compileall src tests research` passed.
- Remaining caveat: future shell snippets in this repository should use
  PowerShell-compatible fallbacks rather than Bash `|| true`.
- Prevention: split optional `gh` probes into separate PowerShell commands or
  use explicit PowerShell error handling.

An additional pre-publish formatting issue occurred during commit:

- Original mistake: `git diff --cached --check` and `git commit` were run in
  the same PowerShell command block.
- Consequence: the whitespace check reported an issue, but the commit still
  completed because the command block did not stop after the failed check.
- Evidence: `docs/original_goal_gap_analysis.md:214: new blank line at EOF.`
- Investigation: the new checkpoint document ended with an extra blank line,
  and the command sequencing allowed the commit to proceed before fixing it.
- Correction attempt: inspected the end of the document, removed the extra EOF
  blank line, and amended the same commit instead of creating a second cleanup
  commit.
- Final fix: the final branch commit contains the corrected document and
  updated engineering log.
- Verification: `git diff --check origin/main..HEAD` was rerun after the amend
  and passed.
- Remaining caveat: Windows LF-to-CRLF warnings can still appear, but they are
  not whitespace errors.
- Prevention: run `git diff --cached --check` as a separate gating command
  before `git commit`, or explicitly stop on failure before committing.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, metrics, CSV loader
behavior, normalization, factor combination, diagnostics, data access,
execution assumptions, or performance claims. It does not fetch data, download
data, add vendor access, introduce live trading, add brokerage or
order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
209 passed

python -m compileall src tests research
passed
```

---

## 2026-06-03 - WorldQuant Alpha Catalog Status Refresh

This documentation-only milestone refreshed `docs/worldquant_alpha_catalog.md`
after the post-CSV checkpoint identified stale catalog-era wording.

Assumption: the post-CSV checkpoint recommendation to refresh the WorldQuant
catalog is the next unblocked safe stage because PR #29 was merged, `main` was
synced, baseline validation passed, and there were no open pull requests.

The catalog now distinguishes the original Stage 1 classification from the
current repository status: the reusable operator layer exists, `alpha_009` is
implemented and tested as a close-only research feature, other
WorldQuant-style alphas remain unimplemented, and there is no dedicated
WorldQuant-style alpha backtest integration.

The refresh also clarifies that `alpha_009` is not a full strategy, not a
trading recommendation, not connected to a dedicated alpha strategy backtest,
and not evidence of profitability. Remaining close-only candidates require
separate formula review and tests. `alpha_012` remains blocked on volume plus
close schema support, `alpha_101` remains blocked on OHLC support, and VWAP,
market-cap, and industry-neutral categories remain deferred.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, metrics, CSV loader
behavior, normalization, factor combination, diagnostics, data access,
execution assumptions, or performance claims. It does not fetch data, download
data, add vendor access, introduce live trading, add brokerage or
order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
209 passed

python -m compileall src tests research
passed
```

---

## 2026-06-03 - Active Goal Behavior Rules

This workflow-control milestone updated the long-running staged workflow rules
for bounded autonomous execution.

Assumption: the user's active-goal clarification should be persisted as
controller and Skill guidance, not implemented as source-code behavior.

The controller now states that low-risk ambiguity should be handled by making a
reasonable assumption, recording it in the final report and relevant durable
log, and continuing. It also distinguishes missing workflow/documentation
scaffolds, which can be created in separate workflow-control PRs, from missing
product-behavior artifacts, which require a stop report.

The stop conditions were expanded to cover dirty working trees before new
stages, unclear requirements that could cause destructive or broad
architecture changes, missing credentials or external access, new production
dependencies, unsafe test failures, high or medium review issues, security,
privacy, data-loss, or irreversible-operation risks, scope conflicts with
project governance, and ready PR gates requiring human review or merge.

The staged workflow Skill was updated with the same low-risk ambiguity and
missing-file behavior so future sessions do not require a fresh prompt after
every small step while remaining bounded by safety, scope, validation, and PR
review gates.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, metrics, CSV loader
behavior, alpha formulas, normalization, factor combination, diagnostics, data
access, execution assumptions, or performance claims. It does not fetch data,
download data, add vendor access, introduce live trading, add brokerage or
order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
209 passed

python -m compileall src tests research
passed

.\scripts\audit-skills.ps1
passed
```

---

## 2026-06-03 - Long-Running Workflow Control Scaffolding

This workflow-control milestone added the supporting process artifacts that the
long-running staged workflow now expects to read before continuing:
`docs/codex_long_running_controller.md`, `docs/decision_log.md`,
`docs/troubleshooting_log.md`, `CHANGELOG.md`, and
`scripts/audit-skills.ps1`.

The controller defines startup checks, merge gates, stage-selection guidance,
stop conditions, logging requirements, validation checks, Skill audit use, and
the rule to pause after PR creation without merging. The decision and
troubleshooting logs capture durable workflow decisions and detailed
failure-to-fix records. The changelog records user-visible repository changes.
The Skill audit script checks local repository Skill files for required
frontmatter, headings, and balanced Markdown code fences.

The staged workflow Skill was updated to read the new controller/log artifacts
and to run `.\scripts\audit-skills.ps1` for workflow-control or Skill changes.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, metrics, CSV loader
behavior, alpha formulas, normalization, factor combination, diagnostics, data
access, execution assumptions, or performance claims. It does not fetch data,
download data, add vendor access, introduce live trading, add brokerage or
order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
209 passed

python -m compileall src tests research
passed

.\scripts\audit-skills.ps1
passed
```

---

## 2026-06-03 - Beginner-Facing Project Overview

This documentation-only milestone added `docs/project_overview.md` and linked
it from `README.md`.

The overview explains the repository as an AI-assisted, simulated, auditable
equity factor research pipeline. It defines factor, signal, portfolio,
strategy, and conclusion; summarizes current components; lists what the project
is not; records evaluation standards for factor research; and keeps current
limitations visible for synthetic-only results, `alpha_009`, staged local CSV
readiness, and future QuantConnect/LEAN work.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, metrics, CSV loader
behavior, alpha formulas, normalization, factor combination, diagnostics, data
access, execution assumptions, or performance claims. It does not fetch data,
download data, add vendor access, introduce live trading, add brokerage or
order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
209 passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Project Staged Workflow Skill

This research-process milestone added
`.agents/skills/staged-quant-workflow/SKILL.md` so future Codex sessions can
resume the long-running staged workflow without requiring the user to paste a
fresh detailed prompt for every phase.

The Skill records the recurring workflow gates: verify current repo and PR
state, stop at unmerged PR gates, sync latest `main` after a merge, rerun
baseline validation, choose the next stage from current checkpoint evidence,
keep each branch and PR narrowly scoped, open documentation-only or low-risk
checkpoint PRs ready for review, gate code-changing PRs on tests plus read-only
review, and pause after PR creation without merging.

It also preserves the project guardrails: no real data fetching, downloads,
vendor APIs, live trading, brokerage integration, order execution, credentials,
or profitability claims. It records the problem-logging rule that technical,
methodological, environment, testing, workflow, or reasoning problems require a
durable log entry covering the initial mistake, consequence, evidence,
investigation, correction attempts, final fix, validation, remaining caveats,
reflection, and prevention.

This change does not modify source code, tests, strategy logic, feature
calculations, backtester behavior, metrics, generated reports, research scripts,
data access, execution assumptions, or performance claims.

---

## 2026-06-02 - Post-CSV Checkpoint Review

This documentation-only milestone added `docs/post_csv_checkpoint_report.md`
after the CSV interface design, local CSV loader, real-data readiness audit,
LEAN validation mapping, local CSV experiment-log requirements, and CSV loader
missing-value bugfix milestones were merged.

The checkpoint records the current state of the local CSV infrastructure,
baseline validation, read-only guardrail review, stage traceability, remaining
low-severity documentation and roadmap issues, and the recommended next stage:
refreshing the WorldQuant alpha catalog and roadmap status before any new alpha
or data-schema implementation.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, CSV loader behavior, or
synthetic demos. It does not fetch data, download data, add vendor access,
introduce live trading, add brokerage or order-execution logic, store
credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
209 passed

python -m compileall src tests research
passed
```

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

## 2026-06-02 - Local CSV Experiment-Log Requirements

This documentation-only milestone updated `EXPERIMENT_LOG.md` with required
record fields for future user-provided local CSV research runs.

The new section requires local source paths, file hashes or version identifiers,
schemas, validation summaries, provenance, price adjustment policy, universe
rules, feature and signal timing, sample splits, benchmark assumptions, costs,
slippage, limitations, failure modes, and next actions before local CSV results
are interpreted.

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
