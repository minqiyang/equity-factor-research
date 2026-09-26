# M4.7a-0 Implementation Report: Statistical and Portfolio Core on Golden Fixtures

- Task/attempt: `m4_7a0-engine-labels-and-wrapper-a1`
- Card: `coord/v8_review_20260923/card_m4_7a0_engine_labels_and_wrapper.md`
- Operative plan: `coord/plans/m4_7_binding_plan.md` Revision 11, SHA-256
  `6541db93336e9181ebf3ad2f066b7b17f4550a17565036c2db5a5d82872a6407`
  (verified), sections 7.2 (a-0), 3.5, 4, 6.2, 6.8, 6.9.
- Branch: `claude/m4_7a0-engine-labels-and-wrapper`, worktree
  `/private/tmp/efr-m47a0-core-20260925`, baseline
  `49eacdd4ce69fe1db9b779bfb7cc975d8b5950d3`.
- State: implemented and verified in the working tree. Nothing is committed,
  pushed, or opened as a PR.
- Environment: Python 3.12.13, pandas 3.0.6, NumPy 2.5.3 (`.venv`).
- Evidence ceiling: synthetic golden fixtures only. No vendor file, snapshot,
  network access, or private data was read. No profitability or
  predictability claim follows from this stage.

## Result

All deliverables in the card are implemented. The 91 new tests pass. The
2,716 pre-existing tests pass except one: the handoff-lag test compares against
`HEAD~1` and passes once the branch holds its commit (evidence below). Ruff,
`compileall`, and `git diff --check` pass.

## Deliverables

### 1. Engine consideration bases, v2 contract, and mask wrapper (section 3.5)

| Item | Location | Behavior |
| --- | --- | --- |
| `ACCEPTED_TERMINAL_BASES` | `src/backtest/portfolio.py` | Frozen set of the cash, stock, and mixed completion-date labels; `long_short.py` imports the engine helpers |
| `_prepare_terminal_events` | same | Accepts any label in the set; every other string (including case and whitespace variants) raises `terminal_events_invalid`. Schema, reference-row, `known_at`, and settlement arithmetic are unchanged |
| `terminal_basis_counts` | both engines' `assumptions` | Count per accepted label, zero for absent labels; omitted on event-free calls |
| `terminal_settlement_contract` | both engines | `prior_observed_close_to_consideration_at_completion_date_row_v2` via `TERMINAL_SETTLEMENT_CONTRACT` |
| `resolve_pit_universe_mask` | `src/backtest/portfolio.py` | `_resolve_pit_universe(universe_mask=None, ...)` over `_prepare_terminal_events(...)`; no other logic |
| Timing contract | `docs/signal_execution_timing_contract.md` | New subsection "M4.7 consideration bases" inside the M4.4 section: the three labels and return formulas, `L`, `S`, the valuation row `V = row(completion_date)` with `V in {L, S}`, unchanged settlement on `S`, the v2 string, `terminal_basis_counts`, and the wrapper. The M4.4 closing sentence no longer lists stock or mixed consideration as an open gate |
| Existing terminal test | `tests/test_pit_universe_delisting.py` | The cash hand-oracle test keeps the cash label and asserts the v2 string |

### 2. Family A factors and diagnostics (sections 6.2, 6.4, 6.8)

