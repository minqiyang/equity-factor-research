# Current Roadmap Gap Refresh

Date: 2026-06-12

This checkpoint refreshes the repository roadmap after PR #102 merged the post
precomputed volume-aware slippage checkpoint and after the latest `main`
description update. It reconciles the older roadmap with the current
implementation so the next PR-sized stage does not duplicate completed work.

It is documentation only. It does not modify source code, tests, research
scripts, generated reports, strategy logic, backtester behavior, metrics, data
access, execution assumptions, or performance claims. It does not fetch real
data, download data, add vendor APIs, add credentials, add live trading, add
paper trading, add brokerage integration, add order execution, or claim
profitability.

## 1. Review Baseline

Current synced state before this checkpoint:

```text
Branch reviewed: main
HEAD reviewed: 91c2fc9 Update project description in README
Latest merged staged PR reviewed: PR #102, [codex] Add post precomputed slippage checkpoint
Open pull requests before branch creation: none
```

Validation before creating this checkpoint:

```text
python -m pytest -q
488 passed

python -m compileall src tests research
passed
```

## 2. Why The Prior Roadmap Is Stale

The previous `docs/current_roadmap_gap_refresh.md` was written after PR #46.
It correctly routed the project toward validation splits and synthetic
diagnostic discipline, but many of those stages are now complete.

Since then, the repository has added or refreshed:

| Area | Current evidence | Current status |
| --- | --- | --- |
| Train/validation/test split helper | `src/features/validation.py`, `tests/test_validation.py` | Implemented and tested on synthetic/local panels. |
| Split-aware IC / Rank IC demo | `research/synthetic_split_ic_rank_ic_demo.py`, `tests/test_synthetic_split_ic_rank_ic_demo.py` | Implemented as synthetic diagnostics only; no committed generated report/log is present for this demo. |
| Local fixture split metadata | `research/local_csv_fixture_workflow_demo.py`, `reports/local_csv_fixture_workflow_demo.md`, `reports/experiment_logs/local_csv_fixture_workflow_demo.json` | Implemented for committed synthetic fixture workflow only. |
| OHLCV/local CSV readiness path | `docs/volume_ohlcv_schema_plan.md`, `src/data/csv_loader.py`, `tests/test_csv_loader.py`, `tests/fixtures/local_csv_loader_smoke/` | Planned and implemented for strict local fixture loading, not real-data interpretation. |
| Alpha#012 and volume/close smoke coverage | `docs/volume_close_alpha_plan.md`, `src/features/worldquant_alphas.py`, `tests/test_worldquant_alphas.py`, `research/local_csv_fixture_workflow_demo.py` | Implemented as feature and fixture diagnostics only. |
| Liquidity eligibility and universe-mask sequence | `docs/liquidity_dollar_volume_universe_plan.md`, `docs/liquidity_universe_construction_design.md`, `docs/liquidity_universe_backtest_integration_design.md`, `src/features/liquidity.py`, `tests/test_liquidity.py`, `tests/test_liquidity_masked_signal_smoke.py`, `tests/test_liquidity_masked_signal_backtest_smoke.py` | Implemented through synthetic/local-panel helpers and smoke tests. |
| Fixed-bps transaction cost and slippage accounting | `docs/simulated_slippage_cost_assumption_design.md`, `src/backtest/portfolio.py`, `src/backtest/metrics.py`, `tests/test_backtest_portfolio.py`, synthetic reports/logs | Implemented and refreshed for synthetic backtests. |
| Volume-aware slippage diagnostic and precomputed-impact path | `docs/volume_aware_slippage_design.md`, `src/backtest/slippage.py`, `docs/volume_aware_slippage_backtester_integration_design.md`, `docs/volume_aware_slippage_backtester_integration_test_plan.md`, `src/backtest/portfolio.py`, `tests/test_volume_aware_slippage.py`, `tests/test_backtest_portfolio.py` | Implemented with `diagnostic_only` default and explicit precomputed-impact opt-in. |
| Synthetic generated-log refresh for volume-aware metric | `reports/experiment_logs/synthetic_momentum_demo.json`, `reports/experiment_logs/synthetic_combined_score_backtest_demo.json` | Refreshed with `total_volume_aware_slippage_cost_impact: 0.0` in default diagnostic mode. |
| LEAN planning and non-executing scaffold path | `lean/README.md`, `lean/smoke_test_algorithm.py`, `lean/signal_only_momentum_draft.py`, `tests/test_lean_*`, `docs/lean_*` | Still non-executing and signal-only by design. |

