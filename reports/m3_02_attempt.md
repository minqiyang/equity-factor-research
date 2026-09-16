# M3-02 Attempt Report

Worktree: `efr-m3-02-zerovol-20260916` on branch `codex/m3-02-zero-volume-refuse-20260916`.
This attempt implements the M3-02 zero-volume / missing-bar refusal layer for Demo v0 and the M3-01 three-factor backtest demo.

## Files

- `research/bar_integrity.py`: fail-closed price and volume bar checks. Price bars must keep the configured row and asset counts and remain finite and strictly positive. A supplied volume panel must share those axes and remain finite and strictly positive.
- `research/demo_v0.py`: calls the price-bar check after `generate_synthetic_prices` and the volume-bar check when a volume panel is supplied. Frozen `DEMO_V0_CONFIG` is unchanged. Volume is not passed into the backtester or cost engines.
- `research/synthetic_multifactor_backtest_demo.py`: the same bar checks before factor generation and backtest accounting.
- `tests/test_bar_integrity.py`: helper killing tests for missing, dropped, zero, infinite, zero-volume, and misaligned bars. Inputs are left unmutated.
- `tests/test_demo_v0.py` and `tests/test_synthetic_multifactor_backtest_demo.py`: demo-level killing tests. Missing, dropped, or zero price bars and a supplied zero-volume panel raise, write `started` then `failure`, and leave the comparison report unwritten.
- `README.md`, `docs/current_roadmap.md`, `docs/engineering_log.md`, `CHANGELOG.md`, `EXPERIMENT_LOG.md`, `docs/repo_map.md`: M3-02 status and English prose updates.

## Tests

Focused tests passed:

- `python -m pytest -q tests/test_bar_integrity.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py tests/test_csv_loader.py tests/test_liquidity.py tests/test_volume_aware_slippage.py` — 167 passed.
- `python -m ruff check research/bar_integrity.py research/demo_v0.py research/synthetic_multifactor_backtest_demo.py tests/test_bar_integrity.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py`
- `python -m compileall -q src research tests`
- `git diff --check`
- `PYTHONPATH=src python -m research.demo_v0` and `PYTHONPATH=src python -m research.synthetic_multifactor_backtest_demo` refreshed the comparison reports and appended started then success for attempt 2 on each command.

Covered behavior:

- Frozen Demo v0 config remains seed 20260521, 20 assets, 756 rows, lookback 252, skip 21, ME, top_n 5, 10 bps, 0 slippage.
- Missing, dropped, zero, and infinite price bars raise before report replacement.
- A supplied zero-volume or missing-volume panel raises. A strictly positive aligned volume panel is accepted and unused by the backtester.
- The local CSV loader still accepts zero volume as loader-valid.
- Existing Demo v0, M3-01, loader, liquidity, and volume-aware slippage tests still pass.

## Remaining Limits

- M3-02 is a synthetic demo data-cleaning layer. It is a workflow diagnostic and makes no profitability claim.
- Official Demo v0 and M3-01 commands remain price-only in production; volume is an optional supplied panel for the refuse path.
- The local CSV loader still accepts zero volume as loader-valid. Liquidity eligibility and volume-aware slippage keep their existing contracts.
- Unchanging-price segment reporting, date-gap calendar alignment, and adjustment-event checks remain later Milestone 3 layers.
- All-Attempt Case Logging remains lightweight demo logging, not charter Stage 4 experiment/trial-ledger accounting.
- Private data, brokerage, orders, paper/live trading, new calendars, and new cost engines stay out of scope.
- This worktree implements the slice. GitHub publication is outside this card.
