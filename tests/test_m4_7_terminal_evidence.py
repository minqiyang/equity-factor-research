"""M4.7 stage a-2 terminal evidence oracles (plan section 3; T-TERM-1..11 validator and projection parts).

The engine parts of T-TERM-1, 2, and 4 are a-0 oracles in
``tests/test_pit_universe_delisting.py`` and ``tests/test_m4_7_engine_bases.py``;
here the projected events run through both merged engines.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backtest.long_short import run_long_short_backtest
from backtest.portfolio import (
    TERMINAL_SETTLEMENT_CONTRACT,
    capture_backtest_source_provenance,
    resolve_pit_universe_mask,
    run_long_only_backtest,
)
from data.constituent_table import build_pit_membership_mask, load_constituent_intervals_csv
from data.holdout_partition import SnapshotRefusal, sha256_bytes
from data.parquet_loader import load_eod_cohort_panels
from m4_7_snapshot_support import CAL, I_H, Harness, bars, day, entry, interval_rows, record_reads, rows
from research.m4_7_common_support import scheduled_reset_rows, signal_eligibility
from research.m4_7_terminal_evidence import (
    BASIS,
    CURATED,
    ENGINE_FIELDS,
    EVIDENCE_COLUMNS,
    project,
    read_engine_events,
    validate,
    write_template,
)
from research.m4_7_universe_build import build_universe


N = len(CAL)
RESETS = scheduled_reset_rows(CAL)
CASH, STOCK, MIXED = BASIS["cash"], BASIS["stock"], BASIS["mixed"]


def target(last, price, **extra):
    return {"last": last, "price": price, **extra}


def terminal_snapshot(tmp_path, monkeypatch, name, targets, acquirers=None, *, acquirer_only=(), hook=None):
    """Targets are open-interval members whose bars stop at ``last``; acquirers trade on every row."""
    harness = Harness(tmp_path, monkeypatch, snapshot_id=name)
    vendor = harness.vendor
    vendor.code("SPY.US", bars(rows(0, N)))
    for code, spec in targets.items():
        vendor.entries.append(entry(code, day(spec.get("start", I_H + 10))))
        history = spec.get("bars") or bars(rows(I_H + 5, spec["last"] + 1), close=spec["price"],
                                           adjusted=spec.get("adjusted"), volume=spec.get("volume", 1000.0))
        vendor.code(f"{code}.US", history, spec.get("splits", []), spec.get("dividends", []))
    for code, spec in (acquirers or {}).items():
        if code not in acquirer_only:
            vendor.entries.append(entry(code, day(I_H + 10)))
        closes = spec.get("closes", {})
        kept = [r for r in rows(0, N) if r not in spec.get("missing", ())]
        vendor.code(f"{code}.US", bars(kept, close=lambda r, c=closes: c.get(r, 100.0)), spec.get("splits", []),
                    spec.get("dividends", []))

    def default(h):
        assert h.run("components") == 0 and h.run("symbols") == 0
        h.seal()
        assert h.run("calendar") == 0
        if acquirer_only:
            codes_file = tmp_path / f"{name}_codes.txt"
            codes_file.write_text("".join(f"{code}.US\n" for code in acquirer_only))
            assert h.run("splits", "--codes", str(codes_file)) == 0
        for table in ("splits", "eod", "dividends"):
            assert h.run(table) == 0
        if hook is not None:
            hook(h)
        h.run("verify")

    default(harness)
    build_universe(harness.snapshot_dir)
    write_template(harness.snapshot_dir)
    return harness.snapshot_dir


def curate(code, last, kind, lag=0, *, announced=None, event_kind="merger_or_acquisition", cash="", ratio="",
           acquirer="", currency="", source="8-K filed at completion", notes="", settlement=None):
    s = last + 1
    row = dict.fromkeys(EVIDENCE_COLUMNS, "")
    row.update({
        "event_id": f"TE-{code}.US#E1-{day(s if settlement is None else settlement)}", "permanent_id": f"{code}.US#E1",
        "curation_status": "curated", "event_kind": event_kind, "consideration_type": kind,
        "announcement_date": announced or day(last - 30), "completion_date": day(s + lag),
        "cash_per_share": str(cash), "exchange_ratio": str(ratio), "acquirer_permanent_id": acquirer,
        "cash_currency": currency or ("USD" if kind in ("cash", "mixed") else ""), "source_evidence": source,
        "curator": "research_curator", "notes": notes,
    })
    return row


def write_curated(snap: Path, rows_: list[dict]) -> None:
    template = pd.read_csv(snap / "terminal/terminal_evidence_template.csv", dtype=str, keep_default_na=False)
    curated = {row["permanent_id"]: row for row in rows_}
    merged = [curated.get(row["permanent_id"], {c: row[c] for c in EVIDENCE_COLUMNS})
              for row in template.to_dict(orient="records")]
    merged += [row for row in rows_ if row["permanent_id"] not in set(template["permanent_id"])]
    pd.DataFrame(merged, columns=list(EVIDENCE_COLUMNS)).to_csv(snap / CURATED, index=False)


def results(report):
    return {row["permanent_id"].split(".")[0]: row for row in report["rows"]}


# The shared deal fixture of T-TERM-1, 2, 3, 7, 8.
L_CASH, L_STK0, L_STK1, L_MIX0, L_MIX1, L_WORT = (I_H + 300 + 20 * k for k in range(6))
DEALS = {
    "CSH": target(L_CASH, 24.0), "STK0": target(L_STK0, 45.0), "STK1": target(L_STK1, 45.0),
    "MIX0": target(L_MIX0, 25.0), "MIX1": target(L_MIX1, 25.0), "WRT": target(L_WORT, 10.0),
}
ACQ_CLOSES = {L_STK0 + 1: 100.0, L_STK1: 100.0, L_STK1 + 1: 97.0, L_MIX0 + 1: 80.0, L_MIX1: 80.0, L_MIX1 + 1: 85.0}


def deal_rows(acquirer="ACQ.US#E1"):
    return [
        curate("CSH", L_CASH, "cash", 0, cash=30),
        curate("STK0", L_STK0, "stock", 0, ratio=0.5, acquirer=acquirer),
        curate("STK1", L_STK1, "stock", -1, ratio=0.5, acquirer=acquirer),
        curate("MIX0", L_MIX0, "mixed", 0, cash=10, ratio=0.25, acquirer=acquirer),
        curate("MIX1", L_MIX1, "mixed", -1, cash=10, ratio=0.25, acquirer=acquirer),
        curate("WRT", L_WORT, "evidenced_worthless", 0, event_kind="bankruptcy_or_liquidation"),
    ]


@pytest.fixture
def deals(tmp_path, monkeypatch):
    snap = terminal_snapshot(tmp_path, monkeypatch, "deals", DEALS, {"ACQ": {"closes": ACQ_CLOSES}})
    write_curated(snap, deal_rows())
    report = validate(snap)
    project(snap)
    return snap, report


def test_t_term_1_2_7_consideration_arithmetic_and_valuation_rows(deals):
    snap, report = deals
    got = results(report)
    assert got["STK0"]["terminal_return"] == pytest.approx(0.5 * 100 / 45 - 1)
    assert got["STK0"]["return_basis"] == STOCK and got["STK0"]["valuation_row"] == day(L_STK0 + 1)
    assert got["MIX0"]["terminal_return"] == pytest.approx(0.2) and got["MIX0"]["return_basis"] == MIXED
    assert got["MIX1"]["terminal_return"] == pytest.approx(0.2) and got["MIX1"]["valuation_row"] == day(L_MIX1)
    assert got["STK1"]["valuation_row"] == day(L_STK1)
    assert got["CSH"]["terminal_return"] == pytest.approx(0.25) and got["CSH"]["return_basis"] == CASH
    assert got["WRT"]["terminal_return"] == -1.0 and got["WRT"]["return_basis"] == CASH
    assert {k: v["status"] for k, v in got.items()} == dict.fromkeys(got, "accepted")
    assert report["valuation_row_offsets"] == {"L": 2, "S": 2}
    assert report["settlement_lag_distribution"] == {
        "cash": {"0": 1}, "evidenced_worthless": {"0": 1}, "mixed": {"-1": 1, "0": 1}, "stock": {"-1": 1, "0": 1}}


def test_t_term_7_accepted_lags_by_type(tmp_path, monkeypatch):
    targets = {f"C{k}": target(I_H + 300 + 10 * k, 20.0) for k in range(4)}
    targets |= {"SL": target(I_H + 350, 50.0), "SS": target(I_H + 360, 50.0)}
    snap = terminal_snapshot(tmp_path, monkeypatch, "lags", targets, {"ACQ": {}})
    lags = {"C0": -1, "C1": 0, "C2": 1, "C3": 3}
    write_curated(snap, [curate(code, targets[code]["last"], "cash", lag, cash=21) for code, lag in lags.items()]
                  + [curate("SL", targets["SL"]["last"], "stock", -1, ratio=1, acquirer="ACQ.US#E1"),
                     curate("SS", targets["SS"]["last"], "stock", 0, ratio=1, acquirer="ACQ.US#E1")])
    got = results(validate(snap))
    assert {code: got[code]["settlement_lag_rows"] for code in lags} == lags
    assert all(got[code]["status"] == "accepted" for code in got)
    assert got["SL"]["valuation_row"] == day(targets["SL"]["last"])
    assert got["SS"]["valuation_row"] == day(targets["SS"]["last"] + 1)


def test_t_term_8_projection_fields_and_rows(deals, tmp_path):
    snap, report = deals
    path = snap / "terminal/terminal_events_engine.csv"
    header = path.read_text().splitlines()[0]
    assert header == "# validation_report_sha256: " + sha256_bytes((snap / "terminal/terminal_validation.json").read_bytes())
    events = pd.read_csv(path, skiprows=1, dtype=str)
    assert tuple(events.columns) == ENGINE_FIELDS and len(events) == 6
    for event in events.to_dict(orient="records"):
        s = CAL.get_loc(pd.Timestamp(event["effective_date"]))
        assert event["reference_date"] == day(s - 1) and event["known_at"] <= event["reference_date"]
    for row in report["rows"]:
        if row["consideration_type"] in ("stock", "mixed"):
            completion = CAL.searchsorted(pd.Timestamp(day(CAL.get_loc(pd.Timestamp(row["effective_date"]))
                                                           + row["settlement_lag_rows"])))
            assert row["valuation_row"] == day(completion) and row["valuation_row"] in (row["reference_date"], row["effective_date"])


def engine_inputs(snap, exclude=()):
    table = load_constituent_intervals_csv(snap / "membership/constituent_intervals.csv")
    inventory = json.loads((snap / "panel/inventory_discovery.json").read_text())
    members = sorted(set(table.data["permanent_id"]) & {r["symbol"] for r in inventory["files"]} - set(exclude))
    panels = load_eod_cohort_panels(snap / "panel", members, inventory_path=snap / "panel/inventory_discovery.json")
    prices = panels["adjusted_close"].reindex(CAL[I_H:])
    events = read_engine_events(snap)
    events = events[events["permanent_id"].isin(members)].reset_index(drop=True)
    return table, prices, events


def run_books(table, prices, events, start, end, signal=None):
    mask = resolve_pit_universe_mask(table, events, prices.index, list(prices.columns))
    s_mask = signal_eligibility(mask, prices.notna())
    scores = signal if signal is not None else s_mask.astype(float).where(s_mask)
    common = dict(evaluation_start=start, evaluation_end=end, rebalance_frequency="ME", constituent_intervals=table,
                  terminal_events=events)
    long_only = run_long_only_backtest(prices, scores, source_provenance=capture_backtest_source_provenance(prices, scores),
                                       top_pct=1.0, **common)
    ranked = s_mask.astype(float).where(s_mask).mul(np.arange(prices.shape[1], 0, -1), axis=1)
    long_short = run_long_short_backtest(prices, ranked, quantiles=2, **common)
    return long_only, long_short


def test_t_term_3_projected_events_settle_through_both_engines(deals):
    snap, report = deals
    table, prices, events = engine_inputs(snap, exclude=("MIX1.US#E1",))
    long_only, long_short = run_books(table, prices, events, CAL[I_H + 20], CAL[-1])
    counts = {CASH: 2, STOCK: 2, MIXED: 1}
    for book in (long_only, long_short):
        assert book.assumptions["terminal_basis_counts"] == counts
        assert book.assumptions["terminal_settlement_contract"] == TERMINAL_SETTLEMENT_CONTRACT
    rho = {row["permanent_id"]: row["terminal_return"] for row in report["rows"] if row["permanent_id"] != "MIX1.US#E1"}
    logged = {record["permanent_id"]: record for record in long_only.terminal_event_log}
    assert set(logged) == set(rho)
    for pid, record in logged.items():
        s = CAL.get_loc(pd.Timestamp(record["effective_date"]))
        assert record["terminal_return"] == pytest.approx(rho[pid]) and record["incoming_weight"] > 0
        assert record["cashflow"] == pytest.approx(
            long_only.equity_curve.loc[CAL[s - 1]] * record["incoming_weight"] * (1 + rho[pid]))
        assert long_only.holdings.loc[CAL[s], pid] == 0.0


def reset_settlement():
    s = int(next(r for r in RESETS if r >= I_H + 430))
    return s - 1, s


def test_t_term_4_known_at_must_not_follow_the_reference_row(tmp_path, monkeypatch):
    last, s = reset_settlement()
    snap = terminal_snapshot(tmp_path, monkeypatch, "known", {"K4": target(last, 40.0)}, {"ACQ": {}})
    write_curated(snap, [curate("K4", last, "cash", 0, cash=44, announced=day(s))])
    assert results(validate(snap))["K4"]["validation_reason"] == "known_at_after_reference"
    write_curated(snap, [curate("K4", last, "cash", 0, cash=44, announced=day(last))])
    assert results(validate(snap))["K4"]["status"] == "accepted"
    project(snap)
    table, prices, events = engine_inputs(snap)
    assert s in RESETS
    long_only, long_short = run_books(table, prices, events, CAL[I_H + 20], CAL[-1])
    assert long_only.holdings.loc[CAL[s], "K4.US#E1"] == 0.0 and long_only.holdings.loc[CAL[s - 1], "K4.US#E1"] > 0.0
    assert long_short.net_holdings.loc[CAL[s], "K4.US#E1"] == 0.0
    for book in (long_only, long_short):
        assert [record["permanent_id"] for record in book.terminal_event_log] == ["K4.US#E1"]


FAULT_LAST = {name: I_H + 300 + 6 * k for k, name in enumerate(
    ["ACQ0", "ACQ1", "LAG4", "STK1", "MIX2", "NEGC", "NEGS", "TSPL", "ASPL", "ADJ", "ATT", "D404", "DABS", "AQQ",
     "INC", "KIND", "UNJ", "REF", "CUR"])}


def test_t_term_5_one_fault_fixtures(tmp_path, monkeypatch):
    f = FAULT_LAST
    targets = {name: target(last, 50.0) for name, last in f.items()}
    targets["TSPL"]["splits"] = [{"date": day(f["TSPL"] + 1), "split": "2/1"}]
    targets["ADJ"]["adjusted"] = 49.0
    targets["ATT"].update(adjusted=25.0, volume=2000.0, splits=[{"date": day(f["ATT"] + 3), "split": "2/1"}])
    targets["D404"]["dividends"] = 404
    acquirers = {
        "ACQ": {}, "ACQG": {"missing": (f["ACQ0"] + 1, f["ACQ1"])},
        "ACQS": {"splits": [{"date": day(f["ASPL"] + 1), "split": "2/1"}]},
        "ACQQ": {"splits": [{"date": day(f["AQQ"] + 1), "split": "0/1"}]},
    }

    def drop_dividends(h):
        h.edit_manifest(lambda m: m["entries"].pop("dividends/DABS.US"))

    snap = terminal_snapshot(tmp_path, monkeypatch, "faults", targets, acquirers, hook=drop_dividends)
    stock = dict(ratio=0.5, acquirer="ACQ.US#E1")
    rows_ = [
        curate("ACQ0", f["ACQ0"], "stock", 0, ratio=0.5, acquirer="ACQG.US#E1"),
        curate("ACQ1", f["ACQ1"], "stock", -1, ratio=0.5, acquirer="ACQG.US#E1"),
        curate("LAG4", f["LAG4"], "cash", 4, cash=50),
        curate("STK1", f["STK1"], "stock", 1, **stock),
        curate("MIX2", f["MIX2"], "mixed", 2, cash=5, **stock),
        curate("NEGC", f["NEGC"], "cash", -2, cash=50),
        curate("NEGS", f["NEGS"], "stock", -2, **stock),
        curate("TSPL", f["TSPL"], "cash", 0, cash=50),
        curate("ASPL", f["ASPL"], "stock", 0, ratio=0.5, acquirer="ACQS.US#E1"),
        curate("ADJ", f["ADJ"], "cash", 0, cash=50),
        curate("ATT", f["ATT"], "cash", 0, cash=50),
        curate("D404", f["D404"], "cash", 0, cash=50),
        curate("DABS", f["DABS"], "cash", 0, cash=50),
        curate("AQQ", f["AQQ"], "stock", 0, ratio=0.5, acquirer="ACQQ.US#E1"),
        curate("INC", f["INC"], "cash", 0, cash=50, source=""),
        curate("KIND", f["KIND"], "cash", 0, cash=50, event_kind=""),
        curate("UNJ", f["UNJ"], "cash", 0, cash=150),
        curate("REF", f["REF"], "cash", 0, cash=50, settlement=f["REF"] + 2),
        curate("CUR", f["CUR"], "cash", 0, cash=50, currency="EUR"),
    ]
    write_curated(snap, rows_)
    got = {code: row["validation_reason"] for code, row in results(validate(snap)).items()}
    missing = "terminal_basis_ambiguous:corporate_action_evidence_missing"
    assert got == {
        "ACQ0": "acquirer_bar_missing", "ACQ1": "acquirer_bar_missing", "LAG4": "settlement_lag_exceeds_3_rows",
        "STK1": "stock_consideration_lag_positive", "MIX2": "stock_consideration_lag_positive",
        "NEGC": "settlement_lag_negative", "NEGS": "settlement_lag_negative", "TSPL": "terminal_basis_ambiguous",
        "ASPL": "terminal_basis_ambiguous", "ADJ": "terminal_basis_ambiguous", "ATT": "terminal_basis_ambiguous",
        "D404": missing, "DABS": missing, "AQQ": missing, "INC": "evidence_incomplete", "KIND": "evidence_incomplete",
        "UNJ": "terminal_return_unjustified", "REF": "reference_not_last_bar", "CUR": "terminal_currency_unsupported",
    }
    events = project(snap)
    assert events.empty
    manifest = json.loads((snap / "membership/membership_build_manifest.json").read_text())
    att = next(c for c in manifest["episode_checks"] if c["permanent_id"] == "ATT.US#E1")
    assert att["outcome"] == "attributed_applied"


def test_t_term_5_negative_return_refuses_the_command(tmp_path, monkeypatch):
    snap = terminal_snapshot(tmp_path, monkeypatch, "neg", {"NEG": target(I_H + 300, 50.0)}, {"ACQ": {}})
    write_curated(snap, [curate("NEG", I_H + 300, "cash", 0, cash=-5)])
    assert results(validate(snap))["NEG"]["validation_reason"] == "evidence_incomplete"
    snap_rows = [curate("NEG", I_H + 300, "stock", 0, ratio=0.5, acquirer="ACQ.US#E1")]
    write_curated(snap, snap_rows)
    assert results(validate(snap))["NEG"]["status"] == "accepted"


def test_t_term_6_future_price_invariance(tmp_path, monkeypatch):
    base_closes = {L_STK0 + 1: 100.0, L_STK1: 100.0, L_STK1 + 1: 97.0}
    later = {**base_closes, **{r: 250.0 for r in range(L_STK1 + 2, N)}}
    targets = {"STK0": DEALS["STK0"], "STK1": DEALS["STK1"], "CSH": DEALS["CSH"]}

    def run(name, closes, cash_lag=0):
        snap = terminal_snapshot(tmp_path, monkeypatch, name, targets, {"ACQ": {"closes": closes}}, acquirer_only=("ACQ",))
        write_curated(snap, [curate("STK0", L_STK0, "stock", 0, ratio=0.5, acquirer="ACQ.US#E1"),
                             curate("STK1", L_STK1, "stock", -1, ratio=0.5, acquirer="ACQ.US#E1"),
                             curate("CSH", L_CASH, "cash", cash_lag, cash=30)])
        report = validate(snap)
        project(snap)
        return snap, {code: row["terminal_return"] for code, row in results(report).items()}

    base_snap, base = run("base", base_closes)
    master = pd.read_csv(base_snap / "identity/security_master.csv", dtype=str, keep_default_na=False)
    assert master.loc[master["vendor_code"] == "ACQ.US", "role"].tolist() == ["acquirer_only"]
    later_snap, after = run("later", later)
    assert after == base
    def event_rows(snap):
        return (snap / "terminal/terminal_events_engine.csv").read_text().splitlines()[1:]

    assert event_rows(later_snap) == event_rows(base_snap)
    moved_snap, moved = run("moved", base_closes, cash_lag=3)
    assert moved["CSH"] == base["CSH"]
    table, prices, events = engine_inputs(base_snap)
    moved_events = engine_inputs(moved_snap)[2]
    assert events.equals(moved_events)
    first = run_books(table, prices, events, CAL[I_H + 20], CAL[-1])
    second = run_books(*engine_inputs(later_snap), CAL[I_H + 20], CAL[-1])
    for one, two in zip(first, second):
        pd.testing.assert_series_equal(one.equity_curve, two.equity_curve)
    _, at_v = run("at_v", {**base_closes, L_STK0 + 1: 90.0})
    assert at_v["STK0"] != base["STK0"]
    _, at_s = run("at_s", {**base_closes, L_STK1 + 1: 55.0})
    assert at_s["STK1"] == base["STK1"]
    _, at_l = run("at_l", {**base_closes, L_STK1: 55.0})
    assert at_l["STK1"] != base["STK1"]


def test_t_term_9_exit_classes_partition_and_agree_with_the_mask(tmp_path, monkeypatch):
    reset = int(next(r for r in RESETS if r >= I_H + 300))
    d_last = N - 1
    next_reset = int(next(r for r in RESETS if r > reset))
    sunday_row = CAL.get_loc(pd.Timestamp("2005-10-31"))
    holiday_row = CAL.get_loc(pd.Timestamp("2006-03-31"))
    cases = {
        "IRT": (day(reset + 2), rows(I_H, N), "index_removal_still_trading"),
        "DOM": (day(reset - 3), rows(I_H, reset + 1), "disappearance_outside_membership"),
        "DO3": (day(reset - 3), rows(I_H, reset + 31), "disappearance_outside_membership"),
        "DLC": (day(reset - 3), rows(I_H, reset), "delisting_candidate"),
        "OPM": (None, rows(I_H, reset), "delisting_candidate"),
        "OPE": (None, rows(I_H, N), "index_removal_still_trading"),
        "SUN": ("2005-10-30", rows(I_H, sunday_row + 1), "delisting_candidate"),
        "HOL": ("2006-03-30", rows(I_H, holiday_row + 1), "delisting_candidate"),
    }
    harness = Harness(tmp_path, monkeypatch, snapshot_id="exits")
    harness.vendor.code("SPY.US", bars(rows(0, N)))
    for code, (end, history, _) in cases.items():
        harness.vendor.entries.append(entry(code, day(I_H + 10), end))
        harness.vendor.code(f"{code}.US", bars(history))
    snap = harness.retrieve()
    build_universe(snap)
    got = {row["vendor_code"][:-3]: row for row in interval_rows(snap).to_dict(orient="records")}
    assert {code: row["exit_class"] for code, row in got.items()} == {code: c[2] for code, c in cases.items()}
    assert got["SUN"]["R_exit"] == day(next(r for r in RESETS if r > sunday_row))
    assert got["HOL"]["R_exit"] == day(next(r for r in RESETS if r > holiday_row))
    table = load_constituent_intervals_csv(snap / "membership/constituent_intervals.csv")
    mask = build_pit_membership_mask(table, CAL, [f"{c}.US#E1" for c in cases], signal_lag_periods=1)
    for code, row in got.items():
        column = mask[f"{code}.US#E1"].to_numpy()
        r_exit = CAL.get_loc(pd.Timestamp(row["R_exit"]))
        admitted_resets = [r for r in RESETS if column[r]]
        if row["m_out"]:
            assert not column[r_exit] and all(r < r_exit for r in admitted_resets)
        else:
            assert r_exit == d_last
    assert next_reset > reset


def test_t_term_10_rename_under_both_vendor_behaviors(tmp_path, monkeypatch):
    last = I_H + 300
    harness = Harness(tmp_path, monkeypatch, snapshot_id="rename")
    vendor = harness.vendor
    vendor.code("SPY.US", bars(rows(0, N)))
    vendor.entries = [entry("OLDN", day(I_H + 10), day(last + 1), name="Rename Co"),
                      entry("NEWN", day(last + 1), name="Rename Co"), entry("PEER", day(I_H + 10))]
    vendor.code("OLDN.US", bars(rows(I_H + 5, last + 1), close=40.0))
    vendor.code("NEWN.US", bars(rows(last + 1, N), close=44.0))
    vendor.code("PEER.US", bars(rows(0, N)))
    snap = harness.retrieve()
    build_universe(snap)
    write_template(snap)
    write_curated(snap, [curate("OLDN", last, "stock", 0, ratio=1.0, acquirer="NEWN.US#E1",
                                event_kind="rename_or_code_change", source="exchange code-change notice")])
    got = results(validate(snap))["OLDN"]
    assert got["status"] == "accepted" and got["terminal_return"] == pytest.approx(0.1)
    project(snap)
    table, prices, events = engine_inputs(snap)
    long_only, long_short = run_books(table, prices, events, CAL[I_H + 20], CAL[-1])
    for book in (long_only, long_short):
        (logged,) = book.terminal_event_log
        assert pd.Timestamp(logged["effective_date"]) == CAL[last + 1]
    next_reset = int(next(r for r in RESETS if r > last + 1))
    assert long_only.holdings.loc[CAL[last + 1], "OLDN.US#E1"] == 0.0
    assert long_only.holdings.loc[CAL[next_reset], "NEWN.US#E1"] > 0.0

    harness_b = Harness(tmp_path, monkeypatch, snapshot_id="rekeyed")
    vendor_b = harness_b.vendor
    vendor_b.code("SPY.US", bars(rows(0, N)))
    vendor_b.entries = list(vendor.entries)
    vendor_b.code("OLDN.US", json.dumps([]).encode())
    vendor_b.code("NEWN.US", bars(rows(I_H + 5, N), close=44.0))
    vendor_b.code("PEER.US", bars(rows(0, N)))
    snap_b = harness_b.retrieve()
    build_universe(snap_b)
    template = write_template(snap_b)
    old = next(r for r in interval_rows(snap_b).to_dict(orient="records") if r["vendor_code"] == "OLDN.US")
    assert old["resolution"] == "no_containing_episode:rekeyed_rename_candidate" and old["census_cap"] == "R-CENSUS-9"
    assert template.empty


def test_t_term_11_holdout_boundary_deferral(tmp_path, monkeypatch):
    targets = {"DEF": target(I_H - 1, 30.0), "DSC": target(I_H, 30.0, start=I_H - 30)}
    targets["DEF"].update(bars=bars(rows(I_H - 60, I_H), close=30.0), start=I_H - 50)
    targets["DSC"]["bars"] = bars(rows(I_H - 60, I_H + 1), close=30.0)
    snap = terminal_snapshot(tmp_path, monkeypatch, "boundary", targets, {"ACQ": {"closes": {I_H: 60.0}}})
    template = pd.read_csv(snap / "terminal/terminal_evidence_template.csv", dtype=str, keep_default_na=False)
    by_pid = {row["permanent_id"]: row for row in template.to_dict(orient="records")}
    assert by_pid["DEF.US#E1"]["curation_status"] == "deferred_holdout"
    assert by_pid["DEF.US#E1"]["event_id"] == f"TE-DEF.US#E1-{day(I_H)}"
    assert all(by_pid["DEF.US#E1"][c] == "" for c in EVIDENCE_COLUMNS[3:])
    deferred = dict(by_pid["DEF.US#E1"])
    discovery = curate("DSC", I_H, "stock", -1, ratio=0.5, acquirer="ACQ.US#E1", announced=day(I_H - 5))
    write_curated(snap, [{c: deferred[c] for c in EVIDENCE_COLUMNS}, discovery])
    with record_reads(snap) as recorder:
        report = validate(snap)
    assert recorder.forbidden() == []
    got = results(report)
    assert got["DEF"]["status"] == "deferred_holdout" and got["DEF"]["terminal_return"] is None
    assert got["DSC"]["status"] == "accepted" and got["DSC"]["valuation_row"] == day(I_H)
    assert got["DSC"]["terminal_return"] == pytest.approx(0.5 * 60 / 30 - 1)
    write_curated(snap, [{**{c: deferred[c] for c in EVIDENCE_COLUMNS}, "consideration_type": "cash",
                          "cash_per_share": "31"}, discovery])
    with pytest.raises(SnapshotRefusal) as refused:
        validate(snap)
    assert refused.value.code == "holdout_terms_forbidden"


# ---------------------------------------------------------------- attempt 2 remediation (AUDIT1-M47A2-M1, M2; AUDIT2 A2-01, A2-04, A2-05)


CONTRADICTORY = "evidence_incomplete:contradictory_consideration_fields"


def test_consideration_fields_are_dispatched_strictly_by_type(tmp_path, monkeypatch):
    """A-M1/A2-04: unused term fields are refused; each type uses only its registered formula."""
    names = ["STKC", "STKZ", "CSHR", "CSHA", "MIXZ", "MIXN", "MIXE", "WRTC", "M2S", "CSHP", "MIXP"]
    lasts = {name: I_H + 300 + 6 * k for k, name in enumerate(names)}
    targets = {name: target(last, 45.0) for name, last in lasts.items()}
    snap = terminal_snapshot(tmp_path, monkeypatch, "fields", targets, {"ACQ": {}})
    acq = dict(acquirer="ACQ.US#E1")
    mixed = curate("M2S", lasts["M2S"], "mixed", 0, cash=10, ratio=0.5, **acq)
    write_curated(snap, [
        curate("STKC", lasts["STKC"], "stock", 0, cash=10, ratio=0.5, **acq),
        curate("STKZ", lasts["STKZ"], "stock", 0, cash=0, ratio=0.5, **acq),
        curate("CSHR", lasts["CSHR"], "cash", 0, cash=50, ratio=0.5),
        curate("CSHA", lasts["CSHA"], "cash", 0, cash=50, **acq),
        curate("MIXZ", lasts["MIXZ"], "mixed", 0, cash=0, ratio=0.5, **acq),
        curate("MIXN", lasts["MIXN"], "mixed", 0, cash=10, **acq),
        curate("MIXE", lasts["MIXE"], "mixed", 0, cash=10, ratio=0.5, currency="EUR", **acq),
        curate("WRTC", lasts["WRTC"], "evidenced_worthless", 0, cash=5),
        {**mixed, "consideration_type": "stock"},
        curate("CSHP", lasts["CSHP"], "cash", 0, cash=54),
        curate("MIXP", lasts["MIXP"], "mixed", 0, cash=10, ratio=0.5, **acq),
    ])
    got = results(validate(snap))
    assert {name: got[name]["validation_reason"] for name in names} == {
        "STKC": CONTRADICTORY, "STKZ": None, "CSHR": CONTRADICTORY, "CSHA": CONTRADICTORY,
        "MIXZ": "evidence_incomplete", "MIXN": "evidence_incomplete", "MIXE": "terminal_currency_unsupported",
        "WRTC": CONTRADICTORY, "M2S": CONTRADICTORY, "CSHP": None, "MIXP": None,
    }
    assert got["STKZ"]["terminal_return"] == 0.5 * 100.0 / 45.0 - 1.0 and got["STKZ"]["return_basis"] == STOCK
    assert got["CSHP"]["terminal_return"] == 54.0 / 45.0 - 1.0 and got["CSHP"]["return_basis"] == CASH
    assert got["MIXP"]["terminal_return"] == (10.0 + 0.5 * 100.0) / 45.0 - 1.0 and got["MIXP"]["return_basis"] == MIXED
    events = project(snap)
    assert sorted(events["permanent_id"]) == ["CSHP.US#E1", "MIXP.US#E1", "STKZ.US#E1"]
    table, prices, engine_events = engine_inputs(snap, exclude=tuple(f"{n}.US#E1" for n in names
                                                                    if n not in ("STKZ", "CSHP", "MIXP")))
    long_only, _ = run_books(table, prices, engine_events, CAL[I_H + 20], CAL[-1])
    stock = next(r for r in long_only.terminal_event_log if r["permanent_id"] == "STKZ.US#E1")
    s = CAL.get_loc(pd.Timestamp(stock["effective_date"]))
    assert stock["cashflow"] == pytest.approx(long_only.equity_curve.loc[CAL[s - 1]] * stock["incoming_weight"] * (100.0 / 90.0))


def test_valuation_row_is_never_indexed_past_the_calendar_end(tmp_path, monkeypatch):
    """A2-05: deals completing after the last calendar row validate without an ``IndexError``."""
    last = N - 2
    targets = {name: target(last, 40.0) for name in ("CEND", "WEND", "SEND")}
    snap = terminal_snapshot(tmp_path, monkeypatch, "calendar_end", targets, {"ACQ": {}})
    after_end = "2007-01-05"

    def at_end(code, kind, **terms):
        return {**curate(code, last, kind, 0, **terms), "completion_date": after_end}

    write_curated(snap, [at_end("CEND", "cash", cash=44), at_end("WEND", "evidenced_worthless",
                                                                  event_kind="bankruptcy_or_liquidation"),
                         at_end("SEND", "stock", ratio=1.0, acquirer="ACQ.US#E1")])
    got = results(validate(snap))
    assert (got["CEND"]["status"], got["CEND"]["settlement_lag_rows"]) == ("accepted", 1)
    assert got["CEND"]["terminal_return"] == pytest.approx(0.1) and got["CEND"]["valuation_row"] is None
    assert (got["WEND"]["status"], got["WEND"]["terminal_return"]) == ("accepted", -1.0)
    assert got["SEND"]["validation_reason"] == "stock_consideration_lag_positive"


def support_and_census(snap, out):
    from research.m4_7_common_support import write_support_files
    from research.m4_7_coverage_census import run_census

    support = write_support_files(snap)
    return support, run_census(snap, reports_dir=out / "reports", seal_out=out / "seal.json", code_commit="t")


def refused(callable_, *args):
    with pytest.raises(SnapshotRefusal) as caught:
        callable_(*args)
    return caught.value.code


def test_engine_events_must_be_the_projection_of_the_current_validation(deals, tmp_path):
    """A-M2/A2-01: support and census refuse a stale projection or a validation older than the evidence."""
    from research.m4_7_common_support import write_support_files
    from research.m4_7_coverage_census import run_census

    snap, _ = deals
    census = lambda: run_census(snap, reports_dir=tmp_path / "r", seal_out=tmp_path / "s.json")  # noqa: E731
    support, before = support_and_census(snap, tmp_path / "before")
    assert "STK0.US#E1" not in support.unresolved
    stale = "derived_artifact_stale:terminal_events_engine_mismatch"
    evidence_stale = "derived_artifact_stale:terminal_validation_evidence_mismatch"

    edits = {
        "accepted_to_unresolved": lambda rows_: [dict(r, curation_status="unresolved")
                                                 if r["permanent_id"] == "STK0.US#E1" else r for r in rows_],
        "changed_payoff": lambda rows_: [dict(r, cash_per_share="31") if r["permanent_id"] == "CSH.US#E1" else r
                                         for r in rows_],
        "deleted_row": lambda rows_: [r for r in rows_ if r["permanent_id"] != "WRT.US#E1"],
    }
    rows_ = deal_rows()
    for name, edit in edits.items():
        rows_ = edit(rows_)
        write_curated(snap, rows_)
        assert refused(write_support_files, snap) == evidence_stale, name
        assert refused(project, snap) == evidence_stale, name
        validate(snap)
        assert refused(write_support_files, snap) == stale, name
        assert refused(census) == stale, name
        project(snap)
        write_support_files(snap)
    support, after = support_and_census(snap, tmp_path / "after")
    assert support.unresolved_in_window() == {"STK0.US#E1": L_STK0 + 1 - I_H, "WRT.US#E1": L_WORT + 1 - I_H}
    assert after["public"]["exclusion_set"]["unresolved_events"] == 2
    assert before["public"]["exclusion_set"]["unresolved_events"] == 0
    assert after["public"]["price_coverage"]["eligible_unpriced_member_days"]["after_unresolved_disappearance"] > 0

    path = snap / "terminal/terminal_events_engine.csv"
    lines = path.read_text().splitlines()
    path.write_text("\n".join(lines[:-1]) + "\n")
    assert refused(write_support_files, snap) == stale
    assert refused(census) == stale
