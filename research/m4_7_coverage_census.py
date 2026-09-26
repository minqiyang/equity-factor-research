"""Coverage census, readiness, power projection, and seal confirmation for M4.7 (plan section 5).

Runs after the universe build and the terminal projection and before any
factor computation. Refuses ``derived_artifact_stale`` before any metric when
a derived input no longer matches the current manifest (S7). Writes the
private ``census/census_detail.json`` and support files into the snapshot,
the public count-only ``reports/m4_7_coverage_census.{json,md}``, and the
confirmed seal record. Every figure is ``DIAGNOSTIC_ONLY``; nothing here
supports a ranking, selection, or profitability claim (R2, R10).

Run as ``python -m research.m4_7_coverage_census --snapshot-id <ID>``.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm

from data import holdout_partition
from data.holdout_partition import SEAL_FILE, SnapshotRefusal, coverage_start, monthly_raw_counts, sha256_bytes
from research.m4_7_common_support import ic_month_set, signal_eligibility, write_support_files
from research.m4_7_family_a import FAMILY_A
from research.m4_7_holdout_seal import REPOSITORY_SEAL, confirmed_seal_bytes
from research.m4_7_terminal_evidence import CURATED, ENGINE_EVENTS, read_engine_events, require_current_terminal
from research.m4_7_universe_build import (
    BENCHMARK,
    BUILD_MANIFEST,
    DISTRIBUTION_SUPPORT,
    INTERVAL_CSV,
    INTERVAL_RESULTS,
    INVENTORY,
    REKEY_STATUSES,
    SECURITY_MASTER,
    TABLES,
    Snapshot,
    _parquet,
    canonical_json,
    discovery_window,
    membership_codes,
    normalized_eod_subreason,
    read_bar_dates,
    read_derived_json,
    request_list,
    require_current,
    snapshot_dir_from_args,
    write_bytes,
)
from backtest.portfolio import resolve_pit_universe_mask
from data.constituent_table import load_constituent_intervals_csv
from research.unchanging_price import report_unchanging_price_segments


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = "m4_7_coverage_census.json"
REPORT_MD = "m4_7_coverage_census.md"
CENSUS_DETAIL = "census/census_detail.json"
IN_BAND_YEARS = 16
LATEST_HOLDOUT_END = "2014-01-01"
IDENTITY_CAP, OFF_CALENDAR_CAP, UNPRICED_CAP = 0.05, 0.001, 0.02
MAX_WINDOWS, MAX_EXCLUDED_FRACTION, MIN_IC_MONTHS = 6, 0.05, 60
VP2_LEVEL, VP2_SHARE = 0.05, 0.01
VOLUME_BASIS_BARS, VOLUME_BASIS_MIN_ROWS, VOLUME_BASIS_TAIL_SHARE = 20, 10, 0.20
PRIOR_EXPOSURES = (("static_50_name_cohort", "2016-08-08", "2026-08-07"),
                   ("historical_evaluation", "2025-05-01", "2026-05-31"))
SCALE_STEP, SPLIT_WINDOW_ROWS, E1_GAP_ROWS = 0.15, 5, 20
FAILURE_CODES = {
    "R-CENSUS-1": "blocked:insufficient_in_band_history",
    "R-CENSUS-2": "blocked:excluded_coverage",
    "R-CENSUS-3": "blocked:identity_refusal_fraction",
    "R-CENSUS-4": "blocked:calendar_divergence",
    "R-CENSUS-5": "blocked:calendar_source_missing",
    "R-CENSUS-6": "blocked:snapshot_integrity",
    "R-CENSUS-7": "ready_with_caveats:holdout_breadth_after_identity",
    "R-CENSUS-8": "blocked:insufficient_ic_months",
    "R-CENSUS-9": "blocked:unpriced_eligible_member_days",
    "R-CENSUS-10": "blocked:retrieval_incomplete",
}


# ---------------------------------------------------------------- pure pieces


def power_projection(ic_month_supply: int) -> dict[str, Any]:
    """Plan 5.5: projected MDE for the BY-first-rejection and single-test thresholds."""
    h6 = sum(1.0 / k for k in range(1, 7))
    alpha_eff = 0.05 / (6 * h6)
    z_eff = float(norm.ppf(1 - alpha_eff / 2) + norm.ppf(0.80))
    z_single = float(norm.ppf(0.975) + norm.ppf(0.80))
    rows = []
    for s in (0.08, 0.10, 0.12):
        rows.append({
            "s": s,
            "mde_eff": z_eff * s / math.sqrt(ic_month_supply) if ic_month_supply else None,
            "mde_single": z_single * s / math.sqrt(ic_month_supply) if ic_month_supply else None,
            "months_for_mde_eff_0_02": math.ceil((z_eff * s / 0.02) ** 2),
            "months_for_mde_single_0_02": math.ceil((z_single * s / 0.02) ** 2),
        })
    mde = rows[1]["mde_eff"]
    return {"T_proj": ic_month_supply, "H_6": h6, "alpha_eff": alpha_eff, "z_eff": z_eff, "z_single": z_single,
            "band": rows, "kill_reachable_projection": mde is not None and mde <= 0.02,
            "note": "declared prior band for the monthly Rank IC standard deviation; the gate applies realized power"}


def post_join_warmup_estimate(s_mask: pd.DataFrame, bars: pd.DataFrame, ic_resets: tuple[int, ...]) -> dict[str, int]:
    """Section 5.2: eligible asset-months per Family A factor whose signal row precedes ``first_bar + warmup_rows``."""
    first_bar = {pid: int(np.flatnonzero(bars[pid].to_numpy())[0]) for pid in bars.columns if bars[pid].any()}
    return {
        factor.factor_id: int(sum(
            1 for r in ic_resets for pid in s_mask.columns[s_mask.iloc[r - 1].to_numpy()]
            if r - 1 < first_bar.get(pid, 0) + factor.warmup_rows))
        for factor in FAMILY_A
    }


def prior_exposure_overlap(ic_month_dates: list[date]) -> dict[str, Any]:
    """Section 5.2 exposure: the fraction of IC months inside each prior exposure window."""
    return {
        kind: {"window": f"{start}..{end}", "note": "the prior exposure covered 50 names",
               "fraction_of_ic_months": (sum(date.fromisoformat(start) <= d <= date.fromisoformat(end)
                                             for d in ic_month_dates) / len(ic_month_dates)) if ic_month_dates else 0.0}
        for kind, start, end in PRIOR_EXPOSURES
    }


def derive_readiness(inputs: dict[str, Any]) -> dict[str, Any]:
    """Plan 5.3: every rule's inputs and result; ``ready`` needs all ten rules."""
    results = {
        "R-CENSUS-1": inputs["in_band_years"] >= IN_BAND_YEARS and inputs["holdout_end"] <= LATEST_HOLDOUT_END,
        "R-CENSUS-2": inputs["gap_window_count"] <= MAX_WINDOWS and inputs["excluded_fraction"] <= MAX_EXCLUDED_FRACTION,
        "R-CENSUS-3": inputs["identity_refusal_fraction"] <= IDENTITY_CAP,
        "R-CENSUS-4": inputs["off_calendar_fraction"] <= OFF_CALENDAR_CAP,
        "R-CENSUS-5": inputs["calendar_covers_coverage_start"] and inputs["benchmark_complete"],
        "R-CENSUS-6": inputs["snapshot_integrity"],
        "R-CENSUS-7": inputs["holdout_band_after_identity"],
        "R-CENSUS-8": inputs["ic_month_supply"] >= MIN_IC_MONTHS,
        "R-CENSUS-9": inputs["unpriced_fraction"] <= UNPRICED_CAP,
        "R-CENSUS-10": inputs["retrieval_complete"],
    }
    failures = []
    for rule, passed in results.items():
        if passed:
            continue
        code = FAILURE_CODES[rule]
        if rule == "R-CENSUS-1" and inputs["holdout_end"] > LATEST_HOLDOUT_END:
            code = "blocked:holdout_overlaps_prior_exposure"
        if rule == "R-CENSUS-5" and inputs["calendar_covers_coverage_start"]:
            code = "blocked:benchmark_gap"
        failures.append({"rule": rule, "result": code})
    if not failures:
        status = "ready"
    elif [f["rule"] for f in failures] == ["R-CENSUS-7"]:
        status = FAILURE_CODES["R-CENSUS-7"]
    else:
        status = "blocked"
    return {"status": status, "failures": failures, "rules": {rule: {"passed": bool(ok)} for rule, ok in results.items()},
            "inputs": inputs}


