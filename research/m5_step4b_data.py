"""Milestone 5 step 4b data build: the SEC CIK map and company-facts cache for the real_v2 securities.

Run with ``PYTHONPATH=src .venv/bin/python -m research.m5_step4b_data --snapshot-dir <real_v2> --reason "<why>"``.
It refuses unless ``EFR_SEC_USER_AGENT`` is set and ``real_v2`` matches amendment 4's pins. It downloads SEC's
ticker files, the EDGAR name list, and the submissions (with history pages) of every rule F candidate CIK, maps
each eligible permanent ID under fail-closed rule F (``research.m5_sec_identity``), and then downloads company
facts for every uniquely mapped CIK. Every request goes through ``data.sec_edgar``. ``--offline`` rebuilds from
the cache only and refuses unless the CIK map and the per-file hash list equal the committed manifest.

Outputs (R11 and the O-10 terms):

- local only, beside the snapshot in ``<snapshot parent>/m5_step4b_sec/``: the CIK map, which pairs vendor codes
  with CIKs, and the full per-file hash list;
- committed: ``reports/m5_step4b_sec_manifest.json`` (URL templates, retrieval dates, file counts and bytes, one
  SHA-256 over the sorted hash list, and the SHA-256 of the CIK map) and ``reports/m5_step4b_data.md`` (coverage
  counts), plus one start and one end record per attempt in ``reports/m5_step4b_data_attempts.jsonl``.

No signal, sleeve, return, or rule result is computed. Nothing is written inside the snapshot, and nothing under
its ``terminal/`` or ``quarantine/`` directories is opened (an audit hook refuses either). Evidence ceiling
``DIAGNOSTIC_ONLY``.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

from data.sec_edgar import (
    CIK_LOOKUP_URL,
    COMPANY_TICKERS_EXCHANGE_URL,
    COMPANY_TICKERS_URL,
    COMPANYFACTS_URL,
    SUBMISSIONS_URL,
    SecClient,
    SecFile,
    SecRefusal,
    user_agent,
)
from research import m5_factor_baseline as base
from research import m5_sec_identity as ident
from research import m5_step4 as step4
from research.m4_7_universe_build import INTERVAL_RESULTS, SECURITY_MASTER

REPO_ROOT = base.REPO_ROOT
CACHE_DIR = Path("data/public_cache/sec")
PRIVATE_DIRNAME = "m5_step4b_sec"
MAP_FILE = "cik_map.csv"
HASH_LIST_FILE = "file_hashes.tsv"
MANIFEST_JSON = "reports/m5_step4b_sec_manifest.json"
REPORT_MD = "reports/m5_step4b_data.md"
ATTEMPTS_JSONL = "reports/m5_step4b_data_attempts.jsonl"
SNAPSHOT_READ_SCOPE_BLOCKED = ("terminal", "quarantine")
ENDED = frozenset({"delisting_candidate", "disappearance_outside_membership"})
ANNUAL_FACT_FORMS = frozenset({"10-K", "10-KT"})
PAGE_NAME = re.compile(r"CIK\d{10}-submissions-\d{3}\.json")
MAP_COLUMNS = ["permanent_id", "vendor_code", "segments", "exit_class", "status", "reason", "cik"]
SUBMISSIONS_TEMPLATE = SUBMISSIONS_URL.format(name="CIK{cik:010d}.json")
PAGE_TEMPLATE = SUBMISSIONS_URL.format(name="CIK{cik:010d}-submissions-{page:03d}.json")


def refuse(reason: str, detail: str = "") -> step4.runner.RunnerStop:
    return step4.runner.RunnerStop(reason, detail)


# Snapshot guard and eligible pool ---------------------------------------------------------

def guard_snapshot(snapshot_dir: Path) -> None:
    """Refuse any write inside the snapshot and any open under its ``terminal/`` or ``quarantine/``."""

    root = os.path.abspath(snapshot_dir) + os.sep
    blocked = tuple(root + name + os.sep for name in SNAPSHOT_READ_SCOPE_BLOCKED)
    write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND

    def hook(event: str, args: tuple[Any, ...]) -> None:
        if event != "open" or not isinstance(args[0], (str, bytes, os.PathLike)):
            return
        path = os.path.abspath(os.fsdecode(args[0])) + os.sep
        if not path.startswith(root):
            return
        mode, flags = args[1], args[2] if len(args) > 2 else 0
        writes = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool((flags or 0) & write_flags)
        if writes or path.startswith(blocked):
            raise PermissionError("snapshot access outside the step 4b read scope")

    sys.addaudithook(hook)


def eligible_pool(intervals: pd.DataFrame, master: pd.DataFrame,
                  inventory_files: Iterable[Mapping[str, Any]]) -> pd.DataFrame:
    """One row per eligible permanent ID: resolved, with a side panel, and a member window overlapping a segment.

    This is the pool of ``m5_step4.unpriced_share`` (resolved and panel-backed) over each segment's
    [first reset, last book row] span; ``segments`` lists the segments the ID is eligible in.
    """

    panels: dict[str, set[str]] = {}
    for record in inventory_files:
        panels.setdefault(record["side"], set()).add(record["symbol"])
    resolved = intervals[intervals["resolution"] == "resolved"]
    if resolved["permanent_id"].duplicated().any():
        raise refuse("registration_invalid", "more than one resolved interval for a permanent ID")
    rows_of = master[master["permanent_id"].isin(set(resolved["permanent_id"]))]
    merged = resolved.merge(rows_of[["permanent_id", "vendor_code", "vendor_name", "isin"]],
                            on=["permanent_id", "vendor_code"], how="left", validate="one_to_one")
    if merged["vendor_name"].isna().any():
        raise refuse("registration_invalid", "resolved interval without a security master row")
    rows = []
    for row in merged.to_dict(orient="records"):
        segments = [seg for seg, dates in step4.SEGMENT_DATES.items()
                    if row["permanent_id"] in panels.get(dates["side"], set()) and row["m_in"]
                    and row["m_in"] <= dates["last_book_row"]
                    and (not row["m_out"] or row["m_out"] > dates["first_reset"])]
        if segments:
            klass = row["exit_class"] if row["exit_class"] in step4.EXIT_CLASSES else step4.UNKNOWN
            rows.append({"permanent_id": row["permanent_id"], "vendor_code": row["vendor_code"],
                         "vendor_name": row["vendor_name"], "isin": row["isin"], "m_in": row["m_in"],
                         "m_out": row["m_out"], "exit_class": klass, "segments": ";".join(segments)})
    return pd.DataFrame(rows).sort_values("permanent_id").reset_index(drop=True)


def securities(pool: pd.DataFrame) -> list[ident.Security]:
    return [ident.Security(r["permanent_id"], r["vendor_code"], r["vendor_name"], r["m_in"], r["m_out"])
            for r in pool.to_dict(orient="records")]


# SEC retrieval ------------------------------------------------------------------------------

def fetch_index(client: SecClient) -> tuple[ident.SecIndex, list[SecFile]]:
    files = [client.get(COMPANY_TICKERS_URL, "company_tickers.json"),
             client.get(COMPANY_TICKERS_EXCHANGE_URL, "company_tickers_exchange.json"),
             client.get(CIK_LOOKUP_URL, "cik-lookup-data.txt")]
    tickers, exchange, lookup = (f.read_bytes(client.cache_dir) for f in files)
    return ident.build_index(json.loads(tickers), json.loads(exchange), lookup.decode("latin-1")), files


def fetch_submissions(client: SecClient, ciks: Iterable[int]
                      ) -> tuple[dict[int, ident.Filer | None], dict[int, dict[str, Any]], list[SecFile]]:
    """Each CIK's submissions and every history page it lists; a 404 is a typed absence (``None``)."""

    filers: dict[int, ident.Filer | None] = {}
    names: dict[int, dict[str, Any]] = {}
    files: list[SecFile] = []
    for cik in sorted(set(ciks)):
        main_file = client.get(SUBMISSIONS_TEMPLATE.format(cik=cik), f"submissions/CIK{cik:010d}.json",
                               allow_absent=True)
        files.append(main_file)
        if main_file.status == 404:
            filers[cik] = None
            continue
        main = json.loads(main_file.read_bytes(client.cache_dir))
        pages = []
        for entry in main["filings"].get("files", []):
            name = entry["name"]
            if not PAGE_NAME.fullmatch(name) or not name.startswith(f"CIK{cik:010d}-"):
                raise SecRefusal("submissions history page with an unexpected name")
            page = client.get(SUBMISSIONS_URL.format(name=name), f"submissions/{name}")
            files.append(page)
            pages.append(json.loads(page.read_bytes(client.cache_dir)))
        filers[cik] = ident.filer_from_submissions(main, pages)
        names[cik] = {"name": main.get("name", ""), "formerNames": main.get("formerNames", [])}
    return filers, names, files


