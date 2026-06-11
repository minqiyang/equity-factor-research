---
name: staged-quant-workflow
description: Continue the ai-equity-factor-research staged workflow without requiring the user to paste a new prompt for every phase. Use when resuming the long-running goal, advancing after a merged PR, creating the next small stage, or deciding whether to pause at a merge gate.
---

# Staged Quant Workflow

## When to use

Use this Skill for the `ai-equity-factor-research` repository when the user asks to continue the long-running staged workflow, resume after a PR merge, plan the next phase, publish a stage PR, or recover from a workflow/test/environment issue.

Do not use it for unrelated one-off explanations unless the explanation depends on current staged workflow state.

## Desired outcome

Codex should be able to advance one small, reviewable stage at a time without waiting for the user to supply a fresh detailed prompt. Each stage should either:

- stop at a clear merge gate or blocker report; or
- produce a validated branch, commit, and ready-for-review PR, then pause without merging.

## Success criteria

- The current repo and PR state are verified before making decisions.
- The next stage is chosen from current evidence: latest merged PRs, checkpoint reports, `docs/engineering_log.md`, `PROJECT_SPEC.md`, `EXPERIMENT_LOG.md`, and relevant roadmap docs.
- Changes are tightly scoped to one coherent documentation update, test improvement, bugfix, feature, or research-process milestone.
- Documentation-only and low-risk checkpoint PRs are opened ready for review, not draft.
- Code-changing PRs are opened ready for review only after tests pass and a read-only review finds no high or medium issues.
- Codex does not merge PRs unless the user explicitly instructs it to merge.
- Guardrails remain intact: no real data fetching, no live trading, no brokerage or order execution, no credentials, and no profitability claims.
- Any technical, methodological, environment, testing, workflow, or reasoning problem is recorded in the relevant log with the full failure-to-fix chain.
- Low-risk ambiguity is handled by making a reasonable assumption, recording it in the final report and relevant log, and continuing.

## Inputs and context to collect

Start each continuation by reading `docs/current_handoff.md` first, then
`docs/repo_map.md` for concise orientation when needed. Read deeper logs and
long documents only when the handoff points to them, the active stage requires
them, a check fails, or a guardrail-sensitive decision needs source evidence.

After the handoff, collect:

- current branch and working-tree status;
- latest local and remote `main`;
- recent git history;
- open and recently merged PRs;
- `docs/codex_long_running_controller.md`;
- deeper decision, troubleshooting, changelog, checkpoint, or roadmap docs only
  when needed for the active stage;
- current test status when continuing beyond a merge gate.

If a previous stage PR is still open, stop and report the merge gate instead of starting a new stage.

If a prompt expects a missing file, do not silently treat that as fatal. Create the file in a separate workflow-control PR when it is a low-risk documentation, logging, controller, or audit-script scaffold. Stop and report when the missing file affects product behavior, strategy logic, data access, execution, credentials, or external systems.

## Context Budget And Retrieval Policy

Use a staged retrieval ladder so continuation work stays current without
overloading context.

First-pass context is limited to:

- `docs/current_handoff.md`
- `docs/repo_map.md`
- `AGENTS.md`
- `PROJECT_SPEC.md`
- `docs/codex_long_running_controller.md`
- `.agents/skills/staged-quant-workflow/SKILL.md`

Treat the short-entry files as retrieval controls:

- `docs/current_handoff.md` should stay short, ideally 100-200 lines, and
  include the latest merged PR, current open PR gate, next recommended stage,
  known blockers, recent validation result, and a reminder not to read full
  logs by default.
- `docs/repo_map.md` should be an index rather than history: directory
  structure, folder purposes, key file locations, and which files are long
  enough to require search, tail, or small-range reads.
- `docs/codex_long_running_controller.md` should define workflow behavior and
  stop conditions, not duplicate detailed stage history.

Do not read multiple long logs, generated reports, experiment JSON logs, or
checkpoint/design reports in parallel. Long files include
`docs/engineering_log.md`, `docs/decision_log.md`,
`docs/troubleshooting_log.md`, `CHANGELOG.md`, `reports/*.md`,
`reports/experiment_logs/*.json`, and long checkpoint or design docs.

Detailed logs can remain comprehensive, but default access is restricted.
Use tail, keyword search, or small line ranges for `docs/engineering_log.md`,
`docs/decision_log.md`, and `docs/troubleshooting_log.md`. For `CHANGELOG.md`,
prefer `git log`, `git show --stat`, `rg -n "Unreleased" CHANGELOG.md`, or a
tail read instead of a full-file read.

Context ladder:

- Level 0: git, PR, branch, and status commands only.
- Level 1: `docs/current_handoff.md` and `docs/repo_map.md`.
- Level 2: one targeted roadmap or design doc for the active stage only.
- Level 3: tail or keyword search in long logs.
- Level 4: full-file read only if absolutely required; explain why.