def in_band_month_ends(start: date | None, last: date | None) -> int:
    """Month-ends from the in-band start through the last month-end, inclusive; 192 month-ends are 16 years."""
    if start is None or last is None or last < start:
        return 0
    return (last.year - start.year) * 12 + last.month - start.month + 1


def tolerant_band(counts: list[int]) -> bool:
    """The seal's tolerant rule over a fixed window: at most 3 isolated exceptions inside the hard band."""
    band, hard = holdout_partition.BAND, holdout_partition.HARD_BAND
    exceptions = [i for i, n in enumerate(counts) if not band[0] <= n <= band[1]]
    return (len(exceptions) <= holdout_partition.TOLERANCE_EXCEPTIONS
            and all(b - a > 1 for a, b in zip(exceptions, exceptions[1:]))
            and all(hard[0] <= counts[i] <= hard[1] for i in exceptions))


def volume_basis_diagnostic(ells: list[tuple[float, float | None]]) -> dict[str, Any]:
    """C79/C85: ``ells`` holds ``(ratio, ell)`` per eligible split row.

    ``ell`` is ``None`` when a 20-bar median dollar turnover on either side of
    the split is zero, so its logarithm is undefined. Such rows stay typed and
    counted under ``rows_undefined_zero_median_turnover``; they enter neither
    the median, the tail share, nor the ten-row sufficiency count.
    """
    defined = [(ratio, ell) for ratio, ell in ells if ell is not None]
    values = np.array([ell for _, ell in defined], dtype=float)
    large = [ell for ratio, ell in defined if abs(math.log(ratio)) >= math.log(2.0)]
    share = (sum(ell > 0.5 for ell in large) / len(large)) if large else None
    if len(values) < VOLUME_BASIS_MIN_ROWS:
        verdict = "insufficient"
    elif np.median(values) > 0.5 or (len(large) >= VOLUME_BASIS_MIN_ROWS and share > VOLUME_BASIS_TAIL_SHARE):
        verdict = "contradicted"
    else:
        verdict = "consistent"
    quartiles = np.quantile(values, [0.25, 0.5, 0.75]).tolist() if len(values) else [None] * 3
    return {"rows": int(len(values)), "rows_undefined_zero_median_turnover": len(ells) - len(defined),
            "median_ell": quartiles[1], "quartiles_ell": [quartiles[0], quartiles[2]],
            "rows_ratio_at_least_2": len(large), "share_ell_above_half_at_ratio_2": share, "a1_volume_half": verdict}


# ---------------------------------------------------------------- census


@dataclass
class Context:
    snapshot: Snapshot
    calendar: pd.DatetimeIndex
    i_h: int
    d0: int
    d_last: int
    master: pd.DataFrame
    intervals: pd.DataFrame
    build: dict[str, Any]
    validation: dict[str, Any]
    panels: dict[str, pd.DataFrame]

    @property
    def window(self) -> slice:
        return slice(self.d0, self.d_last + 1)


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _row(calendar: pd.DatetimeIndex, text: str) -> int | None:
    return None if not text else int(calendar.get_loc(pd.Timestamp(text)))


def _panels(root: Path, inventory: dict[str, Any]) -> dict[str, pd.DataFrame]:
    panels = {}
    for record in inventory["files"]:
        payload = (root / "panel" / record["file"]).read_bytes()
        if sha256_bytes(payload) != record["sha256"]:
            raise SnapshotRefusal("derived_artifact_stale", f"panel {record['symbol']}")
        frame = _parquet(payload, record["file"])
        panels[record["symbol"]] = frame.assign(date=pd.DatetimeIndex(frame["date"])).set_index("date")
    return panels


