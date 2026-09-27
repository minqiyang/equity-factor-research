"""M4.8 Stage A: discovery segments and segment-local validation (plan 2.5, 2.7).

T-SEG-1..3, T-SEG-8, T-SEG-9 (segment rows), T-UNI-SEG-1..8, T-ID-SEAL-1..3,
T-VOL-SEAL-1..4, T-SEAL-BR-1. Every snapshot is retrieved through the real
retrieval path and built by the real universe build. Floating-point panel
values compare at 1e-12 relative, and statuses, refusals, ranks, and holdings
compare exactly (Seat 1 R3-A03, Seat 2 R3-A1).
"""

from __future__ import annotations

import json
import math
from datetime import date

import numpy as np
import pandas as pd
import pytest

from data.holdout_partition import SnapshotRefusal
from features.liquidity import calculate_amihud_illiquidity
from m4_7_snapshot_support import entry, record_reads
from m4_8_snapshot_support import (
    ALL_ROWS,
    CAL2,
    D0_PRE,
    HE_ROW,
    HOLDOUT_END,
    HOLDOUT_START,
    HS_ROW,
    N_ROWS,
    bars2,
    day2,
    dividend_row,
    manifest_entry,
    row_of,
    side_file,
    snapshot_v2,
    split_row,
)
from research.m4_7_common_support import scheduled_reset_rows
from research.m4_7_universe_build import (
    discovery_segments,
    reset_in_month,
    segment_ic_resets,
)
from research.real_data_multifactor_diagnostic import build_adjusted_research_panels


LAST_BOOK_PRE = row_of("2019-06-28")
EOD_COLUMNS = ["date", "open", "high", "low", "close", "adjusted_close", "volume"]


def build(snap):
    return json.loads((snap / "membership/membership_build_manifest.json").read_bytes())


def panel(snap, side, pid):
    path = snap / "panel" / side / f"{pid}.parquet"
    return pd.read_parquet(path) if path.is_file() else None


def csv(snap, name):
    return pd.read_csv(snap / name, dtype=str, keep_default_na=False)


def checks_of(snap, pid):
    return {c["side"]: c for c in build(snap)["episode_checks"] if c["permanent_id"] == pid}


def assert_frames_close(left, right):
    assert list(left.columns) == list(right.columns) and len(left) == len(right)
    for column in left.columns:
        if pd.api.types.is_float_dtype(left[column]):
            np.testing.assert_allclose(left[column].to_numpy(), right[column].to_numpy(), rtol=1e-12, atol=0.0)
        else:
            assert left[column].tolist() == right[column].tolist(), column


def split_series(splits: dict[int, float]):
    """``(raw_close_divisor(t), later_product(t))`` from ``{row: ratio}``: splits at or before and after ``t``."""
    before = np.ones(N_ROWS)
    after = np.ones(N_ROWS)
    for row, ratio in splits.items():
        before[row:] *= ratio
        after[:row] *= ratio
    return before, after


def served_asset(splits: dict[int, float], base, raw_volume, rows=ALL_ROWS, adjusted_scale=1.0):
    """Vendor rows for a security with raw closes, split-adjusted volume, and adjusted closes on the last basis."""
    before, after = split_series(splits)
    close = {r: base(r) / before[r] for r in rows}
    adjusted = {r: close[r] / after[r] * (adjusted_scale if r < HS_ROW else 1.0) for r in rows}
    served = {r: raw_volume(r) * after[r] for r in rows}
    eod = bars2(rows, close=lambda r: close[r], adjusted=lambda r: adjusted[r], volume=lambda r: served[r])
    ratios = [split_row(r, f"{ratio}/1" if ratio >= 1 else f"1/{round(1 / ratio)}") for r, ratio in sorted(splits.items())]
    return eod, ratios


# ---------------------------------------------------------------- T-SEG


def test_t_seg_1_discovery_segments_return_the_documented_rows():
    pre, post = discovery_segments(CAL2, HOLDOUT_START, HOLDOUT_END, D0_PRE)
    dates = {name: CAL2[getattr(pre, name)].date().isoformat() for name in (
        "anchor_row", "first_reset_row", "last_ic_reset_row", "last_book_row", "feature_floor_row", "feature_ceiling_row")}
    assert dates == {"anchor_row": "2018-06-28", "first_reset_row": "2018-06-29", "last_ic_reset_row": "2019-05-31",
                     "last_book_row": "2019-06-28", "feature_floor_row": "2018-01-02", "feature_ceiling_row": "2019-06-28"}
    assert (pre.segment_id, pre.side, post.segment_id, post.side) == ("pre", "discovery_pre", "post", "discovery_post")
    resets = scheduled_reset_rows(CAL2)
    assert post.first_reset_row == int(resets[resets >= HE_ROW + 253][0])
    assert post.anchor_row == post.first_reset_row - 1 and post.feature_floor_row == HE_ROW
    assert post.last_book_row == int(resets[-1]) == N_ROWS - 1 and post.last_ic_reset_row == int(resets[-2])


