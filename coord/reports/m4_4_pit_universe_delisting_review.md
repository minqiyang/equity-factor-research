Current verdict for `18f3741f5fa7053fff2132adaff4041a57641a07`: **PASS (MATERIAL: 0)**.
See the appended independent re-review for finding closures and current validation.
The original review below preserves the parent candidate findings.

# Milestone 4.4 Independent Code Review

Verdict: **CHANGES REQUIRED — MATERIAL: 2 (two P2 findings).**

The ordinary PIT membership timing and terminal cash calculations pass the
reviewed synthetic controls. Two reproducible boundary defects remain: CSV
ingestion repairs permanent IDs before strict validation, and initialization-row
terminal events lose their required zero-holding evidence records.

## Candidate and review provenance

| Item | Verified value |
| --- | --- |
| Candidate digest | `a2d6f3fe97be945a90e2c67f1bd67ab9dc16a38d` |
| Candidate branch | `feat/m4-4-pit-universe-delisting`, resolving to that digest during review |
| Baseline | `37437df765155b902566dc41e60e0d314355ec3d` |
| Reviewer | Independent Codex session `01a0c7d5-25e1-7672-92fc-e0c9f95ca9f5` |
| Review execution date | 2026-09-21, America/Los_Angeles |
| Clean candidate root | `/private/tmp/efr-m4-4-independent-a2d6f3f` |
| Clean baseline root | `/private/tmp/efr-m4-3-independent-37437df` |
| Local execution evidence | `/private/tmp/efr-m4-4-independent-evidence` |
| Report destination | `/private/tmp/efr-m4-4-review/coord/reports/m4_4_pit_universe_delisting_review.md` |

The supplied review workspace contained an untracked `.venv` symlink and review
card. Verification therefore used a fresh detached worktree at the exact
candidate. Its Git status was clean before and after verification. The producer
worktree and candidate implementation remained unchanged. Repository edits in
the supplied workspace consist solely of this report; synthetic probe scripts,
JUnit records, and numerical captures live in the separate evidence directory.

This session performed the review directly and dispatched zero child reviewers.
The review card requests one GPT-6 Astra High Fast seat; the implementation card
records an owner single-seat override and uses extra-high wording. Runtime
model/effort/service-tier attestation remains the coordinator's dispatch evidence;
this report records the observed session ID and does not manufacture that
attestation.

Read inputs included `AGENTS.md`, the review card, implementation card and report,
the live `coordinator.md` and `routing_table.json`, north star, roadmap, repository
map, timing contract, changed source/tests/reports, and relevant legacy helpers.
The review followed the explicit read-only candidate scope and single-seat task.

## Material findings

### M44-R1 — P2: Preserve strict permanent-ID validation at the PIT CSV boundary

- Classification: **MATERIAL**. Status: **OPEN**, independently reproduced.
- Reporting session and candidate: the session and exact digest above.
- Affected code: `src/data/constituent_table.py:97-108`, where the new PIT CSV
  path consumes IDs already processed by `_parse_symbols`;
  `src/data/csv_loader.py:387-392`, where that helper strips whitespace;
  `src/data/constituent_table.py:273-275`, where the direct PIT interface requires
  exact, unpadded strings.
- Contract: the review card requires strict permanent-ID strings; the
  implementation card at lines 45-46 defines the permanent ID as the exact
  price/signal key. AGENTS requires fail-closed identity handling and prohibits
  silent repair.

**Reproduction and result.** Supply a synthetic interval with
`permanent_id=" ID_A"` or `"ID_A "`, valid daily availability fields, and price
axis `"ID_A"`. Calling `build_pit_membership_mask` directly raises the intended
`PIT-005` exact-string error. Writing the same table to CSV, loading it with
`load_constituent_intervals_csv`, and passing the wrapper to the same mask succeeds.
The loaded ID becomes `"ID_A"`; the mask grants membership after the lag cutoff.
The reviewer tests
`test_csv_pit_id_refuses_silent_whitespace_repair[ ID_A]` and
`test_csv_pit_id_refuses_silent_whitespace_repair[ID_A ]` both fail with
`Failed: DID NOT RAISE ValueError`.