def fetch_companyfacts(client: SecClient, ciks: Iterable[int]) -> dict[int, SecFile]:
    return {cik: client.get(COMPANYFACTS_URL.format(cik=cik), f"companyfacts/CIK{cik:010d}.json",
                            allow_absent=True) for cik in sorted(set(ciks))}


def annual_fact_in_window(payload: bytes, m_in: str, m_out: str) -> bool:
    """Whether any us-gaap fact from a 10-K or 10-KT was filed inside [m_in, m_out)."""

    end = m_out or ident.OPEN_END
    for concept in json.loads(payload).get("facts", {}).get("us-gaap", {}).values():
        for values in concept.get("units", {}).values():
            if any(v.get("form") in ANNUAL_FACT_FORMS and m_in <= v.get("filed", "") < end for v in values):
                return True
    return False


# Coverage -----------------------------------------------------------------------------------

def _count(rows: Iterable[tuple[str, str]], columns: tuple[str, ...]) -> dict[str, dict[str, int]]:
    table: dict[str, Counter[str]] = {}
    for key, value in rows:
        table.setdefault(key, Counter())[value] += 1
    return {key: {c: int(table[key].get(c, 0)) for c in columns} for key in sorted(table)}


def mapping_coverage(pool: pd.DataFrame, outcomes: Mapping[str, ident.Outcome]) -> dict[str, Any]:
    status = {pid: o.status for pid, o in outcomes.items()}
    seg_rows = [(seg, status[r["permanent_id"]]) for r in pool.to_dict(orient="records")
                for seg in r["segments"].split(";")]
    exit_rows = [(r["exit_class"], status[r["permanent_id"]]) for r in pool.to_dict(orient="records")]
    seg_exit_rows = [(f"{seg} / {r['exit_class']}", status[r["permanent_id"]])
                     for r in pool.to_dict(orient="records") for seg in r["segments"].split(";")]
    shared = [o for o in outcomes.values() if o.status == ident.MULTI_CLASS]
    return {
        "eligible_ids": len(pool),
        "eligible_by_segment": dict(sorted(Counter(s for v in pool["segments"] for s in v.split(";")).items())),
        "by_status": {s: sum(o.status == s for o in outcomes.values()) for s in ident.STATUSES},
        "by_reason": dict(sorted(Counter(f"{o.status}: {o.reason}" for o in outcomes.values()).items())),
        "by_segment": _count(seg_rows, ident.STATUSES),
        "by_exit_class": _count(exit_rows, ident.STATUSES),
        "by_segment_and_exit_class": _count(seg_exit_rows, ident.STATUSES),
        "multi_class": {"ids": len(shared), "overlapping": sum(o.reason == "shared_cik_overlapping" for o in shared),
                        "disjoint": sum(o.reason == "shared_cik_disjoint" for o in shared)},
        "unique_ciks": len({o.cik for o in outcomes.values() if o.status == ident.UNIQUE}),
    }


