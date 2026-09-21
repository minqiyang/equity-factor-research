"""Deterministic behavior tests for the Stage 2b timing contract."""

from __future__ import annotations

from dataclasses import asdict, replace
from fractions import Fraction
import inspect
from numbers import Real

import numpy as np
import pandas as pd
import pytest

import backtest.portfolio as portfolio_module
from backtest.portfolio import (
    BacktestSourceProvenance,
    BacktestValidationError,
    _validate_execution_price_legs,
    _validate_postcost_net_equity,
    _validate_pretrade_gross,
    apply_tracked_backtest_source_mutation,
    capture_backtest_source_provenance,
    run_long_only_backtest as _run_long_only_backtest,
)
from features.validation import (
    make_price_forward_return_labels,
    make_train_validation_test_split,
)


def run_long_only_backtest(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    **kwargs: object,
):
    """Run ordinary fixtures with provenance captured before execution."""

    return _run_long_only_backtest(
        prices,
        signals,
        source_provenance=capture_backtest_source_provenance(prices, signals),
        **kwargs,
    )


def _run(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    **kwargs: object,
):
    return run_long_only_backtest(
        prices,
        signals,
        evaluation_start=prices.index[0],
        evaluation_end=prices.index[-1],
        rebalance_frequency="D",
        top_n=1,
        **kwargs,
    )


@pytest.mark.parametrize("shape", [(3, 0), (0, 3), (0, 0), (3, 3)])
def test_bounded_signal_validation_preserves_empty_and_named_axes(shape) -> None:
    frame = pd.DataFrame(
        np.zeros(shape),
        index=pd.date_range("2024-01-01", periods=shape[0], name="date"),
        columns=pd.Index(["A"] * shape[1], name="asset"),
    )
    actual = portfolio_module._validate_bounded_signal_values(frame)
    pd.testing.assert_frame_equal(actual, frame, check_exact=True)


def test_bounded_signal_validation_preserves_mixed_scalar_values() -> None:
    dates = pd.date_range("2024-01-01", periods=3, name="date")
    frame = pd.DataFrame({
        "integer": pd.Series([2**63 + 1, 2**63 + 3, 0], index=dates, dtype="uint64"),
        "float": [1.25, -0.0, np.nan],
        "object": pd.Series([np.int16(7), np.float32(2.5), Fraction(1, 2)], index=dates, dtype=object),
        "nullable": pd.Series([1, 2, 3], index=dates, dtype="Int64"),
    }, index=dates)
    original = frame.copy(deep=True)
    # The reference reads each scalar with the original positional accessor.
    expected = pd.DataFrame(
        [[float(frame.iat[row, col]) for col in range(frame.shape[1])]
         for row in range(frame.shape[0])], index=dates, columns=frame.columns,
    )
    actual = portfolio_module._validate_bounded_signal_values(frame)
    pd.testing.assert_frame_equal(actual, expected, check_exact=True)
    assert np.signbit(actual.loc[dates[1], "float"])
    pd.testing.assert_frame_equal(frame, original, check_exact=True)


@pytest.mark.parametrize("invalid", [True, np.bool_(False), "2", 1 + 0j, pd.NA, np.inf, -np.inf])
def test_bounded_signal_validation_retains_first_invalid_cell(invalid) -> None:
    dates = pd.date_range("2024-01-01", periods=3)
    frame = pd.DataFrame([[1.0, invalid], [invalid, 2.0], [3.0, 4.0]],
                         index=dates, columns=[1, "1"], dtype=object)
    with pytest.raises(BacktestValidationError) as caught:
        portfolio_module._validate_bounded_signal_values(frame)
    assert caught.value.reason == "signal_value_invalid"
    assert caught.value.date == dates[0]
    assert caught.value.asset == "1"


@pytest.mark.parametrize("policy", ["raise", "zero_return"])
@pytest.mark.parametrize("bad_value", [np.nan, np.inf, -np.inf, 0.0, -1.0])
@pytest.mark.parametrize("endpoint", ["previous", "current"])
def test_held_return_native_path_matches_scalar_path(policy, bad_value, endpoint) -> None:
    dates = pd.date_range("2024-01-01", periods=2)
    assets = pd.Index([1, "1", "unheld", "tiny"], name="asset")
    previous = pd.Series([100.0, 200.0, 0.0, 1e-300], index=assets)
    current = pd.Series([101.0, 198.0, np.inf, 1e-299], index=assets)
    holdings = pd.Series([0.5, -0.5, 0.0, 0.1], index=assets)
    (previous if endpoint == "previous" else current).iloc[1] = bad_value

    def execute(as_object):
        try:
            return portfolio_module._calculate_held_asset_returns(
                previous_prices=previous.astype(object) if as_object else previous,
                current_prices=current.astype(object) if as_object else current,
                previous_holdings=holdings,
                previous_date=dates[0], current_date=dates[1], missing_price_policy=policy,
            )
        except BacktestValidationError as exc:
            return exc.reason, exc.date, exc.asset

    expected = execute(True)
    actual = execute(False)
    if isinstance(expected, pd.Series):
        pd.testing.assert_series_equal(actual, expected, check_exact=True)
    else:
        assert actual == expected


@pytest.mark.parametrize("dtype", ["int64", "uint64", "float16", "float32", "float64", "longdouble"])
def test_held_return_native_dtypes_match_scalar_path(dtype) -> None:
    assets = pd.Index(["held", "unheld"], name="asset")
    previous = pd.Series([10, 0], index=assets, dtype=dtype)
    current = pd.Series([11, 0], index=assets, dtype=dtype)
    kwargs = dict(
        previous_holdings=pd.Series([1.0, 0.0], index=assets),
        previous_date=pd.Timestamp("2024-01-01"),
        current_date=pd.Timestamp("2024-01-02"), missing_price_policy="raise",
    )
    actual = portfolio_module._calculate_held_asset_returns(
        previous_prices=previous, current_prices=current, **kwargs,
    )
    expected = portfolio_module._calculate_held_asset_returns(
        previous_prices=previous.astype(object), current_prices=current.astype(object), **kwargs,
    )
    pd.testing.assert_series_equal(actual, expected, check_exact=True)


def test_timing_001_hand_calculated_reference_case() -> None:
    dates = pd.bdate_range("2025-01-06", periods=4)
    prices = pd.DataFrame(
        [[100.0, 100.0], [100.0, 100.0], [110.0, 100.0], [110.0, 100.0]],
        index=dates,
        columns=["AAA", "BBB"],
    )
    signals = pd.DataFrame(
        [[2.0, 1.0], [1.0, 2.0], [1.0, 2.0], [2.0, 1.0]],
        index=dates,
        columns=prices.columns,
    )
    benchmark = pd.Series(
        [100.0, 100.0, 102.0, 100.98],
        index=dates,
        name="benchmark",
    )

    result = _run(
        prices,
        signals,
        transaction_cost_bps=100.0,
        benchmark_prices=benchmark,
    )

    np.testing.assert_allclose(result.gross_returns, [0.0, 0.0, 0.1, 0.0])
    np.testing.assert_allclose(result.turnover, [0.0, 1.0, 2.0, 0.0])
    np.testing.assert_allclose(result.transaction_costs, [0.0, 0.01, 0.022, 0.0])
    np.testing.assert_allclose(result.returns, [0.0, -0.01, 0.078, 0.0])
    np.testing.assert_allclose(result.equity_curve, [1.0, 0.99, 1.06722, 1.06722])
    np.testing.assert_allclose(
        result.holdings,
        [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0]],
    )
    np.testing.assert_allclose(
        result.signed_trade_weights.loc[dates[1]],
        [1.0, 0.0],
    )
    np.testing.assert_allclose(
        result.signed_trade_weights.loc[dates[2]],
        [-1.0, 1.0],
    )
    assert result.metrics["total_return"] == pytest.approx(0.06722)
    assert result.metrics["average_turnover"] == pytest.approx(1.0)
    assert result.timing_metadata["measured_return_count"] == 3
    assert result.timing_metadata["resolved_rebalance_dates"] == tuple(dates)

    ledger = [asdict(row) for row in result.timing_ledger]
    assert ledger[0]["event_status"] == "initialization_anchor_no_execution"
    assert ledger[1]["signal_source_date"] == dates[0]
    assert ledger[1]["first_holding_return_end"] == dates[2]
    assert ledger[-1]["is_terminal_scheduled_row"] is True
    assert ledger[-1]["first_holding_return_end"] is None


@pytest.mark.parametrize(
    "lag",
    [0, False, 0.0, -1, 1.5, "1", None],
)
def test_timing_002_rejects_invalid_signal_lag_before_alignment(lag: object) -> None:
    dates = pd.bdate_range("2025-01-06", periods=3)
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)
    mismatched_signals = pd.DataFrame(
        {"BBB": [1.0, 1.0, 1.0]},
        index=dates[::-1],
    )

    with pytest.raises(BacktestValidationError, match="signal_lag_invalid") as exc:
        _run(
            prices,
            mismatched_signals,
            signal_lag_periods=lag,  # type: ignore[arg-type]
        )

    assert exc.value.reason == "signal_lag_invalid"


