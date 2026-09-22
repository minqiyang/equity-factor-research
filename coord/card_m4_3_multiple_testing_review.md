# Review Card: Milestone 4.3 Auditable Multiple-Testing Diagnostics

## Objective
Independent formal code review of Milestone 4.3 Auditable Multiple-Testing Diagnostics (`src/features/multiple_testing.py`, `research/multiple_testing_diagnostics.py`, and diagnostic runner integrations).

## Scope & Target
- Candidate branch: `feat/m4-3-multiple-testing-dsr`
- Lane: CRITICAL (owner directive authorizes single reviewer seat: GPT-6 Astra Extra High Fast)
- Reviewer route: Exactly 1 fresh independent GPT-6 Astra session (`gpt-6-astra`, `xhigh`, `service_tier="fast"`). Model-diversity degradation and single-seat review authorized by owner 24-hour directive.
- Output report: `coord/reports/m4_3_multiple_testing_review.md`
- Candidate digest: Exact HEAD commit of `feat/m4-3-multiple-testing-dsr` (to be recorded at candidate freeze).

## Key Review Checkpoints

### 1. Multiple-Testing Correction Mathematics (`src/features/multiple_testing.py`)
- **Bonferroni**: $q_i = \min(1, m \cdot p_i)$.
- **Holm Step-Down**: $q_{(i)} = \min(1, \max_{j \le i} [(m - j + 1) p_{(j)}])$.
- **Benjamini-Hochberg (BH)**: $q_{(i)} = \min(1, \min_{j \ge i} [\frac{m}{j} p_{(j)}])$.
- **Benjamini-Yekutieli (BY)**: $q_{(i)} = \min(1, H_m \min_{j \ge i} [\frac{m}{j} p_{(j)}])$, where $H_m = \sum_{j=1}^m \frac{1}{j} = \psi(m + 1) + \gamma$.
- **Family Size Scaling**: When `family_size` $m > k$, verify that unavailable slots are implicitly treated as $p=1$ and the scaling by $m$ is strictly correct.
- **Axis & Labeled Preservation**: Verify that `adjust_pvalues` strictly preserves the original index, index labels, duplicate labels, and Series name.
- **Edge Cases**: Empty Series, NaN slots, all-zero, all-one, ties, weak monotonicity ($q_{(i)} \ge p_{(i)}$).

### 2. Return Test Statistics & Causality
- **HAC & IID Statistics**:
  - Newey-West HAC $t$-statistic using `newey_west_mean_tstat` with Bartlett lag truncation $L = \lfloor 4 (T/100)^{2/9} \rfloor$.
  - IID Student-$t$ statistic: $t = \frac{\bar{r}}{s} \sqrt{T}$.
  - Correct degree of freedom $T - 1$ for Student-$t$ distribution.
- **Fail-Closed Degeneracy Handling**:
  - Sample size $T < 3$ returns status `insufficient_observations`.
  - Nonfinite returns return `nonfinite_observations`.
  - Constant series returns `zero_variance`.
  - Zero risk-free rate and sample standard deviation ($ddof=1$).
- **Zero Lookahead**: Returns evaluated strictly post-trade without leaking future return rows.

### 3. Sharpe Haircut Formulation & Tail Sensitivity
- **Haircut Inversion**:
  - $t_{\text{adjusted}} = \text{isf}(q/2, T - 1)$.
  - Signed shrinkage: $\text{SR}_{\text{adjusted}} = \text{sign}(\text{SR}) \cdot \min(|\text{SR}|, t_{\text{adjusted}} \sqrt{A/T})$.
  - $\text{haircut} = 1 - \frac{|\text{SR}_{\text{adjusted}}|}{|\text{SR}|}$.
- **Boundary Guarantees**:
  - $q = 1 \implies t_{\text{adjusted}} = 0 \implies \text{SR}_{\text{adjusted}} = 0, \text{haircut} = 1.0$.
  - $q = 0 \implies \text{haircut} = 0.0$.
  - Refuses $q < p_{\text{raw}}$ (adjusted p-value cannot be strictly more significant than raw).
  - Underflow protection using positive float floor `P_VALUE_FLOOR`.

### 4. Integration, Family Retention & Anti-Overengineering
- **Shared Summarization (`research/multiple_testing_diagnostics.py`)**:
  - `summarize_multiple_testing` covers all semantic trial combinations (factors, long-only, long-short, weighting, and penalty variants).
  - Failed and incomplete attempts retain family slots (All-Attempt Case Logging invariant preserved).
  - Strict JSON serialization (`allow_nan=False` compatible).
- **Pipeline Non-Interference**:
  - Integration into `multifactor_diagnostic_mvp.py` and `real_data_multifactor_diagnostic.py` does not alter book holdings, execution timing, turnover, PBO, or baseline DSR.
- **Anti-Overengineering**: Minimal diff footprint; no speculative multi-layer registry classes or unnecessary wrappers.

### 5. Verification Evidence
- Verification against published BH 1995 benchmark table.
- Independent test cases passing across both CI lanes (`core` and `diagnostics`).
- Ruff lint and compile clean.
