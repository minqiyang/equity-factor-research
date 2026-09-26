"""Committed synthetic end-to-end snapshot fixture for M4.7 stage a-2 (plan 7.2 a-2 acceptance).

``build_vendor`` returns the fake vendor: components JSON, symbol lists, the
index calendar, and per-code ``eod``, ``splits``, and ``div`` responses.
``run_pipeline`` drives the merged a-1 retrieval module, the seal script, the
universe build, the terminal tooling, the common support, and the census, so
the fixture flows from components JSON to a confirmed seal. Rows are positions
on ``m4_7_snapshot_support.CAL``; ``I_H = 152`` is the first discovery row and
``D0 = 412``.

The fixture carries every case the a-2 acceptance row names: one cash, one
stock at lag 0, one stock at lag -1, one mixed, and one evidenced-worthless
event; a rename under each vendor behavior with its re-keyed candidate; a
two-episode code with a split only in its second episode; post-final-bar
splits under each convention on one- and two-episode codes; an omitted split;
a reverse split cancelled by a dividend; dividends carried back without a
split; an undeclared and an unapplied in-span split; prior-close dividends;
same-pair split and distribution cases; repeated small undeclared steps; an
exact repeat and a genuine overlap; one episode with two exit classes; a
delisted member on a reused listed code; a 404 member; a member whose reused
code trades years later; a persistent split provider error; an episode ending
in the holdout decade with a later discovery split; an episode continuous
across ``holdout_end``; and the Round 2 and Round 3 peeling joiners.
"""

from __future__ import annotations

import json
import math

from pathlib import Path
from typing import Any

import pandas as pd

from data import holdout_partition
from m4_7_snapshot_support import CAL, I_H, Harness, Vendor, bars, day, entry, rows
from research.m4_7_common_support import write_support_files
from research.m4_7_coverage_census import run_census
from research.m4_7_holdout_seal import seal_snapshot
from research.m4_7_terminal_evidence import CURATED, EVIDENCE_COLUMNS, project, validate, write_template
from research.m4_7_universe_build import build_universe


N = len(CAL)
START = "1993-12-15"
BAND, HARD_BAND = (15, 60), (10, 80)
ANCHORS = [f"A{k:02d}" for k in range(1, 11)]
TARGETS = {"CSH": (600, 24.0), "STK0": (620, 45.0), "STK1": (640, 45.0), "MIX": (660, 25.0), "WRT": (680, 10.0)}
ACQ_CLOSES = {621: 100.0, 640: 90.0, 661: 80.0}
EP1, EP2 = rows(420, 546), rows(580, N)
PEEL_OLD_MISSING, JOIN_MISSING, JOIN2_MISSING = 510, 509, 508
A03_DIVIDENDS = (250, 313, 376, 439, 502, 565, 628, 691, 754, 817)
CONSIDERATION = ("ACQ.US",)


def anchor_close(k: int):
    return lambda r: 50.0 + 5.0 * k + 3.0 * math.sin((r + 7 * k) / 11.0)


def _dividend_factor(close, dividend_rows, rate=0.01):
    """Prior-close factors: ``D(t)`` and the per-row amounts ``rate * close(t - 1)``."""
    amounts = {d: rate * close(d - 1) for d in dividend_rows}

    def factor(r):
        value = 1.0
        for d, amount in amounts.items():
            if d > r:
                value *= 1.0 - amount / close(d - 1)
        return value

    return factor, amounts


