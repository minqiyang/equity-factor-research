"""Strict local Parquet loaders for EODHD daily market-data panels.

This module reads user-provided local Parquet files only. It does not download
data, call vendor APIs, store credentials, connect to brokers, place orders, or
make profitability claims.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype


REMOTE_PATH_PREFIXES = (
    "http://",
    "https://",
    "ftp://",
    "s3://",
    "gs://",
)

_REQUIRED_COLUMNS = (
    "date",
    "open",
    "high",
    "low",
    "close",
    "adjusted_close",
    "volume",
)
_PRICE_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
    "adjusted_close",
)
_PANEL_FIELDS = (
    "open",
    "high",
    "low",
    "close",
    "adjusted_close",
    "volume",
)
_INVENTORY_RECORD_KEYS = ("stocks", "coverage", "symbols", "files", "inventory", "items")


class DataIntegrityError(ValueError):
    """Raised when a local Parquet market-data file fails integrity checks."""


def load_eod_parquet(file_path: Path | str) -> pd.DataFrame:
    """Load one local EODHD daily Parquet file into a date-indexed frame.

    The file must contain ``date``, ``open``, ``high``, ``low``, ``close``,
    ``adjusted_close``, and ``volume``. Dates must be unique, increasing, and
    timezone-naive. Price columns must be strictly positive finite numbers.
    Volume must be a non-negative finite number.
    """

    path = _validate_local_parquet_path(file_path)
    raw = pd.read_parquet(path, engine="pyarrow")
    if not isinstance(raw, pd.DataFrame):
        raise TypeError("Parquet file must contain a table")
    return _standardize_eod_frame(raw)


def load_eod_cohort_panels(
    data_dir: Path | str,
    symbols: list[str],
    inventory_path: Path | str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, pd.DataFrame]:
    """Load per-symbol EOD Parquet files into aligned wide field panels.

    When ``inventory_path`` is provided, each symbol maps to a relative file
    under ``data_dir`` through ``symbol`` / ``file`` records. Otherwise the
    loader looks for ``{symbol}.parquet`` and then ``{symbol.lower()}.parquet``
    directly under ``data_dir``.

    Each file is validated in full before an optional inclusive date slice.
    Panels share the union of remaining dates; missing symbol-date cells stay
    as ``NaN``.
    """

    directory = _validate_local_directory(data_dir)
    requested = _validate_symbols(symbols)
    inventory_map = (
        _load_inventory_symbol_map(inventory_path) if inventory_path is not None else None
    )
    start = _optional_timestamp(start_date, field_name="start_date")
    end = _optional_timestamp(end_date, field_name="end_date")
    if start is not None and end is not None and start > end:
        raise ValueError("start_date must be on or before end_date")

    per_symbol: dict[str, pd.DataFrame] = {}
    for symbol in requested:
        path = _resolve_symbol_parquet_path(
            directory,
            symbol,
            inventory_map=inventory_map,
        )
        frame = load_eod_parquet(path)
        per_symbol[symbol] = _slice_date_index(frame, start=start, end=end)

    return _align_symbol_panels(per_symbol, symbols=requested)


def _standardize_eod_frame(raw: pd.DataFrame) -> pd.DataFrame:
    frame = raw.rename(columns=lambda column: str(column))
    if "date" not in frame.columns and isinstance(frame.index, pd.DatetimeIndex):
        frame = frame.rename_axis("date").reset_index()

    duplicated_columns = _duplicates([str(column) for column in frame.columns])
    if duplicated_columns:
        raise ValueError(f"Parquet file contains duplicate columns: {duplicated_columns}")

    missing = [column for column in _REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Parquet file is missing required columns: {missing}")
    if frame.empty:
        raise DataIntegrityError("Parquet file must contain at least one row")

    dates = _parse_dates(frame["date"])
    _validate_unique_sorted_dates(dates)

    values: dict[str, np.ndarray] = {}
    for column in _PANEL_FIELDS:
        numeric = _as_numeric_series(frame[column], field_name=column)
        if column in _PRICE_COLUMNS:
            _validate_positive_values(numeric, field_name=column)
        else:
            _validate_non_negative_values(numeric, field_name=column)
        values[column] = numeric.to_numpy(dtype=float)

    panel = pd.DataFrame(values, index=dates)
    panel.index.name = "date"
    return panel.loc[:, list(_PANEL_FIELDS)]


def _validate_local_parquet_path(file_path: Path | str) -> Path:
    _reject_remote_path(file_path, field_name="file_path")
    path = Path(file_path)
    if path.suffix.lower() != ".parquet":
        raise ValueError("file_path must point to a .parquet file")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _validate_local_directory(data_dir: Path | str) -> Path:
    _reject_remote_path(data_dir, field_name="data_dir")
    path = Path(data_dir)
    if not path.is_dir():
        raise FileNotFoundError(path)
    return path


def _reject_remote_path(raw_path: Path | str, *, field_name: str) -> None:
    text = str(raw_path).strip()
    if text.lower().startswith(REMOTE_PATH_PREFIXES):
        raise ValueError(
            f"{field_name} must be a local filesystem path; remote data access is not supported"
        )


def _validate_symbols(symbols: list[str]) -> list[str]:
    if not isinstance(symbols, list) or not symbols:
        raise ValueError("symbols must be a nonempty list")
    cleaned: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbols must contain nonempty strings")
        name = symbol.strip()
        if Path(name).name != name:
            raise ValueError(f"symbol must be a bare identifier: {symbol}")
        if name in seen:
            raise ValueError(f"symbols must be unique: {name}")
        seen.add(name)
        cleaned.append(name)
    return cleaned


def _load_inventory_symbol_map(inventory_path: Path | str) -> dict[str, str]:
    _reject_remote_path(inventory_path, field_name="inventory_path")
    path = Path(inventory_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("inventory_path must contain valid JSON") from exc

    mapping: dict[str, str] = {}
    for record in _inventory_records(payload):
        if not isinstance(record, dict):
            raise ValueError("inventory records must be objects")
        symbol = record.get("symbol")
        relative_file = record.get("file")
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("inventory records require a nonempty symbol")
        if not isinstance(relative_file, str) or not relative_file.strip():
            raise ValueError("inventory records require a nonempty file path")
        name = symbol.strip()
        if name in mapping:
            raise DataIntegrityError(f"inventory contains duplicate symbol: {name}")
        mapping[name] = relative_file.strip()

    if not mapping:
        raise ValueError("inventory must map at least one symbol to a file")
    return mapping


def _inventory_records(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise ValueError("inventory must be a JSON object or array")

    for key in _INVENTORY_RECORD_KEYS:
        value = payload.get(key)
        if isinstance(value, list):
            return value

    if payload and all(isinstance(value, str) for value in payload.values()):
        return [{"symbol": str(symbol), "file": str(file_name)} for symbol, file_name in payload.items()]

    raise ValueError("inventory must contain symbol/file records")


def _resolve_symbol_parquet_path(
    data_dir: Path,
    symbol: str,
    *,
    inventory_map: dict[str, str] | None,
) -> Path:
    if inventory_map is not None:
        relative = inventory_map.get(symbol)
        if relative is None:
            raise FileNotFoundError(f"inventory has no file mapping for symbol: {symbol}")
        path = _resolve_under_data_dir(data_dir, relative)
        if path.suffix.lower() != ".parquet":
            raise ValueError(f"inventory file for {symbol} must be a .parquet path")
        if not path.is_file():
            raise FileNotFoundError(path)
        return path

    candidates = [data_dir / f"{symbol}.parquet", data_dir / f"{symbol.lower()}.parquet"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(data_dir / f"{symbol}.parquet")


def _resolve_under_data_dir(data_dir: Path, relative: str) -> Path:
    relative_path = Path(relative)
    if relative_path.is_absolute():
        raise ValueError("inventory file path must be relative to data_dir")
    candidate = (data_dir / relative_path).resolve()
    root = data_dir.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("inventory file path must stay under data_dir")
    return candidate


def _parse_dates(values: pd.Series) -> pd.DatetimeIndex:
    try:
        parsed = pd.to_datetime(values, errors="raise")
    except (TypeError, ValueError) as exc:
        raise ValueError("date must contain parseable dates") from exc

    if parsed.isna().any():
        raise DataIntegrityError("date must not contain missing dates")

    index = pd.DatetimeIndex(parsed)
    if index.tz is not None:
        index = pd.DatetimeIndex([timestamp.tz_localize(None) for timestamp in index])
    return pd.DatetimeIndex(index, name="date")


def _validate_unique_sorted_dates(dates: pd.DatetimeIndex) -> None:
    if dates.has_duplicates:
        raise DataIntegrityError("date must not contain duplicate dates")
    if not bool(dates.is_monotonic_increasing):
        raise DataIntegrityError("date must be sorted in increasing date order")


def _as_numeric_series(values: pd.Series, *, field_name: str) -> pd.Series:
    _reject_boolean_series(values, field_name=field_name)
    try:
        numeric = pd.to_numeric(values, errors="raise")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must contain numeric values") from exc

    numeric = numeric.astype(float)
    if not np.isfinite(numeric.to_numpy()).all():
        raise DataIntegrityError(f"{field_name} must contain finite numeric values")
    return numeric


def _reject_boolean_series(values: pd.Series, *, field_name: str) -> None:
    if is_bool_dtype(values.dtype):
        raise DataIntegrityError(
            f"{field_name} must be numeric; boolean columns are rejected"
        )
    if values.dtype == object:
        boolean_mask = values.map(lambda value: isinstance(value, (bool, np.bool_)))
        if bool(boolean_mask.any()):
            raise DataIntegrityError(
                f"{field_name} must be numeric; boolean columns are rejected"
            )


def _validate_positive_values(values: pd.Series, *, field_name: str) -> None:
    if bool((values <= 0.0).any()):
        raise DataIntegrityError(f"{field_name} must contain only strictly positive values")


def _validate_non_negative_values(values: pd.Series, *, field_name: str) -> None:
    if bool((values < 0.0).any()):
        raise DataIntegrityError(f"{field_name} must contain only non-negative values")


def _optional_timestamp(value: str | None, *, field_name: str) -> pd.Timestamp | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a nonempty date string")
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must contain a parseable date") from exc
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp


def _slice_date_index(
    frame: pd.DataFrame,
    *,
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
) -> pd.DataFrame:
    if start is None and end is None:
        return frame
    return frame.loc[start:end]


def _align_symbol_panels(
    per_symbol: dict[str, pd.DataFrame],
    *,
    symbols: list[str],
) -> dict[str, pd.DataFrame]:
    panels: dict[str, pd.DataFrame] = {}
    for field in _PANEL_FIELDS:
        pieces = [per_symbol[symbol][field].rename(symbol) for symbol in symbols]
        panel = pd.concat(pieces, axis=1) if pieces else pd.DataFrame()
        panel = panel.reindex(columns=symbols)
        panel.index = pd.DatetimeIndex(pd.to_datetime(panel.index), name="date", freq=None)
        panels[field] = panel
    return panels


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates


__all__ = [
    "DataIntegrityError",
    "load_eod_cohort_panels",
    "load_eod_parquet",
]
