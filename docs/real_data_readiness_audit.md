# Real-Data Readiness Audit

Date: 2026-06-02

This checklist is a pre-experiment gate for using user-provided local CSV data
in the research pipeline. It does not fetch data, download data, choose a data
vendor, add credentials, connect to a broker, place orders, support live
trading, or make profitability claims.

Passing this checklist does not make a strategy or dataset validated. It only
records that the local-data intake has enough documented context for the next
scope-limited review.

This checklist is subordinate to `docs/research_program_charter.md` and the
active gates in `docs/current_roadmap.md`.
`docs/point_in_time_data_methodology_contract.md` is the normative Stage 3
authority for any dataset-specific provenance, universe, corporate-action,
field, privacy, and holdout review. A passing diagnostic audit cannot authorize
formal historical interpretation while a dataset manifest or any timing,
all-trial ledger, statistical, cost, privacy, or holdout-classification gate
remains blocked.

Under the demo-first engineering discipline, an exploratory local-data diagnostic
run for an initial working slice (Demo v0) may qualify under the existing
diagnostic-scope readiness path without requiring full formal Stage 4 ledger
infrastructure or complete SEC lineage proofs. However, skipping formal Stage 4
or universal SEC proof is never a waiver for scope-relevant schema, date
alignment, adjustment consistency, identifier continuity, or economic
correctness. Unknown adjustments, unresolved identifier continuity, or
unresolved high/medium data defects continue to block interpretation under stop
conditions below; simply documenting an unresolved correctness issue in the
backlog does not award readiness. Any such mode-local readiness decision
(`diagnostic_ready`) remains strictly bounded to its declared diagnostic scope
and must not be confused with the historical hash-bound Track A campaign state
(`DIAGNOSTIC_READY`).

## Readiness Classification

Every decision must state one of these scope-qualified outcomes:

- `diagnostic_ready`: the declared metadata, loader, or fixed-cohort diagnostic
  has no unresolved high or medium issue.
- `diagnostic_ready_with_low_caveats`: only low limitations remain and they do
  not affect the stated diagnostic interpretation.
- `formal_ready`: every applicable charter and roadmap prerequisite is
  implemented, reviewed, tested, and supported by the data contract.
- `blocked`: required evidence is absent or unresolved.

The Stage 1 split and Stage 2 timing gates are implemented. Stage 3 contract
acceptance establishes only `methodology_contract_accepted`; it does not
establish `dataset_manifest_reviewed` or `formal_interpretation_eligible`.
Until a specific manifest and the Stage 4 immutable all-trial/access ledger,
Stage 5 statistical package, and other applicable gates pass, the highest
possible outcome remains diagnostic readiness.

A diagnostic-scope audit may return `diagnostic_ready` without a
dataset-review decision only when every requirement for the declared metadata,
loader, or fixed-cohort diagnostic scope passes and its limitations remain
explicit. That outcome records `dataset_manifest_reviewed = false` and
`formal_interpretation_eligible = false`; formal readiness remains blocked and
the outcome is not `formal_ready`. It does not interpret the result beyond the
approved diagnostic scope.

The previously accessed 2025-05-01 through 2026-05-31 interval is
`historical_evaluation`, not a pristine holdout, and must never be upgraded.
Missing, backfilled, unknown-actor/time/impact, outcome-reconstructible, or
overlapping protected access forces a monotone downgrade; a form or later
record cannot restore a less-exposed classification.

## Required Scope Statement

Before running any local CSV experiment, write a short scope statement that
answers:

- What local files will be used?
- What private manifest ID and safe public dataset ID identify the inputs?
- Which schema each file follows: wide price, long price, benchmark, universe
  membership, factor panel, metadata, or another documented schema.
- Which date range is intended for the run.
- Which assets or universe rules are intended.
- Which features, if any, will be calculated.
- Whether the run is a loader smoke test, feature calculation audit, backtest
  diagnostic, or full experiment candidate.
- Whether the requested decision is ingestion-only, `diagnostic_ready`, or a
  later formal-eligibility review.

If this statement cannot be written clearly, stop before running the
experiment.

## Data Provenance

Record enough information that another reviewer can identify the exact local
inputs without relying on memory.

Required in the repo-external private manifest:

- private locator for each input plus a stable logical `input_id`;
- actual byte hash, byte size, schema version, retrieval timestamp, provider
  product/release/as-of identity, and ordered manifest hash;
- `canonicalization_id`, `environment_id`, `environment_lock_sha256`,
  interpreter/platform, locale, process timezone, and all
  parsing/calendar/transformation library versions;
- provider/source and evidence-backed license/entitlement status for the
  declared internal, publication, redistribution, retention, and reproduction
  uses;
- raw export, hand-cleaned, vendor-cleaned, normalized, or derived status;
- complete parent hashes, transformation/config hash, and code SHA;
- known manual edits, quality exceptions, revisions, missing symbols/dates,
  stale observations, and exclusions.

