# Roadmap-Code Conformance Audit

Date: 2026-07-01

## 1. Executive Summary

Overall verdict: mostly aligned.

The repository implementation generally matches the intended research plan: factor helpers, strict local CSV loaders, diagnostics, local fixture workflows, synthetic backtest scaffolding, EODHD private-output runners, and LEAN guardrails all preserve the stated no-live-trading and no-performance-claim boundary. The main drift is documentation freshness, not code behavior. Several older roadmap and handoff documents still describe completed work as future or active, while newer checkpoint docs and tests show the work has landed. The biggest conformance risk is that a future continuation could follow stale handoff/roadmap text and repeat or mis-sequence work.

## Main-Line Divergence Verdict

The current codebase is aligned with the intended main line for a local, auditable, research-only equity-factor pipeline. The aligned parts are the factor helper layer, strict local CSV loading, split-aware diagnostics, synthetic/local-fixture workflows, simulated long-only backtester accounting, private EODHD diagnostic guardrails, and non-executing LEAN scaffold. These match the project objective and non-goals in `PROJECT_SPEC.md:3-18`, `PROJECT_SPEC.md:28-47`, and `PROJECT_SPEC.md:89-98`.

The drift is concentrated in documentation chronology. The docs most likely to mislead a future Codex session are `docs/current_handoff.md`, `docs/current_roadmap_gap_refresh.md`, `docs/factor_normalization_roadmap.md`, `docs/csv_data_interface_plan.md`, and older volume-aware slippage design/test-plan docs. They can make completed work look future, make active work look incomplete, or hide the distinction between private diagnostics and broader research interpretation.

Code areas ahead of older roadmap text include normalization, combination, factor diagnostics, CSV loaders, volume-aware precomputed slippage accounting, and private EODHD IC/Rank IC/quantile-spread diagnostics. Roadmap, spec, or public-doc claims ahead of code include portfolio-level risk constraints, exposure concentration metrics, fully accepted real-data methodology, point-in-time universe policy, accepted EODHD adjustment policy, plotting-helper capability, and runnable LEAN implementation.

This revision also includes `EXPERIMENT_LOG.md` as an experiment-record source of truth. It confirms that synthetic JSON sidecar logs and the synthetic registry exist, while full local CSV or EODHD experiment interpretation still requires provenance, adjustment, benchmark, sample-split, cost/slippage, limitations, and failure-mode records before metrics are treated as evidence.

## 2. Current Repository State

| Item | Evidence |
| --- | --- |
| Branch | `codex/roadmap-code-conformance-audit` |
| Base commit | `45fea65` (`Merge pull request #129 from minqiyang/codex/improve-readme`) |
| Upstream checked | `origin/main` matched `HEAD` at `45fea65` before branch creation |
| Open PR gate | `gh pr list --state open` returned `[]` |
| Pre-existing local edit | `AGENTS.md` was already modified in the worktree before this audit branch; it is not part of this audit report commit |
| Validation | See Appendix command summary |

## 3. Source-of-Truth Files Inspected

- `AGENTS.md` from `HEAD`, especially startup, review, PR, strict-prohibition, and date-alignment rules (`AGENTS.md:5-131`).
- `README.md`, including current status, limitations, validation commands, research integrity, and roadmap (`README.md:25-158`).
- `EXPERIMENT_LOG.md`, including synthetic-log caveats, local CSV experiment-record requirements, provenance, alignment, benchmark, sample split, cost/slippage, and failure-mode requirements (`EXPERIMENT_LOG.md:1-73`).
- `PROJECT_SPEC.md`, including project objective, universe assumptions, factor ideas, leakage rules, evaluation metrics, transaction-cost/slippage assumptions, phases, and non-goals (`PROJECT_SPEC.md:3-98`).
- `docs/current_handoff.md`, current EODHD handoff state (`docs/current_handoff.md:1-26`).
- `docs/current_roadmap_gap_refresh.md`, current roadmap inventory and recommended next roadmap (`docs/current_roadmap_gap_refresh.md:39-132`).
- `docs/factor_normalization_roadmap.md`, original normalization/combination roadmap (`docs/factor_normalization_roadmap.md:1-82`).
- `docs/csv_data_interface_plan.md`, local CSV design plan (`docs/csv_data_interface_plan.md:1-184`).
- `docs/decision_log.md`, especially EODHD private-output decisions and local CSV readiness boundary decisions.
- `docs/engineering_log.md`, especially the current implementation history for CSV, diagnostics, LEAN, and EODHD stages.
- `docs/eodhd_*` checkpoint and handoff docs for private-data policy and current EODHD stages.
- `docs/quantconnect_lean_plan.md`, `lean/README.md`, and LEAN static tests.
- `docs/repo_map.md`, `CHANGELOG.md`, `pyproject.toml`, `.github/workflows/ci.yml`, `src/`, `research/`, `tests/`, `scripts/`, `reports/`, and `lean/`.

## From-Start-To-Current Coverage Checklist