**Mismatch and impact.** Equivalent raw evidence has different eligibility
depending on its ingestion route. The loader silently changes the identifier
used to bind interval evidence to a price column. This bypasses the new strict
identity boundary and hides malformed evidence from the caller. Existing legacy
CSV trimming predates this candidate; the defect concerns reusing that trimming
inside the newly introduced strict PIT path. The reproduction establishes an
input-validation defect; the committed valid-ID demo retains its verified P&L.

**Required resolution.** For CSVs entering the optional PIT interface, validate
raw permanent IDs before normalization, including custom `permanent_id_column`
names. Apply the same raw exact-string rule to `symbol`, which the direct PIT
interface also validates. Preserve the existing legacy-loader contract where
appropriate. Add CSV/direct-frame parity tests for leading/trailing whitespace,
blank IDs, valid string IDs with leading zeros, and custom column names. Both
reproduced padded-ID cases must refuse before membership construction.

### M44-R2 — P2: Retain zero-holding terminal evidence on the initialization row

- Classification: **MATERIAL**. Status: **OPEN**, independently reproduced in
  both engines.
- Reporting session and candidate: the session and exact digest above.
- Affected code: `src/backtest/portfolio.py:968-983` and
  `src/backtest/long_short.py:198-209`.
- Contract: `coord/card_m4_4_pit_universe_delisting.md:137-139` requires event
  records including zero-holding events in the bounded window.
  `coord/reports/m4_4_pit_universe_delisting_impl.md:71-73` claims this retention
  and distinguishes prior-to-window events. The timing contract defines
  accounting dates as the inclusive slice beginning at `evaluation_start`.

**Reproduction and result.** Use a valid full source panel starting 2024-01-01,
declare a terminal event effective 2024-01-08 with reference and known-at dates
2024-01-05, and set `evaluation_start=2024-01-08`. Both engines accept the event,
mark its identity settled, and return `terminal_event_log == ()`. The full source
contains the required preceding reference row. Each book begins entirely in
cash, so the expected event record has zero incoming weight and zero cashflow.
The reviewer test `test_unheld_event_at_bounded_anchor_retains_evidence` fails
for both `lo` and `ls`: `assert 0 == 1` for the event-log length.

**Mismatch and impact.** Initialization puts events with effective dates at or
before the anchor into `settled`, while logging begins only at row one. Thus an
accepted event on the first included accounting date affects future eligibility
and disappears from the result's evidence log. The observed equity and cash are
correct for an all-cash initialization. The defect reduces audit completeness
and violates the explicit zero-holding event contract.

**Required resolution.** Record events effective exactly at the initialization
anchor with zero incoming holdings and zero cashflow. Retain prior-window closure
behavior for events strictly earlier than that anchor. Add both-engine tests
covering an anchor event with a valid full-source reference, a strictly prior
event, a later unheld event, and a single-row bounded evaluation. Verify unchanged
initial capital, zero ordinary turnover/costs, one anchor evidence record, and
continued post-settlement exclusion.

## Self-contained finding reproduction

Run from the clean candidate root with the supplied interpreter and
`PYTHONPATH=src:.`. This uses generated fixtures only and prints both observed
defects without modifying candidate files:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from data.constituent_table import (
    build_pit_membership_mask, load_constituent_intervals_csv,
)
from backtest.portfolio import (
    capture_backtest_source_provenance, run_long_only_backtest,
)
from backtest.long_short import run_long_short_backtest

