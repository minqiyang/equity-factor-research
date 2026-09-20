# Changelog

All notable repository changes should be recorded here.

This project does not use changelog entries to claim investment performance,
profitability, or trading readiness.

## Unreleased

### Added

- `research/multifactor_diagnostic_mvp.py`: Wired advanced multi-factor combinations
  (`ICIR_WEIGHTED_COMPOSITE`, `CORRELATION_DISCOUNTED_COMPOSITE`), cross-factor interactions
  (`ALPHA_PRODUCT_INTERACTION`, `CONDITIONAL_RANK_INTERACTION`), and cross-sectional volatility
  neutralization (`NEUTRALIZED_IC_COMPOSITE`) into the diagnostic cohort pipeline.
- `research/multifactor_diagnostic_mvp.py`: Integrated dollar-neutral long-short decile spread
  backtesting (`run_long_short_backtest`) across all 59 evaluated factors, reporting long-short
  Sharpe, annualized returns, drawdowns, win rate, decile spreads, and Spearman monotonicity
  in `reports/multifactor_diagnostic_mvp.md` and `reports/experiment_logs/multifactor_diagnostic_mvp.json`.
- `src/features/combination.py`: Added `icir_weighted_composite` (Information Ratio weighting)
  and `correlation_discounted_composite` (collinearity-adjusted factor combination with ridge regularization).
- `src/features/interaction.py`: Added `factor_product_interaction` (cross-sectional bivariate product),
  `conditional_factor_rank` (quantile double-sorting), and `factor_quadrant_interaction` (regime quadrant classification).
- `src/features/neutralize.py`: Added `cross_sectional_demean`, `cross_sectional_neutralize` (OLS
  regression against single or multiple risk factors with $X^T \epsilon = 0$ orthogonality guarantee),
  and `cross_sectional_group_neutralize` (industry/sector demeaning) for cross-sectional risk adjustment.
- `src/backtest/portfolio.py`: Added configurable `weighting_scheme` (`"equal"`, `"rank"`) and dynamic
  point-in-time `universe_mask` for universe filtering and immediate liquidation upon asset exit.
- `src/backtest/long_short.py`: Added `run_long_short_backtest` and `LongShortBacktestResult` supporting
  dollar-neutral quantile/decile portfolios, long-short spread (D10 - D1), turnover, and explicit transaction costs.
- `src/features/diagnostics.py`: Added `probability_of_backtest_overfitting` implementing
  Combinatorially Symmetric Cross-Validation (CSCV) to evaluate backtest overfitting probability
  and out-of-sample loss probability across multiple strategy/alpha variants.
- `src/data/constituent_table.py`: Added point-in-time constituent membership table loader
  `load_constituent_intervals_csv` and lookahead-free dynamic universe mask builder
  `build_membership_mask` with ticker reuse prevention (PIT-005).
- `research/multifactor_diagnostic_mvp.py`: Wired PBO evaluation across the 52 implemented
  WorldQuant alphas into the consolidated diagnostic report and experiment log.

### Changed

- `AGENTS.md` has a first-class Ablation section: after every completed design
  or implementation, run an ablation experiment and keep the simplest code that
  still meets current requirements.
- `docs/codex_long_running_controller.md` keeps this repository's GitHub PR
  lifecycle (Draft/Ready, predecessor gate, exact-head review wait, protected
  merge). Reviewer routing, quota rotation, and named-model seats live in the
  live Herdr+Pi coordination standard. An ablation of deleting the file is
  rejected: those GitHub lifecycle owners have no other canonical home.
- `AGENTS.md` keeps repository invariants, research-safety review standards,
  and writing style. Reviewer routing, quota rotation, and review-loop
  dispatch live in the live Herdr+Pi coordination standard.

### Fixed

- Walking Skeleton DSR uses the Euler-Mascheroni constant in the
  Bailey-Lopez de Prado expected-maximum mix. Sample skewness and
  kurtosis remain only in `V[SR]`. Regenerated diagnostic report DSR
  values and golden tests follow the paper mix. DIAGNOSTIC_ONLY.
- Synthetic dividend evidence dictionaries encode as
  `{"json_evidence": "object", "items": {<caller keys>}}`. Nested caller
  `items` and `json_evidence` keys stay inside the envelope, so
  classification-changing mutations change digest and snapshot when the
  declared hash is left unchanged. Selected revision identifiers serialize
  through `json_evidence`. See `reports/dividend_comparison_attempt.md`.
- Overlapping synthetic dividend comparison scopes that assign the same
  supplied asset to different permanent identities, or the same identity to
  different assets, now diagnose `identity_unresolved` and keep economic
  acceptance false. Evidence canonicalization distinguishes caller
  dictionaries from encoded scalars, so classification-changing mutations
  change the digest and retained snapshot. Invalid observation states and
  non-string evidence keys remain typed on completed diagnostic items. The
  opt-in report JSON copies the runner `attempt_id` onto each item. See
  `reports/dividend_comparison_attempt.md`.
- Demo v0 All-Attempt Case Logging now writes a start record before
  computation, keeps incomplete and interrupted attempts visible, records
  catchable `KeyboardInterrupt` and `SystemExit` outcomes and re-raises
  them, and refuses to replace the comparison report when the attempt log
  cannot begin.

### Added

- WorldQuant classical price-volume alphas `alpha_015`, `alpha_016`,
  `alpha_022`, `alpha_025`, `alpha_031`, `alpha_036`, `alpha_037`,
  `alpha_040`, `alpha_041`, `alpha_042`, `alpha_044`, `alpha_046`,
  `alpha_050`, and `alpha_052`. Command
  `python -m research.multifactor_diagnostic_mvp` now evaluates all 52
  implemented alphas plus equal-weighted and IC-weighted composites with
  Rank IC, ICIR, Newey-West t-stat, Euler-Mascheroni DSR (`n_trials=54`),
  and 5 bps monthly backtests under `DIAGNOSTIC_ONLY`. See
  `reports/multifactor_diagnostic_mvp.md`.

- WorldQuant classical price-volume alphas `alpha_021`, `alpha_024`,
  `alpha_026`, `alpha_030`, `alpha_032`, `alpha_034`, `alpha_035`,
  `alpha_039`, `alpha_043`, `alpha_045`, `alpha_049`, `alpha_051`,
  `alpha_053`, `alpha_055`, and `alpha_060`. Command
  `python -m research.multifactor_diagnostic_mvp` now evaluates all 38
  implemented alphas plus equal-weighted and IC-weighted composites with
  Rank IC, ICIR, Newey-West t-stat, Euler-Mascheroni DSR (`n_trials=40`),
  and 5 bps monthly backtests under `DIAGNOSTIC_ONLY`. See
  `reports/multifactor_diagnostic_mvp.md`.

- WorldQuant classical price-volume alphas `alpha_007`, `alpha_009`,
  `alpha_017`, `alpha_019`, `alpha_023`, `alpha_028`, `alpha_033`,
  `alpha_038`, `alpha_054`, and `alpha_101`. Command
  `python -m research.multifactor_diagnostic_mvp` now evaluates all 23
  implemented alphas plus equal-weighted and IC-weighted composites with
  Rank IC, ICIR, Newey-West t-stat, Euler-Mascheroni DSR (`n_trials=25`),
  and 5 bps monthly backtests under `DIAGNOSTIC_ONLY`. See
  `reports/multifactor_diagnostic_mvp.md`.

- WorldQuant classical price-volume alphas `alpha_005`, `alpha_008`,
  `alpha_010`, `alpha_013`, `alpha_014`, `alpha_018`, and `alpha_020`, plus
  equal-weighted and IC-weighted z-score composites in
  `src/features/combination.py`. Companion diagnostic OHLCV now includes high
  and typical-price VWAP. Command
  `python -m research.multifactor_diagnostic_mvp` writes Rank IC, ICIR,
  Newey-West t-stat, Euler-Mascheroni DSR, and 5 bps monthly backtests under
  `DIAGNOSTIC_ONLY`. See `reports/multifactor_diagnostic_mvp.md`.

- WorldQuant-style panel operators `ts_sum`, `ts_mean`, `ts_std`, `ts_min`,
  `ts_max`, `ts_argmax`, `ts_argmin`, `ts_corr`, and `ts_cov`, plus classical
  price-volume alphas `alpha_001`, `alpha_002`, `alpha_003`, `alpha_004`,
  `alpha_006`, and `alpha_012`. The 50-stock diagnostic cohort now has a
  companion synthetic OHLCV generator. Command
  `python -m research.alphas_diagnostic_mvp` writes Rank IC, ICIR,
  Newey-West t-stat, Euler-Mascheroni DSR, and 5 bps monthly backtests under
  `DIAGNOSTIC_ONLY`. See `reports/alphas_diagnostic_mvp.md`.

- Step 3 adds the accepted ordinary synthetic dividend comparison as an explicit
  opt-in argument to Demo v0 and M3-01. Exact rational diagnoses retain scoped
  evidence, revisions, typed gaps, and negative outcomes under the same attempt.
  The opt-in report uses temporary-file replacement after per-item retention.
  Default reports, configurations, event metadata, and accounting stay intact.
  See `reports/dividend_comparison_attempt.md` for D01-D47, fault tests, QA,
  ablation evidence, and the remaining coordinator review/private-data gates.


- M3-08 supplied-event date membership for Demo v0 and M3-01: an optional
  `event_table` DataFrame uses a `DatetimeIndex` of event dates. Every date must
  exist in the declared source index; absent or missing dates are refused.
  Repeated dates and empty typed tables are accepted. Event values remain
  metadata, and prices and held returns remain unchanged. The PIT-007
  cash-dividend overlay refusal remains active. Both official reports state
  that event-level reconciliation was not performed because no independent
  event table was supplied. Frozen `DEMO_V0_CONFIG` remains unchanged.
  Full economic dividend/split reconciliation remains separately scoped work.

