"""Coverage census, readiness, power projection, and seal confirmation for M4.7 (plan section 5) and M4.8.

Runs after the universe build and the terminal projection and before any
factor computation. Refuses ``derived_artifact_stale`` before any metric when
a derived input no longer matches the current manifest (S7). Writes the
private ``census/census_detail_v2.json`` and ``census/asset_support.json``
into the snapshot, the public count-only ``reports/m4_7_coverage_census_v2.{json,md}``,
and the v2 confirmation of the seal record. Support v2 isolates a missing bar or
an unevidenced disappearance to the affected asset and holding period; the v1
census outputs and seal record stay unchanged as history. Every figure is ``DIAGNOSTIC_ONLY``; nothing here
supports a ranking, selection, or profitability claim (R2, R10).

Run as ``python -m research.m4_7_coverage_census --snapshot-id <ID>``.

M4.8 (plan section 5) adds two subcommands. ``membership-census`` reads
membership metadata and the private curation files only and fixes
``coverage_start_pre``, ``D0_pre``, and gate G1. ``census-v3`` runs on a rule
v2 snapshot after the universe build and takes the terminal summary and the
per-segment access logs from the later stages; it writes the private detail and
the count-only public ``reports/m4_8_coverage_census_v3.{json,md}``. Both
refuse to publish a payload that holds a code, a name, or a private path
(T-PUB-1).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm

from data import holdout_partition
from data.holdout_partition import (
    SEAL_FILE,
    SEAL_RULE_VERSION,
    SEAL_RULES,
    SnapshotRefusal,
    coverage_start,
    monthly_raw_counts,
    parse_strict_date,
    sha256_bytes,
)
from research import m4_8_membership
from research.m4_7_common_support import SUPPORT_CONTRACT, ic_month_set, scheduled_reset_rows, write_support_files
from research.m4_7_family_a import FAMILY_A
from research.m4_7_holdout_seal import confirmed_seal_bytes
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
    Segment,
    Snapshot,
    _parquet,
    canonical_json,
    discovery_segments,
    discovery_window,
    membership_codes,
    normalized_eod_subreason,
    read_bar_dates,
    read_derived_json,
    request_list,
    require_current,
    reset_in_month,
    segment_ic_resets,
    snapshot_dir_from_args,
    write_bytes,
)
from backtest.portfolio import resolve_pit_universe_mask
from data.constituent_table import load_constituent_intervals_csv
from research.unchanging_price import report_unchanging_price_segments


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = "m4_7_coverage_census_v2.json"
REPORT_MD = "m4_7_coverage_census_v2.md"
CENSUS_DETAIL = "census/census_detail_v2.json"
SEAL_CONFIRMATION = REPOSITORY_ROOT / "docs/preregistrations/m4_7_holdout_seal_v1_confirmation_v2.json"
IDENTITY_CAP, OFF_CALENDAR_CAP, UNPRICED_CAP = 0.05, 0.001, 0.02
MAX_EXCLUDED_FRACTION = 0.05
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
    "shortfall": "ready_with_caveats:coverage_shortfall_accepted",
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


def derive_readiness(inputs: dict[str, Any], rule_version: str = SEAL_RULE_VERSION) -> dict[str, Any]:
    """Plan 5.3: every rule's inputs and result; ``ready`` needs all ten rules.

    The in-band, prior-exposure, and IC-month minima come from the seal rule
    (``data.holdout_partition.SEAL_RULES``); the other caps are fixed. A failed
    R-CENSUS-1, 2, 8, or 9 whose value stays inside the rule's owner-accepted
    shortfall bounds is the caveat ``coverage_shortfall_accepted``; the rule's
    ``passed`` flag still reports the registered threshold. Under support v2,
    R-CENSUS-2 reads the asset-level excluded fraction: support-excluded cells
    over signal-eligible cells at the evaluation resets.
    """
    seal_rule = SEAL_RULES[rule_version]
    cap = None if seal_rule["latest_holdout_end"] is None else seal_rule["latest_holdout_end"].isoformat()
    overlaps = cap is not None and inputs["holdout_end"] > cap
    results = {
        "R-CENSUS-1": inputs["in_band_years"] >= seal_rule["min_in_band_years"] and not overlaps,
        "R-CENSUS-2": inputs["excluded_fraction"] <= MAX_EXCLUDED_FRACTION,
        "R-CENSUS-3": inputs["identity_refusal_fraction"] <= IDENTITY_CAP,
        "R-CENSUS-4": inputs["off_calendar_fraction"] <= OFF_CALENDAR_CAP,
        "R-CENSUS-5": inputs["calendar_covers_coverage_start"] and inputs["benchmark_complete"],
        "R-CENSUS-6": inputs["snapshot_integrity"],
        "R-CENSUS-7": inputs["holdout_band_after_identity"],
        "R-CENSUS-8": inputs["ic_month_supply"] >= seal_rule["min_ic_months"],
        "R-CENSUS-9": inputs["unpriced_fraction"] <= UNPRICED_CAP,
        "R-CENSUS-10": inputs["retrieval_complete"],
    }
    bounds = seal_rule["accepted_shortfall"]
    accepted = {} if bounds is None else {
        "R-CENSUS-1": inputs["in_band_years"] >= bounds["min_in_band_years"] and not overlaps,
        "R-CENSUS-2": inputs["excluded_fraction"] <= bounds["max_excluded_fraction"],
        "R-CENSUS-8": inputs["ic_month_supply"] >= bounds["min_ic_months"],
        "R-CENSUS-9": inputs["unpriced_fraction"] <= bounds["max_unpriced_fraction"],
    }
    failures = []
    for rule, passed in results.items():
        if passed:
            continue
        code = FAILURE_CODES["shortfall"] if accepted.get(rule) else FAILURE_CODES[rule]
        if rule == "R-CENSUS-1" and overlaps:
            code = "blocked:holdout_overlaps_prior_exposure"
        if rule == "R-CENSUS-5" and inputs["calendar_covers_coverage_start"]:
            code = "blocked:benchmark_gap"
        failures.append({"rule": rule, "result": code})
    caveats = sorted({f["result"].split(":", 1)[1] for f in failures if f["result"].startswith("ready_with_caveats:")})
    if not failures:
        status = "ready"
    elif len(caveats) == len({f["result"] for f in failures}):
        status = "ready_with_caveats:" + ",".join(caveats)
    else:
        status = "blocked"
    thresholds = {"seal_rule_version": rule_version, "min_in_band_years": seal_rule["min_in_band_years"],
                  "latest_holdout_end": cap, "min_ic_months": seal_rule["min_ic_months"],
                  "accepted_shortfall": bounds}
    return {"status": status, "failures": failures, "rules": {name: {"passed": bool(ok)} for name, ok in results.items()},
            "inputs": inputs, "thresholds": thresholds}


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
    """Compute the census and write every output; return the public JSON, the detail, and the digests.

    The v2 census derives coverage starts from counts, so it refuses on a
    carried seal (``seal_window_recompute_forbidden``); census v3 serves rule v2.
    """
    holdout_partition.refuse_carried_window_recompute(Path(snapshot_dir))
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
    coverage, detail_unpriced = _unpriced(ctx, mask)
    identity = _identity(ctx, membership)
    episodes = _episode_metrics(ctx, mask)
    ic_included, ic_excluded = ic_month_set(support.schedule)
    reset_dates = [support.calendar[r].date() for r in ic_included]
    schedule = support.schedule
    warmup = post_join_warmup_estimate(schedule.evaluation_mask, support.bars, ic_included)
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
        "excluded_fraction": schedule.excluded_fraction,
        "identity_refusal_fraction": coverage["identity_refusal_fraction"],
        "off_calendar_fraction": off_calendar / coverage["member_days_all"] if coverage["member_days_all"] else 0.0,
        "calendar_covers_coverage_start": calendar[0].date().isoformat() <= coverage_start_sealed,
        "benchmark_complete": bool(benchmark_complete), "snapshot_integrity": integrity["passed"],
        "holdout_band_after_identity": breadth["holdout_band_after_identity"],
        "ic_month_supply": len(ic_included), "unpriced_fraction": coverage["unpriced_fraction"],
        "retrieval_complete": bool(verify.get("retrieval_complete", False)),
    }
    readiness = derive_readiness(readiness_inputs, seal["rule_version"])
    status_counts = _table_status_counts(snapshot, membership)
    counters = snapshot.manifest.get("counters", {})
    public = {
        "schema_version": "m4_7_coverage_census_v2",
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
                     "calendar_source": seal["calendar_source"],
                     "max_reset_to_reset_rows": schedule.max_reset_to_reset_rows},
        "price_coverage": {**coverage["public"], **episodes["coverage"]},
        "asset_support": {
            "support_contract": SUPPORT_CONTRACT, "unresolved_events": record["unresolved_in_window"],
            "evaluation_resets": record["evaluation_resets"], "signal_eligible_cells": record["signal_eligible_cells"],
            "excluded_cells": record["excluded_cells"], "excluded_fraction": record["excluded_fraction"],
            "excluded_cells_by_reason": record["excluded_cells_by_reason"],
            "evaluated_breadth": _breadth_summary(record["breadth"]),
            "breadth_by_reset": record["breadth"],
            "support_sha256": support.support_sha256,
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
            "support_sha256": support.support_sha256,
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
    seal_confirmed = write_bytes(Path(seal_out) if seal_out is not None else SEAL_CONFIRMATION, confirmed)
    return {"public": public, "detail": detail, "census_json_sha256": census_sha,
            "seal_prospective_sha256": sha256_bytes(seal_bytes_prospective), "seal_confirmed_sha256": seal_confirmed}


def _breadth_summary(breadth: list[dict[str, Any]]) -> dict[str, Any]:
    """Minimum, median, and maximum evaluated names over the evaluation resets."""
    values = [row["evaluated"] for row in breadth]
    return {"min": min(values, default=0), "median": float(np.median(values)) if values else 0.0,
            "max": max(values, default=0)}


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


def _unpriced(ctx: Context, mask: pd.DataFrame) -> tuple[dict[str, Any], dict[str, dict[str, int]]]:
    """Section 5.2 ``eligible_unpriced_member_days`` with R-CENSUS-3 and R-CENSUS-9 counts."""
    window = ctx.window
    masters = {r["permanent_id"]: r for r in ctx.master.to_dict(orient="records") if r["permanent_id"]}
    settled = set(read_engine_events(ctx.snapshot.root)["permanent_id"])
    reasons: dict[str, int] = {}
    detail: dict[str, dict[str, int]] = {}
    member_days = 0
    with_bar = 0

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
        for r in rows:
            if r in panel_rows:
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
        "volume_basis": volume_basis_diagnostic(_volume_ells(ctx.panels, checks)),
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


def _volume_ells(panels: dict[str, pd.DataFrame], checks: list[dict[str, Any]]) -> list[tuple[float, float | None]]:
    """VP-1 input: per attributed split of ratio 1.25 or more, the 20-bar median dollar-turnover elasticity."""
    ells = []
    for check in checks:
        panel = panels.get(check["permanent_id"])
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


# ---------------------------------------------------------------- M4.8 membership census and census v3 (plan 5)


MEMBERSHIP_REPORT = "m4_8_membership_census"
MEMBERSHIP_DETAIL = "membership_census_detail.json"
CENSUS_V3_REPORT = "m4_8_coverage_census_v3"
CENSUS_V3_DETAIL = "census/census_detail_v3.json"
MIN_PRE_IC_MONTHS, MIN_TOTAL_IC_MONTHS = 34, 60
R3_2C_CAP, R3_3_CAP, R3_5_CAP, R3_10_CAP = 0.01, 0.05, 0.001, 0.05
UNEXPOSED_BEFORE = date(2016, 8, 8)
READINESS_V3 = (
    ("R3-1", "blocked:insufficient_pre_segment"),
    ("R3-2a", "blocked:unresolved_membership_changes"),
    ("R3-2b", "blocked:anchor_count_delta"),
    ("R3-2c", "blocked:unpriced_absent_members"),
    ("R3-3", "blocked:unpriced_eligible_member_days"),
    ("R3-4", "blocked:residual_unevidenced_disappearance"),
    ("R3-5", "ready_with_caveats:halt_frequency"),
    ("R3-6", ""),
    ("R3-7", "blocked:insufficient_ic_months"),
    ("R3-8", "ready_with_caveats:vp2_revisit"),
    ("R3-9", "blocked:seal_carry_mismatch"),
    ("R3-10", "ready_with_caveats:membership_discrepancies"),
)


def derive_readiness_v3(inputs: dict[str, Any]) -> dict[str, Any]:
    """Plan 5.3: rules R3-1..R3-10 in table order.

    ``ready`` when every rule passes; ``ready_with_caveats:<rules>`` when only
    caveat rules fail; otherwise ``blocked:<code>`` of the first failing
    blocking rule. Every failing rule is listed. R3-2c and R3-3 take one
    fraction per segment, and a ``None`` fraction (zero denominator,
    ``not_evaluable``) fails. R3-6 applies the M4.7 rules R-CENSUS-3..7 and 10
    with their codes.
    """
    m47 = {
        "R-CENSUS-3": inputs["identity_refusal_fraction"] <= IDENTITY_CAP,
        "R-CENSUS-4": inputs["off_calendar_fraction"] <= OFF_CALENDAR_CAP,
        "R-CENSUS-5": inputs["calendar_covers_coverage_start"] and inputs["benchmark_complete"],
        "R-CENSUS-6": inputs["snapshot_integrity"],
        "R-CENSUS-7": inputs["holdout_band_after_identity"],
        "R-CENSUS-10": inputs["retrieval_complete"],
    }

    def per_segment(values: dict[str, float | None], cap: float) -> bool:
        return bool(values) and all(value is not None and value <= cap for value in values.values())

    fraction = inputs["unresolved_change_fraction"]
    results = {
        "R3-1": inputs["pre_ic_months"] >= MIN_PRE_IC_MONTHS,
        "R3-2a": fraction is not None and fraction <= m4_8_membership.MAX_UNRESOLVED_CHANGE_FRACTION,
        "R3-2b": not inputs["failing_anchors"],
        "R3-2c": per_segment(inputs["unpriced_absent_fraction"], R3_2C_CAP),
        "R3-3": per_segment(inputs["unpriced_eligible_fraction"], R3_3_CAP),
        "R3-4": inputs["residual_count"] == 0,
        "R3-5": inputs["untradeable_fraction"] <= R3_5_CAP,
        "R3-6": all(m47.values()),
        "R3-7": inputs["total_ic_months"] >= MIN_TOTAL_IC_MONTHS,
        "R3-8": not inputs["vp2_revisit_required"],
        "R3-9": inputs["seal_carry_passed"],
        "R3-10": inputs["discrepancy_fraction"] <= R3_10_CAP,
    }
    failures = []
    for rule, code in READINESS_V3:
        if results[rule]:
            continue
        if rule != "R3-6":
            failures.append({"rule": rule, "result": code})
            continue
        for sub, passed in m47.items():
            if not passed:
                result = FAILURE_CODES[sub]
                if sub == "R-CENSUS-5" and inputs["calendar_covers_coverage_start"]:
                    result = "blocked:benchmark_gap"
                failures.append({"rule": f"R3-6/{sub}", "result": result})
    blocked = [f["result"] for f in failures if f["result"].startswith("blocked:")]
    caveats = list(dict.fromkeys(f["result"].split(":", 1)[1] for f in failures))
    status = blocked[0] if blocked else ("ready_with_caveats:" + ",".join(caveats) if failures else "ready")
    return {"status": status, "failures": failures, "rules": {rule: {"passed": bool(ok)} for rule, ok in results.items()},
            "r3_6_rules": {rule: {"passed": bool(ok)} for rule, ok in m47.items()}, "inputs": inputs}


_ABSOLUTE_PATH = re.compile(r"(?<![\w.])/(?:Users|private|home|tmp|var|Volumes|mnt)/")
_AGGREGATE_KEY = re.compile(r"^(?:[a-z][a-z0-9_]*(?::[a-z0-9_]+)*|-?\d+)$")


def known_codes(snapshot: Snapshot, private_paths: tuple[Path, ...] = ()) -> set[str]:
    """Vendor member codes, requested codes, and every curated supplement code the snapshot or a private directory holds."""
    codes = set(membership_codes(snapshot.read_file("membership"))) | set(snapshot.manifest.get("requested_codes", []))
    for directory in (snapshot.root / "membership", *private_paths):
        if (Path(directory) / m4_8_membership.SUPPLEMENT_FILE).is_file():
            supplement = m4_8_membership.read_curated(directory).supplement
            codes |= {str(code) for code in supplement["code"] if str(code).strip()}
    return codes


def public_leak_scan(text: str, snapshot: Snapshot, private_paths: tuple[Path, ...] = ()) -> list[str]:
    """T-PUB-1: the codes, names, and private paths a public payload holds (an empty list passes).

    ``<Code>.US`` forms always count; a bare code counts at three or more
    characters as a whole token; a vendor name counts at six or more characters.
    Codes include curated-only absent members; any absolute path under a user,
    private, temporary, or volume root counts as a path.
    """
    found = []
    for path in (snapshot.root, *private_paths):
        if str(path) in text:
            found.append(f"path:{path.name}")
    if _ABSOLUTE_PATH.search(text):
        found.append("path:absolute")
    membership = snapshot.read_file("membership")
    for code in sorted(known_codes(snapshot, private_paths)):
        bare = code.removesuffix(".US")
        if code in text or (len(bare) >= 3 and re.search(rf"(?<![A-Za-z0-9_]){re.escape(bare)}(?![A-Za-z0-9_])", text)):
            found.append("code")
    lowered = text.casefold()
    for name in {str(n) for n in membership["Name"] if isinstance(n, str) and len(n.strip()) >= 6}:
        if name.casefold() in lowered:
            found.append("name")
    return sorted(set(found))


def aggregate_terminal_summary(summary: dict[str, Any], codes: set[str]) -> dict[str, Any]:
    """The public projection of a terminal summary: aggregate counts only (R11, M48A-A1-M02).

    A field is a non-negative integer count or a flat map from a lowercase
    reason code (or an integer bucket such as a settlement lag) to such a count.
    Anything else refuses ``terminal_summary_not_aggregate`` before any public
    write: a list, a nested record, a string, a path, a permanent ID, or a key
    equal to a known code. The summary needs ``residual_count``.
    """
    lowered = {code.removesuffix(".US").casefold() for code in codes}

    def count(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0

    def key_ok(key: Any) -> bool:
        return (isinstance(key, str) and _AGGREGATE_KEY.match(key) is not None
                and not any(part in lowered for part in key.split(":")))

    public: dict[str, Any] = {}
    for key, value in summary.items():
        if key_ok(key) and count(value):
            public[key] = value
        elif key_ok(key) and isinstance(value, dict) and all(key_ok(k) and count(v) for k, v in value.items()):
            public[key] = dict(sorted(value.items()))
        else:
            raise SnapshotRefusal("terminal_summary_not_aggregate", "a field holds a value other than aggregate counts")
    if "residual_count" not in public:
        raise SnapshotRefusal("terminal_summary_incomplete", "residual_count")
    return dict(sorted(public.items()))


def _write_public(reports: Path, stem: str, public: dict[str, Any], markdown: str, snapshot: Snapshot,
                  private_paths: tuple[Path, ...]) -> str:
    body = canonical_json(public)
    leaks = public_leak_scan(body.decode("utf-8") + markdown, snapshot, private_paths)
    if leaks:
        raise SnapshotRefusal("public_output_leak", ", ".join(leaks))
    digest = write_bytes(reports / f"{stem}.json", body)
    write_bytes(reports / f"{stem}.md", markdown.encode("utf-8"))
    return digest


def _month_end_before(day: date) -> date:
    return day.replace(day=1) - timedelta(days=1)


def _member_rows(calendar: pd.DatetimeIndex, start: date, end: date | None) -> tuple[int, int]:
    """``[m_in, m_out)``: the calendar-row membership of an effective-date interval under the one-row signal lag."""
    m_in = int(calendar.searchsorted(pd.Timestamp(start))) + 1
    m_out = len(calendar) if end is None else int(calendar.searchsorted(pd.Timestamp(end))) + 1
    return m_in, m_out


def _rows_inside(interval: tuple[int, int], first: int, last: int) -> int:
    return max(0, min(interval[1], last + 1) - max(interval[0], first))


def membership_census(snapshot: Snapshot, curated: m4_8_membership.Curated) -> dict[str, Any]:
    """Plan 5.1 ``membership-census``: coverage, anchors, changes, supplement counts, and gate G1 (metadata only)."""
    calendar = snapshot.calendar()
    retrieved = snapshot.components_retrieved()
    holdout_start, holdout_end = snapshot.holdout_start, snapshot.holdout_end
    vendor = snapshot.read_file("membership")
    records = m4_8_membership.validate_supplement(curated.supplement, vendor, calendar)
    augmented = m4_8_membership.apply_supplement(vendor, records, retrieved)
    by_id = {r["supplement_id"]: r for r in records}
    entries, match_entries = [], []
    for classified, row in zip(holdout_partition.classify_membership_entries(augmented, retrieved),
                               augmented.to_dict(orient="records")):
        if classified["outcome"] != "retained":
            continue
        ref = str(row["raw_row"])
        record = by_id.get(ref)
        name = row.get("Name")
        entry = {"ref": ref, "kind": "supplement" if record else "vendor_entry", "code": f"{classified['code']}.US",
                 "start": classified["start"], "end": classified["end"], "name": name if isinstance(name, str) else ""}
        if record is not None:
            bar_dates = read_bar_dates(snapshot, entry["code"])
            bar_rows = np.array([] if bar_dates is None else calendar.get_indexer(bar_dates), dtype=int)
            m_in, m_out = _member_rows(calendar, entry["start"], entry["end"])
            record["priced"] = entry["priced"] = m4_8_membership.absent_member_priced(bar_rows[bar_rows >= 0], m_in - 1, m_out - 1)
        entries.append(entry)
        match_entries.append(entry)
    for record in records:
        if record["status"] == "valid" and record["action"] != "absent_member_add":
            match_entries.append({"ref": record["supplement_id"], "kind": "supplement", "code": record["code"],
                                  "start": record["start"], "end": record["end"]})
    changes = m4_8_membership.match_changes(curated.changes, match_entries, calendar)
    counts = m4_8_membership.month_end_counts([(e["code"], e["start"], e["end"]) for e in entries], calendar,
                                              m4_8_membership.COVERAGE_FLOOR, retrieved)
    last_anchor = _month_end_before(holdout_start)
    coverage = m4_8_membership.curated_coverage_start_v2(
        counts, m4_8_membership.published_anchors(curated.anchors), changes,
        reconstruction_end=holdout_start, last_anchor=last_anchor)
    for anchor in coverage["anchors"]:
        if anchor["kind"] == "anchor_floor_500" and anchor["as_of"] is not None:
            day = date.fromisoformat(anchor["as_of"])
            anchor["dual_class_lines"] = m4_8_membership.dual_class_lines(
                [e["name"] for e in entries if e["start"] <= day and (e["end"] is None or e["end"] > day)])
    pre, pre_ic_months, r3_2c = None, 0, {"unpriced_absent_member_days": 0, "eligible_member_days": 0, "fraction": None}
    if coverage["coverage_start_pre"] is not None:
        d0_pre = calendar[reset_in_month(calendar, date.fromisoformat(coverage["coverage_start_pre"]))].date()
        try:
            pre = discovery_segments(calendar, holdout_start, holdout_end, d0_pre)[0]
        except SnapshotRefusal:
            pre = None
    if pre is not None:
        pre_ic_months = int(len(segment_ic_resets(calendar, pre)))
        eligible = unpriced = 0
        for entry in entries:
            days = _rows_inside(_member_rows(calendar, entry["start"], entry["end"]), pre.first_reset_row, pre.last_book_row)
            eligible += days
            unpriced += days if entry.get("priced") is False else 0
        r3_2c = {"unpriced_absent_member_days": unpriced, "eligible_member_days": eligible,
                 "fraction": unpriced / eligible if eligible else None}
    conditions = {"coverage_start_pre_exists": coverage["coverage_start_pre"] is not None,
                  "pre_ic_months_at_least_34": pre_ic_months >= MIN_PRE_IC_MONTHS,
                  "r3_2c_pre_passes": r3_2c["fraction"] is not None and r3_2c["fraction"] <= R3_2C_CAP}
    g1 = ("passed" if all(conditions.values()) else coverage["status"] if not conditions["coverage_start_pre_exists"]
          else "blocked:insufficient_pre_segment" if not conditions["pre_ic_months_at_least_34"]
          else "blocked:unpriced_absent_members")
    post_first = discovery_window(calendar, holdout_end)[1]
    warm_up_end = calendar[min(post_first, len(calendar) - 1)].date()
    late = {"seal_window": 0, "post_holdout_warm_up": 0}
    for row in vendor.to_dict(orient="records"):
        end = parse_strict_date(row.get("EndDate"))
        if parse_strict_date(row.get("StartDate")) is None and end is not None and holdout_start <= end <= warm_up_end:
            late["seal_window" if end < holdout_end else "post_holdout_warm_up"] += 1
    discrepancies = m4_8_membership.discrepancy_rows(records)
    absent = [r for r in records if r["action"] == "absent_member_add"]
    match_counts: dict[str, int] = {}
    reasons: dict[str, int] = {}
    for change in changes:
        match_counts[change["match"]] = match_counts.get(change["match"], 0) + 1
        if change["match"] == "unresolved":
            reasons[change["reason"]] = reasons.get(change["reason"], 0) + 1
    public = {
        "schema_version": "m4_8_membership_census_v1",
        "evidence_ceiling": "DIAGNOSTIC_ONLY",
        "coverage_rule": m4_8_membership.COVERAGE_RULE,
        "coverage_status": coverage["status"],
        "coverage_start_pre": coverage["coverage_start_pre"],
        "D0_pre": None if pre is None else calendar[pre.first_reset_row].date().isoformat(),
        "r_pre_last": None if pre is None else calendar[pre.last_ic_reset_row].date().isoformat(),
        "pre_ic_months": pre_ic_months,
        "n_cur_by_month_end": [{"month_end": c["month_end"].isoformat(),
                                "as_of": None if c["as_of"] is None else c["as_of"].isoformat(), "n_cur": c["n_cur"]}
                               for c in counts],
        "anchors": coverage["anchors"],
        "failing_anchors": coverage["failing_anchors"],
        "unresolved_change_fraction": coverage["unresolved_change_fraction"],
        "reconstructed_changes": {"total": len(changes), "by_match": dict(sorted(match_counts.items())),
                                  "unresolved_by_reason": dict(sorted(reasons.items()))},
        "supplement_counts_by_action_and_status": m4_8_membership.supplement_counts(records),
        "absent_members": {
            "priced": sum(1 for r in absent if r["status"] == "valid" and r.get("priced")),
            "unpriced": sum(1 for r in absent if r["status"] == "valid" and r.get("priced") is False),
            "identity_refused": sum(1 for r in absent if r["status"] == "identity_refused"),
        },
        "corrections": {"confirmed": int((discrepancies["adjudication"] == "membership_date_corrected_primary_v1").sum()),
                        "unadjudicated_discrepancies": int((discrepancies["adjudication"] == "unadjudicated").sum())},
        "late_undated_entries": late,
        "r3_2c_pre": r3_2c,
        "gate_g1": {"status": g1, "conditions": conditions},
        "curated_file_sha256": curated.sha256,
    }
    detail = {
        "supplement": [{key: (value.isoformat() if isinstance(value, date) else value) for key, value in r.items()
                        if key != "discrepancies"} for r in records],
        "changes": [{**c, "effective_date": None if c["effective_date"] is None else c["effective_date"].isoformat()}
                    for c in changes],
    }
    return {"public": public, "detail": detail, "discrepancies": discrepancies, "changes": changes,
            "records": records, "entries": entries, "coverage": coverage}


def run_membership_census(
    snapshot_dir: Path | str,
    curated_dir: Path | str,
    *,
    reports_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Write the private detail and discrepancy file beside the curation files and the public counts."""
    snapshot = Snapshot.open(snapshot_dir)
    curated_dir = Path(curated_dir)
    result = membership_census(snapshot, m4_8_membership.read_curated(curated_dir))
    write_bytes(curated_dir / MEMBERSHIP_DETAIL, canonical_json(result["detail"]))
    write_bytes(curated_dir / m4_8_membership.DISCREPANCIES_FILE,
                result["discrepancies"].to_csv(index=False, lineterminator="\n").encode("utf-8"))
    reports = Path(reports_dir) if reports_dir is not None else REPOSITORY_ROOT / "reports"
    public = result["public"]
    markdown = "\n".join([
        "# M4.8 Membership Census", "",
        "Evidence ceiling: `DIAGNOSTIC_ONLY`. Membership metadata and curated files only; no price value was read.", "",
        f"- Coverage rule: `{public['coverage_rule']}`; status `{public['coverage_status']}`",
        f"- coverage_start_pre: `{public['coverage_start_pre']}`; D0_pre: `{public['D0_pre']}`; "
        f"pre IC months: {public['pre_ic_months']}",
        f"- Unresolved change fraction: {public['unresolved_change_fraction']}",
        f"- Gate G1: `{public['gate_g1']['status']}`",
        f"- Failing anchors: {len(public['failing_anchors'])}", ""])
    result["public_sha256"] = _write_public(reports, MEMBERSHIP_REPORT, public, markdown, snapshot, (curated_dir,))
    return result


