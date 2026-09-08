"""Baseline-passing public-boundary regression plus fresh-process baseline oracle."""

import json
from pathlib import Path

import pytest

from ablation_public_capture_support import cases, collect


FIXTURE = Path(__file__).parent / "fixtures/ablation/public_capture_baseline.json"
EXPECTED = json.loads(FIXTURE.read_text())


@pytest.fixture(scope="module")
def observed():
    return collect()


@pytest.mark.parametrize("name", tuple(EXPECTED))
def test_public_baseline_parity(name, observed):
    assert observed[name] == EXPECTED[name]


@pytest.mark.parametrize("name", tuple(cases()))
def test_capture_keeps_public_shape_and_current_digest(name, observed):
    record = observed[name]
    if name == "unsupported_custom_real":
        assert record["status"] == "rejected"
        assert record["reason"] == "source_provenance_invalid"
        return
    assert record["status"] == "accepted"
    rows, columns = record["shape"]
    for role in ("prices", "signals"):
        frame = record["capture"][role]
        assert len(frame["original_cells"]) == rows
        assert all(len(row) == columns for row in frame["original_cells"])
        assert frame["current_state_digest"] == frame["original_state_digest"]
        assert frame["mutations"] == []


def test_independent_two_by_zero_golden(observed):
    prices = observed["shape_2x0"]["capture"]["prices"]
    assert prices["original_cells"] == [[], []]
    assert prices["original_state_digest"] == "eae69de8f97556d7a3022e1d56f4258d7c13b675a879bbc81f4219ed8efecf4b"


def test_mixed_scalar_identity_and_signed_zero(observed):
    cells = observed["mixed_uint64_float"]["capture"]["prices"]["original_cells"]
    assert cells[0][0] == {"kind": "integer", "payload": [str(2**63 + 1)]}
    assert cells[1][0] == {"kind": "integer", "payload": [str(2**63 + 3)]}
    assert cells[1][1] == {"kind": "real_float", "payload": ["-0x0.0p+0"]}
    cells = observed["mixed_real_complex"]["capture"]["prices"]["original_cells"]
    assert [cell["kind"] for cell in cells[0]] == ["real_float", "complex"]
    assert cells[1][1]["payload"] == ["-0x0.0p+0", "-0x0.0p+0"]


@pytest.mark.parametrize("role", ["prices", "signals"])
def test_tracked_current_digest_matches_public_recapture(role, observed):
    events = observed[f"tracked_chain_{role}"]
    initial = events[0]["capture"][role]
    for index, event in enumerate(events[1:], start=1):
        assert event["status"] == "accepted"
        frame = event["capture"][role]
        assert frame["original_cells"] == initial["original_cells"]
        assert frame["original_state_digest"] == initial["original_state_digest"]
        assert frame["current_state_digest"] == event["recapture"][role]["original_state_digest"]
        assert len(frame["mutations"]) == index
