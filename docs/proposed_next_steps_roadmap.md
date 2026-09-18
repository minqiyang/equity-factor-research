# Proposed Next Steps After M3-08

The recommended first step is a test-only synthetic split proof through Demo
v0 and M3-01, reusing the committed split golden and existing accounting.
This step requires no new owner semantic choice. Its execution belongs to the
next authorized task; the present delivery ends with guidance and a local
commit.

Proposal date: 2026-09-17. Source HEAD:
`1a3cee50b2fa508f86d605d2cb9adb178f5f0263`.
[The assessment](../reports/program_assessment_20260917.md) records delivered
behavior and source locations. [The current roadmap](current_roadmap.md)
continues to own milestone status, execution gates, and the imperfection
backlog. The numbered steps below are proposed work slices; their numbers
create no new canonical milestone IDs.

## Fixed boundaries for every proposed slice

- Work remains synthetic and simulated, using existing dependencies and
  accepted timing, benchmark, turnover, and cost conventions.
- `DEMO_V0_CONFIG` and M3-01 `FROZEN_CONFIG` remain unchanged. Test fixtures may
  use explicit `dataclasses.replace` overrides and temporary output paths;
  official commands retain their frozen defaults. Any proposal to change an
  official configuration requires a separately scoped owner decision before
  implementation or report regeneration.
- Existing source dates and prices remain intact. Every attempted run retains
  its outcome, including refusal, interruption, and negative evidence.
- PIT-005 identity integrity, PIT-006 terminal evidence, PIT-007 double-count
  prevention and compatible field bases, PIT-009 typed missingness, timing,
  sample honesty, and privacy remain mandatory.
- Private data, provider downloads, credentials, calendar construction,
  corporate-action adjustment engines, new cost engines, brokerage, and
  paper/live execution stay outside these synthetic slices. Formal promotion
  and profitability claims remain closed.

## 1. Extend the accepted split golden through both demo consumers

**Objective:** Add one deterministic proof that both demo pipelines preserve
the economics of an already adjusted synthetic split series, together with a
raw-price contamination counterexample. Deliver tests and a concise evidence
record; preserve runtime behavior.

**Why now:** M3-08 proves date membership and input preservation. The existing
campaign golden already fixes adjusted held returns, drift, turnover, and
cost expectations around a split. Binding those expectations to the demo
consumers advances the remaining adjustment question with a small, bounded
experiment. This proof establishes consumption of a declared adjusted series;
independent event reconciliation remains the subject of later steps.

**Inputs/files:** Open
`tests/fixtures/campaign_runner_v1/split_corporate_action.json`,
`tests/test_campaign_paths.py`, `tests/test_event_date_membership.py`,
`tests/test_dividend_policy.py`, `research/dividend_policy.py`,
`research/demo_v0.py`, `research/synthetic_multifactor_backtest_demo.py`, and
`src/backtest/portfolio.py`. Use the existing test-only injection pattern and
the shared regression files in the assessment map. Preserve the original
golden bytes. A new focused test file is sufficient if the existing tests
would become harder to read.

**Acceptance tests:**

- Supply enough synthetic warm-up and observed rows to establish holdings
  before the split interval. Freeze equal-weight selection in the fixture,
  and distinguish initial deployment costs from the event interval.
- Bind the accepted adjusted anchors to zero split-only gross return,
  unchanged drifted weights, zero event-induced turnover, and zero
  event-induced cost. Exercise both demo run functions and their existing
  backtester with explicit fixture outputs.
- Keep the raw-price counterexample visible. Substituting the golden's raw
  move must break the adjusted-economics assertions. The test oracle must use
  the committed expectations independently of the function under test.
- Compare with/without the supplied event metadata: input prices, source
  index, events, holdings, gross/net returns, turnover, and costs remain
  equivalent under the existing M3-08 contract.
- Preserve absent/malformed-date refusal, empty/repeated-date compatibility,
  separate cash-overlay refusal, start/failure retention, previous-report
  preservation, and frozen-config checks.
