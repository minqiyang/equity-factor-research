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


def fixture(seed: int = 7, stop: bool = False, stop_asset: str = STOP_ASSET,
            stop_date: pd.Timestamp = STOP_DATE) -> tilt.TiltInputs:
    rng = np.random.default_rng(seed)
    vol = np.linspace(0.05, 0.15, len(ASSETS))
    steps = 0.0003 + vol * rng.standard_normal((len(CAL), len(ASSETS)))
    prices = pd.DataFrame(50.0 * np.exp(np.cumsum(steps, axis=0)), index=CAL, columns=ASSETS)
    late = CAL.get_loc(START) - 100
    prices.iloc[:late, ASSETS.index(LATE_ASSET)] = np.nan
    if stop:
        prices.loc[stop_date:, stop_asset] = np.nan
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
        disappearances = pd.DataFrame([{"permanent_id": stop_asset, "effective_date": stop_date,
                                         "known_at": stop_date, "cause": "failure", "delisting_return": np.nan}],
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


def test_event_unknown_at_the_cutoff_leaves_the_traded_set_but_not_the_ranks() -> None:
    # B2: the same event, first known at the effective close, cannot trade at r. The r - 1 ranks keep A, so
    # c = (-1, 1/3, -1/3) for B, C, D; the event known at r - 1 ranks B, C, D alone: c = (-1, 1, 0).
    inputs = _four_stock_inputs()
    unknown = tilt.build_targets(replace(inputs, disappearances=_event("A.US#E1", "2000-02-29", "2000-02-29")))
    known = tilt.build_targets(replace(inputs, disappearances=_event("A.US#E1", "2000-02-29", "2000-02-28")))
    first = pd.Timestamp("2000-02-29")
    for built in (unknown, known):
        assert np.isnan(built["targets"]["tilt"].loc[first, "A.US#E1"])
        assert built["targets"]["cw"].loc[first].dropna().tolist() == pytest.approx([0.5, 1.0 / 3.0, 1.0 / 6.0],
                                                                                  abs=1e-15)
    # Known at r - 1: D has c = 0 and stays at b; B and C hit the cap.
    assert known["targets"]["tilt"].loc[first].dropna().tolist() == pytest.approx([0.49, 1.0 / 3.0 + 0.01,
                                                                                   1.0 / 6.0], abs=1e-15)
    # Unknown at r - 1: D keeps its r - 1 rank below C, so it is not pinned and tilts down.
    w = unknown["targets"]["tilt"].loc[first].dropna()
    assert w["D.US#E1"] < 1.0 / 6.0 and w["B.US#E1"] < 0.5 and w["C.US#E1"] > 1.0 / 3.0
    assert math.fsum(w) == pytest.approx(1.0, abs=1e-15) and (w >= 0.0).all()
    assert (w - unknown["targets"]["cw"].loc[first].dropna()).abs().max() <= tilt.STOCK_CAP + tilt.CAP_TOLERANCE
    rows = {name: built["rebalances"].loc[first] for name, built in (("unknown", unknown), ("known", known))}
    assert (rows["unknown"]["unknown_event_excluded"], rows["unknown"]["settled_excluded"]) == (1, 0)
    assert (rows["known"]["unknown_event_excluded"], rows["known"]["settled_excluded"]) == (0, 1)
    assert rows["unknown"]["unknown_event_cw_share"] == pytest.approx(0.4, abs=1e-15)
    assert rows["known"]["unknown_event_cw_share"] == 0.0
    assert (rows["unknown"]["members"], rows["known"]["members"]) == (4, 3)


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
    # known at r itself leaves the traded set at r under the B2 rule. The pair of that case (B3): the same
    # event known at r - 1 removes the member at r. Neither changes an earlier target.
    inputs = replace(fixture(), disappearances=_event(ASSETS[2], effective, known))
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


# B2: an event effective and first known at a rebalance row -----------------------------------

B2_ASSET = ASSETS[2]            # last close 2001-01-30; settles at the rebalance row 2001-01-31, first known there


def _b2_inputs(cause: str = "failure", supplied: float = np.nan, known: pd.Timestamp = PERTURB_AT) -> tilt.TiltInputs:
    inputs = fixture(stop=True, stop_asset=B2_ASSET, stop_date=PERTURB_AT)
    table = pd.DataFrame([{"permanent_id": B2_ASSET, "effective_date": PERTURB_AT, "known_at": known,
                           "cause": cause, "delisting_return": supplied}], columns=FIELDS)
    return replace(inputs, disappearances=table)


def _tilt_calls(monkeypatch: pytest.MonkeyPatch, inputs: tilt.TiltInputs) -> dict:
    """Run build_targets and keep the (b, c, window, pinned) arguments of each tilt step by rebalance date."""
    calls = []
    original = tilt.tilt_weights

    def spy(b, c, window, pinned):
        calls.append((b, c, window, pinned))
        return original(b, c, window, pinned)

    monkeypatch.setattr(tilt, "tilt_weights", spy)
    built = tilt.build_targets(inputs)
    monkeypatch.setattr(tilt, "tilt_weights", original)
    return {"built": built, **dict(zip(built["targets"]["cw"].index, calls))}


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
def test_b2_unknown_event_at_r_settles_identically_in_both_books(cause: str, supplied: float, run: str,
                                                                 expected: float) -> None:
    inputs = _b2_inputs(cause, supplied)
    built = tilt.build_targets(inputs)
    assert built["rebalances"].loc[PERTURB_AT, "unknown_event_excluded"] == 1
    events = tilt.terminal_events(built["disappearances"], CAL, run)
    costs = tilt.dated_cost_frame(CAL)
    logs = {}
    for book in tilt.BOOKS:
        target = built["targets"][book]
        assert np.isnan(target.loc[PERTURB_AT, B2_ASSET])
        assert target.loc[pd.Timestamp("2000-12-29"), B2_ASSET] > 0.0
        result = tilt.run_book(inputs, target, events, costs)
        (record,) = [r for r in result.terminal_event_log if r["permanent_id"] == B2_ASSET]
        assert record["incoming_weight"] > 0.0
        assert record["terminal_return"] == expected
        assert result.holdings.loc[PERTURB_AT:, B2_ASSET].eq(0.0).all()
        logs[book] = record
    assert logs["cw"]["effective_date"] == logs["tilt"]["effective_date"]
    assert pd.Timestamp(logs["cw"]["effective_date"]) == PERTURB_AT
    assert built["targets"]["cw"].loc[PERTURB_AT].dropna().index.equals(
        built["targets"]["tilt"].loc[PERTURB_AT].dropna().index)


def test_b2_keeps_every_score_rank_and_covariance_at_r_minus_1(monkeypatch: pytest.MonkeyPatch) -> None:
    # The other members' c, pinned flags, and covariance window at r equal those of a run without the event.
    base = _tilt_calls(monkeypatch, fixture())
    event = _tilt_calls(monkeypatch, _b2_inputs())
    b0, c0, window0, pinned0 = base[PERTURB_AT]
    b1, c1, window1, pinned1 = event[PERTURB_AT]
    traded = b0.index.drop(B2_ASSET)
    assert b1.index.equals(traded)
    assert_series_equal(c1, c0[traded], check_exact=True)
    assert_series_equal(pinned1, pinned0[traded], check_exact=True)
    assert_frame_equal(window1, window0[traded], check_exact=True)
    me = fixture().market_equity.iloc[CAL.get_loc(PERTURB_AT) - 1][traded]
    assert_series_equal(event["built"]["targets"]["cw"].loc[PERTURB_AT].dropna(), me / math.fsum(me),
                        check_names=False, check_exact=True)
    for book in tilt.BOOKS:
        assert_frame_equal(event["built"]["targets"][book].loc[:"2000-12-29"],
                           base["built"]["targets"][book].loc[:"2000-12-29"], check_exact=True)
    # Contrast: the same event known at r - 1 leaves the rank pool, so the other members' c change.
    known = _tilt_calls(monkeypatch, _b2_inputs(known=CAL[CAL.get_loc(PERTURB_AT) - 1]))
    b2, c2, _, _ = known[PERTURB_AT]
    assert b2.index.equals(traded)
    assert_series_equal(known["built"]["targets"]["cw"].loc[PERTURB_AT],
                        event["built"]["targets"]["cw"].loc[PERTURB_AT], check_exact=True)
    assert (c2 != c1).any()
    assert not known["built"]["targets"]["tilt"].loc[PERTURB_AT].equals(
        event["built"]["targets"]["tilt"].loc[PERTURB_AT])


def test_b2_rebalance_meets_the_cap_the_budget_and_the_te_limit() -> None:
    inputs = _b2_inputs()
    built = tilt.build_targets(inputs)
    w = built["targets"]["tilt"].loc[PERTURB_AT].dropna()
    b = built["targets"]["cw"].loc[PERTURB_AT].dropna()
    assert w.index.equals(b.index) and B2_ASSET not in w.index
    assert (w >= 0.0).all()
    assert math.fsum(w) == pytest.approx(1.0, abs=1e-12) and math.fsum(b) == pytest.approx(1.0, abs=1e-12)
    assert (w - b).abs().max() <= tilt.STOCK_CAP + tilt.CAP_TOLERANCE
    t = CAL.get_loc(PERTURB_AT) - 1
    window = inputs.prices.pct_change(fill_method=None).iloc[t - 251:t + 1][w.index]
    full = window.notna().all()
    assert ((w - b)[~full] == 0.0).all()
    cov = np.cov(window.loc[:, full].to_numpy(), rowvar=False, ddof=1)
    active = (w - b)[full].to_numpy()
    te = math.sqrt(252.0 * active @ cov @ active)
    assert te <= tilt.TE_TARGET * (1.0 + 1e-9)
    assert te == pytest.approx(built["rebalances"].loc[PERTURB_AT, "ex_ante_te"], rel=1e-9, abs=1e-15)


@pytest.mark.parametrize("field", ["score", "market_equity", "returns", "eligibility", "event_return", "cause"])
def test_b2_inputs_after_r_minus_1_change_no_weight_at_r(field: str) -> None:
    before = tilt.build_targets(_b2_inputs())
    if field == "event_return":
        after = tilt.build_targets(_b2_inputs(supplied=-0.9))
    elif field == "cause":
        after = tilt.build_targets(_b2_inputs(cause="cash_merger"))
    else:
        after = tilt.build_targets(_perturbed(_b2_inputs(), field, CAL.get_loc(PERTURB_AT)))
    last = END if field in ("event_return", "cause") else PERTURB_AT
    for book in tilt.BOOKS:
        assert_frame_equal(after["targets"][book].loc[:last], before["targets"][book].loc[:last], check_exact=True)
    assert_frame_equal(after["rebalances"].loc[:last], before["rebalances"].loc[:last], check_exact=True)


def test_b2_reports_count_and_cap_weight_share() -> None:
    built = tilt.build_targets(_b2_inputs())
    table = built["rebalances"]
    assert table["unknown_event_excluded"].tolist() == [int(d == PERTURB_AT) for d in table.index]
    assert (table["unknown_event_cw_share"].drop(PERTURB_AT) == 0.0).all()
    t = CAL.get_loc(PERTURB_AT) - 1
    me = fixture().market_equity.iloc[t]
    members = me.index[fixture().eligible.iloc[t] & me.notna()]
    share = me[B2_ASSET] / math.fsum(me[members])
    assert table.loc[PERTURB_AT, "unknown_event_cw_share"] == pytest.approx(share, rel=1e-15)
    assert table.loc[PERTURB_AT, "members"] == len(members)
    assert built["counts"]["unknown_event_excluded"] == 1
    assert built["counts"]["settled_excluded"] == tilt.build_targets(fixture())["counts"]["settled_excluded"]


def test_b2_rebalance_with_every_target_member_excluded_refuses() -> None:
    inputs = _four_stock_inputs()
    alone = inputs.eligible.copy()
    alone.loc[:, ["B.US#E1", "C.US#E1", "D.US#E1"]] = False
    with pytest.raises(RunnerStop, match="traded_set_empty"):
        tilt.build_targets(replace(inputs, eligible=alone,
                                   disappearances=_event("A.US#E1", "2000-02-29", "2000-02-29")))


# Low-risk book (card m55-lowrisk, owner decision O-20) -----------------------------------------

LOW_G = 0.5                     # the 12-name fixture holds one member near 38 percent; the cap loop converges here


@pytest.fixture(scope="module")
def low_built() -> dict:
    return tilt.build_targets(fixture(), g=LOW_G)


@pytest.fixture(scope="module")
def low_run() -> dict:
    return tilt.run_index_tilt(fixture(stop=True), g=LOW_G)


def _window(vols: list[float], seed: int = 1, rows: int = 252) -> np.ndarray:
    return np.random.default_rng(seed).standard_normal((rows, len(vols))) * np.array(vols)


def _lowrisk(b: list[float], returns: np.ndarray, g: float) -> tuple[pd.Series, pd.Series, dict]:
    names = [chr(ord("A") + k) for k in range(len(b))]
    window = pd.DataFrame(returns, columns=names)
    vol = tilt.member_vols(window, pd.Series(True, index=names))
    bs = pd.Series(b, index=names)
    w, info = tilt.lowrisk_weights(bs, vol, window, g)
    return bs, w, info


def _shifted_prices(prices: pd.DataFrame, shift: np.ndarray) -> pd.DataFrame:
    """Prices whose daily simple return is the old one plus a per-stock constant; missing cells stay missing."""
    ratio = (prices / prices.shift(1)).add(shift, axis=1).fillna(1.0)
    first = prices.bfill().iloc[0]
    return (ratio.cumprod() * first).where(prices.notna())


def test_lowrisk_constants() -> None:
    assert (tilt.LOWRISK_CAP, tilt.LOWRISK_TE, tilt.LOWRISK_TARGET_RATIO) == (0.02, 0.05, 0.87)
    assert tilt.LOWRISK_GRID == (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0)
    assert tilt.BOOKS == ("cw", "tilt")


@pytest.mark.parametrize("field", ["score", "market_equity", "returns", "eligibility"])
def test_lowrisk_inputs_on_or_after_row_r_change_no_weight_at_row_r(low_built: dict, field: str) -> None:
    r = CAL.get_loc(PERTURB_AT)
    after = tilt.build_targets(_perturbed(fixture(), field, r), g=LOW_G)
    assert_frame_equal(after["targets"]["lowrisk"].loc[:PERTURB_AT], low_built["targets"]["lowrisk"].loc[:PERTURB_AT],
                       check_exact=True)
    assert_frame_equal(after["rebalances"].loc[:PERTURB_AT], low_built["rebalances"].loc[:PERTURB_AT],
                       check_exact=True)


@pytest.mark.parametrize("field", ["market_equity", "returns"])
def test_lowrisk_inputs_at_row_r_minus_1_do_change_the_weight_at_row_r(low_built: dict, field: str) -> None:
    r = CAL.get_loc(PERTURB_AT)
    after = tilt.build_targets(_perturbed(fixture(), field, r - 1), g=LOW_G)
    assert not after["targets"]["lowrisk"].loc[PERTURB_AT].equals(low_built["targets"]["lowrisk"].loc[PERTURB_AT])
    if field == "returns":
        assert (after["rebalances"].loc[PERTURB_AT, "lowrisk_vol_median"]
                != low_built["rebalances"].loc[PERTURB_AT, "lowrisk_vol_median"])
    assert_frame_equal(after["targets"]["lowrisk"].loc[:"2000-12-29"], low_built["targets"]["lowrisk"].loc[:"2000-12-29"],
                       check_exact=True)


def test_lowrisk_ignores_a_constant_shift_in_daily_returns(low_built: dict) -> None:
    # Volatility and TE ignore the mean: a per-stock constant added to every daily return moves no target.
    inputs = fixture()
    shifted = replace(inputs, prices=_shifted_prices(inputs.prices, np.linspace(-0.004, 0.006, len(ASSETS))))
    returns = tilt.simple_returns(shifted.prices) - tilt.simple_returns(inputs.prices)
    assert returns.std().max() < 1e-12 and returns.mean().abs().min() > 1e-4
    after = tilt.build_targets(shifted, g=LOW_G)
    gap = (after["targets"]["lowrisk"] - low_built["targets"]["lowrisk"]).abs().max().max()
    assert gap <= 1e-12
    assert_frame_equal(after["targets"]["lowrisk"].isna(), low_built["targets"]["lowrisk"].isna())
    grid = (0.1, 0.2, 0.3, 0.4, 0.5)
    base = tilt.calibrate_lowrisk(inputs, grid, 0.995, START, END)
    moved = tilt.calibrate_lowrisk(shifted, grid, 0.995, START, END)
    assert base["chosen_g"] == moved["chosen_g"] is not None
    assert np.allclose(base["grid"]["median_vol_ratio"], moved["grid"]["median_vol_ratio"], rtol=0.0, atol=1e-12)


def test_lowrisk_cap_holds_and_a_large_low_volatility_member_reaches_it() -> None:
    b, w, info = _lowrisk([0.5, 0.1, 0.1, 0.1, 0.1, 0.1], _window([0.002, 0.004, 0.005, 0.006, 0.007, 0.008]), 2.0)
    assert info["te_scale"] == 1.0 and info["capped"] >= 1
    assert abs((w["A"] - b["A"]) - tilt.LOWRISK_CAP) <= 1e-12
    assert (w - b).abs().max() <= tilt.LOWRISK_CAP + 1e-12
    assert math.fsum(w) == pytest.approx(1.0, abs=1e-12) and (w >= 0.0).all()


def test_lowrisk_loop_refuses_when_it_does_not_converge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tilt, "RENORMALIZE_LOOPS", 1)
    with pytest.raises(RunnerStop, match="lowrisk_loop_not_converged"):
        _lowrisk([0.5, 0.1, 0.1, 0.1, 0.1, 0.1], _window([0.002, 0.004, 0.005, 0.006, 0.007, 0.008]), 2.0)


