import ast
import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

import data.csv_loader as csv_loader
from data.csv_loader import (
    CSVValidationSummary,
    ValidatedCSVFrame,
    load_benchmark_price_csv,
    load_long_price_csv,
    load_ohlcv_csv,
    load_wide_price_csv,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "local_csv_loader_smoke"


def _write_csv(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_load_wide_price_csv_returns_validated_panel_and_summary(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "prices.csv",
        "date,AAPL,MSFT\n"
        "2024-01-02,184.73,370.87\n"
        "2024-01-03,183.35,370.60\n",
    )

    result = load_wide_price_csv(csv_path)

    expected = pd.DataFrame(
        {"AAPL": [184.73, 183.35], "MSFT": [370.87, 370.60]},
        index=pd.DatetimeIndex(["2024-01-02", "2024-01-03"], name="date"),
    )
    assert_frame_equal(result.data, expected)
    assert isinstance(result.summary, CSVValidationSummary)
    assert result.summary.schema == "wide_price"
    assert result.summary.source_path == csv_path
    assert result.summary.source_row_count == 2
    assert result.summary.value_column_count == 2
    assert result.summary.missing_value_count == 0
    assert result.summary.columns == ("AAPL", "MSFT")


def test_load_wide_price_csv_rejects_remote_paths_and_non_csv_files(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="local filesystem path"):
        load_wide_price_csv("https://example.com/prices.csv")

    txt_path = _write_csv(tmp_path / "prices.txt", "date,AAPL\n2024-01-02,100\n")
    with pytest.raises(ValueError, match=".csv"):
        load_wide_price_csv(txt_path)


def test_load_wide_price_csv_rejects_missing_duplicate_or_unsorted_dates(tmp_path: Path) -> None:
    missing_date_path = _write_csv(tmp_path / "missing_date.csv", "AAPL\n100\n")
    with pytest.raises(ValueError, match="missing required columns"):
        load_wide_price_csv(missing_date_path)

    duplicate_date_path = _write_csv(
        tmp_path / "duplicate_date.csv",
        "date,AAPL\n2024-01-02,100\n2024-01-02,101\n",
    )
    with pytest.raises(ValueError, match="duplicate dates"):
        load_wide_price_csv(duplicate_date_path)

    unsorted_date_path = _write_csv(
        tmp_path / "unsorted_date.csv",
        "date,AAPL\n2024-01-03,101\n2024-01-02,100\n",
    )
    with pytest.raises(ValueError, match="sorted"):
        load_wide_price_csv(unsorted_date_path)


def test_load_wide_price_csv_rejects_duplicate_header_columns(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "duplicate_header.csv",
        "date,AAPL,AAPL\n2024-01-02,100,101\n",
    )

    with pytest.raises(ValueError, match="duplicate columns"):
        load_wide_price_csv(csv_path)


@pytest.mark.parametrize("bad_value", ["bad", "nan", "NaN", "NA", "null", "", " ", "   "])
def test_load_wide_price_csv_rejects_invalid_or_missing_numeric_values_by_default(
    tmp_path: Path,
    bad_value: str,
) -> None:
    csv_path = _write_csv(
        tmp_path / f"bad_{bad_value or 'blank'}.csv",
        f"date,AAPL\n2024-01-02,100\n2024-01-03,{bad_value}\n",
    )

    with pytest.raises((TypeError, ValueError)):
        load_wide_price_csv(csv_path)


def test_load_wide_price_csv_can_preserve_missing_values_when_explicit(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "missing_allowed.csv",
        "date,AAPL,MSFT\n2024-01-02,100,200\n2024-01-03,,201\n",
    )

    result = load_wide_price_csv(csv_path, allow_missing=True)

    assert np.isnan(result.data.loc[pd.Timestamp("2024-01-03"), "AAPL"])
    assert result.summary.missing_value_count == 1


def test_load_wide_price_csv_rejects_non_positive_prices(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "non_positive.csv",
        "date,AAPL\n2024-01-02,100\n2024-01-03,0\n",
    )

    with pytest.raises(ValueError, match="positive"):
        load_wide_price_csv(csv_path)


def test_load_long_price_csv_pivots_to_wide_panel_and_preserves_symbol_order(
    tmp_path: Path,
) -> None:
    csv_path = _write_csv(
        tmp_path / "long_prices.csv",
        "date,symbol,adjusted_close\n"
        "2024-01-03,MSFT,370.60\n"
        "2024-01-02,AAPL,184.73\n"
        "2024-01-02,MSFT,370.87\n"
        "2024-01-03,AAPL,183.35\n",
    )

    result = load_long_price_csv(csv_path)

    expected = pd.DataFrame(
        {"MSFT": [370.87, 370.60], "AAPL": [184.73, 183.35]},
        index=pd.DatetimeIndex(["2024-01-02", "2024-01-03"], name="date"),
    )
    assert_frame_equal(result.data, expected)
    assert result.summary.schema == "long_price"
    assert result.summary.source_row_count == 4
    assert result.summary.columns == ("MSFT", "AAPL")


def test_load_long_price_csv_rejects_duplicate_pairs_and_missing_symbols(
    tmp_path: Path,
) -> None:
    duplicate_path = _write_csv(
        tmp_path / "duplicate_pair.csv",
        "date,symbol,adjusted_close\n"
        "2024-01-02,AAPL,100\n"
        "2024-01-02,AAPL,101\n",
    )
    with pytest.raises(ValueError, match="duplicate"):
        load_long_price_csv(duplicate_path)

    missing_symbol_path = _write_csv(
        tmp_path / "missing_symbol.csv",
        "date,symbol,adjusted_close\n2024-01-02,,100\n",
    )
    with pytest.raises(ValueError, match="missing symbols"):
        load_long_price_csv(missing_symbol_path)


def test_load_ohlcv_csv_returns_validated_frame_and_summary() -> None:
    result = load_ohlcv_csv(FIXTURE_DIR / "synthetic_ohlcv.csv")

    expected = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03"]
            ),
            "symbol": ["AAA", "BBB", "AAA", "BBB"],
            "open": [100.00, 50.00, 100.50, 50.25],
            "high": [101.00, 50.75, 102.00, 51.00],
            "low": [99.50, 49.75, 100.00, 50.00],
            "close": [100.50, 50.25, 101.25, 50.75],
            "volume": [100000.0, 250000.0, 110000.0, 260000.0],
            "adjusted_close": [100.50, 50.25, 101.25, 50.75],
        }
    )
    assert_frame_equal(result.data, expected)
    assert isinstance(result, ValidatedCSVFrame)
    assert result.summary.schema == "ohlcv_long"
    assert result.summary.source_row_count == 4
    assert result.summary.value_column_count == 6
    assert result.summary.missing_value_count == 0
    assert result.summary.columns == (
        "open",
        "high",
        "low",
        "close",
        "volume",
        "adjusted_close",
    )