def run_census(
    snapshot_dir: Path | str,
    *,
    reports_dir: Path | str | None = None,
    seal_out: Path | str | None = None,
    code_commit: str | None = None,
) -> dict[str, Any]:
    """Compute the census and write every output; return the public JSON, the detail, and the digests."""
    snapshot = Snapshot.open(snapshot_dir)
    root = snapshot.root
    build = read_derived_json(root, BUILD_MANIFEST)
    require_current(snapshot, build.get("discovery_inputs_sha256"), BUILD_MANIFEST)
    inventory = read_derived_json(root, INVENTORY)
    require_current(snapshot, inventory.get("discovery_inputs_sha256"), INVENTORY)
    validation, inputs_sha = require_current_terminal(snapshot)
    support = write_support_files(root)
    calendar = snapshot.calendar()
    i_h, d0, d_last = discovery_window(calendar, snapshot.holdout_end)
    ctx = Context(snapshot, calendar, i_h, d0, d_last, _read_csv(root / SECURITY_MASTER),
                  _read_csv(root / INTERVAL_RESULTS), build, validation, _panels(root, inventory))
    seal_bytes_prospective = (root / SEAL_FILE).read_bytes()
    seal = json.loads(seal_bytes_prospective)
    membership = snapshot.read_file("membership")

    table = load_constituent_intervals_csv(root / INTERVAL_CSV).data
    member_pids = sorted(set(table["permanent_id"]))
    events = read_engine_events(root)
    mask = (resolve_pit_universe_mask(table, events if len(events) else None, calendar, member_pids)
            if member_pids else pd.DataFrame(index=calendar))
    breadth = _breadth(ctx, table, mask, seal)
    coverage, detail_unpriced = _unpriced(ctx, mask, support)
    identity = _identity(ctx, membership)
    episodes = _episode_metrics(ctx, mask)
    ic_included, ic_excluded = ic_month_set(support.schedule)
    reset_dates = [support.calendar[r].date() for r in ic_included]
    warmup = post_join_warmup_estimate(signal_eligibility(support.mask, support.bars), support.bars, ic_included)
    schedule = support.schedule
    record = support.record()
    verify = snapshot.manifest.get("verify") or {}
    member_codes = membership_codes(membership)
    off_calendar = sum(count for code, count in build["off_calendar_bar_rows"].items() if code in member_codes)
    spy = ctx.panels.get(f"{BENCHMARK}#E1")
    benchmark_complete = spy is not None and support.calendar.isin(spy.index[np.isfinite(spy["adjusted_close"])]).all()
    coverage_start_sealed = seal["holdout_start"]
    integrity = _integrity(snapshot, seal, verify)
    readiness_inputs = {
        "in_band_years": breadth["in_band_years"], "holdout_end": seal["holdout_end_exclusive"],
        "gap_window_count": len(schedule.windows), "excluded_fraction": schedule.excluded_fraction,
        "identity_refusal_fraction": coverage["identity_refusal_fraction"],
        "off_calendar_fraction": off_calendar / coverage["member_days_all"] if coverage["member_days_all"] else 0.0,
        "calendar_covers_coverage_start": calendar[0].date().isoformat() <= coverage_start_sealed,
        "benchmark_complete": bool(benchmark_complete), "snapshot_integrity": integrity["passed"],
        "holdout_band_after_identity": breadth["holdout_band_after_identity"],
        "ic_month_supply": len(ic_included), "unpriced_fraction": coverage["unpriced_fraction"],
        "retrieval_complete": bool(verify.get("retrieval_complete", False)),
    }
    readiness = derive_readiness(readiness_inputs)
    status_counts = _table_status_counts(snapshot, membership)
    counters = snapshot.manifest.get("counters", {})
    public = {
        "schema_version": "m4_7_coverage_census_v1",
        "evidence_ceiling": "DIAGNOSTIC_ONLY",
        "formal_universe_evidence_eligible": False,
        "snapshot_id": snapshot.manifest["snapshot"].get("id"),
        "code_commit": code_commit if code_commit is not None else _code_commit(),
        "holdout_metrics_scope": "metadata_only",
        "discovery_window": {"holdout_end": seal["holdout_end_exclusive"], "D0": calendar[d0].date().isoformat(),
                             "D_last": calendar[d_last].date().isoformat(), "D_end": record["D_end"]},
        "membership_breadth": {key: breadth[key] for key in (
            "members_per_date_by_year", "members_per_month_end", "coverage_start_sealed", "coverage_start_confirmed",
            "coverage_start_strict", "in_band_years", "identity_adjusted_min_holdout_month_end_count")},
        "ever_members": identity["ever_members"],
        "identity": identity["identity"],
        "calendar": {"off_calendar_bar_rows": off_calendar, "calendar_rows": len(calendar),
                     "calendar_source": "GSPC.INDX_eod_dates_v1",
                     "max_reset_to_reset_rows": schedule.max_reset_to_reset_rows},
        "price_coverage": {**coverage["public"], **episodes["coverage"]},
        "exclusion_set": {
            "unresolved_events": len(support.unresolved_in_window()),
            "missing_bar_cells": int(schedule.g_base.to_numpy().sum()), "terminal_reset_cells": len(schedule.g_term),
            "gap_window_count": len(schedule.windows), "excluded_rows": schedule.excluded_rows,
            "excluded_fraction": schedule.excluded_fraction, "segment_count": len(schedule.segments),
            "min_segment_rows": min((s.rows for s in schedule.segments if s.valid), default=0),
            "segments_sha256": support.segments_sha256,
            "gap_windows": [{"start_month": w["start"][:7], "end_month": w["end"][:7], "reason_types": w["reasons"],
                             "rows": _rows_between(support.calendar, w["start"], w["end"])} for w in record["gap_windows"]],
            "segments": [{"first_month": s["first_row"][:7], "last_month": s["last_row"][:7],
                          "measured_rows": s["measured_rows"], "valid": s["valid"]} for s in record["segments"]],
        },
        "price_quality": episodes["quality"],
        "corporate_actions": {**episodes["corporate_actions"],
                              "split_tables_by_status": status_counts["splits"],
                              "dividend_tables_by_status": status_counts["dividends"],
                              "split_evidence_basis_counts": _evidence_basis_counts(snapshot, membership),
                              "corporate_action_partitions_quarantined": {
                                  f"{t}_{p}_quarantined": counters.get(f"{t}_{p}_quarantined", 0)
                                  for t in TABLES for p in ("discovery", "holdout")}},
        "exits": episodes["exits"],
        "terminal_evidence": _terminal(ctx),
        "warm_up_estimate": {"post_join_warmup_estimate": warmup, "unit": "eligible_asset_months",
                             "estimate_scope": "family_a_first_bar_warmup"},
        "ic_supply": {"ic_month_supply": len(ic_included),
                      **{f"{reason.replace('ic_month_', 'ic_months_')}": len(rows) for reason, rows in ic_excluded.items()}},
        "power_projection": power_projection(len(ic_included)),
        "discovery_overlap_with_prior_exposures": prior_exposure_overlap(reset_dates),
        "volume_basis_split_diagnostic": episodes["volume_basis"],
        "in_span_distribution_support": episodes["distribution_support"],
        "vp2_revisit_required": episodes["vp2_revisit_required"],
        "retrieval": {"retrieval_complete": bool(verify.get("retrieval_complete", False)),
                      "incomplete_counts_by_table_and_status": _incomplete_counts(verify),
                      "table_status_counts": status_counts,
                      "persistent_provider_error_member_days": coverage["persistent_member_days"]},
        "census_readiness": readiness,
        "snapshot_identity": {
            "manifest_sha256": sha256_bytes((root / "manifest.json").read_bytes()),
            "discovery_inputs_sha256": inputs_sha,
            "interval_csv_sha256": sha256_bytes((root / INTERVAL_CSV).read_bytes()),
            "security_master_sha256": sha256_bytes((root / SECURITY_MASTER).read_bytes()),
            "interval_results_sha256": sha256_bytes((root / INTERVAL_RESULTS).read_bytes()),
            "evidence_sha256": sha256_bytes((root / CURATED).read_bytes()) if (root / CURATED).is_file() else None,
            "engine_events_sha256": sha256_bytes((root / ENGINE_EVENTS).read_bytes()),
            "segments_sha256": support.segments_sha256,
            "seal_prospective_sha256": sha256_bytes(seal_bytes_prospective),
        },
        "premises": {
            "VP-1": "served volume carries the split product the prices carry; tested by volume_basis_split_diagnostic",
            "VP-2": "declared distributions are applied as non-split adjustments by the prior-close formula and no other; "
                    "ratified under owner item O-8; exposure measured by B_D and S_D",
            "O-8": "ratified; revisit when member-days with S_D > 0.05 exceed 1 percent of eligible member-days",
            "rounding_selection": "rounding refusals at low adjusted levels select on later splits",
        },
    }
    detail = {
        "discovery_inputs_sha256": inputs_sha,
        "eligible_unpriced_by_permanent_id": detail_unpriced,
        "interval_refusals": identity["detail"],
        "incomplete_codes_by_table_and_status": verify.get("incomplete_codes_by_table_and_status", {}),
        "unresolved": support.unresolved_in_window(),
        "gap_windows": record["gap_windows"], "segments": record["segments"],
    }
    write_bytes(root / CENSUS_DETAIL, canonical_json(detail))
    reports = Path(reports_dir) if reports_dir is not None else REPOSITORY_ROOT / "reports"
    census_bytes = canonical_json(public)
    census_sha = write_bytes(reports / REPORT_JSON, census_bytes)
    write_bytes(reports / REPORT_MD, render_markdown(public).encode("utf-8"))
    seal_status = "confirmed" if breadth["holdout_band_after_identity"] else "caveat"
    confirmed = confirmed_seal_bytes(
        seal_bytes_prospective, census_json_sha256=census_sha, status=seal_status,
        identity_adjusted_min_month_end_count=breadth["identity_adjusted_min_holdout_month_end_count"],
        integrity=_holdout_integrity(snapshot),
    )
    seal_confirmed = write_bytes(Path(seal_out) if seal_out is not None else REPOSITORY_SEAL, confirmed)
    return {"public": public, "detail": detail, "census_json_sha256": census_sha,
            "seal_prospective_sha256": sha256_bytes(seal_bytes_prospective), "seal_confirmed_sha256": seal_confirmed}


