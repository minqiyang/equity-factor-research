"""M4.7 stage a-2 coverage census oracles (plan section 5; T-CENSUS-1..10) and the end-to-end acceptance run."""

from __future__ import annotations

import json
import math
import re
from datetime import date

import numpy as np
import pandas as pd
import pytest

from backtest.long_short import run_long_short_backtest
from backtest.portfolio import capture_backtest_source_provenance, run_long_only_backtest
from data import holdout_partition
from data.constituent_table import load_constituent_intervals_csv
from data.holdout_partition import SEAL_RULE_OPTION_A, SnapshotRefusal
from data.parquet_loader import load_eod_cohort_panels
from fixtures.m4_7.e2e_scenario import JOIN2_MISSING, JOIN_MISSING, PEEL_OLD_MISSING, run_pipeline
from m4_7_snapshot_support import CAL, I_H, Harness, bars, day, entry, rows
from research.m4_7_common_support import signal_eligibility
from research.m4_7_coverage_census import (
    derive_readiness,
    power_projection,
    prior_exposure_overlap,
    run_census,
    volume_basis_diagnostic,
)
from research.m4_7_holdout_seal import seal_snapshot
from research.m4_7_terminal_evidence import CURATED, EVIDENCE_COLUMNS, project, read_engine_events, validate, write_template
from research.m4_7_universe_build import build_universe, discovery_window


N = len(CAL)
START = "1993-12-15"
_, D0, D_LAST = discovery_window(CAL, date(2003, 12, 31))
SPAN = D_LAST - D0 + 1
ANCHORS = {f"A0{k}": bars(rows(0, N), close=50.0 + k) for k in range(1, 5)}


def census(tmp_path, monkeypatch, name, entries, codes, *, listed=(), delisted=(), hook=None, band=(1, 1000),
           rebuild_only=None):
    """Retrieve, build, template, validate, project, and run the census; return the harness and census result."""
    monkeypatch.setattr(holdout_partition, "BAND", band)
    monkeypatch.setattr(holdout_partition, "HARD_BAND", (max(band[0] - 1, 0), band[1] + 1))
    harness = Harness(tmp_path, monkeypatch, snapshot_id=name)
    vendor = harness.vendor
    vendor.entries, vendor.listed, vendor.delisted = list(entries), list(listed), list(delisted)
    vendor.code("SPY.US", bars(rows(0, N)))
    for code, spec in codes.items():
        vendor.code(code, *spec) if isinstance(spec, tuple) else vendor.code(code, spec)
    (hook or (lambda h: h.retrieve()))(harness)
    return harness, downstream(harness, tmp_path / f"{name}_out")


def downstream(harness, out):
    snap = harness.snapshot_dir
    build_universe(snap)
    template = write_template(snap)
    template[list(EVIDENCE_COLUMNS)].to_csv(snap / CURATED, index=False)
    validate(snap)
    project(snap)
    return run_census(snap, reports_dir=out / "reports", seal_out=out / "seal.json", code_commit="test")


def anchors_with(**codes):
    entries = [entry(code, START) for code in ANCHORS]
    return entries, {f"{code}.US": history for code, history in ANCHORS.items()} | codes


def failing(result):
    return {f["rule"]: f["result"] for f in result["public"]["census_readiness"]["failures"]}


def unpriced(result):
    return result["public"]["price_coverage"]["eligible_unpriced_member_days"]


# ---------------------------------------------------------------- T-CENSUS-1


def test_t_census_1_breadth_series_and_within_month_collapse(tmp_path, monkeypatch):
    entries = [entry(f"M{k}", START) for k in (1, 2, 3)]
    for k in (4, 5, 6):
        entries += [entry(f"M{k}", START, "2005-06-10"), entry(f"M{k}", "2005-06-20")]
    codes = {f"M{k}.US": bars(rows(0, N)) for k in range(1, 7)}
    _, result = census(tmp_path, monkeypatch, "c1", entries, codes, band=(5, 6))
    breadth = result["public"]["membership_breadth"]
    r10, r20 = CAL.get_loc(pd.Timestamp("2005-06-10")), CAL.get_loc(pd.Timestamp("2005-06-20"))
    assert breadth["members_per_date_by_year"]["2005"] == {"min": 3, "median": 6.0, "max": 6, "dates_below_band": r20 - r10}
    assert breadth["members_per_date_by_year"]["2006"] == {"min": 6, "median": 6.0, "max": 6, "dates_below_band": 0}
    months = {m["month"]: m for m in breadth["members_per_month_end"]}
    assert months["2005-06"] == {"month": "2005-06", "count": 6, "status": "in_band"}
    assert all(m["count"] == 6 for m in months.values())
    coverage = result["public"]["price_coverage"]
    assert coverage["member_days_total"] == 6 * SPAN - 3 * (r20 - r10)
    assert coverage["member_days_with_bar"] == coverage["member_days_total"] and coverage["member_days_missing_bar"] == 0


# ---------------------------------------------------------------- end-to-end fixture: T-CENSUS-2, 3 and acceptance


@pytest.fixture(scope="module")
def e2e(tmp_path_factory):
    with pytest.MonkeyPatch.context() as patch:
        yield run_pipeline(tmp_path_factory.mktemp("e2e"), patch)


