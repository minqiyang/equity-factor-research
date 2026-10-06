"""Synthetic tests for the Milestone 5.5 WRDS loader (card m55-loader).

Every table is generated here; no test reads the WRDS folder or opens a network connection.
"""

from __future__ import annotations

import hashlib
import json
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
from research.m55_index_tilt import TiltInputs, check_disappearances, check_inputs


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
                          "dlyvol": 100.0})
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
    shares = pd.DataFrame({"permno": [*MEMBERS, SPY], "shrstartdt": at("1985-01-01"),
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
    rows = pd.DataFrame({"permno": 1, "date": pd.to_datetime(["1985-01-02", "2018-06-29"]),
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
                                    "fiscal_key_conflict": 2}
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


def test_ajexq_must_be_first_reported_before_a_split(world: w.WrdsData) -> None:
    check = w.ajexq_check(world)
    assert check["quarters_before_split"] == check["ajexq_one"] == 4
    quarters = world_frames()["comp_urq"]
    a_before = int(((quarters["gvkey"] == f"G{A}") & (quarters["datadate"] < SPLIT)).sum())
    assert check["urq_rows_matched"] == len(quarters) and check["urq_equal_current"] == len(quarters) - a_before
    frames = world_frames()
    urq = frames["comp_urq"].copy()
    before = (urq["gvkey"] == f"G{A}") & urq["rdq"].between(SPLIT - pd.Timedelta(days=365), SPLIT)
    urq.loc[before, "ajexq"] = 2.0                                  # a current-vintage factor after the split
    data = make_data(edit(frames, "comp_urq", urq))
    with pytest.raises(RunnerStop, match="ajexq_not_first_reported"):
        w.signal_inputs(data)
    report = w.intake_report(data)
    assert report["ajexq_check"]["passed"] is False and report["ajexq_check"]["ajexq_one"] == 0
    assert "- FAIL: URQ `ajexq` is first-reported" in w.intake_markdown(report)