def _rows_between(calendar: pd.DatetimeIndex, start: str, end: str) -> int:
    return int(calendar.get_loc(pd.Timestamp(end)) - calendar.get_loc(pd.Timestamp(start)) + 1)


def _code_commit() -> str | None:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=False)
    except OSError:
        return None
    return result.stdout.strip() or None


# ---------------------------------------------------------------- metric groups


def _breadth(ctx: Context, table: pd.DataFrame, mask: pd.DataFrame, seal: dict[str, Any]) -> dict[str, Any]:
    band = holdout_partition.BAND
    counts = mask.sum(axis=1) if len(mask.columns) else pd.Series(0, index=ctx.calendar)
    by_year = {}
    for year, values in counts.groupby(counts.index.year):
        by_year[str(year)] = {"min": int(values.min()), "median": float(values.median()), "max": int(values.max()),
                              "dates_below_band": int((values < band[0]).sum())}
    entries = [(row.permanent_id, row.start_date.date(), None if pd.isna(row.end_date) else row.end_date.date())
               for row in table.itertuples(index=False)]
    monthly = monthly_raw_counts(entries, ctx.calendar[-1].date()) if entries else []
    month_end = [{"month": m.isoformat()[:7], "count": n,
                  "status": "in_band" if band[0] <= n <= band[1] else ("below_band" if n < band[0] else "above_band")}
                 for m, n in monthly]
    sealed_start = date.fromisoformat(seal["holdout_start"])
    holdout_end = date.fromisoformat(seal["holdout_end_exclusive"])
    confirmed = coverage_start(monthly, holdout_partition.TOLERANCE_EXCEPTIONS)
    strict = coverage_start(monthly, 0)
    tail = [(m, n) for m, n in monthly if m >= sealed_start]
    tail_start = coverage_start(tail, holdout_partition.TOLERANCE_EXCEPTIONS)
    in_band_years = in_band_month_ends(tail_start, monthly[-1][0] if monthly else None) / 12
    holdout_counts = [n for m, n in monthly if sealed_start <= m < holdout_end]
    return {
        "members_per_date_by_year": by_year, "members_per_month_end": month_end,
        "coverage_start_sealed": seal["holdout_start"],
        "coverage_start_confirmed": None if confirmed is None else confirmed.isoformat(),
        "coverage_start_strict": None if strict is None else strict.isoformat(),
        "in_band_years": in_band_years,
        "holdout_band_after_identity": bool(holdout_counts) and tolerant_band(holdout_counts),
        "identity_adjusted_min_holdout_month_end_count": min(holdout_counts) if holdout_counts else None,
    }


def _interval_rows(ctx: Context, row: dict[str, Any]) -> np.ndarray:
    m_in = _row(ctx.calendar, row["m_in"])
    if m_in is None:
        return np.array([], dtype=int)
    m_out = _row(ctx.calendar, row["m_out"])
    m_out = len(ctx.calendar) if m_out is None else m_out
    return np.arange(max(m_in, ctx.d0), min(m_out, ctx.d_last + 1))


