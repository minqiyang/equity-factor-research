# Current Roadmap Gap Refresh

Date: 2026-06-05

This checkpoint refreshes the repository roadmap after PR #46 merged. It
compares the older `docs/original_goal_gap_analysis.md` recommendations with
the current implementation so the next stage does not duplicate completed work.

It is documentation only. It does not modify source code, tests, research
scripts, generated reports, strategy logic, backtester behavior, metrics, data
access, execution assumptions, or performance claims. It does not fetch real
data, download data, add vendor APIs, add credentials, add live trading, add
brokerage integration, add order execution, or claim profitability.

## 1. Review Baseline

Current synced state before this checkpoint:

```text
Branch reviewed: main
HEAD reviewed: ebeb10a Merge pull request #46 from minqiyang/codex/lean-signal-only-momentum-draft
Open pull requests: none
```

Validation before creating this checkpoint:

```text
python -m pytest -q
272 passed

python -m compileall src tests research
passed
```

## 2. Why The Older Gap Analysis Is Stale

`docs/original_goal_gap_analysis.md` remains useful for the original project
objective and high-level guardrails, but several of its recommended next
stages have since been completed.

The older analysis recommended:

- a local CSV loader smoke demo using committed synthetic local fixtures.
- synthetic IC and Rank IC helpers.
- a synthetic quantile spread diagnostic.
- a local CSV research workflow demo using local fixtures only.
- QuantConnect/LEAN planning updates.

Current repository evidence shows these items are now implemented or refreshed:

| Older roadmap item | Current evidence | Current status |
| --- | --- | --- |
| Local CSV loader smoke demo | `tests/fixtures/local_csv_loader_smoke/`, `tests/test_local_csv_loader_smoke_demo.py` | Complete for committed synthetic fixtures. |
| Synthetic IC / Rank IC helper | `src/features/diagnostics.py`, `tests/test_diagnostics.py` | Implemented and tested. |
| Synthetic quantile spread diagnostic | `src/features/diagnostics.py`, `tests/test_diagnostics.py` | Implemented and tested. |
| Local CSV research workflow demo | `research/local_csv_fixture_workflow_demo.py`, `tests/test_local_csv_fixture_workflow_demo.py`, `reports/local_csv_fixture_workflow_demo.md`, `reports/experiment_logs/local_csv_fixture_workflow_demo.json` | Implemented with committed synthetic fixtures only. |
| QuantConnect/LEAN planning refresh | `docs/quantconnect_lean_plan.md`, `docs/lean_parity_checklist.md`, `docs/lean_smoke_test_design.md`, `docs/lean_implementation_planning_checkpoint.md` | Refreshed through planning and scaffold checkpoints. |
| LEAN scaffold boundary | `lean/README.md`, `lean/smoke_test_algorithm.py`, `tests/test_lean_smoke_test_scope.py` | Implemented as non-executing metadata only. |
| LEAN signal-only boundary | `docs/lean_signal_only_draft_design.md`, `lean/signal_only_momentum_draft.py`, `tests/test_lean_signal_only_draft_scope.py` | Implemented as pure-Python metadata only. |

## 3. Current Implementation Traceability

| Goal area | Current implementation | Evidence files | Remaining gap |
| --- | --- | --- | --- |
| Auditable governance | Agent rules, project spec, engineering log, decision log, troubleshooting log, changelog, staged workflow Skill, and long-running controller. | `AGENTS.md`, `PROJECT_SPEC.md`, `docs/engineering_log.md`, `docs/decision_log.md`, `docs/troubleshooting_log.md`, `.agents/skills/staged-quant-workflow/SKILL.md`, `docs/codex_long_running_controller.md`, `CHANGELOG.md` | Keep logs current and concise as new stages land. |
| Factor features | 12-1 momentum and `alpha_009` exist as research features. | `src/features/momentum.py`, `src/features/worldquant_alphas.py`, `tests/test_momentum.py`, `tests/test_worldquant_alphas.py` | Reversal, volatility, liquidity, and additional alphas remain future work. |
| Factor preprocessing | Normalization, winsorization, factor combination, correlation diagnostics, IC, Rank IC, and quantile spread diagnostics exist. | `src/features/normalize.py`, `src/features/combine.py`, `src/features/diagnostics.py`, `tests/test_normalize.py`, `tests/test_combine.py`, `tests/test_diagnostics.py` | No real user-provided data interpretation yet. |
| Local CSV path | Strict local CSV loaders and committed synthetic local fixture workflows exist. | `src/data/csv_loader.py`, `tests/test_csv_loader.py`, `research/local_csv_fixture_workflow_demo.py`, `tests/test_local_csv_fixture_workflow_demo.py` | No user-provided local CSV research study has been run or interpreted. |
| Experiment records | Synthetic JSON sidecar logs, registry, and caveated reports exist. | `src/reporting/experiment_log.py`, `src/reporting/experiment_registry.py`, `reports/experiment_logs/`, `reports/experiment_registry.md` | Real user-provided local CSV records remain gated by readiness requirements. |
| Simulated backtesting | Long-only local backtester and metrics helpers exist for synthetic workflows. | `src/backtest/portfolio.py`, `src/backtest/metrics.py`, `tests/test_backtest_portfolio.py` | Train/validation/test discipline and real benchmark/universe studies remain incomplete. |
| LEAN path | Non-executing scaffold and pure-Python signal-only metadata draft exist. | `lean/README.md`, `lean/smoke_test_algorithm.py`, `lean/signal_only_momentum_draft.py`, `tests/test_lean_*` | Runnable LEAN code remains intentionally blocked. |

