# M3-06 Attempt Report

Worktree: `efr-m3-06-unchanging-price-20260916` on branch `codex/m3-06-unchanging-price-20260916`.
This attempt proves Demo v0 and the M3-01 three-factor backtest demo report unchanging-price segments. An unchanging-price segment is a consecutive run of equal prices for one asset with length >= 2. Both comparison reports record segment count, assets affected, and max run length. Consecutive equal prices stay in the panel. The backtest uses every supplied bar. Frozen `DEMO_V0_CONFIG` remains seed 20260521, 20 assets, 756 rows, lookback 252, skip 21, ME, top_n 5, 10 bps, 0 slippage. Official commands stay `python -m research.demo_v0` and `python -m research.synthetic_multifactor_backtest_demo`.

## Files

- `research/unchanging_price.py`: counts unchanging-price segments, assets affected, and max run length. The supplied panel stays in place.
- `research/demo_v0.py`: writes those counts into the Demo v0 comparison report. Frozen `DEMO_V0_CONFIG` is unchanged.
- `research/synthetic_multifactor_backtest_demo.py`: writes the same counts into the M3-01 comparison report.
- `tests/test_unchanging_price.py`: a known flat-run fixture is counted and keeps its input bytes; a strictly moving panel reports zero segments; official `DEMO_V0_CONFIG` stays frozen; Demo v0 and M3-01 keep every supplied bar.
- `tests/test_demo_v0.py` and `tests/test_synthetic_multifactor_backtest_demo.py`: comparison-report claims include the unchanging-price counts.
- `reports/demo_v0.md` and `reports/synthetic_multifactor_backtest_demo.md`: official frozen-config reports now include the counts. The official synthetic panels have zero unchanging-price segments.
- `README.md`, `docs/current_roadmap.md`, `docs/engineering_log.md`, `CHANGELOG.md`, `EXPERIMENT_LOG.md`, `docs/repo_map.md`: M3-06 status and English prose updates.

## Tests

Focused tests passed:

- `python -m pytest -q tests/test_unchanging_price.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py tests/test_bar_integrity.py tests/test_source_row_lag.py tests/test_dividend_policy.py tests/test_broader_windows.py tests/test_backtest_timing_contract.py` — 257 passed, 2 skipped.
- CI-baseline `python -m pytest -q` — 2850 passed, 2 skipped.
- `python -m ruff check .`
- `python -m compileall -q src tests research lean`
- `git diff --check`

Covered behavior:

- Frozen Demo v0 config remains seed 20260521, 20 assets, 756 rows, lookback 252, skip 21, ME, top_n 5, 10 bps, 0 slippage.
- A fixture with a known flat run is counted; prices after reporting match the input bytes.
- A strictly moving panel reports zero segments.
- Demo v0 and M3-01 write the counts and keep every supplied bar.
- Existing Demo v0, M3-01, M3-02, M3-03, M3-04, and M3-05 tests still pass.

## Remaining Limits

- M3-06 is a synthetic unchanging-price diagnostic. Official commands keep the frozen 756-row config.
- Calendar-alignment infrastructure, invented-session detection, and event-level dividend and split reconciliation remain later Milestone 3/4 layers.
- All-Attempt Case Logging remains lightweight demo logging, distinct from charter Stage 4 experiment/trial-ledger accounting.
- Private data, brokerage, orders, paper/live trading, new calendars, and new cost engines stay out of scope.
