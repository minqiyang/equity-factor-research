# Binding Card: M4.6 Multi-Factor Risk Attribution

Base: `b60e109c6959e059dea6c19c3573dd5e861a2ac2`.
Producer: `feat/m4-6-risk-attribution`. Evidence ceiling: `DIAGNOSTIC_ONLY`.
This card freezes the implementation interface before runtime edits. The
coordinator records this card commit; the producer continues the authorized
baseline, implementation, QA, and frozen-candidate handoff sequence.

## Scope and public interfaces

All model code lives in `src/backtest/risk_attribution.py`. Existing dependencies
NumPy and pandas supply linear algebra and labelled arrays. The module exports:

```python
STYLE_FACTORS = ("Size", "Value", "Momentum", "Volatility", "Liquidity")
class RiskAttributionError(ValueError):
    def __init__(self, reason: str, message: str) -> None: ...

@dataclass(frozen=True)
class StyleFactorExposures:
    panels: dict[str, pd.DataFrame]
    @classmethod
    def from_descriptors(cls, descriptors: Mapping[str, pd.DataFrame], *,
                         winsor_quantile: float = 0.01) -> StyleFactorExposures: ...
    @classmethod
    def from_market_data(cls, prices: pd.DataFrame, volumes: pd.DataFrame,
                         market_caps: pd.DataFrame, book_to_price: pd.DataFrame, *,
                         price_basis: str, volume_basis: str,
                         momentum_window: int = 252, momentum_skip: int = 21,
                         volatility_window: int = 60, liquidity_window: int = 21,
                         winsor_quantile: float = 0.01) -> StyleFactorExposures: ...
    def at(self, date: pd.Timestamp) -> pd.DataFrame: ...

@dataclass(frozen=True)
class FactorReturnFit:
    factor_returns: pd.DataFrame
    residual_returns: pd.DataFrame
    diagnostics: pd.DataFrame

@dataclass(frozen=True)
class ActiveRiskDecomposition:
    factor_contributions: pd.Series
    specific_contributions: pd.Series
    factor_variance: float
    specific_variance: float
    active_variance: float
    tracking_error: float
    annualized_tracking_error: float

def decompose_active_risk(exposures: pd.DataFrame,
                          portfolio_weights: pd.Series,
                          benchmark_weights: pd.Series,
                          factor_covariance: pd.DataFrame,
                          specific_variances: pd.Series, *,
                          periods_per_year: int = 252) -> ActiveRiskDecomposition: ...

@dataclass(frozen=True)
class CrossSectionalRiskModel:
    exposures: StyleFactorExposures
    regression_weights: pd.DataFrame | None = None
    benchmark_weights: pd.DataFrame | None = None
    covariance_window: int = 60
    min_covariance_observations: int = 20
    def fit(self, asset_returns: pd.DataFrame, *,
            interval_starts: pd.Series) -> FactorReturnFit: ...
    def attribute(self, asset_returns: pd.DataFrame, weights: pd.DataFrame, *,
                  interval_starts: pd.Series,
                  trading_costs: pd.Series | None = None,
                  periods_per_year: int = 252) -> PortfolioRiskAttribution: ...

@dataclass(frozen=True)
class PortfolioRiskAttribution:
    fit: FactorReturnFit
    exposures: pd.DataFrame
    factor_contributions: pd.DataFrame
    specific_return: pd.Series
    gross_return: pd.Series
    trading_costs: pd.Series
    net_return: pd.Series
    active_exposures: pd.DataFrame
    risk: pd.DataFrame
    factor_risk_contributions: pd.DataFrame
    specific_risk_contributions: pd.DataFrame

def attribute_backtest(model: CrossSectionalRiskModel | None, *,
                       prices: pd.DataFrame, holdings: pd.DataFrame,
                       gross_returns: pd.Series, net_returns: pd.Series,
                       trading_costs: pd.Series, periods_per_year: int,
                       terminal_events: pd.DataFrame | None,
                       missing_price_policy: str = "raise"
                       ) -> PortfolioRiskAttribution | None: ...
```

The two engines gain keyword-only `risk_model: CrossSectionalRiskModel | None =
None` and a result `risk_attribution: PortfolioRiskAttribution | None = None`.
All existing fields, assumptions, arithmetic, and defaults retain their exact
values. Disabled attribution returns before inspecting model inputs. The new
field is explicitly outside the pre-existing result schema comparison.

## Exposure definitions and timing

