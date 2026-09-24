# Current Handoff

Updated: 2026-09-23 after owner adoption of the strategic audit recommendations.

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
  `05284bc55e7d6d9cac46e981e18f74b2bd8135db` (main after PR #259).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #259: M4.0 local real-data 50-name diagnostic, M4.1
  walk-forward ML combination, M4.2 purged CPCV, M4.3 multiple-testing
  diagnostics, M4.4 point-in-time membership and terminal cash, M4.5 optional
  square-root impact, M4.6 style risk attribution, the coordination standard
  V8.0 path (PR #256), the governance constitution (PR #257), the impact
  reconciliation and M4.6 timing fixes (PR #258), and the Track A code
  retirement (PR #259).
- M4.3 through M4.6 carry synthetic evidence only; the committed real-data
  report predates M4.3.
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88a6e049b63aa2ddeae8560fea08fda23e` (PR #200 merge), and
  `e76ddb4efe916b5d733e6b583b05c13b2f3ff85d` (PR #203 merge).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`);
  it is preserved history outside the active queue.
- Raw private data, provider responses, provider-derived membership lists, and
  private paths remain outside the public repository.

## Recorded Delivery Scope

- Owner decision 2026-09-23: adopt coordination standard V8.0 and every decision
  of the strategic audit.
- Governance streamlining: the V8.0 standard path, an `AGENTS.md` constitution
  with invariants R1–R12, owner grants recorded in `AUTHORITY.md`, North Star
  edge thesis and kill criteria, and a handoff freshness test.
- Diagnostic corrections: the M4.5 relative post-trade tolerance, a capacity
  report Sharpe guard for short books, real-data report benchmark excess and
  code identity with long-short PBO, and a timing-contract M4.6 section. The
  spread floor and changing-universe style attribution wait for M4.8.
- Legacy Track A code retirement: the campaign runner, PIT manifest validator,
  and ledger runtime leave the tree; tag `track-a-legacy-final` keeps them at
  `8fa0055`.

## Current Research Gate Summary

Milestone 4 diagnostic capabilities M4.0 through M4.6 are merged; see
`docs/current_roadmap.md`. The static 50-name real-data diagnostic shows no
detectable cross-sectional predictability and lacks statistical power. M4.7,
a survivorship-reduced S&P 500 point-in-time universe with a pre-registered
rerun, is the next research milestone. The evidence ceiling remains
`DIAGNOSTIC_ONLY`.

## Immediate Blockers Or Owner Decisions

- PR #260 needs its V8.0 review seat; the producing session dispatches none.
  The owner approved `AUTHORITY.md` on 2026-09-23, and PR #257 merged it at
  `5c5fd0c`.
- M4.7 implementation waits for its binding plan from the V8.0 DESIGN route.
  The retrieval run needs the owner to set `EFR_EODHD_API_TOKEN` in its
  environment.
- Regenerating the committed real-data report needs explicit authorization to
  read local private data.

## Next Safe Action

- PR #259 (Track A code retirement) is merged at `05284bc`. The active task is
  this decision record, PR #260: its exact-head REVIEW seat.
- After PR #260 merges, the M4.7 planning card follows: the pre-flight `AUDIT`
  of M4.2–M4.4 and the DESIGN route for the M4.7 binding plan.

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
