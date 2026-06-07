from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_index_equal

from data.csv_loader import (
    load_benchmark_price_csv,
    load_ohlcv_csv,
    load_wide_price_csv,
)
from features.worldquant_alphas import alpha_012


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "local_csv_loader_smoke"


def _write_csv(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _pivot_ohlcv_panel(frame: pd.DataFrame, value_column: str) -> pd.DataFrame:
    panel = frame.pivot(index="date", columns="symbol", values=value_column)
    panel.columns.name = None
    return panel


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


def test_local_synthetic_ohlcv_fixture_loads_with_expected_audit_summary() -> None:
    result = load_ohlcv_csv(
        FIXTURE_DIR / "synthetic_ohlcv.csv",
        require_adjusted_close=True,
    )

    assert list(result.data.columns) == [
        "date",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "adjusted_close",
    ]
    assert result.data["date"].tolist() == [
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-03"),
    ]
    assert result.data["symbol"].tolist() == ["AAA", "BBB", "AAA", "BBB"]
    assert not result.data[["date", "symbol"]].duplicated().any()

    numeric_columns = ["open", "high", "low", "close", "volume", "adjusted_close"]
    assert result.data[numeric_columns].dtypes.eq(float).all()
    assert result.data.loc[2, "close"] == 101.25
    assert result.data.loc[3, "volume"] == 260000.0

    assert (result.data["high"] >= result.data["low"]).all()
    assert (result.data["high"] >= result.data["open"]).all()
    assert (result.data["high"] >= result.data["close"]).all()
    assert (result.data["low"] <= result.data["open"]).all()
    assert (result.data["low"] <= result.data["close"]).all()

    assert result.summary.schema == "ohlcv_long"
    assert result.summary.source_path == FIXTURE_DIR / "synthetic_ohlcv.csv"
    assert result.summary.source_row_count == 4
    assert result.summary.value_column_count == 6
    assert result.summary.start_date == pd.Timestamp("2024-01-02")
    assert result.summary.end_date == pd.Timestamp("2024-01-03")
    assert result.summary.missing_value_count == 0
    assert result.summary.columns == (
        "open",
        "high",
        "low",
        "close",
        "volume",
        "adjusted_close",
    )


def test_local_synthetic_ohlcv_fixture_computes_alpha_012_feature_only() -> None:
    result = load_ohlcv_csv(
        FIXTURE_DIR / "synthetic_ohlcv.csv",
        require_adjusted_close=True,
    )

    close = _pivot_ohlcv_panel(result.data, "adjusted_close")
    volume = _pivot_ohlcv_panel(result.data, "volume")
    alpha = alpha_012(close, volume)

    assert_index_equal(
        alpha.index,
        pd.DatetimeIndex(["2024-01-02", "2024-01-03"], name="date"),
    )
    assert alpha.columns.tolist() == ["AAA", "BBB"]
    assert alpha.loc[pd.Timestamp("2024-01-02"), ["AAA", "BBB"]].isna().all()
    assert alpha.loc[pd.Timestamp("2024-01-03"), "AAA"] == pytest.approx(-0.75)
    assert alpha.loc[pd.Timestamp("2024-01-03"), "BBB"] == pytest.approx(-0.50)


def test_local_synthetic_ohlcv_fixture_missing_values_require_explicit_policy(
    tmp_path: Path,
) -> None:
    missing_fixture = _write_csv(
        tmp_path / "synthetic_ohlcv_with_missing.csv",
        "date,symbol,open,high,low,close,volume,adjusted_close\n"
        "2024-01-02,AAA,100.00,101.00,99.50,100.50,100000,100.50\n"
        "2024-01-03,AAA,,102.00,100.00,101.25,110000,101.25\n",
    )

    with pytest.raises(ValueError, match="missing values"):
        load_ohlcv_csv(missing_fixture)

    result = load_ohlcv_csv(missing_fixture, allow_missing=True)

    assert result.summary.missing_value_count == 1
    assert np.isnan(result.data.loc[1, "open"])


def test_local_synthetic_ohlcv_smoke_demo_rejects_impossible_relationships(
    tmp_path: Path,
) -> None:
    invalid_fixture = _write_csv(
        tmp_path / "synthetic_ohlcv_invalid_relationship.csv",
        "date,symbol,open,high,low,close,volume,adjusted_close\n"
        "2024-01-02,AAA,100.00,99.00,99.50,100.50,100000,100.50\n",
    )

    with pytest.raises(ValueError, match="OHLC relationship"):
        load_ohlcv_csv(invalid_fixture)
