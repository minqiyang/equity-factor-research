# Step 1: Synthetic Split Consumption Proof

The two demo consumers preserve the committed adjusted split economics in 20
new deterministic cases. Raw-price contamination produces the committed
negative counterexample. Runtime behavior and official artifacts retain their
baseline bytes.

## Identity and scope

- Source HEAD: `744f4922485b34317bb472e43bf5eb79e7f713e7`, the local merge
  commit for PR #219, verified through Git history.
- Writer branch: `codex/split-proof-20260918`.
- Authorized slice: Step 1 of `docs/proposed_next_steps_roadmap.md`.
- New test: `tests/test_demo_split_proof.py`, SHA-256
  `653d0e80146fed242c4574ddb7194601e0975d4d6e26231b2ef59737c757b12f`.
- Immutable golden: `tests/fixtures/campaign_runner_v1/split_corporate_action.json`,
  SHA-256 `90487b6ffabdc5b5d9eca9220712e5f1e84789658b5fa1fad614205038c1a52a`.
- Existing-file changes: append-only engineering evidence and the generated
  repository-map test count. Official configurations, runtime sources,
  reports, attempt logs, fixture bytes, and earlier engineering entries are
  preserved. A SHA-256 manifest of every baseline tracked file is retained at
  `build/split-proof-evidence/baseline-manifest.json`.

## Fixture and independent oracle

Eight synthetic observed rows span 2026-03-26 through 2026-04-06. Test-only
`dataclasses.replace` overrides select both assets, rebalance daily, apply the
golden's 10 bps transaction cost, and retain zero slippage. Demo v0 computes
its actual momentum with lookback 2 and skip 0. M3-01 preprocesses and combines
fixed two-asset synthetic factor panels. Both runners call their actual
backtester, benchmark builder, report writer, and attempt logger.

The golden's April 1-2 anchors remain 50 -> 50 for T000 and 100 -> 100 for
T001. Initial deployment precedes April 1: March 31 for Demo v0 and March 27
for M3-01. Tests require actual 0.5/0.5 holdings at the beginning of the event
interval. Initial turnover 1 and cost impact 0.001 receive separate
assertions. The event row uses the previous observed row's signal.

| Event measurement | Adjusted oracle | Raw contamination oracle |
| --- | --- | --- |
| Asset returns, T000 / T001 | 0 / 0 | -0.5 / 0 |
| Gross portfolio return | 0 | -0.25 |
| Pre-trade drift, T000 / T001 | 0.5 / 0.5 | 1/3 / 2/3 |
| Undivided turnover | 0 | 1/3 |
| Cost impact | 0 | 0.00025 |
| Net event return | 0 | -0.25025 |

Expected values come directly from the committed `expected` and `forbidden`
objects, with their absolute tolerance 1e-15 and relative tolerance zero.
The tests recover pre-trade drift from public holdings minus signed trades.
Campaign calculation helpers supply no test oracle. The raw case substitutes
100 -> 50 for T000; each adjusted gross, drift, turnover, and cost assertion
raises the expected assertion failure when applied to the raw result.

## Coverage and retained attempts

Twelve cases cover two consumers, adjusted/raw inputs, and single/empty/repeated
event dates. Every case compares absent metadata against supplied metadata,
including exact prices passed to the backtester, source index, event table,
holdings, signed/absolute trades, gross/net returns, turnover, each cost
component, equity, benchmark paths, and the timing ledger. Eight further
cases cover absent, malformed, and missing dates plus separate cash-overlay
refusal for both consumers. Each refusal follows a successful run and
preserves the previous report and attempt-log byte prefix, exact error type
and reason, and input objects. Fixture teardown checks the frozen
configurations and original golden bytes.

Each focused execution retains 40 runner invocations: 32 successes and eight
expected refusals, each with its start record. Raw contamination receives a
successful diagnostic outcome under the current supplied-series contract;
the independent test assertions expose its economic mismatch. The existing
regressions also cover catchable interruption and logging-readiness failure.

## QA and environment

Environment: macOS 27 arm64, Python 3.12.14, NumPy 2.5.3, pandas 3.0.5,
SciPy 1.18.1, pytest 9.1.1, Ruff 0.16.7, build 1.6.1. The supplied interpreter
resides in the adjacent Demo v0 virtual environment. `PYTHONPATH=src` binds
the local runtime. Package discovery initially raised `PackageNotFoundError`
for setuptools; setuptools and wheel are absent from that virtual environment.

