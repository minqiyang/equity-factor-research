"""Milestone 5.5: the public screen report of trial family v1 from the private stage files of run 1 and run 2.

The script reads the stage files that ``research/m55_driver.py`` wrote for run 1 (coverage and calibration, then the
coverage stop) and run 2 (all five stages), checks them, and writes three public files with aggregates only:

- ``reports/m55_screen_v1.json``: every aggregate of the report;
- ``reports/m55_screen_v1.md``: the same aggregates in plain tables;
- ``reports/m55_screen_v1_attempts.jsonl``: one line per run (R9).

Checks (each refuses with a non-zero exit, and no file is written): each ``<stage>.sha256`` file matches its stage
file; the stage files of one run share one context and each names the digests of the stages before it; run 2 was
made from the frozen trial file; both runs were made from the data of ``reports/wrds_manifest_2025.json``; the test B
record of each later stage equals ``m55_driver.record_test_b``; and the shortlist digest that
``m55_criteria.freeze_shortlist`` recomputes from the screen records equals the freeze file and
``shortlist_digest.txt``. The script computes no new statistic.

Privacy (owner grant O-22, R11): the stage files hold per-position rows (path-break positions, blanked level
windows, and B2 rows, each with a date or a weight). The report gives only their aggregates. The public weight rule
(coordinator, 2026-10-08, REVIEW M-1) also applies: a weight is published only as a sum over at least 3 positions, and
no two published sums may differ by fewer than 3 positions. So the report gives weight sums only for the run-level
look groups, no weight for a screen candidate group (each nests in the look group), and no single maximum weight.
The report holds no private path: the stage folders are command-line arguments, and the report names them only as
``m55_screen_v1`` and ``m55_screen_v2``. The output is the same bytes on each run.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import re
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from research import m55_criteria as crit
from research import m55_driver as d
from research import m55_wrds_loader as w
from research.m4_7_sp500_pit_rerun import RunnerStop
from research.m55_index_tilt import LOWRISK_TARGET_RATIO, LOWRISK_UNDEFINED_MAX, ME_REASONS, refuse


REPORT_JSON = "m55_screen_v1.json"
REPORT_MD = "m55_screen_v1.md"
ATTEMPTS_JSONL = "m55_screen_v1_attempts.jsonl"
RUNS = d.RUNS                                   # loader runs: ("primary", "last_close")
CASES = d.CASES                                 # cost cases: ("primary", "sensitivity_2x")
EXITS = w.EXIT_CLASSES
DECISION_CELL = ("primary", "primary")          # the freeze reads only the primary loader run with primary costs
# The run facts that the stage files do not hold: the folder name, the date, and the code commit of each run.
RUN_FACTS = (
    {"run": 1, "folder": "m55_screen_v1", "date": "2026-10-07",
     "code_commit": "ebc97054301dda53e0193d59f8003d3fa904867d", "trial": "trial family v1 with amendment 1",
     "stages": ("coverage", "calibration")},
    {"run": 2, "folder": "m55_screen_v2", "date": "2026-10-08",
     "code_commit": "8590b2e9ca11513cf9f5aa2c552e1d6a9f6d3925", "trial": "trial family v1 with amendments 1 and 2",
     "stages": d.STAGES},
)
RUN_1_GATE = 'GO_ON = ("chosen",)'               # the calibration gate of the run 1 code
# Per-position rows of the stage files (each with a date or a weight), per-month blank declarations, and single
# maximum weights: the report keeps their aggregates only. FORBIDDEN and SINGLE_MAX are the output guard.
SINGLE_MAX = frozenset({"incoming_weight_max", "max_cw_share"})
DROP = frozenset({"positions", "path_break_positions", "each", "blank_months"}) | SINGLE_MAX
FORBIDDEN = frozenset({"positions", "path_break_positions", "each", "break_row", "break_rows", "previous_valid_row",
                       "weight_at_last_rebalance"})
# The public weight rule (coordinator, 2026-10-08): no weight in a screen candidate group, and a weight sum covers at
# least MIN_POSITIONS positions and differs from each other published sum by 0 or at least MIN_POSITIONS positions.
GROUP_WEIGHTS = frozenset({"weight_at_last_rebalance_sum", "incoming_weight_sum", "weight_sum"})
MIN_POSITIONS = 3
WEIGHT_RULE = "private per O-22 (public weight rule, 2026-10-08)"
# Split so this file holds no literal private path (the governance path test reads tracked files).
PRIVATE_TEXT = re.compile("|".join((r"(?:/Users|/home)/", "private_data" + "/", "efr_local" + "_data")))


# Checks -----------------------------------------------------------------------------------

def check_run(folder: Path, stages: tuple[str, ...]) -> tuple[dict[str, dict], dict[str, str]]:
    """Read the stage files of one run with ``m55_driver.read_stage``: each must match its ``.sha256`` file and the
    context of the coverage file, and name the digests of the stages before it. No later stage file may exist."""
    folder = Path(folder)
    if not (folder / "coverage.json").is_file():
        raise refuse("stage_missing", "coverage")
    ctx = json.loads((folder / "coverage.json").read_bytes())["context"]
    payloads, digests = {}, {}
    for name in stages:
        payloads[name], digests[name] = d.read_stage(folder, name, ctx)
        if payloads[name]["previous"] != {k: digests[k] for k in d.STAGES[:d.STAGES.index(name)]}:
            raise refuse("stage_chain_mismatch", f"{name} was not built on the earlier stages of its run")
    for later in d.STAGES[len(stages):]:
        if (folder / f"{later}.json").exists() or (folder / f"{later}.sha256").exists():
            raise refuse("stage_unexpected", later)
    return payloads, digests


def check_freeze(run: Mapping[str, dict], folder: Path) -> dict[str, Any]:
    """Recompute the shortlist record from the screen records; refuse unless its digest equals the freeze file and
    ``shortlist_digest.txt``, and ``verify_frozen_screen`` accepts the saved record."""
    frozen = crit.freeze_shortlist(run["screen"]["result"]["records_for_freeze"])
    saved = run["freeze"]["result"]
    text = folder / "shortlist_digest.txt"
    kept = text.read_text().strip() if text.is_file() else None
    if not (frozen["digest_sha256"] == saved["digest_sha256"] == saved["record"]["digest_sha256"] == kept
            and frozen["shortlist"] == saved["shortlist"] and frozen["decision"] == saved["decision"]):
        raise refuse("shortlist_digest_mismatch", "the recomputed shortlist record differs from the freeze file")
    crit.verify_frozen_screen(saved["record"], frozen["digest_sha256"])
    return frozen


def check_output(doc: Mapping[str, Any], texts: Mapping[str, str]) -> None:
    """The output guard: no per-position key and no single maximum weight in the document, no weight in a screen
    candidate group, and no private path in any output text."""
    def keys(value: Any) -> set:
        if isinstance(value, Mapping):
            return set(value) | set().union(*(keys(v) for v in value.values()))
        if isinstance(value, list):
            return set().union(*(keys(v) for v in value))
        return set()
    groups = [doc["screen"]["candidates"], *(part["screen"] for part in doc["reports_owed"].values()
                                              if isinstance(part, Mapping) and "screen" in part)]
    found = keys(doc) & (FORBIDDEN | SINGLE_MAX) | keys(groups) & GROUP_WEIGHTS
    if found:
        raise refuse("private_field_in_output", ", ".join(sorted(found)))
    if any(PRIVATE_TEXT.search(text) for text in texts.values()):
        raise refuse("private_path_in_output", "an output text holds a private path")


# Aggregates -------------------------------------------------------------------------------

def aggregate(value: Any, drop: frozenset = DROP) -> Any:
    """A stage subtree without per-position rows, per-month blank declarations, and single maximum weights
    (``DROP``), and without the other keys of ``drop``."""
    if isinstance(value, Mapping):
        return {k: aggregate(v, drop) for k, v in value.items() if k not in drop}
    if isinstance(value, list):
        return [aggregate(v, drop) for v in value]
    return value


def path_break(positions: list[Mapping[str, Any]], books: tuple[str, ...] = ()) -> dict[str, Any]:
    """Count, months, count by later exit class, the span in months (min, median, max), and the weight sum of each
    book in ``books`` (the run-level look set only, by the public weight rule)."""
    spans = [len(p["months"]) for p in positions]
    out = {"position_count": len(positions),
           "months": len({m for p in positions for m in p["months"]}),
           "by_exit_class": d.per_class(Counter(p["exit_class"] for p in positions)),
           "span_months": {"min": min(spans), "median": statistics.median(spans), "max": max(spans)}
           if spans else None}
    if books:
        out["weight_sum"] = {b: sum(p["weight_at_last_rebalance"][b] for p in positions) for b in books}
    return out


def weight_rule(groups: Mapping[tuple[str, str], Mapping[str, int]]) -> bool:
    """The public weight rule on look R4 groups keyed by (loader run, cost case), each given as held counts by cause.

    Each group must cover at least MIN_POSITIONS events, and two groups must hold the same events or differ by at
    least MIN_POSITIONS events. The causes split the events, so two groups differ by at least the sum of their count
    differences. The cost cases of one loader run read one disappearance table and one CW-PIT target, so equal counts
    there are the same events. The stage files hold no event identity, so two loader runs with equal counts fail.
    """
    if any(sum(g.values()) < MIN_POSITIONS for g in groups.values()):
        return False
    for a, b in itertools.combinations(groups, 2):
        apart = sum(abs(groups[a][c] - groups[b][c]) for c in groups[a])
        if not (apart >= MIN_POSITIONS or (a[0] == b[0] and apart == 0)):
            return False
    return True


def look_r4(parts: Mapping[str, Mapping[str, Any]]) -> tuple[dict[str, Any], str]:
    """The look R4 groups under the public weight rule, and the level of the weight sums it allows.

    ``by_cause``: the weight sum of each cause and their total; ``total``: the total over causes only; ``none``: no
    weight sum. The engine total at the event (``incoming_weight_sum``) covers the same events as the total.
    """
    groups = {run: {case: aggregate(parts[run][case]["r4"]) for case in CASES} for run in RUNS}
    flat = {(run, case): groups[run][case] for run in RUNS for case in CASES}
    causes = list(flat[DECISION_CELL]["by_cause"])
    held = {k: {c: g["by_cause"][c]["held"] for c in causes} for k, g in flat.items()}
    by_cause = all(weight_rule({k: {c: h[c]} for k, h in held.items()}) for c in causes)
    total = weight_rule(held)
    for g in flat.values():
        sums = [g["by_cause"][c]["weight_at_last_rebalance_sum"] for c in causes]
        if total:
            g["weight_at_last_rebalance_sum"] = math.fsum(sums)
        else:
            g.pop("incoming_weight_sum")
        if not by_cause:
            for c in causes:
                g["by_cause"][c].pop("weight_at_last_rebalance_sum")
    return groups, "by_cause" if by_cause else "total" if total else "none"


def by_year(months: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(m[:4] for m in months).items()))


def meets(record: Mapping[str, Any]) -> bool:
    """The frozen O-21 rule on one record; an undefined record fails."""
    return record["status"] == "ok" and record["information_ratio"] >= crit.IR_MIN and record["hac_t"] >= crit.T_MIN


def candidate(item: Mapping[str, Any], coverage: Mapping[str, Any], shortlisted: bool) -> dict[str, Any]:
    """One screen candidate: its span, months with values, and each cell's records (aggregates only)."""
    cells = {run: {case: aggregate(item["records"][run][case]) for case in CASES} for run in RUNS}
    for run in RUNS:
        for case in CASES:
            cells[run][case].pop("tilt_stats", None)
            cells[run][case].pop("r4", None)
            cells[run][case]["meets_rule"] = meets(cells[run][case]["screen_record"])
    record = item["records"][DECISION_CELL[0]][DECISION_CELL[1]]["screen_record"]
    blank = {run: len(item["records"][run]["primary"]["screen_record"].get("blank_months", {})) for run in RUNS}
    return {"real_start": item["real_start"], "first_month": item["first_month"],
            "screen_months_before_blanks": coverage["screen_months_before_blanks"],
            "months_with_values": item["months_with_values"], "blank_months": blank,
            "undefined_reason": record.get("undefined_reason"), "cells": cells,
            "shortlisted": shortlisted}


