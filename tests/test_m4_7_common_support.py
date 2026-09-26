"""M4.7 stage a-0 common-support, label, and IC-month oracles (T-SUP-1, 2, 8, 11; T-REG-4b)."""

import numpy as np
import pandas as pd
import pytest

from backtest.long_short import run_long_short_backtest
from backtest.portfolio import (
    BacktestValidationError,
    _get_rebalance_dates,
    capture_backtest_source_provenance,
    resolve_pit_universe_mask,
    run_long_only_backtest,
)
from features.combination import walk_forward_ic_weighted_composite, walk_forward_icir_weighted_composite
from research.m4_7_common_support import (
    GapWindow,
    base_exclusion_cells,
    common_support_schedule,
    gap_windows,
    holding_cells,
    ic_month_set,
    max_reset_to_reset_rows,
    monthly_rank_ic,
    peel_terminal_resets,
    reset_to_reset_labels,
    scheduled_reset_rows,
    signal_eligibility,
    support_segments,
)


CASH = "prior_observed_close_to_cash"
STOCK = "prior_observed_close_to_stock_consideration_valued_at_completion_date_close"
Y2024 = pd.bdate_range("2024-01-01", "2024-12-31", name="date")


def intervals(dates, starts, ends=None):
    assets = list(starts)
    ends = ends or {}
    return pd.DataFrame({
        "symbol": assets, "permanent_id": assets,
        "start_date": [dates[starts[a]] for a in assets],
        "start_known_at": [dates[starts[a]] for a in assets],
        "end_date": [dates[ends[a]] if a in ends else pd.NaT for a in assets],
        "end_known_at": [dates[ends[a]] if a in ends else pd.NaT for a in assets],
    })


def events(dates, rows):
    return pd.DataFrame([
        {"event_id": f"e-{asset}", "permanent_id": asset, "effective_date": dates[settle],
         "known_at": dates[known], "reference_date": dates[settle - 1],
         "terminal_return": value, "return_basis": basis}
        for asset, settle, known, value, basis in rows
    ])


def windows_as_tuples(windows):
    return [(w.start, w.end, frozenset(w.reasons)) for w in windows]


def test_reset_rows_match_engine_month_end_schedule():
    for calendar in (Y2024, pd.bdate_range("2022-01-03", "2026-08-31")):
        rows = scheduled_reset_rows(calendar)
        assert calendar[rows].equals(_get_rebalance_dates(calendar, "ME"))
    assert scheduled_reset_rows(Y2024[:1]).tolist() == [0]


def test_t_sup_1_gap_windows_bounds_and_merging():
    R = scheduled_reset_rows(Y2024)
    d0, d_last = int(R[0]), int(R[-1])
    g = pd.DataFrame(False, index=Y2024, columns=["A", "B", "C", "D"])
    g.iloc[R[3] + 5:R[3] + 8, 0] = True        # run [m, m'] inside a month
    g.iloc[R[2], 1] = True                      # run starting on a reset row
    g.iloc[R[7] - 3:R[7] - 1, 2] = True         # ends the day before a reset ...
    g.iloc[R[7], 0] = True                      # ... and the reset opens an adjacent window
    g.iloc[R[3] + 9, 3] = True                  # overlaps A's window
    g.iloc[d_last, 3] = True                    # no following reset
    windows = gap_windows(g, {"U1": int(R[5]) + 2, "U_OUT": d_last + 1}, R, d0, d_last)
    assert windows_as_tuples(windows) == [
        (R[2], R[3] - 1, frozenset({"missing_bar"})),
        (R[3] + 5, R[4] - 1, frozenset({"missing_bar"})),
        (R[5] + 2, R[6] - 1, frozenset({"unresolved_delisting"})),
        (R[7] - 3, R[8] - 1, frozenset({"missing_bar"})),
        (d_last, d_last, frozenset({"missing_bar"})),
    ]


def test_t_sup_1_windows_outside_the_discovery_span_are_clipped():
    R = scheduled_reset_rows(Y2024)
    g = pd.DataFrame(False, index=Y2024, columns=["A"])
    g.iloc[R[1] - 4, 0] = True
    g.iloc[R[2] - 2, 0] = True
    windows = gap_windows(g, {}, R, int(R[2]), int(R[-1]))
    assert windows_as_tuples(windows) == []
    windows = gap_windows(g, {}, R, int(R[1]), int(R[-1]))
    assert windows_as_tuples(windows) == [(R[2] - 2, R[2] - 1, frozenset({"missing_bar"}))]
    assert gap_windows(g.iloc[:, :0], {}, R, int(R[0]), int(R[-1])) == []