| Check | Result |
| --- | --- |
| Existing focused baseline | 78 passed, 3.05 s |
| Initial new proof | 20 passed, 0.56 s |
| Isolated helper ablation | 20 passed, 0.63 s |
| Baseline archive suite | 2888 passed, 2 skipped, 1 warning, 43.73 s |
| Candidate full suite after harness/map correction | 2908 passed, 2 skipped, 1 warning, 42.91 s |
| Ruff | Passed |
| Compile source, tests, research, LEAN | Passed |
| Default isolated build | Environment failure: dependency download could not resolve PyPI |
| Offline build with cached setuptools 84.0.0 and wheel 0.48.0 | sdist and wheel built successfully |

The two skips concern platform long-double precision. The warning is the
existing constant-input Spearman case. The baseline archive suite uses the
archived pytest configuration and source tree; research imports may resolve
through the working root, whose runtime bytes match the baseline manifest.
This producer QA establishes local software behavior. Linux/Python 3.11 CI
and independent review remain coordinator gates.

The first candidate suite retained 102 failures, 2806 passes, two skips, and
one warning. Its explicit in-repository `--basetemp` triggered 101 existing
repository-external output-path guard failures; the remaining failure was the
generated map's stale test count. The corrected run uses pytest's standard
temporary location and the regenerated map. Runtime guards and tests retain
their original bytes. The failed download build and failed harness run remain
in `build/split-proof-evidence/build.log` and `pytest.log`.

### Exact commands

Commands ran from the writer root. The shell variable below abbreviates the
same absolute interpreter used by every execution. Each run's combined output
is retained under `build/split-proof-evidence/` with the names in the hash table.

```sh
SPLIT_PYTHON=/Users/rhapsoul/Documents/Codex/projects/efr-demo-v0-20260916/.venv/bin/python
PYTHONPATH=src "$SPLIT_PYTHON" -m pytest -q tests/test_campaign_paths.py tests/test_event_date_membership.py tests/test_dividend_policy.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py
PYTHONPATH=src "$SPLIT_PYTHON" -m pytest -q tests/test_demo_split_proof.py --basetemp=build/split-proof-evidence/focused-01
PYTHONPATH=src "$SPLIT_PYTHON" -m pytest -q tests/test_demo_split_proof.py --basetemp=build/split-proof-evidence/ablation-01
PYTHONPATH=src "$SPLIT_PYTHON" -m pytest -q --basetemp=build/split-proof-evidence/full-suite
"$SPLIT_PYTHON" scripts/repo_map.py
PYTHONPATH=src "$SPLIT_PYTHON" -m pytest -q
mkdir -p build/split-proof-evidence/baseline-source
git archive 744f4922485b34317bb472e43bf5eb79e7f713e7 | tar -x -C build/split-proof-evidence/baseline-source
PYTHONPATH=src "$SPLIT_PYTHON" -m pytest -q -c build/split-proof-evidence/baseline-source/pyproject.toml build/split-proof-evidence/baseline-source/tests
"$SPLIT_PYTHON" -m ruff check .
"$SPLIT_PYTHON" -m compileall src tests research lean
"$SPLIT_PYTHON" -m build
mkdir -p build/split-proof-evidence/tmp
TMPDIR="$PWD/build/split-proof-evidence/tmp" PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src:/Users/rhapsoul/.cache/uv/archive-v0/-XwZ4dJTzcJgXo7y:/Users/rhapsoul/.cache/uv/archive-v0/StOX7ZoawKj9Chai" "$SPLIT_PYTHON" -m build --no-isolation
git diff --check
```

The offline command reads existing cached build tools and leaves the supplied
virtual environment unchanged. Temporary suite outputs contain synthetic
fixtures only. Official demo commands were exercised solely through tests
with temporary report and log paths.

## Isolated ablation

The baseline test had one single-use `_event_values(result, event_date)`
helper. The experiment inlined its body at the call site, preserving every
assertion and tolerance. The file decreased from 221 to 217 lines and lost
one helper and one call. The retained baseline file is
`build/split-proof-evidence/test_demo_split_proof.baseline.py`, SHA-256
`28586309537452149de856182b7748162d9755cb937f37db3615dbce9ff30496`.

All 12 `split_evidence.json` files, 20 attempt logs, and 20 temporary reports
matched after replacing only the `focused-01`/`ablation-01` output-directory
labels. Tests retained exact metadata equivalence, all golden values, refusal
reasons, input preservation, and report/log retention. The 0.56/0.63 second
single executions establish successful runs; they provide no speedup claim.
The four-line simplification is retained. The backtester capture wrapper,
input snapshots, independent golden assertions, and refusal checks remain
necessary coverage.

