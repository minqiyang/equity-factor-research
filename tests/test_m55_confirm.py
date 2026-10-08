"""Synthetic tests for the confirm and check stages of the Milestone 5.5 driver (card m55-confirm).

The long world is the small world of ``test_m55_driver`` with 900013 as a new listing in 1970 (the calibration
coverage stop, so test B is stopped), on a calendar to 2025-12-31 with no row from 2019-07-31 to 2020-07-31. It adds
SPY, members with events after 1992, Compustat quarters from 2010, a listing after the seal, and a synthetic quote
table and quote manifest. Its chain runs from the coverage counts to the check stage. No test reads the WRDS folder
or opens a network connection.
"""

from __future__ import annotations

import json
import math
import shutil
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import research.m55_driver as d
import research.m55_wrds_loader as w
from m55_bytes_support import BASE_COMMIT, module_at
from research import m55_criteria as crit
from research import m55_index_tilt as tilt
from research import m55_signals as sig
from research.m4_7_sp500_pit_rerun import RunnerStop
from test_m55_driver import (OPEN, TRACKED, VINTAGE, Member, make_data, member_rows, month_end, perturb_after,
                             rechain, row, set_calibration, small_members, sparse_calendar, stage, to_arrow,
                             world_frames)


pytestmark = pytest.mark.xdist_group("m55_confirm")

SPY_PERMNO = 900099


def long_calendar() -> pd.DatetimeIndex:
    """The small-world calendar to 2025-12-31 without the seal rows (2019-07-31 to 2020-07-31, both included), and
    every business day from 2020-08-03 to 2021-08-31 (the post-seal 252-row windows fill by 2021-08-31)."""
    cal = sparse_calendar("1961-01-03", "1963-06-28", "2025-12-31")
    cal = cal[(cal < sig.SEAL[0]) | (cal > sig.SEAL[1])]
    return cal.union(pd.bdate_range("2020-08-03", "2021-08-31")).rename("date")


LONG_CAL = long_calendar()


def long_members(cal: pd.DatetimeIndex) -> list[Member]:
    """The coverage-stop members, and members whose events fall in the confirm and check segments."""
    r = lambda date: row(cal, date)            # noqa: E731
    base = [replace(m, listed=r("1970-02-01"), facts_from=r("1970-02-01"), spell=None) if m.permno == 900013 else m
            for m in small_members(cal)]
    later = [
        Member(900019, 0.05, spell=(r("1994-03-01"), OPEN), last=r("2004-06-15"), delist=("MER", "UNAV", "CASH"),
               y_return=0.15),                                                      # cash merger in the confirm
        Member(900020, 0.03, spell=(r("1995-03-01"), OPEN), last=month_end(cal, "2009-05"),
               delist=("GDR", "BKPY", "UNAV")),                                     # failure with no return
        Member(900021, 0.07, spell=(r("1996-03-01"), OPEN), gp=month_end(cal, "2011-06")),   # a confirm path break
        Member(900022, 0.02, spell=(r("1997-03-01"), OPEN), split=r("2016-04-29")),   # between rdq and known date
        Member(900023, 0.06, spell=(r("2021-01-04"), OPEN), last=r("2024-04-15"), delist=("GLI", "UNAV", "PRCF"),
               y_return=-1.0),                                                      # joins after the seal
        Member(900024, -0.02, spell=(r("2018-03-01"), OPEN)),                       # held across the seal
        Member(900025, 0.04, listed=pd.Timestamp("2020-08-03"), facts_from=pd.Timestamp("2020-03-02"),
               spell=(r("2021-01-04"), OPEN)),                                      # first share fact in the seal
    ]
    return base + [replace(m, beta=1.8 if m.permno % 2 == 0 else 0.3) for m in later]


def spy_frames(frames: dict[str, pd.DataFrame], cal: pd.DatetimeIndex) -> dict[str, pd.DataFrame]:
    """Add SPY: daily rows from 1993-01-15 (first return 1993-01-29), the ticker row, and no index spell."""
    out = dict(frames)
    rows = member_rows(Member(SPY_PERMNO, 0.0, listed=row(cal, "1993-01-15"), drift=0.0004, vol=0.009), cal,
                       np.random.default_rng(99), pd.Series(0.0, index=cal))
    out["crsp_dsf_v2"] = pd.concat([frames["crsp_dsf_v2"], rows], ignore_index=True)
    out["crsp_stksecurityinfohist"] = pd.concat([frames["crsp_stksecurityinfohist"], pd.DataFrame(
        {"permno": [SPY_PERMNO], "ticker": ["SPY"], "secinfostartdt": [pd.Timestamp("1993-01-01")],
         "secinfoenddt": [OPEN]})], ignore_index=True)
    return out


