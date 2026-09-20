import ast
import inspect
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from data.bluechip_cohort import (
    BENCHMARK_SYMBOL,
    BLUECHIP_50_COHORT,
    get_bluechip_50_symbols,
)
from data.parquet_loader import (
    DataIntegrityError,
    load_eod_cohort_panels,
    load_eod_parquet,
)
import data.parquet_loader as parquet_loader


def _sample_frame(
    dates: list[str],
    *,
    open_: float = 100.0,
    high: float = 101.0,
    low: float = 99.0,
    close: float = 100.5,
    adjusted_close: float = 100.4,
    volume: float = 1_000.0,
    **overrides: object,
) -> pd.DataFrame:
    count = len(dates)
    data: dict[str, object] = {
        "date": pd.to_datetime(dates),
        "open": np.full(count, open_, dtype=float),
        "high": np.full(count, high, dtype=float),
        "low": np.full(count, low, dtype=float),
        "close": np.full(count, close, dtype=float),
        "adjusted_close": np.full(count, adjusted_close, dtype=float),
        "volume": np.full(count, volume, dtype=float),
    }
    data.update(overrides)
    return pd.DataFrame(data)


def _write_parquet(path: Path, frame: pd.DataFrame) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False, engine="pyarrow")
    return path


def test_load_eod_parquet_returns_standardized_date_indexed_frame(tmp_path: Path) -> None:
    csv_like = _sample_frame(
        ["2024-01-02", "2024-01-03"],
        open_=184.0,
        high=186.0,
        low=183.0,
        close=185.0,
        adjusted_close=184.5,
        volume=10_000.0,
    )
    csv_like["extra"] = [1.0, 2.0]
    path = _write_parquet(tmp_path / "AAPL.US.parquet", csv_like)

    loaded = load_eod_parquet(path)

    expected = pd.DataFrame(
        {
            "open": [184.0, 184.0],
            "high": [186.0, 186.0],
            "low": [183.0, 183.0],
            "close": [185.0, 185.0],
            "adjusted_close": [184.5, 184.5],
            "volume": [10_000.0, 10_000.0],
        },
        index=pd.DatetimeIndex(["2024-01-02", "2024-01-03"], name="date"),
    )
    assert_frame_equal(loaded, expected)
    assert list(loaded.columns) == [
        "open",
        "high",
        "low",
        "close",
        "adjusted_close",
        "volume",
    ]
    assert isinstance(loaded.index, pd.DatetimeIndex)
    assert loaded.index.tz is None
    assert loaded.index.name == "date"
    assert loaded.index.is_monotonic_increasing
    assert not loaded.index.has_duplicates


def test_load_eod_parquet_accepts_date_index_without_date_column(tmp_path: Path) -> None:
    frame = _sample_frame(["2024-01-02", "2024-01-03"]).set_index("date")
    path = tmp_path / "indexed.parquet"
    frame.to_parquet(path, engine="pyarrow")

    loaded = load_eod_parquet(path)

    assert list(loaded.index) == list(pd.to_datetime(["2024-01-02", "2024-01-03"]))
    assert loaded.index.name == "date"


def test_load_eod_parquet_converts_timezone_aware_dates_to_naive(tmp_path: Path) -> None:
    frame = _sample_frame(["2024-01-02", "2024-01-03"])
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    path = _write_parquet(tmp_path / "tz.parquet", frame)

    loaded = load_eod_parquet(path)

    assert loaded.index.tz is None
    assert list(loaded.index) == list(pd.to_datetime(["2024-01-02", "2024-01-03"]))


def test_load_eod_parquet_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_eod_parquet(tmp_path / "missing.parquet")


def test_load_eod_parquet_rejects_remote_paths_and_non_parquet_files(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="local filesystem path"):
        load_eod_parquet("https://example.com/AAPL.US.parquet")

    other = tmp_path / "prices.csv"
    other.write_text("date,open\n2024-01-02,100\n", encoding="utf-8")
    with pytest.raises(ValueError, match=".parquet"):
        load_eod_parquet(other)


def test_load_eod_parquet_missing_required_columns_raise_value_error(tmp_path: Path) -> None:
    frame = _sample_frame(["2024-01-02"]).drop(columns=["adjusted_close"])
    path = _write_parquet(tmp_path / "missing_column.parquet", frame)

    with pytest.raises(ValueError, match="missing required columns"):
        load_eod_parquet(path)


@pytest.mark.parametrize("column", ["open", "high", "low", "close", "adjusted_close"])
@pytest.mark.parametrize("bad_value", [0.0, -1.0])
def test_load_eod_parquet_non_positive_prices_raise_value_error(
    tmp_path: Path,
    column: str,
    bad_value: float,
) -> None:
    frame = _sample_frame(["2024-01-02", "2024-01-03"])
    frame.loc[1, column] = bad_value
    path = _write_parquet(tmp_path / f"non_positive_{column}_{bad_value}.parquet", frame)

    with pytest.raises(ValueError, match="strictly positive"):
        load_eod_parquet(path)


