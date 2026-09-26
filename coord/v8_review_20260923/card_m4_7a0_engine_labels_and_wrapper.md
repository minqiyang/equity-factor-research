# Task Card: M4.7a-0 Statistical and Portfolio Core on Golden Fixtures

- **Task/attempt**: `m4_7a0-engine-labels-and-wrapper-a1`
- **Objective**: Implement the pure statistical, factor, and portfolio core of Milestone 4.7 Binding Implementation Plan Revision 11 (`coord/plans/m4_7_binding_plan.md` §7.2, stage `a-0`) on deterministic golden fixtures, completely decoupled from vendor data and network access.
- **Target audience**: Project Owner and Coordinator.
- **Route**: `GENERAL_EXEC` (Coordination Standard V8.5).
- **Binding**: `OPUS_LATEST` (`claude-opus-5-5`), Claude Code, effort: `medium`, normal service tier, `--dangerously-skip-permissions`.
- **Lane**: CRITICAL. **Structural**: true (`ARCHITECTURE`, `SCHEMA_PROTOCOL_CONTRACT`).
- **Ablation applicability**: Major implementation candidate; requires ABLATION pass before final merge.
- **Candidate branch**: `claude/m4_7a0-engine-labels-and-wrapper` from `main` (`49eacdd4ce69fe1db9b779bfb7cc975d8b5950d3`).
- **Operative Plan Reference**: `coord/plans/m4_7_binding_plan.md` (Revision 11, SHA-256 `6541db93336e9181ebf3ad2f066b7b17f4550a17565036c2db5a5d82872a6407`).
- **Report destination**: `/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/coord/reports/m4_7a0_engine_labels_and_wrapper_impl.md`.

---

## Deliverables & Acceptance Criteria (§7.2, §3.5, §4, §6.2, §6.8, §6.9)

### 1. Engine Consideration Bases, V2 Contract String & Mask Wrapper (§3.5)
- **`src/backtest/portfolio.py` & `src/backtest/long_short.py`**:
  - Define and export `ACCEPTED_TERMINAL_BASES`:
    ```python
    ACCEPTED_TERMINAL_BASES = {
        "prior_observed_close_to_cash",
        "prior_observed_close_to_stock_consideration_valued_at_completion_date_close",
        "prior_observed_close_to_mixed_consideration_valued_at_completion_date_close",
    }
    ```
  - Update `_prepare_terminal_events`: accept any `return_basis` in `ACCEPTED_TERMINAL_BASES`; refuse all other strings with `terminal_events_invalid`.
  - Record assumption `terminal_basis_counts`: dictionary mapping each accepted label to its event count.
  - Update `terminal_settlement_contract` in backtest results to:
    `"prior_observed_close_to_consideration_at_completion_date_row_v2"` (replacing `prior_observed_close_to_cash_v1`).
  - Export public wrapper `resolve_pit_universe_mask`:
    ```python
    def resolve_pit_universe_mask(
        constituent_intervals: pd.DataFrame,
        terminal_events: pd.DataFrame | None,
        dates: pd.Index,
        assets: list[str],
        *,
        signal_lag_periods: int = 1,
    ) -> pd.DataFrame:
        ...
    ```
    Returns the mask `_resolve_pit_universe` produces after `_prepare_terminal_events`, with zero added logic.
- **Documentation**:
  - Add subsection "M4.7 consideration bases" to `docs/signal_execution_timing_contract.md` specifying the three labels, valuation row $V$, settlement on $S$, and the v2 contract string.
- **Existing Tests**:
  - Update existing terminal tests (e.g. `tests/test_pit_universe_delisting.py`) for the v2 contract string.

### 2. Family A Factors & Diagnostics (§6.2, §6.8, §6.4)
- **`src/features/momentum.py`**:
  - Implement `calculate_52_week_high_proximity(prices: pd.DataFrame, window: int = 252) -> pd.DataFrame`.
    Formula: `prices[t] / max(prices[t-window+1..t])`, full window (NaN if any row in window is missing).
- **`src/features/volatility.py`**:
  - Implement `calculate_rolling_market_beta(returns: pd.DataFrame, market_returns: pd.Series, window: int = 252) -> pd.DataFrame`.
    Formula: `Cov_252(r_a, r_SPY) / Var_252(r_SPY)` with `ddof=1` over the 252-row window ending at $t$, full window.
- **`src/features/liquidity.py`**:
  - Implement `calculate_amihud_illiquidity(returns: pd.DataFrame, dollar_volume: pd.DataFrame, window: int = 63) -> pd.DataFrame`.
    Formula: Mean over 63 rows ending at $t$ of `abs(r_d) / dollar_volume_d` (`dollar_volume = split_close * volume`). Missing/zero dollar volume makes term missing, full window missing.