A timestamp or future `hash_plan` may support intake planning but is not an
immutable formal version. Tracked records use only a schema-versioned,
allowlisted public projection. They do not store private absolute paths,
credentials, account/contract IDs, license documents, tokens, restricted
queries, raw rows, or private performance values.

## Schema And Loader Checks

For each CSV file, record:

| Check | Required evidence |
| --- | --- |
| Schema selected | Wide price, long price, benchmark, universe, factor, or metadata |
| Required columns | Present with exact expected names |
| Date parsing | Dates parse successfully and are timezone-naive unless explicitly documented |
| Date order | Dates are sorted after validation |
| Duplicate dates | No duplicates in wide date-indexed files |
| Duplicate date-symbol pairs | No duplicates in long asset files |
| Numeric fields | Parsed explicitly with errors surfaced |
| Missing values | Counted by file, field, date, and symbol where possible |
| Non-positive prices | Rejected or separately justified before use |
| Forward-fill/backward-fill | Disabled unless a later reviewed stage adds explicit policy |

The current local CSV loader is allowed only to read user-provided local files.
It must not download data or call vendor APIs.

## Price Adjustment Policy

Document the adjustment convention before calculating returns or features.

Required:

- Whether prices are adjusted close, raw close, split-adjusted, dividend-adjusted,
  total-return adjusted, or unknown.
- Whether open, high, low, close, and adjusted close fields use the same
  adjustment convention.
- Whether volume is raw share volume or adjusted volume.
- How splits, dividends, mergers, symbol changes, and delistings are represented.
- Whether the benchmark uses the same adjustment convention as the asset panel.
- Field-level adjustment-set identity, dividend treatment, split-factor
  direction, raw/adjusted volume basis, allowed field roles, and prevention of
  double counting or incompatible price-volume products.
- Delisting terminal-value, merger consideration, spin-off, and successor
  handling.

If adjustment policy is unknown, do not treat return metrics as research
evidence.

## Universe Construction

Universe rules must be date-aware and documented before the run.

Required:

- Starting universe definition.
- Liquidity or volume filters, if any.
- Price filters, if any.
- Minimum history requirements.
- Inclusion and exclusion rules.
- How delisted, merged, stale, suspended, or missing symbols are handled.
- Permanent security and listing identifiers plus effective-dated ticker,
  exchange, share-class, listing, and successor history.
- Verified point-in-time membership for each formal evidence window, or an
  explicit static/unverified label for a diagnostic-only cohort.
- Membership effective interval, decision/public `known_at`, revision, and
  inclusion/exclusion evidence.
- Survivorship-bias risk statement.

Future universe membership must not be used for earlier dates.
A static current list or otherwise unverified historical membership blocks
formal interpretation even when its survivorship-bias caveat is documented.
Ticker text or presence in a price file is not permanent identity or membership
evidence.

## Benchmark Choice

Record benchmark assumptions before computing benchmark-relative metrics.

Required:

- Benchmark symbol or local benchmark file.
- Why the benchmark matches the intended universe.
- Benchmark date range.
- Benchmark price or return field.
- Missing benchmark dates.
- Adjustment convention.
- How benchmark dates align to strategy dates.
- Benchmark purpose, permanent identity, investability, point-in-time
  composition when applicable, currency/FX, calendar/timezone, corporate-action
  and distribution basis, and no-substitution rule.
- Risk-free source or reviewed `NOT_APPLICABLE`, including currency, tenor,
  quote type, units, day count, compounding, availability lag, interval
  conversion, revision, and missing policy.

If benchmark coverage is incomplete, the experiment should stop unless the
missing-data policy is explicitly documented as diagnostic.

## Feature And Signal Timing

Feature dates must remain distinct from execution and return measurement dates.

Required:

- Feature formula and required input fields.
- Lookback windows and skipped windows.
- Latest data timestamp available for each signal date.
- Economic effective time, source publication time, public/provider availability
  time, revision publication time, selected vintage, and supersession lineage.
- Conservative `known_at`, no earlier than every applicable public, provider,
  revision, parent, and environment-resolved availability time, with
  `known_at <= decision_time`.
- Signal lag before portfolio formation.
- Execution timing assumption: next open, next close, next available row, or
  another explicit rule.
- Tests or manual checks for off-by-one risk in rolling windows and lags.

Same-period target returns must not be used as features.
Latest-only fundamentals or classifications are diagnostic-only when an
as-known-at vintage cannot be reconstructed. A date-only release uses the
contract's conservative next-session rule unless a reviewed timestamp proves
earlier availability.

## Sample Splits And Parameter Policy

Before evaluating parameter choices, define:

- In-sample period.
- Validation period.
- Test or holdout period.
- Explicit start and end dates for every split.
- Label horizon, boundary purge, optional embargo, and excluded-row metadata.
- Any warm-up period excluded from evaluation.
- Parameter grid or fixed parameter policy.
- Whether parameter choices were made before or after looking at results.
- How weak, failed, or ambiguous cases will be recorded.

Do not report only the best parameter result.

## Costs, Slippage, And Execution Assumptions

Every backtest-like run must state:

