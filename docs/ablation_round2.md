# Round 2 Whole-Codebase Ablation: Quantified Evidence and Architecture Summary

> [!NOTE]
> **Document Status: Frozen B2 Checkpoint Accepted for Integration (Binding Plan A2)**  
> This document is a durable, detailed publication report prepared following formal acceptance of frozen review candidate `3e006260952521eac66b62dcaf4527fc867e453e04b8fbd7af180ea1e4a95392` (source manifest `fdfd4d7c8533bd6190171fa679ac4acc52a61ca6cb504427c92e9d3a932a28ac`, 448 files) as the implementation input to controlled integration under accepted binding plan A2. Three eligible mutually blind static reviews (GPT-6-Astra medium normal/default, Grok-4.6 xhigh, Gemini-3.8-Flash high) completed with zero MATERIAL findings and three OPEN advisories. Controlled integration creates a fresh candidate; final integration QA (including repeated campaign cohort and independent smoke execution of reproduction commands), fresh final-candidate static reviews, local latest/high normal Codex PR review, and Linux/Python 3.11 continuous integration gates remain pending. The owner has authorized a separate branch/PR after the required gates; merge, auto-merge, deployment and main pushes are not authorized. No integration, repeat, final-head review, commit, push, or publication has occurred at this checkpoint.

---

## 1. Executive Summary & Scope Definition

This report documents the quantitative outcomes, architectural mechanisms, quality assurance evidence, and defensive boundaries of the Round 2 whole-codebase ablation for the AI Equity Factor Research codebase (`ai_equity_factor_research`).

### 1.1 Context and Historical Relationship
The present Round 2 whole-codebase ablation builds upon and must be rigorously distinguished from prior experimental cycles:
1. **Prior Merged September 7 Ablation (`sep7-ablation`):** Completed 7 independent ablations (3 applied, 3 rejected, 1 deferred) resulting in a net reduction of 89 production Python lines (with 8 boundary tests added), achieving 2,572 passed tests and 2 platform skips. Its changes were integrated into mainline and are fully included within baseline commit `6ee193c9bb43f8290b3e09396fd241fec32df695`.
2. **Prior Unpublished Fast Pass (`sep7-fast-ablation`):** A subsequent separate exploratory session investigated 5 candidate removals (3 retained: `E01`, `E02`, `E05`; 2 rejected: `E03`, `E04`), achieving 2,598 passed tests and 2 skips. This work was a separate, unpublished investigation; its gains are not counted twice and no speedups from that exploratory pass are added to Round 2.
3. **Current Round 2 Whole-Codebase Scope:** Initiated to address an owner-identified P1 claim-calibration boundary: whole-codebase ablation requires systematic accounting of all subsystems, explicit reading depths, experimental controls, boundary invariant defenses, paired workload timings across multiple scales, and memory instrumentation, rather than local hypothesis sampling.

### 1.2 Frozen Baseline and Candidate Checkpoint Identity
- **Baseline Commit:** `6ee193c9bb43f8290b3e09396fd241fec32df695` (439 inventoried files, manifest `70237d678616cd309632117cac062dba9d24d63f29d9fd97361b29a4b2146dc4`).
- **Candidate Checkpoint Tree:** 448 files (9 files added over baseline), with candidate source manifest SHA-256 `fdfd4d7c8533bd6190171fa679ac4acc52a61ca6cb504427c92e9d3a932a28ac`.
- **Review Candidate Content Identity:** `3e006260952521eac66b62dcaf4527fc867e453e04b8fbd7af180ea1e4a95392`.
- **Operating Environment for Timing & Instrumentation:** Apple Silicon macOS (macOS 27 arm64), existing isolated Python 3.12.14 virtual environment, NumPy 2.5.2, pandas 3.0.5, SciPy 1.18.1, pytest 9.1.1, Ruff 0.16.6. Thread settings locked to 1 for all numerical libraries.

### 1.3 Whole-Round Inventory Coverage and Stated Limitations
The Round 2 survey accounts for all **439 first-party files** across inventory groups as recorded in `coverage_a.json`:

| Subsystem / Functional Group | Inventoried File Count | Primary Classification |
|---|---:|---|
| Tests (`tests/`) | 197 | Deterministic test oracles, synthetic data, regression fixtures |
| Documentation & Contracts (`docs/`) | 111 | Architectural specs, engineering log, contracts, repo map |
| Source Packages (`src/`) | 75 | Core production packages across 10 subsystems (see breakdown below) |
| Reports & Summaries (`reports/`) | 14 | Historical phase reports, binding plans, validation notes |
| Research Workflows (`research/`) | 14 | Synthetic end-to-end backtests, factor sweeps, fixture demos |
| Graphical Assets (`assets/`) | 11 | Static documentation images and figures |
| Root Project Controls (`(root)`) | 9 | Build configuration, license, pyproject, pyright |
| Lean Platform Scaffolding (`lean/`) | 3 | Lean platform integration stubs |
| Administrative Tooling (`scripts/`) | 2 | Repo map generator, audit helpers |
| Agent Workflows (`.agents/`) | 2 | Skill guidelines and task definitions |
| Continuous Integration (`.github/`) | 1 | GitHub Actions workflow configuration |
| **Total Baseline Inventory** | **439** | **Complete repository scope** |

The **75 files under `src/`** span ten distinct subsystem packages:
- `src/campaign/`: 21 files (runner, inference, accounting, schedule, factors, entry)
- `src/ledger/`: 23 files (3 Python modules + 20 package resources in `src/ledger/schemas/`, comprising JSON schemas and checksum sidecars)
- `src/features/`: 11 files (operators, validation, diagnostics, liquidity, alphas)
- `src/pit_manifest_validator_v1/`: 5 files (parser, validator, canonicalizer, CLI)
- `src/backtest/`: 4 files (portfolio, metrics, slippage, risk)
- `src/reporting/`: 4 files (experiment log, registry, plot placeholders)
- `src/data/`: 3 files (CSV loaders, metadata inventory, wrappers)
- `src/risk/`: 2 files (constraints, position sizing)
- `src/strategies/`: 1 file (initialization placeholder)
- `src/utils/`: 1 file (initialization placeholder)

Across the **72 runtime and tooling files** classified for execution analysis, the producer recorded explicit read depths:
- **29 Full-File Reads:** Producer-recorded full source inspection of module logic, internal helpers, and data structures.
- **43 Targeted Reads:** Structural inspection of public interfaces, symbol exports, caller/callee boundaries, and validator chains.

> [!WARNING]
> **Coverage Boundaries & Non-Claims:**  
> Producer-recorded read depth classifications reflect survey documentation depth, not a claim of 100% semantic verification or line-by-line proof of all 23,094 source Python lines or 43,240 test Python lines. No claim of universal minimality, code-deletion quota fulfillment, or exhaustive formal equivalence across arbitrary inputs is made.

---

## 2. Experiment Inventory & Complete Disposition Table

During Phase A and Phase A2, eighteen initial prototype variants were designed, implemented in isolation, and experimentally challenged against the frozen baseline. Seven directions were ultimately accepted into the binding plan and implemented in Phase B1, with C10b refined in Phase B2.

### 2.1 Complete 19-Row Prototype & Replacement Disposition Table

The table below details all **18 initial exploratory variants plus the C04b replacement (19 rows total)**, documenting their target files, intended mechanisms, experimental findings, and final dispositions:

| Prototype ID | Subsystem & Target File | Intended Mechanism / Hypothesis | Experimental Outcome & Evidence | Final Disposition & Rationale |
|---|---|---|---|---|
| **C01_campaign_index** | `src/campaign/runner.py` | Cache panel date index as a cached property on `_PreparedPanel`. | 61 tests passed; end-to-end parity exact. Adversarial probes revealed stale date index when private panel is directly mutated or reconstructed. | **Rejected / Superseded.** Direct panel construction must remain safe. Superseded by C01c. |
| **C01b_parser_owned_index** | `src/campaign/runner.py` | Return an indexed panel subtype directly from `_parse_prepared_campaign`. | `dataclasses.replace` on returned indexed panel retained stale index across replacements. | **Rejected / Superseded.** Superseded by C01c. |
| **C01c_execution_owned_index** | `src/campaign/runner.py` | Construct date index locally within `_execute_prepared`, bounding its lifetime to one execution. | 61 tests passed; mutation boundary probes passed. Index constructed per execution; direct parser mutation behavior fully retained. 5.197s vs 27.280s baseline. | **Selected for Binding Plan.** Implemented in candidate; execution-local lifetime eliminates stale cache risk. |
| **C02_registry_once** | `src/ledger/schema_registry.py` | Eliminate redundant structural schema traversals within a single validation call. | 1,413 tests passed; raw duplicate key/number/encoding checks and packaged authority preserved. 0.900s→0.378s (30 validations). | **Selected for Binding Plan.** Implemented in candidate; preserves complete release isolation and final event verification. |
| **C03_bootstrap_arrays** | `src/campaign/inference.py` | Vectorize bootstrap resampling loops using NumPy arrays. | Numerical parity failed on signed zero (`-0.0` vs `0.0`); also violated T-8 frozen inference file SHA-256 byte freeze. | **Rejected / Superseded.** Unacceptable numerical drift; core statistical contracts are frozen. |
| **C03b_bootstrap_zero_seed** | `src/campaign/inference.py` | Corrected bootstrap array loop preserving signed zero across 18 seed segments. | Passed numerical corpus, but yielded only an 8.4% subpath speedup and still tripped the T-8 frozen byte gate. | **Not Selected.** Marginal subpath gain does not justify altering frozen statistical artifact contracts. |
| **C04_snapshot_columns** | `src/backtest/portfolio.py` | Replace row-by-row cell inspection in `capture_backtest_source_provenance` with column iteration. | 217 tests passed; 1.386x backtest gain. However, independent QA uncovered that 2-row x 0-column input changed original cells from `((), ())` to `()`. | **Withdrawn / Superseded.** Independent finding QA-A-C04-EMPTY demonstrated public API regression. Superseded by C04b. *(Superseded A1 'selected' label withdrawn).* |
| **C04b_snapshot_empty_axes** | `src/backtest/portfolio.py` | Column iteration with explicit check: if column count is zero, return one empty tuple per source row. | Passed all 39 public capture probe records including Nx0, 0xM, 0x0; 74 regression tests and 300 original tests passed. 1.394x paired backtest gain. | **Selected for Binding Plan (A2).** Replaced withdrawn C04; preserves public provenance shape invariants exactly. |
| **C05_episode_arrays** | `src/backtest/metrics.py` | Access validated numeric metrics panels via NumPy array views instead of DataFrame scalars. | 130 tests passed; chronological episode state, fees, slippage, turnover, and terminal open exclusion preserved. 3.270s→2.306s backtest gain. | **Selected for Binding Plan.** Implemented in candidate; scalar lookup eliminated without changing accounting engine. |
| **C06_sweep_preparation** | `research/` | Extract parameter preparation across 8 sweep cases using an unchecked `_prepared` parameter. | 24 tests passed, but interface allowed declaring 9 assets while executing 4. Modest 5.7% speedup. | **Rejected Prototype.** Bypassing validation for marginal throughput degrades defensive boundaries. |
| **C10_diagnostics_batch** | `src/features/diagnostics.py` | Full batching of both Pearson and Spearman correlation across factor matrices. | 100 tests passed, but finite high-offset stress case exhibited Pearson numerical difference of 1.4686e-8. | **Rejected / Superseded.** Pearson must remain exact to baseline. Superseded by C10b. |
| **C10b_rank_ic_batch** | `src/features/diagnostics.py` | Leave Pearson exact to baseline; batch Spearman Rank IC by pair-masking, average-ranking, and row correlation. | Pearson exact; Spearman maximum absolute error on 48 stress cases is 5.5511e-17 (well within 1e-12 gate). 0.270s→0.113s. Refined in B2 with row-level valid asset-pair count pre-check (verifying whether any date row contains at least `min_periods` valid asset pairs). | **Selected for Binding Plan.** Implemented in candidate; numerical gate strictly enforced; repaired in B2. |
| **C12_label_gather** | `src/features/validation.py` | Batch eligible endpoint gathering and vectorized division after split reconstruction rather than scalar row indexing. | 80 tests passed; exact normalized byte equality on 1260x100 ledger/labels. 0.146s→0.050s. | **Selected for Binding Plan.** Implemented in candidate; batches eligible endpoint gathering and avoids repeated scalar indexing (baseline already restricted computation to eligible rows; optimization removes indexing and division overhead). |
| **C13_campaign_shared_returns** | `src/campaign/runner.py` | Construct execution-local memo of cost-independent interval return maps across the 14 trials. | 61 tests passed; exact raw output equality on campaign children; 27.280s→5.124s. Cost-dependent holdings remain unshared. | **Selected for Binding Plan.** Implemented in candidate; eliminates redundant interval evaluations across trials via execution-local `_held_map` and `_held_return` lookups, while cost-dependent holdings remain unshared. (Combined with C01c to optimize campaign execution). |
| **N04_snapshot_numpy** | `src/backtest/portfolio.py` | Coerce raw input DataFrame directly to homogeneous NumPy array via `to_numpy()`. | 168 ordinary tests passed, but mixed uint64/float and real/complex provenance identity probes failed silently. | **Rejected Negative Control.** Demonstrates that ordinary tests miss precision loss in mixed-type financial data. |
| **N07_catalog_no_snapshot** | `src/ledger/runtime.py` | Remove defensive transactional catalog snapshots during ledger commit. | 91 ordinary tests passed, but source mutation between validation and commit altered records (`RECORD_CONTENT_MISMATCH`). | **Rejected Negative Control.** Proves transactional snapshots are mandatory to prevent mutation anomalies. |
| **N08_split_no_revalidation** | `src/features/validation.py` | Remove canonical split revalidation under the assumption that frozen dataclasses protect nested state. | 4 existing tests and forged-eligibility probe failed; frozen dataclasses do not freeze nested DataFrames. | **Rejected Negative Control.** Proves nested mutable collections require explicit structural revalidation. |
| **N09_stdlib_canonical** | `src/pit_manifest_validator_v1/` | Replace custom iterative PIT canonicalizer with Python standard library `json.dumps(sort_keys=True)`. | Failed package-tree freeze; changed UTF-16 surrogate ordering; accepted direct non-standard floats and oversized ints. | **Rejected Negative Control.** Custom canonical serialization preserves strict authority domains. |
| **N11_provenance_no_state_check** | `src/backtest/portfolio.py` | Omit runtime state digest checks during backtest execution. | Failed untracked source edit detection; timing test asserting `source_provenance_invalid` precedence failed. | **Rejected Negative Control.** Proves digest verification is essential to catch source changes during execution. |

### 2.2 Key Overrides and Corrections
1. **Withdrawal of C04 & Substitution with C04b:** A1 originally labeled C04 as selected. Independent finding `QA-A-C04-EMPTY` proved that C04 corrupted public provenance for 2-row x 0-column inputs (`((), ())` became `()`). C04 was formally withdrawn and superseded by C04b in Phase A2.
2. **Refinement of C10b in B2:** In Phase B1, C10b caused an 8.8 ms (+12.57%) regression on a tiny 4x3 fixture workflow because all rows were ranked as a batch before checking whether any date row contained at least `min_periods` valid asset pairs. B2 added an eligibility pre-check: if no individual date row contains at least `min_periods` valid asset pairs, ranking is bypassed entirely and an all-NaN series is returned immediately, restoring fixture performance without altering the eligible batch path or Pearson calculation.
3. **Distinction Between Prototypes and Directions:** The 18 prototypes represent exploratory variants and negative controls. Exactly seven directions were implemented into the frozen candidate.

---

## 3. Mechanisms and Preserved Architectural Boundaries

The seven implemented directions span six runtime source files:

### 3.1 Implemented Mechanisms
1. **C13 (Campaign Shared Returns - `src/campaign/runner.py`):**
   - *Mechanism:* Constructs a single dictionary in `_execute_prepared`, passed through `_execute_trial`, keyed by exact `(begin_session, end_session)` for that execution's fixed schedule. `_held_map` is populated once on first demand, eliminating redundant `_held_return` evaluations across trials.
   - *Preserved Boundary:* Dictionary lifetime is strictly execution-local. No module-level cache, persistent store, or cross-execution leakage. Cost-dependent state (`ContinuousHoldings`, transaction costs, slippage, cash adjustments, trial validity) is never cached or shared.
2. **C01c (Execution-Owned Anchor Index - `src/campaign/runner.py`):**
   - *Mechanism:* Builds an internal index at the entry of `_execute_prepared`, used for date lookups across pre-parsed records. Uses bisect to slice sorted source sessions.
   - *Preserved Boundary:* Index lifetime is restricted to the execution call. Direct calls to private helpers without indexed views fall back to safe linear scans. Base panel mutation behavior is fully preserved.