def facts_coverage(pool: pd.DataFrame, outcomes: Mapping[str, ident.Outcome], facts: Mapping[int, SecFile],
                   cache_dir: Path) -> dict[str, Any]:
    """Company-facts availability for uniquely mapped IDs, by segment and later exit class."""

    columns = ("present_with_annual_fact_in_window", "present_no_annual_fact_in_window", "absent")
    rows = []
    for r in pool.to_dict(orient="records"):
        outcome = outcomes[r["permanent_id"]]
        if outcome.status != ident.UNIQUE:
            continue
        file = facts[outcome.cik]  # type: ignore[index]
        if file.status == 404:
            state = "absent"
        elif annual_fact_in_window(file.read_bytes(cache_dir), r["m_in"], r["m_out"]):
            state = columns[0]
        else:
            state = columns[1]
        rows.append((r, state))
    ended = [(("ended" if r["exit_class"] in ENDED else "not_ended"), s) for r, s in rows]
    return {
        "mapped_ids": len(rows),
        "by_state": {c: sum(s == c for _, s in rows) for c in columns},
        "by_segment": _count([(seg, s) for r, s in rows for seg in r["segments"].split(";")], columns),
        "by_exit_class": _count([(r["exit_class"], s) for r, s in rows], columns),
        "ended_vs_not": _count(ended, columns),
    }


