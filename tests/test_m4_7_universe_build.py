"""M4.7 stage a-2 universe build oracles (plan 1.5, 1.6, 2; T-UNI-1..10, 12..17).

Every snapshot is produced by the merged a-1 retrieval module from a synthetic
vendor (``tests/m4_7_snapshot_support.py``). T-UNI-11 is an a-0 oracle in
``tests/test_m4_7_engine_bases.py``.
"""

from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
import pytest

from data.constituent_table import build_pit_membership_mask, load_constituent_intervals_csv
from data.holdout_partition import SnapshotRefusal
from data.parquet_loader import load_eod_cohort_panels
from features.liquidity import calculate_amihud_illiquidity
from m4_7_snapshot_support import (
    CAL,
    I_H,
    Harness,
    bars,
    build_manifest,
    day,
    entry,
    interval_rows,
    master_rows,
    panel,
    read_csv,
    record_reads,
    rows,
    turnover,
)
from research.m4_7_common_support import scheduled_reset_rows
from research.m4_7_universe_build import build_universe, normalize_name
from research.real_data_multifactor_diagnostic import build_adjusted_research_panels


N = len(CAL)
FULL = rows(0, N)
C_DISC = CAL[I_H:]
RESETS = scheduled_reset_rows(CAL)


def snapshot(tmp_path, monkeypatch, name, entries, codes, *, listed=(), delisted=(), build=True, harness_hook=None):
    """Retrieve a synthetic snapshot with ``SPY.US`` on every row and run the universe build."""
    harness = Harness(tmp_path, monkeypatch, snapshot_id=name)
    vendor = harness.vendor
    vendor.entries, vendor.listed, vendor.delisted = list(entries), list(listed), list(delisted)
    vendor.code("SPY.US", bars(FULL))
    for code, spec in codes.items():
        vendor.code(code, *spec) if isinstance(spec, tuple) else vendor.code(code, spec)
    if harness_hook is None:
        harness.retrieve()
    else:
        harness_hook(harness)
    if build:
        build_universe(harness.snapshot_dir)
    return harness.snapshot_dir


def by_id(frame, column="interval_id"):
    return {row[column]: row for row in frame.to_dict(orient="records")}


def resolution_of(snap, code):
    return [row["resolution"] for row in interval_rows(snap).to_dict(orient="records") if row["vendor_code"] == code]


def master_of(snap, code):
    return [row for row in master_rows(snap).to_dict(orient="records") if row["vendor_code"] == code]


def intervals_csv(snap):
    return read_csv(snap / "membership/constituent_intervals.csv")


def inventory(snap):
    return json.loads((snap / "panel/inventory_discovery.json").read_text())


def load_panels(snap, pids):
    return load_eod_cohort_panels(snap / "panel", pids, inventory_path=snap / "panel/inventory_discovery.json")


def assert_loaded_factor_equals_written(snap):
    pids = [record["symbol"] for record in inventory(snap)["files"]]
    loaded = load_panels(snap, pids)
    for pid in pids:
        written = panel(snap, pid).set_index("date")["split_factor"]
        np.testing.assert_array_equal(loaded["split_factor"][pid].dropna().to_numpy(), written.to_numpy())


# ---------------------------------------------------------------- T-UNI-1, 2, 3, 4


def test_t_uni_1_clean_member_interval_and_mask_boundaries(tmp_path, monkeypatch):
    snap = snapshot(tmp_path, monkeypatch, "u1", [entry("AAA", day(300), day(500))], {"AAA.US": bars(FULL)})
    table = intervals_csv(snap)
    assert table.to_dict(orient="records") == [{
        "symbol": "AAA.US", "permanent_id": "AAA.US#E1", "start_date": day(300), "end_date": day(500),
        "start_known_at": day(300), "end_known_at": day(500)}]
    mask = build_pit_membership_mask(load_constituent_intervals_csv(snap / "membership/constituent_intervals.csv"),
                                     CAL, ["AAA.US#E1"], signal_lag_periods=1)["AAA.US#E1"]
    assert not mask.iloc[300] and mask.iloc[301]
    assert mask.iloc[500] and not mask.iloc[501]
    row = interval_rows(snap).iloc[0]
    assert (row["m_in"], row["m_out"], row["resolution"]) == (day(301), day(501), "resolved")


def test_t_uni_2_reused_ticker_with_a_gap_yields_two_permanent_ids(tmp_path, monkeypatch):
    first, second = rows(I_H + 10, I_H + 150), rows(I_H + 210, N)
    snap = snapshot(tmp_path, monkeypatch, "u2",
                    [entry("REU", day(I_H + 20), day(I_H + 140), name="Old Co"), entry("REU", day(I_H + 220), name="New Co")],
                    {"REU.US": bars(first + second)})
    assert [row["permanent_id"] for row in master_of(snap, "REU.US")] == ["REU.US#E1", "REU.US#E2"]
    for pid in ("REU.US#E1", "REU.US#E2"):
        frame = panel(snap, pid)
        assert frame["permanent_id"].unique().tolist() == [pid] and frame["symbol"].unique().tolist() == ["REU.US"]
    loaded = load_panels(snap, ["REU.US#E1", "REU.US#E2"])
    assert list(loaded["adjusted_close"].columns) == ["REU.US#E1", "REU.US#E2"]
    table = load_constituent_intervals_csv(snap / "membership/constituent_intervals.csv")
    mask = build_pit_membership_mask(table, CAL, ["REU.US#E1", "REU.US#E2"], signal_lag_periods=1)
    assert mask["REU.US#E1"].to_numpy().nonzero()[0].tolist() == list(range(I_H + 21, I_H + 141))
    assert mask["REU.US#E2"].to_numpy().nonzero()[0].tolist() == list(range(I_H + 221, N))


def test_t_uni_3_continuous_history_with_different_names_fails_closed(tmp_path, monkeypatch):
    snap = snapshot(tmp_path, monkeypatch, "u3",
                    [entry("CON", day(I_H + 20), day(I_H + 140), name="Alpha Inc"), entry("CON", day(I_H + 140), name="Beta Corp")],
                    {"CON.US": bars(FULL)})
    assert resolution_of(snap, "CON.US") == ["ambiguous_reuse_continuous_history"] * 2
    assert "CON.US" not in intervals_csv(snap)["symbol"].tolist()
    (row,) = master_of(snap, "CON.US")
    assert (row["permanent_id"], row["resolution"]) == ("", "ambiguous_reuse_continuous_history")
    assert "CON.US#E1" not in [record["symbol"] for record in inventory(snap)["files"]]


def test_t_uni_4_short_gap_discontinuity_needs_a_nearby_split_row(tmp_path, monkeypatch):
    jump = I_H + 311
    history = bars(rows(I_H + 10, I_H + 301)) + bars(rows(jump, N), close=300.0)
    entries = [entry("JMP", day(I_H + 20))]
    refused = snapshot(tmp_path, monkeypatch, "u4a", entries, {"JMP.US": history})
    assert resolution_of(refused, "JMP.US") == ["ambiguous_reuse_discontinuity"]
    split = [{"date": day(jump - 2), "split": "3.000000/1.000000"}]
    resolved = snapshot(tmp_path, monkeypatch, "u4b", entries, {"JMP.US": (history, split)})
    assert resolution_of(resolved, "JMP.US") == ["resolved"]
    holdout_split = [{"date": day(20), "split": "3/1"}]
    unaffected = snapshot(tmp_path, monkeypatch, "u4c", entries, {"JMP.US": (history, holdout_split)})
    assert resolution_of(unaffected, "JMP.US") == ["ambiguous_reuse_discontinuity"]


# ---------------------------------------------------------------- T-UNI-5, 6, 7


def test_t_uni_5_round_trip_overlaps_and_exact_repeats(tmp_path, monkeypatch):
    entries = [
        entry("OVR", day(I_H + 20), day(I_H + 300)), entry("OVR", day(I_H + 200)),
        entry("DUP", day(I_H + 20), day(I_H + 300)), entry("DUP", day(I_H + 20), day(I_H + 300)),
        entry("OK", day(I_H + 20)),
    ]
    snap = snapshot(tmp_path, monkeypatch, "u5", entries, {code: bars(FULL) for code in ("OVR.US", "DUP.US", "OK.US")})
    results = interval_rows(snap)
    overlap = results[results["vendor_code"] == "OVR.US"]
    assert overlap["resolution"].tolist() == ["raw_overlap"] * 2
    assert overlap["census_cap"].tolist() == ["R-CENSUS-9"] * 2 and overlap["permanent_id"].tolist() == ["", ""]
    dup = results[results["vendor_code"] == "DUP.US"]
    assert dup["resolution"].tolist() == ["resolved", "exact_duplicate_collapsed"]
    assert dup["duplicate_of"].tolist() == ["", dup["interval_id"].iloc[0]]
    assert dup["member_days_disc"].tolist()[1] == "0" and dup["census_cap"].tolist() == ["none", "none"]
    table = load_constituent_intervals_csv(snap / "membership/constituent_intervals.csv").data
    assert sorted(table["permanent_id"]) == ["DUP.US#E1", "OK.US#E1"]


