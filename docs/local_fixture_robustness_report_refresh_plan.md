# Local Fixture Robustness Report Refresh Plan

This documentation-only plan defines how the reviewed all-case, split-aware
synthetic robustness reporting format should later be applied to the committed
synthetic local CSV fixture workflow. It does not modify source code, tests,
research scripts, generated reports, generated experiment logs, data files,
backtester behavior, metrics behavior, factor logic, diagnostics behavior, or
LEAN code.

## 1. Problem

The repository now has two adjacent diagnostic paths:

- the synthetic split-aware robustness demo, which reports every configured
  case across train, validation, and test splits and records invalid cases; and
- the committed local CSV fixture workflow, which exercises loader, benchmark,
  liquidity, factor, split, IC, Rank IC, quantile spread, and diagnostic-only
  volume-aware slippage wiring on tiny committed synthetic fixtures.

The local fixture report is useful as a smoke check, but the next refresh
should not simply append more favorable metrics. Before any behavior or
generated-output change, the fixture path needs a reviewed plan for preserving
all-case rows, invalid rows, split coverage, cost and slippage assumptions,
and guardrails.

The integration problem this plan solves is reporting discipline: future local
fixture robustness output should show all configured fixture cases and their
failure modes without implying real-data evidence, strategy validation,
execution realism, tradeability, or profitability.

## 2. Current Boundary

The future refresh may use only committed synthetic fixtures and existing local
diagnostic helpers unless a later PR explicitly scopes and tests a narrower
change. It must not use user-provided data, fetch real data, call vendor APIs,
use credentials, connect to brokerage, place orders, add live or paper trading,
or make profitability claims.

Current artifacts that define the boundary:

- `research/local_csv_fixture_workflow_demo.py`
- `tests/test_local_csv_fixture_workflow_demo.py`
- `reports/local_csv_fixture_workflow_demo.md`
- `reports/experiment_logs/local_csv_fixture_workflow_demo.json`
- `reports/experiment_registry.md`
- `docs/synthetic_robustness_validation_plan.md`
- `docs/post_synthetic_robustness_generated_output_checkpoint.md`

The current local fixture workflow already records split metadata, benchmark
alignment, caveats, synthetic-only inventory review, liquidity diagnostics,
factor diagnostics, and a diagnostic-only volume-aware slippage smoke summary.
The future work should reorganize or extend those outputs only after tests
prove that every configured case and every split remains visible.

## 3. Required Future Inputs

Any future implementation PR must define the configured fixture cases before
writing refreshed output. At minimum, each case should have:

- stable `case_id` and human-readable case label.
- fixture input paths limited to committed synthetic fixture files.
- factor or diagnostic path under test, such as existing `alpha_009`,
  `alpha_012`, liquidity-mask wiring, or diagnostic-only volume-aware
  slippage wiring.
- chronological split policy and explicit split windows.
- IC, Rank IC, quantile spread, coverage, and missing-data minimums.
- benchmark assumption and date-alignment rule.
- fixed transaction-cost assumption, if reported.
- fixed-bps slippage assumption, if reported.
- volume-aware slippage mode: `absent`, `diagnostic_only`, or another reviewed
  value from a prior implementation.
- zero-slippage diagnostic flag, if fixed-bps slippage output is included.
- output-writing mode and generated artifact paths.

The local fixture path must continue to distinguish diagnostic target weights
used for helper wiring from factor-ranked weights, portfolio construction,
orders, fills, or trade recommendations.

## 4. Required Future Behavior

Future local fixture robustness output should:

- report every configured case, including invalid or insufficient cases.
- report every configured split for each case, even when a split has no valid
  metric observations.
- keep invalid and insufficient rows in the Markdown report and JSON
  experiment log with explicit reasons.
- keep deterministic row and column ordering.
- preserve date alignment: feature inputs must not use future returns,
  same-period target returns, future universe membership, or future volume.
- state benchmark, universe, cost, slippage, and execution-timing assumptions
  next to the diagnostics they affect.
- keep fixed-bps transaction costs, fixed-bps slippage, and volume-aware
  slippage diagnostics separately inspectable.
- keep zero-cost or zero-slippage output labeled as diagnostic only.
- avoid ranking or selecting cases by favorable outcomes.
- avoid language that presents fixture metrics as real-market evidence,
  strategy validation, execution realism, tradeability, or profitability.

If a future change introduces a helper that builds an all-case summary, the
helper should be pure and deterministic so it can be unit tested without
writing generated reports.

## 5. Stop Conditions And Defaults

Future implementation must stop before output refresh when any of these are
true:

- user-provided local CSV files are required.
- real data, vendor APIs, downloads, credentials, secrets, tokens, `.env`
  files, brokerage, live trading, paper trading, or order execution would be
  needed.
- fixture provenance, fixture schema, benchmark alignment, or split windows
  are ambiguous.
- split windows overlap, fall outside the available panel, or leave rows
  unassigned without an explicit invalid-row policy.
- factor inputs cannot be proven to be known before the diagnostic target date.
- rolling windows are incomplete and the case does not explicitly record an
  invalid or insufficient reason.
