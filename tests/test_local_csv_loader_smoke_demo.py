from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_index_equal

from data.csv_loader import load_benchmark_price_csv, load_wide_price_csv


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "local_csv_loader_smoke"


def test_local_synthetic_wide_price_fixture_loads_with_expected_audit_summary() -> None:
    result = load_wide_price_csv(FIXTURE_DIR / "synthetic_adjusted_close.csv")

    assert list(result.data.columns) == ["AAA", "BBB", "CCC"]
    assert_index_equal(
        result.data.index,
        pd.DatetimeIndex(
            ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            name="date",
        ),
    )
    assert result.data.dtypes.eq(float).all()
    assert result.data.loc[pd.Timestamp("2024-01-05"), "AAA"] == 103.50

    assert result.summary.schema == "wide_price"
    assert result.summary.source_path == FIXTURE_DIR / "synthetic_adjusted_close.csv"
    assert result.summary.source_row_count == 4
    assert result.summary.value_column_count == 3
    assert result.summary.start_date == pd.Timestamp("2024-01-02")
    assert result.summary.end_date == pd.Timestamp("2024-01-05")
    assert result.summary.missing_value_count == 0
    assert result.summary.columns == ("AAA", "BBB", "CCC")


def test_local_synthetic_benchmark_fixture_aligns_to_wide_price_dates() -> None:
    prices = load_wide_price_csv(FIXTURE_DIR / "synthetic_adjusted_close.csv")
    benchmark = load_benchmark_price_csv(FIXTURE_DIR / "synthetic_benchmark.csv")

    assert benchmark.summary.schema == "benchmark_price"
    assert benchmark.summary.source_row_count == 4
    assert benchmark.summary.value_column_count == 1
    assert benchmark.summary.missing_value_count == 0
    assert benchmark.summary.columns == ("benchmark_price",)
    assert_index_equal(benchmark.data.index, prices.data.index)
    assert benchmark.data.dtype == float
    assert benchmark.data.loc[pd.Timestamp("2024-01-05")] == 303.75


def test_local_synthetic_fixture_missing_values_require_explicit_policy() -> None:
    missing_fixture = FIXTURE_DIR / "synthetic_adjusted_close_with_missing.csv"

    with pytest.raises(ValueError, match="missing values"):
        load_wide_price_csv(missing_fixture)

    result = load_wide_price_csv(missing_fixture, allow_missing=True)

    assert result.summary.missing_value_count == 1
    assert np.isnan(result.data.loc[pd.Timestamp("2024-01-03"), "BBB"])
    assert result.data.loc[pd.Timestamp("2024-01-02"), "BBB"] == 50.00
    assert result.data.loc[pd.Timestamp("2024-01-04"), "BBB"] == 50.50
