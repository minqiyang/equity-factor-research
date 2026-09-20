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


def test_inverse_volatility_weighting_scheme() -> None:
    # 25 days: AAA has low volatility (~0.001), BBB has high volatility (~0.03)
    dates = pd.bdate_range("2025-01-06", periods=25)
    aaa_prices = [100.0]
    bbb_prices = [100.0]
    for i in range(1, 25):
        aaa_ret = 0.003 if i % 2 == 1 else 0.001
        aaa_prices.append(aaa_prices[-1] * (1.0 + aaa_ret))
        bbb_ret = 0.03 if i % 2 == 1 else -0.03
        bbb_prices.append(bbb_prices[-1] * (1.0 + bbb_ret))

    prices = pd.DataFrame(
        {
            "AAA": aaa_prices,
            "BBB": bbb_prices,
            "CCC": [100.0] * 25,
        },
        index=dates,
    )
    # Top 2 are AAA and BBB
    signals = pd.DataFrame(
        {
            "AAA": 10.0,
            "BBB": 9.0,
            "CCC": 1.0,
        },
        index=dates,
    )
    prov = capture_backtest_source_provenance(prices, signals)

    result = run_long_only_backtest(
        prices,
        signals,
        source_provenance=prov,
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=2,
        weighting_scheme="inverse_volatility",
        volatility_window=10,
        min_volatility_periods=5,
    )

    assert result.assumptions["weighting_scheme"] == "inverse_volatility"
    assert result.assumptions["volatility_window"] == 10
    assert result.assumptions["min_volatility_periods"] == 5

    # After warmup (position >= 6): AAA has lower vol than BBB, so AAA weight > BBB weight
    for date in prices.index[10:]:
        w_aaa = result.holdings.loc[date, "AAA"]
        w_bbb = result.holdings.loc[date, "BBB"]
        assert w_aaa > w_bbb
        assert w_aaa + w_bbb == pytest.approx(1.0, abs=1e-6)
        assert result.holdings.loc[date, "CCC"] == pytest.approx(0.0)


def test_inverse_volatility_causality_mutation() -> None:
    dates = pd.bdate_range("2025-01-06", periods=25)
    aaa_prices = [100.0]
    bbb_prices = [100.0]
    for i in range(1, 25):
        aaa_ret = 0.003 if i % 2 == 1 else 0.001
        aaa_prices.append(aaa_prices[-1] * (1.0 + aaa_ret))
        bbb_ret = 0.03 if i % 2 == 1 else -0.03
        bbb_prices.append(bbb_prices[-1] * (1.0 + bbb_ret))

    prices = pd.DataFrame(
        {"AAA": aaa_prices, "BBB": bbb_prices, "CCC": [100.0] * 25},
        index=dates,
    )
    signals = pd.DataFrame(
        {"AAA": 10.0, "BBB": 9.0, "CCC": 1.0},
        index=dates,
    )
    prov = capture_backtest_source_provenance(prices, signals)

    res_base = run_long_only_backtest(
        prices,
        signals,
        source_provenance=prov,
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=2,
        weighting_scheme="inverse_volatility",
        volatility_window=10,
        min_volatility_periods=5,
        signal_lag_periods=1,
    )

    # Pick rebalance date t (index 15). Signal/vol cutoff is t-1 (index 14).
    t = dates[15]
    base_weights_t = res_base.holdings.loc[t].copy()

    # Mutate prices on and after t (index >= 15) by 10x
    prices_mutated = prices.copy()
    prices_mutated.iloc[15:] = prices_mutated.iloc[15:] * 10.0
    prov_mut = capture_backtest_source_provenance(prices_mutated, signals)

    res_mut = run_long_only_backtest(
        prices_mutated,
        signals,
        source_provenance=prov_mut,
        evaluation_start=prices_mutated.index[0],
        evaluation_end=prices_mutated.index[-1],
        rebalance_frequency="D",
        top_n=2,
        weighting_scheme="inverse_volatility",
        volatility_window=10,
        min_volatility_periods=5,
        signal_lag_periods=1,
    )

    # Holdings established at close of t must be strictly identical
    mut_weights_t = res_mut.holdings.loc[t]
    for asset in ("AAA", "BBB", "CCC"):
        assert mut_weights_t[asset] == pytest.approx(base_weights_t[asset], abs=1e-10)


def test_turnover_penalty_lambda_reduces_turnover() -> None:
    dates = pd.bdate_range("2025-01-06", periods=10)
    prices = pd.DataFrame(
        {
            "AAA": [100.0 + i * 0.5 for i in range(10)],
            "BBB": [100.0 + i * 0.5 for i in range(10)],
        },
        index=dates,
    )
    # Signals alternate top asset between AAA and BBB every day
    signals = pd.DataFrame(
        {
            "AAA": [10.0 if i % 2 == 0 else 1.0 for i in range(10)],
            "BBB": [1.0 if i % 2 == 0 else 10.0 for i in range(10)],
        },
        index=dates,
    )
    prov = capture_backtest_source_provenance(prices, signals)

    # Without turnover penalty (lambda = 0.0)
    res_no_penalty = run_long_only_backtest(
        prices,
        signals,
        source_provenance=prov,
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=1,
        weighting_scheme="equal",
        turnover_penalty_lambda=0.0,
    )

    # With turnover penalty (lambda = 0.5)
    res_with_penalty = run_long_only_backtest(
        prices,
        signals,
        source_provenance=prov,
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=1,
        weighting_scheme="equal",
        turnover_penalty_lambda=0.5,
    )

    assert res_with_penalty.assumptions["turnover_penalty_lambda"] == 0.5
    # Turnover must be strictly lower with penalty
    assert res_with_penalty.turnover.sum() < res_no_penalty.turnover.sum()

    # ADV-239-2: Pin simplex invariants (non-negativity and unit-sum)
    assert (res_with_penalty.holdings >= -1e-10).all().all()
    for date in dates[1:]:
        assert res_with_penalty.holdings.loc[date].sum() == pytest.approx(1.0, abs=1e-6)


def test_weighting_and_turnover_validation_errors() -> None:
    prices, signals = _make_test_panels()
    prov = capture_backtest_source_provenance(prices, signals)

    # Invalid weighting_scheme
    with pytest.raises(BacktestValidationError, match="weighting_scheme_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            source_provenance=prov,
            evaluation_start=prices.index[0],
            evaluation_end=prices.index[-1],
            weighting_scheme="unsupported",  # type: ignore[arg-type]
        )

    # Invalid turnover_penalty_lambda
    with pytest.raises(BacktestValidationError, match="turnover_penalty_lambda_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            source_provenance=prov,
            evaluation_start=prices.index[0],
            evaluation_end=prices.index[-1],
            turnover_penalty_lambda=-0.1,
        )

    with pytest.raises(BacktestValidationError, match="turnover_penalty_lambda_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            source_provenance=prov,
            evaluation_start=prices.index[0],
            evaluation_end=prices.index[-1],
            turnover_penalty_lambda=1.0,
        )

    # Invalid volatility_window
    with pytest.raises(BacktestValidationError, match="volatility_window_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            source_provenance=prov,
            evaluation_start=prices.index[0],
            evaluation_end=prices.index[-1],
            volatility_window=0,
        )

    # Invalid min_volatility_periods
    with pytest.raises(BacktestValidationError, match="min_volatility_periods_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            source_provenance=prov,
            evaluation_start=prices.index[0],
            evaluation_end=prices.index[-1],
            volatility_window=10,
            min_volatility_periods=15,
        )

