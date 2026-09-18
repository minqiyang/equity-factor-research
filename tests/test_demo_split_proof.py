"""Consume the immutable split golden through both synthetic demo pipelines."""

from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_index_equal, assert_series_equal

import research.demo_v0 as demo_v0
import research.synthetic_multifactor_backtest_demo as multifactor


GOLDEN_PATH = Path(__file__).parent / "fixtures/campaign_runner_v1/split_corporate_action.json"
FRAME_FIELDS = ("holdings", "signed_trade_weights", "trade_weights")
SERIES_FIELDS = (
    "gross_returns", "returns", "turnover", "transaction_costs", "slippage_costs",
    "volume_aware_slippage_costs", "total_trading_costs", "equity_curve",
    "benchmark_returns", "benchmark_equity_curve",
)


@pytest.fixture(params=[demo_v0, multifactor], ids=["demo_v0", "m3_01"])
def consumer(request, monkeypatch, tmp_path):
    module = request.param
    golden_bytes = GOLDEN_PATH.read_bytes()
    golden = json.loads(golden_bytes)
    inputs = golden["inputs"]
    # Four warm-up/deployment rows precede the golden's April 1-2 interval.
    dates = pd.bdate_range("2026-03-26", "2026-04-06", name="observed_date")
    prices = pd.DataFrame(
        {asset: row["start_anchor"] for asset, row in inputs["adjusted"].items()},
        index=dates,
    )
    event_date = pd.Timestamp(inputs["session_date"])
    for asset, row in inputs["adjusted"].items():
        prices.loc[event_date:, asset] = row["end_anchor"]
        assert dates[dates.get_loc(event_date) - 1] == pd.Timestamp(
            row["anchors"][0]["session_date"]
        )
    frozen = deepcopy(asdict(
        module.DEMO_V0_CONFIG if module is demo_v0 else module.FROZEN_CONFIG
    ))
    overrides = dict(
        periods=len(prices), asset_count=2, top_n=2, start_date=str(dates[0].date()),
        rebalance_frequency="D", transaction_cost_bps=inputs["transaction_cost_bps"],
        slippage_bps=0.0,
    )
    if module is demo_v0:
        config = replace(module.DEMO_V0_CONFIG, lookback_periods=2, skip_periods=0,
                         **overrides)
        run = module.run_demo_v0
    else:
        config = replace(module.FROZEN_CONFIG, **overrides)
        run = module.run_synthetic_multifactor_backtest_demo
        # Select both assets while exercising the actual preprocessing/combine path.
        factors = {
            name: pd.DataFrame({"T000": 2.0, "T001": 1.0}, index=dates)
            for name in module.FACTOR_NAMES
        }
        monkeypatch.setattr(module, "generate_synthetic_factor_panels", lambda config: factors)
    monkeypatch.setattr(module, "generate_synthetic_prices", lambda config: prices)
    supplied = []
    backtest = module.run_long_only_backtest

    def capture(prices, *args, **kwargs):
        supplied.append(prices.copy(deep=True))
        return backtest(prices, *args, **kwargs)

    monkeypatch.setattr(module, "run_long_only_backtest", capture)
    yield module, run, prices, golden, supplied, dict(
        config=config, report_path=tmp_path / "report.md",
        attempt_log_path=tmp_path / "attempts.jsonl",
    )
    assert GOLDEN_PATH.read_bytes() == golden_bytes
    assert asdict(module.DEMO_V0_CONFIG if module is demo_v0 else module.FROZEN_CONFIG) == frozen


def _backtest(result):
    return result.backtest_result if hasattr(result, "backtest_result") else result