def scenario() -> dict[str, Any]:
    """Entries, symbol lists, and per-code responses as plain Python values."""
    entries: list[dict[str, Any]] = []
    codes: dict[str, tuple[Any, Any, Any]] = {}

    for k, code in enumerate(ANCHORS, start=1):
        entries.append(entry(code, START, name=f"Anchor {k} Inc"))
        close = anchor_close(k)
        kept = [r for r in rows(0, N) if not (code == "A02" and r == PEEL_OLD_MISSING)]
        if code == "A03":
            factor, amounts = _dividend_factor(close, (60, *A03_DIVIDENDS))
            dividends = [{"date": day(d), "value": a, "unadjustedValue": a} for d, a in sorted(amounts.items())]
            codes[f"{code}.US"] = (bars(kept, close=close, adjusted=lambda r: close(r) * factor(r)), [], dividends)
        else:
            codes[f"{code}.US"] = (bars(kept, close=close, volume=1000.0 + 10 * k), [], [])
    codes["SPY.US"] = (bars(rows(0, N), close=lambda r: 400.0 + math.sin(r / 13.0)), [], [])
    codes["ACQ.US"] = (bars(rows(0, N), close=lambda r: ACQ_CLOSES.get(r, 100.0)), [], [])
    for code, (last, price) in TARGETS.items():
        entries.append(entry(code, START, name=f"Target {code} Inc"))
        codes[f"{code}.US"] = (bars(rows(0, last + 1), close=price), [], [])

    entries += [entry("OLDN", START, day(701), name="Rename Co"), entry("NEWN", day(701), name="Rename Co")]
    codes["OLDN.US"] = (bars(rows(0, 701), close=40.0), [], [])
    codes["NEWN.US"] = (bars(rows(701, N), close=44.0), [], [])
    entries += [entry("RKO", START, day(750), name="Rekey Corp"), entry("RKN", day(750), name="Rekey Inc")]
    codes["RKO.US"] = (b"[]", [], [])
    codes["RKN.US"] = (bars(rows(0, N), close=70.0), [], [])

    def two_entries(code):
        return [entry(code, day(425), day(520), name=f"{code} One"), entry(code, day(585), name=f"{code} Two")]

    entries += two_entries("TWO")
    two = bars(EP1) + bars(EP2, close=lambda r: 100.0 if r < 700 else 50.0, adjusted=50.0,
                           volume=lambda r: 2000.0 if r < 700 else 1000.0)
    codes["TWO.US"] = (two, [{"date": day(40), "split": "2/1"}, {"date": day(700), "split": "2/1"}], [])

    late = rows(430, 601)
    entries += [entry("PFU", day(435), day(560)), entry("PFA", day(435), day(560))]
    codes["PFU.US"] = (bars(late), [{"date": day(605), "split": "2/1"}], [])
    codes["PFA.US"] = (bars(late, adjusted=50.0, volume=2000.0), [{"date": day(605), "split": "2/1"}], [])
    second = rows(590, 701)
    for code in ("RE2S", "RE2U"):
        entries += [entry(code, day(425), day(520), name=f"{code} One"), entry(code, day(595), day(680), name=f"{code} Two")]
    codes["RE2S.US"] = (bars(EP1 + second, adjusted=50.0, volume=2000.0), [{"date": day(705), "split": "2/1"}], [])
    codes["RE2U.US"] = (bars(EP1) + bars(second, adjusted=50.0, volume=2000.0), [{"date": day(705), "split": "2/1"}], [])

    entries += two_entries("OMIT")
    grow = lambda r: 100.0 * math.exp(0.001 * (r - EP1[0]))  # noqa: E731
    codes["OMIT.US"] = (bars(EP1, close=grow, adjusted=lambda r: grow(r) / 2, volume=2000.0) + bars(rows(590, N)), [], [])
    entries += two_entries("CANC")
    cancel = bars(rows(590, N), close=lambda r: 100.0 if r < 650 else (200.0 if r == 650 else 100.0), adjusted=100.0,
                  volume=lambda r: 500.0 if r < 650 else 1000.0)
    codes["CANC.US"] = (bars(EP1, volume=500.0) + cancel, [{"date": day(650), "split": "1/2"}],
                        [{"date": day(651), "value": 100.0, "unadjustedValue": 100.0}])
    entries += two_entries("CARB")
    carb_rows = (600, 650, 700, 750)
    carried = lambda r: 0.99 ** sum(d > r for d in carb_rows)  # noqa: E731
    codes["CARB.US"] = (bars(EP1, adjusted=lambda r: 100.0 * carried(r)) + bars(rows(590, N), adjusted=lambda r: 100.0 * carried(r)),
                        [], [{"date": day(d), "value": 1.0, "unadjustedValue": 1.0} for d in carb_rows])

    span = rows(430, N)
    entries += [entry(code, day(435)) for code in ("UNDS", "DNAP", "SDSP", "SDS3")]
    codes["UNDS.US"] = (bars(span, close=lambda r: 100.0 if r < 700 else 100.0 / 1.1, adjusted=100.0 / 1.1,
                             volume=lambda r: 1100.0 if r < 700 else 1000.0), [], [])
    codes["DNAP.US"] = (bars(span), [{"date": day(700), "split": "2/1"}], [])
    codes["SDSP.US"] = (bars(span, close=lambda r: 100.0 if r < 700 else 49.0, adjusted=49.0,
                             volume=lambda r: 2000.0 if r < 700 else 1000.0), [{"date": day(700), "split": "2/1"}],
                        [{"date": day(700), "value": 1.0, "unadjustedValue": 1.0}])
    codes["SDS3.US"] = (bars([r for r in span if not 850 <= r <= 854], close=lambda r: 100.0 if r < 850 else 49.0,
                             adjusted=49.0, volume=lambda r: 2000.0 if r < 850 else 1000.0),
                        [{"date": day(852), "split": "2/1"}],
                        [{"date": day(850), "value": 1.0, "unadjustedValue": 1.0},
                         {"date": day(853), "value": 0.5, "unadjustedValue": 0.5}])
    small = rows(430, 590)
    entries.append(entry("SMAL", day(435), day(560)))
    codes["SMAL.US"] = (bars(small, adjusted=lambda r: 100.0 * 1.0009 ** (r - 589), volume=lambda r: 1000.0 * 1.0009 ** (589 - r)),
                        [], [])

    entries += [entry("DUPE", START), entry("DUPE", START)]
    codes["DUPE.US"] = (bars(rows(0, N), close=33.0), [], [])
    entries += [entry("OVLP", START, day(700)), entry("OVLP", day(600))]
    codes["OVLP.US"] = (bars(rows(0, N), close=34.0), [], [])
    entries += [entry("REPEAT", day(425), day(520)), entry("REPEAT", day(600))]
    codes["REPEAT.US"] = (bars(rows(420, 801), close=35.0), [], [])
    entries += [entry("RUS", day(425), day(480), name="Old Railroad", delisted=True),
                entry("RUS", day(820), name="New Software")]
    codes["RUS.US"] = (bars(rows(800, N), close=36.0), [], [])
    entries.append(entry("GONE", START, day(500), delisted=True))
    codes["GONE.US"] = (404, 404, 404)
    entries.append(entry("YRS", day(425), day(480), name="Years Old"))
    codes["YRS.US"] = (bars(rows(880, N), close=37.0), [], [])
    entries.append(entry("PPE", START))
    codes["PPE.US"] = (bars(rows(0, N), close=38.0), 500, [])
    entries.append(entry("HEND", START, day(90)))
    codes["HEND.US"] = (bars(rows(0, 101), close=39.0), [{"date": day(500), "split": "2/1"}], [])
    entries.append(entry("CROSS", day(50), day(I_H + 30)))
    codes["CROSS.US"] = (bars(rows(0, N), close=41.0), [], [])
    entries += [entry("JOIN", "2005-05-12"), entry("JOIN2", "2005-05-11")]
    codes["JOIN.US"] = (bars([r for r in span if r != JOIN_MISSING], close=42.0), [], [])
    codes["JOIN2.US"] = (bars([r for r in span if r != JOIN2_MISSING], close=43.0), [], [])

    listed = [{"Code": "RUS", "Name": "New Software", "Exchange": "NYSE", "Type": "Common Stock", "Isin": "US0000000009"}]
    delisted = [{"Code": "RUS", "Name": "Old Railroad", "Exchange": "NYSE", "Type": "Common Stock", "Isin": None}]
    return {"entries": entries, "codes": codes, "listed": listed, "delisted": delisted}


