"""Generate a concise repository map for Codex handoffs.

The script reads repository paths and writes only docs/repo_map.md. It skips
cache/build directories, generated reports, and large artifacts by default.
"""

from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "docs" / "repo_map.md"
MAX_FILE_BYTES = 512 * 1024

SKIP_DIR_NAMES = {
    ".cache",
    ".git",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "cache",
    "dist",
    "env",
    "node_modules",
    "venv",
}
GENERATED_TOP_LEVEL_DIRS = {"reports"}

MAJOR_DIRS = [
    (".agents/skills", "Project-specific Codex Skills and workflow gates."),
    (".github", "Repository automation such as CI workflows."),
    ("docs", "Project process notes, readiness gates, designs, logs, and maps."),
    ("scripts", "Workflow tooling; scripts here must not fetch data or trade."),
    (
        "src/campaign",
        "Frozen dataset-independent computations for bounded research campaigns.",
    ),
    ("src/features", "Factor calculations, validation, normalization, combination, and diagnostics."),
    ("src/backtest", "Simulated long-only backtester and metrics helpers."),
    ("src/data", "Strict local CSV and Parquet loaders, blue-chip cohort spec, and metadata review helpers."),
    (
        "src/ledger",
        "Fail-closed Stage 4B schema-registry helpers and Path A/B sqlite3 runtime; caller-supplied DB path outside the repository.",
    ),
    (
        "src/reporting",
        "Experiment log and registry helpers; plotting helpers are placeholder-only future work.",
    ),
    ("research", "Synthetic, committed-fixture, and local real-data diagnostic workflows."),
    ("tests", "Deterministic tests for research logic and guardrails."),
    ("tests/fixtures", "Tiny committed synthetic fixtures only."),
    ("lean", "LEAN-adjacent planning/scaffold files under no-trading guardrails."),
    ("reports", "Generated synthetic reports and logs; summarized but not traversed."),
]

IMPORTANT_FILES = [
    (
        "AGENTS.md",
        "Canonical external-action authority boundary, repository invariants, and research-safety review standards. Reviewer routing lives in the live Herdr+Pi coordination standard.",
    ),
    (
        "docs/current_handoff.md",
        "Concise operational handoff with a timestamped checkpoint, blockers, and next safe action. Authority remains in AGENTS.md.",
    ),
    (
        "docs/north_star.md",
        "Active North Star product aspiration and demo-first delivery principles; not an external-action authority source.",
    ),
    (
        "docs/research_program_charter.md",
        "Preserved historical formal research evidence policy; not an external-action authority source or product delivery blocker.",
    ),
    (
        "docs/purged_bounded_split_contract.md",
        "Accepted Stage 1a timing and sample-isolation design.",
    ),
    (
        "docs/signal_execution_timing_contract.md",
        "Accepted Stage 2a signal, execution, and metric timing design.",
    ),
    (
        "docs/point_in_time_data_methodology_contract.md",
        "Accepted Stage 3 point-in-time data and holdout-evidence methodology.",
    ),
    (
        "docs/experiment_trial_ledger_contract.md",
        "Accepted Stage 4a experiment/trial identity, lifecycle, completeness, access, and integrity design.",
    ),
    (
        "docs/experiment_trial_ledger_schema_registry_contract.md",
        "Accepted Stage 4B-R0 fail-closed schema-registry foundation.",
    ),
    (
        "docs/experiment_trial_ledger_allocation_registration_schema_contract.md",
        "Accepted Stage 4B-R1A/R1B allocation architecture and campaign/experiment release.",
    ),
    (
        "docs/experiment_trial_ledger_trial_family_registration_schema_contract.md",
        "Accepted Stage 4B-R1C-A trial-family registration authority.",
    ),
    (
        "docs/experiment_trial_ledger_sample_registration_schema_contract.md",
        "Accepted Stage 4B-R1D-A local sample registration authority.",
    ),
    (
        "docs/experiment_trial_ledger_binding_schema_contract.md",
        "Accepted Stage 4B-R1E-A binding authority.",
    ),
    (
        "docs/experiment_trial_ledger_trial_allocation_schema_contract.md",
        "Accepted Stage 4B-R1F-A semantic trial-allocation authority.",
    ),
    (
        "docs/experiment_trial_ledger_campaign_inventory_seal_schema_contract.md",
        "Accepted Stage 4B-R1G-A initial campaign-inventory-seal authority.",
    ),
    (
        "docs/experiment_trial_ledger_attempt_allocation_schema_contract.md",
        "Accepted Stage 4B-R1H-A attempt-allocation authority.",
    ),
    (
        "docs/experiment_trial_ledger_attempt_start_schema_contract.md",
        "Accepted Stage 4B-R1I-A attempt-start authority.",
    ),
    (
        "docs/eodhd_sp500_diagnostic_campaign_contract.md",
        "Historical Track A/Track B diagnostic campaign scope authority.",
    ),
    (
        "docs/campaign_bounded_diagnostic_runner_v1.md",
        "Public-safe Track A PR 3 bounded diagnostic runner design note; not an authority source.",
    ),
    (
        "docs/preregistrations/eodhd_sp500_three_factor_diagnostic_v1.yaml",
        "Frozen public Track A machine-readable protocol.",
    ),
    (
        "docs/preregistrations/"
        "eodhd_sp500_three_factor_trial_inventory_v1.json",
        "Exact frozen 14-semantic-trial inventory.",
    ),
    (
        "docs/current_roadmap.md",
        "Canonical program stages, dependency order, gate and completion criteria, and coarse status.",
    ),
    ("docs/repo_map.md", "Generated concise repo map."),
    (
        "docs/codex_long_running_controller.md",
        "Canonical staged workflow and GitHub review lifecycle controller.",
    ),
    (
        ".agents/skills/staged-quant-workflow/SKILL.md",
        "Thin invocation router for the canonical staged workflow documents.",
    ),
    (
        ".github/workflows/ci.yml",
        "Canonical continuous-integration commands and platform test matrix.",
    ),
    (
        "PROJECT_SPEC.md",
        "Research scope, evidence layers, timing rules, assumptions, and non-goals.",
    ),
    ("README.md", "Newcomer overview and runnable demo guidance."),
    ("CHANGELOG.md", "User-visible repository changes."),
    ("docs/engineering_log.md", "Chronological engineering notes and validation history."),
    ("docs/decision_log.md", "Durable research and workflow decisions."),
    ("docs/troubleshooting_log.md", "Failures, recovery steps, and prevention notes."),
    ("EXPERIMENT_LOG.md", "Research experiment records; not for workflow-only changes."),
    ("pyproject.toml", "Package metadata and test dependencies."),
    ("src/backtest/market_impact.py", "Causal daily liquidity, square-root impact, participation policies, and self-financing simulated fills."),
    ("research/market_impact_capacity_demo.py", "Generated AUM scenarios with retained refusals, net-return capacity tables, and attempt evidence."),
]

