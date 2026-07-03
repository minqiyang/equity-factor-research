# Current Handoff

Last updated: 2026-07-03 after PR #130 merged.

## Latest Verified State

- Latest verified merged PR: #130, `Add roadmap-code conformance audit`, merged at `ce29e3e`.
- Current baseline audit report: `docs/roadmap_code_conformance_audit_2026-07-01.md`.
- Recent relevant merges: #127 EODHD limited diagnostics brief, #128 review guidelines, #129 README refresh, #130 roadmap-code conformance audit.
- Current project objective: maintain an auditable, reproducible simulated equity factor research pipeline with explicit guardrails before any real-data interpretation.
- Current remediation sequence: work through the PR #130 audit findings one small PR at a time. Stop before each merge for human review.
- Local worktree note: a pre-existing unstaged `AGENTS.md` edit may be present and is unrelated to this handoff. Do not stage or rewrite it unless explicitly scoped.

## What Is Complete

- Strict local CSV loaders, factor helpers, diagnostics, synthetic/local-fixture workflows, simulated backtester accounting, private EODHD diagnostic guardrails, and LEAN non-execution scaffold are implemented where cited by the audit.
- Private EODHD validation-only loader/schema checks passed and remain outside the repository under `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run`.
- Private EODHD IC, Rank IC, and quantile-spread diagnostic calculations exist through the private diagnostics workflow and neutral review/brief checkpoints.
- `EXPERIMENT_LOG.md` is now treated as a source-of-truth gate for provenance, alignment, benchmark, sample split, cost/slippage, and failure-mode records before local CSV or EODHD metrics are interpreted.

## Still Blocked

- Broader real-data interpretation remains blocked until point-in-time universe policy, adjustment policy, benchmark methodology, sample split, cost/slippage assumptions, and interpretation policy are accepted.
- Private diagnostics are not strategy, portfolio, PnL, Sharpe, drawdown, alpha, profitability, investment, robustness, or trading-readiness evidence.
- `src/reporting/plots.py` is placeholder-only; public docs still need a later scoped clarification.
- `src/risk/constraints.py` is placeholder-only; portfolio-level constraints, exposure concentration, tracking error or active risk, hit rate, and average-holdings coverage remain future work.
- Older roadmap/design docs still need status or superseded notes where implementation has landed.

## Next Safe Stage

After this handoff refresh PR is reviewed and merged, start the next PR-sized stage:

```text
Add status and superseded notes to older roadmap/design docs.
```

Scope that stage to stale roadmap/design documents such as:

- `docs/factor_normalization_roadmap.md`
- `docs/csv_data_interface_plan.md`
- `docs/volume_aware_slippage_backtester_integration_design.md`
- `docs/volume_aware_slippage_backtester_integration_test_plan.md`
- `docs/post_precomputed_volume_aware_slippage_checkpoint.md` if a narrow successor pointer is needed

Do not change implementation, tests, CI, generated outputs, private data, README, or EODHD docs in that stage unless a narrow cross-reference is required and justified.

## Do Not Touch Without Explicit Scope

- `src/`, `research/`, `tests/`, `.github/`, `pyproject.toml`, generated reports/logs, private data, vendor APIs, credentials, broker/order logic, live trading, and strategy/performance interpretation.
- Raw private EODHD CSV/JSON/Markdown files. Repo docs may reference aggregate counts and private paths only.
- `docs/repo_map.md` until the planned repo-map refresh stage, unless the current PR explicitly regenerates it.

## Key Files

- `docs/roadmap_code_conformance_audit_2026-07-01.md`
- `docs/current_handoff.md`
- `docs/current_roadmap_gap_refresh.md`
- `EXPERIMENT_LOG.md`
- `README.md`
- `PROJECT_SPEC.md`
- `docs/eodhd_*`
- `docs/repo_map.md`
- `CHANGELOG.md`

Read deeper logs only when this handoff points to them, the active stage touches higher-risk areas, PR state is unclear, a check fails, or the stage involves data provenance, missing-data policy, slippage, costs, benchmark choice, execution timing, or other research assumptions.
