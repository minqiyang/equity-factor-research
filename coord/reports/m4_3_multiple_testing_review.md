# Milestone 4.3 Independent Code Review

**Verdict: PASS (MATERIAL: 0).** This review found zero material defects and
zero advisory findings in candidate
`e542c0646d8799cd12c43b0051ce20983d031af7` on
`feat/m4-3-multiple-testing-dsr`. The implementation satisfies the reviewed
observed-family diagnostic contract. Statistical interpretation remains
conditional on the assumptions and evidence limits stated below.

**Review identity and isolation.** Review completed on 2026-09-21 Pacific
time; evidence manifest timestamp is `2026-09-22T05:45:31.562257+00:00`.
Reviewer session: `01a0c7a1-7921-7fd1-b6de-6c5ffccdfd5f`, fresh Codex terminal
review session, role `/root`. The supplied review card specifies the
owner-authorized single GPT-6 Astra / xhigh / Fast seat. This report records
the work performed by this session; model and service-tier dispatch attestation
remains in the coordinator's launch record.

The supplied checkout contained an untracked review card. It was preserved.
All candidate verification used the separately created, clean detached root
`/private/tmp/efr-m4-3-independent-e542c06`, at the exact candidate commit.
The baseline root was `/private/tmp/efr-m4-3-independent-baseline`, at
`8fb9050fbc6cacdb3ae6ef5f71a20615d450b5af`. Both roots are separate from the
producer worktree. Candidate HEAD and the local candidate branch still matched
the requested digest after verification; candidate Git status was clean and
`git diff --exit-code HEAD -- .` passed. The sole repository deliverable from
this review is this report in the originally requested checkout.

**Scope and governing inputs.** Read `AGENTS.md`,
`coord/card_m4_3_multiple_testing_review.md`, the accepted implementation card,
`coord/reports/m4_3_multiple_testing_impl.md`, the north star, current roadmap,
repository map, CI workflow, and both live coordinator-standard files. The
current review card supplies the single-seat scope; the implementation records
retain their earlier two-reviewer handoff. Reviewed the complete changes from
the stated baseline, with detailed inspection of:

- `src/features/multiple_testing.py` and the reused
  `src/features/diagnostics.py:newey_west_mean_tstat`.
- `research/multiple_testing_diagnostics.py`.
- `research/multifactor_diagnostic_mvp.py` and
  `research/real_data_multifactor_diagnostic.py`, including shared book execution,
  semantic trial inventory, report rendering, and experiment-log integrations.
- Added and changed tests, the generated synthetic report, roadmap claims,
  engineering record, and supplied source-hash and ablation evidence.

All executions used generated synthetic data or committed synthetic fixtures.
The real-data runner was exercised through synthetic Parquet tests. Candidate
implementation, baseline implementation, private market data, and external
publication state remained outside this review's write scope.

**Mathematical verification.** The following checks passed through source
inspection, repository tests, and separately authored reviewer tests.

| Surface | Verification and conclusion |
| --- | --- |
| Bonferroni, lines 60-61 | Computes `min(1, m*p)` with the full declared family size. |
| Holm, lines 62-65 | Stable sorting, multipliers `m, m-1, ...`, cumulative maximum, and inverse placement implement the step-down adjusted p-values. Ties and original ordering are preserved. |
| BH, line 67 | SciPy BH on the supplied `k` slots followed by `m/k` scaling and clipping gives the required padded-family correction. The published 15-hypothesis example yields four BH discoveries and three Bonferroni discoveries at 5%. |
| BY, lines 68-70 | Multiplies by `digamma(m+1) + EulerGamma`. Independent explicit harmonic sums agreed for `m=1,2,3,148,1000,10000`; the repository also exercises the maximum accepted declared count. |
| Missing and additional slots, lines 51-71 | Supplied NaNs become internal `p=1`, contribute to the denominator, and return as NaN. Extra declared hypotheses also contribute `p=1` mathematically. Twenty seeded families per method, each with three declared-size choices, agreed with a scalar oracle that explicitly pads every additional slot. |
| HAC, lines 89 and 113; diagnostics.py lines 224-242 | Uses `L=floor(4*(T/100)^(2/9))`, centered returns, autocovariance denominator `T`, Bartlett weights `1-lag/(L+1)`, and standard error `sqrt(long_run_variance/T)`. Independent quadratic-form covariance oracles passed for six sample sizes and negative, zero, and positive autocorrelation. Two-sided p-values correctly use an asymptotic normal reference. |
| IID, lines 106-122 | Uses sample standard deviation with `ddof=1`, `t=mean/s*sqrt(T)`, and two-sided Student-t probability with `T-1` degrees of freedom. Independent scalar-moment and `stdtr` oracles passed. Annualized Sharpe uses `sqrt(A)` and zero risk-free rate. |
| Haircut, lines 145-158 | Inverts `q/2` with Student-t `T-1` degrees of freedom, multiplies by `sqrt(A/T)`, caps magnitude at observed Sharpe, and restores its sign. Probability roundtrips passed for both signs, four sample sizes, and three annualizations. Increasing adjusted p-values weakly reduced the adjusted magnitude. |

