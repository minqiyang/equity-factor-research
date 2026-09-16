# AI Agent Rules

Canonical responsibility: repository invariants, authority boundaries,
research-safety review standards, and writing-style rules.

## Authority And Scope

- Repository instructions define constraints and eligibility; they never expand
  current system, developer, user, or global authority.
- No repository file grants authority to push, create or update a PR, post a
  comment or review request, enable auto-merge, merge, close, deploy, access
  private data, or take destructive action. Each requires explicit user or
  higher-level authorization for that action and scope.
- Unless the user narrows the request, an explicit instruction to create or
  publish a PR authorizes the normal protected lifecycle for that same PR:
  readiness transition, required review request, in-scope remediation
  publication, verified review-thread reply and resolution, and eligible normal
  merge. The user may revoke that lifecycle authorization at any time.
- Lifecycle authorization never covers another PR, scope expansion, auto-merge,
  administrative or protection bypass, deployment, private data, credentials,
  brokerage, or destructive action.
- Approval for a named PR or remediation does not expand its stage or file
  scope. The owner grants standing same-change publication: completing an
  owner-requested in-scope repository change is explicit action-and-scope
  authorization for that change's ordinary feature-branch publication and
  same-PR protected lifecycle through eligible normal merge. A higher-level
  STOP or narrowed request remains a stop. Asking the owner for a second 建PR
  or merge prompt after that completion is a P1 process failure.
- Never direct-push or direct-merge to `main`, bypass protections, checks,
  reviews, or a merge queue, or use administrative override flags.
- Preserve unrelated user changes. Do not reset, clean, overwrite, or hide them;
  use a separate clean branch or worktree when the current tree is dirty.
- Treat credentials, private data, licenses, account identifiers, and production
  systems as sensitive. Never store secrets or raw private data in the repo.
- When ChatGPT/Codex CLI quota is exhausted, rotate to the next owner-designated
  ChatGPT CLI account in private control before Fable or Grok. Do not skip the
  remaining designated CLI account. Do not publish those addresses. Do not
  logout until the replacement login can complete. Skipping that rotation and
  jumping to Grok is a P1 process failure.
- Do not use GitHub Code Review. Do not post `@codex review`, enable Auto
  review, Exhaustive review, or credits-for-review. Keep GitHub Automatic Review
  disabled. Required PR review follows the live coordinator V7.23 standard:
  NORMAL lane has no mandatory formal review seat (coordinator verification);
  STANDARD and CRITICAL reviewer routing remains table-owned in routing_table.json
  (STANDARD lane requires 1 fresh independent reviewer, fresh Grok latest XHigh;
  CRITICAL lane requires 2 fresh independent reviewers, fresh Grok latest XHigh
  plus GPT Astra latest High / AUDIT). Review is read-only on a clean root at the
  exact current head, never the producer worktree. Required review runs in a new
  Herdr tab or pane opened from the coordinator workspace; a coordinator-session
  hidden `codex exec review` is not a visible review seat. The current owner
  no-GPT / lsgz:1 exception is session-scoped, not the permanent default.
- After two completed formal reviews on the same PR still report P1 or P2,
  stop the review-and-fix loop. Dispatch a fresh Grok latest session and a fresh
  Gemini latest / Antigravity session to analyze the whole PR and current tree,
  then the coordinator decides: escalate that task to EXPERT, keep fixing, or
  accept/ignore the remaining reported P1/P2 when within authorized bounds.
- If the coordinator chose keep-fixing and an in-scope fix lands, one additional
  review of that new exact head is allowed. If that review still reports P1/P2,
  Grok latest and Antigravity/Gemini latest judge whether those findings should
  be fixed. If yes, Grok Extra High implements; if no, the coordinator records
  ignore/accept. Do not resume an unbounded review loop.

## Writing Style And Syntax

This section binds every model and harness working in this repository,
including Codex, Grok Build, Gemini, Pi, and any later replacement.
Newly authored explanatory prose, comments, reports, and documentation
use this style. Research-safety invariants and authority prohibitions
keep their existing wording.

- Direct affirmative construction: state strictly what things are.
  Define concepts using direct predicates (subject + verb +
  object/predicate).
- Definition by negation is banned. False-dichotomy templates are
  banned: "not just X, but Y"; "not merely X, but rather Y";
  "it is not about X, it is about Y". Strawmen and
  pseudo-philosophical antithesis used to make an idea sound deeper
  are banned.
- Assertive tone: the first clause states the core definition or
  conclusion.
- When a Mermaid diagram or other visualization shows the structure more
  clearly than prose, use that diagram.

## Startup And Sources

- Live Herdr+Pi coordination standard is mandatory. Before dispatch or review,
  read both files in `Codex/Standards/herdr_pi_coordinator_v7_two_file/`:
  `coordinator.md` and `routing_table.json`. Those files own topology, lanes,
  routing, review seats, and visible-tab review. Do not load
  `Codex/standards/archive/`.