- Complete the shared validation and isolated ablation below. Record the
  exact tested HEAD and the proof's synthetic scope in the engineering log.

**Forbidden work:** Runtime adjustments, event-driven price rebuilding,
new schemas for arbitrary event types, factor tuning, official config/report
rebaselining, campaign execution, and changes to the frozen Track A fixture
are excluded. Existing campaign helpers serve as reference software only.

**Stop/owner gate:** Proceed in the next authorized implementation scope using
the existing split and supplied-return semantics. Stop if the proof requires a
different return convention, a production behavior change, new data, or a
change to official configuration. A failing baseline receives a retained
counterexample and a separately bounded fix proposal. Success records this
one consumption proof.

**Estimated size:** One test-and-evidence PR; one proof slice.

## 2. Freeze one economic event-comparison contract

**Objective:** Specify the smallest independent comparison between declared
event economics and an already supplied adjusted return series. Scope the
first comparison to one ordinary synthetic cash dividend after the split
proof, with an explicit reference calculation and refusal matrix.

**Why now:** The current `event_table` intentionally treats values as opaque
metadata. Economic comparison needs accepted amount, identity, timestamp, and
field-basis semantics before a value-based pass/fail result can be meaningful.

**Inputs/files:** Read the corporate-action, bitemporal availability, field
dictionary, benchmark, and typed-missingness sections of
`docs/point_in_time_data_methodology_contract.md`, together with
`docs/signal_execution_timing_contract.md`, `PROJECT_SPEC.md`,
`research/dividend_policy.py`, the Step 1 evidence, and
`tests/test_event_date_membership.py`. A proposed bounded design note can live
at `docs/synthetic_event_reconciliation_design.md`; that file is a future
deliverable.

**Acceptance tests:** The design supplies a hand-calculated synthetic example
and an expected-outcome matrix for matching and mismatched evidence, unknown
bases, missing anchors, ambiguous identities, later-known revisions, duplicate
event identities, absent event evidence, and invalid numeric values. It names
the consumed price/return basis, cash entitlement units and currency, event
date role, availability rule, withholding and reinvestment treatment, comparison
window, and numeric tolerance. Repeated dates remain compatible with distinct
events; empty evidence supplies zero reconciliation coverage. Existing M3-08
date-only acceptance and PIT-007 overlay refusal remain independently intact.

**Forbidden work:** Provider selection, event acquisition, latest-only history
reconstruction, automatic repair, generalized event processing, and runtime
changes are excluded. This design leaves official demo defaults intact.

**Stop/owner gate:** The first new owner semantic decision is acceptance of
the dividend comparison basis and its entitlement/reinvestment/timing policy.
Present one concrete proposed convention and its synthetic example. Resolve
that decision before implementing an economic acceptance result; preserve any
unresolved field as a blocking design item. A synthetic convention establishes
only its declared fixture scope and requires separate dataset acceptance for
later historical use.

**Estimated size:** One design PR; one event-family proof specification.

## 3. Implement the accepted synthetic comparison and expose its evidence

**Objective:** Add one opt-in, read-only economic comparison for the Step 2
fixture and expose matched, mismatched, or insufficient-evidence outcomes
through the existing diagnostic report/log path.

**Why now:** An accepted reference convention and independent expected values
allow a small implementation to distinguish event-date consistency from
tested economics. The comparison consumes supplied evidence and preserves
the original prices and accounting inputs.

**Inputs/files:** Use the accepted Step 2 note, `research/dividend_policy.py`,
both demo runners, their attempt/report tests, the Step 1 split proof, and the
point-in-time contract. Reuse existing return/accounting functions. Keep the
default date-only `event_table` behavior compatible; the accepted design must
give economic evidence an explicit opt-in boundary.