def test_t_uni_6_holdout_discontinuity_is_not_evaluated_and_not_read(tmp_path, monkeypatch):
    history = bars(rows(0, 100)) + bars(rows(105, N), close=300.0)
    snap = snapshot(tmp_path, monkeypatch, "u6", [entry("HLD", day(I_H + 20))], {"HLD.US": history}, build=False)
    with record_reads(snap) as recorder:
        build_universe(snap)
    assert recorder.forbidden() == []
    assert resolution_of(snap, "HLD.US") == ["resolved"]
    assert build_manifest(snap)["e5_not_evaluated_holdout_rows"] == {"HLD.US": 1}


def test_t_uni_7_open_end_date_variants(tmp_path, monkeypatch):
    entries = [entry("E1", day(I_H + 20), ""), entry("E2", day(I_H + 20), None), entry("E3", day(I_H + 20), "2099-12-31")]
    snap = snapshot(tmp_path, monkeypatch, "u7", entries, {f"{code}.US": bars(FULL) for code in ("E1", "E2", "E3")})
    table = intervals_csv(snap)
    assert table["end_date"].tolist() == ["", "", ""] and table["end_known_at"].tolist() == ["", "", ""]
    data = load_constituent_intervals_csv(snap / "membership/constituent_intervals.csv").data
    assert data["end_date"].isna().all() and data["end_known_at"].isna().all()


# ---------------------------------------------------------------- T-UNI-8 (E6)


def symbol(code, isin=None, name=None):
    return {"Code": code, "Name": name or f"{code} Inc", "Exchange": "NYSE", "Type": "Common Stock", "Isin": isin}


def test_t_uni_8_e6_delisted_and_listed_reuse(tmp_path, monkeypatch):
    cont = {"SIX.US": bars(FULL)}
    entries = [entry("SIX", day(I_H + 20))]
    a = snapshot(tmp_path, monkeypatch, "u8a", entries, cont, listed=[symbol("SIX", "US1")], delisted=[symbol("SIX", "US1")])
    (row,) = master_of(a, "SIX.US")
    assert row["permanent_id"] == "SIX.US#E1" and "E6:isin_continuity" in row["resolution_evidence"]
    b = snapshot(tmp_path, monkeypatch, "u8b", entries, cont, listed=[symbol("SIX", "US1")], delisted=[symbol("SIX")])
    assert resolution_of(b, "SIX.US") == ["ambiguous_reuse_delisted_and_listed_continuous_history"]
    assert "missing_identifier=delisted_isin" in master_of(b, "SIX.US")[0]["resolution_evidence"]
    c = snapshot(tmp_path, monkeypatch, "u8c", entries, cont, listed=[symbol("SIX", "US1")], delisted=[symbol("SIX", "US2")])
    assert resolution_of(c, "SIX.US") == ["ambiguous_reuse_isin_conflict"]
    d = snapshot(tmp_path, monkeypatch, "u8d",
                 [entry("SIX", day(I_H + 20), day(I_H + 200), name="Old Co"), entry("SIX", day(I_H + 200), name="New Co")],
                 cont, listed=[symbol("SIX", "US1")], delisted=[symbol("SIX", "US1")])
    assert set(resolution_of(d, "SIX.US")) == {"ambiguous_reuse_continuous_history"}
    gap = {"SIX.US": bars(rows(I_H + 10, I_H + 150) + rows(I_H + 181, N))}
    e = snapshot(tmp_path, monkeypatch, "u8e",
                 [entry("SIX", day(I_H + 20), day(I_H + 140), name="Old Co"), entry("SIX", day(I_H + 190), name="New Co")],
                 gap, listed=[symbol("SIX", "US1")], delisted=[symbol("SIX", "US2")])
    assert resolution_of(e, "SIX.US") == ["resolved", "resolved"]
    assert [row["permanent_id"] for row in master_of(e, "SIX.US")] == ["SIX.US#E1", "SIX.US#E2"]
    assert "SIX.US" in intervals_csv(e)["symbol"].tolist()


def t_uni_8f_snapshot(tmp_path, monkeypatch, name="u8f"):
    """An old delisted member years before the reused code's only episode, and a current member (MA6-1)."""
    entries = [entry("RUS", day(I_H + 5), day(I_H + 100), name="Old Railroad", delisted=True),
               entry("RUS", day(I_H + 420), name="New Software")]
    return snapshot(tmp_path, monkeypatch, name, entries, {"RUS.US": bars(rows(I_H + 400, N))},
                    listed=[symbol("RUS", "US9", "New Software")], delisted=[symbol("RUS", None, "Old Railroad")])


def test_t_uni_8_f_old_zero_bar_interval_keeps_its_e2_refusal(tmp_path, monkeypatch):
    snap = t_uni_8f_snapshot(tmp_path, monkeypatch)
    old, current = interval_rows(snap).to_dict(orient="records")
    assert old["resolution"] == "no_containing_episode:no_bars_in_interval"
    assert old["eod_status"] == "retrieved" and old["census_cap"] == "R-CENSUS-9"
    assert "E6:ambiguous_reuse_delisted_and_listed_continuous_history" in old["resolution_evidence"]
    assert current["resolution"] == "ambiguous_reuse_delisted_and_listed_continuous_history"
    assert current["census_cap"] == "R-CENSUS-3"
    (row,) = master_of(snap, "RUS.US")
    assert (row["permanent_id"], row["resolution"]) == ("", "ambiguous_reuse_delisted_and_listed_continuous_history")
    assert "RUS.US" not in intervals_csv(snap)["symbol"].tolist()


# ---------------------------------------------------------------- T-UNI-9 (E2)


def test_t_uni_9_containment_outcomes_partition_every_interval(tmp_path, monkeypatch):
    first = I_H + 100
    body = bars(rows(first, N))
    two = bars(rows(I_H + 10, I_H + 150) + rows(I_H + 181, N))
    weekend = [day_row for day_row in pd.date_range(CAL[I_H], CAL[-1]) if day_row.weekday() == 5]
    weekend_bars = [{"date": d.date().isoformat(), "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0,
                     "adjusted_close": 1.0, "volume": 1.0} for d in weekend]
    duplicate = json.dumps(bars([I_H + 10, I_H + 10])).encode()
    entries = [
        entry("DEG", day(first + 10), day(first + 10)),
        entry("P30", day(first - 30), day(first + 50)),
        entry("B30", day(first - 30), day(first - 5)),
        entry("AFT", day(N - 5)),
        entry("GIN", day(I_H + 155), day(I_H + 175)),
        entry("GBO", day(I_H + 100), day(I_H + 200)),
        entry("P10", day(first - 10), day(first + 50)),
        entry("MIS", day(I_H + 20)), entry("SKP", day(I_H + 20)), entry("DUS", day(I_H + 20)), entry("OFF", day(I_H + 20)),
    ]
    codes = {"DEG.US": body, "P30.US": body, "B30.US": body, "AFT.US": bars(rows(I_H, N - 20)),
             "GIN.US": two, "GBO.US": two, "P10.US": body, "MIS.US": 404, "SKP.US": (bars(FULL), 500),
             "DUS.US": duplicate, "OFF.US": weekend_bars}
    snap = snapshot(tmp_path, monkeypatch, "u9", entries, codes)
    got = {row["vendor_code"]: row for row in interval_rows(snap).to_dict(orient="records")}
    assert got["DEG.US"]["resolution"] == "degenerate_interval" and got["DEG.US"]["member_days_disc"] == "0"
    assert got["P30.US"]["resolution"] == "no_containing_episode"
    assert got["B30.US"]["resolution"] == "no_containing_episode:no_bars_in_interval"
    assert got["B30.US"]["eod_status"] == "retrieved"
    assert got["AFT.US"]["resolution"] == "no_containing_episode:no_bars_in_interval"
    assert got["GIN.US"]["resolution"] == "no_containing_episode:no_bars_in_interval"
    assert got["GBO.US"]["resolution"] == "ambiguous_reuse_gap"
    assert got["P10.US"]["resolution"] == "resolved"
    assert got["MIS.US"]["resolution"] == "no_containing_episode:no_vendor_bars:missing_symbol"
    assert got["SKP.US"]["resolution"] == "no_containing_episode:no_vendor_bars:skipped_split_table_provider_error"
    assert got["DUS.US"]["resolution"] == "no_containing_episode:no_vendor_bars:date_structure_duplicate"
    assert got["OFF.US"]["resolution"] == "no_containing_episode:no_vendor_bars:retrieved_no_calendar_bars"
    assert {row["census_cap"] for code, row in got.items() if code in ("P30.US", "GBO.US")} == {"R-CENSUS-3"}
    assert {row["census_cap"] for code, row in got.items()
            if code in ("B30.US", "AFT.US", "GIN.US", "MIS.US", "SKP.US", "DUS.US", "OFF.US")} == {"R-CENSUS-9"}


# ---------------------------------------------------------------- T-UNI-10, 12, 13


