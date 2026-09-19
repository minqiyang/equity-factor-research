import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from features.alphas import (
    alpha_001,
    alpha_002,
    alpha_003,
    alpha_004,
    alpha_005,
    alpha_006,
    alpha_008,
    alpha_010,
    alpha_012,
    alpha_013,
    alpha_014,
    alpha_018,
    alpha_020,
)
from features.worldquant_alphas import alpha_012 as worldquant_alpha_012


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALPHAS_SOURCE = PROJECT_ROOT / "src" / "features" / "alphas.py"


def _panel(values: dict[str, list[float]], *, start: str = "2024-01-01") -> pd.DataFrame:
    first_column = next(iter(values.values()))
    dates = pd.date_range(start, periods=len(first_column), freq="D")
    return pd.DataFrame(values, index=dates)


def _returns_from_close(close: pd.DataFrame) -> pd.DataFrame:
    return close.pct_change(fill_method=None)


def test_alpha_001_all_positive_returns_use_close_and_tie_at_newest_argmax() -> None:
    close = _panel(
        {
            "AAA": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
            "BBB": [20.0, 21.0, 22.0, 23.0, 24.0, 25.0],
        }
    )
    returns = _returns_from_close(close)

    alpha = alpha_001(close, returns)

    assert alpha.iloc[:4].isna().all().all()
    # both assets have strictly increasing positive closes, so ts_argmax=5
    # two-way ties: percentile rank 0.75, then subtract 0.5
    assert alpha.iloc[4, 0] == pytest.approx(0.25)
    assert alpha.iloc[5, 0] == pytest.approx(0.25)
    assert alpha.iloc[5, 1] == pytest.approx(0.25)


def test_alpha_001_negative_return_uses_trailing_stddev_in_signed_power() -> None:
    aaa = [100.0] * 21 + [99.0]
    bbb = [100.0 + float(i) for i in range(22)]
    close = _panel({"AAA": aaa, "BBB": bbb})
    returns = _returns_from_close(close)

    alpha = alpha_001(close, returns)

    # AAA last 20 returns are 19 zeros and -0.01; population std^2 = 0.00000475
    # ts_argmax window is [10000, 10000, 10000, 10000, 0.00000475] -> 1
    # BBB last window of close^2 is strictly increasing -> 5
    # ranks 0.5 and 1.0, then subtract 0.5
    assert alpha.iloc[-1, 0] == pytest.approx(0.0)
    assert alpha.iloc[-1, 1] == pytest.approx(0.5)


def test_alpha_001_does_not_use_future_close_or_returns() -> None:
    close = _panel({"AAA": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0]})
    returns = _returns_from_close(close)
    changed_close = close.copy()
    changed_returns = returns.copy()
    changed_close.iloc[-1, 0] = 10_000.0
    changed_returns.iloc[-1, 0] = 10_000.0

    signal_date = close.index[-2]
    assert_series_equal(
        alpha_001(changed_close, changed_returns).loc[signal_date],
        alpha_001(close, returns).loc[signal_date],
        check_names=False,
    )