def test_t_seg_2_no_feature_row_lies_in_the_seal():
    pre, post = discovery_segments(CAL2, HOLDOUT_START, HOLDOUT_END, D0_PRE)
    assert pre.feature_ceiling_row < HS_ROW and post.feature_floor_row >= HE_ROW
    for segment in (pre, post):
        rows = range(segment.feature_floor_row, segment.feature_ceiling_row + 1)
        assert not any(HS_ROW <= r < HE_ROW for r in rows)
    # r_pre_last excludes the reset whose horizon equals holdout_start (the 2019-06-28 reset).
    assert CAL2[pre.last_book_row] < pd.Timestamp(HOLDOUT_START)
    assert CAL2[reset_in_month(CAL2, date(2019, 6, 1))] == pd.Timestamp("2019-06-28")


def test_t_seg_3_pre_ic_months_equal_the_reset_count_and_an_empty_segment_refuses():
    pre, _ = discovery_segments(CAL2, HOLDOUT_START, HOLDOUT_END, D0_PRE)
    resets = scheduled_reset_rows(CAL2)
    expected = [r for r in resets if pre.first_reset_row <= r <= pre.last_ic_reset_row]
    assert list(segment_ic_resets(CAL2, pre)) == expected and len(expected) == 12
    with pytest.raises(SnapshotRefusal) as refused:
        discovery_segments(CAL2, HOLDOUT_START, HOLDOUT_END, date(2019, 6, 28))
    assert refused.value.code == "discovery_segment_empty"


def test_t_seg_9_one_anchor_row_precedes_each_first_reset():
    for segment in discovery_segments(CAL2, HOLDOUT_START, HOLDOUT_END, D0_PRE):
        accounting = range(segment.anchor_row, segment.last_book_row + 1)
        assert [r for r in accounting if r < segment.first_reset_row] == [segment.anchor_row]
        assert segment.anchor_row == segment.first_reset_row - 1


def test_t_seg_8_no_check_pairs_a_pre_side_bar_with_a_post_side_bar(tmp_path, monkeypatch):
    # The adjusted-to-close ratio differs between the sides; a pair across the seal would fail the in-span check.
    across = bars2(ALL_ROWS, close=lambda r: 100.0 if r < HE_ROW else 500.0, adjusted=lambda r: 50.0 if r < HE_ROW else 500.0)
    gap_pre = [r for r in ALL_ROWS if not 200 <= r < 205]
    jump_pre = bars2(gap_pre, close=lambda r: 100.0 if r < 200 else 900.0)
    harness = snapshot_v2(tmp_path, monkeypatch, "S8", [entry("AAA", "2018-01-02"), entry("JMP", "2018-01-02")],
                          {"AAA.US": across, "JMP.US": jump_pre})
    snap = harness.snapshot_dir
    checks = checks_of(snap, "AAA.US#E1")
    assert checks["discovery_pre"]["refusal"] is None and checks["discovery_post"]["refusal"] is None
    assert checks["discovery_pre"]["pairs"] == HS_ROW - 1 and checks["discovery_post"]["pairs"] == N_ROWS - HE_ROW - 1
    pre, post = panel(snap, "discovery_pre", "AAA.US#E1"), panel(snap, "discovery_post", "AAA.US#E1")
    assert pre["date"].max() < pd.Timestamp(HOLDOUT_START) and post["date"].min() >= pd.Timestamp(HOLDOUT_END)
    # E5 still evaluates an in-side gap: the 9x jump across the pre-side gap refuses the code.
    assert [r for r in csv(snap, "identity/interval_results.csv").to_dict(orient="records")
            if r["vendor_code"] == "JMP.US"][0]["resolution"] == "ambiguous_reuse_discontinuity"


# ---------------------------------------------------------------- T-UNI-SEG


