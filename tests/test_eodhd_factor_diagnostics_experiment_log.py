import json
from pathlib import Path

import pytest

from research.eodhd_factor_diagnostics_experiment_log import (
    EODHDFactorDiagnosticsExperimentLogConfig,
    run_eodhd_factor_diagnostics_experiment_log,
)


def test_writes_private_experiment_log_from_factor_diagnostics_summary(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    normalized = bundle / "normalized"
    normalized.mkdir(parents=True)
    ohlcv_path = normalized / "eodhd_ohlcv_long.csv"
    benchmark_path = normalized / "eodhd_benchmark_spy.csv"
    summary_path = bundle / "FACTOR_DIAGNOSTICS_DRY_RUN_SUMMARY.md"
    log_path = bundle / "FACTOR_DIAGNOSTICS_EXPERIMENT_LOG.json"
    markdown_path = bundle / "FACTOR_DIAGNOSTICS_EXPERIMENT_LOG.md"

    ohlcv_path.write_text(
        "\n".join(
            [
                "date,symbol,open,high,low,close,adjusted_close,volume",
                "2020-01-02,AAPL.US,1,1,1,1,1,10",
                "2020-01-03,AAPL.US,2,2,2,2,2,20",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    benchmark_path.write_text(
        "\n".join(
            [
                "date,symbol,open,high,low,close,adjusted_close,volume",
                "2020-01-02,SPY.US,1,1,1,1,1,10",
                "2020-01-03,SPY.US,2,2,2,2,2,20",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    summary_path.write_text(
        "\n".join(
            [
                "# EODHD Factor Diagnostics Dry Run Summary",
                "",
                "## Private Inputs",
                "",
                f"- OHLCV: `{ohlcv_path}`",
                f"- Benchmark: `{benchmark_path}`",
                f"- Output: `{summary_path}`",
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
                "| alpha_012 | 2 | 1 | 2 | 0 |",
                "",
                "## Split Diagnostics",
                "",
                "| factor | split | date_count | ic_valid_dates | rank_ic_valid_dates | quantile_spread_valid_dates |",
                "| --- | --- | --- | --- | --- | --- |",
                "| alpha_009 | train | 2 | 1 | 1 | 1 |",
                "| alpha_012 | validation | 2 | 1 | 1 | 1 |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    payload = run_eodhd_factor_diagnostics_experiment_log(
        EODHDFactorDiagnosticsExperimentLogConfig(
            bundle_path=bundle,
            summary_path=summary_path,
            log_path=log_path,
            markdown_path=markdown_path,
            run_label="unit-test-run",
        )
    )

    assert log_path.exists()
    assert markdown_path.exists()
    assert json.loads(log_path.read_text(encoding="utf-8")) == payload
    assert payload["run_label"] == "unit-test-run"
    assert payload["data_source"] == "EODHD local CSV private bundle"
    assert payload["local_private_bundle_path"] == str(bundle)
    assert payload["input_file_paths"]["factor_diagnostics_summary"] == str(summary_path)
    assert payload["input_file_paths"]["ohlcv"] == str(ohlcv_path)
    assert payload["input_file_paths"]["benchmark"] == str(benchmark_path)
    assert payload["output_file_paths"]["experiment_log_json"] == str(log_path)
    assert payload["output_file_paths"]["experiment_log_markdown"] == str(markdown_path)
    assert payload["symbol_coverage"] == 2
    assert payload["row_counts"] == {"asset_rows": 2, "benchmark_rows": 2}
    assert payload["date_range"] == {"start": "2020-01-02", "end": "2020-01-03"}
    assert payload["factor_diagnostics_stage_name"] == "EODHD factor diagnostics dry run"
    assert payload["allowed_diagnostics"] == [
        "factor coverage",
        "factor missingness",
        "IC",
        "Rank IC",
        "quantile spread",
        "split labels",
    ]
    assert "Sharpe" in payload["forbidden_interpretations"]
    assert "adjusted_close" in payload["adjusted_close_policy"]
    assert "static" in payload["static_universe_survivorship_caveat"]
    assert "No strategy" in payload["no_strategy_no_backtest_statement"]
    assert payload["next_checkpoint"]
    assert "alpha_009" in payload["factor_coverage"]
    assert payload["split_labels"] == ["train", "validation"]


def test_experiment_log_rejects_repo_output_path(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.md"
    summary_path.write_text("# summary\n", encoding="utf-8")

    with pytest.raises(ValueError, match="log_path must be under bundle_path"):
        run_eodhd_factor_diagnostics_experiment_log(
            EODHDFactorDiagnosticsExperimentLogConfig(
                bundle_path=tmp_path,
                summary_path=summary_path,
                log_path=Path(__file__).resolve(),
                markdown_path=tmp_path / "out.md",
            )
        )
