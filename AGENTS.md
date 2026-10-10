# AI Agent Rules

Canonical responsibility: repository invariants, authority boundaries,
research-safety review standards, the owner's process constraints, and writing
rules.

This repository is the simulation-only research phase of an automated
stock-selection program. Procedures and review rules live in
`docs/codex_long_running_controller.md`, standing owner grants in
`AUTHORITY.md`, product direction in `docs/north_star.md`, and the latest
checkpoint in `docs/current_handoff.md`. The Claude-herdr coordination
standard in `Codex/Standards/claude-herdr-coordination-standard/`
(`coordinator.md` and `model_bindings.json`) owns dispatch, review seats, and
model bindings; do not copy them here, and do not load
`Codex/Standards/archive/`.

## Authority And Scope

- No repository file grants authority to push, create or update a PR, request
  a review, merge, deploy, access private data, or take destructive action. Each
  needs explicit user or higher-level authorization for that action and scope.
  `AUTHORITY.md` records the owner's standing grants; agents never edit it.
- Never direct-push or direct-merge to `main`, bypass protections, checks, or
  reviews, or use administrative override flags.
- Preserve unrelated user changes; use a clean branch or worktree when the
  current tree is dirty.
- Never store secrets or raw private data in any checkout, in tracked,
  untracked, or ignored files.

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
- Review rounds and escalation follow the failure limit in section 5 of the
  standard's `coordinator.md`, with no separate round cap (owner, 2026-10-09).
  Wording, style, claims-file, and record findings are ADVISORY and go to the
  backlog. Reviewers also ask whether a rule drops data in a way that biases
  the sample.
- An R1–R12 finding has one of three tiers (owner decision of 2026-10-09):
  - Executed: a concrete trigger path exists on this project's data and
    stages (a named path, or a count above zero on the run-of-record data).
    It is MATERIAL and is fixed whatever its impact, zero included.
  - Latent: an actual count of zero on the run-of-record data, not an
    argument, shows that the violation needs inputs the project does not
    hold. It is ADVISORY but stays a defect. The backlog records the count
    and a revisit trigger: a new data vintage, reuse in a new stage, or a
    change to that code. Before that use, fix it or make it refuse.
  - R11 and R12: a leak of private material or an execution path is fixed
    before push or publication, with no exception. A record or wording item
    that an invariant needs is fixed in the next records change, at the
    latest before publication; it never reopens a reviewed code candidate.
- A design note of at most two pages replaces a binding plan unless the owner
  asks for a plan.
- The coordinator sets technical defaults and logs each one; no default loosens
  R1, R2, R4, R6, R8, or R9. The owner decides money, data access, legal terms,
  and goals.
- Work that cannot change a result or a decision in the current step waits.

## Writing Style And Syntax

- Everything written to the repository, to GitHub (PR titles and bodies,
  comments, commit messages), and to any report is English only; Chinese
  characters are prohibited there, and a test enforces it for tracked files. Only
  live chat with the owner uses the owner's language, in plain words.
- Write at about 80% of ASD-STE100 (Simplified Technical English).

## Engineering And Change Discipline

- Never remove, weaken, or skip tests to make a change pass. Add deterministic
  behavioral tests for calculation changes.
- Choose the simplest implementation that meets current requirements. Add no
  speculative registries, abstraction layers, or optional engine parameters
  without a consumer; reuse established libraries before writing custom code.
- Every milestone changes a real-data result or an owner decision. A factor
  catalog entry needs no consumer; other capabilities wait for the milestone
  that consumes them. When a capability, data source, or module is retired,
  delete its code in the same PR.
- Record strategy changes in `EXPERIMENT_LOG.md` or `PROJECT_SPEC.md`, process
  evidence in `docs/engineering_log.md` with the newest entry first, and durable
  choices in `docs/decision_log.md`. Keep bulky evidence out of Git.
- Every PR refreshes `docs/current_handoff.md` to its base. A test fails when
  the handoff trails the base by more than one merged PR.

## Continuation

Execute the next clear, already-authorized step without asking again. Stop for
a genuine blocker, missing authority, or a large owner choice. An explicit
owner STOP governs.
