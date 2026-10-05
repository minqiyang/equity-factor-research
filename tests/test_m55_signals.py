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


def ticker(p: int) -> str:
    return f"T{p}"


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
    ibes_link = pd.DataFrame({"ticker": [ticker(p) for p in PERMNOS], "permno": PERMNOS,
                              "sdate": pd.Timestamp("1990-01-01"), "edate": pd.NaT, "score": 0})
    ibes_link["edate"] = ibes_link["edate"].astype("datetime64[ns]")
    index_daily = pd.DataFrame({"date": CAL, "indno": sig.MARKET_INDNO, "ret": rng.normal(0.0004, 0.008, len(CAL))})
    annual, quarterly, ibes = [], [], []
    shares = {"revt": 0.8, "cogs": 0.5, "act": 0.4, "che": 0.1, "lct": 0.3, "dlc": 0.05, "txp": 0.01, "dp": 0.03,
              "seq": 0.4, "ceq": 0.38, "pstk": 0.02, "pstkrv": 0.02, "pstkl": 0.02, "txditc": 0.01, "lt": 0.6}
    for k, p in enumerate(PERMNOS):
        for n, year in enumerate(range(1992, 2002)):
            at = 100.0 * (1 + k) * 1.06 ** n * (1 + 0.02 * rng.standard_normal())
            datadate = pd.Timestamp(f"{year}-12-31")
            row = {"gvkey": gvkey(p), "datadate": datadate, "fyear": year, "known_date": datadate + pd.Timedelta(days=80),
                   "at": at}
            row.update({name: at * f * (1 + 0.05 * rng.standard_normal()) for name, f in shares.items()})
            annual.append(row)
        for datadate in pd.date_range("1992-03-31", "2002-09-30", freq="QE"):
            rdq = datadate + pd.Timedelta(days=25)
            quarterly.append({"gvkey": gvkey(p), "datadate": datadate, "fyearq": datadate.year,
                              "fqtr": datadate.quarter, "known_date": rdq + pd.Timedelta(days=5),
                              "epspxq": 1.0 + 0.1 * rng.standard_normal(), "ajexq": 1.0, "rdq": rdq})
        estimate = 2.0
        for month in pd.date_range("1994-01-01", "2002-12-01", freq="MS"):
            estimate += 0.02 * rng.standard_normal()
            statpers = month + pd.Timedelta(days=14)
            ibes.append({"ticker": ticker(p), "statpers": statpers, "fpedats": pd.Timestamp(f"{statpers.year}-12-31"),
                         "fpi": "1", "meanest": estimate})
    quarterly = pd.DataFrame(quarterly)
    announcements = quarterly[["gvkey", "datadate", "fyearq", "fqtr", "rdq"]].copy()
    return sig.SignalInputs(daily=daily, members=members, fund_annual=pd.DataFrame(annual), fund_quarterly=quarterly,
                            announcements=announcements, link=link, ibes_link=ibes_link, ibes=pd.DataFrame(ibes),
                            index_daily=index_daily)


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


def ibes_mask(inputs: sig.SignalInputs, p: int, statpers: str) -> pd.Series:
    return (inputs.ibes["ticker"] == ticker(p)) & (inputs.ibes["statpers"] == pd.Timestamp(statpers))


def quarter_mask(frame: pd.DataFrame, p: int, datadate: str) -> pd.Series:
    return (frame["gvkey"] == gvkey(p)) & (frame["datadate"] == pd.Timestamp(datadate))


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
    # S1: the yearly FY1 roll breaks one revision of three, so December fiscal-year firms stay valid all year.
    s1 = counts[counts["signal"] == "S1"]
    assert set(s1["reason"]) == {"valid"}

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
    """Change every row dated at or after r, and add revisions, links, and a member spell that start at r."""
    daily = inputs.daily.copy()
    late = daily["date"] >= r
    market = ["ret", "prc", "shrout", "cfacpr", "cfacshr"]
    daily.loc[late, market] = daily.loc[late, market] * 1.7
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
    quarterly.loc[late, "ajexq"] = 3.0
    quarterly.loc[late, "rdq"] = quarterly.loc[late, "rdq"] + pd.Timedelta(days=20)
    # A revision known at r of every quarter known before r, for every gvkey: new EPS, ajexq, and rdq.
    revision = quarterly[quarterly["known_date"] < r].copy()
    revision["known_date"] = r
    revision["epspxq"] = revision["epspxq"] * 3.0 + 1.0
    revision["ajexq"] = 2.0
    revision["rdq"] = revision["rdq"] - pd.Timedelta(days=3)
    quarterly = pd.concat([quarterly, revision], ignore_index=True)
    announcements = inputs.announcements.copy()
    late = announcements["rdq"] >= r
    announcements.loc[late, "rdq"] = announcements.loc[late, "rdq"] + pd.Timedelta(days=20)
    ibes = inputs.ibes.copy()
    late = ibes["statpers"] >= r
    ibes.loc[late, "meanest"] = ibes.loc[late, "meanest"] + 9.0
    ibes.loc[late, "fpedats"] = pd.Timestamp("2099-12-31")
    index_daily = inputs.index_daily.copy()
    index_daily.loc[index_daily["date"] >= r, "ret"] = index_daily.loc[index_daily["date"] >= r, "ret"] * 1.7
    # Links that start at r: a second gvkey for permno 102, and ticker T102 also on permno 103.
    link = pd.concat([inputs.link, inputs.link.iloc[[1]].assign(gvkey="G999", linkdt=r)], ignore_index=True)
    ibes_link = pd.concat([inputs.ibes_link, inputs.ibes_link.iloc[[1]].assign(permno=103, sdate=r)],
                          ignore_index=True)
    # A new member whose spell starts at r (R2: it is not a member at r).
    members = pd.concat([inputs.members, pd.DataFrame({"permno": [106], "start": [r], "end": [CAL[-1]]})],
                        ignore_index=True)
    return sig.SignalInputs(daily=daily, members=members, fund_annual=annual, fund_quarterly=quarterly,
                            announcements=announcements, link=link, ibes_link=ibes_link, ibes=ibes,
                            index_daily=index_daily)


