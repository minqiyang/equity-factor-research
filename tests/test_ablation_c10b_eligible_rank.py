"""Eligibility-local Rank IC regressions for the C10b tiny-fixture repair.

These checks are deterministic. They do not assert wall time. Intended RED on
frozen B1 is the ineligible-row ranking/correlation skip; numerical contracts
must remain GREEN on baseline, B1 and the repair.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from features.diagnostics import (
    factor_information_coefficient,
    factor_rank_information_coefficient,
)


GOLDEN = json.loads(
    (Path(__file__).parent / "fixtures/ablation/ic_baseline.json").read_text()
)


def _panel(rows, columns=None, start="2024-01-02"):
    frame = pd.DataFrame(rows, columns=columns, dtype=float)
    frame.index = pd.date_range(start, periods=len(frame), freq="D")
    return frame


def _row_spearman(factor, forward_returns, min_periods=2):
    values = []
    for date in factor.index:
        factor_row = factor.loc[date]
        returns_row = forward_returns.loc[date]
        valid_pair = factor_row.notna() & returns_row.notna()
        if int(valid_pair.sum()) < min_periods:
            values.append(np.nan)
            continue
        with np.errstate(divide="ignore", invalid="ignore"):
            values.append(
                float(
                    factor_row[valid_pair].corr(
                        returns_row[valid_pair],
                        method="spearman",
                    )
                )
            )
    return pd.Series(
        values,
        index=factor.index,
        name="information_coefficient",
        dtype="float64",
    )


def _assert_spearman_contract(actual, expected):
    pd.testing.assert_index_equal(actual.index, expected.index, exact=True)
    assert actual.dtype == expected.dtype
    assert actual.name == expected.name
    assert actual.isna().equals(expected.isna())
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-12, equal_nan=True)


def _install_batch_trackers(monkeypatch):
    rank_indexes = []
    corr_indexes = []
    original_rank = pd.DataFrame.rank
    original_corrwith = pd.DataFrame.corrwith

    def rank(self, *args, **kwargs):
        rank_indexes.append(self.index.copy())
        return original_rank(self, *args, **kwargs)

    def corrwith(self, other, *args, **kwargs):
        corr_indexes.append(self.index.copy())
        return original_corrwith(self, other, *args, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "rank", rank)
    monkeypatch.setattr(pd.DataFrame, "corrwith", corrwith)
    return rank_indexes, corr_indexes


def _assert_no_ineligible_batch_work(rank_indexes, corr_indexes, eligible):
    allowed = set(eligible.index[eligible])
    for index in rank_indexes + corr_indexes:
        assert set(index).issubset(allowed)


def test_all_ineligible_empty_valid_pairs_are_not_ranked(monkeypatch):
    rank_indexes, corr_indexes = _install_batch_trackers(monkeypatch)
    factor = _panel(
        [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0],
            [10.0, 11.0, 12.0],
        ],
        columns=["AAA", "BBB", "CCC"],
    )
    returns = _panel(
        [
            [np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan],
        ],
        columns=["AAA", "BBB", "CCC"],
    )
    result = factor_information_coefficient(
        factor,
        returns,
        method="spearman",
        min_periods=2,
    )
    expected = pd.Series(
        np.nan,
        index=factor.index,
        name="information_coefficient",
        dtype="float64",
    )
    _assert_spearman_contract(result, expected)
    assert rank_indexes == []
    assert corr_indexes == []


def test_all_ineligible_below_min_periods_are_not_ranked(monkeypatch):
    rank_indexes, corr_indexes = _install_batch_trackers(monkeypatch)
    factor = _panel([[1.0, np.nan, 3.0], [np.nan, 2.0, np.nan], [4.0, np.nan, np.nan]])
    returns = _panel([[0.1, 0.2, np.nan], [0.3, np.nan, 0.4], [np.nan, 0.5, 0.6]])
    result = factor_information_coefficient(
        factor,
        returns,
        method="spearman",
        min_periods=2,
    )
    assert result.isna().all()
    assert result.name == "information_coefficient"
    assert rank_indexes == []
    assert corr_indexes == []


def test_large_ineligible_panel_is_not_size_gated(monkeypatch):
    rank_indexes, corr_indexes = _install_batch_trackers(monkeypatch)
    dates = pd.bdate_range("2020-01-01", periods=40)
    factor = pd.DataFrame(np.arange(40 * 25, dtype=float).reshape(40, 25), index=dates)
    returns = pd.DataFrame(np.nan, index=dates, columns=factor.columns)
    result = factor_information_coefficient(
        factor,
        returns,
        method="spearman",
        min_periods=3,
    )
    assert len(result) == 40
    assert result.isna().all()
    assert rank_indexes == []
    assert corr_indexes == []


def test_mixed_rows_rank_only_eligible_dates(monkeypatch):
    rank_indexes, corr_indexes = _install_batch_trackers(monkeypatch)
    factor = _panel(
        [
            [1.0, 2.0, 3.0],
            [1.0, np.nan, np.nan],
            [3.0, 1.0, 2.0],
            [np.nan, np.nan, np.nan],
        ]
    )
    returns = _panel(
        [
            [0.3, 0.2, 0.1],
            [0.9, 0.8, 0.7],
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]
    )
    result = factor_information_coefficient(
        factor,
        returns,
        method="spearman",
        min_periods=2,
    )
    expected = _row_spearman(factor, returns, min_periods=2)
    _assert_spearman_contract(result, expected)
    eligible = (factor.notna() & returns.notna()).sum(axis=1) >= 2
    assert bool(eligible.iloc[0]) and bool(eligible.iloc[2])
    assert not bool(eligible.iloc[1]) and not bool(eligible.iloc[3])
    _assert_no_ineligible_batch_work(rank_indexes, corr_indexes, eligible)
    assert rank_indexes and corr_indexes


def test_min_periods_boundary_eligibility(monkeypatch):
    rank_indexes, corr_indexes = _install_batch_trackers(monkeypatch)
    factor = _panel(
        [
            [1.0, 2.0, 3.0],
            [1.0, 2.0, np.nan],
            [1.0, np.nan, np.nan],
        ]
    )
    returns = _panel(
        [
            [0.3, 0.2, 0.1],
            [0.1, 0.2, 0.9],
            [0.8, 0.7, 0.6],
        ]
    )
    result = factor_information_coefficient(
        factor,
        returns,
        method="spearman",
        min_periods=3,
    )
    expected = _row_spearman(factor, returns, min_periods=3)
    _assert_spearman_contract(result, expected)
    assert np.isfinite(result.iloc[0])
    assert np.isnan(result.iloc[1]) and np.isnan(result.iloc[2])
    eligible = (factor.notna() & returns.notna()).sum(axis=1) >= 3
    _assert_no_ineligible_batch_work(rank_indexes, corr_indexes, eligible)


def test_tied_constant_and_missing_spearman_matches_row_oracle(monkeypatch):
    rank_indexes, corr_indexes = _install_batch_trackers(monkeypatch)
    factor = _panel(
        [
            [1.0, 1.0, 2.0, 3.0],
            [4.0, 4.0, 4.0, 4.0],
            [1.0, np.nan, 3.0, np.nan],
            [np.nan, np.nan, np.nan, np.nan],
            [5.0, 6.0, 7.0, 8.0],
        ]
    )
    returns = _panel(
        [
            [0.4, 0.3, 0.2, 0.1],
            [0.1, 0.2, 0.3, 0.4],
            [0.9, 0.8, np.nan, 0.1],
            [0.1, 0.2, 0.3, 0.4],
            [np.nan, 0.2, 0.3, 0.4],
        ]
    )
    result = factor_information_coefficient(
        factor,
        returns,
        method="spearman",
        min_periods=2,
    )
    expected = _row_spearman(factor, returns, min_periods=2)
    _assert_spearman_contract(result, expected)
    ranked = factor_rank_information_coefficient(factor, returns, min_periods=2)
    assert ranked.name == "rank_information_coefficient"
    pd.testing.assert_index_equal(ranked.index, result.index, exact=True)
    np.testing.assert_allclose(ranked.to_numpy(), result.to_numpy(), rtol=0, atol=1e-12, equal_nan=True)
    eligible = (factor.notna() & returns.notna()).sum(axis=1) >= 2
    _assert_no_ineligible_batch_work(rank_indexes, corr_indexes, eligible)


@pytest.mark.parametrize(
    "kwargs,match,exc",
    [
        ({"method": "kendall"}, "method", ValueError),
        ({"min_periods": 1}, "at least 2", ValueError),
        ({"min_periods": True}, "integer", TypeError),
        ({"min_periods": 2.5}, "integer", TypeError),
    ],
)
def test_invalid_inputs_raise_before_batch_optimization(monkeypatch, kwargs, match, exc):
    rank_indexes, corr_indexes = _install_batch_trackers(monkeypatch)
    factor = _panel([[1.0, 2.0], [3.0, 4.0]])
    returns = _panel([[0.1, 0.2], [0.3, 0.4]])
    with pytest.raises(exc, match=match):
        factor_information_coefficient(factor, returns, **kwargs)
    assert rank_indexes == []
    assert corr_indexes == []


def test_misaligned_and_nonfinite_inputs_raise_before_batch_optimization(monkeypatch):
    rank_indexes, corr_indexes = _install_batch_trackers(monkeypatch)
    factor = _panel([[1.0, 2.0], [3.0, 4.0]], start="2024-01-01")
    returns = _panel([[0.1, 0.2], [0.3, 0.4]], start="2024-01-02")
    with pytest.raises(ValueError, match="identical indexes"):
        factor_information_coefficient(factor, returns, method="spearman")
    factor = _panel([[1.0, 2.0]], columns=["AAA", "BBB"])
    returns = _panel([[0.1, 0.2]], columns=["AAA", "CCC"])
    with pytest.raises(ValueError, match="identical columns"):
        factor_information_coefficient(factor, returns, method="spearman")
    factor = _panel([[1.0, 2.0]])
    returns = _panel([[0.1, np.inf]])
    with pytest.raises(ValueError, match="finite numeric"):
        factor_information_coefficient(factor, returns, method="spearman")
    factor = _panel([[1.0, 2.0]])
    returns = pd.DataFrame([[0.1, "1.0"]], index=factor.index, columns=factor.columns)
    with pytest.raises(TypeError, match="numeric non-boolean"):
        factor_information_coefficient(factor, returns, method="spearman")
    assert rank_indexes == []
    assert corr_indexes == []


def test_pearson_path_does_not_use_dataframe_rank_or_corrwith(monkeypatch):
    rank_indexes, corr_indexes = _install_batch_trackers(monkeypatch)
    factor = _panel([[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]])
    returns = _panel([[0.1, 0.2, 0.3], [0.3, 0.2, 0.1]])
    result = factor_information_coefficient(factor, returns, method="pearson")
    pd.testing.assert_series_equal(
        result,
        pd.Series([1.0, 1.0], index=factor.index, name="information_coefficient"),
        check_exact=True,
    )
    assert rank_indexes == []
    assert corr_indexes == []


@pytest.mark.parametrize(
    "case",
    [row for row in GOLDEN["cases"] if row["method"] == "spearman"],
    ids=lambda case: case["id"],
)
def test_reused_spearman_golden_remains_bounded(case):
    dates = pd.date_range("2020-01-01", periods=8)
    left = pd.DataFrame(case["left"], index=dates, dtype=float)
    right = pd.DataFrame(case["right"], index=dates, dtype=float)
    actual = factor_information_coefficient(
        left,
        right,
        method="spearman",
        min_periods=2,
    )
    expected = pd.Series(
        case["expected"],
        index=dates,
        name=case["name"],
        dtype=case["dtype"],
    )
    _assert_spearman_contract(actual, expected)
