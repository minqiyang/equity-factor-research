"""Milestone 5 step 4b: fail-closed rule F from a permanent security to one SEC CIK (R3).

Rule F (step 4b design note, section 2):

1. Candidates are the CIKs that SEC's current ticker files list for the vendor
   ticker, plus the CIKs whose normalized EDGAR name (current or former) equals
   the normalized vendor name.
2. A candidate survives only if its SEC name or a ``formerNames`` entry matches
   the vendor name, and it filed a 10-K or 10-Q (the /A, 405, and T variants
   included) on a date inside the member window ``[m_in, m_out)``.
3. With more than one survivor, keep those that are a ticker-route CIK or list
   the ticker in their submissions; accept only when exactly one remains.
4. The ID is ambiguous when a unique ticker-route CIK disagrees with the result.

Then, fail closed: an accepted CIK that filed a 20-F or 40-F inside the window
is not accepted (``unmapped``, reason ``foreign_form_in_window``), and a CIK
accepted for more than one permanent ID types every one of them ``multi_class``.
There are no hand overrides, and no predecessor or successor CIK is ever joined
to the accepted one. Every ID ends ``unique``, ``unmapped``, ``ambiguous``, or
``multi_class``, with a reason.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

UNIQUE, UNMAPPED, AMBIGUOUS, MULTI_CLASS = "unique", "unmapped", "ambiguous", "multi_class"
STATUSES = (UNIQUE, UNMAPPED, AMBIGUOUS, MULTI_CLASS)
PERIODIC = frozenset(f"{form}{suffix}" for form in ("10-K", "10-Q", "10-K405", "10-KT", "10-QT")
                     for suffix in ("", "/A"))
FOREIGN = frozenset({"20-F", "20-F/A", "40-F", "40-F/A"})
OPEN_END = "9999-12-31"

SUFFIX = re.compile(r"\b(INCORPORATED|INC|CORPORATION|CORP|COMPANY|CO|LIMITED|LTD|PLC|LLC|LP|L P|NV|N V|SA|AG|SE|"
                    r"HOLDINGS?|GROUP|THE|CLASS [A-Z]|CL [A-Z]|COMMON STOCK|COM|NEW|DEL|DE|/[A-Z]{2}/?)\b")


def norm(name: str) -> str:
    """Upper case, '&' as AND, state tags and punctuation removed, and corporate suffixes dropped."""

    text = str(name).upper().replace("&", " AND ")
    text = re.sub(r"/[A-Z]{2,3}/?$", " ", text)
    text = re.sub(r"[^A-Z0-9 ]", " ", text)
    text = SUFFIX.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def ticker_of(vendor_code: str) -> str:
    """The exchange ticker of a vendor code: the exchange suffix and any reuse tag ``_old<n>`` removed."""

    root = vendor_code.rsplit(".", 1)[0]
    return re.sub(r"_old\d*$", "", root).upper()


@dataclass(frozen=True)
class Filer:
    """What rule F reads from one CIK's submissions: normalized names, current tickers, and (form, date) filings."""

    names: frozenset[str]
    tickers: frozenset[str]
    filings: tuple[tuple[str, str], ...]

    def filed_in(self, forms: frozenset[str], m_in: str, m_out: str) -> bool:
        end = m_out or OPEN_END
        return any(form in forms and m_in <= date < end for form, date in self.filings)


def filer_from_submissions(main: Mapping[str, Any], pages: Iterable[Mapping[str, Any]]) -> Filer:
    """A ``Filer`` from a submissions JSON and every history page it lists (the caller supplies all pages)."""

    names = [main.get("name", "")] + [entry.get("name", "") for entry in main.get("formerNames", [])]
    filings: list[tuple[str, str]] = []
    for block in (main["filings"]["recent"], *pages):
        forms, dates = block.get("form", []), block.get("filingDate", [])
        if len(forms) != len(dates):
            raise ValueError("submissions block has unequal form and filingDate lengths")
        filings.extend(zip(forms, dates))
    return Filer(frozenset(n for n in (norm(x) for x in names) if n),
                 frozenset(str(t).upper() for t in main.get("tickers", []) if t), tuple(filings))


@dataclass(frozen=True)
class SecIndex:
    """Ticker -> CIKs from both current ticker files, and normalized EDGAR name -> CIKs."""

    by_ticker: Mapping[str, frozenset[int]]
    by_name: Mapping[str, frozenset[int]]