@pytest.mark.parametrize("r", [R, pd.Timestamp("2001-03-30"), pd.Timestamp("2002-01-31")])
def test_future_perturbation_leaves_every_signal_bit_identical(base: sig.SignalInputs, base_result: dict,
                                                               r: pd.Timestamp) -> None:
    after = sig.build_signals(perturb_from(base, r), REBALANCES)
    upto = REBALANCES[REBALANCES <= r]
    assert not after["members"].loc[upto, 106].any()
    assert after["members"].loc[REBALANCES > r, 106].all()
    for s in sig.SIGNAL_IDS:
        assert_frame_equal(after["values"][s].loc[upto, PERMNOS], base_result["values"][s].loc[upto],
                           check_exact=True)
        assert_frame_equal(after["reasons"][s].loc[upto, PERMNOS], base_result["reasons"][s].loc[upto])
    later = REBALANCES[REBALANCES > r]
    if len(later):
        changed = [s for s in sig.SIGNAL_IDS
                   if not after["values"][s].loc[later, PERMNOS].equals(base_result["values"][s].loc[later])]
        assert set(changed) == set(sig.SIGNAL_IDS)


def test_positive_controls_at_the_latest_usable_row(base: sig.SignalInputs) -> None:
    """The same kind of change at the last row each rule admits changes the value; one row later it does not."""
    before = at_r(base)

    def changed(inputs: sig.SignalInputs) -> set[str]:
        after = at_r(inputs)
        return {s for s in sig.SIGNAL_IDS if after[s] != before[s]}

    # An annual record first known at r - 2 is usable at r; first known at r - 1 it is not, and the prior
    # fiscal year is the current one (S4, S5, S6, S8 change).
    fy1999 = annual_mask(base, 101, "1999-12-31")
    for known, expected in (("2000-07-27", set()), ("2000-07-28", {"S4", "S5", "S6", "S8"})):
        assert changed(replace(base, fund_annual=edit(base.fund_annual, fy1999, known_date=pd.Timestamp(known)))) \
            == expected

    # S2: a quarter reported and known at r - 2 is used at r; at r - 1 it is not.
    q2 = quarter_mask(base.fund_quarterly, 101, "2000-06-30")
    for day, expected in (("2000-07-27", {"S2"}), ("2000-07-28", set())):
        quarterly = edit(base.fund_quarterly, q2, rdq=pd.Timestamp(day), known_date=pd.Timestamp(day))
        assert changed(replace(base, fund_quarterly=quarterly)) == expected

    # S3: usable from rdq + 2 trading days, so the last admitted report date is r - 3; the day +1 return is r - 2.
    a2 = quarter_mask(base.announcements, 101, "2000-06-30")
    s3_inputs = replace(base, announcements=edit(base.announcements, a2, rdq=pd.Timestamp("2000-07-26")))
    s3_before = at_r(s3_inputs)["S3"]
    assert isinstance(s3_before, float)
    for day, moves in (("2000-07-27", True), ("2000-07-28", False)):
        bumped = replace(s3_inputs, daily=edit(base.daily, daily_mask(base, 101, day), ret=0.05))
        assert (at_r(bumped)["S3"] != s3_before) == moves
        index = edit(base.index_daily, base.index_daily["date"] == pd.Timestamp(day), ret=0.05)
        assert (at_r(replace(s3_inputs, index_daily=index))["S3"] != s3_before) == moves
    # Reported at r - 2, the quarter is not usable yet; S3 uses the previous announcement.
    late = replace(base, announcements=edit(base.announcements, a2, rdq=pd.Timestamp("2000-07-27")))
    assert at_r(late)["S3"] == at_r(replace(base, announcements=base.announcements[~a2]))["S3"]

    # S1: the June statistics date is usable from the June month end; the July one (before r) waits for 2000-07-31.
    june, july = ibes_mask(base, 101, "2000-06-15"), ibes_mask(base, 101, "2000-07-15")
    assert changed(replace(base, ibes=edit(base.ibes, june, meanest=7.0))) == {"S1"}
    assert changed(replace(base, ibes=edit(base.ibes, july, meanest=7.0))) == set()

    # S7 and S8 read shares at the month end before t's month, not at r - 2.
    assert changed(replace(base, daily=edit(base.daily, daily_mask(base, 101, A), shrout=1300.0))) == {"S7", "S8"}
    assert changed(replace(base, daily=edit(base.daily, daily_mask(base, 101, "2000-07-27"), shrout=1300.0))) \
        == set()


def test_s2_report_date_gate_alone(base: sig.SignalInputs) -> None:
    """Killing test for the rdq + 1 gate: the quarter is first known well before rdq, so only rdq decides."""
    q2 = quarter_mask(base.fund_quarterly, 101, "2000-06-30")
    used = edit(base.fund_quarterly, q2, known_date=pd.Timestamp("2000-07-05"), rdq=pd.Timestamp("2000-07-27"))
    used_s2 = at_r(replace(base, fund_quarterly=used))["S2"]
    assert isinstance(used_s2, float) and used_s2 != at_r(base)["S2"]          # rdq = r - 2: the quarter is read
    waiting = edit(used, q2, rdq=pd.Timestamp("2000-07-28"))
    assert at_r(replace(base, fund_quarterly=waiting))["S2"] == "not_yet_known"   # rdq = r - 1: not yet


