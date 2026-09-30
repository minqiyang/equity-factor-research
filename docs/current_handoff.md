# Current Handoff

Updated: 2026-09-30 for Milestone 5 step 4b (SEC as-filed value and quality classes on point-in-time books).

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
  `c7d2d8da101c0788f3295b7d2676b8561c32f9c7` (main after PR #280).
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
  step 4 (PR #280: price classes on `real_v2`; R0 is the point-in-time baseline, R2 closes, fragile).
- Historical baselines: `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (CCA1 start),
  `425b7c88` (PR #200), `e76ddb4e` (PR #203), `770cfe54` (PR #260), `49eacdd4` (PR #261),
  `2c07ee4d` (PR #262), `76a0e43a` (PR #264), `de3172bc` (PR #265), `d15ef1d4` (PR #266),
  `45fe5adc` (PR #267), `0d87d7eb` (PR #268), `a9c94dca` (PR #269), `e4662859` (PR #270),
  `dcf7b86a` (PR #271), `bfdca57a` (PR #272), `f416af8c` (PR #273), `1c56939b` (PR #274), and
  `9dee2df2` (PR #275), `5b74d35a` (PR #276), `23b1c734` (PR #263), `edbd34c3` (PR #277), `cb77a4e8` (PR #278),
  `e6d04cdf` (PR #279), and `c7d2d8da` (PR #280).
- PR #180 is merged. PR #181 is merged at `12e280d9afa2f23aa2850b13a08f7e8447c4b89e`.
  No pull request was open at the verified start of the CCA1 correction work.
- Historical Track A 14-trial run remains REFUSED
  (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`); preserved history.
- This candidate adds no raw private data, provider response, provider-derived membership list, security code, or
  private path.

## Recorded Delivery Scope

- Candidate branch `claude/m5-step4b` delivers Milestone 5 step 4b on the private `real_v2` snapshot and a local
  SEC companyfacts cache, under owner decisions O-5 and O-9 as extended to step 4b and O-10 (SEC EDGAR access),
  at `DIAGNOSTIC_ONLY`.
  - SEC data build (`src/data/sec_edgar.py`, `research/m5_sec_identity.py`, `research/m5_step4b_data.py`, code
    `7560b4a`): fail-closed rule F maps 563 of 632 eligible IDs to one CIK; two-seat review `MATERIAL: 0`, and the
    map and hash list reproduced offline. The map and raw files stay local; the manifest holds hashes only.
  - Amendment 5 revision 2 (SHA-256 `a712188c...`) was committed alone before any step 4b code or result and
    passed two rounds of GPT and Opus review with `MATERIAL: 0`.
  - `research/m5_sec_signals.py` implements the as-filed rule (first-filed 10-K values, no amendment or older-year
    fallback, 18-month staleness, 15 typed missing reasons) for BM_AF, EP_AF, and GP_AT_AF; `research/m5_step4b.py`
    runs them beside the six step 4 sleeves, recomputes step 4, and runs S4b.ADD (BY family 481).
    `tests/test_m5_step4b.py` has 35 tests.
  - Code review round 1 at `27133b9`: `MATERIAL: 0` from both seats; each reran the full run and matched the JSON.
    The five report advisories were fixed in the renderer; the JSON is unchanged.
- Result (`reports/m5_step4b.md`): the SEC classes do not join. R0 over nine sleeves meets 2 of 8 conditions
  against the six-sleeve R0 (the two post Sharpe conditions); S4b.ADD +0.051 percent a month, HAC p 0.42, BY q 1;
  not fragile, not coverage-tilted, last-close rerun 2 of 8. GP_AT_AF ranks about 55 percent of member-days
  because the frozen COGS chain excludes filers without a cost-of-revenue line.
- Records: the engineering-log entry, the implementation readings in the decision log, and the step 4b data-build
  and runner advisories in the roadmap backlog.

## Current Research Gate Summary

See `docs/current_roadmap.md` for milestone status. Milestone 5 steps 1 to 4b are delivered on this candidate. On
point-in-time books, R0 over the four price classes is the baseline product; the return-timing line through R2 is
closed, and the SEC Value and Quality classes do not join. M4.8 stays paused after Stage D, and the seal window
remains unaccessed.

## Immediate Blockers Or Owner Decisions

- None blocks step 5.
- Before any further online SEC run: the redirect handling of the SEC client (GPT-S4BD-A2, OPUS-S4B-D-04).
- Carried to the M4.8 resume point: nine Stage D advisories and the M-2 disposition of 10 discrepancy lines.
- Owner items carried: the iCloud sync of the private data root (A2-D-ADV-6); the Stage C Wikipedia request that
  sent the owner's account email in its user agent (engineering log, c2 entry); the registration v2 validator
  accepting a cash completion after the calendar end (A2-05); a factor-ETF return source, if wanted.
- Open for the first stock-level confirmation design: whether to spend the seal window.

## Next Safe Action

- Step 5 (discovery) per `docs/current_roadmap.md`: freeze its trial amendment before any step 5 result, on the
  four-price-class R0 baseline.

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