def build(run_1: Path, run_2: Path, repo: Path = d.REPO) -> dict[str, Any]:
    """Check both runs and return the report document (aggregates only)."""
    trial, trial_sha = d.load_trial(repo)
    tracked = json.loads((repo / d.TRACKED_MANIFEST).read_text())
    data_sha = d.check_data(w.WrdsData({}, tracked), tracked, trial)    # the files digest of the tracked manifest
    first, digests_1 = check_run(Path(run_1), RUN_FACTS[0]["stages"])
    second, digests_2 = check_run(Path(run_2), RUN_FACTS[1]["stages"])
    ctx_1, ctx_2 = first["coverage"]["context"], second["coverage"]["context"]
    if ctx_2["trial_sha256"] != trial_sha:
        raise refuse("trial_mismatch", "run 2 was not made from the frozen trial file")
    if not ctx_1["data_files_sha256"] == ctx_2["data_files_sha256"] == data_sha:
        raise refuse("data_manifest_mismatch", "a run was not made from the tracked manifest's data")
    calibration = second["calibration"]["result"]
    test_b = d.record_test_b(calibration, digests_2["calibration"])
    if any(second[s]["result"].get("test_b") != test_b for s in ("look", "screen", "freeze")):
        raise refuse("test_b_mismatch", "a later stage does not record test B as the calibration gives it")
    frozen = check_freeze(second, Path(run_2))

    coverage, look, screen = (second[s]["result"] for s in ("coverage", "look", "screen"))
    after_stop = trial["primary_family"]["test_B"]["after_coverage_stop"]
    reuse = next(i for i in trial["prior_exposures"]["items"] if i.startswith("M5 step 2"))
    runs = []
    for facts, payloads, digests in ((RUN_FACTS[0], first, digests_1), (RUN_FACTS[1], second, digests_2)):
        ctx = payloads["coverage"]["context"]
        entry = {"run": facts["run"], "folder": facts["folder"], "date": facts["date"],
                 "code_commit": facts["code_commit"], "trial": facts["trial"], "trial_sha256": ctx["trial_sha256"],
                 "code_sha256": ctx["code_sha256"], "code_pins_sha256": ctx["code_pins_sha256"],
                 "data_files_sha256": ctx["data_files_sha256"], "stage_sha256": digests,
                 "calibration_decision": payloads["calibration"]["result"]["decision"]}
        if facts["run"] == 1:
            entry.update(status="stopped", stop="coverage_stop",
                         reason=f"calibration decision {entry['calibration_decision']}; the gate {RUN_1_GATE} of "
                                f"this code stops the sequence before the look; no return of any kind was computed",
                         calibration_sha256_in_trial=digests["calibration"] in after_stop)
        else:
            entry.update(status="completed", freeze_decision=frozen["decision"], shortlist=frozen["shortlist"],
                         shortlist_digest_sha256=frozen["digest_sha256"])
        runs.append(entry)

    parts = {run: look["runs"][run] for run in RUNS}
    look_doc = {"screen_months": len(pd.period_range(crit.SCREEN_START, crit.SCREEN_END, freq="M")),
                "same_blank_set_in_both_runs": parts["primary"]["blank_months"] == parts["last_close"]["blank_months"],
                "runs": {run: {"blank_month_count": part["blank_month_count"],
                               "blank_month_share": part["blank_month_share"],
                               "blank_months": part["blank_months"],
                               "blank_months_by_year": by_year(part["blank_months"]),
                               "cases": {case: {"cw_vs_vwretd": aggregate(part[case]["cw_vs_vwretd"]),
                                                "cw_annual_turnover": part[case]["cw_annual_turnover"],
                                                "cw_annual_cost_drag": part[case]["cw_annual_cost_drag"]}
                                         for case in CASES}}
                         for run, part in parts.items()}}
    ids = sorted(screen["candidates"])
    items = screen["candidates"]
    cand = {s: candidate(items[s], coverage["signals"][s], frozen["candidates"][s]["shortlisted"]) for s in ids}
    ran = [s for s in ids if "counts" in items[s]]                     # candidates with an engine call
    r4_look, r4_level = look_r4(parts)
    owed = {
        "r4": {"look": r4_look, "look_weight_level": r4_level,
               "screen": {s: {run: {case: aggregate(items[s]["records"][run][case]["r4"], DROP | GROUP_WEIGHTS)
                                    for case in CASES} for run in RUNS} for s in ran}},
        "fragility": {"look": aggregate(look["fragility"]), "screen": {s: aggregate(items[s]["fragility"])
                                                                       for s in ids}},
        "r6": {"signal_reason_shares_by_exit_class": {s: coverage["signals"][s]["reason_share_by_exit_class"]
                                                      for s in ids},
               "member_day_census": coverage["missingness_census"],
               "screen_census": screen["r6"],
               "c_zero_by_exit_class": {s: items[s]["c_zero_by_exit_class"] for s in ran}},
        "me_coverage": {**coverage["me_coverage"], "s7_early": coverage["s7_early"]},
        "s2_short_history": coverage["signals"]["S2"]["short_history_size"] if "S2" in ids else None,
        "s2_history_rule": None if "S2" not in ids else {
            "split_in_basis_window_cells_by_year": {
                y: r["split_in_basis_window"] for y, r in coverage["signals"]["S2"]["reason_counts_by_year"].items()
                if "split_in_basis_window" in r},
            "basis_quarters_by_year": coverage["signals"]["S2"]["basis_quarters_by_year"]},
        "path_break": {"look": {run: path_break(parts[run]["positions"], ("cw",)) for run in RUNS},
                       "screen": {s: {run: path_break(items[s]["path_break_positions"][run]) for run in RUNS}
                                  for s in ran},
                       "blanked_level_windows": {run: aggregate(parts[run]["blanked_level_windows"]) for run in RUNS}},
        "b2": {"look": {run: aggregate(parts[run]["coverage"]["b2"]) for run in RUNS},
               "screen": {s: {run: aggregate(items[s]["counts"][run]["b2"]) for run in RUNS} for s in ran}},
        "counts": {"look": {run: aggregate(parts[run]["coverage"]) for run in RUNS},
                   "screen": {s: {run: aggregate(items[s]["counts"][run]) for run in RUNS} for s in ran}},
        "tilt_stats": {s: {run: {case: {k: v for k, v in items[s]["records"][run][case]["tilt_stats"].items()
                                        if k != "post_publication"} for case in CASES} for run in RUNS} for s in ran},
        "post_publication_split": {s: {run: {case: items[s]["records"][run][case]["tilt_stats"]["post_publication"]
                                             for case in CASES} for run in RUNS} for s in ran},
        "labels": {"rule": coverage["header"]["labels"], "run_label": coverage["header"]["run_label"],
                   "factor_level_reuse": reuse},
        "bid_ask_midpoint_share": coverage["bid_ask_share"],
        "low_risk_r6": {k: calibration[k] for k in ("ratio_status_counts", "gap_rebalances", "ratio_gap_members",
                                                    "max_ratio_gap_cw_share", "r6_by_exit_class")},
        "check_period_end": {"status": "owed_by_confirm_stage", "reason": trial["reports_owed"]["check_period_end"]},
        "check_gap_months": {"status": "owed_by_confirm_stage", "reason": trial["reports_owed"]["check_gap_months"]},
    }
    missing = {"s2_history_rule": "The confirm stage owes the post-seal parts, because the screen stages do not open "
                                  "the check period. These are the member quarters with rdq before 2020-08-03 and a "
                                  "known date on or after it, and the S2 valid share in the post-seal check months.",
               "path_break": "The trial asks for each held position with its weight in each book. The report gives "
                             "aggregates only (owner data terms O-22). The rows stay in the private stage files.",
               "b2": "The trial asks for unknown_event_excluded and unknown_event_cw_share at each rebalance. The "
                     "report gives aggregates only (owner data terms O-22). The rows stay in the private stage files."}
    dropped = {"r4.look.incoming_weight_max": "The largest book weight at one event.",
               "r4.screen.weight_at_last_rebalance_sum": "The weight share by cause of each candidate group, CW and "
                                                         "TILT. Each group nests in the look group, so a difference "
                                                         "can isolate one event.",
               "r4.screen.incoming_weight_sum": "The engine total weight at the event of each candidate group, CW "
                                                "and TILT.",
               "r4.screen.incoming_weight_max": "The largest book weight at one event in each candidate group.",
               "b2.max_cw_share": "The largest CW share excluded at one rebalance, for the look and each candidate.",
               "counts.b2.max_cw_share": "The same B2 maximum in the counts of the look and each candidate.",
               "path_break.screen.weight_sum": "The weight sum of each candidate group, CW and TILT. The run-level "
                                               "look sum stays."}
    if r4_level != "by_cause":
        dropped["r4.look.by_cause.weight_at_last_rebalance_sum"] = (
            "The weight share of each cause in the look groups. At least one cause does not meet the rule. Two loader "
            "runs with equal counts of a cause fail it, because the stage files hold no event identity to show that "
            "the events are the same.")
    if r4_level == "none":
        dropped["r4.look.weight_at_last_rebalance_sum"] = "The look total over causes. The totals do not meet the rule."
        dropped["r4.look.incoming_weight_sum"] = ("The engine total weight at the event in the look groups. It "
                                                  "covers the same events as the total.")
    missing.update({k: f"{v} The report does not give it: {WEIGHT_RULE}. The value stays in the private stage "
                       "files." for k, v in sorted(dropped.items())})
    doc = {
        "report": "m55_screen_v1",
        "header": {**coverage["header"], "factor_level_reuse": reuse},
        "provenance": {"trial_file": d.TRIAL_FILE, "trial_sha256": trial_sha, "data_manifest": d.TRACKED_MANIFEST,
                       "vintage": tracked["vintage"], "data_files_sha256": data_sha,
                       "shortlist_digest_sha256": frozen["digest_sha256"]},
        "runs": runs,
        "calibration": {"result_equal_to_run_1": first["calibration"]["result"] == calibration,
                        "coverage_equal_to_run_1": first["coverage"]["result"] == coverage,
                        "target_ratio": LOWRISK_TARGET_RATIO, "undefined_max": LOWRISK_UNDEFINED_MAX,
                        **{k: v for k, v in calibration.items() if k != "header"}},
        "test_b": {**test_b, "holm_alpha": crit.ALPHA,
                   # Holm over two tests: with p_B = 1.0, test A's adjusted p is 2 x p_A, so it needs p_A <= ALPHA / 2.
                   "p_a_max_for_holm": crit.ALPHA / 2 if test_b["stopped"] else None},
        "coverage": {s: {k: coverage["signals"][s][k] for k in ("real_start", "first_month",
                                                                 "screen_months_before_blanks", "valid_share_by_year",
                                                                 "min_month_valid_share_by_year",
                                                                 "reason_counts_by_year")} for s in ids},
        "look": look_doc,
        "screen": {"decision_cell": {"loader_run": DECISION_CELL[0], "cost_case": DECISION_CELL[1]},
                   "rule": dict(crit.SHORTLIST_RULE), "min_months": crit.SCREEN_MIN_MONTHS,
                   "q_values": {"stage": "confirm", "method": "Benjamini-Yekutieli",
                                "family_size": trial["secondary_family"]["family_size"]},
                   "cost_schedule": [list(row) for row in crit.SCREEN_COST_SCHEDULE      # rows that start in the screen
                                     if row[0] is None or row[0] < str(crit.SCREEN_END + 1)],
                   "candidates": cand},
        "freeze": {"decision": frozen["decision"], "shortlist": frozen["shortlist"], "rule": frozen["rule"],
                   "digest_sha256": frozen["digest_sha256"], "recomputed_from_screen_records": True,
                   "test_b": test_b},
        "reports_owed": owed,
        "missing": missing,
    }
    doc["limitations"] = limitations(doc)
    return doc


