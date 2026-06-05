import ast
import inspect

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_index_equal

import features.validation as validation
from features.validation import (
    TrainValidationTestSplit,
    make_train_validation_test_split,
    split_panel_by_train_validation_test,
)


def _dates() -> pd.DatetimeIndex:
    return pd.date_range("2024-01-01", periods=6, freq="D")


def _panel() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "BBB": [6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
        },
        index=_dates(),
    )


def test_make_train_validation_test_split_is_hand_calculated() -> None:
    split = make_train_validation_test_split(
        _dates(),
        train_end="2024-01-02",
        validation_end="2024-01-04",
    )

    assert_index_equal(split.train, pd.DatetimeIndex(["2024-01-01", "2024-01-02"]))
    assert_index_equal(
        split.validation,
        pd.DatetimeIndex(["2024-01-03", "2024-01-04"]),
    )
    assert_index_equal(split.test, pd.DatetimeIndex(["2024-01-05", "2024-01-06"]))
    assert split.train_end == pd.Timestamp("2024-01-02")
    assert split.validation_end == pd.Timestamp("2024-01-04")
    assert split.test_end == pd.Timestamp("2024-01-06")


def test_make_train_validation_test_split_accepts_timestamp_boundaries() -> None:
    split = make_train_validation_test_split(
        _dates(),
        train_end=pd.Timestamp("2024-01-02"),
        validation_end=pd.Timestamp("2024-01-04"),
        test_end=pd.Timestamp("2024-01-06"),
    )

    assert isinstance(split, TrainValidationTestSplit)
    assert_index_equal(split.all_dates, _dates())


def test_make_train_validation_test_split_uses_inclusive_ordered_boundaries() -> None:
    split = make_train_validation_test_split(
        _dates(),
        train_end="2024-01-02 12:00:00",
        validation_end="2024-01-04 12:00:00",
    )

    assert_index_equal(split.train, pd.DatetimeIndex(["2024-01-01", "2024-01-02"]))
    assert_index_equal(
        split.validation,
        pd.DatetimeIndex(["2024-01-03", "2024-01-04"]),
    )
    assert_index_equal(split.test, pd.DatetimeIndex(["2024-01-05", "2024-01-06"]))


def test_split_as_dict_preserves_window_order() -> None:
    split = make_train_validation_test_split(
        _dates(),
        train_end="2024-01-02",
        validation_end="2024-01-04",
    )

    assert list(split.as_dict()) == ["train", "validation", "test"]


def test_split_panel_by_train_validation_test_preserves_values_without_filling() -> None:
    panel = _panel()
    panel.loc[pd.Timestamp("2024-01-03"), "AAA"] = pd.NA
    split = make_train_validation_test_split(
        panel.index,
        train_end="2024-01-02",
        validation_end="2024-01-04",
    )

    result = split_panel_by_train_validation_test(panel, split)

    assert_frame_equal(result["train"], panel.iloc[:2].astype(float))
    assert_frame_equal(result["validation"], panel.iloc[2:4].astype(float))
    assert_frame_equal(result["test"], panel.iloc[4:].astype(float))
    assert pd.isna(result["validation"].loc[pd.Timestamp("2024-01-03"), "AAA"])


def test_split_panel_by_train_validation_test_rejects_mismatched_index() -> None:
    split = make_train_validation_test_split(
        _dates(),
        train_end="2024-01-02",
        validation_end="2024-01-04",
    )
    shorter_panel = _panel().iloc[:-1]

    with pytest.raises(ValueError, match="exactly match split dates"):
        split_panel_by_train_validation_test(shorter_panel, split)


def test_split_panel_by_train_validation_test_rejects_non_numeric_panel() -> None:
    panel = pd.DataFrame({"AAA": [1.0, "2.0", 3.0, 4.0, 5.0, 6.0]}, index=_dates())
    split = make_train_validation_test_split(
        panel.index,
        train_end="2024-01-02",
        validation_end="2024-01-04",
    )

    with pytest.raises(TypeError, match="numeric non-boolean"):
        split_panel_by_train_validation_test(panel, split)


def test_split_panel_by_train_validation_test_rejects_invalid_split_object() -> None:
    with pytest.raises(TypeError, match="TrainValidationTestSplit"):
        split_panel_by_train_validation_test(_panel(), "bad split")  # type: ignore[arg-type]


