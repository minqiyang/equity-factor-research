"""Strict local CSV loaders for research data panels.

This module reads user-provided local CSV files only. It does not download
data, call vendor APIs, store credentials, connect to brokers, place orders, or
make profitability claims.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REMOTE_PATH_PREFIXES = (
    "http://",
    "https://",
    "ftp://",
    "s3://",
    "gs://",
)

MISSING_SENTINELS = {"", "na", "n/a", "nan", "null", "none"}


@dataclass(frozen=True)
class CSVValidationSummary:
    """Audit metadata for a loaded local CSV input."""

    schema: str
    source_path: Path
    source_row_count: int
    value_column_count: int
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    missing_value_count: int
    columns: tuple[str, ...]


@dataclass(frozen=True)
class ValidatedCSVPanel:
    """Validated wide date-asset panel plus audit metadata."""

    data: pd.DataFrame
    summary: CSVValidationSummary


@dataclass(frozen=True)
class ValidatedCSVSeries:
    """Validated date-indexed series plus audit metadata."""

    data: pd.Series
    summary: CSVValidationSummary


def load_wide_price_csv(
    csv_path: str | Path,
    *,
    date_column: str = "date",
    allow_missing: bool = False,
) -> ValidatedCSVPanel:
    """Load a wide adjusted-close price panel from a local CSV file.

    The CSV must contain a date column plus one numeric column per asset.
    Dates must be sorted, duplicate-free, and parseable. Price values must be
    numeric and positive when present. Missing values are rejected by default
    and preserved only when ``allow_missing=True``.
    """

    path = _validate_local_csv_path(csv_path)
    raw = _read_local_csv(path)
    _require_columns(raw, [date_column], schema="wide_price")

    dates = _parse_dates(raw[date_column], field_name=date_column)
    _validate_unique_sorted_dates(dates, field_name=date_column)

    value_columns = [column for column in raw.columns if column != date_column]
    if not value_columns:
        raise ValueError("wide_price CSV must contain at least one asset column")

    panel = pd.DataFrame(index=dates)
    for column in value_columns:
        panel[column] = _parse_numeric_column(
            raw[column],
            field_name=column,
            allow_missing=allow_missing,
        ).to_numpy()

    _validate_positive_values(panel, field_name="wide_price values")
    panel.index.name = date_column
    return ValidatedCSVPanel(
        data=panel,
        summary=_panel_summary(
            schema="wide_price",
            source_path=path,
            source_row_count=len(raw),
            panel=panel,
        ),
    )


def load_long_price_csv(
    csv_path: str | Path,
    *,
    date_column: str = "date",
    symbol_column: str = "symbol",
    value_column: str = "adjusted_close",
    allow_missing: bool = False,
) -> ValidatedCSVPanel:
    """Load long-form adjusted-close prices and pivot to a wide panel."""

    path = _validate_local_csv_path(csv_path)
    raw = _read_local_csv(path)
    _require_columns(raw, [date_column, symbol_column, value_column], schema="long_price")

    dates = _parse_dates(raw[date_column], field_name=date_column)
    symbols = _parse_symbols(raw[symbol_column], field_name=symbol_column)
    values = _parse_numeric_column(
        raw[value_column],
        field_name=value_column,
        allow_missing=allow_missing,
    )

    duplicate_rows = pd.DataFrame({"date": dates, "symbol": symbols}).duplicated()
    if duplicate_rows.any():
        raise ValueError("long_price CSV must not contain duplicate (date, symbol) rows")

    long_data = pd.DataFrame(
        {
            "date": dates,
            "symbol": symbols,
            value_column: values.to_numpy(),
        }
    )
    panel = long_data.pivot(index="date", columns="symbol", values=value_column)
    panel = panel.sort_index()
    panel = panel.reindex(columns=_unique_in_order(symbols))
    panel.columns.name = None
    panel.index.name = date_column

    _validate_positive_values(panel, field_name=value_column)
    return ValidatedCSVPanel(
        data=panel,
        summary=_panel_summary(
            schema="long_price",
            source_path=path,
            source_row_count=len(raw),
            panel=panel,
        ),
    )


def load_benchmark_price_csv(
    csv_path: str | Path,
    *,
    date_column: str = "date",
    value_column: str = "benchmark_price",
    allow_missing: bool = False,
) -> ValidatedCSVSeries:
    """Load a local benchmark price series from a CSV file."""

    path = _validate_local_csv_path(csv_path)
    raw = _read_local_csv(path)
    _require_columns(raw, [date_column, value_column], schema="benchmark_price")

    dates = _parse_dates(raw[date_column], field_name=date_column)
    _validate_unique_sorted_dates(dates, field_name=date_column)
    values = _parse_numeric_column(
        raw[value_column],
        field_name=value_column,
        allow_missing=allow_missing,
    )
    series = pd.Series(values.to_numpy(), index=dates, name=value_column)
    series.index.name = date_column

    _validate_positive_values(series, field_name=value_column)
    return ValidatedCSVSeries(
        data=series,
        summary=CSVValidationSummary(
            schema="benchmark_price",
            source_path=path,
            source_row_count=len(raw),
            value_column_count=1,
            start_date=series.index.min(),
            end_date=series.index.max(),
            missing_value_count=int(series.isna().sum()),
            columns=(value_column,),
        ),
    )


def _validate_local_csv_path(csv_path: str | Path) -> Path:
    raw_path = str(csv_path).strip()
    if raw_path.lower().startswith(REMOTE_PATH_PREFIXES):
        raise ValueError("csv_path must be a local filesystem path; remote data access is not supported")

    path = Path(csv_path)
    if path.suffix.lower() != ".csv":
        raise ValueError("csv_path must point to a .csv file")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _read_local_csv(path: Path) -> pd.DataFrame:
    header = _read_header(path)
    duplicated_columns = _duplicates(header)
    if duplicated_columns:
        raise ValueError(f"CSV header contains duplicate columns: {duplicated_columns}")

    return pd.read_csv(path, keep_default_na=False, dtype=str)


def _read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        try:
            return next(reader)
        except StopIteration as exc:
            raise ValueError("CSV file must contain a header row") from exc


def _require_columns(frame: pd.DataFrame, columns: list[str], *, schema: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{schema} CSV is missing required columns: {missing}")


def _parse_dates(values: pd.Series, *, field_name: str) -> pd.DatetimeIndex:
    try:
        parsed = pd.to_datetime(values, errors="raise")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must contain parseable dates") from exc

    if parsed.isna().any():
        raise ValueError(f"{field_name} must not contain missing dates")

    try:
        timezone = parsed.dt.tz
    except AttributeError as exc:
        raise ValueError(f"{field_name} must parse to one consistent datetime dtype") from exc

    if timezone is not None:
        raise ValueError(f"{field_name} must be timezone-naive")

    return pd.DatetimeIndex(parsed)


def _validate_unique_sorted_dates(dates: pd.DatetimeIndex, *, field_name: str) -> None:
    if dates.has_duplicates:
        raise ValueError(f"{field_name} must not contain duplicate dates")
    if not dates.is_monotonic_increasing:
        raise ValueError(f"{field_name} must be sorted in increasing date order")


def _parse_symbols(values: pd.Series, *, field_name: str) -> pd.Series:
    symbols = values.astype(str).str.strip()
    missing_symbols = symbols.str.lower().isin(MISSING_SENTINELS)
    if missing_symbols.any():
        raise ValueError(f"{field_name} must not contain missing symbols")
    return symbols


def _parse_numeric_column(
    values: pd.Series,
    *,
    field_name: str,
    allow_missing: bool,
) -> pd.Series:
    missing_mask = _missing_value_mask(values)
    if missing_mask.any() and not allow_missing:
        raise ValueError(
            f"{field_name} contains {int(missing_mask.sum())} missing values; "
            "pass allow_missing=True only if missing values should be preserved"
        )

    cleaned = values.mask(missing_mask, np.nan)
    try:
        numeric = pd.to_numeric(cleaned, errors="raise")
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{field_name} must contain numeric values") from exc

    numeric = numeric.astype(float)
    finite_or_missing = np.isfinite(numeric.to_numpy()) | numeric.isna().to_numpy()
    if not finite_or_missing.all():
        raise ValueError(f"{field_name} must contain finite numeric values")
    return numeric


def _missing_value_mask(values: pd.Series) -> pd.Series:
    if values.isna().any():
        base_mask = values.isna()
    else:
        base_mask = pd.Series(False, index=values.index)

    if values.dtype == object or pd.api.types.is_string_dtype(values.dtype):
        text = values.astype(str).str.strip().str.lower()
        return base_mask | text.isin(MISSING_SENTINELS)
    return base_mask


def _validate_positive_values(values: pd.DataFrame | pd.Series, *, field_name: str) -> None:
    invalid = values.notna() & values.le(0.0)
    if isinstance(invalid, pd.DataFrame):
        has_invalid = invalid.to_numpy().any()
    else:
        has_invalid = bool(invalid.any())

    if has_invalid:
        raise ValueError(f"{field_name} must contain only positive values when present")


def _panel_summary(
    *,
    schema: str,
    source_path: Path,
    source_row_count: int,
    panel: pd.DataFrame,
) -> CSVValidationSummary:
    return CSVValidationSummary(
        schema=schema,
        source_path=source_path,
        source_row_count=source_row_count,
        value_column_count=len(panel.columns),
        start_date=panel.index.min(),
        end_date=panel.index.max(),
        missing_value_count=int(panel.isna().sum().sum()),
        columns=tuple(str(column) for column in panel.columns),
    )


def _unique_in_order(values: pd.Series) -> list[Any]:
    return list(dict.fromkeys(values.to_list()))


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates


__all__ = [
    "CSVValidationSummary",
    "ValidatedCSVPanel",
    "ValidatedCSVSeries",
    "load_benchmark_price_csv",
    "load_long_price_csv",
    "load_wide_price_csv",
]
