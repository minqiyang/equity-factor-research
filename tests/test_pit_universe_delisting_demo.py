"""Complete synthetic comparison, failure retention, and report reproduction."""

import json

import pandas as pd
import pytest

from research import pit_universe_delisting_demo as demo


def test_demo_complete_cases_and_repeated_append_only_attempts(tmp_path):
    path = tmp_path / "pit.md"
    result = demo.run_pit_universe_delisting_demo(report_path=path)
    assert len(result["cases"]) == 6
    assert [case["status"] for case in result["cases"]] == [
        "success",
        "success",
        "refused",
    ] * 2
    for case in result["cases"]:
        if case["status"] == "refused":
            assert case["reason"] == "incoming_price_invalid"
        else:
            assert len(case["path"]) == 12
            assert len(case["terminal_event_log"]) == 1
            for row in case["path"]:
                assert row["cash"] + row["equity"] * sum(
                    row["holdings"].values()
                ) == pytest.approx(row["equity"])
    text = path.read_text()
    assert text == demo.render_report(result)
    for token in (
        "DIAGNOSTIC_ONLY",
        "SEC_OLD",
        "SEC_NEW",
        "-60%",
        "incoming_price_invalid",
    ):
        assert token in text
    payload = json.loads(path.with_suffix(".json").read_text())
    assert len(payload["metrics"]["cases"]) == 6
    assert payload["diagnostics"]["membership"][1]["end_date"] is None
    attempt_path = path.with_name("pit_attempts.jsonl")
    original = attempt_path.read_bytes()
    events = [json.loads(line) for line in original.splitlines()]
    assert len(events) == 12
    assert all(record["command"] == demo.COMMAND for record in events)
    assert len({record["attempt_id"] for record in events}) == 6
    demo.run_pit_universe_delisting_demo(report_path=path)
    assert attempt_path.read_bytes().startswith(original)
    assert len(attempt_path.read_text().splitlines()) == 24
    assert path.read_text() == text


def test_demo_write_outputs_false_preserves_files(tmp_path):
    path = tmp_path / "unused.md"
    result = demo.run_pit_universe_delisting_demo(report_path=path, write_outputs=False)
    assert len(result["cases"]) == 6
    assert list(tmp_path.iterdir()) == []


def test_demo_retains_unexpected_failures_before_raising(tmp_path, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("injected synthetic failure")

    monkeypatch.setattr(demo, "run_long_only_backtest", broken)
    path = tmp_path / "failure.md"
    with pytest.raises(RuntimeError, match="unexpected synthetic case outcomes"):
        demo.run_pit_universe_delisting_demo(report_path=path)
    payload = json.loads(path.with_suffix(".json").read_text())
    assert [case["status"] for case in payload["metrics"]["cases"][:3]] == [
        "failure"
    ] * 3
    assert len(path.with_name("failure_attempts.jsonl").read_text().splitlines()) == 12


def test_demo_retains_interruption(tmp_path, monkeypatch):
    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(demo, "run_long_only_backtest", interrupted)
    path = tmp_path / "interrupted.md"
    with pytest.raises(KeyboardInterrupt):
        demo.run_pit_universe_delisting_demo(report_path=path)
    events = [
        json.loads(line)
        for line in path.with_name("interrupted_attempts.jsonl")
        .read_text()
        .splitlines()
    ]
    assert [event["status"] for event in events] == ["started", "interrupted"]


def test_synthetic_terminal_event_is_independent_of_future_price_quotes():
    prices, signals, membership, events = demo.synthetic_inputs()
    assert prices["SEC_OLD"].iloc[5:].isna().all()
    assert events.iloc[0]["reference_date"] == prices.index[4]
    assert events.iloc[0]["effective_date"] == prices.index[5]
    assert membership.loc[0, "symbol"] == membership.loc[1, "symbol"]
    assert membership.loc[0, "permanent_id"] != membership.loc[1, "permanent_id"]
    assert signals.index.equals(prices.index)
    pd.testing.assert_index_equal(signals.columns, prices.columns)
