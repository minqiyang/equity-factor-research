"""Unchanging-price segment reporting for Demo v0 and the M3-01 demo.

An unchanging-price segment is a consecutive run of equal prices for one
asset with length >= 2. The helper counts segments, assets affected, and
max run length. Consecutive equal prices stay in the panel.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class UnchangingPriceSegmentReport:
    """Counts of consecutive equal-price runs on a price panel."""

    segment_count: int
    assets_affected: int
    max_run_length: int


def report_unchanging_price_segments(
    prices: pd.DataFrame,
) -> UnchangingPriceSegmentReport:
    """Count unchanging-price segments without mutating the supplied panel."""

    if not isinstance(prices, pd.DataFrame):
        raise TypeError("prices must be a pandas DataFrame")

    values = prices.to_numpy()
    segment_count = 0
    assets_affected = 0
    max_run_length = 0

    for column_index in range(values.shape[1]):
        column_segments, column_max = _segment_count_and_max_run(
            values[:, column_index]
        )
        if column_segments:
            segment_count += column_segments
            assets_affected += 1
            if column_max > max_run_length:
                max_run_length = column_max

    return UnchangingPriceSegmentReport(
        segment_count=segment_count,
        assets_affected=assets_affected,
        max_run_length=max_run_length,
    )


def _segment_count_and_max_run(column: np.ndarray) -> tuple[int, int]:
    n = column.shape[0]
    if n < 2:
        return 0, 0
    run_ids = np.cumsum(
        np.concatenate(([True], column[1:] != column[:-1]))
    )
    counts = np.bincount(run_ids)
    long_runs = counts[counts >= 2]
    if long_runs.size == 0:
        return 0, 0
    return int(long_runs.size), int(long_runs.max())