- After `AGENTS.md`, for staged continuations through a thin routing Skill, read
  `docs/current_handoff.md`, `docs/codex_long_running_controller.md`, then
  `docs/current_roadmap.md` for checkpoint, execution gates, and program status.
- Read `docs/north_star.md` for active product vision and demo-first delivery
  principles; read `docs/current_roadmap.md` for program milestones, execution
  gates, and the authoritative imperfection backlog.
- Use `docs/repo_map.md` for targeted orientation; verify cached handoff facts live.
- Read long logs or contracts only for active-stage or failed/sensitive checks.
- Cap unknown output and prefer targeted searches or short views. Regenerate
  `docs/repo_map.md` when workflow-control changes alter the map.

## Research Safety Invariants

- North Star and Project Scope: The ultimate aspiration is automated stock
  selection and trading pursuing sustainable risk-controlled long-term net
  returns. Stable profit is an objective, not a guarantee. This research
  repository is the first simulation phase; execution, live order capabilities,
  pre-trade risk limits, position/cash reconciliation, health monitoring, and
  emergency kill switches belong strictly to a future, separately authorized private
  execution repository. Active product aspiration and demo-first delivery
  principles are in `docs/north_star.md`.
- Keep this project simulated, auditable, reproducible, and explainable; never
  add brokerage connections, orders, paper/live trading, or live-account behavior.
- Demo-first delivery: deliver a working, presentable end-to-end vertical slice
  (Demo v0) first; record non-blocking imperfections, data caveats, and missing
  coverage in a lightweight backlog and improve in layers. Do not block early
  demos on an ideal pipeline, comprehensive SEC entity lineage, complete ledger
  schema coverage, or a factor zoo. While comprehensive SEC lineage may be
  deferred, basic identity and accounting integrity are NEVER deferrable:
  fail-closed ticker reuse / identity mis-stitching prevention (PIT-005);
  no default last-price exits or zero payoff at asset disappearance (PIT-006);
  no dividend double counting (PIT-007); no incompatible price/volume dollar
  turnover calculations (such as raw price multiplied by split-adjusted volume
  or vice-versa; price and volume bases must match); accepted timing contract
  without lookahead, realistic costs under existing turnover conventions, no
  future-membership selection, no silent repairs (PIT-009 typed missingness),
  sample honesty, trial retention, privacy, and non-execution. Preserved minimum
  correctness across these non-negotiable boundaries is mandatory. Formal promotion
  controls remain prerequisites for formal claims, not universal blockers for
  limited exploratory demos.
- Never invent results or claim profitability without reproducible evidence.
  Zero-cost or no-slippage results are diagnostics only.
- Keep failed, weak, invalid, abandoned, and contrary results visible; never
  cherry-pick only the best parameter or trial.
- Never use future returns, future universe membership, future fundamentals,
  same-period target returns, or any other look-ahead or survivorship leakage.
- Real/private-data access or interpretation requires accepted methodology,
  evidence gates, and explicit authorization.
- Explain data provenance, missingness, costs, slippage, execution timing,
  benchmark choice, sample splits, and material limitations.

## Alignment And Evidence

- Inputs must be known before trading. Distinguish feature, signal, rebalance,
  execution, and return dates; state execution time and test every boundary.
- Add deterministic tests for feature, strategy, portfolio, accounting, or
  reporting calculation changes.
- Document strategy changes in `EXPERIMENT_LOG.md`, `PROJECT_SPEC.md`, or the
  relevant note; record durable process evidence in `docs/engineering_log.md`.
- Keep reports and experiment records reproducible.
- Reports, handoffs, and section closings state completed facts and current
  measurements. Close a section with what it records. Authority remains in
  this file rather than in a closing disclaimer.

## Owner Corrections And Continuation

When the owner points out an agent process failure, do not stop at the
apology. Acknowledge the concrete failure, record a durable rule so it does
not recur, then continue the still-authorized task unless the correction
itself is a hold or unblock condition.

- Record authority, research-safety, and writing-style invariants here. Record the incident
  in `docs/engineering_log.md`. Operational review, quota, merge-wait, and Herdr
  tab-cleanup steps live in `docs/codex_long_running_controller.md`.
- Rank severity. Skipping a required live availability check is P1 process
  failure. Skipping the required pre-round Herdr tab inspection is P1 process
  failure. Asking the owner to type 建PR or merge after an owner-requested
  in-scope repository change is already complete is a P1 process failure.
  Asking the owner to type the next already-determined command, including
  running a demo or starting the next roadmap slice, is a P1 process failure
  during an authorized unattended session.
- Before starting the next round of Herdr work, inspect live tabs. Close only
  execution tabs whose process is inactive, required outputs are saved and
  hash-verified, write responsibility is released, and the tab will not be
  resumed. Keep the coordinator tab, working or blocked tabs, tabs whose disk
  and live state disagree, and any tab still needed for the current or next
  authorized card.