def test_t_uni_10_off_calendar_bar_is_counted_and_kept_out_of_the_panel(tmp_path, monkeypatch):
    history = bars(FULL)
    saturday = {**history[I_H + 50], "date": "2004-03-13"}
    holiday = {**history[I_H + 50], "date": "2004-07-05"}
    history = sorted(history + [saturday, holiday], key=lambda row: row["date"])
    snap = snapshot(tmp_path, monkeypatch, "u10", [entry("OFC", day(I_H + 20))], {"OFC.US": history})
    assert build_manifest(snap)["off_calendar_bar_rows"] == {"OFC.US": 2}
    frame = panel(snap, "OFC.US#E1")
    assert pd.DatetimeIndex(frame["date"]).equals(pd.DatetimeIndex(C_DISC, name=None))


BOUNDARY_CASES = {
    "sunday": ("2005-10-30", "2005-10-31"),
    "holiday": ("2006-03-30", "2006-03-31"),
    "trading": ("2006-05-30", "2006-05-30"),
}


@pytest.mark.parametrize("case", sorted(BOUNDARY_CASES))
def test_t_uni_12_interval_boundary_rows_agree_with_the_engine_mask(tmp_path, monkeypatch, case):
    vendor_day, row_day = BOUNDARY_CASES[case]
    row_d = CAL.get_loc(pd.Timestamp(row_day))
    assert row_d == CAL.searchsorted(pd.Timestamp(vendor_day))
    assert (row_d + 1 if case == "trading" else row_d) in RESETS
    entries = [entry("STA", vendor_day), entry("END", day(I_H + 20), vendor_day)]
    snap = snapshot(tmp_path, monkeypatch, f"u12{case}", entries,
                    {"STA.US": bars(FULL), "END.US": bars(rows(I_H, row_d + 1))})
    got = by_id(interval_rows(snap), "vendor_code")
    table = load_constituent_intervals_csv(snap / "membership/constituent_intervals.csv")
    mask = build_pit_membership_mask(table, CAL, ["STA.US#E1", "END.US#E1"], signal_lag_periods=1)
    admitted = np.flatnonzero(mask["STA.US#E1"].to_numpy())
    assert admitted[0] == row_d + 1 and got["STA.US"]["m_in"] == day(row_d + 1)
    held = np.flatnonzero(mask["END.US#E1"].to_numpy())
    assert held[-1] == row_d and got["END.US"]["m_out"] == day(row_d + 1)
    r_entry = next(r for r in RESETS if r >= row_d + 1)
    r_exit = next(r for r in RESETS if r >= row_d + 1)
    assert got["STA.US"]["R_entry"] == day(r_entry) and mask["STA.US#E1"].iloc[r_entry]
    assert got["END.US"]["R_exit"] == day(r_exit) and not mask["END.US#E1"].iloc[r_exit]
    assert got["END.US"]["exit_class"] == "delisting_candidate"
    assert got["STA.US"]["exit_class"] == "index_removal_still_trading"


def test_t_uni_13_panel_bars_equal_the_sidecar_projection_and_master_ignores_holdout_quarantine(tmp_path, monkeypatch):
    gappy = [r for r in rows(0, N) if r % 17 != 5]
    clean = snapshot(tmp_path, monkeypatch, "u13a", [entry("GAP", day(I_H + 20))], {"GAP.US": bars(gappy)})
    history = bars(gappy)
    history[3] = {**history[3], "low": -1.0}
    quarantined = snapshot(tmp_path, monkeypatch, "u13b", [entry("GAP", day(I_H + 20))], {"GAP.US": history})
    manifest = json.loads((quarantined / "manifest.json").read_text())
    assert manifest["entries"]["eod/GAP.US"]["partition_statuses"]["holdout"].startswith("quarantined:")
    frame = panel(clean, "GAP.US#E1")
    expected = [CAL[r] for r in gappy if r >= I_H]
    assert pd.DatetimeIndex(frame.loc[np.isfinite(frame["adjusted_close"]), "date"]).tolist() == expected
    columns = ["permanent_id", "first_bar", "last_bar", "bar_count"]
    assert master_of(clean, "GAP.US")[0]["bar_count"] == str(len(gappy))
    assert [{k: r[k] for k in columns} for r in master_of(clean, "GAP.US")] == \
        [{k: r[k] for k in columns} for r in master_of(quarantined, "GAP.US")]
    assert panel(quarantined, "GAP.US#E1").equals(frame)


# ---------------------------------------------------------------- T-UNI-14 (re-keyed renames)


def rename_snapshot(tmp_path, monkeypatch, name, a_eod, *, b_name="Acme Holdings Inc", hook=None):
    boundary = I_H + 200
    entries = [entry("AAA", day(I_H + 20), day(boundary), name="ACME Holdings Corp."),
               entry("BBB", day(boundary), name=b_name)]
    codes = {"AAA.US": a_eod, "BBB.US": bars(rows(I_H + 5, N))}
    return snapshot(tmp_path, monkeypatch, name, entries, codes, harness_hook=hook), boundary


def test_t_uni_14_rekeyed_rename_candidates(tmp_path, monkeypatch):
    snap, _ = rename_snapshot(tmp_path, monkeypatch, "u14a", json.dumps([]).encode())
    assert resolution_of(snap, "AAA.US") == ["no_containing_episode:rekeyed_rename_candidate"]
    assert resolution_of(snap, "BBB.US") == ["resolved"]
    assert intervals_csv(snap)["symbol"].tolist() == ["BBB.US"]

    kept, boundary = rename_snapshot(tmp_path, monkeypatch, "u14b", bars(rows(I_H + 5, I_H + 200)))
    assert resolution_of(kept, "AAA.US") == ["resolved"] and resolution_of(kept, "BBB.US") == ["resolved"]
    assert by_id(interval_rows(kept), "vendor_code")["AAA.US"]["exit_class"] == "delisting_candidate"

    skipped, _ = rename_snapshot(tmp_path, monkeypatch, "u14c", (json.dumps([]).encode(), 500))
    assert resolution_of(skipped, "AAA.US") == ["no_containing_episode:no_vendor_bars:skipped_split_table_provider_error"]
    failing, _ = rename_snapshot(tmp_path, monkeypatch, "u14d", 500)
    assert resolution_of(failing, "AAA.US") == ["no_containing_episode:no_vendor_bars:provider_error"]

    def three_days(harness):
        harness.retrieve()
        for _ in range(2):
            harness.clock.advance(days=1)
            assert harness.run("eod") == 0

    persistent, _ = rename_snapshot(tmp_path, monkeypatch, "u14e", 500, hook=three_days)
    assert resolution_of(persistent, "AAA.US") == ["no_containing_episode:no_vendor_bars:persistent_provider_error"]

    reused_eod = bars(rows(I_H + 260, N))
    reused, _ = rename_snapshot(tmp_path, monkeypatch, "u14f", reused_eod)
    row = by_id(interval_rows(reused), "vendor_code")["AAA.US"]
    assert row["resolution"] == "no_containing_episode:rekeyed_rename_candidate"
    assert (row["eod_status"], row["bars_in_span"]) == ("retrieved", "0")
    assert f"first_bar={day(I_H + 260)}" in row["resolution_evidence"]
    other, _ = rename_snapshot(tmp_path, monkeypatch, "u14g", reused_eod, b_name="Zenith Inc")
    assert resolution_of(other, "AAA.US") == ["no_containing_episode:no_bars_in_interval"]


# ---------------------------------------------------------------- T-UNI-16 (counting grain and keys)


def repeat_entries(extra=()):
    return [entry("REPEAT", day(I_H + 10), day(I_H + 120)), entry("REPEAT", day(I_H + 240)), *extra]


REPEAT_BARS = {"REPEAT.US": bars(rows(I_H + 5, I_H + 450))}


def test_t_uni_16_a_one_episode_two_intervals_two_classes(tmp_path, monkeypatch):
    snap = snapshot(tmp_path, monkeypatch, "u16a", repeat_entries(), REPEAT_BARS)
    (row,) = master_of(snap, "REPEAT.US")
    assert (row["permanent_id"], row["interval_count"], row["has_delisting_candidate_interval"]) == ("REPEAT.US#E1", "2", "True")
    results = interval_rows(snap)
    assert results["interval_id"].tolist() == [f"REPEAT.US/{day(I_H + 10)}/{day(I_H + 120)}/1", f"REPEAT.US/{day(I_H + 240)}/open/1"]
    assert results["exit_class"].tolist() == ["disappearance_outside_membership", "delisting_candidate"]


