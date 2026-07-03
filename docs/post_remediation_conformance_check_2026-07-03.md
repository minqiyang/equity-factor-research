# Post-Remediation Conformance Check

Date: 2026-07-03

## Scope

This report checks whether the roadmap-code conformance findings from
`docs/roadmap_code_conformance_audit_2026-07-01.md` have been closed by the
follow-up documentation-control PRs, or remain explicitly deferred.

It is documentation only. It does not change source code, tests, CI, private
data, generated reports, existing roadmap docs, strategy logic, data access,
execution assumptions, or performance claims.

## Evidence Checked

| Area | Status | Evidence |
| --- | --- | --- |
| Current handoff freshness | Closed for the known stale-stage issue; ongoing freshness is now guarded. | `docs/current_handoff.md` has a cached-baseline warning, separate open/merged PR checks, a freshness checklist, and the `@codex review` P1/P2 merge gate. `tests/test_project_structure.py` checks those guardrails and known stale active-stage phrasing. |
| Older roadmap/status notes | Closed for the audited stale future-work docs. | `docs/factor_normalization_roadmap.md`, `docs/csv_data_interface_plan.md`, `docs/volume_aware_slippage_backtester_integration_design.md`, and `docs/volume_aware_slippage_backtester_integration_test_plan.md` have historical or superseded-in-part status notes with implementation/test pointers. |
| EODHD validation and diagnostics wording | Closed for the audited wording drift. | `docs/current_roadmap_gap_refresh.md`, `docs/current_handoff.md`, and `docs/eodhd_*` checkpoint docs distinguish private validation-only checks, private IC/Rank IC/quantile-spread diagnostics, and still-blocked broader interpretation. |
| Reporting plotting-helper placeholder wording | Closed for public docs and repo map. | `README.md` and `docs/repo_map.md` distinguish implemented experiment-log/registry helpers from placeholder-only plotting helpers. |
| Risk, exposure, and evaluation-metrics gap | Closed as documentation; implementation remains deferred. | `docs/current_roadmap_gap_refresh.md` marks `src/risk/constraints.py` placeholder-only and lists tracking error or active risk, hit rate, average holding-period return, average holdings, exposure concentration, and portfolio-level risk constraints as future work. |
| Documentation freshness guard | Closed. | `docs/current_handoff.md` has the freshness checklist; `tests/test_project_structure.py` checks the checklist, independent open/merged PR commands, readiness inputs, guardrail phrases, and stale current-PR merge wording. |
| Repo map freshness | Closed. | `python scripts/repo_map.py` was rerun after adding this report; the generated diff only updates the mapped `docs/` file count. |

## Findings Closed

- P2 stale current handoff guidance from PR #130.
- P2 stale historical roadmap/design wording for normalization, CSV loader, and volume-aware slippage implementation status.
- P2 EODHD validation-only versus private diagnostics wording drift.
- P2 `EXPERIMENT_LOG.md` source-of-truth omission in the baseline audit.
- P2 reporting plotting-helper placeholder overstatement in public docs/repo map.
- P2 risk-constraint and evaluation-metric implementation inventory drift.
- P2 manual-only handoff freshness risk, now covered by a checklist and a small CI guard.

## Findings Deferred

- Real local CSV/EODHD interpretation remains blocked until dataset scope,
  provenance, schema, adjustment policy, point-in-time universe or survivorship
  policy, benchmark methodology, sample split, costs/slippage, experiment-log
  requirements, and interpretation policy are accepted.
- `src/reporting/plots.py` remains placeholder-only. Plotting implementation and
  tests should be a future scoped PR if needed.
- `src/risk/constraints.py` remains placeholder-only. Portfolio-level risk
  constraints and missing evaluation metrics should start with a scoped test
  plan before implementation.
- Robustness and parameter-sensitivity interpretation for user-provided local
  CSV/EODHD research remains blocked until a dataset passes the readiness gates.

## Remaining Risks

- Handoff freshness is not fully automatic; the new test checks required
  guardrails and known stale active-stage phrasing, but semantic drift still
  requires reviewer judgment.
- Private EODHD raw outputs were not opened. This check relies on repository
  checkpoint docs and tests that summarize private outputs without exposing
  private data.
- `docs/current_handoff.md` intentionally records a cached baseline, not live
  GitHub state. Future sessions must run the freshness checklist commands
  before acting.

## Validation

Validation run for this PR:

- `python scripts/repo_map.py`
- `git diff --check`
- `.venv/bin/python -m pytest -q`
- `.venv/bin/python -m compileall src tests research`
- `.venv/bin/python -m compileall lean`
- hidden Unicode/control-character scan for changed Markdown files
