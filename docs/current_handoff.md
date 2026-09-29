# Current Handoff

Updated: 2026-09-28 for the controller review-rule update (PR #263) after North Star v2 (PR #276).

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
  `5b74d35a81aca61f3fb28f065922831056659e78` (main after PR #276).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #275: M4.0 local real-data diagnostic through M4.7 (PIT universe, registrations v1 and v2 on
  real_v1, `extend_first`), M4.7 support v2, and M4.8 Stages A–D (partition rule v2 and seal carry, causal engines
  and terminal schema v3, membership curation with gate G1 passed, private snapshot `real_v2`), and North Star
  v2 (PR #276: factor-class allocator, owner process constraints, M4.8 paused, Milestone 5 active).
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88` (PR #200), `e76ddb4e` (PR #203), `770cfe54` (PR #260), `49eacdd4` (PR #261),
  `2c07ee4d` (PR #262), `76a0e43a` (PR #264), `de3172bc` (PR #265), `d15ef1d4` (PR #266),
  `45fe5adc` (PR #267), `0d87d7eb` (PR #268), `a9c94dca` (PR #269), `e4662859` (PR #270),
  `dcf7b86a` (PR #271), `bfdca57a` (PR #272), `f416af8c` (PR #273), `1c56939b` (PR #274), and
  `9dee2df2` (PR #275), and `5b74d35a` (PR #276).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`); preserved history.
- Milestone 5 steps 1 and 2 sit on the unpublished branch `claude/m5-baseline`; they touch no controller text.
- This candidate adds no raw private data, provider response, provider-derived membership list, security code, or
  private path.

## Recorded Delivery Scope

- Candidate branch `docs/controller-v85-alignment` (PR #263, rebuilt on `main` after PR #276) updates the
  controller review rules to the live coordination standard: findings are `MATERIAL` or `ADVISORY`, review
  rounds follow the owner's limit of two per card, merge needs `MATERIAL: 0` or an explicit disposition, and
  "Herdr+Pi" becomes "Herdr". It adds the owner's rule that PR text is short and plain.
- Records: `docs/decision_log.md`, `docs/engineering_log.md`, regenerated `docs/repo_map.md`.
- Test change: `test_controller_review_rules_follow_materiality_and_owner_round_limit`; two controller pins
  updated.

## Current Research Gate Summary

See `docs/current_roadmap.md` for milestone status. Registration v2 on real_v1 records `extend_first` (60 IC
months; Family A MDE_f 0.0437–0.1293 against the 0.02 floor). M4.8 is paused after Stage D; its registered gate
would need 286 to 2,508 IC months. Milestone 5 moves the core question to long public factor-return histories and a
factor catalog, with the local point-in-time snapshots as the stock-level check. The seal window remains
unaccessed. Evidence ceiling remains `DIAGNOSTIC_ONLY`.

## Immediate Blockers Or Owner Decisions

- Cross-family review of the Milestone 5 trial freeze and step 2 code before the Milestone 5 PR.
- Carried to the M4.8 resume point: nine Stage D advisories and the M-2 disposition of 10 discrepancy lines.
- Owner items carried: the iCloud sync of the private data root (Stage D, A2-D-ADV-6); the Stage C Wikipedia
  request that sent the owner's account email in its user agent (engineering log, c2 entry); the frozen
  registration v2 validator accepting a cash completion after the calendar end (A2-05).
- Open for the first stock-level confirmation design: whether to spend the seal window.

## Next Safe Action

- Milestone 5: review the trial freeze and step 2 code, then open the Milestone 5 PR; step 3 (timing
  questions) follows.

## Source Routing

- Authority, research-safety invariants, and continuation: `AGENTS.md`.
- Standing owner grants: `AUTHORITY.md`.
- Workflow, review, waiting, and stop behavior: `docs/codex_long_running_controller.md`.
- Active North Star, core question, and decision rule: `docs/north_star.md`.
- Program milestones, Demo v0 criteria, and imperfection backlog: `docs/current_roadmap.md`.
- Long-term evidence policy: `docs/research_program_charter.md`.
- Track A protocol and gate semantics (historical protocol context):
  `docs/eodhd_sp500_diagnostic_campaign_contract.md` and its preregistrations.
- Historical decisions, validation, and failures: `docs/decision_log.md`,
  `docs/engineering_log.md`, and `docs/troubleshooting_log.md`.