The BH padding equivalence also follows directly from the sorted formulas.
Each additional sorted `p=1` slot has `m/j >= 1`; its contribution is absorbed
by the final upper bound of one. Thus the supplied slots can use the original
BH factors scaled by `m/k`. BY applies the harmonic factor for the complete
declared family. Holm's additional slots occur after every supplied p-value
below one and leave the relevant prefix maxima unchanged.

The published benchmark and dependency assumptions were checked against
[SciPy's FDR documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.false_discovery_control.html).
The harmonic identity is documented in
[NIST DLMF 5.4.14](https://dlmf.nist.gov/5.4.E14).
The survival-function inversion was checked against
[SciPy's Student-t interface](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html).
The default Bartlett kernel and automatic lag rule agree with the documented
[HAC convention](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html).

**Boundaries and refusal behavior.** Empty and single-slot families, all-missing
families, zero and unit probabilities, ties, permutations, tiny probabilities,
nullable numerics, declared-family overrides, invalid types/ranges, and
duplicate/named axes pass. Reviewer cases additionally cover mixed-scalar
MultiIndex labels and empty CategoricalIndex metadata. Adjustments preserve the
Series name and index; finite outputs satisfy `p <= q <= 1` and sorted weak
monotonicity across the exercised families. The API accepts one-dimensional
Series; rectangular empty-axis shapes belong outside this interface.

Return inference withholds both p-values for `T<3`, any nonfinite observation,
constant values, underflowed or overflowed variance, and nonfinite statistics.
Nonfinite-input status takes precedence when a short sample also contains an
invalid value. Complete samples retain their observation count and order.
The new wrapper validates finiteness before calling the existing HAC helper,
so its finite-series cleanup preserves every observation in this call path.
The constant `0.1` three-row regression remains covered. Undefined results
serialize as JSON null through `allow_nan=False`.

For nonzero observed Sharpe, `q=1` gives zero adjusted magnitude and a full
haircut. Zero observed Sharpe gives zero magnitude and zero haircut, matching
the accepted implementation card's explicit zero-effect convention. `q=0`
preserves magnitude at the underflowed raw-probability boundary; a materially
smaller adjusted p-value otherwise raises. The raw-versus-adjusted comparison
allows the implemented `1e-12` relative numerical tolerance. The disclosed
smallest-normal-float floor provides conservative raw-tail resolution.

**Causality and pipeline integration.** `_run_recorded_trial` computes the new
statistics after the backtester returns, from `backtest.returns.iloc[1:]`.
Both directions therefore exclude the accounting anchor exactly once and
retain net book returns with existing costs. Reviewer tests verify this exact
sample, input immutability, returned book identity, and started/completed event
ordering for long-only and long-short books. The summary consumes finalized
attempt records after book execution. Every use of the new fields is in
diagnostic results, report rendering, or experiment logging.

The complete diagnostics lane includes
`test_m01_integrated_future_labels_and_prices_prefix_invariance` and the
parameterized frozen-smoothing/execution future-price invariance cases.
These passed on the candidate. Full-sample diagnostic values summarize the
completed sample; portfolio decisions retain their existing causal inputs.
The statistical helper expects the caller-supplied chronological sequence.
Calendar and timestamp eligibility remain enforced at the runner/backtest
boundaries reviewed and tested here.

An independent capture wrapper recorded every executed book, including the
weighting-comparison executions omitted from the producer's 124-book capture.
Baseline and candidate captures are byte-identical across **156 book
executions, 2,418 dataclass fields, 148 distinct semantic trials, 62 factor DSR
values, PBO, family dispersion, and weighting-comparison summaries**. This
covers returns, holdings, execution/accounting fields, turnover, costs, and
metrics. The common capture SHA-256 is:

```text
c2e975d91ebe2c27cfa35374a9bacfabb7039698d1f51086fe52c6a2793750bd
```

**Family retention and reporting.** Grouping retains every semantic trial ID.
Identical repetitions share one slot. Failed/incomplete records, unavailable
tests, degenerate samples, and conflicting repetitions receive undefined
inference while retaining their slots. Four corrections are computed separately
for HAC and IID; IID haircuts use their corresponding IID adjusted p-values.
Bonferroni hurdles use each trial's sample count and the complete family size.
Two-sided negative discoveries retain an unfavorable sign, with favorable
discoveries separately counted through positive mean return.

The fresh default synthetic run reproduced **156 attempts, 148 distinct and
valid trials, and zero primary HAC-BY rejections**. The committed Markdown
diagnostic section exactly equals rendering this fresh summary. Both runner
integration tests verify report presence, complete experiment-log summary
equality, return-test attachment to completed attempts, both directions, and
strict JSON serialization. The implementation's completion claims match this
diagnostic scope and explicitly retain historical-search limitations.

**Verification record.** Environment: macOS arm64; Python 3.11.15; NumPy 2.4.6;
pandas 3.0.6; SciPy 1.17.1; pytest 9.1.1. The existing producer virtual
environment supplied dependencies. Explicit `PYTHONPATH=.:src` and recorded
module paths confirm that tests imported source from the independent candidate
root. Six CI native-thread variables were set to one. Each repository lane used
two xdist workers with work stealing and worker restart disabled.

| Check | Independently observed result |
| --- | --- |
| Core pytest lane | 3,871 passed, 2 platform skips; 28.63 seconds |
| Diagnostics pytest lane | 125 passed; 92.94 seconds |
| Reviewer-authored pytest verification | 149 passed; 0.99 seconds in final run |
| Combined final pytest outcomes | 4,145 passed, 2 skipped, zero failures |
| Ruff | `ruff check .` passed |
| Compilation | `compileall -q src tests research lean` passed |
| Whitespace and tracked-source preservation | Passed |
| Distribution build | Isolated source distribution and wheel build passed; packaged statistical module equals reviewed source bytes |
| Default synthetic baseline/candidate comparison | Exact equality; 53.67 / 53.65 seconds under concurrent execution |
| Fresh synthetic report comparison | Exact rendered-section equality |
| Producer evidence binding | All eight source hashes in the supplied final QA manifest match the reviewed candidate |

The two skips arise from this platform's `longdouble` having float64 precision.
Existing constant-input correlation warnings remain visible in the saved logs.
An initial optional build with `--no-isolation` failed because the dependency
environment lacks setuptools. The normal isolated build installed its declared
build requirements and passed. Both logs are retained. Concurrent capture
timings describe these executions and provide no controlled speedup estimate.

**Reproduction and evidence.** Reviewer-owned tests, capture code, logs, JUnit
XML, source hashes, runtime metadata, full synthetic summary, distribution
artifacts, and both captures are retained at
`/private/tmp/efr-m4-3-review-evidence`. `manifest.json` binds the candidate,
baseline, imported modules, source hashes, and evidence-file hashes.

```sh
cd /private/tmp/efr-m4-3-independent-e542c06
REVIEW_PYTHON=/private/tmp/efr-m4-3-multiple-testing-dsr/.venv/bin/python
export PYTHONPATH=.:src
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export BLIS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
"$REVIEW_PYTHON" -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 \
  tests --ignore=tests/test_multifactor_diagnostic_mvp.py \
  --ignore=tests/test_m3_10_hardening.py
"$REVIEW_PYTHON" -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 \
  tests/test_multifactor_diagnostic_mvp.py tests/test_m3_10_hardening.py
"$REVIEW_PYTHON" -m pytest -q \
  /private/tmp/efr-m4-3-review-evidence/test_independent_m4_3.py
```

`capture_independent.py` accepts an output pickle path and runs from either
frozen root with that root on `PYTHONPATH`. The final three reviewer tests use
the retained baseline/candidate captures, fresh summary, and built wheel.
The manifest and logs preserve the exact results of this review execution.

**Ablation assessment and limitations.** The two added modules contain narrow
functions using existing NumPy, pandas, and SciPy dependencies. The integration
adds diagnostic fields at existing boundaries. Inspection found zero speculative
registries, duplicated DSR implementations, or unnecessary wrapper layers.
The supplied isolated ablation evidence records retained constant-series and
conflicting-attempt guards and removal of a redundant final maximum traversal.
This review independently revalidated those guards and the resulting correction
bounds, labeled-axis preservation, and empty inputs. Candidate source remained
unchanged throughout this review.

The evidence establishes correctness of the implemented diagnostic formulas and
their tested integration. HAC inference uses an asymptotic approximation with
finite-sample, stationarity, and lag-selection limitations. FDR/FWER guarantees
require valid marginal p-values; adaptive strategy construction and a run-local
family leave historical-search completeness open. IID haircuts retain their
Gaussian independence assumptions. Empirical-population Harvey-Liu calibration,
private-data inference, new remote CI execution, and profitability validation
remain outside this review's evidence. The author-hosted Harvey-Liu MATLAB URL
was unavailable to the browser during review; the implemented IID mapping was
verified directly against the accepted mathematical contract.

**Disposition.** Open MATERIAL findings: **0**. Open ADVISORY findings: **0**.
This exact candidate receives **PASS (MATERIAL: 0)** for the requested code
review. The next gate is coordinator reconciliation of this report and its
evidence with the current review card and exact candidate digest.