def test_alpha_002_perfect_rank_correlation_is_minus_one() -> None:
    open_price = _panel(
        {
            "AAA": [10.0] * 8,
            "BBB": [10.0] * 8,
        }
    )
    close = _panel(
        {
            "AAA": [11.0, 9.0, 11.0, 9.0, 11.0, 9.0, 11.0, 9.0],
            "BBB": [9.0, 11.0, 9.0, 11.0, 9.0, 11.0, 9.0, 11.0],
        }
    )
    volume = _panel(
        {
            "AAA": list(np.exp([0.0, 1.0, 3.0, 0.0, 5.0, 1.0, 7.0, 2.0])),
            "BBB": list(np.exp([1.0, 0.0, 0.0, 3.0, 1.0, 5.0, 2.0, 7.0])),
        }
    )

    alpha = alpha_002(open_price, close, volume)

    assert alpha.iloc[:7].isna().all().all()
    assert alpha.iloc[-1, 0] == pytest.approx(-1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(-1.0)


def test_alpha_002_zero_volume_is_missing_in_log_term() -> None:
    open_price = _panel({"AAA": [10.0] * 8, "BBB": [10.0] * 8})
    close = _panel(
        {
            "AAA": [11.0, 9.0, 11.0, 9.0, 11.0, 9.0, 11.0, 9.0],
            "BBB": [9.0, 11.0, 9.0, 11.0, 9.0, 11.0, 9.0, 11.0],
        }
    )
    volume = _panel(
        {
            "AAA": list(np.exp([0.0, 1.0, 3.0, 0.0, 5.0, 1.0, 7.0, 2.0])),
            "BBB": list(np.exp([1.0, 0.0, 0.0, 3.0, 1.0, 5.0, 2.0, 7.0])),
        }
    )
    volume.iloc[-1, 0] = 0.0

    alpha = alpha_002(open_price, close, volume)

    assert np.isnan(alpha.iloc[-1, 0])


def test_alpha_002_does_not_use_future_open_close_or_volume() -> None:
    open_price = _panel({"AAA": [10.0] * 8, "BBB": [10.0] * 8})
    close = _panel(
        {
            "AAA": [11.0, 9.0, 11.0, 9.0, 11.0, 9.0, 11.0, 9.0],
            "BBB": [9.0, 11.0, 9.0, 11.0, 9.0, 11.0, 9.0, 11.0],
        }
    )
    volume = _panel(
        {
            "AAA": list(np.exp([0.0, 1.0, 3.0, 0.0, 5.0, 1.0, 7.0, 2.0])),
            "BBB": list(np.exp([1.0, 0.0, 0.0, 3.0, 1.0, 5.0, 2.0, 7.0])),
        }
    )
    changed_close = close.copy()
    changed_volume = volume.copy()
    changed_close.iloc[-1] = 10_000.0
    changed_volume.iloc[-1] = 10_000.0

    signal_date = close.index[-2]
    assert_series_equal(
        alpha_002(open_price, changed_close, changed_volume).loc[signal_date],
        alpha_002(open_price, close, volume).loc[signal_date],
        check_names=False,
    )


def test_alpha_003_alternating_ranks_with_matching_volume_is_minus_one() -> None:
    open_price = _panel(
        {
            "AAA": [1.0, 3.0] * 5,
            "BBB": [2.0] * 10,
        }
    )
    volume = _panel(
        {
            "AAA": [1.0, 3.0] * 5,
            "BBB": [2.0] * 10,
        }
    )

    alpha = alpha_003(open_price, volume)

    assert alpha.iloc[:9].isna().all().all()
    assert alpha.iloc[-1, 0] == pytest.approx(-1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(-1.0)


def test_alpha_004_constant_low_is_negative_average_ts_rank() -> None:
    low = _panel({"AAA": [5.0] * 9, "BBB": [5.0] * 9})

    alpha = alpha_004(low)

    assert alpha.iloc[:8].isna().all().all()
    # nine-way tie: average rank 5, pct=5/9, then multiply by -1
    assert alpha.iloc[-1, 0] == pytest.approx(-5.0 / 9.0)
    assert alpha.iloc[-1, 1] == pytest.approx(-5.0 / 9.0)


def test_alpha_004_hand_calculated_crossing_low_ranks() -> None:
    low = _panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
            "BBB": [9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
        }
    )

    alpha = alpha_004(low)

    # current cs_rank AAA=1.0 occupies average ordinal 7.5 of 9
    assert alpha.iloc[-1, 0] == pytest.approx(-7.5 / 9.0)
    # current cs_rank BBB=0.5 occupies average ordinal 2.5 of 9
    assert alpha.iloc[-1, 1] == pytest.approx(-2.5 / 9.0)


def test_alpha_005_hand_calculated_rank_product() -> None:
    open_price = _panel({"AAA": [12.0] * 10, "BBB": [15.0] * 10})
    close = _panel({"AAA": [30.0] * 10, "BBB": [21.0] * 10})
    vwap = _panel({"AAA": [10.0] * 10, "BBB": [20.0] * 10})

    alpha = alpha_005(open_price, close, vwap)

    assert alpha.iloc[:9].isna().all().all()
    # ts_mean(vwap, 10) = 10, 20; open - mean = 2, -5; cs_rank = 1.0, 0.5
    # close - vwap = 20, 1; cs_rank = 1.0, 0.5; -abs(rank) = -1.0, -0.5
    assert alpha.iloc[-1, 0] == pytest.approx(-1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(-0.25)


def test_alpha_006_perfect_and_inverse_correlation() -> None:
    open_price = _panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "BBB": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
        }
    )
    volume = _panel(
        {
            "AAA": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
            "BBB": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        }
    )

    alpha = alpha_006(open_price, volume)

    assert alpha.iloc[:9].isna().all().all()
    assert alpha.iloc[-1, 0] == pytest.approx(-1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(1.0)


def test_alpha_008_hand_calculated_delayed_sum_product() -> None:
    open_price = _panel({"AAA": [1.0] * 14 + [10.0], "BBB": [1.0] * 15})
    returns = _panel({"AAA": [1.0] * 15, "BBB": [1.0] * 15})

    alpha = alpha_008(open_price, returns)

    assert alpha.iloc[:14].isna().all().all()
    # last ts_sum(open, 5) = 14, 5; ts_sum(returns, 5) = 5, 5; product = 70, 25
    # delayed product from index 4 = 25, 25; difference = 45, 0
    # cs_rank = 1.0, 0.5 then multiply by -1
    assert alpha.iloc[-1, 0] == pytest.approx(-1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(-0.5)


def test_alpha_010_trend_continuation_and_reversal_branches() -> None:
    close = _panel(
        {
            "AAA": [10.0, 11.0, 12.0, 13.0, 14.0],
            "BBB": [14.0, 13.0, 12.0, 11.0, 10.0],
        }
    )

    alpha = alpha_010(close)

    assert alpha.iloc[:4].isna().all().all()
    # AAA deltas all +1, ts_min(4) > 0 -> keep +1
    # BBB deltas all -1, ts_max(4) < 0 -> keep -1
    # cs_rank(1, -1) = 1.0, 0.5
    assert alpha.iloc[-1, 0] == pytest.approx(1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(0.5)


def test_alpha_010_mixed_window_uses_negative_delta() -> None:
    close = _panel(
        {
            "AAA": [10.0, 12.0, 11.0, 13.0, 12.0],
            "BBB": [10.0, 11.0, 12.0, 13.0, 14.0],
        }
    )

    alpha = alpha_010(close)

    # AAA last four deltas: +2, -1, +2, -1; min < 0 and max > 0 -> -delta = 1
    # BBB last four deltas all +1 -> keep +1
    # cs_rank of (1, 1) is a two-way tie at 0.75
    assert alpha.iloc[-1, 0] == pytest.approx(0.75)
    assert alpha.iloc[-1, 1] == pytest.approx(0.75)


def test_alpha_012_matches_public_formula_hand_calculation() -> None:
    close = _panel(
        {
            "AAA": [10.0, 11.0, 9.0, 12.0],
            "BBB": [20.0, 19.0, 21.0, 21.5],
        }
    )
    volume = _panel(
        {
            "AAA": [100.0, 120.0, 90.0, 90.0],
            "BBB": [50.0, 40.0, 60.0, 55.0],
        }
    )

    alpha = alpha_012(close, volume)

    assert np.isnan(alpha.loc[close.index[0], "AAA"])
    assert alpha.loc[close.index[1], "AAA"] == pytest.approx(-1.0)
    assert alpha.loc[close.index[2], "AAA"] == pytest.approx(-2.0)
    assert alpha.loc[close.index[3], "AAA"] == pytest.approx(0.0)
    assert alpha.loc[close.index[1], "BBB"] == pytest.approx(-1.0)
    assert alpha.loc[close.index[2], "BBB"] == pytest.approx(-2.0)
    assert alpha.loc[close.index[3], "BBB"] == pytest.approx(0.5)
    assert_frame_equal(alpha, worldquant_alpha_012(close, volume))


def test_alpha_013_identical_ranked_panels_have_equal_negative_tie() -> None:
    close = _panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0, 5.0],
            "BBB": [5.0, 4.0, 3.0, 2.0, 1.0],
        }
    )
    volume = close.copy()

    alpha = alpha_013(close, volume)

    assert alpha.iloc[:4].isna().all().all()
    # both assets have the same 5-day rank covariance, so cs_rank is a tie
    # at 0.75 and the alpha is -0.75
    assert alpha.iloc[-1, 0] == pytest.approx(-0.75)
    assert alpha.iloc[-1, 1] == pytest.approx(-0.75)


