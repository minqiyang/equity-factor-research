"""Synthetic SEC inputs for the Milestone 5 step 4b tests.

Companyfacts documents are built in memory in the SEC JSON layout: one 10-K a year per company, filed in
March, with its prior-year comparatives, a dei cover share count, and frame, fy, and fp fields the rule must
ignore. The CIK map follows the data-build columns. Every value is synthetic; no test reads the SEC cache,
a snapshot row, or the network.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

import m5_step4_support as fx
import research.m5_sec_identity as ident
import research.m5_sec_signals as sig
import research.m5_step4 as s4
import research.m5_step4b as s4b
import research.m5_step4b_data as dm

YEARS = range(2007, 2017)
CIK_OF = {asset: 1000 + k for k, asset in enumerate(fx.ASSETS)}
UNMAPPED, AMBIGUOUS, MULTI, ABSENT = fx.ASSETS[1], fx.ASSETS[2], (fx.ASSETS[3], fx.ASSETS[4]), fx.ASSETS[5]
NO_GP = fx.ASSETS[6]              # reports Revenues and CostOfRevenue instead of GrossProfit
BANK = fx.ASSETS[7]               # Revenues only: GP_AT_AF is concept_missing
FALLBACK_SHARES = fx.ASSETS[8]    # no dei cover count: CommonStockSharesOutstanding at E*
NEGATIVE_BE = fx.ASSETS[9]        # BE <= 0 in some years


def accn(cik: int, year: int, seq: int = 1) -> str:
    return f"{cik:010d}-{year % 100:02d}-{seq:06d}"


def fact(val: float, end: str, filed: str, accession: str, form: str = "10-K", start: str | None = None,
         **extra: Any) -> dict[str, Any]:
    out = {"end": end, "val": val, "accn": accession, "fy": int(filed[:4]), "fp": "FY", "form": form, "filed": filed}
    if start is not None:
        out["start"] = start
    out.update(extra)
    return out


def document(us_gaap: dict[str, dict[str, list[dict]]], dei_shares: list[dict] | None = None) -> dict[str, Any]:
    facts: dict[str, Any] = {"us-gaap": {c: {"units": units} for c, units in us_gaap.items()}}
    if dei_shares is not None:
        facts["dei"] = {sig.DEI_SHARES: {"units": {"shares": dei_shares}}}
    return {"cik": 1, "entityName": "synthetic", "facts": facts}


def fy(year: int) -> tuple[str, str]:
    return f"{year}-01-01", f"{year}-12-31"


def company(asset: str, filed: dict[int, str] | None = None) -> dict[str, Any]:
    """Annual 10-Ks for ``YEARS`` with comparatives; ``filed`` overrides a fiscal year's filing date."""

    k = fx.ASSETS.index(asset)
    cik = CIK_OF[asset]
    rng = np.random.default_rng(100 + k)
    se = {y: 1e9 * (1 + 0.1 * k) * (1 + 0.05 * (y - 2007)) * rng.uniform(0.9, 1.1) for y in YEARS}
    if asset == NEGATIVE_BE:
        se = {y: (-5e8 if y % 3 == 0 else v) for y, v in se.items()}
    ni = {y: 0.08 * abs(se[y]) * rng.normal(1.0, 0.8) for y in YEARS}
    assets = {y: 2.5 * abs(se[y]) for y in YEARS}
    gp = {y: 0.3 * assets[y] * rng.uniform(0.5, 1.5) for y in YEARS}
    units: dict[str, list[dict]] = {c: [] for c in (sig.SE, sig.NI, sig.ASSETS, "GrossProfit", "Revenues",
                                                     "CostOfRevenue", sig.CSO)}
    dei = []
    for y in YEARS:
        year_filed = (filed or {}).get(y, f"{y + 1}-03-{1 + k % 20:02d}")
        a = accn(cik, y + 1)
        for yy in (y - 1, y):                                     # the filing year and its comparative
            if yy not in se:
                continue
            start, end = fy(yy)
            units[sig.SE].append(fact(se[yy], end, year_filed, a, frame=f"CY{yy}Q4I"))
            units[sig.ASSETS].append(fact(assets[yy], end, year_filed, a))
            units[sig.NI].append(fact(ni[yy], end, year_filed, a, start=start, frame=f"CY{yy}"))
            if asset == NO_GP:
                units["Revenues"].append(fact(3 * gp[yy], end, year_filed, a, start=start))
                units["CostOfRevenue"].append(fact(2 * gp[yy], end, year_filed, a, start=start))
            elif asset == BANK:
                units["Revenues"].append(fact(3 * gp[yy], end, year_filed, a, start=start))
            else:
                units["GrossProfit"].append(fact(gp[yy], end, year_filed, a, start=start))
        if asset == FALLBACK_SHARES:
            units[sig.CSO].append(fact(1e8, fy(y)[1], year_filed, a))
        else:
            cover = (pd.Timestamp(year_filed) - pd.Timedelta(days=10)).date().isoformat()
            dei.append(fact(1e8 * (1 + 0.01 * k), cover, year_filed, a))
    return document({c: {"USD" if c != sig.CSO else "shares": v} for c, v in units.items() if v}, dei)


def identity() -> pd.DataFrame:
    rows = []
    for asset in fx.ASSETS:
        status, reason, cik = ident.UNIQUE, "accepted", f"{CIK_OF[asset]:010d}"
        if asset == UNMAPPED:
            status, reason, cik = ident.UNMAPPED, "name_mismatch", ""
        elif asset == AMBIGUOUS:
            status, reason, cik = ident.AMBIGUOUS, "several_survivors", ""
        elif asset in MULTI:
            status, reason, cik = ident.MULTI_CLASS, "shared_cik_overlapping", ""
        rows.append({"permanent_id": asset, "vendor_code": asset.split("#")[0], "segments": "pre;post",
                     "exit_class": "index_removal_still_trading", "status": status, "reason": reason, "cik": cik})
    return pd.DataFrame(rows, columns=dm.MAP_COLUMNS)


def sec_inputs(overrides: dict[str, dict[str, Any]] | None = None) -> s4b.SecInputs:
    """``overrides`` maps an asset to a replacement companyfacts document."""

    table = identity()
    facts: dict[int, sig.CompanyFacts | None] = {}
    for row in table.to_dict(orient="records"):
        if row["status"] != ident.UNIQUE:
            continue
        cik = int(row["cik"])
        if row["permanent_id"] == ABSENT:
            facts[cik] = None
            continue
        doc = (overrides or {}).get(row["permanent_id"]) or company(row["permanent_id"])
        facts[cik] = sig.parse_companyfacts(doc)
    return s4b.SecInputs(identity=table, facts=facts)


def public9() -> s4.PublicInputs:
    """The step 4 synthetic public inputs plus be_me, ni_me, gp_at and the Value and Quality class returns."""

    public = fx.public()
    rng = np.random.default_rng(21)
    months = public.jkp.index
    jkp = public.jkp.copy()
    for char in ("be_me", "ni_me", "gp_at"):
        jkp[char] = rng.normal(0.002, 0.02, len(months))
    classes = public.class_values.copy()
    for theme in s4b.SEC_THEMES:
        classes[theme] = rng.normal(0.002, 0.02, len(classes))
    return s4.PublicInputs(rf=public.rf, multipliers=public.multipliers, class_values=classes, jkp=jkp,
                           nets=public.nets, last_month=public.last_month, manifest=[])
