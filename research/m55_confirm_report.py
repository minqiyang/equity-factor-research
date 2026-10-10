"""Milestone 5.5: the public report of the confirm and check stages of trial family v1 from the private stage files
of run 4.

The script reads the seven stage files and the run log that ``research/m55_driver.py`` wrote for run 4, checks them,
and writes three public files with aggregates only:

- ``reports/m55_confirm_v1.json``: every aggregate of the report;
- ``reports/m55_confirm_v1.md``: the decision tables and the reports owed in plain tables;
- ``reports/m55_confirm_v1_attempts.jsonl``: one line per attempt of run 4 (R9), after one reference line per earlier
  run: run 1 and run 2 (``reports/m55_screen_v1_attempts.jsonl``), and run 3, which refused at the confirm stage and
  wrote no confirm or check file (``RUN_3``).

Checks (each refuses with a non-zero exit, and no file is written): each ``<stage>.sha256`` file matches its stage
file, the stages share one context and each names the digests of the stages before it
(``m55_screen_report.check_run``); the context names the merged trial file (``m55_driver.TRIAL_SHA256``), the data of
both tracked manifests, the code pins of the trial file, and the code of main ``e5ac840``; the shortlist digest
recomputed from the screen records equals the freeze file (``m55_screen_report.check_freeze``) and the run 2 digest
that amendment 3 states, and so does the digest of the confirm and check files; the test B record of each later stage
equals ``m55_driver.record_test_b`` and is stopped; each segment and loader run of the confirm and check files has
``exit_gap_events`` (amendment 4); and the run log names each stage file once, with its digest. The script computes
no new test statistic.

Privacy (owner grant O-22, R11): the stage files hold per-position rows (path-break positions, blanked level windows,
and B2 rows) and per-cell trade weights. The report gives aggregates only, under the public weight rule (coordinator,
2026-10-08, REVIEW M-1): a weight is published only as a sum over at least 3 positions, and no two published sums
differ by fewer than 3 positions. So only the CW-PIT book of each segment and loader run gets R4, path-break, and
amendment 4 weight sums, a signal set gets counts only, and no single maximum weight is given. The half-spread tables
give shares of the traded notional and no traded notional sum by year, and the largest half-spread of a traded cell
as a band.
The report holds no private path: the stage folder is a command-line argument and the report does not name it. The
output is the same bytes on each run.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from research import m55_criteria as crit
from research import m55_driver as d
from research import m55_screen_report as rep
from research import m55_wrds_loader as w
from research.m4_7_sp500_pit_rerun import RunnerStop
from research.m55_index_tilt import COST_SCALES, COST_SCHEDULE, QUOTE_REASONS, refuse


REPORT_JSON = "m55_confirm_v1.json"
REPORT_MD = "m55_confirm_v1.md"
ATTEMPTS_JSONL = "m55_confirm_v1_attempts.jsonl"
SCREEN_ATTEMPTS = "reports/m55_screen_v1_attempts.jsonl"     # the lines of run 1 and run 2 (R9)
RUNS, CASES, EXITS = d.RUNS, d.CASES, w.EXIT_CLASSES
DECISION = ("primary", "primary")               # test A reads the primary loader run with the primary cost case
# The run facts that the stage files do not hold: the code commit of run 4 and the digest of its research/ and src/
# Python files (m55_driver.code_digest) at that commit.
RUN_4 = {"run": 4, "code_commit": "e5ac840e6e04406683dc93879898d272c76aaa32",
         "code_sha256": "af01de3e1b399f8e2a12099e5f525b6c71ff187a9b15c4e1735a1de1c982af0d",
         "trial": "trial family v1 with amendments 1 to 4"}
# The reference line of run 3 (R9), from the coordinator's record: the confirm stage refused (engine check H-5) and
# wrote no file, so no report reads its folder. Its detail text stays in its private run log.
RUN_3 = {"run": 3, "status": "refused", "code_commit": "b1b0517294247e92de6734916fa84937c1351622",
         "stages": {**{s: "written" for s in d.STAGES[:d.STAGES.index("freeze") + 1]}, "confirm": "refused",
                    "check": "not_run"},
         "reason": "unresolved_disappearance",
         "run_log_sha256": "3c7e6553b4fdf5ec0101ce7e9e98bd5e21978a48f54e2b4ada517c76a4b862b8",
         "see": "docs/decision_log.md", "entry": "Trial Family v1 Amendment 4"}
SETS = (d.COMPOSITE, *d.SECONDARY)              # the composite of the shortlist, S1 to S8 alone, the Family A baseline
SEGMENTS = {"confirm": ("confirm",), "check": ("check_pre_seal", "check_post_seal")}
# The largest half-spread of a traded cell is published as a band in bp (lower edge included): an exact value with
# its book and year can single out one security and day in the CRSP quotes.
HALF_SPREAD_BANDS = (5.0, 10.0, 20.0, 50.0, 100.0, 200.0)
# The output guard: identifier keys, the half-spread fields that are weight sums or a single quote, and the per-year
# turnover and cost drag of one book (with them, a notional share gives a weight sum).
IDENTIFIERS = frozenset({"permno", "permanent_id", "gvkey", "ticker", "cusip", "comnam"})
PRIVATE_KEYS = rep.FORBIDDEN | rep.SINGLE_MAX | IDENTIFIERS | frozenset(
    {"traded_notional", "traded_notional_by_status", "max_half_spread", "cw_weight_by_exit_class"})
RUN_LEVEL = "run_level"                         # the only key under which a weight sum may appear
EXIT_GAP_WEIGHT = "held_cw_weight_sum"          # the CW-PIT weight sum of the held amendment 4 events
WEIGHTS = rep.GROUP_WEIGHTS | {EXIT_GAP_WEIGHT}
BY_YEAR = ("turnover_by_year", "cost_drag_by_year")
# Words that would call the result a confirmation or claim a profit. The run label of the trial file is quoted word
# for word, so it is removed from a text before the check.
CLAIM = re.compile(r"confirmation|confirmed|confirms|profitab|profit\b|outperform|\bbeats?\b", re.IGNORECASE)
NO_CLAIM = ("no profitability claim",)


# Checks -----------------------------------------------------------------------------------

def data_digest(trial: Mapping[str, Any], tracked: Mapping[str, Any], tracked_quotes: Mapping[str, Any]) -> str:
    """The ``data_files_sha256`` of a stage context made from the data of both tracked manifests (as in
    ``m55_driver.run_stage``)."""
    wrds = d.check_data(w.WrdsData({}, tracked), tracked, trial)
    quotes = d.check_quotes(w.WrdsData({}, tracked_quotes), tracked_quotes, trial)
    return d.sha256_bytes(json.dumps({"wrds": wrds, "quotes": quotes}, sort_keys=True).encode())


def check_context(ctx: Mapping[str, Any], trial: Mapping[str, Any], data_sha: str, repo: Path) -> None:
    """The one context of run 4: the merged trial file, the tracked data, the trial's code pins, and the code of
    ``RUN_4["code_commit"]``."""
    if ctx["trial_sha256"] != d.TRIAL_SHA256:
        raise refuse("trial_mismatch", "run 4 was not made from the merged trial file with amendments 1 to 4")
    if ctx["data_files_sha256"] != data_sha:
        raise refuse("data_manifest_mismatch", "run 4 was not made from the data of the two tracked manifests")
    if ctx["code_pins_sha256"] != d.context(trial, d.TRIAL_SHA256, data_sha, repo)["code_pins_sha256"]:
        raise refuse("code_pins_mismatch", "run 4 was not made from the code pins of the trial file")
    if ctx["code_sha256"] != RUN_4["code_sha256"]:
        raise refuse("code_mismatch", f"run 4 was not made from the code of {RUN_4['code_commit']}")


def check_test_b(payloads: Mapping[str, dict], digests: Mapping[str, str]) -> dict[str, Any]:
    """Test B in each stage after the calibration equals ``record_test_b`` and is stopped (amendment 2)."""
    test_b = d.record_test_b(payloads["calibration"]["result"], digests["calibration"])
    if any(payloads[s]["result"].get("test_b") != test_b for s in d.STAGES[d.STAGES.index("look"):]):
        raise refuse("test_b_mismatch", "a later stage does not record test B as the calibration gives it")
    if not test_b["stopped"]:
        raise refuse("test_b_open", "the confirm and check stages run only after the coverage stop of test B")
    return test_b


def check_digest(payloads: Mapping[str, dict], frozen: Mapping[str, Any], trial: Mapping[str, Any]) -> str:
    """The freeze digest, and the digest and shortlist of the confirm and check files, equal the run 2 freeze that
    amendment 3 states."""
    run_2 = d.run2_digest(trial)
    if frozen["digest_sha256"] != run_2 or any(
            payloads[s]["result"]["digest_sha256"] != run_2 or payloads[s]["result"].get("shortlist",
                                                                                     frozen["shortlist"])
            != frozen["shortlist"] for s in SEGMENTS):
        raise refuse("run2_digest_mismatch", "the run 4 freeze is not the run 2 freeze that amendment 3 states")
    return run_2


def attempts_of(folder: Path, digests: Mapping[str, str]) -> list[dict[str, Any]]:
    """One line per attempt of a stage in the run log: written (with the stage digest), refused, or error (with the
    reason). The detail text stays in the private run log. Each stage file is written once, with its digest."""
    path = folder / "run_log.jsonl"
    if not path.is_file():
        raise refuse("run_log_missing", "run_log.jsonl")
    lines, written = [], {}
    for text in path.read_text().splitlines():
        entry = json.loads(text)
        outcome = next((k for k in ("written", "refused", "error") if k in entry), None)
        if outcome is None:
            continue
        line = {"run": RUN_4["run"], "attempt": len(lines) + 1, "stage": entry["stage"], "outcome": outcome}
        if outcome == "written":
            line["stage_sha256"] = entry["written"]
            written.setdefault(entry["stage"], []).append(entry["written"])
        else:
            line["reason"] = entry[outcome]
        lines.append(line)
    if written != {s: [digests[s]] for s in d.STAGES}:
        raise refuse("run_log_mismatch", "the run log does not name each stage file once with its digest")
    return lines


def earlier_runs(repo: Path) -> list[dict[str, Any]]:
    """The reference lines of run 1 and run 2 (R9): the screen report's attempts file and its SHA-256."""
    raw = (repo / SCREEN_ATTEMPTS).read_bytes()
    found = [json.loads(line) for line in raw.decode().splitlines()]
    if [r["run"] for r in found] != [1, 2]:
        raise refuse("attempts_reference_invalid", SCREEN_ATTEMPTS)
    return [{"run": r["run"], "status": r["status"], "see": SCREEN_ATTEMPTS, "file_sha256": d.sha256_bytes(raw)}
            for r in found]