def test_t_census_2_public_outputs_carry_no_security_level_content(e2e):
    base = e2e["base"]
    public_json = (base / "reports/m4_7_coverage_census.json").read_text()
    public_md = (base / "reports/m4_7_coverage_census.md").read_text()
    master = pd.read_csv(e2e["snapshot"] / "identity/security_master.csv", dtype=str, keep_default_na=False)
    for text in (public_json, public_md):
        assert ".US#E" not in text and ".US" not in text
        for code in set(master["vendor_code"]):
            assert not re.search(rf"\b{re.escape(code.removesuffix('.US'))}\b", text), code
    public = json.loads(public_json)
    day_level = re.compile(r"\d{4}-\d{2}-\d{2}")
    for record in public["exclusion_set"]["gap_windows"] + public["exclusion_set"]["segments"]:
        assert not day_level.search(json.dumps(record))
    assert {"start_month", "end_month", "reason_types", "rows"} == set(public["exclusion_set"]["gap_windows"][0])

    def keys(value):
        if isinstance(value, dict):
            for key, inner in value.items():
                yield key
                yield from keys(inner)
        elif isinstance(value, list):
            for inner in value:
                yield from keys(inner)

    value_fields = {"open", "high", "low", "close", "adjusted_close", "volume", "price", "terminal_return", "returns", "rho"}
    assert not value_fields & set(keys(public))
    detail = json.loads((e2e["snapshot"] / "census/census_detail.json").read_text())
    assert all(day_level.fullmatch(window["start"]) for window in detail["gap_windows"])


def test_t_census_3_holdout_years_are_metadata_only(tmp_path, monkeypatch):
    entries, codes = anchors_with(**{"HX.US": (bars(rows(0, N), close=60.0, volume=lambda r: 0.0 if r in (40, 600) else 1000.0),
                                              [{"date": "2003-08-01", "split": "2/1"}],
                                              [{"date": "2003-09-02", "value": 0.0}, {"date": day(600), "value": 0.0}])})
    entries.append(entry("HX", START))

    def hook(harness):
        assert harness.run("components") == 0 and harness.run("symbols") == 0
        harness.seal(holdout_start="1994-01-31", holdout_end="2004-01-31")
        for command in ("calendar", "splits", "eod", "dividends", "verify"):
            harness.run(command)

    _, result = census(tmp_path, monkeypatch, "c3", entries, codes, hook=hook)
    public = result["public"]
    assert public["holdout_metrics_scope"] == "metadata_only"
    assert "2003" in public["membership_breadth"]["members_per_date_by_year"]
    for group in ("price_quality", "corporate_actions"):
        assert min(public[group]["discovery_years"]) >= "2004"
    assert public["corporate_actions"]["split_rows"] == 0 and public["corporate_actions"]["dividend_rows"] == 1
    assert public["corporate_actions"]["discovery_years"]["2005"]["dividend_rows"] == 1
    assert public["price_quality"]["zero_volume_member_days"] == 1


def equal_weight(s_mask):
    return s_mask.astype(float).where(s_mask)


def test_a2_end_to_end_fixture_flows_and_every_book_completes_on_the_peeled_schedule(e2e):
    snap, support = e2e["snapshot"], e2e["support"]
    seal = json.loads((e2e["base"] / "seal/m4_7_holdout_seal_v1.json").read_text())
    assert seal["confirmation"]["status"] == "confirmed" and seal["holdout_end_exclusive"] == "2003-12-31"
    assert e2e["validation"]["counts"] == {"accepted": 6, "curation_unresolved": 1, "deferred_holdout": 1}
    windows = [(w.start, w.end, sorted(w.reasons), w.peeled_rows) for w in support.schedule.windows]
    peel = next(w for w in windows if "terminal_reset_missing_bar" in w[2])
    assert (peel[0] + I_H, peel[3]) == (JOIN2_MISSING, 2)
    assert set(support.schedule.g_term) == {("JOIN.US#E1", JOIN_MISSING - I_H), ("JOIN2.US#E1", JOIN2_MISSING - I_H)}
    assert PEEL_OLD_MISSING - I_H in [row for row in np.flatnonzero(support.schedule.g_base["A02.US#E1"].to_numpy())]
    census_exclusion = e2e["census"]["public"]["exclusion_set"]
    assert census_exclusion["excluded_rows"] == support.schedule.excluded_rows
    assert census_exclusion["gap_window_count"] == len(support.schedule.windows)
    segments = json.loads((snap / "census/segments.json").read_text())
    assert segments["segments_sha256"] == support.segments_sha256 == census_exclusion["segments_sha256"]
    assert segments["segments"][0]["last_row"] == day(JOIN2_MISSING - 1) and segments["D0"] == day(412)
    table = load_constituent_intervals_csv(snap / "membership/constituent_intervals.csv")
    assets = list(support.bars.columns)
    panels = load_eod_cohort_panels(snap / "panel", assets, inventory_path=snap / "panel/inventory_discovery.json")
    prices = panels["adjusted_close"].reindex(support.calendar)
    events = read_engine_events(snap)
    events = events[events["permanent_id"].isin(assets)].reset_index(drop=True)
    s_mask = signal_eligibility(support.mask, support.bars)
    scores = s_mask.astype(float).where(s_mask).mul(np.arange(len(assets), 0, -1), axis=1)
    settled, executable = set(), set()
    for segment in (s for s in support.schedule.segments if s.valid):
        span = support.calendar[segment.first:segment.last + 1]
        executable |= set(events.loc[events["effective_date"].isin(span), "permanent_id"])
        start, end = support.calendar[segment.anchor], support.calendar[segment.last]
        common = dict(evaluation_start=start, evaluation_end=end, rebalance_frequency="ME", constituent_intervals=table,
                      terminal_events=events, transaction_cost_bps=1.0, slippage_bps=4.0)
        top = run_long_only_backtest(prices, scores, source_provenance=capture_backtest_source_provenance(prices, scores),
                                     top_pct=0.1, **common)
        benchmark_signal = equal_weight(s_mask)
        benchmark = run_long_only_backtest(prices, benchmark_signal, top_pct=1.0, **{**common, "transaction_cost_bps": 0.0,
                                           "slippage_bps": 0.0}, source_provenance=capture_backtest_source_provenance(
                                               prices, benchmark_signal))
        spread = run_long_short_backtest(prices, scores, quantiles=2, **common)
        for book in (top, benchmark, spread):
            assert np.isfinite(book.equity_curve.to_numpy()).all()
        settled |= {record["permanent_id"] for record in benchmark.terminal_event_log}
    assert settled == executable == set(events["permanent_id"])
    assert set(events["return_basis"].value_counts().to_dict().values()) == {1, 2, 3}