- M3-07 calendar-day span reporting for Demo v0 and M3-01: both reports record
  the count of adjacent timestamp pairs spanning more than one day and the
  maximum span. Both pipelines reuse `refuse_inserted_source_rows` against a
  declared source index; official demos declare the generated price index.
  Session and holiday status remains unverified. Every supplied observed bar
  stays in place, including Friday-Monday bars. Frozen `DEMO_V0_CONFIG` stays
  unchanged. Remaining Milestone 3 work is event-level dividend/split
  reconciliation.

- M3-06 unchanging-price segment reporting for Demo v0 and the M3-01
  three-factor backtest demo: consecutive equal prices of length >= 2
  are counted as segments, with assets affected and max run length
  written into both comparison reports. Consecutive equal prices stay
  in the panel. The backtest uses every supplied bar. Frozen Demo v0
  config is unchanged. No new public command. Remaining Milestone 3
  work is event-level dividend/split reconciliation.
- M3-05 broader historical window tests for Demo v0 and the M3-01
  three-factor backtest demo: `dataclasses.replace` with
  `periods=2 * DEMO_V0_CONFIG.periods` runs both pipelines on 1512
  synthetic rows. Official frozen Demo v0 config remains seed 20260521,
  20 assets, 756 rows, lookback 252, skip 21, ME, top_n 5, 10 bps,
  0 slippage. Official commands keep that frozen config. Output is a
  synthetic diagnostic. Remaining Milestone 3 work is
  event-level dividend/split reconciliation.
- M3-04 PIT-007 tests for Demo v0 and the M3-01 three-factor backtest
  demo: held returns use the supplied price series only
  (`current / previous - 1`), and a separate cash-dividend overlay on that
  series is refused. Frozen Demo v0 config is unchanged. No corporate-action
  engine was added. Event-level dividend and split reconciliation remains
  later Milestone 3/4 work.
- M3-03 source-row lag tests for Demo v0 and the M3-01 three-factor
  backtest demo: signal lag counts observed source rows in the bounded
  accounting slice, and a missing source row remains an omitted
  observation. Those demos keep the supplied observed index. M3-07 now
  reports adjacent calendar-day spans and refuses panel timestamps absent
  from the declared source index. Frozen Demo v0
  config is unchanged. Remaining Milestone 3 work is event-level
  dividend/split reconciliation.
- M3-02 zero-volume and missing-bar refusal for Demo v0 and the M3-01
  three-factor backtest demo: complete finite strictly positive price bars
  are required, a supplied volume panel must be strictly positive, and
  killing tests cover missing, dropped, zero, and zero-volume bars without
  silent fill, clip, drop, or repair. Frozen Demo v0 config is unchanged.
  The local CSV loader still accepts zero volume as loader-valid.
- M3-01 exploratory synthetic three-factor backtest:
  `python -m research.synthetic_multifactor_backtest_demo` reuses Demo v0
  synthetic price dates and assets, the existing factor generator and
  0.50 / 0.30 / 0.20 weights, existing winsorize/z-score/`combine_factors`
  helpers, and the Demo v0 long-only backtester (monthly top-five, 10 bps,
  0 bps slippage labeled diagnostic,
  `after_close_signal_next_observed_close_v1`). It writes a comparison
  report and All-Attempt Case Logging with a start record before
  computation. The three panels are artificial quality, reversal, and
  momentum fixtures. `python -m research.demo_v0` remains the official
  Demo v0 command. `python -m research.synthetic_multifactor_workflow_demo`
  remains the feature-only workflow. No profitability claim. No private
  data. No new cost engines.
- Official Demo v0 synthetic vertical slice: `python -m research.demo_v0`
  reuses existing 12-1 momentum and frozen `SyntheticDemoConfig` values,
  writes a comparison report, and appends All-Attempt Case Logging for
  successes and failures. `python -m research.synthetic_momentum_demo`
  remains a legacy diagnostic. No profitability claim. No private data.
- Demo-first delivery alignment and North Star specification: added
  `docs/north_star.md`, updated project specifications, roadmap, and handoffs
  around five primary milestones (while preserving the hash-pinned research
  program charter byte-identical as historical formal evidence policy),
  establishing Milestone 2 Demo v0 (minimal reproducible end-to-end slice)
  as the active delivery target.
- Lightweight imperfection backlog table distinguishing safe deferrals
  from non-deferrable demo-blocking correctness and safety invariants.

### Fixed

- Public and private consumer consistency corrections under PROSE-007: updated
  roadmap date-gap Status cell to state that calendar infrastructure can wait
  for synthetic Demo v0 while unresolved scope-relevant local-data gaps block
  affected interpretation; scoped campaign-contract gates in `PROJECT_SPEC.md`
  to vendor acquisitions governed by that campaign, routing local CSV use to
  explicit authorization and the readiness audit; deduplicated Demo v0
  acceptance criteria to point exclusively at the roadmap Definition of Done
  anchor; clarified prospective Demo v0 All-Attempt Case Logging in
  `docs/north_star.md` while retaining universal trial retention; aligned
  `docs/project_overview.md` Recommended Next Direction with handoff STOP and
  Milestone 2; and synchronized the private exploration goal interpretation
  via an append-only clarification section preserving historical bytes.

- Contract-term and gate-namespace corrections under PROSE-006: replaced the
  backlog date-gap "next observed trade" restatement with "next observed source
  row"; disambiguated charter experiment/trial-ledger Stage 4, historical Track A
  Stage 4, and Milestone 4 in active Demo/logging prose; removed the timeless
  controller documentation-task ablation exemption; aligned cost wording with
  existing fixed-bps charges on undivided turnover; made Demo v0 All-Attempt
  logging prospective; pointed detailed Demo v0 definitions at the Definition of
  Done section; and aligned the September 13 diagnostic public wording with
  qualitative planning context only.

- Residual-copy and routing convergence under PROSE-005: replaced residual short floor
  summaries in `PROJECT_SPEC.md` and `docs/current_roadmap.md` with pointers to canonical `AGENTS.md`
  Research Safety Invariants and the blocking backlog table (F-001); clarified that local CSV
  `diagnostic_ready` is a separately authorized exploratory path strictly outside mandatory Demo v0
  acceptance, and public September 13 references are qualitative planning context only (F-002);
  reframed `Final Objective` in `docs/project_overview.md` as `Current Research-Platform Workflow`
  and added active governance documents (A-001); marked remaining Track A operational sections as
  historical protocol context and routed readiness active gates to Primary Milestones Demo v0 (A-002);
  and clarified PIT-006 backlog handling as failing closed with an affected-window block when terminal
  evidence is absent (A-003).

- Post-adjudication remediation under PROSE-004: replaced absolute sample-property
  phrase "no survivorship bias" and bare shorthand with the operational selection
  rule in `docs/north_star.md`, `PROJECT_SPEC.md`, `docs/current_roadmap.md`,
  and private addendum; clarified Demo v0 status in `README.md` as a target deliverable
  (not yet implemented) and quickstarts as legacy diagnostics; adopted `All-Attempt Case Logging`
  for Demo v0 run recording, distinguishing it from Stage 4 complete immutable ledger accounting;
  added historical protocol context to Track A handoff and roadmap headings; corrected
  the earlier log claim to reflect the actual 17-row backlog count; and aligned private
  addendum Item 5 title to synthetic-first demonstration.

- Remediation under PROSE-003: expanded `AGENTS.md` Research Safety Invariants
  with explicit non-deferrable boundaries (fail-closed ticker reuse/identity
  stitching, no default last-price or zero disappearance payoff, no dividend
  double counting, no incompatible price/volume dollar turnover); separated
  governance and goal-routing roles into unambiguous sentences in
  `docs/codex_long_running_controller.md` and `docs/research_method.md` with
  `docs/north_star.md` as the sole active goal owner; added provider date gaps
  row and removed false PIT-005 tag on survivorship in the canonical backlog;
  deduplicated milestone and backlog ownership to `docs/current_roadmap.md`;
  labeled Demo v0 as an unimplemented target and scoped the performance
  calculation statement in `PROJECT_SPEC.md`.

- Path B plan producer IDs no longer coerce missing/null to `[]`; plan
  validity timestamps parse as canonical UTC instants; the plan binds
  retained trial/seal tuples and relation; allocation authority compares
  the complete eight-field plan tuple; readiness binds `ledger_id`.
  DIAGNOSTIC_ONLY.

- Path B plan acceptance compares the complete plan tuple (including version,
  schema, and canonicalization) and relation; readiness
  `private_input_producer_actor_ids` no longer coerces missing/null to `[]`;
  EXECUTE consume requires canonical UTC instants; plan currentness is checked
  at allocation and start; plan and authorities bind the same ledger and start
  authority binds the complete readiness tuple including version.
  DIAGNOSTIC_ONLY.

- Path B ATTEMPT_ALLOCATED binds plan acceptance to the exact plan, attempt,
  trial, seal, and scope. ATTEMPT_STARTED enforces readiness role
  independence and missing role fields, and start-authority must bind
  operation `ATTEMPT_STARTED`. EXECUTE consume checks activation/expiry
  against transaction `as_of`. DIAGNOSTIC_ONLY.

