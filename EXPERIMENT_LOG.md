# Experiment Log

Use this file to record every meaningful experiment, including failed or
inconclusive runs. Do not delete weak results to make the project look better.

## Current Authority And Limitation

This file is the repository's diagnostic/legacy experiment record. It preserves
the current synthetic and local-CSV documentation workflow, but it is not the
immutable all-trial ledger required by Stage 4 of `docs/research_program_charter.md`
and `docs/experiment_trial_ledger_contract.md`.

`docs/point_in_time_data_methodology_contract.md` defines the Stage 3
provider-agnostic data and holdout-evidence requirements. Accepting that
contract does not review a dataset manifest or make a run eligible for formal
interpretation.

Until that ledger allocates experiment, campaign, trial-family, and trial
identifiers before execution and retains every attempt, failure, invalid or
aborted run, full configuration, code/data lineage, output hash, review
outcome, and protected-sample access, entries here may support only
appropriately caveated diagnostics. They must not support formal historical
interpretation, factor promotion, a `RESEARCH_PASS`, or a holdout-independence
claim. "Every configured case" is not evidence of complete trial accounting.

Under the demo-first engineering discipline, All-Attempt Case Logging applies
to Demo v0 runs and to the M3-01 exploratory three-factor backtest:
`python -m research.demo_v0` appends every attempted case, including failures,
to `reports/demo_v0_attempts.jsonl` and writes the synthetic comparison report
to `reports/demo_v0.md`. `python -m research.synthetic_multifactor_backtest_demo`
appends every attempted case, including failures and catchable interruptions,
to `reports/synthetic_multifactor_backtest_demo_attempts.jsonl` and writes the
synthetic comparison report to `reports/synthetic_multifactor_backtest_demo.md`.
A start record is written before computation so incomplete attempts remain
visible. This lightweight diagnostic run logging is explicitly distinguished
from the formal experiment/trial-ledger accounting required by charter Stage 4 /
`docs/experiment_trial_ledger_contract.md` and by Milestone 4 formal research.
Existing synthetic sidecar logs under `reports/experiment_logs/` remain legacy
diagnostics and are not accepted Demo v0 evidence. `python -m research.synthetic_multifactor_workflow_demo`
remains the feature-only workflow. All-Attempt records support reproducible
demo evidence and track non-blocking imperfections in the lightweight backlog;
formal factor promotion remains reserved for Milestone 4.

## Automated Synthetic Demo Logs

Synthetic demo scripts also write deterministic JSON sidecar logs under
`reports/experiment_logs/`. These logs capture configuration, synthetic-only
data assumptions, caveats, outputs, and diagnostics from reproducible smoke
demos.

They are not substitutes for full experiment records when real data, real
universe definitions, validation splits, or parameter studies are introduced.
Synthetic demo metrics remain workflow diagnostics only and are not financial
advice, strategy validation, or profitability evidence.

`reports/experiment_registry.md` summarizes the JSON logs in a deterministic
table for review. The registry is a reporting view over existing logs; it does
not run experiments, recalculate metrics, or replace full experiment records.

`reports/synthetic_multifactor_parameter_sweep.md` is a synthetic-only
parameter sensitivity smoke test. It reports every configured case and should
not be used as parameter selection, strategy validation, financial advice, or
profitability evidence.

## Local CSV Experiment Records

Any future run that uses user-provided local CSV data must add or prepare a full
entry in this file before results are interpreted. The entry is required for
loader smoke tests, feature audits, backtest diagnostics, parameter studies, and
full experiment candidates.

This requirement does not authorize data downloads, remote data access, vendor
APIs, credentials, live trading, brokerage integration, order execution, or
profitability claims. Local CSV runs remain research-only and must pass the
real-data readiness audit before being treated as diagnostic evidence. A
completed entry does not by itself satisfy the point-in-time methodology,
purged-split, timing, all-trial ledger, statistical, privacy, cost, or holdout
gates required for formal evidence.

At minimum, a local CSV experiment record must include:

- Private-manifest ID and redacted public logical ID for each input. Tracked
  records must not contain private absolute paths.
- Private evidence that records the hash algorithm, actual raw-byte and
  ordered-manifest hashes, immutable dataset version, retrieval timestamp,
  extraction scope, transformation lineage, and any revision/supersession
  relationship, plus `canonicalization_id`, `environment_id`,
  `environment_lock_sha256`, interpreter/platform, locale, process timezone,
  and parsing/calendar/transformation library versions. Actual hashes remain
  in the private manifest; this tracked record contains only a
  publication-approved hash or redacted private-evidence reference and
  verification state.
- Redacted license-decision ID/evidence reference and review state, permitted
  research use, redistribution restriction, and public/private classification.
  License documents, contract/account IDs, and restricted entitlement metadata
  remain private. An asserted license is not an accepted entitlement decision.
- Schema for each file: wide price, long price, benchmark, universe membership,
  factor panel, metadata, or another reviewed schema.
- Validation summary: date parsing, sorted dates, duplicate checks, numeric
  parsing, missing-value counts, non-positive price handling, and whether any
  forward-fill or backward-fill was used.
- Data provenance: source name as provided by the user, export type, known
  manual edits, and known missing, stale, revised, or excluded observations.
- Price adjustment policy: adjusted close, raw close, split-adjusted,
  dividend-adjusted, total-return adjusted, or unknown, including benchmark
  adjustment compatibility.
- Universe rules: starting universe, point-in-time membership status, liquidity
  filters, price filters, minimum history, exclusions, permanent/listing/issuer
  identifiers, ticker-alias intervals, membership effective/known times,
  delistings, mergers, corporate actions, and survivorship-bias caveats.
- Field and calendar policy: source field dictionary/version, units/currency,
  field availability and revision timestamps, exchange calendar,
  session/timezone conventions, typed missingness, and stale/zero-volume rules.
- Feature and signal timing: formulas, lookbacks, skipped windows, latest data
  timestamp available for each signal date, conservative `known_at` with
  `known_at <= decision_time`, signal lag, and execution timing.
- Sample splits and parameter policy: in-sample, validation, test or holdout
  periods, warm-up exclusion, fixed parameters or grid, and whether choices were
  made before seeing results.
- Benchmark: symbol or local benchmark file, date range, price or return field,
  version, role, missing dates, adjustment convention, availability, and
  alignment to strategy dates; include risk-free source, version, tenor,
  units, day-count, availability, and missing-date policy when applicable.
- Costs, slippage, turnover, rebalance frequency, and execution assumptions,
  including whether zero-cost or zero-slippage settings are diagnostic only.
- Metric names, computation status, redacted private-evidence references, and
  limitations, including missing-data limitations, benchmark mismatch,
  corporate-action uncertainty, vendor differences, stale prices, delisting
  risk, and any unresolved low issues from the readiness audit. Private
  performance values remain outside tracked records unless a separate
  publication decision explicitly approves named aggregate fields.
- Failure modes and next action, including weak, failed, ambiguous, or stopped
  cases. Do not report only the best parameter result.
- Holdout-exposure classification and append-only access-record identifier.
  The historically examined 2025-05-01 through 2026-05-31 interval is
  `historical_evaluation`, not a pristine holdout.
- When formal interpretation is proposed, the immutable dataset-review
  decision ID, exact reviewed manifest/projection identities,
  reviewer-authority reference, scope, timestamp, and finding dispositions.
  This must be a non-self-issued exact-version dataset-review decision; the
  tracked record cannot grant a gate or self-certify its own manifest.
- For diagnostic scope without a dataset-review decision, do not fabricate a
  decision ID: record `dataset_manifest_reviewed = false`,
  `formal_interpretation_eligible = false`, the diagnostic limitation, and
  omit the formal-only decision identity, reviewer, and finding fields.
  Protected-sample access-record and exposure-decision IDs remain
  scope-applicable and are not formal-only.

