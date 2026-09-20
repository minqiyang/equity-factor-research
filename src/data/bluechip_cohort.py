"""Static 50-stock liquid blue-chip diagnostic cohort.

BLUECHIP_50_COHORT is a fixed current-membership snapshot of 50 liquid
U.S. large-cap symbols. BENCHMARK_SYMBOL identifies the SPY.US comparator.
The cohort is DIAGNOSTIC_ONLY and carries survivorship bias from static
membership. Formal point-in-time universe construction remains a later
Milestone 4 evidence gate.
"""

from __future__ import annotations


BLUECHIP_50_COHORT = [
    "AAPL.US", "MSFT.US", "NVDA.US", "AMZN.US", "GOOGL.US", "META.US", "BRK-B.US", "UNH.US", "JNJ.US", "JPM.US",
    "V.US", "PG.US", "XOM.US", "HD.US", "CVX.US", "MA.US", "LLY.US", "ABBV.US", "MRK.US", "PEP.US",
    "KO.US", "BAC.US", "TMO.US", "WMT.US", "COST.US", "CSCO.US", "MCD.US", "DIS.US", "ACN.US", "ABT.US",
    "ADBE.US", "CRM.US", "LIN.US", "NKE.US", "PFE.US", "CMCSA.US", "DHR.US", "TXN.US", "VZ.US", "PM.US",
    "INTC.US", "AMD.US", "HON.US", "WFC.US", "UPS.US", "QCOM.US", "IBM.US", "CAT.US", "GE.US", "AMGN.US",
]

BENCHMARK_SYMBOL = "SPY.US"


def get_bluechip_50_symbols() -> list[str]:
    """Return a copy of the static 50-stock blue-chip diagnostic cohort."""

    return list(BLUECHIP_50_COHORT)


__all__ = [
    "BENCHMARK_SYMBOL",
    "BLUECHIP_50_COHORT",
    "get_bluechip_50_symbols",
]