# ---------------------------------------------------------------- T-CENSUS-4, 5, 6


CLEAN = {
    "in_band_years": 20.0, "holdout_end": "2000-01-31", "gap_window_count": 3, "excluded_fraction": 0.01,
    "identity_refusal_fraction": 0.01, "off_calendar_fraction": 0.0, "calendar_covers_coverage_start": True,
    "benchmark_complete": True, "snapshot_integrity": True, "holdout_band_after_identity": True,
    "ic_month_supply": 120, "unpriced_fraction": 0.01, "retrieval_complete": True,
}


@pytest.mark.parametrize("change, rule, result", [
    ({"in_band_years": 15.0}, "R-CENSUS-1", "blocked:insufficient_in_band_history"),
    ({"holdout_end": "2014-02-28"}, "R-CENSUS-1", "blocked:holdout_overlaps_prior_exposure"),
    ({"gap_window_count": 7}, "R-CENSUS-2", "blocked:excluded_coverage"),
    ({"gap_window_count": 6, "excluded_fraction": 0.051}, "R-CENSUS-2", "blocked:excluded_coverage"),
    ({"identity_refusal_fraction": 0.051}, "R-CENSUS-3", "blocked:identity_refusal_fraction"),
    ({"off_calendar_fraction": 0.0011}, "R-CENSUS-4", "blocked:calendar_divergence"),
    ({"calendar_covers_coverage_start": False}, "R-CENSUS-5", "blocked:calendar_source_missing"),
    ({"benchmark_complete": False}, "R-CENSUS-5", "blocked:benchmark_gap"),
    ({"snapshot_integrity": False}, "R-CENSUS-6", "blocked:snapshot_integrity"),
    ({"ic_month_supply": 59}, "R-CENSUS-8", "blocked:insufficient_ic_months"),
    ({"unpriced_fraction": 0.021}, "R-CENSUS-9", "blocked:unpriced_eligible_member_days"),
    ({"retrieval_complete": False}, "R-CENSUS-10", "blocked:retrieval_incomplete"),
])
def test_t_census_4_readiness_truth_table(change, rule, result):
    readiness = derive_readiness({**CLEAN, **change})
    assert readiness["status"] == "blocked" and readiness["failures"] == [{"rule": rule, "result": result}]


def test_t_census_4_ready_caveat_and_cap_edges():
    assert derive_readiness(CLEAN)["status"] == "ready"
    assert derive_readiness({**CLEAN, "gap_window_count": 6, "excluded_fraction": 0.049})["status"] == "ready"
    caveat = derive_readiness({**CLEAN, "holdout_band_after_identity": False})
    assert caveat["status"] == "ready_with_caveats:holdout_breadth_after_identity"
    assert not any("vp2" in key for key in derive_readiness(CLEAN)["inputs"])


def test_option_a_readiness_thresholds_follow_the_seal_rule():
    """Owner decision O-3: 7 in-band years, no prior-exposure cap, and 48 IC months under Option A."""
    option_a = {**CLEAN, "in_band_years": 7.0, "holdout_end": "2020-07-31", "ic_month_supply": 48}
    readiness = derive_readiness(option_a, SEAL_RULE_OPTION_A)
    assert readiness["status"] == "ready"
    assert readiness["thresholds"] == {"seal_rule_version": SEAL_RULE_OPTION_A, "min_in_band_years": 7,
                                       "latest_holdout_end": None, "min_ic_months": 48}
    assert derive_readiness({**option_a, "in_band_years": 6.9}, SEAL_RULE_OPTION_A)["failures"] == [
        {"rule": "R-CENSUS-1", "result": "blocked:insufficient_in_band_history"}]
    assert derive_readiness({**option_a, "ic_month_supply": 47}, SEAL_RULE_OPTION_A)["failures"] == [
        {"rule": "R-CENSUS-8", "result": "blocked:insufficient_ic_months"}]
    assert derive_readiness(option_a)["failures"] == [
        {"rule": "R-CENSUS-1", "result": "blocked:holdout_overlaps_prior_exposure"},
        {"rule": "R-CENSUS-8", "result": "blocked:insufficient_ic_months"}]


