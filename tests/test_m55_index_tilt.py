"""Synthetic tests for the Milestone 5.5 cap-weight and index-tilt engine (card m55-engine).

Every panel is generated here; no test reads data or opens a network connection.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

import research.m55_index_tilt as tilt
from research.m4_7_family_a import FAMILY_A_IDS
from research.m4_7_sp500_pit_rerun import RunnerStop


CAL = pd.bdate_range("1999-06-01", "2001-09-07", name="date")
END = pd.Timestamp("2001-08-31")
ASSETS = [f"S{k:02d}.US#E1" for k in range(12)]
SHARES = np.array([40, 20, 12, 8, 6, 5, 4, 3, 2.5, 2, 1.5, 1]) * 1e6
START = pd.Timestamp("2000-06-30")
LATE_ASSET = ASSETS[9]          # first close 100 rows before START: short history at the early rebalances
FEW_ASSET = ASSETS[11]          # three of six signals missing: c = 0
ME_ASSET = ASSETS[8]            # ME missing (stale_share_fact) in 2000-10
STOP_ASSET = ASSETS[3]          # last close 2001-02-14; held, then disappears
STOP_DATE = pd.Timestamp("2001-02-15")
FIELDS = list(tilt.DISAPPEARANCE_FIELDS)


def intervals(assets: list[str] = ASSETS, calendar: pd.DatetimeIndex = CAL) -> pd.DataFrame:
    return pd.DataFrame({"symbol": assets, "permanent_id": assets, "start_date": calendar[0],
                         "start_known_at": calendar[0], "end_date": pd.NaT, "end_known_at": pd.NaT})


def fixture(seed: int = 7, stop: bool = False) -> tilt.TiltInputs:
    rng = np.random.default_rng(seed)
    vol = np.linspace(0.05, 0.15, len(ASSETS))
    steps = 0.0003 + vol * rng.standard_normal((len(CAL), len(ASSETS)))
    prices = pd.DataFrame(50.0 * np.exp(np.cumsum(steps, axis=0)), index=CAL, columns=ASSETS)
    late = CAL.get_loc(START) - 100
    prices.iloc[:late, ASSETS.index(LATE_ASSET)] = np.nan
    if stop:
        prices.loc[STOP_DATE:, STOP_ASSET] = np.nan
    eligible = prices.notna()
    signals = {s: pd.DataFrame(rng.standard_normal(prices.shape), index=CAL, columns=ASSETS).where(eligible)
               for s in FAMILY_A_IDS}
    for s in FAMILY_A_IDS[:3]:
        signals[s][FEW_ASSET] = np.nan
    me = (prices * SHARES).where(eligible)
    reason = pd.DataFrame(None, index=CAL, columns=ASSETS, dtype=object)
    october = (CAL >= "2000-10-01") & (CAL <= "2000-10-31")
    me.loc[october, ME_ASSET] = np.nan
    reason.loc[october, ME_ASSET] = "stale_share_fact"
    disappearances = pd.DataFrame(columns=FIELDS)
    if stop:
        disappearances = pd.DataFrame([{"permanent_id": STOP_ASSET, "effective_date": STOP_DATE,
                                         "known_at": STOP_DATE, "cause": "failure", "delisting_return": np.nan}],
                                       columns=FIELDS)
    return tilt.TiltInputs(prices=prices, signals=signals, eligible=eligible, market_equity=me, me_reason=reason,
                           intervals=intervals(), disappearances=disappearances, start=START, end=END)


@pytest.fixture(scope="module")
def built() -> dict:
    return tilt.build_targets(fixture())


@pytest.fixture(scope="module")
def full_run() -> dict:
    return tilt.run_index_tilt(fixture(stop=True))


# Constants -------------------------------------------------------------------------------

def test_declared_constants() -> None:
    assert tilt.TIMING_CONTRACT == "after_close_signal_next_observed_close_v1"
    assert (tilt.TILT_STRENGTH, tilt.STOCK_CAP, tilt.TE_TARGET) == (0.5, 0.01, 0.02)
    assert (tilt.COV_ROWS, tilt.ANNUAL_ROWS, tilt.MIN_VALID_SIGNALS) == (252, 252, 4)
    assert (tilt.RENORMALIZE_LOOPS, tilt.CAP_TOLERANCE, tilt.TE_TOLERANCE) == (100, 1e-12, 1e-9)
    assert tilt.SIGNAL_IDS == FAMILY_A_IDS and len(tilt.SIGNAL_IDS) == 6
    assert tilt.ME_REASONS == ("unmapped", "ambiguous", "multi_class", "no_share_fact", "stale_share_fact")
    assert tilt.COST_SCHEDULE == ((None, 5.0, 20.0), ("2001-04-01", 2.0, 8.0), ("2007-01-01", 1.0, 4.0))
    assert tilt.COST_SCALES == {"primary": 1.0, "sensitivity_2x": 2.0}


# Future perturbation (R1) ------------------------------------------------------------------

PERTURB_AT = pd.Timestamp("2001-01-31")


def _perturbed(inputs: tilt.TiltInputs, field: str, first_row: int) -> tilt.TiltInputs:
    rng = np.random.default_rng(99)
    rows = slice(first_row, None)
    if field == "score":
        signals = {s: f.copy() for s, f in inputs.signals.items()}
        for frame in signals.values():
            frame.iloc[rows] = rng.standard_normal(frame.iloc[rows].shape)
        return replace(inputs, signals=signals)
    if field == "market_equity":
        me = inputs.market_equity.copy()
        me.iloc[rows] = me.iloc[rows] * rng.uniform(0.2, 5.0, me.iloc[rows].shape)
        return replace(inputs, market_equity=me)
    if field == "returns":
        prices = inputs.prices.copy()
        prices.iloc[rows] = prices.iloc[rows] * rng.uniform(0.5, 2.0, prices.iloc[rows].shape)
        return replace(inputs, prices=prices)
    eligible = inputs.eligible.copy()
    eligible.iloc[rows, :6] = False
    return replace(inputs, eligible=eligible)


@pytest.mark.parametrize("field", ["score", "market_equity", "returns", "eligibility"])
def test_inputs_on_or_after_row_r_change_no_weight_at_row_r(built: dict, field: str) -> None:
    r = CAL.get_loc(PERTURB_AT)
    after = tilt.build_targets(_perturbed(fixture(), field, r))
    for book in tilt.BOOKS:
        assert_frame_equal(after["targets"][book].loc[:PERTURB_AT], built["targets"][book].loc[:PERTURB_AT],
                           check_exact=True)
    assert_frame_equal(after["rebalances"].loc[:PERTURB_AT], built["rebalances"].loc[:PERTURB_AT], check_exact=True)


@pytest.mark.parametrize("field", ["score", "market_equity", "returns", "eligibility"])
def test_inputs_at_row_r_minus_1_do_change_the_weight_at_row_r(built: dict, field: str) -> None:
    r = CAL.get_loc(PERTURB_AT)
    after = tilt.build_targets(_perturbed(fixture(), field, r - 1))
    if field == "returns":
        before_te = built["rebalances"].loc[PERTURB_AT, "ex_ante_te_before_scale"]
        assert after["rebalances"].loc[PERTURB_AT, "ex_ante_te_before_scale"] != before_te
    else:
        assert not after["targets"]["tilt"].loc[PERTURB_AT].equals(built["targets"]["tilt"].loc[PERTURB_AT])


# Cap, renormalization, and tracking error ---------------------------------------------------

def test_every_rebalance_meets_the_cap_the_budget_and_the_te_limit(built: dict) -> None:
    returns = fixture().prices.pct_change(fill_method=None)
    for date in built["targets"]["tilt"].index:
        w = built["targets"]["tilt"].loc[date].dropna()
        b = built["targets"]["cw"].loc[date].dropna()
        assert w.index.equals(b.index)
        assert (w >= 0.0).all()
        assert math.fsum(w) == pytest.approx(1.0, abs=1e-12)
        assert (w - b).abs().max() <= tilt.STOCK_CAP + tilt.CAP_TOLERANCE
        t = CAL.get_loc(date) - 1
        window = returns.iloc[t - 251:t + 1][w.index]
        full = window.notna().all()
        assert ((w - b)[~full] == 0.0).all()
        cov = np.cov(window.loc[:, full].to_numpy(), rowvar=False, ddof=1)
        active = (w - b)[full].to_numpy()
        te = math.sqrt(252.0 * active @ cov @ active)
        assert te <= tilt.TE_TARGET * (1.0 + 1e-9)
        assert te == pytest.approx(built["rebalances"].loc[date, "ex_ante_te"], rel=1e-9, abs=1e-15)
    table = built["rebalances"]
    assert (table["te_scale"] < 1.0).any() and (table["te_scale"] == 1.0).any()
    assert (table["loops"] > 1).any()


def test_zero_scores_everywhere_give_cap_weight_exactly() -> None:
    inputs = fixture()
    flat = {s: f.where(f.isna(), 1.0) for s, f in inputs.signals.items()}
    result = tilt.run_index_tilt(replace(inputs, signals=flat))
    assert_frame_equal(result["targets"]["tilt"], result["targets"]["cw"], check_exact=True)
    for run in result["runs"].values():
        assert_series_equal(run["tilt"]["daily_net"], run["cw"]["daily_net"], check_exact=True)
        assert (run["active"]["daily"] == 0.0).all()


def test_score_rules_and_counts() -> None:
    assert tilt.signed_ranks(pd.Series([3.0, 1.0, 2.0, 2.0])).tolist() == [1.0, -1.0, 0.0, 0.0]
    assert tilt.signed_ranks(pd.Series([7.0])).tolist() == [0.0]
    thirds = tilt.signed_ranks(pd.Series([4.0, 3.0, 2.0, 1.0])).tolist()
    assert thirds[1] == -thirds[2] and thirds[1] == pytest.approx(1.0 / 3.0)
    names = ["A", "B", "C", "D"]
    rows = {s: pd.Series([4.0, 3.0, 2.0, 1.0], index=names) for s in FAMILY_A_IDS}
    for s in FAMILY_A_IDS[:3]:
        rows[s]["B"] = np.nan                      # B keeps three valid signals
    rows[FAMILY_A_IDS[5]]["A"] = np.nan             # A keeps five
    full = pd.Series([True, True, True, False], index=names)
    c, counts = tilt.composite_scores(rows, full)
    # A: ranks among the valid values only; D has a short history.
    a = np.mean([1.0, 1.0, 1.0, 1.0, 1.0])
    assert c["A"] == pytest.approx(a)
    assert c["B"] == 0.0 and c["D"] == 0.0
    # C: u = 0.5 among (A, C, D) on signals 1-3, u = 1/3 among all four on signals 4-5, u = 0.5 among (B, C, D).
    expected_c = np.mean([0.0, 0.0, 0.0, -1.0 / 3.0, -1.0 / 3.0, 0.0])
    assert c["C"] == pytest.approx(expected_c)
    assert counts == {"c_zero": 2, "c_zero_few_signals": 1, "c_zero_short_history": 1, "c_zero_window_gap": 0,
                      "c_zero_natural": 0}


def test_fixture_counts_c_zero_cases(built: dict) -> None:
    table = built["rebalances"]
    assert (table["c_zero_few_signals"] >= 1).all()            # FEW_ASSET at every rebalance
    assert table["c_zero_short_history"].iloc[0] >= 1           # LATE_ASSET early on
    assert table["c_zero_short_history"].iloc[-1] == 0
    assert built["counts"]["c_zero"] == int(table["c_zero"].sum())


# Hand-computed examples ---------------------------------------------------------------------

def test_hand_computed_cap_and_renormalize_loop() -> None:
    names = ["A", "B", "C", "D"]
    b = pd.Series([0.4, 0.3, 0.2, 0.1], index=names)
    c = pd.Series([1.0, -1.0, 0.5, 0.0], index=names)
    # Identical returns for every stock: any zero-sum active vector has zero TE.
    window = pd.DataFrame(np.tile(np.resize([0.01, -0.01], 252)[:, None], 4), columns=names)
    w, info = tilt.tilt_weights(b, c, window, pd.Series(False, index=names))
    # Tilt (0.6, 0.15, 0.25, 0.1); cap (0.41, 0.29, 0.21, 0.10). D has c = 0, so it stays at 0.1 exactly.
    # Renormalizing A, B, C to their cap-weight sum 0.9 pushes B below the cap again, so the loop
    # converges to B = 0.29 and A, C scaled by x = 0.61 / 0.62.
    x = 0.61 / 0.62
    assert w.tolist() == pytest.approx([0.41 * x, 0.29, 0.21 * x, 0.10], abs=1e-11)
    assert w["D"] == 0.1
    assert info["loops"] > 1 and info["te_scale"] == 1.0
    assert info["ex_ante_te"] == pytest.approx(0.0, abs=1e-15)


def test_hand_computed_te_scaling() -> None:
    names = ["A", "B", "C", "D"]
    b = pd.Series(0.25, index=names)
    c = pd.Series([0.04, -0.04, 0.0, 0.0], index=names)
    path = np.resize([0.2, -0.2], 252)
    window = pd.DataFrame({"A": path, "B": -path, "C": 0.0, "D": 0.0})
    w, info = tilt.tilt_weights(b, c, window, pd.Series(False, index=names))
    # Active (0.005, -0.005, 0, 0); daily active return 0.01 x (+-0.2); ddof-1 deviation 0.002 sqrt(252 / 251).
    te_before = math.sqrt(252) * 0.002 * math.sqrt(252 / 251)
    k = 0.02 / te_before
    assert info["ex_ante_te_before_scale"] == pytest.approx(te_before, rel=1e-12)
    assert info["te_scale"] == pytest.approx(k, rel=1e-12)
    assert w.tolist() == pytest.approx([0.25 + 0.005 * k, 0.25 - 0.005 * k, 0.25, 0.25], abs=1e-15)
    assert info["ex_ante_te"] == pytest.approx(0.02, rel=1e-12)


def test_loop_refuses_when_it_does_not_converge(monkeypatch: pytest.MonkeyPatch) -> None:
    names = ["A", "B", "C", "D"]
    b = pd.Series([0.4, 0.3, 0.2, 0.1], index=names)
    c = pd.Series([1.0, -1.0, 0.5, 0.0], index=names)
    window = pd.DataFrame(0.0, index=range(252), columns=names)
    monkeypatch.setattr(tilt, "RENORMALIZE_LOOPS", 3)
    with pytest.raises(RunnerStop, match="tilt_loop_not_converged"):
        tilt.tilt_weights(b, c, window, pd.Series(False, index=names))


def _four_stock_inputs() -> tilt.TiltInputs:
    calendar = pd.bdate_range("1999-01-01", "2000-04-07", name="date")
    names = ["A.US#E1", "B.US#E1", "C.US#E1", "D.US#E1"]
    prices = pd.DataFrame(100.0, index=calendar, columns=names)
    prices.loc["2000-03-15":, "A.US#E1"] = 110.0          # +10 percent on 2000-03-15 only
    order = pd.Series([4.0, 1.0, 3.0, 2.0], index=names)  # A > C > D > B on every signal
    signals = {s: pd.DataFrame(np.tile(order.to_numpy(), (len(calendar), 1)), index=calendar, columns=names)
               for s in FAMILY_A_IDS}
    me = prices * np.array([4.0, 3.0, 2.0, 1.0])
    return tilt.TiltInputs(prices=prices, signals=signals, eligible=prices.notna(), market_equity=me,
                           me_reason=pd.DataFrame(None, index=calendar, columns=names, dtype=object),
                           intervals=intervals(names, calendar), disappearances=pd.DataFrame(columns=FIELDS),
                           start=pd.Timestamp("2000-01-31"), end=pd.Timestamp("2000-03-31"))


def test_hand_computed_four_stock_rebalance() -> None:
    inputs = _four_stock_inputs()
    result = tilt.run_index_tilt(inputs)
    first, second = pd.Timestamp("2000-02-29"), pd.Timestamp("2000-03-31")
    targets = result["targets"]
    # c = (1, -1, 1/3, -1/3). First rebalance: b = (0.4, 0.3, 0.2, 0.1); every active weight hits the cap.
    assert targets["cw"].loc[first].tolist() == pytest.approx([0.4, 0.3, 0.2, 0.1], abs=1e-15)
    assert targets["tilt"].loc[first].tolist() == pytest.approx([0.41, 0.29, 0.21, 0.09], abs=1e-15)
    # Second rebalance: A's ME is 440 of 1040 at row r - 1.
    b2 = np.array([440.0, 300.0, 200.0, 100.0]) / 1040.0
    w2 = b2 + np.array([0.01, -0.01, 0.01, -0.01])
    assert targets["cw"].loc[second].tolist() == pytest.approx(b2.tolist(), abs=1e-15)
    assert targets["tilt"].loc[second].tolist() == pytest.approx(w2.tolist(), abs=1e-15)
    # Turnover against the drifted book: A grew 10 percent, so the book grew by 1 + 0.41 x 0.10.
    drifted = np.array([0.451, 0.29, 0.21, 0.09]) / 1.041
    turnover = float(np.abs(w2 - drifted).sum())
    book = result["runs"][("primary", "primary")]["tilt"]
    assert book["turnover"].loc[first] == pytest.approx(1.0, abs=1e-15)
    assert book["turnover"].loc[second] == pytest.approx(turnover, abs=1e-15)
    # Year 2000 rate: 5 + 20 bp one way; the rebalance rows carry no price move.
    assert book["cost"].loc[first] == pytest.approx(0.0025, abs=1e-15)
    assert book["cost"].loc[second] == pytest.approx(turnover * 0.0025, abs=1e-15)
    stressed = result["runs"][("sensitivity_2x", "primary")]["tilt"]
    assert stressed["cost"].loc[second] == pytest.approx(turnover * 0.0050, abs=1e-15)
    cw_turnover = float(np.abs(b2 - np.array([0.44, 0.3, 0.2, 0.1]) / 1.04).sum())
    assert result["runs"][("primary", "primary")]["cw"]["turnover"].loc[second] == pytest.approx(cw_turnover, abs=1e-15)


# Market equity status -----------------------------------------------------------------------

def test_me_missing_member_leaves_both_books_and_is_counted(built: dict, full_run: dict) -> None:
    october = pd.Timestamp("2000-10-31")
    for book in tilt.BOOKS:
        assert np.isnan(built["targets"][book].loc[october, ME_ASSET])
        assert np.isfinite(built["targets"][book].loc[pd.Timestamp("2000-09-29"), ME_ASSET])
        held = full_run["runs"][("primary", "primary")][book]["weights"]
        assert held.loc[october, ME_ASSET] == 0.0
    table = built["rebalances"]
    assert table.loc[october, "me_missing"] == 1 and table.loc[october, "me_missing_stale_share_fact"] == 1
    assert built["counts"]["me_missing"] == 1 and built["counts"]["me_missing_stale_share_fact"] == 1
    assert built["counts"]["me_missing_unmapped"] == 0


@pytest.mark.parametrize(("reason", "code"), [(None, "me_reason_invalid"), ("guess", "me_reason_invalid")])
def test_me_missing_without_a_typed_reason_refuses(reason: str | None, code: str) -> None:
    inputs = fixture()
    october = (CAL >= "2000-10-01") & (CAL <= "2000-10-31")
    inputs.me_reason.loc[october, ME_ASSET] = reason
    with pytest.raises(RunnerStop, match=code):
        tilt.build_targets(inputs)


def test_invalid_or_conflicting_me_refuses() -> None:
    inputs = fixture()
    inputs.market_equity.loc["2000-08-30", ASSETS[0]] = -1.0
    with pytest.raises(RunnerStop, match="me_invalid"):
        tilt.build_targets(inputs)
    inputs = fixture()
    inputs.me_reason.loc["2000-08-30", ASSETS[0]] = "unmapped"
    with pytest.raises(RunnerStop, match="me_reason_conflict"):
        tilt.build_targets(inputs)


@pytest.mark.parametrize("dtype", ["boolean", "object", "float64"])
def test_eligible_must_be_plain_boolean(dtype: str) -> None:
    # R6: a nullable or non-boolean eligibility frame refuses; it is never coerced.
    inputs = fixture()
    inputs = replace(inputs, eligible=inputs.eligible.astype(dtype))
    with pytest.raises(RunnerStop, match="eligible_not_boolean"):
        tilt.build_targets(inputs)


# Disappearance (R4) -------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("cause", "supplied", "run", "expected"),
    [
        ("failure", -0.3, "primary", -0.3),
        ("failure", np.nan, "primary", -1.0),
        ("unknown", np.nan, "primary", -1.0),
        ("cash_merger", np.nan, "primary", 0.0),
        ("failure", -0.3, "last_close", 0.0),
    ],
)
def test_held_disappearance_settles_identically_in_both_books(cause: str, supplied: float, run: str,
                                                              expected: float) -> None:
    inputs = fixture(stop=True)
    table = pd.DataFrame([{"permanent_id": STOP_ASSET, "effective_date": STOP_DATE, "known_at": STOP_DATE,
                           "cause": cause, "delisting_return": supplied}], columns=FIELDS)
    built = tilt.build_targets(replace(inputs, disappearances=table))
    events = tilt.terminal_events(built["disappearances"], CAL, run)
    costs = tilt.dated_cost_frame(CAL)
    logs = {}
    for book in tilt.BOOKS:
        result = tilt.run_book(inputs, built["targets"][book], events, costs)
        (record,) = [r for r in result.terminal_event_log if r["permanent_id"] == STOP_ASSET]
        assert record["incoming_weight"] > 0.0
        assert record["terminal_return"] == expected
        assert result.holdings.loc[STOP_DATE:, STOP_ASSET].eq(0.0).all()
        logs[book] = record
    assert logs["cw"]["effective_date"] == logs["tilt"]["effective_date"]
    for book in tilt.BOOKS:
        assert np.isnan(built["targets"][book].loc[pd.Timestamp("2001-02-28"), STOP_ASSET])


def test_full_run_reports_r4_events_and_fragility(full_run: dict) -> None:
    for key, run in full_run["runs"].items():
        for book in tilt.BOOKS:
            assert run[book]["held_events"]["count"] == 1
            assert run[book]["held_events"]["weight_sum"] > 0.0
    primary = full_run["runs"][("primary", "primary")]
    rerun = full_run["runs"][("primary", "last_close")]
    for book in tilt.BOOKS:
        assert primary[book]["monthly_net"].loc["2001-02"] < rerun[book]["monthly_net"].loc["2001-02"]
    assert set(full_run["fragile_active_sign"]) == {"primary", "sensitivity_2x"}


def test_disappearance_table_is_validated() -> None:
    inputs = fixture(stop=True)
    bad = pd.DataFrame([{"permanent_id": STOP_ASSET, "effective_date": STOP_DATE, "known_at": STOP_DATE,
                         "cause": "merger", "delisting_return": np.nan}], columns=FIELDS)
    with pytest.raises(RunnerStop, match="disappearances_invalid"):
        tilt.build_targets(replace(inputs, disappearances=bad))
    bad = bad.assign(cause="failure", delisting_return=-1.5)
    with pytest.raises(RunnerStop, match="disappearances_invalid"):
        tilt.build_targets(replace(inputs, disappearances=bad))


# Costs (R8) ---------------------------------------------------------------------------------

def test_cost_schedule_switches_at_the_declared_dates() -> None:
    dates = pd.DatetimeIndex(["1995-01-03", "2001-03-30", "2001-04-02", "2006-12-29", "2007-01-02", "2020-06-01"])
    frame = tilt.dated_cost_frame(dates)
    assert frame["transaction_cost_bps"].tolist() == [5.0, 5.0, 2.0, 2.0, 1.0, 1.0]
    assert frame["slippage_bps"].tolist() == [20.0, 20.0, 8.0, 8.0, 4.0, 4.0]
    double = tilt.dated_cost_frame(dates, scale=2.0)
    assert (double == 2.0 * frame).all().all()
    with pytest.raises(RunnerStop, match="cost_schedule_invalid"):
        tilt.dated_cost_frame(dates, ((None, 1.0, 1.0), ("2007-01-01", 1.0, 1.0), ("2001-04-01", 1.0, 1.0)))


def test_engine_charges_the_rate_of_each_rebalance_row(full_run: dict) -> None:
    book = full_run["runs"][("primary", "primary")]["tilt"]
    gross = book["daily_gross"]
    for date, rate in [("2001-03-30", 25.0), ("2001-04-30", 10.0), ("2001-07-31", 10.0)]:
        date = pd.Timestamp(date)
        expected = book["turnover"].loc[date] * rate / 10_000.0 * (1.0 + gross.loc[date])
        assert book["turnover"].loc[date] > 0.0
        assert book["cost"].loc[date] == pytest.approx(expected, rel=1e-12)


def test_outputs_per_book(full_run: dict) -> None:
    run = full_run["runs"][("primary", "primary")]
    for book in tilt.BOOKS:
        out = run[book]
        assert_series_equal(out["daily_net"], out["daily_gross"] - out["cost"], check_names=False, atol=1e-15)
        assert out["annual_turnover"] > 0.0 and out["annual_cost_drag"] > 0.0
        assert str(out["monthly_net"].index[0]) == "2000-08"     # first rebalance 2000-07-31 earns from August
        assert out["weights"].index.equals(full_run["targets"][book].index)
    active = run["active"]
    assert_series_equal(active["daily"], run["tilt"]["daily_net"] - run["cw"]["daily_net"])
    assert active["realized_te_daily"] > 0.0 and active["realized_te_monthly"] > 0.0
    assert {"ex_ante_te", "c_zero", "me_missing"} <= set(full_run["rebalances"].columns)
    stressed = full_run["runs"][("sensitivity_2x", "primary")]
    assert stressed["tilt"]["annual_cost_drag"] == pytest.approx(2.0 * run["tilt"]["annual_cost_drag"], rel=0.05)


def test_engine_membership_disagreement_fails_closed() -> None:
    inputs = fixture()
    built = tilt.build_targets(inputs)
    short = intervals()
    short.loc[0, ["end_date", "end_known_at"]] = pd.Timestamp("2000-09-01")   # the engine drops S00 from September
    with pytest.raises(RunnerStop, match="engine_target_mismatch"):
        tilt.run_book(replace(inputs, intervals=short), built["targets"]["cw"],
                      tilt.terminal_events(built["disappearances"], CAL, "primary"), tilt.dated_cost_frame(CAL))


# Repair round 1 ------------------------------------------------------------------------------

def _event(asset: str, effective: str, known: str, cause: str = "unknown") -> pd.DataFrame:
    return pd.DataFrame([{"permanent_id": asset, "effective_date": pd.Timestamp(effective),
                          "known_at": pd.Timestamp(known), "cause": cause, "delisting_return": np.nan}],
                        columns=FIELDS)


def test_event_known_at_the_cutoff_leaves_the_pool_at_r() -> None:
    # GPT-R1-01: A settles at the 2000-02-29 close and the caller says it was known on 2000-02-28.
    inputs = _four_stock_inputs()
    built = tilt.build_targets(replace(inputs, disappearances=_event("A.US#E1", "2000-02-29", "2000-02-28")))
    first = pd.Timestamp("2000-02-29")
    cw = built["targets"]["cw"].loc[first]
    assert np.isnan(cw["A.US#E1"])
    assert cw.dropna().tolist() == pytest.approx([0.5, 1.0 / 3.0, 1.0 / 6.0], abs=1e-15)
    assert built["rebalances"].loc[first, "settled_excluded"] == 1


def test_event_unknown_at_the_cutoff_that_settles_at_execution_refuses() -> None:
    # GPT-R1-01: the same event, first known at the effective close, may not change the target; it refuses.
    inputs = _four_stock_inputs()
    with pytest.raises(RunnerStop, match="event_unknown_at_cutoff"):
        tilt.build_targets(replace(inputs, disappearances=_event("A.US#E1", "2000-02-29", "2000-02-29")))


def test_event_known_early_but_effective_later_keeps_the_member_until_it_settles() -> None:
    inputs = _four_stock_inputs()
    base = tilt.build_targets(inputs)
    built = tilt.build_targets(replace(inputs, disappearances=_event("A.US#E1", "2000-03-15", "1999-12-01",
                                                                     "cash_merger")))
    first, second = pd.Timestamp("2000-02-29"), pd.Timestamp("2000-03-31")
    for book in tilt.BOOKS:
        assert_series_equal(built["targets"][book].loc[first], base["targets"][book].loc[first], check_exact=True)
        assert np.isnan(built["targets"][book].loc[second, "A.US#E1"])


@pytest.mark.parametrize(("effective", "known"), [("2001-02-15", "2001-01-31"), ("2001-02-15", "2001-02-15"),
                                                  ("2001-03-30", "2001-02-01"), ("2001-01-31", "2001-01-31"),
                                                  ("2001-01-31", "2001-01-30")])
def test_events_change_the_target_at_r_only_when_known_at_r_minus_1(built: dict, effective: str,
                                                                     known: str) -> None:
    # Events known at or after r (or effective after r) change nothing at r; an event effective and first
    # known at r itself refuses instead of changing the target. The pair of that case (B3): the same event
    # known at r - 1 removes the member at r and changes no earlier target.
    inputs = replace(fixture(), disappearances=_event(ASSETS[2], effective, known))
    if pd.Timestamp(effective) == pd.Timestamp(known) == PERTURB_AT:
        with pytest.raises(RunnerStop, match="event_unknown_at_cutoff"):
            tilt.build_targets(inputs)
        return
    after = tilt.build_targets(inputs)
    used = pd.Timestamp(effective) <= PERTURB_AT
    same = pd.Timestamp("2000-12-29") if used else PERTURB_AT
    for book in tilt.BOOKS:
        assert_frame_equal(after["targets"][book].loc[:same], built["targets"][book].loc[:same], check_exact=True)
        assert np.isnan(after["targets"][book].loc[PERTURB_AT, ASSETS[2]]) == used


def test_event_known_at_r_minus_1_does_change_row_r(built: dict) -> None:
    inputs = replace(fixture(), disappearances=_event(ASSETS[2], "2001-01-31", "2001-01-30"))
    after = tilt.build_targets(inputs)
    assert np.isnan(after["targets"]["cw"].loc[PERTURB_AT, ASSETS[2]])
    assert_frame_equal(after["targets"]["cw"].loc[:"2000-12-29"], built["targets"]["cw"].loc[:"2000-12-29"],
                       check_exact=True)


@pytest.mark.parametrize(("effective", "known"), [("2001-02-15", "2001-02-16"), ("2001-02-15", "2001-02-17")])
def test_known_at_is_validated(effective: str, known: str) -> None:
    inputs = fixture(stop=True)
    with pytest.raises(RunnerStop, match="disappearances_invalid"):
        tilt.build_targets(replace(inputs, disappearances=_event(STOP_ASSET, effective, known)))


@pytest.mark.parametrize("case", ["few_signals", "natural_zero"])
def test_members_with_zero_score_stay_at_cap_weight_in_target_and_holdings(case: str) -> None:
    # GPT-R1-02: a complete-history member with c = 0 keeps w = b while the others tilt.
    inputs = _four_stock_inputs()
    names = list(inputs.prices.columns)
    signals = {s: f.copy() for s, f in inputs.signals.items()}
    if case == "few_signals":
        for s in FAMILY_A_IDS[:3]:
            signals[s]["D.US#E1"] = np.nan
        zero = ["D.US#E1"]
    else:
        # D is top on three signals and bottom on three; C ranks 1/3 and 2/3: both composites are exactly 0.
        for s in FAMILY_A_IDS[:3]:
            signals[s].loc[:, names] = [3.0, 0.0, 1.0, 4.0]
        for s in FAMILY_A_IDS[3:]:
            signals[s].loc[:, names] = [4.0, 2.0, 3.0, 1.0]
        zero = ["C.US#E1", "D.US#E1"]
    inputs = replace(inputs, signals=signals)
    built = tilt.build_targets(inputs)
    table = built["rebalances"]
    if case == "few_signals":
        assert (table["c_zero_few_signals"] == 1).all()
    else:
        assert (table["c_zero_natural"] == 2).all()
    events = tilt.terminal_events(built["disappearances"], inputs.prices.index, "primary")
    result = tilt.run_book(inputs, built["targets"]["tilt"], events, tilt.dated_cost_frame(inputs.prices.index))
    for date in built["targets"]["tilt"].index:
        w, b = built["targets"]["tilt"].loc[date], built["targets"]["cw"].loc[date]
        assert (w[zero] == b[zero]).all()
        assert (result.holdings.loc[date, zero] == b[zero]).all()
        assert (w.drop(zero) != b.drop(zero)).all()
        assert math.fsum(w) == pytest.approx(1.0, abs=1e-15)


@pytest.mark.parametrize("case", ["primary", "sensitivity_2x"])
def test_monthly_returns_keep_the_first_purchase_cost(case: str) -> None:
    # GPT-R1-03: flat prices; the only return is the first purchase cost on 2000-02-29.
    inputs = _four_stock_inputs()
    flat = pd.DataFrame(100.0, index=inputs.prices.index, columns=inputs.prices.columns)
    inputs = replace(inputs, prices=flat, market_equity=flat * np.array([4.0, 3.0, 2.0, 1.0]))
    result = tilt.run_index_tilt(inputs)
    rate = 0.0025 * tilt.COST_SCALES[case]
    for book in tilt.BOOKS:
        out = result["runs"][(case, "primary")][book]
        assert out["daily_net"].index[0] == pd.Timestamp("2000-02-29")
        assert out["initial_purchase_cost"] == pytest.approx(rate, abs=1e-15)
        assert out["monthly_net"].loc["2000-03"] == pytest.approx(-rate, abs=1e-15)
        assert np.prod(1.0 + out["monthly_net"]) == pytest.approx(np.prod(1.0 + out["daily_net"]), abs=1e-15)


def test_monthly_growth_equals_daily_growth_with_active_returns(full_run: dict) -> None:
    for run in full_run["runs"].values():
        for book in tilt.BOOKS:
            out = run[book]
            assert np.prod(1.0 + out["monthly_net"]) == pytest.approx(np.prod(1.0 + out["daily_net"]), rel=1e-12)
            assert str(out["monthly_net"].index[0]) == "2000-08"
            assert out["daily_net"].index[0] == pd.Timestamp("2000-07-31")     # no all-cash rows (A3)
            # GPT-R2-01: one monthly row per holding month, all inside the span (August 2000 to the end month).
            assert out["monthly_net"].index.equals(pd.period_range("2000-08", "2001-08", freq="M"))
            assert len(out["monthly_net"]) == len(full_run["rebalances"]) - 1
            assert out["daily_net"].index[-1] == END
        assert run["active"]["monthly"].abs().max() > 0.0


@pytest.mark.parametrize("value", [np.inf, -np.inf, 0.0, -5.0])
def test_invalid_present_price_before_the_window_refuses(value: float) -> None:
    # GPT-R1-04: the bad close is in the covariance window and before the accounting start.
    inputs = _four_stock_inputs()
    inputs.prices.loc["1999-10-15", "A.US#E1"] = value
    with pytest.raises(RunnerStop, match="price_invalid"):
        tilt.build_targets(inputs)


@pytest.mark.parametrize("break_it", ["nan", "negative", "budget", "cap", "te"])
def test_target_check_refuses_invalid_books(break_it: str) -> None:
    b = np.array([0.4, 0.3, 0.2, 0.1])
    w = np.array([0.41, 0.29, 0.21, 0.09])
    info = {"loops": 1, "ex_ante_te": 0.01}
    if break_it == "nan":
        w = np.array([np.nan, 0.29, 0.21, 0.09])
    elif break_it == "negative":
        w = np.array([0.51, 0.29, 0.21, -0.01])
    elif break_it == "budget":
        w = np.array([0.41, 0.29, 0.21, 0.10])
    elif break_it == "cap":
        w = np.array([0.42, 0.28, 0.21, 0.09])
    else:
        info = {"loops": 1, "ex_ante_te": 0.03}
    tilt.check_target(b, np.array([0.41, 0.29, 0.21, 0.09]), {"loops": 1, "ex_ante_te": 0.01})
    with pytest.raises(RunnerStop, match="target_invalid"):
        tilt.check_target(b, w, info)


@pytest.mark.parametrize("end", ["2001-08-15", "2001-09-07"])
def test_window_end_must_be_a_month_end_row(end: str) -> None:
    # A2: a mid-month end, or an end with no later row in a later month, refuses.
    with pytest.raises(RunnerStop, match="window_end_not_month_end"):
        tilt.build_targets(replace(fixture(), end=pd.Timestamp(end)))


def test_terminal_rebalance_cost_is_reported(full_run: dict) -> None:
    out = full_run["runs"][("primary", "primary")]["tilt"]
    assert out["terminal_rebalance_cost"] == out["cost"].loc[END] > 0.0


def test_halt_gap_is_counted_apart_from_short_history() -> None:
    # A4: a three-day gap inside the window pins the member as a window gap, not as a short history.
    base = tilt.build_targets(fixture())
    inputs = fixture()
    inputs.prices.loc["2000-08-14":"2000-08-16", ASSETS[5]] = np.nan
    after = tilt.build_targets(inputs)
    inside = slice("2000-08-31", "2001-07-31")            # rebalances whose 252-row window holds the gap
    later = after["rebalances"].loc[inside]
    assert (later["c_zero_window_gap"] == 1).all()
    assert after["rebalances"].loc["2001-08-31", "c_zero_window_gap"] == 0
    assert_series_equal(later["c_zero_short_history"], base["rebalances"].loc[inside, "c_zero_short_history"])
    assert (after["targets"]["tilt"].loc[inside, ASSETS[5]] == after["targets"]["cw"].loc[inside, ASSETS[5]]).all()


def test_future_me_reason_changes_no_target(built: dict) -> None:
    inputs = fixture()
    r = CAL.get_loc(PERTURB_AT)
    inputs.market_equity.iloc[r:, 0] = np.nan
    inputs.me_reason.iloc[r:, 0] = "ambiguous"
    after = tilt.build_targets(inputs)
    assert_frame_equal(after["targets"]["tilt"].loc[:PERTURB_AT], built["targets"]["tilt"].loc[:PERTURB_AT],
                       check_exact=True)
    assert np.isnan(after["targets"]["tilt"].loc["2001-02-28", ASSETS[0]])


def test_empty_book_and_one_member_book() -> None:
    inputs = _four_stock_inputs()
    nobody = inputs.eligible.copy()
    nobody.loc["2000-02-28"] = False
    with pytest.raises(RunnerStop, match="empty_book"):
        tilt.build_targets(replace(inputs, eligible=nobody))
    alone = inputs.eligible.copy()
    alone.loc[:, ["B.US#E1", "C.US#E1", "D.US#E1"]] = False
    built = tilt.build_targets(replace(inputs, eligible=alone))
    for book in tilt.BOOKS:
        assert built["targets"][book]["A.US#E1"].tolist() == [1.0, 1.0]


def test_engine_rebalance_mismatch_refuses() -> None:
    inputs = _four_stock_inputs()
    built = tilt.build_targets(inputs)
    events = tilt.terminal_events(built["disappearances"], inputs.prices.index, "primary")
    with pytest.raises(RunnerStop, match="engine_rebalance_mismatch"):
        tilt.check_engine_targets(tilt.run_book(inputs, built["targets"]["cw"], events,
                                                tilt.dated_cost_frame(inputs.prices.index)),
                                  built["targets"]["cw"].iloc[:1], inputs.prices.index)


def test_member_leaving_the_index_between_rebalances() -> None:
    # S01 leaves on 2000-11-15 in both the intervals and the eligibility: it is sold at the next rebalance.
    inputs = fixture()
    table = intervals()
    table.loc[1, ["end_date", "end_known_at"]] = pd.Timestamp("2000-11-15")
    eligible = inputs.eligible.copy()
    eligible.loc["2000-11-15":, ASSETS[1]] = False
    inputs = replace(inputs, intervals=table, eligible=eligible)
    built = tilt.build_targets(inputs)
    events = tilt.terminal_events(built["disappearances"], CAL, "primary")
    for book in tilt.BOOKS:
        result = tilt.run_book(inputs, built["targets"][book], events, tilt.dated_cost_frame(CAL))
        assert result.holdings.loc["2000-10-31", ASSETS[1]] > 0.0
        assert result.holdings.loc["2000-11-30":, ASSETS[1]].eq(0.0).all()


def test_loop_converges_on_a_concentrated_book_with_adversarial_scores() -> None:
    # A1 stress: 500 Zipf cap weights (top weight about 15 percent); the top 20 at c = +1, all others at c = -1.
    n = 500
    names = [f"N{k:03d}" for k in range(n)]
    raw = 1.0 / np.arange(1, n + 1)
    b = pd.Series(raw / raw.sum(), index=names)
    c = pd.Series(np.where(np.arange(n) < 20, 1.0, -1.0), index=names)
    rng = np.random.default_rng(5)
    window = pd.DataFrame(rng.normal(0.0, 0.02, (252, n)), columns=names)
    w, info = tilt.tilt_weights(b, c, window, pd.Series(False, index=names))
    assert info["loops"] < tilt.RENORMALIZE_LOOPS
    assert (w >= 0.0).all() and math.fsum(w) == pytest.approx(1.0, abs=1e-12)
    assert (w - b).abs().max() <= tilt.STOCK_CAP + tilt.CAP_TOLERANCE


# Expert repair after review round 2 ------------------------------------------------------------

@pytest.mark.parametrize("start", ["2000-01-31", "2000-02-15"])
def test_window_with_one_rebalance_refuses(start: str) -> None:
    # GPT-R2-01: the only rebalance is at ``end``, so no holding month follows it inside the window. The full
    # run refuses in ``build_targets``, before either cost case runs, and returns no monthly row.
    inputs = replace(_four_stock_inputs(), start=pd.Timestamp(start), end=pd.Timestamp("2000-02-29"))
    with pytest.raises(RunnerStop, match="window_too_short"):
        tilt.run_index_tilt(inputs)


@pytest.mark.parametrize("case", list(tilt.COST_SCALES))
def test_minimum_window_reports_one_month_inside_the_span(case: str) -> None:
    # GPT-R2-01: two rebalances (2000-02-29 and ``end`` 2000-03-31) give exactly one monthly row, March 2000.
    result = tilt.run_index_tilt(_four_stock_inputs())
    march = pd.PeriodIndex(["2000-03"], freq="M")
    rows = 1 + len(pd.bdate_range("2000-03-01", "2000-03-31"))
    for event_run in tilt.EVENT_RUNS:
        run = result["runs"][(case, event_run)]
        for book in tilt.BOOKS:
            out = run[book]
            assert out["daily_net"].index[0] == pd.Timestamp("2000-02-29")
            assert out["daily_net"].index[-1] == pd.Timestamp("2000-03-31")
            assert len(out["daily_net"]) == rows
            assert out["monthly_net"].index.equals(march)
            assert np.prod(1.0 + out["monthly_net"]) == pytest.approx(np.prod(1.0 + out["daily_net"]), rel=1e-12)
        active = run["active"]
        assert active["monthly"].index.equals(march)
        assert active["mean_monthly"] == active["monthly"].iloc[0]
        assert active["realized_te_monthly"] is None
        assert len(active["daily"]) == rows and math.isfinite(active["realized_te_daily"])


def test_monthly_row_after_the_last_rebalance_refuses() -> None:
    # GPT-R2-01: the summary refuses a monthly row outside the evaluation span. Measured from ``end`` only, the
    # one daily row would report April 2000.
    inputs = _four_stock_inputs()
    built = tilt.build_targets(inputs)
    target = built["targets"]["cw"]
    events = tilt.terminal_events(built["disappearances"], inputs.prices.index, "primary")
    result = tilt.run_book(inputs, target, events, tilt.dated_cost_frame(inputs.prices.index))
    assert tilt.book_summary(result, target)["monthly_net"].index.equals(pd.PeriodIndex(["2000-03"], freq="M"))
    with pytest.raises(RunnerStop, match="monthly_period_invalid"):
        tilt.book_summary(result, target.iloc[-1:])
    # A daily row after the last rebalance, in the same month, also refuses.
    early = target.rename(index={pd.Timestamp("2000-03-31"): pd.Timestamp("2000-03-30")})
    with pytest.raises(RunnerStop, match="monthly_period_invalid"):
        tilt.book_summary(result, early)


@pytest.mark.parametrize("start", ["2000-01-14", "1999-11-30"])
def test_calendar_without_a_month_inside_the_window_refuses(start: str) -> None:
    # An empty February 2000, right after the first rebalance or between two rebalances, would give a monthly row
    # without daily rows or join two holding months, so the run refuses.
    inputs = _four_stock_inputs()
    keep = inputs.prices.index.to_period("M") != pd.Period("2000-02", freq="M")
    inputs = replace(inputs, prices=inputs.prices.loc[keep], eligible=inputs.eligible.loc[keep],
                     signals={s: f.loc[keep] for s, f in inputs.signals.items()},
                     market_equity=inputs.market_equity.loc[keep], me_reason=inputs.me_reason.loc[keep],
                     start=pd.Timestamp(start))
    with pytest.raises(RunnerStop, match="calendar_month_missing"):
        tilt.run_index_tilt(inputs)


def test_eleven_member_natural_zero_is_exact_and_stays_at_cap_weight() -> None:
    # Opus B1: X ranks 7 of 11 on three signals and 3 of 11 on the fourth, and misses two signals. Its signed
    # ranks are (0.2, 0.2, 0.2, -0.6), so c = 0; in floating point the same sum is about 1.39e-17.
    names = [f"M{k:02d}" for k in range(11)]
    x = names[6]
    rows = {s: pd.Series(np.arange(1.0, 12.0), index=names) for s in FAMILY_A_IDS[:3]}
    rows[FAMILY_A_IDS[3]] = pd.Series([1.0, 2.0, 4.0, 5.0, 6.0, 7.0, 3.0, 8.0, 9.0, 10.0, 11.0], index=names)
    for s in FAMILY_A_IDS[4:]:
        rows[s] = pd.Series(np.arange(11.0), index=names)
        rows[s][x] = np.nan
    assert math.fsum([0.2, 0.2, 0.2, -0.6]) != 0.0
    full = pd.Series(True, index=names)
    c, counts = tilt.composite_scores(rows, full)
    assert c[x] == 0.0
    assert (c.drop(x) != 0.0).all()                   # every other composite has one sign on all six signals
    assert counts["c_zero_natural"] == counts["c_zero"] == 1
    b = pd.Series(np.arange(11.0, 0.0, -1.0) / 66.0, index=names)
    window = pd.DataFrame(np.random.default_rng(3).normal(0.0, 0.1, (252, 11)), columns=names)
    w, info = tilt.tilt_weights(b, c, window, pd.Series(False, index=names))
    assert info["te_scale"] < 1.0
    assert w[x] == b[x]
    assert (w.drop(x) != b.drop(x)).all()


def test_natural_zeros_are_exact_at_a_realistic_book_size() -> None:
    # Opus B1: 500 members in four equal tie groups per signal. Level l has signed rank (250 l - 375) / 499, so a
    # composite is zero exactly when the six levels sum to 9; many of these do not cancel in floating point.
    n = 500
    names = [f"N{k:03d}" for k in range(n)]
    rng = np.random.default_rng(11)
    levels = np.column_stack([rng.permutation(np.repeat(np.arange(4.0), n // 4)) for _ in FAMILY_A_IDS])
    rows = {s: pd.Series(levels[:, k], index=names) for k, s in enumerate(FAMILY_A_IDS)}
    zero = pd.Series(levels.sum(axis=1) == 9.0, index=names)
    c, counts = tilt.composite_scores(rows, pd.Series(True, index=names))
    assert zero.sum() > 50
    assert (c[zero] == 0.0).all() and (c[~zero] != 0.0).all()
    assert counts["c_zero_natural"] == counts["c_zero"] == int(zero.sum())
    raw = 1.0 / np.arange(1, n + 1)
    b = pd.Series(raw / raw.sum(), index=names)
    window = pd.DataFrame(rng.normal(0.0, 0.2, (252, n)), columns=names)
    w, info = tilt.tilt_weights(b, c, window, pd.Series(False, index=names))
    assert info["te_scale"] < 1.0
    assert (w[zero] == b[zero]).all()