@pytest.mark.parametrize("bad_value", [np.inf, -np.inf, np.nan])
def test_load_eod_parquet_non_finite_prices_raise_value_error(
    tmp_path: Path,
    bad_value: float,
) -> None:
    frame = _sample_frame(["2024-01-02", "2024-01-03"])
    frame.loc[1, "close"] = bad_value
    path = _write_parquet(tmp_path / "non_finite_close.parquet", frame)

    with pytest.raises(ValueError, match="finite"):
        load_eod_parquet(path)


def test_load_eod_parquet_negative_volume_raises_value_error(tmp_path: Path) -> None:
    frame = _sample_frame(["2024-01-02", "2024-01-03"])
    frame.loc[1, "volume"] = -1.0
    path = _write_parquet(tmp_path / "negative_volume.parquet", frame)

    with pytest.raises(ValueError, match="non-negative"):
        load_eod_parquet(path)


def test_load_eod_parquet_zero_volume_is_accepted(tmp_path: Path) -> None:
    frame = _sample_frame(["2024-01-02"], volume=0.0)
    path = _write_parquet(tmp_path / "zero_volume.parquet", frame)

    loaded = load_eod_parquet(path)

    assert loaded.loc[pd.Timestamp("2024-01-02"), "volume"] == 0.0


def test_load_eod_parquet_duplicate_dates_raise_value_error(tmp_path: Path) -> None:
    frame = _sample_frame(["2024-01-02", "2024-01-02"])
    path = _write_parquet(tmp_path / "duplicate_dates.parquet", frame)

    with pytest.raises(ValueError, match="duplicate dates"):
        load_eod_parquet(path)


def test_load_eod_parquet_unordered_dates_raise_value_error(tmp_path: Path) -> None:
    frame = _sample_frame(["2024-01-03", "2024-01-02"])
    path = _write_parquet(tmp_path / "unordered_dates.parquet", frame)

    with pytest.raises(ValueError, match="sorted"):
        load_eod_parquet(path)


def test_load_eod_parquet_boolean_price_column_raises_value_error(tmp_path: Path) -> None:
    frame = _sample_frame(["2024-01-02", "2024-01-03"])
    frame["close"] = pd.Series([True, False], dtype=bool)
    path = _write_parquet(tmp_path / "boolean_close.parquet", frame)

    with pytest.raises(ValueError, match="boolean"):
        load_eod_parquet(path)


def test_data_integrity_error_is_a_value_error() -> None:
    assert issubclass(DataIntegrityError, ValueError)


def test_load_eod_cohort_panels_aligns_inventory_mapped_files(tmp_path: Path) -> None:
    data_dir = tmp_path / "eod"
    aaa = _sample_frame(
        ["2024-01-02", "2024-01-03", "2024-01-04"],
        close=10.0,
        adjusted_close=10.0,
        volume=100.0,
    )
    bbb = _sample_frame(
        ["2024-01-03", "2024-01-04", "2024-01-05"],
        close=20.0,
        adjusted_close=20.0,
        volume=200.0,
    )
    _write_parquet(data_dir / "nested" / "AAA.US.parquet", aaa)
    _write_parquet(data_dir / "BBB.US.parquet", bbb)
    inventory_path = tmp_path / "per_stock_coverage.json"
    inventory_path.write_text(
        json.dumps(
            {
                "stocks": [
                    {"symbol": "AAA.US", "file": "nested/AAA.US.parquet"},
                    {"symbol": "BBB.US", "file": "BBB.US.parquet"},
                ]
            }
        ),
        encoding="utf-8",
    )

    panels = load_eod_cohort_panels(
        data_dir,
        ["AAA.US", "BBB.US"],
        inventory_path=inventory_path,
    )

    expected_index = pd.DatetimeIndex(
        ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
        name="date",
    )
    assert list(panels) == [
        "open",
        "high",
        "low",
        "close",
        "adjusted_close",
        "volume",
    ]
    for field, panel in panels.items():
        assert list(panel.columns) == ["AAA.US", "BBB.US"]
        assert panel.index.equals(expected_index)
        assert panel.index.name == "date"
        assert panel.index.freq is None

    assert_series_equal(
        panels["close"]["AAA.US"],
        pd.Series(
            [10.0, 10.0, 10.0, np.nan],
            index=expected_index,
            name="AAA.US",
        ),
    )
    assert_series_equal(
        panels["close"]["BBB.US"],
        pd.Series(
            [np.nan, 20.0, 20.0, 20.0],
            index=expected_index,
            name="BBB.US",
        ),
    )
    assert_frame_equal(
        panels["volume"],
        pd.DataFrame(
            {"AAA.US": [100.0, 100.0, 100.0, np.nan], "BBB.US": [np.nan, 200.0, 200.0, 200.0]},
            index=expected_index,
        ),
    )