def test_lowrisk_loop_converges_on_a_large_concentrated_book() -> None:
    # 500 lognormal cap weights (top weight near 5 percent); volatility falls with size; g at the top of the grid.
    n = 500
    rng = np.random.default_rng(4)
    raw = np.exp(rng.normal(0.0, 1.25, n))
    size = pd.Series(raw).rank(pct=True).to_numpy()
    returns = np.outer(rng.standard_normal(252) * 0.009, rng.uniform(0.5, 1.5, n))
    returns += rng.standard_normal((252, n)) * 0.014 * (1.25 - 0.5 * size)
    b, w, info = _lowrisk(list(raw / raw.sum()), returns, tilt.LOWRISK_GRID[-1])
    assert info["loops"] < tilt.RENORMALIZE_LOOPS and info["capped"] > 0
    assert (w >= 0.0).all() and math.fsum(w) == pytest.approx(1.0, abs=1e-12)
    assert (w - b).abs().max() <= tilt.LOWRISK_CAP + tilt.CAP_TOLERANCE


def test_lowrisk_te_scaling() -> None:
    returns = _window([0.12, 0.16, 0.24, 0.32])
    b, w, info = _lowrisk([0.25, 0.25, 0.25, 0.25], returns, 6.0)
    assert info["te_scale"] < 1.0 and info["ex_ante_te_before_scale"] > tilt.LOWRISK_TE
    cov = np.cov(returns, rowvar=False, ddof=1)
    active = (w - b).to_numpy()
    te = math.sqrt(252.0 * active @ cov @ active)
    assert te == pytest.approx(tilt.LOWRISK_TE, rel=1e-9)
    assert info["ex_ante_te"] == pytest.approx(tilt.LOWRISK_TE, rel=1e-9)
    _, _, small = _lowrisk([0.25, 0.25, 0.25, 0.25], returns, 0.01)
    assert small["te_scale"] == 1.0 and small["ex_ante_te"] < tilt.LOWRISK_TE


