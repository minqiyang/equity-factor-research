# Changelog

All notable repository changes should be recorded here.

This project does not use changelog entries to claim investment performance,
profitability, or trading readiness.

## Unreleased

### Added

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

- Updated the long-running controller and staged workflow Skill with bounded
  execution behavior, low-risk ambiguity handling, missing-file recovery rules,
  and expanded stop conditions.
- Updated `.agents/skills/staged-quant-workflow/SKILL.md` to reference the
  long-running controller and Skill audit script.
