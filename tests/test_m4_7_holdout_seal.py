"""Holdout seal derivation from raw membership counts (M4.7 plan 1.4, T-SEAL-1).

Synthetic membership fixtures only; no vendor file or network access.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from data.holdout_partition import (
    MEMBERSHIP_FILE,
    RETRIEVAL_ORDER,
    SnapshotRefusal,
    coverage_start,
    derive_holdout_window,
    monthly_raw_counts,
    parse_membership_entries,
    read_holdout_end,
    sha256_bytes,
    write_prospective_seal,
)


RETRIEVED = date(2026, 9, 25)


def entry(code: str | None, start: str | None, end: str | None = None) -> dict:
    return {"Code": code, "Name": f"{code} Inc", "StartDate": start, "EndDate": end, "IsActiveNow": "1", "IsDelisted": "0"}


def gap(codes: range, leave: str, rejoin: str) -> list[dict]:
    """Each code leaves before a month-end and rejoins after it (two raw entries)."""

    return [row for i in codes for row in (entry(f"C{i:03d}", "1989-01-10", leave), entry(f"C{i:03d}", rejoin))]


def membership(*, adjacent: bool = False, deep: bool = False, shift_years: int = 0) -> pd.DataFrame:
    """300 members from 1989, 500 from 1990-01, and isolated 465-member month-ends.

    Codes C000..C034 leave around 1995-03-31 and C035..C069 around 1997-07-31;
    ``adjacent`` adds three consecutive 465-member month-ends (1992-05..07);
    ``deep`` adds one 440-member month-end at 1996-01-31.
    """

    gapped = set(range(70))
    rows = gap(range(0, 35), "1995-03-15", "1995-04-10") + gap(range(35, 70), "1997-07-15", "1997-08-05")
    if adjacent:
        gapped |= set(range(70, 105))
        rows += gap(range(70, 105), "1992-05-10", "1992-08-05")
    if deep:
        gapped |= set(range(105, 165))
        rows += gap(range(105, 165), "1996-01-10", "1996-02-05")
    rows += [entry(f"C{i:03d}", "1989-01-10") for i in range(300) if i not in gapped]
    rows += [entry(f"C{i:03d}", "1990-01-15") for i in range(300, 500)]
    frame = pd.DataFrame(rows)
    if shift_years:
        for column in ("StartDate", "EndDate"):
            frame[column] = [
                f"{int(value[:4]) + shift_years}{value[4:]}" if isinstance(value, str) else None
                for value in frame[column]
            ]
    return frame


def counts_of(frame: pd.DataFrame, retrieved: date = RETRIEVED) -> dict[date, int]:
    entries, _ = parse_membership_entries(frame, retrieved)
    return dict(monthly_raw_counts(entries, retrieved))


def write_snapshot(snapshot_dir: Path, frame: pd.DataFrame, retrieved: date = RETRIEVED) -> str:
    path = snapshot_dir / MEMBERSHIP_FILE
    path.parent.mkdir(parents=True)
    frame.to_parquet(path, index=False)
    payload = path.read_bytes()
    manifest = {
        "snapshot": {"components_retrieved_utc_date": retrieved.isoformat()},
        "files": {"membership": {"path": MEMBERSHIP_FILE, "sha256": sha256_bytes(payload), "bytes": len(payload), "rows": len(frame)}},
        "entries": {},
    }
    (snapshot_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return sha256_bytes(payload)


def test_t_seal_1_raw_counts_and_tolerant_coverage_start() -> None:
    counts = counts_of(membership())
    assert counts[date(1989, 1, 31)] == 300
    assert counts[date(1989, 12, 31)] == 300
    assert counts[date(1990, 1, 31)] == 500
    assert counts[date(1995, 3, 31)] == 465
    assert counts[date(1995, 4, 30)] == 500
    assert counts[date(1997, 7, 31)] == 465
    assert max(counts) == date(2026, 8, 31)

    window = derive_holdout_window(membership(), RETRIEVED)
    assert window["holdout_start"] == "1990-01-31"
    assert window["coverage_start_strict"] == "1997-08-31"
    assert window["holdout_end_exclusive"] == "2000-01-31"


def test_t_seal_1_three_adjacent_exceptions_move_the_tolerant_start_forward() -> None:
    counts = counts_of(membership(adjacent=True))
    assert [counts[date(1992, month, day)] for month, day in ((5, 31), (6, 30), (7, 31))] == [465] * 3
    window = derive_holdout_window(membership(adjacent=True), RETRIEVED)
    assert window["holdout_start"] == "1992-08-31"
    assert window["coverage_start_strict"] == "1997-08-31"
    assert window["holdout_end_exclusive"] == "2002-08-31"


def test_t_seal_1_exception_outside_the_hard_band_is_not_tolerated() -> None:
    counts = counts_of(membership(deep=True))
    assert counts[date(1996, 1, 31)] == 440
    assert derive_holdout_window(membership(deep=True), RETRIEVED)["holdout_start"] == "1996-02-29"


def test_t_seal_1_coverage_start_rule_on_hand_counts() -> None:
    months = [date(2000, month, 28) for month in range(1, 13)]
    series = lambda values: list(zip(months, values))  # noqa: E731
    base = [400, 500, 469, 500, 531, 500, 500, 469, 500, 500, 500, 500]
    assert coverage_start(series(base), 3) == months[1]
    assert coverage_start(series(base), 0) == months[8]
    four = [500, 469, 500, 469, 500, 469, 500, 469, 500, 500, 500, 500]
    assert coverage_start(series(four), 3) == months[2]
    adjacent = [500, 469, 469, 500, 500, 500, 500, 500, 500, 500, 500, 500]
    assert coverage_start(series(adjacent), 3) == months[3]
    assert coverage_start(series([400] * 12), 3) is None
    # m* itself is in band: a tolerated exception never opens the window.
    assert coverage_start(series([460] + [500] * 11), 3) == months[1]


def test_t_seal_1_entry_rule_counts_shared_with_the_build() -> None:
    frame = pd.DataFrame(
        [
            entry("OPEN", "2000-01-03", "2026-09-26"),
            entry("SHUT", "2000-01-03", "2026-09-25"),
            entry("DUP", "2000-01-03", "2001-01-03"),
            entry("DUP", "2000-01-03", "2001-01-03"),
            entry("OVR", "2000-01-03", "2002-01-03"),
            entry("OVR", "2001-06-01", None),
            entry("ADJ", "2000-01-03", "2001-01-03"),
            entry("ADJ", "2001-01-03", None),
            entry(None, "2000-01-03"),
            entry("NOSTART", ""),
            entry("BAD", "2000/01/03"),
            entry("BADEND", "2000-01-03", "20010103"),
            entry("DEG", "2000-01-03", "2000-01-03"),
        ]
    )
    retained, counts = parse_membership_entries(frame, RETRIEVED)
    assert retained == [
        ("OPEN", date(2000, 1, 3), None),
        ("SHUT", date(2000, 1, 3), date(2026, 9, 25)),
        ("DUP", date(2000, 1, 3), date(2001, 1, 3)),
        ("ADJ", date(2000, 1, 3), date(2001, 1, 3)),
        ("ADJ", date(2001, 1, 3), None),
    ]
    assert counts == {
        "raw_entries": 13,
        "entry_missing_field": 2,
        "entry_unparseable_date": 2,
        "degenerate_interval": 1,
        "exact_duplicate_collapsed": 1,
        "raw_overlap": 2,
        "retained": 5,
    }


def test_t_seal_1_prospective_seal_bytes_hash_and_rerun_stability(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    membership_sha = write_snapshot(first, membership())
    write_snapshot(second, membership())
    record, prospective = write_prospective_seal(
        first, sealed_at="2026-09-25T12:00:00Z", sealing_actor="coordinator", authorization_reference="log-1"
    )
    seal_bytes = (first / "holdout_seal_v1.json").read_bytes()
    assert prospective == sha256_bytes(seal_bytes)
    assert json.loads(seal_bytes) == record
    assert record["schema_version"] == "m4_7_holdout_seal_v1"
    assert record["coverage_start_rule"] == "coverage_start_tolerant_3_isolated_v1"
    assert (record["holdout_start"], record["holdout_end_exclusive"]) == ("1990-01-31", "2000-01-31")
    assert record["band"] == [470, 530] and record["tolerance_exceptions"] == 3
    assert record["inputs"] == {"components_raw_sha256": membership_sha, "components_retrieved_utc_date": "2026-09-25"}
    assert record["value_fields_accessed"] == []
    assert record["confirmation"]["status"] == "pending"
    assert record["retrieval_order"] == list(RETRIEVAL_ORDER)
    assert read_holdout_end(first) == date(2000, 1, 31)

    rerun, _ = write_prospective_seal(
        second, sealed_at="2027-09-25T12:00:00Z", sealing_actor="owner", authorization_reference="log-2"
    )
    volatile = {"sealed_at", "sealing_actor", "authorization_reference"}
    assert {k: v for k, v in rerun.items() if k not in volatile} == {k: v for k, v in record.items() if k not in volatile}
    with pytest.raises(SnapshotRefusal) as refused:
        write_prospective_seal(first, sealed_at="x", sealing_actor="x", authorization_reference="x")
    assert refused.value.code == "snapshot_file_exists"


def test_t_seal_1_refusals(tmp_path: Path) -> None:
    with pytest.raises(SnapshotRefusal) as refused:
        derive_holdout_window(membership(shift_years=15), RETRIEVED)
    assert refused.value.code == "holdout_overlaps_prior_exposure"
    with pytest.raises(SnapshotRefusal) as refused:
        read_holdout_end(tmp_path)
    assert refused.value.code == "holdout_seal_missing"

    snapshot = tmp_path / "tampered"
    write_snapshot(snapshot, membership())
    (snapshot / MEMBERSHIP_FILE).write_bytes((snapshot / MEMBERSHIP_FILE).read_bytes() + b"x")
    with pytest.raises(SnapshotRefusal) as refused:
        write_prospective_seal(snapshot, sealed_at="x", sealing_actor="x", authorization_reference="x")
    assert refused.value.code == "artifact_hash_mismatch"
    assert not (snapshot / "holdout_seal_v1.json").exists()
