# Troubleshooting Log

This log records failures, missing prerequisites, confusing environment
behavior, incorrect assumptions, failed checks, and recovery steps.

It is not an experiment log and must not be used to claim profitability or
investment performance.

## How To Update This Log

For technical, methodological, environment, testing, workflow, or reasoning
problems, include:

- original mistake or incorrect assumption.
- consequence.
- exact error or evidence.
- investigation steps.
- correction attempts.
- final fix.
- verification results.
- remaining caveats.
- prevention measures.

---

## 2026-06-03 - Missing Long-Running Workflow Control Files

Original assumption:

- The continuation request referenced
  `docs/codex_long_running_controller.md`, `docs/decision_log.md`,
  `docs/troubleshooting_log.md`, `CHANGELOG.md`, and
  `scripts/audit-skills.ps1` as files to read before continuing.

Consequence:

- Future Codex sessions could not rely on those files for startup order,
  durable decisions, troubleshooting history, changelog review, or Skill audit
  checks.
- The staged workflow Skill existed, but supporting controller and log
  artifacts were incomplete.

Evidence:

```text
MISSING docs\codex_long_running_controller.md
MISSING docs\decision_log.md
MISSING docs\troubleshooting_log.md
MISSING CHANGELOG.md
MISSING scripts\audit-skills.ps1
```

Investigation:

- Synced latest `main` after PR #27 was merged.
- Confirmed the repository was clean and had no open PRs.
- Read `README.md`, `AGENTS.md`,
  `.agents/skills/staged-quant-workflow/SKILL.md`,
  `docs/engineering_log.md`, and `docs/project_overview.md`.
- Listed `docs/`, `.agents/skills/`, and `scripts/` paths to confirm the
  referenced files were absent rather than overlooked.

Correction attempts:

- No failed correction attempt occurred in this stage. The missing files were a
  repository scaffolding gap, not a failing code path.

Final fix:

- Added `docs/codex_long_running_controller.md`.
- Added `docs/decision_log.md`.
- Added `docs/troubleshooting_log.md`.
- Added `CHANGELOG.md`.
- Added `scripts/audit-skills.ps1`.
- Updated `.agents/skills/staged-quant-workflow/SKILL.md` to reference the
  controller and audit script.
- Updated `docs/engineering_log.md` with the workflow-control scaffolding
  milestone.

Verification:

- `python -m pytest -q`: 209 passed.
- `python -m compileall src tests research`: passed.
- `.\scripts\audit-skills.ps1`: passed for 1 Skill file.
- `git diff --check`: passed with Windows line-ending conversion warnings only.

Remaining caveats:

- The audit script checks local Skill file structure only. It does not prove
  that a Skill is semantically complete.
- The controller should stay concise and should not become a substitute for
  current repo and PR state checks.

Prevention:

- Future long-running workflow continuations should read the controller and
  logs first.
- Missing expected controller or log files should be treated as workflow
  infrastructure gaps before new research implementation begins.
