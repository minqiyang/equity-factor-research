# M4.4 Implementation and Validation Report

Date: 2026-09-21. Executor: GPT-6 Astra, extra-high reasoning, Fast.
Base: `37437df765155b902566dc41e60e0d314355ec3d` (M4.3, PR #252).
Branch: `feat/m4-4-pit-universe-delisting`.
Producer worktree: `/private/tmp/efr-m4-4-pit-universe-delisting`.
Plan commit: `4932ce815041954f267f42370fdfd186c2f674cd`.
The containing implementation commit identifies this report's candidate.
Original candidate: `a2d6f3fe97be945a90e2c67f1bd67ab9dc16a38d`.
Status: M44-R1 and M44-R2 remediated; local revalidation is recorded below.
Independent re-review and hosted CI remain pending.

## Review remediation

The independent review of `a2d6f3f` returned CHANGES REQUIRED with two P2
MATERIAL findings. This revision addresses both findings in their existing
modules. Formal finding closure belongs to the independent re-review of the
new commit.

| Finding | Implemented correction | Regression evidence |
| --- | --- | --- |
| M44-R1 | PIT CSV input validates original symbol and permanent-ID strings before normalization. The guard uses the caller's column names and raises the intended `PIT-005` exact-string error for padded, blank, or missing identities. Legacy CSVs retain their existing trimming behavior. | Sixteen CSV/direct-frame refusal cases cover two identity fields, leading/trailing whitespace and blank strings, and standard/custom headers. Two valid leading-zero round trips preserve identities and mask equality; one legacy control preserves trimming. |
| M44-R2 | Both engines pass events effective exactly at the initialization anchor through the existing settlement-log helper with their initialized zero holdings. Cash and accounting arrays retain their zero initialization. Strictly prior events remain settled outside the bounded log. | Six both-engine cases cover strictly prior, anchor, and later unheld events; two longer-window cases prove one anchor record and continued exclusion; two single-row cases preserve the existing window refusal. |

The 29 new regression cases produced 20 failures and 9 passing controls against
the reviewed implementation. The complete targeted run now passes 139 tests:
the PIT implementation/demo tests plus the existing constituent-table tests.
The independent reviewer's unmodified probe file also passes all 25 cases,
including its four original failing reproductions. This probe replay was run
by the producer and supplies remediation evidence.

| Remediation validation | Result |
| --- | --- |
| Targeted PIT/demo/constituent suite | 139 passed, 1.75 seconds |
| Full core CI lane | 4,003 passed, 2 platform skips, 26.63 seconds |
| Full diagnostics CI lane | 125 passed, 90.85 seconds |
| Combined full-suite count | 4,128 passed, 2 skipped; targeted tests are included in core |
| Independent review probe replay | 25 passed, 0.94 seconds |
| Ruff, compileall for source/tests/research/LEAN, distribution build, map freshness, whitespace | Passed |

The environment and two-worker thread caps match the original producer setup
recorded below. The skips retain the platform `longdouble` precision condition.
Constant-input warnings remain confined to constant correlation fixtures.

Single-row bounded evaluation retains the established public contract. The
long-only engine raises `evaluation_bounds_invalid`; the long-short engine
raises `evaluation_window_invalid`. Both tests provide a full source panel and
a valid terminal reference, isolating the minimum-window refusal. Accepted
multi-row windows retain anchor evidence without changing initial capital,
holdings, ordinary turnover, or costs.

Three isolated removal experiments preserved the corrected source:

| Removal | Observed result | Retained necessity |
| --- | --- | --- |
| Raw identity guard | 16 failures, 3 passing controls | Exact-string validation at CSV ingestion |
| Long-only anchor logging | 2 failures, 6 passing controls | Initialization-row evidence retention |
| Long-short anchor logging | 2 failures, 6 passing controls | Initialization-row evidence retention |

The removals ran in copied packages in separate subprocesses; producer files
remained byte-identical. Pytest elapsed times were 0.55, 0.10, and 0.11 seconds.
The existing settlement helper supplies the shared event representation;
this revision adds no event abstraction or dependency. The unchanged synthetic
demo reproduces its committed Markdown, JSON metrics/diagnostics, and all 24
attempt records under the reviewer's probe.

Current source identities:

| File | SHA-256 |
| --- | --- |
| `src/data/constituent_table.py` | `28b3857e66528d5500a16d81b92c1d8b2e9f142fe3653e203af2e66d17585333` |
| `src/backtest/portfolio.py` | `4eb82e37324d4a5c19c6ee3136b3ea6aa5f4bbc1fb86b07671cb3e3e62ee0006` |
| `src/backtest/long_short.py` | `7b33283f3cef4b5eac61e2e325e2b2a88592c016b052dce3da2b95bebc935877` |
| `tests/test_pit_universe_delisting.py` | `ac4181754b3d0cc44ad2796dc2c48a5440c5126e4e0da72660b2d4360fc94dec` |

Remediation execution evidence is retained separately at
`/private/tmp/efr-m4-4-remediation-evidence`: pre-fix reproductions, focused and
full-lane JUnit/logs, reviewer-probe replay, build output, corrected source
copies, and isolated ablation results. The sections below preserve the initial
implementation record for `a2d6f3f`, including its original source hashes and QA.

## Delivered behavior

Both portfolio engines accept optional identity-backed constituent intervals
and explicit immediate-cash terminal events. Membership uses the schedule known
at each lagged decision close. A terminal event replaces one incoming return,
settles signed cash, and clears the security's holding, including between
scheduled resets. Reused tickers retain separate permanent-ID price columns.

The accepted [implementation card](../card_m4_4_pit_universe_delisting.md)
defines the exact fields, timing, accounting order, and review scope. The
coordinator accepted the card and copied it to the canonical root before
implementation. The owner directed immediate execution and a single fresh
GPT-6 Astra extra-high Fast review. This is a structural cross-engine input and
accounting contract change.

| File or group | Responsibility |
| --- | --- |
| `src/data/constituent_table.py` | Preserve optional CSV availability columns; validate daily source-close labels and permanent identities; build causal execution-date membership masks |
| `src/backtest/portfolio.py` | Shared terminal validation, causal eligibility, signed settlement, frozen-target refusal; long-only integration and cash outputs |
| `src/backtest/long_short.py` | Signed long-short settlement, surviving-book drift, diagnostic terminal returns, and cash outputs |
| `research/pit_universe_delisting_demo.py` | Six deterministic synthetic cases, all-attempt logging, Markdown comparison and structured evidence |
| `tests/test_pit_universe_delisting*.py` | Independent accounting oracles, causality and identity boundaries, invalid evidence, attempt retention, and output parity |
| `reports/pit_universe_delisting_demo.*` and attempt log | Preserved successful and refused synthetic cases, inputs, eligibility, equity, cash, holdings, and event records |
| Timing contract, roadmap, engineering log, repository map | Additive interface contract, current implementation state, limitations, and repository navigation |

No dependency, workflow, benchmark implementation, existing empirical report,
private-data runner, or formal promotion threshold changed.

## Accounting and causality

At execution row `a[j]`, membership requires an effective start by `a[j]` and
start availability by bounded source row `a[j-L]`. A known effective closure
removes eligibility. An unknown future closure preserves prior decisions. An
empty eligible set produces cash at the next scheduled reset. Prices and
signals use permanent IDs; display aliases remain descriptive evidence.

The terminal schema specifies the immediately preceding full-source reference
row and the complete return from that close to cash. It uses the literal basis
`prior_observed_close_to_cash`. Separate market and delisting legs require
caller-side compounding `(1+r_market)*(1+r_delist)-1`. This complete return
replaces the event-row quote return once. A held reference quote remains
mandatory; the event-row quote may be missing.

For previous equity `E` and signed weight `w`, settlement cash is
`E*w*(1+r_terminal)`. Long proceeds credit cash and a short settlement pays the
remaining liability. The engine zeroes the settled holding before ordinary
market trades. Existing gross and postcost solvency guards apply. An explicit
return of -1 permits zero recovery when the whole portfolio remains solvent.

Known terminal schedules exclude later targets. A surprise terminal event that
collides with a nonzero frozen target refuses with `terminal_target_invalid`.
The engine preserves decision-time ranking. Surviving positions drift between
resets, including temporary long-short exposure imbalance. Terminal redemption
has zero additional modeled fee and a separate cash-flow record. Subsequent
market trades pay the existing turnover-based costs and slippage.

`cash_balance` equals equity times one minus the sum of signed closing weights.
It follows the existing postcost target-weight accounting convention. Tests
reconcile cash plus signed asset value to equity and prove that settlement cash
stays constant while surviving asset prices change between resets.
`terminal_event_log` records input evidence, incoming signed weight, and cash
flow. Unheld events retain a zero-flow log entry. Prior-to-window events keep
their identities closed without creating an in-window settlement entry.

## Synthetic end-to-end evidence

Command: `python -m research.pit_universe_delisting_demo`.
The fixture contains 12 generated source dates, three predeclared identities,
one reused ticker, and an explicitly announced -60% terminal return. Initial
capital is 1,000; market turnover pays 10 bps commission plus 5 bps slippage.
The same explicit terminal evidence is supplied to each successful static/PIT
comparison. All cases remain `DIAGNOSTIC_ONLY`.

| Case | Outcome | Final equity | Signed terminal proceeds |
| --- | --- | ---: | ---: |
| Long-only static roster | success | 1102.965192 | 0.000000 |
| Long-only PIT membership | success | 423.335191 | 399.400000 |
| Long-only missing terminal evidence | refused: `incoming_price_invalid` | undefined | undefined |
| Long-short static roster | success | 1205.507104 | -101.352982 |
| Long-short PIT membership | success | 719.378524 | 199.700000 |
| Long-short missing terminal evidence | refused: `incoming_price_invalid` | undefined | undefined |

These values describe synthetic accounting controls. The static roster includes
the later index entrant throughout its generated price history. The PIT schedule
changes eligibility and retains the old identity's severe terminal loss. The
comparison supplies a reproducible mechanism demonstration. Historical universe
quality and investment performance require separate evidence.

The committed attempt log retains two complete executions: 12 attempts with
start and terminal records, totaling 24 JSONL records. Failed and interrupted
execution handling is tested separately. JSON evidence includes all six outcomes
and each successful book's path; Markdown and structured payload parity is tested.

## Original candidate coverage and validation

| Runtime boundary | Deterministic evidence |
| --- | --- |
| Identity and membership | Reused ticker with distinct price levels, ticker-axis refusal, overlap refusal, same-ID reentry, additions/deletions, empty eligibility, exact string axes |
| Timing and availability | Lag 1/2, bounded initialization, gapped observed dates, preannounced and late changes, future-record prefix invariance, intraday/timezone refusal |
| Long and short settlement | Hand-computed proceeds/liabilities, positive/negative terminal returns, explicit zero recovery, insolvency refusal, absent event quote and invalid reference quote |
| Holding lifecycle | Off-rebalance and final-row events, simultaneous events, one-time application, pre-window closure, future-window event, frozen-target collision, post-event reentry prevention |
| Cash and costs | Equity reconciliation, changing survivor prices, same-close reinvestment, inherited transaction/slippage arithmetic, terminal redemption excluded from market turnover |
| Input and evidence boundaries | Missing, duplicate, extra or invalid fields; unknown IDs/dates; return basis including null; nonfinite/Boolean returns; strict missing-price policy; ambiguous universe ownership |
| Reporting and retention | All six cases, repeated-run append retention, unexpected failure and interruption retention, deterministic rendering and structured parity |
| Legacy behavior | Both complete CI lanes; 124 default diagnostic books and 1,674 captured public calculation fields compared with the saved baseline |

Local validation uses Python 3.11.15 on macOS arm64, NumPy 2.4.6, pandas 3.0.6,
SciPy 1.17.1, pytest 9.1.1, pytest-xdist 3.8.0, and Ruff 0.16.8.
Each parallel test lane uses two workers with work stealing and zero worker
restarts. BLAS/OpenMP/NumExpr thread caps match hosted CI.

- New focused tests: 103 passed.
- Full core lane: 3,974 passed, 2 skipped in 26.20 seconds.
- Full diagnostics lane: 125 passed in 90.01 seconds.
- Combined coverage: 4,099 passed, 2 skipped. Both skips reflect this platform's
  `longdouble` precision matching float64. Constant-input correlation warnings
  occur in intentionally constant fixtures.
- Ruff, source/test/research/LEAN compilation, distribution build, repository-map
  freshness, and whitespace checks passed.

The saved default diagnostic comparison is byte-identical for all captured
values: 62 factors, 124 books, 1,674 public calculation fields, DSR, PBO, trial
family, weighting comparisons, and the M4.3 multiple-testing summary. Both
comparison files have SHA-256
`dc11ab9bef09476e609aaea869aa38019a0b54c9dc7252303b4c3fc832af9e8c`.
The capture excludes the three newly added cash/event fields and non-numerical
book metadata; dedicated tests cover zero-event outputs and optional assumptions.
Baseline and candidate captures took 51.65 and 50.08 seconds respectively.
These single local observations establish operational cost context; controlled
performance comparison and hosted elapsed time remain unmeasured for M4.4.

Final boundary inspection found that the legacy CSV loader normalized effective
dates before the new mask received them. The PIT CSV path now checks raw entry
and exit timestamps at full precision. Four regression cases cover intraday and
timezone-bearing effective dates. The original start-date parser already rejects
timezones; the test accepts that existing refusal reason. Legacy tables without
availability fields retain their original loader behavior.

Reproduction uses the checked-in CI lane selections:

```sh
python -m pytest -q tests/test_pit_universe_delisting.py tests/test_pit_universe_delisting_demo.py
python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 tests --ignore=tests/test_multifactor_diagnostic_mvp.py --ignore=tests/test_m3_10_hardening.py
python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 tests/test_multifactor_diagnostic_mvp.py tests/test_m3_10_hardening.py
python -m ruff check .
python -m compileall -q src tests research lean
python -m build
python scripts/repo_map.py
git diff --check
```

## Original candidate isolated ablation

The experiment preserved the candidate portfolio module and copied its package
into a separate temporary root for each removal. Each subprocess imported only
its selected mutated package. The producer source remained unchanged, with
SHA-256 `40dfd96734e798c0c09274ff4db4f6af309bbf0fddaa8cd64d489ca2c06c11cd`.

| Isolated removal | Result | Decision |
| --- | --- | --- |
| Remove `cutoffs >= record["known_at"]` from terminal schedule masking | Both long-only and long-short late-information collision tests fail: a future announcement silently changes the frozen target and the required refusal disappears | Retain the knowledge cutoff |
| Remove long-only `pretrade_weights.loc[list(terminal_returns)] = 0.0` | Three long-only payoff cases fail on the following missing-price interval because the settled asset remains held; three unchanged long-short controls pass | Retain explicit holding clearance |
| Remove raw effective-date precision validation in the PIT CSV loader | Both intraday entry/exit tests fail because legacy normalization silently accepts the timestamps | Retain the raw-date boundary check |

The mutated selections took 0.06, 0.14, and 0.51 seconds of pytest time. All three
removed operations protect correctness, so the implementation ablation retains them.
The subsequent focused and full core runs pass against the preserved producer.
Design simplification confines settlement to one complete-window immediate-cash
event per security, with shared helpers in the existing portfolio module.
General corporate-action dispatch, a schema registry, and payment-lag receivable
valuation remain outside this implementation. This ablation covers the added
membership/terminal path and its baseline compatibility.

## Original candidate evidence identities and remaining gates

| Artifact | SHA-256 |
| --- | --- |
| `src/data/constituent_table.py` | `74aafc599f174a5fd7e2d39a0751a5452fe4b324f798e1c7ab8a6172f9dc4cef` |
| `src/backtest/portfolio.py` | `40dfd96734e798c0c09274ff4db4f6af309bbf0fddaa8cd64d489ca2c06c11cd` |
| `src/backtest/long_short.py` | `ed21523f29ea1df5c67fde1830354b0209dee89a4676d758bb1508470e480cc3` |
| `research/pit_universe_delisting_demo.py` | `d157653c87e5e8a61b2b44bee34719aef6143a1777cde29ff74328dafe1c8656` |
| Synthetic Markdown report | `91778c99cc59dd17ea53796f01f6850b6c80c3fea8a40f4fbdbe6eb48b335dbe` |
| Synthetic JSON report | `ea30b17566c1778826a2981c48dcbfe9af9b25163f8ae292dcee992de1b47f60` |
| Append-only synthetic attempt log | `b8d24606854ae8a302061e8d0fcbd04a975c2e589fed517a756ee6f3f033bd95` |

Local capture scripts, baseline/candidate JSON, JUnit lane evidence, build log,
and isolated ablation packages/logs are retained at
`/private/tmp/efr-m4-4-evidence`. The committed tests, contract, and synthetic
artifacts provide the durable reproduction surface.

Caller-declared identities, availability labels, and terminal values establish
the implemented simulation inputs. Full historical universe completeness,
verified identity lineage, source revision selection, source calendar evidence,
and formal real-data promotion remain open. Delayed bankruptcy recoveries,
unpriced receivables, stock/mixed consideration, borrow economics, and calibrated
terminal fees require separately specified accounting. Existing static-cohort
research retains its prior limitations. This candidate reads generated fixtures
and synthetic panels only. The next gate is the coordinator's independent
single-seat review on a clean worktree at the frozen implementation commit,
followed by hosted checks and the protected same-change publication lifecycle.
