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

## 2026-06-05 - Validation Split Empty-Test Expectation Mismatch

Original mistake:

- The first version of `tests/test_validation.py` included a parameterized
  empty-window test case with `validation_end="2024-01-06"` while the default
  `test_end` was also the final index date, `2024-01-06`.
- The test expected the helper to report an empty test split.

Consequence:

- The focused validation test failed even though the helper was rejecting the
  input for a stricter and earlier reason: the configured split boundaries did
  not satisfy the required chronological order.
- No files were committed, pushed, or merged before the failure was fixed.

Evidence:

```text
tests/test_validation.py::test_make_train_validation_test_split_rejects_empty_windows[2024-01-02-2024-01-06-test split]
AssertionError: Regex pattern did not match.
Expected regex: 'test split'
Actual message: 'split boundaries must satisfy train_end < validation_end < test_end'
```

Investigation:

- Reviewed the failing case against the helper contract.
- Confirmed that when `test_end` is omitted, the helper uses the final
  available date as the test boundary.
- Confirmed that `validation_end == test_end` violates the intended strict
  boundary ordering before any empty-window check should run.
- Confirmed that another test already covers this invalid boundary-order case.

Correction attempts:

- No code change was needed because the helper behavior was correct.
- Removed the contradictory duplicate parameter from the empty-window test
  case instead of weakening the boundary-order validation.

Final fix:

- Kept strict `train_end < validation_end < test_end` validation.
- Kept empty-window tests for train and validation windows where the boundary
  ordering remains meaningful.
- Left the `validation_end == test_end` case covered by the invalid-boundary
  test.

Verification:

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

Remaining caveats:

- The helper is intentionally limited to chronological date-window splitting.
  It does not perform model selection, calculate returns, or interpret any
  diagnostic result.

Prevention:

- For future split tests, separate invalid-boundary-order cases from
  empty-window cases.
- When a helper performs staged validation, assert the earliest intended
  validation failure rather than a later condition that cannot be reached.

---

## 2026-06-04 - README Diff Filter Regex Error

Original mistake:

- During the GitHub landing-page polish scope review, an optional
  `Select-String` diff-filter command used a regex that included an unescaped
  `[` character.

Consequence:

- The optional filtered diff display failed before printing its intended
  heading summary.
- No repository files were modified by the failed command, and the required
  validation checks had already passed, but the diff review needed to be rerun
  with a valid command before commit.

Evidence:

```text
Select-String : The string ... is not a valid regular expression:
Unterminated [] set.
```

Investigation:

- The failing pattern included alternatives such as `^\+![` without escaping
  the bracket.
- The failure was isolated to the optional presentation filter, not to
  Markdown, tests, link checking, or repository content.

Correction attempts:

- The invalid regex was not reused.
- The diff review was rerun with simpler `git diff --stat` and
  `Select-String -SimpleMatch` commands.

Final fix:

- Used fixed-string matching for README section headings and the visual asset
  reference.

Verification:

- The rerun diff review showed the intended README sections and visual asset
  reference.
- `git status --short --untracked-files=all` still showed only the intended
  documentation and asset files.

Remaining caveats:

- The failed command was an inspection aid only; it did not affect repository
  content.

Prevention:

- Prefer `Select-String -SimpleMatch` for literal diff-heading checks.
- Escape regex metacharacters when using `Select-String -Pattern`.

---

## 2026-06-04 - Parallel Pull And State Check Race

Original mistake:

- During the continuation after PR #41 was open, `git pull --ff-only origin
  main` was run in parallel with `git status` and `git log`.

Consequence:

- The `git log` output could show the pre-pull commit while the pull was
  fast-forwarding `main`.
- No files were edited, staged, committed, pushed, or merged during the
  ambiguous state check, but the state evidence needed to be refreshed before
  choosing the next stage.

Evidence:

- `git pull --ff-only origin main` fast-forwarded from the PR #40 merge to the
  PR #41 merge.
- The parallel `git log` output still showed the PR #40 merge as `HEAD`.

Investigation:

- Treated the parallel state output as potentially stale.
- Reran `git status`, `git log`, `gh pr view 41`, and `gh pr list --state
  open` after the pull completed.

Correction attempts:

- No failed correction attempt occurred. The recovery was to rerun the state
  checks after the branch-changing command completed.

Final fix:

- Used the post-pull state as authoritative.
- Confirmed `main` was at the PR #41 merge commit before selecting the next
  stage.

Verification:

- `git log --oneline --decorate -8` showed `main` at the PR #41 merge commit.
- `gh pr view 41` confirmed PR #41 was merged.
- `gh pr list --state open` returned no open pull requests.
- `python -m pytest -q` reported 264 passed.
- `python -m compileall src tests research` passed.

Remaining caveats:

- Parallel shell commands are appropriate for independent reads only when no
  command mutates the working tree, branch pointer, or index.

Prevention:

- Do not run `git pull`, `git switch`, or other branch-changing commands in
  parallel with status or log reads used as authoritative evidence.
- After any branch-changing command, rerun state checks before selecting a
  stage or editing files.

---

## 2026-06-04 - Parallel Read And Branch Switch Race

Original mistake:

- During a long-running workflow continuation after PR #40, file reads for
  roadmap documents were run in parallel with `git switch main`.

Consequence:

- Some displayed document output could have come from the pre-switch branch
  rather than the synced `main` checkout.
- No files were edited, staged, committed, pushed, or merged during this
  ambiguous read window, but the evidence used for next-stage selection needed
  to be refreshed from the authoritative current branch.

Evidence:

- The parallel output showed PR #40 scaffold content while the branch switch
  was still occurring.
- Because the file reads and branch switch were independent parallel tool
  calls, their exact ordering was not guaranteed.

Investigation:

- Treated the parallel-read output as potentially stale instead of relying on
  it for stage selection.
- Confirmed local `main` was then fast-forwarded to the PR #40 merge commit.
- Reread current scaffold and planning documents from the synced `main`
  checkout before selecting the next stage.

Correction attempts:

- No failed correction attempt occurred. The immediate recovery was to rerun
  state checks and reread the relevant current files after `main` was synced.

Final fix:

- Used the post-pull `main` state as authoritative for the next-stage decision.
- Selected a documentation-only LEAN scaffold review checklist based on the
  merged PR #40 scaffold and current planning documents.

Verification:

- `git log --oneline --decorate -8` showed `main` at the PR #40 merge commit.
- `gh pr view 40` confirmed PR #40 was merged.
- `gh pr list --state open` returned no open pull requests.
- `python -m pytest -q` reported 264 passed.
- `python -m compileall src tests research` passed.

Remaining caveats:

- Parallel file reads are safe only when the working tree reference is stable.
  They are not reliable while a branch switch or pull is changing the checkout.

Prevention:

- Do not run branch-changing commands in parallel with file reads whose content
  is used for stage selection.
- After any branch switch or pull, rerun state checks and reread relevant
  roadmap files before editing.

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