Each panel row labels its caller-declared availability at that observed close.
The market-data constructor uses log market capitalization, supplied point-in-time
book-to-price, `price[t-skip] / price[t-window] - 1`, trailing sample return
volatility, and log trailing average dollar volume. Price and volume share an
explicit `raw` or `split_adjusted` basis. Market caps and fundamental availability
remain caller assertions; synthetic inputs provide the delivery evidence.

Each descriptor is independently winsorized across assets at quantiles q and 1-q,
demeaned, and divided by population standard deviation. Constant rows become
zero exposures. Whole-row rolling warmup stays missing; partial missingness,
infinities, duplicate axes, empty axes, and mismatched panels refuse explicitly.
Used exposure rows must be finite. A unit Market intercept joins the five styles.
A constant or dependent style therefore fails the regression rank requirement.

Return rows label interval ends t; `interval_starts` labels their immediately
previous observed exposure row t-1. Portfolio and benchmark weight rows label
those starts. Regression weights are positive diagonal W entries known at t-1;
WLS solves `sqrt(W) X f = sqrt(W) r` using `numpy.linalg.lstsq`. OLS uses W=I.
Every fit requires more assets than six coefficients and full column rank at
rcond=1e-12. Rank and condition diagnostics accompany each fit. Singular fits
raise a typed refusal, preserving identification honesty.

Engine integration uses actual previous-close post-trade holdings, including
drift and impact partial fills. Asset returns use complete observed price
endpoints for the whole regression universe. Initialization has no attributed
return. Enabled integration requires finite positive complete prices, strict
missing-price policy, and an absent terminal-event table. Terminal/unbalanced
coverage refuses explicitly pending a separately scoped changing-universe model.
Existing terminal accounting remains available with `risk_model=None`.

## Return and risk algebra

`r_t = X_(t-1) f_t + u_t`, `beta_P = w_P.T X`,
`factor_contribution_k = beta_P,k f_k`, and `specific_return = w_P.T u`.
The sum reconciles to `w_P.T r_t` with absolute tolerance 1e-12. Gross and net
returns remain separate: net equals gross minus the engine's exact cost series.
Specific return measures residual return; economic alpha requires further evidence.

Active weights equal portfolio minus explicitly supplied benchmark weights.
An absent benchmark means a zero-risk cash benchmark, disclosed in the report.
Active exposures equal active weights times X. Sample covariance and residual
sample variances use at most `covariance_window` earlier fitted intervals,
strictly excluding the attributed interval. Insufficient history yields a typed
`insufficient_history` status and missing risk numbers; return attribution remains
available. Minimum history is at least two observations.

Factor Euler variance contributions equal `delta_beta * (Sigma_f @ delta_beta)`;
specific contributions equal `delta_w**2 * var(u)`. Their sums give factor and
specific variance, then total active variance. Tracking error is the square root;
annualized tracking error multiplies by sqrt(periods_per_year). Contributions may
be negative for correlated factors. Covariance must be finite, symmetric and PSD;
specific variances must be finite and nonnegative. Covariances remain in per-period
units. The diagonal specific-risk and zero factor/residual cross-covariance
assumptions define a model forecast rather than exact realized active variance.

## Evidence sequence and delivery

1. Commit this card independently and record its SHA for the coordinator.
2. Preserve the pre-implementation 62-factor/124-book capture using the existing
   `capture_baseline.py`; also capture every M4.5 result field with a stricter
   serializer. Replay both after implementation and compare artifact bytes.
3. Implement the module, two optional integrations, deterministic tests, and
   `research/risk_attribution_demo.py`. Every synthetic case logs start and final
   status to `reports/risk_attribution_demo_attempts.jsonl`, including negative
   and failed attempts. Generate `reports/risk_attribution_demo.md`.
4. Test orthogonal OLS/WLS golden values, collinearity refusal, return/risk
   identities, signed/extreme/zero weights, covariance validity, warmup, sparse
   boundaries, label alignment, causal prefix invariance, costs, both engines,
   and impact integration. Run isolated negative ablations against preserved
   source copies; document a coverage matrix and limitations.
5. Run disjoint CI core and diagnostics lanes, repository Ruff, compileall,
   baseline replay, and repo-map freshness. Retain failures and final results.
6. Commit `coord/reports/m4_6_risk_attribution_impl.md` with evidence and freeze
   the candidate. Release producer write responsibility. The coordinator owns
   independent single-seat GPT-6 Astra High Fast review from a clean exact-head
   root and subsequent delivery decisions.

## Design ablation

The retained design uses one model module and labelled data containers. A separate
risk registry, fitting backend, cache, and portfolio optimizer have been removed
from the design. Direct NumPy least squares, pandas rolling windows, and one
optional sidecar meet the current mathematical and integration requirements.
The implementation ablation will test guards and calculations independently.
