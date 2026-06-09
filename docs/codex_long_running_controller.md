# Codex Long-Running Controller

This controller defines how Codex should resume and advance the long-running
staged workflow for this repository without requiring the user to paste a new
prompt for every small step.

It is a process document only. It does not authorize real data fetching, live
trading, brokerage integration, order execution, credentials, API downloads, or
profitability claims.

## Startup Checklist

At the start of a continuation, read `docs/current_handoff.md` first. Then read
`AGENTS.md`, this controller, and `.agents/skills/staged-quant-workflow/SKILL.md`
as governing workflow documents. Use `docs/repo_map.md` for concise repository
orientation before broad scans.

Read deeper logs and long documents only when `docs/current_handoff.md` points
to them, the active stage requires them, a check fails, or a guardrail-sensitive
decision needs source evidence. Deeper sources include:

- `docs/engineering_log.md`
- `docs/decision_log.md`
- `docs/troubleshooting_log.md`
- `CHANGELOG.md`
- `EXPERIMENT_LOG.md`
- generated reports under `reports/`

Then run the state checks from the staged workflow Skill:

```bash
git fetch origin
git branch --show-current
git status --porcelain | head -n 50
git log --oneline -20
gh pr list --state all --limit 10 --json number,state,isDraft,mergedAt,url,title,headRefName,baseRefName 2>&1 | head -c 8000
```

If an expected controller, log, or Skill file is missing, treat that as a
workflow-control gap. The next safe stage may be to add or repair the missing
process artifact before continuing research work.

## Command Output Budget

Protect token budget without hiding evidence:

- cap unknown large command output by default.
- prefer `git status --porcelain | head -n 50`.
- prefer `git log --oneline -20`.
- prefer `git diff --name-only | head -n 80`.
- use `COMMAND 2>&1 | head -c 8000` for unknown output.
- in PowerShell, use equivalent caps such as `Select-Object -First` when
  `head` is unavailable.
- write full output to temp files and inspect targeted ranges only if full
  review is needed.
- never `cat` full generated reports or large logs by default.

## Merge Gate

Do not start a new stage while a previous stage PR is open and awaiting human
review or merge.

If the previous stage PR has merged:

```bash
git switch main
git pull --ff-only origin main
git status --porcelain | head -n 50
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

## Low-Risk Ambiguity

For low-risk ambiguity, make a reasonable assumption, record the assumption in
the final report and the relevant durable log, and continue.

Low-risk ambiguity includes minor documentation placement choices, wording
scope, whether to update a workflow log alongside a controller change, and
whether to create a missing workflow-control scaffold file that the current
prompt clearly expects.

Do not continue on an assumption if the ambiguity could cause a destructive
operation, broad architecture change, product behavior change, data loss,
security or privacy risk, new production dependency, or scope conflict with
`AGENTS.md`, `PROJECT_SPEC.md`, this controller, or the staged workflow Skill.

If a file is missing but the current prompt expects it:

- create it in a separate workflow-control PR when it is a low-risk
  documentation, logging, controller, or audit-script scaffold.
- stop and report when the missing file affects product behavior, strategy
  logic, data access, execution, credentials, or external systems.

## Stop Conditions

Stop and report instead of continuing when any of these occurs:

- an open PR requires human review, approval, merge, or close decision.
- a push, PR creation, or merge decision is needed after local validation.
- a PR has been opened and is ready for human review or merge.
- the working tree is dirty before a new stage starts.
- baseline tests fail.
- `python -m compileall src tests research` fails.
- `git diff --check` fails.
- an unclear requirement could cause destructive work or broad architecture
  change.
- missing credentials or external access are required.
- a new production dependency would be required.
- tests fail in a way that cannot be fixed safely within the current scope.
- a read-only review finds a high or medium issue.
- security, privacy, data-loss, or irreversible-operation risk appears.
- the stage conflicts with `AGENTS.md`, `PROJECT_SPEC.md`, this controller, or
  the staged workflow Skill.
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
git diff --check origin/main..HEAD
```

For Skill or workflow-control changes, also run:

```powershell
.\scripts\audit-skills.ps1
python scripts/repo_map.py
```

Before opening a PR, confirm:

- changed files match the intended stage.
- `git diff --name-only origin/main..HEAD | head -n 80` contains only intended
  files.
- guardrail grep results are prohibitions, caveats, tests, or documentation
  warnings only.
- no generated reports changed unless explicitly intended.
- no real data, live trading, brokerage, order execution, credential, or
  profitability logic was added.

After opening a PR, pause and report branch, commit, PR link, changed files,
validation, issues, and that Codex did not merge.