def limitations(doc: Mapping[str, Any]) -> list[str]:
    """The limitations, stated from the document's own numbers."""
    look, cand = doc["look"], doc["screen"]["candidates"]
    run = look["runs"]["primary"]
    pb = doc["reports_owed"]["path_break"]["look"]["primary"]
    cut = [f"{s} from {c['screen_months_before_blanks']} to {c['months_with_values']['primary']} months"
           for s, c in cand.items() if c["blank_months"]["primary"]]
    blank = (f"The path_break_held blank set removes {run['blank_month_count']} of {look['screen_months']} screen "
             f"months (share {run['blank_month_share']:.4f}). {pb['position_count']} held positions cause it, with a "
             f"CW-PIT weight sum of {pb['weight_sum']['cw']:.4f} at their last rebalance. The longest position "
             f"blanks {pb['span_months']['max'] if pb['span_months'] else 0} months."
             if run["blank_month_count"] else "No screen month is blank.")
    out = [blank + (" The blanks cut " + ", and ".join(cut) + "." if cut else "")]
    if run["blank_month_count"]:
        out.append("The coordinator ruled on 2026-10-08 that the blank is the frozen rule, correctly applied. Each "
                   "gap is a gap in CRSP itself: the pull takes every daily row of every PERMNO that was ever a "
                   "member, and the loader drops only off-calendar rows. The halt policy locks a held position with "
                   "no close, and R6 forbids a fill. Both books lose the same months, so the cut cannot favor a "
                   "candidate against CW-PIT. It lowers the power of the candidates that lose months. No fix and no "
                   "rerun follow, because a rule change after the result is a forking path (R9).")
    for s, c in cand.items():
        if not c["shortlisted"]:
            continue
        fails = [f"the {r} run with {k} costs (IR {c['cells'][r][k]['screen_record']['information_ratio']:.3f}, "
                 f"HAC t {c['cells'][r][k]['screen_record']['hac_t']:.3f})"
                 for r in RUNS for k in CASES if (r, k) != DECISION_CELL and not c["cells"][r][k]["meets_rule"]]
        if fails:
            out.append(f"{s} meets the frozen rule in the decision cell, but it fails the rule in "
                       + " and in ".join(fails) + ". These cells decide nothing.")
    short = [s for s, c in cand.items() if c["months_with_values"]["primary"] == doc["screen"]["min_months"]]
    if short:
        out.append(f"{' and '.join(short)} have {doc['screen']['min_months']} screen months with values, the "
                   "minimum of the rule.")
    out += [f"The run label is '{doc['header']['run_label']}'. {doc['header']['factor_level_reuse']}.",
            f"The sample is the point-in-time S&P 500 over the screen months {crit.SCREEN_START} to "
            f"{crit.SCREEN_END}. The confirm and check months are not opened.",
            "The screen p-values have no multiple-testing correction. The trial applies Benjamini-Yekutieli q-values "
            f"(family size {doc['screen']['q_values']['family_size']}) at the confirm stage, so this report gives no "
            "q-value. The candidate table is in ID order and is not a ranking.",
            "No result in this report is a profitability claim. Costs follow the screen cost schedule; the books are "
            "long only, so no borrow cost applies."]
    return out