# Aggregates -------------------------------------------------------------------------------

def counts_only(r4: Mapping[str, Any]) -> dict[str, Any]:
    """An R4 record with counts by cause and settlement only (a signal-set group nests in the CW-PIT group)."""
    return rep.aggregate(r4, rep.DROP | rep.GROUP_WEIGHTS)


def path_break_runs(runs: Mapping[str, Mapping[str, Any]]) -> tuple[dict[str, Any], bool]:
    """The path-break aggregates of the CW-PIT book of each loader run, with the CW weight sum when the public
    weight rule allows it. A position is known by its break row, previous valid row, and later exit class, so two
    loader runs hold the same positions or differ by the size of the difference of the two sets."""
    held = {run: Counter((p["break_row"], p["previous_valid_row"], p["exit_class"]) for p in runs[run]["positions"])
            for run in RUNS}
    apart = [sum(((held[a] - held[b]) + (held[b] - held[a])).values()) for a, b in itertools.combinations(RUNS, 2)]
    allowed = (all(sum(h.values()) >= rep.MIN_POSITIONS for h in held.values())
               and all(n == 0 or n >= rep.MIN_POSITIONS for n in apart))
    return {run: rep.path_break(runs[run]["positions"], ("cw",) if allowed else ()) for run in RUNS}, allowed


def exit_gap_runs(part: Mapping[str, Any], r4: Mapping[str, Any], level: str) -> tuple[dict[str, Any], bool]:
    """The amendment 4 events of each loader run (``exit_gap_events``): every count, and the CW-PIT weight sum of
    the held events when the public weight rule allows it.

    The held events are CW-PIT R4 events of cause unknown, so the rule also compares this sum with each R4 weight
    sum of the segment that the report gives (``level``, from ``look_r4``). In one loader run the held events are
    part of each R4 group, so a count difference there is a difference of positions. Across loader runs, equal
    counts fail (``m55_screen_report.weight_rule``).
    """
    runs = part["runs"]
    if any("exit_gap_events" not in runs[run] for run in RUNS):
        raise refuse("exit_gap_events_missing", f"{part['segment']['name']}: a loader run has no exit_gap_events")
    found = {run: dict(runs[run]["exit_gap_events"]) for run in RUNS}
    causes = list(r4["primary"]["primary"]["by_cause"])

    def split(held: Mapping[str, int]) -> dict[str, int]:
        return {c: held.get(c, 0) for c in causes}
    groups = {(run, "exit_gap"): split({d.EXIT_GAP_CAUSE: found[run]["held"]}) for run in RUNS}
    if level != "none":
        for run, case in itertools.product(RUNS, CASES):
            groups[(run, case)] = held = {c: r4[run][case]["by_cause"][c]["held"] for c in causes}
            if level == "by_cause":
                groups.update({(run, case, c): split({c: held[c]}) for c in causes})
    allowed = rep.weight_rule(groups)
    if not allowed:
        for v in found.values():
            v.pop(EXIT_GAP_WEIGHT)
    return found, allowed


def band(value: float | None) -> str | None:
    """The band in bp of a half-spread (``HALF_SPREAD_BANDS``, lower edge included)."""
    if value is None:
        return None
    edges = (0.0, *HALF_SPREAD_BANDS)
    for low, high in zip(edges, edges[1:]):
        if value < high:
            return f"{low:g} to {high:g}"
    return f"{edges[-1]:g} or more"


