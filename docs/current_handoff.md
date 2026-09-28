# Current Handoff

Updated: 2026-09-28 for the North Star v2 governance change (M4.8 paused after Stage D; Milestone 5 factor
collection and factor timing active).

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
  `9dee2df2267c4cfb4b587783a8447d2cbae3d88a` (main after PR #275).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #275: M4.0 local real-data diagnostic through M4.7 (PIT universe, registrations v1 and v2 on
  real_v1, `extend_first`), M4.7 support v2, and M4.8 Stages A–D (partition rule v2 and seal carry, causal engines
  and terminal schema v3, membership curation with gate G1 passed, private snapshot `real_v2`).
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88` (PR #200), `e76ddb4e` (PR #203), `770cfe54` (PR #260), `49eacdd4` (PR #261),
  `2c07ee4d` (PR #262), `76a0e43a` (PR #264), `de3172bc` (PR #265), `d15ef1d4` (PR #266),
  `45fe5adc` (PR #267), `0d87d7eb` (PR #268), `a9c94dca` (PR #269), `e4662859` (PR #270),
  `dcf7b86a` (PR #271), `bfdca57a` (PR #272), `f416af8c` (PR #273), `1c56939b` (PR #274), and
  `9dee2df2` (PR #275).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`); preserved history.
- PR #263 (controller alignment with Coordination Standard V8.5, opened 2026-09-26) is stale and overlaps
  `docs/codex_long_running_controller.md`; verify its live state before touching the controller.
- This candidate adds no raw private data, provider response, provider-derived membership list, security code, or
  private path.

## Recorded Delivery Scope

- Candidate branch `claude/north-star-v2-governance` records the owner decisions of 2026-09-28
  (`docs/decision_log.md`): North Star v2 (`docs/north_star.md`), amended invariants and the Owner Process
  Constraints (`AGENTS.md`), six primary milestones with M4.8 paused and Milestone 5 active
  (`docs/current_roadmap.md`, Milestone 5 = factor-class allocator), controller startup, seat, stop, and
  Process Failures updates, factor intake in `PROJECT_SPEC.md`, `README.md`, and the regenerated
  `docs/repo_map.md`.
- Assessments committed with it: `coord/reports/progress_assessment_opus.md`,
  `coord/reports/north_star_speed_audit_opus.md`, and `coord/reports/north_star_vision_assessment_opus.md`.
- Test change: the North Star structure test checks the v2 sections (Core Question, Objective And Benchmark,
  Decision Rule).
- The change takes effect when the owner confirms the PR.

## Current Research Gate Summary

See `docs/current_roadmap.md` for milestone status. Registration v2 on real_v1 records `extend_first` (60 IC
months; Family A MDE_f 0.0437–0.1293 against the 0.02 floor). M4.8 is paused after Stage D; its registered gate
would need 286 to 2,508 IC months. Milestone 5 moves the core question to long public factor-return histories and a
factor catalog, with the local point-in-time snapshots as the stock-level check. The seal window remains
unaccessed. Evidence ceiling remains `DIAGNOSTIC_ONLY`.

## Immediate Blockers Or Owner Decisions

- Owner confirmation of this governance PR.
- Carried to the M4.8 resume point: nine Stage D advisories and the M-2 disposition of 10 discrepancy lines.
- Owner items carried: the iCloud sync of the private data root (Stage D, A2-D-ADV-6); the Stage C Wikipedia
  request that sent the owner's account email in its user agent (engineering log, c2 entry); the frozen
  registration v2 validator accepting a cash completion after the calendar end (A2-05).
- Open for the first stock-level confirmation design: whether to spend the seal window.

## Next Safe Action

- After the owner confirms this PR: Milestone 5 step 1 (hashed trial file and factor catalog) and step 2
  (risk-balanced all-class baseline on French and JKP returns with FRED condition series).

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
