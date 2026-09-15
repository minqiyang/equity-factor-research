# Current Roadmap

Updated: 2026-09-15 after owner alignment on North Star and demo-first delivery.

Canonical responsibility: program stage sequence, dependency order, gate and
completion criteria, and coarse stage status.

This is the canonical roadmap.

Repository authority is [AGENTS.md](../AGENTS.md), workflow behavior is owned by
the [controller](codex_long_running_controller.md), and the timestamped
operational checkpoint is in the [current handoff](current_handoff.md).

## North Star And Program Scope

The ultimate aspiration of the project is automated stock selection and trading,
pursuing sustainable risk-controlled long-term net returns. Stable profit is an
explicit objective, not a guarantee. Active product aspiration and demo-first
delivery principles are defined in [docs/north_star.md](north_star.md).
The preserved historical [research program charter](research_program_charter.md)
remains formal evidence policy, not an active product delivery blocker.

The research and simulation platform built in this repository is the foundational
first phase—not the final execution product. The repository remains strictly
simulated and non-order-capable; live trading, broker integrations, and order
routing belong to a future, separately authorized private execution system.

The engineering approach is **demo-first**: ship a small, presentable, and
reproducible end-to-end version first, record non-blocking imperfections in a
lightweight backlog, and improve in layers. We avoid blocking a working
demonstration on an ideal pipeline, complete SEC identity proof for every
security, optional ledger/schema coverage, or a broad factor zoo. Minimum
correctness (no-lookahead, explicit transaction costs, sample honesty, full trial
accounting, privacy, and non-execution) is preserved at every layer.

## Primary Milestones

The program follows five primary milestones:

| Milestone | Scope | Status | Deliverable & Evidence Criteria |
| --- | --- | --- | --- |
| **1. Core Research & Synthetic Engine** | Data contracts, signal timing, portfolio accounting, synthetic demos, Track B first checkpoints | **Completed Baseline** | Core loaders, signal execution timing, drift-aware portfolio accounting, synthetic demos, and SQLite ledger first checkpoints (Path A PR #199, Path B PR #200). Historical Track A 14-trial run is REFUSED (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`); preserved as immutable history. 2026-09-13 local diagnostic confirmed exploration feasibility with documented caveats. |
| **2. Demo v0 Working Vertical Slice** | Minimal end-to-end reproducible workflow | **Active Delivery Target** | One reproducible local command using an existing price-only factor and fixed strategy configuration -> simulated selection/holdings -> human-readable comparison report with benchmark, explicit cost/timing, risk, and limitations. Demonstrable on synthetic fixtures without private data; separately approved local-data runs remain exploratory diagnostics. Non-blocking imperfections logged in backlog. |
| **3. Exploratory Multi-Factor & Diagnostics** | Multi-factor combination and data-cleaning layers | **Planned Follow-up** | Layered additions on the working vertical slice: multi-factor combination (e.g., three-factor combination), broader historical windows, and handling data caveats (date gaps, zero-volume segments, adjustment checks). All empirical runs remain explicitly caveated exploratory diagnostics. |
| **4. Formal Research & Strict Lineage Controls** | Full auditability for formal promotion claims | **Future Evidence Gate** | Full point-in-time corporate action reconciliation, survivorship-bias-free universe construction, complete all-trial append-only ledger enforcement, purged/embargoed sample splits, and multiple-testing inference packages. Prerequisite for formal factor promotion; not a blocker for early exploratory demos. |
| **5. Automated Execution & Trading Platform** | Live execution and order management | **Future Separately Authorized Scope** | Distinct future progression: candidate comparison and freezing -> independent reproduction -> forward observation -> separately authorized paper trading -> separately authorized small-capital evaluation -> separately authorized live evaluation. Maintained in a separate execution repository owning pre-trade risk limits, position and cash reconciliation, real-time health monitoring, emergency kill switches, broker connectivity, credentials, and live orders; strictly outside the authority of this research repository. No milestone grants authority and no candidate or strategy model has been validated by this documentation task. |

## Program Position

- Last externally verified protected baseline:
  `e76ddb4efe916b5d733e6b583b05c13b2f3ff85d` (remote `main` following PR #203 merge; post-merge CI verified).
- Historical start and intermediate baselines:
  `c178d16d84a455774bcde73f21a9e3ff39ea7b2c` (historical CCA1 start baseline);
  `425b7c88a6e049b63aa2ddeae8560fea08fda23e` (historical PR #200 merge).
- Working clone baseline:
  `e76ddb4efe916b5d733e6b583b05c13b2f3ff85d`.
- PR #180 and PR #181 are merged. No pull request was open at the verified
  start of this work.
- Remote `main` at `e76ddb4efe916b5d733e6b583b05c13b2f3ff85d` incorporates the
  Pearson IC golden fixture fix (`26785bf`) and post-merge CI as historical
  software evidence, without erasing the unre-reviewed golden-fix gap or B2
  advisories.
- Track A PR 1 is complete through PR #177: the EODHD diagnostic scope,
  three-factor protocol, and exact 14-semantic-trial inventory are frozen.
- Governance source convergence and the subsequent handoff and lifecycle work
  are complete through PR #181. They changed no campaign protocol, research
  runtime, private data, or empirical conclusion.
- Stage 1 (private entitlement, retention, and publication) is accepted.
  The public-safe record is `docs/stage1_accepted_public_record_v1.json`.
- The evidence ceiling remains `DIAGNOSTIC_ONLY`. A blinded dataset-review
  decision of `diagnostic_only` exists and campaign acceptance is
  `DIAGNOSTIC_READY`, bound by hash. Formal interpretation is not accepted.
- Track A PR 2 public validator and status are on protected main through
  PR #186. Track A PR 3 runner code is on protected main through PR #187.
- Stage 4 G-2 binding is accepted by hash. Stage 4 is not fully complete.
  14-trial remains REFUSED, reason ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL.
  Terminal refusal is disposition, not Stage 4 / PR 4 completion;
  Stage 4 incomplete; DIAGNOSTIC_ONLY.
- Path A first checkpoint merged as PR #199; Path B first checkpoint merged
  as PR #200. These are first checkpoints only; optional 37-event schema
  completion stays off the critical path.
- A local 2026-09-13 metadata and numerical diagnostic is complete and indicates
  sufficient local data history for exploration, with documented caveats
  (zero-volume segments, date gaps, unverified adjustment events) deferred for
  layered handling. No new strategy run or profitability evidence was produced.
- D8, A2, identity reopen, result/performance access stay closed.
- No private paths, tickers, prices, or performance values in public docs.
- The 2025-05-01 through 2026-05-31 interval remains permanently
  `historical_evaluation`, never a pristine holdout.

## Active Delivery Target: Demo v0 Definition of Done

The first delivery target is deliberately narrow:
1. **Single Command/Workflow**: One reproducible local command/workflow using an
   existing price-only factor and one fixed strategy configuration.
2. **End-to-End Simulation**: Generates simulated selection and holdings with
   drift-aware portfolio accounting.
3. **Transparent Reporting**: Produces a human-readable comparison report with
   benchmark comparisons, explicit frictional cost and timing models, risk
   metrics, and stated limitations.
4. **Complete Trial Accounting**: Records all attempted cases in a reproducible log.
5. **Demonstrable on Synthetic Fixtures**: Runnable without requiring private data.
   Any separately authorized local-data run remains explicitly exploratory.

Additional factors or multi-factor combinations are deferred until this vertical
slice is working and presentable.

## Imperfection Policy And Lightweight Backlog

Imperfections are handled under an explicit classification to avoid blocking
delivery while maintaining research validity:
- **Safe to defer**: Presentation polish, extra factors/markets, optional schema
  breadth, advanced statistics beyond demo claims, and full SEC identity proof
  (provided the actual claimed calculation remains valid without fabricating economics).
- **Non-deferrable (Demo-blocking)**: Identity mis-stitching and ticker reuse,
  future-membership selection and survivorship, silent fill/clip/drop/repair,
  default last-price or zero-payoff disappearance, dividend double counting,
  incompatible price/volume dollar turnover, lookahead leakage or timing mismatch,
  incorrect cost/return math, falsified or cherry-picked results, unhedged/leaked
  private data, and live execution or brokerage integration. A known defect is not
  made safe merely by adding a caveat.

| Item | Category | Impact | Current Handling / Limitation | Revisit Trigger | Status |
| --- | --- | --- | --- | --- | --- |
| Complete SEC entity lineage & symbol aliasing | Data Lineage | Incomplete corporate action / alias history | Disclose symbol alias risk and lack of full historical CIK/FIGI mapping; do not silently join across permanent securities; do not select on future continuity or survivor cohorts | Milestone 4 formal lineage promotion | Safe to defer for Demo v0 (provided no identity mis-stitching occurs) |
| Zero-volume & unchanging price segments | Data Quality | Potential stale prices or illiquid periods | Log caveats in diagnostic reports; do not silently drop, interpolate, or clip missing or zero-volume bars; adhere to explicit dollar-volume conventions if filtering | Milestone 3 data cleaning layer | Safe to defer with explicit caveated reporting (no silent repair) |
| Dividend/split event-level reconciliation | Adjustments | Documented adjustments not reconciled against independent raw events | Use vendor-provided adjusted series as exploratory input with documented uncertainty; strictly forbid adding cash dividends on top of total-return series | Milestone 3/4 corporate action pipeline | Safe to defer for demo; cannot claim audited point-in-time adjustment |
| Factor zoo expansion (10+ factors, multi-factor models) | Features | Single price-only factor used in initial slice | Focus on end-to-end vertical flow with one existing factor (e.g., momentum) | Milestone 3 after Demo v0 vertical slice stabilizes | Safe to defer; demo-first requires 1 working factor first |
| Full 37-event ledger schema runtime coverage | Audit Ledger | Only epoch, registration, and first checkpoints implemented | Use existing SQLite Path A/B or lightweight run logger with explicit diagnostic ceiling | Milestone 4 formal ledger completion | Safe to defer for Demo v0 |
| Advanced multiple-testing statistics | Statistics | Deflated Sharpe / Family-Wise Error Rate not computed | Rely on basic Sharpe, turnover, max drawdown, benchmark relative return | Milestone 4 formal research promotion | Safe to defer; metrics must state descriptive limitations |
| Plotting and visual dashboard generation | Presentation | Text and markdown/JSON output only | Generate clean, human-readable terminal and Markdown comparison reports | Post-v0 visualization polish | Safe to defer |
| Identity mis-stitching & ticker reuse (PIT-005) | Lineage Correctness | Spurious continuity across distinct permanent securities | Must fail closed on ticker reassignment; never stitch returns across permanent securities | Never deferrable | **BLOCKING (Cannot Defer)** |
| Future-membership selection & survivorship (PIT-005) | Sample Honesty | Severe upward performance bias from hindsight selection | Must not select universe on future listing continuity, future index membership, or survivor cohorts | Never deferrable | **BLOCKING (Cannot Defer)** |
| Silent fill, clip, drop, or data repair (PIT-009) | Data Honesty | Fabricated price history or distorted returns | Must fail closed or explicitly preserve missingness; never silently forward-fill, interpolate, clip, or drop bad bars | Never deferrable | **BLOCKING (Cannot Defer)** |
| Disappearance & delisting payoffs (PIT-006) | Economic Correctness | Unrealistic liquidation economics | Must not default to last-price exit or zero payoff at asset disappearance; terminal payoffs must have accepted evidence | Never deferrable | **BLOCKING (Cannot Defer)** |
| Dividend double counting (PIT-007) | Return Correctness | Double-counted total returns | Must not add cash dividends on top of already adjusted return series; corporate action adjustments must be consistent | Never deferrable | **BLOCKING (Cannot Defer)** |
| Incompatible price/volume dollar turnover | Accounting Correctness | Distorted liquidity, sizing, or capacity | Must not multiply raw price with split-adjusted volume or vice-versa; must use compatible price and volume bases | Never deferrable | **BLOCKING (Cannot Defer)** |
| Lookahead leakage or timing mismatch | Timing Correctness | Invalidates all backtest validity | Must enforce accepted `after_close_signal_next_observed_close_v1` timing contract (signals computed strictly after close, earliest target reset at next observed close; no same-bar or open execution without separate typed contract); no lookahead | Never deferrable | **BLOCKING (Cannot Defer)** |
| Frictional cost and turnover accounting | Accounting Correctness | Phantom profitability from ignored trading fees | Must apply explicit transaction costs (bid-ask spread and commission bps) to turnover computed from portfolio trades under existing turnover conventions (sum of absolute signed trades under undivided convention) | Never deferrable | **BLOCKING (Cannot Defer)** |
| Brokerage connection & live execution | Safety/Authority | Unsafe order placement, real-money risk | Strictly prohibited in research repo; simulated portfolio only | Future execution repo (Milestone 5) | **PROHIBITED IN CURRENT REPO** |

## Canonical Research Sources

- [North Star and demo-first delivery](north_star.md): active product aspiration
  and demo-first delivery principles.
- [Research program charter](research_program_charter.md): preserved historical
  formal evidence policy and evidence-state boundaries.
- [Track A/Track B campaign contract](eodhd_sp500_diagnostic_campaign_contract.md):
  scope, private-data gate, freeze sequence, and historical stop conditions.
- [Canonical preregistration](preregistrations/eodhd_sp500_three_factor_diagnostic_v1.yaml)
  and [trial inventory](preregistrations/eodhd_sp500_three_factor_trial_inventory_v1.json):
  frozen historical protocol and exactly 14 semantic trials.
- [Point-in-time methodology contract](point_in_time_data_methodology_contract.md):
  dataset review and formal-interpretation requirements.
- [Repository map](repo_map.md): accepted timing, split, ledger, and schema
  contracts without duplicating their semantics here.
- [Decision log](decision_log.md), [engineering log](engineering_log.md), and
  [troubleshooting log](troubleshooting_log.md): historical evidence, not queues.
- [Stage 1 public-safe record](stage1_accepted_public_record_v1.json),
  [identity-evidence aggregates](identity_evidence_public_aggregate_v1.json),
  and [Track A PR 2 public status](track_a_pr2_public_status_v1.json):
  hashes and counts only.

## Active Dependency Chain

This section records the preserved protocol sequence of the historical Track A/Track B
diagnostic campaign (PR 2/3/4 refusal, Track B first checkpoints PR #199/PR #200). It
provides historical protocol context, not prerequisites for Demo v0. The active product
delivery queue is governed by the Primary Milestones above, with Milestone 2 (Demo v0
Working Vertical Slice) as the active delivery target.

| Order | Stage | Status | Dependency or completion criterion |
| --- | --- | --- | --- |
| 1 | Private entitlement, retention, and publication gate | Accepted 2026-08-22 | Accepted private capability and written-term record exists; public-safe hashes are in `docs/stage1_accepted_public_record_v1.json`. |
| 2 | Track A PR 2: dataset manifest and validation | Public validator on main; campaign `DIAGNOSTIC_READY`; formal interpretation not granted | Complete for the diagnostic track with validator, safe projection, freeze hashes, blinded `diagnostic_only` review, and `DIAGNOSTIC_READY` hashes. |
| 3 | Track A PR 3: bounded diagnostic runner | Code on main via PR #187 | Complete when shippable runner code and synthetic golden fixtures satisfy the binding PR 3 acceptance criteria. Does not include a 14-trial run. |
| 4 | Detached pre-run binding | G-2 accepted; 14-trial remains REFUSED | Complete only when exact code, configuration, environment, protocol, inventory, and accepted dataset identities are bound outside the repository. G-2 is accepted by hash; 14-trial remains REFUSED, reason ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL. Terminal refusal is disposition, not Stage 4 / PR 4 completion; Stage 4 incomplete; DIAGNOSTIC_ONLY. |
| 5 | Track A PR 4: frozen diagnostic evidence | Terminal disposition; 14-trial remains REFUSED | Terminal refusal is disposition, not Stage 4 / PR 4 completion; Stage 4 incomplete; DIAGNOSTIC_ONLY. The 14-trial run remains REFUSED and did not execute. |
| 6 | Track B minimal formal evidence runtime | Path A/B first checkpoints merged | Path A first checkpoint merged as PR #199. Path B first checkpoint merged as PR #200. Evidence ceiling remains `DIAGNOSTIC_ONLY`. First checkpoints only; optional 37-event completion stays off the critical path. |

## Parallel Dataset-Independent Protocol-Core Lane

Frozen protocol-core modules may be implemented in parallel with the owner-side
EODHD gate only when all three conditions hold:

- The exact computation is already frozen in the accepted campaign artifacts.
- A committed golden fixture exists for that computation.
- The work requires no dataset-specific input or result access.

This lane is neither Track A PR 2 nor Track A PR 3. Track A PR 2 and PR 3
keep exclusive ownership of starting, satisfying, and unblocking those
stages. The frozen protocol, preregistration, and 14-trial inventory stay as
already accepted.
The lane implements frozen golden-backed protocol-core modules that already
have committed fixtures. Later stages own:

- ingestion;
- security-master construction;
- historical membership;
- alias lineage;
- terminal/delisting-return semantics;
- decision-time eligibility;
- benchmark-membership construction;
- runner orchestration;
- private-data access;
- result-bearing execution.

## Binding Track A PR 3 Acceptance Criteria

Track A PR 3 must satisfy all of the following:

- Committed golden fixtures execute against shippable runner code rather than
  test-local closures.
- Each frozen factor ID maps to exactly one explicit implementation validated
  by its golden and anchor-mutation fixtures.
- Generic helper defaults never define campaign semantics.
- The factor-matched equal-weight benchmark is canonical and strict: it uses no
  fill, interpolation, or survivor renormalization, and invalid comparisons are
  retained and routed under the frozen contract.

## Gate Completion Criteria

Stage 1 is accepted. Track A PR 2 public surfaces and campaign
`DIAGNOSTIC_READY` hashes are recorded under `DIAGNOSTIC_ONLY`. Track A PR 3
runner code is on protected main. Stage 4 G-2 binding is accepted by hash.
The 14-trial run is REFUSED for
`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`. Evidence ceiling
remains `DIAGNOSTIC_ONLY`. Terminal refusal is not Stage 4 / PR 4 completion.
Path A first checkpoint is merged as PR #199. Path B first checkpoint is
merged as PR #200. The handoff owns the timestamped operational checkpoint.

This section defines dependency and completion state only. It grants no
authority and adds no vendor, data, publication, or interpretation rule beyond
the linked canonical sources.

## Deferred And Out Of Scope

Optional 37-event completion and factor-zoo stay off the critical path.
Broad factor-zoo expansion, formal statistics, strategy promotion, independent
cross-provider replication, LEAN parity, and completion of the remaining 26
optional ledger event schemas are outside the active queue. Broad empirical
expansion and formal factor promotion belong to Milestones 3 and 4, whereas the
active delivery target is Demo v0 (synthetic-first, with separately authorized
exploratory local-data diagnostics under the existing audit protocol); no
unauthorized data access or live execution is authorized here. Real-money
trading, brokerage connectivity, live orders, and paper trading belong strictly
to a future, separately authorized private execution repository and are permanently
out of scope for this repository.

Authority and execution remain in [AGENTS.md](../AGENTS.md) and the
[controller](codex_long_running_controller.md). The latest checkpoint is in
the [handoff](current_handoff.md).
