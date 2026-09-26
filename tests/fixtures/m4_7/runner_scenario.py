"""Committed synthetic fixture universe for the M4.7 stage b-1 runner (plan 7.3 b-1 acceptance).

``build_vendor`` serves 104 random-walk anchors and the special cases the
b-1 acceptance row and T-SUP-5 name: one cash deal, one stock deal at each
accepted lag (-1 and 0), one rename, one unresolved delisting, one two-row
mid-month halt, one missing bar on a reset row, one ticker reuse, one joiner
with prior history, one new listing, one index removal, and one
terminal-reset joiner, plus ``SPY.US`` and the acquirer-only ``ACQ.US``.
``run_pipeline`` drives the merged a-1 retrieval module, the seal script, the
universe build, the terminal tooling, and the census, so the runner reads a
snapshot written by the real stages; ``registration`` fills the Appendix C
document from the census outputs.

The calendar is weekly, so the 252-row warm-up and more than 60 IC months fit
in 591 rows and every engine call stays small. Rows are positions on ``CAL``;
``I_H = 30`` is the first discovery row and ``D0 = 286`` (2008-11-28). The
halt, the reset-row gap, the unresolved delisting, and the terminal-reset
joiner share the month after the reset row 429, so their windows merge into
one peeled window ``[430, 437]`` between two valid segments. No test opens a
network connection or reads private data.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from data import holdout_partition
from fixtures.m4_7.e2e_scenario import retrieve
from m4_7_snapshot_support import Harness, Vendor, bars, entry
from research.m4_7_coverage_census import run_census
from research.m4_7_sp500_pit_rerun import REGISTERED
from research.m4_7_terminal_evidence import CURATED, EVIDENCE_COLUMNS, project, validate, write_template
from research.m4_7_universe_build import build_universe


CAL = pd.date_range("2003-06-06", "2014-09-26", freq="W-FRI", name="date")
N = len(CAL)
I_H = int(CAL.searchsorted(pd.Timestamp("2003-12-31")))
START = "1993-12-15"
BAND, HARD_BAND = (100, 130), (90, 140)
ANCHORS = [f"N{k:03d}" for k in range(1, 105)]
WINDOW_RESET = 429
LAST_BAR = {"CSH": 340, "STK0": 360, "STK1": 380, "OLDN": 400, "UNRES": WINDOW_RESET + 2}
ACQ_CLOSES = {361: 100.0, 380: 90.0}
HALT_ROWS, JOIN_START, JOIN_MISSING = (WINDOW_RESET + 2, WINDOW_RESET + 3), WINDOW_RESET, WINDOW_RESET + 1
RESET_MISSING = WINDOW_RESET + 5
TICK_ONE_END, TICK_ONE_LAST, TICK_TWO_FIRST, TICK_TWO_START = 318, 326, 360, 365
INDEX_REMOVAL_END, PRIOR_START, NEW_LISTING = 470, 480, 500
CONSIDERATION = ("ACQ.US",)


def day(row: int) -> str:
    return CAL[row].date().isoformat()


def walk(seed: int, level: float = 50.0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return level * np.exp(np.cumsum(rng.normal(0.0002, 0.015, N)))


def _bars(row_ids, close, volume=None) -> list[dict[str, Any]]:
    price = (lambda r: float(close[r])) if isinstance(close, np.ndarray) else close
    size = 1000.0 if volume is None else (lambda r: float(volume[r]))
    return bars(row_ids, close=price, volume=size, dates=CAL)


def scenario() -> dict[str, Any]:
    """Entries and per-code responses as plain Python values."""
    entries: list[dict[str, Any]] = []
    codes: dict[str, tuple[Any, Any, Any]] = {}
    everything = range(N)

    def member(code, row_ids, close, *, start=START, end=None, name=None, volume_seed=None):
        entries.append(entry(code, start, end, name=name or f"{code} Inc"))
        volume = None if volume_seed is None else np.random.default_rng(volume_seed).uniform(5e5, 2e6, N)
        codes[f"{code}.US"] = (_bars(list(row_ids), close, volume), [], [])

    for k, code in enumerate(ANCHORS, start=1):
        member(code, everything, walk(k), volume_seed=1000 + k)
    codes["SPY.US"] = (_bars(list(everything), walk(0, 400.0)), [], [])
    codes["ACQ.US"] = (_bars(list(everything), lambda r: ACQ_CLOSES.get(r, 100.0)), [], [])
    member("CSH", range(LAST_BAR["CSH"] + 1), 24.0)
    member("STK0", range(LAST_BAR["STK0"] + 1), 45.0)
    member("STK1", range(LAST_BAR["STK1"] + 1), 45.0)
    member("OLDN", range(LAST_BAR["OLDN"] + 1), 40.0, end=day(LAST_BAR["OLDN"] + 1), name="Rename Co")
    member("NEWN", range(LAST_BAR["OLDN"] + 1, N), 44.0, start=day(LAST_BAR["OLDN"] + 1), name="Rename Co")
    member("UNRES", range(LAST_BAR["UNRES"] + 1), walk(201))
    member("HALT", [r for r in everything if r not in HALT_ROWS], walk(202))
    member("JOIN", [r for r in everything if r != JOIN_MISSING], walk(203), start=day(JOIN_START))
    member("RSTM", [r for r in everything if r != RESET_MISSING], walk(204))
    member("INDX", everything, walk(205), end=day(INDEX_REMOVAL_END))
    member("PRIOR", everything, walk(206), start=day(PRIOR_START))
    member("NEWL", range(NEW_LISTING, N), walk(207), start=day(NEW_LISTING))
    tick = walk(208)
    entries.append(entry("TICK", START, day(TICK_ONE_END), name="Tick One"))
    entries.append(entry("TICK", day(TICK_TWO_START), name="Tick Two"))
    codes["TICK.US"] = (_bars(list(range(TICK_ONE_LAST + 1)) + list(range(TICK_TWO_FIRST, N)), tick), [], [])
    return {"entries": entries, "codes": codes}


def build_vendor() -> Vendor:
    spec = scenario()
    vendor = Vendor(calendar=CAL)
    vendor.entries = spec["entries"]
    for code, (eod, splits, dividends) in spec["codes"].items():
        vendor.code(code, eod, splits, dividends)
    return vendor


def curated_rows() -> list[dict[str, str]]:
    """Curated terminal evidence for the four deals and the rename; UNRES stays uncurated."""

    def row(code, kind, lag, **terms):
        s = LAST_BAR[code] + 1
        base = dict.fromkeys(EVIDENCE_COLUMNS, "")
        base.update({"event_id": f"TE-{code}.US#E1-{day(s)}", "permanent_id": f"{code}.US#E1", "curation_status": "curated",
                     "event_kind": terms.pop("event_kind", "merger_or_acquisition"), "consideration_type": kind,
                     "announcement_date": day(LAST_BAR[code] - 40), "completion_date": day(s + lag),
                     "cash_currency": "USD" if kind == "cash" else "",
                     "source_evidence": "fixture public notice", "curator": "fixture_curator"})
        base.update({key: str(value) for key, value in terms.items()})
        return base

    return [
        row("CSH", "cash", 0, cash_per_share=30),
        row("STK0", "stock", 0, exchange_ratio=0.5, acquirer_permanent_id="ACQ.US#E1"),
        row("STK1", "stock", -1, exchange_ratio=0.5, acquirer_permanent_id="ACQ.US#E1"),
        row("OLDN", "stock", 0, exchange_ratio=1.0, acquirer_permanent_id="NEWN.US#E1", event_kind="rename_or_code_change"),
    ]


def downstream(snapshot_dir: Path, out: Path) -> dict[str, Any]:
    """Universe build, terminal curation and projection, and the census on a retrieved snapshot."""
    build = build_universe(snapshot_dir)
    template = write_template(snapshot_dir)
    curated = {r["permanent_id"]: r for r in curated_rows()}
    merged = [curated.get(r["permanent_id"], {c: r[c] for c in EVIDENCE_COLUMNS}) for r in template.to_dict(orient="records")]
    pd.DataFrame(merged, columns=list(EVIDENCE_COLUMNS)).to_csv(snapshot_dir / CURATED, index=False)
    validation = validate(snapshot_dir)
    project(snapshot_dir)
    census = run_census(snapshot_dir, reports_dir=out / "reports", seal_out=out / "seal" / "m4_7_holdout_seal_v1.json",
                        code_commit="fixture")
    return {"build": build, "validation": validation, "census": census,
            "census_json": out / "reports" / "m4_7_coverage_census.json",
            "seal_record": out / "seal" / "m4_7_holdout_seal_v1.json"}


def run_pipeline(base: Path, monkeypatch) -> dict[str, Any]:
    """Retrieve, seal, build, curate, project, and run the census under ``base`` with a frozen clock."""
    monkeypatch.setattr(holdout_partition, "BAND", BAND)
    monkeypatch.setattr(holdout_partition, "HARD_BAND", HARD_BAND)
    base.mkdir(parents=True, exist_ok=True)
    harness = Harness(base, monkeypatch, snapshot_id="RUN", vendor=build_vendor())
    consideration = base / "consideration_securities.txt"
    consideration.write_text("".join(f"{code}\n" for code in CONSIDERATION))
    retrieve(harness, consideration, REGISTERED["universe"]["calendar_source"])
    return {"harness": harness, "snapshot": harness.snapshot_dir, "base": base,
            **downstream(harness.snapshot_dir, base)}


def registration(result: dict[str, Any], *, o3: str = "proceed_as_registered") -> dict[str, Any]:
    """The Appendix C document for the fixture snapshot: the registered protocol plus the census values."""
    public, census = result["census"]["public"], result["census"]
    identity = public["snapshot_identity"]
    segments = json.loads((result["snapshot"] / "census/segments.json").read_text())
    seal = json.loads(Path(result["seal_record"]).read_text())
    manifest = json.loads((result["snapshot"] / "manifest.json").read_text())
    doc = copy.deepcopy(REGISTERED)
    doc["snapshot"] = {
        "snapshot_id": public["snapshot_id"],
        **{key: identity[key] for key in ("manifest_sha256", "discovery_inputs_sha256", "interval_csv_sha256",
                                          "security_master_sha256", "interval_results_sha256", "engine_events_sha256",
                                          "segments_sha256", "seal_prospective_sha256")},
        "seal_confirmed_sha256": census["seal_confirmed_sha256"], "census_json_sha256": census["census_json_sha256"],
        "retrieval_complete": public["retrieval"]["retrieval_complete"],
        "components_retrieved_utc_date": manifest["snapshot"]["components_retrieved_utc_date"],
    }
    doc["holdout"].update(holdout_start=seal["holdout_start"], holdout_end_exclusive=seal["holdout_end_exclusive"])
    horizon = segments["max_reset_to_reset_rows"]
    doc["discovery"].update(
        first_reset=segments["D0"], last_reset=segments["D_last"], last_ic_month=segments["D_end"],
        ic_month_supply=public["ic_supply"]["ic_month_supply"], max_reset_to_reset_rows=horizon,
        prior_exposure_overlap_fraction={k: v["fraction_of_ic_months"]
                                         for k, v in public["discovery_overlap_with_prior_exposures"].items()})
    doc["common_support"].update(
        gap_window_count=public["exclusion_set"]["gap_window_count"],
        excluded_fraction=public["exclusion_set"]["excluded_fraction"],
        eligible_unpriced_member_day_fraction=public["price_coverage"]["eligible_unpriced_fraction"])
    doc["statistics"]["power_projection"].update(
        kill_reachable_projection=public["power_projection"]["kill_reachable_projection"], owner_decision_o3=o3)
    doc["statistics"]["cpcv"]["holding_periods"] = horizon
    return doc


def write_registration(doc: dict[str, Any], path: Path) -> str:
    """Write the registration and return its SHA-256."""
    payload = (json.dumps(doc, sort_keys=True, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()
