import ast
import inspect

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

import backtest.slippage as slippage
from backtest.slippage import calculate_volume_aware_slippage_diagnostics


def _panel(values: dict[str, list[object]], *, start: str = "2024-01-01") -> pd.DataFrame:
    first_column = next(iter(values.values()))
    dates = pd.date_range(start, periods=len(first_column), freq="D")
    return pd.DataFrame(values, index=dates)


def test_volume_aware_slippage_diagnostics_are_hand_calculated() -> None:
    target_weights = _panel(
        {
            "AAA": [0.0, 0.0, 0.5, 0.25],
            "BBB": [0.0, 0.0, 0.5, 0.75],
        },
    )
    price = _panel(
        {
            "AAA": [10.0, 10.0, 20.0, 20.0],
            "BBB": [20.0, 20.0, 20.0, 20.0],
        },
    )
    volume = _panel(
        {
            "AAA": [1000.0, 1000.0, 1000.0, 1000.0],
            "BBB": [2000.0, 2000.0, 2000.0, 2000.0],
        },
    )

    result = calculate_volume_aware_slippage_diagnostics(
        target_weights,
        price,
        volume,
        window=2,
        portfolio_notional=1000.0,
        base_slippage_bps=10.0,
        participation_slope_bps=100.0,
        max_participation=1.0,
        name="test_slippage",
    )

    expected_trade_weights = _panel(
        {
            "AAA": [0.0, 0.0, 0.5, 0.25],
            "BBB": [0.0, 0.0, 0.5, 0.25],
        },
    )
    expected_lagged_capacity = _panel(
        {
            "AAA": [np.nan, np.nan, 10000.0, 15000.0],
            "BBB": [np.nan, np.nan, 40000.0, 40000.0],
        },
    )
    expected_participation = _panel(
        {
            "AAA": [0.0, 0.0, 0.05, 1.0 / 60.0],
            "BBB": [0.0, 0.0, 0.0125, 0.00625],
        },
    )
    expected_asset_bps = _panel(
        {
            "AAA": [0.0, 0.0, 15.0, 35.0 / 3.0],
            "BBB": [0.0, 0.0, 11.25, 10.625],
        },
    )
    expected_impact = _panel(
        {
            "AAA": [0.0, 0.0, 0.00075, 7.0 / 24000.0],
            "BBB": [0.0, 0.0, 0.0005625, 0.000265625],
        },
    )
    expected_portfolio_impact = pd.Series(
        [0.0, 0.0, 0.0013125, 0.0005572916666666667],
        index=target_weights.index,
        name="portfolio_slippage_impact",
    )

    assert result.name == "test_slippage"
    assert result.start_date == target_weights.index[0]
    assert result.end_date == target_weights.index[-1]
    assert result.asset_count == 2
    assert result.parameters["slippage_model"] == "candidate_linear_participation_slippage"
    assert result.parameters["missing_or_zero_liquidity_policy"] == "raise"
    assert "not_backtest_integration" in result.caveats
    assert "no_profitability_claim" in result.caveats
    assert_frame_equal(result.trade_weights, expected_trade_weights)
    assert_frame_equal(result.lagged_rolling_dollar_volume, expected_lagged_capacity)
    assert_frame_equal(result.participation, expected_participation)
    assert_frame_equal(result.asset_slippage_bps, expected_asset_bps)
    assert_frame_equal(result.asset_slippage_impact, expected_impact)
    assert_series_equal(result.portfolio_slippage_impact, expected_portfolio_impact)
    assert result.summary["trade_count"].tolist() == [0, 0, 2, 2]
    assert result.summary["missing_capacity_count"].tolist() == [0, 0, 0, 0]
    assert result.summary["zero_volume_window_count"].tolist() == [0, 0, 0, 0]


def test_volume_aware_slippage_uses_lagged_capacity_not_same_day_volume() -> None:
    target_weights = _panel({"AAA": [0.0, 0.0, 0.5]})
    price = _panel({"AAA": [10.0, 10.0, 1000.0]})
    volume = _panel({"AAA": [100.0, 100.0, 1_000_000.0]})

    result = calculate_volume_aware_slippage_diagnostics(
        target_weights,
        price,
        volume,
        window=2,
        portfolio_notional=100.0,
        max_participation=1.0,
    )

    assert result.lagged_rolling_dollar_volume.loc[target_weights.index[2], "AAA"] == pytest.approx(1000.0)
    assert result.participation.loc[target_weights.index[2], "AAA"] == pytest.approx(0.05)


def test_volume_aware_slippage_requires_explicit_positive_notional() -> None:
    target_weights = _panel({"AAA": [0.0, 0.0, 0.5]})
    price = _panel({"AAA": [10.0, 10.0, 10.0]})
    volume = _panel({"AAA": [100.0, 100.0, 100.0]})

    with pytest.raises(ValueError, match="portfolio_notional"):
        calculate_volume_aware_slippage_diagnostics(
            target_weights,
            price,
            volume,
            window=2,
            portfolio_notional=0.0,
        )


def test_volume_aware_slippage_raises_when_trade_needs_warmup_capacity() -> None:
    target_weights = _panel({"AAA": [0.0, 0.5, 0.5]})
    price = _panel({"AAA": [10.0, 10.0, 10.0]})
    volume = _panel({"AAA": [100.0, 100.0, 100.0]})

    with pytest.raises(ValueError, match="Missing lagged rolling dollar volume"):
        calculate_volume_aware_slippage_diagnostics(
            target_weights,
            price,
            volume,
            window=2,
            portfolio_notional=100.0,
        )


