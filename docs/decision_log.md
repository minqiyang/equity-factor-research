# Decision Log

This log records durable workflow, architecture, and research-process decisions
for the simulated equity factor research project.

It is not an experiment log and must not be used to claim profitability or
investment performance.

## How To Update This Log

- Add a dated entry for decisions that future Codex sessions should preserve.
- State the context, decision, rationale, consequences, and follow-up.
- Keep entries factual and separate observed evidence from assumptions.
- Link or name the relevant files, branches, PRs, checks, or logs when useful.

---

## 2026-06-11 - Add Precomputed Volume-Aware Slippage Backtester Boundary

Context:

- PR #99 added the documentation-only test plan for volume-aware slippage
  backtester integration.
- The reviewed design and test plan both recommend keeping helper calculation
  outside the backtester and using a precomputed impact boundary for the first
  implementation.

Decision:

- Add a narrow `apply_precomputed_impact` path to `run_long_only_backtest()`.
- Keep `volume_aware_slippage_mode="diagnostic_only"` as the default.
- Add a separate `volume_aware_slippage_costs` result series, separate metrics,
  and explicit assumption fields for applied volume-aware slippage metadata.
- Reject positive fixed-bps slippage plus positive applied volume-aware impact
  by default to avoid hidden double counting.
- Do not make the backtester compute rolling dollar volume, read OHLCV panels,
  fetch data, use vendor APIs, connect to brokers, or place orders.

Rationale:

- A precomputed series keeps date alignment, notional scale, volume policy,
  missing/zero/stale liquidity policy, and participation-cap handling in the
  diagnostic helper boundary.
- Separate result and metric fields keep fixed transaction costs, fixed-bps
  slippage, volume-aware candidate slippage, and total trading impact
  inspectable.
- The default diagnostic mode preserves existing behavior unless callers
  explicitly opt into applied precomputed impact with required metadata.

Consequences:

- Future generated reports and experiment logs may need a separate refresh or
  review stage so new metrics and audit fields are visible and caveated.
- User-provided local CSV interpretation remains blocked by readiness-audit,
  provenance, alignment, and experiment-handoff gates.

Follow-up:

- After this implementation PR merges, review and refresh affected synthetic
  generated outputs in a separate PR if the diff confirms new default fields.

---

## 2026-06-11 - Require Tests Before Volume-Aware Slippage Backtester Implementation

Context:

- PR #98 added the documentation-only backtester integration design for
  volume-aware slippage.
- The design recommends keeping `diagnostic_only` as default and using a
  precomputed-impact boundary if volume-aware slippage is later applied to
  simulated returns.
- No source code, tests, research scripts, generated reports, backtester
  behavior, metrics behavior, or diagnostics behavior changed in this stage.

Decision:

- Add `docs/volume_aware_slippage_backtester_integration_test_plan.md` as the
  acceptance checklist before any implementation.
- Require deterministic unit, integration, failure-mode, guardrail, result
  field, audit field, report-field, and experiment-log tests before or with any
  future code-changing integration PR.
- Keep generated reports unchanged until after a future implementation is
  reviewed and merged.

Rationale:

- Applying volume-aware slippage to net returns is an accounting change, not a
  documentation detail.
- Tests must prove date alignment, separate cost/slippage inspection, zero
  diagnostic behavior, invalid-liquidity failures, and no double counting
  before behavior changes.
- A test plan keeps the next implementation PR smaller and less ambiguous.

Consequences:

- The next possible implementation must keep helper calculation outside the
  backtester, keep `diagnostic_only` as default, and add deterministic tests in
  the same PR.
- Implementation must stop for missing, zero, stale, or incomplete volume
  ambiguity; invalid notional; excessive participation; ambiguous fixed-bps
  plus volume-aware slippage semantics; real-data needs; vendor APIs;
  credentials; brokerage; live or paper trading; order execution; or
  profitability language.

Follow-up:

- After this test-plan PR merges, consider a narrow code-changing
  precomputed-impact implementation PR with deterministic tests and no
  generated-output refresh.

---

