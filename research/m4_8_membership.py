"""Curated point-in-time membership for M4.8 (plan sections 2.3 and 2.4).

Reads the three private curation files of a membership directory, applies
rules M-1..M-9, and evaluates ``curated_coverage_start_v2``. Everything here
reads membership metadata and the curated files only; no price value is opened
(R2, R11). Invalid rows stay typed and counted; nothing is filled or repaired
(R6). The files never leave ``<private_data_root>``; callers publish counts.

Supplement rows use ``effective_date_as_known_at_v1`` (M-6): a fill, an absent
member, or a corrected date enters the eligibility mask through
``build_pit_membership_mask`` with the registered signal lag, exactly as a
vendor date does.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from data import holdout_partition
from data.holdout_partition import SnapshotRefusal, parse_strict_date, sha256_bytes


SUPPLEMENT_FILE = "curated_membership_supplement.csv"
CHANGES_FILE = "reconstructed_changes.csv"
ANCHORS_FILE = "published_counts.csv"
DISCREPANCIES_FILE = "membership_discrepancies.csv"
SUPPLEMENT_COLUMNS = ("supplement_id", "action", "vendor_raw_row", "code", "start_date", "end_date", "source_kind",
                      "source_locator", "corroboration_locator", "retrieved_utc_date", "curator", "notes")
CHANGE_COLUMNS = ("change_id", "effective_date", "action", "code", "source_kind", "source_locator",
                  "corroboration_locator", "match", "match_ref", "retrieved_utc_date", "curator", "notes")
ANCHOR_COLUMNS = ("month_end", "n_published", "source_locator", "retrieved_utc_date", "curator")
DISCREPANCY_COLUMNS = ("supplement_id", "vendor_raw_row", "code", "field", "vendor_date", "source_date",
                       "source_kind", "source_locator", "adjudication")
ACTIONS = ("start_date_fill", "absent_member_add", "date_correction")
SOURCE_KINDS = ("sp_dji_announcement", "sec_filing", "public_changes_list")
MATCH_TOLERANCE_ROWS = 5
ENDPOINT_CLASSES = ("change_matched", "discrepancy", "vendor_only")
COVERAGE_RULE = "curated_coverage_start_v2"
COVERAGE_FLOOR = date(2011, 8, 31)
MAX_UNRESOLVED_CHANGE_FRACTION = 0.02
ANCHOR_TOLERANCE = 5
FLOOR_ANCHOR_COUNT = 500
FLOOR_ANCHOR_MIN = 495
_CLASS_SUFFIX = re.compile(r"\b(class|cl|series)\s+[a-z]\b")


@dataclass(frozen=True)
class Curated:
    """The three curation files as string frames, with their SHA-256 (``None`` when a file is absent)."""

    supplement: pd.DataFrame
    changes: pd.DataFrame
    anchors: pd.DataFrame
    sha256: dict[str, str | None]


def _read(directory: Path, name: str, columns: tuple[str, ...]) -> tuple[pd.DataFrame, str | None]:
    path = directory / name
    if not path.is_file():
        return pd.DataFrame({column: pd.Series(dtype=object) for column in columns}), None
    payload = path.read_bytes()
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise SnapshotRefusal("curated_file_malformed", f"{name} lacks {missing}")
    return frame, sha256_bytes(payload)


def read_curated(directory: Path | str) -> Curated:
    """Read the supplement, change log, and count anchors of one membership directory."""
    directory = Path(directory)
    supplement, s_sha = _read(directory, SUPPLEMENT_FILE, SUPPLEMENT_COLUMNS)
    changes, c_sha = _read(directory, CHANGES_FILE, CHANGE_COLUMNS)
    anchors, a_sha = _read(directory, ANCHORS_FILE, ANCHOR_COLUMNS)
    return Curated(supplement, changes, anchors, {SUPPLEMENT_FILE: s_sha, CHANGES_FILE: c_sha, ANCHORS_FILE: a_sha})


def trading_row(calendar: pd.DatetimeIndex, day: date) -> int:
    """Position of ``day`` on the calendar: its row, or the first row after it."""
    return int(calendar.searchsorted(pd.Timestamp(day)))


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, float) and value != value) or str(value).strip() == ""


def _source_reason(row: dict[str, Any]) -> str | None:
    if row["source_kind"] not in SOURCE_KINDS or _blank(row["source_locator"]):
        return "source_missing"
    if row["source_kind"] == "public_changes_list" and _blank(row["corroboration_locator"]):
        return "corroboration_missing"
    return None


def _vendor_dates(vendor_row: dict[str, Any]) -> tuple[date | None, date | None, bool]:
    """``(start, end, end_parseable)`` of a vendor row; a blank end is open."""
    start = parse_strict_date(vendor_row.get("StartDate"))
    end_raw = vendor_row.get("EndDate")
    end = None if _blank(end_raw) else parse_strict_date(end_raw)
    return start, end, _blank(end_raw) or end is not None


def validate_supplement(
    supplement: pd.DataFrame,
    vendor: pd.DataFrame,
    calendar: pd.DatetimeIndex,
) -> list[dict[str, Any]]:
    """M-1..M-4: one typed record per supplement row, in file order.

    ``status`` is ``valid`` or ``supplement_invalid:<reason>``. Valid fills and
    corrections carry the governing ``start`` and ``end``; valid absent
    members carry both dates. M-5 collisions are typed later by
    ``apply_supplement``, which sees the corrected vendor intervals.
    """
    vendor_rows: dict[str, list[dict[str, Any]]] = {}
    for row in vendor.to_dict(orient="records"):
        vendor_rows.setdefault(str(row.get("raw_row")), []).append(row)
    targets = supplement.loc[supplement["action"].isin(("start_date_fill", "date_correction")), "vendor_raw_row"]
    shared_targets = set(targets[targets.duplicated(keep=False)])
    ids = supplement["supplement_id"]
    duplicate_ids = set(ids[ids.duplicated(keep=False)])
    records = []
    for row in supplement.to_dict(orient="records"):
        record: dict[str, Any] = {"supplement_id": row["supplement_id"], "action": row["action"],
                                  "vendor_raw_row": row["vendor_raw_row"], "code": row["code"],
                                  "start": None, "end": None, "discrepancies": []}
        records.append(record)
        record["status"] = _supplement_status(row, record, vendor_rows, shared_targets, duplicate_ids, calendar)
    return records


def _supplement_status(
    row: dict[str, Any], record: dict[str, Any], vendor_rows: dict[str, list[dict[str, Any]]],
    shared_targets: set[str], duplicate_ids: set[str], calendar: pd.DatetimeIndex,
) -> str:
    action = row["action"]
    if action not in ACTIONS:
        return "supplement_invalid:action_unknown"
    if row["supplement_id"] in duplicate_ids:
        return "supplement_invalid:duplicate_id"
    start = parse_strict_date(row["start_date"])
    end = None if _blank(row["end_date"]) else parse_strict_date(row["end_date"])
    if start is None or (not _blank(row["end_date"]) and end is None) or _blank(row["code"]):
        return "supplement_invalid:date_unparseable"
    reason = _source_reason(row)
    if reason is not None:
        return f"supplement_invalid:{reason}"
    if action == "absent_member_add":
        record.update(start=start, end=end)
        return "supplement_invalid:degenerate_interval" if end is not None and end <= start else "valid"
    matches = vendor_rows.get(str(row["vendor_raw_row"]), [])
    if len(matches) != 1 or row["vendor_raw_row"] in shared_targets:
        return "supplement_invalid:target_ambiguous"
    vendor_start, vendor_end, end_parseable = _vendor_dates(matches[0])
    if action == "start_date_fill":
        if not _blank(matches[0].get("StartDate")):
            return "supplement_invalid:target_not_undated"
        if not end_parseable:
            return "supplement_invalid:date_unparseable"
        record.update(start=start, end=vendor_end)
        return "supplement_invalid:degenerate_interval" if vendor_end is not None and vendor_end <= start else "valid"
    if vendor_start is None or not end_parseable:
        return "supplement_invalid:target_not_dated"
    changed = [(field, vendor_value, source_value) for field, vendor_value, source_value
               in (("start_date", vendor_start, start), ("end_date", vendor_end, end)) if vendor_value != source_value]
    record["discrepancies"] = [
        {"supplement_id": row["supplement_id"], "vendor_raw_row": row["vendor_raw_row"], "code": row["code"],
         "field": field, "vendor_date": "" if vendor_value is None else vendor_value.isoformat(),
         "source_date": "" if source_value is None else source_value.isoformat(), "source_kind": row["source_kind"],
         "source_locator": row["source_locator"], "adjudication": "unadjudicated"}
        for field, vendor_value, source_value in changed]
    if row["source_kind"] != "sp_dji_announcement":
        return "supplement_invalid:correction_not_primary"
    within = not changed or any(
        vendor_value is not None and source_value is not None
        and abs(trading_row(calendar, vendor_value) - trading_row(calendar, source_value)) <= MATCH_TOLERANCE_ROWS
        for _, vendor_value, source_value in changed)
    if within:
        return "supplement_invalid:correction_within_tolerance"
    for discrepancy in record["discrepancies"]:
        discrepancy["adjudication"] = "membership_date_corrected_primary_v1"
    record.update(start=start, end=end)
    return "supplement_invalid:degenerate_interval" if end is not None and end <= start else "valid"


def apply_supplement(
    vendor: pd.DataFrame,
    records: list[dict[str, Any]],
    components_retrieved_utc_date: date,
) -> pd.DataFrame:
    """The vendor table with valid fills and corrections applied and valid absent members appended.

    M-5: an absent member whose code meets a retained vendor interval of the
    same ``<Code>.US`` over overlapping dates becomes ``identity_refused`` and
    stays out. Appended rows carry the ``supplement_id`` as ``raw_row``.
    """
    frame = vendor.copy()
    frame["raw_row"] = frame["raw_row"].astype(object)
    by_raw_row = {str(value): position for position, value in enumerate(frame["raw_row"])}
    for record in records:
        if record["status"] != "valid" or record["action"] == "absent_member_add":
            continue
        position = by_raw_row[str(record["vendor_raw_row"])]
        frame.iloc[position, frame.columns.get_loc("StartDate")] = record["start"].isoformat()
        frame.iloc[position, frame.columns.get_loc("EndDate")] = None if record["end"] is None else record["end"].isoformat()
    retained = [(f"{code}.US", start, end) for code, start, end in
                holdout_partition.parse_membership_entries(frame, components_retrieved_utc_date)[0]]
    appended = []
    for record in records:
        if record["status"] != "valid" or record["action"] != "absent_member_add":
            continue
        code, start, end = record["code"], record["start"], record["end"]
        if any(other == code and (other_end is None or start < other_end) and (end is None or other_start < end)
               for other, other_start, other_end in retained):
            record["status"] = "identity_refused"
            continue
        appended.append({"raw_row": record["supplement_id"], "Code": code.removesuffix(".US"), "Name": "",
                         "StartDate": start.isoformat(), "EndDate": None if end is None else end.isoformat(),
                         "IsActiveNow": None, "IsDelisted": None})
    if appended:
        frame = pd.concat([frame, pd.DataFrame(appended, columns=frame.columns)], ignore_index=True)
    return frame


def absent_member_priced(bar_rows: np.ndarray, start_row: int, end_row: int) -> bool:
    """M-7: an absent member is priced when it has a bar inside its membership interval."""
    return bool(((bar_rows >= start_row) & (bar_rows < end_row)).any())


def supplement_counts(records: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for record in records:
        bucket = counts.setdefault(record["action"], {})
        bucket[record["status"]] = bucket.get(record["status"], 0) + 1
    return {action: dict(sorted(values.items())) for action, values in sorted(counts.items())}


def discrepancy_rows(records: list[dict[str, Any]]) -> pd.DataFrame:
    """M-2: the vendor date of every correction row; non-primary or within-tolerance rows stay unadjudicated."""
    rows = [row for record in records for row in record["discrepancies"]]
    return pd.DataFrame(rows, columns=list(DISCREPANCY_COLUMNS))


# ---------------------------------------------------------------- change log (plan 2.3, M-8)


def match_changes(
    changes: pd.DataFrame,
    entries: list[dict[str, Any]],
    calendar: pd.DatetimeIndex,
) -> list[dict[str, Any]]:
    """Type every reconstructed change as ``vendor_entry``, ``supplement``, or ``unresolved``.

    ``entries`` holds the retained intervals with ``ref`` (vendor ``raw_row`` or
    ``supplement_id``), ``kind`` (``vendor_entry`` or ``supplement``), ``code``
    (``<Code>.US``), ``start``, and ``end``. A change matches when an entry of
    the same code, or the curator's ``match_ref`` with a documented code change
    in ``notes``, carries the corresponding date within 5 trading days. An
    invalid row is ``unresolved`` with its reason.
    """
    by_ref = {str(entry["ref"]): entry for entry in entries}
    ids = changes["change_id"]
    duplicates = set(ids[ids.duplicated(keep=False)])
    results = []
    for row in changes.to_dict(orient="records"):
        effective = parse_strict_date(row["effective_date"])
        result = {"change_id": row["change_id"], "action": row["action"], "code": row["code"],
                  "effective_date": effective, "match": "unresolved", "match_ref": "", "reason": ""}
        results.append(result)
        reason = ("duplicate_id" if row["change_id"] in duplicates else
                  "date_unparseable" if effective is None else
                  "action_unknown" if row["action"] not in ("add", "delete") else
                  "code_missing" if _blank(row["code"]) else _source_reason(row))
        if reason is not None:
            result["reason"] = f"change_invalid:{reason}"
            continue
        field = "start" if row["action"] == "add" else "end"

        def near(entry: dict[str, Any]) -> bool:
            value = entry[field]
            return value is not None and abs(trading_row(calendar, value) - trading_row(calendar, effective)) <= MATCH_TOLERANCE_ROWS

        claimed = by_ref.get(str(row["match_ref"])) if not _blank(row["match_ref"]) else None
        if claimed is not None and near(claimed) and (claimed["code"] == row["code"] or not _blank(row["notes"])):
            result.update(match=claimed["kind"], match_ref=str(claimed["ref"]))
            continue
        found = [entry for entry in entries if entry["code"] == row["code"] and near(entry)]
        if found:
            result.update(match=found[0]["kind"], match_ref=str(found[0]["ref"]))
        else:
            result["reason"] = "match_ref_unverified" if not _blank(row["match_ref"]) else "no_entry_within_tolerance"
    return results


def unresolved_change_fraction(changes: list[dict[str, Any]], start: date, end: date) -> float | None:
    """R3-2a: unresolved share of the changes effective in ``[start, end)``; ``None`` for an empty span."""
    span = [c for c in changes if c["effective_date"] is not None and start <= c["effective_date"] < end]
    undated = sum(1 for c in changes if c["effective_date"] is None)
    total = len(span) + undated
    if not total:
        return None
    return (sum(1 for c in span if c["match"] == "unresolved") + undated) / total


def vendor_endpoints(
    entries: list[dict[str, Any]],
    changes: list[dict[str, Any]],
    records: list[dict[str, Any]],
    start: date,
    end: date,
) -> list[dict[str, Any]]:
    """M-9: every add or delete endpoint of a retained vendor entry effective in ``[start, end)``, classified once.

    ``change_matched`` when a matched change names the entry, or its fill or
    correction, with that action; ``discrepancy`` when an M-2 discrepancy line
    names the entry and field; ``vendor_only`` otherwise. A vendor-only
    endpoint stays outside R3-2a and counts in R3-10.
    """
    vendor_ref = {r["supplement_id"]: str(r["vendor_raw_row"]) for r in records if r["action"] != "absent_member_add"}
    matched = {(vendor_ref.get(c["match_ref"], c["match_ref"]), c["action"]) for c in changes if c["match"] != "unresolved"}
    lines = {(str(line["vendor_raw_row"]), "add" if line["field"] == "start_date" else "delete")
             for record in records for line in record["discrepancies"]}
    endpoints = []
    for entry in entries:
        if entry["kind"] != "vendor_entry":
            continue
        for action, day in (("add", entry["start"]), ("delete", entry["end"])):
            if day is None or not start <= day < end:
                continue
            key = (entry["ref"], action)
            endpoint_class = "change_matched" if key in matched else "discrepancy" if key in lines else "vendor_only"
            endpoints.append({"ref": entry["ref"], "code": entry["code"], "action": action, "effective_date": day,
                              "class": endpoint_class})
    return endpoints


def m8_charges(
    changes: list[dict[str, Any]],
    calendar: pd.DatetimeIndex,
    first_row: int,
    last_row: int,
    coverage_start_row: int,
) -> int:
    """M-8 worst-case member-days of the unresolved changes on segment rows ``[first_row, last_row]``.

    An unresolved ``add`` counts its rows from the effective date to the matched
    deletion (the next ``delete`` of the code in the log) or to the last row; an
    unresolved ``delete`` counts its rows from the later of the first row and
    ``coverage_start_row`` up to the effective date.
    """
    total = 0
    dated = sorted((c for c in changes if c["effective_date"] is not None), key=lambda c: c["effective_date"])
    for change in dated:
        if change["match"] != "unresolved":
            continue
        row = trading_row(calendar, change["effective_date"])
        if change["action"] == "add":
            deletion = next((trading_row(calendar, c["effective_date"]) for c in dated
                             if c["action"] == "delete" and c["code"] == change["code"]
                             and c["effective_date"] > change["effective_date"]), last_row + 1)
            total += max(0, min(deletion, last_row + 1) - max(row, first_row))
        elif change["action"] == "delete":
            total += max(0, min(row, last_row + 1) - max(first_row, coverage_start_row))
    return total


# ---------------------------------------------------------------- coverage rule (plan 2.4)


def _month_ends(first: date, last_exclusive: date) -> list[date]:
    months = []
    month_end = holdout_partition._month_end(first.year, first.month)
    while month_end < last_exclusive:
        months.append(month_end)
        month_end = holdout_partition._month_end(month_end.year + month_end.month // 12, month_end.month % 12 + 1)
    return months


def as_of(calendar: pd.DatetimeIndex, day: date) -> date | None:
    """``d(m)``: the last calendar row on or before ``day``."""
    position = int(calendar.searchsorted(pd.Timestamp(day), side="right")) - 1
    return None if position < 0 else calendar[position].date()


def month_end_counts(
    entries: list[tuple[str, date, date | None]],
    calendar: pd.DatetimeIndex,
    first: date,
    components_retrieved_utc_date: date,
) -> list[dict[str, Any]]:
    """Rule 1: ``n_cur(m)`` at ``d(m)`` for every month-end from ``first`` before the retrieval date."""
    counts = []
    for month_end in _month_ends(first, components_retrieved_utc_date):
        day = as_of(calendar, month_end)
        n = 0 if day is None else sum(1 for _, start, end in entries if start <= day and (end is None or end > day))
        counts.append({"month_end": month_end, "as_of": day, "n_cur": n})
    return counts


def _band_screen(values: list[int]) -> bool:
    """Rule 2: the tolerant band rule with the first month-end in band."""
    band, hard = holdout_partition.BAND, holdout_partition.HARD_BAND
    exceptions = [i for i, n in enumerate(values) if not band[0] <= n <= band[1]]
    return (bool(values) and 0 not in exceptions and len(exceptions) <= holdout_partition.TOLERANCE_EXCEPTIONS
            and all(b - a > 1 for a, b in zip(exceptions, exceptions[1:]))
            and all(hard[0] <= values[i] <= hard[1] for i in exceptions))


def required_anchors(start: date, last_anchor: date) -> list[date]:
    """Rule 3: the month-end of ``start``, each December month-end, and ``last_anchor``, within ``[start, last_anchor]``."""
    anchors = {start, last_anchor} | {m for m in _month_ends(start, last_anchor) if m.month == 12}
    return sorted(a for a in anchors if start <= a <= last_anchor)


def anchor_results(
    start: date,
    counts: dict[date, dict[str, Any]],
    published: dict[date, int],
    last_anchor: date,
) -> list[dict[str, Any]]:
    """Rule 3 per required anchor: ``n_ref`` is the published count, else the 500 floor."""
    results = []
    for anchor in required_anchors(start, last_anchor):
        n_cur = counts[anchor]["n_cur"]
        if anchor in published:
            n_ref, kind = published[anchor], "published"
            passed = abs(n_ref - n_cur) <= ANCHOR_TOLERANCE
        else:
            n_ref, kind = FLOOR_ANCHOR_COUNT, "anchor_floor_500"
            passed = n_cur >= FLOOR_ANCHOR_MIN
        as_of = counts[anchor]["as_of"]
        results.append({"month_end": anchor.isoformat(), "as_of": None if as_of is None else as_of.isoformat(),
                        "kind": kind, "n_cur": n_cur, "n_ref": n_ref, "delta": n_cur - n_ref, "passed": passed})
    return results


def published_anchors(anchors: pd.DataFrame) -> dict[date, int]:
    """Published counts keyed by calendar month-end; a malformed row refuses."""
    published: dict[date, int] = {}
    for row in anchors.to_dict(orient="records"):
        month_end = parse_strict_date(row["month_end"])
        if month_end is None or not str(row["n_published"]).isdigit() or month_end in published:
            raise SnapshotRefusal("curated_file_malformed", f"{ANCHORS_FILE} row {row['month_end']!r}")
        published[month_end] = int(row["n_published"])
    return published


def curated_coverage_start_v2(
    counts: list[dict[str, Any]],
    published: dict[date, int],
    changes: list[dict[str, Any]],
    *,
    reconstruction_end: date,
    last_anchor: date,
    floor: date = COVERAGE_FLOOR,
) -> dict[str, Any]:
    """Rule 5: the earliest month-end ``m >= floor`` at which rules 2, 3, and 4 hold.

    ``reconstruction_end`` is the exclusive end of the change span (the carried
    ``holdout_start``); ``last_anchor`` is its preceding month-end. With no
    passing month-end the result carries ``status`` ``blocked:<code>`` from the
    first failing rule (band, anchors, changes) at the latest month-end the band
    screen admits, with the failing anchors listed.
    """
    by_month = {row["month_end"]: row for row in counts}
    candidates = [row["month_end"] for row in counts if floor <= row["month_end"] <= last_anchor]
    evaluations = []
    for month_end in candidates:
        tail = [row["n_cur"] for row in counts if row["month_end"] >= month_end]
        band = _band_screen(tail)
        anchors = anchor_results(month_end, by_month, published, last_anchor)
        fraction = unresolved_change_fraction(changes, month_end, reconstruction_end)
        change_ok = fraction is not None and fraction <= MAX_UNRESOLVED_CHANGE_FRACTION
        evaluation = {"month_end": month_end, "band": band, "anchors": anchors, "unresolved_change_fraction": fraction,
                      "anchors_passed": all(a["passed"] for a in anchors), "changes_passed": change_ok}
        evaluations.append(evaluation)
        if band and evaluation["anchors_passed"] and change_ok:
            return {"rule": COVERAGE_RULE, "status": "passed", "coverage_start_pre": month_end.isoformat(),
                    "anchors": anchors, "unresolved_change_fraction": fraction, "failing_anchors": []}
    admitted = [e for e in evaluations if e["band"]]
    last = admitted[-1] if admitted else (evaluations[-1] if evaluations else None)
    if last is None or not last["band"]:
        status = "blocked:coverage_start_undefined"
    elif not last["anchors_passed"]:
        status = "blocked:anchor_count_delta"
    elif last["unresolved_change_fraction"] is None:
        status = "blocked:membership_reconstruction_empty"
    else:
        status = "blocked:unresolved_membership_changes"
    return {"rule": COVERAGE_RULE, "status": status, "coverage_start_pre": None,
            "anchors": [] if last is None else last["anchors"],
            "unresolved_change_fraction": None if last is None else last["unresolved_change_fraction"],
            "failing_anchors": [] if last is None else [a for a in last["anchors"] if not a["passed"]],
            "evaluated_month_end": None if last is None else last["month_end"].isoformat()}


def dual_class_lines(names: list[str]) -> int:
    """Lines beyond one per company among active entries: names equal after dropping a share-class suffix."""
    bases = [_CLASS_SUFFIX.sub("", str(name).casefold()).strip() if name else None for name in names]
    named = [base for base in bases if base]
    return len(named) - len(set(named))