# Markdown ---------------------------------------------------------------------------------

def pct(x: float | None, places: int = 2) -> str:
    return "none" if x is None else f"{100 * x:.{places}f}%"


def num(x: float | None, places: int = 3) -> str:
    return "none" if x is None else f"{x:.{places}f}"


def yes(flag: bool) -> str:
    return "yes" if flag else "no"


def table(head: list[str], rows: list[list[Any]]) -> list[str]:
    return ["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |",
            *("| " + " | ".join(str(c) for c in row) + " |" for row in rows), ""]


def by_class(label: str, values: Mapping[str, Any], fmt=str) -> list[Any]:
    return [label, *(fmt(values.get(c)) for c in EXITS)]


def render(doc: Mapping[str, Any]) -> str:
    """The Markdown report: the document's aggregates in plain tables, candidates in ID order."""
    head, prov, runs, cal, tb = doc["header"], doc["provenance"], doc["runs"], doc["calibration"], doc["test_b"]
    look, screen, freeze, owed = doc["look"], doc["screen"], doc["freeze"], doc["reports_owed"]
    cand = screen["candidates"]
    out = ["# Milestone 5.5 screen of trial family v1", "",
           f"Evidence ceiling: `{head['evidence_ceiling']}`. This is a simulated research diagnostic. It gives "
           "aggregates only and makes no profitability claim. The JSON file `reports/m55_screen_v1.json` holds every "
           "aggregate of this report.", "",
           f"- Run label: {head['run_label']}.",
           f"- Factor-level reuse (`reports_owed.labels`): {head['factor_level_reuse']}.",
           f"- Benchmark note: {head['vwretd']}.",
           f"- Low-risk label: {head['low_risk_label']}. Test B is stopped, so no low-risk return exists.", "",
           "## Result", "",
           f"- Freeze decision `{freeze['decision']}`. Shortlist: {', '.join(freeze['shortlist']) or 'none'}. "
           f"Digest `{freeze['digest_sha256']}`.",
           f"- The freeze reads only the {screen['decision_cell']['loader_run']} loader run with the "
           f"{screen['decision_cell']['cost_case']} cost case. The rule is IR >= {screen['rule']['ir_min']} and HAC "
           f"t >= {screen['rule']['t_min']} against CW-PIT, at most {screen['rule']['shortlist_cap']} candidates. "
           "The other three cells are reported and decide nothing.",
           f"- Test B is stopped (label `{tb['label']}`, p_B {tb['p_b']}). With p_B = {tb['p_b']}, test A needs "
           f"p_A <= {tb['p_a_max_for_holm']} for its Holm condition (alpha {tb['holm_alpha']}, two tests).",
           "- The candidate tables are in ID order and are not a ranking. The one-sided p-values have no "
           "multiple-testing correction; the trial applies Benjamini-Yekutieli q-values (family size "
           f"{screen['q_values']['family_size']}) at the confirm stage.", "",
           "## Limitations", "", *(f"- {line}" for line in doc["limitations"]), "",
           "## Provenance", ""]
    rows = [["Trial file", f"`{prov['trial_file']}`, SHA-256 `{prov['trial_sha256']}` (run 2)"],
            ["Data", f"`{prov['data_manifest']}` (vintage {prov['vintage']}), files SHA-256 "
                     f"`{prov['data_files_sha256']}` (both runs)"],
            ["Shortlist digest", f"`{prov['shortlist_digest_sha256']}`"]]
    for r in runs:
        rows.append([f"Run {r['run']} trial", f"{r['trial']}, SHA-256 `{r['trial_sha256']}`"])
        rows.append([f"Run {r['run']} code", f"commit `{r['code_commit']}`, code SHA-256 `{r['code_sha256']}`"])
        rows += [[f"Run {r['run']} {stage}.json", f"`{digest}`"] for stage, digest in r["stage_sha256"].items()]
    out += table(["Item", "Value"], rows)
    pins = runs[1]["code_pins_sha256"]
    out += ["Pinned files of run 2 (SHA-256):", "",
            *table(["File", "SHA-256"], [[f"`{p}`", f"`{v}`"] for p, v in sorted(pins.items())])]

    out += ["## Runs (R9)", "", "Each run of the trial family is listed. `reports/m55_screen_v1_attempts.jsonl` has "
            "one line per run.", ""]
    out += table(["Run", "Date", "Folder", "Trial", "Calibration decision", "Stages written", "Status"],
                 [[r["run"], r["date"], f"`{r['folder']}`", r["trial"], f"`{r['calibration_decision']}`",
                   ", ".join(r["stage_sha256"]), r["status"]] for r in runs])
    r1 = runs[0]
    out += [f"Run 1 stopped at the coverage stop. Reason: {r1['reason']}. The trial file names the run 1 "
            "calibration digest in `primary_family.test_B.after_coverage_stop`: "
            f"{yes(r1['calibration_sha256_in_trial'])}"
            ". Run 2 ran under amendment 2 and wrote all five stage files with no refusal.", ""]

    out += ["## Calibration and test B", "",
            f"The run 2 calibration result equals run 1 on every field: {yes(cal['result_equal_to_run_1'])}. The run "
            f"2 coverage result equals run 1 on every field: {yes(cal['coverage_equal_to_run_1'])}.", ""]
    status = cal["ratio_status_counts"]
    out += table(["Field", "Value"], [
        ["decision", f"`{cal['decision']}`"], ["rebalances", f"{cal['rebalances']} ({cal['start']} to {cal['end']})"],
        *([[f"`{k}`", v] for k, v in sorted(status.items())]),
        ["undefined share", f"{cal['undefined_share']:.4f} (limit {cal['undefined_max']:.2f})"],
        ["chosen g", "none" if cal["chosen_g"] is None else cal["chosen_g"]], ["target ratio", cal["target_ratio"]],
        ["window diagnostic undefined share", f"{cal['window_diag_undefined_share']:.4f}"],
        ["window decision", f"`{cal['window_decision']}`"],
        ["window diagnostic coverage high", yes(cal["window_diag_coverage_high"])],
        ["gap rebalances", cal["gap_rebalances"]], ["ratio gap members", cal["ratio_gap_members"]],
        ["max ratio_gap_cw_share", f"{cal['max_ratio_gap_cw_share']:.4f}"]])
    out += ["Grid (risk only, no return):", ""]
    out += table(["g", "Bracket", "Bracket, full windows", "Defined", "Undefined", "Median ratio", "Median hi",
                  "Median lo", "Share cap binds", "Share TE-scaled"],
                 [[row["g"], row["bracket"], row["bracket_full_windows"], row["defined"], row["undefined"],
                   num(row["median_vol_ratio"], 4), num(row["median_hi"], 4), num(row["median_lo"], 4),
                   num(row["share_cap_binds"], 4), num(row["share_te_scaled"], 4)] for row in cal["grid"]])
    out += [f"Test B record (the same in the look, screen, and freeze files): stopped {yes(tb['stopped'])}, label "
            f"`{tb['label']}`, p_B {tb['p_b']}, calibration decision `{tb['calibration_decision']}`, calibration "
            f"SHA-256 `{tb['calibration_sha256']}`.", ""]

    out += ["## Look: CW-PIT against vwretd", "",
            f"The look runs the engine with no signal, so TILT equals CW-PIT. Screen months: {look['screen_months']}. "
            "Mean gap is CW-PIT minus vwretd, annual, over the months with values.", ""]
    rows = []
    for run, part in look["runs"].items():
        for case, c in part["cases"].items():
            g = c["cw_vs_vwretd"]
            rows.append([run, case, g["months"], part["blank_month_count"], pct(g["book_annual_mean"]),
                         pct(g["benchmark_annual_mean"]), pct(g["annual_mean_gap"], 3), pct(g["annual_te"], 3),
                         num(g["correlation"], 5), num(c["cw_annual_turnover"], 4), pct(c["cw_annual_cost_drag"], 3)])
    out += table(["Loader run", "Cost case", "Months with values", "Blank months", "CW-PIT annual mean",
                  "vwretd annual mean", "Mean gap", "TE", "Correlation", "CW annual turnover", "CW cost drag"], rows)
    frag = owed["fragility"]["look"]
    out += ["R4 fragility of the look (sign flip of the mean gap between the loader runs): " + "; ".join(
        f"{case} {'fragile' if f['cw_vs_vwretd']['fragile'] else 'no sign flip'}" for case, f in frag.items()) + ".",
        "", f"Blank months, all with the reason `path_break_held`. The set is the same in both loader runs: "
        f"{yes(look['same_blank_set_in_both_runs'])}. Count "
        f"{look['runs']['primary']['blank_month_count']}, share {look['runs']['primary']['blank_month_share']:.4f}. "
        "By year (primary run): " + ", ".join(f"{y} {n}" for y, n in
                                             look["runs"]["primary"]["blank_months_by_year"].items()) + ". "
        "The JSON lists each blank month.", ""]
    out += ["Rebalance coverage of CW-PIT in the look (`reports_owed.counts`):", ""]
    out += counts_table({run: owed["counts"]["look"][run] for run in RUNS}, "Loader run")

    out += ["## Screen", "",
            f"Each candidate runs alone as a 2 percent TE tilt against the CW-PIT of the same run. The decision cell "
            f"is the {screen['decision_cell']['loader_run']} loader run with the {screen['decision_cell']['cost_case']}"
            f" cost case. Annual active mean, TE, IR, and HAC t are against CW-PIT over the screen months with "
            f"values. A candidate with fewer than {screen['min_months']} months gets a typed undefined record.", "",
            "Screen cost schedule (one way, bp per traded notional): " + "; ".join(
                f"from {row[0] or 'the first row'}, commission {row[1]:g} and spread {row[2]:g}"
                for row in screen["cost_schedule"]) + ". The 2x case doubles each cost.", ""]
    out += table(["ID", "Real start", "First month", "Months before blanks"],
                 [[s, c["real_start"] or "none", c["first_month"] or "none", c["screen_months_before_blanks"]]
                  for s, c in cand.items()])
    rows = []
    for s, c in cand.items():
        for run in RUNS:
            for case in CASES:
                rec = c["cells"][run][case]["screen_record"]
                status_ = rec["status"] + (f" (`{rec['undefined_reason']}`)" if rec.get("undefined_reason") else "")
                decision = (("shortlisted" if c["shortlisted"] else "not shortlisted") if (run, case) == DECISION_CELL
                            else "reported only")
                rows.append([s, run, case, rec["months"], c["blank_months"][run], status_,
                             pct(rec["annual_active_mean"]), pct(rec["annual_te"]), num(rec["information_ratio"]),
                             num(rec["hac_t"]), num(rec["p_one_sided"]), num(rec["annual_turnover"]), decision])
    out += table(["ID", "Loader run", "Cost case", "Months with values", "Blank months", "Record",
                  "Annual active mean", "TE", "IR", "HAC t", "p one-sided", "Turnover", "Decision"], rows)
    rows = []
    for s, c in cand.items():
        for case in CASES:
            cell = c["cells"]["primary"][case]
            if "tilt_vs_vwretd" in cell:
                t, cw = cell["tilt_vs_vwretd"], cell["cw_vs_vwretd"]
                rows.append([s, case, pct(t["annual_mean_gap"]), pct(t["annual_te"]), num(t["correlation"], 4),
                             pct(cw["annual_mean_gap"], 3)])
    out += ["TILT and CW-PIT against vwretd, primary loader run (annual mean gap and TE):", ""]
    out += table(["ID", "Cost case", "TILT mean gap", "TILT TE", "TILT correlation", "CW-PIT mean gap"], rows)

    out += ["## Freeze", "",
            f"- Decision `{freeze['decision']}`; shortlist {', '.join(freeze['shortlist']) or 'none'}.",
            f"- Rule: `ir_min` {freeze['rule']['ir_min']}, `t_min` {freeze['rule']['t_min']}, `shortlist_cap` "
            f"{freeze['rule']['shortlist_cap']}.",
            f"- Digest `{freeze['digest_sha256']}`. The script recomputed it with `m55_criteria.freeze_shortlist` "
            "from the screen records, and it equals the freeze file and `shortlist_digest.txt`.",
            f"- Test B: stopped {yes(freeze['test_b']['stopped'])}, label `{freeze['test_b']['label']}`, p_B "
            f"{freeze['test_b']['p_b']}.", ""]

    out += ["## Reports owed", "", "Each item of `reports_owed` that the stage files hold has its own key in the "
            "JSON under `reports_owed`. The tables give the primary cost case unless they say otherwise.", ""]
    out += r4_section(owed)
    out += ["### fragility", "", "A sign flip of an active annual mean between the primary run and the last_close "
            "rerun labels a result fragile (R4).", ""]
    rows = []
    for s, f in owed["fragility"]["screen"].items():
        for case, g in f.items():
            if g.get("status") == "not_evaluated":
                rows.append([s, case, "not evaluated", "", "", f"`{g['reason']}`"])
            else:
                flips = [k for k, v in g.items() if v["fragile"]]
                rows.append([s, case, pct(g["tilt_vs_cw"]["primary"]), pct(g["tilt_vs_cw"]["last_close"]),
                             ", ".join(flips) or "none", "fragile" if flips else "not fragile"])
    out += table(["ID", "Cost case", "TILT - CW, primary run", "TILT - CW, last_close run", "Sign flips", "Label"],
                 rows)
    out += r6_section(owed)
    out += me_section(owed)
    out += s2_section(owed, doc["missing"])
    out += path_break_section(owed, doc["missing"], cand)
    out += ["### counts", "", "Primary loader run, by candidate:", ""]
    out += counts_table({s: v["primary"] for s, v in owed["counts"]["screen"].items()}, "ID")
    out += tilt_section(owed)
    out += ["### labels", "", f"- Rule: {owed['labels']['rule']}.", f"- Run label: {owed['labels']['run_label']}.",
            f"- Factor-level reuse: {owed['labels']['factor_level_reuse']}.", "",
            "### bid_ask_midpoint_share", "",
            f"Share of member-days (1963 to 1992) with `dlyprcflg` = 'BA': {owed['bid_ask_midpoint_share']:.4f}.", ""]
    low = owed["low_risk_r6"]
    out += ["### low_risk_r6", "",
            "Ratio status counts: " + ", ".join(f"`{k}` {v}" for k, v in sorted(low["ratio_status_counts"].items()))
            + f". Gap rebalances {low['gap_rebalances']}, ratio gap members {low['ratio_gap_members']}, max "
            f"ratio_gap_cw_share {low['max_ratio_gap_cw_share']:.4f}. Members by later exit class:", ""]
    out += table(["Group", *EXITS], [by_class(k, v) for k, v in low["r6_by_exit_class"].items()])
    out += ["## Owed by later stages, items given as aggregates only, and withheld weights", "",
            *(f"- `{k}`: the confirm stage owes it. The trial asks for {owed[k]['reason']}."
              for k in ("check_period_end", "check_gap_months")),
            *(f"- `{k}`: {v}" for k, v in doc["missing"].items()), ""]
    return "\n".join(out).rstrip("\n") + "\n"