## 3. Current Implementation Traceability

| Goal area | Current implementation | Evidence files | Remaining gap |
| --- | --- | --- | --- |
| Auditable governance | Agent rules, project spec, controller, staged workflow Skill, engineering/decision/troubleshooting logs, changelog, and handoff. | `AGENTS.md`, `PROJECT_SPEC.md`, `docs/codex_long_running_controller.md`, `.agents/skills/staged-quant-workflow/SKILL.md`, `docs/engineering_log.md`, `docs/decision_log.md`, `docs/troubleshooting_log.md`, `CHANGELOG.md`, `docs/current_handoff.md` | Keep handoff and roadmap current after each staged merge. |
| Factor features | Momentum, reversal, volatility, liquidity, alpha#009, and alpha#012 research features exist. | `src/features/momentum.py`, `src/features/reversal.py`, `src/features/volatility.py`, `src/features/liquidity.py`, `src/features/worldquant_alphas.py`, tests under `tests/` | Additional factors remain future work; no bulk WorldQuant implementation. |
| Factor preprocessing and diagnostics | Normalization, winsorization, factor combination, correlation diagnostics, IC, Rank IC, quantile spread, and split helpers exist. | `src/features/normalize.py`, `src/features/combine.py`, `src/features/diagnostics.py`, `src/features/validation.py`, related tests | Robustness and parameter-sensitivity policy is not yet documented for split-aware research runs. |
| Local CSV path | Strict local CSV loader, inventory review, committed synthetic fixtures, and fixture workflow demos exist. | `src/data/csv_loader.py`, `src/data/local_csv_inventory.py`, `tests/fixtures/local_csv_loader_smoke/`, `research/local_csv_fixture_workflow_demo.py` | No user-provided local CSV bundle has passed readiness/provenance/alignment review. |
| Experiment records and reports | Synthetic JSON sidecar logs, registry, and caveated Markdown reports exist. | `src/reporting/experiment_log.py`, `src/reporting/experiment_registry.py`, `reports/experiment_logs/`, `reports/experiment_registry.md` | Real-data experiment records remain blocked; robustness summaries need a documented policy before expansion. |
| Simulated backtesting | Long-only local backtester includes benchmark, costs, fixed-bps slippage, turnover, and optional precomputed volume-aware impact. | `src/backtest/portfolio.py`, `src/backtest/metrics.py`, `src/backtest/slippage.py`, `tests/test_backtest_portfolio.py`, `tests/test_volume_aware_slippage.py` | No real-data benchmark/universe study; volume-aware capacity remains synthetic/local-fixture only. |
| LEAN path | Non-executing scaffold and pure-Python signal-only metadata draft exist. | `lean/README.md`, `lean/smoke_test_algorithm.py`, `lean/signal_only_momentum_draft.py`, `tests/test_lean_*` | Runnable LEAN, live trading, paper trading, brokerage, and order execution remain blocked. |

## 4. Remaining Gaps Toward The Original Goal

The original goal is still not achieved. The repository has strong synthetic
and local-fixture infrastructure, but it does not yet contain real-market
evidence that any factor is a verifiable stock-selection signal.

Remaining gaps:

- No user-provided local CSV research study has been run under the readiness
  audit, provenance, schema, survivorship, benchmark, and experiment-log gates.
- No real-data IC, Rank IC, quantile spread, benchmark-relative, or
  train/validation/test interpretation has been completed.
- No real benchmark, point-in-time universe, liquidity universe, or adjustment
  policy has been accepted for a user-provided dataset.