- Path A catalog `get` refuses body/digest mismatch, appends snapshot
  catalog evidence through commit, SAMPLE_REGISTERED requires current
  projection, ACCESS authorities bind operation/sample/campaign and
  capability accessor, and trial allocation resolves projection and
  family identity. Exact replay returns `event_sha256`. Trial definitions
  bind experiment and complete code identity; publication approval binds
  sample/projection; allocation authority binds operation/campaign/trial/
  definition; seal revalidates allocation authority; resolvers compare
  schema/owner/canonicalization; ACCESS capabilities include activation
  and expiry. DIAGNOSTIC_ONLY.

### Added

- Walking Skeleton MVP: committed 50-stock static diagnostic cohort
  fixture under `DIAGNOSTIC_ONLY`, named operators `ts_delay`,
  `ts_delta`, `ts_rank`, `decay_linear`, and `cs_rank`, and a synthetic
  end-to-end pipeline through `MOM_12_1`, `REV_1M`, and `LOW_VOL_3M`
  with monthly Rank IC, ICIR, Newey-West t-stat, DSR, and equal-weight
  monthly rebalance at 5 bps slippage. The static cohort is not
  point-in-time universe evidence and is not a 14-trial run. This adds
  no private data, D8, A2, identity reopen, brokerage, or vendor API.

- Track B v7 Path B first checkpoint: extend the stdlib sqlite3 Path A
  ledger runtime with first-attempt `ATTEMPT_ALLOCATED` then valid
  `ATTEMPT_STARTED` after inventory/seal. Caller-supplied database path
  outside the repository, synthetic catalogs only, DIAGNOSTIC_ONLY.
  Unselected names refuse `WIRE_TYPE_NOT_SELECTED`. Retry and terminal
  attempt events are not appended. Path B does not claim ACCESS_COMPLETED
  or EXPOSURE_DECISION. This adds no private data, 14-trial run, D8,
  identity reopen, brokerage, or vendor API.

- Track B v7 Path A first checkpoint: stdlib sqlite3 ledger runtime with a
  caller-supplied database path outside the repository, synthetic catalogs
  only, and registry `0.10.0` ACCESS payload schemas. Happy path is epoch
  through local sample, trial, seal, ACCESS_INTENT, then ACCESS_STARTED.
  Path A stops before ACCESS_COMPLETED, does not append EXPOSURE_DECISION,
  and remains DIAGNOSTIC_ONLY. Unselected names refuse
  `WIRE_TYPE_NOT_SELECTED`. This adds no private data, 14-trial run, D8,
  identity reopen, brokerage, or vendor API.

### Changed

- Campaign runner execution P1 tests shrink and merge expensive synthetic
  14-trial panels. Rank IC omission now asserts eligible-cross-section IC
  pairs rather than forward-return row presence. Timing, leakage, cost, and
  ledger assertions remain. This adds no private data, D8, A2, identity
  reopen, or real 14-trial run.

- Track A PR 4 `run_campaign` now executes the 14 diagnostic trials from
  an input-bearing prepared campaign (`prices`, `anchors`, `listings`)
  under `DIAGNOSTIC_ONLY`. Authorized work returns
  `EXECUTED_DIAGNOSTIC_ONLY` with `trials_executed == 14` in inventory
  order via existing PR 3 machinery. Diagnostic payload, Rank IC, forward
  returns, continuous paths, and bundle children are taken from that
  execution: monthly Rank IC, execution-anchored `e=t+1` through `e+21`
  labels, scheduled execution resets, and parseable executed artifacts.
  The one-run attempt is reserved before trial execution. Benchmark paths
  are retained per factor, continuous resets omit cutoff-boundary signals,
  initial deployment is charged, held returns require exact boundary
  anchors, and invalid 25 bps paths fail hard validity. Precomputed
  result-bearing payloads are refused. `RESULT_ACCESS` and
  `PERFORMANCE_ACCESS` stay unexecutable. This adds no private data, D8,
  A2, identity reopen, or real 14-trial run.

### Fixed

- Monthly Rank IC omits ineligible listings instead of appending missing
  pairs that invalidate a month with eligible n>=100. A month with fewer
  than 100 eligible names stays invalid. Unscheduled listing
  dates are skipped in Rank IC, episode, freeze, continuous resets, and
  held-return representatives. Unscheduled lineage metadata cannot overwrite
  scheduled listing keys. Required Rank IC and episode outputs use the
  primary evaluation calendar, so a missing warm-up label does not
  invalidate those outputs. Continuous resets use primary-era
  `continuous_included` rows, including a December signal whose label ends
  in January. Fold-purged December months are retained as invalid Rank IC
  records and counted in `invalid_and_missing_summary.json`, including when
  the December listings key is omitted. A scheduled primary-era
  cutoff-boundary month with an incomplete label is retained as
  `EVALUATION_FOLD_LABEL_PURGED` when its listings key is omitted.
  Continuous resets still use that
  scheduled January execution. An empty 2018+
  calendar returns no required Rank IC/episode rows and cannot score
  warm-up as primary.
  Coverage gates use primary evaluation dates, including when that calendar
  is empty, so pre-2018 warm-up missing labels do not fail coverage.
  Evidence ceiling remains `DIAGNOSTIC_ONLY`. This adds no private data,
  D8, A2, or real 14-trial run.
- Closed remaining Track A PR 3 exact-head findings: ledger schema tests
  still collapse independent fail-closed axes for speed, but only after an
  equivalence check proves every representative delegates to the same
  constraint kind. Mixed field kinds can no longer hide a later-field
  schema regression behind `cases[0]`. F-1 and F-2 remain deferred. This
  adds no private data, result access, or 14-trial run.
- Closed remaining Track A PR 3 exact-head findings: a frozen signal set
  must contain every continuously included schedule row between its
  endpoints. Supplying January and March while February remains
  continuously included is refused, so January membership cannot stay in
  force across February execution. F-1 and F-2 remain deferred. This
  adds no private data, result access, or 14-trial run.
- Closed remaining Track A PR 3 exact-head findings: factor-matched
  benchmark comparison now requires the exact execution-bounded span for
  every nonempty frozen set, including a one-point path dated at signal
  close. A frozen decision on a `continuous_included=False` schedule row
  is refused, and the bounded endpoint may not exceed `accepted_cutoff`.
  The committed June-excluded July 1 through August 1 path is invalid.
  F-1 and F-2 remain deferred. This adds no private data, result access,
  or 14-trial run.
- Closed remaining Track A PR 3 exact-head findings: factor-matched
  benchmark comparison now binds to the accepted `CampaignSchedule` and
  requires the exact execution-bounded daily span from the first included
  execution through the execution following the last target. A contiguous
  sub-slice is invalid, including a February 28 start after a January 31
  frozen decision that omits the February 1 execution. Prefix and suffix
  truncation are refused. F-1 and F-2 remain deferred. This adds no
  private data, result access, or 14-trial run.
- Closed remaining Track A PR 3 exact-head findings: the factor-matched
  benchmark now applies a new monthly target at execution close so old
  holdings earn the incoming return, binds a daily path to the campaign
  schedule's exact ordered session slice and refuses sparse, duplicate,
  or reversed dates, and rejects a mixed-factor frozen-decision sequence.
  F-1 and F-2 remain deferred. This adds no private data, result access,
  or 14-trial run.
- Closed remaining Track A PR 3 exact-head findings: factor-matched
  benchmark comparison now maps daily execution-calendar points onto
  monthly frozen decisions and resets membership only at the next
  factor-month, and evidence-bundle assembly requires one structured
  status for every reconciled inventory trial. Empty, short, duplicate,
  and unknown-trial status lists are invalid. F-1 and F-2 remain
  deferred. This adds no private data, result access, or 14-trial run.
- Closed remaining Track A PR 3 exact-head findings: random-rank seeds
  now hash only the frozen factor-month identity and refuse caller
  overrides; factor-matched benchmark comparison requires the same
  session on each decision, held-return interval, and strategy point;
  evidence-bundle assembly fails unless every detached-root binding is
  present and well-typed; lineage `adjusted_close` and referenced prices
  that are Boolean or text invalidate eligibility and simple returns;
  and computed factor values that are non-finite are invalid even when
  the anchors were finite and positive. F-1 and F-2 remain deferred.
  This adds no private data, result access, or 14-trial run.
- Closed remaining Track A PR 3 exact-head findings: `authorize` now
  refuses unless `RunConfig.environment_id` and
  `environment_lock_sha256` match the accepted record calendar, and a
  grant must list `TRACK_A_PR3_PLANNING` in `now_eligible`. Empty or
  unrelated eligibility still refuses, and planning-only grants still
  cannot emit a result-bearing run. F-1 and F-2 were not authorized.
  This adds no private data, result access, or 14-trial run.
- Closed owner-authorized Track A PR 3 FIX-4 findings F-3, F-4, and F-5:
  Rank IC now invalidates a month when any pair member is missing, Boolean,
  or non-finite; evidence-bundle assembly fails when a frozen protocol or
  trial-inventory digest field is missing or not 64-hex; and diagnostic
  real vectors reject Boolean or non-finite members before conversion.
  F-1 and F-2 were not authorized. This adds no private data, result
  access, or 14-trial run.
- Closed remaining Track A PR 3 exact-head findings: eligibility now refuses
  listings whose referenced factor prices do not match the paired lineage
  `adjusted_close` values, and evidence-bundle assembly rejects protocol or
  trial-inventory children that violate carried frozen digests. Calendar
  mismatch still refuses before `AUTHORIZED`, planning-only grants still
  authorize the `TRACK_A_PR3_PLANNING` code path without opening a
  fourteen-trial run, and return anchors remain lineage-bound. This adds no
  private data, result access, or 14-trial run.