def test_lowrisk_record_values() -> None:
    returns = _window([0.06, 0.08, 0.12, 0.16])
    b, w, info = _lowrisk([0.4, 0.3, 0.2, 0.1], returns, 1.0)
    vol_w = np.std(returns @ w.to_numpy(), ddof=1) * math.sqrt(252)
    vol_b = np.std(returns @ b.to_numpy(), ddof=1) * math.sqrt(252)
    assert info["ex_ante_vol"] == pytest.approx(vol_w, rel=1e-12)
    assert info["cw_ex_ante_vol"] == pytest.approx(vol_b, rel=1e-12)
    assert info["vol_ratio"] == pytest.approx(vol_w / vol_b, rel=1e-12)
    assert info["g"] == 1.0 and info["pinned"] == 0 and info["pinned_cw_share"] == 0.0
    assert info["ratio_status"] == "defined_full" and info["ratio_rows"] == 252
    assert info["vol_median"] == pytest.approx(np.median(returns.std(axis=0, ddof=1)), rel=1e-15)


def test_lowrisk_budget_and_pinned_members(low_built: dict) -> None:
    table = low_built["rebalances"]
    for date in low_built["targets"]["lowrisk"].index:
        w = low_built["targets"]["lowrisk"].loc[date].dropna()
        b = low_built["targets"]["cw"].loc[date].dropna()
        assert w.index.equals(b.index)
        assert np.isfinite(w).all() and (w >= 0.0).all()
        assert abs(math.fsum(w) - 1.0) <= 1e-12
        assert (w - b).abs().max() <= tilt.LOWRISK_CAP + tilt.CAP_TOLERANCE
        assert table.loc[date, "lowrisk_ex_ante_te"] <= tilt.LOWRISK_TE * (1.0 + tilt.TE_TOLERANCE)
    first = low_built["targets"]["lowrisk"].index[0]
    assert table.loc[first, "lowrisk_pinned"] == 1                      # LATE_ASSET has no full window yet
    assert low_built["targets"]["lowrisk"].loc[first, LATE_ASSET] == low_built["targets"]["cw"].loc[first, LATE_ASSET]
    assert table.loc[first, "lowrisk_pinned_cw_share"] == low_built["targets"]["cw"].loc[first, LATE_ASSET]
    assert table["lowrisk_pinned"].iloc[-1] == 0
    assert low_built["counts"]["lowrisk_pinned"] == int(table["lowrisk_pinned"].sum())
    assert (table["lowrisk_g"] == LOW_G).all()
    assert (table["lowrisk_te_scale"] < 1.0).any() and (table["lowrisk_capped"] > 0).any()


def test_lowrisk_g_zero_gives_cap_weight_exactly() -> None:
    built = tilt.build_targets(fixture(), g=0.0)
    assert_frame_equal(built["targets"]["lowrisk"], built["targets"]["cw"], check_exact=True)
    table = built["rebalances"]
    short = table["lowrisk_ratio_status"] == "ratio_window_short"
    assert short.sum() == 1 and (table.loc[short, "lowrisk_ratio_rows"] < tilt.LOWRISK_RATIO_MIN_ROWS).all()
    assert table.loc[short, "lowrisk_vol_ratio"].isna().all() and (table.loc[~short, "lowrisk_vol_ratio"] == 1.0).all()


def test_lowrisk_equal_volatilities_give_cap_weight_exactly() -> None:
    x = _window([0.01])[:, 0]
    b, w, info = _lowrisk([0.4, 0.3, 0.2, 0.1], np.column_stack([x, -x, x, -x]), 3.0)
    assert (w == b).all()
    assert info["te_scale"] == 1.0 and info["capped"] == 0


def test_lowrisk_lower_volatility_gets_the_higher_weight() -> None:
    b, w, info = _lowrisk([0.3, 0.3, 0.2, 0.2], _window([0.010, 0.012, 0.011, 0.0105]), 0.3)
    assert info["capped"] == 0 and info["te_scale"] == 1.0
    assert w["A"] > b["A"] > w["B"]


def test_lowrisk_zero_volatility_refuses() -> None:
    returns = _window([0.01, 0.01, 0.01])
    returns[:, 1] = 0.0
    with pytest.raises(RunnerStop, match="lowrisk_vol_invalid"):
        _lowrisk([0.5, 0.3, 0.2], returns, 1.0)


@pytest.mark.parametrize("g", [-0.5, np.nan, np.inf])
def test_lowrisk_invalid_g_refuses(g: float) -> None:
    with pytest.raises(RunnerStop, match="lowrisk_g_invalid"):
        tilt.build_targets(fixture(), g=g)


def test_lowrisk_leaves_the_other_books_unchanged(built: dict, low_built: dict) -> None:
    for book in tilt.BOOKS:
        assert_frame_equal(low_built["targets"][book], built["targets"][book], check_exact=True)
    assert_frame_equal(low_built["rebalances"][built["rebalances"].columns], built["rebalances"], check_exact=True)
    extra = [c for c in low_built["rebalances"].columns if c not in built["rebalances"].columns]
    assert extra and all(c.startswith("lowrisk_") for c in extra)
    assert set(built["targets"]) == set(tilt.BOOKS) and not any(c.startswith("lowrisk") for c in built["counts"])