def test_t_uni_16_c_exact_repeat_collapses_and_a_renamed_copy_refuses(tmp_path, monkeypatch):
    base = snapshot(tmp_path, monkeypatch, "u16base", repeat_entries(), REPEAT_BARS)
    copy = snapshot(tmp_path, monkeypatch, "u16c", repeat_entries([entry("REPEAT", day(I_H + 240))]), REPEAT_BARS)
    results = interval_rows(copy)
    first, second = f"REPEAT.US/{day(I_H + 240)}/open/1", f"REPEAT.US/{day(I_H + 240)}/open/2"
    got = by_id(results)
    assert got[first]["resolution"] == "resolved" and got[first]["exit_class"] == "delisting_candidate"
    assert (got[second]["resolution"], got[second]["duplicate_of"], got[second]["member_days_disc"],
            got[second]["census_cap"]) == ("exact_duplicate_collapsed", first, "0", "none")
    assert intervals_csv(copy).equals(intervals_csv(base))
    assert build_manifest(copy)["exact_duplicate_entries_collapsed"] == 1
    renamed = snapshot(tmp_path, monkeypatch, "u16d",
                       repeat_entries([entry("REPEAT", day(I_H + 240), name="Different Name Co")]), REPEAT_BARS)
    assert set(resolution_of(renamed, "REPEAT.US")) >= {"ambiguous_reuse_continuous_history"}
    cosmetic = snapshot(tmp_path, monkeypatch, "u16e",
                        repeat_entries([entry("REPEAT", day(I_H + 240), name="repeat, INC.")]), REPEAT_BARS)
    assert intervals_csv(cosmetic).equals(intervals_csv(base))


def test_t_uni_16_d_genuine_overlap_refuses_both_entries(tmp_path, monkeypatch):
    snap = snapshot(tmp_path, monkeypatch, "u16f",
                    repeat_entries([entry("REPEAT", day(I_H + 300), day(I_H + 420))]), REPEAT_BARS)
    assert resolution_of(snap, "REPEAT.US") == ["resolved", "raw_overlap", "raw_overlap"]
    assert intervals_csv(snap)["start_date"].tolist() == [day(I_H + 10)]


def test_t_uni_16_e_interval_keys(tmp_path, monkeypatch):
    start = day(I_H + 10)
    entries = [entry("KEY", start, None), entry("KEY", start, ""), entry("KEY", start, "2099-12-31"),
               entry("CLS", start, "2007-01-02"), entry("CLS", start, None),
               entry("BAD", "2004/01/04"), entry("A/B", start)]
    snap = snapshot(tmp_path, monkeypatch, "u16g", entries, {"KEY.US": bars(FULL), "CLS.US": bars(FULL)})
    results = interval_rows(snap)
    assert results["interval_id"].tolist() == [
        f"KEY.US/{start}/open/1", f"KEY.US/{start}/open/2", f"KEY.US/{start}/2099-12-31/1",
        f"CLS.US/{start}/2007-01-02/1", f"CLS.US/{start}/open/1", "raw_row/5", f"A%2FB.US/{start}/open/1"]
    assert results["resolution"].tolist()[:6] == [
        "resolved", "exact_duplicate_collapsed", "exact_duplicate_collapsed", "raw_overlap", "raw_overlap",
        "entry_unparseable_date"]
    assert all(len(key.split("/")) in (2, 4) for key in results["interval_id"])


def test_name_normalization_v1():
    assert normalize_name("The Acme Holdings, Inc.") == normalize_name("ACME holdings corp") == "acme holdings"
    assert normalize_name("Co-Op Company Ltd") == "co op"
    assert normalize_name(None) == ""


def test_build_refuses_when_a_panel_split_table_exists(tmp_path, monkeypatch):
    snap = snapshot(tmp_path, monkeypatch, "split_table", [entry("AAA", day(I_H + 20))], {"AAA.US": bars(FULL)}, build=False)
    (snap / "panel" / "splits").mkdir(parents=True)
    pd.DataFrame({"date": [CAL[I_H + 30]], "ratio": [2.0]}).to_parquet(snap / "panel" / "splits" / "AAA.US#E1.parquet")
    with pytest.raises(SnapshotRefusal) as refused:
        build_universe(snap)
    assert refused.value.code == "panel_split_table_present"
    assert not (snap / "panel/inventory_discovery.json").exists()


# ---------------------------------------------------------------- T-UNI-15 (corporate-action episode isolation)


EP1 = rows(I_H + 10, I_H + 130)
EP2 = rows(I_H + 170, I_H + 330)
SPLIT = I_H + 250
REUSE_ENTRIES = [entry("REUSE", day(I_H + 15), day(I_H + 100), name="Reuse One"),
                 entry("REUSE", day(I_H + 175), name="Reuse Two"),
                 entry("CTRL", day(I_H + 15), day(I_H + 100), name="Control")]


def split_rows(*pairs):
    return [{"date": day(r), "split": text} for r, text in pairs]


def ep2_bars(ratio=2.0, adjusted=50.0):
    return bars(EP2, close=lambda r: adjusted * ratio if r < SPLIT else adjusted, adjusted=adjusted,
                volume=lambda r: 1000.0 * ratio if r < SPLIT else 1000.0)


def check_of(snap, pid):
    return next(c for c in build_manifest(snap)["episode_checks"] if c["permanent_id"] == pid)


def refusal_of(snap, pid):
    return next(r["episode_panel_refusal"] for r in master_rows(snap).to_dict(orient="records") if r["permanent_id"] == pid)


def evidence_of(snap, pid):
    return next(r["resolution_evidence"] for r in master_rows(snap).to_dict(orient="records") if r["permanent_id"] == pid)


def panel_bytes(snap, pid):
    return (snap / "panel" / "discovery" / f"{pid}.parquet").read_bytes()


def reuse_snapshot(tmp_path, monkeypatch, name, ep1, ep2, splits):
    return snapshot(tmp_path, monkeypatch, name, REUSE_ENTRIES,
                    {"REUSE.US": (ep1 + ep2, splits), "CTRL.US": (bars(EP1), [])})


def test_t_uni_15_a_split_attributed_to_the_later_episode_only(tmp_path, monkeypatch):
    snap = reuse_snapshot(tmp_path, monkeypatch, "u15a", bars(EP1), ep2_bars(), split_rows((SPLIT, "2/1")))
    first, control, second = panel(snap, "REUSE.US#E1"), panel(snap, "CTRL.US#E1"), panel(snap, "REUSE.US#E2")
    assert (first["split_factor"] == 1.0).all() and (turnover(first) == 100_000.0).all()
    for column in ("open", "high", "low", "close", "adjusted_close", "split_factor"):
        np.testing.assert_array_equal(first[column].to_numpy(), control[column].to_numpy())
    np.testing.assert_array_equal(turnover(first), turnover(control))
    loaded = build_adjusted_research_panels(load_panels(snap, ["REUSE.US#E1", "CTRL.US#E1"]))
    amihud = calculate_amihud_illiquidity(loaded["returns"], loaded["dollar_volume"], window=63)
    np.testing.assert_array_equal(amihud["REUSE.US#E1"].to_numpy(), amihud["CTRL.US#E1"].to_numpy())
    before = pd.DatetimeIndex(second["date"]) < CAL[SPLIT]
    assert second.loc[before, "split_factor"].eq(2.0).all() and second.loc[~before, "split_factor"].eq(1.0).all()
    assert (second["close"] / second["split_factor"]).eq(50.0).all()
    np.testing.assert_allclose(turnover(second), second["close"] * 1000.0)
    assert turnover(second)[before].tolist() == [100_000.0] * before.sum()
    assert turnover(second)[~before].tolist() == [50_000.0] * (~before).sum()
    assert_loaded_factor_equals_written(snap)


def test_t_uni_15_b_misstated_ratio_refuses_only_the_later_episode(tmp_path, monkeypatch):
    base = reuse_snapshot(tmp_path, monkeypatch, "u15a", bars(EP1), ep2_bars(), split_rows((SPLIT, "2/1")))
    wrong = reuse_snapshot(tmp_path, monkeypatch, "u15b", bars(EP1), ep2_bars(), split_rows((SPLIT, "3/1")))
    assert panel_bytes(wrong, "REUSE.US#E1") == panel_bytes(base, "REUSE.US#E1")
    assert refusal_of(wrong, "REUSE.US#E2") == "split_basis_unverified:in_span_step_mismatch"
    (pair,) = check_of(wrong, "REUSE.US#E2")["failing_pairs"]
    assert pair["kind"] == "declared_split_pair" and pair["residual"] == pytest.approx(1 / 3)
    assert not (wrong / "panel/discovery/REUSE.US#E2.parquet").exists()
    consistent = reuse_snapshot(tmp_path, monkeypatch, "u15b2", bars(EP1), ep2_bars(ratio=3.0), split_rows((SPLIT, "3/1")))
    second = panel(consistent, "REUSE.US#E2")
    before = pd.DatetimeIndex(second["date"]) < CAL[SPLIT]
    assert second.loc[before, "split_factor"].eq(3.0).all() and second.loc[~before, "split_factor"].eq(1.0).all()
    np.testing.assert_allclose(turnover(second), second["close"] * 1000.0)
    assert panel_bytes(consistent, "REUSE.US#E1") == panel_bytes(base, "REUSE.US#E1")


