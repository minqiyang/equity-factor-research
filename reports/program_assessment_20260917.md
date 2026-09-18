# Program Assessment: 2026-09-17

The project has delivered a reproducible synthetic research demonstration and
eight Milestone 3 increments. The next useful increment is a bounded synthetic
split proof through both demo pipelines. Economic reconciliation against
independent corporate-action evidence remains open.

This assessment describes source HEAD
`1a3cee50b2fa508f86d605d2cb9adb178f5f0263` on
`codex/astra-max-next-roadmap-20260917`. Local `main` and the cached
`origin/main` reference both resolve to that SHA. Local first-parent history
contains the merges listed below; live GitHub state was outside this analysis.
[The current roadmap](../docs/current_roadmap.md) retains canonical ownership
of milestones, gates, and the imperfection backlog. The companion
[proposed next steps](../docs/proposed_next_steps_roadmap.md) supply a suggested
sequence after M3-08.

## Purpose and evidence ceiling

[The North Star](../docs/north_star.md) is automated stock selection and
trading pursuing sustainable, risk-controlled long-term net returns. Profit
is an aspiration with uncertain outcomes. This repository supplies the
simulated research foundation: deterministic inputs, inspectable signals,
portfolio accounting, benchmark comparisons, and retained evidence.

Delivery proceeds in working layers. Demo v0 supplies the presentable vertical
slice; exploratory diagnostics add narrowly tested capabilities; formal
research requires stronger data, trial, and statistical evidence. A future
execution system occupies a separately authorized private repository.
[AGENTS.md](../AGENTS.md) owns the research-safety boundaries, and the
[charter](../docs/research_program_charter.md) preserves the formal evidence
policy. Their minimum correctness requirements apply throughout delivery.

The current evidence supports synthetic software behavior and limited
diagnostics. Both official configurations use 10 bps transaction costs and
zero slippage. Zero-slippage and zero-cost results retain a diagnostic
ceiling. Empirical profitability, validated stock-selection value, formal
promotion, and trading readiness remain unestablished.

## Progress against the five primary milestones

| Milestone | Assessment at source HEAD | Delivered evidence and remaining boundary |
| --- | --- | --- |
| 1. Core Research & Synthetic Engine | Completed baseline under the canonical milestone criteria. | Strict loaders, factor helpers, timing/provenance contracts, drift-aware accounting, synthetic workflows, and Track B Path A/B first checkpoints exist. Path A PR #199 and Path B PR #200 are in local main history. Complete trial/access closure and all 37 event schemas remain future work. |
| 2. Demo v0 Working Vertical Slice | Implemented and run on synthetic fixtures. | `python -m research.demo_v0` produces selection, holdings, a comparison report, and All-Attempt Case Logging. PR #206 delivered the command. Its frozen configuration remains intact through M3-08. |
| 3. Exploratory Multi-Factor & Diagnostics | In progress; M3-01 through M3-08 are implemented. | M3-01 adds an artificial three-factor backtest; subsequent increments cover invalid bars, observed-row lag, dividend-overlay refusal, longer synthetic windows, unchanging-price counts, wall-time spans, and supplied-event date membership. Independent event economics and data-specific reconciliation remain open. |
| 4. Formal Research & Strict Lineage Controls | Future evidence gate with contracts and partial runtime foundations. | Methodology, timing, split, and ledger contracts exist. Formal promotion still requires accepted dataset evidence, point-in-time identity/membership and corporate actions, complete trial/access accounting, applicable purged splits, cost/capacity evidence, and registered statistical controls. |
| 5. Automated Execution & Trading Platform | Future separately authorized scope. | The research repository remains simulated. Candidate freezing, independent reproduction, forward observation, and separately authorized execution evaluations belong to later gates; the private execution repository would own broker connectivity, orders, risk limits, reconciliation, monitoring, and kill switches. |

Milestone 3 delivery advances the exploratory program while preserving the
formal evidence requirements of Milestone 4.

## Delivered stages in local main history

The entries below describe the merged behavior, with
[CHANGELOG.md](../CHANGELOG.md), the recent
[engineering entries](../docs/engineering_log.md), and the source/tests as
supporting evidence.