| Item | Location | Behavior |
| --- | --- | --- |
| `calculate_52_week_high_proximity(prices, window=252)` | `src/features/momentum.py` | `price[t] / max(price[t-251..t])`; any missing or non-positive price in the window gives NaN |
| `calculate_rolling_market_beta(returns, market_returns, window=252)` | `src/features/volatility.py` | Rolling `Cov / Var` with `ddof=1`, full window (pairwise-complete); zero market variance gives NaN |
| `calculate_amihud_illiquidity(returns, dollar_volume, window=63)` | `src/features/liquidity.py` | Full-window mean of `abs(r) / dollar_volume`; zero or missing dollar volume makes the term missing |
| Family A definitions | `research/m4_7_family_a.py` | `FAMILY_A` frozen tuple: IDs, read-only parameters, `warmup_rows = (252, 251, 21, 252, 252, 63)`, `higher_is_better`. `family_a_signals(adjusted_close, market_adjusted_close, dollar_volume, s_mask)` computes on unmasked panels, negates `LOW_VOL_252` and `LOW_BETA_252`, and applies `.where(S_mask)`; call parameters come from the frozen tuple |
| `newey_west_long_run_variance(values, lags)` | `src/features/diagnostics.py` | Bartlett LRV with `gamma_k / T`; NaN input raises `ValueError`; empty, constant, non-finite, or non-positive estimates return NaN. `newey_west_mean_tstat` now calls it |
| `mde_from_long_run_variance(lrv, count, z)` | same | `z * sqrt(lrv / count)`; NaN when `lrv` is non-finite or non-positive or `count < 1` |
| `summarize_multiple_testing(..., family_sizes=None, statistic_key="return_test")` | `research/multiple_testing_diagnostics.py` | With `family_sizes`: every record needs a declared `family` (`family_unknown` otherwise); each family's distinct trial count must equal its declared size (`family_size_mismatch`); BY and the other methods run within each family at its size; attempts that disagree on `family` are `conflicting_attempts`. `statistic_key="ic_test"` reads the IC statistics and states the Rank IC null. The default path is unchanged |

### 3. Pure evaluation core (sections 4, 6.3, 6.8, 6.9)

`research/m4_7_common_support.py` (integer rows on the discovery calendar):

| Function | Plan element |
| --- | --- |
| `scheduled_reset_rows(calendar)` | `R`, the last row of each month; equals the engine's `_get_rebalance_dates(calendar, "ME")` (tested) |
| `signal_eligibility(mask, bars)` | `S_mask = M.shift(-1, fill_value=False) & B` (section 2.5) |
| `holding_cells(mask, reset_rows, d_last)` | `H(a) = [R_entry, R_exit]` per membership run when `R_entry < R_exit` |
| `base_exclusion_cells(...)` | `G_base`: held cells between first and last bar with a missing bar (section 4.1) |
| `gap_windows(g_base, unresolved_rows, reset_rows, d0, d_last)` | Steps 1-2: `Gamma(m) = [m, R2(m) - 1]` or `[m, D_last]`, `U` runs, merge of overlapping or adjacent windows, reasons `missing_bar` and `unresolved_delisting` |
| `peel_terminal_resets(windows, mask, bars, d0)` | Step 4: while `q > p` and some asset has `M[q] & B[q-1] & ~B[q]`, add `(a, q)` to `G_term` (`terminal_reset_missing_bar`) and move the window start to `q` |
| `support_segments(windows, d0, d_last)` | Steps 3 and 5: complements of `W`, `anchor = p - 1`, valid iff `q - p + 1 >= 42` |
| `max_reset_to_reset_rows(reset_rows, d0, d_last)` | Largest consecutive reset gap in `[D0, D_last]` |
| `common_support_schedule(calendar, bars, mask, unresolved_rows, d0)` | Sections 4.1-4.2 end to end, returning `SupportSchedule` with `g_base`, `g_term`, windows with reasons and peeled-row counts, segments, `excluded_rows`, `excluded_fraction`, and `max_reset_to_reset_rows` |
| `ic_month_set(schedule)` | `T_IC` and the typed exclusions `ic_month_in_gap`, `ic_month_in_dropped_segment`, `ic_month_horizon_unmeasured` (section 4.6) |
| `reset_to_reset_labels(adjusted_close, s_mask, reset_rows, label_resets, engine_events)` | Terminal-aware `label(r, a)` keyed by `t = r - 1`, with per-month `eligible_count`, terminal-aware count, and guard counts `missing_execution_bar`, `missing_horizon_end_bar`. Events pass through the engine's own `_prepare_terminal_events` |
| `monthly_rank_ic(signal, labels, label_resets, min_pairs=100)` | Rank IC per reset from rows `t = r - 1`, `finite_pair_count`, and status `valid`, `ic_month_invalid:insufficient_pairs`, or `ic_month_invalid:undefined_rank_ic` |

