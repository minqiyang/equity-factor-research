"""Train/validation/test split helpers for factor research panels.

This module separates already-prepared date indexes or numeric factor panels
into deterministic chronological research windows. It does not fetch data,
calculate returns, choose parameters, run a backtest, or make performance
claims.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from features.operators import validate_panel_data


@dataclass(frozen=True)
class TrainValidationTestSplit:
    """Chronological train, validation, and test date windows."""

    train: pd.DatetimeIndex
    validation: pd.DatetimeIndex
    test: pd.DatetimeIndex
    train_end: pd.Timestamp
    validation_end: pd.Timestamp
    test_end: pd.Timestamp

    @property
    def all_dates(self) -> pd.DatetimeIndex:
        """Return the split dates in chronological order."""

        return self.train.append([self.validation, self.test])

    def as_dict(self) -> dict[str, pd.DatetimeIndex]:
        """Return split dates keyed by window name."""

        return {
            "train": self.train,
            "validation": self.validation,
            "test": self.test,
        }


def make_train_validation_test_split(
    index: pd.DatetimeIndex,
    *,
    train_end: str | pd.Timestamp,
    validation_end: str | pd.Timestamp,
    test_end: str | pd.Timestamp | None = None,
) -> TrainValidationTestSplit:
    """Create non-overlapping chronological date windows.

    Boundaries are inclusive. The train window contains dates on or before
    ``train_end``. The validation window contains dates after ``train_end`` and
    on or before ``validation_end``. The test window contains dates after
    ``validation_end`` and on or before ``test_end``. If ``test_end`` is not
    provided, the final available date is used.

    The input index is validated but not sorted, reindexed, filled, or
    otherwise transformed. Each output window must contain at least one date.
    """

    date_index = _validate_date_index(index, name="index")
    train_boundary = _coerce_boundary(train_end, "train_end")
    validation_boundary = _coerce_boundary(validation_end, "validation_end")
    test_boundary = (
        date_index[-1]
        if test_end is None
        else _coerce_boundary(test_end, "test_end")
    )

    if not train_boundary < validation_boundary < test_boundary:
        raise ValueError(
            "split boundaries must satisfy train_end < validation_end < test_end"
        )

    if test_boundary < date_index[-1]:
        raise ValueError("test_end must be on or after the final index date")

    train_dates = date_index[date_index <= train_boundary]
    validation_dates = date_index[
        (date_index > train_boundary) & (date_index <= validation_boundary)
    ]
    test_dates = date_index[
        (date_index > validation_boundary) & (date_index <= test_boundary)
    ]

    _validate_non_empty_window(train_dates, "train")
    _validate_non_empty_window(validation_dates, "validation")
    _validate_non_empty_window(test_dates, "test")

    return TrainValidationTestSplit(
        train=train_dates,
        validation=validation_dates,
        test=test_dates,
        train_end=train_boundary,
        validation_end=validation_boundary,
        test_end=test_boundary,
    )


def split_panel_by_train_validation_test(
    panel: pd.DataFrame,
    split: TrainValidationTestSplit,
    *,
    name: str = "panel",
) -> dict[str, pd.DataFrame]:
    """Slice a numeric factor panel by a validated train/validation/test split."""

    if not isinstance(split, TrainValidationTestSplit):
        raise TypeError("split must be a TrainValidationTestSplit")

    validated = validate_panel_data(panel, name=name)
    if not validated.index.equals(split.all_dates):
        raise ValueError("panel index must exactly match split dates")

    return {
        split_name: validated.loc[dates].copy()
        for split_name, dates in split.as_dict().items()
    }


def _validate_date_index(index: pd.DatetimeIndex, *, name: str) -> pd.DatetimeIndex:
    if not isinstance(index, pd.DatetimeIndex):
        raise TypeError(f"{name} must be a pandas DatetimeIndex")

    if index.empty:
        raise ValueError(f"{name} must not be empty")

    if index.has_duplicates:
        raise ValueError(f"{name} must not contain duplicate dates")

    if not index.is_monotonic_increasing:
        raise ValueError(f"{name} must be sorted in increasing date order")

    return index


def _coerce_boundary(value: str | pd.Timestamp, name: str) -> pd.Timestamp:
    if not isinstance(value, (str, pd.Timestamp)):
        raise TypeError(f"{name} must be a date string or pandas Timestamp")

    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        raise ValueError(f"{name} must be a valid timestamp")

    return timestamp


def _validate_non_empty_window(index: pd.DatetimeIndex, name: str) -> None:
    if index.empty:
        raise ValueError(f"{name} split must contain at least one date")


__all__ = [
    "TrainValidationTestSplit",
    "make_train_validation_test_split",
    "split_panel_by_train_validation_test",
]