def _unpriced(ctx: Context, mask: pd.DataFrame, support) -> tuple[dict[str, Any], dict[str, dict[str, int]]]:
    """Section 5.2 ``eligible_unpriced_member_days`` with R-CENSUS-3 and R-CENSUS-9 counts."""
    window = ctx.window
    masters = {r["permanent_id"]: r for r in ctx.master.to_dict(orient="records") if r["permanent_id"]}
    settled = set(read_engine_events(ctx.snapshot.root)["permanent_id"])
    reasons: dict[str, int] = {}
    detail: dict[str, dict[str, int]] = {}
    member_days = 0
    with_bar = 0
    schedule = support.schedule
    x_rows: dict[str, set[int]] = {}
    for row, column in np.argwhere(schedule.g_base.to_numpy(dtype=bool)):
        x_rows.setdefault(schedule.g_base.columns[column], set()).add(int(row) + ctx.i_h)
    for pid, row in list(schedule.g_term) + list(support.unresolved.items()):
        x_rows.setdefault(pid, set()).add(int(row) + ctx.i_h)

    def add(key: str, count: int, pid: str | None = None) -> None:
        if count:
            reasons[key] = reasons.get(key, 0) + count
            if pid is not None:
                detail.setdefault(pid, {})[key] = detail.setdefault(pid, {}).get(key, 0) + count

    for pid in mask.columns:
        eligible = mask[pid].to_numpy()[window]
        rows = np.arange(ctx.d0, ctx.d_last + 1)[eligible]
        member_days += len(rows)
        record = masters[pid]
        sidecar = read_bar_dates(ctx.snapshot, record["vendor_code"])
        sidecar_rows = set(ctx.calendar.get_indexer(sidecar)) if sidecar is not None else set()
        with_bar += sum(1 for r in rows if r in sidecar_rows)
        first, last = _row(ctx.calendar, record["first_bar"]), _row(ctx.calendar, record["last_bar"])
        panel = ctx.panels.get(pid)
        panel_rows = set() if panel is None else set(ctx.calendar.get_indexer(panel.index[np.isfinite(panel["adjusted_close"])]))
        excluded = x_rows.get(pid, set())
        for r in rows:
            if r in panel_rows or r in excluded:
                continue
            if panel is None:
                add("post_last_bar_deferred_holdout" if last < ctx.i_h else "no_discovery_panel", 1, pid)
            elif r < first:
                add("pre_first_bar", 1, pid)
            elif r > last:
                unresolved = record["has_delisting_candidate_interval"] == "True" and pid not in settled
                add("after_unresolved_disappearance" if unresolved else "unclassified", 1, pid)
            else:
                add("in_missing_run_after_first_row", 1, pid)
    refused_member_days = 0
    identity_member_days = 0
    persistent = 0
    overlap_cells: dict[str, set[int]] = {}
    span = ctx.d_last - ctx.d0 + 1
    for row in ctx.intervals.to_dict(orient="records"):
        resolution = row["resolution"]
        cells = _interval_rows(ctx, row)
        if resolution.startswith("no_containing_episode:no_vendor_bars:"):
            key = "no_vendor_bars:" + resolution.rsplit(":", 1)[1]
        elif resolution == "no_containing_episode:rekeyed_rename_candidate":
            key = ("no_vendor_bars:" + normalized_eod_subreason(row["eod_status"])
                   if row["eod_status"] in REKEY_STATUSES else "no_bars_in_interval")
        elif resolution == "no_containing_episode:no_bars_in_interval":
            key = "no_bars_in_interval"
        elif resolution == "raw_overlap":
            overlap_cells.setdefault(row["vendor_code"], set()).update(cells.tolist())
            continue
        elif resolution in ("entry_missing_field", "entry_unparseable_date"):
            add("entry_unusable_upper_bound", span)
            refused_member_days += span
            continue
        else:
            if row["census_cap"] == "R-CENSUS-3":
                identity_member_days += len(cells)
            continue
        add(key, len(cells))
        refused_member_days += len(cells)
        if key == "no_vendor_bars:persistent_provider_error":
            persistent += len(cells)
    overlap = sum(len(cells) for cells in overlap_cells.values())
    add("raw_overlap", overlap)
    refused_member_days += overlap
    eligible_total = member_days + refused_member_days
    unpriced = sum(reasons.values())
    member_days_all = eligible_total + identity_member_days
    public = {
        "member_days_total": member_days, "member_days_with_bar": with_bar,
        "member_days_missing_bar": member_days - with_bar,
        "eligible_unpriced_member_days": dict(sorted(reasons.items())),
        "eligible_unpriced_member_days_total": unpriced,
        "eligible_member_days": eligible_total,
        "eligible_unpriced_fraction": unpriced / eligible_total if eligible_total else 0.0,
        "identity_refused_member_days": identity_member_days,
        "identity_refusal_fraction": identity_member_days / member_days_all if member_days_all else 0.0,
    }
    return ({"public": public, "unpriced_fraction": public["eligible_unpriced_fraction"],
             "identity_refusal_fraction": public["identity_refusal_fraction"], "member_days_all": member_days_all,
             "persistent_member_days": persistent, "eligible_member_days": eligible_total},
            {pid: dict(sorted(values.items())) for pid, values in sorted(detail.items())})


def _identity(ctx: Context, membership: pd.DataFrame) -> dict[str, Any]:
    results = ctx.intervals.to_dict(orient="records")
    entry_codes = ("entry_missing_field", "entry_unparseable_date", "degenerate_interval", "raw_overlap")
    refusals: dict[str, dict[str, int]] = {}
    entries: dict[str, int] = {}
    detail = []
    for row in results:
        resolution = row["resolution"]
        if resolution in entry_codes:
            entries[resolution] = entries.get(resolution, 0) + 1
        elif resolution not in ("resolved", "exact_duplicate_collapsed"):
            bucket = refusals.setdefault(resolution, {"intervals": 0, "member_days": 0})
            bucket["intervals"] += 1
            bucket["member_days"] += int(row["member_days_disc"] or 0)
        if resolution != "resolved":
            detail.append({"interval_id": row["interval_id"], "resolution": resolution,
                           "member_days_disc": int(row["member_days_disc"] or 0), "census_cap": row["census_cap"]})
    masters = ctx.master[ctx.master["permanent_id"] != ""]
    episodes_per_code = masters.groupby("vendor_code").size().value_counts().sort_index()
    resolved = [row for row in results if row["resolution"] == "resolved"]
    per_episode = pd.Series([row["permanent_id"] for row in resolved]).value_counts().value_counts().sort_index()
    rekeyed = [row for row in results if row["resolution"] == "no_containing_episode:rekeyed_rename_candidate"]
    return {
        "ever_members": {
            "ever_member_codes": len(membership_codes(membership)),
            "permanent_ids": int(len(masters)),
            "episodes_per_code": {str(k): int(v) for k, v in episodes_per_code.items()},
            "acquirer_only_ids": int((masters["role"] == "acquirer_only").sum()),
            "membership_intervals": len(results),
            "intervals_per_episode": {str(k): int(v) for k, v in per_episode.items()},
        },
        "identity": {
            "identity_refusals_by_code": dict(sorted(refusals.items())),
            "entry_refusals_by_code": dict(sorted(entries.items())),
            "exact_duplicate_entries_collapsed": sum(row["resolution"] == "exact_duplicate_collapsed" for row in results),
            "rekeyed_rename_candidates": len(rekeyed),
            "rekeyed_rename_candidate_member_days": sum(int(row["member_days_disc"] or 0) for row in rekeyed),
            "name_mismatch_recorded": ctx.build["name_mismatch_recorded"],
        },
        "detail": detail,
    }


def _cells(ctx: Context, mask: pd.DataFrame, pid: str) -> int:
    return int(mask[pid].to_numpy()[ctx.window].sum()) if pid in mask.columns else 0