| Delivery | Merge evidence | Scope delivered |
| --- | --- | --- |
| Demo v0 | PR #206, `0dd4bcd` | Existing 12-1 momentum, long-only backtesting, human-readable comparison, and retained invocation outcomes. |
| M3-01 | PR #208, `3e757a2` | Artificial momentum/quality/reversal panels combined with weights 0.50/0.30/0.20 after existing winsorization and z-score normalization; backtest and attempt logging reuse existing infrastructure. |
| M3-02 | PR #209, `35afcf8` | Complete finite positive price bars; supplied volume must also be finite and positive. Invalid input receives refusal and retained failure evidence. The local CSV loader's separate zero-volume policy remains unchanged. |
| M3-03 | PR #210, `b8b7233` | Signal lag counts observed source rows on gapped input. Missing observations remain omitted; every supplied observation stays in place. |
| M3-04 | PR #211, `e611338` | Held returns use the supplied price ratio; separate cash-dividend overlays are refused under PIT-007. |
| M3-05 | PR #215, `4d1d589` | Tests run both pipelines on 1512 synthetic rows through `dataclasses.replace`; official commands retain 756 rows. |
| M3-06 | PR #216, `e7098e6` | Reports count consecutive equal-price runs of length at least two, affected assets, and maximum run length. Bars remain intact; these counts establish observed equality only. |
| M3-07 | PR #217, `e033e9d` | Reports disclose adjacent calendar-day spans; exact declared-source checks refuse inserted, dropped, or reordered source rows. Exchange sessions and holidays remain unverified. |
| M3-08 | PR #218, `1a3cee5` | Optional event tables receive exact timestamp membership checks. Repeated dates and empty typed tables pass. Values remain opaque metadata; both default reports disclose absent independent event evidence. |

M3-08 supplies a consistency guard. Its `event_table` carries no accepted
amount, ratio, identity, revision, or return-construction contract. The
[M3-08 attempt report](m3_08_attempt.md) records 21 new cases and a historical
full-suite result of 2888 passed, two platform skips, and one constant-input
correlation warning. Those counts describe the earlier implementation check.

## What the working demos show

Demo v0 uses seed 20260521, 20 assets, 756 rows starting 2021-01-01, starting
price 100, momentum lookback 252 with skip 21, month-end (`ME`) rebalancing,
top five equal-weight targets, 10 bps transaction costs, zero slippage, and
252 periods per year. Its close-derived signals use
`after_close_signal_next_observed_close_v1`: availability follows the signal
close, target reset occurs at the next observed source-row close, and the new
holdings first earn the following close-to-close return. Turnover is the
undivided sum of absolute signed trades against drifted pre-trade weights.
Costs apply to post-return portfolio value under the existing accounting.

M3-01 reuses the same synthetic price fixture and backtester, with artificial
factor seed 20260528 and 0.05/0.95 winsorization quantiles. Its three panels
represent generated test scores. They provide combination and alignment
evidence; real fundamental availability and factor validity remain later
research questions.

Both commands have already run on synthetic fixtures. Each committed attempt
log retains success records for attempts 1 through 5. Demo v0 has nine records
(four starts and five successes); M3-01 has ten (five starts and five
successes). Demo v0's earliest success predates the start-record fix, and those
historical bytes remain preserved. Current failure/interruption behavior is
covered by runner tests and the start-before-computation implementation.

| Committed synthetic report | Evaluation dates | Strategy total return | Synthetic benchmark total return | Excess total return |
| --- | --- | ---: | ---: | ---: |
| [Demo v0](demo_v0.md) | 2021-12-21 to 2023-11-24 | -7.91% | 9.85% | -17.75% |
| [M3-01](synthetic_multifactor_backtest_demo.md) | 2021-01-01 to 2023-11-24 | 24.03% | 28.16% | -4.14% |

These values reproduce the committed reports, including negative evidence.
The evaluation windows differ, so the rows serve as separate reproduction
checks. Each benchmark is the synthetic equal-weight universe series and is
cost-free. Both reports disclose zero slippage, synthetic-only inputs, and
missing real-market coverage. Neither fixture supplies a sealed empirical
holdout. The official reports record zero unchanging-price segments, 151
adjacent timestamp pairs spanning more than one day, a maximum span of three
days, and absent independent event tables.

## Remaining work and source freshness

The main technical gap is economic evidence for supplied price adjustments.
Date membership and overlay refusal preserve useful boundaries, while split
ratios, dividend amounts, event identity, knowability, and revision lineage
still require a separately scoped comparison. The repository already contains
a split golden and a campaign-path test that expose raw-price contamination.
Extending that accepted example through the two demo consumers is the first
proposed proof slice.

