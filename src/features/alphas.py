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
    signed_power,
    ts_argmax,
    ts_corr,
    ts_delta,
    ts_rank,
    ts_std,
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


def alpha_006(open_price: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#006 from open and volume panels.

    ``-1 * correlation(open, volume, 10)``
    """

    panels = _validate_named_panels(open=open_price, volume=volume)
    _reject_negative_volume(panels["volume"])
    return -ts_corr(panels["open"], panels["volume"], 10)


def alpha_012(close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Calculate WorldQuant Alpha#012 from close and volume panels.

    ``sign(delta(volume, 1)) * (-1 * delta(close, 1))``
    """

    panels = _validate_named_panels(close=close, volume=volume)
    _reject_negative_volume(panels["volume"])
    return np.sign(delta(panels["volume"], periods=1)) * (
        -1.0 * delta(panels["close"], periods=1)
    )


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
    "alpha_006",
    "alpha_012",
]
