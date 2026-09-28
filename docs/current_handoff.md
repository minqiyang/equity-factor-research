# Current Handoff

Updated: 2026-09-28 for M4.8 Stage D (private snapshot real_v2 under partition rule v2, seal carry, universe build
across both segments, curated identity boundary rule, terminal template).

Canonical responsibility: the latest recorded operational checkpoint, exact
last-verified repository and PR facts, immediate blockers or owner decisions,
and the next safe action.

Recorded remote facts are cached evidence and must be verified live before any
action. This file defines no authority, workflow policy, research methodology,
stage dependency, or historical review narrative.

## Resume Order

1. Read `AGENTS.md` for repository authority, research-safety boundaries, and continuation rules.
2. Read `docs/current_handoff.md` for the latest recorded operational checkpoint.
3. Read `docs/codex_long_running_controller.md` for execution and review gates.
4. Read `docs/current_roadmap.md` for program milestones and demo delivery criteria.

Use `docs/repo_map.md` only for targeted file orientation. Before acting, follow
the controller's live-remote, clean-tree, authorization, validation, and review
requirements. Standing owner grants are recorded in `AUTHORITY.md`.

## Latest Recorded Operational Checkpoint

- Last externally verified protected baseline when this handoff was authored:
  `1c56939b0172b8f248c993961bac89fc8d2b6a13` (main after PR #274).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #274: M4.0 local real-data diagnostic through M4.7a-3 PIT universe construction,
  M4.7b-2 preregistration freeze on real_v1, M4.7c-1 point-in-time rerun on real_v1
  (`extend_first`), the M4.7c-2 decision record, M4.7 support v2 with the registration v2 rerun, M4.8
  Stage A (partition rule v2, seal carry, segment-local validation, census v3 code), and M4.8 Stage B (causal
  engines, locked capital, terminal schema v3, segment runner), and the M4.8 Stage C membership curation record
  (plan Revision 4, rule M-9, gate G1 passed).
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88` (PR #200), `e76ddb4e` (PR #203), `770cfe54` (PR #260), `49eacdd4` (PR #261),
  `2c07ee4d` (PR #262), `76a0e43a` (PR #264), `de3172bc` (PR #265), `d15ef1d4` (PR #266),
  `45fe5adc` (PR #267), `0d87d7eb` (PR #268), `a9c94dca` (PR #269), `e4662859` (PR #270),
  `dcf7b86a` (PR #271), `bfdca57a` (PR #272), `f416af8c` (PR #273), and `1c56939b` (PR #274).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`);
  it is preserved history outside the active queue.
- This candidate's diff and artifacts add no raw private data, provider response, provider-derived membership
  list, security code, or private path. Inherited private-path occurrences in the tracked tree are unchanged from
  the base; redacting them needs separate owner authorization.

## Recorded Delivery Scope

- Candidate branch `claude/m4_8d-build-real-v2` records M4.8 Stage D under binding plan Revision 4
  (`816a3bea…bd74c`), sections 2.2, 2.7, and 7.3.
  - Private snapshot `real_v2` under `<private_data_root>`, built offline from the local acquisitions (no network
    request): manifest with 10,615 hash-verified authorized files, rule `sealed_window_only_partition_v2`, per-side
    discovery files, SL-8 pre-side volume basis on all 815 retrieved codes, seal carry record `holdout_seal_v2.json`
    (`40471065…b741`) with the three bound hashes and real_v1's prospective seal verified.
  - Universe build with `D0_pre` 2014-04-30: pre segment 62 IC months, post 60; 755 of 848 intervals resolved;
    926 permanent IDs; 1,223 side panels; 158 seal-gap identity splits; one curated identity boundary.
  - Terminal template: 88 candidates (68 in scope, 5 `deferred_holdout`, 15 outside the holding windows).
  - Access: 0 holdout, raw, or quarantine opens downstream of the partitioner (build access log and an `open`
    audit hook).
  - Code: rule `curated_identity_boundary_v1` (`research/m4_8_membership.py`, `research/m4_7_universe_build.py`);
    tests T-ID-BND-1..3 in `tests/test_m4_8_universe_segments.py`.
  - Records: `docs/engineering_log.md` and `docs/decision_log.md` (Stage D entries).
- `real_v1` (8,830 files) and every committed M4.7 and M4.8 artifact stay byte-identical; the membership census on
  real_v2 reproduces the committed census byte for byte.
- Evidence ceiling remains `DIAGNOSTIC_ONLY`.

## Current Research Gate Summary

Milestone 4.7 is completed; see `docs/current_roadmap.md`. Registration v2 on real_v1 records the
gate outcome `extend_first` (60 IC months; Family A MDE_f 0.0437-0.1293 against the 0.02 floor).
M4.8 Stages A, B, and C are merged. Stage C gate G1 (attempt c4, plan Revision 4)
on real_v1 membership metadata passed: `coverage_start_pre` = `D0_pre` = 2014-04-30, 62 pre-segment IC months,
unresolved-change fraction 4 / 303 = 0.0132 (cap 0.02), R3-2c 0.0088 (0.0104 and blocked without rule M-5a(a)).
Rule M-9 counts 6 vendor-only endpoints (3 entries) outside R3-2a; typed as sourceless change rows they would
block G1 (start 2018-11-30, 7 months). Seven required anchors pass on the floor rule (no December factsheet
exists); modelled anchors would move the start to 2016-10-31 (32 months, blocked). Stage C read no price value.
Stage D built real_v2; its universe build and template opened discovery side files only, and the holdout window
remains sealed and unaccessed. Evidence ceiling remains `DIAGNOSTIC_ONLY`.

## Immediate Blockers Or Owner Decisions

- CRITICAL review of the Stage D candidate, including the new private boundary file format
  (`membership/identity_boundaries.csv`, rule `curated_identity_boundary_v1`), which plan section 2.3 does not yet
  state.
- Owner disposition of the 10 M-2 discrepancy lines (accept as the R3-10 caveat, revise M-2 by plan revision, or
  seek primary sources); Stage D leaves it open for Stage F.
- Owner confirmation: the first Stage C Wikipedia request sent the owner's account email in its user agent
  (engineering log, c2 entry).
- Owner item carried: the frozen registration v2 validator accepts a cash completion dated after the calendar end
  (review A2-05); schema v3 refuses it.

## Next Safe Action

- After review and merge of Stage D, Stage E curates the 68 in-scope terminal candidates on real_v2 and runs the
  two-pass `validate` and `project`; Stage F then runs census v3, which measures the pre-side panel shortfall
  (111 of 448 members at `D0_pre` without a pre-side panel).

## Source Routing

- Authority, research-safety invariants, and continuation: `AGENTS.md`.
- Standing owner grants: `AUTHORITY.md`.
- Workflow, review, waiting, and stop behavior: `docs/codex_long_running_controller.md`.
- Active North Star and demo-first delivery: `docs/north_star.md`.
- Program milestones, Demo v0 criteria, and imperfection backlog: `docs/current_roadmap.md`.
- Long-term evidence policy: `docs/research_program_charter.md`.
- Track A protocol and gate semantics (historical protocol context):
  `docs/eodhd_sp500_diagnostic_campaign_contract.md` and its preregistrations.
- Historical decisions, validation, and failures: `docs/decision_log.md`,
  `docs/engineering_log.md`, and `docs/troubleshooting_log.md`.
