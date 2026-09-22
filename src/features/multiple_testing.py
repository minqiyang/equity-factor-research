"""Observed-family corrections and explicitly conditional return diagnostics."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_complex_dtype, is_numeric_dtype
from scipy.special import digamma
from scipy.stats import false_discovery_control, norm, t

from features.diagnostics import newey_west_mean_tstat


METHODS = ("bonferroni", "holm", "bh", "by")
P_VALUE_FLOOR = float(np.finfo(float).tiny)


def _count(value: int, *, minimum: int, name: str) -> int:
    if (isinstance(value, (bool, np.bool_))
            or not isinstance(value, (int, np.integer))
            or not minimum <= value <= 2**53 - 1):
        raise ValueError(f"{name} must be an integer in [{minimum}, 2**53-1]")
    return int(value)


def _values(series: pd.Series) -> np.ndarray:
    if not isinstance(series, pd.Series):
        raise TypeError("input must be a pandas Series")
    if len(series) and (is_bool_dtype(series.dtype) or is_complex_dtype(series.dtype)
                        or not is_numeric_dtype(series.dtype)):
        raise TypeError("input must contain real numeric non-boolean values")
    return series.to_numpy(dtype=float, na_value=np.nan)


def adjust_pvalues(
    pvalues: pd.Series, *, method: str = "by", family_size: int | None = None,
) -> pd.Series:
    """Adjust p-values, retaining unavailable slots and the supplied labeled axis.

    NaN slots and additional declared hypotheses contribute p=1 internally.
    BY accommodates arbitrary dependence of valid marginal p-values; BH assumes
    independence or positive regression dependence. Bonferroni and Holm control
    family-wise error for valid marginal p-values.
    """
    values = _values(pvalues)
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}")
    count = len(values)
    size = count if family_size is None else _count(
        family_size, minimum=count, name="family_size",
    )
    if np.isinf(values).any() or ((values < 0) | (values > 1)).any():
        raise ValueError("p-values must lie in [0, 1] or be NaN")
    if count == 0:
        return pd.Series(values, index=pvalues.index, name=pvalues.name)
    missing = np.isnan(values)
    supplied = np.where(missing, 1.0, values)
    if method == "bonferroni":
        adjusted = supplied * size
    elif method == "holm":
        order = np.argsort(supplied, kind="stable")
        adjusted = np.empty(count)
        adjusted[order] = np.maximum.accumulate(supplied[order] * (size - np.arange(count)))
    else:
        adjusted = false_discovery_control(supplied, method="bh") * (size / count)
        if method == "by":
            adjusted *= float(digamma(size + 1) + np.euler_gamma)
    adjusted = np.minimum(adjusted, 1.0)
    adjusted[missing] = np.nan
    return pd.Series(adjusted, index=pvalues.index, name=pvalues.name)


def return_test_statistics(
    returns: pd.Series, *, periods_per_year: int = 252,
) -> dict[str, object]:
    """Test mean net return against zero on the supplied chronological sample.

    IID Student-t inference assumes Gaussian independent observations. HAC
    inference uses an asymptotic normal reference and Bartlett lag truncation.
    Both retain the supplied observation sequence and require complete values.
    Annualized Sharpe uses a zero risk-free rate and sample standard deviation.
    """
    values = _values(returns)
    annualization = _count(periods_per_year, minimum=1, name="periods_per_year")
    count = len(values)
    nonfinite = int((~np.isfinite(values)).sum())
    lags = int(np.floor(4.0 * (count / 100.0) ** (2.0 / 9.0)))
    result: dict[str, object] = {
        "status": "insufficient_observations", "n_observations": count,
        "nonfinite_count": nonfinite, "periods_per_year": annualization,
        "hac_lags": lags, "mean_return": None, "observed_sharpe": None,
        "iid_statistic": None, "iid_pvalue": None,
        "hac_statistic": None, "hac_pvalue": None,
    }
    if nonfinite:
        result["status"] = "nonfinite_observations"
        return result
    if count < 3:
        return result
    if np.all(values == values[0]):
        result["status"] = "zero_variance"
        return result
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        mean = float(np.mean(values))
        std = float(np.std(values, ddof=1))
        if not math.isfinite(std) or std <= 0:
            result["status"] = "undefined_variance"
            return result
        sharpe = mean / std * math.sqrt(annualization)
        iid_statistic = mean / std * math.sqrt(count)
        hac_statistic = newey_west_mean_tstat(pd.Series(values), lags=lags)
    if not all(math.isfinite(x) for x in (mean, sharpe, iid_statistic, hac_statistic)):
        result["status"] = "undefined_statistic"
        return result
    result.update(
        status="ok", mean_return=mean, observed_sharpe=sharpe,
        iid_statistic=iid_statistic,
        iid_pvalue=max(P_VALUE_FLOOR, float(2 * t.sf(abs(iid_statistic), count - 1))),
        hac_statistic=hac_statistic,
        hac_pvalue=max(P_VALUE_FLOOR, float(2 * norm.sf(abs(hac_statistic)))),
    )
    return result


def sharpe_haircut(
    observed_sharpe: float, *, n_observations: int,
    adjusted_pvalue: float, periods_per_year: int = 252,
) -> dict[str, float]:
    """Invert an adjusted two-sided IID p-value into signed Sharpe magnitude.

    This is an observed-family IID sensitivity. Harvey-Liu empirical-population
    calibration requires additional distribution and dependence assumptions.
    """
    count = _count(n_observations, minimum=3, name="n_observations")
    annualization = _count(periods_per_year, minimum=1, name="periods_per_year")
    for name, value in (("observed_sharpe", observed_sharpe), ("adjusted_pvalue", adjusted_pvalue)):
        if (isinstance(value, (bool, np.bool_))
                or not isinstance(value, (int, float, np.integer, np.floating))
                or not math.isfinite(value)):
            raise ValueError(f"{name} must be finite and real")
    if not 0 <= adjusted_pvalue <= 1:
        raise ValueError("adjusted_pvalue must lie in [0, 1]")
    raw_statistic = abs(observed_sharpe) * math.sqrt(count / annualization)
    if not math.isfinite(raw_statistic):
        raise ValueError("observed_sharpe implies an unrepresentable IID statistic")
    raw_p = float(2 * t.sf(raw_statistic, count - 1))
    if adjusted_pvalue < raw_p and not math.isclose(adjusted_pvalue, raw_p, rel_tol=1e-12):
        raise ValueError("adjusted_pvalue must be at least the raw IID p-value")
    adjusted_t = float(t.isf(adjusted_pvalue / 2, count - 1)) if adjusted_pvalue else raw_statistic
    if adjusted_pvalue == 1:
        adjusted_t = 0.0
    magnitude = min(abs(observed_sharpe), max(0.0, adjusted_t) * math.sqrt(annualization / count))
    return {
        "adjusted_sharpe": math.copysign(magnitude, observed_sharpe),
        "haircut_fraction": 1.0 - magnitude / abs(observed_sharpe) if observed_sharpe else 0.0,
        "adjusted_t_magnitude": min(raw_statistic, max(0.0, adjusted_t)),
    }