3. **C02 (Registry Traversal Consolidation - `src/ledger/schema_registry.py`):**
   - *Mechanism:* `_require_packaged_registry_authority` validates structural rules once and returns the validated object; `validate_event` reuses this object rather than initiating another validation traversal.
   - *Preserved Boundary:* Preserves packaged digest authority, ASCII canonical serializer, R0 default, raw duplicate key/number rejection, and final event validation in `_commit_event`. No public "already validated" bypass flags.
4. **C04b (Empty-Axis Column Iteration - `src/backtest/portfolio.py`):**
   - *Mechanism:* When snapshotting source cells, checks if column count is 0. If so, emits one empty tuple per source row; otherwise, iterates column arrays and applies `_snapshot_source_cell` to each scalar.
   - *Preserved Boundary:* Preserves Nx0, 0xM, and 0x0 capture invariants, duplicate/named/MultiIndex axes, wide integer identity (uint64), complex numbers, Fractions, signed zeros, and original/current state digests.
5. **C05 (Validated Episode Arrays - `src/backtest/metrics.py`):**
   - *Mechanism:* Extracts NumPy array views only after metrics validators have verified aligned numeric panels, replacing DataFrame scalar lookup overhead during episode accounting.
   - *Preserved Boundary:* Retains the chronological episode loops and accounting state machine. Active-episode lifecycle, pro-rata fee/slippage allocation, exact turnover reconciliation, and terminal-open exclusion remain unchanged. C05 does NOT eliminate episode loops; it retains loops while operating on validated array data.
6. **C12 (Eligible Label Endpoint Gathering - `src/features/validation.py`):**
   - *Mechanism:* After canonical split reconstruction, gathers start and end price endpoints for eligible rows as contiguous arrays, computes price returns via vectorized division, and assigns into the output panel, replacing repeated scalar indexing and per-row assignment. (Baseline already restricted evaluation to eligible rows; C12 batches the gathering and computation).
   - *Preserved Boundary:* Preserves Series/DataFrame interfaces, purge/embargo boundaries, date alignment, and missing value representations. Full-source future labels are never computed and masked retroactively.
7. **C10b (Batched Rank IC with Eligibility Gating - `src/features/diagnostics.py`):**
   - *Mechanism:* Retains the original row-loop Pearson calculation untouched. For Spearman, applies pairwise valid masks, checks if each date row meets `min_periods` valid asset pairs (B2 repair), ranks eligible rows with average ties, and computes row correlations.
   - *Preserved Boundary:* Pearson correlation is exact to baseline. Spearman Rank IC alone has the accepted absolute 1e-12 numerical gate. Axis names, dtypes, NaN masks, and public input error orders are preserved.

### 3.2 Preserved Core Invariants & Disclosures
- **No Strategy or Commercial Invention:** No new trading strategies, alpha formulations, portfolio optimization models, live trading connectors, brokerage interfaces, or profitability claims are introduced.
- **Statistical Separation:** Common-month primary inference rules remain distinct from continuous economic returns. RNG seeds, Holm adjustments, and classification semantics are preserved.
- **Numerical Gate Scope:** Pearson correlation, axes, dtypes, names, NaN masks, and public error order remain exact to baseline in tested contracts. ONLY Spearman Rank IC operates under the accepted absolute 1e-12 tolerance.
- **Warning Frequency Disclosure:** In accepted plan A2 (line 97) and implementation B1 (line 49), it was explicitly disclosed that third-party constant-input warnings (e.g., SciPy/pandas `ConstantInputWarning`) occur less frequently under C10b batch ranking than under baseline per-row `Series.corr` (e.g., 0 vs 25 warnings on feature validation test suites). This warning-frequency change is an accepted behavioral difference, with output values exact to baseline except for the accepted absolute 1e-12 tolerance on Spearman Rank IC, and public error conditions remaining exact.

---

## 4. Comprehensive Producer Workload Matrix (18 Workloads)

### 4.1 Measurement Protocol
All 18 workloads were evaluated under the B2 matrix protocol (`repair_b2/runs/matrix_002`):
- **Cohort:** 18 distinct workloads covering synthetic and committed-fixture paths.
- **Sample Design:** Seven alternating baseline, B1, and B2 triples (126 triples, 378 total executions).
- **Execution Isolation:** Every execution ran in an independent fresh Python subprocess following one unprofiled warmup execution. Order within each triple was rotated/reversed across pairs.
- **Host Context:** Runs began after lower-load checks, but host background activity varies over time and its exact causal effect cannot be isolated. Matched serial order mitigates confounding across variants within each triple, but does not demonstrate control of all shared host conditions. Observed values are reported directly without causal speculation or automatic noise thresholds.

### 4.2 Complete 18-Workload Benchmark Results

The table below presents producer matrix results across all 18 workloads, recording medians, min/max ranges, baseline/B2 and B1/B2 speedup ratios, explicit elapsed-time deltas, percentage shifts, and slower pair counts:

| Workload ID & Case Scope | Baseline Median [Min, Max] (s) | B1 Median [Min, Max] (s) | B2 Median [Min, Max] (s) | B2 vs Base Delta (% / Ratio) | B2 vs B1 Delta (% / Ratio) | B2 Slower than B1 |
|---|---:|---:|---:|---:|---:|:---:|
| `campaign_504x100` | 18.812112 [18.342081, 20.500147] | 1.431882 [1.422953, 1.448038] | 1.441289 [1.416513, 1.463597] | -17.371 s (-92.34% / 13.052×) | +9.4 ms (+0.66% / 0.993×) | 5 / 7 |
| `campaign_84x10_below_floor` | 0.008245 [0.007965, 0.008769] | 0.008100 [0.007983, 0.009287] | 0.008013 [0.007920, 0.008731] | -0.232 ms (-2.81% / 1.029×) | -0.087 ms (-1.08% / 1.011×) | 3 / 7 |
| `backtest_160x12` | 0.151932 [0.150477, 0.155687] | 0.096890 [0.096443, 0.098225] | 0.096672 [0.095875, 0.099899] | -55.260 ms (-36.37% / 1.572×) | -0.218 ms (-0.22% / 1.002×) | 3 / 7 |
| `backtest_504x100` | 2.216679 [2.205956, 2.244941] | 0.910506 [0.909615, 0.921145] | 0.913914 [0.911066, 0.923825] | -1.303 s (-58.77% / 2.425×) | +3.4 ms (+0.37% / 0.996×) | 5 / 7 |
| `features_160x12` | 0.010824 [0.010500, 0.011368] | 0.010669 [0.010499, 0.011027] | 0.010725 [0.010491, 0.010990] | -0.099 ms (-0.91% / 1.009×) | +0.056 ms (+0.53% / 0.995×) | 4 / 7 |
| `features_504x100` | 0.036696 [0.036367, 0.037702] | 0.036777 [0.036549, 0.037480] | 0.036525 [0.036265, 0.037834] | -0.170 ms (-0.46% / 1.005×) | -0.251 ms (-0.68% / 1.007×) | 3 / 7 |
| `features_1260x500` | 0.251411 [0.248776, 0.261245] | 0.251522 [0.248643, 0.263656] | 0.250782 [0.247352, 0.255328] | -0.629 ms (-0.25% / 1.003×) | -0.741 ms (-0.29% / 1.003×) | 3 / 7 |
| `labels_1260x100` | 0.099651 [0.098301, 0.100509] | 0.034210 [0.034028, 0.035307] | 0.034563 [0.034008, 0.035343] | -65.088 ms (-65.32% / 2.883×) | +0.353 ms (+1.03% / 0.990×) | 5 / 7 |
| `diagnostics_504x100_sparse` | 0.183312 [0.181282, 0.185061] | 0.077203 [0.076164, 0.094676] | 0.077906 [0.077412, 0.079873] | -105.406 ms (-57.50% / 2.353×) | +0.703 ms (+0.91% / 0.991×) | 5 / 7 |
| `sweep_160x12_eight_cases` | 1.242607 [1.230281, 1.261512] | 0.775320 [0.773309, 0.808862] | 0.783465 [0.773462, 0.803607] | -459.141 ms (-36.95% / 1.586×) | +8.145 ms (+1.05% / 0.990×) | 3 / 7 |
| `fixture_all_configured` | 0.046235 [0.044502, 0.046587] | 0.050919 [0.049215, 0.052250] | 0.044466 [0.044169, 0.045399] | -1.769 ms (-3.83% / 1.040×) | -6.452 ms (-12.67% / 1.145×) | 0 / 7 |
| `ledger_a` | 0.196732 [0.194527, 0.214537] | 0.089259 [0.086346, 0.108228] | 0.087859 [0.086938, 0.090592] | -108.874 ms (-55.34% / 2.239×) | -1.400 ms (-1.57% / 1.016×) | 1 / 7 |
| `ledger_a_1000` | 0.270166 [0.266914, 0.277021] | 0.161596 [0.159566, 0.163931] | 0.160476 [0.159420, 0.165726] | -109.690 ms (-40.60% / 1.684×) | -1.119 ms (-0.69% / 1.007×) | 2 / 7 |
| `ledger_b` | 0.197585 [0.194139, 0.203866] | 0.088713 [0.086406, 0.090465] | 0.088313 [0.085495, 0.089801] | -109.271 ms (-55.30% / 2.237×) | -0.400 ms (-0.45% / 1.005×) | 2 / 7 |
| `ledger_b_1000` | 0.271843 [0.268375, 0.292202] | 0.162485 [0.161524, 0.169545] | 0.163081 [0.161737, 0.176689] | -108.762 ms (-40.01% / 1.667×) | +0.596 ms (+0.37% / 0.996×) | 5 / 7 |
| `registry_30` | 0.596901 [0.592206, 0.600308] | 0.243623 [0.240431, 0.259033] | 0.242939 [0.241651, 0.245797] | -353.962 ms (-59.30% / 2.457×) | -0.684 ms (-0.28% / 1.003×) | 3 / 7 |
| `manifest_20` | 0.064199 [0.063654, 0.065215] | 0.063998 [0.063867, 0.064479] | 0.064124 [0.063833, 0.064997] | -0.075 ms (-0.12% / 1.001×) | +0.126 ms (+0.20% / 0.998×) | 4 / 7 |
| `inference_120_20000_retained` | 0.642651 [0.633749, 0.651172] | 0.639363 [0.634499, 0.716508] | 0.640288 [0.635280, 0.648909] | -2.363 ms (-0.37% / 1.004×) | +0.925 ms (+0.14% / 0.999×) | 4 / 7 |

