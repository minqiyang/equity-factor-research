"""Milestone 5 step 4b: do three SEC as-filed sleeves join the price classes on point-in-time books?

Run with ``PYTHONPATH=src .venv/bin/python -m research.m5_step4b --snapshot-dir <dir> --reason "<why>"``.
The command implements ``docs/preregistrations/m5_trial_family_v1_amendment_5.json`` revision 2 on top of
v1 and amendments 1 to 4. It refuses unless the six trial files equal HEAD and their pins, the public cache
matches the committed public manifest, the ``real_v2`` snapshot matches its pins, and the SEC data (the local
CIK map, the cache's retrieval records, and the three data-build code files) matches the amendment's pins.

Chain: the step 4 chain, recomputed (R0_6, its metrics checked against ``reports/m5_step4.json``); three SEC
sleeves BM_AF, EP_AF, GP_AT_AF on the same engine call, from the as-filed rule of ``research.m5_sec_signals``
at signal row r - 1; the candidate R0_9 over nine sleeves; the S4b.ADD test in a BY family of 481; the
last-close rerun; and R0_6_mapped, the price sleeves on the 563 uniquely mapped IDs (coverage tilt).

The SEC cache is read offline only (no request, every opened file matches its retrieval record). Per-company
values stay in memory. Outputs: ``reports/m5_step4b.md``, ``reports/m5_step4b.json`` (aggregates only, R11),
and a start and an end record per attempt in ``reports/m5_step4b_attempts.jsonl``. Evidence ceiling
``DIAGNOSTIC_ONLY``.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import io
import json
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from data.sec_edgar import SecClient, SecFile, SecRefusal
from features.multiple_testing import adjust_pvalues
from research import m5_factor_baseline as base
from research import m5_sec_identity as ident
from research import m5_sec_signals as sig
from research import m5_step3 as step3
from research import m5_step4 as s4
from research import m5_step4b_data as dm
from research import m4_7_sp500_pit_rerun as runner
from research.m4_7_family_a import FAMILY_A_IDS
from research.m4_7_universe_build import INTERVAL_RESULTS, SECURITY_MASTER


REPO_ROOT = base.REPO_ROOT
AMENDMENT_5_PATH = "docs/preregistrations/m5_trial_family_v1_amendment_5.json"
AMENDMENT_5_SHA256 = "a712188c877621af675e9986ae5c3da834fb66ad5adf90480c5d475555b0c75c"
TRIAL_PINS = {**s4.TRIAL_PINS, AMENDMENT_5_PATH: AMENDMENT_5_SHA256}
REPORT_MD = "reports/m5_step4b.md"
REPORT_JSON = "reports/m5_step4b.json"
ATTEMPTS_JSONL = "reports/m5_step4b_attempts.jsonl"
STEP4_JSON = s4.REPORT_JSON

SEC_PINS = {"cik_map_sha256": "09d163b91d386064553935d0648424fa1bd1d1469fec2404a440c65c3fed120a",
            "file_hash_list_sha256": "3c73ffe2210bd87147ecc79e1963ef08a86843a937b06fe62ede372e27c6698a"}
BUILD_CODE = {"research/m5_sec_identity.py": "98c7cb9390cfff24ae8aa141c6a3922ddf0e5be4090162300fe8039a4a858641",
              "src/data/sec_edgar.py": "a077eee5e82fd985efabe5acbed7bf0437dcbb0494ba98e33e367e97dc931472",
              "research/m5_step4b_data.py": "81c4dfacc78cb6b182cfac3898adec22bb7cfd5b8190bb854e2b94860e2b0fd7"}
SIDECAR = ".retrieval.json"

SEC_SLEEVES = {sig.BM: ("be_me", "Value"), sig.EP: ("ni_me", "Value"), sig.GP_AT: ("gp_at", "Quality")}
SEC_IDS = tuple(SEC_SLEEVES)
SEC_THEMES = ("Value", "Quality")
ALL_SLEEVES = {**s4.SLEEVES, **SEC_SLEEVES}
ALL_IDS = (*FAMILY_A_IDS, *SEC_IDS)
PUBLIC_THEMES = (*s4.THEMES, *SEC_THEMES)
BOOKS = ("R0_9", "R0_6", "R0_6_mapped", "R1_9")
OBSERVED_TESTS = 1
FAMILY_SIZE = 481
TEST_ID = "S4b.ADD"
COMPARISON_MONTHS = {"pre": ("2014-12", "2019-06", 55), "post": ("2022-05", "2025-12", 44)}
IDENTITY_REASON = {ident.UNMAPPED: "identity_unmapped", ident.AMBIGUOUS: "identity_ambiguous",
                   ident.MULTI_CLASS: "identity_multi_class"}
STATUSES = (sig.RANKED, *sig.REASON_ORDER)
EXIT_CLASSES = (*s4.EXIT_CLASSES, s4.UNKNOWN)
LOCKED_HOLDINGS = ("A not_ranked_at_rebalance member-day means the member cannot be newly selected at that "
                   "rebalance. The engine's halt_gap_return_v1 accounting is unchanged: a previously held "
                   "position locked by a missing execution price stays held, so status counts and holdings are "
                   "distinct (coordinator ruling on GPT-S4BF-R2-A1 and OPUS-S4BF-R2-A3).")


def refuse(reason: str, detail: str = "") -> runner.RunnerStop:
    return runner.RunnerStop(reason, detail)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# SEC inputs --------------------------------------------------------------------------------

@dataclass
class SecInputs:
    """The pinned CIK map (one row per eligible permanent ID) and the parsed facts of each unique CIK."""

    identity: pd.DataFrame
    facts: dict[int, sig.CompanyFacts | None]     # None: a recorded 404
    requests: int = 0

    def status_of(self) -> dict[str, tuple[str, int | None]]:
        return {r["permanent_id"]: (r["status"], int(r["cik"]) if r["cik"] else None)
                for r in self.identity.to_dict(orient="records")}


def _no_network(*_args: Any, **_kwargs: Any) -> Any:
    raise refuse("sec_pin_mismatch", "a network request was attempted")


def verify_build_code(repo_root: Path, code: Mapping[str, str] = BUILD_CODE) -> None:
    for relative, pinned in code.items():
        path = repo_root / relative
        if not path.is_file() or _sha(path.read_bytes()) != pinned:
            raise refuse("sec_pin_mismatch", f"data-build code {relative}")


def cache_files(client: SecClient) -> dict[str, SecFile]:
    """Every cached file with its retrieval record, each checked against that record (offline)."""

    files = {}
    for sidecar in sorted(client.cache_dir.rglob("*" + SIDECAR)):
        relative = sidecar.relative_to(client.cache_dir).as_posix()[:-len(SIDECAR)]
        record = json.loads(sidecar.read_text(encoding="utf-8"))
        files[relative] = client.get(record["url"], relative, allow_absent=True)
    return files


def load_sec(repo_root: Path, snapshot_dir: Path, pins: Mapping[str, str] = SEC_PINS,
             code: Mapping[str, str] = BUILD_CODE, opener: Any = _no_network) -> SecInputs:
    """Verify every SEC pin, then parse the companyfacts of each unique CIK; any mismatch is ``sec_pin_mismatch``."""

    verify_build_code(repo_root, code)
    manifest = json.loads((repo_root / dm.MANIFEST_JSON).read_text(encoding="utf-8"))
    if (manifest["cik_map"]["sha256"], manifest["file_hash_list"]["sha256"]) != (
            pins["cik_map_sha256"], pins["file_hash_list_sha256"]):
        raise refuse("sec_pin_mismatch", "manifest")
    private = dm.private_dir_for(snapshot_dir, repo_root)
    map_bytes = (private / dm.MAP_FILE).read_bytes()
    if _sha(map_bytes) != pins["cik_map_sha256"]:
        raise refuse("sec_pin_mismatch", "cik map")
    if _sha((private / dm.HASH_LIST_FILE).read_bytes()) != pins["file_hash_list_sha256"]:
        raise refuse("sec_pin_mismatch", "local hash list")
    client = SecClient(repo_root / dm.CACHE_DIR, offline=True, opener=opener)
    try:
        files = cache_files(client)
    except SecRefusal as exc:
        raise refuse("sec_pin_mismatch", "cached file") from exc
    if _sha(dm.hash_list_bytes(files.values())) != pins["file_hash_list_sha256"]:
        raise refuse("sec_pin_mismatch", "hash list rebuilt from the cache")
    identity = pd.read_csv(io.BytesIO(map_bytes), dtype=str, keep_default_na=False)
    if list(identity.columns) != dm.MAP_COLUMNS or identity["permanent_id"].duplicated().any():
        raise refuse("sec_pin_mismatch", "cik map layout")
    facts: dict[int, sig.CompanyFacts | None] = {}
    for cik in sorted({int(c) for c in identity.loc[identity["status"] == ident.UNIQUE, "cik"]}):
        record = files.get(f"companyfacts/CIK{cik:010d}.json")
        if record is None:
            raise refuse("sec_pin_mismatch", "companyfacts without a retrieval record")
        if record.status == 404:
            facts[cik] = None
            continue
        payload = record.read_bytes(client.cache_dir)
        if _sha(payload) != record.sha256:
            raise refuse("sec_pin_mismatch", "companyfacts changed after verification")
        facts[cik] = sig.parse_companyfacts(json.loads(payload))
    if client.requests:
        raise refuse("sec_pin_mismatch", "a network request was made")
    return SecInputs(identity=identity, facts=facts, requests=client.requests)


def check_identity_pool(segments: Mapping[str, s4.SegmentInputs], sec: SecInputs) -> None:
    """Every asset ever in a segment's evaluation mask has a row in the pinned map."""

    known = set(sec.identity["permanent_id"])
    for sid, seg in segments.items():
        mask = seg.schedule.evaluation_mask
        used = set(mask.columns[mask.to_numpy(dtype=bool).any(axis=0)])
        missing = used - known
        if missing:
            raise refuse("sec_identity_pool_mismatch", f"{sid}: {len(missing)} assets")


