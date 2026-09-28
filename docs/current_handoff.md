# Current Handoff

Updated: 2026-09-27 for the M4.8 Stage C record, attempt c2 (private point-in-time membership curation on
real_v1 and gate G1 under the plan-literal code rule).

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
  `f416af8c5196844052c20cb6ebf580c39ab765fa` (main after PR #273).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #272: M4.0 local real-data diagnostic through M4.7a-3 PIT universe construction,
  M4.7b-2 preregistration freeze on real_v1, M4.7c-1 point-in-time rerun on real_v1
  (`extend_first`), the M4.7c-2 decision record, M4.7 support v2 with the registration v2 rerun, M4.8
  Stage A (partition rule v2, seal carry, segment-local validation, census v3 code), and M4.8 Stage B (causal
  engines, locked capital, terminal schema v3, segment runner).
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88` (PR #200), `e76ddb4e` (PR #203), `770cfe54` (PR #260), `49eacdd4` (PR #261),
  `2c07ee4d` (PR #262), `76a0e43a` (PR #264), `de3172bc` (PR #265), `d15ef1d4` (PR #266),
  `45fe5adc` (PR #267), `0d87d7eb` (PR #268), `a9c94dca` (PR #269), `e4662859` (PR #270),
  `dcf7b86a` (PR #271), `bfdca57a` (PR #272), and `f416af8c` (PR #273).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`);
  it is preserved history outside the active queue.
- This candidate's diff and artifacts add no raw private data, provider response, provider-derived membership
  list, or private path. The tracked tree holds 53 inherited private-path occurrences in 17 files, identical at
  the base; redacting them needs separate owner authorization.

## Recorded Delivery Scope

- Candidate branch `claude/m4_8c-membership` records M4.8 Stage C under the accepted binding plan Revision 3
  (`bd1bf587…bf3e`), sections 2.3, 2.4, 5.1, and 7.3. No repository code changes.
  - Private curation files (under `<private_data_root>`, never committed): 182 supplement rows (142
    `start_date_fill`, 30 `absent_member_add` keyed by as-traded codes, 10 `date_correction` typed
    `correction_not_primary`), 360 reconstructed changes, and 17 S&P DJI factsheet line counts, from public
    documents under O48-1(a).
  - Public census output `reports/m4_8_membership_census.{json,md}` (counts and hashes only).
  - Records: `docs/engineering_log.md` (Stage C c1 and c2 entries) and `docs/decision_log.md` (Stage C record).
- `real_v1` and every committed M4.7 and M4.8 artifact stay byte-identical.
- Evidence ceiling remains `DIAGNOSTIC_ONLY`.

## Current Research Gate Summary

Milestone 4.7 is completed; see `docs/current_roadmap.md`. Registration v2 on real_v1 records the
gate outcome `extend_first` (60 IC months; Family A MDE_f 0.0437-0.1293 against the 0.02 floor).
M4.8 Stages A and B are merged (synthetic fixtures). Stage C gate G1 (attempt c2, plan-literal codes)
on real_v1 membership metadata passed: `coverage_start_pre` = `D0_pre` = 2015-07-31, 47 pre-segment IC months,
unresolved-change fraction 0.0196 (cap 0.02), R3-2c 0.0079. Six required anchors pass on the floor rule (no
December factsheet exists); modelled anchors would move the start to 2016-10-31 (32 months, blocked). No price
value was read. The holdout
window remains sealed and unaccessed. Evidence ceiling remains `DIAGNOSTIC_ONLY`.

## Immediate Blockers Or Owner Decisions

- Stage C convention C-1 is withdrawn from the gate of record; a plan clarification for it is optional (the
  C-1 diagnostic keeps the 2015-07-31 start with R3-2c 0.0064).
- Owner disposition of the 10 M-2 discrepancy lines (vendor start dates the public lists and all 17 S&P DJI
  factsheet counts contradict): accept as the R3-10 caveat, revise M-2 by plan revision, or seek primary sources.
- The Stage C attempt c2 record needs its Round 2 CRITICAL two-seat review before Stage D builds real_v2.
- Owner confirmation: the first Stage C Wikipedia request sent the owner's account email in its user agent
  (engineering log, c2 entry).
- Owner item carried: the frozen registration v2 validator accepts a cash completion dated after the calendar end
  (review A2-05); schema v3 refuses it.

## Next Safe Action

- Coordinator dispatches the Round 2 CRITICAL review of Stage C attempt c2; after the owner's M-2 disposition,
  Stage D builds real_v2 with the curated files and splits identity at the 2017-04-03 share exchange (A2-C-ADV-2).

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