- Closed remaining Track A PR 3 exact-head findings: planning-only grants
  still authorize the code-and-fixture path but refuse a result-bearing run,
  return anchors must match the paired lineage `adjusted_close` values, the
  runner no longer loads an unbound prepared campaign file, and missing
  required trial outputs classify as `INVALID_DIAGNOSTIC`. Calendar binding
  from FIX-1 remains in force. This adds no private data, result access, or
  14-trial run.

### Added

- Added the Track A PR 3 EXEC-5 repo-integration surface: import-boundary,
  no-default, and T-7 owner-uniqueness conformance tests, the public-safe
  bounded-runner design note, a repo-map refresh, and CI wiring that runs
  only committed synthetic campaign fixtures. Existing frozen campaign
  modules are unchanged. This adds no private data, result access, or
  14-trial run.
- Added the Track A PR 3 EXEC-3 continuous path, cost, benchmark, and
  metric surface: drifted-weight holdings, post-return-equity cost, the
  factor-matched primary comparison, SPY secondary retention, and path
  metrics. D-1 now binds those goldens to `campaign.paths` instead of the
  generic backtester. Existing frozen campaign modules are unchanged.
  This adds no private data, result access, or 14-trial run.
- Added the Track A PR 3 EXEC-2 decision-time eligibility, baseline-target,
  and diagnostic surface: the five frozen-at-`t` objects, the three named
  zero-target triggers, equal-weight and random-rank targets, the static
  episode return, Spearman Rank IC, decile-curve diagnostics, and the
  post-`t` mutation oracle. Existing frozen campaign modules are unchanged.
  This adds no private data, result access, or 14-trial run.
- Added the Track A PR 3 EXEC-1 decision-time spine: a derived factor
  registry, `factor_anchor_lineage_v1`, the common-session schedule, and
  one simple adjusted-close return gate, each bound to committed synthetic
  fixtures. Existing frozen campaign modules are unchanged. This adds no
  private data, result access, or 14-trial run.
- Published Track A PR 2 public-safe validator, status hashes, allowlisted
  projection, and safe dataset-review fields. Raw private data stays out.

### Changed

- Replaced the 837-line active handoff with a bounded operational checkpoint,
  moved unique historical audit identifiers into the engineering log, restored
  permanent handoff/controller/roadmap routing, and added guards against stale
  PR narratives and future active-document regrowth.
- Consolidated repository governance so `AGENTS.md` owns authority and research
  safety, the controller owns staged workflow and review lifecycle, and the
  charter and roadmap reference those sources instead of repeating polling,
  push, review, or merge policy. The roadmap now reflects PR #177's protected
  merge and current private evidence gate. Structure tests verify ownership,
  references, and explicit authorization boundaries rather than duplicated
  prose or handoff review history.

### Added

- Added a frozen `campaign` protocol-core package for canonical listing-key
  bytes, scalar three-factor anchors, deterministic deciles, factor
  target-to-target turnover, Holm adjustment, prepared-segment circular block
  bootstrap, common-complete-case robustness, and ordered diagnostic-state
  classification. Named factor bindings permanently fix `MOM_12_1`, `REV_1M`,
  and `LOW_VOL_3M`; AST guards keep the package dataset-independent, and
  conformance tests reuse the existing drift-aware strategy turnover and cost
  accounting instead of duplicating them. This adds no data ingestion, runner,
  private-data access, result execution, or empirical interpretation.
- Added the owner-approved EODHD historical S&P 500 diagnostic campaign scope
  reset. R1I is complete, the accepted 37-event work is preserved as optional
  `full_ledger_profile_v1`, and the public protocol freezes exactly three
  price-only factors and 14 semantic trials. Track A may proceed through a
  private entitlement/license gate, blinded dataset review, bounded runner,
  and repository-external evidence bundle without first implementing the
  formal ledger runtime. Track B remains required before prospective
  performance access and is limited to 8-12 conceptual event families. The
  protocol also freezes decision-time eligibility independently of all future
  availability, canonical listing-key bytes, all-in fixed-bps cost semantics,
  and an exhaustive deterministic final-state decision tree. Review remediation
  further pins the 63-return low-volatility slice, the only three decision-time
  zero-target conditions, an exact-byte YAML evidence child, and an exact-byte
  14-trial inventory child. Final-state robustness now uses only the primary
  common complete-case Rank IC table with an outcome-independent required-year
  set, all required years in the yearly denominator, and exact required-year
  omissions. A missing required factor-matched primary comparison is a hard
  `INVALID_DIAGNOSTIC` failure, while a missing secondary SPY comparison is
  retained as descriptive-only evidence with no final-state effect. Factor
  turnover always uses the immediately preceding
  scheduled frozen decision-time target, so an outcome-invalid middle month
  cannot make later turnover skip to the last outcome-valid target. Execution
  cost now follows the accepted post-return-equity order and includes the
  gross multiplier in both portfolio and security-level return impacts. The
  random-rank continuous baseline is frozen net at the primary 10-bps case,
  while episodic baseline diagnostics remain gross and cost-free. Its random
  target now uses the signal date in the seed, treats the permutation as high-
  to-low rank, selects the first remainder-aware top-decile chunk, and
  serializes equal weights by canonical key; the semantic inventory remains
  exactly 14. Holm adjusted p-values now explicitly use one-based mathematical
  indices with Python `k-1` access, a capped sorted running maximum, stable
  factor-order tie breaking, and mapping back to original factor order.
  `LOW_VOL_3M` now explicitly uses adjacent adjusted-close simple returns and
  requires exactly 64 finite, strictly positive real non-Boolean anchors;
  invalid anchors are retained and counted with no fill or log-return fallback.
  Diagnostic endpoint returns likewise use fail-closed adjusted-close simple
  returns. Bootstrap interval and null distributions now share one exact block-
  index draw per replicate/segment across all factors, with no second RNG pass.
  Long segments now use circular starts over every within-segment position;
  wrapping never crosses a segment boundary, and truncation preserves uniform
  expected row inclusion even when segment length is not divisible by six. A
  63-record exhaustive golden rejects the former non-circular boundary weights
  and nonzero centered-null expectation.
  Momentum and reversal now require every referenced numerator and denominator
  anchor to be a finite, strictly positive real non-Boolean value; invalid
  anchors are retained, excluded, and counted without repair. Their 253/22
  lookbacks are common-calendar position spans, not contiguous-price screens:
  exactly the two formula anchors must be observed, while an unreferenced
  interior missing value has no factor-value or eligibility effect. The
  decision-time gate now uses those same factor-specific position/anchor rules
  rather than a contradictory full-history flag. Prospective counting starts
  only at the first eligible signal strictly after the latest protocol, runner-
  code, and dataset-policy freeze timestamp; prior months cannot be backfilled.
  That signal must have all three factor rebalances decision-time valid; a
  subset-valid month is retained but does not increment the 12/24 clock. The
  random-rank baseline inherits the factor's three invalid-month triggers and
  retains an invalid zero-target/full-cash output without treating episodic
  missingness as zero or consuming a random permutation. The equal-weight
  baseline and primary benchmark instead remain invested in a nonempty unique
  eligible universe on sparse/tied factor months; their return is not replaced
  by cash. The zero-target strategy month, invested benchmark return,
  liquidation/redeployment turnover, costs, and active return remain in one
  unfiltered continuous path used by economic support; removing a month or
  restarting the path is forbidden. Continuous strategy targets are also
  calendar-filtered before freeze to require their next monthly execution on or
  before the accepted cutoff. A boundary signal with a complete diagnostic
  label but a later execution beyond cutoff remains a factor diagnostic and
  cannot become a hard-invalid strategy target. Prospective boundaries now use
  timezone-aware freeze instants normalized to UTC and official frozen-calendar
  XNYS close instants converted to UTC, with strict instant ordering for same-
  day freezes. The 12/24 counter is operational only: protected opening waits
  strictly beyond the later of the threshold signal's `e+21` label close and
  following monthly execution close, without bypassing Track B logging or
  separate access authorization. The latest prospective anchor also requires
  completed detached run binding of the exact protocol, inventory, accepted
  data, runner code, configuration, and environment identity; runner-code
  freeze alone cannot start or increment the window. That binding now freezes
  an immutable historical seed/cutoff and an append-only prospective succession
  policy rather than pretending to hash future bytes. Consecutive previous-
  hash/batch-hash records extend strictly increasing session bounds without
  resetting the original anchor; corrections append audit records and cannot
  overwrite or retroactively recompute frozen signals. Every factor-input
  price anchor now also carries the accepted normalized permanent-security,
  listing, and listing-episode identity. Symbol-change traversal is allowed
  only for an evidenced rename inside that exact identity; ticker reuse,
  relisting, venue/listing moves, share-class changes, distinct successor
  securities, and ambiguous alias chains fail closed. Rename and reused-ticker
  fixtures reject ticker-text-only stitching. Continuous factor-strategy,
  long-only baseline, and primary factor-matched benchmark held returns now
  use one adjacent common-calendar adjusted-close simple-return policy. A
  split fixture rejects raw-close return, drifted-weight, turnover, cost, and
  active-return contamination; missing anchors fail closed and separate split
  or dividend cash-flow addition is forbidden as double counting. Baseline
  21-row episode outputs now freeze a factor-matched signal-time target and
  hold its execution weights statically through `e+21`, independent of an
  intervening monthly continuous reset. Their exact weighted constituent
  adjusted-close formula fails the whole episode on any invalid target return
  without survivor renormalization, fill, cash, or zero substitution.
  Bootstrap segments of two through
  six rows now use genuine one-row within-segment resampling, with a
  nondegenerate-support gate that prevents false Holm support and is an
  explicit all-three-factor classifier coverage input. Listing keys
  freeze once campaign-wide at earliest any-factor eligibility, so later
  factor eligibility cannot re-encode an endpoint. Repository
  governance fixes safe in-scope review findings without owner round trips and
  keeps the task active through current-head review and remediation; only a
  genuinely critical owner-decision follow-up retains the four-run,
  thirty-minute cap. This release changes no research runtime, data, or
  performance output.