| Source-of-truth source | Coverage result | Produced traceability rows? |
| --- | --- | --- |
| `AGENTS.md` | Inspected from `HEAD`; local unstaged user edit was intentionally not used as committed source of truth. | Yes: governance, no-secrets, current handoff priority, review discipline. |
| `README.md` | Inspected for public claims, status, limitations, validation, research integrity, and roadmap. | Yes: README capability claims, validation commands, public-data/private-data boundary. |
| `EXPERIMENT_LOG.md` | Inspected for required experiment provenance, validation, adjustment, universe, timing, sample-split, benchmark, cost/slippage, limitation, and failure-mode records before local CSV or EODHD results are interpreted. | Yes: experiment-record gate, synthetic-registry boundary, EODHD/private-data interpretation boundary, reporting helper traceability. |
| `PROJECT_SPEC.md` | Inspected from project objective through phases and non-goals. | Yes: main-line verdict, backtester alignment, risk/evaluation gap, LEAN future path. |
| `docs/current_handoff.md` | Inspected as the latest active handoff file. | Yes: stale handoff finding. |
| `docs/STAGE_PLAN.md` | Not present. Roadmap equivalents were inspected instead. | No direct row; absence recorded as no file. |
| `docs/current_roadmap_gap_refresh.md` | Inspected for current roadmap inventory and recommended next stages. | Yes: stale roadmap, EODHD diagnostics drift, implemented feature status. |
| `docs/decision_log.md` | Inspected for accepted decisions around EODHD, local CSV readiness, PR gates, and protected merge policy. | Yes: EODHD private-output boundary and non-interpretive diagnostics. |
| `docs/engineering_log.md` | Targeted inspection for implementation history across CSV, diagnostics, LEAN, slippage, and staged checkpoints. | Yes: implementation chronology and stale older-doc context. |
| `docs/repo_map.md` | Inspected for current map, validation commands, and output discipline. | Yes: repo-map freshness finding and implementation inventory. |
| `CHANGELOG.md` | Inspected for chronological added features and EODHD entries. | Yes: implementation chronology cross-check. |
| EODHD checkpoint/handoff docs | All `docs/eodhd_*` checkpoint and handoff files were inventoried; current EODHD diagnostic docs were inspected in detail. | Yes: EODHD validation, private diagnostics, and interpretation-boundary rows. |
| Roadmap/design equivalents | Inspected roadmap and plan files including normalization, CSV, liquidity, slippage, synthetic robustness, and LEAN plans. | Yes: stale roadmap/design rows and future-gaps rows. |
| `pyproject.toml`, CI, scripts | Inspected package metadata, CI validation workflow, and repo tooling. | Yes: validation/inventory rows. |
| `src/`, `research/`, `tests/`, `scripts/`, `lean/` | Inventoried by file list and targeted code/test evidence. | Yes: implementation inventory and traceability rows. |
| `reports/` and private-data policy | Reports inventoried as committed synthetic/fixture outputs; private data not opened. | Yes: generated-output/private-data boundary rows. |

## 4. Roadmap Inventory

| Roadmap or checkpoint item | Intended behavior | Evidence |
| --- | --- | --- |
| Main project objective | Build a rigorous, reproducible, auditable local Python pipeline for simulated cross-sectional equity factor research, prioritizing correctness and assumptions over returns. | `PROJECT_SPEC.md:3-8` |
| Data leakage and availability | Use only information available before portfolio formation; preserve alignment; lag features when needed; document data availability and execution timing. | `PROJECT_SPEC.md:28-47` |
| Evaluation metrics and risk outputs | Metrics may include return, volatility, Sharpe when appropriate, drawdown, benchmark-relative return, tracking error/active risk, holdings, exposure concentration, and cost impact, but only as simulated research output. | `PROJECT_SPEC.md:49-64` |
| Governance and audit discipline | Use handoff/repo map first, preserve date alignment, caveats, tests, and no-secrets rules. | `AGENTS.md:5-36`, `AGENTS.md:104-122`, `docs/repo_map.md:25-53` |
| Train/validation/test splits | Chronological split helpers and split slicing for factor panels. | `docs/current_roadmap_gap_refresh.md:49`, `src/features/validation.py:45-119`, `tests/test_validation.py:30-216` |
| Factor features | Momentum, reversal, volatility, liquidity, Alpha#009, Alpha#012 as research features. | `docs/current_roadmap_gap_refresh.md:66`, `src/features/`, `tests/test_momentum.py`, `tests/test_reversal.py`, `tests/test_volatility.py`, `tests/test_liquidity.py`, `tests/test_worldquant_alphas.py` |
| Factor normalization | Row-wise z-score, rank, percentile-rank, and winsorization without hidden filling or lagging. | `docs/factor_normalization_roadmap.md:24-48`, `src/features/normalize.py:20-153`, `tests/test_normalize.py:24-367` |
| Factor combination | Combine aligned normalized factors only after explicit weights and missing-value policy. | `docs/factor_normalization_roadmap.md:50-62`, `src/features/combine.py:18-101`, `tests/test_combine.py:19-202` |
| Factor diagnostics | Correlation, IC, Rank IC, and quantile spread as diagnostics, not performance proof. | `docs/current_roadmap_gap_refresh.md:67`, `src/features/diagnostics.py:103-235`, `tests/test_diagnostics.py:195-524` |
| Local CSV interface | Local-only loaders, strict schema/date/numeric validation, no remote/vendor access. | `docs/csv_data_interface_plan.md:21-31`, `src/data/csv_loader.py:68-307`, `tests/test_csv_loader.py:29-382` |
| Local CSV inventory | Metadata-only review that records redacted declarations, not file contents or secrets. | `src/data/local_csv_inventory.py:90-230`, `tests/test_local_csv_inventory.py` |
| Liquidity universe | Lagged volume/dollar-volume eligibility, universe masks, and masked signals before backtest use. | `docs/current_roadmap_gap_refresh.md:55`, `src/features/liquidity.py:91-285`, `tests/test_liquidity.py:45-260` |
| Fixed costs and fixed-bps slippage | Simulated target-weight turnover costs and separate slippage fields. | `docs/current_roadmap_gap_refresh.md:56`, `src/backtest/portfolio.py:93-113`, `tests/test_backtest_portfolio.py:83-158` |
| Volume-aware slippage | Diagnostic-only by default; applied path must use explicit precomputed impact and metadata. | `docs/post_precomputed_volume_aware_slippage_checkpoint.md:25-49`, `src/backtest/portfolio.py:100-103`, `tests/test_backtest_portfolio.py:160-360` |
| Experiment records | Every meaningful experiment, including failed or inconclusive runs, must be recorded; local CSV interpretation requires provenance, schema, adjustment, universe, signal timing, sample splits, benchmark, cost/slippage, limitations, and failure-mode entries. | `EXPERIMENT_LOG.md:3-73`, `reports/experiment_registry.md:1-24` |
| Synthetic reports and logs | Deterministic, caveated synthetic outputs and experiment registry. | `README.md:97-116`, `src/reporting/experiment_log.py:47-94`, `src/reporting/experiment_registry.py:67-118`, `reports/experiment_registry.md` |
| EODHD validation bundle | Private local bundle outside repo, aggregate-only repo docs, no strategy/performance interpretation. | `docs/eodhd_local_csv_validation_handoff.md:5-50`, `docs/eodhd_data_quality_diagnostics_checkpoint.md:5-76` |
| EODHD factor diagnostics | Private-output factor diagnostics only, with readiness/review/brief stages and no performance claims. | `docs/eodhd_factor_diagnostics_dry_run_checkpoint.md:5-61`, `docs/eodhd_limited_factor_diagnostics_brief_checkpoint.md:5-77`, `research/eodhd_*`, `tests/test_eodhd_*` |
| LEAN path | Planning/scaffold only, no runtime algorithm, no orders, no brokerage, no live or paper trading. | `docs/quantconnect_lean_plan.md:3-18`, `lean/README.md:4-81`, `tests/test_lean_smoke_test_scope.py:40-108`, `tests/test_lean_signal_only_draft_scope.py:60-153` |

