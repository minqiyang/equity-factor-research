# M4.3 Multiple-Testing Implementation Report

Date: 2026-09-21. Author/executor: GPT-6 Astra, extra-high reasoning.
Branch: `feat/m4-3-multiple-testing-dsr`.
Baseline: `8fb9050fbc6cacdb3ae6ef5f71a20615d450b5af`.
Working root: `/private/tmp/efr-m4-3-multiple-testing-dsr`.
Accepted card: `coord/card_m4_3_multiple_testing_dsr.md`, originally frozen at
`c8f37732b5d1ac48cb7aba9f4f591ead1b28b1fc`.
The owner/coordinator explicitly accepted that card with MATERIAL: 0 and
authorized immediate implementation. Two fresh independent GPT-6 Astra
implementation reviews remain the next acceptance gate. The 24-hour GPT-only
mandate supplies the same-model diversity exception.

## Decision and completed scope

Direction 1 provides the strongest immediate research-validity improvement for
the existing diagnostic thread. Its mathematical algorithms and complete
reporting path admit deterministic synthetic verification. The accepted card
compares all four directions and records the evidence dependencies of dynamic
PIT membership, impact/capacity calibration, and style-risk attribution.

Implemented:

- `src/features/multiple_testing.py`: Bonferroni, Holm, BH, and BY p-value
  adjustments; complete-sample IID and HAC mean-return diagnostics; signed
  correction-implied IID Sharpe haircuts. Existing NumPy, pandas, and SciPy
  provide the numerical operations. Dependency declarations remain unchanged.
- `research/multiple_testing_diagnostics.py`: conservative semantic-trial
  deduplication, retained unavailable slots, per-method corrections and IID
  haircuts, Bonferroni t/Sharpe hurdles, and a shared full-family report section.
- Both multifactor runners attach test statistics to completed attempt events
  and include the summary in returned results, Markdown reports, and experiment
  log metrics. The first accounting anchor is excluded exactly once.
- `tests/test_multiple_testing.py` and
  `tests/test_multiple_testing_diagnostics.py`: 81 new deterministic cases.
  Existing synthetic and synthetic-Parquet integration tests also check the new
  report/log fields, family membership, attempt events, and JSON serialization.
- `reports/m4_3_multiple_testing_synthetic.md`: a new complete synthetic report
  with 148 distinct configurations from 156 attempts, all retained. It records
  zero primary HAC-BY rejections at 5% for the default synthetic fixture.
- The roadmap's statistical backlog row, engineering log, and generated
  repository map record the delivered diagnostic layer and its remaining limits.

The existing DSR implementation, its across-trial dispersion calculation, PBO,
factor construction, portfolio decisions, accounting, timing, and cost formulas
retain their baseline code and behavior. Historical report artifacts remain
preserved. All execution in this task used committed synthetic data or generated
synthetic Parquet fixtures.

## Statistical interpretation

The primary family includes both long-only and long-short books and every
evaluated weighting and penalty configuration. Repeated identical semantic
trials share one slot. Failed, incomplete, unavailable, zero-variance, and
conflicting outcomes retain denominator slots with undefined displayed inference.
An explicit larger family count reserves additional unavailable hypotheses at
p=1. The default fixture contains 148 valid trial summaries.

The null is zero mean net book return at a zero risk-free rate. Primary HAC
p-values use the existing Newey-West Bartlett statistic, automatic lag selection,
and an asymptotic normal reference. BY at 5% supplies the primary correlated-family
diagnostic. BH remains conditional on independence or PRDS; Bonferroni and Holm
target family-wise error. Two-sided unfavorable discoveries retain their signs.

The IID leg uses Student-t mean tests and inverts adjusted p-values to signed
annualized Sharpe magnitudes. These values are explicitly labeled sensitivities.
Harvey and Liu's full empirical-population simulation uses additional calibrated
mixture and dependence assumptions. That simulator remains deferred. A fixed
universal t hurdle and an invented correlation-to-effective-count transform
would overstate what these inputs identify. Each actual Bonferroni hurdle depends
on family size and sample count.

Valid marginal p-values remain a prerequisite for formal error-control claims.
Finite-sample HAC calibration, stationarity, lag truncation, adaptive strategy
construction, and historical-search completeness remain limitations. Raw p-values
use a disclosed smallest-normal-float resolution floor. The empirical evidence
ceiling remains DIAGNOSTIC_ONLY.

## Verification and preserved baseline

Environment: macOS arm64, Python 3.11.15; NumPy 2.4.6, pandas 3.0.6,
SciPy 1.17.1, pytest 9.1.1, pytest-xdist 3.8.0. The six CI native-thread
environment variables were set to 1. Each lane used two xdist workers,
`--dist worksteal --max-worker-restart=0`.