def dividend_payer(rows, dividend_rows, amount=1.0, close=100.0):
    """Constant close with dividends; adjusted closes carry the prior-close factor of every later dividend."""
    factors = {r: 1.0 - amount / close for r in dividend_rows}
    adjusted = {r: close * math.prod(f for d, f in factors.items() if d > r) for r in rows}
    return bars2(rows, close=close, adjusted=lambda r: adjusted[r]), [dividend_row(d, amount, amount) for d in dividend_rows]


def test_t_uni_seg_1_and_4_a_dividend_payer_and_the_benchmark_pass_both_sides(tmp_path, monkeypatch):
    payouts = [60, 120, HS_ROW - 30, HS_ROW + 60, HS_ROW + 190, HE_ROW + 40, HE_ROW + 200]
    eod, dividends = dividend_payer(ALL_ROWS, payouts)
    harness = snapshot_v2(tmp_path, monkeypatch, "U1", [entry("DIV", "2018-01-02")],
                          {"DIV.US": (eod, [], dividends), "SPY.US": (eod, [], dividends)})
    snap = harness.snapshot_dir
    for pid in ("DIV.US#E1", "SPY.US#E1"):
        checks = checks_of(snap, pid)
        assert checks["discovery_pre"]["refusal"] is None and checks["discovery_post"]["refusal"] is None, pid
        assert checks["discovery_pre"]["segment_anchor"] is True and checks["discovery_post"]["segment_anchor"] is False
        assert panel(snap, "discovery_pre", pid) is not None and panel(snap, "discovery_post", pid) is not None
    assert checks_of(snap, "DIV.US#E1")["discovery_pre"]["dividend_pairs"] == 3


def test_t_uni_seg_2_a_seal_split_refuses_nothing_and_pre_side_scale_cancels(tmp_path, monkeypatch):
    def build_with(scale, name):
        eod, ratios = served_asset({HS_ROW + 40: 2.0}, lambda r: 100.0 + (r % 7), lambda r: 1000.0 + r,
                                   adjusted_scale=scale)
        return snapshot_v2(tmp_path / name, monkeypatch, name, [entry("SPL", "2018-01-02")], {"SPL.US": (eod, ratios)})

    plain, scaled = build_with(1.0, "U2A").snapshot_dir, build_with(3.7, "U2B").snapshot_dir
    assert checks_of(plain, "SPL.US#E1")["discovery_pre"]["refusal"] is None
    for side in ("discovery_pre", "discovery_post"):
        assert_frames_close(panel(plain, side, "SPL.US#E1"), panel(scaled, side, "SPL.US#E1"))
    for name in ("identity/interval_results.csv", "membership/constituent_intervals.csv"):
        assert (plain / name).read_bytes() == (scaled / name).read_bytes()
    keep = ("refusal", "outcome", "split_basis", "in_span", "pairs", "segment_anchor")
    assert [{k: c[k] for k in keep} for c in build(plain)["episode_checks"]] == \
        [{k: c[k] for k in keep} for c in build(scaled)["episode_checks"]]


def test_t_uni_seg_3_an_unexplained_step_inside_one_segment_still_refuses(tmp_path, monkeypatch):
    stepped = bars2(ALL_ROWS, close=100.0, adjusted=lambda r: 95.0 if r < 150 else 100.0)
    harness = snapshot_v2(tmp_path, monkeypatch, "U3", [entry("STP", "2018-01-02")], {"STP.US": stepped})
    check = checks_of(harness.snapshot_dir, "STP.US#E1")["discovery_pre"]
    assert check["refusal"].startswith("split_basis_unverified:")
    assert checks_of(harness.snapshot_dir, "STP.US#E1")["discovery_post"]["refusal"] is None


def test_t_uni_seg_5_a_code_without_later_rows_keeps_the_carried_final_bar_rules(tmp_path, monkeypatch):
    last = row_of("2019-03-28")
    clean = bars2(range(0, last + 1))
    deviating = bars2(range(0, last + 1), close=100.0, adjusted=90.0)
    harness = snapshot_v2(tmp_path, monkeypatch, "U5",
                          [entry("CLN", "2018-01-02", "2019-03-29"), entry("DEV", "2018-01-02", "2019-03-29")],
                          {"CLN.US": clean, "DEV.US": deviating})
    snap = harness.snapshot_dir
    assert checks_of(snap, "CLN.US#E1")["discovery_pre"]["refusal"] is None
    assert checks_of(snap, "CLN.US#E1")["discovery_pre"]["segment_anchor"] is False
    assert checks_of(snap, "DEV.US#E1")["discovery_pre"]["refusal"] == "split_basis_unverified:unexplained_deviation"


