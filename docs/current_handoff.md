# Current Handoff

Last updated: 2026-06-09 for token-efficient workflow controls.

## State

- Current project objective: maintain an auditable, reproducible simulated equity factor research pipeline with explicit guardrails before any real-data interpretation.
- Last merged PR: #88, `[codex] Add post slippage cost checkpoint`, merged 2026-06-09.
- Current open PR gate: none observed before this branch. If `codex/token-efficient-workflow-controls` is open, pause there for human review or merge.
- Next safe stage: merge this workflow-control PR, then start future work from this handoff and `docs/repo_map.md`. The current roadmap still favors a documentation-only volume-aware slippage design before implementation.
- Known blockers: no user-provided local CSV bundle, completed readiness audit, or experiment-log handoff is available; volume-aware slippage still needs a design gate.
- Do-not-touch areas for this stage: research source, tests, research scripts, generated reports, CSV loader, backtester, metrics, alpha files, normalization, combination, diagnostics, LEAN code, real-data access, broker/order logic, credentials, and `PROJECT_SPEC.md`.
- Key files for the next stage: `docs/current_handoff.md`, `docs/repo_map.md`, `docs/codex_long_running_controller.md`, `.agents/skills/staged-quant-workflow/SKILL.md`, `docs/engineering_log.md`, `docs/decision_log.md`, and `docs/troubleshooting_log.md`.
- Latest baseline check: 2026-06-09 on this branch, `python -m pytest -q` passed with 461 tests, `python -m compileall src tests research` passed, `.\scripts\audit-skills.ps1` passed, `python scripts/repo_map.py` regenerated the map, and `git diff --check` passed before commit.

Read deeper logs only when this handoff points to them, the active stage touches higher-risk areas, PR state is unclear, a check fails, or the stage involves data provenance, missing-data policy, slippage, costs, benchmark choice, execution timing, or other research assumptions.