@pytest.mark.parametrize("bad_value", ["bad", "nan", "NaN", "NA", "null", "", " ", "   "])
def test_load_ohlcv_csv_rejects_invalid_or_missing_numeric_values_by_default(
    tmp_path: Path,
    bad_value: str,
) -> None:
    csv_path = _write_csv(
        tmp_path / f"bad_ohlcv_{bad_value or 'blank'}.csv",
        "date,symbol,open,high,low,close,volume\n"
        "2024-01-02,AAA,100,101,99,100.5,100000\n"
        f"2024-01-03,AAA,100.5,102,100,101.25,{bad_value}\n",
    )

    with pytest.raises((TypeError, ValueError)):
        load_ohlcv_csv(csv_path)


def test_load_ohlcv_csv_can_preserve_missing_values_when_explicit(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "ohlcv_missing_allowed.csv",
        "date,symbol,open,high,low,close,volume\n"
        "2024-01-02,AAA,100,101,99,100.5,100000\n"
        "2024-01-03,AAA,,102,100,101.25,110000\n",
    )

    result = load_ohlcv_csv(csv_path, allow_missing=True)

    assert np.isnan(result.data.loc[1, "open"])
    assert result.summary.missing_value_count == 1


def test_load_ohlcv_csv_rejects_duplicate_pairs_and_missing_symbols(
    tmp_path: Path,
) -> None:
    duplicate_path = _write_csv(
        tmp_path / "duplicate_ohlcv_pair.csv",
        "date,symbol,open,high,low,close,volume\n"
        "2024-01-02,AAA,100,101,99,100.5,100000\n"
        "2024-01-02,AAA,101,102,100,101.5,110000\n",
    )
    with pytest.raises(ValueError, match="duplicate"):
        load_ohlcv_csv(duplicate_path)

    missing_symbol_path = _write_csv(
        tmp_path / "missing_ohlcv_symbol.csv",
        "date,symbol,open,high,low,close,volume\n"
        "2024-01-02,,100,101,99,100.5,100000\n",
    )
    with pytest.raises(ValueError, match="missing symbols"):
        load_ohlcv_csv(missing_symbol_path)


