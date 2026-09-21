# GROK_REVIEW: Stage B/C CI acceleration candidate `ccaf59c`

**Verdict: PASS (MATERIAL: 0)**

- Reviewer seat: `GROK_REVIEW` (Grok 4.6 Extra High, independent formal review)
- Exact candidate: `ccaf59cf5c800c0dfc484dbbbb0beefe3cb0e00b` (`ccaf59c`, `docs(ci): record hosted CI verification for Stage B/C acceleration`)
- Kernel commit included in this candidate: `b08c3eba6b5b0ccd70631b1233147a9e2086cea2` (`perf(ci): accelerate diagnostic kernels and split validation lanes`)
- Tree: `a42e000090c19d838fe2b2905b340b96d8c9232b`
- Stage A base: `431cdd2a32e1a5d94f1d0f139005750ee64b2da4`
- Review root: `/private/tmp/efr-ci-review-grok-ccaf59c` (detached HEAD at the exact candidate)
- Producer worktree was not used as the review root
- Design card: `coord/card_ci_acceleration_and_optimization.md`
- Producer report: `coord/reports/ci_acceleration_stage_bc_impl.md`
- Coordination standard read from `/Users/rhapsoul/Documents/Codex/Standards/herdr_pi_coordinator_v7_two_file/` (`coordinator.md`, `routing_table.json`; table status `TEMPLATE_NOT_ACTIVE`)
- Date: 2026-09-21
- Review posture: read-only on this clean root; this report is the only authored deliverable

This body reviews the exact candidate bytes named above. Coverage is Stage B kernel acceleration (`ts_rank`, bounded signal validation, held-asset returns, accounting output storage), Stage C core/diagnostics lanes with the required `Python validation` gate, research-safety of the accounting path, and independent local execution of both CI lanes.

Evidence ceiling is workflow, test-infrastructure, and simulation-kernel change. Official diagnostic artifacts under `reports/` are unchanged versus Stage A. This review records no profitability claim.

## Scope

`ccaf59c` records hosted verification on top of kernel commit `b08c3eb`. The executable kernel, tests, and workflow are identical between `b08c3eb` and `ccaf59c`. Delta versus Stage A `431cdd2`: 10 files, `+534 / −99`.

| Path | Role |
| --- | --- |
| `src/features/operators.py` | Native `Rolling.rank(pct=True)` for `average`/`min`/`max`; fallback apply path retained |
| `src/backtest/portfolio.py` | Column-array signal validation, numeric held-return path, array-backed long-only outputs |
| `src/backtest/long_short.py` | Array-backed outputs; diagnostic price conversion on rebalance dates only |
| `.github/workflows/ci.yml` | Stage C matrix lanes plus required `Python validation` gate |
| `tests/test_operators.py` | Rank oracle, causal prefix, empty/duplicate-axis refusals |
| `tests/test_backtest_timing_contract.py` | Empty-axis validation, mixed scalars, native/scalar held-return equality |
| `tests/test_campaign_conformance.py` | Lane/gate pins and success-only gate probe |
| `CHANGELOG.md` | Unreleased Changed notes |
| `docs/engineering_log.md` | 2026-09-21 Stage B/C process record |
| `coord/reports/ci_acceleration_stage_bc_impl.md` | Producer assessment, ablation, and hosted measurement |

`pyproject.toml` is unchanged versus Stage A. Runtime dependency declarations, pytest `addopts = "-ra"`, synthetic panel sizes, factor inventory, trial retention, official report fixtures, and timing-contract names remain the existing contracts.

## Coverage

