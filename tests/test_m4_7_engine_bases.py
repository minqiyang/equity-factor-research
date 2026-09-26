"""M4.7 stage a-0 engine oracles: consideration bases, v2 contract, and mask wrapper."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backtest.long_short import run_long_short_backtest
from backtest.portfolio import (
    ACCEPTED_TERMINAL_BASES,
    TERMINAL_SETTLEMENT_CONTRACT,
    BacktestValidationError,
    _prepare_terminal_events,
    _resolve_pit_universe,
    capture_backtest_source_provenance,
    resolve_pit_universe_mask,
    run_long_only_backtest,
)
from data.constituent_table import build_pit_membership_mask
from research.m4_7_common_support import signal_eligibility


CASH = "prior_observed_close_to_cash"
STOCK = "prior_observed_close_to_stock_consideration_valued_at_completion_date_close"
MIXED = "prior_observed_close_to_mixed_consideration_valued_at_completion_date_close"
V2 = "prior_observed_close_to_consideration_at_completion_date_row_v2"


def panels():
    dates = pd.bdate_range("2024-01-01", periods=12, name="date")
    prices = pd.DataFrame({"SEC_A": 10.0, "SEC_B": 20.0}, index=dates)
    signals = pd.DataFrame({"SEC_A": 2.0, "SEC_B": 1.0}, index=dates)
    return dates, prices, signals


def intervals(dates, assets=("SEC_A", "SEC_B"), starts=None):
    starts = starts or [dates[0]] * len(assets)
    return pd.DataFrame({
        "symbol": list(assets), "permanent_id": list(assets),
        "start_date": starts, "end_date": [pd.NaT] * len(assets),
        "start_known_at": starts, "end_known_at": [pd.NaT] * len(assets),
    })


def events(dates, rows):
    """rows: (event_id, asset, settlement_position, known_position, return, basis)."""
    return pd.DataFrame([
        {"event_id": event_id, "permanent_id": asset, "effective_date": dates[position],
         "known_at": dates[known], "reference_date": dates[position - 1],
         "terminal_return": value, "return_basis": basis}
        for event_id, asset, position, known, value, basis in rows
    ], columns=["event_id", "permanent_id", "effective_date", "known_at",
                "reference_date", "terminal_return", "return_basis"])


def run(kind, prices, signals, **kwargs):
    settings = dict(evaluation_start=prices.index[0], evaluation_end=prices.index[-1],
                    rebalance_frequency="W-FRI", initial_capital=100.0)
    settings.update(kwargs)
    if kind == "lo":
        settings.setdefault("top_n", 1)
        return run_long_only_backtest(
            prices, signals, source_provenance=capture_backtest_source_provenance(prices, signals), **settings,
        )
    return run_long_short_backtest(prices, signals, quantiles=2, **settings)


def holdings(kind, book):
    return book.holdings if kind == "lo" else book.net_holdings


def test_accepted_bases_and_contract_are_frozen():
    assert ACCEPTED_TERMINAL_BASES == frozenset({CASH, STOCK, MIXED})
    assert TERMINAL_SETTLEMENT_CONTRACT == V2


@pytest.mark.parametrize("case", ["empty", "cash", "stock"])
def test_t_eng_1_wrapper_equals_engine_resolution(case):
    dates = pd.bdate_range("2024-01-01", periods=30, name="date")
    assets = ["SEC_A", "SEC_B", "SEC_C"]
    table = intervals(dates, assets, starts=[dates[0], dates[7], dates[0]])
    rows = {"empty": [], "cash": [("e1", "SEC_A", 12, 10, -0.2, CASH)],
            "stock": [("e1", "SEC_C", 20, 15, 0.1, STOCK)]}[case]
    table_events = events(dates, rows)
    wrapped = resolve_pit_universe_mask(table, table_events, dates, assets, signal_lag_periods=1)
    engine = _resolve_pit_universe(
        constituent_intervals=table, universe_mask=None, dates=dates, assets=pd.Index(assets),
        signal_lag_periods=1, terminal_events=_prepare_terminal_events(table_events, dates, pd.Index(assets)),
    )
    pd.testing.assert_frame_equal(wrapped, engine)
    if case == "empty":
        pd.testing.assert_frame_equal(wrapped, build_pit_membership_mask(table, dates, assets, signal_lag_periods=1))
        pd.testing.assert_frame_equal(
            resolve_pit_universe_mask(table, None, dates, assets),
            build_pit_membership_mask(table, dates, assets, signal_lag_periods=1),
        )
    else:
        asset = rows[0][1]
        assert not wrapped.loc[dates[rows[0][2]]:, asset].any()
        assert wrapped.loc[dates[rows[0][2] - 1], asset]


def test_t_eng_1_wrapper_refuses_unknown_basis():
    dates = pd.bdate_range("2024-01-01", periods=30, name="date")
    with pytest.raises(BacktestValidationError, match="terminal_events_invalid"):
        resolve_pit_universe_mask(
            intervals(dates), events(dates, [("e1", "SEC_A", 12, 10, 0.1, "stock")]), dates, ["SEC_A", "SEC_B"],
        )


@pytest.mark.parametrize("kind", ["lo", "ls"])
@pytest.mark.parametrize("basis", [CASH, STOCK, MIXED])
def test_t_eng_2_engines_accept_each_label_and_count_it(kind, basis):
    dates, prices, signals = panels()
    prices.loc[dates[5]:, "SEC_A"] = np.nan
    book = run(kind, prices, signals, terminal_events=events(dates, [("e1", "SEC_A", 5, 4, 0.2, basis)]))
    assert book.assumptions["terminal_settlement_contract"] == V2
    assert book.assumptions["terminal_basis_counts"] == {CASH: int(basis == CASH), STOCK: int(basis == STOCK),
                                                         MIXED: int(basis == MIXED)}


@pytest.mark.parametrize("kind", ["lo", "ls"])
@pytest.mark.parametrize("basis", ["prior_observed_close_to_stock", "", CASH + " ", "PRIOR_OBSERVED_CLOSE_TO_CASH"])
def test_t_eng_2_engines_refuse_unknown_label(kind, basis):
    dates, prices, signals = panels()
    prices.loc[dates[5]:, "SEC_A"] = np.nan
    with pytest.raises(BacktestValidationError, match="terminal_events_invalid"):
        run(kind, prices, signals, terminal_events=events(dates, [("e1", "SEC_A", 5, 4, 0.2, basis)]))


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_t_eng_2_counts_multiple_events_and_event_free_call_omits_keys(kind):
    dates = pd.bdate_range("2024-01-01", periods=12, name="date")
    prices = pd.DataFrame({"SEC_A": 10.0, "SEC_B": 20.0, "SEC_C": 30.0, "SEC_D": 40.0}, index=dates)
    signals = pd.DataFrame({"SEC_A": 4.0, "SEC_B": 3.0, "SEC_C": 2.0, "SEC_D": 1.0}, index=dates)
    prices.loc[dates[5]:, ["SEC_A", "SEC_C"]] = np.nan
    prices.loc[dates[8]:, "SEC_D"] = np.nan
    table = events(dates, [("e1", "SEC_A", 5, 4, 0.1, STOCK), ("e2", "SEC_C", 5, 4, 0.0, STOCK),
                           ("e3", "SEC_D", 8, 6, -1.0, CASH)])
    book = run(kind, prices, signals, terminal_events=table, **({"top_n": 2} if kind == "lo" else {}))
    assert book.assumptions["terminal_basis_counts"] == {CASH: 1, STOCK: 2, MIXED: 0}
    assert book.assumptions["terminal_settlement_contract"] == V2
    free = run(kind, prices.ffill(), signals)
    assert "terminal_settlement_contract" not in free.assumptions
    assert "terminal_basis_counts" not in free.assumptions


def test_t_eng_3_timing_contract_names_the_consideration_bases():
    text = Path(__file__).resolve().parents[1].joinpath("docs/signal_execution_timing_contract.md").read_text(
        encoding="utf-8")
    m44 = text[text.index("## M4.4 Optional PIT Membership"):text.index("## M4.5 Optional Daily Market Impact")]
    assert "### M4.7 consideration bases" in m44
    for phrase in (CASH, STOCK, MIXED, V2, "valuation row `V = row(completion_date)`",
                   "Settlement is unchanged: the engine credits cash on `S`", "terminal_basis_counts",
                   "resolve_pit_universe_mask"):
        assert phrase in m44, phrase


@pytest.mark.parametrize("kind", ["lo", "ls"])
@pytest.mark.parametrize(("basis", "value"), [(STOCK, 0.5 * 100 / 45 - 1), (MIXED, (10 + 0.25 * 80) / 25 - 1)])
def test_t_term_1_2_stock_and_mixed_settlement_hand_oracle(kind, basis, value):
    dates, prices, signals = panels()
    prices.loc[dates[5]:, "SEC_A"] = np.nan
    book = run(kind, prices, signals, terminal_events=events(dates, [("e1", "SEC_A", 5, 4, value, basis)]))
    weight = 1.0 if kind == "lo" else 0.5
    assert book.terminal_cashflows.loc[dates[5], "SEC_A"] == pytest.approx(100 * weight * (1 + value), abs=1e-12)
    assert book.equity_curve.loc[dates[5]] == pytest.approx(100 * (1 + weight * value), abs=1e-12)
    assert holdings(kind, book).loc[dates[5]:, "SEC_A"].eq(0).all()
    assert book.turnover.loc[dates[5]] == 0
    assert book.terminal_event_log[0]["return_basis"] == basis
    if basis == STOCK:
        assert value == pytest.approx(0.11111111111111, abs=1e-12)
    else:
        assert value == pytest.approx(0.2, abs=1e-12)


@pytest.mark.parametrize("kind", ["lo", "ls"])
def test_t_term_2_evidenced_worthless_records_zero_proceeds(kind):
    dates, prices, signals = panels()
    prices.loc[dates[5]:, "SEC_A"] = np.nan
    extra = {"max_position_weight": 0.5} if kind == "lo" else {}
    book = run(kind, prices, signals, terminal_events=events(dates, [("e1", "SEC_A", 5, 4, -1.0, CASH)]), **extra)
    assert book.terminal_cashflows.loc[dates[5], "SEC_A"] == 0.0
    assert book.terminal_event_log[0]["cashflow"] == 0.0
    assert holdings(kind, book).loc[dates[5]:, "SEC_A"].eq(0).all()


@pytest.mark.parametrize("kind", ["lo", "ls"])
@pytest.mark.parametrize("basis", [STOCK, MIXED])
def test_t_term_4_known_at_settlement_row_collides_with_frozen_target(kind, basis):
    dates, prices, signals = panels()
    prices.loc[dates[5]:, "SEC_A"] = np.nan
    late = events(dates, [("e1", "SEC_A", 5, 5, 0.1, basis)])
    with pytest.raises(BacktestValidationError, match="terminal_target_invalid"):
        run(kind, prices, signals, terminal_events=late, rebalance_frequency="D")
    on_time = events(dates, [("e1", "SEC_A", 5, 4, 0.1, basis)])
    book = run(kind, prices, signals, terminal_events=on_time, rebalance_frequency="D")
    assert holdings(kind, book).loc[dates[5]:, "SEC_A"].eq(0).all()


def test_t_uni_11_signal_eligibility_properties():
    dates = pd.bdate_range("2023-01-02", periods=260, name="date")
    assets = ["MEMBER", "JOINER", "GAPPY", "SETTLED"]
    table = intervals(dates, assets, starts=[dates[0], dates[200], dates[0], dates[0]])
    settle = 150
    engine_events = events(dates, [("e1", "SETTLED", settle, 140, 0.05, STOCK)])
    mask = resolve_pit_universe_mask(table, engine_events, dates, assets, signal_lag_periods=1)
    bars = pd.DataFrame(True, index=dates, columns=assets)
    bars.loc[dates[settle]:, "SETTLED"] = False
    bars.iloc[120, assets.index("GAPPY")] = False

    everywhere = signal_eligibility(mask, pd.DataFrame(True, index=dates, columns=assets))
    pd.testing.assert_frame_equal(everywhere, mask.shift(-1, fill_value=False))
    assert not everywhere.iloc[-1].any()

    s_mask = signal_eligibility(mask, bars)
    assert not s_mask["JOINER"].iloc[:200].any()
    assert s_mask["JOINER"].iloc[200:-1].all()
    assert not s_mask["GAPPY"].iloc[120]
    assert s_mask["GAPPY"].iloc[119] and s_mask["GAPPY"].iloc[121]
    assert not s_mask["SETTLED"].iloc[settle - 1]
    assert s_mask["SETTLED"].iloc[settle - 2]
    assert not mask["SETTLED"].iloc[settle]