def test_t_census_4_unusable_entry_charge_and_one_row_missing_bar(tmp_path, monkeypatch):
    entries, codes = anchors_with(**{"GAP1.US": bars([r for r in rows(0, N) if r != 600])})
    entries += [entry("GAP1", START), entry(None, START)]
    harness, result = census(tmp_path, monkeypatch, "c4", entries, codes)
    coverage = result["public"]["price_coverage"]
    assert unpriced(result)["entry_unusable_upper_bound"] == SPAN
    assert coverage["eligible_member_days"] == coverage["member_days_total"] + SPAN
    assert failing(result)["R-CENSUS-9"] == "blocked:unpriced_eligible_member_days"
    assert result["public"]["identity"]["entry_refusals_by_code"] == {"entry_missing_field": 1}
    exclusion = json.loads((harness.snapshot_dir / "census/exclusion_set.json").read_text())
    assert exclusion["g_base"] == [["GAP1.US#E1", day(600)]]
    assert result["public"]["exclusion_set"]["gap_window_count"] == 1


def test_t_census_5_power_projection_reference_table():
    table = {0.08: [(0.0275, 0.0205), (0.0225, 0.0167), (0.0195, 0.0145), (0.0174, 0.0129), (228, 126)],
             0.10: [(0.0344, 0.0256), (0.0281, 0.0209), (0.0243, 0.0181), (0.0218, 0.0162), (356, 197)],
             0.12: [(0.0413, 0.0307), (0.0337, 0.0251), (0.0292, 0.0217), (0.0261, 0.0194), (512, 283)]}
    for index, months in enumerate((120, 180, 240, 300)):
        projection = power_projection(months)
        for row in projection["band"]:
            assert (round(row["mde_eff"], 4), round(row["mde_single"], 4)) == table[row["s"]][index]
            assert (row["months_for_mde_eff_0_02"], row["months_for_mde_single_0_02"]) == table[row["s"]][4]
    projection = power_projection(120)
    assert round(projection["alpha_eff"], 7) == 0.0034014
    assert (round(projection["z_eff"], 4), round(projection["z_single"], 4)) == (3.7705, 2.8016)
    assert not power_projection(355)["kill_reachable_projection"] and power_projection(356)["kill_reachable_projection"]


def test_t_census_6_discovery_overlap_with_prior_exposures():
    months = [pd.Timestamp(d).date() for d in pd.date_range("2016-05-31", "2016-12-31", freq="ME")]
    overlap = prior_exposure_overlap(months)
    assert overlap["static_50_name_cohort"]["fraction_of_ic_months"] == pytest.approx(5 / 8)
    assert overlap["historical_evaluation"]["fraction_of_ic_months"] == 0.0
    assert prior_exposure_overlap([])["static_50_name_cohort"]["fraction_of_ic_months"] == 0.0


# ---------------------------------------------------------------- T-CENSUS-7


def test_t_census_7_eligible_unpriced_member_days_by_reason(tmp_path, monkeypatch):
    quarantined = bars(rows(400, N))
    quarantined[200] = {**quarantined[200], "low": -1.0}
    codes = {
        "QUAR.US": quarantined, "PRE.US": bars(rows(610, N)), "HOLD.US": bars(rows(0, 101)),
        "UNR.US": bars(rows(400, 701)), "MISS.US": 404, "DLST.US": bars(rows(880, N)),
    }
    entries, codes = anchors_with(**codes)
    entries += [entry("QUAR", day(450), day(550)), entry("PRE", day(600)), entry("HOLD", START, day(451)),
                entry("UNR", day(420), day(731)), entry("MISS", day(500), day(550)),
                entry("DLST", day(420), day(480), delisted=True)]
    harness, result = census(tmp_path, monkeypatch, "c7", entries, codes)
    assert unpriced(result) == {
        "no_discovery_panel": 100, "pre_first_bar": 9, "post_last_bar_deferred_holdout": 40,
        "after_unresolved_disappearance": 731 - 701, "no_vendor_bars:missing_symbol": 50, "no_bars_in_interval": 60,
    }
    exclusion = json.loads((harness.snapshot_dir / "census/exclusion_set.json").read_text())
    assert exclusion["unresolved"] == [["UNR.US#E1", day(701)]]
    in_x = {pid for pid, _ in exclusion["g_base"] + exclusion["g_term"]}
    assert not in_x & {"QUAR.US#E1", "PRE.US#E1", "HOLD.US#E1", "DLST.US#E1"}


# ---------------------------------------------------------------- T-CENSUS-8


def test_t_census_8_a_open_statuses_block_until_resumed(tmp_path, monkeypatch):
    entries, codes = anchors_with(**{"PERR.US": 500})
    entries.append(entry("PERR", START))
    harness, first = census(tmp_path, monkeypatch, "c8a", entries, codes)
    assert failing(first)["R-CENSUS-10"] == "blocked:retrieval_incomplete"
    assert first["detail"]["incomplete_codes_by_table_and_status"] == {"eod": {"PERR.US": "provider_error"}}
    harness.vendor.code("PERR.US", bars(rows(0, N)))
    assert harness.run("eod") == 0
    harness.run("verify")
    second = downstream(harness, tmp_path / "c8a_resumed")
    assert "R-CENSUS-10" not in failing(second) and second["public"]["retrieval"]["retrieval_complete"]

    entries, codes = anchors_with(**{"SKIP.US": (bars(rows(0, N)), 500)})
    entries.append(entry("SKIP", START))
    _, skipped = census(tmp_path, monkeypatch, "c8a2", entries, codes)
    assert skipped["detail"]["incomplete_codes_by_table_and_status"] == {
        "splits": {"SKIP.US": "provider_error"}, "eod": {"SKIP.US": "skipped:split_table_provider_error"}}

    def budget(h):
        h.retrieve()
        h.edit_manifest(lambda m: m["entries"].pop("eod/A01.US"))
        h.run("verify")

    _, absent = census(tmp_path, monkeypatch, "c8a3", *anchors_with(), hook=budget)
    assert absent["detail"]["incomplete_codes_by_table_and_status"] == {"eod": {"A01.US": "absent"}}
    assert failing(absent)["R-CENSUS-10"] == "blocked:retrieval_incomplete"


