# Directive Card: Milestone 4.6 Multi-Factor Risk Attribution (Barra-Style Style Risk Model)

**Target Session**: GPT-6 Astra `xhigh` (`w3:pFA`)  
**Coordinator**: Antigravity (`w3:tC9`)  
**Base Commit**: `b60e109` (`main`, clean and verified)  
**Branch**: `feat/m4-6-risk-attribution`  
**Producer Worktree**: `/private/tmp/efr-m4-6-risk-attribution`

---

## 1. Objective and Architectural Context

Following the completion and merge of Milestone 4.5 (`b60e109`), this milestone advances to **Milestone 4.6: Multi-Factor Risk Attribution (Barra-Style Style Risk Model & Factor Exposure Decomposition)**.

Current backtest engines report portfolio returns, transaction costs, market impact, Sharpe ratios, and drawdowns. However, a strategy's observed excess return may be driven by unintended, uncompensated systematic style exposures (such as Size, Value, Momentum, Volatility, or Liquidity bets) rather than genuine idiosyncratic alpha. 

Milestone 4.6 establishes an auditable, strictly causal, mathematically rigorous multi-factor risk attribution framework that decomposes portfolio returns and risk into systematic style factor contributions and asset-specific residual alpha.

---

## 2. Core Invariants and Mathematical Formulations

### 2.1 Causal Timing & Data Contracts (No Lookahead)
- Factor exposures $X_{i, k, t-1}$ must be strictly known prior to the return realization interval $[t-1, t]$.
- Portfolio weights $w_{i, t-1}$ are established at the close of $t-1$ (following accepted timing contracts).
- Realized asset returns $r_{i, t}$ cover the interval $(t-1, t]$.

### 2.2 Cross-Sectional Style Factor Model
For each cross-section at time $t$:
$$r_{i, t} = \sum_{k=1}^K X_{i, k, t-1} f_{k, t} + u_{i, t}$$
where:
- $X_{i, k, t-1}$: Standardized cross-sectional exposure of asset $i$ to style factor $k$ at $t-1$ (cross-sectionally demeaned and normalized by standard deviation, with outlier winsorization).
- Core style factors:
  1. **Size**: Log market capitalization (or log volume/price proxy).
  2. **Value**: Fundamental-to-price proxy (e.g. simulated book-to-price or dividend yield).
  3. **Momentum**: Standard intermediate-term momentum (e.g. 12-1 momentum or return momentum).
  4. **Volatility**: Realized historical return volatility over rolling historical window (e.g. 60-day standard deviation).
  5. **Liquidity**: Rolling Average Daily Volume / turnover (e.g. 21-day log ADV).
- $f_{k, t}$: Realized factor return of factor $k$ at time $t$, estimated via cross-sectional OLS or WLS (weighted by square root of market cap or inverse residual variance):
  $$f_t = (X_{t-1}^T W_{t-1} X_{t-1})^{-1} X_{t-1}^T W_{t-1} r_t$$
- $u_{i, t}$: Idiosyncratic / asset-specific return at time $t$, where $u_{i, t} = r_{i, t} - \sum_{k=1}^K X_{i, k, t-1} f_{k, t}$.

### 2.3 Portfolio Return Decomposition
Portfolio total return at time $t$ decomposes into factor return contributions and specific alpha:
$$R_{P, t} = \sum_{i=1}^N w_{i, t-1} r_{i, t} = \sum_{k=1}^K \beta_{P, k, t-1} f_{k, t} + R_{\text{specific}, t}$$
where:
- $\beta_{P, k, t-1} = \sum_{i=1}^N w_{i, t-1} X_{i, k, t-1}$ is the portfolio's net exposure to factor $k$.
- $R_{k, t}^{\text{factor}} = \beta_{P, k, t-1} f_{k, t}$ is the return contributed by factor $k$.
- $R_{\text{specific}, t} = \sum_{i=1}^N w_{i, t-1} u_{i, t}$ is the specific return contribution.
- **Exact Accounting Identity**: $\sum_k R_{k, t}^{\text{factor}} + R_{\text{specific}, t} \equiv R_{P, t}$ within machine numerical tolerance ($10^{-12}$).

### 2.4 Active Risk & Covariance Attribution
Using rolling factor covariance $\Sigma_{f}$ and specific variance matrix $\Delta$:
- Active factor variance: $\sigma_{\text{factor}}^2 = \Delta \beta^T \Sigma_f \Delta \beta$.
- Active specific variance: $\sigma_{\text{specific}}^2 = \sum_i \Delta w_i^2 \sigma_{u, i}^2$.
- Total active variance: $\sigma_{\text{active}}^2 = \sigma_{\text{factor}}^2 + \sigma_{\text{specific}}^2$.

### 2.5 Baseline Preservation & Optional Integration
- Risk attribution must be strictly optional: `risk_model=None` by default in portfolio engines.
- When `risk_model=None`, existing engine results across all 124 books and 1,674 fields must be **100% byte-for-byte identical** to the baseline captured at `b60e109`.

---

## 3. Implementation Deliverables

1. **Core Risk Model & Attribution Engine**:
   - `src/features/risk_attribution.py` (or `src/backtest/risk_attribution.py`):
     - `StyleFactorExposures`: Standardized factor exposure estimation.
     - `CrossSectionalRiskModel`: Fama-MacBeth / Barra cross-sectional regression, factor return extraction, residual calculation.
     - `PortfolioRiskAttribution`: Return decomposition ($R_P = \sum R_k + R_{\text{specific}}$), exposure time series, and risk decomposition.
2. **Backtest Engine Integration**:
   - Add optional risk attribution capability to `src/backtest/portfolio.py` and `src/backtest/long_short.py`.
   - Preserve all existing interfaces, fields, and timing contracts.
3. **Reproducible Diagnostic Demo**:
   - `research/risk_attribution_demo.py`: Run multi-style factor attribution across synthetic and diagnostic portfolios.
   - All-Attempt Case Logging (`reports/risk_attribution_demo_attempts.jsonl`).
   - Markdown report (`reports/risk_attribution_demo.md`).
4. **Deterministic Test Suite**:
   - `tests/test_risk_attribution.py`:
     - Orthogonal exposure golden tests.
     - Perfect collinearity / singularity handling.
     - Exact algebraic return decomposition identity.
     - Extreme and zero weight vectors.
     - Zero lookahead causal tests.
5. **Negative Ablation Suite**:
   - `coord/reports/m4_6_evidence/ablate.py`: Demonstrate necessity of each component.
6. **Delivery & Implementation Report**:
   - Authored implementation report: `coord/reports/m4_6_risk_attribution_impl.md`.
