# Changelog

All notable repository changes should be recorded here.

This project does not use changelog entries to claim investment performance,
profitability, or trading readiness.

## Unreleased

### Fixed

- Streamlined the public README and workflow diagram, removed unused runtime
  dependencies, completed package metadata, and added lint/build CI gates.
- Replaced the accumulated checkpoint chain with a concise canonical roadmap
  and current handoff aligned to the merged implementation baseline.
- Vectorized capped liquidity-universe ranking while preserving per-date
  selection, missing-ranking counts, and input-column-order tie breaks.
- Aligned candidate volume-aware slippage diagnostics with drift-aware
  portfolio accounting by exposing per-asset trade weights from the backtester
  and accepting those weights through an explicit diagnostic entrypoint. The
  consecutive-target interface remains available as a labeled compatibility
  path. Raw helper impact is labeled as post-return portfolio-value basis and
  converted to beginning-period return basis when explicitly applied.
- Hardened shared numeric panel validation to reject duplicate asset columns
  and positive or negative infinity while continuing to preserve real `NaN`
  missing values, and made strict long-price CSV loading reject sparse
  date-symbol grids created during pivot with the first missing cell identified.
- Corrected simulated portfolio accounting so holdings drift with asset
  returns between scheduled rebalances and turnover is measured against
  drifted pre-trade weights instead of prior targets. Refreshed affected
  synthetic reports and experiment logs under the same research-only caveats.
- Corrected close-time fixed transaction-cost and slippage impacts so
  drift-adjusted turnover is charged against post-return portfolio value, and
  fail explicitly when asset returns plus any trading-cost impact exhaust the
  simulated portfolio.
- Corrected the explicit benchmark `zero_return` fallback so missing benchmark
  dates freeze at the last observed price, including an observation before the
  first strategy date, without discarding the cumulative move when observations
  resume.

### Added

- Added `research/eodhd_limited_factor_diagnostics_brief.py` with a
  private-output-only neutral diagnostics brief runner, plus synthetic tests
  and a docs checkpoint that reports allowed diagnostic direction, magnitude,
  and split consistency without strategy, backtest, portfolio, investment,
  profitability, alpha, or trading-readiness claims.
- Added `research/eodhd_limited_factor_diagnostics_review.py` with a
  private-output-only limited factor diagnostics review runner, plus synthetic
  tests and a docs checkpoint that summarizes allowed diagnostics only without
  strategy, backtest, portfolio, investment, profitability, alpha, or
  trading-readiness interpretation.
- Added `research/eodhd_factor_diagnostics_readiness_review.py` with a
  private-output-only EODHD factor diagnostics readiness review runner, plus
  synthetic tests and a docs checkpoint that records readiness metadata without
  strategy, backtest, portfolio, or performance interpretation.
- Added `research/eodhd_factor_diagnostics_experiment_log.py` with a
  private-output-only EODHD factor diagnostics experiment-log handoff runner,
  plus synthetic tests and a docs checkpoint that records required readiness
  fields without strategy, backtest, portfolio, or performance interpretation.
- Added `research/eodhd_factor_diagnostics_dry_run.py` with a private-output
  EODHD factor diagnostics dry run, plus synthetic tests and a docs checkpoint
  that keeps IC, Rank IC, and quantile-spread diagnostics separate from
  strategy, backtest, portfolio, and performance interpretation.
- Added `docs/eodhd_data_quality_diagnostics_checkpoint.md` to record the
  completed private EODHD no-performance data-quality diagnostics dry run,
  aggregate readiness counts, open caveats, and the next docs-only
  factor-diagnostics planning boundary.
- Added `docs/eodhd_loader_smoke_checkpoint_and_diagnostics_dry_run_plan.md`
  to record the completed private EODHD validation-only loader smoke test,
  aggregate loader/schema evidence, private-output boundary, and the next
  no-performance diagnostics dry-run stop conditions.
- Added `docs/eodhd_local_csv_loader_smoke_test_plan.md` to scope the next
  validation-only loader smoke test for the private EODHD bundle, including
  allowed existing-loader checks, private-output location, stop conditions,
  and caveats before any source, test, report, strategy, or performance work.
