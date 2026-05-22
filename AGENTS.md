# AI Agent Rules

This repository is a serious simulated quantitative research project. AI coding agents must preserve auditability, reproducibility, and research discipline.

## Required Behavior

- Before editing, summarize the intended changes.
- After editing, summarize changed files, tests run, and next steps.
- Prefer small, reviewable changes.
- Keep strategy logic transparent and explainable.
- Preserve date alignment in all feature, backtest, and reporting code.
- Always explain assumptions about data, costs, slippage, execution timing, and benchmark choice.
- Add or update tests for any feature calculation change.
- Document any change to strategy logic in `EXPERIMENT_LOG.md`, `PROJECT_SPEC.md`, or a relevant research note.
- Treat zero-cost or no-slippage results as diagnostics only.
- Keep failures, weak results, and caveats visible.

## Strict Prohibitions

- Never claim a strategy is profitable without reproducible evidence.
- Never invent backtest results.
- Never remove, weaken, or skip tests to make code pass.
- Never change strategy logic without documenting the change.
- Never introduce future data leakage.
- Never use future returns, future universe membership, future fundamentals, or same-period target returns as features.
- Never connect live brokerage accounts.
- Never add live trading functionality.
- Never hide failed experiments or cherry-pick only the best parameter result.
- Never store secrets, API keys, account IDs, or credentials in the repository.

## Date Alignment Requirements

- Signal inputs must be known before the trade date.
- Feature dates must be clearly distinguished from execution dates and return measurement dates.
- Rebalance logic must state whether trades occur at next open, next close, or another explicit execution time.
- Tests should cover off-by-one errors for rolling windows, lags, and rebalance dates.

## Engineering Standards

- Use deterministic tests for core calculations.
- Keep modules narrowly scoped.
- Prefer clear pandas operations over opaque cleverness.
- Add concise comments only where they clarify non-obvious alignment or research logic.
- Do not add heavyweight dependencies without justification.
- Keep generated reports and experiment logs reproducible.
