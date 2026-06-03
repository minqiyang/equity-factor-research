# Project Overview

This repository is an AI-assisted, simulated, auditable equity factor research
pipeline. It is a learning and research project for studying stock-selection
ideas with clear assumptions, tests, and logs.

It is not live trading, not paper trading, not financial advice, and not a
profitability claim.

## Final Objective

The final objective is to build a reproducible research platform that can take
factor ideas through a disciplined workflow:

1. Define a stock factor idea.
2. Calculate the factor with explicit date alignment.
3. Validate the calculation with deterministic tests.
4. Normalize and winsorize raw factor values when appropriate.
5. Combine factors only after alignment, missing-data behavior, and weighting
   policy are clear.
6. Run diagnostics on factor behavior, overlap, and redundancy.
7. Use synthetic workflow demos to smoke-test the pipeline.
8. Run simulated backtests with explicit timing, costs, turnover, and benchmark
   assumptions.
9. Record experiments, failures, caveats, and next actions.
10. Prepare for future user-provided local CSV research and possible
    QuantConnect/LEAN translation without adding live trading or automatic data
    downloads.

The project should help answer whether a factor idea is implemented correctly,
whether it behaves coherently under controlled tests, and whether it deserves
further research. It should not turn a formula into a trading claim.

## Core Concept

The central question is whether a stock factor can become a verifiable
stock-selection signal.

A factor is a rule that scores stocks. For example, a factor might score stocks
by past returns, recent reversal behavior, volatility, liquidity, or a
WorldQuant-style formula.

A signal is a processed factor score used for ranking. A raw factor may need
normalization, winsorization, missing-value handling, alignment checks, or
combination with other factors before it can be used as a ranking input.

A portfolio is the way selected stocks are held. It defines holdings, weights,
constraints, rebalance frequency, turnover, and benchmark comparison.

A strategy is more than a signal. It is signal plus portfolio construction,
timing, transaction costs, slippage assumptions, risk controls, benchmark
choice, and validation rules.

A conclusion is a limited, evidence-based research interpretation. A conclusion
should state what was tested, what data was used, what assumptions were made,
what failed, what remains uncertain, and what should happen next.

## Current Components

The repository currently includes:

- governance documents: `README.md`, `PROJECT_SPEC.md`, `AGENTS.md`, and
  `EXPERIMENT_LOG.md`.
- reusable factor operators in `src/features/operators.py`.
- `alpha_009` as a close-only WorldQuant-style research feature in
  `src/features/worldquant_alphas.py`.
- factor normalization and winsorization helpers in `src/features/normalize.py`.
- factor combination helpers in `src/features/combine.py`.
- factor diagnostics in `src/features/diagnostics.py`.
- a simulated long-only backtester and metrics layer in `src/backtest/`.
- synthetic workflow demos in `research/`.
- synthetic reports and experiment logs under `reports/`.
- a structured synthetic experiment registry.
- a local CSV interface plan, strict CSV loader, and real-data readiness audit.
- a QuantConnect/LEAN planning document for future platform translation.
- an engineering log for durable implementation notes, reviews, bugs, and
  workflow decisions.

These pieces are infrastructure for research discipline. They are not evidence
that any strategy is profitable.

## What This Is Not

This project is not:

- an automatic trading bot.
- real-money trading.
- paper trading.
- broker integration.
- order execution logic.
- a data downloader.
- a vendor API client.
- proof of profitability.
- a bulk WorldQuant 101 implementation.
- investment advice.

The project deliberately separates formulas, signals, portfolios, strategies,
and conclusions so that no single step is over-interpreted.

## Evaluation Standards

A factor should not be treated as useful just because it produces a number. A
credible research review should check:

- Clear formula: the factor definition is explicit and reproducible.
- Reproducible inputs: the data source, schema, date range, and version are
  recorded.
- No look-ahead bias: features do not use future returns, future membership, or
  future data revisions.
- Explicit signal timing: the date a signal becomes known is clear.
- Trading lag: simulated trades occur after the signal is known.
- Strict missing-data policy: missing values are reported or rejected instead
  of silently filled.
- Unit tests: core calculations have deterministic tests.
- IC and Rank IC later: later real-data stages should measure information
  coefficient and rank information coefficient before over-interpreting
  backtests.
- Quantile spread later: later stages should compare return behavior across
  ranked factor buckets.
- Transaction costs: costs are explicit and included when evaluating simulated
  portfolios.
- Turnover: rebalancing activity and cost impact are measured.
- Sample-out validation: parameter choices are checked outside the sample used
  to choose them.
- Parameter robustness: results are not based only on one cherry-picked
  parameter setting.
- Factor correlation and redundancy: combined factors are checked for overlap.
- Risk exposure: concentration, volatility, benchmark-relative behavior, and
  other risk exposures are reviewed.
- Multiple-testing risk: many tried factors or parameter grids increase the
  chance of false discovery.
- Failure logging: weak, failed, ambiguous, and stopped experiments remain
  visible.
- No overclaiming: synthetic diagnostics and simulated backtests are not
  profitability evidence.

## Current Limitations

Current limitations are intentional and should remain visible:

- Results are synthetic-only at this stage.
- Synthetic demos are workflow smoke tests, not market evidence.
- `alpha_009` is a research feature only and is not a profitability claim.
- The local CSV pipeline is staged and guarded by readiness checks.
- No real-data train/validation/test study has been run.
- No local CSV experiment has been interpreted as evidence.
- No live trading or paper trading exists.
- No broker, order, credential, or automatic download logic exists.
- QuantConnect/LEAN work remains a plan, not a deployed algorithm.

## Recommended Next Direction

Continue in small PR-sized stages. Finish active bugfixes first, keep each
stage narrowly scoped, and preserve the project guardrails.

Future local data work should use user-provided local CSV files only. Avoid
automatic downloads, vendor APIs, credentials, broker logic, and order
execution.

Eventually, factors should be evaluated with IC, Rank IC, quantile spread,
cost-adjusted simulated backtests, sample-out checks, parameter robustness,
factor correlation diagnostics, risk exposure review, and complete experiment
logging.

The correct direction is disciplined research evidence, not faster claims.