def long_world_frames(cal: pd.DatetimeIndex) -> dict[str, pd.DataFrame]:
    """The long world. Compustat quarters from 2010 for 900001, 900002, and 900022 give S2 values in the confirm and
    the check; the quarter of 2020-06-30 has rdq before 2020-08-03 and its known date after it. 900025 has no 2021
    share fact, so its seal-window fact (basis_unseen seal) is read after the post-seal anchor."""
    frames = spy_frames(world_frames(long_members(cal), cal), cal)
    rng = np.random.default_rng(13)
    quarters = pd.date_range("2010-03-31", "2025-06-30", freq="QE")
    comp = (900001, 900002, 900022)
    fundq = pd.DataFrame([{"gvkey": f"G{p}", "datadate": q, "fyearq": q.year, "ajexq": 1.0}
                          for p in comp for q in quarters])
    urq = pd.DataFrame([{"gvkey": f"G{p}", "datadate": q, "fqtr": float(q.quarter), "rdq": q + pd.Timedelta(days=25),
                         "prelimqprd": q + pd.Timedelta(days=30), "finalqprd": q + pd.Timedelta(days=60),
                         "epspxq": 1.0 + 0.1 * rng.standard_normal(), "ajexq": 1.0} for p in comp for q in quarters])
    urq.loc[urq["datadate"] == pd.Timestamp("2020-06-30"), "prelimqprd"] = pd.Timestamp("2020-08-05")
    frames["comp_fundq"] = pd.concat([frames["comp_fundq"], fundq], ignore_index=True)
    frames["comp_urq"] = pd.concat([frames["comp_urq"], urq], ignore_index=True)
    facts = frames["crsp_stkshares"]
    mine = facts["permno"] == 900025
    gone = mine & (facts["shrstartdt"] == pd.Timestamp("2021-03-01"))
    facts.loc[mine & (facts["shrstartdt"] == pd.Timestamp("2020-03-02")), "shrenddt"] = facts.loc[gone, "shrenddt"].iloc[0]
    frames["crsp_stkshares"] = facts[~gone].reset_index(drop=True)
    return frames


def quote_rows(dsf: pd.DataFrame, seed: int = 5) -> pd.DataFrame:
    """One quote row per daily row from 1992-11 (half-spread 1 to 30 bp), with each invalid case on a few rows:
    no quote row, both sides missing, one side missing, a side at 0, and ask below bid."""
    rng = np.random.default_rng(seed)
    rows = dsf[dsf["dlycaldt"] >= pd.Timestamp("1992-11-01")].reset_index(drop=True)
    h = rng.uniform(1.0, 30.0, len(rows)) / 10_000.0
    price = rows["dlyprc"].abs().to_numpy()
    table = pd.DataFrame({"permno": rows["permno"].to_numpy(), "dlycaldt": rows["dlycaldt"].to_numpy(),
                          "dlybid": price * (1.0 - h), "dlyask": price * (1.0 + h),
                          "dlyprcflg": rows["dlyprcflg"].to_numpy()})
    table.loc[table.index[3::41], ["dlybid", "dlyask"]] = np.nan
    table.loc[table.index[5::43], "dlyask"] = np.nan
    table.loc[table.index[7::47], "dlybid"] = 0.0
    swap = table.index[11::53]
    table.loc[swap, ["dlybid", "dlyask"]] = table.loc[swap, ["dlyask", "dlybid"]].to_numpy()
    return table.drop(index=table.index[13::59]).reset_index(drop=True)


QUOTE_PARTS = ("1993", "late", "nulldate")


def quote_manifest(table: pd.DataFrame) -> dict:
    """A synthetic quote manifest: one part with every row and two empty parts (no data file)."""
    files = {f"{d.QUOTE_STEM}/{part}.parquet": {"rows": len(table) if part == "1993" else 0,
                                                "sha256": f"{k:064x}"} for k, part in enumerate(QUOTE_PARTS)}
    return {"vintage": VINTAGE, "files": files}


def make_quotes(table: pd.DataFrame) -> w.WrdsData:
    return w.WrdsData({d.QUOTE_STEM: to_arrow(table)}, quote_manifest(table))


def run_one(name: str, data: w.WrdsData, out: Path, quotes: w.WrdsData) -> str:
    """One stage; the in-memory quote copy's manifest is the tracked quote manifest."""
    return d.run_stage(name, data, out, TRACKED, quotes=quotes, tracked_quotes=quotes.manifest)


