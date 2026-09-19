"""Classical WorldQuant-style price-volume alpha features.

The functions in this module implement public formulaic-alpha definitions as
research features. They do not select portfolios, apply trading lags, run
backtests, or claim profitability.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from features.operators import (
    cs_rank,
    delta,
    safe_divide,
    scale,
    signed_power,
    ts_argmax,
    ts_corr,
    ts_cov,
    ts_delay,
    ts_delta,
    ts_max,
    ts_mean,
    ts_min,
    ts_rank,
    ts_std,
    ts_sum,
    validate_panel_data,
)


def alpha_001(close: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#001 from close and return panels.

    ``rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close),
    2), 5)) - 0.5``

    The feature at date ``t`` uses ``close[t]``, ``returns[t]``, and trailing
    history only.
    """

    panels = _validate_named_panels(close=close, returns=returns)
    inner = panels["close"].where(
        ~panels["returns"].lt(0.0),
        ts_std(panels["returns"], 20),
    )
    return cs_rank(ts_argmax(signed_power(inner, 2.0), 5)) - 0.5


def alpha_002(
    open_price: pd.DataFrame,
    close: pd.DataFrame,
    volume: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#002 from open, close, and volume panels.

    ``-1 * correlation(rank(delta(log(volume), 2)),
    rank((close - open) / open), 6)``

    Non-positive volume produces ``NaN`` in the log term. The feature at date
    ``t`` uses open, close, and volume on or before ``t`` only.
    """

    panels = _validate_named_panels(open=open_price, close=close, volume=volume)
    _reject_negative_volume(panels["volume"])
    positive_volume = panels["volume"].where(panels["volume"] > 0.0)
    log_volume = pd.DataFrame(
        np.log(positive_volume.to_numpy(dtype=float)),
        index=positive_volume.index,
        columns=positive_volume.columns,
    )
    intraday_return = safe_divide(panels["close"] - panels["open"], panels["open"])
    return -ts_corr(
        cs_rank(ts_delta(log_volume, 2)),
        cs_rank(intraday_return),
        6,
    )


def alpha_003(open_price: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#003 from open and volume panels.

    ``-1 * correlation(rank(open), rank(volume), 10)``
    """

    panels = _validate_named_panels(open=open_price, volume=volume)
    _reject_negative_volume(panels["volume"])
    return -ts_corr(cs_rank(panels["open"]), cs_rank(panels["volume"]), 10)


def alpha_004(low: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#004 from a low-price panel.

    ``-1 * Ts_Rank(rank(low), 9)``
    """

    low_panel = validate_panel_data(low, name="low")
    return -ts_rank(cs_rank(low_panel), 9)


def alpha_005(
    open_price: pd.DataFrame,
    close: pd.DataFrame,
    vwap: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#005 from open, close, and VWAP panels.

    ``rank(open - ts_mean(vwap, 10)) * (-1 * abs(rank(close - vwap)))``

    The feature at date ``t`` uses open, close, and VWAP on or before ``t``
    only.
    """

    panels = _validate_named_panels(open=open_price, close=close, vwap=vwap)
    return cs_rank(panels["open"] - ts_mean(panels["vwap"], 10)) * (
        -1.0 * cs_rank(panels["close"] - panels["vwap"]).abs()
    )


def alpha_006(open_price: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#006 from open and volume panels.

    ``-1 * correlation(open, volume, 10)``
    """

    panels = _validate_named_panels(open=open_price, volume=volume)
    _reject_negative_volume(panels["volume"])
    return -ts_corr(panels["open"], panels["volume"], 10)


def alpha_007(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    adv20: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#007 from close and volume panels.

    ``np.where(adv20 < volume, (-1 * ts_rank(abs(ts_delta(close, 7)), 60))
    * sign(ts_delta(close, 7)), -1)``

    ``adv20`` defaults to ``ts_mean(volume, 20)`` when omitted. Missing
    volume or incomplete average-volume windows stay ``NaN``.
    """

    panels = _validate_named_panels(close=close, volume=volume)
    _reject_negative_volume(panels["volume"])
    adv20_panel = _resolve_adv20(panels["volume"], adv20)
    delta_close = ts_delta(panels["close"], 7)
    true_branch = (-1.0 * ts_rank(delta_close.abs(), 60)) * np.sign(delta_close)
    result = true_branch.where(adv20_panel < panels["volume"], -1.0)
    valid = adv20_panel.notna() & panels["volume"].notna()
    return result.where(valid)


def alpha_008(open_price: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#008 from open and return panels.

    ``-1 * rank((ts_sum(open, 5) * ts_sum(returns, 5))
    - ts_delay(ts_sum(open, 5) * ts_sum(returns, 5), 10))``
    """

    panels = _validate_named_panels(open=open_price, returns=returns)
    summed_product = ts_sum(panels["open"], 5) * ts_sum(panels["returns"], 5)
    return -1.0 * cs_rank(summed_product - ts_delay(summed_product, 10))


def alpha_009(close: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#009 from a close-price panel.

    ``cs_rank(delta if ts_min(delta, 5) > 0 or ts_max(delta, 5) < 0
    else -delta)`` where ``delta = ts_delta(close, 1)``.

    Incomplete trailing windows stay ``NaN`` instead of taking the else branch.
    """

    close_panel = validate_panel_data(close, name="close")
    delta_close = ts_delta(close_panel, 1)
    trailing_min = ts_min(delta_close, 5)
    trailing_max = ts_max(delta_close, 5)
    trend_continuation = trailing_min.gt(0.0) | trailing_max.lt(0.0)
    inner = delta_close.where(trend_continuation, -1.0 * delta_close)
    valid = delta_close.notna() & trailing_min.notna() & trailing_max.notna()
    return cs_rank(inner.where(valid))


def alpha_010(close: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#010 from a close-price panel.

    ``rank(ts_delta(close, 1) if ts_min(ts_delta(close, 1), 4) > 0 or
    ts_max(ts_delta(close, 1), 4) < 0 else -ts_delta(close, 1))``

    Incomplete trailing windows stay ``NaN`` instead of taking the else branch.
    """

    close_panel = validate_panel_data(close, name="close")
    delta_close = ts_delta(close_panel, 1)
    trailing_min = ts_min(delta_close, 4)
    trailing_max = ts_max(delta_close, 4)
    trend_continuation = trailing_min.gt(0.0) | trailing_max.lt(0.0)
    inner = delta_close.where(trend_continuation, -1.0 * delta_close)
    valid = delta_close.notna() & trailing_min.notna() & trailing_max.notna()
    return cs_rank(inner.where(valid))


def alpha_012(close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#012 from close and volume panels.

    ``sign(delta(volume, 1)) * (-1 * delta(close, 1))``
    """

    panels = _validate_named_panels(close=close, volume=volume)
    _reject_negative_volume(panels["volume"])
    return np.sign(delta(panels["volume"], periods=1)) * (
        -1.0 * delta(panels["close"], periods=1)
    )


def alpha_013(close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#013 from close and volume panels.

    ``-1 * rank(ts_cov(rank(close), rank(volume), 5))``
    """

    panels = _validate_named_panels(close=close, volume=volume)
    _reject_negative_volume(panels["volume"])
    return -1.0 * cs_rank(ts_cov(cs_rank(panels["close"]), cs_rank(panels["volume"]), 5))


def alpha_014(
    open_price: pd.DataFrame,
    volume: pd.DataFrame,
    returns: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#014 from open, volume, and return panels.

    ``-1 * rank(ts_delta(returns, 3)) * ts_corr(open, volume, 10)``
    """

    panels = _validate_named_panels(open=open_price, volume=volume, returns=returns)
    _reject_negative_volume(panels["volume"])
    return (-1.0 * cs_rank(ts_delta(panels["returns"], 3))) * ts_corr(
        panels["open"],
        panels["volume"],
        10,
    )


def alpha_017(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    adv20: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#017 from close and volume panels.

    ``(-1 * cs_rank(ts_rank(close, 10))) * cs_rank(ts_delta(ts_delta(close, 1), 1))
    * cs_rank(ts_rank(volume / adv20, 5))``

    ``adv20`` defaults to ``ts_mean(volume, 20)`` when omitted.
    """

    panels = _validate_named_panels(close=close, volume=volume)
    _reject_negative_volume(panels["volume"])
    adv20_panel = _resolve_adv20(panels["volume"], adv20)
    volume_ratio = safe_divide(panels["volume"], adv20_panel)
    return (
        (-1.0 * cs_rank(ts_rank(panels["close"], 10)))
        * cs_rank(ts_delta(ts_delta(panels["close"], 1), 1))
        * cs_rank(ts_rank(volume_ratio, 5))
    )


def alpha_018(open_price: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#018 from open and close panels.

    ``-1 * rank(ts_std(abs(close - open), 5) + (close - open)
    + ts_corr(close, open, 10))``
    """

    panels = _validate_named_panels(open=open_price, close=close)
    spread = panels["close"] - panels["open"]
    inner = ts_std(spread.abs(), 5) + spread + ts_corr(panels["close"], panels["open"], 10)
    return -1.0 * cs_rank(inner)


def alpha_019(close: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#019 from close and return panels.

    ``(-1 * sign((close - ts_delay(close, 7)) + ts_delta(close, 7)))
    * (1 + cs_rank(1 + ts_sum(returns, 250)))``
    """

    panels = _validate_named_panels(close=close, returns=returns)
    signed_move = (panels["close"] - ts_delay(panels["close"], 7)) + ts_delta(
        panels["close"],
        7,
    )
    return (-1.0 * np.sign(signed_move)) * (
        1.0 + cs_rank(1.0 + ts_sum(panels["returns"], 250))
    )


def alpha_020(
    open_price: pd.DataFrame,
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#020 from open, high, low, and close panels.

    ``-1 * rank(open - ts_delay(high, 1)) * rank(open - ts_delay(close, 1))
    * rank(open - ts_delay(low, 1))``
    """

    panels = _validate_named_panels(open=open_price, high=high, low=low, close=close)
    return (
        -1.0
        * cs_rank(panels["open"] - ts_delay(panels["high"], 1))
        * cs_rank(panels["open"] - ts_delay(panels["close"], 1))
        * cs_rank(panels["open"] - ts_delay(panels["low"], 1))
    )


def alpha_023(high: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#023 from a high-price panel.

    ``np.where(ts_mean(high, 20) < high, -1 * ts_delta(high, 2), 0)``

    Incomplete trailing windows stay ``NaN`` instead of taking the else branch.
    """

    high_panel = validate_panel_data(high, name="high")
    mean_high = ts_mean(high_panel, 20)
    delta_high = ts_delta(high_panel, 2)
    result = (-1.0 * delta_high).where(mean_high < high_panel, 0.0)
    valid = mean_high.notna() & delta_high.notna()
    return result.where(valid)


def alpha_028(
    close: pd.DataFrame,
    high: pd.DataFrame,
    low: pd.DataFrame,
    volume: pd.DataFrame,
    adv20: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#028 from OHLC and volume panels.

    ``scale((ts_corr(adv20, low, 5) + (high + low) / 2) - close)``

    ``adv20`` defaults to ``ts_mean(volume, 20)`` when omitted.
    """

    panels = _validate_named_panels(close=close, high=high, low=low, volume=volume)
    _reject_negative_volume(panels["volume"])
    adv20_panel = _resolve_adv20(panels["volume"], adv20)
    typical_price = (panels["high"] + panels["low"]) / 2.0
    inner = ts_corr(adv20_panel, panels["low"], 5) + typical_price - panels["close"]
    return scale(inner)


def alpha_033(open_price: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#033 from open and close panels.

    ``cs_rank(-1 * (1 - (open / close)))``
    """

    panels = _validate_named_panels(open=open_price, close=close)
    open_over_close = safe_divide(panels["open"], panels["close"])
    return cs_rank(-1.0 * (1.0 - open_over_close))


def alpha_038(open_price: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#038 from open and close panels.

    ``(-1 * cs_rank(ts_rank(close, 10))) * cs_rank(close / open)``
    """

    panels = _validate_named_panels(open=open_price, close=close)
    return (-1.0 * cs_rank(ts_rank(panels["close"], 10))) * cs_rank(
        safe_divide(panels["close"], panels["open"])
    )


def alpha_054(
    open_price: pd.DataFrame,
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#054 from open, high, low, and close panels.

    ``(-1 * ((low - close) * (open ** 5))) / ((low - high) * (close ** 5))``

    A zero denominator is replaced with ``NaN``.
    """

    panels = _validate_named_panels(open=open_price, high=high, low=low, close=close)
    numerator = -1.0 * ((panels["low"] - panels["close"]) * panels["open"].pow(5.0))
    denominator = (panels["low"] - panels["high"]) * panels["close"].pow(5.0)
    return numerator / denominator.replace(0.0, np.nan)


def alpha_101(
    open_price: pd.DataFrame,
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#101 from open, high, low, and close panels.

    ``(close - open) / ((high - low) + 0.001)``
    """

    panels = _validate_named_panels(open=open_price, high=high, low=low, close=close)
    return (panels["close"] - panels["open"]) / ((panels["high"] - panels["low"]) + 0.001)


def _resolve_adv20(
    volume: pd.DataFrame,
    adv20: pd.DataFrame | None,
    *,
    window: int = 20,
) -> pd.DataFrame:
    if adv20 is None:
        return ts_mean(volume, window)
    return _validate_named_panels(volume=volume, adv20=adv20)["adv20"]


def _validate_named_panels(**panels: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if not panels:
        raise ValueError("at least one panel is required")

    validated = {
        name: validate_panel_data(panel, name=name) for name, panel in panels.items()
    }
    names = list(validated)
    first_name = names[0]
    first_panel = validated[first_name]
    for name in names[1:]:
        other = validated[name]
        if not first_panel.index.equals(other.index):
            raise ValueError(f"{first_name} and {name} must have identical indexes")
        if not first_panel.columns.equals(other.columns):
            raise ValueError(f"{first_name} and {name} must have identical columns")
    return validated


def _reject_negative_volume(volume: pd.DataFrame) -> None:
    if (volume < 0.0).any().any():
        raise ValueError("volume must contain non-negative values when present")


__all__ = [
    "alpha_001",
    "alpha_002",
    "alpha_003",
    "alpha_004",
    "alpha_005",
    "alpha_006",
    "alpha_007",
    "alpha_008",
    "alpha_009",
    "alpha_010",
    "alpha_012",
    "alpha_013",
    "alpha_014",
    "alpha_017",
    "alpha_018",
    "alpha_019",
    "alpha_020",
    "alpha_023",
    "alpha_028",
    "alpha_033",
    "alpha_038",
    "alpha_054",
    "alpha_101",
]