- Added `docs/eodhd_local_csv_validation_handoff.md` to record the
  documentation-only handoff for the completed private EODHD local CSV
  validation-only dry run, including aggregate loader/schema evidence,
  static-universe and adjustment-policy caveats, placeholders for sample
  splits and costs/slippage, and the stop-before-strategy next-stage boundary.
- Added `docs/local_csv_validation_dry_run_intake_checklist.md` as a concise
  user-facing intake checklist for local CSV validation-only dry runs before
  Codex inspects user-provided files.
- Added `docs/local_csv_readiness_input_checkpoint.md` to make the required
  user-provided local CSV readiness package explicit before any real-data
  interpretation, while preserving the default pause at the readiness boundary.
- Refreshed the roadmap gap checkpoint after the local fixture configured-case
  output sequence, routing the next default stage to user-provided local CSV
  readiness inputs instead of more synthetic output.
- Refreshed the committed synthetic local fixture Markdown report and JSON
  experiment log with the opt-in configured-case summary, preserving every
  configured case/split row and invalid reason without changing registry
  output.
- Added opt-in local fixture configured-case report/log wiring so the
  committed synthetic fixture workflow can include all-case/all-split summary
  rows in ad hoc outputs without refreshing committed generated artifacts.
- Added protected PR merge governance so non-high-risk PRs authored/pushed by
  `minqiyang` may use GitHub auto-merge or normal protected PR merge only after
  author/head-owner, branch protection, required checks, required reviews, and
  changed-file scope are verified, while direct `main` pushes, protection
  bypass, and `--admin` remain forbidden.
- Added local fixture configured-case summary support with focused tests that
  preserve every configured case/split row, invalid reasons, and separately
  inspectable cost/slippage diagnostic fields without regenerating reports.
- Added paused external PR gate governance so an open or not-verified-merged PR
  is reported once, then treated as an external wait state without repeated
  GitHub checks, gate reports, pause notes, goal completion, or blocked status
  unless the user explicitly resumes, says the PR merged, or asks for PR
  inspection.
- Added `docs/local_fixture_robustness_report_refresh_plan.md` to define the
  documentation gate for applying all-case, split-aware robustness reporting to
  committed synthetic local CSV fixtures before changing fixture workflows or
  generated outputs.
- Added `docs/post_synthetic_robustness_generated_output_checkpoint.md` to
  record the completed synthetic split-aware robustness plan,
  implementation, report/log support, generated-output refresh, and next
  local-fixture robustness planning boundary.
- Added the committed synthetic split-aware robustness Markdown report, JSON
  experiment log, and refreshed experiment registry with all-case and
  invalid-case diagnostics preserved as synthetic-only outputs.
- Added PR-gate governance that pauses after one current-state check when a
  previous-stage PR is not verified merged, avoiding repeated PR polling or
  baseline validation while the gate remains unresolved.
- Added opt-in Markdown report and JSON experiment-log support for the
  synthetic split-aware robustness demo while keeping default module execution
  free of committed generated-output changes.
- Added a deterministic synthetic split-aware robustness demo that reports
  every configured signal case across train, validation, and test splits,
  including invalid diagnostics, without writing generated reports or logs.
- Added `docs/synthetic_robustness_validation_plan.md` to define the
  documentation gate for future synthetic/local-fixture robustness summaries,
  including split policy, all-case reporting, missing-data stop conditions,
  future tests, and future report/log fields before implementation.
- Added `docs/post_precomputed_volume_aware_slippage_checkpoint.md` to record
  the completed volume-aware slippage integration design, test-plan,
  precomputed-impact implementation, and synthetic generated-log refresh
  sequence, and to route the next safe stage toward a documentation-only
  roadmap gap refresh.
- Added an explicit precomputed volume-aware slippage impact path to the local
  backtester, with deterministic tests and separate result, metric, and
  assumption fields while keeping `diagnostic_only` as the default and leaving
  generated reports unchanged.
- Added `docs/volume_aware_slippage_backtester_integration_test_plan.md` to
  define the deterministic unit, integration, failure-mode, guardrail,
  result-field, audit-field, report-field, and experiment-log tests required
  before any future volume-aware slippage backtester implementation.
