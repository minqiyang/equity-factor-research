"""Synthetic tests for the Milestone 5.5 driver (card m55-driver).

Every WRDS table is generated here; no test reads the WRDS folder or opens a network connection. The small world
runs every stage from the coverage counts to the frozen shortlist digest. The real-size world (about 500 members
at a time on about 7,900 business days) runs only when M55_DRIVER_REAL_SIZE=1 and prints its run time.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import time
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pytest

import research.m55_driver as d
import research.m55_wrds_loader as w
from research import m55_criteria as crit
from research import m55_index_tilt as tilt
from research import m55_signals as sig
from research.m4_7_sp500_pit_rerun import RunnerStop


pytestmark = pytest.mark.xdist_group("m55_driver")

VINTAGE = "2025-12-31"
OPEN = pd.Timestamp(VINTAGE)                  # a spell open at the vintage end: exit class current
TRACKED = {"vintage": VINTAGE, "files": {}}
MU, K, VOL = 0.0005, 0.03, 0.008              # daily drift MU - K x share growth: S7 (sign -1) predicts returns
DATA_START_FACT = pd.Timestamp("1960-12-01")  # before the first calendar row: basis_unseen data_start
IBES_FROM = pd.Timestamp("1990-06-15")        # S1 real start 1991: 24 screen months, a typed undefined record
PERMNO = re.compile(r"(?<![\d.])9000[0-9]{2}(?![\d])")


def sparse_calendar(first: str, dense_to: str, last: str) -> pd.DatetimeIndex:
    """Business days to ``dense_to`` (so a 252-row window fills before 1963-06), then three rows a month."""
    days = pd.bdate_range(first, last)
    dense, late = days[days <= pd.Timestamp(dense_to)], days[days > pd.Timestamp(dense_to)]
    rows = pd.Series(late, index=late)
    month = late.to_period("M")
    mid = late.day >= 15
    keep = set(rows.groupby(month).min()) | set(rows.groupby(month).max()) | set(rows[mid].groupby(month[mid]).min())
    return dense.append(pd.DatetimeIndex(sorted(keep))).rename("date")


CAL = sparse_calendar("1961-01-03", "1963-06-28", "1993-02-26")


def row(cal: pd.DatetimeIndex, date: str) -> pd.Timestamp:
    """The first calendar row on or after ``date``."""
    return cal[cal.searchsorted(pd.Timestamp(date))]


def month_end(cal: pd.DatetimeIndex, month: str) -> pd.Timestamp:
    return cal[cal.to_period("M") == pd.Period(month, "M")][-1]


@dataclass(frozen=True)
class Member:
    permno: int
    g: float                                   # annual growth of the split-adjusted share count
    listed: pd.Timestamp | None = None         # first daily row (default: the first calendar row)
    spell: tuple | None = None                 # index spell (default: listed to OPEN)
    last: pd.Timestamp | None = None           # the dlydelflg = 'Y' row of a delisting
    delist: tuple | None = None                # (delactiontype, delreasontype, delpaymenttype)
    y_return: float = math.nan
    split: pd.Timestamp | None = None          # a 2-for-1 split row
    gp: pd.Timestamp | None = None             # a row with a price and no return (CIZ GP): path_break on the next
    facts_from: pd.Timestamp | None = None     # first share fact (default: the data_start fact)
    drift: float | None = None                 # daily drift (default MU - K g)
    vol: float = VOL


def small_members(cal: pd.DatetimeIndex) -> list[Member]:
    r = lambda date: row(cal, date)            # noqa: E731
    return [
        Member(900001, 0.02, split=r("1980-03-01")),
        Member(900002, -0.03), Member(900003, 0.10), Member(900004, 0.00),
        Member(900005, 0.05, gp=month_end(cal, "1975-06")),                      # break spans 1975-06 and 07
        Member(900006, 0.08),
        Member(900007, 0.04, spell=(cal[0], r("1975-03-01"))),                    # left_index, keeps trading
        Member(900008, -0.01, last=r("1979-08-15"), delist=("MER", "UNAV", "CASH"), y_return=0.25),
        Member(900009, 0.06, last=month_end(cal, "1983-05"), delist=("GDR", "BKPY", "UNAV")),   # B2 at r
        Member(900010, 0.03, last=r("1986-04-15"), delist=("GLI", "UNAV", "PRCF"), y_return=-1.0),
        Member(900011, 0.07, last=r("1988-09-15"), delist=("MER", "UNAV", "STK")),              # unknown
        Member(900012, 0.01, facts_from=r("1966-03-01")),                         # no_share_fact before
        Member(900013, -0.02, listed=r("1970-02-01"), facts_from=r("1970-02-01")),               # new listing
        Member(900014, 0.09),
        Member(900015, 0.11, spell=(r("1975-03-15"), OPEN)),
        Member(900016, -0.04, spell=(r("1979-09-01"), OPEN)),
        Member(900017, 0.12, spell=(r("1983-06-01"), OPEN)),
        Member(900018, 0.015, spell=(r("1986-05-01"), OPEN)),
    ]


def share_facts(m: Member, cal: pd.DatetimeIndex, factor: pd.Series) -> pd.DataFrame:
    """One fact a year (first row of March) with the raw count on its basis row; the first at ``facts_from``."""
    first = m.facts_from if m.facts_from is not None else DATA_START_FACT
    starts = [first] + [row(cal, f"{y}-03-01") for y in range(max(first.year + 1, 1962), cal[-1].year + 1)
                        if pd.Timestamp(f"{y}-03-01") <= factor.index[-1]]
    out = []
    for k, start in enumerate(starts):
        basis = factor.index[factor.index.searchsorted(start)]
        adjusted = 1000.0 * (1.0 + m.g) ** (start.year - 1960)
        end = starts[k + 1] - pd.Timedelta(days=1) if k + 1 < len(starts) else OPEN
        out.append({"permno": m.permno, "shrstartdt": start, "shrenddt": end, "shrout": adjusted / factor[basis]})
    return pd.DataFrame(out)


def member_rows(m: Member, cal: pd.DatetimeIndex, rng: np.random.Generator) -> pd.DataFrame:
    listed = m.listed if m.listed is not None else cal[0]
    dates = cal[(cal >= listed) & (cal <= (m.last if m.last is not None else cal[-1]))]
    drift = MU - K * m.g if m.drift is None else m.drift
    ret = rng.normal(drift, m.vol, len(dates))
    factor = np.where(dates < m.split, 2.0, 1.0) if m.split is not None else np.ones(len(dates))
    adjusted = 1000.0 * (1.0 + m.g) ** (dates.year - 1960)
    table = pd.DataFrame({"permno": m.permno, "dlycaldt": dates, "dlyret": ret,
                          "dlyprc": 20.0 * np.cumprod(1.0 + ret) * factor, "dlydelflg": "N",
                          "dlycumfacpr": factor, "dlycumfacshr": factor, "dlyfacprc": 1.0,
                          "shrout": np.round(adjusted / factor), "dlyvol": 100.0, "primaryexch": "N",
                          "dlyprcflg": "TR"})
    table.loc[table.index[1::50], "dlyprcflg"] = "BA"
    table["dlyprevdt"] = table["dlycaldt"].shift(1)
    table.loc[0, "dlyret"] = np.nan                       # a new security has no first return
    if m.split is not None:
        table.loc[table["dlycaldt"] == m.split, "dlyfacprc"] = 2.0
    if m.gp is not None:
        table.loc[table["dlycaldt"] == m.gp, "dlyret"] = np.nan
    if m.last is not None:
        last = table.index[-1]
        table.loc[last, ["dlydelflg", "dlyret"]] = ["Y", m.y_return]
        table.loc[last, ["dlycumfacpr", "dlycumfacshr", "shrout"]] = np.nan
    return table


def world_frames(members: list[Member], cal: pd.DatetimeIndex, seed: int = 7,
                 comp: tuple[int, ...] = (900001, 900002)) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    dsf = [member_rows(m, cal, rng) for m in members]
    facts = [share_facts(m, cal, t.set_index("dlycaldt")["dlycumfacshr"].ffill()) for m, t in zip(members, dsf)]
    permnos = [m.permno for m in members]
    spells = pd.DataFrame([{"permno": m.permno, "indno": 1000502,
                            "mbrstartdt": (m.spell or (m.listed or cal[0], OPEN))[0],
                            "mbrenddt": m.last if m.last is not None else (m.spell or (None, OPEN))[1]}
                           for m in members])
    delists = pd.DataFrame([{"permno": m.permno, "delactiontype": m.delist[0], "delreasontype": m.delist[1],
                             "delpaymenttype": m.delist[2]} for m in members if m.delist],
                           columns=["permno", "delactiontype", "delreasontype", "delpaymenttype"])
    info = pd.DataFrame({"permno": permnos, "ticker": [f"T{p}" for p in permnos],
                         "secinfostartdt": pd.Timestamp("1960-01-01"), "secinfoenddt": OPEN})
    index = pd.DataFrame({"indno": 1000200, "dlycaldt": cal, "dlytotret": rng.normal(0.0004, 0.008, len(cal)),
                          "dlyprcret": 0.0})
    legacy = pd.DataFrame({"caldt": cal, "vwretd": rng.normal(0.0004, 0.008, len(cal)), "sprtrn": 9.0})
    link = pd.DataFrame({"gvkey": [f"G{p}" for p in permnos], "lpermno": [float(p) for p in permnos],
                         "linkdt": pd.Timestamp("1960-01-01"), "linkenddt": pd.NaT})
    quarters = pd.date_range("1977-03-31", "1982-12-31", freq="QE")
    fundq = pd.DataFrame([{"gvkey": f"G{p}", "datadate": q, "fyearq": q.year, "ajexq": 1.0}
                          for p in comp for q in quarters])
    urq = pd.DataFrame([{"gvkey": f"G{p}", "datadate": q, "fqtr": float(q.quarter), "rdq": q + pd.Timedelta(days=25),
                         "prelimqprd": q + pd.Timedelta(days=30), "finalqprd": q + pd.Timedelta(days=60),
                         "epspxq": 1.0 + 0.1 * rng.standard_normal(), "ajexq": 1.0} for p in comp for q in quarters])
    split_quarter = (urq["gvkey"] == f"G{comp[0]}") & (urq["datadate"] == pd.Timestamp("1979-12-31"))
    urq.loc[split_quarter, ["rdq", "prelimqprd"]] = [pd.Timestamp("1980-02-25"), pd.Timestamp("1980-03-05")]
    years = pd.date_range("1994-12-31", "1995-12-31", freq="YE")
    snapshot = pd.DataFrame([{"gvkey": f"G{comp[0]}", "datadate": y, "fyear": float(y.year),
                              "pitdate1": y + pd.Timedelta(days=80), **{k: 1.0 for k in sig.ANNUAL_ITEMS}}
                             for y in years])
    alive = [m.permno for m in members if m.last is None or m.last >= IBES_FROM]
    months = pd.date_range(IBES_FROM - pd.Timedelta(days=14), cal[-1], freq="MS") + pd.Timedelta(days=14)
    ibes = pd.DataFrame([{"ticker": f"T{p}", "statpers": s, "fpedats": pd.Timestamp(f"{s.year}-12-31"), "fpi": "1",
                          "meanest": 2.0 + 0.01 * k + 0.02 * rng.standard_normal(), "curcode": "USD"}
                         for p in alive for k, s in enumerate(months)])
    ibes_link = pd.DataFrame({"ticker": [f"T{p}" for p in alive], "permno": alive,
                              "sdate": pd.Timestamp("1990-01-01"), "edate": pd.NaT, "score": 1.0})
    return {"crsp_dsf_v2": pd.concat(dsf, ignore_index=True), "crsp_stkshares": pd.concat(facts, ignore_index=True),
            "crsp_stkdelists": delists, "crsp_stksecurityinfohist": info, "crsp_dsp500list_v2": spells,
            "crsp_index_daily": index, "crsp_dsp500_legacy": legacy, "ccm_lnkhist": link, "comp_fundq": fundq,
            "comp_urq": urq, "comp_snapshot_csa_pit": snapshot, "ibes_statsumu_epsus": ibes,
            "ibes_crsp_link": ibes_link}


def to_arrow(table: pd.DataFrame) -> pa.Table:
    out = pa.Table.from_pandas(table.reset_index(drop=True), preserve_index=False)
    for k, f in enumerate(out.schema):
        if pa.types.is_timestamp(f.type):
            out = out.set_column(k, f.name, out.column(k).cast(pa.timestamp("ns")).cast(pa.date32()))
    return out


def make_data(frames: dict[str, pd.DataFrame]) -> w.WrdsData:
    return w.WrdsData({k: to_arrow(v) for k, v in frames.items()}, {"vintage": VINTAGE, "code": "0" * 64,
                                                                     "files": {}})


def perturb_after(frames: dict[str, pd.DataFrame], after: pd.Timestamp, seed: int = 11) -> dict[str, pd.DataFrame]:
    """Change every value dated after ``after``; keep the NaN pattern, the Y rows, and the delisting structure."""
    rng = np.random.default_rng(seed)
    out = {k: v.copy() for k, v in frames.items()}
    dsf = out["crsp_dsf_v2"]
    late = (dsf["dlycaldt"] > after) & (dsf["dlydelflg"] != "Y")
    dsf.loc[late, "dlyret"] = dsf.loc[late, "dlyret"] + rng.normal(0.0, 0.03, int(late.sum()))
    dsf.loc[late, "dlyprc"] = dsf.loc[late, "dlyprc"] * 1.3
    dsf.loc[late, "dlyvol"] = 7.0
    facts = out["crsp_stkshares"]
    facts.loc[facts["shrstartdt"] > after, "shrout"] *= 1.7
    for stem, column, value in (("crsp_index_daily", "dlycaldt", "dlytotret"), ("crsp_dsp500_legacy", "caldt", "vwretd")):
        table = out[stem]
        hit = table[column] > after
        table.loc[hit, value] = rng.normal(0.0, 0.05, int(hit.sum()))
    ibes = out["ibes_statsumu_epsus"]
    ibes.loc[ibes["statpers"] > after, "meanest"] += 0.5
    urq = out["comp_urq"]
    urq.loc[urq["datadate"] > after, "epspxq"] -= 0.4
    snapshot = out["comp_snapshot_csa_pit"]
    snapshot.loc[snapshot["datadate"] > after, "at"] = 9.0
    return out


def run_chain(data: w.WrdsData, out: Path) -> dict[str, str]:
    return {stage: d.run_stage(stage, data, out, TRACKED) for stage in d.STAGES}


def stage(out: Path, name: str) -> dict:
    return json.loads((out / f"{name}.json").read_text())["result"]


def copy_until(chain: dict, folder: Path, name: str) -> Path:
    """A copy of the small-world stage folder without stage ``name`` and the stages after it."""
    out = folder / "out"
    shutil.copytree(chain["w0"]["folder"], out)
    for later in d.STAGES[d.STAGES.index(name):]:
        for suffix in (".json", ".sha256"):
            (out / f"{later}{suffix}").unlink()
    (out / "shortlist_digest.txt").unlink(missing_ok=True)
    return out


def rechain(out: Path, edit) -> None:
    """Apply ``edit(stage, payload)`` to each stage file in order, then renew its digest and the chain after it."""
    digests: dict[str, str] = {}
    for name in d.STAGES:
        path = out / f"{name}.json"
        if not path.exists():
            break
        payload = json.loads(path.read_text())
        edit(name, payload)
        payload["previous"] = dict(digests)
        text = json.dumps(payload, sort_keys=True, indent=1) + "\n"
        path.write_text(text)
        digests[name] = d.sha256_bytes(text.encode())
        (out / f"{name}.sha256").write_text(digests[name] + "\n")


def set_calibration(decision: str):
    def edit(name: str, payload: dict) -> None:
        if name == "calibration":
            payload["result"]["decision"] = decision
    return edit


@pytest.fixture(scope="module")
def frames() -> dict[str, pd.DataFrame]:
    return world_frames(small_members(CAL), CAL)


@pytest.fixture(scope="module")
def chain(frames, tmp_path_factory) -> dict:
    """The small world through every stage, and the same world with every value after 1992-12-31 changed."""
    out = {}
    for name, world in (("w0", frames), ("w2", perturb_after(frames, pd.Timestamp("1992-12-31")))):
        folder = tmp_path_factory.mktemp(name) / "out"
        begin = time.perf_counter()
        digests = run_chain(make_data(world), folder)
        out[name] = {"folder": folder, "digests": digests, "seconds": time.perf_counter() - begin}
    print(f"small-world chain: {out['w0']['seconds']:.1f} s")
    return out


# Trial file and context --------------------------------------------------------------------

def test_check_trial_accepts_the_frozen_file_and_refuses_a_changed_rule() -> None:
    trial, _ = d.load_trial()
    changed = json.loads(json.dumps(trial))
    changed["books"]["tilt"]["weight"] = changed["books"]["tilt"]["weight"].replace("TILT_STRENGTH = 0.5",
                                                                                    "TILT_STRENGTH = 0.6")
    with pytest.raises(RunnerStop) as caught:
        d.check_trial(changed)
    assert caught.value.reason == "trial_rule_mismatch" and "TILT_STRENGTH" in caught.value.detail
    for edit, name in ((lambda t: t["books"]["costs"]["SCREEN_COST_SCHEDULE"][1].__setitem__(1, 11.0),
                        "SCREEN_COST_SCHEDULE"),
                       (lambda t: t["screen_and_shortlist"]["shortlist_rule"].__setitem__("ir_min", 0.1),
                        "shortlist rule"),
                       (lambda t: t["candidates"]["list"][6].__setitem__("sign", 1), "signs"),
                       (lambda t: t["code_pins"]["research/m55_criteria.py"].__setitem__("file_sha256", "0" * 64),
                        "code pin research/m55_criteria.py")):
        changed = json.loads(json.dumps(trial))
        edit(changed)
        with pytest.raises(RunnerStop) as caught:
            d.check_trial(changed)
        assert caught.value.detail == name


def test_the_trial_file_must_have_the_frozen_bytes(tmp_path: Path) -> None:
    """One changed byte refuses, also where ``check_trial`` alone accepts the change (the HAC lag rule)."""
    assert d.load_trial()[1] == d.TRIAL_SHA256
    raw = (d.REPO / d.TRIAL_FILE).read_bytes()
    changed = raw.replace(b"floor(4 (n / 100)^(2/9))", b"floor(5 (n / 100)^(2/9))", 1)
    assert len(changed) == len(raw) and changed != raw
    d.check_trial(json.loads(changed))
    (tmp_path / d.TRIAL_FILE).parent.mkdir(parents=True)
    (tmp_path / d.TRIAL_FILE).write_bytes(changed)
    with pytest.raises(RunnerStop) as caught:
        d.load_trial(tmp_path)
    assert caught.value.reason == "trial_digest_mismatch"


def test_stated_reads_each_written_form() -> None:
    assert d.stated("max |w - b| <= cap + 1e-12 (CAP_TOLERANCE) in", "CAP_TOLERANCE") == 1e-12
    assert d.stated("in at most 100 passes (RENORMALIZE_LOOPS), else", "RENORMALIZE_LOOPS") == 100
    assert d.stated("w = b x (1 + TILT_STRENGTH x c), TILT_STRENGTH = 0.5", "TILT_STRENGTH") == 0.5
    assert d.stated("TE_TOLERANCE 1e-9; BUDGET_TOLERANCE 1e-12", "TE_TOLERANCE") == 1e-9
    with pytest.raises(RunnerStop):
        d.stated("no value here", "STOCK_CAP")


def test_clean_types_every_value() -> None:
    assert d.clean({"a": np.float64("nan"), "b": pd.NaT, "c": np.datetime64("1990-01-31"), "d": pd.Period("1990-01"),
                    "e": (np.int64(2), np.bool_(True)), "f": pd.Timestamp("1991-02-28")}) == {
        "a": None, "b": None, "c": "1990-01-31", "d": "1990-01", "e": [2, True], "f": "1991-02-28"}
    with pytest.raises(RunnerStop):
        d.clean({"x": object()})


def test_run_log_masks_identifiers_in_refusal_text() -> None:
    assert d.masked("KeyError: '900003' at 0.123456 on 1992-12-31, 12 names") == \
        "KeyError: '<id>' at 0.123456 on 1992-12-31, 12 names"


def test_context_digest_covers_every_module(tmp_path: Path) -> None:
    for folder in d.CODE_FOLDERS:
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "a.py").write_text("x = 1\n")
    before = d.code_digest(tmp_path)
    (tmp_path / "src" / "a.py").write_text("x = 2\n")
    assert d.code_digest(tmp_path) != before


# Gates (R9) -----------------------------------------------------------------------------------

def test_chain_writes_each_stage_with_its_digest_and_chain(chain) -> None:
    out = chain["w0"]["folder"]
    for k, name in enumerate(d.STAGES):
        raw = (out / f"{name}.json").read_bytes()
        assert (out / f"{name}.sha256").read_text().strip() == d.sha256_bytes(raw) == chain["w0"]["digests"][name]
        assert json.loads(raw)["previous"] == {s: chain["w0"]["digests"][s] for s in d.STAGES[:k]}
    assert (out / "shortlist_digest.txt").read_text().strip() == stage(out, "freeze")["digest_sha256"]


@pytest.mark.parametrize("damage, reason", [
    ("missing", "stage_missing"), ("tampered", "stage_digest_mismatch"), ("context", "stage_context_mismatch"),
    ("chain", "stage_chain_mismatch")])
def test_a_later_stage_refuses_unless_earlier_outputs_exist_and_match(chain, frames, tmp_path, damage,
                                                                      reason) -> None:
    out = tmp_path / "out"
    shutil.copytree(chain["w0"]["folder"], out)
    for name in ("screen", "freeze"):
        for suffix in (".json", ".sha256"):
            (out / f"{name}{suffix}").unlink()
    look = out / "look.json"
    if damage == "missing":
        look.unlink()
    elif damage == "tampered":
        look.write_text(look.read_text().replace('"blank_month_count"', '"blank_month_count_x"'))
    else:
        payload = json.loads(look.read_text())
        if damage == "context":
            payload["context"]["code_sha256"] = "0" * 64
        else:
            payload["previous"]["coverage"] = "0" * 64
        text = json.dumps(payload, sort_keys=True, indent=1) + "\n"
        look.write_text(text)
        (out / "look.sha256").write_text(d.sha256_bytes(text.encode()) + "\n")
    with pytest.raises(RunnerStop) as caught:
        d.run_stage("screen", make_data(frames), out, TRACKED)
    assert caught.value.reason == reason
    assert json.loads((out / "run_log.jsonl").read_text().splitlines()[-1])["refused"] == reason


def test_a_stage_output_is_never_overwritten_and_needs_a_folder_outside_git(chain, frames, tmp_path) -> None:
    with pytest.raises(RunnerStop) as caught:
        d.run_stage("look", make_data(frames), chain["w0"]["folder"], TRACKED)
    assert caught.value.reason == "stage_output_exists"
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    with pytest.raises(RunnerStop) as caught:
        d.run_stage("coverage", make_data(frames), tmp_path / "repo" / "out", TRACKED)
    assert caught.value.reason == "output_inside_checkout"
    with pytest.raises(RunnerStop) as caught:
        d.run_stage("coverage", make_data(frames), tmp_path / "other", {"vintage": VINTAGE, "files": {"x": {
            "rows": 1, "sha256": "0"}}})
    assert caught.value.reason == "data_manifest_mismatch"


@pytest.mark.parametrize("decision, goes_on", [
    ("chosen", True), ("ratio_coverage_low", True), ("refused", False), ("ratio_coverage_ambiguous", False),
    ("no_g_reaches_target", False)])
def test_each_calibration_decision_goes_on_or_stops(decision, goes_on) -> None:
    if goes_on:
        d.check_calibration({"decision": decision})
        return
    with pytest.raises(RunnerStop) as caught:
        d.check_calibration({"decision": decision})
    assert (caught.value.reason, caught.value.detail) == ("calibration_stop", f"calibration decision {decision}")


@pytest.mark.parametrize("name", ["look", "screen", "freeze"])
def test_look_screen_and_freeze_refuse_after_a_calibration_stop(chain, frames, tmp_path, name) -> None:
    data = make_data(frames)
    for decision in ("refused", "ratio_coverage_ambiguous", "no_g_reaches_target"):
        out = copy_until(chain, tmp_path / decision, name)
        rechain(out, set_calibration(decision))
        with pytest.raises(RunnerStop) as caught:
            d.run_stage(name, data, out, TRACKED)
        assert (caught.value.reason, caught.value.detail) == ("calibration_stop", f"calibration decision {decision}")
        assert not (out / f"{name}.json").exists()
        assert json.loads((out / "run_log.jsonl").read_text().splitlines()[-1])["refused"] == "calibration_stop"


def test_the_sequence_goes_on_after_chosen_and_ratio_coverage_low(chain, frames, tmp_path) -> None:
    """The small world's own decision is ratio_coverage_low (its chain ran on); a saved chosen also goes on."""
    assert stage(chain["w0"]["folder"], "calibration")["decision"] == "ratio_coverage_low"
    out = copy_until(chain, tmp_path, "freeze")
    rechain(out, set_calibration("chosen"))
    d.run_stage("freeze", make_data(frames), out, TRACKED)
    assert stage(out, "freeze")["record"] == stage(chain["w0"]["folder"], "freeze")["record"]


