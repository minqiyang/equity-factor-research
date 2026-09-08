"""Prepared campaign caches must be owned by one execution, never reused later."""

from datetime import date

from campaign import runner
from test_campaign_runner import _p1_cases, _reconcile_ready_config, _session_range, _synthetic_panel


def test_separate_executions_recompute_intervals_and_keep_cost_outputs(tmp_path, monkeypatch):
    cases = _p1_cases()
    settings = cases["inputs"]["rebalance"]
    sessions = _session_range(date.fromisoformat(settings["start"]), settings["session_count"])
    flags = {row["signal_date"]: row["in_universe"] for row in settings["signals"]}
    prepared = _synthetic_panel(sessions, settings["listing_count"], flags, "rebalance", cases)
    calls = []
    original = runner._held_map

    def observe(panel, begin, end, schedule):
        calls.append(panel)
        return original(panel, begin, end, schedule)

    monkeypatch.setattr(runner, "_held_map", observe)
    outputs = []
    previous_panels = []
    for index in range(2):
        directory = tmp_path / f"execution_{index}"
        directory.mkdir()
        monkeypatch.setenv("HOME", str(directory / "home"))
        config, _ = _reconcile_ready_config(directory, prepared, "ownership")
        start = len(calls)
        result = runner.run_campaign(config)
        assert result.status == cases["inputs"]["executed_status"]
        current_panels = calls[start:]
        assert current_panels, "a later execution must prepare its own held returns"
        assert all(panel is not previous for panel in current_panels for previous in previous_panels)
        previous_panels = current_panels
        outputs.append({name: value for name, value in result.artifacts.items() if name != "run_manifest.json"})
    assert outputs[0] == outputs[1]