- Added `docs/volume_aware_slippage_backtester_integration_design.md` to
  define a documentation-only boundary for any future integration of the
  existing volume-aware slippage diagnostic helper into simulated backtester
  accounting, including required inputs, strict stop conditions, reporting
  fields, tests, non-goals, and the next test-plan stage.
- Added `docs/post_local_fixture_slippage_output_refresh_checkpoint.md` to
  record the post-PR #94 generated-output refresh state, keep volume-aware
  slippage diagnostic-only, and route the next safe stage toward a
  documentation-only backtester integration design.
- Added a context-budget and retrieval policy to the long-running controller
  and staged workflow Skill so future continuations start from the handoff and
  repo map, avoid broad parallel reads of long logs/reports, and recover
  safely from truncated tool output. The policy also keeps `current_handoff`
  and `repo_map` as short entry/index files and directs long log and changelog
  access through tail, keyword search, stats, or small snippets by default.
- Refreshed the synthetic local CSV fixture report, JSON experiment log, and
  experiment registry so the generated artifacts include the volume-aware
  slippage smoke diagnostic while preserving the no-backtest and
  no-profitability boundary.
- Added `docs/post_volume_aware_slippage_smoke_checkpoint.md` to record the
  completed volume-aware slippage design/helper/local-fixture smoke sequence
  and route the next safe stage toward synthetic generated-output refresh
  before any backtester integration.
- Added a synthetic local CSV fixture smoke diagnostic that calls the
  volume-aware slippage helper on fixed diagnostic target weights and reports
  participation plus rejected/cap counts without applying slippage to returns
  or changing backtester behavior.
- Added a synthetic-only volume-aware slippage diagnostic helper with
  deterministic tests for lagged rolling dollar volume, explicit notional
  scaling, participation, missing/zero liquidity, and participation caps
  without changing backtester returns or generated reports.
- Added `docs/volume_aware_slippage_design.md` to define a documentation-only
  design gate for future lagged dollar-volume, participation, missing/zero
  volume, notional-scale, cap-policy, and caveat handling before any
  volume-aware slippage implementation.
- Added `docs/current_handoff.md`, `scripts/repo_map.py`, and
  `docs/repo_map.md` workflow controls so future Codex stages can start from a
  concise durable handoff, regenerate a short repo map, and preserve capped
  command-output discipline without weakening safety guardrails.
- Added `docs/post_slippage_cost_checkpoint.md` to record that the fixed-bps
  slippage design, implementation, and synthetic report/log refresh sequence is
  complete, and to route future volume-aware slippage work through a
  documentation-only design gate.
- Refreshed synthetic backtest reports, JSON experiment logs, and the
  experiment registry so fixed-bps transaction cost, fixed-bps slippage,
  zero-slippage diagnostics, and total trading cost impact are explicit after
  the local backtester slippage extension, with related slippage planning docs
  synced to the current implementation state.
- Added a narrow fixed-bps `slippage_bps` extension to the simulated
  backtester, keeping slippage impact separate from transaction-cost impact
  and recording explicit diagnostic assumptions without adding real data,
  broker/order logic, or generated report changes.
- Added `docs/simulated_slippage_cost_assumption_design.md` to define a
  documentation-only boundary for future fixed-bps slippage, transaction cost,
  zero-slippage diagnostics, and deferred market-impact assumptions before any
  backtester implementation changes.
- Added `docs/post_local_csv_fixture_audit_rehearsal_checkpoint.md` to record
  the post-PR #83 local CSV readiness gate state and recommend a
  documentation-only simulated slippage and cost assumption design before any
  cost/slippage implementation.
- Added `docs/local_csv_fixture_readiness_audit_rehearsal.md` to fill the
  local CSV readiness audit report format with committed synthetic fixture
  evidence only, preserving the no-user-data and no-profitability boundary.
- Added `docs/post_local_csv_readiness_gates_checkpoint.md` to record the
  post-readiness-gates local CSV state, remaining stop conditions, and the
  boundary between prepared audit artifacts and any future user-provided local
  CSV smoke run.
