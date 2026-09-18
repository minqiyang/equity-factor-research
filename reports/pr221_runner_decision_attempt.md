# PR221 Delegated Runner-Outcome Decision Attempt 01

The delegated decision selects **diagnostic-only completion** for the
synthetic ordinary-dividend comparison. Completed `MATCHED`, `MISMATCHED`
and valid `INSUFFICIENT_EVIDENCE` results permit terminal attempt `success`
after evidence retention and report/log completion. Negative outcomes remain
explicit and block the affected economic acceptance claim. `NOT_REQUESTED`
preserves the existing default path. Input refusals, unexpected exceptions,
interruptions and infrastructure failures retain their failure behavior.

## Authority, identity and scope

- Decision date: 2026-09-18. Owner delegation names GPT-6 Astra Max, DESIGN,
  CRITICAL structural `SCHEMA_PROTOCOL_CONTRACT`. Model/effort names record
  the dispatch instruction; this worker performed no independent host-model
  or service-tier inspection.
- Card: `coord/pr221_astra_decision_card.md` under
  `/Users/rhapsoul/Documents/Codex/projects/efr-demo-first-docs-20260915/`.
  Card SHA-256:
  `63513da756d935defa77249899919c878b7bdf759593b04bc4e8e922642866ca`.
- Writer root:
  `/Users/rhapsoul/Documents/Codex/projects/efr-pr221-astra-decision`.
- Branch: `codex/pr221-astra-outcome-decision`. Clean starting HEAD:
  `3cee36c3a335e69a21e29edd6246fc0421787ce2`.
- One writer edited the design, this report and an appended engineering
  record. Local scripts, scenarios and logs live under ignored
  `build/pr221-runner-decision-evidence/`.
- The complete prior Astra and Grok reviews, owner economic acceptance,
  current design and precision-repair report were read. Source inspection
  covered both runners' run/report/attempt paths, event/overlay guards,
  relevant tests, AGENTS, North Star, current/proposed roadmaps, repository
  map, CI workflow and existing dependency metadata. The read-evidence
  manifest preserves the four coordinator-document hashes.

