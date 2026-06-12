# Current Handoff

Last updated: 2026-06-12 for synthetic robustness report/log support.

## State

- Current project objective: maintain an auditable, reproducible simulated equity factor research pipeline with explicit guardrails before any real-data interpretation.
- Last merged PR: #105, `[codex] Add synthetic split robustness demo`, merged at `2026-06-12T05:30:44Z`.
- Current open PR gate: this synthetic robustness report/log support branch once opened. Pause there for human review or GitHub auto-merge only if protections are verifiable and the PR remains eligible.
- Current stage: add explicit opt-in Markdown report and JSON experiment-log support to `research/synthetic_split_robustness_demo.py` without refreshing committed generated reports/logs.
- Next safe stage: after this support PR is reviewed and merged, run a generated-output refresh for the synthetic robustness demo only if explicitly scoped and caveats/all-case/invalid-case fields are verified.
- Known blockers: no user-provided local CSV bundle, completed readiness audit, or experiment-log handoff is available; volume-aware slippage remains synthetic/local-fixture only and must not be treated as execution realism or profitability evidence.
- Do-not-touch areas for the next continuation unless explicitly scoped: CSV loader, backtester, metrics, alpha files, normalization, combination, diagnostics helpers, research scripts, generated reports/logs, LEAN code, real-data access, vendor APIs, broker/order logic, credentials, and `PROJECT_SPEC.md`.
- Key files for the next stage: likely `reports/synthetic_split_robustness_demo.md`, `reports/experiment_logs/synthetic_split_robustness_demo.json`, `reports/experiment_registry.md`, `research/synthetic_split_robustness_demo.py`, focused tests, `docs/current_handoff.md`, `docs/engineering_log.md`, `docs/decision_log.md`, and `CHANGELOG.md`.
- Latest validation: 2026-06-12 on the synthetic robustness report/log support branch, `python -m pytest tests/test_synthetic_split_robustness_demo.py -q` passed with 13 tests, `python -m research.synthetic_split_robustness_demo` passed without creating default reports/logs, `python -m pytest -q` passed with 501 tests, `python -m compileall src tests research` passed, `python scripts/repo_map.py` produced no `docs/repo_map.md` diff, `git diff --check` passed, and `.\scripts\audit-skills.ps1` passed.

Read deeper logs only when this handoff points to them, the active stage touches higher-risk areas, PR state is unclear, a check fails, or the stage involves data provenance, missing-data policy, slippage, costs, benchmark choice, execution timing, or other research assumptions.