| Check | Result on `ccaf59c` |
| --- | --- |
| Exact-head identity | HEAD `ccaf59cf5c800c0dfc484dbbbb0beefe3cb0e00b`. Tracked tree matches HEAD. Untracked review interpreter only: `.venv`. |
| Kernel vs docs split | `git diff --name-only b08c3eb..ccaf59c` is `CHANGELOG.md`, `coord/reports/ci_acceleration_stage_bc_impl.md`, `docs/engineering_log.md`. |
| Native `ts_rank` | `src/features/operators.py:335-338` uses `panel.rolling(window=window, min_periods=window).rank(...)` for `average`/`min`/`max`. `first` and `dense` keep the Series-apply path. |
| Signal validation | `_validate_bounded_signal_values` walks column `.array` values in row-major order and writes a float buffer. First-invalid cell order is preserved. |
| Held-asset returns | Numeric path requires aligned unique float holdings and numeric numpy dtypes; other representations keep the scalar reader. Unheld assets stay at zero return. |
| Accounting outputs | Both engines allocate numpy buffers, keep pretrade/post-cost solvency guards in the existing order, and construct public pandas objects after the loop. |
| Stage C workflow | Job `test-lanes` matrix `core`/`diagnostics`; job `validation` named `Python validation`; `needs: [test-lanes]`; `if: ${{ always() }}`; `test "$LANES_RESULT" = success`. |
| Thread clamps and xdist | Six native-thread keys equal `"1"`; pytest `-n 2 --dist worksteal --max-worker-restart=0`; fail-closed `git diff --exit-code HEAD -- .`; per-lane artifacts. |
| Lane partition | Collect-only: core 3,792 unique, diagnostics 125 unique, intersection 0, union 3,917, union equals full collection. |
| Hosted run 35630871052 | Independent GitHub API read: `head_sha` `b08c3eb`, conclusion `success`, created `2026-09-21T17:15:41Z`, updated `2026-09-21T17:19:47Z` (246 s). Jobs: Tests (core) 144 s success, Tests (diagnostics) 236 s success, Python validation 3 s success. |
| Deterministic QA | See QA table. Core 3,790 passed + 2 skipped in 38.66 s; diagnostics 125 passed in 134.83 s. |

## Stage B research-safety

### Trailing rank

`validate_panel_data` still rejects empty panels, duplicate dates, unsorted dates, duplicate columns, and non-numeric dtypes, then copies to float. The native branch uses a trailing rolling window with `min_periods=window`, so date `t` sees only the window ending at `t`. Independent review probe: for methods `average`, `min`, and `max` on a 40×3 panel with interior NaNs and a constant column, native output equals

```python
data.rolling(10, min_periods=10).apply(
    lambda row: row.rank(method=method, ascending=True, pct=True).iloc[-1],
    raw=False,
)
```

with `check_exact=True`. Mutating rows after index 30 leaves the first 30 native ranks unchanged.

Added tests in `tests/test_operators.py` cover methods `average`/`min`/`max`/`first`/`dense`, both sort directions, windows 1/2/5/20/40, NaNs, a constant column, extreme values, named mixed-label axes, input immutability, causal prefix mutation, empty-axis refusal, and duplicate-axis refusal.

### Lag-1 execution and guards

Long-only and long-short still compute held returns from previously held weights and the previous/current close pair before valuation, drift, or liquidation. Signal lag remains `shift(signal_lag_periods)`. Execution-price validation still runs on nonzero frozen trade legs at the current close. Pretrade gross and post-cost equity refusals keep their predicates and call order.

Long-short quantile diagnostics that convert every asset price with `_read_positive_price` now run only when `date in rebalance_dates`. Executable P&L on that interval still uses `_calculate_held_asset_returns` with `missing_price_policy="raise"` before that block. Dollar-neutrality and gross-leverage checks on the invested target are unchanged (`target_exposure_invalid`, `position_cap_infeasible`).

Independent probe: native held-return path matches the object-dtype scalar path exactly on mixed held/unheld assets, including an unheld `inf` price that stays at zero return.

### Output construction

Long-only turnover on a rebalance row is `float(signed_trades.abs().sum())`; non-rebalance rows stay 0.0. That matches the previous `trade_weights.loc[date].sum()` after writing `signed_trades.abs()` only on rebalance rows.

Long-short long/short legs are `np.where(net < 0, 0, net)` and `-np.where(net > 0, 0, net)`. Independent probe against `Series.clip(lower=0)` / `-clip(upper=0)` matches values and signed-zero bits, including `-0.0` holdings.

