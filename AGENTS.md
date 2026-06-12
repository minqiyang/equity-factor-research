# AI Agent Rules

This repository is a serious simulated quantitative research project. AI coding agents must preserve auditability, reproducibility, and research discipline.

## Startup And Context Budget

- For staged workflow continuations, read `docs/current_handoff.md` first.
- Use `docs/repo_map.md` for concise orientation before broad repository scans.
- Read deeper logs and long documents only when the handoff points to them, the active stage requires them, a check fails, or a guardrail-sensitive decision needs source evidence.
- Regenerate the repo map with `python scripts/repo_map.py` after workflow-control changes that alter the repository map.

## Command Output Protection

- Cap unknown large command output by default.
- Prefer `git status --porcelain | head -n 50` for quick status checks.
- Prefer `git log --oneline -20` for recent history.
- Prefer `git diff --name-only | head -n 80` for scope checks.
- Use `COMMAND 2>&1 | head -c 8000` for unknown commands that may print large output.
- In PowerShell, use equivalent caps such as `Select-Object -First` for line limits.
- Write full command output to temp files and inspect targeted ranges only when full review is needed.
- Never `cat` full generated reports or large logs by default.

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
- After meaningful code or research-process changes, check whether the work
  should be added to `docs/engineering_log.md` as a durable engineering note.

## Pull Request and Commit Discipline

- Prefer small, reviewable pull requests.
- Each PR should represent one clear feature, bug fix, test improvement, documentation update, or refactor.
- Prefer meaningful commits.
- Each commit should represent one coherent engineering step.
- Do not split trivial edits into artificial PRs or commits just to increase counts.
- Do not combine unrelated changes in one PR.
- Use separate PRs for distinct features, bug fixes, test hardening, documentation updates, and refactors.
- Use a separate branch for each stage or milestone.
- If a previous PR is not verified merged, pause after one current-state status
  check and report the gate; do not repeatedly re-check, poll, rerun baseline
  validation, or start another stage until the PR is merged or the user
  explicitly asks for PR inspection.
- For research features, prefer this sequence:
  1. planning
  2. tests or documentation
  3. implementation
  4. read-only review
  5. commit
  6. PR
  7. merge only after review
- When a PR has multiple meaningful commits, preserve them unless the commit history is messy.
- Do not treat PR count or commit count as a quality metric by itself.

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