# SEC signals and member-day statuses --------------------------------------------------------

@dataclass
class SecPanels:
    """One segment's SEC signal panels (values at signal rows r - 1 only) and its rebalance statuses."""

    signals: dict[str, pd.DataFrame]
    statuses: dict[str, dict[int, np.ndarray]]     # signal -> reset row r -> status per column (None: not in set)
    preferred_zero: dict[int, np.ndarray]          # reset row r -> BM_AF ranked with preferred 0 by absence


def sec_panels(seg: s4.SegmentInputs, sec: SecInputs) -> SecPanels:
    """The as-filed signals of each ranking set: the evaluation mask at row r - 1 of every scheduled rebalance r."""

    if seg.split_close is None or seg.split_factor is None or not seg.split_close.columns.equals(seg.prices.columns):
        raise refuse("registration_invalid", f"{seg.segment_id}: split-only close panels")
    prices = sig.PricePanel(seg.calendar, seg.prices.columns, seg.split_close.to_numpy(dtype=float),
                            seg.split_factor.reindex_like(seg.split_close).to_numpy(dtype=float))
    mask = seg.schedule.evaluation_mask.to_numpy(dtype=bool)
    status_of = sec.status_of()
    columns = list(seg.prices.columns)
    values = {s: np.full(mask.shape, np.nan) for s in sig.SIGNALS}
    statuses: dict[str, dict[int, np.ndarray]] = {s: {} for s in sig.SIGNALS}
    preferred: dict[int, np.ndarray] = {}
    for r in (int(x) for x in seg.schedule.evaluation_resets):
        row = r - 1
        day = seg.calendar[row].date().isoformat()
        for s in sig.SIGNALS:
            statuses[s][r] = np.full(len(columns), None, dtype=object)
        preferred[r] = np.zeros(len(columns), dtype=bool)
        for col in np.flatnonzero(mask[row]):
            if columns[col] not in status_of:
                raise refuse("sec_identity_pool_mismatch", seg.segment_id)
            status, cik = status_of[columns[col]]
            if status != ident.UNIQUE:
                for s in sig.SIGNALS:
                    statuses[s][r][col] = IDENTITY_REASON[status]
                continue
            cf = sec.facts[cik]  # type: ignore[index]
            if cf is None:
                for s in sig.SIGNALS:
                    statuses[s][r][col] = "facts_absent"
                continue
            fund = sig.fundamentals(cf, day)
            for s in sig.SIGNALS:
                value, reason = sig.signal_value(s, fund[s], day, prices, col, row)
                statuses[s][r][col] = reason or sig.RANKED
                if value is not None:
                    values[s][row, col] = value
            preferred[r][col] = statuses[sig.BM][r][col] == sig.RANKED and bool(fund[sig.BM]["preferred_zero"])
    frames = {s: pd.DataFrame(v, index=seg.prices.index, columns=seg.prices.columns) for s, v in values.items()}
    return SecPanels(signals=frames, statuses=statuses, preferred_zero=preferred)


def _class_rows(seg: s4.SegmentInputs, lookup: dict | None) -> np.ndarray:
    """Later exit class index per (segment row, column), from the member's resolved window."""

    out = np.full(seg.schedule.evaluation_mask.shape, EXIT_CLASSES.index(s4.UNKNOWN), dtype=np.int8)
    if lookup is None:
        return out
    n = out.shape[0]
    for col, pid in enumerate(seg.prices.columns):
        for m_in, m_out, klass in lookup.get(pid, []):
            lo, hi = max(m_in - seg.offset, 0), min(m_out - seg.offset, n)
            if hi > lo:
                out[lo:hi, col] = EXIT_CLASSES.index(klass)
    return out


