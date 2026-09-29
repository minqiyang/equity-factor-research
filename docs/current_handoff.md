# Current Handoff

Updated: 2026-09-29 for Milestone 5 step 3 (state tilt, factor momentum tilt, and pooled ridge against R1).

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
  `cb77a4e8fd93f8b2413bd1dbed0373b6989fd89b` (main after PR #278).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #275: M4.0 local real-data diagnostic through M4.7 (PIT universe, registrations v1 and v2 on
  real_v1, `extend_first`), M4.7 support v2, and M4.8 Stages A–D (partition rule v2 and seal carry, causal engines
  and terminal schema v3, membership curation with gate G1 passed, private snapshot `real_v2`), and North Star
  v2 (PR #276: factor-class allocator, owner process constraints, M4.8 paused, Milestone 5 active), and the
  controller review rules (PR #263: `MATERIAL` or `ADVISORY` findings, two review rounds, short plain PR text),
  and Milestone 5 steps 1 and 2 (PR #277: trial file and two amendments, 1,160-row factor catalog, and the R1
  inverse-volatility baseline on public factor data, `DIAGNOSTIC_ONLY`), and the CI speed change (PR #278: four
  parallel test lanes, one shared runner v3 run, about 10 minutes per PR).
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88` (PR #200), `e76ddb4e` (PR #203), `770cfe54` (PR #260), `49eacdd4` (PR #261),
  `2c07ee4d` (PR #262), `76a0e43a` (PR #264), `de3172bc` (PR #265), `d15ef1d4` (PR #266),
  `45fe5adc` (PR #267), `0d87d7eb` (PR #268), `a9c94dca` (PR #269), `e4662859` (PR #270),
  `dcf7b86a` (PR #271), `bfdca57a` (PR #272), `f416af8c` (PR #273), `1c56939b` (PR #274), and
  `9dee2df2` (PR #275), `5b74d35a` (PR #276), `23b1c734` (PR #263), `edbd34c3` (PR #277), and `cb77a4e8` (PR #278).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`); preserved history.
- This candidate adds no raw private data, provider response, provider-derived membership list, security code, or
  private path.

## Recorded Delivery Scope

- Candidate branch `claude/m5-step3` delivers Milestone 5 step 3 on public factor data, at `DIAGNOSTIC_ONLY`.
  - `docs/preregistrations/m5_trial_family_v1_amendment_3.json` (revision 2, SHA-256 `c59f69c8...`) was committed
    alone before any step 3 code or result. It passed two rounds of GPT and Opus review with `MATERIAL: 0`.
  - `research/m5_step3.py` forms R2 (state tilt), R3 (factor momentum tilt), and R4 (pooled ridge) on R1. It also
    runs the S3 tests (BY family 1047), the 999-draw random-date null, and the closure rule.
  - `tests/test_m5_step3.py` has 47 tests. Code review round 1 at `1775e42` reported `MATERIAL: 0` from both
    seats, and each seat recomputed the results independently.
- Result (`reports/m5_step3.md`):
  - Closure is open: R2 meets all 8 conditions against R1.
  - The state-timing claim does not qualify, because conditions 2 to 6 fail.
    - R2's mean is 0.23 bp a month below R1's (HAC p 0.38, BY q 1, random-date p 0.32).
    - It fails the post-publication drawdown check.
    - market_trend has 9 down episodes in 2000-2025.
  - No class x state cell survives.
- New public retrievals: `french_ff3_daily` and `jkp_accounting_characteristics_list`. Their hashes are in
  `reports/m5_public_data_manifest.json`, and the raw files stay in the gitignored cache.
- Records:
  - the review-seat rule in `docs/codex_long_running_controller.md` (GPT seats are Codex in their own Herdr tab and
    never relayed by a Claude agent);
  - the step 3 reporting conventions in `docs/decision_log.md`;
  - six code-review advisories in the roadmap backlog.

## Current Research Gate Summary

See `docs/current_roadmap.md` for milestone status. Milestone 5 steps 1 to 3 are delivered on this candidate. R1
(inverse volatility across all factors) stays the baseline product, and R2 goes to step 4 beside it, labeled "no
evidence of state timing". M4.8 stays paused after Stage D, and the seal window remains unaccessed.

## Immediate Blockers Or Owner Decisions

- None for step 3.
- Carried to the M4.8 resume point: nine Stage D advisories and the M-2 disposition of 10 discrepancy lines.
- Owner items carried:
  - the iCloud sync of the private data root (Stage D, A2-D-ADV-6);
  - the Stage C Wikipedia request that sent the owner's account email in its user agent (engineering log, c2
    entry);
  - the frozen registration v2 validator accepting a cash completion after the calendar end (A2-05).
- Open for the first stock-level confirmation design: whether to spend the seal window.

## Next Safe Action

- Milestone 5 step 4 (bridge): form the factor classes as long-only top-quintile point-in-time S&P 500 portfolios
  with costs, on the local snapshots, for R1 and R2.
  - Price classes come first; SEC as-filed value and quality classes come next.
  - The report states how much of the long-short result survives.
  - Commit the step 4 trial amendment before any step 4 result.

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
