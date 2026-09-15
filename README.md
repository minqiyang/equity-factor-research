<p align="center">
  <img src="assets/readme/hero.svg" width="100%" alt="Equity Factor Research: a deterministic research pipeline shown as an aligned dithered factor panel">
</p>

<p align="center">
  <a href="https://github.com/minqiyang/equity-factor-research/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/minqiyang/equity-factor-research/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.11 or newer" src="https://img.shields.io/badge/Python-3.11%2B-348FEF">
  <a href="LICENSE"><img alt="Apache 2.0 license" src="https://img.shields.io/badge/License-Apache--2.0-8B5CF6"></a>
</p>

An auditable Python toolkit for equity-factor research with strict data contracts, deterministic diagnostics, drift-aware portfolio accounting, and reproducible experiment records.

The ultimate aspiration of the project is automated stock selection and trading, pursuing sustainable risk-controlled long-term net returns (stable profit is an objective, not a guarantee). See [North Star](docs/north_star.md) for the active product aspiration and demo-first delivery principles. The historical [research charter](docs/research_program_charter.md) remains preserved as formal evidence policy. This repository builds the simulated research and backtesting foundation—the essential first part, not the final execution product. Live execution, broker connectivity, pre-trade risk limits, reconciliation, and emergency kill switches belong strictly to a future, separately authorized private execution repository.

`LAGGED FEATURE CONTRACTS` · `EXPLICIT SIGNAL LAG` · `DRIFT-AWARE ACCOUNTING` · `JSON EVIDENCE`

[Quickstart](#quickstart) · [North Star](docs/north_star.md) · [Research charter](docs/research_program_charter.md) · [Data methodology](docs/point_in_time_data_methodology_contract.md) · [Research method](docs/research_method.md) · [Project specification](PROJECT_SPEC.md) · [Experiment registry](reports/experiment_registry.md) · [Current roadmap](docs/current_roadmap.md)

## Quickstart

Python 3.11 or newer is required.

```bash
git clone https://github.com/minqiyang/equity-factor-research.git
cd equity-factor-research
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
```

Run the reproducible examples:

```bash
python -m research.synthetic_momentum_demo
python -m research.synthetic_multifactor_workflow_demo
python -m research.synthetic_combined_score_backtest_demo
python -m research.local_csv_fixture_workflow_demo
```

These commands use synthetic data or committed fixtures and may refresh files under `reports/`. Their outputs are legacy reproducibility and engineering diagnostics, not acceptance of Demo v0. Multi-factor examples remain available for workflow testing but are outside the single-factor Demo v0 scope.

## Demo-First Delivery Target (Demo v0)

The project follows a **demo-first** engineering strategy: ship a basic, presentable, and reproducible end-to-end version first, record non-blocking imperfections in a lightweight backlog, and iterate in layers. We avoid blocking a working demonstration on an ideal pipeline, full SEC entity lineage proof, complete ledger schema coverage, or a broad factor zoo.

The active delivery target is **Demo v0** (target deliverable, not yet implemented):
- One reproducible local command/workflow using an existing price-only factor and a fixed strategy configuration;
- Simulated stock selection and drift-aware portfolio holdings;
- Human-readable comparison report with benchmark, explicit transaction cost and timing models (accepted `after_close_signal_next_observed_close_v1`), risk metrics, and limitations;
- All-Attempt Case Logging recording all attempted cases (distinguishing lightweight diagnostic run logging from formal experiment/trial-ledger accounting required by charter Stage 4 / Milestone 4).

Synthetic fixture workflows are demonstrable without private data. Any separately authorized local-data run remains explicitly exploratory and diagnostic.

## Method

`LOCAL CSV → FACTOR PANELS → DIAGNOSTICS → DRIFT-AWARE ACCOUNTING → MARKDOWN + JSON`

The timing model, portfolio accounting, control gates, system map, and evidence lifecycle live on a dedicated page:

**[Read the research method →](docs/research_method.md)**

Plotting is a placeholder module; the roadmap tracks its delivery.

The public research path uses local files and committed fixtures. The
provider-agnostic
[point-in-time data methodology contract](docs/point_in_time_data_methodology_contract.md)
defines manifest, universe, corporate-action, field, privacy, and
holdout-access requirements. Stage 3 contract acceptance is
methodology-process evidence.

## Current program status

- **North Star & Roadmap Alignment**: Five primary milestones define the path from core research foundation to simulated demo slice, exploratory multi-factor expansion, formal research promotion, and eventual separately authorized execution. See the [current roadmap](docs/current_roadmap.md).
- **Historical Track A Disposition**: Track A (14-trial EODHD diagnostic design) remains frozen and REFUSED (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`) under evidence ceiling `DIAGNOSTIC_ONLY`. This historical refusal is preserved as immutable evidence and is not a universal blocker for the demo-first program.
- **Track B First Checkpoints**: SQLite ledger runtime first checkpoints (Path A PR #199, Path B PR #200) are merged on main as software progress; optional 37-event schema completion is safely deferred.
- **Exploration Diagnostic Context**: A local 2026-09-13 metadata and numerical diagnostic provided qualitative feasibility and planning context on local data history, with documented caveats (zero-volume segments, date gaps, unverified adjustment events) deferred for layered handling. It is outside Demo v0 acceptance, produces no strategy or profitability claims, and does not prove tradability, universe completeness, or a pristine holdout.
- See the [current roadmap](docs/current_roadmap.md) for execution gates and milestone tracking.

## Quality gates

```bash
python -m pytest -q
python -m ruff check .
python -m compileall -q src research tests lean
python -m build
git diff --check
```

## License

Licensed under the [Apache License 2.0](LICENSE).