- When the next step is already determined by an accepted plan, owner decision,
  or repository rules, automatically execute the next clear, already-authorized
  step in the same turn without stopping to request repeat permission. Continue
  through ordinary QA, review, and remediation waits. Authorized unattended
  overnight work keeps executing determined roadmap slices until a stop
  condition. Decision-class questions go to GPT Astra xhigh. Stop only for a
  genuine blocker, a large unresolvable owner-semantic choice, missing
  authority, or additional authority. When the owner
  explicitly directs a STOP boundary after an authorized task, checks, and
  version management, that explicit stop directive governs; do not continue into
  unauthorized implementation or data tasks. Completing an owner-requested
  in-scope repository change includes ordinary feature-branch publication, the
  PR for that same change, required checks and review, and eligible normal
  merge. Private data access, new paid services, credentials, and trading stay
  outside that standing publication path. Do not end a turn merely on dispatch
  acknowledgment while delegated work is outstanding.
- Do not end the coordinator process while an authorized PR is waiting for its
  exact-head review body. Keep the session alive and re-check until that body
  exists (pass, findings, or an explicit current limit). Timeout is not a review
  result.
- Owner-authorized Antigravity child sessions start with session-only
  `--dangerously-skip-permissions`. Do not persist that setting into global
  `settings.json`.
- Delivery methodology correction: avoid unbounded perfectionism. Prioritize
  shipping a small, demonstrable, presentable end-to-end version (Demo v0);
  record non-blocking imperfections and caveats in a lightweight backlog and
  improve in working layers. Do not block early demos on an ideal pipeline or
  100% formal infrastructure. Historical Track A 14-trial refusal remains
  preserved historical evidence, but is no longer the sole entry point of the
  project.

- A whole-project ablation completion claim requires an explicit runtime and
  subsystem coverage matrix, tested high-impact hypotheses, preserved baseline
  and negative evidence, and an explicit limitations/gap assessment. Local QA,
  review success, a file inventory, or a handful of local optimizations cannot
  substitute for fulfillment of the owner's requested scope. Plan readiness
  records a planning checkpoint, not completion of the implementation round.

- For ablations that replace array traversal, test every accepted public
  boundary's empty-axis shapes (Nx0, 0xM and 0x0), duplicate/named axes and mixed
  scalar identity. A downstream function's stricter inputs do not narrow an
  upstream public API. Compare public cells, state digests and refusal reasons;
  ordinary test success cannot dispose of a demonstrated counterexample.

## Review Priorities

- Prioritize research-validity risk over style. A P1 requires concrete evidence
  from changed code, tests, or documentation; touching a factor input alone is
  not evidence of leakage.
- Flag as P1 an unsupported implemented/completed claim or a concrete mismatch
  in signal/factor timing, rebalance/execution timing, return-window or benchmark
  alignment, portfolio construction or accounting, or leakage prevention.
- Flag as P2 undocumented implemented/tested behavior, partial work called
  complete, stale next steps, or missing sparse/empty/invalid-data, cost,
  turnover, benchmark, or calendar edge tests unless evidence creates P1 risk.
- Rank misleading claims, hidden assumptions, and missing non-goals by impact;
  ignore typos unless meaning changes. Flag unexplained Unicode/control changes.
- Every finding must cite the file and claim, code/test evidence, mismatch and
  impact, plus a recommended fix or targeted test.

## Engineering And Change Discipline

- State scope before editing; afterward report files, tests, caveats, and next gate.
- Keep branches, PRs, and commits coherent; separate unrelated change types.
- Never remove, weaken, or skip tests to make a change pass.
- Choose the simplest implementation that fully meets current requirements;
  avoid speculative abstractions, configuration, and indirection.
- Grow the system in working layers: start with the smallest end-to-end
  version, then add capabilities without trading a working product for
  unfinished complexity.
- After every completed design or staged implementation, conduct ablation
  experiments to remove unnecessary abstractions, speculative design, and
  superfluous code, aiming for the simplest implementation sufficient for current
  requirements. Preserve baseline; test removals in isolation, compare behavior,
  correctness, and relevant costs, keep justified simplifications, and restore
  regressions. Never drop necessary tests, validation, or guards, and never conceal
  failures just to reduce line count. Record removals, retained necessities, and
  known limitations. A supported no-change outcome is valid. Ablation revalidation
  itself is not an infinite recursive ablation loop.
- Keep components modular and concerns clearly separated; prefer narrow modules,
  clear pandas, and deterministic tests.
- Prefer established, well-maintained libraries when they reduce complexity or
  improve reliability; reimplement common functionality only with a clear reason.
- Reuse existing project dependencies before writing custom implementations or
  adding packages. Check library documentation and types before deciding a
  needed capability is missing.
- Do not add an unjustified heavyweight dependency. The controller owns workflow
  and review lifecycle.
- Documentation Language Standard: Every newly authored or edited
  equity-factor-research-related documentation must be written in English. This
  includes public docs, AGENTS, skills, logs, private addenda, task handoffs, and
  reports. Do not rewrite immutable historical evidence just to translate it;
  report any retained historical exception explicitly. No newly authored
  non-English prose anywhere in this project's documentation. User-facing chat
  interactions may remain in the user's preferred language.
