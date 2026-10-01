# AI Agent Rules

Canonical responsibility: repository invariants, authority boundaries,
research-safety review standards, the owner's process constraints, writing
rules, and ablation.

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

- The coordination standard owns dispatch, reviewer routing, model bindings,
  quota, and visible-tab review. Before dispatch or review, read the three
  policy files in `Codex/Standards/coordination-standard/`: `coordinator.md`,
  `routing_table.json`, and `model_bindings.json`. Do not copy seats or
  bindings into this file. Do not load `Codex/Standards/archive/`. The owner's
  process constraints below set which work in this repository needs which gate.
- After `AGENTS.md`, for staged continuations through a thin routing Skill, read
  `docs/current_handoff.md`, `docs/codex_long_running_controller.md`, then
  `docs/current_roadmap.md` for checkpoint, execution gates, and program status.
- Use `docs/repo_map.md` for targeted orientation and verify cached handoff
  facts live. Read long logs or contracts only for the active stage, cap unknown
  output, and regenerate `docs/repo_map.md` when workflow changes alter it.

## Research Safety Invariants

The North Star is in `docs/north_star.md`. Invariants R1–R12 guard against fake
backtest profits at every layer, including demos and factor-timing studies.
Everything else may wait in the `docs/current_roadmap.md` backlog. A known
defect stays a defect when a caveat is added.

- **R1 Timing.** Inputs are known before trading under
  `after_close_signal_next_observed_close_v1`. Distinguish feature, signal,
  rebalance, execution, and return dates, and test every boundary with a
  future-perturbation test. Fundamentals are usable from filing date plus one
  trading day; macro series carry their release lag. Never use future returns,
  revised or retrospectively dated series (such as NBER recession flags),
  full-sample standardization, or same-period target returns as inputs.
- **R2 Universe.** Eligibility uses only membership known at decision time,
  including members later removed, acquired, or bankrupt. A static survivor
  cohort is permitted only under `DIAGNOSTIC_ONLY`, with the bias stated in each
  report header, and it never supports a ranking, selection, promotion, or
  profitability claim.
- **R3 Identity (PIT-005).** Fail closed on ticker reuse; never stitch returns
  across permanent securities. Vendor identifiers with fail-closed ambiguity
  handling suffice; unresolved SEC EDGAR lineage parsing never blocks research.
- **R4 Disappearance (PIT-006).** A held disappearance uses accepted terminal
  evidence when it exists and otherwise a declared side-aware adverse default:
  a cash acquisition settles at the last close or the deal price; a failure or
  unknown cause settles at −100% for a long position and at the last close plus
  30% for a short position, or the run makes no long-short claim. The benchmark
  uses the same rule. The report states the count and weight share affected
  and a rerun with the last close for all; a sign flip labels the result fragile.
- **R5 Distributions (PIT-007).** Use one total-return basis; never add cash
  dividends to an adjusted series.
- **R6 Missingness (PIT-009).** Missing values stay typed; no silent fill, clip,
  drop, or repair. Bad data blanks every window that touches it, lookbacks and
  holding periods included, and the report states the blanked or unpriced share
  split by later exit class.
- **R7 Price and volume basis.** Dollar turnover, liquidity, and capacity use
  split-only close times split-adjusted volume, checked by one split-continuity
  test.
- **R8 Costs.** Apply explicit commission and spread or slippage under existing
  turnover conventions, and a switch cost for factor-allocation rules. State
  borrow cost for shorts. Zero-cost results are labelled gross diagnostics.
- **R9 Trials.** Commit the trial family before results; append every run; keep
  failed, weak, invalid, abandoned, and contrary results visible. The
  multiple-testing correction counts every tested variant, and its method is
  fixed before results. Exploratory screens are fully visible; a confirmatory
  shortlist of at most ten is frozen before its confirmation data is opened, and
  confirmation uses months the screen never used.
- **R10 Claims.** Never invent results or claim profitability without
  reproducible evidence. Report excess over a declared benchmark at a stated
  evidence ceiling, with q-values beside any ranking, and state data provenance,
  missingness, costs, execution timing, sample reuse, and material limitations.