def test_t_uni_seg_6_a_member_ending_inside_the_seal_passes_with_no_holdout_read(tmp_path, monkeypatch):
    last = HS_ROW + 80
    rows = range(0, last + 1)
    eod, ratios = served_asset({HS_ROW + 50: 2.0}, lambda r: 100.0, lambda r: 1000.0, rows=rows)
    factor = 1.0 - 1.0 / 100.0
    eod = [{**bar, "adjusted_close": bar["adjusted_close"] * (factor if row < HS_ROW + 20 else 1.0)}
           for row, bar in zip(rows, eod)]
    harness = snapshot_v2(tmp_path, monkeypatch, "U6", [entry("END", "2018-01-02", day2(last + 1))],
                          {"END.US": (eod, ratios, [dividend_row(HS_ROW + 20, 1.0, 1.0)])}, build=False)
    snap = harness.snapshot_dir
    from research.m4_7_universe_build import build_universe

    with record_reads(snap) as reads:
        manifest = build_universe(snap, D0_PRE)
    assert reads.forbidden() == [] and manifest["access_log"]["holdout_partition_opens"] == 0
    check = checks_of(snap, "END.US#E1")["discovery_pre"]
    assert check["refusal"] is None and check["segment_anchor"] is True


def test_t_uni_seg_7_an_sl5_pre_side_id_passes_anchored_at_the_last_pre_side_bar(tmp_path, monkeypatch):
    rows = [r for r in ALL_ROWS if not HS_ROW + 10 <= r < HS_ROW + 14]
    eod, ratios = served_asset({HS_ROW + 100: 3.0}, lambda r: 80.0 + (r % 5), lambda r: 2000.0, rows=rows)
    harness = snapshot_v2(tmp_path, monkeypatch, "U7", [entry("GAP", "2018-01-02")], {"GAP.US": (eod, ratios)})
    snap = harness.snapshot_dir
    assert build(snap)["seal_gap_identity_split"] == 1
    assert checks_of(snap, "GAP.US#E1")["discovery_pre"]["refusal"] is None
    assert checks_of(snap, "GAP.US#E1")["discovery_pre"]["segment_anchor"] is True
    assert checks_of(snap, "GAP.US#E2")["discovery_post"]["refusal"] is None
    assert panel(snap, "discovery_post", "GAP.US#E1") is None and panel(snap, "discovery_pre", "GAP.US#E2") is None


def test_t_uni_seg_8_a_code_ending_before_the_seal_with_a_seal_dated_distribution_passes(tmp_path, monkeypatch):
    last = HS_ROW - 6
    eod = bars2(range(0, last + 1), close=100.0, adjusted=99.0)
    harness = snapshot_v2(tmp_path, monkeypatch, "U8", [entry("LTD", "2018-01-02", day2(last + 1))],
                          {"LTD.US": (eod, [], [dividend_row(HS_ROW + 3, 1.0, 1.0)])})
    snap = harness.snapshot_dir
    assert manifest_entry(snap, "dividends", "LTD.US")["has_row_on_or_after_holdout_start"] is True
    check = checks_of(snap, "LTD.US#E1")["discovery_pre"]
    assert check["refusal"] is None and check["segment_anchor"] is True


# ---------------------------------------------------------------- T-ID-SEAL


def test_t_id_seal_1_continuous_bar_dates_across_the_seal_keep_one_permanent_id(tmp_path, monkeypatch):
    harness = snapshot_v2(tmp_path, monkeypatch, "I1", [entry("AAA", "2018-01-02")], {"AAA.US": bars2(ALL_ROWS)})
    snap = harness.snapshot_dir
    master = csv(snap, "identity/security_master.csv")
    assert master.loc[master["vendor_code"] == "AAA.US", "permanent_id"].tolist() == ["AAA.US#E1"]
    assert build(snap)["seal_gap_identity_split"] == 0
    assert panel(snap, "discovery_pre", "AAA.US#E1") is not None and panel(snap, "discovery_post", "AAA.US#E1") is not None


