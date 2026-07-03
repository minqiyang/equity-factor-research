# Current Roadmap Gap Refresh

Date: 2026-06-23

## Status: Superseded In Part

This roadmap refresh predates the private EODHD validation-only and factor
diagnostics checkpoints. It should no longer be read as saying that no local
CSV bundle has passed validation-only loader/schema checks, or that no private
IC, Rank IC, or quantile-spread diagnostics have been calculated.

The current distinction is:

- Private EODHD validation-only loader/schema checks exist and remain outside
  the repository.
- Private EODHD IC, Rank IC, and quantile-spread diagnostic calculations exist
  through the private diagnostics workflow.
- Broader real-data interpretation remains blocked until point-in-time
  universe policy, adjustment policy, benchmark methodology, sample splits,
  cost/slippage assumptions, experiment-log requirements, and interpretation
  policy are accepted.

This checkpoint refreshes the repository roadmap after the protected PR merge
governance update, the opt-in local fixture configured-case report/log support,
and the committed local fixture configured-case generated-output refresh. It
reconciles the older roadmap with the current implementation so the next
PR-sized stage does not duplicate completed synthetic or local-fixture work.

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
HEAD reviewed: 546784d Merge pull request #115 from minqiyang/codex/local-fixture-configured-output-refresh
Latest merged staged PR reviewed: PR #115, [codex] Refresh local fixture configured-case outputs
Open pull requests before branch creation: none
```

Validation before creating this checkpoint:

```text
.venv/bin/python -m pytest -q
503 passed

.venv/bin/python -m compileall src tests research
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
| Synthetic split-aware robustness sequence | `docs/synthetic_robustness_validation_plan.md`, `research/synthetic_split_robustness_demo.py`, `tests/test_synthetic_split_robustness_demo.py`, `reports/synthetic_split_robustness_demo.md`, `reports/experiment_logs/synthetic_split_robustness_demo.json` | Completed through plan, implementation, opt-in output support, and generated-output refresh. |
| Local fixture configured-case robustness sequence | `docs/local_fixture_robustness_report_refresh_plan.md`, `research/local_csv_fixture_workflow_demo.py`, `tests/test_local_csv_fixture_workflow_demo.py`, `reports/local_csv_fixture_workflow_demo.md`, `reports/experiment_logs/local_csv_fixture_workflow_demo.json` | Completed for committed synthetic local fixtures only; all configured fixture case/split rows and invalid reasons are now reported. |
| OHLCV/local CSV readiness path | `docs/volume_ohlcv_schema_plan.md`, `src/data/csv_loader.py`, `tests/test_csv_loader.py`, `tests/fixtures/local_csv_loader_smoke/` | Planned and implemented for strict local fixture loading, not real-data interpretation. |
| Private EODHD validation-only checks | `docs/eodhd_local_csv_validation_handoff.md`, `docs/eodhd_data_quality_diagnostics_checkpoint.md`, `docs/current_handoff.md` | Completed as private validation-only loader/schema and data-quality diagnostics; raw private files remain outside the repo and broader interpretation remains blocked. |
| Private EODHD factor diagnostics | `docs/eodhd_factor_diagnostics_dry_run_checkpoint.md`, `docs/eodhd_factor_diagnostics_experiment_log_checkpoint.md`, `docs/eodhd_factor_diagnostics_readiness_review_checkpoint.md`, `docs/eodhd_limited_factor_diagnostics_review_checkpoint.md`, `docs/eodhd_limited_factor_diagnostics_brief_checkpoint.md`, `tests/test_eodhd_*` | Private IC, Rank IC, and quantile-spread diagnostics exist with neutral review/brief guardrails; they are not strategy, performance, alpha, or trading-readiness evidence. |
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
| Local CSV path | Strict local CSV loader, inventory review, committed synthetic fixtures, fixture workflow demos, and private EODHD validation-only checks exist. | `src/data/csv_loader.py`, `src/data/local_csv_inventory.py`, `tests/fixtures/local_csv_loader_smoke/`, `research/local_csv_fixture_workflow_demo.py`, `docs/eodhd_local_csv_validation_handoff.md`, `docs/eodhd_data_quality_diagnostics_checkpoint.md` | Broader real-data interpretation remains blocked until provenance, point-in-time universe status, adjustment policy, benchmark methodology, sample splits, costs/slippage, and interpretation policy are accepted. |
| Experiment records and reports | Synthetic JSON sidecar logs, registry, caveated Markdown reports, and private EODHD experiment-log handoff paths exist. | `src/reporting/experiment_log.py`, `src/reporting/experiment_registry.py`, `reports/experiment_logs/`, `reports/experiment_registry.md`, `docs/eodhd_factor_diagnostics_experiment_log_checkpoint.md` | Private EODHD diagnostic values still require accepted experiment-log interpretation records before they can be treated as research evidence. |
| Private EODHD diagnostics | Private validation-only checks and private IC, Rank IC, and quantile-spread diagnostic calculations exist. | `docs/eodhd_local_csv_validation_handoff.md`, `docs/eodhd_factor_diagnostics_dry_run_checkpoint.md`, `docs/eodhd_limited_factor_diagnostics_review_checkpoint.md`, `docs/eodhd_limited_factor_diagnostics_brief_checkpoint.md` | Diagnostic calculations are not broader interpretation, strategy, backtest, portfolio, performance, alpha, investment, or trading-readiness evidence. |
| Simulated backtesting | Long-only local backtester includes benchmark, costs, fixed-bps slippage, turnover, and optional precomputed volume-aware impact. | `src/backtest/portfolio.py`, `src/backtest/metrics.py`, `src/backtest/slippage.py`, `tests/test_backtest_portfolio.py`, `tests/test_volume_aware_slippage.py` | No real-data benchmark/universe study; volume-aware capacity remains synthetic/local-fixture only. |
| LEAN path | Non-executing scaffold and pure-Python signal-only metadata draft exist. | `lean/README.md`, `lean/smoke_test_algorithm.py`, `lean/signal_only_momentum_draft.py`, `tests/test_lean_*` | Runnable LEAN, live trading, paper trading, brokerage, and order execution remain blocked. |