- Added `docs/local_csv_readiness_audit_report_template.md` as a
  documentation-only manual audit report format for future user-provided local
  CSV studies, recording evidence, high/medium/low issues, stop conditions,
  and gate decisions before interpretation.
- Added a committed synthetic-fixture inventory dry-run rehearsal to the local
  CSV fixture workflow, recording redacted inventory review summaries before
  loader output is interpreted and keeping the workflow free of real user
  files, downloads, credentials, trading behavior, and profitability claims.
- Added a local CSV inventory dry-run validator that checks declared local
  file metadata before loading user files, keeps raw local paths out of review
  results, and remains free of data fetching, vendor APIs, credentials,
  trading behavior, report generation, and profitability interpretation.
- Added `docs/local_csv_study_checklist.md` as a documentation-only pre-run
  checklist for future user-provided local CSV studies before any user file is
  loaded, diagnosed, reported, or interpreted.
- Added `docs/user_provided_local_csv_research_plan.md` to define a
  documentation-only plan, scope template, validation gates, stop conditions,
  and future PR-sized stages before any user-provided local CSV result is
  interpreted.
- Added `docs/local_csv_readiness_checkpoint.md` to record the post-fixture
  local CSV readiness state, current gaps, guardrails, stop conditions, and
  the next documentation-only user-provided local CSV planning stage.
- Added a synthetic local CSV fixture universe-masked signal smoke check that
  applies the reviewed liquidity universe mask to the existing `alpha_009`
  fixture signal panel, records masked-signal audit counts, and keeps the
  workflow free of backtesting, ranking, target weights, real data, trading
  behavior, or performance interpretation.
- Added a synthetic masked-signal backtest smoke test that feeds
  universe-masked signals into the existing long-only backtester and verifies
  lagged holdings, signal coverage, and transaction-cost accounting without
  changing backtester behavior, generating reports, using real data, or
  interpreting performance.
- Added a synthetic masked-signal smoke test that composes liquidity
  eligibility, liquidity universe construction, and universe-mask signal
  application on deterministic synthetic panels without running a backtest,
  generating reports, using real data, or interpreting performance.
- Added a synthetic/local-panel universe-masked signal adapter that applies an
  already-constructed boolean liquidity universe mask to an already-computed
  factor signal panel with strict alignment, missing-mask rejection, and
  deterministic audit counts, without backtest integration, report generation,
  real data, trading behavior, or performance interpretation.
- Added `docs/liquidity_universe_backtest_integration_design.md` to define a
  documentation-only contract for future signal masking and simulated
  backtest consumption of liquidity universe masks before any source code
  changes.
- Added a synthetic liquidity universe-mask count smoke check to the local CSV
  fixture workflow demo, reusing the committed synthetic OHLCV fixture and
  existing liquidity universe helper without backtest integration,
  tradeability claims, real data, or performance interpretation.
- Added a synthetic/local-panel liquidity universe helper that returns an
  inspectable mask and audit summary without backtesting, report generation,
  real data, or performance interpretation.
- Added `docs/liquidity_universe_construction_design.md` to define a
  documentation-only future liquidity universe-mask API and audit-summary
  boundary before any backtest consumes liquidity eligibility.
- Added `docs/post_alpha012_checkpoint_report.md` to refresh the roadmap after
  Alpha#012 implementation, synthetic OHLCV smoke coverage, and local-fixture
  diagnostics.
- Added Alpha#012 diagnostics to the synthetic local CSV fixture workflow,
  reusing existing IC, Rank IC, and quantile-spread helpers on committed
  fixture data only.
- Added a synthetic OHLCV fixture smoke check that loads the committed local
  fixture and computes `alpha_012` as a feature-only output without reports,
  backtesting, real data, or performance interpretation.
- Added `alpha_012` as a single volume + close WorldQuant-style research
  feature with deterministic formula, alignment, missing-value, zero-volume,
  negative-volume, and no-lookahead tests.
- Added `docs/volume_close_alpha_plan.md` as a documentation-only planning
  gate before any volume + close WorldQuant-style alpha implementation.
