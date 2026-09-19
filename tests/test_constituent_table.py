from pathlib import Path
import pytest
import pandas as pd

from data.constituent_table import (
    ValidatedConstituentIntervals,
    build_membership_mask,
    load_constituent_intervals_csv,
)


def test_load_constituent_intervals_csv_valid(tmp_path: Path) -> None:
    csv_file = tmp_path / "sp500_constituents.csv"
    csv_file.write_text(
        "symbol,start_date,end_date\n"
        "AAPL,2020-01-01,\n"
        "MSFT,2020-01-01,\n"
        "XYZ,2020-01-01,2021-06-30\n"
        "XYZ,2022-01-01,2023-01-01\n",
        encoding="utf-8",
    )

    result = load_constituent_intervals_csv(csv_file)

    assert isinstance(result, ValidatedConstituentIntervals)
    assert len(result.data) == 4
    assert list(result.data["symbol"]) == ["AAPL", "MSFT", "XYZ", "XYZ"]
    assert pd.isna(result.data.loc[0, "end_date"])
    assert result.data.loc[2, "end_date"] == pd.Timestamp("2021-06-30")
    assert result.summary.missing_value_count == 2
    assert result.summary.source_row_count == 4


def test_load_constituent_intervals_csv_rejects_missing_columns(tmp_path: Path) -> None:
    csv_file = tmp_path / "bad.csv"
    csv_file.write_text("symbol,start_date\nAAPL,2020-01-01\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        load_constituent_intervals_csv(csv_file)


def test_load_constituent_intervals_csv_rejects_inverted_dates(tmp_path: Path) -> None:
    csv_file = tmp_path / "inverted.csv"
    csv_file.write_text(
        "symbol,start_date,end_date\n"
        "AAPL,2021-01-01,2020-01-01\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="start_date .* after end_date"):
        load_constituent_intervals_csv(csv_file)


def test_load_constituent_intervals_csv_rejects_overlapping_intervals(tmp_path: Path) -> None:
    csv_file = tmp_path / "overlap.csv"
    csv_file.write_text(
        "symbol,start_date,end_date\n"
        "AAPL,2020-01-01,2021-06-30\n"
        "AAPL,2021-01-01,2022-01-01\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="overlapping membership intervals"):
        load_constituent_intervals_csv(csv_file)


def test_build_membership_mask_exclusive_exit() -> None:
    table = pd.DataFrame(
        {
            "symbol": ["AAPL", "XYZ"],
            "start_date": [pd.Timestamp("2021-01-04"), pd.Timestamp("2021-01-04")],
            "end_date": [None, pd.Timestamp("2021-01-06")],
        }
    )
    dates = pd.DatetimeIndex(["2021-01-04", "2021-01-05", "2021-01-06", "2021-01-07"])

    mask = build_membership_mask(table, dates, assets=["AAPL", "XYZ", "UNKNOWN"])

    assert mask.shape == (4, 3)
    assert list(mask.columns) == ["AAPL", "XYZ", "UNKNOWN"]

    # AAPL is open-ended, active on all dates >= 2021-01-04
    assert mask["AAPL"].tolist() == [True, True, True, True]

    # XYZ ends on 2021-01-06 (exclusive by default), so active on Jan 4 and 5, False on Jan 6 and 7
    assert mask["XYZ"].tolist() == [True, True, False, False]

    # UNKNOWN is not in table, all False
    assert mask["UNKNOWN"].tolist() == [False, False, False, False]


def test_build_membership_mask_inclusive_exit() -> None:
    table = pd.DataFrame(
        {
            "symbol": ["XYZ"],
            "start_date": [pd.Timestamp("2021-01-04")],
            "end_date": [pd.Timestamp("2021-01-06")],
        }
    )
    dates = pd.DatetimeIndex(["2021-01-04", "2021-01-05", "2021-01-06", "2021-01-07"])

    mask = build_membership_mask(table, dates, inclusive_exit=True)

    # XYZ with inclusive_exit is active on Jan 4, Jan 5, and Jan 6
    assert mask["XYZ"].tolist() == [True, True, True, False]


def test_build_membership_mask_validates_dates() -> None:
    table = pd.DataFrame(
        {
            "symbol": ["XYZ"],
            "start_date": [pd.Timestamp("2021-01-04")],
            "end_date": [None],
        }
    )

    with pytest.raises(TypeError, match="must be a pandas DatetimeIndex"):
        build_membership_mask(table, ["2021-01-04"])  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must not be empty"):
        build_membership_mask(table, pd.DatetimeIndex([]))

    with pytest.raises(ValueError, match="monotonic increasing"):
        build_membership_mask(table, pd.DatetimeIndex(["2021-01-05", "2021-01-04"]))