def potentially_held(s_mask: np.ndarray, bars: np.ndarray, resets: list[int]) -> dict[int, np.ndarray]:
    """Plan 4.6 ``P_r = S_mask(r - 1) ∪ {a in P_prev(r) : no close at r}``; ``P_prev`` is empty at the first reset."""
    held: dict[int, np.ndarray] = {}
    previous = np.zeros(bars.shape[1], dtype=bool)
    for r in resets:
        previous = s_mask[r - 1] | (previous & ~bars[r])
        held[r] = previous
    return held


def halt_counts(held: dict[int, np.ndarray], bars: np.ndarray, horizons: dict[int, int]) -> dict[str, int]:
    """Plan 5.2 halts from bar presence: untradeable execution cells and unmarked rows inside a bar run."""
    has_before = np.maximum.accumulate(bars, axis=0)
    has_after = np.maximum.accumulate(bars[::-1], axis=0)[::-1]
    inside_run = ~bars & np.vstack([np.zeros((1, bars.shape[1]), bool), has_before[:-1]]) & \
        np.vstack([has_after[1:], np.zeros((1, bars.shape[1]), bool)])
    untradeable = cells = unmarked = 0
    for r, assets in held.items():
        cells += int(assets.sum())
        untradeable += int((assets & ~bars[r]).sum())
        h = horizons[r]
        unmarked += int((inside_run[r + 1:h + 1] & assets[None, :]).sum())
    return {"potentially_held_cells": cells, "untradeable_execution_cells": untradeable, "unmarked_halt_rows": unmarked}


