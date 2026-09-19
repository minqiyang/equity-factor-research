"""Deterministic tests for portfolio weighting schemes and universe masking."""

from __future__ import annotations

import pandas as pd
import pytest

from backtest.portfolio import (
    BacktestValidationError,
    capture_backtest_source_provenance,
    run_long_only_backtest,
)


def _make_test_panels(
    n_days: int = 10,
    assets: tuple[str, ...] = ("AAA", "BBB", "CCC", "DDD", "EEE"),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range("2025-01-06", periods=n_days)
    prices = pd.DataFrame(
        {asset: 100.0 + 0.5 * i for i, asset in enumerate(assets)},
        index=dates,
    )
    # Give assets distinct scores: AAA highest (5.0), EEE lowest (1.0)
    signals = pd.DataFrame(
        {asset: 5.0 - i for i, asset in enumerate(assets)},
        index=dates,
    )
    return prices, signals


def test_equal_weighting_scheme_default() -> None:
    prices, signals = _make_test_panels()
    prov = capture_backtest_source_provenance(prices, signals)

    result = run_long_only_backtest(
        prices,
        signals,
        source_provenance=prov,
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=2,
        weighting_scheme="equal",
    )

    assert result.assumptions["weighting_scheme"] == "equal"
    assert result.assumptions["universe_mask_applied"] is False

    # AAA and BBB selected with equal weight 0.5
    for date in prices.index[2:]:
        assert result.holdings.loc[date, "AAA"] == pytest.approx(0.5)
        assert result.holdings.loc[date, "BBB"] == pytest.approx(0.5)
        assert result.holdings.loc[date, "CCC"] == pytest.approx(0.0)


def test_rank_weighting_scheme() -> None:
    prices, signals = _make_test_panels()
    prov = capture_backtest_source_provenance(prices, signals)

    # Top 3 assets: AAA (score 5), BBB (score 4), CCC (score 3)
    # Ranks among top 3: CCC=1, BBB=2, AAA=3 -> sum = 6
    # Expected weights: AAA=3/6=0.5, BBB=2/6=1/3, CCC=1/6
    result = run_long_only_backtest(
        prices,
        signals,
        source_provenance=prov,
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=3,
        weighting_scheme="rank",
    )

    assert result.assumptions["weighting_scheme"] == "rank"
    for date in prices.index[2:]:
        assert result.holdings.loc[date, "AAA"] == pytest.approx(3.0 / 6.0)
        assert result.holdings.loc[date, "BBB"] == pytest.approx(2.0 / 6.0)
        assert result.holdings.loc[date, "CCC"] == pytest.approx(1.0 / 6.0)
        assert result.holdings.loc[date, "DDD"] == pytest.approx(0.0)
        assert result.holdings.loc[date, "EEE"] == pytest.approx(0.0)


def test_rank_weighting_scheme_with_ties() -> None:
    prices, signals = _make_test_panels()
    # Create tie for top 2
    signals["AAA"] = 5.0
    signals["BBB"] = 5.0
    signals["CCC"] = 2.0
    prov = capture_backtest_source_provenance(prices, signals)

    # Top 3: AAA (5), BBB (5), CCC (2)
    # Ranks: CCC=1, AAA=2.5, BBB=2.5 -> sum = 6.0
    # Expected weights: AAA=2.5/6, BBB=2.5/6, CCC=1/6
    result = run_long_only_backtest(
        prices,
        signals,
        source_provenance=prov,
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=3,
        weighting_scheme="rank",
    )

    for date in prices.index[2:]:
        assert result.holdings.loc[date, "AAA"] == pytest.approx(2.5 / 6.0)
        assert result.holdings.loc[date, "BBB"] == pytest.approx(2.5 / 6.0)
        assert result.holdings.loc[date, "CCC"] == pytest.approx(1.0 / 6.0)


def test_rank_weighting_scheme_single_asset() -> None:
    prices, signals = _make_test_panels()
    prov = capture_backtest_source_provenance(prices, signals)

    result = run_long_only_backtest(
        prices,
        signals,
        source_provenance=prov,
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=1,
        weighting_scheme="rank",
    )

    for date in prices.index[2:]:
        assert result.holdings.loc[date, "AAA"] == pytest.approx(1.0)
        assert result.holdings.loc[date, "BBB"] == pytest.approx(0.0)


def test_rank_weighting_scheme_negative_scores() -> None:
    prices, signals = _make_test_panels()
    # Shift signals to negative numbers: AAA=-1, BBB=-2, CCC=-3, DDD=-4, EEE=-5
    signals -= 6.0
    prov = capture_backtest_source_provenance(prices, signals)

    result = run_long_only_backtest(
        prices,
        signals,
        source_provenance=prov,
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=3,
        weighting_scheme="rank",
    )

    for date in prices.index[2:]:
        # Ranks: CCC(-3)=1, BBB(-2)=2, AAA(-1)=3 -> sum = 6
        assert result.holdings.loc[date, "AAA"] == pytest.approx(0.5)
        assert result.holdings.loc[date, "BBB"] == pytest.approx(1.0 / 3.0)
        assert result.holdings.loc[date, "CCC"] == pytest.approx(1.0 / 6.0)


def test_weighting_scheme_validation() -> None:
    prices, signals = _make_test_panels()
    prov = capture_backtest_source_provenance(prices, signals)

    with pytest.raises(BacktestValidationError, match="weighting_scheme_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            source_provenance=prov,
            evaluation_start=prices.index[0],
            evaluation_end=prices.index[-1],
            top_n=2,
            weighting_scheme="invalid_scheme",  # type: ignore[arg-type]
        )


def test_universe_mask_filters_selection() -> None:
    prices, signals = _make_test_panels()
    prov = capture_backtest_source_provenance(prices, signals)

    # Mask out AAA (which has the highest score)
    universe_mask = pd.DataFrame(True, index=prices.index, columns=prices.columns)
    universe_mask["AAA"] = False

    result = run_long_only_backtest(
        prices,
        signals,
        source_provenance=prov,
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=2,
        universe_mask=universe_mask,
    )

    assert result.assumptions["universe_mask_applied"] is True
    # AAA was masked out, so BBB and CCC should be selected
    for date in prices.index[2:]:
        assert result.holdings.loc[date, "AAA"] == pytest.approx(0.0)
        assert result.holdings.loc[date, "BBB"] == pytest.approx(0.5)
        assert result.holdings.loc[date, "CCC"] == pytest.approx(0.5)


def test_universe_mask_liquidates_removed_asset() -> None:
    prices, signals = _make_test_panels(n_days=6)
    prov = capture_backtest_source_provenance(prices, signals)

    # AAA eligible for first 3 days, then removed on day 4 onwards
    universe_mask = pd.DataFrame(True, index=prices.index, columns=prices.columns)
    universe_mask.iloc[3:, universe_mask.columns.get_loc("AAA")] = False

    result = run_long_only_backtest(
        prices,
        signals,
        source_provenance=prov,
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=1,
        universe_mask=universe_mask,
    )

    # Before removal (day 2): AAA selected
    assert result.holdings.loc[prices.index[2], "AAA"] == pytest.approx(1.0)
    assert result.holdings.loc[prices.index[2], "BBB"] == pytest.approx(0.0)

    # After removal (day 3): AAA liquidated, BBB selected
    assert result.holdings.loc[prices.index[3], "AAA"] == pytest.approx(0.0)
    assert result.holdings.loc[prices.index[3], "BBB"] == pytest.approx(1.0)


def test_universe_mask_validation_errors() -> None:
    prices, signals = _make_test_panels()
    prov = capture_backtest_source_provenance(prices, signals)

    # Not a DataFrame
    with pytest.raises(BacktestValidationError, match="universe_mask_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            source_provenance=prov,
            evaluation_start=prices.index[0],
            evaluation_end=prices.index[-1],
            top_n=1,
            universe_mask="not_a_df",  # type: ignore[arg-type]
        )

    # Not a DatetimeIndex
    bad_index_mask = pd.DataFrame(True, index=[1, 2, 3], columns=prices.columns)
    with pytest.raises(BacktestValidationError, match="universe_mask_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            source_provenance=prov,
            evaluation_start=prices.index[0],
            evaluation_end=prices.index[-1],
            top_n=1,
            universe_mask=bad_index_mask,
        )
