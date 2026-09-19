"""Static 50-stock diagnostic cohort fixture loader.

A static survivor cohort may be used for diagnostics but not presented as
point-in-time universe evidence. This module loads a committed synthetic
manifest, stamps ``DIAGNOSTIC_ONLY``, and generates deterministic local prices.
It does not fetch data, call vendor APIs, or claim a point-in-time universe.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REQUIRED_ASSET_COUNT = 50
REQUIRED_EVIDENCE_CEILING = "DIAGNOSTIC_ONLY"
REQUIRED_REVIEW_DECISION = "diagnostic_only"
REQUIRED_GENERATION_KIND = "synthetic_local_generator"
REQUIRED_CALENDAR = "pandas_bdate_range"


def load_diagnostic_cohort_manifest(path: str | Path) -> dict[str, Any]:
    """Load and validate a static diagnostic-cohort manifest.

    The manifest must declare ``DIAGNOSTIC_ONLY``, survivorship bias, and that
    it is not point-in-time universe evidence. It must list exactly 50 unique
    identifiers.
    """

    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"diagnostic cohort manifest not found: {manifest_path}")

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("diagnostic cohort manifest must be a JSON object")

    return _validate_diagnostic_cohort_manifest(payload)


def generate_diagnostic_cohort_prices(manifest: Mapping[str, Any]) -> pd.DataFrame:
    """Generate deterministic synthetic prices for a validated diagnostic cohort.

    Prices are local synthetic draws from the manifest seed. They are not real
    market data and are not a point-in-time membership record.
    """

    validated = _validate_diagnostic_cohort_manifest(manifest)
    generation = validated["generation"]
    identifiers = list(validated["identifiers"])
    periods = int(generation["periods"])
    rng = np.random.default_rng(int(generation["seed"]))
    dates = pd.bdate_range(str(generation["start_date"]), periods=periods)
    asset_count = len(identifiers)

    market_component = rng.normal(loc=0.0002, scale=0.0060, size=(periods, 1))
    asset_noise = rng.normal(loc=0.0, scale=0.0120, size=(periods, asset_count))
    asset_drifts = rng.normal(loc=0.00005, scale=0.00020, size=(1, asset_count))
    log_returns = market_component + asset_noise + asset_drifts
    prices = float(generation["starting_price"]) * np.exp(np.cumsum(log_returns, axis=0))
    return pd.DataFrame(prices, index=dates, columns=identifiers)


def load_diagnostic_cohort(path: str | Path) -> tuple[dict[str, Any], pd.DataFrame]:
    """Load a validated diagnostic-cohort manifest and its synthetic price panel."""

    manifest = load_diagnostic_cohort_manifest(path)
    return manifest, generate_diagnostic_cohort_prices(manifest)


def _validate_diagnostic_cohort_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    required_text = {
        "cohort_id": str,
        "evidence_ceiling": str,
        "review_decision": str,
        "universe_status": str,
    }
    for field_name, expected_type in required_text.items():
        value = manifest.get(field_name)
        if not isinstance(value, expected_type) or not value:
            raise ValueError(f"{field_name} must be a nonempty string")

    if manifest["evidence_ceiling"] != REQUIRED_EVIDENCE_CEILING:
        raise ValueError("evidence_ceiling must be DIAGNOSTIC_ONLY")
    if manifest["review_decision"] != REQUIRED_REVIEW_DECISION:
        raise ValueError("review_decision must be diagnostic_only")
    if manifest.get("dataset_manifest_reviewed") is not False:
        raise ValueError("dataset_manifest_reviewed must be false")
    if manifest.get("formal_interpretation_eligible") is not False:
        raise ValueError("formal_interpretation_eligible must be false")
    if manifest.get("survivorship_bias") is not True:
        raise ValueError("survivorship_bias must be true")
    if manifest.get("not_point_in_time_universe_evidence") is not True:
        raise ValueError("not_point_in_time_universe_evidence must be true")

    identifiers = manifest.get("identifiers")
    if not isinstance(identifiers, list) or not identifiers:
        raise ValueError("identifiers must be a nonempty list")
    if any(not isinstance(item, str) or not item for item in identifiers):
        raise ValueError("identifiers must contain nonempty strings")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("identifiers must be unique")

    asset_count = manifest.get("asset_count")
    if isinstance(asset_count, bool) or not isinstance(asset_count, int):
        raise TypeError("asset_count must be an integer")
    if asset_count != REQUIRED_ASSET_COUNT or len(identifiers) != REQUIRED_ASSET_COUNT:
        raise ValueError(f"diagnostic cohort must contain exactly {REQUIRED_ASSET_COUNT} assets")

    generation = manifest.get("generation")
    if not isinstance(generation, dict):
        raise TypeError("generation must be an object")
    if generation.get("kind") != REQUIRED_GENERATION_KIND:
        raise ValueError("generation.kind must be synthetic_local_generator")
    if generation.get("calendar") != REQUIRED_CALENDAR:
        raise ValueError("generation.calendar must be pandas_bdate_range")

    seed = generation.get("seed")
    periods = generation.get("periods")
    starting_price = generation.get("starting_price")
    start_date = generation.get("start_date")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("generation.seed must be an integer")
    if isinstance(periods, bool) or not isinstance(periods, int) or periods < 2:
        raise ValueError("generation.periods must be an integer of at least 2")
    if isinstance(starting_price, bool) or not isinstance(starting_price, (int, float)):
        raise TypeError("generation.starting_price must be a real number")
    if float(starting_price) <= 0.0:
        raise ValueError("generation.starting_price must be positive")
    if not isinstance(start_date, str) or not start_date:
        raise ValueError("generation.start_date must be a nonempty string")

    return {
        "cohort_id": manifest["cohort_id"],
        "evidence_ceiling": REQUIRED_EVIDENCE_CEILING,
        "review_decision": REQUIRED_REVIEW_DECISION,
        "dataset_manifest_reviewed": False,
        "formal_interpretation_eligible": False,
        "universe_status": manifest["universe_status"],
        "survivorship_bias": True,
        "not_point_in_time_universe_evidence": True,
        "asset_count": REQUIRED_ASSET_COUNT,
        "identifiers": list(identifiers),
        "generation": {
            "kind": REQUIRED_GENERATION_KIND,
            "seed": int(seed),
            "start_date": start_date,
            "periods": int(periods),
            "starting_price": float(starting_price),
            "calendar": REQUIRED_CALENDAR,
        },
    }


__all__ = [
    "REQUIRED_ASSET_COUNT",
    "REQUIRED_EVIDENCE_CEILING",
    "generate_diagnostic_cohort_prices",
    "load_diagnostic_cohort",
    "load_diagnostic_cohort_manifest",
]