@pytest.fixture(scope="module")
def long_frames() -> dict[str, pd.DataFrame]:
    return long_world_frames(LONG_CAL)


@pytest.fixture(scope="module")
def quotes(long_frames) -> w.WrdsData:
    return make_quotes(quote_rows(long_frames["crsp_dsf_v2"]))


@pytest.fixture(scope="module")
def long_chain(long_frames, quotes, tmp_path_factory) -> dict:
    """The long world from the coverage counts to the check stage; amendment 3's run 2 digest is replaced by the
    world's own freeze digest."""
    folder = tmp_path_factory.mktemp("long") / "out"
    data = make_data(long_frames)
    digests, seconds = {}, {}
    with pytest.MonkeyPatch.context() as patch:
        for name in d.STAGES:
            if name == "confirm":
                frozen = (folder / "shortlist_digest.txt").read_text().strip()
                patch.setattr(d, "run2_digest", lambda trial: frozen)
            begin = time.perf_counter()
            digests[name] = run_one(name, data, folder, quotes)
            seconds[name] = round(time.perf_counter() - begin, 1)
    print(f"long-world chain: {seconds}")
    return {"folder": folder, "digests": digests, "frozen": frozen}


def log_calls(out: Path, name: str) -> list[str]:
    """The criteria calls of one stage in the run log, with repeats merged."""
    calls: list[str] = []
    for line in (out / "run_log.jsonl").read_text().splitlines():
        entry = json.loads(line)
        if entry.get("stage") == name and "call" in entry and (not calls or calls[-1] != entry["call"]):
            calls.append(entry["call"])
    return calls


SETS = {d.COMPOSITE, *sig.SIGNAL_IDS, d.FAMILY_A_SET}
SEGMENT_REPORTS = {"runs", "sets", "segment", "signals_r6", "s2_short_history", "s2_valid_share_by_month",
                   "s2_split_in_basis_window_by_year", "s2_basis_quarters_by_year"}
RUN_REPORTS = {"blank_months", "blank_month_count", "blank_month_share", "positions", "positions_by_exit_class",
               "cw_weight_by_exit_class", "blanked_level_windows", "r6_members"}
RECORD_REPORTS = {"tilt_stats", "r4", "half_spread"}
HALF_SPREAD = {"traded_notional", "traded_notional_by_status", "crsp_binds_share", "bid_ask_share", "max_half_spread",
               "cost_above_schedule", "invalid_traded_cells_by_exit_class"}


def check_segment(part: dict, name: str) -> None:
    """Every set on both loader runs and both cost cases, with each report owed (reports_owed)."""
    assert set(part) == SEGMENT_REPORTS and part["segment"]["name"] == name
    assert set(part["sets"]) == SETS
    for run in d.RUNS:
        assert set(part["runs"][run]) == RUN_REPORTS
    for set_name, item in part["sets"].items():
        assert set(item["records"]) == set(d.RUNS) and set(item["counts"]) == set(d.RUNS)
        assert set(item["path_break_positions"]) == set(d.RUNS)
        assert ("c_zero_by_exit_class" in item) is (set_name in sig.SIGNAL_IDS)
        for run in d.RUNS:
            assert "b2" in item["counts"][run]
            assert set(item["records"][run]) == set(d.CASES)
            for case in d.CASES:
                record = item["records"][run][case]
                assert set(record) == RECORD_REPORTS and set(record["r4"]) == set(record["half_spread"]) == set(
                    tilt.BOOKS)
                assert "post_publication" in record["tilt_stats"]
                for year in record["half_spread"]["tilt"].values():
                    assert set(year) == HALF_SPREAD
                    assert set(year["traded_notional_by_status"]) == {"valid", *tilt.QUOTE_REASONS}


def test_the_long_world_chain_reaches_check(long_chain) -> None:
    out = long_chain["folder"]
    for k, name in enumerate(d.STAGES):
        raw = (out / f"{name}.json").read_bytes()
        assert (out / f"{name}.sha256").read_text().strip() == d.sha256_bytes(raw) == long_chain["digests"][name]
        assert json.loads(raw)["previous"] == {s: long_chain["digests"][s] for s in d.STAGES[:k]}
    assert stage(out, "calibration")["decision"] == "ratio_coverage_low"
    assert stage(out, "freeze")["shortlist"] == ["S7"]
    stopped = {"stopped": True, "label": "stopped_coverage", "p_b": 1.0, "calibration_decision": "ratio_coverage_low",
               "calibration_sha256": long_chain["digests"]["calibration"]}
    for name in ("confirm", "check"):
        assert stage(out, name)["test_b"] == stopped
        assert stage(out, name)["digest_sha256"] == long_chain["frozen"]


