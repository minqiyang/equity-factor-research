# Troubleshooting Log

This log records failures, missing prerequisites, confusing environment
behavior, incorrect assumptions, failed checks, and recovery steps.

It is not an experiment log and must not be used to claim profitability or
investment performance.

## How To Update This Log

For technical, methodological, environment, testing, workflow, or reasoning
problems, include:

- original mistake or incorrect assumption.
- consequence.
- exact error or evidence.
- investigation steps.
- correction attempts.
- final fix.
- verification results.
- remaining caveats.
- prevention measures.

---

## 2026-06-08 - Local CSV Inventory Patch Context Mismatch

Original mistake:

- During the local CSV inventory dry-run validator stage, the first combined
  `apply_patch` attempted to add the new source file, tests, engineering-log
  entry, and changelog entry in one patch.
- The patch used a stale `CHANGELOG.md` context that expected
  `docs/user_provided_local_csv_research_plan.md` to be the first item under
  `### Added`.
- After PR #78 merged, `docs/local_csv_study_checklist.md` was the first item.

Consequence:

- `apply_patch` rejected the entire combined patch.
- No repository files were modified by that failed patch, but the stage needed
  to be reapplied in smaller chunks against the current main state.

Evidence:

```text
apply_patch verification failed: Failed to find expected lines in
D:\Users\MINQI\Documents\New project\CHANGELOG.md:
### Added

- Added `docs/user_provided_local_csv_research_plan.md` to define a
  documentation-only plan, scope template, validation gates, stop conditions,
  and future PR-sized stages before any user-provided local CSV result is
  interpreted.
```

Investigation:

- Checked `git status -sb --untracked-files=all` and confirmed the failed
  combined patch left no modified or untracked files.
- Read the top of `CHANGELOG.md` and confirmed PR #78 had inserted the local
  CSV study checklist entry above the user-provided local CSV research plan
  entry.
- Confirmed this was a patch-authoring/context issue only, not a source-code,
  data, CSV-loader, test, trading, credential, or profitability issue.

Correction attempts:

- Did not force the stale patch context.
- Reapplied the source module, tests, API export, engineering-log entry,
  changelog entry, and this troubleshooting note as smaller patches using the
  current file context.

Final fix:

- Added the local CSV inventory dry-run validator and focused tests in scoped
  patches.
- Updated the durable logs using the current post-PR #78 changelog and
  engineering-log context.

Verification:

- Focused and full validation are rerun before this stage is committed and
  opened as a PR.

Remaining caveats:

- This was local patch tooling friction only. It did not change project
  behavior until the corrected patches were applied.

Prevention:

- After syncing a newly merged PR, inspect the exact top-of-file changelog and
  log context before applying broad multi-file documentation patches.
- Prefer smaller patches when recent merged stages have touched the same
  durable logs.

---

## 2026-06-08 - PowerShell PR Body Quoting Error

Original mistake:

- During the local CSV fixture inventory dry-run rehearsal stage, the first
  `gh pr create` command passed a long Markdown PR body inside a PowerShell
  double-quoted argument.
- The body text contained Markdown backticks around file names and commands.
- In PowerShell, backticks are escape characters, so the shell parsed the
  command string before `gh` could receive the intended body.

Consequence:

- PR creation failed on the first attempt.
- No repository files, staged content, commits, branches, or remote PRs were
  modified by the failed command.
- The stage was not complete until the PR body was submitted with
  PowerShell-safe quoting and this recovery was logged.

Evidence:

```text
The string is missing the terminator: ".
CategoryInfo          : ParserError
FullyQualifiedErrorId : TerminatorExpectedAtEndOfString
```

Investigation:

- The failure was a shell parse error, not a GitHub, git, test, source-code,
  data, trading, credential, or profitability issue.
- The command used Markdown backticks inside a double-quoted PowerShell string.
- The repository remained clean after the existing commit, and the failed
  command did not open a PR.

Correction attempts:

- Did not retry the same double-quoted command.
- Recreated the PR body as a PowerShell single-quoted here-string assigned to
  a variable.
- Passed that variable to `gh pr create --body`, so Markdown backticks were
  treated as literal content rather than PowerShell escapes.

Final fix:

- Opened the ready-for-review PR with the here-string body command.
- The resulting PR is
  `https://github.com/minqiyang/ai-equity-factor-research/pull/80`.

Verification:

- `gh pr create` returned the PR #80 URL successfully.
- The failed command did not modify the working tree.
- This troubleshooting entry is added as a follow-up log-only update to the
  same PR branch.

Remaining caveats:

- This was command-line quoting friction only. It did not affect the local CSV
  fixture workflow implementation, generated synthetic report, JSON sidecar
  log, tests, data access, trading scope, or profitability language.

Prevention:

- Use PowerShell here-strings or `--body-file` for long Markdown PR bodies in
  this workspace.
- Avoid PowerShell double-quoted strings for Markdown text containing
  backticks.
- Treat PR creation failures as workflow problems that require durable logging
  when they occur during the staged workflow.

---

## 2026-06-07 - PowerShell Rejected Bash Here-Doc Syntax

Original mistake:

- During the local CSV fixture universe-masked signal smoke stage, a quick
  Python inspection snippet was run with Bash here-doc syntax:
  `python - <<'PY'`.
- The active shell for this workspace is Windows PowerShell, not Bash.

Consequence:

- PowerShell rejected the command before Python ran.
- No repository files were modified by the failed command, but the intended
  inspection of exact masked-signal values still had to be rerun.

Evidence:

```text
At line:2 char:11
+ python - <<'PY'
+           ~
Missing file specification after redirection operator.
The '<' operator is reserved for future use.
```

Investigation:

- The error occurred at shell-parse time, before any Python import or fixture
  workflow code executed.
- The command used a Bash redirection pattern that is not valid PowerShell
  syntax.
