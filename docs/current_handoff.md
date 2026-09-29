# Current Handoff

Updated: 2026-09-29 for the CI speed change (four test lanes, one shared runner v3 run).

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
  `edbd34c325ed39c5735065ff9da913e4fb625b8e` (main after PR #277).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #275: M4.0 local real-data diagnostic through M4.7 (PIT universe, registrations v1 and v2 on
  real_v1, `extend_first`), M4.7 support v2, and M4.8 Stages A–D (partition rule v2 and seal carry, causal engines
  and terminal schema v3, membership curation with gate G1 passed, private snapshot `real_v2`), and North Star
  v2 (PR #276: factor-class allocator, owner process constraints, M4.8 paused, Milestone 5 active), and the
  controller review rules (PR #263: `MATERIAL` or `ADVISORY` findings, two review rounds, short plain PR text),
  and Milestone 5 steps 1 and 2 (PR #277: trial file and two amendments, 1,160-row factor catalog, and the R1
  inverse-volatility baseline on public factor data, `DIAGNOSTIC_ONLY`).
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88` (PR #200), `e76ddb4e` (PR #203), `770cfe54` (PR #260), `49eacdd4` (PR #261),
  `2c07ee4d` (PR #262), `76a0e43a` (PR #264), `de3172bc` (PR #265), `d15ef1d4` (PR #266),
  `45fe5adc` (PR #267), `0d87d7eb` (PR #268), `a9c94dca` (PR #269), `e4662859` (PR #270),
  `dcf7b86a` (PR #271), `bfdca57a` (PR #272), `f416af8c` (PR #273), `1c56939b` (PR #274), and
  `9dee2df2` (PR #275), `5b74d35a` (PR #276), `23b1c734` (PR #263), and `edbd34c3` (PR #277).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`); preserved history.
- This candidate adds no raw private data, provider response, provider-derived membership list, security code, or
  private path.

## Recorded Delivery Scope

- Candidate branch `claude/ci-speed` shortens PR CI without changing any test's check or any file under `src/` or
  `research/`. `.github/workflows/ci.yml` runs four parallel lanes (`runner-v3`, `m4-pipelines`, `core`,
  `diagnostics`) with `-n 2 --dist loadgroup`; `xdist_group` marks keep each expensive module fixture on one
  worker; the runner v3 clean run is computed once per session and shared by pickle.
- Measured cause: the old core lane took 28m38s because the runner v3 clean run (about 550 s on CI) ran three
  times. Projected PR CI time: about 10 minutes, against about 30; the branch's first CI run confirms it.
- Tests: `test_ci_lanes_run_every_test_file_exactly_once` and the shared-helper test are new (3,343 collected, up
  from 3,341); three CI pins in `tests/test_ci_workflow.py` match the new layout.
- Milestone 5 step 1 and 2 records: `reports/m5_factor_baseline.md`, `docs/preregistrations/m5_trial_family_v1*`.

## Current Research Gate Summary

See `docs/current_roadmap.md` for milestone status. Milestone 5 steps 1 and 2 are delivered on this candidate: the
baseline product is R1 (inverse volatility across all factors) at `DIAGNOSTIC_ONLY`. M4.8 stays paused after Stage
D; the seal window remains unaccessed. The stock-level check on the local point-in-time snapshots is step 4.

## Immediate Blockers Or Owner Decisions

- None for steps 1 and 2.
- Carried to the M4.8 resume point: nine Stage D advisories and the M-2 disposition of 10 discrepancy lines.
- Owner items carried: the iCloud sync of the private data root (Stage D, A2-D-ADV-6); the Stage C Wikipedia
  request that sent the owner's account email in its user agent (engineering log, c2 entry); the frozen
  registration v2 validator accepting a cash completion after the calendar end (A2-05).
- Open for the first stock-level confirmation design: whether to spend the seal window.

## Next Safe Action

- Milestone 5 step 3: commit the v2 trial amendment that fixes the R2 to R4 parameters and the step 3 tests before
  any step 3 result; it settles the two open review advisories (A2-A2: whether prior exposures join the BY family;
  A2R2-A1: R4 against baselines on the same factor-month set). Then run the state tilt and the pooled class model
  against R1. The pooled model must avoid the `src/features/ml_combination.py:136` and `:179` NaN path.

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
