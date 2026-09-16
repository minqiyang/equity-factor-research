# M3-01 Attempt Report

Worktree: `efr-m3-01-20260916` on branch `codex/m3-01-multifactor-backtest-20260916`.
Command: `python -m research.synthetic_multifactor_backtest_demo`.
This attempt implements the M3-01 synthetic three-factor backtest demo in this worktree.

## Files

- `research/synthetic_multifactor_backtest_demo.py`: M3-01 command. Reuses Demo v0 synthetic price dates and assets via `generate_synthetic_prices`, the existing factor generator and 0.50 / 0.30 / 0.20 weights, existing `cross_sectional_winsorize_factor` / `cross_sectional_zscore_factor` / `combine_factors` helpers, `run_long_only_backtest`, `after_close_signal_next_observed_close_v1`, undivided absolute-trade turnover, explicit 10 bps cost, and explicit 0 bps slippage labeled diagnostic. Monthly top-five selection. Writes `reports/synthetic_multifactor_backtest_demo.md` and appends All-Attempt Case Logging with a start record before computation.
- `tests/test_synthetic_multifactor_backtest_demo.py`: deterministic scores/holdings/metrics/report, combination check, mismatched-axis and nonfinite refusal without silent repair, timing/cost claims, and All-Attempt success/failure/interrupt plus start-before-compute.
- `reports/synthetic_multifactor_backtest_demo.md`: comparison report from the official frozen run.
- `reports/synthetic_multifactor_backtest_demo_attempts.jsonl`: All-Attempt Case Logging with the official start and success records (attempt 1).
- `README.md`, `docs/current_roadmap.md`, `docs/engineering_log.md`, `CHANGELOG.md`, `EXPERIMENT_LOG.md`, `docs/repo_map.md`: M3-01 status and English prose updates.
- `python -m research.demo_v0` remains the official Demo v0 command. `python -m research.synthetic_multifactor_workflow_demo` remains the feature-only workflow.

## Tests

Focused tests passed:

- `.venv/bin/python -m pytest -q tests/test_synthetic_multifactor_backtest_demo.py tests/test_demo_v0.py tests/test_synthetic_multifactor_workflow_demo.py tests/test_combine.py tests/test_normalize.py` — 107 passed.
- `.venv/bin/python -m ruff check research/synthetic_multifactor_backtest_demo.py tests/test_synthetic_multifactor_backtest_demo.py`
- `.venv/bin/python -m compileall -q src research tests`
- `git diff --check`
- `PYTHONPATH=src .venv/bin/python -m research.synthetic_multifactor_backtest_demo` wrote the comparison report and appended started then success for attempt 1.

Covered behavior:

- Frozen config copies Demo v0 price fixture fields (seed 20260521, 20 assets, 756 rows, start 2021-01-01, ME, top_n 5, 10 bps, 0 slippage) and workflow weights 0.50 / 0.30 / 0.20.
- Generated prices match the Demo v0 synthetic price fixture.
- Combined score equals `combine_factors` on z-scored panels and equals the explicit weighted sum.
- Report includes benchmark, timing contract name, 10 bps cost, 0 bps slippage, diagnostic zero-cost/zero-slippage label, and the artificial-panel caveat.
- Mismatched factor dates or assets raise before report replacement. NaN and inf factor values raise. Silent reindex, fill, clip, drop, or repair is refused.
- A start record is written before computation. Failures and catchable `KeyboardInterrupt` / `SystemExit` remain in the log. If the attempt log cannot begin, the comparison report is left in place.
- Existing Demo v0 and legacy feature-only multifactor tests still pass.

## Remaining Limits

- M3-01 is an exploratory synthetic three-factor backtest. It is a workflow diagnostic and makes no profitability claim.
- The three synthetic panels are artificial quality, reversal, and momentum fixtures. They are distinct from Demo v0 12-1 momentum and from fundamentals.
- Zero slippage remains labeled diagnostic.
- All-Attempt Case Logging is lightweight demo logging in `reports/synthetic_multifactor_backtest_demo_attempts.jsonl`. It is not charter Stage 4 experiment/trial-ledger accounting.
- `python -m research.demo_v0` remains the official Demo v0 command.
- `python -m research.synthetic_multifactor_workflow_demo` remains the feature-only workflow.
- Remaining Milestone 3 work covers broader historical windows and data-cleaning layers.
- Private data, brokerage, orders, paper/live trading, new calendars, and new cost engines stay out of scope.
- This worktree implements the slice. GitHub publication is outside this card.
