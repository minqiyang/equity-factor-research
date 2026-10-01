"""Milestone 5 step 4b: the as-filed point-in-time rule and the three SEC signals (amendment 5 revision 2).

``parse_companyfacts`` reduces one CIK's companyfacts JSON to the key metadata the frozen rule reads:
for each (concept, unit, start, end) key, its discovery date (the earliest fact among 10-K, 10-KT, 10-K/A,
and 10-KT/A), whether it is amendment-first (every earliest fact is an /A filing), and its first-filed
10-K or 10-KT value. ``fundamentals`` runs the frozen procedure at the date of signal row r - 1:
period discovery, amendment-first classification, value selection, staleness (``as_filed.procedure``).
``signal_value`` adds ME from the anchor filing's share count and the split-only close (R7).

Every missing case carries exactly one typed reason, the first in ``REASON_ORDER`` that applies
(OPUS-S4BF-R2-A2); nothing is filled, clipped, or repaired (R6). ``frame``, ``fy``, and ``fp`` are
never read. No function here reads a file, the network, or a snapshot.
"""

from __future__ import annotations

from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

FAMILY_FORMS = frozenset({"10-K", "10-KT", "10-K/A", "10-KT/A"})
ORIGINAL_FORMS = frozenset({"10-K", "10-KT"})
ANNUAL_DAYS = (350, 380)
STALE_MONTHS = 18
PRICE_ROWS = 10
USD, SHARES = "USD", "shares"

SE = "StockholdersEquity"
NI = "NetIncomeLoss"
ASSETS = "Assets"
PREFERRED = ("PreferredStockValue", "PreferredStockValueOutstanding",
             "PreferredStockIncludingAdditionalPaidInCapitalNetOfDiscount")
GROSS_PROFIT = ("GrossProfit",)
REVENUE = ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet")
COGS = ("CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold")
CSO = "CommonStockSharesOutstanding"
DEI_SHARES = "EntityCommonStockSharesOutstanding"
NEEDED = frozenset({SE, NI, ASSETS, *PREFERRED, *GROSS_PROFIT, *REVENUE, *COGS})

BM, EP, GP_AT = "BM_AF", "EP_AF", "GP_AT_AF"
SIGNALS = (BM, EP, GP_AT)
ANCHOR = {BM: (SE, "instant"), EP: (NI, "flow"), GP_AT: (ASSETS, "instant")}
USES_ME = frozenset({BM, EP})

RANKED = "ranked"
NOT_RANKED = "not_ranked_at_rebalance"
REASON_ORDER = (NOT_RANKED, "identity_unmapped", "identity_ambiguous", "identity_multi_class", "facts_absent",
                "non_usd", "no_annual_fact", "amendment_first", "stale", "concept_missing", "be_nonpositive",
                "assets_nonpositive", "shares_ambiguous", "shares_missing", "price_missing")
PREFERRED_ZERO = "preferred_zero_by_absence"


def first_reason(reasons: Iterable[str]) -> str | None:
    """The first entry of the frozen order among ``reasons`` (OPUS-S4BF-R2-A2); ``None`` when none applies."""
    present = set(reasons)
    unknown = present - set(REASON_ORDER)
    if unknown:
        raise ValueError(f"reason outside the frozen order: {sorted(unknown)}")
    return next((r for r in REASON_ORDER if r in present), None)


# Parsing ---------------------------------------------------------------------------------

@dataclass(frozen=True)
class KeyInfo:
    """One (concept, unit, start, end) key: discovery, amendment-first status, and the first-filed value."""

    concept: str
    unit: str
    start: str | None
    end: str
    discovered: str          # earliest filed date among its 10-K-family facts
    earliest_accn: str       # lowest accn among the facts filed on that date
    amendment_first: bool    # every fact filed on that date is an /A filing
    value: float | None      # the earliest 10-K or 10-KT fact's value (lowest accn on a tie); None if amendment-first
    accn: str | None
    filed: str | None
    value_conflict: bool     # distinct values inside that first-filed tie

    @property
    def is_flow(self) -> bool:
        return self.start is not None