## 5. Implementation Inventory

| Area | Actual implementation |
| --- | --- |
| Source modules | `src/features/` has operators, validation, normalization, combination, diagnostics, liquidity, momentum, reversal, volatility, and WorldQuant examples; `src/backtest/` has portfolio, metrics, and slippage; `src/data/` has CSV loaders and inventory; `src/reporting/` has experiment log/registry helpers, while `src/reporting/plots.py` is placeholder-only and not implemented plotting functionality; `src/risk/` currently has only a constraints placeholder, not implemented portfolio-level risk constraints. |
| Research scripts | `research/` contains synthetic demos, local CSV fixture workflow, EODHD dry-run/log/readiness/review/brief runners, and split robustness workflows. |
| Tests | `tests/` includes deterministic unit, integration, fixture, private-runner, generated-output, and LEAN-scope tests. There is no portfolio-level `src/risk/constraints.py` behavior test beyond project-structure import/docstring coverage because the module is still placeholder-only. |
| CI | `.github/workflows/ci.yml` installs `.[dev]`, runs `python -m pytest -q`, `python -m compileall src tests research`, and `python -m compileall lean`. |
| Generated output policy | `reports/` contains committed synthetic or fixture reports/logs; EODHD private outputs stay under `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run`. |
| Package metadata | `pyproject.toml` requires Python `>=3.11` and declares `numpy`, `pandas`, `matplotlib`, `scipy`, and dev `pytest`. |
| Scripts | `scripts/repo_map.py` rewrites only `docs/repo_map.md` and skips generated reports/cache directories; `scripts/audit-skills.ps1` audits local Skill frontmatter/fences. |
| LEAN scaffold | `lean/` contains metadata-only scaffold/draft files and a README with no runtime LEAN dependency, no orders, no brokerage, and no performance claim. |

## 6. Traceability Matrix