def two_gap_fixture():
    """Members from row 0 with missing bars that yield a dropped 30-row segment and a gap month."""
    R = scheduled_reset_rows(Y2024)
    bars = pd.DataFrame(True, index=Y2024, columns=["A", "B", "C"])
    bars.iloc[R[3] + 2, 0] = False
    bars.iloc[R[4] + 30, 1] = False
    bars.iloc[R[9], 2] = False
    mask = resolve_pit_universe_mask(intervals(Y2024, {"A": 0, "B": 0, "C": 0}), None, Y2024, ["A", "B", "C"])
    return R, bars, mask, common_support_schedule(Y2024, bars, mask, {}, int(R[0]))


def test_t_sup_2_segments_complement_windows_and_short_segments_drop():
    R, _, _, schedule = two_gap_fixture()
    assert windows_as_tuples(schedule.windows) == [
        (R[3] + 2, R[4] - 1, frozenset({"missing_bar"})),
        (R[4] + 30, R[6] - 1, frozenset({"missing_bar"})),
        (R[9], R[10] - 1, frozenset({"missing_bar"})),
    ]
    segments = [(s.first, s.last, s.valid) for s in schedule.segments]
    assert segments == [
        (R[0], R[3] + 1, True), (R[4], R[4] + 29, False), (R[6], R[9] - 1, True), (R[10], R[11], False),
    ]
    assert schedule.segments[1].rows == 30
    covered = sorted(
        row for part in [*schedule.windows, *schedule.segments]
        for row in range(part.start if isinstance(part, GapWindow) else part.first,
                         (part.end if isinstance(part, GapWindow) else part.last) + 1)
    )
    assert covered == list(range(schedule.d0, schedule.d_last + 1))
    assert all(s.first in set(R.tolist()) and s.anchor == s.first - 1 for s in schedule.segments)
    span = schedule.d_last - schedule.d0 + 1
    assert schedule.excluded_rows == span - 66 - 66
    assert schedule.excluded_fraction == schedule.excluded_rows / span
    assert schedule.max_reset_to_reset_rows == int(np.diff(R).max()) == 23
    assert schedule.g_term == ()


def test_t_sup_8_ic_month_set_and_typed_exclusions():
    R, _, _, schedule = two_gap_fixture()
    t_ic, excluded = ic_month_set(schedule)
    assert t_ic == tuple(int(R[k]) for k in (0, 1, 2, 6, 7))
    assert excluded == {
        "ic_month_in_gap": (int(R[9]),),
        "ic_month_in_dropped_segment": tuple(int(R[k]) for k in (4, 5, 10, 11)),
        "ic_month_horizon_unmeasured": (int(R[3]), int(R[8])),
    }
    assert len(t_ic) + sum(map(len, excluded.values())) == len(R)


def test_t_sup_8_review_probe_rank_ic_is_minus_one_half():
    dates = pd.bdate_range("2024-01-01", periods=24, name="date")
    prices = pd.DataFrame(100.0, index=dates, columns=["A", "B", "C"])
    prices.iloc[10:, 0] = np.nan
    prices.iloc[22:, 1] = 110.0
    prices.iloc[22:, 2] = 120.0
    s_mask = pd.DataFrame(False, index=dates, columns=prices.columns)
    s_mask.iloc[0] = True
    signal = pd.DataFrame(np.nan, index=dates, columns=prices.columns)
    signal.iloc[0] = [3.0, 1.0, 2.0]
    resets = np.array([1, 22])
    worthless = events(dates, [("A", 10, 5, -1.0, CASH)])
    labels, records = reset_to_reset_labels(prices, s_mask, resets, (1,), worthless)
    assert labels.iloc[0].tolist() == pytest.approx([-1.0, 0.1, 0.2], abs=1e-15)
    assert labels.drop(index=dates[0]).isna().all().all()
    assert records.loc[dates[1]].to_dict() == {
        "signal_date": dates[0], "eligible_count": 3, "terminal_aware_labels": 1,
        "missing_execution_bar": 0, "missing_horizon_end_bar": 0,
    }
    ic = monthly_rank_ic(signal, labels, (1,), min_pairs=3)
    assert ic["rank_ic"].iloc[0] == pytest.approx(-0.5, abs=1e-15)
    assert ic["status"].iloc[0] == "valid"
    assert ic.index[0] == dates[0] and ic["reset_date"].iloc[0] == dates[1]

    price_only, records = reset_to_reset_labels(prices, s_mask, resets, (1,), None)
    assert np.isnan(price_only.iloc[0, 0])
    assert records.loc[dates[1], "missing_horizon_end_bar"] == 1
    assert monthly_rank_ic(signal, price_only, (1,), min_pairs=2)["rank_ic"].iloc[0] == pytest.approx(1.0)