def annual(start: str | None, end: str) -> bool:
    if start is None:
        return False
    days = (pd.Timestamp(end) - pd.Timestamp(start)).days
    return ANNUAL_DAYS[0] <= days <= ANNUAL_DAYS[1]


def key_info(concept: str, unit: str, start: str | None, end: str, facts: list[Mapping[str, Any]]) -> KeyInfo:
    discovered = min(f["filed"] for f in facts)
    at_first = [f for f in facts if f["filed"] == discovered]
    amendment_first = all(f["form"].endswith("/A") for f in at_first)
    earliest_accn = min(f["accn"] for f in at_first)
    value = accn = filed = None
    conflict = False
    if not amendment_first:
        originals = [f for f in facts if f["form"] in ORIGINAL_FORMS]
        first = min(originals, key=lambda f: (f["filed"], f["accn"]))
        tied = {float(f["val"]) for f in originals if (f["filed"], f["accn"]) == (first["filed"], first["accn"])}
        value, accn, filed, conflict = float(first["val"]), first["accn"], first["filed"], len(tied) > 1
    return KeyInfo(concept, unit, start, end, discovered, earliest_accn, amendment_first, value, accn, filed,
                   conflict)


@dataclass
class CompanyFacts:
    """The parsed companyfacts of one CIK: keys of the needed concepts, annual-flow ends by accn, share facts."""

    keys: dict[str, list[KeyInfo]]
    annual_ends_by_accn: dict[str, set[str]]
    dei_shares: dict[str, list[tuple[str, float]]]        # accn -> [(end, value)]
    cso_shares: dict[str, list[tuple[str, float]]]        # accn -> [(end, value)]
    discovery_dates: list[str] = field(default_factory=list)
    _memo: dict[int, dict[str, dict[str, Any]]] = field(default_factory=dict, repr=False)

    @property
    def value_conflicts(self) -> int:
        return sum(k.value_conflict for infos in self.keys.values() for k in infos)


def _share_facts(body: Mapping[str, Any] | None) -> dict[str, list[tuple[str, float]]]:
    out: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for fact in ((body or {}).get("units", {}).get(SHARES, [])):
        out[fact["accn"]].append((fact["end"], float(fact["val"])))
    return dict(out)


def parse_companyfacts(doc: Mapping[str, Any]) -> CompanyFacts:
    """Reduce a companyfacts JSON to what the frozen rule reads. Facts outside the 10-K family are dropped
    here, except the share counts, which are matched by accn."""

    gaap = doc.get("facts", {}).get("us-gaap", {})
    keys: dict[str, list[KeyInfo]] = defaultdict(list)
    ends: dict[str, set[str]] = defaultdict(set)
    dates: set[str] = set()
    for concept, body in gaap.items():
        for unit, facts in body.get("units", {}).items():
            groups: dict[tuple[str | None, str], list[Mapping[str, Any]]] = defaultdict(list)
            for fact in facts:
                if fact.get("form") in FAMILY_FORMS:
                    groups[(fact.get("start"), fact["end"])].append(fact)
            for (start, end), group in groups.items():
                info = key_info(concept, unit, start, end, group)
                if annual(start, end):
                    ends[info.earliest_accn].add(end)
                if concept in NEEDED:
                    keys[concept].append(info)
                    dates.add(info.discovered)
    dei = doc.get("facts", {}).get("dei", {})
    return CompanyFacts(keys=dict(keys), annual_ends_by_accn=dict(ends), dei_shares=_share_facts(dei.get(DEI_SHARES)),
                        cso_shares=_share_facts(gaap.get(CSO)), discovery_dates=sorted(dates))


# The procedure ---------------------------------------------------------------------------

def _qualifies(cf: CompanyFacts, info: KeyInfo) -> bool:
    """Annual flows, and fiscal-year-end instants (end equals an annual flow end first filed in the same accn)."""
    if info.is_flow:
        return annual(info.start, info.end)
    return info.end in cf.annual_ends_by_accn.get(info.earliest_accn, ())