def test_s1_statistics_date_on_the_decision_row(base: sig.SignalInputs) -> None:
    """Killing test: a statistics date on the month-end row t is not usable at r = t + 1 (nor one on r)."""
    r = pd.Timestamp("2000-07-03")                       # t = 2000-06-30, a month-end row
    june = ibes_mask(base, 101, "2000-06-15")
    no_july = ~ibes_mask(base, 101, "2000-07-15")             # one FY1 row per month: room for a row on r

    def s1(statpers: str, meanest: float) -> float | str:
        ibes = edit(base.ibes, june, statpers=pd.Timestamp(statpers), meanest=meanest)[no_july]
        return sig.build_signals(replace(base, ibes=ibes), pd.DatetimeIndex([r]))["values"]["S1"].loc[r, 101]

    for day in ("2000-06-30", "2000-07-03"):
        assert s1(day, 7.0) == s1(day, 2.0)
    assert s1("2000-06-29", 7.0) != s1("2000-06-29", 2.0)      # one row earlier it is used


def test_membership_uses_the_decision_row(base: sig.SignalInputs) -> None:
    """Killing test (R2): members are the spells that cover t = r - 1, not r."""
    members = pd.concat([edit(base.members, base.members["permno"] == 105, end=T),
                         pd.DataFrame({"permno": [106, 107], "start": [R, T], "end": [CAL[-1], CAL[-1]]})],
                        ignore_index=True)
    got = sig.build_signals(replace(base, members=members), pd.DatetimeIndex([R]))["members"].loc[R]
    assert got[got].index.tolist() == [101, 102, 103, 104, 105, 107]     # 105 leaves after t; 106 joins at r
    leaves = edit(base.members, base.members["permno"] == 105, end=pd.Timestamp("2000-07-27"))
    got = sig.build_signals(replace(base, members=leaves), pd.DatetimeIndex([R]))["members"].loc[R]
    assert got[got].index.tolist() == [101, 102, 103, 104]


# First-reported values (R1) ----------------------------------------------------------------

def test_later_revisions_never_replace_first_reported_values(base: sig.SignalInputs) -> None:
    """Appending or changing later revisions leaves S2, S4, S5, S6, S8 bit-identical, before and after they are
    public."""
    days = pd.DatetimeIndex(["2000-07-31", "2000-10-31", "2001-03-30"])
    expected = sig.build_signals(base, days)
    fy = base.fund_annual[annual_mask(base, 101, "1999-12-31") | annual_mask(base, 101, "1998-12-31")].copy()
    revisions = []
    for known in ("2000-07-27", "2000-10-16"):
        rows = fy.assign(known_date=pd.Timestamp(known))
        rows[list(sig.ANNUAL_ITEMS)] = rows[list(sig.ANNUAL_ITEMS)] + 40.0
        revisions.append(rows)
    quarters = base.fund_quarterly[(base.fund_quarterly["gvkey"] == "G101")
                                   & (base.fund_quarterly["known_date"] < pd.Timestamp("2000-07-01"))]
    q_revision = quarters.assign(known_date=pd.Timestamp("2000-07-20"), epspxq=quarters["epspxq"] + 1.0,
                                 ajexq=2.0, rdq=quarters["rdq"] + pd.Timedelta(days=2))
    inputs = replace(base, fund_annual=pd.concat([base.fund_annual, *revisions], ignore_index=True),
                     fund_quarterly=pd.concat([base.fund_quarterly, q_revision], ignore_index=True))
    got = sig.build_signals(inputs, days)
    # Changing a revision that is already public changes nothing either.
    changed = inputs.fund_annual.copy()
    changed.loc[changed["known_date"] == pd.Timestamp("2000-07-27"), "revt"] = 1.0
    got_changed = sig.build_signals(replace(inputs, fund_annual=changed), days)
    for s in ("S2", "S4", "S5", "S6", "S8"):
        assert_frame_equal(got["values"][s], expected["values"][s], check_exact=True)
        assert_frame_equal(got_changed["values"][s], expected["values"][s], check_exact=True)


def test_first_non_missing_item_is_used_from_its_own_row(base: sig.SignalInputs) -> None:
    """An item missing in the first row and present in a revision is usable from that revision's row + 1."""
    first = edit(base.fund_annual, annual_mask(base, 101, "1999-12-31"), revt=np.nan)
    revision = base.fund_annual[annual_mask(base, 101, "1999-12-31")].assign(
        known_date=pd.Timestamp("2000-10-16"), revt=77.0, cogs=1.0)          # Monday; usable from 2000-10-17
    inputs = replace(base, fund_annual=pd.concat([first, revision], ignore_index=True))
    old = base.fund_annual[annual_mask(base, 101, "1999-12-31")].iloc[0]
    result = sig.build_signals(inputs, pd.DatetimeIndex(["2000-10-17", "2000-10-18"]))
    assert result["reasons"]["S4"][101].iloc[0] == "missing_item"
    assert result["values"]["S4"][101].iloc[1] == (77.0 - old["cogs"]) / old["at"]     # cogs stays first-reported


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
        quarterly.loc[quarter_mask(quarterly, 101, datadate), "epspxq"] = value
    # S3: the 2000Q2 announcement on 2000-07-25 (quarter end + 25 days); window 07-24 to 07-26.
    daily = base.daily.copy()
    index_daily = base.index_daily.copy()
    for day, stock, index in (("2000-07-24", 0.01, 0.002), ("2000-07-25", 0.02, 0.004), ("2000-07-26", -0.01, -0.002)):
        daily.loc[daily_mask(base, 101, day), "ret"] = stock
        index_daily.loc[index_daily["date"] == pd.Timestamp(day), "ret"] = index
    # S7 and S8: shares at A and A12; price at A.
    daily.loc[daily_mask(base, 101, A), ["prc", "shrout"]] = [25.0, 1100.0]
    daily.loc[daily_mask(base, 101, A12), "shrout"] = 1000.0
    # S1: March to June 2000 estimates, one FY1; prices at the March, April, and May month ends.
    ibes = base.ibes.copy()
    for statpers, value in (("2000-03-15", 2.0), ("2000-04-15", 2.1), ("2000-05-15", 2.1), ("2000-06-15", 2.3)):
        ibes.loc[ibes_mask(base, 101, statpers), "meanest"] = value
    for day, price in (("2000-03-31", 40.0), ("2000-04-28", 50.0), ("2000-05-31", 20.0)):
        daily.loc[daily_mask(base, 101, day), "prc"] = price
    return replace(base, daily=daily, fund_annual=annual, fund_quarterly=quarterly, ibes=ibes,
                   index_daily=index_daily)


