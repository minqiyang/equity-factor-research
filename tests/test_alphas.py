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
    alpha_007,
    alpha_008,
    alpha_009,
    alpha_010,
    alpha_012,
    alpha_013,
    alpha_014,
    alpha_017,
    alpha_018,
    alpha_019,
    alpha_020,
    alpha_021,
    alpha_023,
    alpha_024,
    alpha_026,
    alpha_028,
    alpha_030,
    alpha_032,
    alpha_033,
    alpha_034,
    alpha_035,
    alpha_038,
    alpha_039,
    alpha_043,
    alpha_045,
    alpha_049,
    alpha_051,
    alpha_053,
    alpha_054,
    alpha_055,
    alpha_060,
    alpha_101,
)
from features.operators import cs_rank, scale, ts_corr, ts_mean
from features.worldquant_alphas import alpha_009 as worldquant_alpha_009
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


def test_alpha_007_volume_gate_and_constant_abs_delta_rank() -> None:
    n = 67
    close = _panel(
        {
            "AAA": [10.0 + float(i) for i in range(n)],
            "BBB": [100.0 - float(i) for i in range(n)],
        }
    )
    volume = _panel(
        {
            "AAA": [1.0 + float(i) for i in range(n)],
            "BBB": [float(n) - float(i) for i in range(n)],
        }
    )

    alpha = alpha_007(close, volume)

    assert alpha.iloc[:19].isna().all().all()
    # 60-way tie of |delta(close, 7)| = 7; percentile rank = 30.5 / 60
    expected_rank = 30.5 / 60.0
    assert alpha.iloc[-1, 0] == pytest.approx(-expected_rank)
    # BBB current volume is below adv20, so the else branch is -1
    assert alpha.iloc[-1, 1] == pytest.approx(-1.0)
    assert alpha.iloc[19, 1] == pytest.approx(-1.0)
    assert np.isnan(alpha.iloc[19, 0])


def test_alpha_007_supplied_adv20_matches_explicit_mean() -> None:
    n = 67
    close = _panel(
        {
            "AAA": [10.0 + float(i) for i in range(n)],
            "BBB": [100.0 - float(i) for i in range(n)],
        }
    )
    volume = _panel(
        {
            "AAA": [1.0 + float(i) for i in range(n)],
            "BBB": [float(n) - float(i) for i in range(n)],
        }
    )

    assert_frame_equal(alpha_007(close, volume), alpha_007(close, volume, ts_mean(volume, 20)))


