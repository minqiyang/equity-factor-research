# AI Agent Rules

Canonical responsibility: repository invariants, authority boundaries, and
research-safety review standards.

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
- Local-edit authorization is not publication authorization; approval for a
  named PR or remediation does not expand its stage or file scope.
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
  disabled. Required PR review follows the live coordinator V7.22 standard:
  STANDARD lane requires 1 fresh independent reviewer (fresh Grok latest XHigh);
  CRITICAL lane requires 2 fresh independent reviewers (fresh Grok latest XHigh
  plus GPT Astra latest High). Review is read-only on a clean root at the exact
  current head, never the producer worktree. The current owner no-GPT / lsgz:1
  exception is session-scoped, not the permanent default.
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

## Startup And Sources

- After `AGENTS.md`, for staged continuations through a thin routing Skill, read
  `docs/current_handoff.md`, `docs/codex_long_running_controller.md`, then
  `docs/current_roadmap.md` for checkpoint, execution gates, and program status.
- Use `docs/repo_map.md` for targeted orientation; verify cached handoff facts live.
- Read long logs or contracts only for active-stage or failed/sensitive checks.
- Cap unknown output and prefer targeted searches or short views. Regenerate
  `docs/repo_map.md` when workflow-control changes alter the map.

## Research Safety Invariants

- North Star and Project Scope: The ultimate aspiration is automated stock
  selection and trading pursuing sustainable risk-controlled long-term net
  returns. Stable profit is an objective, not a guarantee. This research
  repository is the first simulation phase; execution and live order capabilities
  belong strictly to a future, separately authorized private execution repository.
- Keep this project simulated, auditable, reproducible, and explainable; never
  add brokerage connections, orders, paper/live trading, or live-account behavior.
- Demo-first delivery: deliver a working, presentable end-to-end vertical slice
  (Demo v0) first; record non-blocking imperfections, data caveats, and missing
  coverage in a lightweight backlog and improve in layers. Do not block early
  demos on an ideal pipeline, full SEC entity lineage, complete ledger schema
  coverage, or a factor zoo. Preserved minimum correctness (no lookahead,
  realistic costs, sample honesty, trial retention, privacy, and non-execution)
  is non-negotiable. Formal promotion controls remain prerequisites for formal
  claims, not universal blockers for limited exploratory demos.
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

- Record authority and research-safety invariants here. Record the incident
  in `docs/engineering_log.md`. Operational review, quota, merge-wait, and Herdr
  tab-cleanup steps live in `docs/codex_long_running_controller.md`.
- Rank severity. Skipping a required live availability check is P1 process
  failure. Skipping the required pre-round Herdr tab inspection is P1 process
  failure.
- Before starting the next round of Herdr work, inspect live tabs. Close only
  execution tabs whose process is inactive, required outputs are saved and
  hash-verified, write responsibility is released, and the tab will not be
  resumed. Keep the coordinator tab, working or blocked tabs, tabs whose disk
  and live state disagree, and any tab still needed for the current or next
  authorized card.
- When the next step is already determined by an accepted plan, owner decision,
  or repository rules, automatically execute the next clear, already-authorized
  step in the same turn without stopping to request repeat permission. Continue
  through ordinary QA, review, and remediation waits; stop only for a genuine
  blocker, a necessary owner decision, or additional authority. A plan does not
  authorize push, PR creation or merge, private data access, new paid services,
  credentials, or trading. Do not end a turn merely on dispatch acknowledgment
  while delegated work is outstanding.
- Do not end the coordinator process while an authorized PR is waiting for its
  exact-head review body. Keep the session alive and re-check until that body
  exists (pass, findings, or an explicit current limit). Timeout is not a review
  result. Check the review-comments API, not only issue comments.
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