| Roadmap item | Intended behavior | Evidence in docs | Evidence in code | Evidence in tests | Status | Drift severity | Recommended action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Governance and no-secrets rules | Preserve audit trail, tests, caveats, no secrets. | `AGENTS.md:23-36`, `AGENTS.md:104-115` | No secret-reading code in inspected source; EODHD output paths are private-only. | Private-runner tests use `tmp_path` and reject repo output paths, for example `tests/test_eodhd_factor_diagnostics_experiment_log.py:122-126`. | Implemented and tested | None | Keep current rules. |
| Experiment records and provenance gate | Record every meaningful experiment, including failed or inconclusive runs; require provenance, schema, validation, adjustment policy, universe rules, signal timing, sample splits, benchmark, costs/slippage, limitations, and failure modes before local CSV or EODHD metrics are interpreted. | `EXPERIMENT_LOG.md:3-73`, `reports/experiment_registry.md:1-24`, EODHD checkpoint docs keep private diagnostics non-interpretive. | `src/reporting/experiment_log.py:47-94` writes deterministic synthetic logs; `src/reporting/experiment_registry.py:67-118` loads and writes the synthetic registry; EODHD experiment-log runners write private bundle outputs. | `tests/test_experiment_log.py`, `tests/test_experiment_registry.py`, `tests/test_eodhd_factor_diagnostics_experiment_log.py:12-127`. | Partially aligned: synthetic and private-runner logging paths exist, but full local CSV/EODHD interpretation still requires explicit experiment records before use as evidence. | P2 interpretation-control gap | Keep `EXPERIMENT_LOG.md` in the source-of-truth set; future local CSV/EODHD interpretation PRs must verify required experiment-record fields before discussing metrics. |
| Split helpers | Chronological train/validation/test split without filling. | `docs/current_roadmap_gap_refresh.md:49` | `src/features/validation.py:45-119` | `tests/test_validation.py:30-216` | Implemented and tested | None | None. |
| Factor construction | Research features only, no strategy claim. | `docs/current_roadmap_gap_refresh.md:66` | `src/features/worldquant_alphas.py:16-136` plus momentum/reversal/volatility/liquidity modules | Feature tests plus static no-trading import checks | Implemented and tested | None | None. |
| Normalization | Row-wise normalization, no hidden filling or future use. | `docs/factor_normalization_roadmap.md:24-48` | `src/features/normalize.py:20-153` | `tests/test_normalize.py:100-115` proves future-row edits do not change current row. | Implemented and tested | P2 stale docs | Mark original roadmap as implemented/superseded in a follow-up docs PR. |
| Factor combination | Combine aligned factor panels with explicit weights. | `docs/factor_normalization_roadmap.md:50-62` | `src/features/combine.py:18-101` | `tests/test_combine.py:19-202` | Implemented and tested | P2 stale docs | Update roadmap status, not code. |
| Diagnostics | IC/Rank IC/quantile spread only on aligned evaluation panels. | `docs/current_roadmap_gap_refresh.md:67` | `src/features/diagnostics.py:103-235` | `tests/test_diagnostics.py:237-404` | Implemented and tested | None | None. |
| CSV loaders | Local-only strict validation, no downloads/vendor API. | `docs/csv_data_interface_plan.md:21-31`, `docs/csv_data_interface_plan.md:105-129` | `src/data/csv_loader.py:68-307` | `tests/test_csv_loader.py:53-382` | Implemented and tested | P2 stale docs | Update older plan lines that still say the loader is future-only. |
| Liquidity universe | Lagged eligibility, visible low-coverage/missing counts, mask signals without filling. | `docs/current_roadmap_gap_refresh.md:55` | `src/features/liquidity.py:91-285` | `tests/test_liquidity.py:45-260` | Implemented and tested | None | None. |
| Backtester alignment | Use lagged signals, next-row returns, explicit costs/slippage/turnover. | `README.md:126-128`, `docs/current_roadmap_gap_refresh.md:70` | `src/backtest/portfolio.py:80-113`, `src/backtest/portfolio.py:131-171` | `tests/test_backtest_portfolio.py:32-158` | Implemented and tested | None | None. |
| Volume-aware slippage integration | Default diagnostic-only, explicit precomputed application path. | `docs/post_precomputed_volume_aware_slippage_checkpoint.md:25-49` | `src/backtest/portfolio.py:161-203` | `tests/test_backtest_portfolio.py:160-360`, `tests/test_volume_aware_slippage.py:19-258` | Implemented and tested | P2 stale docs | Add superseded note to older design/test-plan docs that describe this as future. |
| EODHD validation and diagnostics | Private outputs only, aggregate repo docs, no strategy/performance claims. | `docs/eodhd_local_csv_validation_handoff.md:24-50`, `docs/eodhd_limited_factor_diagnostics_brief_checkpoint.md:62-77` | `research/eodhd_*` runners write under bundle paths and guard forbidden interpretations. | `tests/test_eodhd_limited_factor_diagnostics_brief.py:124-152` and related EODHD tests | Implemented and tested using synthetic/temp files | P2 stale handoff | Refresh `docs/current_handoff.md` to match post-PR #127/#129 state. |
| EODHD IC/Rank IC/quantile-spread diagnostics drift | Roadmap text should distinguish still-blocked broad real-data interpretation from private diagnostic calculations that now exist. | `docs/current_roadmap_gap_refresh.md:81-86` says no real-data IC, Rank IC, quantile-spread, or train/validation/test interpretation has been completed; `docs/eodhd_factor_diagnostics_dry_run_checkpoint.md:33-40` records non-empty private diagnostic dates. | `research/eodhd_factor_diagnostics_dry_run.py:81` constructs forward returns, and `research/eodhd_factor_diagnostics_dry_run.py:175-220` computes private IC, Rank IC, and quantile-spread diagnostics. | EODHD private-runner tests cover aggregate output and guardrails. | Diagnostic calculations exist privately; broader research interpretation remains blocked | P2 stale docs | Add a docs-only status clarification or targeted grep/check preserving the distinction between private diagnostics and blocked research interpretation. |
| Risk constraints and evaluation-risk metrics | Project spec expects simulated portfolio metrics such as tracking error/active risk, exposure concentration, and cost impact to be explicit when relevant. | `PROJECT_SPEC.md:57-62` lists tracking error or active risk, turnover, average holdings, exposure concentration, and cost impact; metrics must remain simulated research output. | `src/risk/constraints.py:1-4` is a placeholder saying constraints will eventually contain position limits, liquidity screens, volatility filters, and exposure caps. | Existing tests cover backtest costs/turnover, but no portfolio-level risk constraints or exposure-metric implementation is evidenced by the placeholder module. | Placeholder / remaining gap | P2 implementation inventory drift | Clarify docs-only status now; future PR should add a scoped risk/exposure/evaluation-risk test plan before implementation. |
| Current handoff | Should identify latest active state and next safe stage. | `docs/current_handoff.md:8-15` still says PR #126 and active brief stage. | Brief runner exists in `research/eodhd_limited_factor_diagnostics_brief.py`; README and checkpoint reflect completed state. | `tests/test_eodhd_limited_factor_diagnostics_brief.py:124-152` | Implemented but docs differ from plan | P2 | Update handoff only in a dedicated docs PR. |
| README and repo-map reporting claims | Public docs should distinguish implemented experiment-log/registry helpers from placeholder plotting helpers. | `README.md:32` correctly limits implemented status to experiment-log and registry helpers, but `README.md:61` and `docs/repo_map.md:18` describe `src/reporting/` as having plotting helpers. | `src/reporting/experiment_log.py:47-94` and `src/reporting/experiment_registry.py:67-118` are implemented; `src/reporting/plots.py:1-5` is placeholder-only. | `tests/test_experiment_log.py` and `tests/test_experiment_registry.py` cover logging and registry behavior; `tests/test_project_structure.py:45-55` only imports `reporting.plots` and checks a docstring. | Partially aligned: reporting logs/registry are implemented, plotting helpers are not. | P2 placeholder docs drift | Use a docs-only README/repo-map clarification PR, or defer actual plotting to a future scoped implementation/test-plan PR. |
| LEAN path | Keep non-executing scaffold, no orders/brokerage/live trading. | `docs/quantconnect_lean_plan.md:3-18`, `lean/README.md:4-81` | `lean/smoke_test_algorithm.py`, `lean/signal_only_momentum_draft.py` are metadata/scaffold files. | `tests/test_lean_smoke_test_scope.py:40-108`, `tests/test_lean_signal_only_draft_scope.py:60-153` | Implemented as scaffold and tested | None | Keep LEAN non-execution boundary. |

## 7. Drift Findings

### P2-1: `docs/current_handoff.md` is stale after later merges

