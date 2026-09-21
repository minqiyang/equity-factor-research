# Implementation Report: Milestone 4.2 Purged & Embargoed Cross-Validation (CPCV)

## Executive Summary
Milestone 4.2 delivers Purged and Embargoed Cross-Validation (`PurgedGroupTimeSeriesSplit` and `combinatorial_purged_cross_validation_pbo`) in accordance with Marcos Lopez de Prado's framework (*Advances in Financial Machine Learning*, Ch. 7 & 12). This eliminates information leakage resulting from overlapping forward returns (purging) and serial auto-correlation persistence across temporal boundaries (embargoing) during cross-validation and overfitting diagnostics.

## Key Changes & Architecture

### 1. `src/features/cross_validation.py`
- **`PurgedGroupTimeSeriesSplit`**:
  - Inherits from Scikit-Learn `BaseCrossValidator`.
  - Splits $T$ sequential observations into $S$ contiguous temporal groups.
  - Generates $\binom{S}{k}$ combinations of test groups ($k = S // 2$ by default).
  - Purges training observations where the forward-holding window $[s, s + H]$ intersects any test block $[T_{\text{start}}, T_{\text{end}}]$.
  - Embargoes training observations following any test block within $[T_{\text{end}} + 1, T_{\text{end}} + E]$.
  - Scikit-Learn API compliant: `split(X, y=None, groups=None)`, `get_n_splits(X=None, y=None, groups=None)`.
- **`combinatorial_purged_cross_validation_pbo`**:
  - Evaluates PBO across all purged and embargoed combinations.
  - Calculates out-of-sample loss probability, mean/median relative ranks, and IS/OOS Sharpe distributions.
  - Maintains exact backward-compatibility with classical CSCV when $H=0$ and $E=0$ via an optimized vector path.

### 2. `src/features/diagnostics.py` & `src/features/__init__.py`
- Extended `probability_of_backtest_overfitting` with optional parameters `holding_periods=0` and `embargo_periods=0`.
- Routes directly to `combinatorial_purged_cross_validation_pbo` when either is non-zero.
- Exported in `src/features/__init__.py`.

### 3. `research/real_data_multifactor_diagnostic.py`
- Added `pbo_holding_periods: int = FORWARD_HOLDING_PERIODS` (21 bars) and `pbo_embargo_periods: int = 5` bars to `RealDataMultifactorDiagnosticConfig`.
- Evaluates both classical CSCV (unpurged) and CPCV (purged and embargoed) on the real EODHD 50-stock blue-chip dataset.
- Added CPCV diagnostics section to `reports/real_data_multifactor_diagnostic.md` and experiment metadata logs.

## Verification Evidence
- `tests/test_cross_validation.py`: 8 tests covering invalid inputs, split combinations, exact label purging boundaries, embargo boundaries, `cross_val_score` integration, and numeric equivalence to CSCV when $H=0, E=0$.
- `tests/test_diagnostics.py`: Added `test_probability_of_backtest_overfitting_purged_and_embargoed`.
- `tests/test_real_data_multifactor_diagnostic.py`: All 18 tests pass.
- `tests/test_project_structure.py`: All 66 tests pass.
- Full local suite passes deterministically (168 tests).
