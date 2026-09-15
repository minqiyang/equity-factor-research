# Project Specification

## Objective And North Star

The ultimate aspiration of the project is automated stock selection and trading,
pursuing sustainable risk-controlled long-term net returns. Stable profit is an
explicit objective, not a guarantee.

The research and simulation platform built in this repository is the foundational
first phase—not the final execution product. The repository remains strictly
simulated and non-order-capable; live trading, broker integrations, and order
routing belong to a future, separately authorized private execution system.

The engineering approach is **demo-first**: ship a basic, presentable, and
reproducible end-to-end version first, record non-blocking imperfections in a
lightweight backlog, and improve in layers. We avoid blocking a working
demonstration on an ideal pipeline, complete SEC identity proof for every
security, optional ledger/schema coverage, or a broad factor zoo. Canonical
minimum correctness and non-negotiable boundaries are defined exclusively in
[AGENTS.md Research Safety Invariants](AGENTS.md#research-safety-invariants) and the
[blocking backlog table](docs/current_roadmap.md#imperfection-policy-and-lightweight-backlog),
enforced at every layer (with Demo v0 maintaining All-Attempt Case Logging rather
than formal Stage 4 complete ledger accounting).

Optimize the research process for evidence quality rather than the highest
historical Sharpe ratio. Retain negative, failed, invalid, and inconclusive
results.

`docs/north_star.md` is the active product aspiration and demo-first delivery policy.
`docs/research_program_charter.md` is the preserved historical formal evidence policy.
`docs/current_roadmap.md` is the active staged delivery plan.
`docs/signal_execution_timing_contract.md` is the accepted Stage 2 timing
authority. Stage 2b implements it with required, role-bound, immutable source
provenance whose caller-declared baseline is captured before later mutation,
plus a controlled coordinate ledger for any later source write. Enforcement
begins at capture and cannot reconstruct pre-capture history.
`docs/point_in_time_data_methodology_contract.md` is the accepted Stage 3
provider-agnostic data authority. It separates acceptance of the methodology
contract from review of a particular immutable dataset manifest and from
eligibility for formal interpretation.
`docs/experiment_trial_ledger_contract.md` is the accepted Stage 4a design
authority. It separates semantic trials from execution attempts, freezes
allocation-before-action and access-intent-before-read semantics, and requires
append-only completeness plus independently retained evidence and adjudication
checkpoints.
`docs/experiment_trial_ledger_schema_registry_contract.md` defines the
protected-main Stage 4B-R0 fail-closed registry foundation. R0 supports only
the exact epoch schema, rejects the other 36 known events as
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`, and does not claim a complete payload
registry or Stage 4b runtime enforcement.
The owner-approved diagnostic exception in
`docs/eodhd_sp500_diagnostic_campaign_contract.md` superseded the registry-first
delivery dependency only for historical Track A. It did not change the immutable ledger
contracts or make a diagnostic result formally eligible.
`docs/experiment_trial_ledger_allocation_registration_schema_contract.md`
defines the owner-selected Stage 4B-R1A architecture-A decision. It preserves
R0 unchanged, retains the 37-event vocabulary, selects reservation-only
campaign/experiment allocation, entity subjects, explicit campaign scope, a
versioned closed R1 schema-language path, and requirements for future exact
reference-based family and Stage 3 sample authorities. R1A accepts neither
authority and is design-only: it promotes no event, creates no trial or
access, and leaves Stage 4b runtime and Stage 5 blocked.
The same contract now contains the bounded Stage 4B-R1B implementation
authority. The owner ratified `exp_<32 lowercase hex>` as the exact experiment
namespace. A separate immutable registry/schema-language `0.2.0` release
supports only epoch plus reservation-only campaign and experiment allocation,
keeps the other 34 events `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`, and preserves
the R0 artifacts, default entry point, and behavior. Shape validation does not
implement allocation, append, parent existence, uniqueness, authorization,
campaign execution, or research interpretation.
`docs/experiment_trial_ledger_trial_family_registration_schema_contract.md`
defines the owner-selected Stage 4B-R1C-A trial-family registration authority.
It freezes `fam_<32 lowercase hex>`, a common direct-scope maximum of 32,
retrieval of complete repository-external canonical family definitions through
an exact digest-pinned authority tuple, a separate immutable acceptance record
with reviewer independence, stable global family identity, monotonic current
acceptance generations, explicit `supersedes`/`depends_on` relations, and
anti-reset rules. A separate immutable registry `0.3.0` promotes only
`TRIAL_FAMILY_REGISTERED`, keeps the other 33 events incomplete, and preserves
R0/R1 bytes and behavior. Local schema acceptance proves only closed event
shape; retrieval, authority, acceptance currentness, role independence,
history, and append behavior remain fail-closed stateful requirements.
`docs/experiment_trial_ledger_sample_registration_schema_contract.md` defines
the owner-selected Stage 4B-R1D-A local sample-registration authority. It
freezes `smp_<32 lowercase hex>`, the existing direct-scope maximum of 32, an
exact digest-pinned repository-external Stage 3 sample authority, a separate
non-self-issued acceptance record, allowlisted public projection and
publication-approval references, single-current generations, mutually
exclusive local/global/external representation paths, and anti-reset overlap
semantics. A separate immutable registry `0.4.0` promotes only
`SAMPLE_REGISTERED`, keeps both binding events and the other 30 events
incomplete, and preserves R0/R1/R2 bytes and behavior. Local schema acceptance
proves only closed event shape; retrieval, authority, acceptance and
publication currentness, role independence, path exclusivity, exposure
history, prior allocation, and append behavior remain fail-closed stateful
requirements.
`docs/experiment_trial_ledger_binding_schema_contract.md` defines the
owner-selected Stage 4B-R1E-A binding authority. A separate immutable registry
`0.5.0` preserves R0/R1/R2/R3 bytes and behavior while promoting only
`CAMPAIGN_ENTITY_BOUND` and `STAGE3_SAMPLE_REFERENCE_BOUND`. Campaign binding
uses a closed outer subject union and, for samples, a closed local-registration
versus external-reference source union. The first external Stage 3 reference
allocates one `smp_<32 lowercase hex>` identity for one campaign; later
campaigns reuse that same external-origin identity only by binding the exact
first event ID/hash. Local schema acceptance proves only event shape and
reference syntax; retained-source bytes/digests, prior campaign allocation,
authority/currentness, path exclusivity, anti-reset history, uniqueness, and
append behavior remain fail-closed stateful requirements.
`docs/experiment_trial_ledger_trial_allocation_schema_contract.md` defines the
owner-selected Stage 4B-R1F-A semantic trial-allocation authority. A separate
immutable registry `0.6.0` preserves R0/R1/R2/R3/R4 bytes and behavior while
promoting only `TRIAL_ALLOCATED`. It freezes `trl_<32 lowercase hex>`, one
singleton campaign scope, exact earlier campaign/experiment/family/sample
evidence, a complete repository-external canonical trial definition and
independent acceptance/publication/actor-authority records, closed
original/child/clone/rerun relations, and closed clean-commit/dirty-tree code
identity. Local schema acceptance proves only closed event shape; parent
existence and order, external retrieval and currentness, reviewer
independence, actor authority, relation acyclicity, code-byte retention,
uniqueness, append behavior, and pre-action enforcement remain fail-closed
stateful requirements.
`docs/experiment_trial_ledger_campaign_inventory_seal_schema_contract.md`
defines the owner-selected Stage 4B-R1G-A initial campaign-inventory-seal
authority. A separate immutable registry `0.7.0` preserves R0 through R5 bytes
and behavior while promoting only `CAMPAIGN_INVENTORY_SEALED`. It pins a
complete repository-external canonical inventory record, separate independent
acceptance, seal-actor authority, exact campaign allocation, singleton scope,
the nonrecursive `campaign_inventory_preseal_head_v1`, and a 4096-trial
schema/review bound. Local schema acceptance proves only closed event shape;
record retrieval, all-and-only inventory completeness, reviewer independence,
authority/currentness, predecessor-head comparison, exact sequence arithmetic,
single-seal uniqueness, atomic append, and pre-action enforcement remain
fail-closed stateful requirements.
`docs/experiment_trial_ledger_attempt_allocation_schema_contract.md` defines
the owner-selected Stage 4B-R1H-A attempt-allocation authority. A separate
immutable registry `0.8.0` preserves R0 through R6 bytes and behavior while
promoting only `ATTEMPT_ALLOCATED`. It freezes
`att_<32 lowercase hex>`, singleton campaign scope, exact earlier
trial-allocation and initial inventory-seal evidence, a complete
repository-external canonical attempt plan, separate independent acceptance
and allocation-actor authority records, and closed first-attempt/retry
relations. Local schema acceptance proves only closed event shape; source
existence/order, external retrieval/currentness, reviewer independence, actor
authority, unique monotonic ordinals, terminal retry predecessor, retry
permission/budget, durable append, and the pre-action barrier remain
fail-closed stateful requirements.
`docs/experiment_trial_ledger_attempt_start_schema_contract.md` defines the
owner-selected Stage 4B-R1I-A attempt-start authority. A separate immutable
registry `0.9.0` preserves R0 through R7 bytes and behavior while promoting
only `ATTEMPT_STARTED`. It binds the exact earlier attempt-allocation event,
semantic trial, singleton campaign scope, a complete repository-external
canonical readiness record, separate start-actor authority, and one
ledger-owned `cap_<32 lowercase hex>` one-shot execution-capability identity
with a complete private external record. Exact lost-ack replay returns the
same start/capability identity, and future execution may begin only after a
durable start plus one atomic capability consumption. Local schema acceptance
proves only closed event shape; source order, external retrieval, literal
readiness truth, effective-principal role independence, authority/currentness,
single-start history, atomic capability mint, idempotency, consumption,
durable append, execution, artifact, access, and research behavior remain
fail-closed stateful requirements.
R1I is complete on protected main through PR #176 at `6386c59`. The accepted
37-event vocabulary and immutable releases are preserved as optional
`full_ledger_profile_v1`; completing 37/37 was not required before the historical
bounded Track A campaign or the later minimal Track B runtime.

`docs/eodhd_sp500_diagnostic_campaign_contract.md` defines the preserved
historical Track A/Track B diagnostic campaign protocol. Track A froze exactly
three price-only factors and 14 semantic trials, using purged bounded historical
evaluation, dependence-aware inference, fixed cost cases, complete result retention,
and a repository-external content-addressed evidence bundle (whose 14-trial
empirical run received a terminal REFUSED outcome on data provenance/lineage).
Track B was defined as a later 8-12-event-family stateful runtime required before
prospective performance access or formal promotion. This campaign contract remains
preserved historical protocol context, not the active delivery queue (which is
Milestone 2 Demo v0 in `docs/north_star.md` and `docs/current_roadmap.md`).

## Current Phase and Boundary

The current phase is research-only.

- No brokerage connection, orders, paper deployment, live deployment, or
  real-money execution.
- Current research work performs no vendor download, credential use, remote data
  access, or unauthorized real-data/result-bearing performance calculation. (This
  documentation task produced no new empirical strategy-performance results; existing
  synthetic fixture diagnostics and unit-test cost accounting remain permitted). Any future
  private entitlement/capability probe and acquisition may proceed only through the
  campaign contract's explicit license, privacy, purchase, and blinded dataset-acceptance gates.
- The public repository may use synthetic data, committed fixtures, and local
  data only under explicit privacy and methodology gates.
- `lean/` remains a non-executing scaffold until a future `PORTFOLIO_PASS`
  candidate and a separate scope decision authorize parity work.

## Evidence Layers

The project distinguishes:

1. **Factor:** a date-by-asset score and its incremental cross-sectional
   information.
2. **Strategy:** a frozen signal, selection, holding, rebalance, and execution
   rule.
3. **Portfolio:** strategies under benchmark, weighting, exposure, liquidity,
   concentration, capacity, and risk constraints.
4. **Execution:** target-to-order-intent, fill, cost, position, and
   reconciliation behavior.

Evidence from one layer does not certify the next layer. Passing deterministic
tests proves implementation behavior, not historical validity.

## Data and Universe Requirements

- Asset class: listed equities.
- Initial formal baseline: liquid US common stocks, subject to an accepted
  point-in-time universe definition.
- Initial strategy posture: long-only. Long-short research requires a separate
  borrow and shortability contract.
- Every feature must use information available by its declared signal
  availability timestamp.
- Formal data must record provider and license, version/hash, retrieval time,
  permanent identifiers, historical membership, delistings, mergers, ticker
  changes, corporate actions, raw/adjusted field semantics, filing/publication
  times, revision policy, missing/stale behavior, calendar/timezone, benchmark,
  risk-free policy, canonicalization and environment identity, an immutable
  non-self-issued dataset-review decision, and the private-data boundary.
- A static survivor cohort may be used for diagnostics but not presented as
  point-in-time universe evidence.

No research-grade provider is selected by this specification.
Stage 3 contract acceptance is methodology-process evidence. Dataset review,
entitlement, historical validity, and formal interpretation remain later
accepted records.
A dataset-specific private manifest, safe public projection, and
exact-version immutable review decision issued by an authorized
non-producing reviewer must satisfy the Stage 3 contract for one declared
use. Later trial, statistical, cost, privacy, and evidence-layer gates remain
independently required.

## Factor Program

Begin with interpretable baselines:

- momentum and reversal variants;
- realized and idiosyncratic volatility;
- beta;
- liquidity, turnover, and Amihud-style measures;
- size;
- value;
- profitability and quality;
- investment;
- leverage; and
- volume shocks.

Fundamental factors may enter formal campaigns only after point-in-time filing
availability is supported.

WorldQuant-style formulas enter in reviewed batches of 5-10 by compatible data
family. Every factor requires source traceability, exact formula, expected
direction, required fields, availability lag, parameters, horizon,
preprocessing, neutralization, missing policy, golden fixture, timing tests,
known limitations, and a trial family. A factor implementation is not a
strategy or profitability claim.

## Timing and Sample Isolation

- Record feature time, signal availability, decision, execution, label start,
  label end, and return measurement end.
- Signal inputs must be known before the declared execution time.
- Under the accepted close-only contract, a close-derived signal becomes
  available strictly after its stamped close, the earliest supported idealized
  target reset is the next observed source-row close, and the target first
  earns the following close-to-close return.
- Close-derived daily signals require a non-boolean integer lag of at least one
  observed source row. Lag zero requires a different typed and reviewed
  execution model and is not authorized implicitly.
- Use bounded development, validation, and evaluation windows.
- Purge labels that cross split boundaries; add embargo when overlapping
  labels or the accepted dependence model requires it.
- Keep feature warm-up/down history separate from measured evaluation periods.
- Preserve exact alignment among raw data, factors, ranks, target returns,
  weights, benchmark returns, and reported metrics.
- Never use future prices, future membership, future fundamentals, later
  revisions, future corporate actions, or same-period target returns as
  features.

These timing rules are normative. The Stage 2b backtester rejects zero and
invalid lag types, requires exact full-source axes and exact inclusive
evaluation bounds, requires source provenance captured after final panel
construction as the caller-declared baseline before later mutation, validates
only bounded final-signal values,
freezes targets without execution-close reranking, validates held endpoints
and frozen trade legs in their declared order, and gives period metrics one
common post-anchor window. Untracked source writes fail closed. Typed metadata
and a deterministic timing ledger expose the resolved schedule and
signal/holding intervals. Direct/nested provenance objects are rejected by the
experiment-log serializer, while current committed logs contain only the
allowlisted provenance policy/status; extracted primitives remain a caller
responsibility. This implementation conformance is software evidence only;
exchange-calendar, point-in-time data, cost-capacity, and empirical-validity
gates remain open.

Every protected-sample access must enter the holdout exposure ledger. Previously
examined data is `historical_evaluation` or `pseudo_holdout`, not an untouched
holdout.

Viewing asset or benchmark levels, corporate-action inputs, returns, labels,
or any other data from which protected outcomes can be reconstructed is
protected-sample access, not metadata-only intake.

The private diagnostics covering 2025-05-01 through 2026-05-31 are confirmed
historical access and are classified `historical_evaluation`; that interval
cannot be upgraded to a pristine holdout. Stage 3 defines the exposure schema
and downgrade rules. Stage 4 must implement append-only, pre-access allocation
and completeness enforcement.

## Backtesting Principles

- Use explicit rebalancing and execution dates.
- Apply trades only after signals are available.
- State next-open, next-close, auction, or other execution assumptions.
- Keep target weights, drifted holdings, trades, turnover, costs, and residual
  cash auditable.
- Compare against a preregistered investable benchmark and simple baselines.
- Include explicit transaction costs, slippage, capacity, and stress cases
  before promotion.
- Treat zero-cost or no-slippage output as diagnostic only.
- Define missing, stale, suspended, delisted, and infeasible-target behavior.
- Preserve drift-aware accounting identities.

## Trial and Statistical Discipline

Before a formal run, allocate immutable campaign, experiment, global
trial-family, semantic-trial, and execution-attempt IDs under
`docs/experiment_trial_ledger_contract.md`. Record every configured variation,
invocation, retry, failure, abort, invalid/excluded run, data revision, output
disposition/hash, review outcome, selection decision, and protected-sample
access. Trial completion is an execution state, not a research pass. Do not
report only the best configuration.

Formal validation is staged to include:

- IC, Rank IC, dispersion, ICIR, and sign hit rate;
- quantile returns, monotonicity, coverage, and decay;
- HAC/Newey-West and block/bootstrap inference where appropriate;
- permutation/placebo and leave-out stability checks;
- FDR or another registered multiple-testing adjustment;
- Deflated Sharpe Ratio;
- PBO/CSCV or a reviewed practical alternative; and
- purged walk-forward evaluation with a frozen candidate set.

The exact inference method and thresholds must be preregistered before protected
results are viewed.

## Evaluation Framework

Use a multi-objective framework appropriate to the evidence layer:

- net active return;
- Sharpe and Information Ratio with stated assumptions;
- maximum drawdown, downside risk, and CVaR;
- turnover, cost sensitivity, and capacity;
- concentration and benchmark, sector, beta, size, and style exposures;
- fold, subperiod, universe, and parameter stability;
- statistical uncertainty and multiple-testing-adjusted evidence;
- simplicity and economic rationale; and
- later local-to-LEAN parity.

If future-winner recall is studied, predefine the positive class and report
Precision@K, Recall@K, NDCG, Rank IC, breadth, turnover, and net portfolio
results together. Never optimize recall alone.

## Candidate States

Use exactly one evidence state for each evaluated object:

`INVALID`, `INCONCLUSIVE`, `REJECTED`, `DIAGNOSTIC_ONLY`, `CONDITIONAL`,
`RESEARCH_PASS`, `PORTFOLIO_PASS`, `PAPER_CANDIDATE`, or `LIVE_CANDIDATE`.

Use the lowest state supported by completed gates. A candidate label is not
authorization to paper trade or trade live.

Track A uses only `INVALID_DIAGNOSTIC`, `INCONCLUSIVE_DIAGNOSTIC`,
`NEGATIVE_DIAGNOSTIC`, `MIXED_DIAGNOSTIC`, or `POSITIVE_DIAGNOSTIC`. None of
those states is `RESEARCH_PASS` or evidence of alpha, profitability, broader
market validity, paper readiness, or live readiness.

## Operational Modes

The project operates under two clearly bounded modes to prevent conflating exploratory demo development with formal empirical promotion:

1. **Exploratory Demo Mode (Demo-First Delivery)**:
   - Target deliverable for active Milestone 2 (not yet implemented): will deliver a basic, presentable, and reproducible end-to-end slice (Demo v0) showing simulated stock selection, portfolio holdings, benchmark comparison, explicit frictional costs, and diagnostic reporting.
   - Planned to run locally on committed synthetic fixtures without private data. Any separately authorized local CSV runs remain explicitly exploratory and diagnostic.
   - Non-blocking imperfections and data caveats are recorded in the canonical lightweight backlog in [docs/current_roadmap.md](docs/current_roadmap.md#imperfection-policy-and-lightweight-backlog) and improved in layers.
   - Results are diagnostic only; no claims of market alpha, general predictability, or trading profitability.

2. **Formal Research Promotion Mode**:
   - Applies strict point-in-time corporate-action reconciliation, survivorship-bias-free universe construction, complete all-trial append-only ledger enforcement, purged/embargoed sample splits, and multiple-testing inference.
   - A mandatory prerequisite before promoting a factor, strategy, or portfolio to `RESEARCH_PASS` or claims of empirical robustness.
   - Not a blocker for demonstrating an initial, visibly caveated exploratory demo slice.

## Imperfection Policy And Backlog

To balance rigorous research hygiene with demo-first engineering velocity, imperfections are handled under an explicit classification:
- **Safe to defer**: Presentation polish, extra factor families, optional ledger schema breadth beyond demo needs, advanced multiple-testing packages beyond demo claims, and exhaustive historical entity lineage proofs (provided the actual claimed calculation remains valid without fabricating economics).
- **Non-deferrable (Demo-blocking)**: Identity mis-stitching and ticker reuse, future-membership selection and survivor-cohort filtering (no historical eligibility selected by future continuity or survivor cohorts; unverified diagnostics labeled explicitly survivorship-biased; no claim of a survivorship-free universe until Milestone 4), silent fill/clip/drop/repair, default last-price or zero-payoff disappearance (PIT-006; if accepted terminal evidence is absent, the affected window blocks), dividend double counting, incompatible price/volume dollar turnover, lookahead leakage or timing mismatch, incorrect cost/return math, falsified or cherry-picked results, unhedged/leaked private data, and live execution or brokerage integration. A known defect is not made safe merely by adding a caveat.

The complete, single authoritative imperfection backlog table is maintained exclusively in
[docs/current_roadmap.md#imperfection-policy-and-lightweight-backlog](docs/current_roadmap.md#imperfection-policy-and-lightweight-backlog).
See that document for active row-level caveats, handling rules, revisit triggers, and blocking boundaries.

## Primary Milestones

The program follows a five-milestone sequence from foundational research to simulated demo delivery and future execution. Program stage sequence, status, gate and completion criteria are owned exclusively by [docs/current_roadmap.md#primary-milestones](docs/current_roadmap.md#primary-milestones).

Detailed Demo v0 acceptance requirements for active Milestone 2:
1. **Single Command/Workflow**: One reproducible local command or workflow using an existing price-only factor and one fixed strategy configuration.
2. **End-to-End Simulation**: Generates simulated selection and holdings with drift-aware portfolio accounting.
3. **Transparent Reporting**: Produces a human-readable comparison report with benchmark comparisons, explicit frictional cost and timing models, risk metrics, and stated limitations.
4. **All-Attempt Case Logging**: Records all attempted cases in a reproducible log (all-attempt case logging is mandatory; cherry-picking or omitting failed trials is strictly forbidden; distinguishes lightweight diagnostic run logging from Stage 4 complete immutable ledger accounting).
5. **Demonstrable on Synthetic Fixtures**: Runnable without requiring private data. Any separately authorized local-data run remains explicitly exploratory.

## Explicit Non-Goals

- No live trading or real-money execution.
- No brokerage integration, credentials, or order placement.
- No paper deployment under the current phase.
- No self-modifying production strategy.
- No black-box strategy oracle.
- No unsupported claims of alpha, profitability, robustness, investment
  value, or readiness.
- No parameter mining presented as discovery.
- No best-only result reporting.
- No hidden manual edits or removal of failed evidence.
- No external data fetching without separate explicit authorization.