## 2026-06-11 - Define Volume-Aware Slippage Backtester Integration Boundary

Context:

- PR #97 merged the post local fixture slippage output refresh checkpoint.
- The repository has a standalone volume-aware slippage diagnostic helper and
  synthetic/local-fixture outputs that report participation and rejected/cap
  counts.
- Candidate volume-aware slippage is still not applied to simulated backtester
  net returns.

Decision:

- Add `docs/volume_aware_slippage_backtester_integration_design.md` as the
  reviewed boundary before any future net-return integration.
- Keep volume-aware slippage diagnostic-only by default.
- If implemented later, prefer a precomputed-impact boundary: compute the
  diagnostic outside the backtester, pass an aligned
  `portfolio_slippage_impact` series plus audit metadata into the backtester or
  wrapper, and deduct it from net returns only under an explicit opt-in.
- Defer internal backtester calculation from price and volume panels until a
  separate design justifies making the backtester own OHLCV semantics.

Rationale:

- Applying volume-aware slippage to returns would change cost accounting and
  report interpretation.
- A precomputed-impact boundary keeps volume validation, notional scale, lagged
  dollar-volume construction, stale-volume handling, and participation caps
  auditable before net-return behavior changes.
- Fixed-bps slippage and volume-aware candidate slippage can be double-counted
  unless a reviewed rule blocks or explicitly permits combination.

Consequences:

- Source code, tests, research scripts, generated reports, loaders, backtester
  behavior, metrics behavior, diagnostics behavior, LEAN code, and real-data
  access remain unchanged in this stage.
- Any future implementation must define strict defaults and stop conditions for
  missing volume, zero volume, stale volume, invalid notional, and excessive
  participation before touching returns.
- Reports and experiment logs must distinguish transaction costs, fixed-bps
  slippage, volume-aware candidate slippage, total trading impact, diagnostic
  flags, and caveats.

Follow-up:

- After this design merges, the next safe stage is a documentation-only
  backtester integration test plan, not implementation.
- Stop if a later stage needs real data, downloads, vendor APIs, credentials,
  brokerage, live or paper trading, order execution, silent missing-data repair,
  or profitability claims.

---

## 2026-06-11 - Require Design Before Volume-Aware Slippage Net-Return Integration

Context:

- PR #90 added the volume-aware slippage design boundary.
- PR #91 added the standalone synthetic-only diagnostic helper.
- PR #92 added a committed synthetic local CSV fixture smoke diagnostic.
- PR #93 checkpointed the smoke diagnostic before generated-output refresh.
- PR #94 refreshed the committed synthetic local CSV fixture report, JSON
  experiment log, and experiment registry with the diagnostic outputs.
- None of those stages applied candidate volume-aware slippage to simulated
  portfolio returns.

Decision:

- Treat the volume-aware slippage design/helper/smoke/output-refresh sequence
  as complete at the diagnostic artifact level.
- Require a separate documentation-only integration design before any future
  stage changes `run_long_only_backtest()`, metrics, reports, or generated
  logs so volume-aware slippage affects simulated net returns.

Rationale:

- Net-return accounting needs explicit semantics for gross returns, fixed
  transaction costs, fixed-bps slippage, candidate volume-aware slippage,
  rejected/capped trades, zero-slippage diagnostics, and caveats.
- A design gate is lower risk than implementation and keeps the next PR
  reviewable.
- Synthetic/local fixture diagnostics are useful for plumbing and audit
  visibility, but they are not real-data evidence or profitability support.

Consequences:

- The next safe stage after the checkpoint can be a documentation-only
  volume-aware slippage backtester integration design.
- Source code, tests, research scripts, generated reports, and backtester
  behavior should remain unchanged until that design is reviewed.
- User-provided local CSV interpretation remains blocked by readiness-audit,
  provenance, schema, alignment, and experiment-handoff gates.

Follow-up:

- Draft `docs/volume_aware_slippage_backtester_integration_design.md` in a
  later PR after the checkpoint merges.