- Doc claim: `docs/current_handoff.md:8-10` says the last merged PR is #126 and the current stage is to add the private-output neutral diagnostics brief runner.
- Code/test evidence: `docs/eodhd_limited_factor_diagnostics_brief_checkpoint.md:5-14` records that the brief checkpoint was added, and `tests/test_eodhd_limited_factor_diagnostics_brief.py:124-152` validates the brief payload and guardrail fields. The repository head is also past PR #129.
- Mismatch: The handoff still describes completed work as active.
- Why it matters: Future staged continuations are instructed to read `docs/current_handoff.md` first, so stale active-stage guidance can send the next agent to duplicate or mis-sequence EODHD work.
- Recommended remediation: Refresh only `docs/current_handoff.md` with latest merged PR, current stage, next safe stage, and do-not-touch list.

### P2-2: Older roadmap gap text says no local CSV bundle passed readiness gates, but EODHD private validation has since passed validation-only gates

- Doc claim: `docs/current_roadmap_gap_refresh.md:68` and `docs/current_roadmap_gap_refresh.md:81-86` say no user-provided local CSV bundle has passed readiness/provenance/alignment review and no real benchmark/universe/adjustment policy has been accepted.
- Later doc evidence: `docs/eodhd_local_csv_validation_handoff.md:29-46` records a private EODHD validation-only dry run with symbol coverage, benchmark alignment, row counts, duplicate checks, and credential-marker scan results. `docs/eodhd_data_quality_diagnostics_checkpoint.md:28-68` adds later aggregate diagnostics and caveats.
- Mismatch: The older roadmap is no longer current for validation-only EODHD bundle status, although it remains right that broader interpretation is blocked.
- Why it matters: The stale wording can obscure the difference between "validated for local loader/schema diagnostics" and "accepted for broader real-data interpretation."
- Recommended remediation: Update the roadmap gap refresh to distinguish completed validation-only EODHD bundle checks from still-blocked research interpretation.

### P2-3: Original normalization/combination roadmap still frames implemented helpers as future work

- Doc claim: `docs/factor_normalization_roadmap.md:76-82` lists normalization helpers, combination helpers, factor correlation, and Alpha#009 smoke demo as future PRs.
- Code/test evidence: `src/features/normalize.py:20-153`, `src/features/combine.py:18-101`, and `src/features/diagnostics.py:103-235` implement those helper families; `tests/test_normalize.py:100-115`, `tests/test_combine.py:19-202`, and `tests/test_diagnostics.py:237-404` cover critical behavior.
- Mismatch: Older roadmap sequence is now obsolete but not marked as superseded.
- Why it matters: It can cause redundant planning or false assumptions that these foundations are missing.
- Recommended remediation: Add a short superseded-by note pointing to `docs/current_roadmap_gap_refresh.md` and current tests.

### P2-4: Older CSV interface plan still describes loaders as future-only, while strict loaders exist

- Doc claim: `docs/csv_data_interface_plan.md:5-8` and `docs/csv_data_interface_plan.md:105-108` describe the CSV interface and returned audit summary as future/non-implemented.
- Code/test evidence: `src/data/csv_loader.py:68-307` implements wide, long, benchmark, and OHLCV loaders with summaries; `tests/test_csv_loader.py:29-382` covers schema, path, date, numeric, duplicate, price, volume, OHLC, benchmark, and forbidden-import behavior.
- Mismatch: The plan was not updated after implementation.
- Why it matters: It understates current loader readiness and may cause future audit work to ignore already-tested helpers.
- Recommended remediation: Add a status header or successor pointer from the plan to the implemented loader and current readiness docs.

### P2-5: Older volume-aware slippage design/test-plan docs are partly superseded by the implemented precomputed-impact path

- Doc claim: `docs/volume_aware_slippage_backtester_integration_design.md:80-140` and `docs/volume_aware_slippage_backtester_integration_test_plan.md:45-99` discuss future precomputed-impact integration requirements.
- Later doc/code/test evidence: `docs/post_precomputed_volume_aware_slippage_checkpoint.md:25-49` says the sequence is complete through the precomputed-impact path; `src/backtest/portfolio.py:161-203` deducts an explicit impact series when `volume_aware_slippage_mode="apply_precomputed_impact"`; `tests/test_backtest_portfolio.py:189-360` covers applied impact and failure modes.
- Mismatch: The older docs remain useful design history, but they are not clearly marked as historical.
- Why it matters: Reviewers could mistake completed test-plan requirements for still-missing implementation work.
- Recommended remediation: Add superseded/history notes to older docs or link them from the post-checkpoint as design provenance.

### P2-6: EODHD factor diagnostics drift is separate from broader blocked research interpretation

- Doc claim: `docs/current_roadmap_gap_refresh.md:81-86` says no real-data IC, Rank IC, quantile-spread, benchmark-relative, or train/validation/test interpretation has been completed.
- Later doc/code evidence: `docs/eodhd_factor_diagnostics_dry_run_checkpoint.md:33-40` records non-empty private IC, Rank IC, and quantile-spread diagnostic dates, while `research/eodhd_factor_diagnostics_dry_run.py:81` builds forward returns and `research/eodhd_factor_diagnostics_dry_run.py:175-220` computes private IC, Rank IC, and quantile-spread diagnostics by split.
- Mismatch: The older roadmap wording is too broad if read as saying no private diagnostic calculations exist; it remains correct only for broader research interpretation, accepted benchmark/universe/adjustment policy, and performance-use readiness.
- Why it matters: A future remediation that updates only validation-bundle readiness could still miss the stronger roadmap-code drift around private diagnostic evidence, or could overcorrect by implying the diagnostics support investment interpretation.
- Recommended remediation: Add a docs-only clarification and, if useful, a targeted grep/check that keeps "private diagnostics exist" separate from "real-data research interpretation remains blocked."

### P2-7: Risk constraints are placeholders, not implemented portfolio-level constraints