d = pd.bdate_range("2024-01-01", periods=12)
p = pd.DataFrame({"ID_A": 10.0, "ID_B": 20.0}, index=d)
s = pd.DataFrame({"ID_A": 2.0, "ID_B": 1.0}, index=d)
table = pd.DataFrame([dict(
    symbol="ALIAS", permanent_id=" ID_A", start_date=d[0], end_date=pd.NaT,
    start_known_at=d[0], end_known_at=pd.NaT,
)])
try:
    build_pit_membership_mask(table, d, ["ID_A"])
except ValueError as exc:
    print("direct frame:", exc)
with TemporaryDirectory() as tmp:
    path = Path(tmp) / "synthetic.csv"
    table.to_csv(path, index=False)
    loaded = load_constituent_intervals_csv(path)
    mask = build_pit_membership_mask(loaded, d, ["ID_A"])
    print("CSV accepted:", repr(loaded.data.permanent_id.iloc[0]),
          bool(mask.iloc[1, 0]))  # 'ID_A', True

events = pd.DataFrame([dict(
    event_id="cash", permanent_id="ID_A", effective_date=d[5],
    reference_date=d[4], known_at=d[4], terminal_return=-0.4,
    return_basis="prior_observed_close_to_cash",
)])
settings = dict(evaluation_start=d[5], evaluation_end=d[-1],
                rebalance_frequency="W-FRI", initial_capital=100.0,
                terminal_events=events)
lo = run_long_only_backtest(
    p, s, top_n=2, source_provenance=capture_backtest_source_provenance(p, s),
    **settings,
)
ls = run_long_short_backtest(p, s, quantiles=2, **settings)
print("anchor event logs:", lo.terminal_event_log, ls.terminal_event_log)
# Actual: () (); required: one zero-weight, zero-cashflow record per book.
```

## Completed verification coverage

| Boundary | Review evidence and outcome |
| --- | --- |
| Causal membership cutoff | `constituent_table.py:290-298` shifts bounded observed dates by the requested lag. Effective entry and entry knowledge both apply; closure requires both effective end and known end. Focused lag-1/2, future-prefix and bounded-window tests pass. Independent scalar-loop oracles also pass on a gapped calendar for lags 1, 2, 4, and 20. |
| Permanent identity and ticker reuse | Direct-frame IDs/axes require exact nonempty strings. Existing symbol and permanent-ID overlap guards run before masking. Reused tickers map to distinct permanent price columns; same-ID reentry, missing IDs, mixed axes, ticker-axis refusal, and overlap tests pass. CSV strictness has M44-R1. |
| Raw date precision | PIT CSV effective/availability dates pass through `_source_close_column`; intraday and timezone-bearing values refuse. Four independent probes add one nanosecond separately to each effective/availability field and all refuse. Legacy CSV behavior remains separately scoped. |
| Terminal schema | `_prepare_terminal_events` enforces exact columns, unique event/security IDs, known source asset/date, preceding full-source reference, known-at no later than effective date, finite non-Boolean return at least -1, and literal complete-return basis. Existing invalid-evidence tests pass. |
| Return replacement | `_calculate_held_asset_returns` requires a valid held reference quote and substitutes the complete terminal return for the incoming quote return exactly once. Missing event quotes are accepted; missing reference quotes and missing evidence refuse. Contradictory finite event quotes cannot double-count the terminal payoff. |
| Signed settlement | `_terminal_settlement` computes `previous_equity * incoming_weight * (1 + terminal_return)` and checks finite cashflow. Both engines clear the position after gross return/drift and before ordinary trades. Long credit, short liability, positive/negative payoff, explicit -1, simultaneous/final-row settlement, and insolvency tests pass. |
| Frozen targets | Schedule masking requires `known_at <= a[j-lag]` and effective date by execution. `_validate_terminal_target` refuses a nonzero target in `settled`. Late-information collision and future-return-magnitude prefix-invariance tests pass. |
| Costs and turnover | Ordinary signed trades use holdings after terminal clearance. Redemption contributes zero ordinary turnover and zero additional settlement fee. Same-close market trades retain the existing cost convention. Focused tests and the independent fixed-share controls pass. |
| Cash accounting | Both result objects compute equity times one minus summed signed closing weights. Twelve independently constructed long-only/long-short cases verify actual cash plus fixed surviving-share value over four changing-price dates, with terminal returns -1, -0.4, and +0.7 and nonzero entry commission/slippage. |
| Holding episodes | Long-only episode calculation receives terminal return and zero closing holding while market redemption trades remain zero. The existing explicit-zero-recovery test closes the episode at return -1. |
| Window and event evidence | Prior-window exclusion, later-window events, final-row events, and unheld demo events pass. Initialization-row retention has M44-R2. |
| Synthetic end-to-end demo | Independent execution reproduces committed Markdown exactly and matches JSON metrics and diagnostics structurally. All six cases remain present: four successful books and two `incoming_price_invalid` refusals. |
| Attempt retention | Independently parsed all 24 committed JSONL records, paired 12 attempt IDs, verified one start and one terminal record each, and matched each terminal payload to the regenerated case. Existing repeated-append, unexpected-failure, and interruption tests pass. |
| Default compatibility | Independently executed baseline and candidate default diagnostics with new arguments absent; all captured legacy calculation values match byte for byte. |

The independent cash oracle starts from equity 99.85 after a 15-bps entry cost,
computes terminal proceeds from the signed 0.5 weight, and values the survivor
using a fixed share count at four subsequent prices. It tests cash economically
through share quantities in addition to checking the residual-cash identity.

## Independent commands and measured results

Interpreter: `/private/tmp/efr-m4-4-review/.venv/bin/python`.
Environment: macOS 27.2 arm64; Python 3.12.13; NumPy 2.5.3; pandas 3.0.6;
SciPy 1.18.1; pytest 9.1.1; pytest-xdist 3.8.0; Ruff 0.16.8.
This environment differs from the producer's Python 3.11 environment.

Commands ran in the clean candidate worktree. Focused/core/diagnostics and
baseline captures used thread caps of `1` for `OMP_NUM_THREADS`,
`OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `BLIS_NUM_THREADS`,
`VECLIB_MAXIMUM_THREADS`, and `NUMEXPR_NUM_THREADS`.
Below, `python` denotes the interpreter above. Test commands additionally saved
JUnit XML into the local evidence directory.

