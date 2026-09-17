from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "report_name",
    ["demo_v0", "synthetic_multifactor_backtest_demo"],
)
def test_committed_official_report_uses_relative_attempt_log(report_name: str) -> None:
    report = Path(__file__).resolve().parents[1] / "reports" / f"{report_name}.md"
    text = report.read_text(encoding="utf-8")

    assert (
        f"- All-Attempt Case Logging: `reports/{report_name}_attempts.jsonl` "
        "(lightweight demo logging; not charter Stage 4 ledger accounting)"
    ) in text.splitlines()
    assert "/var/folders" not in text