If required provenance, adjustment policy, date alignment, benchmark coverage,
sample splits, cost/slippage assumptions, license evidence, verified private
hash evidence,
identifier history, field availability, calendar policy, privacy projection,
canonicalization/environment identity, protected-sample classification, or
missing-data evidence is absent, stop before interpreting even diagnostic
metrics. Synthetic JSON sidecar logs are not substitutes for local CSV
experiment records, and neither record type is the future immutable all-trial
ledger.

## Template

### Experiment ID

`YYYYMMDD-NNN-short-name`

### Date

`YYYY-MM-DD`

### Hypothesis

What should be true if this experiment is useful?

### Data Source

Dataset name, vendor, private-manifest ID, redacted public logical ID, immutable
version, hash-verification state plus a publication-approved hash or redacted
private-evidence reference, retrieval/extraction metadata, lineage, license
state, `canonicalization_id`, `environment_id`, `environment_lock_sha256`,
privacy class, and any known limitations. Do not record a private absolute path
or an unapproved digest.

### Dataset Review Decision

When formal interpretation is proposed, record the immutable decision ID, exact
reviewed manifest/projection identities, safe reviewer-authority reference,
review time, declared scope, decision, finding dispositions, contract identity,
and redacted evidence reference. This must be a non-self-issued exact-version
dataset-review decision. The manifest producer or this template cannot grant
`dataset_manifest_reviewed`.

For diagnostic scope without a dataset-review decision, do not fabricate a
decision ID. Record `dataset_manifest_reviewed = false`,
`formal_interpretation_eligible = false`, the diagnostic limitation, and omit
the formal-only decision identity, reviewer, and finding fields. Continue to
record every scope-applicable protected-sample access-record and
exposure-decision ID under Sample Split.

### Universe

Universe definition, permanent/listing identifiers, point-in-time membership
and known-at times, liquidity screen, exclusions, corporate actions,
delistings, and survivorship-bias notes.

### Date Range

Start date, end date, and any excluded dates.

### Features / Factors

Feature names, formulas, lookback windows, lags, and data availability assumptions.

### Parameters

All strategy, backtest, ranking, selection, and risk-control parameters.

### Benchmark

Benchmark identity/version, role, availability/calendar/alignment, and return
calculation assumptions. Include the risk-free source and convention when
risk-adjusted metrics are claimed.

### Transaction Costs

Cost model, basis points, minimum commissions, and any simplifications.

### Slippage Model

Slippage model, basis points or volume-aware rule, and limitations.

### Rebalance Frequency

Daily, weekly, monthly, or custom schedule. State exact execution timing.

### Performance Metrics

For synthetic or explicitly publication-approved evidence, record the named
total-return, annualized-return, volatility, Sharpe-style,
benchmark-relative, or other approved fields. For private evidence, record
only metric names, computation status, and redacted private-evidence IDs unless
a separate publication decision approves the named aggregate values.

### Turnover

Record the method and approved evidence fields. Private turnover values and
distributions remain external unless separately approved for publication.

### Max Drawdown

Record the method and approved evidence fields. Private drawdown values, dates,
and benchmark comparison remain external unless separately approved for
publication.

### Sample Split

In-sample, validation, and test period definitions, protected-sample
classification, append-only access-record identifier, and exposure-decision
ID. Missing, backfilled, uncertain, outcome-reconstructible, or overlapping
access downgrades the sample monotonically; the 2025-05-01 through 2026-05-31
interval remains `historical_evaluation` and cannot be upgraded.

### Result Summary

Concise summary of what happened. Include weak, failed, or ambiguous results.
For private evidence, do not reveal direction, magnitude, rank, or metric
value; record only status and a redacted private-evidence reference unless
publication is separately approved.

### Failure Modes

Known problems, possible leakage risks, sensitivity issues, data quality concerns, overfitting risks, or execution assumptions that may be unrealistic.

### Next Action

Keep, reject, revise, test further, add data, improve validation, or stop.
