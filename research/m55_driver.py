"""Milestone 5.5: run the frozen trial file from the coverage counts to the check period (cards m55-driver and
m55-confirm).

The driver runs ``docs/preregistrations/m55_trial_family_v1.json`` (status FROZEN, amendments 1 to 3) on the WRDS
working copy and the quote copy of the second pull in seven stages, in this order:

1. ``coverage``: signal validity counts and real starts, ME coverage, and the missingness census. No return.
2. ``calibration``: the low-risk ``g`` from ex-ante second moments, once, on the primary panel. No book return.
3. ``look``: CW-PIT against ``vwretd`` over the screen months, the only look before any tilt return, and the
   ``path_break_held`` blank set of each loader run.
4. ``screen``: each candidate alone as a 2 percent TE tilt against the CW-PIT of the same run, with the reports owed.
5. ``freeze``: the shortlist record and its digest (``m55_criteria.freeze_shortlist``).
6. ``confirm``: test A and the secondary family over 1993-02 to 2014-03, and the Family A baseline over the screen
   months, after ``verify_frozen_screen`` on the run 2 digest that amendment 3 states.
7. ``check``: the check means and the test A label over 2014-04 to ``check_period_end``, ``CHECK_GAP_MONTHS`` left
   out. It runs after a confirm stop too, because declared runs stay visible (R9).

Coverage comes before any return and the look comes before any tilt return (``declaration_timing``,
``candidates.real_start``, ``pre_tilt_look``). After the coverage stop of test B (amendment 2), the low-risk book gets
no ``g``, no engine call, and no return in any period, and test A uses p_B = 1.0 in Holm.

Confirm and check (amendment 3): three engine segments start from cash, with dates from the calendar
(``segment_plan``), and each cuts every input at its end row. Every book pays the half-spread override
(``m55_index_tilt.spread_rates``) on quotes of the second pull that pass ``quote_files`` and ``quote_table``. The
signal sets are the frozen composite, S1 to S8 alone, and the Family A baseline. The driver calls the pinned
criteria functions in the order of ``m55_criteria.primary_decision``; it does not call that function, because
it always runs the low-risk test.

Gates (R9): each stage writes ``<stage>.json`` and ``<stage>.sha256`` to a folder outside every Git checkout and
never overwrites them. A stage refuses unless every earlier stage file exists, matches its digest, was made from the
same trial file, code, and data, and names the digests of the stages before it. The look, the screen, and the freeze
also refuse unless the saved calibration decision is ``chosen`` or ``ratio_coverage_low`` (amendment 2), and each of
them records test B as stopped after ``ratio_coverage_low``. The freeze parses no data table. Each criteria output is
appended with its declaration to ``run_log.jsonl``, and so is each refusal.

Period: up to the freeze, every signal-input table, the engine frames, and ``vwretd`` are cut at the last screen
row (1992-12-31) right after the load. The engine frames keep the first row of 1993 as a date with no value, because
``m55_index_tilt.check_inputs`` accepts an end row only when a later row in a later month follows it. Each signal
build, engine call, and criteria call refuses a value after 1992-12-31. Outputs hold aggregates, dates, and weights
only: no PERMNO, ticker, or name.

R4: the rerun is a second engine call on ``tilt_frames(run="last_close")``. Fragility is a sign flip of an active
annual mean between the two calls. The driver never reads the engine fields ``fragile_active_sign`` and
``fragile_lowrisk_active_sign``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from research import m55_criteria as crit
from research import m55_index_tilt as tilt
from research import m55_signals as sig
from research import m55_wrds_loader as w
from research.m4_7_family_a import FAMILY_A, family_a_signals
from research.m55_index_tilt import refuse


REPO = Path(__file__).resolve().parents[1]
TRIAL_FILE = "docs/preregistrations/m55_trial_family_v1.json"
TRIAL_SHA256 = "6ccad16d3f2a1274f8448dfbbb7e0491c26c04186d75a0a4c2a69aef02e8a54d"   # the frozen file this driver runs
TRACKED_MANIFEST = "reports/wrds_manifest_2025.json"
QUOTE_MANIFEST = "reports/wrds_quotes_manifest_2025.json"     # the second pull (amendment 3 one-pull rule)
QUOTE_STEM = "crsp_dsf_v2_quotes"
QUOTE_COLUMNS = ["permno", "dlycaldt", "dlybid", "dlyask", "dlyprcflg"]
CODE_FOLDERS = ("research", "src")               # every module of the run; one digest over their Python files
STAGES = ("coverage", "calibration", "look", "screen", "freeze", "confirm", "check")
QUOTE_STAGES = ("confirm", "check")              # the stages that parse the quote table
RUNS = tilt.EVENT_RUNS                           # ("primary", "last_close"): the two loader runs of R4
CASES = tuple(tilt.COST_SCALES)                  # ("primary", "sensitivity_2x")
COVERAGE_FIRST = pd.Period("1963-01", "M")       # real-start panel: return months 1963-01 to 1992-12
S7_MONTHS = pd.period_range("1963-01", "1964-12", freq="M")
POST_SEAL_ANCHOR = pd.Timestamp("2021-07-30")    # periods.check.left_out: the post-seal engine segment starts here
POST_SEAL_FIRST_REBALANCE = pd.Timestamp("2021-08-31")
PRE_SEAL_LAST = crit.CHECK_GAP_MONTHS[0] - 1     # 2019-06: the last pre-seal check month
POST_SEAL_FIRST = crit.CHECK_GAP_MONTHS[-1] + 1  # 2021-09: the first post-seal check month
# reports_owed.check_gap_months: the part of periods.check.left_out that each gap month belongs to.
GAP_PARTS = (("seal", "2019-07", "2020-07"), ("sealed_2020_07_31_row", "2020-08", "2020-08"),
             ("warm_up", "2020-09", "2021-08"))
END_REASONS = {"screen": "row_after_screen_end", "confirm": "row_after_confirm_end", "check": "row_after_check_end"}
COMPOSITE = "composite"
FAMILY_A_SET = "family_a_baseline"
SECONDARY = (*sig.SIGNAL_IDS, FAMILY_A_SET)      # secondary_family.members, in order
# candidates.family_a_baseline.crsp_inputs (OI-12): Gao and Ritter (2010) volume divisors on primaryexch 'Q' rows.
GAO_RITTER = ((None, 2.0), ("2001-02-01", 1.8), ("2002-01-01", 1.6), ("2004-01-01", 1.0))
NASDAQ = "Q"
GAO_RITTER_TEXT = "2.0 before 2001-02, 1.8 from 2001-02 to 2001-12, 1.6 in 2002 and 2003, 1.0 from 2004"
RUN2_DIGEST = re.compile(r"run 3 must repeat the run 2 digest ([0-9a-f]{64})")
NO_SIGNAL = "NO_SIGNAL"                          # an all-missing set: every composite is 0, so TILT equals CW-PIT
BLANK = crit.BLANK_REASONS[0]                    # path_break_held
EXIT_CLASSES = w.EXIT_CLASSES
GO_ON = ("chosen", "ratio_coverage_low")         # the calibration decisions after which the later stages run
TEST_B_STOPPED = "stopped_coverage"              # test B's label after ratio_coverage_low (amendment 2)
# The engine frames' row after the last screen row: a date with these blank values (the loader's fill for a cell
# without a daily row).
BLANK_ROW = {"prices": np.nan, "market_equity": np.nan, "path_break": False, "eligible": False,
             "me_reason": tilt.ME_REASONS[0]}
# The dates of a signal-input row: the row is after the last screen row when one of them is after it.
SIGNAL_DATES = {"daily": ("date",), "index_daily": ("date",), "members": ("start",), "fund_annual": ("known_date",),
                "fund_quarterly": ("known_date",), "announcements": ("datadate", "rdq"), "link": ("linkdt",),
                "ibes_link": ("sdate",), "ibes": ("statpers",)}
NUMBER = r"(-?\d+(?:\.\d+)?(?:e-?\d+)?)"


# Frozen rules -----------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stated(text: str, name: str) -> float:
    """The number the trial file states for ``name``: ``NAME = 0.5``, ``NAME 1e-9``, or ``0.01 a year (NAME)``."""
    found = (re.search(rf"\b{name} = {NUMBER}", text) or re.search(rf"\b{name} {NUMBER}", text)
             or re.search(rf"{NUMBER}(?: [a-z]+){{0,2}} \({name}\)", text))
    if not found:
        raise refuse("trial_rule_missing", name)
    return float(found.group(1))


def schedule(rows: list) -> tuple:
    return tuple((None if first is None else str(first), float(c), float(s)) for first, c, s in rows)


def check_trial(trial: Mapping[str, Any], repo: Path = REPO) -> None:
    """Refuse unless every rule value the driver uses equals the frozen file and every pinned file has its bytes."""
    def need(ok: bool, what: str) -> None:
        if not ok:
            raise refuse("trial_rule_mismatch", what)

    need(str(trial.get("status", "")).startswith("FROZEN"), "status is not FROZEN")
    need(trial["evidence_ceiling"]["value"] == "DIAGNOSTIC_ONLY", "evidence_ceiling.value")
    books, costs = trial["books"], trial["books"]["costs"]
    need(schedule(costs["SCREEN_COST_SCHEDULE"]) == crit.SCREEN_COST_SCHEDULE, "SCREEN_COST_SCHEDULE")
    need(schedule(costs["COST_SCHEDULE"]) == tilt.COST_SCHEDULE, "COST_SCHEDULE")
    need(costs["which_schedule"].startswith("screen runs use SCREEN_COST_SCHEDULE only"), "which_schedule")
    need(costs["scales"] == tilt.COST_SCALES and costs["every_case_at_2x"] is True, "cost scales")
    rules = books["tilt"]
    for field, name, value in (("weight", "TILT_STRENGTH", tilt.TILT_STRENGTH), ("stock_cap", "STOCK_CAP",
                               tilt.STOCK_CAP), ("te_target", "TE_TARGET", tilt.TE_TARGET),
                               ("te_estimate", "COV_ROWS", tilt.COV_ROWS),
                               ("loop", "CAP_TOLERANCE", tilt.CAP_TOLERANCE),
                               ("loop", "RENORMALIZE_LOOPS", tilt.RENORMALIZE_LOOPS),
                               ("loop", "TE_TOLERANCE", tilt.TE_TOLERANCE),
                               ("loop", "BUDGET_TOLERANCE", tilt.BUDGET_TOLERANCE)):
        need(stated(rules[field], name) == value, name)
    low, calibration = books["low_risk"]["construction"], books["low_risk"]["calibration"]
    need(stated(low, "LOWRISK_CAP") == tilt.LOWRISK_CAP and stated(low, "LOWRISK_TE") == tilt.LOWRISK_TE,
         "LOWRISK_CAP, LOWRISK_TE")
    need(tuple(float(g) for g in calibration["grid"]) == tilt.LOWRISK_GRID, "low-risk grid")
    need(stated(calibration["target"], "LOWRISK_TARGET_RATIO") == tilt.LOWRISK_TARGET_RATIO, "LOWRISK_TARGET_RATIO")
    need(f"screen rebalances ({crit.SCREEN_START} to {crit.SCREEN_END})" in calibration["target"],
         "calibration rebalances")
    need(stated(calibration["ratio"], "LOWRISK_RATIO_MIN_ROWS") == tilt.LOWRISK_RATIO_MIN_ROWS,
         "LOWRISK_RATIO_MIN_ROWS")
    need(stated(calibration["choice"], "LOWRISK_UNDEFINED_MAX") == tilt.LOWRISK_UNDEFINED_MAX,
         "LOWRISK_UNDEFINED_MAX")
    need('once, on the tilt_frames(run="primary") panel' in calibration["order"] and "never recalibrates" in
         books["disappearance_r4"]["last_close_rerun"], "one calibration on the primary panel")
    need(f"run after the calibration decision {' or '.join(GO_ON)}." in
         trial["declaration_timing"]["order_after_freeze"], "calibration go-on rule")
    need(f"label {TEST_B_STOPPED}; p_B = 1.0; the Holm family keeps size 2." in
         trial["primary_family"]["test_B"]["after_coverage_stop"], "test B stop")
    need(trial["screen_and_shortlist"]["shortlist_rule"] == crit.SHORTLIST_RULE, "shortlist rule")
    screen = trial["periods"]["screen"]
    need(screen["first"].startswith(str(crit.SCREEN_START)) and screen["last"] == str(crit.SCREEN_END)
         and screen["min_months"] == crit.SCREEN_MIN_MONTHS, "screen period")
    need(trial["pre_tilt_look"]["period"] == f"screen months {crit.SCREEN_START} to {crit.SCREEN_END}",
         "pre_tilt_look.period")
    need("vwretd as is" in trial["data"]["benchmarks"]["before_1993_02"], "vwretd benchmark")
    candidates = trial["candidates"]
    need(tuple(c["id"] for c in candidates["list"]) == sig.SIGNAL_IDS, "candidate IDs")
    need({c["id"]: c["sign"] for c in candidates["list"]} == sig.SIGNS, "signs")
    need({c["id"]: c["max_age_months"] for c in candidates["list"]} == sig.MAX_AGE_MONTHS, "max ages")
    need(tuple(candidates["reasons"]) == sig.REASONS, "reasons")
    need(stated(candidates["backfill"], "MIN_ANNUAL_RECORDS") == sig.MIN_ANNUAL_RECORDS
         and stated(candidates["backfill"], "MIN_QUARTER_RECORDS") == sig.MIN_QUARTER_RECORDS, "backfill")
    need(f"return months {COVERAGE_FIRST} to {crit.SCREEN_END}" in candidates["real_start"]
         and f"= {sig.COVERAGE_NUMERATOR} / {sig.COVERAGE_DENOMINATOR}" in candidates["real_start"], "real start")
    need("half_rule(1) = 1" in candidates["composite"]["single_candidate_runs"] and tilt.half_rule(1) == 1,
         "single-candidate min_valid")
    need(trial["data"]["seal"]["window"] == f"[{sig.SEAL[0].date()}, {sig.SEAL[1].date()})", "seal window")
    need(f"anchor {POST_SEAL_ANCHOR.date()} (first rebalance {POST_SEAL_FIRST_REBALANCE.date()}"
         in trial["periods"]["check"]["left_out"], "post-seal anchor")
    need(f"the reason {BLANK}" in trial["data"]["loader_rules"]["P1_path_break"], "P1_path_break blank reason")
    # Confirm and check (amendment 3).
    need(len(RUN2_DIGEST.findall(trial["declaration_timing"].get("amendment_3", ""))) == 1, "run 2 digest")
    override = costs["half_spread_override"]
    need("scale x max(the spread of the dated schedule at r, the CRSP closing half-spread at r - 1)" in override
         and "10,000 x (ask - bid) / (ask + bid)" in override
         and [override.find(r) for r in tilt.QUOTE_REASONS] == sorted(override.find(r) for r in tilt.QUOTE_REASONS)
         and min(override.find(r) for r in tilt.QUOTE_REASONS) >= 0 and QUOTE_MANIFEST in override,
         "half_spread_override")
    confirm, check = trial["periods"]["confirm"], trial["periods"]["check"]
    need((confirm["first"], confirm["last"], confirm["months"]) == (str(crit.CONFIRM_START), str(crit.CONFIRM_END),
                                                                   crit.CONFIRM_MONTHS), "confirm period")
    need(check["first"] == str(crit.CHECK_START) and f"months {crit.CHECK_START} to {PRE_SEAL_LAST}" in
         check["segments"] and f"months {POST_SEAL_FIRST} to check_period_end" in check["segments"], "check period")
    need(f"CONFIRM_FLOOR = {crit.CONFIRM_FLOOR}" in trial["stop_rule"]["after_confirm"]
         and stated(trial["primary_family"]["correction"], "ALPHA") == crit.ALPHA, "CONFIRM_FLOOR, ALPHA")
    secondary = trial["secondary_family"]
    need(secondary["family_size"] == len(SECONDARY) and secondary["members"][:-1] == list(sig.SIGNAL_IDS),
         "secondary family")
    family = candidates["family_a_baseline"]
    need(tuple(family["signals"]) == tuple(f.factor_id for f in FAMILY_A)
         and family["min_valid"] == tilt.MIN_VALID_SIGNALS, "Family A baseline")
    need(GAO_RITTER_TEXT in family["crsp_inputs"]["amihud_nasdaq_divisor"]
         and family["crsp_inputs"]["low_beta_market_series"].startswith(f"INDNO {sig.MARKET_INDNO}"),
         "Family A CRSP inputs")
    need(set(next(o for o in trial["open_items"] if o["id"] == "OI-08")["publication_years"]) == set(sig.SIGNAL_IDS),
         "publication years")
    need("half_spread" in trial["reports_owed"], "reports_owed.half_spread")
    for path, pin in trial["code_pins"].items():
        if path == "statement" or pin["commit"] is None:
            continue
        need(sha256_bytes((repo / path).read_bytes()) == pin["file_sha256"], f"code pin {path}")


def run2_digest(trial: Mapping[str, Any]) -> str:
    """The run 2 freeze digest that amendment 3 states; the confirm and check stages give it to
    ``verify_frozen_screen`` (``screen_and_shortlist.freeze``)."""
    return RUN2_DIGEST.search(trial["declaration_timing"]["amendment_3"]).group(1)


def load_trial(repo: Path = REPO) -> tuple[dict[str, Any], str]:
    """The trial file, refused unless its bytes are the frozen file (``TRIAL_SHA256``) and ``check_trial`` passes."""
    raw = (repo / TRIAL_FILE).read_bytes()
    digest = sha256_bytes(raw)
    if digest != TRIAL_SHA256:
        raise refuse("trial_digest_mismatch", "the trial file is not the frozen file that this driver runs")
    trial = json.loads(raw)
    check_trial(trial, repo)
    return trial, digest


def check_data(data: w.WrdsData, tracked: Mapping[str, Any], trial: Mapping[str, Any]) -> str:
    """Refuse unless the working copy is the tracked manifest's data and vintage; return the files digest."""
    files = {name: {"rows": int(r["rows"]), "sha256": r["sha256"]} for name, r in data.manifest["files"].items()}
    known = {name: {"rows": int(r["rows"]), "sha256": r["sha256"]} for name, r in tracked["files"].items()}
    if files != known:
        raise refuse("data_manifest_mismatch", "the working copy differs from the tracked manifest")
    if not data.manifest["vintage"] == tracked["vintage"] == trial["data"]["vintage"]:
        raise refuse("data_manifest_mismatch", "vintage")
    return sha256_bytes(json.dumps(files, sort_keys=True).encode())