| Check | Completed result |
| --- | --- |
| Baseline complete suite | 3,915 passed, 2 inherited platform skips, 138.73 seconds |
| Initial focused statistical/family/Parquet integration run | 97 passed, 2.65 seconds |
| Final core lane | 3,871 passed, 2 inherited platform skips, 25.62 seconds |
| Initial diagnostics lane | 125 passed, 91.82 seconds |
| Final diagnostics lane | 125 passed, 92.39 seconds |
| Ruff, source/tests/research/LEAN compilation, whitespace check | Passed |
| Source distribution and wheel build | Passed; packaged statistical module matches final source bytes |
| Repository-map regeneration | Completed; project-structure checks are included in core QA |
| Final observed-family summary versus captured pre-ablation summary | Exact dictionary equality; 0.0241 seconds for 148 distinct trials |

The two inherited skips concern platforms where longdouble has float64
precision. Existing constant-input correlation warnings remain visible.
The final lane collection contains 3,998 cases: 3,996 passes and two platform
skips across both final lanes. Hosted CI remains a subsequent publication check.

The default 756-date, 50-asset synthetic run was captured before implementation
and after integration. The two JSON captures compare byte for byte across
124 books and 1,674 captured book fields, including pandas return, holding,
turnover, cost and other public series/frame values and metric dictionaries.
The same capture retains every factor's DSR, PBO summary, weighting comparisons,
and family dispersion. Its common SHA-256 is
`6128f06b0328300dbff4401865478b558d85a6a5f9fd63cceb695633e70dda54`.
Baseline and candidate full-run wall times were 55.58 and 54.08 seconds under
concurrent local QA; these timings establish operational cost observations.
They supply no controlled speedup estimate.

Runtime/subsystem coverage:

| Surface | Evidence |
| --- | --- |
| Four correction procedures | Published BH numerical example; hand oracles; ties, permutations, empty/single families, duplicate/named labels, missing slots and declared-family scaling |
| Return inference and haircut mapping | Independent Student-t and Bartlett covariance oracles; signed effects, annualization, zero variance, short and nonfinite samples, extreme tails and overflow refusal |
| Correlated trials | Synthetic common-factor returns; SciPy BH/BY oracle comparison and conditional dependence disclosures |
| Trial retention | Failed/incomplete events, semantic repetitions, conflicting outcomes, unavailable family slots, strict JSON serialization |
| Both diagnostic runners | Full synthetic pipeline plus generated synthetic-Parquet real-runner fixtures; shared Markdown and experiment-log assertions |
| Portfolio and causal outputs | Preserved baseline captures plus all existing accounting, timing, causality, DSR and PBO regression cases |
| Packaging and repository | Ruff, compile, source/wheel build, exact packaged module comparison and generated map |
| Private empirical data and hosted runtime | Outside local execution evidence; private artifacts preserved and hosted CI remains pending |

## Ablation experiments

Design ablation removed the speculative correlation-derived effective-count
layer, empirical-population simulator, and duplicate DSR estimator from the
proposed scope. A 24-case numerical prototype confirmed implicit p=1 family
extensions against explicitly padded SciPy BH/BY calculations.

Implementation ablation preserved original module bytes and ran isolated
modified copies outside the producer tree. Each experiment changed one element.

| Removal | Observed result | Disposition |
| --- | --- | --- |
| Constant-series guard | 2 failures in the initial 73-case experiment; a follow-up three-observation constant 0.1 series produced IID p=9.63e-33 after guard removal, demonstrating spurious inference from floating-point variance | Retained guard |
| Conflicting-attempt guard | 2 failures, 5 passes; successful/failed siblings and conflicting repeated outcomes gained inference | Retained guard |
| Final elementwise maximum of adjusted and raw p-values | 73 passes; monotonic correction formulas already supply the bound | Removed the redundant array traversal and its comment |

After the retained simplification, 20 additional randomized procedure/size
checks spanning raw p-values down to 1e-300 preserved q>=p and q<=1. The complete
default family summary remains exactly equal to its captured pre-ablation value.
The final full CI lanes revalidate the resulting implementation. These experiments
cover the added diagnostic layer and its touched integrations; broader economic
calibration and historical-search reconstruction remain open research work.

## Evidence locations and reproduction

Local evidence directory: `/private/tmp/efr-m4-3-evidence`.
It retains baseline/candidate captures, the capture script, final JUnit XML,
build log/distributions, the full machine-readable synthetic summary, design
oracle script, isolated ablation source copies and results, and final source
hash manifest. An initial standalone boundary-check invocation omitted the
research-root PYTHONPATH; rerunning with `PYTHONPATH=.:src` completed successfully.

Reproduce the generated report section from the repository root:

```python
from research.multifactor_diagnostic_mvp import run_multifactor_diagnostic_mvp
from research.multiple_testing_diagnostics import render_multiple_testing

result = run_multifactor_diagnostic_mvp(write_outputs=False)
print(render_multiple_testing(result["multiple_testing"]))
```

The committed report adds a static provenance preface to that exact generated
section. Normal runner output writes the complete machine-readable summary into
experiment-log metrics. A review candidate is identified by its delivered Git
commit; saved QA source hashes bind component evidence to the reviewed code.

This report records the implemented scope, mathematical limits, deterministic
QA, preserved baseline, and isolated ablation evidence for independent review.