def test_lowrisk_full_run_reports_the_book_like_the_others(full_run: dict, low_run: dict) -> None:
    assert set(low_run["targets"]) == {"cw", "tilt", "lowrisk"}
    assert set(low_run["fragile_lowrisk_active_sign"]) == set(tilt.COST_SCALES)
    assert "fragile_lowrisk_active_sign" not in full_run and "lowrisk_active" not in full_run["runs"][("primary",
                                                                                                         "primary")]
    for key, run in low_run["runs"].items():
        for book in tilt.BOOKS:
            assert_series_equal(run[book]["daily_net"], full_run["runs"][key][book]["daily_net"], check_exact=True)
        out = run["lowrisk"]
        assert out["held_events"]["count"] == 1 and out["held_events"]["weight_sum"] > 0.0
        assert out["monthly_net"].index.equals(pd.period_range("2000-08", "2001-08", freq="M"))
        assert np.prod(1.0 + out["monthly_net"]) == pytest.approx(np.prod(1.0 + out["daily_net"]), rel=1e-12)
        assert_series_equal(run["lowrisk_active"]["daily"], out["daily_net"] - run["cw"]["daily_net"])
        assert run["lowrisk_active"]["realized_te_daily"] > 0.0
    primary, stressed = low_run["runs"][("primary", "primary")], low_run["runs"][("sensitivity_2x", "primary")]
    assert stressed["lowrisk"]["annual_cost_drag"] == pytest.approx(2.0 * primary["lowrisk"]["annual_cost_drag"],
                                                                    rel=0.05)


@pytest.mark.parametrize(
    ("cause", "supplied", "run", "expected"),
    [("failure", np.nan, "primary", -1.0), ("cash_merger", np.nan, "primary", 0.0), ("failure", -0.3, "last_close", 0.0)],
)
@pytest.mark.parametrize("b2", [False, True])
def test_lowrisk_disappearance_settles_as_in_the_other_books(b2: bool, cause: str, supplied: float, run: str,
                                                             expected: float) -> None:
    if b2:
        inputs, asset, date = _b2_inputs(cause, supplied), B2_ASSET, PERTURB_AT
    else:
        inputs, asset, date = fixture(stop=True), STOP_ASSET, STOP_DATE
        inputs = replace(inputs, disappearances=pd.DataFrame(
            [{"permanent_id": asset, "effective_date": date, "known_at": date, "cause": cause,
              "delisting_return": supplied}], columns=FIELDS))
    built = tilt.build_targets(inputs, g=LOW_G)
    events = tilt.terminal_events(built["disappearances"], CAL, run)
    records = {}
    for book in ("cw", "lowrisk"):
        result = tilt.run_book(inputs, built["targets"][book], events, tilt.dated_cost_frame(CAL))
        (records[book],) = [r for r in result.terminal_event_log if r["permanent_id"] == asset]
        assert records[book]["incoming_weight"] > 0.0 and records[book]["terminal_return"] == expected
        assert result.holdings.loc[date:, asset].eq(0.0).all()
    assert records["cw"]["effective_date"] == records["lowrisk"]["effective_date"]
    if b2:
        assert np.isnan(built["targets"]["lowrisk"].loc[PERTURB_AT, B2_ASSET])
        assert built["targets"]["lowrisk"].loc[PERTURB_AT].dropna().index.equals(
            built["targets"]["cw"].loc[PERTURB_AT].dropna().index)


def test_lowrisk_b2_keeps_the_excluded_name_in_the_volatility_median(low_built: dict) -> None:
    unknown = tilt.build_targets(_b2_inputs(), g=LOW_G)["rebalances"].loc[PERTURB_AT]
    known = tilt.build_targets(_b2_inputs(known=CAL[CAL.get_loc(PERTURB_AT) - 1]), g=LOW_G)["rebalances"].loc[PERTURB_AT]
    base = low_built["rebalances"].loc[PERTURB_AT]
    assert unknown["unknown_event_excluded"] == 1
    assert unknown["lowrisk_vol_median"] == base["lowrisk_vol_median"]
    assert known["lowrisk_vol_median"] != base["lowrisk_vol_median"]


# Low-risk calibration (design note section 4) ---------------------------------------------------

CAL_GRID = (0.1, 0.2, 0.3, 0.4, 0.5)
CAL_START = pd.Timestamp("2000-08-31")      # from here LATE_ASSET has at least 126 complete rows: no undefined ratio


@pytest.fixture(scope="module")
def calibration() -> dict:
    return tilt.calibrate_lowrisk(fixture(), CAL_GRID, 0.99, CAL_START, END)


def test_calibration_records_every_grid_value_and_matches_the_book(calibration: dict) -> None:
    grid, table = calibration["grid"], calibration["rebalances"]
    assert grid["g"].tolist() == list(CAL_GRID)
    dates = tilt.rebalance_dates(CAL, CAL_START, END)
    assert (grid["rebalances"] == len(dates)).all()
    for g in (CAL_GRID[0], CAL_GRID[-1]):
        book = tilt.build_targets(replace(fixture(), start=CAL_START), g=g)["rebalances"]
        part = table[table["g"] == g].set_index("date")
        assert part.index.equals(book.index)
        assert_series_equal(part["vol_ratio"], book["lowrisk_vol_ratio"], check_names=False, check_exact=True)
        row = grid[grid["g"] == g].iloc[0]
        assert row["median_vol_ratio"] == np.median(book["lowrisk_vol_ratio"])
        assert row["share_cap_binds"] == (book["lowrisk_capped"] > 0).mean()
        assert row["share_te_scaled"] == (book["lowrisk_te_scale"] < 1.0).mean()
        assert row["share_pinned"] == (book["lowrisk_pinned"] > 0).mean()


def test_calibration_picks_the_smallest_g_at_or_below_the_target(calibration: dict) -> None:
    medians = calibration["grid"].set_index("g")["median_vol_ratio"]
    for target in sorted(set(medians)):
        result = tilt.calibrate_lowrisk(fixture(), CAL_GRID, target, CAL_START, END)
        expected = min(g for g in CAL_GRID if medians[g] <= target)
        assert result["chosen_g"] == expected and result["decision"] == "chosen"
    assert calibration["chosen_g"] == min(g for g in CAL_GRID if medians[g] <= 0.99)
    none = tilt.calibrate_lowrisk(fixture(), CAL_GRID, float(medians.min()) * 0.999, CAL_START, END)
    assert none["chosen_g"] is None and none["decision"] == "no_g_reaches_target"
    assert none["grid"]["g"].tolist() == list(CAL_GRID)


def test_calibration_runs_no_book(monkeypatch: pytest.MonkeyPatch, calibration: dict) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("the calibration must not run a book")

    monkeypatch.setattr(tilt, "run_book", forbidden)
    monkeypatch.setattr(tilt, "run_long_only_backtest", forbidden)
    result = tilt.calibrate_lowrisk(fixture(), CAL_GRID, 0.99, CAL_START, END)
    assert_frame_equal(result["grid"], calibration["grid"], check_exact=True)


@pytest.mark.parametrize("grid", [(), (0.5, 0.5), (1.0, 0.5), (-0.5, 0.5), (0.5, np.nan)])
def test_calibration_grid_is_validated(grid: tuple) -> None:
    with pytest.raises(RunnerStop, match="calibration_grid_invalid|lowrisk_g_invalid"):
        tilt.calibrate_lowrisk(fixture(), grid, 0.87, START, END)


def test_calibration_future_rows_change_nothing(calibration: dict) -> None:
    inputs = _perturbed(fixture(), "returns", CAL.get_loc(END))
    result = tilt.calibrate_lowrisk(inputs, CAL_GRID, 0.99, CAL_START, END)
    assert_frame_equal(result["rebalances"], calibration["rebalances"], check_exact=True)


# Repair round 1 (card m55-lowrisk-repair-r1) -----------------------------------------------------

def _dominant_pinned_inputs(mask: str | None) -> tilt.TiltInputs:
    """GPT-R1-01: three stocks, ME weights (0.01, 0.01, 0.98); the large one has no full window when masked."""
    calendar = pd.bdate_range("1999-01-01", "2000-04-03", name="date")
    names = ["A.US#E1", "B.US#E1", "C.US#E1"]
    returns = np.random.default_rng(217).normal(size=(len(calendar), 3)) * np.array([0.002, 0.020, 0.10])
    prices = pd.DataFrame(100.0 * np.cumprod(1.0 + returns, axis=0), index=calendar, columns=names)
    if mask == "short_history":
        prices.iloc[:240, 2] = np.nan
    elif mask == "window_gap":
        prices.iloc[200:203, 2] = np.nan
    eligible = pd.DataFrame(True, index=calendar, columns=names)
    me = pd.DataFrame(np.tile([1.0, 1.0, 98.0], (len(calendar), 1)), index=calendar, columns=names)
    zero = pd.DataFrame(0.0, index=calendar, columns=names)
    return tilt.TiltInputs(prices=prices, signals={s: zero.copy() for s in FAMILY_A_IDS}, eligible=eligible,
                           market_equity=me, me_reason=pd.DataFrame(None, index=calendar, columns=names, dtype=object),
                           intervals=intervals(names, calendar), disappearances=pd.DataFrame(columns=FIELDS),
                           start=pd.Timestamp("1999-12-31"), end=pd.Timestamp("2000-03-31"))