def test_a_refusal_inside_the_calibration_writes_no_file(chain, frames, tmp_path, monkeypatch) -> None:
    """``calibrate_lowrisk`` raises the refusal of a g below the first g that meets: no file, so the look stops."""
    out = copy_until(chain, tmp_path, "calibration")

    def refused(*args, **kwargs):
        raise tilt.refuse("g_refused", "a refusal below the first g that meets")
    monkeypatch.setattr(tilt, "calibrate_lowrisk", refused)
    data = make_data(frames)
    with pytest.raises(RunnerStop):
        d.run_stage("calibration", data, out, TRACKED)
    assert not (out / "calibration.json").exists()
    with pytest.raises(RunnerStop) as caught:
        d.run_stage("look", data, out, TRACKED)
    assert caught.value.reason == "stage_missing"


def test_the_freeze_parses_no_data_table(chain, tmp_path, monkeypatch) -> None:
    """The freeze checks the file bytes against the manifest and writes the same file as the chain."""
    out = copy_until(chain, tmp_path, "freeze")
    root = tmp_path / "wrds"
    root.mkdir()
    (root / w.MANIFEST).write_text(json.dumps({"vintage": VINTAGE, "files": {}}))

    def parsed(*args, **kwargs):
        raise AssertionError("the freeze parsed a data table")
    for module, name in ((w, "load"), (w, "frame"), (w.pq, "read_table")):
        monkeypatch.setattr(module, name, parsed)
    d.run_stage("freeze", d.stage_data("freeze", root), out, TRACKED)
    assert (out / "freeze.json").read_bytes() == (chain["w0"]["folder"] / "freeze.json").read_bytes()
    # The bytes of each listed file are hashed, never read as a table; one changed byte refuses.
    (root / "part.parquet").write_bytes(b"not a table")
    record = {"rows": 1, "sha256": d.sha256_bytes(b"not a table")}
    (root / w.MANIFEST).write_text(json.dumps({"vintage": VINTAGE, "files": {"part.parquet": record}}))
    assert d.data_files(root).manifest["files"] == {"part.parquet": record}
    (root / "part.parquet").write_bytes(b"not a tablE")
    with pytest.raises(RunnerStop) as caught:
        d.data_files(root)
    assert caught.value.reason == "hash_mismatch"


