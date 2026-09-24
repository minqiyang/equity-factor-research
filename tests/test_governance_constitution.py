"""Structural checks for the governance constitution, standing grants, and handoff freshness."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

import pytest

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
# Earlier formulations of the standing grants, kept so a reintroduced copy fails.
HISTORICAL_GRANT_PHRASES = [
    "The owner grants standing",
    "Owner-Authorized Autonomous Coordinator Lifecycle",
    "is authorized to autonomously",
]
GRANT_SHINGLE_WORDS = 8
MAX_HANDOFF_MERGE_LAG = 1
SQUASH_SUBJECT = re.compile(r"\(#(\d+)\)\s*$")


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


def _normalize(text: str) -> str:
    return " ".join(re.sub(r"[*_`>]", " ", text).casefold().split())


def _grant_quotes(authority: str) -> list[str]:
    """Return the quoted source text of each grant in the authority record."""
    quotes = []
    for heading in re.findall(r"^## (.+)$", authority, re.MULTILINE):
        lines = _section(authority, heading).splitlines()
        quote = " ".join(line.strip()[1:] for line in lines if line.strip().startswith(">"))
        assert quote.strip(), f"grant {heading!r} quotes no source text"
        quotes.append(quote)
    return quotes


def _grant_language_hits(
    documents: dict[str, str], grant_quotes: list[str]
) -> list[tuple[str, str]]:
    """Find standing-grant wording in agent-maintained governance files.

    This is a finite textual regression guard. It matches the historical grant
    formulations and every run of `GRANT_SHINGLE_WORDS` consecutive words from
    the current grant quotes, after case and whitespace normalization. It does
    not interpret paraphrased authority.
    """
    patterns = {_normalize(phrase) for phrase in HISTORICAL_GRANT_PHRASES}
    for quote in grant_quotes:
        words = _normalize(quote).split()
        patterns.update(
            " ".join(words[i : i + GRANT_SHINGLE_WORDS])
            for i in range(len(words) - GRANT_SHINGLE_WORDS + 1)
        )
    return [
        (path, pattern)
        for path, text in documents.items()
        for pattern in sorted(patterns)
        if pattern in _normalize(text)
    ]


def _first_parent_history(start: str) -> list[tuple[str, str]]:
    result = subprocess.run(
        ["git", "log", "--first-parent", "--format=%H%x00%s", start],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    history = []
    for line in result.stdout.splitlines():
        sha, subject = line.split("\0", 1)
        history.append((sha, subject))
    return history


def _merges_since(checkpoint: str, history: list[tuple[str, str]]) -> int:
    """Count merged pull requests on a first-parent history after a checkpoint.

    `history` runs newest first from the base tip. Squash-merge subjects end
    with `(#N)`. A checkpoint that the history does not contain, including a
    future or foreign commit, is refused.
    """
    merges = 0
    for sha, subject in history:
        if sha == checkpoint:
            return merges
        if SQUASH_SUBJECT.search(subject):
            merges += 1
    raise AssertionError(f"checkpoint {checkpoint} is absent from the base history")


def _handoff_checkpoint(handoff: str) -> str:
    checkpoint = _section(handoff, "Latest Recorded Operational Checkpoint")
    match = re.search(
        r"^- Last externally verified protected baseline.*?`([0-9a-f]{40})`",
        checkpoint,
        re.MULTILINE | re.DOTALL,
    )
    assert match, "the checkpoint records the baseline commit as a full SHA"
    return match.group(1)


def test_agents_constitution_stays_bounded_with_twelve_invariants() -> None:
    agents = _read("AGENTS.md")
    assert len(agents.splitlines()) <= MAX_AGENTS_LINES

    invariants = _section(agents, "Research Safety Invariants")
    labels = re.findall(r"^- \*\*(R\d+) ", invariants, re.MULTILINE)
    assert labels == [f"R{number}" for number in range(1, 13)]


def test_authority_record_fields_and_quotes() -> None:
    authority = _read("AUTHORITY.md")
    assert (
        "Canonical responsibility: the owner's standing grants for this repository."
        in authority
    )
    grants = re.findall(r"^## (.+)$", authority, re.MULTILINE)
    assert len(grants) == len(_grant_quotes(authority)) == 2
    for grant in grants:
        body = _section(authority, grant)
        for field in ("Grant", "Scope", "Source", "Expiry"):
            assert re.search(rf"^- {field}\b", body, re.MULTILINE), (grant, field)


def test_standing_grants_live_only_in_the_authority_record() -> None:
    documents = {path: _read(path) for path in AGENT_MAINTAINED_GOVERNANCE}
    quotes = _grant_quotes(_read("AUTHORITY.md"))
    assert _grant_language_hits(documents, quotes) == []


@pytest.mark.parametrize("copy", ["current_grant_0", "current_grant_1", *HISTORICAL_GRANT_PHRASES])
def test_grant_guard_detects_copied_grant_text(copy: str) -> None:
    quotes = _grant_quotes(_read("AUTHORITY.md"))
    text = quotes[int(copy[-1])] if copy.startswith("current_grant_") else copy
    for path in AGENT_MAINTAINED_GOVERNANCE:
        documents = {p: _read(p) for p in AGENT_MAINTAINED_GOVERNANCE}
        documents[path] += f"\n- {text}\n"
        assert any(hit[0] == path for hit in _grant_language_hits(documents, quotes))


@pytest.mark.parametrize("index", [0, 1])
def test_grant_guard_detects_grant_text_without_historical_phrases(index: int) -> None:
    """An adapted copy without any historical phrase still matches word runs."""
    quotes = _grant_quotes(_read("AUTHORITY.md"))
    text = _normalize(quotes[index])
    for phrase in HISTORICAL_GRANT_PHRASES:
        text = text.replace(_normalize(phrase), " ")
    documents = {"AGENTS.md": _read("AGENTS.md") + f"\n- {text}\n"}
    assert not any(_normalize(p) in _normalize(text) for p in HISTORICAL_GRANT_PHRASES)
    assert _grant_language_hits(documents, quotes)


def test_grant_guard_detects_a_partial_copy() -> None:
    quotes = _grant_quotes(_read("AUTHORITY.md"))
    fragment = " ".join(quotes[1].split()[10 : 10 + GRANT_SHINGLE_WORDS])
    documents = {"AGENTS.md": _read("AGENTS.md") + f"\n{fragment.upper()}\n"}
    assert _grant_language_hits(documents, quotes)


def test_north_star_states_edge_objective_and_kill_criteria() -> None:
    north_star = _read("docs/north_star.md")
    for heading in ("Edge Thesis", "Objective And Hurdle", "Kill Criteria"):
        assert _section(north_star, heading).strip()
    assert "R1–R12" in north_star


@pytest.mark.parametrize(
    "history,checkpoint,merges",
    [
        # A skipped PR number is still one merged PR.
        ([("c258", "feat: b (#258)"), ("c255", "feat: a (#255)")], "c255", 1),
        # Out-of-order PR numbers still count merges, not identifiers.
        (
            [("c257", "fix: c (#257)"), ("c300", "feat: b (#300)"), ("c299", "feat: a (#299)")],
            "c299",
            2,
        ),
        # Feature commits on a stacked branch carry no merge subject.
        ([("f2", "fix: y"), ("f1", "docs: x"), ("c256", "docs: v8 (#256)")], "c256", 0),
    ],
)
def test_merges_since_counts_merged_pull_requests(history, checkpoint, merges) -> None:
    assert _merges_since(checkpoint, history) == merges


def test_merges_since_refuses_an_unknown_checkpoint() -> None:
    with pytest.raises(AssertionError, match="absent from the base history"):
        _merges_since("future", [("c256", "docs: v8 (#256)"), ("c255", "feat (#255)")])


def test_handoff_trails_its_base_by_at_most_one_merged_pr() -> None:
    """HEAD~1 is the base tip in a pull-request merge ref and after a squash merge."""
    checkpoint = _handoff_checkpoint(_read("docs/current_handoff.md"))
    lag = _merges_since(checkpoint, _first_parent_history("HEAD~1"))
    assert lag <= MAX_HANDOFF_MERGE_LAG, f"handoff trails its base by {lag} merged PRs"