def test_make_train_validation_test_split_rejects_non_datetime_index() -> None:
    with pytest.raises(TypeError, match="DatetimeIndex"):
        make_train_validation_test_split(  # type: ignore[arg-type]
            pd.Index(["2024-01-01", "2024-01-02"]),
            train_end="2024-01-01",
            validation_end="2024-01-02",
        )


def test_make_train_validation_test_split_rejects_empty_index() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        make_train_validation_test_split(
            pd.DatetimeIndex([]),
            train_end="2024-01-01",
            validation_end="2024-01-02",
        )


def test_make_train_validation_test_split_rejects_duplicate_dates() -> None:
    duplicate_index = pd.DatetimeIndex(["2024-01-01", "2024-01-01", "2024-01-02"])

    with pytest.raises(ValueError, match="duplicate"):
        make_train_validation_test_split(
            duplicate_index,
            train_end="2024-01-01",
            validation_end="2024-01-02",
        )


def test_make_train_validation_test_split_rejects_unsorted_dates() -> None:
    unsorted_index = pd.DatetimeIndex(["2024-01-02", "2024-01-01", "2024-01-03"])

    with pytest.raises(ValueError, match="sorted"):
        make_train_validation_test_split(
            unsorted_index,
            train_end="2024-01-01",
            validation_end="2024-01-02",
        )


@pytest.mark.parametrize(
    ("train_end", "validation_end", "test_end"),
    [
        ("2024-01-03", "2024-01-03", None),
        ("2024-01-04", "2024-01-03", None),
        ("2024-01-02", "2024-01-06", None),
        ("2024-01-02", "2024-01-05", "2024-01-05"),
    ],
)
def test_make_train_validation_test_split_rejects_invalid_boundary_order(
    train_end: str,
    validation_end: str,
    test_end: str | None,
) -> None:
    with pytest.raises(ValueError, match="train_end < validation_end < test_end"):
        make_train_validation_test_split(
            _dates(),
            train_end=train_end,
            validation_end=validation_end,
            test_end=test_end,
        )


@pytest.mark.parametrize(
    ("train_end", "validation_end", "expected_message"),
    [
        ("2023-12-31", "2024-01-03", "train split"),
        ("2024-01-02", "2024-01-02 12:00:00", "validation split"),
        ("2024-01-02", "2024-01-07", "test split"),
    ],
)
def test_make_train_validation_test_split_rejects_empty_windows(
    train_end: str,
    validation_end: str,
    expected_message: str,
) -> None:
    with pytest.raises(ValueError, match=expected_message):
        make_train_validation_test_split(
            _dates(),
            train_end=train_end,
            validation_end=validation_end,
            test_end="2024-01-08" if expected_message == "test split" else None,
        )


def test_make_train_validation_test_split_rejects_test_end_before_final_date() -> None:
    with pytest.raises(ValueError, match="final index date"):
        make_train_validation_test_split(
            _dates(),
            train_end="2024-01-02",
            validation_end="2024-01-04",
            test_end="2024-01-05",
        )


@pytest.mark.parametrize("bad_boundary", [1, 1.5, True])
def test_make_train_validation_test_split_rejects_non_date_boundaries(
    bad_boundary: object,
) -> None:
    with pytest.raises(TypeError, match="date string or pandas Timestamp"):
        make_train_validation_test_split(
            _dates(),
            train_end=bad_boundary,  # type: ignore[arg-type]
            validation_end="2024-01-04",
        )


def test_make_train_validation_test_split_rejects_invalid_timestamp_string() -> None:
    with pytest.raises(ValueError):
        make_train_validation_test_split(
            _dates(),
            train_end="not-a-date",
            validation_end="2024-01-04",
        )


def test_validation_module_has_no_data_trading_or_backtest_imports() -> None:
    source = inspect.getsource(validation)
    tree = ast.parse(source)
    forbidden_terms = {
        "backtest",
        "broker",
        "requests",
        "urllib",
        "yfinance",
        "alpaca",
        "ccxt",
        "reporting",
        "strategies",
    }
    imported_modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    for module_name in imported_modules:
        assert not any(term in module_name.lower() for term in forbidden_terms)