def test_t_census_8_b_missing_symbol_member_days_enter_r9_only(tmp_path, monkeypatch):
    entries, codes = anchors_with(**{"MISS.US": 404})
    entries.append(entry("MISS", day(500), day(550), delisted=True))
    _, result = census(tmp_path, monkeypatch, "c8b", entries, codes)
    coverage = result["public"]["price_coverage"]
    assert unpriced(result) == {"no_vendor_bars:missing_symbol": 50}
    assert coverage["eligible_member_days"] == 4 * SPAN + 50 and coverage["identity_refused_member_days"] == 0
    assert coverage["eligible_unpriced_fraction"] == pytest.approx(50 / (4 * SPAN + 50))
    assert coverage["eligible_unpriced_fraction"] > 0.021
    assert "R-CENSUS-9" in failing(result) and "R-CENSUS-3" not in failing(result)


def test_t_census_8_c_skipped_code_becomes_a_rekeyed_candidate_after_resume(tmp_path, monkeypatch):
    entries, codes = anchors_with(**{"SKP.US": (bars(rows(0, N)), 500), "SKN.US": bars(rows(0, N))})
    entries += [entry("SKP", START, day(600), name="Skip Co"), entry("SKN", day(600), name="Skip Co")]
    harness, first = census(tmp_path, monkeypatch, "c8c", entries, codes)
    assert unpriced(first)["no_vendor_bars:skipped_split_table_provider_error"] == 601 - D0
    assert first["public"]["identity"]["rekeyed_rename_candidates"] == 0
    assert failing(first)["R-CENSUS-10"] == "blocked:retrieval_incomplete"
    harness.vendor.code("SKP.US", b"[]", b"[]")
    assert harness.run("splits") == 0 and harness.run("eod") == 0
    harness.run("verify")
    second = downstream(harness, tmp_path / "c8c_resumed")
    assert second["public"]["identity"]["rekeyed_rename_candidates"] == 1
    assert unpriced(second) == {"no_vendor_bars:empty_payload": 601 - D0}


def reused(old, current, rus_bars):
    entries, codes = anchors_with(**{"RUS.US": rus_bars})
    entries += [entry("RUS", *old, name="Old Railroad", delisted=True), entry("RUS", current, name="New Software")]
    listed = [{"Code": "RUS", "Name": "New Software", "Isin": "US9"}]
    delisted = [{"Code": "RUS", "Name": "Old Railroad", "Isin": None}]
    return entries, codes, listed, delisted


def test_t_census_8_d_reused_code_accounting(tmp_path, monkeypatch):
    entries, codes, listed, delisted = reused((day(420), day(470)), day(900), bars(rows(880, N)))
    _, old_heavy = census(tmp_path, monkeypatch, "c8d1", entries, codes, listed=listed, delisted=delisted)
    assert unpriced(old_heavy) == {"no_bars_in_interval": 50}
    assert old_heavy["public"]["price_coverage"]["identity_refused_member_days"] == N - 901
    assert "R-CENSUS-9" in failing(old_heavy) and "R-CENSUS-3" not in failing(old_heavy)
    assert old_heavy["public"]["identity"]["rekeyed_rename_candidates"] == 0

    entries, codes, listed, delisted = reused((START, day(300)), day(700), bars(rows(680, N)))
    _, current_heavy = census(tmp_path, monkeypatch, "c8d2", entries, codes, listed=listed, delisted=delisted)
    assert current_heavy["public"]["price_coverage"]["identity_refusal_fraction"] > 0.051
    assert "R-CENSUS-3" in failing(current_heavy) and "R-CENSUS-9" not in failing(current_heavy)

    entries, codes, listed, delisted = reused((day(420), day(470)), day(900), 404)
    _, no_bars = census(tmp_path, monkeypatch, "c8d3", entries, codes, listed=listed, delisted=delisted)
    assert unpriced(no_bars) == {"no_vendor_bars:missing_symbol": 50 + N - 901}
    assert no_bars["public"]["price_coverage"]["eligible_member_days"] == \
        old_heavy["public"]["price_coverage"]["eligible_member_days"] + N - 901


