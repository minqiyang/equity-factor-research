---
name: real-data-readiness-audit
description: Use before interpreting, reporting, committing, or publishing results from user-provided local CSV market data in this project.
---

# Real-Data Readiness Audit

## When to use

Use this Skill in `ai-equity-factor-research` before interpreting, reporting,
committing, or publishing any result derived from user-provided local CSV market
data.

Use it for local CSV experiment readiness, real-data smoke-test review, local
data provenance review, schema and adjustment-policy review, or deciding whether
a result is safe to describe beyond diagnostics.

## When not to use

Do not use this Skill for synthetic-only demos, committed fixture checks,
general staged workflow continuation, PR branch management, or Skill
maintenance. Those remain covered by `staged-quant-workflow` or `skill-maker`.

This Skill does not approve real data fetching, vendor APIs, credentials,
brokerage connections, live or paper trading, order placement, or profitability
claims.

## Desired outcome

Produce a scope-qualified readiness decision before result interpretation:

- `diagnostic_ready` only when the approved diagnostic scope has no unresolved
  high or medium issues.
- `diagnostic_ready_with_low_caveats` only when limitations are documented and
  do not affect provenance, schema validity, date alignment, privacy, or the
  stated diagnostic interpretation.
- `formal_ready` only when no high or medium issues remain and every active
  program gate listed below is implemented and evidenced.
- `blocked` when any required evidence is missing or unresolved.

Under demo-first delivery, exploratory local-data runs for an initial working slice
(Demo v0) may achieve `diagnostic_ready` or `diagnostic_ready_with_low_caveats`
without requiring complete formal Stage 4 ledger infrastructure or full SEC lineage
proofs, provided that minimum correctness (no lookahead, explicit frictional costs,
sample honesty) is strictly enforced, non-blocking data caveats are documented in
the backlog, and results remain strictly diagnostic without profitability or
formal promotion claims. Formal research promotion controls remain prerequisites
for formal claims, not universal blockers for the initial visibly limited demo.

The audit should make assumptions, caveats, and stop conditions visible before
any local CSV output is treated as research evidence.

## Required inputs/files to inspect

Inspect the current project rules and readiness references:

- `AGENTS.md`
- `PROJECT_SPEC.md`
- `README.md`
- `docs/research_program_charter.md`
- `docs/current_roadmap.md`
- `docs/point_in_time_data_methodology_contract.md`
- `docs/real_data_readiness_audit.md`
- `docs/csv_data_interface_plan.md`
- `docs/volume_ohlcv_schema_plan.md`
- `docs/liquidity_dollar_volume_universe_plan.md`, when present and relevant
- `EXPERIMENT_LOG.md`
- relevant proposed report, log, or research-script paths

Inspect user-provided CSV paths only after the user explicitly approves each
path for metadata inspection or hashing. Do not inspect `.env`, credentials,
tokens, private keys, account files, or credential-like paths.

## Evidence classification and program gates

This audit can approve metadata inspection, loader checks, and explicitly
caveated fixed-cohort diagnostics. It cannot supersede
`docs/research_program_charter.md` or promote a run to formal historical
evidence while a prerequisite remains blocked in `docs/current_roadmap.md`.

Stage 3 keeps three decisions separate:

- `methodology_contract_accepted` accepts the provider-agnostic rules only.
- `dataset_manifest_reviewed` accepts one immutable dataset manifest and its
  redacted public projection only after evidence review.
- `formal_interpretation_eligible` accepts a specific frozen run only after all
  active program gates pass.

`methodology_contract_accepted` does not imply `dataset_manifest_reviewed`, and
`dataset_manifest_reviewed` does not imply
`formal_interpretation_eligible`. A checklist, loader success, hash, license
assertion, or readiness report cannot collapse those gates.

`formal_ready` requires implemented, reviewed, and tested evidence for all of
the following:

