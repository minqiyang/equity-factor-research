"""Causal, synthetic-diagnostic style return and active-risk attribution.

Input rows declare availability at observed closes. A Market intercept and five
standardized styles explain realized returns. Specific return is a residual;
economic alpha and empirical risk calibration require separate evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from numbers import Integral, Real

import numpy as np
import pandas as pd

STYLE_FACTORS = ("Size", "Value", "Momentum", "Volatility", "Liquidity")
FACTORS = ("Market", *STYLE_FACTORS)


class RiskAttributionError(ValueError):
    """A stable reason identifies the refused input or calculation."""

    def __init__(self, reason: str, message: str) -> None:
        self.reason = reason
        super().__init__(f"{reason}: {message}")


def _require(condition: bool, reason: str, message: str) -> None:
    if not condition:
        raise RiskAttributionError(reason, message)


def _axis(axis: pd.Index) -> bool:
    return len(axis) > 0 and axis.is_unique and not axis.hasnans


def _frame(frame: pd.DataFrame, name: str, *, finite: bool = True) -> None:
    _require(isinstance(frame, pd.DataFrame), "axes", f"{name} requires a DataFrame")
    _require(_axis(frame.index) and _axis(frame.columns), "axes", f"{name} requires nonempty unique axes")
    _require(all(dtype.kind in "fiu" for dtype in frame.dtypes), "numeric", f"{name} requires real numeric values")
    if finite:
        _require(np.isfinite(frame.to_numpy(dtype=float)).all(), "nonfinite", f"{name} requires finite values")


def _dates(index: pd.Index) -> None:
    _require(isinstance(index, pd.DatetimeIndex) and index.tz is None
             and _axis(index) and index.is_monotonic_increasing,
             "dates", "dates require increasing unique timezone-naive observed closes")


def _same_axes(left: pd.DataFrame, right: pd.DataFrame) -> None:
    _require(left.index.equals(right.index) and left.columns.equals(right.columns),
             "alignment", "panel axes must match exactly, including order")


def _series(series: pd.Series, index: pd.Index, name: str) -> np.ndarray:
    _require(isinstance(series, pd.Series) and series.index.equals(index), "alignment", f"{name} axis must match exactly")
    _require(series.dtype.kind in "fiu", "numeric", f"{name} requires real numeric values")
    values = series.to_numpy(dtype=float)
    _require(np.isfinite(values).all(), "nonfinite", f"{name} requires finite values")
    return values


def _positive_int(value: int, minimum: int, name: str) -> None:
    _require(isinstance(value, Integral) and not isinstance(value, bool) and value >= minimum,
             "configuration", f"{name} requires an integer >= {minimum}")


@dataclass(frozen=True)
class StyleFactorExposures:
    """Five standardized exposure panels, indexed by their availability close."""

    panels: dict[str, pd.DataFrame]

    @classmethod
    def from_descriptors(
        cls, descriptors: Mapping[str, pd.DataFrame], *, winsor_quantile: float = 0.01,
    ) -> StyleFactorExposures:
        _require(set(descriptors) == set(STYLE_FACTORS), "styles", "exactly five declared styles are required")
        _require(isinstance(winsor_quantile, Real) and not isinstance(winsor_quantile, bool)
                 and np.isfinite(winsor_quantile) and 0 <= winsor_quantile < 0.5,
                 "configuration", "winsor_quantile must lie in [0, 0.5)")
        reference = descriptors[STYLE_FACTORS[0]]
        panels = {}
        for name in STYLE_FACTORS:
            raw = descriptors[name]
            _frame(raw, name, finite=False)
            _dates(raw.index)
            _same_axes(reference, raw)
            values = raw.to_numpy(dtype=float)
            _require(~np.isinf(values).any(), "nonfinite", "descriptor infinities are refused")
            _require((raw.notna().all(axis=1) | raw.isna().all(axis=1)).all(),
                     "partial_missing", "descriptor missingness must cover an entire warmup row")
            bounds = raw.quantile([winsor_quantile, 1 - winsor_quantile], axis=1)
            clipped = raw.clip(lower=bounds.iloc[0], upper=bounds.iloc[1], axis=0)
            centered = clipped.sub(clipped.mean(axis=1), axis=0)
            scale = clipped.std(axis=1, ddof=0)
            panels[name] = centered.div(scale.where(scale.ne(0), 1.0), axis=0)
        return cls(panels)

    @classmethod
    def from_market_data(
        cls, prices: pd.DataFrame, volumes: pd.DataFrame,
        market_caps: pd.DataFrame, book_to_price: pd.DataFrame, *,
        price_basis: str, volume_basis: str,
        momentum_window: int = 252, momentum_skip: int = 21,
        volatility_window: int = 60, liquidity_window: int = 21,
        winsor_quantile: float = 0.01,
    ) -> StyleFactorExposures:
        _require(price_basis in ("raw", "split_adjusted") and price_basis == volume_basis,
                 "basis", "price and volume require matching declared bases")
        for name, panel in (("prices", prices), ("volumes", volumes),
                            ("market_caps", market_caps), ("book_to_price", book_to_price)):
            _frame(panel, name)
            _dates(panel.index)
            _same_axes(prices, panel)
            if name != "book_to_price":
                _require((panel.to_numpy() > 0).all(), "positive_inputs", f"{name} must be positive")
        for name, value, minimum in (("momentum_window", momentum_window, 1),
                                     ("momentum_skip", momentum_skip, 0),
                                     ("volatility_window", volatility_window, 2),
                                     ("liquidity_window", liquidity_window, 1)):
            _positive_int(value, minimum, name)
        _require(momentum_skip < momentum_window, "configuration", "momentum skip must precede lookback")
        returns = prices.pct_change(fill_method=None)
        descriptors = {
            "Size": np.log(market_caps),
            "Value": book_to_price,
            "Momentum": prices.shift(momentum_skip) / prices.shift(momentum_window) - 1.0,
            "Volatility": returns.rolling(volatility_window, min_periods=volatility_window).std(ddof=1),
            "Liquidity": np.log((prices * volumes).rolling(liquidity_window, min_periods=liquidity_window).mean()),
        }
        return cls.from_descriptors(descriptors, winsor_quantile=winsor_quantile)

    def at(self, date: pd.Timestamp) -> pd.DataFrame:
        _require(set(self.panels) == set(STYLE_FACTORS), "styles", "exactly five declared styles are required")
        reference = self.panels[STYLE_FACTORS[0]]
        values = {}
        for name in STYLE_FACTORS:
            panel = self.panels[name]
            _frame(panel, name, finite=False)
            _dates(panel.index)
            _same_axes(reference, panel)
            _require(date in panel.index, "availability", "exposure availability close is missing")
            row = panel.loc[date]
            _require(np.isfinite(row.to_numpy(dtype=float)).all(), "exposure_unavailable", "exposure row requires complete finite data")
            values[name] = row
        result = pd.DataFrame(values)
        result.insert(0, "Market", 1.0)
        return result


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


def decompose_active_risk(
    exposures: pd.DataFrame, portfolio_weights: pd.Series,
    benchmark_weights: pd.Series, factor_covariance: pd.DataFrame,
    specific_variances: pd.Series, *, periods_per_year: int = 252,
) -> ActiveRiskDecomposition:
    """Euler variance contributions under a diagonal specific-covariance model."""
    _positive_int(periods_per_year, 1, "periods_per_year")
    _frame(exposures, "exposures")
    _frame(factor_covariance, "factor_covariance")
    _require(factor_covariance.index.equals(exposures.columns)
             and factor_covariance.columns.equals(exposures.columns),
             "alignment", "covariance factors must match exposure columns")
    p = _series(portfolio_weights, exposures.index, "portfolio_weights")
    b = _series(benchmark_weights, exposures.index, "benchmark_weights")
    specific = _series(specific_variances, exposures.index, "specific_variances")
    _require((specific >= 0).all(), "specific_variance", "specific variances must be nonnegative")
    covariance = factor_covariance.to_numpy(dtype=float)
    _require(np.allclose(covariance, covariance.T, rtol=0, atol=1e-14),
             "covariance_symmetry", "factor covariance must be symmetric")
    _require(np.linalg.eigvalsh(covariance).min() >= -1e-14,
             "covariance_psd", "factor covariance must be positive semidefinite")
    active_weights = p - b
    beta = active_weights @ exposures.to_numpy(dtype=float)
    factor_terms = beta * (covariance @ beta)
    specific_terms = active_weights**2 * specific
    factor_variance = float(factor_terms.sum())
    specific_variance = float(specific_terms.sum())
    variance = factor_variance + specific_variance
    _require(np.isfinite(factor_terms).all() and np.isfinite(specific_terms).all()
             and np.isfinite(variance) and variance >= 0 and factor_variance >= 0,
             "risk_numerical", "risk calculation requires finite nonnegative variances")
    tracking_error = float(np.sqrt(variance))
    return ActiveRiskDecomposition(
        pd.Series(factor_terms, index=exposures.columns),
        pd.Series(specific_terms, index=exposures.index),
        factor_variance, specific_variance, variance, tracking_error,
        tracking_error * float(np.sqrt(periods_per_year)),
    )


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


@dataclass(frozen=True)
class CrossSectionalRiskModel:
    """OLS/WLS factor returns with strictly earlier rolling risk observations.

    Regression weights are positive entries of W, indexed by availability close.
    An absent benchmark denotes zero-weight cash. All forecasts are diagnostic.
    """

    exposures: StyleFactorExposures
    regression_weights: pd.DataFrame | None = None
    benchmark_weights: pd.DataFrame | None = None
    covariance_window: int = 60
    min_covariance_observations: int = 20

    def _starts(self, asset_returns: pd.DataFrame, interval_starts: pd.Series) -> pd.DatetimeIndex:
        _frame(asset_returns, "asset_returns")
        _dates(asset_returns.index)
        _require(isinstance(interval_starts, pd.Series)
                 and interval_starts.index.equals(asset_returns.index)
                 and isinstance(interval_starts.dtype, np.dtypes.DateTime64DType),
                 "alignment", "interval_starts must map each return end to a datetime start")
        starts = pd.DatetimeIndex(interval_starts)
        _dates(starts)
        _require((starts < asset_returns.index).all(), "causality", "exposures and weights must precede realized return ends")
        reference = self.exposures.panels[STYLE_FACTORS[0]]
        _dates(reference.index)
        end_positions = reference.index.get_indexer(asset_returns.index)
        _require((end_positions > 0).all(), "availability", "return ends require a previous exposure observation")
        _require(reference.index.take(end_positions - 1).equals(starts),
                 "causality", "starts must be the immediately previous observed exposure close")
        _require(reference.columns.equals(asset_returns.columns), "alignment", "return assets must match exposure assets")
        return starts

    def _known_panel(self, panel: pd.DataFrame, starts: pd.DatetimeIndex, assets: pd.Index, name: str) -> pd.DataFrame:
        _frame(panel, name, finite=False)
        _dates(panel.index)
        _require(panel.columns.equals(assets) and starts.isin(panel.index).all(),
                 "alignment", f"{name} requires all start dates and identical assets")
        selected = panel.loc[starts]
        _frame(selected, name)
        return selected

    def fit(self, asset_returns: pd.DataFrame, *, interval_starts: pd.Series) -> FactorReturnFit:
        starts = self._starts(asset_returns, interval_starts)
        weights = None
        if self.regression_weights is not None:
            weights = self._known_panel(self.regression_weights, starts, asset_returns.columns, "regression_weights")
            _require((weights.to_numpy() > 0).all(), "regression_weights", "WLS weights must be strictly positive")
        factors, residuals, diagnostics = [], [], []
        for i, start in enumerate(starts):
            x = self.exposures.at(start).to_numpy(dtype=float)
            y = asset_returns.iloc[i].to_numpy(dtype=float)
            _require(x.shape[0] > x.shape[1], "sample_size", "regression requires more assets than coefficients")
            sqrt_w = np.ones(len(y)) if weights is None else np.sqrt(weights.iloc[i].to_numpy(dtype=float))
            design = x * sqrt_w[:, None]
            coefficients, _, rank, singular = np.linalg.lstsq(design, y * sqrt_w, rcond=1e-12)
            _require(rank == x.shape[1], "rank_deficient", "style coefficients require full column rank")
            residual = y - x @ coefficients
            _require(np.isfinite(coefficients).all() and np.isfinite(residual).all(),
                     "fit_numerical", "regression outputs must be finite")
            factors.append(coefficients)
            residuals.append(residual)
            diagnostics.append({"exposure_date": start, "rank": int(rank),
                                "condition_number": float(singular[0] / singular[-1]),
                                "observations": len(y), "method": "OLS" if weights is None else "WLS"})
        return FactorReturnFit(
            pd.DataFrame(factors, index=asset_returns.index, columns=FACTORS),
            pd.DataFrame(residuals, index=asset_returns.index, columns=asset_returns.columns),
            pd.DataFrame(diagnostics, index=asset_returns.index),
        )

    def attribute(
        self, asset_returns: pd.DataFrame, weights: pd.DataFrame, *,
        interval_starts: pd.Series, trading_costs: pd.Series | None = None,
        periods_per_year: int = 252,
    ) -> PortfolioRiskAttribution:
        _positive_int(self.covariance_window, 2, "covariance_window")
        _positive_int(self.min_covariance_observations, 2, "min_covariance_observations")
        _positive_int(periods_per_year, 1, "periods_per_year")
        _require(self.min_covariance_observations <= self.covariance_window,
                 "configuration", "minimum observations must fit the covariance window")
        fit = self.fit(asset_returns, interval_starts=interval_starts)
        starts = pd.DatetimeIndex(interval_starts)
        p = self._known_panel(weights, starts, asset_returns.columns, "portfolio_weights")
        _require(weights.index.equals(starts), "alignment", "portfolio weight rows must exactly match interval starts")
        b = pd.DataFrame(0.0, index=starts, columns=asset_returns.columns)
        if self.benchmark_weights is not None:
            b = self._known_panel(self.benchmark_weights, starts, asset_returns.columns, "benchmark_weights")
        dates = asset_returns.index
        costs = pd.Series(0.0, index=dates, name="trading_costs") if trading_costs is None else trading_costs.copy()
        cost_values = _series(costs, dates, "trading_costs")
        _require((cost_values >= 0).all(), "costs", "trading costs must be nonnegative")
        betas, active_betas, factor_parts, specific_parts, gross, risk_rows = [], [], [], [], [], []
        factor_risk, specific_risk = [], []
        for i, start in enumerate(starts):
            x = self.exposures.at(start)
            beta = p.iloc[i].to_numpy() @ x.to_numpy()
            active_beta = (p.iloc[i].to_numpy() - b.iloc[i].to_numpy()) @ x.to_numpy()
            factor_part = beta * fit.factor_returns.iloc[i].to_numpy()
            specific_part = float(p.iloc[i].to_numpy() @ fit.residual_returns.iloc[i].to_numpy())
            total = float(p.iloc[i].to_numpy() @ asset_returns.iloc[i].to_numpy())
            _require(np.isfinite(total) and np.isfinite(factor_part).all()
                     and np.isfinite(specific_part) and abs(float(factor_part.sum()) + specific_part - total) <= 1e-12,
                     "return_identity", "factor plus specific return must reconcile within 1e-12")
            betas.append(beta)
            active_betas.append(active_beta)
            factor_parts.append(factor_part)
            specific_parts.append(specific_part)
            gross.append(total)
            history_start = max(0, i - self.covariance_window)
            factor_history = fit.factor_returns.iloc[history_start:i]
            residual_history = fit.residual_returns.iloc[history_start:i]
            row = {"status": "insufficient_history", "observations": len(factor_history),
                   "factor_variance": np.nan, "specific_variance": np.nan,
                   "active_variance": np.nan, "tracking_error": np.nan,
                   "annualized_tracking_error": np.nan,
                   "benchmark": "cash" if self.benchmark_weights is None else "supplied_weights"}
            if len(factor_history) >= self.min_covariance_observations:
                risk = decompose_active_risk(x, p.iloc[i], b.iloc[i], factor_history.cov(ddof=1),
                                             residual_history.var(ddof=1), periods_per_year=periods_per_year)
                row.update(status="estimated", **{name: getattr(risk, name) for name in (
                    "factor_variance", "specific_variance", "active_variance", "tracking_error", "annualized_tracking_error")})
                factor_risk.append(risk.factor_contributions.to_numpy())
                specific_risk.append(risk.specific_contributions.to_numpy())
            else:
                factor_risk.append(np.full(len(FACTORS), np.nan))
                specific_risk.append(np.full(len(asset_returns.columns), np.nan))
            risk_rows.append(row)
        gross_series = pd.Series(gross, index=dates, name="gross_return")
        net = (gross_series - costs).rename("net_return")
        _require(np.isfinite(net.to_numpy()).all(), "return_identity", "net returns must be finite")
        return PortfolioRiskAttribution(
            fit, pd.DataFrame(betas, index=dates, columns=FACTORS),
            pd.DataFrame(factor_parts, index=dates, columns=FACTORS),
            pd.Series(specific_parts, index=dates, name="specific_return"),
            gross_series, costs, net,
            pd.DataFrame(active_betas, index=dates, columns=FACTORS),
            pd.DataFrame(risk_rows, index=dates),
            pd.DataFrame(factor_risk, index=dates, columns=FACTORS),
            pd.DataFrame(specific_risk, index=dates, columns=asset_returns.columns),
        )


def attribute_backtest(
    model: CrossSectionalRiskModel | None, *, prices: pd.DataFrame,
    holdings: pd.DataFrame, gross_returns: pd.Series, net_returns: pd.Series,
    trading_costs: pd.Series, periods_per_year: int,
    terminal_events: pd.DataFrame | None, missing_price_policy: str = "raise",
) -> PortfolioRiskAttribution | None:
    """Attach diagnostics to complete static panels using actual prior holdings."""
    if model is None:
        return None
    _require(terminal_events is None and missing_price_policy == "raise",
             "integration_scope", "enabled risk attribution requires complete prices and absent terminal events")
    _frame(prices, "prices")
    _require((prices.to_numpy() > 0).all(), "positive_inputs", "regression prices require positive endpoints")
    _same_axes(prices, holdings)
    _require(len(prices) >= 2, "sample_size", "attribution requires a realized interval")
    asset_returns = prices.pct_change(fill_method=None).iloc[1:]
    starts = pd.Series(prices.index[:-1], index=prices.index[1:])
    attribution = model.attribute(asset_returns, holdings.iloc[:-1], interval_starts=starts,
                                  trading_costs=trading_costs.iloc[1:], periods_per_year=periods_per_year)
    for attributed, expected in ((attribution.gross_return, gross_returns.iloc[1:]),
                                 (attribution.net_return, net_returns.iloc[1:])):
        values = _series(expected, attributed.index, "engine_returns")
        _require(np.allclose(attributed.to_numpy(), values, rtol=0, atol=1e-12),
                 "engine_identity", "risk attribution must reconcile with engine returns within 1e-12")
    return attribution
