"""Cash-dividend overlay policy for Demo v0 and the M3-01 demo.

Held returns use the supplied price series only: current / previous - 1.
A separate cash-dividend overlay on that series is refused. Event-level
corporate-action reconciliation remains later Milestone 3/4 work.
"""

from __future__ import annotations

from typing import Any


PRICE_RETURN_BASIS = "supplied_price_series_simple_return_v1"
CASH_DIVIDEND_OVERLAY_POLICY = (
    "refuse_separate_cash_dividend_on_supplied_price_series"
)


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