def test_t_id_seal_2_a_ticker_reused_inside_the_seal_splits_into_two_ids(tmp_path, monkeypatch):
    old, new = range(0, HS_ROW + 50), range(HS_ROW + 120, N_ROWS)
    small_gap = [r for r in ALL_ROWS if not HS_ROW + 30 <= r < HS_ROW + 33]
    harness = snapshot_v2(tmp_path, monkeypatch, "I2", [
        entry("REU", "2018-01-02", day2(HS_ROW + 50), name="Old Co"), entry("REU", day2(HS_ROW + 120), name="New Co"),
        entry("HOP", "2018-01-02")], {"REU.US": bars2([*old, *new]), "HOP.US": bars2(small_gap)},
        listed=[{"Code": "HOP", "Name": "Hopper Renamed Corp", "Isin": "US0000000009"}])
    snap = harness.snapshot_dir
    assert build(snap)["seal_gap_identity_split"] == 2
    assert build(snap)["name_mismatch_recorded"] == 1
    intervals = csv(snap, "identity/interval_results.csv")
    reused = intervals[intervals["vendor_code"] == "REU.US"]
    assert sorted(reused["permanent_id"]) == ["REU.US#E1", "REU.US#E2"]
    hop = intervals[intervals["vendor_code"] == "HOP.US"]
    assert hop["permanent_id"].tolist() == ["HOP.US#E1", "HOP.US#E2"]
    assert hop["exit_class"].tolist()[0] == "seal_gap_identity_split"
    assert hop["interval_id"].tolist()[1].endswith("#seal_split_2")
    constituents = csv(snap, "membership/constituent_intervals.csv")
    hop_rows = constituents[constituents["symbol"] == "HOP.US"]
    assert hop_rows["end_date"].tolist()[0] == hop_rows["start_date"].tolist()[1] == day2(HS_ROW + 33)
    assert "delisting_candidate" not in set(hop["exit_class"])
    assert reused["exit_class"].tolist() == ["delisting_candidate", "index_removal_still_trading"]


def test_t_id_seal_3_an_isin_conflict_across_the_seal_still_refuses(tmp_path, monkeypatch):
    harness = snapshot_v2(tmp_path, monkeypatch, "I3", [entry("ISN", "2018-01-02")], {"ISN.US": bars2(ALL_ROWS)},
                          listed=[{"Code": "ISN", "Name": "ISN Inc", "Isin": "US0000000001"}],
                          delisted=[{"Code": "ISN", "Name": "ISN Inc", "Isin": "US0000000002"}])
    intervals = csv(harness.snapshot_dir, "identity/interval_results.csv")
    assert intervals.loc[intervals["vendor_code"] == "ISN.US", "resolution"].tolist() == ["ambiguous_reuse_isin_conflict"]


# ---------------------------------------------------------------- T-VOL-SEAL


def _raw(i):
    return (lambda r: 50.0 + i + 10.0 * math.sin(r / 20.0 + i)), (lambda r: 1.0e5 + 1000.0 * i + 50.0 * (r % 17))


SPLIT_PLANS = (
    lambda: {HS_ROW + 30: 2.0},
    lambda: {HE_ROW + 30: 3.0},
    lambda: {HS_ROW + 60: 0.1},
    lambda: {150: 2.0, HS_ROW + 90: 3.0, HE_ROW + 50: 0.1},
)


def test_t_vol_seal_1_pre_side_dollar_volume_and_amihud_match_the_raw_basis_oracle(tmp_path, monkeypatch):
    codes, entries, oracle_close, oracle_volume, oracle_return = {}, [], {}, {}, {}
    pre_rows = range(0, LAST_BOOK_PRE + 1)
    for i in range(100):
        code = f"V{i:03d}"
        base, raw_volume = _raw(i)
        splits = SPLIT_PLANS[i % 4]()
        eod, ratios = served_asset(splits, base, raw_volume)
        codes[f"{code}.US"] = (eod, ratios)
        entries.append(entry(code, "2018-01-02"))
        before, _ = split_series(splits)
        oracle_close[f"{code}.US#E1"] = [base(r) / before[r] for r in pre_rows]
        oracle_volume[f"{code}.US#E1"] = [raw_volume(r) for r in pre_rows]
        oracle_return[f"{code}.US#E1"] = [math.nan] + [base(r) / base(r - 1) - 1.0 for r in pre_rows[1:]]
    harness = snapshot_v2(tmp_path, monkeypatch, "VOL1", entries, codes)
    snap = harness.snapshot_dir
    fields = {name: {} for name in ("open", "high", "low", "close", "adjusted_close", "volume", "split_factor")}
    for pid in oracle_close:
        frame = panel(snap, "discovery_pre", pid).set_index("date")
        for name in fields:
            fields[name][pid] = frame[name]
    field_panels = {name: pd.DataFrame(values) for name, values in fields.items()}
    research = build_adjusted_research_panels(field_panels)
    index = CAL2[:LAST_BOOK_PRE + 1]
    raw_dollar = pd.DataFrame({pid: np.array(oracle_close[pid]) * np.array(oracle_volume[pid]) for pid in oracle_close},
                              index=index)
    np.testing.assert_allclose(research["dollar_volume"].to_numpy(), raw_dollar.to_numpy(), rtol=1e-12)
    oracle_returns = pd.DataFrame(oracle_return, index=index)
    ours = calculate_amihud_illiquidity(research["returns"], research["dollar_volume"], 63)
    oracle = calculate_amihud_illiquidity(oracle_returns, raw_dollar, 63)
    np.testing.assert_allclose(ours.to_numpy(), oracle.to_numpy(), rtol=1e-9, equal_nan=True)
    for row in (100, 250, LAST_BOOK_PRE):
        ranked, expected = ours.iloc[row].rank(method="first"), oracle.iloc[row].rank(method="first")
        assert ranked.tolist() == expected.tolist()
        assert set(ours.iloc[row].nlargest(10).index) == set(oracle.iloc[row].nlargest(10).index)