- Stop if the design would require real data, downloads, vendor APIs,
  credentials, live or paper trading, brokerage integration, order execution,
  silent missing-data repair, or profitability claims.

---

## 2026-06-09 - Refresh Local Fixture Outputs Before Backtester Slippage Integration

Context:

- PR #90 added the volume-aware slippage design boundary.
- PR #91 added the standalone synthetic-only diagnostic helper.
- PR #92 added a committed synthetic local CSV fixture smoke diagnostic that
  calls the helper and reports participation plus rejected/cap counts only.
- PR #92 intentionally did not refresh committed generated reports/logs and
  did not integrate volume-aware slippage into backtester net returns.

Decision:

- Treat the volume-aware design, helper, and local fixture smoke diagnostic
  sequence as complete at the code/test level.
- Before considering any backtester net-return integration, refresh the
  committed synthetic local CSV fixture generated report/log/registry in a
  separate narrow stage if the checkpoint is reviewed and merged.
- Keep any generated-output refresh synthetic-only and caveated. It may record
  participation and rejected/cap counts, but it must not treat candidate
  slippage diagnostics as real-data evidence, execution realism, or
  profitability support.

Rationale:

- The repository should not carry stale generated artifacts after a workflow
  report/log writer changes.
- Generated-output refresh is lower risk than backtester integration because
  it does not change source behavior or net returns.
- Separating artifact refresh from code changes keeps PR scope reviewable and
  prevents generated report diffs from hiding implementation changes.

Consequences:

- The next safe stage after the checkpoint can be a local fixture generated
  artifact refresh, not a new alpha, real-data study, or backtester slippage
  integration.
- Volume-aware slippage remains diagnostic-only until a later design stage
  explicitly reviews whether it should affect simulated returns.
- User-provided local CSV interpretation remains blocked by readiness-audit
  and `EXPERIMENT_LOG.md` gates.

Follow-up:

- Refresh `reports/local_csv_fixture_workflow_demo.md`,
  `reports/experiment_logs/local_csv_fixture_workflow_demo.json`, and
  `reports/experiment_registry.md` in a separate stage after this checkpoint
  merges.
- Stop if the refresh would require real data, downloads, vendor APIs,
  credentials, live or paper trading, brokerage integration, order execution,
  backtester behavior changes, or profitability claims.

---

## 2026-06-09 - Keep Volume-Aware Slippage Helper Diagnostic-Only

Context:

- PR #90 added `docs/volume_aware_slippage_design.md`.
- That design recommends a synthetic-only helper or diagnostic stage before
  any backtester net-return integration.
- The current backtester already has fixed-bps slippage, so adding a
  volume-aware path directly to `run_long_only_backtest()` would change
  strategy accounting before the new data and capacity semantics are
  independently tested.

Decision:

- Add a standalone diagnostic helper under `src/backtest/slippage.py`.
- Do not integrate the helper with `run_long_only_backtest()`,
  `calculate_basic_metrics()`, research scripts, generated reports, or local
  CSV workflows in this stage.
- Default to strict behavior: missing lagged capacity, zero or incomplete
  volume windows, zero lagged dollar volume, missing inputs, invalid notional,
  and participation above cap raise instead of being filled, clipped, or
  ignored.

Rationale:

- A standalone helper keeps the PR reviewable and makes the volume-aware
  assumptions testable before they affect simulated returns.
- Explicit `portfolio_notional` prevents normalized backtest capital from
  being mistaken for real tradable capital.
- Strict missing and zero-liquidity behavior preserves the project rule
  against silent missing-data repair.

Consequences:

- Future work can inspect participation and candidate slippage impact on
  deterministic synthetic panels without changing existing backtest output.
- Backtester integration remains a separate reviewed decision after helper
  behavior and caveats are accepted.
- User-provided local CSV interpretation remains blocked by readiness-audit
  and `EXPERIMENT_LOG.md` gates.

Follow-up:

- After this helper is reviewed and merged, consider a synthetic/local-fixture
  smoke diagnostic that reports participation and rejected/capped counts only.