Public result objects are labeled pandas frames/series with the same names as before (`gross_return`, `return`, `turnover`, cost columns, `equity`). Official `reports/` files are absent from `431cdd2..HEAD`.

## Stage C workflow fidelity

`.github/workflows/ci.yml` keeps Stage A triggers, `contents: read`, concurrency, native-thread `env`, `defaults.run.shell: bash`, campaign-safety comments, checkout, setup-python 3.11 with `cache-dependency-path: pyproject.toml`, `--prefer-binary` install, evidence recording, fail-closed `git diff`, and `actions/upload-artifact@v4`.

The jobs mapping follows card section 8:

| Contract | Candidate |
| --- | --- |
| Matrix | `lane: [core, diagnostics]`, `fail-fast: false`, `max-parallel: 2` |
| Core selection | `tests --ignore=tests/test_multifactor_diagnostic_mvp.py --ignore=tests/test_m3_10_hardening.py` |
| Diagnostics selection | those two modules only |
| Unknown lane | `exit 2` |
| Lint/compile/build | core lane only (separate steps; card shows one combined step) |
| Gate | job ID `validation`, name `Python validation`, `timeout-minutes: 5`, `needs: [test-lanes]`, `if: ${{ always() }}`, `test "$LANES_RESULT" = success` |
| Artifact name | `ci-evidence-${{ matrix.lane }}-${{ github.run_id }}-${{ github.run_attempt }}` |

`tests/test_campaign_conformance.py` pins the safety phrases, a single `python -m pytest -q` substring, xdist flags, the six thread keys, both ignore paths, the diagnostics selection tuple, matrix/fail-fast/max-parallel, per-lane artifact names, and the gate `needs`/`always()`/`LANES_RESULT` expressions. `test_ci_required_gate_accepts_only_successful_lanes` executes the gate command under `success`/`failure`/`cancelled`/`skipped`/empty and accepts only `success`.

New tests enter core by default because core discovers `tests` and ignores only those two files.

## Deterministic QA

Commands ran on exact `ccaf59cf5c800c0dfc484dbbbb0beefe3cb0e00b` with `/private/tmp/efr-ci-review-grok-ccaf59c/.venv/bin/python` and `PYTHONPATH=src:.`. Native thread variables were set to `1` for pytest.

Review interpreter: CPython 3.12.13, pytest 9.1.1, pytest-xdist 3.8.0, NumPy 2.5.3, pandas 3.0.6. CI remains Python 3.11 on `ubuntu-latest`. Local elapsed times are compatibility evidence on this machine.

```
PYTHONPATH=src:. .venv/bin/python -m ruff check .
PYTHONPATH=src:. .venv/bin/python -m compileall -q src tests research lean
PYTHONPATH=src:. .venv/bin/python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 \
  tests/test_operators.py tests/test_backtest_timing_contract.py tests/test_campaign_conformance.py \
  tests/test_long_short_backtest.py tests/test_backtest_portfolio.py tests/test_m3_10_hardening.py \
  tests/test_campaign_runner.py
PYTHONPATH=src:. .venv/bin/python -m pytest -q --collect-only tests \
  --ignore=tests/test_multifactor_diagnostic_mvp.py --ignore=tests/test_m3_10_hardening.py
PYTHONPATH=src:. .venv/bin/python -m pytest -q --collect-only \
  tests/test_multifactor_diagnostic_mvp.py tests/test_m3_10_hardening.py
PYTHONPATH=src:. .venv/bin/python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 \
  tests --ignore=tests/test_multifactor_diagnostic_mvp.py --ignore=tests/test_m3_10_hardening.py
PYTHONPATH=src:. .venv/bin/python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 \
  tests/test_multifactor_diagnostic_mvp.py tests/test_m3_10_hardening.py
```

