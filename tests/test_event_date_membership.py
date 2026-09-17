from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_index_equal, assert_series_equal

import research.demo_v0 as demo_v0
import research.synthetic_multifactor_backtest_demo as multifactor
from research.dividend_policy import require_event_date_membership


NO_TABLE_SENTENCE = (
    "Event-level reconciliation was not performed because no independent "
    "event table was supplied."
)


@pytest.fixture(params=[demo_v0, multifactor], ids=["demo_v0", "m3_01"])
def demo(request, monkeypatch, tmp_path):
    module = request.param
    if module is demo_v0:
        config = replace(
            module.DEMO_V0_CONFIG, periods=12, asset_count=3, top_n=2,
            lookback_periods=2, skip_periods=0,
        )
        run = module.run_demo_v0
        price_config = config
    else:
        config = replace(module.FROZEN_CONFIG, periods=12, asset_count=3, top_n=2)
        run = module.run_synthetic_multifactor_backtest_demo
        price_config = module._price_config(config)
    prices = module.generate_synthetic_prices(price_config)
    monkeypatch.setattr(module, "generate_synthetic_prices", lambda config: prices)
    return module, run, prices, dict(
        config=config,
        report_path=tmp_path / "report.md",
        attempt_log_path=tmp_path / "attempts.jsonl",
    )


@pytest.mark.parametrize("event_date", [
    "2020-12-31", "2021-01-02", "2021-01-20", "2021-01-04 12:00",
])
def test_absent_event_date_refused_with_inputs_and_report_preserved(demo, event_date):
    module, run, prices, kwargs = demo
    source = prices.index.copy(deep=True)
    events = pd.DataFrame(
        {"dividend": [2.0, 3.0], "split_factor": [2.0, 4.0]},
        index=pd.DatetimeIndex([source[0], event_date], name="event_date"),
    )
    before_prices, before_events = prices.copy(deep=True), events.copy(deep=True)
    before_source = source.copy(deep=True)
    kwargs["report_path"].write_text("previous report\n")

    with pytest.raises(ValueError, match="event date absent from the declared source index"):
        run(**kwargs, event_table=events, observed_index=source)

    assert_frame_equal(prices, before_prices)
    assert_frame_equal(events, before_events)
    assert_index_equal(source, before_source)
    assert kwargs["report_path"].read_text() == "previous report\n"
    records = module.load_attempt_records(kwargs["attempt_log_path"])
    assert [record["status"] for record in records] == ["started", "failure"]
    assert "event date absent" in records[-1]["error_message"]


@pytest.mark.parametrize("empty", [False, True], ids=["dividend_and_split", "empty"])
def test_supplied_events_preserve_prices_and_all_held_returns(demo, monkeypatch, empty):
    module, run, prices, kwargs = demo
    # Repeated dates permit a dividend and split on the same source row.
    events = pd.DataFrame(
        {"dividend": [2.0, 0.0, 3.0], "split_factor": [1.0, 4.0, 0.5]},
        index=pd.DatetimeIndex([prices.index[0], prices.index[0], prices.index[-1]]),
    )
    if empty:
        events = events.iloc[:0]
    before_events = events.copy(deep=True)
    before_prices = prices.copy(deep=True)
    backtest = module.run_long_only_backtest
    supplied = []

    def capture(prices, *args, **kwargs):
        supplied.append(prices.copy(deep=True))
        return backtest(prices, *args, **kwargs)

    monkeypatch.setattr(module, "run_long_only_backtest", capture)
    baseline = run(**kwargs)
    assert NO_TABLE_SENTENCE in kwargs["report_path"].read_text()
    result = run(**kwargs, event_table=events, observed_index=prices.index.copy())
    if module is multifactor:
        baseline, result = baseline.backtest_result, result.backtest_result
    assert len(supplied) == 2
    for panel in supplied:
        assert_frame_equal(panel, before_prices)
    assert_frame_equal(prices, before_prices)
    assert_frame_equal(events, before_events)
    assert_frame_equal(result.holdings, baseline.holdings)
    for field in ("returns", "gross_returns", "equity_curve", "turnover", "total_trading_costs"):
        assert_series_equal(getattr(result, field), getattr(baseline, field))
    report = kwargs["report_path"].read_text()
    assert "Supplied event dates passed membership in the declared source index." in report
    assert "Full economic dividend/split reconciliation remains deferred." in report
    assert NO_TABLE_SENTENCE not in report


@pytest.mark.parametrize("events, error, message", [
    ([], TypeError, "pandas DataFrame"),
    (pd.DataFrame(index=["2021-01-01"]), TypeError, "DatetimeIndex"),
    (pd.DataFrame(index=pd.DatetimeIndex([pd.NaT])), ValueError, "missing event dates"),
])
def test_malformed_event_dates_refused(demo, events, error, message):
    module, run, prices, kwargs = demo
    before = prices.copy(deep=True)
    with pytest.raises(error, match=message):
        run(**kwargs, event_table=events)
    assert_frame_equal(prices, before)
    assert module.load_attempt_records(kwargs["attempt_log_path"])[-1]["status"] == "failure"


def test_event_membership_uses_declared_source_without_calendar_inference():
    source = pd.DatetimeIndex(["2021-01-02", "2021-01-04", "2021-01-06"], name="source")
    require_event_date_membership(None, observed_index=source)
    require_event_date_membership(pd.DataFrame(index=source), observed_index=source)
    with pytest.raises(ValueError, match="event date absent"):
        require_event_date_membership(
            pd.DataFrame(index=pd.DatetimeIndex(["2021-01-05"])), observed_index=source,
        )


@pytest.mark.parametrize("module", [demo_v0, multifactor], ids=["demo_v0", "m3_01"])
def test_official_reports_disclose_no_independent_event_table(module, tmp_path):
    run = (module.run_demo_v0 if module is demo_v0
           else module.run_synthetic_multifactor_backtest_demo)
    report = tmp_path / "report.md"
    run(report_path=report, attempt_log_path=tmp_path / "attempts.jsonl")
    assert NO_TABLE_SENTENCE in report.read_text()
    committed = Path(__file__).resolve().parents[1] / "reports" / module.DEFAULT_REPORT_PATH.name
    assert NO_TABLE_SENTENCE in committed.read_text()