def reconcile_sec_share(segment: str, signal_id: str, denominator: int, counts: Mapping[tuple[str, str], int]) -> None:
    """The statuses partition the evaluation-mask member-days; a gap or a double count refuses."""

    if None in {status for status, _ in counts} or sum(counts.values()) != denominator:
        raise refuse("sec_share_unreconciled", f"{segment} {signal_id}")


def day_statuses(seg: s4.SegmentInputs, panels: SecPanels, signal_id: str) -> np.ndarray:
    """The status of every evaluation-mask member-day over [first reset, last book row]; ``None`` elsewhere.

    A day belongs to the latest rebalance r at or before it: a member of that rebalance's ranking set (the mask at
    row r - 1) carries its rebalance-r status, any other member is ``not_ranked_at_rebalance``.
    """

    mask = seg.schedule.evaluation_mask.to_numpy(dtype=bool)
    resets = [int(x) for x in seg.schedule.evaluation_resets]
    first, last = seg.schedule.d0, seg.schedule.d_last
    if not resets or resets[0] != first:
        raise refuse("sec_share_unreconciled", f"{seg.segment_id}: first reset")
    out = np.full(mask.shape, None, dtype=object)
    for i, r in enumerate(resets):
        hi = min(resets[i + 1] if i + 1 < len(resets) else last + 1, last + 1)
        label = np.where(mask[r - 1], panels.statuses[signal_id][r], sig.NOT_RANKED)
        block = mask[r:hi]
        out[r:hi] = np.where(block, np.broadcast_to(label, block.shape), None)
    return out


def member_day_statuses(seg: s4.SegmentInputs, panels: SecPanels, lookup: dict | None) -> dict[str, Any]:
    """Per SEC sleeve: every evaluation-mask member-day over [first reset, last book row] gets one status."""

    mask = seg.schedule.evaluation_mask.to_numpy(dtype=bool)
    first, last = seg.schedule.d0, seg.schedule.d_last
    classes = _class_rows(seg, lookup)
    denominator = int(mask[first:last + 1].sum())
    out = {}
    for signal_id in sig.SIGNALS:
        days = day_statuses(seg, panels, signal_id)[first:last + 1]
        in_mask = mask[first:last + 1]
        counts = Counter(zip(days[in_mask], (EXIT_CLASSES[k] for k in classes[first:last + 1][in_mask])))
        reconcile_sec_share(seg.segment_id, signal_id, denominator, counts)
        by_status = {s: sum(n for (st, _), n in counts.items() if st == s) for s in STATUSES}
        by_class = {s: {k: counts.get((s, k), 0) for k in EXIT_CLASSES} for s in STATUSES}
        entry = {"denominator": denominator, "by_status": by_status,
                 "share": {s: by_status[s] / denominator if denominator else None for s in STATUSES},
                 "by_status_and_exit_class": by_class,
                 "exit_class_totals": {k: sum(by_class[s][k] for s in STATUSES) for k in EXIT_CLASSES}}
        if signal_id == sig.BM:
            pz: Counter[str] = Counter()
            resets = [int(x) for x in seg.schedule.evaluation_resets]
            for i, r in enumerate(resets):
                hi = min(resets[i + 1] if i + 1 < len(resets) else last + 1, last + 1)
                flag = mask[r - 1] & panels.preferred_zero[r]
                rows, cols = np.nonzero(mask[r:hi] & flag)
                pz.update(EXIT_CLASSES[k] for k in classes[rows + r, cols])
            entry["preferred_zero_by_absence"] = {"days": sum(pz.values()), "by_exit_class": dict(sorted(pz.items()))}
        out[signal_id] = entry
    return out


def rebalance_statuses(panels: SecPanels) -> dict[str, dict[str, int]]:
    """Member-rebalance counts: each ranking-set member gets exactly one rebalance status."""

    out = {}
    for signal_id, by_reset in panels.statuses.items():
        counts = Counter(v for arr in by_reset.values() for v in arr if v is not None)
        out[signal_id] = {s: int(counts.get(s, 0)) for s in STATUSES if s != sig.NOT_RANKED}
    out["preferred_zero_by_absence"] = {sig.BM: int(sum(a.sum() for a in panels.preferred_zero.values()))}
    return out


def identity_exposure(pool: pd.DataFrame, identity: pd.DataFrame, calendar: pd.DatetimeIndex,
                      spans: Mapping[str, tuple[int, int]]) -> dict[str, Any]:
    """Not-mapped share of member-days (calendar rows of [m_in, m_out) clipped to each segment span)."""

    status = {r["permanent_id"]: (r["status"], r["reason"]) for r in identity.to_dict(orient="records")}

    def table(counter: Counter) -> dict[str, Any]:
        total = sum(counter.values())
        not_mapped = sum(n for (st, _, _), n in counter.items() if st != ident.UNIQUE)
        by_class = {}
        for klass in EXIT_CLASSES:
            days = sum(n for (_, _, k), n in counter.items() if k == klass)
            miss = sum(n for (st, _, k), n in counter.items() if k == klass and st != ident.UNIQUE)
            by_class[klass] = {"days": days, "not_mapped": miss, "share": miss / days if days else None}
        reasons = Counter()
        for (st, reason, _), n in counter.items():
            if st != ident.UNIQUE:
                reasons[f"{st}: {reason}"] += n
        return {"days": total, "not_mapped": not_mapped, "share": not_mapped / total if total else None,
                "by_exit_class": by_class,
                "by_reason": {k: {"days": v, "share": v / total if total else None} for k, v in sorted(reasons.items())}}

    per: dict[str, Counter] = {}
    for row in pool.to_dict(orient="records"):
        window = s4.member_rows(row, calendar)
        if window is None:
            continue
        st, reason = status[row["permanent_id"]]
        for segment in row["segments"].split(";"):
            first, last = spans[segment]
            lo, hi = max(window[0], first), min(window[1], last + 1)
            if hi > lo:
                per.setdefault(segment, Counter())[(st, reason, row["exit_class"])] += hi - lo
    pooled: Counter = Counter()
    for counter in per.values():
        pooled.update(counter)
    return {**{segment: table(per[segment]) for segment in sorted(per)}, "pooled": table(pooled)}


# Books, class layer, and the decision ----------------------------------------------------------

def mapped_segment(seg: s4.SegmentInputs, unique_ids: set[str]) -> s4.SegmentInputs:
    """The price sleeves on the mapped universe: the evaluation mask restricted to uniquely mapped IDs."""

    keep = seg.prices.columns.isin(sorted(unique_ids))
    signals = {k: v.where(np.broadcast_to(keep, v.shape)) for k, v in seg.signals.items()}
    return dataclasses.replace(seg, signals=signals)


