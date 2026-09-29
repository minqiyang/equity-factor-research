"""CI workflow conformance: lanes, thread limits, the required gate, and data scope.

Moved from the retired Track A campaign conformance suite on 2026-09-23. The lane
partition test was added with the four-shard layout on 2026-09-28.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_runs_only_committed_synthetic_fixtures() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    lowered = workflow.lower()
    assert "name: python validation" in lowered
    assert "python -m pytest -q" in workflow
    assert workflow.count("python -m pytest -q") == 1
    assert "-n 2 --dist loadgroup" in workflow
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
    cases = workflow.split('case "$CI_LANE" in\n', 1)[1].split("\n          esac\n", 1)[0]
    selections = {lane: words.split() for lane, words
                  in re.findall(r"^ +([a-z0-9-]+)\)\n +selection=\(([^)]*)\)", cases, re.M)}
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
