# Current Handoff

Updated: 2026-09-25 for the Milestone 4.7 stage a-1 retrieval and partition candidate.

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
  `2c07ee4db70bc90cd449382c69b63765de2eab7d` (main after PR #262).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #262: M4.0 local real-data 50-name diagnostic, M4.1
  walk-forward ML combination, M4.2 purged CPCV, M4.3 multiple-testing
  diagnostics, M4.4 point-in-time membership and terminal cash, M4.5 optional
  square-root impact, M4.6 style risk attribution, the coordination standard
  V8.0 path (PR #256), the governance constitution (PR #257), the impact
  reconciliation and M4.6 timing fixes (PR #258), the Track A code
  retirement (PR #259), the owner-delegated decision record (PR #260), and
  the typed CPCV geometry refusal and fail-closed DSR/Newey-West inputs (PR #261),
  and the M4.7a-0 statistical and portfolio core on golden fixtures (PR #262).
- M4.3 through M4.6 carry synthetic evidence only; the committed real-data
  report predates M4.3.
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88a6e049b63aa2ddeae8560fea08fda23e` (PR #200 merge),
  `e76ddb4efe916b5d733e6b583b05c13b2f3ff85d` (PR #203 merge), and
  `770cfe5415c371aba4fa67312ff23130ccec1785` (PR #260 merge), and
  `49eacdd4ce69fe1db9b779bfb7cc975d8b5950d3` (PR #261 merge).
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
- M4.7a-0 (merged in PR #262): the engines accept the three consideration bases, record `terminal_basis_counts`
  and the v2 `terminal_settlement_contract`, and export
  `resolve_pit_universe_mask`; Family A factor functions and definitions;
  `newey_west_long_run_variance`, `mde_from_long_run_variance`, and the
  family-partitioned `summarize_multiple_testing`; the common-support core in
  `research/m4_7_common_support.py`; the gate and halves in
  `research/m4_7_sp500_pit_rerun.py`. Synthetic golden fixtures only; report
  `coord/reports/m4_7a0_engine_labels_and_wrapper_impl.md`.
- M4.7a-1 candidate (branch `claude/m4_7a1-retrieval-and-partition`):
  `src/data/eodhd_retrieval.py`, the one network-capable module, with the
  nine-command CLI, the injected transport seam, the token sanitizer, the
  role-keyed manifest with atomic writes, seal-gated `calendar`, `splits`,
  `eod`, and `dividends` partitioned at `holdout_end`, the run-local scale
  check, `provider_error_history`, and offline `plan` and `verify`;
  `src/data/holdout_partition.py` with the raw-count seal derivation and
  manifest-authorized, hash-verified reads; T-RET-1..17, T-SEAL-1, and
  T-STRUCT-1 on a fake transport. No live network call and no private data;
  report `coord/reports/m4_7a1_retrieval_and_partition_impl.md`.

## Current Research Gate Summary

Milestone 4 diagnostic capabilities M4.0 through M4.6 are merged; see
`docs/current_roadmap.md`. The static 50-name real-data diagnostic shows no
detectable cross-sectional predictability and lacks statistical power. M4.7,
a survivorship-reduced S&P 500 point-in-time universe with a pre-registered
rerun, is the active research milestone. The evidence ceiling remains
`DIAGNOSTIC_ONLY`.

## Immediate Blockers Or Owner Decisions

- No blocker for Phase M4.7a-1: every test runs on the injected fake
  transport and synthetic fixtures.
- Phase M4.7a-3 private data retrieval will require `EFR_EODHD_API_TOKEN` and
  standing data authority D1.

## Next Safe Action

- CRITICAL-lane review of the M4.7a-1 candidate (two fresh formal reviewers)
  and coordinator acceptance of its exact head; M4.7a-2 proceeds under its own
  card and consumes `data.holdout_partition` for the seal script and
  manifest-authorized reads.

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