*Note on Parameter Semantics:* In ledger workloads, generic CLI `--rows` and `--assets` arguments are unused; workloads evaluate built-in synthetic catalog state (Paths A & B) and the +1,000 extra catalog records variant. In `fixture_all_configured`, the dataset is the committed 4-date × 3-asset fixture. In `registry_30` and `manifest_20`, rows represent repetition counts (30 validations and 20 validations respectively).

### 4.3 Analysis of Workload Outcomes & Adverse Findings
1. **Major End-to-End Speedups Retained:**  
   Substantial, repeatable throughput gains are established against the baseline across all primary execution paths:
   - Campaign Execution (`campaign_504x100`): **13.052×** speedup (18.812s → 1.441s, -92.34%).
   - Generic Backtest (`backtest_504x100`): **2.425×** speedup (2.217s → 0.914s, -58.77%); 160x12: **1.572×** (151.9ms → 96.7ms, -36.37%).
   - Feature Labels (`labels_1260x100`): **2.883×** speedup (99.7ms → 34.6ms, -65.32%).
   - Sparse Diagnostics (`diagnostics_504x100_sparse`): **2.353×** speedup (183.3ms → 77.9ms, -57.50%).
   - Research Sweep (`sweep_160x12_eight_cases`): **1.586×** speedup (1.243s → 0.783s, -36.95%).
   - Ledger Transactions (`ledger_a`, `ledger_b`): **2.237× – 2.239×** speedup (197ms → 88ms, -55.3%); with 1,000 extra records: **1.667× – 1.684×** (271ms → 161ms, -40.0% to -40.6%).
   - Schema Registry (`registry_30`): **2.457×** speedup (596.9ms → 242.9ms, -59.30%).
2. **Transparent Disclosure of Adverse B1-to-B2 Differences:**  
   B2 observations exhibit small shifts relative to B1:
   - In `campaign_504x100`, B2 median wall time (1.441s) is 9.4 ms (+0.66%) slower than B1 (1.432s), with B2 slower in 5 out of 7 pairs.
   - In `backtest_504x100`, B2 median (0.914s) is 3.4 ms (+0.37%) slower than B1 (0.911s), with B2 slower in 5 out of 7 pairs.
   - In `labels_1260x100`, B2 median (34.56ms) is 0.353 ms (+1.03%, ratio 0.990×) slower than B1 (34.21ms), with B2 slower in 5 out of 7 pairs.
   - In `sweep_160x12_eight_cases`, B2 median (783.5ms) is 8.145 ms (+1.05%, ratio 0.990×) slower than B1 (775.3ms), with B2 slower in 3 out of 7 pairs.
   - In `diagnostics_504x100_sparse`, B2 median (77.91ms) is 0.703 ms (+0.91%) slower than B1 (77.20ms), with B2 slower in 5 out of 7 pairs.
   - In `ledger_b_1000`, B2 median (163.08ms) is 0.596 ms (+0.37%) slower than B1 (162.49ms), with B2 slower in 5 out of 7 pairs.
   These shifts are reported exactly rather than dismissed under general noise labels.
3. **Cohort Distinction in Fixture Timing:**  
   In Phase B1, the committed 4x3 fixture workflow exhibited an initial +12.57% regression (69.835ms → 78.611ms, +8.78ms). In the resumed B2 matrix cohort (`matrix_002`), the baseline median is 46.235 ms, B1 is 50.919 ms, and B2 is 44.466 ms. B2 is faster than B1 in **7 out of 7 pairs** (a 1.145× ratio; -6.452 ms, -12.67%) and faster than baseline in **6 out of 7 pairs** (slower in 1 pair by 0.897 ms). Percentages must always be computed from the respective matched cohort.
4. **Preserved Contrary Observation in Independent Campaign 504 (Repetition 1):**  
   In the independent verification cohort (`independent_b2`), the single initial repetition of `campaign_504x100` recorded:
   - Baseline wall: **18.091250 s** (CPU 18.075572 s)
   - B1 runtime: wall **1.407054 s** (CPU 1.405663 s)
   - B2 candidate: wall **1.558791 s** (CPU 1.557491 s)
   - Difference: B2 was **+0.151737 s** (about **+10.8%**) slower than B1 in wall time, and **+0.151828 s** in CPU time.  
   This measurement is one single triple, not a repeated distribution, and must qualify B1-preservation statements. Equal runner source bytes between B1 and B2 do not prove host-noise causation. Recurrence and underlying cause remain unresolved; repeated independent campaign measurements are planned for final integration QA but **have not run**. No findings, acceptance, results, or aggregate counts are assumed for that future QA.

---

## 5. Distinct Independent Population & Audit Verification

To prevent reliance on self-certifying producer execution, a distinct independent verification population was executed under `qa/independent_b2/` and `qa/recorded_b2_audit/`.

### 5.1 Independent Population Scope & Test Counts
The `independent_b2` verification suite comprised **106 separate executions**:
- **Full Test Suite Executions:**
  - Baseline Full Suite: **2,573 passed, 2 platform skips** (97.43s).
  - B1 Full Suite: **2,722 passed, 2 platform skips** (36.28s; +149 tests over baseline).
  - B2 Candidate Full Suite: **2,758 passed, 2 platform skips, 1 warning** (36.53s; +36 tests over B1, +185 tests over baseline).
  Both skips reflect the platform condition where macOS longdouble offers no extended precision beyond float64.
- **Nine Rejected Mutation Controls:** 9 executions asserting that negative controls (`negative_C01`, `negative_C01b`, `negative_C04`, `negative_C10`, `negative_N04`, `negative_N07`, `negative_N08`, `negative_N09`, `negative_N11`) produce their expected deterministic failures.
- **30 Fresh Independent Triples:** Fresh baseline/B1/B2 measurements across all 18 scopes:
  - 7 fresh triples on `fixture_all_configured`
  - 7 fresh triples on `diagnostics_504x100_sparse`
  - 1 fresh triple on each of the remaining 16 scopes

### 5.2 Separate Fresh Import Cohort
The 7 fresh import triples plus 3 warmup processes constitute a **separate 24-process cohort** (`independent_b2_imports`), distinct from the 106 executions of `independent_b2`. Across 11 first-party modules, measured fresh-process import medians across the 7 measured triples were:
- **Baseline:** **0.205355 s** (`0.20535458299855236 s`)
- **B1:** **0.206648 s** (`0.20664750000287313 s`)
- **B2 Candidate:** **0.205939 s** (`0.2059387090121163 s`)