## 4. Remaining Gaps Toward The Original Goal

The original goal is still not fully achieved. Current completed work is strong
synthetic and local-fixture research infrastructure, not real-market evidence.

Remaining gaps:

- No real user-provided local CSV research study has been run under the
  readiness audit and experiment-log requirements.
- No real-data IC, Rank IC, or quantile spread interpretation has been
  completed.
- No train, validation, and test split helper or workflow is currently applied
  to factor research stages.
- No real benchmark, point-in-time universe, or liquidity-based universe study
  has been completed.
- No volume, OHLCV, VWAP, market-cap, or industry-neutral data layer exists.
- No runnable QuantConnect/LEAN algorithm exists; the current LEAN artifacts
  remain non-executing and signal-only.
- Paper trading and live trading remain intentionally out of scope.

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
| No bulk WorldQuant 101 implementation | Satisfied. Only `alpha_009` is implemented as a research feature. |

## 6. Recommended Next Roadmap

The next stages should move back toward the original research-pipeline gaps
without touching real data or execution systems.

| Stage | Purpose | Expected files | Tests/checks | Stop condition |
| --- | --- | --- | --- | --- |
| A. Synthetic train/validation/test split helper | Add deterministic date-window split utilities for factor research panels before any real-data evaluation. | Likely `src/features/validation.py` or `src/utils/validation.py`, `tests/`, `docs/engineering_log.md`, `CHANGELOG.md` | Hand-calculated split tests, date-order tests, overlap tests, full pytest, compileall. | Stop if the design requires real data, model selection, performance interpretation, or broad backtester changes. |
| B. Synthetic split-aware IC / Rank IC demo | Apply the split helper to synthetic factor and forward-return panels as diagnostics only. | Likely `research/`, `tests/`, optional caveated report/log. | Deterministic demo tests, full pytest, compileall, generated-output review. | Stop if diagnostics are framed as strategy validation or parameter selection. |
| C. Local fixture split-aware workflow update | Apply split metadata to the committed synthetic local CSV fixture workflow. | Likely `research/local_csv_fixture_workflow_demo.py`, tests, reports/logs if regenerated intentionally. | Focused workflow tests, full pytest, compileall, output review. | Stop if a user-provided real dataset is required. |
| D. Volume/OHLCV schema planning | Plan local CSV schema support for volume or OHLCV before adding volume-dependent factors. | `docs/`, `docs/engineering_log.md`, `CHANGELOG.md` | Full pytest, compileall, docs diff review. | Stop if vendor downloads or real-data access are needed. |
| E. Next factor planning | Choose between reversal, volatility, or liquidity after data prerequisites and validation splits are in place. | `docs/`, maybe later `src/features/` and tests. | Planning checks or code tests depending on scope. | Stop if the stage would combine formula, data schema, and backtest behavior in one PR. |

## 7. Final Recommendation

The next implementation stage after this checkpoint should be:

```text
Synthetic train/validation/test split helper
```

Reason:

- The project already has factor diagnostics, local fixture demos, and
  synthetic smoke tests.
- The next major original-goal gap is validation discipline: separating
  in-sample, validation, and test periods before interpreting factor variants.
- A deterministic split helper can be implemented and tested without real data,
  vendor access, trading logic, backtester changes, or performance claims.

The next stage should remain synthetic/local-fixture only and should not fetch
data, use vendor APIs, add credentials, add live or paper trading, add
brokerage/order logic, or claim profitability.