- Added the bounded Stage 4B-R1I attempt-start release. The owner selected
  bundle `R1I-A`, freezing the exact earlier attempt-allocation reference, a
  complete digest-pinned external readiness record, separate start-actor
  authority, reviewer/executor/allocation/plan role independence, and one
  ledger-owned `cap_<32 lowercase hex>` one-shot execution capability
  identity with fail-closed lost-ack, currentness, single-start, and atomic
  consumption rules. A separate immutable registry and digest at version
  `0.9.0` preserve R0 through R7 byte and behavior authority while promoting
  only `ATTEMPT_STARTED`; the other 26 events remain fail closed. This adds no
  external resolver, authority/capability service, append/storage backend,
  executor, artifact, protected-access, private-data, research, brokerage,
  order, paper, or live behavior.
- Added the bounded Stage 4B-R1H attempt-allocation release. The owner selected
  bundle `R1H-A`, freezing `att_<32 lowercase hex>`, singleton campaign scope,
  exact earlier trial-allocation and initial inventory-seal evidence, a
  complete digest-pinned external attempt plan, separate independent
  acceptance and allocation-actor authorities, and closed first-attempt/retry
  relations with monotonic policy-bounded ordinals. A separate immutable
  registry and digest at version `0.8.0` preserve R0 through R6 byte and
  behavior authority while promoting only `ATTEMPT_ALLOCATED`; the other 27
  events remain fail closed. This adds no retrieval/currentness runtime,
  append/storage backend, dependency, attempt start/execution, artifact,
  private data, protected access, or trading behavior.
- Added the bounded Stage 4B-R1G campaign-inventory seal release. The owner
  selected bundle `R1G-A`, freezing singleton campaign scope, exact campaign
  allocation, a complete digest-pinned external canonical inventory, separate
  independent acceptance and seal-actor authorities, a 1-to-4096 trial
  schema/review bound, and the exact nonrecursive pre-seal ledger head. A
  separate immutable registry and digest at version `0.7.0` preserve
  R0/R1/R2/R3/R4/R5 byte and behavior authority while promoting only
  `CAMPAIGN_INVENTORY_SEALED`; the other 28 events remain fail closed. This
  adds no retrieval/currentness runtime, append/storage backend, dependency,
  private data, research trial, attempt, protected access, or trading
  behavior.
- Added the bounded Stage 4B-R1F semantic trial-allocation release. The owner
  selected bundle `R1F-A`, freezing `trl_<32 lowercase hex>`, singleton
  campaign scope, exact prior campaign/experiment/family/sample evidence, a
  complete canonical external trial definition with separate
  acceptance/publication/actor-authority records, and closed relation and
  code-identity unions. A separate immutable registry and digest at version
  `0.6.0` preserve R0/R1/R2/R3/R4 byte and behavior authority while promoting
  only `TRIAL_ALLOCATED`; the other 29 events remain fail closed. This adds no
  external retrieval/currentness runtime, append/storage backend, dependency,
  private data, research trial, execution attempt, protected access, or
  trading behavior.
- Added the bounded Stage 4B-R1E binding release. The owner selected bundle
  `R1E-A`, freezing closed trial-family/sample and
  local-registration/external-reference campaign-binding branches, singleton
  campaign scope, exact source event ID/hash, one campaign-scoped external
  Stage 3 sample-reference origin, and stable cross-campaign reuse of the same
  external-origin `sample_id`. A separate immutable registry and digest at
  version `0.5.0` preserve R0/R1/R2/R3 byte and behavior authority while
  promoting only `CAMPAIGN_ENTITY_BOUND` and
  `STAGE3_SAMPLE_REFERENCE_BOUND`; the other 30 events remain fail closed.
  This adds no source resolver, currentness/path runtime, append/storage
  backend, dependency, private data, research trial, protected access, or
  trading behavior.
- Added the bounded Stage 4B-R1D local sample-registration release. The owner
  selected bundle `R1D-A`, freezing `smp_<32 lowercase hex>`, the common
  32-campaign direct-scope maximum, a digest-pinned external Stage 3
  sample-record authority, separate acceptance and publication-approval
  records, mutually exclusive local/global/external representation paths,
  stable lineage identity, anti-reset/currentness rules, and private complete
  records with allowlisted public projections. A separate immutable registry
  and digest at version `0.4.0` preserve R0/R1/R2 byte and behavior authority
  while promoting only `SAMPLE_REGISTERED`; the other 32 events remain fail
  closed. This adds no retrieval/currentness runtime, binding event,
  append/storage backend, dependency, private data, research trial, protected
  access, or trading behavior.
- Added the bounded Stage 4B-R1C trial-family registration release. The owner
  selected bundle `R1C-A`, freezing `fam_<32 lowercase hex>`, an immutable
  external family-definition catalog/record tuple, a separate digest-pinned
  acceptance record with reviewer independence, stable family identity,
  monotonic current generations, explicit `supersedes`/`depends_on` relations,
  anti-reset rules, and a common direct-scope maximum of 32. A separate
  immutable registry and digest at version `0.3.0` preserve R0/R1 byte and
  behavior authority while promoting only `TRIAL_FAMILY_REGISTERED`; the other
  33 events remain fail closed. This adds no retrieval, authority runtime,
  append/storage backend, dependency, research trial, protected access,
  private data, or trading behavior.
- Added the bounded Stage 4B-R1B schema release. The owner ratified
  `exp_<32 lowercase hex>` as the exact experiment namespace; a separate,
  immutable registry and digest at version `0.2.0` preserve R0 byte-for-byte
  while supporting exactly epoch plus reservation-only
  `CAMPAIGN_ALLOCATED` and `EXPERIMENT_ALLOCATED`. Explicit release selection,
  independent fixtures, subject/scope/namespace attacks, arbitrary-promotion
  rejection, and complete `tagged_union`, `array_contains_path`, and
  `safe_public_id` meta-tests keep the other 34 events fail closed. This adds
  no append/storage runtime, dependency, campaign, trial, attempt, protected
  access, private data, or trading behavior.
- Added the design-only Stage 4B-R1A allocation/registration architecture-A
  contract. It preserves the accepted R0 authority byte-for-byte, retains the
  37-event vocabulary, selects reservation-only campaign/experiment
  allocation, entity subjects, explicit campaign scope, a separately versioned
  closed R1 schema language, and requirements for future exact reference-based
  family and Stage 3 sample authorities. It accepts neither authority,
  promotes no event, adds no runtime or dependency, and creates no trial,
  attempt, protected access, private data, or trading behavior.
- Added the Stage 4B-R0 fail-closed ledger schema-registry foundation in a
  separate `ledger` namespace. It packages a self-contained canonical JSON
  registry and digest, rejects duplicate raw JSON properties and unsafe
  numbers before mapping, freezes the closed 37-event vocabulary, validates
  the exact accepted epoch schema, and rejects the other 36 known events as
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. This is not complete payload-registry
  acceptance or a ledger runtime and adds no backend, data access, research
  trial, dependency, or trading behavior.
- Added the Stage 4a experiment and trial ledger design contract. It separates
  semantic trials from execution attempts; freezes durable preallocation,
  campaign inventory/closure, failure and artifact retention, protected-access
  capabilities, canonical chained events, independently retained checkpoints,
  review binding, and private/public projections; and adds a synthetic golden
  epoch event, rejection/semantic fact vectors, and a 15-case later-runtime
  matrix. A nonrecursive pre-seal stream-head anchor is bound inside each
  campaign-inventory seal and atomically checked before the first attempt or
  protected access; it is distinct from the later independently retained
  closure checkpoint. A separate exact, version-linked, independently retained
  adjudication checkpoint anchors the final closure/review/promotion/
  adjudication chain; any later campaign-scoped event makes it non-current.
  The closure checkpoint now has an exact canonical preimage and digest whose
  all-and-only campaign prefix, cutoff, freeze, inventory, trial/attempt
  counts, and unique ordered reference are deterministically checked.
  Formal currentness remains fail closed until Stage 4b selects and verifies an
  independent append-only anti-rollback/latestness authority. The epoch
  atomically introduces `ledger_id`; its
  external `actor_id` is claimed attribution only and grants no permission.
  Exact schemas for `TRIAL_ALLOCATED` and the rest of the closed event
  vocabulary remain a Stage 4b prerequisite. It does not implement or select
  an identity provider, authorization mechanism, ledger backend, legacy-log
  migration, data access, dependency, or research trial.
- Added the accepted provider-agnostic point-in-time data methodology contract.
  It separates methodology acceptance, dataset-manifest review, and
  run-specific formal-interpretation eligibility; freezes provenance/license,
  canonicalization/environment identity, immutable non-self-issued dataset
  review, bitemporal universe and field availability, corporate actions,
  adjustment semantics, calendars, benchmark/risk-free, typed missingness,
  privacy, and protected-sample requirements; and adds a deterministic 14-case
  documentation matrix plus an RFC 8785/JCS synthetic canonical-byte golden
  fixture without approving a vendor, dataset, or real-data interpretation.
- Implemented the accepted signal, execution, and metric timing contract for
  an after-close signal and next-observed-close idealized target reset. The
  runtime now enforces nonzero source-row lag, exact axes/bounds, decision-time
  targets, ordered price/solvency gates, common strategy/benchmark metric rows,
  terminal behavior, typed metadata, and the Stage 2b behavior matrix.