def test_the_confirm_stage_follows_primary_decision_with_p_b_one(long_chain) -> None:
    """verify_frozen_screen, composite_test, composite_means at 2x, holm_primary(p_A, 1.0), stop_after_confirm; the
    same calls on the last_close run (R4). primary_decision itself is never called."""
    out = long_chain["folder"]
    confirm = stage(out, "confirm")
    assert log_calls(out, "confirm")[:6] == ["verify_frozen_screen", "composite_test", "composite_means",
                                             "holm_primary", "stop_after_confirm", "holm_primary"]
    assert "primary_decision" not in (out / "run_log.jsonl").read_text()
    for key, run in (("decision", "primary"), ("last_close", "last_close")):
        found = confirm["test_a"][key]
        record = confirm["test_a"]["records"][run]["primary"]
        assert found["p_b"] == 1.0 and found["p_a"] == record["p_a"]
        assert found["holm"] == crit.holm_primary(found["p_a"], 1.0)
        assert found["holm"]["A"] == min(1.0, 2.0 * found["p_a"])
        assert found["confirm_means"] == {k: record[k]["annual_mean"] for k in ("vs_spy", "vs_cw")}
        means_2x = confirm["means"][d.COMPOSITE][run]["sensitivity_2x"]
        assert found["cost_2x_means"] == {k: means_2x[k] for k in ("vs_spy", "vs_cw")}
        assert found["stop"] == crit.stop_after_confirm(found["confirm_means"]["vs_spy"])
        months = record["vs_spy"]["months"]
        assert months == crit.CONFIRM_MONTHS - record["blank_reason_counts"].get("path_break_held", 0)
    assert confirm["segment"]["segment"]["anchor"] == "1992-12-31"
    check_segment(confirm["segment"], "confirm")
    secondary = confirm["secondary"]["primary"]["primary"]
    assert secondary["family_size"] == 9 and set(secondary["members"]) | set(secondary["undefined"]) == set(
        d.SECONDARY)
    assert all(m["q_by"] >= m["p_a"] for m in secondary["members"].values())
    assert set(confirm["family_a_screen"]) == {"records", "counts", "fragility"}
    assert set(confirm) >= {"header", "fragility", "oi09", "me_coverage", "bid_ask_midpoint_share", "means"}


def test_the_check_stage_joins_both_segments_without_a_gap_month(long_chain) -> None:
    out = long_chain["folder"]
    check, confirm = stage(out, "check"), stage(out, "confirm")
    assert check["check_period_end"] == "2025-11"
    assert check["series_months"] == {"first": "2014-04", "last": "2025-11", "count": 63 + 51,
                                      "gap_months_in_series": 0}
    assert list(check["check_gap_months"]) == [str(m) for m in crit.CHECK_GAP_MONTHS]
    assert [check["check_gap_months"][m] for m in ("2019-07", "2020-07", "2020-08", "2020-09", "2021-08")] == [
        "seal", "seal", "sealed_2020_07_31_row", "warm_up", "warm_up"]
    for name in ("check_pre_seal", "check_post_seal"):
        check_segment(check["segments"][name], name)
    log = log_calls(out, "check")
    assert log[0] == "verify_frozen_screen" and "decide_a" in log and "composite_test" not in log
    for key, run in (("label", "primary"), ("last_close", "last_close")):
        before = confirm["test_a"]["decision" if run == "primary" else "last_close"]
        assert check["test_a"][key] == crit.decide_a(before["holm"]["A"], before["confirm_means"],
                                                    before["cost_2x_means"], check["means"][d.COMPOSITE][run]["primary"])
    # The confirm stopped below the floor, and the check still ran (R9).
    assert check["test_a"]["confirm_stop"] == confirm["test_a"]["decision"]["stop"] == "confirm_below_floor"
    rule = check["s2_history_rule"]
    assert rule["seal_quarters_by_year"] == {"2020": 3}
    assert set(rule["valid_share_by_post_seal_month"]) == {str(m) for m in pd.period_range("2021-09", "2025-11",
                                                                                         freq="M")}
    assert check["me_coverage"]["basis_unseen_member_days_by_year"]["seal"]
    assert {"header", "fragility", "oi09", "bid_ask_midpoint_share", "means"} <= set(check)