LOCAL_VALIDATION_COMMANDS = [
    ("Repo map refresh", "python scripts/repo_map.py"),
    ("Unstaged whitespace check", "git diff --check"),
    ("Staged whitespace check", "git diff --cached --check"),
    ("Committed branch whitespace check", "git diff --check origin/main...HEAD"),
    (
        "Skill audit for workflow/Skill changes",
        "pwsh -NoProfile -File scripts/audit-skills.ps1",
    ),
]


def _is_skipped_dir(name: str) -> bool:
    lowered = name.lower()
    return (
        lowered in SKIP_DIR_NAMES
        or "pycache" in lowered
        or lowered.endswith(".egg-info")
    )


def _is_generated_dir(rel_path: Path) -> bool:
    return bool(rel_path.parts) and rel_path.parts[0] in GENERATED_TOP_LEVEL_DIRS


def _iter_mapped_files() -> list[Path]:
    mapped: list[Path] = []
    for root, dirs, files in os.walk(REPO_ROOT):
        root_path = Path(root)
        rel_root = root_path.relative_to(REPO_ROOT)

        dirs[:] = sorted(
            dirname
            for dirname in dirs
            if not _is_skipped_dir(dirname)
            and not _is_generated_dir(rel_root / dirname)
        )

        if _is_generated_dir(rel_root):
            dirs[:] = []
            continue

        for filename in sorted(files):
            path = root_path / filename
            rel_path = path.relative_to(REPO_ROOT)
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            mapped.append(rel_path)
    return mapped


def _count_under(files: list[Path], rel_dir: str) -> int:
    prefix = Path(rel_dir).parts
    if rel_dir == "reports":
        return 0
    return sum(1 for path in files if path.parts[: len(prefix)] == prefix)


def _count_label(count: int) -> str:
    suffix = "file" if count == 1 else "files"
    return f"{count} mapped {suffix}"


def _exists_label(rel_path: str) -> str:
    if REPO_ROOT / rel_path == OUTPUT_PATH:
        return "generated by this script"
    path = REPO_ROOT / rel_path
    if path.exists():
        return "present"
    return "missing"


def build_repo_map() -> str:
    files = _iter_mapped_files()
    lines = [
        "# Repo Map",
        "",
        "Generated by `python scripts/repo_map.py`.",
        "",
        "Scope: concise orientation for Codex handoffs. Cache/build directories, generated reports, and files larger than 512 KiB are skipped by default.",
        "",
        "## Major Directories",
        "",
        "| Path | Purpose | Map status |",
        "| --- | --- | --- |",
    ]

    for rel_dir, purpose in MAJOR_DIRS:
        path = REPO_ROOT / rel_dir
        if rel_dir == "reports":
            status = "generated outputs summarized only"
        elif path.exists():
            status = _count_label(_count_under(files, rel_dir))
        else:
            status = "missing"
        lines.append(f"| `{rel_dir}/` | {purpose} | {status} |")

    lines.extend(
        [
            "",
            "## Important Files",
            "",
        ]
    )
    for rel_path, purpose in IMPORTANT_FILES:
        lines.append(f"- `{rel_path}` ({_exists_label(rel_path)}): {purpose}")

    lines.extend(
        [
            "",
            "## Test And Validation Commands",
            "",
            "- CI validation commands are defined only in `.github/workflows/ci.yml`; this map does not duplicate them.",
        ]
    )
    for label, command in LOCAL_VALIDATION_COMMANDS:
        lines.append(f"- {label}: `{command}`")

    lines.extend(
        [
            "",
            "## Output Discipline",
            "",
            "- Read `docs/current_handoff.md` for the recorded checkpoint, then the controller and `docs/current_roadmap.md`; verify remote facts live before acting.",
            "- Do not print full generated reports or large logs by default; inspect targeted ranges only when needed.",
            "- Use capped command output for unknown commands, and save full output to a temp file when full review is necessary.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_repo_map(), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