| Command | Observed result |
| --- | --- |
| `python -m pytest -q tests/test_pit_universe_delisting.py tests/test_pit_universe_delisting_demo.py` | 103 passed, 2.85 s |
| `python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 tests --ignore=tests/test_multifactor_diagnostic_mvp.py --ignore=tests/test_m3_10_hardening.py` | 3,974 passed, 2 skipped, 29.24 s |
| `python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 tests/test_multifactor_diagnostic_mvp.py tests/test_m3_10_hardening.py` | 125 passed, 92.27 s |
| `python -m ruff check .` | Exit 0; all checks passed |
| `python -m compileall -q src tests research lean` | Exit 0 |
| `PYTHONPATH=src:. python -m pytest -q /private/tmp/efr-m4-4-independent-evidence/test_review_probes.py` | 21 passed, 4 failed, 1.04 s; the four failures reproduce the two findings |
| Read-only `scripts.repo_map.build_repo_map()` comparison with committed map | Exact equality |
| `git diff --check 37437df HEAD` | Exit 0 |
| Candidate `git status --porcelain` and `git rev-parse HEAD` | Clean; exact requested candidate |

Combined core/diagnostics coverage is 4,099 passed and 2 skipped. Focused tests
are already included in core and add no extra unique-suite count. Both skips
come from platform `longdouble` precision equaling float64. Constant-input
correlation warnings arise in deliberately constant synthetic fixtures.

Local evidence includes `focused.xml`, `core.xml`, `diagnostics.xml`,
`probes.xml`, the full failing probe output `probes.txt`, and
`test_review_probes.py`. Reproduction snippets above preserve the findings
independently of temporary evidence retention.