Prefer targeted commands such as `git diff --name-only`, `git diff --stat`,
`git show --stat`, `rg -n "keyword" file`, `Get-Content -Tail`, and
`Select-String` with explicit patterns. Avoid uncapped full-file reads.

Do not paste full large files. Summarize command results, cap log output, and
switch to narrower searches if output is too large. If tool output reports
`Output exceeded the available model context and was truncated`, do not rely
on the truncated output. Stop broad reading, record the issue in
`docs/troubleshooting_log.md` if meaningful, resume from
`docs/current_handoff.md` and `docs/repo_map.md`, and reread only the targeted
sections needed for the active stage.

Do not read or print full generated reports unless the current stage
specifically concerns that report. Prefer headings, grep, or small snippets.

Keep final reports concise: branch, PR, files changed, checks, issues,
assumptions, next stage, and confirmation that Codex did not merge.

## Workflow guidance

Begin with read-only state inspection. If the previous required PR has merged, switch to `main`, fast-forward from `origin/main`, and rerun baseline validation before branching.

Choose the next stage conservatively from the latest checkpoint recommendation. Prefer documentation or planning stages when roadmap state is stale, when data prerequisites are missing, or when guardrails need clarification before implementation. Prefer code only when the needed design, tests, and scope boundaries are already clear.

Continue as a bounded staged execution agent. Do not ask the user for a new prompt after every small step; stop only at controller-defined stop conditions, failed checks, human approval gates, PR/push/merge decisions, or the final stage report.

Before editing, state the intended files and scope. Use a separate branch for each stage. Use the app's default `codex/` branch prefix unless the user or stage instructions specify another branch name.

After editing, run focused validation appropriate to the scope plus the standard baseline unless the stage explicitly says otherwise:

```bash
python -m pytest -q
python -m compileall src tests research
git diff --check
```

Run a read-only scope review before committing. Confirm changed files match the stage, guardrail grep findings are acceptable, and generated reports did not change unless the stage explicitly updates them.

For workflow-control or Skill changes, run `.\scripts\audit-skills.ps1` before committing when the script exists.

Commit only intended files. Push the branch and create a ready-for-review PR when the applicable readiness gate is met. Pause after PR creation.

## Known pitfalls

- Do not continue to a new stage merely because the user says "merged"; verify the PR state and sync `main`.
- Do not mix bugfixes into unrelated stage branches. Split independent fixes into separate PRs.
- Do not treat synthetic diagnostics as real-data evidence or profitability support.
- Do not let pandas or line-ending behavior hide meaningful CSV validation bugs; inspect semantic diffs and line-ending-only diffs when relevant.
- Do not skip detailed logging after a technical or workflow problem just because the final tests pass.
- Do not stop on low-risk documentation ambiguity when a narrow, logged assumption can keep the staged workflow moving.

## Tools and deterministic operations

Reliable state checks:

```bash
git fetch origin
git branch --show-current
git status --porcelain | head -n 50
git log --oneline -20
gh pr list --state all --limit 10 --json number,state,isDraft,mergedAt,url,title,headRefName,baseRefName 2>&1 | head -c 8000
```

Merge-gate sync:

```bash
git switch main
git pull --ff-only origin main
git status --porcelain | head -n 50
```

Baseline validation:

```bash
python -m pytest -q
python -m compileall src tests research
git diff --check origin/main..HEAD
```

Skill audit:

```powershell
.\scripts\audit-skills.ps1
```

Workflow map refresh:

```bash
python scripts/repo_map.py
```

Command-output protection:

```bash
git diff --name-only | head -n 80
COMMAND 2>&1 | head -c 8000
```

Use equivalent PowerShell caps such as `Select-Object -First` when needed.
Write full output to temp files and inspect targeted ranges only if full review
is necessary. Never print full generated reports or large logs by default.

Guardrail review:

```bash
git grep -n -i "live trading\|broker\|alpaca\|yfinance\|ccxt\|requests\|real data\|profitability\|guaranteed\|guarantee" -- . || true
```

Interpret guardrail matches carefully. Prohibitions, caveats, tests, and warning language can be acceptable; active fetching, execution, credential, or unsupported performance-claim logic is not.

## Verification

Before finalizing a stage, report:

- PR or merge gate status;
- branch name;
- commit hash, if committed;
- PR link, if opened;
- files changed;
- tests and checks run;
- high, medium, and low issues;
- confirmation that Codex paused after PR creation and did not merge.

## Update policy

After each use, update this Skill only with concise lessons verified in that run, such as a new stable command, a recurring pitfall, or a changed PR readiness rule. Do not add speculative future instructions.
