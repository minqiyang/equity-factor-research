"""Point-in-time constituent membership table loader and universe mask builder.

Membership intervals describe effective dates. Permanent security IDs preserve
identity across repeated ticker episodes (PIT-005). Repeated symbols without IDs
are refused. Availability/announcement evidence remains a caller responsibility;
effective dates alone establish membership timing only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from data.csv_loader import (
    CSVValidationSummary,
    _parse_dates,
    _parse_symbols,
    _read_local_csv,
    _require_columns,
    _validate_local_csv_path,
)


@dataclass(frozen=True)
class ValidatedConstituentIntervals:
    """Validated point-in-time constituent intervals plus audit metadata."""

    data: pd.DataFrame
    summary: CSVValidationSummary


def load_constituent_intervals_csv(
    csv_path: str | Path,
    *,
    symbol_column: str = "symbol",
    start_date_column: str = "start_date",
    end_date_column: str = "end_date",
    permanent_id_column: str = "permanent_id",
) -> ValidatedConstituentIntervals:
    """Load and validate point-in-time constituent membership intervals from a local CSV.

    The CSV must contain symbol, start_date, and end_date columns.
    Repeated ticker episodes require permanent_id on every record. When provided,
    permanent IDs become membership-mask asset columns and must match price IDs.
    end_date may be empty / NaN to indicate an ongoing/active membership.
    Intervals for the same symbol must not overlap. Start date must be less than
    or equal to end date.

    Args:
        csv_path: Path to local CSV file.
        symbol_column: Name of symbol/identifier column.
        start_date_column: Name of effective entry date column.
        end_date_column: Name of effective exit date column (empty for active).

    Returns:
        ValidatedConstituentIntervals holding validated records and summary metadata.
    """

    path = _validate_local_csv_path(csv_path)
    raw = _read_local_csv(path)
    _require_columns(
        raw,
        [symbol_column, start_date_column, end_date_column],
        schema="constituent_intervals",
    )

    symbols = _parse_symbols(raw[symbol_column], field_name=symbol_column)
    start_dates = _parse_dates(raw[start_date_column], field_name=start_date_column)

    # End dates can be null/empty for currently active constituents
    end_raw = raw[end_date_column].astype(str).str.strip()
    is_open_ended = end_raw.isin({"", "na", "n/a", "nan", "null", "none"}) | raw[end_date_column].isna()

    end_dates_list: list[pd.Timestamp | None] = []
    for val, is_open in zip(end_raw, is_open_ended, strict=True):
        if is_open:
            end_dates_list.append(None)
        else:
            parsed = pd.to_datetime(val, errors="coerce")
            if pd.isna(parsed):
                raise ValueError(f"unparseable date in {end_date_column!r}: {val!r}")
            end_dates_list.append(pd.Timestamp(parsed).normalize())

    # Build validated DataFrame
    df = pd.DataFrame(
        {
            "symbol": symbols,
            "start_date": start_dates,
            "end_date": end_dates_list,
        }
    )

    if permanent_id_column in raw:
        df["permanent_id"] = _parse_symbols(raw[permanent_id_column], field_name=permanent_id_column)

    # Validate each interval: start_date <= end_date
    for _, row in df.iterrows():
        if pd.notna(row["end_date"]) and row["start_date"] > row["end_date"]:
            raise ValueError(
                f"symbol {row['symbol']!r} has start_date ({row['start_date']}) "
                f"after end_date ({row['end_date']})"
            )

    # Validate interval overlap separately from permanent identity.
    _validate_no_overlapping_intervals(df)
    _membership_identity_column(df)

    # Sort deterministically
    df = df.sort_values(by=["symbol", "start_date"]).reset_index(drop=True)

    summary = CSVValidationSummary(
        schema="constituent_intervals",
        source_path=path,
        source_row_count=len(df),
        value_column_count=len(df.columns),
        start_date=df["start_date"].min(),
        end_date=pd.Timestamp.max if any(e is None for e in end_dates_list) else max(e for e in end_dates_list if e is not None),
        missing_value_count=int(is_open_ended.sum()),
        columns=tuple(df.columns),
    )

    return ValidatedConstituentIntervals(data=df, summary=summary)


def build_membership_mask(
    intervals: ValidatedConstituentIntervals | pd.DataFrame,
    dates: pd.DatetimeIndex,
    assets: list[str] | None = None,
    *,
    inclusive_exit: bool = False,
) -> pd.DataFrame:
    """Build a point-in-time boolean universe membership mask for given dates and assets.

    For each date t and asset a, the mask is True if and only if t falls within
    an active membership interval [start_date, end_date) (or [start_date, end_date]
    if inclusive_exit=True).

    Args:
        intervals: ValidatedConstituentIntervals object or DataFrame with symbol,
            start_date, and end_date columns.
        dates: DatetimeIndex of trading/rebalance dates to evaluate. Must be sorted
            and monotonic increasing.
        assets: Optional list of assets/symbols to include as columns. If None,
            uses permanent IDs when supplied, otherwise single-episode symbols.
            Price panels must use these same identifiers.
        inclusive_exit: If True, end_date is inclusive (t <= end_date).
            If False (default), end_date is exclusive (t < end_date), meaning
            an asset removed on date t is not eligible for selection on date t.

    Returns:
        DataFrame of shape (len(dates), len(assets)) with boolean values.
    """

    if isinstance(intervals, ValidatedConstituentIntervals):
        table = intervals.data
    elif isinstance(intervals, pd.DataFrame):
        table = intervals
    else:
        raise TypeError("intervals must be a ValidatedConstituentIntervals or pd.DataFrame")

    if not isinstance(dates, pd.DatetimeIndex):
        raise TypeError("dates must be a pandas DatetimeIndex")
    if dates.empty:
        raise ValueError("dates must not be empty")
    if not dates.is_monotonic_increasing:
        raise ValueError("dates must be monotonic increasing")

    _validate_no_overlapping_intervals(table)
    identity_column = _membership_identity_column(table)
    all_symbols = sorted(table[identity_column].unique())
    target_assets = list(assets) if assets is not None else all_symbols
    if not target_assets:
        raise ValueError("assets list must not be empty")

    if identity_column == "permanent_id":
        ticker_aliases = set(table["symbol"]) - set(all_symbols)
        if ticker_aliases.intersection(target_assets):
            raise ValueError("PIT-005: assets must use permanent IDs for identity-backed intervals")
    mask = pd.DataFrame(False, index=dates, columns=target_assets, dtype=bool)

    # Group intervals by symbol
    grouped = table.groupby(identity_column)
    for symbol in target_assets:
        if symbol not in grouped.groups:
            continue
        symbol_intervals = grouped.get_group(symbol)
        for _, row in symbol_intervals.iterrows():
            start = row["start_date"]
            end = row["end_date"]
            if pd.isna(end):
                condition = dates >= start
            elif inclusive_exit:
                condition = (dates >= start) & (dates <= end)
            else:
                condition = (dates >= start) & (dates < end)
            mask.loc[condition, symbol] = True

    return mask


def _validate_no_overlapping_intervals(df: pd.DataFrame) -> None:
    """Ensure no symbol has overlapping membership intervals."""

    for symbol, group in df.groupby("symbol"):
        sorted_intervals = group.sort_values(by="start_date")
        prev_end: pd.Timestamp | None = None
        for _, row in sorted_intervals.iterrows():
            start = row["start_date"]
            end = row["end_date"]
            if prev_end is not None:
                if start < prev_end:
                    raise ValueError(
                        f"symbol {symbol!r} has overlapping membership intervals: "
                        f"interval starts at {start} before previous interval ended at {prev_end}"
                    )
            prev_end = pd.Timestamp.max if pd.isna(end) else end


def _membership_identity_column(table: pd.DataFrame) -> str:
    """Require identity evidence at both CSV and direct-frame mask boundaries."""
    if "permanent_id" in table:
        ids = table["permanent_id"]
        if ids.isna().any() or ids.astype(str).str.strip().eq("").any():
            raise ValueError("PIT-005: permanent_id must be present for every interval")
        # An identity can reenter under the same ticker or an updated alias.
        _validate_no_overlapping_intervals(table.assign(symbol=ids))
        return "permanent_id"
    if table["symbol"].duplicated().any():
        raise ValueError("PIT-005: repeated ticker episodes require permanent_id")
    return "symbol"