- The issue was an environment/command-form mistake, not a data, strategy,
  liquidity, backtest, trading, credential, or profitability issue.

Correction attempts:

- Did not change code or tests in response to the failed command.
- Replaced the Bash here-doc with a PowerShell here-string piped to Python:
  `@' ... '@ | python -`.

Final fix:

- Reran the inspection with PowerShell-compatible syntax and printed the
  `alpha_009` fixture factor, masked signal panel, masked-signal summary, and
  low-coverage dates.

Verification:

- The corrected command completed successfully.
- It confirmed the fixture universe mask keeps only `BBB` on `2024-01-04`,
  the masked `alpha_009` valid observation count is `1`, and low-coverage
  dates are `2024-01-02`, `2024-01-03`, and `2024-01-05`.

Remaining caveats:

- This was a local command syntax issue only. It did not affect repository
  behavior or generated outputs.

Prevention:

- Use PowerShell here-strings or `python -c` for ad hoc Python snippets in
  this workspace.
- Treat shell syntax failures as failed checks and rerun the intended check
  before relying on the result.

---

## 2026-06-07 - Universe-Masked Signal Duplicate-Column Validation Order

Original mistake:

- The first `apply_universe_mask_to_signals()` implementation checked
  duplicate signal columns only after passing `signals` through
  `validate_panel_data()`.
- `validate_panel_data()` is designed for normal unique-column numeric panels.
  With duplicate column labels, `data[column]` can return a DataFrame rather
  than a Series, so the validator may try to read a DataFrame `.dtype`
  attribute before the new helper reports the clearer duplicate-column
  problem.

Consequence:

- A new duplicate-column boundary test failed.
- The helper still rejected the bad input, but the failure path was an
  implementation-detail `AttributeError` rather than the intended auditable
  `ValueError`.

Evidence:

```text
tests/test_liquidity.py::test_apply_universe_mask_to_signals_rejects_duplicate_columns
AttributeError: 'DataFrame' object has no attribute 'dtype'. Did you mean: 'dtypes'?

1 failed, 57 passed
```

Investigation:

- The failure occurred before `_validate_unique_columns(signal_panel,
  "signals")` was reached.
- The root cause was validation order, not masking semantics, real-data
  handling, backtest integration, trading behavior, or profitability language.
- `universe_mask` already checked duplicate columns before dtype validation,
  so the issue was limited to the signal-panel path.

Correction attempts:

- Did not remove or weaken the duplicate-column test.
- Did not modify the shared `validate_panel_data()` helper because this stage
  is scoped to the universe-masked signal adapter.
- Moved the duplicate-column check ahead of `validate_panel_data()` only when
  `signals` is already a pandas DataFrame, preserving the existing non-DataFrame
  type error from the shared validator.

Final fix:

- `apply_universe_mask_to_signals()` now checks duplicate signal columns on
  the raw `signals` DataFrame before numeric panel validation.
- Duplicate labels now raise the intended `ValueError` with
  `columns must not contain duplicates`.

Verification:

```text
python -m pytest -q tests/test_liquidity.py
58 passed
```

Remaining caveats:

- The fix is local to the new adapter. Other helpers that rely directly on
  `validate_panel_data()` were not changed in this Stage 72 PR.

Prevention:

- For future strict panel adapters, validate duplicate labels before selecting
  columns by label or delegating to validators that assume unique columns.

---

## 2026-06-07 - Local CSV Fixture Universe-Mask Test Expectation Drift

Original mistake:

- The first partial update to the local CSV fixture workflow added a
  universe-mask count diagnostic to the report and JSON log, but the existing
  report/log test still asserted the old caveat text
  `not universe construction`.
- That old assertion was correct before the helper existed, but it became stale
  once this stage intentionally began reporting a synthetic universe-mask
  count smoke check.

Consequence:

- The first full test run on the branch failed with one test failure.
- The branch was not safe to commit because the tests no longer described the
  intended workflow boundary: there is now a universe-mask diagnostic, but
  still no tradeable universe study, backtest integration, portfolio
  construction, execution logic, or performance interpretation.

Evidence:

```text
tests/test_local_csv_fixture_workflow_demo.py::test_workflow_report_and_experiment_log_are_created_with_caveats
AssertionError: assert 'not universe construction' in '# Local CSV Fixture Workflow Demo\n...'

1 failed, 416 passed
```

Investigation:

- Inspected the working diff and confirmed the code had intentionally added
  `construct_liquidity_universe()` to the local fixture workflow.
- Checked the generated report text and confirmed it now contains a
  `Liquidity Universe Mask Smoke Check` section with count-only audit output.
- Verified the mismatch was not a real-data, trading, credential, brokerage,
  order-execution, profitability, loader, backtester, or metrics issue.
- Identified the root cause as test expectation drift: the old test was still
  checking for "no universe construction" wording instead of the new, narrower
  "universe-mask count only, no backtest/tradeability integration" boundary.

Correction attempts:

- Did not restore the old wording because that would hide the newly intended
  universe-mask smoke diagnostic.
- Did not weaken the test to ignore the liquidity section.
- Updated the test to assert the new Markdown section, expected count row,
  JSON universe-count diagnostics, low-coverage dates, caveats, and helper
  call count.
- Tightened JSON serialization so the `low_coverage` audit flag remains a
  boolean instead of being serialized as a numeric value.

Final fix:

- `research/local_csv_fixture_workflow_demo.py` now serializes universe-mask
  audit summaries with boolean `low_coverage` values and preserves caveated
  count-only wording.
- `tests/test_local_csv_fixture_workflow_demo.py` now verifies the universe
  mask, summary, low-coverage dates, generated report section, JSON
  diagnostics, caveats, helper reuse, and invalid universe-mask config.
- The default synthetic report and experiment log were regenerated from the
  committed fixture only.

Verification:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
13 passed

python -m pytest -q
417 passed