def test_t_uni_15_c_gap_dated_split_refuses_the_preceding_episode(tmp_path, monkeypatch):
    base = reuse_snapshot(tmp_path, monkeypatch, "u15a", bars(EP1), ep2_bars(), split_rows((SPLIT, "2/1")))
    snap = reuse_snapshot(tmp_path, monkeypatch, "u15c", bars(EP1), bars(EP2, volume=2000.0),
                          split_rows((I_H + 150, "2/1")))
    assert refusal_of(snap, "REUSE.US#E1") == "split_attribution_ambiguous"
    assert build_manifest(snap)["split_rows_unattributed"] == 1
    second = panel(snap, "REUSE.US#E2")
    assert second["split_factor"].eq(1.0).all() and (turnover(second) == 200_000.0).all()
    assert intervals_csv(snap).equals(intervals_csv(base))
    columns = ["permanent_id", "first_bar", "last_bar", "bar_count", "resolution"]
    assert master_rows(snap)[columns].equals(master_rows(base)[columns])


def test_t_uni_15_d_cross_episode_adjustment_and_e_split_before_first_bar(tmp_path, monkeypatch):
    base = reuse_snapshot(tmp_path, monkeypatch, "u15a", bars(EP1), ep2_bars(), split_rows((SPLIT, "2/1")))
    stitched = reuse_snapshot(tmp_path, monkeypatch, "u15d", bars(EP1, adjusted=50.0, volume=2000.0), ep2_bars(),
                              split_rows((SPLIT, "2/1")))
    assert refusal_of(stitched, "REUSE.US#E1") == "cross_episode_adjustment"
    assert panel_bytes(stitched, "REUSE.US#E2") == panel_bytes(base, "REUSE.US#E2")
    early = reuse_snapshot(tmp_path, monkeypatch, "u15e", bars(EP1), ep2_bars(), split_rows((I_H + 3, "2/1"), (SPLIT, "2/1")))
    assert build_manifest(early)["split_rows_before_first_bar"] == {"REUSE.US": 1}
    for pid in ("REUSE.US#E1", "REUSE.US#E2"):
        assert panel_bytes(early, pid) == panel_bytes(base, pid)


LATE = rows(I_H + 40, I_H + 100)
LATE_SPLIT = I_H + 104


def test_t_uni_15_f_post_final_bar_rows_under_each_vendor_convention(tmp_path, monkeypatch):
    variants = {
        "LU": (bars(LATE), "2/1"), "LA": (bars(LATE, adjusted=50.0, volume=2000.0), "2/1"),
        "LB": (bars(LATE, adjusted=80.0), "2/1"), "LC": (bars(LATE, adjusted=50.0, volume=2000.0), "3/1"),
        "LR": (bars(LATE, close=10.0, adjusted=100.0, volume=100.0), "1/10"), "L1": (bars(LATE), "1/1"),
    }
    entries = [entry(code, day(I_H + 40), day(I_H + 140)) for code in variants]
    codes = {f"{code}.US": (history, split_rows((LATE_SPLIT, ratio))) for code, (history, ratio) in variants.items()}
    snap = snapshot(tmp_path, monkeypatch, "u15f", entries, codes)
    unapplied, applied, reverse, one = (panel(snap, f"{c}.US#E1") for c in ("LU", "LA", "LR", "L1"))
    assert unapplied["split_factor"].eq(1.0).all() and (turnover(unapplied) == 100_000.0).all()
    assert applied["split_factor"].eq(2.0).all() and (applied["close"] / applied["split_factor"]).eq(50.0).all()
    assert (turnover(applied) == 100_000.0).all()
    assert reverse["split_factor"].eq(0.1).all()
    np.testing.assert_allclose(reverse["close"] / reverse["split_factor"], 100.0)
    np.testing.assert_allclose(turnover(reverse), 10_000.0)
    assert one["split_factor"].eq(1.0).all()
    assert check_of(snap, "LU.US#E1")["outcome"] == "excluded_unapplied"
    assert check_of(snap, "LA.US#E1")["outcome"] == "attributed_applied"
    assert check_of(snap, "L1.US#E1")["outcome"] == "excluded_unapplied"
    assert refusal_of(snap, "LB.US#E1") == "split_attribution_ambiguous"
    assert refusal_of(snap, "LC.US#E1") == "split_attribution_ambiguous"
    assert build_manifest(snap)["split_rows_after_final_bar"] == {
        "excluded_unapplied": 2, "attributed_applied": 2, "refused": 2, "not_evaluated_no_discovery_bar": 0}
    assert "post_final_bar=attributed_applied" in evidence_of(snap, "LA.US#E1")
    assert_loaded_factor_equals_written(snap)


REUSE2_EP1, REUSE2_EP2 = rows(I_H + 10, I_H + 130), rows(I_H + 170, I_H + 230)


def test_t_uni_15_g_two_and_three_episode_post_final_witnesses(tmp_path, monkeypatch):
    split = split_rows((I_H + 234, "2/1"))
    stitched_bars = bars(REUSE2_EP1 + REUSE2_EP2, adjusted=50.0, volume=2000.0)
    entries = [entry("REU2", day(I_H + 15), day(I_H + 100)), entry("REU2", day(I_H + 175)),
               entry("CTRL", day(I_H + 15), day(I_H + 100))]
    control = {"CTRL.US": (bars(REUSE2_EP1), [])}
    stitched = snapshot(tmp_path, monkeypatch, "u15g1", entries, {"REU2.US": (stitched_bars, split), **control})
    assert check_of(stitched, "REU2.US#E2")["outcome"] == "attributed_applied"
    second = panel(stitched, "REU2.US#E2")
    assert second["split_factor"].eq(2.0).all() and (turnover(second) == 100_000.0).all()
    assert refusal_of(stitched, "REU2.US#E1") == "cross_episode_adjustment"
    assert build_manifest(stitched)["split_basis_check_by_outcome"]["refused"] == 1
    assert by_id(interval_rows(stitched))[f"REU2.US/{day(I_H + 15)}/{day(I_H + 100)}/1"]["permanent_id"] == "REU2.US#E1"

    unstitched = snapshot(tmp_path, monkeypatch, "u15g2", entries, {
        "REU2.US": (bars(REUSE2_EP1) + bars(REUSE2_EP2, adjusted=50.0, volume=2000.0), split), **control})
    first = panel(unstitched, "REU2.US#E1")
    assert first["split_factor"].eq(1.0).all()
    np.testing.assert_array_equal(turnover(first), turnover(panel(unstitched, "CTRL.US#E1")))
    assert panel_bytes(unstitched, "REU2.US#E2") == panel_bytes(stitched, "REU2.US#E2")

    early_entries = [entry("REU2", day(15), day(100)), entry("REU2", day(I_H + 175))]
    early = snapshot(tmp_path, monkeypatch, "u15g3", early_entries,
                     {"REU2.US": (bars(rows(10, 130)) + bars(REUSE2_EP2, adjusted=50.0, volume=2000.0), split)},
                     build=False)
    with record_reads(early) as recorder:
        build_universe(early)
    assert recorder.forbidden() == []
    assert "split_basis:not_evaluated:no_discovery_bar" in evidence_of(early, "REU2.US#E1")
    assert not (early / "panel/discovery/REU2.US#E1.parquet").exists()
    assert panel_bytes(early, "REU2.US#E2") == panel_bytes(stitched, "REU2.US#E2")

    ep3 = rows(I_H + 270, I_H + 330)
    three = [entry("REU3", day(I_H + 15), day(I_H + 100)), entry("REU3", day(I_H + 175), day(I_H + 225)),
             entry("REU3", day(I_H + 275))]
    gap_split = split_rows((I_H + 250, "2/1"))
    stitched3 = snapshot(tmp_path, monkeypatch, "u15g4", three, {
        "REU3.US": (bars(REUSE2_EP1 + REUSE2_EP2, adjusted=50.0, volume=2000.0) + bars(ep3), gap_split)})
    assert refusal_of(stitched3, "REU3.US#E1") == refusal_of(stitched3, "REU3.US#E2") == "cross_episode_adjustment"
    assert panel(stitched3, "REU3.US#E3")["split_factor"].eq(1.0).all()
    unstitched3 = snapshot(tmp_path, monkeypatch, "u15g5", three, {
        "REU3.US": (bars(REUSE2_EP1 + REUSE2_EP2 + ep3), gap_split)})
    assert refusal_of(unstitched3, "REU3.US#E1") == ""
    assert check_of(unstitched3, "REU3.US#E2")["split_basis"] == "unapplied"
    assert refusal_of(unstitched3, "REU3.US#E2") == "split_attribution_ambiguous"
    assert build_manifest(unstitched3)["split_rows_unattributed"] == 1
    assert panel(unstitched3, "REU3.US#E3")["split_factor"].eq(1.0).all()


def grow(r, start):
    return 100.0 * math.exp(0.001 * (r - start))