@pytest.mark.parametrize(
    "invalid_value",
    [
        True,
        1.0 + 0.0j,
        1.0 + 2.0j,
        complex(1.0, float("nan")),
        "1",
        np.inf,
        -np.inf,
        None,
        pd.NA,
    ],
)
def test_timing_003_rejects_invalid_bounded_signal_values(
    invalid_value: object,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=4)
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0, 103.0]}, index=dates)
    signals = pd.DataFrame(
        {"AAA": [1.0, invalid_value, 1.0, 1.0]},
        index=dates,
        dtype=object,
    )

    with pytest.raises(BacktestValidationError, match="signal_value_invalid") as exc:
        _run(prices, signals)

    assert exc.value.reason == "signal_value_invalid"


@pytest.mark.parametrize(
    "outside_value",
    [True, 1.0 + 0.0j, 1.0 + 2.0j, "1", np.inf, -np.inf, None, pd.NA],
)
@pytest.mark.filterwarnings(
    "ignore:Setting an item of incompatible dtype is deprecated:FutureWarning"
)
def test_timing_003_out_of_window_signal_values_do_not_change_result(
    outside_value: object,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=6)
    prices = pd.DataFrame(
        {"AAA": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]},
        index=dates,
    )
    signals = pd.DataFrame({"AAA": np.ones(6)}, index=dates)
    source_provenance = capture_backtest_source_provenance(prices, signals)
    baseline = _run_long_only_backtest(
        prices,
        signals,
        source_provenance=source_provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[4],
        rebalance_frequency="D",
        top_n=1,
    )

    mutated_prices, mutated_signals, mutated_provenance = (
        apply_tracked_backtest_source_mutation(
            prices,
            signals,
            source_provenance,
            source_role="signals",
            row_position=0,
            column_position=0,
            value=outside_value,
        )
    )
    mutated_prices, mutated_signals, mutated_provenance = (
        apply_tracked_backtest_source_mutation(
            mutated_prices,
            mutated_signals,
            mutated_provenance,
            source_role="signals",
            row_position=-1,
            column_position=0,
            value=outside_value,
        )
    )
    observed = _run_long_only_backtest(
        mutated_prices,
        mutated_signals,
        source_provenance=mutated_provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[4],
        rebalance_frequency="D",
        top_n=1,
    )

    pd.testing.assert_series_equal(observed.returns, baseline.returns)
    pd.testing.assert_frame_equal(observed.holdings, baseline.holdings)
    assert observed.metrics == baseline.metrics


def test_timing_003_outside_complex_then_object_write_preserves_bounded_result() -> None:
    dates = pd.bdate_range("2025-01-06", periods=6)
    prices = pd.DataFrame(
        {"AAA": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]},
        index=dates,
    )
    signals = pd.DataFrame({"AAA": np.ones(6)}, index=dates)
    provenance = capture_backtest_source_provenance(prices, signals)
    baseline = _run_long_only_backtest(
        prices,
        signals,
        source_provenance=provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[4],
        rebalance_frequency="D",
        top_n=1,
    )
    tracked_prices, tracked_signals, provenance = (
        apply_tracked_backtest_source_mutation(
            prices,
            signals,
            provenance,
            source_role="signals",
            row_position=0,
            column_position=0,
            value=1.0 + 0.0j,
        )
    )
    tracked_prices, tracked_signals, provenance = (
        apply_tracked_backtest_source_mutation(
            tracked_prices,
            tracked_signals,
            provenance,
            source_role="signals",
            row_position=-1,
            column_position=0,
            value="outside",
        )
    )
    assert pd.api.types.is_object_dtype(tracked_signals["AAA"].dtype)

    observed = _run_long_only_backtest(
        tracked_prices,
        tracked_signals,
        source_provenance=provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[4],
        rebalance_frequency="D",
        top_n=1,
    )

    pd.testing.assert_series_equal(observed.returns, baseline.returns)
    pd.testing.assert_frame_equal(observed.holdings, baseline.holdings)
    assert observed.metrics == baseline.metrics
    assert (
        observed.timing_metadata["backtest_source_provenance_status"]
        == "validated_with_tracked_complex_recovery"
    )


@pytest.mark.filterwarnings(
    "ignore:Setting an item of incompatible dtype is deprecated:FutureWarning"
)
def test_timing_003_complex_upcast_preserves_bounded_ieee_nan() -> None:
    dates = pd.bdate_range("2025-01-06", periods=6)
    prices = pd.DataFrame({"AAA": np.full(6, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, np.nan, 1.0, 1.0, 1.0]}, index=dates)
    source_provenance = capture_backtest_source_provenance(prices, signals)
    baseline = _run_long_only_backtest(
        prices,
        signals,
        source_provenance=source_provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[4],
        rebalance_frequency="D",
        top_n=1,
    )
    mutated_prices, mutated_signals, mutated_provenance = (
        apply_tracked_backtest_source_mutation(
            prices,
            signals,
            source_provenance,
            source_role="signals",
            row_position=0,
            column_position=0,
            value=1.0 + 2.0j,
        )
    )

    observed = _run_long_only_backtest(
        mutated_prices,
        mutated_signals,
        source_provenance=mutated_provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[4],
        rebalance_frequency="D",
        top_n=1,
    )

    pd.testing.assert_series_equal(observed.returns, baseline.returns)
    pd.testing.assert_frame_equal(observed.holdings, baseline.holdings)
    assert observed.metrics == baseline.metrics