- Doc/spec claim: `PROJECT_SPEC.md:57-62` lists evaluation-risk outputs such as tracking error or active risk, exposure concentration, cost impact, turnover, and average holdings when relevant.
- Code evidence: `src/risk/constraints.py:1-4` is only a placeholder saying portfolio-level constraints such as position limits, liquidity screens, volatility filters, and exposure caps will eventually exist.
- Mismatch: The implementation inventory previously listed `src/risk/` as having constraints, which could be read as implemented risk/exposure controls.
- Why it matters: Readers could assume portfolio-level constraints or exposure-risk metrics are available when the file evidence shows a remaining gap.
- Recommended remediation: Keep this audit docs-only, mark the module as placeholder, and plan a future scoped risk/exposure/evaluation-risk test plan before any implementation.

### P2-8: Project-spec evaluation metrics are only partially implemented

- Spec claim: `PROJECT_SPEC.md:49-64` lists total return, annualized return, annualized volatility, Sharpe when appropriate, maximum drawdown, benchmark-relative return, tracking error or active risk if relevant, hit rate and holding-period return if relevant, turnover, average holdings, exposure concentration, and cost impact.
- Code/test evidence: `src/backtest/metrics.py` implements basic return, volatility, Sharpe-style, drawdown, benchmark-relative, turnover, and cost-impact metrics; `src/risk/constraints.py:1-4` remains a placeholder for exposure/risk controls. Existing tests cover basic backtester metrics and cost/turnover behavior, but no evidence shows implemented tracking error/active risk, hit rate, average holdings, or exposure concentration.
- Mismatch: Core simulated backtest metrics are present, but the broader spec list is not fully implemented and should not be described as complete.
- Why it matters: The roadmap/code audit should not let broad evaluation-language in the spec become an implied implementation claim.
- Recommended remediation: Add a future evaluation-metrics gap note or test plan before implementing missing risk/exposure metrics.

### P2-9: `EXPERIMENT_LOG.md` is a required interpretation gate for local CSV and EODHD metrics

- Doc claim: `EXPERIMENT_LOG.md:28-73` requires a full local CSV experiment record before results are interpreted, including source paths, schemas, validation summaries, provenance, adjustment policy, universe rules, feature/signal timing, sample splits, benchmark, costs/slippage, limitations, failure modes, and next action.
- Code/test evidence: `src/reporting/experiment_log.py:47-94` writes deterministic synthetic JSON sidecar logs, `src/reporting/experiment_registry.py:67-118` summarizes existing logs, and `tests/test_eodhd_factor_diagnostics_experiment_log.py:12-127` covers private EODHD experiment-log guardrails. `reports/experiment_registry.md:1-24` remains synthetic-only and explicitly says full experiment records are still required before real-data validation or parameter studies.
- Mismatch: Synthetic and private-runner logging paths exist, but local CSV/EODHD metrics are still not interpretable as research evidence unless the root experiment-log requirements are satisfied or explicitly deferred.
- Why it matters: A future docs remediation could overstate validation-only or private diagnostic status if it treats aggregate checkpoint docs as substitutes for full experiment provenance, sample-split, cost/slippage, benchmark, and failure-mode records.
- Recommended remediation: Keep `EXPERIMENT_LOG.md` in the source-of-truth inventory; future EODHD readiness or real-data interpretation docs must either cite an experiment-log entry or state that interpretation remains blocked.

### P2-10: README and repo map overstate reporting plotting-helper implementation

- Doc claim: `README.md:61` and `docs/repo_map.md:18` describe `src/reporting/` as containing plotting helpers.
- Code/test evidence: `src/reporting/experiment_log.py:47-94` and `src/reporting/experiment_registry.py:67-118` implement deterministic experiment-log and registry helpers, but `src/reporting/plots.py:1-5` is only a module docstring saying charts will eventually exist. `tests/test_project_structure.py:45-55` checks only that `reporting.plots` imports and has a docstring.
- Mismatch: Public docs can be read as saying plotting helpers exist, while the code only contains a placeholder module.
- Why it matters: This is a public capability claim, so future users or agents could rely on plotting functionality that is not implemented or tested.
- Recommended remediation: Use a docs-only README/repo-map clarification PR to distinguish implemented experiment-log/registry helpers from placeholder plotting helpers, or defer real plotting to a separately scoped implementation/test-plan PR.

### P3-1: Repo map has not been refreshed after the README/audit sequence

- Doc claim: `docs/repo_map.md:3-5` says it is generated by `python scripts/repo_map.py`.
- Current evidence: This audit adds a new docs file, so the existing repo map will not mention it until a future repo-map refresh.
- Mismatch: Expected generated-map staleness for this PR because the task only allowed adding the audit report.
- Recommended remediation: Refresh `docs/repo_map.md` in a separate workflow-control docs PR if desired.

## 8. Research-Integrity Alignment

- Look-ahead prevention: Mostly aligned. Backtester docs and implementation use lagged signals (`src/backtest/portfolio.py:80-85`, `src/backtest/portfolio.py:131-135`), and tests cover current rebalance not using future signals (`tests/test_backtest_portfolio.py:32-52`). Normalization tests show future-row edits do not change a prior row (`tests/test_normalize.py:100-115`).
- Leakage prevention: Mostly aligned. Diagnostics require pre-aligned forward returns as evaluation targets and explicitly do not calculate or shift returns (`src/features/diagnostics.py:110-116`, `src/features/diagnostics.py:189-195`). EODHD docs keep forward returns diagnostic-only (`docs/eodhd_factor_diagnostics_dry_run_checkpoint.md:46-55`).
- Signal lag: Aligned in backtester and liquidity helper defaults. `signal_lag_periods=1` is explicit (`src/backtest/portfolio.py:73-85`), and liquidity eligibility has an `eligibility_lag` default with timing language (`src/features/liquidity.py:91-105`).
- Rebalance/execution/return-window alignment: Mostly aligned for the local simulated backtester. The implementation uses rebalance dates, lagged signals, previous holdings, and next-row returns (`src/backtest/portfolio.py:131-171`). LEAN docs clearly warn that local close-to-close assumptions differ from platform fills (`docs/quantconnect_lean_plan.md:141-144`, `docs/quantconnect_lean_plan.md:208-219`).
- Benchmark alignment: Aligned for loaders and EODHD diagnostics. Benchmark loaders validate dates and values (`src/data/csv_loader.py:165-201`), private EODHD dry run validates benchmark dates (`research/eodhd_factor_diagnostics_dry_run.py:69-82`, `research/eodhd_factor_diagnostics_dry_run.py:134-136`), and docs keep benchmark usage scoped (`docs/eodhd_local_csv_validation_handoff.md:48-50`).
- Transaction costs and turnover: Aligned as simulated accounting, not execution realism. The backtester uses target-weight turnover and separate cost/slippage series (`src/backtest/portfolio.py:93-113`, `src/backtest/portfolio.py:155-171`), with tests for turnover, fixed costs, fixed slippage, and volume-aware impact (`tests/test_backtest_portfolio.py:83-232`).