S1_HAND = 3 * (0.1 / 40.0 + 0.0 / 50.0 + 0.2 / 20.0) / 3


def test_hand_computed_values(base: sig.SignalInputs) -> None:
    got = at_r(hand_inputs(base))
    assert got["S1"] == pytest.approx(S1_HAND, rel=1e-12)
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
    """A 2-for-1 split on 2000-05-01 halves the later estimates and prices; S1 does not change."""
    inputs = hand_inputs(base)
    daily = inputs.daily.copy()
    split = (daily["permno"] == 101) & (daily["date"] < pd.Timestamp("2000-05-01"))
    daily.loc[split, "cfacpr"] = 2.0                         # rows before the split: CRSP price factor 2
    daily.loc[daily_mask(base, 101, "2000-05-31"), "prc"] = 10.0
    ibes = inputs.ibes.copy()
    for statpers, value in (("2000-05-15", 1.05), ("2000-06-15", 1.15)):
        ibes.loc[ibes_mask(base, 101, statpers), "meanest"] = value
    assert at_r(replace(inputs, daily=daily, ibes=ibes))["S1"] == pytest.approx(S1_HAND, rel=1e-12)


def test_s1_stays_valid_through_the_fiscal_year_roll(base: sig.SignalInputs) -> None:
    """At 2001-02-28 the January revision crosses the FY1 roll; the November and December revisions give S1."""
    ibes, daily = base.ibes.copy(), base.daily.copy()
    for statpers, value in (("2000-10-15", 2.0), ("2000-11-15", 2.1), ("2000-12-15", 2.4), ("2001-01-15", 1.0)):
        ibes.loc[ibes_mask(base, 101, statpers), "meanest"] = value
    for day, price in (("2000-10-31", 40.0), ("2000-11-30", 30.0)):
        daily.loc[daily_mask(base, 101, day), "prc"] = price
    day = pd.Timestamp("2001-02-28")
    result = sig.build_signals(replace(base, ibes=ibes, daily=daily), pd.DatetimeIndex([day]))
    assert result["values"]["S1"].loc[day, 101] == pytest.approx(3 * (0.1 / 40.0 + 0.3 / 30.0) / 2, rel=1e-12)


def test_s1_needs_two_valid_revisions(base: sig.SignalInputs) -> None:
    ibes = base.ibes.copy()
    for statpers, fpe in (("2000-05-15", "2001-06-30"), ("2000-06-15", "2001-12-31")):   # two rolls in three months
        ibes.loc[ibes_mask(base, 101, statpers), "fpedats"] = pd.Timestamp(fpe)
    assert at_r(replace(base, ibes=ibes))["S1"] == "fpe_changed"
    gone = ibes_mask(base, 101, "2000-03-15") | ibes_mask(base, 101, "2000-04-15")
    assert at_r(replace(base, ibes=base.ibes[~gone]))["S1"] == "short_history"
    one_nan = edit(base.ibes, ibes_mask(base, 101, "2000-04-15"), meanest=np.nan)
    assert isinstance(at_r(replace(base, ibes=one_nan))["S1"], str)       # Apr NaN breaks two revisions


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
        quarterly.loc[quarter_mask(quarterly, 101, datadate), "epspxq"] = np.nan
    assert at_r(replace(base, fund_quarterly=quarterly))["S2"] == "short_history"


def test_s2_split_between_known_dates_matches_the_no_split_world(base: sig.SignalInputs) -> None:
    """A 2-for-1 split on 1999-07-01, between the known dates of q - 4 (1999-04-30) and q (2000-04-30).

    First-known rows carry the basis of their own date: quarters known before the split keep pre-split EPS and
    ajexq 1; quarters known after it report post-split EPS (half) and ajexq 1. The CRSP factor ratio puts every
    EPS on the basis of t, so S2 equals the no-split value.
    """
    inputs = hand_inputs(base)
    split = pd.Timestamp("1999-07-01")
    daily = edit(inputs.daily, (inputs.daily["permno"] == 101) & (inputs.daily["date"] < split), cfacpr=2.0)
    q = inputs.fund_quarterly
    after = (q["gvkey"] == "G101") & (q["known_date"] >= split)
    quarterly = edit(q, after, epspxq=q.loc[after, "epspxq"] / 2.0)
    assert at_r(replace(inputs, daily=daily, fund_quarterly=quarterly))["S2"] == pytest.approx(at_r(inputs)["S2"],
                                                                                                 rel=1e-12)
    # Without the factor ratio the bases mix and S2 changes (the defect of round 1).
    assert at_r(replace(inputs, fund_quarterly=quarterly))["S2"] != pytest.approx(at_r(inputs)["S2"], rel=1e-3)
    missing = edit(inputs.fund_quarterly, quarter_mask(q, 101, "2000-03-31"), ajexq=np.nan)
    assert at_r(replace(inputs, fund_quarterly=missing))["S2"] == "missing_item"
    zero = edit(inputs.fund_quarterly, quarter_mask(q, 101, "2000-03-31"), ajexq=0.0)
    assert at_r(replace(inputs, fund_quarterly=zero))["S2"] == "invalid_value"
    no_factor = edit(inputs.daily, daily_mask(base, 101, "1999-04-30"), cfacpr=np.nan)   # q - 4 known date
    assert at_r(replace(inputs, daily=no_factor))["S2"] == "missing_item"


