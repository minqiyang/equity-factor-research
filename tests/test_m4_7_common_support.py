"""M4.7 asset-level support, label, and IC-month oracles (T-SUP-1, 2, 3, 8, 11 under support v2; T-REG-4b)."""

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
    common_support_schedule,
    ic_month_set,
    max_reset_to_reset_rows,
    monthly_rank_ic,
    reset_to_reset_labels,
    scheduled_reset_rows,
    signal_eligibility,
    support_exclusions,
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


def test_reset_rows_match_engine_month_end_schedule():
    for calendar in (Y2024, pd.bdate_range("2022-01-03", "2026-08-31")):
        rows = scheduled_reset_rows(calendar)
        assert calendar[rows].equals(_get_rebalance_dates(calendar, "ME"))
    assert scheduled_reset_rows(Y2024[:1]).tolist() == [0]


def isolation_fixture():
    """Five members from row 0 plus a late joiner; each special asset has one support defect."""
    R = scheduled_reset_rows(Y2024)
    assets = ["HALT", "RESET", "GONE", "DEAL", "LAST", "CLEAN", "LATE"]
    bars = pd.DataFrame(True, index=Y2024, columns=assets)
    bars.iloc[R[3] + 5, 0] = False              # mid-month halt inside the R[3] period
    bars.iloc[R[5], 1] = False                  # missing bar on a reset row: sale and buy both need it
    bars.iloc[R[7] + 3:, 2] = False             # unevidenced disappearance after R[7] + 2
    bars.iloc[R[8] + 4:, 3] = False             # settled terminal event at R[8] + 4
    bars.iloc[R[-1], 4] = False                 # missing bar on the last reset
    bars.iloc[R[2] - 1, 6] = False              # LATE joins after its only missing bar
    table = intervals(Y2024, {**{a: 0 for a in assets[:-1]}, "LATE": int(R[2]) + 1})
    deal = events(Y2024, [("DEAL", int(R[8]) + 4, int(R[8]), 0.1, CASH)])
    mask = resolve_pit_universe_mask(table, deal, Y2024, assets)
    schedule = common_support_schedule(Y2024, bars, mask, {"GONE": int(R[7]) + 3}, int(R[0]),
                                       {"DEAL": int(R[8]) + 4})
    return R, bars, mask, schedule


def test_t_sup_1_exclusion_cells_are_asset_and_period_local():
    R, bars, mask, schedule = isolation_fixture()
    assert sorted(schedule.reasons) == sorted([
        ("HALT", int(R[3]), "missing_bar"),
        ("RESET", int(R[4]), "missing_bar"), ("RESET", int(R[5]), "missing_bar"),
        ("GONE", int(R[7]), "unresolved_delisting"),
        ("LAST", int(R[-2]), "missing_bar"), ("LAST", int(R[-1]), "missing_bar"),
    ])
    rows, columns = np.nonzero(schedule.exclusions.to_numpy())
    assert sorted((schedule.exclusions.columns[c], int(r) + 1) for r, c in zip(rows, columns)) == sorted(
        (asset, row) for asset, row, _ in schedule.reasons)
    assert not schedule.exclusions[["DEAL", "CLEAN", "LATE"]].any().any()
    evaluated = schedule.evaluation_mask
    assert evaluated.iloc[R[2] - 1]["HALT"] and evaluated.iloc[R[4] - 1]["HALT"]
    assert not evaluated.iloc[R[3] - 1]["HALT"]
    assert not schedule.s_mask.iloc[R[8] - 1:, 2].any()
    assert schedule.s_mask.iloc[R[8] - 1]["DEAL"] and not mask.iloc[R[8] + 4:, 3].any()
    assert schedule.s_mask.iloc[R[3] - 1]["LATE"] and not schedule.s_mask.iloc[R[1] - 1]["LATE"]


def test_t_sup_1_reason_types_only_the_period_that_holds_the_disappearance():
    """Ablation witness: an asset in ``U`` with an earlier halt keeps ``missing_bar`` for the halt's period."""
    R = scheduled_reset_rows(Y2024)
    s_mask = pd.DataFrame(True, index=Y2024, columns=["GONE"])
    s_mask.iloc[R[6]:] = False
    bars = pd.DataFrame(True, index=Y2024, columns=["GONE"])
    bars.iloc[R[2] + 4, 0] = False
    bars.iloc[R[6] + 3:, 0] = False
    _, reasons = support_exclusions(s_mask, bars, R, int(R[0]), int(R[-1]), {}, {"GONE": int(R[6]) + 3})
    assert reasons == (("GONE", int(R[2]), "missing_bar"), ("GONE", int(R[6]), "unresolved_delisting"))


