# PR221 Precision-Contract Repair Attempt 01

The local repair specifies exact rational comparison, conversion semantics,
and an unrounded absolute tolerance for the synthetic ordinary-dividend
design. Owner-approved economics are unchanged. Runtime comparison, schemas,
and publication remain outside this attempt.

## Task, ownership and candidate

- Task card:
  `/Users/rhapsoul/Documents/Codex/projects/efr-demo-first-docs-20260915/coord/pr221_fix_card.md`.
- Writer root:
  `/Users/rhapsoul/Documents/Codex/projects/efr-pr221-fix`.
- Branch: `codex/pr221-precision-fix`.
- Repair baseline: `3a040b67d874dc850772d8053fd8c15cc9e29060`.
- Source-base merge: `57035fbfe3f8495e6495feecb8afbc2664f3f237`.
- Initial working tree was clean on the repair baseline. One worker wrote
  this root. No child writers or reviewers were started.
- Lane on the card: FIXER, Grok latest xhigh; CRITICAL structural
  `SCHEMA_PROTOCOL_CONTRACT` candidate remains unaccepted.
- Allowed writes: design, report, engineering evidence, and map refresh.
  Historical reports, owner decision, runtime, config, fixture, and official
  report bytes are preserved.
- Design:
  `docs/synthetic_event_reconciliation_design.md`, SHA-256
  `b0055d07206297a11070af9776932bc9b9a542d89fa3dd185456fcb54cd39f60`.
- Local evidence directory:
  `build/pr221-precision-fix-evidence/` (gitignored `build/`).

## Finding dispositions

| Finding | Severity | Disposition |
| --- | --- | --- |
| AUDIT-001 finite-rounding false match | MATERIAL | Repaired. Normative match uses exact rationals after `to_rational`. Witness D41 is `MISMATCHED`, exact delta `-1`. |
| GROK-221-ADV-1 injected vs reconstructed levels | ADVISORY | Repaired. D04/D05/D44 are injected decimal `r_supplied` literals. D42/D43/D45 are explicit `A_p`/`A_e` binary64 literals with unrounded computed deltas. |
| GROK-221-ADV-2 default reason tokens | ADVISORY | Repaired. Comparable success uses `within_tolerance`. Comparable difference uses `return_difference`. Those tokens appear on every comparable matrix row. |
| GROK-221-ADV-3 runner effect of diagnostic labels | ADVISORY | Recorded existing diagnostic/exception split and M3-08 metadata compatibility. Step 3 mapping of `MATCHED` / `MISMATCHED` / `INSUFFICIENT_EVIDENCE` onto demo-runner attempt success or official-report replacement remains an owner-semantic implementation question. This repair leaves that mapping unset and invents no new outcome policy. |
| GROK-221-ADV-4 D31 supplied levels | ADVISORY | Repaired. D31 names raw anchors `P_p`, `P_e` and supplied levels `A_p`, `A_e` together with `D`. |

Owner semantic acceptance remains the four synthetic knobs bound to draft
`a6a22e8a3f9007dfe439192aae1dd433d6a093f7`: pre-ex-date holder gross
entitlement, zero withholding, theoretical fractional ex-close reinvestment,
and after-ex-close evidence cutoff. The 100 / 98 / 2 zero-return example is
unchanged.

## Numeric contract

Admitted inputs are real non-Boolean finite scalars equal to finite IEEE-754
binary64 encodings. Conversion is the unique dyadic rational of that
encoding:

```text
to_rational(x) = Fraction(*float(x).as_integer_ratio())
```

Formulas run in Q. Absolute tolerance is the exact decimal `1/10^12`.
Relative tolerance is zero. The match predicate uses the unrounded rational
delta. Display rounding occurs after the predicate.

A proven error bound is a permitted equivalent when it selects one side of
`1/10^12`. A bound that includes both sides, with no rational
classification produced, is `INSUFFICIENT_EVIDENCE` /
`comparison_precision_insufficient`.