def test_split_after_the_decision_row_rescales_both_factors(base: sig.SignalInputs) -> None:
    """A 3-for-1 split on 2000-08-15, after t, multiplies every earlier CRSP factor by 3.

    This is the only perturbation test that is not bit-identical: S1, S2, and S7 read ratios of two factors,
    and the factor scaling can move the last bit, so it checks equality within 1e-12 relative.
    """
    inputs = hand_inputs(base)
    before = inputs.daily["date"] < pd.Timestamp("2000-08-15")
    daily = inputs.daily.copy()
    daily.loc[before, ["cfacpr", "cfacshr"]] = daily.loc[before, ["cfacpr", "cfacshr"]] * 3.0
    daily.loc[~before, "prc"] = daily.loc[~before, "prc"] / 3.0
    daily.loc[~before, "shrout"] = daily.loc[~before, "shrout"] * 3.0
    got, expected = at_r(replace(inputs, daily=daily)), at_r(inputs)
    for s in sig.SIGNAL_IDS:
        assert got[s] == pytest.approx(expected[s], rel=1e-12), s


def test_s2_reads_only_quarters_whose_report_date_is_usable(base: sig.SignalInputs) -> None:
    """GPT-R1-M2: q, q - 4, and the denominator quarters each need first row + 1 and rdq + 1 at or before t."""
    inputs = hand_inputs(base)
    q = inputs.fund_quarterly
    # q - 4 (1999Q1) with a report date after t: not read, so S2 has no value; its EPS cannot move anything.
    late = edit(q, quarter_mask(q, 101, "1999-03-31"), rdq=pd.Timestamp("2001-01-02"))
    assert at_r(replace(inputs, fund_quarterly=late))["S2"] == "not_yet_known"
    no_rdq = edit(q, quarter_mask(q, 101, "1999-03-31"), rdq=pd.NaT)
    assert at_r(replace(inputs, fund_quarterly=no_rdq))["S2"] == "missing_item"
    # A denominator quarter (1998Q1) with a late or missing rdq drops differences k = 4 and k = 8; six stay valid.
    six = 0.1 / statistics.stdev([0.08, 0.07, 0.06, 0.04, 0.03, 0.02])
    for rdq in (pd.Timestamp("2001-01-02"), pd.NaT):
        dropped = edit(q, quarter_mask(q, 101, "1998-03-31"), rdq=rdq)
        assert at_r(replace(inputs, fund_quarterly=dropped))["S2"] == pytest.approx(six, rel=1e-12)
        moved = edit(dropped, quarter_mask(q, 101, "1998-03-31"), epspxq=9.0)
        assert at_r(replace(inputs, fund_quarterly=moved))["S2"] == pytest.approx(six, rel=1e-12)
    # The current quarter's rdq is read as known at t: one filled in by a revision after t is missing at t.
    blank = edit(q, quarter_mask(q, 101, "2000-03-31"), rdq=pd.NaT)
    fill = q[quarter_mask(q, 101, "2000-03-31")].assign(known_date=pd.Timestamp("2000-10-02"),
                                                         rdq=pd.Timestamp("1999-01-04"))
    assert at_r(replace(inputs, fund_quarterly=pd.concat([blank, fill], ignore_index=True)))["S2"] == "missing_item"
    # The first row decides too: a quarter first known after t is not read even when its rdq is old.
    unknown = edit(q, quarter_mask(q, 101, "1998-03-31"), known_date=pd.Timestamp("2001-01-02"))
    assert at_r(replace(inputs, fund_quarterly=unknown))["S2"] == pytest.approx(six, rel=1e-12)


def test_fiscal_keys_match_years_and_quarters(base: sig.SignalInputs) -> None:
    """A fiscal year-end change moves datadate to another month; the fiscal keys still match the prior period."""
    before = at_r(base)
    annual = edit(base.fund_annual, annual_mask(base, 101, "1999-12-31"), datadate=pd.Timestamp("1999-11-30"))
    assert at_r(replace(base, fund_annual=annual))["S6"] == before["S6"]
    q1 = quarter_mask(base.fund_quarterly, 101, "2000-03-31")
    quarterly = edit(base.fund_quarterly, q1, datadate=pd.Timestamp("2000-02-29"))
    assert at_r(replace(base, fund_quarterly=quarterly))["S2"] == before["S2"]


def test_s5_missing_item_share_by_year(base: sig.SignalInputs) -> None:
    txp = edit(base.fund_annual, annual_mask(base, 104, "1999-12-31"), txp=np.nan)
    share = sig.reason_share(sig.build_signals(replace(base, fund_annual=txp), REBALANCES), "S5", "missing_item")
    assert share.loc[1999] == 0.0
    # FY1999 is the current year from 2000-07 to 2001-06 and the prior year from 2001-07 to 2001-12.
    assert share.loc[2000] == pytest.approx(6 / 60) and share.loc[2001] == pytest.approx(12 / 54)


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
    q, a = base.fund_quarterly, base.announcements
    keep_q = ~((q["gvkey"] == "G101") & (q["datadate"] > pd.Timestamp("1999-12-31")))
    keep_a = ~((a["gvkey"] == "G101") & (a["datadate"] > pd.Timestamp("1999-12-31")))
    for rdq, valid in (("2000-01-28", True), ("2000-01-27", False)):
        quarterly = edit(q[keep_q], quarter_mask(q, 101, "1999-12-31")[keep_q], rdq=pd.Timestamp(rdq),
                         known_date=pd.Timestamp(rdq))
        announcements = edit(a[keep_a], quarter_mask(a, 101, "1999-12-31")[keep_a], rdq=pd.Timestamp(rdq))
        got = at_r(replace(base, fund_quarterly=quarterly, announcements=announcements))
        for s in ("S2", "S3"):
            assert isinstance(got[s], float) if valid else got[s] == "stale"


