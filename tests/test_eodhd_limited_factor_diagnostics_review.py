import json
from pathlib import Path

import pytest

from research.eodhd_limited_factor_diagnostics_review import (
    EODHDLimitedFactorDiagnosticsReviewConfig,
    run_eodhd_limited_factor_diagnostics_review,
)


def test_writes_limited_factor_diagnostics_review(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    dry_run_summary_path = bundle / "FACTOR_DIAGNOSTICS_DRY_RUN_SUMMARY.md"
    readiness_review_path = bundle / "FACTOR_DIAGNOSTICS_READINESS_REVIEW.json"
    experiment_log_path = bundle / "FACTOR_DIAGNOSTICS_EXPERIMENT_LOG.json"
    output_json_path = bundle / "LIMITED_FACTOR_DIAGNOSTICS_REVIEW.json"
    output_markdown_path = bundle / "LIMITED_FACTOR_DIAGNOSTICS_REVIEW.md"

    dry_run_summary_path.write_text(
        "\n".join(
            [
                "# EODHD Factor Diagnostics Dry Run Summary",
                "",
                "## Factor Coverage",
                "",
                "| factor | date_count | asset_count | valid_observations | missing_observations |",
                "| --- | --- | --- | --- | --- |",
                "| alpha_009 | 3 | 2 | 4 | 2 |",
                "| alpha_012 | 3 | 2 | 5 | 1 |",
                "",
                "## Split Diagnostics",
                "",
                "| factor | split | date_count | factor_valid_observations | forward_return_valid_observations | ic_valid_dates | rank_ic_valid_dates | quantile_spread_valid_dates | mean_ic | mean_rank_ic | mean_quantile_spread |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| alpha_009 | train | 2 | 3 | 3 | 1 | 1 | 1 | 0.10 | 0.20 | 0.30 |",
                "| alpha_012 | validation | 1 | 2 | 2 | 1 | 1 | 1 | -0.10 | -0.20 | -0.30 |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    readiness_review_path.write_text(
        json.dumps(
            {
                "ready_for_limited_factor_diagnostics_review": True,
                "input_file_paths": {
                    "experiment_log": str(experiment_log_path),
                    "dry_run_summary": str(dry_run_summary_path),
                },
                "summary_counts": {
                    "asset_rows": 6,
                    "benchmark_rows": 3,
                    "symbol_coverage": 3,
                },
                "date_range": {"start": "2020-01-02", "end": "2020-01-06"},
                "no_interpretation_statement": (
                    "This readiness review does not interpret IC, Rank IC, "
                    "quantile spread, returns, alpha, profitability, or trading readiness."
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    experiment_log_path.write_text(
        json.dumps(
            {
                "allowed_diagnostics": [
                    "factor coverage",
                    "factor missingness",
                    "IC",
                    "Rank IC",
                    "quantile spread",
                    "split labels",
                ],
                "forbidden_interpretations": [
                    "strategy run",
                    "backtest",
                    "portfolio construction",
                    "trade simulation",
                    "PnL",
                    "Sharpe",
                    "drawdown",
                    "performance interpretation",
                    "profitability claim",
                    "alpha claim",
                    "trading-readiness claim",
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = run_eodhd_limited_factor_diagnostics_review(
        EODHDLimitedFactorDiagnosticsReviewConfig(
            bundle_path=bundle,
            dry_run_summary_path=dry_run_summary_path,
            readiness_review_path=readiness_review_path,
            experiment_log_path=experiment_log_path,
            output_json_path=output_json_path,
            output_markdown_path=output_markdown_path,
        )
    )

    assert json.loads(output_json_path.read_text(encoding="utf-8")) == payload
    assert output_markdown_path.exists()
    assert payload["review_scope"] == "limited_factor_diagnostics_review"
    assert payload["diagnostics_are_research_only"] is True
    assert payload["input_readiness"]["ready_for_limited_factor_diagnostics_review"] is True
    assert payload["factor_coverage"]["alpha_009"]["valid_observations"] == 4
    assert payload["factor_coverage"]["alpha_009"]["missing_observations"] == 2
    assert payload["split_labels"] == ["train", "validation"]
    assert payload["split_diagnostics"][0]["mean_ic"] == 0.1
    assert payload["split_diagnostics"][0]["mean_rank_ic"] == 0.2
    assert payload["split_diagnostics"][0]["mean_quantile_spread"] == 0.3
    assert payload["summary_counts"] == {
        "asset_rows": 6,
        "benchmark_rows": 3,
        "symbol_coverage": 3,
    }
    assert "ready_for_trading" not in payload
    assert "ready_for_strategy" not in payload
    assert "ready_for_alpha" not in payload
    assert "ready_for_live_use" not in payload
    assert "No strategy" in payload["no_strategy_no_performance_statement"]


def test_limited_review_rejects_not_ready_input(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    summary_path = bundle / "summary.md"
    readiness_path = bundle / "readiness.json"
    experiment_log_path = bundle / "experiment.json"
    summary_path.write_text("# summary\n", encoding="utf-8")
    readiness_path.write_text(
        json.dumps({"ready_for_limited_factor_diagnostics_review": False}) + "\n",
        encoding="utf-8",
    )
    experiment_log_path.write_text(json.dumps({}) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="readiness review is not ready"):
        run_eodhd_limited_factor_diagnostics_review(
            EODHDLimitedFactorDiagnosticsReviewConfig(
                bundle_path=bundle,
                dry_run_summary_path=summary_path,
                readiness_review_path=readiness_path,
                experiment_log_path=experiment_log_path,
                output_json_path=bundle / "review.json",
                output_markdown_path=bundle / "review.md",
            )
        )