def test_volume_aware_slippage_rejects_missing_price_or_volume_by_default() -> None:
    target_weights = _panel({"AAA": [0.0, 0.0, 0.5]})
    price = _panel({"AAA": [10.0, np.nan, 10.0]})
    volume = _panel({"AAA": [100.0, 100.0, 100.0]})

    with pytest.raises(ValueError, match="price must not contain missing values"):
        calculate_volume_aware_slippage_diagnostics(
            target_weights,
            price,
            volume,
            window=2,
            portfolio_notional=100.0,
        )

    valid_price = _panel({"AAA": [10.0, 10.0, 10.0]})
    missing_volume = _panel({"AAA": [100.0, np.nan, 100.0]})
    with pytest.raises(ValueError, match="volume must not contain missing values"):
        calculate_volume_aware_slippage_diagnostics(
            target_weights,
            valid_price,
            missing_volume,
            window=2,
            portfolio_notional=100.0,
        )


def test_volume_aware_slippage_rejects_zero_volume_window_by_default() -> None:
    target_weights = _panel({"AAA": [0.0, 0.0, 0.5]})
    price = _panel({"AAA": [10.0, 10.0, 10.0]})
    volume = _panel({"AAA": [100.0, 0.0, 100.0]})

    with pytest.raises(ValueError, match="Zero or incomplete volume window"):
        calculate_volume_aware_slippage_diagnostics(
            target_weights,
            price,
            volume,
            window=2,
            portfolio_notional=100.0,
        )


def test_volume_aware_slippage_rejects_zero_lagged_dollar_volume() -> None:
    target_weights = _panel({"AAA": [0.0, 0.0, 0.5]})
    price = _panel({"AAA": [10.0, 10.0, 10.0]})
    volume = _panel({"AAA": [0.0, 0.0, 100.0]})

    with pytest.raises(ValueError, match="Non-positive lagged rolling dollar volume"):
        calculate_volume_aware_slippage_diagnostics(
            target_weights,
            price,
            volume,
            window=2,
            portfolio_notional=100.0,
        )


def test_volume_aware_slippage_rejects_participation_above_cap() -> None:
    target_weights = _panel({"AAA": [0.0, 0.0, 0.5]})
    price = _panel({"AAA": [10.0, 10.0, 10.0]})
    volume = _panel({"AAA": [100.0, 100.0, 100.0]})

    with pytest.raises(ValueError, match="Participation exceeds max_participation"):
        calculate_volume_aware_slippage_diagnostics(
            target_weights,
            price,
            volume,
            window=2,
            portfolio_notional=1000.0,
            max_participation=0.1,
        )


def test_volume_aware_slippage_rejects_unaligned_panels() -> None:
    target_weights = _panel({"AAA": [0.0, 0.0, 0.5]})
    price = _panel({"AAA": [10.0, 10.0, 10.0]})
    volume = _panel({"BBB": [100.0, 100.0, 100.0]})

    with pytest.raises(ValueError, match="identical columns"):
        calculate_volume_aware_slippage_diagnostics(
            target_weights,
            price,
            volume,
            window=2,
            portfolio_notional=100.0,
        )


def test_volume_aware_slippage_rejects_missing_or_leveraged_targets() -> None:
    target_weights = _panel({"AAA": [0.0, np.nan, 0.5]})
    price = _panel({"AAA": [10.0, 10.0, 10.0]})
    volume = _panel({"AAA": [100.0, 100.0, 100.0]})

    with pytest.raises(ValueError, match="target_weights must not contain missing"):
        calculate_volume_aware_slippage_diagnostics(
            target_weights,
            price,
            volume,
            window=2,
            portfolio_notional=100.0,
        )

    leveraged_targets = _panel({"AAA": [0.0, 0.0, 0.75], "BBB": [0.0, 0.0, 0.75]})
    leveraged_price = _panel({"AAA": [10.0, 10.0, 10.0], "BBB": [10.0, 10.0, 10.0]})
    leveraged_volume = _panel({"AAA": [100.0, 100.0, 100.0], "BBB": [100.0, 100.0, 100.0]})
    with pytest.raises(ValueError, match="row sum exceeds 1.0"):
        calculate_volume_aware_slippage_diagnostics(
            leveraged_targets,
            leveraged_price,
            leveraged_volume,
            window=2,
            portfolio_notional=100.0,
        )


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"window": 0}, "window must be at least 1"),
        ({"volume_lag": 0}, "volume_lag must be at least 1"),
        ({"base_slippage_bps": -1.0}, "base_slippage_bps"),
        ({"participation_slope_bps": -1.0}, "participation_slope_bps"),
        ({"max_participation": 0.0}, "max_participation"),
        ({"name": " "}, "name must not be empty"),
    ],
)
def test_volume_aware_slippage_rejects_invalid_parameters(
    kwargs: dict[str, object],
    match: str,
) -> None:
    target_weights = _panel({"AAA": [0.0, 0.0, 0.5]})
    price = _panel({"AAA": [10.0, 10.0, 10.0]})
    volume = _panel({"AAA": [100.0, 100.0, 100.0]})
    params: dict[str, object] = {
        "window": 2,
        "portfolio_notional": 100.0,
    }
    params.update(kwargs)

    with pytest.raises((TypeError, ValueError), match=match):
        calculate_volume_aware_slippage_diagnostics(
            target_weights,
            price,
            volume,
            **params,  # type: ignore[arg-type]
        )


def test_volume_aware_slippage_module_has_no_data_trading_or_lean_imports() -> None:
    source = inspect.getsource(slippage)
    tree = ast.parse(source)
    forbidden_terms = {
        "broker",
        "requests",
        "urllib",
        "yfinance",
        "alpaca",
        "ccxt",
        "lean",
        "order",
        "credentials",
    }
    imported_modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    for module_name in imported_modules:
        assert not any(term in module_name.lower() for term in forbidden_terms)