def _oracle_ratio(window: pd.DataFrame, full_returns: pd.DataFrame, b: np.ndarray, w: np.ndarray) -> tuple:
    """The whole-book ratio from the unmasked history on the rows where ``window`` is complete, and those rows."""
    ok = window.notna().all(axis=1).to_numpy()
    x = full_returns.loc[window.index, window.columns].to_numpy()[ok]
    return np.std(x @ w, ddof=1) / np.std(x @ b, ddof=1), int(ok.sum())


@pytest.mark.parametrize("mask", ["short_history", "window_gap"])
def test_calibration_with_a_dominant_pinned_member_measures_the_whole_book(mask: str) -> None:
    # GPT-R1-01: the ratio covers the 98 percent member on its complete-case rows, or it is undefined.
    inputs = _dominant_pinned_inputs(mask)
    result = tilt.calibrate_lowrisk(inputs, tilt.LOWRISK_GRID, tilt.LOWRISK_TARGET_RATIO, inputs.start, inputs.end)
    table, grid = result["rebalances"], result["grid"]
    assert ((table["pinned_cw_share"] - 0.98).abs() <= 1e-15).all()
    assert grid["g"].tolist() == list(tilt.LOWRISK_GRID) and (grid["status"] == "ok").all()
    assert result["chosen_g"] is None
    built = tilt.build_targets(inputs, g=0.5)
    assert (built["targets"]["lowrisk"]["C.US#E1"] == built["targets"]["cw"]["C.US#E1"]).all()
    if mask == "short_history":
        assert result["decision"] == "ratio_coverage_low" and result["undefined_share"] == 1.0
        assert (table["ratio_status"] == "ratio_window_short").all() and table["vol_ratio"].isna().all()
        assert (table["ratio_rows"] < tilt.LOWRISK_RATIO_MIN_ROWS).all() and (table["ratio_rows_gap"] == 0).all()
        assert (grid["undefined"] == 3).all() and (grid["defined"] == 0).all() and grid["median_vol_ratio"].isna().all()
        assert built["rebalances"]["lowrisk_vol_ratio"].isna().all()
        return
    # Four returns touch the three missing prices; every other row of the window stays.
    assert (table["ratio_status"] == "defined_partial").all() and (table["ratio_rows"] == 248).all()
    assert (table["ratio_rows_gap"] == 4).all() and (table["ratio_limiting_members"] == 1).all()
    assert result["decision"] == "no_g_reaches_target" and (grid["bracket"] == "fails").all()
    full_returns = tilt.simple_returns(_dominant_pinned_inputs(None).prices)
    _, returns, _ = tilt.prepare(inputs)
    for date in built["targets"]["lowrisk"].index:
        t = inputs.prices.index.get_loc(date) - 1
        window = returns.iloc[t - 251:t + 1]
        w, b = built["targets"]["lowrisk"].loc[date].to_numpy(), built["targets"]["cw"].loc[date].to_numpy()
        oracle, rows = _oracle_ratio(window, full_returns, b, w)
        assert rows == 248 and built["rebalances"].loc[date, "lowrisk_vol_ratio"] == pytest.approx(oracle, rel=1e-12)


def test_calibration_complete_history_control_gives_the_whole_book_ratio() -> None:
    inputs = _dominant_pinned_inputs(None)
    # One free member holds 98 percent, so the cap loop converges only for a small g here (g = 0.1 and 0.2).
    result = tilt.calibrate_lowrisk(inputs, (0.1, 0.2), 0.99, inputs.start, inputs.end)
    assert (result["rebalances"]["ratio_status"] == "defined_full").all() and result["undefined_share"] == 0.0
    assert (result["rebalances"]["ratio_rows"] == 252).all() and (result["rebalances"]["pinned"] == 0).all()
    assert result["decision"] == "chosen" and result["chosen_g"] == 0.2
    assert result["window_decision"] == "chosen" and not result["window_sensitive"]
    built = tilt.build_targets(inputs, g=0.2)
    returns = inputs.prices.pct_change(fill_method=None)
    part = result["rebalances"][result["rebalances"]["g"] == 0.2].set_index("date")
    for date in built["targets"]["lowrisk"].index:
        t = inputs.prices.index.get_loc(date) - 1
        window = returns.iloc[t - 251:t + 1].to_numpy()
        w, b = built["targets"]["lowrisk"].loc[date].to_numpy(), built["targets"]["cw"].loc[date].to_numpy()
        whole = np.std(window @ w, ddof=1) / np.std(window @ b, ddof=1)
        assert part.loc[date, "vol_ratio"] == pytest.approx(whole, rel=1e-12)


def test_calibration_coverage_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    # From START, LATE_ASSET has fewer than 126 complete rows at the first of the fourteen rebalances only.
    monkeypatch.setattr(tilt, "LOWRISK_UNDEFINED_MAX", 1 / 14)
    at = tilt.calibrate_lowrisk(fixture(), CAL_GRID, 0.99, START, END)
    assert at["undefined_share"] == 1 / 14 and at["decision"] == "ratio_coverage_ambiguous"
    table = at["rebalances"]
    for row in at["grid"].itertuples():
        defined = table[(table["g"] == row.g) & table["ratio_status"].isin(["defined_full", "defined_partial"])]
        assert (row.defined, row.undefined) == (13, 1)
        assert row.median_vol_ratio == np.median(defined["vol_ratio"])
    monkeypatch.setattr(tilt, "LOWRISK_UNDEFINED_MAX", 1 / 14 - 1e-12)
    above = tilt.calibrate_lowrisk(fixture(), CAL_GRID, 0.99, START, END)
    assert above["decision"] == "ratio_coverage_low" and above["chosen_g"] is None
    assert above["grid"]["g"].tolist() == list(CAL_GRID)


def _refuse_at(monkeypatch: pytest.MonkeyPatch, refused_g: float) -> None:
    """Make the low-risk step refuse at every rebalance for one grid value only."""
    original = tilt.lowrisk_weights

    def spy(b, vol, window, g):
        if g == refused_g:
            raise RunnerStop("lowrisk_loop_not_converged", "test")
        return original(b, vol, window, g)

    monkeypatch.setattr(tilt, "lowrisk_weights", spy)


def test_calibration_records_a_refusal_above_the_chosen_g(monkeypatch: pytest.MonkeyPatch, calibration: dict) -> None:
    # Opus ADV-01: a grid value above the choice that refuses is recorded and does not stop the calibration.
    chosen = calibration["chosen_g"]
    assert chosen is not None and chosen < CAL_GRID[-1]
    _refuse_at(monkeypatch, CAL_GRID[-1])
    result = tilt.calibrate_lowrisk(fixture(), CAL_GRID, 0.99, CAL_START, END)
    assert result["decision"] == "chosen" and result["chosen_g"] == chosen
    grid = result["grid"].set_index("g")
    assert grid["status"].tolist() == ["ok"] * (len(CAL_GRID) - 1) + ["refused"]
    assert grid.loc[CAL_GRID[-1], "refusal"].startswith("lowrisk_loop_not_converged")
    assert grid.loc[CAL_GRID[-1], "refusal_date"] == tilt.rebalance_dates(CAL, CAL_START, END)[0]
    assert np.isnan(grid.loc[CAL_GRID[-1], "median_vol_ratio"])
    assert not (result["rebalances"]["g"] == CAL_GRID[-1]).any()
    ok = grid.drop(CAL_GRID[-1])
    assert_frame_equal(ok[["median_vol_ratio"]], calibration["grid"].set_index("g").drop(CAL_GRID[-1])[
        ["median_vol_ratio"]], check_exact=True)


@pytest.mark.parametrize("where", ["first", "chosen"])
def test_calibration_stops_on_a_refusal_at_or_below_the_choice(monkeypatch: pytest.MonkeyPatch, calibration: dict,
                                                              where: str) -> None:
    _refuse_at(monkeypatch, CAL_GRID[0] if where == "first" else calibration["chosen_g"])
    with pytest.raises(RunnerStop, match="lowrisk_loop_not_converged"):
        tilt.calibrate_lowrisk(fixture(), CAL_GRID, 0.99, CAL_START, END)