`research/m4_7_sp500_pit_rerun.py`: `split_halves` (earlier half takes the
extra month), `sign_stability` (`None` below 24 months per half),
`ic_minimum_detectable_effect` (automatic-lag LRV; undefined below 60 months
or for an undefined LRV), `decide_gate` (section 6.9 rules in order, with
`contrary_rejections`, `kill_reachable_projection`, and `power_status`), and
the constants `Z_EFF = 3.770547` and `Z_SINGLE = 2.801585` derived from
`alpha_eff = 0.05 / (6 * H_6)`.

Composite keying (section 6.3): the builders are unchanged. Labels keyed by
`t = r - 1` feed IC histories indexed by the signal date, with
`execution_lag_periods = 1` and `forward_holding_periods =
max_reset_to_reset_rows`. The T-REG-4b test runs this against
`walk_forward_ic_weighted_composite` and `walk_forward_icir_weighted_composite`.

## Test Evidence

Commands run from the worktree root with `.venv/bin/python`:

```text
python -m pytest -q -p no:cacheprovider -n 4          # full suite
python -m ruff check .                                 # All checks passed!
python -m compileall -q src tests research             # ok
git diff --check                                       # ok
```

Full suite: `1 failed, 2806 passed, 2 skipped` in 229 s. The failure is
`test_handoff_trails_its_base_by_at_most_one_merged_pr`, which reads the base
as `HEAD~1`; with no commit on the branch, `HEAD~1` is `770cfe5` and the
recorded checkpoint `49eacdd` is absent from that history. Evaluating the
test's own `_merges_since` against `HEAD` (the base tip once the branch holds
one commit) gives lag 0 against the maximum of 1. The two skips are the
existing long-double precision skips.

New tests (91):

| File | Count | Oracles |
| --- | --- | --- |
| `tests/test_m4_7_engine_bases.py` | 33 | T-ENG-1 (empty, cash, and stock event tables; equality with `build_pit_membership_mask` without events; unknown-label refusal through the wrapper), T-ENG-2 (both engines, all three labels, four unknown strings, multi-event counts, event-free omission), T-ENG-3, T-TERM-1 and T-TERM-2 engine parts (stock `rho = 0.1111`, mixed `rho = 0.2`, worthless zero proceeds), T-TERM-4 engine part (stock and mixed labels with `known_at = S` raise `terminal_target_invalid`; `known_at = L` completes), T-UNI-11 |
| `tests/test_m4_7_family_a.py` | 12 | T-REG-4 (first finite rows 552, 551, 321, 552, 552, 363 for a first bar at row 300; `MOM_12_1[300] = 0.2598592394492314` and `REV_1M[300] = -0.02122205163752855`; masking; `HIGH_52W = 2/3` at a known maximum; `LOW_BETA_252 = -2` within 1e-10 on a beta-2 series; Amihud `0.01 / 2e6`; interior-gap losses on the 600-row panel: `MOM_12_1` 1 row, `REV_1M` 2, `LOW_VOL_252`, `LOW_BETA_252`, and `HIGH_52W` 200 each (through the panel end), `AMIHUD_ILLIQ_63` 64), beta against a NumPy reference, T-REG-5 (MDE goldens within 1e-6, LRV against a NumPy Bartlett reference within 1e-12 on a 240-row MA(1) series with `lags = 4`, t-statistic reproduction, undefined and refusal cases, halves 121/120) |
| `tests/test_m4_7_common_support.py` | 24 | T-SUP-1, T-SUP-2 (segments, anchors, a 30-row segment dropped, cover of `[D0, D_last]`), T-SUP-8 (review probe Rank IC `-0.5` and price-only `+1.0`; cash, stock, worthless, membership ending inside the horizon, `S_a = e` absent from `Elig(r)`; guard counts; 99 versus 100 pairs; `T_IC` and typed exclusions against a hand count of 5 included, 1 gap, 4 dropped, and 2 unmeasured months), T-SUP-11 (a) through (d) array oracles on the Round 2 calendar, engine confirmation of (a) for the long-only book, the long-short book, and the equal-weight benchmark, T-REG-4b composite part for two builders, empty-axis and misalignment boundaries |
| `tests/test_m4_7_decision.py` | 22 | T-REG-3 (within-family BY, a Family B trial cannot enter Family A, aborted-trial `p = 1` slot, count of 5 refuses, unknown or missing family refuses, `statistic_key="ic_test"`, unchanged default), T-REG-7 (all five outcomes, contrary rejection routed by power with its flag, negative first half, `T_f = 1` and zero variance, realized power independent of `kill_reachable_projection`) |