def data_files(root: str | Path) -> w.WrdsData:
    """The working copy for the freeze: the manifest after a SHA-256 check of each file's bytes, and no table.

    No table is parsed. ``check_data`` reads only the manifest, so it gives the same digest as after ``w.load``.
    """
    root = Path(root).expanduser().resolve()
    sealed = root / w.SEALED
    if w.SEALED in root.parts:
        raise refuse("sealed_path", "the data root is inside a sealed folder")
    manifest = json.loads((root / w.MANIFEST).read_text())
    for relative, record in sorted(manifest["files"].items()):
        path = (root / relative).resolve()
        if path == sealed or sealed in path.parents or root not in path.parents:
            raise refuse("sealed_path", "the manifest lists a sealed path or a path outside the root")
        if record["rows"] and (not path.is_file() or w.sha256(path) != record["sha256"]):
            raise refuse("hash_mismatch", relative)
    return w.WrdsData({}, manifest, root)


def stage_data(stage: str, root: str | Path) -> w.WrdsData:
    """The freeze checks the file bytes only; every other stage loads the tables (``w.load``)."""
    return data_files(root) if stage == "freeze" else w.load(root)


def quote_files(root: str | Path, read: bool) -> w.WrdsData:
    """The quote copy of the second pull: its manifest after a SHA-256 and row-count check of each main file, and
    with ``read`` the quote table (``QUOTE_COLUMNS`` only).

    A path under ``sealed/`` or outside the root refuses (as ``data_files`` and D9), and so does a file of another
    table. ``check_quotes`` then compares the manifest with the tracked quote manifest.
    """
    root = Path(root).expanduser().resolve()
    sealed = root / w.SEALED
    if w.SEALED in root.parts:
        raise refuse("sealed_path", "the quote root is inside a sealed folder")
    manifest = json.loads((root / w.MANIFEST).read_text())
    parts = []
    for relative, record in sorted(manifest["files"].items()):
        path = (root / relative).resolve()
        if relative.split("/")[0] == w.SEALED or path == sealed or sealed in path.parents:
            raise refuse("sealed_path", "the quote manifest lists a sealed path")
        if root not in path.parents:
            raise refuse("path_outside_root", relative)
        if w.stem_of(relative) != QUOTE_STEM:
            raise refuse("quote_file_unexpected", relative)
        if record["rows"] == 0:          # an empty part writes no data file
            if path.exists():
                raise refuse("file_unexpected", relative)
            continue
        if not path.is_file():
            raise refuse("file_missing", relative)
        if w.sha256(path) != record["sha256"]:
            raise refuse("hash_mismatch", relative)
        if pq.ParquetFile(path).metadata.num_rows != record["rows"]:
            raise refuse("row_count_mismatch", relative)
        if read:
            parts.append(pq.read_table(path, columns=QUOTE_COLUMNS))
    return w.WrdsData({QUOTE_STEM: pa.concat_tables(parts)} if parts else {}, manifest, root)


def check_quotes(quotes: w.WrdsData, tracked: Mapping[str, Any], trial: Mapping[str, Any]) -> str:
    """Refuse unless the quote copy is the tracked quote manifest's files and vintage; return its files digest."""
    files = {name: {"rows": int(r["rows"]), "sha256": r["sha256"]} for name, r in quotes.manifest["files"].items()}
    known = {name: {"rows": int(r["rows"]), "sha256": r["sha256"]} for name, r in tracked["files"].items()}
    if files != known:
        raise refuse("quote_manifest_mismatch", "the quote copy differs from the tracked quote manifest")
    if not quotes.manifest["vintage"] == tracked["vintage"] == trial["data"]["vintage"]:
        raise refuse("quote_manifest_mismatch", "vintage")
    return sha256_bytes(json.dumps(files, sort_keys=True).encode())


def quote_table(quotes: w.WrdsData, data: w.WrdsData) -> pd.DataFrame:
    """The checked quote rows (``permno`` as text, ``date``, ``dlybid``, ``dlyask``, ``dlyprcflg``).

    Refuses a row without a PERMNO or a date, a row dated in the seal window, a repeated (PERMNO, date), and a row
    without a main daily row of the first pull on (``permno``, ``dlycaldt``), which would show a seal difference
    between the two pulls.
    """
    if QUOTE_STEM not in quotes.tables:
        raise refuse("file_missing", QUOTE_STEM)
    table = w.frame(quotes, QUOTE_STEM, QUOTE_COLUMNS)
    if table["permno"].isna().any() or table["dlycaldt"].isna().any():
        raise refuse("quote_key_missing", "a quote row has no PERMNO or no date")
    if ((table["dlycaldt"] >= sig.SEAL[0]) & (table["dlycaldt"] < sig.SEAL[1])).any():
        raise refuse("quote_row_in_seal", "a quote row is dated in the seal window")
    if table.duplicated(["permno", "dlycaldt"]).any():
        raise refuse("quote_key_repeated", "a (PERMNO, date) repeats in the quote rows")
    keys = {"permno": "int64"}
    main = w.frame(data, "crsp_dsf_v2", ["permno", "dlycaldt"]).astype(keys).drop_duplicates()
    joined = table[["permno", "dlycaldt"]].astype(keys).merge(main, how="left", indicator=True)
    if (joined["_merge"] != "both").any():
        raise refuse("quote_row_unmatched", "a quote row has no main daily row of the first pull")
    return table.assign(permno=table["permno"].astype(int).astype(str)).rename(columns={"dlycaldt": "date"})


