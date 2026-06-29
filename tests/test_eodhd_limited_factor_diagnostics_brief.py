import json
from pathlib import Path

import pytest

from research.eodhd_limited_factor_diagnostics_brief import (
    EODHDLimitedFactorDiagnosticsBriefConfig,
    run_eodhd_limited_factor_diagnostics_brief,
)


def test_writes_neutral_limited_factor_diagnostics_brief(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    limited_review_path = bundle / "LIMITED_FACTOR_DIAGNOSTICS_REVIEW.json"
    readiness_review_path = bundle / "FACTOR_DIAGNOSTICS_READINESS_REVIEW.json"
    experiment_log_path = bundle / "FACTOR_DIAGNOSTICS_EXPERIMENT_LOG.json"
    output_json_path = bundle / "LIMITED_FACTOR_DIAGNOSTICS_BRIEF.json"
    output_markdown_path = bundle / "LIMITED_FACTOR_DIAGNOSTICS_BRIEF.md"

    readiness_review_path.write_text(
        json.dumps({"ready_for_limited_factor_diagnostics_review": True}) + "\n",
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
            }
        )
        + "\n",
        encoding="utf-8",
    )
    limited_review_path.write_text(
        json.dumps(
            {
                "review_scope": "limited_factor_diagnostics_review",
                "diagnostics_are_research_only": True,
                "summary_counts": {
                    "asset_rows": 6,
                    "benchmark_rows": 3,
                    "symbol_coverage": 3,
                },
                "date_range": {"start": "2020-01-02", "end": "2020-01-06"},
                "factor_coverage": {
                    "alpha_009": {
                        "date_count": 3,
                        "asset_count": 2,
                        "valid_observations": 4,
                        "missing_observations": 2,
                        "total_observations": 6,
                        "missing_fraction": 1 / 3,
                    },
                    "alpha_012": {
                        "date_count": 3,
                        "asset_count": 2,
                        "valid_observations": 5,
                        "missing_observations": 1,
                        "total_observations": 6,
                        "missing_fraction": 1 / 6,
                    },
                },
                "factor_missingness": {
                    "alpha_009": {
                        "missing_observations": 2,
                        "total_observations": 6,
                        "missing_fraction": 1 / 3,
                    },
                    "alpha_012": {
                        "missing_observations": 1,
                        "total_observations": 6,
                        "missing_fraction": 1 / 6,
                    },
                },
                "split_labels": ["train", "validation"],
                "split_diagnostics": [
                    {
                        "factor": "alpha_009",
                        "split": "train",
                        "mean_ic": 0.10,
                        "mean_rank_ic": 0.20,
                        "mean_quantile_spread": 0.30,
                        "ic_valid_dates": 2,
                        "rank_ic_valid_dates": 2,
                        "quantile_spread_valid_dates": 2,
                    },
                    {
                        "factor": "alpha_009",
                        "split": "validation",
                        "mean_ic": -0.05,
                        "mean_rank_ic": 0.10,
                        "mean_quantile_spread": 0.15,
                        "ic_valid_dates": 1,
                        "rank_ic_valid_dates": 1,
                        "quantile_spread_valid_dates": 1,
                    },
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = run_eodhd_limited_factor_diagnostics_brief(
        EODHDLimitedFactorDiagnosticsBriefConfig(
            bundle_path=bundle,
            limited_review_path=limited_review_path,
            readiness_review_path=readiness_review_path,
            experiment_log_path=experiment_log_path,
            output_json_path=output_json_path,
            output_markdown_path=output_markdown_path,
        )
    )

    assert json.loads(output_json_path.read_text(encoding="utf-8")) == payload
    assert output_markdown_path.exists()
    assert payload["brief_scope"] == "limited_factor_diagnostics_brief"
    assert payload["diagnostics_are_research_only"] is True
    assert payload["factor_count"] == 2
    assert payload["split_labels"] == ["train", "validation"]
    assert payload["summary_counts"] == {
        "asset_rows": 6,
        "benchmark_rows": 3,
        "symbol_coverage": 3,
    }
    assert payload["date_range"] == {"start": "2020-01-02", "end": "2020-01-06"}
    assert payload["factor_briefs"]["alpha_009"]["coverage"]["valid_observations"] == 4
    assert payload["factor_briefs"]["alpha_009"]["missingness"]["missing_observations"] == 2
    assert payload["factor_briefs"]["alpha_009"]["diagnostics"]["mean_ic"]["split_consistency"] == "mixed_sign"
    assert payload["factor_briefs"]["alpha_009"]["diagnostics"]["mean_rank_ic"]["split_consistency"] == "positive"
    first_ic = payload["factor_briefs"]["alpha_009"]["diagnostics"]["mean_ic"]["by_split"][0]
    assert first_ic == {
        "split": "train",
        "value": 0.10,
        "direction": "positive",
        "magnitude": 0.10,
        "valid_dates": 2,
    }
    assert "ready_for_trading" not in payload
    assert "ready_for_strategy" not in payload
    assert "ready_for_alpha" not in payload
    assert "ready_for_live_use" not in payload
    assert "No strategy" in payload["no_strategy_no_performance_statement"]


def test_brief_rejects_non_limited_review_scope(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    limited_review_path = bundle / "limited.json"
    readiness_review_path = bundle / "readiness.json"
    experiment_log_path = bundle / "experiment.json"
    limited_review_path.write_text(
        json.dumps({"review_scope": "strategy_review"}) + "\n",
        encoding="utf-8",
    )
    readiness_review_path.write_text("{}\n", encoding="utf-8")
    experiment_log_path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="limited review scope"):
        run_eodhd_limited_factor_diagnostics_brief(
            EODHDLimitedFactorDiagnosticsBriefConfig(
                bundle_path=bundle,
                limited_review_path=limited_review_path,
                readiness_review_path=readiness_review_path,
                experiment_log_path=experiment_log_path,
                output_json_path=bundle / "brief.json",
                output_markdown_path=bundle / "brief.md",
            )
        )