Round 2 counterexample (T-SUP-11 (a)): the base window is
`[2024-05-16, 2024-05-30]`; peeling adds `(JOIN, 2024-05-15)`, the window
becomes `[2024-05-15, 2024-05-30]`, the first segment is `[D0, 2024-05-14]`
with 358 rows, and `excluded_rows = 12`. All three books raise
`execution_price_invalid` with the segment ending 2024-05-15 and complete with
it ending 2024-05-14. Fixture (b) adds no cell; fixture (c) adds
`(JOIN2, 2024-05-14)` second and ends the segment on 2024-05-13.

Default-path equivalence for `summarize_multiple_testing`: the `49eacdd`
implementation (from `git show HEAD:...`) and the new one produced identical
sorted JSON on an 11-record inventory (valid, negative, failed, unavailable,
and duplicate records) with `family_size` `None` and 15.

## Implementation Decisions And Boundaries

1. `H(a)` comes from the runs of the engine-resolved mask `M`. A settled
   identity's run ends at `S_a`, and every row from `S_a` on lies after
   `L_a`, so `G_base` equals the interval-table definition.
2. `U` enters as a mapping from permanent ID to `S_a`; the
   delisting-candidate classification that builds it belongs to a-2.
3. Gap windows are clipped to `[D0, D_last]` after merging, so a window that
   ends before `D0` counts toward no window cap.
4. Peeling runs one pass in date order (see Ablation).
5. The readiness caps (`count(W) <= 6`, `excluded_fraction <= 0.05`, T-SUP-3)
   belong to a-2's census. T-SUP-11 (d) asserts the segment drop and the
   `excluded_rows` value; cap evaluation waits for a-2.
6. Peeling cannot cross an interior scheduled reset (section 4.2 argument), so
   a segment peeled to one row lies inside one month and already had fewer than
   42 rows. T-SUP-11 (d) records that `excluded_rows` is unchanged by that peel.
7. A constant series now gives an undefined LRV and an undefined Newey-West
   t-statistic. Mean subtraction of a constant 0.05 series left a positive
   residue of 2.4e-34, which would have produced a finite MDE for a
   zero-variance IC series. No existing test depended on the old value.
8. `monthly_rank_ic` types a constant cross-section as
   `ic_month_invalid:undefined_rank_ic` (R6); section 4.6 names only
   `insufficient_pairs`. An empty asset axis raises through
   `factor_rank_information_coefficient`'s existing refusal.
9. `decide_gate` refuses fewer or more than six factors with
   `family_size_mismatch`. `family_b_context` is a runner flag (b-1) and stays
   out of the pure gate.
10. The engine runs of T-SUP-11 belong to a-2; the fixture (a) engine check is
    included here because it costs under a second and pins the peel against the
    real engines.
11. The Family B masking part of T-REG-4b, T-SUP-3 through T-SUP-7,
    T-SUP-9, T-SUP-10, and every validator, projection, census, and runner
    oracle belong to later stages.

## Ablation

Baseline preserved: each removal ran alone against the new tests, and
regressions were restored.

Simplification attempts:

| Attempt | Evidence | Outcome |
| --- | --- | --- |
| Drop the explicit full-window mask in `calculate_rolling_market_beta` | Probe: pandas rolling `cov` with `min_periods = window` is pairwise-complete, NaN for a missing asset or market return | Removed |
| Drop the explicit completeness mask in `calculate_52_week_high_proximity` | Rolling `max` with `min_periods = window` is NaN whenever the window holds a missing value; the gapped-window test passes | Removed |
| Replace the plan's repeat-until-stable peel loop with one pass | A peel changes only its own preceding segment. Fuzz over 400 random fixtures (3 to 24 assets, bar-missing rates 0.2 to 5 percent) against a literal fixpoint implementation: 400/400 identical windows, reasons, peeled counts, and cells | Kept one pass |
| Remove the merge after peeling | The `q > p` stop leaves at least one segment row; the fuzz found 0/400 merges needed; tests pass | Removed |
| Duplicate call literals in `family_a_signals` | Parameters now come from the frozen `FAMILY_A` tuple, so the registration and the call cannot drift | Simplified |

