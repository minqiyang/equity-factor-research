"""CI workflow conformance: lanes, thread limits, the required gate, and data scope.

Moved from the retired Track A campaign conformance suite on 2026-09-23. The lane
partition test was added with the four-shard layout on 2026-09-28. The docs-only
change scope tests were added on 2026-10-11.
"""

from __future__ import annotations

from pathlib import Path
import re
import runpy
import subprocess
import sys
import textwrap
import tomllib

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
CHANGE_SCOPE_SCRIPT = PROJECT_ROOT / "scripts" / "ci_change_scope.py"
SLOW_PYTESTMARK = re.compile(r"^pytestmark = (pytest\.mark\.slow|\[pytest\.mark\.slow, [^\n]+\])$", re.M)


def _lane_selections(workflow: str) -> dict[str, list[str]]:
    cases = workflow.split('case "$CI_LANE" in\n', 1)[1].split("\n          esac\n", 1)[0]
    return {lane: words.split() for lane, words
            in re.findall(r"^ +([a-z0-9-]+)\)\n +selection=\(([^)]*)\)", cases, re.M)}


def _step_script(name: str) -> str:
    step = CI_WORKFLOW.read_text(encoding="utf-8").split(f"\n      - name: {name}\n", 1)[1]
    return textwrap.dedent(step.split("        run: |\n", 1)[1].split("\n\n", 1)[0])


def _run_bash(script: str, env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script],
        env=env, cwd=cwd, capture_output=True, text=True, check=False,
    )


def test_ci_runs_only_committed_synthetic_fixtures() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    lowered = workflow.lower()
    assert "name: python validation" in lowered
    assert "python -m pytest -q" in workflow
    assert workflow.count("python -m pytest -q") == 1
    assert "-n auto --dist loadgroup" in workflow
    assert "-n 2" not in workflow
    assert "--max-worker-restart=0" in workflow
    assert "lane: [runner-v3, m4-pipelines, core, diagnostics]" in workflow
    assert "fail-fast: false" in workflow
    assert "max-parallel: 4" in workflow
    assert "shell: bash" in workflow
    assert '"${selection[@]}"' in workflow
    assert "--ignore=tests/test_multifactor_diagnostic_mvp.py" in workflow
    assert "--ignore=tests/test_m3_10_hardening.py" in workflow
    assert "selection=(tests/test_multifactor_diagnostic_mvp.py tests/test_m3_10_hardening.py)" in workflow
    assert "name: ci-evidence-${{ matrix.lane }}-" in workflow
    gate = workflow.split("\n  validation:\n", 1)[1]
    assert "needs: [test-lanes]" in gate
    assert "if: ${{ always() }}" in gate
    assert "LANES_RESULT: ${{ needs.test-lanes.result }}" in gate
    for env_var in (
        'OMP_NUM_THREADS: "1"',
        'OPENBLAS_NUM_THREADS: "1"',
        'MKL_NUM_THREADS: "1"',
        'BLIS_NUM_THREADS: "1"',
        'VECLIB_MAXIMUM_THREADS: "1"',
        'NUMEXPR_NUM_THREADS: "1"',
    ):
        assert env_var in workflow
    assert "python_files=test_campaign_*.py" not in workflow
    assert "committed synthetic fixtures" in lowered
    assert "not result-bearing" in lowered
    assert "private panel" in lowered
    for forbidden in (
        "private_data",
        "performance_access",
        "result_access",
        "fourteen_trial",
        "14-trial",
        "eodhd.com",
    ):
        assert forbidden not in lowered


def test_ci_lanes_run_every_test_file_exactly_once() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    selections = _lane_selections(workflow)
    matrix = workflow.split("        lane: [", 1)[1].split("]", 1)[0].split(", ")
    assert list(selections) == matrix == ["runner-v3", "m4-pipelines", "core", "diagnostics"]
    core = selections.pop("core")
    assert core[0] == "tests" and all(word.startswith("--ignore=") for word in core[1:])
    ignored = [word.removeprefix("--ignore=") for word in core[1:]]
    files = {path.relative_to(PROJECT_ROOT).as_posix() for path in (PROJECT_ROOT / "tests").rglob("test_*.py")}
    named = [path for selected in selections.values() for path in selected]
    assert set(named) <= files and set(ignored) <= files
    for path in sorted(files):
        lanes = [lane for lane, selected in selections.items() if path in selected]
        assert len(lanes + ([] if path in ignored else ["core"])) == 1, path


@pytest.mark.parametrize("lane_result", ["success", "failure", "cancelled", "skipped", ""])
def test_ci_required_gate_accepts_only_successful_lanes(lane_result: str) -> None:
    gate = CI_WORKFLOW.read_text(encoding="utf-8").split("\n  validation:\n", 1)[1]
    command = gate.split("        run: ", 1)[1].strip()
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", command],
        env={"LANES_RESULT": lane_result}, capture_output=True, check=False,
    )
    assert (result.returncode == 0) == (lane_result == "success")