The main documentation gap is checkpoint freshness.
`docs/current_handoff.md` still records the PR #203 baseline and Milestone 2
as the active target. The roadmap's Program Position also retains that older
baseline, while its primary table and M3-08 entries describe later delivery.
The concrete consequence is stale resume guidance. A later authorized
checkpoint refresh should bind its claims to its then-current source HEAD and
preserve historical entries. This assessment leaves those canonical files
unchanged and identifies the discrepancy for the next implementer.

The longer-window proof expands synthetic coverage. It establishes behavior
on 1512 generated rows; empirical history, exchange-calendar validity, and
corporate-action completeness retain their existing evidence requirements.
Presentation polish, extra factors, optional ledger breadth, and advanced
statistics remain off the immediate demonstration path under the canonical
backlog.

## Non-goals and closed gates

| Boundary | Current disposition |
| --- | --- |
| Private/local market data and vendor access | Access, outcome interpretation, and publication each require their applicable explicit scope, methodology, privacy, and readiness gates. This task uses repository evidence and synthetic fixtures. |
| Historical Track A 14-trial campaign | Execution remains `REFUSED` with `ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`; ceiling `DIAGNOSTIC_ONLY`. The real 14-trial run did not execute. D8, A2, identity reopen, and private result/performance access stay closed. |
| Formal research claims | Accepted contracts and passing synthetic tests supply software evidence. Factor/strategy/portfolio promotion requires the complete applicable Milestone 4 evidence package. |
| Previously examined sample | 2025-05-01 through 2026-05-31 remains `historical_evaluation`; its classification is permanently exposed. |
| Identity and disappearance | PIT-005 requires fail-closed identity joins; PIT-006 blocks affected windows lacking accepted terminal evidence. These remain mandatory before affected calculations. |
| Returns, liquidity, and timing | PIT-007 prevents dividend double counting and incompatible price/volume bases. Accepted timing, explicit costs, decision-time membership, and PIT-009 typed missingness remain mandatory. |
| Evidence retention | Failed, invalid, interrupted, weak, and negative evidence stays visible. Lightweight demo logging has a diagnostic scope; formal trial/access completeness remains a separate requirement. |
| Brokerage and execution | Orders, broker connections, credentials, paper/live trading, and execution-capable behavior remain outside this repository. |
| This delivery | Three English guidance/attempt files, the required generated-map count refresh, and one local commit define the scope. Product code, canonical roadmap edits, external publication, and worktree changes are excluded. |

## File map for the next implementer

The first group establishes the task boundary; the second supports the first
proof slice; the final group supports later gated work. Each path is relative
to the Git root.