Guard-necessity checks (each guard disabled alone, targeted tests run):

| Guard | Result without it | Disposition |
| --- | --- | --- |
| G1 `R_entry < R_exit` in `holding_cells` | `test_holding_cells_follow_membership_runs_and_open_intervals` fails (a member joining and leaving inside one month becomes held) | Retained |
| G2 constant-series check in the LRV | Two T-REG-5 tests fail (2.4e-34 residue reads as positive variance) | Retained |
| G3 `family` in the attempt comparison | `test_t_reg_3_family_b_trial_cannot_enter_family_a` fails | Retained |
| G4 zero market variance in the beta | Passed at first because the test used an exact-zero market series; a constant 0.001 market gives variance 0 with a nonzero covariance residue, so the ratio is `+/-inf`. The test now covers that case and fails without the guard | Retained; test added |
| G5 six-factor check in `decide_gate` | `test_decide_gate_requires_six_factors` fails | Retained |
| G6 zero dollar volume in Amihud | No failure: the raw term is `inf`, and pandas rolling `mean` returns NaN for windows holding `inf` | Retained to state the R6 rule without relying on pandas' inf handling; behaviorally redundant under pandas 3.0.6 |
| G7 basis membership in `_prepare_terminal_events` | Nine T-ENG tests fail | Retained |
| G8 cutoff bar `B[q-1]` in the peel condition | `test_t_sup_11_b_missing_cutoff_bar_forces_no_peel` fails (selectability condition) | Retained |

Empty-axis boundaries: an N x 0 asset panel yields no window, one full valid
segment, zero exclusions, and empty labels; a 0-row calendar has no resets and
`common_support_schedule` refuses it with the `d0` check; misaligned panels
refuse. The empty-column case exposed an object-dtype conversion in
`base_exclusion_cells`, fixed with an explicit `bool` cast.

Scripts: `ablation_peel_fuzz.py` and `guard_ablation.py` in the session
scratchpad (not committed).

## Files

Modified: `src/backtest/portfolio.py`, `src/backtest/long_short.py`,
`src/features/momentum.py`, `src/features/volatility.py`,
`src/features/liquidity.py`, `src/features/diagnostics.py`,
`research/multiple_testing_diagnostics.py`,
`docs/signal_execution_timing_contract.md`, `docs/engineering_log.md`,
`docs/repo_map.md` (regenerated: 32 research and 205 test files),
`docs/current_handoff.md`, `tests/test_pit_universe_delisting.py`.

Added: `research/m4_7_family_a.py`, `research/m4_7_common_support.py`,
`research/m4_7_sp500_pit_rerun.py`, `tests/test_m4_7_engine_bases.py`,
`tests/test_m4_7_family_a.py`, `tests/test_m4_7_common_support.py`,
`tests/test_m4_7_decision.py`, this report.

Pre-existing uncommitted changes in the worktree are preserved:
`docs/decision_log.md` (plan acceptance and O-8, unchanged by this stage) and
the plan-acceptance edit of `docs/current_handoff.md`. That edit had removed
the sentence "PR #180 is merged. PR #181 is merged at ..." that
`test_cca1_correction_checkpoint_is_consistent_across_active_sources` pins;
this stage restores it and adds the a-0 delivery bullet and next action. The
handoff's en dash in "Directives 1–4" comes from that earlier edit.

## Next Gate

1. Coordinator: commit the candidate on the branch (the handoff-lag test then
   passes), publish the PR under the same-change publication grant, and run the
   CRITICAL lane: CI lanes, two fresh formal reviewers with model diversity,
   and acceptance of the exact head.
2. a-1 and a-2 proceed under their cards; a-2 wires this core to snapshot
   fixtures, adds the readiness caps (T-SUP-3), and runs the projected events
   through both engines on the peeled schedule.
