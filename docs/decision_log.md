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

## 2026-06-04 - Keep First LEAN-Adjacent Code Signal-Only

Context:

- PR #42 merged the LEAN runnable draft readiness decision.
- That decision found the repository is not ready for runnable LEAN code under
  the current guardrails.
- The active workflow still prohibits real market data fetching, downloads,
  credentials, live trading, paper trading, brokerage integration, order
  execution, and profitability claims.

Decision:

- Define the next LEAN-adjacent code boundary as signal-only and
  metadata-only.
- Do not allow the next code stage to import `AlgorithmImports`, subclass
  `QCAlgorithm`, create `config.json`, run LEAN, subscribe to platform data,
  call history APIs, create portfolio targets, place orders, model fills,
  configure brokerage, or produce backtest results.
- If this design is reviewed and merged, the next possible code PR should be a
  pure-Python `lean/signal_only_momentum_draft.py` plus static scope tests.

Rationale:

- A signal-only draft can make the factor translation boundary auditable
  without introducing runtime dependencies, account access, data-source
  semantics, order semantics, or performance interpretation.
- Keeping the first code step metadata-only preserves forward progress while
  maintaining the existing simulated-research guardrails.

Consequences:

- Runnable LEAN code remains intentionally blocked.
- The future signal-only draft must avoid order dates, target weights,
  brokerage models, fill models, live mode, paper mode, and implemented
  portfolio behavior.
- Static tests should continue to reject data downloads, credential reads,
  runtime LEAN imports, order calls, and profitability or trading-readiness
  claims.

Follow-up:

- After this design is reviewed and merged, create a small code PR for a
  pure-Python LEAN signal-only momentum draft with static guardrail tests, or
  stop if the implementation cannot satisfy the documented boundary.

---

## 2026-06-04 - Defer Runnable LEAN Draft Until Signal-Only Boundary Is Designed

Context:

- PR #41 merged the LEAN scaffold review checklist.
- The repository now has a metadata-only LEAN scaffold and static tests that
  intentionally reject runtime LEAN imports, credential/data imports,
  brokerage calls, and order calls in the scaffold.
- The current workflow guardrails still prohibit real market data fetching,
  downloads, credentials, live trading, paper trading, brokerage integration,
  order execution, and profitability claims.

Decision:

- Do not add a runnable LEAN draft in the next stage.
- Add a readiness decision documenting that runnable LEAN code is not yet
  approved under current guardrails.
- Make the next safe LEAN stage a documentation-only signal-only draft design.

Rationale:

- A normal runnable LEAN algorithm would likely use `AlgorithmImports`,
  `QCAlgorithm`, platform data subscriptions or history, scheduled events,
  portfolio targets, orders, fills, fee models, and slippage models.
- Those pieces may be appropriate in a future simulated LEAN backtest, but they
  need an explicit scope boundary before implementation so they are not
  confused with live trading, brokerage integration, real data fetching, or
  profitability evidence.
- The signal-only design stage can preserve forward progress while keeping the
  implementation bounded and reviewable.

Consequences:

- Future LEAN code remains blocked until the project defines a signal-only
  code boundary and static validation plan.
- The existing non-executing scaffold remains unchanged.
- No source code, tests, research scripts, reports, data access, execution
  behavior, credentials, or performance claims are changed by this decision.

Follow-up:

- Create a documentation-only LEAN signal-only draft design after this decision
  is reviewed and merged.
- If that design cannot avoid runtime, data, credential, order, or
  interpretation risks, stop and document the blocker before code is added.

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