python -m compileall src tests research
passed
```

Remaining caveats:

- This remains a committed synthetic fixture smoke check only.
- It does not integrate a liquidity universe into the backtester, produce
  weights, create trades, fetch real data, validate market tradeability, or
  support any performance interpretation.

Prevention:

- When a staged PR intentionally changes a caveat boundary from "not present"
  to "present only as a diagnostic," update tests to assert the new positive
  diagnostic contract and the negative guardrails together.
- Keep future liquidity stages split between eligibility counts, universe-mask
  diagnostics, and backtest consumption so stale wording does not blur the
  scope boundary.

---

## 2026-06-07 - Liquidity Universe Missing-Eligibility Downcast Warning

Original mistake:

- The first implementation of `construct_liquidity_universe()` cleaned a
  boolean-or-missing eligibility panel with `fillna(False).astype(bool)`.
- That worked for the current test data, but object-dtype panels containing
  booleans and `NaN` triggered pandas' future silent-downcasting warning.

Consequence:

- The focused liquidity tests passed, but the run emitted a warning that could
  become a future behavior change or hide an avoidable dtype assumption.
- The stage was not ready for commit while validation was warning-clean only by
  coincidence.

Evidence:

```text
tests/test_liquidity.py::test_construct_liquidity_universe_counts_missing_eligibility_before_excluding
FutureWarning: Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated
and will change in a future version.
src\features\liquidity.py:314: clean_mask = eligibility_mask.fillna(False).astype(bool)
```

Investigation:

- The warning came from the missing-eligibility path, where tests intentionally
  use an object-dtype panel so `True`, `False`, and `NaN` can coexist before
  validation.
- Non-missing values were already validated to be actual booleans, so missing
  values did not need string, numeric, or sentinel coercion.

Correction attempts:

- Did not suppress the warning.
- Did not relax the missing-value test.
- Did not replace missing eligibility with forward-fill, backward-fill, zero
  defaults, or any repair policy.
- First replaced `fillna(False).astype(bool)` with `eq(True).astype(bool)`.
- A follow-up robustness check showed that pandas nullable `boolean` dtype can
  preserve `<NA>` after `eq(True)`, causing `astype(bool)` to fail.

Final fix:

- Replaced `fillna(False).astype(bool)` with
  `eq(True).fillna(False).astype(bool)`.
- This keeps only explicit `True` values eligible and maps `False`, `NaN`, or
  nullable `<NA>` values to `False` without relying on object-array
  downcasting.

Verification:

```text
python -m pytest -q tests/test_liquidity.py
44 passed
```

Remaining caveats:

- This helper still consumes synthetic/local panels only. It does not validate
  real-data provenance or make a liquidity rule tradable.

Prevention:

- For future pandas object panels that intentionally preserve missing values,
  prefer explicit boolean comparisons or typed construction over
  `fillna(...).astype(...)` when pandas warns about silent downcasting.

---

## 2026-06-07 - Alpha#012 LEAN Plan Patch Context Mismatch

Original mistake:

- During the Alpha#012 QuantConnect/LEAN plan refresh, the first attempted
  patch used an imprecise context line for the universe filter section in
  `docs/quantconnect_lean_plan.md`.
- The patch expected `Candidate filter:` without matching the exact markdown
  bullet context used in the file.

Consequence:

- `apply_patch` rejected the combined patch before any file changes from that
  patch were applied.
- The documentation stage could not proceed safely until the exact current file
  context was inspected.

Evidence:

```text
apply_patch verification failed: Failed to find expected lines in
D:\Users\MINQI\Documents\New project\docs\quantconnect_lean_plan.md:
Candidate filter:
  - price above a minimum threshold, such as `$5`.
  - positive dollar volume.
  - sufficient daily history for 252-day lookback plus 21-day skip.
  - exclude symbols with missing or stale data at rebalance.