def test_t_sup_8_terminal_aware_label_cases():
    dates = pd.bdate_range("2024-01-01", periods=60, name="date")
    assets = ["MEMBER", "CASHX", "STOCKX", "EXEC", "END"]
    growth = np.array([1.001, 1.002, 1.003, 1.004, 0.999])
    prices = pd.DataFrame(100.0 * growth ** np.arange(60)[:, None], index=dates, columns=assets)
    engine_events = events(dates, [("CASHX", 30, 25, 0.25, CASH), ("STOCKX", 43, 30, 1 / 9, STOCK),
                                   ("EXEC", 22, 15, 0.0, CASH)])
    prices.iloc[30:, 1] = np.nan
    prices.iloc[43:, 2] = np.nan
    prices.iloc[22:, 3] = np.nan
    table = intervals(dates, {a: 0 for a in assets}, ends={"END": 35})
    mask = resolve_pit_universe_mask(table, engine_events, dates, assets)
    s_mask = signal_eligibility(mask, prices.notna())
    resets = scheduled_reset_rows(dates)
    assert resets.tolist()[:2] == [22, 43]
    labels, records = reset_to_reset_labels(prices, s_mask, resets, (22,), engine_events)
    p = prices.to_numpy()
    expected = {
        "MEMBER": p[43, 0] / p[22, 0] - 1,
        "CASHX": p[29, 1] / p[22, 1] * 1.25 - 1,
        "STOCKX": p[42, 2] / p[22, 2] * (1 + 1 / 9) - 1,
        "END": p[43, 4] / p[22, 4] - 1,
    }
    row = labels.iloc[21]
    for asset, value in expected.items():
        assert row[asset] == pytest.approx(value, abs=1e-15), asset
    assert np.isnan(row["EXEC"]) and not s_mask.iloc[21]["EXEC"]
    assert not mask.iloc[43]["END"]
    assert records.iloc[0][["eligible_count", "terminal_aware_labels"]].tolist() == [4, 2]


def test_t_sup_8_guard_reasons_are_counted():
    dates = pd.bdate_range("2024-01-01", periods=60, name="date")
    prices = pd.DataFrame(100.0, index=dates, columns=["X", "Y", "Z"])
    prices.iloc[22, 0] = np.nan
    prices.iloc[43, 1] = np.nan
    s_mask = pd.DataFrame(True, index=dates, columns=prices.columns)
    labels, records = reset_to_reset_labels(prices, s_mask, scheduled_reset_rows(dates), (22,), None)
    assert records.iloc[0][["missing_execution_bar", "missing_horizon_end_bar"]].tolist() == [1, 1]
    assert labels.iloc[21].isna().tolist() == [True, True, False]
    with pytest.raises(ValueError, match="following scheduled reset"):
        reset_to_reset_labels(prices, s_mask, scheduled_reset_rows(dates), (59,), None)


@pytest.mark.parametrize(("count", "status"), [(99, "ic_month_invalid:insufficient_pairs"), (100, "valid")])
def test_t_sup_8_month_needs_one_hundred_finite_pairs(count, status):
    dates = pd.bdate_range("2024-01-01", periods=30, name="date")
    rng = np.random.default_rng(count)
    signal = pd.DataFrame(np.nan, index=dates, columns=[f"S{i:03d}" for i in range(120)])
    labels = signal.copy()
    signal.iloc[21, :count] = rng.normal(size=count)
    labels.iloc[21, :count] = rng.normal(size=count)
    labels.iloc[21, count:count + 10] = 0.5
    result = monthly_rank_ic(signal, labels, (22,))
    assert result["finite_pair_count"].tolist() == [count]
    assert result["status"].tolist() == [status]
    assert np.isnan(result["rank_ic"].iloc[0]) == (status != "valid")


