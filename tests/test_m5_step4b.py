"""Milestone 5 step 4b (amendment 5 revision 2): the required tests on synthetic fixtures.

Every fixture is synthetic (``tests/m5_step4_support.py`` for the books, ``tests/m5_step4b_support.py`` for
companyfacts and the CIK map). No test reads a snapshot row, the SEC cache, or the network.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import m5_step4_support as fx
import m5_step4b_support as fb
import research.m4_7_sp500_pit_rerun as runner
import research.m5_factor_baseline as base
import research.m5_sec_identity as ident
import research.m5_sec_signals as sig
import research.m5_step3 as step3
import research.m5_step4 as s4
import research.m5_step4b as s4b
import research.m5_step4b_data as dm
from data.public_factors import PublicDataRefusal
from data.sec_edgar import COMPANYFACTS_URL


pytestmark = pytest.mark.xdist_group("m5_step4b")
REPO_ROOT = Path(__file__).resolve().parents[1]
# The step 4 synthetic summary before the step 4b parameterization (base `aad02a0`), as sorted JSON text, and the
# step 4 report rendered from that stored document. The regression test compares the recomputed summary with it.
STEP4_GOLDEN = Path(__file__).resolve().parent / "fixtures" / "m5_step4_synthetic_summary.json"
STEP4_JSON_SHA256 = "8868e0175dfeb9fa5821b970f5b0164f12bd524ce4e3cf947b5441f49ba34af5"
STEP4_GOLDEN_MD_SHA256 = "9b5c0512502cd56c2b01caefcb1db41e22de2b41ff84a504540f1190599a5b96"
REL_TOL, ABS_TOL = 1e-9, 1e-12       # 1-ulp input noise moves the summary by at most 4.6e-11 relative


@pytest.fixture(scope="module")
def chain():
    segments = fx.prepared()
    public = fb.public9()
    sec = fb.sec_inputs()
    result4 = s4.evaluate(segments, public, {fx.STOP_ASSET}, None)
    committed = s4b.step4_document(result4, segments, None)
    result = s4b.evaluate(segments, public, sec, committed, {fx.STOP_ASSET}, None, expected_months=None,
                          step4_result=result4)
    return {"segments": segments, "public": public, "sec": sec, "result4": result4, "committed": committed,
            "result": result, "doc": s4b.summarize(result)}


def _cf(doc: dict) -> sig.CompanyFacts:
    return sig.parse_companyfacts(doc)


def _value(doc: dict, signal: str, day: str, prices=None, column: int = 0, row: int = 0):
    cf = _cf(doc)
    return sig.signal_value(signal, sig.fundamentals(cf, day)[signal], day, prices, column, row)


def _flat_prices(close: float = 20.0, n: int = 40, start: str = "2012-01-02", factor: np.ndarray | None = None):
    calendar = pd.bdate_range(start, periods=n)
    split = np.ones((n, 1)) if factor is None else factor.reshape(n, 1)
    return sig.PricePanel(calendar, pd.Index(["X"]), np.full((n, 1), close), split)


def _gp_doc(**concepts):
    """A company with SE, Assets, NI at FY2011 and the named GP components."""
    a = fb.accn(9, 2012)
    start, end = fb.fy(2011)
    gaap = {sig.SE: {"USD": [fb.fact(100.0, end, "2012-03-01", a)]},
            sig.ASSETS: {"USD": [fb.fact(400.0, end, "2012-03-01", a)]},
            sig.NI: {"USD": [fb.fact(10.0, end, "2012-03-01", a, start=start)]}}
    for concept, facts in concepts.items():
        gaap[concept] = {"USD": facts}
    return fb.document(gaap, [fb.fact(50.0, "2012-02-20", "2012-03-01", a)])


# ---------------------------------------------------------------- future perturbation (required test 1)

def test_future_perturbation_filing_and_prices(chain):
    seg = chain["segments"]["pre"]
    r = int(seg.schedule.evaluation_resets[16])
    day = seg.calendar[r - 1]
    asset = fx.ASSETS[12]
    col = list(seg.prices.columns).index(asset)
    year = day.year - 1                                   # the fiscal year normally filed in March of ``day.year``
    base_value = s4b.sec_panels(seg, chain["sec"]).signals[sig.BM].iloc[r - 1, col]
    on_day = fb.sec_inputs({asset: fb.company(asset, {year: day.date().isoformat()})})
    before = fb.sec_inputs({asset: fb.company(asset, {year: (day - pd.Timedelta(days=1)).date().isoformat()})})
    late = fb.sec_inputs({asset: fb.company(asset, {year: (day + pd.Timedelta(days=30)).date().isoformat()})})
    on_value = s4b.sec_panels(seg, on_day).signals[sig.BM].iloc[r - 1, col]
    late_value = s4b.sec_panels(seg, late).signals[sig.BM].iloc[r - 1, col]
    before_value = s4b.sec_panels(seg, before).signals[sig.BM].iloc[r - 1, col]
    assert on_value == late_value                          # filed on date(r - 1) or later: not yet usable
    assert before_value != on_value                        # filed the calendar day before: usable
    assert np.isfinite(base_value)
    # A price change after row r - 1 leaves the SEC signal row and the target at r unchanged.
    paths = fx.vendor_paths()
    shocked = {k: v.copy() for k, v in paths.items()}
    for field in ("open", "high", "low", "close", "adjusted_close"):
        shocked[field].iloc[r:] = shocked[field].iloc[r:] * 1.7
    later = fx.prepared(shocked)["pre"]
    a = s4b.sec_panels(seg, chain["sec"]).signals
    b = s4b.sec_panels(later, chain["sec"]).signals
    held = []
    for s, panels in ((seg, a), (later, b)):
        np.testing.assert_array_equal(a[sig.EP].iloc[r - 1].to_numpy(), panels[sig.EP].iloc[r - 1].to_numpy())
        result = runner.run_book("long_only", s.prices, s4.book_signal(dataclasses.replace(s, signals=panels), sig.EP),
                                 s.calendar, (s.schedule.d0 - 1, r + 1), intervals=s.intervals,
                                 events=s4.empty_events(), cost=dict(s4.STOCK_COSTS["primary"]), top_pct=s4.TOP_PCT,
                                 missing_price_policy=s4.HALT_POLICY)
        held.append(result.holdings.loc[s.calendar[r]])
    pd.testing.assert_series_equal(held[0], held[1])


def test_engine_reads_the_signal_only_at_row_r_minus_1(chain):
    """A price signal kept only at rows r - 1 gives the same book: the SEC panels need no other row."""
    seg = chain["segments"]["pre"]
    full = s4.book_signal(seg, "MOM_12_1")
    keep = np.zeros(len(full), dtype=bool)
    keep[[int(r) - 1 for r in seg.schedule.evaluation_resets]] = True
    sparse = full.where(pd.DataFrame(np.broadcast_to(keep[:, None], full.shape), index=full.index,
                                     columns=full.columns))
    books = [runner.run_book("long_only", seg.prices, s, seg.calendar, seg.window, intervals=seg.intervals,
                             events=s4.segment_events(seg, -1.0), cost=dict(s4.STOCK_COSTS["primary"]),
                             top_pct=s4.TOP_PCT, missing_price_policy=s4.HALT_POLICY) for s in (full, sparse)]
    pd.testing.assert_series_equal(books[0].returns, books[1].returns)
    pd.testing.assert_frame_equal(books[0].holdings, books[1].holdings)


def test_engine_rebalances_on_the_schedule_resets(chain):
    seg = chain["segments"]["post"]
    books = chain["result"]["runs"]["primary"]["seg"]["post"]["sec_books"]
    s4b.check_rebalance_rows(seg, books)
    shifted = dataclasses.replace(seg, schedule=dataclasses.replace(
        seg.schedule, reset_rows=seg.schedule.reset_rows[:-1]))
    with pytest.raises(runner.RunnerStop) as stop:
        s4b.check_rebalance_rows(shifted, books)
    assert stop.value.reason == "sec_rebalance_rows_mismatch"


# ---------------------------------------------------------------- first_filed (2) and annual keys (3)

def _se_doc(facts, flows=True):
    start, end = fb.fy(2010)
    gaap = {sig.SE: {"USD": facts}}
    if flows:
        gaap[sig.NI] = {"USD": [fb.fact(5.0, end, f["filed"], f["accn"], form=f["form"], start=start)
                                for f in facts]}
    return fb.document(gaap)


def test_first_filed_never_replaced_and_amendment_first():
    end = "2010-12-31"
    facts = [fb.fact(100.0, end, "2011-03-01", "0000000009-11-000001"),
             fb.fact(120.0, end, "2011-06-01", "0000000009-11-000002", form="10-K/A"),
             fb.fact(130.0, end, "2012-03-01", "0000000009-12-000001"),
             fb.fact(140.0, end, "2011-08-01", "0000000009-11-000003", form="10-Q")]
    key = next(k for k in _cf(_se_doc(facts)).keys[sig.SE] if k.end == end)
    assert (key.value, key.amendment_first, key.discovered) == (100.0, False, "2011-03-01")
    amended = [dict(f, form="10-K/A") if f["accn"].endswith("11-000001") else f for f in facts]
    key = next(k for k in _cf(_se_doc(amended)).keys[sig.SE] if k.end == end)
    assert key.amendment_first and key.value is None
    renamed = [dict(f, frame="CY2099Q4I", fy=1999, fp="Q2") for f in facts]
    assert _cf(_se_doc(renamed)).keys == _cf(_se_doc(facts)).keys


def test_same_day_10k_and_10ka_is_not_amendment_first():
    """OPUS-S4BF-R2-A1: amendment-first only when every earliest-filed fact is an /A filing."""
    end = "2010-12-31"
    mixed = [fb.fact(90.0, end, "2011-03-01", "0000000009-11-000002", form="10-K/A"),
             fb.fact(100.0, end, "2011-03-01", "0000000009-11-000003"),
             fb.fact(110.0, end, "2011-03-01", "0000000009-11-000004")]
    key = next(k for k in _cf(_se_doc(mixed)).keys[sig.SE] if k.end == end)
    assert (key.amendment_first, key.value, key.accn) == (False, 100.0, "0000000009-11-000003")
    only_a = [dict(f, form="10-K/A") for f in mixed]
    key = next(k for k in _cf(_se_doc(only_a)).keys[sig.SE] if k.end == end)
    assert key.amendment_first


def test_annual_and_instant_keys():
    assert not sig.annual("2010-01-01", "2010-12-16")      # 349 days
    assert sig.annual("2010-01-01", "2010-12-17")          # 350
    assert sig.annual("2010-01-01", "2011-01-16")          # 380
    assert not sig.annual("2010-01-01", "2011-01-17")      # 381
    a = "0000000009-11-000001"
    start, end = fb.fy(2010)
    doc = fb.document({sig.SE: {"USD": [fb.fact(100.0, end, "2011-03-01", a),
                                        fb.fact(150.0, "2011-06-30", "2011-08-01", "0000000009-11-000009",
                                                form="10-K")]},
                       sig.NI: {"USD": [fb.fact(5.0, end, "2011-03-01", a, start=start)]}})
    fund = sig.fundamentals(_cf(doc), "2011-09-01")[sig.BM]
    assert fund["end"] == end                              # the mid-year instant has no annual flow in its accn


# ---------------------------------------------------------------- selection, staleness, amendment order (4, 5)

def test_selection_and_staleness():
    doc = _gp_doc(GrossProfit=[fb.fact(40.0, "2010-12-31", "2011-03-01", fb.accn(9, 2011),
                                       start="2010-01-01")])
    assert _value(doc, sig.GP_AT, "2012-04-02") == (None, "concept_missing")   # GP only at another end
    ok = _gp_doc(GrossProfit=[fb.fact(40.0, "2011-12-31", "2012-03-01", fb.accn(9, 2012), start="2011-01-01")])
    assert _value(ok, sig.GP_AT, "2013-06-30") == (0.1, None)                   # E* exactly 18 months earlier
    assert _value(ok, sig.GP_AT, "2013-07-01") == (None, "stale")
    assert _value(ok, sig.GP_AT, "2012-03-01") == (None, "no_annual_fact")       # filed on d is not usable


def _anchor_years(amend_latest: bool, with_older: bool) -> dict:
    facts = []
    if with_older:
        facts.append(fb.fact(80.0, "2010-12-31", "2011-03-01", fb.accn(9, 2011)))
    facts.append(fb.fact(100.0, "2011-12-31", "2012-03-01", fb.accn(9, 2012),
                         form="10-K/A" if amend_latest else "10-K"))
    ni = [fb.fact(5.0, f["end"], f["filed"], f["accn"], form=f["form"], start=f["end"][:4] + "-01-01") for f in facts]
    return fb.document({sig.SE: {"USD": facts}, sig.NI: {"USD": ni}},
                       [fb.fact(10.0, f["filed"], f["filed"], f["accn"]) for f in facts])


def test_amendment_first_order():
    prices = _flat_prices(start="2012-01-02", n=80)
    assert _value(_anchor_years(True, True), sig.BM, "2012-04-02", prices, 0, 60) == (None, "amendment_first")
    assert _value(_anchor_years(True, False), sig.BM, "2012-04-02", prices, 0, 60) == (None, "amendment_first")
    value, reason = _value(_anchor_years(False, True), sig.BM, "2012-04-02", prices, 0, 60)
    assert reason is None and value == pytest.approx(100.0 / (10.0 * 20.0))
    # An amendment-first first chain concept at E* decides: no fall-through to the next concept or to 0.
    a, a_amend = fb.accn(9, 2012), fb.accn(9, 2012, 7)
    start, end = fb.fy(2011)
    for chain_concepts, signal in ((("PreferredStockValue", "PreferredStockValueOutstanding"), sig.BM),
                                   (("GrossProfit", "Revenues"), sig.GP_AT),
                                   (("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"), sig.GP_AT),
                                   (("CostOfGoodsAndServicesSold", "CostOfRevenue"), sig.GP_AT)):
        flow = signal == sig.GP_AT
        first, second = chain_concepts
        # The first concept is first tagged in a later 10-K/A, which also restates an annual flow.
        extra = {first: [fb.fact(7.0, end, "2012-03-15", a_amend, form="10-K/A", start=start if flow else None)],
                 second: [fb.fact(9.0, end, "2012-03-01", a, start=start if flow else None)],
                 "OperatingIncomeLoss": [fb.fact(1.0, end, "2012-03-15", a_amend, form="10-K/A", start=start)]}
        if first.startswith("Cost"):
            extra["Revenues"] = [fb.fact(30.0, end, "2012-03-01", a, start=start)]
        doc = _gp_doc(**extra)
        assert _value(doc, signal, "2012-04-02", prices, 0, 60) == (None, "amendment_first"), first


# ---------------------------------------------------------------- chains (6)

def test_chains_preferred_gross_profit_and_cogs():
    prices = _flat_prices(start="2012-01-02", n=80)
    a = fb.accn(9, 2012)
    start, end = fb.fy(2011)
    old_a = fb.accn(9, 2011)
    # Preferred: an untagged line at E* after an earlier tagged year gives 0 and the counted status.
    doc = _gp_doc(PreferredStockValue=[fb.fact(30.0, "2010-12-31", "2011-03-01", old_a)])
    cf = _cf(doc)
    fund = sig.fundamentals(cf, "2012-04-02")[sig.BM]
    assert fund["preferred_zero"] and fund["numerator"] == 100.0
    tagged = _gp_doc(PreferredStockValueOutstanding=[fb.fact(30.0, end, "2012-03-01", a)],
                     PreferredStockIncludingAdditionalPaidInCapitalNetOfDiscount=[fb.fact(60.0, end, "2012-03-01", a)])
    assert sig.fundamentals(_cf(tagged), "2012-04-02")[sig.BM]["numerator"] == 70.0
    # A later-filed preferred fact at E* does not change an earlier rebalance.
    late_a = fb.accn(9, 2012, 3)                            # a later 10-K-form filing with its own annual flow
    late = _gp_doc(PreferredStockValue=[fb.fact(30.0, end, "2012-05-01", late_a)],
                   OperatingIncomeLoss=[fb.fact(1.0, end, "2012-05-01", late_a, start=start)])
    assert sig.fundamentals(_cf(late), "2012-04-02")[sig.BM]["numerator"] == 100.0
    assert sig.fundamentals(_cf(late), "2012-06-01")[sig.BM]["numerator"] == 70.0
    negative = _gp_doc(PreferredStockValue=[fb.fact(100.0, end, "2012-03-01", a)])
    assert _value(negative, sig.BM, "2012-04-02", prices, 0, 60) == (None, "be_nonpositive")
    # GrossProfit precedes Revenue - COGS; Revenue and COGS must share start and end.
    both = _gp_doc(GrossProfit=[fb.fact(40.0, end, "2012-03-01", a, start=start)],
                   Revenues=[fb.fact(300.0, end, "2012-03-01", a, start=start)],
                   CostOfRevenue=[fb.fact(100.0, end, "2012-03-01", a, start=start)])
    assert _value(both, sig.GP_AT, "2012-04-02") == (0.1, None)
    shifted = _gp_doc(Revenues=[fb.fact(300.0, end, "2012-03-01", a, start=start)],
                      CostOfRevenue=[fb.fact(100.0, end, "2012-03-01", a, start="2011-01-05")])
    assert _value(shifted, sig.GP_AT, "2012-04-02") == (None, "concept_missing")
    # CostOfGoodsSold only after the two earlier COGS concepts have no key at E*.
    cogs = _gp_doc(Revenues=[fb.fact(300.0, end, "2012-03-01", a, start=start)],
                   CostOfRevenue=[fb.fact(100.0, end, "2012-03-01", a, start=start)],
                   CostOfGoodsSold=[fb.fact(200.0, end, "2012-03-01", a, start=start)])
    assert _value(cogs, sig.GP_AT, "2012-04-02") == (0.5, None)
    deprecated = _gp_doc(Revenues=[fb.fact(300.0, end, "2012-03-01", a, start=start)],
                         CostOfGoodsSold=[fb.fact(200.0, end, "2012-03-01", a, start=start)])
    assert _value(deprecated, sig.GP_AT, "2012-04-02") == (0.25, None)
    bank = _gp_doc(Revenues=[fb.fact(300.0, end, "2012-03-01", a, start=start)])
    assert _value(bank, sig.GP_AT, "2012-04-02") == (None, "concept_missing")


# ---------------------------------------------------------------- shares (7) and ME (8)

def _shares_doc(dei=None, cso=None):
    a = fb.accn(9, 2012)
    start, end = fb.fy(2011)
    gaap = {sig.SE: {"USD": [fb.fact(100.0, end, "2012-03-01", a)]},
            sig.NI: {"USD": [fb.fact(10.0, end, "2012-03-01", a, start=start)]}}
    if cso is not None:
        gaap[sig.CSO] = {"shares": [fb.fact(v, e, "2012-03-01", a) for e, v in cso]}
    return fb.document(gaap, None if dei is None else [fb.fact(v, e, "2012-03-01", a) for e, v in dei])


def test_shares_order():
    prices = _flat_prices(start="2012-01-02", n=80)
    fund = lambda doc: sig.fundamentals(_cf(doc), "2012-04-02")[sig.BM]          # noqa: E731
    comparative = _shares_doc(cso=[("2011-12-31", 20.0), ("2010-12-31", 25.0)])
    assert (fund(comparative)["share_date"], fund(comparative)["shares"]) == ("2011-12-31", 20.0)
    two = _shares_doc(dei=[("2012-02-15", 20.0), ("2012-02-15", 21.0)])
    assert _value(two, sig.BM, "2012-04-02", prices, 0, 60) == (None, "shares_ambiguous")
    latest = _shares_doc(dei=[("2012-01-15", 20.0), ("2012-02-15", 20.0)])
    assert fund(latest)["share_date"] == "2012-02-15"
    after = _shares_doc(dei=[("2012-03-05", 20.0)], cso=[("2011-12-31", 20.0)])
    assert _value(after, sig.BM, "2012-04-02", prices, 0, 60) == (None, "shares_missing")
    zero = _shares_doc(cso=[("2011-12-31", 0.0)])
    assert _value(zero, sig.BM, "2012-04-02", prices, 0, 60) == (None, "shares_missing")


def test_me_split_continuity():
    n = 30
    calendar = pd.bdate_range("2012-02-01", periods=n)
    s_row = int(calendar.searchsorted(pd.Timestamp("2012-02-15"), side="right")) - 1
    raw = np.full(n, 40.0)
    raw[s_row + 3:] = 20.0                                   # a 2-for-1 split between p and r - 1
    factor = np.where(np.arange(n) >= s_row + 3, 0.5, 1.0)
    split = sig.PricePanel(calendar, pd.Index(["X"]), (raw / factor).reshape(n, 1), factor.reshape(n, 1))
    plain = sig.PricePanel(calendar, pd.Index(["X"]), np.full((n, 1), 40.0), np.ones((n, 1)))
    row = n - 5
    assert split.market_equity(0, row, "2012-02-15", 10.0) == pytest.approx(10.0 * 2 * 20.0)
    assert split.market_equity(0, row, "2012-02-15", 10.0) == plain.market_equity(0, row, "2012-02-15", 10.0)
    later = factor.copy()
    later[row + 1:] = 0.25                                   # a split after r - 1 never enters ME at r - 1
    raw_later = raw.copy()
    raw_later[row + 1:] = 10.0
    after = sig.PricePanel(calendar, pd.Index(["X"]), (raw_later / later).reshape(n, 1), later.reshape(n, 1))
    assert after.market_equity(0, row, "2012-02-15", 10.0) == split.market_equity(0, row, "2012-02-15", 10.0)
    assert plain.market_equity(0, row, "2012-01-15", 10.0) is None          # s before the loaded rows
    gappy = np.full((n, 1), 40.0)
    gappy[:s_row + 1] = np.nan
    far = sig.PricePanel(calendar, pd.Index(["X"]), gappy, np.ones((n, 1)))
    assert far.market_equity(0, row, "2012-02-15", 10.0) is None            # no finite close within 10 rows
    near = gappy.copy()
    near[s_row - 9] = 40.0
    assert sig.PricePanel(calendar, pd.Index(["X"]), near, np.ones((n, 1))).market_equity(
        0, row, "2012-02-15", 10.0) == pytest.approx(400.0)
    near[s_row - 9], near[s_row - 10] = np.nan, 40.0
    assert sig.PricePanel(calendar, pd.Index(["X"]), near, np.ones((n, 1))).market_equity(
        0, row, "2012-02-15", 10.0) is None


# ---------------------------------------------------------------- identity gate (9) and pins (10)

def test_identity_gate(chain):
    doc = chain["doc"]
    for sid, seg in chain["segments"].items():
        panels = chain["result"]["panels"][sid]
        for asset in (fb.UNMAPPED, fb.AMBIGUOUS, *fb.MULTI, fb.ABSENT):
            col = list(seg.prices.columns).index(asset)
            for s in sig.SIGNALS:
                assert not np.isfinite(panels.signals[s].iloc[:, col]).any()
            assert np.isfinite(s4.book_signal(seg, "MOM_12_1").iloc[:, col]).any()   # still in the price sleeves
        share = doc["sec_share"][sid][sig.BM]
        for reason, n_ids in (("identity_unmapped", 1), ("identity_ambiguous", 1), ("identity_multi_class", 2),
                              ("facts_absent", 1)):
            assert share["by_status"][reason] > 0
            assert share["by_status_and_exit_class"][reason]["unknown"] == share["by_status"][reason]
        assert doc["rebalance_statuses"][sid][sig.BM]["identity_multi_class"] == \
            2 * doc["rebalance_statuses"][sid][sig.BM]["identity_unmapped"]


def _sec_repo(tmp_path: Path) -> tuple[Path, Path, dict[str, str], dict[str, str], list]:
    repo, snap = tmp_path / "repo", tmp_path / "snap"
    cache = repo / dm.CACHE_DIR
    (cache / "companyfacts").mkdir(parents=True)
    snap.mkdir()
    identity = fb.identity()
    files = []
    for row in identity.to_dict(orient="records"):
        if row["status"] != ident.UNIQUE:
            continue
        cik = int(row["cik"])
        relative = f"companyfacts/CIK{cik:010d}.json"
        url = COMPANYFACTS_URL.format(cik=cik)
        path = cache / relative
        record = {"url": url, "retrieved_utc": "2026-01-01T00:00:00Z", "status": 404, "sha256": None}
        if row["permanent_id"] != fb.ABSENT:
            payload = json.dumps(fb.company(row["permanent_id"])).encode()
            path.write_bytes(payload)
            record.update(status=200, sha256=hashlib.sha256(payload).hexdigest())
        path.with_name(path.name + s4b.SIDECAR).write_text(json.dumps(record))
        files.append(dm.SecFile(relative, url, record["retrieved_utc"], record["status"], record["sha256"],
                                path.stat().st_size if path.exists() else 0))
    map_bytes = identity.to_csv(index=False, lineterminator="\n").encode()
    hash_list = dm.hash_list_bytes(files)
    private = tmp_path / dm.PRIVATE_DIRNAME
    private.mkdir()
    (private / dm.MAP_FILE).write_bytes(map_bytes)
    (private / dm.HASH_LIST_FILE).write_bytes(hash_list)
    pins = {"cik_map_sha256": hashlib.sha256(map_bytes).hexdigest(),
            "file_hash_list_sha256": hashlib.sha256(hash_list).hexdigest()}
    (repo / "reports").mkdir()
    (repo / dm.MANIFEST_JSON).write_text(json.dumps({"cik_map": {"sha256": pins["cik_map_sha256"]},
                                                     "file_hash_list": {"sha256": pins["file_hash_list_sha256"]}}))
    (repo / "code.py").write_text("x = 1\n")
    code = {"code.py": hashlib.sha256(b"x = 1\n").hexdigest()}
    return repo, snap, pins, code, files


def _cached(repo: Path, suffix: str = "") -> list[Path]:
    """The cached companyfacts payloads (or, with ``suffix``, their retrieval records), sorted: glob order is
    filesystem order, and ``*.json`` also matches the ``*.json.retrieval.json`` records."""
    files = sorted((repo / dm.CACHE_DIR / "companyfacts").glob("*.json"))
    return [p for p in files if p.name.endswith(s4b.SIDECAR) == bool(suffix)]


def test_sec_pins_offline(tmp_path):
    repo, snap, pins, code, _ = _sec_repo(tmp_path)
    calls = []
    sentinel = lambda *a, **k: calls.append(a)                                 # noqa: E731
    sec = s4b.load_sec(repo, snap, pins, code, opener=sentinel)
    assert sec.requests == 0 and not calls
    assert sum(v is None for v in sec.facts.values()) == 1 and len(sec.facts) == 26
    for label, mutate in (
            ("map", lambda: (tmp_path / dm.PRIVATE_DIRNAME / dm.MAP_FILE).write_bytes(b"changed")),
            ("file", lambda: _cached(repo)[0].write_bytes(b"{}")),
            ("sidecar", lambda: _cached(repo, s4b.SIDECAR)[0].write_bytes(b"{}")),
            ("code", lambda: (repo / "code.py").write_text("x = 2\n"))):
        backup = {p: p.read_bytes() for p in [tmp_path / dm.PRIVATE_DIRNAME / dm.MAP_FILE, repo / "code.py",
                                              *sorted((repo / dm.CACHE_DIR / "companyfacts").glob("*.json"))]}
        mutate()
        with pytest.raises(runner.RunnerStop) as stop:
            s4b.load_sec(repo, snap, pins, code, opener=sentinel)
        assert stop.value.reason == "sec_pin_mismatch", label
        for path, data in backup.items():
            path.write_bytes(data)
    with pytest.raises(runner.RunnerStop) as stop:
        s4b.load_sec(repo, snap, {**pins, "file_hash_list_sha256": "0" * 64}, code, opener=sentinel)
    assert stop.value.reason == "sec_pin_mismatch"
    assert not calls


def test_identity_pool_mismatch_refuses(chain):
    sec = chain["sec"]
    short = s4b.SecInputs(identity=sec.identity[sec.identity["permanent_id"] != fx.ASSETS[20]], facts=sec.facts)
    with pytest.raises(runner.RunnerStop) as stop:
        s4b.check_identity_pool(chain["segments"], short)
    assert stop.value.reason == "sec_identity_pool_mismatch"
    # An asset in the mask only on warm-up rows before d0 - 1 enters no ranking set and no member-day.
    seg = chain["segments"]["pre"]
    col = list(seg.prices.columns).index(fx.ASSETS[20])
    mask = seg.schedule.evaluation_mask.copy()
    mask.iloc[seg.schedule.d0 - 1:, col] = False
    warm_only = dataclasses.replace(seg, schedule=dataclasses.replace(seg.schedule, exclusions=~mask | seg.schedule.exclusions))
    assert warm_only.schedule.evaluation_mask.iloc[:seg.schedule.d0 - 1, col].any()
    s4b.check_identity_pool({"pre": warm_only}, short)


# ---------------------------------------------------------------- reasons (11) and member-day statuses (12)

def test_sec_reasons_frozen_order_and_stale_before_missing():
    """OPUS-S4BF-R2-A2: the first applicable reason of the frozen order; stale wins over concept_missing."""
    assert len(sig.REASON_ORDER) == 15 and sig.REASON_ORDER[0] == sig.NOT_RANKED
    amendment = json.loads((REPO_ROOT / s4b.AMENDMENT_5_PATH).read_text())
    assert [r["type"] for r in amendment["missingness"]["sec_reasons"]["order"]] == list(sig.REASON_ORDER)
    assert sig.first_reason({"concept_missing", "stale"}) == "stale"
    assert sig.first_reason({"price_missing", "be_nonpositive", "amendment_first"}) == "amendment_first"
    old_gp_only = _gp_doc(GrossProfit=[fb.fact(40.0, "2010-12-31", "2011-03-01", fb.accn(9, 2011),
                                               start="2010-01-01")])
    assert _value(old_gp_only, sig.GP_AT, "2012-04-02") == (None, "concept_missing")
    assert _value(old_gp_only, sig.GP_AT, "2013-08-01") == (None, "stale")


def test_every_ranking_set_member_gets_one_rebalance_status(chain):
    for sid, seg in chain["segments"].items():
        panels = chain["result"]["panels"][sid]
        mask = seg.schedule.evaluation_mask.to_numpy(dtype=bool)
        for s in sig.SIGNALS:
            for r, status in panels.statuses[s].items():
                assert all((v is not None) == bool(m) for v, m in zip(status, mask[r - 1]))
                assert {v for v in status if v is not None} <= set(s4b.STATUSES) - {sig.NOT_RANKED}
                finite = np.isfinite(panels.signals[s].iloc[r - 1].to_numpy())
                assert list(finite) == [v == sig.RANKED for v in status]


def _day_fixture():
    """Six members over two rebalances (rows 3 and 8) and rows 3 to 12."""
    rows, cols = 13, ["M0", "M1", "M2", "M3", "M4", "M5"]
    mask = np.zeros((rows, len(cols)), dtype=bool)
    mask[:, 0] = True                                      # always in
    mask[5:, 1] = True                                     # enters between rebalances (after row 3)
    mask[:6, 2] = True                                     # exits between rebalances
    mask[:, 3] = True
    mask[7, 3] = False                                     # bar gap covering r - 1 = 7, resumes at 8
    mask[:, 4] = True
    mask[5, 4] = False                                     # bar gap between rebalances, not covering r - 1
    mask[9:, 5] = True                                     # enters after the second rebalance
    frame = pd.DataFrame(mask, columns=cols)
    schedule = SimpleNamespace(evaluation_mask=frame, evaluation_resets=np.array([3, 8]), d0=3, d_last=12)
    seg = SimpleNamespace(schedule=schedule, prices=frame, offset=0, segment_id="pre")
    statuses = {}
    for s in sig.SIGNALS:
        statuses[s] = {3: np.array([sig.RANKED, None, "stale", sig.RANKED, "price_missing", None], dtype=object),
                       8: np.array([sig.RANKED, "shares_missing", None, None, sig.RANKED, None], dtype=object)}
    preferred = {3: np.zeros(6, dtype=bool), 8: np.zeros(6, dtype=bool)}
    return seg, s4b.SecPanels(signals={}, statuses=statuses, preferred_zero=preferred)


def test_member_day_statuses_partition_the_mask():
    seg, panels = _day_fixture()
    days = s4b.day_statuses(seg, panels, sig.BM)
    assert list(days[3:8, 1]) == [None, None, sig.NOT_RANKED, sig.NOT_RANKED, sig.NOT_RANKED]   # entrant
    assert list(days[3:8, 2]) == ["stale", "stale", "stale", None, None]                        # stops at exit
    assert list(days[8:13, 3]) == [sig.NOT_RANKED] * 5                                          # gap covers r - 1
    assert list(days[3:8, 4]) == ["price_missing", "price_missing", None, "price_missing", "price_missing"]
    assert list(days[8:13, 1]) == ["shares_missing"] * 5
    assert list(days[9:13, 5]) == [sig.NOT_RANKED] * 4
    out = s4b.member_day_statuses(seg, panels, None)[sig.BM]
    assert out["denominator"] == int(seg.schedule.evaluation_mask.to_numpy()[3:13].sum())
    assert sum(out["by_status"].values()) == out["denominator"]
    # No status uses a later rebalance's information.
    later = {s: {3: v[3], 8: np.array(["stale"] * 6, dtype=object)} for s, v in panels.statuses.items()}
    changed = s4b.day_statuses(seg, dataclasses.replace(panels, statuses=later), sig.BM)
    assert all(a == b for a, b in zip(days[3:8].ravel(), changed[3:8].ravel()))


def test_member_day_gap_or_double_count_refuses():
    seg, panels = _day_fixture()
    broken = {s: {3: v[3].copy(), 8: v[8]} for s, v in panels.statuses.items()}
    broken[sig.BM][3][0] = None                            # a ranking-set member without a rebalance status
    with pytest.raises(runner.RunnerStop) as stop:
        s4b.member_day_statuses(seg, dataclasses.replace(panels, statuses=broken), None)
    assert stop.value.reason == "sec_share_unreconciled"
    for delta in (-1, 1):
        with pytest.raises(runner.RunnerStop) as stop:
            s4b.reconcile_sec_share("pre", sig.BM, 10, {(sig.RANKED, "unknown"): 10 + delta})
        assert stop.value.reason == "sec_share_unreconciled"
    s4b.reconcile_sec_share("pre", sig.BM, 10, {(sig.RANKED, "unknown"): 6, ("stale", "unknown"): 4})


def test_locked_holding_stays_held_while_its_day_is_not_ranked(chain):
    """GPT-S4BF-R2-A1 and OPUS-S4BF-R2-A3: a retained halt keeps its engine holding; its status stays distinct."""
    seg = chain["segments"]["pre"]                          # pre rows equal full-calendar rows
    resets = [int(r) for r in seg.schedule.evaluation_resets]
    k = 10
    r = resets[k]
    books = chain["result"]["runs"]["primary"]["seg"]["pre"]["sec_books"]["sleeves"][(sig.EP, "primary")]
    before = books.holdings.loc[seg.calendar[r - 1]]
    asset = before[before > 0].index[0]
    paths = fx.vendor_paths()
    for field in ("open", "high", "low", "close", "adjusted_close", "volume"):
        paths[field].iloc[r - 1:r + 1, fx.ASSETS.index(asset)] = np.nan       # halted at r - 1 and r
    halted = fx.prepared(paths)["pre"]
    panels = s4b.sec_panels(halted, chain["sec"])
    col = list(halted.prices.columns).index(asset)
    result = s4.run_books(dataclasses.replace(halted, signals=panels.signals), -1.0, (sig.EP,))
    book = result["sleeves"][(sig.EP, "primary")]
    assert any(asset in row["locked"] for row in book.halt_ledger["locked_execution_rows"])
    days = s4b.day_statuses(halted, panels, sig.EP)
    after = [t for t in range(r + 1, resets[k + 1]) if halted.schedule.evaluation_mask.iloc[t, col]]
    assert after and all(days[t, col] == sig.NOT_RANKED for t in after)
    held = book.holdings[asset].reindex(halted.calendar[after])
    assert (held > 0).all()                                 # the locked position stays held
    counts = s4b.member_day_statuses(halted, panels, None)[sig.EP]
    assert counts["by_status"][sig.NOT_RANKED] >= len(after)
    assert s4b.LOCKED_HOLDINGS in s4b.render_report(_render_doc(chain))


# ---------------------------------------------------------------- empty target (13), step 4 regression (14)

def test_empty_sec_sleeve_refuses(chain):
    seg = chain["segments"]["pre"]
    signals = {k: v.copy() for k, v in chain["result"]["panels"]["pre"].signals.items()}
    r = int(seg.schedule.evaluation_resets[5])
    signals[sig.GP_AT].iloc[r - 1] = np.nan
    with pytest.raises(runner.RunnerStop) as stop:
        s4.run_books(dataclasses.replace(seg, signals=signals), -1.0, s4b.SEC_IDS)
    assert stop.value.reason == "empty_sleeve_target"


def _step4_summary(segments=None, public=None) -> dict:
    doc = s4.summarize(s4.evaluate(segments or fx.prepared(), public or fx.public(), {fx.STOP_ASSET}, None))
    return json.loads(json.dumps(s4._clean(doc), sort_keys=True, allow_nan=False))


def _differences(got, want, path: str = "") -> list[str]:
    """Paths where ``got`` differs from ``want``: exact for keys, lengths, and every non-float leaf; floats within
    REL_TOL relative plus ABS_TOL absolute (last-bit platform differences only)."""
    if isinstance(want, dict):
        if not isinstance(got, dict) or set(got) != set(want):
            return [path or "/"]
        return [d for k in sorted(want) for d in _differences(got[k], want[k], f"{path}/{k}")]
    if isinstance(want, list):
        if not isinstance(got, list) or len(got) != len(want):
            return [path]
        return [d for i, (g, w) in enumerate(zip(got, want)) for d in _differences(g, w, f"{path}[{i}]")]
    if isinstance(want, float) and isinstance(got, float) and not isinstance(got, bool):
        return [] if abs(got - want) <= REL_TOL * max(abs(got), abs(want)) + ABS_TOL else [path]
    return [] if (type(got), got) == (type(want), want) else [path]


def test_step4_regression_matches_the_pre_change_golden():
    """The parameterized step 4 reproduces its pre-change synthetic output; the golden is that output byte for byte."""
    text = STEP4_GOLDEN.read_text(encoding="utf-8")
    assert hashlib.sha256(text.encode()).hexdigest() == STEP4_JSON_SHA256
    golden = json.loads(text)
    assert _differences(_step4_summary(), golden) == []
    report = s4.render_report({**golden, "unpriced": {}})
    assert hashlib.sha256(report.encode()).hexdigest() == STEP4_GOLDEN_MD_SHA256


def test_step4_regression_check_catches_a_one_line_change(monkeypatch):
    """A one-line change to a step 4 cost constant fails the comparison (hundreds of leaves move)."""
    golden = json.loads(STEP4_GOLDEN.read_text(encoding="utf-8"))
    monkeypatch.setitem(s4.SWITCH_BPS, "primary", 21)
    assert len(_differences(_step4_summary(), golden)) > 100
    assert _differences(json.loads(json.dumps(golden)), golden) == []
    nudged = json.loads(json.dumps(golden))
    nudged["runs"]["primary"]["rules"]["R0"]["primary"]["pre"]["sharpe"] *= 1 + 1e-8
    assert _differences(nudged, golden) == ["/runs/primary/rules/R0/primary/pre/sharpe"]


def test_comparator_mismatch_refuses(chain):
    committed = json.loads(json.dumps(chain["committed"]))
    s4b.check_comparator(chain["result4"]["runs"]["primary"]["grid"]["R0"], committed, "primary")
    committed["runs"]["last_close"]["rules"]["R0"]["primary"]["pre"]["sharpe"] += 1e-15
    with pytest.raises(runner.RunnerStop) as stop:
        s4b.check_comparator(chain["result4"]["runs"]["last_close"]["grid"]["R0"], committed, "last_close")
    assert stop.value.reason == "comparator_mismatch"
    committed = json.loads(json.dumps(chain["committed"]))
    committed["runs"]["primary"]["transmission"]["pre"]["MOM_12_1"]["months"] += 1
    with pytest.raises(runner.RunnerStop) as stop:
        s4b.check_step4_regeneration(chain["committed"], committed)
    assert stop.value.reason == "step4_regeneration_mismatch"


def test_comparison_months_mismatch_refuses(chain):
    six = chain["result4"]["runs"]["primary"]["seg"]["pre"]["layer"]
    nine = chain["result"]["runs"]["primary"]["seg"]["pre"]["layer9"]
    s4b.check_months(nine, six, None, "pre")
    shorter = {case: {**nine[case], "months": nine[case]["months"][1:]} for case in s4.CASES}
    with pytest.raises(runner.RunnerStop) as stop:
        s4b.check_months(shorter, six, None, "pre")
    assert stop.value.reason == "comparison_months_mismatch"
    with pytest.raises(runner.RunnerStop) as stop:
        s4b.check_months(nine, six, s4b.COMPARISON_MONTHS["pre"], "pre")
    assert stop.value.reason == "comparison_months_mismatch"
    assert s4b.COMPARISON_MONTHS == {"pre": ("2014-12", "2019-06", 55), "post": ("2022-05", "2025-12", 44)}


# ---------------------------------------------------------------- coverage tilt, decision, fragility (15-18)

def _rows(margins):
    keys = [(s, c, m) for s in s4.SEGMENTS for c in s4.CASES for m in ("max_drawdown", "sharpe")]
    return [{"segment": s, "cost_case": c, "metric": m, "margin": x, "holds": x is not None and x >= -1e-12}
            for (s, c, m), x in zip(keys, margins)]


def test_coverage_tilt(chain):
    unique = set(chain["sec"].identity.loc[chain["sec"].identity["status"] == ident.UNIQUE, "permanent_id"])
    mapped = s4b.mapped_segment(chain["segments"]["pre"], unique)
    for signal in mapped.signals.values():
        used = signal.columns[np.isfinite(signal.to_numpy()).any(axis=0)]
        assert set(used) <= unique
    assert not s4b.coverage_tilt(_rows([0.1] * 8), _rows([0.2] * 8))["coverage_tilted"]
    label = s4b.coverage_tilt(_rows([0.1] * 8), _rows([0.1] * 7 + [-0.1]))
    assert label == {"coverage_tilted": True, "sign_changes": ["post:sensitivity:sharpe"]}
    run = chain["result"]["runs"]["primary"]
    assert run["outcome"] == s4b.decide(run["conditions"])       # the outcome reads R0_6 conditions only


def test_decide_4b():
    grid = lambda sharpe=1.0, dd=-0.1: {c: {s: {"sharpe": sharpe, "max_drawdown": dd} for s in s4.SEGMENTS}  # noqa: E731
                                        for c in s4.CASES}
    assert s4b.decide(s4.conditions(grid(), grid())) == "join"
    assert s4b.decide(s4.conditions(grid(1.0 - 5e-13), grid())) == "join"
    worse = grid()
    worse["sensitivity"]["post"] = {"sharpe": 0.9, "max_drawdown": -0.1}
    assert s4b.decide(s4.conditions(worse, grid())) == "not_join"
    undefined = grid()
    undefined["primary"]["pre"] = {"sharpe": None, "max_drawdown": -0.1}
    assert s4b.decide(s4.conditions(undefined, grid())) == "not_join"


def test_fragility_4b(chain):
    base_run = {"s4b_mean": 0.001, "conditions": _rows([0.1] * 8), "outcome": "join"}
    assert not s4b.fragility(base_run, dict(base_run))["fragile"]
    assert s4b.fragility(base_run, {**base_run, "s4b_mean": -0.001})["sign_changes"] == [s4b.TEST_ID]
    assert s4b.fragility(base_run, {**base_run, "conditions": _rows([0.1] * 7 + [-0.1])})["fragile"]
    assert s4b.fragility(base_run, {**base_run, "outcome": "not_join"})["outcome_changes"] == ["outcome"]
    assert set(chain["doc"]["s4b_test"]) == {s4b.TEST_ID}
    assert "hac_pvalue" not in json.dumps(chain["doc"]["runs"]["last_close"])


def test_s4b_family_is_by_with_481_slots(chain):
    stat = chain["doc"]["s4b_test"][s4b.TEST_ID]
    q = s4b.s4b_family(pd.Series({s4b.TEST_ID: stat["family_p"]}))
    assert stat["by_qvalue"] == pytest.approx(float(q.iloc[0]))
    assert stat["by_qvalue"] == pytest.approx(min(1.0, stat["family_p"] * 481 * sum(1 / k for k in range(1, 482))))
    assert chain["doc"]["family"] == {"observed_tests": 1, "prior_slots": 480, "family_size": 481, "method": "by"}
    for bad in (pd.Series({"a": 0.1, "b": 0.2}), pd.Series(dtype=float)):
        with pytest.raises(runner.RunnerStop):
            s4b.s4b_family(bad)
    with pytest.raises(runner.RunnerStop):
        s4b.s4b_family(pd.Series({"a": 0.1}), family_size=480)


def test_rule_r1_descriptive(chain):
    run = chain["result"]["runs"]["primary"]
    assert set(run["grid"]) == set(s4b.BOOKS)
    assert {r["comparator"] for r in run["conditions"]} == {m["sharpe"] for c in run["grid"]["R0_6"].values()
                                                            for m in c.values()} | {
        m["max_drawdown"] for c in run["grid"]["R0_6"].values() for m in c.values()}
    assert "R1_9" not in json.dumps(chain["doc"]["s4b_test"])


def test_public_counterpart_is_r0_over_nine_against_six(chain):
    run = chain["result"]["runs"]["primary"]
    pub = run["public"]
    chars9 = [s4b.ALL_SLEEVES[s][0] for s in s4b.ALL_IDS]
    months = chain["result4"]["runs"]["primary"]["seg"]["pre"]["layer"]["primary"]["months"]
    values = chain["public"].jkp[chars9]
    span = values.index[values.notna().all(axis=1)]
    net = values.loc[span[0]:chain["public"].last_month].mean(axis=1)
    expected = base.performance(net.loc[months[0]:months[-1]])
    assert pub["rules"]["R0_9"]["primary"]["pre"]["annualized_mean"] == pytest.approx(expected["annualized_mean"])
    assert len(run["survival"]) == 8 and all("public_margin" in r for r in run["survival"])


def test_identity_exposure_by_exit_class_and_reason():
    calendar = pd.bdate_range("2020-01-01", periods=60)
    day = lambda r: calendar[r].date().isoformat()                              # noqa: E731
    pool = pd.DataFrame([
        {"permanent_id": "P1", "m_in": day(0), "m_out": "", "exit_class": "index_removal_still_trading",
         "segments": "pre"},
        {"permanent_id": "P2", "m_in": day(15), "m_out": day(25), "exit_class": "delisting_candidate",
         "segments": "pre"},
        {"permanent_id": "P3", "m_in": day(5), "m_out": day(50), "exit_class": "delisting_candidate",
         "segments": "pre;post"}])
    identity = pd.DataFrame([{"permanent_id": "P1", "status": "unique", "reason": "accepted"},
                             {"permanent_id": "P2", "status": "unmapped", "reason": "name_mismatch"},
                             {"permanent_id": "P3", "status": "unique", "reason": "accepted"}])
    out = s4b.identity_exposure(pool, identity, calendar, {"pre": (10, 29), "post": (40, 59)})
    assert out["pre"]["days"] == 20 + 10 + 20 and out["pre"]["not_mapped"] == 10
    assert out["pre"]["by_exit_class"]["delisting_candidate"] == {"days": 30, "not_mapped": 10, "share": 1 / 3}
    assert out["pre"]["by_reason"] == {"unmapped: name_mismatch": {"days": 10, "share": 10 / 50}}
    assert out["post"]["days"] == 10 and out["pooled"]["days"] == 60 and out["pooled"]["not_mapped"] == 10


# ---------------------------------------------------------------- R11 (21) and trial pins (23)

FORBIDDEN = (re.compile(r"\b[A-Z][A-Z0-9-]*\.US\b"), re.compile(r"/Users/|/private/|/home/|private_data|/tmp/"),
             re.compile(r"CIK\d|\b0\d{9}\b"), re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"))


def _scan(text: str, extra: tuple[str, ...] = ()) -> None:
    for pattern in FORBIDDEN:
        assert not pattern.search(text), pattern.pattern
    for token in extra:
        assert token not in text, token


def _render_doc(chain) -> dict:
    """The synthetic summary plus the run-level fields ``run`` adds (no snapshot accounting)."""
    return {**chain["doc"], "unpriced": {}, "identity_exposure": {},
            "costs": {"stock": s4.STOCK_COSTS, "switch_bps": s4.SWITCH_BPS}, "top_pct": s4.TOP_PCT,
            "sigma_rows": s4.SIGMA_ROWS, "git": {"commit": "synthetic", "tracked_changes": False},
            "sec": {"identity_counts": dict(fb.identity()["status"].value_counts())}}


def test_outputs_hold_no_identifier_or_path(chain):
    doc = _render_doc(chain)
    text = json.dumps(s4._clean(doc)) + s4b.render_report(doc)
    ciks = tuple(f"{c:010d}" for c in fb.CIK_OF.values())
    _scan(text, tuple(fx.ASSETS) + tuple(a.split(".")[0] for a in fx.ASSETS) + ciks)
    for relative in (s4b.REPORT_MD, s4b.REPORT_JSON, s4b.ATTEMPTS_JSONL):
        path = REPO_ROOT / relative
        if path.is_file():
            _scan(path.read_text(encoding="utf-8"))


def test_report_leads_with_the_decision_and_every_table_row_fits(chain):
    report = s4b.render_report(_render_doc(chain))
    sections = [line for line in report.splitlines() if line.startswith("## ")]
    assert sections[0] == "## Decision Outcome (primary run)"
    lead = report.split("## Decision Outcome")[1].split("\n## ")[0]
    for token in ("Outcome:", "BY q", "Fragility:", "Coverage tilt:", "Last-close outcome:"):
        assert token in lead
    assert report.index("DIAGNOSTIC_ONLY") < report.index("VP-2") < report.index("## Decision Outcome")
    width = None
    for line in report.splitlines():
        if line.startswith("|"):
            cells = line.count("|") - 1
            width = cells if width is None else width
            assert cells == width, line
        else:
            width = None


def test_report_states_method_costs_and_sample_causes(chain):
    """GPT-S4BC-R1-A1 and OPUS-S4BC-A1 to A4: disclosures come from the document and the module constants."""
    from backtest.portfolio import _TIMING_CONTRACT

    report = s4b.render_report(_render_doc(chain))
    method = report.split("## Method, Costs, and Provenance")[1].split("\n## ")[0]
    assert s4b.TIMING_CONTRACT == _TIMING_CONTRACT and _TIMING_CONTRACT in method
    for case in s4.CASES:
        stock = s4.STOCK_COSTS[case]
        assert (f"{case} {stock['transaction_cost_bps']:g} + {stock['slippage_bps']:g} bp stock with a "
                f"{s4.SWITCH_BPS[case]:g} bp switch cost") in method
    for token in ("row r - 1", "close of row r", "row r + 1", "month t-2", "month t-1 close", "no borrow",
                  "Nothing nets across sleeves", "no market-impact model", s4b.AMENDMENT_5_SHA256, s4b.REPORT_JSON,
                  f"{s4.SIGMA_ROWS} daily rows", "top 20%"):
        assert token in method, token
    header = report.split("## Decision Outcome")[0]
    assert s4b.VP2_STEP4B in header and "for step 4 only" not in header
    assert "for step 4 only" in s4.VP2                     # the step 4 constant and outputs are unchanged
    missing = report.split("## SEC Missingness")[1].split("\n## ")[0]
    for token in ("row m_in - 1", "not dropped", "OPUS-S4BC-A1", "GP_AT_AF ranks", "no COGS key",
                  "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", "ProfitLoss"):
        assert token in missing, token
    share = chain["doc"]["sec_share"]
    assert f"{share['pre'][sig.BM]['by_status_and_exit_class'][sig.NOT_RANKED]['unknown']} pre" in missing


def test_committed_report_renders_from_the_committed_json():
    """The committed report is ``render_report`` of the committed JSON, in the declared segment and run order."""
    md, doc = REPO_ROOT / s4b.REPORT_MD, REPO_ROOT / s4b.REPORT_JSON
    if not (md.is_file() and doc.is_file()):
        pytest.skip("step 4b outputs not present")
    text = s4b.render_report(json.loads(doc.read_text(encoding="utf-8")))
    assert text == md.read_text(encoding="utf-8")
    assert text.index("| pre | all |") < text.index("| post | all |") < text.index("| pooled | all |")


def test_trial_file_pins_refuse_a_changed_pin(tmp_path, monkeypatch):
    assert set(s4b.TRIAL_PINS) == {*s4.TRIAL_PINS, s4b.AMENDMENT_5_PATH}
    step3.verify_trial_files(REPO_ROOT, s4b.TRIAL_PINS)
    amendment = json.loads((REPO_ROOT / s4b.AMENDMENT_5_PATH).read_text())
    assert amendment["sec_data"]["pins"]["cik_map_sha256"] == s4b.SEC_PINS["cik_map_sha256"]
    assert amendment["sec_data"]["pins"]["file_hash_list_sha256"] == s4b.SEC_PINS["file_hash_list_sha256"]
    assert {k: v for k, v in amendment["sec_data"]["build_code"].items() if k != "commit"} == s4b.BUILD_CODE
    s4b.verify_build_code(REPO_ROOT)
    for path in s4b.TRIAL_PINS:
        monkeypatch.setattr(s4b, "TRIAL_PINS", {**s4b.TRIAL_PINS, path: "0" * 64})
        with pytest.raises(PublicDataRefusal):
            s4b.run(REPO_ROOT, tmp_path / "absent", {"commit": "x", "tracked_changes": False})
        monkeypatch.undo()