- Stop if the next stage would require real data, downloads, vendor APIs,
  credentials, live or paper trading, brokerage integration, order execution,
  silent fill/clip policies, generated performance interpretation, or
  profitability claims.

---

## 2026-06-09 - Define Volume-Aware Slippage Design Boundary

Context:

- PR #85 designed fixed-bps transaction cost and slippage assumptions.
- PR #86 implemented fixed-bps slippage in the local backtester.
- PR #87 refreshed synthetic reports and logs for fixed-bps slippage fields.
- PR #88 recorded that the fixed-bps slippage path is complete and that
  volume-aware slippage requires a design gate before implementation.
- PR #89 added token-efficient workflow controls, so the current stage can use
  the handoff and repo map instead of broad repo scans.

Decision:

- Add `docs/volume_aware_slippage_design.md` as a documentation-only boundary
  before any volume-aware slippage helper, backtester integration,
  generated-output update, or local CSV interpretation.
- Treat lagged rolling dollar volume, explicit portfolio notional,
  missing/zero-volume handling, participation caps, and adjustment-policy
  compatibility as required design inputs for any future code.
- Keep same-day volume, silent missing-data repair, silent cap clipping, real
  data fetching, broker/order behavior, and execution-realism claims out of
  scope.

Rationale:

- Volume-aware slippage has higher look-ahead and interpretation risk than
  fixed-bps target-weight turnover friction.
- Current backtests are normalized research accounting; dollar-volume
  capacity requires an explicit notional scale before participation can be
  calculated.
- Zero volume, missing volume, stale volume, and incompatible price/volume
  adjustment policies can make a volume-aware estimate invalid even when the
  CSV loader accepts the rows.

Consequences:

- The next possible code stage should be a synthetic-only helper or diagnostic
  stage, not immediate backtester net-return integration.
- Any future implementation must default to strict missing/zero-liquidity and
  participation-cap behavior, with no silent fills or silent clipping.
- User-provided local CSV interpretation remains blocked until readiness audit
  and `EXPERIMENT_LOG.md` gates are complete for a specific dataset.

Follow-up:

- After this design is reviewed and merged, consider a narrow synthetic-only
  participation/slippage diagnostic helper with deterministic tests.
- Stop if implementation would require real data, downloads, vendor APIs,
  credentials, live or paper trading, brokerage integration, order execution,
  silent missing-data repair, or profitability claims.

---

## 2026-06-09 - Require Volume-Aware Slippage Design Before Implementation

Context:

- PR #85 added the simulated slippage and cost assumption design.
- PR #86 implemented the narrow fixed-bps local backtester slippage extension.
- PR #87 refreshed synthetic backtest reports, JSON logs, registry output, and
  current slippage planning docs.
- The fixed-bps path is now represented in design, code, deterministic tests,
  and synthetic generated outputs.
- Volume-aware slippage and market impact remain deferred.

Decision:

- Treat the fixed-bps slippage sequence as complete for the current synthetic
  research pipeline.
- Do not proceed directly to a volume-aware slippage helper or backtester
  extension.
- Require a documentation-only volume-aware slippage design before any
  volume-based cost/slippage implementation, generated-output update, or
  local CSV interpretation.

Rationale:

- Volume-aware slippage has higher leakage and interpretation risk than fixed
  basis-point turnover friction.
- A future model would need explicit policy for adjusted versus raw volume,
  dollar-volume alignment, lag rules, zero volume, missing volume, stale data,
  participation assumptions, liquidity caps, and benchmark/universe mismatch.
- Synthetic/local fixtures can test wiring and edge cases, but they cannot
  prove realistic execution or market impact.

Consequences:

- The next safe repository-internal stage can be a design gate for
  volume-aware slippage.
- Any future implementation must remain synthetic/local-fixture only until
  user-provided local CSV readiness gates are completed for a specific dataset.
- User-provided local CSV interpretation remains blocked by the readiness
  audit and `EXPERIMENT_LOG.md` requirements.
- No source code, tests, research scripts, reports, data access, execution
  behavior, credentials, or performance claims are changed by this decision.

Follow-up:

- Add a documentation-only volume-aware slippage design if no higher-priority
  merge gate, blocker, or stale roadmap issue appears.
- Stop before implementation if the next stage would require real data,
  downloads, vendor APIs, credentials, live or paper trading, brokerage
  integration, order execution, or profitability claims.

---

## 2026-06-09 - Require Slippage And Cost Design Before Implementation

Context:

- PR #84 merged the post-local-CSV-fixture audit rehearsal checkpoint.
- That checkpoint recommends simulated slippage and cost assumption design as
  the next repository-internal stage.
- The local backtester currently applies `transaction_cost_bps` to
  target-weight turnover, but it does not separately represent slippage or
  market impact.
- The project specification requires transaction costs, slippage, turnover,
  and execution assumptions to be explicit.

Decision:

- Add a documentation-only design before any local backtester cost/slippage
  implementation changes.
- Treat the first future implementation, if approved later, as a narrow fixed
  basis-point slippage extension on the current target-weight turnover model.
- Defer volume-aware slippage and market impact until separate policy, data,
  lag, and testing requirements are reviewed.

Rationale:

- Cost and slippage assumptions can materially affect simulated results.
- A design gate prevents a small-looking parameter addition from becoming an
  implicit execution model.
- Fixed-basis-point turnover friction is deterministic and testable, but it
  must remain caveated as simulated research accounting rather than realistic
  execution evidence.

Consequences:

- Backtester source code remains unchanged by this decision.
- Future code must keep transaction cost and slippage assumptions visible in
  outputs and logs.
- Zero-cost or no-slippage runs remain diagnostics only.
- User-provided local CSV interpretation remains blocked by the readiness
  audit and experiment-log gates.

Follow-up:

- After the design is reviewed and merged, consider a narrow synthetic-only
  implementation PR with deterministic tests for separate fixed-bps slippage.
- Stop before implementation if the next stage would require real data,
  broker fills, order execution, credential access, or performance
  interpretation.

---

## 2026-06-08 - Pause User-Provided Local CSV Work At The Readiness Gate

Context:

- PR #83 merged the committed synthetic local CSV fixture readiness audit
  rehearsal.
- The repository now has the future local CSV study plan, checklist, inventory
  validator, audit report template, and synthetic fixture rehearsal artifacts.
- No user-provided local CSV bundle, completed scope statement, completed
  checklist, completed inventory review, completed readiness audit report, or
  prepared user-data `EXPERIMENT_LOG.md` entry is available.
- Starting a user-data smoke run would require external files and human review
  decisions that are not present in the repository context.

Decision:

- Do not proceed to a user-provided local CSV smoke run by default.
- Treat local CSV user-data interpretation as blocked until the required
  bundle, checklist, inventory, readiness audit, and experiment-log gates are
  complete.
- Route the next repository-internal stage toward simulated slippage and cost
  assumption design before any cost/slippage implementation changes.

Rationale:

- The local CSV readiness artifacts are preparation gates, not evidence that a
  specific user dataset is safe to interpret.
- The original project specification requires explicit transaction costs,
  slippage, turnover, and execution assumptions.
- The current backtester has fixed basis-point transaction costs but no
  separate slippage or market-impact model; a design gate keeps that boundary
  reviewable before source code changes.

Consequences:

- Local CSV work remains synthetic, local-fixture only, or documentation-only
  until user data and completed audit artifacts are available.
- The next stage should not fetch data, add vendor APIs, add credentials, add
  live or paper trading, add brokerage/order logic, or claim profitability.
- Backtester source code remains unchanged by this decision.

Follow-up:

- Add a documentation-only simulated slippage and cost assumption design stage.
- Stop before implementation if the design would require real market data,
  broker fills, order execution, or performance interpretation.

---

## 2026-06-07 - Require Universe-Mask Backtest Integration Design Before Code

Context:

- The synthetic liquidity universe helper has merged.
- The local CSV fixture workflow now reports universe-mask counts on committed
  synthetic fixtures only.
- `run_long_only_backtest()` currently consumes prices and signals, not
  universe masks.
