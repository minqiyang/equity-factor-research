"""Synthetic M4.7 snapshot harness for the a-2 suites.

A fake vendor serves components, symbol lists, the index calendar, and per-code
``eod``, ``splits``, and ``div`` responses; the merged a-1 retrieval module
(``data.eodhd_retrieval``) writes the Appendix A layout from them, so every
a-2 test reads a snapshot produced by the real retrieval path. No test opens a
network connection.
"""

from __future__ import annotations

import builtins
import io
import json
import pathlib
import urllib.error
import urllib.parse
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd
import pytest

from data import holdout_partition
from data.eodhd_retrieval import DATA_DIR_ENV, TOKEN_ENV, main as retrieval_main
from data.holdout_partition import (
    MEMBERSHIP_FILE,
    SEAL_FILE,
    build_prospective_seal,
    read_manifest,
    seal_bytes,
)


HOLIDAYS = ("2004-07-05", "2004-11-25", "2005-07-04", "2005-11-24", "2006-03-30", "2006-07-04")
CAL = pd.bdate_range("2003-06-02", "2006-12-29", name="date").difference(pd.DatetimeIndex(HOLIDAYS))
HOLDOUT_START = "1993-12-31"
HOLDOUT_END = "2003-12-31"
I_H = int(CAL.searchsorted(pd.Timestamp(HOLDOUT_END)))
RETRIEVED = datetime(2007, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
TOKEN = "fixture-token-not-a-secret"


def day(row: int) -> str:
    return CAL[row].date().isoformat()


def rows(start: int, stop: int) -> list[int]:
    return list(range(start, stop))


def bars(
    row_ids: Iterable[int],
    close: float | Callable[[int], float] = 100.0,
    adjusted: float | Callable[[int], float] | None = None,
    volume: float | Callable[[int], float] = 1000.0,
    dates: pd.DatetimeIndex = CAL,
) -> list[dict[str, Any]]:
    """Vendor ``eod`` rows on the given calendar rows; callables receive the row id."""

    def value(spec, row):
        return spec(row) if callable(spec) else spec

    out = []
    for row in row_ids:
        c = float(value(close, row))
        a = c if adjusted is None else float(value(adjusted, row))
        out.append({"date": dates[row].date().isoformat(), "open": c, "high": c, "low": c, "close": c,
                    "adjusted_close": a, "volume": float(value(volume, row))})
    return out


def entry(code: str | None, start: str | None, end: str | None = None, name: str | None = None,
          delisted: bool = False) -> dict[str, Any]:
    return {"Code": code, "Name": name if name is not None else f"{code} Inc", "StartDate": start,
            "EndDate": end, "IsActiveNow": 0 if delisted else 1, "IsDelisted": 1 if delisted else 0}


class Vendor:
    """Route table keyed by endpoint path; values are bodies, HTTP status ints, or lists of either."""

    def __init__(self, calendar: pd.DatetimeIndex = CAL) -> None:
        self.calendar = calendar
        self.entries: list[dict[str, Any]] = []
        self.listed: list[dict[str, Any]] = []
        self.delisted: list[dict[str, Any]] = []
        self.routes: dict[str, Any] = {}
        self.urls: list[str] = []

    def code(self, code: str, eod: Any, splits: Any = (), dividends: Any = ()) -> None:
        """Serve ``code`` (``XYZ.US``); list payloads become JSON bodies, ints become HTTP errors."""
        for table, payload in (("eod", eod), ("splits", splits), ("div", dividends)):
            self.routes[f"{table}/{code}"] = payload if isinstance(payload, (int, bytes)) else _body(list(payload))

    def __call__(self, url: str) -> bytes:
        self.urls.append(url)
        parts = urllib.parse.urlsplit(url)
        key = parts.path.removeprefix("/api/")
        query = urllib.parse.parse_qs(parts.query)
        if key == "fundamentals/GSPC.INDX":
            return _body({"HistoricalTickerComponents": {str(i): e for i, e in enumerate(self.entries)}})
        if key == "exchange-symbol-list/US":
            return _body(self.listed if query["delisted"][0] == "0" else self.delisted)
        if key == "eod/GSPC.INDX":
            return _body([{"date": d.date().isoformat(), "close": 1000.0 + i} for i, d in enumerate(self.calendar)])
        response = self.routes.get(key, 404)
        if isinstance(response, list):
            response = response.pop(0) if len(response) > 1 else response[0]
        if isinstance(response, int):
            raise urllib.error.HTTPError(url, response, "vendor error", {}, io.BytesIO(b'{"error":"vendor"}'))
        return response


def _body(payload: Any) -> bytes:
    return json.dumps(payload).encode("utf-8")


class Clock:
    def __init__(self) -> None:
        self.value = RETRIEVED

    def __call__(self) -> datetime:
        return self.value

    def advance(self, **delta: float) -> None:
        self.value += timedelta(**delta)


class Harness:
    """Drive the a-1 retrieval CLI against a ``Vendor`` into ``<tmp>/private/sp500_pit_<id>``."""

    def __init__(self, tmp_path: Path, monkeypatch, snapshot_id: str = "T", vendor: Vendor | None = None) -> None:
        monkeypatch.setenv(TOKEN_ENV, TOKEN)
        self.data_dir = tmp_path / "private"
        monkeypatch.setenv(DATA_DIR_ENV, str(self.data_dir))
        self.snapshot_id = snapshot_id
        self.snapshot_dir = self.data_dir / f"sp500_pit_{snapshot_id}"
        self.vendor = vendor or Vendor()
        self.clock = Clock()

    def run(self, command: str, *extra: str) -> int:
        self.clock.advance(seconds=1)
        return retrieval_main(
            [command, "--snapshot-id", self.snapshot_id, "--data-dir", str(self.data_dir),
             "--requests-per-minute", "60000000", "--retries", "1", *extra],
            transport=self.vendor, clock=self.clock, sleep=lambda seconds: None,
        )

    def seal(self, holdout_start: str = HOLDOUT_START, holdout_end: str = HOLDOUT_END) -> None:
        """Write a prospective seal with a chosen window and the snapshot's true inputs."""
        manifest = read_manifest(self.snapshot_dir)
        membership = manifest["files"]["membership"]
        record = build_prospective_seal(
            {"holdout_start": holdout_start, "holdout_end_exclusive": holdout_end,
             "coverage_start_strict": holdout_start, "entry_counts": {}},
            components_raw_sha256=membership["sha256"],
            components_retrieved_utc_date=date.fromisoformat(manifest["snapshot"]["components_retrieved_utc_date"]),
            sealed_at="2007-01-02T12:00:00Z", sealing_actor="test", authorization_reference="test",
        )
        (self.snapshot_dir / SEAL_FILE).write_bytes(seal_bytes(record))

    def retrieve(self, *, seal: bool = True, tables: tuple[str, ...] = ("splits", "eod", "dividends")) -> Path:
        assert self.run("components") == 0
        assert self.run("symbols") == 0
        if seal:
            self.seal()
        assert self.run("calendar") == 0
        for table in tables:
            assert self.run(table) == 0
        self.run("verify")
        return self.snapshot_dir

    def manifest(self) -> dict[str, Any]:
        return read_manifest(self.snapshot_dir)

    def edit_manifest(self, change: Callable[[dict[str, Any]], None]) -> None:
        manifest = self.manifest()
        change(manifest)
        (self.snapshot_dir / "manifest.json").write_bytes(json.dumps(manifest, sort_keys=True).encode("utf-8"))


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def interval_rows(snapshot_dir: Path) -> pd.DataFrame:
    return read_csv(snapshot_dir / "identity/interval_results.csv")


def master_rows(snapshot_dir: Path) -> pd.DataFrame:
    return read_csv(snapshot_dir / "identity/security_master.csv")


def build_manifest(snapshot_dir: Path) -> dict[str, Any]:
    return json.loads((snapshot_dir / "membership/membership_build_manifest.json").read_text())


def panel(snapshot_dir: Path, permanent_id: str) -> pd.DataFrame:
    return pd.read_parquet(snapshot_dir / "panel" / "discovery" / f"{permanent_id}.parquet")


def turnover(frame: pd.DataFrame) -> np.ndarray:
    """Dollar turnover as the research panels form it: ``close / split_factor * volume``."""
    return (frame["close"] / frame["split_factor"] * frame["volume"]).to_numpy()


# ---------------------------------------------------------------- read recorder (plan 5.4)


FORBIDDEN_PREFIXES = ("eod/holdout/", "splits/holdout/", "dividends/holdout/", "quarantine/", "raw/")


class ReadRecorder:
    """Record every file read under a snapshot through the patched readers of plan 5.4."""

    def __init__(self, snapshot_dir: Path) -> None:
        self.root = Path(snapshot_dir).resolve()
        self.reads: list[tuple[str, str, Any]] = []

    def _relative(self, source: Any) -> str | None:
        """Snapshot-relative path of a read source: a path, a path string, or a named byte buffer."""
        name = source if isinstance(source, (str, Path)) else getattr(source, "name", None)
        if not isinstance(name, (str, Path)):
            return None
        path = Path(name)
        if not path.is_absolute():
            return path.as_posix() if (self.root / path).exists() else None
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except (ValueError, OSError):
            return None

    def note(self, reader: str, source: Any, columns: Any = None) -> None:
        relative = self._relative(source)
        if relative is not None:
            self.reads.append((reader, relative, columns))

    def forbidden(self) -> list[str]:
        return [path for _, path, _ in self.reads if path.startswith(FORBIDDEN_PREFIXES)]

    def paths(self, reader: str | None = None) -> list[str]:
        return [path for name, path, _ in self.reads if reader is None or name == reader]


@contextmanager
def record_reads(snapshot_dir: Path):
    """Patch the plan 5.4 readers in a private patch context and record every snapshot read."""
    recorder = ReadRecorder(snapshot_dir)
    original_read_parquet = pd.read_parquet
    original_open = builtins.open
    original_read_bytes = pathlib.Path.read_bytes
    original_read_text = pathlib.Path.read_text
    original_json_load = json.load

    def read_parquet(path, *args, **kwargs):
        recorder.note("read_parquet", path, kwargs.get("columns"))
        return original_read_parquet(path, *args, **kwargs)

    def open_(file, *args, **kwargs):
        recorder.note("open", file)
        return original_open(file, *args, **kwargs)

    def read_bytes(self):
        recorder.note("read_bytes", self)
        return original_read_bytes(self)

    def read_text(self, *args, **kwargs):
        recorder.note("read_text", self)
        return original_read_text(self, *args, **kwargs)

    def json_load(handle, *args, **kwargs):
        recorder.note("json_load", handle)
        return original_json_load(handle, *args, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(pd, "read_parquet", read_parquet)
        patch.setattr(builtins, "open", open_)
        patch.setattr(pathlib.Path, "read_bytes", read_bytes)
        patch.setattr(pathlib.Path, "read_text", read_text)
        patch.setattr(json, "load", json_load)
        yield recorder


__all__ = [
    "CAL", "HOLDOUT_END", "HOLDOUT_START", "I_H", "MEMBERSHIP_FILE", "Harness", "Vendor", "bars", "day", "entry",
    "holdout_partition", "interval_rows", "master_rows", "panel", "record_reads", "rows", "turnover",
]
