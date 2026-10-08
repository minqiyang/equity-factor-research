"""Synthetic tests for the public M5.5 confirm and check report (card m55-conrep, prod-m55conrep-1).

The stage files are made here with ``m55_driver.write_stage``; no test reads real data. One small run stands in for
run 3 (all seven stages and a run log). Its first four stages come from the screen report tests, and its confirm and
check stages have the shape that ``m55_driver.confirm_stage`` and ``check_stage`` write, with per-position rows, so
the tests can check that the report keeps only their aggregates. ``test_m55_confirm`` runs the report on the
long-world chain of the driver itself.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import research.m55_confirm_report as rep3
import research.m55_driver as d
import research.m55_screen_report as rep
import research.m55_wrds_loader as w
from m55_bytes_support import module_at
from research import m55_criteria as crit
from research.m4_7_sp500_pit_rerun import RunnerStop
from research.m55_index_tilt import ME_REASONS, QUOTE_REASONS
from test_m55_screen_report import keys, per, results


RUNS, CASES, EXITS = d.RUNS, d.CASES, w.EXIT_CLASSES
MAIN_BEFORE = "b1b0517294247e92de6734916fa84937c1351622"     # main before this card: the screen report bytes
USERS, HOME = "/Users", "/home"     # split so this file holds no literal home path
PER_POSITION = rep.FORBIDDEN | rep.SINGLE_MAX | {"traded_notional", "traded_notional_by_status", "max_half_spread",
                                                 "cw_weight_by_exit_class"}


def trial() -> dict:
    return d.load_trial()[0]


def tracked() -> tuple[dict, dict]:
    return (json.loads((d.REPO / d.TRACKED_MANIFEST).read_text()),
            json.loads((d.REPO / d.QUOTE_MANIFEST).read_text()))


def context(**change) -> dict:
    """The run 3 context the report accepts: merged trial, tracked data, trial code pins, code of main b1b0517."""
    data_sha = rep3.data_digest(trial(), *tracked())
    pins = d.context(trial(), d.TRIAL_SHA256, data_sha)["code_pins_sha256"]
    return {"trial_sha256": d.TRIAL_SHA256, "data_files_sha256": data_sha, "code_pins_sha256": pins,
            "code_sha256": rep3.RUN_3["code_sha256"], **change}


def r4(held: dict[str, int], run: str) -> dict:
    """An R4 record of the driver (``r4_counts``) with ``held`` events by cause, 0.01 weight each."""
    def settle(n: int) -> dict:
        return ({"settled_at_last_close": n} if run == "last_close" else
                {"ciz_return_in_path": n, "supplied_terminal_return": 0, "missing_engine_default": 0})
    total = sum(held.values())
    return {"held": total, "incoming_weight_sum": 0.01 * total, "incoming_weight_max": 0.01,
            "by_cause": {c: {"held": held.get(c, 0), "weight_at_last_rebalance_sum": 0.01 * held.get(c, 0),
                             **settle(held.get(c, 0))} for c in ("cash_merger", "failure", "unknown")}}


def position(k: int, exit_class: str = "failure") -> dict:
    return {"break_row": f"1995-0{k + 3}-01", "previous_valid_row": f"1995-0{k + 2}-28",
            "months": [f"1995-0{k + 3}"], "exit_class": exit_class,
            "weight_at_last_rebalance": {"cw": 0.001 * (k + 1), "tilt": 0.002 * (k + 1)}}


def year_spread(max_half_spread: float | None = 37.5) -> dict:
    """One book-year of ``half_spread_report``: one quote_crossed cell, two no_quote_row cells."""
    invalid = {r: per(0) for r in QUOTE_REASONS}
    invalid["quote_crossed"] = {**per(0), "failure": 1}
    invalid["no_quote_row"] = {**per(0), "current": 2}
    return {"traded_notional": 1.25, "traded_notional_by_status": {"valid": 1.0, "no_quote_row": 0.2,
                                                                   "quote_missing": 0.0, "quote_one_sided": 0.0,
                                                                   "quote_nonpositive": 0.0, "quote_crossed": 0.05},
            "crsp_binds_share": 0.3, "bid_ask_share": 0.01, "max_half_spread": max_half_spread,
            "cost_above_schedule": 0.0004, "invalid_traded_cells_by_exit_class": invalid}


def segment(name: str, period: str, first: str, last: str, held: dict, positions: dict) -> dict:
    """One ``run_segment`` result: every signal set, both loader runs, both cost cases, each report owed."""
    stats = {"realized_te_daily": 0.02, "worst_relative_drawdown": -0.03, "size_exposure_mean": 0.01,
             "annual_turnover": {"tilt": 1.5, "cw": 0.5, "active": 1.0},
             "annual_cost_drag": {"tilt": 0.006, "cw": 0.002, "active": 0.004},
             "turnover_by_year": {k: {first[:4]: v} for k, v in (("tilt", 1.5), ("cw", 0.5), ("active", 1.0))},
             "cost_drag_by_year": {k: {first[:4]: v} for k, v in (("tilt", 0.006), ("cw", 0.002), ("active", 0.004))},
             "post_publication": [{"publication_year": 1989, "months_after": 36, "months_before": 0,
                                   "annual_mean_after": 0.006, "annual_mean_before": None}]}
    counts = {"rebalances": 37, "members_mean": 500.0, "members_min": 499, "traded_mean": 500.0, "traded_min": 499,
              "pinned_mean": 10.0, "c_zero_few_signals": 3, "c_zero_short_history": 1, "c_zero_window_gap": 1,
              "me_missing": 0, **{f"me_missing_{r}": 0 for r in ME_REASONS}, "settled_excluded": 0,
              "share_cap_at_final_weights": 0.0, "share_te_scaled": 0.0,
              "b2": {"rebalances": 1, "excluded": 1, "max_cw_share": 0.002,
                     "each": [{"date": "1996-03-29", "excluded": 1, "cw_share": 0.002}]}}
    c_zero = {"member_cells": per(5), **{k: {"cells": per(1), "share": per(0.2)}
                                         for k in ("few_signals", "short_history", "window_gap")}}
    shares = {"cells": per(0), "share": per(0.0)}
    sets = {}
    for s in rep3.SETS:
        item = {"records": {run: {case: {"tilt_stats": stats, "r4": {"cw": r4(held[run], run), "tilt": r4(held[run], run)},
                                         "half_spread": {book: {first[:4]: year_spread()} for book in ("cw", "tilt")}}
                                  for case in CASES} for run in RUNS},
                "path_break_positions": positions, "counts": {run: counts for run in RUNS}}
        if s in d.SECONDARY[:-1]:
            item["c_zero_by_exit_class"] = {run: c_zero for run in RUNS}
        sets[s] = item
    months = sorted({m for p in positions["primary"] for m in p["months"]})
    runs = {run: {"blank_months": months, "blank_month_count": len(months), "blank_month_share": len(months) / 254,
                  "positions": [{**p, "weight_at_last_rebalance": {"cw": p["weight_at_last_rebalance"]["cw"]}}
                                for p in positions[run]],
                  "positions_by_exit_class": per(0), "cw_weight_by_exit_class": per(0.0),
                  "blanked_level_windows": {"windows": 1, "by_exit_class": {**per(0), "failure": 1},
                                            "each": [{"rebalance": "1995-03-31", "exit_class": "failure",
                                                      "break_rows": ["1995-04-03"]}]},
                  "r6_members": {"pool_cells": per(10), "me_missing": {m: shares for m in ME_REASONS},
                                 **{k: shares for k in ("unpriced", "basis_unseen", "blanked_windows")}}}
            for run in RUNS}
    return {"segment": {"name": name, "period": period, "first": first, "last": last, "anchor": "1992-12-31",
                        "first_rebalance": "1993-01-29", "end": "2014-03-31"},
            "runs": runs, "sets": sets,
            "signals_r6": {s: {"reason_counts_by_year": {first[:4]: {"valid": 5}},
                               "reason_share_by_exit_class": {"valid": per(1.0)}} for s in d.SECONDARY[:-1]},
            "s2_short_history": {first[:4]: {"short_history_share": 0.1, "mean_me_percentile_short_history": 0.4,
                                             "mean_me_percentile_valid": 0.5}},
            "s2_valid_share_by_month": {first: 0.9}, "s2_split_in_basis_window_by_year": {first[:4]: 0},
            "s2_basis_quarters_by_year": {first[:4]: {"changed": 0, "same": 3, "unread": 0}}}


def a_record(spy: float, cw: float) -> dict:
    def side(mean: float) -> dict:
        return {"months": 252, "annual_mean": mean, "hac_t": 2.4, "p_one_sided": 0.008}
    return {"vs_spy": side(spy), "vs_cw": side(cw), "p_a": 0.012, "blank_months": {"1995-03": d.BLANK},
            "blank_reason_counts": {d.BLANK: 1}}


def means(spy: float, cw: float) -> dict:
    return {"vs_spy": spy, "vs_cw": cw, "blank_months": {"1995-03": d.BLANK}, "blank_reason_counts": {d.BLANK: 1}}


def fragility() -> dict:
    return {s: {case: {k: {"primary": 0.004, "last_close": 0.004, "fragile": False} for k in ("vs_spy", "vs_cw")}
                for case in CASES} for s in rep3.SETS}


def oi09() -> dict:
    gap = {"months": 252, "annual_mean_gap": -0.001, "annual_te": 0.004, "correlation": 0.999,
           "book_annual_mean": 0.1, "benchmark_annual_mean": 0.101, "blank_months": {"1995-03": d.BLANK},
           "blank_reason_counts": {d.BLANK: 1}}
    return {run: {case: {"cw_vs_spy": gap, "decomposition": {"tilt_vs_spy": 0.004, "tilt_vs_cw": 0.005,
                                                             "cw_vs_spy": -0.001}} for case in CASES} for run in RUNS}


def me_coverage() -> dict:
    row = {"member_days": 10, "days_present": 10, **{f"days_{r}": 0 for r in ME_REASONS},
           "dv_share_present": 1.0, **{f"dv_share_{r}": 0.0 for r in ME_REASONS}}
    return {"by_year": {"1993": row}, "by_exit_class": per(row),
            "basis_unseen_member_days_by_year": {"data_start": {}, "seal": {"2021": 4}}}


def stage_results(frozen: dict, header: dict) -> tuple[dict, dict]:
    """Confirm and check results with the driver's shape. Confirm CW-PIT: 9 and 12 held events (equal cash_merger
    counts in both loader runs) and 3 path-break positions in each run; the pre-seal segment has 1 event and 1
    position; the post-seal segment has none."""
    big = {"primary": {"cash_merger": 5, "failure": 4}, "last_close": {"cash_merger": 5, "failure": 7}}
    three = {run: [position(0), position(1), position(2, "cash_merger")] for run in RUNS}
    one = {"primary": {"failure": 1}, "last_close": {"failure": 1}}
    confirm_part = segment("confirm", "confirm", "1993-02", "2014-03", big, three)
    pre = segment("check_pre_seal", "check", "2014-04", "2019-06", one, {run: [position(0)] for run in RUNS})
    post = segment("check_post_seal", "check", "2021-09", "2025-11", {run: {} for run in RUNS},
                   {run: [] for run in RUNS})
    decision = {"p_a": 0.012, "p_b": 1.0, "holm": crit.holm_primary(0.012, 1.0), "holm_p_at_most_alpha": True,
                "confirm_means": {"vs_spy": 0.004, "vs_cw": 0.005}, "cost_2x_means": {"vs_spy": 0.002, "vs_cw": 0.003},
                "stop": crit.stop_after_confirm(0.004)}
    undefined = {"status": "undefined", "undefined_reason": "statistic_undefined", "detail": "HAC t is undefined"}
    members = {s: {**a_record(0.004, 0.005), "q_by": 0.1} for s in d.SECONDARY if s != "S5"}
    secondary = {run: {case: {"members": members, "family_size": 9, "decides_nothing": True,
                              "note": crit.SECONDARY_NOTE, "undefined": {"S5": undefined}} for case in CASES}
                 for run in RUNS}
    screen_record = {"status": "ok", "first_month": "1963-07", "last_month": "1992-12", "months": 352,
                     "annual_active_mean": 0.002, "annual_te": 0.01, "information_ratio": 0.2, "hac_t": 1.1,
                     "p_one_sided": 0.13, "annual_turnover": 1.4, "blank_months": {"1967-07": d.BLANK},
                     "blank_reason_counts": {d.BLANK: 1}}
    gap = oi09()["primary"]["primary"]["cw_vs_spy"]
    family = {"records": {run: {case: {"screen_record": screen_record, "tilt_vs_vwretd": gap,
                                       "r4": {"cw": r4(big[run], run), "tilt": r4(big[run], run)}}
                                for case in CASES} for run in RUNS},
              "counts": {run: confirm_part["sets"][d.COMPOSITE]["counts"][run] for run in RUNS},
              "fragility": {case: {k: {"primary": 0.002, "last_close": 0.002, "fragile": False}
                                   for k in ("tilt_vs_cw", "tilt_vs_vwretd")} for case in CASES}}
    all_means = {s: {run: {case: means(0.004, 0.005) for case in CASES} for run in RUNS} for s in rep3.SETS}
    confirm = {"header": header, "digest_sha256": frozen["digest_sha256"], "shortlist": frozen["shortlist"],
               "segment": confirm_part,
               "test_a": {"decision": decision, "last_close": decision,
                          "records": {run: {case: a_record(0.004, 0.005) for case in CASES} for run in RUNS}},
               "means": all_means, "fragility": fragility(), "secondary": secondary, "oi09": oi09(),
               "family_a_screen": family, "me_coverage": me_coverage(), "bid_ask_midpoint_share": 0.001}
    label = crit.decide_a(decision["holm"]["A"], decision["confirm_means"], decision["cost_2x_means"],
                          {"vs_spy": 0.004, "vs_cw": 0.005})
    gap_months = {str(m): part for part, first, end in d.GAP_PARTS for m in
                  crit.CHECK_GAP_MONTHS[(crit.CHECK_GAP_MONTHS >= first) & (crit.CHECK_GAP_MONTHS <= end)]}
    check = {"header": header, "digest_sha256": frozen["digest_sha256"], "check_period_end": "2025-11",
             "check_gap_months": gap_months, "segments": {"check_pre_seal": pre, "check_post_seal": post},
             "series_months": {"first": "2014-04", "last": "2025-11", "count": 114, "gap_months_in_series": 0},
             "test_a": {"label": label, "last_close": label, "fragile": False, "confirm_stop": decision["stop"]},
             "means": all_means, "fragility": fragility(), "oi09": oi09(),
             "s2_history_rule": {"split_in_basis_window_by_year": {"2016": 1},
                                 "basis_quarters_by_year": {"2016": {"changed": 1, "same": 2, "unread": 0}},
                                 "seal_quarters_by_year": {"2020": 3},
                                 "valid_share_by_post_seal_month": {"2021-09": 0.8}},
             "me_coverage": me_coverage(), "bid_ask_midpoint_share": 0.002}
    return confirm, check


LOG = [{"stage": "confirm", "refused": "shortlist_digest_mismatch", "detail": f"seen at {USERS}/someone/x"},
       {"stage": "confirm", "error": "FileNotFoundError", "detail": f"no such file {HOME}/someone/y"}]


def write_run3(folder: Path, ctx: dict | None = None, edit=None, log: list | None = None) -> Path:
    """Write the seven stage files and the run log as the driver does, with test B in the later stages. ``edit``
    changes the results before they are written; ``log`` adds attempt lines before the confirm stage."""
    folder.mkdir(parents=True)
    ctx = context() if ctx is None else ctx
    found = results()
    frozen = crit.freeze_shortlist(found["screen"]["records_for_freeze"])
    found["freeze"] = {"record": frozen, "digest_sha256": frozen["digest_sha256"], "decision": frozen["decision"],
                       "shortlist": frozen["shortlist"]}
    found["confirm"], found["check"] = stage_results(frozen, d.header(trial()))
    if edit:
        edit(found)
    digests, lines = {}, []
    for stage in d.STAGES:
        result = found[stage]
        if stage == "freeze":
            (folder / "shortlist_digest.txt").write_text(frozen["digest_sha256"] + "\n")
        if "calibration" in digests:
            result = {**result, "test_b": d.record_test_b(found["calibration"], digests["calibration"])}
        if stage == "confirm":
            lines += LOG if log is None else log
        lines.append({"stage": stage, "call": "composite_test", "output": {}})
        digests[stage] = d.write_stage(folder, stage, ctx, dict(digests), result)
        lines.append({"stage": stage, "written": digests[stage]})
    (folder / "run_log.jsonl").write_text("".join(json.dumps(line) + "\n" for line in lines))
    return folder


@pytest.fixture()
def run2_digest(monkeypatch) -> None:
    """The synthetic freeze stands in for the run 2 freeze that amendment 3 states."""
    frozen = crit.freeze_shortlist(results()["screen"]["records_for_freeze"])["digest_sha256"]
    monkeypatch.setattr(d, "run2_digest", lambda trial: frozen)


@pytest.fixture()
def run3(tmp_path, run2_digest) -> Path:
    return write_run3(tmp_path / "private" / "run3")


def rewrite(folder: Path, stage: str, edit) -> None:
    """Edit one stage file and renew its own digest file (the chain after it is not renewed)."""
    payload = json.loads((folder / f"{stage}.json").read_text())
    edit(payload)
    text = json.dumps(payload, sort_keys=True, indent=1) + "\n"
    (folder / f"{stage}.json").write_text(text)
    (folder / f"{stage}.sha256").write_text(d.sha256_bytes(text.encode()) + "\n")


# The report ---------------------------------------------------------------------------------

def test_a_full_run_gives_three_aggregate_files_with_the_same_bytes_on_a_second_run(run3, tmp_path) -> None:
    out = [tmp_path / "out1", tmp_path / "out2"]
    for folder in out:
        folder.mkdir()
        assert rep3.main([str(run3)], out=folder) == 0
    files = sorted(p.name for p in out[0].iterdir())
    assert files == sorted([rep3.REPORT_JSON, rep3.REPORT_MD, rep3.ATTEMPTS_JSONL])
    assert all((out[0] / f).read_bytes() == (out[1] / f).read_bytes() for f in files)

    doc = json.loads((out[0] / rep3.REPORT_JSON).read_text())
    lines = [json.loads(line) for line in (out[0] / rep3.ATTEMPTS_JSONL).read_text().splitlines()]
    assert not (keys(doc) | keys(lines)) & PER_POSITION
    for f in files:
        text = (out[0] / f).read_text()
        assert "/Users/" not in text and "/home/" not in text and str(tmp_path) not in text
        assert "break_row" not in text and "1996-03-29" not in text and "37.5" not in text

    # R9: run 1 and run 2 by reference, then each attempt of run 3, without its detail text.
    screen_sha = d.sha256_bytes((d.REPO / rep3.SCREEN_ATTEMPTS).read_bytes())
    assert lines[:2] == [{"run": 1, "status": "stopped", "see": rep3.SCREEN_ATTEMPTS, "file_sha256": screen_sha},
                         {"run": 2, "status": "completed", "see": rep3.SCREEN_ATTEMPTS, "file_sha256": screen_sha}]
    run_3 = lines[2:]
    assert [(a["stage"], a["outcome"]) for a in run_3] == [
        *((s, "written") for s in d.STAGES[:5]), ("confirm", "refused"), ("confirm", "error"),
        ("confirm", "written"), ("check", "written")]
    assert run_3[5]["reason"] == "shortlist_digest_mismatch" and run_3[6]["reason"] == "FileNotFoundError"
    assert [a["attempt"] for a in run_3] == list(range(1, 10))
    assert doc["runs"]["attempts"] == {"error": 1, "refused": 1, "written": 7}
    assert doc["runs"]["stage_sha256"] == {s: (run3 / f"{s}.sha256").read_text().strip() for s in d.STAGES}

    # Test A, test B, and the R10 header.
    a = doc["test_a"]["runs"]["primary"]
    assert a["p_b"] == 1.0 and a["holm"]["A"] == pytest.approx(0.024) and a["holm_p_at_most_alpha"]
    assert a["decide_a"]["label"] == "met" and a["stop"] is None and a["check_means"]["vs_spy"] == 0.004
    assert doc["test_b"]["label"] == "stopped_coverage" and doc["test_b"]["p_a_max_for_holm"] == 0.025
    head = doc["header"]
    assert head["evidence_ceiling"] == "DIAGNOSTIC_ONLY"
    assert head["run_label"] == trial()["evidence_ceiling"]["run_label"]
    assert head["execution_timing"].startswith("after_close_signal_next_observed_close_v1")
    prov = doc["provenance"]
    assert prov["data_vintage"] == "2025-12-31" and prov["run2_digest_sha256"] == d.run2_digest(None)
    assert {m["file"] for m in prov["manifests"].values()} == {d.TRACKED_MANIFEST, d.QUOTE_MANIFEST}
    assert prov["manifests"]["second_pull_quotes"]["file_sha256"] == d.sha256_bytes(
        (d.REPO / d.QUOTE_MANIFEST).read_bytes())
    assert doc["runs"]["code_commit"] == MAIN_BEFORE

    # The secondary family keeps its BY q-value beside each member; S5 is typed undefined.
    cell = doc["stages"]["confirm"]["secondary"]["primary"]["primary"]
    assert cell["members"]["S1"]["q_by"] == 0.1 and cell["undefined"]["S5"]["undefined_reason"] == "statistic_undefined"
    assert doc["stages"]["check"]["check_period_end"] == "2025-11"
    assert len(doc["stages"]["check"]["check_gap_months"]) == 26


def test_the_public_weight_rule_on_nested_groups(run3) -> None:
    """Confirm CW-PIT: cash_merger 5 and 5 in the two loader runs (the stage files cannot show the same events),
    totals 9 and 12 (3 apart): totals only. Pre-seal: 1 event: no weight. Path breaks: 3 equal positions in both
    runs: a CW weight sum; 1 position: none. No signal set gets a weight, and no single maximum is given."""
    doc, _ = rep3.build(run3)
    confirm = doc["stages"]["confirm"]["segments"]["confirm"]
    pre = doc["stages"]["check"]["segments"]["check_pre_seal"]
    assert confirm["r4"]["weight_level"] == "total" and pre["r4"]["weight_level"] == "none"
    group = confirm["r4"][rep3.RUN_LEVEL]["last_close"]["sensitivity_2x"]
    assert group["weight_at_last_rebalance_sum"] == pytest.approx(0.12) and group["incoming_weight_sum"] == 0.12
    assert not rep.keys(group["by_cause"]) & rep.GROUP_WEIGHTS
    assert not rep.keys(pre["r4"][rep3.RUN_LEVEL]) & rep.GROUP_WEIGHTS
    assert confirm["path_break"]["weight_given"] and not pre["path_break"]["weight_given"]
    assert confirm["path_break"][rep3.RUN_LEVEL]["primary"]["weight_sum"] == {"cw": pytest.approx(0.006)}
    assert "weight_sum" not in pre["path_break"][rep3.RUN_LEVEL]["primary"]
    for seg in (confirm, pre):
        assert not rep.keys([seg["r4"]["tilt"], seg["path_break"]["sets"]]) & rep.GROUP_WEIGHTS
    assert not rep.keys(doc) & (rep.SINGLE_MAX | {"each", "positions", "path_break_positions"})
    assert {"r4.check.check_pre_seal.weight_at_last_rebalance_sum", "path_break.check.check_pre_seal.weight_sum",
            "r4.confirm.confirm.by_cause.weight_at_last_rebalance_sum"} <= set(doc["missing"])


@pytest.mark.parametrize("primary, shared, other, allowed", [
    (3, 3, 0, True), (3, 3, 1, False), (3, 3, 2, False), (3, 3, 3, True), (4, 3, 0, False), (2, 2, 0, False)])
def test_path_break_weights_need_three_positions_and_runs_equal_or_three_apart(primary, shared, other,
                                                                               allowed) -> None:
    """The last_close run holds ``shared`` positions of the primary run and ``other`` positions of its own."""
    first = [position(k) for k in range(primary)]
    second = first[:shared] + [position(k, "unknown") for k in range(other)]
    runs = {"primary": {"positions": first}, "last_close": {"positions": second}}
    found, given = rep3.path_break_runs(runs)
    assert given is allowed
    assert all(("weight_sum" in v) is allowed for v in found.values())


def test_half_spread_gives_shares_a_band_and_no_notional_sum() -> None:
    found = rep3.half_spread({"1995": year_spread(), "1996": year_spread(None)})
    year = found["1995"]
    assert sum(year["notional_share_by_status"].values()) == pytest.approx(1.0)
    assert year["notional_share_by_status"]["quote_crossed"] == pytest.approx(0.04)
    assert year["max_half_spread_band_bp"] == "20 to 50" and found["1996"]["max_half_spread_band_bp"] is None
    assert not set(year) & {"traded_notional", "traded_notional_by_status", "max_half_spread"}
    assert [rep3.band(x) for x in (0.0, 4.99, 5.0, 199.9, 200.0, 5000.0)] == [
        "0 to 5", "0 to 5", "5 to 10", "100 to 200", "200 or more", "200 or more"]


def test_the_text_never_calls_the_result_a_confirmation_or_claims_a_profit(run3) -> None:
    texts = rep3.outputs(*rep3.build(run3))
    label = trial()["evidence_ceiling"]["run_label"]
    assert "confirmation" in label and label in texts[rep3.REPORT_MD]
    for text in texts.values():
        rest = text.replace(label, "").lower()
        for word in ("confirmation", "confirmed", "confirms", "outperform", " beat"):
            assert word not in rest
        assert rest.count("profit") == rest.count("no profitability claim")


# Refusals -----------------------------------------------------------------------------------

def bad_sha(folder: Path) -> None:
    (folder / "check.sha256").write_text("0" * 64 + "\n")


def bad_chain(folder: Path) -> None:
    rewrite(folder, "confirm", lambda p: p.update(previous={}))


def bad_context(folder: Path) -> None:
    rewrite(folder, "check", lambda p: p["context"].update(code_sha256="d" * 64))


def no_stage(folder: Path) -> None:
    (folder / "check.json").unlink()


def bad_freeze(folder: Path) -> None:
    (folder / "shortlist_digest.txt").write_text("e" * 64 + "\n")


def bad_test_b(folder: Path) -> None:
    rewrite(folder, "check", lambda p: p["result"]["test_b"].update(p_b=0.5))


def no_log(folder: Path) -> None:
    (folder / "run_log.jsonl").unlink()


def log_without_check(folder: Path) -> None:
    lines = (folder / "run_log.jsonl").read_text().splitlines()
    (folder / "run_log.jsonl").write_text("".join(f"{line}\n" for line in lines if '"written"' not in line
                                                  or '"check"' not in line))


@pytest.mark.parametrize("damage, reason", [
    (bad_sha, "stage_digest_mismatch"), (bad_chain, "stage_chain_mismatch"), (bad_context, "stage_context_mismatch"),
    (no_stage, "stage_missing"), (bad_freeze, "shortlist_digest_mismatch"), (bad_test_b, "test_b_mismatch"),
    (no_log, "run_log_missing"), (log_without_check, "run_log_mismatch")])
def test_a_failed_check_refuses_and_writes_nothing(run3, tmp_path, capsys, damage, reason) -> None:
    damage(run3)
    out = tmp_path / "out"
    out.mkdir()
    assert rep3.main([str(run3)], out=out) == 1
    assert f"refused: {reason}:" in capsys.readouterr().err
    assert list(out.iterdir()) == []


@pytest.mark.parametrize("change, reason", [
    ({"trial_sha256": "a" * 64}, "trial_mismatch"), ({"data_files_sha256": "b" * 64}, "data_manifest_mismatch"),
    ({"code_pins_sha256": {}}, "code_pins_mismatch"), ({"code_sha256": "c" * 64}, "code_mismatch")])
def test_a_run_from_another_trial_data_or_code_refuses(tmp_path, capsys, run2_digest, change, reason) -> None:
    folder = write_run3(tmp_path / "run3", context(**change))
    assert rep3.main([str(folder)], out=tmp_path) == 1
    assert f"refused: {reason}:" in capsys.readouterr().err
    assert not any(p.is_file() for p in tmp_path.iterdir())


def test_a_freeze_other_than_the_run_2_freeze_refuses(run3, monkeypatch) -> None:
    monkeypatch.setattr(d, "run2_digest", lambda trial: "f" * 64)
    with pytest.raises(RunnerStop) as stop:
        rep3.build(run3)
    assert stop.value.reason == "run2_digest_mismatch"


def test_test_b_open_refuses(tmp_path, run2_digest) -> None:
    def chosen(found: dict) -> None:
        found["calibration"]["decision"] = "chosen"
    with pytest.raises(RunnerStop) as stop:
        rep3.build(write_run3(tmp_path / "run3", edit=chosen))
    assert stop.value.reason == "test_b_open"


# Guards -----------------------------------------------------------------------------------

def put(doc: dict, path: tuple, value) -> None:
    for k in path[:-1]:
        doc = doc[k]
    doc[path[-1]] = value


SEG = ("stages", "confirm", "segments", "confirm")


@pytest.mark.parametrize("path, value, reason", [
    ((*SEG, "path_break", "positions"), [], "private_field_in_output"),
    ((*SEG, "r4", "tilt", "S1", "primary", "primary", "incoming_weight_max"), 0.01, "private_field_in_output"),
    ((*SEG, "r4", "tilt", "S1", "primary", "primary", "incoming_weight_sum"), 0.01, "private_field_in_output"),
    ((*SEG, "counts", "S1", "primary", "permno"), 900001, "private_field_in_output"),
    ((*SEG, "half_spread", "cw_pit", "primary", "primary", "1993", "traded_notional"), 1.2, "private_field_in_output"),
    ((*SEG, "half_spread", "cw_pit", "primary", "primary", "1993", "max_half_spread"), 37.5, "private_field_in_output"),
    ((*SEG, "tilt_stats", "S1", "primary", "primary", "turnover_by_year"), {"tilt": {}}, "private_field_in_output"),
    (("limitations",), [f"see {USERS}/someone/efr"], "private_path_in_output"),
    (("limitations",), ["The result is a confirmation."], "claim_in_output"),
    (("limitations",), ["The tilt is profitable."], "claim_in_output")])
def test_each_guard_refuses(run3, path, value, reason) -> None:
    doc, attempts = rep3.build(run3)
    rep3.outputs(doc, attempts)
    put(doc, path, value)
    with pytest.raises(RunnerStop) as stop:
        rep3.outputs(doc, attempts)
    assert stop.value.reason == reason


def test_an_attempt_line_with_its_detail_refuses(run3) -> None:
    doc, attempts = rep3.build(run3)
    with pytest.raises(RunnerStop) as stop:
        rep3.outputs(doc, [*attempts, {"run": 3, "stage": "check", "outcome": "refused", "detail": "x"}])
    assert stop.value.reason == "private_field_in_output"


# Run facts and the screen report ------------------------------------------------------------

def test_the_run_3_code_digest_is_the_code_of_main_b1b0517(tmp_path) -> None:
    """``code_digest`` over the research/ and src/ Python files at the commit (CI checks out the full history)."""
    archive = subprocess.run(["git", "archive", rep3.RUN_3["code_commit"], *d.CODE_FOLDERS], cwd=d.REPO,
                             capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(tmp_path)], input=archive, check=True)
    assert d.code_digest(tmp_path) == rep3.RUN_3["code_sha256"]


def test_the_screen_report_gives_the_same_bytes_as_on_main_before(tmp_path) -> None:
    """The shared ``keys`` helper leaves every screen report output byte unchanged."""
    from test_m55_screen_report import RUN_2_STAGES, RUN_2_TRIAL, data_sha, write_run
    old = module_at(MAIN_BEFORE, "research/m55_screen_report.py", "m55_screen_report_before", tmp_path)

    def ctx(trial_sha: str, code: str) -> dict:
        return {"trial_sha256": trial_sha, "data_files_sha256": data_sha(), "code_pins_sha256": {},
                "code_sha256": code}
    v1 = write_run(tmp_path / "m55_screen_v1", ("coverage", "calibration"), ctx("a" * 64, "b" * 64))
    v2 = write_run(tmp_path / "m55_screen_v2", RUN_2_STAGES, ctx(RUN_2_TRIAL, "c" * 64))
    assert rep.outputs(rep.build(v1, v2)) == old.outputs(old.build(v1, v2))
