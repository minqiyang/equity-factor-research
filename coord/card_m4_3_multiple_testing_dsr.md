# M4.3: Auditable Multiple-Testing Diagnostics

Date: 2026-09-21. Author/executor: GPT-6 Astra, extra-high reasoning.
Baseline: `8fb9050fbc6cacdb3ae6ef5f71a20615d450b5af`.
Branch: `feat/m4-3-multiple-testing-dsr`.
Working root: `/private/tmp/efr-m4-3-multiple-testing-dsr`.
Implementation report: `coord/reports/m4_3_multiple_testing_impl.md`.
Lane: CRITICAL, because inferential claims affect research validity.
Structural: false; this additive diagnostic feature preserves existing accounting,
selection, timing, and external protocol contracts.
Review: two fresh, independent, mutually blind GPT-6 Astra high/xhigh sessions,
with clean roots at the frozen candidate. The owner's 24-hour GPT-only mandate
authorizes the recorded model-diversity degradation and replaces Grok seats.

## Decision and comparison

Execute Direction 1 now. Multiplicity belongs directly in the existing
data-to-factor-to-portfolio-to-report thread. Its correction algorithms admit
published numerical oracles, and synthetic fixtures exercise the complete path.

| Direction | Validity and roadmap value | Dependencies and complexity | Decision |
| --- | --- | --- | --- |
| 1: multiple testing | Exposes selection risk across the books already evaluated; completes an explicit statistical backlog item | Small deterministic statistical module and shared reporting; existing SciPy supplies FDR procedures | Execute M4.3 |
| 2: dynamic PIT universe and delisting | Required for stronger universe and terminal-accounting claims | Accepted identity, membership, and terminal-event evidence plus portfolio accounting changes; existing identity/disappearance refusal tests remain mandatory | Follow when evidence supports a bounded dynamic-universe slice |
| 3: impact and capacity | Improves net-return realism at a declared trade size | Requires a calibrated impact coefficient, volatility and compatible ADV bases, and participation assumptions; portfolio.py already supports precomputed volume impact | Follow a concrete capacity scenario and calibration contract |
| 4: style-risk attribution | Explains systematic versus residual exposures | Requires PIT style inputs and a defined exposure/return model; current sector and beta diagnostics provide a smaller existing slice | Follow the data and style specification |

Existing `features.diagnostics.deflated_sharpe_ratio` already computes DSR with
across-trial Sharpe dispersion. Preserve that implementation and its tests.
The current synthetic runner evaluates 156 books representing 148 distinct
configurations: 62 factor/composite rows, both portfolio directions, and weighting
and penalty variants. Derive counts from the retained inventory for every run.
Real-data subsets and ML composites can produce other counts.

## Statistical scope and methodological correction

The family comprises distinct semantic trial IDs in the current run, including
all evaluated factor, direction, weighting, and penalty combinations. Every
attempt remains in the append-only event stream. Failed, incomplete, degenerate,
or conflicting repetitions retain a family slot and receive undefined inference.
Exact repetitions share one hypothesis. Repeated records with different outcomes
withhold inference for that ID, preventing outcome selection by last-write order.
An explicit `n_trials` override reserves additional unavailable hypotheses at
p=1. It supplies a disclosed count sensitivity. Historical search completeness
remains unestablished.

The tested quantity is mean daily net book return against zero, with zero
risk-free rate. It measures absolute-return evidence. Benchmark-relative alpha
and future profitability remain separate questions. Two-sided tests retain
negative discoveries; a separate positive-mean flag identifies favorable signs.

Primary diagnostic inference uses a Newey-West mean statistic and asymptotic
normal p-values. BY at 5% accommodates arbitrary cross-trial dependence when
the marginal p-values are valid. Finite-sample validity still depends on the
time-series model, lag truncation, and adaptive research history. BH is a
conditional sensitivity for independent or PRDS p-values. Bonferroni and Holm
provide FWER adjustments under valid marginal p-values.

