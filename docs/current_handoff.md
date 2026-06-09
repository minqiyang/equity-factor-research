# Current Handoff

Last updated: 2026-06-09 for volume-aware slippage diagnostic helper.

## State

- Current project objective: maintain an auditable, reproducible simulated equity factor research pipeline with explicit guardrails before any real-data interpretation.
- Last merged PR: #90, `[codex] Add volume-aware slippage design`, merged 2026-06-09.
- Current open PR gate: none observed before creating the volume-aware slippage diagnostic helper branch. If `codex/volume-aware-slippage-diagnostic-helper` is open, pause there for human review or merge.
- Next safe stage: after the diagnostic helper is reviewed and merged, consider a synthetic/local-fixture smoke diagnostic that reports participation and rejected/capped counts only. Do not integrate volume-aware slippage into backtester net returns until the helper and smoke diagnostic boundaries are reviewed.
- Known blockers: no user-provided local CSV bundle, completed readiness audit, or experiment-log handoff is available; volume-aware slippage remains synthetic/local-fixture diagnostic-only until later reviewed stages.
- Do-not-touch areas for this stage: research source, tests, research scripts, generated reports, CSV loader, backtester, metrics, alpha files, normalization, combination, diagnostics, LEAN code, real-data access, broker/order logic, credentials, and `PROJECT_SPEC.md`.
- Key files for the next stage: `docs/current_handoff.md`, `docs/repo_map.md`, `docs/codex_long_running_controller.md`, `.agents/skills/staged-quant-workflow/SKILL.md`, `docs/engineering_log.md`, `docs/decision_log.md`, and `docs/troubleshooting_log.md`.
- Latest baseline check: 2026-06-09 on synced `main` after PR #90, `python -m pytest -q` passed with 461 tests and `python -m compileall src tests research` passed before creating the volume-aware slippage diagnostic helper branch.

Read deeper logs only when this handoff points to them, the active stage touches higher-risk areas, PR state is unclear, a check fails, or the stage involves data provenance, missing-data policy, slippage, costs, benchmark choice, execution timing, or other research assumptions.