def test_t_census_8_e_persistent_provider_errors(tmp_path, monkeypatch):
    def days(table, count):
        def hook(h):
            assert h.run("components") == 0 and h.run("symbols") == 0
            h.seal()
            assert h.run("calendar") == 0
            order = ("splits", "eod", "dividends")
            for name in order[:order.index(table)]:
                assert h.run(name) == 0
            for _ in range(count):
                assert h.run(table) == 0
                h.clock.advance(days=1)
            for name in order[order.index(table) + 1:]:
                assert h.run(name) == 0
            h.run("verify")
        return hook

    entries, codes = anchors_with(**{"PSP.US": (bars(rows(0, N)), 500)})
    entries.append(entry("PSP", START))
    _, two = census(tmp_path, monkeypatch, "c8e1", entries, codes, hook=days("splits", 2))
    assert failing(two)["R-CENSUS-10"] == "blocked:retrieval_incomplete"
    harness, three = census(tmp_path, monkeypatch, "c8e2", entries, codes, hook=days("splits", 3))
    assert "R-CENSUS-10" not in failing(three)
    manifest = harness.manifest()
    assert manifest["entries"]["splits/PSP.US"]["status"] == "unavailable:persistent_provider_error"
    assert manifest["entries"]["eod/PSP.US"]["split_evidence_basis"] == "none_discontinuity_fallback"

    entries, codes = anchors_with(**{"PEO.US": 500})
    entries.append(entry("PEO", START))
    _, eod_result = census(tmp_path, monkeypatch, "c8e3", entries, codes, hook=days("eod", 3))
    assert unpriced(eod_result) == {"no_vendor_bars:persistent_provider_error": SPAN}
    assert eod_result["public"]["retrieval"]["persistent_provider_error_member_days"] == SPAN

    close = lambda r: 100.0  # noqa: E731
    adjusted = lambda r: 99.0 if r < 700 else 100.0  # noqa: E731
    entries, codes = anchors_with(**{"PDV.US": (bars(rows(0, N), close=close, adjusted=adjusted), [], 500)})
    entries.append(entry("PDV", START))
    _, dividend_result = census(tmp_path, monkeypatch, "c8e4", entries, codes, hook=days("dividends", 3))
    coverage = dividend_result["public"]["price_coverage"]
    assert unpriced(dividend_result) == {"no_discovery_panel": SPAN}
    assert coverage["failing_pairs_by_kind"]["undeclared_step"] == 1
    assert coverage["failing_pairs_by_dividend_evidence"] == {"valid": 0, "unavailable": 1}
    assert coverage["member_days_refused_while_dividend_evidence_unavailable"] == SPAN


# ---------------------------------------------------------------- T-CENSUS-9


@pytest.mark.parametrize("new_state, reason", [
    (404, "no_vendor_bars:missing_symbol"), (b"[]", "no_vendor_bars:empty_payload"), ("quarantine", "no_discovery_panel"),
])
def test_t_census_9_refresh_accounting(tmp_path, monkeypatch, new_state, reason):
    broken = bars(rows(0, N))
    broken[700] = {**broken[700], "low": -1.0}
    state = broken if new_state == "quarantine" else new_state
    entries, codes = anchors_with(**{"RFR.US": bars(rows(0, N))})
    entries.append(entry("RFR", START))
    harness, _ = census(tmp_path, monkeypatch, "c9", entries, codes)
    harness.vendor.code("RFR.US", state)
    assert harness.run("eod", "--refresh") == 0
    harness.run("verify")
    with pytest.raises(SnapshotRefusal) as refused:
        run_census(harness.snapshot_dir, reports_dir=tmp_path / "stale", seal_out=tmp_path / "stale.json")
    assert refused.value.code == "derived_artifact_stale"
    refreshed = downstream(harness, tmp_path / "c9_after")
    _, fresh = census(tmp_path, monkeypatch, "c9fresh", entries, {**codes, "RFR.US": state})
    assert unpriced(refreshed) == unpriced(fresh) == {reason: SPAN}
    for key in ("eligible_member_days", "eligible_unpriced_member_days_total", "member_days_with_bar"):
        assert refreshed["public"]["price_coverage"][key] == fresh["public"]["price_coverage"][key]
    assert refreshed["public"]["retrieval"]["table_status_counts"] == fresh["public"]["retrieval"]["table_status_counts"]


# ---------------------------------------------------------------- T-CENSUS-10


def test_t_census_10_a_exact_repeats_collapse_in_the_seal_and_the_build(tmp_path, monkeypatch):
    members = [f"E{k:02d}" for k in range(50)]
    codes = {f"{code}.US": bars(rows(0, N), close=40.0 + k) for k, code in enumerate(members)}
    base_entries = [entry(code, START) for code in members]
    repeats = [entry(code, START) for code in members[:7]]

    def sealed(h):
        assert h.run("components") == 0 and h.run("symbols") == 0
        seal_snapshot(h.snapshot_dir, sealing_actor="t", authorization_reference="t", clock=h.clock)
        for command in ("calendar", "splits", "eod", "dividends", "verify"):
            h.run(command)

    harness, plain = census(tmp_path, monkeypatch, "c10a0", base_entries, codes, band=(45, 55), hook=sealed)
    harness_r, repeated = census(tmp_path, monkeypatch, "c10a1", base_entries + repeats, codes, band=(45, 55), hook=sealed)
    seal = json.loads((harness_r.snapshot_dir / "holdout_seal_v1.json").read_text())
    assert seal["entry_counts"]["retained"] == 50 and seal["entry_counts"]["exact_duplicate_collapsed"] == 7
    identity = repeated["public"]["identity"]
    assert identity["exact_duplicate_entries_collapsed"] == 7
    assert repeated["public"]["ever_members"]["permanent_ids"] == 51  # 50 members and the benchmark
    assert repeated["public"]["price_coverage"]["member_days_total"] == plain["public"]["price_coverage"]["member_days_total"]
    assert repeated["public"]["census_readiness"]["status"] == plain["public"]["census_readiness"]["status"]
    raw_frame = pd.read_parquet(harness_r.snapshot_dir / "membership/historical_components_raw.parquet")
    retained, _ = holdout_partition.parse_membership_entries(raw_frame, date(2007, 1, 2))
    n_raw = dict(holdout_partition.monthly_raw_counts(retained, CAL[-1].date()))
    month_end = {m["month"]: m["count"] for m in repeated["public"]["membership_breadth"]["members_per_month_end"]}
    assert month_end == {m.isoformat()[:7]: n for m, n in n_raw.items()}
    assert len(members) - len(repeats) == 43  # the refuse-both-copies rule would keep 43 of 50


