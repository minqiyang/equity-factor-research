# Step 2 Dividend Design Attempt 01

The local draft proposes one synthetic ordinary cash dividend comparison and
one owner semantic decision. Literal design checks and existing software QA
passed. The proposal remains unaccepted; product implementation and
publication remain outside this attempt.

## Task, ownership and candidate

- Task card:
  `/Users/rhapsoul/Documents/Codex/projects/efr-demo-first-docs-20260915/coord/dividend_design_card.md`.
- Writer root:
  `/Users/rhapsoul/Documents/Codex/projects/efr-dividend-design-20260918`.
- Branch: `codex/dividend-design-20260918`.
- Source HEAD: `57035fbfe3f8495e6495feecb8afbc2664f3f237`, the locally
  recorded merge of Step 1 PR #220. Local `main` and `origin/main` equal this
  hash. Live remote verification failed with DNS resolution failure; this
  report makes only the local-history claim.
- Initial working tree was clean; resolved root is this standalone checkout.
  One worker wrote this root. No child writers or reviewers were started.
- Requested route/settings: DESIGN, fresh `gpt-6-astra`, max effort,
  normal/non-Fast tier. The card supplies those settings. Effective native
  settings and rendered pane visibility remain unverified because the sandbox
  denied Herdr inspection. Effective tool permissions are workspace-write,
  read-only `.git`, restricted network and approval policy `never`.
- Inherited session locator: Herdr workspace `w3`, tab `w3:tBS`, pane
  `w3:pDR`, with `HERDR_ENV=1`. These are inherited locators, rather than a
  successful live API response.
- Risk classification: CRITICAL with structural reason
  `SCHEMA_PROTOCOL_CONTRACT` for eventual binding acceptance. Incorrect
  dividend or timing semantics could invalidate later economic evidence.
- Draft:
  `docs/synthetic_event_reconciliation_design.md`, SHA-256
  `6ff0a7da213c36c1a2e11c02dae70e4fc89211003d9b4d4dd6df97c2c2200d08`.
- Proposed convention: `synthetic_ordinary_cash_dividend_gross_ex_close_v1`.
  The final four-file manifest and complete local evidence manifest are
  saved under `build/dividend-design-evidence/` at handoff. They identify the
  final bytes without a self-referential report hash.

## One owner semantic decision

**Accept gross ordinary-dividend entitlement for the pre-ex-date reference
holder, zero withholding, theoretical fractional reinvestment at the ex-date
close, and an after-ex-close evidence cutoff for this first synthetic
comparison?** Recommended answer: **Yes, for this synthetic fixture only**.

With prior raw close USD 100, ex-date raw close USD 98 and gross dividend
USD 2 per share, ending wealth is USD 100 and the expected gross return is
0%. Supplied total-return levels 100 -> 100 match. Raw levels 100 -> 98 yield
-2%; a second dividend credit on the already flat total-return series would
yield +2%. A 20% withholding convention would instead yield -0.4%.

The proposal values the declared entitlement at par on the ex-date even
though the synthetic payment date is later. The owner decision explicitly
covers that convention. The comparison cutoff is the artificial ex-date
close plus one second; all required evidence must be available by that
cutoff. Its output has no path to earlier signals or portfolio accounting.
Owner acceptance remains pending. Formal binding review and separately
authorized Step 3 implementation follow that semantic gate.

## Complete read scope

`build/dividend-design-evidence/read-scope.json` records 27 source paths,
SHA-256 identities and read extents. Reads covered:

| Source | Extent and purpose |
| --- | --- |
| Task card; `AGENTS.md` | Full; action scope, safety, writing, single writer and stop boundary |
| `docs/current_handoff.md`, controller, current roadmap, proposed next steps | Full; inherited checkpoint, workflow gates and Step 2 scope; older handoff task statements treated as historical context under the current card |
| `docs/north_star.md`, `docs/repo_map.md`, `PROJECT_SPEC.md` | Full; product scope, file orientation, evidence and timing boundaries |
| `docs/point_in_time_data_methodology_contract.md` | Heading/keyword index; lines 328-503, 516-584 and 717-773: availability/revisions, identities, events, field bases, typed missingness, calendar/currency, benchmark and blocking matrix |
| `docs/signal_execution_timing_contract.md` | Full, read in contiguous sections; incoming return, target/execution, anchor and benchmark alignment |
| `reports/split_proof_attempt.md`, `tests/test_demo_split_proof.py`, split golden | Full; adjusted-consumption baseline and preserved counterexample |
| `research/dividend_policy.py`, event-date and dividend-policy tests | Full; metadata-only acceptance, date refusals, input preservation and PIT-007 overlay refusal |
| `research/demo_v0.py` | Lines 147-198, 330-380 and event/config symbol index; start/failure/report sequencing and guard call sites |
| `research/synthetic_multifactor_backtest_demo.py` | Lines 200-260, 390-425 and event/config symbol index; same M3-01 boundaries |
| `.github/workflows/ci.yml`, `pyproject.toml` | Full; canonical local check commands and existing dependencies |
| `scripts/repo_map.py` | Lines 1-180 and 190-290; deterministic generated map behavior |
| `tests/test_project_structure.py` | Targeted symbol locations for generated-map and documentation checks; execution covered the entire file through pytest |
| `docs/engineering_log.md` | Final 95 pre-attempt lines; Step 1 evidence and historical incidents; earlier entries preserved |
| Herdr skill and both live coordination files | Full; CLI syntax, visible work, evidence handoff, route and adaptive waiting requirements |

The coordination sources are
`/Users/rhapsoul/Documents/Codex/Standards/herdr_pi_coordinator_v7_two_file/coordinator.md`
and its sibling `routing_table.json`. The operating card reads
`v7.24-draft` and `LIVE_OPERATING_CARD`; the routing file reads version
`7.24-draft` with status `TEMPLATE_NOT_ACTIVE`. This worker performed no model
dispatch or review routing; the coordinator owns resolving that status before
any later routed acceptance. The installed Herdr skill was read at
`/Users/rhapsoul/.codex/skills/herdr/SKILL.md`. Archived standards, private
market data and protected C were untouched.

## Verification and exact scope of evidence

The design checker operates on invented literals with Python standard-library
rational arithmetic and binary64 cross-checks. It supplies no importable
product comparison API, general event parser, schema, return adjustment or
backtester integration. Its evidence consists of 12 numeric scenario checks,
scalar-domain and cutoff/identity witnesses, consistency checks over all 40
documented matrix rows, and six isolated design-guard removals: **169
assertions passed**. Matrix text checks establish documented dispositions;
they provide no runtime enforcement evidence for the proposed API.

| Check | Observed result |
| --- | --- |
| Literal arithmetic/scenario and ablation checker | 169 assertions passed; 40 matrix rows; 12 numeric scenarios; 6 guard-removal witnesses |
| Focused existing consumer, split, event and overlay regressions | 94 passed in 2.96 s |
| Full existing repository suite | 2908 passed, 2 skipped, 1 warning in 41.08 s |
| Ruff | Passed |
| Compilation of source, tests, research and LEAN | Passed |
| Offline build with existing cached build tools | sdist and wheel built successfully |
| Unstaged, staged and source-base whitespace checks | Passed at QA checkpoint |
| Generated map | Refreshed; documentation file count 148 -> 149 |

The two skips concern platform `longdouble` precision. The warning is the
existing constant-input Spearman case. There were no failing product tests.
The full suite preserves the baseline test count and software behaviors;
Step 2 adds a design and local evidence rather than product tests or runtime.

Environment: macOS 27 arm64, Python 3.12.14, NumPy 2.5.3, pandas 3.0.5,
SciPy 1.18.1, pytest 9.1.1, Ruff 0.16.7 and build 1.6.1. The interpreter is
`/Users/rhapsoul/Documents/Codex/projects/efr-demo-v0-20260916/.venv/bin/python`.
`PYTHONPATH` selects this worker's `src`. Setuptools and wheel are absent
from that supplied environment. The offline build reads cached setuptools
and wheel without installing dependencies, using the cache paths recorded
in `qa-results.json`. An isolated downloading build was outside this
network-restricted, no-download attempt; Linux/Python 3.11 CI remains
unverified.