## Baseline comparison and synthetic artifacts

The inspected producer capture utility was copied into the independent evidence
directory and executed afresh against each clean root with `PYTHONPATH=src:.`:

```sh
python /private/tmp/efr-m4-4-independent-evidence/capture.py OUTPUT.json
```

Each execution called `run_multifactor_diagnostic_mvp(write_outputs=False)`.
Baseline execution took 54.72 seconds and candidate execution took 55.23 seconds.
The captures cover 62 factors, 124 books, and 1,674 existing public calculation
fields, together with DSR, PBO, trial family, weighting comparisons, and
multiple-testing results. They hash Series/DataFrame values and indices and
retain metrics. Newly added cash/event fields and nonnumerical book metadata
fall outside that capture; focused tests cover the added outputs.

Both independently generated capture files are byte-identical and have SHA-256:

```text
dc11ab9bef09476e609aaea869aa38019a0b54c9dc7252303b4c3fc832af9e8c
```

The regenerated demo reproduces the following final equity and signed terminal
cashflow values, rounded here to six decimals:

| Synthetic case | Status | Final equity | Terminal cashflow |
| --- | --- | ---: | ---: |
| Long-only static | success | 1102.965192 | 0.000000 |
| Long-only PIT | success | 423.335191 | 399.400000 |
| Long-only missing evidence | refused | undefined | undefined |
| Long-short static | success | 1205.507104 | -101.352982 |
| Long-short PIT | success | 719.378524 | 199.700000 |
| Long-short missing evidence | refused | undefined | undefined |

The committed source and artifact hashes match every corresponding hash in the
implementation report, including constituent parsing, both engines, demo code,
Markdown, JSON, and the attempt log. The static and PIT cases use the same
declared settlement evidence and explicitly different membership rules. All
results retain their synthetic `DIAGNOSTIC_ONLY` meaning.

## Ablation, limitations, and next gate

The producer's retained `ablation.json` describes three isolated removals:
terminal knowledge cutoff, long-only holding clearance, and raw PIT CSV date
precision validation. Their recorded failures correspond to necessary guards
visible in the reviewed source. The candidate source hashes match the preserved
baseline hashes in that evidence. This review independently reran the intact
guard tests and inspected the recorded ablation evidence; mutation experiments
remain producer evidence. The review authored zero implementation changes.

Hosted CI and a distribution build were outside this independent execution set.
The local runs establish the stated environment's results; the hosted Python
3.11 gate retains its separate status. Timing measurements are individual local
observations. Model/effort/tier dispatch provenance requires the coordinator's
record as described above.

This review exercised synthetic inputs and committed synthetic fixtures.
Historical identity lineage, source availability certification, revision-vintage
selection, delayed recoveries, receivables, stock consideration, and formal
real-data promotion retain the limitations stated in the accepted contract.
The two findings address implemented contract boundaries within the current
milestone.

The next gate is in-scope remediation of M44-R1 and M44-R2, deterministic
revalidation, and fresh exact-candidate review. This report records two open P2
material findings and the passing verification coverage above.

---

## Independent re-review — completed 2026-09-22

Verification ran on 2026-09-21, America/Los_Angeles.

Verdict: **PASS (MATERIAL: 0)** for candidate
`18f3741f5fa7053fff2132adaff4041a57641a07`.
M44-R1 and M44-R2 are **CLOSED — independently verified**. This re-review found
zero new material defects in the remediation and exercised regression coverage.
The earlier CHANGES REQUIRED verdict and OPEN statuses above describe parent
`a2d6f3fe97be945a90e2c67f1bd67ab9dc16a38d`; this section records their resolution.

### Candidate, independence, and evidence

- Candidate branch: `feat/m4-4-pit-universe-delisting`, verified locally at the
  requested candidate; its immediate parent matches the requested parent.