def _pick(infos: list[KeyInfo]) -> KeyInfo:
    """Several keys at one end: the key whose earliest fact was filed first, ties to the lowest accn."""
    return min(infos, key=lambda k: (k.discovered, k.earliest_accn))


def _discovered(cf: CompanyFacts, concept: str, d: str, unit: str = USD) -> list[KeyInfo]:
    return [k for k in cf.keys.get(concept, []) if k.unit == unit and k.discovered < d and _qualifies(cf, k)]


def _anchor(cf: CompanyFacts, concept: str, d: str) -> tuple[KeyInfo | None, str | None]:
    keys = _discovered(cf, concept, d)
    if not keys:
        other = [k for k in cf.keys.get(concept, []) if k.unit != USD and k.discovered < d and _qualifies(cf, k)]
        return None, "non_usd" if other else "no_annual_fact"
    end = max(k.end for k in keys)
    return _pick([k for k in keys if k.end == end]), None


def _chain(cf: CompanyFacts, chain: Iterable[str], d: str, end: str, flow: bool,
           start: str | None = None) -> tuple[str, KeyInfo | None]:
    """The first chain concept with a discovered key at ``end`` decides; a chain never falls through past it.

    Returns ("ok", key), ("amendment_first", key), or ("missing", None). For a flow the key must be annual
    and, when ``start`` is given, share that start.
    """

    for concept in chain:
        keys = [k for k in _discovered(cf, concept, d) if k.end == end and k.is_flow == flow
                and (start is None or k.start == start)]
        if keys:
            key = _pick(keys)
            return ("amendment_first" if key.amendment_first else "ok"), key
    return "missing", None


def _stale(end: str, d: str) -> bool:
    return pd.Timestamp(end) < pd.Timestamp(d) - pd.DateOffset(months=STALE_MONTHS)


def _shares(cf: CompanyFacts, accn: str, filed: str, end_star: str) -> tuple[str | None, float | None, str | None]:
    """(share date s, shares, reason) from the anchor accn (classes_and_signals.shares)."""

    primary = cf.dei_shares.get(accn, [])
    if primary:
        kept = [(e, v) for e, v in primary if e <= filed]
        if not kept:
            return None, None, "shares_missing"
        s = max(e for e, _ in kept)
        values = {v for e, v in kept if e == s}
    else:
        s = end_star
        values = {v for e, v in cf.cso_shares.get(accn, []) if e == end_star}
        if not values:
            return None, None, "shares_missing"
    if len(values) > 1:
        return None, None, "shares_ambiguous"
    value = values.pop()
    return (s, value, None) if value > 0 else (None, None, "shares_missing")


def _fundamental(cf: CompanyFacts, signal: str, d: str) -> dict[str, Any]:
    concept, _ = ANCHOR[signal]
    anchor, reason = _anchor(cf, concept, d)
    if anchor is None:
        return {"reasons": {reason}}
    out: dict[str, Any] = {"reasons": set(), "end": anchor.end, "preferred_zero": False}
    if anchor.amendment_first:
        out["reasons"].add("amendment_first")
    if signal == BM:
        status, pref = _chain(cf, PREFERRED, d, anchor.end, flow=False)
        if status == "amendment_first":
            out["reasons"].add("amendment_first")
        elif not anchor.amendment_first:
            preferred = 0.0 if status == "missing" else pref.value  # type: ignore[union-attr]
            out["preferred_zero"] = status == "missing"
            out["numerator"] = anchor.value - preferred  # type: ignore[operator]
            if out["numerator"] <= 0:
                out["reasons"].add("be_nonpositive")
    elif signal == EP:
        if not anchor.amendment_first:
            out["numerator"] = anchor.value
    else:
        gp = _gross_profit(cf, d, anchor.end)
        if gp[0] != "ok":
            out["reasons"].add(gp[0])
        elif not anchor.amendment_first:
            out["numerator"] = gp[1]
        if not anchor.amendment_first:
            out["denominator"] = anchor.value
            if anchor.value <= 0:  # type: ignore[operator]
                out["reasons"].add("assets_nonpositive")
    if signal in USES_ME and not anchor.amendment_first:
        s, shares, share_reason = _shares(cf, anchor.accn, anchor.filed, anchor.end)  # type: ignore[arg-type]
        if share_reason:
            out["reasons"].add(share_reason)
        out["share_date"], out["shares"] = s, shares
    return out


