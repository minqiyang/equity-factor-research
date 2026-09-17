"""Observed source-row lag helpers for Demo v0 and the M3-01 demo.

Lag counts observed source rows in the supplied index. The demos keep that
index. A missing source row remains an omitted observation. Calendar-day
spans describe wall-time gaps. Invented sessions are refused against the
declared source index.
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral

import pandas as pd

from features.operators import validate_panel_data


DEMO_SIGNAL_LAG_PERIODS = 1
SIGNAL_LAG_UNIT = "observed_source_rows_within_bounded_accounting_slice"


@dataclass(frozen=True)
class CalendarDaySpanReport:
    """Wall-time span counts across consecutive observed timestamps."""

    pairs_over_one_day: int
    max_span_days: int


def report_calendar_day_spans(index: pd.DatetimeIndex) -> CalendarDaySpanReport:
    """Measure normalized adjacent spans; an index with no pairs reports zero."""

    normalized = index.normalize()
    spans = (normalized[1:] - normalized[:-1]).days
    return CalendarDaySpanReport(
        pairs_over_one_day=int((spans > 1).sum()),
        max_span_days=int(spans.max()) if len(spans) else 0,
    )


def require_observed_source_index(
    panel: pd.DataFrame,
    *,
    name: str = "prices",
) -> pd.DataFrame:
    """Return a validated panel whose index is the observed source rows."""

    validated = validate_panel_data(panel, name=name)
    if validated.index.hasnans:
        raise ValueError(
            f"{name} source index must not contain missing timestamps; "
            "silent bar insertion is refused"
        )
    return validated


def refuse_inserted_source_rows(
    panel: pd.DataFrame,
    *,
    observed_index: pd.DatetimeIndex,
    name: str = "prices",
) -> pd.DataFrame:
    """Refuse a panel whose index added or dropped observed source rows."""

    validated = require_observed_source_index(panel, name=name)
    observed = pd.DatetimeIndex(observed_index)
    extra = validated.index.difference(observed)
    if len(extra) > 0:
        raise ValueError(
            f"{name} silently inserted {len(extra)} source rows; "
            "silent bar insertion is refused"
        )
    missing = observed.difference(validated.index)
    if len(missing) > 0:
        raise ValueError(
            f"{name} dropped {len(missing)} observed source rows; "
            "silent drop or repair is refused"
        )
    if not validated.index.equals(observed):
        raise ValueError(
            f"{name} source index must match the observed source rows; "
            "silent reindex is refused"
        )
    return validated


def lag_by_observed_source_rows(
    panel: pd.DataFrame,
    lag_periods: int = DEMO_SIGNAL_LAG_PERIODS,
    *,
    name: str = "signals",
) -> pd.DataFrame:
    """Shift panel values by observed source rows."""

    if isinstance(lag_periods, bool) or not isinstance(lag_periods, Integral):
        raise TypeError(
            "lag_periods must be a non-boolean integer of at least one"
        )
    if lag_periods < 1:
        raise ValueError(
            "lag_periods must be a non-boolean integer of at least one"
        )
    validated = require_observed_source_index(panel, name=name)
    return validated.shift(int(lag_periods))