def test_load_eod_cohort_panels_uses_direct_and_lowercase_filenames(tmp_path: Path) -> None:
    data_dir = tmp_path / "eod"
    _write_parquet(data_dir / "AAA.US.parquet", _sample_frame(["2024-01-02"], close=11.0))
    _write_parquet(data_dir / "bbb.us.parquet", _sample_frame(["2024-01-02"], close=22.0))

    panels = load_eod_cohort_panels(data_dir, ["AAA.US", "BBB.US"])

    assert panels["close"].loc[pd.Timestamp("2024-01-02"), "AAA.US"] == 11.0
    assert panels["close"].loc[pd.Timestamp("2024-01-02"), "BBB.US"] == 22.0


def test_load_eod_cohort_panels_filters_inclusive_start_and_end_dates(tmp_path: Path) -> None:
    data_dir = tmp_path / "eod"
    _write_parquet(
        data_dir / "AAA.US.parquet",
        _sample_frame(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]),
    )
    _write_parquet(
        data_dir / "BBB.US.parquet",
        _sample_frame(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]),
    )

    panels = load_eod_cohort_panels(
        data_dir,
        ["AAA.US", "BBB.US"],
        start_date="2024-01-03",
        end_date="2024-01-04",
    )

    expected_index = pd.DatetimeIndex(["2024-01-03", "2024-01-04"], name="date")
    assert panels["close"].index.equals(expected_index)
    assert panels["open"].shape == (2, 2)


def test_load_eod_cohort_panels_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    data_dir = tmp_path / "eod"
    data_dir.mkdir()
    _write_parquet(data_dir / "AAA.US.parquet", _sample_frame(["2024-01-02"]))

    with pytest.raises(FileNotFoundError):
        load_eod_cohort_panels(data_dir, ["AAA.US", "ZZZ.US"])


def test_load_eod_cohort_panels_missing_inventory_mapping_raises_file_not_found(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "eod"
    _write_parquet(data_dir / "AAA.US.parquet", _sample_frame(["2024-01-02"]))
    inventory_path = tmp_path / "per_stock_coverage.json"
    inventory_path.write_text(
        json.dumps({"stocks": [{"symbol": "AAA.US", "file": "AAA.US.parquet"}]}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError, match="ZZZ.US"):
        load_eod_cohort_panels(
            data_dir,
            ["AAA.US", "ZZZ.US"],
            inventory_path=inventory_path,
        )


def test_load_eod_cohort_panels_rejects_path_escape_in_inventory(tmp_path: Path) -> None:
    data_dir = tmp_path / "eod"
    data_dir.mkdir()
    outside = tmp_path / "outside.parquet"
    _write_parquet(outside, _sample_frame(["2024-01-02"]))
    inventory_path = tmp_path / "per_stock_coverage.json"
    inventory_path.write_text(
        json.dumps({"stocks": [{"symbol": "AAA.US", "file": "../outside.parquet"}]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="stay under data_dir"):
        load_eod_cohort_panels(data_dir, ["AAA.US"], inventory_path=inventory_path)


def test_bluechip_50_cohort_is_fifty_unique_symbols_with_spy_benchmark() -> None:
    symbols = get_bluechip_50_symbols()

    assert symbols == [
        "AAPL.US", "MSFT.US", "NVDA.US", "AMZN.US", "GOOGL.US", "META.US", "BRK-B.US", "UNH.US", "JNJ.US", "JPM.US",
        "V.US", "PG.US", "XOM.US", "HD.US", "CVX.US", "MA.US", "LLY.US", "ABBV.US", "MRK.US", "PEP.US",
        "KO.US", "BAC.US", "TMO.US", "WMT.US", "COST.US", "CSCO.US", "MCD.US", "DIS.US", "ACN.US", "ABT.US",
        "ADBE.US", "CRM.US", "LIN.US", "NKE.US", "PFE.US", "CMCSA.US", "DHR.US", "TXN.US", "VZ.US", "PM.US",
        "INTC.US", "AMD.US", "HON.US", "WFC.US", "UPS.US", "QCOM.US", "IBM.US", "CAT.US", "GE.US", "AMGN.US",
    ]
    assert len(symbols) == 50
    assert len(set(symbols)) == 50
    assert BENCHMARK_SYMBOL == "SPY.US"
    assert BENCHMARK_SYMBOL not in symbols
    assert symbols == BLUECHIP_50_COHORT

    symbols.append("NOT-A-MEMBER.US")
    assert "NOT-A-MEMBER.US" not in BLUECHIP_50_COHORT
    assert get_bluechip_50_symbols() == BLUECHIP_50_COHORT


def test_parquet_loader_module_has_no_remote_data_or_trading_imports() -> None:
    source = inspect.getsource(parquet_loader)
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
    assert parquet_loader.__doc__
