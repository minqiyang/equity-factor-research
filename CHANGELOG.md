# Changelog

All notable repository changes should be recorded here.

This project does not use changelog entries to claim investment performance,
profitability, or trading readiness.

## Unreleased

### Added

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