def test_the_half_spread_report_shows_each_quote_status_and_the_cost_above_the_schedule(long_chain) -> None:
    for name, part in (("confirm", stage(long_chain["folder"], "confirm")["segment"]),
                       *stage(long_chain["folder"], "check")["segments"].items()):
        years = part["sets"][d.COMPOSITE]["records"]["primary"]["primary"]["half_spread"]["tilt"]
        statuses = {s for y in years.values() for s, v in y["traded_notional_by_status"].items() if v > 0.0}
        assert statuses == {"valid", *tilt.QUOTE_REASONS}, name
        for year in years.values():
            assert math.isclose(sum(year["traded_notional_by_status"].values()), year["traded_notional"])
            assert year["cost_above_schedule"] >= -1e-15 and year["max_half_spread"] < 30.0
        assert any(y["crsp_binds_share"] > 0.0 for y in years.values())
        assert any(y["cost_above_schedule"] > 0.0 for y in years.values())


# Quote files and rows ------------------------------------------------------------------------

def write_quotes(root: Path, table: pd.DataFrame) -> dict:
    """A quote folder: the rows as ``1993.parquet``, two empty parts with no file, and ``MANIFEST_local.json``."""
    folder = root / d.QUOTE_STEM
    folder.mkdir(parents=True)
    pq.write_table(to_arrow(table).append_column("dlyretx", pa.array([0.0] * len(table))), folder / "1993.parquet")
    manifest = {"vintage": VINTAGE, "files": {
        f"{d.QUOTE_STEM}/1993.parquet": {"rows": len(table), "sha256": w.sha256(folder / "1993.parquet")},
        f"{d.QUOTE_STEM}/late.parquet": {"rows": 0, "sha256": "0" * 64},
        f"{d.QUOTE_STEM}/nulldate.parquet": {"rows": 0, "sha256": "0" * 64}}}
    (root / w.MANIFEST).write_text(json.dumps(manifest))
    return manifest


def small_quotes() -> pd.DataFrame:
    return pd.DataFrame({"permno": [900001, 900002], "dlycaldt": pd.to_datetime(["1993-01-29", "1993-01-29"]),
                         "dlybid": [9.9, 19.8], "dlyask": [10.1, 20.2], "dlyprcflg": ["TR", "BA"]})


def test_quote_files_check_each_file_and_read_the_quote_columns_only(tmp_path) -> None:
    manifest = write_quotes(tmp_path / "wrds_quotes_x", small_quotes())
    read = d.quote_files(tmp_path / "wrds_quotes_x", read=True)
    assert read.manifest == manifest and read.tables[d.QUOTE_STEM].column_names == d.QUOTE_COLUMNS
    assert read.tables[d.QUOTE_STEM].num_rows == 2
    assert d.quote_files(tmp_path / "wrds_quotes_x", read=False).tables == {}
    assert d.check_quotes(read, manifest, d.load_trial()[0]) == d.check_quotes(read, json.loads(json.dumps(
        manifest)), d.load_trial()[0])


def _relist(root: Path, edit) -> None:
    manifest = json.loads((root / w.MANIFEST).read_text())
    edit(manifest["files"])
    (root / w.MANIFEST).write_text(json.dumps(manifest))


@pytest.mark.parametrize("damage, reason", [
    ("sealed_root", "sealed_path"), ("sealed_file", "sealed_path"), ("outside", "path_outside_root"),
    ("other_table", "quote_file_unexpected"), ("empty_part_has_file", "file_unexpected"),
    ("missing", "file_missing"), ("hash", "hash_mismatch"), ("rows", "row_count_mismatch")])
def test_quote_files_refuse_each_damage(tmp_path, damage, reason) -> None:
    root = tmp_path / ("sealed" if damage == "sealed_root" else "wrds_quotes_x")
    write_quotes(root, small_quotes())
    main = f"{d.QUOTE_STEM}/1993.parquet"
    if damage == "sealed_file":
        _relist(root, lambda f: f.update({"sealed/crsp_dsf_v2_quotes.parquet": {"rows": 1, "sha256": "0"}}))
    elif damage == "outside":
        _relist(root, lambda f: f.update({f"../{d.QUOTE_STEM}/1994.parquet": {"rows": 1, "sha256": "0"}}))
    elif damage == "other_table":
        _relist(root, lambda f: f.update({"crsp_dsf_v2/1993.parquet": {"rows": 1, "sha256": "0"}}))
    elif damage == "empty_part_has_file":
        shutil.copy(root / main, root / d.QUOTE_STEM / "late.parquet")
    elif damage == "missing":
        (root / main).unlink()
    elif damage == "hash":
        _relist(root, lambda f: f[main].update({"sha256": "0" * 64}))
    elif damage == "rows":
        _relist(root, lambda f: f[main].update({"rows": 3}))
    with pytest.raises(RunnerStop) as caught:
        d.quote_files(root, read=True)
    assert caught.value.reason == reason


