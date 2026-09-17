# M3-07 Attempt Report

M3-07 implements calendar-day span reporting and invented-session refusal
for Demo v0 and the M3-01 synthetic three-factor demo.

Worktree: `efr-m3-07-calendar-20260917`.
Branch: `codex/m3-07-calendar-alignment-20260917`.
Baseline HEAD: `e7098e6eea39a35ef4a40f20aa554f6fd7a9e290`.

## Behavior and evidence

- `report_calendar_day_spans` measures
  `(next.normalize() - current.normalize()).days` for consecutive observed
  timestamps. It reports the number of pairs greater than one day and the
  maximum span; an index with zero pairs reports zero for both fields.
- Mon/Wed/Fri yields 2 pairs greater than one day and a maximum of 2 days.
  Consecutive calendar days yield 0 such pairs and a maximum of 1 day.
  Empty, singleton, same-day intraday, normalized multi-day, and Friday-Monday
  fixtures retain their supplied timestamp bytes.
- Both run functions accept `observed_index` as an optional source declaration.
  Omission declares the generated price index as source. Both pipelines reuse
  `refuse_inserted_source_rows`; the existing helper also refuses dropped or
  reordered source rows. A planted extra date is refused through each run
  function, preserving the panel, source index, previous report, and failure
  logging. Membership uses exact timestamps; span measurement uses normalization.
- Integration tests capture the complete price panel passed to the backtester.
  Every supplied observed bar remains present, including Friday-Monday bars.
  Demo v0's established evaluation slice still follows its warm-up period.
- Official commands succeeded with the frozen 756-row configs. Both reports
  record 151 pairs greater than one calendar day and a maximum of 3 days.
  Byte comparison against baseline confirms all other report content remains
  identical. Each official All-Attempt log retains its prior bytes and appends
  attempt 4 with started/success records.
- The `DEMO_V0_CONFIG` source expression is byte-identical to baseline:
  seed 20260521, 20 assets, 756 rows, lookback 252, skip 21, ME, top_n 5,
  10 bps cost, and 0 slippage.

## Changed files

- `research/source_row_lag.py`: shared span report and current scope prose.
- `research/demo_v0.py`, `research/synthetic_multifactor_backtest_demo.py`:
  declared-source refusal and span counts in report generation.
- `tests/test_calendar_day_spans.py`: 15 deterministic span, preservation,
  pipeline, reporting, and planted-date refusal cases.
- `tests/test_demo_v0.py`, `tests/test_synthetic_multifactor_backtest_demo.py`:
  source-wiring assertions now require the reused refusal helper.
- `reports/demo_v0.md`, `reports/synthetic_multifactor_backtest_demo.md`:
  regenerated official synthetic reports.
- `reports/demo_v0_attempts.jsonl`,
  `reports/synthetic_multifactor_backtest_demo_attempts.jsonl`:
  appended official command outcomes.
- `CHANGELOG.md`, `README.md`, `EXPERIMENT_LOG.md`, `docs/current_roadmap.md`:
  current M3-07 behavior and remaining-work wording.
- `docs/engineering_log.md`, `reports/m3_07_attempt.md`: implementation,
  validation, failed-fixture, and ablation evidence.
- `docs/repo_map.md`: regenerated map includes the added test file.

## Validation commands and outcomes

All commands ran from this worktree with the existing interpreter:

```sh
M3_PYTHON=/Users/rhapsoul/Documents/Codex/projects/efr-demo-v0-20260916/.venv/bin/python
PYTHONPATH=src "$M3_PYTHON" -m pytest -q tests/test_calendar_day_spans.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py tests/test_bar_integrity.py tests/test_source_row_lag.py tests/test_dividend_policy.py tests/test_broader_windows.py tests/test_unchanging_price.py tests/test_backtest_timing_contract.py tests/test_official_report_paths.py
PYTHONPATH=src "$M3_PYTHON" -m pytest -q
"$M3_PYTHON" -m ruff check research/source_row_lag.py research/demo_v0.py research/synthetic_multifactor_backtest_demo.py tests/test_calendar_day_spans.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py
PYTHONPATH=src "$M3_PYTHON" -m research.demo_v0
PYTHONPATH=src "$M3_PYTHON" -m research.synthetic_multifactor_backtest_demo
"$M3_PYTHON" scripts/repo_map.py
git diff --check
```

Baseline focused tests, excluding the new file: **259 passed, 2 skipped**.
Initial expanded focused run: **3 failed, 271 passed, 2 skipped**. Demo v0's
three-row integration fixture had only one measured return after warm-up;
tracking error requires two. A preceding adjacent warm-up date corrected the
integration fixture while preserving the expected span counts and all guards.
The exact Mon/Wed/Fri unit fixture remains three timestamps.

Final focused run: **274 passed, 2 skipped**. Full suite: **2867 passed,
2 skipped, 1 warning**. Both skips reflect platform `longdouble` precision.
The warning records undefined Spearman correlation on a constant input.
Ruff, official commands, map regeneration, and whitespace checks passed.

## Ablation

The implementation source files were SHA-256 checked before and after three
separate Python subprocesses. Each subprocess replaced one function in memory,
then called `pytest.main` with `-q --tb=no`. Disk source bytes stayed identical.

| Isolated removal | Selection | Outcome | Decision |
| --- | --- | --- | --- |
| Replace `source_row_lag.report_calendar_day_spans` with a function returning `CalendarDaySpanReport(0, 0)` | `tests/test_calendar_day_spans.py` | 10 failed, 5 passed | Keep span measurement |
| Replace `demo_v0.refuse_inserted_source_rows` with a function returning its input | `tests/test_calendar_day_spans.py::test_demo_refuses_invented_session_and_preserves_input[demo_v0]` | 1 failed | Keep Demo v0 refusal |
| Replace `synthetic_multifactor_backtest_demo.refuse_inserted_source_rows` with a function returning its input | `tests/test_calendar_day_spans.py::test_demo_refuses_invented_session_and_preserves_input[m3_01]` | 1 failed | Keep M3-01 refusal |

Each bypassed refusal allowed the planted-date run to succeed, causing the
expected-refusal assertion to fail. The span removal lost required counts in
unit and report tests. The final focused and full suites verify the retained
implementation. Existing source-index validation is reused through the refusal
helper, keeping one source-validation call per pipeline at that boundary.

The supported ablation conclusion retains both features. The implementation
adds one small report type and one span helper to the existing source-row
module. Span measurement traverses adjacent timestamps. The experiment assesses
behavior and correctness; runtime and allocation costs remain unbenchmarked.
Market calendars and Friday-Monday filtering have zero implementation footprint.

## Limits and next gate

Spans disclose omitted-observation gaps in wall time. Session and holiday
status remains unverified. Official synthetic generators declare their own
source index; source membership alone establishes consistency with that
index. Remaining Milestone 3 work is event-level dividend/split reconciliation.
Earlier dated engineering entries and prior attempt reports retain historical
checkpoint wording, including any historical language exceptions.

The slice remains synthetic and diagnostic. New public commands, exchange or
holiday calendars, date insertion/filling/clipping/dropping/repair, private
data, brokerage, and profitability claims remain outside its scope. Delivery
ends with the authorized local implementation commit. The coordinator card
`reports/m3_07_card.md` remains untracked and excluded from that commit.
