# Current Handoff

Updated: 2026-09-29 for Milestone 5 steps 1 and 2 (trial file, factor catalog, public-data baseline).

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
- PR #263 (controller review rules, rebuilt on `main` after PR #276 on 2026-09-28) touches the controller, the
  handoff, and both logs; whichever of it and this candidate lands second refreshes those files.
- This candidate adds no raw private data, provider response, provider-derived membership list, security code, or
  private path.

## Recorded Delivery Scope

- Candidate branch `claude/m5-baseline` delivers Milestone 5 steps 1 and 2 (`docs/current_roadmap.md`).
- Step 1: trial file `docs/preregistrations/m5_trial_family_v1.json` (SHA-256 `a99a862c...417a`, committed alone
  before any result), amendment 1 for the post-publication split (`b3992b32...0751`), and amendment 2 for the
  monthly execution order and the publication trait (`59461b15...72f1`), each committed alone before the results
  it governs; factor catalog `research/factor_catalog.csv` with 1,160 rows (58 implemented).
- Step 2: `src/data/public_factors.py` (cached public downloads with a SHA-256 manifest) and
  `research/m5_factor_baseline.py`; report `reports/m5_factor_baseline.md` with its JSON, manifest, and attempt log.
- Result (`DIAGNOSTIC_ONLY`, public long-short series, signal month t-2, execution at the t-1 close): the declared
  rule picks R1, inverse volatility, as the baseline product; 8 of 8 conditions hold on the 153 JKP factors. R1
  has lower drawdown and higher Sharpe in both halves and at both costs, with a slightly lower mean; no S2 test
  survives correction. The round 1 results under v1 timing stay recorded as prior exposure.
- Reviews (CRITICAL, two seats): round 1 at `58f398c` found one MATERIAL each (execution order; publication trait);
  round 2 at `1100e3c` reports `MATERIAL: 0` from both seats. The later handoff and roadmap refresh is records only.
- Tests: `tests/test_m5_factor_baseline.py` (31 synthetic tests) and `tests/test_factor_catalog.py`. The network
  allowlist adds `src/data/public_factors.py`, limited to `urllib.request`.

## Current Research Gate Summary

See `docs/current_roadmap.md` for milestone status. Milestone 5 steps 1 and 2 are delivered on this candidate: the
baseline product is R1 (inverse volatility across all factors) at `DIAGNOSTIC_ONLY`. M4.8 stays paused after Stage
D; the seal window remains unaccessed. The stock-level check on the local point-in-time snapshots is step 4.

## Immediate Blockers Or Owner Decisions

- None for steps 1 and 2. PR #263 (controller review rules) awaits the owner's merge.
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
