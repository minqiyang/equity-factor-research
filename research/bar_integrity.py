"""Fail-closed bar integrity for synthetic research demos.

Price bars must be complete, finite, and strictly positive. A supplied volume
panel must be complete, finite, and strictly positive. The helpers raise when
those requirements fail. They do not fill, clip, drop, or repair incomplete
bars.

The local CSV loader remains a separate validation layer: zero volume is
loader-valid there. These helpers treat zero volume as invalid research-bar
input for Demo v0 and the M3-01 three-factor backtest demo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from features.operators import validate_panel_data


def require_complete_price_bars(
    prices: pd.DataFrame,
    *,
    expected_rows: int | None = None,
    expected_assets: int | None = None,
    name: str = "prices",
) -> pd.DataFrame:
    """Return a validated price panel with complete strictly positive bars."""

    panel = validate_panel_data(prices, name=name)
    _require_expected_shape(
        panel,
        expected_rows=expected_rows,
        expected_assets=expected_assets,
        name=name,
    )
    values = panel.to_numpy()
    if not np.isfinite(values).all():
        raise ValueError(
            f"{name} must be finite; silent fill, clip, drop, or repair of "
            "missing bars is refused"
        )
    if np.any(values <= 0.0):
        raise ValueError(
            f"{name} must be strictly positive; silent fill, clip, drop, or "
            "repair is refused"
        )
    return panel


def require_positive_volume_bars(
    volume: pd.DataFrame,
    *,
    prices: pd.DataFrame | None = None,
    name: str = "volume",
) -> pd.DataFrame:
    """Return a validated volume panel with complete strictly positive bars."""

    panel = validate_panel_data(volume, name=name)
    if prices is not None:
        price_panel = validate_panel_data(prices, name="prices")
        if not panel.index.equals(price_panel.index):
            raise ValueError(
                f"{name} index must match price dates; silent reindex or "
                "repair is refused"
            )
        if not panel.columns.equals(price_panel.columns):
            raise ValueError(
                f"{name} columns must match price assets; silent reindex or "
                "repair is refused"
            )
    values = panel.to_numpy()
    if not np.isfinite(values).all():
        raise ValueError(
            f"{name} must be finite; silent fill, clip, drop, or repair of "
            "missing bars is refused"
        )
    if np.any(values <= 0.0):
        raise ValueError(
            f"{name} must be strictly positive; zero volume is refused "
            "without silent fill, clip, drop, or repair"
        )
    return panel


def _require_expected_shape(
    panel: pd.DataFrame,
    *,
    expected_rows: int | None,
    expected_assets: int | None,
    name: str,
) -> None:
    if expected_rows is not None:
        _require_positive_int(expected_rows, "expected_rows")
        if len(panel.index) != expected_rows:
            raise ValueError(
                f"{name} must keep {expected_rows} source rows; silent drop "
                "or repair of missing bars is refused"
            )
    if expected_assets is not None:
        _require_positive_int(expected_assets, "expected_assets")
        if len(panel.columns) != expected_assets:
            raise ValueError(
                f"{name} must keep {expected_assets} assets; silent drop or "
                "repair of missing bars is refused"
            )


def _require_positive_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a non-boolean integer")
    if value < 1:
        raise ValueError(f"{name} must be at least 1")