| Command | Result |
| --- | --- |
| `ruff check .` | All checks passed |
| `compileall -q src tests research lean` | passed (exit 0) |
| `git diff --check 431cdd2..HEAD` | clean |
| Three workflow `run: \|` bodies via `bash -n` | exit 0 |
| Independent rank/held-return/clip probes | exact matches as described above |
| Key suites including M3-10 causal hardening | 539 passed, 2 skipped in 49.54 s |
| Collect-only core / diagnostics / full | 3,792 / 125 / 3,917 unique; disjoint exhaustive union |
| Core lane `-n 2 --dist worksteal` | 3,790 passed, 2 skipped, 3 warnings in 38.66 s |
| Diagnostics lane same flags | 125 passed, 20 warnings in 134.83 s |
| JUnit union | 3,917 unique node IDs, 0 duplicates, 0 failures |
| `git diff --exit-code HEAD -- .` after both lanes | exit 0 |

The two skips are the existing ARM `longdouble` / `clongdouble` cases in `tests/test_backtest_timing_contract.py:1221`. Longest diagnostics JUnit call in this review: 80.109 s (`test_multifactor_diagnostic_official_report_table_matches_default_fixture`). That case still executes the 756×50 official fixture. The M3-10 integrated future-label/future-price prefix test passed (45.861 s).

Candidate SHA-256 (review-root bytes):

| File | SHA-256 |
| --- | --- |
| `src/features/operators.py` | `d6324abce5e40e416c67b7ef4ebdd2326e1a41c5eae3ae7976821d62c20ded2f` |
| `src/backtest/portfolio.py` | `8ce16ab171734c49621c246b0f2019aba82f317ed0864fa6f29937af2c92282e` |
| `src/backtest/long_short.py` | `28b720a88c459f28d48f9385347e2db863926764cbfd4f06177ca732d3e89cfe` |
| `.github/workflows/ci.yml` | `e4e5958ed6b4b4b2f293ca7f3ca42a8d7812e044e7b287bcc4791d8111281307` |

## Findings

MATERIAL: none.

### ADV-BC-1 — Hosted 5–8 minute acceptance is a single verified run

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `ccaf59cf5c800c0dfc484dbbbb0beefe3cb0e00b`
- Claim: Card section 10 requires that all of three initial comparable warm runs finish within eight minutes, and that a warm-only result be labelled warm-only. Cold-cache correctness has its own eight-minute clause.
- Evidence: Independent GitHub API read of [run 35630871052](https://github.com/minqiyang/equity-factor-research/actions/runs/35630871052) confirms conclusion `success` on head `b08c3eb` in 246 s (4m06s) from `created_at` to `updated_at`, with required check `Python validation` successful. The producer report and engineering log describe this as the measured target on this run. This review found one completed hosted success for that kernel SHA. Cache-hit versus cold-cache classification is not recorded on the candidate's hosted table. `ccaf59c` adds documentation only; it does not add a second or third warm run.
- Impact: Kernel correctness and lane coverage on this candidate stand on the QA table. The three-run warm-acceptance band and cold-cache label in the design card remain open operational measurements for later heads.
- Resolution: Record two additional comparable warm runs and one labelled cold-cache run against the then-current head, or narrow the card's three-run sentence to match a single-run measurement policy.

## Residual notes

- Local core/diagnostics elapsed times (38.66 s / 134.83 s) are this machine's workload evidence. Hosted diagnostics pytest 194.52 s in the producer table is the runner measurement for `b08c3eb`.
- Diagnostic RSS 466,516 KiB in the producer hosted table is below the card's 5.5 GB two-worker budget. This review did not re-measure Linux cgroup `memory.peak`.
- Card section 8 shows one combined core lint/compile/build step. The candidate uses four separately gated steps. Commands and core-only gating match the card.

## Verdict

**PASS (MATERIAL: 0)**

Stage B/C on `ccaf59cf5c800c0dfc484dbbbb0beefe3cb0e00b` keeps trailing-window ranks, lag-1 held-price accounting, solvency guards, and dollar-neutral long-short targets, while shipping the card's two-lane workflow behind required check `Python validation`. Independent local lanes collected 3,917 unique cases with an empty intersection and passed 3,915 with the two existing ARM precision skips. Hosted run 35630871052 on included kernel `b08c3eb` completed successfully in 246 s.

OPEN advisories: ADV-BC-1. MATERIAL count is 0.

This report records the exact-head review of `ccaf59cf5c800c0dfc484dbbbb0beefe3cb0e00b`.