### 5.3 Independent Timings vs Producer Evidence
Producer focused (14 triples), producer full matrix (126 triples), and resource profiles (14 triples) are recorded recomputed evidence; they do not constitute independent timing samples.

In the independent population:
- **Independent Fixture Medians:** Baseline **43.368958 ms**, B1 **48.363959 ms**, B2 **42.282500 ms**. B2 is faster than B1 in **7/7 pairs**.
- **Independent Sparse IC Medians:** Baseline **178.135042 ms**, B1 **74.979042 ms**, B2 **75.295666 ms**. B2 is slower than B1 in **4/7 pairs** (pairs 2, 4, 6, 7).
- **Independent Campaign Repetition 1 (Single Triple):** Baseline **18.091250 s**, B1 **1.407054 s**, B2 **1.558791 s** (+0.151737 s, ~+10.8% B2 vs B1; CPU 1.557491 s vs 1.405663 s). This single observation qualifies B1 preservation; recurrence and cause remain unresolved pending final integration QA.

> [!IMPORTANT]
> **Interpretation of Finite Samples:**  
> Finite sample ranges are empirical observations, not asymptotic confidence intervals. Small percentage differences (e.g. B2 sparse IC ~0.4% slower than B1) are neither automatically noise nor proof of degradation. The report preserves all individual sample values and does not prescribe owner risk acceptance.

---

## 6. Resource Profiles & Memory Tradeoffs

Timing speedups must be evaluated alongside instrumented resource and allocation behavior. Resource profiles were captured under `qa/recorded_b2_audit/resources.json` using current B2 measurements.

### 6.1 Current Instrumented Resource Metrics (B2 Checkpoint)

| Workload Case | Mode | Baseline Measured | B1 Measured | B2 Candidate Measured | Causal Attribution / Analysis |
|---|---|---:|---:|---:|---|
| `labels_1260x100` | Profile (Calls) | 1,395,314 calls | 298,527 calls | **298,527 calls** | 78.6% call reduction; batches eligible endpoint gathering and division, eliminating repeated scalar indexing. |
| `labels_1260x100` | Memory (Tracemalloc) | 2,961,986 bytes | 4,678,517 bytes | **4,676,808 bytes** | **+57.9% (+1,714,822 bytes) allocation increase**; batched endpoint arrays offer plausible context; causal attribution is not isolated. |
| `labels_1260x100` | Memory (Peak RSS) | 113,901,568 bytes | 113,917,952 bytes | **113,836,032 bytes** | Process RSS effectively flat (-65,536 bytes, -0.06%). |
| `diagnostics_504x100_sparse` | Profile (Calls) | 2,045,460 calls | 940,804 calls | **941,275 calls** | 54.0% call reduction from batched Spearman rank correlation. |
| `diagnostics_504x100_sparse` | Memory (Tracemalloc) | 272,308 bytes | 3,981,408 bytes | **3,986,292 bytes** | **Peak 14.6× baseline (+3,713,984 bytes)**; intermediate rank correlation matrices offer plausible context. |
| `diagnostics_504x100_sparse` | Memory (Peak RSS) | 162,185,216 bytes | 97,058,816 bytes | **96,976,896 bytes** | **-40.2% RSS reduction (-65,208,320 bytes)**; batch execution offers plausible context; allocation and RSS causes not isolated. |
| `campaign_504x100` | Profile (Calls) | 622,526,103 calls | 34,626,624 calls | **34,626,584 calls** | 94.4% call reduction from combined campaign optimizations (C13 execution-local `_held_map` / `_held_return` memo and C01c execution-owned date index); eliminates redundant interval return lookups. |
| `campaign_504x100` | Memory (Tracemalloc) | 103,348,539 bytes | 103,868,362 bytes | **103,868,016 bytes** | Observed +0.50% (+519,477 bytes) allocation increase; interval return memo provides plausible context, not isolated causal attribution. |
| `campaign_504x100` | Memory (Peak RSS) | 417,792,000 bytes | 419,217,408 bytes | **419,512,320 bytes** | +0.41% (+1,720,320 bytes) instrumented process RSS increase. |
| `backtest_504x100` | Profile (Calls) | 31,682,116 calls | 12,478,269 calls | **12,478,177 calls** | 60.6% call reduction; eliminates scalar cell conversions and episode lookups. |
| `backtest_504x100` | Memory (Tracemalloc) | 39,863,469 bytes | 39,853,700 bytes | **39,851,483 bytes** | Peak allocation virtually unchanged (-11,986 bytes, -0.03%). |
| `backtest_504x100` | Memory (Peak RSS) | 252,739,584 bytes | 250,331,136 bytes | **250,462,208 bytes** | -0.90% (-2,277,376 bytes) process RSS reduction. |
| `features_1260x500` | Profile (Calls) | 1,327,864 calls | 1,328,002 calls | **1,327,910 calls** | Unmodified control; 1,327,864 baseline vs 1,327,910 B2 (+46 calls, +0.003%). |
| `features_1260x500` | Memory (Tracemalloc) | 121,298,216 bytes | 121,298,406 bytes | **121,298,259 bytes** | Unmodified control; 121,298,216 bytes baseline vs 121,298,259 bytes B2 (+43 bytes). |
| `features_1260x500` | Memory (Peak RSS) | 1,248,411,648 bytes | 1,248,296,960 bytes | **1,248,329,728 bytes** | Unmodified control; 1,248,411,648 bytes baseline vs 1,248,329,728 bytes B2 (-81,920 bytes, -0.007%). |
| `ledger_b_1000` | Profile (Calls) | 7,632,928 calls | 5,088,268 calls | **5,088,232 calls** | 33.3% call reduction; eliminates redundant registry schema traversals. |
| `ledger_b_1000` | Memory (Tracemalloc) | 3,045,880 bytes | 3,046,246 bytes | **3,045,912 bytes** | 3,045,880 bytes baseline vs 3,045,912 bytes B2 (+32 bytes). |
| `ledger_b_1000` | Memory (Peak RSS) | 103,432,192 bytes | 103,890,944 bytes | **103,596,032 bytes** | 103,432,192 bytes baseline vs 103,596,032 bytes B2 (+163,840 bytes, +0.16%). |
| `registry_30` | Profile (Calls) | 14,591,912 calls | 6,109,712 calls | **6,109,592 calls** | 58.1% call reduction; 90 structural schema validations reduced to 30. |
| `registry_30` | Memory (Tracemalloc) | 370,007 bytes | 369,994 bytes | **369,959 bytes** | Peak allocation 370,007 bytes baseline vs 369,959 bytes B2 (-48 bytes). |
| `registry_30` | Memory (Peak RSS) | 94,879,744 bytes | 94,175,232 bytes | **93,503,488 bytes** | -1.45% (-1,376,256 bytes) process RSS reduction. |

### 6.2 Evaluation of Resource Behavior
- **Memory Tradeoffs:** Vectorized NumPy paths trade temporary array allocations for execution speed. In `diagnostics_504x100_sparse`, tracemalloc peak rises from 272,308 bytes to 3,986,292 bytes (peak 14.6× baseline, +3,713,984 bytes) to hold intermediate rank matrices; simultaneously, peak RSS drops from 162,185,216 bytes to 96,976,896 bytes (-65,208,320 bytes, -40.2%). Mechanisms provide plausible context, not isolated causal proofs; causal attribution between internal allocation changes and process-level RSS was not isolated.
- **No Uniform Memory Claim:** The candidate does not achieve uniform memory reduction. In `labels_1260x100`, tracemalloc peak increases from 2,961,986 bytes to 4,676,808 bytes (+1,714,822 bytes, +57.9%).
- **Campaign Process RSS: Unprofiled Campaign vs Instrumented Mode:**
  Unprofiled campaign measurements must be distinguished from instrumented profiling runs:
  - In **unprofiled campaign execution** (`campaign_504x100` measured samples across 7 triples in `performance_summary.json`), process median peak RSS was:
    - Baseline: **309,526,528 bytes**
    - B1: **310,706,176 bytes** (+1,179,648 bytes, +0.38% vs baseline)
    - B2 Candidate: **311,394,304 bytes** (+1,867,776 bytes, +0.60% vs baseline; +688,128 bytes, +0.22% vs B1)
  - In **instrumented memory profiling mode** (`resources_summary.json`), peak RSS includes tracemalloc tracking overhead and evidence serialization:
    - Baseline: **417,792,000 bytes**
    - B1: **419,217,408 bytes** (+1,425,408 bytes, +0.34% vs baseline)
    - B2 Candidate: **419,512,320 bytes** (+1,720,320 bytes, +0.41% vs baseline; +294,912 bytes, +0.07% vs B1)
  Both measurements preserve the adverse finding that campaign execution peak RSS increased slightly in B1 and B2, rather than decreasing.