def sleeve_series(seg: s4.SegmentInputs, books: dict[str, Any], signal_ids: tuple[str, ...]) -> dict[str, Any]:
    labels = s4.month_labels(seg)
    months = s4.sleeve_months(seg)
    first_row = seg.calendar[seg.schedule.d0]
    monthly, sigma = {}, {}
    for case in s4.CASES:
        monthly[case] = pd.DataFrame({i: s4.compound_monthly(books["sleeves"][(i, case)].returns, labels)
                                      for i in signal_ids})
        sigma[case] = pd.DataFrame({i: s4.own_sigma(books["sleeves"][(i, case)].returns, months, first_row)
                                    for i in signal_ids})
    return {"monthly": monthly, "sigma": sigma}


def r0_book(monthly: pd.DataFrame, months: pd.PeriodIndex, bps: float) -> pd.DataFrame:
    in_set = pd.DataFrame(True, index=months, columns=monthly.columns)
    return s4.drift_portfolio(base.rule_weights("R0", in_set, in_set.astype(float)), monthly, bps)


def check_months(layer9: dict[str, Any], layer6: dict[str, Any], expected: tuple[str, str, int] | None,
                 segment: str) -> None:
    for case in s4.CASES:
        months = layer9[case]["months"]
        if not months.equals(layer6[case]["months"]):
            raise refuse("comparison_months_mismatch", f"{segment} {case}")
        if expected is not None and (str(months[0]), str(months[-1]), len(months)) != expected:
            raise refuse("comparison_months_mismatch", f"{segment} {case}: amendment 4 months")


def decide(rows: list[dict]) -> str:
    return "join" if s4.holds_all(rows) else "not_join"


def check_comparator(grid_r0: dict, committed: Mapping[str, Any], run_name: str) -> None:
    """R0_6 metrics must equal the committed step 4 R0 exactly (``comparator_mismatch``)."""

    mine = json.loads(json.dumps(s4._clean(grid_r0), sort_keys=True, allow_nan=False))
    if mine != committed["runs"][run_name]["rules"]["R0"]:
        raise refuse("comparator_mismatch", run_name)


def s4b_family(pvalues: pd.Series, family_size: int = FAMILY_SIZE) -> pd.Series:
    if len(pvalues) != OBSERVED_TESTS or family_size != FAMILY_SIZE:
        raise refuse("s4b_family_invalid", f"{len(pvalues)} observed, family size {family_size}")
    return adjust_pvalues(pvalues, method="by", family_size=family_size)


def fragility(primary: dict[str, Any], other: dict[str, Any]) -> dict[str, Any]:
    """Fragile when the S4b.ADD mean sign, any of the 8 margin signs, or the outcome differs between the runs."""

    flips = [TEST_ID] if s4.sign(primary["s4b_mean"]) != s4.sign(other["s4b_mean"]) else []
    for a, b in zip(primary["conditions"], other["conditions"]):
        if s4.sign(a["margin"]) != s4.sign(b["margin"]):
            flips.append(f"{a['segment']}:{a['cost_case']}:{a['metric']}")
    outcome = ["outcome"] if primary["outcome"] != other["outcome"] else []
    return {"fragile": bool(flips or outcome), "sign_changes": flips, "outcome_changes": outcome}


def coverage_tilt(vs_r0_6: list[dict], vs_mapped: list[dict]) -> dict[str, Any]:
    flips = [f"{a['segment']}:{a['cost_case']}:{a['metric']}" for a, b in zip(vs_r0_6, vs_mapped)
             if s4.sign(a["margin"]) != s4.sign(b["margin"])]
    return {"coverage_tilted": bool(flips), "sign_changes": flips}