def seal_carry_check(snapshot: Snapshot, build: dict[str, Any], segment_access_logs: dict[str, list[str]] | None,
                     repository_root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    """R3-9: the carried window equals the seal v1 byte-derived window, the bound hashes verify, and no read crossed."""
    record = holdout_partition.read_seal_carry(snapshot.root)
    try:
        rebuilt = holdout_partition.build_seal_carry_record(
            (repository_root / holdout_partition.SEAL_V1_DOCS_PATH).read_bytes(),
            (repository_root / holdout_partition.SEAL_V1_CONFIRMATION_V2_PATH).read_bytes(),
            written_at=record["written_at"], writing_actor=record["writing_actor"],
            authorization_reference=record["authorization_reference"])
        hashes = True
    except SnapshotRefusal:
        rebuilt, hashes = {}, False
    sides = {"pre": "discovery_pre", "post": "discovery_post"}
    checks = {
        "window_equals_seal_v1_bytes": hashes and all(record[key] == rebuilt[key] for key in
                                                      ("holdout_start", "holdout_end_exclusive", "calendar_source")),
        "carried_from_hashes_verify": hashes,
        "no_holdout_partition_open": build.get("access_log", {}).get("holdout_partition_opens", 1) == 0,
        "segment_logs_open_own_side_only": segment_access_logs is not None and set(segment_access_logs) == set(sides)
        and all(set(opened) <= {sides[segment]} for segment, opened in segment_access_logs.items()),
    }
    return {"passed": all(checks.values()), "checks": checks}


def _side_panels(root: Path, inventory: dict[str, Any]) -> dict[tuple[str, str], pd.DataFrame]:
    panels = {}
    for record in inventory["files"]:
        payload = (root / "panel" / record["file"]).read_bytes()
        if sha256_bytes(payload) != record["sha256"]:
            raise SnapshotRefusal("derived_artifact_stale", f"panel {record['file']}")
        frame = _parquet(payload, record["file"])
        panels[(record["side"], record["symbol"])] = frame.assign(date=pd.DatetimeIndex(frame["date"])).set_index("date")
    return panels


def _segment_metrics(
    segment: Segment, calendar: pd.DatetimeIndex, mask: pd.DataFrame, panels: dict[tuple[str, str], pd.DataFrame],
    intervals: pd.DataFrame, build: dict[str, Any], membership: dict[str, Any], support: pd.DataFrame,
) -> dict[str, Any]:
    """Plan 5.2 per segment: member-days by cause (R3-2c, R3-3 with M-8), volume basis, IC supply, exposure, halts,
    VP-1 (the volume half diagnostic on the segment's side panels), and VP-2."""
    first, last, side = segment.first_reset_row, segment.last_book_row, segment.side
    rows = np.arange(first, last + 1)
    unpriced_absent_refs = {r["supplement_id"] for r in membership["records"] if r.get("priced") is False}
    reasons: dict[str, int] = {}
    member_days = identity_days = absent_unpriced = 0
    bars = np.zeros((len(calendar), len(mask.columns)), dtype=bool)
    volume_days: dict[str, int] = {}
    volume_basis = build.get("pre_side_volume_basis_by_code", {})
    for column, pid in enumerate(mask.columns):
        panel = panels.get((side, pid))
        if panel is not None:
            bars[calendar.get_indexer(panel.index[np.isfinite(panel["adjusted_close"])]), column] = True
        eligible = mask[pid].to_numpy()[rows]
        member_days += int(eligible.sum())
        missing = eligible & ~bars[rows, column]
        if missing.any():
            key = "no_side_panel" if panel is None else "missing_bar_on_side"
            reasons[key] = reasons.get(key, 0) + int(missing.sum())
        status = volume_basis.get(pid.split("#", 1)[0], "")
        if side == "discovery_pre" and status.startswith("volume_basis_unverified:"):
            volume_days[status] = volume_days.get(status, 0) + int(eligible.sum())
    refused = 0
    overlap_rows: dict[str, set[int]] = {}
    for row in intervals.to_dict(orient="records"):
        resolution = row["resolution"]
        if resolution in ("resolved", "exact_duplicate_collapsed", "degenerate_interval"):
            continue
        if resolution in ("entry_missing_field", "entry_unparseable_date"):
            # M-4: an entry left undated keeps the M4.7 worst-case charge over the whole segment.
            reasons["entry_unusable_upper_bound"] = reasons.get("entry_unusable_upper_bound", 0) + len(rows)
            refused += len(rows)
            continue
        if not row["m_in"]:
            continue
        m_in = int(calendar.get_loc(pd.Timestamp(row["m_in"])))
        m_out = len(calendar) if not row["m_out"] else int(calendar.get_loc(pd.Timestamp(row["m_out"])))
        if resolution == "raw_overlap":
            overlap_rows.setdefault(row["vendor_code"], set()).update(range(max(m_in, first), min(m_out, last + 1)))
            continue
        days = _rows_inside((m_in, m_out), first, last)
        if row["census_cap"] == "R-CENSUS-3":
            identity_days += days
            continue
        reasons[resolution] = reasons.get(resolution, 0) + days
        refused += days
        if str(row["raw_row"]) in unpriced_absent_refs:
            absent_unpriced += days
    overlap = sum(len(cells) for cells in overlap_rows.values())
    if overlap:
        reasons["raw_overlap"] = overlap
        refused += overlap
    for record in membership["records"]:
        if record["status"] == "identity_refused":
            # M-5: a refused absent member stays out of the universe and its member-days are charged to R3-3.
            days = _rows_inside(_member_rows(calendar, record["start"], record["end"]), first, last)
            reasons["absent_member_identity_refused"] = reasons.get("absent_member_identity_refused", 0) + days
            refused += days
    coverage_start = membership["coverage"]["coverage_start_pre"]
    coverage_row = int(calendar.searchsorted(pd.Timestamp(coverage_start))) if coverage_start else first
    m8 = m4_8_membership.m8_charges(membership["changes"], calendar, first, last, coverage_row)
    if m8:
        reasons["m8_unresolved_change_charge"] = m8
    eligible_total = member_days + refused
    unpriced_total = sum(reasons.values())
    resets = segment_ic_resets(calendar, segment)
    all_resets = scheduled_reset_rows(calendar)
    horizons = {int(r): int(all_resets[np.searchsorted(all_resets, r) + 1]) for r in resets}
    s_mask = (mask.shift(-1, fill_value=False).to_numpy(dtype=bool) & bars)
    halts = halt_counts(potentially_held(s_mask, bars, [int(r) for r in resets]), bars, horizons)
    reset_dates = [calendar[r].date() for r in resets]
    side_panels = {pid: frame for (panel_side, pid), frame in panels.items() if panel_side == side}
    volume_premise = volume_basis_diagnostic(
        _volume_ells(side_panels, [check for check in build["episode_checks"] if check.get("side") == side]))
    own = support[(support["date"] >= calendar[first]) & (support["date"] <= calendar[last])]
    s_d_days = 0
    for column, pid in enumerate(mask.columns):
        eligible_dates = calendar[rows][mask[pid].to_numpy()[rows] & bars[rows, column]]
        values = own[own["permanent_id"] == pid].set_index("date")["s_d"].reindex(eligible_dates).fillna(0.0)
        s_d_days += int((values > VP2_LEVEL).sum())
    return {
        "segment_id": segment.segment_id,
        "ic_months": int(len(resets)),
        "eligible_member_days": eligible_total,
        "eligible_unpriced_member_days": dict(sorted(reasons.items())),
        "eligible_unpriced_member_days_total": unpriced_total,
        "unpriced_eligible_fraction": unpriced_total / eligible_total if eligible_total else None,
        "unpriced_absent_member_days": absent_unpriced,
        "unpriced_absent_fraction": absent_unpriced / eligible_total if eligible_total else None,
        "identity_refused_member_days": identity_days,
        "m8_unresolved_change_charge": m8,
        "volume_basis_unverified": {"codes": sum(1 for s in volume_basis.values() if s.startswith("volume_basis_unverified:"))
                                    if side == "discovery_pre" else 0,
                                    "eligible_member_days": sum(volume_days.values())},
        "volume_basis_unverified_by_reason": dict(sorted(volume_days.items())),
        "halts": halts,
        "prior_exposure_overlap": prior_exposure_overlap(reset_dates),
        "calendar_unexposed_ic_months": sum(1 for r in resets if calendar[horizons[int(r)]].date() < UNEXPOSED_BEFORE),
        "member_days_s_d_above_0_05": s_d_days,
        "vp2_revisit_required": bool(eligible_total and s_d_days > VP2_SHARE * eligible_total),
        "volume_basis_split_diagnostic": volume_premise,
    }


def run_census_v3(
    snapshot_dir: Path | str,
    *,
    terminal_summary: dict[str, Any],
    segment_access_logs: dict[str, list[str]] | None,
    reports_dir: Path | str | None = None,
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, Any]:
    """Plan 5.1-5.3 census v3 on a rule v2 snapshot; returns the public JSON, the detail, and the digest.

    ``terminal_summary`` carries the terminal and residual counts from the
    two-pass validation (Stage E), at least ``residual_count``; only its
    aggregate projection (``aggregate_terminal_summary``) reaches the public JSON;
    ``segment_access_logs`` maps ``pre`` and ``post`` to the sides each
    segment's run opened (Stage H runner logs).
    """
    snapshot = Snapshot.open(snapshot_dir)
    if snapshot.partition_rule != holdout_partition.PARTITION_RULE_V2:
        raise SnapshotRefusal("census_v3_requires_rule_v2", snapshot.partition_rule)
    terminal = aggregate_terminal_summary(terminal_summary, known_codes(snapshot))
    root = snapshot.root
    build = read_derived_json(root, BUILD_MANIFEST)
    require_current(snapshot, build.get("discovery_inputs_sha256"), BUILD_MANIFEST)
    inventory = read_derived_json(root, INVENTORY)
    require_current(snapshot, inventory.get("discovery_inputs_sha256"), INVENTORY)
    calendar = snapshot.calendar()
    segments = discovery_segments(calendar, snapshot.holdout_start, snapshot.holdout_end, date.fromisoformat(build["d0_pre"]))
    membership = membership_census(snapshot, m4_8_membership.read_curated(root / "membership"))
    table = load_constituent_intervals_csv(root / INTERVAL_CSV).data
    pids = sorted(set(table["permanent_id"]))
    mask = resolve_pit_universe_mask(table, None, calendar, pids) if pids else pd.DataFrame(index=calendar)
    intervals = _read_csv(root / INTERVAL_RESULTS)
    panels = _side_panels(root, inventory)
    support = pd.read_parquet(root / DISTRIBUTION_SUPPORT)
    support = support.assign(date=pd.DatetimeIndex(support["date"]))
    per_segment = {s.segment_id: _segment_metrics(s, calendar, mask, panels, intervals, build, membership, support)
                   for s in segments}
    seal = seal_carry_check(snapshot, build, segment_access_logs, repository_root)
    verify = snapshot.manifest.get("verify") or {}
    member_codes = membership_codes(snapshot.read_file("membership"))
    off_calendar = sum(count for code, count in build["off_calendar_bar_rows"].items() if code in member_codes)
    member_days_all = sum(m["eligible_member_days"] + m["identity_refused_member_days"] for m in per_segment.values())
    spy = {s.side: panels.get((s.side, f"{BENCHMARK}#E1")) for s in segments}
    benchmark_complete = all(
        spy[s.side] is not None and calendar[s.anchor_row:s.last_book_row + 1].isin(
            spy[s.side].index[np.isfinite(spy[s.side]["adjusted_close"])]).all() for s in segments)
    holdout_counts = [c["n_cur"] for c in membership["public"]["n_cur_by_month_end"]
                      if snapshot.holdout_start.isoformat() <= c["month_end"] < snapshot.holdout_end.isoformat()]
    dated_pre = sum(1 for e in membership["entries"] if e["kind"] == "vendor_entry" and _rows_inside(
        _member_rows(calendar, e["start"], e["end"]), segments[0].first_reset_row, segments[0].last_book_row))
    halts_cells = sum(m["halts"]["potentially_held_cells"] for m in per_segment.values())
    inputs = {
        "pre_ic_months": per_segment["pre"]["ic_months"],
        "unresolved_change_fraction": membership["public"]["unresolved_change_fraction"],
        "failing_anchors": membership["public"]["failing_anchors"],
        "unpriced_absent_fraction": {k: m["unpriced_absent_fraction"] for k, m in per_segment.items()},
        "unpriced_eligible_fraction": {k: m["unpriced_eligible_fraction"] for k, m in per_segment.items()},
        "residual_count": terminal["residual_count"],
        "untradeable_fraction": (sum(m["halts"]["untradeable_execution_cells"] for m in per_segment.values()) / halts_cells
                                 if halts_cells else 0.0),
        "identity_refusal_fraction": (sum(m["identity_refused_member_days"] for m in per_segment.values()) / member_days_all
                                      if member_days_all else 0.0),
        "off_calendar_fraction": off_calendar / member_days_all if member_days_all else 0.0,
        "calendar_covers_coverage_start": membership["public"]["coverage_start_pre"] is not None
        and calendar[0].date().isoformat() <= membership["public"]["coverage_start_pre"],
        "benchmark_complete": bool(benchmark_complete),
        "snapshot_integrity": bool(verify) and not verify.get("token_leak_detected", ["unverified"])
        and not verify.get("artifact_hash_mismatch", ["unverified"]) and not verify.get("split_evidence_stale", ["unverified"])
        and all(status == "valid" or (status.startswith("quarantined:") and len(status) > len("quarantined:"))
                for entry in snapshot.manifest.get("entries", {}).values()
                for status in entry.get("partition_statuses", {}).values()),
        "holdout_band_after_identity": bool(holdout_counts) and tolerant_band(holdout_counts),
        "retrieval_complete": bool(verify.get("retrieval_complete", False)),
        "total_ic_months": sum(m["ic_months"] for m in per_segment.values()),
        "vp2_revisit_required": any(m["vp2_revisit_required"] for m in per_segment.values()),
        "seal_carry_passed": seal["passed"],
        "discrepancy_fraction": (membership["public"]["corrections"]["unadjudicated_discrepancies"] / dated_pre
                                 if dated_pre else 0.0),
    }
    readiness = derive_readiness_v3(inputs)
    public_segments = {k: {key: value for key, value in m.items() if key != "volume_basis_unverified_by_reason"}
                       for k, m in per_segment.items()}
    public = {
        "schema_version": "m4_8_coverage_census_v3",
        "evidence_ceiling": "DIAGNOSTIC_ONLY",
        "formal_universe_evidence_eligible": False,
        "snapshot_id": snapshot.manifest["snapshot"].get("id"),
        "partition_rule": snapshot.partition_rule,
        "seal": {"rule_version": holdout_partition.SEAL_CARRY_RULE, "holdout_start": snapshot.holdout_start.isoformat(),
                 "holdout_end_exclusive": snapshot.holdout_end.isoformat(), "carry_check": seal,
                 "description": "carried seal with stated prior exposures"},
        "segments": build["segments"],
        "membership": {key: membership["public"][key] for key in (
            "coverage_status", "coverage_start_pre", "D0_pre", "pre_ic_months", "anchors", "unresolved_change_fraction",
            "reconstructed_changes", "supplement_counts_by_action_and_status", "absent_members", "corrections",
            "late_undated_entries", "gate_g1", "curated_file_sha256")},
        "identity": {"seal_gap_identity_split": build.get("seal_gap_identity_split", 0),
                     "segment_anchor_checks": build.get("segment_anchor_checks", 0),
                     "pre_side_split_rows_after_anchor": build.get("pre_side_split_rows_after_anchor", 0),
                     "interval_resolution_counts": build["interval_resolution_counts"],
                     "episode_panel_refusal_counts": build["episode_panel_refusal_counts"]},
        "per_segment": public_segments,
        "terminal_evidence": terminal,
        "ic_supply": {"total_ic_months": inputs["total_ic_months"],
                      **{f"{k}_ic_months": m["ic_months"] for k, m in per_segment.items()}},
        "power_projection": power_projection(inputs["total_ic_months"]),
        "census_readiness": readiness,
        "snapshot_identity": {"manifest_sha256": sha256_bytes((root / "manifest.json").read_bytes()),
                              "discovery_inputs_sha256": build["discovery_inputs_sha256"],
                              "seal_carry_sha256": sha256_bytes((root / holdout_partition.SEAL_CARRY_FILE).read_bytes()),
                              "interval_csv_sha256": sha256_bytes((root / INTERVAL_CSV).read_bytes())},
    }
    detail = {"discovery_inputs_sha256": build["discovery_inputs_sha256"],
              "volume_basis_unverified_by_reason": {k: m["volume_basis_unverified_by_reason"] for k, m in per_segment.items()},
              "membership": membership["detail"]}
    write_bytes(root / CENSUS_V3_DETAIL, canonical_json(detail))
    reports = Path(reports_dir) if reports_dir is not None else REPOSITORY_ROOT / "reports"
    markdown = "\n".join([
        "# M4.8 Coverage Census v3", "",
        "Evidence ceiling: `DIAGNOSTIC_ONLY`. No figure below supports a ranking, selection, promotion, or "
        "profitability claim. The holdout is a carried seal with stated prior exposures.", "",
        f"- Readiness: `{readiness['status']}`" + (
            f" ({', '.join(f['rule'] + ' ' + f['result'] for f in readiness['failures'])})" if readiness["failures"] else ""),
        *[f"- Segment `{s['segment_id']}`: first reset {s['first_reset_row']}, last IC reset {s['last_ic_reset_row']}, "
          f"last book row {s['last_book_row']}, IC months {s['ic_months']}" for s in build["segments"]],
        f"- Total IC months: {inputs['total_ic_months']}",
        *[f"- VP-1 volume half `{k}`: `{m['volume_basis_split_diagnostic']['a1_volume_half']}` over "
          f"{m['volume_basis_split_diagnostic']['rows']} split rows" for k, m in per_segment.items()],
        "", "| Rule | Passed |", "| --- | --- |",
        *[f"| {rule} | {value['passed']} |" for rule, value in readiness["rules"].items()], ""])
    digest = _write_public(reports, CENSUS_V3_REPORT, public, markdown, snapshot, ())
    return {"public": public, "detail": detail, "census_json_sha256": digest}


# ---------------------------------------------------------------- report


def render_markdown(public: dict[str, Any]) -> str:
    readiness = public["census_readiness"]
    identity = public["snapshot_identity"]
    support = public["in_span_distribution_support"]
    volume = public["volume_basis_split_diagnostic"]
    coverage = public["price_coverage"]
    exclusion = public["asset_support"]
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
        f"- Seal rule: `{readiness['thresholds']['seal_rule_version']}` (minimum in-band years "
        f"{readiness['thresholds']['min_in_band_years']}, latest holdout end "
        f"{readiness['thresholds']['latest_holdout_end']}, minimum IC months {readiness['thresholds']['min_ic_months']})",
        f"- Owner-accepted shortfall bounds: {readiness['thresholds']['accepted_shortfall']}",
        f"- Calendar source: `{public['calendar']['calendar_source']}`",
        f"- Readiness: `{readiness['status']}`" + (
            f" ({', '.join(f['rule'] + ' ' + f['result'] for f in readiness['failures'])})" if readiness["failures"] else ""),
        f"- manifest_sha256: `{identity['manifest_sha256']}`",
        f"- discovery_inputs_sha256: `{identity['discovery_inputs_sha256']}`",
        f"- support_sha256: `{identity['support_sha256']}` (`{exclusion['support_contract']}`)",
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
        f"| Unresolved events in the window | {exclusion['unresolved_events']} |",
        f"| Support-excluded cells | {exclusion['excluded_cells']} of {exclusion['signal_eligible_cells']} |",
        f"| Support-excluded fraction | {exclusion['excluded_fraction']:.6f} |",
        f"| Evaluated breadth (min, median, max) | {exclusion['evaluated_breadth']['min']}, "
        f"{exclusion['evaluated_breadth']['median']:g}, {exclusion['evaluated_breadth']['max']} |",
        f"| IC month supply | {public['ic_supply']['ic_month_supply']} |",
        f"| Kill reachable (projection) | {public['power_projection']['kill_reachable_projection']} |",
        "",
        "## Asset-level support exclusions",
        "",
        "A missing bar or an unevidenced disappearance excludes only the affected asset from the reset whose holding "
        "period needs that bar. Each exclusion conditions on that asset's own bar availability over one holding period.",
        "",
        f"- Excluded cells by reason: {exclusion['excluded_cells_by_reason']}",
        "",
        "| Reset | Signal-eligible | Support-excluded | Evaluated |",
        "| --- | --- | --- | --- |",
        *[f"| {row['reset_date']} | {row['signal_eligible']} | {row['support_excluded']} | {row['evaluated']} |"
          for row in exclusion["breadth_by_reset"]],
        "",
        "## Holdout integrity (metadata)",
        "",
        *[f"- {key}: {value}" for key, value in public["corporate_actions"]["corporate_action_partitions_quarantined"].items()
          if "holdout" in key],
        "",
    ]
    return "\n".join(lines)


