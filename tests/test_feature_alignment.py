import pandas as pd


def test_signal_must_precede_forward_return_measurement() -> None:
    dates = pd.date_range("2024-01-31", periods=6, freq="ME")
    prices = pd.Series([100.0, 110.0, 105.0, 115.0, 120.0, 118.0], index=dates)

    trailing_return = prices.pct_change(2)
    next_period_return = prices.pct_change().shift(-1)

    signal_date = dates[3]
    assert trailing_return.loc[signal_date] == prices.loc[dates[3]] / prices.loc[dates[1]] - 1.0
    assert next_period_return.loc[signal_date] == prices.loc[dates[4]] / prices.loc[dates[3]] - 1.0
    assert trailing_return.index.equals(next_period_return.index)


def test_momentum_placeholder_documents_no_lookahead_requirement() -> None:
    import features.momentum as momentum

    docstring = momentum.__doc__ or ""
    assert "known before" in docstring
    assert "execution date" in docstring