def identifier_checks(pool: pd.DataFrame, outcomes: Mapping[str, ident.Outcome],
                      names: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    """Whether ``vendor_name`` and ``isin`` behave as current or point-in-time values (design note 9.8).

    Names: for uniquely mapped IDs whose CIK changed its SEC name inside the member window, does the vendor name
    equal the current SEC name or only an earlier one? ISIN: one undated value per ID; count ISINs shared across
    IDs, including reused vendor codes (``_old``) that share the ISIN or name of the ID now holding the ticker.
    """

    renamed = equals_current = equals_former_only = 0
    for r in pool.to_dict(orient="records"):
        outcome = outcomes[r["permanent_id"]]
        if outcome.status != ident.UNIQUE:
            continue
        info = names[outcome.cik]  # type: ignore[index]
        end = r["m_out"] or ident.OPEN_END
        changes = [x for x in info["formerNames"] if r["m_in"] <= str(x.get("to", ""))[:10] < end]
        if not changes:
            continue
        renamed += 1
        vendor = ident.norm(r["vendor_name"])
        if vendor == ident.norm(info["name"]):
            equals_current += 1
        elif vendor in {ident.norm(x.get("name", "")) for x in info["formerNames"]}:
            equals_former_only += 1
    isin = pool["isin"].fillna("")
    filled = pool[isin != ""]
    shared_isin = int(filled["isin"].duplicated(keep=False).sum())
    ticker = pool["vendor_code"].map(ident.ticker_of)
    reused = pool[pool["vendor_code"].str.contains("_old", regex=False)]
    reuse_same_isin = reuse_same_name = reuse_pairs = 0
    for r in reused.to_dict(orient="records"):
        holders = pool[(ticker == ident.ticker_of(r["vendor_code"])) & (pool["permanent_id"] != r["permanent_id"])]
        for h in holders.to_dict(orient="records"):
            reuse_pairs += 1
            reuse_same_isin += bool(r["isin"]) and r["isin"] == h["isin"]
            reuse_same_name += ident.norm(r["vendor_name"]) == ident.norm(h["vendor_name"])
    return {
        "renamed_in_window_mapped_ids": renamed, "vendor_name_equals_current_sec_name": equals_current,
        "vendor_name_equals_only_former_sec_name": equals_former_only,
        "isin_blank": int((isin == "").sum()), "isin_non_us": int(((isin != "") & ~isin.str.startswith("US")).sum()),
        "ids_sharing_isin": shared_isin, "reused_code_pairs_in_pool": reuse_pairs,
        "reused_pairs_same_isin": int(reuse_same_isin), "reused_pairs_same_name": int(reuse_same_name),
    }


# Local map, hash list, and manifest ---------------------------------------------------------

def map_bytes(pool: pd.DataFrame, outcomes: Mapping[str, ident.Outcome]) -> bytes:
    frame = pool[["permanent_id", "vendor_code", "segments", "exit_class"]].copy()
    frame["status"] = frame["permanent_id"].map(lambda p: outcomes[p].status)
    frame["reason"] = frame["permanent_id"].map(lambda p: outcomes[p].reason)
    frame["cik"] = frame["permanent_id"].map(lambda p: "" if outcomes[p].cik is None else f"{outcomes[p].cik:010d}")
    buffer = io.StringIO()
    frame[MAP_COLUMNS].sort_values("permanent_id").to_csv(buffer, index=False, lineterminator="\n")
    return buffer.getvalue().encode("utf-8")


def hash_list_bytes(files: Iterable[SecFile]) -> bytes:
    lines = sorted({f"{f.relative}\t{f.status}\t{f.sha256 or '-'}\t{f.n_bytes}\n" for f in files})
    return ("relative_path\tstatus\tsha256\tbytes\n" + "".join(lines)).encode("utf-8")


def _source(source_id: str, template: str, files: list[SecFile]) -> dict[str, Any]:
    present = [f for f in files if f.status == 200]
    dates = sorted(f.retrieved_utc for f in files)
    return {"id": source_id, "url_template": template, "files": len(present),
            "recorded_absent_404": len(files) - len(present), "bytes": sum(f.n_bytes for f in present),
            "retrieved_utc_first": dates[0] if dates else None, "retrieved_utc_last": dates[-1] if dates else None}


def build_manifest(index_files: list[SecFile], submissions: list[SecFile], facts: list[SecFile],
                   hash_list: bytes, cik_map: bytes, git: Mapping[str, Any], map_rows: int) -> dict[str, Any]:
    ids = ("company_tickers", "company_tickers_exchange", "cik_lookup_data")
    mains = [f for f in submissions if not PAGE_NAME.fullmatch(Path(f.relative).name)]
    pages = [f for f in submissions if PAGE_NAME.fullmatch(Path(f.relative).name)]
    return {
        "schema_version": "m5_step4b_sec_manifest_v1",
        "evidence_ceiling": "DIAGNOSTIC_ONLY",
        "code_commit": git["commit"], "tracked_changes": git["tracked_changes"],
        "snapshot": {"id": step4.SNAPSHOT_ID, "amendment_4_sha256": step4.AMENDMENT_4_SHA256},
        "cache_dir": "data/public_cache/sec/ (gitignored; raw SEC files are never committed)",
        "user_agent": "owner-provided contact read from EFR_SEC_USER_AGENT; never recorded",
        "rate_limit": "at most 4 requests a second; retry with backoff on HTTP 429 and 5xx",
        "sources": [
            *[{"id": i, "url": f.url, "retrieved_utc": f.retrieved_utc, "sha256": f.sha256, "bytes": f.n_bytes}
              for i, f in zip(ids, index_files)],
            _source("submissions", SUBMISSIONS_TEMPLATE, mains),
            _source("submissions_history_pages", PAGE_TEMPLATE, pages),
            _source("companyfacts", COMPANYFACTS_URL, facts),
        ],
        "file_hash_list": {"files": hash_list.count(b"\n") - 1, "sha256": hashlib.sha256(hash_list).hexdigest(),
                           "format": "tab-separated relative_path, status, sha256, bytes; one header line; "
                                     "rows sorted; kept local because paths name CIKs"},
        "cik_map": {"sha256": hashlib.sha256(cik_map).hexdigest(), "rows": map_rows, "columns": MAP_COLUMNS,
                    "location": "local only, beside the snapshot (never in a repository checkout)"},
    }


# Report -------------------------------------------------------------------------------------

def _table(title: str, table: Mapping[str, Mapping[str, int]], columns: tuple[str, ...]) -> list[str]:
    lines = [f"| {title} | " + " | ".join(columns) + " | total |", "|---" * (len(columns) + 2) + "|"]
    for key, row in table.items():
        lines.append(f"| {key} | " + " | ".join(str(row[c]) for c in columns) + f" | {sum(row.values())} |")
    return lines + [""]


def render_report(doc: Mapping[str, Any]) -> str:
    m, f, ids, man = doc["mapping"], doc["facts"], doc["identifiers"], doc["manifest"]
    fcols = ("present_with_annual_fact_in_window", "present_no_annual_fact_in_window", "absent")
    by_id = m["by_status"]
    lines = [
        "# Milestone 5 Step 4b SEC Data Build: CIK Map and Company-Facts Coverage", "",
        "Evidence ceiling `DIAGNOSTIC_ONLY`. Identity and schema coverage only: no signal, sleeve, return, or rule "
        "result was computed. Counts are aggregates; the CIK map and per-file hashes stay local (R11, O-10).", "",
        f"**Conclusion.** Rule F maps {by_id['unique']} of {m['eligible_ids']} eligible permanent IDs to one CIK "
        f"({by_id['unique'] / m['eligible_ids']:.1%}); {by_id['ambiguous']} are ambiguous, {by_id['unmapped']} "
        f"unmapped, and {by_id['multi_class']} multi-class, all typed missing. Company facts exist for "
        f"{f['mapped_ids'] - f['by_state']['absent']} of {f['mapped_ids']} mapped IDs.", "",
        "## Provenance", "",
        f"- Code commit `{man['code_commit']}`; snapshot `{man['snapshot']['id']}` bound to amendment 4 "
        f"(`{man['snapshot']['amendment_4_sha256']}`).",
        "- Sources: SEC `company_tickers.json`, `company_tickers_exchange.json`, `cik-lookup-data.txt`, submissions "
        "with history pages, and XBRL companyfacts, through `src/data/sec_edgar.py` only.",
        f"- Manifest `{MANIFEST_JSON}`: {man['file_hash_list']['files']} cached files, hash-list SHA-256 "
        f"`{man['file_hash_list']['sha256']}`, CIK-map SHA-256 `{man['cik_map']['sha256']}`.", "",
        "| Source | Files | Recorded 404 | Bytes |", "|---|---|---|---|",
    ]
    for s in man["sources"]:
        if "url_template" in s:
            lines.append(f"| {s['id']} | {s['files']} | {s['recorded_absent_404']} | {s['bytes']} |")
        else:
            lines.append(f"| {s['id']} | 1 | 0 | {s['bytes']} |")
    lines += [
        "", "## Eligible pool", "",
        f"- {m['eligible_ids']} permanent IDs: resolved, with a side panel, and a member window overlapping the "
        f"segment (by segment: {', '.join(f'{k} {v}' for k, v in m['eligible_by_segment'].items())}).", "",
        "## Mapping outcome (rule F, fail-closed)", "",
        "Per permanent ID:", "",
        "| unique | ambiguous | unmapped | multi_class |", "|---|---|---|---|",
        f"| {by_id['unique']} | {by_id['ambiguous']} | {by_id['unmapped']} | {by_id['multi_class']} |", "",
        "By segment (one row per ID and segment):", "",
        *_table("segment", m["by_segment"], ident.STATUSES),
        "By later exit class (per ID):", "",
        *_table("exit class", m["by_exit_class"], ident.STATUSES),
        "By segment and later exit class:", "",
        *_table("segment / exit class", m["by_segment_and_exit_class"], ident.STATUSES),
        "Reasons (per ID):", "", "| status: reason | IDs |", "|---|---|",
        *[f"| {k} | {v} |" for k, v in m["by_reason"].items()], "",
        f"Multi-class: {m['multi_class']['ids']} IDs share an accepted CIK "
        f"({m['multi_class']['overlapping']} with overlapping member windows, {m['multi_class']['disjoint']} "
        f"disjoint); {m['unique_ciks']} distinct CIKs are uniquely mapped.", "",
        "## Company facts for mapped IDs", "",
        "An annual fact is a us-gaap fact from a 10-K or 10-KT filed inside the ID's member window. A 404 is "
        "recorded as a typed absence.", "",
        *_table("segment", f["by_segment"], fcols),
        *_table("exit class", f["by_exit_class"], fcols),
        *_table("ended filers", f["ended_vs_not"], fcols),
        "## vendor_name and isin: current or point-in-time", "",
        f"- Mapped IDs whose CIK changed its SEC name inside the member window: {ids['renamed_in_window_mapped_ids']}. "
        f"The vendor name equals the current SEC name for {ids['vendor_name_equals_current_sec_name']} and only a "
        f"former SEC name for {ids['vendor_name_equals_only_former_sec_name']}.",
        f"- ISIN is one undated value per permanent ID: blank {ids['isin_blank']}, non-US prefix {ids['isin_non_us']}, "
        f"IDs sharing an ISIN with another eligible ID {ids['ids_sharing_isin']}.",
        f"- Reused vendor codes (`_old`) paired with the ID now holding the ticker: {ids['reused_code_pairs_in_pool']} "
        f"pairs; same ISIN {ids['reused_pairs_same_isin']}, same normalized name {ids['reused_pairs_same_name']}.",
        f"- Reading: {doc['identifier_reading']}", "",
        "## Limitations", "",
        "- Not uniquely mapped, by later exit class: " + "; ".join(
            f"{k} {sum(v.values()) - v['unique']} of {sum(v.values())}" for k, v in m["by_exit_class"].items())
        + ". Where the not-mapped share differs by exit class, the mapped sample is tilted; step 4b's "
        "coverage-tilt guard addresses this, and this build makes no claim.",
        "- SEC's ticker files are current, not point-in-time; rule F uses them only as candidates and requires a "
        "name match and a periodic filing inside the member window.",
        "- Multi-class and foreign-form IDs are typed missing, not repaired; there is no hand override list.", "",
    ]
    return "\n".join(lines)


def identifier_reading(ids: Mapping[str, Any]) -> str:
    if ids["renamed_in_window_mapped_ids"] and ids["vendor_name_equals_current_sec_name"] > \
            ids["vendor_name_equals_only_former_sec_name"]:
        name = (f"vendor_name behaves mostly as a current (latest) value, not a point-in-time one "
                f"({ids['vendor_name_equals_current_sec_name']} of {ids['renamed_in_window_mapped_ids']} renamed IDs)")
    elif ids["renamed_in_window_mapped_ids"]:
        name = "vendor_name often carries an earlier name, so it is not reliably current"
    else:
        name = "no in-window rename was observed, so vendor_name's timing is untested"
    return (f"{name}; isin has one undated value per ID, so it cannot be point-in-time. Neither field enters "
            "a signal; rule F uses vendor_name only with an in-window filing check.")


# Run ----------------------------------------------------------------------------------------

def bind(snapshot_dir: Path, repo_root: Path) -> dict[str, Any]:
    if hashlib.sha256((repo_root / step4.AMENDMENT_4_PATH).read_bytes()).hexdigest() != step4.AMENDMENT_4_SHA256:
        raise refuse("trial_file_changed", step4.AMENDMENT_4_PATH)
    return step4.bind_step4(snapshot_dir)


def private_dir_for(snapshot_dir: Path, repo_root: Path) -> Path:
    target = Path(snapshot_dir).resolve().parent / PRIVATE_DIRNAME
    if target.is_relative_to(Path(repo_root).resolve()) or (target / ".git").exists():
        raise refuse("private_output_in_checkout", "the local map must stay outside every repository checkout")
    return target


def collect(pool: pd.DataFrame, client: SecClient) -> dict[str, Any]:
    """Every SEC read and the map, from an eligible pool. Returns outcomes, files, and coverage."""

    index, index_files = fetch_index(client)
    secs = securities(pool)
    cands = {s.permanent_id: ident.candidates(s, index) for s in secs}
    filers, names, submissions = fetch_submissions(client, (c for v in cands.values() for c in v.pool))
    outcomes = ident.map_securities(secs, index, filers)
    facts = fetch_companyfacts(client, (o.cik for o in outcomes.values() if o.status == ident.UNIQUE))
    identifiers = identifier_checks(pool, outcomes, names)
    return {"outcomes": outcomes, "index_files": index_files, "submissions": submissions, "facts": facts,
            "candidate_ciks": len(filers), "mapping": mapping_coverage(pool, outcomes),
            "facts_coverage": facts_coverage(pool, outcomes, facts, client.cache_dir), "identifiers": identifiers}


def run(repo_root: Path, snapshot_dir: Path, git: Mapping[str, Any], *, offline: bool) -> dict[str, Any]:
    bound = bind(snapshot_dir, repo_root)
    root = bound["snapshot"].root
    pool = eligible_pool(pd.read_csv(root / INTERVAL_RESULTS, dtype=str, keep_default_na=False),
                         pd.read_csv(root / SECURITY_MASTER, dtype=str, keep_default_na=False),
                         bound["inventory"]["files"])
    private = private_dir_for(snapshot_dir, repo_root)
    client = SecClient(repo_root / CACHE_DIR, offline=offline)
    got = collect(pool, client)
    step4.verify_pins_unchanged(snapshot_dir)
    facts = list(got["facts"].values())
    cik_map = map_bytes(pool, got["outcomes"])
    hash_list = hash_list_bytes([*got["index_files"], *got["submissions"], *facts])
    manifest = build_manifest(got["index_files"], got["submissions"], facts, hash_list, cik_map, git, len(pool))
    summary = {"requests": client.requests, "retries": client.retries, "candidate_ciks": got["candidate_ciks"],
               "eligible_ids": len(pool), "by_status": got["mapping"]["by_status"],
               "cik_map_sha256": manifest["cik_map"]["sha256"], "hash_list_sha256": manifest["file_hash_list"]["sha256"]}
    if offline:
        committed = json.loads((repo_root / MANIFEST_JSON).read_text(encoding="utf-8"))
        for key, part in (("cik_map", "sha256"), ("file_hash_list", "sha256")):
            if committed[key][part] != manifest[key][part]:
                raise refuse("offline_reproduction_mismatch", key)
        return {**summary, "reproduced": True}
    private.mkdir(parents=True, exist_ok=True)
    (private / MAP_FILE).write_bytes(cik_map)
    (private / HASH_LIST_FILE).write_bytes(hash_list)
    (repo_root / MANIFEST_JSON).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    doc = {"mapping": got["mapping"], "facts": got["facts_coverage"], "identifiers": got["identifiers"],
           "identifier_reading": identifier_reading(got["identifiers"]), "manifest": manifest}
    (repo_root / REPORT_MD).write_text(render_report(doc), encoding="utf-8")
    outputs = {p: hashlib.sha256((repo_root / p).read_bytes()).hexdigest() for p in (MANIFEST_JSON, REPORT_MD)}
    return {**summary, "outputs": outputs}


def _append_attempt(repo_root: Path, record: dict[str, Any]) -> None:
    path = repo_root / ATTEMPTS_JSONL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--snapshot-dir", required=True, help="the real_v2 snapshot directory (never recorded)")
    parser.add_argument("--reason", required=True, help="why this attempt runs")
    parser.add_argument("--offline", action="store_true", help="read only the cache and check the committed manifest")
    args = parser.parse_args(argv)
    user_agent()
    attempt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    git = base.git_state(REPO_ROOT)
    _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "start", "reason": args.reason,
                                "mode": "offline" if args.offline else "online", "snapshot_id": step4.SNAPSHOT_ID,
                                "amendment_4_sha256": step4.AMENDMENT_4_SHA256, **git})
    started = time.perf_counter()
    guard_snapshot(Path(args.snapshot_dir))
    try:
        summary = run(REPO_ROOT, Path(args.snapshot_dir), git, offline=args.offline)
    except Exception as error:
        _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "end", "status": "refused",
                                    "reason": getattr(error, "reason", type(error).__name__),
                                    "seconds": round(time.perf_counter() - started, 1)})
        raise
    _append_attempt(REPO_ROOT, {"attempt": attempt, "event": "end", "status": "completed", **summary,
                                "seconds": round(time.perf_counter() - started, 1)})
    print(f"eligible {summary['eligible_ids']}; {summary['by_status']}; requests {summary['requests']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
