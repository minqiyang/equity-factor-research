# Current Handoff

Updated: 2026-09-15 after owner alignment on North Star and demo-first delivery.

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
requirements.

## Latest Recorded Operational Checkpoint

- Last externally verified protected baseline when this handoff was authored:
  `425b7c88a6e049b63aa2ddeae8560fea08fda23e`.
- Historical CCA1 start baseline:
  `c178d16d84a455774bcde73f21a9e3ff39ea7b2c`.
- Working clone baseline:
  `e76ddb4efe916b5d733e6b583b05c13b2f3ff85d`.
- PR #180 is merged. It records the long-term factor-to-portfolio direction
  and leaves the frozen Track A campaign in place.
- PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
- PR #199 Path A first checkpoint and PR #200 Path B first checkpoint are
  merged. PR #200 landed at that protected baseline.
- No pull request was open at the verified start of this work.
- This publication began from a clean `main` checkout at the baseline above.
  Its live PR and merge state must be checked separately after publication.
- Milestone 1 (Core Research & Synthetic Engine) is completed baseline:
  data contracts, signal timing, drift-aware portfolio accounting, synthetic demos,
  and Track B first checkpoints (Path A PR #199, Path B PR #200).
- Historical Track A 14-trial diagnostic run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`).
  This refusal is preserved as immutable historical evidence and is not an active
  blocker for demo-first development.
- A local 2026-09-13 metadata and numerical diagnostic confirmed sufficient local
  data history for exploration, with documented caveats (zero-volume segments,
  date gaps, unverified adjustment events) deferred for layered handling. No
  profitability is claimed.
- Milestone 2 (Demo v0 Working Vertical Slice) is the active delivery target.
- Raw private data, ticker lists, provider responses, and performance values
  remain outside the public repository.

## Recorded Delivery Scope

- Demo-first delivery alignment: Milestone 2 Demo v0 vertical slice.
- Maintain immutable historical record of Track A refusal without letting it
  block the new demo program.
- Defer non-blocking imperfections (presentation polish, extra factors,
  optional ledger schemas, advanced statistics) to the lightweight backlog.
- Strictly preserve research safety invariants: simulated portfolio only,
  no broker integrations, orders, paper/live trading, or lookahead.

## Current Research Gate Summary

Milestone 1 completed; see `docs/current_roadmap.md`. Historical Track A 14-trial run
remains REFUSED. Track B Path A and Path B first checkpoints are merged on main.
The local 2026-09-13 data diagnostic established exploration feasibility under
documented caveats. Formal research promotion controls remain prerequisites for
formal claims, not universal blockers for the initial visibly limited Demo v0.

## Immediate Blockers Or Owner Decisions

- Current task authorization is strictly for documentation, roadmap, and log
  alignment; the owner explicitly directs STOP after this documentation task
  and its version/QA checks.
- Running or interpreting local CSV market data requires separate explicit
  authorization and real-data readiness audit.
- No push, PR creation, merge, or external action without explicit authorization.

## Next Safe Action

- STOP after completing this documentation/log task, checks, and GitHub version
  management, per explicit owner directive.
- Do not implement Demo v0 or run market data in this task. The coordinator
  handles GitHub publication and eligible tab cleanup.
- Future authorized work will execute Milestone 2 Demo v0 vertical slice under
  single-writer rules.

## Source Routing

- Authority, research-safety invariants, and continuation: `AGENTS.md`.
- Workflow, review, waiting, and stop behavior:
  `docs/codex_long_running_controller.md`.
- Active North Star and demo-first delivery: `docs/north_star.md`.
- Program milestones, Demo v0 criteria, and imperfection backlog:
  `docs/current_roadmap.md`.
- Long-term evidence policy: `docs/research_program_charter.md`.
- Track A protocol and gate semantics:
  `docs/eodhd_sp500_diagnostic_campaign_contract.md` and its preregistrations.
- Historical decisions, validation, and failures: `docs/decision_log.md`,
  `docs/engineering_log.md`, and `docs/troubleshooting_log.md`.