- bounded, horizon-purged sample splits and an explicit timing contract.
- the accepted point-in-time methodology contract plus a reviewed immutable
  dataset manifest and non-self-issued exact-version dataset-review decision
  proving provenance/license, canonicalization/environment identity, permanent
  identifiers, bitemporal membership and field availability,
  delisting/corporate-action handling, field semantics, calendar/session
  policy, benchmark/risk-free policy, typed missingness, privacy, and
  protected-sample classification.
- immutable experiment, campaign, trial-family, and trial identifiers allocated
  before execution, including failed and invalid trials.
- the registered statistical and multiple-testing protocol required for the
  claim.
- explicit cost, slippage, turnover, capacity, and execution assumptions
  appropriate to the evidence layer.
- private-data handling and a holdout-exposure classification that does not
  overstate previously examined samples.

Roadmap intent is not implementation evidence. Until these gates are accepted,
the highest possible decision is diagnostic readiness. A static current
constituent list or otherwise unverified historical membership can support only
an explicitly survivorship-biased diagnostic, never `formal_ready`.

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

## Read-only checks

Start with read-only repo state:

```powershell
git status -sb --untracked-files=all
```

For each user-approved local CSV path, metadata and hashing are allowed only
when explicitly approved:

```powershell
Get-Item -LiteralPath "<approved-local-csv-path>" | Select-Object FullName,Length,LastWriteTime
Get-FileHash -Algorithm SHA256 -LiteralPath "<approved-local-csv-path>"
```

Skip any command that would write files, fetch data, install software, call a
vendor API, read secrets, or mutate git state.

## Data provenance checks

Before any result interpretation, record in the repo-external private manifest:

- a stable private-manifest identifier for each input and a separate redacted
  public logical identifier.
- the hash algorithm and actual raw-byte hash, ordered-manifest hash, immutable
  dataset version, retrieval timestamp, extraction query or scope, and
  transformation lineage.
- `canonicalization_id`, `environment_id`, `environment_lock_sha256`,
  interpreter/platform, locale, process timezone, and parsing/calendar/library
  versions.
- the user-provided source name and whether each input is a raw export,
  hand-cleaned, vendor-cleaned, or derived.
- evidence-backed license state (`owner_accepted`, `asserted`, `unknown`, or
  `blocked`), permitted research use, redistribution restriction, and reviewer.
- known manual edits, revisions, missing symbols, missing dates, stale prices,
  or excluded rows.
- confirmation that no credentials, account IDs, API keys, private paths,
  source rows, or private account metadata enter the public projection.

Tracked records must not contain private absolute paths. They may contain only
a publication-approved hash or redacted private-evidence reference and
verification state, never an unapproved digest.

A hash plan, mutable timestamp, unreviewed license assertion, or filename is
not immutable provenance. Unknown provenance, license entitlement, lineage, or
privacy classification blocks formal interpretation.

## Schema and OHLCV checks

Confirm the selected schema and required columns before using data:

- wide adjusted-close price panel.
- long adjusted-close price rows.
- benchmark price or return series.
- OHLCV long rows with `date`, `symbol`, `open`, `high`, `low`, `close`,
  `volume`, and optional `adjusted_close`.
- universe, factor-panel, or metadata schema only when already documented.

Check for exact required column names, duplicate headers, parseable
timezone-naive dates, sorted dates, duplicate dates or `(date, symbol)` rows,
missing symbols, invalid numeric strings, non-finite values, boolean market
data fields, non-positive prices, negative volume, and impossible OHLC
relationships.

Unresolved schema or OHLCV issues block interpretation.

## Date alignment and leakage checks

Keep these dates distinct:

- observation date.
- feature date.
- universe decision date.
- source effective date.
- source publication timestamp.
- source ingestion timestamp.
- revision/supersession timestamp.
- signal date.
- execution date.
- return measurement date.

Confirm that features use only information known before portfolio formation.
Check lookbacks, skipped windows, rolling warm-up periods, signal lag, and
rebalance timing. Every membership, classification, fundamental, and revised
field needs a conservative `known_at` no earlier than every applicable public,
provider, revision, parent, and environment-resolved availability time; require
`known_at <= decision_time`. Same-period target returns, future returns, future
universe membership, future fundamentals, later revisions, future benchmark
data, or same-day close data without an explicit execution assumption must not
enter features.

