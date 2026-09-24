"""Structural checks for the governance constitution, standing grants, and handoff freshness."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAX_AGENTS_LINES = 200
AGENT_MAINTAINED_GOVERNANCE = [
    "AGENTS.md",
    "docs/codex_long_running_controller.md",
    "docs/current_roadmap.md",
    "docs/current_handoff.md",
    "docs/north_star.md",
    ".agents/skills/staged-quant-workflow/SKILL.md",
]
GRANT_LANGUAGE = [
    "The owner grants standing",
    "Owner-Authorized Autonomous Coordinator Lifecycle",
    "is authorized to autonomously",
]


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"missing section: {heading}"
    return match.group(1)


def _latest_merged_pr_before_head() -> int:
    result = subprocess.run(
        ["git", "log", "--first-parent", "--format=%s", "-n", "200", "HEAD~1"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    for subject in result.stdout.splitlines():
        # Protected merges are squash merges whose subject ends with (#N).
        match = re.search(r"\(#(\d+)\)\s*$", subject)
        if match:
            return int(match.group(1))
    raise AssertionError("first-parent history before HEAD has no merged PR subject")


def test_agents_constitution_stays_bounded_with_twelve_invariants() -> None:
    agents = _read("AGENTS.md")
    assert len(agents.splitlines()) <= MAX_AGENTS_LINES

    invariants = _section(agents, "Research Safety Invariants")
    labels = re.findall(r"^- \*\*(R\d+) ", invariants, re.MULTILINE)
    assert labels == [f"R{number}" for number in range(1, 13)]


def test_standing_grants_live_only_in_the_authority_record() -> None:
    authority = _read("AUTHORITY.md")
    assert (
        "Canonical responsibility: the owner's standing grants for this repository."
        in authority
    )
    grants = re.findall(r"^## (.+)$", authority, re.MULTILINE)
    assert grants
    for grant in grants:
        body = _section(authority, grant)
        for field in ("- Grant:", "- Scope:", "- Source:", "- Expiry:"):
            assert field in body, (grant, field)

    for relative_path in AGENT_MAINTAINED_GOVERNANCE:
        normalized = " ".join(_read(relative_path).split())
        for phrase in GRANT_LANGUAGE:
            assert phrase not in normalized, (relative_path, phrase)


def test_grant_language_check_detects_a_reintroduced_grant() -> None:
    mutated = "- **Owner-Authorized Autonomous Coordinator Lifecycle**: ..."
    assert any(phrase in mutated for phrase in GRANT_LANGUAGE)


def test_north_star_states_edge_objective_and_kill_criteria() -> None:
    north_star = _read("docs/north_star.md")
    for heading in ("Edge Thesis", "Objective And Hurdle", "Kill Criteria"):
        assert _section(north_star, heading).strip()
    assert "R1–R12" in north_star


def test_handoff_tracks_the_latest_merged_pr() -> None:
    checkpoint = _section(
        _read("docs/current_handoff.md"), "Latest Recorded Operational Checkpoint"
    )
    recorded = re.search(r"\(main after PR #(\d+)\)", checkpoint)
    assert recorded, "the baseline bullet records `(main after PR #N)`"
    assert int(recorded.group(1)) >= _latest_merged_pr_before_head() - 1