def test_alpha_014_perfect_and_inverse_open_volume_correlation() -> None:
    open_price = _panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "BBB": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
        }
    )
    volume = _panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "BBB": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        }
    )
    returns = _panel(
        {
            "AAA": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
            "BBB": [9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0],
        }
    )

    alpha = alpha_014(open_price, volume, returns)

    assert alpha.iloc[:9].isna().all().all()
    # ts_delta(returns, 3) last row = 3, -3; cs_rank = 1.0, 0.5
    # ts_corr(open, volume, 10) = 1.0, -1.0
    # -rank * corr = -1.0, 0.5
    assert alpha.iloc[-1, 0] == pytest.approx(-1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(0.5)


def test_alpha_018_hand_calculated_spread_and_correlation() -> None:
    open_price = _panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "BBB": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
        }
    )
    close = _panel(
        {
            "AAA": [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0],
            "BBB": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
        }
    )

    alpha = alpha_018(open_price, close)

    assert alpha.iloc[:9].isna().all().all()
    # AAA: ts_std(|spread|, 5)=0, spread=1, corr=1 -> inner=2
    # BBB: ts_std(0, 5)=0, spread=0, corr=1 -> inner=1
    # cs_rank = 1.0, 0.5 then multiply by -1
    assert alpha.iloc[-1, 0] == pytest.approx(-1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(-0.5)


def test_alpha_020_hand_calculated_delayed_ohlc_ranks() -> None:
    open_price = _panel({"AAA": [10.0, 13.0], "BBB": [20.0, 18.0]})
    high = _panel({"AAA": [12.0, 14.0], "BBB": [25.0, 19.0]})
    low = _panel({"AAA": [8.0, 12.0], "BBB": [15.0, 17.0]})
    close = _panel({"AAA": [11.0, 13.5], "BBB": [22.0, 18.5]})

    alpha = alpha_020(open_price, high, low, close)

    assert alpha.iloc[0].isna().all()
    # open - delay(high) = 1, -7 -> ranks 1.0, 0.5
    # open - delay(close) = 2, -4 -> ranks 1.0, 0.5
    # open - delay(low) = 5, 3 -> ranks 1.0, 0.5
    # product * -1 = -1.0, -0.125
    assert alpha.iloc[-1, 0] == pytest.approx(-1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(-0.125)


def test_alpha_012_zero_volume_delta_is_explicit_zero() -> None:
    close = _panel({"AAA": [10.0, 11.0, 12.0]})
    volume = _panel({"AAA": [100.0, 0.0, 0.0]})

    alpha = alpha_012(close, volume)

    assert alpha.iloc[1, 0] == pytest.approx(1.0)
    assert alpha.iloc[2, 0] == pytest.approx(0.0)


@pytest.mark.parametrize(
    "alpha_fn",
    [
        lambda panels: alpha_001(panels["close"], panels["returns"]),
        lambda panels: alpha_002(panels["open"], panels["close"], panels["volume"]),
        lambda panels: alpha_003(panels["open"], panels["volume"]),
        lambda panels: alpha_004(panels["low"]),
        lambda panels: alpha_005(panels["open"], panels["close"], panels["vwap"]),
        lambda panels: alpha_006(panels["open"], panels["volume"]),
        lambda panels: alpha_008(panels["open"], panels["returns"]),
        lambda panels: alpha_010(panels["close"]),
        lambda panels: alpha_012(panels["close"], panels["volume"]),
        lambda panels: alpha_013(panels["close"], panels["volume"]),
        lambda panels: alpha_014(panels["open"], panels["volume"], panels["returns"]),
        lambda panels: alpha_018(panels["open"], panels["close"]),
        lambda panels: alpha_020(panels["open"], panels["high"], panels["low"], panels["close"]),
    ],
)
def test_alphas_do_not_use_future_rows(alpha_fn) -> None:
    n = 24
    close = _panel(
        {
            "AAA": list(np.linspace(10.0, 20.0, n)),
            "BBB": list(np.linspace(20.0, 10.0, n)),
        }
    )
    panels = {
        "close": close,
        "returns": _returns_from_close(close),
        "open": close * 0.99,
        "high": close * 1.01,
        "low": close * 0.98,
        "vwap": close * 1.00,
        "volume": _panel({"AAA": list(np.linspace(100.0, 200.0, n)), "BBB": list(np.linspace(200.0, 100.0, n))}),
    }
    changed = {name: panel.copy() for name, panel in panels.items()}
    for panel in changed.values():
        panel.iloc[-1] = 10_000.0

    signal_date = close.index[-2]
    assert_series_equal(
        alpha_fn(changed).loc[signal_date],
        alpha_fn(panels).loc[signal_date],
        check_names=False,
    )


def test_alphas_preserve_shape_index_and_columns() -> None:
    close = _panel({"AAA": [10.0, 11.0, 12.0, 13.0], "BBB": [20.0, 19.0, 18.0, 17.0]})
    volume = _panel({"AAA": [100.0, 110.0, 120.0, 130.0], "BBB": [50.0, 60.0, 70.0, 80.0]})
    open_price = close * 0.99
    high = close * 1.01
    low = close * 0.98
    vwap = close
    returns = _returns_from_close(close)

    results = [
        alpha_001(close, returns),
        alpha_002(open_price, close, volume),
        alpha_003(open_price, volume),
        alpha_004(low),
        alpha_005(open_price, close, vwap),
        alpha_006(open_price, volume),
        alpha_008(open_price, returns),
        alpha_010(close),
        alpha_012(close, volume),
        alpha_013(close, volume),
        alpha_014(open_price, volume, returns),
        alpha_018(open_price, close),
        alpha_020(open_price, high, low, close),
    ]
    for result in results:
        assert result.index.equals(close.index)
        assert result.columns.equals(close.columns)
        assert result.dtypes.tolist() == [np.dtype("float64"), np.dtype("float64")]


def test_alphas_sparse_and_constant_inputs_do_not_fill() -> None:
    close = _panel({"AAA": [10.0, np.nan, 12.0, 13.0], "BBB": [5.0, 5.0, 5.0, 5.0]})
    returns = _returns_from_close(close)
    volume = _panel({"AAA": [1.0, np.nan, 1.0, 1.0], "BBB": [1.0, 1.0, 1.0, 1.0]})

    alpha = alpha_001(close, returns)
    assert np.isnan(alpha.iloc[2, 0])
    assert np.isnan(alpha.iloc[3, 0])
    assert np.isnan(alpha_012(close, volume).iloc[1, 0])
    assert np.isnan(alpha_012(close, volume).iloc[2, 0])

    constant_low = _panel({"AAA": [3.0, 3.0, 3.0], "BBB": [3.0, 3.0, 3.0]})
    constant_alpha = alpha_004(constant_low)
    assert constant_alpha.isna().all().all()

    zero_volume = _panel({"AAA": [0.0, 0.0, 0.0, 0.0], "BBB": [0.0, 0.0, 0.0, 0.0]})
    open_price = close * 0.99
    vwap = _panel({"AAA": [10.0, np.nan, 12.0, 13.0], "BBB": [5.0, 5.0, 5.0, 5.0]})
    assert alpha_002(open_price, close, zero_volume).isna().all().all()
    assert np.isnan(alpha_005(open_price, close, vwap).iloc[1, 0])
    constant_close = _panel({"AAA": [3.0, 3.0, 3.0, 3.0, 3.0], "BBB": [3.0, 3.0, 3.0, 3.0, 3.0]})
    constant_alpha_010 = alpha_010(constant_close)
    assert constant_alpha_010.iloc[:4].isna().all().all()
    assert constant_alpha_010.iloc[-1, 0] == pytest.approx(0.75)
    assert constant_alpha_010.iloc[-1, 1] == pytest.approx(0.75)


def test_alphas_reject_empty_and_mismatched_panels() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    empty = pd.DataFrame(index=dates)
    close = _panel({"AAA": [10.0, 11.0, 12.0]})
    volume = _panel({"BBB": [100.0, 110.0, 120.0]})
    shifted = _panel({"AAA": [100.0, 110.0, 120.0]}, start="2024-01-02")

    with pytest.raises(ValueError, match="empty"):
        alpha_004(empty)
    with pytest.raises(ValueError, match="identical columns"):
        alpha_012(close, volume)
    with pytest.raises(ValueError, match="identical indexes"):
        alpha_012(close, shifted)
    with pytest.raises(ValueError, match="non-negative"):
        alpha_012(close, _panel({"AAA": [100.0, -1.0, 120.0]}))
    with pytest.raises(ValueError, match="non-negative"):
        alpha_003(close, _panel({"AAA": [100.0, -1.0, 120.0]}))


def test_alphas_module_has_no_abstract_class_hierarchy() -> None:
    tree = ast.parse(ALPHAS_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        assert not isinstance(node, ast.ClassDef)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert "backtest" not in node.module
            assert "portfolio" not in node.module