def test_load_ohlcv_csv_validates_adjusted_close_policy(tmp_path: Path) -> None:
    no_adjusted_close_path = _write_csv(
        tmp_path / "ohlcv_no_adjusted_close.csv",
        "date,symbol,open,high,low,close,volume\n"
        "2024-01-02,AAA,100,101,99,100.5,100000\n",
    )
    with pytest.raises(ValueError, match="adjusted_close"):
        load_ohlcv_csv(no_adjusted_close_path, require_adjusted_close=True)

    result = load_ohlcv_csv(FIXTURE_DIR / "synthetic_ohlcv.csv", require_adjusted_close=True)

    assert "adjusted_close" in result.data.columns
    assert result.summary.columns == (
        "open",
        "high",
        "low",
        "close",
        "volume",
        "adjusted_close",
    )


def test_load_ohlcv_csv_rejects_negative_volume_but_allows_zero_volume(
    tmp_path: Path,
) -> None:
    negative_volume_path = _write_csv(
        tmp_path / "negative_volume.csv",
        "date,symbol,open,high,low,close,volume\n"
        "2024-01-02,AAA,100,101,99,100.5,-1\n",
    )
    with pytest.raises(ValueError, match="non-negative"):
        load_ohlcv_csv(negative_volume_path)

    zero_volume_path = _write_csv(
        tmp_path / "zero_volume.csv",
        "date,symbol,open,high,low,close,volume\n"
        "2024-01-02,AAA,100,101,99,100.5,0\n",
    )
    result = load_ohlcv_csv(zero_volume_path)

    assert result.data.loc[0, "volume"] == 0.0


def test_load_ohlcv_csv_rejects_non_positive_prices(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "non_positive_ohlcv.csv",
        "date,symbol,open,high,low,close,volume\n"
        "2024-01-02,AAA,0,101,99,100.5,100000\n",
    )

    with pytest.raises(ValueError, match="positive"):
        load_ohlcv_csv(csv_path)


def test_load_ohlcv_csv_rejects_impossible_ohlc_relationships(
    tmp_path: Path,
) -> None:
    csv_path = _write_csv(
        tmp_path / "bad_ohlc_relationship.csv",
        "date,symbol,open,high,low,close,volume\n"
        "2024-01-02,AAA,100,98,99,100.5,100000\n",
    )

    with pytest.raises(ValueError, match="OHLC relationship"):
        load_ohlcv_csv(csv_path)


def test_load_benchmark_price_csv_returns_validated_series(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "benchmark.csv",
        "date,benchmark_price\n2024-01-02,472.65\n2024-01-03,468.79\n",
    )

    result = load_benchmark_price_csv(csv_path)

    expected = pd.Series(
        [472.65, 468.79],
        index=pd.DatetimeIndex(["2024-01-02", "2024-01-03"], name="date"),
        name="benchmark_price",
    )
    assert_series_equal(result.data, expected)
    assert result.summary.schema == "benchmark_price"
    assert result.summary.value_column_count == 1
    assert result.summary.columns == ("benchmark_price",)


def test_load_benchmark_price_csv_rejects_bad_values(tmp_path: Path) -> None:
    bad_numeric_path = _write_csv(
        tmp_path / "bad_benchmark.csv",
        "date,benchmark_price\n2024-01-02,472.65\n2024-01-03,bad\n",
    )
    with pytest.raises(TypeError, match="numeric"):
        load_benchmark_price_csv(bad_numeric_path)

    non_positive_path = _write_csv(
        tmp_path / "non_positive_benchmark.csv",
        "date,benchmark_price\n2024-01-02,472.65\n2024-01-03,-1\n",
    )
    with pytest.raises(ValueError, match="positive"):
        load_benchmark_price_csv(non_positive_path)


def test_csv_loader_module_has_no_remote_data_or_trading_imports() -> None:
    source = inspect.getsource(csv_loader)
    tree = ast.parse(source)
    forbidden_terms = [
        "requests",
        "urllib",
        "yfinance",
        "alpaca",
        "ccxt",
        "broker",
        "brokerage",
        "order",
        "execution",
        "live_trading",
    ]

    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    for module_name in imported_modules:
        assert not any(term in module_name for term in forbidden_terms)
