# M3-05 Attempt Report

Worktree: `efr-m3-05-broader-windows-20260916` on branch `codex/m3-05-broader-windows-20260916`.
This attempt proves Demo v0 and the M3-01 three-factor backtest demo run on a longer synthetic panel of length `2 * DEMO_V0_CONFIG.periods` (1512) through `dataclasses.replace(..., periods=...)`. Official frozen `DEMO_V0_CONFIG` remains seed 20260521, 20 assets, 756 rows, lookback 252, skip 21, ME, top_n 5, 10 bps, 0 slippage. Official commands stay `python -m research.demo_v0` and `python -m research.synthetic_multifactor_backtest_demo`.

## Files

- `tests/test_broader_windows.py`: replace-only longer-window runs for Demo v0 and M3-01. Official `periods` stays 756. The replaced configs keep lookback 252, skip 21, ME, top_n 5, 10 bps, and 0 slippage. Both pipelines write 1512 source rows and keep the synthetic-diagnostic claim.
- `README.md`, `docs/current_roadmap.md`, `docs/engineering_log.md`, `CHANGELOG.md`, `EXPERIMENT_LOG.md`, `docs/repo_map.md`: M3-05 status and English prose updates.

## Tests

Focused tests passed:

- `python -m pytest -q tests/test_broader_windows.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py tests/test_bar_integrity.py tests/test_source_row_lag.py tests/test_dividend_policy.py tests/test_backtest_timing_contract.py` — 248 passed, 2 skipped.
- CI-baseline `python -m pytest -q` — 2839 passed, 2 skipped.
- `python -m ruff check .`
- `python -m compileall -q src tests research lean`
- `git diff --check`

Covered behavior:

- Frozen Demo v0 config remains seed 20260521, 20 assets, 756 rows, lookback 252, skip 21, ME, top_n 5, 10 bps, 0 slippage.
- `dataclasses.replace(..., periods=2 * DEMO_V0_CONFIG.periods)` runs Demo v0 and M3-01 on 1512 synthetic rows.
- Lookback, skip, costs, top_n, and rebalance frequency stay the frozen Demo v0 values on those longer runs.
- Output is a synthetic diagnostic.
- Existing Demo v0, M3-01, M3-02, M3-03, and M3-04 tests still pass.

## Remaining Limits

- M3-05 is a synthetic longer-window diagnostic. Official commands keep the frozen 756-row config.
- Calendar-alignment infrastructure, invented-session detection, and event-level dividend and split reconciliation remain later Milestone 3/4 layers.
- All-Attempt Case Logging remains lightweight demo logging, distinct from charter Stage 4 experiment/trial-ledger accounting.
- Private data, brokerage, orders, paper/live trading, new calendars, and new cost engines stay out of scope.
