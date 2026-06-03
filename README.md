# AI-Assisted Equity Factor Research Pipeline

This repository is a local, simulated quantitative research project for building and auditing an equity factor strategy from first principles. The goal is to create a portfolio-quality research workflow that can later be compared with, or translated into, a QuantConnect/LEAN implementation.

For a beginner-facing explanation of the project goal, factor-research concepts,
current components, evaluation standards, and limitations, see
[`docs/project_overview.md`](docs/project_overview.md).

## What This Project Is

- A reproducible Python research pipeline for cross-sectional equity factor research.
- A transparent implementation of feature calculation, portfolio construction, backtesting, risk checks, and reporting.
- A place to document assumptions, failed experiments, validation decisions, and limitations.
- A learning project that uses AI coding tools to accelerate engineering while keeping research logic auditable.

## What This Project Is Not

- It is not a live trading bot.
- It does not connect to brokerage accounts.
- It does not provide financial advice.
- It does not claim that any strategy is profitable without evidence.
- It does not optimize for attractive backtest charts at the expense of correctness.

All results produced by this repository, once implemented, should be treated as simulated research output only. Backtests can be wrong because of data errors, survivorship bias, look-ahead bias, bad cost assumptions, parameter overfitting, or market regime changes.

## Intended Workflow

1. Define an experiment in `EXPERIMENT_LOG.md`.
2. Load or prepare point-in-time-safe data.
3. Compute features with explicit date alignment.
4. Rank a liquid equity universe cross-sectionally.
5. Construct a long-only portfolio with documented constraints.
6. Run a backtest with transaction costs and slippage assumptions.
7. Compare results with a benchmark.
8. Record metrics, turnover, drawdown, failure modes, and next actions.
9. Add or update tests whenever feature logic changes.

## Planned Phases

1. Project skeleton, governance files, and test scaffolding.
2. Implement 12-1 month momentum with no look-ahead bias.
3. Add short-term reversal, realized volatility, and liquidity filters.
4. Build a simple long-only rank-and-select strategy.
5. Add portfolio accounting, turnover, costs, slippage, and benchmark comparison.
6. Add reporting charts and experiment summaries.
7. Add train/validation/test splits and robustness checks.
8. Translate the research logic into a QuantConnect/LEAN-style workflow.
9. Consider long-short extensions only after the long-only pipeline is validated.

## Running Tests

Once dependencies are installed, run:

```bash
python -m pytest
```

The initial tests only validate project structure and feature-alignment conventions. Strategy logic and performance claims will be added only after tested implementations exist.