Finite-rounding witness D41: `P_p=1`, `P_e=1e16`, `D=1`, `A_p=1`,
`A_e=1e16`. Every input is a positive finite exact binary64 value.
`1e16 + 1` rounds to `1e16` in binary64, so the documented float formulas
yield delta `0.0`. Exact evaluation yields delta `-1`. Required outcome:
`MISMATCHED`, `1/1`, `return_difference`.

Overflow/range witness D46: `P_p=2^-1074`, `P_e=1`, `D=1`, `A_p=1`,
`A_e=1`. Exact evaluation is finite and `MISMATCHED`. Diagnostic binary64
evaluation is nonfinite. An implementation that emits no rational or
proven-bound classification uses D32 `arithmetic_nonfinite`.

## Isolated design ablation

The repaired contract is the ablation baseline. Each experiment removes one
guard in the local checker, records a concrete witness, and restores the
guard. Product tests and runtime files were left in place.

| Removal hypothesis | Concrete witness | Baseline -> removal | Disposition |
| --- | --- | --- | --- |
| Binary64 `abs(delta) <= 1e-12` is sufficient | D41: float delta `0.0`, exact delta `-1` | MISMATCHED -> false MATCHED | Restore |
| D31 may omit supplied-level positivity | `A_e=0` on the base fixture | INSUFFICIENT `numeric_domain_invalid` -> comparable MISMATCHED | Restore |
| Rounding delta to 12 decimal places preserves the predicate | D45 unrounded `3519/3518437208883200`; `round(float, 12) == 1e-12` | MISMATCHED -> false MATCHED | Restore |
| Reconstructed `A_e=A_p*(1+5e-13)` equals injected `5/10^13` | D42 unrounded `3519/7036874417766400` | distinct documented deltas -> collapsed literals | Restore |
| `to_rational` may accept Booleans | `True.as_integer_ratio() == (1, 1)` | D30 `numeric_invalid` -> treated as `1` | Restore |

Supported outcome: **no design removal**. Exact conversion, unrounded
tolerance, supplied-level domain, injected-versus-reconstructed literals,
and Boolean refusal before conversion remain. The experiments measure
predicate verdicts on invented literals. They make no runtime-speed claim
and leave future comparator enforcement unverified.

## Verification and exact scope of evidence

The design checker uses only the Python standard library (`fractions`,
`math`, `json`, `re`, `pathlib`). It supplies no importable product
comparison API.

| Check | Observed result |
| --- | --- |
| Literal arithmetic, matrix-token, conversion, witness, domain and ablation checker | 110 assertions passed; 47 matrix rows; 5 restored ablations |
| Documentation QA `tests/test_project_structure.py` | 66 passed in 0.45 s |
| Focused existing consumer, split, event and overlay regressions | 94 passed in 3.15 s |
| Full existing repository suite | 2908 passed, 2 skipped, 1 warning in 44.21 s |
| Ruff | Passed |
| Compilation of source, tests, research and LEAN | Passed |
| Offline build with existing cached build tools | sdist and wheel built successfully |
| Unstaged, staged and source-base whitespace checks | Passed |
| Generated map | Regenerated; bytes identical to baseline (`docs/` count remains 149) |

The two skips concern platform `longdouble` precision. The warning is the
existing constant-input Spearman case. Runtime, tests, fixtures, official
reports, `reports/dividend_design_attempt.md`, and owner-decision economics
are unchanged.

Environment: macOS Darwin 27.0.0 arm64, Python 3.12.14, NumPy 2.5.3,
pandas 3.0.5, SciPy 1.18.1, pytest 9.1.1, Ruff 0.16.7 and build 1.6.1. The
interpreter is
`/Users/rhapsoul/Documents/Codex/projects/efr-demo-v0-20260916/.venv/bin/python`.
`PYTHONPATH` selects this worker's `src`. Setuptools 84.0.0 and wheel 0.48.0
are read from the uv cache paths below. Linux/Python 3.11 CI remains
unverified.

The following commands ran from the writer root. Combined output streamed
through this worker. Full logs, timestamps, exit codes, durations and log
hashes are in `build/pr221-precision-fix-evidence/qa-results.json`.