def test_max_age_ibes(base: sig.SignalInputs) -> None:
    """S1 uses a statistics date of t - 2 months; one day earlier it is stale."""
    ibes = base.ibes
    keep = ~((ibes["ticker"] == "T101") & (ibes["statpers"] > pd.Timestamp("2000-05-31")))
    may = ibes_mask(base, 101, "2000-05-15")[keep]
    for statpers, valid in (("2000-05-28", True), ("2000-05-27", False)):
        got = at_r(replace(base, ibes=edit(ibes[keep], may, statpers=pd.Timestamp(statpers))))["S1"]
        assert isinstance(got, float) if valid else got == "stale"


def test_absent_anchor_row_is_never_filled(base: sig.SignalInputs) -> None:
    """GPT-R1-M3: an absent month-end anchor row is no_market_data; a present row with NaN is missing_item."""
    inputs = hand_inputs(base)
    gone = inputs.daily[~daily_mask(base, 101, A)]
    got = at_r(replace(inputs, daily=gone))
    assert got["S7"] == "no_market_data" and got["S8"] == "no_market_data"
    nan = edit(inputs.daily, daily_mask(base, 101, A), prc=np.nan, shrout=np.nan)
    got = at_r(replace(inputs, daily=nan))
    assert got["S7"] == "missing_item" and got["S8"] == "missing_item"
    # The 12-month anchor: an absent row in a trading history is no_market_data; no history there is short.
    assert at_r(replace(inputs, daily=inputs.daily[~daily_mask(base, 101, A12)]))["S7"] == "no_market_data"
    young = inputs.daily[~((inputs.daily["permno"] == 101) & (inputs.daily["date"] <= A12))]
    assert at_r(replace(inputs, daily=young))["S7"] == "short_history"
    # S1 price at the May month end (June revision): absent or NaN types that revision, not a filled price.
    may = daily_mask(base, 101, "2000-05-31")
    two = 3 * (0.0 / 50.0 + 0.1 / 40.0) / 2
    assert at_r(replace(inputs, daily=inputs.daily[~may]))["S1"] == pytest.approx(two, rel=1e-12)
    assert at_r(replace(inputs, daily=edit(inputs.daily, may, prc=np.nan)))["S1"] == pytest.approx(two, rel=1e-12)
    # A member near exit: permno 105 leaves on 2001-06-29; its 2001-05-31 anchor row is absent.
    day = pd.Timestamp("2001-06-29")
    near = sig.build_signals(replace(base, daily=base.daily[~daily_mask(base, 105, "2001-05-31")]),
                             pd.DatetimeIndex([day]))
    assert near["reasons"]["S7"].loc[day, 105] == "no_market_data"
    assert near["reasons"]["S8"].loc[day, 105] == "no_market_data"


def test_s1_split_factor_maximum_age(base: sig.SignalInputs) -> None:
    """The factor at the March 15 statistics date comes from a row at most one month old (2000-02-15)."""
    inputs = hand_inputs(base)
    two = 3 * (0.0 / 50.0 + 0.2 / 20.0) / 2                  # the April revision drops out
    for last_row, expected in (("2000-02-15", S1_HAND), ("2000-02-14", two)):
        gone = (inputs.daily["permno"] == 101) & (inputs.daily["date"] > pd.Timestamp(last_row)) \
            & (inputs.daily["date"] <= pd.Timestamp("2000-03-15"))
        assert at_r(replace(inputs, daily=inputs.daily[~gone]))["S1"] == pytest.approx(expected, rel=1e-12)


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


def ibes_row(ticker_: str, permno: int, sdate: str, edate: str | None = None, score: int = 0) -> pd.DataFrame:
    return pd.DataFrame({"ticker": [ticker_], "permno": [permno], "sdate": [pd.Timestamp(sdate)],
                         "edate": [pd.Timestamp(edate) if edate else pd.NaT], "score": [score]}).astype(
        {"edate": "datetime64[ns]"})