def test_calibration_stops_when_the_cap_loop_does_not_converge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tilt, "RENORMALIZE_LOOPS", 1)
    with pytest.raises(RunnerStop, match="lowrisk_loop_not_converged"):
        tilt.calibrate_lowrisk(fixture(), CAL_GRID, 0.99, START, END)


def test_lowrisk_uses_each_event_run_end_to_end(low_run: dict) -> None:
    # Opus ADV-02: the lowrisk book in each run case equals a direct run with that case's events and costs.
    inputs = fixture(stop=True)
    built = tilt.build_targets(inputs, g=LOW_G)
    for (case, event_run), run in low_run["runs"].items():
        events = tilt.terminal_events(built["disappearances"], CAL, event_run)
        direct = tilt.run_book(inputs, built["targets"]["lowrisk"], events,
                               tilt.dated_cost_frame(CAL, scale=tilt.COST_SCALES[case]))
        (record,) = [r for r in direct.terminal_event_log if r["permanent_id"] == STOP_ASSET]
        assert record["terminal_return"] == (-1.0 if event_run == "primary" else 0.0)
        summary = tilt.book_summary(direct, built["targets"]["lowrisk"])
        assert_series_equal(run["lowrisk"]["daily_net"], summary["daily_net"], check_exact=True)
    for case in tilt.COST_SCALES:
        primary = low_run["runs"][(case, "primary")]["lowrisk"]["monthly_net"]
        rerun = low_run["runs"][(case, "last_close")]["lowrisk"]["monthly_net"]
        assert primary.loc["2001-02"] < rerun.loc["2001-02"]


def test_lowrisk_very_large_g_refuses_with_a_typed_reason() -> None:
    # Opus ADV-04: the power overflows; it refuses before the cap loop.
    with pytest.raises(RunnerStop, match="lowrisk_multiplier_invalid"):
        _lowrisk([0.25, 0.25, 0.25, 0.25], _window([0.01, 0.02, 0.05, 0.10]), 1000.0)


def test_lowrisk_zero_book_volatility_refuses() -> None:
    # Two members that hedge each other exactly: sd(window @ b) = 0, so the ratio is not finite.
    x = _window([0.01])[:, 0]
    with pytest.raises(RunnerStop, match="lowrisk_vol_ratio_invalid"):
        _lowrisk([0.5, 0.5], np.column_stack([x, -x]), 1.0)


def test_signals_do_not_move_the_lowrisk_book(low_built: dict) -> None:
    # Opus ADV-06: new random values in every signal frame at every row.
    inputs = fixture()
    rng = np.random.default_rng(31)
    signals = {s: pd.DataFrame(rng.standard_normal(f.shape), index=f.index, columns=f.columns).where(f.notna())
               for s, f in inputs.signals.items()}
    after = tilt.build_targets(replace(inputs, signals=signals), g=LOW_G)
    assert not after["targets"]["tilt"].equals(low_built["targets"]["tilt"])
    assert_frame_equal(after["targets"]["lowrisk"], low_built["targets"]["lowrisk"], check_exact=True)
    columns = [c for c in low_built["rebalances"].columns if c.startswith("lowrisk_")]
    assert_frame_equal(after["rebalances"][columns], low_built["rebalances"][columns], check_exact=True)


@pytest.mark.parametrize("target", [0.0, -1.0, np.nan, np.inf])
def test_calibration_target_ratio_is_validated(target: float) -> None:
    with pytest.raises(RunnerStop, match="calibration_target_invalid"):
        tilt.calibrate_lowrisk(fixture(), CAL_GRID, target, START, END)


# Repair round 2: the whole-book ratio on complete-case rows (expert decision of 2026-10-05) ----------

GPT_NAMES = [f"N{k:03d}.US#E1" for k in range(101)]


def _gpt_inputs(mask: str | None, first: int = 240) -> tuple[tilt.TiltInputs, pd.DataFrame]:
    """GPT-R2-01: 101 stocks, ME weights 0.0098 x 100 and 0.02; the 0.02 member has the highest volatility.

    Returns the masked inputs and the unmasked daily returns (the audit oracle only).
    """
    calendar = pd.bdate_range("1999-01-01", "2000-04-03", name="date")
    scale = np.array([0.01] * 50 + [0.03] * 50 + [0.10])
    returns = np.random.default_rng(217).normal(size=(len(calendar), 101)) * scale
    full = pd.DataFrame(100.0 * np.cumprod(1.0 + returns, axis=0), index=calendar, columns=GPT_NAMES)
    prices = full.copy()
    if mask == "leading":
        prices.iloc[:first, -1] = np.nan
    elif mask == "gap":
        prices.iloc[200:203, -1] = np.nan
    eligible = prices.notna()
    me = pd.DataFrame(np.tile([0.0098] * 100 + [0.02], (len(calendar), 1)), index=calendar, columns=GPT_NAMES)
    zero = pd.DataFrame(0.0, index=calendar, columns=GPT_NAMES)
    inputs = tilt.TiltInputs(prices=prices, signals={s: zero.copy() for s in FAMILY_A_IDS}, eligible=eligible,
                             market_equity=me,
                             me_reason=pd.DataFrame(None, index=calendar, columns=GPT_NAMES, dtype=object),
                             intervals=intervals(GPT_NAMES, calendar), disappearances=pd.DataFrame(columns=FIELDS),
                             start=pd.Timestamp("1999-12-31"), end=pd.Timestamp("2000-03-31"))
    return inputs, tilt.simple_returns(full)


def _calibrate_with_calls(monkeypatch: pytest.MonkeyPatch, inputs: tilt.TiltInputs,
                          grid: tuple = tilt.LOWRISK_GRID) -> tuple[dict, list]:
    """Calibrate and keep the (window, b, w) of each low-risk step, in the order of the rebalance table rows."""
    calls = []
    original = tilt.lowrisk_weights

    def spy(b, vol, window, g):
        w, info = original(b, vol, window, g)
        calls.append((window, b.to_numpy(), w.to_numpy()))
        return w, info

    monkeypatch.setattr(tilt, "lowrisk_weights", spy)
    result = tilt.calibrate_lowrisk(inputs, grid, tilt.LOWRISK_TARGET_RATIO, inputs.start, inputs.end)
    monkeypatch.setattr(tilt, "lowrisk_weights", original)
    assert len(calls) == len(result["rebalances"])
    return result, calls


def _oracle_choice(table: pd.DataFrame, oracle: np.ndarray, target: float) -> float | None:
    """The bracket decision written out on its own: u undefined rows at +inf and -inf, the median, the first g."""
    for g in table["g"].unique():
        part = table["g"] == g
        defined = oracle[part.to_numpy() & ~np.isnan(oracle)]
        u = int(part.sum()) - len(defined)
        if u / int(part.sum()) > tilt.LOWRISK_UNDEFINED_MAX:
            return None
        hi = np.median(np.r_[defined, [np.inf] * u])
        lo = np.median(np.r_[defined, [-np.inf] * u])
        if hi <= target:
            return float(g)
        if lo <= target:
            return None
    return None


@pytest.mark.parametrize("mask", ["leading", "gap"])
def test_gpt_fixture_measures_the_whole_book(monkeypatch: pytest.MonkeyPatch, mask: str) -> None:
    # T1, GPT-R2-01: the 2 percent member is in the ratio; the choice is not g = 0.5 from the free sub-book.
    inputs, full_returns = _gpt_inputs(mask)
    result, calls = _calibrate_with_calls(monkeypatch, inputs)
    table = result["rebalances"]
    oracle, rows = [], []
    for window, b, w in calls:
        ratio, n = _oracle_ratio(window, full_returns, b, w)
        rows.append(n)
        oracle.append(ratio if n >= tilt.LOWRISK_RATIO_MIN_ROWS else np.nan)
    oracle = np.array(oracle)
    assert (table["ratio_rows"].to_numpy() == rows).all() and (table["pinned_cw_share"] == 0.02).all()
    assert (table["ratio_limiting_members"] == 1).all() and (table["ratio_limiting_cw_share"] == 0.02).all()
    if mask == "leading":
        assert (table["ratio_status"] == "ratio_window_short").all() and table["vol_ratio"].isna().all()
        assert (table["ratio_rows_leading"] == 252 - table["ratio_rows"]).all() and (table["ratio_rows_gap"] == 0).all()
        assert result["decision"] == "ratio_coverage_low" and result["chosen_g"] is None
    else:
        assert (table["ratio_status"] == "defined_partial").all() and (table["ratio_rows"] == 248).all()
        assert (table["ratio_rows_gap"] == 4).all() and (table["ratio_rows_leading"] == 0).all()
        assert np.allclose(table["vol_ratio"], oracle, rtol=1e-12, atol=0.0)
        assert result["decision"] == "chosen"
    assert result["chosen_g"] == _oracle_choice(table, oracle, tilt.LOWRISK_TARGET_RATIO)
    assert result["chosen_g"] != 0.5


