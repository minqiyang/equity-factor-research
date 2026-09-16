# M3-03 Attempt Report

Worktree: `efr-pr210-review` on branch `codex/m3-03-source-row-lag-20260916`.
This attempt proves Demo v0 and the M3-01 three-factor backtest demo count signal lag in observed source rows. Those demos keep the supplied observed index. Detecting invented sessions remains later calendar-alignment work.

## Files

- `research/source_row_lag.py`: observed-source-index checks and positional source-row lag. Lag counts observed source rows. A missing source row remains an omitted observation. The demos keep the supplied index.
- `research/demo_v0.py`: validates the observed source index after bar integrity and uses `DEMO_SIGNAL_LAG_PERIODS`. Frozen `DEMO_V0_CONFIG` is unchanged.
- `research/synthetic_multifactor_backtest_demo.py`: the same observed-source-index check and lag constant.
- `tests/test_source_row_lag.py`: helper and backtester killing tests on a Monday/Wednesday/Friday gap. Calendar-day lag of one day points at the omitted weekday; source-row lag uses the previous observed row.
- `tests/test_demo_v0.py` and `tests/test_synthetic_multifactor_backtest_demo.py`: demo-level gapped-index lag tests and extra-row count mismatch versus configured periods.
- `README.md`, `docs/current_roadmap.md`, `docs/engineering_log.md`, `CHANGELOG.md`, `EXPERIMENT_LOG.md`, `docs/repo_map.md`: M3-03 status and English prose updates.

## Tests

Focused tests passed:

- `python -m pytest -q tests/test_source_row_lag.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py tests/test_bar_integrity.py tests/test_backtest_timing_contract.py` — 233 passed, 2 skipped.
- `python -m ruff check research/source_row_lag.py research/demo_v0.py research/synthetic_multifactor_backtest_demo.py tests/test_source_row_lag.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py`
- `python -m compileall -q src research tests`
- `git diff --check`

Covered behavior:

- Frozen Demo v0 config remains seed 20260521, 20 assets, 756 rows, lookback 252, skip 21, ME, top_n 5, 10 bps, 0 slippage.
- Signal lag of one observed source row maps Wednesday execution to Monday's signal on a Monday/Wednesday/Friday index.
- A dropped weekday remains an omitted observation. The next observed row uses the previous observed row.
- A price panel with extra rows versus `config.periods` is refused by the existing source-row count check.
- Existing Demo v0, M3-01, M3-02, and timing-contract tests still pass.

## Remaining Limits

- M3-03 is a synthetic demo timing proof. It is a workflow diagnostic and makes no profitability claim.
- Official Demo v0 and M3-01 commands still generate consecutive business-day fixtures. The gapped-index proof uses test panels through those commands.
- These demos keep the supplied observed index. Detecting invented sessions against a calendar remains later Milestone 3 calendar-alignment work.
- Broader historical windows, unchanging-price segment reporting, and adjustment-event checks remain later Milestone 3 layers.
- All-Attempt Case Logging remains lightweight demo logging, not charter Stage 4 experiment/trial-ledger accounting.
- Private data, brokerage, orders, paper/live trading, new calendars, and new cost engines stay out of scope.
