# Current Handoff

Last updated: 2026-06-11 for post local fixture slippage output refresh checkpoint.

## State

- Current project objective: maintain an auditable, reproducible simulated equity factor research pipeline with explicit guardrails before any real-data interpretation.
- Last merged PR: #96, `[codex] Refine context entry file policy`, merged 2026-06-11.
- Current open PR gate: none observed before creating the post local fixture slippage output refresh checkpoint branch. If `codex/post-output-refresh-handoff-checkpoint` is open, pause there for human review or merge.
- Next safe stage: after this checkpoint is reviewed and merged, consider a documentation-only volume-aware slippage backtester integration design. Do not integrate volume-aware slippage into backtester net returns until that design boundary is explicitly reviewed in a later stage.
- Known blockers: no user-provided local CSV bundle, completed readiness audit, or experiment-log handoff is available; volume-aware slippage remains synthetic/local-fixture diagnostic-only until later reviewed stages.
- Do-not-touch areas for the next continuation unless explicitly scoped: CSV loader, backtester, metrics, alpha files, normalization, combination, diagnostics helpers, LEAN code, real-data access, vendor APIs, broker/order logic, credentials, generated performance reports, and `PROJECT_SPEC.md`.
- Key files for the next stage: `docs/current_handoff.md`, `docs/repo_map.md`, `docs/codex_long_running_controller.md`, `.agents/skills/staged-quant-workflow/SKILL.md`, `docs/post_local_fixture_slippage_output_refresh_checkpoint.md`, `docs/engineering_log.md`, and `docs/decision_log.md`.
- Latest baseline check: 2026-06-11 on synced `main` after PR #96, `python -m pytest -q` passed with 478 tests and `python -m compileall src tests research` passed before creating the post local fixture slippage output refresh checkpoint branch.

Read deeper logs only when this handoff points to them, the active stage touches higher-risk areas, PR state is unclear, a check fails, or the stage involves data provenance, missing-data policy, slippage, costs, benchmark choice, execution timing, or other research assumptions.