def test_t_sup_2_every_reset_stays_in_one_continuous_window():
    R, _, _, schedule = isolation_fixture()
    assert schedule.evaluation_resets.tolist() == R.tolist()
    breadth = schedule.breadth()
    assert breadth.index.equals(Y2024[R])
    assert (breadth["signal_eligible"] - breadth["support_excluded"]).equals(breadth["evaluated"])
    assert breadth["support_excluded"].sum() == len(schedule.reasons) == 6
    assert breadth["evaluated"].min() == 4 and breadth["support_excluded"].max() == 1
    assert schedule.excluded_fraction == 6 / breadth["signal_eligible"].sum()
    assert schedule.max_reset_to_reset_rows == int(np.diff(R).max()) == 23


def test_t_sup_2_terminal_settlement_ends_the_holding_period():
    R = scheduled_reset_rows(Y2024)
    settle = int(R[8]) + 4
    s_mask = pd.DataFrame(True, index=Y2024, columns=["DEAL"])
    s_mask.iloc[R[8]:] = False
    bars = pd.DataFrame(True, index=Y2024, columns=["DEAL"])
    bars.iloc[settle:, 0] = False
    window = (s_mask, bars, R, int(R[0]), int(R[-1]))
    assert support_exclusions(*window, {"DEAL": settle}, {})[1] == ()
    assert support_exclusions(*window, {}, {"DEAL": settle})[1] == (("DEAL", int(R[8]), "unresolved_delisting"),)
    bars.iloc[settle - 2, 0] = False
    exclusions, reasons = support_exclusions(*window, {"DEAL": settle}, {})
    assert reasons == (("DEAL", int(R[8]), "missing_bar"),)
    assert np.flatnonzero(exclusions["DEAL"]).tolist() == [int(R[8]) - 1]


def test_t_sup_8_ic_month_set_keeps_every_reset_with_a_horizon():
    R, _, _, schedule = isolation_fixture()
    t_ic, excluded = ic_month_set(schedule)
    assert t_ic == tuple(int(r) for r in R[:-1])
    assert excluded == {"ic_month_horizon_unmeasured": (int(R[-1]),)}


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


def round2():
    """OLD misses 2024-05-16 inside its May holding period; JOIN misses 2024-05-15 before its first reset."""
    assets = ["OLD", "JOIN", "OTHER"]
    starts = {"OLD": 0, "JOIN": ROUND2.get_loc(pd.Timestamp("2024-05-10")), "OTHER": 0}
    prices = pd.DataFrame(100.0, index=ROUND2, columns=assets)
    prices.loc[pd.Timestamp("2024-05-16"), "OLD"] = np.nan
    prices.loc[pd.Timestamp("2024-05-15"), "JOIN"] = np.nan
    table = intervals(ROUND2, starts)
    mask = resolve_pit_universe_mask(table, None, ROUND2, assets)
    reset_rows = scheduled_reset_rows(ROUND2)
    d0 = int(next(r for r in reset_rows if r >= 253))
    schedule = common_support_schedule(ROUND2, prices.notna(), mask, {}, d0)
    return prices, table, mask, schedule


def test_t_sup_11_one_asset_one_period_on_the_round_two_counterexample():
    _, _, _, schedule = round2()
    assert schedule.reasons == (("OLD", ROUND2.get_loc(pd.Timestamp("2024-04-30")), "missing_bar"),)
    assert schedule.evaluation_resets.tolist() == [r for r in scheduled_reset_rows(ROUND2) if r >= schedule.d0]
    may = ROUND2.get_loc(pd.Timestamp("2024-05-31")) - 1
    assert schedule.evaluation_mask.iloc[may].tolist() == [True, True, True]


def equal_weight_signal(s_mask):
    return s_mask.astype(float).where(s_mask)


