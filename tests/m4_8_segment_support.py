"""Synthetic two-segment inputs for the M4.8 Stage B runner oracles (plan 7: Stage B tests on synthetic segments).

A weekly calendar puts the 252-row warm-up and more than 60 IC months into two
sides of a one-year seal. Each ``SegmentRun`` holds only its side's rows, as
the per-side loaders of Stage A deliver them. The pre side carries a two-row
mid-month halt and an evidenced cash disappearance; the post side carries a
halt across a reset and a missing bar on a reset row. No test opens a network
connection or reads private data.
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd

import research.m4_7_sp500_pit_rerun as runner
from research.m4_7_common_support import scheduled_reset_rows


CAL = pd.date_range("2000-01-07", "2016-12-30", freq="W-FRI", name="date")
N = len(CAL)
HOLDOUT_START, HOLDOUT_END = "2008-01-01", "2009-01-01"
ROW_START, ROW_END = int(CAL.searchsorted(pd.Timestamp(HOLDOUT_START))), int(CAL.searchsorted(pd.Timestamp(HOLDOUT_END)))
RESETS = scheduled_reset_rows(CAL)
ASSETS = [f"N{k:03d}.US#E1" for k in range(110)]
WARMUP = 252


@dataclass(frozen=True)
class Segment:
    """A synthetic ``discovery_segments`` record: the Stage A interface fixed in plan section 7."""

    segment_id: str
    side: str
    anchor_row: int
    first_reset_row: int
    last_ic_reset_row: int
    last_book_row: int
    feature_floor_row: int
    feature_ceiling_row: int


def _next(row: int) -> int:
    return int(RESETS[RESETS > row][0])


def segments() -> tuple[Segment, Segment]:
    pre_first = int(RESETS[RESETS >= WARMUP + 1][0])
    pre_last_ic = int([r for r in RESETS[:-1] if _next(int(r)) < ROW_START][-1])  # r_pre_last: h(r) < holdout_start
    post_first = int(RESETS[RESETS >= ROW_END + WARMUP + 1][0])
    pre = Segment("pre", "discovery_pre", pre_first - 1, pre_first, pre_last_ic, _next(pre_last_ic), 0, ROW_START - 1)
    post = Segment("post", "discovery_post", post_first - 1, post_first, int(RESETS[-2]), N - 1, ROW_END, N - 1)
    return pre, post


PRE, POST = segments()
HALT_PRE = (PRE.first_reset_row + 40, PRE.first_reset_row + 42)          # mid-month, two rows
CASH_LAST = PRE.first_reset_row + 60                                     # evidenced cash disappearance
POST_RESET = int(RESETS[RESETS > POST.first_reset_row + 30][0])
HALT_POST = (POST_RESET - 1, POST_RESET + 2)                             # a halt across a reset
POST_GAP = int(RESETS[RESETS > POST.first_reset_row + 60][0])            # a missing bar on a reset row


def vendor_paths(seed: int = 5) -> dict[str, pd.DataFrame]:
    """One full-calendar path per asset plus ``SPY.US#E1``; sides are sliced from it."""
    rng = np.random.default_rng(seed)
    columns = ASSETS + [runner.BENCHMARK_ID]
    close = pd.DataFrame(40.0 * np.exp(np.cumsum(rng.normal(0.001, 0.03, (N, len(columns))), axis=0)),
                         index=CAL, columns=columns)
    close.iloc[HALT_PRE[0]:HALT_PRE[1], 0] = np.nan
    close.iloc[CASH_LAST + 1:, 1] = np.nan
    close.iloc[HALT_POST[0]:HALT_POST[1], 2] = np.nan
    close.iloc[POST_GAP, 3] = np.nan
    spread = pd.DataFrame(rng.uniform(0.002, 0.02, close.shape), index=CAL, columns=columns)
    volume = pd.DataFrame(rng.uniform(5e5, 5e6, close.shape), index=CAL, columns=columns).where(close.notna())
    return {"open": close * (1.0 + spread / 2), "high": close * (1.0 + spread), "low": close * (1.0 - spread),
            "close": close, "adjusted_close": close.copy(), "volume": volume}


def intervals() -> pd.DataFrame:
    return pd.DataFrame({"symbol": ASSETS, "permanent_id": ASSETS, "start_date": CAL[0], "start_known_at": CAL[0],
                         "end_date": pd.NaT, "end_known_at": pd.NaT})


def master() -> pd.DataFrame:
    return pd.DataFrame({"permanent_id": ASSETS,
                         "has_delisting_candidate_interval": ["True" if a == ASSETS[1] else "False" for a in ASSETS],
                         "last_bar": [CAL[CASH_LAST].date().isoformat() if a == ASSETS[1] else CAL[-1].date().isoformat()
                                      for a in ASSETS]})


def pre_events() -> pd.DataFrame:
    return pd.DataFrame([{"event_id": f"TE-{ASSETS[1]}-{CAL[CASH_LAST + 1].date()}", "permanent_id": ASSETS[1],
                          "effective_date": CAL[CASH_LAST + 1], "known_at": CAL[CASH_LAST - 8],
                          "reference_date": CAL[CASH_LAST], "terminal_return": 0.15,
                          "return_basis": "prior_observed_close_to_cash"}])


EMPTY_EVENTS = pre_events().iloc[0:0]


def runs(paths: dict[str, pd.DataFrame] | None = None) -> list[runner.SegmentRun]:
    paths = vendor_paths() if paths is None else paths
    out = []
    for segment, events in ((PRE, pre_events()), (POST, EMPTY_EVENTS)):
        rows = slice(segment.feature_floor_row, segment.last_book_row + 1)
        out.append(runner.SegmentRun(segment=segment, full_calendar=CAL,
                                     fields={k: v.iloc[rows].copy() for k, v in paths.items()},
                                     intervals=intervals(), events=events, master=master()))
    return out


def horizon() -> int:
    spans = []
    for segment in (PRE, POST):
        inside = RESETS[(RESETS >= segment.first_reset_row) & (RESETS <= segment.last_book_row)]
        spans.append(int(np.diff(inside).max()))
    return max(spans)


def registration() -> dict:
    doc = copy.deepcopy(runner.REGISTERED_V3)
    doc["holdout"].update(holdout_start=HOLDOUT_START, holdout_end_exclusive=HOLDOUT_END)
    doc["discovery"]["segments"] = [
        {"segment_id": s.segment_id, "side": s.side, "anchor_row": CAL[s.anchor_row].date().isoformat(),
         "first_reset": CAL[s.first_reset_row].date().isoformat(),
         "last_ic_reset": CAL[s.last_ic_reset_row].date().isoformat(),
         "last_book_row": CAL[s.last_book_row].date().isoformat(),
         "ic_months": int(((RESETS >= s.first_reset_row) & (RESETS <= s.last_ic_reset_row)).sum()),
         "prior_exposure_overlap_fraction": {}}
        for s in (PRE, POST)]
    doc["discovery"]["max_reset_to_reset_rows"] = horizon()
    doc["statistics"]["power_projection"].update(kill_reachable_projection=False,
                                                 owner_decision_o48_3="proceed_as_registered")
    doc["statistics"]["cpcv"]["holding_periods"] = horizon()
    doc["snapshot"] = {"snapshot_id": "synthetic_real_v2", "retrieval_complete": True,
                       **{key: hashlib.sha256(key.encode()).hexdigest() for key in runner.SNAPSHOT_DIGESTS_V3}}
    doc["costs"] = copy.deepcopy(runner.REGISTERED["costs"])
    doc["objective"] = copy.deepcopy(runner.REGISTERED["objective"])
    return doc
