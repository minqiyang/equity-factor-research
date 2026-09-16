# M3-04 Attempt Report

Worktree: `efr-m3-04-pit007-20260916` on branch `codex/m3-04-pit007-no-double-div-20260916`.
This attempt proves Demo v0 and the M3-01 three-factor backtest demo compute held returns from the supplied price series only. A separate cash-dividend overlay on that series is refused. Frozen `DEMO_V0_CONFIG` is unchanged. Event-level dividend and split reconciliation remains later Milestone 3/4 work.

## Files

- `research/dividend_policy.py`: price-series simple-return basis and cash-dividend overlay refusal. Held returns use `current / previous - 1`. A separate cash-dividend overlay on that series is refused.
- `research/demo_v0.py`: calls `refuse_cash_dividend_overlay` after bar integrity and observed-source-index checks. Frozen `DEMO_V0_CONFIG` is unchanged.
- `research/synthetic_multifactor_backtest_demo.py`: the same overlay refusal.
- `tests/test_dividend_policy.py`: helper and backtester killing tests on an already-adjusted flat series. Adding cash dividends to that series inflates the return; the backtester keeps the price-ratio return. `run_long_only_backtest` has no cash-dividend parameter.
- `tests/test_demo_v0.py` and `tests/test_synthetic_multifactor_backtest_demo.py`: demo-level overlay refusal keeps the comparison report unwritten.
- `README.md`, `docs/current_roadmap.md`, `docs/engineering_log.md`, `CHANGELOG.md`, `EXPERIMENT_LOG.md`, `docs/repo_map.md`: M3-04 status and English prose updates.

## Tests

Focused tests passed:

- `python -m pytest -q tests/test_dividend_policy.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py tests/test_bar_integrity.py tests/test_source_row_lag.py tests/test_backtest_timing_contract.py` — 245 passed, 2 skipped.
- CI-baseline `python -m pytest -q` — 2836 passed, 2 skipped.
- `python -m ruff check .`
- `python -m compileall -q src tests research lean`
- `git diff --check`

Covered behavior:

- Frozen Demo v0 config remains seed 20260521, 20 assets, 756 rows, lookback 252, skip 21, ME, top_n 5, 10 bps, 0 slippage.
- Held returns on a total-return / already-adjusted flat series match `current / previous - 1` and stay below the price-ratio-plus-cash-dividend figure.
- A supplied cash-dividend overlay is refused at Demo v0 and M3-01.
- Existing Demo v0, M3-01, M3-02, M3-03, and timing-contract tests still pass.

## Remaining Limits

- M3-04 is a synthetic demo return-basis proof. It is a workflow diagnostic and makes no profitability claim.
- Event-level dividend and split reconciliation against independent raw events remains later Milestone 3/4 corporate-action work.
- These demos treat the supplied price series as the complete return vehicle. They do not classify a vendor series as raw, split-adjusted, or total-return.
- Broader historical windows, calendar-alignment infrastructure, and invented-session detection remain later Milestone 3 layers.
- All-Attempt Case Logging remains lightweight demo logging, not charter Stage 4 experiment/trial-ledger accounting.
- Private data, brokerage, orders, paper/live trading, new calendars, and new cost engines stay out of scope.