def test_alpha_009_trend_continuation_and_reversal_branches() -> None:
    close = _panel(
        {
            "AAA": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
            "BBB": [15.0, 14.0, 13.0, 12.0, 11.0, 10.0],
        }
    )

    alpha = alpha_009(close)

    assert alpha.iloc[:5].isna().all().all()
    # AAA deltas all +1, ts_min(5) > 0 -> keep +1
    # BBB deltas all -1, ts_max(5) < 0 -> keep -1
    # cs_rank(1, -1) = 1.0, 0.5
    assert alpha.iloc[-1, 0] == pytest.approx(1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(0.5)
    assert_frame_equal(alpha, cs_rank(worldquant_alpha_009(close)))


def test_alpha_009_mixed_window_uses_negative_delta() -> None:
    close = _panel(
        {
            "AAA": [10.0, 12.0, 11.0, 13.0, 12.0, 14.0],
            "BBB": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        }
    )

    alpha = alpha_009(close)

    # AAA last five deltas mixed -> -delta = -2; BBB all +1 -> keep +1
    # cs_rank(-2, 1) = 0.5, 1.0
    assert alpha.iloc[-1, 0] == pytest.approx(0.5)
    assert alpha.iloc[-1, 1] == pytest.approx(1.0)


def test_alpha_017_hand_calculated_rank_product() -> None:
    n = 24
    close = _panel(
        {
            "AAA": [float(i + 1) for i in range(n)],
            "BBB": [float(n - i) for i in range(n)],
        }
    )
    volume = _panel({"AAA": [10.0] * n, "BBB": [10.0] * n})

    alpha = alpha_017(close, volume)

    assert alpha.iloc[:23].isna().all().all()
    # ts_rank(close, 10): AAA current max -> 1.0; BBB current min -> 0.1
    # cs_rank of those values -> 1.0, 0.5 then multiply by -1
    # second close delta is 0, 0; cs_rank tie at 0.75
    # volume/adv20 is 1, 1; ts_rank of a 5-way tie is 0.6; cs_rank tie 0.75
    assert alpha.iloc[-1, 0] == pytest.approx(-1.0 * 0.75 * 0.75)
    assert alpha.iloc[-1, 1] == pytest.approx(-0.5 * 0.75 * 0.75)


def test_alpha_019_hand_calculated_signed_move_and_return_sum() -> None:
    n = 251
    close = _panel(
        {
            "AAA": [float(i) for i in range(n)],
            "BBB": [float(n - 1 - i) for i in range(n)],
        }
    )
    returns = _panel({"AAA": [0.01] * n, "BBB": [0.02] * n})

    alpha = alpha_019(close, returns)

    assert alpha.iloc[:249].isna().all().all()
    # (close - delay(close, 7)) + delta(close, 7) = 2 * delta; signs +1, -1
    # ts_sum(returns, 250) = 2.5, 5.0; 1 + rank(1 + sum) = 1.5, 2.0
    assert alpha.iloc[-1, 0] == pytest.approx(-1.5)
    assert alpha.iloc[-1, 1] == pytest.approx(2.0)


def test_alpha_023_mean_gate_keeps_incomplete_windows_missing() -> None:
    high = _panel(
        {
            "AAA": [float(i + 1) for i in range(20)],
            "BBB": [float(20 - i) for i in range(20)],
        }
    )

    alpha = alpha_023(high)

    assert alpha.iloc[:19].isna().all().all()
    # AAA last high 20 > mean 10.5, delta(high, 2) = 2 -> -2
    # BBB last high 1 < mean 10.5 -> 0
    assert alpha.iloc[-1, 0] == pytest.approx(-2.0)
    assert alpha.iloc[-1, 1] == pytest.approx(0.0)


def test_alpha_028_scale_of_correlation_plus_typical_minus_close() -> None:
    adv20 = _panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0, 5.0],
            "BBB": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )
    low = _panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0, 5.0],
            "BBB": [5.0, 4.0, 3.0, 2.0, 1.0],
        }
    )
    high = low.copy()
    close = low.copy()
    volume = _panel({"AAA": [1.0] * 5, "BBB": [1.0] * 5})

    alpha = alpha_028(close, high, low, volume, adv20=adv20)

    assert alpha.iloc[:4].isna().all().all()
    # corr = 1, -1; typical equals close, so inner = corr; scale abs-sum 2 -> 0.5, -0.5
    assert alpha.iloc[-1, 0] == pytest.approx(0.5)
    assert alpha.iloc[-1, 1] == pytest.approx(-0.5)
    inner = ts_corr(adv20, low, 5) + (high + low) / 2.0 - close
    assert_frame_equal(alpha, scale(inner))


def test_alpha_033_hand_calculated_open_close_ratio_rank() -> None:
    open_price = _panel({"AAA": [10.0], "BBB": [20.0]})
    close = _panel({"AAA": [10.0], "BBB": [10.0]})

    alpha = alpha_033(open_price, close)

    # AAA: -1 * (1 - 1) = 0; BBB: -1 * (1 - 2) = 1; cs_rank = 0.5, 1.0
    assert alpha.iloc[-1, 0] == pytest.approx(0.5)
    assert alpha.iloc[-1, 1] == pytest.approx(1.0)


def test_alpha_033_zero_close_is_missing() -> None:
    open_price = _panel({"AAA": [10.0], "BBB": [20.0]})
    close = _panel({"AAA": [0.0], "BBB": [10.0]})

    alpha = alpha_033(open_price, close)

    assert np.isnan(alpha.iloc[-1, 0])
    assert alpha.iloc[-1, 1] == pytest.approx(1.0)


