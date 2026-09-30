"""Milestone 5 step 4b: fail-closed rule F (R3) and the SEC data-build driver, on synthetic fixtures only.

No test reads a snapshot row or opens a network connection: SEC responses come
from a fake opener over synthetic JSON.
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Mapping

import pandas as pd
import pytest

import data.sec_edgar as sec
import research.m5_sec_identity as ident
import research.m5_step4b_data as drv
from research.m5_sec_identity import Filer, Security

REPO = Path(__file__).resolve().parents[1]


def filer(names: tuple[str, ...], filings: tuple[tuple[str, str], ...], tickers: tuple[str, ...] = ()) -> Filer:
    return Filer(frozenset(ident.norm(n) for n in names), frozenset(tickers), filings)


def sec_index(tickers: dict[str, set[int]], names: dict[str, set[int]]) -> ident.SecIndex:
    return ident.SecIndex({k: frozenset(v) for k, v in tickers.items()},
                          {ident.norm(k): frozenset(v) for k, v in names.items()})


SEC_A = Security("P1", "ABC.US", "Alpha Beta Corp", "2015-01-02", "")
IN_WINDOW = (("10-K", "2016-02-20"), ("10-Q", "2016-05-01"))


def outcome(security: Security, index: ident.SecIndex, filers: Mapping[int, Filer | None]) -> ident.Outcome:
    return ident.map_securities([security], index, filers)[security.permanent_id]


# Normalization -----------------------------------------------------------------------------

def test_name_and_ticker_normalization() -> None:
    assert ident.norm("Alpha & Beta Holdings, Inc. /DE/") == ident.norm("ALPHA AND BETA INC") == "ALPHA AND BETA"
    assert ident.ticker_of("brk-b.US") == "BRK-B"
    assert ident.ticker_of("ABC_old2.US") == "ABC"


def test_build_index_reads_both_ticker_files_and_the_name_list() -> None:
    index = ident.build_index({"0": {"cik_str": 11, "ticker": "abc", "title": "x"}},
                              {"fields": ["cik", "name", "ticker", "exchange"], "data": [[12, "y", "ABC", "NYSE"]]},
                              "ALPHA BETA CORP:0000000011:\nFORMER ALPHA INC:0000000011:\n:0000000099:\n")
    assert index.by_ticker["ABC"] == {11, 12}
    assert index.by_name["ALPHA BETA"] == {11} and index.by_name["FORMER ALPHA"] == {11}
    assert "" not in index.by_name


def test_filer_reads_recent_block_history_pages_and_former_names() -> None:
    main = {"name": "Alpha Beta Corp", "formerNames": [{"name": "Old Alpha Inc", "from": "x", "to": "y"}],
            "tickers": ["abc"], "filings": {"recent": {"form": ["10-K"], "filingDate": ["2020-02-01"]}}}
    got = ident.filer_from_submissions(main, [{"form": ["10-Q"], "filingDate": ["2012-05-01"]}])
    assert got.names == {"ALPHA BETA", "OLD ALPHA"} and got.tickers == {"ABC"}
    assert got.filings == (("10-K", "2020-02-01"), ("10-Q", "2012-05-01"))
    with pytest.raises(ValueError, match="unequal"):
        ident.filer_from_submissions(main, [{"form": ["10-Q"], "filingDate": []}])


# Rule F ------------------------------------------------------------------------------------

def test_rule_f_accepts_only_a_unique_cik() -> None:
    index = sec_index({"ABC": {1}}, {"Alpha Beta Corp": {1}})
    got = outcome(SEC_A, index, {1: filer(("Alpha Beta Corp",), IN_WINDOW)})
    assert got == ident.Outcome(ident.UNIQUE, 1, "accepted")
    name_only = sec_index({}, {"Alpha Beta Corp": {1}})
    assert outcome(SEC_A, name_only, {1: filer(("Alpha Beta Corp",), IN_WINDOW)}).cik == 1


def test_several_survivors_are_ambiguous_unless_the_ticker_tie_break_leaves_one() -> None:
    names = sec_index({}, {"Alpha Beta Corp": {1, 2}})
    both = {1: filer(("Alpha Beta Corp",), IN_WINDOW), 2: filer(("Alpha Beta Corp",), IN_WINDOW)}
    assert outcome(SEC_A, names, both) == ident.Outcome(ident.AMBIGUOUS, None, "several_survivors")
    tickered = {1: filer(("Alpha Beta Corp",), IN_WINDOW, ("ABC",)), 2: filer(("Alpha Beta Corp",), IN_WINDOW, ("ABC",))}
    assert outcome(SEC_A, names, tickered).status == ident.AMBIGUOUS
    one = {1: filer(("Alpha Beta Corp",), IN_WINDOW), 2: filer(("Alpha Beta Corp",), IN_WINDOW, ("ABC",))}
    assert outcome(SEC_A, names, one) == ident.Outcome(ident.UNIQUE, 2, "accepted")


def test_unique_ticker_cik_that_disagrees_fails_closed() -> None:
    index = sec_index({"ABC": {2}}, {"Alpha Beta Corp": {1}})
    filers = {1: filer(("Alpha Beta Corp",), IN_WINDOW), 2: filer(("Other Co",), IN_WINDOW, ("ABC",))}
    assert outcome(SEC_A, index, filers) == ident.Outcome(ident.AMBIGUOUS, None, "ticker_cik_disagrees")


def test_ticker_reuse_never_maps_to_the_current_holder() -> None:
    old = Security("P0", "ABC_old.US", "Gamma Delta Inc", "2014-06-02", "2017-03-01")
    new_holder = {2: filer(("Alpha Beta Corp",), IN_WINDOW, ("ABC",))}
    ticker_only = sec_index({"ABC": {2}}, {"Alpha Beta Corp": {2}})
    assert outcome(old, ticker_only, new_holder) == ident.Outcome(ident.UNMAPPED, None, "name_mismatch")
    with_name = sec_index({"ABC": {2}}, {"Gamma Delta Inc": {1}})
    filers = {**new_holder, 1: filer(("Gamma Delta Inc",), (("10-K", "2015-03-01"),))}
    assert outcome(old, with_name, filers) == ident.Outcome(ident.AMBIGUOUS, None, "ticker_cik_disagrees")


def test_a_filing_outside_the_member_window_fails_closed() -> None:
    index = sec_index({"ABC": {1}}, {"Alpha Beta Corp": {1}})
    closed = Security("P1", "ABC.US", "Alpha Beta Corp", "2015-01-02", "2016-01-04")
    for filings in ((("10-K", "2014-12-31"),), (("10-K", "2016-01-04"),), (("8-K", "2015-06-01"),),
                    (("20-F", "2015-06-01"),)):
        got = outcome(closed, index, {1: filer(("Alpha Beta Corp",), filings)})
        assert got == ident.Outcome(ident.UNMAPPED, None, "no_periodic_filing_in_window"), filings
    assert outcome(closed, index, {1: filer(("Alpha Beta Corp",), (("10-Q", "2015-01-02"),))}).status == ident.UNIQUE
    assert outcome(closed, index, {1: filer(("Alpha Beta Corp",), (("10-K/A", "2016-01-03"),))}).status == ident.UNIQUE


def test_foreign_form_filer_and_missing_submissions_are_not_accepted() -> None:
    index = sec_index({"ABC": {1}}, {"Alpha Beta Corp": {1}})
    mixed = filer(("Alpha Beta Corp",), (("10-Q", "2016-05-01"), ("20-F", "2017-04-01")))
    assert outcome(SEC_A, index, {1: mixed}) == ident.Outcome(ident.UNMAPPED, None, "foreign_form_in_window")
    assert outcome(SEC_A, index, {1: None}) == ident.Outcome(ident.UNMAPPED, None, "name_mismatch")
    assert outcome(SEC_A, sec_index({}, {}), {}) == ident.Outcome(ident.UNMAPPED, None, "no_candidate")


def test_a_cik_shared_by_two_ids_types_both_multi_class() -> None:
    index = sec_index({"ABC": {1}, "ABCK": {1}}, {"Alpha Beta Corp": {1}})
    filers = {1: filer(("Alpha Beta Corp",), IN_WINDOW, ("ABC", "ABCK"))}
    second = Security("P2", "ABCK.US", "Alpha Beta Corp", "2015-06-01", "")
    got = ident.map_securities([SEC_A, second], index, filers)
    assert {o.status for o in got.values()} == {ident.MULTI_CLASS}
    assert {o.reason for o in got.values()} == {"shared_cik_overlapping"} and all(o.cik is None for o in got.values())
    early = Security("P3", "ABCK.US", "Alpha Beta Corp", "2014-01-02", "2015-01-02")
    disjoint = ident.map_securities([SEC_A, early], index, {1: filer(("Alpha Beta Corp",), IN_WINDOW + (
        ("10-K", "2014-03-01"),), ("ABC", "ABCK"))})
    assert {o.reason for o in disjoint.values()} == {"shared_cik_disjoint"}


# Driver ------------------------------------------------------------------------------------

def test_eligible_pool_needs_resolution_a_side_panel_and_window_overlap() -> None:
    intervals = pd.DataFrame([
        {"permanent_id": "P1", "vendor_code": "AAA.US", "resolution": "resolved", "m_in": "2010-01-04", "m_out": "",
         "exit_class": "index_removal_still_trading"},
        {"permanent_id": "P2", "vendor_code": "BBB.US", "resolution": "resolved", "m_in": "2010-01-04",
         "m_out": "2014-04-30", "exit_class": "delisting_candidate"},
        {"permanent_id": "P3", "vendor_code": "CCC.US", "resolution": "resolved", "m_in": "2019-06-28",
         "m_out": "2019-09-03", "exit_class": "disappearance_outside_membership"},
        {"permanent_id": "", "vendor_code": "DDD.US", "resolution": "ambiguous_reuse_discontinuity", "m_in": "2015-01-02",
         "m_out": "", "exit_class": ""},
        {"permanent_id": "P5", "vendor_code": "EEE.US", "resolution": "resolved", "m_in": "2015-01-02", "m_out": "",
         "exit_class": "index_removal_still_trading"},
    ])
    master = pd.DataFrame([{"permanent_id": p, "vendor_code": c, "vendor_name": f"{c} Corp", "isin": ""}
                           for p, c in zip(intervals["permanent_id"], intervals["vendor_code"])])
    inventory = [{"side": "discovery_pre", "symbol": p} for p in ("P1", "P2", "P3")] + [
        {"side": "discovery_post", "symbol": "P1"}]
    pool = drv.eligible_pool(intervals, master, inventory)
    assert pool[["permanent_id", "segments"]].values.tolist() == [["P1", "pre;post"], ["P3", "pre"]]


SEC_FIXTURE = {
    "tickers": {"0": {"cik_str": 11, "ticker": "AAA", "title": "Alpha"}, "1": {"cik_str": 12, "ticker": "BBB",
                                                                               "title": "Beta"}},
    "names": "ALPHA INC:0000000011:\nBETA CORP:0000000012:\nBETA CORP:0000000013:\nGAMMA LTD:0000000014:\n",
}


def _subs(name: str, filings: list[tuple[str, str]], tickers: list[str]) -> dict:
    return {"name": name, "formerNames": [], "tickers": tickers, "filings": {
        "recent": {"form": [f for f, _ in filings], "filingDate": [d for _, d in filings]}, "files": []}}


def fake_sec() -> tuple[dict[str, object], pd.DataFrame]:
    subs = {11: _subs("Alpha Inc", [("10-K", "2016-02-01")], ["AAA"]),
            12: _subs("Beta Corp", [("10-K", "2016-02-01")], ["BBB"]),
            13: _subs("Beta Corp", [("10-K", "2009-02-01")], []),
            14: _subs("Gamma Ltd", [("20-F", "2016-02-01")], [])}
    subs[11]["filings"]["files"] = [{"name": "CIK0000000011-submissions-001.json"}]
    facts = {11: {"facts": {"us-gaap": {"Assets": {"units": {"USD": [{"form": "10-K", "filed": "2016-02-01"}]}}}}}}
    script: dict[str, object] = {
        sec.COMPANY_TICKERS_URL: json.dumps(SEC_FIXTURE["tickers"]).encode(),
        sec.COMPANY_TICKERS_EXCHANGE_URL: json.dumps({"fields": ["cik", "name", "ticker", "exchange"],
                                                      "data": []}).encode(),
        sec.CIK_LOOKUP_URL: SEC_FIXTURE["names"].encode("latin-1"),
        sec.SUBMISSIONS_URL.format(name="CIK0000000011-submissions-001.json"):
            json.dumps({"form": ["10-Q"], "filingDate": ["2012-01-01"]}).encode(),
    }
    for cik, body in subs.items():
        script[sec.SUBMISSIONS_URL.format(name=f"CIK{cik:010d}.json")] = json.dumps(body).encode()
    for cik in (11, 12):
        script[sec.COMPANYFACTS_URL.format(cik=cik)] = json.dumps(facts[cik]).encode() if cik in facts else 404
    pool = pd.DataFrame([
        {"permanent_id": "P1", "vendor_code": "AAA.US", "vendor_name": "Alpha Inc", "isin": "US0000000001",
         "m_in": "2015-01-02", "m_out": "", "exit_class": "index_removal_still_trading", "segments": "pre;post"},
        {"permanent_id": "P2", "vendor_code": "BBB.US", "vendor_name": "Beta Corp", "isin": "US0000000002",
         "m_in": "2015-01-02", "m_out": "2017-01-03", "exit_class": "delisting_candidate", "segments": "pre"},
        {"permanent_id": "P3", "vendor_code": "GGG.US", "vendor_name": "Gamma Ltd", "isin": "",
         "m_in": "2015-01-02", "m_out": "", "exit_class": "index_removal_still_trading", "segments": "post"},
    ])
    return script, pool


def _run_collect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, offline: bool = False):
    from test_sec_edgar import FakeClock, FakeOpener

    monkeypatch.setenv(sec.USER_AGENT_ENV, "Sentinel Research sentinel.probe@example.org")
    script, pool = fake_sec()
    clock = FakeClock()
    opener = FakeOpener(script, clock)
    client = sec.SecClient(tmp_path / "cache", offline=offline, opener=opener, clock=clock, sleep=clock.sleep)
    return drv.collect(pool, client), pool, opener


def test_collect_maps_fetches_facts_for_unique_ciks_only_and_reproduces_offline(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    got, pool, opener = _run_collect(tmp_path, monkeypatch)
    status = {pid: o.status for pid, o in got["outcomes"].items()}
    assert status == {"P1": "unique", "P2": "unique", "P3": "unmapped"}
    assert got["outcomes"]["P3"].reason == "no_periodic_filing_in_window"
    assert sorted(got["facts"]) == [11, 12] and got["facts"][12].status == 404
    assert got["facts_coverage"]["by_state"] == {"present_with_annual_fact_in_window": 1,
                                                 "present_no_annual_fact_in_window": 0, "absent": 1}
    assert got["mapping"]["by_segment"]["pre"] == {"unique": 2, "unmapped": 0, "ambiguous": 0, "multi_class": 0}
    first_map = drv.map_bytes(pool, got["outcomes"])
    first_hashes = drv.hash_list_bytes([*got["index_files"], *got["submissions"], *got["facts"].values()])
    assert b"0000000011" in first_map and b"AAA.US" in first_map  # the local map pairs codes with CIKs
    again, _, offline_opener = _run_collect(tmp_path, monkeypatch, offline=True)
    assert not offline_opener.calls
    assert drv.map_bytes(pool, again["outcomes"]) == first_map
    assert drv.hash_list_bytes([*again["index_files"], *again["submissions"], *again["facts"].values()]) == first_hashes


PRIVATE_PATTERNS = {
    "vendor code": re.compile(r"\b[A-Z][A-Z0-9-]{0,6}(?:_old\d*)?\.US\b"),
    "CIK": re.compile(r"CIK\d|\b\d{10}\b"),
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "private path": re.compile(r"/Users/|private_data|\\Users\\|/home/"),
    "permanent id": re.compile(r"#E\d+\b|\bP\d\b"),
}


def assert_r11_clean(text: str, extra: tuple[str, ...] = ()) -> None:
    for label, pattern in PRIVATE_PATTERNS.items():
        assert not pattern.search(text), f"{label} in a committed output"
    for token in extra:
        assert token not in text


def test_manifest_and_report_carry_no_cik_code_email_or_private_path(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    got, pool, _ = _run_collect(tmp_path, monkeypatch)
    facts = list(got["facts"].values())
    cik_map = drv.map_bytes(pool, got["outcomes"])
    hash_list = drv.hash_list_bytes([*got["index_files"], *got["submissions"], *facts])
    manifest = drv.build_manifest(got["index_files"], got["submissions"], facts, hash_list, cik_map,
                                  {"commit": "c" * 40, "tracked_changes": False}, len(pool))
    doc = {"mapping": got["mapping"], "facts": got["facts_coverage"], "identifiers": got["identifiers"],
           "identifier_reading": drv.identifier_reading(got["identifiers"]), "manifest": manifest}
    manifest_text, report = json.dumps(manifest), drv.render_report(doc)
    for text in (manifest_text, report):
        assert_r11_clean(text, ("Alpha", "Beta", "Gamma", "AAA", "BBB", "sentinel"))
    templates = [s.get("url_template", s.get("url")) for s in manifest["sources"]]
    assert all("{cik:010d}" in t for t in templates[3:]) and manifest["cik_map"]["rows"] == 3
    assert manifest["file_hash_list"]["files"] == len(facts) + len(got["submissions"]) + 3


def test_committed_step4b_outputs_pass_the_r11_scan() -> None:
    paths = [REPO / drv.MANIFEST_JSON, REPO / drv.REPORT_MD, REPO / drv.ATTEMPTS_JSONL]
    present = [p for p in paths if p.exists()]
    if not present:
        pytest.skip("step 4b data outputs are not committed yet")
    for path in present:
        assert_r11_clean(path.read_text(encoding="utf-8"))


def test_private_outputs_refuse_a_repository_checkout(tmp_path: Path) -> None:
    with pytest.raises(drv.step4.runner.RunnerStop, match="private_output_in_checkout"):
        drv.private_dir_for(REPO / "data" / "snap", REPO)
    assert drv.private_dir_for(tmp_path / "snap", REPO) == (tmp_path / drv.PRIVATE_DIRNAME).resolve()


def test_snapshot_guard_refuses_writes_and_terminal_or_quarantine_opens(tmp_path: Path) -> None:
    snap = tmp_path / "snap"
    for sub in ("identity", "terminal", "quarantine"):
        (snap / sub).mkdir(parents=True)
        (snap / sub / "f.txt").write_text("x")
    code = io.StringIO()
    code.write("import sys, os\nfrom pathlib import Path\nimport research.m5_step4b_data as d\n")
    code.write(f"s = Path({str(snap)!r})\nd.guard_snapshot(s)\n")
    code.write("assert (s / 'identity' / 'f.txt').read_text() == 'x'\nout = []\n")
    code.write("for p, m in (('terminal/f.txt', 'r'), ('quarantine/f.txt', 'rb'), ('identity/f.txt', 'a'), "
               "('identity/new.txt', 'w')):\n")
    code.write("    try:\n        open(s / p, m)\n        out.append('opened')\n")
    code.write("    except PermissionError:\n        out.append('refused')\n")
    code.write("print(','.join(out))\n")
    done = subprocess.run([sys.executable, "-c", code.getvalue()], capture_output=True, text=True,
                          env={"PYTHONPATH": f"{REPO / 'src'}:{REPO}"}, cwd=REPO, check=True)
    assert done.stdout.strip() == "refused,refused,refused,refused"
    assert not (snap / "identity" / "new.txt").exists()
