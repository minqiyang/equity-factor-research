# AI-Assisted Equity Factor Research Pipeline

An educational, research-grade sandbox for building auditable equity factor workflows with synthetic and local fixture data.

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB)
![Local tests](https://img.shields.io/badge/local%20tests-264%20passed-2EA44F)
![Data scope](https://img.shields.io/badge/data-synthetic%20%2B%20local%20fixtures-0969DA)
![Live trading](https://img.shields.io/badge/live%20trading-not%20supported-B42318)
![License](https://img.shields.io/badge/license-not%20selected-6E7781)

This repository is a local Python research project for studying cross-sectional
equity factor ideas with explicit date alignment, deterministic tests, caveated
reports, and reproducible experiment logs. It is designed to show the discipline
behind a quantitative research workflow before any real-data interpretation,
live trading, or brokerage integration is considered.

![Research workflow diagram](docs/assets/research_workflow.svg)

The project is useful if you want to see how factor research can be structured
so that a newcomer, reviewer, recruiter, or professor can trace the path from a
factor idea to tested code, diagnostics, reports, limitations, and next steps.

## What You Can Run Today

The current repository supports deterministic smoke tests and demos only. They
use generated synthetic panels or committed tiny local CSV fixtures.

- Run the full test suite: `python -m pytest -q`
- Exercise the local CSV fixture workflow: `python -m research.local_csv_fixture_workflow_demo`
- Run a synthetic multi-factor feature workflow: `python -m research.synthetic_multifactor_workflow_demo`
- Run a synthetic combined-score backtest smoke test: `python -m research.synthetic_combined_score_backtest_demo`

These workflows are reproducibility checks and research-pipeline demos. Synthetic
metrics are not market evidence and should not be used as strategy-validation or
profitability claims.

## Quick Start

From a fresh checkout:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
```

Run the safest beginner demo:

```powershell
python -m research.local_csv_fixture_workflow_demo
```

Then inspect:

- [`reports/local_csv_fixture_workflow_demo.md`](reports/local_csv_fixture_workflow_demo.md)
- [`reports/experiment_logs/local_csv_fixture_workflow_demo.json`](reports/experiment_logs/local_csv_fixture_workflow_demo.json)
- [`reports/experiment_registry.md`](reports/experiment_registry.md)
- [`research/local_csv_fixture_workflow_demo.py`](research/local_csv_fixture_workflow_demo.py)

The local CSV fixture demo loads committed synthetic CSV files, validates date
alignment, computes `alpha_009` as a research feature, and writes caveated
diagnostics. It does not run a portfolio backtest, fetch real market data,
connect to a broker, place orders, or claim that any factor works.

## Demo Walkthrough

The local CSV fixture workflow is the best first read because it is small and
end-to-end:

1. Load synthetic adjusted-close and benchmark fixtures from
   [`tests/fixtures/local_csv_loader_smoke/`](tests/fixtures/local_csv_loader_smoke/).
2. Validate strict CSV schemas and matching dates.
3. Compute the close-only `alpha_009` research feature.
4. Compute forward returns for diagnostic evaluation only; they are not feature
   inputs.
5. Write an auditable Markdown report and JSON experiment log.
6. Refresh the synthetic experiment registry so outputs are discoverable.

For a broader synthetic workflow, see the combined-score smoke test:

- Script: [`research/synthetic_combined_score_backtest_demo.py`](research/synthetic_combined_score_backtest_demo.py)
- Report: [`reports/synthetic_combined_score_backtest_demo.md`](reports/synthetic_combined_score_backtest_demo.md)
- Log: [`reports/experiment_logs/synthetic_combined_score_backtest_demo.json`](reports/experiment_logs/synthetic_combined_score_backtest_demo.json)

## Why It Is Credible

The repository prioritizes research hygiene over attractive charts:

- Feature dates and signal timing are explicit.
- Tests cover alignment, missing-data behavior, and off-by-one risks.
- Synthetic demos are clearly labeled as workflow diagnostics.
- Backtest smoke tests include transaction-cost assumptions and benchmark
  comparison caveats.
- Experiment reports, JSON logs, and the registry keep weak or limited evidence
  visible.
- QuantConnect/LEAN work is staged behind design notes and guardrails before
  any runnable platform implementation.

For a beginner-facing explanation of the project goal, core concepts, current
components, evaluation standards, and limitations, see
[`docs/project_overview.md`](docs/project_overview.md).

## Project Map

| Path | Purpose |
| --- | --- |
| [`src/features/`](src/features/) | Factor operators, momentum, WorldQuant-style `alpha_009`, normalization, combination, and diagnostics. |
| [`src/backtest/`](src/backtest/) | Simulated long-only backtester and metrics helpers. |
| [`src/data/`](src/data/) | Strict local CSV loaders for controlled local-file workflows. |
| [`research/`](research/) | Runnable synthetic and local-fixture demo scripts. |
| [`reports/`](reports/) | Caveated generated reports, experiment logs, and the synthetic experiment registry. |
| [`tests/`](tests/) | Deterministic tests for feature logic, diagnostics, backtesting, loaders, reports, and guardrails. |
| [`docs/`](docs/) | Project overview, readiness audits, workflow logs, LEAN planning, and research-process notes. |
| [`lean/`](lean/) | Non-executing LEAN-adjacent planning/scaffold work under strict guardrails. |

## Key Reports And Docs

- [`reports/experiment_registry.md`](reports/experiment_registry.md) - index of deterministic synthetic demo logs.
- [`reports/local_csv_fixture_workflow_demo.md`](reports/local_csv_fixture_workflow_demo.md) - local CSV fixture walkthrough output.
- [`reports/synthetic_multifactor_workflow_demo.md`](reports/synthetic_multifactor_workflow_demo.md) - synthetic feature preprocessing and combination workflow.
- [`reports/synthetic_combined_score_backtest_demo.md`](reports/synthetic_combined_score_backtest_demo.md) - synthetic combined-score backtest smoke test.
- [`docs/real_data_readiness_audit.md`](docs/real_data_readiness_audit.md) - requirements before interpreting real local CSV research.
- [`docs/quantconnect_lean_plan.md`](docs/quantconnect_lean_plan.md) - staged QuantConnect/LEAN translation plan.
- [`docs/engineering_log.md`](docs/engineering_log.md) - chronological engineering notes, reviews, and validation history.

## Research Safety And Scope

This project is not:

- live trading.
- paper trading.
- broker integration.
- order execution logic.
- a data downloader.
- financial advice.
- proof that any strategy is profitable.

All current reports use synthetic data or committed synthetic local fixtures.
Future real-data work must document the data source, universe, sample splits,
benchmark, costs, slippage, limitations, and validation process before any
result can be interpreted.

## Current Status

The repository has working factor infrastructure, synthetic workflow demos,
strict local CSV fixture checks, experiment logging, and LEAN planning
documents. It does not yet have a GitHub Actions workflow, selected license, or
real-data validation study. License selection remains a recommended follow-up
before broader public reuse.
