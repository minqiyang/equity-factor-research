from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_required_directories_exist() -> None:
    required_directories = [
        "src/data",
        "src/features",
        "src/strategies",
        "src/backtest",
        "src/risk",
        "src/reporting",
        "src/utils",
        "tests",
        "research",
        "reports",
    ]

    for directory in required_directories:
        assert (PROJECT_ROOT / directory).is_dir(), f"Missing directory: {directory}"


def test_required_governance_files_exist() -> None:
    required_files = [
        "README.md",
        "PROJECT_SPEC.md",
        "AGENTS.md",
        "EXPERIMENT_LOG.md",
        "pyproject.toml",
    ]

    for file_name in required_files:
        assert (PROJECT_ROOT / file_name).is_file(), f"Missing file: {file_name}"


def test_current_roadmap_and_handoff_define_one_active_status_source() -> None:
    roadmap = (PROJECT_ROOT / "docs/current_roadmap.md").read_text(
        encoding="utf-8"
    )
    handoff = (PROJECT_ROOT / "docs/current_handoff.md").read_text(encoding="utf-8")
    historical_roadmap = (
        PROJECT_ROOT / "docs/current_roadmap_gap_refresh.md"
    ).read_text(encoding="utf-8")

    for phrase in [
        "This is the canonical roadmap",
        "## Implemented Baseline",
        "## Open Gaps",
        "## Delivery Sequence",
        "Require CI and current-head Codex review before merge",
        "Reporting plots are not implemented",
        "LEAN execution remains out of scope",
    ]:
        assert phrase in roadmap

    for phrase in [
        "Active roadmap: `docs/current_roadmap.md`",
        "## Completed",
        "## Active Stage",
        "## Do Not Infer",
        "## Next Safe Actions",
    ]:
        assert phrase in handoff

    assert "## Status: Historical" in historical_roadmap
    assert "must not be used as the current task queue" in historical_roadmap


def test_placeholder_modules_are_importable() -> None:
    import backtest.metrics
    import backtest.portfolio
    import data.csv_loader
    import features.momentum
    import features.reversal
    import features.volatility
    import reporting.plots
    import risk.constraints

    assert features.momentum.__doc__
    assert features.reversal.__doc__
    assert features.volatility.__doc__
    assert backtest.portfolio.__doc__
    assert backtest.metrics.__doc__
    assert data.csv_loader.__doc__
    assert risk.constraints.__doc__
    assert reporting.plots.__doc__


def test_public_metadata_and_readme_match_implemented_scope() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    metadata = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]

    assert "docs/current_roadmap.md" in readme
    assert "plotting remains unimplemented" in readme
    assert "No market-data downloader" in readme
    assert "private_data" not in readme
    assert metadata["license"] == "Apache-2.0"
    assert metadata["urls"]["Repository"].endswith("equity-factor-research")
    assert metadata["dependencies"] == [
        "numpy>=1.26",
        "pandas>=2.1",
        "scipy>=1.11",
    ]