def counts_table(counts: Mapping[str, Mapping[str, Any]], label: str) -> list[str]:
    rows = []
    for key, c in counts.items():
        b2 = c["b2"]
        rows.append([key, c["rebalances"], num(c["members_mean"], 2), c["members_min"], num(c["traded_mean"], 2),
                     c["traded_min"], num(c["pinned_mean"], 1), c["c_zero_few_signals"], c["c_zero_short_history"],
                     c["c_zero_window_gap"], c["me_missing"],
                     ", ".join(f"{r} {c['me_missing_' + r]}" for r in ME_REASONS if c["me_missing_" + r]) or "none",
                     c["settled_excluded"], num(c["share_cap_at_final_weights"]), num(c["share_te_scaled"]),
                     f"{b2['rebalances']} / {b2['excluded']}"])
    return table([label, "Rebalances", "Members mean", "Members min", "Traded mean", "Traded min", "Pinned mean",
                  "c = 0 few signals", "c = 0 short history", "c = 0 window gap", "ME missing", "ME missing by reason",
                  "Settled excluded", "Share at stock cap", "Share TE-scaled",
                  "B2 rebalances / excluded"], rows)


def r4_cells(r4: Mapping[str, Any]) -> str:
    parts = []
    for cause, c in r4["by_cause"].items():
        if c["held"]:
            split = ", ".join(f"{k} {v}" for k, v in c.items()
                              if k not in ("held", "weight_at_last_rebalance_sum") and v)
            parts.append(f"{cause} {c['held']} ({split})")
    return "; ".join(parts) or "none"