- Added mandatory `tracked_pre_mutation_source_snapshot_v1` provenance to the
  close-only backtester. A controlled coordinate ledger distinguishes native
  or bounded complex values from tracked post-capture out-of-window dtype
  propagation and rejects stale/untracked/tampered later state. Direct and
  nested provenance objects are refused by experiment-log serialization;
  current committed logs carry only allowlisted policy/status metadata.
- Added the accepted purged and bounded chronological split contract with six
  explicit inclusive boundaries, complete label-interval ownership, a hard
  bounded test cutoff, horizon-aware purge, optional embargo, raw-axis target
  masking, warm-up/down metadata, and a deterministic 22-case Stage 1b test
  matrix. This design stage changes no research calculation or evidence.
- Added the canonical research program charter and reconciled the project
  specification, roadmap, handoff, controller, staged workflow Skill, public
  method routing, and documentation contracts around factor-to-execution
  evidence layers, point-in-time methodology, complete trial accounting,
  protected-sample access, statistical controls, and independent reproduction.
- Recorded the verified timing/sample blockers and classified the previously
  examined 2025-05-01 through 2026-05-31 interval as historical evaluation or
  pseudo-holdout evidence rather than a presumed pristine holdout.
- Completed a full repository conformance audit with no actionable P1/P2
  findings and linked the merged report from the current project records.
- Implemented signed trade weights, completed-episode hit rate and average
  holding-period return, exact applied-cost allocation, terminal-open counts,
  audit metadata, and refreshed synthetic evidence.
- Approved continuous positive-weight holding episodes, signed-trade evidence,
  net contribution over deployed weight, applied-cost allocation, and explicit
  terminal-open handling for future episode metrics.
- Implemented the optional long-only position cap with clip-without-
  renormalization behavior, residual cash, strict validation, backtester
  integration, and audit metadata.
- Approved the design contract for an optional long-only position cap applied
  after selection and before trade calculation, with clipping, no
  renormalization, and explicit residual cash.

### Fixed

- Rejected every leap-second timestamp from the Stage 4a ledger event schema
  because no immutable leap-second table is pinned, while preserving
  proleptic-Gregorian year `0000`, ordinary UTC ranges, and normalized
  arbitrary-precision fractional seconds without changing canonical JSON
  serialization.
- Added an independently retained adjudication-checkpoint contract and
  deterministic tail-tamper/currentness vectors so a valid evidence-freeze
  checkpoint cannot be mistaken for proof that later closure, review,
  promotion, and adjudication records were retained.
- Closed coordinated evidence-checkpoint substitution paths by recomputing the
  exact campaign prefix and checkpoint digest, checking freeze facts and the
  all-and-only freeze-to-closure campaign reference interval, and retaining
  explicit Stage 4b payload/currentness gates.
- Made the latest controlled bounded real/complex assignment authoritative
  when recovering a real column after an out-of-window complex dtype upcast,
  including when a later out-of-window non-real write changes the container to
  object.
- Made completed current-head Codex review with no unresolved actionable
  findings an explicit prerequisite before auto-merge or normal protected
  merge for review-required PRs.
- Froze the intended Ruff lint baseline explicitly so a newly released Ruff
  version cannot silently expand CI into a repository-wide lint migration.
- Aligned the active real-data readiness Skill and checklist with the charter:
  static or otherwise unverified historical membership is diagnostic-only,
  formal readiness requires implemented program gates, and the current
  experiment log is explicitly not the future immutable all-trial ledger.
- Scoped PR pause rules to required predecessor and current-stage PRs so an
  unrelated Draft cannot become an accidental global workflow gate.
- Streamlined the public README and workflow diagram, removed the unused
  plotting dependency, completed package metadata, and added lint/build CI
  gates.
- Replaced the accumulated checkpoint chain with a concise canonical roadmap
  and current handoff aligned to the merged implementation baseline.
- Vectorized capped liquidity-universe ranking while preserving per-date
  selection, missing-ranking counts, and input-column-order tie breaks.
- Aligned candidate volume-aware slippage diagnostics with drift-aware
  portfolio accounting by exposing per-asset trade weights from the backtester
  and accepting those weights through an explicit diagnostic entrypoint. The
  consecutive-target interface remains available as a labeled compatibility
  path. Raw helper impact is labeled as post-return portfolio-value basis and
  converted to beginning-period return basis when explicitly applied.
- Hardened shared numeric panel validation to reject duplicate asset columns
  and positive or negative infinity while continuing to preserve real `NaN`
  missing values, and made strict long-price CSV loading reject sparse
  date-symbol grids created during pivot with the first missing cell identified.
- Corrected simulated portfolio accounting so holdings drift with asset
  returns between scheduled rebalances and turnover is measured against
  drifted pre-trade weights instead of prior targets. Refreshed affected
  synthetic reports and experiment logs under the same research-only caveats.
- Corrected close-time fixed transaction-cost and slippage impacts so
  drift-adjusted turnover is charged against post-return portfolio value, and
  fail explicitly when asset returns plus any trading-cost impact exhaust the
  simulated portfolio.
- Corrected the explicit benchmark `zero_return` fallback so missing benchmark
  dates freeze at the last observed price, including an observation before the
  first strategy date, without discarding the cumulative move when observations
  resume.

### Added

- Added benchmark-relative `tracking_error` as annualized population volatility
  of exact-date aligned daily net strategy returns versus cost-free benchmark
  returns. The metric excludes the synthetic first row, includes the terminal
  observed return window, rejects missing or imputed benchmark returns, records
  its audit contract, and is included in deterministic synthetic reports,
  experiment logs, and the experiment registry.
- Added the Stage 2 tracking-error design contract for daily close-to-close
  active-return volatility, including net strategy cost basis, cost-free
  benchmark returns, exact index/timezone alignment, first-row and terminal
  window semantics, validation errors, metadata, and the implementation test
  matrix. No tracking-error code or generated evidence was added.
- Added active-date average holding count plus gross-normalized average and
  maximum position-concentration HHI to simulated backtest metrics, synthetic
  reports, experiment logs, and parameter sweeps.
- Added the canonical risk/evaluation metrics design, selecting active-date
  holdings count and normalized HHI for the first implementation while
  deferring tracking error, episode metrics, and constraints to separate
  reviewed stages.
- Added `research/eodhd_limited_factor_diagnostics_brief.py` with a
  private-output-only neutral diagnostics brief runner, plus synthetic tests
  and a docs checkpoint that reports allowed diagnostic direction, magnitude,
  and split consistency without strategy, backtest, portfolio, investment,
  profitability, alpha, or trading-readiness claims.
- Added `research/eodhd_limited_factor_diagnostics_review.py` with a
  private-output-only limited factor diagnostics review runner, plus synthetic
  tests and a docs checkpoint that summarizes allowed diagnostics only without
  strategy, backtest, portfolio, investment, profitability, alpha, or
  trading-readiness interpretation.
- Added `research/eodhd_factor_diagnostics_readiness_review.py` with a
  private-output-only EODHD factor diagnostics readiness review runner, plus
  synthetic tests and a docs checkpoint that records readiness metadata without
  strategy, backtest, portfolio, or performance interpretation.
- Added `research/eodhd_factor_diagnostics_experiment_log.py` with a
  private-output-only EODHD factor diagnostics experiment-log handoff runner,
  plus synthetic tests and a docs checkpoint that records required readiness
  fields without strategy, backtest, portfolio, or performance interpretation.
- Added `research/eodhd_factor_diagnostics_dry_run.py` with a private-output
  EODHD factor diagnostics dry run, plus synthetic tests and a docs checkpoint
  that keeps IC, Rank IC, and quantile-spread diagnostics separate from
  strategy, backtest, portfolio, and performance interpretation.
- Added `docs/eodhd_data_quality_diagnostics_checkpoint.md` to record the
  completed private EODHD no-performance data-quality diagnostics dry run,
  aggregate readiness counts, open caveats, and the next docs-only
  factor-diagnostics planning boundary.
- Added `docs/eodhd_loader_smoke_checkpoint_and_diagnostics_dry_run_plan.md`
  to record the completed private EODHD validation-only loader smoke test,
  aggregate loader/schema evidence, private-output boundary, and the next
  no-performance diagnostics dry-run stop conditions.
- Added `docs/eodhd_local_csv_loader_smoke_test_plan.md` to scope the next
  validation-only loader smoke test for the private EODHD bundle, including
  allowed existing-loader checks, private-output location, stop conditions,
  and caveats before any source, test, report, strategy, or performance work.
- Added `docs/eodhd_local_csv_validation_handoff.md` to record the
  documentation-only handoff for the completed private EODHD local CSV
  validation-only dry run, including aggregate loader/schema evidence,
  static-universe and adjustment-policy caveats, placeholders for sample
  splits and costs/slippage, and the stop-before-strategy next-stage boundary.
- Added `docs/local_csv_validation_dry_run_intake_checklist.md` as a concise
  user-facing intake checklist for local CSV validation-only dry runs before
  Codex inspects user-provided files.
- Added `docs/local_csv_readiness_input_checkpoint.md` to make the required
  user-provided local CSV readiness package explicit before any real-data
  interpretation, while preserving the default pause at the readiness boundary.
- Refreshed the roadmap gap checkpoint after the local fixture configured-case
  output sequence, routing the next default stage to user-provided local CSV
  readiness inputs instead of more synthetic output.
