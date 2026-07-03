# Equity Factor Research

A research-only Python project for building auditable equity factor workflows with deterministic tests, synthetic demos, strict local CSV loaders, and private-data diagnostics guardrails.

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB)
[![CI](https://github.com/minqiyang/equity-factor-research/actions/workflows/ci.yml/badge.svg)](https://github.com/minqiyang/equity-factor-research/actions/workflows/ci.yml)
![Data scope](https://img.shields.io/badge/data-synthetic%20%2B%20local%20fixtures%20%2B%20private%20local%20CSV-0969DA)
![Live trading](https://img.shields.io/badge/live%20trading-not%20supported-B42318)
[![License](https://img.shields.io/badge/license-Apache--2.0-2EA44F)](LICENSE)

This repository demonstrates the engineering discipline around a quantitative equity factor research pipeline: date alignment, factor construction, diagnostics, local-file validation, reproducible reports, and explicit caveats before any broader interpretation.

It is a research and educational project. It is not investment advice. Synthetic demos, local fixture runs, and private diagnostics are not live-trading evidence and must not be read as profitability, alpha, or trading-readiness claims.

![Research workflow diagram](docs/assets/research_workflow.svg)

## What This Project Demonstrates

- Factor construction for momentum, reversal, volatility, liquidity, normalization, combination, and WorldQuant-style alpha examples.
- Signal-timing discipline around feature dates, forward-return diagnostics, train/validation/test splits, and benchmark alignment.
- A simulated long-only backtesting scaffold with transaction-cost, slippage, turnover, and metrics helpers.
- Research diagnostics including factor coverage, missingness, IC, Rank IC, quantile spread, split labels, and neutral private-data briefs.
- Reproducible tests, Markdown reports, JSON experiment logs, and repo-state handoffs.

## Current Status

Implemented:

- `src/features/`: factor operators, feature calculations, validation helpers, diagnostics, and factor combination.
- `src/backtest/`: simulated portfolio accounting, metrics, and slippage helpers.
- `src/data/`: strict local CSV loaders and local inventory helpers.
- `src/reporting/`: deterministic experiment-log and registry helpers.
- `research/`: synthetic demos, committed local-fixture demos, and private-output-only EODHD diagnostics runners.
- `tests/`: deterministic coverage for features, loaders, diagnostics, reports, synthetic workflows, LEAN-scope guardrails, and private-runner behavior using synthetic/temp files.
- `.github/workflows/ci.yml`: Python validation on pull requests and pushes to `main`.

Latest validated private EODHD work is intentionally outside the repository under:

```text
/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run
```

Those outputs support validation-only local CSV diagnostics and neutral briefs. The repo does not commit raw EODHD CSV/JSON data, tokens, or private diagnostic files.

Known limitations:

- Most committed reports use synthetic data or tiny committed fixtures.
- Private EODHD work is local-only and not committed.
- The selected EODHD universe is static and not point-in-time membership.
- EODHD raw OHLC and `adjusted_close` adjustment semantics still require review before broader interpretation.
- Sample split policy, cost/slippage assumptions, point-in-time universe membership, and real-data methodology decisions are not complete.
- No live trading, brokerage integration, real-money execution, investment recommendation, or production deployment is supported.

## Repository Map

| Path | Purpose |
| --- | --- |
| `src/features/` | Factor calculations, operators, validation, normalization, combination, and diagnostics. |
| `src/backtest/` | Simulated long-only backtester, metrics, and slippage helpers. |
| `src/data/` | Strict local CSV loading and local-file inventory helpers. |
| `src/reporting/` | Experiment log and registry helpers; plotting helpers are placeholder-only future work. |
| `research/` | Runnable synthetic demos, committed-fixture workflows, and private-output-only diagnostics runners. |
| `tests/` | Deterministic tests for research logic, guardrails, loaders, reports, workflows, and private-runner behavior. |
| `scripts/` | Repo tooling such as `scripts/repo_map.py`. Scripts must not fetch market data or trade. |
| `docs/` | Project specs, readiness gates, engineering logs, decision logs, roadmap notes, and checkpoint docs. |
| `reports/` | Generated synthetic reports and experiment logs committed for reproducible demos. |
| `lean/` | LEAN-adjacent planning/scaffold files under no-trading guardrails. |
| `pyproject.toml` | Package metadata, Python version, dependencies, dev extras, and pytest config. |
| `.github/workflows/ci.yml` | Pull-request and `main` validation workflow. |

## Quickstart

```bash
git clone https://github.com/minqiyang/equity-factor-research.git
cd equity-factor-research
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
```

Run a small committed-fixture workflow:

```bash
python -m research.local_csv_fixture_workflow_demo
```

Run synthetic research demos:

```bash
python -m research.synthetic_momentum_demo
python -m research.synthetic_multifactor_workflow_demo
python -m research.synthetic_combined_score_backtest_demo
```

These commands write or refresh generated synthetic reports under `reports/`. They are useful for reproducibility checks and code walkthroughs, not for market claims.

## Validation Commands

The current CI workflow runs:

```bash
python -m pytest -q
python -m compileall src tests research
python -m compileall lean
```

Useful local maintenance commands:

```bash
python scripts/repo_map.py
git diff --check
```

The repo map command rewrites `docs/repo_map.md`; run it only when you expect that generated file to change or when validating a repo-map refresh.

## Research Integrity

The project tries to keep research claims auditable by making these risks explicit:

- Look-ahead bias: features and diagnostics are tested for signal timing and off-by-one mistakes.
- Data leakage: target returns and same-period outcomes are separated from feature inputs.
- Survivorship bias: static universe caveats are documented before interpreting real-data diagnostics.
- Signal-lag mistakes: feature dates, execution assumptions, and return measurement windows are treated as separate concepts.
- Rebalance/execution mismatch: portfolio and diagnostics code keeps rebalance dates and return windows explicit.
- Benchmark misalignment: loaders and diagnostics check date alignment before benchmark-relative analysis.
- Unrealistic costs: zero-cost or no-slippage results are treated as diagnostics only, not evidence of deployable performance.
- Private-data scope: EODHD outputs remain local and private, with repo docs recording aggregate evidence and caveats only.

## Reports And Docs

- [`reports/experiment_registry.md`](reports/experiment_registry.md): index of committed synthetic experiment logs.
- [`reports/local_csv_fixture_workflow_demo.md`](reports/local_csv_fixture_workflow_demo.md): local CSV fixture workflow output.
- [`reports/synthetic_multifactor_workflow_demo.md`](reports/synthetic_multifactor_workflow_demo.md): synthetic feature preprocessing and combination workflow.
- [`reports/synthetic_combined_score_backtest_demo.md`](reports/synthetic_combined_score_backtest_demo.md): synthetic combined-score backtest smoke output.
- [`docs/project_overview.md`](docs/project_overview.md): beginner-facing overview.
- [`docs/real_data_readiness_audit.md`](docs/real_data_readiness_audit.md): requirements before interpreting real local CSV research.
- [`docs/current_handoff.md`](docs/current_handoff.md): current staged-workflow state.
- [`docs/engineering_log.md`](docs/engineering_log.md): chronological engineering notes and validation history.
- [`docs/decision_log.md`](docs/decision_log.md): durable research-process decisions.
- [`docs/quantconnect_lean_plan.md`](docs/quantconnect_lean_plan.md): staged LEAN translation plan.

## Roadmap

Near-term checkpoints should stay small and reviewable:

1. Decide whether another metadata-only methodology/data-readiness checkpoint is needed before broader real-data interpretation.
2. Resolve EODHD adjustment-policy questions around raw OHLC versus `adjusted_close`.
3. Document sample split, benchmark, cost, slippage, and universe assumptions for any future real-data study.
4. Keep private EODHD diagnostics separate from strategy, portfolio, PnL, Sharpe, drawdown, profitability, alpha, and trading-readiness claims.
5. Continue LEAN work only inside the existing non-execution planning/scaffold boundary until explicitly reviewed.

## Review And Governance

Pull requests should preserve research correctness, tests, docs, and the audit trail. Review findings should focus on concrete evidence of look-ahead bias, data leakage, benchmark/date mismatch, portfolio construction errors, misleading claims, hidden assumptions, or unsafe generated/private-data handling.

Agents and contributors must not store secrets, API keys, account IDs, credentials, raw private data, or downloaded market data in the repository.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
