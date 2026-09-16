# DEMO-V0-001 Attempt Report

Worktree: `efr-demo-v0-20260916` on branch `codex/demo-v0-20260916`.
Command: `python -m research.demo_v0`.
This attempt implements the official synthetic vertical slice in this worktree.

## Files

- `research/demo_v0.py`: official Demo v0 command. Reuses `calculate_12_1_momentum`, `run_long_only_backtest`, `after_close_signal_next_observed_close_v1`, undivided absolute-trade turnover, explicit 10 bps cost, explicit 0 bps slippage, and frozen `SyntheticDemoConfig` values (seed 20260521, 20 assets, 756 rows, lookback 252, skip 21, ME, top_n 5). Writes `reports/demo_v0.md` and appends All-Attempt Case Logging.
- `research/synthetic_momentum_demo.py`: docstring marks this module as the legacy diagnostic. Frozen defaults stay the source copied into Demo v0.
- `tests/test_demo_v0.py`: deterministic tests for the command, report claims, timing/cost strings, synthetic-only constraint, and a failed attempt that remains in the log.
- `reports/demo_v0.md`: comparison report from the official frozen run.
- `reports/demo_v0_attempts.jsonl`: All-Attempt Case Logging with the official success record (attempt 1).
- `README.md`, `docs/current_roadmap.md`, `docs/engineering_log.md`, `docs/north_star.md`, `PROJECT_SPEC.md`, `CHANGELOG.md`, `EXPERIMENT_LOG.md`, `docs/repo_map.md`: Demo v0 status and English prose updates.

## Tests

Focused tests passed:

- `.venv/bin/python -m pytest -q tests/test_demo_v0.py tests/test_synthetic_momentum_demo.py tests/test_experiment_log.py tests/test_experiment_registry.py tests/test_project_structure.py` — 83 passed.
- `.venv/bin/python -m ruff check research/demo_v0.py tests/test_demo_v0.py research/synthetic_momentum_demo.py`
- `.venv/bin/python -m compileall -q src research tests`
- `git diff --check`
- `.venv/bin/python -m research.demo_v0` wrote the comparison report and appended the success attempt.

Covered behavior:

- Frozen config matches the listed `SyntheticDemoConfig` values.
- `main()` calls `run_demo_v0()` with no overrides.
- Report includes benchmark, timing contract name, 10 bps cost, 0 bps slippage, diagnostic zero-cost/zero-slippage label, and risk metrics.
- Source stays synthetic-only: `generate_synthetic_prices`, no CSV loader, no EODHD path.
- A later failing invocation (insufficient warm-up) is logged as `status=failure` while the earlier success remains visible.

## Remaining Limits

- Demo v0 is the synthetic vertical slice. It is a workflow diagnostic and makes no profitability claim.
- Zero slippage remains labeled diagnostic.
- All-Attempt Case Logging is lightweight demo logging in `reports/demo_v0_attempts.jsonl`. It is not charter Stage 4 experiment/trial-ledger accounting.
- `python -m research.synthetic_momentum_demo` remains a legacy diagnostic.
- Private data, brokerage, orders, paper/live trading, and new factors, calendars, or cost engines stay out of scope.
- Milestone 3 multi-factor work, Milestone 4 formal promotion, and presentation polish remain in the backlog.
- This worktree implements the slice. GitHub publication is outside this card.
