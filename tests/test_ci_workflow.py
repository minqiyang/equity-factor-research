"""CI workflow conformance: lanes, thread limits, the required gate, and data scope.

Moved verbatim from the retired Track A campaign conformance suite (2026-09-23).
"""

from __future__ import annotations

from pathlib import Path
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
    assert "-n 2 --dist worksteal" in workflow
    assert "--max-worker-restart=0" in workflow
    assert "lane: [core, diagnostics]" in workflow
    assert "fail-fast: false" in workflow
    assert "max-parallel: 2" in workflow
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


@pytest.mark.parametrize("lane_result", ["success", "failure", "cancelled", "skipped", ""])
def test_ci_required_gate_accepts_only_successful_lanes(lane_result: str) -> None:
    gate = CI_WORKFLOW.read_text(encoding="utf-8").split("\n  validation:\n", 1)[1]
    command = gate.split("        run: ", 1)[1].strip()
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", command],
        env={"LANES_RESULT": lane_result}, capture_output=True, check=False,
    )
    assert (result.returncode == 0) == (lane_result == "success")
