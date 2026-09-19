import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data.diagnostic_cohort import (
    REQUIRED_ASSET_COUNT,
    REQUIRED_EVIDENCE_CEILING,
    generate_diagnostic_cohort_ohlcv,
    generate_diagnostic_cohort_prices,
    load_diagnostic_cohort,
    load_diagnostic_cohort_manifest,
    load_diagnostic_cohort_ohlcv,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "walking_skeleton" / "diagnostic_cohort_v1.json"
)


def test_committed_diagnostic_cohort_is_fifty_names_and_diagnostic_only() -> None:
    manifest, prices = load_diagnostic_cohort(DEFAULT_MANIFEST_PATH)

    assert manifest["evidence_ceiling"] == REQUIRED_EVIDENCE_CEILING
    assert manifest["dataset_manifest_reviewed"] is False
    assert manifest["formal_interpretation_eligible"] is False
    assert manifest["survivorship_bias"] is True
    assert manifest["not_point_in_time_universe_evidence"] is True
    assert manifest["asset_count"] == REQUIRED_ASSET_COUNT
    assert len(manifest["identifiers"]) == REQUIRED_ASSET_COUNT
    assert prices.shape == (manifest["generation"]["periods"], REQUIRED_ASSET_COUNT)
    assert list(prices.columns) == manifest["identifiers"]
    assert isinstance(prices.index, pd.DatetimeIndex)
    assert prices.min().min() > 0.0


def test_diagnostic_cohort_prices_are_deterministic() -> None:
    first = generate_diagnostic_cohort_prices(
        load_diagnostic_cohort_manifest(DEFAULT_MANIFEST_PATH)
    )
    second = generate_diagnostic_cohort_prices(
        load_diagnostic_cohort_manifest(DEFAULT_MANIFEST_PATH)
    )

    pd.testing.assert_frame_equal(first, second)


def test_diagnostic_cohort_ohlcv_matches_close_prices_and_stays_positive() -> None:
    manifest = load_diagnostic_cohort_manifest(DEFAULT_MANIFEST_PATH)
    prices = generate_diagnostic_cohort_prices(manifest)
    first = generate_diagnostic_cohort_ohlcv(manifest)
    second = generate_diagnostic_cohort_ohlcv(manifest)
    loaded_manifest, loaded_panels = load_diagnostic_cohort_ohlcv(DEFAULT_MANIFEST_PATH)

    pd.testing.assert_frame_equal(first["close"], prices)
    pd.testing.assert_frame_equal(first["close"], second["close"])
    pd.testing.assert_frame_equal(first["open"], second["open"])
    pd.testing.assert_frame_equal(first["volume"], second["volume"])
    assert loaded_manifest["evidence_ceiling"] == REQUIRED_EVIDENCE_CEILING
    pd.testing.assert_frame_equal(loaded_panels["close"], prices)
    assert (first["open"] > 0.0).all().all()
    assert (first["low"] > 0.0).all().all()
    assert (first["volume"] > 0.0).all().all()
    assert (
        first["low"].to_numpy()
        <= np.minimum(first["open"].to_numpy(), first["close"].to_numpy()) + 1e-12
    ).all()


def test_diagnostic_cohort_rejects_non_diagnostic_ceiling(tmp_path: Path) -> None:
    payload = json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))
    payload["evidence_ceiling"] = "RESEARCH_PASS"
    bad_path = tmp_path / "bad_cohort.json"
    bad_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="DIAGNOSTIC_ONLY"):
        load_diagnostic_cohort_manifest(bad_path)


def test_diagnostic_cohort_rejects_point_in_time_universe_claim(tmp_path: Path) -> None:
    payload = json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))
    payload["not_point_in_time_universe_evidence"] = False
    bad_path = tmp_path / "pit_claim.json"
    bad_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="not_point_in_time_universe_evidence"):
        load_diagnostic_cohort_manifest(bad_path)


def test_diagnostic_cohort_rejects_wrong_asset_count(tmp_path: Path) -> None:
    payload = json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))
    payload["identifiers"] = payload["identifiers"][:49]
    payload["asset_count"] = 49
    bad_path = tmp_path / "short_cohort.json"
    bad_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="exactly 50"):
        load_diagnostic_cohort_manifest(bad_path)
