"""Synthetic tests for the public M5.5 screen report (card m55-screen, prod-m55screen-3).

The stage files are made here with ``m55_driver.write_stage``; no test reads real data. Two small runs stand in for
run 1 (coverage and calibration) and run 2 (all five stages). Each holds per-position rows, so the tests can check
that the report keeps only their aggregates.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import research.m55_driver as d
import research.m55_screen_report as rep
import research.m55_wrds_loader as w
from research import m55_criteria as crit
from research.m4_7_sp500_pit_rerun import RunnerStop
from research.m55_index_tilt import ME_REASONS


RUNS, CASES, EXITS, BLANK = d.RUNS, d.CASES, w.EXIT_CLASSES, d.BLANK
HEADER = {"evidence_ceiling": "DIAGNOSTIC_ONLY", "run_label": "stock-level out-of-sample",
          "low_risk_label": "in-sample", "labels": "every header states the run label", "vwretd": "vwretd as is"}
PER_POSITION = {"break_row", "break_rows", "previous_valid_row", "weight_at_last_rebalance", "each", "positions"}


def per(value):
    return {c: value for c in EXITS}


def data_sha() -> str:
    trial, _ = d.load_trial()
    tracked = json.loads((d.REPO / d.TRACKED_MANIFEST).read_text())
    return d.check_data(w.WrdsData({}, tracked), tracked, trial)


def results() -> dict:
    """Stage results with the shape the driver writes: S2 is shortlisted, S5 is a typed undefined record."""
    me_row = {"member_days": 10, **{f"days_{r}": 0 for r in ME_REASONS}, "days_present": 10, "dv_share_present": 1.0}
    signal = {"valid_share_by_year": {"1990": 0.5}, "min_month_valid_share_by_year": {"1990": 0.4},
              "reason_counts_by_year": {"1990": {"split_in_basis_window": 1, "valid": 5}},
              "reason_share_by_exit_class": {"valid": per(0.5)}}
    coverage = {"header": HEADER, "bid_ask_share": 0.01,
                "signals": {"S2": {**signal, "real_start": 1990, "first_month": "1990-01",
                                   "screen_months_before_blanks": 36,
                                   "short_history_size": {"1990": {"short_history_share": 0.1,
                                                                   "mean_me_percentile_short_history": 0.4,
                                                                   "mean_me_percentile_valid": 0.5}},
                                   "basis_quarters_by_year": {"1990": {"changed": 1, "same": 9, "unread": 0}}},
                            "S5": {**signal, "real_start": None, "first_month": None,
                                   "screen_months_before_blanks": 0}},
                "s7_early": {"1963-01": {"members": 2, "valid": 1, "valid_share": 0.5, "reasons": {"missing_item": 1},
                                         "basis_unseen_at_anchor": 0, "basis_unseen_at_anchor_12": 1}},
                "me_coverage": {"by_year": {"1990": me_row}, "by_exit_class": per(me_row),
                                "basis_unseen_member_days_to_1992": {"data_start": {"by_year": {"1961": 3},
                                                                                    "last": "1961-12-29"},
                                                                     "seal": {"by_year": {}, "last": None}}},
                "missingness_census": {"by_exit_class": per({k: 10 for k in ("member_days", "with_daily_row",
                                                                                 "with_price", "with_return",
                                                                                 "with_path_value")})}}
    calibration = {"header": HEADER, "decision": "ratio_coverage_low", "chosen_g": None, "rebalances": 354,
                   "start": "1963-05-31", "end": "1992-11-30", "undefined_share": 0.18,
                   "window_decision": "ratio_coverage_ambiguous", "window_diag_undefined_share": 0.6,
                   "window_diag_coverage_high": True,
                   "grid": [{"g": 4.0, "bracket": "meets", "bracket_full_windows": "ambiguous", "defined": 290,
                             "undefined": 64, "median_vol_ratio": 0.85, "median_hi": 0.86, "median_lo": 0.83,
                             "share_cap_binds": 1.0, "share_te_scaled": 0.07}],
                   "ratio_status_counts": {"defined_full": 131, "defined_partial": 159, "ratio_window_short": 64},
                   "gap_rebalances": 296, "ratio_gap_members": 3660, "max_ratio_gap_cw_share": 0.09,
                   "r6_by_exit_class": {k: per(1) for k in ("gap_members", "limiting_partial", "limiting_short")}}
    blank = ["1967-07", "1967-08"]
    position = {"break_row": "1967-09-01", "previous_valid_row": "1967-06-30", "months": blank,
                "exit_class": "failure", "weight_at_last_rebalance": {"cw": 0.001, "tilt": 0.002}}
    gap = {"months": 352, "annual_mean_gap": -0.001, "annual_te": 0.002, "correlation": 0.999,
           "book_annual_mean": 0.1, "benchmark_annual_mean": 0.101, "blank_months": {m: BLANK for m in blank},
           "blank_reason_counts": {BLANK: 2}}
    r4 = {"held": 1, "incoming_weight_sum": 0.01, "incoming_weight_max": 0.01,
          "by_cause": {"cash_merger": {"held": 1, "weight_at_last_rebalance_sum": 0.01, "ciz_return_in_path": 1}}}
    counts = {"rebalances": 37, "members_mean": 500.0, "members_min": 499, "traded_mean": 500.0, "traded_min": 499,
              "pinned_mean": 10.0, "c_zero_few_signals": 3, "c_zero_short_history": 1, "c_zero_window_gap": 1,
              "me_missing": 0, **{f"me_missing_{r}": 0 for r in ME_REASONS}, "settled_excluded": 0,
              "share_cap_at_final_weights": 0.0, "share_te_scaled": 0.0,
              "b2": {"rebalances": 1, "excluded": 1, "max_cw_share": 0.002,
                     "each": [{"date": "1990-03-30", "excluded": 1, "cw_share": 0.002}]}}
    part = {"blank_months": blank, "blank_month_count": 2, "blank_month_share": 2 / 354,
            "positions": [{**position, "weight_at_last_rebalance": {"cw": 0.001}}],
            "blanked_level_windows": {"windows": 1, "by_exit_class": {**per(0), "failure": 1},
                                      "each": [{"rebalance": "1967-08-31", "exit_class": "failure",
                                                "break_rows": ["1967-09-01"]}]},
            "coverage": counts,
            **{case: {"cw_vs_vwretd": gap, "r4": r4, "cw_annual_turnover": 0.26, "cw_annual_cost_drag": 0.001}
               for case in CASES}}
    look = {"header": HEADER, "runs": {run: part for run in RUNS},
            "fragility": {case: {"cw_vs_vwretd": {"primary": -0.001, "last_close": -0.001, "fragile": False}}
                          for case in CASES}}
    ok = {"status": "ok", "first_month": "1990-01", "last_month": "1992-12", "months": 36, "annual_active_mean": 0.006,
          "annual_te": 0.005, "information_ratio": 1.2, "hac_t": 1.9, "p_one_sided": 0.03, "annual_turnover": 1.5}
    undefined = {"status": "undefined", "undefined_reason": "screen_too_short", "first_month": None,
                 "last_month": None, "months": 0, "annual_active_mean": None, "annual_te": None,
                 "information_ratio": None, "hac_t": None, "p_one_sided": None, "annual_turnover": None}
    stats = {"realized_te_daily": 0.005, "worst_relative_drawdown": -0.01, "size_exposure_mean": 0.01,
             "annual_turnover": {"tilt": 1.5, "cw": 0.5, "active": 1.0},
             "annual_cost_drag": {"tilt": 0.006, "cw": 0.002, "active": 0.004},
             "turnover_by_year": {"active": {"1990": 1.0}}, "cost_drag_by_year": {"active": {"1990": 0.004}},
             "post_publication": {"publication_year": 1989, "months_after": 36, "months_before": 0,
                                  "annual_mean_after": 0.006, "annual_mean_before": None}}
    no_gap = {k: v for k, v in gap.items() if k not in ("blank_months", "blank_reason_counts")}
    cell = {"screen_record": ok, "tilt_vs_vwretd": no_gap, "cw_vs_vwretd": no_gap, "tilt_stats": stats,
            "r4": {"cw": r4, "tilt": r4}}
    c_zero = {"member_cells": per(5), **{k: {"cells": per(1), "share": per(0.2)}
                                         for k in ("few_signals", "short_history", "window_gap")}}
    screen = {"header": HEADER, "blank_months": {run: blank for run in RUNS},
              "candidates": {
                  "S2": {"real_start": 1990, "first_month": "1990-01", "months_with_values": {r: 36 for r in RUNS},
                         "records": {r: {c: cell for c in CASES} for r in RUNS},
                         "path_break_positions": {r: [position] for r in RUNS}, "counts": {r: counts for r in RUNS},
                         "c_zero_by_exit_class": {r: c_zero for r in RUNS},
                         "fragility": {c: {k: {"primary": 0.006, "last_close": 0.006, "fragile": False}
                                           for k in ("tilt_vs_cw", "tilt_vs_vwretd", "cw_vs_vwretd")}
                                       for c in CASES}},
                  "S5": {"real_start": None, "first_month": None, "months_with_values": {r: 0 for r in RUNS},
                         "records": {r: {c: {"screen_record": undefined} for c in CASES} for r in RUNS},
                         "fragility": {c: {"status": "not_evaluated", "reason": "screen_too_short",
                                           "short_runs": list(RUNS)} for c in CASES}}},
              "r6": {r: {"pool_cells": per(10), **{k: {"cells": per(0), "share": per(0.0)}
                                                   for k in ("unpriced", "basis_unseen", "blanked_windows")},
                         "me_missing": {m: {"cells": per(0), "share": per(0.0)} for m in ME_REASONS}} for r in RUNS},
              "records_for_freeze": {"S2": ok, "S5": undefined}}
    return {"coverage": coverage, "calibration": calibration, "look": look, "screen": screen}


def write_run(folder: Path, stages: tuple, ctx: dict, edit=None) -> Path:
    """Write the stage files of one run as the driver does, with test B and the freeze in the later stages."""
    folder.mkdir(parents=True)
    found, digests = results(), {}
    if edit:
        edit(found)
    for stage in stages:
        result = found.get(stage)
        if stage == "freeze":
            frozen = crit.freeze_shortlist(found["screen"]["records_for_freeze"])
            result = {"record": frozen, "digest_sha256": frozen["digest_sha256"], "decision": frozen["decision"],
                      "shortlist": frozen["shortlist"]}
            (folder / "shortlist_digest.txt").write_text(frozen["digest_sha256"] + "\n")
        if "calibration" in digests:
            result = {**result, "test_b": d.record_test_b(found["calibration"], digests["calibration"])}
        digests[stage] = d.write_stage(folder, stage, ctx, dict(digests), result)
    return folder


@pytest.fixture()
def runs(tmp_path: Path) -> tuple[Path, Path]:
    def ctx(trial: str, code: str) -> dict:
        return {"trial_sha256": trial, "data_files_sha256": data_sha(), "code_pins_sha256": {}, "code_sha256": code}
    return (write_run(tmp_path / "private" / "m55_screen_v1", ("coverage", "calibration"), ctx("a" * 64, "b" * 64)),
            write_run(tmp_path / "private" / "m55_screen_v2", d.STAGES, ctx(d.TRIAL_SHA256, "c" * 64)))


def rewrite(folder: Path, stage: str, edit) -> None:
    """Edit one stage file and renew its own digest file (the chain after it is not renewed)."""
    payload = json.loads((folder / f"{stage}.json").read_text())
    edit(payload)
    text = json.dumps(payload, sort_keys=True, indent=1) + "\n"
    (folder / f"{stage}.json").write_text(text)
    (folder / f"{stage}.sha256").write_text(d.sha256_bytes(text.encode()) + "\n")


def keys(value) -> set:
    if isinstance(value, dict):
        return set(value) | set().union(*(keys(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(keys(v) for v in value))
    return set()


def test_report_is_aggregate_only_and_the_same_bytes_on_a_second_run(runs, tmp_path) -> None:
    out = [tmp_path / "out1", tmp_path / "out2"]
    for folder in out:
        folder.mkdir()
        assert rep.main([str(runs[0]), str(runs[1])], out=folder) == 0
    files = sorted(p.name for p in out[0].iterdir())
    assert files == sorted([rep.REPORT_JSON, rep.REPORT_MD, rep.ATTEMPTS_JSONL])
    assert all((out[0] / f).read_bytes() == (out[1] / f).read_bytes() for f in files)

    doc = json.loads((out[0] / rep.REPORT_JSON).read_text())
    lines = [json.loads(line) for line in (out[0] / rep.ATTEMPTS_JSONL).read_text().splitlines()]
    assert not (keys(doc) | keys(lines)) & PER_POSITION
    for f in files:
        text = (out[0] / f).read_text()
        assert "/Users/" not in text and "/home/" not in text and str(tmp_path) not in text
        assert "break_row" not in text and "previous_valid_row" not in text and "1990-03-30" not in text

    assert [line["folder"] for line in lines] == ["m55_screen_v1", "m55_screen_v2"]
    assert [line["status"] for line in lines] == ["stopped", "completed"]
    assert doc["freeze"]["shortlist"] == ["S2"] and doc["freeze"]["digest_sha256"] == (
        runs[1] / "shortlist_digest.txt").read_text().strip()
    assert doc["screen"]["candidates"]["S5"]["undefined_reason"] == "screen_too_short"
    assert doc["test_b"]["stopped"] and doc["test_b"]["p_a_max_for_holm"] == 0.025
    assert doc["calibration"]["result_equal_to_run_1"]
    pb = doc["reports_owed"]["path_break"]
    assert pb["look"]["primary"] == {"position_count": 1, "months": 2, "weight_sum": {"cw": 0.001},
                                     "by_exit_class": {**per(0), "failure": 1},
                                     "span_months": {"min": 2, "median": 2, "max": 2}}
    assert "weight_sum" not in pb["screen"]["S2"]["primary"]
    assert doc["reports_owed"]["b2"]["look"]["primary"] == {"rebalances": 1, "excluded": 1}
    assert doc["reports_owed"]["r4"]["look_weight_level"] == "none"          # one event: below 3 positions
    assert doc["reports_owed"]["check_period_end"]["status"] == "owed_by_confirm_stage"


def bad_sha(v1: Path, v2: Path) -> None:
    (v2 / "screen.sha256").write_text("0" * 64 + "\n")


def bad_chain(v1: Path, v2: Path) -> None:
    rewrite(v2, "look", lambda p: p.update(previous={}))


def bad_context(v1: Path, v2: Path) -> None:
    rewrite(v2, "freeze", lambda p: p["context"].update(code_sha256="d" * 64))


def bad_digest(v1: Path, v2: Path) -> None:
    (v2 / "shortlist_digest.txt").write_text("e" * 64 + "\n")


def bad_test_b(v1: Path, v2: Path) -> None:
    rewrite(v2, "freeze", lambda p: p["result"]["test_b"].update(p_b=0.5))


@pytest.mark.parametrize("damage, reason", [
    (bad_sha, "stage_digest_mismatch"), (bad_chain, "stage_chain_mismatch"), (bad_context, "stage_context_mismatch"),
    (bad_digest, "shortlist_digest_mismatch"), (bad_test_b, "test_b_mismatch"),
])
def test_a_failed_check_refuses_and_writes_nothing(runs, tmp_path, capsys, damage, reason) -> None:
    damage(*runs)
    out = tmp_path / "out"
    out.mkdir()
    assert rep.main([str(runs[0]), str(runs[1])], out=out) == 1
    assert f"refused: {reason}:" in capsys.readouterr().err
    assert list(out.iterdir()) == []


def test_runs_from_another_trial_file_or_data_refuse(tmp_path, capsys) -> None:
    def ctx(trial: str, data: str) -> dict:
        return {"trial_sha256": trial, "data_files_sha256": data, "code_pins_sha256": {}, "code_sha256": "c" * 64}
    v1 = write_run(tmp_path / "m55_screen_v1", ("coverage", "calibration"), ctx("a" * 64, data_sha()))
    for name, context, reason in (("trial", ctx("a" * 64, data_sha()), "trial_mismatch"),
                                  ("data", ctx(d.TRIAL_SHA256, "f" * 64), "data_manifest_mismatch")):
        v2 = write_run(tmp_path / name / "m55_screen_v2", d.STAGES, context)
        assert rep.main([str(v1), str(v2)], out=tmp_path) == 1
        assert f"refused: {reason}:" in capsys.readouterr().err
    assert not any(p.is_file() for p in tmp_path.iterdir())


def nested(found: dict) -> None:
    """Look R4 groups of 9 events (primary run) and 12 events (last_close run); the S2 groups nest in the look group
    and hold one failure fewer."""
    def r4(failure: int) -> dict:
        return {"held": 5 + failure, "incoming_weight_sum": 0.05, "incoming_weight_max": 0.01,
                "by_cause": {"cash_merger": {"held": 5, "weight_at_last_rebalance_sum": 0.02, "ciz_return_in_path": 5},
                             "failure": {"held": failure, "weight_at_last_rebalance_sum": 0.01 * failure,
                                         "missing_engine_default": failure}}}
    look = found["look"]["runs"]
    for run, failure in zip(RUNS, (4, 7)):
        look[run] = {**look[run], **{case: {**look[run][case], "r4": r4(failure)} for case in CASES}}
    records = found["screen"]["candidates"]["S2"]["records"]
    for run in RUNS:
        records[run] = {case: {**records[run][case], "r4": {"cw": r4(3), "tilt": r4(3)}} for case in CASES}


def test_nested_groups_one_event_apart_give_no_candidate_weight(tmp_path) -> None:
    ctx = {"trial_sha256": d.TRIAL_SHA256, "data_files_sha256": data_sha(), "code_pins_sha256": {},
           "code_sha256": "c" * 64}
    v1 = write_run(tmp_path / "m55_screen_v1", ("coverage", "calibration"), {**ctx, "trial_sha256": "a" * 64})
    doc = rep.build(v1, write_run(tmp_path / "m55_screen_v2", d.STAGES, ctx, nested))
    owed = doc["reports_owed"]
    groups = [doc["screen"]["candidates"], *(part["screen"] for part in owed.values()
                                              if isinstance(part, dict) and "screen" in part)]
    assert not keys(groups) & rep.GROUP_WEIGHTS and not keys(doc) & rep.SINGLE_MAX
    # Equal cash_merger counts in the two loader runs cannot show the same events: the look gives totals only.
    assert owed["r4"]["look_weight_level"] == "total"
    look = owed["r4"]["look"]["primary"]["primary"]
    assert look["weight_at_last_rebalance_sum"] == pytest.approx(0.06) and look["incoming_weight_sum"] == 0.05
    assert not keys(look["by_cause"]) & rep.GROUP_WEIGHTS
    assert {"r4.screen.weight_at_last_rebalance_sum", "r4.look.by_cause.weight_at_last_rebalance_sum",
            "b2.max_cw_share", "path_break.screen.weight_sum"} <= set(doc["missing"])
    rep.outputs(doc)
    owed["r4"]["screen"]["S2"]["primary"]["primary"]["cw"]["incoming_weight_sum"] = 0.05
    with pytest.raises(RunnerStop) as stop:
        rep.outputs(doc)
    assert stop.value.reason == "private_field_in_output"