def perturb_holdout_rows(codes: dict[str, tuple[Any, Any, Any]]) -> dict[str, tuple[Any, Any, Any]]:
    """Change every holdout-dated value; make one price, one split ratio, and one dividend value invalid."""
    holdout_end = CAL[I_H]
    changed = {}
    for code, (eod, splits, dividends) in codes.items():
        if isinstance(eod, list):
            eod = [({**row, **{f: row[f] * 1.01 for f in ("open", "high", "low", "close", "adjusted_close")},
                     "volume": row["volume"] + 7.0} if pd.Timestamp(row["date"]) < holdout_end else row) for row in eod]
            if code == "CROSS.US":
                eod[100] = {**eod[100], "adjusted_close": 0.0}
        if isinstance(splits, list):
            splits = [({**row, "split": "0/1" if code == "TWO.US" else "3/1"} if pd.Timestamp(row["date"]) < holdout_end
                       else row) for row in splits]
        if isinstance(dividends, list):
            dividends = [({**row, "value": "n/a" if code == "A03.US" else row["value"] * 1.1}
                          if pd.Timestamp(row["date"]) < holdout_end else row) for row in dividends]
        changed[code] = (eod, splits, dividends)
    return changed


def build_vendor(*, perturb_holdout: bool = False, perturb_discovery: bool = False) -> Vendor:
    spec = scenario()
    codes = perturb_holdout_rows(spec["codes"]) if perturb_holdout else spec["codes"]
    if perturb_discovery:
        eod, splits, dividends = codes["A05.US"]
        eod = list(eod)
        eod[700] = {**eod[700], "close": eod[700]["close"] + 0.5, "high": eod[700]["high"] + 0.5,
                    "open": eod[700]["open"] + 0.5, "low": eod[700]["low"] + 0.5, "adjusted_close": eod[700]["adjusted_close"] + 0.5}
        codes = {**codes, "A05.US": (eod, splits, dividends)}
    vendor = Vendor()
    vendor.entries, vendor.listed, vendor.delisted = spec["entries"], spec["listed"], spec["delisted"]
    for code, (eod, splits, dividends) in codes.items():
        vendor.code(code, eod, splits, dividends)
    return vendor