def test_frozen_shortlist_and_decision(chain) -> None:
    out = chain["w0"]["folder"]
    frozen = stage(out, "freeze")
    record = frozen["record"]
    assert frozen["decision"] == "shortlist_frozen" and frozen["shortlist"] == ["S7"]
    assert crit.verify_frozen_screen(record, (out / "shortlist_digest.txt").read_text().strip())
    assert crit.shortlist_digest(record) == frozen["digest_sha256"]
    s7 = record["candidates"]["S7"]
    assert s7["status"] == "ok" and s7["first_month"] == "1964-01" and s7["last_month"] == "1992-12"
    assert s7["information_ratio"] >= crit.IR_MIN and s7["hac_t"] >= crit.T_MIN
    assert s7["blank_months"] == {"1975-06": d.BLANK, "1975-07": d.BLANK}
    assert s7["months"] == len(pd.period_range("1964-01", "1992-12", freq="M")) - 2


def test_no_stage_uses_a_value_after_1992(chain) -> None:
    """Every value dated after 1992-12-31 changes, and every stage file stays byte for byte the same."""
    assert chain["w2"]["digests"] == chain["w0"]["digests"]


def test_coverage_and_calibration_compute_no_return(chain, frames, tmp_path, monkeypatch) -> None:
    """Coverage and calibration run with the book runner, the criteria statistics, and vwretd made to raise, and
    write the same files; their results hold no return statistic (they run before any book return)."""
    def computed(*args, **kwargs):
        raise AssertionError("a book return or a return statistic was computed")
    for module, names in ((tilt, ("run_book", "run_index_tilt", "book_summary", "monthly_returns", "active_summary")),
                          (crit, ("screen_record", "check_paired", "check_series", "annual_mean", "annual_vol",
                                  "hac_t", "mean_test", "drawdown_episodes")),
                          (d, ("monthly_vwretd", "engine_pair", "mean_gap"))):
        for name in names:
            monkeypatch.setattr(module, name, computed)
    data = make_data(frames)
    for name in ("coverage", "calibration"):
        d.run_stage(name, data, tmp_path / "out", TRACKED)
        assert (tmp_path / "out" / f"{name}.json").read_bytes() == (chain["w0"]["folder"] / f"{name}.json").read_bytes()
    out = chain["w0"]["folder"]
    for name in ("coverage", "calibration"):
        text = json.dumps(stage(out, name))
        for key in ("monthly_net", "annual_mean", "annual_active_mean", "information_ratio", "annual_mean_gap"):
            assert f'"{key}"' not in text
    look = stage(out, "look")
    assert set(look["runs"]["primary"]["primary"]) == {"cw_vs_vwretd", "r4", "cw_annual_turnover",
                                                        "cw_annual_cost_drag"}