def _two_seal_variants(tmp_path, monkeypatch, plans):
    snaps = []
    for label, seal in plans:
        codes, entries = {}, []
        for i in range(4):
            base, raw_volume = _raw(i)
            eod, ratios = served_asset({100: 2.0, **seal(i)}, base, raw_volume)
            dividends = [dividend_row(HS_ROW + 70, 0.4, 0.4)] if label == "B" else []
            codes[f"W{i}.US"] = (eod, ratios, dividends)
            entries.append(entry(f"W{i}", "2018-01-02"))
        snaps.append(snapshot_v2(tmp_path / label, monkeypatch, f"VS{label}", entries, codes).snapshot_dir)
    return snaps


def test_t_vol_seal_2_different_seal_splits_give_equal_pre_side_volume_and_outputs(tmp_path, monkeypatch):
    first, second = _two_seal_variants(tmp_path, monkeypatch, [
        ("A", lambda i: {HS_ROW + 40: 2.0}), ("B", lambda i: {HS_ROW + 20: 0.1, HS_ROW + 200: 3.0})])
    for i in range(4):
        code, pid = f"W{i}.US", f"W{i}.US#E1"
        a, b = side_file(first, "eod", code, "discovery_pre"), side_file(second, "eod", code, "discovery_pre")
        np.testing.assert_allclose(a["volume"].to_numpy(), b["volume"].to_numpy(), rtol=1e-12, atol=0.0)
        np.testing.assert_array_equal(a["close"].to_numpy(), b["close"].to_numpy())
        assert_frames_close(panel(first, "discovery_pre", pid), panel(second, "discovery_pre", pid))
        for snap in (first, second):
            assert list(side_file(snap, "eod", code, "discovery_pre").columns) == EOD_COLUMNS
            for side in ("discovery_pre", "discovery_post"):
                dates = pd.DatetimeIndex(side_file(snap, "splits", code, side)["date"])
                assert not ((dates >= pd.Timestamp(HOLDOUT_START)) & (dates < pd.Timestamp(HOLDOUT_END))).any()
            entry_keys = set(manifest_entry(snap, "eod", code))
            assert not {key for key in entry_keys if "factor" in key or "ratio" in key}
    keep = ("refusal", "outcome", "pairs", "segment_anchor")
    pre_checks = [[{k: c[k] for k in keep} for c in build(s)["episode_checks"] if c["side"] == "discovery_pre"]
                  for s in (first, second)]
    assert pre_checks[0] == pre_checks[1]


def test_t_vol_seal_3_dividend_only_and_composed_splits_and_the_post_side_basis(tmp_path, monkeypatch):
    payouts = [70, HS_ROW + 40, HE_ROW + 30]
    div_eod, dividends = dividend_payer(ALL_ROWS, payouts)
    div_eod = [{**bar, "volume": 777.0 + row} for row, bar in zip(ALL_ROWS, div_eod)]
    splits = {150: 2.0, HS_ROW + 90: 3.0, HE_ROW + 50: 0.1}
    base, raw_volume = _raw(2)
    split_eod, ratios = served_asset(splits, base, raw_volume)
    harness = snapshot_v2(tmp_path, monkeypatch, "VOL3", [entry("DVO", "2018-01-02"), entry("CMP", "2018-01-02")],
                          {"DVO.US": (div_eod, [], dividends), "CMP.US": (split_eod, ratios)})
    snap = harness.snapshot_dir
    served_pre = [777.0 + r for r in range(0, HS_ROW)]
    assert side_file(snap, "eod", "DVO.US", "discovery_pre")["volume"].tolist() == served_pre
    written = side_file(snap, "eod", "CMP.US", "discovery_pre")["volume"].to_numpy()
    expected = np.array([raw_volume(r) * (2.0 if r < 150 else 1.0) for r in range(0, HS_ROW)])
    np.testing.assert_allclose(written, expected, rtol=1e-12)
    post = panel(snap, "discovery_post", "CMP.US#E1").set_index("date")
    served_post = np.array([raw_volume(r) * (0.1 if r < HE_ROW + 50 else 1.0) for r in range(HE_ROW, N_ROWS)])
    np.testing.assert_allclose(post["volume"].to_numpy(), served_post, rtol=1e-12)
    np.testing.assert_allclose(post["split_factor"].to_numpy(),
                               [0.1 if r < HE_ROW + 50 else 1.0 for r in range(HE_ROW, N_ROWS)], rtol=1e-12)


