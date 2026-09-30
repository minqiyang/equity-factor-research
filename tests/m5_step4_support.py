"""Synthetic two-segment inputs for the Milestone 5 step 4 tests.

A business-day calendar from 2010 to early December 2016 holds a one-year seal
in 2013. Each ``SegmentRun`` carries only its side's rows, as the step 4 loader
delivers them. Thirty random-walk members and ``SPY.US#E1`` fill the panels;
one pre-side member has a strong low-volatility uptrend and stops trading
mid-segment, so it is a residual held stop. The public inputs are synthetic
monthly series. No test opens a network connection or reads private data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import research.m4_7_sp500_pit_rerun as runner
import research.m5_step4 as step4
from m4_8_segment_support import Segment
from research.m4_7_common_support import scheduled_reset_rows


CAL = pd.bdate_range("2010-01-01", "2016-12-07", name="date")
N = len(CAL)
HOLDOUT_START, HOLDOUT_END = "2013-01-01", "2014-01-01"
SEAL = (HOLDOUT_START, HOLDOUT_END)
ROW_START, ROW_END = int(CAL.searchsorted(pd.Timestamp(HOLDOUT_START))), int(CAL.searchsorted(pd.Timestamp(HOLDOUT_END)))
RESETS = scheduled_reset_rows(CAL)
ASSETS = [f"S{k:03d}.US#E1" for k in range(30)]
STOP_ASSET = ASSETS[0]
WARMUP = 252
PUBLIC_LAST = pd.Period("2016-09", freq="M")


def _next(row: int) -> int:
    return int(RESETS[RESETS > row][0])


def segments() -> tuple[Segment, Segment]:
    pre_first = int(RESETS[RESETS >= WARMUP + 1][0])
    pre_last_ic = int([r for r in RESETS[:-1] if _next(int(r)) < ROW_START][-1])
    post_first = int(RESETS[RESETS >= ROW_END + WARMUP + 1][0])
    pre = Segment("pre", "discovery_pre", pre_first - 1, pre_first, pre_last_ic, _next(pre_last_ic), 0, ROW_START - 1)
    post = Segment("post", "discovery_post", post_first - 1, post_first, int(RESETS[-2]), N - 1, ROW_END, N - 1)
    return pre, post


PRE, POST = segments()
STOP_LAST = PRE.first_reset_row + 200          # the stop asset's last bar; its stop row is STOP_LAST + 1


def vendor_paths(seed: int = 11) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    columns = ASSETS + [runner.BENCHMARK_ID]
    drift = rng.normal(0.0003, 0.0004, len(columns))
    vol = rng.uniform(0.008, 0.03, len(columns))
    drift[0], vol[0] = 0.003, 0.004                   # the stop asset ranks high on momentum and low volatility
    close = pd.DataFrame(30.0 * np.exp(np.cumsum(drift + vol * rng.standard_normal((N, len(columns))), axis=0)),
                         index=CAL, columns=columns)
    close.iloc[STOP_LAST + 1:, 0] = np.nan
    spread = pd.DataFrame(rng.uniform(0.002, 0.02, close.shape), index=CAL, columns=columns)
    volume = pd.DataFrame(rng.uniform(5e5, 5e6, close.shape), index=CAL, columns=columns).where(close.notna())
    return {"open": close * (1.0 + spread / 2), "high": close * (1.0 + spread), "low": close * (1.0 - spread),
            "close": close, "adjusted_close": close.copy(), "volume": volume}


def intervals() -> pd.DataFrame:
    return pd.DataFrame({"symbol": ASSETS, "permanent_id": ASSETS, "start_date": CAL[0], "start_known_at": CAL[0],
                         "end_date": pd.NaT, "end_known_at": pd.NaT})


def master() -> pd.DataFrame:
    return pd.DataFrame({"permanent_id": ASSETS, "has_delisting_candidate_interval": "False",
                         "last_bar": [CAL[STOP_LAST if a == STOP_ASSET else N - 1].date().isoformat() for a in ASSETS]})


def runs(paths: dict[str, pd.DataFrame] | None = None,
         member_intervals: pd.DataFrame | None = None) -> list[runner.SegmentRun]:
    paths = vendor_paths() if paths is None else paths
    member_intervals = intervals() if member_intervals is None else member_intervals
    out = []
    for segment in (PRE, POST):
        rows = slice(segment.feature_floor_row, segment.last_book_row + 1)
        out.append(runner.SegmentRun(segment=segment, full_calendar=CAL,
                                     fields={k: v.iloc[rows].copy() for k, v in paths.items()},
                                     intervals=member_intervals, events=step4.empty_events(), master=master()))
    return out


def registered(segment: Segment) -> dict[str, str]:
    return {"side": segment.side, "anchor_row": CAL[segment.anchor_row].date().isoformat(),
            "first_reset": CAL[segment.first_reset_row].date().isoformat(),
            "last_ic_reset": CAL[segment.last_ic_reset_row].date().isoformat(),
            "last_book_row": CAL[segment.last_book_row].date().isoformat()}


def prepared(paths: dict[str, pd.DataFrame] | None = None,
             member_intervals: pd.DataFrame | None = None) -> dict[str, step4.SegmentInputs]:
    return {run.segment.segment_id: step4.prepare(run, registered(run.segment), SEAL)
            for run in runs(paths, member_intervals)}


THEME_COLUMNS = ["Low Risk", "Momentum", "Quality", "Short-Term Reversal", "Size", "Value"]


def public(seed: int = 3, last: pd.Period = PUBLIC_LAST) -> step4.PublicInputs:
    rng = np.random.default_rng(seed)
    months = pd.period_range("2008-01", last, freq="M")
    rf_months = pd.period_range("2008-01", "2017-06", freq="M")
    multipliers = pd.DataFrame(rng.uniform(0.6, 1.6, (len(months), len(THEME_COLUMNS))), index=months,
                               columns=THEME_COLUMNS)
    class_values = pd.DataFrame(rng.normal(0.003, 0.02, (len(months), 4)), index=months, columns=list(step4.THEMES))
    jkp = pd.DataFrame(rng.normal(0.002, 0.02, (len(months), 6)), index=months,
                       columns=[step4.SLEEVES[s][0] for s in step4.FAMILY_A_IDS])
    nets = {rule: {case: pd.Series(rng.normal(0.002, 0.01, len(months)), index=months) for case in step4.CASES}
            for rule in step4.RULES}
    return step4.PublicInputs(rf=pd.Series(0.001, index=rf_months), multipliers=multipliers,
                              class_values=class_values, jkp=jkp, nets=nets, last_month=last, manifest=[])