def public_counterpart(public: s4.PublicInputs, layers: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
    """R0 over the 9 matched JKP characteristics against R0 over the 6 (v1 Sharpe), sliced to each window."""

    chars = {"R0_9": [ALL_SLEEVES[s][0] for s in ALL_IDS], "R0_6": [ALL_SLEEVES[s][0] for s in FAMILY_A_IDS]}
    values = public.jkp[chars["R0_9"]]
    defined = values.notna().all(axis=1)
    months = values.index[defined.to_numpy() & (values.index <= public.last_month)]
    span = pd.period_range(months[0], months[-1], freq="M")
    grid: dict[str, dict[str, dict[str, Any]]] = {book: {} for book in chars}
    for book, columns in chars.items():
        in_set = pd.DataFrame(True, index=span, columns=columns)
        weights = base.rule_weights("R0", in_set, in_set.astype(float))
        for case in s4.CASES:
            net = base.portfolio(weights, values[columns], s4.SWITCH_BPS[case])["net"]
            grid[book][case] = {sid: base.performance(net.loc[layer[case]["months"][0]:layer[case]["months"][-1]])
                                for sid, layer in layers.items()}
    return {"rules": grid, "conditions": s4.conditions(grid["R0_9"], grid["R0_6"])}


def evaluate_run(segments: Mapping[str, s4.SegmentInputs], panels: Mapping[str, SecPanels],
                 public: s4.PublicInputs, step4_run: dict[str, Any], unique_ids: set[str], terminal_return: float,
                 seal_gap_ids: set[str], lookup: dict | None, expected_months: Mapping[str, Any] | None
                 ) -> dict[str, Any]:
    """One event run: SEC sleeves, R0_9 and rule R1 over nine, R0_6 from step 4, R0_6_mapped, and tables."""

    seg_out = {}
    for sid, seg in segments.items():
        six = step4_run["seg"][sid]
        sec_seg = dataclasses.replace(seg, signals=panels[sid].signals)
        sec_books = s4.run_books(sec_seg, terminal_return, SEC_IDS)
        sec_series = sleeve_series(sec_seg, sec_books, SEC_IDS)
        monthly = {c: pd.concat([six["monthly"][c], sec_series["monthly"][c]], axis=1) for c in s4.CASES}
        sigma = {c: pd.concat([six["sigma"][c], sec_series["sigma"][c]], axis=1) for c in s4.CASES}
        layer9 = s4.class_layer(monthly, sigma, None, public.last_month)
        check_months(layer9, six["layer"], None if expected_months is None else expected_months[sid], sid)
        mapped_seg = mapped_segment(seg, unique_ids)
        mapped = sleeve_series(mapped_seg, s4.run_books(mapped_seg, terminal_return), FAMILY_A_IDS)
        books = {}
        for case in s4.CASES:
            months = six["layer"][case]["months"]
            books[case] = {"R0_9": layer9[case]["books"]["R0"], "R1_9": layer9[case]["books"]["R1"],
                           "R0_6": six["layer"][case]["books"]["R0"],
                           "R0_6_mapped": r0_book(mapped["monthly"][case], months, s4.SWITCH_BPS[case])}
        seg_out[sid] = {"sec_books": sec_books, "monthly": monthly, "sigma": sigma, "layer9": layer9,
                        "books": books, "six": six}
    grid = {book: {case: {sid: s4.metrics(seg_out[sid]["books"][case][book]["net"], public.rf,
                                          seg_out[sid]["books"][case][book]["turnover"])
                          for sid in segments} for case in s4.CASES} for book in BOOKS}
    cond = s4.conditions(grid["R0_9"], grid["R0_6"])
    cond_mapped = s4.conditions(grid["R0_9"], grid["R0_6_mapped"])
    diff = pd.concat([seg_out[sid]["books"]["primary"]["R0_9"]["net"] - seg_out[sid]["books"]["primary"]["R0_6"]["net"]
                      for sid in s4.SEGMENTS if sid in segments])
    pub = public_counterpart(public, {sid: seg_out[sid]["six"]["layer"] for sid in segments})
    survival = [{**row, "public_margin": p["margin"], "public_holds": p["holds"],
                 "margin_ratio": s4.ratio(row["margin"], p["margin"])} for row, p in zip(cond, pub["conditions"])]
    tables = describe(segments, seg_out, public, seal_gap_ids, lookup)
    return {"seg": seg_out, "grid": grid, "conditions": cond, "conditions_vs_mapped": cond_mapped,
            "outcome": decide(cond), "counts": {"vs_R0_6": sum(r["holds"] for r in cond),
                                                "vs_R0_6_mapped": sum(r["holds"] for r in cond_mapped)},
            "diff": diff, "s4b_mean": float(diff.mean()), "public": pub, "survival": survival, "tables": tables}


def describe(segments: Mapping[str, s4.SegmentInputs], seg_out: dict[str, Any], public: s4.PublicInputs,
             seal_gap_ids: set[str], lookup: dict | None) -> dict[str, Any]:
    out: dict[str, Any] = {"sleeves": {}, "benchmarks": {}, "excess": {}, "events": {}, "halts": {},
                           "transmission": {}, "class_transmission": {}, "comparison_months": {}, "weights_mean": {}}
    for sid, seg in segments.items():
        s, six = seg_out[sid], seg_out[sid]["six"]
        months = six["sleeve_months"]
        cmp_months = {case: six["layer"][case]["months"] for case in s4.CASES}
        out["comparison_months"][sid] = {c: [str(m[0]), str(m[-1]), int(len(m))] for c, m in cmp_months.items()}
        out["sleeves"][sid] = {f"{i}|{case}": {**s4.metrics(s["monthly"][case][i], public.rf),
                                               **s4.stock_trading(s["sec_books"]["sleeves"][(i, case)],
                                                                  six["sleeve_rows"], len(months))}
                               for i in SEC_IDS for case in s4.CASES}
        ex = {}
        for case in s4.CASES:
            for book in BOOKS:
                net = s["books"][case][book]["net"]
                ex[f"{book}|{case}"] = {"vs_spy": s4.excess(net, six["spy"]), "vs_equal_weight": s4.excess(net, six["ew"])}
            for i in SEC_IDS:
                net = s["monthly"][case][i]
                ex[f"{i}|{case}"] = {"vs_spy": s4.excess(net, six["spy"]), "vs_equal_weight": s4.excess(net, six["ew"])}
            out["weights_mean"].setdefault(sid, {})[case] = {
                "R1_9": {k: float(v) for k, v in s["layer9"][case]["weights"]["R1"].mean().items()}}
        out["excess"][sid] = ex
        window = set(cmp_months["primary"])
        ev = {f"{i}|{case}": s4.book_event_summary(s4.held_events(s["sec_books"]["sleeves"][(i, case)]),
                                                   seal_gap_ids, window)
              for i in SEC_IDS for case in s4.CASES}
        for case in s4.CASES:
            books = {**{i: six["books"]["sleeves"][(i, case)] for i in FAMILY_A_IDS},
                     **{i: s["sec_books"]["sleeves"][(i, case)] for i in SEC_IDS}}
            ev[f"R0_9|{case}"] = s4.rule_event_summary(
                {i: s4.held_events(b) for i, b in books.items()}, {i: s4.gross_growth_path(b) for i, b in books.items()},
                s["layer9"][case]["weights"]["R0"], seg.calendar, seal_gap_ids)
        out["events"][sid] = ev
        out["halts"][sid] = {f"{i}|{case}": s4.halt_counts(s["sec_books"]["sleeves"][(i, case)], seg, lookup)
                             for i in SEC_IDS for case in s4.CASES}
        t_months = months[months <= public.last_month]
        active = s["monthly"]["primary"].loc[t_months, list(SEC_IDS)].sub(six["ew"].loc[t_months], axis=0)
        out["transmission"][sid] = {i: s4._transmission(active[i], public.jkp[SEC_SLEEVES[i][0]].reindex(t_months))
                                    for i in SEC_IDS}
        cm = cmp_months["primary"]
        klass = s4.class_returns(s["monthly"]["primary"], s["sigma"]["primary"], cm, SEC_SLEEVES, SEC_THEMES)
        klass = klass.sub(six["ew"].loc[cm], axis=0)
        out["class_transmission"][sid] = {t: s4._transmission(klass[t], public.class_values[t].reindex(cm))
                                          for t in SEC_THEMES}
    pooled = {}
    for i in SEC_IDS:
        a, b = [], []
        for sid in segments:
            months = seg_out[sid]["six"]["sleeve_months"]
            months = months[months <= public.last_month]
            a.append(seg_out[sid]["monthly"]["primary"].loc[months, i] - seg_out[sid]["six"]["ew"].loc[months])
            b.append(public.jkp[SEC_SLEEVES[i][0]].reindex(months))
        pooled[i] = s4._transmission(pd.concat(a), pd.concat(b))
    out["transmission"]["pooled"] = pooled
    return out


def step4_document(result4: dict[str, Any], segments: Mapping[str, s4.SegmentInputs], lookup: dict | None
                   ) -> dict[str, Any]:
    """The computed part of ``reports/m5_step4.json`` from the recomputed step 4 chain."""

    doc = s4.summarize(result4)
    doc["runs"]["primary"]["signal_exclusions"] = s4._clean(
        {sid: s4.signal_exclusions(seg, lookup) for sid, seg in segments.items()})
    return json.loads(json.dumps(doc, sort_keys=True, allow_nan=False))


def check_step4_regeneration(doc4: Mapping[str, Any], committed: Mapping[str, Any]) -> None:
    """The recomputed step 4 results equal the committed step 4 report (parameterization kept outputs unchanged)."""

    for key in ("runs", "s4_tests", "fragility", "family"):
        if doc4[key] != committed[key]:
            raise refuse("step4_regeneration_mismatch", key)


def evaluate(segments: Mapping[str, s4.SegmentInputs], public: s4.PublicInputs, sec: SecInputs,
             committed: Mapping[str, Any], seal_gap_ids: set[str] = frozenset(), lookup: dict | None = None,
             expected_months: Mapping[str, Any] | None = COMPARISON_MONTHS,
             step4_result: dict[str, Any] | None = None) -> dict[str, Any]:
    """Both event runs, the comparator and month checks, S4b.ADD with its BY q-value, and the labels."""

    check_identity_pool(segments, sec)
    result4 = step4_result or s4.evaluate(dict(segments), public, set(seal_gap_ids), lookup)
    doc4 = step4_document(result4, segments, lookup)
    for name in s4.EVENT_RUNS:
        check_comparator(result4["runs"][name]["grid"]["R0"], committed, name)
    check_step4_regeneration(doc4, committed)
    panels = {sid: sec_panels(seg, sec) for sid, seg in segments.items()}
    unique_ids = set(sec.identity.loc[sec.identity["status"] == ident.UNIQUE, "permanent_id"])
    runs = {name: evaluate_run(segments, panels, public, result4["runs"][name], unique_ids, value,
                               set(seal_gap_ids), lookup, expected_months)
            for name, value in s4.EVENT_RUNS.items()}
    primary = runs["primary"]
    test = step3.rule_test(primary["diff"])
    pvalue = pd.Series({TEST_ID: 1.0 if test["hac_pvalue"] is None else float(test["hac_pvalue"])})
    test["family_p"], test["by_qvalue"] = float(pvalue[TEST_ID]), float(s4b_family(pvalue)[TEST_ID])
    statuses = {sid: member_day_statuses(seg, panels[sid], lookup) for sid, seg in segments.items()}
    return {"runs": runs, "test": test, "fragility": fragility(primary, runs["last_close"]),
            "coverage_tilt": coverage_tilt(primary["conditions"], primary["conditions_vs_mapped"]),
            "sec_share": statuses, "rebalance_statuses": {sid: rebalance_statuses(p) for sid, p in panels.items()},
            "value_conflicts": sum(cf.value_conflicts for cf in sec.facts.values() if cf is not None),
            "panels": panels, "step4": result4}


# Output ---------------------------------------------------------------------------------------

def summarize(result: dict[str, Any]) -> dict[str, Any]:
    """The JSON-ready aggregate view: no series, no identifier, no path."""

    runs = {}
    for name, run in result["runs"].items():
        runs[name] = {"outcome": run["outcome"], "counts": run["counts"], "conditions": run["conditions"],
                      "conditions_vs_mapped": run["conditions_vs_mapped"], "s4b_mean": run["s4b_mean"],
                      "rules": run["grid"], "survival": run["survival"], "public_rules": run["public"]["rules"],
                      **run["tables"]}
    keys = ("status", "n_observations", "mean_return", "hac_statistic", "hac_pvalue", "hac_lags", "ci95_monthly",
            "ci95_annual", "family_p", "by_qvalue")
    return s4._clean({
        "decision": {"outcome": result["runs"]["primary"]["outcome"],
                     "last_close_outcome": result["runs"]["last_close"]["outcome"]},
        "runs": runs, "s4b_test": {TEST_ID: {k: result["test"].get(k) for k in keys}},
        "fragility": result["fragility"], "coverage_tilt": result["coverage_tilt"],
        "family": {"observed_tests": OBSERVED_TESTS, "prior_slots": FAMILY_SIZE - OBSERVED_TESTS,
                   "family_size": FAMILY_SIZE, "method": "by"},
        "sec_share": result["sec_share"], "rebalance_statuses": result["rebalance_statuses"],
        "first_filed_value_conflicts": result["value_conflicts"], "locked_holdings": LOCKED_HOLDINGS})


_f, _book = s4._f, s4._book


def _conditions_table(rows: list[dict], with_public: bool = False) -> list[str]:
    head = "| Segment | Cost case | Metric | R0_9 | Comparator | Margin | Holds |"
    rule = "| --- | --- | --- | --- | --- | --- | --- |"
    if with_public:
        head, rule = head + " Public margin | Public holds | Ratio |", rule + " --- | --- | --- |"
    lines = [head, rule]
    for r in rows:
        line = (f"| {r['segment']} | {r['cost_case']} | {r['metric']} | {_f(r['candidate'], 4)} | "
                f"{_f(r['comparator'], 4)} | {_f(r['margin'], 4)} | {'yes' if r['holds'] else 'no'} |")
        if with_public:
            line += f" {_f(r['public_margin'], 4)} | {'yes' if r['public_holds'] else 'no'} | {_f(r['margin_ratio'], 2)} |"
        lines.append(line)
    return lines + [""]


def render_report(doc: dict[str, Any]) -> str:
    p, lc = doc["runs"]["primary"], doc["runs"]["last_close"]
    test = doc["s4b_test"][TEST_ID]
    frag, tilt = doc["fragility"], doc["coverage_tilt"]
    unpriced = doc.get("unpriced", {})
    outcome = doc["decision"]["outcome"]
    joined = "join" if outcome == "join" else "do not join"
    lines = [
        "# Milestone 5 Step 4b: SEC Value and Quality Sleeves on Point-in-Time S&P 500 Books", "",
        "**Evidence ceiling: `DIAGNOSTIC_ONLY`.** Simulated research on the local `real_v2` snapshot and the pinned "
        "SEC companyfacts cache; no profitability claim. Aggregates only.", "",
        f"- **VP-2.** {s4.VP2} Owner decision O-9 extends it to step 4b.",
        "- **R4.** No terminal evidence is accepted. Every residual held stop settles at -100 percent in every price "
        "and SEC sleeve and in the equal-weight benchmark; a last-close rerun is reported beside it.",
        "- **Unpriced members** are never held. Unpriced member-day share: "
        + "; ".join(f"{sid} {_f(u.get('unpriced_share'), 3, True)} (upper bound "
                    f"{_f(u.get('unpriced_share_upper_bound'), 3, True)})" for sid, u in unpriced.items())
        + f". {s4.STAGE_D_PRE_UNPRICED}.",
        "- **Missing crash.** The seal window and its buffers exclude 2019-07 to 2021-08, including the 2020 crash, "
        "so drawdowns are understated.",
        "- **Prior exposure.** Every step 4 number is seen on the same 99 comparison months; be_me, ni_me, and gp_at "
        "are in the public books of steps 2 and 3. No step 4b result is confirmatory.", "",
        "## Decision Outcome (primary run)", "",
        f"- **Outcome: {outcome}.** The SEC Value and Quality classes {joined} the baseline class set: R0_9 meets "
        f"{p['counts']['vs_R0_6']} of 8 conditions against R0_6.",
        f"- **{TEST_ID}:** mean monthly difference {_f(test['mean_return'], 5)} over {test['n_observations']} months, "
        f"HAC p {_f(test['hac_pvalue'], 4)}, BY q {_f(test['by_qvalue'], 4)} (family of {FAMILY_SIZE}, 1 observed), "
        f"95% interval (monthly) {_interval(test['ci95_monthly'])}.",
        f"- **Fragility: {'FRAGILE' if frag['fragile'] else 'not fragile'}** ({len(frag['sign_changes'])} sign "
        f"changes between the -100 percent run and the last-close rerun; outcome changes: "
        f"{', '.join(frag['outcome_changes']) or 'none'}).",
        f"- **Coverage tilt: {'COVERAGE-TILTED' if tilt['coverage_tilted'] else 'not coverage-tilted'}** "
        f"({len(tilt['sign_changes'])} margin signs differ against R0_6_mapped; R0_9 meets "
        f"{p['counts']['vs_R0_6_mapped']} of 8 against it).",
        f"- **Last-close outcome: {lc['outcome']}** ({lc['counts']['vs_R0_6']} of 8; {TEST_ID} mean "
        f"{_f(lc['s4b_mean'], 5)}, no p-value).",
        "- The labels, the q-value, and the last-close outcome are reported beside the outcome and do not change it.",
        "",
        "## Conditions: R0_9 Against R0_6 Beside the Public Margins (primary run)", "",
        *_conditions_table(p["survival"], with_public=True),
        "## Coverage Tilt: R0_9 Against R0_6_mapped (primary run)", "",
        *_conditions_table(p["conditions_vs_mapped"]),
        "## Conditions in the Last-Close Rerun", "",
        *_conditions_table(lc["conditions"]),
        "## Rule Books", "",
        "| Run | Book | Cost case | Segment | Months | Ann. mean | Volatility | Sharpe | Max drawdown | Turnover |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, run in doc["runs"].items():
        for book in BOOKS:
            for case in s4.CASES:
                for sid, m in run["rules"][book][case].items():
                    lines.append(f"| {name} | {book} | {case} | {sid} | {m['months']} | {_f(m['annualized_mean'], 3, True)}"
                                 f" | {_f(m['volatility'], 3, True)} | {_f(m['sharpe'])} | "
                                 f"{_f(m['max_drawdown'], 3, True)} | {_f(m['average_monthly_turnover'])} |")
    lines += ["", "Rule R1 over nine sleeves (R1_9) is descriptive: no test and no decision. R2 is not run.", "",
              "## SEC Sleeves (primary run)", "",
              "| Segment | Sleeve | Months | Ann. mean | Sharpe | Max drawdown | Stock turnover / month | "
              "Stock cost / month |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for sid, rows in p["sleeves"].items():
        for key, m in rows.items():
            lines.append(f"| {sid} | {_book(key)} | {m['months']} | {_f(m['annualized_mean'], 3, True)} | "
                         f"{_f(m['sharpe'])} | {_f(m['max_drawdown'], 3, True)} | "
                         f"{_f(m['stock_turnover_monthly_mean'])} | {_f(m['stock_cost_monthly_mean'], 5)} |")
    lines += ["", "## Benchmarks: Net Excess (primary run, comparison months for books)", "",
              "| Segment | Book | Ann. excess vs SPY | Compounded vs SPY | Ann. excess vs EW | Compounded vs EW | "
              "Unpriced share |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for sid, rows in p["excess"].items():
        share = _f(unpriced.get(sid, {}).get("unpriced_share"), 3, True)
        for key, e in rows.items():
            lines.append(f"| {sid} | {_book(key)} | {_f(e['vs_spy']['annualized_mean_excess'], 3, True)} | "
                         f"{_f(e['vs_spy']['excess_total_return'], 3, True)} | "
                         f"{_f(e['vs_equal_weight']['annualized_mean_excess'], 3, True)} | "
                         f"{_f(e['vs_equal_weight']['excess_total_return'], 3, True)} | {share} |")
    lines += ["", "## SEC Missingness by Reason and Later Exit Class (member-days)", "",
              "Every evaluation-mask member-day over [first reset, last book row] carries exactly one status per SEC "
              "sleeve; a ranking-set member carries its rebalance status, any other member-day is "
              f"not_ranked_at_rebalance. {LOCKED_HOLDINGS}", ""]
    lines += _share_tables(doc["sec_share"])
    lines += ["## Identity Exposure (member-days of the eligible pool)", ""]
    lines += _exposure_tables(doc.get("identity_exposure", {}))
    lines += ["## Affected Events (primary run, R4 default)", "",
              "| Segment | Book | Events | Weight sum | Weight max |", "| --- | --- | --- | --- | --- |"]
    for sid, rows in p["events"].items():
        for key, e in rows.items():
            if "unique_events" in e:
                lines.append(f"| {sid} | {_book(key)} | {e['unique_events']} | {_f(e['weight_sum'], 4)} | "
                             f"{_f(e['weight_max'], 4)} |")
            else:
                lines.append(f"| {sid} | {_book(key)} | {e['all']['count']} | {_f(e['all']['weight_sum'], 4)} | "
                             f"{_f(e['all']['weight_max'], 4)} |")
    lines += ["", "## Transmission (descriptive, primary cost case)", "",
              "| Segment | Sleeve or class | Months | PIT mean active | Public mean | Ratio | Correlation |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for sid, rows in {**p["transmission"], **{f"{k} (class)": v for k, v in p["class_transmission"].items()}}.items():
        for key, t in rows.items():
            lines.append(f"| {sid} | {key} | {t['months']} | {_f(t['pit_mean_active'], 5)} | {_f(t['public_mean'], 5)} "
                         f"| {_f(t['ratio'], 2)} | {_f(t['correlation'], 2)} |")
    lines += ["", "## Halts in the SEC Sleeves (primary run)", "",
              "| Segment | Sleeve | Unmarked halt rows | Locked execution rows |", "| --- | --- | --- | --- |"]
    for sid, rows in p["halts"].items():
        for key, h in rows.items():
            lines.append(f"| {sid} | {_book(key)} | {h['unmarked_halt_rows']} | {h['locked_execution_rows']} |")
    lines += ["", "## Data Quality", "",
              f"- First-filed value ties with distinct values inside one accession: {doc['first_filed_value_conflicts']} "
              "keys; the lowest accession's first fact in file order is used.",
              "- Rebalance statuses (member-rebalances, each ranking-set member exactly once): "
              + "; ".join(f"{sid} {i} ranked {rs[i]['ranked']}" for sid, rs in doc["rebalance_statuses"].items()
                          for i in SEC_IDS) + ".", "",
              "## Limitations", "",
              "- Companyfacts carries no dimensional facts, so unlisted share classes are not detected.",
              "- Concept chains are frozen; a filer whose tag is outside a chain is concept_missing, not repaired.",
              "- The mapped universe keeps 563 of 632 eligible IDs; the not-mapped share differs by later exit class "
              "(identity exposure above), which the coverage-tilt label addresses descriptively.",
              "- SEC facts filed inside the seal window may enter an early post-segment signal; no seal-window price "
              "is read.", ""]
    return "\n".join(lines) + "\n"


def _interval(pair: Any) -> str:
    return "n/a" if not pair else f"[{_f(pair[0], 5)}, {_f(pair[1], 5)}]"


def _share_tables(share: Mapping[str, Any]) -> list[str]:
    lines = []
    for sid, sleeves in share.items():
        for signal_id, entry in sleeves.items():
            lines += [f"{sid}, {signal_id}: {entry['denominator']} member-days."
                      + (f" preferred_zero_by_absence: {entry['preferred_zero_by_absence']['days']} ranked member-days."
                         if "preferred_zero_by_absence" in entry else ""), "",
                      "| Status | Days | Share | " + " | ".join(EXIT_CLASSES) + " |",
                      "| --- | --- | --- |" + " --- |" * len(EXIT_CLASSES)]
            for status in STATUSES:
                row = entry["by_status_and_exit_class"][status]
                lines.append(f"| {status} | {entry['by_status'][status]} | {_f(entry['share'][status], 3, True)} | "
                             + " | ".join(str(row[k]) for k in EXIT_CLASSES) + " |")
            lines.append("")
    return lines


def _exposure_tables(exposure: Mapping[str, Any]) -> list[str]:
    lines = ["| Scope | Exit class | Member-days | Not mapped | Share |", "| --- | --- | --- | --- | --- |"]
    for scope, t in exposure.items():
        lines.append(f"| {scope} | all | {t['days']} | {t['not_mapped']} | {_f(t['share'], 3, True)} |")
        for klass, c in t["by_exit_class"].items():
            lines.append(f"| {scope} | {klass} | {c['days']} | {c['not_mapped']} | {_f(c['share'], 3, True)} |")
    lines += ["", "| Scope | Status: reason | Member-days | Share of all |", "| --- | --- | --- | --- |"]
    for scope, t in exposure.items():
        for reason, c in t["by_reason"].items():
            lines.append(f"| {scope} | {reason} | {c['days']} | {_f(c['share'], 3, True)} |")
    return lines + [""]


# Run --------------------------------------------------------------------------------------------

def run(repo_root: Path, snapshot_dir: Path, git: dict[str, Any]) -> dict[str, Any]:
    step3.verify_trial_files(repo_root, TRIAL_PINS)
    public = s4.load_public(repo_root, ALL_SLEEVES, PUBLIC_THEMES)
    bound = dm.bind(snapshot_dir, repo_root)
    root = bound["snapshot"].root
    pool = dm.eligible_pool(pd.read_csv(root / INTERVAL_RESULTS, dtype=str, keep_default_na=False),
                            pd.read_csv(root / SECURITY_MASTER, dtype=str, keep_default_na=False),
                            bound["inventory"]["files"])
    sec = load_sec(repo_root, snapshot_dir)
    if sorted(pool["permanent_id"]) != sorted(sec.identity["permanent_id"]):
        raise refuse("sec_identity_pool_mismatch", "eligible pool and pinned map differ")
    runs, access = s4.load_segment_runs_step4(bound)
    segments = {r.segment.segment_id: s4.prepare(r, s4.registered_rows(r.segment.segment_id)) for r in runs}
    shares, lookup, seal_gap = s4.snapshot_accounting(bound)
    committed = json.loads((repo_root / STEP4_JSON).read_text(encoding="utf-8"))
    result = evaluate(segments, public, sec, committed, seal_gap, lookup)
    spans = {seg.segment_id: (seg.first_reset_row, seg.last_book_row) for seg in bound["segments"]}
    exposure = identity_exposure(pool, sec.identity, bound["calendar"], spans)
    s4.verify_pins_unchanged(snapshot_dir)
    doc = summarize(result)
    doc.update(s4._clean({
        "schema_version": "m5_step4b_v1", "evidence_ceiling": "DIAGNOSTIC_ONLY",
        "run_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trial_files": TRIAL_PINS, "git": git,
        "snapshot": {"id": s4.SNAPSHOT_ID, "pins": s4.SNAPSHOT_PINS,
                     "discovery_inputs_sha256": s4.DISCOVERY_INPUTS_SHA256, "segment_access_sides": access},
        "sec": {"pins": SEC_PINS, "build_code": BUILD_CODE, "requests": sec.requests,
                "unique_ciks_read": len(sec.facts), "recorded_absent": sum(v is None for v in sec.facts.values()),
                "identity_counts": dict(sorted(Counter(sec.identity["status"]).items()))},
        "public_manifest_sha256": s4.PUBLIC_MANIFEST_SHA256, "public_last_month": str(public.last_month),
        "vp2": s4.VP2, "unpriced": shares, "identity_exposure": exposure, "stage_d_note": s4.STAGE_D_PRE_UNPRICED,
        "costs": {"stock": s4.STOCK_COSTS, "switch_bps": s4.SWITCH_BPS}, "sigma_rows": s4.SIGMA_ROWS,
        "top_pct": s4.TOP_PCT, "step4_regenerated": True,
    }))
    return doc


def _append_attempt(repo_root: Path, record: dict[str, Any]) -> None:
    path = repo_root / ATTEMPTS_JSONL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def write_outputs(repo_root: Path, doc: dict[str, Any]) -> dict[str, str]:
    (repo_root / REPORT_JSON).write_text(json.dumps(doc, indent=2, sort_keys=True, allow_nan=False) + "\n",
                                         encoding="utf-8")
    (repo_root / REPORT_MD).write_text(render_report(doc), encoding="utf-8")
    return {path: _sha((repo_root / path).read_bytes()) for path in (REPORT_MD, REPORT_JSON)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--snapshot-dir", required=True, help="the real_v2 snapshot directory (never recorded)")
    parser.add_argument("--reason", required=True, help="why this attempt runs")
    args = parser.parse_args(argv)
    snapshot_dir = Path(args.snapshot_dir)
    attempt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    git = base.git_state(REPO_ROOT)
    _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "start", "reason": args.reason,
                                "amendment_5_sha256": AMENDMENT_5_SHA256, "snapshot_id": s4.SNAPSHOT_ID,
                                "snapshot_pins": s4.SNAPSHOT_PINS, "sec_pins": SEC_PINS, **git})
    started = time.perf_counter()
    try:
        for guarded in (snapshot_dir, REPO_ROOT / dm.CACHE_DIR, dm.private_dir_for(snapshot_dir, REPO_ROOT)):
            dm.guard_snapshot(guarded)
        doc = run(REPO_ROOT, snapshot_dir, git)
        outputs = write_outputs(REPO_ROOT, doc)
    except Exception as error:
        _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "end", "status": "refused",
                                    "reason": getattr(error, "reason", type(error).__name__),
                                    "seconds": round(time.perf_counter() - started, 1)})
        raise
    _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "end", "status": "completed",
                                "outcome": doc["decision"]["outcome"],
                                "last_close_outcome": doc["decision"]["last_close_outcome"],
                                "fragile": doc["fragility"]["fragile"],
                                "coverage_tilted": doc["coverage_tilt"]["coverage_tilted"],
                                "by_qvalue": doc["s4b_test"][TEST_ID]["by_qvalue"], "outputs": outputs,
                                "seconds": round(time.perf_counter() - started, 1)})
    print(f"outcome {doc['decision']['outcome']}; fragile {doc['fragility']['fragile']}; "
          f"coverage-tilted {doc['coverage_tilt']['coverage_tilted']}; report {REPORT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
