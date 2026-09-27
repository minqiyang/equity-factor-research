"""M4.8 Stage B support and terminal oracles: T-LAB, T-CAUSAL-4, T-CAUSAL-6, T-RES-1..5, T-TERM3-1..10.

The support oracles run on small synthetic panels. The terminal oracles build
a rule v1 fixture snapshot with the M4.7 harness and validate it under schema
v3 with synthetic discovery segments on that calendar (one discovery side, so
reads carry no side). No test opens a network connection or reads private data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import pytest

from backtest.portfolio import capture_backtest_source_provenance, resolve_pit_universe_mask, run_long_only_backtest
from m4_7_snapshot_support import CAL, HOLDOUT_START, I_H, day
from research.m4_7_common_support import (
    MISSING_EXECUTION_HALT,
    MISSING_HORIZON_DISAPPEARANCE,
    MISSING_HORIZON_HALT,
    causal_support_schedule,
    claim_demand,
    ic_month_set,
    potentially_held,
    reset_to_reset_labels,
    residual_bound_events,
    residual_disappearances,
    scheduled_reset_rows,
    signal_eligibility,
)
from research.m4_7_family_a import family_a_signals
from research.m4_7_terminal_evidence import (
    CURATED,
    DEFERRED,
    EVIDENCE_COLUMNS,
    EVIDENCE_COLUMNS_V3,
    IN_SCOPE,
    OUTSIDE,
    event_scope,
    project,
    read_engine_events,
    validate,
)
from test_m4_7_terminal_evidence import ACQ_CLOSES, DEALS, curate, deal_rows, target, terminal_snapshot


@dataclass(frozen=True)
class Segment:
    """A synthetic ``discovery_segments`` record (the Stage A interface, plan 7)."""

    segment_id: str
    side: str | None
    anchor_row: int
    first_reset_row: int
    last_ic_reset_row: int
    last_book_row: int
    feature_floor_row: int
    feature_ceiling_row: int


def segment(segment_id, first_reset, last_book, *, floor=0, side=None):
    return Segment(segment_id, side, first_reset - 1, first_reset, last_book - 1, last_book, floor, last_book)


DATES = pd.bdate_range("2021-01-01", periods=130)
RESETS = scheduled_reset_rows(DATES)


def walk(n_assets, seed, dates=DATES):
    rng = np.random.default_rng(seed)
    values = 50.0 * np.exp(np.cumsum(rng.normal(0.0002, 0.01, (len(dates), n_assets)), axis=0))
    return pd.DataFrame(values, index=dates, columns=[f"A{i:02d}" for i in range(n_assets)])


def members(assets, dates=DATES):
    return pd.DataFrame({"symbol": assets, "permanent_id": assets, "start_date": dates[0], "start_known_at": dates[0],
                         "end_date": pd.NaT, "end_known_at": pd.NaT})


def schedule_of(prices, events=None, d0=None):
    bars = prices.notna()
    mask = resolve_pit_universe_mask(members(list(prices.columns), prices.index), events, prices.index,
                                     list(prices.columns))
    return causal_support_schedule(prices.index, bars, mask, int(RESETS[1]) if d0 is None else d0), bars


# ---------------------------------------------------------------- T-LAB-1..3


def test_t_lab_typed_missing_labels_drop_the_pair_and_count_without_a_stop():
    prices = walk(6, 1)
    r, h = int(RESETS[2]), int(RESETS[3])
    prices.iloc[r, 0] = np.nan                    # no bar at the execution row
    prices.iloc[h, 1] = np.nan                    # no bar at the horizon, a later bar exists
    prices.iloc[h - 3:, 2] = np.nan               # disappears inside (r, h]: reachable only under Branch R
    schedule, _ = schedule_of(prices)
    labels, records = reset_to_reset_labels(prices, schedule.s_mask, schedule.reset_rows, (r,), None, typed=True)
    row = records.loc[DATES[r]]
    assert (row[MISSING_EXECUTION_HALT], row[MISSING_HORIZON_HALT], row[MISSING_HORIZON_DISAPPEARANCE]) == (1, 1, 1)
    assert labels.iloc[r - 1, :3].isna().all() and labels.iloc[r - 1, 3:].notna().all()
    assert row["eligible_count"] == 6
    carried, carried_records = reset_to_reset_labels(prices, schedule.s_mask, schedule.reset_rows, (r,), None)
    assert set(carried_records.columns) >= {"missing_execution_bar", "missing_horizon_end_bar"}
    assert MISSING_EXECUTION_HALT not in carried_records.columns  # registration v2 records keep their shape


# ---------------------------------------------------------------- T-CAUSAL-4


def test_t_causal_4_signal_eligibility_and_label_dependence():
    prices = walk(8, 2)
    spy = prices.mean(axis=1).rename("SPY")
    volume = prices * 1e6
    schedule, bars = schedule_of(prices)
    r = int(RESETS[3])
    h = int(RESETS[4])
    base_signals = family_a_signals(prices, spy, volume, schedule.s_mask)
    edited = prices.copy()
    edited.iloc[r:] *= np.random.default_rng(3).uniform(0.5, 1.5, edited.iloc[r:].shape)
    edited.iloc[r + 2:r + 5, 4] = np.nan
    edited_schedule, _ = schedule_of(edited)
    assert edited_schedule.s_mask.iloc[:r].equals(schedule.s_mask.iloc[:r])
    for factor_id, panel in dict(family_a_signals(edited, spy, volume, edited_schedule.s_mask)).items():
        assert panel.iloc[:r].equals(dict(base_signals)[factor_id].iloc[:r]), factor_id

    def label(p, events=None):
        s, _ = schedule_of(p, events)
        return reset_to_reset_labels(p, s.s_mask, s.reset_rows, (r,), events, typed=True)[0].iloc[r - 1]

    base = label(prices)
    outside = prices.copy()
    outside.iloc[:r] *= 1.1   # rows before r: the label reads only [r, h]
    outside.iloc[h + 1:] *= 0.9
    assert label(outside).equals(base)
    for row in (r, h):
        moved = prices.copy()
        moved.iloc[row, 0] *= 1.05
        assert label(moved)["A00"] != base["A00"]
    # an evidenced cash label: editing the reference close and reprojecting rho leaves the label unchanged
    settle, cash = r + 6, 60.0
    evidenced = prices.copy()
    evidenced.iloc[settle:, 1] = np.nan

    def cash_event(p):
        rho = cash / p.iloc[settle - 1, 1] - 1.0
        return pd.DataFrame([{"event_id": "e", "permanent_id": "A01", "effective_date": DATES[settle],
                              "known_at": DATES[settle - 1], "reference_date": DATES[settle - 1],
                              "terminal_return": rho, "return_basis": "prior_observed_close_to_cash"}])

    first = label(evidenced, cash_event(evidenced))["A01"]
    reference_moved = evidenced.copy()
    reference_moved.iloc[settle - 1, 1] *= 1.2
    assert label(reference_moved, cash_event(reference_moved))["A01"] == pytest.approx(first, rel=1e-12)
    assert first == pytest.approx(cash / prices.iloc[r, 1] - 1.0, rel=1e-12)
    assert label(evidenced, cash_event(evidenced))["A01"] == first  # the event precedes h; edits at h are unseen
    stock_rho = {close: 0.5 * close / evidenced.iloc[settle - 1, 1] - 1.0 for close in (100.0, 110.0)}
    stock_labels = set()
    for value in stock_rho.values():
        event = cash_event(evidenced).assign(terminal_return=value)
        stock_labels.add(label(evidenced, event)["A01"])
    assert len(stock_labels) == 2  # a stock label changes with the acquirer close at its valuation row


# ---------------------------------------------------------------- T-RES-1..5 and the -100 percent case


def test_t_res_1_2_residual_membership_over_p_r():
    prices = walk(6, 4)
    stop = int(RESETS[2]) + 4
    prices.iloc[stop:, 0] = np.nan  # A00 eligible, bars stop inside a window: residual
    prices.iloc[: int(RESETS[3]), 5] = np.nan  # A05 lists later; never eligible before its bars
    schedule, bars = schedule_of(prices)
    residual = residual_disappearances(schedule, bars, set(), {"A00": stop})
    assert residual == (("A00", stop, int(RESETS[2])),)
    # T-RES-2: a candidate never in any P_r stays out
    never = walk(6, 5)
    never.iloc[: int(RESETS[1]) - 2, 3] = np.nan
    never.iloc[int(RESETS[1]) - 2:, 3] = np.nan
    s2, b2 = schedule_of(never)
    assert residual_disappearances(s2, b2, set(), {"A03": int(RESETS[2]) + 3}) == ()


def test_t_res_4_p_r_carries_a_locked_asset_that_lost_eligibility():
    prices = walk(6, 6)
    r2 = int(RESETS[2])
    prices.iloc[r2:r2 + 3, 1] = np.nan                     # no close at r2: locked if held, so carried in P_r2
    table = members(list(prices.columns)).assign(end_date=DATES[r2 - 5], end_known_at=DATES[r2 - 5])
    table.loc[table["permanent_id"] != "A01", ["end_date", "end_known_at"]] = pd.NaT
    mask = resolve_pit_universe_mask(table, None, DATES, list(prices.columns))
    schedule = causal_support_schedule(DATES, prices.notna(), mask, int(RESETS[1]))
    held = potentially_held(schedule, prices.notna())
    column = list(prices.columns).index("A01")
    assert not schedule.s_mask.iloc[r2 - 1, column] and held[r2][column]
    prices.iloc[r2 + 6:, 1] = np.nan                       # the carried lock resumes, then disappears inside the window
    schedule = causal_support_schedule(DATES, prices.notna(), mask, int(RESETS[1]))
    assert residual_disappearances(schedule, prices.notna(), set(), {}) == (("A01", r2 + 6, r2),)


def test_t_res_5_accepted_settlements_stay_out_of_the_residual():
    prices = walk(6, 7)
    stop = int(RESETS[2]) + 4
    prices.iloc[stop:, 2] = np.nan
    schedule, bars = schedule_of(prices)
    assert residual_disappearances(schedule, bars, {"A02"}, {"A02": stop}) == ()
    assert residual_disappearances(schedule, bars, set(), {"A02": stop})[0][0] == "A02"


def _long_only(prices, signals, events=None, end=None):
    return run_long_only_backtest(
        prices, signals, source_provenance=capture_backtest_source_provenance(prices, signals),
        evaluation_start=DATES[int(RESETS[1]) - 1], evaluation_end=end or DATES[-1], top_pct=1.0,
        constituent_intervals=members(list(prices.columns)), terminal_events=events,
        missing_price_policy="halt_gap_return_v1")


def test_t_res_3_minus_100pct_bound_case():
    prices = walk(6, 8)
    signals = pd.DataFrame(1.0, index=DATES, columns=prices.columns)
    schedule, bars = schedule_of(prices)
    residual = residual_disappearances(schedule, bars, set(), {})
    assert residual == () and len(residual_bound_events(residual, DATES)) == 0
    primary = _long_only(prices, signals)
    vacuous = _long_only(prices, signals, None)
    assert primary.returns.equals(vacuous.returns) and primary.holdings.equals(vacuous.holdings)
    stop = int(RESETS[3]) + 5
    lost = prices.copy()
    lost.iloc[stop:, 3] = np.nan
    schedule, bars = schedule_of(lost)
    residual = residual_disappearances(schedule, bars, set(), {})
    assert [pid for pid, _, _ in residual] == ["A03"]
    with pytest.raises(Exception) as refused:
        _long_only(lost, signals)
    assert getattr(refused.value, "reason", None) == "unresolved_disappearance"
    bound = _long_only(lost, signals, residual_bound_events(residual, DATES))
    before = _long_only(lost, signals, end=DATES[stop - 1])
    assert bound.returns.loc[:DATES[stop - 1]].equals(before.returns)
    assert bound.terminal_event_log[0]["terminal_return"] == -1.0


# ---------------------------------------------------------------- T-TERM3 (schema v3 two-pass validation)


N = len(CAL)
ONE = (segment("post", I_H + 5, N - 1),)
ACCESSION = "0000950123-05-000001"


def v3(row, *, terms=None, timing=None, payment_date="", payment_source="", accession=ACCESSION, second=""):
    kind = row["consideration_type"]
    default = "at_completion_evidenced" if kind in ("cash", "mixed") else "not_applicable"
    return {**row, "source_accession": accession, "source_form": "8-K/2.01",
            "terms_known_at": row["announcement_date"] if terms is None else terms,
            "payment_timing": default if timing is None else timing, "payment_date": payment_date,
            "payment_source_accession": payment_source, "second_check": second}


def write_v3(snap, rows_):
    template = pd.read_csv(snap / "terminal/terminal_evidence_template.csv", dtype=str, keep_default_na=False)
    curated = {row["permanent_id"]: row for row in rows_}
    merged = [curated.get(row["permanent_id"], {**{c: row[c] for c in EVIDENCE_COLUMNS},
                                                **dict.fromkeys(EVIDENCE_COLUMNS_V3[len(EVIDENCE_COLUMNS):], "")})
              for row in template.to_dict(orient="records")]
    pd.DataFrame(merged, columns=list(EVIDENCE_COLUMNS_V3)).to_csv(snap / CURATED, index=False)


def by_code(report):
    return {row["permanent_id"].split(".")[0]: row for row in report["rows"]}


def run_v3(snap, segments=ONE, seed=7):
    return validate(snap, segments=segments, holdout_start=pd.Timestamp(HOLDOUT_START).date(),
                    second_check_seed=seed)


@pytest.fixture
def deal_snapshot(tmp_path, monkeypatch):
    return terminal_snapshot(tmp_path, monkeypatch, "deals", DEALS, {"ACQ": {"closes": ACQ_CLOSES}})


def test_t_term3_1_curated_rows_need_an_accession_and_terms_known_at(deal_snapshot):
    rows_ = deal_rows()
    write_v3(deal_snapshot, [v3(rows_[0], accession=""), v3(rows_[1], terms="")] + [v3(r) for r in rows_[2:]])
    got = by_code(run_v3(deal_snapshot))
    assert got["CSH"]["validation_reason"] == "evidence_incomplete:source_accession_missing"
    assert got["STK0"]["validation_reason"] == "evidence_incomplete:terms_known_at_missing"
    assert {got[c]["status"] for c in ("STK1", "MIX0", "MIX1", "WRT")} == {"accepted"}


def test_t_term3_2_3_scope_classes():
    seal = (100, 150)
    segments = (segment("pre", 20, 80), segment("post", 200, 300))
    assert event_scope(21, segments, seal) == (IN_SCOPE, segments[0])
    assert event_scope(80, segments, seal) == (IN_SCOPE, segments[0])
    assert event_scope(300, segments, seal) == (IN_SCOPE, segments[1])
    for row in (100, 149):
        assert event_scope(row, segments, seal) == (DEFERRED, None)
    for row in (20, 90, 99, 150, 200, 301):  # D0_pre, (h, holdout_start), holdout_end, D0_post, after D_last
        assert event_scope(row, segments, seal) == (OUTSIDE, None)


def test_t_term3_2_3_pre_segment_events_validate_and_the_complement_needs_no_terms(deal_snapshot):
    rows_ = deal_rows()
    # CSH settles at I_H + 301, between the two synthetic segments: outside, blank terms allowed
    blank = {**rows_[0], **dict.fromkeys(("event_kind", "consideration_type", "announcement_date", "completion_date",
                                          "cash_per_share", "cash_currency", "source_evidence"), "")}
    write_v3(deal_snapshot, [v3(blank, terms="", timing="", accession="")] + [v3(r) for r in rows_[1:]])
    early, late = segment("pre", I_H + 5, I_H + 300), segment("post", I_H + 310, N - 1)
    report = run_v3(deal_snapshot, (early, late))
    got = by_code(report)
    assert got["CSH"]["status"] == OUTSIDE and got["CSH"]["scope"] == OUTSIDE
    assert got["STK0"]["status"] == "accepted" and got["STK0"]["segment_id"] == "post"
    events = project(deal_snapshot)
    assert "CSH.US#E1" not in set(events["permanent_id"])
    assert report["counts_by"]["scope"][OUTSIDE] == 1


def test_t_term3_4_second_check_disagreement_and_a_reproducible_sample(deal_snapshot):
    rows_ = deal_rows()
    write_v3(deal_snapshot, [v3(rows_[0], second="disagree")] + [v3(r) for r in rows_[1:]])
    first = run_v3(deal_snapshot, seed=11)
    assert by_code(first)["CSH"]["validation_reason"] == "second_check_disagree"
    again = run_v3(deal_snapshot, seed=11)
    assert first["second_check"] == again["second_check"] and first["second_check"]["seed"] == 11
    assert len(first["second_check"]["sampled_event_ids"]) == 2  # ceil(0.2 * 6)
    mandatory = set(first["second_check"]["mandatory_event_ids"])
    assert {row["event_id"] for row in first["rows"] if row["terminal_return"] is not None
            and abs(row["terminal_return"]) > 0.5} <= mandatory
    required = first["second_check"]["required_event_ids"]
    assert first["second_check"]["pending"] == len(required) - sum(e.startswith("TE-CSH") for e in required)


def test_t_term3_5_9_payment_timing_rules(deal_snapshot):
    rows_ = deal_rows()
    s = DEALS["CSH"]["last"] + 1
    mixed_s = DEALS["MIX0"]["last"] + 1
    mixed_delayed = v3(rows_[3], timing="delayed_evidenced", payment_date=day(mixed_s + 2), payment_source="PA-1")
    write_v3(deal_snapshot, [
        v3(rows_[0], timing="delayed_evidenced", payment_date=day(s + 4), payment_source="PA-0"),
        v3(rows_[1], timing=""),
        v3(rows_[2]),
        mixed_delayed,
        v3(rows_[4], timing="unknown"),
        v3(rows_[5]),
    ])
    got = by_code(run_v3(deal_snapshot))
    assert got["CSH"]["validation_reason"] == "payment_lag_exceeds_bound"
    assert got["CSH"]["timing_failures"] == ["payment_lag_exceeds_bound"] and got["CSH"]["terms_pass"] == "terms_valid"
    assert got["STK0"]["validation_reason"] == "evidence_incomplete:payment_timing_missing"
    assert got["MIX0"]["status"] == "accepted" and got["MIX0"]["payment_lag_rows"] == 2
    assert got["MIX1"]["validation_reason"] == "payment_timing_unknown"
    assert got["MIX1"]["terms_pass"] == "terms_invalid"
    write_v3(deal_snapshot, [v3(rows_[0], timing="delayed_evidenced", payment_source="PA-0")]
             + [v3(r) for r in rows_[1:]])
    assert by_code(run_v3(deal_snapshot))["CSH"]["validation_reason"] == "evidence_incomplete:payment_date_missing"


def test_t_term3_6_stock_and_mixed_returns_equal_the_m4_7_formula(deal_snapshot, tmp_path, monkeypatch):
    rows_ = deal_rows()
    write_v3(deal_snapshot, [v3(r) for r in rows_])
    report = run_v3(deal_snapshot)
    assert "stock_consideration_converted_at_completion_close_v1" in report["labels"]
    carried_snap = terminal_snapshot(tmp_path / "carried", monkeypatch, "carried", DEALS,
                                     {"ACQ": {"closes": ACQ_CLOSES}})
    pd.DataFrame(rows_, columns=list(EVIDENCE_COLUMNS)).to_csv(carried_snap / CURATED, index=False)
    carried = by_code(validate(carried_snap))
    for code, row in by_code(report).items():
        assert row["status"] == carried[code]["status"] == "accepted"
        assert row["terminal_return"] == carried[code]["terminal_return"], code


def test_t_term3_7_8_terms_availability_and_carried_lags(tmp_path, monkeypatch):
    targets = {f"C{k}": target(I_H + 300 + 10 * k, 20.0) for k in range(4)}
    targets |= {"SL": target(I_H + 350, 50.0), "SS": target(I_H + 360, 50.0)}
    snap = terminal_snapshot(tmp_path, monkeypatch, "lags", targets, {"ACQ": {}})
    rows_ = []
    for code, lag in {"C0": -1, "C1": 0, "C2": 3}.items():
        rows_.append(v3(curate(code, targets[code]["last"], "cash", lag, cash=21), terms=day(targets[code]["last"])))
    rows_.append(v3(curate("C3", targets["C3"]["last"], "cash", 0, cash=21), terms=day(targets["C3"]["last"] + 1)))
    for code, lag in {"SL": -1, "SS": 0}.items():
        rows_.append(v3(curate(code, targets[code]["last"], "stock", lag, ratio=1, acquirer="ACQ.US#E1"),
                        terms=day(targets[code]["last"])))
    write_v3(snap, rows_)
    got = by_code(run_v3(snap))
    for code, lag in {"C0": -1, "C1": 0, "C2": 3, "SL": -1, "SS": 0}.items():
        assert got[code]["status"] == "accepted" and got[code]["settlement_lag_rows"] == lag, code
        assert got[code]["known_at"] == day(targets[code]["last"])  # max(announcement, terms_known_at)
    assert got["C3"]["validation_reason"] == "terms_known_after_reference"
    assert got["C3"]["timing_failures"] == ["terms_known_after_reference"]
    projected = project(snap)
    assert set(read_engine_events(snap)["permanent_id"]) == {f"{c}.US#E1" for c in ("C0", "C1", "C2", "SL", "SS")}
    assert set(projected["known_at"]) == {day(targets[c]["last"]) for c in ("C0", "C1", "C2", "SL", "SS")}


def test_t_term3_10_claim_demand_from_the_terms_pass(deal_snapshot):
    rows_ = deal_rows()
    s = DEALS["CSH"]["last"] + 1
    write_v3(deal_snapshot, [
        v3(rows_[0], timing="delayed_evidenced", payment_date=day(s + 20), payment_source="PA-0"),
        v3(rows_[1]), v3(rows_[2]), v3(rows_[3], timing="unknown"), v3(rows_[4]), v3(rows_[5])])
    report = run_v3(deal_snapshot)
    assert report["timing_only_failures"] == 1
    residual = (("CSH.US#E1", s, s - 3), ("MIX0.US#E1", DEALS["MIX0"]["last"] + 1, s))
    assert claim_demand(report["rows"], residual) == {"claim_demand": 1, "claim_contract": "stage_e2_required"}
    assert claim_demand(report["rows"], residual[1:]) == {"claim_demand": 0,
                                                          "claim_contract": "claim_not_built:no_consumer"}


def test_t_causal_6_paired_final_terms_leave_books_identical_before_settlement(tmp_path, monkeypatch):
    last = I_H + 300
    books = {}
    for name, cash, terms in (("late_a", 21, day(last + 2)), ("late_b", 30, day(last + 2)),
                              ("known_a", 21, day(last)), ("known_b", 30, day(last))):
        snap = terminal_snapshot(tmp_path / name, monkeypatch, name, {"CSH": target(last, 20.0)})
        write_v3(snap, [v3(curate("CSH", last, "cash", 0, cash=cash), terms=terms)])
        report = run_v3(snap)
        events = project(snap)
        books[name] = (report, events)
    assert books["late_a"][0]["rows"][0]["validation_reason"] == "terms_known_after_reference"
    assert len(books["late_a"][1]) == len(books["late_b"][1]) == 0
    assert len(books["known_a"][1]) == len(books["known_b"][1]) == 1
    prices = pd.DataFrame(20.0 * np.exp(np.cumsum(np.random.default_rng(9).normal(0, 0.01, (N, 4)), axis=0)),
                          index=CAL, columns=["CSH.US#E1", "B", "C", "D"])
    prices.iloc[last + 1:, 0] = np.nan
    signals = pd.DataFrame(1.0, index=CAL, columns=prices.columns)
    table = pd.DataFrame({"symbol": prices.columns, "permanent_id": prices.columns, "start_date": CAL[0],
                          "start_known_at": CAL[0], "end_date": pd.NaT, "end_known_at": pd.NaT})

    def book(events):
        frame = None
        if len(events):
            frame = events.assign(**{c: pd.to_datetime(events[c]) for c in ("effective_date", "known_at",
                                                                            "reference_date")},
                                  terminal_return=events["terminal_return"].astype(float))
        return run_long_only_backtest(prices, signals, source_provenance=capture_backtest_source_provenance(
            prices, signals), evaluation_start=CAL[I_H + 20], evaluation_end=CAL[last + 30], top_pct=1.0,
            constituent_intervals=table, terminal_events=frame, missing_price_policy="halt_gap_return_v1")

    known_a, known_b = book(books["known_a"][1]), book(books["known_b"][1])
    assert known_a.returns.loc[:CAL[last]].equals(known_b.returns.loc[:CAL[last]])
    assert known_a.returns.loc[CAL[last + 1]] != known_b.returns.loc[CAL[last + 1]]


def test_signal_eligibility_is_the_causal_evaluation_mask():
    prices = walk(4, 10)
    prices.iloc[int(RESETS[2]) + 3, 1] = np.nan
    schedule, bars = schedule_of(prices)
    assert schedule.evaluation_mask.equals(schedule.s_mask) and schedule.reasons == ()
    mask = resolve_pit_universe_mask(members(list(prices.columns)), None, DATES, list(prices.columns))
    assert schedule.s_mask.equals(signal_eligibility(mask, bars))
    included, unmeasured = ic_month_set(schedule)
    assert included[-1] == int(RESETS[-2]) and unmeasured == {"ic_month_horizon_unmeasured": (int(RESETS[-1]),)}
