"""M4.8 Stage B engine oracles: T-HALT-1..9, T-CAUSAL-1..3, and T-HAC-1 (plan 4.3, 6.4, 8.1).

Every fixture is a small synthetic daily panel. ``halt_gap_return_v1`` marks a
held asset at its last observed close, realizes the gap at its next close, and
executes scheduled rows under ``self_financing_locked_capital_v1``. No test
opens a network connection or reads private data.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

import research.m4_7_sp500_pit_rerun as runner
from backtest.long_short import run_long_short_backtest
from backtest.market_impact import SquareRootImpactModel
from backtest.portfolio import (
    HALT_GAP_POLICY,
    BacktestValidationError,
    capture_backtest_source_provenance,
    run_long_only_backtest,
)
from features.diagnostics import newey_west_long_run_variance, segment_aware_bartlett_long_run_variance
from research.m4_7_common_support import scheduled_reset_rows


HALT = HALT_GAP_POLICY
DATES = pd.bdate_range("2021-01-01", periods=90)
RESETS = scheduled_reset_rows(DATES)  # [20, 39, 62, 83, 89]
R1, R2, R3 = (int(r) for r in RESETS[1:4])


def walk(n_assets: int, seed: int, dates: pd.DatetimeIndex = DATES) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    values = 50.0 * np.exp(np.cumsum(rng.normal(0.0002, 0.01, (len(dates), n_assets)), axis=0))
    return pd.DataFrame(values, index=dates, columns=[f"A{i:02d}" for i in range(n_assets)])


def ranked(prices: pd.DataFrame, order: list[str], *, after: int | None = None, later: list[str] | None = None):
    """Constant scores: earlier names rank higher; from row ``after`` on, ``later`` gives the order."""
    scores = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    for rank, asset in enumerate(order):
        scores[asset] = float(len(order) - rank)
    if after is not None:
        for rank, asset in enumerate(later):
            scores.iloc[after:, scores.columns.get_loc(asset)] = float(len(later) - rank)
        rest = [a for a in prices.columns if a not in later]
        scores.iloc[after:, [scores.columns.get_loc(a) for a in rest]] = -1.0
    return scores


def long_only(prices, signals, *, policy=HALT, costs=(1.0, 4.0), **kwargs):
    return run_long_only_backtest(
        prices, signals, source_provenance=capture_backtest_source_provenance(prices, signals),
        evaluation_start=kwargs.pop("start", prices.index[0]), evaluation_end=kwargs.pop("end", prices.index[-1]),
        transaction_cost_bps=costs[0], slippage_bps=costs[1], missing_price_policy=policy, **kwargs)


def long_short(prices, signals, *, policy=HALT, costs=(1.0, 4.0), quantiles=4, **kwargs):
    return run_long_short_backtest(
        prices, signals, evaluation_start=kwargs.pop("start", prices.index[0]),
        evaluation_end=kwargs.pop("end", prices.index[-1]), quantiles=quantiles, transaction_cost_bps=costs[0],
        slippage_bps=costs[1], missing_price_policy=policy, **kwargs)


def halt(prices: pd.DataFrame, asset: str, start: int, stop: int) -> pd.DataFrame:
    edited = prices.copy()
    edited.iloc[start:stop, edited.columns.get_loc(asset)] = np.nan
    return edited


def values(result, asset: str) -> pd.Series:
    held = result.net_holdings if hasattr(result, "net_holdings") else result.holdings
    return held[asset] * result.equity_curve


def locked_rows(result) -> dict[pd.Timestamp, dict]:
    return {row["date"]: row for row in result.halt_ledger["locked_execution_rows"]}


# ---------------------------------------------------------------- T-HALT-1, 2


@pytest.mark.parametrize("engine", ["long_only", "long_short"])
def test_t_halt_1_2_gap_return_at_resumption_equals_the_price_ratio(engine):
    prices = walk(8, 1)
    signals = ranked(prices, [f"A{i:02d}" for i in range(8)])
    asset = "A00" if engine == "long_only" else "A07"  # a long and a short position
    edited = halt(prices, asset, 30, 33)
    if engine == "long_only":
        result = long_only(edited, signals, top_n=2)
        with pytest.raises(BacktestValidationError) as refused:
            long_only(edited, signals, top_n=2, policy="raise")
    else:
        result = long_short(edited, signals)
        with pytest.raises(BacktestValidationError) as refused:
            long_short(edited, signals, policy="raise")
    assert refused.value.reason == "incoming_price_invalid"
    value = values(result, asset)
    assert np.allclose(value.iloc[30:33], value.iloc[29], rtol=1e-12, atol=0.0)
    assert value.iloc[33] / value.iloc[29] == pytest.approx(prices[asset].iloc[33] / prices[asset].iloc[29], rel=1e-12)
    assert result.halt_ledger["unmarked_halt_rows"] == [(DATES[r], asset) for r in (30, 31, 32)]
    summary = result.assumptions
    assert summary["unmarked_halt_row_count"] == 3 and summary["locked_execution_row_count"] == 0


# ---------------------------------------------------------------- T-HALT-3, 3b, 3c (long-only book and benchmark)


def _long_only_invariants(result):
    cash = result.cash_balance
    gross = result.holdings.sum(axis=1)
    assert (cash >= -1e-12).all() and (gross <= 1.0 + 1e-12).all() and (result.holdings >= 0.0).all().all()
    assert np.allclose(cash + (result.holdings * result.equity_curve.to_numpy()[:, None]).sum(axis=1),
                       result.equity_curve, rtol=1e-12, atol=1e-12)
    for row in result.halt_ledger["locked_execution_rows"]:
        for asset, weight in row["executable_target"].items():
            if asset not in row["locked"]:
                assert weight <= row["intended_target"][asset] + 1e-15


def test_t_halt_3_untradeable_target_stays_in_cash_and_a_locked_asset_keeps_its_quantity():
    prices = walk(6, 2)
    order = ["A00", "A01", "A02", "A03", "A04", "A05"]
    signals = ranked(prices, order, after=R2 - 3, later=["A01", "A02", "A00", "A03", "A04", "A05"])
    edited = halt(halt(prices, "A02", R2, R2 + 1), "A00", R2 - 1, R2 + 2)  # A02 unheld target, A00 held
    result = long_only(edited, signals, top_n=2)
    row = locked_rows(result)[DATES[R2]]
    assert row["untradeable_targets"] == ["A02"] and list(row["locked"]) == ["A00"]
    assert result.holdings.loc[DATES[R2], "A02"] == 0.0
    free = 1.0 - row["locked"]["A00"]
    assert row["phi"][1] == pytest.approx(free, rel=1e-12)  # W' = 1 over A01 and A02
    cost = result.total_trading_costs.loc[DATES[R2]] / (1.0 + result.gross_returns.loc[DATES[R2]])
    assert result.cash_balance.loc[DATES[R2]] / result.equity_curve.loc[DATES[R2]] == pytest.approx(
        0.5 * (free - cost) / (1.0 - cost), rel=1e-9)  # A02's share stays in cash; the free sleeve pays the cost
    mark = prices["A00"].iloc[R2 - 2]
    quantity = values(result, "A00").iloc[R2 - 2:R2 + 2] / mark
    assert np.allclose(quantity, quantity.iloc[0], rtol=1e-12)
    assert (DATES[R2], "A02") in result.halt_ledger["untradeable_execution_cells"]
    assert result.holdings.loc[DATES[R3], "A02"] > 0.0  # bought at the next reset with a close
    _long_only_invariants(result)


@pytest.mark.parametrize("case", ["outgoing_target_zero", "locked_stays_selected", "simultaneous", "above_budget",
                                  "benchmark"])
def test_t_halt_3b_long_only_cash_and_gross_stay_bounded(case):
    prices = walk(6, 3)
    order = ["A00", "A01", "A02", "A03", "A04", "A05"]
    kwargs = {"top_n": 2}
    if case == "outgoing_target_zero":
        signals = ranked(prices, order, after=R2 - 3, later=["A02", "A03", "A00", "A01", "A04", "A05"])
        edited = halt(prices, "A00", R2 - 1, R2 + 3)
    elif case == "locked_stays_selected":
        signals = ranked(prices, order)
        edited = halt(prices, "A00", R2 - 1, R2 + 3)
    elif case == "simultaneous":
        signals = ranked(prices, order, after=R2 - 3, later=["A02", "A00", "A03", "A01", "A04", "A05"])
        edited = halt(halt(prices, "A00", R2 - 1, R2 + 3), "A01", R2, R2 + 2)
    elif case == "above_budget":
        signals = ranked(prices, order, after=R2 - 3, later=["A01", "A02", "A03", "A00", "A04", "A05"])
        edited, kwargs = halt(prices, "A00", R2 - 1, R2 + 3), {"top_n": 1}
    else:
        signals = pd.DataFrame(1.0, index=prices.index, columns=prices.columns)
        edited, kwargs = halt(halt(prices, "A00", R2 - 1, R2 + 3), "A03", R2, R2 + 1), {"top_pct": 1.0}
    result = long_only(edited, signals, **kwargs)
    row = locked_rows(result)[DATES[R2]]
    assert "A00" in row["locked"]
    if case == "above_budget":
        assert row["phi"][1] == 0.0 and row["executable_target"] == row["locked"]
    if case == "benchmark":  # the benchmark holds every eligible name, so both halted names are locked
        assert set(row["locked"]) == {"A00", "A03"} and row["untradeable_targets"] == []
    _long_only_invariants(result)


def test_t_halt_3c_locked_turnover_and_cost_are_charged_at_the_release_row():
    prices = walk(6, 4)
    signals = ranked(prices, ["A00", "A01", "A02", "A03", "A04", "A05"], after=R1 - 3,
                     later=["A01", "A02", "A03", "A00", "A04", "A05"])
    edited = halt(prices, "A00", R1 - 1, R1 + 3)
    result = long_only(edited, signals, top_n=2)
    assert result.trade_weights.loc[DATES[R1], "A00"] == 0.0
    mark = prices["A00"].iloc[R1 - 2]
    quantity = values(result, "A00").iloc[R1 - 2:R1 + 3] / mark
    assert np.allclose(quantity, quantity.iloc[0], rtol=1e-12)
    pretrade = values(result, "A00").iloc[R2 - 1] * (prices["A00"].iloc[R2] / prices["A00"].iloc[R2 - 1])
    equity_before = result.equity_curve.iloc[R2 - 1] * (1.0 + result.gross_returns.iloc[R2])
    assert result.trade_weights.loc[DATES[R2], "A00"] == pytest.approx(pretrade / equity_before, rel=1e-12)
    assert result.holdings.loc[DATES[R2], "A00"] == 0.0
    free_turnover = float(result.trade_weights.loc[DATES[R2]].sum())
    assert result.turnover.loc[DATES[R2]] == pytest.approx(free_turnover, rel=1e-15)
    assert result.total_trading_costs.loc[DATES[R2]] == pytest.approx(
        free_turnover * 5.0 / 10_000.0 * (1.0 + result.gross_returns.iloc[R2]), rel=1e-12)


# ---------------------------------------------------------------- T-HALT-4, 4b (long-short)


def test_t_halt_4_short_side_halt_mirrors_the_long_side():
    prices = walk(8, 5)
    order = [f"A{i:02d}" for i in range(8)]
    signals = ranked(prices, order, after=R2 - 3, later=["A00", "A01", "A02", "A03", "A04", "A06", "A05", "A07"])
    edited = halt(halt(prices, "A07", R2 - 1, R2 + 2), "A05", R2, R2 + 1)  # A07 held short, A05 unheld short target
    result = long_short(edited, signals)
    row = locked_rows(result)[DATES[R2]]
    assert list(row["locked"]) == ["A07"] and row["locked"]["A07"] < 0.0 and row["untradeable_targets"] == ["A05"]
    assert result.net_holdings.loc[DATES[R2], "A05"] == 0.0 and result.net_holdings.loc[DATES[R2], "A06"] == 0.0
    mark = prices["A07"].iloc[R2 - 2]
    quantity = values(result, "A07").iloc[R2 - 2:R2 + 1] / mark
    assert np.allclose(quantity, quantity.iloc[0], rtol=1e-12)
    value = values(result, "A07")
    assert value.iloc[R2 + 2] / value.iloc[R2 - 2] == pytest.approx(
        prices["A07"].iloc[R2 + 2] / prices["A07"].iloc[R2 - 2], rel=1e-12)


def _typed(result, kind):
    return [row for row in result.halt_ledger["typed_exposure_rows"] if row["type"] == kind]


def test_t_halt_4b_outgoing_short_and_side_reversal_are_matched_at_zero_pre_cost_net():
    prices = walk(8, 6)
    order = [f"A{i:02d}" for i in range(8)]
    reversal = ["A07", "A06", "A02", "A03", "A04", "A05", "A00", "A01"]  # locked long A00 now targeted short
    signals = ranked(prices, order, after=R2 - 3, later=reversal)
    edited = halt(halt(prices, "A00", R2 - 1, R2 + 2), "A07", R2 - 1, R2 + 2)  # A07 an outgoing short
    result = long_short(edited, signals)
    row = locked_rows(result)[DATES[R2]]
    assert row["locked"]["A00"] > 0.0 and row["locked"]["A07"] < 0.0
    assert row["executable_target"]["A00"] == row["locked"]["A00"]
    assert all(row["executable_target"].get(a, 0.0) <= 0.0 for a in ("A01",))
    assert abs(row["pre_cost_net"]) < 1e-15
    weights = result.net_holdings.loc[DATES[R2]]
    for typed in result.halt_ledger["typed_exposure_rows"]:
        if typed["type"] == "locked_net_exposure" and typed["date"] == DATES[R2]:
            assert typed["value"] == pytest.approx(float(weights.sum()), rel=1e-12)


def test_t_halt_4b_a_locked_leg_above_the_other_legs_attainable_value_is_typed():
    prices = walk(8, 7)
    order = [f"A{i:02d}" for i in range(8)]
    signals = ranked(prices, order, after=R2 - 3, later=["A02", "A03", "A04", "A05", "A00", "A01", "A06", "A07"])
    edited = prices.copy()
    for asset, (start, stop) in {"A00": (R2 - 1, R2 + 2), "A01": (R2 - 1, R2 + 2), "A06": (R2, R2 + 1),
                                 "A07": (R2, R2 + 1)}.items():
        edited = halt(edited, asset, start, stop)
    result = long_short(edited, signals)
    row = locked_rows(result)[DATES[R2]]
    assert row["lam"][1] > row["attainable"][-1]  # locked long exceeds the short leg's attainable value
    assert row["pre_cost_net"] == pytest.approx(row["lam"][1] - row["attainable"][-1], rel=1e-12)
    net = _typed(result, "locked_net_exposure")
    assert [r["date"] for r in net] == [DATES[R2]]
    assert net[0]["value"] == pytest.approx(float(result.net_holdings.loc[DATES[R2]].sum()), rel=1e-12)
    assert result.assumptions["locked_net_exposure_row_count"] == 1


def test_t_halt_4b_symmetric_locked_legs_type_the_cost_created_gross_excess():
    dates = DATES
    prices = pd.DataFrame(50.0, index=dates, columns=[f"A{i:02d}" for i in range(50)])
    rng = np.random.default_rng(8)
    first, second = rng.permutation(50), rng.permutation(50)
    signals = pd.DataFrame(np.tile(first, (len(dates), 1)).astype(float), index=dates, columns=prices.columns)
    signals.iloc[R2 - 3:] = second.astype(float)
    top, bottom = prices.columns[first >= 45], prices.columns[first < 5]
    long_locked, short_locked = top[0], bottom[0]
    edited = halt(halt(prices, long_locked, R2 - 1, R2 + 2), short_locked, R2 - 1, R2 + 2)
    result = long_short(edited, signals, quantiles=10)
    row = locked_rows(result)[DATES[R2]]
    assert row["locked"] == {long_locked: pytest.approx(0.1), short_locked: pytest.approx(-0.1)}
    delta = float(result.total_trading_costs.loc[DATES[R2]]) / (1.0 + float(result.gross_returns.loc[DATES[R2]]))
    excess = _typed(result, "locked_gross_excess")
    assert [r["date"] for r in excess] == [DATES[R2]]
    assert excess[0]["value"] == pytest.approx(0.2 * delta / (1.0 - delta), rel=1e-9)
    assert not _typed(result, "locked_net_exposure")


def test_t_halt_4b_between_reset_drift_is_recorded_and_never_typed():
    dates = DATES
    prices = pd.DataFrame(50.0, index=dates, columns=["L", "S"])
    prices.loc[dates[R1 + 1]:, "L"] = 50.5  # +1 percent on the long leg, 0 percent on the short leg
    signals = pd.DataFrame({"L": 1.0, "S": 0.0}, index=dates)
    result = long_short(prices, signals, quantiles=2, costs=(0.0, 0.0))
    net = result.net_holdings.sum(axis=1)
    assert net.loc[dates[R1 + 1]] == pytest.approx(0.005 / 1.005, rel=1e-12)
    assert round(float(net.loc[dates[R1 + 1]]), 6) == 0.004975
    assert result.halt_ledger["typed_exposure_rows"] == [] and result.halt_ledger["locked_execution_rows"] == []


# ---------------------------------------------------------------- T-HALT-5, 6, 7b, 8, 9


def _event(asset, effective, reference, known, value):
    return pd.DataFrame([{"event_id": f"e-{asset}", "permanent_id": asset, "effective_date": effective,
                          "known_at": known, "reference_date": reference, "terminal_return": value,
                          "return_basis": "prior_observed_close_to_cash"}])


@pytest.mark.parametrize("engine", ["long_only", "long_short"])
def test_t_halt_5_halt_then_resumption_then_an_evidenced_disappearance_settles(engine):
    prices = walk(8, 9)
    asset = "A00" if engine == "long_only" else "A07"
    edited = halt(prices, asset, 30, 33)
    edited.iloc[50:, edited.columns.get_loc(asset)] = np.nan
    events = _event(asset, DATES[50], DATES[49], DATES[45], 0.1)
    signals = ranked(prices, [f"A{i:02d}" for i in range(8)])
    run = long_only if engine == "long_only" else long_short
    kwargs = {"top_n": 2} if engine == "long_only" else {}
    result = run(edited, signals, terminal_events=events, **kwargs)
    assert [record["permanent_id"] for record in result.terminal_event_log] == [asset]
    held = result.net_holdings if engine == "long_short" else result.holdings
    assert (held[asset].iloc[50:] == 0.0).all()
    assert len(result.halt_ledger["unmarked_halt_rows"]) == 3


@pytest.mark.parametrize("engine", ["long_only", "long_short"])
def test_t_halt_6_an_asset_unmarked_at_the_last_row_raises_unresolved_disappearance(engine):
    prices = walk(8, 10)
    asset = "A00" if engine == "long_only" else "A07"
    edited = halt(prices, asset, 70, 90)
    signals = ranked(prices, [f"A{i:02d}" for i in range(8)])
    with pytest.raises(BacktestValidationError) as refused:
        if engine == "long_only":
            long_only(edited, signals, top_n=2)
        else:
            long_short(edited, signals)
    assert refused.value.reason == "unresolved_disappearance" and refused.value.asset == asset


def _numeric_fields(result):
    names = ("equity_curve", "returns", "gross_returns", "turnover", "total_trading_costs", "cash_balance",
             "terminal_cashflows")
    holdings = ("holdings", "trade_weights", "signed_trade_weights") if hasattr(result, "holdings") else (
        "net_holdings", "long_holdings", "short_holdings", "decile_returns", "spread_returns")
    return {name: getattr(result, name) for name in names + holdings}


@pytest.mark.parametrize("engine", ["long_only", "long_short"])
def test_t_halt_7b_complete_inputs_are_byte_identical_to_raise(engine):
    prices = walk(12, 11)
    signals = pd.DataFrame(np.random.default_rng(12).normal(size=prices.shape), index=DATES, columns=prices.columns)
    events = _event("A03", DATES[60], DATES[59], DATES[50], 0.2)
    edited = prices.copy()
    edited.iloc[60:, edited.columns.get_loc("A03")] = np.nan
    run = long_only if engine == "long_only" else long_short
    kwargs = {"top_pct": 0.25} if engine == "long_only" else {}
    raised = _numeric_fields(run(edited, signals, policy="raise", terminal_events=events, **kwargs))
    halted = _numeric_fields(run(edited, signals, terminal_events=events, **kwargs))
    for name, frame in raised.items():
        assert frame.equals(halted[name]), name
    # a held asset's halt on a non-execution row falls outside the precondition: raise refuses it
    gap = halt(prices, "A00", 30, 31)
    signals_held = ranked(prices, [f"A{i:02d}" for i in range(12)])
    with pytest.raises(BacktestValidationError):
        run(gap, signals_held, policy="raise", **kwargs)
    assert run(gap, signals_held, **kwargs).halt_ledger["locked_execution_rows"] == []


@pytest.mark.parametrize("engine", ["long_only", "long_short"])
def test_t_halt_8_terminal_reference_without_a_close_refuses(engine):
    prices = walk(8, 13)
    edited = prices.copy()
    edited.iloc[49:, edited.columns.get_loc("A02")] = np.nan
    events = _event("A02", DATES[50], DATES[49], DATES[45], 0.1)
    signals = ranked(prices, [f"A{i:02d}" for i in range(8)])
    with pytest.raises(BacktestValidationError) as refused:
        if engine == "long_only":
            long_only(edited, signals, top_n=2, terminal_events=events)
        else:
            long_short(edited, signals, terminal_events=events)
    assert refused.value.reason == "terminal_reference_bar_missing"


@pytest.mark.parametrize("engine", ["long_only", "long_short"])
def test_t_halt_9_the_halt_policy_refuses_an_impact_model(engine):
    prices = walk(8, 14)
    signals = ranked(prices, [f"A{i:02d}" for i in range(8)])
    model = SquareRootImpactModel()
    with pytest.raises(BacktestValidationError) as refused:
        if engine == "long_only":
            long_only(prices, signals, top_n=2, costs=(1.0, 0.0), impact_model=model)
        else:
            long_short(prices, signals, costs=(1.0, 0.0), impact_model=model)
    assert refused.value.reason == "halt_policy_impact_model_unsupported"


# ---------------------------------------------------------------- T-CAUSAL-1..3


def _perturb(prices: pd.DataFrame, events: pd.DataFrame | None, t: int, kind: str, rng):
    """Edit only rows ``> t``: scale, a new halt, a disappearance with or without an event, delete, or append."""
    settled = set() if events is None else set(events["permanent_id"])
    candidates = [a for a in prices.columns if a not in settled]  # an evidenced asset keeps its reference close
    edited, asset = prices.copy(), candidates[int(rng.integers(len(candidates)))]
    column, n = edited.columns.get_loc(asset), len(prices)
    if kind == "scale":
        edited.iloc[t + 1:, column] *= float(rng.uniform(0.5, 1.5))
    elif kind == "halt":
        start = int(rng.integers(t + 1, n - 2))
        edited.iloc[start:min(start + int(rng.integers(1, 6)), n - 1), column] = np.nan
    elif kind in ("disappearance_with_event", "disappearance_without_event"):
        stop = int(rng.integers(t + 2, n))
        while kind == "disappearance_with_event" and not np.isfinite(edited.iloc[stop - 1, column]):
            stop = int(rng.integers(t + 2, n))  # the tooling places the settlement after an observed close (H-4)
        edited.iloc[stop:, column] = np.nan
        if kind == "disappearance_with_event":
            new = _event(asset, prices.index[stop], prices.index[stop - 1], prices.index[stop - 1], -0.3)
            events = new if events is None else pd.concat([events, new], ignore_index=True)
    elif kind == "delete":
        edited = edited.iloc[:int(rng.integers(t + 2, n + 1))]
    else:  # append
        extra = pd.bdate_range(prices.index[-1] + pd.offsets.BDay(), periods=int(rng.integers(1, 30)))
        tail = pd.DataFrame(edited.iloc[-1].to_numpy() * np.exp(np.cumsum(rng.normal(0, 0.01, (len(extra), n_cols(
            edited))), axis=0)), index=extra, columns=edited.columns)
        edited = pd.concat([edited, tail])
    return edited, events


def n_cols(frame: pd.DataFrame) -> int:
    return len(frame.columns)


def _extend_signals(signals: pd.DataFrame, index: pd.DatetimeIndex) -> pd.DataFrame:
    return signals.reindex(index).ffill()


@pytest.mark.parametrize("book", ["long_only", "long_short", "equal_weight"])
def test_t_causal_1_3_edits_after_t_leave_every_row_up_to_t_unchanged(book):
    prices = walk(12, 20)
    prices = halt(prices, "A05", 25, 28)
    base_events = _event("A09", DATES[70], DATES[69], DATES[60], 0.05)
    prices.iloc[70:, prices.columns.get_loc("A09")] = np.nan
    signals = pd.DataFrame(np.random.default_rng(21).normal(size=prices.shape), index=DATES, columns=prices.columns)
    if book == "equal_weight":
        signals = pd.DataFrame(1.0, index=DATES, columns=prices.columns)

    def run(p, events):
        s = _extend_signals(signals, p.index)
        if book == "long_short":
            result = long_short(p, s, terminal_events=events)
            return result, result.net_holdings
        result = long_only(p, s, terminal_events=events, **({"top_pct": 0.25} if book == "long_only"
                                                           else {"top_pct": 1.0}), costs=(
            (0.0, 0.0) if book == "equal_weight" else (1.0, 4.0)))
        return result, result.holdings

    base, base_held = run(prices, base_events)
    rng = np.random.default_rng(22)
    kinds = ["scale", "halt", "disappearance_with_event", "disappearance_without_event", "delete", "append"]
    compared = 0
    for draw in range(200):
        t = int(rng.integers(1, len(DATES) - 3))
        kind = kinds[draw % len(kinds)]
        edited, events = _perturb(prices, base_events, t, kind, rng)
        events = None if events is None else events[events["effective_date"].isin(edited.index)
                                                    & (events["effective_date"] <= edited.index[-1])]
        try:
            result, held = run(edited, events if events is not None and len(events) else None)
        except BacktestValidationError as refused:
            assert refused.reason == "unresolved_disappearance" and refused.date > DATES[t], (kind, t)
            continue
        rows = slice(0, t + 1)
        assert held.iloc[rows].equals(base_held.iloc[rows]), (kind, t)
        assert result.returns.iloc[rows].equals(base.returns.iloc[rows]), (kind, t)
        assert result.equity_curve.iloc[rows].equals(base.equity_curve.iloc[rows]), (kind, t)
        compared += 1
    assert compared >= 150


# ---------------------------------------------------------------- T-HAC-1


def test_t_hac_1_segment_aware_estimator():
    rng = np.random.default_rng(30)
    values = pd.Series(rng.normal(0.02, 0.1, 94))
    lags = runner.automatic_lag(len(values))
    one = segment_aware_bartlett_long_run_variance(values, ["post"] * len(values), lags)
    assert one == newey_west_long_run_variance(values, lags)
    labels = ["pre"] * 34 + ["post"] * 60
    two = segment_aware_bartlett_long_run_variance(values, labels, lags)
    residual = values.to_numpy() - values.mean()
    expected = float(np.dot(residual, residual) / 94)
    for lag in range(1, lags + 1):
        pairs = [(t, t - lag) for t in range(lag, 94) if labels[t] == labels[t - lag]]
        assert len(pairs) == 94 - lag - lag  # exactly the ``lag`` cross-segment pairs are omitted
        gamma = sum(residual[a] * residual[b] for a, b in pairs) / 94
        expected += 2.0 * (1.0 - lag / (lags + 1.0)) * gamma
    assert two == pytest.approx(expected, rel=1e-12)
    ic = pd.Series(values.to_numpy(), index=pd.date_range("2010-01-31", periods=94, freq="ME"))
    carried = runner.ic_minimum_detectable_effect(ic.iloc[:40])
    runner_lags = int(np.floor(4.0 * (40 / 100.0) ** (2.0 / 9.0)))
    lrv = newey_west_long_run_variance(ic.iloc[:40], runner_lags)
    assert carried[0] == pytest.approx(runner.Z_EFF * math.sqrt(lrv / 40), rel=1e-15)
    segmented = runner.ic_minimum_detectable_effect(ic, segments=labels, min_months=60)
    assert segmented[0] == pytest.approx(runner.Z_EFF * math.sqrt(two / 94), rel=1e-15)
    test = runner.segment_ic_test(ic, labels)
    assert test["hac_estimator"] == "segment_aware_bartlett_hac_v1" and test["hac_lags"] == lags
    assert test["hac_statistic"] == pytest.approx(float(ic.mean()) / math.sqrt(two / 94), rel=1e-12)
    single = runner.segment_ic_test(ic, ["post"] * 94)
    assert single["hac_statistic"] == pytest.approx(
        runner.return_test_statistics(ic.reset_index(drop=True), periods_per_year=12)["hac_statistic"], rel=1e-12)


# ---------------------------------------------------------------- M48B-A1-A01: a present invalid close is corrupt data


@pytest.mark.parametrize("engine", ["long_only", "long_short"])
@pytest.mark.parametrize("value", [0.0, -1.0, np.inf, -np.inf])
def test_a01_a_present_invalid_held_close_refuses_and_a_missing_close_stays_a_halt(engine, value):
    prices = walk(8, 1)
    signals = ranked(prices, [f"A{i:02d}" for i in range(8)])
    asset = "A00" if engine == "long_only" else "A07"
    run = (lambda p: long_only(p, signals, top_n=2)) if engine == "long_only" else (lambda p: long_short(p, signals))
    corrupt = prices.copy()
    corrupt.iloc[30, corrupt.columns.get_loc(asset)] = value
    with pytest.raises(BacktestValidationError) as refused:
        run(corrupt)
    assert (refused.value.reason, refused.value.date, refused.value.asset) == ("incoming_price_invalid", DATES[30], asset)
    assert run(halt(prices, asset, 30, 31)).halt_ledger["unmarked_halt_rows"] == [(DATES[30], asset)]


@pytest.mark.parametrize("engine", ["long_only", "long_short"])
def test_a01_a_present_invalid_close_on_an_unheld_target_refuses_at_execution(engine):
    prices = walk(8, 2)
    order = [f"A{i:02d}" for i in range(8)]
    later = ["A02", "A00", "A01", "A03", "A04", "A05", "A06", "A07"]  # A02 enters the long leg at R2
    signals = ranked(prices, order, after=R2 - 3, later=later)
    corrupt = prices.copy()
    corrupt.iloc[R2, corrupt.columns.get_loc("A02")] = 0.0
    with pytest.raises(BacktestValidationError) as refused:
        long_only(corrupt, signals, top_n=2) if engine == "long_only" else long_short(corrupt, signals)
    assert (refused.value.reason, refused.value.date, refused.value.asset) == ("execution_price_invalid", DATES[R2], "A02")