def test_monthly_rank_ic_types_an_undefined_correlation():
    dates = pd.bdate_range("2024-01-01", periods=30, name="date")
    signal = pd.DataFrame(1.0, index=dates, columns=[f"S{i}" for i in range(5)])
    labels = pd.DataFrame(np.arange(5.0)[None, :].repeat(30, axis=0), index=dates, columns=signal.columns)
    assert monthly_rank_ic(signal, labels, (22,), min_pairs=5)["status"].tolist() == [
        "ic_month_invalid:undefined_rank_ic"]


ROUND2 = pd.bdate_range("2022-01-03", "2026-08-31", name="date")


def round2(join_missing=("2024-05-15",), join2=False):
    assets = ["OLD", "JOIN", "OTHER"] + (["JOIN2"] if join2 else [])
    starts = {"OLD": 0, "JOIN": ROUND2.get_loc(pd.Timestamp("2024-05-10")), "OTHER": 0}
    if join2:
        starts["JOIN2"] = ROUND2.get_loc(pd.Timestamp("2024-05-09"))
    prices = pd.DataFrame(100.0, index=ROUND2, columns=assets)
    prices.loc[pd.Timestamp("2024-05-16"), "OLD"] = np.nan
    for day in join_missing:
        prices.loc[pd.Timestamp(day), "JOIN"] = np.nan
    if join2:
        prices.loc[pd.Timestamp("2024-05-14"), "JOIN2"] = np.nan
    table = intervals(ROUND2, starts)
    mask = resolve_pit_universe_mask(table, None, ROUND2, assets)
    reset_rows = scheduled_reset_rows(ROUND2)
    d0 = int(next(r for r in reset_rows if r >= 253))
    schedule = common_support_schedule(ROUND2, prices.notna(), mask, {}, d0)
    return prices, table, mask, schedule


def row(day):
    return ROUND2.get_loc(pd.Timestamp(day))


def test_t_sup_11_a_single_peel_on_the_round_two_counterexample():
    prices, _, mask, schedule = round2()
    base = gap_windows(schedule.g_base, {}, schedule.reset_rows, schedule.d0, schedule.d_last)
    assert windows_as_tuples(base) == [(row("2024-05-16"), row("2024-05-30"), frozenset({"missing_bar"}))]
    assert not schedule.g_base.loc[pd.Timestamp("2024-05-15"), "JOIN"]
    assert schedule.g_term == (("JOIN", row("2024-05-15")),)
    assert windows_as_tuples(schedule.windows) == [
        (row("2024-05-15"), row("2024-05-30"), frozenset({"missing_bar", "terminal_reset_missing_bar"}))]
    assert schedule.windows[0].peeled_rows == 1
    first, second = schedule.segments
    assert (first.first, first.last, first.valid) == (schedule.d0, row("2024-05-14"), True)
    assert first.rows == 358
    assert (second.first, second.last) == (row("2024-05-31"), schedule.d_last)
    assert schedule.excluded_rows == 12
    peeled_again, cells = peel_terminal_resets(list(schedule.windows), mask, prices.notna(), schedule.d0)
    assert windows_as_tuples(peeled_again) == windows_as_tuples(schedule.windows) and cells == ()


def test_t_sup_11_b_missing_cutoff_bar_forces_no_peel():
    _, _, _, schedule = round2(join_missing=("2024-05-14", "2024-05-15"))
    assert schedule.g_term == ()
    assert windows_as_tuples(schedule.windows) == [
        (row("2024-05-16"), row("2024-05-30"), frozenset({"missing_bar"}))]
    assert schedule.segments[0].last == row("2024-05-15")


def test_t_sup_11_c_second_peel_from_a_second_terminal_window_joiner():
    _, _, _, schedule = round2(join2=True)
    assert not schedule.g_base.loc[pd.Timestamp("2024-05-14"), "JOIN2"]
    assert schedule.g_term == (("JOIN", row("2024-05-15")), ("JOIN2", row("2024-05-14")))
    assert (schedule.windows[0].start, schedule.windows[0].end) == (row("2024-05-14"), row("2024-05-30"))
    assert schedule.windows[0].peeled_rows == 2
    assert schedule.segments[0].last == row("2024-05-13")