- Refreshed the committed synthetic local fixture Markdown report and JSON
  experiment log with the opt-in configured-case summary, preserving every
  configured case/split row and invalid reason without changing registry
  output.
- Added opt-in local fixture configured-case report/log wiring so the
  committed synthetic fixture workflow can include all-case/all-split summary
  rows in ad hoc outputs without refreshing committed generated artifacts.
- Added protected PR merge governance so non-high-risk PRs authored/pushed by
  `minqiyang` may use GitHub auto-merge or normal protected PR merge only after
  author/head-owner, branch protection, required checks, required reviews, and
  changed-file scope are verified, while direct `main` pushes, protection
  bypass, and `--admin` remain forbidden.
- Added local fixture configured-case summary support with focused tests that
  preserve every configured case/split row, invalid reasons, and separately
  inspectable cost/slippage diagnostic fields without regenerating reports.
- Added paused external PR gate governance so an open or not-verified-merged PR
  is reported once, then treated as an external wait state without repeated
  GitHub checks, gate reports, pause notes, goal completion, or blocked status
  unless the user explicitly resumes, says the PR merged, or asks for PR
  inspection.
- Added `docs/local_fixture_robustness_report_refresh_plan.md` to define the
  documentation gate for applying all-case, split-aware robustness reporting to
  committed synthetic local CSV fixtures before changing fixture workflows or
  generated outputs.
- Added `docs/post_synthetic_robustness_generated_output_checkpoint.md` to
  record the completed synthetic split-aware robustness plan,
  implementation, report/log support, generated-output refresh, and next
  local-fixture robustness planning boundary.
- Added the committed synthetic split-aware robustness Markdown report, JSON
  experiment log, and refreshed experiment registry with all-case and
  invalid-case diagnostics preserved as synthetic-only outputs.
- Added PR-gate governance that pauses after one current-state check when a
  previous-stage PR is not verified merged, avoiding repeated PR polling or
  baseline validation while the gate remains unresolved.
- Added opt-in Markdown report and JSON experiment-log support for the
  synthetic split-aware robustness demo while keeping default module execution
  free of committed generated-output changes.
- Added a deterministic synthetic split-aware robustness demo that reports
  every configured signal case across train, validation, and test splits,
  including invalid diagnostics, without writing generated reports or logs.
- Added `docs/synthetic_robustness_validation_plan.md` to define the
  documentation gate for future synthetic/local-fixture robustness summaries,
  including split policy, all-case reporting, missing-data stop conditions,
  future tests, and future report/log fields before implementation.
- Added `docs/post_precomputed_volume_aware_slippage_checkpoint.md` to record
  the completed volume-aware slippage integration design, test-plan,
  precomputed-impact implementation, and synthetic generated-log refresh
  sequence, and to route the next safe stage toward a documentation-only
  roadmap gap refresh.
- Added an explicit precomputed volume-aware slippage impact path to the local
  backtester, with deterministic tests and separate result, metric, and
  assumption fields while keeping `diagnostic_only` as the default and leaving
  generated reports unchanged.
- Added `docs/volume_aware_slippage_backtester_integration_test_plan.md` to
  define the deterministic unit, integration, failure-mode, guardrail,
  result-field, audit-field, report-field, and experiment-log tests required
  before any future volume-aware slippage backtester implementation.
- Added `docs/volume_aware_slippage_backtester_integration_design.md` to
  define a documentation-only boundary for any future integration of the
  existing volume-aware slippage diagnostic helper into simulated backtester
  accounting, including required inputs, strict stop conditions, reporting
  fields, tests, non-goals, and the next test-plan stage.
- Added `docs/post_local_fixture_slippage_output_refresh_checkpoint.md` to
  record the post-PR #94 generated-output refresh state, keep volume-aware
  slippage diagnostic-only, and route the next safe stage toward a
  documentation-only backtester integration design.
- Added a context-budget and retrieval policy to the long-running controller
  and staged workflow Skill so future continuations start from the handoff and
  repo map, avoid broad parallel reads of long logs/reports, and recover
  safely from truncated tool output. The policy also keeps `current_handoff`
  and `repo_map` as short entry/index files and directs long log and changelog
  access through tail, keyword search, stats, or small snippets by default.
- Refreshed the synthetic local CSV fixture report, JSON experiment log, and
  experiment registry so the generated artifacts include the volume-aware
  slippage smoke diagnostic while preserving the no-backtest and
  no-profitability boundary.
- Added `docs/post_volume_aware_slippage_smoke_checkpoint.md` to record the
  completed volume-aware slippage design/helper/local-fixture smoke sequence
  and route the next safe stage toward synthetic generated-output refresh
  before any backtester integration.
- Added a synthetic local CSV fixture smoke diagnostic that calls the
  volume-aware slippage helper on fixed diagnostic target weights and reports
  participation plus rejected/cap counts without applying slippage to returns
  or changing backtester behavior.
- Added a synthetic-only volume-aware slippage diagnostic helper with
  deterministic tests for lagged rolling dollar volume, explicit notional
  scaling, participation, missing/zero liquidity, and participation caps
  without changing backtester returns or generated reports.
- Added `docs/volume_aware_slippage_design.md` to define a documentation-only
  design gate for future lagged dollar-volume, participation, missing/zero
  volume, notional-scale, cap-policy, and caveat handling before any
  volume-aware slippage implementation.
- Added `docs/current_handoff.md`, `scripts/repo_map.py`, and
  `docs/repo_map.md` workflow controls so future Codex stages can start from a
  concise durable handoff, regenerate a short repo map, and preserve capped
  command-output discipline without weakening safety guardrails.
- Added `docs/post_slippage_cost_checkpoint.md` to record that the fixed-bps
  slippage design, implementation, and synthetic report/log refresh sequence is
  complete, and to route future volume-aware slippage work through a
  documentation-only design gate.
- Refreshed synthetic backtest reports, JSON experiment logs, and the
  experiment registry so fixed-bps transaction cost, fixed-bps slippage,
  zero-slippage diagnostics, and total trading cost impact are explicit after
  the local backtester slippage extension, with related slippage planning docs
  synced to the current implementation state.
- Added a narrow fixed-bps `slippage_bps` extension to the simulated
  backtester, keeping slippage impact separate from transaction-cost impact
  and recording explicit diagnostic assumptions without adding real data,
  broker/order logic, or generated report changes.
- Added `docs/simulated_slippage_cost_assumption_design.md` to define a
  documentation-only boundary for future fixed-bps slippage, transaction cost,
  zero-slippage diagnostics, and deferred market-impact assumptions before any
  backtester implementation changes.
- Added `docs/post_local_csv_fixture_audit_rehearsal_checkpoint.md` to record
  the post-PR #83 local CSV readiness gate state and recommend a
  documentation-only simulated slippage and cost assumption design before any
  cost/slippage implementation.
- Added `docs/local_csv_fixture_readiness_audit_rehearsal.md` to fill the
  local CSV readiness audit report format with committed synthetic fixture
  evidence only, preserving the no-user-data and no-profitability boundary.
- Added `docs/post_local_csv_readiness_gates_checkpoint.md` to record the
  post-readiness-gates local CSV state, remaining stop conditions, and the
  boundary between prepared audit artifacts and any future user-provided local
  CSV smoke run.
- Added `docs/local_csv_readiness_audit_report_template.md` as a
  documentation-only manual audit report format for future user-provided local
  CSV studies, recording evidence, high/medium/low issues, stop conditions,
  and gate decisions before interpretation.
- Added a committed synthetic-fixture inventory dry-run rehearsal to the local
  CSV fixture workflow, recording redacted inventory review summaries before
  loader output is interpreted and keeping the workflow free of real user
  files, downloads, credentials, trading behavior, and profitability claims.
- Added a local CSV inventory dry-run validator that checks declared local
  file metadata before loading user files, keeps raw local paths out of review
  results, and remains free of data fetching, vendor APIs, credentials,
  trading behavior, report generation, and profitability interpretation.
- Added `docs/local_csv_study_checklist.md` as a documentation-only pre-run
  checklist for future user-provided local CSV studies before any user file is
  loaded, diagnosed, reported, or interpreted.
- Added `docs/user_provided_local_csv_research_plan.md` to define a
  documentation-only plan, scope template, validation gates, stop conditions,
  and future PR-sized stages before any user-provided local CSV result is
  interpreted.
- Added `docs/local_csv_readiness_checkpoint.md` to record the post-fixture
  local CSV readiness state, current gaps, guardrails, stop conditions, and
  the next documentation-only user-provided local CSV planning stage.
- Added a synthetic local CSV fixture universe-masked signal smoke check that
  applies the reviewed liquidity universe mask to the existing `alpha_009`
  fixture signal panel, records masked-signal audit counts, and keeps the
  workflow free of backtesting, ranking, target weights, real data, trading
  behavior, or performance interpretation.
- Added a synthetic masked-signal backtest smoke test that feeds
  universe-masked signals into the existing long-only backtester and verifies
  lagged holdings, signal coverage, and transaction-cost accounting without
  changing backtester behavior, generating reports, using real data, or
  interpreting performance.
- Added a synthetic masked-signal smoke test that composes liquidity
  eligibility, liquidity universe construction, and universe-mask signal
  application on deterministic synthetic panels without running a backtest,
  generating reports, using real data, or interpreting performance.
- Added a synthetic/local-panel universe-masked signal adapter that applies an
  already-constructed boolean liquidity universe mask to an already-computed
  factor signal panel with strict alignment, missing-mask rejection, and
  deterministic audit counts, without backtest integration, report generation,
  real data, trading behavior, or performance interpretation.
