"""M4.8 Stage A: curated membership rules M-1..M-8 and ``curated_coverage_start_v2`` (plan 2.3, 2.4; T-MEM, T-COV)."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from data.constituent_table import build_pit_membership_mask, load_constituent_intervals_csv
from data.holdout_partition import classify_membership_entries
from m4_7_snapshot_support import entry
from m4_8_snapshot_support import (
    ALL_ROWS,
    CAL2,
    bars2,
    change_row,
    row_of,
    snapshot_v2,
    supplement_row,
)
from research import m4_8_membership as mm
from research.m4_7_coverage_census import derive_readiness_v3, membership_census
from research.m4_7_universe_build import Snapshot, discovery_segments, reset_in_month


CAL = pd.bdate_range("2010-01-01", "2021-12-31", name="date")
RETRIEVED = date(2021, 12, 31)
FLOOR, END, LAST_ANCHOR = date(2011, 8, 31), date(2019, 7, 31), date(2019, 6, 30)


def vendor(*rows):
    """A vendor components frame; each row is ``(Code, StartDate, EndDate[, Name])``."""
    records = []
    for position, row in enumerate(rows):
        code, start, end, *name = row
        records.append({"raw_row": position, "Code": code, "Name": name[0] if name else f"{code} Inc",
                        "StartDate": start, "EndDate": end, "IsActiveNow": 1, "IsDelisted": 0})
    return pd.DataFrame(records)


def supplement(*rows):
    return pd.DataFrame(list(rows), columns=list(mm.SUPPLEMENT_COLUMNS)).fillna("")


def statuses(records):
    return [r["status"] for r in records]


# ---------------------------------------------------------------- T-MEM


def test_t_mem_1_a_valid_fill_supplies_only_the_start_date():
    frame = vendor(("AAA", None, "2015-06-30"))
    records = mm.validate_supplement(supplement(supplement_row("MS-1", "start_date_fill", "AAA.US", "2012-03-01",
                                                               raw_row="0")), frame, CAL)
    assert statuses(records) == ["valid"] and records[0]["end"] == date(2015, 6, 30)
    applied = mm.apply_supplement(frame, records, RETRIEVED)
    assert classify_membership_entries(applied, RETRIEVED)[0]["outcome"] == "retained"
    assert applied.loc[0, "StartDate"] == "2012-03-01" and applied.loc[0, "EndDate"] == "2015-06-30"
    assert mm.supplement_counts(records) == {"start_date_fill": {"valid": 1}}


def test_t_mem_2_a_fill_targeting_a_dated_or_shared_entry_is_typed():
    frame = vendor(("AAA", "2012-01-03", "2015-06-30"), ("BBB", None, "2016-01-29"))
    records = mm.validate_supplement(supplement(
        supplement_row("MS-1", "start_date_fill", "AAA.US", "2011-09-01", raw_row="0"),
        supplement_row("MS-2", "start_date_fill", "BBB.US", "2012-01-03", raw_row="1"),
        supplement_row("MS-3", "start_date_fill", "BBB.US", "2012-02-01", raw_row="1"),
        supplement_row("MS-4", "start_date_fill", "ZZZ.US", "2012-02-01", raw_row="9")), frame, CAL)
    assert statuses(records) == ["supplement_invalid:target_not_undated", "supplement_invalid:target_ambiguous",
                                 "supplement_invalid:target_ambiguous", "supplement_invalid:target_ambiguous"]


def test_t_mem_3_unparseable_and_degenerate_rows_are_typed():
    frame = vendor(("AAA", None, "2015-06-30"))
    records = mm.validate_supplement(supplement(
        supplement_row("MS-1", "start_date_fill", "AAA.US", "2012/03/01", raw_row="0"),
        supplement_row("MS-2", "start_date_fill", "AAA.US", "2016-01-04", raw_row="0"),
        supplement_row("MS-3", "absent_member_add", "NEW.US", "2014-05-01", "2014-05-01")), frame, CAL)
    assert statuses(records) == ["supplement_invalid:date_unparseable", "supplement_invalid:target_ambiguous",
                                 "supplement_invalid:degenerate_interval"]
    alone = mm.validate_supplement(supplement(supplement_row("MS-2", "start_date_fill", "AAA.US", "2016-01-04",
                                                             raw_row="0")), frame, CAL)
    assert statuses(alone) == ["supplement_invalid:degenerate_interval"]


def test_t_mem_4_missing_source_or_corroboration_is_typed_and_counted():
    records = mm.validate_supplement(supplement(
        {**supplement_row("MS-1", "absent_member_add", "NEW.US", "2014-05-01"), "source_locator": ""},
        supplement_row("MS-2", "absent_member_add", "NEX.US", "2014-05-01", source_kind="public_changes_list"),
        supplement_row("MS-3", "absent_member_add", "NEY.US", "2014-05-01", source_kind="public_changes_list",
                       corroboration="second"),
        supplement_row("MS-4", "renamed", "NEZ.US", "2014-05-01")), vendor(), CAL)
    assert statuses(records) == ["supplement_invalid:source_missing", "supplement_invalid:corroboration_missing",
                                 "valid", "supplement_invalid:action_unknown"]
    assert mm.supplement_counts(records)["absent_member_add"] == {
        "supplement_invalid:corroboration_missing": 1, "supplement_invalid:source_missing": 1, "valid": 1}


def test_t_mem_5_an_absent_member_colliding_with_a_vendor_code_is_identity_refused_and_charged():
    frame = vendor(("AAA", "2012-01-03", "2015-06-30"))
    records = mm.validate_supplement(supplement(
        supplement_row("MS-1", "absent_member_add", "AAA.US", "2014-01-02", "2016-01-04"),
        supplement_row("MS-2", "absent_member_add", "AAA.US", "2016-01-04", "2017-01-03")), frame, CAL)
    applied = mm.apply_supplement(frame, records, RETRIEVED)
    assert statuses(records) == ["identity_refused", "valid"]
    assert applied["raw_row"].tolist() == [0, "MS-2"]


def test_t_mem_6_and_7_supplement_members_enter_the_mask_by_the_registered_lag(tmp_path, monkeypatch):
    start = "2018-09-04"
    curated = {"supplement": [supplement_row("MS-1", "absent_member_add", "ABS.US", start),
                              supplement_row("MS-2", "absent_member_add", "UNP.US", start)]}
    harness = snapshot_v2(tmp_path, monkeypatch, "M6", [entry("AAA", "2018-01-02")],
                          {"AAA.US": bars2(ALL_ROWS), "ABS.US": bars2(ALL_ROWS)}, curated=curated, requested=["ABS.US"])
    snap = harness.snapshot_dir
    table = load_constituent_intervals_csv(snap / "membership/constituent_intervals.csv")
    assert "ABS.US#E1" in set(table.data["permanent_id"])
    mask = build_pit_membership_mask(table, CAL2, ["ABS.US#E1"], signal_lag_periods=1)
    assert int(mask["ABS.US#E1"].to_numpy().argmax()) == row_of(start) + 1
    intervals = pd.read_csv(snap / "identity/interval_results.csv", dtype=str, keep_default_na=False)
    unpriced = intervals[intervals["raw_row"] == "MS-2"]
    assert unpriced["resolution"].tolist() == ["no_containing_episode:no_vendor_bars:absent"]
    result = membership_census(Snapshot.open(snap), mm.read_curated(snap / "membership"))
    assert result["public"]["absent_members"] == {"priced": 1, "unpriced": 1, "identity_refused": 0}


def test_t_mem_8_a_primary_correction_governs_and_a_non_primary_one_is_unadjudicated():
    frame = vendor(("AAA", "2012-01-03", "2015-06-30"), ("BBB", "2012-01-03", None))
    records = mm.validate_supplement(supplement(
        supplement_row("MS-1", "date_correction", "AAA.US", "2012-01-03", "2015-09-30", raw_row="0"),
        supplement_row("MS-2", "date_correction", "BBB.US", "2012-02-15", raw_row="1", source_kind="sec_filing"),
        supplement_row("MS-3", "date_correction", "AAA.US", "2012-01-05", "2015-06-30", raw_row="0")), frame, CAL)
    assert statuses(records) == ["supplement_invalid:target_ambiguous", "supplement_invalid:correction_not_primary",
                                 "supplement_invalid:target_ambiguous"]
    records = mm.validate_supplement(supplement(
        supplement_row("MS-1", "date_correction", "AAA.US", "2012-01-03", "2015-09-30", raw_row="0"),
        supplement_row("MS-2", "date_correction", "BBB.US", "2012-02-15", raw_row="1", source_kind="sec_filing")),
        frame, CAL)
    assert statuses(records) == ["valid", "supplement_invalid:correction_not_primary"]
    applied = mm.apply_supplement(frame, records, RETRIEVED)
    assert applied.loc[0, "EndDate"] == "2015-09-30" and applied.loc[1, "StartDate"] == "2012-01-03"
    discrepancies = mm.discrepancy_rows(records)
    assert discrepancies[["supplement_id", "field", "adjudication"]].values.tolist() == [
        ["MS-1", "end_date", "membership_date_corrected_primary_v1"], ["MS-2", "start_date", "unadjudicated"]]
    near = mm.validate_supplement(supplement(
        supplement_row("MS-9", "date_correction", "AAA.US", "2012-01-09", "2015-06-30", raw_row="0")), frame, CAL)
    assert statuses(near) == ["supplement_invalid:correction_within_tolerance"]


def test_t_mem_8_the_corrected_exit_governs_eligibility_across_a_reset(tmp_path, monkeypatch):
    curated = {"supplement": [supplement_row("MS-1", "date_correction", "AAA.US", "2018-01-02", "2018-12-31",
                                             raw_row="0")]}
    harness = snapshot_v2(tmp_path, monkeypatch, "M8", [entry("AAA", "2018-01-02", "2018-09-28")],
                          {"AAA.US": bars2(ALL_ROWS)}, curated=curated)
    table = load_constituent_intervals_csv(harness.snapshot_dir / "membership/constituent_intervals.csv")
    assert table.data["end_date"].dt.date.tolist() == [date(2018, 12, 31)]
    mask = build_pit_membership_mask(table, CAL2, ["AAA.US#E1"], signal_lag_periods=1)
    october_reset = reset_in_month(CAL2, date(2018, 10, 31))
    assert bool(mask["AAA.US#E1"].iloc[october_reset]) and not bool(mask["AAA.US#E1"].iloc[row_of("2019-01-31")])


def test_t_mem_9_a_change_within_five_trading_days_matches_and_a_later_one_stays_unresolved():
    entries = [{"ref": "0", "kind": "vendor_entry", "code": "AAA.US", "start": date(2014, 3, 3), "end": None},
               {"ref": "MS-1", "kind": "supplement", "code": "NEW.US", "start": date(2015, 1, 5), "end": date(2016, 1, 4)}]
    changes = pd.DataFrame([change_row("RC-1", "2014-03-10", "add", "AAA.US"),
                            change_row("RC-2", "2014-03-11", "add", "AAA.US"),
                            change_row("RC-3", "2016-01-08", "delete", "NEW.US"),
                            change_row("RC-4", "2015-01-05", "add", "OLD.US", match_ref="MS-1", notes="renamed"),
                            change_row("RC-5", "2015-01-05", "add", "OLD.US", match_ref="MS-1"),
                            change_row("RC-6", "2015/01/05", "add", "OLD.US")], columns=list(mm.CHANGE_COLUMNS))
    result = mm.match_changes(changes, entries, CAL)
    assert [(c["match"], c["match_ref"]) for c in result] == [
        ("vendor_entry", "0"), ("unresolved", ""), ("supplement", "MS-1"), ("supplement", "MS-1"),
        ("unresolved", ""), ("unresolved", "")]
    assert result[5]["reason"] == "change_invalid:date_unparseable"
    assert mm.unresolved_change_fraction(result, date(2014, 1, 1), date(2019, 7, 31)) == pytest.approx(3 / 6)


def test_t_mem_9_a_change_row_without_a_valid_source_stays_unresolved_despite_an_exact_match():
    entries = [{"ref": "0", "kind": "vendor_entry", "code": "AAA.US", "start": date(2015, 11, 10), "end": date(2015, 11, 11)}]
    no_locator = {**change_row("RC-3", "2015-11-10", "add", "AAA.US", match_ref="0"), "source_locator": ""}
    changes = pd.DataFrame([
        change_row("RC-1", "2015-11-10", "add", "AAA.US", match_ref="0", source_kind="public_changes_list"),
        change_row("RC-2", "2015-11-11", "delete", "AAA.US", source_kind="public_changes_list", corroboration="second"),
        no_locator,
        change_row("RC-4", "2015-11-10", "add", "AAA.US", source_kind="press_release"),
        change_row("RC-5", "2015-11-11", "delete", "AAA.US"),
    ], columns=list(mm.CHANGE_COLUMNS))
    result = mm.match_changes(changes, entries, CAL)
    assert [(c["match"], c["match_ref"], c["reason"]) for c in result] == [
        ("unresolved", "", "change_invalid:corroboration_missing"),
        ("vendor_entry", "0", ""),
        ("unresolved", "", "change_invalid:source_missing"),
        ("unresolved", "", "change_invalid:source_missing"),
        ("vendor_entry", "0", "")]
    assert mm.unresolved_change_fraction(result, date(2015, 1, 1), date(2019, 7, 31)) == pytest.approx(3 / 5)
    assert mm.unresolved_change_fraction(result, date(2015, 12, 31), date(2019, 7, 31)) is None


def test_t_mem_10_m8_worst_case_charges_and_a_not_evaluable_segment():
    calendar = pd.bdate_range("2014-01-01", "2014-12-31")
    changes = [{"change_id": "RC-1", "action": "add", "code": "A.US", "effective_date": date(2014, 3, 3), "match": "unresolved"},
               {"change_id": "RC-2", "action": "add", "code": "B.US", "effective_date": date(2014, 3, 3), "match": "unresolved"},
               {"change_id": "RC-3", "action": "delete", "code": "B.US", "effective_date": date(2014, 4, 1), "match": "vendor_entry"},
               {"change_id": "RC-4", "action": "delete", "code": "C.US", "effective_date": date(2014, 6, 2), "match": "unresolved"}]
    first, last = 10, 200
    row = lambda d: int(calendar.searchsorted(pd.Timestamp(d)))  # noqa: E731
    expected = (last + 1 - row("2014-03-03")) + (row("2014-04-01") - row("2014-03-03")) + (row("2014-06-02") - 40)
    assert mm.m8_charges(changes, calendar, first, last, coverage_start_row=40) == expected
    base = _clean_readiness()
    blocked = derive_readiness_v3({**base, "unpriced_eligible_fraction": {"pre": None, "post": 0.0}})
    assert blocked["status"] == "blocked:unpriced_eligible_member_days"


def _clean_readiness():
    return {"pre_ic_months": 70, "unresolved_change_fraction": 0.0, "failing_anchors": [],
            "unpriced_absent_fraction": {"pre": 0.0, "post": 0.0}, "unpriced_eligible_fraction": {"pre": 0.0, "post": 0.0},
            "residual_count": 0, "untradeable_fraction": 0.0, "identity_refusal_fraction": 0.0,
            "off_calendar_fraction": 0.0, "calendar_covers_coverage_start": True, "benchmark_complete": True,
            "snapshot_integrity": True, "holdout_band_after_identity": True, "retrieval_complete": True,
            "total_ic_months": 130, "vp2_revisit_required": False, "seal_carry_passed": True, "discrepancy_fraction": 0.0}


# ---------------------------------------------------------------- T-COV


def series(overrides=None, default=500, start=date(2010, 1, 31)):
    """Month-end counts from ``start`` through 2021-11-30 with ``as_of`` on the business-day calendar."""
    months = mm._month_ends(start, date(2021, 12, 31))
    return [{"month_end": m, "as_of": mm.as_of(CAL, m), "n_cur": (overrides or {}).get(m, default)} for m in months]


def coverage(counts, published=None, changes=None):
    changes = changes if changes is not None else [
        {"change_id": "RC-1", "action": "add", "code": "A.US", "effective_date": date(2018, 1, 2), "match": "vendor_entry"}]
    return mm.curated_coverage_start_v2(counts, published or {}, changes, reconstruction_end=END, last_anchor=LAST_ANCHOR)


def test_t_cov_1_to_5_band_screen_truth_table():
    assert coverage(series())["coverage_start_pre"] == "2011-08-31"
    three = {date(2013, 3, 31): 465, date(2015, 5, 31): 535, date(2020, 9, 30): 460}
    assert coverage(series(three))["coverage_start_pre"] == "2011-08-31"
    adjacent = {date(2014, 4, 30): 465, date(2014, 5, 31): 466}
    assert coverage(series(adjacent))["coverage_start_pre"] == "2014-06-30"
    hard = {date(2013, 2, 28): 440}
    assert coverage(series(hard))["coverage_start_pre"] == "2013-03-31"
    assert coverage(series(start=date(2005, 1, 31)))["coverage_start_pre"] == "2011-08-31"


def test_t_cov_6_and_10_r_pre_last_and_a_saturday_month_end():
    calendar = pd.bdate_range("2013-01-01", "2021-12-31")
    pre, _ = discovery_segments(calendar, date(2019, 7, 31), date(2020, 7, 31), date(2013, 8, 31))
    assert calendar[pre.first_reset_row] == pd.Timestamp("2013-08-30")
    assert calendar[pre.last_ic_reset_row] == pd.Timestamp("2019-05-31")
    assert calendar[pre.last_book_row] == pd.Timestamp("2019-06-28")
    assert calendar[reset_in_month(calendar, date(2013, 8, 31))] == pd.Timestamp("2013-08-30")


def test_t_cov_7_an_evidenced_absent_member_never_turns_a_passing_start_into_a_block():
    entries = [(f"M{i}.US", date(2009, 1, 2), None) for i in range(497)]
    published = {m: 500 for m in mm.required_anchors(FLOOR, LAST_ANCHOR)}
    counts = mm.month_end_counts(entries, CAL, date(2010, 1, 31), RETRIEVED)
    before = coverage(counts, published)
    added = mm.month_end_counts(entries + [("ABS.US", date(2011, 5, 2), None)], CAL, date(2010, 1, 31), RETRIEVED)
    after = coverage(added, published)
    assert before["coverage_start_pre"] == after["coverage_start_pre"] == "2011-08-31"
    assert all(a["n_cur"] - a["n_ref"] <= 5 for a in after["anchors"])


def test_t_cov_8_an_undercount_at_a_published_anchor_moves_the_start_past_it():
    counts = series({date(2013, 12, 31): 470})
    result = coverage(counts, {date(2013, 12, 31): 500})
    assert result["coverage_start_pre"] == "2014-01-31"
    first = coverage(counts, {date(2013, 12, 31): 500, date(2011, 8, 31): 500})
    assert first["coverage_start_pre"] == "2014-01-31"


def test_t_cov_9_floor_anchor_edge_and_unresolved_change_fraction():
    assert coverage(series({date(2012, 12, 31): 495}))["coverage_start_pre"] == "2011-08-31"
    assert coverage(series({date(2012, 12, 31): 494}))["coverage_start_pre"] == "2013-01-31"
    changes = [{"change_id": f"RC-{i}", "action": "add", "code": "A.US", "effective_date": date(2012, 1 + i % 12, 2),
                "match": "unresolved" if i == 0 else "vendor_entry"} for i in range(30)]
    changes += [{"change_id": f"RC-L{i}", "action": "add", "code": "A.US", "effective_date": date(2016, 1, 4),
                 "match": "vendor_entry"} for i in range(30)]
    assert coverage(series(), changes=changes)["coverage_start_pre"] == "2011-08-31"
    changes[1]["match"] = "unresolved"
    result = coverage(series(), changes=changes)
    assert result["coverage_start_pre"] == "2012-01-31" and result["unresolved_change_fraction"] == pytest.approx(1 / 57)
    assert coverage(series(), changes=[])["status"] == "blocked:membership_reconstruction_empty"


def test_t_cov_11_the_upper_crossing_blocks_and_lists_the_anchor():
    published = {LAST_ANCHOR: 500}
    passing = coverage(series({LAST_ANCHOR: 505}), published)
    assert passing["coverage_start_pre"] == "2011-08-31"
    crossing = coverage(series({LAST_ANCHOR: 506}), published)
    assert crossing["coverage_start_pre"] is None and crossing["status"] == "blocked:anchor_count_delta"
    assert [a["month_end"] for a in crossing["failing_anchors"]] == ["2019-06-30"]


def test_t_cov_12_anchor_dates_evaluate_at_the_last_trading_day_and_dual_class_lines_are_reported(tmp_path, monkeypatch):
    counts = {row["month_end"]: row for row in series()}
    results = mm.anchor_results(date(2011, 12, 31), counts, {}, LAST_ANCHOR)
    as_of = {a["month_end"]: a["as_of"] for a in results}
    assert as_of["2011-12-31"] == "2011-12-30" and as_of["2017-12-31"] == "2017-12-29" and as_of["2019-06-30"] == "2019-06-28"
    assert mm.dual_class_lines(["Alpha Inc Class A", "Alpha Inc Class C", "Beta Corp", "", "Gamma Series B"]) == 1
    harness = snapshot_v2(tmp_path, monkeypatch, "C12", [
        entry("ALA", "2018-01-02", name="Alpha Inc Class A"), entry("ALC", "2018-01-02", name="Alpha Inc Class C"),
        entry("BET", "2018-01-02", name="Beta Corp")],
        {"ALA.US": bars2(ALL_ROWS), "ALC.US": bars2(ALL_ROWS), "BET.US": bars2(ALL_ROWS)}, build=False)
    result = membership_census(Snapshot.open(harness.snapshot_dir), mm.read_curated(harness.snapshot_dir / "membership"))
    floor = [a for a in result["public"]["anchors"] if a["kind"] == "anchor_floor_500" and a["as_of"]]
    assert floor and floor[-1]["as_of"] == "2019-06-28" and floor[-1]["dual_class_lines"] == 1


def test_t_mem_9_a_change_may_name_a_fill_by_supplement_id_with_a_documented_code_change(tmp_path, monkeypatch):
    curated = {"supplement": [supplement_row("MS-1", "start_date_fill", "OLD.US", "2018-03-01", raw_row="0")],
               "changes": [change_row("RC-1", "2018-03-02", "add", "NEW.US", match_ref="MS-1", notes="code change NEW to OLD"),
                           change_row("RC-2", "2018-03-02", "add", "NEW.US", match_ref="MS-1")]}
    harness = snapshot_v2(tmp_path, monkeypatch, "FIL", [entry("OLD", None, "2019-03-29"), entry("AAA", "2018-01-02")],
                          {"OLD.US": bars2(ALL_ROWS), "AAA.US": bars2(ALL_ROWS)}, curated=curated, build=False)
    result = membership_census(Snapshot.open(harness.snapshot_dir), mm.read_curated(harness.snapshot_dir / "membership"))
    assert [(c["match"], c["match_ref"]) for c in result["changes"]] == [("supplement", "MS-1"), ("unresolved", "")]