def test_the_quote_copy_must_be_the_tracked_quote_manifest() -> None:
    trial = d.load_trial()[0]
    quotes = make_quotes(small_quotes())
    files = quotes.manifest["files"]
    for tracked in ({"vintage": VINTAGE, "files": {**files, f"{d.QUOTE_STEM}/1994.parquet": {"rows": 1,
                                                                                            "sha256": "0"}}},
                    {"vintage": VINTAGE, "files": {k: {**v, "rows": v["rows"] + 1} for k, v in files.items()}},
                    {"vintage": VINTAGE, "files": {k: {**v, "sha256": "f" * 64} for k, v in files.items()}},
                    {"vintage": "2024-12-31", "files": files}):
        with pytest.raises(RunnerStop) as caught:
            d.check_quotes(quotes, tracked, trial)
        assert caught.value.reason == "quote_manifest_mismatch"


def test_quote_rows_refuse_a_missing_key_a_seal_date_a_repeat_and_an_unmatched_row(long_frames) -> None:
    data = make_data(long_frames)
    good = small_quotes()
    table = d.quote_table(make_quotes(good), data)
    assert list(table.columns) == ["permno", "date", "dlybid", "dlyask", "dlyprcflg"]
    assert table["permno"].tolist() == ["900001", "900002"]
    no_date = good.astype({"dlycaldt": object})
    no_date.loc[1, "dlycaldt"] = None
    cases = {"quote_key_missing": [good.astype({"permno": "float"}).assign(permno=[900001.0, np.nan]), no_date],
             "quote_row_in_seal": [good.assign(dlycaldt=pd.to_datetime(["1993-01-29", "2019-07-31"])),
                                   good.assign(dlycaldt=pd.to_datetime(["1993-01-29", "2020-07-30"]))],
             "quote_key_repeated": [pd.concat([good, good.iloc[:1]], ignore_index=True)],
             "quote_row_unmatched": [good.assign(dlycaldt=pd.to_datetime(["1993-01-29", "1993-01-30"])),
                                     good.assign(permno=[900001, SPY_PERMNO + 1])]}
    for reason, tables in cases.items():
        for bad in tables:
            with pytest.raises(RunnerStop) as caught:
                d.quote_table(w.WrdsData({d.QUOTE_STEM: to_arrow(bad)}, quote_manifest(bad)), data)
            assert caught.value.reason == reason
    with pytest.raises(RunnerStop) as caught:
        d.quote_table(w.WrdsData({}, quote_manifest(good)), data)
    assert caught.value.reason == "file_missing"


def test_a_quote_change_at_r_or_later_leaves_the_rate_at_r(long_frames, quotes) -> None:
    """R1: the rate at rebalance r reads the quote at r - 1 only, so changed quotes on r and later rows leave it."""
    data = make_data(long_frames)
    plan = d.segment_plan(w.calendar(data))["confirm"]
    frames = d.segment_frames(data, "primary", plan)
    r = month_end(LONG_CAL, "2003-06")
    table = d.quote_table(quotes, data)
    later = table["date"] >= r
    changed = table.assign(dlyask=table["dlyask"].where(~later, table["dlybid"] * 1.5))
    rates = {}
    for name, rows in (("base", table), ("changed", changed)):
        panel = d.quote_panels(rows, frames, plan["end"])
        rates[name] = tilt.spread_rates(panel["half_spread"], tilt.COST_SCHEDULE, 1.0)
    rows = rates["base"].index
    at = rows.get_loc(r)
    pd.testing.assert_frame_equal(rates["base"].iloc[:at + 1], rates["changed"].iloc[:at + 1])
    assert (rates["changed"].iloc[at + 1] > rates["base"].iloc[at + 1]).any()


def test_the_quote_manifest_digest_enters_every_stage_context(long_frames, tmp_path) -> None:
    data = make_data(long_frames)
    table = small_quotes()
    other = make_quotes(table)
    other.manifest["files"][f"{d.QUOTE_STEM}/1993.parquet"]["sha256"] = "e" * 64
    contexts = []
    for name, copy in (("a", make_quotes(table)), ("b", other)):
        run_one("coverage", data, tmp_path / name, copy)
        contexts.append(json.loads((tmp_path / name / "coverage.json").read_text())["context"])
    assert contexts[0]["data_files_sha256"] != contexts[1]["data_files_sha256"]
    assert {k: v for k, v in contexts[0].items() if k != "data_files_sha256"} == {
        k: v for k, v in contexts[1].items() if k != "data_files_sha256"}