def _m48_main(argv: list[str]) -> int:
    """``membership-census`` and ``census-v3`` subcommands (plan 5.1)."""
    parser = argparse.ArgumentParser(prog="python -m research.m4_7_coverage_census")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("membership-census", "census-v3"):
        sub = commands.add_parser(name)
        sub.add_argument("--snapshot-id", required=True)
        sub.add_argument("--data-dir", default=None)
        sub.add_argument("--reports-dir", default=None)
        if name == "membership-census":
            sub.add_argument("--curated-dir", required=True, help="private directory holding the three curation files")
        else:
            sub.add_argument("--terminal-summary", required=True, help="JSON counts from the two-pass terminal validation")
            sub.add_argument("--segment-access-log", default=None, help="JSON {segment_id: [sides opened]}")
    args = parser.parse_args(argv)
    try:
        if args.command == "membership-census":
            result = run_membership_census(snapshot_dir_from_args(args), args.curated_dir, reports_dir=args.reports_dir)
            summary = {"gate_g1": result["public"]["gate_g1"]["status"], "D0_pre": result["public"]["D0_pre"],
                       "public_sha256": result["public_sha256"]}
        else:
            logs = None if args.segment_access_log is None else json.loads(Path(args.segment_access_log).read_bytes())
            result = run_census_v3(snapshot_dir_from_args(args),
                                   terminal_summary=json.loads(Path(args.terminal_summary).read_bytes()),
                                   segment_access_logs=logs, reports_dir=args.reports_dir)
            summary = {"census_readiness": result["public"]["census_readiness"]["status"],
                       "census_json_sha256": result["census_json_sha256"]}
    except SnapshotRefusal as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ("membership-census", "census-v3"):
        return _m48_main(argv)
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