- **Profiling Calls vs Throughput:** Total call reductions in `cProfile` (e.g. 622.5M to 34.6M in campaign) corroborate that work was removed from hot loops, but total call changes do not isolate every causal contribution. Throughput is established by unprofiled fresh-process wall clock times.

---

## 7. Code Churn & Structural Impact

### 7.1 Git-Numstat Churn Breakdown
The code churn between baseline commit `6ee193c9bb43f8290b3e09396fd241fec32df695` and candidate checkpoint `fdfd4d7c8533bd6190171fa679ac4acc52a61ca6cb504427c92e9d3a932a28ac` is measured using `git diff --numstat`:

```
13      0       AGENTS.md
133     0       docs/engineering_log.md
2       2       docs/repo_map.md
14      8       src/backtest/metrics.py
6       4       src/backtest/portfolio.py
44      13      src/campaign/runner.py
35      16      src/features/diagnostics.py
4       4       src/features/validation.py
6       7       src/ledger/schema_registry.py
185     0       tests/ablation_public_capture_support.py
24585   0       tests/fixtures/ablation/ic_baseline.json
8       0       tests/fixtures/ablation/provenance.json
5732    0       tests/fixtures/ablation/public_capture_baseline.json
338     0       tests/test_ablation_c10b_eligible_rank.py
38      0       tests/test_ablation_campaign_ownership.py
168     0       tests/test_ablation_defensive_boundaries.py
41      0       tests/test_ablation_ic_golden.py
68      0       tests/test_ablation_public_capture.py
```

### 7.2 Summary by Functional Category

| Category | Files Changed | Lines Added | Lines Deleted | Net Churn | Notes |
|---|:---:|---:|---:|---:|---|
| **Production Python (`src/`)** | 6 | 109 | 52 | **+57** | Algorithmic optimizations & execution ownership |
| **Test Python (`tests/`)** | 6 (1 support + 5 tests) | 838 | 0 | **+838** | Defensive boundaries, IC goldens, capture tests |
| **Golden Fixtures (`tests/fixtures/`)** | 3 | 30,325 | 0 | **+30,325** | Immutable baseline oracle snapshots (IC, capture) |
| **Documentation & Controls** | 3 | 148 | 2 | **+146** | Process lessons, engineering log, repo map update |
| **Total Pre-Publication Churn** | **18 files** | **31,420** | **54** | **+31,366** | **Baseline 439 → Candidate 448 (+9 added files)** |

> [!NOTE]
> **Methodology and PR Scope Notice:**  
> 1. *Diff Alignment:* Standard `git diff --numstat` reports +109 / -52 on production Python. Certain versions of GNU `diffstat` may align one line in `diagnostics.py` differently (reporting +108 / -51), but the net line count is identically **+57 net lines**.
> 2. *Publication Material:* The counts above represent candidate code churn **before** drafting publication prose. The final whole-PR totals will include further documentation additions; checkpoint counts must not be mislabeled as whole-PR totals.

---

## 8. Failure History, Test Discipline & Source-Binding Corrections

A foundational requirement of this ablation round is preserving failed, noisy, and interrupted attempts, and documenting test discipline corrections without rewriting history.

### 8.1 Chronological Failure & Noise Record
1. **Initial Pytest Source-Binding Defect & Distinction of Solutions:**  
   When executing test scripts against separated worktrees using absolute file paths, pytest inspected the repository root `pyproject.toml` containing `pythonpath = ["src"]`. Consequently, the test runner imported modules from `work/src` rather than the requested candidate or baseline tree. Hashing the file on disk did not prove the loaded in-memory module.
   - *Producer Correction:* The producer established `repair_b2/isolated_qa/` with a local `pytest.ini` (omitting `pythonpath`), pinned `--rootdir` to that isolated directory, and utilized a local `conftest.py` recording `features.diagnostics.__file__` and SHA-256 at `sessionstart`, `collection_finish`, `session_fixture`, and `teardown`.
   - *Independent QA Correction:* Independent QA under `qa/independent_b2/` used `-o pythonpath=` alongside `-p independent_binding`, where a `pytest_collection_finish` hook directly asserted that both module `__file__` and function `factor_information_coefficient.__code__.co_filename` matched `QA_EXPECTED_SOURCE` along with matching SHA-256 digests.
2. **Checkpoint 001 Test-Discipline Regression & Restoration:**  
   During initial B2 repair attempts, test `test_mixed_rows_rank_only_eligible_dates` in `tests/test_ablation_c10b_eligible_rank.py` omitted the assertion `assert rank_indexes and corr_indexes`. Removing this assertion meant that a complete rollback to row-by-row looping would pass the test vacuously, losing the mechanism-level assertion that eligible rows actually execute via the batch path.
   - *Correction:* Checkpoint 001 was frozen as immutable at `frozen_checkpoint_001/` (manifest `24c72d8df...`). Checkpoint 002 restored `assert rank_indexes and corr_indexes` byte-for-byte from original inputs without changing runtime code (`b554c001...`). No assertions or tolerances in the current candidate were weakened.
3. **Bound Verification Results on Restored Checkpoint 002:**  
   With in-process module and code verification active, the restored guard yielded exact mechanism-control differentiation:
   - `bound2_baseline_eligible_rank`: **1 failed, 35 passed (exit 1)**. Expected mechanism control failure: `test_mixed_rows_rank_only_eligible_dates` line 193 fails `assert rank_indexes and corr_indexes` because baseline row loops never call `DataFrame.rank` or `corrwith`. Numerical contracts pass.
   - `bound2_b1_eligible_rank`: **6 failed, 30 passed (exit 1)**. Ineligible rows are improperly ranked by the un-repaired B1 batch path.
   - `bound2_b2_eligible_rank`: **36 passed, 0 failed (exit 0)**. Eligible rows use batch ranking; ineligible rows are skipped.
4. **Preserved Noisy and Interrupted Benchmark Attempts:**  
   - `focused_001`: An initial benchmark sample captured coincident background activity on the host system, yielding erratic medians (141.9ms base, 145.6ms B1, 171.7ms B2). This noisy attempt is retained in `logs/focused_001.log` and was rejected as acceptance proof.
   - `matrix_001`: Interrupted during campaign pair 1 when the source-binding issue was diagnosed; retained with `interrupted.txt` marker.
5. **Preserved Public Counterexample:**  
   The public 2-row x 0-column counterexample (`QA-A-C04-EMPTY`) is permanently retained as an automated negative regression (`tests/test_ablation_public_capture.py`), asserting that `((), ())` is preserved and digest `eae69de8...` is maintained.

---

## 9. Platform & Runtime Verification Boundaries

### 9.1 Verified Platform Environment
- **Hardware & OS:** Apple Silicon (macOS 27 arm64).
- **Runtime Interpreter:** Existing isolated Python 3.12.14 virtual environment.
- **Core Dependencies:** NumPy 2.5.2, pandas 3.0.5, SciPy 1.18.1, pytest 9.1.1, Ruff 0.16.6.
- **Build Certification (`platform_build_002`):**
  - All 161 repository Python files compiled in memory via `compile()` and parsed under Python 3.11 AST grammar rules without syntax errors.
  - Isolated distribution builds (`python -m build --no-isolation`) generated sdist (`e4c92832...`, containing 137 Python files) and wheel (`682b806f...`, containing 55 Python files).
  - All 20 package resources in `src/ledger/schemas/` (JSON schemas and checksum sidecars) verified exact within distribution archives.

### 9.2 Explicit Runtime Limitations
- **Prior Linux CI Fixture Resolution:** During earlier PR202 integration, decimal-fixture test failures occurred on Linux CI. Those fixture issues were corrected prior to merged baseline commit `6ee193c9bb43f8290b3e09396fd241fec32df695`, and baseline postmerge CI succeeded on Linux. Current B2 candidate execution on Linux and Python 3.11 has not been performed, so cross-platform runtime continuous integration remains unverified.
- **Current Linux & Python 3.11 Runtime CI Pending:** Execution on Linux x86_64 / aarch64 and Python 3.11 has not been performed for the current B2 candidate. Static grammar compilation under Python 3.11 does not establish runtime behavioral equivalence, standard library compatibility, or operating system allocator characteristics.
- **No Universal Minimality Claim:** The candidate retains substantial defensive scaffolding, recovery handlers, and reporting structures. No claim is made that the codebase is universally minimal.

---