- **R11 Data and privacy.** Private-data access requires explicit owner
  authorization. Public academic factor libraries and FRED series are authorized
  for download and interpretation. Publication follows the owner's written data
  terms: noncommercial aggregates may be public; raw provider rows, provider
  responses, provider-derived membership lists, raw third-party files,
  credentials, and private paths stay private; commit a manifest and hashes.
- **R12 Non-execution.** Keep this project simulated, auditable, and
  reproducible; simulated factor-selection and factor-timing strategies are in
  scope. Never add brokerage connections, orders, paper/live trading, or
  live-account behavior; execution belongs to a separate future repository.

## Owner Process Constraints

Owner decision of 2026-09-28: the fastest route to the North Star, R1–R12 intact.

- Two formal review seats from different model families are required only for
  code on the real-data path that computes signals, returns, identity, costs, or
  statistics, and for a trial-family freeze. Other code gets one seat. Docs,
  records, and catalogs get coordinator verification.
- At most two review rounds per card. Wording, style, claims-file, and record
  findings are ADVISORY and go to the backlog. Reviewers also ask whether a
  rule drops data in a way that biases the sample.
- A design note of at most two pages replaces a binding plan unless the owner
  asks for a plan.
- The coordinator sets technical defaults and logs each one; no default loosens
  R1, R2, R4, R6, R8, or R9. The owner decides money, data access, legal terms,
  and goals.
- Work that cannot change a result or a decision in the current step waits.

## Review Priorities

- Prioritize research-validity risk over style. A P1 requires concrete evidence
  from changed code, tests, or documentation; touching a factor input alone is
  not evidence of leakage.
- Flag as P1 an unsupported completed claim or a concrete mismatch in signal,
  execution, return-window, benchmark, portfolio accounting, or leakage timing.
- Flag as P2 undocumented implemented/tested behavior, partial work called
  complete, stale next steps, or missing sparse/empty/invalid-data, cost,
  turnover, benchmark, or calendar edge tests unless evidence creates P1 risk.
- Ignore typos unless meaning changes. Flag unexplained Unicode/control changes.
  Every finding cites the file and claim, evidence, impact, and a fix or test.

## Writing Style And Syntax

- Everything written to the repository, to GitHub (PR titles and bodies,
  comments, commit messages), and to any report is English only; Chinese
  characters are prohibited there, and a test enforces it for tracked files. Only
  live chat with the owner uses the owner's language, in plain words.
- Lead with the conclusion. Use a Mermaid diagram when it shows structure more
  clearly than prose. Reports and handoffs state completed facts and current
  measurements.

## Engineering And Change Discipline

- State scope before editing; afterward report files, tests, caveats, and the
  next gate. Keep branches, PRs, and commits coherent; separate unrelated change
  types.
- Never remove, weaken, or skip tests to make a change pass. Add deterministic
  tests for feature, strategy, portfolio, accounting, or reporting calculation
  changes; prefer behavioral tests over source-text assertions.
- Walking skeleton first: keep one working thread from data through factor,
  statistics, portfolio backtest, and report, and grow it in working layers.
- Milestone admission: every milestone changes a real-data result or an owner
  decision. A factor catalog entry needs no consumer; a factor run once in a
  declared screening family counts as consumed. Other capabilities without a
  real-data consumer wait for the milestone that consumes them.
- Choose the simplest implementation that meets current requirements. Add no
  speculative registries, abstraction layers, or optional engine parameters
  without a consumer; reuse established libraries before writing custom code.
- When data or infrastructure is blocked, unblocked modules use synthetic fixtures.
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

Ablation runs only when a milestone retires a capability or data source, a scan
finds a module with no consumer, production code grows sharply, or the owner
asks. Start with cheap static checks; cap a pass at 20 million tokens and two
subagents; target whole modules, stages, rules, and unused evidence. Verify with
one combined recompute against the baseline, restore regressions, keep the guards
R1–R12 require, and record removals. No change is a valid outcome.
