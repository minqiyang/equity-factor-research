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

## 2026-06-04 - LEAN Scaffold README Guardrail Phrase Mismatch

Original mistake:

- The first version of `lean/README.md` described the same guardrail as
  "real data downloads" and "real market data fetching or downloads", but the
  new static guardrail test expected the exact phrase `no real market data`.

Consequence:

- The focused scaffold test failed even though the intended guardrail was
  present in less exact wording.

Evidence:

```text
tests/test_lean_smoke_test_scope.py::test_lean_scaffold_readme_preserves_guardrails
AssertionError: assert 'no real market data' in ...
```

Investigation:

- Compared the failing expected phrase with `lean/README.md`.
- Confirmed the README prohibited real data downloads but did not include the
  exact wording required by the static test.
- Confirmed this was a documentation/test wording mismatch, not an
  implementation of real data access.

Correction attempts:

- The test was not weakened and the guardrail expectation was not removed.
- First correction attempt added `no real market data path`, but the line wrap
  split the phrase as `no\nreal market data`, so the exact string check still
  failed.
- Second correction attempt placed `no real market data` on one line, but the
  focused test then exposed that other exact README phrases such as
  `no live trading` and `no brokerage` were still implied rather than written
  directly.

Final fix:

- Updated `lean/README.md` to include an `Explicit Guardrail Phrases` section
  containing the exact static-review phrases required by the test.

Verification:

- The focused test and full validation were rerun after the README fix:
  `python -m pytest -q tests/test_lean_smoke_test_scope.py` reported
  6 passed, `python -m pytest -q` reported 264 passed,
  `python -m compileall src tests research` passed,
  `python -m compileall lean` passed, and `git diff --check` passed with
  Windows line-ending conversion warnings only.

Remaining caveats:

- Exact-phrase guardrail tests can fail on equivalent wording. In this case
  the explicit wording is useful because it makes the human-facing README
  clearer.

Prevention:

- When adding static documentation guardrail tests, copy the required caveat
  phrases directly into the human-facing document during the same edit pass.

---

## 2026-06-04 - Stage Edits Started Before Branch Creation

Original mistake:

- During the synthetic IC / Rank IC diagnostics stage, implementation edits
  began after syncing `main` but before creating the dedicated stage branch.

Consequence:

- The worktree had uncommitted stage changes on local `main`.
- No files were staged, committed, pushed, or merged, and the remote `main` was
  not affected, but the local workflow temporarily violated the project rule to
  use a separate branch for each stage.

Evidence:

- The startup checks showed the repository on `main` after PR #32 was merged
  and pulled.
- After implementing the helper and tests, `git diff --name-only` showed local
  changes in `docs/engineering_log.md`, `src/features/diagnostics.py`, and
  `tests/test_diagnostics.py` before a stage branch had been created.

Investigation:

- Confirmed the issue was a workflow sequencing error, not a source-code
  correctness failure.
- Confirmed the changes were still unstaged and uncommitted, so they could be
  moved safely onto a branch without rewriting history or touching remote
  state.

Correction attempts:

- No failed correction attempt occurred. The direct recovery path was to create
  the branch from the current `main` state while preserving the unstaged
  changes.

Final fix:

- Ran `git switch -c codex/synthetic-ic-rank-ic-diagnostics`.
- The uncommitted stage changes moved onto the dedicated branch.

Verification:

- `git branch --show-current` returned
  `codex/synthetic-ic-rank-ic-diagnostics`.
- `git status -sb --untracked-files=all` showed only intended unstaged files on
  that branch before commit review.

Remaining caveats:

- The branch was created after edits instead of before edits. The final branch
  diff is still reviewable, but the sequencing mistake should remain visible in
  the durable log.

Prevention:

- After syncing `main` and passing baseline validation, create the stage branch
  before applying any patch.
- Treat the branch creation step as part of the pre-edit checklist, not as a
  pre-commit cleanup step.

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
