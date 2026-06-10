# Current Handoff

Last updated: 2026-06-09 for post volume-aware slippage smoke checkpoint.

## State

- Current project objective: maintain an auditable, reproducible simulated equity factor research pipeline with explicit guardrails before any real-data interpretation.
- Last merged PR: #92, `[codex] Add local fixture slippage smoke diagnostic`, merged 2026-06-09.
- Current open PR gate: none observed before creating the post volume-aware slippage smoke checkpoint branch. If `codex/post-volume-aware-slippage-smoke-checkpoint` is open, pause there for human review or merge.
- Next safe stage: after the checkpoint is reviewed and merged, consider a narrow synthetic generated-output refresh for the local CSV fixture report/log/registry so those artifacts reflect the volume-aware slippage smoke diagnostic. Do not integrate volume-aware slippage into backtester net returns until that boundary is explicitly reviewed in a later design stage.
- Known blockers: no user-provided local CSV bundle, completed readiness audit, or experiment-log handoff is available; volume-aware slippage remains synthetic/local-fixture diagnostic-only until later reviewed stages. Generated local CSV fixture artifacts are expected to remain stale until the recommended refresh stage runs.
- Do-not-touch areas for the next continuation unless explicitly scoped: CSV loader, backtester, metrics, alpha files, normalization, combination, diagnostics helpers, LEAN code, real-data access, vendor APIs, broker/order logic, credentials, generated performance reports, and `PROJECT_SPEC.md`.
- Key files for the next stage: `docs/current_handoff.md`, `docs/repo_map.md`, `docs/codex_long_running_controller.md`, `.agents/skills/staged-quant-workflow/SKILL.md`, `docs/engineering_log.md`, `docs/decision_log.md`, and `docs/troubleshooting_log.md`.
- Latest baseline check: 2026-06-09 on synced `main` after PR #92, `python -m pytest -q` passed with 478 tests and `python -m compileall src tests research` passed before creating the post volume-aware slippage smoke checkpoint branch.

Read deeper logs only when this handoff points to them, the active stage touches higher-risk areas, PR state is unclear, a check fails, or the stage involves data provenance, missing-data policy, slippage, costs, benchmark choice, execution timing, or other research assumptions.