def test_alpha_038_hand_calculated_close_rank_and_open_ratio() -> None:
    n = 10
    close = _panel(
        {
            "AAA": [float(i + 1) for i in range(n)],
            "BBB": [float(n - i) for i in range(n)],
        }
    )
    open_price = close.copy()

    alpha = alpha_038(open_price, close)

    assert alpha.iloc[:9].isna().all().all()
    # ts_rank(close, 10): 1.0, 0.1; cs_rank -> 1.0, 0.5; times -1
    # close/open = 1, 1; cs_rank tie 0.75
    assert alpha.iloc[-1, 0] == pytest.approx(-0.75)
    assert alpha.iloc[-1, 1] == pytest.approx(-0.375)


def test_alpha_054_hand_calculated_powered_ohlc_ratio() -> None:
    open_price = _panel({"AAA": [2.0], "BBB": [1.0]})
    high = _panel({"AAA": [10.0], "BBB": [6.0]})
    low = _panel({"AAA": [4.0], "BBB": [2.0]})
    close = _panel({"AAA": [8.0], "BBB": [4.0]})

    alpha = alpha_054(open_price, high, low, close)

    assert alpha.iloc[-1, 0] == pytest.approx(-1.0 / 1536.0)
    assert alpha.iloc[-1, 1] == pytest.approx(-1.0 / 2048.0)


def test_alpha_054_zero_range_or_close_is_missing() -> None:
    open_price = _panel({"AAA": [2.0], "BBB": [1.0]})
    high = _panel({"AAA": [5.0], "BBB": [6.0]})
    low = _panel({"AAA": [5.0], "BBB": [2.0]})
    close = _panel({"AAA": [5.0], "BBB": [0.0]})

    alpha = alpha_054(open_price, high, low, close)

    assert np.isnan(alpha.iloc[-1, 0])
    assert np.isnan(alpha.iloc[-1, 1])


def test_alpha_101_hand_calculated_intraday_range_ratio() -> None:
    open_price = _panel({"AAA": [10.0], "BBB": [10.0]})
    high = _panel({"AAA": [12.0], "BBB": [10.0]})
    low = _panel({"AAA": [8.0], "BBB": [10.0]})
    close = _panel({"AAA": [11.0], "BBB": [10.0]})

    alpha = alpha_101(open_price, high, low, close)

    assert alpha.iloc[-1, 0] == pytest.approx(1.0 / 4.001)
    assert alpha.iloc[-1, 1] == pytest.approx(0.0)