- Added `docs/liquidity_universe_backtest_integration_design.md` to define a
  documentation-only contract for future signal masking and simulated
  backtest consumption of liquidity universe masks before any source code
  changes.
- Added a synthetic liquidity universe-mask count smoke check to the local CSV
  fixture workflow demo, reusing the committed synthetic OHLCV fixture and
  existing liquidity universe helper without backtest integration,
  tradeability claims, real data, or performance interpretation.
- Added a synthetic/local-panel liquidity universe helper that returns an
  inspectable mask and audit summary without backtesting, report generation,
  real data, or performance interpretation.
- Added `docs/liquidity_universe_construction_design.md` to define a
  documentation-only future liquidity universe-mask API and audit-summary
  boundary before any backtest consumes liquidity eligibility.
- Added `docs/post_alpha012_checkpoint_report.md` to refresh the roadmap after
  Alpha#012 implementation, synthetic OHLCV smoke coverage, and local-fixture
  diagnostics.
- Added Alpha#012 diagnostics to the synthetic local CSV fixture workflow,
  reusing existing IC, Rank IC, and quantile-spread helpers on committed
  fixture data only.
- Added a synthetic OHLCV fixture smoke check that loads the committed local
  fixture and computes `alpha_012` as a feature-only output without reports,
  backtesting, real data, or performance interpretation.
- Added `alpha_012` as a single volume + close WorldQuant-style research
  feature with deterministic formula, alignment, missing-value, zero-volume,
  negative-volume, and no-lookahead tests.
- Added `docs/volume_close_alpha_plan.md` as a documentation-only planning
  gate before any volume + close WorldQuant-style alpha implementation.
- Added a realized volatility research feature that computes trailing standard
  deviation of one-period adjusted-price returns with deterministic
  no-lookahead, full-window, missing-anchor, non-positive-anchor, and
  input-validation tests.
- Added a short-term reversal research feature that computes negative trailing
  returns from adjusted-close panels with deterministic date-alignment,
  missing-anchor, non-positive-anchor, and input-validation tests.
- Added `docs/post_liquidity_checkpoint_report.md` to refresh the roadmap
  after the OHLCV and liquidity eligibility stages and recommend the next
  short-term reversal stage from current evidence.
- Added a synthetic liquidity eligibility count smoke check to the local CSV
  fixture workflow demo, using the committed OHLCV fixture to report lagged ADV
  and dollar-volume eligibility counts without constructing a universe or
  interpreting performance.
- Added synthetic-only liquidity eligibility helpers for rolling average daily
  volume and rolling average dollar volume, with explicit lag, warm-up,
  missing-value, and zero-volume tests.
- Added `docs/liquidity_dollar_volume_universe_plan.md` as a
  documentation-only planning gate for future synthetic liquidity and
  dollar-volume universe eligibility work before any code filters assets by
  volume.
- Added synthetic OHLCV local CSV loader smoke coverage for the committed
  fixture, including summary metadata, strict missing-value policy, and invalid
  OHLC relationship checks without computing a strategy.
- Added a strict local OHLCV long-format CSV loader with committed synthetic
  fixture coverage for raw-string validation, missing-value sentinels,
  duplicate `(date, symbol)` rows, positive OHLC prices, non-negative volume,
  optional `adjusted_close`, and impossible OHLC relationships.
- Added `docs/volume_ohlcv_schema_plan.md` as a documentation-only planning
  gate for future local volume and OHLCV CSV schema support before any
  volume-dependent factor or OHLC-dependent alpha implementation.
- Added split metadata to the synthetic local CSV fixture workflow, including
  train/validation/test coverage, per-split IC / Rank IC / quantile-spread
  diagnostics, and caveated report/log output.
- Added a synthetic split-aware IC / Rank IC diagnostic demo that applies the
  train/validation/test split helper to deterministic synthetic factor and
  forward-return panels without real data, backtesting, or performance claims.
- Added an official root `LICENSE` file for Apache-2.0 public reuse terms.
- Added `CITATION.cff` with repository citation metadata inferred from
  existing GitHub and git author metadata.
- Added `docs/assets/social_preview.svg` as an original source asset for a
  future GitHub social-preview upload.
- Added deterministic train/validation/test date-split helpers for synthetic
  factor research panels, with tests covering chronological boundaries,
  non-overlap, panel slicing, missing-value preservation, and invalid inputs.
- Added `docs/current_roadmap_gap_refresh.md` to reconcile the original gap
  analysis with the current implemented IC / Rank IC, quantile spread, local
  CSV fixture, and LEAN signal-only milestones.
- Added a pure-Python LEAN signal-only momentum draft plus static guardrail
  tests, keeping the draft non-runnable and free of data access, credentials,
  brokerage/order behavior, and profitability claims.
- Added a GitHub Actions `CI` workflow for pull requests to `main` and pushes
  to `main`, running the same pytest and compile checks used locally.
- Added an original `docs/assets/research_workflow.svg` diagram for the public
  README landing page.
- Added `docs/lean_signal_only_draft_design.md` to define a documentation-only
  boundary for a future pure-Python LEAN signal-only draft before any runnable
  LEAN code, data access, credentials, brokerage/order behavior, or performance
  interpretation is introduced.
- Added `docs/lean_runnable_draft_readiness_decision.md` to record that the
  project is not yet ready for a runnable LEAN draft under the current
  guardrails and should next design a signal-only draft boundary.
- Added `docs/lean_scaffold_review_checklist.md` to define review questions,
  static checks, safe expansion criteria, and stop conditions before any future
  runnable LEAN draft.
- Added a minimal non-executing LEAN smoke-test scaffold with static guardrail
  tests, without adding a runnable LEAN project, external data access,
  credentials, live or paper trading, brokerage integration, order execution,
  or profitability claims.
- Added `docs/lean_implementation_planning_checkpoint.md` to choose the exact
  future first LEAN code-PR boundary, validation strategy, review gates, and
  stop conditions before adding any LEAN scaffold or algorithm code.
- Added `docs/lean_smoke_test_design.md` to turn the LEAN parity checklist into
  a documentation-only smoke-test design before any LEAN implementation or
  project scaffold.
- Added `docs/lean_parity_checklist.md` to map local factor, diagnostics,
  benchmark, fee, slippage, and experiment-log requirements to future
  QuantConnect/LEAN smoke-test assertions before any LEAN algorithm code.
- Added a local CSV fixture workflow demo that loads committed synthetic CSV
  fixtures, computes `alpha_009` as a research feature, runs IC / Rank IC /
  quantile spread diagnostics, and writes caveated synthetic report/log
  artifacts.
- Added `docs/codex_long_running_controller.md` to define startup checks,
  merge gates, stage selection, stop conditions, logging requirements, and PR
  pause behavior for long-running Codex workflow.
- Added `docs/decision_log.md` for durable workflow, architecture, and
  research-process decisions.
- Added `docs/troubleshooting_log.md` for failures, missing prerequisites,
  correction attempts, verification, caveats, and prevention notes.
- Added `scripts/audit-skills.ps1` for local structural audits of repository
  Skill files.

### Changed

- Refreshed `docs/current_roadmap_gap_refresh.md` after the completed split,
  liquidity, fixed-bps slippage, volume-aware diagnostic,
  precomputed-impact, generated-log, and checkpoint stages, and routed the
  next safe stage toward a documentation-only synthetic robustness and
  split-aware validation plan.
- Refreshed the synthetic momentum and synthetic combined-score JSON
  experiment logs so their deterministic metrics payloads include the default
  `total_volume_aware_slippage_cost_impact` field after the precomputed
  volume-aware slippage backtester path, with the value remaining `0.0` in
  diagnostic-only mode.
- Updated the liquidity universe plan and decision log to separate liquidity
  eligibility, universe-mask construction, and backtest consumption into
  distinct reviewed stages.
- Refreshed the QuantConnect/LEAN plan and parity checklist for Alpha#012
  signal mapping, keeping the LEAN path documentation-only, non-runnable, and
  free of data subscriptions, credentials, brokerage/order behavior, and
  performance interpretation.
- Updated the Alpha#012 and WorldQuant roadmap docs to mark the completed
  Alpha#012 fixture diagnostics stage and recommend a LEAN plan refresh before
  any Alpha#012 LEAN mapping work.
- Updated the OHLCV schema plan and WorldQuant alpha catalog to route future
  volume-based universe work through the liquidity and dollar-volume planning
  gate before implementation.
- Updated the CSV interface plan and WorldQuant alpha catalog to reference the
  volume/OHLCV schema planning gate before future volume or OHLC-dependent
  implementation work.
- Updated the README license badge and current-status language to link to the
  Apache-2.0 license and remove obsolete license follow-up wording.
- Replaced the static README local-test status label with a live GitHub Actions
  CI badge for `.github/workflows/ci.yml`.
- Polished `README.md` as a public GitHub landing page with truthful status
  labels, beginner Quick Start commands, demo walkthrough links, a project map,
  key report links, and explicit no-live-trading scope language.
- Refreshed `docs/quantconnect_lean_plan.md` to reflect the current local CSV
  loader, synthetic local CSV workflow, IC / Rank IC diagnostics, quantile
  spread diagnostics, and experiment-registry state before any LEAN code.
- Refreshed `docs/worldquant_alpha_catalog.md` to distinguish current
  `alpha_009` research-feature status from the original catalog-only milestone
  and to restate data prerequisites for future WorldQuant-style alpha stages.
- Updated the long-running controller and staged workflow Skill with bounded
  execution behavior, low-risk ambiguity handling, missing-file recovery rules,
  and expanded stop conditions.
- Updated `.agents/skills/staged-quant-workflow/SKILL.md` to reference the
  long-running controller and Skill audit script.