def _episode_metrics(ctx: Context, mask: pd.DataFrame) -> dict[str, Any]:
    build = ctx.build
    checks = build["episode_checks"]
    refused_by_reason: dict[str, dict[str, int]] = {}
    for row in ctx.master.to_dict(orient="records"):
        if row["episode_panel_refusal"]:
            bucket = refused_by_reason.setdefault(row["episode_panel_refusal"], {"episodes": 0, "member_days": 0})
            bucket["episodes"] += 1
            bucket["member_days"] += _cells(ctx, mask, row["permanent_id"])
    refused_drift = {"(2e-3,1e-2]": 0, ">1e-2": 0}
    distribution_drift = {"episodes": 0, "member_days": 0}
    rounding = {"<0.1": 0, "[0.1,1)": 0, ">=1": 0}
    by_evidence = {"valid": 0, "unavailable": 0}
    unavailable_member_days = 0
    for check in checks:
        state = "valid" if check["dividend_evidence"] else "unavailable"
        by_evidence[state] += len(check["failing_pairs"])
        refusal = check["refusal"]
        if refusal and not check["dividend_evidence"] and refusal.startswith("split_basis_unverified:"):
            unavailable_member_days += _cells(ctx, mask, check["permanent_id"])
        if refusal == "split_basis_unverified:cumulative_basis_drift":
            refused_drift["(2e-3,1e-2]" if check["max_cumulative_drift"] <= 1e-2 else ">1e-2"] += 1
            if check["dividend_pairs"]:
                distribution_drift["episodes"] += 1
                distribution_drift["member_days"] += _cells(ctx, mask, check["permanent_id"])
        residuals = [pair["residual"] for pair in check["failing_pairs"]]
        if refusal == "split_basis_unverified:in_span_step_mismatch" and residuals and all(
                r is not None and 1e-3 < r <= 1e-2 for r in residuals):
            level = check["min_adjusted_close"]
            rounding["<0.1" if level < 0.1 else "[0.1,1)" if level < 1 else ">=1"] += _cells(ctx, mask, check["permanent_id"])
    missing_history, partial_history = _history(ctx)
    coverage = {
        "codes_missing_history": missing_history, "codes_partial_history": partial_history,
        "episodes_without_panel_by_reason": dict(sorted(refused_by_reason.items())),
        "split_basis_check_by_outcome": build["split_basis_check_by_outcome"],
        "split_basis_refusals_with_later_distribution": build["split_basis_refusals_with_later_distribution"],
        "in_span_step_check_by_outcome": build["in_span_step_check_by_outcome"],
        "failing_pairs_by_kind": build["failing_pairs_by_kind"],
        "failing_pairs_by_residual_bucket": build["failing_pairs_by_residual_bucket"],
        "failing_pairs_by_dividend_evidence": by_evidence,
        "member_days_refused_while_dividend_evidence_unavailable": unavailable_member_days,
        "written_max_cumulative_drift_by_bucket": build["written_max_cumulative_drift_by_bucket"],
        "refused_max_cumulative_drift_by_bucket": refused_drift,
        "cumulative_basis_drift_refusals_with_declared_distribution": distribution_drift,
        "rounding_refusals_by_min_adjusted_level": rounding,
        "dividend_rows_amount_undefined": build["dividend_rows_amount_undefined"],
        "split_rows_unattributed": build["split_rows_unattributed"],
        "split_rows_after_final_bar": build["split_rows_after_final_bar"],
        "split_rows_before_first_bar": sum(build["split_rows_before_first_bar"].values()),
    }
    written = [pid for pid in ctx.panels if pid in mask.columns]
    support = pd.read_parquet(ctx.snapshot.root / DISTRIBUTION_SUPPORT)
    support = support.assign(date=pd.DatetimeIndex(support["date"]))
    b_values, s_values = [], []
    for pid in written:
        rows = ctx.calendar[ctx.window][mask[pid].to_numpy()[ctx.window]]
        rows = rows[rows.isin(ctx.panels[pid].index)]
        own = support[support["permanent_id"] == pid].set_index("date")
        b_values.extend(own["b_d"].reindex(rows).fillna(0.0).tolist())
        s_values.extend(own["s_d"].reindex(rows).fillna(0.0).tolist())
    distribution_pids = [c["permanent_id"] for c in checks if c["dividend_pairs"] and c["refusal"] is None]
    distribution_days = sum(_cells(ctx, mask, pid) for pid in distribution_pids)
    eligible = sum(_cells(ctx, mask, pid) for pid in mask.columns)
    above = int(sum(value > VP2_LEVEL for value in s_values))

    def quantiles(values: list[float]) -> dict[str, float | None]:
        if not values:
            return {"median": None, "p90": None, "max": None}
        array = np.array(values)
        return {"median": float(np.median(array)), "p90": float(np.quantile(array, 0.9)), "max": float(array.max())}

    distribution_support = {
        "written_episodes_with_declared_distribution_pair": len(distribution_pids),
        "member_days": distribution_days, "fraction_of_eligible_member_days": distribution_days / eligible if eligible else 0.0,
        "b_d": quantiles(b_values), "s_d": quantiles(s_values), "member_days_s_d_above_0_05": above,
    }
    return {
        "coverage": coverage,
        "distribution_support": distribution_support,
        "vp2_revisit_required": bool(eligible and above > VP2_SHARE * eligible),
        "volume_basis": volume_basis_diagnostic(_volume_ells(ctx, checks)),
        "quality": _quality(ctx, mask),
        "corporate_actions": _corporate_actions(ctx),
        "exits": _exits(ctx),
    }


def _history(ctx: Context) -> tuple[dict[str, int], int]:
    missing: dict[str, int] = {}
    partial = 0
    snapshot = ctx.snapshot
    for code, rows in ctx.intervals.groupby("vendor_code"):
        if not code:
            continue
        pids = [pid for pid in rows["permanent_id"] if pid]
        if not any(pid in ctx.panels for pid in pids):
            status = snapshot.status("eod", code)
            partition = snapshot.discovery_status("eod", code)
            if status == "retrieved" and partition.startswith("quarantined:"):
                reason = f"discovery_partition_{partition}"
            elif status == "retrieved":
                reason = "retrieved_no_discovery_panel"
            else:
                reason = status
            missing[reason] = missing.get(reason, 0) + 1
        starts = [_row(ctx.calendar, text) for text in rows["m_in"] if text]
        firsts = [_row(ctx.calendar, r["first_bar"]) for r in ctx.master.to_dict(orient="records") if r["vendor_code"] == code]
        if starts and firsts and min(firsts) - (min(starts) - 1) > E1_GAP_ROWS:
            partial += 1
    return dict(sorted(missing.items())), partial


def _volume_ells(ctx: Context, checks: list[dict[str, Any]]) -> list[tuple[float, float | None]]:
    ells = []
    for check in checks:
        panel = ctx.panels.get(check["permanent_id"])
        if panel is None or check["refusal"] is not None:
            continue
        turnover = (panel["close"] / panel["split_factor"] * panel["volume"]).to_numpy()
        dates = panel.index
        for split in check["attributed_splits"]:
            ratio = split["ratio"]
            if abs(math.log(ratio)) < math.log(1.25):
                continue
            position = int(dates.searchsorted(pd.Timestamp(split["date"])))
            before, after = turnover[max(0, position - VOLUME_BASIS_BARS):position], turnover[position:position + VOLUME_BASIS_BARS]
            if len(before) == VOLUME_BASIS_BARS and len(after) == VOLUME_BASIS_BARS:
                medians = float(np.median(before)), float(np.median(after))
                ell = math.log(medians[1] / medians[0]) / math.log(ratio) if min(medians) > 0 else None
                ells.append((ratio, ell))
    return ells