def test_outputs_hold_no_permno_ticker_or_engine_fragility_field(chain) -> None:
    for path in chain["w0"]["folder"].iterdir():
        text = path.read_text()
        assert not PERMNO.search(text), path.name
        assert "fragile_active_sign" not in text and "fragile_lowrisk_active_sign" not in text


# Coverage, calibration, look, and screen reports ------------------------------------------------

def test_coverage_counts_real_starts_and_s7_early_rows(chain) -> None:
    result = stage(chain["w0"]["folder"], "coverage")
    starts = {s: result["signals"][s]["real_start"] for s in sig.SIGNAL_IDS}
    assert starts == {"S1": 1991, "S2": None, "S3": None, "S4": None, "S5": None, "S6": None, "S7": 1964,
                      "S8": None}
    s7 = result["s7_early"]
    assert s7["1963-01"]["valid"] == 0 and s7["1963-01"]["reasons"] == {"missing_item": s7["1963-01"]["members"]}
    assert s7["1963-01"]["basis_unseen_at_anchor_12"] == s7["1963-01"]["members"] - 1    # one has no fact yet
    assert s7["1964-12"]["valid_share"] >= 0.8
    basis = result["me_coverage"]["basis_unseen_member_days_to_1992"]["data_start"]
    assert basis["last"] < "1962-08-01" and sum(basis["by_year"].values()) > 0
    assert result["signals"]["S2"]["basis_quarters_by_year"]["1980"]["changed"] == 1
    assert result["data_span"]["first_full_window_rebalance"] <= "1963-05-31"
    assert set(result["signals"]["S7"]["reason_share_by_exit_class"]["valid"]) == set(w.EXIT_CLASSES)


