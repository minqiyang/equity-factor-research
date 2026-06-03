# Decision Log

This log records durable workflow, architecture, and research-process decisions
for the simulated equity factor research project.

It is not an experiment log and must not be used to claim profitability or
investment performance.

## How To Update This Log

- Add a dated entry for decisions that future Codex sessions should preserve.
- State the context, decision, rationale, consequences, and follow-up.
- Keep entries factual and separate observed evidence from assumptions.
- Link or name the relevant files, branches, PRs, checks, or logs when useful.

---

## 2026-06-03 - Refresh WorldQuant Catalog Before More Alpha Work

Context:

- `docs/post_csv_checkpoint_report.md` identified stale wording in
  `docs/worldquant_alpha_catalog.md`.
- The catalog still described the repository as catalog-only even though the
  operator layer and `alpha_009` research feature now exist.
- PR #29 was merged, latest `main` was synced, baseline validation passed, and
  no open pull request gate remained.
- Assumption: refreshing the catalog is the next unblocked safe stage because
  it is documentation-only and directly addresses the latest checkpoint
  recommendation.

Decision:

- Refresh `docs/worldquant_alpha_catalog.md` before implementing another
  formula or expanding data schemas.
- Treat `alpha_009` as implemented research-feature status only, not a full
  strategy, backtest integration, trading recommendation, or profitability
  claim.
- Keep `alpha_012` blocked on volume plus close support and `alpha_101`
  blocked on OHLC support.
- Keep VWAP, market-cap, and industry-neutral categories deferred until the
  required data support and validation rules exist.

Rationale:

- Roadmap documents should not guide future stages from stale pre-`alpha_009`
  assumptions.
- Documentation cleanup is lower risk than starting another formula while the
  data prerequisites and next-stage options are still being clarified.
- The project should continue to avoid bulk WorldQuant 101 implementation.

Consequences:

- Future alpha stages should start from current implementation status rather
  than the original Stage 1 catalog-only milestone.
- Additional formula work should be PR-sized and preceded by explicit formula,
  data, operator, missing-value, and test scope.
- This decision changes documentation only. It does not modify source code,
  data access, strategy logic, backtester behavior, execution assumptions, or
  performance claims.

Follow-up:

- If the next alpha stage is code-changing, run the stricter code PR readiness
  gate: tests plus read-only review with no high or medium issues.
- Consider a future planning stage for volume + close or OHLC schema support
  before `alpha_012` or `alpha_101`.

---

## 2026-06-03 - Bounded Staged Execution Behavior

Context:

- The staged workflow now has a repository-local Skill and long-running
  controller.
- The user clarified that Codex should continue as a bounded staged execution
  agent and should not ask for a new prompt after every small step.
- Assumption: this clarification should be preserved as workflow-control
  documentation and Skill guidance, not treated as a source-code or product
  behavior change.

Decision:

- Add an explicit low-risk ambiguity policy to
  `docs/codex_long_running_controller.md`.
- Expand controller stop conditions to cover dirty working trees before new
  stages, destructive or broad architecture ambiguity, missing credentials or
  external access, new production dependencies, unsafe test failures,
  high/medium review issues, security/privacy/data-loss/irreversible risks,
  scope conflicts, and PR-ready human review gates.
- Update `.agents/skills/staged-quant-workflow/SKILL.md` so future sessions
  continue through low-risk ambiguity with logged assumptions and treat missing
  expected files as workflow scaffolding only when that is low-risk.

Rationale:

- The project needs forward motion without turning every minor ambiguity into a
  user prompt.
- The same behavior must remain bounded by safety, scope, review, and merge
  gates.
- Missing workflow files can be repaired safely in small process PRs, while
  missing product-behavior artifacts require a stop report.

Consequences:

- Future Codex sessions should continue through minor documentation/workflow
  ambiguities after recording assumptions.
- Future sessions must still stop for the defined safety, scope, review, and
  human approval conditions.
- This decision changes process guidance only. It does not modify source code,
  data access, trading behavior, strategy logic, or performance claims.

Follow-up:

- Keep each behavior update PR-sized.
- If this policy causes overreach, record the failure in
  `docs/troubleshooting_log.md` and tighten the stop conditions.

---

## 2026-06-03 - Add Long-Running Workflow Control Artifacts

Context:

- The staged workflow Skill exists at
  `.agents/skills/staged-quant-workflow/SKILL.md`.
- The user requested continuation based on `docs/codex_long_running_controller.md`,
  `docs/decision_log.md`, `docs/troubleshooting_log.md`, `CHANGELOG.md`, and
  `scripts/audit-skills.ps1`.
- On latest `main`, those controller, log, changelog, and audit script files
  were missing.

Decision:

- Add a repository-local long-running controller document.
- Add durable decision and troubleshooting logs.
- Add a changelog.
- Add a local PowerShell Skill audit script.
- Update the staged workflow Skill so future continuations read the controller
  and can run the Skill audit.

Rationale:

- The project now depends on a recurring staged workflow, not a one-off prompt.
- Missing controller and log files make future continuation ambiguous.
- A local Skill audit gives future sessions a deterministic check before
  relying on project Skills.

Consequences:

- Future Codex sessions have explicit startup, stop-condition, logging, and PR
  gate guidance.
- Workflow-control changes remain separate from factor research implementation.
- The repository gains process infrastructure but no source-code, data-access,
  strategy, backtest, or performance-claim changes.

Follow-up:

- Keep the controller concise and update it only when a reusable workflow rule
  is verified.
- Use `docs/troubleshooting_log.md` for detailed failure chains.
- Continue normal staged PR review and do not merge PRs without explicit user
  instruction.