def test_t_uni_15_h_detected_deviation_without_a_later_split_row(tmp_path, monkeypatch):
    start = REUSE2_EP1[0]
    omitted = bars(REUSE2_EP1, close=lambda r: grow(r, start), adjusted=lambda r: grow(r, start) / 2, volume=2000.0)
    single = bars(LATE, close=lambda r: grow(r, LATE[0]), adjusted=lambda r: grow(r, LATE[0]) / 2, volume=2000.0)
    ep2_start = REUSE2_EP2[0]
    div_rows = [ep2_start + k for k in (10, 20, 30, 40)]
    ep2_close = {r: grow(r, ep2_start) for r in REUSE2_EP2}
    deltas = {r: 1.0 - 1.0 / ep2_close[r - 1] for r in div_rows}

    def carried(r):
        return float(np.prod([deltas[d] for d in div_rows if d > r]))

    carried_ep1 = bars(REUSE2_EP1, adjusted=lambda r: 100.0 * carried(r))
    ep2_div = bars(REUSE2_EP2, close=lambda r: ep2_close[r], adjusted=lambda r: ep2_close[r] * carried(r))
    dividends = [{"date": day(r), "value": 1.0, "unadjustedValue": 1.0} for r in div_rows]
    entries = [entry("OMIT", day(I_H + 15), day(I_H + 100)), entry("OMIT", day(I_H + 175)),
               entry("OMI1", day(I_H + 45), day(I_H + 90)),
               entry("CARB", day(I_H + 15), day(I_H + 100)), entry("CARB", day(I_H + 175))]
    snap = snapshot(tmp_path, monkeypatch, "u15h", entries, {
        "OMIT.US": (omitted + bars(REUSE2_EP2), []), "OMI1.US": (single, []),
        "CARB.US": (carried_ep1 + ep2_div, [], dividends)})
    assert refusal_of(snap, "OMIT.US#E1") == "split_basis_unverified:unexplained_deviation"
    assert refusal_of(snap, "OMI1.US#E1") == "split_basis_unverified:unexplained_deviation"
    assert by_id(interval_rows(snap))[f"OMIT.US/{day(I_H + 15)}/{day(I_H + 100)}/1"]["permanent_id"] == "OMIT.US#E1"
    assert refusal_of(snap, "CARB.US#E1") == "split_basis_unverified:unexplained_deviation"
    assert check_of(snap, "CARB.US#E1")["later_distribution"] is True
    assert build_manifest(snap)["split_basis_refusals_with_later_distribution"] == 1
    carb2 = panel(snap, "CARB.US#E2")
    np.testing.assert_allclose(turnover(carb2), carb2["close"] * 1000.0)
    assert "in_span_steps:passed" in evidence_of(snap, "CARB.US#E2")


CANCEL_SPLIT, CANCEL_DIV = I_H + 200, I_H + 201


def cancel_ep2(dividend=True):
    def close(r):
        if r < CANCEL_SPLIT:
            return 100.0
        return 200.0 if (r == CANCEL_SPLIT or not dividend) else 100.0
    adjusted = 100.0 if dividend else 200.0
    return bars(REUSE2_EP2, close=close, adjusted=adjusted, volume=lambda r: 500.0 if r < CANCEL_SPLIT else 1000.0)


def test_t_uni_15_i_reverse_split_and_dividend_cancellation(tmp_path, monkeypatch):
    split = split_rows((CANCEL_SPLIT, "1/2"))
    div = [{"date": day(CANCEL_DIV), "value": 100.0, "unadjustedValue": 100.0}]
    div90 = [{"date": day(CANCEL_DIV), "value": 90.0, "unadjustedValue": 90.0}]
    codes = {
        "CAN.US": (bars(REUSE2_EP1, volume=500.0) + cancel_ep2(), split, div),
        "CAN5.US": (bars(REUSE2_EP1, adjusted=100.0 * (1 + 5e-7), volume=500.0) + cancel_ep2(), split, div),
        "CAN2.US": (bars(REUSE2_EP1, adjusted=100.0 * (1 + 2e-6), volume=500.0) + cancel_ep2(), split, div),
        "CAN9.US": (bars(REUSE2_EP1, volume=500.0) + cancel_ep2(), split, div90),
        "CANC.US": (bars(REUSE2_EP1) + cancel_ep2(dividend=False), split, []),
        "POST.US": (bars(REUSE2_EP1, volume=500.0), split_rows((I_H + 135, "1/2")),
                    [{"date": day(I_H + 136), "value": 100.0, "unadjustedValue": 100.0}]),
        "LATX.US": (bars(LATE, adjusted=50.0, volume=2000.0), split_rows((LATE_SPLIT, "2/1")), 404),
    }
    entries = [e for code in ("CAN", "CAN5", "CAN2", "CAN9", "CANC")
               for e in (entry(code, day(I_H + 15), day(I_H + 100)), entry(code, day(I_H + 175)))]
    entries += [entry("POST", day(I_H + 15), day(I_H + 100)), entry("LATX", day(I_H + 45), day(I_H + 90))]
    snap = snapshot(tmp_path, monkeypatch, "u15i", entries, codes)
    assert refusal_of(snap, "CAN.US#E1") == "split_basis_unverified:explanations_disagree"
    second = panel(snap, "CAN.US#E2")
    before = pd.DatetimeIndex(second["date"]) < CAL[CANCEL_SPLIT]
    assert second.loc[before, "split_factor"].eq(0.5).all() and second.loc[~before, "split_factor"].eq(1.0).all()
    raw_volume = 1000.0
    np.testing.assert_allclose(turnover(second), second["close"] * raw_volume)
    assert refusal_of(snap, "CAN5.US#E1") == "split_basis_unverified:explanations_disagree"
    assert refusal_of(snap, "CAN2.US#E1") == "split_basis_unverified:unexplained_deviation"
    assert refusal_of(snap, "CAN9.US#E1") == "split_basis_unverified:explanations_disagree"
    assert refusal_of(snap, "CAN9.US#E2") == "split_basis_unverified:in_span_step_mismatch"
    (pair,) = check_of(snap, "CAN9.US#E2")["failing_pairs"]
    assert pair["kind"] == "declared_dividend_pair" and pair["residual"] == pytest.approx(0.1)
    clean = panel(snap, "CANC.US#E1")
    assert clean["split_factor"].eq(1.0).all() and (turnover(clean) == 100_000.0).all()
    assert refusal_of(snap, "POST.US#E1") == "split_attribution_ambiguous"
    assert refusal_of(snap, "LATX.US#E1") == "split_attribution_ambiguous"
    assert_loaded_factor_equals_written(snap)


# ---------------------------------------------------------------- T-UNI-17 (in-span, cumulative, last-bar support)


def single(code, start, close, adjusted, volume, *, dates=CAL, skip=()):
    """One episode of ``len(close)`` bars from ``start``; arrays are indexed by bar position ``t``."""
    kept = [t for t in range(len(close)) if t not in skip]
    rows_ = [start + t for t in kept]
    return bars(rows_, close=lambda r: close[r - start], adjusted=lambda r: adjusted[r - start],
                volume=lambda r: volume[r - start], dates=dates)


def exp_close(n):
    return 100.0 * np.exp(0.001 * np.arange(n))


START = I_H + 10


def members(codes, dates=CAL, start=START):
    return [entry(code, dates[start + 5].date().isoformat()) for code in codes]


def test_t_uni_17_a_undeclared_splits_at_every_size(tmp_path, monkeypatch):
    ratios = {"S10": 1.1, "SR1": 1 / 1.1, "S15": 1.15, "S17": 1.17, "S18": 1.18, "S01": 1.01, "S11": 1.0011, "S09": 1.0009}
    t = np.arange(160)
    codes = {}
    for code, s in ratios.items():
        base = exp_close(160)
        codes[f"{code}.US"] = (single(code, START, np.where(t < 80, base, base / s), base / s,
                                      np.where(t < 80, 1000.0 * s, 1000.0)), [])
    snap = snapshot(tmp_path, monkeypatch, "u17a", members(ratios), codes)
    manifest = json.loads((snap / "manifest.json").read_text())
    for code, s in ratios.items():
        pid = f"{code}.US#E1"
        if code == "S18":
            assert manifest["entries"]["eod/S18.US"]["partition_statuses"]["discovery"] == "quarantined:unverified_split"
            continue
        assert manifest["entries"][f"eod/{code}.US"]["partition_statuses"]["discovery"] == "valid"
        if code == "S09":
            frame = panel(snap, pid)
            ratio = turnover(frame) / (frame["close"] * 1000.0)
            np.testing.assert_allclose(ratio.to_numpy()[:80], 1.0009)
            np.testing.assert_allclose(ratio.to_numpy()[80:], 1.0)
            assert check_of(snap, pid)["max_cumulative_drift"] == pytest.approx(math.log(1.0009), abs=1e-12)
            continue
        assert refusal_of(snap, pid) == "split_basis_unverified:in_span_step_mismatch"
        (pair,) = check_of(snap, pid)["failing_pairs"]
        assert pair["kind"] == "undeclared_step" and pair["residual"] == pytest.approx(abs(s - 1))
        assert "in_span_steps:mismatch:pairs=159" in evidence_of(snap, pid)