def test_timing_003_complex_upcast_preserves_bounded_signed_zero() -> None:
    dates = pd.bdate_range("2025-01-06", periods=5)
    prices = pd.DataFrame({"AAA": np.full(5, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": np.full(5, -0.0)}, index=dates)
    source_provenance = capture_backtest_source_provenance(prices, signals)
    baseline = _run_long_only_backtest(
        prices,
        signals,
        source_provenance=source_provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[-1],
        rebalance_frequency="D",
        top_n=1,
    )
    mutated_prices, mutated_signals, mutated_provenance = (
        apply_tracked_backtest_source_mutation(
            prices,
            signals,
            source_provenance,
            source_role="signals",
            row_position=0,
            column_position=0,
            value=1.0 + 2.0j,
        )
    )

    observed = _run_long_only_backtest(
        mutated_prices,
        mutated_signals,
        source_provenance=mutated_provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[-1],
        rebalance_frequency="D",
        top_n=1,
    )

    pd.testing.assert_series_equal(observed.returns, baseline.returns)
    pd.testing.assert_frame_equal(observed.holdings, baseline.holdings)
    assert observed.metrics == baseline.metrics


def test_timing_003_object_complex_inside_stays_invalid_after_outside_mutation() -> None:
    dates = pd.bdate_range("2025-01-06", periods=5)
    prices = pd.DataFrame({"AAA": np.full(5, 100.0)}, index=dates)
    signals = pd.DataFrame(
        {"AAA": [1.0 + 2.0j, 1.0, 1.0 + 0.0j, 1.0, 1.0]},
        index=dates,
        dtype=object,
    )

    with pytest.raises(BacktestValidationError, match="signal_value_invalid") as exc:
        run_long_only_backtest(
            prices,
            signals,
            evaluation_start=dates[1],
            evaluation_end=dates[-1],
            rebalance_frequency="D",
            top_n=1,
        )

    assert exc.value.reason == "signal_value_invalid"
    assert exc.value.date == dates[2]
    assert exc.value.asset == "AAA"


@pytest.mark.parametrize("outside_position", [0, -1])
@pytest.mark.parametrize(
    "outside_value",
    [
        True,
        100.0 + 0.0j,
        100.0 + 2.0j,
        "100",
        np.inf,
        -np.inf,
        None,
        pd.NA,
    ],
)
@pytest.mark.filterwarnings(
    "ignore:Setting an item of incompatible dtype is deprecated:FutureWarning"
)
def test_timing_003_out_of_window_price_values_do_not_change_result(
    outside_position: int,
    outside_value: object,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=6)
    prices = pd.DataFrame({"AAA": [98.0, 100.0, 101.0, 102.0, 103.0, 104.0]}, index=dates)
    signals = pd.DataFrame({"AAA": np.ones(6)}, index=dates)
    source_provenance = capture_backtest_source_provenance(prices, signals)
    baseline = _run_long_only_backtest(
        prices,
        signals,
        source_provenance=source_provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[4],
        rebalance_frequency="D",
        top_n=1,
    )
    mutated_prices, mutated_signals, mutated_provenance = (
        apply_tracked_backtest_source_mutation(
            prices,
            signals,
            source_provenance,
            source_role="prices",
            row_position=outside_position,
            column_position=0,
            value=outside_value,
        )
    )

    observed = _run_long_only_backtest(
        mutated_prices,
        mutated_signals,
        source_provenance=mutated_provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[4],
        rebalance_frequency="D",
        top_n=1,
    )

    pd.testing.assert_series_equal(observed.returns, baseline.returns)
    pd.testing.assert_frame_equal(observed.holdings, baseline.holdings)
    assert observed.metrics == baseline.metrics


@pytest.mark.filterwarnings(
    "ignore:Setting an item of incompatible dtype is deprecated:FutureWarning"
)
def test_timing_003_outside_mutation_preserves_bounded_exception_evidence() -> None:
    dates = pd.bdate_range("2025-01-06", periods=5)
    prices = pd.DataFrame({"AAA": np.full(5, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, np.inf, 1.0, 1.0]}, index=dates)

    def _capture(
        candidate: pd.DataFrame,
        provenance: BacktestSourceProvenance,
    ) -> tuple[str, pd.Timestamp | None, str | None]:
        with pytest.raises(
            BacktestValidationError,
            match="signal_value_invalid",
        ) as exc:
            _run_long_only_backtest(
                prices,
                candidate,
                source_provenance=provenance,
                evaluation_start=dates[1],
                evaluation_end=dates[-1],
                rebalance_frequency="D",
                top_n=1,
            )
        return exc.value.reason, exc.value.date, exc.value.asset

    source_provenance = capture_backtest_source_provenance(prices, signals)
    baseline = _capture(signals, source_provenance)
    _, mutated_signals, mutated_provenance = (
        apply_tracked_backtest_source_mutation(
            prices,
            signals,
            source_provenance,
            source_role="signals",
            row_position=0,
            column_position=0,
            value=1.0 + 2.0j,
        )
    )

    assert _capture(mutated_signals, mutated_provenance) == baseline


@pytest.mark.filterwarnings(
    "ignore:Setting an item of incompatible dtype is deprecated:FutureWarning"
)
def test_timing_003_mutation_ledger_distinguishes_identical_complex_frames() -> None:
    dates = pd.bdate_range("2025-01-06", periods=5)
    prices = pd.DataFrame({"AAA": np.full(5, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": np.ones(5)}, index=dates)
    source_provenance = capture_backtest_source_provenance(prices, signals)

    outside_prices, outside_signals, outside_provenance = (
        apply_tracked_backtest_source_mutation(
            prices,
            signals,
            source_provenance,
            source_role="signals",
            row_position=0,
            column_position=0,
            value=1.0 + 0.0j,
        )
    )
    bounded_prices, bounded_signals, bounded_provenance = (
        apply_tracked_backtest_source_mutation(
            prices,
            signals,
            source_provenance,
            source_role="signals",
            row_position=1,
            column_position=0,
            value=1.0 + 0.0j,
        )
    )
    assert outside_signals.equals(bounded_signals)

    outside_result = _run_long_only_backtest(
        outside_prices,
        outside_signals,
        source_provenance=outside_provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[3],
        rebalance_frequency="D",
        top_n=1,
    )
    assert (
        outside_result.timing_metadata["backtest_source_provenance_status"]
        == "validated_with_tracked_complex_recovery"
    )

    both_prices, both_signals, both_provenance = (
        apply_tracked_backtest_source_mutation(
            outside_prices,
            outside_signals,
            outside_provenance,
            source_role="signals",
            row_position=2,
            column_position=0,
            value=1.0 + 0.0j,
        )
    )
    assert both_signals.equals(outside_signals)
    with pytest.raises(BacktestValidationError, match="signal_value_invalid") as exc:
        _run_long_only_backtest(
            both_prices,
            both_signals,
            source_provenance=both_provenance,
            evaluation_start=dates[1],
            evaluation_end=dates[3],
            rebalance_frequency="D",
            top_n=1,
        )
    assert exc.value.date == dates[2]
    assert exc.value.asset == "AAA"

    with pytest.raises(BacktestValidationError, match="signal_value_invalid") as exc:
        _run_long_only_backtest(
            bounded_prices,
            bounded_signals,
            source_provenance=bounded_provenance,
            evaluation_start=dates[1],
            evaluation_end=dates[3],
            rebalance_frequency="D",
            top_n=1,
        )
    assert exc.value.reason == "signal_value_invalid"
    assert exc.value.date == dates[1]
    assert exc.value.asset == "AAA"


def test_timing_003_latest_tracked_bounded_assignment_controls_recovery() -> None:
    dates = pd.bdate_range("2025-01-06", periods=5)
    prices = pd.DataFrame(
        {
            "AAA": np.full(5, 100.0),
            "BBB": np.full(5, 100.0),
        },
        index=dates,
    )
    signals = pd.DataFrame(
        {
            "AAA": np.ones(5),
            "BBB": np.full(5, 2.0),
        },
        index=dates,
    )
    provenance = capture_backtest_source_provenance(prices, signals)
    tracked_prices, tracked_signals, provenance = (
        apply_tracked_backtest_source_mutation(
            prices,
            signals,
            provenance,
            source_role="signals",
            row_position=0,
            column_position=0,
            value=1.0 + 0.0j,
        )
    )
    tracked_prices, tracked_signals, provenance = (
        apply_tracked_backtest_source_mutation(
            tracked_prices,
            tracked_signals,
            provenance,
            source_role="signals",
            row_position=1,
            column_position=0,
            value=3.0 + 0.0j,
        )
    )
    tracked_prices, tracked_signals, provenance = (
        apply_tracked_backtest_source_mutation(
            tracked_prices,
            tracked_signals,
            provenance,
            source_role="signals",
            row_position=1,
            column_position=0,
            value=3.0,
        )
    )
    assert pd.api.types.is_complex_dtype(tracked_signals["AAA"].dtype)

    recovered = _run_long_only_backtest(
        tracked_prices,
        tracked_signals,
        source_provenance=provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[3],
        rebalance_frequency="D",
        top_n=1,
    )
    assert recovered.holdings.loc[dates[2], "AAA"] == pytest.approx(1.0)
    assert (
        recovered.timing_metadata["backtest_source_provenance_status"]
        == "validated_with_tracked_complex_recovery"
    )

    tracked_prices, tracked_signals, provenance = (
        apply_tracked_backtest_source_mutation(
            tracked_prices,
            tracked_signals,
            provenance,
            source_role="signals",
            row_position=1,
            column_position=0,
            value=3.0 + 0.0j,
        )
    )
    with pytest.raises(BacktestValidationError, match="signal_value_invalid") as exc:
        _run_long_only_backtest(
            tracked_prices,
            tracked_signals,
            source_provenance=provenance,
            evaluation_start=dates[1],
            evaluation_end=dates[3],
            rebalance_frequency="D",
            top_n=1,
        )

    assert exc.value.date == dates[1]
    assert exc.value.asset == "AAA"


def test_timing_003_native_homogeneous_complex_source_is_not_recovered() -> None:
    dates = pd.bdate_range("2025-01-06", periods=4)
    prices = pd.DataFrame({"AAA": np.full(4, 100.0)}, index=dates)
    signals = pd.DataFrame(
        {"AAA": np.full(4, 1.0 + 0.0j, dtype=complex)},
        index=dates,
    )
    source_provenance = capture_backtest_source_provenance(prices, signals)

    with pytest.raises(BacktestValidationError, match="signal_value_invalid") as exc:
        _run_long_only_backtest(
            prices,
            signals,
            source_provenance=source_provenance,
            evaluation_start=dates[0],
            evaluation_end=dates[-1],
            rebalance_frequency="D",
            top_n=1,
        )

    assert exc.value.reason == "signal_value_invalid"
    assert exc.value.date == dates[0]
    assert exc.value.asset == "AAA"


def test_timing_003_capture_cannot_infer_pre_capture_type_history() -> None:
    dates = pd.bdate_range("2025-01-06", periods=4)
    prices = pd.DataFrame({"AAA": np.full(4, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": np.ones(4)}, index=dates)
    signals.isetitem(0, signals.iloc[:, 0].astype(complex))
    signals.iat[0, 0] = 1.0 + 0.0j
    source_provenance = capture_backtest_source_provenance(prices, signals)

    with pytest.raises(BacktestValidationError, match="signal_value_invalid") as exc:
        _run_long_only_backtest(
            prices,
            signals,
            source_provenance=source_provenance,
            evaluation_start=dates[1],
            evaluation_end=dates[-1],
            rebalance_frequency="D",
            top_n=1,
        )

    assert exc.value.reason == "signal_value_invalid"
    assert exc.value.date == dates[1]
    assert exc.value.asset == "AAA"


def test_timing_003_source_provenance_is_required_and_has_no_bypass() -> None:
    parameter = inspect.signature(_run_long_only_backtest).parameters[
        "source_provenance"
    ]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty

    dates = pd.bdate_range("2025-01-06", periods=3)
    prices = pd.DataFrame({"AAA": np.full(3, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": np.ones(3)}, index=dates)
    with pytest.raises(TypeError, match="source_provenance"):
        _run_long_only_backtest(
            prices,
            signals,
            evaluation_start=dates[0],
            evaluation_end=dates[-1],
            rebalance_frequency="D",
            top_n=1,
        )
    with pytest.raises(
        BacktestValidationError,
        match="source_provenance_invalid",
    ) as exc:
        _run_long_only_backtest(
            prices,
            signals,
            source_provenance=None,  # type: ignore[arg-type]
            evaluation_start=dates[0],
            evaluation_end=dates[-1],
            rebalance_frequency="D",
            top_n=1,
        )
    assert exc.value.reason == "source_provenance_invalid"


@pytest.mark.parametrize("untracked_change", ["in_place", "astype"])
@pytest.mark.filterwarnings(
    "ignore:Setting an item of incompatible dtype is deprecated:FutureWarning"
)
def test_timing_003_untracked_source_changes_fail_closed(
    untracked_change: str,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=5)
    prices = pd.DataFrame({"AAA": np.full(5, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": np.ones(5)}, index=dates)
    source_provenance = capture_backtest_source_provenance(prices, signals)
    if untracked_change == "in_place":
        signals.isetitem(0, signals.iloc[:, 0].astype(complex))
        signals.iat[0, 0] = 1.0 + 0.0j
        changed_signals = signals
    else:
        changed_signals = signals.astype(complex)

    with pytest.raises(
        BacktestValidationError,
        match="source_provenance_invalid",
    ) as exc:
        _run_long_only_backtest(
            prices,
            changed_signals,
            source_provenance=source_provenance,
            evaluation_start=dates[1],
            evaluation_end=dates[-1],
            rebalance_frequency="D",
            top_n=1,
        )

    assert exc.value.reason == "source_provenance_invalid"


def test_timing_003_wrong_role_and_tampered_ledger_fail_closed() -> None:
    dates = pd.bdate_range("2025-01-06", periods=5)
    prices = pd.DataFrame({"AAA": np.full(5, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": np.ones(5)}, index=dates)
    source_provenance = capture_backtest_source_provenance(prices, signals)
    swapped = replace(
        source_provenance,
        prices=source_provenance.signals,
        signals=source_provenance.prices,
    )

    with pytest.raises(
        BacktestValidationError,
        match="source_provenance_invalid",
    ):
        _run_long_only_backtest(
            prices,
            signals,
            source_provenance=swapped,
            evaluation_start=dates[0],
            evaluation_end=dates[-1],
            rebalance_frequency="D",
            top_n=1,
        )

    mutated_prices, mutated_signals, mutated_provenance = (
        apply_tracked_backtest_source_mutation(
            prices,
            signals,
            source_provenance,
            source_role="signals",
            row_position=0,
            column_position=0,
            value=1.0 + 2.0j,
        )
    )
    record = mutated_provenance.signals.mutations[0]
    tampered_signal_provenance = replace(
        mutated_provenance.signals,
        mutations=(replace(record, row_position=1),),
    )
    tampered = replace(
        mutated_provenance,
        signals=tampered_signal_provenance,
    )
    with pytest.raises(
        BacktestValidationError,
        match="source_provenance_invalid",
    ):
        _run_long_only_backtest(
            mutated_prices,
            mutated_signals,
            source_provenance=tampered,
            evaluation_start=dates[1],
            evaluation_end=dates[-1],
            rebalance_frequency="D",
            top_n=1,
        )


@pytest.mark.parametrize("axis_change", ["index_name", "column_name", "timezone"])
def test_timing_003_stale_axis_bound_provenance_fails_closed(
    axis_change: str,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=4)
    prices = pd.DataFrame({"AAA": np.full(4, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": np.ones(4)}, index=dates)
    source_provenance = capture_backtest_source_provenance(prices, signals)
    evaluation_start = dates[0]
    evaluation_end = dates[-1]
    if axis_change == "index_name":
        prices.index.name = "changed_date"
        signals.index.name = "changed_date"
    elif axis_change == "column_name":
        prices.columns.name = "changed_asset"
        signals.columns.name = "changed_asset"
    else:
        prices.index = prices.index.tz_localize("UTC")
        signals.index = signals.index.tz_localize("UTC")
        evaluation_start = prices.index[0]
        evaluation_end = prices.index[-1]

    with pytest.raises(
        BacktestValidationError,
        match="source_provenance_invalid",
    ) as exc:
        _run_long_only_backtest(
            prices,
            signals,
            source_provenance=source_provenance,
            evaluation_start=evaluation_start,
            evaluation_end=evaluation_end,
            rebalance_frequency="D",
            top_n=1,
        )

    assert exc.value.reason == "source_provenance_invalid"


@pytest.mark.filterwarnings(
    "ignore:Setting an item of incompatible dtype is deprecated:FutureWarning"
)
def test_timing_003_complex_evidence_inside_changed_bounds_is_not_recovered() -> None:
    dates = pd.bdate_range("2025-01-06", periods=5)
    prices = pd.DataFrame({"AAA": np.full(5, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": np.ones(5)}, index=dates)
    source_provenance = capture_backtest_source_provenance(prices, signals)
    mutated_prices, mutated_signals, mutated_provenance = (
        apply_tracked_backtest_source_mutation(
            prices,
            signals,
            source_provenance,
            source_role="signals",
            row_position=0,
            column_position=0,
            value=1.0 + 0.0j,
        )
    )

    with pytest.raises(BacktestValidationError, match="signal_value_invalid") as exc:
        _run_long_only_backtest(
            mutated_prices,
            mutated_signals,
            source_provenance=mutated_provenance,
            evaluation_start=dates[0],
            evaluation_end=dates[3],
            rebalance_frequency="D",
            top_n=1,
        )

    assert exc.value.date == dates[0]
    assert exc.value.asset == "AAA"


@pytest.mark.filterwarnings(
    "ignore:Setting an item of incompatible dtype is deprecated:FutureWarning"
)
def test_timing_003_lossy_integer_upcast_is_not_recovered() -> None:
    dates = pd.bdate_range("2025-01-06", periods=5)
    prices = pd.DataFrame({"AAA": np.full(5, 100.0)}, index=dates)
    large_integer = 2**53 + 1
    signals = pd.DataFrame(
        {"AAA": np.full(5, large_integer, dtype=np.int64)},
        index=dates,
    )
    source_provenance = capture_backtest_source_provenance(prices, signals)
    mutated_prices, mutated_signals, mutated_provenance = (
        apply_tracked_backtest_source_mutation(
            prices,
            signals,
            source_provenance,
            source_role="signals",
            row_position=0,
            column_position=0,
            value=complex(large_integer, 0.0),
        )
    )

    with pytest.raises(BacktestValidationError, match="signal_value_invalid") as exc:
        _run_long_only_backtest(
            mutated_prices,
            mutated_signals,
            source_provenance=mutated_provenance,
            evaluation_start=dates[1],
            evaluation_end=dates[-1],
            rebalance_frequency="D",
            top_n=1,
        )

    assert exc.value.date == dates[1]
    assert exc.value.asset == "AAA"


@pytest.mark.parametrize("signal_kind", ["nullable_float", "numeric_categorical"])
def test_timing_003_tracked_outside_complex_preserves_extension_signals(
    signal_kind: str,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=4)
    prices = pd.DataFrame({"AAA": np.full(4, 100.0)}, index=dates)
    values = (
        pd.array([pd.NA, 1.0, 1.0, 1.0], dtype="Float64")
        if signal_kind == "nullable_float"
        else pd.Categorical([1.0, 1.0, 1.0, 1.0])
    )
    signals = pd.DataFrame({"AAA": values}, index=dates)
    source_provenance = capture_backtest_source_provenance(prices, signals)
    baseline = _run_long_only_backtest(
        prices,
        signals,
        source_provenance=source_provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[-1],
        rebalance_frequency="D",
        top_n=1,
    )
    mutated_prices, mutated_signals, mutated_provenance = (
        apply_tracked_backtest_source_mutation(
            prices,
            signals,
            source_provenance,
            source_role="signals",
            row_position=0,
            column_position=0,
            value=1.0 + 2.0j,
        )
    )

    observed = _run_long_only_backtest(
        mutated_prices,
        mutated_signals,
        source_provenance=mutated_provenance,
        evaluation_start=dates[1],
        evaluation_end=dates[-1],
        rebalance_frequency="D",
        top_n=1,
    )

    pd.testing.assert_series_equal(observed.returns, baseline.returns)
    pd.testing.assert_frame_equal(observed.holdings, baseline.holdings)
    assert observed.metrics == baseline.metrics


def test_timing_003_custom_real_is_rejected_at_provenance_capture() -> None:
    class MutableReal:
        def __init__(self, value: float) -> None:
            self.value = value

        def __float__(self) -> float:
            return self.value

        def __repr__(self) -> str:
            return "MutableReal(constant-repr)"

    Real.register(MutableReal)

    dates = pd.bdate_range("2025-01-06", periods=4)
    prices = pd.DataFrame(
        {
            "AAA": np.full(4, 100.0),
            "BBB": np.full(4, 100.0),
        },
        index=dates,
    )
    mutable_score = MutableReal(2.0)
    signals = pd.DataFrame(
        {
            "AAA": [mutable_score, 1.0, 1.0, 1.0],
            "BBB": [1.0, 1.0, 1.0, 1.0],
        },
        index=dates,
        dtype=object,
    )
    with pytest.raises(
        BacktestValidationError,
        match="source_provenance_invalid",
    ) as exc:
        capture_backtest_source_provenance(prices, signals)

    assert exc.value.reason == "source_provenance_invalid"


def test_timing_003_stateful_custom_real_is_never_observed_economically() -> None:
    class StatefulReal:
        def __init__(self) -> None:
            self.float_calls = 0

        def __float__(self) -> float:
            self.float_calls += 1
            return 2.0 if self.float_calls <= 2 else 0.0

        def __repr__(self) -> str:
            return "StatefulReal(constant-repr)"

    Real.register(StatefulReal)

    dates = pd.bdate_range("2025-01-06", periods=3)
    prices = pd.DataFrame({"AAA": np.full(3, 100.0)}, index=dates)
    stateful_score = StatefulReal()
    signals = pd.DataFrame(
        {"AAA": [stateful_score, 1.0, 1.0]},
        index=dates,
        dtype=object,
    )

    with pytest.raises(
        BacktestValidationError,
        match="source_provenance_invalid",
    ):
        capture_backtest_source_provenance(prices, signals)

    assert stateful_score.float_calls == 0


def test_timing_003_stateful_float_subclass_is_rejected_without_conversion() -> None:
    class StatefulFloat(float):
        def __new__(cls, value: float):
            instance = super().__new__(cls, value)
            instance.float_calls = 0
            return instance

        def __float__(self) -> float:
            self.float_calls += 1
            return 2.0 if self.float_calls <= 2 else 0.0

    dates = pd.bdate_range("2025-01-06", periods=3)
    prices = pd.DataFrame({"AAA": np.full(3, 100.0)}, index=dates)
    stateful_score = StatefulFloat(2.0)
    signals = pd.DataFrame(
        {"AAA": [stateful_score, 1.0, 1.0]},
        index=dates,
        dtype=object,
    )

    with pytest.raises(
        BacktestValidationError,
        match="source_provenance_invalid",
    ):
        capture_backtest_source_provenance(prices, signals)

    assert stateful_score.float_calls == 0


@pytest.mark.skipif(
    np.finfo(np.longdouble).nmant <= np.finfo(np.float64).nmant,
    reason="platform longdouble has no precision beyond float64",
)
@pytest.mark.parametrize("wide_type", [np.longdouble, np.clongdouble])
def test_timing_003_rejects_source_scalars_wider_than_float64(
    wide_type: type[np.generic],
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=3)
    prices = pd.DataFrame({"AAA": np.full(3, 100.0)}, index=dates)
    wide_value = np.nextafter(
        np.longdouble(1.0),
        np.longdouble(2.0),
    )
    assert wide_value != np.longdouble(1.0)
    assert float(wide_value) == 1.0
    signals = pd.DataFrame(
        {"AAA": [wide_type(wide_value), 1.0, 1.0]},
        index=dates,
        dtype=object,
    )

    with pytest.raises(
        BacktestValidationError,
        match="source_provenance_invalid",
    ):
        capture_backtest_source_provenance(prices, signals)


@pytest.mark.parametrize(
    "columns",
    [
        pd.Index([None], name="asset_id"),
        pd.MultiIndex.from_tuples(
            [("technology", "AAA"), ("financials", "BBB")],
            names=["sector", "ticker"],
        ),
    ],
)
def test_timing_003_bounded_extraction_preserves_exact_asset_axis(
    columns: pd.Index,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=4)
    prices = pd.DataFrame(
        np.full((4, len(columns)), 100.0),
        index=dates,
        columns=columns,
    )
    signals = pd.DataFrame(
        np.ones((4, len(columns))),
        index=dates,
        columns=columns,
    )

    result = _run(prices, signals)

    pd.testing.assert_index_equal(result.holdings.columns, columns, exact=True)
    pd.testing.assert_index_equal(
        result.signed_trade_weights.columns,
        columns,
        exact=True,
    )
    pd.testing.assert_index_equal(
        result.trade_weights.columns,
        columns,
        exact=True,
    )


def test_timing_003_ieee_nan_is_the_only_unavailable_signal_sentinel() -> None:
    dates = pd.bdate_range("2025-01-06", periods=3)
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [np.nan, 1.0, 1.0]}, index=dates)

    result = _run(prices, signals)

    assert result.holdings.loc[dates[1], "AAA"] == 0.0
    assert result.timing_ledger[1].event_status == "executed_cash_target"


@pytest.mark.parametrize(
    "kind",
    [
        "reordered_dates",
        "missing_date",
        "extra_date",
        "duplicate_date",
        "reordered_assets",
        "missing_asset",
        "extra_asset",
        "duplicate_asset",
        "timezone",
    ],
)
def test_timing_003_requires_exact_full_source_axes(kind: str) -> None:
    dates = pd.bdate_range("2025-01-06", periods=3)
    prices = pd.DataFrame(
        {"AAA": [100.0, 101.0, 102.0], "BBB": [200.0, 201.0, 202.0]},
        index=dates,
    )
    signals = pd.DataFrame(
        {"AAA": [1.0, 1.0, 1.0], "BBB": [2.0, 2.0, 2.0]},
        index=dates,
    )
    if kind == "reordered_dates":
        signals = signals.iloc[::-1]
    elif kind == "missing_date":
        signals = signals.iloc[:-1]
    elif kind == "extra_date":
        signals.loc[dates[-1] + pd.offsets.BDay()] = [1.0, 2.0]
    elif kind == "duplicate_date":
        signals.index = pd.DatetimeIndex([dates[0], dates[1], dates[1]])
    elif kind == "reordered_assets":
        signals = signals.loc[:, ["BBB", "AAA"]]
    elif kind == "missing_asset":
        signals = signals.loc[:, ["AAA"]]
    elif kind == "extra_asset":
        signals["CCC"] = 3.0
    elif kind == "duplicate_asset":
        signals = pd.DataFrame(
            np.ones((3, 2)),
            index=dates,
            columns=["AAA", "AAA"],
        )
    elif kind == "timezone":
        signals.index = signals.index.tz_localize("UTC")

    with pytest.raises(BacktestValidationError, match="source_axes_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            evaluation_start=dates[0],
            evaluation_end=dates[-1],
            rebalance_frequency="D",
            top_n=1,
        )


def test_timing_004_lag_counts_irregular_observed_rows() -> None:
    dates = pd.DatetimeIndex(["2025-01-03", "2025-01-06", "2025-01-08"])
    prices = pd.DataFrame(
        {"AAA": [100.0, 100.0, 100.0], "BBB": [100.0, 100.0, 100.0]},
        index=dates,
    )
    signals = pd.DataFrame(
        {"AAA": [2.0, 1.0, 1.0], "BBB": [1.0, 2.0, 2.0]},
        index=dates,
    )

    lag_one = _run(prices, signals, signal_lag_periods=1)
    lag_two = _run(prices, signals, signal_lag_periods=2)

    assert lag_one.holdings.loc[dates[1], "AAA"] == 1.0
    assert lag_one.holdings.loc[dates[2], "BBB"] == 1.0
    assert lag_two.holdings.loc[dates[1]].sum() == 0.0
    assert lag_two.holdings.loc[dates[2], "AAA"] == 1.0
    assert lag_two.timing_ledger[1].event_status == "insufficient_lag_no_execution"


def test_timing_005_monthly_execution_uses_previous_source_row_signal() -> None:
    dates = pd.bdate_range("2025-01-29", periods=6)
    prices = pd.DataFrame(
        {"AAA": np.full(6, 100.0), "BBB": np.full(6, 100.0)},
        index=dates,
    )
    signals = pd.DataFrame(
        {
            "AAA": [1.0, 1.0, 2.0, 1.0, 1.0, 1.0],
            "BBB": [2.0, 2.0, 1.0, 2.0, 2.0, 2.0],
        },
        index=dates,
    )

    result = run_long_only_backtest(
        prices,
        signals,
        evaluation_start=dates[0],
        evaluation_end=dates[-1],
        rebalance_frequency="ME",
        top_n=1,
    )

    january_execution = pd.Timestamp("2025-01-31")
    assert result.holdings.loc[january_execution, "BBB"] == 1.0
    january_ledger = next(
        row for row in result.timing_ledger if row.ledger_date == january_execution
    )
    assert january_ledger.signal_source_date == pd.Timestamp("2025-01-30")
    assert result.trade_weights.loc[pd.Timestamp("2025-01-30")].eq(0.0).all()


@pytest.mark.parametrize(
    "invalid_price",
    [
        np.nan,
        True,
        1.0 + 2.0j,
        "100",
        np.inf,
        -np.inf,
        0.0,
        -1.0,
        None,
        pd.NA,
        Fraction(10**400, 1),
    ],
)
def test_timing_006_rejects_invalid_intended_buy_price(
    invalid_price: object,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=3)
    prices = pd.DataFrame(
        {"AAA": [100.0, invalid_price, 100.0], "BBB": [100.0, 100.0, 100.0]},
        index=dates,
    )
    signals = pd.DataFrame(
        {"AAA": [2.0, 2.0, 2.0], "BBB": [1.0, 1.0, 1.0]},
        index=dates,
    )

    with pytest.raises(BacktestValidationError, match="execution_price_invalid") as exc:
        _run(prices, signals)

    assert exc.value.reason == "execution_price_invalid"


@pytest.mark.parametrize(
    "invalid_price",
    [
        np.nan,
        True,
        1.0 + 2.0j,
        "100",
        np.inf,
        -np.inf,
        0.0,
        -1.0,
        None,
        pd.NA,
        Fraction(10**400, 1),
    ],
)
def test_timing_006_rejects_invalid_held_incoming_endpoint(
    invalid_price: object,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=4)
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 100.0, invalid_price, 100.0],
            "BBB": [100.0, 100.0, 100.0, 100.0],
        },
        index=dates,
        dtype=object,
    )
    signals = pd.DataFrame(
        {"AAA": [2.0, 2.0, 2.0, 2.0], "BBB": [1.0, 1.0, 1.0, 1.0]},
        index=dates,
    )

    with pytest.raises(BacktestValidationError, match="incoming_price_invalid") as exc:
        _run(prices, signals)

    assert exc.value.reason == "incoming_price_invalid"


def test_timing_006_ignores_invalid_price_for_unheld_unselected_asset() -> None:
    dates = pd.bdate_range("2025-01-06", periods=4)
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 101.0, 102.0, 103.0],
            "BBB": ["bad", pd.NA, 0.0, np.inf],
        },
        index=dates,
    )
    signals = pd.DataFrame(
        {"AAA": [2.0, 2.0, 2.0, 2.0], "BBB": [1.0, 1.0, 1.0, 1.0]},
        index=dates,
    )

    result = _run(prices, signals)

    assert result.holdings["BBB"].eq(0.0).all()
    assert np.isfinite(result.returns).all()


@pytest.mark.parametrize(
    "invalid_price",
    [
        np.nan,
        True,
        1.0 + 2.0j,
        "100",
        np.inf,
        -np.inf,
        0.0,
        -1.0,
        None,
        pd.NA,
        Fraction(10**400, 1),
    ],
)
def test_timing_006_direct_sell_leg_validator_is_independent(
    invalid_price: object,
) -> None:
    date = pd.Timestamp("2025-01-07")
    prices = pd.Series({"AAA": invalid_price, "BBB": 100.0}, dtype=object)
    signed_trades = pd.Series({"AAA": -1.0, "BBB": 1.0})

    with pytest.raises(BacktestValidationError, match="execution_price_invalid"):
        _validate_execution_price_legs(
            execution_prices=prices,
            signed_trade_weights=signed_trades,
            date=date,
        )


def test_timing_007_execution_row_signal_cannot_change_frozen_current_target() -> None:
    dates = pd.bdate_range("2025-01-06", periods=4)
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 100.0, 110.0, 110.0],
            "BBB": [100.0, 100.0, 100.0, 100.0],
        },
        index=dates,
    )
    signals = pd.DataFrame(
        {
            "AAA": [2.0, 2.0, 2.0, 2.0],
            "BBB": [1.0, 1.0, 1.0, 1.0],
        },
        index=dates,
    )
    baseline = _run(prices, signals)

    mutated_signals = signals.copy()
    mutated_signals.loc[dates[1]] = [0.0, 10.0]
    signal_mutation = _run(prices, mutated_signals)
    assert signal_mutation.holdings.loc[dates[1]].equals(
        baseline.holdings.loc[dates[1]]
    )
    assert signal_mutation.gross_returns.loc[dates[2]] == pytest.approx(
        baseline.gross_returns.loc[dates[2]]
    )

    later_prices = prices.copy()
    later_prices.loc[dates[3], "BBB"] = 500.0
    later_price_mutation = _run(later_prices, signals)
    assert later_price_mutation.holdings.loc[dates[1]].equals(
        baseline.holdings.loc[dates[1]]
    )
    assert later_price_mutation.gross_returns.loc[dates[2]] == pytest.approx(
        baseline.gross_returns.loc[dates[2]]
    )


def test_timing_008_pre_anchor_history_cannot_satisfy_local_lag() -> None:
    dates = pd.bdate_range("2025-01-06", periods=6)
    prices = pd.DataFrame({"AAA": np.full(6, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": np.ones(6)}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        evaluation_start=dates[2],
        evaluation_end=dates[5],
        rebalance_frequency="D",
        top_n=1,
        signal_lag_periods=2,
    )

    assert result.holdings.loc[dates[2]].sum() == 0.0
    assert result.holdings.loc[dates[3]].sum() == 0.0
    assert result.holdings.loc[dates[4], "AAA"] == 1.0
    assert result.timing_ledger[0].event_status == "initialization_anchor_no_execution"
    assert result.timing_ledger[1].event_status == "insufficient_lag_no_execution"


def test_timing_008_mid_bucket_anchor_appears_once_in_ledger_union() -> None:
    dates = pd.bdate_range("2025-01-06", periods=10)
    prices = pd.DataFrame({"AAA": np.full(10, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": np.ones(10)}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        evaluation_start=dates[2],
        evaluation_end=dates[-1],
        rebalance_frequency="W-FRI",
        top_n=1,
    )

    ledger_dates = [row.ledger_date for row in result.timing_ledger]
    assert ledger_dates.count(dates[2]) == 1
    anchor = result.timing_ledger[0]
    assert anchor.ledger_date == dates[2]
    assert anchor.is_scheduled_rebalance is False
    assert anchor.scheduled_execution_date is None
    assert anchor.incoming_return_start is None
    assert anchor.first_holding_return_start is None


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2025-01", pd.Timestamp("2025-01-08")),
        (pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-08")),
        (pd.Timestamp("2025-01-06"), pd.Timestamp("2025-01-06")),
        (pd.Timestamp("2025-01-08"), pd.Timestamp("2025-01-06")),
    ],
)
def test_timing_009_requires_exact_ordered_timestamp_bounds(
    start: object,
    end: object,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=3)
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    with pytest.raises(BacktestValidationError, match="evaluation_bounds_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            evaluation_start=start,  # type: ignore[arg-type]
            evaluation_end=end,  # type: ignore[arg-type]
            rebalance_frequency="D",
            top_n=1,
        )


@pytest.mark.parametrize("timezone_case", ["aware_naive", "different_timezone"])
def test_timing_009_rejects_timezone_incompatible_bounds(
    timezone_case: str,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=3, tz="UTC")
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)
    if timezone_case == "aware_naive":
        start = dates[0].tz_localize(None)
        end = dates[-1]
    else:
        start = dates[0].tz_convert("America/New_York")
        end = dates[-1].tz_convert("America/New_York")

    with pytest.raises(BacktestValidationError, match="evaluation_bounds_invalid"):
        run_long_only_backtest(
            prices,
            signals,
            evaluation_start=start,
            evaluation_end=end,
            rebalance_frequency="D",
            top_n=1,
        )


def test_timing_009_long_warmup_is_excluded_from_all_period_metrics() -> None:
    dates = pd.bdate_range("2025-01-06", periods=12)
    prices = pd.DataFrame(
        {
            "AAA": [
                1.0,
                1000.0,
                2.0,
                800.0,
                4.0,
                600.0,
                100.0,
                102.0,
                101.0,
                104.0,
                103.0,
                106.0,
            ]
        },
        index=dates,
    )
    signals = pd.DataFrame({"AAA": np.ones(12)}, index=dates)
    accounting_dates = dates[6:]
    benchmark = pd.Series(
        [200.0, 201.0, 203.0, 202.0, 204.0, 205.0],
        index=accounting_dates,
    )

    with_warmup = run_long_only_backtest(
        prices,
        signals,
        evaluation_start=accounting_dates[0],
        evaluation_end=accounting_dates[-1],
        rebalance_frequency="D",
        top_n=1,
        benchmark_prices=benchmark,
    )
    exact_bounded = run_long_only_backtest(
        prices.loc[accounting_dates],
        signals.loc[accounting_dates],
        evaluation_start=accounting_dates[0],
        evaluation_end=accounting_dates[-1],
        rebalance_frequency="D",
        top_n=1,
        benchmark_prices=benchmark,
    )

    pd.testing.assert_index_equal(with_warmup.returns.index, accounting_dates)
    pd.testing.assert_index_equal(
        with_warmup.benchmark_returns.index,
        accounting_dates,
    )
    assert with_warmup.timing_metadata["measured_return_count"] == 5
    for metric_name in [
        "annualized_return",
        "annualized_volatility",
        "sharpe_ratio",
        "benchmark_total_return",
        "excess_total_return",
        "tracking_error",
        "average_turnover",
    ]:
        assert with_warmup.metrics[metric_name] == pytest.approx(
            exact_bounded.metrics[metric_name],
            nan_ok=True,
        )


@pytest.mark.parametrize(
    "capital",
    [
        True,
        False,
        1.0 + 2.0j,
        "1",
        None,
        0.0,
        -1.0,
        np.nan,
        np.inf,
        -np.inf,
        Fraction(10**400, 1),
    ],
)
def test_timing_010_rejects_invalid_initial_capital_before_accounting(
    capital: object,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=2)
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)

    with pytest.raises(BacktestValidationError, match="initial_capital_invalid"):
        _run(prices, signals, initial_capital=capital)  # type: ignore[arg-type]


def test_timing_010_rejects_stateful_initial_capital_without_conversion() -> None:
    class StatefulReal:
        def __init__(self) -> None:
            self.float_calls = 0

        def __float__(self) -> float:
            self.float_calls += 1
            return 1.0 if self.float_calls == 1 else 2.0

    Real.register(StatefulReal)

    dates = pd.bdate_range("2025-01-06", periods=2)
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)
    capital = StatefulReal()

    with pytest.raises(BacktestValidationError, match="initial_capital_invalid"):
        _run(prices, signals, initial_capital=capital)  # type: ignore[arg-type]

    assert capital.float_calls == 0


@pytest.mark.parametrize(
    ("parameter_name", "error_match"),
    [
        ("top_pct", "top_pct must be greater than 0 and no more than 1"),
        ("transaction_cost_bps", "transaction_cost_bps must be non-negative"),
        ("slippage_bps", "slippage_bps must be non-negative"),
    ],
)
def test_timing_010_rejects_stateful_float_control_subclasses(
    parameter_name: str,
    error_match: str,
) -> None:
    class StatefulFloat(float):
        def __new__(cls, value: float):
            instance = super().__new__(cls, value)
            instance.float_calls = 0
            return instance

        def __float__(self) -> float:
            self.float_calls += 1
            return super().__float__()

    dates = pd.bdate_range("2025-01-06", periods=2)
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)
    value = StatefulFloat(0.5)
    kwargs: dict[str, object] = {
        "evaluation_start": dates[0],
        "evaluation_end": dates[-1],
        "rebalance_frequency": "D",
        "top_n": 1,
    }
    if parameter_name == "top_pct":
        kwargs["top_n"] = None
    kwargs[parameter_name] = value

    with pytest.raises(ValueError, match=error_match):
        run_long_only_backtest(prices, signals, **kwargs)

    assert value.float_calls == 0


@pytest.mark.parametrize(
    ("parameter_name", "error_match"),
    [
        ("signal_lag_periods", "signal_lag_invalid"),
        ("top_n", "top_n must be positive"),
        ("periods_per_year", "periods_per_year_invalid"),
    ],
)
def test_timing_010_rejects_stateful_integer_control_subclasses(
    parameter_name: str,
    error_match: str,
) -> None:
    class StatefulInt(int):
        def __new__(cls, value: int):
            instance = super().__new__(cls, value)
            instance.int_calls = 0
            return instance

        def __int__(self) -> int:
            self.int_calls += 1
            return super().__int__()

    dates = pd.bdate_range("2025-01-06", periods=2)
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)
    value = StatefulInt(1 if parameter_name != "periods_per_year" else 252)
    kwargs: dict[str, object] = {
        "evaluation_start": dates[0],
        "evaluation_end": dates[-1],
        "rebalance_frequency": "D",
        "top_n": 1,
    }
    kwargs[parameter_name] = value

    with pytest.raises(ValueError, match=error_match):
        run_long_only_backtest(prices, signals, **kwargs)

    assert value.int_calls == 0


@pytest.mark.parametrize(
    ("gross_return", "gross_multiplier"),
    [
        (-1.0, 0.0),
        (-1.1, -0.1),
        (np.nan, np.nan),
        (np.inf, np.inf),
        (-np.inf, -np.inf),
    ],
)
def test_timing_010_pretrade_gross_validator_has_stable_reason(
    gross_return: float,
    gross_multiplier: float,
) -> None:
    with pytest.raises(
        BacktestValidationError,
        match="portfolio_insolvent_or_non_finite_before_trade",
    ):
        _validate_pretrade_gross(
            gross_return=gross_return,
            gross_multiplier=gross_multiplier,
            date=pd.Timestamp("2025-01-07"),
        )


def test_timing_010_invalid_gross_stops_before_execution_or_costs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=3)
    tiny = np.nextafter(0.0, 1.0)
    prices = pd.DataFrame({"AAA": [tiny, tiny, np.finfo(float).max]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)
    execution_dates: list[pd.Timestamp] = []
    original = portfolio_module._validate_execution_price_legs

    def _record_execution(**kwargs: object) -> None:
        execution_dates.append(kwargs["date"])  # type: ignore[arg-type]
        original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(
        portfolio_module,
        "_validate_execution_price_legs",
        _record_execution,
    )

    with pytest.raises(
        BacktestValidationError,
        match="portfolio_insolvent_or_non_finite_before_trade",
    ):
        _run(prices, signals, transaction_cost_bps=100.0)

    assert execution_dates == [dates[1]]


@pytest.mark.parametrize(
    ("net_return", "net_multiplier", "equity_candidate"),
    [
        (-1.0, 0.0, 0.0),
        (-1.1, -0.1, -0.1),
        (np.nan, np.nan, np.nan),
        (np.inf, np.inf, np.inf),
        (-np.inf, -np.inf, -np.inf),
        (0.0, 1.0, np.inf),
    ],
)
def test_timing_010_postcost_validator_has_stable_reason(
    net_return: float,
    net_multiplier: float,
    equity_candidate: float,
) -> None:
    with pytest.raises(
        BacktestValidationError,
        match="portfolio_insolvent_or_non_finite_after_costs",
    ):
        _validate_postcost_net_equity(
            net_return=net_return,
            net_multiplier=net_multiplier,
            equity_candidate=equity_candidate,
            date=pd.Timestamp("2025-01-07"),
        )


@pytest.mark.parametrize("periods_per_year", [False, True, 251, 252.0, 365])
def test_timing_010_requires_daily_integer_annualizer(
    periods_per_year: object,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=2)
    prices = pd.DataFrame({"AAA": [100.0, 100.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)

    with pytest.raises(BacktestValidationError, match="periods_per_year_invalid"):
        _run(
            prices,
            signals,
            periods_per_year=periods_per_year,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "invalid_benchmark",
    [
        lambda dates: pd.Series([100.0, 101.0], index=dates[:2]),
        lambda dates: pd.Series([100.0, 101.0, 102.0], index=dates[::-1]),
        lambda dates: pd.Series([100.0, np.nan, 102.0], index=dates),
        lambda dates: pd.Series([100.0, True, 102.0], index=dates),
        lambda dates: pd.Series([100.0, 1.0 + 2.0j, 102.0], index=dates),
        lambda dates: pd.Series([100.0, "101", 102.0], index=dates),
        lambda dates: pd.Series([100.0, np.inf, 102.0], index=dates),
        lambda dates: pd.Series([100.0, 0.0, 102.0], index=dates),
    ],
)
def test_timing_011_requires_exact_strict_benchmark(
    invalid_benchmark,
) -> None:
    dates = pd.bdate_range("2025-01-06", periods=3)
    prices = pd.DataFrame({"AAA": [100.0, 101.0, 102.0]}, index=dates)
    signals = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    with pytest.raises(BacktestValidationError, match="benchmark_prices_invalid"):
        _run(prices, signals, benchmark_prices=invalid_benchmark(dates))


def test_timing_012_terminal_observed_bucket_executes_without_future_row() -> None:
    dates = pd.bdate_range("2025-01-20", periods=10)
    prices = pd.DataFrame(
        {"AAA": np.full(10, 100.0), "BBB": np.full(10, 100.0)},
        index=dates,
    )
    signals = pd.DataFrame(
        {
            "AAA": [2.0] * 8 + [1.0, 1.0],
            "BBB": [1.0] * 8 + [2.0, 2.0],
        },
        index=dates,
    )

    result = run_long_only_backtest(
        prices,
        signals,
        evaluation_start=dates[0],
        evaluation_end=dates[-1],
        rebalance_frequency="W-FRI",
        top_n=1,
        transaction_cost_bps=100.0,
    )

    terminal = result.timing_ledger[-1]
    assert terminal.ledger_date == dates[-1]
    assert terminal.is_terminal_scheduled_row is True
    assert terminal.first_holding_return_start == dates[-1]
    assert terminal.first_holding_return_end is None
    assert result.turnover.loc[dates[-1]] == pytest.approx(2.0)
    assert result.transaction_costs.loc[dates[-1]] == pytest.approx(0.02)
    assert result.total_trading_costs.loc[dates[-1]] == pytest.approx(0.02)
    assert result.returns.loc[dates[-1]] == pytest.approx(-0.02)
    assert result.signed_trade_weights.loc[dates[-1], "AAA"] == pytest.approx(
        -1.0
    )
    assert result.signed_trade_weights.loc[dates[-1], "BBB"] == pytest.approx(
        1.0
    )
    assert result.holdings.loc[dates[-1], "BBB"] == 1.0


def test_timing_013_same_row_and_one_row_inputs_cannot_be_executable_pnl() -> None:
    dates = pd.date_range("2025-01-01", periods=18, freq="D")
    prices = pd.DataFrame(
        {"AAA": 100.0 + np.arange(18, dtype=float)},
        index=dates,
    )
    same_row_split = make_train_validation_test_split(
        dates,
        train_start=dates[0],
        train_end=dates[4],
        validation_start=dates[5],
        validation_end=dates[9],
        test_start=dates[10],
        test_end=dates[14],
        label_kind="synthetic_same_row_response",
        label_derivation="factor_scaled_same_row_response_v1",
        label_horizon_rows=0,
        embargo_rows=0,
    )
    assert same_row_split.label_kind == "synthetic_same_row_response"
    assert (
        same_row_split.label_ledger["label_start"]
        == same_row_split.label_ledger["label_end"]
    ).all()

    with pytest.raises(BacktestValidationError, match="signal_lag_invalid"):
        run_long_only_backtest(
            prices,
            prices.copy(),
            evaluation_start=dates[0],
            evaluation_end=dates[4],
            rebalance_frequency="D",
            top_n=1,
            signal_lag_periods=0,
        )

    forward_split = make_train_validation_test_split(
        dates,
        train_start=dates[0],
        train_end=dates[4],
        validation_start=dates[5],
        validation_end=dates[9],
        test_start=dates[10],
        test_end=dates[14],
        label_kind="price_forward_return",
        label_derivation="adjusted_close_forward_return_v1",
        label_horizon_rows=1,
        embargo_rows=0,
    )
    forward_labels = make_price_forward_return_labels(prices, forward_split)
    label_date = forward_split.window_metadata["train"].eligible_dates[0]
    ledger_row = forward_split.label_ledger.loc[
        forward_split.label_ledger["signal_date"].eq(label_date)
    ].iloc[0]
    assert ledger_row["label_start"] == label_date
    assert ledger_row["label_end"] == dates[1]

    with pytest.raises(BacktestValidationError, match="evaluation_bounds_invalid"):
        run_long_only_backtest(
            prices.loc[[label_date]],
            forward_labels.loc[[label_date]],
            evaluation_start=label_date,
            evaluation_end=label_date,
            rebalance_frequency="D",
            top_n=1,
        )


def test_timing_014_metadata_ledger_and_accounting_arrays_reconcile() -> None:
    dates = pd.bdate_range("2025-01-06", periods=5)
    prices = pd.DataFrame({"AAA": np.full(5, 100.0)}, index=dates)
    signals = pd.DataFrame({"AAA": np.ones(5)}, index=dates)

    result = run_long_only_backtest(
        prices,
        signals,
        evaluation_start=dates[0],
        evaluation_end=dates[-1],
        rebalance_frequency="D",
        top_n=1,
        signal_lag_periods=2,
    )

    expected_metadata = {
        "timing_contract": "after_close_signal_next_observed_close_v1",
        "feature_time": "source_row_close_conservative",
        "signal_availability_time": "strictly_after_feature_row_close",
        "decision_time": (
            "immediately_after_signal_availability_on_signal_source_row"
        ),
        "execution_time": "observed_source_row_close_idealized_reset",
        "signal_lag_rows": 2,
        "signal_lag_unit": (
            "observed_source_rows_within_bounded_accounting_slice"
        ),
        "return_frequency": "daily_close_to_close",
        "periods_per_year": 252,
        "return_interval": "previous_close_to_current_close",
        "holding_effective_interval": (
            "execution_close_to_next_observed_close"
        ),
        "cost_application_time": "execution_close_after_row_gross_return",
        "cost_return_basis": "beginning_period_portfolio_value",
        "evaluation_start": dates[0],
        "evaluation_end": dates[-1],
        "metric_anchor_policy": (
            "exclude_initialization_anchor_use_common_measured_rows"
        ),
        "measured_return_start": dates[1],
        "measured_return_end": dates[-1],
        "measured_return_count": 4,
        "rebalance_resolution": "last_observed_row_in_resample_bucket",
        "resolved_rebalance_dates": tuple(dates),
        "backtest_source_provenance_policy": (
            "tracked_pre_mutation_source_snapshot_v1"
        ),
        "backtest_source_provenance_status": "validated_without_recovery",
        "signal_value_failure_policy": (
            "validate_bounded_scores_after_exact_slice_raise_on_invalid_available_score"
        ),
        "target_freeze_policy": (
            "decision_information_only_no_execution_close_rerank"
        ),
        "target_input_scope": "final_masked_signal_matrix_only",
        "incoming_price_failure_policy": (
            "raise_before_asset_return_on_invalid_held_endpoint"
        ),
        "execution_price_failure_policy": (
            "raise_execution_price_invalid_without_redistribution"
        ),
        "gross_insolvency_failure_policy": (
            "raise_before_pretrade_division_or_costs"
        ),
        "insolvency_failure_policy": (
            "raise_before_successful_result_on_invalid_or_insolvent_capital"
        ),
        "equity_curve_failure_policy": (
            "reject_invalid_equity_before_metrics"
        ),
        "returns_failure_policy": (
            "reject_invalid_returns_before_basic_metrics"
        ),
        "terminal_row_policy": (
            "include_return_trade_cost_open_holdings_no_future_return"
        ),
        "benchmark_return_window": (
            "same_measured_rows_cost_free_close_to_close"
        ),
        "initialization_anchor_policy": (
            "zero_return_trade_turnover_cost_and_holdings"
        ),
        "missing_price_policy_classification": "formal_raise",
        "benchmark_missing_policy_classification": "formal_raise",
    }
    assert result.timing_metadata == expected_metadata

    ledger = result.timing_ledger
    assert tuple(row.ledger_date for row in ledger) == tuple(dates)
    assert set(asdict(ledger[0])) == {
        "ledger_date",
        "scheduled_execution_date",
        "is_scheduled_rebalance",
        "event_status",
        "signal_source_date",
        "feature_observation_end",
        "signal_availability_phase",
        "decision_phase",
        "execution_phase",
        "incoming_return_start",
        "incoming_return_end",
        "first_holding_return_start",
        "first_holding_return_end",
        "is_terminal_scheduled_row",
    }

    anchor = ledger[0]
    assert anchor.is_scheduled_rebalance is True
    assert anchor.scheduled_execution_date == dates[0]
    assert anchor.event_status == "initialization_anchor_no_execution"
    assert anchor.signal_source_date is None
    assert anchor.feature_observation_end is None
    assert anchor.signal_availability_phase is None
    assert anchor.decision_phase is None
    assert anchor.execution_phase is None
    assert anchor.incoming_return_start is None
    assert anchor.incoming_return_end is None
    assert anchor.first_holding_return_start is None
    assert anchor.first_holding_return_end is None
    assert anchor.is_terminal_scheduled_row is False
    assert result.holdings.loc[dates[0]].eq(0.0).all()
    assert result.signed_trade_weights.loc[dates[0]].eq(0.0).all()
    assert result.turnover.loc[dates[0]] == 0.0
    assert result.total_trading_costs.loc[dates[0]] == 0.0

    insufficient = ledger[1]
    assert insufficient.event_status == "insufficient_lag_no_execution"
    assert insufficient.signal_source_date is None
    assert insufficient.feature_observation_end is None
    assert insufficient.signal_availability_phase is None
    assert insufficient.decision_phase is None
    assert insufficient.execution_phase is None
    assert insufficient.incoming_return_start == dates[0]
    assert insufficient.incoming_return_end == dates[1]
    assert insufficient.first_holding_return_start is None
    assert insufficient.first_holding_return_end is None
    assert result.holdings.loc[dates[1]].eq(0.0).all()
    assert result.signed_trade_weights.loc[dates[1]].eq(0.0).all()
    assert result.turnover.loc[dates[1]] == 0.0
    assert result.total_trading_costs.loc[dates[1]] == 0.0

    for position, row in enumerate(ledger[2:], start=2):
        assert row.event_status == "executed_invested_target"
        assert row.signal_source_date == dates[position - 2]
        assert row.feature_observation_end == dates[position - 2]
        assert (
            row.signal_availability_phase
            == "strictly_after_feature_row_close"
        )
        assert row.decision_phase == "immediately_after_signal_availability"
        assert row.execution_phase == "observed_source_row_close_idealized_reset"
        assert row.incoming_return_start == dates[position - 1]
        assert row.incoming_return_end == dates[position]
        assert row.first_holding_return_start == dates[position]
        assert row.first_holding_return_end == (
            dates[position + 1] if position + 1 < len(dates) else None
        )
        assert row.is_terminal_scheduled_row is (position == len(dates) - 1)

    accounting_series = [
        result.equity_curve,
        result.returns,
        result.gross_returns,
        result.turnover,
        result.transaction_costs,
        result.slippage_costs,
        result.volume_aware_slippage_costs,
        result.total_trading_costs,
    ]
    accounting_frames = [
        result.holdings,
        result.signed_trade_weights,
        result.trade_weights,
    ]
    assert all(series.index.equals(dates) for series in accounting_series)
    assert all(frame.index.equals(dates) for frame in accounting_frames)
    assert result.metrics["total_turnover"] == pytest.approx(
        float(result.turnover.sum())
    )
    assert result.metrics["total_trading_cost_impact"] == pytest.approx(
        float(result.total_trading_costs.sum())
    )