- No real-data volume, participation, capacity, or market-impact conclusion
  exists.
- No documented robustness and parameter-sensitivity policy exists for
  split-aware synthetic or local-fixture research runs.
- Generated reports and experiment logs remain synthetic diagnostics or
  committed-fixture smoke checks, not investment evidence.
- LEAN work remains non-executing and must not imply live, paper, brokerage,
  or order-execution readiness.

## 5. Guardrail Review

Current guardrail status:

| Guardrail | Finding |
| --- | --- |
| No real data fetching | Satisfied. Data use is synthetic or committed fixture only. |
| No vendor downloads | Satisfied. No `requests`, `yfinance`, Alpaca, CCXT, or API-download path is part of the workflow. |
| No credentials | Satisfied. No credential, token, account, or environment-secret path is part of the workflow. |
| No live trading or paper trading | Satisfied. Mentions are prohibitions, caveats, or static tests. |
| No brokerage or order execution | Satisfied. LEAN artifacts are non-executing; backtester behavior is simulated research accounting only. |
| No profitability claims | Satisfied. Current reports and logs frame results as synthetic diagnostics or local-fixture smoke checks only. |
| No bulk WorldQuant 101 implementation | Satisfied. Only alpha#009 and alpha#012 are implemented as research features. |

## 6. Recommended Next Roadmap

The next stages should improve validation discipline and robustness reporting
without touching real data or execution systems.

| Stage | Purpose | Expected files | Tests/checks | Stop condition |
| --- | --- | --- | --- | --- |
| Synthetic robustness and split-aware validation plan | Define how future synthetic/local-fixture research should report train/validation/test splits, parameter sensitivity, all-case reporting, benchmark assumptions, cost/slippage assumptions, and no-best-only filtering before new implementation. | `docs/synthetic_robustness_validation_plan.md`, `docs/current_handoff.md`, `docs/engineering_log.md`, `docs/decision_log.md`, `CHANGELOG.md`, `docs/repo_map.md` if regenerated | `python -m pytest -q`; `python -m compileall src tests research`; `python scripts/repo_map.py`; `git diff --check origin/main..HEAD`; Skill audit if workflow files change | Stop if the stage requires real data, external APIs, performance interpretation, or code behavior changes. |
| Synthetic split-aware robustness implementation | Only after the plan is reviewed, add deterministic synthetic summaries that report all configured cases across split windows without selecting winners. | Likely `research/`, `tests/`, and generated outputs only if explicitly scoped | Focused tests, full baseline, generated-output diff review | Stop if outputs imply strategy validation or profitability. |
| Local fixture robustness/report refresh | If synthetic robustness implementation merges, apply the reviewed summary format to committed local fixtures only. | Fixture workflow, tests, reports/logs if scoped | Focused workflow tests, full baseline, output review | Stop if a user-provided dataset is required. |
| User-provided local CSV readiness run | Only when a user explicitly provides dataset scope, run the readiness audit before interpretation. | Readiness audit artifacts and experiment handoff only | Readiness checks defined by the project Skill | Stop for missing provenance, schema ambiguity, survivorship ambiguity, benchmark ambiguity, credentials, vendor APIs, or profitability framing. |

## 7. Final Recommendation

The next PR-sized stage after this roadmap refresh merges should be:

```text
Synthetic robustness and split-aware validation plan
```

Reason:

- The repository now has split helpers, synthetic diagnostics, local fixture
  demos, backtest accounting, fixed-bps cost/slippage, and a precomputed
  volume-aware slippage boundary.
- The next original-goal gap is not another metric field by default; it is a
  reviewed policy for how to evaluate robustness without cherry-picking or
  implying real-data validation.
- A documentation-only plan is safer than implementation because it can define
  all-case reporting, split windows, benchmark assumptions, transaction-cost
  assumptions, slippage assumptions, and stop conditions before any new
  research script or generated-output change.

The next stage should remain synthetic/local-fixture only and should not fetch
data, use vendor APIs, add credentials, add live or paper trading, add
brokerage/order logic, or claim profitability.