def test_t_uni_17_b_declared_split_contradictions_and_share_basis(tmp_path, monkeypatch):
    t = np.arange(120)
    base = exp_close(120)
    half = np.where(t < 60, base, base / 2)
    ones = np.full(120, 1000.0)
    vol2 = np.where(t < 60, 2000.0, 1000.0)
    amount = 0.01 * base[59] / 2
    same_date_adj = np.where(t < 60, half * 0.99 / 2, half)
    codes = {
        "CA.US": (single("CA", START, base, base, ones), split_rows((START + 60, "2/1"))),
        "CB.US": (single("CB", START, half, base / 2, vol2), split_rows((START + 60, "3/2"))),
        "CC.US": (single("CC", START, half, base / 2, vol2), split_rows((START + 63, "2/1"))),
        "CD.US": (single("CD", START, half, base / 2, vol2), split_rows((START + 60, "2/1"))),
        "CE.US": (single("CE", START, half, same_date_adj, vol2), split_rows((START + 60, "2/1")),
                  [{"date": day(START + 60), "value": amount, "unadjustedValue": amount}]),
    }
    u = np.arange(160)
    flat = np.full(160, 100.0)

    def share_case(code, after_close, adjusted, volume, ratio, dividends, skip=()):
        close = np.where(u < 80, flat, after_close)
        codes[f"{code}.US"] = (single(code, START, close, np.full(160, adjusted), volume, skip=skip),
                               split_rows((START + 80 if not skip else START + 83, ratio)), dividends)

    div1 = [{"date": day(START + 80), "value": 1.0, "unadjustedValue": 1.0}]
    share_case("SA", 49.0, 49.0, np.where(u < 80, 2000.0, 1000.0), "2/1", div1)
    share_case("SB", 49.5, 49.5, np.where(u < 80, 1000.0 * 200 / 101, 1000.0), "2/1", div1)
    share_case("SC", 49.0, 49.0, np.where(u < 80, 2000.0, 1000.0), "2/1",
               [{"date": day(START + 80), "value": 2.0, "unadjustedValue": 2.0}])
    share_case("SD", 199.0, 199.0, np.where(u < 80, 500.0, 1000.0), "1/2", div1)
    spanning = [{"date": day(START + 81), "value": 1.0, "unadjustedValue": 1.0},
                {"date": day(START + 84), "value": 0.5, "unadjustedValue": 0.5}]
    share_case("SE", 49.0, 49.0, np.where(u < 80, 2000.0, 1000.0), "2/1", spanning, skip=range(80, 85))
    snap = snapshot(tmp_path, monkeypatch, "u17b", members([c[:-3] for c in codes]), codes)
    for pid, kinds, residual in (("CA.US#E1", ["declared_split_pair"], 0.5), ("CB.US#E1", ["declared_split_pair"], 1 / 3),
                                 ("CC.US#E1", ["undeclared_step", "declared_split_pair"], None),
                                 ("SB.US#E1", ["declared_split_pair"], 0.0101),
                                 ("SC.US#E1", ["declared_split_pair"], 0.0204)):
        pairs = check_of(snap, pid)["failing_pairs"]
        assert [p["kind"] for p in pairs] == kinds
        if residual is not None:
            assert pairs[0]["residual"] == pytest.approx(residual, abs=5e-5)
    for pid in ("CD.US#E1", "CE.US#E1", "SA.US#E1", "SD.US#E1", "SE.US#E1"):
        frame = panel(snap, pid)
        raw_volume = 1000.0
        np.testing.assert_allclose(turnover(frame), frame["close"] * raw_volume, rtol=1e-12)
    assert check_of(snap, "SE.US#E1")["pairs"] == 154
    assert check_of(snap, "SA.US#E1")["max_cumulative_drift"] < 1e-12
    assert check_of(snap, "SE.US#E1")["max_cumulative_drift"] < 1e-12


def test_t_uni_17_c_distributions_by_formula_and_evidence(tmp_path, monkeypatch):
    t = np.arange(160)
    base = exp_close(160)
    ones = np.full(160, 1000.0)
    amount = 0.02 * base[79]
    div = [{"date": day(START + 80), "value": amount, "unadjustedValue": amount}]
    prior = np.where(t < 80, base * 0.98, base)
    exdate = np.where(t < 80, base * (1 - 0.02 / 0.98), base)
    codes = {
        "DP.US": (single("DP", START, base, prior, ones), [], div),
        "DX.US": (single("DX", START, base, exdate, ones), [], div),
        "DN.US": (single("DN", START, base, base, ones), [], div),
        "DR.US": (single("DR", START, base, base, np.where(t < 80, 980.0, 1000.0)), [], div),
        "DU.US": (single("DU", START, base, prior, ones), [], 404),
    }
    snap = snapshot(tmp_path, monkeypatch, "u17c", members([c[:-3] for c in codes]), codes)
    np.testing.assert_allclose(turnover(panel(snap, "DP.US#E1")), panel(snap, "DP.US#E1")["close"] * 1000.0)
    assert check_of(snap, "DX.US#E1")["refusal"] is None
    assert "in_span_steps:passed" in evidence_of(snap, "DX.US#E1")
    residual = abs((1.0 / (1 - 0.02 / 0.98)) * 0.98 - 1.0)
    assert residual == pytest.approx(4.2e-4, abs=1e-5)
    assert check_of(snap, "DX.US#E1")["max_cumulative_drift"] == pytest.approx(math.log(1 + residual), rel=1e-6)
    for pid in ("DN.US#E1", "DR.US#E1"):
        assert [p["kind"] for p in check_of(snap, pid)["failing_pairs"]] == ["declared_dividend_pair"]
    assert [p["kind"] for p in check_of(snap, "DU.US#E1")["failing_pairs"]] == ["undeclared_step"]
    assert check_of(snap, "DU.US#E1")["dividend_evidence"] is False


def test_t_uni_17_d_amount_basis_is_unadjusted_value(tmp_path, monkeypatch):
    t = np.arange(120)
    base = exp_close(120)
    close = np.where(t < 80, base, base / 2)
    adjusted = np.where(t < 30, close * 0.98 / 2, np.where(t < 80, close / 2, close))
    volume = np.where(t < 80, 2000.0, 1000.0)
    amount = 0.02 * base[29]
    split = split_rows((START + 80, "2/1"))
    nosplit_adj = np.where(t < 30, base * 0.98, base)
    same_day_close = np.where(t < 30, base, base / 2)
    codes = {
        "AU.US": (single("AU", START, close, adjusted, volume), split,
                  [{"date": day(START + 30), "value": amount / 2, "unadjustedValue": amount}]),
        "AV.US": (single("AV", START, close, adjusted, volume), split, [{"date": day(START + 30), "value": amount / 2}]),
        "AW.US": (single("AW", START, base, nosplit_adj, np.full(120, 1000.0)), [],
                  [{"date": day(START + 30), "value": amount}]),
        "AX.US": (single("AX", START, same_day_close, np.where(t < 30, same_day_close * 0.98 / 2, same_day_close),
                         np.where(t < 30, 2000.0, 1000.0)),
                  split_rows((START + 30, "2/1")), [{"date": day(START + 30), "value": amount}]),
    }
    snap = snapshot(tmp_path, monkeypatch, "u17d", members([c[:-3] for c in codes]), codes)
    frame = panel(snap, "AU.US#E1")
    np.testing.assert_allclose(turnover(frame), np.where(t < 80, base, base / 2) * 1000.0, rtol=1e-12)
    assert refusal_of(snap, "AV.US#E1") == "split_basis_unverified:in_span_step_mismatch"
    assert refusal_of(snap, "AW.US#E1") == ""
    assert refusal_of(snap, "AX.US#E1") == "split_basis_unverified:in_span_step_mismatch"
    assert build_manifest(snap)["dividend_rows_amount_undefined"] == 2


def rounding_series(level, n=500):
    t = np.arange(n)
    close = np.round(level * (1 + 0.1 * np.sin(t / 9.0)) * np.exp(0.0002 * t), 4)
    dividend_rows = list(range(60, 481, 60))
    factor = np.ones(n)
    dividends = []
    for d in dividend_rows:
        amount = 0.01 * close[d - 1]
        factor[:d] *= 1 - amount / close[d - 1]
        dividends.append((d, amount))
    return close, np.round(close * factor, 4), dividends


def test_t_uni_17_e_four_decimal_rounding_by_adjusted_level(tmp_path, monkeypatch):
    codes = {}
    for code, level in (("R91", 91.0), ("R09", 0.91), ("R18", 0.18), ("R04", 0.046)):
        close, adjusted, dividends = rounding_series(level)
        codes[f"{code}.US"] = (single(code, START, close, adjusted, np.full(500, 1000.0)), [],
                               [{"date": day(START + d), "value": a, "unadjustedValue": a} for d, a in dividends])
    snap = snapshot(tmp_path, monkeypatch, "u17e", members([c[:-3] for c in codes]), codes)
    for pid in ("R91.US#E1", "R09.US#E1", "R18.US#E1"):
        check = check_of(snap, pid)
        assert check["refusal"] is None and check["max_cumulative_drift"] < 2e-3
    assert check_of(snap, "R91.US#E1")["max_cumulative_drift"] < 1e-5
    failing = check_of(snap, "R04.US#E1")
    assert failing["refusal"] == "split_basis_unverified:in_span_step_mismatch"
    assert failing["failing_pairs"] and all(1e-3 < p["residual"] <= 1e-2 for p in failing["failing_pairs"])
    assert failing["min_adjusted_close"] < 0.1