def test_gpt_fixture_defined_leading_history(monkeypatch: pytest.MonkeyPatch) -> None:
    # T2: with the first 100 prices masked, every rebalance keeps at least 126 rows; the ratio is the whole book.
    inputs, full_returns = _gpt_inputs("leading", first=100)
    result, calls = _calibrate_with_calls(monkeypatch, inputs)
    table = result["rebalances"]
    assert (table["ratio_rows"] >= tilt.LOWRISK_RATIO_MIN_ROWS).all() and (table["ratio_rows"] < 252).all()
    assert (table["ratio_status"] == "defined_partial").all()
    oracle, free_only = [], []
    for window, b, w in calls:
        oracle.append(_oracle_ratio(window, full_returns, b, w)[0])
        free = window.notna().all().to_numpy()
        x = window.to_numpy()[:, free]
        free_only.append(np.std(x @ w[free], ddof=1) / np.std(x @ b[free], ddof=1))
    assert np.allclose(table["vol_ratio"], oracle, rtol=1e-12, atol=0.0)
    assert (np.abs(table["vol_ratio"].to_numpy() - np.array(free_only)) > 1e-3).all()
    assert result["chosen_g"] == _oracle_choice(table, np.array(oracle), tilt.LOWRISK_TARGET_RATIO)
    assert result["decision"] == "chosen" and result["chosen_g"] != 0.5


