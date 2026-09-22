# M4.6 Independent Remediation Re-Review

Verdict: PASS (MATERIAL: 0)

M46-R1 is resolved on candidate `be177ce57036e48bccc5425950995f044bddf794`.
Independent reruns reproduce every requested QA lane and evidence check. This
re-review identifies zero new material findings.

## Identity and scope

- Date: 2026-09-22.
- Reviewer: user-assigned single independent Codex session, task `/root`.
- Candidate: `be177ce57036e48bccc5425950995f044bddf794`.
- Base: `b60e109c6959e059dea6c19c3573dd5e861a2ac2`.
- Remediation code commit: `cfec56d016be17937a2496280e2a53d6722a0c0e`.
- Directive: `coord/card_m4_6_risk_attribution_rereview.md` in the supplied root.
- Clean candidate verification root: `/private/tmp/efr-m46-independent-be177ce`.
- Clean base verification root: `/private/tmp/efr-m46-rereview-base-b60e109`.
- Retained evidence: `/private/tmp/efr-m46-independent-evidence`.
- Authoritative report: `/private/tmp/efr-m4-6-rereview-clean-be177ce/coord/reports/m4_6_risk_attribution_review.md`.

The supplied root had untracked `.venv` and directive-card entries at startup.
Both remain preserved. Separate detached worktrees established clean exact-commit
verification roots; empty `git status --porcelain` was verified before and after
the experiments. Candidate source, tests, and committed evidence remain unchanged.
This report is the sole added deliverable in the supplied root.

The previous review report was absent from the supplied root. Its existing copy
at `/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/coord/reports/m4_6_risk_attribution_review.md`
was read to verify the original M46-R1 claim and fixture. That review identifies
candidate `a79d4bd69ff82c354fc5f993bf8758ab6e826c83` and one open P2 material finding.
The implementation report's remediation section and changes since that candidate
were inspected alongside the current source and tests.

The live coordinator and routing files under
`/Users/rhapsoul/Documents/Codex/Standards/herdr_pi_coordinator_v7_two_file/`
were read. The user's explicit single-reviewer assignment governs this task.
The directive requests GPT-6 Astra High Fast; actual model, effort, and service-tier
dispatch attestation remains coordinator-owned metadata outside these local
repository checks.

## M46-R1 — P2 MATERIAL — RESOLVED

The prior finding identified a valid singular-covariance case rejected by an
exact-nonnegative aggregate guard despite the covariance guard's `-1e-14` tolerance.
The repair aligns the aggregate boundary with the requested fixed absolute policy.

| Requirement | Verified evidence |
| --- | --- |
| Aligned tolerance | `src/backtest/risk_attribution.py:196` accepts covariance eigenvalues down to `-1e-14`; line 206 requires both `variance >= -1e-14` and `factor_variance >= -1e-14`. |
| Bounded clamping | Lines 208–209 apply `max(factor_variance, 0.0)` and `max(variance, 0.0)` after validation. |
| Material-negative refusal | Lines 205–207 preserve `RiskAttributionError("risk_numerical", ...)`. `test_material_negative_factor_variance_refused` at `tests/test_risk_attribution.py:597` passes for zero and positive specific risk; levered factor variance is `-4e-14`. |
| Non-finite refusal | The same guard checks finite factor terms, specific terms, and total variance. `test_public_guard_counterexamples[risk_numerical]` passes with overflow-inducing finite input weights. |
| Original regression | `test_valid_rank_one_covariance_with_hedged_factor_exposure` at `tests/test_risk_attribution.py:527` passes with active variance approximately `6.25e-7`, zero clamped factor variance, and finite tracking error approximately `0.000790569415042095`. |
| Signed contributions | The regression checks exact preservation of the computed signed Euler terms and reconciliation within `1e-14`. |
| Boundary coverage | Six cases at `tests/test_risk_attribution.py:572` pass for `-1e-14`, `-1e-20`, and zero, each with zero and positive specific variance. |

The dedicated regression run records ranks `[6, 6, 6]`, minimum covariance
eigenvalue `-1.4247650757080005e-51`, raw summed factor variance
`-1.6940658945085947e-22`, and specific variance `6.250000000000002e-7`.
Its active-variance assertion uses `rtol=0, atol=1e-12`. All ten selected
regression, boundary, material-negative, and overflow cases pass.

The implemented policy retains raw signed contributions and independently clamps
the two aggregate scalars. Consequently, scalar-sum reconciliation includes the
documented correction of at most `1e-14` plus floating-point addition rounding.
The fixed tolerance follows this re-review directive. Ordinary positive-variance
arithmetic and the existing return-reconstruction tolerance remain intact.

## Independently completed QA