- Added a realized volatility research feature that computes trailing standard
  deviation of one-period adjusted-price returns with deterministic
  no-lookahead, full-window, missing-anchor, non-positive-anchor, and
  input-validation tests.
- Added a short-term reversal research feature that computes negative trailing
  returns from adjusted-close panels with deterministic date-alignment,
  missing-anchor, non-positive-anchor, and input-validation tests.
- Added `docs/post_liquidity_checkpoint_report.md` to refresh the roadmap
  after the OHLCV and liquidity eligibility stages and recommend the next
  short-term reversal stage from current evidence.
- Added a synthetic liquidity eligibility count smoke check to the local CSV
  fixture workflow demo, using the committed OHLCV fixture to report lagged ADV
  and dollar-volume eligibility counts without constructing a universe or
  interpreting performance.
- Added synthetic-only liquidity eligibility helpers for rolling average daily
  volume and rolling average dollar volume, with explicit lag, warm-up,
  missing-value, and zero-volume tests.
- Added `docs/liquidity_dollar_volume_universe_plan.md` as a
  documentation-only planning gate for future synthetic liquidity and
  dollar-volume universe eligibility work before any code filters assets by
  volume.
- Added synthetic OHLCV local CSV loader smoke coverage for the committed
  fixture, including summary metadata, strict missing-value policy, and invalid
  OHLC relationship checks without computing a strategy.
- Added a strict local OHLCV long-format CSV loader with committed synthetic
  fixture coverage for raw-string validation, missing-value sentinels,
  duplicate `(date, symbol)` rows, positive OHLC prices, non-negative volume,
  optional `adjusted_close`, and impossible OHLC relationships.
- Added `docs/volume_ohlcv_schema_plan.md` as a documentation-only planning
  gate for future local volume and OHLCV CSV schema support before any
  volume-dependent factor or OHLC-dependent alpha implementation.
- Added split metadata to the synthetic local CSV fixture workflow, including
  train/validation/test coverage, per-split IC / Rank IC / quantile-spread
  diagnostics, and caveated report/log output.
- Added a synthetic split-aware IC / Rank IC diagnostic demo that applies the
  train/validation/test split helper to deterministic synthetic factor and
  forward-return panels without real data, backtesting, or performance claims.
- Added an official root `LICENSE` file for Apache-2.0 public reuse terms.
- Added `CITATION.cff` with repository citation metadata inferred from
  existing GitHub and git author metadata.
- Added `docs/assets/social_preview.svg` as an original source asset for a
  future GitHub social-preview upload.
- Added deterministic train/validation/test date-split helpers for synthetic
  factor research panels, with tests covering chronological boundaries,
  non-overlap, panel slicing, missing-value preservation, and invalid inputs.
- Added `docs/current_roadmap_gap_refresh.md` to reconcile the original gap
  analysis with the current implemented IC / Rank IC, quantile spread, local
  CSV fixture, and LEAN signal-only milestones.
- Added a pure-Python LEAN signal-only momentum draft plus static guardrail
  tests, keeping the draft non-runnable and free of data access, credentials,
  brokerage/order behavior, and profitability claims.
- Added a GitHub Actions `CI` workflow for pull requests to `main` and pushes
  to `main`, running the same pytest and compile checks used locally.
- Added an original `docs/assets/research_workflow.svg` diagram for the public
  README landing page.
- Added `docs/lean_signal_only_draft_design.md` to define a documentation-only
  boundary for a future pure-Python LEAN signal-only draft before any runnable
  LEAN code, data access, credentials, brokerage/order behavior, or performance
  interpretation is introduced.
- Added `docs/lean_runnable_draft_readiness_decision.md` to record that the
  project is not yet ready for a runnable LEAN draft under the current
  guardrails and should next design a signal-only draft boundary.
- Added `docs/lean_scaffold_review_checklist.md` to define review questions,
  static checks, safe expansion criteria, and stop conditions before any future
  runnable LEAN draft.
- Added a minimal non-executing LEAN smoke-test scaffold with static guardrail
  tests, without adding a runnable LEAN project, external data access,
  credentials, live or paper trading, brokerage integration, order execution,
  or profitability claims.