@pytest.mark.parametrize("book", ["lo", "ls", "ew"])
def test_t_sup_11_engines_refuse_s_mask_and_complete_the_whole_window_on_e(book):
    prices, table, _, schedule = round2()
    scores = pd.DataFrame({"OLD": 2.0, "JOIN": 3.0, "OTHER": 1.0}, index=ROUND2)

    def run(mask):
        common = dict(evaluation_start=ROUND2[schedule.d0 - 1], evaluation_end=ROUND2[schedule.d_last],
                      rebalance_frequency="ME", constituent_intervals=table)
        signal = scores.where(mask)
        if book == "ls":
            return run_long_short_backtest(prices, signal, quantiles=2, transaction_cost_bps=1.0,
                                           slippage_bps=4.0, **common)
        signal = signal if book == "lo" else equal_weight_signal(mask)
        sizing = {"top_n": 1, "transaction_cost_bps": 1.0, "slippage_bps": 4.0} if book == "lo" else {"top_pct": 1.0}
        return run_long_only_backtest(prices, signal, source_provenance=capture_backtest_source_provenance(
            prices, signal), **sizing, **common)

    with pytest.raises(BacktestValidationError, match="incoming_price_invalid"):
        run(schedule.s_mask)
    result = run(schedule.evaluation_mask)
    assert result.equity_curve.notna().all() and len(result.returns) == schedule.d_last - schedule.d0 + 2
    held = (result.net_holdings if book == "ls" else result.holdings)["OLD"]
    assert (held.loc["2024-04-30":"2024-05-30"] == 0.0).all()
    assert (held.loc["2024-05-31":"2024-06-27"] != 0.0).all() or book == "lo"


def test_max_reset_span_refuses_a_single_reset():
    R = scheduled_reset_rows(Y2024)
    assert max_reset_to_reset_rows(R, int(R[0]), int(R[1])) == int(R[1] - R[0])
    with pytest.raises(ValueError):
        max_reset_to_reset_rows(R, int(R[-1]), int(R[-1]))
    with pytest.raises(ValueError, match="d0"):
        common_support_schedule(Y2024, pd.DataFrame(True, index=Y2024, columns=["A"]),
                                pd.DataFrame(True, index=Y2024, columns=["A"]), {}, int(R[0]) + 1)
    first = pd.bdate_range("2024-01-31", "2024-03-29", name="date")
    with pytest.raises(ValueError, match="after the first calendar row"):
        common_support_schedule(first, pd.DataFrame(True, index=first, columns=["A"]),
                                pd.DataFrame(True, index=first, columns=["A"]), {}, 0)


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


def test_empty_asset_axis_yields_every_reset_and_empty_labels():
    R = scheduled_reset_rows(Y2024)
    empty = pd.DataFrame(index=Y2024, columns=pd.Index([], dtype=object), dtype=bool)
    schedule = common_support_schedule(Y2024, empty, empty, {}, int(R[0]))
    assert schedule.reasons == () and schedule.evaluation_resets.tolist() == R.tolist()
    assert schedule.exclusions.shape == (len(Y2024), 0) and schedule.excluded_fraction == 0.0
    assert schedule.breadth()["evaluated"].tolist() == [0] * len(R)
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


def readiness_after(schedule):
    from research.m4_7_coverage_census import derive_readiness

    clean = {
        "in_band_years": 20.0, "holdout_end": "2000-01-31", "identity_refusal_fraction": 0.0, "off_calendar_fraction": 0.0,
        "calendar_covers_coverage_start": True, "benchmark_complete": True, "snapshot_integrity": True,
        "holdout_band_after_identity": True, "ic_month_supply": 120, "unpriced_fraction": 0.0, "retrieval_complete": True,
    }
    return derive_readiness({**clean, "excluded_fraction": schedule.excluded_fraction})


@pytest.mark.parametrize("count, status", [(4, "blocked"), (3, "ready")])
def test_t_sup_3_cap_reads_the_asset_level_excluded_fraction(count, status):
    """R-CENSUS-2 reads support-excluded cells over signal-eligible cells; no window count exists."""
    calendar = pd.bdate_range("2019-01-01", "2024-12-31", name="date")
    R = scheduled_reset_rows(calendar)
    bars = pd.DataFrame(True, index=calendar, columns=["A"])
    for month in range(count):
        bars.iloc[R[6 + 7 * month] - 2, 0] = False
    mask = resolve_pit_universe_mask(intervals(calendar, {"A": 0}), None, calendar, ["A"])
    schedule = common_support_schedule(calendar, bars, mask, {}, int(R[0]))
    assert len(schedule.reasons) == count and len(schedule.evaluation_resets) == len(R) == 72
    assert schedule.excluded_fraction == pytest.approx(count / 72)
    readiness = readiness_after(schedule)
    assert readiness["status"] == status and readiness["inputs"]["excluded_fraction"] == schedule.excluded_fraction
