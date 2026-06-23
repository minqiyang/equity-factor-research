# Current Handoff

Last updated: 2026-06-23 for opt-in local fixture configured-case report/log support.

## State

- Current project objective: maintain an auditable, reproducible simulated equity factor research pipeline with explicit guardrails before any real-data interpretation.
- Last merged PR: #113, `[codex] Update protected PR merge workflow governance`, is present on local `main` at merge commit `6475cc1`.
- Current open PR gate: none in `equity-factor-research` at the start of this stage. If a previous-stage PR is not verified merged and is not eligible for GitHub-managed auto-merge or normal protected PR merge, report it once, enter a paused external PR gate state, and do not query GitHub again, repeat gate reports, print repeated pause notes, mark complete, or mark blocked merely because the same external PR remains pending unless the user explicitly says the PR merged, asks to resume, or asks to inspect the PR.
- Current stage: add opt-in configured-case summary report/log support to the committed synthetic local CSV fixture workflow without refreshing committed generated outputs.
- Next safe stage: after this PR is reviewed and merged, either refresh the committed synthetic local fixture report/log/registry for the configured-case summary as an explicitly generated-output-scoped PR, or pause for user-provided local CSV readiness inputs before any real-data interpretation.
- Known blockers: no user-provided local CSV bundle, completed readiness audit, or experiment-log handoff is available; volume-aware slippage remains synthetic/local-fixture only and must not be treated as execution realism or profitability evidence.
- Do-not-touch areas for the next continuation unless explicitly scoped: CSV loader, backtester, metrics, alpha files, normalization, combination, diagnostics helpers outside local fixture output wiring, committed generated reports/logs, LEAN code, real-data access, vendor APIs, broker/order logic, credentials, and `PROJECT_SPEC.md`.
- Key files for the current stage: `research/local_csv_fixture_workflow_demo.py`, `tests/test_local_csv_fixture_workflow_demo.py`, `docs/current_handoff.md`, `docs/engineering_log.md`, `docs/troubleshooting_log.md`, and `CHANGELOG.md`.
- Latest validation: focused local fixture workflow tests passed with 16 tests; full pytest passed with 503 tests; compileall passed for `src`, `tests`, and `research`; `git diff --check` passed.

Read deeper logs only when this handoff points to them, the active stage touches higher-risk areas, PR state is unclear, a check fails, or the stage involves data provenance, missing-data policy, slippage, costs, benchmark choice, execution timing, or other research assumptions.