def r4_section(owed: Mapping[str, Any]) -> list[str]:
    level = owed["r4"]["look_weight_level"]
    out = ["### r4", "", "Held disappearances by cause. In the primary run, `ciz_return_in_path` means CIZ put the "
           "delisting return in the path, `supplied_terminal_return` is a supplied return, and "
           "`missing_engine_default` takes the engine default. The last_close run settles every event at the last "
           "trade close. The weight at the event is the engine total book weight at the events. The weight at the "
           "last rebalance is the total post-trade weight at the last rebalance before each event.", "",
           "Public weight rule (2026-10-08): the report gives weight sums only for the look groups, "
           + {"by_cause": "by cause and in total.", "total": "as totals over causes. The stage files cannot show "
              "that the two loader runs hold the same events of a cause with equal counts, so no weight by cause "
              "is given.", "none": "and here it gives none."}[level]
           + " It gives no weight for a screen candidate group and no single maximum weight.", ""]
    rows = []
    for run in RUNS:
        for case in CASES:
            r = owed["r4"]["look"][run][case]
            rows.append([run, case, r["held"], num(r.get("incoming_weight_sum"), 4),
                         num(r.get("weight_at_last_rebalance_sum"), 4), r4_cells(r)])
    out += ["Look, CW-PIT:", ""]
    out += table(["Loader run", "Cost case", "Held", "Weight at the event, sum", "Weight at the last rebalance, sum",
                  "By cause"], rows)
    rows = []
    for s, v in owed["r4"]["screen"].items():
        p, lc = v["primary"]["primary"], v["last_close"]["primary"]
        rows.append([s, p["cw"]["held"], p["tilt"]["held"], r4_cells(p["cw"]), lc["cw"]["held"]])
    out += ["Screen, primary cost (counts only):", ""]
    out += table(["ID", "Held CW, primary run", "Held TILT, primary run", "CW by cause, primary run",
                  "Held CW, last_close run"], rows)
    return out


