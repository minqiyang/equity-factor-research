# Current Handoff

Updated: 2026-09-26 for the Milestone 4.7 stage c-2 decision record and milestone conclusion.

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
  `a9c94dca59649dcb62af9b5d9fd65bde3400af45` (main after PR #269).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #269: M4.0 local real-data diagnostic through M4.7a-3 PIT universe construction,
  M4.7b-2 preregistration freeze on real_v1, and M4.7c-1 point-in-time rerun on real_v1 (`extend_first`).
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88` (PR #200), `e76ddb4e` (PR #203), `770cfe54` (PR #260), `49eacdd4` (PR #261),
  `2c07ee4d` (PR #262), `76a0e43a` (PR #264), `de3172bc` (PR #265), `d15ef1d4` (PR #266),
  `45fe5adc` (PR #267), `0d87d7eb` (PR #268), and `a9c94dca` (PR #269).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`);
  it is preserved history outside the active queue.
- Raw private data, provider responses, provider-derived membership lists, and
  private paths remain outside the public repository.

## Recorded Delivery Scope

- Milestone 4.7 Binding Implementation Plan Revision 11 (`coord/plans/m4_7_binding_plan.md`,
  SHA-256 `6541db93…6407`) is formally completed.
- Phase M4.7c-2 candidate delivers:
  - `docs/decision_log.md`: deterministic decision gate record for M4.7 rerun on real_v1 (`extend_first`).
  - `docs/current_roadmap.md`: Milestone 4.7 completed status and updated imperfection backlog rows.
  - `docs/engineering_log.md`: M4.7c-2 milestone completion entry.
  - `docs/current_handoff.md`: refreshed handoff to baseline `a9c94dca...`.
- Program decision: "Extend breadth or history under a new registration; the holdout stays sealed."
- Evidence ceiling remains `DIAGNOSTIC_ONLY`.

## Current Research Gate Summary

Milestone 4.7 is completed; see `docs/current_roadmap.md`. The pre-registered point-in-time rerun on real_v1
confirms that statistical power is inadequate and no factor or composite survives BY correction.
Under the deterministic gate, the outcome is `extend_first` and the holdout window remains sealed and unaccessed.
Evidence ceiling remains `DIAGNOSTIC_ONLY`.

## Immediate Blockers Or Owner Decisions

- No operational blocker. Milestone 4.7 delivery is complete.
- Follow-up research requires expanding universe breadth or historical depth under a new preregistration.

## Next Safe Action

- Open PR for Phase M4.7c-2, execute review verification, squash-merge into `main`,
  and await owner scoping instructions for the next research phase.

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