- Transaction cost model.
- Slippage model.
- Turnover model.
- Rebalance frequency.
- Execution timing.
- Benchmark choice.
- Whether zero-cost or zero-slippage settings are used only as diagnostics.

Zero-cost or no-slippage results must not be presented as realistic execution
evidence.

## Required Experiment-Log Fields

Before committing any real-data experiment output, add or prepare an
`EXPERIMENT_LOG.md` entry that includes:

- Private-manifest IDs and redacted public logical IDs; never tracked private
  absolute paths.
- Immutable version, retrieval/extraction metadata, transformation lineage,
  `canonicalization_id`, `environment_id`, `environment_lock_sha256`, license
  decision, and privacy classification. Actual hashes remain in the private
  manifest; the tracked record contains only a publication-approved hash or
  redacted private-evidence reference.
- Universe definition and survivorship-bias caveats.
- Date range and sample splits.
- Feature formulas, lookbacks, lags, and data availability assumptions.
- Parameters and parameter-selection policy.
- Benchmark.
- Transaction costs and slippage.
- Rebalance and execution timing.
- Metrics and limitations.
- Missing-data summary.
- Private manifest ID and safe public projection ID; never a tracked absolute
  private path.
- When formal interpretation is proposed, the immutable dataset-review
  decision ID, exact reviewed manifest/projection identities,
  reviewer-authority reference, scope/time, finding dispositions, and safe
  decision-record reference. It must be a non-self-issued exact-version
  dataset-review decision; a checklist or manifest producer cannot grant this
  gate.
- For diagnostic scope without a dataset-review decision, do not fabricate a
  decision ID: record `dataset_manifest_reviewed = false`,
  `formal_interpretation_eligible = false`, the diagnostic limitation, and
  omit the formal-only decision identity fields.
- Protected-sample access intent/completion references, append-only
  access-record and exposure-decision IDs, classification before and after,
  accessed artifact/metric names without values, and design impact; these
  remain scope-applicable for diagnostics.
- Metric names, computation status, and redacted private-evidence references;
  private performance values require a separate explicit publication decision.
- Failure modes.
- Next action.

Synthetic demo JSON logs are not substitutes for this real-data experiment
record. The current `EXPERIMENT_LOG.md` template remains a diagnostic/legacy
record, not the immutable all-trial ledger required by Stage 4. A formal run
must allocate experiment, campaign, trial-family, and trial identifiers before
execution and retain every attempted, failed, invalid, aborted, and excluded
trial plus configuration, code/data lineage, output hashes, review outcome, and
protected-sample access.

## Stop Conditions

Stop the run before interpreting any result if:

- Required data provenance is missing.
- License/entitlement or permitted-use evidence is asserted, unknown, expired,
  incompatible, or not owner-accepted.
- When formal interpretation is proposed, the dataset-review decision is
  absent, self-issued, stale, version-mismatched, outside reviewer authority,
  or lacks finding dispositions.
- Actual hashes, retrieval/version identity, extraction identity, or
  transformation lineage are absent.
- Canonicalization identity, environment identity/lock, locale/timezone, or
  parsing/calendar/transformation library versions are absent or incomplete;
  an unlocked/incomplete environment blocks formal interpretation and
  independent reproduction.
- Price adjustment policy is unknown.
- Formal interpretation is proposed with a static current list or otherwise
  unverified historical membership; documenting survivorship bias permits only
  diagnostic use.
- Benchmark coverage or adjustment is incompatible with the asset data.
- Missing values are silently filled.
- Dates or date-symbol rows are duplicated without reviewed resolution.
- Feature timing cannot be shown to precede execution timing.
- Filing, classification, membership, identifier, or corporate-action
  availability/revision timing is unknown.
- Permanent identity, listing/delisting history, or terminal-value policy is
  unresolved.
- Missing, stale, halt, suspension, exchange-closure, provider-gap, and
  delisting states are conflated or silently filled.
- Calendar/session/timezone, benchmark, currency, or risk-free compatibility is
  unresolved.
- A tracked/public artifact may expose a private locator, entitlement document,
  restricted hash/query, raw value, or private performance value.
- Protected access is missing, backfilled, uncertain, or would upgrade an
  exposed sample.
- Sample splits are not defined for parameter selection.
- Costs, slippage, or execution assumptions are absent.
- A required timing, point-in-time methodology, all-trial ledger, statistical,
  cost, privacy, or holdout-classification program gate lacks accepted
  implementation evidence for the proposed formal claim.
- The result would require a profitability or investment-performance claim.

## Approval Gate

A diagnostic real-data experiment may proceed only after this audit identifies
no unresolved high or medium issues within its stated diagnostic scope. Low
issues may proceed only when they are documented as limitations and do not
affect date alignment, data availability, privacy, or the diagnostic
interpretation.

`formal_ready` additionally requires every applicable charter and active
roadmap gate to have accepted implementation evidence. Contract acceptance
does not verify a dataset. The first use of local CSV data remains a smoke test
unless a dataset-specific manifest, Stage 4 trial/access ledger, Stage 5
validation protocol, and every other applicable interpretation gate have
passed.