```

Investigation:

- Checked `git status -sb --untracked-files=all` to verify that the failed
  patch did not leave partial changes.
- Used `Select-String` around `Current local status`, `Local component`,
  `Candidate filter`, `Signal Generation Timing`, and
  `Recommended Next LEAN` to inspect the exact current markdown structure.
- Confirmed the failed context was a patch-authoring issue, not a repository
  content problem or test failure.

Correction attempts:

- Did not force the combined patch.
- Reapplied the same intended documentation changes as smaller patches with
  exact nearby context.
- Kept the stage scope documentation-only and limited to the LEAN planning
  docs, durable logs, and changelog.

Final fix:

- Updated `docs/quantconnect_lean_plan.md` in smaller chunks for current
  status, local-to-LEAN mapping, universe/history assumptions, signal timing,
  diagnostic export, and next LEAN-related stage.
- Updated `docs/lean_parity_checklist.md` separately for Alpha#012 assertions
  and coverage requirements.

Verification:

- `git diff --check` passed after the corrected patches.
- Full validation is rerun before the associated PR is committed and opened.

Remaining caveats:

- The failed patch was local tooling friction only. It did not modify source
  code, tests, research scripts, generated reports, data access, execution
  behavior, credentials, brokerage behavior, or performance language.

Prevention:

- For future edits to long markdown files, inspect the exact target section
  before applying broad multi-section patches, and prefer smaller patches when
  the file has recently changed.

---

## 2026-06-07 - Alpha#012 Fixture Rank IC Exact-Float Test Expectation

Original mistake:

- During the Alpha#012 local-fixture diagnostics stage, the new JSON-log test
  asserted that the serialized Alpha#012 Rank IC value for `2024-01-03` was
  exactly `1.0`.

Consequence:

- The focused local CSV fixture workflow test failed even though the diagnostic
  calculation produced the expected perfect rank relationship within normal
  floating-point precision.

Evidence:

```text
tests/test_local_csv_fixture_workflow_demo.py::test_workflow_report_and_experiment_log_are_created_with_caveats
AssertionError: {'2024-01-03': 0.9999999999999999} != {'2024-01-03': 1.0}
```

Investigation:

- The Alpha#012 fixture values on the only valid diagnostic date have two
  overlapping assets, so the expected Rank IC is effectively 1.
- The value is computed through pandas/Spearman correlation and JSON
  serialization, which can represent the result as `0.9999999999999999`
  instead of exactly `1.0`.
- This was a test-expectation precision issue, not a workflow, alignment,
  missing-data, or guardrail failure.

Correction attempts:

- The diagnostic calculation was not changed.
- The test was not weakened to ignore the diagnostic.
- The assertion was changed to keep exact `None` checks for missing dates while
  using `pytest.approx(1.0)` for the finite Rank IC value.

Final fix:

- Updated `tests/test_local_csv_fixture_workflow_demo.py` to compare the
  finite Alpha#012 Rank IC JSON value with approximate floating-point equality.

Verification:

- The focused workflow test was rerun after the assertion fix:
  `python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py`
  reported 13 passed.

Remaining caveats:

- Exact JSON equality remains useful for structural fields and missing dates,
  but floating correlation values should use tolerance-based comparisons.

Prevention:

- Future tests for Pearson, Spearman, IC, Rank IC, and other floating
  diagnostics should assert exact structure and use approximate comparisons for
  finite computed floats.

---

## 2026-06-07 - Alpha#012 Hand-Calculation Test Sign Error

Original mistake:

- During the first Alpha#012 implementation stage, the hand-calculated
  expected value for ticker `BBB` on the first valid date was written as
  `+1.0`.
- The public formula being implemented is:

```text
sign(delta(volume, 1)) * (-1 * delta(close, 1))
```

- For that test row, volume decreased from `50.0` to `40.0`, so
  `sign(delta(volume, 1))` is `-1`. Close decreased from `20.0` to `19.0`,
  so `(-1 * delta(close, 1))` is `+1`. The correct product is `-1`.

Consequence:

- The focused WorldQuant alpha test suite failed before the stage could be
  validated.
- No files were staged, committed, pushed, or merged while the failure was
  present.

Evidence:

```text
tests/test_worldquant_alphas.py::test_alpha_012_matches_public_formula_hand_calculation

E       assert np.float64(-1.0) == 1.0 +/- 1.0e-06
E         Obtained: -1.0
E         Expected: 1.0 +/- 1.0e-06
```

Investigation:

- Recomputed the formula terms for the failing row.
- Confirmed the implementation output matched the source formula.
- Confirmed only the test expectation had the wrong sign.

Correction attempts:

- Did not change the implementation because the implementation matched the
  reviewed formula.
- Corrected the expected value in
  `tests/test_worldquant_alphas.py::test_alpha_012_matches_public_formula_hand_calculation`
  from `+1.0` to `-1.0`.

Final fix:

- The test now matches the hand calculation for both falling-volume /
  falling-close and mixed-sign cases.

Verification:

- Focused and full validation are rerun in the Alpha#012 PR after this fix.

Remaining caveats:

- Alpha#012 is still a research feature only. Passing formula tests does not
  imply factor validity, strategy performance, or profitability.

Prevention:

- For future formula tests, write each hand-calculated term explicitly before
  asserting the final product, especially when nested signs are involved.
- Keep any failed formula-transcription or hand-calculation check visible in
  this log before committing.

---

## 2026-06-06 - Reversal Missing-Value Test Assumed Full Interior Window

Original mistake:

- Wrote the first short-term reversal missing-value test as if every row inside
  the lookback span had to be non-missing.
- The implemented and documented formula uses explicit current and trailing
  price anchors:

```text
-(price[t] / price[t - lookback_periods] - 1)
```

- Under that anchor-based formula, a missing non-anchor price inside the span is
  not used in the calculation and should not force the score to `NaN`.

Consequence:

- The focused reversal test suite failed even though the implementation
  matched the explicit anchor formula.
- The failure exposed that the test was enforcing an unstated rolling-window
  completeness policy rather than the chosen return-anchor policy.

Evidence:

```text
tests/test_reversal.py::test_short_term_reversal_does_not_fill_missing_values