def test_every_stage_needs_the_quote_copy_and_the_tracked_quote_manifest(long_frames, tmp_path) -> None:
    """A repository copy with the trial file and the pinned files but no tracked quote manifest."""
    data = make_data(long_frames)
    with pytest.raises(RunnerStop) as caught:
        d.run_stage("coverage", data, tmp_path / "a", TRACKED)
    assert caught.value.reason == "quotes_missing"
    repo = tmp_path / "repo"
    trial = d.load_trial()[0]
    for path in [d.TRIAL_FILE, *(p for p, pin in trial["code_pins"].items() if p != "statement" and pin["commit"])]:
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(d.REPO / path, repo / path)
    with pytest.raises(RunnerStop) as caught:
        d.run_stage("coverage", data, tmp_path / "b", TRACKED, repo=repo, quotes=make_quotes(small_quotes()))
    assert caught.value.reason == "quote_manifest_missing"


# Segments --------------------------------------------------------------------------------

def test_the_three_segments_take_their_dates_from_the_calendar() -> None:
    plan = d.segment_plan(LONG_CAL)
    found = {name: (str(s["first"]), str(s["last"]), *(s[k].date().isoformat() for k in (
        "anchor", "first_rebalance", "end"))) for name, s in plan.items()}
    assert found == {"confirm": ("1993-02", "2014-03", "1992-12-31", "1993-01-29", "2014-03-31"),
                     "check_pre_seal": ("2014-04", "2019-06", "2014-02-28", "2014-03-31", "2019-06-28"),
                     "check_post_seal": ("2021-09", "2025-11", "2021-07-30", "2021-08-31", "2025-11-28")}
    assert {name: s["period"] for name, s in plan.items()} == {"confirm": "confirm", "check_pre_seal": "check",
                                                              "check_post_seal": "check"}
    for cal, reason in ((LONG_CAL.drop(pd.Timestamp("2021-07-30")), "post_seal_anchor_mismatch"),
                        (LONG_CAL[LONG_CAL.to_period("M") != pd.Period("2014-02", "M")], "calendar_month_missing"),
                        (LONG_CAL[LONG_CAL <= pd.Timestamp("2021-09-30")], "check_period_invalid")):
        with pytest.raises(RunnerStop) as caught:
            d.segment_plan(cal)
        assert caught.value.reason == reason
    assert d.check_period_end(LONG_CAL[LONG_CAL <= pd.Timestamp("2021-10-01")]) == pd.Period("2021-09", "M")


# The long chain ------------------------------------------------------------------------------

def test_coverage_to_freeze_give_the_results_of_the_run_2_driver(long_frames, long_chain, tmp_path,
                                                                  monkeypatch) -> None:
    """Screen months keep SCREEN_COST_SCHEDULE with no half-spread panel, so the driver at main 8590b2e (the code of
    run 2) gives the same result in every stage from the coverage counts to the freeze. Only the calibration stage
    file digest in each test B record differs, because the stage context now holds the quote manifest digest."""
    old = module_at(BASE_COMMIT, "research/m55_driver.py", "m55_driver_run2", tmp_path)
    monkeypatch.setattr(old, "TRIAL_SHA256", d.TRIAL_SHA256)
    data = make_data(long_frames)
    out = tmp_path / "out"
    assert old.STAGES == d.STAGES[:d.STAGES.index("freeze") + 1]
    for name in old.STAGES:
        old.run_stage(name, data, out, TRACKED, repo=d.REPO)
        before, after = stage(out, name), stage(long_chain["folder"], name)
        if "test_b" in before:
            assert before["test_b"].pop("calibration_sha256") == (out / "calibration.sha256").read_text().strip()
            assert after["test_b"].pop("calibration_sha256") == long_chain["digests"]["calibration"]
        assert before == after, name
    assert (out / "shortlist_digest.txt").read_text() == (long_chain["folder"] / "shortlist_digest.txt").read_text()


def copy_chain(long_chain: dict, folder: Path, name: str) -> Path:
    """A copy of the long-world stage folder without stage ``name`` and the stages after it."""
    out = folder / "out"
    shutil.copytree(long_chain["folder"], out)
    for later in d.STAGES[d.STAGES.index(name):]:
        for suffix in (".json", ".sha256"):
            (out / f"{later}{suffix}").unlink()
    return out