def curated_rows() -> list[dict[str, str]]:
    """The fixture's curated terminal evidence, as a curator would enter it from public documents."""

    def row(code, kind, lag, **terms):
        last = TARGETS[code][0] if code in TARGETS else 700
        s = last + 1
        base = dict.fromkeys(EVIDENCE_COLUMNS, "")
        base.update({"event_id": f"TE-{code}.US#E1-{day(s)}", "permanent_id": f"{code}.US#E1", "curation_status": "curated",
                     "event_kind": terms.pop("event_kind", "merger_or_acquisition"), "consideration_type": kind,
                     "announcement_date": day(last - 40), "completion_date": day(s + lag),
                     "cash_currency": "USD" if kind in ("cash", "mixed") else "",
                     "source_evidence": "fixture public notice", "curator": "fixture_curator"})
        base.update({key: str(value) for key, value in terms.items()})
        return base

    return [
        row("CSH", "cash", 0, cash_per_share=30),
        row("STK0", "stock", 0, exchange_ratio=0.5, acquirer_permanent_id="ACQ.US#E1"),
        row("STK1", "stock", -1, exchange_ratio=0.5, acquirer_permanent_id="ACQ.US#E1"),
        row("MIX", "mixed", 0, cash_per_share=10, exchange_ratio=0.25, acquirer_permanent_id="ACQ.US#E1"),
        row("WRT", "evidenced_worthless", 0, event_kind="bankruptcy_or_liquidation"),
        row("OLDN", "stock", 0, exchange_ratio=1.0, acquirer_permanent_id="NEWN.US#E1", event_kind="rename_or_code_change"),
    ]


def retrieve(harness: Harness, consideration_file: Path) -> None:
    """Retrieval through the seal: ``components``, ``symbols``, seal, ``calendar``, and the three tables."""
    assert harness.run("components") == 0 and harness.run("symbols") == 0
    seal_snapshot(harness.snapshot_dir, sealing_actor="coordinator", authorization_reference="fixture-log-entry",
                  clock=harness.clock)
    assert harness.run("calendar") == 0
    assert harness.run("splits", "--codes", str(consideration_file)) == 0
    for _ in range(3):
        assert harness.run("splits") == 0
        harness.clock.advance(days=1)
    for table in ("eod", "dividends"):
        assert harness.run(table) == 0
    harness.run("verify")


def downstream(snapshot_dir: Path, out: Path) -> dict[str, Any]:
    """Universe build, terminal tooling, common support, and census on a retrieved snapshot."""
    build = build_universe(snapshot_dir)
    write_template(snapshot_dir)
    template = pd.read_csv(snapshot_dir / "terminal/terminal_evidence_template.csv", dtype=str, keep_default_na=False)
    curated = {r["permanent_id"]: r for r in curated_rows()}
    merged = [curated.get(r["permanent_id"], {c: r[c] for c in EVIDENCE_COLUMNS}) for r in template.to_dict(orient="records")]
    pd.DataFrame(merged, columns=list(EVIDENCE_COLUMNS)).to_csv(snapshot_dir / CURATED, index=False)
    report = validate(snapshot_dir)
    project(snapshot_dir)
    support = write_support_files(snapshot_dir)
    census = run_census(snapshot_dir, reports_dir=out / "reports", seal_out=out / "seal" / "m4_7_holdout_seal_v1.json",
                        code_commit="fixture")
    return {"build": build, "validation": report, "support": support, "census": census}


def run_pipeline(base: Path, monkeypatch, *, perturb_holdout: bool = False, perturb_discovery: bool = False) -> dict[str, Any]:
    """Run the fixture end to end under ``base``; every run uses the same frozen clock sequence."""
    monkeypatch.setattr(holdout_partition, "BAND", BAND)
    monkeypatch.setattr(holdout_partition, "HARD_BAND", HARD_BAND)
    base.mkdir(parents=True, exist_ok=True)
    harness = Harness(base, monkeypatch, snapshot_id="E2E",
                      vendor=build_vendor(perturb_holdout=perturb_holdout, perturb_discovery=perturb_discovery))
    consideration = base / "consideration_securities.txt"
    consideration.write_text("".join(f"{code}\n" for code in CONSIDERATION))
    retrieve(harness, consideration)
    result = downstream(harness.snapshot_dir, base)
    return {"harness": harness, "snapshot": harness.snapshot_dir, "base": base, **result}



def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text())