The [design](../docs/synthetic_event_reconciliation_design.md#diagnostic-labels-and-runner-effect)
contains the normative outcome and failure tables, ordered logging behavior,
negative-evidence retention and Step 3 acceptance requirements. Its SHA-256 is
`a7b7ccdb4086e97b46dae484a85bc74c717aa7baf1eed344c74cab5e757ee843`.
GROK-221-ADV-3 now has a selected policy; independent review disposition and
binding acceptance remain pending. The owner A/B choice is resolved.

## Chosen policy and trade-off

| Completed comparison | Attempt | Selected diagnostic report |
| --- | --- | --- |
| `MATCHED` | `success` | Replace after retaining scoped match evidence. |
| `MISMATCHED` | `success` | Replace after retaining the mismatch; display the negative result beside completion. |
| `INSUFFICIENT_EVIDENCE` | `success` | Replace after retaining reasons and coverage; display the evidence gap beside completion. |
| `NOT_REQUESTED` | Existing completion behavior | Preserve the existing report/log sequence and format; conceptual coverage `0/0`, no percentage or new comparison fields. |

Execution success states that the diagnostic work completed. Each economic
claim depends on the comparison status and requested-window coverage. A
mixed request retains every item; one insufficient item or mismatch blocks
an aggregate match. This lets the demonstration expose missing and contrary
evidence in its current report. Strict failure would keep the previous report
and turn an expected negative diagnostic into a runner exception. The chosen
policy requires readers and consumers to inspect both status dimensions.

An inspectable request with absent/empty evidence follows D25/D26. Typed
evidence deficiencies, including D30/D31 invalid numeric evidence, retain
their matrix reasons. Malformed request structure raises `TypeError` or
`ValueError`; existing malformed-date, source-date, config, price, volume,
factor and overlay inputs retain their refusals. An actual comparator
exception propagates as an execution failure. D32/D47 remain reasoned numeric
diagnoses, and D41/D46 retain their exact rational mismatch outcomes.

The future explicit-request order is start -> existing guards and simulation
-> compare and retain each item -> prepare and replace the diagnostic report
-> append success. Each completed item survives a later item failure.
Evidence-append failure blocks report replacement. Report preparation uses a
temporary file on the same filesystem; terminal success follows replacement.
A late success-log failure raises and leaves an incomplete attempt even when
the new report already exists. This scope specifies no cross-file crash
transaction. Prior log prefixes and mismatches survive later matches.

The four accepted economic choices remain byte-identical in the owner
decision section: pre-ex-date holder gross entitlement, zero withholding,
theoretical fractional ex-close reinvestment and after-ex-close cutoff.
The evidence boundary, fixture definitions, timing/revisions, exact rational
contract and D01-D47 matrix also retain their baseline bytes. Runtime,
schemas, configurations, fixtures, official reports/attempt logs and both
historical Step 2 reports retain their original bytes. Comparison output has
no accounting or signal feedback path. Every calculation here uses synthetic
literals or existing committed synthetic test fixtures.

## Existing-runner observations

`probe_existing_runners.py` exercised 22 scenarios per consumer, using short
synthetic configurations and output paths under the evidence directory.
All 44 scenario assertions passed. These are checks of the current runtime;
the current runners expose no economic-comparison request API.

| Boundary exercised in both consumers | Observed behavior |
| --- | --- |
| Default, empty metadata, repeated-date metadata with opaque values | `started`, pipeline, report write, `success`; default log shape preserved. |
| Zero/empty overlay; wrong event container/index; missing/off-source event date; invalid declared source, config, volume or price | Original typed refusal; `started` then `failure`; previous report preserved. |
| Pipeline exception; `KeyboardInterrupt`; `SystemExit` | Original exception propagates; `failure` or `interrupted` retained; previous report preserved. |
| Start-log failure | `RuntimeError`; pipeline remains unstarted; previous report preserved. |
| Report preparation failure | Failure retained; previous report preserved. |
| Injected partial report write followed by I/O failure | Failure retained; previous report bytes damaged. Current direct writes provide no atomic replacement guarantee. |
| Terminal success-log failure after report write | Logging error propagates; new report exists; log retains an incomplete `started` attempt. |
| Pipeline error plus unavailable failure log | Original pipeline exception preserved; retained start remains incomplete. |
| Failure followed by success | Earlier failure and complete log prefix preserved under successive attempt IDs. |

The partial-write and late-log observations are retained negative evidence.
The design assigns bounded report preparation/replacement requirements to the
future opt-in path and leaves default runtime behavior intact. Runtime
enforcement of that future path remains unverified.

## Isolated design ablation

`check_decision.py` checks frozen economic sections, all 47 matrix rows,
15 rational witnesses, 22 finite lifecycle traces and all 24 permutations of
start/result-retention/report/success. Exactly one successful opt-in ordering
satisfies the retained constraints. The checker passed 103 assertions.

Each removal below changes one constraint in the local trace checker. Its
witness violates that constraint alone; removal admits the witness and
restoration rejects it. The saved design baseline remains intact.

| Removed constraint | Admitted counterexample | Disposition |
| --- | --- | --- |
| Separate attempt/comparison status | A completed mismatch is displayed as a match. | Retain |
| Evidence retention before replacement | New report replaces the old report before negative evidence is retained. | Retain |
| Exception propagation | A true execution error returns successful diagnostic completion. | Retain |
| Explicit opt-in | Default no-request execution gains a comparison record and match. | Retain |
| Append-only history | A later outcome erases the earlier mismatch. | Retain |
| Preservation before replacement | A preparation error leaves partial bytes in the selected report. | Retain |
| Success after report replacement | Terminal success precedes actual report replacement. | Retain |

Supported outcome: **no further design removal**. The chosen policy uses the
existing attempt statuses and one diagnostic path; a strict-mode option and
additional aggregate statuses add no required behavior. These finite traces
test design consistency and retention obligations. They establish no future
runtime enforcement, crash recovery guarantee or performance measurement.

## QA and reproducibility

| Check | Observed result |
| --- | --- |
| Design checker and ablation | 103 assertions; 22 traces; 15 arithmetic witnesses; seven retained guards |
| Current runner probes | 44 scenarios passed |
| Documentation QA | 66 passed |
| Focused consumer/split/event/overlay tests | 94 passed in 3.03 s |
| Full repository suite | 2908 passed, 2 skipped, 1 warning in 42.87 s |
| Ruff, source/tests/research/LEAN compilation, offline sdist/wheel build | Passed |
| Generated repository map | Regenerated with identical bytes |
| Whitespace and preserved-file manifest | Checked again on the released files; detailed results accompany the release manifest |

The two skips concern platform `longdouble` precision; the warning is the
existing constant-input Spearman case. Local environment: macOS 27.0 arm64,
Python 3.12.14, NumPy 2.5.3, pandas 3.0.5, SciPy 1.18.1, pytest 9.1.1,
Ruff 0.16.7 and build 1.6.1. QA used the existing interpreter
`/Users/rhapsoul/Documents/Codex/projects/efr-demo-v0-20260916/.venv/bin/python`
with `PYTHONPATH=src`. The build reused the previously recorded local
setuptools/wheel cache through `--no-isolation`; no installation ran.

Reproduction commands from this writer root:

```sh
PR221_PYTHON=/Users/rhapsoul/Documents/Codex/projects/efr-demo-v0-20260916/.venv/bin/python
"$PR221_PYTHON" build/pr221-runner-decision-evidence/check_decision.py
PYTHONPATH=src "$PR221_PYTHON" -c "import runpy; runpy.run_path('build/pr221-runner-decision-evidence/probe_existing_runners.py', run_name='__main__')"
PYTHONPATH=src "$PR221_PYTHON" build/pr221-runner-decision-evidence/run_local_qa.py
```

The probe and QA scripts create fresh output files and refuse to overwrite
their prior run directories/logs. Reproduction uses a copied script with a
fresh evidence destination. `qa-results.json` records commands, timestamps,
exit codes, durations and log hashes. `design-results.json` records the
individual arithmetic/trace/ablation witnesses. `existing-runner-results.json`
records actual error types, message text, event order and output hashes.

Initial evidence-tool failures remain saved: direct script invocation
could not import `research` with `PYTHONPATH=src`, corrected by root-context
`runpy`; a prose-anchor check treated wrapped indentation as significant,
corrected by whitespace normalization. The first shell pipeline reported the
`tee` exit code; the rerun used `pipefail`. Both corrected checks passed.
The first release style check included preserved historical prose; its
scope was corrected to newly added prose. These failures changed no product
source or product tests.

## Version management, release and remaining gates

Local staging returned exit 128: `.git/index.lock` creation received
`Operation not permitted`. The sandbox exposes Git metadata as read-only.
HEAD remains `3cee36c3a335e69a21e29edd6246fc0421787ce2`; this worker created
no commit. The release package under
`build/pr221-runner-decision-evidence/` contains `delivery.patch`,
`release-manifest.json` and `evidence-manifest.json`. The release manifest
binds all three delivery files and the patch by SHA-256; the evidence
manifest binds the local scripts, logs and preserved baselines. Patch replay
verification and final QA are recorded there. Writer responsibility is
released with the final manifest handoff for coordinator commit.

Genuine remaining gates are coordinator version management/publication under
its own authority, exact-head CI including Linux/Python 3.11, fresh two-seat
CRITICAL independent reviews, binding-plan acceptance and separately scoped
Step 3 implementation with behavioral validation. Local producer QA supplies
no self-acceptance. This worker performed no publication or runtime/schema
implementation. Every newly authored documentation passage is English;
immutable historical language exceptions retain their bytes.