def test_t_sup_11_d_peeling_stops_at_the_first_reset_and_drops_the_segment():
    R = scheduled_reset_rows(ROUND2)
    d0 = int(next(r for r in R if r >= 253))
    k = int(np.flatnonzero(R == d0)[0]) + 6
    p = int(R[k])
    joiners = [f"J{i}" for i in range(1, 6)]
    assets = ["OLD", "OLD2", *joiners]
    starts = {"OLD": 0, "OLD2": 0, **{j: p for j in joiners}}
    bars = pd.DataFrame(True, index=ROUND2, columns=assets)
    bars.iloc[p - 3, 0] = False
    bars.iloc[p + 6, 1] = False
    for i, joiner in enumerate(joiners, start=1):
        bars.iloc[p + 6 - i, assets.index(joiner)] = False
    mask = resolve_pit_universe_mask(intervals(ROUND2, starts), None, ROUND2, assets)
    schedule = common_support_schedule(ROUND2, bars, mask, {}, d0)
    base = gap_windows(schedule.g_base, {}, R, d0, schedule.d_last)
    unpeeled = support_segments(base, d0, schedule.d_last)
    assert [(s.first, s.last) for s in unpeeled][1] == (p, p + 5)
    assert schedule.g_term == tuple((f"J{i}", p + 6 - i) for i in range(1, 6))
    dropped = next(s for s in schedule.segments if s.first == p)
    assert (dropped.last, dropped.valid) == (p, False)
    assert schedule.windows[1].start == p + 1 and schedule.windows[1].peeled_rows == 5
    unpeeled_excluded = (schedule.d_last - d0 + 1) - sum(s.rows for s in unpeeled if s.valid)
    assert schedule.excluded_rows == unpeeled_excluded
    assert not schedule.g_base[joiners].any().any()


def equal_weight_signal(s_mask):
    return s_mask.astype(float).where(s_mask)


@pytest.mark.parametrize("book", ["lo", "ls", "ew"])
def test_t_sup_11_a_engines_refuse_unpeeled_and_complete_peeled(book):
    prices, table, mask, schedule = round2()
    s_mask = signal_eligibility(mask, prices.notna())
    scores = pd.DataFrame({"OLD": 2.0, "JOIN": 3.0, "OTHER": 1.0}, index=ROUND2).where(s_mask)

    def run(end_day):
        common = dict(evaluation_start=ROUND2[schedule.d0 - 1], evaluation_end=pd.Timestamp(end_day),
                      rebalance_frequency="ME", constituent_intervals=table)
        if book == "ls":
            return run_long_short_backtest(prices, scores, quantiles=2, transaction_cost_bps=1.0,
                                           slippage_bps=4.0, **common)
        signal = scores if book == "lo" else equal_weight_signal(s_mask)
        sizing = {"top_n": 1, "transaction_cost_bps": 1.0, "slippage_bps": 4.0} if book == "lo" else {"top_pct": 1.0}
        return run_long_only_backtest(prices, signal, source_provenance=capture_backtest_source_provenance(
            prices, signal), **sizing, **common)

    with pytest.raises(BacktestValidationError, match="execution_price_invalid"):
        run("2024-05-15")
    assert run(ROUND2[schedule.segments[0].last]).equity_curve.notna().all()


def test_holding_cells_follow_membership_runs_and_open_intervals():
    dates = Y2024
    R = scheduled_reset_rows(dates)
    table = intervals(dates, {"A": 0, "B": int(R[2]) - 3, "C": int(R[4]) + 1}, ends={"A": int(R[3]) + 2,
                                                                                         "C": int(R[4]) + 5})
    mask = resolve_pit_universe_mask(table, None, dates, ["A", "B", "C"])
    held = holding_cells(mask, R, int(R[-1]))
    assert np.flatnonzero(held["A"]).tolist() == list(range(int(R[0]), int(R[4]) + 1))
    assert np.flatnonzero(held["B"]).tolist() == list(range(int(R[2]), int(R[-1]) + 1))
    assert not held["C"].any()
    bars = pd.DataFrame(True, index=dates, columns=["A", "B", "C"])
    bars.iloc[: int(R[2]) + 1, 1] = False
    bars.iloc[int(R[3]):, 0] = False
    g = base_exclusion_cells(bars, mask, R, int(R[-1]))
    assert not g.any().any()