def code_digest(repo: Path) -> str:
    """One SHA-256 over the path and bytes of every Python file under ``CODE_FOLDERS``, in path order."""
    digest = hashlib.sha256()
    for path in sorted(p for folder in CODE_FOLDERS for p in (repo / folder).rglob("*.py")):
        digest.update(str(path.relative_to(repo)).encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def context(trial: Mapping[str, Any], trial_sha: str, data_sha: str, repo: Path = REPO) -> dict[str, Any]:
    """What every stage must share: the trial file, the code (pinned files and every other module), and the data."""
    pins = {p: pin["file_sha256"] for p, pin in trial["code_pins"].items() if p != "statement" and pin["commit"]}
    return {"trial_sha256": trial_sha, "data_files_sha256": data_sha, "code_pins_sha256": pins,
            "code_sha256": code_digest(repo)}


def header(trial: Mapping[str, Any]) -> dict[str, str]:
    ceiling = trial["evidence_ceiling"]
    return {"evidence_ceiling": ceiling["value"], "run_label": ceiling["run_label"],
            "low_risk_label": ceiling["low_risk_label"], "labels": trial["reports_owed"]["labels"],
            "vwretd": trial["data"]["benchmarks"]["before_1993_02"]}


# Stage files ------------------------------------------------------------------------------

def clean(value: Any) -> Any:
    """Plain JSON values: NaN, infinity, and NaT become None; dates and months become text."""
    if isinstance(value, Mapping):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(value) else None
    if value is None or value is pd.NaT:
        return None
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        stamp = pd.Timestamp(value)
        return None if pd.isna(stamp) else str(stamp.date())
    if isinstance(value, pd.Period):
        return str(value)
    if isinstance(value, str):
        return value
    raise refuse("output_value_invalid", type(value).__name__)


def check_out(out: Path) -> Path:
    """R11: real outputs go only to a folder outside every Git checkout."""
    out = Path(out).expanduser().resolve()
    for folder in (out, *out.parents):
        if (folder / ".git").exists():
            raise refuse("output_inside_checkout", "the output folder is inside a Git checkout")
    out.mkdir(parents=True, exist_ok=True)
    return out


def read_stage(out: Path, stage: str, ctx: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    path, sums = out / f"{stage}.json", out / f"{stage}.sha256"
    if not path.is_file() or not sums.is_file():
        raise refuse("stage_missing", stage)
    raw = path.read_bytes()
    digest = sha256_bytes(raw)
    if sums.read_text().strip() != digest:
        raise refuse("stage_digest_mismatch", stage)
    payload = json.loads(raw)
    if payload.get("stage") != stage or payload.get("context") != clean(ctx):
        raise refuse("stage_context_mismatch", f"{stage} was made from another trial file, code, or data")
    return payload, digest


def earlier(out: Path, stage: str, ctx: Mapping[str, Any]) -> tuple[dict[str, dict], dict[str, str]]:
    """Read and check every stage before ``stage``; each must name the digests of the stages before it."""
    payloads, digests = {}, {}
    for name in STAGES[:STAGES.index(stage)]:
        payloads[name], digests[name] = read_stage(out, name, ctx)
        if payloads[name]["previous"] != {k: digests[k] for k in STAGES[:STAGES.index(name)]}:
            raise refuse("stage_chain_mismatch", f"{name} was not built on the current earlier stages")
    return payloads, digests


def check_calibration(calibration: Mapping[str, Any]) -> None:
    """``declaration_timing.order_after_freeze`` (amendment 2): the look, the screen, and the freeze run only after
    the decision ``chosen`` or ``ratio_coverage_low``. ``ratio_coverage_low`` is the coverage stop of test B only
    (``primary_family.test_B.after_coverage_stop``). Every other outcome keeps its meaning in
    ``books.low_risk.calibration.choice``, a stop or an owner decision, and refuses with its ``calibrate_lowrisk``
    name: ``refused`` (a refusal below the first g that meets "stops"; the calibration stage itself stops on it and
    writes no file), ``ratio_coverage_ambiguous`` ("the owner decides"), and ``no_g_reaches_target`` ("stop and ask
    the owner")."""
    if calibration["decision"] not in GO_ON:
        raise refuse("calibration_stop", f"calibration decision {calibration['decision']}")


def record_test_b(calibration: Mapping[str, Any], digest: str) -> dict[str, Any]:
    """Test B after the calibration, for each later stage file: after ``ratio_coverage_low`` it is stopped with the
    label ``TEST_B_STOPPED`` and p_B = 1.0 (the Holm family keeps size 2); after ``chosen`` it is still open.
    ``digest`` is the SHA-256 of the calibration stage file."""
    stopped = calibration["decision"] == "ratio_coverage_low"
    return {"stopped": stopped, "label": TEST_B_STOPPED if stopped else None, "p_b": 1.0 if stopped else None,
            "calibration_decision": calibration["decision"], "calibration_sha256": digest}


def write_stage(out: Path, stage: str, ctx: Mapping[str, Any], previous: Mapping[str, str],
                result: Mapping[str, Any]) -> str:
    path = out / f"{stage}.json"
    if path.exists() or (out / f"{stage}.sha256").exists():
        raise refuse("stage_output_exists", f"{stage}: a stage output is never overwritten (R9)")
    text = json.dumps(clean({"stage": stage, "context": ctx, "previous": previous, "result": result}),
                      sort_keys=True, indent=1, allow_nan=False) + "\n"
    path.write_text(text)
    digest = sha256_bytes(text.encode())
    (out / f"{stage}.sha256").write_text(digest + "\n")
    return digest


def masked(text: str) -> str:
    """A refusal or error text with each 5- or 6-digit integer (a possible PERMNO) replaced by ``<id>``."""
    return re.sub(r"(?<![\d.])\d{5,6}(?![\d.])", "<id>", str(text))


def log(out: Path, entry: Mapping[str, Any]) -> None:
    """Append one line to the run log (R9: every criteria output with its declaration, every refusal)."""
    with (out / "run_log.jsonl").open("a") as handle:
        handle.write(json.dumps(clean(entry), sort_keys=True, allow_nan=False) + "\n")


# Calendar and frames ----------------------------------------------------------------------

def month_ends(cal: pd.DatetimeIndex) -> pd.Series:
    """The last calendar row of each month, indexed by month."""
    return pd.Series(cal, index=cal).groupby(cal.to_period("M")).max()


def screen_end(data: w.WrdsData) -> pd.Timestamp:
    """The last screen row: the last calendar row of 1992-12."""
    return month_ends(w.calendar(data))[crit.SCREEN_END]


def window(cal: pd.DatetimeIndex, first: pd.Period) -> tuple[pd.Timestamp, pd.Timestamp]:
    """The engine anchor and end of a screen series whose first return month is ``first``.

    The row dated in month m - 1 forms month m, so the anchor is the last row of ``first - 2`` and the first
    rebalance is the last row of ``first - 1``; the end is the last row of 1992-12.
    """
    ends = month_ends(cal)
    return ends[first - 2], ends[crit.SCREEN_END]


def cut_frames(frames: Mapping[str, Any], last: pd.Timestamp) -> dict[str, Any]:
    """The loader frames with no value after ``last``, the last screen row.

    The engine accepts an end row only when a row in a later month follows it (``m55_index_tilt.check_inputs``), so
    the loader's row after ``last`` stays as a date with every value blank (``BLANK_ROW``). Events that settle after
    ``last`` and spells that start after it are dropped, and so is a column left without a spell (the backtest
    needs a spell for each column). An end date after ``last`` on an earlier spell stays: it reads as open on every
    row up to ``last``.
    """
    spells = frames["intervals"][frames["intervals"]["start_date"] <= last]
    columns = frames["prices"].columns[frames["prices"].columns.isin(spells["permanent_id"])]
    after = frames["prices"].index > last
    out = {**frames, "intervals": spells}
    for key, fill in BLANK_ROW.items():
        table = frames[key][columns].copy()
        table.loc[after] = fill
        out[key] = table
    events = frames["disappearances"]
    out["disappearances"] = events[(events["effective_date"] <= last) & events["permanent_id"].isin(columns)]
    return out


def check_engine_cut(inputs: tilt.TiltInputs, last: pd.Period = crit.SCREEN_END, period: str = "screen",
                     half_spread: pd.DataFrame | None = None) -> None:
    """Refuse when a value after month ``last`` (1992-12 for the screen, else the segment end) reaches the engine:
    a value on a row after it (one blank date row may follow the end row), an event that settles after it, or a
    spell that starts after it. The half-spread panel is checked too."""
    reason = END_REASONS[period]
    after = inputs.prices.index.to_period("M") > last
    tables = {"prices": inputs.prices, "market_equity": inputs.market_equity, "eligible": inputs.eligible,
              "me_reason": inputs.me_reason, **{f"signal {s}": v for s, v in inputs.signals.items()},
              **({} if half_spread is None else {"half_spread": half_spread})}
    for key, table in tables.items():
        fill = BLANK_ROW.get(key, np.nan)
        part = table[after]
        if after.sum() > 1 or not (part.isna() if pd.isna(fill) else part == fill).all().all():
            raise refuse(reason, f"{key}: a value on a row after {last} reaches the engine")
    for key, column in (("disappearances", "effective_date"), ("intervals", "start_date")):
        if (pd.to_datetime(getattr(inputs, key)[column]).dt.to_period("M") > last).any():
            raise refuse(reason, f"{key}: a row after {last} reaches the engine")


def frames_for(data: w.WrdsData, run: str) -> dict[str, Any]:
    """The loader frames of the screen window, cut at the last screen row right after the load (``cut_frames``).
    Their rows do not depend on the anchor, so every candidate uses them."""
    start, end = window(w.calendar(data), crit.SCREEN_START)
    return cut_frames(w.tilt_frames(data, start, end, run), end)


def inputs_for(frames: Mapping[str, Any], signals: Mapping[str, pd.DataFrame], start: pd.Timestamp,
               end: pd.Timestamp) -> tilt.TiltInputs:
    """``TiltInputs`` on the unmasked loader panels; one declared signal set, ``min_valid = half_rule(n)``."""
    ids = tuple(signals)
    return tilt.TiltInputs(prices=frames["prices"], signals=dict(signals), eligible=frames["eligible"],
                           market_equity=frames["market_equity"], me_reason=frames["me_reason"],
                           intervals=frames["intervals"], disappearances=frames["disappearances"], start=start,
                           end=end, signal_ids=ids, min_valid=tilt.half_rule(len(ids)))


def no_signal(frames: Mapping[str, Any]) -> dict[str, pd.DataFrame]:
    return {NO_SIGNAL: pd.DataFrame(np.nan, index=frames["prices"].index, columns=frames["prices"].columns)}


def frames_digest(frames: Mapping[str, Any], last: pd.Timestamp) -> str:
    """SHA-256 over the panels and tables of a frame set, cut at row ``last`` (the calibration panel is cut and
    hashed, Opus ADV-05). The loader adds the first row of the next month, which no screen output uses."""
    digest = hashlib.sha256()
    for key in ("prices", "path_break", "eligible", "market_equity", "me_reason", "intervals", "disappearances"):
        table = frames[key]
        if key == "disappearances":
            table = table[table["effective_date"] <= last]
        elif key != "intervals":
            table = table.loc[:last]
        table = table.astype(str) if key == "me_reason" else table
        digest.update(key.encode())
        digest.update(pd.util.hash_pandas_object(table, index=True).to_numpy().tobytes())
        digest.update("|".join(map(str, table.columns)).encode())
    digest.update("|".join(map(str, frames["calendar"][frames["calendar"] <= last])).encode())
    return digest.hexdigest()


# Signals ----------------------------------------------------------------------------------

def after(table: pd.DataFrame, columns: tuple[str, ...], last: pd.Timestamp) -> np.ndarray:
    """True for each row with a date in ``columns`` after ``last``; a missing date is not after it."""
    return np.logical_or.reduce([(table[c] > last).to_numpy() for c in columns])


def cut_inputs(inputs: sig.SignalInputs, last: pd.Timestamp) -> sig.SignalInputs:
    """The signal inputs without a row dated after ``last`` (``SIGNAL_DATES``). An end date after ``last`` on an
    earlier spell or link stays: it reads as open on every row up to ``last``."""
    return replace(inputs, **{name: getattr(inputs, name)[~after(getattr(inputs, name), columns, last)]
                              .reset_index(drop=True) for name, columns in SIGNAL_DATES.items()})


def check_inputs_cut(inputs: sig.SignalInputs, last: pd.Timestamp, period: str = "screen") -> None:
    """Refuse when a signal-input table holds a row dated after ``last`` (checked before each signal build)."""
    for name, columns in SIGNAL_DATES.items():
        if after(getattr(inputs, name), columns, last).any():
            raise refuse(END_REASONS[period], f"{name} holds a row after {last.date()}")


def screen_inputs(data: w.WrdsData) -> sig.SignalInputs:
    """The loader's signal inputs, cut at the last screen row right after the load."""
    return cut_inputs(w.signal_inputs(data), screen_end(data))


def segment_inputs(inputs: sig.SignalInputs, post: bool) -> sig.SignalInputs:
    """The daily and index rows of one seal segment (before 2019-07-31, or from 2020-07-31)."""
    def cut(table: pd.DataFrame) -> pd.DataFrame:
        keep = table["date"] >= sig.SEAL[1] if post else table["date"] < sig.SEAL[0]
        return table[keep].reset_index(drop=True)
    return replace(inputs, daily=cut(inputs.daily), index_daily=cut(inputs.index_daily))


def segment_signals(inputs: sig.SignalInputs, rebalances: pd.DatetimeIndex,
                    last: pd.Timestamp | None = None, period: str = "screen") -> dict[str, Any]:
    """``build_signals`` on one seal segment only, so no window crosses the seal (V4, loader Opus A-1).

    The rebalances lie in one segment. A post-seal rebalance before 2021-08-31 (the first after the anchor
    2021-07-30) refuses. With ``last``, inputs that hold a row after it refuse.
    """
    rows = pd.DatetimeIndex(rebalances)
    post = rows >= sig.SEAL[1]
    if post.any() and not post.all():
        raise refuse("rebalances_cross_seal", "build the signals once per seal segment")
    if post.any() and rows.min() < POST_SEAL_FIRST_REBALANCE:
        raise refuse("post_seal_rebalance_early", f"the post-seal segment starts at the anchor {POST_SEAL_ANCHOR.date()}")
    if last is not None:
        check_inputs_cut(inputs, last, period)
    return sig.build_signals(segment_inputs(inputs, bool(post.any())), rows)


def signal_panels(data: w.WrdsData, inputs: sig.SignalInputs) -> dict[str, Any]:
    """S1 to S8 at the month-end rows dated 1962-12 to 1992-12, from ``screen_inputs`` (pre-seal rows only)."""
    ends = month_ends(w.calendar(data))
    rows = pd.DatetimeIndex(ends[COVERAGE_FIRST - 1:crit.SCREEN_END].to_numpy())
    return segment_signals(inputs, rows, screen_end(data))


def check_decision_rows(panels: Mapping[str, Any], data: w.WrdsData, inputs: sig.SignalInputs,
                        post: bool = False) -> None:
    """The decision row of each signal rebalance is the engine's row r - 1 (one calendar for both)."""
    cal = w.calendar(data)
    daily = pd.DatetimeIndex(np.unique(segment_inputs(inputs, post).daily["date"]))
    for date in panels["members"].index:
        if daily[daily.get_loc(date) - 1] != cal[cal.get_loc(date) - 1]:
            raise refuse("calendar_mismatch", str(date.date()))


def signal_frame(panels: Mapping[str, Any], signal: str, frames: Mapping[str, Any],
                 dates: pd.DatetimeIndex) -> pd.DataFrame:
    """The engine frame of one signal: the value built for rebalance r, times its declared sign, on row r - 1.

    Every engine rebalance in ``dates`` must have a signal row; a missing row refuses (it would read as no value).
    """
    rows, columns = frames["prices"].index, frames["prices"].columns
    values = panels["values"][signal]
    values = values.set_axis(values.columns.astype(str), axis=1)
    if len(dates.difference(values.index)):
        raise refuse("signal_rebalance_missing", f"{signal}: an engine rebalance has no signal row")
    if values.loc[dates, values.columns.difference(columns)].notna().any().any():
        raise refuse("signal_column_missing", f"{signal}: a value at an engine rebalance has no engine column")
    out = pd.DataFrame(np.nan, index=rows, columns=columns)
    for date in dates:
        out.iloc[rows.get_loc(date) - 1] = sig.SIGNS[signal] * values.loc[date].reindex(columns).to_numpy(dtype=float)
    return out


def by_return_month(panel: pd.DataFrame) -> pd.DataFrame:
    """Index a rebalance-row panel by the return month each row forms (the row dated m - 1 forms m)."""
    months = panel.index.to_period("M") + 1
    keep = (months >= COVERAGE_FIRST) & (months <= crit.SCREEN_END)
    out = panel[keep]
    out.index = months[keep].to_timestamp()
    if len(out) != len(pd.period_range(COVERAGE_FIRST, crit.SCREEN_END, freq="M")):
        raise refuse("coverage_panel_invalid", "the real-start panel needs every month from 1963-01 to 1992-12")
    return out


def real_starts(panels: Mapping[str, Any]) -> dict[str, int | None]:
    members = by_return_month(panels["members"])
    return {s: sig.real_start(by_return_month(panels["reasons"][s]), members) for s in sig.SIGNAL_IDS}


def first_month(start_year: int | None) -> pd.Period | None:
    return None if start_year is None else max(pd.Period(f"{start_year}-01", "M"), crit.SCREEN_START)


# Exit classes, the path_break blank set, and declarations ----------------------------------

def exit_map(data: w.WrdsData) -> dict[str, str]:
    return {str(p): c for p, c in w.exit_class(data).items()}


def held_weight(weights: pd.DataFrame, row: pd.Timestamp, name: str, inclusive: bool = True) -> float:
    """The post-trade engine holding at the last rebalance at (or before) ``row``; 0 before the first rebalance."""
    prior = weights.index[weights.index <= row] if inclusive else weights.index[weights.index < row]
    return float(weights.at[prior[-1], name]) if len(prior) else 0.0


def path_break_positions(frames: Mapping[str, Any], books: Mapping[str, pd.DataFrame], exits: Mapping[str, str],
                         months: pd.PeriodIndex, last: pd.Timestamp) -> list[dict[str, Any]]:
    """Each position held across a loader ``path_break`` row (P1_path_break, V6), from frames and holdings only.

    The previous valid row W is the last row before the break row X with a close in the path. A book holds the
    position when its post-trade holding at the last rebalance at or before W is not zero and the name has not
    settled by W (a held weight drifts between rebalances but stays above zero). The position blanks the holding
    months of the rows after W up to X, inside ``months``. Every book holds only names that CW-PIT holds; a book
    that does not refuses. The engine return at X must be missing, so a close on the row before X refuses when the
    name is eligible on a row whose 252-row return window holds X.

    Only rows up to ``last`` are read. A held position with no close on ``last`` that has not settled refuses: its
    return after W falls after ``last``, and the frozen file has no rule for that case.
    """
    prices, breaks = frames["prices"], frames["path_break"]
    rows, values = prices.index, prices.to_numpy(dtype=float)
    stop = rows.get_loc(last)
    settled = dict(zip(frames["disappearances"]["permanent_id"], frames["disappearances"]["effective_date"]))
    eligible = frames["eligible"].to_numpy()
    out = []
    for i, j in zip(*np.nonzero(breaks.to_numpy()[:stop + 1])):
        name = prices.columns[j]
        valid = np.flatnonzero(np.isfinite(values[:i, j]))
        if not len(valid):
            continue
        k = int(valid[-1])
        if k == i - 1 and eligible[i:min(i + tilt.COV_ROWS, stop + 1), j].any():
            raise refuse("path_break_adjacent", f"{rows[i].date()}: the row before the break has a close")
        gone = name in settled and settled[name] <= rows[k]
        held = {book: 0.0 if gone else held_weight(table, rows[k], name) for book, table in books.items()}
        if not held["cw"]:
            if any(held.values()):
                raise refuse("book_holds_outside_cw", str(rows[i].date()))
            continue
        touched = pd.PeriodIndex(sorted(set(rows[k + 1:i + 1].to_period("M"))), freq="M")
        out.append({"break_row": rows[i], "previous_valid_row": rows[k],
                    "months": [m for m in touched if m in months], "exit_class": exits[name],
                    "weight_at_last_rebalance": held})
    for j in np.flatnonzero(~np.isfinite(values[stop])):
        name = prices.columns[j]
        valid = np.flatnonzero(np.isfinite(values[:stop, j]))
        if not len(valid) or (name in settled and settled[name] <= last):
            continue
        k = int(valid[-1])
        if any(held_weight(table, rows[k], name) for table in books.values()):
            raise refuse("path_gap_at_period_end", f"{rows[k].date()}: a held position has no close from the next "
                                                   f"row to {last.date()}")
    return out


def blank_set(positions: list[dict[str, Any]]) -> list[pd.Period]:
    return sorted({pd.Period(m, "M") for p in positions for m in p["months"]})


def blanked_windows(frames: Mapping[str, Any], dates: pd.DatetimeIndex, exits: Mapping[str, str],
                    last: pd.Timestamp) -> dict[str, Any]:
    """Each blanked level window (R6, P1_path_break): a member at an engine rebalance whose 252-row return window,
    ending at the decision row r - 1, holds a row after the previous valid row W and on or before the break row X,
    while the member is eligible at r - 1. The engine return on these rows is missing (``path_break_positions``
    checks the row before X), so the window is short of 252 returns and the member stays at w = b. A window counts
    once, however many breaks it holds. Breaks after ``last`` are not read.
    """
    rows, columns = frames["prices"].index, frames["prices"].columns
    values, eligible = frames["prices"].to_numpy(dtype=float), frames["eligible"].to_numpy()
    breaks = frames["path_break"].to_numpy()[:rows.get_loc(last) + 1]
    decision = np.array([rows.get_loc(date) - 1 for date in dates], dtype=int)
    cells = defaultdict(list)
    for i, j in zip(*np.nonzero(breaks)):
        valid = np.flatnonzero(np.isfinite(values[:i, j]))
        first = int(valid[-1]) + 1 if len(valid) else 0
        hit = decision[(decision >= first) & (decision < i + tilt.COV_ROWS)]
        for k in hit[eligible[hit, j]]:
            cells[(int(k), int(j))].append(rows[i])
    each = [{"rebalance": rows[k + 1], "exit_class": exits[columns[j]], "break_rows": found}
            for (k, j), found in sorted(cells.items())]
    by_class = Counter(e["exit_class"] for e in each)
    return {"windows": len(each), "by_exit_class": per_class(by_class), "each": each}


def declaration(run_set: list, first: pd.Period, last: pd.Period = crit.SCREEN_END) -> dict[pd.Period, str]:
    """One comparison's declaration: the months of the run set inside the comparison's span."""
    return {pd.Period(m, "M"): BLANK for m in run_set if first <= pd.Period(m, "M") <= last}


def check_declaration(declared: Mapping[pd.Period, str], run_set: list, first: pd.Period,
                      last: pd.Period = crit.SCREEN_END) -> None:
    """Refuse unless a declaration equals the run set cut to the span, every month with the reason ``BLANK``."""
    expected = {pd.Period(m, "M") for m in run_set if first <= pd.Period(m, "M") <= last}
    if set(declared) != expected or any(reason != BLANK for reason in declared.values()):
        raise refuse("declaration_invalid", "a declaration must equal the run set cut to the span")


def without(series: pd.Series, declared: Mapping[pd.Period, str]) -> pd.Series:
    """A declared blank month has no row in any series of the comparison (``m55_criteria.check_series``)."""
    return series[~series.index.isin(pd.PeriodIndex(list(declared), freq="M"))]


# Book reports -----------------------------------------------------------------------------

def monthly_vwretd(data: w.WrdsData, first: pd.Period) -> pd.Series:
    """Legacy S&P 500 ``vwretd`` compounded by calendar month, ``first`` to 1992-12; a missing day leaves its month
    missing (never filled). Only rows up to the last screen row are read."""
    last = screen_end(data)
    cal = w.calendar(data)
    legacy = w.frame(data, "crsp_dsp500_legacy", ["caldt", "vwretd"])
    legacy = legacy[legacy["caldt"] <= last].set_index("caldt")["vwretd"]
    if not legacy.index.isin(cal).all() or legacy.index.duplicated().any():
        raise refuse("calendar_invalid", "a legacy S&P 500 date is not a calendar row")
    daily = legacy.reindex(cal[(cal.to_period("M") >= first) & (cal <= last)]).astype(float)
    months = daily.index.to_period("M")
    monthly = (1.0 + daily).groupby(months).prod() - 1.0
    monthly[daily.isna().groupby(months).any()] = np.nan
    return monthly.rename("vwretd")


def check_months(*series: pd.Series, last: pd.Period = crit.SCREEN_END, period: str = "screen") -> None:
    """Refuse when a monthly series passed to the criteria holds a month after ``last`` (1992-12 for the screen),
    or, in the check period, a ``CHECK_GAP_MONTHS`` month."""
    if any(len(s) and s.index.max() > last for s in series):
        raise refuse(END_REASONS[period], f"a monthly series holds a month after {last}")
    if period == "check" and any(s.index.isin(crit.CHECK_GAP_MONTHS).any() for s in series):
        raise refuse("check_gap_month", "a check series holds a CHECK_GAP_MONTHS month")


def mean_gap(book: pd.Series, benchmark: pd.Series, declared: Mapping[pd.Period, str], period: str = "screen",
             last: pd.Period = crit.SCREEN_END) -> dict[str, Any]:
    """Annual mean gap, TE, and correlation of book - benchmark over the months of ``period`` with values."""
    check_months(book, benchmark, last=last, period=period)
    span = book.index
    clean_ = crit.check_paired({"book": without(book, declared),
                                "benchmark": without(benchmark.reindex(span), declared)}, period, declared)
    gap = clean_["book"] - clean_["benchmark"]
    return {"months": len(gap), "annual_mean_gap": crit.annual_mean(gap),
            "annual_te": float(gap.std(ddof=1)) * math.sqrt(crit.MONTHS_PER_YEAR),
            "correlation": float(np.corrcoef(clean_["book"], clean_["benchmark"])[0, 1]),
            "book_annual_mean": crit.annual_mean(clean_["book"]),
            "benchmark_annual_mean": crit.annual_mean(clean_["benchmark"]), **crit.blank_record(declared)}


def r4_counts(summary: Mapping[str, Any], events: pd.DataFrame, end: pd.Timestamp, run: str) -> dict[str, Any]:
    """Held disappearances by cause (R4), rebuilt from the engine holdings and checked against the engine count.

    The engine gives the total weight at the event (``incoming_weight``); the split by cause uses the holding at the
    last rebalance before the event. In the primary run, a loader ``delisting_return`` of 0 means that CIZ put the
    delisting return in the path, another value is a supplied return (-100 percent or less), and NaN takes the
    engine default. In the last_close run, every event settles at the last trade close.
    """
    weights = summary["weights"]
    first = weights.index[0]
    held = []
    for record in events.to_dict("records"):
        effective = pd.Timestamp(record["effective_date"])
        if first < effective <= end:
            weight = held_weight(weights, effective, record["permanent_id"], inclusive=False)
            if weight:
                held.append({**record, "weight": weight})
    if len(held) != summary["held_events"]["count"]:
        raise refuse("r4_held_count_mismatch", f"{len(held)} rebuilt, {summary['held_events']['count']} in the engine")
    out = {"held": len(held), "incoming_weight_sum": summary["held_events"]["weight_sum"],
           "incoming_weight_max": summary["held_events"]["weight_max"], "by_cause": {}}
    for cause in tilt.CAUSES:
        part = [h for h in held if h["cause"] == cause]
        returns = np.array([h["delisting_return"] for h in part], dtype=float)
        counts = ({"settled_at_last_close": len(part)} if run == "last_close" else
                  {"ciz_return_in_path": int((returns == 0.0).sum()),
                   "supplied_terminal_return": int((np.isfinite(returns) & (returns != 0.0)).sum()),
                   "missing_engine_default": int(np.isnan(returns).sum())})
        out["by_cause"][cause] = {"held": len(part), "weight_at_last_rebalance_sum": math.fsum(h["weight"] for h in part),
                                  **counts}
    return out


def fragility(primary: Mapping[str, float], rerun: Mapping[str, float]) -> dict[str, Any]:
    """R4: a sign flip of an active annual mean between the primary run and the loader last_close rerun."""
    return {key: {"primary": primary[key], "last_close": rerun[key],
                  "fragile": tilt.sign(primary[key]) != tilt.sign(rerun[key])} for key in primary}


def label_months(daily: pd.Series) -> pd.PeriodIndex:
    """The holding month of each measured daily row (``m55_index_tilt.monthly_returns``: the first row joins the next)."""
    labels = daily.index.to_period("M").to_numpy().copy()
    labels[0] = labels[0] + 1
    return pd.PeriodIndex(labels, freq="M")


def rebalance_counts(table: pd.DataFrame) -> dict[str, Any]:
    """Counts and B2 records from the engine rebalance table (reports_owed.counts and b2)."""
    traded = table["members"] - table["unknown_event_excluded"]
    b2 = table[table["unknown_event_excluded"] > 0]
    return {"rebalances": len(table), "members_mean": float(table["members"].mean()),
            "members_min": int(table["members"].min()), "traded_mean": float(traded.mean()),
            "traded_min": int(traded.min()), "pinned_mean": float(table["c_zero"].mean()),
            **{key: int(table[key].sum()) for key in table.columns
               if key.startswith("c_zero") or key.startswith("me_missing") or key == "settled_excluded"},
            "share_cap_at_final_weights": float((table["max_abs_active"] >= tilt.STOCK_CAP - tilt.CAP_TOLERANCE).mean()),
            "share_te_scaled": float((table["te_scale"] < 1.0).mean()),
            "b2": {"rebalances": len(b2), "excluded": int(b2["unknown_event_excluded"].sum()),
                   "max_cw_share": float(b2["unknown_event_cw_share"].max()) if len(b2) else 0.0,
                   "each": [{"date": d, "excluded": int(r["unknown_event_excluded"]),
                             "cw_share": float(r["unknown_event_cw_share"])} for d, r in b2.iterrows()]}}


def by_year(daily: pd.Series) -> dict[str, float]:
    return {str(y): float(v) for y, v in daily.groupby(daily.index.year).sum().items()}


def post_publication(active: pd.Series, publication_year: int) -> dict[str, Any]:
    """reports_owed.post_publication_split: the active months after and before the publication year (OI-08)."""
    after = active.index.year > publication_year
    return {"publication_year": publication_year,
            "months_after": int(after.sum()), "months_before": int((~after).sum()),
            "annual_mean_after": crit.annual_mean(active[after]) if after.any() else None,
            "annual_mean_before": crit.annual_mean(active[~after]) if (~after).any() else None}


def tilt_stats(found: Mapping[str, Any], declared: Mapping[pd.Period, str], frames: Mapping[str, Any],
               targets: Mapping[str, pd.DataFrame], publication_year: int | None, period: str = "screen",
               last: pd.Period = crit.SCREEN_END) -> dict[str, Any]:
    """reports_owed.tilt_stats and post_publication_split for one run and cost case (months with values only).

    The trial file names a size exposure but does not define it. The driver reports the mean over rebalances of
    sum((w - b) x ln ME) at the decision row r - 1 (an open question in the card report). With no publication
    year, ``post_publication`` is None.
    """
    cw, book = found["cw"], found["tilt"]
    check_months(book["monthly_net"], cw["monthly_net"], last=last, period=period)
    daily = book["daily_net"] - cw["daily_net"]
    keep = ~label_months(daily).isin(pd.PeriodIndex(list(declared), freq="M"))
    relative = without((1.0 + book["monthly_net"]) / (1.0 + cw["monthly_net"]) - 1.0, declared)
    active = without(book["monthly_net"] - cw["monthly_net"], declared)
    me = frames["market_equity"]
    exposure = []
    for date in targets["tilt"].index:
        t = me.index[me.index.get_loc(date) - 1]
        w_, b = targets["tilt"].loc[date], targets["cw"].loc[date]
        names = b.index[b.notna().to_numpy()]
        exposure.append(math.fsum(((w_[names] - b[names]) * np.log(me.loc[t, names].astype(float))).tolist()))
    turnover = {"tilt": by_year(book["turnover"]), "cw": by_year(cw["turnover"])}
    cost = {"tilt": by_year(book["cost"]), "cw": by_year(cw["cost"])}
    return {"realized_te_daily": float(daily[keep].std(ddof=1) * math.sqrt(tilt.ANNUAL_ROWS)),
            "worst_relative_drawdown": min((e["depth"] for e in crit.drawdown_episodes(relative)), default=0.0),
            "size_exposure_mean": float(np.mean(exposure)),
            "annual_turnover": {"tilt": book["annual_turnover"], "cw": cw["annual_turnover"],
                                "active": book["annual_turnover"] - cw["annual_turnover"]},
            "annual_cost_drag": {"tilt": book["annual_cost_drag"], "cw": cw["annual_cost_drag"],
                                 "active": book["annual_cost_drag"] - cw["annual_cost_drag"]},
            "turnover_by_year": {**turnover, "active": {y: v - turnover["cw"][y] for y, v in turnover["tilt"].items()}},
            "cost_drag_by_year": {**cost, "active": {y: v - cost["cw"][y] for y, v in cost["tilt"].items()}},
            "post_publication": None if publication_year is None else post_publication(active, publication_year)}


# Member census (R6 by later exit class) ---------------------------------------------------

def shares(counts: Mapping[str, int], totals: Mapping[str, int]) -> dict[str, float | None]:
    return {c: (counts.get(c, 0) / totals[c] if totals.get(c) else None) for c in EXIT_CLASSES}


def per_class(counter: Counter) -> dict[str, int]:
    return {c: int(counter.get(c, 0)) for c in EXIT_CLASSES}


def census(inputs: tilt.TiltInputs, dates: pd.DatetimeIndex, last: pd.Period = crit.SCREEN_END,
           period: str = "screen") -> dict[pd.Timestamp, dict[str, Any]]:
    """Each rebalance's target members from the engine's own ``rebalance_members`` (row r - 1 only)."""
    check_engine_cut(inputs, last, period)
    disappearances, returns, first_return = tilt.prepare(inputs)
    return {date: tilt.rebalance_members(inputs, date, returns, disappearances, first_return) for date in dates}


def pool_missing(inputs: tilt.TiltInputs, date: pd.Timestamp, setup: Mapping[str, Any]) -> pd.Series:
    """The ME reason of each pool member without ME at r - 1, as ``rebalance_members`` counts them."""
    calendar = inputs.prices.index
    t = calendar.get_loc(date) - 1
    events = inputs.disappearances
    settled = set(events.loc[(pd.to_datetime(events["effective_date"]) <= date)
                             & (pd.to_datetime(events["known_at"]) <= calendar[t]), "permanent_id"])
    pool = inputs.eligible.iloc[t] & ~inputs.prices.columns.isin(sorted(settled))
    reasons = inputs.me_reason.iloc[t][pool & inputs.market_equity.iloc[t].isna()]
    if len(reasons) != setup["record"]["me_missing"]:
        raise refuse("census_mismatch", f"me_missing at {date.date()}")
    return reasons


def r6_members(inputs: tilt.TiltInputs, setups: Mapping[pd.Timestamp, Mapping[str, Any]],
               exits: Mapping[str, str], unseen: set, blanked: Mapping[str, int]) -> dict[str, Any]:
    """ME missing by reason, unpriced, basis_unseen, and blanked-window pool cells by later exit class over the
    rebalances (``blanked``: ``blanked_windows`` by exit class on the same rebalances)."""
    me = {r: Counter() for r in tilt.ME_REASONS}
    unpriced, basis_unseen, pool = Counter(), Counter(), Counter()
    calendar = inputs.prices.index
    for date, setup in setups.items():
        t = calendar[calendar.get_loc(date) - 1]
        reasons = pool_missing(inputs, date, setup)
        for name, reason in reasons.items():
            me[reason][exits[name]] += 1
            unpriced[exits[name]] += int(pd.isna(inputs.prices.at[t, name]))
            basis_unseen[exits[name]] += int((int(name), t) in unseen)
        pool.update(exits[n] for n in [*setup["names"], *reasons.index])
    totals = per_class(pool)
    return {"pool_cells": totals,
            "me_missing": {r: {"cells": per_class(c), "share": shares(c, totals)} for r, c in me.items()},
            "unpriced": {"cells": per_class(unpriced), "share": shares(unpriced, totals)},
            "basis_unseen": {"cells": per_class(basis_unseen), "share": shares(basis_unseen, totals)},
            "blanked_windows": {"cells": dict(blanked), "share": shares(blanked, totals)}}


def c_zero_by_exit(inputs: tilt.TiltInputs, setups: Mapping[pd.Timestamp, Mapping[str, Any]], table: pd.DataFrame,
                   exits: Mapping[str, str]) -> dict[str, Any]:
    """c = 0 by reason and later exit class for a single-signal run, checked against the engine counts."""
    calendar = inputs.prices.index
    (signal,) = inputs.signal_ids
    out = {key: Counter() for key in ("few_signals", "short_history", "window_gap")}
    members = Counter()
    for date, setup in setups.items():
        names, full, short = setup["names"], setup["full"], setup["short"]
        values = inputs.signals[signal].iloc[calendar.get_loc(date) - 1][names]
        parts = {"few_signals": names[values.isna().to_numpy()],
                 "short_history": names[(~full & short).to_numpy()],
                 "window_gap": names[(~full & ~short).to_numpy()]}
        row = table.loc[date]
        if (len(parts["few_signals"]), len(parts["short_history"]), len(parts["window_gap"])) != (
                row["c_zero_few_signals"], row["c_zero_short_history"], row["c_zero_window_gap"]):
            raise refuse("census_mismatch", f"c_zero at {date.date()}")
        for key, found in parts.items():
            out[key].update(exits[n] for n in found)
        members.update(exits[n] for n in names)
    totals = per_class(members)
    return {"member_cells": totals,
            **{key: {"cells": per_class(v), "share": shares(v, totals)} for key, v in out.items()}}


def ratio_members(setup: Mapping[str, Any]) -> tuple[pd.Index, pd.Index]:
    """Gap and limiting members of the low-risk ratio, by the rule of ``whole_book_ratio`` (IDs for the R6 split)."""
    traded = setup["traded"]
    missing = setup["window"][traded].isna().to_numpy()
    seen = np.logical_or.accumulate(~missing, axis=0) | ~setup["short"][traded].to_numpy(dtype=bool)
    gap = (missing & seen).any(axis=0)
    return traded[gap], traded[~gap & missing.any(axis=0)]


def unseen_cells(data: w.WrdsData) -> set:
    """(PERMNO, date) daily rows whose share basis was not observed (loader ``basis_unseen``)."""
    me = w.member_market_equity(data)
    rows = w.daily(data).loc[me.index, ["permno", "date"]][me["basis_unseen"].notna().to_numpy()]
    return set(zip(rows["permno"].astype(int), rows["date"]))


# Coverage reports -------------------------------------------------------------------------

def cell_table(members: pd.DataFrame, reasons: pd.DataFrame, member_exit: np.ndarray) -> pd.DataFrame:
    """One row per member cell of a return-month panel: year, later exit class, and reason (``valid`` for a value)."""
    rows, cols = np.nonzero(members.to_numpy(dtype=bool))
    label = reasons.to_numpy(dtype=object)[rows, cols]
    return pd.DataFrame({"year": members.index.year[rows], "exit": member_exit[cols],
                         "reason": np.where(pd.isna(label), "valid", label)})


def counts_of(table: pd.DataFrame, key: str) -> dict[str, dict[str, int]]:
    return {str(k): {str(r): int(n) for r, n in g["reason"].value_counts().sort_index().items()}
            for k, g in table.groupby(key)}


def signal_coverage(members: pd.DataFrame, reasons: pd.DataFrame, member_exit: np.ndarray,
                    start: int | None) -> dict[str, Any]:
    valid = (members & reasons.isna()).sum(axis=1)
    total = members.sum(axis=1)
    first = first_month(start)
    cells = cell_table(members, reasons, member_exit)
    by_exit = counts_of(cells, "exit")
    exit_totals = {c: sum(by_exit.get(c, {}).values()) for c in EXIT_CLASSES}
    reasons_all = sorted(set(cells["reason"]))
    years = sorted(set(valid.index.year))
    return {"real_start": start, "first_month": first,
            "screen_months_before_blanks": 0 if first is None else len(pd.period_range(first, crit.SCREEN_END,
                                                                                       freq="M")),
            "valid_share_by_year": {str(y): float(valid[valid.index.year == y].sum() / total[total.index.year == y]
                                                  .sum()) for y in years},
            "min_month_valid_share_by_year": {str(y): float((valid / total.where(total > 0))[valid.index.year == y]
                                                            .min()) for y in years},
            "reason_counts_by_year": counts_of(cells, "year"),
            "cells_by_exit_class": {c: by_exit.get(c, {}) for c in EXIT_CLASSES},
            "reason_share_by_exit_class": {r: shares({c: by_exit.get(c, {}).get(r, 0) for c in EXIT_CLASSES},
                                                     exit_totals) for r in reasons_all}}


def member_me(data: w.WrdsData, dates: pd.DatetimeIndex, columns: pd.Index) -> pd.DataFrame:
    """D5 ME of the member PERMNOs at ``dates`` (rows) and ``columns`` (PERMNOs), missing as NaN."""
    me = w.member_market_equity(data)
    rows = w.daily(data).loc[me.index, ["permno", "date"]].assign(me=me["market_equity"].to_numpy())
    rows = rows[rows["date"].isin(dates)]
    return rows.pivot(index="date", columns="permno", values="me").reindex(index=dates, columns=columns)


def s2_size(members: pd.DataFrame, reasons: pd.DataFrame, me: pd.DataFrame) -> dict[str, Any]:
    """reports_owed.s2_short_history: by year, the share of S2 member cells typed short_history and the mean ME
    percentile (among members with ME at the decision row) of S2 short_history and S2 valid members."""
    rank = me.where(members.to_numpy()).rank(axis=1, pct=True)
    short = members & (reasons == "short_history")
    valid = members & reasons.isna()
    out = {}
    for year in sorted(set(members.index.year)):
        part = members.index.year == year
        out[str(year)] = {
            "short_history_share": float(short[part].to_numpy().sum() / members[part].to_numpy().sum()),
            "mean_me_percentile_short_history": float(np.nanmean(rank[part].where(short[part]).to_numpy()))
            if rank[part].where(short[part]).notna().any().any() else None,
            "mean_me_percentile_valid": float(np.nanmean(rank[part].where(valid[part]).to_numpy()))
            if rank[part].where(valid[part]).notna().any().any() else None}
    return out


def s2_basis_quarters(inputs: sig.SignalInputs, last: pd.Timestamp) -> dict[str, dict[str, int]]:
    """reports_owed.s2_history_rule: member quarters whose ``cfacshr`` at rdq differs from the one at the known date.

    One count per quarter (its EPS row), by the year of its known date (the share basis), up to ``last``: the gvkey
    links one to one to a PERMNO that is a member at that date. ``changed`` and ``same`` use the two as-of factor
    reads of ``m55_signals`` (at most one month old); ``unread`` counts quarters where either read fails.
    """
    check_inputs_cut(inputs, last)
    data = sig._Signals(inputs)
    links, members, out = {}, {}, defaultdict(Counter)
    for gvkey, rec in data.quarterly.items():
        for i in range(len(rec["quarter"])):
            basis, rdq = rec["basis"][i], rec["rdq"][i]
            if np.isnat(basis) or np.isnat(rdq) or basis > np.datetime64(last):
                continue
            if basis not in links:
                links[basis] = {g: p for p, g in data.links_at(basis).items() if g != "ambiguous_link"}
                members[basis] = set(data.members_at(basis))
            permno = links[basis].get(gvkey)
            if permno is None or permno not in members[basis]:
                continue
            f = data.factor(permno, "cfacshr", basis, rec["basis_floor"][i])
            at_rdq = data.factor(permno, "cfacshr", rdq, rec["rdq_floor"][i])
            key = ("unread" if isinstance(f, str) or isinstance(at_rdq, str)
                   else "same" if np.isclose(at_rdq, f, rtol=1e-9, atol=0.0) else "changed")
            out[str(pd.Timestamp(basis).year)][key] += 1
    return {y: {k: int(c.get(k, 0)) for k in ("changed", "same", "unread")} for y, c in sorted(out.items())}


# Stages -----------------------------------------------------------------------------------

def coverage_stage(data: w.WrdsData, trial: Mapping[str, Any]) -> dict[str, Any]:
    """Validity counts and real starts (no return), ME coverage, the missingness census, and S7 early coverage."""
    cal = w.calendar(data)
    ends = month_ends(cal)
    last = screen_end(data)
    exits = exit_map(data)
    inputs = screen_inputs(data)
    panels = signal_panels(data, inputs)
    check_decision_rows(panels, data, inputs)
    starts = real_starts(panels)
    members = by_return_month(panels["members"])
    member_exit = np.array([exits[str(p)] for p in members.columns])
    reasons = {s: by_return_month(panels["reasons"][s]) for s in sig.SIGNAL_IDS}
    signals = {s: signal_coverage(members, reasons[s], member_exit, starts[s]) for s in sig.SIGNAL_IDS}
    decision = pd.DatetimeIndex([cal[cal.get_loc(r) - 1] for r in panels["members"].index[
        (panels["members"].index.to_period("M") + 1 >= COVERAGE_FIRST)
        & (panels["members"].index.to_period("M") + 1 <= crit.SCREEN_END)]])
    me = member_me(data, decision, members.columns).set_axis(members.index, axis=0)
    signals["S2"]["short_history_size"] = s2_size(members, reasons["S2"], me)
    signals["S2"]["basis_quarters_by_year"] = s2_basis_quarters(segment_inputs(inputs, False), last)
    # S7 by return month in 1963 and 1964, and the basis_unseen cells at its two anchor rows.
    unseen = unseen_cells(data)
    s7 = {}
    for month in S7_MONTHS:
        row = members.index[members.index.to_period("M") == month][0]
        names = members.columns[members.loc[row].to_numpy()]
        cells = reasons["S7"].loc[row, names]
        t = decision[members.index.get_loc(row)]
        a = ends[t.to_period("M") - 1]
        a12 = ends.get(a.to_period("M") - 12)
        s7[str(month)] = {"members": int(len(names)), "valid": int(cells.isna().sum()),
                          "valid_share": float(cells.isna().mean()) if len(names) else None,
                          "reasons": {str(k): int(v) for k, v in Counter(cells.dropna()).items()},
                          "basis_unseen_at_anchor": int(sum((int(n), a) in unseen for n in names)),
                          "basis_unseen_at_anchor_12": None if a12 is None else int(
                              sum((int(n), a12) in unseen for n in names))}
    days = w.member_days(data)
    days = days[days["date"] <= last]
    days["year"] = days["date"].dt.year
    days["exit"] = days["permno"].astype(str).map(exits)
    screen_days = days[days["year"] >= COVERAGE_FIRST.year]
    census_ = {}
    for key, group in (("by_year", "year"), ("by_exit_class", "exit")):
        census_[key] = {str(k): {"member_days": int(len(g)), "with_daily_row": int(g["has_row"].sum()),
                                 "with_price": int(g["prc"].notna().sum()),
                                 "with_return": int(g["dlyret"].notna().sum()),
                                 "with_path_value": int(g["level"].notna().sum())}
                        for k, g in screen_days.groupby(group)}
    basis = {}
    for case in ("data_start", "seal"):
        hit = days[days["basis_unseen"] == case]
        basis[case] = {"by_year": {str(y): int(n) for y, n in hit["year"].value_counts().sort_index().items()},
                       "last": hit["date"].max() if len(hit) else None}
    anchor = next(d for d in ends if cal.get_loc(d) >= tilt.COV_ROWS + 1)    # r - 1 holds 252 returns
    return {"header": header(trial), "signals": signals, "s7_early": s7,
            "me_coverage": {"by_year": w._shares(screen_days, "year"), "by_exit_class": w._shares(screen_days, "exit"),
                            "basis_unseen_member_days_to_1992": basis},
            "missingness_census": census_,
            "bid_ask_share": float((screen_days["dlyprcflg"] == w.BID_ASK_FLAG).mean()),
            "data_span": {"first_calendar_row": cal[0], "first_full_window_rebalance": anchor},
            "coverage_rows": {"first": members.index[0], "last": members.index[-1], "count": len(members)}}


def calibration_stage(data: w.WrdsData, trial: Mapping[str, Any]) -> dict[str, Any]:
    """The low-risk calibration, once, on the primary panel over the rebalances that form 1963-07 to 1992-12."""
    frames = frames_for(data, "primary")
    cal = w.calendar(data)
    start, last = window(cal, crit.SCREEN_START)
    end = month_ends(cal)[crit.SCREEN_END - 1]          # the last rebalance that forms a screen month (1992-12)
    inputs = inputs_for(frames, no_signal(frames), start, last)
    check_engine_cut(inputs)
    result = tilt.calibrate_lowrisk(inputs, tilt.LOWRISK_GRID, tilt.LOWRISK_TARGET_RATIO, start, end)
    per_date = result["rebalances"][result["rebalances"]["g_status"] == "ok"].drop_duplicates("date").set_index("date")
    exits = exit_map(data)
    setups = census(replace(inputs, start=start, end=end), tilt.rebalance_dates(frames["prices"].index, start, end))
    split = {key: Counter() for key in ("gap_members", "limiting_partial", "limiting_short")}
    for date, setup in setups.items():
        gap, limiting = ratio_members(setup)
        if date not in per_date.index:
            raise refuse("census_mismatch", f"no calibration row at {date.date()}")
        row = per_date.loc[date]
        if (len(gap), len(limiting)) != (row["ratio_gap_members"], row["ratio_limiting_members"]):
            raise refuse("census_mismatch", f"ratio members at {date.date()}")
        split["gap_members"].update(exits[n] for n in gap)
        if row["ratio_status"] in ("defined_partial", "ratio_window_short"):
            key = "limiting_partial" if row["ratio_status"] == "defined_partial" else "limiting_short"
            split[key].update(exits[n] for n in limiting)
    gap_rows = per_date[per_date["ratio_gap_members"] > 0]
    cut = frames["prices"].loc[:last]
    return {"header": header(trial), "panel_sha256": frames_digest(frames, last),
            "panel_rows": {"first": cut.index[0], "last": cut.index[-1], "rows": len(cut), "columns": cut.shape[1]},
            "start": start, "end": end, "rebalances": int(len(setups)),
            "decision": result["decision"], "chosen_g": result["chosen_g"],
            "undefined_share": result["undefined_share"], "window_decision": result["window_decision"],
            "window_chosen_g": result["window_chosen_g"], "window_sensitive": result["window_sensitive"],
            "window_diag_undefined_share": result["window_diag_undefined_share"],
            "window_diag_coverage_high": result["window_diag_coverage_high"],
            "grid": result["grid"].to_dict("records"),
            "ratio_status_counts": {k: int(v) for k, v in per_date["ratio_status"].value_counts().items()},
            "gap_rebalances": int(len(gap_rows)), "ratio_gap_members": int(per_date["ratio_gap_members"].sum()),
            "max_ratio_gap_cw_share": float(per_date["ratio_gap_cw_share"].max()) if len(per_date) else None,
            "r6_by_exit_class": {key: per_class(v) for key, v in split.items()}}


def engine_pair(frames: Mapping[str, Mapping[str, Any]], signals: Mapping[str, Mapping[str, pd.DataFrame]],
                start: pd.Timestamp, end: pd.Timestamp, period: str = "screen",
                half_spread: pd.DataFrame | None = None, min_valid: int | None = None) -> dict[str, dict[str, Any]]:
    """The R4 pair (V1): one engine call per loader run, each read only at its own event run.

    The primary run is ``runs[(case, "primary")]`` of the call on ``tilt_frames(run="primary")``; the rerun is
    ``runs[(case, "last_close")]`` of the call on ``tilt_frames(run="last_close")``. The engine's single-call
    fields ``fragile_active_sign`` and ``fragile_lowrisk_active_sign`` are never read.

    Screen months use ``SCREEN_COST_SCHEDULE`` with no half-spread panel (``books.costs.which_schedule``); confirm
    and check runs use ``COST_SCHEDULE`` with the half-spread panel. ``min_valid`` replaces ``half_rule(n)`` (the
    Family A baseline, OI-06).
    """
    if (period == "screen") != (half_spread is None):
        raise refuse("schedule_invalid", "the half-spread override applies in the confirm and check runs only")
    out = {}
    for run in RUNS:
        inputs = inputs_for(frames[run], signals[run], start, end)
        if min_valid is not None:
            inputs = replace(inputs, min_valid=min_valid)
        # The screen windows keep the run 2 check (1992-12); a confirm or check window ends at its segment end.
        check_engine_cut(inputs, crit.SCREEN_END if period == "screen" else end.to_period("M"), period, half_spread)
        if half_spread is None:
            output = tilt.run_index_tilt(inputs, crit.SCREEN_COST_SCHEDULE)
        else:
            output = tilt.run_index_tilt(inputs, tilt.COST_SCHEDULE, half_spread=half_spread)
        out[run] = {"cases": {case: output["runs"][(case, run)] for case in CASES}, "targets": output["targets"],
                    "rebalances": output["rebalances"]}
    return out


def look_stage(data: w.WrdsData, trial: Mapping[str, Any], out: Path) -> dict[str, Any]:
    """CW-PIT against vwretd over the screen months (coverage, TE, correlation, mean gap) and each run's blank set.

    The engine runs with an all-missing signal set, so every composite is 0 and TILT equals CW-PIT (checked); the
    look reads CW-PIT and ``vwretd`` only.
    """
    exits = exit_map(data)
    months = pd.period_range(crit.SCREEN_START, crit.SCREEN_END, freq="M")
    vw = monthly_vwretd(data, crit.SCREEN_START)
    start, end = window(w.calendar(data), crit.SCREEN_START)
    frames = {run: frames_for(data, run) for run in RUNS}
    pair = engine_pair(frames, {run: no_signal(frames[run]) for run in RUNS}, start, end)
    result: dict[str, Any] = {"header": header(trial), "runs": {}}
    gaps, entries = {}, []
    for run in RUNS:
        books = pair[run]["cases"]
        if any(not books[case]["tilt"]["monthly_net"].equals(books[case]["cw"]["monthly_net"]) for case in CASES):
            raise refuse("look_tilt_not_cw", run)
        sets = {case: path_break_positions(frames[run], {"cw": books[case]["cw"]["weights"]}, exits, months, end)
                for case in CASES}
        if blank_set(sets["primary"]) != blank_set(sets["sensitivity_2x"]):
            raise refuse("blank_set_mismatch", f"{run}: the cost cases hold different positions")
        run_set = blank_set(sets["primary"])
        declared = declaration(run_set, crit.SCREEN_START)
        held = Counter(p["exit_class"] for p in sets["primary"])
        weight = Counter()
        for p in sets["primary"]:
            weight[p["exit_class"]] += p["weight_at_last_rebalance"]["cw"]
        part = {"blank_months": [str(m) for m in run_set], "blank_month_count": len(run_set),
                "blank_month_share": len(run_set) / len(months), "positions": sets["primary"],
                "positions_by_exit_class": per_class(held),
                "cw_weight_by_exit_class": {c: float(weight.get(c, 0.0)) for c in EXIT_CLASSES},
                "blanked_level_windows": blanked_windows(frames[run], pair[run]["rebalances"].index, exits, end),
                "coverage": rebalance_counts(pair[run]["rebalances"])}
        for case in CASES:
            book = books[case]["cw"]
            check_declaration(declared, run_set, crit.SCREEN_START)
            stats = mean_gap(book["monthly_net"], vw, declared)
            entries.append({"stage": "look", "call": "check_paired", "series": "cw_vs_vwretd", "run": run,
                            "case": case, "span": [crit.SCREEN_START, crit.SCREEN_END], "declaration": declared,
                            "output": stats})
            part[case] = {"cw_vs_vwretd": stats, "r4": r4_counts(book, frames[run]["disappearances"], end, run),
                          "cw_annual_turnover": book["annual_turnover"],
                          "cw_annual_cost_drag": book["annual_cost_drag"]}
            gaps[(run, case)] = stats["annual_mean_gap"]
        result["runs"][run] = part
    result["fragility"] = {case: fragility({"cw_vs_vwretd": gaps[("primary", case)]},
                                           {"cw_vs_vwretd": gaps[("last_close", case)]}) for case in CASES}
    for entry in entries:                   # after every check of the look that can refuse (AUDIT_2 ADV-2)
        log(out, entry)
    return result


def undefined_record(months: pd.PeriodIndex, declared: Mapping[pd.Period, str],
                     reason: str = "screen_too_short") -> dict[str, Any]:
    """OI-05: fewer than 36 screen months with values gives a typed undefined record. ``screen_record`` is not
    called for it (its ``check_series`` would refuse ``screen_too_short`` and stop the whole screen). The reason
    ``primary_screen_too_short`` types a run that has 36 months or more when the primary run has fewer."""
    kept = months[~months.isin(pd.PeriodIndex(list(declared), freq="M"))]
    return {"status": "undefined", "undefined_reason": reason,
            "first_month": str(kept[0]) if len(kept) else None, "last_month": str(kept[-1]) if len(kept) else None,
            "months": len(kept), "annual_active_mean": None, "annual_te": None, "information_ratio": None,
            "hac_t": None, "p_one_sided": None, "annual_turnover": None, **crit.blank_record(declared)}


def not_evaluated(short: list[str]) -> dict[str, Any]:
    """The R4 fragility of a candidate with a run of fewer than 36 months: typed, never computed."""
    return {case: {"status": "not_evaluated", "reason": "screen_too_short", "short_runs": short} for case in CASES}


def screen_stage(data: w.WrdsData, trial: Mapping[str, Any], out: Path, coverage: Mapping[str, Any],
                 look: Mapping[str, Any]) -> dict[str, Any]:
    """Each candidate alone over its screen months, both loader runs, both cost cases; the reports owed."""
    exits = exit_map(data)
    cal = w.calendar(data)
    inputs = screen_inputs(data)
    panels = signal_panels(data, inputs)
    check_decision_rows(panels, data, inputs)
    starts = real_starts(panels)
    if starts != {s: coverage["signals"][s]["real_start"] for s in sig.SIGNAL_IDS}:
        raise refuse("coverage_mismatch", "the real starts differ from the coverage stage")
    publication = next(o for o in trial["open_items"] if o["id"] == "OI-08")["publication_years"]
    vw = monthly_vwretd(data, crit.SCREEN_START)
    run_sets = {run: look["runs"][run]["blank_months"] for run in RUNS}
    frames = {run: frames_for(data, run) for run in RUNS}
    full_start, end = window(cal, crit.SCREEN_START)
    unseen = unseen_cells(data)
    setups = {}
    result: dict[str, Any] = {"header": header(trial), "blank_months": run_sets, "candidates": {}, "r6": {}}
    for run in RUNS:
        inputs = inputs_for(frames[run], no_signal(frames[run]), full_start, end)
        dates = tilt.rebalance_dates(frames[run]["prices"].index, full_start, end)
        setups[run] = census(inputs, dates)
        blanked = blanked_windows(frames[run], dates, exits, end)["by_exit_class"]
        result["r6"][run] = r6_members(inputs, setups[run], exits, unseen, blanked)
    records = {}
    for s in sig.SIGNAL_IDS:
        first = first_month(starts[s])
        span = pd.PeriodIndex([], freq="M") if first is None else pd.period_range(first, crit.SCREEN_END, freq="M")
        declared = {run: {} if first is None else declaration(run_sets[run], first) for run in RUNS}
        counts = {run: len(span) - len(declared[run]) for run in RUNS}
        short = [run for run in RUNS if counts[run] < crit.SCREEN_MIN_MONTHS]
        item: dict[str, Any] = {"real_start": starts[s], "first_month": first, "months_with_values": counts,
                                "records": {run: {} for run in RUNS}}
        result["candidates"][s] = item
        entries = []
        if "primary" in short:
            # A typed record for every run and cost case, and no engine call or return for this candidate.
            for run in RUNS:
                if first is not None:
                    check_declaration(declared[run], run_sets[run], first)
                record = undefined_record(span, declared[run],
                                          "screen_too_short" if run in short else "primary_screen_too_short")
                for case in CASES:
                    item["records"][run][case] = {"screen_record": record}
                    entries.append({"stage": "screen", "call": "undefined_record", "candidate": s, "run": run,
                                    "case": case, "span": [first, crit.SCREEN_END], "declaration": declared[run],
                                    "output": record})
            item["fragility"] = not_evaluated(short)
            for entry in entries:
                log(out, entry)
            records[s] = item["records"]["primary"]["primary"]["screen_record"]
            continue
        start, _ = window(cal, first)
        dates = tilt.rebalance_dates(frames["primary"]["prices"].index, start, end)
        signals = {run: {s: signal_frame(panels, s, frames[run], dates)} for run in RUNS}
        pair = engine_pair(frames, signals, start, end)
        means: dict[str, dict[str, dict[str, float]]] = {run: {} for run in RUNS}
        item["path_break_positions"] = {}
        for run in RUNS:
            for case in CASES:
                found = pair[run]["cases"][case]
                held = path_break_positions(frames[run], {"cw": found["cw"]["weights"],
                                                          "tilt": found["tilt"]["weights"]}, exits, span, end)
                if not set(blank_set(held)) <= set(declared[run]):
                    raise refuse("path_break_undeclared", f"{s} {run} {case}")
                if case == "primary":
                    item["path_break_positions"][run] = held
                check_declaration(declared[run], run_sets[run], first)
                if run in short:
                    record = undefined_record(span, declared[run])
                    item["records"][run][case] = {"screen_record": record}
                    entries.append({"stage": "screen", "call": "undefined_record", "candidate": s, "run": run,
                                    "case": case, "span": [first, crit.SCREEN_END], "declaration": declared[run],
                                    "output": record})
                    continue
                check_months(found["tilt"]["monthly_net"], found["cw"]["monthly_net"])
                record = crit.screen_record(without(found["tilt"]["monthly_net"], declared[run]),
                                            without(found["cw"]["monthly_net"], declared[run]),
                                            found["tilt"]["annual_turnover"], declared[run])
                vs_vw = mean_gap(found["tilt"]["monthly_net"], vw.reindex(span), declared[run])
                cw_vw = mean_gap(found["cw"]["monthly_net"], vw.reindex(span), declared[run])
                for call, series, output in (("screen_record", "tilt_vs_cw", record),
                                             ("check_paired", "tilt_vs_vwretd", vs_vw),
                                             ("check_paired", "cw_vs_vwretd", cw_vw)):
                    entries.append({"stage": "screen", "call": call, "series": series, "candidate": s, "run": run,
                                    "case": case, "span": [first, crit.SCREEN_END], "declaration": declared[run],
                                    "output": output})
                item["records"][run][case] = {
                    "screen_record": record, "tilt_vs_vwretd": vs_vw, "cw_vs_vwretd": cw_vw,
                    "tilt_stats": tilt_stats(found, declared[run], frames[run], pair[run]["targets"], publication[s]),
                    "r4": {book: r4_counts(found[book], frames[run]["disappearances"], end, run)
                           for book in ("cw", "tilt")}}
                means[run][case] = {"tilt_vs_cw": record["annual_active_mean"],
                                    "tilt_vs_vwretd": vs_vw["annual_mean_gap"],
                                    "cw_vs_vwretd": cw_vw["annual_mean_gap"]}
        table = {run: pair[run]["rebalances"] for run in RUNS}
        item["counts"] = {run: rebalance_counts(table[run]) for run in RUNS}
        item["c_zero_by_exit_class"] = {run: c_zero_by_exit(
            inputs_for(frames[run], signals[run], start, end), {d: setups[run][d] for d in table[run].index},
            table[run], exits) for run in RUNS}
        item["fragility"] = (not_evaluated(short) if short else
                             {case: fragility(means["primary"][case], means["last_close"][case]) for case in CASES})
        for entry in entries:               # after every check of this candidate that can refuse (AUDIT_2 ADV-2)
            log(out, entry)
        records[s] = item["records"]["primary"]["primary"]["screen_record"]
    result["records_for_freeze"] = records
    return result


def freeze_stage(screen: Mapping[str, Any], out: Path) -> dict[str, Any]:
    """Freeze the shortlist from the gated screen records; the digest is saved before any confirm month opens."""
    frozen = crit.freeze_shortlist(screen["result"]["records_for_freeze"])
    crit.verify_frozen_screen(frozen, frozen["digest_sha256"])
    log(out, {"stage": "freeze", "call": "freeze_shortlist", "declaration": {
        c: r.get("blank_months", {}) for c, r in frozen["candidates"].items()}, "output": frozen})
    return {"record": frozen, "digest_sha256": frozen["digest_sha256"], "decision": frozen["decision"],
            "shortlist": frozen["shortlist"]}


# Confirm and check: segments, inputs, and reports --------------------------------------------

def check_period_end(cal: pd.DatetimeIndex) -> pd.Period:
    """``periods.check.segments``: the last month M with a calendar row in M + 1 (expected 2025-11)."""
    last = cal[-1].to_period("M") - 1
    if last < POST_SEAL_FIRST:
        raise refuse("check_period_invalid", f"the calendar ends before {POST_SEAL_FIRST}")
    return last


def segment_plan(cal: pd.DatetimeIndex) -> dict[str, dict[str, Any]]:
    """The run segments of ``periods.confirm.segments`` and ``periods.check.segments``, dates from the calendar.

    A segment for return months ``first`` to ``last`` is anchored at the last row of ``first - 2`` (all cash),
    first rebalances at the last row of ``first - 1``, and ends at the last row of ``last``.
    """
    ends = month_ends(cal)
    spans = {"confirm": ("confirm", crit.CONFIRM_START, crit.CONFIRM_END),
             "check_pre_seal": ("check", crit.CHECK_START, PRE_SEAL_LAST),
             "check_post_seal": ("check", POST_SEAL_FIRST, check_period_end(cal))}
    out = {}
    for name, (period, first, last) in spans.items():
        if any(m not in ends.index for m in (first - 2, first - 1, last)):
            raise refuse("calendar_month_missing", f"{name}: a segment month has no calendar row")
        out[name] = {"name": name, "period": period, "first": first, "last": last, "anchor": ends[first - 2],
                     "first_rebalance": ends[first - 1], "end": ends[last]}
    post = out["check_post_seal"]
    if (post["anchor"], post["first_rebalance"]) != (POST_SEAL_ANCHOR, POST_SEAL_FIRST_REBALANCE):
        raise refuse("post_seal_anchor_mismatch", f"the post-seal segment starts at {POST_SEAL_ANCHOR.date()}")
    return out


def segment_frames(data: w.WrdsData, run: str, segment: Mapping[str, Any]) -> dict[str, Any]:
    """The loader frames of one segment, cut at its end row right after the load (``cut_frames``)."""
    return cut_frames(w.tilt_frames(data, segment["anchor"], segment["end"], run), segment["end"])


def segment_months(panel: pd.DataFrame, segment: Mapping[str, Any]) -> pd.DataFrame:
    """A rebalance-row panel indexed by the return month each row forms, kept to the segment's months."""
    months = panel.index.to_period("M") + 1
    keep = (months >= segment["first"]) & (months <= segment["last"])
    out = panel[keep]
    out.index = months[keep].to_timestamp()
    return out


def market_level(data: w.WrdsData, rows: pd.DatetimeIndex, last: pd.Timestamp) -> pd.Series:
    """The INDNO 1000200 total-return level on one seal segment's rows, 1.0 on its first row, cut at ``last``
    (``candidates.family_a_baseline.crsp_inputs``). A missing market return refuses."""
    returns = w.benchmarks(data)["crsp_vw_market"].reindex(rows).to_numpy(dtype=float).copy()
    inside = np.asarray(rows <= last)
    returns[0] = 0.0
    if np.isnan(returns[inside]).any():
        raise refuse("market_return_missing", "an INDNO 1000200 return is missing on a segment row")
    level = np.cumprod(1.0 + np.where(inside, returns, 0.0))
    level[~inside] = np.nan
    return pd.Series(level, index=rows)


def dollar_volume(data: w.WrdsData, rows: pd.DatetimeIndex, columns: pd.Index, last: pd.Timestamp) -> pd.DataFrame:
    """|dlyprc| x dlyvol on the frame rows up to ``last``, with the Gao and Ritter divisors on 'Q' rows (OI-12)."""
    daily = w.daily(data)
    part = daily[daily["permno"].astype(str).isin(columns) & daily["date"].isin(rows) & (daily["date"] <= last)]
    divisor = np.ones(len(part))
    nasdaq = (part["primaryexch"] == NASDAQ).to_numpy()
    for first, value in GAO_RITTER:
        on = nasdaq if first is None else nasdaq & (part["date"] >= pd.Timestamp(first)).to_numpy()
        divisor[on] = value
    values = part["prc"].to_numpy(dtype=float) * part["dlyvol"].to_numpy(dtype=float) / divisor
    table = pd.DataFrame({"date": part["date"].to_numpy(), "permno": part["permno"].astype(str).to_numpy(),
                          "value": values})
    return table.pivot(index="date", columns="permno", values="value").reindex(index=rows, columns=columns)


def family_a_panel(data: w.WrdsData, frames: Mapping[str, Any], last: pd.Timestamp) -> dict[str, pd.DataFrame]:
    """The six Family A signals (``family_a_signals``) on one segment's primary price path, masked by
    eligibility, with no value after ``last``.

    A signal whose window of ``warmup_rows`` rows ending at row t holds a ``path_break`` row is blank at t
    (``P1_path_break``: a level window across a break is not known). One panel serves both loader runs.
    """
    prices = frames["prices"]
    rows = prices.index
    raw = family_a_signals(prices, market_level(data, rows, last), dollar_volume(data, rows, prices.columns, last),
                           frames["eligible"])
    breaks = frames["path_break"].astype(float)
    after_last = np.asarray(rows > last)[:, None]
    out = {}
    for factor in FAMILY_A:
        held = breaks.rolling(factor.warmup_rows, min_periods=1).max().to_numpy() > 0.0
        out[factor.factor_id] = raw[factor.factor_id].mask(held | after_last)
    return out


def quote_panels(table: pd.DataFrame, frames: Mapping[str, Any], last: pd.Timestamp) -> dict[str, pd.DataFrame]:
    """The half-spread (bp), the quote reason, and the 'BA' flag of each frame cell, from quote rows up to
    ``last`` (``m55_index_tilt.half_spreads``)."""
    rows, columns = frames["prices"].index, frames["prices"].columns
    part = table[table["date"].isin(rows) & (table["date"] <= last) & table["permno"].isin(columns)]
    keyed = part.set_index(["date", "permno"])

    def panel(column: str) -> pd.DataFrame:
        return keyed[column].unstack().reindex(index=rows, columns=columns)

    quoted = pd.Series(True, index=keyed.index).unstack(fill_value=False).reindex(index=rows, columns=columns,
                                                                                 fill_value=False).astype(bool)
    values, reasons = tilt.half_spreads(panel("dlybid").astype(float), panel("dlyask").astype(float), quoted)
    return {"half_spread": values, "reason": reasons, "ba": (panel("dlyprcflg") == w.BID_ASK_FLAG).astype(bool)}


def half_spread_report(book: Mapping[str, Any], quotes: Mapping[str, pd.DataFrame], exits: Mapping[str, str],
                       scale: float) -> dict[str, Any]:
    """reports_owed.half_spread for one book, by year of the rebalance row r (quote cells at r - 1)."""
    trades = book["trades"]
    dates = trades.index
    rows = quotes["half_spread"].index
    prior = rows[[rows.get_loc(d) - 1 for d in dates]]
    names = trades.columns
    t = trades.to_numpy(dtype=float)
    spread = quotes["half_spread"].loc[prior, names].to_numpy(dtype=float)
    reason = quotes["reason"].loc[prior, names].to_numpy(dtype=object)
    ba = quotes["ba"].loc[prior, names].to_numpy(dtype=bool)
    base = tilt.dated_cost_frame(dates, tilt.COST_SCHEDULE, 1.0)["slippage_bps"].to_numpy()
    valid = pd.isna(reason)
    status = np.where(valid, "valid", reason)
    traded = t > 0.0
    scheduled = book["turnover"].loc[dates].to_numpy() * (base * scale / 10_000.0) * (
        1.0 + book["daily_gross"].loc[dates].to_numpy())
    above = book["slippage"].to_numpy(dtype=float) - scheduled
    member_exit = np.array([exits[n] for n in names])
    out = {}
    for year in sorted(set(dates.year)):
        k = np.asarray(dates.year == year)
        tk, total = t[k], float(t[k].sum())
        binds = valid[k] & (spread[k] > base[k][:, None])
        invalid = Counter((str(r), str(e)) for r, e in zip(reason[k][traded[k] & ~valid[k]],
                                                            np.broadcast_to(member_exit, tk.shape)[traded[k] & ~valid[k]]))
        cells = spread[k][traded[k] & valid[k]]
        out[str(year)] = {
            "traded_notional": total,
            "traded_notional_by_status": {s: float(tk[status[k] == s].sum())
                                          for s in ("valid", *tilt.QUOTE_REASONS)},
            "crsp_binds_share": float(tk[binds].sum()) / total if total else None,
            "bid_ask_share": float(tk[ba[k]].sum()) / total if total else None,
            "max_half_spread": float(cells.max()) if len(cells) else None,
            "cost_above_schedule": float(above[k].sum()),
            "invalid_traded_cells_by_exit_class": {r: {c: int(invalid.get((r, c), 0)) for c in EXIT_CLASSES}
                                                   for r in tilt.QUOTE_REASONS}}
    return out


def monthly_spy(data: w.WrdsData, segment: Mapping[str, Any]) -> pd.Series:
    """SPY total return (``benchmarks`` column ``spy``) compounded by calendar month over the segment's months, up to
    its end row; a missing day refuses."""
    cal = w.calendar(data)
    rows = cal[(cal.to_period("M") >= segment["first"]) & (cal <= segment["end"])]
    daily = w.benchmarks(data)["spy"].reindex(rows)
    if daily.isna().any():
        raise refuse("spy_return_missing", f"{segment['name']}: a SPY return is missing")
    monthly = (1.0 + daily).groupby(rows.to_period("M")).prod() - 1.0
    return monthly.rename("spy")


def signal_sets(panels: Mapping[str, Any], frames: Mapping[str, Mapping[str, Any]], dates: pd.DatetimeIndex,
                shortlist: list[str], family: Mapping[str, pd.DataFrame]) -> dict[str, dict[str, Any]]:
    """The composite of the frozen shortlist (``half_rule(n)``), S1 to S8 alone (``half_rule(1)``), and the Family A
    baseline (``MIN_VALID_SIGNALS``, OI-06). Each S1 to S8 frame is built once per loader run."""
    single = {s: {run: signal_frame(panels, s, frames[run], dates) for run in RUNS} for s in sig.SIGNAL_IDS}
    sets = {COMPOSITE: {"signals": {run: {s: single[s][run] for s in shortlist} for run in RUNS}, "min_valid": None}}
    sets.update({s: {"signals": {run: {s: single[s][run]} for run in RUNS}, "min_valid": None} for s in sig.SIGNAL_IDS})
    sets[FAMILY_A_SET] = {"signals": {run: dict(family) for run in RUNS}, "min_valid": tilt.MIN_VALID_SIGNALS}
    return sets


def publication_years(name: str, shortlist: list[str], publication: Mapping[str, int]) -> list[int]:
    """OI-08 years of a set: one per single signal, the shortlist years for the composite, none for Family A."""
    ids = shortlist if name == COMPOSITE else [] if name == FAMILY_A_SET else [name]
    return sorted({publication[s] for s in ids})


def segment_r6(panels: Mapping[str, Any], segment: Mapping[str, Any], exits: Mapping[str, str]) -> dict[str, Any]:
    """reports_owed.r6 signal part: each signal's reason counts by year and its reason shares by later exit class."""
    members = segment_months(panels["members"], segment)
    member_exit = np.array([exits[str(p)] for p in members.columns])
    out = {}
    for s in sig.SIGNAL_IDS:
        cells = cell_table(members, segment_months(panels["reasons"][s], segment), member_exit)
        by_exit = counts_of(cells, "exit")
        totals = {c: sum(by_exit.get(c, {}).values()) for c in EXIT_CLASSES}
        out[s] = {"reason_counts_by_year": counts_of(cells, "year"),
                  "reason_share_by_exit_class": {r: shares({c: by_exit.get(c, {}).get(r, 0) for c in EXIT_CLASSES},
                                                           totals) for r in sorted(set(cells["reason"]))}}
    return out


def member_day_report(data: w.WrdsData, segments: list[Mapping[str, Any]], exits: Mapping[str, str]) -> dict[str, Any]:
    """me_coverage, the basis_unseen cases, and bid_ask_midpoint_share over the member-days of the segments
    (rows after each anchor up to its end row)."""
    days = w.member_days(data)
    keep = np.zeros(len(days), dtype=bool)
    for segment in segments:
        keep |= ((days["date"] > segment["anchor"]) & (days["date"] <= segment["end"])).to_numpy()
    days = days[keep].copy()
    days["year"] = days["date"].dt.year
    days["exit"] = days["permno"].astype(str).map(exits)
    basis = {case: {str(y): int(n) for y, n in days.loc[days["basis_unseen"] == case, "year"].value_counts()
                    .sort_index().items()} for case in ("data_start", "seal")}
    return {"me_coverage": {"by_year": w._shares(days, "year"), "by_exit_class": w._shares(days, "exit"),
                            "basis_unseen_member_days_by_year": basis},
            "bid_ask_midpoint_share": float((days["dlyprcflg"] == w.BID_ASK_FLAG).mean()) if len(days) else None}


def run_segment(data: w.WrdsData, quotes: pd.DataFrame, segment: Mapping[str, Any], shortlist: list[str],
                exits: Mapping[str, str], publication: Mapping[str, int], unseen: set) -> dict[str, Any]:
    """Every signal set on one segment: both loader runs, both cost cases, the half-spread override.

    Returns the monthly series of each set, run, and case, the declaration of each run, and the reports owed. The
    blank set of a run is that of its CW-PIT book (same in every set), and each other book must lie inside it.
    """
    period, anchor, end, last = segment["period"], segment["anchor"], segment["end"], segment["last"]
    frames = {run: segment_frames(data, run, segment) for run in RUNS}
    rows, columns = frames["primary"]["prices"].index, frames["primary"]["prices"].columns
    if any(not frames[run]["prices"].index.equals(rows) or not frames[run]["prices"].columns.equals(columns)
           for run in RUNS):
        raise refuse("frames_misaligned", "the loader runs differ in rows or columns")
    dates = tilt.rebalance_dates(rows, anchor, end)
    if dates[0] != segment["first_rebalance"] or dates[-1] != end:
        raise refuse("segment_dates_invalid", segment["name"])
    months = pd.period_range(segment["first"], last, freq="M")
    inputs = cut_inputs(w.signal_inputs(data), end)
    post = bool(anchor >= sig.SEAL[1])
    panels = segment_signals(inputs, dates, end, period)
    check_decision_rows(panels, data, inputs, post)
    quote = quote_panels(quotes, frames["primary"], end)
    sets = signal_sets(panels, frames, dates, shortlist, family_a_panel(data, frames["primary"], end))
    setups, result = {}, {"segment": {k: v for k, v in segment.items()}, "runs": {}, "sets": {}}
    for run in RUNS:
        census_inputs = inputs_for(frames[run], no_signal(frames[run]), anchor, end)
        setups[run] = census(census_inputs, dates, last, period)
        blanked = blanked_windows(frames[run], dates, exits, end)
        result["runs"][run] = {"blanked_level_windows": blanked,
                               "r6_members": r6_members(census_inputs, setups[run], exits, unseen,
                                                        blanked["by_exit_class"])}
    series: dict[str, dict] = {}
    declared: dict[str, dict] = {}
    for name, spec in sets.items():
        pair = engine_pair(frames, spec["signals"], anchor, end, period, quote["half_spread"], spec["min_valid"])
        if not declared:
            for run in RUNS:
                held = {case: path_break_positions(frames[run], {"cw": pair[run]["cases"][case]["cw"]["weights"]},
                                                   exits, months, end) for case in CASES}
                if blank_set(held["primary"]) != blank_set(held["sensitivity_2x"]):
                    raise refuse("blank_set_mismatch", f"{segment['name']} {run}: the cost cases hold different positions")
                run_set = blank_set(held["primary"])
                declared[run] = declaration(run_set, segment["first"], last)
                weight = Counter()
                for p in held["primary"]:
                    weight[p["exit_class"]] += p["weight_at_last_rebalance"]["cw"]
                result["runs"][run].update({
                    "blank_months": [str(m) for m in run_set], "blank_month_count": len(run_set),
                    "blank_month_share": len(run_set) / len(months), "positions": held["primary"],
                    "positions_by_exit_class": per_class(Counter(p["exit_class"] for p in held["primary"])),
                    "cw_weight_by_exit_class": {c: float(weight.get(c, 0.0)) for c in EXIT_CLASSES}})
        item: dict[str, Any] = {"records": {run: {} for run in RUNS}, "path_break_positions": {}}
        series[name] = {run: {} for run in RUNS}
        years = publication_years(name, shortlist, publication)
        for run in RUNS:
            for case in CASES:
                found = pair[run]["cases"][case]
                held = path_break_positions(frames[run], {"cw": found["cw"]["weights"], "tilt": found["tilt"]["weights"]},
                                            exits, months, end)
                if not set(blank_set(held)) <= set(declared[run]):
                    raise refuse("path_break_undeclared", f"{name} {segment['name']} {run} {case}")
                if case == "primary":
                    item["path_break_positions"][run] = held
                check_months(found["tilt"]["monthly_net"], found["cw"]["monthly_net"], last=last, period=period)
                series[name][run][case] = {"tilt": found["tilt"]["monthly_net"], "cw": found["cw"]["monthly_net"]}
                stats = tilt_stats(found, declared[run], frames[run], pair[run]["targets"], None, period, last)
                active = without(found["tilt"]["monthly_net"] - found["cw"]["monthly_net"], declared[run])
                stats["post_publication"] = [post_publication(active, y) for y in years]
                item["records"][run][case] = {
                    "tilt_stats": stats,
                    "r4": {book: r4_counts(found[book], frames[run]["disappearances"], end, run) for book in tilt.BOOKS},
                    "half_spread": {book: half_spread_report(found[book], quote, exits, tilt.COST_SCALES[case])
                                    for book in tilt.BOOKS}}
        table = {run: pair[run]["rebalances"] for run in RUNS}
        item["counts"] = {run: rebalance_counts(table[run]) for run in RUNS}
        if name in sig.SIGNAL_IDS:
            item["c_zero_by_exit_class"] = {run: c_zero_by_exit(
                inputs_for(frames[run], spec["signals"][run], anchor, end), {d: setups[run][d] for d in table[run].index},
                table[run], exits) for run in RUNS}
        result["sets"][name] = item
    members = segment_months(panels["members"], segment)
    decision = pd.DatetimeIndex([rows[rows.get_loc(r) - 1] for r in dates
                                 if segment["first"] <= r.to_period("M") + 1 <= last])
    me = member_me(data, decision, members.columns).set_axis(members.index, axis=0)
    reasons_s2 = segment_months(panels["reasons"]["S2"], segment)
    result["signals_r6"] = segment_r6(panels, segment, exits)
    result["s2_short_history"] = s2_size(members, reasons_s2, me)
    s2_valid = (members & reasons_s2.isna()).sum(axis=1) / members.sum(axis=1).where(members.sum(axis=1) > 0)
    result["s2_valid_share_by_month"] = {str(m.to_period("M")): float(v) for m, v in s2_valid.items()}
    result["s2_split_in_basis_window_by_year"] = {
        str(y): int(((reasons_s2 == "split_in_basis_window") & members)[members.index.year == y].to_numpy().sum())
        for y in sorted(set(members.index.year))}
    result["s2_basis_quarters_by_year"] = {
        y: c for y, c in s2_basis_quarters(segment_inputs(inputs, post), end).items()
        if anchor.year <= int(y) <= end.year}
    return {"result": result, "series": series, "declared": declared, "inputs": inputs, "rows": rows}


def s2_seal_quarters(inputs: sig.SignalInputs, first_post: pd.Timestamp, last: pd.Timestamp) -> dict[str, int]:
    """reports_owed.s2_history_rule: member quarters with rdq before the first post-seal row and a known date on or
    after it, by year of the known date. They have no S2 value, because signals are built per seal segment.
    Membership and links are read as in ``s2_basis_quarters``."""
    check_inputs_cut(inputs, last, "check")
    data = sig._Signals(inputs)
    links, members, out = {}, {}, Counter()
    post, end = np.datetime64(first_post), np.datetime64(last)
    for gvkey, rec in data.quarterly.items():
        for i in range(len(rec["quarter"])):
            basis, rdq = rec["basis"][i], rec["rdq"][i]
            if np.isnat(basis) or np.isnat(rdq) or not (rdq < post <= basis <= end):
                continue
            if basis not in links:
                links[basis] = {g: p for p, g in data.links_at(basis).items() if g != "ambiguous_link"}
                members[basis] = set(data.members_at(basis))
            permno = links[basis].get(gvkey)
            if permno is not None and permno in members[basis]:
                out[str(pd.Timestamp(basis).year)] += 1
    return {y: int(n) for y, n in sorted(out.items())}


def open_gate(trial: Mapping[str, Any], payloads: Mapping[str, dict], digests: Mapping[str, str]) -> tuple:
    """The frozen-screen gate of every confirm and check call, on the run 2 digest that amendment 3 states, and
    test B as stopped (amendment 2): p_B = 1.0 in Holm. Another calibration decision would need test B, which this
    trial file no longer runs, so it refuses (a stop for the owner)."""
    record = payloads["freeze"]["result"]["record"]
    digest = run2_digest(trial)
    if not crit.verify_frozen_screen(record, digest):
        raise refuse("screen_empty_confirm", "screen_empty: no confirm month is opened for a tilt")
    test_b = record_test_b(payloads["calibration"]["result"], digests["calibration"])
    if not test_b["stopped"]:
        raise refuse("test_b_open", "test B is stopped only after ratio_coverage_low (amendment 2)")
    return record, digest, test_b


def three(series: Mapping[str, pd.Series], spy: pd.Series, declared: Mapping[pd.Period, str]) -> tuple:
    """The composite, SPY, and CW-PIT series of one comparison without the declared blank months."""
    return without(series["tilt"], declared), without(spy, declared), without(series["cw"], declared)


def set_means(series: Mapping[str, dict], spy: pd.Series, declared: Mapping[str, dict], period: str,
              entries: list, stage: str, span: list) -> dict[str, dict]:
    """``composite_means`` of every set, loader run, and cost case (the sign rules and the R4 comparison)."""
    out: dict[str, dict] = {}
    for name, runs in series.items():
        out[name] = {run: {} for run in RUNS}
        for run in RUNS:
            for case in CASES:
                found = crit.composite_means(*three(runs[run][case], spy, declared[run]), period, declared[run])
                out[name][run][case] = found
                entries.append({"stage": stage, "call": "composite_means", "set": name, "run": run, "case": case,
                                "span": span, "declaration": declared[run], "output": found})
    return out


def set_fragility(means: Mapping[str, dict]) -> dict[str, dict]:
    """R4 (reports_owed.fragility): a sign flip of an active annual mean between the two loader runs."""
    return {name: {case: fragility({k: runs["primary"][case][k] for k in ("vs_spy", "vs_cw")},
                                   {k: runs["last_close"][case][k] for k in ("vs_spy", "vs_cw")}) for case in CASES}
            for name, runs in means.items()}


def oi09(series: Mapping[str, dict], spy: pd.Series, declared: Mapping[str, dict], means: Mapping[str, dict],
         period: str, last: pd.Period, entries: list, stage: str, span: list) -> dict[str, dict]:
    """OI-09: CW-PIT against SPY, and both terms of tilt - SPY = (tilt - CW-PIT) + (CW-PIT - SPY) for the composite."""
    out: dict[str, dict] = {run: {} for run in RUNS}
    for run in RUNS:
        for case in CASES:
            books = series[COMPOSITE][run][case]
            gap = mean_gap(books["cw"], spy, declared[run], period, last)
            entries.append({"stage": stage, "call": "check_paired", "series": "cw_vs_spy", "run": run, "case": case,
                            "span": span, "declaration": declared[run], "output": gap})
            found = means[COMPOSITE][run][case]
            out[run][case] = {"cw_vs_spy": gap, "decomposition": {
                "tilt_vs_spy": found["vs_spy"], "tilt_vs_cw": found["vs_cw"], "cw_vs_spy": gap["annual_mean_gap"]}}
    return out


def secondary(record: Mapping[str, Any], digest: str, series: Mapping[str, dict], spy: pd.Series,
              declared: Mapping[str, dict], family_size: int, entries: list, span: list) -> dict[str, dict]:
    """The secondary family (BY q-values) for each loader run and cost case. A member whose ``composite_test``
    refuses with ``statistic_undefined`` (zero or undefined TE or t) is typed undefined and left out; the family
    keeps its size (``secondary_family.size_rule``)."""
    out: dict[str, dict] = {run: {} for run in RUNS}
    for run in RUNS:
        for case in CASES:
            members, undefined = {}, {}
            for name in SECONDARY:
                parts = three(series[name][run][case], spy, declared[run])
                try:
                    crit.composite_test(*parts, declared[run])
                except tilt.runner.RunnerStop as exc:
                    if exc.reason != "statistic_undefined":
                        raise
                    undefined[name] = {"status": "undefined", "undefined_reason": exc.reason, "detail": exc.detail}
                    continue
                members[name] = dict(zip(("composite", "spy", "cw"), parts))
            found = crit.secondary_family(record, digest, members, family_size, declared[run])
            out[run][case] = {**found, "undefined": undefined}
            entries.append({"stage": "confirm", "call": "secondary_family", "run": run, "case": case, "span": span,
                            "declaration": declared[run], "output": out[run][case]})
    return out


def baseline_screen(data: w.WrdsData, look: Mapping[str, Any], exits: Mapping[str, str],
                    entries: list) -> dict[str, Any]:
    """The Family A baseline over the screen months (``family_a_baseline.role``): cut at 1992-12-31,
    ``SCREEN_COST_SCHEDULE``, no half-spread panel, the look's blank set of each run. Not in the freeze."""
    cal = w.calendar(data)
    frames = {run: frames_for(data, run) for run in RUNS}
    start, end = window(cal, crit.SCREEN_START)
    family = family_a_panel(data, frames["primary"], end)
    pair = engine_pair(frames, {run: dict(family) for run in RUNS}, start, end, min_valid=tilt.MIN_VALID_SIGNALS)
    vw = monthly_vwretd(data, crit.SCREEN_START)
    months = pd.period_range(crit.SCREEN_START, crit.SCREEN_END, freq="M")
    span = [crit.SCREEN_START, crit.SCREEN_END]
    out: dict[str, Any] = {"records": {run: {} for run in RUNS}}
    means: dict[str, dict] = {run: {} for run in RUNS}
    for run in RUNS:
        run_set = look["runs"][run]["blank_months"]
        declared = declaration(run_set, crit.SCREEN_START)
        check_declaration(declared, run_set, crit.SCREEN_START)
        for case in CASES:
            found = pair[run]["cases"][case]
            held = path_break_positions(frames[run], {"cw": found["cw"]["weights"], "tilt": found["tilt"]["weights"]},
                                        exits, months, end)
            if not set(blank_set(held)) <= set(declared):
                raise refuse("path_break_undeclared", f"{FAMILY_A_SET} screen {run} {case}")
            check_months(found["tilt"]["monthly_net"], found["cw"]["monthly_net"])
            record = crit.screen_record(without(found["tilt"]["monthly_net"], declared),
                                        without(found["cw"]["monthly_net"], declared),
                                        found["tilt"]["annual_turnover"], declared)
            vs_vw = mean_gap(found["tilt"]["monthly_net"], vw.reindex(months), declared)
            for call, name, output in (("screen_record", "tilt_vs_cw", record), ("check_paired", "tilt_vs_vwretd", vs_vw)):
                entries.append({"stage": "confirm", "call": call, "series": name, "set": FAMILY_A_SET, "run": run,
                                "case": case, "span": span, "declaration": declared, "output": output})
            out["records"][run][case] = {"screen_record": record, "tilt_vs_vwretd": vs_vw,
                                         "r4": {book: r4_counts(found[book], frames[run]["disappearances"], end, run)
                                                for book in tilt.BOOKS}}
            means[run][case] = {"tilt_vs_cw": record["annual_active_mean"], "tilt_vs_vwretd": vs_vw["annual_mean_gap"]}
    out["counts"] = {run: rebalance_counts(pair[run]["rebalances"]) for run in RUNS}
    out["fragility"] = {case: fragility(means["primary"][case], means["last_close"][case]) for case in CASES}
    return out


def confirm_stage(data: w.WrdsData, quotes: w.WrdsData, trial: Mapping[str, Any], out: Path,
                  payloads: Mapping[str, dict], digests: Mapping[str, str]) -> dict[str, Any]:
    """Test A over 1993-02 to 2014-03, the secondary family, OI-09, and the Family A baseline over the screen months.

    The decision calls follow ``primary_decision``: ``verify_frozen_screen`` (``open_gate``), ``composite_test`` on
    the primary run at 1x, ``composite_means`` at 2x, ``holm_primary(p_A, p_B = 1.0)``, ``stop_after_confirm``. The
    same calls run on the last_close run for R4. ``decide_a`` needs the check means and runs in the check stage.
    """
    record, digest, test_b = open_gate(trial, payloads, digests)
    entries: list = [{"stage": "confirm", "call": "verify_frozen_screen", "expected_digest": digest, "output": True}]
    exits = exit_map(data)
    publication = next(o for o in trial["open_items"] if o["id"] == "OI-08")["publication_years"]
    segment = segment_plan(w.calendar(data))["confirm"]
    found = run_segment(data, quote_table(quotes, data), segment, record["shortlist"], exits, publication,
                        unseen_cells(data))
    series, declared = found["series"], found["declared"]
    spy = monthly_spy(data, segment)
    span = [segment["first"], segment["last"]]
    tests: dict[str, dict] = {run: {} for run in RUNS}
    for run in RUNS:
        for case in CASES:
            tests[run][case] = crit.composite_test(*three(series[COMPOSITE][run][case], spy, declared[run]),
                                                   declared[run])
            entries.append({"stage": "confirm", "call": "composite_test", "set": COMPOSITE, "run": run, "case": case,
                            "span": span, "declaration": declared[run], "output": tests[run][case]})
    means = set_means(series, spy, declared, "confirm", entries, "confirm", span)
    decision = {}
    for run in RUNS:
        a, a_2x = tests[run]["primary"], means[COMPOSITE][run]["sensitivity_2x"]
        holm = crit.holm_primary(a["p_a"], test_b["p_b"])
        decision[run] = {"p_a": a["p_a"], "p_b": test_b["p_b"], "holm": holm,
                         "holm_p_at_most_alpha": holm["A"] <= crit.ALPHA,
                         "confirm_means": {"vs_spy": a["vs_spy"]["annual_mean"], "vs_cw": a["vs_cw"]["annual_mean"]},
                         "cost_2x_means": {"vs_spy": a_2x["vs_spy"], "vs_cw": a_2x["vs_cw"]},
                         "stop": crit.stop_after_confirm(a["vs_spy"]["annual_mean"])}
        entries.append({"stage": "confirm", "call": "holm_primary", "run": run, "output": holm})
        entries.append({"stage": "confirm", "call": "stop_after_confirm", "run": run, "output": decision[run]["stop"]})
    family_size = trial["secondary_family"]["family_size"]
    result = {"header": header(trial), "digest_sha256": digest, "shortlist": record["shortlist"],
              "segment": found["result"],
              "test_a": {"decision": decision["primary"], "last_close": decision["last_close"], "records": tests},
              "means": means, "fragility": set_fragility(means),
              "secondary": secondary(record, digest, series, spy, declared, family_size, entries, span),
              "oi09": oi09(series, spy, declared, means, "confirm", segment["last"], entries, "confirm", span),
              "family_a_screen": baseline_screen(data, payloads["look"]["result"], exits, entries),
              **member_day_report(data, [segment], exits)}
    for entry in entries:                   # after every check of the stage that can refuse (AUDIT_2 ADV-2)
        log(out, entry)
    return result


def check_stage(data: w.WrdsData, quotes: w.WrdsData, trial: Mapping[str, Any], out: Path,
                payloads: Mapping[str, dict], digests: Mapping[str, str]) -> dict[str, Any]:
    """The check means and the test A label over 2014-04 to ``check_period_end``, ``CHECK_GAP_MONTHS`` left out.

    Each series joins the pre-seal and post-seal segments, and the declaration joins their blank sets
    (``P1_path_break``). ``decide_a`` takes the Holm p_A and the confirm and 2x means of the confirm stage. The
    check runs after a confirm stop. A secondary member reports its check means only (``composite_test`` is a
    confirm-period statistic).
    """
    record, digest, _ = open_gate(trial, payloads, digests)
    entries: list = [{"stage": "check", "call": "verify_frozen_screen", "expected_digest": digest, "output": True}]
    confirm = payloads["confirm"]["result"]
    exits = exit_map(data)
    publication = next(o for o in trial["open_items"] if o["id"] == "OI-08")["publication_years"]
    cal = w.calendar(data)
    plan = segment_plan(cal)
    table, unseen = quote_table(quotes, data), unseen_cells(data)
    names = ("check_pre_seal", "check_post_seal")
    parts = {n: run_segment(data, table, plan[n], record["shortlist"], exits, publication, unseen) for n in names}
    last = plan["check_post_seal"]["last"]
    span = [crit.CHECK_START, last]
    spy = pd.concat([monthly_spy(data, plan[n]) for n in names])
    declared = {run: {**parts[names[0]]["declared"][run], **parts[names[1]]["declared"][run]} for run in RUNS}
    series: dict[str, dict] = {}
    for name in parts[names[0]]["series"]:
        series[name] = {run: {case: {book: pd.concat([parts[n]["series"][name][run][case][book] for n in names])
                                     for book in ("tilt", "cw")} for case in CASES} for run in RUNS}
        for run in RUNS:
            for case in CASES:
                check_months(*series[name][run][case].values(), spy, last=last, period="check")
    means = set_means(series, spy, declared, "check", entries, "check", span)
    labels = {}
    for run in RUNS:
        before = confirm["test_a"]["decision"] if run == "primary" else confirm["test_a"]["last_close"]
        labels[run] = crit.decide_a(before["holm"]["A"], before["confirm_means"], before["cost_2x_means"],
                                    means[COMPOSITE][run]["primary"])
        entries.append({"stage": "check", "call": "decide_a", "run": run, "declaration": declared[run],
                        "output": labels[run]})
    check_fragility = set_fragility(means)
    fragile = any(v["fragile"] for stage_ in (confirm["fragility"][COMPOSITE], check_fragility[COMPOSITE])
                  for case in CASES for v in stage_[case].values())
    gap = {str(m): part for part, first, end in GAP_PARTS for m in pd.period_range(first, end, freq="M")}
    if list(gap) != [str(m) for m in crit.CHECK_GAP_MONTHS]:
        raise refuse("check_gap_invalid", "the gap parts do not cover CHECK_GAP_MONTHS")
    post = parts["check_post_seal"]
    first_post = cal[cal >= sig.SEAL[1]][0]
    result = {"header": header(trial), "digest_sha256": digest, "check_period_end": last,
              "check_gap_months": gap, "segments": {n: parts[n]["result"] for n in names},
              "series_months": {"first": spy.index[0], "last": spy.index[-1], "count": len(spy),
                                "gap_months_in_series": int(spy.index.isin(crit.CHECK_GAP_MONTHS).sum())},
              "test_a": {"label": labels["primary"], "last_close": labels["last_close"], "fragile": fragile,
                         "confirm_stop": confirm["test_a"]["decision"]["stop"]},
              "means": means, "fragility": check_fragility,
              "oi09": oi09(series, spy, declared, means, "check", last, entries, "check", span),
              "s2_history_rule": {
                  "split_in_basis_window_by_year": {**parts[names[0]]["result"]["s2_split_in_basis_window_by_year"],
                                                    **post["result"]["s2_split_in_basis_window_by_year"]},
                  "basis_quarters_by_year": {**parts[names[0]]["result"]["s2_basis_quarters_by_year"],
                                             **post["result"]["s2_basis_quarters_by_year"]},
                  "seal_quarters_by_year": s2_seal_quarters(post["inputs"], first_post, plan["check_post_seal"]["end"]),
                  "valid_share_by_post_seal_month": post["result"]["s2_valid_share_by_month"]},
              **member_day_report(data, [plan[n] for n in names], exits)}
    for entry in entries:
        log(out, entry)
    return result


def run_stage(stage: str, data: w.WrdsData, out: Path, tracked: Mapping[str, Any] | None = None,
              repo: Path = REPO, quotes: w.WrdsData | None = None,
              tracked_quotes: Mapping[str, Any] | None = None) -> str:
    """Run one stage after its gates; return the stage digest. A refusal is appended to the run log.

    Every stage needs the quote copy of the second pull (``quote_files``), and the tracked quote manifest is
    ``QUOTE_MANIFEST`` unless ``tracked_quotes`` is given. Both data digests enter ``data_files_sha256``.
    """
    if stage not in STAGES:
        raise refuse("stage_invalid", stage)
    out = check_out(out)
    trial, trial_sha = load_trial(repo)
    tracked = json.loads((repo / TRACKED_MANIFEST).read_text()) if tracked is None else tracked
    if quotes is None:
        raise refuse("quotes_missing", "every stage needs the quote copy of the second pull")
    if tracked_quotes is None:
        if not (repo / QUOTE_MANIFEST).is_file():
            raise refuse("quote_manifest_missing", QUOTE_MANIFEST)
        tracked_quotes = json.loads((repo / QUOTE_MANIFEST).read_text())
    data_sha = sha256_bytes(json.dumps({"wrds": check_data(data, tracked, trial),
                                        "quotes": check_quotes(quotes, tracked_quotes, trial)}, sort_keys=True).encode())
    ctx = context(trial, trial_sha, data_sha, repo)
    try:
        payloads, digests = earlier(out, stage, ctx)
        if "calibration" in payloads:
            check_calibration(payloads["calibration"]["result"])
        if (out / f"{stage}.json").exists() or (out / f"{stage}.sha256").exists():
            raise refuse("stage_output_exists", stage)
        if stage == "coverage":
            result = coverage_stage(data, trial)
        elif stage == "calibration":
            result = calibration_stage(data, trial)
        elif stage == "look":
            result = look_stage(data, trial, out)
        elif stage == "screen":
            result = screen_stage(data, trial, out, payloads["coverage"]["result"], payloads["look"]["result"])
        elif stage == "freeze":
            result = freeze_stage(payloads["screen"], out)
        elif stage == "confirm":
            result = confirm_stage(data, quotes, trial, out, payloads, digests)
        else:
            result = check_stage(data, quotes, trial, out, payloads, digests)
        if "calibration" in payloads:
            result = {**result, "test_b": record_test_b(payloads["calibration"]["result"], digests["calibration"])}
        digest = write_stage(out, stage, ctx, digests, result)
    except tilt.runner.RunnerStop as exc:
        log(out, {"stage": stage, "refused": exc.reason, "detail": masked(exc.detail)})
        raise
    except Exception as exc:
        log(out, {"stage": stage, "error": type(exc).__name__, "detail": masked(str(exc))})
        raise
    log(out, {"stage": stage, "written": digest})
    if stage == "freeze":
        (out / "shortlist_digest.txt").write_text(result["digest_sha256"] + "\n")
    return digest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one stage of the frozen M5.5 trial file (aggregates only).")
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--quote-root", type=Path, required=True, help="the wrds_quotes_* folder of the second pull")
    parser.add_argument("--out", type=Path, required=True, help="a folder outside every Git checkout")
    parser.add_argument("--stage", choices=STAGES, required=True)
    args = parser.parse_args()
    digest = run_stage(args.stage, stage_data(args.stage, args.data_root), args.out,
                       quotes=quote_files(args.quote_root, read=args.stage in QUOTE_STAGES))
    print(f"{args.stage} written, sha256 {digest}")


if __name__ == "__main__":
    main()
