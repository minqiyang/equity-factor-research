# Current Handoff

Updated: 2026-09-26 for the Milestone 4.7 stage b-2 registration freeze.

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
  `45fe5adc2a4322dedec3aa109bfb4d30ac95e08a` (main after PR #267).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #267: M4.0 local real-data 50-name diagnostic, M4.1
  walk-forward ML combination, M4.2 purged CPCV, M4.3 multiple-testing
  diagnostics, M4.4 point-in-time membership and terminal cash, M4.5 optional
  square-root impact, M4.6 style risk attribution, the coordination standard
  V8.0 path (PR #256), the governance constitution (PR #257), the impact
  reconciliation and M4.6 timing fixes (PR #258), the Track A code
  retirement (PR #259), the owner-delegated decision record (PR #260), and
  the typed CPCV geometry refusal and fail-closed DSR/Newey-West inputs (PR #261),
  the M4.7a-0 statistical and portfolio core on golden fixtures (PR #262),
  the M4.7a-1 EODHD retrieval and holdout partition modules (PR #264),
  the M4.7a-2 PIT universe build, terminal tooling, and coverage census (PR #265),
  the M4.7b-1 runner integration on the synthetic fixture universe (PR #266),
  and the M4.7a-3 PIT universe construction, delisting curation, and coverage census on real_v1 (PR #267).
- M4.3 through M4.6 carry synthetic evidence only; the committed real-data
  report predates M4.3.
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88` (PR #200), `e76ddb4e` (PR #203), `770cfe54` (PR #260), `49eacdd4` (PR #261),
  `2c07ee4d` (PR #262), `76a0e43a` (PR #264), `de3172bc` (PR #265), and `d15ef1d4` (PR #266).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`);
  it is preserved history outside the active queue.
- Raw private data, provider responses, provider-derived membership lists, and
  private paths remain outside the public repository.

## Recorded Delivery Scope

- Milestone 4.7 Binding Implementation Plan Revision 11 (`coord/plans/m4_7_binding_plan.md`,
  SHA-256 `6541db93336e9181ebf3ad2f066b7b17f4550a17565036c2db5a5d82872a6407`,
  3,237 lines) is formally accepted under Coordination Standard V8.5 and Owner
  Directives 1–4.
- Premise VP-2 is ratified (Owner Item O-8) in `docs/decision_log.md`.
- Implementation is decoupled into pure golden-fixture core (Phase M4.7a-0),
  retrieval module (Phase M4.7a-1), universe build/census (Phase M4.7a-2), and
  runner integration (Phase M4.7b-1).
- M4.7a-0 (PR #262): consideration bases, `resolve_pit_universe_mask`, Family A,
  long-run variance and MDE, family-partitioned BY, the common-support core,
  and the gate; report `coord/reports/m4_7a0_engine_labels_and_wrapper_impl.md`.
- M4.7a-1 (PR #264): `src/data/eodhd_retrieval.py` and
  `src/data/holdout_partition.py`; report
  `coord/reports/m4_7a1_retrieval_and_partition_impl.md`.
- M4.7a-2 (PR #265): the seal script, universe build, terminal tooling, support
  wiring, and coverage census under `research/m4_7_*.py`; report
  `coord/reports/m4_7a2_universe_and_census_impl.md`.
- M4.7b-1 (PR #266): the runner in `research/m4_7_sp500_pit_rerun.py`, tested on
  the committed fixture universe; report `coord/reports/m4_7b1_runner_integration_impl.md`.
- M4.7a-3 (PR #267): O-3 Option A seal rule (one-year holdout, 7 in-band years, 48 IC months,
  declared `calendar_source`) and full offline run on `real_v1`; O-7 accepted shortfall and O-8 VP-2
  re-ratification; census `ready_with_caveats:coverage_shortfall_accepted,holdout_breadth_after_identity`;
  dual audit completed with `MATERIAL: 0`.
- M4.7b-2 candidate (branch `claude/m4_7b2-registration-freeze`): preregistration frozen in
  `docs/preregistrations/m4_7_sp500_pit_rerun_v1.json` (SHA-256 `6ea218a6…1c9f`) binding snapshot `real_v1`
  upstream digests, calendar `SPY.US_eod_dates_v1`, holdout `[2019-07-31, 2020-07-31)`, 32 IC months,
  Owner Decisions O-1, O-3, O-6, O-7, O-8.

## Current Research Gate Summary

Milestone 4 diagnostic capabilities M4.0 through M4.6 are merged; see
`docs/current_roadmap.md`. The static 50-name real-data diagnostic shows no
detectable cross-sectional predictability and lacks statistical power. M4.7,
a survivorship-reduced S&P 500 point-in-time universe with a pre-registered
rerun, is the active research milestone. The evidence ceiling remains
`DIAGNOSTIC_ONLY`.

## Immediate Blockers Or Owner Decisions

- No blocker for PR #268 merge. Dual audit completed (Seat 1 MATERIAL: 0, Seat 2 MATERIAL: 0
  after O-3 decision record reconciliation). Owner Decisions O-1, O-3, O-6, O-7, O-8 recorded.

## Next Safe Action

- Squash-merge PR #268 into `main`, verify target-branch commit, fast-forward local `main`,
  record owner O-4 private-data authorization in `docs/engineering_log.md`, and execute Phase M4.7c-1
  with registration `6ea218a6…1c9f` on `real_v1`.

## Source Routing

- Authority, research-safety invariants, and continuation: `AGENTS.md`.
- Standing owner grants: `AUTHORITY.md`.
- Workflow, review, waiting, and stop behavior:
  `docs/codex_long_running_controller.md`.
- Active North Star and demo-first delivery: `docs/north_star.md`.
- Program milestones, Demo v0 criteria, and imperfection backlog:
  `docs/current_roadmap.md`.
- Long-term evidence policy: `docs/research_program_charter.md`.
- Track A protocol and gate semantics (historical protocol context):
  `docs/eodhd_sp500_diagnostic_campaign_contract.md` and its preregistrations.
- Historical decisions, validation, and failures: `docs/decision_log.md`,
  `docs/engineering_log.md`, and `docs/troubleshooting_log.md`.