def r6_section(owed: Mapping[str, Any]) -> list[str]:
    r6 = owed["r6"]
    out = ["### r6", "", "Typed-missing shares by later exit class. Signal reason shares over the member cells of "
           "the return months 1963-01 to 1992-12 (coverage stage):", ""]
    rows = [[s, f"`{reason}`", *(num(shares.get(c), 4) for c in EXITS)]
            for s, by_reason in r6["signal_reason_shares_by_exit_class"].items()
            for reason, shares in by_reason.items()]
    out += table(["ID", "Reason", *EXITS], rows)
    out += ["Member-day census, 1963 to 1992, by later exit class:", ""]
    census = r6["member_day_census"]["by_exit_class"]
    out += table(["Class", "Member days", "With daily row", "With price", "With return", "With path value"],
                 [[c, *(census[c][k] for k in ("member_days", "with_daily_row", "with_price", "with_return",
                                               "with_path_value"))] for c in EXITS if c in census])
    for run, s in r6["screen_census"].items():
        out += [f"Screen census over the rebalances of the screen window, {run} loader run (cells; share of pool "
                "cells):", ""]
        rows = [by_class("pool cells", s["pool_cells"])]
        for reason, v in s["me_missing"].items():
            rows.append(by_class(f"ME missing, {reason}", {c: f"{v['cells'][c]} ({num(v['share'][c], 4)})"
                                                           for c in EXITS}))
        for key in ("unpriced", "basis_unseen", "blanked_windows"):
            rows.append(by_class(key.replace("_", " "), {c: f"{s[key]['cells'][c]} ({num(s[key]['share'][c], 4)})"
                                                         for c in EXITS}))
        out += table(["Item", *EXITS], rows)
    out += ["c = 0 cells by reason and later exit class, primary loader run:", ""]
    rows = [[s, reason, *(v[reason]["cells"][c] for c in EXITS)]
            for s, runs in r6["c_zero_by_exit_class"].items() for v in [runs["primary"]]
            for reason in ("few_signals", "short_history", "window_gap")]
    out += table(["ID", "Reason", *EXITS], rows)
    return out


def me_section(owed: Mapping[str, Any]) -> list[str]:
    me = owed["me_coverage"]
    head = ["Member days", *(f"{r} days" for r in ME_REASONS), "Present days", "Dollar volume share present"]

    def row(key: str, v: Mapping[str, Any]) -> list[Any]:
        return [key, v["member_days"], *(v[f"days_{r}"] for r in ME_REASONS), v["days_present"],
                num(v["dv_share_present"], 6)]
    out = ["### me_coverage", "", "ME status in member-days and in dollar volume (split-only close times "
           "split-adjusted volume), by later exit class and by year (the JSON holds the dollar volume share of each "
           "reason):", ""]
    out += table(["Class", *head], [row(c, me["by_exit_class"][c]) for c in EXITS if c in me["by_exit_class"]])
    out += table(["Year", *head], [row(y, v) for y, v in me["by_year"].items()])
    out += ["Unmapped member-days that the unseen-basis rule alone gives, to 1992:", ""]
    out += table(["Case", "By year", "Last date"],
                 [[case, ", ".join(f"{y} {n}" for y, n in v["by_year"].items()) or "none", v["last"] or "none"]
                  for case, v in me["basis_unseen_member_days_to_1992"].items()])
    out += ["S7 coverage by return month, 1963 and 1964:", ""]
    out += table(["Month", "Members", "Valid", "Valid share", "Reasons", "basis_unseen at anchor",
                  "basis_unseen at anchor - 12"],
                 [[m, v["members"], v["valid"], num(v["valid_share"], 3),
                   ", ".join(f"{k} {n}" for k, n in sorted(v["reasons"].items())) or "none",
                   v["basis_unseen_at_anchor"], v["basis_unseen_at_anchor_12"]] for m, v in me["s7_early"].items()])
    return out


