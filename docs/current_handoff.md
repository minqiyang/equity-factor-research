# Current Handoff

Updated: 2026-10-02 for the O-16 owner report correction after PR #287.

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
  `d48b8114700ffd3555b8177bdbc829c598636c8d` (main after PR #287).
- This publication began from that baseline. Its live PR and merge state
  must be checked separately after publication.
- Merged through PR #275: M4.0 local real-data diagnostic through M4.7 (PIT universe, registrations v1 and v2 on
  real_v1, `extend_first`), M4.7 support v2, and M4.8 Stages A–D (partition rule v2 and seal carry, causal engines
  and terminal schema v3, membership curation with gate G1 passed, private snapshot `real_v2`), and North Star
  v2 (PR #276: factor-class allocator, owner process constraints, M4.8 paused, Milestone 5 active), and the
  controller review rules (PR #263: `MATERIAL` or `ADVISORY` findings, two review rounds, short plain PR text),
  and Milestone 5 steps 1 and 2 (PR #277: trial file and two amendments, 1,160-row factor catalog, and the R1
  inverse-volatility baseline on public factor data, `DIAGNOSTIC_ONLY`), and the CI speed change (PR #278: four
  parallel test lanes, one shared runner v3 run, about 10 minutes per PR), and Milestone 5 step 3 (PR #279: state
  tilt, factor momentum tilt, and pooled ridge against R1; closure open, no state-timing claim), and Milestone 5
  step 4 (PR #280: price classes on `real_v2`; R0 is the point-in-time baseline, R2 closes, fragile), and
  Milestone 5 step 4b (PR #281: SEC as-filed Value and Quality classes on `real_v2`; they do not join), and the
  step 4 live report check (PR #282: RETRO-GPT-01, test-only, and the PR #281 merge-gate incident), and the
  Milestone 5 owner report (PR #283: O-11 defers step 5; O-12 rules out a seal-window look and forward observation),
  and the post-review commit merge rule (PR #284), and the triggered ablation rule (PR #285: O-13), and the
  AGENTS.md simplification with the ablation rule removed (PR #286: O-14), and the Simplified Technical English
  writing target (PR #287: O-15).
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88` (PR #200), `e76ddb4e` (PR #203), `770cfe54` (PR #260), `49eacdd4` (PR #261),
  `2c07ee4d` (PR #262), `76a0e43a` (PR #264), `de3172bc` (PR #265), `d15ef1d4` (PR #266),
  `45fe5adc` (PR #267), `0d87d7eb` (PR #268), `a9c94dca` (PR #269), `e4662859` (PR #270),
  `dcf7b86a` (PR #271), `bfdca57a` (PR #272), `f416af8c` (PR #273), `1c56939b` (PR #274), and
  `9dee2df2` (PR #275), `5b74d35a` (PR #276), `23b1c734` (PR #263), `edbd34c3` (PR #277), `cb77a4e8` (PR #278),
  `e6d04cdf` (PR #279), `c7d2d8da` (PR #280), `03e06b53` (PR #281), `e36a4a28` (PR #282), `4f7d7096` (PR #283),
  `f6cfc610` (PR #284), `988b4443` (PR #285), `2f93032d` (PR #286), and `d48b8114` (PR #287).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`); preserved history.
- This candidate adds no raw private data, provider response, provider-derived membership list, security code, or
  private path.

## Recorded Delivery Scope

- Candidate branch `claude/m5-report-correction` records owner decision O-16. Docs only; no code, data, or result
  changes. `reports/m5_owner_report.md` gets the exact headline, its limits, and the three step 6 advisories; the
  roadmap step 6 line follows.
  - `AGENTS.md`: one Writing Style line, "Write at about 80% of ASD-STE100 (Simplified Technical English)."
  - The O-15 decision and engineering log entries, and a wording fix to the O-14 entry (advisory O14-R1-A2).

## Current Research Gate Summary

See `docs/current_roadmap.md` for milestone status. Milestone 5 steps 1 to 4b are merged; step 5 is deferred
(O-11); the step 6 owner report is merged (PR #283). On point-in-time books R0 over the four price classes is the
baseline, and it trails SPY and the equal-weight book. M4.8 stays paused after Stage D, and the seal window remains
unaccessed and reserved (O-12).

## Immediate Blockers Or Owner Decisions

- None blocks the R0 freeze. The Milestone 5 ablation patches are dropped (O-13); the ablation rule is removed (O-14).
- Before any further online SEC run: the redirect handling of the SEC client (GPT-S4BD-A2, OPUS-S4B-D-04).
- Carried to the M4.8 resume point: nine Stage D advisories and the M-2 disposition of 10 discrepancy lines.
- Owner items carried: the iCloud sync of the private data root (A2-D-ADV-6); the Stage C Wikipedia request that
  sent the owner's account email in its user agent (engineering log, c2 entry); the registration v2 validator
  accepting a cash completion after the calendar end (A2-05).
- Owner: the next line of work after Milestone 5 (O-12: decided after the report). Forward observation and a
  factor-ETF benchmark need a new owner decision on data and money.

## Next Safe Action

- The dated R0 freeze with two formal review seats; it pins no seal or forward look (O-12).

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