Sharpe haircuts use the explicit IID Student-t sensitivity below. Harvey and
Liu's published implementation additionally calibrates a simulated population
of tests using mixture parameters, an average correlation input, and separate
serial-correlation assumptions. This milestone implements observed-family
corrections and their implied IID Sharpe mapping. Full empirical-population
Harvey-Liu simulation remains deferred. Average correlation supplies insufficient
information to identify a general joint null distribution, so this design uses
BY and retains the raw trial count. A fixed universal t=3 hurdle has no role.

## Exact statistical interface and mathematics

Add `src/features/multiple_testing.py`:

```python
def adjust_pvalues(
    pvalues: pd.Series, *, method: str = "by", family_size: int | None = None,
) -> pd.Series: ...

def return_test_statistics(
    returns: pd.Series, *, periods_per_year: int = 252,
) -> dict[str, object]: ...

def sharpe_haircut(
    observed_sharpe: float, *, n_observations: int,
    adjusted_pvalue: float, periods_per_year: int = 252,
) -> dict[str, float]: ...
```

Let m be the declared family size, k the supplied slots, and p_(i) the sorted
p-values with unavailable slots represented internally by 1. Preserve missing
outputs as NaN, order, index labels, duplicate labels, and index name.

- Bonferroni: q_i = min(1, m p_i).
- Holm: q_(i) = min(1, max_(j<=i) [(m-j+1) p_(j)]).
- BH: q_(i) = min(1, min_(j>=i) [m p_(j)/j]).
- BY: q_(i) = min(1, H_m min_(j>=i) [m p_(j)/j]),
  H_m = sum_(j=1)^m 1/j. Implicit additional p=1 slots contribute only the
  upper bound 1. Reuse SciPy FDR for the supplied slots and scale for declared m.

Input validation accepts real numeric, non-boolean one-dimensional Series.
NaN means unavailable; infinity, out-of-range p-values, unsupported methods,
and family sizes below k raise. Empty input returns an empty labeled Series.
Integer count arguments exclude booleans and require exact representability
through 2**53-1. Periods per year is a positive integer.

For a complete chronological return series of T>=3 finite observations:
s = sample standard deviation (ddof=1), SR = mean(r)/s * sqrt(A),
t_IID = mean(r)/s * sqrt(T), p_IID = 2*StudentT.sf(abs(t_IID), T-1).
Reuse `newey_west_mean_tstat` with lag count floor(4*(T/100)**(2/9));
p_HAC = 2*Normal.sf(abs(z_HAC)). Return sample count, status, mean, observed
annualized Sharpe, lag count, both statistics, and both raw p-values.
Missing observations withhold the whole trial's inference; preserve the supplied
sample and its missing count. Constant series, insufficient samples, and
nonfinite intermediate statistics have explicit undefined statuses. JSON output
uses null for undefined values. Measured returns exclude the existing first-bar
anchor exactly once. Existing transaction costs and slippage remain included.

For each adjusted IID q, t_adjusted = StudentT.isf(q/2, T-1),
SR_adjusted = sign(SR) * min(abs(SR), t_adjusted*sqrt(A/T)),
haircut_fraction = 1 - abs(SR_adjusted)/abs(SR).
This signed magnitude shrinkage retains unfavorable signs. SR=0 yields zero
adjusted SR and zero haircut. Reject q below its corresponding raw IID p-value.
q=0 preserves SR at the representable tail limit; q=1 yields zero magnitude.
Underflowed raw p-values are floored at the smallest positive normal float;
the floor is disclosed and gives conservative tail resolution.
Report the Bonferroni IID hurdle StudentT.isf(0.05/(2m), T-1) for each T.
The implied critical Sharpe is that hurdle multiplied by sqrt(A/T).

## Integration and report contract

Add `research/multiple_testing_diagnostics.py` with:

```python
def summarize_multiple_testing(
    inventory: list[dict[str, Any]], *, family_size: int | None = None,
) -> dict[str, Any]: ...

def render_multiple_testing(summary: dict[str, Any]) -> str: ...
```