def test_t_census_10_b_c_d_overlap_union_degenerate_and_unparseable(tmp_path, monkeypatch):
    members = [f"E{k:02d}" for k in range(50)]
    codes = {f"{code}.US": bars(rows(0, N), close=40.0 + k) for k, code in enumerate(members)}
    overlaps = [entry(code, day(500), day(600)) for code in members[:7]]
    entries = [entry(code, START) for code in members] + overlaps
    _, overlap = census(tmp_path, monkeypatch, "c10b", entries, codes)
    assert overlap["public"]["ever_members"]["permanent_ids"] == 51
    assert overlap["public"]["identity"]["entry_refusals_by_code"] == {"raw_overlap": 14}
    assert unpriced(overlap) == {"raw_overlap": 7 * SPAN}
    coverage = overlap["public"]["price_coverage"]
    assert coverage["eligible_member_days"] == 43 * SPAN + 7 * SPAN
    assert failing(overlap)["R-CENSUS-9"] == "blocked:unpriced_eligible_member_days"
    row_sum = 7 * SPAN + 7 * 100
    assert not re.search(rf"\b{row_sum}\b", json.dumps(overlap["public"]))  # the per-row sum is reported nowhere
    extra = [entry("E00", day(500), day(500)), entry("E01", "2005/01/03")]
    _, edge = census(tmp_path, monkeypatch, "c10c", [entry(code, START) for code in members] + extra, codes)
    assert edge["public"]["identity"]["entry_refusals_by_code"] == {"degenerate_interval": 1, "entry_unparseable_date": 1}
    assert unpriced(edge) == {"entry_unusable_upper_bound": SPAN}


def split_code(raw_volume: bool):
    after = lambda r: r >= 485  # noqa: E731
    volume = (lambda r: 2000.0) if not raw_volume else (lambda r: 2000.0 if after(r) else 1000.0)
    return (bars(rows(450, 521), close=lambda r: 50.0 if after(r) else 100.0, adjusted=50.0, volume=volume),
            [{"date": day(485), "split": "2/1"}])


def test_t_census_10_e_volume_basis_diagnostic(tmp_path, monkeypatch):
    def run(name, count, raw):
        entries, codes = anchors_with(**{f"V{k:02d}.US": split_code(raw) for k in range(count)})
        entries += [entry(f"V{k:02d}", day(455), day(500)) for k in range(count)]
        return census(tmp_path, monkeypatch, name, entries, codes)[1]["public"]["volume_basis_split_diagnostic"]

    adjusted = run("c10e1", 12, False)
    assert adjusted["a1_volume_half"] == "consistent" and adjusted["rows"] == 12 and abs(adjusted["median_ell"]) < 1e-12
    raw = run("c10e2", 12, True)
    assert raw["a1_volume_half"] == "contradicted" and raw["median_ell"] == pytest.approx(1.0)
    assert run("c10e3", 9, False)["a1_volume_half"] == "insufficient"
    for raw_rows, verdict, share in ((2, "consistent", 2 / 12), (3, "contradicted", 0.25), (4, "contradicted", 4 / 12),
                                     (5, "contradicted", 5 / 12), (6, "contradicted", 0.5)):
        mixed = volume_basis_diagnostic([(2.0, 1.0)] * raw_rows + [(2.0, 0.0)] * (12 - raw_rows))
        assert mixed["a1_volume_half"] == verdict and mixed["share_ell_above_half_at_ratio_2"] == pytest.approx(share)
        assert mixed["median_ell"] == (0.5 if raw_rows == 6 else 0.0)


