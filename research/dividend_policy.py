"""Cash-dividend overlay policy for Demo v0 and the M3-01 demo.

Held returns use the supplied price series only: current / previous - 1.
A separate cash-dividend overlay on that series is refused. Supplied event
tables receive an exact date-membership check against the declared source.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


PRICE_RETURN_BASIS = "supplied_price_series_simple_return_v1"
CASH_DIVIDEND_OVERLAY_POLICY = (
    "refuse_separate_cash_dividend_on_supplied_price_series"
)


def require_event_date_membership(
    event_table: pd.DataFrame | None,
    *,
    observed_index: pd.DatetimeIndex,
) -> None:
    """Check a date-indexed event table against the declared source timestamps.

    Repeated dates support multiple events on one source row. Event columns
    remain opaque metadata; this check preserves the table and source index.
    """

    if event_table is None:
        return
    if not isinstance(event_table, pd.DataFrame):
        raise TypeError("event_table must be a pandas DataFrame")
    if not isinstance(event_table.index, pd.DatetimeIndex):
        raise TypeError("event_table must have a DatetimeIndex of event dates")
    if event_table.index.hasnans:
        raise ValueError("event_table contains missing event dates; refused")
    if not event_table.index.isin(observed_index).all():
        raise ValueError("event date absent from the declared source index; refused")


def refuse_cash_dividend_overlay(
    cash_dividends: Any = None,
    *,
    name: str = "cash_dividends",
) -> None:
    """Refuse a separate cash-dividend overlay on the supplied price series."""

    if cash_dividends is None:
        return
    raise ValueError(
        f"{name} overlay on the supplied price series is refused; "
        "adding cash dividends double-counts PIT-007"
    )


def price_series_simple_return(
    previous_price: float,
    current_price: float,
) -> float:
    """Return current / previous - 1 from the supplied price series."""

    return current_price / previous_price - 1.0
