"""Synthetic rule v2 snapshot harness for the M4.8 Stage A suites.

The M4.7 fake vendor (``tests/m4_7_snapshot_support.py``) serves a 2018-2021
business-day calendar, so the carried seal v1 window ``[2019-07-31,
2020-07-31)`` applies unchanged. The harness writes the carry record from the
committed seal v1 documents, runs the real retrieval path, and builds curated
membership files on request. No test opens a network connection.
"""

from __future__ import annotations

import csv
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from data.holdout_partition import SEAL_V1_CONFIRMATION_V2_PATH, SEAL_V1_DOCS_PATH, write_seal_carry
from research import m4_8_membership
from m4_7_snapshot_support import Harness, Vendor, bars, entry  # noqa: F401  (re-exported helpers)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CAL2 = pd.bdate_range("2018-01-02", "2021-12-31", name="date")
HOLDOUT_START = date(2019, 7, 31)
HOLDOUT_END = date(2020, 7, 31)
HS_ROW = int(CAL2.searchsorted(pd.Timestamp(HOLDOUT_START)))
HE_ROW = int(CAL2.searchsorted(pd.Timestamp(HOLDOUT_END)))
N_ROWS = len(CAL2)
D0_PRE = date(2018, 6, 29)
PRE_ROWS = range(0, HS_ROW)
POST_ROWS = range(HE_ROW, N_ROWS)
ALL_ROWS = range(0, N_ROWS)
RETRIEVED_V2 = datetime(2022, 1, 3, 12, 0, 0, tzinfo=timezone.utc)


def row_of(day: str | date) -> int:
    return int(CAL2.searchsorted(pd.Timestamp(day)))


def day2(row: int) -> str:
    return CAL2[row].date().isoformat()


def bars2(row_ids: Iterable[int], close: Any = 100.0, adjusted: Any = None, volume: Any = 1000.0) -> list[dict[str, Any]]:
    return bars(row_ids, close=close, adjusted=adjusted, volume=volume, dates=CAL2)


def split_row(row: int, ratio: str) -> dict[str, Any]:
    return {"date": day2(row), "split": ratio}


def dividend_row(row: int, value: float, unadjusted: float | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"date": day2(row), "value": value}
    if unadjusted is not None:
        payload["unadjustedValue"] = unadjusted
    return payload


class HarnessV2(Harness):
    """Drive the retrieval CLI into a rule v2 snapshot with the carried seal."""

    def __init__(self, tmp_path: Path, monkeypatch, snapshot_id: str = "V2", vendor: Vendor | None = None) -> None:
        super().__init__(tmp_path, monkeypatch, snapshot_id, vendor or Vendor(CAL2))
        self.clock.value = RETRIEVED_V2

    def carry(self) -> None:
        write_seal_carry(self.snapshot_dir, seal_v1_path=REPOSITORY_ROOT / SEAL_V1_DOCS_PATH,
                         confirmation_v2_path=REPOSITORY_ROOT / SEAL_V1_CONFIRMATION_V2_PATH,
                         written_at="2026-09-27T00:00:00Z", writing_actor="test", authorization_reference="test")

    def retrieve(self, *, seal: bool = True, tables: tuple[str, ...] = ("splits", "eod", "dividends")) -> Path:
        assert self.run("components") == 0
        assert self.run("symbols") == 0
        if seal:
            self.carry()
        assert self.run("calendar") == 0
        for table in tables:
            assert self.run(table) == 0
        self.run("verify")
        return self.snapshot_dir


