# Implementation Card: Milestone 4.2 Purged & Embargoed Cross-Validation (CPCV)

## Objective
Implement Purged & Embargoed Cross-Validation (CPCV) and Scikit-Learn compatible `PurgedGroupTimeSeriesSplit` to eliminate temporal leakage and auto-correlation overlap bias in backtest overfitting evaluations and feature validation.

## Scope & Deliverables
1. `src/features/cross_validation.py`:
   - `PurgedGroupTimeSeriesSplit`:
     - Contiguous temporal group partitioning (K-fold or combinatorial groups).
     - Combinatorial test paths $C(S, k)$.
     - Exact label overlap purging: removes training observations $[s, s + H]$ overlapping with test block $[T_{\text{start}}, T_{\text{end}}]$.
     - Post-test embargoing: drops training observations immediately succeeding test blocks within $[T_{\text{end}} + 1, T_{\text{end}} + E]$.
     - Scikit-learn `BaseCrossValidator` compatibility (`split`, `get_n_splits`).
   - `combinatorial_purged_cross_validation_pbo`:
     - Evaluates Probability of Backtest Overfitting (PBO), out-of-sample loss probability, IS/OOS Sharpe distributions, and relative ranks under purged/embargoed paths.
     - Fast path reproducing exact classical symmetric CSCV when $H=0$ and $E=0$.
     - Computes average purged and embargoed sample counts across splits.
2. `src/features/diagnostics.py`:
   - Extended `probability_of_backtest_overfitting` with optional `holding_periods` and `embargo_periods` parameters, routing to `combinatorial_purged_cross_validation_pbo` when non-zero.
3. `src/features/__init__.py`:
   - Exported `PurgedGroupTimeSeriesSplit` and `combinatorial_purged_cross_validation_pbo`.
4. `research/real_data_multifactor_diagnostic.py`:
   - Configured `pbo_holding_periods` (21 bars) and `pbo_embargo_periods` (5 bars).
   - Incorporated `cpcv_summary` into the real data diagnostic runner, markdown report, and experiment logs.
   - Preserved backward-compatible classical CSCV section alongside the new CPCV section.
5. `tests/test_cross_validation.py` & `tests/test_diagnostics.py`:
   - 8 comprehensive tests in `tests/test_cross_validation.py` verifying split counts, exact boundary purging, post-test embargoing, scikit-learn cross_val_score integration, and zero-holding/zero-embargo CSCV equivalence.
   - Diagnostics integration test in `tests/test_diagnostics.py`.