- Reviewer: independent Codex session `01a0c7e6-fe90-7501-aa60-a4b3528d7fe5`.
  This session performed the review directly with zero child reviewers.
- Clean execution root: `/private/tmp/efr-m4-4-rereview-clean-18f3741`, a fresh
  detached worktree at the candidate. Git status was empty before verification
  and after all required checks. The supplied root's untracked review card,
  previous report, and `.venv` link remain preserved.
- Report destination: `/private/tmp/efr-m4-4-rereview/coord/reports/m4_4_pit_universe_delisting_review.md`.
  Candidate implementation files and the producer worktree received zero edits.
- Retained execution evidence: `/private/tmp/efr-m4-4-rereview-evidence`, including
  suite logs/JUnit XML, supplemental probe source, `verification_manifest.json`,
  and the original report snapshot. The original reviewer probes were rerun
  unchanged from `/private/tmp/efr-m4-4-independent-evidence/test_review_probes.py`.
- All seven remediation-file SHA-256 values match the producer's frozen
  `candidate_manifest.json`. The verification manifest records these hashes,
  candidate/parent identities, clean status, timestamp, and prior report/probe
  hashes.

Read inputs included AGENTS, the re-review card, original review, implementation
card/report, live coordinator and routing files, north star, roadmap, repository
map, timing contract, the complete remediation diff, affected helpers, and
regression tests. The review follows the explicit single-seat, read-only task.
The re-review card specifies GPT-6 Astra High Fast; concrete model, reasoning,
and tier dispatch attestation remains the coordinator's retained runtime record.
The observed session identifier above supplies review-session provenance.

### M44-R1 closure — strict raw CSV identities

Status: **CLOSED** against the remediated candidate.

`src/data/constituent_table.py:71-78` identifies the optional PIT CSV path and
validates each original symbol/permanent-ID value as a nonempty, unpadded string.
This executes before `_parse_symbols` at lines 80 and 107. The existing reader
uses `dtype=str` and `keep_default_na=False`, preserving leading zeros and raw
whitespace for validation. The guard uses caller-selected column names.

Both original padded-permanent-ID probes now pass. Eight additional independent
CSV-load probes assert exact exception text for leading whitespace, trailing
whitespace, empty strings, and whitespace-only strings in both identity fields.
For `permanent_id`, every case raises exactly
`ValueError('PIT-005: permanent_id must contain complete exact string IDs')`
at loading. The equivalent symbol cases raise the same message with `symbol`.

Committed regression tests at `tests/test_pit_universe_delisting.py:611-686`
pass CSV/direct-frame refusal parity for standard and custom headers, leading-zero
round trips and membership-mask equality, and the legacy trimming control.
The strict path preserves original valid IDs and refuses malformed identities
before membership construction.

### M44-R2 closure — anchor terminal evidence

Status: **CLOSED** against the remediated candidate.

`src/backtest/portfolio.py:970-976` and `src/backtest/long_short.py:200-206`
select events effective exactly at the bounded initialization anchor and invoke
`_terminal_settlement` with the initialized zero holdings and initial capital.
The shared helper retains every event's evidence plus zero incoming weight and
cashflow. The accounting arrays retain their zero initialization. Both engines
keep events at or before the anchor in `settled`; the subsequent loop starts at
row one, preserving one-time logging and preventing reentry.

Both original `test_unheld_event_at_bounded_anchor_retains_evidence` cases pass
`assert len(book.terminal_event_log) == 1`, zero incoming weight, and zero cashflow.
Committed tests at `tests/test_pit_universe_delisting.py:689-747` pass strictly
prior, anchor, and later unheld events; unchanged initial capital, cash, turnover,
and costs; and continuing post-settlement exclusion. Strictly prior events retain
zero bounded log entries. Two additional independent probes supply simultaneous
anchor events with distinct IDs and different returns: both engines retain two
complete zero-flow records and preserve cash/equity at initial capital.