def build_index(company_tickers: Mapping[str, Any], company_tickers_exchange: Mapping[str, Any],
                cik_lookup_text: str) -> SecIndex:
    by_ticker: dict[str, set[int]] = defaultdict(set)
    for row in company_tickers.values():
        by_ticker[str(row["ticker"]).upper()].add(int(row["cik_str"]))
    fields = company_tickers_exchange["fields"]
    cik_at, ticker_at = fields.index("cik"), fields.index("ticker")
    for row in company_tickers_exchange["data"]:
        by_ticker[str(row[ticker_at]).upper()].add(int(row[cik_at]))
    by_name: dict[str, set[int]] = defaultdict(set)
    for line in cik_lookup_text.splitlines():
        parts = line.rsplit(":", 2)
        if len(parts) == 3 and parts[1].isdigit():
            key = norm(parts[0])
            if key:
                by_name[key].add(int(parts[1]))
    return SecIndex({k: frozenset(v) for k, v in by_ticker.items()}, {k: frozenset(v) for k, v in by_name.items()})


@dataclass(frozen=True)
class Security:
    """One eligible permanent ID: vendor code and name, and its member window [m_in, m_out) (blank = open)."""

    permanent_id: str
    vendor_code: str
    vendor_name: str
    m_in: str
    m_out: str


@dataclass(frozen=True)
class Candidates:
    ticker: str
    name: str
    ticker_ciks: tuple[int, ...]
    name_ciks: tuple[int, ...]

    @property
    def pool(self) -> tuple[int, ...]:
        return tuple(sorted(set(self.ticker_ciks) | set(self.name_ciks)))


def candidates(security: Security, index: SecIndex) -> Candidates:
    ticker, name = ticker_of(security.vendor_code), norm(security.vendor_name)
    return Candidates(ticker, name, tuple(sorted(index.by_ticker.get(ticker, ()))),
                      tuple(sorted(index.by_name.get(name, ()))) if name else ())


@dataclass(frozen=True)
class Outcome:
    status: str
    cik: int | None
    reason: str


def rule_f(security: Security, cand: Candidates, filers: Mapping[int, Filer | None]) -> Outcome:
    """Rule F for one ID. ``filers`` holds every pool CIK; ``None`` means SEC has no submissions for it."""

    def name_ok(cik: int) -> bool:
        filer = filers[cik]
        return filer is not None and cand.name in filer.names

    def periodic_in(cik: int) -> bool:
        filer = filers[cik]
        return filer is not None and filer.filed_in(PERIODIC, security.m_in, security.m_out)

    pool = cand.pool
    if not pool:
        return Outcome(UNMAPPED, None, "no_candidate")
    survivors = [c for c in pool if name_ok(c) and periodic_in(c)]
    if not survivors:
        reason = "name_mismatch" if not any(name_ok(c) for c in pool) else "no_periodic_filing_in_window"
        return Outcome(UNMAPPED, None, reason)
    if len(survivors) > 1:
        kept = [c for c in survivors
                if c in cand.ticker_ciks or cand.ticker in filers[c].tickers]  # type: ignore[union-attr]
        if len(kept) != 1:
            return Outcome(AMBIGUOUS, None, "several_survivors")
        survivors = kept
    cik = survivors[0]
    if len(cand.ticker_ciks) == 1 and cand.ticker_ciks[0] != cik:
        return Outcome(AMBIGUOUS, None, "ticker_cik_disagrees")
    if filers[cik].filed_in(FOREIGN, security.m_in, security.m_out):  # type: ignore[union-attr]
        return Outcome(UNMAPPED, None, "foreign_form_in_window")
    return Outcome(UNIQUE, cik, "accepted")


def windows_overlap(a: Security, b: Security) -> bool:
    return a.m_in < (b.m_out or OPEN_END) and b.m_in < (a.m_out or OPEN_END)


def map_securities(securities: Iterable[Security], index: SecIndex,
                   filers: Mapping[int, Filer | None]) -> dict[str, Outcome]:
    """Rule F for every ID, then every ID that shares its accepted CIK with another ID becomes ``multi_class``.

    The ``multi_class`` reason records whether the sharing IDs' member windows overlap.
    """

    rows = {s.permanent_id: s for s in securities}
    outcomes = {pid: rule_f(s, candidates(s, index), filers) for pid, s in rows.items()}
    by_cik: dict[int, list[str]] = defaultdict(list)
    for pid, outcome in outcomes.items():
        if outcome.status == UNIQUE:
            by_cik[outcome.cik].append(pid)  # type: ignore[index]
    for pids in by_cik.values():
        if len(pids) < 2:
            continue
        for pid in pids:
            overlap = any(windows_overlap(rows[pid], rows[other]) for other in pids if other != pid)
            outcomes[pid] = Outcome(MULTI_CLASS, None, "shared_cik_overlapping" if overlap else "shared_cik_disjoint")
    return outcomes