def test_calibration_runs_once_on_the_primary_panel_with_its_r6_split(chain, frames) -> None:
    result = stage(chain["w0"]["folder"], "calibration")
    data = make_data(frames)
    assert result["panel_sha256"] == d.frames_digest(d.frames_for(data, "primary"), month_end(CAL, "1992-12"))
    assert result["panel_rows"]["last"] == str(month_end(CAL, "1992-12").date())
    assert result["start"] == str(month_end(CAL, "1963-05").date())
    assert result["end"] == str(month_end(CAL, "1992-11").date())
    assert result["rebalances"] == len(pd.period_range("1963-07", "1992-12", freq="M"))
    assert len(result["grid"]) == len(tilt.LOWRISK_GRID)
    # The gap members come back by exit class from the same rebalance_members windows (the break of 900005).
    assert result["gap_rebalances"] > 0 and result["max_ratio_gap_cw_share"] > 0
    assert result["r6_by_exit_class"]["gap_members"]["current"] == result["ratio_gap_members"]


def test_look_blank_set_and_declarations(chain) -> None:
    out = chain["w0"]["folder"]
    look = stage(out, "look")
    for run in d.RUNS:
        part = look["runs"][run]
        assert part["blank_months"] == ["1975-06", "1975-07"]
        (position,) = part["positions"]
        assert position["break_row"] == str(row(CAL, "1975-07-01").date())
        assert position["previous_valid_row"] == str(row(CAL, "1975-06-15").date())
        assert position["exit_class"] == "current" and position["weight_at_last_rebalance"]["cw"] > 0
        blanked = part["blanked_level_windows"]
        assert blanked["windows"] == blanked["by_exit_class"]["current"] == len(blanked["each"]) > 0
        assert blanked["each"][0]["rebalance"] == str(month_end(CAL, "1975-07").date())   # r - 1 after W
        assert all(e["break_rows"] == [str(row(CAL, "1975-07-01").date())] for e in blanked["each"])
        assert part["primary"]["cw_vs_vwretd"]["blank_months"] == {"1975-06": d.BLANK, "1975-07": d.BLANK}
        assert part["coverage"]["b2"]["rebalances"] == 1
    # Each criteria output is logged with its declaration, which equals the run set cut to its span.
    entries = [json.loads(x) for x in (out / "run_log.jsonl").read_text().splitlines()]
    calls = [e for e in entries if "call" in e]
    assert {e["call"] for e in calls} == {"check_paired", "screen_record", "undefined_record", "freeze_shortlist"}
    for e in calls:
        if e["call"] != "freeze_shortlist":
            first, last = (pd.Period(m, "M") for m in e["span"])
            expected = {m: d.BLANK for m in look["runs"][e["run"]]["blank_months"] if first <= pd.Period(m, "M") <= last}
            assert e["declaration"] == expected and e["output"].get("blank_months", {}) == expected


def test_screen_reports_r4_two_calls_counts_and_tilt_stats(chain) -> None:
    screen = stage(chain["w0"]["folder"], "screen")
    s7 = screen["candidates"]["S7"]
    for run in d.RUNS:
        for case in d.CASES:
            item = s7["records"][run][case]
            assert item["screen_record"]["status"] == "ok"
            assert set(item["tilt_stats"]["turnover_by_year"]["active"]) == {str(y) for y in range(1963, 1993)}
            r4 = item["r4"]["cw"]
            assert r4["held"] == sum(c["held"] for c in r4["by_cause"].values()) == 4
    primary, rerun = s7["records"]["primary"]["primary"]["r4"]["cw"], s7["records"]["last_close"]["primary"]["r4"]["cw"]
    assert primary["by_cause"]["cash_merger"]["ciz_return_in_path"] == 1
    assert primary["by_cause"]["failure"]["supplied_terminal_return"] == 1
    assert primary["by_cause"]["failure"]["missing_engine_default"] == 1
    assert primary["by_cause"]["unknown"]["missing_engine_default"] == 1
    assert rerun["by_cause"]["failure"] == {**{k: primary["by_cause"]["failure"][k] for k in (
        "held", "weight_at_last_rebalance_sum")}, "settled_at_last_close": 2}
    assert set(s7["fragility"]["primary"]) == {"tilt_vs_cw", "tilt_vs_vwretd", "cw_vs_vwretd"}
    # Each fragility value is the mean in the record of its own run (the two runs differ in every case).
    for case in d.CASES:
        for key, (part, field) in {"tilt_vs_cw": ("screen_record", "annual_active_mean"),
                                   "tilt_vs_vwretd": ("tilt_vs_vwretd", "annual_mean_gap"),
                                   "cw_vs_vwretd": ("cw_vs_vwretd", "annual_mean_gap")}.items():
            entry = s7["fragility"][case][key]
            assert [entry[run] for run in d.RUNS] == [s7["records"][run][case][part][field] for run in d.RUNS]
            assert entry["primary"] != entry["last_close"]
            assert entry["fragile"] == (tilt.sign(entry["primary"]) != tilt.sign(entry["last_close"]))
    assert s7["counts"]["primary"]["b2"]["rebalances"] == 1
    c_zero = s7["c_zero_by_exit_class"]["primary"]
    assert c_zero["window_gap"]["cells"]["current"] > 0                             # the break pins 900005
    assert screen["r6"]["primary"]["me_missing"]["no_share_fact"]["cells"]["current"] > 0
    assert sum(screen["r6"]["primary"]["unpriced"]["cells"].values()) == 0
    blanked = screen["r6"]["primary"]["blanked_windows"]
    assert blanked["cells"]["current"] == stage(chain["w0"]["folder"], "look")["runs"]["primary"][
        "blanked_level_windows"]["windows"] and 0 < blanked["share"]["current"] < 1


def test_short_candidate_gets_a_typed_undefined_record(chain) -> None:
    out = chain["w0"]["folder"]
    records = stage(out, "freeze")["record"]["candidates"]
    assert records["S1"]["status"] == "undefined" and records["S1"]["undefined_reason"] == "screen_too_short"
    assert (records["S1"]["first_month"], records["S1"]["months"]) == ("1991-01", 24)
    assert records["S2"]["months"] == 0 and records["S2"]["first_month"] is None
    assert not any(r["shortlisted"] for c, r in records.items() if c != "S7")
    # Every run and cost case has a typed record with its month count; the fragility is typed, not computed.
    s1 = stage(out, "screen")["candidates"]["S1"]
    for run in d.RUNS:
        for case in d.CASES:
            record = s1["records"][run][case]["screen_record"]
            assert (record["status"], record["undefined_reason"], record["months"]) == ("undefined",
                                                                                         "screen_too_short", 24)
    assert s1["fragility"] == {case: {"status": "not_evaluated", "reason": "screen_too_short",
                                      "short_runs": ["primary", "last_close"]} for case in d.CASES}
    assert "counts" not in s1 and "path_break_positions" not in s1


def test_a_short_last_close_run_is_typed_and_a_short_candidate_runs_no_engine(chain, frames, tmp_path,
                                                                                monkeypatch) -> None:
    """The look's last_close set is made to blank S7 down to 30 months; S1 is short in both runs. Only S7 calls the
    engine (once per loader run) and only its primary run calls ``screen_record``; S1 checks each declaration."""
    out = copy_until(chain, tmp_path, "screen")
    blank = [str(m) for m in pd.period_range("1963-07", "1990-06", freq="M")]

    def edit(name: str, payload: dict) -> None:
        if name == "look":
            payload["result"]["runs"]["last_close"]["blank_months"] = blank
    rechain(out, edit)
    seen = Counter()

    def spy(module, name, key=None):
        real = getattr(module, name)

        def counted(*args, **kwargs):
            seen[name if key is None else key(*args)] += 1
            return real(*args, **kwargs)
        monkeypatch.setattr(module, name, counted)
    spy(tilt, "run_index_tilt")
    spy(crit, "screen_record")
    spy(d, "check_declaration", lambda declared, run_set, first, *rest: f"check_declaration {first}")
    d.run_stage("screen", make_data(frames), out, TRACKED)
    assert seen["run_index_tilt"] == 2 and seen["screen_record"] == 2
    assert seen["check_declaration 1991-01"] == 2 and seen["check_declaration 1964-01"] == 4
    result = stage(out, "screen")
    s7 = result["candidates"]["S7"]
    assert s7["months_with_values"] == {"primary": 346, "last_close": 30}
    for case in d.CASES:
        assert s7["records"]["primary"][case]["screen_record"]["status"] == "ok"
        record = s7["records"]["last_close"][case]["screen_record"]
        assert (record["status"], record["undefined_reason"], record["months"]) == ("undefined", "screen_too_short", 30)
        assert s7["fragility"][case] == {"status": "not_evaluated", "reason": "screen_too_short",
                                         "short_runs": ["last_close"]}
    assert result["records_for_freeze"] == stage(chain["w0"]["folder"], "screen")["records_for_freeze"]