def write_curated(directory: Path, *, supplement: Iterable[dict[str, str]] = (),
                  changes: Iterable[dict[str, str]] = (), anchors: Iterable[dict[str, str]] = ()) -> None:
    """Write the three curation files with the plan 2.3 columns; missing cells are blank."""
    directory.mkdir(parents=True, exist_ok=True)
    for name, columns, rows in ((m4_8_membership.SUPPLEMENT_FILE, m4_8_membership.SUPPLEMENT_COLUMNS, supplement),
                                (m4_8_membership.CHANGES_FILE, m4_8_membership.CHANGE_COLUMNS, changes),
                                (m4_8_membership.ANCHORS_FILE, m4_8_membership.ANCHOR_COLUMNS, anchors)):
        with (directory / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row.get(column, "") for column in columns})


def supplement_row(supplement_id: str, action: str, code: str, start: str, end: str = "", *, raw_row: str = "",
                   source_kind: str = "sp_dji_announcement", corroboration: str = "") -> dict[str, str]:
    return {"supplement_id": supplement_id, "action": action, "vendor_raw_row": raw_row, "code": code,
            "start_date": start, "end_date": end, "source_kind": source_kind, "source_locator": "locator",
            "corroboration_locator": corroboration, "retrieved_utc_date": "2026-09-27", "curator": "test"}


def change_row(change_id: str, effective: str, action: str, code: str, *, match: str = "", match_ref: str = "",
               notes: str = "", source_kind: str = "sp_dji_announcement", corroboration: str = "") -> dict[str, str]:
    return {"change_id": change_id, "effective_date": effective, "action": action, "code": code,
            "source_kind": source_kind, "source_locator": "locator", "corroboration_locator": corroboration,
            "match": match, "match_ref": match_ref, "retrieved_utc_date": "2026-09-27", "curator": "test",
            "notes": notes}


def snapshot_v2(tmp_path: Path, monkeypatch, name: str, entries: list[dict[str, Any]], codes: dict[str, Any], *,
                listed: Iterable[dict[str, Any]] = (), delisted: Iterable[dict[str, Any]] = (), build: bool = True,
                curated: dict[str, Any] | None = None, d0_pre: date = D0_PRE, spy: list[dict[str, Any]] | None = None,
                requested: Iterable[str] = ()) -> HarnessV2:
    """Retrieve a rule v2 snapshot with ``SPY.US`` on every row, write curated files, and run the universe build."""
    from research.m4_7_universe_build import build_universe

    harness = HarnessV2(tmp_path, monkeypatch, snapshot_id=name)
    vendor = harness.vendor
    vendor.entries, vendor.listed, vendor.delisted = list(entries), list(listed), list(delisted)
    vendor.code("SPY.US", spy if spy is not None else bars2(ALL_ROWS))
    for code, spec in codes.items():
        vendor.code(code, *spec) if isinstance(spec, tuple) else vendor.code(code, spec)
    if requested:
        codes_file = tmp_path / f"{name}_requested.txt"
        codes_file.write_text("\n".join(requested) + "\n", encoding="utf-8")
        assert harness.run("components") == 0
        assert harness.run("symbols") == 0
        harness.carry()
        assert harness.run("calendar") == 0
        for table in ("splits", "eod", "dividends"):
            assert harness.run(table, "--codes", str(codes_file)) == 0
            assert harness.run(table) == 0
        harness.run("verify")
    else:
        harness.retrieve()
    write_curated(harness.snapshot_dir / "membership", **(curated or {}))
    if build:
        build_universe(harness.snapshot_dir, d0_pre)
    return harness


def side_file(snapshot_dir: Path, table: str, code: str, partition: str) -> pd.DataFrame | None:
    """A partition file of the snapshot by manifest role, or ``None`` when the role holds no file."""
    import json

    entry_record = json.loads((snapshot_dir / "manifest.json").read_bytes())["entries"][f"{table}/{code}"]
    record = entry_record["authorized_files"].get(partition)
    return None if record is None else pd.read_parquet(snapshot_dir / record["path"])


def manifest_entry(snapshot_dir: Path, table: str, code: str) -> dict[str, Any]:
    import json

    return json.loads((snapshot_dir / "manifest.json").read_bytes())["entries"][f"{table}/{code}"]
