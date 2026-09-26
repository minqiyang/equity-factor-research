"""EODHD retrieval for the M4.7 S&P 500 point-in-time snapshot (plan 1.3).

This is the single repository module that opens a network connection. It
uses the standard library ``urllib`` only. The vendor token comes from
``EFR_EODHD_API_TOKEN`` at run time, travels only as a function argument and in
the request query string, and never reaches a file, log record, exception
message, or traceback. Every retrieval artifact lives in a private snapshot
directory outside the repository; the manifest replace is the only commit
point, and downstream reads go through manifest roles with SHA-256
verification (``data.holdout_partition.read_authorized_bytes``).

Run as ``python -m data.eodhd_retrieval <command> --snapshot-id <ID>``.
Commands: plan, components, symbols, calendar, splits, eod, dividends, all,
verify. ``plan`` and ``verify`` open no network connection. The module places
no orders and connects to no broker (R12).
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import random
import re
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from data.holdout_partition import (
    MANIFEST_FILE,
    MEMBERSHIP_FILE,
    SEAL_FILE,
    SnapshotRefusal,
    authorized_records,
    parse_strict_date,
    partition_of,
    read_authorized_parquet,
    read_holdout_end,
    sha256_bytes,
)
from data.parquet_loader import _standardize_eod_frame


TOKEN_ENV = "EFR_EODHD_API_TOKEN"
DATA_DIR_ENV = "EFR_EODHD_DATA_DIR"
TOKEN_MISSING_MESSAGE = "EFR_EODHD_API_TOKEN is not set; the owner sets it at run time"
BASE_URL = "https://eodhd.com/api"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_SCHEMA_VERSION = "m4_7_retrieval_manifest_v1"
LOG_FILE = "retrieval_log.jsonl"
TABLES = ("splits", "eod", "dividends")
ENDPOINTS = {"eod": "eod", "splits": "splits", "dividends": "div"}
PARTITIONS = ("discovery", "holdout")
EOD_COLUMNS = ("date", "open", "high", "low", "close", "adjusted_close", "volume")
MEMBERSHIP_FIELDS = ("Code", "Name", "StartDate", "EndDate", "IsActiveNow", "IsDelisted")
SYMBOL_FIELDS = ("Code", "Name", "Exchange", "Type", "Isin")
RATE_LIMIT_BACKOFF_SECONDS = (2, 4, 8, 16, 32)
SCALE_STEP_THRESHOLD = 0.15
SCALE_CHECK_MAX_GAP_ROWS = 20
SPLIT_WINDOW_ROWS = 5
PERSISTENT_PROVIDER_ERROR_DATES = 3


class RetrievalTransportError(Exception):
    """A sanitized transport failure; no attribute or arg holds the token.

    The original ``urllib`` exception is dropped, never chained.
    """

    def __init__(
        self,
        status: int | None,
        typed_outcome: str,
        sanitized_message: str,
        body: bytes = b"",
    ) -> None:
        super().__init__(status, typed_outcome, sanitized_message)
        self.status = status
        self.typed_outcome = typed_outcome
        self.sanitized_message = sanitized_message
        self.body = body


def _redaction_forms(token: str | None) -> list[str]:
    if not token:
        return []
    forms = {
        token,
        urllib.parse.quote(token),
        urllib.parse.quote(token, safe=""),
        urllib.parse.quote_plus(token),
    }
    return sorted(forms, key=len, reverse=True)


def _sanitize(text: str, token: str | None) -> str:
    for form in _redaction_forms(token):
        text = text.replace(form, "<redacted>")
    return text


def _sanitize_bytes(payload: bytes, token: str | None) -> bytes:
    for form in _redaction_forms(token):
        payload = payload.replace(form.encode("utf-8"), b"<redacted>")
    return payload


def _outcome_for_status(status: int | None) -> str:
    if status in (401, 403):
        return "credential_refused"
    if status == 402:
        return "entitlement_refused"
    if status == 404:
        return "missing_symbol"
    if status == 429:
        return "rate_limited"
    return "provider_error"


def _request(
    url_without_token: str,
    token: str,
    *,
    timeout: float,
    transport: Callable[[str], bytes] | None = None,
) -> bytes:
    """Append the token, perform the call, and sanitize every transport failure.

    ``transport`` is the injected seam for offline tests; it receives the full
    URL and returns the body bytes or raises a ``urllib`` exception.
    """

    separator = "&" if "?" in url_without_token else "?"
    url = f"{url_without_token}{separator}api_token={urllib.parse.quote(token, safe='')}"
    status: int | None = None
    body = b""
    try:
        if transport is not None:
            return transport(url)
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        reason = f"HTTP {exc.code} {exc.reason}"
        try:
            body = exc.read() or b""
        except Exception:
            body = b""
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        reason = f"{type(exc).__name__} {exc}"
    # Raised outside the handlers so the original exception is never chained.
    outcome = _outcome_for_status(status)
    message = _sanitize(f"{outcome}: {reason} for {url}", token)
    raise RetrievalTransportError(status, outcome, message, _sanitize_bytes(body, token))


def _public_url(path: str, params: dict[str, str | None]) -> str:
    query = {key: value for key, value in params.items() if value is not None}
    query["fmt"] = "json"
    return f"{BASE_URL}/{path}?{urllib.parse.urlencode(query)}"


@dataclass
class Session:
    args: argparse.Namespace
    snapshot_dir: Path
    token: str | None
    transport: Callable[[str], bytes] | None
    clock: Callable[[], datetime]
    sleep: Callable[[float], None]
    manifest: dict[str, Any] = field(default_factory=dict)
    requests_made: int = 0
    last_request_at: float | None = None

    def now(self) -> datetime:
        return self.clock().astimezone(timezone.utc)

    def stamp(self) -> str:
        return self.now().strftime("%Y%m%dT%H%M%S%fZ")

    def today(self) -> str:
        return self.now().date().isoformat()


# ---------------------------------------------------------------- storage


def _write_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def _parquet_bytes(frame: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    frame.to_parquet(buffer, engine="pyarrow", index=False)
    return buffer.getvalue()


def _write_file(
    session: Session,
    relative: str,
    payload: bytes,
    rows: int | None,
) -> dict[str, Any]:
    if relative in authorized_records(session.manifest):
        raise RuntimeError(f"attempt file name collides with a committed file: {relative}")
    _write_atomic(session.snapshot_dir / relative, payload)
    return {"path": relative, "sha256": sha256_bytes(payload), "bytes": len(payload), "rows": rows}


def _new_manifest(session: Session) -> dict[str, Any]:
    now = session.now().isoformat()
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "snapshot": {
            "id": session.args.snapshot_id,
            "code_commit": _code_commit(),
            "started_utc": now,
            "updated_utc": now,
            "endpoints": {
                "base_url": BASE_URL,
                "components": f"fundamentals/{session.args.index}",
                "symbols": "exchange-symbol-list/US",
                "calendar": f"eod/{session.args.index}",
                **{table: f"{ENDPOINTS[table]}/<CODE>" for table in TABLES},
            },
            "components_retrieved_utc_date": None,
        },
        "files": {},
        "entries": {},
        "requested_codes": [],
        "counters": {},
        "verify": None,
    }


def _code_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() or None


def _commit(session: Session) -> None:
    manifest = session.manifest
    manifest["snapshot"]["updated_utc"] = session.now().isoformat()
    counters = manifest["counters"]
    entries = manifest["entries"]
    for table in TABLES:
        for partition in PARTITIONS:
            counters[f"{table}_{partition}_quarantined"] = sum(
                1
                for key, entry in entries.items()
                if key.startswith(f"{table}/")
                and entry.get("partition_statuses", {}).get(partition, "").startswith("quarantined:")
            )
        counters[f"{table}_date_structure_refusals"] = sum(
            1
            for key, entry in entries.items()
            if key.startswith(f"{table}/")
            and entry["status"].startswith("unavailable:date_structure:")
        )
    payload = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    _write_atomic(session.snapshot_dir / MANIFEST_FILE, payload)


def _log(session: Session, record: dict[str, Any]) -> None:
    path = session.snapshot_dir / LOG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"utc": session.now().isoformat(), "command": session.args.command, **record}, sort_keys=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _files_verify(session: Session, records: dict[str, dict[str, Any]]) -> bool:
    for record in records.values():
        path = session.snapshot_dir / record["path"]
        if not path.is_file() or sha256_bytes(path.read_bytes()) != record["sha256"]:
            return False
    return True


# ---------------------------------------------------------------- transport


def _fetch(
    session: Session,
    path: str,
    params: dict[str, str | None],
    *,
    table: str,
    code: str,
) -> tuple[str, bytes]:
    """Return ``(outcome, body)`` with outcome ``ok``, ``missing_symbol``, or ``provider_error``.

    Credential, entitlement, rate-limit exhaustion, and budget stop the
    invocation with a typed ``SnapshotRefusal``.
    """

    args = session.args
    url = _public_url(path, params)
    rate_limit_attempts = 0
    provider_retries = 0
    while True:
        if session.requests_made >= args.max_requests:
            raise SnapshotRefusal("budget_exhausted", f"{args.max_requests} requests reached")
        _throttle(session)
        session.requests_made += 1
        session.manifest["counters"]["requests_attempted"] = (
            session.manifest["counters"].get("requests_attempted", 0) + 1
        )
        attempt = {"table": table, "code": code, "request": url}
        try:
            body = _request(url, session.token, timeout=args.timeout_seconds, transport=session.transport)
        except RetrievalTransportError as exc:
            _log(session, {**attempt, "outcome": exc.typed_outcome, "http_status": exc.status})
            if exc.typed_outcome in ("credential_refused", "entitlement_refused"):
                raise SnapshotRefusal(exc.typed_outcome, exc.sanitized_message) from None
            if exc.typed_outcome == "missing_symbol":
                return "missing_symbol", exc.body
            if exc.typed_outcome == "rate_limited":
                if rate_limit_attempts == len(RATE_LIMIT_BACKOFF_SECONDS):
                    raise SnapshotRefusal("rate_limited_exhausted", exc.sanitized_message) from None
                session.sleep(RATE_LIMIT_BACKOFF_SECONDS[rate_limit_attempts] + random.uniform(0.0, 1.0))
                rate_limit_attempts += 1
                continue
            if provider_retries >= args.retries:
                return "provider_error", b""
            provider_retries += 1
            continue
        _log(session, {**attempt, "outcome": "ok", "http_status": 200})
        return "ok", body


def _throttle(session: Session) -> None:
    interval = 60.0 / session.args.requests_per_minute
    now = time.monotonic()
    if session.last_request_at is not None and now - session.last_request_at < interval:
        session.sleep(interval - (now - session.last_request_at))
    session.last_request_at = time.monotonic()


# ---------------------------------------------------------------- parsing


def _parse_dated_rows(body: bytes) -> tuple[list[dict[str, Any]], list[date]] | str:
    """Return rows and dates, or the typed failure (plan 1.3 steps 2 and 3)."""

    try:
        payload = json.loads(body)
    except ValueError:
        return "malformed_response"
    if not isinstance(payload, list) or any(
        not isinstance(row, dict) or "date" not in row for row in payload
    ):
        return "malformed_response"
    dates = [parse_strict_date(row["date"]) for row in payload]
    if any(day is None for day in dates):
        return "date_structure:unparseable"
    if len(set(dates)) != len(dates):
        return "date_structure:duplicate"
    if any(later <= earlier for earlier, later in zip(dates, dates[1:])):
        return "date_structure:unsorted"
    return payload, dates  # type: ignore[return-value]


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def split_ratio(value: Any) -> float | None:
    """Parse a vendor ``"N/M"`` split string into ``N / M``; ``None`` when invalid."""

    if not isinstance(value, str) or value.count("/") != 1:
        return None
    numerator, denominator = (_finite_number(part) for part in value.split("/"))
    if numerator is None or denominator is None or numerator <= 0 or denominator <= 0:
        return None
    ratio = numerator / denominator
    return ratio if math.isfinite(ratio) and ratio > 0 else None


def _text(value: Any) -> str | None:
    return None if value is None else str(value)


def _date_column(dates: list[date]) -> pd.Series:
    return pd.Series(pd.to_datetime([day.isoformat() for day in dates]), dtype="datetime64[ns]")


def _quarantine_frame(rows: list[dict[str, Any]], dates: list[date]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": _date_column(dates),
            "row_json": [json.dumps(row, sort_keys=True) for row in rows],
        }
    )


def _validate_split_partition(rows: list[dict[str, Any]], dates: list[date]) -> pd.DataFrame | str:
    ratios = [split_ratio(row.get("split")) for row in rows]
    if any(ratio is None for ratio in ratios):
        return "invalid_split_ratio"
    return pd.DataFrame(
        {
            "date": _date_column(dates),
            "split": pd.Series([str(row["split"]) for row in rows], dtype=object),
            "ratio": pd.Series(ratios, dtype=float),
        }
    )


def _validate_dividend_partition(rows: list[dict[str, Any]], dates: list[date]) -> pd.DataFrame | str:
    values = [_finite_number(row.get("value")) for row in rows]
    if any(value is None or value < 0 for value in values):
        return "invalid_dividend_value"
    return pd.DataFrame(
        {
            "date": _date_column(dates),
            "value": pd.Series(values, dtype=float),
            "row_json": pd.Series([json.dumps(row, sort_keys=True) for row in rows], dtype=object),
        }
    )


def _validate_eod_partition(rows: list[dict[str, Any]], dates: list[date]) -> pd.DataFrame | str:
    if not rows:
        empty = {column: pd.Series(dtype=float) for column in EOD_COLUMNS}
        empty["date"] = _date_column([])
        return pd.DataFrame(empty)
    raw = pd.DataFrame(rows).reindex(columns=list(EOD_COLUMNS))
    try:
        panel = _standardize_eod_frame(raw)
    except (TypeError, ValueError):
        return "bar_values"
    return panel.reset_index()[list(EOD_COLUMNS)]


def _unverified_split(
    panel: pd.DataFrame,
    calendar_rows: dict[pd.Timestamp, int],
    split_rows: list[int],
) -> bool:
    """Run-local scale check over consecutive on-calendar bars (plan 1.3 step 5)."""

    scale = (panel["close"] / panel["adjusted_close"]).to_numpy()
    on_calendar = [
        (calendar_rows[day], scale[index])
        for index, day in enumerate(pd.DatetimeIndex(panel["date"]))
        if day in calendar_rows
    ]
    for (row_a, scale_a), (row_b, scale_b) in zip(on_calendar, on_calendar[1:]):
        if row_b - row_a - 1 > SCALE_CHECK_MAX_GAP_ROWS:
            continue
        if abs(scale_b / scale_a - 1.0) > SCALE_STEP_THRESHOLD and not any(
            abs(split_row - row_b) <= SPLIT_WINDOW_ROWS for split_row in split_rows
        ):
            return True
    return False


# ---------------------------------------------------------------- statuses


def _is_terminal(status: str | None) -> bool:
    return status is not None and (status == "retrieved" or status.startswith("unavailable:"))


def _split_evidence(session: Session, code: str) -> tuple[str, str | None]:
    """``(split_evidence_basis, split_table_sha256_at_eod_validation)`` from the current splits entry."""

    entry = session.manifest["entries"][f"splits/{code}"]
    if entry["status"] != "retrieved":
        return "none_discontinuity_fallback", None
    if entry["partition_statuses"]["discovery"] != "valid":
        return "split_evidence_quarantined", None
    return "discovery_split_table", entry["authorized_files"]["discovery"]["sha256"]


def _eod_stale(session: Session, code: str) -> bool:
    entry = session.manifest["entries"].get(f"eod/{code}")
    if entry is None or entry["status"] != "retrieved":
        return False
    recorded = (entry["split_evidence_basis"], entry["split_table_sha256_at_eod_validation"])
    return _split_evidence(session, code) != recorded


def _is_open(session: Session, table: str, code: str) -> bool:
    entry = session.manifest["entries"].get(f"{table}/{code}")
    if entry is None or not _is_terminal(entry["status"]):
        return True
    if not _files_verify(session, entry["authorized_files"]):
        return True
    return table == "eod" and _eod_stale(session, code)


def _set_entry(session: Session, table: str, code: str, entry: dict[str, Any]) -> None:
    key = f"{table}/{code}"
    previous = session.manifest["entries"].get(key)
    previous_status = None if previous is None else previous["status"]
    session.manifest["entries"][key] = entry
    if previous_status != entry["status"]:
        _log(session, {"table": table, "code": code, "status_change": {"from": previous_status, "to": entry["status"]}})
    _commit(session)


# ---------------------------------------------------------------- tables


def _retrieve_table(
    session: Session,
    table: str,
    code: str,
    holdout_end: date,
    calendar_rows: dict[pd.Timestamp, int] | None = None,
) -> None:
    args = session.args
    key = f"{table}/{code}"
    previous = session.manifest["entries"].get(key)
    history = [] if previous is None else list(previous.get("provider_error_history", []))
    base: dict[str, Any] = {
        "provider_error_history": history,
        "request_window": {"from": args.date_from, "to": args.date_to},
    }
    if table == "eod":
        split_status = session.manifest["entries"][f"splits/{code}"]["status"]
        if split_status == "provider_error":
            _log(session, {"table": table, "code": code, "outcome": "split_table_provider_error"})
            if previous is None or not _is_terminal(previous["status"]):
                _set_entry(session, table, code, {**base, "status": "skipped:split_table_provider_error", "partition_statuses": {}, "authorized_files": {}})
            return
        if split_status.startswith("unavailable:"):
            _log(session, {"table": table, "code": code, "outcome": f"split_table_unavailable:{split_status.split(':', 1)[1]}"})

    outcome, body = _fetch(
        session,
        f"{ENDPOINTS[table]}/{code}",
        {"from": args.date_from, "to": args.date_to},
        table=table,
        code=code,
    )
    if outcome == "provider_error":
        history.append(session.today())
        if previous is not None and _is_terminal(previous["status"]):
            _set_entry(session, table, code, {**previous, "provider_error_history": history})
            return
        status = "provider_error"
        if len(set(history)) >= PERSISTENT_PROVIDER_ERROR_DATES:
            status = "unavailable:persistent_provider_error"
        _set_entry(session, table, code, {**base, "status": status, "partition_statuses": {}, "authorized_files": {}})
        return

    stamp = session.stamp()
    files = {"raw": _write_file(session, f"raw/{table}/{code}.{stamp}.json", body, None)}
    entry: dict[str, Any] = {**base, "retrieved_utc": stamp, "partition_statuses": {}, "authorized_files": files}
    if table == "eod":
        entry["split_evidence_basis"] = None
        entry["split_table_sha256_at_eod_validation"] = None
    if outcome == "missing_symbol":
        _set_entry(session, table, code, {**entry, "status": "unavailable:missing_symbol"})
        return
    parsed = _parse_dated_rows(body)
    if isinstance(parsed, str):
        if parsed.startswith("date_structure:"):
            _log(session, {"table": table, "code": code, "outcome": f"validation_failed:{parsed}"})
        _set_entry(session, table, code, {**entry, "status": f"unavailable:{parsed}"})
        return
    rows, dates = parsed
    if table == "eod" and not rows:
        _set_entry(session, table, code, {**entry, "status": "unavailable:empty_payload"})
        return
    basis, split_rows = "", []
    if table == "eod":
        files["dates"] = _write_file(session, f"dates/{code}.{stamp}.parquet", _parquet_bytes(pd.DataFrame({"date": _date_column(dates)})), len(dates))
        basis, split_sha = _split_evidence(session, code)
        entry["split_evidence_basis"] = basis
        entry["split_table_sha256_at_eod_validation"] = split_sha
        split_rows = _discovery_split_rows(session, code, basis, calendar_rows or {})

    for partition in PARTITIONS:
        selected = [index for index, day in enumerate(dates) if partition_of(day, holdout_end) == partition]
        part_rows = [rows[index] for index in selected]
        part_dates = [dates[index] for index in selected]
        if table == "splits":
            result = _validate_split_partition(part_rows, part_dates)
        elif table == "dividends":
            result = _validate_dividend_partition(part_rows, part_dates)
        else:
            result = _validate_eod_partition(part_rows, part_dates)
            if partition == "discovery" and not isinstance(result, str):
                if basis == "split_evidence_quarantined":
                    result = "split_evidence_quarantined"
                elif _unverified_split(result, calendar_rows or {}, split_rows):
                    result = "unverified_split"
        if isinstance(result, str):
            _log(session, {"table": table, "code": code, "partition": partition, "outcome": f"validation_failed:{result}"})
            entry["partition_statuses"][partition] = f"quarantined:{result}"
            files[f"quarantine_{partition}"] = _write_file(
                session,
                f"quarantine/{table}_{partition}/{code}.{stamp}.parquet",
                _parquet_bytes(_quarantine_frame(part_rows, part_dates)),
                len(part_rows),
            )
        else:
            entry["partition_statuses"][partition] = "valid"
            files[partition] = _write_file(
                session,
                f"{table}/{partition}/{code}.{stamp}.parquet",
                _parquet_bytes(result),
                len(result),
            )
    _set_entry(session, table, code, {**entry, "status": "retrieved"})


def _discovery_split_rows(
    session: Session,
    code: str,
    basis: str,
    calendar_rows: dict[pd.Timestamp, int],
) -> list[int]:
    if basis != "discovery_split_table":
        return []
    record = session.manifest["entries"][f"splits/{code}"]["authorized_files"]["discovery"]
    splits = read_authorized_parquet(session.snapshot_dir, record["path"], session.manifest)
    calendar_dates = pd.DatetimeIndex(sorted(calendar_rows))
    return [int(calendar_dates.searchsorted(day)) for day in pd.DatetimeIndex(splits["date"])]


def _membership_codes(session: Session) -> list[str]:
    if MEMBERSHIP_FILE not in authorized_records(session.manifest):
        return []
    frame = read_authorized_parquet(session.snapshot_dir, MEMBERSHIP_FILE, session.manifest)
    codes: list[str] = []
    for code in frame["Code"]:
        if isinstance(code, str) and code and f"{code}.US" not in codes:
            codes.append(f"{code}.US")
    return codes


def _request_list(session: Session) -> list[str]:
    """Every ever-member code, the benchmark, and every recorded curated code."""

    codes = _membership_codes(session)
    for code in [session.args.benchmark, *session.manifest["requested_codes"]]:
        if code not in codes:
            codes.append(code)
    return codes


def _read_code_file(path: str) -> list[str]:
    codes: list[str] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        code = line.strip()
        if code and not code.startswith("#") and code not in codes:
            codes.append(code)
    return codes


def _record_requested(session: Session, codes: list[str]) -> None:
    for code in codes:
        if code not in session.manifest["requested_codes"]:
            session.manifest["requested_codes"].append(code)


def _run_table(session: Session, table: str, codes_file: str | None, refresh: bool) -> None:
    holdout_end = read_holdout_end(session.snapshot_dir)
    if codes_file is not None:
        codes = _read_code_file(codes_file)
        _record_requested(session, codes)
        session.manifest["counters"]["codes_requested"] = len(_request_list(session))
    else:
        codes = _request_list(session)
        session.manifest["counters"]["codes_requested"] = len(codes)
    calendar_rows = None
    if table == "eod":
        if "calendar" not in session.manifest["files"]:
            raise SnapshotRefusal("calendar_required_before_eod")
        missing = [code for code in codes if f"splits/{code}" not in session.manifest["entries"]]
        if missing:
            raise SnapshotRefusal("splits_required_before_eod", f"{len(missing)} codes have no split status")
        calendar = read_authorized_parquet(
            session.snapshot_dir, session.manifest["files"]["calendar"]["path"], session.manifest
        )
        calendar_rows = {day: row for row, day in enumerate(pd.DatetimeIndex(calendar["date"]))}
    for code in codes:
        if refresh or _is_open(session, table, code):
            _retrieve_table(session, table, code, holdout_end, calendar_rows)
    _commit(session)


# ---------------------------------------------------------------- commands


def _refuse_existing(session: Session, *keys: str) -> None:
    for key in keys:
        if key in session.manifest["files"]:
            raise SnapshotRefusal("snapshot_file_exists", session.manifest["files"][key]["path"])


def _fetch_once(session: Session, path: str, params: dict[str, str | None], table: str) -> bytes:
    outcome, body = _fetch(session, path, params, table=table, code=session.args.index)
    if outcome != "ok":
        raise SnapshotRefusal(outcome, path)
    return body


def cmd_components(session: Session) -> int:
    _refuse_existing(session, "components_raw")
    index = session.args.index
    body = _fetch_once(session, f"fundamentals/{index}", {}, "components")
    files = session.manifest["files"]
    files["components_raw"] = _write_file(session, f"raw/index/{index}.fundamentals.json", body, None)
    session.manifest["snapshot"]["components_retrieved_utc_date"] = session.today()
    try:
        payload = json.loads(body)
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        session.manifest["snapshot"]["components_response_keys"] = sorted(payload)
    history = payload.get("HistoricalTickerComponents") if isinstance(payload, dict) else None
    entries = list(history.values()) if isinstance(history, dict) else history
    if not isinstance(entries, list) or any(not isinstance(item, dict) for item in entries):
        _commit(session)
        raise SnapshotRefusal("components_malformed", "HistoricalTickerComponents is not a list or object of entries")
    if not entries:
        _commit(session)
        raise SnapshotRefusal("components_empty", "HistoricalTickerComponents holds no entry")
    frame = pd.DataFrame(
        {
            "raw_row": pd.Series(range(len(entries)), dtype="int64"),
            **{name: pd.Series([_text(item.get(name)) for item in entries], dtype=object) for name in MEMBERSHIP_FIELDS},
        }
    )
    files["membership"] = _write_file(session, MEMBERSHIP_FILE, _parquet_bytes(frame), len(frame))
    _commit(session)
    print(json.dumps({"components_entries": len(frame), "components_retrieved_utc_date": session.today()}))
    return 0


def cmd_symbols(session: Session) -> int:
    _refuse_existing(session, "symbols_listed", "symbols_delisted")
    files = session.manifest["files"]
    counts = {}
    for name, flag in (("listed", "0"), ("delisted", "1")):
        body = _fetch_once(session, "exchange-symbol-list/US", {"delisted": flag}, "symbols")
        files[f"symbols_{name}_raw"] = _write_file(session, f"raw/symbols/US_{name}.json", body, None)
        try:
            payload = json.loads(body)
        except ValueError:
            payload = None
        if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
            _commit(session)
            raise SnapshotRefusal("malformed_response", f"symbol list {name}")
        frame = pd.DataFrame(
            {field_name: pd.Series([_text(item.get(field_name)) for item in payload], dtype=object) for field_name in SYMBOL_FIELDS}
        )
        files[f"symbols_{name}"] = _write_file(session, f"symbols/{name}.parquet", _parquet_bytes(frame), len(frame))
        counts[name] = len(frame)
    _commit(session)
    print(json.dumps({"symbols": counts}))
    return 0


def cmd_calendar(session: Session) -> int:
    read_holdout_end(session.snapshot_dir)
    _refuse_existing(session, "calendar")
    index = session.args.index
    body = _fetch_once(session, f"eod/{index}", {"from": session.args.date_from, "to": session.args.date_to}, "calendar")
    files = session.manifest["files"]
    files["calendar_raw"] = _write_file(session, f"raw/index/{index}.eod.json", body, None)
    parsed = _parse_dated_rows(body)
    if isinstance(parsed, str) or not parsed[1]:
        _commit(session)
        if not isinstance(parsed, str):
            raise SnapshotRefusal("empty_payload", f"eod/{index}")
        prefix = "validation_failed:" if parsed.startswith("date_structure:") else ""
        raise SnapshotRefusal(f"{prefix}{parsed}", f"eod/{index}")
    frame = pd.DataFrame({"date": _date_column(parsed[1])})
    files["calendar"] = _write_file(session, f"calendar/{index}.dates.parquet", _parquet_bytes(frame), len(frame))
    _commit(session)
    print(json.dumps({"calendar_rows": len(frame)}))
    return 0


def _table_command(table: str) -> Callable[[Session], int]:
    def command(session: Session) -> int:
        _run_table(session, table, session.args.codes, session.args.refresh)
        statuses: dict[str, int] = {}
        for key, entry in session.manifest["entries"].items():
            if key.startswith(f"{table}/"):
                statuses[entry["status"]] = statuses.get(entry["status"], 0) + 1
        print(json.dumps({table: dict(sorted(statuses.items()))}))
        return 0

    return command


def cmd_all(session: Session) -> int:
    files = session.manifest["files"]
    if "components_raw" not in files:
        cmd_components(session)
    if "symbols_listed" not in files:
        cmd_symbols(session)
    if not (session.snapshot_dir / SEAL_FILE).is_file():
        raise SnapshotRefusal("holdout_seal_required", "derive holdout_seal_v1.json, then rerun all")
    if session.args.consideration_securities is not None:
        _record_requested(session, _read_code_file(session.args.consideration_securities))
    if "calendar" not in files:
        cmd_calendar(session)
    for table in TABLES:
        _run_table(session, table, None, False)
    return cmd_verify(session)


def cmd_verify(session: Session) -> int:
    manifest = session.manifest
    records = authorized_records(manifest)
    mismatched = sorted(path for path, record in records.items() if not _files_verify(session, {path: record}))
    codes = _request_list(session)
    manifest["counters"]["codes_requested"] = len(codes)
    incomplete: dict[str, dict[str, str]] = {}
    for table in TABLES:
        for code in codes:
            entry = manifest["entries"].get(f"{table}/{code}")
            if entry is None:
                incomplete.setdefault(table, {})[code] = "absent"
            elif not _is_terminal(entry["status"]):
                incomplete.setdefault(table, {})[code] = entry["status"]
            elif not _files_verify(session, entry["authorized_files"]):
                incomplete.setdefault(table, {})[code] = f"{entry['status']}:artifact_hash_mismatch"
    stale = sorted(code for code in codes if f"splits/{code}" in manifest["entries"] and _eod_stale(session, code))
    leaks = _token_leaks(session)
    manifest["verify"] = {
        "retrieval_complete": not incomplete,
        "incomplete_codes_by_table_and_status": incomplete,
        "split_evidence_stale": stale,
        "artifact_hash_mismatch": mismatched,
        "persistent_provider_error_by_table": {
            table: sum(
                1
                for key, entry in manifest["entries"].items()
                if key.startswith(f"{table}/") and entry["status"] == "unavailable:persistent_provider_error"
            )
            for table in TABLES
        },
        "token_leak_detected": leaks,
    }
    _commit(session)
    print(json.dumps(manifest["verify"], sort_keys=True))
    if leaks:
        raise SnapshotRefusal("token_leak_detected", ", ".join(leaks))
    return 1 if mismatched else 0


def _token_leaks(session: Session) -> list[str]:
    needles = [form.encode("utf-8") for form in _redaction_forms(session.token)]
    leaks = []
    for path in sorted(session.snapshot_dir.rglob("*")):
        if path.is_file() and any(needle in path.read_bytes() for needle in needles):
            leaks.append(path.relative_to(session.snapshot_dir).as_posix())
    return leaks


def cmd_plan(session: Session) -> int:
    args = session.args
    window = {"from": args.date_from, "to": args.date_to}
    requests = [
        _public_url(f"fundamentals/{args.index}", {}),
        _public_url("exchange-symbol-list/US", {"delisted": "0"}),
        _public_url("exchange-symbol-list/US", {"delisted": "1"}),
        _public_url(f"eod/{args.index}", window),
    ]
    codes = _request_list(session) if session.manifest else [args.benchmark]
    for table in TABLES:
        requests.extend(_public_url(f"{ENDPOINTS[table]}/{code}", window) for code in codes)
    for request in requests:
        print(request)
    print(
        json.dumps(
            {
                "projected_requests": len(requests),
                "projected_duration_minutes": round(len(requests) / args.requests_per_minute, 2),
                "codes": len(codes),
                "membership_known": MEMBERSHIP_FILE in authorized_records(session.manifest) if session.manifest else False,
            },
            sort_keys=True,
        )
    )
    return 0


COMMANDS: dict[str, Callable[[Session], int]] = {
    "plan": cmd_plan,
    "components": cmd_components,
    "symbols": cmd_symbols,
    "calendar": cmd_calendar,
    "splits": _table_command("splits"),
    "eod": _table_command("eod"),
    "dividends": _table_command("dividends"),
    "all": cmd_all,
    "verify": cmd_verify,
}


def _strict_date_arg(value: str) -> str:
    if parse_strict_date(value) is None:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD, got {value!r}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m data.eodhd_retrieval", description="EODHD retrieval for the M4.7 snapshot")
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--snapshot-id", required=True)
    shared.add_argument("--data-dir", default=None)
    shared.add_argument("--index", default="GSPC.INDX")
    shared.add_argument("--benchmark", default="SPY.US")
    shared.add_argument("--from", dest="date_from", type=_strict_date_arg, default="1980-01-01")
    shared.add_argument("--to", dest="date_to", type=_strict_date_arg, default=None)
    shared.add_argument("--requests-per-minute", type=int, default=300)
    shared.add_argument("--max-requests", type=int, default=20000)
    shared.add_argument("--timeout-seconds", type=float, default=60.0)
    shared.add_argument("--retries", type=int, default=5)
    shared.add_argument("--refresh", action="store_true")
    shared.add_argument("--debug", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        sub = subparsers.add_parser(name, parents=[shared])
        if name in TABLES:
            sub.add_argument("--codes", default=None)
        if name == "all":
            sub.add_argument("--consideration-securities", default=None)
    return parser


def _snapshot_dir(args: argparse.Namespace) -> Path:
    raw = args.data_dir or os.environ.get(DATA_DIR_ENV, "")
    if not raw.strip():
        raise SnapshotRefusal("data_dir_missing", f"{DATA_DIR_ENV} or --data-dir is required")
    data_dir = Path(raw).expanduser().resolve()
    if data_dir.is_relative_to(REPOSITORY_ROOT):
        raise SnapshotRefusal("data_dir_inside_repository", "the snapshot must live outside the repository")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.snapshot_id):
        raise SnapshotRefusal("snapshot_id_invalid", "use letters, digits, '_' or '-'")
    return data_dir / f"sp500_pit_{args.snapshot_id}"


def main(
    argv: list[str] | None = None,
    *,
    transport: Callable[[str], bytes] | None = None,
    clock: Callable[[], datetime] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    token: str | None = None
    if args.command != "plan":
        token = os.environ.get(TOKEN_ENV)
        if token is None or not token.strip():
            print(TOKEN_MISSING_MESSAGE, file=sys.stderr)
            return 2
    try:
        snapshot_dir = _snapshot_dir(args)
        session = Session(
            args=args,
            snapshot_dir=snapshot_dir,
            token=token,
            transport=transport,
            clock=clock or (lambda: datetime.now(timezone.utc)),
            sleep=sleep or time.sleep,
        )
        manifest_path = snapshot_dir / MANIFEST_FILE
        if manifest_path.is_file():
            session.manifest = json.loads(manifest_path.read_bytes())
        elif args.command not in ("plan", "verify"):
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            session.manifest = _new_manifest(session)
        elif args.command == "verify":
            raise SnapshotRefusal("manifest_missing", MANIFEST_FILE)
        return COMMANDS[args.command](session)
    except SnapshotRefusal as exc:
        print(_sanitize(str(exc), token), file=sys.stderr)
        if args.debug:
            print(_sanitize(traceback.format_exc(), token), file=sys.stderr)
        return 3 if exc.code == "holdout_seal_required" else 1
    except Exception as exc:
        print(_sanitize(f"{type(exc).__name__}: {exc}", token), file=sys.stderr)
        if args.debug:
            print(_sanitize(traceback.format_exc(), token), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
