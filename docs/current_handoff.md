# Current Handoff

Last updated: 2026-06-12 for synthetic split-aware robustness demo.

## State

- Current project objective: maintain an auditable, reproducible simulated equity factor research pipeline with explicit guardrails before any real-data interpretation.
- Last merged PR: #104, `[codex] Add synthetic robustness validation plan`, merged at `2026-06-12T05:20:45Z`.
- Current open PR gate: this synthetic split-aware robustness demo branch once opened. Pause there for human review or GitHub auto-merge only if protections are verifiable and the PR remains clearly low-risk.
- Current stage: synthetic-only research helper and tests that report every configured signal case across train/validation/test splits, including invalid constant-signal diagnostics, without writing generated reports/logs.
- Next safe stage: after this implementation PR is reviewed and merged, add explicit caveated report/log support or a generated-output refresh for the synthetic robustness demo only if that scope is selected deliberately.
- Known blockers: no user-provided local CSV bundle, completed readiness audit, or experiment-log handoff is available; volume-aware slippage remains synthetic/local-fixture only and must not be treated as execution realism or profitability evidence.
- Do-not-touch areas for the next continuation unless explicitly scoped: CSV loader, backtester, metrics, alpha files, normalization, combination, diagnostics helpers, research scripts, generated reports/logs, LEAN code, real-data access, vendor APIs, broker/order logic, credentials, and `PROJECT_SPEC.md`.
- Key files for the next stage: likely `research/synthetic_split_robustness_demo.py`, `tests/test_synthetic_split_robustness_demo.py`, reporting/log docs, `docs/current_handoff.md`, `docs/engineering_log.md`, `docs/decision_log.md`, `CHANGELOG.md`, `docs/repo_map.md`, and generated reports/logs only if explicitly scoped.
- Latest validation: 2026-06-12 on the synthetic split-aware robustness demo branch, `python -m pytest tests/test_synthetic_split_robustness_demo.py -q` passed with 10 tests, `python -m research.synthetic_split_robustness_demo` passed, `python -m pytest -q` passed with 498 tests, `python -m compileall src tests research` passed, `python scripts/repo_map.py` refreshed `docs/repo_map.md`, `git diff --check` passed, and `.\scripts\audit-skills.ps1` passed.

Read deeper logs only when this handoff points to them, the active stage touches higher-risk areas, PR state is unclear, a check fails, or the stage involves data provenance, missing-data policy, slippage, costs, benchmark choice, execution timing, or other research assumptions.