def test_ibes_link_score_and_ambiguity(base: sig.SignalInputs, base_result: dict) -> None:
    others = [p for p in PERMNOS if p != 102]
    # A score above IBES_LINK_MAX_SCORE is no link; it touches only that member and only S1.
    weak = edit(base.ibes_link, base.ibes_link["permno"] == 102, score=2)
    result = sig.build_signals(replace(base, ibes_link=weak), REBALANCES)
    assert (result["reasons"]["S1"][102] == "no_link").all()
    assert_frame_equal(result["values"]["S1"][others], base_result["values"]["S1"][others], check_exact=True)
    for s in sig.SIGNAL_IDS[1:]:
        assert_frame_equal(result["values"][s], base_result["values"][s], check_exact=True)
    accepted = edit(base.ibes_link, base.ibes_link["permno"] == 102, score=1)
    assert_frame_equal(sig.build_signals(replace(base, ibes_link=accepted), REBALANCES)["values"]["S1"],
                       base_result["values"]["S1"], check_exact=True)
    # One ticker on two PERMNOs at the statistics dates: both are ambiguous.
    shared = pd.concat([base.ibes_link, ibes_row("T103", 104, "1990-01-01")], ignore_index=True)
    assert at_r(replace(base, ibes_link=shared), permno=103)["S1"] == "ambiguous_link"
    assert at_r(replace(base, ibes_link=shared), permno=104)["S1"] == "ambiguous_link"
    # One PERMNO with two tickers at the statistics dates: ambiguous, even when the second ticker has no rows.
    two = pd.concat([base.ibes_link, ibes_row("T999", 103, "1990-01-01")], ignore_index=True)
    assert at_r(replace(base, ibes_link=two), permno=103)["S1"] == "ambiguous_link"
    # Two rows of one PERMNO in one statistics month (two tickers on adjacent link dates): ambiguous.
    adjacent = pd.concat([edit(base.ibes_link, base.ibes_link["permno"] == 103, edate=pd.Timestamp("2000-06-10")),
                          ibes_row("T999", 103, "2000-06-11")], ignore_index=True)
    june = ibes_mask(base, 103, "2000-06-15")
    rows = pd.concat([edit(base.ibes, june, statpers=pd.Timestamp("2000-06-05")),
                      base.ibes[june].assign(ticker="T999", statpers=pd.Timestamp("2000-06-20"))], ignore_index=True)
    one = pd.concat([edit(base.ibes, june, statpers=pd.Timestamp("2000-06-05"))], ignore_index=True)
    assert at_r(replace(base, ibes_link=adjacent, ibes=one), permno=103)["S1"] == at_r(base, permno=103)["S1"]
    assert at_r(replace(base, ibes_link=adjacent, ibes=rows), permno=103)["S1"] != at_r(base, permno=103)["S1"]
    # The same pair on two overlapping rows is not ambiguous.
    again = pd.concat([base.ibes_link, ibes_row("T103", 103, "1999-01-04")], ignore_index=True)
    assert at_r(replace(base, ibes_link=again), permno=103) == at_r(base, permno=103)
    # No link row is no_link; a link that ended before the last three statistics months leaves only old rows.
    assert at_r(replace(base, ibes_link=base.ibes_link[base.ibes_link["permno"] != 104]), permno=104)["S1"] \
        == "no_link"
    ended = edit(base.ibes_link, base.ibes_link["permno"] == 104, edate=pd.Timestamp("2000-04-30"))
    assert at_r(replace(base, ibes_link=ended), permno=104)["S1"] == "stale"


def test_ibes_ticker_reuse_never_crosses_permnos(base: sig.SignalInputs) -> None:
    """GPT-R1-M1: T101 is PERMNO 101 to 2000-04-30 and PERMNO 102 from 2000-05-01; no estimate crosses."""
    inputs = hand_inputs(base)
    link = edit(inputs.ibes_link, inputs.ibes_link["permno"].isin([101, 102]), edate=pd.Timestamp("2000-04-30"))
    link = pd.concat([link, ibes_row("T101", 102, "2000-05-01")], ignore_index=True)
    reused = replace(inputs, ibes_link=link)
    got = at_r(reused, permno=102)
    assert isinstance(got["S1"], float)
    # Changing an estimate that belongs to PERMNO 101 (T101 in March) has no effect on PERMNO 102.
    old = edit(inputs.ibes, ibes_mask(base, 101, "2000-03-15"), meanest=200.0)
    assert at_r(replace(reused, ibes=old), permno=102)["S1"] == got["S1"]
    # PERMNO 102 reads T102 to April and T101 from May; its April-to-May revision uses the May T101 row.
    new = edit(inputs.ibes, ibes_mask(base, 101, "2000-05-15"), meanest=200.0)
    assert at_r(replace(reused, ibes=new), permno=102)["S1"] != got["S1"]
    # PERMNO 101 has no row after April: its latest statistics date is too old.
    assert at_r(reused, permno=101)["S1"] == "stale"


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


def test_boundary_s7_lag_is_twelve_months(base: sig.SignalInputs) -> None:
    """S7 reads A12 = 1999-06-30, not the month end 11 or 13 months before A."""
    inputs = hand_inputs(base)
    for day, shares in (("1999-07-30", 1050.0), ("1999-05-28", 900.0)):
        inputs = replace(inputs, daily=edit(inputs.daily, daily_mask(base, 101, day), shrout=shares))
    assert at_r(inputs)["S7"] == pytest.approx(math.log(1.1), rel=1e-12)


def test_boundary_s2_needs_six_valid_differences(base: sig.SignalInputs) -> None:
    """Missing EPS of 1997Q1 and 1997Q2 drops differences k = 8 and k = 7 (six stay); 1997Q3 too leaves five."""
    inputs = hand_inputs(base)
    q = inputs.fund_quarterly
    for datadate in ("1997-03-31", "1997-06-30"):
        q = edit(q, quarter_mask(q, 101, datadate), epspxq=np.nan)
    assert at_r(replace(inputs, fund_quarterly=q))["S2"] == pytest.approx(
        0.1 / statistics.stdev([0.03, 0.04, 0.05, 0.06, 0.07, 0.08]), rel=1e-12)
    q = edit(q, quarter_mask(q, 101, "1997-09-30"), epspxq=np.nan)
    assert at_r(replace(inputs, fund_quarterly=q))["S2"] == "short_history"


def test_boundary_s2_backfill_of_eight_quarters(base: sig.SignalInputs) -> None:
    """With q's EPS missing, eight known quarters give missing_item and seven give short_history.

    The six-difference rule needs at least 11 quarters for a value, so only the reason can show this rule.
    """
    q = base.fund_quarterly
    g101 = q["gvkey"] == "G101"
    for first, expected in (("1998-06-30", "missing_item"), ("1998-09-30", "short_history")):
        kept = q[~(g101 & (q["datadate"] < pd.Timestamp(first)))]
        kept = edit(kept, quarter_mask(kept, 101, "2000-03-31"), epspxq=np.nan)
        assert at_r(replace(base, fund_quarterly=kept))["S2"] == expected


def test_boundary_s3_backfill_of_eight_announcements(base: sig.SignalInputs) -> None:
    a = base.announcements
    g101 = a["gvkey"] == "G101"
    for first, valid in (("1998-09-30", True), ("1998-12-31", False)):
        kept = a[~(g101 & (a["datadate"] < pd.Timestamp(first)))]
        got = at_r(replace(base, announcements=kept))["S3"]
        assert isinstance(got, float) if valid else got == "short_history"


