"""Synthetic tests for the Milestone 5.5 point-in-time signals S1 to S8 (card m55-signals).

Every table is generated here; no test reads data or opens a network connection.
The hand cases change permno 101 (gvkey G101) and read it at rebalance ``R``.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import research.m55_signals as sig
from research.m55_index_tilt import rebalance_dates
from research.m4_7_sp500_pit_rerun import RunnerStop


CAL = pd.bdate_range("1995-01-02", "2002-12-31", name="date")
PERMNOS = [101, 102, 103, 104, 105]
EXIT = pd.Timestamp("2001-06-29")          # permno 105 leaves the index
R = pd.Timestamp("2000-07-31")             # hand rebalance; its decision row t = r - 1 is 2000-07-28
T = pd.Timestamp("2000-07-28")
A = pd.Timestamp("2000-06-30")             # month-end row before t's month (S7, S8 shares)
A12 = pd.Timestamp("1999-06-30")
REBALANCES = rebalance_dates(CAL, pd.Timestamp("1997-12-31"), pd.Timestamp("2002-11-29"))


def gvkey(p: int) -> str:
    return f"G{p}"


def base_inputs(seed: int = 3) -> sig.SignalInputs:
    rng = np.random.default_rng(seed)
    daily = []
    for k, p in enumerate(PERMNOS):
        ret = rng.normal(0.0004, 0.01, len(CAL))
        shrout = 1000.0 * (1.0 + 0.0002 * np.arange(len(CAL))) if p == 102 else np.full(len(CAL), 1000.0)
        daily.append(pd.DataFrame({"permno": p, "date": CAL, "ret": ret, "prc": (20.0 + 5 * k) * np.cumprod(1 + ret),
                                   "shrout": shrout, "cfacpr": 1.0, "cfacshr": 1.0}))
    daily = pd.concat(daily, ignore_index=True)
    members = pd.DataFrame({"permno": PERMNOS, "start": CAL[0], "end": [CAL[-1]] * 4 + [EXIT]})
    link = pd.DataFrame({"gvkey": [gvkey(p) for p in PERMNOS], "permno": PERMNOS,
                         "linkdt": pd.Timestamp("1990-01-01"), "linkenddt": pd.NaT})
    link["linkenddt"] = link["linkenddt"].astype("datetime64[ns]")
    annual, quarterly, ibes = [], [], []
    shares = {"revt": 0.8, "cogs": 0.5, "act": 0.4, "che": 0.1, "lct": 0.3, "dlc": 0.05, "txp": 0.01, "dp": 0.03,
              "seq": 0.4, "ceq": 0.38, "pstk": 0.02, "pstkrv": 0.02, "pstkl": 0.02, "txditc": 0.01, "lt": 0.6}
    for k, p in enumerate(PERMNOS):
        for n, year in enumerate(range(1992, 2002)):
            at = 100.0 * (1 + k) * 1.06 ** n * (1 + 0.02 * rng.standard_normal())
            datadate = pd.Timestamp(f"{year}-12-31")
            row = {"gvkey": gvkey(p), "datadate": datadate, "known_date": datadate + pd.Timedelta(days=80), "at": at}
            row.update({name: at * f * (1 + 0.05 * rng.standard_normal()) for name, f in shares.items()})
            annual.append(row)
        for datadate in pd.date_range("1992-03-31", "2002-09-30", freq="QE"):
            rdq = datadate + pd.Timedelta(days=25)
            quarterly.append({"gvkey": gvkey(p), "datadate": datadate, "known_date": rdq + pd.Timedelta(days=5),
                              "epspxq": 1.0 + 0.1 * rng.standard_normal(), "rdq": rdq})
        estimate = 2.0
        for month in pd.date_range("1994-01-01", "2002-12-01", freq="MS"):
            estimate += 0.02 * rng.standard_normal()
            statpers = month + pd.Timedelta(days=14)
            ibes.append({"permno": p, "statpers": statpers, "fpedats": pd.Timestamp(f"{statpers.year}-12-31"),
                         "fpi": "1", "meanest": estimate})
    return sig.SignalInputs(daily=daily, members=members, fund_annual=pd.DataFrame(annual),
                            fund_quarterly=pd.DataFrame(quarterly), link=link, ibes=pd.DataFrame(ibes))


@pytest.fixture(scope="module")
def base() -> sig.SignalInputs:
    return base_inputs()


@pytest.fixture(scope="module")
def base_result(base: sig.SignalInputs) -> dict:
    return sig.build_signals(base, REBALANCES)


def at_r(inputs: sig.SignalInputs, permno: int = 101, rebalances: pd.DatetimeIndex | None = None) -> dict:
    """Value or reason of each signal for one member at R."""
    result = sig.build_signals(inputs, pd.DatetimeIndex([R]) if rebalances is None else rebalances)
    out = {}
    for s in sig.SIGNAL_IDS:
        value = result["values"][s].loc[R, permno]
        out[s] = result["reasons"][s].loc[R, permno] if np.isnan(value) else float(value)
    return out


def edit(frame: pd.DataFrame, mask: pd.Series, **values) -> pd.DataFrame:
    frame = frame.copy()
    for column, value in values.items():
        frame.loc[mask, column] = value
    return frame


def daily_mask(inputs: sig.SignalInputs, permno: int, date: str | pd.Timestamp) -> pd.Series:
    return (inputs.daily["permno"] == permno) & (inputs.daily["date"] == pd.Timestamp(date))


def annual_mask(inputs: sig.SignalInputs, p: int, datadate: str) -> pd.Series:
    return (inputs.fund_annual["gvkey"] == gvkey(p)) & (inputs.fund_annual["datadate"] == pd.Timestamp(datadate))


# Panels and typed missing (R6) ----------------------------------------------------------

def test_base_panel_shape_signs_and_typed_cells(base_result: dict) -> None:
    assert base_result["signs"] == {"S1": 1, "S2": 1, "S3": 1, "S4": 1, "S5": -1, "S6": -1, "S7": -1, "S8": 1}
    assert base_result["timing_contract"] == "after_close_signal_next_observed_close_v1"
    members = base_result["members"]
    assert list(members.columns) == PERMNOS and members.index.equals(REBALANCES)
    assert not members.loc[members.index > EXIT, 105].any() and members.loc[members.index <= EXIT, 105].all()
    for s in sig.SIGNAL_IDS:
        values = base_result["values"][s].to_numpy()
        reasons = base_result["reasons"][s].to_numpy()
        m = members.to_numpy()
        has_value = np.isfinite(values)
        has_reason = ~pd.isna(reasons)
        assert (has_value ^ has_reason)[m].all(), s            # exactly one: a value or a reason
        assert not (has_value | has_reason)[~m].any(), s        # non-member cells are empty
        assert set(reasons[has_reason].tolist()) <= set(sig.REASONS), s
        assert has_value[m].mean() > 0.5, s                     # the base world is mostly valid


def test_reason_counts_match_cells_and_count_an_injected_gap(base: sig.SignalInputs, base_result: dict) -> None:
    counts = sig.reason_counts(base_result)
    members = base_result["members"]
    per_year = members.groupby(members.index.year).sum().sum(axis=1)
    for s in sig.SIGNAL_IDS:
        total = counts[counts["signal"] == s].groupby("year")["count"].sum()
        assert total.to_dict() == per_year.to_dict()
    # S1: an earlier estimate in the prior fiscal year changes FY1 every February to April.
    s1 = counts[(counts["signal"] == "S1") & (counts["reason"] == "fpe_changed")].set_index("year")["count"]
    assert s1.loc[1999] == 3 * 5

    gap = replace(base, fund_annual=edit(base.fund_annual, annual_mask(base, 104, "1999-12-31"), revt=np.nan))
    after = sig.reason_counts(sig.build_signals(gap, REBALANCES))

    def count(frame: pd.DataFrame, year: int, reason: str) -> int:
        hit = frame[(frame["signal"] == "S4") & (frame["year"] == year) & (frame["reason"] == reason)]
        return int(hit["count"].sum())

    # FY1999 is the current year from the 2000-07 to the 2001-06 rebalance: six cells in 2000, six in 2001.
    assert count(after, 2000, "missing_item") == count(counts, 2000, "missing_item") + 6
    assert count(after, 2001, "missing_item") == count(counts, 2001, "missing_item") + 6
    assert count(after, 2000, "valid") == count(counts, 2000, "valid") - 6


# Timing (R1) ----------------------------------------------------------------------------

def perturb_from(inputs: sig.SignalInputs, r: pd.Timestamp) -> sig.SignalInputs:
    """Change every row dated at or after r, and add a revision known at r."""
    daily = inputs.daily.copy()
    late = daily["date"] >= r
    daily.loc[late, ["ret", "prc", "shrout", "cfacshr"]] = daily.loc[late, ["ret", "prc", "shrout", "cfacshr"]] * 1.7
    annual = inputs.fund_annual.copy()
    late = annual["known_date"] >= r
    annual.loc[late, list(sig.ANNUAL_ITEMS)] = annual.loc[late, list(sig.ANNUAL_ITEMS)] + 7.0
    revision = annual[annual["known_date"] < r].iloc[[-1, -11]].copy()
    revision["known_date"] = r
    revision[list(sig.ANNUAL_ITEMS)] = revision[list(sig.ANNUAL_ITEMS)] * 5.0
    annual = pd.concat([annual, revision], ignore_index=True)
    quarterly = inputs.fund_quarterly.copy()
    late = (quarterly["known_date"] >= r) | (quarterly["rdq"] >= r)
    quarterly.loc[late, "epspxq"] = quarterly.loc[late, "epspxq"] + 4.0
    quarterly.loc[late, "rdq"] = quarterly.loc[late, "rdq"] - pd.Timedelta(days=20)
    ibes = inputs.ibes.copy()
    late = ibes["statpers"] >= r
    ibes.loc[late, "meanest"] = ibes.loc[late, "meanest"] + 9.0
    ibes.loc[late, "fpedats"] = pd.Timestamp("2099-12-31")
    return sig.SignalInputs(daily=daily, members=inputs.members, fund_annual=annual, fund_quarterly=quarterly,
                            link=inputs.link, ibes=ibes)


@pytest.mark.parametrize("r", [R, pd.Timestamp("2001-03-30"), pd.Timestamp("2002-01-31")])
def test_future_perturbation_leaves_every_signal_bit_identical(base: sig.SignalInputs, base_result: dict,
                                                               r: pd.Timestamp) -> None:
    after = sig.build_signals(perturb_from(base, r), REBALANCES)
    upto = REBALANCES[REBALANCES <= r]
    for s in sig.SIGNAL_IDS:
        assert_frame_equal(after["values"][s].loc[upto], base_result["values"][s].loc[upto], check_exact=True)
        assert_frame_equal(after["reasons"][s].loc[upto], base_result["reasons"][s].loc[upto])
    later = REBALANCES[REBALANCES > r]
    if len(later):
        changed = [s for s in sig.SIGNAL_IDS
                   if not after["values"][s].loc[later].equals(base_result["values"][s].loc[later])]
        assert set(changed) == set(sig.SIGNAL_IDS)


def test_positive_controls_at_the_latest_usable_row(base: sig.SignalInputs) -> None:
    """The same kind of change at the last row each rule admits changes the value; one row later it does not."""
    before = at_r(base)

    def changed(inputs: sig.SignalInputs) -> set[str]:
        after = at_r(inputs)
        return {s for s in sig.SIGNAL_IDS if after[s] != before[s]}

    # Annual revision known at r - 2 is usable from r - 1 (S4, S5, S6, S8); known at r - 1 it is not.
    for known, expected in (("2000-07-27", {"S4", "S5", "S6", "S8"}), ("2000-07-28", set())):
        revision = base.fund_annual[annual_mask(base, 101, "1999-12-31")].copy()
        revision["known_date"] = pd.Timestamp(known)
        revision[["at", "revt", "act", "seq"]] = revision[["at", "revt", "act", "seq"]] * 1.5
        assert changed(replace(base, fund_annual=pd.concat([base.fund_annual, revision], ignore_index=True))) \
            == expected

    # S2: a quarter reported and known at r - 2 is used at r; at r - 1 it is not.
    q2 = (base.fund_quarterly["gvkey"] == "G101") & (base.fund_quarterly["datadate"] == pd.Timestamp("2000-06-30"))
    for day, expected in (("2000-07-27", {"S2"}), ("2000-07-28", set())):
        quarterly = edit(base.fund_quarterly, q2, rdq=pd.Timestamp(day), known_date=pd.Timestamp(day))
        assert changed(replace(base, fund_quarterly=quarterly)) - {"S3"} == expected

    # S3: usable from rdq + 2 trading days, so the last admitted report date is r - 3; the day +1 return is r - 2.
    report = edit(base.fund_quarterly, q2, rdq=pd.Timestamp("2000-07-26"), known_date=pd.Timestamp("2000-07-26"))
    s3_inputs = replace(base, fund_quarterly=report)
    s3_before = at_r(s3_inputs)["S3"]
    assert isinstance(s3_before, float)
    bumped = replace(s3_inputs, daily=edit(base.daily, daily_mask(base, 101, "2000-07-27"), ret=0.05))
    assert at_r(bumped)["S3"] != s3_before
    bumped = replace(s3_inputs, daily=edit(base.daily, daily_mask(base, 101, "2000-07-28"), ret=0.05))
    assert at_r(bumped)["S3"] == s3_before
    late = edit(base.fund_quarterly, q2, rdq=pd.Timestamp("2000-07-27"), known_date=pd.Timestamp("2000-07-27"))
    assert at_r(replace(base, fund_quarterly=late))["S3"] == "not_yet_known"

    # S1: the June statistics date is usable from the June month end; the July one (before r) waits for 2000-07-31.
    ibes = base.ibes
    june = (ibes["permno"] == 101) & (ibes["statpers"] == pd.Timestamp("2000-06-15"))
    july = (ibes["permno"] == 101) & (ibes["statpers"] == pd.Timestamp("2000-07-15"))
    assert changed(replace(base, ibes=edit(ibes, june, meanest=7.0))) == {"S1"}
    assert changed(replace(base, ibes=edit(ibes, july, meanest=7.0))) == set()

    # S7 and S8 read shares at the month end before t's month, not at r - 2.
    assert changed(replace(base, daily=edit(base.daily, daily_mask(base, 101, A), shrout=1300.0))) == {"S7", "S8"}
    assert changed(replace(base, daily=edit(base.daily, daily_mask(base, 101, "2000-07-27"), shrout=1300.0))) \
        == set()


def test_revision_is_used_only_from_its_known_date_plus_one_row(base: sig.SignalInputs) -> None:
    revision = base.fund_annual[annual_mask(base, 101, "1999-12-31")].copy()
    revision["known_date"] = pd.Timestamp("2000-10-16")       # Monday; usable from Tuesday 2000-10-17
    revision["revt"] = revision["revt"] + 40.0
    inputs = replace(base, fund_annual=pd.concat([base.fund_annual, revision], ignore_index=True))
    old = base.fund_annual[annual_mask(base, 101, "1999-12-31")].iloc[0]
    days = pd.DatetimeIndex(["2000-10-17", "2000-10-18"])     # decision rows 2000-10-16 and 2000-10-17
    result = sig.build_signals(inputs, days)
    s4 = result["values"]["S4"][101]
    assert s4.iloc[0] == (old["revt"] - old["cogs"]) / old["at"]
    assert s4.iloc[1] == (old["revt"] + 40.0 - old["cogs"]) / old["at"]


# Hand-computed values -------------------------------------------------------------------

def hand_inputs(base: sig.SignalInputs) -> sig.SignalInputs:
    annual = base.fund_annual
    annual = edit(annual, annual_mask(base, 101, "1999-12-31"), at=110.0, revt=52.0, cogs=19.0, act=40.0, che=10.0,
                  lct=30.0, dlc=5.0, txp=2.0, dp=3.0, seq=40.0, pstkrv=2.0, txditc=1.0)
    annual = edit(annual, annual_mask(base, 101, "1998-12-31"), at=90.0, act=35.0, che=8.0, lct=26.0, dlc=4.0,
                  txp=1.0)
    # S2: 13 quarters 1997Q1 to 2000Q1; prior differences 0.01 to 0.08, current difference 0.10.
    eps = [1.0, 1.0, 1.0, 1.0, 1.01, 1.02, 1.03, 1.04, 1.06, 1.08, 1.10, 1.12, 1.16]
    quarterly = base.fund_quarterly.copy()
    for datadate, value in zip(pd.date_range("1997-03-31", "2000-03-31", freq="QE"), eps):
        mask = (quarterly["gvkey"] == "G101") & (quarterly["datadate"] == datadate)
        quarterly.loc[mask, "epspxq"] = value
    # S3: report date 2000-04-25 (base rule: quarter end + 25 days); window 04-24 to 04-26.
    daily = base.daily.copy()
    for day in ("2000-04-21", "2000-04-24", "2000-04-25"):
        daily.loc[daily["date"] == pd.Timestamp(day), ["prc", "shrout"]] = [10.0, 1000.0]
    for day, value in (("2000-04-24", 0.01), ("2000-04-25", 0.02), ("2000-04-26", -0.01)):
        daily.loc[daily["date"] == pd.Timestamp(day), "ret"] = 0.0
        daily.loc[daily_mask(base, 101, day), "ret"] = value
    # S7 and S8: shares at A and A12; price at A.
    daily.loc[daily_mask(base, 101, A), ["prc", "shrout"]] = [25.0, 1100.0]
    daily.loc[daily_mask(base, 101, A12), "shrout"] = 1000.0
    # S1: June and March 2000 statistics, same FY1; price at the March month end.
    ibes = base.ibes.copy()
    ibes.loc[(ibes["permno"] == 101) & (ibes["statpers"] == pd.Timestamp("2000-06-15")), "meanest"] = 2.2
    ibes.loc[(ibes["permno"] == 101) & (ibes["statpers"] == pd.Timestamp("2000-03-15")), "meanest"] = 2.0
    daily.loc[daily_mask(base, 101, "2000-03-31"), "prc"] = 40.0
    return sig.SignalInputs(daily=daily, members=base.members, fund_annual=annual, fund_quarterly=quarterly,
                            link=base.link, ibes=ibes)


def test_hand_computed_values(base: sig.SignalInputs) -> None:
    got = at_r(hand_inputs(base))
    assert got["S1"] == pytest.approx((2.2 - 2.0) / 40.0, rel=1e-12)
    assert got["S2"] == pytest.approx(0.1 / statistics.stdev([0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]),
                                      rel=1e-9)
    assert got["S3"] == pytest.approx(1.01 * 1.02 * 0.99 - 1.002 * 1.004 * 0.998, rel=1e-12)
    assert got["S4"] == pytest.approx((52.0 - 19.0) / 110.0, rel=1e-12)
    # Sloan: ((5 - 2) - (4 - 1 - 1) - 3) / ((110 + 90) / 2) = -2 / 100.
    assert got["S5"] == pytest.approx(-0.02, rel=1e-12)
    assert got["S6"] == pytest.approx(110.0 / 90.0 - 1.0, rel=1e-12)
    assert got["S7"] == pytest.approx(math.log(1.1), rel=1e-12)
    assert got["S8"] == pytest.approx((40.0 - 2.0 + 1.0) / (25.0 * 1100.0), rel=1e-12)


def test_s1_is_split_consistent(base: sig.SignalInputs) -> None:
    """A 2-for-1 split between the two statistics dates leaves S1 as without the split."""
    inputs = hand_inputs(base)
    daily = inputs.daily.copy()
    split = (daily["permno"] == 101) & (daily["date"] < pd.Timestamp("2000-05-01"))
    daily.loc[split, "cfacshr"] = 2.0                        # rows before the split: two new shares per old share
    ibes = inputs.ibes.copy()
    ibes.loc[(ibes["permno"] == 101) & (ibes["statpers"] == pd.Timestamp("2000-06-15")), "meanest"] = 1.1
    got = at_r(replace(inputs, daily=daily, ibes=ibes))
    assert got["S1"] == pytest.approx((2.2 - 2.0) / 40.0, rel=1e-12)


@pytest.mark.parametrize(("items", "be"), [
    ({"seq": 40.0, "pstkrv": 2.0, "txditc": 1.0}, 39.0),
    ({"seq": np.nan, "ceq": 38.0, "pstk": 3.0, "pstkrv": np.nan, "pstkl": 2.5, "txditc": np.nan}, 38.5),
    ({"seq": np.nan, "ceq": np.nan, "at": 100.0, "lt": 70.0, "pstkrv": np.nan, "pstkl": np.nan, "pstk": 1.0,
      "txditc": 2.0}, 31.0),
])
def test_book_equity_fallbacks(base: sig.SignalInputs, items: dict, be: float) -> None:
    inputs = hand_inputs(base)
    inputs = replace(inputs, fund_annual=edit(inputs.fund_annual, annual_mask(base, 101, "1999-12-31"), **items))
    assert at_r(inputs)["S8"] == pytest.approx(be / (25.0 * 1100.0), rel=1e-12)


def test_s8_nonpositive_book_equity_and_missing_preferred(base: sig.SignalInputs) -> None:
    inputs = hand_inputs(base)
    mask = annual_mask(base, 101, "1999-12-31")
    assert at_r(replace(inputs, fund_annual=edit(inputs.fund_annual, mask, seq=2.0, txditc=0.0)))["S8"] \
        == "be_nonpositive"
    gone = edit(inputs.fund_annual, mask, pstkrv=np.nan, pstkl=np.nan, pstk=np.nan)
    assert at_r(replace(inputs, fund_annual=gone))["S8"] == "missing_item"


def test_s2_zero_spread_and_short_history(base: sig.SignalInputs) -> None:
    quarterly = base.fund_quarterly.copy()
    g101 = quarterly["gvkey"] == "G101"
    quarterly.loc[g101, "epspxq"] = 1.0
    assert at_r(replace(base, fund_quarterly=quarterly))["S2"] == "zero_denominator"
    # Three missing quarters remove six of the eight differences: fewer than six stay valid.
    quarterly = base.fund_quarterly.copy()
    for datadate in ("1998-03-31", "1998-06-30", "1998-09-30"):
        quarterly.loc[g101 & (quarterly["datadate"] == pd.Timestamp(datadate)), "epspxq"] = np.nan
    assert at_r(replace(base, fund_quarterly=quarterly))["S2"] == "short_history"


# Maximum age ----------------------------------------------------------------------------

def test_max_age_annual(base: sig.SignalInputs) -> None:
    """S4 uses the record whose fiscal end + 18 months is t; one day earlier it is stale."""
    keep = ~((base.fund_annual["gvkey"] == "G101") & (base.fund_annual["datadate"] >= pd.Timestamp("1999-12-31")))
    for datadate, expected in (("1999-01-28", float), ("1999-01-27", "stale")):
        annual = edit(base.fund_annual[keep], annual_mask(base, 101, "1998-12-31")[keep],
                      datadate=pd.Timestamp(datadate))
        got = at_r(replace(base, fund_annual=annual))["S4"]
        assert isinstance(got, float) if expected is float else got == expected


def test_max_age_quarterly(base: sig.SignalInputs) -> None:
    """S2 and S3 use a report date of t - 6 months; one day earlier they are stale."""
    q = base.fund_quarterly
    keep = ~((q["gvkey"] == "G101") & (q["datadate"] > pd.Timestamp("1999-12-31")))
    last = ((q["gvkey"] == "G101") & (q["datadate"] == pd.Timestamp("1999-12-31")))[keep]
    for rdq, valid in (("2000-01-28", True), ("2000-01-27", False)):
        quarterly = edit(q[keep], last, rdq=pd.Timestamp(rdq), known_date=pd.Timestamp(rdq))
        got = at_r(replace(base, fund_quarterly=quarterly))
        for s in ("S2", "S3"):
            assert isinstance(got[s], float) if valid else got[s] == "stale"


def test_max_age_ibes(base: sig.SignalInputs) -> None:
    """S1 uses a statistics date of t - 2 months; one day earlier it is stale."""
    ibes = base.ibes
    keep = ~((ibes["permno"] == 101) & (ibes["statpers"] > pd.Timestamp("2000-05-31")))
    may = ((ibes["permno"] == 101) & (ibes["statpers"] == pd.Timestamp("2000-05-15")))[keep]
    for statpers, valid in (("2000-05-28", True), ("2000-05-27", False)):
        got = at_r(replace(base, ibes=edit(ibes[keep], may, statpers=pd.Timestamp(statpers))))["S1"]
        assert isinstance(got, float) if valid else got == "stale"


def test_max_age_shares(base: sig.SignalInputs) -> None:
    """S7 reads the latest daily row at most one month before the month-end anchor A."""
    for last_row, valid in (("2000-05-30", True), ("2000-05-29", False)):
        gone = (base.daily["permno"] == 101) & (base.daily["date"] > pd.Timestamp(last_row)) \
            & (base.daily["date"] <= A)
        got = at_r(replace(base, daily=base.daily[~gone]))["S7"]
        assert isinstance(got, float) if valid else got == "stale"


# Identity (R3) and backfill -------------------------------------------------------------

def test_ambiguous_link_blanks_only_that_member(base: sig.SignalInputs, base_result: dict) -> None:
    extra = pd.DataFrame({"gvkey": ["G999"], "permno": [102], "linkdt": [pd.Timestamp("2000-01-03")],
                          "linkenddt": [pd.NaT]}).astype({"linkenddt": "datetime64[ns]"})
    result = sig.build_signals(replace(base, link=pd.concat([base.link, extra], ignore_index=True)), REBALANCES)
    later = REBALANCES[REBALANCES > pd.Timestamp("2000-01-04")]
    for s in ("S2", "S3", "S4", "S5", "S6", "S8"):
        assert (result["reasons"][s].loc[later, 102] == "ambiguous_link").all()
        assert result["values"][s].loc[later, 102].isna().all()
    for s in sig.SIGNAL_IDS:
        others = [p for p in PERMNOS if p != 102]
        assert_frame_equal(result["values"][s][others], base_result["values"][s][others], check_exact=True)
        if s in ("S1", "S7"):   # IBES and CRSP signals use no Compustat link
            assert_frame_equal(result["values"][s], base_result["values"][s], check_exact=True)


def test_one_gvkey_on_two_permnos_and_no_link(base: sig.SignalInputs) -> None:
    link = base.link.copy()
    link.loc[link["permno"] == 104, "gvkey"] = "G103"
    got = at_r(replace(base, link=link), permno=103)
    assert all(got[s] == "ambiguous_link" for s in ("S2", "S3", "S4", "S5", "S6", "S8"))
    assert at_r(replace(base, link=link), permno=104)["S4"] == "ambiguous_link"
    got = at_r(replace(base, link=base.link[base.link["permno"] != 104]), permno=104)
    assert all(got[s] == "no_link" for s in ("S2", "S3", "S4", "S5", "S6", "S8"))
    assert isinstance(got["S1"], float) and isinstance(got["S7"], float)


def test_link_dates_bound_the_join(base: sig.SignalInputs) -> None:
    """A link is used only when it is valid at t."""
    for start, linked in (("2000-07-28", True), ("2000-07-29", False)):
        link = edit(base.link, base.link["permno"] == 101, linkdt=pd.Timestamp(start))
        assert (at_r(replace(base, link=link))["S4"] != "no_link") == linked
    for end, linked in (("2000-07-28", True), ("2000-07-27", False)):
        link = edit(base.link, base.link["permno"] == 101, linkenddt=pd.Timestamp(end))
        assert (at_r(replace(base, link=link))["S4"] != "no_link") == linked


def test_backfilled_history_is_short(base: sig.SignalInputs) -> None:
    """A prior fiscal year that became known only later does not count as history at t."""
    old = (base.fund_annual["gvkey"] == "G103") & (base.fund_annual["datadate"] < pd.Timestamp("1999-12-31"))
    annual = edit(base.fund_annual, old, known_date=pd.Timestamp("2001-01-02"))
    got = at_r(replace(base, fund_annual=annual), permno=103)
    assert all(got[s] == "short_history" for s in ("S4", "S5", "S6", "S8"))
    assert at_r(replace(base, fund_annual=base.fund_annual[~old]), permno=103)["S4"] == "short_history"


def test_annual_value_waits_six_months_after_fiscal_end(base: sig.SignalInputs) -> None:
    days = pd.DatetimeIndex(["2000-06-30", "2000-07-03"])   # decision rows 2000-06-29 and 2000-06-30
    s6 = sig.build_signals(base, days)["values"]["S6"][101]
    at = base.fund_annual.set_index(["gvkey", "datadate"])["at"]
    assert s6.iloc[0] == at[("G101", pd.Timestamp("1998-12-31"))] / at[("G101", pd.Timestamp("1997-12-31"))] - 1
    assert s6.iloc[1] == at[("G101", pd.Timestamp("1999-12-31"))] / at[("G101", pd.Timestamp("1998-12-31"))] - 1


# Universe return and coverage -----------------------------------------------------------

def test_missing_member_return_blanks_the_universe_day(base: sig.SignalInputs) -> None:
    inputs = hand_inputs(base)
    daily = edit(inputs.daily, daily_mask(base, 104, "2000-04-25"), ret=np.nan)
    assert at_r(replace(inputs, daily=daily))["S3"] == "no_market_data"
    # A non-member's gap does not touch the universe: 105 has left by 2001-07, so its return there is unused.
    calendar = np.unique(inputs.daily["date"].to_numpy().astype("datetime64[ns]"))
    late = edit(inputs.daily, daily_mask(base, 105, "2001-08-01"), ret=np.nan)
    before = sig.universe_returns(inputs, calendar)
    after = sig.universe_returns(replace(inputs, daily=late), calendar)
    assert np.array_equal(before, after, equal_nan=True)


def coverage_panels(invalid: dict[pd.Timestamp, int], members: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    index = pd.DatetimeIndex(pd.date_range("1990-01-31", "1992-12-31", freq="ME"), name="date")
    member = pd.DataFrame(True, index=index, columns=range(members))
    reasons = pd.DataFrame(None, index=index, columns=range(members), dtype=object)
    for date, n in invalid.items():
        reasons.loc[date, list(range(n))] = "stale"
    return reasons, member


def test_real_start_at_the_80_percent_boundary() -> None:
    year = {d: 2 for d in pd.date_range("1990-01-31", "1990-12-31", freq="ME")}   # exactly 80 percent valid
    assert sig.real_start(*coverage_panels(year)) == 1990
    year[pd.Timestamp("1990-06-30")] = 3                                            # one month at 70 percent
    assert sig.real_start(*coverage_panels(year)) == 1991
    year[pd.Timestamp("1992-12-31")] = 3                                            # the last year fails
    assert sig.real_start(*coverage_panels(year)) is None
    assert sig.real_start(*coverage_panels({pd.Timestamp("1991-03-31"): 3})) == 1992
    reasons, members = coverage_panels({})
    assert sig.real_start(reasons, members) == 1990
    members.loc[pd.Timestamp("1990-05-31")] = False                                # a month without members fails
    assert sig.real_start(reasons, members) == 1991
    # Non-member cells never count: two invalid members of ten, plus five non-members, is still 80 percent.
    reasons, members = coverage_panels({d: 2 for d in pd.date_range("1990-01-31", "1992-12-31", freq="ME")}, 15)
    members[[10, 11, 12, 13, 14]] = False
    assert sig.real_start(reasons, members) == 1990


# Schema validation ----------------------------------------------------------------------

@pytest.mark.parametrize(("change", "reason"), [
    (lambda i: replace(i, daily=i.daily.drop(columns="cfacshr")), "schema_column_missing"),
    (lambda i: replace(i, fund_quarterly=i.fund_quarterly.drop(columns="rdq")), "schema_column_missing"),
    (lambda i: replace(i, daily=pd.concat([i.daily, i.daily.iloc[[5]]], ignore_index=True)), "duplicate_key"),
    (lambda i: replace(i, fund_annual=pd.concat([i.fund_annual, i.fund_annual.iloc[[3]]], ignore_index=True)),
     "duplicate_key"),
    (lambda i: replace(i, fund_annual=edit(i.fund_annual, i.fund_annual.index == 4,
                                           known_date=pd.Timestamp("1990-01-01"))), "known_before_datadate"),
    (lambda i: replace(i, fund_quarterly=edit(i.fund_quarterly, i.fund_quarterly.index == 4,
                                              known_date=pd.Timestamp("1990-01-01"))), "known_before_datadate"),
    (lambda i: replace(i, daily=edit(i.daily, i.daily.index == 9, prc=-3.0)), "schema_value_invalid"),
    (lambda i: replace(i, daily=edit(i.daily, i.daily.index == 9, ret=np.inf)), "schema_value_invalid"),
    (lambda i: replace(i, ibes=pd.concat([i.ibes, i.ibes.iloc[[7]].assign(
        statpers=i.ibes["statpers"].iloc[7] + pd.Timedelta(days=1))], ignore_index=True)), "duplicate_key"),
    (lambda i: replace(i, members=pd.concat([i.members, i.members.iloc[[0]].assign(
        start=pd.Timestamp("1999-01-04"))], ignore_index=True)), "spell_invalid"),
    (lambda i: replace(i, link=i.link.assign(gvkey=[None, "G102", "G103", "G104", "G105"])), "schema_key_missing"),
])
def test_schema_violations_refuse(base: sig.SignalInputs, change, reason: str) -> None:
    with pytest.raises(RunnerStop) as stop:
        sig.build_signals(change(base), REBALANCES[:2])
    assert stop.value.reason == reason


def test_rebalance_rows_must_be_calendar_rows(base: sig.SignalInputs) -> None:
    for days in (pd.DatetimeIndex(["2000-07-29"]), pd.DatetimeIndex([CAL[0]]),
                 pd.DatetimeIndex(["2000-07-31", "2000-06-30"])):
        with pytest.raises(RunnerStop) as stop:
            sig.build_signals(base, days)
        assert stop.value.reason == "rebalance_invalid"
