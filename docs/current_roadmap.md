# Current Roadmap

Updated: 2026-09-28 after the owner's North Star v2 decision (M4.8 paused after Stage D; Milestone 5 redefined as the factor-class allocator).

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

This repository is the foundational research and simulation phase. It stays
strictly simulated and non-order-capable; live trading, broker integrations,
and order routing belong to a future, separately authorized private execution
system.

The engineering approach is **demo-first**: ship a small, presentable, and
reproducible end-to-end version first, record non-blocking imperfections in a
lightweight backlog, and improve in layers. The core question is which factors
earn more, or lose less, in which market conditions. Minimum correctness is the
invariant set R1–R12 in
[AGENTS.md Research Safety Invariants](../AGENTS.md#research-safety-invariants),
enforced at every layer; the [blocking backlog rows](#imperfection-policy-and-lightweight-backlog)
record each invariant's implementation status.

## Primary Milestones

The program follows six primary milestones:

| Milestone | Scope | Status | Deliverable & Evidence Criteria |
| --- | --- | --- | --- |
| **1. Core Research & Synthetic Engine** | Data contracts, signal timing, portfolio accounting, synthetic demos, Track B first checkpoints | **Completed Baseline** | Core loaders, signal execution timing, drift-aware portfolio accounting, synthetic demos, and SQLite ledger first checkpoints (Path A PR #199, Path B PR #200). Historical Track A 14-trial run is REFUSED (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`, `DIAGNOSTIC_ONLY`); preserved as immutable history. 2026-09-13 local diagnostic provided qualitative feasibility/planning context with documented caveats (outside Demo v0 acceptance; no tradability, universe-completeness, or holdout claim). |
| **2. Demo v0 Working Vertical Slice** | Minimal end-to-end reproducible workflow | **Implemented (synthetic fixtures)** | Official command `python -m research.demo_v0` reuses existing 12-1 momentum and frozen `SyntheticDemoConfig` values -> simulated selection/holdings -> human-readable comparison report with benchmark, explicit cost/timing, risk, and limitations; All-Attempt Case Logging records successes and failures. Synthetic fixtures only; no profitability claim; no private data. `python -m research.synthetic_momentum_demo` remains a legacy diagnostic. Separately approved local-data runs remain exploratory diagnostics. Non-blocking imperfections stay in the backlog. |
| **3. Exploratory Multi-Factor & Diagnostics** | Multi-factor combination and data-cleaning layers | **Completed exploratory layer (M3-01 through M3-08, M3.9 regime composite, M3.10 hardening)** | M3.9 adds 52 WorldQuant-101 alphas with composite, neutralization, weighting, turnover-penalty, and regime layers; M3.10 resolves the M01–M11 causality and accounting audit. M3-01 command `python -m research.synthetic_multifactor_backtest_demo` reuses Demo v0 synthetic prices, existing combine/normalize helpers, and the Demo v0 backtester with All-Attempt Case Logging. M3-02 requires complete finite strictly positive price bars in Demo v0 and the M3-01 demo, and refuses a supplied zero-volume or missing volume panel without silent fill, clip, drop, or repair. M3-03 proves those demos count signal lag in observed source rows; a missing source row remains an omitted observation. Those demos keep the supplied observed index. M3-07 reports adjacent calendar-day spans and refuses panel timestamps absent from the declared source index. Official demos declare the generated price index as source. Session and holiday status remains unverified. M3-04 proves those demos compute held returns from the supplied price series only and refuse a separate cash-dividend overlay (PIT-007). M3-05 proves those demos run on a longer synthetic panel of length `2 * DEMO_V0_CONFIG.periods` (1512) through `dataclasses.replace`; official frozen `DEMO_V0_CONFIG` remains 756 rows. M3-06 counts unchanging-price segments on those demos and keeps every supplied bar. M3-08 implements supplied-event date membership and explicit no-table disclosure. Full economic dividend/split reconciliation against independent events remains deferred to a separately scoped Milestone 3/4 slice. All empirical runs remain explicitly caveated exploratory diagnostics. |
| **4. Formal Research & Strict Lineage Controls** | Real-data point-in-time research engine and registered reruns | **Diagnostic layer M4.0–M4.7 merged; M4.8 paused after Stage D (PR #275)** | M4.0 local 50-name real-data diagnostic; M4.1 walk-forward ML combination; M4.2 purged and embargoed CPCV; M4.3 multiple-testing diagnostics; M4.4 point-in-time membership and terminal cash; M4.5 optional square-root impact; M4.6 style risk attribution; M4.7 S&P 500 point-in-time universe with registered reruns on real_v1 (PR #268, PR #269, PR #271), gate outcome `extend_first` (holdout sealed). M4.8 Stages A–D merged (PR #272–#275, snapshot `real_v2` built); Stages E–H paused by owner decision on 2026-09-28 because the registered gate cannot reach the 0.02 power floor. Resume point: Stage E on `real_v2`. |
| **5. Factor-Class Allocator** | Collect many factors into classes; learn which classes earn more or lose less in real-time market conditions; monthly class allocation turned into a long-only large-cap portfolio; counted discovery of new factors | **Active (next)** | Factor catalog seeded from public libraries and broker formulas; risk-balanced all-class baseline and pre-declared timing questions on long public factor-return histories (French, AQR, JKP, Open Source Asset Pricing, Hou–Xue–Zhang) with FRED condition series; value and quality classes from SEC as-filed data; bridge to long-only point-in-time S&P 500 portfolios with costs on the local snapshots; counted discovery judged against random mining. Success test: net return and maximum drawdown against SPY, a cheap factor-ETF blend, and the risk-balanced baseline, in both halves and after publication, with BY across each declared family. Simulation only (R12). |
| **6. Automated Execution & Trading Platform** | Live execution and order management | **Future Separately Authorized Scope** | Distinct future progression: candidate comparison and freezing -> independent reproduction -> forward observation -> separately authorized paper trading -> separately authorized small-capital evaluation -> separately authorized live evaluation. Maintained in a separate execution repository owning pre-trade risk limits, position and cash reconciliation, real-time health monitoring, emergency kill switches, broker connectivity, credentials, and live orders; strictly outside the authority of this research repository. No milestone grants authority and no candidate or strategy model has been validated by this documentation task. |

## Program Position

- Current checkpoint: merged through PR #275 (M4.8 Stage D, `9dee2df`). On 2026-09-28 the owner adopted
  North Star v2, paused M4.8 after Stage D, authorized public academic factor libraries and FRED series, chose
  SEC as-filed financial data for fundamentals, and kept the local EODHD snapshots (`real_v1`, `real_v2`) as the
  stock-level data without renewing the subscription. Milestone 5 is the active delivery target. Assessments:
  `coord/reports/progress_assessment_opus.md` and `coord/reports/north_star_speed_audit_opus.md`.
- Current checkpoint: merged through PR #269 (M4.7c-1). M4.0–M4.2 ran on the local
  static 50-name survivor cohort; M4.3–M4.6 carry synthetic evidence only.
  Milestone 4.7 completes the first S&P 500 point-in-time universe rerun on
  snapshot `real_v1` under preregistration `6ea218a6…1c9f` with 0 Class I stops.
  The deterministic gate evaluates to `extend_first` (power inadequate, 0 BY
  rejections in Family A or Family B, PBO >= 0.50, holdout partition sealed).
- Support v2 (owner correction, branch `claude/breadth-support-isolation-fix`): asset-level
  holding-period isolation replaces the global gap-window schedule. Registration v2 (`4a6f8b5a…e7dc`)
  on real_v1 evaluates all 61 resets and 60 IC months at 424-433 names per reset; Family A MDE_f
  0.0437-0.1293; outcome stays `extend_first`.
- The following earlier program-position entries preserve the Stage 2/M3
  checkpoint and historical research evidence.
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
- The evidence ceiling remains `DIAGNOSTIC_ONLY`. Under historical Track A,
  a blinded dataset-review decision of `diagnostic_only` exists and campaign
  acceptance is `DIAGNOSTIC_READY`, bound by hash. Formal interpretation is not accepted.
- Track A PR 2 public validator and status are on protected main through
  PR #186. Track A PR 3 runner code is on protected main through PR #187.
- Under historical Track A, Stage 4 G-2 binding is accepted by hash;
  historical Track A Stage 4 is not fully complete.
- Historical Track A 14-trial execution remains REFUSED (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`).
  Terminal refusal is disposition, not Track A Stage 4 / PR 4 completion;
  Track A Stage 4 incomplete; DIAGNOSTIC_ONLY.
- Path A first checkpoint merged as PR #199; Path B first checkpoint merged
  as PR #200. These are first checkpoints only; optional 37-event schema
  completion stays off the critical path.
- A local 2026-09-13 metadata and numerical diagnostic provided qualitative feasibility
  and planning context on local data history, with documented caveats (zero-volume segments,
  date gaps, unverified adjustment events) deferred for layered handling. It is outside
  Demo v0 acceptance, produces no strategy or profitability claims, and does not prove
  tradability, universe completeness, or a pristine holdout.
- D8, A2, identity reopen, and historical Track A 14-trial private result/performance access stay closed; this historical gate does not restrict synthetic Demo v0 diagnostic comparison reports.
- Public docs follow invariant R11 and the owner's written data terms:
  noncommercial aggregates may be public; raw provider rows, provider
  responses, provider-derived membership lists, credentials, and private paths
  stay private.
- The 2025-05-01 through 2026-05-31 interval remains permanently
  `historical_evaluation`, never a pristine holdout.
- Demo v0 is implemented as the synthetic vertical slice:
  `python -m research.demo_v0` using existing 12-1 momentum and frozen
  `SyntheticDemoConfig` values, with All-Attempt Case Logging. No profitability
  claim. No private data. `python -m research.synthetic_momentum_demo` remains
  a legacy diagnostic.
- M3-01 is implemented as `python -m research.synthetic_multifactor_backtest_demo`
  on Demo v0 synthetic price dates and assets, using existing combine/normalize
  helpers and the Demo v0 backtester. The three panels are artificial quality,
  reversal, and momentum fixtures. `python -m research.synthetic_multifactor_workflow_demo`
  remains the feature-only workflow. M3-02 adds fail-closed missing-bar and
  zero-volume refusal for those two demos. M3-03 proves signal lag counts
  observed source rows on those commands. M3-04 proves those commands compute
  held returns from the supplied price series only and refuse a separate
  cash-dividend overlay. M3-05 proves those commands run on a longer
  synthetic panel of length `2 * DEMO_V0_CONFIG.periods` (1512) through
  `dataclasses.replace`; official frozen `DEMO_V0_CONFIG` remains 756 rows.
  M3-06 counts unchanging-price segments on those commands and keeps every
  supplied bar. M3-07 reports adjacent calendar-day spans and refuses panel
  timestamps absent from the declared source index. Official demos declare
  the generated price index as source. M3-08 implements supplied-event date
  membership and explicit no-table disclosure. Full economic dividend/split
  reconciliation against independent events remains deferred to a separately
  scoped Milestone 3/4 slice.

## Active Delivery Target: Demo v0 Definition of Done

The first delivery target is deliberately narrow:
1. **Single Command/Workflow**: One reproducible local command/workflow using an
   existing price-only factor and one fixed strategy configuration.
2. **End-to-End Simulation**: Generates simulated selection and holdings with
   drift-aware portfolio accounting.
3. **Transparent Reporting**: Produces a human-readable comparison report with
   benchmark comparisons, explicit frictional cost and timing models, risk
   metrics, and stated limitations.
4. **All-Attempt Case Logging**: Records all attempted cases in a reproducible log (all-attempt logging is mandatory; cherry-picking or omitting failed trials is strictly forbidden; distinguishes lightweight diagnostic run logging from formal experiment/trial-ledger accounting required by charter Stage 4 / Milestone 4).
5. **Demonstrable on Synthetic Fixtures**: Runnable without requiring private data.
   Any separately authorized local-data run remains explicitly exploratory.

The official synthetic command is `python -m research.demo_v0`. The M3-01
exploratory command is `python -m research.synthetic_multifactor_backtest_demo`.
M3-02 is the missing-bar and zero-volume refusal layer for those commands.
M3-03 proves signal lag counts observed source rows; a missing source row
remains an omitted observation. Those demos keep the supplied observed index.
M3-07 reports adjacent calendar-day spans and refuses panel timestamps absent
from the declared source index. Official demos declare the generated price
index as source. Session and holiday status remains unverified.
M3-04 proves those demos compute held returns from the supplied price series
only and refuse a separate cash-dividend overlay (PIT-007).
M3-05 proves those demos run on a longer synthetic panel of length
`2 * DEMO_V0_CONFIG.periods` (1512) through `dataclasses.replace`; official
frozen `DEMO_V0_CONFIG` remains 756 rows.
M3-06 counts unchanging-price segments on those demos and keeps every
supplied bar.
M3-08 implements supplied-event date membership and explicit no-table disclosure. Full economic dividend/split reconciliation against independent events remains deferred to a separately scoped Milestone 3/4 slice.

## Milestone 4.7: Survivorship-Reduced Universe And Pre-Registered Rerun (Completed)

Milestone 4.7 is completed. All seven stages (pre-flight audit, data retrieval module,
universe build, delisting exits and terminal tooling, coverage census, registration freeze,
and point-in-time rerun on real_v1) were implemented, audited with dual independent reviews
(MATERIAL: 0), and merged through PR #269. The rerun executed with exit 0 and zero Class I stops.
The deterministic gate evaluates to `extend_first` (power inadequate, zero BY rejections across
Family A and Family B, PBO >= 0.50). The holdout window remains sealed and unaccessed.
Evidence ceiling remains `DIAGNOSTIC_ONLY`.

1. **Pre-flight audit.** Completed (PR #257, PR #262).
2. **Data.** Retrieval module implemented in `src/data/eodhd_retrieval.py` and
   `src/data/holdout_partition.py` (PR #264).
3. **Universe.** S&P 500 PIT membership intervals, permanent IDs, and
   `resolve_pit_universe_mask` implemented in `research/m4_7_universe_build.py` (PR #265, PR #267).
4. **Exits.** Delisting consideration types, terminal valuation, and corporate-action
   attribution implemented in `research/m4_7_terminal_evidence.py` (PR #265, PR #267).
5. **Census.** Coverage census and accepted shortfall bounds implemented in
   `research/m4_7_coverage_census.py` (PR #265, PR #267).
6. **Pre-registration.** Frozen in `docs/preregistrations/m4_7_sp500_pit_rerun_v1.json`
   (SHA-256 `6ea218a6…1c9f`) binding upstream digests, Owner Decisions O-1, O-3, O-6, O-7, O-8 (PR #268).
7. **Rerun and gate.** Executed on snapshot `real_v1` with 0 Class I stops, BY corrections,
   and deterministic decision gate outcome `extend_first` (PR #269).
8. **Support v2 (owner correction).** Asset-level holding-period isolation
   (`asset_level_holding_period_support_exclusion_v1`) replaces the v1 gap windows and segments. A missing
   bar or unevidenced delisting excludes only the affected asset-period (27 cells of 26,237 on real_v1).
   Registration v2 restores 60 IC months (v1: 32) and 424-433 evaluated names per reset; MDE_f
   0.0437-0.1293 stays above 0.02, so the outcome stays `extend_first`. v1 artifacts remain unchanged.

## Milestone 4.8: Paused After Stage D

Stages A–D are merged (PR #272–#275): partition rule v2 with the carried seal, causal engines with locked capital
and terminal schema v3, curated point-in-time membership with gate G1 passed (`D0_pre` 2014-04-30, 62 pre-segment
IC months), and the private snapshot `real_v2`. The owner paused Stages E–H on 2026-09-28: at 122 IC months the
Family A minimum detectable effect is 0.031–0.091 against the 0.02 floor, so the registered gate would return
`extend_first` again. The resume point is Stage E on `real_v2`; the nine Stage D advisories and the M-2 disposition
carry to that point. The seal window stays unaccessed.

## Milestone 5: Factor-Class Allocator (Active)

Design basis: `coord/reports/north_star_vision_assessment_opus.md`.

Status 2026-09-29: steps 1 and 2 are delivered. The trial file and amendments 1 and 2 are in
`docs/preregistrations/`, the catalog has 1,160 rows, and the declared rule picks R1 (inverse volatility) as the
baseline product (`reports/m5_factor_baseline.md`, `DIAGNOSTIC_ONLY`). Step 3 is next.

1. **Trial file and catalog.** A hashed trial file committed before any repository result: at most 3 real-time
   states (12-month market trend, 63-day realized volatility, lagged credit spread) with fixed thresholds, at most
   6 traits and 5 rules, baselines of equal weight, inverse volatility, and the market; the 2026-09-28 audit and
   probe runs count as trials already seen. One factor catalog (id, source, formula or reference, inputs, horizon,
   status) seeded from Open Source Asset Pricing, JKP, Hou–Xue–Zhang, French, AQR, WorldQuant 101, Guotai Junan 191,
   and Qlib Alpha158; cataloguing needs no review.
2. **Baseline.** Loaders with a SHA-256 manifest for French, JKP (153 factors, 13 themes), and FRED. Walk-forward
   report of equal weight against inverse volatility across themes and factors, at 20 and 50 bp switch costs, both
   halves, post-publication months, maximum drawdown, and volatility-forecast accuracy.
3. **Timing questions.** The declared state tilt and one pooled class-level model, with HAC standard errors, BY
   correction, a random-date null, and the episode count behind each cell. If the tilt loses to the baseline in
   either half, the return-timing line closes as a reported negative result.
4. **Bridge.** Factor classes as long-only top-quintile point-in-time S&P 500 portfolios with costs on the local
   snapshots, price classes first and SEC as-filed value and quality classes next; the report states how much of
   the long-short result survives.
5. **Discovery.** A counted search for new candidates in trait regions that survived, against a random search with
   the same number of candidates and the Open Source Asset Pricing placebo signals as a control.
6. **Owner report and freeze.** A plain-language report, a dated freeze, and forward observation.

## Imperfection Policy And Lightweight Backlog

This is the single authoritative imperfection backlog table for the project.
Presentation polish, extra factors or markets, optional schema breadth, advanced
statistics beyond demo claims, and full SEC identity proof are safe to defer
when the claimed calculation stays valid. Invariants R1–R12 in `AGENTS.md`
never defer; the BLOCKING rows below record each invariant's implementation
status.

| Item | Category | Impact | Current Handling / Limitation | Revisit Trigger | Status |
| --- | --- | --- | --- | --- | --- |
| Complete SEC entity lineage & symbol aliasing | Data Lineage | Incomplete corporate action / alias history | Disclose symbol alias risk and lack of full historical CIK/FIGI mapping; do not silently join across permanent securities; do not select on future continuity or survivor cohorts | Milestone 4 formal lineage promotion | Safe to defer for Demo v0 (provided no identity mis-stitching occurs) |
| Zero-volume & unchanging price segments | Data Quality | Potential stale prices or illiquid periods | Demo v0 and the M3-01 three-factor demo require complete finite strictly positive price bars and refuse a supplied missing or zero-volume panel without silent fill, clip, drop, or repair. The local CSV loader still accepts zero volume as loader-valid. Those demos count unchanging-price segments (consecutive equal prices of length >= 2), assets affected, and max run length. Consecutive equal prices stay in the panel. The backtest uses every supplied bar. | Later local-CSV volume policy or additional data-quality layers after M3-06 | Safe to defer local-CSV zero-volume handling; M3-02 demo refusal and M3-06 unchanging-price reporting are implemented |
| Internal & provider date gaps | Data Quality | Discontinuous trading history or missing calendar sessions across assets | Transparently disclose in diagnostic reports; do not silently insert, fill, or drop bars; accepted next-observed-close contract advances strictly to the next observed source row (lag counts source rows, not calendar days; absence of a source row does not imply a verified calendar non-session, and existing zero-volume or stale rows are never skipped or dropped); scope-relevant unresolved gaps block affected interpretation. Demo v0 and the M3-01 demo now test that lag on a gapped observed index uses the previous source row. Those demos keep the supplied observed index. M3-07 reports adjacent calendar-day spans and refuses panel timestamps absent from the declared source index. Official demos declare the generated price index as source. Session and holiday status remains unverified. | Separately authorized local-data calendar assessment | M3-07 synthetic span reporting and declared-source refusal are implemented; exchange/holiday classification remains unverified; unresolved scope-relevant local-data gaps block affected interpretation |
| Dividend/split event-level reconciliation | Adjustments | Documented adjustments not reconciled against independent raw events | Use vendor-provided adjusted series as exploratory input with documented uncertainty; strictly forbid adding cash dividends on top of total-return series. Demo v0 and the M3-01 demo compute held returns from the supplied price series only and refuse a separate cash-dividend overlay. M3-08 checks each supplied event date against the declared source index and preserves prices. Both official reports state that event-level reconciliation was not performed because no independent event table was supplied. Full economic reconciliation against independent raw events remains deferred. | Milestone 3/4 corporate action pipeline | Safe to defer event-level reconciliation for demo; cannot claim audited point-in-time adjustment; M3-04 overlay refusal and M3-08 event-date membership are implemented |
| Factor collection (catalog and screening families) | Features | 58 price-volume base factors in code; no fundamentals; no public factor library used yet | Milestone 5 builds one catalog from public libraries and broker formulas and screens it in declared exploratory families (R9 two tiers). | Milestone 5 | Active in Milestone 5 |
| Full 37-event ledger schema runtime coverage | Audit Ledger | The Path A/B SQLite runtime retired with the Track A code on 2026-09-23 (history at `8fa0055`); the frozen schema releases remain as data | Diagnostic runs append trial records with sample hash, specification, statistics, and status to a JSONL log. The run's code commit appears once per run in the experiment log and report; JSONL records carry no per-attempt commit, so attempts appended across commits need the run-level record to recover code identity. | A formal ledger requirement from a later milestone, or per-attempt commit binding | Safe to defer; runtime retired; per-attempt commit binding open |
| Multi-factor risk calibration and coverage | Risk attribution | Estimated covariance and omitted residual correlations affect active-risk forecasts | M4.6 implements causal OLS/WLS style attribution and sample rolling covariance on complete synthetic panels. Rank deficiency and enabled terminal-event coverage refuse explicitly. Specific covariance is diagonal; geometric return linking, industries, dynamic regression universes, and empirical calibration remain open. Enabled attribution requires complete static price panels and market capitalization plus book-to-price inputs, which the price-only real-data pipeline lacks. | Milestone 5 stock-level bridge | Implemented diagnostic layer (PR #255); synthetic evidence only |
| Real-data evidence freshness | Evidence | Committed real-data results predate M4.3–M4.6 | M4.7 executes and commits the S&P 500 point-in-time rerun on snapshot real_v1 under owner authorization O-4 with full multiple-testing diagnostics, CPCV/PBO, and excess metrics against SPY and the equal-weight PIT benchmark (PR #269). | M4.7 rerun (PR #269) | Completed in M4.7 (PR #269); DIAGNOSTIC_ONLY |
| Impact-model spread floor | Cost Realism | `SquareRootImpactModel.fixed_bps` defaults to 0, and an active model forces legacy slippage to 0 | The committed capacity demo sets a 2 bps fixed component. A default-constructed model prices small liquid trades near commission only. Spread, commission, and borrow calibration at the owner's scale waits for its first real-data consumer; M4.8 left cost recalibration out of scope. | Milestone 5 stock-level bridge | Deferred to its first real-data consumer |
| Delisting terminal evidence for held securities | Economic Correctness | An unevidenced held delisting refuses the whole run in both engines | Point-in-time universes contain acquired and delisted members. M4.7 implements terminal evidence tooling, validation, and corporate-action attribution (PR #265, PR #267). | M4.7 universe & census | Implemented in M4.7 (PR #265, PR #267) |
| Advanced multiple-testing statistics | Statistics | Multiplicity and adaptive research affect inference | Existing DSR uses run-family Sharpe dispersion. M4.3 adds Bonferroni, Holm, BH and BY over all semantic book trials, primary HAC BY diagnostics, and explicitly conditional IID Sharpe haircuts. Undefined and conflicting trials retain family slots. Historical search completeness, finite-sample HAC calibration, and empirical-population Harvey-Liu simulation remain open. | Stronger formal research claims and accepted historical-family evidence | Implemented diagnostic layer; DIAGNOSTIC_ONLY; formal promotion limits remain |
| Milestone 5 step 3 BY family and prior exposures | Statistics | The 612 factor x state pairs and the T1 and T3 rules seen before the trial freeze overlap step 3 tests; leaving them out of the step 3 BY family size would understate multiplicity (review advisory A2-A2) | Recorded in `docs/decision_log.md` (Milestone 5 trial amendments entry); no step 3 test exists yet | The step 3 v2 amendment, before any step 3 result | Open; the v2 amendment either counts them or states why they fall outside |
| Milestone 5 step 3 R4 coverage | Statistics | Amendment 2 removes not-yet-published factor-months from R4's inputs (65% of the jkp_factors_153 set, 94% in 1972-1999); comparing R4 with baselines on the full set would measure the publication effect (review advisory A2R2-A1) | No step 3 rule or result exists | The step 3 v2 amendment, before any step 3 result | Open; compare on the same factor-month set, keep the R1 weight where R4 has no forecast, or drop the trait; state the 11 no-year factors and the covered share by half |
| Plotting and visual dashboard generation | Presentation | Text and markdown/JSON output only | Generate clean, human-readable terminal and Markdown comparison reports | Post-v0 visualization polish | Safe to defer |
| Support v2 look-ahead exclusion (R1) | Timing / Invariants | Retrospective asset exclusion at r-1 for mid-month missing bar / unevidenced delisting | Confined to 27 cells of 26,237 (0.103%) on real_v1; DIAGNOSTIC_ONLY ceiling; zero ranking/selection/profitability claim; owner-accepted risk | Revisit immediately if any rerun produces a Family A BY survivor, or if excluded fraction exceeds 0.005; expires at next registration freeze | Owner-accepted, expires at next registration freeze |
| Identity mis-stitching & ticker reuse (PIT-005) | Lineage Correctness | Spurious continuity across distinct permanent securities | Must fail closed on ticker reassignment; never stitch returns across permanent securities. M4.4 requires identity-backed interval tables and exact permanent-ID axes in its optional PIT path; synthetic ticker-reassignment tests preserve separate security returns. External identity evidence remains caller-supplied. | Never deferrable | **BLOCKING (Cannot Defer)**; optional runtime enforcement implemented |
| Future-membership selection & survivor-cohort filtering | Sample Honesty | Severe upward performance bias from hindsight selection | Invariant R2: eligibility uses only membership known at decision time. A static survivor cohort is permitted only under `DIAGNOSTIC_ONLY`, with the bias stated in each report header, and never supports ranking, selection, promotion, or profitability claims. M4.7 implements S&P 500 point-in-time membership intervals and resolve_pit_universe_mask executed on real_v1 (PR #267, PR #269). | Never deferrable | **BLOCKING (Cannot Defer)**; point-in-time universe implemented and executed in M4.7 |
| Silent fill, clip, drop, or data repair (PIT-009) | Data Honesty | Fabricated price history or distorted returns | Must fail closed or explicitly preserve missingness; never silently forward-fill, interpolate, clip, or drop bad bars | Never deferrable | **BLOCKING (Cannot Defer)** |
| Disappearance & delisting payoffs (PIT-006) | Economic Correctness | Unrealistic liquidation economics | Accepted terminal evidence settles a held disappearance; otherwise the declared side-aware adverse default of R4 applies (cash acquisition at last close or deal price; failure or unknown at −100% long and last close +30% short, or no long-short claim; same rule for the benchmark; count, weight share, and a last-close-for-all rerun reported). Adopted 2026-09-28; the engines still refuse an unevidenced held disappearance until the default is implemented. M4.4 implements an explicitly supplied complete prior-close-to-cash return, one-time signed cash settlement, and holding clearance in both engines. Missing reference prices, unknown settlement terms, and frozen-target collisions refuse. An unevidenced held disappearance refuses the whole run. Delayed payments, receivable valuation, and stock consideration remain open. | Never deferrable | **BLOCKING (Cannot Defer)**; immediate-cash synthetic accounting implemented |
| Dividend double counting (PIT-007) | Return Correctness | Double-counted total returns | Must not add cash dividends on top of already adjusted return series; corporate action adjustments must be consistent. Demo v0 and the M3-01 demo compute held returns from the supplied price series only and refuse a separate cash-dividend overlay. M3-08 refuses supplied event dates absent from the declared source index. Full economic corporate-action reconciliation remains separately scoped Milestone 3/4 work. | Never deferrable | **BLOCKING (Cannot Defer)**; Demo v0 and M3-01 overlay refusal is implemented |
| Incompatible price/volume dollar turnover | Accounting Correctness | Distorted liquidity, sizing, or capacity | Must not multiply raw price with split-adjusted volume or vice-versa; must use compatible price and volume bases | Never deferrable | **BLOCKING (Cannot Defer)** |
| Lookahead leakage or timing mismatch | Timing Correctness | Invalidates all backtest validity | Must enforce accepted `after_close_signal_next_observed_close_v1` timing contract (signals computed strictly after close, earliest target reset at next observed close; no same-bar or open execution without separate typed contract); no lookahead | Never deferrable | **BLOCKING (Cannot Defer)** |
| Frictional cost and turnover accounting | Accounting Correctness | Phantom profitability from ignored trading fees | Must apply explicit transaction costs (fixed basis points on turnover under existing undivided turnover conventions; sum of absolute signed trades) and explicit slippage assumptions; no zero-cost or frictionless trading claims | Never deferrable | **BLOCKING (Cannot Defer)** |
| Brokerage connection & live execution | Safety/Authority | Unsafe order placement, real-money risk | Strictly prohibited in research repo; simulated portfolio only | Future execution repo (Milestone 6) | **PROHIBITED IN CURRENT REPO** |

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
Working Vertical Slice) implemented as the synthetic vertical slice.

| Order | Stage | Status | Dependency or completion criterion |
| --- | --- | --- | --- |
| 1 | Private entitlement, retention, and publication gate | Accepted 2026-08-22 | Accepted private capability and written-term record exists; public-safe hashes are in `docs/stage1_accepted_public_record_v1.json`. |
| 2 | Track A PR 2: dataset manifest and validation | Public validator on main; campaign `DIAGNOSTIC_READY`; formal interpretation not granted | Complete for the diagnostic track with validator, safe projection, freeze hashes, blinded `diagnostic_only` review, and `DIAGNOSTIC_READY` hashes. |
| 3 | Track A PR 3: bounded diagnostic runner | Code on main via PR #187 | Complete when shippable runner code and synthetic golden fixtures satisfy the binding PR 3 acceptance criteria. Does not include a 14-trial run. |
| 4 | Detached pre-run binding | G-2 accepted; 14-trial remains REFUSED | Complete only when exact code, configuration, environment, protocol, inventory, and accepted dataset identities are bound outside the repository. G-2 is accepted by hash; 14-trial remains REFUSED, reason ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL. Terminal refusal is disposition, not Stage 4 / PR 4 completion; Stage 4 incomplete; DIAGNOSTIC_ONLY. |
| 5 | Track A PR 4: frozen diagnostic evidence | Terminal disposition; 14-trial remains REFUSED | Terminal refusal is disposition, not Stage 4 / PR 4 completion; Stage 4 incomplete; DIAGNOSTIC_ONLY. The 14-trial run remains REFUSED and did not execute. |
| 6 | Track B minimal formal evidence runtime | Path A/B first checkpoints merged | Path A first checkpoint merged as PR #199. Path B first checkpoint merged as PR #200. Evidence ceiling remains `DIAGNOSTIC_ONLY`. First checkpoints only; optional 37-event completion stays off the critical path. |

## Parallel Dataset-Independent Protocol-Core Lane

> **Historical Protocol Context**: This section records preserved historical Track A execution lanes from prior stages, not active prerequisites for Demo v0.

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

> **Historical Protocol Context**: This section records preserved historical Track A acceptance criteria from prior stages, not prerequisites for Demo v0.

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

> **Historical Protocol Context**: This section records preserved historical Track A gate completion criteria from prior stages, not active prerequisites for Demo v0.

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

Optional 37-event completion stays off the critical path. Strategy promotion,
independent cross-provider replication, LEAN parity, and completion of the
remaining 26 optional ledger event schemas are outside the active queue. Factor
collection, the factor-class allocator, and counted discovery belong to Milestone 5. Demo v0 is
the implemented synthetic vertical slice (`python -m research.demo_v0`), with
separately authorized exploratory local-data diagnostics under the existing
audit protocol; no unauthorized data access or live execution is authorized here. Real-money
trading, brokerage connectivity, live orders, and paper trading belong strictly
to a future, separately authorized private execution repository and are permanently
out of scope for this repository.

Authority and execution remain in [AGENTS.md](../AGENTS.md) and the
[controller](codex_long_running_controller.md). The latest checkpoint is in
the [handoff](current_handoff.md).


## M4.5 Impact and Capacity Limitations

The optional model uses lagged complete daily windows and declared compatible
price/volume bases. Its eta and excess-participation penalty are scenario
coefficients. Benchmark-relative capacity remains unresolved on the generated
AUM grid. Empirical estimation requires separately authorized data and evidence.

Partial fills, cash-funded buys, and price drift can change actual exposures
relative to target position caps and long-short neutrality. Residual share queues
remain visible at the final row. The target timing ledger records scheduled
attempts; actual dollar trades record retries on every accounting row. Borrow
fees, short recalls, intraday execution, corporate-action conversion of pending
shares, and vendor basis verification remain explicitly deferred research work.
