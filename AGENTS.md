# AI Agent Rules

Canonical responsibility: repository invariants, authority boundaries,
research-safety review standards, writing-style rules, and ablation after
completed design or implementation.

This repository is the simulation-only research phase of an automated
stock-selection program. Procedures live in
`docs/codex_long_running_controller.md`, standing owner grants in
`AUTHORITY.md`, and product direction in `docs/north_star.md`.

## Authority And Scope

- Repository instructions define constraints and eligibility; they never expand
  current system, developer, user, or global authority.
- No repository file grants authority to push, create or update a PR, post a
  comment or review request, enable auto-merge, merge, close, deploy, access
  private data, or take destructive action. Each requires explicit user or
  higher-level authorization for that action and scope. `AUTHORITY.md` records
  the owner's standing grants; the owner is their source, and agents never edit
  that file.
- Unless the user narrows the request, an explicit instruction to create or
  publish a PR authorizes the normal protected lifecycle for that same PR:
  readiness transition, required review request, in-scope remediation
  publication, verified review-thread reply and resolution, and eligible normal
  merge. The user may revoke that lifecycle authorization at any time.
- Lifecycle authorization never covers another PR, scope expansion, auto-merge,
  administrative or protection bypass, deployment, private data, credentials,
  brokerage, or destructive action. Approval for a named PR or remediation
  keeps its stage and file scope.
- Never direct-push or direct-merge to `main`, bypass protections, checks,
  reviews, or a merge queue, or use administrative override flags.
- Preserve unrelated user changes. Do not reset, clean, overwrite, or hide them;
  use a separate clean branch or worktree when the current tree is dirty.
- Treat credentials, private data, licenses, account identifiers, and production
  systems as sensitive. Never store secrets or raw private data in the repo; the
  prohibition covers tracked, untracked, and ignored files in every checkout.
  R11 separately governs what may be published.

## Startup And Sources

- The coordination standard owns dispatch, lanes, reviewer routing, model
  bindings, quota, and visible-tab review. Before dispatch or review, read the
  three policy files in `Codex/Standards/coordination-standard/`:
  `coordinator.md`, `routing_table.json`, and `model_bindings.json`. Do not copy
  seats or bindings into this file. Do not load `Codex/Standards/archive/`.
- After `AGENTS.md`, for staged continuations through a thin routing Skill, read
  `docs/current_handoff.md`, `docs/codex_long_running_controller.md`, then
  `docs/current_roadmap.md` for checkpoint, execution gates, and program status.
- Use `docs/repo_map.md` for targeted orientation and verify cached handoff
  facts live. Read long logs or contracts only for the active stage, cap unknown
  output, and regenerate `docs/repo_map.md` when workflow changes alter it.

## Research Safety Invariants

The ultimate aspiration is automated stock selection and trading pursuing
sustainable risk-controlled long-term net returns. Stable profit is an
objective, not a guarantee. Invariants R1–R12 bind every layer, including demos
and diagnostics. Everything else may wait in the backlog in
`docs/current_roadmap.md`. A known defect stays a defect when a caveat is added.

- **R1 Timing.** Inputs are known before trading under
  `after_close_signal_next_observed_close_v1`. Distinguish feature, signal,
  rebalance, execution, and return dates, and test every boundary. Never use
  future returns, future fundamentals, or same-period target returns.
- **R2 Universe.** Eligibility uses only membership known at decision time. A
  static survivor cohort is permitted only under `DIAGNOSTIC_ONLY`, with the
  bias stated in each report header, and it never supports a ranking,
  selection, promotion, or profitability claim.
- **R3 Identity (PIT-005).** Fail closed on ticker reuse; never stitch returns
  across permanent securities. Vendor identifiers with fail-closed ambiguity
  handling suffice for diagnostics; unresolved SEC EDGAR lineage parsing never
  blocks diagnostic research.
- **R4 Disappearance (PIT-006).** No default last-price or zero-payoff exit. A
  held disappearance without accepted terminal evidence refuses the affected
  run or window.
- **R5 Distributions (PIT-007).** Use one total-return basis; never add cash
  dividends to an adjusted series.
- **R6 Missingness (PIT-009).** Missing values stay typed; no silent fill, clip,
  drop, or repair.
- **R7 Price and volume basis.** Dollar turnover, liquidity, and capacity use
  matching price and volume bases.
- **R8 Costs.** Apply explicit commission and spread or slippage under existing
  turnover conventions. Zero-cost or no-slippage results are diagnostics only.