def test_max_reset_span_refuses_a_single_reset():
    R = scheduled_reset_rows(Y2024)
    assert max_reset_to_reset_rows(R, int(R[0]), int(R[1])) == int(R[1] - R[0])
    with pytest.raises(ValueError):
        max_reset_to_reset_rows(R, int(R[-1]), int(R[-1]))
    with pytest.raises(ValueError, match="d0"):
        common_support_schedule(Y2024, pd.DataFrame(True, index=Y2024, columns=["A"]),
                                pd.DataFrame(True, index=Y2024, columns=["A"]), {}, int(R[0]) + 1)


@pytest.mark.parametrize("builder", [walk_forward_ic_weighted_composite, walk_forward_icir_weighted_composite])
def test_t_reg_4b_composite_ignores_labels_whose_horizon_closes_after_t(builder):
    dates = pd.bdate_range("2021-01-01", periods=400, name="date")
    rng = np.random.default_rng(44)
    assets = [f"A{i:02d}" for i in range(40)]
    prices = pd.DataFrame(100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, (400, 40)), axis=0)),
                          index=dates, columns=assets)
    factors = [pd.DataFrame(rng.normal(size=(400, 40)), index=dates, columns=assets) for _ in range(2)]
    R = scheduled_reset_rows(dates)
    d0 = int(R[1])
    label_resets = tuple(int(r) for r in R if d0 <= r < R[-1])
    s_mask = pd.DataFrame(True, index=dates, columns=assets)
    horizon = max_reset_to_reset_rows(R, d0, int(R[-1]))
    rebalances = dates[[int(r) - 1 for r in R if r >= d0]]

    def composite(labels):
        history = pd.DataFrame({
            f"F{i}": monthly_rank_ic(factor, labels, label_resets, min_pairs=10)["rank_ic"]
            for i, factor in enumerate(factors)
        })
        assert history.index.equals(dates[[r - 1 for r in label_resets]])
        return builder(factors, history, rebalances, execution_lag_periods=1, forward_holding_periods=horizon)

    labels, _ = reset_to_reset_labels(prices, s_mask, R, label_resets, None)
    baseline = composite(labels)
    t = int(R[10]) - 1
    closes_after_t = [r for r in label_resets if int(R[R > r][0]) > t]
    perturbed = labels.copy()
    perturbed.iloc[[r - 1 for r in closes_after_t]] = rng.normal(size=(len(closes_after_t), 40))
    pd.testing.assert_series_equal(composite(perturbed).iloc[t], baseline.iloc[t])
    admitted = labels.copy()
    admitted.iloc[label_resets[0] - 1] = -labels.iloc[label_resets[0] - 1]
    assert not np.allclose(composite(admitted).iloc[t].to_numpy(), baseline.iloc[t].to_numpy())


def test_empty_asset_axis_yields_one_full_segment_and_empty_labels():
    R = scheduled_reset_rows(Y2024)
    empty = pd.DataFrame(index=Y2024, columns=pd.Index([], dtype=object), dtype=bool)
    schedule = common_support_schedule(Y2024, empty, empty, {}, int(R[0]))
    assert schedule.windows == () and schedule.g_term == ()
    assert [(s.first, s.last, s.valid) for s in schedule.segments] == [(int(R[0]), int(R[-1]), True)]
    assert schedule.excluded_rows == 0 and schedule.g_base.shape == (len(Y2024), 0)
    assert signal_eligibility(empty, empty).shape == (len(Y2024), 0)
    labels, records = reset_to_reset_labels(empty.astype(float), empty, R, (int(R[1]),), None)
    assert labels.shape == (len(Y2024), 0) and records["eligible_count"].tolist() == [0]
    with pytest.raises(ValueError, match="must not be empty"):
        monthly_rank_ic(empty.astype(float), empty.astype(float), (int(R[1]),))


def test_empty_calendar_and_misaligned_panels_refuse():
    none = pd.DatetimeIndex([], name="date")
    assert scheduled_reset_rows(none).tolist() == []
    frame = pd.DataFrame(index=none, columns=["A"], dtype=bool)
    with pytest.raises(ValueError, match="d0"):
        common_support_schedule(none, frame, frame, {}, 0)
    bars = pd.DataFrame(True, index=Y2024, columns=["A"])
    with pytest.raises(ValueError, match="share index and columns"):
        signal_eligibility(bars.rename(columns={"A": "B"}), bars)
    with pytest.raises(ValueError, match="calendar"):
        common_support_schedule(Y2024[1:], bars, bars, {}, 0)
