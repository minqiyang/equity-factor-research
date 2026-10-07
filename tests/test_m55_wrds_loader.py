"""Synthetic tests for the Milestone 5.5 WRDS loader (card m55-loader).

Every table is generated here; no test reads the WRDS folder or opens a network connection.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import research.m55_wrds_loader as w
from data.constituent_table import build_pit_membership_mask
from research import m55_signals as sig
from research.m4_7_family_a import FAMILY_A_IDS
from research.m4_7_sp500_pit_rerun import RunnerStop
from research.m55_index_tilt import TiltInputs, check_disappearances, check_inputs, terminal_events


DAYS = pd.bdate_range("1992-12-01", "2021-06-30")
CAL = DAYS[~((DAYS >= w.SEAL_START) & (DAYS <= w.SEAL_END))]
VINTAGE = CAL[-1]
A, B, C, D, E, F, G, SPY = 900001, 900002, 900003, 900004, 900005, 900006, 900007, 900099   # outside CRSP
FIRST = pd.Timestamp("1993-01-04")
SPLIT = pd.Timestamp("2018-03-01")                # A: 2-for-1
B_END = pd.Timestamp("2018-05-15")                # B leaves the index and keeps trading
LAST = {C: pd.Timestamp("2018-09-14"), D: pd.Timestamp("2018-10-15"), E: pd.Timestamp("2018-11-15"),
        G: pd.Timestamp("2018-12-14")}            # delisting rows
Y_RETURN = {C: 0.05, D: np.nan, E: -1.0, G: -0.02}
DELISTS = {C: ("MER", "UNAV", "CASH"), D: ("GDR", "BKPY", "UNAV"), E: ("GLI", "UNAV", "PRCF"),
           G: ("MER", "UNAV", "STK")}
NT_DAY, GAP_NEXT = pd.Timestamp("2018-02-06"), pd.Timestamp("2018-02-07")   # F: no price, then a 2-day return
BREAK_DAY = pd.Timestamp("2018-04-10")            # F: a price without a return (CIZ GP)
MEMBERS = (A, B, C, D, E, F, G)


def at(day: str) -> pd.Timestamp:
    return pd.Timestamp(day)


def daily_rows(permno: int, rng: np.random.Generator) -> pd.DataFrame:
    first = at("1993-01-29") if permno == SPY else CAL[0]
    dates = CAL[(CAL >= first) & (CAL <= LAST.get(permno, CAL[-1]))]
    ret = rng.normal(0.0005, 0.01, len(dates))
    prc = 20.0 * np.cumprod(1.0 + ret)
    table = pd.DataFrame({"permno": permno, "dlycaldt": dates, "dlyret": ret, "dlyprc": prc, "dlydelflg": "N",
                          "dlycumfacpr": 1.0, "dlycumfacshr": 1.0, "dlyfacprc": 1.0, "shrout": 1000,
                          "dlyvol": 100.0, "primaryexch": "N", "dlyprcflg": "TR"})
    table.loc[table.index[1::50], "dlyprcflg"] = "BA"   # a bid-ask average now and then
    if permno == B:
        table["primaryexch"] = "Q"
    table["dlyprevdt"] = table["dlycaldt"].shift(1)
    table.loc[0, "dlyret"] = np.nan                       # a new security has no first return (CIZ NS)
    if permno == A:
        before = table["dlycaldt"] < SPLIT
        table.loc[before, ["dlycumfacpr", "dlycumfacshr"]] = 2.0
        table.loc[before, "dlyprc"] *= 2.0
        table.loc[before, "shrout"] = 500
        table.loc[table["dlycaldt"] == SPLIT, "dlyfacprc"] = 2.0
    if permno == F:
        table.loc[table["dlycaldt"] == NT_DAY, ["dlyret", "dlyprc"]] = np.nan
        table.loc[table["dlycaldt"] == GAP_NEXT, "dlyprevdt"] = NT_DAY - pd.offsets.BDay(1)
        table.loc[table["dlycaldt"] == BREAK_DAY, "dlyret"] = np.nan
    if permno in LAST:
        last = table.index[-1]
        table.loc[last, ["dlydelflg", "dlyret"]] = ["Y", Y_RETURN[permno]]
        table.loc[last, ["dlycumfacpr", "dlycumfacshr", "shrout"]] = np.nan
    return table


def world_frames(seed: int = 5) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    dsf = pd.concat([daily_rows(p, rng) for p in (*MEMBERS, SPY)], ignore_index=True)
    shares = pd.DataFrame({"permno": [*MEMBERS, SPY], "shrstartdt": CAL[0],
                           "shrenddt": at("2025-12-31"), "shrout": 1000})
    shares.loc[shares["permno"] == A, "shrenddt"] = SPLIT - pd.Timedelta(days=1)
    shares.loc[shares["permno"] == A, "shrout"] = 500
    shares = pd.concat([shares, pd.DataFrame({"permno": [A], "shrstartdt": [SPLIT], "shrenddt": [at("2025-12-31")],
                                              "shrout": [1000]})], ignore_index=True)
    delists = pd.DataFrame([{"permno": p, "delactiontype": a, "delreasontype": r, "delpaymenttype": m}
                            for p, (a, r, m) in DELISTS.items()])
    info = pd.DataFrame({"permno": [*MEMBERS, SPY], "ticker": [f"T{p}" for p in MEMBERS] + ["SPY"],
                         "secinfostartdt": at("1990-01-01"), "secinfoenddt": at("2025-12-31")})
    info.loc[info["permno"] == SPY, "secinfostartdt"] = at("1993-01-29")
    spells = pd.DataFrame({"permno": list(MEMBERS), "indno": 1000502, "mbrstartdt": FIRST,
                           "mbrenddt": [CAL[-1], B_END, *[LAST[p] for p in (C, D, E)], CAL[-1], LAST[G]]})
    index = pd.concat([pd.DataFrame({"indno": 1000200, "dlycaldt": CAL, "dlytotret": rng.normal(0, 0.01, len(CAL)),
                                     "dlyprcret": 0.5}),
                       pd.DataFrame({"indno": 1000502, "dlycaldt": CAL, "dlytotret": np.nan, "dlyprcret": 0.25})])
    legacy = pd.DataFrame({"caldt": CAL, "vwretd": rng.normal(0, 0.01, len(CAL)), "sprtrn": 9.0})
    link = pd.DataFrame({"gvkey": [f"G{p}" for p in MEMBERS], "lpermno": [float(p) for p in MEMBERS],
                         "linkdt": at("1990-01-01"), "linkenddt": pd.NaT})
    quarters = pd.date_range("1994-03-31", "2021-03-31", freq="QE")
    fundq = pd.DataFrame([{"gvkey": f"G{p}", "datadate": q, "fyearq": q.year,
                           "ajexq": 2.0 if p == A and q < SPLIT else 1.0} for p in MEMBERS for q in quarters])
    urq = pd.DataFrame([{"gvkey": f"G{p}", "datadate": q, "fqtr": float(q.quarter), "rdq": q + pd.Timedelta(days=25),
                         "prelimqprd": q + pd.Timedelta(days=30), "finalqprd": q + pd.Timedelta(days=60),
                         "epspxq": 1.0, "ajexq": 1.0} for p in MEMBERS for q in quarters])
    years = pd.date_range("1993-12-31", "2020-12-31", freq="YE")
    snapshot = pd.DataFrame([{"gvkey": f"G{p}", "datadate": y, "fyear": float(y.year),
                              "pitdate1": y + pd.Timedelta(days=80), **{k: 1.0 for k in sig.ANNUAL_ITEMS}}
                             for p in MEMBERS for y in years])
    months = pd.date_range("1994-01-15", "2021-05-15", freq="MS") + pd.Timedelta(days=14)
    ibes = pd.DataFrame([{"ticker": f"T{p}", "statpers": m, "fpedats": at(f"{m.year}-12-31"), "fpi": "1",
                          "meanest": 2.0, "curcode": "USD"} for p in MEMBERS for m in months])
    ibes_link = pd.DataFrame({"ticker": [f"T{p}" for p in MEMBERS], "permno": list(MEMBERS),
                              "sdate": at("1990-01-01"), "edate": pd.NaT, "score": 1.0})
    return {"crsp_dsf_v2": dsf, "crsp_stkshares": shares, "crsp_stkdelists": delists,
            "crsp_stksecurityinfohist": info, "crsp_dsp500list_v2": spells, "crsp_index_daily": index,
            "crsp_dsp500_legacy": legacy, "ccm_lnkhist": link, "comp_fundq": fundq, "comp_urq": urq,
            "comp_snapshot_csa_pit": snapshot, "ibes_statsumu_epsus": ibes, "ibes_crsp_link": ibes_link}


def to_arrow(table: pd.DataFrame) -> pa.Table:
    out = pa.Table.from_pandas(table.reset_index(drop=True), preserve_index=False)
    for k, f in enumerate(out.schema):
        if pa.types.is_timestamp(f.type):
            out = out.set_column(k, f.name, out.column(k).cast(pa.timestamp("ns")).cast(pa.date32()))
    return out


def make_data(frames: dict[str, pd.DataFrame]) -> w.WrdsData:
    manifest = {"vintage": str(VINTAGE.date()), "code": "0" * 64, "files": {}}
    return w.WrdsData({k: to_arrow(v) for k, v in frames.items()}, manifest)


@pytest.fixture(scope="module")
def world() -> w.WrdsData:
    return make_data(world_frames())


def edit(frames: dict[str, pd.DataFrame], stem: str, table: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {**frames, stem: table}


# Loading and the tracked manifest ---------------------------------------------------------

def write_world(root: Path, frames: dict[str, pd.DataFrame]) -> None:
    files = {}
    for stem, table in frames.items():
        parts = {f"{stem}.parquet": table}
        if stem == "crsp_dsf_v2":       # a by-year table: two parts and an empty one
            early = table["dlycaldt"] < SPLIT
            parts = {f"{stem}/early.parquet": table[early], f"{stem}/late.parquet": table[~early]}
            files[f"{stem}/nulldate.parquet"] = {"rows": 0, "sha256": None, "query": "select 0", "code": "c"}
        for relative, part in parts.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(to_arrow(part), path)
            files[relative] = {"rows": len(part), "sha256": w.sha256(path), "query": f"select {relative}",
                               "code": "c"}
    (root / "sealed" / "crsp_dsf_v2_sealed").mkdir(parents=True)
    (root / "sealed" / "crsp_dsf_v2_sealed" / "2019.parquet").write_bytes(b"not a parquet file")
    (root / "sealed" / "SEALED_MANIFEST.json").write_bytes(b"{sealed}")
    (root / w.MANIFEST).write_text(json.dumps({"vintage": str(VINTAGE.date()), "code": "a" * 64, "files": files}))


@pytest.fixture()
def world_dir(tmp_path: Path) -> Path:
    write_world(tmp_path / "wrds", world_frames())
    return tmp_path / "wrds"


def test_load_reads_main_files_and_never_opens_sealed_files(world_dir: Path, monkeypatch) -> None:
    opened = []
    real_read, real_open = pq.read_table, Path.open
    monkeypatch.setattr(w.pq, "read_table", lambda path, *a, **k: (opened.append(Path(path)), real_read(path))[1])
    monkeypatch.setattr(Path, "open", lambda self, *a, **k: (opened.append(self), real_open(self, *a, **k))[1])
    data = w.load(world_dir)
    assert not any("sealed" in p.parts for p in opened)
    assert data.tables["crsp_dsf_v2"].num_rows == len(world_frames()["crsp_dsf_v2"])
    assert w.calendar(data).equals(pd.DatetimeIndex(CAL, name="date"))


@pytest.mark.parametrize("case", ["hash", "missing", "sealed_listed", "sealed_root", "rows", "extra_empty"])
def test_load_refusals(world_dir: Path, case: str) -> None:
    manifest = json.loads((world_dir / w.MANIFEST).read_text())
    root, reason = world_dir, {"hash": "hash_mismatch", "missing": "file_missing", "sealed_listed": "sealed_path",
                               "sealed_root": "sealed_path", "rows": "row_count_mismatch",
                               "extra_empty": "file_unexpected"}[case]
    if case == "hash":
        manifest["files"]["crsp_stkshares.parquet"]["sha256"] = "0" * 64
    elif case == "missing":
        (world_dir / "comp_urq.parquet").unlink()
    elif case == "sealed_listed":
        manifest["files"]["sealed/crsp_dsf_v2_sealed/2019.parquet"] = {"rows": 1, "sha256": "x"}
    elif case == "sealed_root":
        root = world_dir / "sealed"
        (root / w.MANIFEST).write_text(json.dumps(manifest))
    elif case == "rows":
        manifest["files"]["crsp_stkshares.parquet"]["rows"] += 1
    else:
        manifest["files"]["crsp_dsf_v2/nulldate.parquet"]["rows"] = 0
        (world_dir / "crsp_dsf_v2" / "nulldate.parquet").write_bytes(b"x")
    (world_dir / w.MANIFEST).write_text(json.dumps(manifest))
    with pytest.raises(RunnerStop, match=reason):
        w.load(root)


def test_write_manifest_has_hashes_and_no_identifier_query_or_path(world_dir: Path, tmp_path: Path) -> None:
    data = w.load(world_dir)
    out = w.write_manifest(data, tmp_path / "m.json")
    text = (tmp_path / "m.json").read_text()
    for forbidden in ("SPY", "G9000", "T9000", "select", str(world_dir)):
        assert forbidden not in text

    def strings(value, key=""):
        if isinstance(value, dict):
            return [s for k, v in value.items() for s in [k, *strings(v, k)]]
        return [] if key.endswith("sha256") else [str(value)]
    assert not any(str(p) in s for p in (*MEMBERS, SPY) for s in strings(out))
    sealed = sorted(p for p in (world_dir / "sealed").rglob("*") if p.is_file())
    expected = hashlib.sha256(b"".join(p.read_bytes() for p in sealed)).hexdigest()
    assert out["sealed"] == {"files": 2, "sha256": expected}
    record = out["files"]["crsp_stkshares.parquet"]
    assert record["rows"] == len(world_frames()["crsp_stkshares"])
    assert record["query_sha256"] == hashlib.sha256(b"select crsp_stkshares.parquet").hexdigest()
    assert out["script_code_sha256"] == "a" * 64 and out["units"]["shrout"] == "thousands of shares"


# D3 price path ----------------------------------------------------------------------------

def path_rows(rows: list[tuple]) -> pd.DataFrame:
    table = pd.DataFrame(rows, columns=["permno", "date", "prc", "dlyret", "dlyprevdt", "dlydelflg"])
    table["date"] = pd.to_datetime(table["date"])
    table["dlyprevdt"] = pd.to_datetime(table["dlyprevdt"])
    return table


def test_price_path_across_a_gap_a_break_and_the_seal() -> None:
    rows = path_rows([
        (1, "2018-01-02", 10.0, np.nan, None, "N"),          # anchor
        (1, "2018-01-03", 11.0, 0.10, "2018-01-02", "N"),
        (1, "2018-01-04", np.nan, np.nan, "2018-01-03", "N"),  # no trade
        (1, "2018-01-05", 13.2, 0.20, "2018-01-03", "N"),     # a two-day return from the last price
        (1, "2018-01-08", 14.0, np.nan, "2018-01-05", "N"),   # a price without a return
        (1, "2018-01-09", 15.4, 0.10, "2018-01-08", "N"),     # spans from the row without a return
        (1, "2020-08-03", 30.0, 0.50, "2020-07-31", "N"),     # first row after the seal: a new anchor
        (1, "2020-08-04", 33.0, 0.10, "2020-08-03", "N"),
    ])
    path = w.price_path(rows)
    assert path["level"].tolist()[:4] == pytest.approx([1.0, 1.1, np.nan, 1.1 * 1.2], nan_ok=True)
    assert np.isnan(path["level"].iloc[4])
    assert path["level"].iloc[5] == pytest.approx(1.1 * 1.2 * 1.1)   # the last valid value times (1 + ret)
    assert path["chain_mismatch"].tolist() == [False] * 5 + [True, False, False]
    assert path["level"].tolist()[6:] == pytest.approx([1.0, 1.1])


def test_delisting_return_of_minus_100_percent_stays_out_of_the_path() -> None:
    rows = path_rows([(1, "2018-01-02", 10.0, np.nan, None, "N"), (1, "2018-01-03", np.nan, -1.0, "2018-01-02", "Y")])
    path = w.price_path(rows)
    assert np.isnan(path["level"].iloc[1]) and path["terminal"].iloc[1]
    with pytest.raises(RunnerStop, match="return_invalid"):
        w.price_path(rows.assign(dlydelflg="N"))


# D5 market equity -------------------------------------------------------------------------

T = pd.Timestamp("2018-06-29")


def me_case(shares: list[tuple], price: float = 50.0, factor_t: float = 1.0, basis_factor: float = 1.0,
            level: float = 1.0) -> pd.Series:
    rows = pd.DataFrame({"permno": 1, "date": pd.to_datetime(["1985-01-01", "2018-06-29"]),
                         "prc": [10.0, price], "dlycumfacshr": [basis_factor, factor_t], "level": [1.0, level]})
    facts = pd.DataFrame(shares, columns=["shrstartdt", "shrenddt", "shrout"]).assign(permno=1)
    facts[["shrstartdt", "shrenddt"]] = facts[["shrstartdt", "shrenddt"]].apply(pd.to_datetime)
    return w.market_equity(rows, facts).iloc[1]


def test_share_count_is_used_from_136_days_and_not_one_day_earlier() -> None:
    cutoff = T - pd.Timedelta(days=136)
    old = ("1985-01-01", cutoff - pd.Timedelta(days=1), 1000)
    on_time = me_case([old, (cutoff, "2025-12-31", 1500)])
    assert on_time["market_equity"] == 50.0 * 1500 and pd.isna(on_time["me_reason"])
    late = me_case([(old[0], cutoff, 1000), (cutoff + pd.Timedelta(days=1), "2025-12-31", 1500)])
    assert late["market_equity"] == 50.0 * 1000


def test_share_reasons_stale_none_and_unmapped() -> None:
    cutoff = T - pd.Timedelta(days=136)
    stale = me_case([("1985-01-01", cutoff - pd.Timedelta(days=1), 1000)])
    assert np.isnan(stale["market_equity"]) and stale["me_reason"] == "stale_share_fact"
    assert np.isnan(stale["share_count"])                              # item 7: no count under a D5 reason
    assert me_case([("1985-01-01", cutoff, 1000)])["market_equity"] == 50.0 * 1000
    none = me_case([(cutoff + pd.Timedelta(days=1), "2025-12-31", 1000)])
    assert none["me_reason"] == "no_share_fact"
    for case in (me_case([("1985-01-01", "2025-12-31", 1000)], price=np.nan),
                 me_case([("1985-01-01", "2025-12-31", 1000)], level=np.nan),
                 me_case([("1985-01-01", "2025-12-31", 1000)], factor_t=np.nan)):
        assert np.isnan(case["market_equity"]) and case["me_reason"] == "unmapped"


def test_share_count_moves_to_the_basis_at_t_by_the_factor_ratio() -> None:
    # The count is on the 1985 basis (factor 2); a 2-for-1 split later halves the factor at t.
    assert me_case([("1985-01-01", "2025-12-31", 1000)], basis_factor=2.0)["market_equity"] == 50.0 * 2000


# World tests: D1, D2, D4, D6, D7, D8, benchmarks, and future perturbation ----------------

def test_tilt_frames_build_engine_inputs_that_pass_check_inputs(world: w.WrdsData) -> None:
    frames = w.tilt_frames(world, "2016-12-30", "2018-12-31")
    prices = frames["prices"]
    assert list(prices.columns) == [str(p) for p in MEMBERS]                # D1: the PERMNO string
    signals = {s: pd.DataFrame(0.0, index=prices.index, columns=prices.columns) for s in FAMILY_A_IDS}
    inputs = TiltInputs(prices=prices, signals=signals, eligible=frames["eligible"],
                        market_equity=frames["market_equity"], me_reason=frames["me_reason"],
                        intervals=frames["intervals"], disappearances=frames["disappearances"],
                        start=at("2016-12-30"), end=at("2018-12-31"))
    check_inputs(inputs)
    check_disappearances(inputs.disappearances, prices.index, prices.columns)
    assert prices.index[-1] == at("2019-01-01")
    market, reason = frames["market_equity"], frames["me_reason"]
    assert (market.notna() == reason.isna()).all().all()
    breaks = frames["path_break"]
    assert breaks.index.equals(prices.index) and breaks.columns.equals(prices.columns)
    assert breaks.to_numpy().sum() == 1 and breaks.loc[BREAK_DAY + pd.offsets.BDay(1), str(F)]
    assert np.isnan(prices.loc[BREAK_DAY, str(F)])                         # the row without a return stays NaN
    assert reason.loc["2018-10-16":, str(D)].eq("unmapped").all()           # no daily row: unmapped
    assert market.loc["2018-06-29", str(A)] == pytest.approx(world_frames()["crsp_dsf_v2"].set_index(
        ["permno", "dlycaldt"]).loc[(A, at("2018-06-29")), "dlyprc"] * 1000)


def test_window_across_the_seal_or_without_a_later_month_refuses(world: w.WrdsData) -> None:
    with pytest.raises(RunnerStop, match="window_crosses_seal"):
        w.tilt_frames(world, "2018-12-31", "2020-12-31")
    with pytest.raises(RunnerStop, match="window_invalid"):
        w.tilt_frames(world, "2019-01-31", "2019-07-30")
    frames = w.tilt_frames(world, "2020-08-31", "2021-05-28")
    assert frames["prices"].index[0] == at("2020-08-03") and frames["prices"].iloc[0].dropna().eq(1.0).all()


def test_membership_end_is_inclusive_and_matches_the_engine_mask(world: w.WrdsData) -> None:
    frames = w.tilt_frames(world, "2016-12-30", "2018-12-31")
    rows, eligible, table = frames["calendar"], frames["eligible"], frames["intervals"]
    b = table[table["permanent_id"] == str(B)].iloc[0]
    assert b["end_date"] == B_END + pd.Timedelta(days=1) and b["end_known_at"] == B_END
    assert b["start_known_at"] == b["start_date"] == FIRST
    assert eligible.loc[B_END - pd.offsets.BDay(1), str(B)] and not eligible.loc[B_END, str(B)]
    mask = build_pit_membership_mask(table, rows, list(eligible.columns), signal_lag_periods=1)
    assert eligible.iloc[:-1].to_numpy().tolist() == mask.iloc[1:].to_numpy().tolist()
    members = w.signal_inputs(world).members
    assert members.loc[members["permno"] == B, "end"].iloc[0] == B_END       # signals keep the inclusive end


def test_disappearance_classes_and_delisting_returns(world: w.WrdsData) -> None:
    table = w.disappearances(world).set_index("permanent_id")
    assert table["cause"].to_dict() == {str(C): "cash_merger", str(D): "failure", str(E): "failure",
                                        str(G): "unknown"}
    assert table.loc[str(C), "delisting_return"] == 0.0 and table.loc[str(G), "delisting_return"] == 0.0
    assert np.isnan(table.loc[str(D), "delisting_return"]) and table.loc[str(E), "delisting_return"] == -1.0
    nxt = {p: CAL[CAL.get_loc(day) + 1] for p, day in LAST.items()}
    assert table.loc[str(C), "effective_date"] == nxt[C]                     # the row after the delisting row
    assert table.loc[str(D), "effective_date"] == LAST[D]                    # the delisting row has no value
    assert (table["known_at"] == table["effective_date"]).all()
    for codes, cause in ((("MER", "UNAV", "CASH"), "cash_merger"), (("MER", "UNAV", "CNC"), "unknown"),
                         (("GEX", "MVOT", "CASH"), "failure"), (("GLI", "UNAV", "UNAV"), "failure"),
                         (("GDR", "XYZ", "UMAP"), "unknown"), ((None, None, None), "unknown")):
        assert w.cause_of(*codes) == cause


def test_split_factor_direction_check_refuses_a_rising_factor() -> None:
    frames = world_frames()
    dsf = frames["crsp_dsf_v2"].copy()
    early = (dsf["permno"] == A) & (dsf["dlycaldt"] < SPLIT)
    dsf.loc[early, ["dlycumfacpr", "dlycumfacshr"]] = 0.5
    with pytest.raises(RunnerStop, match="split_factor_invalid"):
        w.daily(make_data(edit(frames, "crsp_dsf_v2", dsf)))
    dsf.loc[early, ["dlycumfacpr", "dlycumfacshr"]] = 1.0                  # the factors do not move at the split
    with pytest.raises(RunnerStop, match="split_factor_invalid"):
        w.daily(make_data(edit(frames, "crsp_dsf_v2", dsf)))
    assert w.split_check(w.daily(make_data(frames)))["both_factors_halve"] == 1


def test_calendar_and_seal_refusals() -> None:
    frames = world_frames()
    dsf = frames["crsp_dsf_v2"]
    off = dsf[dsf["permno"] == A].iloc[[100]].assign(dlycaldt=at("1994-01-01"))     # a Saturday member row
    with pytest.raises(RunnerStop, match="calendar_invalid"):
        w.daily(make_data(edit(frames, "crsp_dsf_v2", pd.concat([dsf, off]))))
    outside = off.assign(permno=SPY, dlycaldt=at("1993-01-02"))                       # not a member: dropped
    data = make_data(edit(frames, "crsp_dsf_v2", pd.concat([dsf, outside])))
    assert len(w.daily(data)) == len(dsf) and data.cache["daily_off_calendar"] == 1
    sealed = off.assign(dlycaldt=at("2019-08-01"))
    with pytest.raises(RunnerStop, match="seal_row_present"):
        w.daily(make_data(edit(frames, "crsp_dsf_v2", pd.concat([dsf, sealed]))))


def test_signal_inputs_pass_check_inputs_and_count_dropped_rows() -> None:
    frames = world_frames()
    urq, fundq, snap = frames["comp_urq"].copy(), frames["comp_fundq"].copy(), frames["comp_snapshot_csa_pit"].copy()
    urq.loc[0, ["prelimqprd", "finalqprd"]] = pd.NaT                   # no known date
    urq.loc[1, ["rdq", "prelimqprd"]] = [pd.NaT, urq.loc[1, "datadate"] - pd.Timedelta(days=1)]   # before datadate
    fundq = pd.concat([fundq, fundq.iloc[[2]].assign(fyearq=1900)])    # two fiscal years: no fiscal key
    urq.loc[3, "fqtr"] = np.nan
    snap.loc[0, "pitdate1"] = snap.loc[0, "datadate"] - pd.Timedelta(days=5)
    snap.loc[1, "fyear"] = np.nan
    snap.loc[2, "fyear"] = snap.loc[3, "fyear"]                        # one fiscal year on two datadates
    data = make_data({**frames, "comp_urq": urq, "comp_fundq": fundq, "comp_snapshot_csa_pit": snap})
    inputs, drops = w.signal_tables(data)
    sig.check_inputs(inputs)
    assert drops["fund_quarterly"] == {"no_fiscal_key": 2, "fiscal_key_conflict": 0, "no_known_date": 1,
                                       "known_before_datadate": 1}
    assert drops["announcements"] == {"no_fiscal_key": 2, "fiscal_key_conflict": 0}
    assert drops["fund_annual"] == {"no_fiscal_key": 1, "no_known_date": 0, "known_before_datadate": 1,
                                    "fiscal_key_conflict": 1}               # the later-known record loses
    q = inputs.fund_quarterly.iloc[5]
    assert q["known_date"] == q["datadate"] + pd.Timedelta(days=30) and q["fyearq"] == q["datadate"].year
    assert set(inputs.daily["permno"]) == set(MEMBERS)                     # SPY is not an input to the signals
    assert (inputs.index_daily["indno"] == 1000200).all()
    later = urq.iloc[[6]].assign(rdq=urq.loc[6, "prelimqprd"] + pd.Timedelta(days=3))
    one = w.signal_tables(make_data(edit(frames, "comp_urq", later)))[0]
    assert one.fund_quarterly["known_date"].iloc[0] == later["rdq"].iloc[0]                                           # the later of rdq and the period date


def test_benchmarks_use_total_returns_only(world: w.WrdsData) -> None:
    frames = world_frames()
    bench = w.benchmarks(world)
    dsf = frames["crsp_dsf_v2"]
    spy = dsf[dsf["permno"] == SPY].set_index("dlycaldt")["dlyret"]
    assert bench["spy"].first_valid_index() == at("1993-02-01")
    reference = spy.loc["1993-02-01":].dropna()
    assert bench["spy"].dropna().index.equals(pd.DatetimeIndex(reference.index))
    assert bench["spy"].dropna().to_numpy() == pytest.approx(reference.to_numpy())
    index = frames["crsp_index_daily"]
    assert bench["crsp_vw_market"].to_numpy() == pytest.approx(index[index["indno"] == 1000200]["dlytotret"])
    assert bench["sp500_vw_legacy"].dropna().to_numpy() == pytest.approx(frames["crsp_dsp500_legacy"]["vwretd"])
    assert w.spy_check(world)["first_return_month"] == "1993-02"


def test_spy_gap_and_duplicate_fy1_refuse() -> None:
    frames = world_frames()
    dsf = frames["crsp_dsf_v2"]
    hole = (dsf["permno"] == SPY) & dsf["dlycaldt"].between("2000-03-01", "2000-03-09")
    with pytest.raises(RunnerStop, match="spy_invalid"):
        w.spy_check(make_data(edit(frames, "crsp_dsf_v2", dsf[~hole])))
    ibes = frames["ibes_statsumu_epsus"]
    twin = ibes.iloc[[10]].assign(statpers=ibes["statpers"].iloc[10] + pd.Timedelta(days=3))
    with pytest.raises(RunnerStop, match="duplicate_key"):
        w.signal_inputs(make_data(edit(frames, "ibes_statsumu_epsus", pd.concat([ibes, twin]))))


def test_intake_report_counts(world: w.WrdsData) -> None:
    report = w.intake_report(world)
    assert report["disappearances"] == {"total": 4, "cash_merger": 1, "failure": 2, "unknown": 1,
                                        "delisting_return_in_path": 2, "delisting_return_supplied_minus_100": 1,
                                        "delisting_return_missing": 1}
    assert report["price_path"]["chain_mismatch_rows"] == 1 and report["price_path"]["chain_mismatch_in_member_spell"] == 1
    assert report["split_check"]["split_rows"] == 1 and report["duplicate_fy1_ticker_month"] == 0
    assert report["members_per_day"]["1994"]["max"] == 7
    assert set(report["me_by_exit"]) == {"current", "left_index", "cash_merger", "failure", "unknown"}
    text = w.intake_markdown(report)
    assert "FAIL" not in text and all(str(p) not in text for p in (*MEMBERS, SPY))


def frames_to(data: w.WrdsData, t: pd.Timestamp) -> dict[str, pd.DataFrame]:
    frames = w.tilt_frames(data, "2016-12-30", "2018-12-31")
    return {k: frames[k].loc[:t] for k in ("prices", "eligible", "market_equity", "me_reason")}


def test_future_rows_change_nothing_up_to_the_decision_row() -> None:
    t = at("2018-06-29")
    frames = world_frames()
    shares = pd.concat([frames["crsp_stkshares"], pd.DataFrame(
        {"permno": [F], "shrstartdt": [t - pd.Timedelta(days=135)], "shrenddt": [at("2025-12-31")],
         "shrout": [7]})])
    shares.loc[shares["permno"] == F, "shrenddt"] = [t - pd.Timedelta(days=136), at("2025-12-31")]
    spells = pd.concat([frames["crsp_dsp500list_v2"], pd.DataFrame(
        {"permno": [B], "indno": [1000502], "mbrstartdt": [t + pd.Timedelta(days=1)], "mbrenddt": [CAL[-1]]})])
    delists = frames["crsp_stkdelists"].copy()
    delists.loc[delists["permno"] == C, "delactiontype"] = "GLI"        # C's delisting row comes after t
    future = make_data({**frames, "crsp_stkshares": shares, "crsp_dsp500list_v2": spells,
                        "crsp_stkdelists": delists})
    base, moved = frames_to(make_data(frames), t), frames_to(future, t)
    for key in base:
        pd.testing.assert_frame_equal(base[key], moved[key])
    later = w.tilt_frames(future, "2016-12-30", "2018-12-31")
    assert later["market_equity"].loc["2018-07-02", str(F)] != w.tilt_frames(
        make_data(frames), "2016-12-30", "2018-12-31")["market_equity"].loc["2018-07-02", str(F)]
    assert later["eligible"].loc["2018-07-02", str(B)]


def test_loader_supplies_ajexq_one_and_never_reads_urq_ajexq() -> None:
    """P-9 option (a): a current-vintage URQ ajexq (2 on quarters reported before A's split) changes nothing."""
    frames = world_frames()
    urq = frames["comp_urq"].copy()
    urq.loc[(urq["gvkey"] == f"G{A}") & (urq["prelimqprd"] < SPLIT), "ajexq"] = 2.0
    data = make_data(edit(frames, "comp_urq", urq))
    inputs = w.signal_inputs(data)
    assert len(inputs.fund_quarterly) and (inputs.fund_quarterly["ajexq"] == 1.0).all()
    pd.testing.assert_frame_equal(inputs.fund_quarterly, w.signal_inputs(make_data(world_frames())).fund_quarterly)
    report = w.intake_report(data)
    assert report["ajexq"]["urq"] == {"quarters_before_split": 4, "ajexq_one": 0}
    assert report["ajexq"]["supplied_one"] == report["ajexq"]["supplied_rows"] == len(inputs.fund_quarterly)
    assert "FAIL" not in w.intake_markdown(report)


def test_s2_across_a_split_matches_the_no_split_world() -> None:
    """A's quarters reported before its 2-for-1 split carry pre-split EPS (twice the post-split basis) and a
    current-vintage URQ ajexq 2; the quarters after it carry post-split EPS. With the supplied ajexq 1.0 and the
    cfacshr ratio, S2 equals S2 of the same firm with no split (halving is exact, so bit-identical)."""
    frames = world_frames()
    urq = frames["comp_urq"].copy()
    a = urq["gvkey"] == f"G{A}"
    k = np.arange(a.sum(), dtype=float)
    eps = 0.25 + 0.002 * k + 0.0005 * k**2                         # post-split basis; differences vary
    before = a & (urq["prelimqprd"] < SPLIT)
    urq.loc[a, "epspxq"] = eps
    urq.loc[before, "epspxq"] *= 2.0
    urq.loc[before, "ajexq"] = 2.0
    split = w.signal_inputs(make_data(edit(frames, "comp_urq", urq)))
    q, d = split.fund_quarterly, split.daily
    no_split = replace(split, daily=d.assign(cfacshr=d["cfacshr"].where(d["permno"] != A, 1.0)),
                       fund_quarterly=q.assign(epspxq=q["epspxq"].where(q["gvkey"] != f"G{A}", q["epspxq"] / np.where(
                           q["known_date"] < SPLIT, 2.0, 1.0))))
    r = at("2018-06-29")                     # q = 2018Q1 known after the split; q - 4 and the prior quarters before

    def s2(inputs: sig.SignalInputs) -> float:
        return sig.build_signals(inputs, pd.DatetimeIndex([r]))["values"]["S2"].loc[r, A]

    expected = s2(no_split)
    assert np.isfinite(expected) and s2(split) == expected
    # The URQ ajexq would count the split twice and move S2 (the defect P-9 avoids).
    urq_ajexq = q.assign(ajexq=np.where((q["gvkey"] == f"G{A}") & (q["known_date"] < SPLIT), 2.0, 1.0))
    assert s2(replace(split, fund_quarterly=urq_ajexq)) != pytest.approx(expected, rel=1e-3)


def test_non_usd_fy1_rows_drop_and_count_by_year() -> None:
    frames = world_frames()
    ibes = frames["ibes_statsumu_epsus"].copy()
    rows = ibes.index[(ibes["ticker"] == f"T{A}") & ibes["statpers"].dt.year.isin([2000, 2001])]
    ibes.loc[rows[[0, 1]], "curcode"] = "CAD"
    ibes.loc[rows[12], "curcode"] = None                           # a missing currency is not USD
    fy2 = ibes.loc[[rows[2]]].assign(fpi="2", curcode="CAD")       # only FY1 rows drop
    data = make_data(edit(frames, "ibes_statsumu_epsus", pd.concat([ibes, fy2], ignore_index=True)))
    inputs, drops = w.signal_tables(data)
    assert drops["ibes"] == {"no_key": 0, "non_usd_fy1": 3}
    assert drops["ibes_non_usd_fy1_by_year"] == {"2000": 2, "2001": 1}
    assert len(inputs.ibes) == len(ibes) + 1 - 3 and (inputs.ibes["fpi"] == "2").sum() == 1
    assert not inputs.ibes.merge(ibes.loc[rows[[0, 1, 12]], ["ticker", "statpers", "fpi"]]).shape[0]
    report = w.intake_report(data)
    assert report["ibes_fy1_rows"]["inputs"] == report["ibes_fy1_rows"]["file_usd"] == len(ibes) - 3
    text = w.intake_markdown(report)
    assert "FAIL" not in text and "dropped before `signal_inputs` returns: 3 (by year: 2000 2, 2001 1)" in text


# Card m55-loader-fix-r1 -------------------------------------------------------------------

def basis_rows(permno: int, spans: list[tuple[str, str, float, float]]) -> pd.DataFrame:
    """Daily rows on CAL in each (first, last, price, factor) span."""
    parts = [pd.DataFrame({"permno": permno, "date": CAL[(CAL >= first) & (CAL <= last)], "prc": price,
                           "dlycumfacshr": factor, "level": 1.0}) for first, last, price, factor in spans]
    return pd.concat(parts, ignore_index=True)


def facts_of(permno: int, facts: list[tuple[str, str, int]]) -> pd.DataFrame:
    table = pd.DataFrame(facts, columns=["shrstartdt", "shrenddt", "shrout"]).assign(permno=permno)
    table[["shrstartdt", "shrenddt"]] = table[["shrstartdt", "shrenddt"]].apply(pd.to_datetime)
    return table


def me_at(rows: pd.DataFrame, facts: pd.DataFrame, permno: int, day: str) -> pd.Series:
    out = w.market_equity(rows, facts, rows, CAL)
    return out[((rows["permno"] == permno) & (rows["date"] == at(day))).to_numpy()].iloc[0]


def test_me_basis_across_the_seal_or_missing_rows_is_unmapped_never_a_wrong_value() -> None:
    """Item 1, Opus probe: a 3-for-1 split inside the seal; the facts dated in the seal have no known basis."""
    rows = basis_rows(1, [("2019-01-02", "2019-07-30", 99.0, 3.0), ("2020-08-03", "2021-06-30", 33.0, 1.0)])
    facts = facts_of(1, [("2015-01-01", "2020-03-30", 208), ("2020-03-31", "2020-05-28", 208),
                         ("2020-05-29", "2020-08-02", 624), ("2020-08-03", "2025-12-31", 624)])
    assert me_at(rows, facts, 1, "2019-07-30")["market_equity"] == 99.0 * 208       # pre-seal: basis 3 = factor 3
    for day in ("2020-08-28", "2020-09-29", "2020-10-13", "2020-12-16"):             # a seal-dated fact is used
        cell = me_at(rows, facts, 1, day)
        assert np.isnan(cell["market_equity"]) and cell["me_reason"] == "unmapped"
        assert np.isnan(cell["share_count"]) and cell["basis_changed_across_gap"]
    assert me_at(rows, facts, 1, "2020-12-17")["market_equity"] == 33.0 * 624        # a post-seal fact: no gap
    # A gap of missing rows (a halt) with a factor change is unmapped; without a factor change the value stands.
    halt = [("2018-01-02", "2018-01-31", 20.0, 2.0), ("2018-03-01", "2018-08-31", 10.0, 1.0)]
    rows = pd.concat([basis_rows(2, halt), basis_rows(3, [(a, b, p, 1.0) for a, b, p, _ in halt])])
    facts = pd.concat([facts_of(p, [("2018-02-15", "2025-12-31", 1000)]) for p in (2, 3)])
    assert me_at(rows, facts, 2, "2018-07-31")["me_reason"] == "unmapped"
    assert me_at(rows, facts, 3, "2018-07-31")["market_equity"] == 10.0 * 1000


def test_post_seal_window_me_equals_the_full_history_value() -> None:
    """Item 1, GPT probe: a pre-seal fact used after a split in the seal keeps its pre-seal basis."""
    frames = world_frames()
    dsf = frames["crsp_dsf_v2"].copy()
    dsf.loc[(dsf["permno"] == F) & (dsf["dlycaldt"] < w.SEAL_START), "dlycumfacshr"] = 2.0
    shares = frames["crsp_stkshares"].copy()
    shares.loc[shares["permno"] == F, "shrenddt"] = at("2020-06-30")
    shares = pd.concat([shares, facts_of(F, [("2020-07-01", "2025-12-31", 2000)])], ignore_index=True)
    data = make_data({**frames, "crsp_dsf_v2": dsf, "crsp_stkshares": shares})
    frames_out = w.tilt_frames(data, "2020-08-31", "2020-12-31")
    rows = w.daily(data)
    full = w.market_equity(rows, w.frame(data, "crsp_stkshares", ["permno", "shrstartdt", "shrenddt", "shrout"]),
                           rows, w.calendar(data))
    price = rows.loc[(rows["permno"] == F) & (rows["date"] == at("2020-08-31")), "prc"].iloc[0]
    expected = full[((rows["permno"] == F) & (rows["date"] == at("2020-08-31"))).to_numpy()]["market_equity"]
    assert frames_out["market_equity"].loc["2020-08-31", str(F)] == expected.iloc[0] == price * 1000 * 2.0
    assert frames_out["me_reason"].loc["2020-11-16", str(F)] == "unmapped"         # the seal-dated fact


def s4_at(data: w.WrdsData, day: str) -> float | str:
    result = sig.build_signals(w.signal_inputs(data), pd.DatetimeIndex([at(day)]))
    value = result["values"]["S4"].loc[at(day), A]
    return result["reasons"]["S4"].loc[at(day), A] if np.isnan(value) else float(value)


def test_a_later_fiscal_key_conflict_never_removes_an_earlier_record() -> None:
    """Item 2, GPT probe: a second FY2016 record first known later loses; the earlier S4 does not change."""
    frames = world_frames()
    snap = frames["comp_snapshot_csa_pit"].copy()
    fy2016 = (snap["gvkey"] == f"G{A}") & (snap["datadate"] == at("2016-12-31"))
    snap.loc[fy2016, "revt"] = 3.0                                    # S4 = (revt - cogs) / at = 2
    later = snap[fy2016].assign(datadate=at("2017-01-31"), pitdate1=at("2017-09-15"), revt=9.0)
    vintage = snap[fy2016].assign(pitdate1=at("2017-10-02"))           # a later vintage of the first record
    snap = pd.concat([snap, vintage], ignore_index=True)
    fy2016 = (snap["gvkey"] == f"G{A}") & (snap["datadate"] == at("2016-12-31"))
    base = make_data(edit(frames, "comp_snapshot_csa_pit", snap))
    moved = make_data(edit(frames, "comp_snapshot_csa_pit", pd.concat([snap, later], ignore_index=True)))
    assert s4_at(base, "2017-08-31") == s4_at(moved, "2017-08-31") == 2.0
    assert s4_at(moved, "2017-10-31") == s4_at(base, "2017-10-31") == 2.0           # the later record lost
    assert w.signal_tables(moved)[1]["fund_annual"]["fiscal_key_conflict"] == 1
    # Two records of one fiscal year first known on the same date: both lose.
    tie = later.assign(pitdate1=snap.loc[fy2016, "pitdate1"].min())
    tied = make_data(edit(frames, "comp_snapshot_csa_pit", pd.concat([snap, tie], ignore_index=True)))
    assert w.signal_tables(tied)[1]["fund_annual"]["fiscal_key_conflict"] == 3     # both records, all their rows


def halted_delisting(frames: dict[str, pd.DataFrame], y_return: float) -> w.WrdsData:
    """E has no price and no return on 2018-11-08 to 2018-11-14; its Y row on 2018-11-15 spans from 11-07."""
    dsf = frames["crsp_dsf_v2"].copy()
    e = dsf["permno"] == E
    dsf.loc[e & dsf["dlycaldt"].between("2018-11-08", "2018-11-14"), ["dlyret", "dlyprc"]] = np.nan
    dsf.loc[e & (dsf["dlycaldt"] == LAST[E]), ["dlyret", "dlyprevdt"]] = [y_return, at("2018-11-07")]
    return make_data(edit(frames, "crsp_dsf_v2", dsf))


def test_no_settlement_before_the_delisting_row_and_a_later_y_row_changes_no_earlier_row() -> None:
    """Item 3, GPT probe: the -100 percent return settles on the Y row's date, not after the last price."""
    frames = world_frames()
    full_loss = halted_delisting(frames, -1.0)
    event = w.disappearances(full_loss).set_index("permanent_id").loc[str(E)]
    assert event["effective_date"] == event["known_at"] == LAST[E] and event["delisting_return"] == -1.0
    assert not event["reference_valued"]
    with pytest.raises(RunnerStop, match="terminal_gap_unsupported"):              # the engine needs a close at r - 1
        w.tilt_frames(full_loss, "2016-12-30", "2018-12-31")
    # Future perturbation: only the Y row changes; no row before it changes, and no event moves before it.
    for y_return in (-0.5, -0.3):
        other = halted_delisting(frames, y_return)
        event = w.disappearances(other).set_index("permanent_id").loc[str(E)]
        assert event["effective_date"] == CAL[CAL.get_loc(LAST[E]) + 1] and event["delisting_return"] == 0.0
        for left, right in ((w.daily(full_loss), w.daily(other)),):
            early = (left["date"] < LAST[E]).to_numpy()
            pd.testing.assert_frame_equal(left[early].drop(columns="dlyret"), right[early].drop(columns="dlyret"))
    half, third = (w.tilt_frames(halted_delisting(frames, r), "2016-12-30", "2018-12-31") for r in (-0.5, -0.3))
    for key in ("prices", "market_equity", "me_reason", "eligible", "path_break"):
        pd.testing.assert_frame_equal(half[key].loc[:"2018-11-14"], third[key].loc[:"2018-11-14"])
    assert (half["disappearances"]["effective_date"] > LAST[E]).loc[half["disappearances"]["permanent_id"] == str(E)].all()


def test_last_close_run_removes_the_terminal_return_from_the_path() -> None:
    """Item 4: a CIZ path with a -80 percent terminal return gives -80 percent by default and 0 in last_close."""
    frames = world_frames()
    dsf = frames["crsp_dsf_v2"].copy()
    y_row = (dsf["permno"] == C) & (dsf["dlycaldt"] == LAST[C])
    dsf.loc[y_row, ["dlyret", "dlycumfacpr", "dlycumfacshr", "shrout"]] = [-0.8, 1.0, 1.0, 1000]   # a priced Y row
    data = make_data(edit(frames, "crsp_dsf_v2", dsf))
    before, after = CAL[CAL.get_loc(LAST[C]) - 1], CAL[CAL.get_loc(LAST[C]) + 1]
    settled = {}
    for run in ("primary", "last_close"):
        out = w.tilt_frames(data, "2016-12-30", "2018-12-31", run=run)
        events = check_disappearances(out["disappearances"], out["calendar"], out["prices"].columns)
        engine = terminal_events(events, out["calendar"], run).set_index("permanent_id").loc[str(C)]
        reference = out["prices"].loc[engine["reference_date"], str(C)]
        settled[run] = reference * (1.0 + engine["terminal_return"]) / out["prices"].loc[before, str(C)] - 1.0
        if run == "primary":
            assert engine["effective_date"] == after
        else:
            assert engine["effective_date"] == LAST[C] and np.isnan(out["prices"].loc[LAST[C], str(C)])
            assert np.isnan(out["market_equity"].loc[LAST[C], str(C)])    # no ME without a close of this run
            assert (out["disappearances"]["delisting_return"] == 0.0).all()
    assert settled["primary"] == pytest.approx(-0.8, abs=1e-12) and settled["last_close"] == 0.0
    with pytest.raises(RunnerStop, match="event_run_invalid"):
        w.tilt_frames(data, "2016-12-30", "2018-12-31", run="other")


def test_daily_signal_shares_are_the_d5_count_and_driver_columns_pass() -> None:
    """Item 7 (and item 5): the daily signal table's shrout is the D5 count; primaryexch and dlyprcflg pass."""
    facts = facts_of(1, [("1985-01-01", "1990-12-30", 1000), ("1990-12-31", "2025-12-31", 3000)])
    days = pd.bdate_range("1985-01-01", "1991-06-28")
    rows = pd.DataFrame({"permno": 1, "date": days, "prc": 10.0, "dlycumfacshr": 1.0, "level": 1.0})
    out = w.market_equity(rows, facts, rows, days).set_index(rows["date"])["share_count"]
    assert out[at("1991-02-28")] == 1000 and out[at("1991-05-15")] == 1000             # 1990-12-31 + 135 days
    assert out[at("1991-05-16")] == 3000                                              # 1990-12-31 + 136 days
    frames = world_frames()
    shares = frames["crsp_stkshares"].copy()
    shares.loc[shares["permno"] == B, "shrenddt"] = at("1999-12-30")
    shares = pd.concat([shares, facts_of(B, [("1999-12-31", "2025-12-31", 3000)])], ignore_index=True)
    shares.loc[shares["permno"] == D, "shrenddt"] = at("1990-12-31")   # D: every count is stale
    data = make_data(edit(frames, "crsp_stkshares", shares))
    table = w.signal_inputs(data).daily.set_index(["permno", "date"])
    assert table.loc[D, "shrout"].isna().all()
    assert table.loc[(B, at("2000-05-12")), "shrout"] == 1000 and table.loc[(B, at("2000-05-15")), "shrout"] == 3000
    assert table.loc[(A, at("2018-03-01")), "shrout"] == 500 * 2.0                    # the 500 count on the 2018 basis
    assert {"primaryexch", "dlyprcflg"} <= set(table.columns)
    report = w.intake_report(data)
    days = w.member_days(data)
    assert report["bid_ask_member_days"] == {"member_days": len(days), "bid_ask": int((days["dlyprcflg"] == "BA").sum())}
    assert report["bid_ask_member_days"]["bid_ask"] > 0 and report["terminal_gap_events"] == {"primary": 0,
                                                                                              "last_close": 0}
    assert "FAIL" not in w.intake_markdown(report)


def test_quarterly_conflicts_use_each_table_clock_and_the_first_known_record_wins() -> None:
    """Item 2 on URQ: fund_quarterly ranks records by known date, announcements by rdq (public on rdq)."""
    frames = world_frames()
    urq, fundq = frames["comp_urq"].copy(), frames["comp_fundq"].copy()
    g = f"G{A}"
    extra = pd.DataFrame([
        # Q4 2016 again on an earlier datadate, known and announced after the 2016-12-31 record: it loses twice.
        {"gvkey": g, "datadate": at("2016-11-30"), "fqtr": 4.0, "rdq": at("2017-09-10"),
         "prelimqprd": at("2017-09-15"), "finalqprd": at("2017-10-15"), "epspxq": 9.0, "ajexq": 1.0},
        # Q3 2016 again: announced before the 2016-09-30 record (rdq 10-20 < 10-25) but known after it (12-15).
        {"gvkey": g, "datadate": at("2016-08-31"), "fqtr": 3.0, "rdq": at("2016-10-20"),
         "prelimqprd": at("2016-12-15"), "finalqprd": at("2017-01-15"), "epspxq": 9.0, "ajexq": 1.0},
        # Q2 2016 again with no rdq and no period date: never known, so it loses (never wins by a missing date).
        {"gvkey": g, "datadate": at("2016-05-31"), "fqtr": 2.0, "rdq": pd.NaT, "prelimqprd": pd.NaT,
         "finalqprd": pd.NaT, "epspxq": 9.0, "ajexq": 1.0}])
    keys = pd.DataFrame({"gvkey": g, "datadate": extra["datadate"], "fyearq": 2016, "ajexq": 1.0})
    data = make_data({**frames, "comp_urq": pd.concat([urq, extra], ignore_index=True),
                      "comp_fundq": pd.concat([fundq, keys], ignore_index=True)})
    inputs, drops = w.signal_tables(data)
    sig.check_inputs(inputs)

    def kept(table: pd.DataFrame, fqtr: int) -> pd.Timestamp:
        rows = table[(table["gvkey"] == g) & (table["fyearq"] == 2016) & (table["fqtr"] == fqtr)]
        assert rows["datadate"].nunique() == 1
        return rows["datadate"].iloc[0]

    assert kept(inputs.fund_quarterly, 4) == kept(inputs.announcements, 4) == at("2016-12-31")
    assert kept(inputs.fund_quarterly, 3) == at("2016-09-30") and kept(inputs.announcements, 3) == at("2016-08-31")
    assert kept(inputs.fund_quarterly, 2) == kept(inputs.announcements, 2) == at("2016-06-30")
    assert drops["announcements"]["fiscal_key_conflict"] == 3
    assert drops["fund_quarterly"]["fiscal_key_conflict"] == 2 and drops["fund_quarterly"]["no_known_date"] == 1


def test_delisting_timing_holds_for_a_missing_y_return_and_in_the_last_close_run() -> None:
    """Item 3 with a Y row without a return, and item 4: the last_close run keeps the item 3 timing."""
    frames = world_frames()
    missing = halted_delisting(frames, np.nan)
    event = w.disappearances(missing).set_index("permanent_id").loc[str(E)]
    assert event["effective_date"] == event["known_at"] == LAST[E] and np.isnan(event["delisting_return"])
    assert not event["reference_valued"]
    with pytest.raises(RunnerStop, match="terminal_gap_unsupported"):
        w.tilt_frames(missing, "2016-12-30", "2018-12-31")
    for y_return in (-1.0, -0.5, np.nan):
        data = halted_delisting(frames, y_return)
        event = w.disappearances(data, "last_close").set_index("permanent_id").loc[str(E)]
        assert event["effective_date"] == event["known_at"] == LAST[E] and event["delisting_return"] == 0.0
        assert not event["reference_valued"]
        with pytest.raises(RunnerStop, match="terminal_gap_unsupported"):
            w.tilt_frames(data, "2016-12-30", "2018-12-31", run="last_close")
    report = w.intake_report(missing)
    assert report["terminal_gap_events"] == {"primary": 1, "last_close": 1}
    assert "- FAIL: D6: no event settles after rows without a value" in w.intake_markdown(report)


def test_driver_columns_and_bid_ask_share_match_the_source_rows() -> None:
    """Item 5: primaryexch and dlyprcflg carry the source values; the BA share counts member-days from the source."""
    frames = world_frames()
    data = make_data(frames)
    table = w.signal_inputs(data).daily
    source = frames["crsp_dsf_v2"].rename(columns={"dlycaldt": "date"})
    joined = table.merge(source[["permno", "date", "primaryexch", "dlyprcflg"]], on=["permno", "date"],
                         suffixes=("", "_source"), validate="one_to_one")
    assert len(joined) == len(table) and set(joined["primaryexch"]) == {"N", "Q"}
    assert (joined["primaryexch"] == joined["primaryexch_source"]).all()
    assert (joined["dlyprcflg"] == joined["dlyprcflg_source"]).all()
    spells = frames["crsp_dsp500list_v2"]
    member = source.merge(spells, on="permno")
    member = member[(member["date"] >= member["mbrstartdt"]) & (member["date"] <= member["mbrenddt"])]
    expected = int((member["dlyprcflg"] == "BA").sum())
    assert expected > 0 and w.intake_report(data)["bid_ask_member_days"]["bid_ask"] == expected


# Card m55-loader-r6 -----------------------------------------------------------------------

def test_seal_listing_without_a_prior_factor_row_is_unmapped_never_half_the_shares() -> None:
    """Item 1, case A: the first row is after the seal and the fact is dated in the seal; a 2-for-1 split in the
    seal after it makes the post-seal factor 1 and the true count 200. The basis is not observed: unmapped."""
    rows = pd.concat([basis_rows(4, [("2020-08-03", "2021-06-30", 30.0, 1.0)]),
                      basis_rows(5, [("2020-08-03", "2021-06-30", 30.0, 1.0)])])
    facts = pd.concat([facts_of(4, [("2020-04-03", "2020-08-02", 100), ("2020-08-03", "2025-12-31", 200)]),
                       facts_of(5, [("2019-06-03", "2020-08-02", 100), ("2020-08-03", "2025-12-31", 200)])])
    for permno in (4, 5):                                       # a fact dated in the seal, or before it
        for day in ("2020-08-17", "2020-10-15", "2020-12-16"):  # the old fact is in use (date + 136 days)
            cell = me_at(rows, facts, permno, day)
            assert np.isnan(cell["market_equity"]) and cell["me_reason"] == "unmapped"
            assert np.isnan(cell["share_count"]) and cell["basis_unseen"] == "seal"
            assert not cell["basis_changed_across_gap"]
        cell = me_at(rows, facts, permno, "2020-12-17")         # a fact dated after the seal: observed basis
        assert cell["share_count"] == 200 and cell["market_equity"] == 30.0 * 200 and pd.isna(cell["basis_unseen"])
    days = DAYS[~w.in_seal(DAYS)]                               # a calendar whose first post-seal row is SEAL_END
    rows = pd.DataFrame({"permno": 12, "date": days[days >= w.SEAL_END], "prc": 30.0, "dlycumfacshr": 1.0,
                         "level": 1.0})
    out = w.market_equity(rows, facts_of(12, [("2020-04-03", "2025-12-31", 100)]), rows, days)
    used = (rows["date"] >= at("2020-08-17")).to_numpy()
    assert rows["date"].iloc[0] == w.SEAL_END and (out.loc[used, "basis_unseen"] == "seal").all()
    assert out.loc[used, "share_count"].isna().all() and (out.loc[used, "me_reason"] == "unmapped").all()


def test_data_start_fact_without_a_prior_factor_row_is_unmapped_until_an_observed_fact_is_used() -> None:
    """Item 1, case B: the PERMNO trades on the first calendar row and the fact is dated before it, so a split
    between the two is not seen; the first row is the basis row, so no gap shows."""
    rows = pd.concat([basis_rows(6, [(str(CAL[0].date()), "1994-06-30", 40.0, 1.0)]),
                      basis_rows(7, [(str(CAL[0].date()), "1994-06-30", 40.0, 1.0)])])
    facts = pd.concat([facts_of(6, [("1992-06-01", "1993-01-14", 100), ("1993-01-15", "2025-12-31", 200)]),
                       facts_of(7, [("1992-06-01", "1992-07-01", 100)])])
    for day in (str(CAL[0].date()), "1993-05-28"):              # the 1992-06-01 fact is in use
        cell = me_at(rows, facts, 6, day)
        assert np.isnan(cell["market_equity"]) and cell["me_reason"] == "unmapped"
        assert np.isnan(cell["share_count"]) and cell["basis_unseen"] == "data_start"
    cell = me_at(rows, facts, 6, "1993-05-31")                  # 1993-01-15 + 136 days: observed basis
    assert cell["share_count"] == 200 and cell["market_equity"] == 40.0 * 200 and pd.isna(cell["basis_unseen"])
    stale = me_at(rows, facts, 7, "1993-01-04")                 # a stale fact keeps its reason and is not counted
    assert stale["me_reason"] == "stale_share_fact" and pd.isna(stale["basis_unseen"])


def test_prior_factor_row_and_observed_gaps_keep_the_fix_r1_rule() -> None:
    """Item 1 control: with a factor row before the fact, the fix-r1 rule decides (a factor change across the seal
    is unmapped, no change keeps the value); a fact before the first row inside the calendar keeps its value."""
    pre, post = ("2019-01-02", "2019-07-30"), ("2020-08-03", "2021-06-30")
    rows = pd.concat([basis_rows(8, [(*pre, 60.0, 2.0), (*post, 30.0, 1.0)]),
                      basis_rows(9, [(*pre, 30.0, 1.0), (*post, 30.0, 1.0)]),
                      basis_rows(10, [(*post, 30.0, 1.0)])])
    facts = pd.concat([facts_of(p, [("2020-04-03", "2025-12-31", 100)]) for p in (8, 9)]
                      + [facts_of(10, [("2020-08-03", "2025-12-31", 100)])])
    changed = me_at(rows, facts, 8, "2020-10-15")
    assert changed["me_reason"] == "unmapped" and changed["basis_changed_across_gap"]
    assert pd.isna(changed["basis_unseen"])
    for permno, day in ((9, "2020-10-15"), (10, "2020-12-17")):
        cell = me_at(rows, facts, permno, day)
        assert cell["market_equity"] == 30.0 * 100 and pd.isna(cell["basis_unseen"])
    early = basis_rows(11, [("2019-01-02", "2019-07-30", 99.0, 3.0)])     # fact 2015, first row 2019 (pre-seal)
    cell = me_at(early, facts_of(11, [("2015-01-01", "2025-12-31", 208)]), 11, "2019-07-30")
    assert cell["market_equity"] == 99.0 * 208 and pd.isna(cell["basis_unseen"])


def test_intake_counts_unseen_share_bases_by_case_and_year() -> None:
    """Item 1 counter: C's only fact is dated before the first calendar row (data_start on each C row but the
    delisting row, which has no factor and is unmapped anyway); B has no row before the seal (seal on every B row,
    none a member-day). Counts by year and the last date, for all rows and for member-days; ME is unmapped."""
    frames = world_frames()
    shares = frames["crsp_stkshares"].copy()
    shares.loc[shares["permno"] == C, "shrstartdt"] = at("1985-01-01")
    dsf = frames["crsp_dsf_v2"]
    dsf = dsf[(dsf["permno"] != B) | (dsf["dlycaldt"] >= w.SEAL_END)]
    data = make_data({**frames, "crsp_stkshares": shares, "crsp_dsf_v2": dsf})
    def counted(days: pd.DatetimeIndex) -> dict:
        years = pd.Series(days).dt.year.value_counts().sort_index()
        return {"by_year": {str(y): int(n) for y, n in years.items()},
                "last": str(days[-1].date()) if len(days) else None}

    c_days, b_days = CAL[CAL < LAST[C]], CAL[CAL >= w.SEAL_END]
    report = w.intake_report(data)
    assert report["share_basis_unseen"] == {
        "data_start": {"rows": counted(c_days), "member_days": counted(c_days[c_days >= FIRST])},
        "seal": {"rows": counted(b_days), "member_days": counted(b_days[:0])}}
    me = w.member_market_equity(data)
    rows = w.daily(data).loc[me.index]
    assert (me.loc[rows["permno"].isin([B, C]).to_numpy(), "me_reason"] == "unmapped").all()
    assert me.loc[~rows["permno"].isin([B, C]).to_numpy(), "basis_unseen"].isna().all()
    frames_out = w.tilt_frames(data, "2016-12-30", "2018-12-31")
    assert frames_out["market_equity"][str(C)].isna().all()
    text = w.intake_markdown(report)
    assert f"- `data_start`: {len(c_days)} rows" in text and f"- `seal`: {len(b_days)} rows" in text
    assert "- `seal`: 0 member-days (by year: none); last date n/a." in text
    assert "FAIL" not in text and all(str(p) not in text for p in (*MEMBERS, SPY))
