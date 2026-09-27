# Current Handoff

Updated: 2026-09-26 for the M4.7 support v2 correction (asset-level holding-period isolation) and
registration v2 rerun.

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
  `e4662859f684d23e1d79b566c14e7391b1f701e6` (main after PR #270).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #270: M4.0 local real-data diagnostic through M4.7a-3 PIT universe construction,
  M4.7b-2 preregistration freeze on real_v1, M4.7c-1 point-in-time rerun on real_v1
  (`extend_first`), and the M4.7c-2 decision record.
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88` (PR #200), `e76ddb4e` (PR #203), `770cfe54` (PR #260), `49eacdd4` (PR #261),
  `2c07ee4d` (PR #262), `76a0e43a` (PR #264), `de3172bc` (PR #265), `d15ef1d4` (PR #266),
  `45fe5adc` (PR #267), `0d87d7eb` (PR #268), `a9c94dca` (PR #269), and `e4662859` (PR #270).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`);
  it is preserved history outside the active queue.
- Raw private data, provider responses, provider-derived membership lists, and
  private paths remain outside the public repository.

## Recorded Delivery Scope

- Candidate PR #271 (branch `claude/breadth-support-isolation-fix`) delivers support v2:
  - `research/m4_7_common_support.py`: asset-level exclusion cells `X` and the evaluation mask
    `E = S_mask & ~X` over one continuous window; gap windows, segments, and peeling removed.
  - `research/m4_7_coverage_census.py`: `census/asset_support.json`, the v2 public census, and
    R-CENSUS-2 on the asset-level excluded fraction.
  - `research/m4_7_sp500_pit_rerun.py`: registration v2 contract, one engine call per book, `E` for
    IC, books, and benchmark; refuses the v1 document at `schema_version`.
  - Real-data outputs: census v2, seal confirmation v2, registration v2 (`4a6f8b5a…e7dc`), and the
    rerun v2 report, sidecar, and 231-record trials JSONL.
  - Audit round 1 completed: Seat 1 AUDIT1-M01, Seat 2 ADV-1.
  - Independent evaluation by Claude Opus 5.5 High recommended Option 1 (Owner Accepted Risk with expiry).
  - Owner fully accepted Opus 5.5 High recommendation; Owner Risk Acceptance recorded in `docs/decision_log.md`.
  - Docs-only remediation commit added.
- v1 registration, seal record, census, rerun outputs, and v1 private derived files are unchanged.
- Evidence ceiling remains `DIAGNOSTIC_ONLY`.

## Current Research Gate Summary

Milestone 4.7 is completed; see `docs/current_roadmap.md`. Registration v2 on real_v1 evaluates all
61 resets and 60 IC months at 424-433 names per reset (27 asset-level exclusion cells of 26,237).
No factor survives BY correction; Family A MDE_f is 0.0437-0.1293 against the 0.02 floor, so the
gate outcome stays `extend_first`. The holdout window remains sealed and unaccessed. Evidence
ceiling remains `DIAGNOSTIC_ONLY`.

## Immediate Blockers Or Owner Decisions

- None. Owner has formally accepted the Support v2 lookahead risk (AUDIT1-M01, ADV-1) at DIAGNOSTIC_ONLY
  ceiling expiring at the next registration freeze.
- Merge disposition for PR #271: Owner-accepted residual MATERIAL.

## Next Safe Action

- Perform delta review verification on docs-only commit, and proceed with authorized squash merge of PR #271.

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