- Feeding a universe mask directly into a backtest without a reviewed contract
  could blur universe dates, signal dates, rebalance dates, return measurement
  dates, low-coverage handling, benchmark assumptions, and performance
  interpretation.

Decision:

- Add a documentation-only liquidity universe backtest-integration design
  before any source code consumes a liquidity universe mask in the backtester.
- Treat the likely first implementation as a narrow signal-masking adapter,
  not a broad backtester rewrite.
- Require strict signal/mask alignment, explicit timing, visible low-coverage
  and empty-rebalance summaries, and caveated synthetic-only interpretation.

Rationale:

- The project already has the lower-level universe-mask primitive.
- The next correctness risk is not mask construction; it is unsafe consumption
  of the mask in simulated portfolio research.
- A design gate keeps universe construction, signal masking, portfolio
  selection, costs, slippage, benchmark comparison, and execution timing
  reviewable as separate concerns.

Consequences:

- Backtester source code remains unchanged in this stage.
- Future code should mask signals before ranking and should not silently
  repair missing universe or signal values.
- Future synthetic backtests that consume a universe mask must record universe
  parameters, coverage, low-coverage dates, timing assumptions, and caveats.
- Real user-provided local CSV interpretation remains blocked by the
  real-data readiness audit and experiment-log requirements.

Follow-up:

- After the design is reviewed and merged, the next narrow code stage can add
  a deterministic synthetic `apply_universe_mask_to_signals()` adapter and
  tests, without running a backtest if keeping the PR narrower is safer.

---

## 2026-06-07 - Keep Liquidity Universe Construction Separate From Backtesting

Context:

- The repository has synthetic-only rolling ADV and rolling dollar-volume
  eligibility helpers.
- The committed synthetic local CSV fixture workflow reports liquidity
  eligibility counts.
- No reviewed helper yet defines a final universe mask, an audit summary, or
  how such a mask should interact with factor scores, rebalance schedules,
  costs, slippage, benchmarks, or execution assumptions.
- The active workflow still prohibits real data fetching, downloads,
  credentials, live trading, paper trading, brokerage integration, order
  execution, and profitability claims.

Decision:

- Treat liquidity eligibility, final universe mask construction, and backtest
  consumption as separate stages.
- Add a documentation-only universe construction design before any code uses
  liquidity eligibility as a final research universe mask.
- Do not wire liquidity eligibility directly into the backtester until a later
  reviewed stage defines the universe mask API, audit summary, signal timing,
  rebalance timing, execution assumptions, costs, slippage, and benchmark
  interaction.

Rationale:

- Liquidity filters are a major survivorship-bias and look-ahead-bias risk if
  they are connected directly to portfolio construction without a reviewed
  timing boundary.
- A universe mask needs its own audit summary so low coverage, missing
  eligibility, capped names, additions, removals, and caveats remain visible.
- Keeping the stages separate preserves progress while preventing a liquidity
  helper from being mistaken for a tradable universe or performance result.

Consequences:

- Future liquidity universe code should be synthetic-only and should return a
  mask plus inspectable summary before any report or backtest integration.
- Backtester integration remains blocked until a separate design defines the
  complete signal/universe/rebalance/execution contract.
- User-provided local CSV universe interpretation remains gated by the
  real-data readiness audit and experiment-log requirements.

Follow-up:

- Implement a small synthetic-only universe-mask helper and deterministic tests
  only after `docs/liquidity_universe_construction_design.md` is reviewed and
  merged.

---

## 2026-06-04 - Keep First LEAN-Adjacent Code Signal-Only

Context:

- PR #42 merged the LEAN runnable draft readiness decision.
- That decision found the repository is not ready for runnable LEAN code under
  the current guardrails.
- The active workflow still prohibits real market data fetching, downloads,
  credentials, live trading, paper trading, brokerage integration, order
  execution, and profitability claims.

Decision:

- Define the next LEAN-adjacent code boundary as signal-only and
  metadata-only.