def half_spread(years: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """One book's half-spread report by year: the notional share of each quote status, the CRSP-binds and BA
    shares, the band of the largest half-spread, the spread cost above the schedule, and the invalid traded cells by
    reason and later exit class (nonzero counts only). The traded notional of the year is not given."""
    out = {}
    for year, v in years.items():
        total = v["traded_notional"]
        out[year] = {"notional_share_by_status": {s: n / total if total else None
                                                  for s, n in v["traded_notional_by_status"].items()},
                     "crsp_binds_share": v["crsp_binds_share"], "bid_ask_share": v["bid_ask_share"],
                     "max_half_spread_band_bp": band(v["max_half_spread"]),
                     "cost_above_schedule": v["cost_above_schedule"],
                     "invalid_traded_cells_by_exit_class": {
                         r: {c: n for c, n in classes.items() if n}
                         for r, classes in v["invalid_traded_cells_by_exit_class"].items() if any(classes.values())}}
    return out


def tilt_stats(stats: Mapping[str, Any]) -> dict[str, Any]:
    """``tilt_stats`` with the per-year turnover and cost drag of the active book only (trial: "active turnover and
    cost drag per year"); the post-publication split is its own report."""
    out = {k: v for k, v in stats.items() if k not in ("post_publication", *BY_YEAR)}
    out.update({k: {"active": stats[k]["active"]} for k in BY_YEAR})
    return out


def segment_doc(part: Mapping[str, Any]) -> dict[str, Any]:
    """One engine segment: its dates and the reports owed, aggregates only.

    CW-PIT is one book in every signal set (the same members, events, and costs), so the report gives it once, from
    the composite run, and refuses when a set has another CW-PIT record. The half-spread tables cover every loader
    run and cost case for the composite TILT and CW-PIT, and the decision cell for the other sets' TILT books.
    """
    sets = [s for s in SETS if s in part["sets"]]
    items, runs = part["sets"], part["runs"]
    cw = {run: {case: items[d.COMPOSITE]["records"][run][case] for case in CASES} for run in RUNS}
    if any(items[s]["records"][run][case][key]["cw"] != cw[run][case][key]["cw"]
           for s in sets for run in RUNS for case in CASES for key in ("r4", "half_spread")):
        raise refuse("cw_pit_not_one_book", f"{part['segment']['name']}: a signal set has another CW-PIT record")
    r4_run_level, r4_level = rep.look_r4({run: {case: {"r4": cw[run][case]["r4"]["cw"]} for case in CASES}
                                          for run in RUNS})
    pb_run_level, pb_weights = path_break_runs(runs)
    gap_run_level, gap_weights = exit_gap_runs(part, r4_run_level, r4_level)

    def each(fn) -> dict[str, Any]:
        return {s: {run: {case: fn(items[s]["records"][run][case]) for case in CASES} for run in RUNS} for s in sets}

    def tilt_spread(s: str) -> dict[str, Any]:
        cells = [(run, case) for run in RUNS for case in CASES] if s == d.COMPOSITE else [DECISION]
        out: dict[str, Any] = {}
        for run, case in cells:
            out.setdefault(run, {})[case] = half_spread(items[s]["records"][run][case]["half_spread"]["tilt"])
        return out
    return {
        "segment": dict(part["segment"]),
        "blank_months": {run: {"months": runs[run]["blank_months"], "count": runs[run]["blank_month_count"],
                               "share": runs[run]["blank_month_share"],
                               "by_year": dict(sorted(Counter(m[:4] for m in runs[run]["blank_months"]).items()))}
                         for run in RUNS},
        "r4": {RUN_LEVEL: r4_run_level, "weight_level": r4_level,
               "tilt": each(lambda r: counts_only(r["r4"]["tilt"]))},
        "path_break": {RUN_LEVEL: pb_run_level, "weight_given": pb_weights,
                       "sets": {s: {run: rep.path_break(items[s]["path_break_positions"][run]) for run in RUNS}
                                for s in sets},
                       "blanked_level_windows": {run: rep.aggregate(runs[run]["blanked_level_windows"])
                                                 for run in RUNS}},
        "exit_gap": {RUN_LEVEL: gap_run_level, "weight_given": gap_weights},
        "r6": {"members": {run: runs[run]["r6_members"] for run in RUNS}, "signals": part["signals_r6"],
               "c_zero_by_exit_class": {s: items[s]["c_zero_by_exit_class"] for s in sets
                                        if "c_zero_by_exit_class" in items[s]}},
        "s2_short_history": part["s2_short_history"],
        "s2_split_in_basis_window_by_year": part["s2_split_in_basis_window_by_year"],
        "s2_basis_quarters_by_year": part["s2_basis_quarters_by_year"],
        "s2_valid_share_by_month": part["s2_valid_share_by_month"],
        "b2": {s: {run: rep.aggregate(items[s]["counts"][run]["b2"]) for run in RUNS} for s in sets},
        "counts": {s: {run: rep.aggregate(items[s]["counts"][run]) for run in RUNS} for s in sets},
        "tilt_stats": each(lambda r: tilt_stats(r["tilt_stats"])),
        "post_publication_split": each(lambda r: r["tilt_stats"]["post_publication"]),
        "half_spread": {"cw_pit": {run: {case: half_spread(cw[run][case]["half_spread"]["cw"]) for case in CASES}
                                   for run in RUNS},
                        "tilt": {s: tilt_spread(s) for s in sets}},
    }


def stage_doc(stage: str, result: Mapping[str, Any]) -> dict[str, Any]:
    """The aggregates of the confirm or the check stage file."""
    out = {"segments": {n: segment_doc(result["segment"] if stage == "confirm" else result["segments"][n])
                        for n in SEGMENTS[stage]},
           "means": rep.aggregate(result["means"]), "fragility": result["fragility"],
           "oi09": rep.aggregate(result["oi09"]),
           "me_coverage": result["me_coverage"], "bid_ask_midpoint_share": result["bid_ask_midpoint_share"]}
    if stage == "confirm":
        family = result["family_a_screen"]
        out["secondary"] = rep.aggregate(result["secondary"])
        out["family_a_screen"] = {
            "records": {run: {case: {"screen_record": rep.aggregate(r["screen_record"]),
                                     "tilt_vs_vwretd": rep.aggregate(r["tilt_vs_vwretd"]),
                                     "r4": {book: counts_only(r["r4"][book]) for book in r["r4"]}}
                              for case, r in family["records"][run].items()} for run in RUNS},
            "counts": {run: rep.aggregate(family["counts"][run]) for run in RUNS},
            "fragility": family["fragility"]}
    else:
        out.update({k: result[k] for k in ("check_period_end", "check_gap_months", "series_months",
                                           "s2_history_rule")})
    return out


def test_a(confirm: Mapping[str, Any], check: Mapping[str, Any]) -> dict[str, Any]:
    """Test A: the confirm decision of each loader run, the composite test records, the check means, the label."""
    runs = {"primary": confirm["test_a"]["decision"], "last_close": confirm["test_a"]["last_close"]}
    labels = {"primary": check["test_a"]["label"], "last_close": check["test_a"]["last_close"]}
    return {"decision_cell": {"loader_run": DECISION[0], "cost_case": DECISION[1]},
            "runs": {run: {**runs[run], "check_means": rep.aggregate(check["means"][d.COMPOSITE][run]["primary"]),
                           "decide_a": labels[run]} for run in RUNS},
            "records": rep.aggregate(confirm["test_a"]["records"]),
            "fragile": check["test_a"]["fragile"], "confirm_stop": check["test_a"]["confirm_stop"],
            "holm_alpha": crit.ALPHA, "confirm_floor": crit.CONFIRM_FLOOR}


def build(run_4: Path, repo: Path = d.REPO, tracked: Mapping[str, Any] | None = None,
          tracked_quotes: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Check run 4 and return the report document (aggregates only) and the attempt lines."""
    folder = Path(run_4)
    trial, _ = d.load_trial(repo)
    tracked = json.loads((repo / d.TRACKED_MANIFEST).read_text()) if tracked is None else tracked
    tracked_quotes = json.loads((repo / d.QUOTE_MANIFEST).read_text()) if tracked_quotes is None else tracked_quotes
    data_sha = data_digest(trial, tracked, tracked_quotes)
    payloads, digests = rep.check_run(folder, d.STAGES)
    ctx = payloads["coverage"]["context"]
    check_context(ctx, trial, data_sha, repo)
    test_b = check_test_b(payloads, digests)
    frozen = rep.check_freeze(payloads, folder)
    run_2 = check_digest(payloads, frozen, trial)
    attempts = [*earlier_runs(repo), RUN_3, *attempts_of(folder, digests)]
    confirm, check = payloads["confirm"]["result"], payloads["check"]["result"]

    periods = trial["periods"]
    reuse = next(i for i in trial["prior_exposures"]["items"] if i.startswith("M5 step 2"))
    run = {"run": RUN_4["run"], "trial": RUN_4["trial"], "trial_sha256": ctx["trial_sha256"],
           "code_commit": RUN_4["code_commit"], "code_sha256": ctx["code_sha256"],
           "code_pins_sha256": ctx["code_pins_sha256"], "data_files_sha256": ctx["data_files_sha256"],
           "stage_sha256": digests, "status": "completed", "freeze_decision": frozen["decision"],
           "shortlist": frozen["shortlist"], "shortlist_digest_sha256": frozen["digest_sha256"],
           "attempts": dict(sorted(Counter(a["outcome"] for a in attempts if a["run"] == RUN_4["run"]).items()))}
    manifests = {name: {"file": path, "file_sha256": d.sha256_bytes((repo / path).read_bytes()),
                        "vintage": manifest["vintage"], "main_files": len(manifest["files"]),
                        "main_rows": sum(int(r["rows"]) for r in manifest["files"].values())}
                 for name, path, manifest in (("first_pull", d.TRACKED_MANIFEST, tracked),
                                              ("second_pull_quotes", d.QUOTE_MANIFEST, tracked_quotes))}
    doc = {
        "report": "m55_confirm_v1",
        "header": {**confirm["header"], "factor_level_reuse": reuse, "check_label": periods["check"]["label"],
                   "benchmarks": {"confirm": periods["confirm"]["benchmarks"],
                                  "check": periods["check"]["benchmarks"],
                                  "spy": trial["data"]["benchmarks"]["confirm_and_check"],
                                  "decomposition": trial["data"]["benchmarks"]["decomposition"]},
                   "execution_timing": trial["universe_and_timing"]["timing_contract"],
                   "prior_exposures": trial["prior_exposures"]["items"]},
        "provenance": {"trial_file": d.TRIAL_FILE, "trial_sha256": ctx["trial_sha256"],
                       "data_vintage": trial["data"]["vintage"], "manifests": manifests,
                       "data_files_sha256": data_sha, "run2_digest_sha256": run_2,
                       "run_log_sha256": d.sha256_bytes((folder / "run_log.jsonl").read_bytes())},
        "runs": run,
        "costs": {"basis": trial["books"]["costs"]["basis"], "schedule": [list(r) for r in COST_SCHEDULE],
                  "scales": dict(COST_SCALES), "half_spread_override": trial["books"]["costs"]["half_spread_override"],
                  "quote_reasons": list(QUOTE_REASONS), "half_spread_bands_bp": list(HALF_SPREAD_BANDS),
                  "family_a_screen_schedule": [list(r) for r in crit.SCREEN_COST_SCHEDULE],
                  "borrow": trial["books"]["costs"]["no_switch_cost"]},
        "test_b": {**test_b, "holm_alpha": crit.ALPHA, "p_a_max_for_holm": crit.ALPHA / 2},
        "test_a": test_a(confirm, check),
        "stages": {"confirm": stage_doc("confirm", confirm), "check": stage_doc("check", check)},
    }
    doc["missing"] = missing(doc)
    doc["limitations"] = limitations(doc)
    return doc, attempts


def missing(doc: Mapping[str, Any]) -> dict[str, str]:
    """The values the stage files hold and the report does not give, each with its reason."""
    levels = {(stage, n): seg["r4"]["weight_level"] for stage, part in doc["stages"].items()
              for n, seg in part["segments"].items()}
    rule = (f"The report does not give it: {rep.WEIGHT_RULE}. The value stays in the private stage files.")
    out = {
        "path_break.positions": "The trial asks for each held position with its weight in each book. The report "
                                "gives aggregates only (owner data terms O-22).",
        "b2.each": "The trial asks for unknown_event_excluded and unknown_event_cw_share at each rebalance. The "
                   "report gives aggregates only (owner data terms O-22).",
        "r4.incoming_weight_max": f"The largest book weight at one event. {rule}",
        "b2.max_cw_share": f"The largest CW share excluded at one rebalance. {rule}",
        "r4.tilt.weights": "The weight sums of each signal set's TILT book. Each group nests in the CW-PIT group of "
                           f"its segment and loader run, so a difference can isolate one event. {rule}",
        "half_spread.tilt.other_cells": "The half-spread tables of the S1 to S8 and Family A TILT books in the "
                                        "last_close run and in the 2x cost case. The report gives the decision cell of "
                                        "these books and every cell of the composite TILT and CW-PIT, to keep the "
                                        "file size small. The tables stay in the private stage files.",
        "path_break.sets.weight_sum": f"The weight sums of each signal set's books. {rule}",
        "path_break.cw_weight_by_exit_class": f"The CW weight of the path-break positions by later exit class. {rule}",
        "half_spread.traded_notional": "The traded notional of each book and year, and the notional by quote status. "
                                       "A quote status or a binding group can hold one or two traded cells. The "
                                       "report gives shares of the year's traded notional instead, and no figure "
                                       f"that gives the year's traded notional. {rule}",
        "half_spread.max_half_spread": "The largest half-spread of a traded cell, a quote value. With its book and "
                                       "year, an exact value can single out one security and day in the CRSP "
                                       "quotes, so the report gives its band in bp (`costs.half_spread_bands_bp`).",
        "tilt_stats.turnover_by_year": "The per-year turnover and cost drag of the TILT and CW-PIT books. With them, "
                                       "a half-spread notional share gives a weight sum. The report gives the "
                                       "active book per year (the trial's 'active turnover and cost drag per "
                                       f"year') and the full-segment figures of each book. {rule}",
        "attempts.detail": "The detail text of each refusal or error. It can name a date of one position or a "
                           "private path, so it stays in the private run log (its SHA-256 is in the provenance).",
    }
    for (stage, n), level in sorted(levels.items()):
        if level != "by_cause":
            out[f"r4.{stage}.{n}.by_cause.weight_at_last_rebalance_sum"] = (
                "The CW-PIT weight of each cause. At least one cause does not meet the rule, or two loader runs "
                f"have equal counts of a cause, which the stage files cannot show to be the same events. {rule}")
        if level == "none":
            out[f"r4.{stage}.{n}.weight_at_last_rebalance_sum"] = f"The CW-PIT total over causes. {rule}"
    for stage, part in doc["stages"].items():
        for n, seg in part["segments"].items():
            if not seg["path_break"]["weight_given"]:
                out[f"path_break.{stage}.{n}.weight_sum"] = f"The CW-PIT weight sum of the path-break positions. {rule}"
            if not seg["exit_gap"]["weight_given"]:
                out[f"exit_gap.{stage}.{n}.{EXIT_GAP_WEIGHT}"] = (
                    "The CW-PIT weight sum of the amendment 4 events that CW-PIT holds. A loader run holds fewer than 3 "
                    "of them, or this sum and another published sum (of the other loader run, or an R4 sum of the "
                    f"segment) can differ by fewer than 3 positions. {rule}")
    return dict(sorted(out.items()))


def limitations(doc: Mapping[str, Any]) -> list[str]:
    """The limitations, stated from the document's own numbers."""
    a, head = doc["test_a"], doc["header"]
    primary = a["runs"]["primary"]
    out = []
    if primary["stop"]:
        out.append(f"The stop rule applies: the confirm annual mean of the composite against SPY is "
                   f"{rep.pct(primary['confirm_means']['vs_spy'], 3)}, below the floor "
                   f"{rep.pct(a['confirm_floor'], 1)} a year. The line stops as a declared negative result, "
                   "whatever the test A label. The check stage still ran, because declared runs stay visible (R9).")
    out.append(f"Test A has the label `{primary['decide_a']['label']}` in the primary loader run. "
               + ("A sign flip of an active annual mean between the primary run and the last_close rerun makes the "
                  "result fragile (R4)." if a["fragile"] else
                  "No active annual mean of the composite changes sign between the primary run and the last_close "
                  "rerun (R4)."))
    for stage, part in doc["stages"].items():
        for name, seg in part["segments"].items():
            blank = seg["blank_months"]["primary"]
            if blank["count"]:
                pb = seg["path_break"][RUN_LEVEL]["primary"]
                weight = (f", with a CW-PIT weight sum of {pb['weight_sum']['cw']:.4f} at their last rebalance"
                          if "weight_sum" in pb else "")
                out.append(f"In the {name} segment, the path_break_held blank set removes {blank['count']} months "
                           f"(share {blank['share']:.4f}) from every series of the primary loader run. "
                           f"{pb['position_count']} held positions cause it{weight}. The frozen rule blanks these "
                           "months in every book, and R6 forbids a fill.")
    gap = [seg["exit_gap"][RUN_LEVEL]["primary"] for part in doc["stages"].values()
           for seg in part["segments"].values()]
    out.append("Under amendment 4, a member that leaves the index on a row without a close gets an R4 event of cause "
               "unknown on that row, in the confirm and check segments only. In the primary loader run there are "
               f"{sum(g['events'] for g in gap)} such events, CW-PIT holds {sum(g['held'] for g in gap)} of them, and "
               f"{sum(g['held_priced_again'] for g in gap)} of the held ones have a close again later in the segment. "
               "The primary run settles a held event at -100 percent, because a later close is not known on that row "
               "(R1). The last_close run settles it at the last close and is the R4 sensitivity for this case.")
    out += [f"The check period is labelled '{head['check_label']}'. It leaves out the {len(crit.CHECK_GAP_MONTHS)} "
            f"months {crit.CHECK_GAP_MONTHS[0]} to {crit.CHECK_GAP_MONTHS[-1]} (the seal, the sealed 2020-07-31 row, "
            "and the warm-up), and each segment starts from cash.",
            f"The run label is '{head['run_label']}'. {head['factor_level_reuse']}.",
            "A member without ME or without a price at r - 1 leaves both books, and SPY keeps it, so it is "
            "replication error (R2, R6). The OI-09 decomposition reports this term (CW-PIT against SPY).",
            "An invalid quote cell pays the schedule spread. The half-spread tables give the share of the traded "
            "notional of each quote status and the invalid cells by later exit class.",
            "The secondary family decides nothing. Its tables are in ID order, are not a ranking, and give the "
            "Benjamini-Yekutieli q-value beside each member.",
            "The trial file states the power of rule A (`limitations`): a test A label other than `met` often means "
            "'not shown', not 'absent'.",
            "This report makes no profitability claim. The books are long only, so no borrow cost applies."]
    return out


# Markdown ---------------------------------------------------------------------------------

pct, num, yes, table = rep.pct, rep.num, rep.yes, rep.table


def mean_cells(means: Mapping[str, Any]) -> list[str]:
    return [pct(means["vs_spy"], 3), pct(means["vs_cw"], 3)]


def render(doc: Mapping[str, Any]) -> str:
    """The Markdown report: test A first, then the secondary family, the Family A baseline, OI-09, the check stage,
    the provenance, and the reports owed (the composite run in tables; the JSON holds every signal set)."""
    head, a, tb = doc["header"], doc["test_a"], doc["test_b"]
    confirm = doc["stages"]["confirm"]
    out = ["# Milestone 5.5 confirm and check stages of trial family v1", "",
           f"Evidence ceiling: `{head['evidence_ceiling']}`. This is a simulated research diagnostic. It gives "
           "aggregates only and makes no profitability claim. The JSON file `reports/m55_confirm_v1.json` holds "
           "every aggregate of this report.", "",
           f"- Run label: {head['run_label']}.",
           f"- Check period label: {head['check_label']}.",
           f"- Factor-level reuse (`reports_owed.labels`): {head['factor_level_reuse']}.",
           "- Sample reuse (`prior_exposures`, R10): seen before the trial declaration, counted under R9:",
           *(f"  - {item}" for item in head["prior_exposures"]),
           f"- Benchmarks: confirm months {head['benchmarks']['confirm']}; check months "
           f"{head['benchmarks']['check']}. SPY: {head['benchmarks']['spy']}.",
           f"- Execution timing: `{head['execution_timing']}`.",
           f"- Test B: stopped at the coverage stop (label `{tb['label']}`, p_B {tb['p_b']}). No low-risk book was "
           "built.", "",
           "## Test A", "",
           f"The decision reads the {a['decision_cell']['loader_run']} loader run with the "
           f"{a['decision_cell']['cost_case']} cost case. The last_close rerun is the R4 comparison and decides "
           f"nothing. With p_B = {tb['p_b']}, the Holm-adjusted p_A is min(1, 2 x p_A), so the Holm condition "
           f"(alpha {a['holm_alpha']}) needs p_A <= {tb['p_a_max_for_holm']}. The stop rule stops the line when the "
           f"confirm annual mean against SPY is below {a['confirm_floor']} a year, whatever the label.", ""]
    rows = []
    for run, r in a["runs"].items():
        rows.append([run, num(r["p_a"], 4), num(r["holm"]["A"], 4), yes(r["holm_p_at_most_alpha"]),
                     *mean_cells(r["confirm_means"]), *mean_cells(r["cost_2x_means"]), r["stop"] or "none",
                     *mean_cells(r["check_means"]), f"`{r['decide_a']['label']}`"])
    out += table(["Loader run", "p_A", "Holm p_A", "Holm condition", "Confirm vs SPY", "Confirm vs CW-PIT",
                  "2x vs SPY", "2x vs CW-PIT", "Stop rule", "Check vs SPY", "Check vs CW-PIT", "Label"], rows)
    out += ["Conditions of `decide_a`:", ""]
    out += table(["Condition", *RUNS], [[c, *(yes(a["runs"][run]["decide_a"]["conditions"][c]) for run in RUNS)]
                                        for c in a["runs"]["primary"]["decide_a"]["conditions"]])
    out += [f"R4 fragility of test A (a sign flip of an active annual mean of the composite, confirm or check, "
            f"against SPY or CW-PIT, either cost case): {'fragile' if a['fragile'] else 'no sign flip'}. The label "
            "stays.", "", "Composite test records, confirm months (annual means, HAC t, one-sided p):", ""]
    rows = []
    for run in RUNS:
        for case in CASES:
            r = a["records"][run][case]
            rows.append([run, case, r["vs_spy"]["months"], r.get("blank_reason_counts", {}).get(d.BLANK, 0),
                         pct(r["vs_spy"]["annual_mean"], 3), num(r["vs_spy"]["hac_t"]), num(r["vs_spy"]["p_one_sided"], 4),
                         pct(r["vs_cw"]["annual_mean"], 3), num(r["vs_cw"]["hac_t"]), num(r["vs_cw"]["p_one_sided"], 4),
                         num(r["p_a"], 4)])
    out += table(["Loader run", "Cost case", "Months", "Blank months", "Mean vs SPY", "t vs SPY", "p vs SPY",
                  "Mean vs CW-PIT", "t vs CW-PIT", "p vs CW-PIT", "p_A"], rows)
    out += ["## Limitations", "", *(f"- {line}" for line in doc["limitations"]), ""]
    out += secondary_section(confirm)
    out += family_section(confirm)
    out += oi09_section(doc)
    out += check_section(doc)
    out += provenance_section(doc)
    out += owed_section(doc)
    out += ["## Withheld values", "", *(f"- `{k}`: {v}" for k, v in doc["missing"].items()), ""]
    return "\n".join(out).rstrip("\n") + "\n"


def secondary_section(confirm: Mapping[str, Any]) -> list[str]:
    sec = confirm["secondary"]
    first = sec["primary"]["primary"]
    out = ["## Secondary family", "",
           f"Test A statistics of each member over the confirm months, with Benjamini-Yekutieli q-values (family size "
           f"{first['family_size']}). The family decides nothing. The rows are in ID order and are not a ranking. A "
           "member with zero or undefined TE or t is typed undefined and keeps its place in the family size.", ""]
    rows = []
    for run in RUNS:
        for case in CASES:
            cell = sec[run][case]
            for name in d.SECONDARY:
                if name in cell["members"]:
                    m = cell["members"][name]
                    rows.append([name, run, case, m["vs_spy"]["months"], pct(m["vs_spy"]["annual_mean"], 3),
                                 num(m["vs_spy"]["hac_t"]), pct(m["vs_cw"]["annual_mean"], 3), num(m["vs_cw"]["hac_t"]),
                                 num(m["p_a"], 4), num(m["q_by"], 4)])
                elif name in cell["undefined"]:
                    rows.append([name, run, case, "", "", "", "", "", f"`{cell['undefined'][name]['undefined_reason']}`",
                                 ""])
    out += table(["Member", "Loader run", "Cost case", "Months", "Mean vs SPY", "t vs SPY", "Mean vs CW-PIT",
                  "t vs CW-PIT", "p_A", "q (BY)"], rows)
    return out


def family_section(confirm: Mapping[str, Any]) -> list[str]:
    fam = confirm["family_a_screen"]
    out = ["## Family A baseline", "",
           "Over the confirm months the baseline is a member of the secondary family (above). Over the screen "
           f"months {crit.SCREEN_START} to {crit.SCREEN_END} it runs with the screen cost schedule and the look's "
           "blank set. It is not in the freeze. Against CW-PIT and against vwretd:", ""]
    rows = []
    for run in RUNS:
        for case in CASES:
            r = fam["records"][run][case]
            s, v = r["screen_record"], r["tilt_vs_vwretd"]
            rows.append([run, case, s["months"], s["status"], pct(s["annual_active_mean"], 3), num(s["information_ratio"]),
                         num(s["hac_t"]), pct(v["annual_mean_gap"], 3), pct(v["annual_te"], 3)])
    out += table(["Loader run", "Cost case", "Months", "Record", "Mean vs CW-PIT", "IR", "HAC t", "Mean gap vs vwretd",
                  "TE vs vwretd"], rows)
    out += ["R4 fragility over the screen months: " + "; ".join(
        f"{case} {'fragile' if any(v['fragile'] for v in f.values()) else 'no sign flip'}"
        for case, f in fam["fragility"].items()) + ".", ""]
    return out


def oi09_section(doc: Mapping[str, Any]) -> list[str]:
    out = ["## OI-09: CW-PIT against SPY", "",
           f"{doc['header']['benchmarks']['decomposition']}. Annual means over the months with values of each stage:",
           ""]
    rows = []
    for stage, part in doc["stages"].items():
        for run in RUNS:
            for case in CASES:
                o = part["oi09"][run][case]
                g, t = o["cw_vs_spy"], o["decomposition"]
                rows.append([stage, run, case, g["months"], pct(g["annual_mean_gap"], 3), pct(g["annual_te"], 3),
                             num(g["correlation"], 5), pct(t["tilt_vs_spy"], 3), pct(t["tilt_vs_cw"], 3)])
    out += table(["Stage", "Loader run", "Cost case", "Months", "CW-PIT - SPY", "TE", "Correlation", "TILT - SPY",
                  "TILT - CW-PIT"], rows)
    return out


def check_section(doc: Mapping[str, Any]) -> list[str]:
    check = doc["stages"]["check"]
    months = check["series_months"]
    parts = Counter(check["check_gap_months"].values())
    out = ["## Check stage", "",
           f"- `check_period_end`: {check['check_period_end']}.",
           f"- Series months: {months['first']} to {months['last']}, {months['count']} months, "
           f"{months['gap_months_in_series']} of them in `CHECK_GAP_MONTHS`.",
           "- `check_gap_months` (left out of every check series): " + "; ".join(
               f"{p} {', '.join(m for m, q in check['check_gap_months'].items() if q == p)}" for p in parts) + ".",
           "", "Check means of every signal set (annual means over the check months with values):", ""]
    rows = [[s, run, case, *mean_cells(check["means"][s][run][case])]
            for s in SETS if s in check["means"] for run in RUNS for case in CASES]
    out += table(["Signal set", "Loader run", "Cost case", "Mean vs SPY", "Mean vs CW-PIT"], rows)
    return out


def provenance_section(doc: Mapping[str, Any]) -> list[str]:
    prov, run, costs = doc["provenance"], doc["runs"], doc["costs"]
    out = ["## Provenance", ""]
    rows = [["Trial file", f"`{prov['trial_file']}`, SHA-256 `{prov['trial_sha256']}`"],
            ["Data vintage", prov["data_vintage"]]]
    for name, m in prov["manifests"].items():
        rows.append([f"Manifest, {name.replace('_', ' ')}", f"`{m['file']}`, SHA-256 `{m['file_sha256']}`, "
                     f"{m['main_files']} main files, {m['main_rows']} main rows"])
    rows += [["Data files SHA-256 (both pulls)", f"`{prov['data_files_sha256']}`"],
             ["Run 2 freeze digest (amendment 3)", f"`{prov['run2_digest_sha256']}`"],
             ["Run 4 code", f"commit `{run['code_commit']}`, code SHA-256 `{run['code_sha256']}`"],
             ["Run 4 run log SHA-256", f"`{prov['run_log_sha256']}`"],
             *([f"Run 4 {stage}.json", f"`{digest}`"] for stage, digest in run["stage_sha256"].items())]
    out += table(["Item", "Value"], rows)
    out += ["Pinned files of run 4 (SHA-256):", "",
            *table(["File", "SHA-256"], [[f"`{p}`", f"`{v}`"] for p, v in sorted(run["code_pins_sha256"].items())]),
            "## Costs", "",
            "Confirm and check runs: " + "; ".join(
                f"from {r[0] or 'the first row'}, commission {r[1]:g} and spread {r[2]:g} bp" for r in costs["schedule"])
            + f" ({costs['basis']}). Every book pays the half-spread override: {costs['half_spread_override']}",
            "", f"Cost cases: {', '.join(f'{k} x{v:g}' for k, v in costs['scales'].items())}. Borrow: "
            f"{costs['borrow']}. The Family A baseline over the screen months uses the screen cost schedule with no "
            "override.", "",
            "## Runs and attempts (R9)", "",
            f"Run 4 ran every stage again from coverage, on the code of amendment 4, into a new folder, as amendment 4 "
            f"states. It froze `{run['freeze_decision']}` with the shortlist {', '.join(run['shortlist'])} and the "
            "run 2 digest. Attempts in the run log: " + ", ".join(f"{k} {v}" for k, v in sorted(run["attempts"].items()))
            + f". `reports/{ATTEMPTS_JSONL}` has one line per attempt of run 4, after the reference lines of run 1 and "
            f"run 2 (`{SCREEN_ATTEMPTS}`) and of run 3. Run 3 wrote the stages "
            + ", ".join(s for s, o in RUN_3["stages"].items() if o == "written")
            + f", and its confirm stage refused (`{RUN_3['reason']}`), so it has no confirm or check file (see "
            f"`{RUN_3['see']}`, entry '{RUN_3['entry']}').", ""]
    return out


def owed_section(doc: Mapping[str, Any]) -> list[str]:
    """The reports owed by segment: the composite run and CW-PIT in tables; the JSON holds every signal set."""
    out = ["## Reports owed", "",
           "Each item of design note section 5 is in the JSON under `stages.<stage>.segments.<segment>`, for every "
           "signal set, both loader runs, and both cost cases. The tables give the composite run.", ""]
    for stage, part in doc["stages"].items():
        flips = [f"{s} {case}" for s, cases in part["fragility"].items() for case, f in cases.items()
                 if any(v["fragile"] for v in f.values())]
        out += [f"fragility, {stage} stage (a sign flip of an active annual mean against SPY or CW-PIT between the "
                "primary run and the last_close rerun, R4): " + (", ".join(flips) or "none") + ".", ""]
        for name, seg in part["segments"].items():
            s = seg["segment"]
            out += [f"### Segment {name}", "",
                    f"Months {s['first']} to {s['last']}; anchor {s['anchor']}, first rebalance {s['first_rebalance']}, "
                    f"end row {s['end']}.", ""]
            out += segment_tables(seg)
        out += [f"Stage {stage}: `bid_ask_midpoint_share` {num(part['bid_ask_midpoint_share'], 4)} of the member-days "
                "of its segments.", ""]
        out += me_table(part["me_coverage"], stage)
    rule = doc["stages"]["check"]["s2_history_rule"]
    out += ["### s2_history_rule (check stage)", "",
            "S2 member quarters with rdq before 2020-08-03 and a known date on or after it (no S2 value): " + (", ".join(
                f"{y} {n}" for y, n in rule["seal_quarters_by_year"].items()) or "none") + ". S2 cells typed "
            "`split_in_basis_window` by year: " + (", ".join(
                f"{y} {n}" for y, n in rule["split_in_basis_window_by_year"].items() if n) or "none") + ".", ""]
    valid = rule["valid_share_by_post_seal_month"]
    out += ["S2 valid share by post-seal check month: " + ", ".join(f"{m} {num(v, 3)}" for m, v in valid.items()) + ".",
            ""]
    return out


def segment_tables(seg: Mapping[str, Any]) -> list[str]:
    composite = d.COMPOSITE
    out = []
    blank = seg["blank_months"]
    out += [f"Blank months (`{d.BLANK}`): " + "; ".join(
        f"{run} {v['count']} (share {v['share']:.4f})" for run, v in blank.items()) + ". By year (primary run): "
        + (", ".join(f"{y} {n}" for y, n in blank["primary"]["by_year"].items()) or "none") + ".", ""]
    level = seg["r4"]["weight_level"]
    out += [f"r4, CW-PIT held disappearances by cause (weights: {level}; the public weight rule gives weight sums "
            "for the CW-PIT book only):", ""]
    rows = []
    for run in RUNS:
        for case in CASES:
            r = seg["r4"][RUN_LEVEL][run][case]
            rows.append([run, case, r["held"], num(r.get("incoming_weight_sum"), 4),
                         num(r.get("weight_at_last_rebalance_sum"), 4), rep.r4_cells(r)])
    out += table(["Loader run", "Cost case", "Held", "Weight at the event, sum", "Weight at the last rebalance, sum",
                  "By cause"], rows)
    rows = [[run, case, seg["r4"]["tilt"][composite][run][case]["held"], rep.r4_cells(seg["r4"]["tilt"][composite][run][case])]
            for run in RUNS for case in CASES]
    out += ["r4, composite TILT (counts only):", ""]
    out += table(["Loader run", "Cost case", "Held", "By cause"], rows)
    pb = seg["path_break"]
    rows = []
    for key, v in [*((f"CW-PIT, {run}", v) for run, v in pb[RUN_LEVEL].items()),
                   *((f"{composite}, {run}", v) for run, v in pb["sets"][composite].items())]:
        span = v["span_months"] or {"min": "none", "median": "none", "max": "none"}
        rows.append([key, v["position_count"], v["months"],
                     num(v["weight_sum"]["cw"], 4) if "weight_sum" in v else "not given",
                     classes(v["by_exit_class"]), f"{span['min']} / {span['median']} / {span['max']}"])
    out += ["path_break (aggregates only):", ""]
    out += table(["Book set", "Positions", "Months blanked", "CW weight sum", "By later exit class",
                  "Span min / median / max"], rows)
    out += ["Blanked level windows (R6), by later exit class:", ""]
    out += table(["Loader run", "Windows", *EXITS], [[run, v["windows"], *(v["by_exit_class"][c] for c in EXITS)]
                                                    for run, v in pb["blanked_level_windows"].items()])
    out += ["exit_gap_events, the amendment 4 events (an index exit on a row without a close). Held means that CW-PIT "
            "holds the member at the last rebalance before the event. Again means a close, or eligibility, on a later "
            "row of the segment.", ""]
    rows = []
    for run, v in seg["exit_gap"][RUN_LEVEL].items():
        rows.append([run, v["events"], classes(v["events_by_exit_class"]), v["held"], classes(v["held_by_exit_class"]),
                     num(v[EXIT_GAP_WEIGHT], 4) if EXIT_GAP_WEIGHT in v else "not given", v["priced_again"],
                     v["held_priced_again"], v["eligible_again"], v["d6_left_out"]])
    out += table(["Loader run", "Events", "By later exit class", "Held", "Held, by later exit class",
                  "Held CW weight sum", "Priced again", "Held and priced again", "Eligible again", "D6 left out"], rows)
    out += ["r6, pool cells by later exit class over the rebalances (cells; share of pool cells), primary loader "
            "run:", ""]
    m = seg["r6"]["members"]["primary"]
    rows = [rep.by_class("pool cells", m["pool_cells"])]
    for reason, v in m["me_missing"].items():
        rows.append(rep.by_class(f"ME missing, {reason}", {c: f"{v['cells'][c]} ({num(v['share'][c], 4)})"
                                                            for c in EXITS}))
    for key in ("unpriced", "basis_unseen", "blanked_windows"):
        rows.append(rep.by_class(key.replace("_", " "), {c: f"{m[key]['cells'][c]} ({num(m[key]['share'][c], 4)})"
                                                         for c in EXITS}))
    out += table(["Item", *EXITS], rows)
    out += ["counts and b2, composite run:", ""]
    out += rep.counts_table({run: seg["counts"][composite][run] for run in RUNS}, "Loader run")
    rows = []
    for run in RUNS:
        for case in CASES:
            t = seg["tilt_stats"][composite][run][case]
            rows.append([run, case, pct(t["realized_te_daily"]), pct(t["worst_relative_drawdown"]),
                         num(t["size_exposure_mean"]), num(t["annual_turnover"]["tilt"]),
                         num(t["annual_turnover"]["active"]), pct(t["annual_cost_drag"]["tilt"], 3),
                         pct(t["annual_cost_drag"]["active"], 3)])
    out += ["tilt_stats, composite (the JSON has the active turnover and cost drag per year):", ""]
    out += table(["Loader run", "Cost case", "Realized TE (daily)", "Worst relative drawdown", "Size exposure mean",
                  "Turnover TILT", "Turnover active", "Cost drag TILT", "Cost drag active"], rows)
    rows = [[p["publication_year"], p["months_after"], p["months_before"], pct(p["annual_mean_after"], 3),
             pct(p["annual_mean_before"], 3)] for p in seg["post_publication_split"][composite]["primary"]["primary"]]
    out += ["post_publication_split, composite, primary loader run and cost (active months after and before each "
            "publication year of its signals):", ""]
    out += table(["Publication year", "Months after", "Months before", "Annual active mean after",
                  "Annual active mean before"], rows)
    out += half_spread_table(seg)
    rows = [[y, num(v["short_history_share"], 4), num(v["mean_me_percentile_short_history"], 4),
             num(v["mean_me_percentile_valid"], 4)] for y, v in seg["s2_short_history"].items()]
    out += ["s2_short_history by year (share of S2 member cells typed `short_history`; mean ME percentile of S2 "
            "`short_history` and valid members):", ""]
    out += table(["Year", "short_history share", "Mean ME percentile, short_history", "Mean ME percentile, valid"],
                 rows)
    return out


def classes(counts: Mapping[str, int]) -> str:
    """Nonzero counts by later exit class."""
    return ", ".join(f"{c} {n}" for c, n in counts.items() if n) or "none"


def half_spread_table(seg: Mapping[str, Any]) -> list[str]:
    """The half-spread tables of the composite TILT and CW-PIT, primary loader run and cost."""
    out = ["half_spread, primary loader run and primary cost (shares of the year's traded notional; the band of "
           "the largest half-spread of a valid traded cell; the spread cost above the schedule as a share of book "
           "value; invalid traded cells):", ""]
    rows = []
    for book, years in (("TILT", seg["half_spread"]["tilt"][d.COMPOSITE]["primary"]["primary"]),
                        ("CW-PIT", seg["half_spread"]["cw_pit"]["primary"]["primary"])):
        for year, v in years.items():
            invalid = sum(n for r in v["invalid_traded_cells_by_exit_class"].values() for n in r.values())
            rows.append([book, year, num(v["notional_share_by_status"]["valid"], 4), num(v["crsp_binds_share"], 4),
                         num(v["bid_ask_share"], 4), v["max_half_spread_band_bp"] or "none",
                         pct(v["cost_above_schedule"], 4), invalid])
    out += table(["Book", "Year", "Valid share", "CRSP binds share", "BA share", "Largest half-spread, bp",
                  "Cost above schedule", "Invalid cells"], rows)
    return out


def me_table(me: Mapping[str, Any], stage: str) -> list[str]:
    head = ["Member days", "Present days", "Dollar volume share present"]
    out = [f"me_coverage, {stage} stage, by later exit class (the JSON has each reason, by year, and the "
           "`basis_unseen` member-days by year):", ""]
    out += table(["Class", *head], [[c, v["member_days"], v["days_present"], num(v["dv_share_present"], 6)]
                                    for c, v in me["by_exit_class"].items()])
    unseen = me["basis_unseen_member_days_by_year"]
    out += ["`basis_unseen` member-days by year: " + "; ".join(
        f"{case} " + (", ".join(f"{y} {n}" for y, n in v.items()) or "none") for case, v in unseen.items()) + ".", ""]
    return out


# Outputs ----------------------------------------------------------------------------------

def check_output(doc: Mapping[str, Any], texts: Mapping[str, str]) -> None:
    """The output guard: no private key (per-position rows, identifiers, single maxima, per-cell trade weights), a
    weight sum only under ``RUN_LEVEL``, per-year turnover and cost drag of the active book only, no attempt detail,
    no private path, and no text that calls the result a confirmation or claims a profit."""
    def walk(value: Any, path: tuple) -> None:
        if isinstance(value, Mapping):
            for k, v in value.items():
                if k in PRIVATE_KEYS:
                    raise refuse("private_field_in_output", k)
                if k in WEIGHTS and RUN_LEVEL not in path:
                    raise refuse("private_field_in_output", f"{k} outside {RUN_LEVEL}")
                if k in BY_YEAR and set(v) != {"active"}:
                    raise refuse("private_field_in_output", f"{k} of one book")
                walk(v, (*path, k))
        elif isinstance(value, list):
            for v in value:
                walk(v, path)
    walk(doc, ())
    if any("detail" in json.loads(line) for line in texts[ATTEMPTS_JSONL].splitlines()):
        raise refuse("private_field_in_output", "attempt detail")
    if any(rep.PRIVATE_TEXT.search(text) for text in texts.values()):
        raise refuse("private_path_in_output", "an output text holds a private path")
    label = doc["header"]["run_label"]
    for text in texts.values():
        rest = text.replace(label, "")
        for phrase in NO_CLAIM:
            rest = re.sub(phrase, "", rest, flags=re.IGNORECASE)
        if CLAIM.search(rest):
            raise refuse("claim_in_output", CLAIM.search(rest).group(0))


def outputs(doc: Mapping[str, Any], attempts: list[Mapping[str, Any]]) -> dict[str, str]:
    texts = {REPORT_JSON: json.dumps(doc, indent=1, sort_keys=True, allow_nan=False) + "\n",
             REPORT_MD: render(doc),
             ATTEMPTS_JSONL: "".join(json.dumps(a, sort_keys=True, allow_nan=False) + "\n" for a in attempts)}
    check_output(doc, texts)
    return texts


def main(argv: list[str] | None = None, out: Path = d.REPO / "reports") -> int:
    parser = argparse.ArgumentParser(description="Write the public M5.5 confirm and check report from the run 4 stage "
                                                 "folder (aggregates only).")
    parser.add_argument("run_4", type=Path, help="the run 4 stage folder (all seven stage files and run_log.jsonl)")
    args = parser.parse_args(argv)
    try:
        texts = outputs(*build(args.run_4))
    except RunnerStop as exc:
        print(f"refused: {exc.reason}: {exc.detail}", file=sys.stderr)
        return 1
    for name, text in texts.items():
        (Path(out) / name).write_text(text, encoding="utf-8")
    print("\n".join(f"wrote reports/{name}" for name in texts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