@pytest.mark.parametrize("name", ["confirm", "check"])
def test_a_confirm_or_check_stage_refuses_another_freeze_digest(long_frames, quotes, long_chain, tmp_path,
                                                                name) -> None:
    """Amendment 3 states the run 2 digest; this world's freeze has another digest, so the gate refuses."""
    out = copy_chain(long_chain, tmp_path, name)
    with pytest.raises(RunnerStop) as caught:
        run_one(name, make_data(long_frames), out, quotes)
    assert caught.value.reason == "shortlist_digest_mismatch" and not (out / f"{name}.json").exists()
    assert json.loads((out / "run_log.jsonl").read_text().splitlines()[-1])["refused"] == "shortlist_digest_mismatch"


@pytest.mark.parametrize("name, uncut, reason", [
    ("confirm", "cut_frames", "row_after_confirm_end"), ("confirm", "cut_inputs", "row_after_confirm_end"),
    ("check", "cut_frames", "row_after_check_end"), ("check", "cut_inputs", "row_after_check_end")])
def test_a_confirm_or_check_stage_refuses_a_row_after_its_segment_end(long_frames, quotes, long_chain, tmp_path,
                                                                      monkeypatch, name, uncut, reason) -> None:
    """Without the cut of the loader frames or of the signal inputs, a row after the segment end reaches a check."""
    out = copy_chain(long_chain, tmp_path, name)
    monkeypatch.setattr(d, "run2_digest", lambda trial: long_chain["frozen"])
    monkeypatch.setattr(d, uncut, lambda table, last: table)
    with pytest.raises(RunnerStop) as caught:
        run_one(name, make_data(long_frames), out, quotes)
    assert caught.value.reason == reason and not (out / f"{name}.json").exists()


def test_a_confirm_stage_refuses_while_test_b_is_open(long_frames, quotes, long_chain, tmp_path, monkeypatch) -> None:
    """After the calibration decision chosen, test B would run, which this trial file no longer does."""
    out = copy_chain(long_chain, tmp_path, "confirm")
    rechain(out, set_calibration("chosen"))
    monkeypatch.setattr(d, "run2_digest", lambda trial: long_chain["frozen"])
    with pytest.raises(RunnerStop) as caught:
        run_one("confirm", make_data(long_frames), out, quotes)
    assert caught.value.reason == "test_b_open"


def test_a_confirm_stage_opens_no_month_after_an_empty_screen(long_frames, quotes, long_chain, tmp_path,
                                                              monkeypatch) -> None:
    out = copy_chain(long_chain, tmp_path, "confirm")

    def empty(name: str, payload: dict) -> None:
        if name == "freeze":
            record = {**payload["result"]["record"], "shortlist": [], "decision": "screen_empty"}
            record["digest_sha256"] = crit.shortlist_digest(record)
            payload["result"].update(record=record, digest_sha256=record["digest_sha256"], decision="screen_empty",
                                     shortlist=[])
    rechain(out, empty)
    monkeypatch.setattr(d, "run2_digest", lambda trial: stage(out, "freeze")["digest_sha256"])
    with pytest.raises(RunnerStop) as caught:
        run_one("confirm", make_data(long_frames), out, quotes)
    assert caught.value.reason == "screen_empty_confirm"


@pytest.mark.parametrize("name", ["confirm", "check_pre_seal"])
def test_values_after_a_segment_end_change_nothing_in_the_segment(long_frames, name, monkeypatch) -> None:
    """R1 at the segment end: every value after the end row changes, the quotes too; the composite's series, the
    declarations, and the reports of the segment do not. The Family A panel is checked alone (no engine call)."""
    real = d.signal_sets
    monkeypatch.setattr(d, "signal_sets", lambda *args: {d.COMPOSITE: real(*args)[d.COMPOSITE]})
    plan = d.segment_plan(LONG_CAL)[name]
    trial = d.load_trial()[0]
    publication = next(o for o in trial["open_items"] if o["id"] == "OI-08")["publication_years"]
    found, family = [], []
    for frames in (long_frames, perturb_after(long_frames, plan["end"])):
        data = make_data(frames)
        table = d.quote_table(make_quotes(quote_rows(frames["crsp_dsf_v2"])), data)
        part = d.run_segment(data, table, plan, ["S7"], d.exit_map(data), publication, d.unseen_cells(data))
        found.append(part)
        family.append(d.family_a_panel(data, d.segment_frames(data, "primary", plan), plan["end"]))
    assert d.clean(found[0]["result"]) == d.clean(found[1]["result"])
    assert found[0]["declared"] == found[1]["declared"]
    for run in d.RUNS:
        for case in d.CASES:
            for book in ("tilt", "cw"):
                pd.testing.assert_series_equal(found[0]["series"][d.COMPOSITE][run][case][book],
                                               found[1]["series"][d.COMPOSITE][run][case][book])
    for factor in family[0]:
        pd.testing.assert_frame_equal(family[0][factor], family[1][factor])