## 10. Reproducibility & Public Artifact Architecture

### 10.1 Proposed Public Artifact Directory Structure
To enable third-party audit without publishing multi-gigabyte local working directories, the proposed compact public evidence package will be located at `docs/ablation_evidence/round2/`. It mirrors the 33-payload-file archive verified in `publication_evidence/manifest.sha256` (2,542,126 payload bytes; manifest SHA-256 `6b3fae7a5dcde564364075002047cb1890a137b4b3f7c5ed56417dac2520811e`):

```
docs/ablation_evidence/round2/
├── manifest.sha256                   # SHA-256 digests for all 33 payload files (manifest sha256: 6b3fae7a...)
├── b1_to_b2_diagnostics.patch        # Portable reverse patch to reconstruct B1 runtime from trusted candidate
├── experiments/                      # 18 counterfactual experiment patches (C01 to N11; not applied to candidate)
│   ├── C01_campaign_index.patch
│   ├── C01b_parser_owned_index.patch
│   ├── C01c_execution_owned_index.patch
│   ├── C02_registry_once.patch
│   ├── C03_bootstrap_arrays.patch
│   ├── C03b_bootstrap_zero_seed.patch
│   ├── C04_snapshot_columns.patch
│   ├── C05_episode_arrays.patch
│   ├── C06_sweep_preparation.patch
│   ├── C10_diagnostics_batch.patch
│   ├── C10b_rank_ic_batch.patch
│   ├── C12_label_gather.patch
│   ├── C13_campaign_shared_returns.patch
│   ├── N04_snapshot_numpy.patch
│   ├── N07_catalog_no_snapshot.patch
│   ├── N08_split_no_revalidation.patch
│   ├── N09_stdlib_canonical.patch
│   └── N11_provenance_no_state_check.patch
├── experiments.json                  # Machine-readable experiment metadata and prototype dispositions
├── measurement_matrix.json           # Declarative specification of 18 workloads and scales
├── performance_summary.json          # Machine-readable timing distributions (medians, ranges, stdev)
├── resources_summary.json            # Tracemalloc peaks, RSS, and cProfile call summaries
├── focused_summary.json              # Focused benchmark distributions (14 triples)
├── imports_summary.json              # Fresh-process import timing distributions (24 processes)
├── independent_summary.json          # Independent QA test suite results and 30 fresh triples
├── recorded_audit_result.json        # Checkpoint audit verification outputs and hashes
├── retained_adverse_history.json     # Preserved noisy attempts, historical runtime hashes, and notes
├── provenance.json                   # Checkpoint manifests, file hashes, and environment facts
└── scripts/
    ├── workload.py.txt               # Standalone workload execution harness (text archive)
    ├── wire.py.txt                   # Serialization and input construction helpers (text archive)
    ├── compare.py.txt                # Output normalizer and assertion comparator (text archive)
    └── fresh_imports.py.txt          # Fresh-process import timing harness (text archive)
```

> [!IMPORTANT]
> **Compact Publication Package vs Full Raw Runs:**  
> The publication evidence package contains all declarative matrices, summary statistics, environment provenance, counterfactual patches, and harness archives (2,542,126 payload bytes). It does not contain full raw multi-megabyte process execution directories; full raw run archives remain preserved locally. The `.txt` files in `scripts/` are byte-preserved documentation archives of the repair scripts (`repair_b2/scripts/`), not installed runtime packages within `src/`.

### 10.2 B1 Runtime Reconstruction Protocol
B1 can be reconstructed for benchmark runtime comparison by:
1. Copying a trusted checkout of the candidate tree into an isolated scratch directory.
2. Reversing `b1_to_b2_diagnostics.patch` on that scratch copy (`patch -p1 -R < b1_to_b2_diagnostics.patch`).
3. Verifying that the resulting six runtime source file SHA-256 hashes match published B1 provenance in `provenance.json`:
   - `src/backtest/metrics.py`: `e2029fcdfff1129296d846a27b4db538dc3fb1bb277e0b72faeffc0e257d4435`
   - `src/backtest/portfolio.py`: `f2feced809ec4607c95b8d0f9a8ea5ad663e0d7de57f484536ffe3907e815912`
   - `src/campaign/runner.py`: `7cbf97260b027bf50db914065096c871c161a7221cd8787942dd43c94674197f`
   - `src/features/diagnostics.py`: `21450364d03f2e7c6a6b62df4d9d6fd8b272aefe62b37aba49125713c19a77a3`
   - `src/features/validation.py`: `a24f0254b5248408506770844e737a8de748a182e5ea69f4cbe52e9e907b04a9`
   - `src/ledger/schema_registry.py`: `9c20b9a5f97905f3a82d0bd4f432f8e65dc2dccd9bd02ad4d08837b0f2e91330`
This represents a **B1 runtime reconstruction**, distinct from the sealed 447-file B1 checkpoint. Baseline uses the named clean baseline commit `6ee193c9bb43f8290b3e09396fd241fec32df695`. No B1 commit hash is invented.

### 10.3 Step-by-Step Bounded Smoke / Replay Protocol
A reader wishing to independently execute a bounded smoke or replay check across baseline, B1 runtime reconstruction, and B2 candidate should follow this protocol:

1. **Trusted Source Checkouts (Without Copying `.git`):**
   - **Baseline Checkout:** Export clean baseline commit `6ee193c9bb43f8290b3e09396fd241fec32df695` via `git archive 6ee193c9bb43f8290b3e09396fd241fec32df695` to `/path/to/baseline_checkout`.
   - **B2 Candidate Checkout:** Export the published/checked-out PR commit via `git archive HEAD` from the trusted final checkout root to `/path/to/b2_checkout`, and verify that the six B2 source hashes match `provenance.json` (source manifest `fdfd4d7c...`, review candidate content identity `3e0062...`).
   - **B1 Runtime Reconstruction:** Copy the trusted B2 checkout without `.git` to `/path/to/b1_reconstructed`, apply `patch -p1 -R < b1_to_b2_diagnostics.patch`, and verify that the six runtime file hashes match the table in Section 10.2 (never an invented B1 commit).
