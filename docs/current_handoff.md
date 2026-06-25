# Current Handoff

Last updated: 2026-06-24 for local CSV validation-only dry run intake checklist.

## State

- Current project objective: maintain an auditable, reproducible simulated equity factor research pipeline with explicit guardrails before any real-data interpretation.
- Last merged PR: #117, `[codex] Add local CSV readiness input checkpoint`, is present on local `main` at merge commit `d8adda1`.
- Current open PR gate: none in `equity-factor-research` at the start of this stage. If a previous-stage PR is not verified merged and is not eligible for GitHub-managed auto-merge or normal protected PR merge, report it once, enter a paused external PR gate state, and do not query GitHub again, repeat gate reports, print repeated pause notes, mark complete, or mark blocked merely because the same external PR remains pending unless the user explicitly says the PR merged, asks to resume, or asks to inspect the PR.
- Current stage: add a concise user-facing intake checklist for a future local CSV validation-only dry run.
- Next safe stage: after this checklist is reviewed and merged, pause for the user-provided CSV bundle and metadata. If the user supplies the bundle, proceed only with metadata-first readiness intake and stop before any strategy run or performance interpretation.
- Known blockers: no user-provided local CSV bundle, completed readiness audit, or experiment-log handoff is available; volume-aware slippage remains synthetic/local-fixture only and must not be treated as execution realism or profitability evidence.
- Do-not-touch areas for the next continuation unless explicitly scoped: CSV loader, backtester, metrics, alpha files, normalization, combination, diagnostics helpers, research scripts, LEAN code, real-data access, vendor APIs, broker/order logic, credentials, and `PROJECT_SPEC.md`.
- Key files for the current stage: `docs/local_csv_validation_dry_run_intake_checklist.md`, `docs/current_handoff.md`, `docs/engineering_log.md`, `CHANGELOG.md`, and `docs/repo_map.md`.
- Latest validation: full pytest passed with 503 tests; compileall passed for `src`, `tests`, and `research`; repo map refresh ran; `git diff --check` passed; guardrail grep matches were documentation prohibitions/caveats only.

Read deeper logs only when this handoff points to them, the active stage touches higher-risk areas, PR state is unclear, a check fails, or the stage involves data provenance, missing-data policy, slippage, costs, benchmark choice, execution timing, or other research assumptions.