def test_ci_docs_only_mode_skips_only_slow_tests() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "      - name: Classify changed files\n        id: scope\n" in workflow
    assert "EVENT_NAME: ${{ github.event_name }}" in workflow
    assert "CHANGE_SCOPE: ${{ steps.scope.outputs.scope }}" in workflow
    assert 'marker=(-m "not slow")' in workflow
    assert '"${marker[@]}" "${selection[@]}"' in workflow
    assert workflow.count('[ "$CHANGE_SCOPE" = docs-only ]') == 1
    options = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["pytest"]["ini_options"]
    assert any(marker.startswith("slow: ") for marker in options["markers"])
    assert "-m" not in options["addopts"].split()


def test_ci_lanes_outside_core_hold_only_slow_modules() -> None:
    selections = _lane_selections(CI_WORKFLOW.read_text(encoding="utf-8"))
    core = selections.pop("core")
    assert core[0] == "tests"
    for path in [path for selected in selections.values() for path in selected]:
        assert SLOW_PYTESTMARK.search((PROJECT_ROOT / path).read_text(encoding="utf-8")), path


@pytest.mark.parametrize(
    ("paths", "scope"),
    [
        (["README.md", "CHANGELOG.md", "CITATION.cff", "LICENSE", "assets/readme/overview.png"], "docs-only"),
        (["docs/current_handoff.md"], "docs-only"),
        (["docs/engineering_log.md", "docs/sub/page.md", "README.md"], "docs-only"),
        (["README.md", "docs/decision_log.md", "src/backtest/portfolio.py"], "full"),
        (["docs/current_handoff.md", "tests/test_ci_workflow.py"], "full"),
        ([], "full"),
        ([""], "full"),
        (["docs/preregistrations/m4_7_sp500_pit_rerun_v2.json"], "full"),
        (["docs/preregistrations/notes.md"], "full"),
        (["docs/repo_map.md", "docs/preregistrations/notes.md"], "full"),
        ([".github/workflows/ci.yml"], "full"),
        ([".github/CODEOWNERS", "README.md"], "full"),
        (["tests/test_ci_workflow.py"], "full"),
        (["docs/data_manifest.json"], "full"),
        (["reports/summary.md"], "full"),
        (["src/README.md"], "full"),
        (["README.md.orig"], "full"),
        (["pyproject.toml"], "full"),
    ],
)
def test_ci_change_scope_is_docs_only_only_for_document_paths(paths: list[str], scope: str) -> None:
    change_scope = runpy.run_path(str(CHANGE_SCOPE_SCRIPT))["change_scope"]
    assert change_scope(paths) == scope


@pytest.mark.parametrize(
    ("event", "listing", "scope"),
    [
        ("pull_request", "README.md\ndocs/current_handoff.md\n", "docs-only"),
        ("pull_request", "README.md\nsrc/backtest/portfolio.py\n", "full"),
        ("pull_request", "", "full"),
        ("pull_request", None, "full"),
        ("push", "README.md\n", "full"),
        ("merge_group", "README.md\n", "full"),
    ],
)
def test_ci_classify_step_is_docs_only_only_for_a_listed_pull_request(
    tmp_path: Path, event: str, listing: str | None, scope: str
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "git_calls.txt"
    git_body = "exit 1" if listing is None else f'cat "{tmp_path / "listing.txt"}"'
    (tmp_path / "listing.txt").write_text(listing or "", encoding="utf-8")
    (bin_dir / "git").write_text(f'#!/bin/sh\necho "$*" >> "{calls}"\n{git_body}\n', encoding="utf-8")
    (bin_dir / "python").write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
    for stub in bin_dir.iterdir():
        stub.chmod(0o755)
    output = tmp_path / "github_output.txt"
    env = {"EVENT_NAME": event, "GITHUB_OUTPUT": str(output), "PATH": f"{bin_dir}:/usr/bin:/bin"}

    result = _run_bash(_step_script("Classify changed files"), env, PROJECT_ROOT)

    assert result.returncode == 0, result.stderr
    assert result.stdout == f"Change scope: {scope}\n"
    assert output.read_text(encoding="utf-8") == f"scope={scope}\n"
    if event == "pull_request":
        assert calls.read_text(encoding="utf-8") == "diff --name-only --no-renames HEAD^1 HEAD\n"
    else:
        assert not calls.exists()


@pytest.mark.parametrize("lane", ["runner-v3", "m4-pipelines", "diagnostics"])
def test_ci_docs_only_lane_of_slow_modules_passes_without_pytest(tmp_path: Path, lane: str) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python").write_text("#!/bin/sh\nexit 97\n", encoding="utf-8")
    (bin_dir / "python").chmod(0o755)
    env = {"CI_LANE": lane, "CHANGE_SCOPE": "docs-only", "RUNNER_TEMP": str(tmp_path), "PATH": f"{bin_dir}:/usr/bin:/bin"}

    result = _run_bash(_step_script("Run tests"), env, tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        f"Docs-only change: every test in the {lane} lane is marked slow, so this lane does not run pytest."
    ]