| Path | One-line role |
| --- | --- |
| [AGENTS.md](../AGENTS.md) | Repository authority, research-safety invariants, writing rules, and required ablation. |
| [docs/north_star.md](../docs/north_star.md) | Active product aspiration and demo-first delivery policy. |
| [docs/current_roadmap.md](../docs/current_roadmap.md) | Canonical milestones, completion criteria, and imperfection backlog. |
| [docs/current_handoff.md](../docs/current_handoff.md) | Timestamped operational checkpoint whose older facts require revalidation. |
| [docs/codex_long_running_controller.md](../docs/codex_long_running_controller.md) | Validation, stop, and authorized lifecycle gates. |
| [docs/research_program_charter.md](../docs/research_program_charter.md) | Preserved formal evidence and promotion policy. |
| [PROJECT_SPEC.md](../PROJECT_SPEC.md) | Research contract, timing, sample classification, and scope. |
| [README.md](../README.md) | Official commands, legacy command distinctions, and environment setup. |
| [docs/repo_map.md](../docs/repo_map.md) | Generated orientation and contract routing. |
| [docs/proposed_next_steps_roadmap.md](../docs/proposed_next_steps_roadmap.md) | Suggested bounded sequence and acceptance gates after M3-08. |
| [research/demo_v0.py](../research/demo_v0.py) | Frozen official configuration, single-factor pipeline, reporting, and attempt logging. |
| [research/synthetic_momentum_demo.py](../research/synthetic_momentum_demo.py) | Existing config type, synthetic price generator, and equal-weight benchmark helper. |
| [research/synthetic_multifactor_backtest_demo.py](../research/synthetic_multifactor_backtest_demo.py) | M3-01 frozen config, artificial-factor pipeline, reporting, and attempt logging. |
| [research/dividend_policy.py](../research/dividend_policy.py) | Supplied-price return convention, cash-overlay refusal, and event-date membership. |
| [research/bar_integrity.py](../research/bar_integrity.py) | Complete positive price/volume validation used by both demos. |
| [research/source_row_lag.py](../research/source_row_lag.py) | Observed-row lag, exact source preservation, and wall-time span reporting. |
| [research/unchanging_price.py](../research/unchanging_price.py) | Equal-price segment counts with input preservation. |
| [src/backtest/portfolio.py](../src/backtest/portfolio.py) | Existing timing, provenance, holdings, turnover, cost, and return engine. |
| [src/backtest/metrics.py](../src/backtest/metrics.py) | Existing metric conventions used by comparison reports. |
| [tests/fixtures/campaign_runner_v1/split_corporate_action.json](../tests/fixtures/campaign_runner_v1/split_corporate_action.json) | Accepted synthetic adjusted-price split golden and forbidden raw-price outcomes. |
| [tests/test_campaign_paths.py](../tests/test_campaign_paths.py) | Existing split golden binding to campaign holdings and cost calculations. |
| [src/campaign/returns.py](../src/campaign/returns.py) | Existing identity-bound adjusted-close ratio gate for reference. |
| [tests/test_campaign_returns.py](../tests/test_campaign_returns.py) | Return-anchor, identity binding, and invalid-input reference tests. |
| [tests/test_dividend_policy.py](../tests/test_dividend_policy.py) | PIT-007 overlay refusal and supplied-series return proofs. |
| [tests/test_event_date_membership.py](../tests/test_event_date_membership.py) | Both-runner event membership, preservation, logging, and disclosure coverage. |
| [tests/test_demo_v0.py](../tests/test_demo_v0.py) | Frozen Demo v0 config, timing, invalid bars, reporting, and attempt outcomes. |
| [tests/test_synthetic_multifactor_backtest_demo.py](../tests/test_synthetic_multifactor_backtest_demo.py) | M3-01 combination, alignment, timing, reporting, and attempt outcomes. |
| [tests/test_bar_integrity.py](../tests/test_bar_integrity.py) | Complete-bar and supplied-volume refusal regression coverage. |
| [tests/test_source_row_lag.py](../tests/test_source_row_lag.py) | Source-index preservation and observed-row lag regression coverage. |
| [tests/test_calendar_day_spans.py](../tests/test_calendar_day_spans.py) | Span counts and declared-source checks across both demos. |
| [tests/test_broader_windows.py](../tests/test_broader_windows.py) | 1512-row proof and unchanged official 756-row configuration. |
| [tests/test_unchanging_price.py](../tests/test_unchanging_price.py) | Equal-price counts and input-preservation regression coverage. |
| [tests/test_backtest_timing_contract.py](../tests/test_backtest_timing_contract.py) | Timing, bounds, source provenance, and metric-window regressions. |
| [tests/test_official_report_paths.py](../tests/test_official_report_paths.py) | Repository-relative official attempt-log paths. |
| [reports/demo_v0.md](demo_v0.md) | Committed official single-factor synthetic comparison. |
| [reports/demo_v0_attempts.jsonl](demo_v0_attempts.jsonl) | Preserved Demo v0 invocation outcomes. |
| [reports/synthetic_multifactor_backtest_demo.md](synthetic_multifactor_backtest_demo.md) | Committed M3-01 synthetic comparison. |
| [reports/synthetic_multifactor_backtest_demo_attempts.jsonl](synthetic_multifactor_backtest_demo_attempts.jsonl) | Preserved M3-01 invocation outcomes. |
| [reports/m3_08_attempt.md](m3_08_attempt.md) | Exact M3-08 scope, validation, ablation, and remaining gap. |
| [docs/engineering_log.md](../docs/engineering_log.md) | Dated implementation and process evidence; start with M3-06 through M3-08. |
| [CHANGELOG.md](../CHANGELOG.md) | User-visible delivered changes. |
| [EXPERIMENT_LOG.md](../EXPERIMENT_LOG.md) | Diagnostic retention policy and requirements for later authorized local-data studies. |
| [.github/workflows/ci.yml](../.github/workflows/ci.yml) | Canonical existing validation commands. |
| [pyproject.toml](../pyproject.toml) | Python, dependency, package, and test configuration. |
| [docs/point_in_time_data_methodology_contract.md](../docs/point_in_time_data_methodology_contract.md) | Event evidence, identity, field bases, missingness, privacy, and dataset-review gates. |
| [docs/signal_execution_timing_contract.md](../docs/signal_execution_timing_contract.md) | Accepted signal, execution, and return-window semantics for later event design. |
| [docs/real_data_readiness_audit.md](../docs/real_data_readiness_audit.md) | Later separately authorized local-data readiness evidence checklist. |

This map routes work to existing owners and the smallest relevant source set.