def s2_section(owed: Mapping[str, Any], missing: Mapping[str, str]) -> list[str]:
    if owed["s2_short_history"] is None:
        return []
    out = ["### s2_short_history", "", "By year: the share of S2 member cells typed `short_history`, and the mean ME "
           "percentile of S2 `short_history` and S2 valid members (the size effect on the S2 ranks):", ""]
    out += table(["Year", "short_history share", "Mean ME percentile, short_history", "Mean ME percentile, valid"],
                 [[y, num(v["short_history_share"], 4), num(v["mean_me_percentile_short_history"], 4),
                   num(v["mean_me_percentile_valid"], 4)] for y, v in owed["s2_short_history"].items()])
    rule = owed["s2_history_rule"]
    out += ["### s2_history_rule", "", "S2 cells typed `split_in_basis_window` by year: " + (", ".join(
        f"{y} {n}" for y, n in rule["split_in_basis_window_cells_by_year"].items()) or "none") + ".", "",
        "Member quarters whose `cfacshr` at rdq differs from the one at the known date, by year of the known date:",
        ""]
    out += table(["Year", "Changed", "Same", "Unread"],
                 [[y, v["changed"], v["same"], v["unread"]] for y, v in rule["basis_quarters_by_year"].items()])
    out += [f"Not in the screen stage files: {missing['s2_history_rule']}.", ""]
    return out


def path_break_section(owed: Mapping[str, Any], missing: Mapping[str, str],
                       cand: Mapping[str, Mapping[str, Any]]) -> list[str]:
    pb = owed["path_break"]
    out = ["### path_break", "", "Held positions across a `path_break` row, as aggregates only. The span is the "
           "number of screen months that one position blanks. By the public weight rule (2026-10-08), only the "
           "run-level look set has a weight sum.", ""]
    rows = []
    for name, v in [*((f"look, {run}", v) for run, v in pb["look"].items()),
                    *((f"{s}, {run}", v) for s, runs in pb["screen"].items() for run, v in runs.items())]:
        span = v["span_months"] or {"min": "none", "median": "none", "max": "none"}
        rows.append([name, v["position_count"], v["months"],
                     num(v["weight_sum"]["cw"], 4) if "weight_sum" in v else "not given",
                     ", ".join(f"{c} {n}" for c, n in v["by_exit_class"].items() if n) or "none",
                     f"{span['min']} / {span['median']} / {span['max']}"])
    out += table(["Book set", "Positions", "Months blanked", "CW weight sum", "By later exit class",
                  "Span min / median / max"], rows)
    lost = [f"{s} loses {c['blank_months']['primary']} months" for s, c in cand.items()
            if c["blank_months"]["primary"] and s in pb["screen"] and not pb["screen"][s]["primary"]["position_count"]]
    out += ["Each candidate's declaration is the run blank set cut to its span (the frozen rule). So a candidate can "
            "lose months to positions that its own books do not hold."
            + (f" In the primary run, {', and '.join(lost)}, with no path-break position in its own books."
               if lost else ""), "",
            "Blanked level windows (R6), by later exit class:", ""]
    out += table(["Loader run", "Windows", *EXITS],
                 [[run, v["windows"], *(v["by_exit_class"][c] for c in EXITS)]
                  for run, v in pb["blanked_level_windows"].items()])
    out += ["### b2", "", "B2 exclusions as aggregates (rebalances with an exclusion and names excluded):", ""]
    rows = [[f"look, {run}", v["rebalances"], v["excluded"]] for run, v in owed["b2"]["look"].items()]
    rows += [[f"{s}, {run}", v["rebalances"], v["excluded"]]
             for s, runs in owed["b2"]["screen"].items() for run, v in runs.items()]
    out += table(["Book set", "Rebalances", "Excluded"], rows)
    out += [f"{missing['path_break']} {missing['b2']}", ""]
    return out


def tilt_section(owed: Mapping[str, Any]) -> list[str]:
    out = ["### tilt_stats", "", "Primary loader run and primary cost (IR is in the screen table). Turnover and cost "
           "drag per year are in the JSON.", ""]
    rows = []
    for s, v in owed["tilt_stats"].items():
        t = v["primary"]["primary"]
        rows.append([s, pct(t["realized_te_daily"]), pct(t["worst_relative_drawdown"]), num(t["size_exposure_mean"]),
                     num(t["annual_turnover"]["tilt"]), num(t["annual_turnover"]["cw"]),
                     num(t["annual_turnover"]["active"]), pct(t["annual_cost_drag"]["tilt"]),
                     pct(t["annual_cost_drag"]["active"])])
    out += table(["ID", "Realized TE (daily)", "Worst relative drawdown", "Size exposure mean", "Turnover TILT",
                  "Turnover CW", "Turnover active", "Cost drag TILT", "Cost drag active"], rows)
    out += ["### post_publication_split", "", "Active months after the signal's publication year (the M5 "
            "convention), primary loader run and primary cost:", ""]
    out += table(["ID", "Publication year", "Months after", "Months before", "Annual active mean after",
                  "Annual active mean before"],
                 [[s, p["publication_year"], p["months_after"], p["months_before"], pct(p["annual_mean_after"]),
                   pct(p["annual_mean_before"])]
                  for s, v in owed["post_publication_split"].items() for p in [v["primary"]["primary"]]])
    return out


def attempts(doc: Mapping[str, Any]) -> str:
    """One JSON line per run of the trial family (R9)."""
    return "".join(json.dumps({k: v for k, v in r.items() if k != "code_pins_sha256"}, sort_keys=True,
                              allow_nan=False) + "\n" for r in doc["runs"])


def outputs(doc: Mapping[str, Any]) -> dict[str, str]:
    texts = {REPORT_JSON: json.dumps(doc, indent=1, sort_keys=True, allow_nan=False) + "\n",
             REPORT_MD: render(doc), ATTEMPTS_JSONL: attempts(doc)}
    check_output(doc, texts)
    return texts


def main(argv: list[str] | None = None, out: Path = d.REPO / "reports") -> int:
    parser = argparse.ArgumentParser(description="Write the public M5.5 screen report from the run 1 and run 2 "
                                                 "stage folders (aggregates only).")
    parser.add_argument("run_1", type=Path, help="the run 1 stage folder (m55_screen_v1)")
    parser.add_argument("run_2", type=Path, help="the run 2 stage folder (m55_screen_v2)")
    args = parser.parse_args(argv)
    try:
        texts = outputs(build(args.run_1, args.run_2))
    except RunnerStop as exc:
        print(f"refused: {exc.reason}: {exc.detail}", file=sys.stderr)
        return 1
    for name, text in texts.items():
        (Path(out) / name).write_text(text, encoding="utf-8")
    print("\n".join(f"wrote reports/{name}" for name in texts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