`_run_recorded_trial` attaches JSON-safe return-test statistics to each completed
attempt before its completion event is retained. Shared family summarization
deduplicates trials conservatively, applies all four methods to HAC and IID
p-values, and records method-specific IID haircuts and Bonferroni hurdles.
Each row carries its full trial ID and specification, status, all test results,
and explicit positive-mean/rejection flags. Fixed alpha is 0.05.

Both diagnostic runners add `multiple_testing` to their result and experiment
log metrics and render the shared section. The human table identifies every
trial by ID, factor, direction, weighting, and penalty; it includes raw HAC p,
four HAC adjusted p-values, BY significance/sign, IID Bonferroni haircut and
hurdle, and undefined status. Machine-readable logs retain all IID methods.
Existing DSR and PBO family disclosures remain intact. All statistical work
occurs after book execution and supplies reporting only.

Update `docs/current_roadmap.md`, `docs/engineering_log.md`, and generated
`docs/repo_map.md`. Generate a new synthetic evidence report for this milestone;
preserve historical real-data artifacts. Use synthetic Parquet fixtures to test
the real-data runner. Private-market-data execution requires its separate
accepted methodology and authorization.

## Acceptance, deterministic QA, and ablation

1. Published BH 1995 15-p-value example: exact adjusted values within numerical
   tolerance, four BH discoveries and three Bonferroni discoveries at 5%.
2. Independent hand-computed Bonferroni/Holm/BH/BY small-family oracles; ties,
   single/empty families, permutations, duplicate labels, missing slots,
   additional declared hypotheses, p=0/1, invalid types/ranges/counts.
3. Student-t mean and haircut inverse oracles; negative/zero effects, q=0/1,
   annualization, tiny p-values, wrong-direction adjustment refusal, short,
   constant, nonfinite, and overflow inputs.
4. Independent explicit Bartlett covariance calculation for HAC; correlated
   synthetic trial returns; HAC/IID distinction and disclosed marginal limits.
5. Family inclusion of both directions and weighting variants; failed and
   conflicting attempts; order-invariant deduplication; override sensitivity;
   strict JSON serialization; complete report rows; no arbitrary filtering.
6. Both runners produce the shared report/log fields. Synthetic integration
   verifies unchanged book returns, holdings, costs, DSR and PBO against baseline.
7. Full pytest suite with the repository's two CI lanes, Ruff, compile, build,
   and repository map freshness. Record environment, runtime, and results.

Design ablation removes a correlation-derived effective-count layer and the
empirical population simulator: the accepted four corrections remain defined
for fully correlated, mixed-sign, and arbitrary-dependence examples. The retained
BY procedure supplies the conservative dependence sensitivity. Recreating DSR
would duplicate an existing tested estimator, so reuse is required.
Implementation ablation preserves a frozen baseline, removes one candidate
abstraction or guard at a time, compares relevant behavior and cost, keeps
justified simplifications, and restores demonstrated regressions. Record gaps.

Freeze the card for independent plan review before implementation, then freeze
the passing implementation for two fresh GPT-only reviews. The coordinator
records exact-candidate acceptance and handles the authorized same-change PR
lifecycle under existing protected-merge rules. MATERIAL findings receive
evidence-backed remediation and fresh review. This task's authority and research
boundaries remain those of the owner's request and repository AGENTS.md.

## Primary references

- [SciPy FDR documentation and the published BH numerical example](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.false_discovery_control.html).
- Benjamini and Hochberg (1995), JRSS B 57(1), 289-300;
  Benjamini and Yekutieli (2001), Annals of Statistics 29(4), 1165-1188.
- [Harvey and Liu, Backtesting, author implementation](https://people.duke.edu/~charvey/backtesting/),
  including [Haircut_SR.m](https://people.duke.edu/~charvey/backtesting/Haircut_SR.m).
- [Harvey and Liu (2015), Backtesting](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2345489).
- Existing Bailey-Lopez de Prado DSR implementation and numeric oracle:
  `src/features/diagnostics.py`, `tests/test_m3_10_hardening.py`.

This card records the selected direction, mathematical contract, retained
limitations, implementation scope, and acceptance evidence required for M4.3.