def test_boundary_annual_lag_must_be_known(base: sig.SignalInputs) -> None:
    """The prior fiscal year first known after t is no lag: S5 and S6 are short_history, S4 stays valid."""
    annual = edit(base.fund_annual, annual_mask(base, 101, "1998-12-31"), known_date=pd.Timestamp("2001-01-02"))
    got = at_r(replace(base, fund_annual=annual))
    assert got["S5"] == "short_history" and got["S6"] == "short_history" and isinstance(got["S4"], float)


def test_s8_market_data_before_book_equity(base: sig.SignalInputs) -> None:
    """A-4: with both an absent anchor and a non-positive book equity, the market reason wins."""
    inputs = hand_inputs(base)
    annual = edit(inputs.fund_annual, annual_mask(base, 101, "1999-12-31"), seq=2.0, txditc=0.0)
    gone = inputs.daily[~daily_mask(base, 101, A)]
    assert at_r(replace(inputs, fund_annual=annual, daily=gone))["S8"] == "no_market_data"


def test_annual_value_waits_six_months_after_fiscal_end(base: sig.SignalInputs) -> None:
    days = pd.DatetimeIndex(["2000-06-30", "2000-07-03"])   # decision rows 2000-06-29 and 2000-06-30
    s6 = sig.build_signals(base, days)["values"]["S6"][101]
    at = base.fund_annual.set_index(["gvkey", "datadate"])["at"]
    assert s6.iloc[0] == at[("G101", pd.Timestamp("1998-12-31"))] / at[("G101", pd.Timestamp("1997-12-31"))] - 1
    assert s6.iloc[1] == at[("G101", pd.Timestamp("1999-12-31"))] / at[("G101", pd.Timestamp("1998-12-31"))] - 1


# Universe return and coverage -----------------------------------------------------------

def test_missing_index_return_gives_no_market_data(base: sig.SignalInputs) -> None:
    inputs = hand_inputs(base)
    day = inputs.index_daily["date"] == pd.Timestamp("2000-07-25")
    assert at_r(replace(inputs, index_daily=edit(inputs.index_daily, day, ret=np.nan)))["S3"] == "no_market_data"
    assert at_r(replace(inputs, index_daily=inputs.index_daily[~day]))["S3"] == "no_market_data"
    # Another member's missing return does not touch S3 of permno 101.
    daily = edit(inputs.daily, daily_mask(base, 104, "2000-07-25"), ret=np.nan)
    assert at_r(replace(inputs, daily=daily))["S3"] == at_r(inputs)["S3"]
    assert at_r(replace(inputs, daily=daily), permno=104)["S3"] == "no_market_data"


def coverage_panels(invalid: dict[pd.Timestamp, int], members: int = 10, start: str = "1990-01-31",
                    end: str = "1992-12-31") -> tuple[pd.DataFrame, pd.DataFrame]:
    index = pd.DatetimeIndex(pd.date_range(start, end, freq="ME"), name="date")
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


def test_real_start_needs_complete_years() -> None:
    """GPT-R1-M4: a year counts only with all twelve months present and passing."""
    def start(drop: list[str], first: str = "1990-01-31", last: str = "1992-12-31") -> int | None:
        reasons, members = coverage_panels({}, start=first, end=last)
        keep = ~reasons.index.isin(pd.DatetimeIndex(drop))
        return sig.real_start(reasons[keep], members[keep])

    assert start([]) == 1990
    assert start([], first="1989-07-31") == 1990               # a partial first year never counts
    assert start(["1990-06-30"]) == 1991                         # an absent month fails its year
    assert start([str(d.date()) for d in pd.date_range("1991-01-31", "1991-12-31", freq="ME")]) == 1992   # no 1991
    assert start([], last="1992-11-30") is None                  # a partial last year never counts
    assert start([], first="1990-01-31", last="1990-12-31") == 1990
    assert start([], first="1990-02-28", last="1990-12-31") is None


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
    (lambda i: replace(i, announcements=i.announcements.drop(columns="fqtr")), "schema_column_missing"),
    (lambda i: replace(i, index_daily=i.index_daily.drop(columns="ret")), "schema_column_missing"),
    (lambda i: replace(i, ibes_link=i.ibes_link.drop(columns="score")), "schema_column_missing"),
    (lambda i: replace(i, fund_quarterly=i.fund_quarterly.drop(columns="ajexq")), "schema_column_missing"),
    (lambda i: replace(i, index_daily=pd.concat([i.index_daily, i.index_daily.iloc[[3]]], ignore_index=True)),
     "duplicate_key"),
    (lambda i: replace(i, ibes_link=edit(i.ibes_link, i.ibes_link.index == 2, edate=pd.Timestamp("1989-01-01"))),
     "link_invalid"),
    (lambda i: replace(i, ibes=i.ibes.assign(fpi=1.0)), "schema_value_invalid"),
    (lambda i: replace(i, ibes=i.ibes.assign(fpi=1)), "schema_value_invalid"),
    (lambda i: replace(i, index_daily=edit(i.index_daily, i.index_daily.index == 5, date=pd.Timestamp("1995-01-07"))),
     "schema_date_invalid"),
    (lambda i: replace(i, index_daily=i.index_daily.assign(indno=1000500)), "schema_value_invalid"),
    (lambda i: replace(i, fund_annual=edit(i.fund_annual, i.fund_annual.index == 4, fyear=1995)),
     "fiscal_key_invalid"),
    (lambda i: replace(i, fund_quarterly=edit(i.fund_quarterly, i.fund_quarterly.index == 4, fqtr=5)),
     "fiscal_key_invalid"),
    (lambda i: replace(i, announcements=i.announcements.assign(
        fyearq=i.announcements["fyearq"].astype(float).where(i.announcements.index != 4, 1993.5))),
     "fiscal_key_invalid"),
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