The following commands ran from the writer root. The evidence runner streams
each command's combined output through this active worker and saves its full
log, timestamp, exit code, duration and log hash. Pytest uses its default
repository-external temporary locations. Official reports were exercised only
through existing tests with temporary output paths.

```sh
DIVIDEND_PYTHON=/Users/rhapsoul/Documents/Codex/projects/efr-demo-v0-20260916/.venv/bin/python
"$DIVIDEND_PYTHON" build/dividend-design-evidence/check_design.py
"$DIVIDEND_PYTHON" scripts/repo_map.py
PYTHONPATH=src "$DIVIDEND_PYTHON" -m pytest -q tests/test_demo_split_proof.py tests/test_event_date_membership.py tests/test_dividend_policy.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py
PYTHONPATH=src "$DIVIDEND_PYTHON" -m pytest -q
"$DIVIDEND_PYTHON" -m ruff check .
"$DIVIDEND_PYTHON" -m compileall src tests research lean
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src:/Users/rhapsoul/.cache/uv/archive-v0/-XwZ4dJTzcJgXo7y:/Users/rhapsoul/.cache/uv/archive-v0/StOX7ZoawKj9Chai" "$DIVIDEND_PYTHON" -m build --no-isolation
git diff --check
git diff --cached --check
git diff --check 57035fbfe3f8495e6495feecb8afbc2664f3f237...HEAD
```

`build/dividend-design-evidence/run_local_qa.py` preserves the exact orchestration
and environment. `qa-results.json` identifies each complete log. Baseline
hashes for all 520 initially tracked files are retained in
`baseline-manifest.json`. Final preservation checks bind every existing
runtime, test, fixture, official report and log to those baseline bytes.

## Isolated design ablation

The pre-ablation design is saved as
`build/dividend-design-evidence/design.baseline.md`, with the same SHA-256 as
the delivered design above. Each experiment constructs a separate finite
predicate candidate, removes exactly one guard, and retains the original
fixture values. `scenario-results.json` saves every baseline/candidate
predicate set, concrete witness, result and restoration disposition.

| Removal hypothesis | Concrete witness | Baseline -> removal | Disposition |
| --- | --- | --- | --- |
| Permanent identity check is redundant for flat levels | Raw identity `SYNTH:ORD_A`, adjusted identity `SYNTH:ORD_B`, identical numeric ratios | Insufficient -> false numeric match | Restore |
| Explicit field basis is redundant when ratios agree | Declared price-return levels with a coincidentally flat ratio | Insufficient -> false numeric match | Restore |
| Event availability is redundant for historical ex-dates | Only `r2` known April 3, comparison cutoff April 2 | Insufficient -> false numeric match | Restore |
| Unique event/revision identity is redundant | Two identical copies of event A revision r1 | Insufficient -> false numeric match | Restore |
| Event coverage is redundant for a flat supplied return | One requested window, empty evidence | Insufficient -> vacuous false match | Restore |
| Typed observation status is redundant for finite values | Finite anchor carrying `PROVIDER_GAP` | Insufficient -> false numeric match | Restore |

Each candidate removes one predicate and loses a required refusal. The
supported outcome is **no design removal**. The proposal already uses one
event family, one window and one algebraic comparison. A generalized event
engine, normalization subsystem, schema registry, FX conversion and
reinvestment runtime remain excluded. The experiments measure predicate
count and verdict correctness; they make no runtime speed claim. They are
producer design ablations, with future implementation behavior and formal
lane acceptance still unverified.

## Process evidence and retained operational limits

Herdr `pane`, `tab` and `agent` command-group discovery printed their help and
returned exit 2. The initial chained discovery stopped at the first such
return; subsequent independent calls completed syntax discovery. These are
CLI-discovery outcomes, rather than failed product tests.

