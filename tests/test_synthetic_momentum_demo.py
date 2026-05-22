from pathlib import Path

import pandas as pd

from research.synthetic_momentum_demo import (
    SyntheticDemoConfig,
    generate_synthetic_prices,
    run_synthetic_momentum_demo,
)


def test_synthetic_price_generation_is_reproducible() -> None:
    config = SyntheticDemoConfig(seed=123, asset_count=20, periods=30)

    first = generate_synthetic_prices(config)
    second = generate_synthetic_prices(config)

    pd.testing.assert_frame_equal(first, second)
    assert first.shape == (30, 20)
    assert list(first.columns[:3]) == ["ASSET_01", "ASSET_02", "ASSET_03"]


def test_synthetic_demo_writes_report_with_profitability_warning(tmp_path: Path) -> None:
    report_path = tmp_path / "synthetic_momentum_demo.md"
    config = SyntheticDemoConfig(seed=123, asset_count=20, periods=320, top_n=5)

    result = run_synthetic_momentum_demo(config=config, report_path=report_path)

    report_text = report_path.read_text(encoding="utf-8")
    assert report_path.is_file()
    assert "synthetic data only" in report_text
    assert "not evidence of real-world strategy profitability" in report_text
    assert "| Total return |" in report_text
    assert result.holdings.shape[1] == 20