def _quality(ctx: Context, mask: pd.DataFrame) -> dict[str, Any]:
    window_dates = ctx.calendar[ctx.window]
    zero = 0
    closes = {}
    per_year: dict[str, dict[str, int]] = {}
    for pid, panel in ctx.panels.items():
        if pid not in mask.columns:
            continue
        eligible = pd.Series(mask[pid].to_numpy()[ctx.window], index=window_dates)
        volume = panel["volume"].reindex(window_dates)
        zero_rows = eligible & volume.eq(0.0)
        zero += int(zero_rows.sum())
        closes[pid] = panel["adjusted_close"].reindex(ctx.calendar[ctx.i_h:])
        for year, count in zero_rows.groupby(zero_rows.index.year).sum().items():
            per_year.setdefault(str(year), {"zero_volume_member_days": 0})["zero_volume_member_days"] += int(count)
    frame = pd.DataFrame(closes, index=ctx.calendar[ctx.i_h:])
    report = report_unchanging_price_segments(frame)
    for year, values in frame.groupby(frame.index.year):
        per_year.setdefault(str(year), {"zero_volume_member_days": 0})["unchanging_price_segments"] = \
            report_unchanging_price_segments(values).segment_count
    return {"zero_volume_member_days": zero,
            "unchanging_price_segments": {"segment_count": report.segment_count, "assets_affected": report.assets_affected,
                                          "max_run_length": report.max_run_length},
            "discovery_years": dict(sorted(per_year.items()))}


def _corporate_actions(ctx: Context) -> dict[str, Any]:
    snapshot = ctx.snapshot
    calendar_rows = {day: row for row, day in enumerate(ctx.calendar)}
    split_rows = dividend_rows = without_discontinuity = without_split = 0
    per_year: dict[str, dict[str, int]] = {}
    member_codes = sorted({code for code in ctx.intervals["vendor_code"] if code})
    for code in member_codes:
        splits = snapshot.read_discovery("splits", code) if snapshot.evidence_valid("splits", code) else None
        dividends = snapshot.read_discovery("dividends", code) if snapshot.evidence_valid("dividends", code) else None
        split_dates = pd.DatetimeIndex([]) if splits is None else pd.DatetimeIndex(splits["date"])
        split_rows += len(split_dates)
        dividend_dates = pd.DatetimeIndex([]) if dividends is None else pd.DatetimeIndex(dividends["date"])
        dividend_rows += len(dividend_dates)
        for label, dates in (("split_rows", split_dates), ("dividend_rows", dividend_dates)):
            for year in dates.year:
                bucket = per_year.setdefault(str(year), {"split_rows": 0, "dividend_rows": 0})
                bucket[label] += 1
        frame = snapshot.read_discovery("eod", code)
        if frame is None:
            continue
        frame = frame.assign(date=pd.DatetimeIndex(frame["date"])).set_index("date")
        frame = frame[frame.index.isin(list(calendar_rows))]
        rows = np.array([calendar_rows[d] for d in frame.index])
        scale = (frame["close"] / frame["adjusted_close"]).to_numpy()
        split_calendar_rows = [int(ctx.calendar.searchsorted(d)) for d in split_dates]
        matched = set()
        for j in range(len(rows) - 1):
            if rows[j + 1] - rows[j] - 1 > E1_GAP_ROWS:
                continue
            step = abs(scale[j + 1] / scale[j] - 1.0) > SCALE_STEP
            inside = [i for i, d in enumerate(split_dates) if frame.index[j] < d <= frame.index[j + 1]]
            if step:
                matched.update(inside)
                if not any(abs(r - rows[j + 1]) <= SPLIT_WINDOW_ROWS for r in split_calendar_rows):
                    without_split += 1
        without_discontinuity += len(split_dates) - len(matched)
    return {"split_rows": split_rows, "dividend_rows": dividend_rows,
            "splits_without_discontinuity": without_discontinuity, "discontinuities_without_split": without_split,
            "e5_not_evaluated_holdout_rows": sum(ctx.build["e5_not_evaluated_holdout_rows"].values()),
            "discovery_years": dict(sorted(per_year.items()))}


def _exits(ctx: Context) -> dict[str, Any]:
    by_year: dict[str, dict[str, int]] = {}
    for row in ctx.intervals.to_dict(orient="records"):
        if row["exit_class"]:
            year = row["R_exit"][:4]
            by_year.setdefault(year, {})[row["exit_class"]] = by_year.setdefault(year, {}).get(row["exit_class"], 0) + 1
    candidates = ctx.intervals[ctx.intervals["exit_class"] == "delisting_candidate"]
    return {"exits_by_class_by_year": dict(sorted(by_year.items())),
            "exits_by_class": ctx.intervals.loc[ctx.intervals["exit_class"] != "", "exit_class"].value_counts().sort_index().to_dict(),
            "delisting_candidate_intervals": int(len(candidates)),
            "delisting_candidate_episodes": int(candidates["permanent_id"].nunique())}


def _terminal(ctx: Context) -> dict[str, Any]:
    rows = ctx.validation["rows"]
    attributed = {c["permanent_id"] for c in ctx.build["episode_checks"] if c["outcome"] == "attributed_applied"}
    candidates = set(ctx.intervals.loc[ctx.intervals["exit_class"] == "delisting_candidate", "permanent_id"])

    def count(key: str, values: list[dict[str, Any]]) -> dict[str, int]:
        result: dict[str, int] = {}
        for row in values:
            label = row[key] or "unresolved"
            result[label] = result.get(label, 0) + 1
        return dict(sorted(result.items()))

    unresolved = [row for row in rows if row["status"] == "unresolved"]
    return {
        "delistings_by_consideration_type": count("consideration_type", rows),
        "delistings_by_event_kind": count("event_kind", rows),
        "curated": sum(1 for row in rows if row["status"] == "accepted" or
                       (row["status"] == "unresolved" and row["validation_reason"] != "curation_unresolved")),
        "accepted": sum(1 for row in rows if row["status"] == "accepted"),
        "unresolved_by_reason": count("validation_reason", unresolved),
        "deferred_holdout": sum(1 for row in rows if row["status"] == "deferred_holdout"),
        "settlement_lag_distribution": ctx.validation["settlement_lag_distribution"],
        "valuation_row_offsets": ctx.validation["valuation_row_offsets"],
        "attributed_applied_delisting_candidates": len(attributed & candidates),
    }


def _table_status_counts(snapshot: Snapshot, membership: pd.DataFrame) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {table: {} for table in TABLES}
    for code in request_list(snapshot, membership):
        for table in TABLES:
            status = snapshot.status(table, code)
            counts[table][status] = counts[table].get(status, 0) + 1
    return {table: dict(sorted(values.items())) for table, values in counts.items()}