Single-row bounded evaluations preserve the established typed refusals:
`evaluation_bounds_invalid` for long-only and `evaluation_window_invalid` for
long-short. Tests at lines 750-763 provide valid full-source references and pass
these existing minimum-window contracts. Accepted multi-row windows exercise
anchor evidence retention.

### Independently executed checks

Interpreter: `/private/tmp/efr-m4-4-rereview/.venv/bin/python`.
Environment: macOS 27.2 arm64, Python 3.12.13, NumPy 2.5.3, pandas 3.0.6,
SciPy 1.18.1, pytest 9.1.1, pytest-xdist 3.8.0, Ruff 0.16.8.
All pytest runs used `PYTHONPATH=src:.` and thread caps of `1` for
`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `BLIS_NUM_THREADS`,
`VECLIB_MAXIMUM_THREADS`, and `NUMEXPR_NUM_THREADS`. Supplemental probes also add
the original probe directory to PYTHONPATH. Commands ran in the clean root.
Below, `python` denotes that interpreter; pytest commands also save JUnit XML.

| Command / selection | Independent result |
| --- | --- |
| `python -m pytest -q tests/test_pit_universe_delisting.py tests/test_pit_universe_delisting_demo.py` | 132 passed, 2.73 s |
| `python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 tests --ignore=tests/test_multifactor_diagnostic_mvp.py --ignore=tests/test_m3_10_hardening.py` | 4,003 passed, 2 skipped, 29.49 s |
| `python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 tests/test_multifactor_diagnostic_mvp.py tests/test_m3_10_hardening.py` | 125 passed, 91.79 s |
| `python -m pytest -q /private/tmp/efr-m4-4-independent-evidence/test_review_probes.py` | 25 passed, 1.96 s; all four former failures pass |
| `python -m pytest -q /private/tmp/efr-m4-4-rereview-evidence/test_closure_exactness.py` | 10 passed, 0.82 s |
| `python -m ruff check .` | Exit 0; all checks passed |
| `python -m compileall -q src tests research lean` | Exit 0 |
| `git diff --check HEAD^ HEAD` | Exit 0 |
| Candidate identity, changed-file hashes, and clean Git status | Passed |

Core plus diagnostics total **4,128 passed, 2 skipped**. Focused tests are included
in core. The two skips record platform `longdouble` precision matching float64;
constant-input correlation warnings arise in constant fixtures. The 25 original
probes additionally revalidate signed fixed-share cash accounting, gapped-calendar
membership cutoffs, nanosecond timestamp refusals, regenerated synthetic report
parity, and all 24 committed attempt records. The required focused selection has
132 tests; the producer's 139-test selection also includes constituent-table tests,
which this review executes through the full core lane.

### Ablation evidence and verification limits

The remediation ablation record at
`/private/tmp/efr-m4-4-remediation-evidence/ablation.json` binds its three preserved
source hashes to this candidate. Its isolated removals record 16 failures for
raw identity validation, two for long-only anchor logging, and two for long-short
anchor logging. This review inspected that evidence and independently reran the
intact controls. Mutation outcomes remain attributed to the producer. The fixes
reuse the existing settlement helper and add zero abstractions or dependencies;
this read-only review introduces zero design or implementation changes.

This re-review covers the complete remediation diff, both closure boundaries,
and the required local regression lanes on synthetic inputs. The original
M4.3 default-output comparison remains historical review evidence; this session
reran the current diagnostics lane and original probes. Hosted CI, distribution
build, and a fresh baseline numerical capture remain outside this re-review's
execution set. Historical identity lineage, availability certification, delayed
recoveries, and real-data promotion retain the implementation's stated limits.

The next gate is coordinator acceptance of this exact candidate and its review
provenance, followed by the separately governed hosted checks and publication
lifecycle. This report records both findings closed and **MATERIAL: 0**.