## 4. Remaining Gaps Toward The Original Goal

The original goal is still not achieved. The repository has strong synthetic
and local-fixture infrastructure, but it does not yet contain real-market
evidence that any factor is a verifiable stock-selection signal.

Remaining gaps:

- No accepted local CSV or EODHD research interpretation has been completed
  under full provenance, schema, survivorship, benchmark, sample-split,
  cost/slippage, and experiment-log gates.
- Private EODHD IC, Rank IC, and quantile-spread diagnostic calculations exist,
  but no benchmark-relative or train/validation/test interpretation has been
  accepted.
- No real benchmark, point-in-time universe, liquidity universe, or adjustment
  policy has been accepted for a user-provided dataset.
- No real-data volume, participation, capacity, or market-impact conclusion
  exists.
- No documented robustness and parameter-sensitivity interpretation exists for
  any user-provided local CSV research run because no such run has passed
  readiness gates.
- Generated reports and experiment logs remain synthetic diagnostics or
  committed-fixture smoke checks, not investment evidence.
- LEAN work remains non-executing and must not imply live, paper, brokerage,
  or order-execution readiness.

## 5. Guardrail Review

Current guardrail status:

| Guardrail | Finding |
| --- | --- |
| No real data fetching | Satisfied. The repository does not fetch data; private EODHD evidence is local-only and remains outside the repo. |
| No vendor downloads | Satisfied. No `requests`, `yfinance`, Alpaca, CCXT, or API-download path is part of the workflow. |
| No credentials | Satisfied. No credential, token, account, or environment-secret path is part of the workflow. |
| No live trading or paper trading | Satisfied. Mentions are prohibitions, caveats, or static tests. |
| No brokerage or order execution | Satisfied. LEAN artifacts are non-executing; backtester behavior is simulated research accounting only. |
| No profitability claims | Satisfied. Current reports and logs frame results as synthetic diagnostics or local-fixture smoke checks only. |
| No bulk WorldQuant 101 implementation | Satisfied. Only alpha#009 and alpha#012 are implemented as research features. |

## 6. Recommended Next Roadmap

The synthetic and committed-local-fixture robustness/reporting path is complete
through generated outputs. Private EODHD validation-only and diagnostic
checkpoints also exist, but broader interpretation remains blocked. The next
stages should not add more synthetic output by default. They should either
stay documentation-only, or wait for explicit acceptance of local CSV/EODHD
methodology inputs before any real-data interpretation.

| Stage | Purpose | Expected files | Tests/checks | Stop condition |
| --- | --- | --- | --- | --- |
| Local CSV/EODHD methodology acceptance | Only when the user supplies or approves dataset scope, prepare or review the scope statement, inventory, schema map, readiness audit, experiment handoff, sample split, benchmark, costs/slippage, and interpretation policy before interpreting data. | Readiness audit artifacts and experiment handoff only; no private data committed. | Readiness checks defined by the project Skill; full pytest and compileall if repo files change. | Stop for missing provenance, schema ambiguity, survivorship ambiguity, benchmark ambiguity, credentials, vendor APIs, private data exposure, or profitability framing. |
| Real-data readiness gate reconciliation | If the user asks to continue without providing local data, reconcile the readiness checklist, audit template, and handoff so the next required user inputs are explicit. | `docs/current_handoff.md`, readiness docs, logs, changelog, `docs/repo_map.md` if regenerated. | Full pytest, compileall, repo map refresh, and `git diff --check origin/main..HEAD`. | Stop if the stage would imply that a real-data study can proceed without the readiness artifacts. |
| Registry schema review | Only if configured-case diagnostics need to become discoverable in `reports/experiment_registry.md`, first add a documentation-only schema review. | Narrow docs first; code/generated outputs only in a later explicitly scoped PR. | Full pytest, compileall, and guardrail review. | Stop if registry fields would imply real-data validation, tradeability, execution realism, or profitability. |

## 7. Final Recommendation

The next PR-sized stage after this roadmap refresh merges should be:

```text
Pause for accepted local CSV/EODHD methodology inputs before any real-data interpretation.
```

Reason:

- The synthetic and committed-local-fixture robustness/reporting path now has
  reviewed plans, tests, opt-in report/log support, and committed generated
  artifacts.
- The remaining original-goal gap is not more synthetic evidence; it is an
  accepted methodology package for local CSV or EODHD data that covers scope,
  provenance, schema, survivorship, benchmark, split, cost/slippage, and
  readiness-audit gates.
- Without those inputs, a real-data study would require assumptions the project
  explicitly forbids.

If the user asks to keep advancing without local data, the next stage should be
documentation-only and should make the required readiness inputs clearer. It
should not fetch data, use vendor APIs, add credentials, add live or paper
trading, add brokerage/order logic, or claim profitability.