@pytest.mark.parametrize("name", ["look", "screen"])
def test_a_late_refusal_leaves_no_output_of_its_comparison_in_the_log(chain, frames, tmp_path, monkeypatch,
                                                                      name) -> None:
    """``r4_counts`` refuses after the first criteria call of the look and of S7: none of their outputs is logged."""
    out = copy_until(chain, tmp_path, name)
    before = len((out / "run_log.jsonl").read_text().splitlines())

    def refused(*args, **kwargs):
        raise tilt.refuse("r4_held_count_mismatch", "a refusal after the first criteria call")
    monkeypatch.setattr(d, "r4_counts", refused)
    with pytest.raises(RunnerStop):
        d.run_stage(name, make_data(frames), out, TRACKED)
    added = [json.loads(x) for x in (out / "run_log.jsonl").read_text().splitlines()[before:]]
    assert added[-1]["refused"] == "r4_held_count_mismatch"
    assert not any(e.get("call") in ("check_paired", "screen_record") for e in added)


# R1: rows after t change nothing at t -----------------------------------------------------------

@pytest.mark.parametrize("month, first, last, signal, positions", [
    ("1976-06", "1974-10", "1977-06", "S7", 1),    # after the 1975 path break, before the 1979 merger
    ("1981-06", "1979-10", "1982-06", "S2", 0)])   # S2 has values (two members with quarters from 1977)
def test_rows_after_t_change_no_signal_weight_decision_or_record_at_t(frames, month, first, last, signal,
                                                                       positions) -> None:
    """Every value after the decision row t of rebalance r changes, the close of r included: nothing at r changes."""
    r = month_end(CAL, month)
    t = CAL[CAL.get_loc(r) - 1]
    end = month_end(CAL, last)
    found = []
    for data in (make_data(frames), make_data(perturb_after(frames, t))):
        panels = d.signal_panels(data, d.screen_inputs(data))
        start = month_end(CAL, first)
        per_run = {run: w.tilt_frames(data, start, end, run) for run in d.RUNS}
        dates = tilt.rebalance_dates(per_run["primary"]["prices"].index, start, end)
        signals = {run: {signal: d.signal_frame(panels, signal, per_run[run], dates)} for run in d.RUNS}
        pair = d.engine_pair(per_run, signals, start, end)
        months = pd.period_range(start.to_period("M") + 1, end.to_period("M"), freq="M")
        held = d.path_break_positions(per_run["primary"], {"cw": pair["primary"]["cases"]["primary"]["cw"]["weights"]},
                                      d.exit_map(data), months, end)
        found.append({"panels": panels, "signals": signals, "pair": pair, "held": held})
    a, b = found
    assert a["panels"]["values"][signal].loc[r].notna().sum() >= 2
    for s in sig.SIGNAL_IDS:
        pd.testing.assert_frame_equal(a["panels"]["values"][s].loc[:r], b["panels"]["values"][s].loc[:r])
        pd.testing.assert_frame_equal(a["panels"]["reasons"][s].loc[:r], b["panels"]["reasons"][s].loc[:r])
    for run in d.RUNS:
        pd.testing.assert_frame_equal(a["signals"][run][signal].loc[:t], b["signals"][run][signal].loc[:t])
        for book in ("cw", "tilt"):
            pd.testing.assert_frame_equal(a["pair"][run]["targets"][book].loc[:r],
                                          b["pair"][run]["targets"][book].loc[:r])
            for case in d.CASES:
                x, y = a["pair"][run]["cases"][case][book], b["pair"][run]["cases"][case][book]
                pd.testing.assert_series_equal(x["daily_net"].loc[:t], y["daily_net"].loc[:t])
                pd.testing.assert_frame_equal(x["weights"].loc[:r], y["weights"].loc[:r])
        pd.testing.assert_frame_equal(a["pair"][run]["rebalances"].loc[:r], b["pair"][run]["rebalances"].loc[:r])
    held = [p for p in a["held"] if p["break_row"] <= t]
    assert len(held) == positions and held == [p for p in b["held"] if p["break_row"] <= t]
    # The perturbation reaches the rows after t: the return on r and the later targets differ.
    assert not a["pair"]["primary"]["targets"]["tilt"].loc[r:].iloc[1:].equals(
        b["pair"]["primary"]["targets"]["tilt"].loc[r:].iloc[1:])
    assert a["pair"]["primary"]["cases"]["primary"]["cw"]["daily_net"].loc[r] != \
        b["pair"]["primary"]["cases"]["primary"]["cw"]["daily_net"].loc[r]


def test_break_flags_after_the_last_row_are_not_read(frames) -> None:
    """A path_break flag on the first 1993 row changes no blank month or blanked window; a held position whose
    path has no close on the last screen row refuses (the frozen file has no rule for it)."""
    data = make_data(frames)
    primary = d.frames_for(data, "primary")
    last = month_end(CAL, "1992-12")
    rows = primary["prices"].index
    dates = pd.DatetimeIndex([month_end(CAL, f"1992-{m:02d}") for m in range(1, 13)])
    weights = pd.DataFrame(0.0, index=dates, columns=primary["prices"].columns)
    weights["900003"] = 0.1
    exits = d.exit_map(data)
    months = pd.period_range(crit.SCREEN_START, crit.SCREEN_END, freq="M")
    before = d.path_break_positions(primary, {"cw": weights}, exits, months, last)
    windows = d.blanked_windows(primary, dates, exits, last)
    flagged = {**primary, "path_break": primary["path_break"].copy()}
    flagged["path_break"].loc[rows[rows > last][0], "900003"] = True
    assert d.path_break_positions(flagged, {"cw": weights}, exits, months, last) == before
    assert d.blanked_windows(flagged, dates, exits, last) == windows
    gap = {**flagged, "prices": flagged["prices"].copy()}
    gap["prices"].loc[(rows > row(CAL, "1992-12-15")) & (rows <= last), "900003"] = np.nan
    with pytest.raises(RunnerStop) as caught:
        d.path_break_positions(gap, {"cw": weights}, exits, months, last)
    assert caught.value.reason == "path_gap_at_period_end"
    weights["900003"] = 0.0
    assert d.path_break_positions(gap, {"cw": weights}, exits, months, last) == before


def test_the_signal_inputs_hold_no_row_after_1992(chain, frames) -> None:
    """Every signal table loses its rows dated after 1992-12-31 at load, and each signal build refuses uncut
    inputs. The annual records known in 1995 and 1996 no longer reach the coverage labels."""
    data = make_data(frames)
    last = month_end(CAL, "1992-12")
    full, cut = w.signal_inputs(data), d.screen_inputs(data)
    for name, columns in d.SIGNAL_DATES.items():
        assert not d.after(getattr(cut, name), columns, last).any()
    for name, columns in (("daily", ("date",)), ("fund_annual", ("known_date",)), ("ibes", ("statpers",))):
        assert d.after(getattr(full, name), columns, last).any()
    rows = pd.DatetimeIndex([month_end(CAL, "1992-11")])
    for build in (lambda x: d.segment_signals(x, rows, last), lambda x: d.s2_basis_quarters(x, last)):
        with pytest.raises(RunnerStop) as caught:
            build(full)
        assert caught.value.reason == "row_after_screen_end"
    d.segment_signals(cut, rows, last)
    coverage = stage(chain["w0"]["folder"], "coverage")["signals"]
    for s in ("S4", "S5", "S6", "S8"):
        assert coverage[s]["cells_by_exit_class"]["current"] == {"no_record": 3719}


