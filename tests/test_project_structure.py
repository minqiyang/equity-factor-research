from pathlib import Path


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


def test_current_handoff_has_freshness_guardrails() -> None:
    handoff = (PROJECT_ROOT / "docs/current_handoff.md").read_text(encoding="utf-8")

    required_phrases = [
        "## Freshness Checklist",
        "Cached baseline at last handoff edit",
        "Latest Verified State",
        "Still Blocked",
        "Next Safe Stage",
        "@codex review",
        "P1/P2 feedback before merge",
    ]
    stale_active_stage_phrases = [
        "after this handoff refresh PR is reviewed and merged",
        "after this PR merges",
        "This handoff refresh is PR",
        "after it merges",
    ]

    for phrase in required_phrases:
        assert phrase in handoff
    for phrase in stale_active_stage_phrases:
        assert phrase not in handoff


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