Unresolved date-alignment or leakage risk blocks interpretation.

## Universe, benchmark, and survivorship checks

Record universe and benchmark assumptions before metrics are interpreted:

- universe definition and eligibility rules.
- permanent security, listing, and issuer identifiers plus ticker-alias
  effective intervals.
- membership effective start/end, `known_at`, inclusion/exclusion reason, and
  point-in-time eligibility for every formal evidence window.
- delisting return/source, terminal valuation, merger/conversion terms, cash
  distributions, symbol changes, and corporate-action effective/known times.
- an explicit survivorship-bias label when a static or otherwise unverified
  cohort is retained for diagnostics only.
- liquidity, dollar-volume, price, stale-data, zero-volume, and minimum-history
  rules when used.
- benchmark identity/version, investable or comparator role, date range,
  adjustment convention, calendar/session/timezone, missing dates, and reason
  it matches the intended universe.
- risk-free source/version, tenor, units, day-count convention, publication
  availability, and missing-date policy when risk-adjusted metrics are claimed.

Incompatible benchmark coverage, unknown benchmark adjustment, unspecified
calendar/session alignment, undocumented survivorship risk, or an undefined
risk-free series for a risk-adjusted claim blocks formal interpretation.
Static or otherwise unverified historical membership blocks formal
interpretation even when its survivorship caveat is documented.

## Missing data and adjustment policy checks

Document price and volume conventions before calculating returns, features, or
diagnostics:

- raw close, adjusted close, split-adjusted, dividend-adjusted, total-return
  adjusted, or unknown.
- whether OHLC and adjusted-close fields share a compatible convention.
- whether volume is raw, adjusted, or unknown.
- handling of splits, dividends, mergers, symbol changes, delistings, halts,
  stale rows, and zero-volume rows.
- typed missingness (`NOT_APPLICABLE`, `NOT_YET_LISTED`, `PROVIDER_GAP`,
  `STALE`, `HALTED`, `DELISTED`, or another reviewed reason) rather than one
  undifferentiated null.
- field dictionary version, currency/unit, source timezone, availability lag,
  and compatible price/volume adjustment bases.

Do not forward-fill, backward-fill, zero-fill, interpolate, or infer corporate
actions by default. Unknown adjustment policy blocks interpretation.

## Costs, slippage, and diagnostics-only language checks

Any backtest-like result must state:

- transaction cost model.
- slippage model.
- turnover model.
- rebalance frequency.
- execution timing.
- benchmark choice.
- whether zero-cost or zero-slippage settings are diagnostics only.

Local CSV diagnostics, IC, Rank IC, quantile spread, loader smoke checks, and
synthetic fixture outputs are not profitability evidence. Use caveated language:
diagnostic, smoke test, readiness check, limitation, and not strategy
validation.

## Experiment logging expectations

Before committing or publishing real-data outputs, prepare an `EXPERIMENT_LOG.md`
entry or approved research note with:

- private-manifest IDs and redacted public logical IDs, never private absolute
  paths.
- schema, immutable version, retrieval/extraction metadata, transformation
  lineage, `canonicalization_id`, `environment_id`,
  `environment_lock_sha256`, license decision, and validation summary; actual
  hashes remain in the private manifest, while the tracked record carries only
  a publication-approved hash or redacted private-evidence reference.
- universe definition and survivorship caveats.
- identifier history, point-in-time membership, corporate actions, field
  availability/revision, calendar/session/timezone, and typed-missingness
  decisions.
- date range and train/validation/test or holdout splits.
- feature formulas, lookbacks, lags, and data availability assumptions.
- parameters and parameter-selection policy.
- benchmark, risk-free policy, costs, slippage, rebalance, and execution timing.
- metrics, missing-data summary, limitations, failure modes, and next action.
- protected-sample classification plus append-only access-record and
  exposure-decision IDs; these remain scope-applicable for diagnostics.