def test_t_uni_17_f_last_bar_later_distribution_witnesses(tmp_path, monkeypatch):
    div_row = REUSE2_EP2[0] + 30
    amount = 100.0 * (1 - 1 / 1.05)
    ep2 = bars(REUSE2_EP2, adjusted=lambda r: 100.0 / 1.05 if r < div_row else 100.0)
    div = [{"date": day(div_row), "value": amount, "unadjustedValue": amount}]
    codes = {
        "WIT.US": (bars(REUSE2_EP1, adjusted=100.0 / 1.05, volume=1050.0) + ep2, [], div),
        "TWN.US": (bars(REUSE2_EP1, adjusted=100.0 / 1.05) + ep2, [], div),
    }
    entries = [e for code in ("WIT", "TWN") for e in (entry(code, day(I_H + 15), day(I_H + 100)), entry(code, day(I_H + 175)))]
    snap = snapshot(tmp_path, monkeypatch, "u17f", entries, codes)
    for code in ("WIT", "TWN"):
        assert refusal_of(snap, f"{code}.US#E1") == "split_basis_unverified:unexplained_deviation"
        frame = panel(snap, f"{code}.US#E2")
        np.testing.assert_allclose(turnover(frame), frame["close"] * 1000.0)
    assert build_manifest(snap)["split_basis_refusals_with_later_distribution"] == 2


LONG = pd.bdate_range("2003-06-02", "2016-12-30", name="date")
LONG_I_H = int(LONG.searchsorted(pd.Timestamp("2003-12-31")))


def long_snapshot(tmp_path, monkeypatch, name, entries, codes):
    from m4_7_snapshot_support import Vendor

    harness = Harness(tmp_path, monkeypatch, snapshot_id=name, vendor=Vendor(calendar=LONG))
    vendor = harness.vendor
    vendor.entries = entries
    vendor.code("SPY.US", bars(range(len(LONG)), dates=LONG))
    for code, spec in codes.items():
        vendor.code(code, *spec)
    harness.retrieve()
    build_universe(harness.snapshot_dir)
    return harness.snapshot_dir


def test_t_uni_17_g_vp2_witness_twin_and_accumulated_exposure(tmp_path, monkeypatch):
    t = np.arange(160)
    base = exp_close(160)
    amount = 0.02 * base[79]
    served_volume = np.where(t < 80, 1000.0 / 0.98, 1000.0)
    codes = {"VPW.US": (single("VPW", START, base, np.where(t < 80, base * 0.98, base), served_volume), [],
                        [{"date": day(START + 80), "value": amount, "unadjustedValue": amount}])}
    snap = snapshot(tmp_path, monkeypatch, "u17g", members(["VPW"]), codes)
    assert "distribution_support:max_b_d=0.020203:max_s_d=0.020203" in evidence_of(snap, "VPW.US#E1")
    frame = panel(snap, "VPW.US#E1")
    support = pd.read_parquet(snap / "identity/distribution_support.parquet")
    s_d = support[support["permanent_id"] == "VPW.US#E1"]["s_d"].to_numpy()
    witness_raw = frame["close"].to_numpy() * 1000.0
    twin_raw = frame["close"].to_numpy() * frame["volume"].to_numpy()
    np.testing.assert_allclose(turnover(frame), twin_raw)
    np.testing.assert_allclose((turnover(frame) / witness_raw)[:80], 1.0 / 0.98)
    np.testing.assert_allclose(np.log(turnover(frame) / witness_raw), s_d, atol=1e-12)

    n = 2520
    div_positions = list(range(40, 40 + 63 * 40, 63))
    factor = np.ones(n)
    for d in div_positions:
        factor[:d] *= 1 - 0.0075
    close = np.full(n, 100.0)
    start = LONG_I_H + 10
    long_codes = {"ACC.US": (single("ACC", start, close, close * factor, 1000.0 / factor, dates=LONG), [],
                             [{"date": LONG[start + d].date().isoformat(), "value": 0.75, "unadjustedValue": 0.75}
                              for d in div_positions])}
    long = long_snapshot(tmp_path, monkeypatch, "u17g2", members(["ACC"], LONG, start), long_codes)
    check = check_of(long, "ACC.US#E1")
    assert check["refusal"] is None
    assert check["max_s_d"] == pytest.approx(40 * -math.log(0.9925), abs=1e-12)
    assert round(check["max_s_d"], 4) == 0.3011 and round(check["max_b_d"], 6) == 0.007528
    frame = panel(long, "ACC.US#E1")
    support = pd.read_parquet(long / "identity/distribution_support.parquet")
    np.testing.assert_allclose(np.log(turnover(frame) / (frame["close"] * 1000.0)), support["s_d"].to_numpy(), atol=1e-12)


def test_t_uni_17_h_cumulative_drift(tmp_path, monkeypatch):
    t = np.arange(160)
    flat = np.full(160, 100.0)

    def served(q):
        return flat, flat / q, 1000.0 * q

    step = 1.0009
    shape = {
        "CF.US": step ** (159 - t), "CR.US": step ** -(159 - t),
        "C3.US": step ** (3 - np.searchsorted([40, 80, 120], t, side="right")),
        "C1.US": step ** (1 - np.searchsorted([80], t, side="right")),
        "C2.US": step ** (2 - np.searchsorted([40, 80], t, side="right")),
    }
    codes = {code: (single(code[:-3], START, *served(q)), []) for code, q in shape.items()}
    u = np.arange(159)
    up_down = step ** -(79 - np.abs(u - 79))
    codes["CU.US"] = (single("CU", START, flat[:159], flat[:159] / up_down, 1000.0 * up_down), [])
    snap = snapshot(tmp_path, monkeypatch, "u17h", members([c[:-3] for c in codes]), codes)
    for pid, drift in (("CF.US#E1", 0.143036), ("CR.US#E1", 0.143036), ("CU.US#E1", 0.071068), ("C3.US#E1", 0.002699)):
        check = check_of(snap, pid)
        assert check["refusal"] == "split_basis_unverified:cumulative_basis_drift"
        assert check["max_cumulative_drift"] == pytest.approx(drift, abs=5e-7)
        assert "in_span_steps:cumulative_drift" in evidence_of(snap, pid)
    assert check_of(snap, "CF.US#E1")["failing_pairs"] == []
    assert step ** 159 == pytest.approx(1.153771, abs=1e-6)
    for pid, drift in (("C1.US#E1", 0.000900), ("C2.US#E1", 0.001799)):
        frame = panel(snap, pid)
        assert np.max(np.abs(np.log(turnover(frame) / (frame["close"] * 1000.0)))) == pytest.approx(drift, abs=5e-7)

    n = 48 * 63 + 40
    div_positions = list(range(40, n, 63))[:48]
    close = np.full(n, 100.0)
    start = LONG_I_H + 10
    long_codes = {}
    for index in range(3):
        for label, per_event in (("P", 1 - 0.01), ("X", 1 - 0.01 / 0.99)):
            factor = np.ones(n)
            for d in div_positions:
                factor[:d] *= per_event
            code = f"Q{label}{index}"
            long_codes[f"{code}.US"] = (single(code, start, close, close * factor, np.full(n, 1000.0), dates=LONG), [],
                                        [{"date": LONG[start + d].date().isoformat(), "value": 1.0, "unadjustedValue": 1.0}
                                         for d in div_positions])
    long = long_snapshot(tmp_path, monkeypatch, "u17h2", members([c[:-3] for c in long_codes], LONG, start), long_codes)
    for index in range(3):
        frame = panel(long, f"QP{index}.US#E1")
        np.testing.assert_allclose(turnover(frame), frame["close"] * 1000.0)
        check = check_of(long, f"QX{index}.US#E1")
        assert check["refusal"] == "split_basis_unverified:cumulative_basis_drift"
        assert check["max_cumulative_drift"] == pytest.approx(4.90e-3, abs=5e-5)


def test_t_uni_12_round_trip_oracle_refuses_a_shifted_boundary_rule(tmp_path, monkeypatch):
    """Ablation witness: step 5's M4.4 round trip catches a boundary rule one row off (calendar_row_semantics_v1)."""
    import research.m4_7_universe_build as universe

    snap = snapshot(tmp_path, monkeypatch, "oracle", [entry("AAA", day(I_H + 20), day(I_H + 200))],
                    {"AAA.US": bars(FULL)}, build=False)
    monkeypatch.setattr(universe, "_row", lambda calendar, value: int(calendar.searchsorted(pd.Timestamp(value), side="right")))
    with pytest.raises(SnapshotRefusal) as refused:
        build_universe(snap)
    assert refused.value.code == "interval_boundary_mismatch"