```sh
PR221_PYTHON=/Users/rhapsoul/Documents/Codex/projects/efr-demo-v0-20260916/.venv/bin/python
"$PR221_PYTHON" -B build/pr221-precision-fix-evidence/check_design.py
"$PR221_PYTHON" scripts/repo_map.py
PYTHONPATH=src "$PR221_PYTHON" -m pytest -q tests/test_project_structure.py
PYTHONPATH=src "$PR221_PYTHON" -m pytest -q tests/test_demo_split_proof.py tests/test_event_date_membership.py tests/test_dividend_policy.py tests/test_demo_v0.py tests/test_synthetic_multifactor_backtest_demo.py
PYTHONPATH=src "$PR221_PYTHON" -m pytest -q
"$PR221_PYTHON" -m ruff check .
"$PR221_PYTHON" -m compileall src tests research lean
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src:/Users/rhapsoul/.cache/uv/archive-v0/-XwZ4dJTzcJgXo7y:/Users/rhapsoul/.cache/uv/archive-v0/StOX7ZoawKj9Chai" "$PR221_PYTHON" -m build --no-isolation
git diff --check
git diff --cached --check
git diff --check 3a040b67d874dc850772d8053fd8c15cc9e29060...HEAD
```

`build/pr221-precision-fix-evidence/run_local_qa.py` preserves that
orchestration. QA log SHA-256 values:

| Step | exit | duration_s | log SHA-256 |
| --- | --- | --- | --- |
| check_design | 0 | 0.023 | `64929613ac32294a1b70a95ceefd8f74de73f52c5d4117fa081716a3263123b9` |
| repo_map | 0 | 0.031 | `189b944325521e89bbd70a379e34aec8b75ee20a1a00aa4a4f89c13cfdc2da5c` |
| docs_qa | 0 | 0.582 | `cff632790057df56d0feddd689e167b6b61fab93212166a23e9834403c765ecb` |
| focused_existing_guards | 0 | 3.274 | `daa270bb3120e9a5c7ee503a2676e921907050905ade5716a72f5ca0bd2bb5e8` |
| full_pytest | 0 | 44.504 | `abce3cfba5069f6f0b382a4f322bc84b6478afb4f4c6e2003c669f73678aa9ca` |
| ruff | 0 | 0.057 | `5b196eb3a6acb50d3fa398d04ca284985cc1ffec870e940264b00780bfd2c971` |
| compileall | 0 | 0.239 | `10422edbc8bc9d0728a417632466dff12e89a63d7c0cb2263f5871b98b512d56` |
| offline_build | 0 | 1.140 | `afd2e414d8cfd68ccd81b6bbdc8219438cd5a0a8f7899008dd1b1bb03103052f` |
| whitespace_unstaged | 0 | 0.015 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| whitespace_staged | 0 | 0.011 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| whitespace_base | 0 | 0.011 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## Read scope

Reads covered the repair card, Astra AUDIT review
`coord/pr221_astra_review.txt`, Grok review `coord/pr221_grok_review.md`,
owner record `coord/step2_semantic_acceptance.md`, `AGENTS.md`, current
handoff, controller, live coordinator files, the design, the historical
Step 2 attempt report, engineering-log tail, CI workflow, `pyproject.toml`,
`scripts/repo_map.py`, and targeted existing dividend/event guards. Private
market data, host `~/.grok` configuration, protected C, other writer roots,
and Herdr were untouched. No external actions were taken.

## Remaining gates and limitations

Formal CRITICAL reviews and binding acceptance remain pending on the new
exact head. Step 3 implementation remains separately authorized. This
attempt is a design-and-evidence repair; runtime comparison and schema
work stay at the later Step 3 gate. ADV-3 Step 3 runner mapping remains
an owner-semantic question. Linux CI is unverified. Local checker scripts
live under gitignored `build/` and are producer evidence; the design note
states the witness and formulas for independent recomputation.

Intended committed files: this report, the repaired design, and
`docs/engineering_log.md`. `docs/repo_map.md` was regenerated and matched
the baseline bytes, so it is omitted from the commit set. Writer
responsibility is released after the local commit recorded in the final
handoff.

Every new documentation passage is English. Immutable historical language
exceptions remain preserved.