- Do not allow the next code stage to import `AlgorithmImports`, subclass
  `QCAlgorithm`, create `config.json`, run LEAN, subscribe to platform data,
  call history APIs, create portfolio targets, place orders, model fills,
  configure brokerage, or produce backtest results.
- If this design is reviewed and merged, the next possible code PR should be a
  pure-Python `lean/signal_only_momentum_draft.py` plus static scope tests.

Rationale:

- A signal-only draft can make the factor translation boundary auditable
  without introducing runtime dependencies, account access, data-source
  semantics, order semantics, or performance interpretation.
- Keeping the first code step metadata-only preserves forward progress while
  maintaining the existing simulated-research guardrails.

Consequences:

- Runnable LEAN code remains intentionally blocked.
- The future signal-only draft must avoid order dates, target weights,
  brokerage models, fill models, live mode, paper mode, and implemented
  portfolio behavior.
- Static tests should continue to reject data downloads, credential reads,
  runtime LEAN imports, order calls, and profitability or trading-readiness
  claims.

Follow-up:

- After this design is reviewed and merged, create a small code PR for a
  pure-Python LEAN signal-only momentum draft with static guardrail tests, or
  stop if the implementation cannot satisfy the documented boundary.

---

## 2026-06-04 - Defer Runnable LEAN Draft Until Signal-Only Boundary Is Designed

Context:

- PR #41 merged the LEAN scaffold review checklist.
- The repository now has a metadata-only LEAN scaffold and static tests that
  intentionally reject runtime LEAN imports, credential/data imports,
  brokerage calls, and order calls in the scaffold.
- The current workflow guardrails still prohibit real market data fetching,
  downloads, credentials, live trading, paper trading, brokerage integration,
  order execution, and profitability claims.

Decision:

- Do not add a runnable LEAN draft in the next stage.
- Add a readiness decision documenting that runnable LEAN code is not yet
  approved under current guardrails.
- Make the next safe LEAN stage a documentation-only signal-only draft design.

Rationale:

- A normal runnable LEAN algorithm would likely use `AlgorithmImports`,
  `QCAlgorithm`, platform data subscriptions or history, scheduled events,
  portfolio targets, orders, fills, fee models, and slippage models.
- Those pieces may be appropriate in a future simulated LEAN backtest, but they
  need an explicit scope boundary before implementation so they are not
  confused with live trading, brokerage integration, real data fetching, or
  profitability evidence.
- The signal-only design stage can preserve forward progress while keeping the
  implementation bounded and reviewable.

Consequences:

- Future LEAN code remains blocked until the project defines a signal-only
  code boundary and static validation plan.
- The existing non-executing scaffold remains unchanged.
- No source code, tests, research scripts, reports, data access, execution
  behavior, credentials, or performance claims are changed by this decision.

Follow-up:

- Create a documentation-only LEAN signal-only draft design after this decision
  is reviewed and merged.
- If that design cannot avoid runtime, data, credential, order, or
  interpretation risks, stop and document the blocker before code is added.

---

## 2026-06-03 - Refresh WorldQuant Catalog Before More Alpha Work

Context:

- `docs/post_csv_checkpoint_report.md` identified stale wording in
  `docs/worldquant_alpha_catalog.md`.
- The catalog still described the repository as catalog-only even though the
  operator layer and `alpha_009` research feature now exist.
- PR #29 was merged, latest `main` was synced, baseline validation passed, and
  no open pull request gate remained.
- Assumption: refreshing the catalog is the next unblocked safe stage because
  it is documentation-only and directly addresses the latest checkpoint
  recommendation.

Decision:

- Refresh `docs/worldquant_alpha_catalog.md` before implementing another
  formula or expanding data schemas.
- Treat `alpha_009` as implemented research-feature status only, not a full
  strategy, backtest integration, trading recommendation, or profitability
  claim.
- Keep `alpha_012` blocked on volume plus close support and `alpha_101`
  blocked on OHLC support.
- Keep VWAP, market-cap, and industry-neutral categories deferred until the
  required data support and validation rules exist.

Rationale:

- Roadmap documents should not guide future stages from stale pre-`alpha_009`
  assumptions.