- **R9 Trials.** Keep failed, weak, invalid, abandoned, and contrary results
  visible. Declare the trial family before results; never cherry-pick only the
  best parameter or trial.
- **R10 Claims.** Never invent results or claim profitability without
  reproducible evidence. Report excess over a declared benchmark at a stated
  evidence ceiling, and explain data provenance, missingness, costs, slippage,
  execution timing, benchmark choice, sample splits, and material limitations.
- **R11 Data and privacy.** Real/private-data access or interpretation requires
  accepted methodology, evidence gates, and explicit authorization. Publication
  follows the owner's written data terms: noncommercial aggregates may be
  public; raw provider rows, provider responses, provider-derived membership
  lists, credentials, and private paths stay private.
- **R12 Non-execution.** Keep this project simulated, auditable, reproducible,
  and explainable; never add brokerage connections, orders, paper/live trading,
  or live-account behavior. Execution belongs to a future, separately
  authorized private repository.

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

## Writing Style And Syntax

These rules bind every model and harness working in this repository.
Research-safety invariants and authority prohibitions keep their existing
wording.

- Every newly authored or edited repository document is English, including
  AGENTS, skills, logs, handoffs, and reports. Historical evidence keeps its
  original bytes. User-facing chat may use the user's preferred language.
- Use direct affirmative construction: state what things are, and let the first
  clause state the conclusion.
- Definition by negation is banned. False-dichotomy templates are banned: "not
  just X, but Y"; "not merely X, but rather Y"; "it is not about X, it is about
  Y". Strawman antithesis is banned.
- When a Mermaid diagram shows structure more clearly than prose, use it.
- Reports, handoffs, and section closings state completed facts and current
  measurements.

## Engineering And Change Discipline

- State scope before editing; afterward report files, tests, caveats, and the
  next gate. Keep branches, PRs, and commits coherent; separate unrelated change
  types.
- Never remove, weaken, or skip tests to make a change pass. Add deterministic
  tests for feature, strategy, portfolio, accounting, or reporting calculation
  changes; prefer behavioral tests over source-text assertions.
- Walking skeleton first: keep one working thread from data through factor,
  statistics, portfolio backtest, and evidence report, and grow it in working
  layers.
- Milestone admission: every milestone changes a real-data result or an owner
  decision within that milestone. A capability without a real-data consumer
  waits for the milestone that consumes it.
- Choose the simplest implementation that meets current requirements. Add no
  speculative registries, capability minting, recursive abstraction layers, or
  optional engine parameters without a consumer. Reuse existing dependencies and
  established libraries before writing custom code.
- When data or infrastructure is blocked, unblocked modules proceed on
  synthetic golden fixtures.
- Record strategy changes in `EXPERIMENT_LOG.md` or `PROJECT_SPEC.md`, process
  evidence in `docs/engineering_log.md` with the newest entry first, and durable
  choices in `docs/decision_log.md`. Commit summaries and hashes; keep bulky
  evidence such as full test logs and multi-megabyte attempt files out of Git.
- Every PR refreshes `docs/current_handoff.md` to its base. A test fails when
  the handoff trails the base by more than one merged PR.

## Owner Corrections And Continuation

- When the owner identifies a process failure, acknowledge it, record the
  incident in `docs/engineering_log.md`, update the rule in its owning document,
  and continue the still-authorized task. Invariants belong here; procedures and
  the process-failure list belong in the controller.
- Execute the next clear, already-authorized step without repeat permission.
  Stop for a genuine blocker, missing or additional authority, or a large
  unresolvable owner-semantic choice. An explicit owner STOP governs.

## Ablation

After every completed design or implementation, run an ablation experiment.
Remove unnecessary abstractions, speculative design, and surplus code. Keep the
simplest implementation that still meets current requirements.

Preserve the baseline. Test each removal in isolation. Compare behavior,
correctness, and relevant costs. Keep justified simplifications. Restore
regressions. Keep necessary tests, validation, and guards.

Report at least one simplification attempt separately from guard-necessity
checks. Record removals, retained necessities, and known limitations. A
supported no-change outcome is valid. Ablation revalidation is not a recursive
ablation loop.

For ablations that replace array traversal, test every public boundary's
empty-axis shapes (Nx0, 0xM, and 0x0), duplicate or named axes, and mixed
scalar identity; compare public cells, state digests, and refusal reasons. A
whole-project ablation completion claim requires a runtime and subsystem
coverage matrix, tested high-impact hypotheses, preserved baseline and negative
evidence, and a limitations assessment.
