# Codex Long-Running Controller

This controller defines how Codex should resume and advance the long-running
staged workflow for this repository without requiring the user to paste a new
prompt for every small step.

It is a process document only. It does not authorize real data fetching, live
trading, brokerage integration, order execution, credentials, API downloads, or
profitability claims.

## Startup Checklist

At the start of a continuation, read the current-state sources before choosing
work:

1. `README.md`
2. `AGENTS.md`
3. `.agents/skills/staged-quant-workflow/SKILL.md`
4. `docs/codex_long_running_controller.md`
5. `docs/engineering_log.md`
6. `docs/decision_log.md`
7. `docs/troubleshooting_log.md`
8. `CHANGELOG.md`

Then run the state checks from the staged workflow Skill:

```bash
git fetch origin
git branch --show-current
git status -sb --untracked-files=all
git log --oneline --decorate -12
gh pr list --state all --limit 10 --json number,state,isDraft,mergedAt,url,title,headRefName,baseRefName
```

If an expected controller, log, or Skill file is missing, treat that as a
workflow-control gap. The next safe stage may be to add or repair the missing
process artifact before continuing research work.

## Merge Gate

Do not start a new stage while a previous stage PR is open and awaiting human
review or merge.

If the previous stage PR has merged:

```bash
git switch main
git pull --ff-only origin main
git status -sb --untracked-files=all
python -m pytest -q
python -m compileall src tests research
```

Proceed only if the working tree is clean and baseline validation passes.

## Choosing The Next Safe Stage

Choose the next stage from current evidence, not from stale memory:

- latest merged PRs.
- latest checkpoint reports.
- `docs/engineering_log.md`.
- `docs/decision_log.md`.
- `docs/troubleshooting_log.md`.
- `docs/project_overview.md`.
- roadmap documents under `docs/`.
- current tests and repository state.

Prefer the smallest stage that removes a real blocker, refreshes stale
documentation, clarifies a research decision, or advances a reviewed roadmap.

If a stage changes source code, tests, research scripts, generated reports, or
strategy behavior, use stricter review gates than a documentation-only stage.

## Stop Conditions

Stop and report instead of continuing when any of these occurs:

- an open PR requires human review, approval, merge, or close decision.
- a push, PR creation, or merge decision is needed after local validation.
- the working tree is dirty in files unrelated to the intended stage.
- baseline tests fail.
- `python -m compileall src tests research` fails.
- `git diff --check` fails.
- the next safe stage would require real data fetching, downloads, vendor APIs,
  credentials, live trading, brokerage integration, order execution, or a
  profitability claim.
- the stage would require changing files outside the intended scope.
- a technical or methodological issue needs human input after reasonable local
  investigation.

Do not merge PRs unless the user explicitly instructs Codex to merge.

## Logging Requirements

For any meaningful stage, update the relevant durable logs before final checks.

Use:

- `docs/engineering_log.md` for implementation decisions, correctness reviews,
  process infrastructure, and stage summaries.
- `docs/decision_log.md` for durable research, workflow, or architecture
  decisions and their rationale.
- `docs/troubleshooting_log.md` for failures, missing prerequisites, confusing
  environment behavior, bad assumptions, failed checks, and recovery steps.
- `CHANGELOG.md` for user-visible repository changes.
- `EXPERIMENT_LOG.md` only for actual research experiments or planned
  experiment records.

When a technical, methodological, environment, testing, workflow, or reasoning
problem occurs, the log entry should include:

- the original mistake or incorrect assumption.
- the consequence.
- the exact error or evidence.
- investigation steps.
- correction attempts.
- final fix.
- verification results.
- remaining caveats.
- prevention measures.

## Stage Completion

Before committing:

```bash
python -m pytest -q
python -m compileall src tests research
git diff --check
```

For Skill or workflow-control changes, also run:

```powershell
.\scripts\audit-skills.ps1
```

Before opening a PR, confirm:

- changed files match the intended stage.
- guardrail grep results are prohibitions, caveats, tests, or documentation
  warnings only.
- no generated reports changed unless explicitly intended.
- no real data, live trading, brokerage, order execution, credential, or
  profitability logic was added.

After opening a PR, pause and report branch, commit, PR link, changed files,
validation, issues, and that Codex did not merge.