| Gate | Measured result |
| --- | --- |
| Core lane | 4,215 passed, 2 skipped, 34.54 seconds. |
| Diagnostics lane | 125 passed, 102.72 seconds. |
| Disjoint union | Fresh JUnit parsing verifies 4,342 unique cases, zero lane overlap, 4,340 passed and 2 skipped. |
| Complete risk suite | 79 passed in the intact isolated ablation baseline. |
| Negative ablations | All 55 injected removals produce expected pytest failures, including tolerance removal and each scalar-clamp removal. |
| Positive ablation controls | Intact baseline and standardized-volatility ddof equivalence pass; 57 total isolated cases. |
| Source and log integrity | Production source hashes remain unchanged. All six producer validation source hashes and all 57 archived remediation log hashes match. Fresh ablation logs match their manifest hashes. |
| Ruff | `python -m ruff check .` passes. |
| Compileall | `python -m compileall -q src tests research lean` passes. |
| Diff hygiene | `git diff --check b60e109 HEAD` passes. |
| Clean roots | Candidate and base verification roots remain clean after all runs. |

The two skips are the inherited platform condition at
`tests/test_backtest_timing_contract.py:1221`: `longdouble` has no precision beyond
`float64`. Existing constant-input correlation warnings remain visible in the logs.
The selected regression run and ablation reruns provide overlapping coverage and
are excluded from the 4,340-test disjoint total.

The ablation script verifies imports from each isolated package and preserves
the original source hashes. Every negative case contains an actual pytest failure.
Its three remediation variants independently establish the need for the tolerance
and both clamps. The supported simplification outcome retains these numerical
controls. This is revalidation of the milestone ablation evidence.

## Baseline and demo reproduction

The committed `capture_baseline.py` was run separately against the clean candidate
and base, with imports resolving through each root's `src`. Both schemas exhibit
100% equality of decompressed JSON bytes across fresh base, fresh candidate,
committed baseline, original committed replay, and remediation replay.

| Schema | Books | Existing fields | Uncompressed SHA-256 |
| --- | ---: | ---: | --- |
| Legacy | 124 | 2,294 | `5a885b96e7379a83658047d4720d701f504f92838ffae10a76fa267580b61ed4` |
| All M4.5 fields | 124 | 3,038 | `878cfc0315ac0fa64ed120205f1c73eb1572c71822c1ea8111c229ab4e17c7d1` |

Each schema covers 62 factor scenarios and 124 books. The all-fields serializer
includes impact fields, raw-value hashes, dtypes, ordered indices, and axis metadata.
The new `risk_attribution` sidecar lies outside the pre-existing-field comparison.
The passing integration tests additionally compare enabled and disabled sidecars
for both engines and fixed-cost/impact execution.

`research.risk_attribution_demo.run_risk_attribution_demo` was executed with a
temporary report path. Generated Markdown matches committed bytes exactly.
Eight cases succeed, all with negative compounded net return; two expected refusals
retain `rank_deficient` and `exposure_unavailable`. Maximum return-reconstruction
error is `3.469446951953614e-18`.

The fresh attempt log contains 20 paired start/final records covering all ten
cases. Both historical runs retain 40 records. Every historical measurement
present in those records agrees with the fresh run; the earlier historical schema
has fewer fields. Passing suite coverage also verifies unexpected-failure logging.

## Reproduction and retained evidence

Environment: CPython 3.12.13, NumPy 2.5.3, pandas 3.0.6, SciPy 1.18.1, using
`/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/.venv/bin/python`.
`PYTHONPATH=src:.` resolves candidate/base imports. Native numeric thread limits
are one for OMP, OpenBLAS, MKL, BLIS, VECLIB, and NumExpr. Both QA lanes use two
worksteal workers with `--max-worker-restart=0`.

The evidence directory contains `run.py`, exact command/exit/timing JSON records,
`core.xml`, `diagnostics.xml`, lane logs, `regression.log`, `ablations/results.json`
and per-case logs, four fresh baseline captures, the demo report and attempt log,
`verify_demo.py`, and `summarize.py`. `verification_summary.json` records the
independently verified counts, hashes, equality checks, and clean-root checks.

Representative commands from the clean candidate root:

```text
python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 tests --ignore=tests/test_multifactor_diagnostic_mvp.py --ignore=tests/test_m3_10_hardening.py --junitxml=<evidence>/core.xml
python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 tests/test_multifactor_diagnostic_mvp.py tests/test_m3_10_hardening.py --junitxml=<evidence>/diagnostics.xml
python -m pytest -q -s tests/test_risk_attribution.py::test_valid_rank_one_covariance_with_hedged_factor_exposure
python coord/reports/m4_6_evidence/ablate.py <fresh-ablation-directory>
python coord/reports/m4_6_evidence/capture_baseline.py <capture>.json.gz
python coord/reports/m4_6_evidence/capture_baseline.py <legacy-capture>.json.gz --legacy
python -m ruff check .
python -m compileall -q src tests research lean
```

The base captures use the same candidate capture script by absolute path while
running from the base root. `run.py` records those exact commands and directories.

## Scope and next gate

Coverage comprises the requested numerical remediation, source inspection of its
integration, and fresh synthetic QA, baseline, demo, and ablation evidence.
Caller-declared identities and availability, empirical covariance calibration,
static-universe eligibility, geometric linking, and terminal/changing-universe
attribution retain the implementation report's stated limitations. The diagnostic
evidence ceiling remains `DIAGNOSTIC_ONLY`.

The next gate is coordinator verification of this exact-head report, dispatch
attestation, and hosted CI under the applicable delivery authorization. This
report records M46-R1 as resolved, every requested local check as complete, and
zero open material findings for the reviewed candidate.
