"""Synthetic tests of trial amendment 4 in the Milestone 5.5 driver: an index exit on a row without a close settles
under R4 on that row (``books.disappearance_r4.exit_gap``).

The world is the small world of ``test_m55_driver`` with five members that leave the index on a row without a close
inside a test segment (anchor 1984-12-31, end row 1989-12-29): on a rebalance row, on a mid-month row, on the end
row, with closes and a new index spell later, and with closes and a delisting later. The loader gives the frames of
both runs, and the engine runs CW-PIT and TILT on random signals, so the books differ. No test reads the WRDS folder.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import research.m55_driver as d
from research import m55_index_tilt as tilt
from research.m4_7_sp500_pit_rerun import RunnerStop
from test_m55_driver import CAL, OPEN, Member, make_data, month_end, row, small_members, world_frames


pytestmark = pytest.mark.xdist_group("m55_exit_gap")

SEGMENT = {"anchor": month_end(CAL, "1984-12"), "end": month_end(CAL, "1989-12")}
START = row(CAL, "1970-03-01")
# The members with an index exit on a row without a close: (permno, exit row W + 1).
EXITS = {"rebalance": (900031, month_end(CAL, "1986-06")), "mid_month": (900032, row(CAL, "1987-03-15")),
         "end_row": (900033, SEGMENT["end"]), "back_and_rejoin": (900034, row(CAL, "1985-05-15")),
         "back_and_delist": (900035, row(CAL, "1985-09-15"))}
BACK = {"back_and_rejoin": row(CAL, "1986-02-01"), "back_and_delist": row(CAL, "1986-04-01")}   # closes come back
REJOIN = row(CAL, "1987-01-02")                  # the new index spell of back_and_rejoin
DELIST = row(CAL, "1988-03-15")                  # the delisting row of back_and_delist (cash merger)
STAYS, STOPS = 900036, 900037                    # a member to the end; a held gap that the rule does not cover
STOPS_FROM = row(CAL, "1988-06-15")              # the first row without a close of STOPS
# The held gaps without an amendment 4 event: STOPS stays in the index, or leaves it two rows after its last close.
UNCOVERED = {"no_index_exit": None, "halt_before_exit": row(CAL, "1988-07-01")}


def before(date: pd.Timestamp) -> pd.Timestamp:
    return CAL[CAL.get_loc(date) - 1]


def set_gap(frames: dict, permno: int, first: pd.Timestamp, last: pd.Timestamp = CAL[-1]) -> None:
    dsf = frames["crsp_dsf_v2"]
    dsf.loc[(dsf["permno"] == permno) & dsf["dlycaldt"].between(first, last), ["dlyprc", "dlyret"]] = np.nan


def set_spell_end(frames: dict, permno: int, end: pd.Timestamp) -> None:
    spells = frames["crsp_dsp500list_v2"]
    spells.loc[spells["permno"] == permno, "mbrenddt"] = end


def add_spell(frames: dict, permno: int, start: pd.Timestamp) -> None:
    frames["crsp_dsp500list_v2"] = pd.concat([frames["crsp_dsp500list_v2"], pd.DataFrame(
        {"permno": [permno], "indno": [1000502], "mbrstartdt": [start], "mbrenddt": [OPEN]})], ignore_index=True)


def exit_world(stops: str | None = None) -> dict[str, pd.DataFrame]:
    """The small world and the members of ``EXITS``; ``stops`` (a key of ``UNCOVERED``) adds STOPS, whose closes stop
    on ``STOPS_FROM`` and do not come back."""
    members = small_members(CAL) + [
        Member(EXITS["rebalance"][0], 0.02, spell=(START, EXITS["rebalance"][1])),
        Member(EXITS["mid_month"][0], 0.04, spell=(START, EXITS["mid_month"][1])),
        Member(EXITS["end_row"][0], 0.06, spell=(START, EXITS["end_row"][1])),
        Member(EXITS["back_and_rejoin"][0], 0.01, spell=(START, EXITS["back_and_rejoin"][1])),
        Member(EXITS["back_and_delist"][0], 0.03, spell=(START, OPEN), last=DELIST, delist=("MER", "UNAV", "CASH"),
               y_return=0.10),
        Member(STAYS, 0.05, spell=(START, OPEN))]
    if stops:
        members.append(Member(STOPS, 0.02, spell=(START, UNCOVERED[stops] or OPEN)))
    frames = world_frames(members, CAL)
    for name, (permno, exit_row) in EXITS.items():
        set_gap(frames, permno, exit_row, before(BACK[name]) if name in BACK else CAL[-1])
    set_spell_end(frames, EXITS["back_and_delist"][0], EXITS["back_and_delist"][1])
    add_spell(frames, EXITS["back_and_rejoin"][0], REJOIN)
    if stops:
        set_gap(frames, STOPS, STOPS_FROM)
    return frames


def random_signals(frames: dict) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(5)
    prices = frames["prices"]
    return {s: pd.DataFrame(rng.standard_normal(prices.shape), index=prices.index, columns=prices.columns)
            for s in tilt.SIGNAL_IDS}


def run_world(world: dict[str, pd.DataFrame], run: str) -> dict:
    """The segment frames of one loader run, the targets, and the engine result of each book at the 1x costs."""
    frames = d.segment_frames(make_data(world), run, SEGMENT)
    inputs = d.inputs_for(frames, random_signals(frames), SEGMENT["anchor"], SEGMENT["end"])
    built = tilt.build_targets(inputs)
    rows = frames["prices"].index
    events = tilt.terminal_events(built["disappearances"], rows, run)
    costs = tilt.dated_cost_frame(rows, tilt.COST_SCHEDULE, 1.0)
    books = {book: tilt.run_book(inputs, target, events, costs) for book, target in built["targets"].items()}
    return {"frames": frames, "built": built, "books": books}


@pytest.fixture(scope="module")
def world() -> dict[str, pd.DataFrame]:
    return exit_world()


@pytest.fixture(scope="module")
def runs(world) -> dict[str, dict]:
    return {run: run_world(world, run) for run in d.RUNS}


@pytest.mark.parametrize("run", d.RUNS)
def test_exit_events_on_a_rebalance_row_and_on_the_end_row_settle_in_both_books(world, runs, run) -> None:
    """Each member of ``EXITS`` gets one event on its exit row, and the D6 event of back_and_delist leaves the table.
    On the rebalance row and on the end row (the last rebalance), the B2 rule leaves the name out of the traded set.
    Both books settle every position on its exit row at the run's own value from the close on W, hold none after
    it, and agree with the R4 counts and the amendment 4 report. H-5 does not refuse at the end row."""
    out = runs[run]
    frames, built, books = out["frames"], out["built"], out["books"]
    names = {str(p): exit_row for p, exit_row in EXITS.values()}
    assert dict(zip(frames["exit_gap_events"]["permanent_id"], frames["exit_gap_events"]["effective_date"])) == names
    assert list(frames["exit_gap_d6_left_out"]["permanent_id"]) == [str(EXITS["back_and_delist"][0])]
    assert not frames["disappearances"]["permanent_id"].duplicated().any()
    table = built["rebalances"]
    for name in ("rebalance", "end_row"):
        permno, exit_row = EXITS[name]
        assert table.at[exit_row, "unknown_event_excluded"] == 1 and table.at[exit_row, "unknown_event_cw_share"] > 0
        for book in tilt.BOOKS:
            target = built["targets"][book].loc[exit_row]
            assert np.isnan(target[str(permno)]) and abs(target.sum() - 1.0) < 1e-12
    value = 0.0 if run == "last_close" else -1.0
    weights = {}
    for book, result in books.items():
        log = {e["permanent_id"]: e for e in result.terminal_event_log}
        for name, exit_row in names.items():
            event = log[name]
            assert (event["effective_date"], event["known_at"], event["reference_date"]) == (
                exit_row.isoformat(), exit_row.isoformat(), before(exit_row).isoformat())
            assert event["terminal_return"] == value and event["incoming_weight"] > 0.0
            assert result.holdings.loc[exit_row:, name].eq(0.0).all()
        summary = tilt.book_summary(result, built["targets"][book])
        held = d.r4_counts(summary, frames["disappearances"], SEGMENT["end"], run)
        unknown = set(frames["disappearances"].query("cause == 'unknown'")["permanent_id"])
        assert held["by_cause"]["unknown"]["held"] == sum(
            log[name]["incoming_weight"] > 0.0 for name in unknown if name in log) >= len(names)
        weights[book] = summary["weights"]
    exits = d.exit_map(make_data(world))
    report = d.exit_gap_report(frames, weights["cw"], exits, SEGMENT["end"])
    assert report == {"events": 5, "events_by_exit_class": {**dict.fromkeys(d.EXIT_CLASSES, 0), "current": 1,
                                                            "left_index": 3, "cash_merger": 1},
                      "held": 5, "held_by_exit_class": report["events_by_exit_class"],
                      "held_cw_weight_sum": report["held_cw_weight_sum"], "priced_again": 2, "held_priced_again": 2,
                      "eligible_again": 1, "d6_left_out": 1}
    assert report["held_cw_weight_sum"] == pytest.approx(sum(
        d.held_weight(weights["cw"], exit_row, name, inclusive=False) for name, exit_row in names.items()))


@pytest.mark.parametrize("run", d.RUNS)
def test_a_settled_column_that_trades_and_rejoins_later_is_never_held_again(world, runs, run) -> None:
    """back_and_rejoin and back_and_delist settle on their exit rows and have closes again later, with a path break
    on the first of them; back_and_rejoin is in the index again from 1987. Neither is bought again: the rebalances
    count the rejoined name as settled_excluded, and the path breaks blank no month, because no book holds the
    names across them."""
    out = runs[run]
    frames, built, books = out["frames"], out["built"], out["books"]
    name = str(EXITS["back_and_rejoin"][0])
    for key in BACK:
        permno = str(EXITS[key][0])
        assert frames["path_break"].at[BACK[key], permno] and np.isfinite(frames["prices"].at[BACK[key], permno])
    table = built["rebalances"]
    again = table.index[[before(r) >= REJOIN for r in table.index]]
    assert len(again) > 30 and (table.loc[again, "settled_excluded"] >= 1).all()
    assert (table.loc[table.index.difference(again), "settled_excluded"] == 0).all()
    for book in tilt.BOOKS:
        assert built["targets"][book].loc[again, name].isna().all()
        for key in BACK:
            assert books[book].holdings.loc[EXITS[key][1]:, str(EXITS[key][0])].eq(0.0).all()
    weights = {book: tilt.book_summary(books[book], built["targets"][book])["weights"] for book in tilt.BOOKS}
    months = pd.period_range("1985-01", "1989-12", freq="M")
    assert d.path_break_positions(frames, weights, d.exit_map(make_data(world)), months, SEGMENT["end"]) == []


def perturb(world: dict[str, pd.DataFrame], case: str) -> dict[str, pd.DataFrame]:
    """A history equal to ``world`` through the row t of ``case`` (``R1_CASES``) and different after it."""
    out = {k: v.copy() for k, v in world.items()}
    dsf = out["crsp_dsf_v2"]
    if case == "event_row":
        # The rebalance member gets closes again after t, a new spell, and a delisting record (a D6 event in the
        # segment); STAYS leaves the index on a row without a close after t.
        permno = EXITS["rebalance"][0]
        mine = (dsf["permno"] == permno) & (dsf["dlycaldt"] > EXITS["rebalance"][1])
        dsf.loc[mine, "dlyprc"] = 30.0
        dsf.loc[mine, "dlyret"] = 0.001
        last = row(CAL, "1988-06-15")
        dsf.drop(dsf.index[mine & (dsf["dlycaldt"] > last)], inplace=True)
        dsf.loc[mine & (dsf["dlycaldt"] == last), ["dlydelflg", "dlyret"]] = ["Y", 0.05]
        out["crsp_stkdelists"] = pd.concat([out["crsp_stkdelists"], pd.DataFrame(
            {"permno": [permno], "delactiontype": ["MER"], "delreasontype": ["UNAV"], "delpaymenttype": ["CASH"]})],
            ignore_index=True)
        add_spell(out, permno, REJOIN)
        set_spell_end(out, STAYS, row(CAL, "1987-09-15"))
        set_gap(out, STAYS, row(CAL, "1987-09-15"))
    elif case == "row_before_event":
        # The rebalance member has a close on its exit row W + 1 and after it: an exit with a close, no event.
        mine = (dsf["permno"] == EXITS["rebalance"][0]) & (dsf["dlycaldt"] >= EXITS["rebalance"][1])
        dsf.loc[mine, ["dlyprc", "dlyret"]] = [30.0, 0.001]
    else:
        # back_and_rejoin stays without a close and out of the index; back_and_delist has no delisting record.
        set_gap(out, EXITS["back_and_rejoin"][0], EXITS["back_and_rejoin"][1])
        spells = out["crsp_dsp500list_v2"]
        out["crsp_dsp500list_v2"] = spells[~((spells["permno"] == EXITS["back_and_rejoin"][0])
                                             & (spells["mbrstartdt"] == REJOIN))].reset_index(drop=True)
        delists = out["crsp_stkdelists"]
        out["crsp_stkdelists"] = delists[delists["permno"] != EXITS["back_and_delist"][0]].reset_index(drop=True)
    return out


R1_CASES = {"event_row": EXITS["rebalance"][1], "row_before_event": before(EXITS["rebalance"][1]),
            "returning_gap": EXITS["back_and_rejoin"][1]}


@pytest.mark.parametrize("run", d.RUNS)
@pytest.mark.parametrize("case", list(R1_CASES))
def test_rows_after_t_change_no_event_trade_holding_or_return_by_t(world, runs, case, run) -> None:
    """R1 inside the segment: two histories equal through row t and different after t, before the end row (closes
    come back or stay missing, eligibility changes, a D6 event appears or goes, a new exit follows), give the same
    events with known_at on or before t, the same targets, and the same trades, holdings, and daily returns of both
    books on every row up to t, in both loader runs. The histories differ after t."""
    t = R1_CASES[case]
    base, other = runs[run], run_world(perturb(world, case), run)
    for key in ("disappearances", "exit_gap_events"):
        known = [table[table["known_at"] <= t].sort_values("permanent_id").reset_index(drop=True)
                 for table in (base["frames"][key], other["frames"][key])]
        pd.testing.assert_frame_equal(*known)
    for book in tilt.BOOKS:
        pd.testing.assert_frame_equal(base["built"]["targets"][book].loc[:t], other["built"]["targets"][book].loc[:t])
        first, second = base["books"][book], other["books"][book]
        pd.testing.assert_series_equal(first.returns.loc[:t], second.returns.loc[:t])
        for field in ("holdings", "trade_weights"):
            pd.testing.assert_frame_equal(getattr(first, field).loc[:t], getattr(second, field).loc[:t])
    pd.testing.assert_frame_equal(base["built"]["rebalances"].loc[:t], other["built"]["rebalances"].loc[:t])
    after = slice(CAL[CAL.get_loc(t) + 1], SEGMENT["end"])
    assert not all(base["frames"][key].loc[after].equals(other["frames"][key].loc[after])
                   for key in ("prices", "eligible"))
    assert not all(base["frames"][key].equals(other["frames"][key])
                   for key in ("exit_gap_events", "exit_gap_d6_left_out"))


@pytest.mark.parametrize("run", d.RUNS)
@pytest.mark.parametrize("stops", list(UNCOVERED))
def test_a_held_gap_that_the_rule_does_not_cover_still_refuses_at_the_end_row(stops, run) -> None:
    """A held member whose closes stop while it stays in the index, or two rows before its index exit, gets no event
    (it is eligible on the first row without a close); the engine holds it halt-locked to the end row and refuses
    (H-5), as before amendment 4."""
    world = exit_world(stops)
    frames = d.segment_frames(make_data(world), run, SEGMENT)
    assert str(STOPS) not in set(frames["disappearances"]["permanent_id"])
    assert len(frames["exit_gap_events"]) == len(EXITS)
    with pytest.raises(RunnerStop) as caught:
        run_world(world, run)
    assert caught.value.reason == "unresolved_disappearance" and SEGMENT["end"].date().isoformat() in str(
        caught.value)
