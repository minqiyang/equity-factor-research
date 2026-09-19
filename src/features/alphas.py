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
    decay_linear,
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


def alpha_015(high: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#015 from high and volume panels.

    ``-1 * ts_sum(cs_rank(ts_corr(cs_rank(high), cs_rank(volume), 3)), 3)``
    """

    panels = _validate_named_panels(high=high, volume=volume)
    _reject_negative_volume(panels["volume"])
    ranked_corr = cs_rank(ts_corr(cs_rank(panels["high"]), cs_rank(panels["volume"]), 3))
    return -1.0 * ts_sum(ranked_corr, 3)


def alpha_016(high: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#016 from high and volume panels.

    ``-1 * cs_rank(ts_cov(cs_rank(high), cs_rank(volume), 5))``
    """

    panels = _validate_named_panels(high=high, volume=volume)
    _reject_negative_volume(panels["volume"])
    return -1.0 * cs_rank(ts_cov(cs_rank(panels["high"]), cs_rank(panels["volume"]), 5))


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


def alpha_021(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    adv20: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#021 from close and volume panels.

    ``np.where((ts_mean(close, 8) + ts_std(close, 8)) < ts_mean(close, 2), -1,
    np.where(ts_mean(close, 2) < (ts_mean(close, 8) - ts_std(close, 8)), 1,
    np.where((volume / adv20) < 1, -1, 1)))``

    ``adv20`` defaults to ``ts_mean(volume, 20)`` when omitted. Incomplete
    trailing windows stay ``NaN``.
    """

    panels = _validate_named_panels(close=close, volume=volume)
    _reject_negative_volume(panels["volume"])
    adv20_panel = _resolve_adv20(panels["volume"], adv20)
    mean_8 = ts_mean(panels["close"], 8)
    std_8 = ts_std(panels["close"], 8)
    mean_2 = ts_mean(panels["close"], 2)
    volume_ratio = safe_divide(panels["volume"], adv20_panel)
    cond1 = (mean_8 + std_8) < mean_2
    cond2 = mean_2 < (mean_8 - std_8)
    cond3 = volume_ratio < 1.0
    result = np.where(
        cond1.to_numpy(),
        -1.0,
        np.where(cond2.to_numpy(), 1.0, np.where(cond3.to_numpy(), -1.0, 1.0)),
    )
    valid = mean_8.notna() & std_8.notna() & mean_2.notna() & volume_ratio.notna()
    return pd.DataFrame(
        result,
        index=panels["close"].index,
        columns=panels["close"].columns,
    ).where(valid)


def alpha_022(
    high: pd.DataFrame,
    volume: pd.DataFrame,
    close: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#022 from high, volume, and close panels.

    ``(-1 * ts_delta(ts_corr(high, volume, 5), 5)) * cs_rank(ts_std(close, 20))``
    """

    panels = _validate_named_panels(high=high, volume=volume, close=close)
    _reject_negative_volume(panels["volume"])
    return (-1.0 * ts_delta(ts_corr(panels["high"], panels["volume"], 5), 5)) * cs_rank(
        ts_std(panels["close"], 20)
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


def alpha_024(close: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#024 from a close-price panel.

    ``np.where((ts_delta(ts_mean(close, 100), 100) / ts_delay(close, 100)) <= 0.05,
    -1 * (close - ts_min(close, 100)), -1 * ts_delta(close, 3))``

    Incomplete trailing windows stay ``NaN``.
    """

    close_panel = validate_panel_data(close, name="close")
    mean_100 = ts_mean(close_panel, 100)
    ratio = safe_divide(ts_delta(mean_100, 100), ts_delay(close_panel, 100))
    true_branch = -1.0 * (close_panel - ts_min(close_panel, 100))
    false_branch = -1.0 * ts_delta(close_panel, 3)
    result = np.where(ratio.le(0.05).to_numpy(), true_branch.to_numpy(), false_branch.to_numpy())
    valid = ratio.notna() & true_branch.notna() & false_branch.notna()
    return pd.DataFrame(
        result,
        index=close_panel.index,
        columns=close_panel.columns,
    ).where(valid)


def alpha_025(
    high: pd.DataFrame,
    close: pd.DataFrame,
    returns: pd.DataFrame,
    volume: pd.DataFrame,
    vwap: pd.DataFrame,
    adv20: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#025 from OHLC, return, volume, and VWAP panels.

    ``cs_rank((((-1 * returns) * adv20) * vwap) * (high - close))``

    ``adv20`` defaults to ``ts_mean(volume, 20)`` when omitted.
    """

    panels = _validate_named_panels(
        high=high,
        close=close,
        returns=returns,
        volume=volume,
        vwap=vwap,
    )
    _reject_negative_volume(panels["volume"])
    adv20_panel = _resolve_adv20(panels["volume"], adv20)
    inner = (((-1.0 * panels["returns"]) * adv20_panel) * panels["vwap"]) * (
        panels["high"] - panels["close"]
    )
    return cs_rank(inner)


def alpha_026(high: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#026 from high and volume panels.

    ``-1 * ts_max(ts_corr(ts_rank(volume, 5), ts_rank(high, 5), 5), 3)``
    """

    panels = _validate_named_panels(high=high, volume=volume)
    _reject_negative_volume(panels["volume"])
    return -1.0 * ts_max(
        ts_corr(ts_rank(panels["volume"], 5), ts_rank(panels["high"], 5), 5),
        3,
    )


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


def alpha_030(close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#030 from close and volume panels.

    ``((1 - cs_rank(sign_sum)) * ts_sum(volume, 5)) / ts_sum(volume, 20)``
    where ``sign_sum`` is the sum of ``sign(ts_delta(close, 1))`` and its
    first two delays.
    """

    panels = _validate_named_panels(close=close, volume=volume)
    _reject_negative_volume(panels["volume"])
    delta_close = ts_delta(panels["close"], 1)
    sign_sum = (
        np.sign(delta_close)
        + np.sign(ts_delay(delta_close, 1))
        + np.sign(ts_delay(delta_close, 2))
    )
    numerator = (1.0 - cs_rank(sign_sum)) * ts_sum(panels["volume"], 5)
    return safe_divide(numerator, ts_sum(panels["volume"], 20))


def alpha_031(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    adv20: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#031 from close and volume panels.

    ``term1 = cs_rank(cs_rank(decay_linear(-1 * cs_rank(cs_rank(ts_delta(close, 10))), 10)))``
    ``term2 = cs_rank(-1 * ts_delta(close, 3))``
    ``term3 = sign(scale(ts_corr(adv20, decay_linear(volume, 20), 12)))``
    ``term1 + term2 + term3``

    ``adv20`` defaults to ``ts_mean(volume, 20)`` when omitted.
    """

    panels = _validate_named_panels(close=close, volume=volume)
    _reject_negative_volume(panels["volume"])
    adv20_panel = _resolve_adv20(panels["volume"], adv20)
    term1 = cs_rank(
        cs_rank(
            decay_linear(-1.0 * cs_rank(cs_rank(ts_delta(panels["close"], 10))), 10)
        )
    )
    term2 = cs_rank(-1.0 * ts_delta(panels["close"], 3))
    term3 = np.sign(
        scale(ts_corr(adv20_panel, decay_linear(panels["volume"], 20), 12))
    )
    return term1 + term2 + term3


def alpha_032(close: pd.DataFrame, vwap: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#032 from close and VWAP panels.

    ``scale((ts_mean(close, 7) - close) + (20 * scale(ts_corr(vwap,
    ts_delay(close, 5), 230))))``
    """

    panels = _validate_named_panels(close=close, vwap=vwap)
    inner = (ts_mean(panels["close"], 7) - panels["close"]) + (
        20.0 * scale(ts_corr(panels["vwap"], ts_delay(panels["close"], 5), 230))
    )
    return scale(inner)


def alpha_033(open_price: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#033 from open and close panels.

    ``cs_rank(-1 * (1 - (open / close)))``
    """

    panels = _validate_named_panels(open=open_price, close=close)
    open_over_close = safe_divide(panels["open"], panels["close"])
    return cs_rank(-1.0 * (1.0 - open_over_close))


def alpha_034(close: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#034 from close and return panels.

    ``cs_rank((1 - cs_rank(ts_std(returns, 2) / ts_std(returns, 5)))
    + (1 - cs_rank(ts_delta(close, 1))))``
    """

    panels = _validate_named_panels(close=close, returns=returns)
    vol_ratio = safe_divide(ts_std(panels["returns"], 2), ts_std(panels["returns"], 5))
    return cs_rank(
        (1.0 - cs_rank(vol_ratio)) + (1.0 - cs_rank(ts_delta(panels["close"], 1)))
    )


def alpha_035(
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
    volume: pd.DataFrame,
    returns: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#035 from OHLC, volume, and return panels.

    ``ts_rank(volume, 32) * (1 - ts_rank((close + high) - low, 16))
    * (1 - ts_rank(returns, 32))``
    """

    panels = _validate_named_panels(
        high=high,
        low=low,
        close=close,
        volume=volume,
        returns=returns,
    )
    _reject_negative_volume(panels["volume"])
    typical_range = (panels["close"] + panels["high"]) - panels["low"]
    return (
        ts_rank(panels["volume"], 32)
        * (1.0 - ts_rank(typical_range, 16))
        * (1.0 - ts_rank(panels["returns"], 32))
    )


def alpha_036(
    open_price: pd.DataFrame,
    close: pd.DataFrame,
    volume: pd.DataFrame,
    returns: pd.DataFrame,
    vwap: pd.DataFrame,
    adv20: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#036 from OHLCV, return, and VWAP panels.

    ``(2.21 * cs_rank(ts_corr(close - open, ts_delay(volume, 1), 15)))
    + (0.7 * cs_rank(open - close))
    + (0.73 * cs_rank(ts_rank(ts_delay(-1 * returns, 6), 5)))
    + cs_rank(abs(ts_corr(vwap, adv20, 6)))
    + (0.6 * cs_rank((ts_mean(close, 200) - open) * (close - open)))``

    ``adv20`` defaults to ``ts_mean(volume, 20)`` when omitted.
    """

    panels = _validate_named_panels(
        open=open_price,
        close=close,
        volume=volume,
        returns=returns,
        vwap=vwap,
    )
    _reject_negative_volume(panels["volume"])
    adv20_panel = _resolve_adv20(panels["volume"], adv20)
    close_minus_open = panels["close"] - panels["open"]
    return (
        (2.21 * cs_rank(ts_corr(close_minus_open, ts_delay(panels["volume"], 1), 15)))
        + (0.7 * cs_rank(panels["open"] - panels["close"]))
        + (0.73 * cs_rank(ts_rank(ts_delay(-1.0 * panels["returns"], 6), 5)))
        + cs_rank(ts_corr(panels["vwap"], adv20_panel, 6).abs())
        + (
            0.6
            * cs_rank(
                (ts_mean(panels["close"], 200) - panels["open"]) * close_minus_open
            )
        )
    )


def alpha_037(open_price: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#037 from open and close panels.

    ``cs_rank(ts_corr(ts_delay(open - close, 1), close, 200))
    + cs_rank(open - close)``
    """

    panels = _validate_named_panels(open=open_price, close=close)
    open_minus_close = panels["open"] - panels["close"]
    return cs_rank(ts_corr(ts_delay(open_minus_close, 1), panels["close"], 200)) + cs_rank(
        open_minus_close
    )


def alpha_038(open_price: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#038 from open and close panels.

    ``(-1 * cs_rank(ts_rank(close, 10))) * cs_rank(close / open)``
    """

    panels = _validate_named_panels(open=open_price, close=close)
    return (-1.0 * cs_rank(ts_rank(panels["close"], 10))) * cs_rank(
        safe_divide(panels["close"], panels["open"])
    )


def alpha_039(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    returns: pd.DataFrame,
    adv20: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#039 from close, volume, and return panels.

    ``(-1 * cs_rank(ts_delta(close, 7) * (1 - cs_rank(decay_linear(volume / adv20, 9)))))
    * (1 + cs_rank(ts_sum(returns, 250)))``

    ``adv20`` defaults to ``ts_mean(volume, 20)`` when omitted.
    """

    panels = _validate_named_panels(close=close, volume=volume, returns=returns)
    _reject_negative_volume(panels["volume"])
    adv20_panel = _resolve_adv20(panels["volume"], adv20)
    decayed = decay_linear(safe_divide(panels["volume"], adv20_panel), 9)
    return (
        -1.0 * cs_rank(ts_delta(panels["close"], 7) * (1.0 - cs_rank(decayed)))
    ) * (1.0 + cs_rank(ts_sum(panels["returns"], 250)))


def alpha_040(high: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#040 from high and volume panels.

    ``(-1 * cs_rank(ts_std(high, 10))) * ts_corr(high, volume, 10)``
    """

    panels = _validate_named_panels(high=high, volume=volume)
    _reject_negative_volume(panels["volume"])
    return (-1.0 * cs_rank(ts_std(panels["high"], 10))) * ts_corr(
        panels["high"],
        panels["volume"],
        10,
    )


def alpha_041(high: pd.DataFrame, low: pd.DataFrame, vwap: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#041 from high, low, and VWAP panels.

    ``sqrt((high * low).clip(lower=0)) - vwap``
    """

    panels = _validate_named_panels(high=high, low=low, vwap=vwap)
    geometric = np.sqrt((panels["high"] * panels["low"]).clip(lower=0.0))
    return geometric - panels["vwap"]


def alpha_042(close: pd.DataFrame, vwap: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#042 from close and VWAP panels.

    ``safe_divide(cs_rank(vwap - close), cs_rank(vwap + close))``
    """

    panels = _validate_named_panels(close=close, vwap=vwap)
    return safe_divide(
        cs_rank(panels["vwap"] - panels["close"]),
        cs_rank(panels["vwap"] + panels["close"]),
    )


def alpha_043(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    adv20: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#043 from close and volume panels.

    ``ts_rank(volume / adv20, 20) * ts_rank(-1 * ts_delta(close, 7), 8)``

    ``adv20`` defaults to ``ts_mean(volume, 20)`` when omitted.
    """

    panels = _validate_named_panels(close=close, volume=volume)
    _reject_negative_volume(panels["volume"])
    adv20_panel = _resolve_adv20(panels["volume"], adv20)
    volume_ratio = safe_divide(panels["volume"], adv20_panel)
    return ts_rank(volume_ratio, 20) * ts_rank(-1.0 * ts_delta(panels["close"], 7), 8)


def alpha_044(high: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#044 from high and volume panels.

    ``-1 * ts_corr(high, cs_rank(volume), 5)``
    """

    panels = _validate_named_panels(high=high, volume=volume)
    _reject_negative_volume(panels["volume"])
    return -1.0 * ts_corr(panels["high"], cs_rank(panels["volume"]), 5)


def alpha_045(close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#045 from close and volume panels.

    ``cs_rank(ts_mean(ts_delay(close, 5), 20) * ts_corr(close, volume, 2))
    * cs_rank(ts_corr(ts_sum(close, 5), ts_sum(close, 20), 2))``
    """

    panels = _validate_named_panels(close=close, volume=volume)
    _reject_negative_volume(panels["volume"])
    delayed_mean = ts_mean(ts_delay(panels["close"], 5), 20)
    close_volume_corr = ts_corr(panels["close"], panels["volume"], 2)
    sum_corr = ts_corr(ts_sum(panels["close"], 5), ts_sum(panels["close"], 20), 2)
    return cs_rank(delayed_mean * close_volume_corr) * cs_rank(sum_corr)


def alpha_046(close: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#046 from a close-price panel.

    ``drift = ((delay(close, 20) - delay(close, 10)) / 10)
    - ((delay(close, 10) - close) / 10)``
    ``where(drift > 0.25, -1, where(drift < 0, 1, -(close - delay(close, 1))))``

    Incomplete trailing windows stay ``NaN``.
    """

    close_panel = validate_panel_data(close, name="close")
    delayed_20 = ts_delay(close_panel, 20)
    delayed_10 = ts_delay(close_panel, 10)
    delayed_1 = ts_delay(close_panel, 1)
    drift = ((delayed_20 - delayed_10) / 10.0) - ((delayed_10 - close_panel) / 10.0)
    else_branch = -1.0 * (close_panel - delayed_1)
    result = np.where(
        drift.gt(0.25).to_numpy(),
        -1.0,
        np.where(drift.lt(0.0).to_numpy(), 1.0, else_branch.to_numpy()),
    )
    valid = delayed_20.notna() & delayed_10.notna() & delayed_1.notna()
    return pd.DataFrame(
        result,
        index=close_panel.index,
        columns=close_panel.columns,
    ).where(valid)


def alpha_049(close: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#049 from a close-price panel.

    ``np.where(((ts_delay(close, 10) - close) / 10) < -0.1, 1,
    -1 * ts_delta(close, 1))``

    Incomplete trailing windows stay ``NaN``.
    """

    close_panel = validate_panel_data(close, name="close")
    delayed = ts_delay(close_panel, 10)
    delta_close = ts_delta(close_panel, 1)
    cond = ((delayed - close_panel) / 10.0) < -0.1
    result = np.where(cond.to_numpy(), 1.0, (-1.0 * delta_close).to_numpy())
    valid = delayed.notna() & delta_close.notna()
    return pd.DataFrame(
        result,
        index=close_panel.index,
        columns=close_panel.columns,
    ).where(valid)


def alpha_050(volume: pd.DataFrame, vwap: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#050 from volume and VWAP panels.

    ``-1 * ts_max(cs_rank(ts_corr(cs_rank(volume), cs_rank(vwap), 5)), 5)``
    """

    panels = _validate_named_panels(volume=volume, vwap=vwap)
    _reject_negative_volume(panels["volume"])
    ranked_corr = cs_rank(ts_corr(cs_rank(panels["volume"]), cs_rank(panels["vwap"]), 5))
    return -1.0 * ts_max(ranked_corr, 5)


def alpha_051(close: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#051 from a close-price panel.

    ``np.where(((ts_delay(close, 20) - close) / 20) < -0.05, 1,
    -1 * ts_delta(close, 1))``

    Incomplete trailing windows stay ``NaN``.
    """

    close_panel = validate_panel_data(close, name="close")
    delayed = ts_delay(close_panel, 20)
    delta_close = ts_delta(close_panel, 1)
    cond = ((delayed - close_panel) / 20.0) < -0.05
    result = np.where(cond.to_numpy(), 1.0, (-1.0 * delta_close).to_numpy())
    valid = delayed.notna() & delta_close.notna()
    return pd.DataFrame(
        result,
        index=close_panel.index,
        columns=close_panel.columns,
    ).where(valid)


def alpha_052(
    low: pd.DataFrame,
    returns: pd.DataFrame,
    volume: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#052 from low, return, and volume panels.

    ``(-1 * ts_delta(ts_min(low, 5), 5))
    * cs_rank((ts_sum(returns, 240) - ts_sum(returns, 20)) / 220)
    * ts_rank(volume, 5)``
    """

    panels = _validate_named_panels(low=low, returns=returns, volume=volume)
    _reject_negative_volume(panels["volume"])
    min_delta = -1.0 * ts_delta(ts_min(panels["low"], 5), 5)
    return_drift = (
        ts_sum(panels["returns"], 240) - ts_sum(panels["returns"], 20)
    ) / 220.0
    return min_delta * cs_rank(return_drift) * ts_rank(panels["volume"], 5)


def alpha_053(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#053 from high, low, and close panels.

    ``-1 * ts_delta(((close - low) - (high - close)) / (close - low), 9)``

    A zero ``close - low`` denominator is replaced with ``NaN``.
    """

    panels = _validate_named_panels(high=high, low=low, close=close)
    close_minus_low = (panels["close"] - panels["low"]).replace(0.0, np.nan)
    inner = (
        (panels["close"] - panels["low"]) - (panels["high"] - panels["close"])
    ) / close_minus_low
    return -1.0 * ts_delta(inner, 9)


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


def alpha_055(
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
    volume: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#055 from OHLC and volume panels.

    ``-1 * ts_corr(cs_rank((close - ts_min(low, 12)) / (ts_max(high, 12)
    - ts_min(low, 12))), cs_rank(volume), 6)``

    A zero high-low trailing range is replaced with ``NaN``.
    """

    panels = _validate_named_panels(high=high, low=low, close=close, volume=volume)
    _reject_negative_volume(panels["volume"])
    min_low = ts_min(panels["low"], 12)
    hl_range = (ts_max(panels["high"], 12) - min_low).replace(0.0, np.nan)
    stoch = (panels["close"] - min_low) / hl_range
    return -1.0 * ts_corr(cs_rank(stoch), cs_rank(panels["volume"]), 6)


def alpha_060(
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
    volume: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#060 from OHLC and volume panels.

    ``-1 * ((2 * scale(cs_rank(inner))) - scale(cs_rank(ts_argmax(close, 10))))``
    where ``inner = (((close - low) - (high - close)) / (high - low)) * volume``.

    A zero high-low range is replaced with ``NaN``.
    """

    panels = _validate_named_panels(high=high, low=low, close=close, volume=volume)
    _reject_negative_volume(panels["volume"])
    hl_range = (panels["high"] - panels["low"]).replace(0.0, np.nan)
    inner = (
        ((panels["close"] - panels["low"]) - (panels["high"] - panels["close"])) / hl_range
    ) * panels["volume"]
    return -1.0 * (
        (2.0 * scale(cs_rank(inner))) - scale(cs_rank(ts_argmax(panels["close"], 10)))
    )


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
    "alpha_015",
    "alpha_016",
    "alpha_017",
    "alpha_018",
    "alpha_019",
    "alpha_020",
    "alpha_021",
    "alpha_022",
    "alpha_023",
    "alpha_024",
    "alpha_025",
    "alpha_026",
    "alpha_028",
    "alpha_030",
    "alpha_031",
    "alpha_032",
    "alpha_033",
    "alpha_034",
    "alpha_035",
    "alpha_036",
    "alpha_037",
    "alpha_038",
    "alpha_039",
    "alpha_040",
    "alpha_041",
    "alpha_042",
    "alpha_043",
    "alpha_044",
    "alpha_045",
    "alpha_046",
    "alpha_049",
    "alpha_050",
    "alpha_051",
    "alpha_052",
    "alpha_053",
    "alpha_054",
    "alpha_055",
    "alpha_060",
    "alpha_101",
]
