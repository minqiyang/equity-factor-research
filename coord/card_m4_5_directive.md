# Milestone 4.5 Directive: Realistic Market Microstructure & Square-Root Law Slippage / Capacity Model

Date: 2026-09-22  
Base: `fe851ba3e198b16fa7cbbf5f1caad6a524a8d461` (`main`, clean post-M4.4 PR #253)  
Branch: `feat/m4-5-market-impact-capacity`  
Producer Worktree: `/private/tmp/efr-m4-5-market-impact-capacity`  
Target Executor: GPT-6 Astra Extra High Fast (`w3:pFA`)  
Coordinator: Antigravity (`w3:pE8`)  

---

## 1. Objective & Motivation

Currently, both long-only and long-short backtest engines rely on fixed basis points (e.g., 10 bps commission + 5 bps fixed slippage) or an exogenous turnover penalty $\lambda$. While computationally clean, fixed slippage creates **phantom profitability** for high-turnover signals and fails to measure the **economic capacity** of an investment strategy.

In real equity markets, execution cost follows the well-established **Square-Root Law of Market Impact** (Barra; Almgren, Thum, Hauptmann, and Li 2005; Frazzini, Israel, and Moskowitz 2012; Bouchaud et al.):
$$\text{Impact}(\%) = \eta \cdot \sigma_i \cdot \sqrt{\frac{\text{Trade Dollar Volume}_i}{\text{ADV}_i}}$$

Milestone 4.5 introduces an auditable, deterministic, and modular market microstructure impact and capacity model into the research platform without violating walking-skeleton or anti-overengineering invariants.

---

## 2. Core Architectural & Accounting Specifications

### 2.1 Microstructure Impact Model (`src/backtest/market_impact.py`)
- Define a lightweight dataclass / model:
  ```python
  @dataclass(frozen=True)
  class SquareRootImpactModel:
      eta: float = 0.25               # Non-dimensional market impact coefficient
      max_participation_rate: float = 0.10  # Hard cap on trade participation per bar
      fixed_bps: float = 0.0          # Base fixed exchange/clearing fee in bps
      min_adv: float = 1e5            # Minimum ADV floor to prevent division-by-zero
  ```
- Impact calculation:
  $$\text{Effective Slippage}_{i, t} = \text{fixed\_bps} \times 10^{-4} + \eta \cdot \sigma_{i, t} \cdot \sqrt{\frac{\text{Trade Value}_{i, t}}{\text{ADV}_{i, t}}}$$
  $$\text{Total Frictional Cost}_{i, t} = \text{Trade Value}_{i, t} \times \text{Effective Slippage}_{i, t}$$
- **Price/Volume Base Compatibility**: In accordance with the non-negotiable AGENTS.md invariant (*no incompatible price/volume dollar turnover calculations*), $\text{ADV}_{i, t}$ must be computed on matching price and volume bases ($P_{i} \times V_{i}$ where both are on the same split-adjusted basis).
- **Volatility Scaling**: $\sigma_{i, t}$ is computed using an expanding or rolling daily return standard deviation known prior to execution.

### 2.2 Participation Rate & Throttling
- When $\frac{\text{Trade Value}_{i, t}}{\text{ADV}_{i, t}} > \text{max\_participation\_rate}$:
  - Support configurable execution handling:
    1. `mode="throttle"`: Trades are clamped to $\text{max\_participation\_rate} \times \text{ADV}_{i, t}$, leaving residual target for subsequent bars.
    2. `mode="penalize"`: Full trade executes but excess volume beyond participation cap incurs quadratic penalty.
    3. `mode="raise"`: Fail-closed on exceeding liquidity threshold.

### 2.3 Portfolio & Accounting Engine Integration
- `src/backtest/portfolio.py` and `src/backtest/long_short.py`:
  - Add optional argument `impact_model: SquareRootImpactModel | None = None`.
  - When `impact_model is None`, **exact 100% numerical equality with M4.4 baseline is preserved**.
  - Deduct dynamic slippage cleanly from cash balance and portfolio equity.
  - Expose `slippage_cost_series: pd.Series`, `realized_slippage_bps: pd.Series`, and `trade_participation_rates: pd.DataFrame` in backtest results.
  - Terminal delisting redemption proceeds (PIT-006) remain exempt from market impact and ordinary turnover.

### 2.4 Strategy Capacity & AUM Scaling Analysis (`research/market_impact_capacity_demo.py`)
- Provide synthetic and cohort capacity evaluation across varying portfolio equity scales:
  e.g., $1M, $10M, $50M, $100M, $500M, $1B.
- Generate comparison report `reports/market_impact_capacity_demo.md`:
  - Net Sharpe Ratio vs. AUM (identifying the "break-even AUM" where alpha is fully degraded by impact).
  - Average realized slippage in bps across AUM tiers.
  - All-attempt case logging adhering to repo logging standards.

---

## 3. Implementation Workflow & Quality Gates

1. **Worktree & Branch**:
   - Check out `feat/m4-5-market-impact-capacity` in `/private/tmp/efr-m4-5-market-impact-capacity` from `main` (`fe851ba`).
2. **Author Binding Card**:
   - Write `coord/card_m4_5_market_impact_capacity.md` specifying exact mathematical formulations, function signatures, edge-case handlers, and ablation targets.
3. **Implementation & Deterministic Testing**:
   - Unit tests covering: zero trade, tiny trades, massive trades exceeding ADV, zero volume handling, constant volatility, extreme volatility, long and short impact symmetry.
   - Preserved baseline equality when `impact_model is None`.
4. **CI & Isolated Ablation**:
   - Run both core and diagnostics CI suites.
   - Run isolated negative ablation testing each guard and coefficient parameter.
5. **Review Gate**:
   - Single-seat independent review by **GPT-6 Astra High Fast** on a clean detached worktree.
