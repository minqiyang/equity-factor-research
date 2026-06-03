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

## 2026-06-03 - PowerShell Search Pattern Quoting Error

Original mistake:

- During the WorldQuant catalog refresh scope review, a stale-text `rg` search
  used a PowerShell double-quoted string that contained Markdown backticks.

Consequence:

- The search command failed before checking the target documents.
- No repository files were modified by the failed command, and baseline tests
  had already passed, but the intended stale-text check still needed to be
  rerun.

Evidence:

```text
The string is missing the terminator: ".
CategoryInfo          : ParserError
FullyQualifiedErrorId : TerminatorExpectedAtEndOfString
```

Investigation:

- The failing pattern included `` `alpha_009` `` inside a PowerShell
  double-quoted command string.
- PowerShell treats the backtick as an escape character, so the shell parsed
  the command incorrectly before `rg` could run.

Correction attempts:

- The failed double-quoted command was not reused.
- The check was rerun with a single-quoted PowerShell pattern so Markdown
  backticks were treated as literal characters.

Final fix:

- Reran the stale-text search successfully with single quotes around the regex
  pattern.

Verification:

- The corrected search completed.
- The only remaining match was an older 2025 historical engineering-log entry,
  not the refreshed `docs/worldquant_alpha_catalog.md`.
- The catalog no longer contains the stale current-state text that said no
  alpha was implemented.

Remaining caveats:

- Historical logs can correctly preserve older milestone wording and should not
  be rewritten unless they are explicitly misleading as current guidance.

Prevention:

- Use single-quoted PowerShell strings for `rg` patterns that contain Markdown
  backticks.
- Treat shell quoting failures as failed checks and rerun the check before
  committing.

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
