# LEAN Implementation Planning Checkpoint

Date: 2026-06-04

This is a documentation-only planning checkpoint for the first future
QuantConnect/LEAN code pull request. It does not add a LEAN algorithm, project
scaffold, local runner, data access path, credential path, brokerage
connection, order-execution path, live trading, paper trading, or
profitability claim.

The goal is to choose a narrow future implementation boundary before any LEAN
code is added.

## 1. Purpose

The first future LEAN code PR should answer one limited engineering question:

```text
Can the repository hold a small, reviewable LEAN smoke-test scaffold whose
timing, assumptions, diagnostics, and caveats can be audited before any
platform run is interpreted?
```

It should not answer whether 12-1 momentum, `alpha_009`, or any combined
signal is useful on real market data.

## 2. Current Stage Boundary

This checkpoint allows only planning documentation.

Allowed files in this checkpoint:

- `docs/lean_implementation_planning_checkpoint.md`
- `docs/engineering_log.md`
- `CHANGELOG.md`

Out of scope for this checkpoint:

- source code changes.
- test changes.
- research script changes.
- generated report changes.
- LEAN project or algorithm files.
- external data access, downloads, vendor APIs, or credentials.
- live trading, paper trading, brokerage integration, or order execution.
- strategy-result interpretation or profitability claims.

## 3. Proposed Future First LEAN Code PR Boundary

If this checkpoint is reviewed and merged, the next LEAN-related stage may be a
minimal non-executing scaffold PR with this exact intended file boundary:

| Future file | Purpose |
| --- | --- |
| `lean/README.md` | Explain the scaffold scope, simulated-research caveats, local inspection steps, and stop conditions. |
| `lean/smoke_test_algorithm.py` | Hold a minimal LEAN smoke-test algorithm draft for simulated backtest review only. |
| `tests/test_lean_smoke_test_scope.py` | Static guardrail and structure tests for the LEAN scaffold file. |
| `docs/engineering_log.md` | Record implementation decisions, assumptions, validation, and any issues found. |
| `CHANGELOG.md` | Record the user-visible scaffold addition. |

No other source, test, research, report, backtester, metrics, data-loader,
feature, normalization, combination, or diagnostics files should change in
that first code PR unless the stage is explicitly re-scoped before editing.

The first code PR should remain non-executing in local validation. It may add a
small algorithm draft and static tests, but it should not require a local LEAN
installation, QuantConnect account, cloud run, credentials, data download, or
brokerage connection.

## 4. Future Algorithm Draft Scope

The future `lean/smoke_test_algorithm.py` should be limited to a transparent
smoke-test shape:

- daily US equity simulated backtest context.
- explicit start date, end date, benchmark, cash buffer, and warm-up history.
- a small universe rule chosen for debuggability, with survivorship caveats if
  any static symbol list is used for local inspection.
- completed-bar timing comments that distinguish algorithm time, latest
  completed data date, feature date, simulated order date, and evaluation
  date.
- one simple factor path, preferably 12-1 momentum.
- optional `alpha_009` feature-parity notes only if it remains outside order
  logic.
- diagnostic logging placeholders for eligible count, skipped count, selected
  symbols, target weights, latest completed bar date, benchmark, fee model,
  slippage model, and caveats.

The draft must not include credential loading, account identifiers, live-mode
switches, paper-trading setup, broker configuration, external download code, or
result promotion language.

## 5. Future Static Validation Strategy

The first code PR should be validated without running LEAN:

| Check | Purpose |
| --- | --- |
| `python -m pytest -q tests/test_lean_smoke_test_scope.py` | Verify scaffold structure and guardrails. |
| `python -m pytest -q` | Ensure existing repository behavior is unchanged. |
| `python -m compileall src tests research` | Preserve current Python syntax checks. |
| `git diff --check` | Catch whitespace and line-ending issues. |
| Guardrail grep on changed files | Confirm risky terms appear only as prohibitions, caveats, or static test assertions. |

Static tests should check at least:

- no imports of `requests`, `yfinance`, `alpaca`, `ccxt`, or credential helpers.
- no environment-variable or secret reads.
- no live or paper trading mode enablement.
- no brokerage model that implies a real account connection.
- no performance, profit, guarantee, or investment-advice wording.
- expected diagnostic placeholder names are present.
- expected timing and caveat comments are present.

## 6. Review Gates For The Future Code PR

Before editing:

- sync latest `main`.
- confirm no prior PR merge gate is open.
- confirm the working tree is clean.
- run full baseline tests and compile checks.
- state the intended future file list and out-of-scope list.

Before commit:

- confirm changed files match the approved file boundary.
- confirm no generated reports changed.
- confirm no existing strategy, backtester, metrics, CSV loader, diagnostics,
  normalization, combination, alpha, or research-demo behavior changed.
- confirm tests and compile checks pass.
- record any technical, workflow, or method issue in the relevant log with the
  full mistake, consequence, evidence, investigation, correction, verification,
  caveat, and prevention chain.

Before PR:

- create a ready-for-review PR only after validation passes and read-only scope
  review finds no high or medium issues.
- do not merge the PR.
- pause for human review.

## 7. Stop Conditions

Stop before implementation if the next stage would require:

- real data fetching or downloading from this repository.
- `requests`, `yfinance`, Alpaca, CCXT, or another vendor download path.
- credentials, tokens, account IDs, local secrets, or environment variables.
- live trading, paper trading, brokerage connection, or real order routing.
- a local or cloud LEAN run before the scaffold is reviewed.
- interpreting a simulated run as investment evidence.
- modifying files outside the approved first-code-PR boundary.
- weakening tests or hiding missing data.
- bulk WorldQuant 101 implementation.

## 8. Recommended Next Stage After Merge

After this planning checkpoint is reviewed and merged, the next safe stage is:

```text
Minimal non-executing LEAN scaffold with static guardrail tests
```

That stage should create only the planned `lean/` scaffold files, focused
static scope tests, and durable logs. It should not run LEAN, fetch data,
download data, add credentials, connect to a broker, enable live or paper
trading, or interpret performance.
