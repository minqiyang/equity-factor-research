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


CAL = pd.bdate_range("1999-06-01", "2001-08-31", name="date")
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
                                         "cause": "failure", "delisting_return": np.nan}], columns=FIELDS)
    return tilt.TiltInputs(prices=prices, signals=signals, eligible=eligible, market_equity=me, me_reason=reason,
                           intervals=intervals(), disappearances=disappearances, start=START, end=CAL[-1])


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
    assert tilt.percentile_ranks(pd.Series([3.0, 1.0, 2.0, 2.0])).tolist() == [1.0, 0.0, 0.5, 0.5]
    assert tilt.percentile_ranks(pd.Series([7.0])).tolist() == [0.5]
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
    assert counts == {"c_zero": 2, "c_zero_few_signals": 1, "c_zero_short_history": 1}


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
    # Tilt (0.6, 0.15, 0.25, 0.1); cap (0.41, 0.29, 0.21, 0.10). Renormalizing pushes B below the cap
    # again, so the loop converges to B = 0.29 and the rest scaled by x = 0.71 / 0.72.
    x = 0.71 / 0.72
    assert w.tolist() == pytest.approx([0.41 * x, 0.29, 0.21 * x, 0.10 * x], abs=1e-11)
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
    calendar = pd.bdate_range("1999-01-01", "2000-03-31", name="date")
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
    table = pd.DataFrame([{"permanent_id": STOP_ASSET, "effective_date": STOP_DATE, "cause": cause,
                           "delisting_return": supplied}], columns=FIELDS)
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
    bad = pd.DataFrame([{"permanent_id": STOP_ASSET, "effective_date": STOP_DATE, "cause": "merger",
                         "delisting_return": np.nan}], columns=FIELDS)
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