- missing volume, zero volume, stale volume, or incomplete rolling
  dollar-volume windows would be silently filled, forward-filled, back-filled,
  interpolated, or treated as zero-capacity without an audit field.
- portfolio notional, target weights, or participation caps are invalid for a
  volume-aware diagnostic case.
- excessive participation would be hidden instead of reported through
  rejected or capped trade counts.
- fixed transaction-cost, fixed-bps slippage, and volume-aware diagnostic
  fields cannot remain separately inspectable.
- generated-output refresh is attempted before focused tests cover the new
  behavior.
- wording implies profitability, investment performance, execution realism,
  tradeability, or real-data validation.

Required default handling:

- Missing volume: record missing-volume counts and mark affected
  volume-aware diagnostics invalid or rejected; do not fill missing values.
- Zero volume: record zero-volume counts and zero-capacity diagnostics; do not
  infer executable capacity.
- Stale volume: require an explicit stale-volume rule before use; otherwise
  mark the case invalid.
- Incomplete rolling volume windows: record insufficient-window counts and
  exclude affected observations from capacity-sensitive metrics unless a
  reviewed test covers the alternate behavior.
- Invalid notional: stop with a deterministic error before report/log writing.
- Invalid target weights: stop with a deterministic error or record the case
  invalid before report/log writing.
- Excessive participation: report rejected or capped counts; do not hide the
  breach in aggregate metrics.

## 6. Required Tests Before Implementation

Before any source, research-script, or generated-output change, a future PR
must add or update deterministic tests for:

- all configured fixture cases appearing in the summary.
- all configured splits appearing for every case.
- invalid or insufficient cases remaining visible with reasons.
- deterministic ordering of all-case, all-split rows.
- report and JSON log schema fields for case identity, split identity,
  validity, invalid reason, coverage, and caveats.
- benchmark alignment and split-window audit fields.
- fixed transaction-cost fields staying separate from fixed-bps slippage
  fields.
- volume-aware diagnostic fields staying separate from fixed-bps cost and
  slippage fields.
- zero-slippage diagnostic mode remaining labeled as diagnostic only.
- missing volume, zero volume, stale volume, invalid notional, invalid target
  weights, excessive participation, and incomplete rolling dollar-volume
  windows.
- guardrail text blocking real data, vendor APIs, credentials, brokerage,
  live or paper trading, order execution, and profitability claims.
- `write_outputs=False` still avoiding generated report/log writes when the
  future implementation touches output paths.

Generated Markdown and JSON artifacts should be refreshed only after the
tested behavior is merged or in a separate PR that is explicitly scoped as a
generated-output refresh.

## 7. Required Future Report And Log Fields

Future Markdown report sections should include:

- explicit committed-synthetic-fixture caveat.
- input artifact table.
- split-window table.
- configured-case table.
- all-case, all-split summary table.
- invalid or insufficient case table.
- benchmark assumption section.
- date-alignment section.
- transaction-cost assumption section, if relevant.
- fixed-slippage assumption section, if relevant.
- volume-aware slippage diagnostic section, if relevant.
- zero-slippage diagnostic caveat, if relevant.
- guardrail and non-goals section.
- recommended next action that does not claim profitability.

Future JSON experiment logs should include:

- `experiment_id`.
- `experiment_type`.
- `data_scope`.
- `fixture_paths`.
- `split_policy`.
- `split_windows`.
- `configured_cases`.
- `reported_case_count`.
- `reported_split_row_count`.
- `invalid_case_count`.
- `invalid_case_reasons`.
- `metrics_by_case_split`.
- `benchmark_assumption`.
- `execution_timing_assumption`.
- `transaction_cost_bps`.
- `slippage_bps`.
- `zero_slippage_diagnostic`.
- `volume_aware_slippage_mode`.
- `volume_aware_slippage_fields`.
- `cost_fields`.
- `slippage_fields`.
- `guardrail_caveats`.
- `generated_artifacts`.

The experiment registry entry should surface the report path, log path,
synthetic fixture scope, case counts, invalid-case counts, guardrail caveats,
and the absence of real-data interpretation.

## 8. Non-Goals

This plan does not authorize:

- source code changes.
- test changes.
- research-script changes.
- generated report or generated log refresh.
- real data access or interpretation.
- vendor APIs, downloads, or credentials.
- brokerage, live trading, paper trading, order execution, or order routing.
- backtester behavior changes.
- metrics behavior changes.
- factor logic changes.
- diagnostic helper behavior changes.
- LEAN or QuantConnect implementation.
- profitability, investment-performance, tradeability, or execution-realism
  claims.

## 9. Recommended Next PR-Sized Stage

After this plan is reviewed and merged, the next safe stage is a test-first
local fixture robustness/report support implementation. That stage should add
focused tests for all-case, all-split fixture reporting and invalid-row
preservation before changing output-writing behavior. A generated-output
refresh should remain a separate later PR unless the reviewed implementation
scope explicitly includes it and the diff is small.