## 9. Documentation Alignment

README claims are mostly aligned with code. It says the project has factor construction, signal timing, backtesting scaffold, diagnostics, tests, strict local CSV loaders, private EODHD guardrails, and no live trading (`README.md:17-52`), which matches the implementation and tests inspected. It also correctly states that private EODHD outputs remain outside the repository (`README.md:37-43`) and that unresolved issues include static universe, adjustment semantics, sample split, cost/slippage, and real-data methodology (`README.md:45-52`).

One public documentation drift remains: the current-status list correctly limits implemented `src/reporting/` work to experiment-log and registry helpers (`README.md:32`), but the repository map table in `README.md:61` and generated `docs/repo_map.md:18` also names plotting helpers. `src/reporting/plots.py:1-5` is placeholder-only, so plotting should be documented as future work until a scoped implementation and tests exist.

The main documentation drift is inside internal roadmap/handoff docs. `docs/current_handoff.md` is the highest-priority stale file because `AGENTS.md:7-10` says staged continuations should read it first. Older roadmap/design documents remain valuable historical evidence, but several need status/superseded notes so they do not conflict with newer checkpoint docs.

## 10. Test Alignment

Covered roadmap claims:

- Chronological splits and split panel slicing: `tests/test_validation.py`.
- No-look-ahead signal lag and backtest target-weight accounting: `tests/test_backtest_portfolio.py`.
- Row-wise normalization and future-row isolation: `tests/test_normalize.py`.
- Strict factor combination and alignment: `tests/test_combine.py`.
- IC, Rank IC, and quantile spread overlap/misalignment behavior: `tests/test_diagnostics.py`.
- Strict local CSV validation: `tests/test_csv_loader.py`.
- Liquidity eligibility, universe masks, and masked signals: `tests/test_liquidity.py`.
- Volume-aware slippage diagnostics and applied precomputed boundary: `tests/test_volume_aware_slippage.py`, `tests/test_backtest_portfolio.py`.
- Synthetic experiment-log and registry helpers: `tests/test_experiment_log.py`, `tests/test_experiment_registry.py`.
- EODHD private-runner guardrails and output-scope checks: `tests/test_eodhd_*`.
- LEAN non-execution scope: `tests/test_lean_smoke_test_scope.py`, `tests/test_lean_signal_only_draft_scope.py`.

Gaps or weak spots:

- Documentation freshness is not automatically tested; stale handoff/roadmap claims can persist after code merges.
- Repo map freshness is manual, so new docs can be absent until `python scripts/repo_map.py` is intentionally run.
- Real-data methodology choices remain intentionally unresolved: point-in-time universe, adjustment policy, benchmark methodology, sample split, cost/slippage assumptions, risk/exposure metrics, and interpretation policy.
- Full local CSV/EODHD interpretation remains blocked without experiment records satisfying `EXPERIMENT_LOG.md` requirements; synthetic JSON sidecar logs and registry reports are not substitutes.
- Evaluation-risk coverage is partial: backtest metrics exist for basic simulated accounting, but risk constraints, exposure concentration, tracking error/active risk, hit rate, and average-holdings metrics are not fully evidenced.
- Plotting-helper coverage is placeholder-only; tests currently prove import/docstring presence, not plotting behavior.

No tests appeared disconnected from the current roadmap. Some tests enforce behavior that older docs still describe as future, which is a documentation drift rather than a code/test drift.

## 11. Recommended Remediation Plan

1. Refresh current handoff.
   - Goal: make `docs/current_handoff.md` reflect PR #127/#129-era state and the next safe metadata/data-readiness checkpoint.
   - Files likely touched: `docs/current_handoff.md`, `CHANGELOG.md`, maybe `docs/repo_map.md` if regenerated.
   - Acceptance criteria: no active-stage text describes completed EODHD brief work as future; next safe stage is explicit; private-data/no-performance boundary remains.
   - Validation: `git diff --check`, `python -m pytest -q`, `python -m compileall src tests research`.

2. Add superseded/status notes to older roadmap docs.
   - Goal: mark `docs/factor_normalization_roadmap.md`, `docs/csv_data_interface_plan.md`, and older volume-aware slippage design/test-plan docs as historical where later implementation exists.
   - Files likely touched: those docs only.
   - Acceptance criteria: each stale future-work section points to current code/tests or successor checkpoint docs.
   - Validation: `git diff --check`.

3. Reconcile EODHD readiness and private diagnostics wording.
   - Goal: distinguish completed private validation-only EODHD bundle checks and private IC/Rank IC/quantile-spread diagnostics from still-blocked broader research interpretation.
   - Files likely touched: `docs/current_roadmap_gap_refresh.md`, possibly `docs/eodhd_local_csv_validation_handoff.md`.
   - Acceptance criteria: docs state validation-only and private-diagnostic status without implying accepted point-in-time universe, adjustment policy, strategy, backtest, performance readiness, or fulfilled `EXPERIMENT_LOG.md` interpretation records.
   - Validation: `git diff --check`, targeted grep for forbidden performance/trading claims.