Live `herdr pane current --current`, workspace tab listing and agent listing
each returned exit 1, `PermissionDenied: Operation not permitted`. The
retained preflight repeats the reads once to save exact errors. Herdr layout,
process ownership, effective model/effort/tier, visible output and recipient
identity could therefore receive no independent worker-side verification.
No tab was created, closed or reassigned. Commands and QA streamed through
the current Codex session; a distinct Herdr shell-QA pane could not be
established. This limitation remains a visible-work verification gate for
the coordinator, rather than a claimed pass.

`git ls-remote origin refs/heads/main` returned exit 128 with
`Could not resolve host: github.com`. Local history supplies the fixed card
baseline. This attempt performed no remote publication, data downloads,
credential actions or private reads. `preflight.json` retains the complete
command results and inherited session locator.

The live operating card's **section 6 adaptive waiting correction** was read
for this attempt. It requires supported state queries, lifecycle/event waits
or adaptive polling selected from expected duration, progress, risk and
intervention needs, under runtime wait limits. Lightweight state checks
precede detailed transcript reads. Notifications supply hints; an unverified
resume mechanism requires an active wait or adaptive polling. Each wake
reconciles task/attempt, report and process state and handles completed or
blocked work independently. Silence supplies no restart evidence. Full report
bytes precede notification, and the recipient verifies the report before
acceptance or successor dispatch. This entry records the current correction;
earlier historical incident entries retain their bytes.

No delegated task remains outstanding. This worker's stop boundary is the
local draft and owner decision. Automatic post-turn monitoring or resumption
is unverified and is outside the delivery claim.

## Remaining gates and handoff

The owner semantic decision, coordinator verification of exact delivered
bytes and visible execution, formal independent CRITICAL reviews and binding
acceptance remain pending. Native model settings and routing-file status need
coordinator verification for that later lifecycle. Linux CI and future runtime
comparison enforcement remain unverified. Step 3 requires its own explicit
implementation scope after acceptance.

The four intended repository files are this report, the proposed design,
`docs/engineering_log.md` and the regenerated `docs/repo_map.md`. Local
scenario scripts, baseline copies, logs and manifests stay in
`build/dividend-design-evidence/`; their inclusion in local evidence grants
no product capability. Every new documentation passage is English. Immutable
historical language exceptions remain preserved.

## Version-management blocker and writer release

The local staging attempt returned exit 128:

```text
fatal: Unable to create '/Users/rhapsoul/Documents/Codex/projects/efr-dividend-design-20260918/.git/index.lock': Operation not permitted
```

The exact four-file `git add` command and result are retained in
`build/dividend-design-evidence/commit-attempt.json`. The session exposes
`.git` as read-only; no commit was created and HEAD remains
`57035fbfe3f8495e6495feecb8afbc2664f3f237`. The candidate remains unstaged.
No elevated permission or alternate write surface was attempted.

Final delivery locations, relative to the exact writer root above:

| Artifact | Purpose |
| --- | --- |
| `build/dividend-design-evidence/delivery-manifest.json` | Absolute paths and SHA-256 hashes for all four repository files, with source HEAD and draft status |
| `build/dividend-design-evidence/evidence-manifest.json` | Absolute paths and SHA-256 hashes for the retained local evidence, including commands, logs, baseline, scenarios, final checks and delivery patch |
| `build/dividend-design-evidence/delivery.patch` | Complete four-file change for a Git-writable coordinator session |
| `build/dividend-design-evidence/final-checks.json` | Final documentation QA, whitespace, ASCII/link checks, generated-map determinism and baseline preservation results |
| `build/dividend-design-evidence/task_record.md` | Final task/session locator, stop boundary, blockers and writer-release record |

The manifests exclude their own bytes and are identified by their hashes in
the final handoff. The evidence manifest includes the delivery manifest.
The full report, final checks and manifests are saved before recipient
notification. Herdr recipient discovery is denied by the sandbox, so direct
coordinator notification remains unavailable; the final response supplies
the report locator and exact manifest hashes. The coordinator can inspect the
existing worker without a replacement dispatch.

**Writer responsibility is released at final handoff.** No worker or QA process
remains running after the saved checks. The coordinator owns the local commit
from these exact bytes in a Git-writable session, visibility/native-setting
verification and routing of the owner decision. Release preserves this
proposal's unaccepted status and the explicit stop before product
implementation or publication.