**Acceptance tests:** Bind the matching fixture to independently calculated
expected returns; perturb amount, ratio where applicable, basis, identity, and
known-at fields individually and retain the resulting mismatch/refusal.
Exercise absent, empty, duplicate, nonfinite, and incomplete evidence according
to the accepted matrix. Unsupported events receive explicit insufficient or
blocked coverage. Compare prices, signals, holdings, costs, and return windows
against the baseline, and preserve both default report disclosures. A failure
records its outcome before any replacement of the previous successful report.
Every result names its evidence scope; partial fixture coverage retains that
limitation. Run the shared validation and isolated guard ablation.

**Forbidden work:** Split/dividend application to prices, reinvestment or
order-fill engines, calendar inference, provider adapters, automatic
imputation, broad event coverage, and formal adjustment certification are
excluded. This slice creates a comparison of supplied evidence.

**Stop/owner gate:** Begin after Step 2 acceptance and explicit implementation
scope. Stop on a new accounting or identity choice, a need to rewrite the
adjusted series, a public/private boundary change, or a concrete conflict with
existing timing/cost behavior. A larger event family becomes a separately
scoped proof. Completion records exactly the fixture family and cases passed.

**Estimated size:** One implementation PR; one event family with both demo
consumers, one report/log integration, and deterministic regression evidence.

## 4. Prepare the next data gate using the completed synthetic evidence

**Objective:** Produce a concrete readiness package for one owner-selected
exploratory dataset and use, or retain a synthetic-only continuation when the
owner leaves private-data scope closed.

**Why now:** The completed proofs identify required evidence and real
limitations before any data-derived outcome can influence design. A named
scope allows the readiness audit to evaluate actual requirements.

**Inputs/files:** Use `EXPERIMENT_LOG.md`,
`docs/point_in_time_data_methodology_contract.md`,
`docs/real_data_readiness_audit.md`, and the audit skill when that work is explicitly authorized,
the Step 2 contract, and the retained synthetic attempt evidence. The
owner supplies authorization and approved private evidence through its
separate boundary.

**Acceptance tests:** The package identifies the exact dataset/version/use,
entitlement and privacy evidence, permanent identity and decision-time
membership, field/volume bases, event and terminal coverage, typed missingness,
calendar/benchmark compatibility, timing/cost assumptions, sample exposure,
and retained-attempt plan. Each unresolved item has a disposition and an
affected scope. Public artifacts contain only approved safe references.
The historical 2025-05-01 through 2026-05-31 interval retains
`historical_evaluation`. A diagnostic result requires its applicable accepted
readiness evidence; formal interpretation requires all later program gates.

**Forbidden work:** This readiness slice excludes downloads, private
outcome-bearing reads before authorization, backtests on newly supplied data,
Track A reopening, parameter search, profitability interpretation, and trading.

**Stop/owner gate:** Explicit owner scope for the named dataset, access, and
intended use precedes private inspection. Missing authorization or unresolved
material lineage/accounting evidence keeps the affected work closed.
Authorizing intake alone leaves result execution and interpretation subject
to their own applicable scope and gates.

**Estimated size:** One readiness evidence slice; a public pointer requires a
separate publication decision when private evidence is involved.

## Shared validation and ablation

For each authorized implementation slice, preserve the source baseline,
frozen configs, original fixture bytes, committed reports, and existing
attempt-log prefixes. Run focused tests covering the changed behavior and both
consumers, then the baselines in `.github/workflows/ci.yml`: pytest, Ruff,
compilation, and package build. Use temporary outputs for fixture runs.
Regenerate official reports only within an explicit report-refresh scope;
retain every attempted refresh outcome and use repository-relative paths.

Ablation removes one proposed helper, guard, or indirection per isolated
experiment. Retain the baseline and compare public values, refusal reasons,
input preservation, evidence retention, and relevant complexity/runtime cost.
Restore a removal that loses required behavior. A documented no-change result
is valid. This process proves the bounded slice; whole-project ablation has
its separate coverage requirements in `AGENTS.md`.

Milestone 4 remains a later formal-evidence program, and Milestone 5 remains
separately authorized execution scope. This proposal ends with four bounded
steps, one immediately specifiable split proof, and explicit later owner and
data gates.
