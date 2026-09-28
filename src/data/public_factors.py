"""Public academic factor files: cached download, parsers, and a manifest.

Sources are the Jensen, Kelly, and Pedersen (JKP) factor files, the Kenneth R.
French Data Library, and FRED. Raw files stay in ``data/public_cache/``, which
is gitignored (R11); the repository commits only the manifest (URL, retrieval
date UTC, SHA-256, row count, date range) and aggregate results.

Every parser keeps missing values typed (R6): a NaN value always carries a
reason code in the parallel ``missing`` frame, and nothing is filled, clipped,
dropped, or repaired. Malformed input refuses the load with
``PublicDataRefusal``; refusal messages name rows and months but never print a
provider value.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import re
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


USER_AGENT = "equity-factor-research/0.1 (noncommercial academic research)"

PRESENT = ""
MISSING_ABSENT = "absent"
MISSING_BLANK = "blank_field"
MISSING_CODE = "provider_missing_code"

FRENCH_MISSING_CODES = (-99.99, -999.0)
JKP_FIXED_VALUES = {"location": "usa", "freq": "monthly", "weighting": "vw_cap"}
JKP_BLANK_TOKENS = frozenset({"", "NA", "NaN", "nan"})
FRED_BLANK_TOKENS = frozenset({"", "."})


class PublicDataRefusal(ValueError):
    """A public file or an input derived from it fails a declared check."""


@dataclass(frozen=True)
class CachedFile:
    path: Path
    url: str
    retrieved_utc: str
    sha256: str
    n_bytes: int


@dataclass(frozen=True)
class MonthlyPanel:
    """Monthly values on a complete calendar-month index with typed missingness.

    ``values`` holds floats with NaN where a value is missing; ``missing``
    holds the reason code for each NaN cell and ``PRESENT`` elsewhere.
    ``n_rows`` counts the data rows parsed from the file.
    """

    values: pd.DataFrame
    missing: pd.DataFrame
    n_rows: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sidecar(path: Path) -> Path:
    return path.with_name(path.name + ".retrieval.json")


def fetch(url: str, path: Path) -> CachedFile:
    """Return the cached copy of ``url`` at ``path``, downloading it once.

    A sidecar JSON next to the file records the URL, the retrieval time (UTC),
    and the SHA-256. A cached file whose bytes or URL disagree with its
    sidecar refuses instead of being silently replaced.
    """

    sidecar = _sidecar(path)
    if path.exists() and sidecar.exists():
        record = json.loads(sidecar.read_text(encoding="utf-8"))
        digest = sha256_file(path)
        if record.get("url") != url:
            raise PublicDataRefusal(f"cached file {path.name} was retrieved from another URL")
        if record.get("sha256") != digest:
            raise PublicDataRefusal(f"cached file {path.name} does not match its recorded SHA-256")
        return CachedFile(path, url, record["retrieved_utc"], digest, path.stat().st_size)
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
    retrieved = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    partial = path.with_name(path.name + ".partial")
    partial.write_bytes(payload)
    partial.replace(path)
    digest = hashlib.sha256(payload).hexdigest()
    sidecar.write_text(
        json.dumps({"url": url, "retrieved_utc": retrieved, "sha256": digest}, indent=2) + "\n",
        encoding="utf-8",
    )
    return CachedFile(path, url, retrieved, digest, len(payload))


def _zip_member_text(path: Path, member: str) -> str:
    with zipfile.ZipFile(path) as archive:
        if member not in archive.namelist():
            raise PublicDataRefusal(f"{path.name} has no member {member!r}")
        return archive.read(member).decode("latin-1")


def _panel(values: dict[str, dict[pd.Period, float]],
           reasons: dict[str, dict[pd.Period, str]], columns: list[str], n_rows: int) -> MonthlyPanel:
    months = [month for column in columns for source in (values, reasons) for month in source[column]]
    if not months:
        raise PublicDataRefusal("file holds no monthly data rows")
    index = pd.period_range(min(months), max(months), freq="M")
    frame = pd.DataFrame(
        {column: pd.Series(values[column], dtype=float) for column in columns}, index=index,
    )
    missing = pd.DataFrame(MISSING_ABSENT, index=index, columns=columns, dtype=object)
    for column in columns:
        present = frame[column].notna()
        missing.loc[present, column] = PRESENT
        for month, reason in reasons[column].items():
            missing.loc[month, column] = reason
    return MonthlyPanel(frame, missing, n_rows)


def read_jkp_zip(path: Path, member: str, *, columns: list[str],
                 expected_names: set[str]) -> MonthlyPanel:
    """Parse a JKP long-format monthly file into a factor-by-month panel.

    Fail-closed checks: the header equals ``columns``; location, freq, and
    weighting each hold their single declared value; the set of names equals
    ``expected_names``; no (name, calendar month) pair repeats; every return
    field is a finite decimal or a blank token (typed ``blank_field``). A
    factor-month without a row is typed ``absent``. Returns are used as
    published: JKP signs each long-minus-short return by its direction column.
    """

    frame = pd.read_csv(io.StringIO(_zip_member_text(path, member)), dtype=str,
                        keep_default_na=False)
    if list(frame.columns) != list(columns):
        raise PublicDataRefusal(f"{member}: header {list(frame.columns)} differs from {list(columns)}")
    for column, expected in JKP_FIXED_VALUES.items():
        found = sorted(set(frame[column]))
        if found != [expected]:
            raise PublicDataRefusal(f"{member}: column {column} holds {found}, expected [{expected!r}]")
    names = set(frame["name"])
    if names != expected_names:
        raise PublicDataRefusal(
            f"{member}: name set differs from the declared members "
            f"(missing {sorted(expected_names - names)}, extra {sorted(names - expected_names)})"
        )
    dates = pd.to_datetime(frame["date"], format="%Y-%m-%d", errors="coerce")
    if dates.isna().any():
        bad = int(dates.isna().sum())
        raise PublicDataRefusal(f"{member}: {bad} rows have a date outside YYYY-MM-DD")
    months = dates.dt.to_period("M")
    duplicated = pd.DataFrame({"name": frame["name"], "month": months}).duplicated()
    if duplicated.any():
        first = int(duplicated.to_numpy().argmax())
        raise PublicDataRefusal(
            f"{member}: {int(duplicated.sum())} duplicate (name, month) pairs, first "
            f"{frame['name'].iloc[first]} {months.iloc[first]}"
        )
    values: dict[str, dict[pd.Period, float]] = {name: {} for name in sorted(names)}
    reasons: dict[str, dict[pd.Period, str]] = {name: {} for name in sorted(names)}
    for name, month, token in zip(frame["name"], months, frame["ret"]):
        token = token.strip()
        if token in JKP_BLANK_TOKENS:
            reasons[name][month] = MISSING_BLANK
            continue
        try:
            value = float(token)
        except ValueError:
            raise PublicDataRefusal(f"{member}: non-numeric return for {name} {month}") from None
        if not math.isfinite(value):
            raise PublicDataRefusal(f"{member}: non-finite return for {name} {month}")
        values[name][month] = value
    return _panel(values, reasons, sorted(names), len(frame))


def _fields(line: str) -> list[str]:
    return [field.strip() for field in line.split(",")]


def read_french_monthly_zip(path: Path, member: str, *, columns: list[str]) -> MonthlyPanel:
    """Parse the monthly block of a Ken French CSV inside a zip file.

    Only rows whose first field is a six-digit YYYYMM before the first line
    containing ``Annual Factors`` are read; the annual block is never read.
    Values are percent per month and become decimals. The codes -99.99 and
    -999 become typed ``provider_missing_code`` values; a calendar month with
    no row is typed ``absent``.
    """

    lines = _zip_member_text(path, member).splitlines()
    stop = next((i for i, line in enumerate(lines) if "Annual Factors" in line), len(lines))
    rows = [i for i in range(stop) if re.fullmatch(r"\d{6}", _fields(lines[i])[0])]
    if not rows:
        raise PublicDataRefusal(f"{member}: no six-digit YYYYMM rows before the annual block")
    header_rows = [i for i in range(rows[0]) if _fields(lines[i])[0] == "" and len(_fields(lines[i])) > 1]
    if not header_rows:
        raise PublicDataRefusal(f"{member}: no header line before the first monthly row")
    header = _fields(lines[header_rows[-1]])[1:]
    absent = [column for column in columns if column not in header]
    if absent:
        raise PublicDataRefusal(f"{member}: header {header} lacks {absent}")
    positions = {column: header.index(column) + 1 for column in columns}
    values: dict[str, dict[pd.Period, float]] = {column: {} for column in columns}
    reasons: dict[str, dict[pd.Period, str]] = {column: {} for column in columns}
    seen: set[pd.Period] = set()
    for i in rows:
        fields = _fields(lines[i])
        if len(fields) != len(header) + 1:
            raise PublicDataRefusal(f"{member}: line {i + 1} has {len(fields)} fields, expected {len(header) + 1}")
        stamp = fields[0]
        if not 1 <= int(stamp[4:]) <= 12:
            raise PublicDataRefusal(f"{member}: line {i + 1} month {stamp} is not a calendar month")
        month = pd.Period(f"{stamp[:4]}-{stamp[4:]}", freq="M")
        if month in seen:
            raise PublicDataRefusal(f"{member}: month {month} repeats")
        seen.add(month)
        for column, position in positions.items():
            try:
                raw = float(fields[position])
            except ValueError:
                raise PublicDataRefusal(f"{member}: non-numeric {column} on line {i + 1}") from None
            if raw in FRENCH_MISSING_CODES:
                reasons[column][month] = MISSING_CODE
            elif not math.isfinite(raw):
                raise PublicDataRefusal(f"{member}: non-finite {column} on line {i + 1}")
            else:
                values[column][month] = raw / 100.0
    return _panel(values, reasons, list(columns), len(rows))


def read_fred_csv(path: Path, *, series: list[str]) -> MonthlyPanel:
    """Parse a FRED ``fredgraph.csv`` download of monthly series.

    The header must be ``observation_date`` followed by ``series``; each
    observation date is the first day of the month it describes. Values stay
    in the series' own units (percent per year for Moody's yields). A blank or
    ``.`` field is typed ``blank_field``.
    """

    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    if list(frame.columns) != ["observation_date", *series]:
        raise PublicDataRefusal(f"{path.name}: header {list(frame.columns)} differs")
    dates = pd.to_datetime(frame["observation_date"], format="%Y-%m-%d", errors="coerce")
    if dates.isna().any() or (dates.dt.day != 1).any():
        raise PublicDataRefusal(f"{path.name}: observation_date must be the first day of a month")
    months = dates.dt.to_period("M")
    if months.duplicated().any():
        raise PublicDataRefusal(f"{path.name}: a month repeats")
    values: dict[str, dict[pd.Period, float]] = {name: {} for name in series}
    reasons: dict[str, dict[pd.Period, str]] = {name: {} for name in series}
    for name in series:
        for month, token in zip(months, frame[name]):
            token = token.strip()
            if token in FRED_BLANK_TOKENS:
                reasons[name][month] = MISSING_BLANK
                continue
            try:
                value = float(token)
            except ValueError:
                raise PublicDataRefusal(f"{path.name}: non-numeric {name} for {month}") from None
            if not math.isfinite(value):
                raise PublicDataRefusal(f"{path.name}: non-finite {name} for {month}")
            values[name][month] = value
    return _panel(values, reasons, list(series), len(frame))


def read_cluster_labels(path: Path) -> dict[str, str]:
    """Map each JKP characteristic to its cluster from ``cluster_labels.csv``."""

    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    if list(frame.columns) != ["characteristic", "cluster"]:
        raise PublicDataRefusal(f"{path.name}: header {list(frame.columns)} differs")
    if frame["characteristic"].duplicated().any() or (frame == "").any().any():
        raise PublicDataRefusal(f"{path.name}: blank or repeated characteristic")
    return dict(zip(frame["characteristic"], frame["cluster"]))


_XLSX_NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def _column_number(reference: str) -> int:
    number = 0
    for letter in re.match(r"[A-Z]+", reference).group(0):
        number = number * 26 + ord(letter) - 64
    return number - 1


def read_xlsx_sheet(path: Path, sheet: str) -> list[list[str | None]]:
    """Read one worksheet of an .xlsx file as rows of cell text (stdlib only)."""

    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", _XLSX_NS):
                shared.append("".join(node.text or "" for node in item.iter(f"{{{_XLSX_NS['m']}}}t")))
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {rel.get("Id"): rel.get("Target") for rel in relations.findall("rel:Relationship", _XLSX_NS)}
        rel_id = next((node.get(f"{{{_XLSX_NS['r']}}}id")
                       for node in workbook.find("m:sheets", _XLSX_NS) if node.get("name") == sheet), None)
        if rel_id is None:
            raise PublicDataRefusal(f"{path.name} has no sheet {sheet!r}")
        target = targets[rel_id].lstrip("/")
        target = target if target.startswith("xl/") else f"xl/{target}"
        rows: list[list[str | None]] = []
        for row in ET.fromstring(archive.read(target)).iter(f"{{{_XLSX_NS['m']}}}row"):
            cells: dict[int, str | None] = {}
            for cell in row.findall("m:c", _XLSX_NS):
                kind = cell.get("t")
                value = cell.find("m:v", _XLSX_NS)
                if kind == "inlineStr":
                    text = "".join(node.text or "" for node in cell.iter(f"{{{_XLSX_NS['m']}}}t"))
                elif value is None:
                    text = None
                elif kind == "s":
                    text = shared[int(value.text)]
                else:
                    text = value.text
                cells[_column_number(cell.get("r"))] = text
            rows.append([cells.get(k) for k in range(max(cells) + 1)] if cells else [])
    return rows


def publication_year(cite: str | None) -> int | None:
    """Four-digit year inside the first pair of parentheses of a citation."""

    match = re.search(r"\(([^)]*)\)", cite or "")
    year = re.fullmatch(r"\s*(\d{4})\s*", match.group(1)) if match else None
    return int(year.group(1)) if year else None


def read_publication_years(path: Path, *, sheet: str = "details") -> dict[str, int | None]:
    """Map JKP ``abr_jkp`` to the publication year parsed from ``cite``."""

    rows = read_xlsx_sheet(path, sheet)
    header = rows[0]
    if "abr_jkp" not in header or "cite" not in header:
        raise PublicDataRefusal(f"{path.name}: sheet {sheet} lacks abr_jkp or cite")
    name_at, cite_at = header.index("abr_jkp"), header.index("cite")
    years: dict[str, int | None] = {}
    for row in rows[1:]:
        name = row[name_at] if len(row) > name_at else None
        if not name:
            continue
        if name in years:
            raise PublicDataRefusal(f"{path.name}: abr_jkp {name} repeats")
        years[name] = publication_year(row[cite_at] if len(row) > cite_at else None)
    return years


def manifest_entry(source_id: str, cached: CachedFile, *, rows: int,
                   first: str | None, last: str | None) -> dict[str, Any]:
    return {
        "id": source_id, "url": cached.url, "retrieved_utc": cached.retrieved_utc,
        "sha256": cached.sha256, "bytes": cached.n_bytes, "rows": rows,
        "first_date": first, "last_date": last,
    }


def write_manifest(path: Path, entries: list[dict[str, Any]], *, notes: dict[str, Any]) -> None:
    """Write the public-data manifest: provenance and hashes, never data rows."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": "m5_public_data_manifest_v1", **notes, "sources": entries}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