2. **Environment & Scratch Preparation:**
   - Establish an isolated Python 3.12 virtual environment (`/path/to/scratch/venv`) and install reader dependencies from project metadata (`pip install .` plus testing/linting metadata: `pytest 9.1.1`, `ruff 0.16.6`). Explicitly select the absolute Python interpreter (`/path/to/scratch/venv/bin/python`).
   - Create an isolated scratch directory containing dedicated subdirectories for `HOME`, `TMPDIR`, and all `XDG_*` paths (`XDG_CACHE_HOME`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_STATE_HOME`).
   - Create dedicated subdirectories for harness scripts (`/path/to/scratch/harness/`), attempt runs (`/path/to/scratch/runs/`), and comparisons (`/path/to/scratch/comparisons/`).
   - Copy `workload.py.txt`, `wire.py.txt`, and `compare.py.txt` into `/path/to/scratch/harness/`, renaming them with `.py` extensions. Because `compare.py` resolves run directories as `Path(__file__).resolve().parents[1] / "runs" / attempt`, situating `compare.py` in `<scratch>/harness/` correctly resolves `<scratch>/runs/<attempt>`.
3. **Execution Instructions (Bounded Three-Source Invocations):**
   - `workload.py` reads `candidate = Path.cwd()`, so the caller must `cd` into the respective checkout root before invocation.
   - `workload.py` takes no `--output-dir` flag; the output path is set exclusively via `EFR_PHASE_B2_RUN`, which must point to an existing unique directory per process under `/path/to/scratch/runs/`.
   - In `--mode measure`, the script runs one unprofiled warmup iteration (logged and excluded from timing samples) followed by one timed measurement. In `--mode replay`, it executes a single run without warmup.
   - Example single-workload execution for `diagnostics` (504 rows, 100 assets):
     ```bash
     # Common environment controls
     export HOME="/path/to/scratch/home"
     export TMPDIR="/path/to/scratch/tmp"
     export XDG_CACHE_HOME="/path/to/scratch/xdg/cache"
     export XDG_CONFIG_HOME="/path/to/scratch/xdg/config"
     export XDG_DATA_HOME="/path/to/scratch/xdg/data"
     export XDG_STATE_HOME="/path/to/scratch/xdg/state"
     mkdir -p "$HOME" "$TMPDIR" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_STATE_HOME"
     export PYTHONDONTWRITEBYTECODE=1
     export OMP_NUM_THREADS=1
     export OPENBLAS_NUM_THREADS=1
     export MKL_NUM_THREADS=1
     export VECLIB_MAXIMUM_THREADS=1
     export NUMEXPR_NUM_THREADS=1

     # Step 3a: Run Baseline
     cd /path/to/baseline_checkout
     export PYTHONPATH="/path/to/baseline_checkout/src:/path/to/baseline_checkout:/path/to/baseline_checkout/tests:/path/to/scratch/harness"
     export EFR_PHASE_B2_RUN="/path/to/scratch/runs/run_baseline_diagnostics"
     mkdir -p "$EFR_PHASE_B2_RUN"
     /path/to/scratch/venv/bin/python /path/to/scratch/harness/workload.py diagnostics --rows 504 --assets 100 --mode measure

     # Step 3b: Run B1 Runtime Reconstruction
     cd /path/to/b1_reconstructed
     export PYTHONPATH="/path/to/b1_reconstructed/src:/path/to/b1_reconstructed:/path/to/b1_reconstructed/tests:/path/to/scratch/harness"
     export EFR_PHASE_B2_RUN="/path/to/scratch/runs/run_b1_diagnostics"
     mkdir -p "$EFR_PHASE_B2_RUN"
     /path/to/scratch/venv/bin/python /path/to/scratch/harness/workload.py diagnostics --rows 504 --assets 100 --mode measure

     # Step 3c: Run B2 Candidate
     cd /path/to/b2_checkout
     export PYTHONPATH="/path/to/b2_checkout/src:/path/to/b2_checkout:/path/to/b2_checkout/tests:/path/to/scratch/harness"
     export EFR_PHASE_B2_RUN="/path/to/scratch/runs/run_b2_diagnostics"
     mkdir -p "$EFR_PHASE_B2_RUN"
     /path/to/scratch/venv/bin/python /path/to/scratch/harness/workload.py diagnostics --rows 504 --assets 100 --mode measure
     ```
4. **Verification via `compare.py` / `compare_attempts` (All Three Pair Comparisons):**
   - The standalone comparator script `compare.py` accepts two positional arguments: `baseline` and `candidate`.
   - By implementation design (`B2 = Path(__file__).resolve().parents[1]`), `compare.py` expects run directories situated at `<scratch>/runs/<attempt_name>`, reading `<scratch>/runs/<attempt_name>/summary.json` and the output directory's `normalized_result.json.gz`.
   - `compare.py` writes `comparison.json` to the directory specified by `os.environ["EFR_PHASE_B2_RUN"]` and prints output JSON to stdout.
   - Run all three pair comparisons with separate comparison output directories:
     ```bash
     # Pair 1: Baseline vs B1
     export EFR_PHASE_B2_RUN="/path/to/scratch/comparisons/comp_baseline_vs_b1"
     mkdir -p "$EFR_PHASE_B2_RUN"
     /path/to/scratch/venv/bin/python /path/to/scratch/harness/compare.py run_baseline_diagnostics run_b1_diagnostics

     # Pair 2: Baseline vs B2
     export EFR_PHASE_B2_RUN="/path/to/scratch/comparisons/comp_baseline_vs_b2"
     mkdir -p "$EFR_PHASE_B2_RUN"
     /path/to/scratch/venv/bin/python /path/to/scratch/harness/compare.py run_baseline_diagnostics run_b2_diagnostics

     # Pair 3: B1 vs B2
     export EFR_PHASE_B2_RUN="/path/to/scratch/comparisons/comp_b1_vs_b2"
     mkdir -p "$EFR_PHASE_B2_RUN"
     /path/to/scratch/venv/bin/python /path/to/scratch/harness/compare.py run_b1_diagnostics run_b2_diagnostics
     ```
   - Alternatively, it can be called directly within Python:
     ```python
     from compare import compare_attempts
     res_base_b1 = compare_attempts("run_baseline_diagnostics", "run_b1_diagnostics")
     res_base_b2 = compare_attempts("run_baseline_diagnostics", "run_b2_diagnostics")
     res_b1_b2   = compare_attempts("run_b1_diagnostics", "run_b2_diagnostics")
     assert res_base_b1["pass"] and res_base_b2["pass"] and res_b1_b2["pass"]
     ```
   - It asserts exact byte-for-byte matching of normalized results across all workloads, with the sole exception of `diagnostics`, where it verifies that Pearson correlation and metadata are exact and Spearman Rank IC errors remain within absolute `1e-12`.
5. **General Benchmark Protocol & Security Boundaries:**
   - *Full Matrix Protocol:* The full producer matrix evaluated 7 rotating and reversed matched triples across all 18 cases in fresh subprocesses, plus separate profile, memory, and fresh-import cohorts. A single smoke run verifies execution parity and timing mechanics on one scope; it does not replace the full 126-triple matrix.
   - *Documentation-Only Protocol:* This documentation describes reproduction commands for independent reviewers; no code execution or environment installation is performed during prose drafting.
   - *Pickle Security Policy:* The harness uses `pickle` strictly to serialize and compare locally generated synthetic execution outputs. **Never load external or untrusted pickle files.**
   - *Platform RSS Units:* Peak RSS is captured via Python's `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss`. On macOS, this value is reported in **bytes**; on Linux, it is reported in **kibibytes (KiB)**. Replicators on Linux must multiply by 1,024 to compare with macOS byte values.

---

## 11. Review Status & Final Gate Clearances

### 11.1 Eligible B2 Static Reviews (Complete)
In accordance with governance controls, three mutually blind, distinct-model sessions completed bounded static reviews of the frozen B2 implementation candidate (`3e006260...`):
- **GPT-6-Astra** (medium effort, normal/default service tier): Coverage complete; 0 Material findings, 1 Advisory.
- **Grok-4.6** (xhigh effort): Coverage complete; 0 Material findings, 2 Advisories.
- **Gemini-3.8-Flash** (high effort): Coverage complete; 0 Material findings, 0 Advisories.

A prior Gemini session was excluded for an explicit prohibited native self-transcript read-boundary violation (metadata-only return, no peer-text exposure); it is preserved in `coord/agy_b2_exclusion.json` as history and does not count toward the gate.

### 11.2 Open Advisories Preserved
Three advisories remain formally **OPEN** and are preserved without dismissal:
1. `B2-GPT-ADD-001`: Original independent campaign single triple recorded B2 wall 1.558791s vs B1 1.407054s (about +10.8% slower), with corresponding CPU increase (1.557491s vs 1.405663s; baseline 18.091250s). Recurrence and underlying cause remain unresolved. A separate repeated independent campaign cohort is required during final integration QA before any unqualified preservation claim. It has not run.
2. `ADVISORY-B2-GROK-001`: Preserves fixture matrix002 pair 4, where B2 is 0.897ms slower than baseline; 7/7 B1 improvement and favorable medians do not erase this pair. The historical conditional tiny-fixture fallback was not exercised and does not authorize new regressions.
3. `ADVISORY-B2-GROK-002`: Preserves all B1-to-B2 slower-pair counts, medians, and allocation/RSS tradeoffs. Overlapping sample ranges and large baseline gains do not prove no B1 regression.

### 11.3 Explicit Implementation Acceptance & Pending Integration Gates
- **Implementation Acceptance:** **ACCEPTED_FOR_INTEGRATION.** The coordinator formally accepted exact review candidate `3e006260952521eac66b62dcaf4527fc867e453e04b8fbd7af180ea1e4a95392` (source manifest `fdfd4d7c8533bd6190171fa679ac4acc52a61ca6cb504427c92e9d3a932a28ac`, 448 files) as the implementation input to controlled integration under accepted binding plan A2 (`coord/decision_implementation_b2.md`). Baseline remains `6ee193c9bb43f8290b3e09396fd241fec32df695`.
- **Next Authorized Integration Gate:** Integration will be executed by a fresh GENERAL_EXEC integrator in a separate clean worktree/branch, consuming accepted B2 source and checked documentation/evidence inputs. Integration creates a fresh candidate requiring:
  1. Final integration QA including the separate repeated campaign cohort;
  2. Independent smoke execution of documented reproduction commands;
  3. Fresh static reviews of the final exact integration candidate;
  4. Local latest/high normal Codex PR review;
  5. Cross-platform Linux / Python 3.11 runtime continuous integration.
- **Current State:** No integration, repeated cohort, final-head review, commit, push, or publication has occurred at this checkpoint. Later final integration facts will receive a separate update.
- **Owner Authorization Status:** The owner has authorized a separate branch/PR after the required gates; merge, auto-merge, deployment and main pushes are not authorized.

---

*This concludes the durable technical summary for Round 2 Whole-Codebase Ablation.*
