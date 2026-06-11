# Current Handoff

Last updated: 2026-06-11 for volume-aware slippage backtester integration design.

## State

- Current project objective: maintain an auditable, reproducible simulated equity factor research pipeline with explicit guardrails before any real-data interpretation.
- Last merged PR: #97, `[codex] Add post output refresh checkpoint`, merged 2026-06-11.
- Current open PR gate: this volume-aware slippage backtester integration design branch once opened. Pause there for human review or merge; do not start implementation while the PR is open.
- Next safe stage: after this design is reviewed and merged, create a documentation-only backtester integration test plan for a possible future precomputed-impact integration. Do not integrate volume-aware slippage into `run_long_only_backtest()` yet.
- Known blockers: no user-provided local CSV bundle, completed readiness audit, or experiment-log handoff is available; volume-aware slippage remains synthetic/local-fixture diagnostic-only until later reviewed implementation stages.
- Do-not-touch areas for the next continuation unless explicitly scoped: CSV loader, backtester, metrics, alpha files, normalization, combination, diagnostics helpers, LEAN code, real-data access, vendor APIs, broker/order logic, credentials, generated performance reports, and `PROJECT_SPEC.md`.
- Key files for the next stage: `docs/current_handoff.md`, `docs/repo_map.md`, `docs/volume_aware_slippage_backtester_integration_design.md`, `docs/engineering_log.md`, and `docs/decision_log.md`.
- Latest baseline check: 2026-06-11 on synced `main` after PR #97, `python -m pytest -q` passed with 478 tests and `python -m compileall src tests research` passed before creating the integration design branch.

Read deeper logs only when this handoff points to them, the active stage touches higher-risk areas, PR state is unclear, a check fails, or the stage involves data provenance, missing-data policy, slippage, costs, benchmark choice, execution timing, or other research assumptions.