4. Clarify README/reporting plotting-helper placeholder status.
   - Goal: make public-facing docs distinguish implemented experiment-log/registry helpers from placeholder plotting helpers.
   - Files likely touched: `README.md`, and `docs/repo_map.md` only through the later generated-map refresh unless intentionally regenerated in that PR.
   - Acceptance criteria: no public docs imply implemented plotting helpers unless `src/reporting/plots.py` receives a scoped implementation and deterministic tests.
   - Validation: `git diff --check`, targeted grep for reporting/plotting wording.

5. Clarify risk/exposure/evaluation-risk gap.
   - Goal: document that `src/risk/constraints.py` is placeholder-only and that portfolio-level risk constraints/exposure metrics remain future work.
   - Files likely touched: docs/status or roadmap files only unless a later implementation stage is explicitly scoped.
   - Acceptance criteria: no docs imply implemented portfolio-level constraints; future implementation starts from a deterministic test plan.
   - Validation: `git diff --check`.

6. Add a lightweight documentation freshness check.
   - Goal: prevent handoff docs from naming stale "current stage" evidence after future staged merges.
   - Files likely touched: a small test or docs checklist, depending on chosen policy.
   - Acceptance criteria: the check fails or checklist flags when `docs/current_handoff.md` references a completed active stage or stale latest PR after a staged merge.
   - Validation: `python -m pytest -q` if test-based; otherwise `git diff --check`.

7. Refresh repo map after documentation-control changes.
   - Goal: make `docs/repo_map.md` include this audit and any follow-up docs.
   - Files likely touched: `docs/repo_map.md`.
   - Acceptance criteria: `python scripts/repo_map.py` produces no unexpected changes after commit.
   - Validation: `python scripts/repo_map.py`, `git diff --check`.

8. Run a final post-remediation conformance check.
   - Goal: verify that the P2 documentation-control findings above are closed or explicitly deferred after the staged PRs merge.
   - Files likely touched: a short post-remediation report only.
   - Acceptance criteria: closed/deferred findings have file evidence; hidden Unicode/control scans pass on changed Markdown; no broad source-code changes or performance claims are introduced.
   - Validation: `git diff --check`, relevant test/compile commands if code or tests changed.

## Not Covered / Uncertainty

- Raw private EODHD CSV/JSON/Markdown outputs under `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run` were not opened. This audit relies on aggregate repo checkpoint docs and tests for private-data claims.
- Historical generated report bodies under `reports/` were inventoried and treated as committed synthetic/fixture outputs, but this pass did not re-render or rewrite them because the task forbids generated-output changes.
- `docs/STAGE_PLAN.md` does not exist, so roadmap equivalents were used.
- Long historical logs were searched and sampled by targeted evidence rather than read end to end. The audit uses concrete file/path evidence for every finding, but it does not claim every historical sentence in every long log was reclassified.

## 12. Non-Goals

This audit did not fix code, refactor modules, update existing roadmap/handoff docs, fetch data, inspect raw private data, run strategy analysis, judge investment performance, or create performance claims. It did not evaluate profitability, alpha, live trading readiness, execution realism, or investment usefulness.

## 13. Appendix

### Files Inspected

- `AGENTS.md`
- `README.md`
- `CHANGELOG.md`
- `EXPERIMENT_LOG.md`
- `PROJECT_SPEC.md`
- `docs/current_handoff.md`
- `docs/current_roadmap_gap_refresh.md`
- `docs/repo_map.md`
- `docs/decision_log.md`
- `docs/engineering_log.md`
- `docs/factor_normalization_roadmap.md`
- `docs/csv_data_interface_plan.md`
- `docs/real_data_readiness_audit.md`
- `docs/eodhd_*`
- `docs/volume_aware_slippage_*`
- `docs/liquidity_*`
- `docs/quantconnect_lean_plan.md`
- `pyproject.toml`
- `.github/workflows/ci.yml`
- `src/`
- `research/`
- `tests/`
- `scripts/`
- `reports/`
- `lean/`

### Commands Run

| Command | Result |
| --- | --- |
| `git fetch origin` | Passed; `origin/main` and `HEAD` were `45fea65` before branch creation. |
| `gh pr list --state open --json number,title,headRefName,baseRefName,url --limit 20` | Passed; no open PRs. |
| `git status --porcelain \| head -n 50` | Showed pre-existing unstaged `AGENTS.md` edit before branch creation. |
| `rg --files ...` and targeted `find`/`rg`/`nl` reads | Passed; used for capped inventory and evidence collection. |
| `.venv/bin/python -m pytest -q` | Passed: 512 tests passed in 3.50s. |
| `.venv/bin/python -m compileall src tests research` | Passed. |
| `.venv/bin/python -m compileall lean` | Passed. |
| `git diff --check` | Full worktree check reported the pre-existing unstaged `AGENTS.md:153` blank-line-at-EOF issue; scoped audit-file check passed with `git diff --check -- docs/roadmap_code_conformance_audit_2026-07-01.md`. |
| Hidden Unicode/control scan for `docs/roadmap_code_conformance_audit_2026-07-01.md` | Passed: ASCII-only final file; no U+202A-U+202E bidi controls, U+2066-U+2069 bidi isolates, U+200B-U+200F zero-width characters, U+FEFF BOM, U+00A0 non-breaking spaces, or unsafe ASCII controls found. If GitHub still shows a hidden/bidirectional Unicode warning on this file, the local evidence indicates a stale or UI-level warning rather than retained hidden characters in the final file. |

### Raw Validation Results Summary

Scoped PR validation passed. The hidden Unicode/control scan found 0 issues and the final audit file is ASCII-only. The full-worktree `git diff --check` result is blocked only by the pre-existing unstaged `AGENTS.md` whitespace issue that remains outside this PR. No source code, tests, CI, notebooks, generated reports, private data, package configuration, README, handoff, roadmap, or existing docs were changed by this audit task.
