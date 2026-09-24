# Codex Long-Running Controller

Canonical responsibility: staged workflow state transitions, external gates,
GitHub review lifecycle, waiting, stop conditions, and completion reporting.

## Scope And Authority

This process is subordinate to the
[repository authority boundary](../AGENTS.md#authority-and-scope), the
[research program charter](research_program_charter.md) (preserved formal research
evidence policy), and current higher-level instructions. Authority remains in
`AGENTS.md`, with the owner's standing grants recorded in `AUTHORITY.md`.
Eligibility is not authorization; every external, sensitive, or destructive
operation must satisfy that boundary.

## Startup And Freshness

1. After `AGENTS.md`, read `docs/current_handoff.md`,
   `docs/codex_long_running_controller.md`, and `docs/current_roadmap.md` for the
   recorded checkpoint, execution gates, and program status, respectively.
   Read `docs/north_star.md` for active product aspiration, edge thesis, and
   kill criteria, and `AUTHORITY.md` for standing owner grants.
2. Use `docs/repo_map.md` for targeted orientation and read only active-stage
   contracts. Research or code stages also require `PROJECT_SPEC.md`.
3. With capped output, check branch/tree state, local and remote `main`, recent
   history, and relevant PR state; verify the live remote before choosing a base.
4. If the tree is dirty or diverged, preserve it in place and use a clean
   worktree. Do not pull, reset, clean, or stash unreviewed user work.
5. Classify unrelated open or Draft PRs once by dependency, changed-file overlap,
   and semantic conflict. Do not rebase, close, merge, or overwrite them without
   authorization.

## Select And Bound The Stage

- `docs/current_handoff.md` owns the latest recorded operational checkpoint and
  next-safe-action routing. Its remote facts are cached evidence, not live state.
- `docs/current_roadmap.md` owns program stage sequence, dependencies, gate and
  completion criteria, coarse stage status, and the authoritative imperfection backlog.
- Active product goals and delivery principles are owned strictly and exclusively
  by `docs/north_star.md`.
- Detailed research specifications live in `PROJECT_SPEC.md`; active Milestone 2 Demo v0
  Definition of Done is owned exclusively by the roadmap anchor
  `docs/current_roadmap.md#active-delivery-target-demo-v0-definition-of-done`.
- `docs/research_program_charter.md` is preserved historical formal evidence policy.
- `docs/eodhd_sp500_diagnostic_campaign_contract.md` is preserved historical protocol
  context (recording the frozen Track A/B campaign scope and 14-trial diagnostic refusal).
  Neither the charter nor the campaign contract is a source of active product goals
  or a prerequisite delivery queue for Demo v0.
- Choose one coherent stage; keep unrelated fixes in separate branches and PRs.
- Do not infer permission for vendor access, protected samples, private results,
  deployment, brokerage behavior, or a broader research interpretation from a
  stage description.

## Local Execution And Validation

- Use a clean feature branch or worktree and state the intended edits first.
- Add or update tests and durable records required by `AGENTS.md`; stage only
  files in the declared scope.
- Run focused tests, then the baselines defined by `.github/workflows/ci.yml`.
- Check whitespace in all states: `git diff --check`,
  `git diff --cached --check`, and `git diff --check origin/main...HEAD` (or the
  established base range) for unstaged, staged, and committed changes.
- For workflow/Skill changes, audit the Skill and deterministically regenerate
  `docs/repo_map.md`. Before publication, review scope, Unicode, privacy, and guardrails.
- Use `docs/engineering_log.md` for implementation/process evidence,
  `docs/decision_log.md` for durable choices, `docs/troubleshooting_log.md` for
  failures, and `EXPERIMENT_LOG.md` only for research experiments.
- Documentation language follows the `AGENTS.md` writing rules.

## External Authorization Gate

Apply the [repository authority boundary](../AGENTS.md#authority-and-scope) to
external, sensitive, or destructive operations. Workflow eligibility and
successful checks do not grant authority. Without explicit action-and-scope
authorization, stop after local validation. The owner's standing same-change
publication grant in `AUTHORITY.md` is that explicit authorization for the
matching PR.

When the same-PR lifecycle authorization defined in `AGENTS.md` is current,
apply the lifecycle below to that PR. Otherwise, stop after local validation and
re-enter this gate before acting on a different PR or changed scope.

## Predecessor PR Gate

- If a required predecessor is not verified merged, check once, report one gate
  summary, and pause. Without an explicit merged/resume/inspect request, do not
  re-query an unchanged gate, rerun baselines, or start its dependent stage.
- An unrelated PR is not automatically a predecessor. Record why it is
  independent and avoid overlapping files.
- Continue only from the newly verified remote baseline after the predecessor
  merges. A clean status check must precede any branch switch or update.

## GitHub Review Lifecycle

- Do not use GitHub Code Review. Keep GitHub Codex Automatic Review disabled.
  Never post `@codex review` and never enable Auto, Exhaustive, or
  credits-for-review. Drafts get no request. After validation and required CI
  stabilize on the final stable current head, conduct formal review under the
  live Herdr+Pi coordination standard. Reviewer routing, lane seats, quota, and
  review-loop dispatch live in `coordinator.md`, `routing_table.json`, and
  `model_bindings.json`. The reviewer is read-only on a clean root at that exact
  head, never the producer worktree.
- For a full-lifecycle-authorized PR, use Draft while scope or validation is
  unstable. Mark it Ready once scope is final, local validation passes, no known
  blocker remains, and any checks available only after Ready can safely begin.
  Do not request review until required exact-head CI has stabilized.
- Review is required for research semantics, returns, costs, benchmarks,
  implementation, CI, security, data handling, or execution scope. Trivial
  spelling, date, count, or equivalent metadata-only edits may omit it.
- Never repeat a request for an unchanged head. An actionable fix changes the
  head and requires validation, CI, and one new current-head review.
- Count completed formal reviews that returned P1 or P2 on that PR. After two
  such reviews, stop the review-and-fix loop. Dispatch the live coordination
  standard's review-loop analysis on a clean read-only root, covering the whole
  PR, exact head, open findings, and current contracts. Their reports go to the
  coordinator. The coordinator then chooses, without inventing new authority:
  EXPERT escalation for this task, continue in-scope fixes, or owner-class
  acceptance/ignore of the remaining reported P1/P2 when the owner has
  authorized that decision class.
- After a keep-fixing decision and a landed in-scope fix, one additional formal
  review of that new exact head is allowed. If it still reports P1/P2, the live
  coordination standard's review-loop analysis judges whether to fix. If yes,
  that standard's fixer route implements; if no, record ignore/accept. Do not
  resume an unbounded review loop.
- A safe actionable finding may be fixed locally inside the already-authorized
  scope. After publishing and verifying the remediation, reply with its evidence
  and resolve only the addressed thread; leave an unverified or disputed thread
  open and stop. Publication, thread-write, and review-request actions still pass
  through the External Authorization Gate; remediation cannot expand the stage.
- No PR is technically merge-eligible while its current head has any unresolved
  actionable finding from any review channel, including PR-level comments or
  independent audits that do not create a resolvable thread.
- For review-required PRs, the review seats in `routing_table.json` supply the
  formal reviews; GitHub `@codex review` is a retired channel. Pending, missing,
  or head-mismatched independent review evidence is ineligible. A
  review-required PR is technically merge-eligible only when required exact-head
  independent reviews report no actionable findings, no review thread remains
  unresolved, and all required checks and formal reviews pass.
- Before claiming a provider, model, or quota is unavailable, probe it live in
  that same turn. Do not reuse an older pull request's limit message.
- Merge wait requires the actual exact-head formal review body: pass or
  findings. A silent wait that times out is not evidence of unavailability.
- Technical eligibility alone never grants merge authority; full-lifecycle or
  explicit merge authorization must also be current for that same PR and scope.

## Post-Delivery Ablation

Ablation experiments follow `AGENTS.md`. ABLATION dispatch lives in the live
Herdr+Pi coordination standard. Revalidation of an ablated candidate follows
this file's ordinary QA and review gates; ablation revalidation itself does
not trigger a recursive ablation loop.

## Herdr Tab Cleanup Before Next Round

Before dispatching the next round of Herdr work, list the current workspace
tabs and inspect process status against saved outputs.

Close an execution tab only when all of the following hold: the process tree
is inactive; required outputs exist and have been hash-verified; write
responsibility is released; and the tab will not be resumed. Do not close the
coordinator tab, a working or blocked tab, a tab whose disk and live state
disagree, or a tab still needed for the current or next authorized card.
Unrelated workspaces are out of scope. Multiple live work tabs may remain.

Skipping this inspection is a P1 process failure. `DONE` or `CARD_DONE` is not
proof that a tab is closeable.

When the next authorized step is already determined, dispatch it in the same
turn. Stop only for a genuine blocker, a large unresolvable owner-semantic
choice, missing authority, or when no capable model can determine the next
legal step. Do not pause to request permission to continue that step. When the
owner explicitly directs a STOP boundary after an authorized task, checks, and
version management, that explicit stop directive governs; do not continue into
unauthorized implementation or data tasks. The owner's standing same-change
publication grant in `AUTHORITY.md` is the explicit authorization for the
matching PR. Private data, new paid services, credentials, and trading stay
outside that path. Do not end a turn merely on dispatch acknowledgment while
delegated work is outstanding.

## Process Failures

The owner ranks these process failures as P1. Each entry names the commit that
first recorded the rule.

| Failure | First recorded |
| --- | --- |
| Skipping a required live availability check before claiming a provider, model, or quota is unavailable | `21d9d27` (2026-09-03); moved to the controller by `9798ba4` |
| Skipping the pre-round Herdr tab inspection | `00f1b3d` (2026-09-14) |
| Ending the coordinator process while an authorized PR waits for its exact-head review body | `00f1b3d` (2026-09-14) |
| Asking the owner for a second create-PR or merge command after an owner-requested in-scope change is complete | `932d576` (2026-09-15) |
| Asking the owner to issue an already-determined next command during authorized unattended work, including running a demo or starting the next roadmap slice | `4859cab` (2026-09-16) |

Each incident is recorded in `docs/engineering_log.md`. A new entry needs its
own incident record and owner confirmation.

## Waiting And Follow-Up

- Report an unchanged external gate once and pause; define no polling schedule,
  except as below.
- When an authorized PR has a requested exact-head review outstanding, keep the
  coordinator session alive and re-check until the exact-head independent review body
  exists: pass, findings, or an explicit current limit. Do not end the process
  and do not treat timeout as a review result. For human PR review feedback, check
  PR review threads when present. Never duplicate review requests for an
  unchanged head.
- Use a product monitor or recurring wait only when the user explicitly requests
  monitoring. Reuse one matching monitor, perform read-only checks, and never
  duplicate review requests.
- Never decide a critical owner choice on the owner's behalf. Missing authority
  remains a paused gate rather than an implicit approval.

## Protected Merge Eligibility

Technical eligibility requires low/clear risk, expected author/head owner,
verified protections, checks and reviews, conflict/queue state, and file scope.
Pending or unverifiable evidence is ineligible; eligibility never authorizes
auto-merge or merge.

When full-lifecycle authorization is current and every technical condition
passes, perform the normal protected PR merge without another prompt. Never use
an administrative override or protection bypass. Auto-merge remains a separate
action and requires separate explicit authorization.

## Stop Conditions

Stop for missing authority; unclear tree/branch ownership; failed validation
outside safe remediation; unresolved P1/high risk; unverifiable protection,
checks, reviews, conflicts, or scope; destructive/security/privacy risk; or
unresolved provenance, license, point-in-time, benchmark, cost, timing, or
statistical choices. Also stop before unapproved vendor/private data,
credentials, brokerage/orders, live behavior, or out-of-scope interpretation.

## Completion Report

Report branch, commit/PR, risk, files, checks, findings, assumptions, external
authorization, and next gate. Keep state with the owners named in `Select And
Bound The Stage`, and history in logs; do not duplicate either across active sources.