- Documentation cleanup is lower risk than starting another formula while the
  data prerequisites and next-stage options are still being clarified.
- The project should continue to avoid bulk WorldQuant 101 implementation.

Consequences:

- Future alpha stages should start from current implementation status rather
  than the original Stage 1 catalog-only milestone.
- Additional formula work should be PR-sized and preceded by explicit formula,
  data, operator, missing-value, and test scope.
- This decision changes documentation only. It does not modify source code,
  data access, strategy logic, backtester behavior, execution assumptions, or
  performance claims.

Follow-up:

- If the next alpha stage is code-changing, run the stricter code PR readiness
  gate: tests plus read-only review with no high or medium issues.
- Consider a future planning stage for volume + close or OHLC schema support
  before `alpha_012` or `alpha_101`.

---

## 2026-06-03 - Bounded Staged Execution Behavior

Context:

- The staged workflow now has a repository-local Skill and long-running
  controller.
- The user clarified that Codex should continue as a bounded staged execution
  agent and should not ask for a new prompt after every small step.
- Assumption: this clarification should be preserved as workflow-control
  documentation and Skill guidance, not treated as a source-code or product
  behavior change.

Decision:

- Add an explicit low-risk ambiguity policy to
  `docs/codex_long_running_controller.md`.
- Expand controller stop conditions to cover dirty working trees before new
  stages, destructive or broad architecture ambiguity, missing credentials or
  external access, new production dependencies, unsafe test failures,
  high/medium review issues, security/privacy/data-loss/irreversible risks,
  scope conflicts, and PR-ready human review gates.
- Update `.agents/skills/staged-quant-workflow/SKILL.md` so future sessions
  continue through low-risk ambiguity with logged assumptions and treat missing
  expected files as workflow scaffolding only when that is low-risk.

Rationale:

- The project needs forward motion without turning every minor ambiguity into a
  user prompt.
- The same behavior must remain bounded by safety, scope, review, and merge
  gates.
- Missing workflow files can be repaired safely in small process PRs, while
  missing product-behavior artifacts require a stop report.

Consequences:

- Future Codex sessions should continue through minor documentation/workflow
  ambiguities after recording assumptions.
- Future sessions must still stop for the defined safety, scope, review, and
  human approval conditions.
- This decision changes process guidance only. It does not modify source code,
  data access, trading behavior, strategy logic, or performance claims.

Follow-up:

- Keep each behavior update PR-sized.
- If this policy causes overreach, record the failure in
  `docs/troubleshooting_log.md` and tighten the stop conditions.

---

## 2026-06-03 - Add Long-Running Workflow Control Artifacts

Context:

- The staged workflow Skill exists at
  `.agents/skills/staged-quant-workflow/SKILL.md`.
- The user requested continuation based on `docs/codex_long_running_controller.md`,
  `docs/decision_log.md`, `docs/troubleshooting_log.md`, `CHANGELOG.md`, and
  `scripts/audit-skills.ps1`.
- On latest `main`, those controller, log, changelog, and audit script files
  were missing.

Decision:

- Add a repository-local long-running controller document.
- Add durable decision and troubleshooting logs.
- Add a changelog.
- Add a local PowerShell Skill audit script.
- Update the staged workflow Skill so future continuations read the controller
  and can run the Skill audit.

Rationale:

- The project now depends on a recurring staged workflow, not a one-off prompt.
- Missing controller and log files make future continuation ambiguous.
- A local Skill audit gives future sessions a deterministic check before
  relying on project Skills.

Consequences:

- Future Codex sessions have explicit startup, stop-condition, logging, and PR
  gate guidance.
- Workflow-control changes remain separate from factor research implementation.
- The repository gains process infrastructure but no source-code, data-access,
  strategy, backtest, or performance-claim changes.

Follow-up:

- Keep the controller concise and update it only when a reusable workflow rule
  is verified.
- Use `docs/troubleshooting_log.md` for detailed failure chains.
- Continue normal staged PR review and do not merge PRs without explicit user
  instruction.