def _gross_profit(cf: CompanyFacts, d: str, end: str) -> tuple[str, float | None]:
    status, key = _chain(cf, GROSS_PROFIT, d, end, flow=True)
    if status == "ok":
        return "ok", key.value  # type: ignore[union-attr]
    if status == "amendment_first":
        return "amendment_first", None
    rev_status, rev = _chain(cf, REVENUE, d, end, flow=True)
    if rev_status != "ok":
        return ("amendment_first" if rev_status == "amendment_first" else "concept_missing"), None
    cost_status, cost = _chain(cf, COGS, d, end, flow=True, start=rev.start)  # type: ignore[union-attr]
    if cost_status != "ok":
        return ("amendment_first" if cost_status == "amendment_first" else "concept_missing"), None
    return "ok", rev.value - cost.value  # type: ignore[union-attr,operator]


def fundamentals(cf: CompanyFacts, d: str) -> dict[str, dict[str, Any]]:
    """The three signals' filing-side parts at the date ``d`` of row r - 1, before staleness and price.

    Memoized on the filing state: the number of discovery dates before ``d``.
    """

    state = bisect_left(cf.discovery_dates, d)
    if state not in cf._memo:
        cf._memo[state] = {signal: _fundamental(cf, signal, d) for signal in SIGNALS}
    return cf._memo[state]


# Price side --------------------------------------------------------------------------------

@dataclass(frozen=True)
class PricePanel:
    """A segment's split-only close and cumulative split factor (research panels), as numpy arrays."""

    calendar: pd.DatetimeIndex
    columns: pd.Index
    split_close: np.ndarray
    split_factor: np.ndarray

    def market_equity(self, column: int, row: int, share_date: str, shares: float) -> float | None:
        """shares * close(p) * split-only close(r - 1) / split-only close(p); ``None`` without a finite price.

        p is the last row on or before the share date, within the 10 calendar rows ending there, with a
        finite close. ``row`` is r - 1.
        """

        last = int(self.calendar.searchsorted(pd.Timestamp(share_date), side="right")) - 1
        sc_now = self.split_close[row, column]
        if last < 0 or not np.isfinite(sc_now) or not sc_now > 0:
            return None
        for p in range(last, max(last - PRICE_ROWS, -1), -1):
            sc, cs = self.split_close[p, column], self.split_factor[p, column]
            if np.isfinite(sc) and sc > 0 and np.isfinite(cs) and cs > 0:
                raw = sc * cs
                return float(shares * raw * sc_now / sc)
        return None


def signal_value(signal: str, fund: Mapping[str, Any], d: str, prices: PricePanel | None, column: int,
                 row: int) -> tuple[float | None, str | None]:
    """(value, reason) for one member at signal row ``row`` (= r - 1) dated ``d``."""

    reasons = set(fund["reasons"])
    if "end" in fund and _stale(fund["end"], d):
        reasons.add("stale")
    value = None
    if signal in USES_ME and fund.get("share_date") is not None and not reasons:
        me = prices.market_equity(column, row, fund["share_date"], fund["shares"]) if prices else None
        if me is None:
            reasons.add("price_missing")
        else:
            value = fund["numerator"] / me
    elif signal == GP_AT and not reasons:
        value = fund["numerator"] / fund["denominator"]
    reason = first_reason(reasons)
    return (None, reason) if reason else (float(value), None)  # type: ignore[arg-type]