def test_t_census_10_f_premise_exposure_and_report_header(tmp_path, monkeypatch):
    t = np.arange(160)
    base = 100.0 * np.exp(0.001 * t)
    witness_bars = bars(rows(450, 610), close=lambda r: base[r - 450],
                        adjusted=lambda r: base[r - 450] * (0.98 if r - 450 < 80 else 1.0),
                        volume=lambda r: 1000.0 / 0.98 if r - 450 < 80 else 1000.0)
    witness_div = [{"date": day(530), "value": 0.02 * base[79], "unadjustedValue": 0.02 * base[79]}]
    eight_rows = [430 + d for d in range(20, 301, 40)]
    factor = lambda r: 0.9875 ** sum(d > r for d in eight_rows)  # noqa: E731
    entries, codes = anchors_with(**{
        "VPW.US": (witness_bars, [], witness_div), "VPT.US": (witness_bars, [], witness_div),
        "EGT.US": (bars(rows(430, N), adjusted=lambda r: 100.0 * factor(r)), [],
                   [{"date": day(d), "value": 1.25, "unadjustedValue": 1.25} for d in eight_rows]),
        "NON.US": bars(rows(430, N)),
    })
    entries += [entry("VPW", day(449), day(560)), entry("VPT", day(449), day(560)), entry("EGT", day(429)), entry("NON", day(429))]
    harness, result = census(tmp_path, monkeypatch, "c10f", entries, codes)
    support = result["public"]["in_span_distribution_support"]
    assert support["written_episodes_with_declared_distribution_pair"] == 3
    member_days = 2 * (561 - 450) + (N - 430)
    assert support["member_days"] == member_days
    assert support["fraction_of_eligible_member_days"] == pytest.approx(member_days / result["public"]["price_coverage"]["eligible_member_days"])
    assert round(support["b_d"]["max"], 6) == 0.020203
    assert round(support["s_d"]["max"], 4) == 0.1006 and support["s_d"]["max"] == pytest.approx(-8 * math.log(0.9875))
    assert support["member_days_s_d_above_0_05"] == eight_rows[4] - 430
    assert result["public"]["vp2_revisit_required"] is True
    header = (tmp_path / "c10f_out/reports/m4_7_coverage_census.md").read_text()
    for phrase in ("VP-1", "VP-2", "B_D max", "S_D max", "O-8", "vp2_revisit_required: True", "DIAGNOSTIC_ONLY"):
        assert phrase in header


def test_t_census_9_a_stale_build_manifest_alone_refuses(tmp_path, monkeypatch):
    """Ablation witness: the census checks the build manifest's inputs digest, not only the inventory's."""
    harness, _ = census(tmp_path, monkeypatch, "c9m", *anchors_with())
    path = harness.snapshot_dir / "membership/membership_build_manifest.json"
    manifest = json.loads(path.read_text())
    manifest["discovery_inputs_sha256"] = "0" * 64
    path.write_text(json.dumps(manifest))
    with pytest.raises(SnapshotRefusal) as refused:
        run_census(harness.snapshot_dir, reports_dir=tmp_path / "r", seal_out=tmp_path / "s.json")
    assert refused.value.code == "derived_artifact_stale"


def test_census_refuses_a_missing_derived_artifact(tmp_path, monkeypatch):
    harness = Harness(tmp_path, monkeypatch, snapshot_id="missing")
    harness.vendor.entries = [entry("A01", START)]
    harness.vendor.code("A01.US", ANCHORS["A01"])
    harness.vendor.code("SPY.US", bars(rows(0, N)))
    harness.retrieve()
    build_universe(harness.snapshot_dir)
    with pytest.raises(SnapshotRefusal) as refused:
        run_census(harness.snapshot_dir, reports_dir=tmp_path / "r", seal_out=tmp_path / "s.json")
    assert (refused.value.code, str(refused.value)) == ("derived_artifact_missing", "derived_artifact_missing: terminal/terminal_validation.json")


# ---------------------------------------------------------------- attempt 2 remediation (AUDIT1-M47A2-A1, AUDIT2 A2-09 (b), (d))


def zero_turnover_code(zero_before: bool, zero_after: bool):
    def volume(r):
        if 465 <= r < 485 and zero_before or 485 <= r < 505 and zero_after:
            return 0.0
        return 2000.0
    return (bars(rows(450, 521), close=lambda r: 50.0 if r >= 485 else 100.0, adjusted=50.0, volume=volume),
            [{"date": day(485), "split": "2/1"}])


def test_zero_median_turnover_rows_stay_typed_and_counted(tmp_path, monkeypatch):
    codes = {"ZA.US": zero_turnover_code(False, True), "ZB.US": zero_turnover_code(True, False),
             "ZC.US": zero_turnover_code(True, True), "ZOK.US": zero_turnover_code(False, False)}
    entries, codes = anchors_with(**codes)
    entries += [entry(code, day(455), day(500)) for code in ("ZA", "ZB", "ZC", "ZOK")]
    _, result = census(tmp_path, monkeypatch, "zero", entries, codes)
    diagnostic = result["public"]["volume_basis_split_diagnostic"]
    assert diagnostic["rows_undefined_zero_median_turnover"] == 3 and diagnostic["rows"] == 1
    assert diagnostic["median_ell"] == 0.0 and diagnostic["a1_volume_half"] == "insufficient"
    mixed = volume_basis_diagnostic([(2.0, 0.0)] * 12 + [(2.0, None)] * 3)
    assert (mixed["rows"], mixed["rows_undefined_zero_median_turnover"], mixed["a1_volume_half"]) == (12, 3, "consistent")


def test_in_band_years_count_month_ends():
    from research.m4_7_coverage_census import in_band_month_ends

    assert in_band_month_ends(date(1990, 1, 31), date(2005, 12, 31)) == 192
    assert in_band_month_ends(date(1990, 1, 31), date(2005, 12, 31)) / 12 == 16.0
    assert in_band_month_ends(date(1990, 1, 31), date(2005, 11, 30)) == 191
    assert in_band_month_ends(None, date(2005, 11, 30)) == 0 and in_band_month_ends(date(2006, 1, 31), date(2005, 1, 31)) == 0
    assert derive_readiness({**CLEAN, "in_band_years": 192 / 12})["rules"]["R-CENSUS-1"]["passed"]
    assert not derive_readiness({**CLEAN, "in_band_years": 191 / 12})["rules"]["R-CENSUS-1"]["passed"]