def _evidence_basis_counts(snapshot: Snapshot, membership: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    for code in request_list(snapshot, membership):
        entry = snapshot.entry("eod", code) or {}
        basis = entry.get("split_evidence_basis") or "none"
        counts[basis] = counts.get(basis, 0) + 1
    return dict(sorted(counts.items()))


def _incomplete_counts(verify: dict[str, Any]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for table, codes in verify.get("incomplete_codes_by_table_and_status", {}).items():
        for status in codes.values():
            counts.setdefault(table, {})[status] = counts.setdefault(table, {}).get(status, 0) + 1
    return counts


def _integrity(snapshot: Snapshot, seal: dict[str, Any], verify: dict[str, Any]) -> dict[str, Any]:
    typed = all(
        status == "valid" or (status.startswith("quarantined:") and len(status) > len("quarantined:"))
        for entry in snapshot.manifest.get("entries", {}).values()
        for status in entry.get("partition_statuses", {}).values()
    )
    seal_inputs = seal.get("inputs", {}) == {
        "components_raw_sha256": snapshot.manifest["files"]["membership"]["sha256"],
        "components_retrieved_utc_date": snapshot.manifest["snapshot"]["components_retrieved_utc_date"],
    }
    checks = {
        "verify_ran": bool(verify), "token_leak_free": not verify.get("token_leak_detected", ["unverified"]),
        "quarantine_typed": typed, "split_evidence_current": not verify.get("split_evidence_stale", ["unverified"]),
        "hashes_verify": not verify.get("artifact_hash_mismatch", ["unverified"]), "seal_inputs_match": seal_inputs,
    }
    return {"passed": all(checks.values()), "checks": checks}


def _holdout_integrity(snapshot: Snapshot) -> dict[str, Any]:
    counters = snapshot.manifest.get("counters", {})
    passed: dict[str, int] = {table: 0 for table in TABLES}
    for key, entry in snapshot.manifest.get("entries", {}).items():
        table = key.split("/", 1)[0]
        if entry.get("partition_statuses", {}).get("holdout") == "valid":
            passed[table] += 1
    return {
        "files_passed": passed,
        "files_quarantined": {table: counters.get(f"{table}_holdout_quarantined", 0) for table in TABLES},
        "date_structure_refusals": {table: counters.get(f"{table}_date_structure_refusals", 0) for table in TABLES},
    }


# ---------------------------------------------------------------- report


def render_markdown(public: dict[str, Any]) -> str:
    readiness = public["census_readiness"]
    identity = public["snapshot_identity"]
    support = public["in_span_distribution_support"]
    volume = public["volume_basis_split_diagnostic"]
    coverage = public["price_coverage"]
    exclusion = public["exclusion_set"]
    lines = [
        "# M4.7 Coverage Census",
        "",
        "Evidence ceiling: `DIAGNOSTIC_ONLY`. No figure below supports a ranking, selection, promotion, or "
        "profitability claim.",
        "",
        f"- Snapshot id: `{public['snapshot_id']}`",
        f"- Code commit: `{public['code_commit']}`",
        f"- Seal: prospective SHA-256 `{identity['seal_prospective_sha256']}`; holdout end "
        f"`{public['discovery_window']['holdout_end']}`",
        f"- Readiness: `{readiness['status']}`" + (
            f" ({', '.join(f['result'] for f in readiness['failures'])})" if readiness["failures"] else ""),
        f"- manifest_sha256: `{identity['manifest_sha256']}`",
        f"- discovery_inputs_sha256: `{identity['discovery_inputs_sha256']}`",
        f"- segments_sha256: `{identity['segments_sha256']}`",
        "",
        "## Premises and owner disposition",
        "",
        f"- VP-1: {public['premises']['VP-1']}; `a1_volume_half = {volume['a1_volume_half']}` over {volume['rows']} rows, "
        f"median ell {volume['median_ell']}, share above 0.5 at ratio >= 2: {volume['share_ell_above_half_at_ratio_2']}.",
        f"- VP-2: {public['premises']['VP-2']}; written episodes with a declared-distribution pair: "
        f"{support['written_episodes_with_declared_distribution_pair']}; B_D max {support['b_d']['max']}; "
        f"S_D max {support['s_d']['max']}; member-days with S_D > 0.05: {support['member_days_s_d_above_0_05']}; "
        f"vp2_revisit_required: {public['vp2_revisit_required']}.",
        f"- O-8: {public['premises']['O-8']}.",
        f"- Rounding: {public['premises']['rounding_selection']}; refused member-days by minimum adjusted level: "
        f"{coverage['rounding_refusals_by_min_adjusted_level']}.",
        "- Survivorship: members without a discovery panel are unpriced eligible member-days, capped by R-CENSUS-9.",
        "- Discovery overlap with prior exposures: " + ", ".join(
            f"{kind} {value['fraction_of_ic_months']:.4f}" for kind, value in public["discovery_overlap_with_prior_exposures"].items()),
        "",
        "## Readiness rules",
        "",
        "| Rule | Passed |",
        "| --- | --- |",
        *[f"| {rule} | {value['passed']} |" for rule, value in readiness["rules"].items()],
        "",
        "## Coverage",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Eligible member-days | {coverage['eligible_member_days']} |",
        f"| Eligible unpriced member-days | {coverage['eligible_unpriced_member_days_total']} |",
        f"| Eligible unpriced fraction | {coverage['eligible_unpriced_fraction']:.6f} |",
        f"| Identity refusal fraction | {coverage['identity_refusal_fraction']:.6f} |",
        f"| Gap windows | {exclusion['gap_window_count']} |",
        f"| Excluded fraction | {exclusion['excluded_fraction']:.6f} |",
        f"| IC month supply | {public['ic_supply']['ic_month_supply']} |",
        f"| Kill reachable (projection) | {public['power_projection']['kill_reachable_projection']} |",
        "",
        "## Gap windows (month granularity)",
        "",
        "| Start month | End month | Reasons | Rows |",
        "| --- | --- | --- | --- |",
        *[f"| {w['start_month']} | {w['end_month']} | {', '.join(w['reason_types'])} | {w['rows']} |"
          for w in exclusion["gap_windows"]],
        "",
        "## Holdout integrity (metadata)",
        "",
        *[f"- {key}: {value}" for key, value in public["corporate_actions"]["corporate_action_partitions_quarantined"].items()
          if "holdout" in key],
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m research.m4_7_coverage_census")
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--reports-dir", default=None)
    parser.add_argument("--seal-out", default=None)
    args = parser.parse_args(argv)
    try:
        result = run_census(snapshot_dir_from_args(args), reports_dir=args.reports_dir, seal_out=args.seal_out)
    except SnapshotRefusal as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"census_readiness": result["public"]["census_readiness"]["status"],
                      "census_json_sha256": result["census_json_sha256"],
                      "seal_confirmed_sha256": result["seal_confirmed_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
