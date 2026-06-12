# Current Handoff

Last updated: 2026-06-12 for synthetic robustness and split-aware validation plan.

## State

- Current project objective: maintain an auditable, reproducible simulated equity factor research pipeline with explicit guardrails before any real-data interpretation.
- Last merged PR: #103, `[codex] Refresh roadmap after volume-aware sequence`, merged at `2026-06-12T05:15:23Z`.
- Current open PR gate: this synthetic robustness and split-aware validation plan branch once opened. Pause there for human review or GitHub auto-merge only if protections are verifiable and the PR remains clearly low-risk.
- Current stage: documentation-only `docs/synthetic_robustness_validation_plan.md` defining the guardrails, inputs, split policy, all-case reporting expectations, stop conditions, and future test/report/log fields needed before synthetic robustness implementation.
- Next safe stage: after this plan PR is reviewed and merged, add deterministic synthetic split-aware robustness implementation tests and code, with generated outputs changed only if explicitly scoped.
- Known blockers: no user-provided local CSV bundle, completed readiness audit, or experiment-log handoff is available; volume-aware slippage remains synthetic/local-fixture only and must not be treated as execution realism or profitability evidence.
- Do-not-touch areas for the next continuation unless explicitly scoped: CSV loader, backtester, metrics, alpha files, normalization, combination, diagnostics helpers, research scripts, generated reports/logs, LEAN code, real-data access, vendor APIs, broker/order logic, credentials, and `PROJECT_SPEC.md`.
- Key files for the next stage: likely `research/`, `tests/`, `docs/engineering_log.md`, `docs/decision_log.md`, `CHANGELOG.md`, and generated reports/logs only if explicitly scoped.
- Latest validation: 2026-06-12 on the synthetic robustness validation plan branch, `python -m pytest -q` passed with 488 tests, `python -m compileall src tests research` passed, `python scripts/repo_map.py` refreshed `docs/repo_map.md`, `git diff --check` passed, and `.\scripts\audit-skills.ps1` passed.

Read deeper logs only when this handoff points to them, the active stage touches higher-risk areas, PR state is unclear, a check fails, or the stage involves data provenance, missing-data policy, slippage, costs, benchmark choice, execution timing, or other research assumptions.