def test_the_engine_frames_hold_no_value_after_1992(frames, monkeypatch) -> None:
    """The first 1993 row stays as a date with no value. A spell that starts after 1992 is dropped, and so is a
    column left without a spell. Each engine call refuses a value after 1992-12."""
    first_1993 = CAL[CAL > month_end(CAL, "1992-12")][0]
    world = world_frames([*small_members(CAL), Member(900019, 0.02, spell=(first_1993, OPEN))], CAL)
    rejoin = pd.DataFrame([{"permno": 900007, "indno": 1000502, "mbrstartdt": pd.Timestamp("1993-02-01"),
                            "mbrenddt": OPEN}])
    world["crsp_dsp500list_v2"] = pd.concat([world["crsp_dsp500list_v2"], rejoin], ignore_index=True)
    data = make_data(world)
    last = month_end(CAL, "1992-12")
    start, end = d.window(w.calendar(data), crit.SCREEN_START)
    raw = w.tilt_frames(data, start, end, "primary")
    assert "900019" in raw["prices"].columns and (raw["intervals"]["start_date"] > last).sum() == 2
    cut = d.frames_for(data, "primary")
    rows = cut["prices"].index
    assert list(rows[rows > last]) == [first_1993] and "900019" not in cut["prices"].columns
    assert "900007" in cut["prices"].columns and not (cut["intervals"]["start_date"] > last).any()
    assert set(cut["prices"].columns) <= set(cut["intervals"]["permanent_id"])     # the backtest needs a spell
    for key, fill in d.BLANK_ROW.items():
        row_ = cut[key].loc[first_1993]
        assert (row_.isna() if pd.isna(fill) else row_ == fill).all()
    pd.testing.assert_frame_equal(cut["prices"].loc[:last], raw["prices"].loc[:last, cut["prices"].columns])
    inputs = d.inputs_for(cut, d.no_signal(cut), start, end)
    d.check_engine_cut(inputs)
    tilt.prepare(inputs)                                  # the engine accepts the end row
    late = cut["disappearances"].iloc[:1].assign(effective_date=first_1993, known_at=first_1993)
    for changed in (d.inputs_for(raw, d.no_signal(raw), start, end), replace(inputs, intervals=raw["intervals"]),
                    replace(inputs, disappearances=pd.concat([inputs.disappearances, late], ignore_index=True))):
        with pytest.raises(RunnerStop) as caught:
            d.check_engine_cut(changed)
        assert caught.value.reason == "row_after_screen_end"
    # Each engine call checks its inputs first.
    with pytest.raises(RunnerStop):
        d.engine_pair({run: raw for run in d.RUNS}, {run: d.no_signal(raw) for run in d.RUNS}, start, end)
    with pytest.raises(RunnerStop):
        d.census(d.inputs_for(raw, d.no_signal(raw), start, end), tilt.rebalance_dates(rows, start, end))
    monkeypatch.setattr(d, "frames_for", lambda data_, run: w.tilt_frames(data_, start, end, run))
    with pytest.raises(RunnerStop) as caught:
        d.calibration_stage(data, d.load_trial()[0])
    assert caught.value.reason == "row_after_screen_end"


# R4: the two-call rerun -----------------------------------------------------------------------

def test_in_path_delisting_return_flips_the_sign_only_in_the_two_call_rerun() -> None:
    """A held, overweighted cash merger with a +100 percent Y-row return in the path: the loader last_close rerun
    (a second engine call) flips the active sign; the single-call engine comparison does not."""
    cal = pd.bdate_range("1979-01-02", "1983-02-28", name="date")
    big = row(cal, "1982-06-15")
    members = [Member(900101, 0.0, last=big, delist=("MER", "UNAV", "CASH"), y_return=1.0, drift=0.0002, vol=0.002,
                      facts_from=cal[0]),
               Member(900102, 0.0, drift=0.0002, vol=0.002, facts_from=cal[0], split=row(cal, "1981-03-02")),
               Member(900103, 0.0, drift=0.0004, vol=0.002, facts_from=cal[0]),
               Member(900104, 0.0, drift=0.0006, vol=0.002, facts_from=cal[0]),
               Member(900105, 0.0, drift=0.0006, vol=0.002, facts_from=cal[0])]
    data = make_data(world_frames(members, cal, seed=3, comp=(900102,)))
    start, end = month_end(cal, "1980-12"), month_end(cal, "1982-12")
    frames = {run: w.tilt_frames(data, start, end, run) for run in d.RUNS}
    score = {"900101": 5.0, "900102": 4.0, "900103": 3.0, "900104": 2.0, "900105": 1.0}

    def panel(f):
        return {"X": pd.DataFrame([[score[c] for c in f["prices"].columns]] * len(f["prices"]),
                                  index=f["prices"].index, columns=f["prices"].columns)}

    signals = {run: panel(frames[run]) for run in d.RUNS}
    pair = d.engine_pair(frames, signals, start, end)
    means = {run: {} for run in d.RUNS}
    for run in d.RUNS:
        for case in d.CASES:
            books = pair[run]["cases"][case]
            means[run][case] = {"tilt_vs_cw": crit.annual_mean(books["tilt"]["monthly_net"] - books["cw"]["monthly_net"])}
    for case in d.CASES:
        flip = d.fragility(means["primary"][case], means["last_close"][case])["tilt_vs_cw"]
        assert flip["primary"] > 0 > flip["last_close"] and flip["fragile"]
    single = tilt.run_index_tilt(d.inputs_for(frames["primary"], signals["primary"], start, end),
                                 crit.SCREEN_COST_SCHEDULE)
    assert single["fragile_active_sign"] == {"primary": False, "sensitivity_2x": False}


# S3 across the seal ---------------------------------------------------------------------------

def seal_inputs() -> sig.SignalInputs:
    days = pd.bdate_range("2017-01-02", "2021-12-31", name="date")
    cal = days[(days < sig.SEAL[0]) | (days >= sig.SEAL[1])]
    rng = np.random.default_rng(5)
    daily = pd.concat([pd.DataFrame({"permno": p, "date": cal, "ret": rng.normal(0.0, 0.01, len(cal)),
                                     "prc": 20.0, "shrout": 1000.0, "cfacpr": 1.0, "cfacshr": 1.0}) for p in (1, 2)],
                      ignore_index=True)
    quarters = pd.date_range("2017-03-31", "2020-03-31", freq="QE")
    announcements = pd.DataFrame([{"gvkey": f"G{p}", "datadate": q, "fyearq": q.year, "fqtr": q.quarter,
                                   "rdq": q + pd.Timedelta(days=25)} for p in (1, 2) for q in quarters])
    quarterly = announcements.assign(known_date=announcements["rdq"] + pd.Timedelta(days=5), epspxq=1.0, ajexq=1.0)
    annual = pd.DataFrame(columns=["gvkey", "datadate", "fyear", "known_date", *sig.ANNUAL_ITEMS])
    annual = annual.astype({"datadate": "datetime64[ns]", "known_date": "datetime64[ns]", "fyear": "int64",
                            **{k: float for k in sig.ANNUAL_ITEMS}})
    link = pd.DataFrame({"gvkey": ["G1", "G2"], "permno": [1, 2], "linkdt": pd.Timestamp("2010-01-01"),
                         "linkenddt": pd.Series([pd.NaT, pd.NaT], dtype="datetime64[ns]")})
    ibes_link = pd.DataFrame({"ticker": ["T1"], "permno": [1], "sdate": pd.Timestamp("2010-01-01"),
                              "edate": pd.Series([pd.NaT], dtype="datetime64[ns]"), "score": 0})
    ibes = pd.DataFrame({"ticker": ["T1"], "statpers": pd.Timestamp("2017-01-19"),
                         "fpedats": pd.Timestamp("2017-12-31"), "fpi": "1", "meanest": 1.0})
    return sig.SignalInputs(daily=daily, members=pd.DataFrame({"permno": [1, 2], "start": cal[0], "end": cal[-1]}),
                            fund_annual=annual, fund_quarterly=quarterly[list(sig.SCHEMA["fund_quarterly"])],
                            announcements=announcements, link=link, ibes_link=ibes_link, ibes=ibes,
                            index_daily=pd.DataFrame({"date": cal, "indno": sig.MARKET_INDNO,
                                                      "ret": rng.normal(0.0, 0.01, len(cal))}))


