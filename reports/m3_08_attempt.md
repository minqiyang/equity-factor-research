# M3-08 Attempt Report

M3-08 implements supplied-event date membership and event-table disclosure
for Demo v0 and the M3-01 synthetic three-factor demo.

Worktree: `efr-m3-08-events-20260917`.
Branch: `codex/m3-08-event-reconciliation-20260917`.
Baseline HEAD: `e033e9d7a55607e0deb0555e759533606efc940b`.

## Behavior and evidence

- Both existing runners accept an optional `event_table` DataFrame whose
  `DatetimeIndex` contains event dates. The existing `dividend_policy` module
  checks every timestamp against the declared `observed_index`. Omission of
  that source declaration retains the generated price index as source.
- Membership uses exact timestamps. Dates before or after the source, an
  absent weekend date, an omitted weekday, and an absent intraday timestamp
  are refused. An observed weekend timestamp is accepted. Missing event dates
  and untyped indexes are refused. Repeated dates support multiple events on
  one source row; an empty table with a `DatetimeIndex` passes vacuously.
- Event columns remain opaque metadata. Tests plant dividend values and split
  factors, capture the prices passed to the backtester, and compare holdings,
  gross and net returns, equity, turnover, and costs with the no-table run.
  Prices, event tables, and source indexes remain unchanged. The existing
  PIT-007 cash-dividend overlay refusal remains active.
- Refused runs preserve the previous report and append started/failure
  All-Attempt records. Successful supplied-table reports describe date
  membership and explicitly defer full economic reconciliation.
- Official commands supply no independent event table. Both official reports
  state: "Event-level reconciliation was not performed because no independent
  event table was supplied." Each official command appended attempt 5 with
  started/success records, preserving the existing log prefix byte-for-byte.
- Both generated reports differ from the baseline only in the event-policy
  sentence. All metrics and relative log paths remain byte-identical.
  The `DEMO_V0_CONFIG` source expression remains byte-identical: seed 20260521,
  20 assets, 756 rows, lookback 252, skip 21, ME, top_n 5, 10 bps cost,
  and 0 slippage.

## Changed files

- `research/dividend_policy.py`: event-date membership guard beside PIT-007.
- `research/demo_v0.py`, `research/synthetic_multifactor_backtest_demo.py`:
  optional table wiring and report disclosure.
- `tests/test_event_date_membership.py`: 21 deterministic membership,
  malformed-input, preservation, reporting, and official-command cases.
- `reports/demo_v0.md`, `reports/synthetic_multifactor_backtest_demo.md`:
  regenerated official reports with explicit event-table limitations.
- `reports/demo_v0_attempts.jsonl`,
  `reports/synthetic_multifactor_backtest_demo_attempts.jsonl`:
  appended official attempt outcomes.
- `CHANGELOG.md`, `docs/engineering_log.md`, `docs/current_roadmap.md`:
  implementation evidence and remaining economic-reconciliation scope.
- `docs/repo_map.md`: regenerated after adding the test file.
- `reports/m3_08_attempt.md`: local attempt and ablation evidence.

## Validation commands and outcomes

Commands ran from this worktree using the owner-specified Python 3.12.14:

```sh
M3_PYTHON=/Users/rhapsoul/Documents/Codex/projects/efr-demo-v0-20260916/.venv/bin/python
PYTHONPATH=src "$M3_PYTHON" -m pytest -q tests/test_calendar_day_spans.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py tests/test_bar_integrity.py tests/test_source_row_lag.py tests/test_dividend_policy.py tests/test_broader_windows.py tests/test_unchanging_price.py tests/test_backtest_timing_contract.py tests/test_official_report_paths.py
PYTHONPATH=src "$M3_PYTHON" -m pytest -q tests/test_event_date_membership.py -k 'not official_reports'
PYTHONPATH=src "$M3_PYTHON" -m research.demo_v0
PYTHONPATH=src "$M3_PYTHON" -m research.synthetic_multifactor_backtest_demo
PYTHONPATH=src "$M3_PYTHON" -m pytest -q tests/test_event_date_membership.py tests/test_calendar_day_spans.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py tests/test_bar_integrity.py tests/test_source_row_lag.py tests/test_dividend_policy.py tests/test_broader_windows.py tests/test_unchanging_price.py tests/test_backtest_timing_contract.py tests/test_official_report_paths.py
PYTHONPATH=src "$M3_PYTHON" -m pytest -q
"$M3_PYTHON" -m ruff check .
"$M3_PYTHON" -m compileall -q src tests research lean
"$M3_PYTHON" scripts/repo_map.py
git diff --check
```

Baseline focused tests: **274 passed, 2 skipped**. Initial new cases:
**19 passed, 2 deselected**. Expanded focused suite: **295 passed, 2 skipped**.
Full suite: **2888 passed, 2 skipped, 1 warning** in 39.33 seconds. Both skips
reflect platform `longdouble` precision. The warning records undefined
Spearman correlation on a constant input. Ruff, compilation, official
commands, map regeneration, and whitespace checks passed.

## Ablation

Four isolated subprocesses replaced one imported guard with
`lambda *args, **kwargs: None`, then called `pytest.main` with `-q --tb=no`.
The three implementation source files were SHA-256 checked before and after;
all disk source hashes remained identical. Each removal returned exit 1.

| Isolated removal | Test selection | Outcome | Decision |
| --- | --- | --- | --- |
| `demo_v0.require_event_date_membership` | New test file, `-k 'absent_event_date and demo_v0'` | 4 failed, 17 deselected | Retain event-date refusal |
| `synthetic_multifactor_backtest_demo.require_event_date_membership` | New test file, `-k 'absent_event_date and m3_01'` | 4 failed, 17 deselected | Retain event-date refusal |
| `demo_v0.refuse_cash_dividend_overlay` | `tests/test_demo_v0.py::test_demo_v0_refuses_cash_dividend_overlay` | 1 failed | Retain overlay refusal |
| `synthetic_multifactor_backtest_demo.refuse_cash_dividend_overlay` | `tests/test_synthetic_multifactor_backtest_demo.py::test_multifactor_demo_refuses_cash_dividend_overlay` | 1 failed | Retain overlay refusal |

Each bypass admitted a prohibited input and failed its expected-refusal
assertion. The retained implementation passes the focused and full regression suites.
The supported ablation outcome keeps both guards. One small helper in the
existing policy module supplies the membership check; an adjustment engine
has zero implementation footprint. This experiment covers M3-08 behavior
and correctness. Runtime and allocation costs remain unbenchmarked.

## Limits and next gate

Date membership establishes consistency with the declared source index.
Event amounts, split economics, adjustment lineage, and provider completeness
remain unverified. Full economic dividend/split reconciliation against
independent events remains a separately scoped Milestone 3/4 task.
The official reports record the absence of an independent event table.

This slice remains synthetic and diagnostic. Public commands and frozen
configuration remain unchanged. Prices retain their supplied values; split
application, price rebuilding, holiday calendars, `asfreq` filling, private
data, brokerage, and profitability claims stay outside this implementation.
Historical logs and prior attempt reports retain their original checkpoint
wording and any historical language exceptions.

Delivery ends at the local implementation commit on the requested branch.
`reports/m3_08_card.md` stays untracked and excluded from the commit. The
owner's scope ends before GitHub publication or work in another worktree.
