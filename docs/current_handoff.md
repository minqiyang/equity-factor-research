# Current Handoff

Updated: 2026-09-26 for the Milestone 4.7 stage c-1 point-in-time rerun on real_v1.

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
  `0d87d7ebd5d5de2bf42f264eb2e29d127c4cc64d` (main after PR #268).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #268: M4.0 local real-data diagnostic through M4.7a-3 PIT universe construction,
  and M4.7b-2 preregistration freeze on real_v1 (`6ea218a6…1c9f`).
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88` (PR #200), `e76ddb4e` (PR #203), `770cfe54` (PR #260), `49eacdd4` (PR #261),
  `2c07ee4d` (PR #262), `76a0e43a` (PR #264), `de3172bc` (PR #265), `d15ef1d4` (PR #266),
  `45fe5adc` (PR #267), and `0d87d7eb` (PR #268).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`);
  it is preserved history outside the active queue.
- Raw private data, provider responses, provider-derived membership lists, and
  private paths remain outside the public repository.

## Recorded Delivery Scope

- Milestone 4.7 Binding Implementation Plan Revision 11 (`coord/plans/m4_7_binding_plan.md`,
  SHA-256 `6541db93…6407`) is formally accepted under Coordination Standard V8.5 and Owner Directives 1–4.
- Phase M4.7c-1 candidate delivers point-in-time rerun on snapshot `real_v1` bound to preregistration `6ea218a6…1c9f`:
  - `reports/m4_7_sp500_pit_rerun.md` (SHA-256 `2de61b35…49ca6`)
  - `reports/experiment_logs/m4_7_sp500_pit_rerun.json` (SHA-256 `07d8ab19…23b6`)
  - `reports/experiment_logs/m4_7_sp500_pit_rerun_trials.jsonl` (SHA-256 `eb366ab7…9b27`)
- Rerun completed with exit 0, zero Class I stops, and decision outcome `extend_first`
  (power inadequate, zero BY rejections across Family A and Family B, holdout unaccessed and sealed).
- Program decision: "Extend breadth or history under a new registration; the holdout stays sealed."

## Current Research Gate Summary

Milestone 4 diagnostic capabilities M4.0 through M4.6 are merged; see
`docs/current_roadmap.md`. The point-in-time rerun on real_v1 (Phase M4.7c-1)
confirms that statistical power is inadequate and no factor or composite
survives BY correction. Under the deterministic gate, the holdout window remains
sealed and unaccessed. Evidence ceiling remains `DIAGNOSTIC_ONLY`.

## Immediate Blockers Or Owner Decisions

- No operational blocker. Phase M4.7c-1 candidate is ready for independent dual audit.
- Owner Decisions O-1 through O-8 are formally recorded in `docs/decision_log.md` and `docs/engineering_log.md`.

## Next Safe Action

- Open PR for Phase M4.7c-1, run independent dual audit, squash-merge into `main`,
  and advance to Phase M4.7c-2 (decision log entry, roadmap close, and milestone conclusion).

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