@pytest.mark.parametrize("raw", [False, True], ids=["adjusted", "raw_contamination"])
@pytest.mark.parametrize("event_kind", ["split", "empty", "repeated"])
def test_split_economics_and_metadata_equivalence(consumer, raw, event_kind):
    module, run, prices, golden, supplied, kwargs = consumer
    inputs, expected, forbidden = golden["inputs"], golden["expected"], golden["forbidden"]
    event_date = pd.Timestamp(inputs["session_date"])
    previous_date = prices.index[prices.index.get_loc(event_date) - 1]
    if raw:
        for asset, held_return in forbidden["raw_held_returns"].items():
            # The golden's raw move implies 100 -> 50 for T000; T001 stays 100.
            prices.loc[prices.index < event_date, asset] = (
                inputs["adjusted"][asset]["end_anchor"] / (1.0 + held_return)
            )
    events = pd.DataFrame(
        {"split_factor": [2.0]}, index=pd.DatetimeIndex([event_date], name="event_date")
    )
    if event_kind == "empty":
        events = events.iloc[:0]
    elif event_kind == "repeated":
        events = pd.concat([events, events])
    source = prices.index.copy(deep=True)
    before_prices, before_events, before_source = (
        prices.copy(deep=True), events.copy(deep=True), source.copy(deep=True)
    )
    baseline = _backtest(run(**kwargs, observed_index=source))
    prior_log = kwargs["attempt_log_path"].read_bytes()
    result = _backtest(run(**kwargs, observed_index=source, event_table=events))

    assert len(supplied) == 2
    for panel in [prices, *supplied]:
        assert_frame_equal(panel, before_prices, check_exact=True)
    assert_frame_equal(events, before_events, check_exact=True)
    assert_index_equal(source, before_source, exact=True)
    for field in FRAME_FIELDS:
        assert_frame_equal(getattr(result, field), getattr(baseline, field), check_exact=True)
    for field in SERIES_FIELDS:
        assert_series_equal(getattr(result, field), getattr(baseline, field), check_exact=True)
    assert result.timing_ledger == baseline.timing_ledger

    tolerance = dict(rel=expected["rel_tol"], abs=expected["abs_tol"])
    # Initial cash deployment occurs strictly before the event's held interval.
    deployment = result.turnover[result.turnover > 0].index[0]
    assert deployment < previous_date < event_date
    assert result.turnover.loc[deployment] == pytest.approx(1.0, **tolerance)
    initial_cost = inputs["transaction_cost_bps"] / 10_000.0
    assert result.total_trading_costs.loc[deployment] == pytest.approx(initial_cost, **tolerance)
    assert result.gross_returns.loc[deployment] == pytest.approx(0.0, **tolerance)
    assert result.returns.loc[deployment] == pytest.approx(-initial_cost, **tolerance)
    assert result.holdings.loc[previous_date].to_dict() == pytest.approx(
        inputs["initial_weights"], **tolerance
    )
    assert result.holdings.loc[event_date].to_dict() == pytest.approx(
        inputs["reset_weights"], **tolerance
    )
    ledger = next(row for row in result.timing_ledger if row.ledger_date == event_date)
    assert ledger.signal_source_date == previous_date

    held_returns = (prices.loc[event_date] / prices.loc[previous_date] - 1).to_dict()
    assert held_returns == pytest.approx(
        forbidden["raw_held_returns"] if raw else expected["adjusted_held_returns"],
        **tolerance,
    )
    # Public post-trade weights minus signed trades recover pre-trade drift.
    drift = result.holdings.loc[event_date] - result.signed_trade_weights.loc[event_date]
    values = {
        "gross_return": result.gross_returns.loc[event_date],
        "drifted_weights": drift.to_dict(),
        "turnover": result.turnover.loc[event_date],
        "cost_impact": result.total_trading_costs.loc[event_date],
    }
    for key, value in values.items():
        oracle = forbidden[f"raw_{key}"] if raw else expected[key]
        assert value == pytest.approx(oracle, **tolerance), key
        if raw:
            # Every adjusted economics assertion detects the raw contamination.
            with pytest.raises(AssertionError):
                assert value == pytest.approx(expected[key], **tolerance), key
    assert result.returns.loc[event_date] == pytest.approx(
        (forbidden["raw_gross_return"] - forbidden["raw_cost_impact"])
        if raw else expected["gross_return"] - expected["cost_impact"], **tolerance
    )
    records = module.load_attempt_records(kwargs["attempt_log_path"])
    assert kwargs["attempt_log_path"].read_bytes().startswith(prior_log)
    assert [row["status"] for row in records] == ["started", "success"] * 2
    assert [row["attempt_id"] for row in records] == [1, 1, 2, 2]
    # Persist the oracle comparison beside each test's retained diagnostic attempts.
    (kwargs["report_path"].parent / "split_evidence.json").write_text(json.dumps({
        "golden_sha256": hashlib.sha256(GOLDEN_PATH.read_bytes()).hexdigest(),
        "case": "raw_contamination" if raw else "adjusted",
        "event_metadata": event_kind, "initial_cost": initial_cost,
        "event_date": str(event_date), "observed": values,
        "event_net_return": result.returns.loc[event_date],
    }, indent=2, sort_keys=True) + "\n")


@pytest.mark.parametrize("failure, error, message", [
    ("absent", ValueError, "event date absent from the declared source index"),
    ("malformed", TypeError, "DatetimeIndex"),
    ("missing", ValueError, "missing event dates"),
    ("overlay", ValueError, "cash_dividends overlay"),
])
def test_split_refusal_preserves_success_and_inputs(consumer, failure, error, message):
    module, run, prices, golden, supplied, kwargs = consumer
    run(**kwargs)
    prior_report = kwargs["report_path"].read_bytes()
    prior_log = kwargs["attempt_log_path"].read_bytes()
    source = prices.index.copy(deep=True)
    index = {
        "absent": pd.DatetimeIndex(["2026-04-02 12:00"]),
        "malformed": pd.Index([golden["inputs"]["session_date"]]),
        "missing": pd.DatetimeIndex([pd.NaT]),
        "overlay": pd.DatetimeIndex([golden["inputs"]["session_date"]]),
    }[failure]
    events = pd.DataFrame({"split_factor": [2.0]}, index=index)
    before_prices, before_events, before_source = (
        prices.copy(deep=True), events.copy(deep=True), source.copy(deep=True)
    )
    with pytest.raises(error, match=message):
        run(**kwargs, event_table=events, observed_index=source,
            **({"cash_dividends": 0.0} if failure == "overlay" else {}))
    assert len(supplied) == 1
    assert_frame_equal(prices, before_prices, check_exact=True)
    assert_frame_equal(events, before_events, check_exact=True)
    assert_index_equal(source, before_source, exact=True)
    assert kwargs["report_path"].read_bytes() == prior_report
    assert kwargs["attempt_log_path"].read_bytes().startswith(prior_log)
    records = module.load_attempt_records(kwargs["attempt_log_path"])
    assert [row["status"] for row in records] == ["started", "success", "started", "failure"]
    assert [row["attempt_id"] for row in records] == [1, 1, 2, 2]
    assert message in records[-1]["error_message"]
    assert records[-1]["error_type"] == error.__name__
    assert records[-1]["metrics"] == {}