The following reconstruction recovers the pre-ablation test bytes from the
candidate for an isolated repeat. Execute the reconstructed test at the
original test path and keep each run's temporary outputs distinct.

```python
from pathlib import Path
candidate = Path("tests/test_demo_split_proof.py").read_text()
start = candidate.index("    # Public post-trade weights")
end = candidate.index("    for key, value in values.items():", start)
body = candidate[start:end]
helper = "def _event_values(result, event_date):\n" + body.replace(
    "    values = {", "    return {"
) + "\n\n"
baseline = candidate[:start] + "    values = _event_values(result, event_date)\n" + candidate[end:]
offset = baseline.index('@pytest.mark.parametrize("raw"')
baseline = baseline[:offset] + helper + baseline[offset:]
Path("build/split-proof-evidence/reconstructed-baseline.py").write_text(baseline)
```

### Retained QA evidence hashes

Paths below are relative to `build/split-proof-evidence/`. They remain local
producer evidence; this committed report preserves the outcomes and hashes.

| File | SHA-256 |
| --- | --- |
| `baseline-focused.log` | `33a3a2a3228d6330a9bfcf9598ed31a16900e14cb004fc198c99ceae701362b4` |
| `focused-01.log` | `e4220b5ffb877eb0c15e85c72deac7eba9f20aaa7ccbead8b89130588c7ac65d` |
| `ablation-01.log` | `80e97c3cdcd83cba9f794fff45bd5ec40eda8378389ac92ed237856bf85bfb7c` |
| `ablation-comparison.json` | `f1bc315892a28e0443759635c8606cbd88a1d6b2c04264ce80f94d053585ab55` |
| `baseline-pytest.log` | `1005b6c5449bb05d5fbfde6c185f8ed3aae03485dd2779c5ab1fd5ba85698336` |
| `pytest.log` | `5ecc5a158e94e823390c77aa5d53804d46dd6d62010c9bf616eb458439102c48` |
| `pytest-02.log` | `9dcad68936ca5f25f91a3bbf19b9d0601dbc053c65e9b68e36383623570a3bb7` |
| `ruff.log` | `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` |
| `compile.log` | `0da681cd18f7e76ccba48f18de6729ec3cf973d40877b3d2ab4080bc617fa8ff` |
| `build.log` | `47587da943b5272c96d14f0abd0d99e8703939dd45c05601b15def40c6ab60d8` |
| `build-offline.log` | `ffbbee583750ef7d3003083303d594f6a773a7c52a9f1d5264e6a820feb91674` |

## Limitations and next gate

This increment proves consumption of one already adjusted synthetic split
series through both demo consumers. Event values remain opaque metadata;
independent split/dividend reconciliation, new schemas, price reconstruction,
private data, campaign execution, and official report regeneration remain
outside this slice. Zero slippage retains the diagnostic ceiling. Milestone 3
remains in progress. Historical records retain their original language and
bytes; this increment's documentation is English.

The first next gate is coordinator verification of the committed candidate,
exact-head CI and independent review before any coordinator-owned publication.
The worker's delivery ends at a local commit and writer release. Step 2's
dividend economic-comparison design and its owner semantic acceptance remain
a separate gate.

## Writer handoff and commit blocker

Implementation, deterministic QA, isolated ablation, preservation checks, and
English incident records are complete. The final documentation regression
passed 66 tests, and Ruff passed again. The ablation reconstruction reproduced
the saved baseline bytes exactly. The final preservation check verified every
pre-existing tracked file against the baseline manifest, with only the
append-only engineering entry and generated map count changed.

Local staging failed with exit 128:

```text
fatal: Unable to create '.git/index.lock': Operation not permitted
```

This session's filesystem permissions expose `.git` as read-only. The command
was `git add tests/test_demo_split_proof.py docs/engineering_log.md
docs/repo_map.md reports/split_proof_attempt.md`. The candidate remains
unstaged; a new commit SHA is unavailable. Current HEAD remains
`744f4922485b34317bb472e43bf5eb79e7f713e7`. Push, PR, and merge actions were
outside worker scope and were never invoked.

The immediate handoff gate is a local four-file commit in an authorized
Git-writable coordinator session, followed by its exact-head CI/review path.
`build/split-proof-evidence/delivery.patch` contains the complete four-file
change, including this blocker record. Writer responsibility is released upon
the final response; all working files and local QA evidence remain available.