- Added `docs/lean_implementation_planning_checkpoint.md` to choose the exact
  future first LEAN code-PR boundary, validation strategy, review gates, and
  stop conditions before adding any LEAN scaffold or algorithm code.
- Added `docs/lean_smoke_test_design.md` to turn the LEAN parity checklist into
  a documentation-only smoke-test design before any LEAN implementation or
  project scaffold.
- Added `docs/lean_parity_checklist.md` to map local factor, diagnostics,
  benchmark, fee, slippage, and experiment-log requirements to future
  QuantConnect/LEAN smoke-test assertions before any LEAN algorithm code.
- Added a local CSV fixture workflow demo that loads committed synthetic CSV
  fixtures, computes `alpha_009` as a research feature, runs IC / Rank IC /
  quantile spread diagnostics, and writes caveated synthetic report/log
  artifacts.
- Added `docs/codex_long_running_controller.md` to define startup checks,
  merge gates, stage selection, stop conditions, logging requirements, and PR
  pause behavior for long-running Codex workflow.
- Added `docs/decision_log.md` for durable workflow, architecture, and
  research-process decisions.
- Added `docs/troubleshooting_log.md` for failures, missing prerequisites,
  correction attempts, verification, caveats, and prevention notes.
- Added `scripts/audit-skills.ps1` for local structural audits of repository
  Skill files.

### Changed

- Refreshed `docs/current_roadmap_gap_refresh.md` after the completed split,
  liquidity, fixed-bps slippage, volume-aware diagnostic,
  precomputed-impact, generated-log, and checkpoint stages, and routed the
  next safe stage toward a documentation-only synthetic robustness and
  split-aware validation plan.
- Refreshed the synthetic momentum and synthetic combined-score JSON
  experiment logs so their deterministic metrics payloads include the default
  `total_volume_aware_slippage_cost_impact` field after the precomputed
  volume-aware slippage backtester path, with the value remaining `0.0` in
  diagnostic-only mode.
- Updated the liquidity universe plan and decision log to separate liquidity
  eligibility, universe-mask construction, and backtest consumption into
  distinct reviewed stages.
- Refreshed the QuantConnect/LEAN plan and parity checklist for Alpha#012
  signal mapping, keeping the LEAN path documentation-only, non-runnable, and
  free of data subscriptions, credentials, brokerage/order behavior, and
  performance interpretation.
- Updated the Alpha#012 and WorldQuant roadmap docs to mark the completed
  Alpha#012 fixture diagnostics stage and recommend a LEAN plan refresh before
  any Alpha#012 LEAN mapping work.
- Updated the OHLCV schema plan and WorldQuant alpha catalog to route future
  volume-based universe work through the liquidity and dollar-volume planning
  gate before implementation.
- Updated the CSV interface plan and WorldQuant alpha catalog to reference the
  volume/OHLCV schema planning gate before future volume or OHLC-dependent
  implementation work.
- Updated the README license badge and current-status language to link to the
  Apache-2.0 license and remove obsolete license follow-up wording.
- Replaced the static README local-test status label with a live GitHub Actions
  CI badge for `.github/workflows/ci.yml`.
- Polished `README.md` as a public GitHub landing page with truthful status
  labels, beginner Quick Start commands, demo walkthrough links, a project map,
  key report links, and explicit no-live-trading scope language.
- Refreshed `docs/quantconnect_lean_plan.md` to reflect the current local CSV
  loader, synthetic local CSV workflow, IC / Rank IC diagnostics, quantile
  spread diagnostics, and experiment-registry state before any LEAN code.
- Refreshed `docs/worldquant_alpha_catalog.md` to distinguish current
  `alpha_009` research-feature status from the original catalog-only milestone
  and to restate data prerequisites for future WorldQuant-style alpha stages.
- Updated the long-running controller and staged workflow Skill with bounded
  execution behavior, low-risk ambiguity handling, missing-file recovery rules,
  and expanded stop conditions.
- Updated `.agents/skills/staged-quant-workflow/SKILL.md` to reference the
  long-running controller and Skill audit script.