def _regime_window() -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Critique 1, probe2: a crash regime in rows 0-119, a calm one after; one 0.001 member misses one price."""
    rng = np.random.default_rng(5)
    low = np.arange(100) < 50
    factor = np.r_[rng.normal(0.0, 0.03, 120), rng.normal(0.0, 0.01, 132)]
    beta = np.where(np.arange(252)[:, None] < 120, 1.0, np.where(low, 0.5, 1.3)[None, :])
    free = factor[:, None] * beta + rng.standard_normal((252, 100)) * np.where(low, 0.005, 0.02)
    pinned = factor + rng.normal(0.0, 0.02, 252)
    names = [f"R{k:03d}" for k in range(101)]
    full = pd.DataFrame(np.column_stack([free, pinned]), columns=names)
    window = full.copy()
    window.iloc[120:122, -1] = np.nan                  # one missing price at row 120 blanks returns 120 and 121
    return window, full, pd.Series([0.999 / 100] * 100 + [0.001], index=names)


def test_regime_fixture_keeps_the_crash_rows() -> None:
    # T3: complete-case rows keep the free members' crash rows; the suffix after the gap would drop them.
    window, full, b = _regime_window()
    vol = tilt.member_vols(window, window.notna().all())
    gaps = []
    for g in tilt.LOWRISK_GRID:
        w, info = tilt.lowrisk_weights(b, vol, window, g)
        assert info["ratio_rows"] == 250 and info["ratio_rows_gap"] == 2 and info["ratio_status"] == "defined_partial"
        bv, wv = b.to_numpy(), w.to_numpy()
        ok = window.notna().all(axis=1).to_numpy()
        x = full.to_numpy()
        rows250 = np.std(x[ok] @ wv, ddof=1) / np.std(x[ok] @ bv, ddof=1)
        rows252 = np.std(x @ wv, ddof=1) / np.std(x @ bv, ddof=1)
        suffix = np.std(x[122:] @ wv, ddof=1) / np.std(x[122:] @ bv, ddof=1)
        assert info["vol_ratio"] == pytest.approx(rows250, rel=1e-12)
        assert abs(info["vol_ratio"] - rows252) <= 1e-3
        gaps.append(abs(suffix - rows252))
    assert max(gaps) > 0.05                            # the fixture bites: the suffix rule would read far lower


def test_ratio_floor_boundary() -> None:
    # T4: 125 complete rows are short; 126 are defined.
    for lead, status in ((127, "ratio_window_short"), (126, "defined_partial")):
        window = pd.DataFrame(_window([0.010, 0.020, 0.015]), columns=["A", "B", "C"])
        window.iloc[:lead, 2] = np.nan
        vol = tilt.member_vols(window, window.notna().all())
        _, info = tilt.lowrisk_weights(pd.Series([0.4, 0.4, 0.2], index=window.columns), vol, window, 1.0)
        assert info["ratio_rows"] == 252 - lead and info["ratio_status"] == status
        assert info["ratio_rows_leading"] == lead and info["ratio_rows_gap"] == 0
        assert math.isnan(info["vol_ratio"]) == (status == "ratio_window_short")


def test_missing_price_at_r_minus_2_removes_two_rows(low_built: dict) -> None:
    # T4 positive control: a missing price at r - 2 blanks the returns at r - 2 and r - 1.
    r = CAL.get_loc(PERTURB_AT)
    inputs = fixture()
    prices = inputs.prices.copy()
    prices.iloc[r - 2, 5] = np.nan
    after = tilt.build_targets(replace(inputs, prices=prices), g=LOW_G)["rebalances"].loc[PERTURB_AT]
    base = low_built["rebalances"].loc[PERTURB_AT]
    assert base["lowrisk_ratio_rows"] == 252 and base["lowrisk_ratio_status"] == "defined_full"
    assert after["lowrisk_ratio_rows"] == 250 and after["lowrisk_ratio_rows_gap"] == 2
    assert after["lowrisk_ratio_status"] == "defined_partial" and after["lowrisk_ratio_limiting_members"] == 1


PINNED_AT = pd.Timestamp("2000-09-29")      # LATE_ASSET is pinned here (164 complete rows)


@pytest.mark.parametrize("change", ["nan", "price"])
def test_pinned_member_future_rows_change_no_ratio(low_built: dict, change: str) -> None:
    # T5, R1: a pinned member's price at row r or later moves no ratio field and no weight at r.
    r = CAL.get_loc(PINNED_AT)
    inputs = fixture()
    prices = inputs.prices.copy()
    prices.iloc[r:, ASSETS.index(LATE_ASSET)] = np.nan if change == "nan" else prices.iloc[r:, 9] * 1.7
    after = tilt.build_targets(replace(inputs, prices=prices), g=LOW_G)
    base = low_built["rebalances"].loc[PINNED_AT]
    assert base["lowrisk_pinned"] == 1 and base["lowrisk_ratio_status"] == "defined_partial"
    assert_frame_equal(after["targets"]["lowrisk"].loc[:PINNED_AT], low_built["targets"]["lowrisk"].loc[:PINNED_AT],
                       check_exact=True)
    assert_frame_equal(after["rebalances"].loc[:PINNED_AT], low_built["rebalances"].loc[:PINNED_AT], check_exact=True)


def test_b2_excluded_name_is_not_in_the_ratio_rows() -> None:
    # T6: a NaN only in the B2-excluded name leaves the ratio rows and the ratio unchanged. The name still enters
    # s_med when it has a full window (Opus round 1), so both calls use the base s_i; the step is the one that
    # calibrate_lowrisk runs.
    inputs = _b2_inputs()
    prices = inputs.prices.copy()
    prices.iloc[CAL.get_loc(PERTURB_AT) - 100, ASSETS.index(B2_ASSET)] = np.nan
    infos, vol = [], None
    for case in (inputs, replace(inputs, prices=prices)):
        disappearances, returns, first_return = tilt.prepare(case)
        setup = tilt.rebalance_members(case, PERTURB_AT, returns, disappearances, first_return)
        assert B2_ASSET in setup["names"] and B2_ASSET not in setup["traded"]
        vol = tilt.member_vols(setup["window"], setup["full"]) if vol is None else vol
        w, info = tilt.lowrisk_weights(setup["b"], vol, setup["window"][setup["traded"]], LOW_G)
        infos.append((w, info))
    assert infos[1][1]["ratio_rows"] == 252 and infos[1][1]["ratio_status"] == "defined_full"
    assert infos[1][1] == infos[0][1]
    assert_series_equal(infos[1][0], infos[0][0], check_exact=True)


def _bracket(ratios: list, rebalances: int, target: float = 0.87, stops: bool = True) -> dict:
    return tilt.lowrisk_bracket([None if r is None else np.array(r) for r in ratios], rebalances, target, stops)


def test_bracket_decisions() -> None:
    # T7: the two-sided median bracket through the helper that calibrate_lowrisk uses.
    one = _bracket([[0.865] * 5 + [0.89] * 4], 10)                 # one undefined in ten
    assert one["decision"] == "ratio_coverage_ambiguous" and one["classes"] == ["ambiguous"]
    assert one["median_hi"][0] == pytest.approx(0.8775) and one["median_lo"] == [0.865]
    critique = _bracket([[0.86] * 5 + [0.88] * 5], 11)             # the defined-only median is 0.87
    assert critique["decision"] == "ratio_coverage_ambiguous" and critique["index"] is None
    robust = _bracket([[0.95] * 9, [0.80, 0.85] * 4 + [0.85]], 10)
    assert robust["decision"] == "chosen" and robust["index"] == 1 and robust["classes"] == ["fails", "meets"]
    fail = _bracket([[0.95] * 10, [0.90] * 10], 10)
    assert fail["decision"] == "no_g_reaches_target" and fail["classes"] == ["fails", "fails"]
    before = _bracket([[0.95] * 10, [0.865] * 5 + [0.89] * 4, [0.80] * 9], 10)
    assert before["classes"] == ["fails", "ambiguous", "meets"] and before["decision"] == "ratio_coverage_ambiguous"
    after = _bracket([[0.80] * 9, [0.865] * 5 + [0.89] * 4], 10)   # an ambiguous value above the choice
    assert after["decision"] == "chosen" and after["index"] == 0


def test_bracket_refusals_and_coverage() -> None:
    # T11: one undefined in ten passes the coverage stop, two do not; the refusal rule comes first.
    assert tilt.LOWRISK_UNDEFINED_MAX == 0.10 and tilt.LOWRISK_RATIO_MIN_ROWS == 126
    assert _bracket([[0.80] * 9], 10)["decision"] == "chosen"
    two = _bracket([[0.80] * 8], 10)
    assert two["decision"] == "ratio_coverage_low" and two["undefined_share"] == 0.2
    assert _bracket([[0.80] * 8], 10, stops=False)["decision"] == "chosen"
    refused = _bracket([[0.95] * 10, None, [0.80] * 10], 10)
    assert (refused["decision"], refused["index"]) == ("refused", 1)
    assert _bracket([[0.95] * 10, None], 10)["decision"] == "refused"
    assert _bracket([[0.80] * 10, None], 10)["decision"] == "chosen"
    assert _bracket([[0.95] * 10, None, [0.80] * 10], 10, stops=False)["index"] == 2


def test_ratio_status_does_not_depend_on_g() -> None:
    # T8: from START the fixture has short, partial, and full rebalances; each holds the same status for every g.
    result = tilt.calibrate_lowrisk(fixture(), CAL_GRID, 0.99, START, END)
    table = result["rebalances"]
    assert set(table["ratio_status"]) == {"ratio_window_short", "defined_partial", "defined_full"}
    fields = ["ratio_status", "ratio_rows", "ratio_rows_leading", "ratio_rows_gap", "ratio_limiting_members",
              "ratio_limiting_cw_share"]
    assert (table.groupby("date")[fields].nunique() == 1).all().all()
    assert (table.groupby("date")["g"].count() == len(CAL_GRID)).all()


def test_complete_history_ratio_is_the_round_one_value() -> None:
    # T9: with no pinned member, the whole book is the free book; the ratio is the ba71a67 expression, bit for bit.
    returns = _window([0.06, 0.08, 0.12, 0.16])
    b, w, info = _lowrisk([0.4, 0.3, 0.2, 0.1], returns, 1.0)
    window = pd.DataFrame(returns).to_numpy(dtype=float)[:, np.ones(4, dtype=bool)]
    expected = tilt.ex_ante_vol(window, w.to_numpy()) / tilt.ex_ante_vol(window, b.to_numpy())
    assert info["vol_ratio"] == expected and info["ratio_rows"] == 252 and info["ratio_limiting_members"] == 0


def test_lowrisk_weights_do_not_depend_on_the_ratio_step(monkeypatch: pytest.MonkeyPatch, low_built: dict) -> None:
    # T10: the weights, TE, TE scale, and cap counts are computed before the ratio and do not read it.
    record = {"ex_ante_vol": 1.0, "cw_ex_ante_vol": 1.0, "vol_ratio": 1.0, "ratio_status": "defined_full",
              "ratio_rows": 0, "ratio_rows_leading": 0, "ratio_rows_gap": 0, "ratio_limiting_members": 0,
              "ratio_limiting_cw_share": 0.0}
    monkeypatch.setattr(tilt, "whole_book_ratio", lambda window, b, w: dict(record))
    after = tilt.build_targets(fixture(), g=LOW_G)
    for book in ("cw", "tilt", "lowrisk"):
        assert_frame_equal(after["targets"][book], low_built["targets"][book], check_exact=True)
    columns = [c for c in low_built["rebalances"].columns if c[len("lowrisk_"):] not in record]
    assert_frame_equal(after["rebalances"][columns], low_built["rebalances"][columns], check_exact=True)


def test_window_diagnostic_flags_a_different_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    # T12: treating the partial rebalances as undefined changes the choice; the flag is set and nothing stops.
    inputs = replace(fixture(), start=CAL_START)
    result = tilt.calibrate_lowrisk(inputs, CAL_GRID, 0.99, CAL_START, END)
    grid = result["grid"].set_index("g")
    assert result["decision"] == "chosen" and result["chosen_g"] == 0.2
    assert grid.loc[0.2, "bracket"] == "meets" and grid.loc[0.2, "bracket_full_windows"] == "ambiguous"
    assert result["window_decision"] == "ratio_coverage_ambiguous" and result["window_chosen_g"] is None
    assert result["window_sensitive"] and result["window_diag_coverage_high"]
    assert result["window_diag_undefined_share"] == pytest.approx(4 / 12)


def test_window_diagnostic_coverage_alone_does_not_flag() -> None:
    # Coordinator ruling (2026-10-05): over 10 percent partial rebalances with the same choice is not sensitive.
    result = tilt.calibrate_lowrisk(fixture(), CAL_GRID, 0.999, CAL_START, END)
    assert result["decision"] == "chosen" and result["window_decision"] == "chosen"
    assert result["chosen_g"] == result["window_chosen_g"]
    assert result["window_diag_undefined_share"] > tilt.LOWRISK_UNDEFINED_MAX
    assert result["window_diag_coverage_high"] and not result["window_sensitive"]


def test_rows_of_a_g_refused_later_are_tagged(monkeypatch: pytest.MonkeyPatch, calibration: dict) -> None:
    # Opus ADV-R2-01: a g above the choice that refuses at the sixth rebalance keeps its five earlier rows, tagged.
    dates = tilt.rebalance_dates(CAL, CAL_START, END)
    original = tilt.lowrisk_weights

    def spy(b, vol, window, g):
        if g == CAL_GRID[-1] and window.index[-1] >= CAL[CAL.get_loc(dates[5]) - 1]:
            raise RunnerStop("lowrisk_loop_not_converged", "test")
        return original(b, vol, window, g)

    monkeypatch.setattr(tilt, "lowrisk_weights", spy)
    result = tilt.calibrate_lowrisk(fixture(), CAL_GRID, 0.99, CAL_START, END)
    assert result["decision"] == "chosen" and result["chosen_g"] == calibration["chosen_g"]
    table = result["rebalances"]
    refused = table[table["g"] == CAL_GRID[-1]]
    assert len(refused) == 5 and (refused["g_status"] == "refused").all()
    assert refused["date"].tolist() == list(dates[:5])
    assert (table.loc[table["g"] != CAL_GRID[-1], "g_status"] == "ok").all()
    row = result["grid"].set_index("g").loc[CAL_GRID[-1]]
    assert row["status"] == "refused" and row["refusal_date"] == dates[5] and np.isnan(row["median_vol_ratio"])
    kept = table.drop(columns="g_status")
    assert_frame_equal(kept[kept["g"] != CAL_GRID[-1]].reset_index(drop=True),
                       calibration["rebalances"].drop(columns="g_status").pipe(
                           lambda t: t[t["g"] != CAL_GRID[-1]]).reset_index(drop=True), check_exact=True)
