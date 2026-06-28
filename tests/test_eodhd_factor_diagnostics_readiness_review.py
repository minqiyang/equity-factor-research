import json
from pathlib import Path

import pytest

from research.eodhd_factor_diagnostics_readiness_review import (
    EODHDFactorDiagnosticsReadinessReviewConfig,
    run_eodhd_factor_diagnostics_readiness_review,
)


def test_writes_readiness_review_from_private_experiment_log(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    summary_path = bundle / "FACTOR_DIAGNOSTICS_DRY_RUN_SUMMARY.md"
    experiment_log_path = bundle / "FACTOR_DIAGNOSTICS_EXPERIMENT_LOG.json"
    experiment_log_markdown_path = bundle / "FACTOR_DIAGNOSTICS_EXPERIMENT_LOG.md"
    review_json_path = bundle / "FACTOR_DIAGNOSTICS_READINESS_REVIEW.json"
    review_markdown_path = bundle / "FACTOR_DIAGNOSTICS_READINESS_REVIEW.md"

    summary_path.write_text(
        "\n".join(
            [
                "# EODHD Factor Diagnostics Dry Run Summary",
                "",
                "## Row Counts",
                "",
                "- Asset rows: 2",
                "- Benchmark rows: 2",
                "- Symbol coverage: 2",
                "",
                "## Factor Coverage",
                "",
                "| factor | date_count | asset_count | valid_observations | missing_observations |",
                "| --- | --- | --- | --- | --- |",
                "| alpha_009 | 2 | 1 | 1 | 1 |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    experiment_log_markdown_path.write_text("# handoff\n", encoding="utf-8")
    experiment_log_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_label": "unit-test-handoff",
                "data_source": "EODHD local CSV private bundle",
                "local_private_bundle_path": str(bundle),
                "input_file_paths": {
                    "factor_diagnostics_summary": str(summary_path),
                    "ohlcv": str(bundle / "normalized" / "eodhd_ohlcv_long.csv"),
                    "benchmark": str(bundle / "normalized" / "eodhd_benchmark_spy.csv"),
                    "dry_run_summary_output": str(summary_path),
                },
                "output_file_paths": {
                    "experiment_log_json": str(experiment_log_path),
                    "experiment_log_markdown": str(experiment_log_markdown_path),
                },
                "symbol_coverage": 2,
                "row_counts": {"asset_rows": 2, "benchmark_rows": 2},
                "date_range": {"start": "2020-01-02", "end": "2020-01-03"},
                "factor_diagnostics_stage_name": "EODHD factor diagnostics dry run",
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
                "adjusted_close_policy": "Diagnostics use adjusted_close.",
                "static_universe_survivorship_caveat": "The selected universe is static.",
                "no_strategy_no_backtest_statement": (
                    "No strategy, backtest, portfolio construction, PnL, Sharpe, "
                    "drawdown, trade simulation, performance interpretation, "
                    "profitability claim, alpha claim, or trading-readiness claim was performed."
                ),
                "next_checkpoint": "Complete a real-data readiness review.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = run_eodhd_factor_diagnostics_readiness_review(
        EODHDFactorDiagnosticsReadinessReviewConfig(
            bundle_path=bundle,
            experiment_log_path=experiment_log_path,
            dry_run_summary_path=summary_path,
            review_json_path=review_json_path,
            review_markdown_path=review_markdown_path,
        )
    )

    assert json.loads(review_json_path.read_text(encoding="utf-8")) == payload
    assert review_markdown_path.exists()
    assert payload["ready_for_limited_factor_diagnostics_review"] is True
    assert "ready_for_trading" not in payload
    assert "ready_for_strategy" not in payload
    assert "ready_for_alpha" not in payload
    assert "ready_for_live_use" not in payload
    assert payload["checks"]["required_private_artifacts_exist"]["passed"] is True
    assert payload["checks"]["expected_data_source"]["passed"] is True
    assert payload["checks"]["symbol_coverage_recorded"]["passed"] is True
    assert payload["checks"]["row_counts_recorded"]["passed"] is True
    assert payload["checks"]["date_range_recorded"]["passed"] is True
    assert payload["checks"]["allowed_diagnostics_recorded"]["passed"] is True
    assert payload["checks"]["forbidden_outputs_recorded"]["passed"] is True
    assert payload["checks"]["adjusted_close_policy_recorded"]["passed"] is True
    assert payload["checks"]["static_universe_survivorship_caveat_recorded"]["passed"] is True
    assert payload["checks"]["no_strategy_no_backtest_statement_recorded"]["passed"] is True
    assert payload["summary_counts"] == {
        "asset_rows": 2,
        "benchmark_rows": 2,
        "symbol_coverage": 2,
    }


def test_readiness_review_fails_fast_on_missing_required_field(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    summary_path = bundle / "summary.md"
    experiment_log_path = bundle / "experiment.json"
    summary_path.write_text("# summary\n", encoding="utf-8")
    experiment_log_path.write_text(
        json.dumps({"data_source": "EODHD local CSV private bundle"}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing experiment log fields"):
        run_eodhd_factor_diagnostics_readiness_review(
            EODHDFactorDiagnosticsReadinessReviewConfig(
                bundle_path=bundle,
                experiment_log_path=experiment_log_path,
                dry_run_summary_path=summary_path,
                review_json_path=bundle / "review.json",
                review_markdown_path=bundle / "review.md",
            )
        )
