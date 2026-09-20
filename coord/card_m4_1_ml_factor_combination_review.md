# Review Card: Milestone 4.1 Non-Linear ML Factor Combination

## Objective
Independent formal code review of Milestone 4.1 non-linear machine learning factor combination models and diagnostic runner integration.

## Scope & Target
- Candidate branch: `feat/m4-1-ml-factor-combination`
- Lane: STANDARD
- Reviewer route: `GROK_REVIEW` (`GROK_LATEST`, `XHIGH`)
- Output report: `coord/reports/m4_1_ml_factor_combination_review.md`

## Key Review Checkpoints
1. **Causal Horizon and Zero-Lookahead Invariant**:
   - In `src/features/ml_combination.py`, verify that on rebalance date `t`, the training set admits strictly historical dates `s` whose execution-aligned forward-return labels have completely closed by `t`:
     `panel_index.get_loc(past_date) + execution_lag_periods + forward_holding_periods <= t_pos`.
   - Verify that no target returns overlapping or open at `t` can ever enter the training set.
2. **Feature and Prediction Integrity**:
   - Verify features are cross-sectionally standardized at each slice and predictions are cross-sectionally z-scored.
   - Verify non-leakage when computing feature importances.
3. **Deterministic Reproducibility**:
   - Verify random seeds are passed to regressors and results are reproducible.
4. **Diagnostic Runner Integration**:
   - In `research/real_data_multifactor_diagnostic.py`, verify `RANDOM_FOREST_COMPOSITE` and `GRADIENT_BOOSTING_COMPOSITE` use the exact causal forward returns and align with `COMPOSITE_IDS`.
5. **Test Coverage**:
   - Verify unit tests in `tests/test_ml_combination.py` test zero lookahead under future mutation, rolling windows, and deterministic seeds.