def test_s3_is_built_once_per_seal_segment() -> None:
    inputs = seal_inputs()
    r = pd.Timestamp("2020-08-31")               # the latest rdq (2020-04-24) is inside the seal
    whole = sig.build_signals(inputs, pd.DatetimeIndex([r]))
    assert np.isfinite(whole["values"]["S3"].loc[r, 1])                  # one segment would cross the seal
    cut = sig.build_signals(d.segment_inputs(inputs, True), pd.DatetimeIndex([r]))
    assert cut["reasons"]["S3"].loc[r, 1] == "no_market_data"
    with pytest.raises(RunnerStop) as caught:
        d.segment_signals(inputs, pd.DatetimeIndex([r]))
    assert caught.value.reason == "post_seal_rebalance_early"
    with pytest.raises(RunnerStop) as caught:
        d.segment_signals(inputs, pd.DatetimeIndex(["2019-06-28", "2021-08-31"]))
    assert caught.value.reason == "rebalances_cross_seal"
    late = d.segment_signals(inputs, pd.DatetimeIndex([d.POST_SEAL_FIRST_REBALANCE]))
    assert late["reasons"]["S3"].loc[d.POST_SEAL_FIRST_REBALANCE, 1] == "stale"
    early = d.cut_inputs(inputs, pd.Timestamp("2018-12-31"))
    assert early.daily["date"].max() <= pd.Timestamp("2018-12-31") and early.index_daily["date"].max() <= \
        pd.Timestamp("2018-12-31")


# Driver helpers -------------------------------------------------------------------------------

def test_signal_frame_refuses_a_rebalance_without_a_signal_row(frames) -> None:
    data = make_data(frames)
    panels = d.signal_panels(data, d.screen_inputs(data))
    primary = d.frames_for(data, "primary")
    dates = pd.DatetimeIndex([month_end(CAL, "1970-01"), month_end(CAL, "1970-02")])
    framed = d.signal_frame(panels, "S7", primary, dates)
    t = primary["prices"].index[primary["prices"].index.get_loc(dates[0]) - 1]
    assert framed.loc[t].dropna().equals(-panels["values"]["S7"].loc[dates[0]].dropna().set_axis(
        framed.loc[t].dropna().index))
    cut = {**panels, "values": {**panels["values"], "S7": panels["values"]["S7"].drop(dates[1])}}
    with pytest.raises(RunnerStop) as caught:
        d.signal_frame(cut, "S7", primary, dates)
    assert caught.value.reason == "signal_rebalance_missing"


def test_declaration_is_the_run_set_cut_to_the_span() -> None:
    run_set = ["1970-03", "1975-06", "1975-07"]
    declared = d.declaration(run_set, pd.Period("1975-07", "M"))
    assert declared == {pd.Period("1975-07", "M"): d.BLANK}
    d.check_declaration(declared, run_set, pd.Period("1975-07", "M"))
    with pytest.raises(RunnerStop):
        d.check_declaration({}, run_set, pd.Period("1975-07", "M"))


def test_a_window_with_two_breaks_counts_once() -> None:
    """Two path breaks of one member inside one 252-row window: each member-rebalance window counts once."""
    rows = pd.bdate_range("1980-01-01", periods=300, name="date")
    prices = pd.DataFrame({"1": 20.0}, index=rows)
    breaks = pd.DataFrame({"1": False}, index=rows)
    for gap in (100, 150):                      # no close on rows 100 and 150: breaks on rows 101 and 151
        prices.iloc[gap] = np.nan
        breaks.iloc[gap + 1] = True
    frames = {"prices": prices, "path_break": breaks, "eligible": pd.DataFrame(True, index=rows, columns=["1"])}
    found = d.blanked_windows(frames, rows[[160, 200, 250]], {"1": "current"}, rows[-1])
    assert found["windows"] == len(found["each"]) == found["by_exit_class"]["current"] == 3
    assert all(e["break_rows"] == [rows[101], rows[151]] for e in found["each"])
    assert d.shares(found["by_exit_class"], {"current": 3})["current"] == 1.0


def test_a_monthly_series_after_1992_refuses_before_the_criteria() -> None:
    months = pd.Series(np.linspace(-0.01, 0.02, 37), index=pd.period_range("1990-01", "1993-01", freq="M"))
    for book, benchmark in ((months, months.iloc[:-1]), (months.iloc[:-1], months)):
        with pytest.raises(RunnerStop) as caught:
            d.mean_gap(book, benchmark, {})
        assert caught.value.reason == "row_after_screen_end"
    with pytest.raises(RunnerStop):
        d.check_months(months.iloc[:-1], months)
    d.check_months(months.iloc[:-1])


def test_monthly_vwretd_leaves_a_month_with_a_missing_day_missing(frames) -> None:
    legacy = frames["crsp_dsp500_legacy"].copy()
    legacy.loc[legacy["caldt"] == row(CAL, "1970-03-16"), "vwretd"] = np.nan
    monthly = d.monthly_vwretd(make_data({**frames, "crsp_dsp500_legacy": legacy}), crit.SCREEN_START)
    assert np.isnan(monthly[pd.Period("1970-03", "M")]) and monthly.drop(pd.Period("1970-03", "M")).notna().all()
    assert monthly.index[-1] == crit.SCREEN_END


# Real size (opt-in) -----------------------------------------------------------------------------

def real_size_members(cal: pd.DatetimeIndex, size: int = 500, per_year: int = 8) -> list[Member]:
    rng = np.random.default_rng(13)
    members = []
    exits = pd.DatetimeIndex(sorted(rng.choice(cal[(cal > pd.Timestamp("1963-12-31")) & (cal < cal[-30])],
                                               size=per_year * 30, replace=False)))
    leaving = {int(k): e for k, e in zip(rng.choice(size + per_year * 30, size=per_year * 30, replace=False), exits)}
    causes = [("MER", "UNAV", "CASH"), ("GDR", "BKPY", "UNAV"), ("MER", "UNAV", "STK"), None]
    joiners = iter(exits)
    for k in range(size + per_year * 30):
        g = float(rng.uniform(-0.05, 0.12))
        spell_start = cal[0] if k < size else next(joiners, None)
        if spell_start is None:
            break
        exit_ = leaving.get(k)
        if exit_ is not None and exit_ <= spell_start:
            exit_ = None
        cause = causes[k % 4] if exit_ is not None else None
        if cause is None and exit_ is not None:
            members.append(Member(900000 + k, g, spell=(spell_start, exit_)))       # left_index
        elif exit_ is not None:
            members.append(Member(900000 + k, g, spell=(spell_start, exit_), last=exit_, delist=cause,
                                  y_return=0.1 if cause[2] == "CASH" else math.nan))
        else:
            members.append(Member(900000 + k, g, spell=(spell_start, OPEN)))
    members[0] = replace(members[0], split=row(cal, "1980-03-03"))
    members[1] = replace(members[1], gp=month_end(cal, "1975-06"))
    return members


@pytest.mark.skipif(os.environ.get("M55_DRIVER_REAL_SIZE") != "1", reason="real-size run: M55_DRIVER_REAL_SIZE=1")
def test_real_size_world_runs_every_stage(tmp_path: Path) -> None:
    cal = pd.bdate_range("1962-01-02", "1993-02-26", name="date")
    begin = time.perf_counter()
    data = make_data(world_frames(real_size_members(cal), cal, seed=21))
    times = {"build": time.perf_counter() - begin}
    for name in d.STAGES:
        begin = time.perf_counter()
        d.run_stage(name, data, tmp_path / "out", TRACKED)
        times[name] = time.perf_counter() - begin
    columns = d.frames_for(data, "primary")["prices"].shape
    print(json.dumps({"rows_columns": columns, "seconds": {k: round(v, 1) for k, v in times.items()}}))
    assert stage(tmp_path / "out", "freeze")["decision"] in ("shortlist_frozen", "screen_empty")