def test_alpha_021_trend_gates_and_incomplete_adv20_windows() -> None:
    n = 20
    close = _panel(
        {
            "AAA": [float(i + 1) for i in range(n)],
            "BBB": [float(n - i) for i in range(n)],
        }
    )
    volume = _panel({"AAA": [10.0] * n, "BBB": [10.0] * n})

    alpha = alpha_021(close, volume)

    assert alpha.iloc[:19].isna().all().all()
    # AAA last 8 closes 13..20 mean 16.5, pop std sqrt(5.25); mean2=19.5
    # mean8 + std8 < mean2 -> -1
    # BBB last 8 closes 8..1 mean 4.5; mean2=1.5; mean2 < mean8 - std8 -> +1
    assert alpha.iloc[-1, 0] == pytest.approx(-1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(1.0)
    assert_frame_equal(alpha, alpha_021(close, volume, ts_mean(volume, 20)))


def test_alpha_021_volume_ratio_branch_when_range_is_tight() -> None:
    n = 20
    close = _panel({"AAA": [10.0] * n, "BBB": [10.0] * n})
    volume = _panel({"AAA": [10.0] * (n - 1) + [1.0], "BBB": [10.0] * n})

    alpha = alpha_021(close, volume)

    # constant close: cond1 and cond2 are false; AAA volume/adv20 < 1 -> -1
    # BBB volume/adv20 = 1, not < 1 -> +1
    assert alpha.iloc[-1, 0] == pytest.approx(-1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(1.0)


def test_alpha_024_mean_drift_gate_and_incomplete_windows() -> None:
    n = 200
    close = _panel(
        {
            "AAA": [float(i + 1) for i in range(n)],
            "BBB": [10.0] * n,
        }
    )

    alpha = alpha_024(close)

    assert alpha.iloc[:199].isna().all().all()
    # AAA: delta(mean100, 100)/delay(close, 100) = 100/100 = 1.0 > 0.05
    # else branch -delta(close, 3) = -3
    # BBB constant: ratio 0 <= 0.05, close - ts_min = 0 -> 0
    assert alpha.iloc[-1, 0] == pytest.approx(-3.0)
    assert alpha.iloc[-1, 1] == pytest.approx(0.0)


def test_alpha_026_identical_high_volume_ranks_are_minus_one() -> None:
    high = _panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0, 5.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "BBB": [5.0, 4.0, 3.0, 2.0, 1.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0],
        }
    )
    volume = high.copy()

    alpha = alpha_026(high, volume)

    assert alpha.iloc[:10].isna().all().all()
    assert alpha.iloc[-1, 0] == pytest.approx(-1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(-1.0)


def test_alpha_030_sign_sum_rank_and_volume_ratio() -> None:
    n = 20
    close = _panel(
        {
            "AAA": [float(i + 1) for i in range(n)],
            "BBB": [float(n - i) for i in range(n)],
        }
    )
    volume = _panel({"AAA": [1.0] * n, "BBB": [1.0] * n})

    alpha = alpha_030(close, volume)

    assert alpha.iloc[:19].isna().all().all()
    # AAA deltas +1, sign_sum=3; BBB deltas -1, sign_sum=-3
    # cs_rank 1.0, 0.5; (1 - rank) * 5 / 20 = 0.0, 0.125
    assert alpha.iloc[-1, 0] == pytest.approx(0.0)
    assert alpha.iloc[-1, 1] == pytest.approx(0.125)


def test_alpha_032_nested_scale_of_delayed_vwap_correlation() -> None:
    n = 235
    close = _panel(
        {
            "AAA": [float(i + 1) for i in range(n)],
            "BBB": [float(n - i) for i in range(n)],
        }
    )
    vwap = close.shift(5)

    alpha = alpha_032(close, vwap)

    assert alpha.iloc[:234].isna().all().all()
    # corr(vwap, delay(close, 5), 230) = 1; scale -> 0.5, 0.5; 20 * 0.5 = 10
    # mean7 - close = -3, +3; inner 7, 13; scale abs-sum 20 -> 0.35, 0.65
    assert alpha.iloc[-1, 0] == pytest.approx(0.35)
    assert alpha.iloc[-1, 1] == pytest.approx(0.65)


def test_alpha_034_hand_calculated_vol_and_delta_ranks() -> None:
    close = _panel(
        {
            "AAA": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "BBB": [6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
        }
    )
    returns = close.copy()

    alpha = alpha_034(close, returns)

    assert alpha.iloc[:4].isna().all().all()
    # std2/std5 both 0.5/sqrt(2); cs_rank tie 0.75; 1 - rank = 0.25
    # delta close +1, -1; cs_rank 1.0, 0.5; 1 - rank = 0.0, 0.5
    # inner 0.25, 0.75 -> cs_rank 0.5, 1.0
    assert alpha.iloc[-1, 0] == pytest.approx(0.5)
    assert alpha.iloc[-1, 1] == pytest.approx(1.0)


def test_alpha_035_hand_calculated_volume_range_and_return_ranks() -> None:
    n = 32
    close = _panel(
        {
            "AAA": [float(i + 1) for i in range(n)],
            "BBB": [float(n - i) for i in range(n)],
        }
    )
    high = close.copy()
    low = close.copy()
    volume = close.copy()
    returns = _panel({"AAA": [0.01] * n, "BBB": [0.01] * n})

    alpha = alpha_035(high, low, close, volume, returns)

    assert alpha.iloc[:31].isna().all().all()
    # AAA: ts_rank(volume, 32)=1, (close+high-low) current max so 1-1=0
    # BBB: volume rank 1/32, range rank 1/16, 1 - 1/16 = 15/16
    # return 32-way tie rank 16.5/32; 1 - 16.5/32 = 15.5/32
    assert alpha.iloc[-1, 0] == pytest.approx(0.0)
    assert alpha.iloc[-1, 1] == pytest.approx((1.0 / 32.0) * (15.0 / 16.0) * (15.5 / 32.0))


def test_alpha_039_hand_calculated_decayed_volume_and_return_sum() -> None:
    n = 250
    close = _panel(
        {
            "AAA": [float(i + 1) for i in range(n)],
            "BBB": [float(n - i) for i in range(n)],
        }
    )
    volume = _panel({"AAA": [10.0] * n, "BBB": [10.0] * n})
    returns = _panel({"AAA": [0.01] * n, "BBB": [0.02] * n})

    alpha = alpha_039(close, volume, returns)

    assert alpha.iloc[:249].isna().all().all()
    # volume/adv20 = 1; decay_linear of ones is 1; cs_rank tie 0.75
    # delta(close, 7) * 0.25 = 1.75, -1.75; -cs_rank = -1.0, -0.5
    # 1 + cs_rank(sum 250) = 1.5, 2.0
    assert alpha.iloc[-1, 0] == pytest.approx(-1.5)
    assert alpha.iloc[-1, 1] == pytest.approx(-1.0)
    assert_frame_equal(alpha, alpha_039(close, volume, returns, ts_mean(volume, 20)))


def test_alpha_043_hand_calculated_volume_ratio_and_negative_delta_ranks() -> None:
    n = 39
    close = _panel(
        {
            "AAA": [float(i + 1) for i in range(n)],
            "BBB": [float(n - i) for i in range(n)],
        }
    )
    volume = _panel({"AAA": [10.0] * n, "BBB": [10.0] * n})

    alpha = alpha_043(close, volume)

    assert alpha.iloc[:38].isna().all().all()
    # volume/adv20 = 1; 20-way ts_rank tie 10.5/20
    # -delta(close, 7) is a constant 8-way tie 4.5/8
    expected = (10.5 / 20.0) * (4.5 / 8.0)
    assert alpha.iloc[-1, 0] == pytest.approx(expected)
    assert alpha.iloc[-1, 1] == pytest.approx(expected)
    assert_frame_equal(alpha, alpha_043(close, volume, ts_mean(volume, 20)))


def test_alpha_045_hand_calculated_delayed_mean_and_sum_correlation() -> None:
    n = 25
    close = _panel(
        {
            "AAA": [float(i + 1) for i in range(n)],
            "BBB": [float(n - i) for i in range(n)],
        }
    )
    volume = _panel(
        {
            "AAA": [float(i + 1) for i in range(n)],
            "BBB": [float(i + 1) for i in range(n)],
        }
    )

    alpha = alpha_045(close, volume)

    assert alpha.iloc[:24].isna().all().all()
    # delay-mean * corr(close, volume, 2) = 10.5 * 1 and 15.5 * -1
    # cs_rank 1.0, 0.5; sum5 vs sum20 2-window corr = 1, 1; cs_rank tie 0.75
    assert alpha.iloc[-1, 0] == pytest.approx(0.75)
    assert alpha.iloc[-1, 1] == pytest.approx(0.375)


def test_alpha_049_jump_gate_keeps_incomplete_windows_missing() -> None:
    close = _panel(
        {
            "AAA": [float(i) for i in range(11)],
            "BBB": [5.0] * 11,
        }
    )

    alpha = alpha_049(close)

    assert alpha.iloc[:10].isna().all().all()
    # AAA (0 - 10) / 10 = -1 < -0.1 -> 1
    # BBB constant -> -delta = 0
    assert alpha.iloc[-1, 0] == pytest.approx(1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(0.0)
    assert np.isnan(alpha.iloc[1, 0])


def test_alpha_051_jump_gate_keeps_incomplete_windows_missing() -> None:
    close = _panel(
        {
            "AAA": [float(i) for i in range(21)],
            "BBB": [5.0] * 21,
        }
    )

    alpha = alpha_051(close)

    assert alpha.iloc[:20].isna().all().all()
    # AAA (0 - 20) / 20 = -1 < -0.05 -> 1
    # BBB constant -> -delta = 0
    assert alpha.iloc[-1, 0] == pytest.approx(1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(0.0)


def test_alpha_053_hand_calculated_range_delta() -> None:
    high = _panel({"AAA": [10.0] * 10, "BBB": [6.0] * 10})
    low = _panel({"AAA": [4.0] * 10, "BBB": [2.0] * 10})
    close_values_a = [8.0] * 9 + [6.0]
    close = _panel({"AAA": close_values_a, "BBB": [4.0] * 10})

    alpha = alpha_053(high, low, close)

    assert alpha.iloc[:9].isna().all().all()
    # AAA inner 0.5 then -1; delta9 = -1.5; * -1 = 1.5
    # BBB inner 0; delta = 0
    assert alpha.iloc[-1, 0] == pytest.approx(1.5)
    assert alpha.iloc[-1, 1] == pytest.approx(0.0)


def test_alpha_053_zero_close_minus_low_is_missing() -> None:
    high = _panel({"AAA": [10.0] * 10, "BBB": [6.0] * 10})
    low = _panel({"AAA": [8.0] * 10, "BBB": [2.0] * 10})
    close = _panel({"AAA": [8.0] * 10, "BBB": [4.0] * 10})

    alpha = alpha_053(high, low, close)

    assert np.isnan(alpha.iloc[-1, 0])
    assert alpha.iloc[-1, 1] == pytest.approx(0.0)


def test_alpha_055_matching_stoch_and_volume_ranks_are_minus_one() -> None:
    n = 17
    high = _panel({"AAA": [10.0] * n, "BBB": [10.0] * n})
    low = _panel({"AAA": [0.0] * n, "BBB": [0.0] * n})
    close = _panel(
        {
            "AAA": [5.0] * 11 + [0.0, 5.0, 10.0, 0.0, 5.0, 10.0],
            "BBB": [5.0] * 11 + [10.0, 5.0, 0.0, 10.0, 5.0, 0.0],
        }
    )
    volume = close + 1.0

    alpha = alpha_055(high, low, close, volume)

    assert alpha.iloc[:16].isna().all().all()
    assert alpha.iloc[-1, 0] == pytest.approx(-1.0)
    assert alpha.iloc[-1, 1] == pytest.approx(-1.0)


def test_alpha_055_zero_trailing_range_is_missing() -> None:
    n = 17
    flat = _panel({"AAA": [5.0] * n, "BBB": [5.0] * n})
    volume = _panel({"AAA": [1.0] * n, "BBB": [2.0] * n})

    alpha = alpha_055(flat, flat, flat, volume)

    assert alpha.isna().all().all()


def test_alpha_060_hand_calculated_scaled_inner_and_argmax() -> None:
    high = _panel({"AAA": [10.0] * 10, "BBB": [10.0] * 10})
    low = _panel({"AAA": [0.0] * 10, "BBB": [0.0] * 10})
    close = _panel(
        {
            "AAA": [float(i + 1) for i in range(10)],
            "BBB": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 0.0],
        }
    )
    volume = _panel({"AAA": [1.0] * 10, "BBB": [1.0] * 10})

    alpha = alpha_060(high, low, close, volume)

    assert alpha.iloc[:9].isna().all().all()
    # inner 1.0, -1.0; cs_rank 1.0, 0.5; scale 2/3, 1/3; 2*scale = 4/3, 2/3
    # ts_argmax 10, 1; same scale 2/3, 1/3; difference 2/3, 1/3; * -1
    assert alpha.iloc[-1, 0] == pytest.approx(-2.0 / 3.0)
    assert alpha.iloc[-1, 1] == pytest.approx(-1.0 / 3.0)


def test_alpha_060_zero_high_low_range_is_missing() -> None:
    flat = _panel({"AAA": [5.0] * 10, "BBB": [6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0, -1.0, -2.0, -3.0]})
    volume = _panel({"AAA": [1.0] * 10, "BBB": [1.0] * 10})
    high = _panel({"AAA": [5.0] * 10, "BBB": [10.0] * 10})
    low = _panel({"AAA": [5.0] * 10, "BBB": [0.0] * 10})

    alpha = alpha_060(high, low, flat, volume)

    assert np.isnan(alpha.iloc[-1, 0])
    assert np.isfinite(alpha.iloc[-1, 1])


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
        lambda panels: alpha_007(panels["close"], panels["volume"]),
        lambda panels: alpha_008(panels["open"], panels["returns"]),
        lambda panels: alpha_009(panels["close"]),
        lambda panels: alpha_010(panels["close"]),
        lambda panels: alpha_012(panels["close"], panels["volume"]),
        lambda panels: alpha_013(panels["close"], panels["volume"]),
        lambda panels: alpha_014(panels["open"], panels["volume"], panels["returns"]),
        lambda panels: alpha_017(panels["close"], panels["volume"]),
        lambda panels: alpha_018(panels["open"], panels["close"]),
        lambda panels: alpha_019(panels["close"], panels["returns"]),
        lambda panels: alpha_020(panels["open"], panels["high"], panels["low"], panels["close"]),
        lambda panels: alpha_021(panels["close"], panels["volume"]),
        lambda panels: alpha_023(panels["high"]),
        lambda panels: alpha_024(panels["close"]),
        lambda panels: alpha_026(panels["high"], panels["volume"]),
        lambda panels: alpha_028(
            panels["close"],
            panels["high"],
            panels["low"],
            panels["volume"],
        ),
        lambda panels: alpha_030(panels["close"], panels["volume"]),
        lambda panels: alpha_032(panels["close"], panels["vwap"]),
        lambda panels: alpha_033(panels["open"], panels["close"]),
        lambda panels: alpha_034(panels["close"], panels["returns"]),
        lambda panels: alpha_035(
            panels["high"],
            panels["low"],
            panels["close"],
            panels["volume"],
            panels["returns"],
        ),
        lambda panels: alpha_038(panels["open"], panels["close"]),
        lambda panels: alpha_039(panels["close"], panels["volume"], panels["returns"]),
        lambda panels: alpha_043(panels["close"], panels["volume"]),
        lambda panels: alpha_045(panels["close"], panels["volume"]),
        lambda panels: alpha_049(panels["close"]),
        lambda panels: alpha_051(panels["close"]),
        lambda panels: alpha_053(panels["high"], panels["low"], panels["close"]),
        lambda panels: alpha_054(
            panels["open"],
            panels["high"],
            panels["low"],
            panels["close"],
        ),
        lambda panels: alpha_055(
            panels["high"],
            panels["low"],
            panels["close"],
            panels["volume"],
        ),
        lambda panels: alpha_060(
            panels["high"],
            panels["low"],
            panels["close"],
            panels["volume"],
        ),
        lambda panels: alpha_101(
            panels["open"],
            panels["high"],
            panels["low"],
            panels["close"],
        ),
    ],
)
def test_alphas_do_not_use_future_rows(alpha_fn) -> None:
    n = 260
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
        alpha_007(close, volume),
        alpha_008(open_price, returns),
        alpha_009(close),
        alpha_010(close),
        alpha_012(close, volume),
        alpha_013(close, volume),
        alpha_014(open_price, volume, returns),
        alpha_017(close, volume),
        alpha_018(open_price, close),
        alpha_019(close, returns),
        alpha_020(open_price, high, low, close),
        alpha_021(close, volume),
        alpha_023(high),
        alpha_024(close),
        alpha_026(high, volume),
        alpha_028(close, high, low, volume),
        alpha_030(close, volume),
        alpha_032(close, vwap),
        alpha_033(open_price, close),
        alpha_034(close, returns),
        alpha_035(high, low, close, volume, returns),
        alpha_038(open_price, close),
        alpha_039(close, volume, returns),
        alpha_043(close, volume),
        alpha_045(close, volume),
        alpha_049(close),
        alpha_051(close),
        alpha_053(high, low, close),
        alpha_054(open_price, high, low, close),
        alpha_055(high, low, close, volume),
        alpha_060(high, low, close, volume),
        alpha_101(open_price, high, low, close),
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

    constant_close_009 = _panel({"AAA": [3.0] * 6, "BBB": [3.0] * 6})
    constant_alpha_009 = alpha_009(constant_close_009)
    assert constant_alpha_009.iloc[:5].isna().all().all()
    assert constant_alpha_009.iloc[-1, 0] == pytest.approx(0.75)
    assert constant_alpha_009.iloc[-1, 1] == pytest.approx(0.75)
    assert np.isnan(alpha_007(close, zero_volume).iloc[1, 0])
    assert np.isnan(alpha_017(close, zero_volume).iloc[-1, 0])
    assert np.isnan(alpha_023(constant_close).iloc[-1, 0])
    constant_open = constant_close.copy()
    assert alpha_033(constant_open, constant_close).iloc[-1, 0] == pytest.approx(0.75)
    assert alpha_101(constant_open, constant_close, constant_close, constant_close).iloc[
        -1, 0
    ] == pytest.approx(0.0)
    constant_close_021 = _panel({"AAA": [3.0] * 20, "BBB": [3.0] * 20})
    constant_volume_021 = _panel({"AAA": [4.0] * 20, "BBB": [4.0] * 20})
    constant_alpha_021 = alpha_021(constant_close_021, constant_volume_021)
    assert constant_alpha_021.iloc[:19].isna().all().all()
    assert constant_alpha_021.iloc[-1, 0] == pytest.approx(1.0)
    zero_volume_021 = _panel({"AAA": [0.0] * 20, "BBB": [0.0] * 20})
    assert np.isnan(alpha_021(constant_close_021, zero_volume_021).iloc[-1, 0])
    constant_close_049 = _panel({"AAA": [3.0] * 11, "BBB": [3.0] * 11})
    constant_alpha_049 = alpha_049(constant_close_049)
    assert constant_alpha_049.iloc[:10].isna().all().all()
    assert constant_alpha_049.iloc[-1, 0] == pytest.approx(0.0)
    assert np.isnan(alpha_030(close, zero_volume).iloc[-1, 0])
    assert np.isnan(alpha_034(constant_close, _returns_from_close(constant_close)).iloc[-1, 0])
    zero_range = _panel({"AAA": [5.0] * 10, "BBB": [6.0] * 10})
    zero_volume_060 = _panel({"AAA": [1.0] * 10, "BBB": [1.0] * 10})
    assert np.isnan(alpha_053(zero_range, zero_range, zero_range).iloc[-1, 0])
    assert np.isnan(alpha_060(zero_range, zero_range, zero_range, zero_volume_060).iloc[-1, 0])


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
    with pytest.raises(ValueError, match="non-negative"):
        alpha_007(close, _panel({"AAA": [100.0, -1.0, 120.0]}))
    with pytest.raises(ValueError, match="non-negative"):
        alpha_021(close, _panel({"AAA": [100.0, -1.0, 120.0]}))
    with pytest.raises(ValueError, match="non-negative"):
        alpha_026(close, _panel({"AAA": [100.0, -1.0, 120.0]}))
    with pytest.raises(ValueError, match="identical columns"):
        alpha_028(close, close, close, volume)
    with pytest.raises(ValueError, match="identical indexes"):
        alpha_101(close, close, close, shifted)
    with pytest.raises(ValueError, match="identical columns"):
        alpha_045(close, volume)
    with pytest.raises(ValueError, match="identical indexes"):
        alpha_060(close, close, close, shifted)


def test_alphas_module_has_no_abstract_class_hierarchy() -> None:
    tree = ast.parse(ALPHAS_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        assert not isinstance(node, ast.ClassDef)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert "backtest" not in node.module
            assert "portfolio" not in node.module