AssertionError: assert np.False_
where np.False_ = np.isnan(np.float64(0.09999999999999998))
```

Investigation:

- Checked the failing row and confirmed `lookback_periods=2` at
  `2024-03-31` used the valid anchors `2024-01-31` and `2024-03-31`.
- Confirmed the missing value on `2024-02-29` was an interior non-anchor value.
- Compared the design to the existing momentum implementation, which also uses
  explicit anchors rather than requiring every interior row to be present.

Correction attempts:

- Did not change the implementation to require full interior windows because
  that would silently change the stated reversal formula and make it less
  consistent with the existing momentum feature style.
- Updated the test to assert the valid anchor-based score for the interior-gap
  row and retain `NaN` expectations for missing current or trailing anchors.

Final fix:

- `tests/test_reversal.py` now verifies that missing anchor values produce
  `NaN`, while a missing non-anchor row does not alter the explicit
  anchor-based return calculation.

Verification:

```text
python -m pytest -q tests/test_reversal.py
13 passed
```

Remaining caveats:

- If a future reversal definition needs a full-window cumulative-return or
  rolling-quality policy, it should be added as a separately named helper with
  its own tests rather than changing this anchor-based feature silently.

Prevention:

- When testing feature missing-data behavior, first identify exactly which
  observations the formula consumes.
- Keep formula-level tests aligned with the documented calculation instead of
  adding stricter data-quality requirements implicitly.

---

## 2026-06-06 - PowerShell Multi-Path Listing Command Failed

Original mistake:

- During the post-liquidity checkpoint review, attempted to list files across
  multiple directories with `Get-ChildItem -Path src/features tests research
  reports -File -Recurse`.
- This syntax treated later path tokens as positional arguments instead of as
  a single array passed to `-Path`.

Consequence:

- The exploratory file listing failed and did not produce evidence for the
  checkpoint report.
- No repository files were modified by the failed command.

Evidence:

```text
Get-ChildItem : A positional parameter cannot be found that accepts argument 'research'.
```

Investigation:

- Confirmed the failure was command syntax, not a repository-state issue.
- Replaced the PowerShell command with `rg --files src/features tests research
  reports`, which accepts multiple search roots and produced the intended
  evidence list.

Correction attempts:

- Did not retry with broad or destructive filesystem operations.
- Used `rg --files` for the file inventory and a focused `rg -n` search for
  implemented helper functions.

Final fix:

```text
rg --files src/features tests research reports | Sort-Object
rg -n "def factor_information_coefficient|def factor_rank_information_coefficient|def factor_quantile_spread|def make_train_validation_test_split|def average_daily_volume_eligibility|def average_dollar_volume_eligibility" src tests research
```

Verification:

- The corrected commands listed the current feature, test, research, and report
  files.
- They confirmed that diagnostics, validation split, and liquidity helper
  functions already exist.

Remaining caveats:

- This was a tooling syntax issue only; it did not affect source code,
  tests, generated reports, data access, trading behavior, or experiment
  results.

Prevention:

- Prefer `rg --files` for multi-root file inventories.
- When using PowerShell `Get-ChildItem` with multiple paths, pass an explicit
  array such as `-Path @("src/features", "tests", "research", "reports")`.

---

## 2026-06-05 - Local CSV Fixture Split Table Formatter Failure

Original mistake:

- Reused the local CSV fixture workflow's existing Markdown table formatter for
  the new split summary table.
- That formatter assumed every DataFrame index value was a date and converted
  each index through `pd.Timestamp(index)`.
- The new split summary index values are labels: `train`, `validation`, and
  `test`.

Consequence:

- The workflow could compute split diagnostics, but report generation failed
  whenever the split summary table was rendered.
- This broke focused tests that create the local CSV fixture workflow report.

Evidence:

```text
tests/test_local_csv_fixture_workflow_demo.py::test_workflow_report_and_experiment_log_are_created_with_caveats
tests/test_local_csv_fixture_workflow_demo.py::test_main_writes_report_to_requested_path
tests/test_local_csv_fixture_workflow_demo.py::test_workflow_text_contains_only_caveated_profitability_language

pandas._libs.tslibs.parsing.DateParseError:
Unknown datetime string format, unable to parse: train
```

Investigation:

- Confirmed that the factor, forward-return, IC, Rank IC, and quantile-spread
  computations completed before report writing.
- Traced the failure to `_format_markdown_table(result.split_summary)`.
- Confirmed that `_format_markdown_table()` was date-table-specific and should
  still be used for date-indexed IC and quantile-spread diagnostics.
- Confirmed that the new split summary needed a labeled-index renderer rather
  than date parsing.

Correction attempts:

- First added `_format_labeled_index_markdown_table()` and used it only for
  `result.split_summary`, leaving the existing date-indexed table formatter in
  place for diagnostic date tables.
- Reran focused tests. Report generation then succeeded, but one report-text
  assertion exposed that count-like split summary columns were formatted as
  `0.0000` because the row dtype was widened by mean columns.
- Extended `_format_table_value()` so count-like fields ending in
  `_observations` or `_valid_dates` render as integers, matching the report's
  diagnostic-count semantics.

Final fix:

- Split-summary rendering now uses a labeled-index Markdown formatter with an
  explicit `split` index label.
- Count-like split summary fields now render as integers while mean IC fields
  remain decimal values and missing means remain `NaN`.

Verification:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
12 passed

python -m pytest -q
309 passed

python -m compileall src tests research
passed
```

Remaining caveats:

- The fixture split has only four dates, so train and validation windows are
  intentionally tiny. The report labels this as a synthetic fixture wiring
  check, not a real train/validation/test research study.

Prevention:

- Do not reuse date-specific renderers for non-date-index tables.
- When adding report tables with mixed count and mean columns, inspect the
  rendered Markdown as well as the underlying DataFrame.
- Keep focused tests that write report and JSON outputs, not only tests that
  inspect in-memory result objects.

---

## 2026-06-05 - Rebase Continue Opened Editor And Timed Out

Original mistake:

- Ran `git rebase --continue` without forcing a non-interactive editor during
  the split-aware IC / Rank IC demo branch rebase.
- In this Windows environment, Git opened Notepad++ for the commit message
  rather than completing the rebase directly.

Consequence:

- The shell command timed out while Git waited for the editor-backed commit to
  finish.
- The rebase remained in progress with all conflict resolutions staged.
- No branch was pushed and no PR was opened while the rebase was incomplete.

Evidence:

```text
command timed out after 124276 milliseconds

git status
interactive rebase in progress; onto 4884a53
all conflicts fixed: run "git rebase --continue"

Get-CimInstance Win32_Process
git.exe rebase --continue
git commit -n --no-gpg-sign -F .git/rebase-merge/message -e --allow-empty
notepad++.exe ... .git/rebase-merge/message
```

Investigation:

- Checked `git status` and confirmed the rebase was still waiting at the final
  continue step with all intended files staged.
- Inspected process command lines and confirmed the timeout was caused by the
  editor-backed commit step, not by a new merge conflict.

Correction attempts:

- Stopped only the stuck Git processes by exact PID.
- Left the user-visible Notepad++ process alone.
- Reran the continue step with a non-interactive editor override.

Final fix:

```text
git -c core.editor=true rebase --continue
```

This completed the rebase and rewrote the local split-aware demo commit onto
the latest `main`.

Verification:

```text
Successfully rebased and updated refs/heads/codex/synthetic-split-ic-rank-ic-demo.

python -m pytest -q tests/test_synthetic_split_ic_rank_ic_demo.py
11 passed

python -m pytest -q
308 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

Remaining caveats:

- This was a Git editor configuration issue, not a source-code or test
  failure.

Prevention:

- Use `git -c core.editor=true rebase --continue` for non-interactive rebase
  continuations in this workspace.
- Avoid plain `git rebase --continue` when a previous conflict resolution has
  staged all files and only commit-message confirmation remains.

---

## 2026-06-05 - Split-Aware Demo Rebase Conflict After PR #49 Merge

Original assumption:

- The locally committed split-aware IC / Rank IC demo branch could be
  published after the prior open merge gate cleared.
- PR #49 merged while this continuation was in progress and modified
  `CHANGELOG.md` and `docs/engineering_log.md`, which were also touched by the
  local split-aware demo commit.

Consequence:

- Rebasing `codex/synthetic-split-ic-rank-ic-demo` onto the latest `main`
  stopped with content conflicts in the two overlapping documentation files.
- No branch was pushed and no PR was opened before the conflict was resolved.

Evidence:

```text
CONFLICT (content): Merge conflict in CHANGELOG.md
CONFLICT (content): Merge conflict in docs/engineering_log.md
error: could not apply 0280093... Add split-aware IC Rank IC demo
```

Investigation:

- Confirmed the conflicts were limited to adjacent top-of-file changelog and
  engineering-log entries.
- Confirmed the code and test files from the split-aware demo applied cleanly.
- Confirmed PR #49 was merged and latest `main` passed baseline validation
  before rebasing the prepared branch.

Correction attempts:

- Resolved `CHANGELOG.md` by keeping both the already-merged Apache-2.0
  metadata entries and the new split-aware diagnostic demo entry.
- Resolved `docs/engineering_log.md` by keeping the PR #49 metadata checkpoint
  and the split-aware demo checkpoint as separate durable entries.

Final fix:

- Removed conflict markers and preserved both stages' documentation.
- Kept the split-aware demo scope unchanged: synthetic panels only, no real
  data fetching, no backtest, no broker, no order execution, and no
  profitability claim.

Verification:

```text
rg -n "<<<<<<<|=======|>>>>>>>" CHANGELOG.md docs/engineering_log.md docs/troubleshooting_log.md research/synthetic_split_ic_rank_ic_demo.py tests/test_synthetic_split_ic_rank_ic_demo.py
no matches

python -m pytest -q tests/test_synthetic_split_ic_rank_ic_demo.py
11 passed

python -m pytest -q
308 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

Remaining caveats:

- This was a documentation merge conflict only. It did not indicate a
  functional failure in the split helper, diagnostic helpers, or demo logic.

Prevention:

- When a local branch waits behind an external PR gate, expect overlapping log
  and changelog conflicts after the gate merges.
- Rebase onto the newly merged `main`, preserve both log entries, and rerun
  focused plus full validation before pushing.

---

## 2026-06-05 - Validation Split Empty-Test Expectation Mismatch

Original mistake:

- The first version of `tests/test_validation.py` included a parameterized
  empty-window test case with `validation_end="2024-01-06"` while the default
  `test_end` was also the final index date, `2024-01-06`.
- The test expected the helper to report an empty test split.

Consequence:

- The focused validation test failed even though the helper was rejecting the
  input for a stricter and earlier reason: the configured split boundaries did
  not satisfy the required chronological order.
- No files were committed, pushed, or merged before the failure was fixed.

Evidence:

```text
tests/test_validation.py::test_make_train_validation_test_split_rejects_empty_windows[2024-01-02-2024-01-06-test split]
AssertionError: Regex pattern did not match.
Expected regex: 'test split'
Actual message: 'split boundaries must satisfy train_end < validation_end < test_end'
```

Investigation:

- Reviewed the failing case against the helper contract.
- Confirmed that when `test_end` is omitted, the helper uses the final
  available date as the test boundary.
- Confirmed that `validation_end == test_end` violates the intended strict
  boundary ordering before any empty-window check should run.
- Confirmed that another test already covers this invalid boundary-order case.

Correction attempts:

- No code change was needed because the helper behavior was correct.
- Removed the contradictory duplicate parameter from the empty-window test
  case instead of weakening the boundary-order validation.

Final fix:

- Kept strict `train_end < validation_end < test_end` validation.
- Kept empty-window tests for train and validation windows where the boundary
  ordering remains meaningful.
- Left the `validation_end == test_end` case covered by the invalid-boundary
  test.

Verification:

```text
python -m pytest -q tests/test_validation.py
25 passed

python -m pytest -q
297 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

Remaining caveats:

- The helper is intentionally limited to chronological date-window splitting.
  It does not perform model selection, calculate returns, or interpret any
  diagnostic result.

Prevention:

- For future split tests, separate invalid-boundary-order cases from
  empty-window cases.
- When a helper performs staged validation, assert the earliest intended
  validation failure rather than a later condition that cannot be reached.

---

## 2026-06-04 - README Diff Filter Regex Error

Original mistake:

- During the GitHub landing-page polish scope review, an optional
  `Select-String` diff-filter command used a regex that included an unescaped
  `[` character.

Consequence:

- The optional filtered diff display failed before printing its intended
  heading summary.
- No repository files were modified by the failed command, and the required
  validation checks had already passed, but the diff review needed to be rerun
  with a valid command before commit.

Evidence:

```text
Select-String : The string ... is not a valid regular expression:
Unterminated [] set.
```

Investigation:

- The failing pattern included alternatives such as `^\+![` without escaping
  the bracket.
- The failure was isolated to the optional presentation filter, not to
  Markdown, tests, link checking, or repository content.

Correction attempts:

- The invalid regex was not reused.
- The diff review was rerun with simpler `git diff --stat` and
  `Select-String -SimpleMatch` commands.

Final fix:

- Used fixed-string matching for README section headings and the visual asset
  reference.

Verification:

- The rerun diff review showed the intended README sections and visual asset
  reference.
- `git status --short --untracked-files=all` still showed only the intended
  documentation and asset files.

Remaining caveats:

- The failed command was an inspection aid only; it did not affect repository
  content.

Prevention:

- Prefer `Select-String -SimpleMatch` for literal diff-heading checks.
- Escape regex metacharacters when using `Select-String -Pattern`.

---

## 2026-06-04 - Parallel Pull And State Check Race

Original mistake:

- During the continuation after PR #41 was open, `git pull --ff-only origin
  main` was run in parallel with `git status` and `git log`.

Consequence:

- The `git log` output could show the pre-pull commit while the pull was
  fast-forwarding `main`.
- No files were edited, staged, committed, pushed, or merged during the
  ambiguous state check, but the state evidence needed to be refreshed before
  choosing the next stage.

Evidence:

- `git pull --ff-only origin main` fast-forwarded from the PR #40 merge to the
  PR #41 merge.
- The parallel `git log` output still showed the PR #40 merge as `HEAD`.

Investigation:

- Treated the parallel state output as potentially stale.
- Reran `git status`, `git log`, `gh pr view 41`, and `gh pr list --state
  open` after the pull completed.

Correction attempts:

- No failed correction attempt occurred. The recovery was to rerun the state
  checks after the branch-changing command completed.

Final fix:

- Used the post-pull state as authoritative.
- Confirmed `main` was at the PR #41 merge commit before selecting the next
  stage.

Verification:

- `git log --oneline --decorate -8` showed `main` at the PR #41 merge commit.
- `gh pr view 41` confirmed PR #41 was merged.
- `gh pr list --state open` returned no open pull requests.
- `python -m pytest -q` reported 264 passed.
- `python -m compileall src tests research` passed.

Remaining caveats:

- Parallel shell commands are appropriate for independent reads only when no
  command mutates the working tree, branch pointer, or index.

Prevention:

- Do not run `git pull`, `git switch`, or other branch-changing commands in
  parallel with status or log reads used as authoritative evidence.
- After any branch-changing command, rerun state checks before selecting a
  stage or editing files.

---

## 2026-06-04 - Parallel Read And Branch Switch Race

Original mistake:

- During a long-running workflow continuation after PR #40, file reads for
  roadmap documents were run in parallel with `git switch main`.

Consequence:

- Some displayed document output could have come from the pre-switch branch
  rather than the synced `main` checkout.
- No files were edited, staged, committed, pushed, or merged during this
  ambiguous read window, but the evidence used for next-stage selection needed
  to be refreshed from the authoritative current branch.

Evidence:

- The parallel output showed PR #40 scaffold content while the branch switch
  was still occurring.
- Because the file reads and branch switch were independent parallel tool
  calls, their exact ordering was not guaranteed.

Investigation:

- Treated the parallel-read output as potentially stale instead of relying on
  it for stage selection.
- Confirmed local `main` was then fast-forwarded to the PR #40 merge commit.
- Reread current scaffold and planning documents from the synced `main`
  checkout before selecting the next stage.

Correction attempts:

- No failed correction attempt occurred. The immediate recovery was to rerun
  state checks and reread the relevant current files after `main` was synced.

Final fix:

- Used the post-pull `main` state as authoritative for the next-stage decision.
- Selected a documentation-only LEAN scaffold review checklist based on the
  merged PR #40 scaffold and current planning documents.

Verification:

- `git log --oneline --decorate -8` showed `main` at the PR #40 merge commit.
- `gh pr view 40` confirmed PR #40 was merged.
- `gh pr list --state open` returned no open pull requests.
- `python -m pytest -q` reported 264 passed.
- `python -m compileall src tests research` passed.

Remaining caveats:

- Parallel file reads are safe only when the working tree reference is stable.
  They are not reliable while a branch switch or pull is changing the checkout.

Prevention:

- Do not run branch-changing commands in parallel with file reads whose content
  is used for stage selection.
- After any branch switch or pull, rerun state checks and reread relevant
  roadmap files before editing.

---

## 2026-06-04 - LEAN Scaffold README Guardrail Phrase Mismatch

Original mistake:

- The first version of `lean/README.md` described the same guardrail as
  "real data downloads" and "real market data fetching or downloads", but the
  new static guardrail test expected the exact phrase `no real market data`.

Consequence:

- The focused scaffold test failed even though the intended guardrail was
  present in less exact wording.

Evidence:

```text
tests/test_lean_smoke_test_scope.py::test_lean_scaffold_readme_preserves_guardrails
AssertionError: assert 'no real market data' in ...
```

Investigation:

- Compared the failing expected phrase with `lean/README.md`.
- Confirmed the README prohibited real data downloads but did not include the
  exact wording required by the static test.
- Confirmed this was a documentation/test wording mismatch, not an
  implementation of real data access.

Correction attempts:

- The test was not weakened and the guardrail expectation was not removed.
- First correction attempt added `no real market data path`, but the line wrap
  split the phrase as `no\nreal market data`, so the exact string check still
  failed.
- Second correction attempt placed `no real market data` on one line, but the
  focused test then exposed that other exact README phrases such as
  `no live trading` and `no brokerage` were still implied rather than written
  directly.

Final fix:

- Updated `lean/README.md` to include an `Explicit Guardrail Phrases` section
  containing the exact static-review phrases required by the test.

Verification:

- The focused test and full validation were rerun after the README fix:
  `python -m pytest -q tests/test_lean_smoke_test_scope.py` reported
  6 passed, `python -m pytest -q` reported 264 passed,
  `python -m compileall src tests research` passed,
  `python -m compileall lean` passed, and `git diff --check` passed with
  Windows line-ending conversion warnings only.

Remaining caveats:

- Exact-phrase guardrail tests can fail on equivalent wording. In this case
  the explicit wording is useful because it makes the human-facing README
  clearer.

Prevention:

- When adding static documentation guardrail tests, copy the required caveat
  phrases directly into the human-facing document during the same edit pass.

---

## 2026-06-04 - Stage Edits Started Before Branch Creation

Original mistake:

- During the synthetic IC / Rank IC diagnostics stage, implementation edits
  began after syncing `main` but before creating the dedicated stage branch.

Consequence:

- The worktree had uncommitted stage changes on local `main`.
- No files were staged, committed, pushed, or merged, and the remote `main` was
  not affected, but the local workflow temporarily violated the project rule to
  use a separate branch for each stage.

Evidence:

- The startup checks showed the repository on `main` after PR #32 was merged
  and pulled.
- After implementing the helper and tests, `git diff --name-only` showed local
  changes in `docs/engineering_log.md`, `src/features/diagnostics.py`, and
  `tests/test_diagnostics.py` before a stage branch had been created.

Investigation:

- Confirmed the issue was a workflow sequencing error, not a source-code
  correctness failure.
- Confirmed the changes were still unstaged and uncommitted, so they could be
  moved safely onto a branch without rewriting history or touching remote
  state.

Correction attempts:

- No failed correction attempt occurred. The direct recovery path was to create
  the branch from the current `main` state while preserving the unstaged
  changes.

Final fix:

- Ran `git switch -c codex/synthetic-ic-rank-ic-diagnostics`.
- The uncommitted stage changes moved onto the dedicated branch.

Verification:

- `git branch --show-current` returned
  `codex/synthetic-ic-rank-ic-diagnostics`.
- `git status -sb --untracked-files=all` showed only intended unstaged files on
  that branch before commit review.

Remaining caveats:

- The branch was created after edits instead of before edits. The final branch
  diff is still reviewable, but the sequencing mistake should remain visible in
  the durable log.

Prevention:

- After syncing `main` and passing baseline validation, create the stage branch
  before applying any patch.
- Treat the branch creation step as part of the pre-edit checklist, not as a
  pre-commit cleanup step.

---

## 2026-06-03 - PowerShell Search Pattern Quoting Error

Original mistake:

- During the WorldQuant catalog refresh scope review, a stale-text `rg` search
  used a PowerShell double-quoted string that contained Markdown backticks.

Consequence:

- The search command failed before checking the target documents.
- No repository files were modified by the failed command, and baseline tests
  had already passed, but the intended stale-text check still needed to be
  rerun.

Evidence:

```text
The string is missing the terminator: ".
CategoryInfo          : ParserError
FullyQualifiedErrorId : TerminatorExpectedAtEndOfString
```

Investigation:

- The failing pattern included `` `alpha_009` `` inside a PowerShell
  double-quoted command string.
- PowerShell treats the backtick as an escape character, so the shell parsed
  the command incorrectly before `rg` could run.

Correction attempts:

- The failed double-quoted command was not reused.
- The check was rerun with a single-quoted PowerShell pattern so Markdown
  backticks were treated as literal characters.

Final fix:

- Reran the stale-text search successfully with single quotes around the regex
  pattern.

Verification:

- The corrected search completed.
- The only remaining match was an older 2025 historical engineering-log entry,
  not the refreshed `docs/worldquant_alpha_catalog.md`.
- The catalog no longer contains the stale current-state text that said no
  alpha was implemented.

Remaining caveats:

- Historical logs can correctly preserve older milestone wording and should not
  be rewritten unless they are explicitly misleading as current guidance.

Prevention:

- Use single-quoted PowerShell strings for `rg` patterns that contain Markdown
  backticks.
- Treat shell quoting failures as failed checks and rerun the check before
  committing.

---

## 2026-06-03 - Missing Long-Running Workflow Control Files

Original assumption:

- The continuation request referenced
  `docs/codex_long_running_controller.md`, `docs/decision_log.md`,
  `docs/troubleshooting_log.md`, `CHANGELOG.md`, and
  `scripts/audit-skills.ps1` as files to read before continuing.

Consequence:

- Future Codex sessions could not rely on those files for startup order,
  durable decisions, troubleshooting history, changelog review, or Skill audit
  checks.
- The staged workflow Skill existed, but supporting controller and log
  artifacts were incomplete.

Evidence:

```text
MISSING docs\codex_long_running_controller.md
MISSING docs\decision_log.md
MISSING docs\troubleshooting_log.md
MISSING CHANGELOG.md
MISSING scripts\audit-skills.ps1
```

Investigation:

- Synced latest `main` after PR #27 was merged.
- Confirmed the repository was clean and had no open PRs.
- Read `README.md`, `AGENTS.md`,
  `.agents/skills/staged-quant-workflow/SKILL.md`,
  `docs/engineering_log.md`, and `docs/project_overview.md`.
- Listed `docs/`, `.agents/skills/`, and `scripts/` paths to confirm the
  referenced files were absent rather than overlooked.

Correction attempts:

- No failed correction attempt occurred in this stage. The missing files were a
  repository scaffolding gap, not a failing code path.

Final fix:

- Added `docs/codex_long_running_controller.md`.
- Added `docs/decision_log.md`.
- Added `docs/troubleshooting_log.md`.
- Added `CHANGELOG.md`.
- Added `scripts/audit-skills.ps1`.
- Updated `.agents/skills/staged-quant-workflow/SKILL.md` to reference the
  controller and audit script.
- Updated `docs/engineering_log.md` with the workflow-control scaffolding
  milestone.

Verification:

- `python -m pytest -q`: 209 passed.
- `python -m compileall src tests research`: passed.
- `.\scripts\audit-skills.ps1`: passed for 1 Skill file.
- `git diff --check`: passed with Windows line-ending conversion warnings only.

Remaining caveats:

- The audit script checks local Skill file structure only. It does not prove
  that a Skill is semantically complete.
- The controller should stay concise and should not become a substitute for
  current repo and PR state checks.

Prevention:

- Future long-running workflow continuations should read the controller and
  logs first.
- Missing expected controller or log files should be treated as workflow
  infrastructure gaps before new research implementation begins.