def test_t_vol_seal_4_missing_or_invalid_later_split_evidence_types_missing_volume(tmp_path, monkeypatch):
    harness = snapshot_v2(tmp_path, monkeypatch, "VOL4",
                          [entry("MIS", "2018-01-02"), entry("INV", "2018-01-02"), entry("OKK", "2018-01-02")],
                          {"MIS.US": (bars2(ALL_ROWS), 404), "INV.US": (bars2(ALL_ROWS), [split_row(HS_ROW + 10, "0/1")]),
                           "OKK.US": bars2(ALL_ROWS)})
    snap = harness.snapshot_dir
    assert manifest_entry(snap, "eod", "MIS.US")["pre_side_volume_basis"] == "volume_basis_unverified:split_evidence_missing"
    assert manifest_entry(snap, "eod", "INV.US")["pre_side_volume_basis"] == "volume_basis_unverified:later_split_invalid"
    assert manifest_entry(snap, "eod", "OKK.US")["pre_side_volume_basis"] == "pre_seal_volume_share_basis_v1"
    statuses = build(snap)["pre_side_volume_basis_by_code"]
    assert statuses["MIS.US"].startswith("volume_basis_unverified:") and statuses["INV.US"].startswith("volume_basis_unverified:")
    for code in ("MIS.US", "INV.US"):
        assert side_file(snap, "eod", code, "discovery_pre")["volume"].isna().all()
        assert side_file(snap, "eod", code, "discovery_post")["volume"].notna().all()
        frame = panel(snap, "discovery_pre", f"{code}#E1").set_index("date")
        fields = {name: pd.DataFrame({code: frame[name]}) for name in
                  ("open", "high", "low", "close", "adjusted_close", "volume", "split_factor")}
        research = build_adjusted_research_panels(fields)
        assert calculate_amihud_illiquidity(research["returns"], research["dollar_volume"], 63).isna().all().all()


# ---------------------------------------------------------------- T-SEAL-BR-1


