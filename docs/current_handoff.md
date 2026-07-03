# Current Handoff

Last updated: 2026-07-03 for the docs freshness guard stage.

## Latest Verified State

- Cached baseline at last handoff edit: PR #136, `Refresh current handoff after risk gap clarification`, merged at `2da5120`.
- Before acting on this handoff, verify live `origin/main` and open PR state with the freshness checklist below.
- Current baseline audit report: `docs/roadmap_code_conformance_audit_2026-07-01.md`.
- Recent baseline merges through the last handoff edit: #130 roadmap-code conformance audit, #131 current handoff refresh, #132 historical roadmap status notes, #133 EODHD readiness wording, #134 reporting placeholder clarification, #135 risk/evaluation gap clarification, #136 handoff review-gate refresh.
- Current project objective: maintain an auditable, reproducible simulated equity factor research pipeline with explicit guardrails before any real-data interpretation.
- Current remediation sequence: continue one small PR at a time from the PR #130 audit findings and `docs/current_roadmap_gap_refresh.md`. Do not merge a PR until GitHub `@codex review` has run on the current head and any P1/P2 feedback is resolved.
- Local worktree note: a pre-existing unstaged `AGENTS.md` edit may be present and is unrelated to this handoff. Do not stage or rewrite it unless explicitly scoped.

## What Is Complete

- Strict local CSV loaders, factor helpers, diagnostics, synthetic/local-fixture workflows, simulated backtester accounting, private EODHD diagnostic guardrails, and LEAN non-execution scaffold are implemented where cited by the audit.
- Private EODHD validation-only loader/schema checks passed and remain outside the repository under `/Users/rhapsoul/Documents/Codex/private_data/eodhd_first_dry_run`.
- Private EODHD IC, Rank IC, and quantile-spread diagnostic calculations exist through the private diagnostics workflow and neutral review/brief checkpoints.
- `EXPERIMENT_LOG.md` is now treated as a source-of-truth gate for provenance, alignment, benchmark, sample split, cost/slippage, and failure-mode records before local CSV or EODHD metrics are interpreted.
- Older roadmap/design docs have historical or superseded-in-part status notes where the PR #130 audit found stale future-work wording.
- Public docs and `docs/repo_map.md` now distinguish implemented experiment-log/registry helpers from placeholder-only plotting helpers.
- The current roadmap gap refresh now distinguishes implemented simulated backtest metrics from missing portfolio-level risk constraints and additional evaluation metrics.

## Still Blocked

- Broader real-data interpretation remains blocked until point-in-time universe policy, adjustment policy, benchmark methodology, sample split, cost/slippage assumptions, and interpretation policy are accepted.
- Private diagnostics are not strategy, portfolio, PnL, Sharpe, drawdown, alpha, profitability, investment, robustness, or trading-readiness evidence.
- `src/reporting/plots.py` remains placeholder-only; do not implement plotting helpers unless a future stage explicitly scopes code and tests.
- `src/risk/constraints.py` is placeholder-only; portfolio-level constraints, exposure concentration, tracking error or active risk, hit rate, and average-holdings coverage remain future work.
- No documented robustness or parameter-sensitivity interpretation exists for a user-provided local CSV or EODHD research run because no such run has passed readiness gates.

## Next Safe Stage

If the user has not supplied and accepted a local CSV/EODHD methodology package, the next safe stage is documentation-only:

```text
Clarify real-data readiness methodology inputs and stop conditions.
```

That stage should make the required readiness inputs explicit before any real-data interpretation:

- dataset scope and provenance
- schema and adjustment policy
- point-in-time universe or survivorship policy
- benchmark methodology
- train/validation/test or other sample split policy
- transaction cost and slippage assumptions
- experiment-log requirements
- interpretation policy and stop conditions

Do not fetch data, interpret private diagnostics, add vendor APIs, change source code, generate reports, or make performance claims in that stage. If the user does supply accepted methodology inputs, run the real-data readiness audit flow before any interpretation.

## Freshness Checklist

Before changing this handoff, verify:

- `origin/main` with `git fetch origin`;
- current open PR gate with `gh pr list --state open --limit 10`;
- recent merged history with `gh pr list --state merged --limit 10`;
- `Latest Verified State`, `What Is Complete`, `Still Blocked`, and `Next Safe Stage` agree with `docs/current_roadmap_gap_refresh.md` and the latest merged PRs;
- stale active-stage wording has been removed instead of treating already-merged work as pending;
- private-data, no-performance-claim, no-live-trading, and no-brokerage boundaries remain visible;
- any PR touching this handoff waits for GitHub `@codex review` on the current head and resolves P1/P2 feedback before merge.

## Do Not Touch Without Explicit Scope

- `src/`, `research/`, `tests/`, `.github/`, `pyproject.toml`, generated reports/logs, private data, vendor APIs, credentials, broker/order logic, live trading, and strategy/performance interpretation.
- Raw private EODHD CSV/JSON/Markdown files. Repo docs may reference aggregate counts and private paths only.
- `docs/repo_map.md` unless the current PR explicitly regenerates it.

## Key Files

- `docs/roadmap_code_conformance_audit_2026-07-01.md`
- `docs/current_handoff.md`
- `docs/current_roadmap_gap_refresh.md`
- `EXPERIMENT_LOG.md`
- `README.md`
- `PROJECT_SPEC.md`
- `docs/eodhd_*`
- `docs/repo_map.md`
- `CHANGELOG.md`

Read deeper logs only when this handoff points to them, the active stage touches higher-risk areas, PR state is unclear, a check fails, or the stage involves data provenance, missing-data policy, slippage, costs, benchmark choice, execution timing, or other research assumptions.