- **`research/m4_7_family_a.py`**:
  - Define frozen definitions for Family A: IDs `("MOM_12_1", "HIGH_52W", "REV_1M", "LOW_VOL_252", "LOW_BETA_252", "AMIHUD_ILLIQ_63")`, directions (all `"higher_is_better"`), and `warmup_rows_f = (252, 251, 21, 252, 252, 63)`.
- **`src/features/diagnostics.py`**:
  - Implement `newey_west_long_run_variance(values: np.ndarray | pd.Series, lags: int) -> float`.
    Bartlett kernel: $\Gamma_0 + 2 \sum_{k=1}^q (1 - k/(q+1)) \Gamma_k$. Return `undefined` (or NaN) for non-finite or $\le 0$.
    Update `newey_west_mean_tstat` to call it.
  - Implement pure function `mde_from_long_run_variance(lrv: float, count: int, z: float) -> float`.
    Formula: $z \times \sqrt{\text{LRV} / T}$.
- **`src/features/multiple_testing.py` / `research/multiple_testing_diagnostics.py`**:
  - `summarize_multiple_testing` gains `family_sizes: Mapping[str, int] | None = None` and `statistic_key: str = "return_test"`.
  - When `family_sizes` is provided, require `family` key in every record, adjust within each family with its declared size, and refuse unknown family. Default path unchanged.

### 3. Pure Evaluation Core (§4, §6.8, §6.9)
- **`research/m4_7_common_support.py`**:
  - Pure functions taking calendar index, reset rows, bar presence matrix, mask, and event table:
    - Exclusion cells $X = G \cup U$ (§4.1).
    - Gap windows $W$ (§4.2 Steps 1–2).
    - Terminal-reset peeling (§4.2 Step 4).
    - Segments $[p, q]$ recomputed after peeling (§4.2 Step 5) with validity ($q - p + 1 \ge 42$).
    - `max_reset_to_reset_rows` calculation.
    - Terminal-aware reset-to-reset labels $label(r, a)$ (§4.6).
    - IC month set $T_{\text{IC}}$ and typed exclusions (§4.6).
- **`research/m4_7_sp500_pit_rerun.py`**:
  - Pure functions `decide_gate(...)` (§6.9) and halves split (§6.8).
- **Composite Label Keying (§6.3)**:
  - Composite builders called with labels keyed by $t = r - 1$ and `forward_holding_periods = max_reset_to_reset_rows`.

---

## Deterministic Test Oracles (§3.7, §4.7, §6.11)

Worker must author and pass dedicated unit tests:
1. **T-ENG-1**: `resolve_pit_universe_mask` equals `_resolve_pit_universe` on same inputs with empty event table, cash event, and stock event under new label.
2. **T-ENG-2**: Both engines accept each of the 3 labels, refuse unknown labels with `terminal_events_invalid`; `terminal_basis_counts` matches; `terminal_settlement_contract` reads v2.
3. **T-ENG-3**: `docs/signal_execution_timing_contract.md` contains "M4.7 consideration bases" subsection.
4. **T-TERM-1 & T-TERM-2 (Engine parts)**: Stock & mixed consideration event settlement through engines.
5. **T-TERM-4 (Engine part)**: Direct engine assertion on frozen target collision.
6. **T-UNI-11**: Mask properties: $E_{\text{sig}} = M.\text{shift}(-1)$, joiner on row 200 false before row 200, missing bar at $t$ false at $t$ and true at $t\pm 1$, engine event at $S_a$ false at $L_a$.
7. **T-SUP-1**: Gap windows merge and bounds.
8. **T-SUP-2**: Segments complement of $W$; anchor precedes by 1 row; 30-row segment dropped as `segment_too_short`.
9. **T-SUP-8**: Labels: cash, stock, worthless, membership ending inside horizon, event at $S_a=e$; probe yields Rank IC $-0.5$.
10. **T-SUP-11 (Array parts a–d)**: Peeling oracle on synthetic calendars.
11. **T-REG-3**: `summarize_multiple_testing` with `family_sizes`.
12. **T-REG-4**: Golden Family A values on 600-row synthetic panel; warm-up rows $(252, 251, 21, 252, 252, 63)$.
13. **T-REG-4b (Composite part)**: Composite builder horizon leakage assertion.
14. **T-REG-5**: MDE golden values: $\text{LRV} = 0.136^2, T = 240 \implies \text{MDE}_f = 0.033101, \text{MDE}_{\text{single}} = 0.024595$ within $10^{-6}$.
15. **T-REG-7**: Decision truth table for `decide_gate`.
16. **Existing Suite**: All 2,716 existing tests pass unchanged.
