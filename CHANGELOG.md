# Changelog

All notable repository changes should be recorded here.

This project does not use changelog entries to claim investment performance,
profitability, or trading readiness.

## Unreleased

### Added

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
