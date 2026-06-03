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

Start each continuation by collecting:

- current branch and working-tree status;
- latest local and remote `main`;
- recent git history;
- open and recently merged PRs;
- `docs/codex_long_running_controller.md`;
- `docs/decision_log.md`;
- `docs/troubleshooting_log.md`;
- `CHANGELOG.md`;
- latest checkpoint or roadmap docs;
- current test status when continuing beyond a merge gate.

If a previous stage PR is still open, stop and report the merge gate instead of starting a new stage.

If a prompt expects a missing file, do not silently treat that as fatal. Create the file in a separate workflow-control PR when it is a low-risk documentation, logging, controller, or audit-script scaffold. Stop and report when the missing file affects product behavior, strategy logic, data access, execution, credentials, or external systems.

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
git status -sb --untracked-files=all
git log --oneline --decorate -12
gh pr list --state all --limit 10 --json number,state,isDraft,mergedAt,url,title,headRefName,baseRefName
```

Merge-gate sync:

```bash
git switch main
git pull --ff-only origin main
git status -sb --untracked-files=all
```

Baseline validation:

```bash
python -m pytest -q
python -m compileall src tests research
git diff --check
```

Skill audit:

```powershell
.\scripts\audit-skills.ps1
```

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