def test_t_seal_br_1_pre_side_bars_after_the_last_book_row_never_reach_an_output(tmp_path, monkeypatch):
    def variant(label, late_close):
        eod = bars2(ALL_ROWS, close=lambda r: late_close if LAST_BOOK_PRE < r < HS_ROW else 100.0 + (r % 3),
                    adjusted=lambda r: (late_close if LAST_BOOK_PRE < r < HS_ROW else 100.0 + (r % 3)) * 0.5
                    if r < HS_ROW else 100.0 + (r % 3),
                    volume=lambda r: 5.0e5 if LAST_BOOK_PRE < r < HS_ROW else 1000.0)
        return snapshot_v2(tmp_path / label, monkeypatch, f"BR{label}", [entry("BRK", "2018-01-02")],
                           {"BRK.US": (eod, [split_row(HS_ROW + 25, "2/1")])}).snapshot_dir

    first, second = variant("A", 100.0), variant("B", 131.0)
    for side in ("discovery_pre", "discovery_post"):
        for pid in ("BRK.US#E1", "SPY.US#E1"):
            assert (first / "panel" / side / f"{pid}.parquet").read_bytes() == \
                (second / "panel" / side / f"{pid}.parquet").read_bytes()
    for name in ("identity/interval_results.csv", "membership/constituent_intervals.csv",
                 "identity/distribution_support.parquet"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    counters = {"episode_checks", "written_max_cumulative_drift_by_bucket", "discovery_inputs_sha256", "output_sha256",
                "pre_side_volume_basis_by_code"}
    left, right = ({k: v for k, v in build(s).items() if k not in counters} for s in (first, second))
    assert left == right
    masters = [csv(s, "identity/security_master.csv").drop(columns=["resolution_evidence"]) for s in (first, second)]
    assert masters[0].equals(masters[1])


def test_a_pre_side_dividend_without_unadjusted_value_before_a_seal_split_is_typed_undefined(tmp_path, monkeypatch):
    ex_row = 120
    close = {r: 100.0 if r < HS_ROW + 40 else 50.0 for r in ALL_ROWS}
    adjusted = {r: close[r] / (2.0 if r < HS_ROW + 40 else 1.0) * (0.99 if r < ex_row else 1.0) for r in ALL_ROWS}
    eod = bars2(ALL_ROWS, close=lambda r: close[r], adjusted=lambda r: adjusted[r])
    harness = snapshot_v2(tmp_path, monkeypatch, "AMT", [entry("AMT", "2018-01-02")],
                          {"AMT.US": (eod, [split_row(HS_ROW + 40, "2/1")], [dividend_row(ex_row, 0.5)])})
    snap = harness.snapshot_dir
    assert build(snap)["dividend_rows_amount_undefined"] == 1
    failing = checks_of(snap, "AMT.US#E1")["discovery_pre"]["failing_pairs"]
    assert failing and failing[0]["residual"] is None


@pytest.mark.parametrize("ratio, resume", [(2.0, HS_ROW + 1), (0.1, HS_ROW + 1), (2.0, HE_ROW + 5), (3.0, HS_ROW + 1)],
                         ids=["forward_seal_gap", "reverse_seal_gap", "forward_post_resume", "forward_with_seal_split"])
def test_a_pre_side_split_after_the_anchor_bar_keeps_dollar_volume_on_the_raw_basis(tmp_path, monkeypatch, ratio, resume):
    # M48A-A1-M01 / A2-ADV-1: bars stop at HS_ROW - 11, a split row sits at HS_ROW - 5, and bars resume later.
    tau = HS_ROW - 11
    splits = {HS_ROW - 5: ratio}
    if resume == HS_ROW + 1 and ratio == 3.0:
        splits[HS_ROW + 60] = 2.0
    rows = [*range(0, tau + 1), *range(resume, N_ROWS)]
    base, raw_volume = (lambda r: 80.0 + 7.0 * math.sin(r / 9.0)), (lambda r: 1.0e5 + 37.0 * (r % 13))
    eod, ratios = served_asset(splits, base, raw_volume, rows=rows)
    harness = snapshot_v2(tmp_path, monkeypatch, "AFT", [entry("AFT", "2018-01-02")], {"AFT.US": (eod, ratios)})
    snap = harness.snapshot_dir
    manifest = build(snap)
    assert manifest["pre_side_split_rows_after_anchor"] == 1 and manifest["seal_gap_identity_split"] == 1
    assert manifest["pre_side_volume_basis_by_code"]["AFT.US"] == "pre_seal_volume_share_basis_v1"
    assert checks_of(snap, "AFT.US#E1")["discovery_pre"]["refusal"] is None
    frame = panel(snap, "discovery_pre", "AFT.US#E1").set_index("date")
    assert frame.index.max() == CAL2[LAST_BOOK_PRE] < CAL2[tau]
    before, _ = split_series(splits)
    pre_rows = range(0, LAST_BOOK_PRE + 1)
    fields = {name: pd.DataFrame({"AFT": frame[name]}) for name in
              ("open", "high", "low", "close", "adjusted_close", "volume", "split_factor")}
    research = build_adjusted_research_panels(fields)
    oracle_dollar = pd.DataFrame({"AFT": [base(r) / before[r] * raw_volume(r) for r in pre_rows]}, index=frame.index)
    np.testing.assert_allclose(research["dollar_volume"].to_numpy(), oracle_dollar.to_numpy(), rtol=1e-12)
    np.testing.assert_allclose(frame["split_factor"].to_numpy(), np.full(len(pre_rows), ratio), rtol=1e-12)
    oracle_returns = pd.DataFrame({"AFT": [math.nan] + [base(r) / base(r - 1) - 1.0 for r in pre_rows[1:]]},
                                  index=frame.index)
    ours = calculate_amihud_illiquidity(research["returns"], research["dollar_volume"], 63)
    oracle = calculate_amihud_illiquidity(oracle_returns, oracle_dollar, 63)
    assert ours.notna().to_numpy().sum() > 0
    np.testing.assert_allclose(ours.to_numpy(), oracle.to_numpy(), rtol=1e-9, equal_nan=True)
