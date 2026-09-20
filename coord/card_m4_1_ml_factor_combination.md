# Implementation Card: Milestone 4.1 Non-Linear ML Factor Combination

## Objective
Implement walk-forward non-linear machine learning factor combination models (Random Forest, Gradient Boosting, HistGradientBoosting, Ridge) that learn empirical mappings from classical alphas to execution-aligned forward returns under strict zero-lookahead causal constraints.

## Scope & Deliverables
1. `src/features/ml_combination.py`:
   - `walk_forward_ml_factor_composite`:
     - Expanding or rolling walk-forward window.
     - Strict causality filter: only historical dates `s` with closed execution-aligned forward-return windows (`s + execution_lag + forward_holding <= t`) are admitted to training set on rebalance date `t`.
     - Zero target return open at rebalance date `t` can ever enter the training set.
     - Cross-sectional feature standardization and prediction z-scoring.
     - Feature importance extraction (tree-based importances with permutation importance fallback).
     - Support for Random Forest, Gradient Boosting, HistGradientBoosting, and Ridge.
2. `research/real_data_multifactor_diagnostic.py`:
   - Added `RANDOM_FOREST_COMPOSITE` and `GRADIENT_BOOSTING_COMPOSITE` to evaluated composites.
   - Evaluated walk-forward ML models on the 50-stock blue-chip cohort across 105 rebalance dates.
   - Added reporting section for ML combinations and top feature importances.
3. `tests/test_ml_combination.py` & `tests/test_real_data_multifactor_diagnostic.py`:
   - Deterministic seed reproduction, zero-lookahead mutation invariance tests, rolling window tests, input validation tests.
   - Runner integration test for ML composites.
4. Generated artifacts:
   - `reports/real_data_multifactor_diagnostic.md`: Updated 50-stock diagnostic report including ML composites.
   - `reports/experiment_logs/`: Updated experiment trial logs and JSON metadata.
