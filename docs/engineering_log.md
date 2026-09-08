# Engineering Log

## 2026-09-08 - Restore eligible-row C10b batch-path guard

- Checkpoint 001 removed `assert rank_indexes and corr_indexes` from
  `test_mixed_rows_rank_only_eligible_dates`. That was not formatting: it
  let a wholesale row-loop rollback pass the remaining subset check. The
  assertion is restored unchanged from
  `runs/red_b1_eligible_rank/input_source_1.py`
  (`065354ffa35382045b597ae4deea0d1195c60610b7420a30adcb4191cad02046`).
  Baseline is expected to fail this mechanism control while still passing
  numerical/public-contract checks. No runtime algorithm change. Prior
  checkpoint source/report/manifest remain frozen.

## 2026-09-08 - B2 eligibility-local Rank IC repair of C10b tiny-fixture overhead

- Bounded FIX-B2 repair keeps C10b pair-mask then average-rank Spearman
  batching. After public validation, Spearman now ranks and correlates only
  rows that already meet the existing `min_periods` pair-count gate. All-ineligible
  panels return a NaN series without `DataFrame.rank` or `corrwith`. Pearson,
  public error ordering, axes/dtypes/names and NaN masks are unchanged. No
  public switch, size threshold, dependency or Pearson rewrite is introduced.
- New deterministic tests in `tests/test_ablation_c10b_eligible_rank.py` cover
  all-ineligible and empty-valid-pair rows, mixed eligibility, min_periods
  boundaries, tied/constant/missing data, reused Spearman goldens, and invalid
  inputs before batch work. Intended RED on frozen B1 is 6 failed / 30 passed
  (`red_b1_pythonpath`). Repair GREEN is 36 passed. Original diagnostics,
  IC golden and defensive checks remain passing.
- Isolated pytest root `repair_b2/isolated_qa` now proves
  `features.diagnostics.__file__` and loaded SHA-256 at session start, after
  collection, and in the session fixture. Earlier absolute-path runs against
  `work/tests` are retained as source-binding failures. Bound RED is frozen B1
  6 failed / 30 passed; bound GREEN is this repair 36 passed; bound baseline
  36 passed without `DataFrame.rank` on ineligible rows.
- Focused seven-triple samples and the interrupted 18-case matrix are retained
  as recorded, not quiet-window acceptance. A live host sample showed unrelated
  GUI load; fixture wall variance does not establish that the tiny regression
  is fixed. New benchmark/resource batches are held for a renewed coordinator
  QA_WINDOW_CLEAR. Conditional acceptance of any residual fixture cost belongs
  to the coordinator under owner instruction, not this producer.

## 2026-09-07 - Seven accepted ablation components applied as one B1 candidate

- The accepted ordered implementation changes six runtime files: registry
  traversal in `ledger/schema_registry.py`; public-preserving empty-axis/column
  snapshots in `backtest/portfolio.py`; validated episode-array access in
  `backtest/metrics.py`; per-execution return preparation and owned anchor
  indexes in `campaign/runner.py`; eligible-only label gathering in
  `features/validation.py`; and batched Rank IC with the original Pearson path
  in `features/diagnostics.py`. No authority, calendar, cost, missingness,
  provenance, canonicalization or frozen-byte policy is changed.
- The producer retained baseline, single-direction and composed checkpoints in
  the separate task's `evidence/phase_b1`. Stage checks pass: 1437 for C02;
  416 plus two unchanged platform skips for separate/composed backtest changes;
  233 for separate/composed campaign changes; and 486 for separate/composed
  feature changes. The original fresh baseline has 2573 passes and two skips.
- The added 149 deterministic regressions use committed synthetic baseline
  oracles and cover public empty axes/digests, mixed scalars, source/catalog
  mutation, canonical split and JSON checks, direct-constructor cache ownership,
  per-execution preparation and exact Pearson/numerically bounded Rank IC.
  All nine rejected controls are detected in isolated copies. Historical A1/A2
  artifacts and every original test/fixture remain unchanged.
- Full raw campaign artifacts/attempt state, reopened ledger tables, backtest
  outputs and labels match baseline in the stage comparisons. Sparse Rank IC
  differs by at most 5.551115123125783e-17 in the stage replay; the accepted
  absolute bound remains 1e-12 only for Rank IC, with exact Pearson and masks.
  In the feature stage's checked scope, C10b changes 25 constant-input warnings
  to none; this warning-frequency difference is recorded explicitly.
- Whole-candidate verification and resource distributions are recorded in the
  separate ablation task's `reports/implementation_b1.md` and
  `evidence/phase_b1`, with an exact candidate identity. This entry records the
  applied components and stage evidence; independent implementation verification,
  three fresh structural reviews and acceptance remain separate gates. No
  release readiness, publication or whole-round completion is asserted.

## 2026-09-07 - Accepted whole-project ablation B1 implementation start

- Coordinator decision accepts plan SHA-256
  15730920f183af8669f760cd606266626a2469bc6cbf60129da16fa41b99c663
  with the bound authority-attribution clarification. The coordinator, not the
  owner, issued A2's measurement-window clearance; that operational clearance
  was not an owner policy waiver. Historical reports remain unchanged.
- The accepted P1 completion-calibration and P2 public-boundary patches are now
  applied in this clean baseline-derived implementation candidate. Public C04
  remains withdrawn; independent feasibility resolved the counterexample for
  C04b only. Implementation acceptance remains a separate gate.
- Review-process lesson: report actual completed inspection and implementation
  scope. Native metadata queries, source-plan assertions, file names and partial
  reads do not establish full-source review, independent verification or scope
  completion. Record completed commands, read depth, preserved failures and
  remaining limits separately from intended work. Do not rewrite the deferred
  unrelated mainline advisory A2-GPT-001 or historical review records.
- B1 executes the accepted ordered components as one candidate, retaining
  baseline, single-direction and composed evidence under the separate ablation
  task's evidence/phase_b1. This start entry records governance/test preparation;
  subsequent implemented facts and measurements are recorded when completed.


## 2026-09-07 - P2 public provenance empty-axis ablation counterexample

- Independent QA-A-C04-EMPTY showed that the proposed C04 column iterator
  discarded empty row tuples for accepted Nx0 public provenance capture,
  changing original cells and state digest. The ordinary regression and
  mixed-scalar corpus missed the boundary; no financial corruption was shown.
- The sealed A1 artifacts and all passing/negative results remain immutable.
  C04 is withdrawn. A fresh baseline-derived C04b preserves the empty row
  tuples, with new public-boundary regression and paired feasibility evidence
  saved under evidence/phase_a2 in the separate ablation task root.
- The new regression passes baseline and C04b and fails C04. The public shape,
  scalar and mutation corpus compares original/current digests for both roles.
  The durable rule now requires testing upstream accepted shapes independently
  of downstream validation. A2 producer evidence is not independent acceptance
  or completion of implementation; correction replay and structural plan gates
  still apply. This entry is prepared externally for accepted implementation.


## 2026-09-07 - P1 whole-project ablation scope and completion correction

- The owner identified a P1 process failure: the prior pass inventoried the
  whole project but experimentally tested only five local hypotheses and
  retained seven net source-line removals. That local result did not fulfill
  the requested comprehensive code/design/efficiency/defensive-implementation
  ablation. Local QA or review success did not establish scope completion.
- The corrective second round investigates every runtime/subsystem boundary,
  ranks major alternatives, profiles synthetic end-to-end paths, and preserves
  isolated single-variable experiments, baseline results and negative evidence.
  A durable completion-claim calibration rule is recorded in AGENTS.md.
- Phase A records investigation and the binding implementation plan. Its
  PHASE_A_READY checkpoint pauses producer writes for independent plan QA and
  three-model acceptance. It does not record completion of the requested
  round; accepted implementation/ablation waves remain to follow.
- This entry and the rule were prepared as an external candidate patch during
  Phase A. Applying this patch belongs to the accepted implementation wave;
  no unrelated governance edits or original-checkout files were overwritten.

## 2026-09-07 - Common-sample fixture binary64 portability

- Ubuntu Python 3.11 CI on `4d4a0f58f5d28063d0e97f10b9a38fe357fd16b1` failed four
  exact `==` assertions: left-to-right `sum` of `0.01 + 0.0001 * i` over 60
  months is `0.012949999999999998`, while JSON `0.01295` is a different binary64.
  Local macOS Python 3.12 passed because builtin `sum` uses compensated addition.
- Fixture inputs/expected means were replaced with finite binary64 dyadics so
  naive and compensated sums match JSON. Opposite-sign common-positive versus
  all-valid-negative classification coverage is preserved. Production mean and
  classifier code were not changed.
- A first full local suite failed the existing numeric-literal conformance
  test on a `0.0` left-to-right sum seed. The helper now starts from the first
  value. That conformance test was not weakened.
- No 14-trial, D8, identity reopen, GitHub review, or real data.

## 2026-09-07 - Isolated A1 empirical code ablations

- The 439-file input snapshot was copied and hash-verified before seven
  independent, single-hypothesis ablations. Source changes were selected after
  executable comparisons using synthetic inputs and isolated HOME/TMPDIR paths.
- Retained three local simplifications: compact the identical registry profile
  initialization while retaining its explicit ten-version allowlist; return
  Alpha#012 arithmetic directly because its final missing-value mask is redundant;
  consume the existing immutable producer caveat tuple in the report registry.
  These remove 89 production-source lines in total.
- Per-ablation checks passed: 1427 ledger tests and 209 exact behavior observations;
  47 alpha/fixture/alignment tests and 251 exact observations; 10 reporting tests
  and 31 exact observations. Eight added boundary cases pass on the original
  baseline and the retained alpha variant.
- Rejected the rolling.rank substitution (first/dense and sparse-window behavior),
  cache deepcopy removal (nested mutation pollution in all ten versions), and
  Alpha#009 operator bypass (finite-input arithmetic overflow stopped raising).
  Existing tests alone missed the ranking and overflow regressions; the added
  tests kill both variants. The PIT CLI simplification remains unapplied because
  its changed package digest conflicts with the published artifact binding.
- The external EFR-ABLATION-A1 report retains all variant hashes, failed attempts,
  commands, outputs, combined-candidate QA, and coverage limits. This entry records
  local simplifications and the rejected hypotheses.

## 2026-09-06 - Public-safe Track B Path A/B first-checkpoint status

- Protected main at authoring:
  `425b7c88a6e049b63aa2ddeae8560fea08fda23e` after PR #199 Path A first
  checkpoint and PR #200 Path B first checkpoint. No open pull request at
  the verified start of this work.
- Public handoff, roadmap, and decision log now record those merged first
  checkpoints. Docs no longer say Track B runtime is undelivered.
- Evidence ceiling remains `DIAGNOSTIC_ONLY`. 14-trial remains REFUSED,
  reason `ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`. Terminal
  refusal is disposition, not Stage 4 / PR 4 completion.
- D8, A2, identity reopen, result/performance access stay closed. Optional
  37-event completion and factor-zoo stay off the critical path.
- No private paths, tickers, prices, or performance values.

## 2026-09-06 - Track B v7 Path B PR 200 extra MATERIAL remediations

- PR #200 head `bf149827e8ff5d85f4de18883212ac7dcc1b6ef4` still admitted
  noncanonical plan stream-member timestamps as sole-current, coerced
  Boolean `True` to integer `1` on relation ordinals and plan-tuple
  versions, and treated garbage `valid_until` as current for readiness,
  plan acceptance, and allocation/start authority.
- Runtime remediations only. Canonical UTC parse now covers every
  `_require_current` kind and stream member. Relation and plan-tuple
  integers use type-strict JSON equality. Producer helper members must
  match `act_<32 lowercase hex>`. Killing tests refuse the listed
  counterexamples with unchanged seal or allocated state and no EXECUTE
  capability on start refusals.
- No 14-trial, D8, identity reopen, GitHub review, or real data.

## 2026-09-05 - Track B v7 Path B PR 200 P1-FIX3 remediations

- PR #200 head `81239b4c75cd968109d1cc5d74a026f06498ebd0` remaining P1s:
  plan `private_input_producer_actor_ids` still coerced missing/null to `[]`;
  plan validity timestamps compared lexically; plan omitted retained
  trial/seal/relation; allocation authority compared only plan id/hash;
  readiness omitted `ledger_id`.
- Runtime remediations only. Killing tests prove unchanged sealed or
  allocated state for omitted/null/malformed plan producers, offset and
  `not-a-timestamp` plan validity, isolated trial/seal/relation mismatches,
  complete allocation-authority plan-tuple mismatches, and
  missing/null/wrong readiness ledger_id with no EXECUTE capability.
- No 14-trial, D8, identity reopen, or real data.

## 2026-09-05 - Track B v7 Path B PR 200 P1-FIX2 remediations

- PR #200 head `24e0001ca25d168133d1bdb9a56345b68639701b` had remaining P1s:
  plan acceptance omitted plan tuple version/schema/canonicalization and
  relation; readiness coerced missing/null producer IDs to `[]`; EXECUTE
  consume compared timestamps lexically; plan currentness was not checked
  at allocation or start; plan/authorities did not bind ledger and start
  authority omitted readiness version.
- Runtime remediations only. Isolated mismatch tests roll back allocation.
  Producer missing/null/malformed/collision tests, canonical-UTC consume
  refusals, revoked/stale plan at allocation and after allocation, and
  ledger/readiness-tuple binding tests are included.
- No 14-trial, D8, identity reopen, or real data.

## 2026-09-05 - Track B v7 Path B PR 200 P1 remediations

- PR #200 head `ac25ca0001d643d991eed09729ed26719215ad98` had four P1s:
  plan acceptance did not bind plan/attempt/trial/seal/scope;
  ATTEMPT_STARTED skipped readiness role independence and missing roles;
  start-authority did not bind operation ATTEMPT_STARTED;
  EXECUTE consume ignored activation/expiry.
- Runtime remediations only. Killing tests cover wrong-subject acceptance
  with unchanged state, issuer/reviewer=executor and missing role fields,
  wrong/missing start operation with no event or capability, and consume
  before activation, at expiry, and after expiry leaving the capability
  unconsumed.
- No 14-trial, D8, identity reopen, or real data.

## 2026-09-05 - Track B v7 Path B first checkpoint

- Implemented the accepted Track B v7 Path B runtime in this worktree on
  base `e4f2545fc17cf15a6541d690d7d61ae6e302b356`, branch
  `codex/track-b-runtime-path-b`. Extends the existing stdlib sqlite3 Path A
  runtime. Caller-supplied database path outside the canonical repository.
  Synthetic catalogs only. No extra DB package.
- Path B happy path: Path A inventory/seal prerequisites, then first
  ATTEMPT_ALLOCATED and valid ATTEMPT_STARTED. EXECUTE capability is minted
  with start and consumed by the readiness executor. Retry relation and
  terminal attempt events are refused. Path B does not append
  ACCESS_COMPLETED or EXPOSURE_DECISION. Evidence ceiling remains
  DIAGNOSTIC_ONLY.
- Deterministic tests cover the Path B happy path and frozen Path B
  refusals, including unselected `WIRE_TYPE_NOT_SELECTED`, retry,
  ATTEMPT_ALLOCATED seal/trial/family/private-producer refusals, inherited
  tuple and operational-value mismatches, start/plan/allocation-authority
  currentness, executor mismatch, and EXECUTE consumer mismatch.
- No 14-trial run, D8, identity reopen, real/private market data, brokerage,
  or vendor API.

## 2026-09-05 - Track B v7 Path A exact-head P1-FIX2 remediations

- PR #199 head `86a7ca5331b6b2d174cbfe72f9c295ba3ec54cde` still had live
  catalog/authority P1s plus new identity, code, approval, resolver-tuple,
  seal-authority, and ACCESS capability-bound findings. Runtime remediations:
  catalog `get` recomputes body digest; trial definition binds experiment
  and complete `code_identity`; publication approval binds sample/projection;
  allocation authority binds operation/campaign/trial/definition; seal
  revalidates allocation authority; resolvers compare schema/owner/
  canonicalization; ACCESS capabilities carry activation/expiry.
- Killing tests cover each listed P1. No 14-trial, D8, identity reopen, or
  real data.

## 2026-09-05 - Track B v7 Path A exact-head P1 remediations

- PR #199 head `d6e1f58dea03d5edcef8203d8e1de41a5f27137e` had eight P1s and
  one P2 from exact-head Codex review. Runtime remediations only: catalog
  `get` refuses body/digest mismatch; each append snapshots the synthetic
  catalog under the writer lock through commit; SAMPLE_REGISTERED requires
  current content-bound projection; ACCESS intent authority binds operation,
  sample, and campaign; ACCESS_STARTED start-authority accessor must equal
  the capability accessor; trial allocation resolves the public projection
  tuple; trial definition binds requested `trial_family_id`; sample resolver
  compares the eight-field authority key and does not overwrite catalog
  metadata. Exact replay now returns `event_sha256`.
- Killing tests cover each P1. No 14-trial, D8, identity, real data, or
  Path B expansion.

## 2026-09-05 - Track B v7 Path A first checkpoint

- Implemented the accepted Track B v7 Path A runtime in this worktree on
  base `6a95d250b04907a4fa4296a480e08c96d4b7c183`, branch
  `codex/track-b-runtime-path-a`. Stdlib sqlite3 only. Caller-supplied
  database path outside the canonical repository. Synthetic catalogs only.
- Registry `0.10.0` promotes ACCESS_INTENT, ACCESS_STARTED, and
  ACCESS_COMPLETED payload schemas using the existing closed DSL. Releases
  `0.1.0` through `0.9.0` remain byte-immutable. Default R0 entry point is
  unchanged.
- Path A happy path: LEDGER_EPOCH_CREATED through local SAMPLE_REGISTERED,
  TRIAL_ALLOCATED, CAMPAIGN_INVENTORY_SEALED, ACCESS_INTENT, then
  ACCESS_STARTED. ACCESS_STARTED consumes the ACCESS capability in the
  same transaction. Path A stops before ACCESS_COMPLETED and does not
  append EXPOSURE_DECISION. Evidence ceiling remains DIAGNOSTIC_ONLY.
- Deterministic tests cover the Path A happy path and frozen Path A
  refusals, including unselected `WIRE_TYPE_NOT_SELECTED`, ingress commit
  fields, empty affected trials and evidence refs, ACCESS role collisions,
  seal role/parent-staleness refusals, and injected ACCESS consume rollback.
- No 14-trial run, D8, identity reopen, real/private market data, brokerage,
  or vendor API.

## 2026-09-05 - Track B v7 design P2-FIX5 exact-head remediations

- PR #198 head `c332ef02945efaa52e5b10f8c79c21da45e7353c` had two remaining
  P2s. `T-B-ACCESS-ROLE-COLLISION` isolates each prohibited equality among
  the five ACCESS_INTENT principals. `T-B-START-READY-FAM-SET` adds missing
  and extra family variants mapped to
  `ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH`.
- Unchanged: `evidence_ref_ids` `1..4096`, `T-B-SEAL-REVIEWER-TRIAL-ISSUER`,
  and the `operation_request_sha256` ingress variant. No SQLite runtime or
  14-trial run.

## 2026-09-05 - Track B v7 design P2-FIX4 exact-head remediation

- PR #198 head `b3bc1df8b05495ad29c441e58ce068b4fd45fee0` had one remaining
  P2: `T-B-INGRESS-COMMIT-FIELDS` now includes independent variant
  `operation_request_sha256`, refusing
  `OPERATION_REQUEST_COMMIT_FIELD_FORBIDDEN`.
- Evidence_ref_ids remains `1..4096`. `T-B-SEAL-REVIEWER-TRIAL-ISSUER`
  is unchanged. The 14-wire budget is unchanged. No SQLite runtime or
  14-trial run.

## 2026-09-05 - Track B v7 design P1-FIX3 exact-head remediations

- PR #198 head `e1c2953ac951b64f8fa4580e653ea42530695398` had one P1 and
  two P2s from exact-head Codex review. Design-only remediations:
  `evidence_ref_ids` is `1..4096` on ACCESS_INTENT, ACCESS_STARTED and
  ACCESS_COMPLETED, with empty-array refusals
  `{EVENT}_EVIDENCE_REF_SET_EMPTY`. External-reference readiness origin is
  `STAGE3_SAMPLE_REFERENCE_BOUND`. Isolated seal case
  `T-B-SEAL-REVIEWER-TRIAL-ISSUER` requires
  `CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION` when the inventory reviewer
  equals an included trial-definition issuer.
- The 14-wire budget is unchanged. No SQLite runtime, 14-trial run, D8,
  identity, or result access.

## 2026-09-05 - Track B v7 design P1-FIX2 exact-head remediations

- PR #198 head `ca4153880e31d79b2c6141f95c6c8fd7dbb007fe` had two P1s and
  two P2s from exact-head Codex review. Design-only remediations:
  ACCESS_INTENT and ACCESS_STARTED now bind typed `evidence_ref_ids`;
  ACCESS_COMPLETED, when later enabled, requires
  `ACCESS_STARTED.recorded_at <= started_at <= ended_at` and has killing
  test `T-B-ACCESS-COMPLETED-BEFORE-START`. Path A still stops after
  ACCESS_STARTED. Readiness retained-source set lists campaign binding and
  attempt allocation, with an external-reference specimen. Readiness entry
  IDs are owner-native `trial_family_id`/`sample_id`/`trial_id`.
- The 14-wire budget is unchanged. No SQLite runtime, 14-trial run, D8,
  identity, or result access.

## 2026-09-05 - Track B v7 design P1 exact-head remediations

- PR #198 head `1cc68fbec1241e70161b24b371648670b523f672` had two P1s and
  two P2s from exact-head Codex review. Design-only remediations: Path A
  first checkpoint now stops after ACCESS_STARTED and does not claim
  terminal ACCESS_COMPLETED, because EXPOSURE_DECISION is not selected;
  the 14-wire budget is unchanged. ACCESS_INTENT requires a nonempty
  sealed affected-trial set and refuses empty set as
  `ACCESS_INTENT_AFFECTED_TRIAL_SET_EMPTY`. The three previously empty
  finding-coverage lists now carry the complete 68-test union. Public
  design Markdown/JSON hashes are committed in
  `docs/experiment_trial_ledger_track_b_v7_design.artifacts.sha256`.
- No SQLite runtime, 14-trial run, D8, identity, or result access.

## 2026-09-04 - Live hosted-review check before merge

- Owner correction: do not claim Codex (or any provider) is quota-limited
  without a live probe in the same turn, and do not stop at the apology.
- Incident: PR #194 had an explicit Codex usage-limit reply on 2026-09-02.
  PR #195 was merged at 2026-09-04T03:23:16Z by treating that older message
  as current. Codex posted a clean exact-head review on `ca3fce465c` at
  2026-09-04T03:23:59Z. No new P1s. The merge process was wrong; the review
  was not missing for lack of quota.
- Continuation invariant is in `AGENTS.md`. Same-turn live probe, merge wait,
  and fallback rules are in `docs/codex_long_running_controller.md`.

## 2026-09-04 - Public-safe 14-trial identity fail-closed stop

- Updated `docs/current_handoff.md` and `docs/current_roadmap.md` so a
  GitHub clone sees the 14-trial run REFUSED, named reason
  `ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, and evidence
  ceiling `DIAGNOSTIC_ONLY`.
- Refreshed `docs/track_a_pr2_public_status.md` and
  `docs/track_a_pr2_public_status_v1.json` with owner-stop SHA
  `163b8f31d3568e460c074592c00376cf86d4f09371a6bb6a40f8d6cdd4548f5a`,
  freeze-record SHA
  `c160a3b21f359dc96eda7f1f018e3315bae79f505078ca5199ed87a8204f0ccd`,
  and protected main after PR #194
  `24bc794d0a6cbd6502a8db088008fa74acbe8752`.
- Recorded that D8, A2, and identity reopen stay closed, no performance
  values are published, and the 14-trial run did not execute.
- No runner, validator, private data, or result-bearing behavior changed.

## 2026-09-02 - Shrink campaign runner synthetic 14-trial panels

- Execution P1 campaign runner tests now use shorter synthetic calendars
  and merge shared 14-trial panel runs for scheduled costs, unscheduled
  listing dates, and Rank IC eligibility.
- `test_rank_ic_omits_ineligible_listings` compares mixed-eligible Rank IC
  cross-sections to the eligible-only panel so ineligible names are omitted
  from IC pairs rather than asserted present in `forward_returns`.
- Timing, leakage, cost, and ledger assertions remain. Evidence ceiling
  remains `DIAGNOSTIC_ONLY`. No private control-tree write, B-8 bind, or
  real 14-trial run.

## 2026-08-30 - Track A PR 4 Rank IC, schedule, and coverage P1s

- Rank IC cross-sections use eligible listings only; ineligible names are
  omitted rather than appended as missing pairs. Months below the 100-name
  floor remain invalid.
- Unscheduled listing dates are skipped in Rank IC, episode, freeze,
  continuous resets, and held-return representatives. A schema-valid
  non-month-end date cannot overwrite scheduled lineage metadata or enter
  trial calculations.
- Coverage gates and required Rank IC and episode outputs use primary
  evaluation dates. Continuous resets use primary-era scheduled rows with
  `continuous_included`, including December signals whose labels end in
  January. Fold-purged December months are retained as invalid Rank IC
  records and counted in `invalid_and_missing_summary.json`, including when
  the December listings key is omitted. A scheduled primary-era
  cutoff-boundary month with an incomplete label is retained as
  `EVALUATION_FOLD_LABEL_PURGED` when its listings key is omitted.
  Continuous resets still use that
  scheduled January execution. An empty 2018+
  calendar returns no required Rank IC/episode rows rather than scoring
  warm-up as primary. Pre-2018 missing
  labels are warm-up only and do not fail coverage.
- Evidence ceiling remains `DIAGNOSTIC_ONLY`. No private control-tree
  write, B-8 bind, or real 14-trial run.

## 2026-08-30 - Track A PR 4 cutoff and 2018 fold P1s

- Accepted cutoff is the last session date, not the latest monthly signal.
- Primary evaluation folds start in 2018; earlier complete labels are warm-up
  only and do not enter required years. Evidence ceiling remains
  `DIAGNOSTIC_ONLY`.

## 2026-08-30 - Track A PR 4 execution P1 follow-up

- The durable attempt is reserved before result-bearing trial execution.
- Equal-weight benchmark holdings are stored per factor. Continuous
  resets use only `continuous_included` signals and charge cash-to-target
  deployment at the first execution.
- Held returns require exact start and end anchors. Invalid 25 bps
  strategy paths fail hard validity. Bootstrap segments split on fold and
  missing-month gaps. Robustness required years come from the schedule.
- Decile children carry executed means, spread, and monotonicity.
  Evidence ceiling remains `DIAGNOSTIC_ONLY`.

## 2026-08-30 - Track A PR 4 execution P1 remediation

- Diagnostic classifier inputs are assembled from executed monthly Rank
  ICs, coverage, bootstrap/Holm when complete-case months exist, and
  strategy-vs-baseline paths. Constant fail-closed payload flags are
  gone.
- Required bundle children carry executed JSON artifacts with explicit
  schemas rather than two-field placeholders.
- Forward returns and episode labels use execution close `e=t+1` through
  `e+21`. Continuous paths reset at every scheduled execution.
- Rank IC is one cross-section per signal month. Evidence ceiling remains
  `DIAGNOSTIC_ONLY`. No private control-tree write, B-8 bind, or real
  14-trial run.

## 2026-08-30 - Track A PR 4 execute from an input-bearing panel

- `run_campaign` admits only an input-bearing prepared campaign:
  `prices`, `anchors`, and `listings`. Result-bearing keys such as
  `trial_outputs`, `diagnostic_payload`, returns, factor, portfolio,
  cumulative, and `bundle_children` refuse
  `PREPARED_CAMPAIGN_SCHEMA_INVALID`.
- Authorized work executes all 14 inventory trials once through existing
  PR 3 eligibility, factor, return, baseline, path, and diagnostic
  entry points, then reconciles those executed outputs and assembles the
  bundle. Status is `EXECUTED_DIAGNOSTIC_ONLY` with `trials_executed`.
- `RESULT_ACCESS` and `PERFORMANCE_ACCESS` remain unexecutable. Evidence
  ceiling remains `DIAGNOSTIC_ONLY`. No D8, A2, identity reopen,
  performance-informed selection, private control-tree write, B-8 bind,
  or real 14-trial campaign run.

## 2026-08-30 - Track A PR 4 durable ledger, bundle preflight, digest recheck

- Attempt consumption lives under the user data directory, not
  `tempfile.gettempdir()`. A missing identity file refuses
  `CAMPAIGN_ATTEMPT_STATE_ABSENT`; deleting a tmp ledger or planting a
  fresh tmp file cannot replay.
- Bundle completeness is checked before consume. Missing required
  children refuse `BUNDLE_CHILD_MISSING`. Invalid assembly is a named
  refusal, not `RECONCILED_DIAGNOSTIC_ONLY`.
- Protocol and inventory bytes consumed after `authorize()` are
  rehashed against the bound digests. A file swap refuses
  `PROTOCOL_FREEZE_BYTES_MISMATCH` or `TRIAL_INVENTORY_BYTES_MISMATCH`
  without spending the attempt.
- Evidence ceiling remains `DIAGNOSTIC_ONLY`. No D8, A2, or 14-trial
  run.

## 2026-08-29 - Track A PR 4 owner binding, cross-process cap, reserved children

- The detached owner digest is authenticated against
  `owner_authorization_file_sha256` on the independently accepted
  acceptance record. Matching RunConfig, grant-block, and binding
  values is not enough; a joint grant-and-binding mutation is refused
  `GRANT_OWNER_AUTHORIZATION_DIGEST_MISMATCH`.
- Attempt consumption uses one durable store uniquely keyed by
  campaign identity. Caller-selected `attempt_state_file` locators and
  process-local sets are not the cap. A second process with a fresh
  caller ledger is refused `CAMPAIGN_ATTEMPT_ALREADY_CONSUMED`.
- Prepared `bundle_children` that collide with runner-owned names
  refuse `PREPARED_CAMPAIGN_CHILD_COLLISION` before the attempt is
  consumed. Runner-owned children are written after prepared children.
- Evidence ceiling remains `DIAGNOSTIC_ONLY`. No D8, A2, or 14-trial
  run.

## 2026-08-29 - Track A PR 4 attempt identity and ledger count

- Attempt consumption is keyed by `campaign_identity` of the trusted
  detached bound fields, not the caller-supplied grant FILE_BYTES.
  A metadata-mutated grant with a fresh ledger still refuses
  `CAMPAIGN_ATTEMPT_ALREADY_CONSUMED`.
- Negative or inconsistent ledger `execution_count` refuses
  `CAMPAIGN_ATTEMPT_STATE_INVALID` before mutation.
- Evidence ceiling remains `DIAGNOSTIC_ONLY`. No D8, A2, or 14-trial
  run.

## 2026-08-29 - Track A PR 4 exact-head P1 replay/ledger remediation

- The attempt ledger is keyed by the bound grant digest. A second
  fresh locator for the same grant refuses
  `CAMPAIGN_ATTEMPT_ALREADY_CONSUMED`. A ledger whose grant digest does
  not match refuses `CAMPAIGN_ATTEMPT_LEDGER_MISMATCH`.
- Nested prepared payloads are reconciled before the attempt is
  consumed, so a nested wrong-type document refuses
  `PREPARED_CAMPAIGN_SCHEMA_INVALID` without spending the one-run
  limit.
- Bundle `attempt_count` comes from the consumed ledger, not the
  prepared payload.
- Evidence ceiling remains `DIAGNOSTIC_ONLY`. No D8, A2, or 14-trial
  run.

## 2026-08-29 - Track A PR 4 exact-head P1 remediation

- Bound `owner_authorization_file_sha256` through RunConfig, the
  detached binding, and the grant block. A forged grant digest now
  refuses `GRANT_OWNER_AUTHORIZATION_DIGEST_MISMATCH`.
- `run_campaign` consumes a durable attempt-state file under an
  exclusive lock so a second authorized invocation refuses
  `CAMPAIGN_ATTEMPT_ALREADY_CONSUMED`.
- Prepared-payload work is labeled `RECONCILED_DIAGNOSTIC_ONLY` with
  `trials_reconciled`. It does not claim trial execution.
- Malformed prepared documents refuse `PREPARED_CAMPAIGN_UNPARSEABLE`
  or `PREPARED_CAMPAIGN_SCHEMA_INVALID`.
- Evidence ceiling remains `DIAGNOSTIC_ONLY`. No D8, A2, or 14-trial
  run.

## 2026-08-29 - Track A PR 4 diagnostic execution path

- Split grant eligibility so `FOURTEEN_TRIAL_RUN` may appear in
  `now_eligible` when the run-authorization block is valid.
- `RESULT_ACCESS` and `PERFORMANCE_ACCESS` in `now_eligible` still
  refuse `GRANT_NOW_ELIGIBLE_AUTHORIZES_FORBIDDEN_STAGE`.
- Explicit forbiddance of both access stages is required in
  `does_not_authorize`; it is not a disqualifier.
- Revised `result_bearing_refusal_reason` branch order. Deleted the
  unconditional `RESULT_BEARING_RUN_NOT_AUTHORIZED` terminal refusal.
- Superseded by later same-day entries: authorized prepared-payload
  work returns `RECONCILED_DIAGNOSTIC_ONLY`, not
  `EXECUTED_DIAGNOSTIC_ONLY`, and `run_campaign` writes the bound
  attempt-state ledger.
- Synthetic tests cover the exact grant-v2 lists, the Lock 2 truth
  table, grant v1 schema invalidity, run-block value refusals, sentinel
  and prepared-byte mismatch, and binding v2 exact-key checks.
- Evidence ceiling remains `DIAGNOSTIC_ONLY`. No D8, A2, identity
  reopen, performance-informed selection, or 14-trial run.

## 2026-08-25 - Public-safe Stage 4 G-2 status

- Updated `docs/current_handoff.md` and `docs/current_roadmap.md` so a
  GitHub clone sees Stage 4 G-2 accepted by hash, the 14-trial run not
  executed, and evidence ceiling `DIAGNOSTIC_ONLY`.
- Refreshed `docs/track_a_pr2_public_status.md` and
  `docs/track_a_pr2_public_status_v1.json` with G-2 acceptance-file,
  frozen-plan markdown, and EXEC-2 fileset hashes on protected main
  `11a9cb8849b5239faa1081eda046d2254a12febc`.
- Recorded that Stage 4 is not fully complete beyond G-2, formal
  interpretation remains not granted, and private control-tree bodies
  stay off GitHub.
- No runner, validator, private data, or result-bearing behavior changed.


## 2026-08-24 - Public docs sync for post-PR3 resume surface

- Updated `docs/current_handoff.md` and `docs/current_roadmap.md` so protected
  `main` no longer points readers at already-closed PR2 owner gates.
- Refreshed `docs/track_a_pr2_public_status.md` and
  `docs/track_a_pr2_public_status_v1.json` with campaign `DIAGNOSTIC_READY`
  acceptance hashes, materiality exact-SHA approval, PR #187 merge identity,
  and next stage `DETACHED_PRE_RUN_BINDING`.
- Recorded that formal interpretation remains not granted, evidence ceiling
  remains `DIAGNOSTIC_ONLY`, the 14-trial run has not executed, and private
  control-tree bodies are not on GitHub.
- No runner, validator, private data, or result-bearing behavior changed.


## 2026-08-23 - Track A PR 3 FIX-12 ledger cross-product equivalence

- Implemented exact-head Codex item from card `EFR-GRK-PR3-FIX-12` on
  `codex/track-a-pr3-fix4` at start HEAD
  `be8ce63da6d96e0f364f805b0e154a4700034f18`. F-1 and F-2 stayed out of
  scope under the recorded `REFUTE_AND_DEFER` disposition.
- `first_full_rest_smoke` still collapses later representatives to one
  smoke case, but only after every representative is proven to delegate
  to the same non-null constraint kind. Mixed kinds, unknown kinds, and
  empty axes fail closed before any collapsed pairs are returned.
- Ledger registry tests now prove field groups against the packaged
  schema path before collapsing Boolean, null, length, and case cases.
  Missing-field fixture groups prove shared requiredness. Fail-closed
  `INVALID_EVENT` behavior is unchanged.
- Existing campaign modules, including `inference.py` at `be2e743c…50a130`,
  were not edited. No private panel, performance value, or 14-trial run
  was accessed.
- Focused ledger tests passed 1267. Full suite after repo-map refresh:
  2412 passed, 2 existing platform-conditional skipped.

## 2026-08-23 - Track A PR 3 FIX-11 interior included decisions

- Implemented exact-head Codex item from card `EFR-GRK-PR3-FIX-11` on
  `codex/track-a-pr3-fix4` at start HEAD
  `4d19e20db9817300e7a37cf6765187016a68d6eb`. F-1 and F-2 stayed out of
  scope under the recorded `REFUTE_AND_DEFER` disposition.
- `factor_matched_cost_free_comparison` now requires the frozen signal
  set to contain every continuously included schedule row between its
  endpoints. Supplying January and March while February is continuously
  included is refused, even when the daily path is the exact
  execution-bounded span.
- Already-closed excluded-row, signal-close, complete-span,
  prefix/suffix, execution-close reset, sparse/duplicate/reversed
  calendar, mixed-factor, grant-planning, environment, Rank IC,
  frozen-child digest, Boolean real-vector, session-identity,
  complete-root, and per-trial status gates were left in place.
- Existing campaign modules, including `inference.py` at `be2e743c…50a130`,
  were not edited except `benchmarks.py`. No private panel, performance
  value, or 14-trial run was accessed.
- Focused campaign tests passed 164. Full suite after repo-map refresh:
  2404 passed, 2 existing platform-conditional skipped.

## 2026-08-23 - Track A PR 3 FIX-10 equal-length bypass and excluded rows

- Implemented exact-head Codex items from card `EFR-GRK-PR3-FIX-10` on
  `codex/track-a-pr3-fix4` at start HEAD
  `993e66d50bad2b177c0223aff70c3d52c72f28e1`. F-1 and F-2 stayed out of
  scope under the recorded `REFUTE_AND_DEFER` disposition.
- `factor_matched_cost_free_comparison` no longer treats an equal-length
  path as a calendar exemption. A one-point strategy dated at signal
  close must match the exact execution-bounded span and therefore is
  refused. Every nonempty frozen set is checked through
  `_validated_signal_row` and `_execution_bounded_span`.
- A frozen decision on a `continuous_included=False` schedule row is
  refused. The bounded endpoint may not exceed `accepted_cutoff`. The
  committed `session_month_cutoff.json` June-excluded July 1 through
  August 1 path cannot produce a valid comparison.
- Already-closed complete-span, prefix/suffix, execution-close reset,
  sparse/duplicate/reversed calendar, mixed-factor, grant-planning,
  environment, Rank IC, frozen-child digest, Boolean real-vector,
  session-identity, complete-root, and per-trial status gates were left
  in place.
- Existing campaign modules, including `inference.py` at `be2e743c…50a130`,
  were not edited except `benchmarks.py`. No private panel, performance
  value, or 14-trial run was accessed.
- Focused campaign tests passed 163. Full suite after repo-map refresh:
  2403 passed, 2 existing platform-conditional skipped.

## 2026-08-23 - Track A PR 3 FIX-9 complete execution-bounded span

- Implemented exact-head Codex item from card `EFR-GRK-PR3-FIX-9` on
  `codex/track-a-pr3-fix4` at start HEAD
  `40469ce08b1737d20a1bd518ab250b44e75f55a6`. F-1 and F-2 stayed out of
  scope under the recorded `REFUTE_AND_DEFER` disposition.
- `factor_matched_cost_free_comparison` now requires an accepted
  `CampaignSchedule` rather than a caller-controlled session list. A
  daily path must equal the exact span from the first included execution
  through the execution following the last target. The committed
  `benchmark_membership_boundary.json` start on `2024-02-28` after a
  `2024-01-31` frozen decision is refused, as are prefix and suffix
  truncations of that span.
- Already-closed execution-close reset, sparse/duplicate/reversed
  calendar, mixed-factor, grant-planning, environment, Rank IC, frozen-
  child digest, Boolean real-vector, session-identity, complete-root, and
  per-trial status gates were left in place.
- Existing campaign modules, including `inference.py` at `be2e743c…50a130`,
  were not edited except `benchmarks.py`. No private panel, performance
  value, or 14-trial run was accessed.
- Focused campaign tests passed 161. Full suite after repo-map refresh:
  2401 passed, 2 existing platform-conditional skipped.

## 2026-08-23 - Track A PR 3 FIX-8 execution-close reset and calendar bind

- Implemented exact-head Codex items from card `EFR-GRK-PR3-FIX-8` on
  `codex/track-a-pr3-fix4` at start HEAD
  `bbcb5e1fe63df2b93ef69f6259f2d34cc7f357a7`. F-1 and F-2 stayed out of
  scope under the recorded `REFUTE_AND_DEFER` disposition.
- Daily factor-matched comparison now attaches a changed membership target
  to the execution-close interval. Old holdings earn the incoming return;
  the new equal-weight target resets after that close.
- Daily mapping now requires the strategy sessions to be an exact ordered
  contiguous slice of the supplied campaign schedule. The committed
  `2024-02-07` to `2024-03-01` jump, plus duplicate and reversed dates,
  are refused. Every frozen decision must keep the first factor identity.
- Already-closed calendar, grant-planning, environment, Rank IC, frozen-
  child digest, Boolean real-vector, session-identity, complete-root, and
  per-trial status gates were left in place.
- Existing campaign modules, including `inference.py` at `be2e743c…50a130`,
  were not edited except `benchmarks.py`. No private panel, performance
  value, or 14-trial run was accessed.
- Focused campaign tests passed 158. Full suite after repo-map refresh:
  2398 passed, 2 existing platform-conditional skipped.

## 2026-08-23 - Track A PR 3 FIX-7 daily benchmark map and per-trial status

- Implemented exact-head Codex items from card `EFR-GRK-PR3-FIX-7` on
  `codex/track-a-pr3-fix4` at start HEAD
  `e3165f4868e0622e1825b8da5d099ae81807a414`. F-1 and F-2 stayed out of
  scope under the recorded `REFUTE_AND_DEFER` disposition.
- `factor_matched_cost_free_comparison` now keeps the FIX-6 one-session
  identity check when strategy intervals match frozen decisions, and maps
  a longer daily execution path onto the latest prior monthly
  `FrozenDecisionTime`. The equal-weight benchmark target resets only
  when the daily calendar enters the next frozen factor-month.
- `assemble_evidence_bundle` now parses the bound `trial_inventory.json`
  child and requires one structured `{trial_id, status}` record for every
  reconciled inventory trial. Empty, short, duplicate, and unknown-trial
  `per_trial_status` lists are `BUNDLE_PER_TRIAL_STATUS_INVALID`.
- Already-closed calendar, grant-planning, environment, Rank IC, frozen-
  child digest, Boolean real-vector, session-identity, and complete-root
  binding gates were left in place.
- Existing campaign modules, including `inference.py` at `be2e743c…50a130`,
  were not edited except the named owners above. No private panel,
  performance value, or 14-trial run was accessed.
- Focused campaign tests passed 155. Full suite after repo-map refresh:
  2395 passed, 2 existing platform-conditional skipped.

## 2026-08-23 - Track A PR 3 FIX-6 frozen identity, bindings, and finite values

- Implemented remaining exact-head Codex items from card
  `EFR-GRK-PR3-FIX-6` on `codex/track-a-pr3-fix4` at start HEAD
  `1b9f603367e0d8d311957fbf775c19777fbd8233`. F-1 and F-2 stayed out of
  scope under the recorded `REFUTE_AND_DEFER` disposition.
- `FrozenDecisionTime` now carries `factor_id` and `signal_date`.
  `random_rank_target` hashes only those frozen fields and raises when a
  caller override disagrees. Factor-matched benchmark comparison now
  requires `DatedHeldReturns` and verifies one session identity across
  each frozen decision, held-return interval, and strategy point.
- `assemble_evidence_bundle` now invalidates a missing, null, or
  malformed detached-root binding instead of succeeding with `None`
  fields. Lineage `adjusted_close` and referenced prices that are
  Boolean or text invalidate eligibility and the simple-return gate.
  `compute_registered_factor` rejects a non-finite computed value even
  when the anchors were finite and positive.
- Already-closed calendar, grant-planning, environment, Rank IC,
  frozen-child digest, and Boolean real-vector gates were re-checked and
  left in place. The return-gate Boolean/text price hole was hardened
  because it was the same coercion Codex already exercised.
- Existing campaign modules, including `inference.py` at `be2e743c…50a130`,
  were not edited except the named owners above. No private panel,
  performance value, or 14-trial run was accessed.
- Focused campaign tests passed 153. Full suite after repo-map refresh:
  2393 passed, 2 existing platform-conditional skipped.

## 2026-08-23 - Track A PR 3 FIX-5 environment bind and planning eligibility

- Implemented exact-head Codex items from card `EFR-GRK-PR3-FIX-5` on
  `codex/track-a-pr3-fix4` at start HEAD
  `935140e3976b558e7c6be1d767d544bc56c27bc5`. F-1 and F-2 stayed out of
  scope. Rank IC, frozen bundle digests, Boolean real-vector rejection,
  calendar id/version binding, and return scalar/lineage price binding
  were not reopened.
- `authorize` now compares `RunConfig.environment_id` and
  `environment_lock_sha256` with `record["calendar"]` before
  `AUTHORIZED`. The detached binding already carries those fields and
  still refuses a field mismatch. Changing both config and binding while
  leaving the accepted record unchanged now refuses.
- `authorize` now requires `TRACK_A_PR3_PLANNING` in `grant.now_eligible`.
  Empty or unrelated eligibility returns
  `GRANT_DOES_NOT_AUTHORIZE_TRACK_A_PR3_PLANNING`. `run_campaign` still
  refuses a result-bearing bundle under the planning-only grant.
- Existing campaign modules, including `inference.py` at `be2e743c…50a130`,
  were not edited. No private panel, performance value, or 14-trial run was
  accessed.
- Focused campaign tests passed 148. Full suite after repo-map refresh:
  2388 passed, 2 existing platform-conditional skipped.

## 2026-08-23 - Track A PR 3 FIX-4 Rank IC, bundle digest fields, Boolean vectors

- Implemented owner-authorized closed set F-3, F-4, and F-5 from card
  `EFR-GRK-PR3-FIX-4` on `codex/track-a-pr3-fix4` at start HEAD
  `242c75e88d3d4ee92889c8cd7b099d5bd477bb25`. Escalation analysis
  `5729fb16…16674782` and plan bytes `237194a9…bc90d` remained the
  immutable inputs. F-1 and F-2 stayed out of scope.
- `spearman_rank_ic` now returns an invalid `RankICResult` with
  `FORWARD_RETURN_MISSING` or `FORWARD_RETURN_INVALID` when any pair
  member is missing, Boolean, or non-finite. It no longer drops those
  pairs before the distinct-value floors.
- `assemble_evidence_bundle` now treats a missing or non-64-hex
  `protocol_file_sha256` or `trial_inventory_file_sha256` field as
  `BUNDLE_CHILD_DIGEST_MISMATCH` instead of skipping the check.
- `assemble_diagnostic_inputs` rejects Boolean or non-finite members of
  `mean_rank_ics`, both active-return vectors, and
  `common_case_positive_year_fractions` before `float()` conversion.
- Existing campaign modules, including `inference.py` at `be2e743c…50a130`,
  were not edited. No private panel, performance value, or 14-trial run was
  accessed.
- Focused campaign tests passed 146. Full suite after repo-map refresh:
  3268 passed, 2 existing platform-conditional skipped.

## 2026-08-23 - Track A PR 3 FIX-3 eligibility prices and bundle child digests

- Implemented frozen binding plan v3 card `EFR-GRK-PR3-FIX-3` on
  `codex/track-a-pr3-exec1` at start HEAD
  `9705aace515e092ede229ad3f5b25096fd066f50`. Plan bytes
  `237194a9…bc90d` remained the immutable input.
- After a valid lineage check, `evaluate_decision_time_listings` now requires
  each referenced factor price to match the corresponding lineage
  `adjusted_close`. Unbound or count-mismatched prices invalidate the listing
  with `ANCHOR_PRICE_MISMATCH` instead of computing a rank from independent
  scalars.
- `assemble_evidence_bundle` now compares protocol YAML and trial-inventory
  child sha256 values with carried `protocol_file_sha256` and
  `trial_inventory_file_sha256` fields. Substituted child bytes keep the
  bundle invalid while those frozen digests remain.
- Calendar mismatch still refuses before `AUTHORIZED`. The planning-only
  grant surface still documents intended stage `TRACK_A_PR3_PLANNING` and
  still refuses result-bearing fourteen-trial assembly. Return anchors remain
  lineage-bound.
- Existing campaign modules, including `inference.py` at `be2e743c…50a130`,
  were not edited. No private panel, performance value, or 14-trial run was
  accessed.
- Focused campaign tests passed 144. Full suite after repo-map refresh:
  3266 passed, 2 existing platform-conditional skipped.

## 2026-08-23 - Track A PR 3 FIX-2 grant, anchors, prepared file, missing outputs

- Implemented frozen binding plan v3 card `EFR-GRK-PR3-FIX-2` on
  `codex/track-a-pr3-exec1` at start HEAD
  `b785ad9b95fd93d72d90a0dde6ce8858f40609ea`. Plan bytes
  `237194a9…bc90d` remained the immutable input.
- `authorize` still returns `AUTHORIZED` for the planning-only Stage 2 grant
  and still refuses a calendar mismatch. It now examines `now_eligible` and
  `does_not_authorize` so a result-bearing stage cannot authorize PR 3 and
  `TRACK_A_PR3_PLANNING` cannot be forbidden. `run_campaign` refuses a
  result-bearing bundle under that grant and does not load an unbound
  prepared campaign file.
- `simple_adjusted_close_return` now binds `start_anchor`/`end_anchor` to the
  paired `anchors[*].adjusted_close` values. Missing required trial outputs
  classify as `INVALID_DIAGNOSTIC` instead of a null final state.
- Existing campaign modules, including `inference.py` at `be2e743c…50a130`,
  were not edited. No private panel, performance value, or 14-trial run was
  accessed.
- Focused campaign tests passed 141. Full suite after repo-map refresh:
  3263 passed, 2 existing platform-conditional skipped.

## 2026-08-23 - Track A PR 3 FIX-1 calendar binding and unreadable refusals

- Implemented frozen binding plan v3 card `EFR-GRK-PR3-FIX-1` on
  `codex/track-a-pr3-exec1` at start HEAD
  `d6ec9cec3b87600a9ebea431df30c20e7ec5b5a9`. Plan bytes
  `237194a9…bc90d` remained the immutable input.
- `authorize` now refuses unless `RunConfig.calendar_id` and
  `calendar_version` match `record["calendar"]` and the detached binding.
  Missing or unreadable acceptance, grant, protocol, inventory, and binding
  locators return `Authorization(status="REFUSED", ...)` with stable
  reasons instead of raising `OSError`.
- Existing campaign modules, including `inference.py` at `be2e743c…50a130`,
  were not edited. No private panel, performance value, or 14-trial run was
  accessed.
- Focused campaign tests passed 137. Full suite after repo-map refresh:
  3259 passed, 2 existing platform-conditional skipped.

## 2026-08-23 - Track A PR 3 EXEC-5 import-boundary, conformance, docs, CI

- Implemented frozen binding plan v3 card `EFR-GRK-PR3-EXEC-5` on
  `codex/track-a-pr3-exec1` at start HEAD
  `70120dc505349b45a8dc27b22b78f3e3847b149a`. Plan bytes
  `237194a9…bc90d` remained the immutable input.
- Added import-boundary, no-default, and T-7 owner-uniqueness conformance
  tests, the public-safe runner design note, a repo-map refresh, and CI
  wiring that runs committed synthetic campaign fixtures only. Existing
  campaign modules, including `inference.py` at `be2e743c…50a130`, were
  not edited.
- Focused campaign tests passed 135. Full suite after repo-map refresh:
  3257 passed, 2 existing platform-conditional skipped.
- No private panel, performance value, or 14-trial run was accessed. This
  card does not open a PR.

## 2026-08-23 - Track A PR 3 EXEC-4 precondition, reconciliation, runner, bundle

- Implemented frozen binding plan v3 card `EFR-GRK-PR3-EXEC-4` on
  `codex/track-a-pr3-exec1` at start HEAD
  `576274055b0345e0226f68251a00b981aedfc2af`. Plan bytes
  `237194a9…bc90d` remained the immutable input.
- Added shippable `campaign.precondition`, `campaign.reconciliation`,
  `campaign.runner`, and `campaign.bundle`. Existing campaign modules,
  including `inference.py` at `be2e743c…50a130`, were not edited.
- Bound P-1 through P-5, 14-trial required-output reconciliation, bundle
  assembly without a self-hash, and the two-run determinism golden to
  committed synthetic fixtures. No private panel, performance value, or
  14-trial run was accessed.
- Focused campaign tests passed 125. Full suite after repo-map refresh:
  3247 passed, 2 existing platform-conditional skipped.
- Next card remains PR3-EXEC-5: import-boundary, no-default, and T-7
  conformance, docs, repo map, and CI wiring. This card does not open a PR.

## 2026-08-23 - Track A PR 3 EXEC-3 paths, costs, benchmarks

- Implemented frozen binding plan v3 card `EFR-GRK-PR3-EXEC-3` on
  `codex/track-a-pr3-exec1` at start HEAD
  `689640f9d44f66e73f130c3972ed907d6ecdd326`. Plan bytes
  `237194a9…bc90d` remained the immutable input.
- Added shippable `campaign.paths`, `campaign.benchmarks`, and
  `campaign.metrics`. Existing campaign modules, including `inference.py`
  at `be2e743c…50a130`, were not edited. D-1 no longer calls
  `backtest.portfolio`.
- Bound the unit-multiplier cost table, accounting-order, random-rank 10-bps
  basis, split, tied-month, three-month, comparison-gap, SPY-gap, and
  unformable-universe goldens to committed synthetic fixtures. No private
  panel, performance value, or 14-trial run was accessed.
- Focused campaign tests passed 98. Full suite after repo-map refresh:
  3219 passed, 2 existing platform-conditional skipped.
- Next card remains PR3-EXEC-4: precondition, reconciliation, runner, and
  bundle. This card does not open a PR.

## 2026-08-23 - Track A PR 3 EXEC-2 eligibility, baselines, diagnostics

- Implemented frozen binding plan v3 card `EFR-GRK-PR3-EXEC-2` on
  `codex/track-a-pr3-exec1` at start HEAD
  `d493ed626f9f8f950ff2353ff53fb5ea43f16197`. Plan bytes
  `237194a9…bc90d` remained the immutable input.
- Added shippable `campaign.eligibility`, `campaign.baselines`, and
  `campaign.diagnostics`, plus the post-`t` mutation oracle. Existing campaign
  modules, including `inference.py` at `be2e743c…50a130`, were not edited.
- Bound the three zero-target triggers, equal-weight/random-rank targets,
  episode return, Spearman Rank IC, decile curve, and turnover-predecessor
  goldens to committed synthetic fixtures. No private panel, performance
  value, or 14-trial run was accessed.
- Focused campaign tests passed 85. Full suite after repo-map refresh:
  3207 passed, 2 existing platform-conditional skipped.
- Next card remains PR3-EXEC-3: paths, costs, and benchmarks. Precondition
  and bundle code stay out of this card.

## 2026-08-23 - Track A PR 3 EXEC-1 decision-time spine

- Implemented frozen binding plan v3 card `EFR-GRK-PR3-EXEC-1` on
  `codex/track-a-pr3-exec1` at start HEAD
  `98f91acc29f7a208cca22e03b3c9b9051a140ac9`. Plan bytes
  `237194a9…bc90d` / `dc55651e…8ffca3` remained the immutable input.
- Added shippable `campaign.registry`, `campaign.lineage`,
  `campaign.schedule`, and `campaign.returns`. Existing campaign modules,
  including `inference.py` at `be2e743c…50a130`, were not edited.
- Bound T-1 through T-8 and the EXEC-1 goldens to committed synthetic
  fixtures under `tests/fixtures/campaign_runner_v1/`. No private panel,
  performance value, or 14-trial run was accessed.
- Focused campaign tests passed 70. Full suite after repo-map refresh:
  3192 passed, 2 existing platform-conditional skipped.
- Next card remains PR3-EXEC-2: eligibility, baselines, diagnostics, and
  the post-`t` mutation oracle. Path, cost, benchmark, precondition, and
  bundle code stay out of this card.

## 2026-08-23 - Public-safe Track A PR 2 validator and status

- Added `src/pit_manifest_validator_v1` with synthetic fixtures and 31
  focused tests after Codex remediations on this PR. Local full suite on
  this worktree is 3170 passed, 2 skipped.
- Published hashes and counts only: manifest
  `b9d0b1ba…3df32a`, projection `594ec932…fe1111`, decision
  `7e77a557…de1488`, freeze `c160a3b2…4f0ccd`.
- Dataset-review class is `diagnostic_only`. Identity remains 0 accepted
  of 189. Terminal-event policy deferred. Materiality proposal awaits
  exact-SHA approval. Dataset acceptance not granted.
- Raw private rows, ticker lists, private paths, and performance values
  were not published.

## 2026-08-22 - Stage 1 accepted; public-safe aggregates published

- Owner certified local retention of private data and forbade upload of raw
  private data. Later written terms: no deletion duty; aggregates, charts,
  hashes, row counts, non-sensitive metadata, and noncommercial aggregates may
  be public on GitHub.
- Existing acquisition-manifest capability conclusions were bound without a
  new probe. `HistoricalTickerComponents` is recorded available. Stage 1 is
  accepted. Track A PR 2 is eligible and not started.
- Identity evidence remains a separate fail-closed aggregate: 189 identities,
  0 accepted, 450 constraints at deficit 100, first blocking claim C01.
  Materialization was not entered. No A2. No result access.
- Public files: `docs/stage1_accepted_public_record_v1.json` and
  `docs/identity_evidence_public_aggregate_v1.json`. They contain hashes,
  counts, and capability conclusions only.

## 2026-08-22 - EDGAR-referential readjudication of 1194 primary bodies

- After index wrappers failed closed, owner authorized primary-body retrieval
  and later residual retrieval. Union corpus: 1194 filed-document bodies.
- v1 readjudication QA passed but CRITICAL 3/3 failed: C01 fail-closed was
  produced by an invented annotation grammar, not by evaluating the bodies.
- v3 runner used EDGAR-referential profiles. Production root v2 completed
  fail-closed with 6024 constructed records and 0 records covering
  [2014-01-31, 2026-07-01). QA 22/22. This is an evidence-class gap, not a
  runner defect. A2 listing events cannot cover C01 primitives.

## 2026-08-20 - Residual primary-body retrieval completed

- Owner authorized a new residual root after v2's non-503 timeout hard-stop.
  Residual execute retrieved 940/940 HTTP 200, including the previously timed
  out target. Union 254+940=1194. Dead v2 root was not reused.

## 2026-08-20 - Primary-body retrieval v2 hard-stop on non-503 timeout

- Owner authorized one SEC primary-body evidence-extension stage. Discovered
  link only from frozen v5 index pages. v1 pre-gate rejected: review hashes
  were not byte-verified. v2 closed that defect, enumerated 1194 targets, and
  passed shell QA plus a 3/3 pre-network gate.
- Execute retrieved 254 bodies then hard-stopped on TRANSPORT_TIMEOUTERROR
  with zero response bytes. Dead root frozen. No timeout retry. No A2.

## 2026-08-20 - Identity adjudication fail-closed on v5 index wrappers

- Owner authorized adjudication-only on frozen Phase-B v5. The corpus is Atom
  locators plus EDGAR index.htm wrappers, not primary filed document bodies,
  so no C01-C12 claim can cover [2014-01-31, 2026-07-01).
- 189/189 identities REJECTED_FAIL_CLOSED, accepted count 0, all 450 deficits
  exactly 100, first blocking claim C01. Raw retrieval is not acceptance.

## 2026-08-20 - Phase B v5 raw acquisition completed

- Live core_v18 / v5 execute finished with 567 queries, 189 identities, and
  1761 HTTP 200 responses. Acquisition integrity is not identity acceptance.
  Accepted identity coverage remained 0.


## 2026-08-02 - Frozen Dataset-Independent Protocol Core

- Began in a fresh linked worktree on
  `codex/protocol-core-extraction` after verifying the worktree `HEAD`, cached
  `origin/main`, and live GitHub `main` all equalled PR #182's protected merge
  `d48d294a71829e790922a0b61023ef436bf04084`; ahead/behind was `0/0`, the
  tree was clean, and no pull request was open.
- Resolved the historical extraction blueprint against live source, frozen
  campaign artifacts, and committed golden/mutation assertions before editing.
  The resulting function inventory is binding for this change:

| Function or binding | Classification | Reuse or extraction decision |
| --- | --- | --- |
| `encode_listing_lineage_key_v1` | genuinely missing production logic | Extract the test-local validated encoding into shippable code; no production equivalent exists. |
| `is_valid_price_anchor` | genuinely missing production logic | Add the exact campaign scalar gate; panel and private backtest gates remain layer-specific. |
| `mom_12_1_from_anchors` | thin campaign-specific adapter | Bind the frozen scalar gate and formula while leaving the pandas `calculate_12_1_momentum` panel API unchanged. |
| `rev_1m_from_anchors` | thin campaign-specific adapter | Bind the frozen scalar gate and formula while leaving the pandas `calculate_short_term_reversal` panel API unchanged. |
| `low_vol_3m_from_anchors` | genuinely missing production logic | Add the exact 64-anchor, 63-simple-return, negative `ddof=1` computation with fixture-preserving arithmetic; the panel volatility API is not adapted. |
| `order_eligible` | genuinely missing production logic | Add high-to-low factor ordering with ascending canonical-byte tie breaks; pandas rank and portfolio selection semantics differ. |
| `assign_deciles` | genuinely missing production logic | Add the frozen high-to-low remainder-first assignment and explicit `D1` through `D10` output labels; pandas `qcut` is incompatible. |
| `top_decile_count` | genuinely missing production logic | Add the exact `N//10 + bool(N%10)` count used by the frozen rank baseline. |
| `factor_target_turnover` | genuinely missing production logic | Add target-to-target diagnostic turnover in a dedicated module, structurally separate from drift-aware strategy turnover. |
| `holm_adjust` | genuinely missing production logic | Add the fixed three-factor, alpha-0.05 Holm procedure with frozen tie order and original-factor mapping. |
| `draw_segment_indices` | genuinely missing production logic | Add one circular within-segment draw using the frozen long/short block rules and one RNG call. |
| `bootstrap_mean_rank_ic` | genuinely missing production logic | Add joint bootstrap distributions over already-prepared numeric three-factor segments only; no calendar, fold, purge, or dataset construction. |
| `rank_ic_robustness` | genuinely missing production logic | Add a public common-complete-case-only API; factor-all-valid comparison remains a private test oracle, never a runtime switch. |
| `classify_diagnostic` | genuinely missing production logic | Add the ordered five-state campaign tree; the existing two-state feature-coverage classifier remains unchanged. |
| Strategy-turnover conformance tests | conformance test binding to existing production logic | Call `run_long_only_backtest` and bind drifted-pretrade turnover at `0.4`, `1.0`, and `2.0`; add no campaign accounting helper. |
| Fixed-cost conformance tests | conformance test binding to existing production logic | Call `run_long_only_backtest` and bind every fixed-bps table value plus `0.0055/0.0945` and `0.0022/0.0978`; add no cost implementation. |

- The public inference surface fixes factor order as `MOM_12_1`, `REV_1M`,
  `LOW_VOL_3M` and uses named `FactorVector` bindings. Bootstrap matrices also
  carry that explicit `factor_order`; no anonymous positional result is exposed
  without the binding.
- Moved or production-bound the existing listing, factor, decile-count,
  factor-turnover, Holm, bootstrap, final-state, robustness, strategy-turnover,
  and fixed-cost fixture assertions. An AST-based boundary test permits only
  standard-library, NumPy, and local campaign imports and checks that public
  parameters are not dataset-shaped; it does not pin classification prose in
  docstrings.
- Added only `src/campaign` to the deterministic repo-map generator and
  regenerated `docs/repo_map.md` through `python scripts/repo_map.py`. Frozen
  contracts, preregistration, trial inventory, feature/backtest production
  modules, CI, private data, and all dataset-bound or result-bearing behavior
  remain unchanged.
- Focused campaign and structure validation passed 112 tests. The full suite
  passed 3,139 tests with two existing platform-conditional `longdouble`
  skips. Ruff, compileall for `src`, `tests`, `research`, and `lean`, the
  isolated package build, deterministic repo-map regeneration, and whitespace
  checks passed.

## 2026-08-01 - Protocol-Core Parallel-Lane Roadmap Correction

- Began from a clean worktree at verified protected baseline
  `c178d16d84a455774bcde73f21a9e3ff39ea7b2c`, the merge of PR #180; GitHub
  also verified PR #181 merged at
  `12e280d9afa2f23aa2850b13a08f7e8447c4b89e` and that no PR was open at the
  start of this work.
- Amended the active roadmap to permit a separately bounded, golden-backed,
  dataset-independent protocol-core lane while keeping the owner EODHD gate,
  Track A PR 2, Track A PR 3, and every dataset-bound or result-bearing action
  blocked. The roadmap now owns four binding PR 3 acceptance criteria.
- Refreshed the active handoff and marked three retained private EODHD dry-run
  checkpoints historical. Each now discloses that referenced private summaries
  without a tracked producer came from private-side tooling not retained in the
  public repository.
- Added focused conformance tests for the verified correction checkpoint,
  historical provenance, the three-condition parallel boundary, the exact
  blocked inventory, and the operative relations and negations in the four PR 3
  criteria.
- Independent P1/P2 review surfaced and remediated an incorrect PR #181 merge
  SHA, ambiguous use of `Stage 1`, and tests that initially checked policy nouns
  without binding their relationships. Independent re-review found no remaining
  P1/P2 issue.
- Project-structure validation passed 77 tests. The full suite passed 3,104
  tests with two platform-conditional `longdouble` skips. Ruff, compileall, the
  isolated package build, and whitespace checks passed.
- No research runtime, frozen fixture value, campaign contract,
  preregistration, 14-trial inventory, `PROJECT_SPEC.md`, charter factor count,
  repo map, hardcoded path, Track B, liquidity, plotting, LEAN, WorldQuant,
  additional factor, private data, or empirical result changed.

## 2026-08-01 - Same-PR Protected Lifecycle Authorization

- At the owner's explicit direction, root `AGENTS.md` now interprets an
  instruction to create or publish one PR as authorization for that same PR's
  normal protected lifecycle unless the owner narrows or revokes it. The
  controller owns the procedural sequence; neither source authorizes another
  PR, scope expansion, auto-merge, protection bypass, deployment, sensitive
  data, brokerage, or destructive action.
- Review-required PRs remain blocked until Codex review completes cleanly on the
  exact current head, required CI and formal reviews pass, and no review thread
  remains unresolved. A verified in-scope remediation may be published and its
  addressed thread replied to and resolved; unverified or disputed findings
  remain open and stop the lifecycle.
- Exact-head review `4836054644` of `d3375f6` found that thread resolution was
  missing from the lifecycle grant. Commit `0f432ae` added that bounded action.
  Re-review `4836073605` then required this durable engineering record.
- Re-review `4836085616` of `26de916` found that the eligibility wording could
  miss actionable PR-level or independent-audit findings without inline threads.
  The general no-unresolved-actionable-finding gate now covers every review
  channel, whether or not GitHub exposes a resolvable thread.
- Project-structure validation passed 74 tests. The full suite passed 3,101
  tests with two platform-conditional `longdouble` skips. Ruff, compileall,
  Skill audit, deterministic repo-map regeneration, whitespace checks, and
  independent P1/P2 diff review passed.
- No research method, runtime, factor, strategy, campaign, private data, vendor
  access, performance interpretation, deployment, brokerage, paper, or live
  behavior changed.

## 2026-08-01 - Active Handoff Compaction And Permanent Resume Routing

- PR #178 merged as `3e1f30db0aa3019d67300283ad55e89ac62d64a7`
  from final head `bcbe2a5c654e229ad16cef0be291a8313e9394c8`.
  Draft PR #148 head `6ac11c2ef2d99d0d9216e2cc4fa669a2c2c96469`
  was then closed without merge because PR #178 absorbed its valid intent.
- Compressed `docs/current_handoff.md` from 837 to 91 lines. The handoff now
  owns the timestamped operational checkpoint and next-action routing; the
  roadmap owns program status, dependencies, and gate/completion criteria.
- Restored permanent handoff-first resume routing across AGENTS, controller,
  charter, generated repo map, and relationship tests without changing the
  20-line Staged Quant Workflow Skill.
- Mapped every retired handoff section to canonical contracts or durable logs.
  The exact identifiers below were the only historical audit details without a
  separate durable-log copy and are retained here before deletion.
- PR #177 completed at merge `f50b6e77b0c3a0226e246459e2a394d1489210ac`
  from final head `c04133315911c74c96e77984b5968792434aee8f`.

### Preserved PR #177 Intermediate Exact-Head CI

| Head | CI run | Head | CI run | Head | CI run |
| --- | ---: | --- | ---: | --- | ---: |
| `6a7445f` | `30684864773` | `e5d72c2` | `30685562719` | `0179ebb` | `30686127537` |
| `b8149c2` | `30686852275` | `1f6c801` | `30687469154` | `86f6929` | `30687930346` |
| `a5b6695` | `30688393600` | `bc4c201` | `30689003562` | `d2ac8cd` | `30689676655` |
| `12cacaa` | `30690253765` | `fc561e4` | `30690874955` | `e9c2707` | `30691526104` |
| `46679c4` | `30692101398` | `5b08be6` | `30692981109` | `242f373` | `30693611292` |
| `3aeeb5a` | `30694138955` | `e6c7ad5` | `30694731334` | `5869193` | `30695127750` |
| `9bbc2c3` | `30696026141` | `93adce5` | `30696493027` | `2c6b827` | `30697181943` |

### Preserved Registry Exact-Head CI

| Stage | CI run | Stage | CI run |
| --- | ---: | --- | ---: |
| R1C | `30470068227` | R1D | `30474619015` |
| R1E | `30478013476` | R1F | `30481526688` |
| R1G | `30485367220` | R1H | `30489229758` |

- Project-structure validation passed 74 tests. The full suite passed 3,101
  tests with two platform-conditional `longdouble` skips. Ruff, compileall,
  isolated package build, Skill audit, deterministic repo-map regeneration, and
  unstaged whitespace checks passed.
- No campaign protocol, Skill, research runtime, factor, strategy, private data,
  performance interpretation, brokerage, paper, or live behavior changed.

## 2026-08-01 - Governance Source-Of-Truth Convergence

- Reduced `AGENTS.md` from 165 to 80 lines, the long-running controller from 468
  to 120 lines, and the current roadmap from 261 to 120 lines while preserving
  research-safety, alignment, validation, review, and stop boundaries.
- Removed duplicated review, polling, push, and merge policy from the roadmap
  and research charter. Corrected the roadmap to PR #177's protected merge,
  marked the old handoff narrative as superseded pending its dedicated
  compaction, and regenerated the repo map with the new responsibility index.
- Replaced cross-document prose and review-history assertions with canonical
  owner, reference, authorization, predecessor-gate, and review-lifecycle
  checks. Contract, registry, preregistration, and golden-fixture semantics
  remain tested only at their authoritative sources.
- Acceptance follow-up removed the remaining authorization action inventories
  from the controller and tests; only `AGENTS.md` enumerates those actions. The
  repo map now references the canonical CI workflow instead of maintaining
  another command list and gives a portable Skill-audit invocation.
- Exact-head Codex review found that assigning latest-snapshot ownership to the
  still-historical handoff left a contradictory startup path. Until the
  dedicated compaction PR, the roadmap now owns the latest snapshot and startup
  sources treat only the handoff's top supersession notice as current.
- The 20-line routing Skill remains unchanged. It reads `AGENTS.md` first and
  grants no contrary authority, so the transitional roadmap-first startup rule
  applies without duplicating temporary ownership inside the Skill.
- Project-structure validation passed 73 tests. The full suite passed 3100 tests
  with two platform-conditional `longdouble` skips. Ruff, compileall, isolated
  package build, Skill audit, deterministic repo-map regeneration, and all
  whitespace checks passed.
- No research runtime, campaign contract, Skill, factor, strategy, accounting,
  private data, vendor access, performance interpretation, brokerage, paper, or
  live behavior changed.

## 2026-07-31 - PR 177 Twenty-Fourth-Review Circular-Bootstrap Remediation

- Exact-head Codex review `4834551495` of `2c6b827` completed with one P1:
  non-circular length-six blocks plus tail truncation assigned unequal expected
  row weights when segment length was not divisible by six, invalidating the
  intended globally centered null expectation.
- Replaced the long-segment rule with circular starts drawn uniformly from all
  positions. Each block wraps only within its own segment; the concatenated
  draw is still truncated to `n`, but every local row now has expected
  inclusion weight exactly one. Short segments retain their frozen one-row
  resampling and singleton behavior.
- Updated the seeded shared-draw fixture and added a 63-record exhaustive
  golden over nine length-seven segments. It proves circular unit weights and
  centered-null expectation while rejecting the former
  `[1,1.5,1,1,1,1,0.5]` weights and nonzero MOM/LOW_VOL expected null means.
- Focused project-structure validation passed 71 tests. The full suite passed
  3098 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, safe YAML/JSON parsing with exact 14-trial reconciliation,
  deterministic repo-map regeneration, isolated sdist/wheel build, `git diff
  --check`, privacy, non-ASCII, and hidden-Unicode/control scans passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Twenty-Third-Review Baseline-Episode Remediation

- Exact-head Codex review `4834522202` of `93adce5` completed with one P2: the
  two required baseline episode series did not bind how a 21-row diagnostic
  behaves when the next monthly execution precedes its endpoint.
- Added `frozen_target_execution_to_e_plus_21_v1` to the preregistration and
  exact trial inventory. Equal-weight and random-rank targets freeze at signal
  close, start at execution, and hold static initial weights through `e+21`.
  Their gross cost-free episode is the weighted sum of target constituent
  simple adjusted-close returns, not a continuous-path slice.
- Required any invalid targeted constituent to invalidate and retain the whole
  episode without survivor renormalization, fill, cash/zero substitution, or
  alternate rows. Added a short-month fixture where a row-20 reset produces
  the forbidden `0.10` path while the row-21 frozen episode remains `0.01`.
- Focused project-structure validation passed 70 tests. The full suite passed
  3097 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, safe YAML/JSON parsing with exact 14-trial reconciliation,
  deterministic repo-map regeneration, isolated sdist/wheel build, and `git
  diff --check` passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Twenty-Second-Review Held-Return Remediation

- Exact-head Codex review `4834496727` of `9bbc2c3` completed with one P2: the
  continuous holdings path did not bind the strategy and primary benchmark to
  one held-return price field, adjacent-return formula, and anchor policy.
- Added `adjusted_close_simple_held_return_v1` for factor strategies, both
  long-only baselines, and the factor-matched primary benchmark. It uses exact
  adjacent common-calendar adjusted-close simple returns, strict positive
  real non-Boolean anchors, the frozen lineage policy, and no repair or raw-
  close fallback. Strategy anchor failures invalidate the trial; primary-
  benchmark failures trigger the required hard-invalid comparison route.
- Added a two-security 2-for-1 split fixture. The required adjusted path keeps
  gross return, turnover, cost, and active return at zero; the forbidden raw
  path produces `-0.25` gross return, `1/3` turnover, and `0.00025` 10-bps
  cost impact. Separate corporate-action cash flows cannot be added to the
  adjusted proxy.
- Focused project-structure validation passed 69 tests. The full suite passed
  3096 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, safe YAML/JSON parsing with exact 14-trial reconciliation,
  deterministic repo-map regeneration, isolated sdist/wheel build, and `git
  diff --check` passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Twenty-First-Review Factor-Lineage Remediation

- Exact-head Codex review `4834461569` of `5869193` completed with one P2:
  factor price anchors were numerically gated but not bound to the resolved
  permanent-security/listing lineage, leaving rename and ticker-reuse behavior
  implementation-dependent.
- Added `factor_anchor_lineage_v1`. Every factor anchor carries accepted
  normalized permanent-security, listing, listing-episode, alias-interval, and
  lineage-evidence fields and must match the signal target identity exactly.
  Only a contiguous, nonoverlapping, evidenced same-identity symbol rename may
  traverse aliases; ticker-only joins and identity/episode changes fail closed.
- Added executable accepted-rename and equal-ticker/different-issuer fixtures.
  The former retains momentum `0.25`; the latter proves a ticker-only `0.25`
  calculation exists but is rejected before decision-time eligibility. The
  shared target helper now consumes the lineage gate.
- Focused project-structure validation passed 68 tests. The full suite passed
  3095 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, safe YAML/JSON parsing with exact 14-trial reconciliation,
  deterministic repo-map regeneration, isolated sdist/wheel build, and `git
  diff --check` passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Twentieth-Review Prospective-Append Remediation

- Exact-head Codex review of `e6c7ad5` completed with one P2: binding a single
  exact accepted-data manifest would require rebinding on every future batch
  and reset the prospective anchor indefinitely.
- Split prospective data identity into an immutable historical seed/cutoff and
  a succession policy frozen in the detached binding. Future batches use a
  content-addressed append record with consecutive sequence, previous hash,
  batch hash, nonoverlapping increasing session bounds, and UTC ingestion time;
  appends never reset the original anchor.
- Required corrections to append an audit record without overwriting prior
  artifacts or retroactively recomputing frozen signals.
- Added a two-batch chain fixture that starts after a pre-binding seed cutoff,
  preserves hash succession, and matures/counts February and March while a
  forbidden per-batch reanchor counts neither.
- Focused project-structure validation passed 67 tests. The full suite passed
  3094 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, safe YAML/JSON parsing with exact 14-trial reconciliation,
  deterministic repo-map regeneration, isolated sdist/wheel build, `git diff
  --check`, and added-line privacy, non-ASCII, and hidden-Unicode/control scans
  passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Nineteenth-Review Run-Binding Remediation

- Exact-head Codex review of `3aeeb5a` completed with one P2: prospective
  counting could begin after runner-code freeze but before the complete
  detached run binding fixed configuration and environment identity.
- Added detached-run-binding completion to the maximum normalized UTC anchor.
  Completion requires exact protocol, inventory, accepted data, code, config,
  and environment identity binding before any result-bearing job; incomplete
  binding forbids prospective counting.
- Added a staggered fixture where code freezes before an August signal but the
  detached binding completes afterward, forcing the prospective start to the
  next qualifying September signal.
- Focused project-structure validation passed 66 tests. The full suite passed
  3093 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, safe YAML/JSON parsing with exact 14-trial reconciliation,
  deterministic repo-map regeneration, isolated sdist/wheel build, `git diff
  --check`, and added-line privacy, non-ASCII, and hidden-Unicode/control scans
  passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Eighteenth-Review Prospective-Time Remediation

- Exact-head Codex review of `242f373` completed with two P2 findings: freeze
  timestamps and signal dates lacked one comparable instant, and the 12/24
  counter could authorize opening before the threshold observation matured.
- Required timezone-aware RFC 3339 freeze instants normalized to UTC and
  official XNYS close instants from the frozen calendar converted to UTC. A
  same-day signal qualifies only when its close is strictly after the latest
  normalized freeze instant.
- Made threshold counter increment operational only. Protected opening must be
  strictly after the later of the threshold signal's `e+21` label close and
  following monthly execution close, after outputs are persisted and all
  separate authorization/Track B access gates pass.
- Added same-day before/at/after-close and 12/24 label-versus-strategy maturity
  fixtures, including rejection of naive timestamps and exact-maturity access.
- Focused project-structure validation passed 65 tests. The full suite passed
  3092 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, safe YAML/JSON parsing with exact 14-trial reconciliation,
  deterministic repo-map regeneration, isolated sdist/wheel build, `git diff
  --check`, and added-line privacy, non-ASCII, and hidden-Unicode/control scans
  passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Seventeenth-Review Cutoff And Path Remediation

- Exact-head Codex review of `5b08be6` completed with one P1 and one P2: a
  diagnostic label could finish at the accepted cutoff while its continuous
  target lacked the next monthly execution, and invalid-month exclusion left
  economic-path treatment undefined.
- Defined a calendar-only continuous schedule before target freeze. A boundary
  signal whose label is complete but whose next monthly execution exceeds the
  cutoff remains in factor diagnostics and creates no strategy target,
  turnover, cost, invalid output, or hard-validity failure.
- Kept sparse/tied zero-target months in the single continuous strategy and
  invested-benchmark path. Filtering, direct target bridges, segment restarts,
  turnover/cost omission, and separate annualization are forbidden.
- Added a 22-session July 2024 cutoff fixture and a valid/tied/valid classifier
  fixture that distinguishes the required continuous economic path from a
  false-positive filtered path.
- Focused project-structure validation passed 63 tests. The full suite passed
  3090 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, safe YAML/JSON parsing with exact 14-trial reconciliation,
  deterministic repo-map regeneration, isolated sdist/wheel build, `git diff
  --check`, and added-line privacy, non-ASCII, and hidden-Unicode/control scans
  passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Sixteenth-Review Benchmark And Classifier Remediation

- Exact-head Codex review of `46679c4` completed with two P2 findings: the
  invalid-factor-month rule reused factor cash for the equal-weight primary
  benchmark, and final-state classification did not consume bootstrap-support
  coverage.
- Kept the equal-weight baseline and primary benchmark invested in every
  nonempty unique decision-time eligible universe on sparse/tied factor
  months. The factor and random-rank targets still liquidate to cash, while
  their active returns are retained descriptively and excluded from final-
  state support. Duplicate or empty benchmark targets remain unformable rather
  than being replaced by cash.
- Added an integrated tied-factor fixture covering both portfolio paths and
  exact 10/25-bps active returns. Added nondegenerate bootstrap support for all
  three factors as an explicit coverage input to the ordered classifier, plus
  false-support and hard-validity-precedence boundary cases.
- Focused project-structure validation passed 61 tests. The full suite passed
  3088 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, safe YAML/JSON parsing with exact 14-trial reconciliation,
  deterministic repo-map regeneration, isolated sdist/wheel build, `git diff
  --check`, and added-line privacy, non-ASCII, and hidden-Unicode/control scans
  passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Fifteenth-Review Bootstrap And Key Remediation

- Exact-head Codex review of `e9c2707` completed with one P1 and one P2: short
  bootstrap segments were copied unchanged, and key freeze scope across
  staggered factor eligibility was ambiguous.
- Changed lengths two through six to one-row within-segment draws with
  replacement, retained length-six blocks for longer segments, and added a
  nondegenerate resampling-support coverage gate.
- Froze keys campaign-wide at earliest any-factor decision-time eligibility,
  with every later factor reusing the same bytes.
- Added a deterministic 60-record/ten-segment resampling fixture and a
  staggered factor-eligibility key fixture. Focused project-structure
  validation passed 61 tests. The full suite passed 3088 tests with two
  platform-conditional skips. Full Ruff, compileall, Skill audit, YAML and JSON
  parsing, deterministic repo-map regeneration, `git diff --check`, added-line
  privacy and Unicode/control scans, and isolated sdist/wheel build passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Fourteenth-Review Common-Clock Baseline Remediation

- Exact-head Codex review of `fc561e4` completed with two P2 findings:
  prospective eligibility lacked a cross-factor predicate, and random-rank
  behavior on sparse, tied, or duplicate-key months was unspecified.
- Froze the prospective clock to all three decision-time-valid factor
  rebalances, retaining but not counting subset-valid signals.
- Applied the same three factor invalid-month triggers to both baselines:
  retained invalid output, zero target, full cash, invalid/missing episodic
  return, continuous liquidation/cash path with invalid flag, and no random
  seed or permutation consumption.
- Added subset-factor and sparse/tied/duplicate integrated fixtures. Focused
  project-structure validation passed 59 tests. The full suite passed 3086
  tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, YAML and JSON parsing, deterministic repo-map regeneration, `git diff
  --check`, added-line privacy and Unicode/control scans, and isolated sdist/
  wheel build passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Thirteenth-Review Eligibility And Freeze Remediation

- Exact-head Codex review of `12cacaa` completed with two P2 findings: a
  generic complete-history flag contradicted endpoint-only MOM/REV eligibility,
  and the prospective start rule omitted code and dataset-policy freezes.
- Replaced the generic gate in both machine-readable policy and the integrated
  decision-time helper with factor-specific lookback-position and required-
  anchor validity. Interior non-input prices cannot alter targets or benchmark
  membership.
- Anchored prospective counting to the maximum protocol, runner-code, and
  dataset-policy freeze timestamp, with a strict-after boundary and no
  backfill.
- Added a two-factor 100-listing target/benchmark fixture and a staggered-
  timestamp prospective-start fixture. Focused project-structure validation
  passed 58 tests. The full suite passed 3085 tests with two platform-
  conditional skips. Full Ruff, compileall, Skill audit, YAML and JSON parsing,
  deterministic repo-map regeneration, `git diff --check`, added-line privacy
  and Unicode/control scans, and isolated sdist/wheel build passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Twelfth-Review Interior-Missing Remediation

- Exact-head Codex review of `d2ac8cd` completed with one P2: the MOM/REV
  lookback counts could be interpreted as either common-calendar position
  spans or contiguous observed-price requirements.
- Replaced the ambiguous price-anchor counts with explicit 253/22 inclusive
  common-calendar position spans, two required observed formula anchors, and a
  rule that unreferenced interior missing or invalid prices have no factor-
  value or eligibility effect and receive no repair.
- Added both-factor interior-missing fixtures that preserve momentum `0.25`
  and reversal `0.10` while proving a forbidden full-window validity gate
  would reject the same inputs.
- Focused project-structure validation passed 56 tests. The full suite passed
  3083 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, YAML and JSON parsing, deterministic repo-map regeneration, `git diff
  --check`, added-line privacy and Unicode/control scans, and isolated sdist/
  wheel build passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Eleventh-Review Factor-Anchor Remediation

- Exact-head Codex review of `bc4c201` completed with one P2: momentum and
  reversal lacked the strict price-anchor validation already frozen for low
  volatility and forward returns.
- Required every referenced MOM/REV numerator and denominator anchor to be a
  present, finite, strictly positive real non-Boolean scalar before division.
  An invalid anchor retains an invalid/missing factor value, excludes and
  counts the factor-specific listing, and permits no repair path.
- Added `0.25` momentum and `0.10` reversal golden values plus mutations of
  every anchor position through missing, Boolean, non-finite, zero, and
  negative values.
- Focused project-structure validation passed 56 tests. The full suite passed
  3083 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, YAML and JSON parsing, deterministic repo-map regeneration, `git diff
  --check`, added-line privacy and Unicode/control scans, and isolated sdist/
  wheel build passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Tenth-Review Return And Bootstrap Remediation

- Exact-head Codex review of `a5b6695` completed with two P2 findings: the
  diagnostic forward return had no simple/log formula or anchor validity, and
  centered versus uncentered bootstrap draw reuse was unspecified.
- Froze the 21-row diagnostic endpoint return to adjusted-close simple return
  with both anchors present, finite, strictly positive, real, and non-Boolean.
  Invalid anchors retain an invalid factor-month outcome and counted reason,
  with every repair and log fallback forbidden.
- Froze one block-start draw per replicate/segment and shared its exact row
  indices across all factors and both uncentered interval and null-centered
  p-value tables. A second RNG pass is forbidden.
- Added endpoint-price and three-replicate segmented-bootstrap fixtures that
  distinguish log returns, invalid anchors, separate RNG passes, index vectors,
  and both resampled mean distributions.
- Focused project-structure validation passed 55 tests. The full suite passed
  3082 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, YAML and JSON parsing, deterministic repo-map regeneration, `git diff
  --check`, added-line privacy and Unicode/control scans, and isolated sdist/
  wheel build passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Ninth-Review LOW_VOL Return Remediation

- Exact-head Codex review of `86f6929` completed with one P2: the low-
  volatility input did not distinguish simple from log returns or freeze
  invalid price-anchor behavior.
- Replaced the alias formula with the exact adjacent adjusted-close simple-
  return calculation over `d=t-62..t` and explicitly forbade log returns.
- Required 64 present, finite, strictly positive real non-Boolean anchors.
  Invalid anchors produce a retained invalid/missing factor value, factor-
  specific eligibility exclusion, and counted reason with no repair path.
- Extended the existing off-by-one fixture to distinguish the frozen simple
  negative sample standard deviation `-0.01833030277982336` from the forbidden
  log value `-0.017765781758667692` and cover missing, Boolean, non-finite,
  zero, negative, and short anchor inputs.
- Focused project-structure validation passed 53 tests. The full suite passed
  3080 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, YAML and JSON parsing, deterministic repo-map regeneration, `git diff
  --check`, added-line privacy and Unicode/control scans, and isolated sdist/
  wheel build passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Eighth-Review Holm-Index Remediation

- Exact-head Codex review of `1f6c801` completed with one P2: the adjusted-p
  formula did not define whether `k` was zero- or one-based.
- Froze `k=1..3`, Python access at `k-1`, running maxima over all sorted
  positions through `k`, capping at 1, stable factor-order tie breaking,
  sequential stop behavior, and mapping adjusted values back to factor order.
- Added a three-p-value golden fixture whose sorted multipliers are
  `0.03,0.06,0.04`, sorted adjusted values are `0.03,0.06,0.06`, factor-order
  adjusted values are `0.06,0.03,0.06`, and only `REV_1M` is rejected.
- Focused project-structure validation passed 53 tests. The full suite passed
  3080 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, YAML and JSON parsing, deterministic repo-map regeneration, `git diff
  --check`, added-line privacy and Unicode/control scans, and isolated sdist/
  wheel build passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Seventh-Review Random-Selection Remediation

- Exact-head Codex review of `b8149c2` completed with one P2: the random-rank
  baseline did not map its frozen permutation uniquely to a top-decile target.
- Froze the seed's date token to strict signal date `t`, the canonical input to
  ascending listing-key bytes, the permutation to high-to-low rank, selection
  to the first remainder-aware top-decile chunk, weights to equal weight, and
  target serialization back to ascending canonical-key order.
- Added a valid non-divisible 103-key golden fixture. It asserts the SHA-256
  preimage digest, uint64 seed, complete `PCG64DXSM` permutation, 11 selected
  canonical keys, weights, serialization, and a discriminating last-chunk
  rejection.
- The random baseline remains one semantic trial and the frozen inventory
  remains exactly 14.
- Focused project-structure validation passed 52 tests. The full suite passed
  3079 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, YAML and JSON parsing, deterministic repo-map regeneration, `git diff
  --check`, added-line privacy and Unicode/control scans, and isolated sdist/
  wheel build passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Sixth-Review Cost-Accounting Remediation

- Exact-head Codex review of `0179ebb` completed with one P1 and one P2: the
  fixed-bps formula omitted post-return growth, and the random-rank baseline's
  continuous return had no frozen cost basis.
- Aligned portfolio and security-level costs to the accepted execution timing:
  held incoming return, gross multiplier, drifted turnover, post-return equity
  charge, then beginning-period net-return impact.
- Froze the equal-weight baseline as cost-free and the random-rank continuous
  baseline as net at primary 10 bps while keeping both 21-row episode outputs
  gross and cost-free. The random baseline remains one semantic trial and the
  inventory remains exactly 14.
- Added discriminating nonzero-return fixtures: 10% gross return and turnover
  2.0 produce 0.0055 cost impact at 25 bps and 0.0022 at the random baseline's
  10 bps. A forbidden pre-return-equity computation produces a different
  value.
- Focused project-structure validation passed 51 tests. The full suite passed
  3078 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, YAML and JSON parsing, deterministic repo-map regeneration, `git diff
  --check`, added-line privacy and Unicode/control scans, and isolated sdist/
  wheel build passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Fifth-Review Benchmark Routing Remediation

- Exact-head Codex review of `e5d72c2` completed with one P2: invalid primary
  factor-matched and secondary SPY comparisons had no unique route through the
  deterministic final-state tree.
- Made any required primary factor-matched comparison gap a campaign hard-
  validity failure and therefore `INVALID_DIAGNOSTIC`. Interval omission,
  filling, and false-economic-predicate treatment are forbidden.
- Kept a SPY-only comparison gap descriptive with no final-state effect while
  retaining its invalid output and missing-date count as required evidence.
- Added separate final-state fixtures for matched-universe and SPY gaps and
  reconciled the protocol, preregistration, handoff, decision log, changelog,
  and troubleshooting record.
- Focused project-structure validation passed 50 tests. The full suite passed
  3077 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, YAML and JSON parsing, deterministic repo-map regeneration, `git diff
  --check`, added-line privacy and Unicode/control scans, and isolated sdist/
  wheel build passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Fourth-Review And Persistent-Wait Remediation

- Exact-head Codex review of `6a7445f` completed with two new P2 findings:
  factor turnover lacked an exact predecessor after an outcome-invalid middle
  month, and the handoff still described the third-round commit/push as
  pending.
- Froze factor turnover to the immediately preceding scheduled frozen
  decision-time target regardless of later outcome validity. The outcome-
  invalid flag remains separate and cannot skip the predecessor back to the
  last outcome-valid month.
- Added a three-month mutation oracle whose middle target later becomes
  outcome-invalid. The required immediate-target path retains turnover 2.0;
  the forbidden last-outcome-valid path would report 0.0.
- Corrected the handoff to record committed/pushed/CI-passed head `6a7445f`
  and identify current-head CI plus review as the actual remaining gate.
- Replaced the review-monitor exhaustion rule with the owner's latest terminal
  condition: keep the task active through current-head review and every safe
  remediation until no actionable finding remains. The four-run critical
  owner-decision wait remains unchanged.
- Focused project-structure validation passed 49 tests. The full suite passed
  3076 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, YAML and JSON parsing, deterministic repo-map regeneration, `git diff
  --check`, added-line privacy and Unicode/control scans, and isolated sdist/
  wheel build passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-31 - PR 177 Third-Review Protocol Remediation

- Deleted the prior bounded PR review monitor as soon as the new findings were
  confirmed. The former temporary worktree had disappeared while its Git
  metadata remained prunable, so a fresh isolated worktree was recreated at
  `4d832c7` without editing or cleaning the stale dirty root checkout.
- Thread-aware GitHub inspection confirmed two new current P2 findings: the
  bundle inventory was not bound to the frozen 14-trial JSON, and final-state
  robustness did not freeze its Rank IC sample or year denominator.
- Added an exact byte/hash/semantic relation from bundle
  `trial_inventory.json` to the committed frozen inventory. A mutation oracle
  changes one cost field and proves the detached hash no longer matches.
- Froze final-state yearly and leave-one-year-out Rank IC robustness to the
  primary common complete-case monthly table. Required years are derived from
  the outcome-independent bounded evaluation schedule, grouped by signal year,
  all remain in the yearly fraction denominator, and are each omitted exactly
  once. Missing-year, exact-zero, and empty-after-omission cases fail
  robustness.
- Added a discriminating fixture where common-case robustness produces
  `POSITIVE_DIAGNOSTIC` while the forbidden factor-all-valid sample would
  produce `MIXED_DIAGNOSTIC`.
- Focused project-structure validation passed 48 tests. The full suite passed
  3075 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, YAML and JSON parsing, deterministic repo-map regeneration, `git diff
  --check`, added-line privacy and Unicode/control scans, and isolated sdist/
  wheel build passed.
- No vendor API, credential, private row, performance value, purchase, review-
  thread reply/resolution, merge, brokerage, paper, or live behavior was
  accessed or performed.

## 2026-07-29 - PR 177 Second-Review And Bounded-Wait Remediation

- Thread-aware GitHub inspection at `97425c0` confirmed three new current P2
  findings: `LOW_VOL_3M` used a Python half-open slice with only 62 returns;
  the strategy did not enumerate which invalid rebalances create a zero target;
  and the private evidence bundle required an unbound JSON preregistration
  instead of the exact frozen YAML bytes.
- Updated the protocol and machine-readable preregistration to use
  `[t-62:t+1]`, exactly 63 one-day returns ending at `t` from 64 price anchors.
- Limited zero-target construction to three decision-time states: fewer than
  100 eligible securities, fewer than 10 distinct finite factor values, or
  duplicate canonical listing-key bytes. Later missing outcomes for unselected
  securities may invalidate the factor-month or comparison but cannot mutate
  the frozen strategy target, create a liquidation, or change the cash path.
  Missing selected execution or held-return values invalidate the strategy
  trial without rewriting its target to zero.
- Replaced `preregistration.json` in the required bundle children with an exact
  byte-for-byte `eodhd_sp500_three_factor_diagnostic_v1.yaml` child whose
  SHA-256 must equal the detached protocol-freeze hash.
- Added deterministic off-by-one, decision-time trigger, future-missingness,
  cash-path, and tampered-hash oracles to the project-structure suite.
- Added the owner-directed `AGENTS.md` policy: safe actionable findings inside
  the authorized scope are fixed without a confirmation round; pending Codex
  review uses one five-minute thread schedule capped at eight runs; a critical
  owner decision uses one thirty-minute follow-up capped at four runs.
- Reconciled the controller, roadmap, handoff, decision log, and changelog.
  Draft PR #148 remains untouched but now overlaps `AGENTS.md` and must be
  rebased and compared before future use.
- Focused validation passed 46 project-structure tests. The full suite passed
  3073 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, YAML and trial-inventory parsing, deterministic repo-map regeneration,
  `git diff --check`, privacy and Unicode/control scans, and isolated sdist/
  wheel build passed.
- No vendor API, credential, private row, performance value, purchase, thread
  resolution, merge, brokerage, paper, or live behavior was accessed or
  performed.

## 2026-07-29 - EODHD Diagnostic Campaign Scope Reset

- Verified PR #176 merged at `6386c59` and exact merge-head CI run
  `30492542975` succeeded. The root checkout was stale and had 43 modified or
  untracked entries, so it was not switched, reset, cleaned, or used for PR 1.
  Work was isolated in a temporary linked worktree on
  `codex/eodhd-diagnostic-scope-reset` from exact `origin/main`.
- The clean protected-main baseline passed 3064 tests with two
  platform-conditional skips and compiled `src`, `tests`, `research`, and
  `lean`.
- Seven bounded read-only audits covered repository/PR state, EODHD
  license/entitlement, constituent and delisted coverage, field adjustment
  semantics, protected-main code capability, minimum statistical design, and
  adversarial survivorship/identity/publication risk. No credential, vendor
  API, private market-data row, expanded-data performance value, or purchase
  was accessed.
- The supplied owner prompt hashed to
  `deff30a98216f2e7fd3ea02a38fbaac263606d6d74f9838b529ab45010451959`;
  the supplied draft preregistration hashed to
  `830c125be53b31be2683af954ae333093765373f6f668b5ef3856d34d434a197`.
  The repository protocol records the reviewed corrections rather than
  pretending the draft placeholders were already frozen.
- Added the canonical Track A/Track B campaign contract, machine-readable
  preregistration, and exact 14-trial JSON inventory. The protocol freezes the
  three factors, higher-is-better directions, monthly after-close/next-close
  timing, execution-anchored common-calendar 21-return endpoint with
  signal-axis 22-row purge, continuous monthly-rebalanced strategy paths, zero
  embargo, 0/10/25-bps undivided-turnover costs, deterministic random-baseline
  seed derivation, exact common-complete-case six-month moving-block bootstrap,
  one-sided Holm family, diagnostic metrics, and allowed final states.
- Replaced the preregistration's open research-choice placeholders with exact
  values. Cutoff/data/calendar identity move to a blinded dataset-acceptance
  record; code/config/environment are linked after the runner merges in a
  detached pre-run binding. The protocol uses a detached hash and does not try
  to hash itself.
- Reconciled the roadmap, handoff, specification, and controller so R1I is
  complete, the 37-event work is optional `full_ledger_profile_v1`, Track A is
  unblocked without the formal runtime, and Track B becomes the bounded
  post-Track-A priority.
- Final validation passed 3065 tests with two platform-conditional skips, the
  38-test project-structure suite, Ruff, compilation, the Skill audit,
  standard-library YAML parsing, the exact 14-trial JSON inventory check,
  deterministic repo-map regeneration, diff checks, and added-content privacy
  and hidden-Unicode scans.
- An independent adversarial review identified and prompted correction of the
  execution-anchored label/purge boundary, the continuous strategy-return
  contract, bootstrap specification, deterministic baseline outputs, and
  license-gated public projection. The final read-only rereview found no
  actionable P1 or P2 issue.
- The later GitHub final review of PR #177 at `3df9a21` found two P1 and two P2
  issues that the local rereview missed: future-conditioned eligibility,
  subjective final-state assignment, unspecified listing-key bytes, and
  ambiguous cost composition. The remediation freezes a decision-time-only
  universe and mutation invariance, exact byte encoding with golden fixtures,
  all-in costs with hand-calculated fixtures, and an exhaustive ordered
  classification oracle covering every allowed state and boundary.
- Review-fix validation passed 42 focused project-structure tests and the full
  3069-test suite with two platform-conditional skips, plus Ruff, compilation,
  standard-library YAML parsing, exact 14-trial JSON validation, the Skill
  audit, deterministic repo-map regeneration, package sdist/wheel build,
  diff checks, and added-line privacy and Unicode/control scans.
- This change adds no data acquisition, factor calculation, strategy runtime,
  performance output, formal evidence, brokerage, order, paper, or live
  behavior.

## 2026-07-29 - Stage 4B-R1I Attempt Start Schema

- Started from protected `main` merge `b42b911` (PR #174) in the isolated
  `codex/ledger-attempt-start-schema` worktree. Exact merge-head CI run
  `30489691309` succeeded. The clean startup baseline passed 2838 tests with
  two platform-conditional skips, Ruff, compilation, exact-base status, and
  immutable R0-R7 hash inspection.
- A read-only dependency/risk graph over all 27 incomplete events selected
  `ATTEMPT_STARTED` as the unique smallest strict compute-path successor.
  Campaign amendment remains optional, protected-access intent remains an
  independent higher-risk capability root, and terminal/artifact/closure
  events remain downstream. The owner selected bundle `R1I-A`.
- Added a design-first R1I contract, an independent positive start fixture,
  and a separate immutable registry `0.9.0` artifact/digest under unchanged
  schema-language `0.2.0`. R1I promotes only `ATTEMPT_STARTED`, preserves
  R0-R7, and leaves the other 26 events
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- The event binds exact attempt/trial/campaign/allocation identity, a complete
  external readiness record, separate current start authority, and one
  ledger-owned `cap_<32 lowercase hex>` one-shot execution-capability identity
  with complete private external record. Stateful rules require role
  independence, durable append plus atomic capability mint, exact lost-ack
  replay, exactly one start, and one successful atomic consumption before any
  executor begins.
- Added literal release, payload, namespace, scope, source, readiness,
  authority, capability, duplicate/unknown/private-field, incomplete-event,
  and unpublished-promotion oracles. Initial R1I-focused validation passed 225
  tests.
- This release adds no resolver, authority/currentness/capability service,
  append/storage backend, executor, terminal/artifact/access event, private
  data, research attempt, brokerage, order, paper, or live behavior.
- Final focused R0/R1/R1C/R1D/R1E/R1F/R1G/R1H/R1I registry and structure
  validation passed 2229 tests. The full suite passed 3064 tests with two
  platform-conditional wide-`longdouble` skips. Ruff, compileall for
  `src`/`tests`/`research`/`lean`, deterministic repo-map regeneration, and
  the Skill audit passed.
- No-isolation source/sdist/wheel validation reproduced byte-identical R0
  through R8 package resources and identical R1I digest,
  supported/incomplete partitions, default-R0 selection, and conformance
  outcomes. No dependency was installed or added. The check reused
  `build==1.5.0`, `setuptools==83.0.0`, `wheel==0.47.0`, and
  `packaging==26.2` from the existing project environment at
  `/Users/rhapsoul/Documents/Codex/projects/equity-factor-research/.venv`;
  its purpose was package-resource parity, and it changed no dependency file
  or persistent environment. Build metadata and artifacts remained in an
  external temporary copy that was removed after validation.
- JSON parsing, exact immutable prior-release hashes, exact bounded v8-to-v9
  succession, privacy/credential, added-line hidden-Unicode/control-character,
  cleanup, and diff gates passed. Generated compile caches were removed. A
  self-adversarial read-only review corrected one ambiguous sentence so the
  contract now states the required allocation-then-validation-then-start
  ordering explicitly; it found no remaining actionable P1/P2 issue.
- Before final exact-head gates, protected `main` advanced to `26bc9a8` through
  one independent README-only change. The R1I branch rebased cleanly onto that
  exact protected base; no R1I file overlapped the intervening change.
- Post-rebase validation re-passed 2229 focused tests and the full 3064-test
  suite with the same two platform skips, plus Ruff, compileall, deterministic
  repo-map, Skill audit, added-line Unicode/control, cleanup, and diff checks.
  The rebased `src` tree and `pyproject.toml` object IDs remained exactly
  `e3308a5` and `044f02b`, identical to the already package-validated R1I head,
  so the no-isolation source/sdist/wheel evidence was not invalidated or
  needlessly rebuilt.

## 2026-07-29 - Stage 4B-R1H Attempt Allocation Schema

- Started from protected `main` merge `520ed65` (PR #173) in the isolated
  `codex/ledger-attempt-allocation-schema` worktree. Exact merge-head CI run
  `30485940985` succeeded. The clean startup baseline passed 2496 tests with
  two platform-conditional skips, Ruff, compilation, exact-base status, and
  immutable R0-R6 hash inspection.
- A read-only dependency/risk graph over all 28 incomplete events selected
  `ATTEMPT_ALLOCATED` as the smallest strict prerequisite before attempt
  start, protected access, terminal evidence, and artifact disposition. The
  owner selected bundle `R1H-A`.
- Added a design-first R1H contract, independent first-attempt and retry
  fixtures, and a separate immutable registry `0.8.0` artifact/digest under
  unchanged schema-language `0.2.0`. R1H promotes only
  `ATTEMPT_ALLOCATED`, preserves R0-R6, and leaves the other 27 events
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- The event uses exact attempt identity and singleton campaign scope; binds
  earlier trial allocation and initial inventory seal; pins a complete
  external attempt plan, independent acceptance, current allocation-actor
  authority, and expected-output digest; and uses closed first/retry branches
  with policy-bounded monotonic ordinals.
- Added literal release, payload, namespace, scope, source, authority,
  acceptance, relation, ordinal, duplicate/unknown-field, incomplete-event,
  and unpublished-promotion oracles. Initial focused R1H validation passed
  341 tests after advancing the older R1 compatibility test to accept
  published `0.8.0` while retaining rejection of unknown future `0.9.0`.
- This release adds no resolver, authority/currentness runtime, append/storage
  backend, attempt start/execution, protected access, artifact production,
  private data, research trial, brokerage, order, paper, or live behavior.
- Final focused R0/R1/R1C/R1D/R1E/R1F/R1G/R1H registry and structure
  validation passed 2003 tests. The full suite passed 2838 tests with two
  platform-conditional wide-`longdouble` skips. Ruff, compileall for
  `src`/`tests`/`research`/`lean`, deterministic repo-map regeneration, and
  the Skill audit passed.
- No-isolation source/sdist/wheel validation reproduced byte-identical R0
  through R7 package resources and identical R1H digest, supported/incomplete
  partitions, default-R0 selection, and conformance outcomes. No dependency
  was installed or added. The check reused `build==1.5.0`,
  `setuptools==83.0.0`, `wheel==0.47.0`, and `packaging==26.2` from the
  existing project environment at
  `/Users/rhapsoul/Documents/Codex/projects/equity-factor-research/.venv`;
  its purpose was package-resource parity, and it changed no dependency file
  or persistent environment. Build metadata and artifacts remained in an
  external temporary copy.
- JSON parsing, exact immutable prior-release hashes, exact bounded v7-to-v8
  succession, privacy/credential, hidden-Unicode/control-character, cleanup,
  and diff gates passed. Generated compile caches were removed. A
  self-adversarial read-only review corrected one stale handoff claim that
  still called completed local gates pending and one roadmap list-grammar
  defect; it found no remaining actionable P1/P2 issue.

## 2026-07-29 - Stage 4B-R1G Initial Campaign Inventory Seal Schema

- Started from protected `main` merge `d9ac67e` (PR #172) in the isolated
  `codex/ledger-campaign-inventory-seal-schema` worktree. Exact merge-head CI
  run `30482706983` succeeded. The clean startup baseline passed 2198 tests
  with two platform-conditional skips, Ruff, compilation, exact-base status,
  and immutable R0-R5 hash inspection.
- A read-only dependency/risk graph over all 29 incomplete events selected
  `CAMPAIGN_INVENTORY_SEALED` as the unique smallest prerequisite after trial
  allocation and before attempt allocation or protected-access intent. The
  owner selected bundle `R1G-A`.
- Added a design-first R1G contract, independent standard-count and
  maximum-count fixtures, and a separate immutable registry `0.7.0`
  artifact/digest under unchanged schema-language `0.2.0`. R1G promotes only
  `CAMPAIGN_INVENTORY_SEALED`, preserves R0-R5, and leaves the other 28 events
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- The event pins exact campaign allocation, a complete external canonical
  inventory record, separate independent acceptance, seal-actor authority,
  singleton scope, a 4096-trial schema/review bound, and the exact
  nonrecursive pre-seal head. Local constraints enforce campaign membership,
  nested ledger equality, and previous-hash equality; all-and-only
  completeness, retrieval, role independence, currentness,
  predecessor/sequence truth, unique seal, and atomic append remain stateful
  fail-closed requirements.
- Added literal release, payload, campaign/scope, authority, acceptance,
  count, pre-seal, duplicate/unknown-field, incomplete-event, and
  unpublished-promotion oracles. Initial focused registry validation passed
  after advancing the older R1 compatibility test from published `0.6.0` to
  published `0.7.0` while retaining rejection of unknown future `0.8.0`.
- This release adds no resolver, authority/currentness runtime, append/storage
  backend, campaign seal operation, trial execution, attempt, protected
  access, private data, brokerage, order, paper, or live behavior.
- Final focused R0/R1/R1C/R1D/R1E/R1F/R1G registry and structure validation
  passed 1661 tests. The full suite passed 2496 tests with two
  platform-conditional wide-`longdouble` skips. Ruff, compileall for
  `src`/`tests`/`research`/`lean`, whitespace validation, deterministic
  repo-map regeneration, and the Skill audit passed.
- No-isolation source/sdist/wheel validation reproduced byte-identical R0
  through R6 package resources and identical R1G digest, supported/incomplete
  partitions, and conformance outcomes. No dependency was installed or added.
  The check reused `build==1.5.0`, `setuptools==83.0.0`, `wheel==0.47.0`, and
  `packaging==26.2` from the existing project environment at
  `/Users/rhapsoul/Documents/Codex/projects/equity-factor-research/.venv`;
  its purpose was package-resource parity, and it changed no dependency file
  or persistent environment. Generated egg-info was removed and temporary
  package artifacts remained outside the repository.
- JSON parsing, exact immutable prior-release hashes, exact bounded
  v6-to-v7 succession, privacy/path/hidden-Unicode/control-character,
  cleanup, and diff gates passed. Self-adversarial read-only review corrected
  two documentation-currentness mismatches, documented the closed-enum
  encoding of the finite count bound, and found no remaining actionable P1/P2
  issue.

## 2026-07-29 - Stage 4B-R1F Semantic Trial Allocation Schema

- Started from protected `main` merge `814bf02` (PR #171) in the isolated
  `codex/ledger-trial-allocation-schema` worktree. Exact merge-head CI run
  `30478870434` succeeded. The clean startup baseline passed 1760 tests with
  two platform-conditional skips, Ruff, compilation, exact-base status, and
  immutable R0/R1/R2/R3/R4 hash checks.
- The owner selected bundle `R1F-A`, freezing
  `trl_<32 lowercase hex>`, singleton campaign scope, exact earlier
  campaign/experiment/family/sample evidence, a complete canonical external
  trial definition with separate acceptance/publication/actor-authority
  records, closed relation and code-identity unions, and fail-closed
  parent/currentness/independence/uniqueness/order rules.
- Added a design-first R1F contract, independent clean-original and
  dirty-rerun fixtures, literal child/clone cases, and a separate immutable
  registry `0.6.0` artifact/digest under unchanged schema-language `0.2.0`.
  R1F promotes only `TRIAL_ALLOCATED`, preserves R0/R1/R2/R3/R4, and leaves
  the other 29 events `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Added literal release, payload, namespace, scope, parent, definition,
  acceptance, projection, authority, relation, code-identity,
  duplicate/unknown-field, incomplete-event, and unpublished-promotion
  oracles. The initial focused R1F/R1 registry run passed 525 tests before
  canonical-document structure tests were added.
- This release adds no resolver, authority/currentness runtime, append/storage
  backend, private data, research trial, execution attempt, protected access,
  brokerage, order, paper, or live behavior.
- Final focused R0/R1/R1C/R1D/R1E/R1F registry and structure validation passed
  1363 tests. The full suite passed 2198 tests with two
  platform-conditional wide-`longdouble` skips. Ruff, compileall for
  `src`/`tests`/`research`/`lean`, and whitespace validation passed.
- No-isolation source/sdist/wheel validation reproduced byte-identical R0,
  R1, R2, R3, R4, and R5 package resources and identical registry digests,
  supported sets, and conformance outcomes. No dependency was installed or
  added. The check reused `build==1.5.0`, `setuptools==83.0.0`,
  `wheel==0.47.0`, and `packaging==26.2` from the existing project
  environment at
  `/Users/rhapsoul/Documents/Codex/projects/equity-factor-research/.venv`;
  its purpose was package-resource parity, and it changed no dependency file
  or persistent environment. Generated egg-info was removed and temporary
  package artifacts remained outside the repository.
- Deterministic repo-map regeneration, Skill audit, JSON parsing, immutable
  prior-release hashes, exact bounded v5-to-v6 succession,
  privacy/path/hidden-Unicode/control-character, cleanup, and diff gates
  passed. A self-adversarial read-only review separated shape-valid
  self-source syntax from the mandatory stateful pre-append rejection and
  found no remaining actionable P1/P2 issue.

## 2026-07-29 - Stage 4B-R1E Binding Schemas

- Started from protected `main` merge `8d02e5a` (PR #170) in the isolated
  `codex/ledger-campaign-entity-stage3-reference-bindings` worktree. Exact
  merge-head CI run `30475306672` succeeded. The clean startup baseline passed
  1404 tests with two platform-conditional skips, Ruff, compilation,
  exact-base status, and immutable R0/R1/R2/R3 hash checks.
- The owner selected bundle `R1E-A`, freezing closed trial-family/sample and
  local-registration/external-reference campaign-binding branches, singleton
  campaign scope, exact source event ID/hash, one campaign-scoped external
  Stage 3 sample-origin event, stable cross-campaign external sample identity,
  and fail-closed prior-allocation/source/currentness/path/anti-reset rules.
- Added a design-first R1E contract, four independent positive fixtures, and a
  separate immutable registry `0.5.0` artifact/digest under unchanged
  schema-language `0.2.0`. R1E promotes only `CAMPAIGN_ENTITY_BOUND` and
  `STAGE3_SAMPLE_REFERENCE_BOUND`, preserves R0/R1/R2/R3, and leaves the other
  30 events `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Added literal release, outer/nested-union, field, namespace,
  singleton-scope, source-reference, authority, acceptance, privacy,
  duplicate/unknown-field, incomplete-event, and unpublished-promotion
  oracles. The initial focused R1E registry run passed 336 tests before
  canonical-document structure tests were added.
- This release adds no source resolver, external retrieval,
  authority/currentness runtime, append/storage backend, private data,
  research trial, protected access, brokerage, order, paper, or live behavior.
- Final focused registry/structure validation passed 925 tests. The full suite
  passed 1760 tests with two platform-conditional wide-`longdouble` skips.
  Ruff and compileall for `src`/`tests`/`research`/`lean` passed.
- No-isolation source/sdist/wheel validation reproduced byte-identical R0, R1,
  R2, R3, and R4 package resources and identical `0.5.0` conformance
  outcomes. No dependency was installed or added. The check reused
  `build==1.5.0`, `setuptools==83.0.0`, `wheel==0.47.0`, and
  `packaging==26.2` from the existing project environment at
  `/Users/rhapsoul/Documents/Codex/projects/equity-factor-research/.venv`;
  its purpose was package-resource parity, and it changed no dependency file
  or persistent environment. Generated egg-info was removed and temporary
  package artifacts remained outside the repository.
- Deterministic repo-map regeneration, Skill audit, JSON parsing, immutable
  prior-release hashes, v4-to-v5 mechanical succession, privacy/path,
  hidden-Unicode/control-character, cleanup, and diff gates passed. A final
  self-adversarial read-only review tightened literal duplicate-envelope
  killing evidence and found no remaining actionable P1/P2 issue. It verified
  that the v4-to-v5 registry delta is limited to release metadata, two closed
  event schemas, and five conformance vectors; that the Stage 3 tuple and
  binding envelopes exactly inherit R1D; and that no runtime, private-data, or
  research behavior entered the release.

## 2026-07-29 - Stage 4B-R1D Local Sample Registration Schema

- Started from protected `main` merge `68a4c4f` (PR #169) in the isolated
  `codex/ledger-sample-registration-schema` worktree. Exact merge-head CI run
  `30471505290` succeeded. The clean startup baseline passed 1171 tests with
  two platform-conditional skips, Ruff, compilation, exact base/status, and
  immutable R0/R1/R2 hash checks.
- The owner selected bundle `R1D-A`, freezing
  `smp_<32 lowercase hex>`, exact external Stage 3 sample-record authority,
  separate acceptance and publication approval, reviewer independence,
  mutually exclusive local/global/external paths, stable lineage identity,
  monotonic single-current generations, anti-reset/overlap rules, private
  complete records, allowlisted public projections, and the shared
  32-campaign direct-scope maximum.
- Added a design-first R1D contract and separate immutable registry `0.4.0`
  artifact/digest under unchanged schema-language `0.2.0`. R1D promotes only
  `SAMPLE_REGISTERED`, preserves R0/R1/R2, and leaves the other 32 events
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Added independent global/direct fixtures and literal release, payload,
  namespace, scope, public-ID, version/generation, digest, authority,
  acceptance, privacy, duplicate/unknown-field, incomplete-event, and
  unpublished-promotion oracles. The initial focused R1D registry run passed
  232 tests before canonical-document structure tests were added.
- Final focused R0/R1/R1C/R1D registry and structure validation passed 569
  tests. The full suite passed 1404 tests with two platform-conditional
  wide-`longdouble` skips. Ruff and compileall for
  `src`/`tests`/`research`/`lean` passed.
- No-isolation source/sdist/wheel validation reproduced byte-identical R0, R1,
  R2, and R3 package resources and identical `0.4.0` conformance outcomes.
  No dependency was installed or added. The check reused
  `build==1.5.0`, `setuptools==83.0.0`, `wheel==0.47.0`, and
  `packaging==26.2` from the existing project environment at
  `/Users/rhapsoul/Documents/Codex/projects/equity-factor-research/.venv`;
  its purpose was package-resource parity, and it changed no dependency file
  or persistent environment. Generated egg-info and temporary package
  artifacts were removed or kept outside the repository.
- Deterministic repo-map regeneration, Skill audit, JSON parsing, immutable
  registry hashes, privacy/path, hidden-Unicode/control-character, cleanup,
  and diff gates passed. A final self-adversarial read-only review verified
  that the v3-to-v4 registry delta is limited to release metadata, `sample_id`,
  `SAMPLE_REGISTERED`, and its vectors; it found no actionable P1/P2.
- This release adds no external retrieval, acceptance/publication-currentness
  runtime, binding event, append/storage backend, private data, research trial,
  protected access, brokerage, order, paper, or live behavior. Final full,
  package, privacy, and review evidence is recorded above without claiming
  external authority enforcement or formal sample use.

## 2026-07-28 - Stage 4B-R1C Trial-Family Registration Schema

- Started from protected `main` merge `a6f7d43` (PR #167) in the isolated
  `codex/ledger-trial-family-registration-schema` worktree. Exact merge-head CI
  run `30424903896` succeeded. The clean startup baseline passed 1002 tests
  with two platform-conditional skips, Ruff, compilation, exact base/status,
  and immutable R0/R1 hash checks.
- While the first R1C head was being published, independent thin-router PR
  #168 advanced protected `main` to `4ac5adb`. R1C overlapped only the generated
  repo map, its generator, and structure tests. The R1C commit was normally
  rebased without conflict, both scopes were verified present, the repo map was
  regenerated, and every local gate was rerun before the remote head update.
- The owner selected bundle `R1C-A`, freezing
  `fam_<32 lowercase hex>`, an exact retrievable external family-definition
  authority tuple, separate acceptance with reviewer independence, stable
  global family identity, monotonic current generations, anti-reset rules,
  closed `supersedes`/`depends_on` relations, and a common direct-scope maximum
  of 32.
- Added a design-first R1C contract and a separate immutable registry `0.3.0`
  artifact/digest under unchanged schema-language `0.2.0`. R1C promotes only
  `TRIAL_FAMILY_REGISTERED`, preserving R0/R1 and leaving the other 33 events
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Added independent global/direct fixtures and literal release, payload,
  namespace, scope, public-ID, version/generation, digest, literal-version,
  duplicate/unknown-field, incomplete-event, and unpublished-promotion
  oracles. The final rebased focused registry/structure run passed 336 tests.
- Final rebased full validation passed 1171 tests with two platform-conditional
  wide-`longdouble` skips, plus Ruff and compileall for
  `src`/`tests`/`research`/`lean`.
- No-isolation source/sdist/wheel validation reproduced byte-identical R0, R1,
  and R2 package resources and identical conformance outcomes. No dependency
  was installed or added. The check reused `build==1.5.0`,
  `setuptools==83.0.0`, `wheel==0.47.0`, and `packaging==26.2` from the
  existing project environment at
  `/Users/rhapsoul/Documents/Codex/projects/equity-factor-research/.venv`;
  its purpose was package-resource parity, and it changed no dependency file or
  persistent environment. Generated egg-info and temporary package artifacts
  were removed.
- This release adds no external retrieval, acceptance/currentness runtime,
  append/storage backend, private data, research trial, protected access,
  brokerage, order, paper, or live behavior. Final privacy/determinism/review
  evidence will be appended only after those gates have actually completed.
- Self-adversarial review caught one methodology drift before commit: the draft
  had strengthened strictly monotonic acceptance generations to mandatory
  `+1` steps while weakening exactly-one-current to at-most-one-current. The
  contract, decision log, handoff, and literal oracle were corrected to the
  owner-selected rule: strictly increasing generations and exactly one current
  accepted generation for registration and later formal use.
- The same review removed two further unauthorized extrapolations: the direct
  campaign-scope maximum 32 is not reused as a `depends_on` graph bound, whose
  finite maximum belongs to the digest-pinned external authority schema; and
  currentness uses the selected explicit supersession rule without inventing a
  separate revocation mechanism.

## 2026-07-28 - Stage 4B-R1B Campaign/Experiment Allocation Schemas

- Started from protected `main` merge `9cf5325` (PR #166) in the isolated
  `codex/ledger-campaign-experiment-allocation-schemas` worktree. Exact
  merge-head CI run `30377401789` succeeded. The clean startup baseline passed
  913 tests with two platform-conditional skips, Ruff, compilation, and exact
  base/status checks.
- The owner selected namespace option `E1`, making
  `exp_<32 lowercase hex>` the sole authority for `experiment_id` syntax.
  Existing helpers, narrative examples, and rejected fixtures were not used as
  authority.
- Added a separate immutable registry `0.2.0` artifact and digest while
  retaining the R0 JSON, sidecar, default loader, canonical digest, and
  validation behavior. Explicit release selection is required for R1.
- R1 supports exactly `LEDGER_EPOCH_CREATED`, reservation-only
  `CAMPAIGN_ALLOCATED`, and reservation-only `EXPERIMENT_ALLOCATED`; the other
  34 event types remain `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Added the closed schema-language `0.2.0` implementations for
  `tagged_union`, `array_contains_path`, and `safe_public_id`. Independent
  fixtures and literal tests cover both promoted schemas, namespace and scope
  attacks, missing/unknown/null/type failures, duplicate raw properties,
  arbitrary unpublished promotion, union branches, public-ID boundaries, and
  path/schema compatibility.
- Final exact-head review found one P2 malformed-registry recursion path. The
  fix propagates visited named-type state through every constraint-path schema
  wrapper/branch and adds an exact nullable-cycle regression oracle.
- Post-fix validation passed 167 focused registry/structure tests and 1002 full
  tests with two platform-conditional skips, plus Ruff, compilation,
  deterministic repo-map, Skill audit, source/sdist/wheel R0/R1 package
  parity, privacy/Unicode/control-character, cleanup, and diff gates.
- No dependency was installed or added. The no-isolation package build reused
  `build==1.5.0`, `setuptools==83.0.0`, `wheel==0.47.0`, and
  `packaging==26.2` from the existing project environment at
  `/Users/rhapsoul/Documents/Codex/projects/equity-factor-research/.venv`.
  Their purpose was package-resource parity validation; they changed no
  dependency declaration or tracked repository file. Generated ignored
  egg-info metadata was removed after validation.
- No private data, research result, campaign, trial, attempt, protected access,
  append/storage runtime, brokerage, order, paper, or live behavior was
  introduced.

## 2026-07-28 - Stage 4B-R1A Allocation/Registration Architecture

- Started from protected `main` merge `4c874eb` (PR #165) in the isolated
  `codex/ledger-allocation-registration-schemas` worktree. The clean starting
  baseline had 912 passing tests and two platform-conditional skips; Ruff,
  compilation, and exact merge-head GitHub CI were successful.
- Six non-overlapping read-only audits covered campaign/experiment allocation,
  family/sample registration, binding and external references, schema-language
  evolution, independent vectors, and adversarial evidence/privacy risks. They
  made no edits, installed no dependency, accessed no private data, and ran no
  research or GitHub mutation.
- The audits agreed that none of the six events could be promoted safely from
  narrative fields or non-append test helpers. The owner selected architecture
  A: immutable R0 plus a separately versioned minimal R1 path.
- Added a design-only R1A contract that retains the 37-event vocabulary,
  freezes reservation-only campaign/experiment allocation, entity subjects,
  explicit campaign scope, prior allocation for every shared direct-scope
  campaign, closed schema-language additions, and future family-definition
  and Stage 3 sample reference-authority requirements. No concrete family or
  Stage 3 sample authority is accepted.
- R1A intentionally does not modify packaged registry JSON, digest sidecars, or
  validator code. Epoch remains the sole supported event; the other 36 remain
  fail-closed. Trial, attempt, protected-access, dependency, backend,
  private-data, and trading impacts remain zero.
- Three independent post-edit reviews initially found no P1 implementation
  defect but identified incomplete byte guards, under-specified registry
  succession and DSL evidence, overstated authority completion, and two
  owner-choice leaks: unaccepted non-campaign ID prefixes and an unselected
  family-review architecture. The integration owner pinned raw R0 bytes and
  exact tables/lists, made every registry release immutable, required complete
  DSL `0.2.0` meta-tests, deferred the owner choices, and clarified Stage 3
  decision currentness at trial, attempt, and access boundaries. All three
  read-only re-reviews then reported zero actionable P1/P2.
- Final validation passed 78 focused structure/R0-registry tests and the full
  913-test suite with two platform-conditional skips. Ruff, compilation,
  deterministic repo-map generation, Skill audit, raw/package resource
  parity, Unicode/privacy, cleanup, and diff checks passed.
- The no-isolation sdist/wheel build reused, without installing,
  `build==1.5.0`, `setuptools==83.0.0`, `wheel==0.47.0`, and
  `packaging==26.2` from
  `/Users/rhapsoul/Documents/Codex/projects/equity-factor-research/.venv`.
  Both artifacts reproduced raw R0 JSON SHA-256
  `4b78c36647621deaec15114558d827c17dae2bfa29918f4cbf2ceb2aa6b6e6d9`
  and sidecar SHA-256
  `dc870da2958a107998d3939350edb20d3a9185e13a4edb48664befcb89e79d51`.
  Temporary build outputs were removed; no dependency declaration, lock file,
  project environment, or persistent environment changed.

## 2026-07-28 - Stage 4B-R0 Ledger Schema Registry Foundation

- Started from protected `main` merge `27f0497` (PR #164) in the isolated
  `codex/experiment-trial-ledger-schema-registry` worktree. The clean starting
  baseline had 863 passing tests and two platform-conditional skips.
- Six non-overlapping read-only audits covered canonical state, all 37 event
  semantics, registry format/dependencies, deterministic vectors, adversarial
  schema risks, and owner-architecture boundaries. They did not edit files,
  access GitHub/private data, install dependencies, or run research.
- The audits agreed that only the common envelope and
  `LEDGER_EPOCH_CREATED` are exact enough to validate. Promoting synthetic
  checkpoint facts, the rejected trial stub, generic objects, or free strings
  would launder incomplete semantics into false schema coverage.
- Added a separate standard-library `ledger` namespace with a packaged,
  self-contained ASCII canonical JSON registry. Its closed meta-contract
  validates the exact 37-event vocabulary, unique version/event keys, disjoint
  supported/incomplete partitions, schema nodes, type references, local
  constraints, and digest-bound vectors.
- Added duplicate-aware raw JSON parsing before mapping, I-JSON safe-integer
  enforcement, deterministic canonical registry bytes and external SHA-256
  verification, exact epoch validation, and fail-closed rejection of every
  incomplete or unknown event before action.
- The registry remains `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`: epoch is the sole
  `FROZEN_SUPPORTED` event and the other 36 event types are explicitly
  incomplete. No append, storage, lifecycle, access, closure, checkpoint,
  review, promotion, private-data, or trading behavior was added.
- Added a dedicated registry test module with an independent literal
  37-event oracle, fixed digest, reorder/mutation checks, duplicate-key raw
  vectors, meta-contract attacks, non-I-JSON number attacks, and epoch
  missing/unknown/null/type/timing/scope/subject failures. Independent
  post-edit reviewers then identified an unpublished-registry authority
  bypass, an unhandled oversized-integer parser exception, a canonical
  int/string object-key alias, a chronology error, and one confounded
  ledger-ID-prefix test. The integration owner bound event execution to the
  packaged sidecar, made integer/key failures stable, added direct killing
  attacks, corrected the dates, and isolated the ID-prefix mutation.
- Final focused validation passed 49 registry tests and 28 structure tests.
  The full suite passed 912 tests with two platform-conditional skips; Ruff,
  compilation, deterministic repo-map generation, package-resource inspection,
  Unicode/privacy, cleanup, and diff checks passed. Independent security and
  evidence and documentation/package re-reviews reported no remaining
  actionable P1/P2.
- No project dependency was installed or added. Validation reused the existing
  project environment. The final PEP 517 build installed
  `setuptools==83.0.0`, `wheel==0.47.0`, and transitive `packaging==26.2` only
  inside automatically removed `build-env-*` directories under the operating
  system temporary directory; the first sandboxed attempt failed DNS and the
  identical approved-network retry succeeded. No dependency declaration, lock
  file, project environment, or persistent environment changed.

## 2026-07-27 - Experiment And Trial Ledger Contract

- Started from protected `main` merge `a6c147e` (PR #163) in the isolated
  `codex/experiment-trial-ledger-contract` worktree. The clean starting baseline
  had 854 passing tests, two platform-conditional skips, successful
  compilation, and successful exact merge-head GitHub CI.
- Eight non-overlapping read-only audits covered legacy writers/callers,
  identity/lifecycle semantics, storage/atomicity, protected access,
  canonical-document conformance, adversarial program risks, and deterministic
  failure tests. No audit edited files, opened private data or performance
  values, ran a research campaign, or added a dependency.
- The audits agreed that current schema-v1 logs are overwrite-capable
  post-success sidecars, not an append-only all-trial ledger. Failed-before-
  write, abandoned, retried, or overwritten history cannot be proven complete.
- Added a backend-neutral Stage 4a contract that separates semantic trials from
  execution attempts; freezes allocation-before-action, campaign inventory,
  lifecycle, artifact, protected-access, canonical-event, chain/checkpoint,
  review/promotion, and private/public projection semantics; and defines
  deterministic `LEDGER-001` through `LEDGER-015` later-runtime cases.
- Added a tiny synthetic event fixture with exact canonical UTF-8, SHA-256,
  source-key reorder invariance, and identity-mutation vectors. The fixture and
  documentation assertions are contract evidence, not a production serializer
  or append-only implementation.
- Four independent post-edit reviewers found that the first draft
  self-invalidated review decisions through its global-head rule, allowed
  result-informed reseal/promotion, omitted the exact idempotency-request
  preimage, left access capability/classification/public-projection behavior
  ambiguous, and prematurely called the unmerged contract accepted. The
  integration owner, not the reviewers, fixed those findings.
- The revised contract uses a nonrecursive campaign-scoped pre-freeze evidence
  projection plus separately anchored freeze event; forbids same-sample
  result-informed promotion; freezes exact request/event preimages and hashes;
  makes capability consumption plus access-start one atomic pre-open barrier;
  defines an explicit atomic-interval exposure transition graph; and freezes an
  exact safe public projection schema. Final targeted re-reviews from all four
  reviewers reported no remaining actionable P1/P2.
- The first stable-head GitHub review then identified one P2 omitted case:
  complete `SOME` observation under a frozen design-purpose access had no
  deterministic classification absent separately confirmed influence. A
  separate fixer mapped that case directly to `development` and added the
  corresponding `LEDGER-015` conformance assertion; a separate reviewer
  rechecked the narrow fix before the head was republished.
- The fixed-head re-review identified a second P2: the original canonical
  `TRIAL_ALLOCATED` vector incorrectly occupied sequence zero with no parent
  chain. A separate fixer replaced the positive vector with a valid
  sequence-zero `LEDGER_EPOCH_CREATED`, retained the orphan trial as rejection
  evidence, and added test-only exact parent-order checks. A separate reviewer
  independently recomputed the request/event hashes and found no remaining
  actionable P1/P2 in the narrow fix.
- The next current-head review identified two further P2s: the documented
  global-family/sample registration and campaign-binding alternatives did not
  agree on one legal parent order, and the contract claimed exact payload
  schemas for the whole event vocabulary without freezing those schemas. A
  separate fixer made campaign allocation and ledger-global registration
  independent siblings in one exact partial order, defined direct,
  ledger-global-plus-binding, and accepted external Stage 3 sample-reference
  paths, closed the vocabulary at 37 event types, and narrowed exact Stage 4a
  payload schemas to `LEDGER_EPOCH_CREATED` and `TRIAL_ALLOCATED` plus the
  common identity envelope. Full Stage 4b conformance now requires a separately
  reviewed complete machine-readable payload-schema registry; an incomplete
  prototype remains `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Independent pre-publication re-review then found three documentation-fact
  P2s: mixed path fields were not rejected, tests imposed an undocumented
  registration-before-campaign total order, and direct shared-campaign scope
  was rejected despite the contract allowing it. The separate fixer added
  exact per-path key sets and source bindings, validated both global sibling
  interleavings, and required direct scopes to be sorted, unique, and contain
  the applicable campaign. Compact positive and negative vectors cover mixed
  paths, identities, campaigns, source event IDs/hashes, external references,
  scope membership/order/uniqueness, and both legal interleavings. The
  canonical and integrity reviewers independently reran focused validation and
  reported no remaining actionable P1/P2.
- The next current-head GitHub review found one timestamp P2: the
  documentation-fact validator accepted impossible numeric calendar/time
  ranges while rejecting every normalized nonzero fractional second allowed by
  the inherited `pit_canonical_json_v1` RFC 3339 profile. A separate fixer
  replaced the whole-second regular expression with exact ASCII UTC syntax,
  proleptic-Gregorian month/day and year-zero leap rules, ordinary time ranges,
  normalized arbitrary-precision fractions, and bounded structural
  leap-second handling at UTC June/December month ends. Primary RFC 3339
  verification and independent re-review exposed and closed the initial
  all-leap-second rejection plus year-zero and fractional-leap coverage gaps.
  Positive vectors now include leap day, year `0000`, a known RFC leap second,
  and long fractional precision; negative vectors cover invalid dates/times,
  misplaced leap seconds, zero/trailing-zero fractions, empty fractions, and
  noncanonical offsets. The golden fixture and its canonical bytes/hashes did
  not change, and the independent reviewer reported no remaining actionable
  P1/P2.
- The following current-head review found one P1 and one P2. The P1 showed that
  Stage 4a's supposedly exact `TRIAL_ALLOCATED` payload omitted many immutable
  bindings that the same contract requires, so an accepted event could not
  prove the trial configuration, code, data, environment, sample, timing,
  execution, and policy identity. The P2 showed that "every entity ID is
  globally unique" had been encoded as if a later lifecycle record could not
  reuse the already allocated entity as its subject, contradicting the
  lifecycle and supersession model.
- A separate read-only remediation audit rejected two unsafe shortcuts:
  inventing unreviewed trial fields merely to satisfy the narrative and
  weakening the required trial bindings to match the incomplete fixture. It
  recommended that Stage 4a freeze only the exact epoch payload, retain the
  full trial bindings as normative semantic requirements, and defer their
  field placement/types/nullability/unions/nested schemas to the complete
  Stage 4b registry. It also distinguished one-time logical-entity allocation
  from legal later typed references and from event/operation/sequence
  uniqueness.
- A different fixer applied that narrow remediation. The fixture now labels the
  trial object as `incomplete_trial_allocation_stub` and proves rejection both
  at sequence zero and after repairing sequence/previous-hash fields. The
  documentation validator accepts only the exact epoch event; trial-parent
  alternatives and entity allocation/reference/idempotency checks are
  explicitly non-append semantic facts. Exact operation replay adds no record,
  while second allocation, reference-before-allocation, wrong-type reference,
  changed-request replay, and event/sequence conflicts fail closed. The epoch
  canonical bytes and request/event hashes remain unchanged.
- The first independent post-remediation integrity review found one P2 in the
  documentation-fact helper: it treated input-list order as sufficient proof
  that an entity reference followed allocation, even when the reference's
  authoritative ledger sequence was earlier. A separate non-reviewing fixer
  retained the allocation sequence with the entity type, required every
  reference sequence to be strictly greater, and added a deterministic
  allocation-at-2/reference-at-1 rejection vector. The focused and full suites
  then passed.
- The next exact-head GitHub review found one genesis P1: sequence-zero
  `LEDGER_EPOCH_CREATED` already carried an `actor_id`, but the one-time entity
  allocation wording required every typed reference to follow an in-ledger
  allocation and the closed vocabulary had no prior actor-registration event.
  The golden epoch therefore could not satisfy its own authorization model.
- A separate read-only audit compared external-principal binding, atomic actor
  bootstrap, and a detached bootstrap fact. It selected external-principal
  binding because an actor allocated by its own epoch is circular and a
  detached fact is substitutable unless the epoch preimage binds it. That first
  candidate scoped one-time allocation to ledger-owned entities and attempted
  to bind registry, record, review, authority, scope, and validity evidence.
- Independent review of that first external-principal candidate found that its
  record, decision, reviewer-authority, and producer fields were all supplied
  by the caller and could be replaced together with freshly computed hashes.
  The same review demonstrated that string ordering of normalized RFC 3339
  timestamps misorders whole and fractional seconds, and that a later actor
  could switch to an internally consistent foreign registry or replay a stale
  snapshot. The candidate therefore did not pass current-remediation review.
- A second read-only audit proposed one acyclic, provider-agnostic trust graph:
  principal record -> authorization decision -> owner-pinned authority
  manifest -> producer intent -> trusted-adapter producer context -> operation
  request -> committed event. The manifest digest is fixed outside the request;
  the context binds the authenticated producer to the intent rather than the
  final request, avoiding a context/request hash cycle. Exact temporal checks
  parse arbitrary-precision fractional seconds rather than comparing strings.
  Concrete IdP, signature, key, adapter, rotation, revocation, and storage
  choices remain Stage 4b owner decisions.
- Independent canonical, integrity, and adversarial reviews rejected that
  second candidate. Fully rehashed vectors could admit malformed/private
  nested values, and a validation-time pin could not prove that the owner had
  activated it before the event or had not later revoked it. More
  fundamentally, the exact manifest/context DAG selected a material identity
  architecture while claiming those owner choices were deferred.
- The final narrow resolution retains the only invariant required to close the
  genesis-allocation contradiction: ledger allocation rules apply only to
  ledger-owned logical entities; the epoch atomically introduces `ledger_id`;
  and `actor_id` is external claimed attribution whose syntax is hash-bound but
  neither authenticated nor authorized. Authority-dependent behavior remains
  fail closed until a separately approved Stage 4b mechanism can preserve
  historical activation, replacement, and revocation evidence. The rejected
  trust-DAG candidate was not adopted.
- Independent canonical, integrity, and adversarial reviews found no remaining
  actionable P1/P2 in that narrow resolution. They separately confirmed the
  ledger-owned/external boundary, epoch genesis semantics, exact epoch payload
  rejection, actor grammar and hash sensitivity, unchanged golden hashes,
  absence of an adopted identity architecture, and the fail-closed Stage 4b
  authority gate. Two final wording-only clarifications were re-reviewed after
  they narrowed all remaining allocation/reference language to ledger-owned
  entities.
- Commit `2e65eee` carried that narrow remediation to PR #164. Exact-head
  GitHub CI run `30327521020` completed successfully before the single final
  review request. Review `4793622375` then found two P2s: the inventory seal's
  "current ledger checkpoint" was circular or ambiguous because the only
  defined checkpoint was created at later campaign closure, and the canonical
  handoff/roadmap still called the already completed commit/push steps pending.
- A separate non-reviewing fixer replaced that phrase with a semantic
  `campaign_inventory_preseal_head_v1` anchor. Its ledger ID and immediate
  predecessor sequence/hash are included in the seal request/event preimage;
  the anchor never names the seal itself. At one serialized atomic boundary,
  the implementation must compare the retained head and assign the seal
  sequence/envelope previous hash, so a concurrent winning append conflicts
  rather than silently rebasing. The v1 path forbids an empty-stream anchor,
  and the pre-seal anchor has no independent trust/retention role or checkpoint
  claim.
- The first independent integrity review of that fix found one P2 in its
  documentation-fact model: it did not bind the retained ledger ID or the seal
  envelope's actual previous hash, and it lacked a forward head-drift vector.
  The same separate fixer added typed retained-ledger/head checks, exact
  envelope previous-hash equality, and independent forward-drift, wrong-
  previous-hash, cross-ledger, epoch-empty, sequence/order, and atomicity
  negatives. This remains documentation-contract evidence; runtime
  compare-and-swap, replay, concurrency, and durability proof stay in Stage 4b.
- Integrity and adversarial re-reviews of the completed P2 fix reported no
  remaining actionable P1/P2. The final P2-remediation snapshot passed 22
  focused structure tests and the full 857-test suite with the same two
  platform-conditional wide-`longdouble` skips, Ruff, compilation of `src`,
  `research`, `tests`, and `lean`, sdist and wheel build, the Skill audit,
  three identical repo-map hashes across two regenerations, JSON parsing,
  privacy/path and hidden-Unicode scans, generated-artifact cleanup, and diff
  checks.
- Exact-head review `4793725387` on the later `30bbc82` snapshot found a P1
  because the independently retained checkpoint ended at the evidence freeze:
  closure, review, promotion/disposition, and adjudication remained a
  replaceable or deletable suffix. It also found a P2 because the timestamp
  fact validator accepted structurally plausible but historically unannounced
  leap seconds.
- A separate timestamp fixer narrowed ledger v1 to ordinary UTC seconds
  `00`-`59`, retained proleptic-Gregorian year `0000` and normalized
  arbitrary-precision nonzero fractions, and exercised both event timestamp
  fields. An independent reviewer found and closed one omitted greater-than-
  nanosecond positive vector. The existing epoch fixture and all four canonical
  hashes remained unchanged.
- Two independent checkpoint-design audits selected a separate exact,
  version-linked `campaign_adjudication_checkpoint_v1` rather than changing
  the evidence checkpoint into a phase union or selecting signatures. Any
  later same-campaign event makes the old generation non-current; an external
  monotonic latest/pending-generation authority is a fail-closed Stage 4b owner
  gate because a local old ledger/checkpoint cannot detect an entirely hidden
  successor.
- The first test-only adjudication model was rejected before commit after a
  scope reviewer found a 1,397-line pseudo-runtime and no independent literal
  hash oracle. A compact replacement split chain, schema, terminal binding,
  lineage, and currentness checks into short helpers and table-driven vectors.
  Subsequent independent adversarial reviews found and separate fixers closed:
  historical-generation coordinated rehash/reset, an unknown event used as a
  positive suffix, an opaque rather than recomputed evidence checkpoint, and a
  freeze-to-closure interval that admitted new same-campaign evidence.
- The final contract freezes exact canonical evidence and adjudication
  checkpoint preimages, hard-coded bytes/hashes, all-and-only scoped prefix,
  cutoff/freeze/reference relations, four flat trial/attempt counts with exact
  fixed-set evidence, one-to-one adjudication generations, terminal tail
  anchoring, and pending/currentness semantics. Full event payload/scope/set
  extraction, storage, provider, authorization, signatures, anti-rollback,
  concurrency, and recovery remain fail closed for Stage 4b owner decisions.
  Final independent integrity and scope reviewers reported no actionable
  P1/P2.
- One noncanonical validation attempt used `/opt/homebrew/bin/python3.14`
  (Python 3.14.6) with a Python 3.9 pytest-tool path and failed 33 tests because
  that interpreter had no SciPy. No dependency was installed. The canonical
  project interpreter `.venv/bin/python` (Python 3.12.13, SciPy 1.18.0) then
  passed 863 tests with the same two platform skips.
- Final validation of the evidence/adjudication checkpoint remediation passed
  seven focused contract tests, all 28 structure-contract tests, and the full
  863-test suite with the same two platform-conditional wide-`longdouble`
  skips. Ruff, compilation of `src`, `research`, `tests`, and `lean`, the Skill
  audit, JSON parsing, three identical repo-map hashes across two
  regenerations, privacy/path and hidden-Unicode scans, generated-artifact
  cleanup, and diff checks also passed. The first PEP 517 build attempt failed
  only because the sandbox could not resolve the package index; the identical
  approved-network retry built both artifacts. It installed
  `setuptools==83.0.0`, `wheel==0.47.0`, and `packaging==26.2` only in
  automatically removed disposable `build-env-*` directories under the
  operating-system temporary directory. No project environment, dependency
  declaration, lock file, tracked artifact, trial, or research result changed.
- Exact-head review `4794514495` on `094f00b` then found two test-contract P2s:
  the synthetic retained chain did not require its sole empty-scope epoch at
  sequence zero, and the terminal-bundle check admitted coherently rehashed
  duplicate review or promotion-decision events. A separate fixer required the
  exact genesis invariant and the all-and-only target-campaign
  closure/review/decision/adjudication projection while preserving
  other-campaign and genuinely global interleaving. Coherently rebuilt
  missing, replaced, moved, duplicate, and wrong-scope epoch vectors plus
  duplicate review/decision vectors now fail for those exact invariants. An
  independent integrity reviewer confirmed both fixes and found no actionable
  P1/P2.
- Final validation after those two P2 fixes again passed seven focused contract
  tests, all 28 structure-contract tests, and the full 863-test suite with the
  same two platform skips, plus Ruff, compilation, the Skill audit,
  deterministic repo-map regeneration, JSON, privacy/path, hidden-Unicode,
  artifact-cleanup, and diff gates. The PEP 517 rebuild again used only
  `setuptools==83.0.0`, `wheel==0.47.0`, and `packaging==26.2` in automatically
  removed disposable build environments; it changed no project environment,
  dependency declaration, lock file, tracked artifact, trial, or result.
- Reconciled Stage 3 acceptance and the Stage 4a/4b split in the specification,
  roadmap, handoff, repo-map generator, decision log, changelog, and
  documentation-contract tests. PR #148 remains an independent draft; this
  stage does not edit `AGENTS.md`.
- The physical backend, locking/journaling/recovery policy, private storage
  location, external checkpoint provider, and cross-platform durability claims
  remain explicit Stage 4b decisions.
- The pre-remediation stable-head local validation passed 856 tests with two
  platform-conditional
  wide-`longdouble` skips, Ruff, compilation, sdist/wheel build, the Skill
  audit, deterministic repo-map regeneration, JSON parsing, privacy/Unicode
  checks, and diff checks.
- Validation of the `db323ed` pre-genesis-authority remediation passed 856
  tests with the same two platform-conditional wide-`longdouble` skips, 21
  focused structure tests, Ruff, compilation of `src`, `research`, `tests`,
  and `lean`, sdist and wheel build, the Skill audit, three identical repo-map
  hashes across two regenerations, JSON parsing, privacy/Unicode scans,
  cleanup, and diff checks.
  The default shell still had no `python` command, so validation reused the
  existing isolated interpreter at
  `/Users/rhapsoul/Documents/Codex/projects/equity-factor-research/.venv`;
  nothing was installed into or changed in that environment.
- Final validation of the narrow external-attribution remediation passed 21
  focused structure tests and the full 856-test suite with the same two
  platform-conditional wide-`longdouble` skips, Ruff, compilation of `src`,
  `research`, `tests`, and `lean`, sdist and wheel build, the Skill audit,
  three identical repo-map hashes across two regenerations, JSON parsing,
  privacy/path and hidden-Unicode scans, generated-artifact cleanup, and diff
  checks.
- The PEP 517 builds, including the final P2-remediation rebuild, installed
  `setuptools==83.0.0`, `wheel==0.47.0`, and `packaging==26.2` only inside
  automatically removed disposable build
  environments under
  `/private/var/folders/5r/vgv5b5gs3s91w6gp1mtbgnnc0000gn/T/build-env-*`.
  They were used only to validate the sdist and wheel; no project environment,
  dependency declaration, lock file, or tracked artifact changed. The final
  external-attribution rebuild first failed because the sandbox could not
  resolve the package index; the identical approved-network retry succeeded.
  The temporary failed and successful isolated environments and build outputs
  were removed.
- During the second review fix, one `uv run` invocation unintentionally
  created the ignored worktree environment
  `/private/tmp/equity-factor-research-stage4a-trial-ledger-contract/.venv`
  and an untracked `uv.lock`. The environment contained the local project
  `ai-equity-factor-research==0.1.0` plus `Pygments==2.20.0`, `build==1.5.0`,
  `iniconfig==2.3.0`, `numpy==2.5.1`, `packaging==26.2`, `pandas==3.0.5`,
  `pluggy==1.6.0`, `pyproject_hooks==1.2.0`, `pytest==9.1.1`,
  `python-dateutil==2.9.0.post0`, `ruff==0.16.0`, `scipy==1.18.0`, and
  `six==1.17.0`; it was used only for focused fixture validation. The untracked
  lock and entire environment were removed before commit, so no repository,
  persistent environment, dependency declaration, or lock-file impact
  remains.
- This stage adds no factor, strategy, trial, generated research evidence,
  provider, data access, private artifact, credential, dependency, paper/live
  path, brokerage connection, or order behavior.

## 2026-07-27 - Point-In-Time Data Methodology Contract

- Started from protected `main` merge `8a352d3` (PR #162) in the isolated
  `codex/point-in-time-data-methodology-contract` worktree. The clean starting
  baseline had 849 passing tests, two platform-conditional skips, successful
  compilation, and successful exact merge-head GitHub CI.
- Five non-overlapping read-only audits covered canonical documentation,
  point-in-time universe and corporate actions, field/calendar/benchmark
  semantics, provenance/privacy/holdout exposure, and adversarial contract
  failure modes. No private source file, private performance value, vendor API,
  credential, or holdout result was opened.
- The audits confirmed that current loaders, inventory metadata, and EODHD
  diagnostics support only scope-limited intake and static-cohort diagnostics.
  They do not prove permanent identity, historical membership, delistings,
  corporate actions, field availability or revisions, license entitlement,
  immutable lineage, calendar alignment, or formal benchmark/risk-free
  suitability.
- Added a provider-agnostic Stage 3 contract that separates
  `methodology_contract_accepted`, `dataset_manifest_reviewed`, and
  `formal_interpretation_eligible`; specifies immutable provenance/license,
  canonicalization/environment, non-self-issued dataset review, bitemporal
  identity/universe/field, adjustment, calendar, missingness,
  benchmark/risk-free, privacy, and exposure-ledger records; and freezes
  deterministic `PIT-001` through `PIT-014` documentation cases.
- Classified the previously examined 2025-05-01 through 2026-05-31 interval as
  `historical_evaluation`, never a pristine holdout. Stage 4 owns append-only
  enforcement; Stage 3 does not backfill or claim that enforcement.
- Reconciled the canonical roadmap, handoff, project specification, README,
  readiness audit and Skill, local-CSV checklist/report, legacy experiment
  template, changelog, decision log, and generated repo map. The new contract
  and updated forward-looking templates require private-manifest IDs and
  redacted public logical IDs rather than private absolute paths; legacy
  diagnostic scripts and historical records still require separate path
  hardening.
- Added documentation-contract tests before implementation. The focused suite
  initially failed seven assertions for the intentionally missing contract and
  stale canonical status, then served as the acceptance gate for the docs-only
  implementation.
- Initial independent review found that general `known_at` was absent from the
  usability predicate, outcome-reconstructible raw inputs were absent from
  exposure downgrade rules, dataset review could be self-declared, tracked
  templates could solicit restricted hashes/license evidence/private metrics,
  environment/canonicalization identity was underspecified, and several
  canonical/test assertions were incomplete. The main integration owner fixed
  those findings; the reviewers did not edit their own findings.
- Final canonicalization review found that the named scheme still omitted
  complete JSON byte rules. The contract now applies exact RFC 8785/JCS after
  typed preprocessing, rejects ambiguous inputs, and carries a tiny synthetic
  canonical-text/SHA-256 golden fixture. This is contract evidence, not a
  production manifest implementation or private data fingerprint.
- This stage adds no research trial, factor, strategy, provider, data download,
  private-data artifact, dependency, generated performance evidence, paper/live
  trading path, brokerage connection, order behavior, or credential handling.
- The initial PR head passed GitHub CI, but its required final current-head
  Codex review found one P1: `ordered_manifest_sha256` and
  `public_projection_sha256` named digests without freezing their exact
  projection fields and canonical byte preimages. The integration owner
  defined exact versioned projections, JCS/UTF-8 byte envelopes, ordering,
  duplicate/unknown-field rejection, and noncircular decision binding, then
  added synthetic base, reorder, and exact identity-mutation byte/hash vectors.
- First-round fix re-review found that allowed public fields could still carry
  path/URI values, physical component splitting was not tied one-to-one to the
  manifest, and `PIT-003` overstated hash mutation behavior. The second-round
  fix added a bounded opaque `safe_public_id` grammar plus allowed-key privacy
  negatives, made `physical_components` an all-and-only retained manifest
  projection, and limited the mutation claim to canonical-preimage change,
  recomputation, and the frozen golden cases. Two independent read-only
  re-reviewers reported no remaining actionable P1/P2 and did not edit their
  own findings.
- The first focused run after the review fix passed 18 tests and failed one
  direct Markdown phrase assertion because a normative sentence wrapped across
  lines. The test now evaluates normalized document text; the semantics and
  golden hashes were unchanged. Focused documentation tests then passed all 19
  cases.
- The first final full run passed 853 tests and failed one stale Stage 2
  documentation assertion that still expected the pre-fix Stage 3 roadmap
  status. The assertion now requires the accurate new-head GitHub-gate status;
  no research behavior or evidence classification changed.
- Final Python 3.12/pandas 2 local validation passed 854 tests with the same two
  platform-conditional wide-`longdouble` skips. Ruff, compilation, PEP 517
  sdist/wheel build, Skill audit, deterministic repo-map equality,
  privacy/path/digest, Markdown-table, Unicode/control-character, and diff
  checks passed.
- A Python 3.11/pandas 3 CI-aligned run reused the isolated Stage 2 environment
  and cached pytest overlay and also passed 854 tests with the same two
  platform-conditional skips. No repository dependency or lock file changed.
- Four pre-PR independent, non-overlapping read-only re-reviews and the two
  post-review digest re-reviews were separated from integration-owner edits.
  No review opened private data, generated performance values, vendor APIs,
  credentials, or network data.
- The digest-fix head passed its complete GitHub CI cycle before the permitted
  re-review. That current-head review found one further P2: the bitemporal
  predicate did not define a currently active listing or membership whose end
  was not known in the frozen dataset version.
- The integration-owner fix made `effective_to` always present and paired it
  with `FINITE` or `OPEN_IN_VINTAGE`, separated the manifest knowledge cutoff
  from per-role coverage, rejected sentinel/end substitutions, selected only a
  unique decision-time-knowable vintage, prohibited later closure
  back-propagation, and added the dated `PIT-015` boundary case. A follow-up
  read-only review caught and removed one remaining ambiguity between nullable
  schema values and absent required properties. Two independent reviewers then
  reported no actionable P1/P2; neither edited the fix.
- The open-interval fix head passed its complete GitHub CI cycle before the
  required current-head re-review. That review found one further P2: the
  readiness Skill treated an absent dataset-review decision as an
  unconditional stop even though the Stage 3 scope matrix permits a bounded
  `diagnostic_ready` outcome without formal dataset acceptance.
- The integration owner scoped the dataset-review decision identity, reviewer,
  and finding-disposition requirements to formal interpretation across the
  readiness Skill, audit, legacy experiment log, and both local-CSV forms.
  Diagnostic scope now records `dataset_manifest_reviewed = false`,
  `formal_interpretation_eligible = false`, and the limitation without
  fabricating formal decision fields. Protected-sample access-record and
  exposure-decision requirements remain scope-applicable so diagnostic access
  still downgrades classification and remains auditable. Documentation tests
  positively require that split and reject the old unconditional wording. Two
  independent read-only re-reviewers found no remaining actionable P1/P2 and
  did not edit their own findings.
- Workflow continuity correction: returning control while the asynchronous
  re-review was pending made the task appear stopped. The owner clarified that
  pending CI/review/merge gates must retain a five-minute scheduled heartbeat.
  The active task automation now persists through review, protected merge,
  exact merge-head CI, and automatic startup of the next roadmap stage without
  weakening any gate.
- The existing project environment lacked repository gate tools, so the owner-
  authorized isolated install added Ruff 0.16.0 and build 1.5.0 plus packaging
  26.2 and pyproject-hooks 1.2.0. The PEP 517 build used a disposable
  setuptools/wheel environment. Its first post-review run failed because the
  sandbox could not resolve the package index; the same isolated build
  succeeded with approved network access. These installs changed no tracked
  dependency declaration or lock file.

## 2026-07-26 - Signal, Execution, And Metric Timing Implementation

- Started from protected `main` merge `275982f` (PR #161) in the isolated
  `codex/signal-execution-timing-implementation` worktree. Verified the exact
  merge, successful merge-head GitHub CI, clean 638-test/Ruff/compilation
  baseline, current roadmap, and the unrelated Draft PR #148 before editing.
- Five non-overlapping read-only audits mapped portfolio timing/leakage,
  metric anchors, caller and serialization scope, deterministic tests, and
  adversarial contract risks. No private report or holdout value was opened.
- Changed `run_long_only_backtest` to require exact inclusive
  `evaluation_start`/`evaluation_end` timestamps. Full-source price/signal axes
  are validated without silent repair; bounded signals are then validated
  cell-by-cell and lagged only inside the accounting slice. Lag is a
  non-Boolean integer of at least one.
- Removed execution-close price filtering from selection. Targets are frozen
  from the bounded lagged final-signal matrix, while held incoming-price
  endpoints and intended nonzero buy/sell legs are validated later with
  distinct stable reasons and precedence.
- Replaced full-panel `pct_change` with row-aware held-asset accounting. Each
  row now advances incoming return, gross solvency, drift, frozen target
  feasibility, trade/turnover, cost, net/equity solvency, and post-trade
  holdings in the accepted order. The initialization anchor cannot trade or
  incur cost; the terminal observed bucket may trade and incur cost without
  inventing a future return.
- Formal benchmark input now uses the exact accounting axis. Explicit
  zero-return price and benchmark policies remain diagnostic-only; diagnostic
  benchmark output does not create formal benchmark-relative metrics.
- Added typed timing metadata and a deterministic dataclass ledger over the
  initialization-anchor/resolved-rebalance union. Current synthetic momentum,
  combined-score, and all eight sweep cases serialize their timing metadata
  and ledger with ISO timestamps and explicit null endpoints.
- Unified annualized return, volatility, zero-risk-free unadjusted Sharpe,
  benchmark total/excess return, tracking error, and average turnover on the
  common post-anchor measured dates. Total return, total turnover, and costs
  retain every accounting row. Drawdown now seeds its running peak with
  validated initial capital.
- Added deterministic TIMING-001 through TIMING-014 behavior coverage,
  including the hand-calculated four-row case, irregular and monthly lag,
  exact axes/bounds, signal mutation isolation, held/trade price precedence,
  mid-bucket anchor ledger, gross/post-cost failure reasons, strict benchmark,
  terminal execution, and serialized evidence. Legacy zero-lag fixtures now
  assert a zero initialization anchor and first legal post-anchor execution.
- The owner selected mandatory source provenance after independent review
  demonstrated that snapshot-only provenance cannot distinguish a pre-start
  `1+0j` write from a bounded `1+0j` write when pandas produces identical
  `complex128` frames. Every backtest caller now declares a role-bound,
  immutable baseline at capture. Enforcement begins there and does not prove
  pre-capture history. A controlled coordinate ledger chains later
  before/after state; untracked post-capture writes, stale source
  identity/axes, role swaps, malformed records, and replay inconsistency fail
  closed.
- Lossless recovery is limited to bounded cells in originally real columns
  with a tracked complex write outside the current bounds. Untouched
  coordinates must match their original snapshot; controlled bounded
  coordinates must match their latest tracked semantic assignment. A latest
  real assignment may recover, while a latest complex assignment remains
  invalid. Native complex inputs, lossy large-integer conversion, and
  moved-bound evidence are not recovered. Direct and nested provenance objects
  are rejected by experiment-log serialization; current committed logs are
  scanned for private field names and contain only the allowlisted policy/status
  strings. Extracted primitive values remain a caller responsibility.
- Generated outputs are refreshed in dependency order for momentum,
  combined-score, and the eight-case sweep, followed by the registry and repo
  map. The current implementation checkpoint has 849 passing tests in both
  the local project environment and a Python 3.11/pandas 3 CI-aligned
  environment. Two wide-`longdouble` provenance regressions skip on macOS
  arm64 because its `longdouble` mantissa is not wider than float64; they are
  retained to execute on Ubuntu CI. Two final dependency-order regenerations
  were byte-identical. Full Ruff, compilation, build, Skill, JSON, privacy,
  Unicode/control-character, and diff gates passed.
- Independent review exposed and the implementation fixed four final boundary
  classes: out-of-window complex dtype propagation, gross-solvency ordering,
  benchmark equity/return anchor and per-period multiplier consistency, and
  numeric conversion overflow. TIMING-012/014 now also reconcile terminal
  cost/turnover and the complete typed metadata/ledger against accounting
  arrays.
- A later adversarial re-review found that custom subclasses of otherwise
  accepted numeric types could hide mutable conversion behavior, and that
  control scalars could be converted again after validation. Source cells and
  backtest controls now use exact immutable built-in/NumPy/Fraction type
  allowlists; numeric subclasses fail before conversion. Position-cap input is
  canonicalized once. Stateful regression fixtures prove that provenance,
  capital, selection, costs, lags, annualization, and position constraints do
  not call attacker-controlled numeric conversions.
- The same review found a Linux-specific provenance collision risk: NumPy
  `longdouble` and `clongdouble` may contain more precision than Python
  `float`, so downcasting them could make distinct sources share a digest or
  falsely label recovery as lossless. Provenance now rejects exact NumPy
  floating/complex scalar types whose mantissa exceeds float64 before
  conversion. Conditional `nextafter` regressions execute only on platforms
  where that wider precision exists.
- Pre-PR independent read-only review reported no remaining actionable P1/P2
  finding after the scalar, metric-helper, wide-precision, and canonical
  documentation fixes. Its focused review suite passed 310 tests with the same
  two expected macOS precision skips; the initial full local suite passed 847
  tests with those two skips.
- Final JSON SHA-256 hashes are
  `8213abbad4dcebaf76cbb0e5e4b2335b65c89ff752a1776131b3b62d4b4beb70`
  (momentum),
  `efd0482d4e28509d94a2fcd903ce4b4dc0790a6cb8bca6389af28517db5d229c`
  (combined score), and
  `f07238493562e6c56445e1f00298d5303cc98eed4f7883de4815236cfbcf0c3a`
  (eight-case sweep).
  Removing only the two allowlisted provenance policy/status keys reconstructs
  the pre-provenance Stage 2b JSON hashes exactly, so the provenance addition
  did not alter numerical, holding, cost, or date evidence. JSON parsing and
  scans found no internal provenance cells, axes, identities, mutation
  ledgers, or digests in committed evidence.
- After the first GitHub CI passed on commit `8611e54`, the required
  stable-head Codex review found one P2 sequence gap. An outside complex write
  can upcast a column; a later controlled bounded real write is then stored as
  `x+0j`. Recovery incorrectly compared that coordinate only with its original
  snapshot and rejected the new valid real value. Extraction now derives the
  latest tracked semantic assignment per bounded coordinate: latest real
  assignments recover only when the stored value matches, and latest complex
  assignments remain invalid. A deterministic complex-to-real-to-complex
  sequence protects both outcomes.
- The first focused run of that new regression failed because the test tried
  to inspect a non-public `target_weights` result attribute. The backtest had
  already completed successfully; the test was corrected to assert the public
  post-trade `holdings` evidence. Both local and pandas 3 focused reruns then
  passed 214 tests with the two expected macOS precision skips.
- Follow-up independent review then found a second P2 in the same chain. An
  outside complex upcast followed by an outside string write changes the
  current column to object while untouched bounded values remain `x+0j`;
  recovery had required a currently complex dtype and rejected those bounded
  cells. A real-origin column with a tracked outside complex write may now
  recover matching bounded semantics from either a complex or object
  container. Latest bounded non-real/complex assignments remain invalid. The
  mixed outside-write regression passes in both local and pandas 3 focused
  suites, which now pass 215 tests with two expected macOS precision skips.
- Final independent re-review exercised 777 mutation sequences spanning real,
  integer, Fraction, IEEE `NaN`, complex, Boolean, string, missing, and object
  promotion cases and reported no remaining actionable P1/P2 finding. The full
  local and Python 3.11/pandas 3 suites each pass 849 tests with the same two
  expected macOS precision skips. Ruff, compilation, build, Skill audit, JSON
  parsing, privacy/path scanning, hidden-Unicode scanning, and diff checks
  pass; new-head GitHub CI and Codex re-review remain protected-merge gates.
- The default `python` alias remains absent and alternate system interpreters
  lack the repository test stack. Local tests reused the existing project
  `.venv` with `PYTHONPATH=src`. A disposable, ignored worktree `.venv` was
  created through `uv` solely for CI-aligned compatibility checks. It contains
  Python 3.11.15, project 0.1.0, NumPy 2.4.6, pandas 3.0.5, SciPy 1.17.1,
  pytest 9.1.1, python-dateutil 2.9.0.post0, six 1.17.0, iniconfig 2.3.0,
  packaging 26.2, pluggy 1.6.0, and Pygments 2.20.0. The environment and uv
  cache are not project artifacts; no dependency declaration or lockfile is
  changed.
- The existing project environment did not contain the `build` frontend. A
  separate transient `uv --no-project` build environment installed build
  1.3.0, packaging 26.2, and pyproject-hooks 1.2.0; its disposable PEP 517
  environments installed setuptools 83.0.0, wheel 0.47.0, and packaging
  26.2. They existed only in the uv cache and operating-system temporary
  directories. The successful sdist/wheel outputs are ignored validation
  artifacts; project dependency declarations and lockfiles remain unchanged.
- Trial-count impact is zero. All changed reports are deterministic synthetic
  implementation evidence. No factor formula, private diagnostic, provider,
  credential, LEAN runtime, brokerage, order, paper, or live behavior changed.

## 2026-07-26 - Signal, Execution, And Metric Timing Contract

- Started from protected `main` merge `202273b` (PR #160) in the isolated
  `codex/signal-execution-timing-contract` worktree. Verified the exact merge,
  successful post-merge GitHub CI, and a clean 637-test/Ruff/compilation/build
  baseline before editing; the unrelated local checkout remained untouched.
- Four non-overlapping read-only audits mapped backtest timing, metric anchors,
  callers, canonical documentation, and adversarial leakage risks. No private
  result or holdout value was opened.
- Distinguished the full source index `s[0..M]` from bounded accounting dates
  `a[0..N]`. Each scheduled execution row `a[j]` uses source signal `a[j-L]`;
  pre-anchor history may support feature calculation but cannot satisfy
  execution lag. Under daily rebalancing, lag one maps fixture `d0`/`a[0]` to a
  target reset after the return ending at `d1`/`a[1]`, with the target's first
  earned return ending at `d2`/`a[2]`. The existing Stage 1 `d0`-to-`d1` label
  is therefore diagnostic and not that strategy return.
- Recorded three high-risk Stage 2b gaps: zero lag is accepted even though
  signals are declared available after close; signals are silently reindexed;
  and execution-close price validity can change target membership.
- Recorded metric-anchor gaps: full feature warm-up can enter reported
  strategy/benchmark metrics, volatility and Sharpe include the initialization
  row while tracking error excludes it, and drawdown does not seed its peak
  from initial capital.
- Added `docs/signal_execution_timing_contract.md` with the sole current policy
  `after_close_signal_next_observed_close_v1`, exact row/event ordering,
  non-Boolean integer lag of at least one, decision-time target freezing,
  bounded evaluation anchors, common metric dates, benchmark and terminal
  rules, typed metadata, a hand-calculated accounting case, and a 14-case
  Stage 2b behavior matrix.
- Kept the close-reset model explicitly idealized. Next-open, same-close,
  auction, intraday, exchange-calendar, partial-fill, capacity, LEAN, real-data,
  and empirical interpretation decisions remain deferred.
- Reconciled the specification, roadmap, handoff, decision record, historical
  metric design wording, changelog, repository map, and documentation-contract
  tests. The repo-map generator only adds the new canonical document to its
  important-file index; no source, research script, LEAN file, generated
  evidence, workflow Skill, or `AGENTS.md` changed.
- Independent semantic and canonical-document reviewers found one P1 and
  several P2 contract gaps in the first draft. The integration owner fixed
  decision-time ambiguity, scheduled-row mapping, buy/sell feasibility,
  annualization, no-op and terminal ledger states, mutation tests, and the
  repo-map scope wording.
- The first stable-head GitHub review then found three P2 ambiguities in the
  intervening-close invariant, non-daily anchor ledger cardinality, and
  evaluation-bound test matrix. A separate executor fixed them. A fresh
  read-only review caught the remaining full-source-versus-accounting lag
  ambiguity, non-executable pandas boundary pseudocode, and no-op incoming
  interval distinction; those were also corrected before the next stable head.
- The first repair-head GitHub re-review found a P1 measured-date omission in
  the displayed tracking-error formula and a P2 missing insolvency policy.
  A separate executor corrected the formula and added typed failure policy.
  Adversarial read-only follow-up then separated gross failure before pretrade
  division from post-cost net/equity failure, preserved the public helper's
  zero benchmark anchor, closed signal, held-price, execution-price, benchmark,
  and direct-return Boolean/complex/string type holes, and added direct
  metric-equity safeguards.
- The next stable-head review caught signal-value validation occurring before
  the exact accounting slice. The contract now validates full-source axes
  structurally, selects exact bounded rows, and only then validates signal
  values; deterministic mutations prove pre-start and post-end bad values
  cannot change bounded results or exceptions.
- Final local validation passes with 638 tests, Ruff, compilation of
  `src`, `research`, `tests`, and `lean`, sdist and wheel build, reproducible
  repo-map generation, Unicode/control scan, and branch diff checks.
- The default `python` alias was absent, Homebrew Python 3.14 lacked pytest,
  and the standalone pytest used Python 3.9 without `tomllib`. Tests therefore
  reused the existing repository `.venv` with the current worktree `src` first
  on the import path; no test dependency was installed.
- Package validation used a disposable `/private/tmp` uv environment with
  `build==1.5.0`, `pyproject-hooks==1.2.0`, `packaging==26.2`,
  `setuptools==83.0.0`, and `wheel==0.47.0`. These packages were not installed
  into the project environment, and no dependency declaration or lock file
  changed.
- Trial-count impact is zero. This design stage changes no factor, label,
  strategy, portfolio, cost, benchmark, execution, report, or research result
  and authorizes no paper or live behavior.

## 2026-07-26 - Purged And Bounded Split Implementation

- Started from protected `main` merge `12e0e86` in the isolated
  `codex/purged-bounded-split-implementation` worktree. The unrelated local
  checkout remained untouched.
- Verified the exact merge SHA, successful post-merge GitHub CI, and a clean
  595-test/Ruff/compilation baseline before editing.
- Implemented the accepted six-bound contract in
  `src/features/validation.py`: exact source-index retention, typed label
  kinds, deterministic per-candidate ledger, row-horizon endpoints,
  per-window purge, gap-aware embargo, feature warm-up, in-window label
  warm-down, hard bounded test suffix, JSON-ready metadata, and raw-axis target
  masking.
- Added a label-aware slicer that rejects unmasked structurally excluded
  values. Price labels are calculated only for eligible intervals; no raw
  cross-boundary or post-test label value is exposed to diagnostics.
- Added consumer availability accounting for eligible target cells,
  valid/missing target cells, usable factor-label pairs,
  `no_eligible_labels`, and `no_usable_label_pairs`.
- Migrated all four current split consumers. EODHD and local-fixture paths use
  the same price-label mask for assets and benchmark. Both synthetic consumers
  now declare `synthetic_same_row_response`, horizon zero, exact `[t, t]`
  intervals, and no forward-price-return wording.
- The tiny four-row local fixture now records one feature warm-up row and three
  one-row horizon-one windows. All are honestly retained as `INVALID` with
  zero eligible labels instead of borrowing values across split boundaries.
- Added deterministic post-test append/mutation, cross-edge mutation,
  asset/benchmark parity, zero-eligible, partial-missing, all-missing,
  irregular-calendar, purge/embargo-overlap, and strict-alignment tests. The
  full suite currently passes with 637 tests.
- Independent review found and the integration owner fixed three P2
  hardening gaps: canonical revalidation now rejects mutated ledgers and
  window schedules, the raw feature slicer requires an explicit feature role,
  and configured-case evidence preserves structural label invalidity instead
  of replacing it with a generic metric-observation reason.
- Regenerated only the affected synthetic local-fixture and robustness
  Markdown/JSON evidence, then regenerated the experiment registry. JSON
  parsing and secret/private-path scans passed; the registry was
  semantically unchanged.
- Built the sdist and wheel successfully. The build tool created disposable
  isolated environments and installed `setuptools==83.0.0`, `wheel==0.47.0`,
  and transitive `packaging==26.2`; these were not installed into the project
  environment, and no dependency or lock file changed.
- PR #160 CI run `30234375203` exposed one pandas-version-sensitive test
  expectation: pandas 3.0.5 constructs an empty literal `DatetimeIndex` at
  second precision while the implementation correctly preserves the source
  index's microsecond precision. The test now derives its expected empty set
  from the source index and passes under both local pandas 2.2.3 and CI-matched
  pandas 3.0.5 without changing implementation behavior.
- The CI reproduction used a disposable `uv run` Python 3.11 environment with
  `numpy==2.4.6`, `pandas==3.0.5`, `scipy==1.17.1`, `pytest==9.1.1`,
  `python-dateutil==2.9.0.post0`, `six==1.17.0`, `iniconfig==2.3.0`,
  `packaging==26.2`, `pluggy==1.6.0`, and `pygments==2.20.0`. Nothing was
  installed into the project environment, and no dependency or lock file
  changed.
- The final Codex review on commit `b0269a1` found one P2 classification gap:
  an EODHD split with usable pairs but no valid IC, Rank IC, or quantile-spread
  dates remained `DIAGNOSTIC_ONLY`. The split summary now preserves structural
  invalid reasons first and otherwise records
  `no_valid_factor_diagnostic_dates` / `INVALID` when every diagnostic is
  empty. A one-asset sparse-universe regression test covers the case.
- The next Codex review on commit `60d7b7f` found the same P2 classification
  gap in the synthetic IC/Rank-IC consumer and local CSV fixture consumer.
  Classification is now centralized in `features.validation`; EODHD,
  synthetic split, and local fixture summaries preserve availability failures
  first and otherwise mark all-metric-empty splits
  `no_valid_factor_diagnostic_dates` / `INVALID`. Two deterministic sparse
  coverage tests reproduce the findings and also verify that the local
  configured-case JSON summary agrees with its split summary. A shared-helper
  contract test preserves availability precedence and confirms that one
  non-empty diagnostic remains `DIAGNOSTIC_ONLY`.
- Independent review then found a pandas 3 compatibility P2 in the robustness
  consumer: a missing availability reason can materialize as `NaN`, so an
  `is not None` check marked valid train rows `INVALID`. The robustness path
  now uses the shared classifier for missing-reason normalization and
  structural precedence while preserving its stricter one-metric failure
  reasons. A CI-aligned pandas 3 regression keeps valid train rows
  `DIAGNOSTIC_ONLY`, constant-signal rows invalid for absent metrics, and
  zero-eligible validation/test rows structurally invalid.
- Regenerating the scoped local-fixture and robustness Markdown/JSON outputs
  plus the experiment registry after the classification fixes reproduced
  their exact prior SHA-256 hashes; no generated evidence changed.
- The review-fix package rebuild reused a disposable `uvx`
  `build==1.5.0` frontend. Its isolated sdist and wheel environments each
  installed `setuptools==83.0.0`, `wheel==0.47.0`, and transitive
  `packaging==26.2`; no project environment, dependency declaration, or lock
  file changed.
- The first narrowed pandas 3 review-fix check omitted the declared SciPy
  runtime dependency and stopped at pandas' Spearman import. The same
  disposable Python 3.11 check passed all six EODHD tests after adding
  `scipy==1.17.1`; no repository environment or dependency file changed.
- The first direct generator invocation could not import `backtest` because a
  one-off Python process did not include the repository `src` directory. The
  same reviewed generator functions succeeded after explicitly placing the
  worktree `src` directory first on that process's import path. No dependency
  was installed and no dependency file changed.
- Assumption: the private EODHD default bounded test ends on 2025-04-30, before
  the already-exposed 2025-05-01 onward interval. No private file, output, or
  performance value was opened or interpreted.
- No factor formula, strategy, portfolio, cost, execution, data-provider, or
  LEAN behavior changed. Trial-count impact is zero because this stage changes
  validation plumbing and deterministic diagnostic evidence only.

## 2026-07-26 - Purged And Bounded Split Contract

- Started from protected `main` merge `57f3db3` in the isolated
  `codex/purged-bounded-split-contract` worktree and preserved the unrelated
  local checkout.
- Verified the 594-test baseline, Ruff, compilation, and package build before
  editing. The first isolated build lacked sandbox network access; the same
  declared build passed when allowed to resolve its temporary build
  requirements.
- Mapped the shared split helper, all four Python consumers, their tests, and
  the duplicated full-panel forward-return calculations. Confirmed that
  repairing only the split dictionary would leave the local fixture's unsplit
  diagnostics unsafe.
- Added `docs/purged_bounded_split_contract.md` with six explicit inclusive
  bounds, hard bounded-test semantics, exact row-horizon label intervals,
  per-window purge, optional embargo, feature warm-up, in-window label
  warm-down, ignored suffix, and deterministic metadata.
- Chose raw-axis target masking so purged and embargoed rows remain visible as
  all-`NaN` targets. Zero-eligible windows remain explicit `INVALID` evidence
  rather than borrowing cross-boundary labels.
- Added a 22-case Stage 1b matrix including hand-calculated ownership,
  irregular calendars, explicit gaps, purge/embargo overlap, asset/benchmark
  parity, synthetic-label honesty, and post-test/cross-edge mutation
  invariance.
- Used one independent read-only timing/leakage reviewer. No private files or
  performance values were opened.
- Kept this stage documentation/test-contract only. No `src/`, `research/`,
  generated research evidence, dependency declaration, factor, backtest,
  benchmark, cost, execution, or LEAN behavior changed. Trial-count impact is
  zero.

## 2026-07-26 - Research Charter Reset

- Verified `origin/main` at `a1486ea`, latest merged PR #157, successful
  exact-head GitHub CI, and a local 591-test baseline with Ruff, compilation,
  and package build passing.
- Preserved a dirty, 47-commit-behind local checkout by creating the isolated
  `codex/research-program-charter-reset` worktree from `origin/main`.
- Ran six non-overlapping read-only audits covering repository state,
  timing/leakage, data/universe, statistical validation,
  factor/strategy/portfolio scope, and adversarial program risks.
- Confirmed two high-priority timing defects: forward labels can cross split
  boundaries, and after-close signals still permit zero lag. Also confirmed
  that the proposed 2025-05-01 through 2026-05-31 interval is inside an
  already-calculated and reviewed diagnostic test tail.
- Added `docs/research_program_charter.md` and reconciled the specification,
  canonical roadmap/handoff, controller, staged workflow Skill, public method
  routing, documentation contracts, and generated repo map.
- Reconciled the active real-data readiness Skill/checklist so static or
  otherwise unverified historical membership can support diagnostics only,
  and marked `EXPERIMENT_LOG.md` as a diagnostic/legacy record rather than the
  future immutable all-trial ledger.
- Fixed a post-publication CI toolchain drift: the unbounded development
  requirement installed Ruff 0.16.0, whose expanded defaults surfaced 95
  repository-wide findings after local Ruff 0.15.18 passed. Added an explicit
  `E4`, `E7`, `E9`, and `F` rule baseline and a configuration contract test;
  both Ruff versions pass without changing unrelated source or tests.
- Addressed the final-head Codex review P1 that auto-merge eligibility could
  precede the required review. Controller, workflow Skill, roadmap, and tests
  now require stable checks and a completed current-head Codex review with no
  unresolved actionable findings before either merge path is eligible.
- An independent documentation review found and then verified fixes for the
  readiness bypass, experiment-log authority, and broad unrelated-PR stop
  clauses. The final contract suite covers those cross-document constraints.
- Final local validation reached 594 passing tests; Ruff, both compilation
  gates, package build, generated repo-map determinism, the equivalent two-Skill
  audit, Unicode/control-character scan, and diff checks passed. PowerShell was
  unavailable for the official Skill-audit entrypoint.
- Kept this stage documentation/workflow-control only. No feature, backtest,
  data loader, statistical calculation, generated research evidence, private
  result, or LEAN behavior changed. Trial-count impact is zero.
- Classified Draft PR #148 as an independent older governance PR that changes
  only `AGENTS.md`; this stage avoids that file and does not alter the PR.

## 2026-07-11 - Full Conformance Audit Closure

- Merged the read-only full repository audit at
  `docs/full_repository_conformance_audit_2026-07-11.md`.
- Verified 591 tests, Ruff, compilation, package build, deterministic generated
  evidence, JSON logs, repository hygiene, privacy boundaries, and LEAN scope.
- Recorded no actionable P1/P2 findings and retained real-data interpretation,
  plotting, broader constraints, calibrated impact, and LEAN execution as
  explicit blocked or out-of-scope work rather than claiming project completion.

## 2026-07-11 - Holding-Episode Metric Implementation

- Exposed signed target-minus-pretrade weights alongside existing absolute
  trade weights and retained exact turnover reconciliation.
- Added completed continuous-positive-weight episode attribution, including
  prior-holding return timing, cumulative deployed weight, and applied trading
  costs allocated pro rata by absolute signed trades.
- Added episode hit rate, average holding-period return, terminal-open and
  completed counts, audit metadata, and deterministic synthetic evidence.
- Preserved terminal-open positions without invented exits and kept zero-cost
  outputs labeled as diagnostics under existing policy.

## 2026-07-11 - Holding-Episode Metric Design

- Defined continuous positive post-trade weight as the episode boundary, with
  resizing retained inside an episode and re-entry after zero starting another.
- Required signed trade weights so deployed capital, turnover, and applied
  costs can reconcile without reconstructing direction from closing holdings.
- Defined net episode contribution over cumulative positive deployed weight,
  equal weighting across completed episodes, and exclusion of terminal-open
  episodes with explicit counts.
- Kept this checkpoint design-only; no source, accounting, metric, or generated
  report behavior changed.

## 2026-07-11 - Position-Cap Implementation

- Added strict target-weight validation and clip-without-renormalization logic
  in `src/risk/constraints.py`.
- Integrated the optional cap after selection and before drift-aware trade
  calculation, so constrained targets drive turnover, costs, holdings, and net
  returns while residual exposure remains non-interest-bearing cash.
- Preserved default backtest behavior when no cap is supplied and emit the
  approved audit metadata only when active.
- Added focused helper and integration tests; default synthetic reports remain
  byte-stable because they do not enable the optional constraint.

## 2026-07-11 - Position-Cap Constraint Design

- Defined the first constraint as an optional long-only per-position cap after
  ranking and selection but before drift-aware trade calculation.
- Chose clipping without redistribution or renormalization; residual exposure
  remains non-interest-bearing cash, including infeasible fully invested
  targets.
- Fixed validation, audit metadata, liquidity ordering, turnover/cost
  interaction, and focused implementation-test requirements.
- Kept `src/risk/constraints.py` unchanged and deferred every other constraint,
  episode metric, plotting feature, and strategy-selection change.

This is a living engineering log for review notes, correctness audits, bug fixes, and implementation decisions that are useful for future PR summaries, interviews, retrospectives, and performance-review material.

## How To Update This Log

- Add a new dated entry after meaningful engineering work, especially after correctness reviews, bug fixes, test design changes, architecture decisions, or non-obvious tradeoffs.
- Do not use this log to claim profitability or investment performance.
- Separate observed facts from assumptions. Use `Assumption:` or `Needs follow-up:` when evidence is incomplete.
- Prefer specific engineering reasoning over generic status updates.
- Link or name the relevant files, functions, tests, and checks when possible.

---

## 2026-07-11 - Tracking-Error Implementation

Stage: Stage 2 benchmark-relative evaluation implementation.

Implementation:

- Added `calculate_tracking_error()` for exact-index daily active returns using
  population `ddof=0`, annualization by `sqrt(252)`, synthetic-anchor exclusion,
  and terminal-window inclusion.
- Added explicit benchmark returns to `BacktestResult`; strategy returns remain
  net of applied transaction costs and slippage, while benchmark returns remain
  cost-free. The diagnostic benchmark `zero_return` fallback is ineligible for
  tracking error and does not emit the metric or its metadata.
- Added strict type, finite-value, date-order, duplicate-date, timezone,
  frequency, benchmark-anchor, and minimum-window validation.
- Refreshed deterministic synthetic reports, experiment logs, and the registry
  with tracking error and its audit metadata. These remain synthetic
  diagnostics, not profitability or investment evidence.

No portfolio selection, holdings, turnover, cost calculation, real-data access,
vendor integration, brokerage, or trading-execution behavior changed.

---

## 2026-07-11 - Tracking-Error Contract Design

Stage: Stage 2 benchmark-relative evaluation design.

Decision:

- Define `tracking_error` as the annualized population volatility of aligned
  active daily close-to-close returns, using `ddof=0` and `sqrt(252)`.
- Use strategy returns net of every cost actually applied by the backtester and
  a cost-free benchmark price-return series. Require exact daily index and
  timezone alignment, reject missing or non-finite inputs, exclude the
  synthetic first row, and include the terminal observed return window.
- Keep this checkpoint documentation-only. The implementation PR must add the
  metric, focused alignment tests, audit metadata, and generated evidence only
  after this contract is accepted.

No portfolio selection, accounting, cost, benchmark, data-access, execution,
or generated-output behavior changed in this design checkpoint.

---

## 2026-07-10 - Strict Input Contract Hardening

Stage: shared panel and local CSV input validation.

Observed defects:

- Shared numeric panel validation reached column dtype inspection before
  detecting duplicate asset labels, so selecting a duplicated label returned a
  DataFrame and produced an unclear `AttributeError`.
- The same validator accepted positive and negative infinity even though those
  values are not meaningful finite research observations.
- Strict long-price CSV loading checked explicit source-cell missingness before
  pivoting, but a sparse date-symbol grid could introduce `NaN` during the
  pivot and pass the default `allow_missing=False` contract.

Implementation:

- Duplicate asset labels are rejected explicitly before per-column dtype
  validation. Numeric panels now require each cell to be finite or a real
  `NaN`, preserving the existing missing-data behavior used by rolling factor
  calculations.
- Strict long-price loading now checks the completed pivoted panel and reports
  the first missing date, value field, and asset. `allow_missing=True` remains
  the explicit permissive path for intentionally sparse panels.
- Focused regressions cover duplicate labels, both signs of infinity, preserved
  `NaN`, strict sparse-pivot rejection, and explicit sparse-pivot preservation.

No feature formulas, signal dates, execution timing, portfolio accounting,
private-data boundaries, vendor access, or live-trading behavior changed.

---

## 2026-07-10 - Drift-Aware Portfolio Accounting

Stage: simulated backtester correctness repair.

Observed defect:

- The backtester forward-filled target weights between rebalance dates. When
  assets earned different returns, this held weights constant without recording
  trades, which was economically equivalent to free daily rebalancing.
- The benchmark `zero_return` fallback filled both a missing date and the first
  valid post-gap return with zero, so `[100, missing, 102]` ended at `1.00`
  instead of `1.02`.
- Review of the first repair found that close-time fixed costs were still
  charged as a fraction of beginning-period value. After a positive held-asset
  return, this understated both transaction-cost and fixed-slippage impacts.
- The backtester allowed net period growth of zero after trading costs, leaving
  a zero-valued equity curve with positive holdings instead of failing.

Implementation:

- Portfolio weights now drift through close-to-close asset returns. On a
  scheduled rebalance, turnover is the sum of absolute changes between drifted
  pre-trade weights and the new target; on other dates turnover is zero.
- The existing turnover convention remains undivided, so a complete switch
  between two assets has turnover `2.0`.
- The benchmark diagnostic fallback forward-fills only from observations
  already available, preserves a prior observation outside the strategy index,
  then recognizes the cumulative move when data resumes.
- Fixed-bps transaction costs and slippage are charged against post-return
  portfolio value and converted to beginning-period return impacts before they
  are deducted. Precomputed volume-aware impact remains an already-scaled
  return-impact input and is not rescaled.
- Net growth at or below zero after all trading-cost components now raises with
  the first exhausted date before an equity curve is produced.
- A two-asset divergent-return regression test distinguishes the corrected
  `2.50` buy-and-hold path from the prior `2.25` constant-weight path and checks
  the `0.60` rebalance turnover against drifted weights.
- A benchmark regression test checks `[1.00, 1.00, 1.02]` across a one-date
  gap, and a separate test preserves a `100` observation before the strategy
  index so a later `102` observation ends at `1.02` without future filling.
- A divergent-return/full-switch test checks transaction cost `0.04`, fixed
  slippage `0.02`, and final equity `1.9109` after a 100% held-asset gain.
  Separate fixed-cost and precomputed-impact tests require explicit failure
  when a cost impact of `1.0` exhausts the portfolio.
- Affected committed synthetic reports, logs, and registry values were
  regenerated. Those values remain synthetic diagnostics, not market or
  profitability evidence.

Needs follow-up:

- The standalone volume-aware slippage diagnostic still derives candidate
  trade weights from target changes. A separate scoped contract change should
  accept explicit per-asset trade weights from a drift-aware portfolio path
  before that helper is treated as execution-accounting evidence.

---

## 2026-06-29 - EODHD Limited Factor Diagnostics Brief

Stage: private-output-only neutral diagnostics brief.

Changed files:

- `research/eodhd_limited_factor_diagnostics_brief.py`
- `tests/test_eodhd_limited_factor_diagnostics_brief.py`
- `docs/eodhd_limited_factor_diagnostics_brief_checkpoint.md`
- `docs/current_handoff.md`
- `docs/engineering_log.md`
- `docs/decision_log.md`
- `CHANGELOG.md`
- `docs/repo_map.md`

Private outputs:

- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/LIMITED_FACTOR_DIAGNOSTICS_BRIEF.json`
- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/LIMITED_FACTOR_DIAGNOSTICS_BRIEF.md`

Implementation:

- Added a narrow research runner that reads the private limited review JSON,
  readiness review JSON, and experiment log JSON, then writes deterministic
  JSON plus a concise Markdown brief.
- The brief reports only factor coverage, factor missingness, IC, Rank IC,
  quantile spread, split labels, factor count, date range, and row counts.
- Direction, magnitude, and split consistency are neutral diagnostic labels.
- Added focused synthetic/temp-file tests only; no private data was committed.

Private generation evidence:

- Factors briefed: 2.
- Split labels: test, train, and validation.
- Asset rows: 21320.
- Benchmark rows: 2132.
- Symbol coverage: 11.
- Date range: 2018-01-02 to 2026-06-26.
- Private brief output sensitive-marker scan: 0 hits.

Guardrails:

- No raw CSV/JSON files were copied into the repository.
- No private market data was committed.
- No data was fetched or downloaded.
- No vendor API, token, credential, or `.env` file was used.
- No strategy, backtest, portfolio construction, PnL, Sharpe, drawdown,
  trading metric, investment recommendation, performance interpretation,
  profitability claim, alpha claim, or trading-readiness claim was made.

Next safe stage:

- Decide whether another metadata-only methodology/data-readiness checkpoint is
  needed before any broader research interpretation.

---

## 2026-06-28 - EODHD Limited Factor Diagnostics Review

Stage: private-output-only limited factor diagnostics review.

Changed files:

- `research/eodhd_limited_factor_diagnostics_review.py`
- `tests/test_eodhd_limited_factor_diagnostics_review.py`
- `docs/eodhd_limited_factor_diagnostics_review_checkpoint.md`
- `docs/current_handoff.md`
- `docs/engineering_log.md`
- `docs/decision_log.md`
- `CHANGELOG.md`
- `docs/repo_map.md`

Private outputs:

- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/LIMITED_FACTOR_DIAGNOSTICS_REVIEW.json`
- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/LIMITED_FACTOR_DIAGNOSTICS_REVIEW.md`

Implementation:

- Added a narrow research runner that reads the private dry-run summary,
  experiment log, and readiness review, then writes deterministic JSON plus a
  concise Markdown limited review.
- The runner summarizes only factor coverage, factor missingness, IC, Rank IC,
  quantile spread, and split labels.
- Added focused synthetic/temp-file tests only; no private data was committed.

Private generation evidence:

- Factors reviewed: 2.
- Split labels: test, train, and validation.
- Asset rows: 21320.
- Benchmark rows: 2132.
- Symbol coverage: 11.
- Date range: 2018-01-02 to 2026-06-26.
- Private limited-review output sensitive-marker scan: 0 hits.

Guardrails:

- No raw CSV/JSON files were copied into the repository.
- No private market data was committed.
- No data was fetched or downloaded.
- No vendor API, token, credential, or `.env` file was used.
- No strategy, backtest, portfolio construction, PnL, Sharpe, drawdown,
  trading metric, investment recommendation, performance interpretation,
  profitability claim, alpha claim, or trading-readiness claim was made.

Next safe stage:

- Decide whether another metadata-only methodology/data-readiness checkpoint is
  needed before any broader research interpretation.

---

## 2026-06-28 - EODHD Factor Diagnostics Readiness Review

Stage: private-output-only readiness review for the EODHD factor diagnostics
workflow.

Changed files:

- `research/eodhd_factor_diagnostics_readiness_review.py`
- `tests/test_eodhd_factor_diagnostics_readiness_review.py`
- `docs/eodhd_factor_diagnostics_readiness_review_checkpoint.md`
- `docs/current_handoff.md`
- `docs/engineering_log.md`
- `docs/decision_log.md`
- `CHANGELOG.md`
- `docs/repo_map.md`

Private outputs:

- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/FACTOR_DIAGNOSTICS_READINESS_REVIEW.json`
- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/FACTOR_DIAGNOSTICS_READINESS_REVIEW.md`

Implementation:

- Added a narrow research runner that reads the private factor diagnostics
  experiment log and dry-run summary, then writes deterministic JSON plus a
  concise Markdown readiness review.
- The readiness field is deliberately named
  `ready_for_limited_factor_diagnostics_review`; it does not use trading,
  strategy, alpha, or live-use readiness language.
- Added focused synthetic/temp-file tests only; no private data was committed.

Private generation evidence:

- `ready_for_limited_factor_diagnostics_review`: `True`.
- Asset rows: 21320.
- Benchmark rows: 2132.
- Symbol coverage: 11.
- Date range: 2018-01-02 to 2026-06-26.
- Private readiness output sensitive-marker scan: 0 hits.

Guardrails:

- No raw CSV/JSON files were copied into the repository.
- No private market data was committed.
- No data was fetched or downloaded.
- No vendor API, token, credential, or `.env` file was used.
- No strategy, backtest, portfolio construction, PnL, Sharpe, drawdown,
  trading metric, performance interpretation, profitability claim, alpha claim,
  or trading-readiness claim was made.

Next safe stage:

- A future limited factor-diagnostics review may inspect diagnostics only
  within the no-strategy/no-performance boundary.

---

## 2026-06-28 - EODHD Factor Diagnostics Experiment Log

Stage: private-output-only experiment-log/readiness handoff for the completed
EODHD factor diagnostics dry run.

Changed files:

- `research/eodhd_factor_diagnostics_experiment_log.py`
- `tests/test_eodhd_factor_diagnostics_experiment_log.py`
- `docs/eodhd_factor_diagnostics_experiment_log_checkpoint.md`
- `docs/current_handoff.md`
- `docs/engineering_log.md`
- `docs/decision_log.md`
- `CHANGELOG.md`
- `docs/repo_map.md`

Private outputs:

- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/FACTOR_DIAGNOSTICS_EXPERIMENT_LOG.json`
- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/FACTOR_DIAGNOSTICS_EXPERIMENT_LOG.md`

Implementation:

- Added a narrow research runner that parses the private factor diagnostics
  dry-run summary, validates private output paths under the private bundle, and
  writes deterministic JSON plus a concise Markdown handoff.
- Reads only the input CSV `date` columns to record the already-validated date
  range; it does not recompute factor diagnostics or inspect raw CSV contents.
- Added focused synthetic/temp-file tests only; no private data was committed.

Private generation evidence:

- Asset rows: 21320.
- Benchmark rows: 2132.
- Symbol coverage: 11.
- Date range: 2018-01-02 to 2026-06-26.
- Private experiment-log output sensitive-marker scan: 0 hits.

Guardrails:

- No raw CSV/JSON files were copied into the repository.
- No private market data was committed.
- No data was fetched or downloaded.
- No vendor API, token, credential, or `.env` file was used.
- No strategy, backtest, portfolio construction, PnL, Sharpe, drawdown,
  trading metric, performance interpretation, profitability claim, alpha claim,
  or trading-readiness claim was made.

Next safe stage:

- Complete a real-data readiness review before any factor diagnostic values are
  interpreted.

---

## 2026-06-28 - EODHD Factor Diagnostics Dry Run

Stage: private-output-only EODHD local CSV factor diagnostics dry run.

Changed files:

- `research/eodhd_factor_diagnostics_dry_run.py`
- `tests/test_eodhd_factor_diagnostics_dry_run.py`
- `docs/eodhd_factor_diagnostics_dry_run_checkpoint.md`
- `docs/current_handoff.md`
- `docs/engineering_log.md`
- `docs/decision_log.md`
- `CHANGELOG.md`
- `docs/repo_map.md`

Private output:

- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/FACTOR_DIAGNOSTICS_DRY_RUN_SUMMARY.md`

Implementation:

- Reused existing strict loaders:
  `load_ohlcv_csv(..., require_adjusted_close=True)` and
  `load_benchmark_price_csv(..., value_column="adjusted_close")`.
- Reused existing feature helpers: `alpha_009` and `alpha_012`.
- Reused existing diagnostics: IC, Rank IC, quantile spread, and chronological
  train/validation/test split helpers.
- Added focused synthetic tests only; no private data was committed.

Private dry-run evidence:

- Asset rows: 21320.
- Benchmark rows: 2132.
- Symbol coverage: 11.
- Alpha#009 coverage: 21270 valid observations and 50 missing observations.
- Alpha#012 coverage: 21310 valid observations and 10 missing observations.
- Split labels: train, validation, and test.
- IC, Rank IC, and quantile-spread diagnostic dates were non-empty in each
  split for both factors.
- Private summary sensitive-marker scan: 0 hits.

Guardrails:

- No raw CSV/JSON files were copied into the repository.
- No private market data was committed.
- No data was fetched or downloaded.
- No vendor API, token, credential, or `.env` file was used.
- No strategy, backtest, portfolio construction, PnL, Sharpe, drawdown,
  trading metric, performance interpretation, profitability claim, alpha claim,
  or trading-readiness claim was made.

Validation note:

- The private dry run is executed with `PYTHONPATH=src .venv/bin/python -m
  research.eodhd_factor_diagnostics_dry_run`, matching the repo's local script
  import pattern in this environment.

Next safe stage:

- Prepare a real-data readiness review or experiment-log handoff before any
  factor diagnostic values are interpreted.

---

## 2026-06-28 - EODHD Data-Quality Diagnostics Checkpoint

Stage: documentation-only checkpoint for the completed private EODHD
no-performance data-quality diagnostics dry run.

Changed files:

- `docs/eodhd_data_quality_diagnostics_checkpoint.md`
- `docs/current_handoff.md`
- `docs/engineering_log.md`
- `docs/decision_log.md`
- `CHANGELOG.md`
- `docs/repo_map.md`

Private evidence reviewed:

- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/DATA_QUALITY_DIAGNOSTICS_DRY_RUN_SUMMARY.md`

Aggregate diagnostics evidence recorded:

- Coverage: 11/11 symbols.
- Rows: 21320 asset rows and 2132 benchmark rows.
- Date range: 2018-01-02 to 2026-06-26 for assets and benchmark.
- Calendar alignment: 0 partial asset-coverage dates, 0 missing benchmark
  dates, and 0 extra benchmark dates.
- Data-quality counts: 0 duplicate date-symbol rows, 0 missing required
  values, 0 non-positive price rows, 0 negative volume rows, 0 zero-volume
  rows, 0 invalid OHLC rows, 0 full-row stale indicators, and 52 unchanged
  adjusted-close indicators.
- Private summary sensitive-marker scan: 0 hits.

Guardrails:

- No raw CSV/JSON files were copied into the repository.
- No private market data was committed.
- No data was fetched or downloaded.
- No vendor API, token, credential, or `.env` file was used.
- No source, tests, research scripts, reports, loaders, backtester, metrics,
  factor logic, or generated outputs were changed.
- No factors, signals, IC, Rank IC, quantile spreads, strategy runs, backtests,
  returns, portfolio metrics, profitability claims, alpha claims, or
  trading-readiness claims were made.

Next safe stage:

- Prepare a docs-only factor-diagnostics plan before computing any real-data
  factor diagnostics. Keep performance interpretation and all trading-readiness
  language out of scope.

---

## 2026-06-28 - EODHD Loader Smoke Checkpoint And Diagnostics Dry Run Plan

Stage: documentation-only checkpoint for the completed private EODHD
validation-only loader smoke test plus the next diagnostics dry-run plan.

Changed files:

- `docs/eodhd_loader_smoke_checkpoint_and_diagnostics_dry_run_plan.md`
- `docs/current_handoff.md`
- `docs/engineering_log.md`
- `docs/decision_log.md`
- `CHANGELOG.md`
- `docs/repo_map.md`

Private evidence reviewed:

- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/LOADER_SMOKE_TEST_SUMMARY.md`

Aggregate loader-smoke evidence recorded:

- Existing strict loaders were used:
  `load_ohlcv_csv(..., require_adjusted_close=True)` and
  `load_benchmark_price_csv(..., value_column="adjusted_close")`.
- Coverage: 11/11 symbols including SPY.US benchmark.
- Date range: 2018-01-02 to 2026-06-26 for assets and benchmark.
- Rows: 21320 asset rows and 2132 benchmark rows.
- Counts: 0 duplicate date-symbol rows, 0 missing required values,
  0 non-positive price values, 0 negative volume rows, 0 zero-volume rows,
  0 invalid OHLC rows, 0 missing benchmark dates, and 0 extra benchmark dates.
- Private summary sensitive-marker scan: 0 hits.

Guardrails:

- No raw CSV/JSON files were copied into the repository.
- No private market data was committed.
- No data was fetched or downloaded.
- No vendor API, token, credential, or `.env` file was used.
- No source, tests, research scripts, reports, loaders, backtester, metrics,
  factor logic, or generated outputs were changed.
- No strategy, factor-performance calculation, backtest, return
  interpretation, profitability claim, alpha claim, or trading-readiness claim
  was made.

Next safe stage:

- A no-performance diagnostics dry run may summarize data-quality, coverage,
  calendar, missingness, stale-row, zero-volume, adjustment-policy, and
  survivorship caveats only. Stop before factor, signal, return, IC, Rank IC,
  quantile-spread, backtest, or performance interpretation.

---

## 2026-06-28 - EODHD Local CSV Loader Smoke Test Plan

Stage: documentation-only plan for the next private EODHD local CSV loader
smoke test.

Changed files:

- `docs/eodhd_local_csv_loader_smoke_test_plan.md`
- `docs/current_handoff.md`
- `docs/engineering_log.md`
- `docs/decision_log.md`
- `CHANGELOG.md`
- `docs/repo_map.md`

Scope:

- Use existing strict loaders only in the next stage.
- Inspect only schema, row counts, date ranges, symbol coverage, missing and
  duplicate counts, invalid-value counts, OHLC consistency, and SPY benchmark
  alignment.
- Write any loader-smoke-test summary only under
  `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run`.

Guardrails:

- No raw CSV/JSON files were copied into the repository.
- No private market data was committed.
- No data was fetched or downloaded.
- No vendor API or credential was used.
- No source, tests, research scripts, reports, loaders, backtester, metrics,
  factor logic, or generated outputs were changed.
- No strategy, factor-performance calculation, backtest, performance
  interpretation, profitability claim, or trading-readiness claim was made.

Next safe stage:

- Run the validation-only loader smoke test against the private normalized
  EODHD CSV files and write a private summary only. Stop before any
  implementation change, experiment-log interpretation, strategy run, factor
  output, or performance language.

---

## 2026-06-27 - EODHD Local CSV Validation Handoff

Stage: documentation-only handoff for the private EODHD local CSV
validation-only dry run.

Changed files:

- `docs/eodhd_local_csv_validation_handoff.md`
- `docs/current_handoff.md`
- `docs/engineering_log.md`
- `docs/decision_log.md`
- `CHANGELOG.md`
- `docs/repo_map.md`

Private evidence reviewed:

- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/LOCAL_CSV_READINESS_INTAKE_SUMMARY.md`
- `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run/VALIDATION_ONLY_DRY_RUN_SUMMARY.md`

Aggregate validation evidence recorded:

- Provider/source: EODHD EOD Historical Data All World.
- Coverage: 11/11 symbols including SPY.US benchmark.
- Date range: 2018-01-02 to 2026-06-26.
- Rows: 21320 universe rows and 2132 benchmark rows.
- Checks: schema pass, benchmark alignment pass, 0 missing required values,
  0 duplicate date-symbol rows, 0 bad date rows, 0 bad price rows,
  0 bad volume rows, and 0 credential-marker scan hits.

Guardrails:

- No raw CSV/JSON files were copied into the repository.
- No private market data was committed.
- No data was fetched or downloaded.
- No vendor API or credential was used.
- No strategy, factor-performance calculation, backtest, performance
  interpretation, profitability claim, or trading-readiness claim was made.

Next safe stage:

- Documentation/test-plan or validation-only loader smoke test only. Stop
  before strategy or performance interpretation until a reviewed experiment-log
  handoff records sample splits, cost/slippage assumptions, point-in-time
  universe status, benchmark policy, and EODHD adjustment-policy decisions.

---

## 2026-06-24 - Local CSV Validation-Only Dry Run Intake Checklist

This documentation-only stage adds
`docs/local_csv_validation_dry_run_intake_checklist.md` as a concise
user-facing checklist for preparing a future user-provided local CSV
validation-only dry run. It summarizes the required files, accepted schemas,
minimum columns, metadata, GitHub exclusions, Codex inspection boundary, and
ready prompt before any private files are read.

The handoff is updated to route the next safe stage to metadata-first readiness
intake only after the user supplies the declared bundle and metadata.

Validation passed with full pytest, compileall for `src`, `tests`, and
`research`, repo map refresh, `git diff --check`, and guardrail grep. The
guardrail grep matches were documentation prohibitions, caveats, and stop
conditions only.

This stage does not modify source code, tests, research scripts, generated
reports/logs, data files, CSV loaders, backtester behavior, metrics behavior,
factor formulas, diagnostics helpers, LEAN code, real-data access, vendor APIs,
credentials, live/paper trading, brokerage/order logic, or profitability
language.

---

## 2026-06-23 - Local CSV Readiness Input Checkpoint

This documentation-only stage adds
`docs/local_csv_readiness_input_checkpoint.md` so the readiness boundary is
explicit about what the user must provide before any future local CSV research
run can be interpreted as real-market evidence. The checkpoint lists the
required scope statement, metadata-only inventory, schema map, readiness audit,
experiment handoff draft, and explicit approval boundary, plus stop conditions
for provenance, schema, point-in-time alignment, benchmark, split,
cost/slippage, privacy, credential, and profitability-framing issues.

The handoff is updated to point future continuations at metadata-only
readiness intake if the user supplies the package, or a narrow
documentation/test-plan clarification if the user asks to continue without
local data.

Validation passed with full pytest, compileall for `src`, `tests`, and
`research`, repo map refresh, `git diff --check`, and guardrail grep. The
guardrail grep matches were documentation prohibitions, caveats, and stop
conditions only.

This stage does not modify source code, tests, research scripts, generated
reports/logs, data files, CSV loaders, backtester behavior, metrics behavior,
factor formulas, diagnostics helpers, LEAN code, real-data access, vendor APIs,
credentials, live/paper trading, brokerage/order logic, or profitability
language.

---

## 2026-06-23 - Post Local Fixture Roadmap Reconciliation

This documentation-only stage refreshes `docs/current_roadmap_gap_refresh.md`
after the synthetic and committed-local-fixture robustness/reporting sequence
completed through generated outputs. The roadmap now treats additional
synthetic output as non-default and routes the next default boundary to
user-provided local CSV readiness inputs before any real-data interpretation.

The handoff is updated to point future continuations at readiness inputs or a
documentation-only readiness-gate clarification if the user asks to continue
without local data.
Validation passed with full pytest, compileall for `src`, `tests`, and
`research`, repo map refresh, and `git diff --check`.

This stage does not modify source code, tests, research scripts, generated
reports/logs, data files, CSV loaders, backtester behavior, metrics behavior,
factor formulas, diagnostics helpers, LEAN code, real-data access, vendor APIs,
credentials, live/paper trading, brokerage/order logic, or profitability
language.

---

## 2026-06-23 - Local Fixture Configured-Case Generated-Output Refresh

This generated-output stage refreshes the committed synthetic local CSV fixture
Markdown report and JSON experiment log through the existing opt-in
configured-case summary path. The refreshed artifacts now show every configured
fixture case across train, validation, and test splits, including invalid rows
with `insufficient_metric_observations`.

The report/log keep transaction-cost, fixed-slippage, volume-aware slippage
mode, and zero-slippage diagnostic fields separate. The fields are diagnostic
metadata only; no cost or slippage model is applied to returns. The experiment
registry was regenerated by the same workflow command but did not change
because its current schema does not surface configured-case diagnostics.
Validation passed with configured-output artifact assertions, focused local
fixture workflow tests, full pytest, compileall for `src`, `tests`, and
`research`, and `git diff --check`.

This stage changes generated synthetic fixture artifacts and workflow notes
only. It does not modify behavior code, tests, CSV loaders, backtester
behavior, metrics behavior, factor formulas, diagnostics helpers, data files,
LEAN code, real-data access, vendor APIs, credentials, live/paper trading,
brokerage/order logic, or profitability language.

---

## 2026-06-23 - Opt-In Local Fixture Configured-Case Report/Log Support

This implementation stage wires the existing configured-case summary discipline
into the committed synthetic local CSV fixture workflow's optional output path.
`run_local_csv_fixture_workflow_demo()` now accepts an opt-in flag that adds an
all-case, all-split configured fixture summary to ad hoc Markdown reports and
JSON experiment logs. The default path stays unchanged so committed generated
reports, JSON logs, and the registry are not refreshed in this PR.

The summary reports `alpha_009` and `alpha_012` fixture cases across train,
validation, and test splits. Insufficient split rows remain visible with
`insufficient_metric_observations`; transaction-cost, fixed-slippage,
volume-aware slippage mode, and zero-slippage diagnostic fields remain separate
diagnostic fields and are not applied to returns.

Focused tests cover deterministic row ordering, invalid-row preservation,
Markdown output, JSON output counts, invalid reasons, and the `alpha_012`
validation coverage row. Validation passed with focused local fixture workflow
tests, full pytest, compileall for `src`, `tests`, and `research`, and
`git diff --check`. This stage does not modify CSV loaders, backtester
behavior, metrics behavior, factor formulas, diagnostics helpers, committed
generated reports/logs, data files, LEAN code, real-data access, vendor APIs,
credentials, live/paper trading, brokerage/order logic, or profitability
language.

---

## 2026-06-23 - Protected PR Merge Governance Update

This workflow-control stage updates the repository staged workflow so Codex no
longer has to stop for manual merge after every PR. The new policy keeps PRs,
branch protection, required checks, required reviews, and merge queues as the
gate. It permits GitHub auto-merge or normal protected PR merge only when risk
is not high or unclear, GitHub PR metadata verifies `minqiyang` as author/head
owner, protection is verifiable, checks pass or auto-merge handles pending
checks, no required review is pending, and changed-file scope matches the
declared stage.

The update explicitly forbids direct-pushing or direct-merging to `main`,
bypassing protection/rulesets/checks/reviews/merge queue, and using
`gh pr merge --admin`. It preserves the paused external PR gate rule for
ineligible, blocked, high-risk, unclear, or unverified PRs.

This stage is workflow/documentation-only. It does not modify source code,
tests, research scripts, generated reports/logs, data files, loaders,
backtester behavior, metrics behavior, factor logic, diagnostics helpers,
LEAN code, real-data access, vendor APIs, credentials, live/paper trading,
brokerage/order logic, or profitability language.

---

## 2026-06-22 - Local Fixture Robustness Support Checkpoint

This implementation stage adds a pure configured-case summary helper for the
committed synthetic local CSV fixture workflow. The helper produces
deterministic all-case, all-split rows, keeps invalid or missing split rows
visible with reasons, and keeps transaction-cost, fixed-slippage, volume-aware
slippage mode, and zero-slippage diagnostic fields separately inspectable.

Focused tests cover configured row ordering, missing split preservation,
invalid-case preservation, caveat retention, and separate cost/slippage fields.
The stage does not regenerate committed Markdown reports, JSON experiment logs,
or the experiment registry.

Environment note: after migration, `python` is not on `PATH`; `/usr/bin/python3`
does not have `pytest` or `pandas`; and `/Users/rhapsoul/.local/bin/pytest`
runs under Python 3.9 without `pandas`. An ignored `.venv` was created from the
Codex bundled Python and given only the missing test runner/dependency pieces
needed for focused validation. See `docs/troubleshooting_log.md` for the
failure-to-workaround chain.

Validation:

- Ignored `.venv` focused pytest passed for
  `tests/test_local_csv_fixture_workflow_demo.py` with 15 tests.
- Direct bundled-Python helper assertion passed with six all-case/all-split
  rows.
- Bundled-Python `compileall` passed for
  `research/local_csv_fixture_workflow_demo.py` and
  `tests/test_local_csv_fixture_workflow_demo.py`.
- `git diff --check` passed.
- Full pytest has not been run in this migrated Mac environment.

This stage does not modify data files, generated reports/logs, loaders,
backtester behavior, metrics behavior, factor logic, real-data access, vendor
APIs, credentials, live/paper trading, brokerage/order logic, or profitability
language.

---

## 2026-06-12 - Paused External PR Gate Governance Update

This workflow-control stage tightens the repository's PR gate behavior after
automatic goal continuations produced repeated pause messages for the same open
or not-verified-merged PR gate.

Root cause:

- Existing governance said to pause after one current-state check, but did not
  define the gate as a terminal external-wait state for the current
  continuation.
- The rule also did not prescribe the exact forced-response behavior when the
  UI or active-goal system resumes without a user-stated merge, resume, or
  inspect instruction.

Fix:

- `AGENTS.md`, `.agents/skills/staged-quant-workflow/SKILL.md`, and
  `docs/codex_long_running_controller.md` now require a paused external PR gate
  state after the first concise gate report.
- Automatic continuations without explicit user merge/resume/inspect input must
  not query GitHub, repeat gate reports, print repeated pause notes, rerun
  validation, mark complete, or mark blocked merely because the same external
  PR remains pending.
- If a response is forced during that state, the only allowed response is
  `Waiting for PR #X to merge; no checks run.`

This stage is documentation/workflow-only. It does not modify source code,
tests, research scripts, generated reports, data, loaders, backtester behavior,
metrics behavior, factor logic, diagnostics helpers, real-data access, vendor
APIs, credentials, live/paper trading, brokerage/order logic, or profitability
language.

---

## 2026-06-12 - Local Fixture Robustness Report Refresh Plan

This documentation-only stage adds a reviewed plan for applying the
all-case, split-aware synthetic robustness reporting discipline to the
committed synthetic local CSV fixture workflow before any fixture workflow,
test, research-script, or generated-output changes.

The plan records the current local fixture boundary, required future inputs,
all-case and all-split reporting behavior, invalid-row preservation,
missing/zero/stale/incomplete volume stop conditions, invalid notional and
target-weight handling, separately inspectable transaction-cost,
fixed-slippage, and volume-aware diagnostic fields, future tests, required
report/log fields, and explicit non-goals.

Validation before this plan branch:

- `python -m pytest -q` passed with 501 tests after syncing `main` at PR #109.
- `python -m compileall src tests research` passed after syncing `main` at
  PR #109.

Branch validation is pending for this stage.

This stage is documentation-only. It does not modify source code, tests,
research scripts, generated reports/logs, data loaders, backtester behavior,
metrics behavior, factor logic, diagnostics helpers, LEAN code, real-data
access, vendor APIs, credentials, live/paper trading, brokerage/order logic,
or profitability language.

---

## 2026-06-12 - Post Synthetic Robustness Generated-Output Checkpoint

This documentation-only checkpoint records the state after PR #108 merged the
synthetic split-aware robustness Markdown report, JSON experiment log, and
refreshed experiment registry.

The checkpoint preserves the reviewed sequence from plan, deterministic
all-case implementation, opt-in report/log support, PR-gate governance, and
committed generated artifacts. It also records remaining gaps before any
local-fixture robustness refresh or user-provided local CSV interpretation:
the all-case split summary format has not yet been mapped to committed local
fixtures, no real-data IC/Rank IC or benchmark-relative study exists, and
readiness/provenance gates still block user-data interpretation.

Validation before this checkpoint branch:

- `python -m pytest -q` passed with 501 tests after syncing `main` at PR #108.
- `python -m compileall src tests research` passed after syncing `main` at
  PR #108.

Checkpoint branch validation:

- Markdown fence checks passed for the checkpoint and updated workflow docs.
- Guardrail text checks confirmed no-real-data, no-vendor-API,
  no-live-trading, no-order-execution, and no-profitability boundaries.
- Scope review found no `src/`, `tests/`, `research/`, `reports/`, or `lean/`
  changes.
- `python -m pytest -q` passed with 501 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` ran.
- `git diff --check` passed before commit.

This stage is documentation-only. It does not modify source code, tests,
research scripts, generated reports/logs, data loaders, backtester behavior,
metrics behavior, factor logic, diagnostics helpers, LEAN code, real-data
access, vendor APIs, credentials, live/paper trading, brokerage/order logic,
or profitability language.

---

## 2026-06-12 - Synthetic Robustness Generated Output Refresh

This generated-output stage commits the default Markdown report, JSON
experiment log, and refreshed experiment registry for the synthetic
split-aware robustness demo after the report/log support path was reviewed and
merged.

The refresh calls the explicit `write_outputs=True` path for
`research.synthetic_split_robustness_demo` and then regenerates the synthetic
experiment registry from committed JSON logs. The committed report preserves
the all-case split summary, invalid/insufficient-case table, synthetic-only
caveats, no-real-data/no-trading guardrails, and separately inspectable
cost/slippage assumptions. The JSON log records three configured cases, nine
all-case rows, three invalid-case rows, empty metrics, and
`volume_aware_slippage_mode` as `absent`.

Validation:

- `python -m pytest tests/test_synthetic_split_robustness_demo.py -q` passed
  with 13 tests.
- Direct JSON/report content checks confirmed the expected experiment id,
  experiment type, reported/invalid case counts, nine all-case rows, three
  invalid-case rows, empty metrics, `volume_aware_slippage_mode=absent`, and
  required caveat strings.
- `python -m pytest -q` passed with 501 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` ran.
- `.\scripts\audit-skills.ps1` passed.
- `git diff --check origin/main..HEAD` passed.

This stage does not modify source code, tests, research scripts, data loaders,
backtester behavior, metrics behavior, factor logic, diagnostics helpers, LEAN
code, real-data access, vendor APIs, credentials, live/paper trading,
brokerage/order logic, or profitability language.

---

## 2026-06-12 - PR Gate Pause Rule Refresh

This workflow-control stage updates the project PR-gate rules so future
continuations pause after one current-state check when a previous-stage PR is
not verified merged.

The rule prevents repeated PR polling, protection checks, review checks,
auto-merge reclassification, baseline validation, or next-stage startup while
the same PR gate remains open, closed-unmerged, unknown, or otherwise unproven
merged. A merged PR still requires the normal `main` fast-forward and baseline
validation before any next stage begins.

This stage changes only workflow documentation and the project staged workflow
Skill. It does not modify source code, tests, research scripts, generated
reports/logs, data access, strategy logic, backtester behavior, metrics, real
data fetching, vendor APIs, credentials, live/paper trading, brokerage/order
logic, or profitability language.

---

## 2026-06-12 - Synthetic Robustness Report/Log Support

This implementation stage adds opt-in Markdown report and JSON experiment-log
support to `research/synthetic_split_robustness_demo.py` after PR #105 added
the deterministic all-case summary.

The report/log support keeps output writing explicit through `write_outputs`.
Default module execution still runs the synthetic demo without creating
committed generated artifacts. The Markdown report includes input artifacts,
split windows, parameter grid, all-case split summary, invalid/insufficient
cases, benchmark/cost/slippage assumptions, and guardrails. The JSON log uses
the existing deterministic experiment-log helper and records empty metrics,
all-case diagnostics, invalid-case diagnostics, caveats, and separately
inspectable cost, fixed-slippage, and volume-aware-slippage assumptions.

Validation:

- `python -m pytest tests/test_synthetic_split_robustness_demo.py -q` passed
  with 13 tests after updating one wording assertion to match the revised
  opt-in output caveat.
- `python -m research.synthetic_split_robustness_demo` passed without creating
  default report/log files.
- `python -m pytest -q` passed with 501 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` ran and produced no `docs/repo_map.md` diff.
- `git diff --check` passed.
- `.\scripts\audit-skills.ps1` passed.

This stage does not refresh committed generated reports/logs, modify source
package modules, change CSV loader behavior, change factor formulas, change
existing diagnostics helpers, change backtester behavior, change metrics
logic, access private data, fetch real data, add vendor APIs, add credentials,
add live or paper trading scope, add brokerage integration, add order
execution, change LEAN runtime behavior, calibrate market impact, or add
profitability language.

---

## 2026-06-12 - Synthetic Split-Aware Robustness Demo

This implementation stage adds `research/synthetic_split_robustness_demo.py`
and focused tests after the reviewed synthetic robustness validation plan.

The demo reuses the existing deterministic split-aware synthetic factor and
forward-return panels, then reports every configured signal case across train,
validation, and test windows. The default cases are an identity signal, inverse
signal, and constant invalid signal. The summary is sorted by stable case and
split order, includes every case/split row, preserves missing values, records
invalid reasons for undefined IC/Rank IC diagnostics, and keeps assumptions for
benchmark, costs, fixed-bps slippage, volume-aware slippage, portfolio
construction, and backtest integration separately inspectable.

Assumption: this PR deliberately avoids generated report/log changes so the
review can focus on deterministic all-case implementation and tests. A later
stage can add report/log output or committed generated artifacts if explicitly
scoped.

Validation:

- `python -m pytest tests/test_synthetic_split_robustness_demo.py -q` passed
  with 10 tests.
- `python -m research.synthetic_split_robustness_demo` passed without writing
  outputs.
- `python -m pytest -q` passed with 498 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` refreshed `docs/repo_map.md`.
- `git diff --check` passed.
- `.\scripts\audit-skills.ps1` passed.
- Guardrail grep found only prohibition, caveat, and test assertion wording.

This stage does not modify source package modules, generated reports/logs, CSV
loader behavior, factor formulas, existing diagnostics helpers, backtester
behavior, metrics logic, private data, real-data access, vendor APIs,
credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact calibration, or profitability
language.

---

## 2026-06-12 - Synthetic Robustness And Split-Aware Validation Plan

This documentation-only stage adds
`docs/synthetic_robustness_validation_plan.md` after the roadmap refresh
identified robustness and split-aware validation policy as the next blocker.

Assumption: after PR #103 merged and synced `main` passed baseline validation,
the next safe stage was a plan for robustness reporting, not implementation,
generated-output refresh, real-data interpretation, or LEAN/runtime work.

The plan defines required inputs, chronological split policy, all-case
robustness reporting behavior, missing-data and insufficient-window stop
conditions, future deterministic test coverage, future experiment-log fields,
and future Markdown report fields. It keeps fixed-bps transaction costs,
fixed-bps slippage, and volume-aware diagnostics or precomputed impacts
separately inspectable.

Validation:

- `python -m pytest -q` passed with 488 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` refreshed `docs/repo_map.md` for the new plan.
- `git diff --check` passed.
- `.\scripts\audit-skills.ps1` passed.
- Guardrail grep found only existing prohibition, caveat, and policy wording.

This stage does not modify source code, tests, research scripts, generated
reports/logs, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics logic, private data, real-data access, vendor
APIs, credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact calibration, or profitability
language.

---

## 2026-06-12 - Post-Volume-Aware Roadmap Gap Refresh

This documentation-only stage refreshes `docs/current_roadmap_gap_refresh.md`
after the split, liquidity, fixed-bps slippage, volume-aware diagnostic,
precomputed-impact, generated-log, and checkpoint stages.

Assumption: after PR #102 merged, no open PR gate remained, and synced `main`
passed baseline validation, the next safe stage was the checkpoint-recommended
roadmap refresh, not source code, tests, research-script changes,
generated-output changes, real-data workflows, or LEAN/runtime work.

The refreshed roadmap records the current implementation traceability,
remaining original-goal gaps, guardrail state, and recommended next roadmap.
The next recommended PR-sized stage is a documentation-only synthetic
robustness and split-aware validation plan before any implementation or
generated-output refresh.

Validation:

- `python -m pytest -q` passed with 488 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` ran and produced no `docs/repo_map.md` diff.
- `git diff --check` passed.
- `.\scripts\audit-skills.ps1` passed.

This stage does not modify source code, tests, research scripts, generated
reports/logs, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics logic, private data, real-data access, vendor
APIs, credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact calibration, or profitability
language.

---

## 2026-06-11 - Post Precomputed Volume-Aware Slippage Checkpoint

This documentation-only checkpoint records the completed PR #98 through
PR #101 sequence for volume-aware slippage backtester integration:
documentation-only design, documentation-only test plan, precomputed-impact
implementation, and synthetic generated-log refresh.

Assumption: after PR #101 merged and synced `main` passed baseline validation,
the next safe stage was the handoff-recommended checkpoint, not new code,
research-script changes, generated-output changes, real-data workflows, or
LEAN/runtime work.

`docs/post_precomputed_volume_aware_slippage_checkpoint.md` records the
baseline, completed implementation and generated-log state, guardrail review,
remaining gaps, and recommended next roadmap. The recommendation is a
documentation-only post-volume-aware roadmap gap refresh because
`docs/current_roadmap_gap_refresh.md` predates several completed split,
liquidity, fixed-bps slippage, volume-aware diagnostic, precomputed-impact, and
generated-log stages.

This stage does not modify source code, tests, research scripts, generated
reports/logs, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics logic, private data, real-data access, vendor
APIs, credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact calibration, or profitability
language.

Validation:

- `python -m pytest -q` passed with 488 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` refreshed `docs/repo_map.md` for the new
  checkpoint document.
- `git diff --check origin/main..HEAD` passed.
- `.\scripts\audit-skills.ps1` passed.

---

## 2026-06-11 - Synthetic Volume-Aware Slippage Generated-Log Refresh

This generated-output stage refreshes the committed synthetic experiment logs
after PR #100 added the default `total_volume_aware_slippage_cost_impact`
metric to the local backtester result metrics.

Assumption: after PR #100 merged and synced `main` passed baseline validation,
the next safe stage was the handoff-recommended generated-output review or
refresh for synthetic/local-fixture artifacts, not source code, tests, research
script behavior, real-data workflows, or LEAN/runtime work.

`python research\synthetic_momentum_demo.py` completed and refreshed the
synthetic momentum experiment log. Direct file invocation of
`research\synthetic_combined_score_backtest_demo.py` and
`research\synthetic_multifactor_parameter_sweep.py` failed with
`ModuleNotFoundError: No module named 'research'` because those scripts import
package-qualified `research.*` modules. Rerunning them as
`python -m research.synthetic_combined_score_backtest_demo` and
`python -m research.synthetic_multifactor_parameter_sweep` completed
successfully. No source or research-script changes were needed.

Only these committed synthetic JSON experiment logs changed:

- `reports/experiment_logs/synthetic_momentum_demo.json`
- `reports/experiment_logs/synthetic_combined_score_backtest_demo.json`

Both now include `total_volume_aware_slippage_cost_impact: 0.0` in the metrics
payload. The synthetic parameter sweep produced no committed diff, and no
Markdown report or experiment-registry file changed.

This stage does not modify source code, tests, research scripts, CSV loader
behavior, factor formulas, diagnostics semantics, backtester behavior, metrics
logic, private data, real-data access, vendor APIs, credentials, live or paper
trading scope, brokerage integration, order execution, LEAN runtime behavior,
market-impact calibration, or profitability language.

Validation:

- `python -m pytest -q` passed with 488 tests.
- `python -m compileall src tests research` passed.
- `python scripts/repo_map.py` ran and produced no `docs/repo_map.md` diff.
- `git diff --check origin/main..HEAD` passed.
- `.\scripts\audit-skills.ps1` passed.

---

## 2026-06-11 - Precomputed Volume-Aware Slippage Backtester Integration

This code-changing stage implements the reviewed precomputed-impact boundary
for volume-aware slippage without moving OHLCV or rolling dollar-volume
calculation into the backtester.

Assumption: after PR #99 merged and synced `main` passed baseline validation,
the next safe stage was the narrow implementation described by
`docs/volume_aware_slippage_backtester_integration_test_plan.md`, with
deterministic tests in the same PR and no generated-output refresh.

`run_long_only_backtest()` now keeps `volume_aware_slippage_mode` at
`diagnostic_only` by default. A caller may explicitly use
`apply_precomputed_impact` with an aligned precomputed impact series and
required audit metadata. Applied impact is recorded in a separate
`volume_aware_slippage_costs` series, included in total trading impact, and
reported through a separate metric while fixed transaction costs and fixed-bps
slippage remain separately inspectable.

The implementation rejects invalid impact indexes, missing or negative impact
values, missing required metadata, invalid modes, and positive fixed-bps
slippage combined with positive applied volume-aware impact. Tests also cover
the integration path where `calculate_volume_aware_slippage_diagnostics()`
feeds the precomputed boundary from outside the backtester.

This stage does not modify data loaders, feature logic, diagnostics helper
behavior, research scripts, generated reports, real-data access, vendor APIs,
credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact calibration, or profitability
language.

---

## 2026-06-11 - Volume-Aware Slippage Backtester Integration Test Plan

This documentation-only stage defines the test coverage required before any
future implementation applies volume-aware slippage to simulated local
backtester returns.

Assumption: after PR #98 merged and `main` was synced, the next safe stage is a
test plan, not source code changes, test file changes, research script changes,
generated report changes, backtester integration, or metrics changes.

`docs/volume_aware_slippage_backtester_integration_test_plan.md` records the
required unit tests, integration tests, failure-mode tests, edge-case expected
behavior, zero-slippage diagnostic behavior, separate inspection requirements,
future result/audit fields, experiment-log/report fields, guardrail tests,
stop conditions, and the recommended next PR-sized stage.

The plan keeps helper calculation outside the backtester for the first future
implementation, keeps `diagnostic_only` as default, and requires deterministic
tests in the same PR as any later precomputed-impact implementation.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, vendor APIs,
credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact modeling, or profitability
language.

---

## 2026-06-11 - Volume-Aware Slippage Backtester Integration Design

This documentation-only stage defines whether and how the existing
volume-aware slippage diagnostic helper could later affect simulated local
backtester net returns.

Assumption: after PR #97 merged and `main` was synced, the next safe stage is a
design boundary, not source code changes, test changes, research script
changes, generated report changes, or backtester integration.

`docs/volume_aware_slippage_backtester_integration_design.md` records the
problem statement, diagnostic-only rationale, required inputs, recommended
future precomputed-impact integration shape, return/cost/audit semantics,
strict defaults and stop conditions, required tests, experiment-log/report
fields, non-goals, and the recommended next PR-sized stage.

The design recommends keeping `diagnostic_only` as the default and deferring
any `run_long_only_backtest()` integration until a separate test-plan stage is
reviewed. If implemented later, the first integration should pass a validated,
date-aligned `portfolio_slippage_impact` series and audit metadata into the
backtester or wrapper rather than making the backtester own OHLCV validation.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, vendor APIs,
credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact modeling, or profitability
language.

---

## 2026-06-11 - Post Local Fixture Slippage Output Refresh Checkpoint

This documentation-only checkpoint records the repository state after PR #94
refreshed the synthetic local CSV fixture generated outputs and PRs #95/#96
added and refined the context-budget retrieval policy.

Assumption: after syncing `main` to PR #96, verifying no open PR gates, and
passing baseline validation, the next safe stage is a checkpoint before any
backtester net-return integration design. It is not source code changes, CSV
loader changes, research script changes, generated report changes,
user-provided local CSV interpretation, or LEAN/runtime work.

`docs/post_local_fixture_slippage_output_refresh_checkpoint.md` records the
reviewed baseline, completed volume-aware slippage design/helper/smoke/output
refresh sequence, diagnostic-only boundary, remaining gaps, guardrail review,
and recommended next roadmap. The recommendation is a documentation-only
volume-aware slippage backtester integration design after this checkpoint is
reviewed and merged.

`docs/current_handoff.md` now routes future continuations through this
checkpoint PR, and `docs/repo_map.md` is refreshed because a docs file was
added.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, vendor APIs,
credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact modeling, or profitability
language.

---

## 2026-06-11 - Context Budget Policy For Staged Workflow

This workflow-control update adds a context-budget and retrieval policy to the
long-running controller and staged workflow Skill after a continuation
encountered tool-output truncation while reading too much context at once.

The policy limits first-pass context to the handoff, repo map, governing agent
rules, project spec, controller, and staged workflow Skill; defines a
retrieval ladder from git/PR state through targeted log searches; discourages
parallel broad reads of long logs, reports, experiment JSON, and checkpoint
documents; and requires targeted rereads after truncation.

Follow-up refinement: the short-entry files are now explicitly maintained as
retrieval controls. `docs/current_handoff.md` should stay around 100-200 lines,
`docs/repo_map.md` should remain an index rather than history, and long logs
plus `CHANGELOG.md` should be accessed by tail, keyword search, stats, or small
line ranges by default.

This stage changes workflow documentation and logs only. It does not modify
source code, tests, research scripts, generated reports, CSV loader behavior,
backtester behavior, metrics, alpha files, normalization, combination,
diagnostics, `PROJECT_SPEC.md`, real-data access, vendor APIs, credentials,
trading scope, order execution, or profitability language.

---

## 2026-06-10 - Local Fixture Slippage Generated-Output Refresh

This generated-output refresh syncs the committed synthetic local CSV fixture
report, JSON experiment log, and experiment registry after PR #92 added the
volume-aware slippage smoke diagnostic and PR #93 recorded the checkpoint.

Assumption: after PR #93 merged and no open PR gate remained, the next safe
stage was the checkpoint-recommended generated-output refresh, not source code
changes, backtester net-return integration, user-provided local CSV
interpretation, or LEAN/runtime work.

`python research/local_csv_fixture_workflow_demo.py` was run from the project
root. It uses committed synthetic fixtures under
`tests/fixtures/local_csv_loader_smoke` and updates:

- `reports/local_csv_fixture_workflow_demo.md`
- `reports/experiment_logs/local_csv_fixture_workflow_demo.json`
- `reports/experiment_registry.md`

The refreshed artifacts now include the volume-aware slippage smoke diagnostic
assumptions, participation and rejected/cap counts, and caveats that the
diagnostic is not applied to returns and is not a trading-cost conclusion.

This stage does not modify source code, tests, research scripts, CSV loader
behavior, factor formulas, diagnostics semantics, backtester behavior, metrics,
private data, real-data access, vendor APIs, credentials, live or paper trading
scope, brokerage integration, order execution, LEAN runtime behavior,
market-impact modeling, or profitability language.

Validation before PR creation:

- `python -m pytest -q` - 478 passed before the refresh branch.
- `python -m compileall src tests research` - passed before the refresh branch.
- Full final validation is recorded in the PR summary after the final gate.

---

## 2026-06-09 - Post Volume-Aware Slippage Smoke Checkpoint

This documentation-only checkpoint records the repository state after PR #92
merged the committed synthetic local CSV fixture smoke diagnostic for
volume-aware slippage.

Assumption: after syncing `main` to PR #92 and verifying no open PR gates,
the next safe stage is a checkpoint, not generated-output refresh,
backtester net-return integration, user-provided local CSV interpretation,
or LEAN/runtime work. The checkpoint should make the next step explicit before
any committed reports/logs are regenerated.

`docs/post_volume_aware_slippage_smoke_checkpoint.md` now records the reviewed
baseline, completed design/helper/smoke sequence, diagnostic-only boundary,
remaining gaps, guardrail review, and recommended next roadmap. The
recommendation is a narrow synthetic local CSV fixture generated-output
refresh so committed report/log artifacts reflect the new smoke diagnostic.

`docs/decision_log.md` records the durable decision to refresh local fixture
generated outputs before considering any backtester slippage integration.
`docs/current_handoff.md` is updated so future continuations pause at this
checkpoint PR and, after merge, route to the generated-output refresh stage.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, vendor APIs,
credentials, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, market-impact modeling, or profitability
language.

Validation before PR creation:

- `python -m pytest -q` - 478 passed.
- `python -m compileall src tests research` - passed.
- Full final validation is recorded in the PR summary after the final gate.

---

## 2026-06-09 - Local Fixture Volume-Aware Slippage Smoke Diagnostic

This code milestone wires the reviewed volume-aware slippage diagnostic helper
into the committed synthetic local CSV fixture workflow as a smoke diagnostic
only.

Assumption: after PR #91 merged and no open PR gate remained, the next safe
stage was the handoff-recommended synthetic/local-fixture smoke diagnostic
that reports participation and rejected/cap counts only. It should not
integrate volume-aware slippage into backtester net returns, generated
performance interpretation, real-data workflows, LEAN runtime behavior, or
trading/execution code.

`research/local_csv_fixture_workflow_demo.py` now builds a tiny deterministic
two-date target-weight panel from complete synthetic OHLCV fixture rows, calls
`calculate_volume_aware_slippage_diagnostics()`, and stores a reduced smoke
summary containing trade count, trade weight/notional, max participation,
missing/zero/zero-window rejection counts, total rejected-capacity count, and
participation-cap breach count. The workflow intentionally does not report or
apply candidate slippage impact to returns.

`tests/test_local_csv_fixture_workflow_demo.py` now verifies the fixed target
weights, date/asset alignment, helper invocation, deterministic participation
summary, Markdown report caveats, JSON experiment-log diagnostics, and
invalid slippage-smoke config rejection.

This stage does not modify `src/backtest/portfolio.py`,
`src/backtest/metrics.py`, the CSV loader, alpha formulas, normalization,
combination, diagnostics helpers, generated reports, user data, real-data
access, vendor APIs, credentials, live or paper trading scope, brokerage
integration, order execution, or profitability language.

Validation before PR creation:

- `python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py` - 14
  passed.
- `python -m pytest -q tests/test_volume_aware_slippage.py` - 17 passed.
- Full validation recorded in the PR summary after the final gate.

Troubleshooting note: this stage also recorded an output-truncation and patch
context recovery chain in `docs/troubleshooting_log.md`. The final
implementation used capped reads and smaller patches.

---

## 2026-06-09 - Volume-Aware Slippage Diagnostic Helper

This code milestone adds a standalone synthetic-only diagnostic helper for
volume-aware slippage assumptions after PR #90's design gate merged.

Assumption: the next safe stage is a narrow helper and deterministic tests, not
backtester net-return integration, generated-output refresh, local CSV
interpretation, or LEAN/runtime work. The helper should make notional,
liquidity lag, participation, missing-data, zero-volume, and cap assumptions
explicit before any later stage decides whether those diagnostics should
affect simulated returns.

`src/backtest/slippage.py` now exposes
`calculate_volume_aware_slippage_diagnostics()` and
`VolumeAwareSlippageDiagnostics`. The helper calculates target-weight trade
changes, lagged rolling dollar volume, trade notional, participation,
candidate asset-level slippage basis points, asset-level slippage impact, and
portfolio-level slippage impact. It requires explicit `portfolio_notional`,
uses rolling dollar volume shifted by `volume_lag`, and raises by default for
missing capacity, non-positive capacity, incomplete or zero-volume windows,
participation above cap, invalid target weights, and invalid parameters.

`tests/test_volume_aware_slippage.py` adds hand-calculated deterministic
coverage for the diagnostic calculation, lagged capacity rather than same-day
volume, required notional, warm-up capacity failures, missing price/volume,
zero-volume windows, zero lagged dollar volume, participation caps, panel
alignment, target-weight validation, invalid parameters, and forbidden import
guardrails.

This stage does not modify `src/backtest/portfolio.py`,
`src/backtest/metrics.py`, research scripts, generated reports, CSV loader
behavior, factor formulas, diagnostics semantics, private data, real-data
access, execution behavior, live or paper trading scope, brokerage
integration, order execution, LEAN runtime behavior, market-impact modeling,
or profitability language.

Validation:

- `python -m pytest -q tests/test_volume_aware_slippage.py` - 17 passed.
- `python -m pytest -q` - 478 passed.
- `python -m compileall src tests research` - passed.
- `python scripts/repo_map.py` - wrote `docs/repo_map.md`.
- `git diff --check` - passed with only Windows LF/CRLF notices.

Warning recovery:

- Original implementation used `.fillna(False)` on the shifted
  `positive_volume_window` boolean mask.
- Consequence: focused tests passed, but pandas emitted a `FutureWarning`
  about silent downcasting on `.fillna`, which could become brittle in a
  future pandas release.
- Evidence: `python -m pytest -q tests/test_volume_aware_slippage.py` reported
  17 passed with warnings from `src/backtest/slippage.py`.
- Investigation: the shifted rolling-window mask can carry missing values and
  object dtype after lagging. The helper only needs to treat literal `True` as
  valid capacity.
- Final fix: replace `.fillna(False)` with `.eq(True)`, avoiding silent
  downcasting while keeping missing values ineligible.
- Verification: focused helper tests were rerun and passed without warnings;
  full pytest also passed with 478 tests.
- Prevention: prefer explicit boolean comparisons for lagged nullable masks
  instead of relying on pandas fill/downcast behavior.

---

## 2026-06-09 - Volume-Aware Slippage Design Gate

This documentation-only design stage defines the boundary for any future
volume-aware slippage work after the fixed-bps slippage sequence and
token-efficient workflow controls merged.

Assumption: after PR #89 merged and the open-PR gate was clear, the current
handoff and checkpoint documents still identify volume-aware slippage design
as the next safe repository-internal stage. The correct next step is not a
helper implementation, generated-output refresh, local CSV interpretation, or
LEAN/runtime integration.

`docs/volume_aware_slippage_design.md` now records the required future input
contract, lagged liquidity-reference policy, candidate participation and
slippage-impact semantics, portfolio-notional requirement, zero/missing/stale
volume policy, participation-cap policy, adjustment-policy constraints,
future reporting fields, required tests, module alignment, and risks.

`docs/decision_log.md` records the durable decision that volume-aware slippage
requires explicit lagged dollar-volume, notional, missing-data, cap, and
adjustment-policy semantics before code. `docs/current_handoff.md` is updated
so the next continuation starts from the current post-PR #89 state.
`CHANGELOG.md` records the user-visible design document addition.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
behavior, live or paper trading scope, brokerage integration, order execution,
LEAN runtime behavior, market-impact modeling, or profitability language.

Validation:

- `python -m pytest -q` - 461 passed.
- `python -m compileall src tests research` - passed.
- `python -m compileall lean` - passed.
- `.\scripts\audit-skills.ps1` - passed for 2 Skill files.
- `python scripts/repo_map.py` - wrote `docs/repo_map.md`.
- `git diff --check` - passed with only Windows LF/CRLF notices.

---

## 2026-06-09 - Token-Efficient Codex Workflow Controls

This documentation and workflow-tooling milestone adds a short durable handoff
and capped-output rules so future staged Codex runs can spend less context on
stable repository state while preserving review quality.

Assumption: after PR #88 merged, the next safe stage is workflow-control only.
The current open-PR gate was clear at branch creation, and no research source,
tests, research scripts, generated reports, CSV loader, backtester, metrics,
alpha files, normalization, combination, diagnostics, LEAN code, real-data
access, broker/order behavior, credentials, or `PROJECT_SPEC.md` changes are
needed to improve Codex context discipline.

`docs/current_handoff.md` now provides the first-read project state summary.
`scripts/repo_map.py` reads repository paths and writes only
`docs/repo_map.md`, skipping cache/build directories, generated reports, and
large artifacts by default. `AGENTS.md`, the long-running controller, and the
staged workflow Skill now require handoff-first startup, capped output for
unknown large commands, targeted inspection of temp-file captures when full
output is needed, and no full generated-report or large-log printing by
default.

Validation before commit:

- `python -m pytest -q` - 461 passed.
- `python -m compileall src tests research` - passed.
- `.\scripts\audit-skills.ps1` - passed for 2 Skill files.
- `python scripts/repo_map.py` - wrote `docs/repo_map.md`.
- `git diff --check` - passed before commit.

Workflow recovery:

- Original assumption: the GitHub connector could create the PR after the
  branch was pushed.
- Consequence: PR creation stopped on the connector path.
- Evidence: the connector returned `403 Resource not accessible by
  integration`.
- Investigation: `gh repo view` confirmed the canonical repository is
  `minqiyang/equity-factor-research` with base branch `main`, and the branch
  had already pushed successfully.
- Correction attempt and final fix: used the documented GitHub CLI fallback
  with a temp Markdown body file, and `gh pr create` opened ready-for-review
  PR #89.
- Verification: the PR URL was returned by `gh`; future runs should continue
  to fall back to `gh pr create` when the connector returns this 403.

---

## 2026-06-09 - Post Slippage And Cost Checkpoint

This documentation checkpoint records the repository state after the fixed-bps
slippage design, implementation, and synthetic report/log refresh merged.

Assumption: after PR #87 merged, the previous checkpoint's recommended
slippage/cost sequence is complete. The safest next stage is not a direct
volume-aware implementation and not a user-provided local CSV run. The safe
repository-internal stage is a checkpoint that marks fixed-bps slippage as
reflected in code and generated synthetic outputs, then routes any broader
slippage work through a new design gate.

`docs/post_slippage_cost_checkpoint.md` now records the current review
baseline, completed slippage/cost state, remaining original-goal gaps,
guardrail review, and recommended next roadmap. It recommends a
documentation-only volume-aware slippage design before any helper,
backtester-extension, generated-output, or local CSV interpretation stage.

`docs/decision_log.md` records the durable decision to require a
volume-aware slippage design before implementation. `CHANGELOG.md` records the
user-visible checkpoint addition.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
assumptions, live or paper trading scope, brokerage integration, order
execution, LEAN runtime behavior, volume-aware slippage implementation,
market-impact modeling, or profitability language.

Validation:

- `python -m pytest -q` - 461 passed.
- `python -m compileall src tests research` - passed.
- `git diff --check` - passed with only Windows LF/CRLF notices.

---

## 2026-06-09 - Synthetic Backtest Slippage Report/Log Refresh

This generated-output milestone refreshes the synthetic backtest demos after
the fixed-bps slippage backtester extension merged.

Assumption: after `run_long_only_backtest()` began exposing separate
transaction cost, slippage, and total trading impact fields, generated
synthetic backtest reports and JSON logs should no longer say slippage is "not
separately modeled." The safest next stage is to update synthetic outputs only,
preserving the existing default `slippage_bps=0.0` as an explicit diagnostic
simplification rather than changing synthetic return paths.

Updated synthetic backtest generators now carry `slippage_bps` in their config,
pass it into the local backtester, record the fixed-bps cost and slippage model
names, record `zero_cost_or_slippage_is_diagnostic`, and include total
slippage cost impact and total trading cost impact in reports/logs. The
experiment registry was regenerated from the updated JSON logs so the registry
shows current fixed-bps cost/slippage assumptions.

`docs/simulated_slippage_cost_assumption_design.md` and
`docs/quantconnect_lean_plan.md` were narrowly refreshed so current roadmap and
planning documents no longer say local slippage is unimplemented. The LEAN plan
still distinguishes local target-weight turnover friction from LEAN
order/fill-level fee and slippage models.

This stage does not change backtester logic, factor formulas, CSV loaders,
local user-data handling, generated private data, real-data access, live or
paper trading scope, brokerage integration, order execution, LEAN runtime
behavior, volume-aware slippage, market-impact modeling, or profitability
language.

Validation:

- `python -m pytest -q tests/test_synthetic_momentum_demo.py tests/test_synthetic_combined_score_backtest_demo.py tests/test_synthetic_multifactor_parameter_sweep.py tests/test_experiment_registry.py` - 27 passed.
- `python -m pytest -q` - 461 passed.
- `python -m compileall src tests research` - passed.
- `git diff --check` - passed with only Windows LF/CRLF notices.

---

## 2026-06-09 - Fixed-Bps Slippage Backtester Extension

This code milestone implements the narrow fixed-basis-point slippage extension
designed in `docs/simulated_slippage_cost_assumption_design.md`.

Assumption: after the slippage and cost assumption design merged, the next safe
code stage is the first fixed-bps implementation only. The implementation
should preserve the existing target-weight turnover model, keep transaction
cost and slippage as separate impact series, keep total trading impact
inspectable, and avoid volume-aware slippage, market impact, generated report
updates, real data, broker fills, order execution, or performance
interpretation.

`run_long_only_backtest()` now accepts `slippage_bps` with default `0.0`.
Slippage impact is calculated as target-weight turnover times
`slippage_bps / 10000`, separately from `transaction_cost_bps`, and both are
deducted from simulated net returns. `BacktestResult` now exposes
`slippage_costs` and `total_trading_costs` in addition to the existing
`transaction_costs`. Backtest assumptions now record the cost model, slippage
model, `slippage_bps`, and whether a zero cost or zero slippage setting is a
diagnostic simplification.

`calculate_basic_metrics()` now records total transaction cost impact, total
slippage cost impact, and total trading cost impact when the relevant series
are supplied. Focused tests cover separate transaction cost and slippage
deduction, zero-cost or zero-slippage diagnostic labeling, first-row slippage
impact with `signal_lag_periods=0`, positive combined impact, and validation
that negative `slippage_bps` raises.

This stage does not modify research scripts, generated reports, CSV loader
behavior, factor formulas, diagnostics semantics, private data, real-data
access, live or paper trading scope, brokerage integration, order execution,
LEAN runtime behavior, volume-aware slippage, market-impact modeling, or
profitability language.

Validation:

- `python -m pytest -q tests/test_backtest_portfolio.py` - 17 passed.
- `python -m pytest -q` - 461 passed.
- `python -m compileall src tests research` - passed.
- `git diff --check` - passed with only Windows LF/CRLF notices.

---

## 2026-06-09 - Simulated Slippage And Cost Assumption Design

This documentation milestone defines the reviewed boundary for future local
backtester cost and slippage expansion.

Assumption: after the post-local-CSV-fixture audit rehearsal checkpoint merged,
the safest repository-internal next stage is not a code change. The current
backtester has deterministic target-weight turnover costs through
`transaction_cost_bps`, but it does not separately represent slippage or market
impact. A design gate keeps transaction cost, slippage, zero-slippage
diagnostics, market-impact caveats, experiment-log fields, and future tests
reviewable before source code changes.

`docs/simulated_slippage_cost_assumption_design.md` now records current
backtester semantics, non-goals, definitions, design principles, a proposed
fixed-basis-point slippage boundary, deferred volume-aware slippage and market
impact scope, future experiment-log fields, required tests, module alignment,
risks, and recommended next stages.

`docs/decision_log.md` records the durable decision to require this design
before cost/slippage implementation. `CHANGELOG.md` records the user-visible
documentation addition.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
assumptions, live or paper trading scope, brokerage integration, order
execution, or profitability language.

Validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Post Local CSV Fixture Audit Rehearsal Checkpoint

This documentation milestone records the repository state after the committed
synthetic local CSV fixture readiness audit rehearsal merged.

Assumption: no user-provided local CSV bundle, completed user-data checklist,
completed inventory review, completed readiness audit report, or prepared
user-data `EXPERIMENT_LOG.md` entry is available in the current repository
context. The next safe stage is therefore not a real local CSV smoke run. The
safe repository-internal stage is a checkpoint that closes the local CSV
readiness-artifact sequence for now and selects the next non-user-data
roadmap item.

`docs/post_local_csv_fixture_audit_rehearsal_checkpoint.md` now records the
post-PR #83 review baseline, completed local CSV readiness artifacts, remaining
user-data gates, original-goal gaps, guardrail review, and recommended next
stage. It recommends a documentation-only simulated slippage and cost
assumption design before any backtester cost/slippage code changes.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
assumptions, live or paper trading scope, brokerage integration, order
execution, or profitability language.

Validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Local CSV Fixture Readiness Audit Rehearsal

This documentation milestone fills the manual local CSV readiness audit report
format using the already-committed synthetic local CSV fixture workflow.

Assumption: after the post-readiness-gates checkpoint merged, no user-provided
local CSV bundle, completed user-data checklist, or completed user-data audit
is available. The next safe repository-internal stage is therefore not a real
local CSV smoke run. A synthetic-only audit rehearsal can still move the
project forward by proving that the new audit report format can represent
known fixture evidence, issue levels, limitations, and gate decisions without
crossing into user-data interpretation.

`docs/local_csv_fixture_readiness_audit_rehearsal.md` now records the audit
identity, fixture input inventory, schema and loader evidence, provenance and
adjustment policy, universe and benchmark review, date-alignment review,
sample split and execution assumptions, low issue register, gate decision, and
experiment-log handoff for the committed synthetic fixture workflow.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
assumptions, live or paper trading scope, brokerage integration, order
execution, or profitability language.

Validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Post Local CSV Readiness Gates Checkpoint

This documentation milestone records the repository state after the local CSV
study checklist, metadata-only inventory dry-run validator, committed synthetic
fixture rehearsal, and manual readiness audit report template merged.

Assumption: after PR #81 merged, the next safe stage is not an actual
user-provided local CSV smoke run because no user-supplied local CSV bundle,
completed scope statement, completed checklist, completed readiness audit
report, or local CSV `EXPERIMENT_LOG.md` entry exists in the repository
context. The safest PR-sized stage is a checkpoint that distinguishes
"readiness gates are available" from "a user-provided dataset is ready for
interpretation."

`docs/post_local_csv_readiness_gates_checkpoint.md` now records the current
review baseline, completed local CSV readiness artifacts, readiness assessment,
remaining stop conditions, guardrail review, and recommended next stage under
two conditions: no user data available, or a future user-supplied local CSV
bundle available outside the repository.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
assumptions, live or paper trading scope, brokerage integration, order
execution, or profitability language.

Validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Local CSV Readiness Audit Report Template

This documentation milestone adds the next manual gate after the committed
synthetic fixture inventory rehearsal.

Assumption: the safest PR-sized next stage is still documentation-only. The
project already has a study checklist, metadata-only inventory dry-run
validator, and synthetic fixture rehearsal. The remaining stage named in the
user-provided local CSV plan is a manually fillable real-data readiness audit
report format that records evidence, high/medium/low issues, stop conditions,
and the final gate decision before any user-provided local CSV result is
interpreted.

`docs/local_csv_readiness_audit_report_template.md` now provides that report
format. It covers audit identity, redacted input inventory, schema and loader
validation evidence, provenance and adjustment policy, universe and benchmark
review, date alignment and timing, sample splits, parameter policy, costs,
slippage, issue register, gate decision, experiment-log handoff, and final stop
statements. The template explicitly states that local CSV diagnostics are not
profitability evidence and that unresolved high or medium issues stop
interpretation.

This stage does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, factor formulas, diagnostics semantics,
backtester behavior, metrics, private data, real-data access, execution
assumptions, live or paper trading scope, brokerage integration, order
execution, or profitability language.

Validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Local CSV Fixture Inventory Dry-Run Rehearsal

This code-and-report milestone connects the local CSV inventory dry-run
validator to the committed synthetic fixture workflow.

Assumption: after the metadata-only inventory validator merged, the safest
PR-sized next stage is a synthetic fixture rehearsal of the user-provided
local CSV research plan. The rehearsal should prove that declared local CSV
inventory metadata can be reviewed and reported before loader output is
interpreted, while still avoiding user-provided files, downloads, vendor APIs,
credentials, trading behavior, and profitability language.

`research/local_csv_fixture_workflow_demo.py` now builds a metadata-only
inventory declaration for the committed synthetic adjusted-close, benchmark,
and OHLCV fixtures and runs `validate_local_csv_inventory()` before loading
those fixtures. The workflow result, Markdown report, and JSON sidecar log now
include redacted inventory review summaries and issue counts. The review
records metadata flags only; it does not store raw local paths in its result,
read files, check path existence, compute hashes, fetch data, or authorize
real-data interpretation.

`tests/test_local_csv_fixture_workflow_demo.py` now verifies the inventory
review has three declared inputs, no high/medium/low issues for the committed
synthetic fixture metadata, no raw-path field on review summaries, deterministic
review output, report/log inventory sections, helper reuse, and caveats.

The generated report and JSON experiment log were regenerated from committed
synthetic fixtures only. This stage does not modify CSV loader behavior, factor
formulas, diagnostics semantics, backtester behavior, metrics, private data,
real-data access, execution assumptions, live or paper trading scope,
brokerage integration, order execution, or profitability language.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
14 passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Local CSV Inventory Dry-Run Validator

This code milestone adds the next local CSV planning gate after the study
checklist template merged.

Assumption: the safest PR-sized next stage is a metadata-only dry-run
validator for a declared local CSV inventory. The helper should review the
declared file labels, schema labels, provenance fields, version/hash evidence,
known-manual-edit disclosure, remote path markers, and credential-like path
markers before any user file is loaded. It should not read files, check path
existence, compute file hashes, write reports, store raw paths in its review
result, fetch data, or interpret research output.

`src/data/local_csv_inventory.py` now exposes
`validate_local_csv_inventory()` plus redacted review, summary, and issue
dataclasses. The result deliberately stores per-input metadata flags rather
than raw local paths so later reports can cite inventory readiness without
leaking private filesystem details. High or medium issues keep the future
local CSV workflow stopped before loading or interpreting data.

`tests/test_local_csv_inventory.py` covers valid inventory metadata, raw-path
redaction, missing required fields, hash or hash-plan version evidence,
unknown schemas, remote paths, credential-like path markers, non-CSV path
warnings, redacted CSV placeholders, duplicate input names, invalid inventory
shape, and absence of file I/O, remote-data, vendor, broker, order, or live
trading imports.

This stage does not modify CSV loaders, factor helpers, diagnostics,
backtester behavior, metrics, research scripts, generated reports, strategy
logic, real data access, execution assumptions, live or paper trading scope,
brokerage integration, order execution, or profitability language.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_inventory.py
19 passed

python -m pytest -q
453 passed

python -m compileall src tests research
passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - Local CSV Study Checklist Template

This documentation milestone adds the first concrete checklist template after
the user-provided local CSV research plan merged.

Assumption: the safest PR-sized next stage is still documentation-only. The
project should prepare a reusable pre-run checklist before any stage loads,
validates, diagnoses, reports, or interprets user-provided local CSV files.

`docs/local_csv_study_checklist.md` now provides a copyable checklist for
scope, file inventory, schema mapping, provenance, adjustment policy,
validation evidence, universe and benchmark assumptions, feature timing,
sample splits, costs, slippage, readiness-audit summary, experiment-log
preparation, and final stop conditions. It is designed to be completed before
any user file is loaded, and it explicitly keeps downloads, vendor APIs,
credentials, live or paper trading, brokerage integration, order execution,
silent missing-data repair, and profitability language out of scope.

This stage does not modify source code, tests, research scripts, generated
reports, strategy logic, data access, execution assumptions, live or paper
trading scope, brokerage integration, order execution, or profitability
language.

Validation at the time of this entry:

```text
python -m pytest -q
434 passed

python -m compileall src tests research
passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-08 - User-Provided Local CSV Research Plan

This documentation milestone defines the Stage 77 plan for future
user-provided local CSV research without loading user files or interpreting
real-data results.

Assumption: after the local CSV readiness checkpoint merged, the safest
PR-sized next stage is a documentation-only planning artifact. The project has
strict local loaders, committed synthetic fixtures, factor diagnostics,
liquidity eligibility, universe masks, universe-masked signals, and synthetic
backtest smoke coverage, but it still needs a clear local-file study plan
before any user-provided CSV result can be interpreted.

`docs/user_provided_local_csv_research_plan.md` now defines the intended
future workflow gates, local input bundle, scope statement template,
validation requirements, research design requirements, interpretation levels,
stop conditions, and next PR-sized stages. It keeps user-provided local CSV
work gated by provenance, schema validation, adjustment policy, universe
documentation, benchmark compatibility, sample splits, cost/slippage
assumptions, experiment logging, and the real-data readiness audit.

This stage does not modify source code, tests, research scripts, generated
reports, strategy logic, data access, execution assumptions, live or paper
trading scope, brokerage integration, order execution, or profitability
language.

Validation at the time of this entry:

```text
python -m pytest -q
434 passed

python -m compileall src tests research
passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Local CSV Readiness Checkpoint

This documentation milestone records the local CSV readiness state after the
fixture workflow was updated with liquidity universe masks and
universe-masked signal audit counts.

Assumption: the safest PR-sized Stage 76 is a checkpoint before planning any
user-provided local CSV research. The project has enough synthetic and
committed-fixture infrastructure to define a future plan, but not enough
provenance, adjustment-policy, universe, benchmark, cost, slippage, or sample
split evidence to interpret real user-provided local CSV results.

`docs/local_csv_readiness_checkpoint.md` summarizes the current implemented
state, readiness assessment, guardrail review, stop conditions before
user-provided local CSV interpretation, and the recommended next stage:
documentation-only user-provided local CSV research planning.

This stage does not modify source code, tests, research scripts, generated
reports, strategy logic, data access, execution assumptions, live or paper
trading scope, brokerage integration, order execution, or profitability
language.

Validation at the time of this entry:

```text
python -m pytest -q
434 passed

python -m compileall src tests research
passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Synthetic Masked-Signal Backtest Smoke Test

This test milestone added the first synthetic smoke check that passes
universe-masked signals into the existing long-only backtester after the
synthetic masked-signal adapter smoke test merged.

Assumption: the safest PR-sized Stage 74 is a focused test-only backtest smoke
check, not a new research script, report, experiment log, backtester rewrite,
portfolio-construction change, parameter study, or real-data workflow.

`tests/test_liquidity_masked_signal_backtest_smoke.py` now builds
deterministic synthetic price, volume, and raw-signal panels, computes lagged
ADV and dollar-volume eligibility, constructs a liquidity universe mask,
applies that mask to raw signals, and passes the masked signal panel to
`run_long_only_backtest()`. The test verifies the exact masked signals,
resulting holdings, aligned signal coverage, transaction-cost impact, and the
existing `signal_lag_periods=1` timing. A second test confirms that a current
rebalance uses the prior masked-signal row, so a same-date universe/signal
change does not affect the current rebalance.

This stage does not modify source helpers, backtester behavior, metrics,
loaders, research scripts, generated reports, real-data handling, vendor
access, credentials, live or paper trading, brokerage integration, order
execution, strategy parameters, reusable report outputs, or profitability
claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_liquidity_masked_signal_backtest_smoke.py
2 passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Local CSV Fixture Universe-Masked Signal Smoke Check

This code-and-report milestone updated the committed synthetic local CSV
fixture workflow after the synthetic masked-signal backtest smoke PR merged.

Assumption: the safest PR-sized Stage 75 is not another backtest, not a
portfolio-construction change, not a real-data workflow, and not a parameter
study. It is a narrow local-fixture wiring check that applies the reviewed
liquidity universe mask to an already-computed `alpha_009` signal panel and
records the resulting masked-signal audit counts.

`research/local_csv_fixture_workflow_demo.py` now calls
`apply_universe_mask_to_signals()` after constructing the synthetic fixture
liquidity universe. The resulting `masked_alpha_009_signals` panel keeps the
original signal only where the universe mask is `True`, turns ineligible cells
into missing values rather than zero scores, preserves existing signal missing
values, and records per-date raw valid signal counts, eligible universe
counts, valid masked signal counts, excluded-by-universe counts, missing signal
counts, and low-coverage dates.

The generated fixture report and JSON sidecar log now include a
universe-masked `alpha_009` signal smoke-check section. The output is a
signal-panel wiring diagnostic only. It does not rank assets, create weights,
run a backtest, create trades, compare benchmark returns, fetch real data,
connect to a broker, support live or paper trading, or make profitability
claims.

`tests/test_local_csv_fixture_workflow_demo.py` now verifies the masked signal
alignment, deterministic output, exact fixture masked-signal values, report
section, JSON diagnostics, helper reuse, caveats, and configuration
validation.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
13 passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Synthetic Masked-Signal Smoke Test

This test milestone added the first synthetic smoke check after the
universe-masked signal adapter merged.

Assumption: the safest PR-sized Stage 73 is an integration-style test that
proves the reviewed liquidity eligibility helpers, liquidity universe
constructor, and `apply_universe_mask_to_signals()` adapter compose into the
masked signal panel a future backtest would consume. It is not yet a backtest
stage, research-script update, generated-report stage, parameter study, or
real-data workflow.

`tests/test_liquidity_masked_signal_smoke.py` now builds deterministic
synthetic price, volume, and raw-signal panels. The smoke test computes lagged
ADV and dollar-volume eligibility masks, constructs a liquidity universe mask,
applies that mask to raw signals, and checks the exact universe mask, masked
signals, and audit summary. Ineligible signals become `NaN`, not zero, and an
existing raw signal `NaN` remains visible in the summary. A second test changes
a future liquidity observation and confirms earlier masked-signal rows do not
change.

This stage does not modify source helpers, backtester behavior, metrics,
loaders, research scripts, generated reports, real-data handling, vendor
access, credentials, live or paper trading, brokerage integration, order
execution, target weights, portfolio construction, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_liquidity_masked_signal_smoke.py
2 passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Universe-Masked Signal Adapter

This code milestone implemented the first narrow helper from the liquidity
universe backtest-integration design after PR #71 merged.

Assumption: the safest PR-sized Stage 72 is a synthetic/local-panel signal
masking adapter only, not a backtest integration, ranking rule, target-weight
constructor, research-script update, generated report, or real-data workflow.

`src/features/liquidity.py` now exposes `UniverseMaskedSignalsResult` and
`apply_universe_mask_to_signals()`. The helper accepts an already-computed
numeric signal panel and an already-constructed boolean universe mask with
identical dates and assets. `True` mask cells preserve the original signal,
`False` mask cells become missing values rather than zero scores, and existing
signal missing values remain missing. The helper rejects mismatched indexes,
mismatched columns, non-boolean masks, duplicate labels, unsorted dates, and
missing universe-mask values by default. It does not reindex, forward-fill,
backward-fill, zero-fill, rank assets, create weights, run a backtest, write
reports, fetch data, or interpret performance.

Focused tests in `tests/test_liquidity.py` cover a hand-calculated masking
example, index and column preservation, ineligible signals becoming `NaN` and
not zero, preservation of existing signal `NaN` values, nullable boolean mask
acceptance, mismatched index rejection, mismatched column rejection,
unsorted and duplicate date rejection, duplicate-column rejection, non-boolean
mask rejection, missing mask rejection by default, and invalid parameter
rejection.

During the stage, a new duplicate-column test initially exposed a validation
order issue: duplicate signal columns reached the shared numeric panel
validator before the adapter's duplicate-column check, producing a pandas
`AttributeError` instead of the intended `ValueError`. The adapter now checks
duplicate signal columns before numeric validation. The full failure-to-fix
chain is recorded in `docs/troubleshooting_log.md`.

This stage remains synthetic/local-panel research infrastructure only. It does
not fetch real data, add vendor access, add credentials, modify loaders,
modify research scripts, generate reports, connect to a broker, place orders,
support live or paper trading, modify the backtester or metrics, tune
thresholds, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_liquidity.py
58 passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Liquidity Universe Backtest Integration Design

This documentation milestone defined the next reviewed boundary after the
synthetic liquidity universe helper and fixture universe-mask smoke check
merged.

Assumption: the next safest PR-sized stage is not source-code integration into
`run_long_only_backtest()`. It is a design gate that specifies how liquidity
universe masks, factor signals, rebalance schedules, costs, slippage,
benchmarks, and execution lag should interact before any backtest consumes a
universe mask.

`docs/liquidity_universe_backtest_integration_design.md` now defines the
purpose, current evidence, non-goals, proposed future signal-masking adapter,
strict signal/mask alignment contract, timing contract, selection and coverage
semantics, required future backtest assumptions, required future tests, and
suggested next stages.

`docs/liquidity_universe_construction_design.md` now marks the first three
recommended follow-up stages as complete and points the next step to the new
backtest-integration design. `docs/liquidity_dollar_volume_universe_plan.md`
also now reflects the completed universe-mask helper and fixture smoke stages.
`docs/decision_log.md` records the decision to require this design before code
consumes liquidity universe masks.

This stage does not modify source code, tests, research scripts, generated
reports, data loaders, backtester behavior, metrics, strategy logic, real-data
handling, vendor access, credentials, live or paper trading, brokerage
integration, order execution, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
417 passed

python -m compileall src tests research
passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Liquidity Universe Fixture Smoke Check

This stage connected the reviewed synthetic liquidity universe helper to the
committed local CSV fixture workflow as a count-only smoke check.

Assumption: after the standalone helper merged, the next safest PR-sized stage
was not backtest consumption, ranking/capping research, threshold tuning, or a
real-data workflow. It was a narrow fixture workflow update that proves the
existing ADV and dollar-volume eligibility masks can be combined into
`construct_liquidity_universe()` and reported as audit counts only.

`research/local_csv_fixture_workflow_demo.py` now constructs a
`synthetic_fixture_liquidity_universe` result from the intersection of the
lagged ADV and dollar-volume eligibility masks. The generated Markdown report
and JSON experiment log include universe-mask counts, low-coverage dates, and
caveats that keep the output separate from portfolio construction, backtest
universe integration, tradeability evidence, trading behavior, or performance
interpretation.

`tests/test_local_csv_fixture_workflow_demo.py` now verifies the universe mask
alignment, deterministic summary, low-coverage dates, JSON diagnostics,
Markdown report section, helper reuse, and invalid `min_assets_per_date`
configuration. The default synthetic report and experiment-log sidecar were
regenerated from the committed fixture only.

During implementation, the first full test run failed because the test suite
still expected the pre-helper caveat text `not universe construction` while
the workflow had intentionally changed to a universe-mask count diagnostic.
The full failure-to-fix chain is recorded in `docs/troubleshooting_log.md`.

This stage does not fetch real data, add vendor access, add credentials,
modify loaders, modify backtester or metrics, create target weights, place
orders, support live or paper trading, tune liquidity thresholds, or make
profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
13 passed

python -m pytest -q
417 passed

python -m compileall src tests research
passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Synthetic Liquidity Universe Helper

This code milestone implemented the first reviewed liquidity universe-mask
boundary after the documentation-only construction design merged.

Assumption: the next safest PR-sized stage after
`docs/liquidity_universe_construction_design.md` is a narrow synthetic/local
panel helper, not a research workflow update, backtest integration, report
generation, threshold-tuning step, or real-data study.

`src/features/liquidity.py` now exposes `LiquidityUniverseResult` and
`construct_liquidity_universe()`. The helper accepts an already-reviewed
boolean eligibility panel, records missing eligibility before treating it as
ineligible, optionally caps eligible assets by an aligned ranking metric with
stable input-column tie handling, and returns both the final boolean universe
mask and an inspectable per-date audit summary. The summary keeps raw eligible
counts, final universe counts, missing eligibility counts, missing ranking
counts, capped counts, additions, removals, and low-coverage flags visible.

Focused tests in `tests/test_liquidity.py` cover summary fields, missing
eligibility exclusion for object and nullable boolean panels, rejection of
non-boolean eligibility values, capped selection, missing ranking exclusion,
deterministic tie handling, mismatched ranking panels, no-lookahead behavior
for ranking values, parameter validation, and continued absence of data,
trading, or backtest imports.

During the stage, the first missing-eligibility implementation passed tests
but emitted a pandas `FutureWarning` because object boolean panels were cleaned
with `fillna(False).astype(bool)`. The conversion was replaced with
`eq(True).fillna(False).astype(bool)`, preserving explicit missing-value
exclusion for both object and nullable boolean panels while avoiding future
silent-downcasting behavior. The full warning-to-fix chain is recorded in
`docs/troubleshooting_log.md`.

This stage does not fetch real data, add vendor access, add credentials,
modify loaders, modify research scripts, generate reports, connect to a
broker, place orders, support live or paper trading, modify the backtester or
metrics, create portfolio weights, tune thresholds, or make profitability
claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_liquidity.py
44 passed
```

Full validation is rerun before the associated PR is committed and opened.

---

## 2026-06-07 - Liquidity Universe Construction Design

This documentation milestone defined the next liquidity-related boundary after
the Alpha#012 LEAN planning refresh merged.

Assumption: after synthetic rolling ADV and rolling dollar-volume eligibility
helpers, local-fixture eligibility count smoke coverage, and Alpha#012
planning are complete, the next safest PR-sized stage is not code and not a
backtest. It is a design that specifies how a future universe mask and audit
summary should behave before any liquidity eligibility is consumed by
portfolio construction.

`docs/liquidity_universe_construction_design.md` now defines the purpose,
non-goals, timing definitions, proposed future API boundary, mask semantics,
audit-summary contract, module alignment, required future tests, risks, and
next stages for a synthetic-only liquidity universe construction helper.

`docs/liquidity_dollar_volume_universe_plan.md` now marks the eligibility
helper, local-fixture count smoke, and experiment-log field work as completed
for synthetic fixtures, then routes future work through the new universe-mask
design. `docs/decision_log.md` records the decision to keep liquidity
eligibility, universe-mask construction, and backtest consumption as separate
reviewed stages.

This stage does not modify source code, tests, research scripts, generated
reports, data access, backtester behavior, metrics, strategy logic, real-data
handling, vendor access, credentials, live or paper trading, brokerage
integration, order execution, runnable LEAN behavior, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
402 passed

python -m compileall src tests research
passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-07 - Alpha#012 QuantConnect/LEAN Plan Refresh

This documentation milestone refreshed the QuantConnect/LEAN planning path
after the post-Alpha#012 roadmap checkpoint merged.

Assumption: the next safest PR-sized stage after the Alpha#012 local feature,
fixture smoke, diagnostics, and checkpoint sequence is a planning refresh, not
runnable LEAN code. The local Alpha#012 feature changes the local-to-LEAN
signal mapping assumptions because it requires both completed close and volume
bars, an explicit close normalization policy, a reviewed volume policy, and
visible skip reasons for missing, stale, mismatched, or invalid inputs.

`docs/quantconnect_lean_plan.md` now records Alpha#012 as an implemented
local research feature and maps it to future LEAN planning requirements:
completed close and volume timing, close normalization, volume-source policy,
date matching, missing and stale data handling, negative-volume rejection,
zero-volume visibility, feature export, and diagnostic-only treatment.

`docs/lean_parity_checklist.md` now includes Alpha#012 parity assertions and
diagnostic coverage requirements. These checklist entries keep Alpha#012 out
of order logic, universe construction, portfolio construction, performance
interpretation, and strategy claims unless a later reviewed stage explicitly
changes that boundary.

This stage does not modify source code, tests, research scripts, generated
reports, data access, backtester behavior, metrics, strategy logic, real-data
handling, vendor access, credentials, live or paper trading, brokerage
integration, order execution, runnable LEAN behavior, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
402 passed

python -m compileall src tests research
passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-07 - Post-Alpha#012 Roadmap Checkpoint

This documentation checkpoint refreshed the staged roadmap after PR #65 merged
the Alpha#012 synthetic local-fixture diagnostics.

Assumption: after Alpha#012 implementation, synthetic OHLCV fixture smoke
coverage, and local-fixture diagnostics all merged, the next safest PR-sized
stage is not another formula or a backtest. It is a checkpoint that reconciles
the now-completed Alpha#012 sequence and chooses the next stage from current
evidence.

`docs/post_alpha012_checkpoint_report.md` now records the current
implementation state, completed Alpha#012 stages, remaining original-goal
gaps, guardrail status, and a recommended next roadmap.
`docs/volume_close_alpha_plan.md` now marks the synthetic fixture diagnostics
stage as complete and updates the recommended next stage.
`docs/worldquant_alpha_catalog.md` now reflects that Alpha#012 has fixture
smoke and diagnostics coverage, while keeping all remaining WorldQuant-style
formulas separate and PR-sized.

The checkpoint recommends a documentation-only QuantConnect/LEAN plan refresh
for Alpha#012 signal mapping as the next safe stage. That recommendation is
limited to planning: no runnable LEAN code, data subscriptions, credentials,
brokerage behavior, orders, portfolio construction, or performance
interpretation should be added.

This stage does not modify source code, tests, research scripts, generated
reports, data access, backtester behavior, metrics, strategy logic, real-data
handling, vendor access, credentials, live or paper trading, brokerage
integration, order execution, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
402 passed

python -m compileall src tests research
passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-07 - Alpha#012 Local Fixture Diagnostics

This workflow milestone extended the committed synthetic local CSV fixture
workflow after the Alpha#012 OHLCV fixture smoke check merged.

Assumption: the next smallest safe stage is a diagnostics-only workflow update
for `alpha_012()`, not a backtest, strategy rule, report interpretation,
additional formula, or real-data study. The existing local fixture workflow
already loads the committed synthetic OHLCV fixture, aligns adjusted close and
volume panels, computes forward-return evaluation targets, applies
train/validation/test split metadata, and runs IC, Rank IC, and quantile-spread
diagnostics for `alpha_009()`.

`research/local_csv_fixture_workflow_demo.py` now computes `alpha_012()` from
the aligned synthetic OHLCV `adjusted_close` and `volume` panels and evaluates
it with the same existing diagnostic helpers against already-aligned
forward-return targets. The generated Markdown report and JSON experiment log
record Alpha#012 diagnostic coverage separately from Alpha#009. The tiny
fixture produces two valid Alpha#012 observations on the validation date, one
valid IC date, one valid Rank IC date, and no valid Alpha#012 quantile-spread
dates because the configured three-quantile diagnostic requires more valid
assets than the fixture supplies.

During the stage, a new JSON-log test initially asserted exact equality for a
computed Rank IC value that serialized as `0.9999999999999999` instead of
`1.0`. The assertion was corrected to use approximate equality for the finite
computed float while preserving exact structural checks; the full
failure-to-fix chain is recorded in `docs/troubleshooting_log.md`.

This stage remains synthetic/local-fixture only. It does not fetch real data,
add vendor access, add credentials, connect to a broker, place orders, support
live or paper trading, modify feature formulas, modify loaders, modify the
backtester, create a portfolio, tune parameters, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
13 passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-07 - Alpha#012 Synthetic OHLCV Fixture Smoke Check

This test milestone added a narrow local-fixture smoke check after PR #63
merged `alpha_012()`.

Assumption: the next safest stage after the Alpha#012 implementation is not
diagnostics, report generation, backtesting, or another alpha formula. It is a
small wiring check from the existing strict OHLCV loader to the new feature
using the committed synthetic OHLCV fixture only.

`tests/test_local_csv_loader_smoke_demo.py` now loads
`tests/fixtures/local_csv_loader_smoke/synthetic_ohlcv.csv` with
`load_ohlcv_csv(require_adjusted_close=True)`, pivots `adjusted_close` and
`volume` into aligned date-asset panels, and computes `alpha_012(close,
volume)`. The test verifies the fixture dates and assets, the first-row `NaN`
delta behavior, and hand-calculated second-row outputs of `-0.75` for `AAA`
and `-0.50` for `BBB`.

This stage is feature-only smoke coverage. It does not modify source feature
logic, loaders, diagnostics, research scripts, reports, generated experiment
logs, backtester behavior, metrics, normalization, factor combination,
QuantConnect/LEAN artifacts, data access, vendor access, credentials, live or
paper trading, brokerage integration, order execution, or profitability
claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_loader_smoke_demo.py
7 passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-07 - Alpha#012 Volume + Close Research Feature

This code milestone implemented `alpha_012` as one reviewed volume + close
WorldQuant-style research feature after the planning gate in
`docs/volume_close_alpha_plan.md` merged.

Formula provenance: the public arXiv version of Zura Kakushadze's
`101 Formulaic Alphas` lists Alpha#012 as:

```text
sign(delta(volume, 1)) * (-1 * delta(close, 1))
```

`alpha_012()` maps that formula to caller-provided close and volume panels. It
requires exactly matching dates and asset columns, rejects negative volume,
does not fill missing close or volume values, preserves zero-volume behavior
explicitly, and returns `NaN` when either one-period delta endpoint is missing.
The feature at date `t` uses only `close[t]`, `volume[t]`, and their one-row
trailing anchors. Execution lag, ranking direction, universe selection,
portfolio construction, costs, slippage, backtesting, and interpretation
remain separate later-stage responsibilities.

Focused tests in `tests/test_worldquant_alphas.py` cover hand-calculated
formula output, shape preservation, no-lookahead behavior for both close and
volume, missing endpoints, zero-volume and zero-volume-delta behavior,
negative-volume rejection, panel alignment, invalid close and volume inputs,
and continued absence of backtest integration imports.

During the stage, the first hand-calculated test had an incorrect expected
sign for one row. The implementation matched the reviewed formula; the test
expectation was corrected and the full failure-to-fix chain is recorded in
`docs/troubleshooting_log.md`.

This stage does not fetch real data, add vendor access, add credentials,
connect to a broker, place orders, support live or paper trading, implement
bulk WorldQuant 101, modify loaders, modify the backtester, generate reports,
or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_worldquant_alphas.py
24 passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-06 - Volume + Close Alpha Planning Gate

This documentation milestone added `docs/volume_close_alpha_plan.md` before
any volume-dependent WorldQuant-style alpha implementation.

Assumption: after PR #61 merged the realized volatility feature, the older
`docs/original_goal_gap_analysis.md` recommendation for a synthetic IC /
Rank IC helper is stale because `factor_information_coefficient()` and
`factor_rank_information_coefficient()` already exist in
`src/features/diagnostics.py` and are covered by tests. The current
post-liquidity roadmap points to volume-dependent alpha planning as the next
small safe stage after reversal and realized volatility are settled.

The new plan keeps the next formula stage separate from data access, loader
changes, universe construction, portfolio construction, backtesting,
QuantConnect/LEAN runtime work, and interpretation. It records prerequisites,
non-goals, formula provenance requirements, close and volume policy questions,
date-alignment rules, missing and zero-volume behavior, required future tests,
research risks, and PR-sized next steps for a single future volume + close
alpha candidate such as `alpha_012`.

No source code, tests, research scripts, generated reports, data loaders,
backtester behavior, metrics, normalization, combination, diagnostics,
synthetic demos, real data fetching, vendor access, credentials, live or paper
trading, brokerage integration, order execution, or profitability claims were
changed.

Validation at the time of this entry:

```text
python -m pytest -q
391 passed

python -m compileall src tests research
passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-06 - Realized Volatility Feature

This code milestone implemented the next safe stage after the short-term
reversal feature: a small adjusted-price realized volatility research feature.

Assumption: the first volatility helper should compute unannualized trailing
realized volatility from simple one-period returns, leaving any annualization,
risk scaling, filtering threshold, portfolio construction, execution timing,
costs, slippage, backtesting, and interpretation to later explicit stages.
`calculate_realized_volatility()` therefore computes adjacent-price returns:

```text
price[t] / price[t - 1] - 1
```

and then calculates a full-window trailing standard deviation ending at the
signal date. The default window is 21 return observations and the default
degrees-of-freedom setting is `ddof=0`.

The feature uses only current and historical prices. It preserves the input
dates and asset columns, does not sort or reindex input data, does not fill
missing values, and treats returns as missing when either adjacent price anchor
is missing or non-positive. Any missing return inside the required trailing
window keeps the volatility value as `NaN`.

Focused tests in `tests/test_volatility.py` cover hand-calculated simple-return
volatility, no-lookahead behavior, date/column alignment, full-window
requirements, missing-price behavior without fills, non-positive anchor
handling, `ddof` behavior, sorted and duplicate date validation, window and
`ddof` validation, and non-numeric input rejection.

This stage does not fetch real data, add vendor access, add credentials,
connect to a broker, place orders, support live or paper trading, modify the
backtester, generate reports, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_volatility.py
20 passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-06 - Short-Term Reversal Feature

This code milestone implemented the next safe stage recommended by
`docs/post_liquidity_checkpoint_report.md`: a small close-price
short-term reversal research feature.

Assumption: the reversal score convention should make higher values represent
stronger contrarian candidates. `calculate_short_term_reversal()` therefore
computes the negative trailing return over a configurable lookback window:

```text
-(price[t] / price[t - lookback_periods] - 1)
```

The feature uses explicit current and trailing price anchors only. It preserves
the input dates and asset columns, does not sort or reindex input data, does
not fill missing values, and returns `NaN` when either required anchor is
missing or non-positive. Execution timing, signal lag, portfolio construction,
costs, slippage, backtesting, and interpretation remain separate later-stage
responsibilities.

Focused tests in `tests/test_reversal.py` cover hand-calculated sign
convention, no-lookahead behavior, date/column alignment, missing anchor
handling without fills, non-positive anchor handling, sorted and duplicate date
validation, lookback validation, and non-numeric input rejection.

This stage does not fetch real data, add vendor access, add credentials,
connect to a broker, place orders, support live or paper trading, modify the
backtester, generate reports, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_reversal.py
13 passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-06 - Post-Liquidity Roadmap Checkpoint

This documentation checkpoint refreshed the roadmap after PR #58 merged the
synthetic local-fixture liquidity eligibility count smoke check.

Assumption: after the OHLCV and liquidity sequence, the next safest PR-sized
stage is to reconcile stale roadmap recommendations before starting another
feature implementation. `docs/original_goal_gap_analysis.md` and
`docs/current_roadmap_gap_refresh.md` still contain useful original-goal
context, but they predate several completed stages: IC / Rank IC diagnostics,
quantile spread diagnostics, validation split helpers, local CSV fixture
workflow, strict OHLCV loading, synthetic liquidity eligibility helpers, and
the local fixture liquidity count smoke check.

`docs/post_liquidity_checkpoint_report.md` now records the current
implementation state, completed roadmap items, remaining gaps, guardrail
review, and a next-stage recommendation. The report identifies
`src/features/reversal.py` and `src/features/volatility.py` as placeholder
modules only and recommends short-term reversal feature design or
implementation as the next safe stage, subject to explicit score-sign and
missing-value tests.

This stage is documentation-only. It does not modify source code, tests,
research scripts, generated reports, strategy logic, backtester behavior,
metrics, data access, execution assumptions, real data handling, vendor
access, credentials, live or paper trading, brokerage integration, order
execution, or profitability claims.

Validation before this checkpoint:

```text
python -m pytest -q
358 passed

python -m compileall src tests research
passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-06 - Synthetic Liquidity Eligibility Fixture Smoke Check

This code milestone extended the committed synthetic local CSV fixture workflow
with a narrow liquidity eligibility count smoke check after the synthetic-only
liquidity helper merged.

Assumption: the next safe PR-sized stage is not universe construction,
strategy validation, backtesting, or real-data interpretation. It is a wiring
check that proves the existing strict local CSV workflow can load the committed
synthetic OHLCV fixture, pivot `adjusted_close` and `volume`, align those panels
to the synthetic adjusted-close fixture, and report lagged ADV and
dollar-volume eligibility counts without filling missing volume.

`research/local_csv_fixture_workflow_demo.py` now loads the synthetic OHLCV
fixture with `load_ohlcv_csv()`, computes lagged eligibility masks with
`average_daily_volume_eligibility()` and
`average_dollar_volume_eligibility()`, and writes decision-date count
diagnostics to the synthetic report and JSON experiment log. The default smoke
parameters use a two-row window, one-row eligibility lag, a minimum average
volume threshold, and a minimum average dollar-volume threshold. Missing and
zero-volume counts remain visible in the report; no forward-fill,
backward-fill, interpolation, zero default, universe construction, portfolio,
backtest, external data access, broker connection, order execution, or
profitability claim is added.

Focused tests in `tests/test_local_csv_fixture_workflow_demo.py` assert the
aligned liquidity panels, expected lagged eligibility counts, missing-volume
counts, zero-volume counts, report caveats, JSON diagnostics, and integration
with the existing loader and liquidity helpers.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
13 passed
```

Full validation is recorded in the associated PR summary.

---

## 2026-06-06 - Synthetic Liquidity Eligibility Helper

This code milestone implemented the next safe stage after
`docs/liquidity_dollar_volume_universe_plan.md`: a narrow synthetic-only
liquidity eligibility helper with deterministic tests.

Assumption: the reviewed liquidity and dollar-volume planning gate made the
function boundary clear enough to implement a small helper rather than adding
another design-only checkpoint. The implementation is limited to already
prepared numeric panels and does not connect to the CSV loader, fetch data,
select a portfolio, run a backtest, modify alpha formulas, alter diagnostics,
generate reports, add vendor access, add credentials, connect to a broker,
place orders, support live or paper trading, or make profitability claims.

`src/features/liquidity.py` now provides rolling average daily volume and
rolling average dollar-volume helpers plus lagged eligibility masks. The
eligibility helpers use full rolling windows only, preserve missing values as
ineligible observations, reject negative volume and non-positive prices,
require positive finite thresholds, default to a one-row eligibility lag, and
require each rolling volume window to contain strictly positive volume by
default. That default keeps zero-volume rows from being silently accepted as
liquid while still allowing an explicit non-default policy for synthetic tests.

Focused tests in `tests/test_liquidity.py` cover hand-calculated ADV and
dollar-volume calculations, date-lag semantics, warm-up ineligibility, missing
values without filling, default zero-volume exclusion, explicit zero-volume
policy override, configurable positive lags, invalid thresholds, invalid
windows, mismatched panels, negative volume, non-positive prices, non-numeric
inputs, and forbidden import boundaries.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_liquidity.py
30 passed

python -m pytest -q
357 passed

python -m compileall src tests research
passed

.\scripts\audit-skills.ps1
passed for 2 Skill files
```

---

## 2026-06-06 - Liquidity And Dollar-Volume Universe Planning Gate

This documentation-only milestone added
`docs/liquidity_dollar_volume_universe_plan.md` after the strict OHLCV loader
and synthetic OHLCV loader smoke coverage merged.

Assumption: the next safe stage after OHLCV validation and smoke coverage is
not volume-based filtering code or a volume-dependent alpha. The safer
PR-sized step is to define local-only liquidity and dollar-volume universe
rules, date-alignment requirements, zero-volume handling, missing-data
behavior, and future implementation gates before any code filters assets by
volume.

The plan defines candidate inputs, average daily volume, dollar-volume, and
rolling dollar-volume formulas, explicit observation/decision/signal/execution
date boundaries, strict missing-value and zero-volume policy, candidate
universe rules, future deterministic test requirements, research risks, and
future PR-sized stages. It preserves the existing research-only boundary and
does not implement a universe filter, modify loaders, modify features, modify
backtests, add research scripts, generate reports, fetch data, add vendor
access, add credentials, connect to a broker, place orders, support live or
paper trading, or make profitability claims.

`docs/volume_ohlcv_schema_plan.md` now records the liquidity planning note as
the completed planning gate before volume-based filtering. The WorldQuant
alpha catalog now points future liquidity or dollar-volume universe work to
this plan before implementation.

Validation at the time of this entry:

```text
python -m pytest -q
327 passed

python -m compileall src tests research
passed
```

---

## 2026-06-06 - Synthetic OHLCV Loader Smoke Demo

This test milestone added fixture-level smoke coverage for the strict local
OHLCV CSV loader after the loader implementation merged.

Assumption: after the strict `load_ohlcv_csv()` stage, the next safe
PR-sized step is Stage 3 from `docs/volume_ohlcv_schema_plan.md`: validate the
committed synthetic OHLCV fixture at the smoke-demo level before any
liquidity filter, dollar-volume workflow, OHLC-dependent alpha, strategy
logic, or generated report is added.

The stage extends `tests/test_local_csv_loader_smoke_demo.py` rather than
creating a research script. That keeps the work focused on loader wiring and
audit metadata: the committed synthetic OHLCV fixture loads with the expected
schema, sorted dates, duplicate-free date-symbol pairs, float numeric fields,
positive OHLC relationships, summary metadata, and required adjusted-close
policy. Additional synthetic temporary files test that missing values remain
strict by default and invalid OHLC relationships are rejected.

`docs/volume_ohlcv_schema_plan.md` now reflects the completed loader and smoke
coverage and recommends a future liquidity or dollar-volume universe planning
note before any code filters assets by volume. This change remains local and
synthetic only. It does not modify source code, research scripts, reports,
feature formulas, alpha modules, diagnostics, backtester behavior, metrics,
real-data access, vendor downloads, credentials, live or paper trading,
brokerage or order execution, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_loader_smoke_demo.py
6 passed

python -m pytest -q
327 passed

python -m compileall src tests research
passed
```

---

## 2026-06-06 - Strict Local OHLCV CSV Loader

This code milestone implemented the next stage recommended by
`docs/volume_ohlcv_schema_plan.md`: a strict local OHLCV long-format CSV
loader using committed synthetic fixtures only.

Assumption: the reviewed OHLCV schema plan made the implementation scope clear
enough to proceed without an additional documentation-only checklist. The
stage is limited to local CSV validation and does not compute a strategy,
generate reports, modify alpha formulas, modify diagnostics, modify the
backtester, fetch data, add vendor APIs, add credentials, connect to a broker,
place orders, support live or paper trading, or make profitability claims.

`src/data/csv_loader.py` now exposes `load_ohlcv_csv()` and
`ValidatedCSVFrame`. The loader preserves raw CSV strings through validation,
requires local `.csv` paths, rejects duplicate headers, validates required
`date`, `symbol`, `open`, `high`, `low`, `close`, and `volume` columns,
supports optional or required `adjusted_close`, rejects duplicate
`(date, symbol)` rows, rejects missing symbols, rejects missing or invalid
numeric sentinels by default, preserves missing values only when
`allow_missing=True`, requires positive OHLC and `adjusted_close` values when
present, allows zero volume but rejects negative volume, and rejects impossible
OHLC relationships.

The zero-volume decision is intentionally narrow: zero volume is accepted as a
non-negative local loader value so the loader does not impose liquidity-policy
assumptions. Future liquidity or dollar-volume stages must explicitly report,
filter, or reject zero-volume rows in their own tests and documentation.

Test coverage in `tests/test_csv_loader.py` and
`tests/fixtures/local_csv_loader_smoke/synthetic_ohlcv.csv` covers valid
synthetic OHLCV loading, summary metadata, strict missing-value rejection,
explicit missing preservation, duplicate date-symbol pairs, missing symbols,
required adjusted close, negative and zero volume behavior, non-positive
prices, and invalid OHLC relationships.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_csv_loader.py
34 passed

python -m pytest -q
324 passed

python -m compileall src tests research
passed
```

---

## 2026-06-06 - Volume And OHLCV Schema Planning Gate

This documentation-only milestone added
`docs/volume_ohlcv_schema_plan.md` after the local CSV fixture split metadata
workflow merged.

Assumption: after Stage C in `docs/current_roadmap_gap_refresh.md` was
completed by the local CSV fixture split metadata workflow, the next safe
roadmap stage is Stage D: volume/OHLCV schema planning. The planning gate is
needed before implementing volume-dependent factors, OHLC-dependent
WorldQuant-style alphas, or liquidity-based universe filters.

The plan defines future local volume-only and OHLCV long-format schemas,
optional metadata sidecar expectations, strict validation rules, alignment
requirements with existing feature and backtest modules, research risks, and
future PR-sized stages. It preserves the existing local-file-only boundary and
does not implement a loader, add fixtures, modify `src/`, modify tests,
generate reports, fetch data, add vendor access, add credentials, connect to a
broker, place orders, support live or paper trading, or make profitability
claims.

`docs/csv_data_interface_plan.md` now points to this plan as the schema gate
before volume or OHLCV loader support. `docs/worldquant_alpha_catalog.md` now
points future volume or OHLC-dependent alpha work to the plan before code is
added.

Validation at the time of this entry:

```text
python -m pytest -q
309 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-05 - Local CSV Fixture Split Metadata Workflow Update

This code milestone updated the committed synthetic local CSV fixture workflow
after the split helper and split-aware IC / Rank IC demo had merged.

Assumption: after the split-aware diagnostic demo, the next safe roadmap stage
is the local fixture split-aware workflow update recommended by
`docs/current_roadmap_gap_refresh.md`. The stage applies existing
train/validation/test metadata to the already-committed synthetic local CSV
fixture workflow. It remains a fixture wiring and diagnostic coverage check,
not a real-data study, model-selection result, backtest, strategy validation,
or performance claim.

The workflow now configures chronological fixture split boundaries, creates a
`TrainValidationTestSplit` from the loaded price index, slices the `alpha_009`
factor panel and forward-return target panel with
`split_panel_by_train_validation_test()`, and computes IC, Rank IC, and
quantile-spread diagnostics both overall and by split. The generated Markdown
report and JSON experiment log now include split boundaries, split coverage,
per-split diagnostic metadata, explicit signal-date split timing caveats, and
caveats that the output is synthetic, fixture-only, not model selection, and
not strategy validation.

Test coverage was expanded to check the expected train, validation, and test
fixture windows; alignment of split factor and target panels; deterministic
split outputs; caveated report/log fields; helper-use monkeypatch counts;
invalid split-boundary rejection; forbidden-import checks; and caveated
profitability language.

This change does not modify CSV loader behavior, alpha formulas, diagnostic
helper behavior, validation helper behavior, backtester behavior, metrics,
LEAN code, normalization, combination, real-data access, vendor downloads,
credentials, live or paper trading, brokerage or order execution, or
profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
12 passed

python -m pytest -q
309 passed

python -m compileall src tests research
passed
```

---

## 2026-06-05 - Synthetic Split-Aware IC / Rank IC Demo

This code milestone added `research/synthetic_split_ic_rank_ic_demo.py` and
`tests/test_synthetic_split_ic_rank_ic_demo.py` after the
train/validation/test split helper merged.

Assumption: after PR #48 merged, the next safe roadmap stage is the
split-aware diagnostic demo recommended by
`docs/current_roadmap_gap_refresh.md`. The stage applies the existing
chronological split helper to deterministic synthetic factor and
forward-return panels before computing IC and Rank IC diagnostics. It is a
wiring and coverage demonstration only, not model selection, strategy
validation, a backtest, or evidence of factor performance.

The demo builds a small synthetic factor panel, derives synthetic
forward-return evaluation targets by split, preserves missing values, slices
both panels through `split_panel_by_train_validation_test()`, computes
`factor_information_coefficient()` and
`factor_rank_information_coefficient()` separately for train, validation, and
test windows, and summarizes date counts, valid observations, valid diagnostic
dates, mean IC, and mean Rank IC. Optional report and JSON log outputs are
caveated and can be redirected to temporary paths in tests.

The test coverage includes expected split windows, alignment checks,
missing-value preservation, deterministic reruns, hand-checked split summary
diagnostics, skipped output mode, caveated report and log creation, helper-use
monkeypatch checks, invalid configuration rejection, `main()` output writing,
forbidden import checks, and caveated profitability-language checks.

This change does not modify source feature formulas, diagnostics helper
behavior, validation helper behavior, CSV loader behavior, generated reports,
backtester behavior, metrics, LEAN code, alpha modules, normalization,
combination, or strategy logic. It does not fetch real data, download data,
add vendor APIs, add credentials, add live or paper trading, add brokerage or
order execution, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_synthetic_split_ic_rank_ic_demo.py
11 passed

python -m pytest -q
308 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-05 - Public Repository Metadata And License Polish

This documentation-stage checkpoint records the owner decision to publish the
repository under Apache-2.0 and updates the public GitHub shell around the
already-polished README landing page.

The file changes add the official Apache-2.0 root `LICENSE`, add a concise
`CITATION.cff` using only the repository URL, SPDX license identifier, GitHub
owner login, and observed git author name, and add
`docs/assets/social_preview.svg` as an original source asset for a possible
future GitHub social-preview upload. The README license badge now links to the
root license file, and the current-status language now states the Apache-2.0
license selection.

Assumption: this stage is public-presentation metadata work only. It does not
change `src/`, `tests/`, `research/`, `reports/`, data loading, factor formulas,
diagnostics, backtester behavior, generated result numbers, private-data
protections, LEAN behavior, live or paper trading scope, brokerage integration,
order execution, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
297 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only

gh api licenses/apache-2.0 --jq .spdx_id
Apache-2.0
```

---

## 2026-06-05 - Synthetic Train/Validation/Test Split Helper

This code milestone added `src/features/validation.py` and
`tests/test_validation.py` after the current roadmap gap refresh merged.

Assumption: the next safe implementation stage is the deterministic
train/validation/test split helper recommended by
`docs/current_roadmap_gap_refresh.md`. The helper is deliberately limited to
already-prepared date indexes and numeric factor panels. It does not fetch
data, calculate returns, choose parameters, run a backtest, modify reports, or
interpret performance.

The new `make_train_validation_test_split()` helper validates a
`DatetimeIndex`, preserves chronological order, rejects duplicate or unsorted
dates, applies inclusive train, validation, and test boundaries, requires
non-empty windows, and returns a `TrainValidationTestSplit` dataclass. The new
`split_panel_by_train_validation_test()` helper slices an already-prepared
numeric panel by those dates and preserves missing values instead of filling
or coercing them into synthetic observations.

The test coverage includes hand-calculated date windows, timestamp boundary
handling, split ordering, panel slicing, missing-value preservation, invalid
date indexes, invalid boundary order, empty windows, non-date boundaries,
invalid timestamp strings, non-numeric panels, mismatched indexes, and an
import guardrail check.

This change does not modify research scripts, generated reports, CSV loader
behavior, diagnostics behavior, backtester behavior, metrics, factor formulas,
normalization, combination, LEAN code, or strategy logic. It does not add real
data fetching, downloads, credentials, live or paper trading, brokerage,
order execution, a LEAN run, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_validation.py
25 passed

python -m pytest -q
297 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-05 - Current Roadmap Gap Refresh

This documentation-only checkpoint added
`docs/current_roadmap_gap_refresh.md` after PR #46 merged.

Assumption: after the LEAN signal-only momentum draft merged, the safest next
stage is to refresh the roadmap before adding more code. The older
`docs/original_goal_gap_analysis.md` still captures the original objective,
but several of its recommended next stages are now complete: local CSV fixture
smoke/demo work, IC and Rank IC helpers, quantile spread diagnostics, LEAN
planning, the non-executing LEAN scaffold, and the LEAN signal-only metadata
draft.

The checkpoint records current implementation traceability, remaining gaps,
guardrail status, and a refreshed roadmap. It recommends the next
implementation stage as a synthetic train/validation/test split helper because
validation-discipline support is now a larger gap than adding another factor
or duplicating already-implemented diagnostics.

This change does not modify `src/`, tests, research scripts, generated
reports, CSV loader behavior, diagnostics behavior, backtester behavior,
metrics, factor formulas, normalization, combination, LEAN code, or strategy
logic. It does not add real data fetching, downloads, credentials, live or
paper trading, brokerage, order execution, a LEAN run, or profitability
claims.

Validation at the time of this entry:

```text
python -m pytest -q
272 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-05 - LEAN Signal-Only Momentum Draft

This code milestone added a pure-Python LEAN-adjacent signal-only draft after
the signal-only design merged and later public-facing README/CI stages were
also merged.

Assumption: the current next safe stage is the implementation recommended by
`docs/lean_signal_only_draft_design.md`: a metadata-only
`lean/signal_only_momentum_draft.py` plus static guardrail tests. The stage is
code-changing, but it remains pre-runtime and signal-only. It does not import
LEAN runtime symbols, create a runnable QuantConnect algorithm, create
`config.json`, run LEAN, fetch data, read credentials, configure brokerage,
define orders, calculate returns, produce reports, or claim profitability.

The new draft records the signal name, 12-1 momentum lookback and skip-window
metadata, required input fields, timing contract fields, diagnostic field
names, guardrails, and caveats. It exposes
`describe_signal_only_momentum_draft()` so reviewers can inspect the metadata
without calculating a signal or touching data.

The new `tests/test_lean_signal_only_draft_scope.py` statically checks that
the draft exists, remains non-runnable, avoids banned runtime/data/credential
imports, avoids LEAN runtime and order/brokerage calls, declares the required
timing and diagnostic metadata, returns no performance or order outputs, and
keeps README guardrail language visible. `lean/README.md` now documents the
signal-only draft and its focused validation command.

This change does not modify `src/`, research scripts, generated reports, CSV
loader behavior, diagnostics behavior, backtester behavior, metrics, factor
formulas, normalization, combination, or strategy logic. It does not add real
data fetching, downloads, credentials, live or paper trading, brokerage,
order execution, runnable LEAN code, a LEAN run, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_lean_signal_only_draft_scope.py
8 passed

python -m pytest -q tests/test_lean_smoke_test_scope.py tests/test_lean_signal_only_draft_scope.py
14 passed

python -m pytest -q
272 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - GitHub Actions CI Badge

This CI/documentation milestone adds the first repository GitHub Actions
workflow after the public landing-page polish merged.

Assumption: the next safe public-facing stage is a minimal CI workflow that
uses the repository's existing Python packaging and validation commands. The
workflow installs dependencies with `python -m pip install -e ".[dev]"`, which
matches the existing `pyproject.toml` optional dev dependency setup, and uses
Python 3.11 to satisfy the documented `requires-python >=3.11` boundary.

The new `.github/workflows/ci.yml` workflow is named `CI` and runs on pull
requests targeting `main` and pushes to `main`. It checks out the repository,
sets up Python 3.11, installs project and dev dependencies, runs
`python -m pytest -q`, runs `python -m compileall src tests research`, and
runs `python -m compileall lean`. The README replaces the static local-test
status label with a live badge for the new workflow file.

This change does not modify `src/`, tests, research scripts, generated reports,
CSV loader behavior, diagnostics behavior, backtester behavior, metrics, factor
formulas, normalization, combination, LEAN scaffold behavior, strategy logic,
private-data protections, result numbers, repository visibility, or license
state. It does not add real data fetching, credentials, live trading,
brokerage integration, order execution, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
264 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only

README badge/workflow target check
passed
```

---

## 2026-06-04 - Public GitHub Landing Page Polish

This documentation-only milestone improves the public README as a newcomer
landing page after the LEAN signal-only draft design merged.

Assumption: the next safe public-facing stage is presentation polish rather
than additional research logic. The update keeps the current research scope
unchanged and makes the repository easier to evaluate from the GitHub first
screen.

The README now has a concise tagline, truthful static status labels, a short
description of what the repository is, runnable synthetic/local-fixture demo
commands, a beginner-friendly PowerShell Quick Start, a local CSV fixture demo
walkthrough, a project map, links to key reports and demo files, and an
explicit safety/scope section. The new `docs/assets/research_workflow.svg`
diagram is an original workflow visual that explains the research process
without implying live trading, brokerage integration, order execution, or
profitability.

This change does not modify `src/`, tests, research scripts, generated reports,
CSV loader behavior, diagnostics behavior, backtester behavior, metrics, factor
formulas, normalization, combination, LEAN scaffold behavior, strategy logic,
private-data protections, or result numbers. It does not add a license file,
GitHub Actions workflow, real data fetching, credentials, live trading,
brokerage integration, order execution, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
264 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

README relative-link sanity check
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - LEAN Signal-Only Draft Design

This documentation-only milestone added
`docs/lean_signal_only_draft_design.md` after the runnable draft readiness
decision merged.

Assumption: after PR #42 merged, the next unblocked safe stage is the
signal-only draft design that PR #42 explicitly recommended. The design keeps
the next LEAN-adjacent code boundary pure Python and metadata-only, without
LEAN runtime imports, local or cloud LEAN execution, real data access,
credentials, live trading, paper trading, brokerage integration, order
execution, or profitability claims.

The design defines the purpose, decision, future file boundary, timing
contract, static validation plan, out-of-scope items, stop conditions, and the
recommended next stage. It narrows the next possible code PR to
`lean/signal_only_momentum_draft.py` and
`tests/test_lean_signal_only_draft_scope.py`, with optional updates to
`lean/README.md`, durable logs, and `CHANGELOG.md` if that future PR documents
the scope.

This change does not modify `src/`, tests, research scripts, generated
reports, LEAN code, CSV loader behavior, diagnostics behavior, backtester
behavior, metrics, factor formulas, normalization, combination, or strategy
logic. It does not add `AlgorithmImports`, `QCAlgorithm`, `config.json`, data
fetching, downloads, credentials, live or paper trading, brokerage, order
execution, a LEAN run, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
264 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - LEAN Runnable Draft Readiness Decision

This documentation-only milestone added
`docs/lean_runnable_draft_readiness_decision.md` after the LEAN scaffold review
checklist merged.

Assumption: after PR #41 merged, the next safe stage is an
implementation-readiness decision rather than a runnable LEAN algorithm draft.
The current guardrails still prohibit real market data fetching, downloads,
credentials, live trading, paper trading, brokerage integration, order
execution, and profitability claims. A normal runnable LEAN draft would likely
introduce runtime imports, platform data semantics, portfolio target calls,
orders, fills, fee models, slippage models, and backtest outputs before those
boundaries are explicitly approved.

The decision records that the repository is not yet ready for runnable LEAN
code under current guardrails. It identifies blockers around runtime imports,
data-source semantics, order semantics, credential/account boundaries, and
result interpretation. It recommends the next stage as a documentation-only
LEAN signal-only draft design that can define whether any future code PR may
import LEAN runtime symbols and how static validation should separate signal
metadata from order execution.

This change does not modify `src/`, tests, research scripts, generated
reports, the LEAN scaffold code, CSV loader behavior, diagnostics behavior,
backtester behavior, metrics, factor formulas, normalization, combination, or
strategy logic. It does not add `AlgorithmImports`, `QCAlgorithm`,
`config.json`, data access, credentials, live or paper trading, brokerage,
order execution, a LEAN run, or profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
264 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - LEAN Scaffold Review Checklist

This documentation-only milestone added `docs/lean_scaffold_review_checklist.md`
after the minimal non-executing LEAN scaffold merged.

Assumption: after PR #40 merged, the next unblocked safe stage is a scaffold
review checklist before deciding whether a future PR can safely create a
runnable LEAN draft. This keeps the workflow moving while avoiding a premature
runtime implementation that could require platform access, credentials, real
data, brokerage integration, order execution, live trading, paper trading, or
performance interpretation.

The checklist defines the current scaffold files under review, required review
questions, static checks, safe expansion criteria, stop conditions, and the
recommended next stage: a narrow implementation-readiness decision. It does
not approve a runnable LEAN algorithm, `config.json`, local or cloud LEAN run,
data download, credential path, order path, or profitability claim.

This change does not modify `src/`, tests, research scripts, generated
reports, the LEAN scaffold code, CSV loader behavior, diagnostics behavior,
backtester behavior, metrics, factor formulas, normalization, combination, or
strategy logic.

Validation at the time of this entry:

```text
python -m pytest -q
264 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - Minimal Non-Executing LEAN Smoke-Test Scaffold

This scaffold milestone added a first `lean/` directory after the LEAN
implementation planning checkpoint merged.

Assumption: after PR #39 merged, the next unblocked safe stage is the planned
minimal non-executing LEAN scaffold with static guardrail tests. The scaffold
is deliberately metadata-only and does not import the LEAN runtime, create a
`config.json`, run a local or cloud backtest, fetch data, read credentials,
connect to a broker, enable live trading or paper trading, submit orders, or
interpret performance.

The new `lean/README.md` records the scaffold purpose, current files, local
validation commands, and stop conditions. The new
`lean/smoke_test_algorithm.py` defines review metadata, configuration fields,
the timing contract, diagnostic field names, and guardrail constants without
creating a runnable QuantConnect algorithm. The new
`tests/test_lean_smoke_test_scope.py` statically validates the scaffold file
boundary, rejects external data and credential imports, rejects order and
brokerage calls, and checks for timing, diagnostic, and caveat coverage.

This change does not modify `src/`, research scripts, generated reports, CSV
loader behavior, diagnostics behavior, backtester behavior, metrics, factor
formulas, normalization, combination, or strategy logic. It does not fetch
data, download data, connect to a broker, place orders, add credentials,
enable live trading, add paper trading, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_lean_smoke_test_scope.py
6 passed

python -m pytest -q
264 passed

python -m compileall src tests research
passed

python -m compileall lean
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - LEAN Implementation Planning Checkpoint

This documentation-only milestone added
`docs/lean_implementation_planning_checkpoint.md` after PR #38 merged.

Assumption: after the LEAN smoke-test design note merged, the next unblocked
safe LEAN-related stage is an implementation planning checkpoint before any
LEAN algorithm file or project scaffold. This keeps the workflow moving while
preserving the merge gate and avoiding external platform access, credentials,
real data downloads, brokerage integration, order execution, live trading,
paper trading, and performance interpretation.

The checkpoint chooses the intended boundary for the first future LEAN code
PR: `lean/README.md`, `lean/smoke_test_algorithm.py`,
`tests/test_lean_smoke_test_scope.py`, `docs/engineering_log.md`, and
`CHANGELOG.md`. It also defines the future algorithm draft scope, static local
validation strategy, review gates, stop conditions, and the recommended next
stage: a minimal non-executing LEAN scaffold with static guardrail tests.

This change does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, diagnostics behavior, backtester behavior,
metrics, data access, or strategy logic. It does not fetch data, download data,
connect to a broker, place orders, add credentials, enable live trading, add
paper trading, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
258 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - LEAN Smoke-Test Design Note

This documentation-only milestone added `docs/lean_smoke_test_design.md` after
the LEAN parity checklist merged.

Assumption: after PR #37 merged, the next unblocked safe LEAN-related stage is
a smoke-test design note, not LEAN algorithm code or a project scaffold. This
keeps the stage aligned with the checklist recommendation while avoiding
external platform access, credentials, real data downloads, brokerage
integration, order execution, live trading, paper trading, or performance
interpretation.

The design note defines future smoke-test preconditions, a minimal future
scenario, a timing contract, smoke-test assertions, diagnostics to preserve,
local-vs-LEAN comparison priorities, experiment-record shape, stop conditions,
and the next planning checkpoint before any future LEAN code PR.

This change does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, diagnostics behavior, backtester behavior,
metrics, data access, or strategy logic. It does not fetch data, download data,
connect to a broker, place orders, add credentials, enable live trading, add
paper trading, or make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
258 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - LEAN Parity Checklist Planning

This documentation-only milestone added `docs/lean_parity_checklist.md` after
the refreshed QuantConnect/LEAN plan merged.

Assumption: after PR #36 merged and baseline validation passed, the next
unblocked safe stage from `docs/quantconnect_lean_plan.md` is a LEAN parity
checklist or smoke-test plan. The stage is kept documentation-only because the
repository still needs explicit parity gates before any LEAN algorithm,
platform scaffold, real data, credentials, brokerage integration, order
execution, live trading, or performance interpretation.

The checklist maps current local evidence to future LEAN smoke-test
assertions: 12-1 momentum timing, `alpha_009` feature-only status, strict data
validation mindset, IC / Rank IC / quantile spread diagnostics, benchmark
configuration, fees, slippage, cash buffer, simulated order-accounting caveats,
experiment-log requirements, local-vs-LEAN parity review, and stop conditions.

This change does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, diagnostics behavior, backtester behavior,
metrics, data access, or strategy logic. It does not fetch data, download data,
connect to a broker, place orders, add credentials, enable live trading, or
make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
258 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - QuantConnect/LEAN Plan Refresh After CSV Diagnostics

This documentation-only milestone refreshed `docs/quantconnect_lean_plan.md`
after the local CSV fixture workflow demo merged.

Assumption: after PR #35 merged and baseline validation passed, the next
unblocked safe stage from `docs/original_goal_gap_analysis.md` is Stage F:
refresh the QuantConnect/LEAN plan from the current local modules. The stage is
kept plan-only because the repository is not ready for LEAN algorithm code,
real data, platform access, credentials, brokerage integration, order
execution, or performance interpretation.

The updated plan now records the current local status before any LEAN code:
strict local CSV loaders, committed synthetic CSV fixtures, the local CSV
fixture workflow demo, `alpha_009`, IC / Rank IC diagnostics, quantile spread
diagnostics, experiment logs, and the experiment registry. It maps those local
components to future LEAN planning concepts while preserving the distinction
between local synthetic fixtures, user-provided local CSV work, and platform
subscriptions/history.

The plan also adds diagnostic mapping guidance for IC, Rank IC, and quantile
spread exports from a future LEAN smoke run. Forward returns remain evaluation
targets only and must not become signal inputs. Quantile spread remains a
diagnostic, not a strategy-validation or profitability claim. The recommended
next LEAN-related stage is a parity checklist or smoke-test plan, not an
algorithm implementation.

This change does not modify source code, tests, research scripts, generated
reports, CSV loader behavior, diagnostics behavior, backtester behavior,
metrics, data access, or strategy logic. It does not fetch data, download data,
connect to a broker, place orders, add credentials, enable live trading, or
make profitability claims.

Validation at the time of this entry:

```text
python -m pytest -q
258 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

---

## 2026-06-04 - Local CSV Fixture Research Workflow Demo

This code-and-report milestone added a synthetic local CSV fixture workflow
demo after the local CSV loader smoke tests, synthetic IC / Rank IC
diagnostics, and synthetic quantile spread diagnostics had merged.

Assumption: after PR #34 merged, the next unblocked safe stage from
`docs/original_goal_gap_analysis.md` is Stage E: run a complete local-file
workflow on committed synthetic CSV fixtures only. The stage is intentionally
small and uses the already-reviewed local CSV loader, `alpha_009`, IC, Rank IC,
and quantile spread helpers instead of introducing new source-layer behavior.

The new `research/local_csv_fixture_workflow_demo.py` script loads the
committed synthetic adjusted-close and benchmark fixtures under
`tests/fixtures/local_csv_loader_smoke/`, verifies benchmark date alignment,
computes `alpha_009` as a close-only research feature with a one-row diagnostic
window, computes next-row forward returns as evaluation targets only, and runs
IC, Rank IC, and quantile spread diagnostics. The forward returns are not
feature inputs, not a portfolio rule, and not an execution assumption.

The generated report and JSON sidecar log are synthetic fixture diagnostics
only. They are included to prove that the local CSV path can participate in a
caveated, auditable workflow without using real data, downloads, vendor APIs,
credentials, live trading, brokerage integration, order execution, or
profitability claims. The experiment registry is refreshed so the new
synthetic local CSV workflow log is discoverable alongside earlier synthetic
demos.

Focused tests in `tests/test_local_csv_fixture_workflow_demo.py` cover fixture
loading, date and asset alignment, deterministic outputs, report and log
caveats, output-suppression behavior for tests, use of existing loader/feature
and diagnostic helpers, rejection of absolute fixture paths, config
validation, import guardrails, and caveated profitability language.

This change does not modify CSV loader behavior, feature formulas,
normalization, factor combination, diagnostics, backtester behavior, metrics,
or external data access. It does not run a backtest or claim that `alpha_009`
is useful on real market data.

Validation at the time of this entry:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
11 passed

python -m pytest -q
258 passed

python -m compileall src tests research
passed
```

---

## 2026-06-04 - Synthetic Quantile Spread Diagnostics

This code milestone added synthetic-first quantile spread diagnostics to
`src/features/diagnostics.py`.

Assumption: after the synthetic IC / Rank IC diagnostics PR merged, the next
unblocked safe stage from `docs/original_goal_gap_analysis.md` is Stage D: add
a quantile-bucket diagnostic helper using synthetic panels first. The helper is
kept in the existing diagnostics module because it is research visibility
infrastructure, not a strategy, backtest integration, report generator, or data
loader.

The new `factor_quantile_spread` helper computes per-date cross-sectional
factor quantile diagnostics against an already-aligned forward-return
evaluation panel. The helper reports bottom-quantile mean return,
top-quantile mean return, top-minus-bottom spread, valid asset count, and edge
quantile counts. `forward_returns` is treated as an evaluation target supplied
by the caller, not as a feature input.

Missing values are handled conservatively: each date uses only overlapping
non-missing factor and return pairs; missing values are not filled,
forward-filled, backward-filled, or converted to zeros. Dates with too few
valid assets, too few distinct factor values to form the requested quantiles,
or too few assets in either edge quantile return `NaN` for the return and
spread columns while preserving coverage counts.

Focused tests in `tests/test_diagnostics.py` cover hand-calculated
top-minus-bottom spreads, pairwise missing-value overlap without filling,
low-coverage dates, insufficient distinct factor values, minimum edge-bucket
size checks, date and asset alignment validation, invalid string-value
rejection, and quantile-parameter validation.

This change does not modify CSV loader behavior, local CSV fixtures, synthetic
reports, research scripts, feature formulas, normalization, factor combination,
backtester behavior, metrics, data access, execution assumptions, or
performance claims. It does not fetch data, download data, add vendor access,
introduce live trading, add brokerage or order-execution logic, store
credentials, or make profitability claims.

Validation:

```text
python -m pytest -q tests/test_diagnostics.py
58 passed

python -m pytest -q
247 passed

python -m compileall src tests research
passed
```

---

## 2026-06-04 - Synthetic IC And Rank IC Diagnostics

This code milestone added synthetic-first information coefficient diagnostics
to `src/features/diagnostics.py`.

Assumption: after the local CSV loader smoke demo merged, the next unblocked
safe stage from `docs/original_goal_gap_analysis.md` is Stage C: add IC and
Rank IC helpers using synthetic panels first. The implementation is kept in the
existing diagnostics module because the helper is diagnostic research
infrastructure, not a strategy, backtest integration, report generator, or data
loader.

The new `factor_information_coefficient` helper computes a per-date
cross-sectional correlation between an already-prepared factor panel and an
already-aligned forward-return evaluation panel. The helper does not compute
returns, shift dates, select assets, fill missing values, connect to the
backtester, or interpret results. `forward_returns` is explicitly treated as an
evaluation target supplied by the caller, not as a feature input.

The new `factor_rank_information_coefficient` helper wraps the same alignment
and missing-data behavior with Spearman correlation for Rank IC. Dates with
fewer than `min_periods` overlapping valid assets return `NaN`; missing values
are not filled, forward-filled, backward-filled, or converted to zeros.

Focused tests in `tests/test_diagnostics.py` cover hand-calculated Pearson IC,
hand-calculated Spearman Rank IC, pairwise missing-value overlap without
filling, low-coverage dates returning `NaN`, date and asset alignment
validation, invalid string-value rejection, method validation, and
`min_periods` validation. The existing diagnostics import-boundary test still
guards against adding backtest, alpha, reporting, vendor download, or real-data
imports to the diagnostics module.

This change does not modify CSV loader behavior, local CSV fixtures, synthetic
reports, research scripts, feature formulas, normalization, factor combination,
backtester behavior, metrics, data access, execution assumptions, or
performance claims. It does not fetch data, download data, add vendor access,
introduce live trading, add brokerage or order-execution logic, store
credentials, or make profitability claims.

Validation:

```text
python -m pytest -q tests/test_diagnostics.py
38 passed

python -m pytest -q
227 passed

python -m compileall src tests research
passed
```

---

## 2026-06-03 - Local CSV Loader Synthetic Fixture Smoke Demo

This test-focused milestone added a committed synthetic local CSV fixture set
and smoke tests for the existing strict local CSV loader.

Assumption: the next stage recommended by
`docs/original_goal_gap_analysis.md` should be implemented as a focused test
and fixture stage, not as a research script or generated report. This keeps the
stage deterministic and avoids interpreting any result as market evidence.

The new fixtures under `tests/fixtures/local_csv_loader_smoke/` are synthetic,
small, local-only CSV files:

- `synthetic_adjusted_close.csv`
- `synthetic_adjusted_close_with_missing.csv`
- `synthetic_benchmark.csv`

The new smoke tests in `tests/test_local_csv_loader_smoke_demo.py` verify that
the existing loader can read a local wide adjusted-close panel, preserve
expected date indexes and asset columns, produce float-valued panels, align a
benchmark series to the same dates, expose audit summary metadata, and enforce
the missing-value policy. Missing values are rejected by default and preserved
only through explicit `allow_missing=True`; no fill, forward-fill,
backward-fill, or zero default is introduced.

This change does not modify CSV loader source code, feature calculations,
backtester behavior, metrics, research scripts, generated reports,
normalization, factor combination, diagnostics, data access, execution
assumptions, or performance claims. It does not fetch data, download data, add
vendor access, introduce live trading, add brokerage or order-execution logic,
store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q tests/test_local_csv_loader_smoke_demo.py tests/test_csv_loader.py
22 passed

python -m pytest -q
212 passed

python -m compileall src tests research
passed
```

---

## 2026-06-03 - Original Goal Gap Analysis Checkpoint

This documentation-only checkpoint added
`docs/original_goal_gap_analysis.md` before starting any new feature stage.

The analysis compares the original project objective from `PROJECT_SPEC.md`,
`README.md`, and `docs/project_overview.md` against the current implemented
state recorded in checkpoint reports, `docs/engineering_log.md`,
`CHANGELOG.md`, `EXPERIMENT_LOG.md`, `docs/worldquant_alpha_catalog.md`, and
`docs/quantconnect_lean_plan.md`.

The current repository has progressed from governance and skeleton work to a
tested simulated research pipeline with 12-1 momentum, a long-only backtester,
synthetic demos, synthetic experiment logs and registry, WorldQuant catalog and
`alpha_009`, reusable operators, normalization, winsorization, factor
combination, diagnostics, local CSV interface planning, a strict local CSV
loader, real-data readiness documentation, and QuantConnect/LEAN planning.

The main remaining gap is that the project has not yet completed a full
local-CSV-based research study. No real-data IC, Rank IC, quantile spread,
train/validation/test split, benchmark/universe study, or LEAN implementation
exists yet. Paper and live trading remain intentionally out of scope.

The recommended next stage after this checkpoint PR is a local CSV loader smoke
demo using a committed synthetic local fixture only. That stage should verify
local-file workflow wiring without fetching data, interpreting market evidence,
or adding trading functionality.

During the startup checks for this checkpoint, a low-risk workflow command
issue occurred:

- Original mistake: a GitHub PR state command used Bash-style `|| true` inside
  PowerShell.
- Consequence: PowerShell rejected the command before `gh pr view 30` could
  run.
- Evidence: `The token '||' is not a valid statement separator in this
  version.`
- Investigation: the command was written with a Bash fallback despite the
  repository running in a Windows PowerShell shell.
- Correction attempt: reran PR checks as separate PowerShell-compatible
  commands.
- Final fix: `gh pr list --state open` returned no open PRs, and
  `gh pr view 30` confirmed PR #30 was merged.
- Verification: baseline validation passed before the documentation was
  created: `python -m pytest -q` reported 209 passed and
  `python -m compileall src tests research` passed.
- Remaining caveat: future shell snippets in this repository should use
  PowerShell-compatible fallbacks rather than Bash `|| true`.
- Prevention: split optional `gh` probes into separate PowerShell commands or
  use explicit PowerShell error handling.

An additional pre-publish formatting issue occurred during commit:

- Original mistake: `git diff --cached --check` and `git commit` were run in
  the same PowerShell command block.
- Consequence: the whitespace check reported an issue, but the commit still
  completed because the command block did not stop after the failed check.
- Evidence: `docs/original_goal_gap_analysis.md:214: new blank line at EOF.`
- Investigation: the new checkpoint document ended with an extra blank line,
  and the command sequencing allowed the commit to proceed before fixing it.
- Correction attempt: inspected the end of the document, removed the extra EOF
  blank line, and amended the same commit instead of creating a second cleanup
  commit.
- Final fix: the final branch commit contains the corrected document and
  updated engineering log.
- Verification: `git diff --check origin/main..HEAD` was rerun after the amend
  and passed.
- Remaining caveat: Windows LF-to-CRLF warnings can still appear, but they are
  not whitespace errors.
- Prevention: run `git diff --cached --check` as a separate gating command
  before `git commit`, or explicitly stop on failure before committing.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, metrics, CSV loader
behavior, normalization, factor combination, diagnostics, data access,
execution assumptions, or performance claims. It does not fetch data, download
data, add vendor access, introduce live trading, add brokerage or
order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
209 passed

python -m compileall src tests research
passed
```

---

## 2026-06-03 - WorldQuant Alpha Catalog Status Refresh

This documentation-only milestone refreshed `docs/worldquant_alpha_catalog.md`
after the post-CSV checkpoint identified stale catalog-era wording.

Assumption: the post-CSV checkpoint recommendation to refresh the WorldQuant
catalog is the next unblocked safe stage because PR #29 was merged, `main` was
synced, baseline validation passed, and there were no open pull requests.

The catalog now distinguishes the original Stage 1 classification from the
current repository status: the reusable operator layer exists, `alpha_009` is
implemented and tested as a close-only research feature, other
WorldQuant-style alphas remain unimplemented, and there is no dedicated
WorldQuant-style alpha backtest integration.

The refresh also clarifies that `alpha_009` is not a full strategy, not a
trading recommendation, not connected to a dedicated alpha strategy backtest,
and not evidence of profitability. Remaining close-only candidates require
separate formula review and tests. `alpha_012` remains blocked on volume plus
close schema support, `alpha_101` remains blocked on OHLC support, and VWAP,
market-cap, and industry-neutral categories remain deferred.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, metrics, CSV loader
behavior, normalization, factor combination, diagnostics, data access,
execution assumptions, or performance claims. It does not fetch data, download
data, add vendor access, introduce live trading, add brokerage or
order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
209 passed

python -m compileall src tests research
passed
```

---

## 2026-06-03 - Active Goal Behavior Rules

This workflow-control milestone updated the long-running staged workflow rules
for bounded autonomous execution.

Assumption: the user's active-goal clarification should be persisted as
controller and Skill guidance, not implemented as source-code behavior.

The controller now states that low-risk ambiguity should be handled by making a
reasonable assumption, recording it in the final report and relevant durable
log, and continuing. It also distinguishes missing workflow/documentation
scaffolds, which can be created in separate workflow-control PRs, from missing
product-behavior artifacts, which require a stop report.

The stop conditions were expanded to cover dirty working trees before new
stages, unclear requirements that could cause destructive or broad
architecture changes, missing credentials or external access, new production
dependencies, unsafe test failures, high or medium review issues, security,
privacy, data-loss, or irreversible-operation risks, scope conflicts with
project governance, and ready PR gates requiring human review or merge.

The staged workflow Skill was updated with the same low-risk ambiguity and
missing-file behavior so future sessions do not require a fresh prompt after
every small step while remaining bounded by safety, scope, validation, and PR
review gates.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, metrics, CSV loader
behavior, alpha formulas, normalization, factor combination, diagnostics, data
access, execution assumptions, or performance claims. It does not fetch data,
download data, add vendor access, introduce live trading, add brokerage or
order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
209 passed

python -m compileall src tests research
passed

.\scripts\audit-skills.ps1
passed
```

---

## 2026-06-03 - Long-Running Workflow Control Scaffolding

This workflow-control milestone added the supporting process artifacts that the
long-running staged workflow now expects to read before continuing:
`docs/codex_long_running_controller.md`, `docs/decision_log.md`,
`docs/troubleshooting_log.md`, `CHANGELOG.md`, and
`scripts/audit-skills.ps1`.

The controller defines startup checks, merge gates, stage-selection guidance,
stop conditions, logging requirements, validation checks, Skill audit use, and
the rule to pause after PR creation without merging. The decision and
troubleshooting logs capture durable workflow decisions and detailed
failure-to-fix records. The changelog records user-visible repository changes.
The Skill audit script checks local repository Skill files for required
frontmatter, headings, and balanced Markdown code fences.

The staged workflow Skill was updated to read the new controller/log artifacts
and to run `.\scripts\audit-skills.ps1` for workflow-control or Skill changes.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, metrics, CSV loader
behavior, alpha formulas, normalization, factor combination, diagnostics, data
access, execution assumptions, or performance claims. It does not fetch data,
download data, add vendor access, introduce live trading, add brokerage or
order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
209 passed

python -m compileall src tests research
passed

.\scripts\audit-skills.ps1
passed
```

---

## 2026-06-03 - Beginner-Facing Project Overview

This documentation-only milestone added `docs/project_overview.md` and linked
it from `README.md`.

The overview explains the repository as an AI-assisted, simulated, auditable
equity factor research pipeline. It defines factor, signal, portfolio,
strategy, and conclusion; summarizes current components; lists what the project
is not; records evaluation standards for factor research; and keeps current
limitations visible for synthetic-only results, `alpha_009`, staged local CSV
readiness, and future QuantConnect/LEAN work.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, metrics, CSV loader
behavior, alpha formulas, normalization, factor combination, diagnostics, data
access, execution assumptions, or performance claims. It does not fetch data,
download data, add vendor access, introduce live trading, add brokerage or
order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
209 passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Project Staged Workflow Skill

This research-process milestone added
`.agents/skills/staged-quant-workflow/SKILL.md` so future Codex sessions can
resume the long-running staged workflow without requiring the user to paste a
fresh detailed prompt for every phase.

The Skill records the recurring workflow gates: verify current repo and PR
state, stop at unmerged PR gates, sync latest `main` after a merge, rerun
baseline validation, choose the next stage from current checkpoint evidence,
keep each branch and PR narrowly scoped, open documentation-only or low-risk
checkpoint PRs ready for review, gate code-changing PRs on tests plus read-only
review, and pause after PR creation without merging.

It also preserves the project guardrails: no real data fetching, downloads,
vendor APIs, live trading, brokerage integration, order execution, credentials,
or profitability claims. It records the problem-logging rule that technical,
methodological, environment, testing, workflow, or reasoning problems require a
durable log entry covering the initial mistake, consequence, evidence,
investigation, correction attempts, final fix, validation, remaining caveats,
reflection, and prevention.

This change does not modify source code, tests, strategy logic, feature
calculations, backtester behavior, metrics, generated reports, research scripts,
data access, execution assumptions, or performance claims.

---

## 2026-06-02 - Post-CSV Checkpoint Review

This documentation-only milestone added `docs/post_csv_checkpoint_report.md`
after the CSV interface design, local CSV loader, real-data readiness audit,
LEAN validation mapping, local CSV experiment-log requirements, and CSV loader
missing-value bugfix milestones were merged.

The checkpoint records the current state of the local CSV infrastructure,
baseline validation, read-only guardrail review, stage traceability, remaining
low-severity documentation and roadmap issues, and the recommended next stage:
refreshing the WorldQuant alpha catalog and roadmap status before any new alpha
or data-schema implementation.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, CSV loader behavior, or
synthetic demos. It does not fetch data, download data, add vendor access,
introduce live trading, add brokerage or order-execution logic, store
credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
209 passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - CSV Loader Missing-Value Debug And Fix

This bugfix corrected strict missing-value validation in the local CSV loader
after a WSL-only test failure exposed a pandas version difference.

Initial mistake:

- The first fix assumed that `pd.read_csv(..., keep_default_na=False,
  dtype=str)` was sufficient to preserve raw CSV values through validation.
- The missing-value detector still checked sentinel strings only when
  `values.dtype == object`.
- That assumption held in the Windows validation environment, where the focused
  CSV loader tests and full test suite passed, but it did not cover WSL with
  pandas 3.0.3.

Consequence:

- In WSL, `pd.read_csv(..., dtype=str)` produced a pandas string dtype rather
  than an `object` dtype.
- `_missing_value_mask` therefore skipped the string-sentinel branch for an
  empty wide-price value.
- The empty string was then passed to `pd.to_numeric`, which converted it to
  `NaN` instead of raising before the loader's strict default policy could
  reject it.
- As a result, `load_wide_price_csv(..., allow_missing=False)` accepted a blank
  numeric field that should have failed.

Failing evidence:

```text
tests/test_csv_loader.py::test_load_wide_price_csv_rejects_invalid_or_missing_numeric_values_by_default[]
bad_value = ""
Failed: DID NOT RAISE any of (<class 'TypeError'>, <class 'ValueError'>)
```

The WSL run also showed large apparent diffs across docs, reports, research
scripts, source modules, and tests. Review showed those broad diffs were
line-ending noise from the Windows/WSL working tree, not intended source
changes.

Investigation:

- Confirmed WSL imported the expected module:
  `src/data/csv_loader.py`.
- Confirmed WSL was using pandas 3.0.3.
- Printed `_read_local_csv` and verified it already used
  `keep_default_na=False, dtype=str`.
- Probed a temporary CSV containing a blank `AAPL` field. WSL read the column
  with dtype `str`, represented the blank as `""`, and returned
  `_missing_value_mask == [False, False]`.
- Confirmed `_parse_numeric_column` then returned `[100.0, NaN]` and the loader
  accepted the file instead of raising.

Correction attempts:

- The first Windows-side correction added `dtype=str` and expanded tests for
  `NA` and whitespace-only values. That made Windows tests pass, but it did not
  address pandas string dtype in WSL.
- Applying the saved WSL patch directly on the independent bugfix branch worked
  functionally but introduced whole-file CRLF/LF whitespace noise. That patch
  was restored before commit.

Final fix:

- `_read_local_csv` now reads local CSV files with
  `pd.read_csv(path, keep_default_na=False, dtype=str)` so raw string values are
  preserved before validation.
- `_missing_value_mask` now checks both `object` dtype and pandas string dtype
  via `pd.api.types.is_string_dtype(values.dtype)` before applying the sentinel
  set.
- `tests/test_csv_loader.py` now covers `""`, whitespace-only strings, `nan`,
  `NaN`, `NA`, `null`, and a nonnumeric `bad` value for strict default
  validation.

Verification:

```text
WSL python -m pytest -q tests/test_csv_loader.py
19 passed

WSL python -m pytest -q
209 passed

WSL python -m compileall src tests research
passed

git diff --check origin/main..HEAD
passed
```

Scope review:

- Meaningful branch diff was limited to `src/data/csv_loader.py` and
  `tests/test_csv_loader.py`.
- The direct WSL patch application was rejected as a commit candidate because
  it carried line-ending noise.
- The committed branch used only the minimal semantic patch.

Remaining caveats:

- Windows and WSL can still display noisy diffs if line endings are touched
  broadly.
- Future CSV loader changes should inspect both normal diffs and
  `git diff --ignore-space-at-eol` before staging.
- Environment-specific behavior should be checked when pandas dtype handling is
  part of the bug.

Prevention:

- Treat pandas dtype assumptions as version-sensitive.
- Keep missing-value checks independent of only one dtype spelling.
- When fixing validation behavior, probe the raw value, dtype, missing mask,
  conversion result, and final loader behavior in the environment that reported
  the failure.
- Do not consider a technical fix complete until this type of full debug chain
  is recorded in the relevant engineering log.

This fix did not fetch real data, add vendor access, add live trading, add
brokerage or order-execution logic, store credentials, modify backtester or
metrics behavior, modify synthetic reports, or make profitability claims.

---

## 2026-06-02 - Local CSV Experiment-Log Requirements

This documentation-only milestone updated `EXPERIMENT_LOG.md` with required
record fields for future user-provided local CSV research runs.

The new section requires local source paths, file hashes or version identifiers,
schemas, validation summaries, provenance, price adjustment policy, universe
rules, feature and signal timing, sample splits, benchmark assumptions, costs,
slippage, limitations, failure modes, and next actions before local CSV results
are interpreted.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, or synthetic demos. It does
not fetch data, download data, add vendor access, introduce live trading, add
brokerage or order-execution logic, store credentials, or make profitability
claims.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - QuantConnect/LEAN CSV Validation Mapping

This documentation-only milestone updated `docs/quantconnect_lean_plan.md` to
map the future local CSV validation checklist to QuantConnect/LEAN data,
calendar, universe, benchmark, fee, slippage, and execution assumptions.

The new mapping treats local CSV validation and LEAN backtests as separate
research artifacts. Local CSV checks improve auditability of user-provided
files, but LEAN runs must still document platform datasets, data normalization,
scheduled event timing, skipped symbols, benchmark configuration, brokerage
model, fee model, slippage model, order type, cash buffer, and diagnostics.

This change does not modify source code, tests, research scripts, generated
reports, feature calculations, backtester behavior, or synthetic demos. It does
not fetch data, download data, add vendor access, introduce live trading, add
brokerage or order-execution logic, store credentials, or make profitability
claims.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Real-Data Readiness Audit Checklist

This documentation-only milestone added `docs/real_data_readiness_audit.md` as a pre-experiment checklist for using user-provided local CSV data.

The checklist covers scope statements, data provenance, schema and loader checks, price adjustment policy, universe construction, benchmark choice, feature and signal timing, sample splits, costs, slippage, experiment-log fields, stop conditions, and an approval gate before any local CSV run is interpreted.

It does not fetch data, download data, choose a vendor, implement a loader, change feature calculations, modify backtester behavior, alter reports, introduce live trading, add brokerage or order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Local CSV Loader

This milestone added a strict local CSV loader module for user-provided files under `src/data/csv_loader.py`.

The loader supports wide adjusted-close price panels, long adjusted-close price rows that are pivoted to a date-asset panel, and benchmark price series. It reads local `.csv` files only, rejects remote URL-like paths, validates parseable dates, rejects duplicate or unsorted dates where order matters, rejects duplicate long `(date, symbol)` rows, parses numeric fields with explicit errors, preserves missing values only when requested, and rejects non-positive prices.

This does not fetch real data, choose a vendor, add downloads, change feature calculations, modify backtester behavior, alter reports, introduce live trading, add brokerage or order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - CSV Data Interface Design Plan

This documentation-only milestone added `docs/csv_data_interface_plan.md` as a design plan for a future local CSV research interface.

The plan defines intended local CSV data types, proposed wide and long schemas, validation rules, alignment expectations for existing feature/backtest modules, and risks around survivorship bias, corporate actions, delistings, adjusted versus raw prices, vendor differences, and benchmark mismatch.

It does not implement a loader, fetch real data, add remote downloads, change feature calculations, modify backtester behavior, alter reports, introduce live trading, add brokerage or order-execution logic, store credentials, or make profitability claims.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Synthetic Multi-Factor Parameter Sweep

This research-process milestone added a deterministic synthetic-only parameter sweep for the combined-score backtest workflow.

The sweep varies only explicit factor weight sets and selected-asset counts while holding synthetic seeds, date range, transaction cost, signal lag, benchmark, and execution assumptions fixed. It reports every configured case in `reports/synthetic_multifactor_parameter_sweep.md`, writes a JSON log under `reports/experiment_logs/`, and refreshes the synthetic experiment registry.

This is a sensitivity smoke test, not parameter selection or strategy validation. It does not change feature calculations, backtester behavior, strategy logic, real-data access, live trading functionality, brokerage integration, order execution, or profitability claims.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Structured Synthetic Experiment Registry

This research-process milestone added a structured registry helper for the synthetic JSON experiment logs.

The helper validates required log fields and synthetic-research caveats, rejects duplicate experiment IDs, builds a deterministic registry table, and writes `reports/experiment_registry.md` as a caveated review report. The report summarizes existing synthetic logs only; it does not run experiments, recalculate metrics, choose parameters, fetch real data, or make profitability claims.

This does not change feature calculations, strategy logic, backtester behavior, report metrics, data access, live trading functionality, brokerage integration, order execution, or credential handling.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Synthetic Demo Experiment Logging Automation

This research-process milestone added deterministic JSON experiment-log sidecars for the existing synthetic demos.

The logs capture each demo's configuration, synthetic-only data assumptions, caveats, output paths, and diagnostics or metrics. Backtest smoke-test logs also record benchmark choice, transaction-cost assumptions, signal lag, execution-timing assumptions, and the explicit caveat that slippage is not separately modeled.

This does not change feature calculations, strategy logic, backtester behavior, portfolio construction, report metrics, real-data access, brokerage integration, live trading functionality, or profitability claims. The logs are reproducibility and auditability metadata for synthetic workflows only.

Validation:

```text
python -m pytest -q
passed

python -m compileall src tests research
passed
```

---

## 2026-06-02 - Post-4H Checkpoint Review

This documentation-only checkpoint reviewed the repository after the synthetic combined-score backtest smoke test was merged to `main`.

The review synced `main`, confirmed the latest reviewed commit was `6811b58`, reran the full test suite and compile check, and interpreted guardrail grep matches for live trading, brokerage, real-data fetching, and profitability language. The matches were governance warnings, synthetic caveats, LEAN planning caveats, module docstrings, or tests that enforce forbidden-import and warning-language rules.

No source code, tests, strategy logic, backtester behavior, feature calculations, report-generation code, data access, live trading functionality, or profitability claims were changed.

Validation:

```text
python -m pytest -q
171 passed

python -m compileall src tests research
passed
```

---

## 2026-05-28 - Repository Checkpoint Audit And Phase Report

This documentation-only checkpoint captured the project state before moving from individual factor normalization helpers toward factor combination work.

The audit reviewed tracked files, stage traceability, test status, scope guardrails, and current limitations. It did not change source code, tests, strategy logic, reports, real data access, backtester behavior, metrics, or profitability claims.

---

## 2026-05-22 - Backtester Correctness Review: Silent Data Failures, Leakage Tests, and Return Semantics

### Context

This work was part of a correctness audit for a local equity factor research pipeline. The system already had a 12-1 month momentum feature, a minimal long-only cross-sectional backtester, basic metrics, a synthetic-data demo, and a QuantConnect/LEAN implementation plan.

The goal was not to add new strategy features. The goal was to run a strict read-only review first, identify subtle correctness risks, then make targeted fixes with tests. The review focused on failure modes that are especially dangerous in quantitative research: silent data fallbacks, hidden future leakage, ambiguous return semantics, benchmark alignment problems, and weak tests that pass on happy-path examples but fail to protect core invariants.

### What I Was Looking For

The review strategy was to look for places where the system could appear to work while producing misleading research output.

The main checks were:

- Where missing data could be silently converted into plausible market behavior.
- Where default values could make metrics look normal while hiding data-quality issues.
- Where signal and return alignment could allow same-day or future information leakage.
- Where tests asserted surface behavior but not the underlying correctness invariant.
- Whether benchmark handling had the same data-quality discipline as strategy returns.
- Whether momentum window tests covered nontrivial skip windows, not only the simplest case.
- Whether the backtest output exposed enough diagnostics to evaluate whether the result was trustworthy.

This was a correctness audit, not a performance optimization pass.

### Issues Found And Fixed

#### 1. Missing Held-Asset Prices Were Silently Treated As 0% Return

The issue:

The backtester computed asset returns and then filled missing returns with zero. That meant if an asset was already held and its next price was missing, the system treated the missing return as a real 0% return.

Why it was subtle:

This does not crash. The equity curve remains smooth, metrics still compute, and tests using complete synthetic data all pass. The failure only appears when real data has gaps, stale symbols, delistings, vendor issues, or incomplete histories.

Risk:

A missing price is not the same as a flat price. Treating missing data as 0% return can silently contaminate the equity curve, drawdown, volatility, turnover-adjusted performance, and benchmark-relative metrics.

Correct behavior:

For a first-phase research engine, the safest default is to fail loudly when a held asset has missing return data.

Fix:

Added an explicit missing held-price policy in `src/backtest/portfolio.py`:

- default: `missing_price_policy="raise"`
- diagnostic fallback: `missing_price_policy="zero_return"`

The default now raises `ValueError` when a held asset has a missing return. The zero-return behavior still exists only as an explicit, documented fallback.

Verification:

Added tests in `tests/test_backtest_portfolio.py` that confirm:

- default behavior raises when a held asset has missing return data.
- explicit `zero_return` policy allows the fallback and records the assumption.

#### 2. Future-Signal Leakage Test Was Too Weak

The issue:

The original future-signal test did not force a disagreement between the lagged signal and the same-day signal on the checked rebalance date. As a result, the test could still pass even if the backtester accidentally used same-day signals.

Why it was subtle:

The implementation was correct, but the test was not strong enough to protect the invariant. A test can give false confidence when it checks a scenario where both the correct and incorrect implementations produce the same output.

Risk:

In a backtest, using same-day or future signals can create inflated performance that looks legitimate. This is one of the most dangerous classes of research bugs because it often improves results instead of causing failures.

Correct behavior:

A rebalance on date `t` with `signal_lag_periods=1` must use the signal from the previous available date, not the signal stamped at `t`.

Fix:

Strengthened the test setup:

- date 0 signal ranks asset A highest.
- date 1 signal ranks asset B highest.
- date 1 rebalance must still hold asset A.
- if signal shifting is removed, the test fails because date 1 would hold asset B.

Verification:

The updated test directly protects the signal-lag invariant.

#### 3. `total_return` Used `equity_curve.iloc[0]` Instead Of Explicit Initial Capital

The issue:

The metrics function calculated total return as:

```text
final_equity / equity_curve.iloc[0] - 1
```

This assumes the first equity curve value is always the starting capital.

Why it was subtle:

With the default signal lag, first-row equity often remains equal to initial capital, so the issue is hidden. But if first-row trading costs or other initial adjustments exist, `equity_curve.iloc[0]` is no longer the true capital base.

Risk:

Return metrics can understate or hide first-period costs. The meaning of total return becomes dependent on how the equity curve is indexed rather than on an explicit capital convention.

Correct behavior:

Total return should be measured against the known initial capital base.

Fix:

Updated `src/backtest/metrics.py` so `calculate_basic_metrics` accepts and uses explicit `initial_capital`:

```text
total_return = final_equity / initial_capital - 1
```

Benchmark total return now uses the same explicit base.

While adding the test, I also found that first-row turnover was not being counted correctly when `signal_lag_periods=0`. That was fixed so first-row entry costs can be represented.

Verification:

Added a test where first-row trading costs exist. The test verifies that total return includes those costs instead of using the already-cost-adjusted first equity value as the denominator.

#### 4. Missing Benchmark Prices Were Silently Filled As Zero Returns

The issue:

Benchmark prices were reindexed to strategy dates. Missing benchmark returns were then filled with zero.

Why it was subtle:

This makes benchmark series look complete even when benchmark data is missing. The benchmark equity curve remains usable, so the problem is easy to miss.

Risk:

A missing benchmark return is not neutral. Filling it with zero makes a concrete assumption that the benchmark was flat. That can distort benchmark total return, excess return, alpha-like diagnostics, and performance interpretation.

Correct behavior:

Benchmark data gaps should be explicit.

Fix:

Added a benchmark missing-data policy in `src/backtest/portfolio.py`:

- default: `benchmark_missing_policy="raise"`
- diagnostic fallback: `benchmark_missing_policy="zero_return"`

The default raises `ValueError` if benchmark prices are missing on strategy dates.

Verification:

Added tests for both default raise behavior and explicit zero-return fallback.

#### 5. Momentum Skip-Window Tests Did Not Cover Wider Skipped Windows

The issue:

Momentum tests covered a simple skip case, but not `skip_periods > 1`.

Why it was subtle:

The implementation used explicit shifts correctly, but off-by-one errors in momentum features often appear only when the skipped window is wider than one period.

Risk:

A wrong implementation could accidentally use prices inside the skipped recent window, or use the wrong boundary price, while still passing simple tests.

Correct behavior:

For a signal date `t`, the formula should be:

```text
momentum[t] = price[t - skip_periods] / price[t - lookback_periods] - 1
```

Interior prices between `t - skip_periods + 1` and `t` should not affect the signal.

Fix:

Added a test with `skip_periods=3` in `tests/test_momentum.py`:

- changing an interior skipped-window price does not change momentum.
- changing the boundary price at `t - skip_periods` does change momentum.

Verification:

The test protects both sides of the invariant: ignored interior prices and included boundary price.

#### 6. Signal Coverage Was Not Exposed

The issue:

After aligning signals to the price index and columns, the caller had no quick way to see how much signal data remained non-null.

Why it was subtle:

The backtester can still run with sparse signals. It may simply hold fewer names, skip assets, or produce plausible results. Without signal coverage diagnostics, a user may not realize the backtest is running on weak or incomplete signal data.

Risk:

A strategy can appear valid while most of its intended universe has missing signals.

Correct behavior:

Signal coverage should be visible as part of backtest assumptions or diagnostics.

Fix:

Added aligned signal coverage to the backtest result assumptions:

```text
result.assumptions["aligned_signal_coverage"]
```

Verification:

Added a test asserting full coverage in a complete signal example.

### Deep Reasoning

These issues share a common pattern: the system was mostly correct on clean synthetic data, but several defaults could hide problems once the data became messy.

The biggest engineering risk in a backtester is not always a crash. Often the bigger risk is a plausible number produced from bad assumptions.

Examples:

- A missing held-asset return filled with `0.0` is not neutral. It converts a data-quality issue into a fake market observation.
- `equity_curve.iloc[0]` looks like a convenient base, but it conflates starting capital with first recorded portfolio value.
- A missing benchmark return filled with zero does not mean unknown; it means the benchmark was flat.
- A future-leakage test must use inputs where the correct and incorrect implementations diverge. Otherwise the test only verifies that code runs.
- Signal coverage is part of backtest credibility. It is not just debugging metadata.

The broader lesson is that a research pipeline needs explicit semantics at the boundaries: data availability, signal timing, return calculation, benchmark alignment, and missing-data behavior.

### Tests Added Or Strengthened

The test suite was strengthened around specific invariants.

- Held asset missing price: verifies default behavior raises when a held asset has missing return data.
- Explicit zero-return fallback: verifies the fallback is opt-in and visible in assumptions.
- Future-signal leakage: verifies date `t` rebalance uses date `t-1` signal when `signal_lag_periods=1`.
- Total return base: verifies first-row costs are included when measuring return against `initial_capital`.
- Benchmark missing data: verifies missing benchmark dates raise by default.
- Benchmark zero-return fallback: verifies benchmark zero-return behavior is opt-in and documented through assumptions.
- Momentum `skip_periods > 1`: verifies skipped-window interior prices do not affect the signal, while the boundary price does.
- Signal coverage: verifies aligned signal coverage is exposed in backtest assumptions.

These tests are not just coverage additions. Each one protects a correctness invariant that could otherwise silently fail.

### Outcome

The system moved from "runs correctly on clean examples" toward "fails loudly on dangerous data assumptions."

Key improvements:

- Missing held-asset prices no longer silently freeze P&L.
- Benchmark data gaps no longer silently become flat benchmark returns.
- Total return now has an explicit capital base.
- Signal lag behavior is protected by a stronger leakage test.
- Momentum window behavior is tested for wider skip periods.
- Signal coverage is exposed as a first-pass observability diagnostic.

No real market data was fetched. No live trading was added. No profitability claims were made.

Validation at the time of this entry:

```text
python -m pytest -q
24 passed

python -m compileall src tests research
passed

python -m research.synthetic_momentum_demo
passed
```

### Interview Story Version

Situation:

I was building a local quantitative research pipeline with a 12-1 momentum feature, a long-only cross-sectional backtester, basic metrics, and a synthetic-data demo. Before adding more features, I wanted to audit the implementation for correctness risks that could invalidate future research.

Task:

The goal was to perform a strict read-only review first, identify subtle bugs, then make targeted fixes without changing project scope. I focused on look-ahead bias, missing data behavior, return semantics, benchmark alignment, and whether the tests actually protected the intended invariants.

Action:

I inspected the momentum calculation, portfolio return path, benchmark handling, metrics calculation, and tests. The code was mostly correct on the happy path, but I found several silent failure modes. Held-asset missing returns were being filled as 0%, benchmark gaps were also effectively frozen, and total return inferred its base from the first equity curve value. I also found that the future-signal leakage test would not necessarily fail if signal lagging were removed.

I fixed these with explicit policies and stronger tests. Missing held-asset prices now raise by default. Benchmark gaps raise by default. Total return uses explicit initial capital. The future-leakage test now constructs a case where same-day and lagged signals choose different assets. I also added a wider momentum skip-window test and exposed signal coverage in the backtest assumptions.

Result:

The backtester became more auditable and less likely to produce misleading results from bad data or ambiguous accounting. The final checks passed: the full pytest suite, compile check, and synthetic demo all ran successfully. More importantly, the tests now protect the correctness assumptions that matter most for a financial research pipeline.

### Resume / Performance Review Bullets

- Performed a correctness audit of a Python quantitative backtesting pipeline, identifying silent data-quality failures in held-asset returns, benchmark alignment, and return-base semantics.
- Strengthened backtest invariants by adding explicit missing-data policies, signal-lag validation, initial-capital-based return calculation, and signal coverage diagnostics.
- Improved unit tests to catch future-signal leakage, momentum window off-by-one errors, benchmark data gaps, and missing held-price behavior.
- Converted ambiguous silent fallbacks into explicit default failures with opt-in diagnostic policies for synthetic or controlled research scenarios.
- Preserved project scope by fixing correctness issues without adding live trading, external data fetching, or unsupported profitability claims.

### PR Summary Draft

This change tightens correctness guarantees in the research backtester and momentum tests. Missing held-asset returns and missing benchmark prices now raise by default instead of being silently treated as zero-return observations. Total return is now calculated against explicit `initial_capital`, avoiding ambiguity when the first equity-curve row already includes costs. The signal-lag test was strengthened so it fails if same-day signals are accidentally used. Momentum tests now cover wider skipped windows, and the backtest result exposes aligned signal coverage for basic observability.

Tests added or strengthened cover held-asset missing prices, explicit zero-return fallback policies, future-signal leakage, total-return base semantics, benchmark missing-data handling, `skip_periods > 1` momentum behavior, and signal coverage exposure.

---

## 2026-05-22 - WorldQuant Alpha Catalog Stage 1

This was a documentation-only, catalog-first milestone for adding WorldQuant-style alpha research to the project. The work created `docs/worldquant_alpha_catalog.md` to classify the 101 Formulaic Alpha references by data requirement and priority before any implementation work.

No alpha code, operator layer, real market data, or backtest integration was added. The catalog explicitly treats the formulas as educational research references, not trading recommendations or guaranteed profitable strategies.

The next milestone is operator-layer implementation and tests, not alpha backtesting.

Validation:

```text
python -m pytest -q
24 passed
```

---

## 2026-05-23 - WorldQuant Operator Layer Stage 2

This milestone added a reusable pandas operator layer for future WorldQuant-style alpha research. The work is infrastructure only: no alpha formulas, backtest integration, real data fetching, live trading, or profitability claims were added.

The key correctness decisions were to require sorted date-indexed DataFrames, preserve index and columns, use full trailing windows for rolling operators, reject invalid non-numeric panel values instead of silently coercing them to missing data, and require exact index/column matches for pairwise operators such as rolling correlation, rolling covariance, and safe division.

Tests were added for hand-calculated examples, missing-data propagation, invalid input handling, tie behavior in ranks, zero-denominator division, zero cross-sectional standard deviation, full-window rolling behavior, and future-row isolation for time-series operators.

Follow-up review note:

The read-only review found one subtle validation gap: `astype(float)` correctly rejects values such as `"bad"`, but can silently convert string sentinel values such as `"nan"` into real missing values. That behavior would blur the difference between an intentional missing value and an invalid non-numeric data error. The validator was tightened to require numeric, non-boolean dtypes before conversion to a float copy, rejecting object, string, category, boolean, and numeric-looking string columns. Regression tests were added for `"nan"`, `"NaN"`, and `"1.0"` string inputs while preserving support for real numeric `NaN` values in numeric columns. The `ts_rank` docstring was also clarified to state that ties use average rank by default and that `pct=True` returns percentile ranks.

Validation at the time of this entry:

```text
python -m pytest -q
46 passed
```

---

## 2026-05-25 - Stage 3 Planning Rationale: Start With alpha_009 Only

Stage 3 intentionally starts with a single WorldQuant-style alpha candidate: `alpha_009`. This is a scope-control decision, not a rejection of `alpha_012`, `alpha_101`, or the broader WorldQuant 101 set as future research candidates. The project is deliberately avoiding a bulk implementation milestone because formulaic alpha work is only useful if each formula has clear data requirements, date alignment, missing-data behavior, and tests.

`alpha_009` is the safest first candidate because it is close-only. The repository already has close-price-based feature work, and the Stage 2 reusable operator layer now provides the primitives needed for this formula: strict panel validation, one-period deltas, and full trailing rolling minimum and maximum operators. It does not require volume, OHLC, VWAP, market cap, or industry classification schemas. That makes it a good first formulaic alpha for testing operator reuse, date alignment, missing-data propagation, strict input validation, and no-look-ahead behavior without expanding the data model.

Other candidates remain staged. `alpha_012` requires volume + close data, so it should wait until the project defines a volume schema and adds volume-specific validation tests. `alpha_101` requires OHLC inputs, so it should wait until the project has explicit open, high, low, and close schemas plus safe denominator handling and OHLC alignment tests. VWAP, market cap, and industry-neutral alphas remain deferred until the project has explicit data support and validation rules for those inputs.

The WorldQuant 101 Formulaic Alphas are treated here as educational formulaic alpha references, not guaranteed profitable trading strategies. A formulaic alpha is not a complete strategy. It still requires universe selection, data cleaning, date alignment, signal lag, ranking or normalization, portfolio construction, transaction costs, slippage assumptions, risk controls, benchmark comparison, and out-of-sample validation before it can be evaluated as part of a research workflow.

The implementation philosophy for this project is to keep milestones small and reviewable. Reusable operators are tested before formulas. Formulas are implemented one at a time. Alpha outputs are not connected to the backtester until formula correctness has been reviewed. Real market data is deferred until synthetic and unit-test behavior is stable. No profitability claim is made from implementing a formula alone.

Codex is being used as an engineering agent, not as a strategy oracle. Stage 3 prompts use hard preflight checks, strict allowed-file lists, no-go conditions, self-checks after implementation, read-only review before commit, and separate commit and PR steps. When subagents are used, their role is read-only review or scoped analysis; they are not used to modify the same files concurrently.

The prompt workflow is also designed to be queue-safe. Each prompt checks the active branch, working-tree cleanliness, test status, and allowed file set before proceeding. If a prerequisite fails, the prompt must stop instead of continuing. This prevents later queued tasks from blindly building on a broken, stale, or dirty state.

Explicit Stage 3 non-goals:

- no `alpha_012`
- no `alpha_101`
- no full WQ101 implementation
- no backtester integration
- no performance report
- no real data fetching
- no live trading
- no profitability claim

---

## 2026-05-25 - WorldQuant Alpha#009 Stage 3

This milestone implemented `alpha_009` as the first close-only WorldQuant-style alpha candidate. The function is a research feature only: it calculates a point-in-time-safe signal from close prices and does not define portfolio construction, execution timing, backtest integration, or expected profitability.

The implementation uses the reusable operator layer from Stage 2. It computes one-period close deltas, evaluates full trailing rolling windows over those deltas, and applies the Alpha#009 rule: continue the current delta when the trailing delta window is strictly all positive or strictly all negative; otherwise use the negative current delta. A zero delta falls into the mixed-window branch because the conditions are strict.

Date alignment is explicit: the feature at date `t` may use `close[t]` and earlier closes only, so it is known after the close at `t`. Trading lag remains the responsibility of a later strategy or backtest layer.

Tests were added for hand-calculated positive, negative, mixed, and zero-delta cases; output shape preservation; future-row isolation; missing close behavior; strict input validation; window validation; and absence of backtest integration imports.

No real market data was fetched. No reports were modified. No profitability claim or strategy performance result was added.

Validation at the time of this entry:

```text
python -m pytest -q
60 passed
```

---

## 2026-05-25 - Pull Request and Commit Hygiene Rules

This documentation-only governance update added explicit pull request and commit discipline to `AGENTS.md`.

The project is adopting small, meaningful PR and commit practices to improve reviewability and traceability. The goal is not artificial PR or commit inflation. Trivial edits should not be split just to increase counts, and unrelated changes should not be combined into one PR.

Future alpha work should continue to be split by clear milestones, such as planning, tests or documentation, implementation, read-only review, and PR review.

No source code, tests, strategy logic, backtester behavior, metrics, reports, real data fetching, or profitability claims were changed.

---

## 2026-05-28 - Factor Correlation Diagnostics

This milestone added diagnostic-only factor correlation infrastructure for aligned factor panels.

The helper measures pairwise Pearson or Spearman relationships across flattened factor panels using overlapping non-missing observations only. It preserves factor names, validates panel alignment, and does not fill missing values.

Factor selection, model training, backtest integration, performance reporting, real data fetching, new alpha formulas, and profitability claims remain deferred.

---

## 2026-05-28 - Factor Combination Helper

This milestone added a narrow helper for combining already-preprocessed factor panels with explicit weights.

The helper enforces exact date and asset alignment, finite non-boolean weights, at least one nonzero weight, and strict missing-value behavior before producing a weighted combined score.

Normalization, factor correlation diagnostics, synthetic alpha smoke demos, backtest integration, real data fetching, new alpha formulas, reports, and profitability claims remain deferred.

---

## 2026-05-27 - Cross-Sectional Z-Score Normalization Helper

This milestone added the first factor normalization helper: cross-sectional z-score normalization for date-indexed asset factor panels.

The helper is intentionally narrow. It reuses the existing strict operator-layer validation and row-wise z-score behavior so missing factor values remain visible, zero-dispersion cross-sections produce `NaN`, and index and asset alignment are preserved.

Rank normalization, factor combination, factor diagnostics, synthetic alpha smoke demos, and backtest integration remain deferred to later PRs.

No backtester behavior, metrics, WorldQuant alpha formulas, reports, real data fetching, or profitability claims were changed.

---

## 2026-05-28 - Cross-Sectional Factor Winsorization Helper

This milestone added a row-wise winsorization helper for date-indexed asset factor panels.

The helper is intentionally limited to factor preprocessing. It preserves missing values, reuses strict panel validation, and clips each date's cross-section independently using explicit lower and upper quantile bounds.

Factor combination, factor correlation diagnostics, synthetic alpha smoke demos, and backtest integration remain deferred to later PRs.

No backtester behavior, metrics, WorldQuant alpha formulas, reports, real data fetching, or profitability claims were changed.

---

## 2026-05-27 - Rank-Based Factor Normalization Helpers

This milestone added rank-based factor normalization helpers for date-indexed asset factor panels: ordinal cross-sectional ranks and pandas-style percentile ranks.

The helpers are intentionally limited to row-wise ranking across assets. They preserve missing values, reuse strict panel validation, and document that pandas percentile ranks use `pct=True` semantics rather than min-max percentile scaling.

Winsorization, factor combination, factor correlation diagnostics, synthetic alpha smoke demos, and backtest integration remain deferred to later PRs.

No backtester behavior, metrics, WorldQuant alpha formulas, reports, real data fetching, or profitability claims were changed.

---

## 2026-05-25 - Factor Normalization And Combination Roadmap

This documentation-only roadmap defines the next research infrastructure step before combining factor outputs or connecting WorldQuant-style alphas to the backtester.

The roadmap explains why raw factor values should not be combined directly, distinguishes raw factors from normalized factors, combined scores, and full strategies, and records expected policies for cross-sectional normalization, ranking, winsorization, missing values, factor alignment, and correlation diagnostics.

The intended future sequence is normalization helpers first, factor combination helpers second, factor correlation diagnostics third, an `alpha_009` synthetic feature smoke demo fourth, and backtest integration only after those pieces are tested.

No source code, tests, strategy logic, backtester behavior, metrics, reports, real data fetching, or profitability claims were changed.

---

## 2026-05-28 - Synthetic Multi-Factor Workflow Demo

This milestone added a synthetic-only workflow demo showing how existing factor preprocessing, normalization, diagnostics, and combination helpers can be used together on deterministic factor panels.

The demo applies row-wise winsorization, z-score normalization, rank-based normalization, factor correlation diagnostics, and explicit weighted factor combination before writing a synthetic workflow report.

It does not add backtest integration, portfolio construction, real market data, new alpha formulas, reports beyond the synthetic demo report, live trading functionality, or profitability claims.

---

## 2026-05-28 - Synthetic Combined-Score Backtest Smoke Test

This milestone added a synthetic-only smoke test that passes a deterministic combined factor score into the existing long-only backtester.

The workflow generates synthetic prices and synthetic factor panels, applies existing factor preprocessing and normalization helpers, combines z-scored factors with explicit weights, and runs the existing backtester with transaction costs and signal lag.

The output is a workflow diagnostic only. It does not modify backtester or feature helper behavior, fetch real market data, add broker or live trading logic, introduce order execution, or make profitability claims.

---

## 2026-09-08: Round 2 Whole-Codebase Ablation (Historical B2 Acceptance & Initial C1 Evidence Checkpoints)

- **Status:** B2 Implementation Accepted (Plan A2); Initial C1 Integration Checkpoint QA Complete (124 Executions, 36 Triples, 7-Triple Campaign Cohort Evaluated); Three B2 Static Reviews Complete (3 Open Advisories Preserved); Gates for Later Final Candidate (Fresh Exact-Candidate QA, Fresh Static Reviews, Local Codex PR Review, Linux/Python 3.11 CI) and Owner-Authorized Separate Branch/PR Publication Pending (Live Checks Belong in Eventual PR Gate Record); Merge, auto-merge, deployment and main pushes are not authorized.
- **Baseline Commit:** `6ee193c9bb43f8290b3e09396fd241fec32df695` (439 files, manifest `70237d678616cd309632117cac062dba9d24d63f29d9fd97361b29a4b2146dc4`).
- **Review Candidate Checkpoint (B2):** `3e006260952521eac66b62dcaf4527fc867e453e04b8fbd7af180ea1e4a95392` (448 files, candidate source manifest `fdfd4d7c8533bd6190171fa679ac4acc52a61ca6cb504427c92e9d3a932a28ac`).
- **Initial Integration Checkpoint (C1):** `713bba95e393514720973ca2fcb58b70cba23d8d` (tree `359090fbca29034648307ab7740b776f0122eff6`, parent `6ee193c9bb43f8290b3e09396fd241fec32df695`, 483 tracked files, initial churn 53 files / +89,521 / -55, not final PR churn; runtime/test bytes identical to B2; documentation/evidence composition differs).
- **Executed Environment:** macOS 27 arm64, existing isolated Python 3.12.14 virtual environment, NumPy 2.5.2, pandas 3.0.5, SciPy 1.18.1, pytest 9.1.1, Ruff 0.16.6. Numerical library threads locked to 1.

### Scope & Architectural Changes
This ablation round completes the implementation and machine verification of seven accepted architectural simplifications across six runtime files:
1. `src/campaign/runner.py` (C13 + C01c): Per-execution memo of cost-independent interval return maps (`_held_map` / `_held_return` lookups, `C13`) and execution-owned anchor date indexing (`C01c`). Per-trial costs, holdings, and validation state remain strictly isolated.
2. `src/ledger/schema_registry.py` (C02): Consolidated redundant structural schema traversals within single validation calls while preserving packaged schema authority, release isolation, and transactional event validation.
3. `src/backtest/portfolio.py` (C04b): Empty-axis preserving column iteration in source provenance capture, guaranteeing exact Nx0, 0xM, and 0x0 shape invariants (`((), ())` on 2x0 input), original/current digests, and wide/nullable scalar typing.
4. `src/backtest/metrics.py` (C05): Direct array access for validated numeric episode accounting, preserving chronological episode state transitions, fees, slippage, and terminal-open exclusions. C05 retains episode loops while replacing DataFrame scalar lookups.
5. `src/features/validation.py` (C12): Canonical eligible-only label endpoint gathering after split reconstruction, batching endpoint gathering and vectorized division to eliminate repeated scalar indexing (baseline already restricted computation to eligible rows).
6. `src/features/diagnostics.py` (C10b): Vectorized Spearman Rank IC batching with eligibility-local gating (B2 repair, checking valid asset-pair counts within each date row) while keeping baseline Pearson correlation byte-exact; ONLY Spearman receives the 1e-12 gate; Pearson, public axes, dtypes, names, NaN masks, and error order stay exact in tested contracts.

### Code Churn Summary (Pre-Publication Checkpoint)
- **Production Python (`src/`):** 109 added / 52 deleted across 6 files (+57 net lines).
- **Test Python (`tests/`):** 838 added / 0 deleted across 6 files (+838 net lines).
- **Golden Fixtures (`tests/fixtures/`):** 30,325 added / 0 deleted across 3 files (+30,325 net lines).
- **Documentation & Controls:** 148 added / 2 deleted across 3 files (`AGENTS.md`, `docs/engineering_log.md`, `docs/repo_map.md`; +146 net lines) before publication material.
- **Repository Membership:** 439 baseline files → 448 candidate files (+9 added files).

### Measured Performance & Tradeoffs (Producer Matrix: 18 Cases, 126 Triples)
- **Core Speedups (Median Wall Clock):**
  - Campaign 504×100: **13.052×** speedup (18.812s → 1.441s; -17.371s, -92.34%; cProfile calls 622.5M → 34.6M).
  - Generic Backtest 504×100: **2.425×** speedup (2.217s → 0.914s; -1.303s, -58.77%); 160×12: **1.572×** (151.9ms → 96.7ms; -55.3ms, -36.37%).
  - Feature Labels 1260×100: **2.883×** speedup (99.7ms → 34.6ms; -65.1ms, -65.32%).
  - Sparse Diagnostics 504×100: **2.353×** speedup (183.3ms → 77.9ms; -105.4ms, -57.50%).
  - Research Sweep 160×12 (8 cases): **1.586×** speedup (1.243s → 0.783s; -459.1ms, -36.95%).
  - Ledger Transactions (Paths A & B): **2.237× – 2.239×** (197ms → 88ms; -109ms, -55.3%); with +1,000 extra records: **1.667× – 1.684×** (271ms → 161ms; -109ms, -40.0% to -40.6%).
  - Schema Registry (30 Validations): **2.457×** speedup (596.9ms → 242.9ms; -354.0ms, -59.30%).
- **Adverse Observations & Memory Tradeoffs Disclosed:**
  - Independent campaign repetition 1: In the single initial independent triple, B2 was +0.151737s (~+10.8%) slower than B1 in wall time (1.558791s vs 1.407054s; CPU 1.557491s vs 1.405663s; baseline wall 18.091250s). This single observation qualifies B1-preservation statements; equal runner bytes do not prove host noise; recurrence/cause remain unresolved pending final integration QA.
  - Minor B1-to-B2 shifts observed on large cases: `labels_1260x100` B2 median is +0.353ms (+1.03%) slower than B1; `sweep_160x12_eight_cases` B2 median is +8.145ms (+1.05%) slower than B1; `campaign_504x100` B2 is +9.4ms (+0.66%) slower than B1. Matched serial order mitigates confounding within pairs, but host activity varies over time; observed values are reported directly without causal speculation.
  - Vectorized allocation costs: `labels_1260x100` tracemalloc peak increased +57.9% (+1,714,822 bytes) to 4.68 MB; `diagnostics_504x100_sparse` tracemalloc peak increased to peak 14.6× baseline (+3,713,984 bytes) while process peak RSS dropped 40.2% (-65.2 MB). Mechanisms provide plausible context, not isolated causal proofs.
  - Unprofiled campaign peak RSS: In `campaign_504x100` measured executions, median process peak RSS rose slightly: baseline 309,526,528 bytes, B1 310,706,176 bytes, B2 311,394,304 bytes (+0.60% vs baseline, +0.22% vs B1), preserving the adverse finding across unprofiled and instrumented runs.
  - Fixture resolution: Committed 4×3 fixture median is 44.47 ms in B2 vs 46.24 ms in baseline and 50.92 ms in B1 (7/7 pairs faster than B1, a 1.145× speedup; 6/7 faster than baseline).

### Test Discipline, Source-Binding & Verification Lessons
1. **Source-Binding Verification:** To prevent test harness path hijacking from repository root `pyproject.toml` `pythonpath`, the producer ran under `repair_b2/isolated_qa/` using isolated `pytest.ini` and conftest hooks, while independent QA under `qa/independent_b2/` used `-p independent_binding -o pythonpath=` with postcollection hooks asserting both module `__file__` and function `__code__.co_filename` matched expected candidate paths.
2. **Restored Mechanism Assertions:** Checkpoint 001 omitted `assert rank_indexes and corr_indexes`. Checkpoint 002 restored the assertion byte-for-byte: baseline fails as an expected mechanism control (1 failed, 35 passed), B1 fails ineligible ranking (6 failed, 30 passed), and B2 passes completely (36 passed, exit 0). No assertions or tolerances in the current candidate were weakened.
3. **Independent Population Structure:** Independent execution series under `qa/independent_b2/` comprises 106 separate executions (full suites 2,573 / 2,722 / 2,758 passes with 2 platform skips; 9 rejected controls; 30 fresh triples across 18 scopes). A separate 24-process cohort (`independent_b2_imports`) verified 7 fresh import triples plus 3 warmups across 11 first-party modules (medians: baseline 0.205355s, B1 0.206648s, B2 0.205939s).
4. **Initial C1 Integration QA & Repeated Campaign Cohort:** Independent C1 execution QA, recorded in the supplemental public evidence (with raw runs preserved in local execution archive `qa/independent_c1_001`), comprised 124 separate executions (full suites 2,573 / 2,722 / 2,758 passes with 2 platform skips; 9 negative variants reproduced exact failure nodes; bound new guards baseline 1 failed/35 passed, B1 6 failed/30 passed, C1 36 passed). It evaluated 36 fresh triples across 18 scopes (7 triples each for `fixture_all_configured`, `diagnostics_504x100_sparse`, and `campaign_504x100`; 1 triple each for the other 15 scopes; campaign 7 are a subset of 36, separate from earlier populations).
   - *Repeated Campaign 504 Medians:* Baseline wall 17.828260s / CPU 17.810254s; B1 wall 1.411179s / CPU 1.409800s; C1 wall 1.414200s / CPU 1.412997s.
   - *Campaign Paired Behavior:* Ratio of wall medians is +0.214059%; CPU medians +0.226770%. C1 was slower than B1 in 5 of 7 wall pairs and 6 of 7 CPU pairs; largest observed paired wall increase was +3.858665% (rep 5: 1.470304s vs 1.415677s). All 7 samples are published in supplemental public evidence (`docs/ablation_evidence/round2_integration/summary.json`). Overlapping ranges do not prove equivalence or that regressions are eliminated; the original adverse B2 single triple (+10.8% slower; baseline wall 18.091250s) remains visible and preserved.
   - *Independent Reproduction Smoke Execution:* Documented reproduction commands were independently smoke-executed on C1 using trusted git archive baseline and HEAD, runtime-only B1 reverse patch with 6 verified source hashes, concrete path substitution with `-B`, and existing isolated interpreter/dependencies (no installation performed). Verified on `diagnostics_504x100` (all 3 CLI pair comparisons and Python alternative PASS).
   - *Source-Binding & Packaging Checks:* 3 fresh import processes (one process for each: baseline, sealed B1, and C1) verified module/function origins across 11 modules each. No-install build from trusted C1 export verified wheel (55 Python members) and sdist (137 Python members) with 20 packaged schema/checksum resources.
   - *Diff Cleanliness Check:* `git diff --check` returned 2 with 78 diagnostics bound to archived patch context, Markdown hard breaks, and test EOF blank (not a clean check; no patch/test normalized or removed).

### Current Limitations & Downstream Final Candidate Gates
- Current runtime verification is strictly limited to macOS 27 arm64 / Python 3.12.14.
- Isolated distribution build (`platform_build_002`) verified syntax compilation and Python 3.11 AST grammar parsing across 161 files, with valid wheel (55 Python members) and sdist (137 Python members) containing all 20 package resources in `src/ledger/schemas/` (JSON schemas and checksum sidecars); however, Linux / Python 3.11 **runtime CI remains pending** (prior PR202 Linux fixture failures were corrected prior to baseline, but current B2 candidate execution on Linux/3.11 is unverified).
- **Implementation & Review Status:** The coordinator has formally accepted exact frozen review candidate `3e006260952521eac66b62dcaf4527fc867e453e04b8fbd7af180ea1e4a95392` (source manifest `fdfd4d7c8533bd6190171fa679ac4acc52a61ca6cb504427c92e9d3a932a28ac`, 448 files) as the implementation input to controlled integration under accepted binding plan A2 (recorded in local coordinator archive `coord/decision_implementation_b2.md`). Three eligible mutually blind reviews (GPT-6-Astra medium normal/default, Grok-4.6 xhigh, Gemini-3.8-Flash high) reported zero MATERIAL findings. (A prior Gemini attempt was excluded for a prohibited native self-transcript read-boundary violation; metadata-only observed return, no peer-text exposure; preserved in local coordinator archive `coord/agy_b2_exclusion.json` as internal audit history, not a published repository artifact).
- **Open Advisories Preserved:** Three advisories remain OPEN: `B2-GPT-ADD-001` (original independent campaign single triple +10.8% wall time slower than B1; recurrence/cause unresolved; follow-up 7-triple cohort on C1 evaluated with wall median +0.214059% and CPU +0.226770% vs B1, 5/7 wall pairs slower, max increase +3.858665% in rep 5); `ADVISORY-B2-GROK-001` (fixture matrix002 pair 4 slower 0.897ms than baseline); and `ADVISORY-B2-GROK-002` (named B1-to-B2 slower-pair counts, medians, and allocation/RSS tradeoffs preserved).
- **Gates Applying to Later Final Candidate:** Initial clean worktree integration checkpoint (commit `713bba95...`) and initial C1 integration QA are complete. Initial C1 whole-commit QA does not imply acceptance of changed final bytes. Any later assembled final candidate (incorporating documentation updates) requires fresh exact-candidate QA before fresh reviews, followed by fresh exact-candidate static reviews, local latest/high normal Codex PR review, and Linux/Python 3.11 runtime CI. Live publication head and check verification belong in the eventual PR gate record rather than this historical checkpoint log. No integration PR acceptance, Codex PR review, Linux CI, or publication has occurred at this checkpoint. The owner has authorized a separate branch/PR after the required gates; merge, auto-merge, deployment and main pushes are not authorized.
