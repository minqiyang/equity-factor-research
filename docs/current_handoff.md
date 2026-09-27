# Current Handoff

Updated: 2026-09-27 for the M4.8 Stage A candidate (partition rule v2, seal carry, segment-local
validation, and census v3 code on synthetic fixtures).

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
  `dcf7b86ae920502271894c17659e80886e7a235c` (main after PR #271).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #271: M4.0 local real-data diagnostic through M4.7a-3 PIT universe construction,
  M4.7b-2 preregistration freeze on real_v1, M4.7c-1 point-in-time rerun on real_v1
  (`extend_first`), the M4.7c-2 decision record, and M4.7 support v2 with the registration v2 rerun.
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88` (PR #200), `e76ddb4e` (PR #203), `770cfe54` (PR #260), `49eacdd4` (PR #261),
  `2c07ee4d` (PR #262), `76a0e43a` (PR #264), `de3172bc` (PR #265), `d15ef1d4` (PR #266),
  `45fe5adc` (PR #267), `0d87d7eb` (PR #268), `a9c94dca` (PR #269), `e4662859` (PR #270), and
  `dcf7b86a` (PR #271).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`);
  it is preserved history outside the active queue.
- Raw private data, provider responses, provider-derived membership lists, and
  private paths remain outside the public repository.

## Recorded Delivery Scope

- Candidate branch `claude/m4_8a-partition` delivers M4.8 Stage A under the accepted binding plan
  Revision 3 (`bd1bf587…bf3e`) and owner decision O48-2(i), on synthetic fixtures only:
  - `src/data/holdout_partition.py`, `src/data/eodhd_retrieval.py`: partition rule v2
    (`sealed_window_only_partition_v2`) with per-side discovery files, per-side validation, the pre-seal
    volume rebase (`pre_seal_volume_share_basis_v1`), and the seal carry record `holdout_seal_v2.json`.
  - `research/m4_8_membership.py`: curated supplement, change log, and anchor readers (M-1..M-8) and
    `curated_coverage_start_v2`.
  - `research/m4_7_universe_build.py`: `discovery_segments` and segment-local validation (SL-1..SL-6, SL-8).
  - `research/m4_7_coverage_census.py`: `membership-census`, `census-v3`, and readiness R3-1..R3-10.
  - SL-7 consumer inventory in `docs/engineering_log.md` (2026-09-27 entry).
  - Attempt a2 (PR #272) resolves the review findings: after-anchor split basis (R7), aggregate-only public
    terminal summary (R11), and the census v3 VP-1 diagnostic; attempt a3 binds that summary to an explicit
    approved schema.
- v1 and v2 registrations, seal records, census reports, and rerun outputs are unchanged; the rule v1 code
  path gives byte-identical outputs on the synthetic end-to-end fixtures.
- Evidence ceiling remains `DIAGNOSTIC_ONLY`.

## Current Research Gate Summary

Milestone 4.7 is completed; see `docs/current_roadmap.md`. Registration v2 on real_v1 records the
gate outcome `extend_first` (60 IC months; Family A MDE_f 0.0437-0.1293 against the 0.02 floor).
M4.8 Stage A code is a candidate on synthetic fixtures; no real-data M4.8 result exists. The holdout
window remains sealed and unaccessed. Evidence ceiling remains `DIAGNOSTIC_ONLY`.

## Immediate Blockers Or Owner Decisions

- O48-1 (public-document retrieval) is needed before Stage C.
- The Stage A candidate needs its CRITICAL review and ablation acceptance before publication.

## Next Safe Action

- Coordinator dispatches the CRITICAL review of the Stage A candidate; Stage B rebases on merged Stage A.

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
