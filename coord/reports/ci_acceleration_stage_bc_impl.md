# CI Stage B/C assessment and implementation

Date: 2026-09-21. Delivery branch: `feat/ci-stage-bc-acceleration`.
Base: `431cdd2a32e1a5d94f1d0f139005750ee64b2da4` (Stage A, PR #250).

## Assessment and delivery status

Stage B and Stage C are feasible and complementary. The implemented solution combines native rolling ranks, faster scalar-preserving validation and accounting output storage, and two exhaustive CI lanes. Local validation passes all 3,917 collected cases: 3,915 passed and two platform-specific precision skips. All 3,819 original cases remain present. The longest diagnostic test fell from a freshly measured 218.774 seconds to 79.844 seconds, a 2.74× speedup. The diagnostics lane completes in 135.04 seconds locally.

Hosted CI confirms the target: [run 35630871052](https://github.com/minqiyang/equity-factor-research/actions/runs/35630871052), on PR #251 head `b08c3eba6b5b0ccd70631b1233147a9e2086cea2`, completed successfully in **4m06s** from run creation to completion. All 3,917 hosted cases passed with zero skips. The observed result beats the eight-minute upper target and the earlier 7.2-minute forecast. Independent review remains a merge gate.

The implementation ran in the isolated worktree `/private/tmp/efr-ci-stage-bc-431cdd2`, preserving the delivery root's unrelated untracked coordination files. The user brief explicitly assigns GPT direct verification and implementation. Changes affect accounting internals, so acceptance requires fresh independent review under the repository's CRITICAL lane. `structural: false`: public interfaces, research semantics, canonical data, and authority boundaries retain their existing contracts. This producer's validation constitutes implementation evidence.

## Baseline and critical path

The Stage A [GitHub run 35575413849](https://github.com/minqiyang/equity-factor-research/actions/runs/35575413849) finished its validation job in 20m04s. Its retained JUnit and resource artifacts establish:

| Measurement | Stage A hosted value |
| --- | ---: |
| Pytest wall time | 1,169.05 s |
| Sum of all test-case times | 2,284.338 s |
| Sum of diagnostics test-case times, W | 2,054.822 s |
| Longest diagnostics case, L | 646.495 s |
| Largest remaining diagnostics cases | 385.104, 348.761, 339.954, 328.994 s |
| Job overhead relative to reported pytest wall time | approximately 34.95 s |
| Process-tree CPU utilization | 197% |
| Maximum RSS reported by GNU time | 556,468 KiB |

The artifact's `nproc` output is 1 while the measured process-tree utilization is 197%. Native thread environment limits can affect processor-count reporting. The observed two-worker utilization supplies stronger scheduling evidence than interpreting that count as the runner's physical CPU inventory. This implementation keeps the measured two-worker configuration.

For two workers, the diagnostics lower bound is:

`T_diagnostics >= max(W / 2, L) = max(1,027.411, 646.495) seconds`.

Stage C alone therefore has a measured work floor of **17m07s**, before setup and scheduling. The brief's 10–13 minute estimate describes a longest-case constraint and understates the stronger total-work constraint. Moving core tests to another runner removes competition for workers; the unchanged diagnostics lane still exceeds eight minutes.

With a conservative 60-second allowance for setup, evidence upload and the final gate:

| Job target | Available test time | Necessary work reduction | Necessary L reduction |
| --- | ---: | ---: | ---: |
| 8 minutes | 420 s | at least 2.45× | at least 1.54× |
| 5 minutes | 240 s | at least 4.28× | at least 2.69× |

These are necessary conditions. Scheduling inefficiency and runner queues can increase elapsed time. Amdahl's Law also limits kernel-only improvements: `S = 1 / ((1-p) + p/k)`, where `p` is the optimized share and `k` its speedup. The baseline cProfile attributes 47.811 of 639.058 pipeline seconds to `ts_rank`, approximately 7.5%. Even eliminating that work entirely permits only about 1.08× overall speedup. Rank optimization alone cannot satisfy the target.

## Profile and selected implementation

The profile executes the unchanged official 756×50 fixture, all 62 factors, and the weighting comparisons. It records 156 books: 78 long-only and 78 long-short executions. Instrumentation substantially increases elapsed time, so profile seconds identify work distribution; uninstrumented measurements establish wall-clock improvements.

| Baseline profile component | Calls | Cumulative seconds |
| --- | ---: | ---: |
| Full diagnostic pipeline | 1 | 639.058 |
| Long-short backtests | 78 | 299.201 |
| Long-only backtests | 78 | 250.273 |
| Bounded signal validation | 156 | 185.453 |
| Held-asset return calculation | 113,880 | 92.971 |
| Long-only accounting path | 78 | 110.473 |
| `ts_rank` | 14 | 47.811 |

The validation and held-return rows are nested within the engine totals. Adding these overlapping rows would overstate their share. Together the two engines account for approximately 86% of instrumented pipeline time.

1. **Native rolling rank.** `src/features/operators.py::ts_rank` uses pandas `Rolling.rank(pct=True)` for `average`, `min`, and `max`. Existing validation, full-window missingness and trailing-window timing remain in place. `first`, `dense`, and unsupported-method behavior retain the existing Series-based path. The [pandas API](https://pandas.pydata.org/docs/reference/api/pandas.api.typing.Rolling.rank.html) documents the three native tie rules. A 756×50, window-20 microbenchmark measured 1.013 seconds for the original and 0.0102 seconds for the candidate, with exact frame equality. The rank-only full profile reduced rank time from 47.811 to 0.156 seconds; the remaining pipeline dominated elapsed time.
2. **Scalar-preserving signal traversal.** `_validate_bounded_signal_values` traverses per-column extension arrays in row order and writes a float output array. It retains the original exact scalar reader, IEEE NaN handling, first-invalid date/asset, and input ownership. Column-wise arrays preserve mixed integer/float/object identities before the existing float conversion. A 756×50 validation benchmark measured median 0.3294 seconds versus 0.0356 seconds.
3. **Held-return numeric path.** `_calculate_held_asset_returns` uses aligned native real numeric rows with unique asset labels and float holdings to calculate held returns in arrays. It preserves held-only validation, first-invalid asset and endpoint precedence, `zero_return` behavior, float conversion and zero values for unheld assets. The existing scalar path handles other representations and alignment cases. Both books retain their incoming-price, execution-price, pretrade-solvency and post-cost-solvency guards.
4. **Accounting output arrays.** Both engines allocate their output buffers once and construct the public labeled pandas objects after the accounting loop. Signal lagging, target selection, drift, summation formulas, costs, benchmark handling and guard order retain their existing implementations. Long-only turnover uses the same signed-trade absolute sum on trade rows and zero on other rows. Long-short bucket diagnostics execute on rebalance dates, where their results are consumed. Output clipping preserves signed zeros and missing-value behavior. The ordinary accounting state remains local to each invocation.
5. **Two CI lanes.** Core includes `tests` with the two diagnostics modules excluded, and runs lint, both compilation steps and distribution build. Diagnostics includes exactly `test_multifactor_diagnostic_mvp.py` and `test_m3_10_hardening.py`. Both use `-n 2 --dist worksteal --max-worker-restart=0`, six native-thread limits, per-lane resource/JUnit artifacts, and tracked-file checks. New test files automatically enter core.

The required `Python validation` job keeps its name and waits for the matrix using `needs: [test-lanes]` and `if: ${{ always() }}`. Its shell command accepts exactly `needs.test-lanes.result == success`. Tests execute the gate with success, failure, cancellation, skipped and empty results. The matrix uses `fail-fast: false` and `max-parallel: 2`; artifact names include the lane. PR, main-push and merge-group triggers remain present. The [GitHub workflow specification](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idneeds) defines dependency and always-run behavior. A live branch-protection read confirms the required context remains `Python validation`, Actions app 15368.

`pyproject.toml` retains its existing dependencies and serial pytest defaults. The implementation uses the installed NumPy, pandas and pytest-xdist capabilities. Test dimensions, assertions, tolerances, trial inventory, and official report expectations retain their original scope.

## Fixture caching assessment

Cross-test caching offers limited benefit for the dominant work and increases ownership complexity. The four large MVP runs exercise different configuration and output contracts. The hardening test independently perturbs future labels and future prices and observes causal prefixes. Reusing whole results across these calls would remove exercised behavior. Shared mutable panels would also require ownership and mutation invalidation rules.

The selected solution keeps each pipeline invocation independent. Production kernels become faster for CI and ordinary research execution. Fixtures, result objects and mutation-sensitive outputs receive fresh execution. No cache, session fixture, factor subset, reduced history, or result reuse was introduced.

## Deterministic validation

Environment: macOS ARM64, CPython 3.11.15, NumPy 2.4.6, pandas 3.0.6, SciPy 1.17.1, pytest 9.1.1 and pytest-xdist 3.8.0. Python and the core numerical package versions match the retained Stage A hosted dependency artifact. Native thread limits were set to one.

| Check | Result |
| --- | --- |
| Ruff over repository | PASS |
| Compile `src tests research lean` | PASS |
| Isolated sdist and wheel build | PASS |
| Ledger package contents | All 20 JSON/hash files byte-identical to source in both artifacts |
| actionlint 1.7.12 | PASS |
| `git diff --check` | PASS |
| Core lane, two-worker worksteal | 3,790 passed, 2 skipped, 39.74 s |
| Diagnostics lane, two-worker worksteal | 125 passed, 135.04 s |
| Collection union | 3,917 unique cases; zero missing or duplicate cases |
| Original collection retention | All 3,819 baseline cases retained; 98 added cases |
| Tracked fixtures, reports and ledger schemas | Unchanged from base |
| Generated repository map | Regenerated; content unchanged |

The two local skips concern long-double precision exceeding float64 on the current platform; they are inherited platform conditions. The baseline hosted run exercised all 3,819 cases. The final local lanes retain 23 existing constant-input warnings.

Added tests cover native and fallback rank tie rules, both sort directions, five window sizes including incomplete windows, missingness, extreme values, causal prefixes, named/mixed-label axes, input immutability, and empty/duplicate-axis refusals. Validation tests cover empty axis shapes, duplicate/named axes at the helper boundary, mixed scalar values, signed zero, and row-first refusal order. Held-return tests compare the numeric and scalar paths across invalid prior/current endpoints, both missing-price policies, unheld invalid prices and six numeric dtypes. Existing public-capture golden tests retain their cell snapshots and state digests.

A preserved-baseline differential experiment runs **24 book configurations** spanning both engines, daily/monthly rebalancing, equal/rank/inverse-volatility weights, smoothing 0/0.4, nonzero costs, bounded dates, a changing universe mask and missing signals. Every public pandas field, metric, assumption and timing record matches exactly, including signed-zero bits. Existing hardening tests additionally exercise timing, future-input perturbations, disappearance, price refusal, cost scaling, caps, smoothing and solvency.

## Local performance and target estimate

| Execution | Local elapsed or call time |
| --- | ---: |
| Fresh original official test | 219.79 s pytest; 218.774 s call |
| Rank + signal-validation intermediate official test | 160.62 s pytest; 159.34 s call |
| Candidate diagnostics before long-only output buffers | 152.27 s lane; 92.18 s longest call |
| Final diagnostics | 135.04 s lane; 79.844 s longest call |
| Final core | 39.74 s lane |
| Final diagnostic summed work W | 260.240 s |
| Final diagnostic two-worker lower bound | max(130.120, 79.844) = 130.120 s |

The observed diagnostics lane is close to its two-worker work bound. Its final five largest cases take 79.844, 46.80, 46.51, 44.68 and 40.94 seconds. The official case preserves the complete 756×50 fixture and all report-table checks.

The earlier design measured a 141-second official case in a different local execution period. This assessment uses the fresh 218.774-second baseline to avoid silently mixing local load conditions. Profiling and some independent validations overlapped on this host; measurements are indicative, and the same-process ablation below supplies the most controlled comparison.

A simple calibration uses the unchanged official case: `646.495 / 218.774 = 2.955` hosted seconds per current local second. Applying it to the final diagnostics lane gives approximately `135.04 * 2.955 = 399.0` seconds. Adding the measured 34.95-second job overhead gives approximately **434 seconds, or 7m14s**, before the small gate job and queue variation. The modeled longest case is approximately 236 seconds. Core is expected to finish earlier. This extrapolation supports implementing B+C for the target; the hosted measurement below establishes the observed result for this candidate.

## Ablation and retained necessities

The original source files were preserved before edits. Six isolated book variants used the same deterministic 756×50 panels, three timed repetitions each, and exact comparison of every public result field. Each removal changed one candidate optimization while retaining the others.

| Variant | Median pair-of-books time | Relative to candidate | Output comparison |
| --- | ---: | ---: | --- |
| Original implementations | 2.0527 s | 3.01× | Exact |
| Selected candidate | 0.6818 s | 1.00× | Exact |
| Restore scalar-indexed validation | 1.2615 s | 1.85× | Exact |
| Restore scalar held-return loop | 0.9426 s | 1.38× | Exact |
| Restore long-only pandas output writes | 0.8094 s | 1.19× | Exact |
| Restore original long-short loop/output writes | 1.0703 s | 1.57× | Exact |

The long-short experiment treats its output buffers, clipping and rebalance-only diagnostic work as one loop change. Their individual shares remain unmeasured. Every retained runtime change contributes measurable savings. The simpler original loops preserve behavior and increase runtime; the selected changes retain measurable latency headroom. Native rolling rank independently removes the Python callback for supported tie rules; its fallback remains necessary for the other accepted rules.

The selected design omits fixture caches, a custom scheduler, dynamic worker sizing, a new numerical dependency and extra matrix dimensions. The required gate, native thread caps, scalar fallback, input validation, provenance checks, economic guards and exhaustive tests remain necessary. This bounded ablation covers the changed CI/runtime path; it records no whole-project ablation completion claim.

## Hosted verification

[PR #251](https://github.com/minqiyang/equity-factor-research/pull/251) produced successful [run 35630871052](https://github.com/minqiyang/equity-factor-research/actions/runs/35630871052) for head `b08c3eba6b5b0ccd70631b1233147a9e2086cea2`.

| Hosted measurement | Result |
| --- | ---: |
| Run creation to completion | **246 s (4m06s)** |
| First lane start to required-gate completion | 241 s (4m01s) |
| Core job | 144 s (2m24s), PASS |
| Diagnostics job | 236 s (3m56s), PASS |
| Required `Python validation` gate | 3 s, PASS |
| Core pytest | 3,792 passed in 92.34 s |
| Diagnostics pytest | 125 passed in 194.52 s |
| Hosted test union | 3,917 unique cases, zero failures/skips/duplicates |
| Diagnostic summed work W | 372.049 s |
| Longest diagnostic L | 113.15 s |
| Diagnostic maximum RSS | 466,516 KiB |
| Diagnostic process-tree CPU utilization | 192% |

The run was created at 17:15:41 UTC, lanes started at 17:15:46 UTC, and the required gate completed at 17:19:47 UTC. Thus the end-to-end total includes five seconds before the lanes started and the final gate. Relative to the recorded Stage A 20m04s job, this workflow result represents approximately **4.9× lower elapsed time**. Diagnostic work falls from 2,054.822 to 372.049 seconds, and the longest case falls from 646.495 to 113.15 seconds. Hosted runner variability limits attribution of the full observed difference to individual changes; the isolated local ablations establish each change's contribution.

The hosted result is stronger than the conservative cross-run calibration. It preserves every test and all tracked-input checks. The target is measured on this run; later head changes still require their own required CI and eligible reviews.

## Evidence and handoff

Raw local evidence is under `/private/tmp/efr-ci-stage-bc-evidence/`:

- `stage-a-hosted/` and `stage-a-github.log`: downloaded baseline evidence.
- `baseline-official.prof`, `rank-official.prof`, `profile-summary.txt`: preserved profiles.
- `baseline-official.xml`, `final-core.xml`, `final-diagnostics.xml` and matching logs: timings and outcomes.
- `final-collection.txt`, `validation-summary.json`: exhaustive partition comparison and candidate source/test hashes.
- `compare_books.py`, `book-equivalence.json`: 24-case exact public-result comparison.
- `ablation.py`, `ablation.json`, `baseline_*.py`: reproducible isolated removals and original sources.
- `build.log`, `dist/`: packaging evidence.
- `hosted-run.json`, `hosted-jobs.json`, `hosted-core/`, `hosted-diagnostics/` and hosted job logs: downloaded completed-run evidence.

The durable report and engineering log retain the measurements and limitations. The remaining acceptance gate is coordinator verification and two eligible fresh independent reviews of the final candidate, followed by its ordinary protected lifecycle. The coordinator owns the delivery root after the implementation handoff. Hosted target acceptance records total CI elapsed time, with runner queue delays reported separately. Any accounting/refusal mismatch blocks acceptance and requires a scoped repair followed by relevant validation. Forward recovery follows the repository's ordinary protected change process.