- when formal interpretation is proposed, the immutable dataset-review
  decision ID, exact reviewed manifest/projection identities, reviewer
  authority, scope/time, and finding dispositions. It must be a non-self-issued
  exact-version dataset-review decision; a checklist or manifest producer
  cannot grant the gate.
- for diagnostic scope without a dataset-review decision, do not fabricate a
  decision ID: record `dataset_manifest_reviewed = false`,
  `formal_interpretation_eligible = false`, the diagnostic limitation, and
  omit the formal-only decision identity fields.
- metric names, status, and redacted private-evidence references only; private
  performance values require a separate explicit publication decision.

Synthetic JSON sidecar logs are not substitutes for the real-data experiment
record. The current `EXPERIMENT_LOG.md` template is a diagnostic/legacy record,
not the immutable all-trial ledger required by Stage 4. It cannot satisfy
`formal_ready` until the ledger allocates identifiers before execution and
retains every attempted, failed, invalid, aborted, and excluded trial plus
lineage, hashes, review outcomes, and protected-sample access.

## Stop conditions

Stop before interpretation, reporting, committing, or publishing when any of
these are true:

- user did not explicitly approve a local CSV path for inspection.
- a path appears credential-like or may contain secrets.
- provenance, actual content hash, immutable version, extraction lineage,
  canonicalization/environment identity, environment-lock digest, license
  entitlement, or public/private projection is unknown.
- schema, required columns, duplicate rows, invalid numeric values, missing
  values, or OHLCV checks remain unresolved.
- adjustment policy is unknown or incompatible with the intended calculation.
- date alignment, signal lag, execution timing, or leakage risk is unresolved.
- identifier continuity, corporate-action or delisting treatment, field
  availability/revisions, calendar/session/timezone, or typed missingness is
  unresolved.
- universe membership is static, current-list-based, or otherwise unverified
  for the intended historical dates when formal interpretation is proposed; a
  survivorship caveat permits diagnostics only.
- benchmark or risk-free coverage, units, adjustment, availability, or
  calendar alignment is incompatible.
- costs, slippage, or diagnostic-only language are absent for a backtest-like
  result.
- when formal interpretation is proposed, `dataset_manifest_reviewed` or
  `formal_interpretation_eligible` is absent, or any required timing,
  point-in-time methodology, all-trial ledger, statistical, privacy, or
  holdout-classification program gate lacks accepted implementation evidence.
- when formal interpretation is proposed, the dataset-review decision is
  absent, self-issued, stale, version-mismatched, outside reviewer authority,
  or lacks finding dispositions.
- any high or medium readiness issue remains unresolved.
- the result would require real data fetching, vendor APIs, credentials,
  live or paper trading, broker integration, order execution, or profitability
  claims.

## Mistakes to avoid

- Treating a local CSV loader success as research validation.
- Treating contract acceptance, a hash plan, or a self-asserted license as
  dataset approval.
- Treating a form checkbox or manifest-author declaration as an immutable
  dataset-review decision.
- Treating an unlocked/incomplete environment or ambiguous canonicalization as
  reproducible evidence.
- Treating a survivorship caveat as a substitute for point-in-time membership.
- Treating unknown adjustment policy as acceptable evidence.
- Silently filling missing prices, volumes, benchmark rows, or universe data.
- Using future membership, future returns, or same-period targets as features.
- Reporting only the best parameter result.
- Committing private local paths, source rows, credentials, vendor secrets, or
  account metadata instead of a redacted public projection.
- Committing restricted hashes, license/entitlement documents, or private
  metric values instead of safe decision/evidence references.
- Presenting diagnostics, synthetic fixtures, or smoke tests as profitability,
  robustness, or trading-readiness evidence.
- Duplicating `staged-quant-workflow` branch, PR, merge, and long-running stage
  process inside this Skill.

## Update policy

Update this Skill only after a real-data readiness audit verifies a reusable
lesson. Add concise new stop conditions, stable commands, known pitfalls, or
required evidence fields. Remove stale guidance when project docs change. Keep
this Skill focused on the pre-experiment readiness gate.
