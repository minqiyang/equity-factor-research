from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_index_equal

import research.demo_v0 as demo_v0
import research.synthetic_multifactor_backtest_demo as multifactor
from research.source_row_lag import report_calendar_day_spans


@pytest.mark.parametrize(
    "timestamps, count, maximum",
    [
        (["2021-01-04", "2021-01-06", "2021-01-08"], 2, 2),
        (["2021-01-04", "2021-01-05", "2021-01-06"], 0, 1),
        (["2021-01-08", "2021-01-11", "2021-01-12"], 1, 3),
        (["2021-01-04 23:00", "2021-01-06 01:00"], 1, 2),
        (["2021-01-04 01:00", "2021-01-04 23:00"], 0, 0),
        (["2021-01-04"], 0, 0),
        ([], 0, 0),
    ],
)
def test_span_counts_preserve_observed_index(timestamps, count, maximum) -> None:
    index = pd.DatetimeIndex(timestamps, name="observed")
    before = index.copy(deep=True)
    before_bytes = index.asi8.tobytes()

    result = report_calendar_day_spans(index)

    assert result.pairs_over_one_day == count
    assert result.max_span_days == maximum
    assert_index_equal(index, before)
    assert index.asi8.tobytes() == before_bytes


def _fixture_run(module, index, monkeypatch, tmp_path):
    prices = pd.DataFrame(
        {"ASSET_01": 100.0 + np.arange(len(index)),
         "ASSET_02": 100.0 - np.arange(len(index))},
        index=index,
    )
    monkeypatch.setattr(module, "generate_synthetic_prices", lambda config: prices)
    if module is demo_v0:
        config = replace(
            demo_v0.DEMO_V0_CONFIG, periods=len(index), asset_count=2,
            top_n=1, lookback_periods=1, skip_periods=0,
        )
        run = module.run_demo_v0
    else:
        config = replace(module.FROZEN_CONFIG, periods=len(index), asset_count=2, top_n=1)
        generate = module.generate_synthetic_factor_panels

        def factors(config):
            panels = generate(config)
            for panel in panels.values():
                panel.index = index.copy()
            return panels

        monkeypatch.setattr(module, "generate_synthetic_factor_panels", factors)
        run = module.run_synthetic_multifactor_backtest_demo
    return prices, run, dict(
        config=config,
        report_path=tmp_path / "report.md",
        attempt_log_path=tmp_path / "attempts.jsonl",
    )


@pytest.mark.parametrize("module", [demo_v0, multifactor], ids=["demo_v0", "m3_01"])
@pytest.mark.parametrize(
    "timestamps, count, maximum",
    [
        (["2021-01-04", "2021-01-06", "2021-01-08"], 2, 2),
        (["2021-01-04", "2021-01-05", "2021-01-06"], 0, 1),
        (["2021-01-08", "2021-01-11", "2021-01-12"], 1, 3),
    ],
)
def test_demo_reports_spans_and_backtests_every_supplied_bar(
    module, timestamps, count, maximum, monkeypatch, tmp_path: Path,
) -> None:
    index = pd.DatetimeIndex(timestamps)
    if module is demo_v0:
        # Supply the warm-up anchor required before two measured returns.
        index = index.insert(0, index[0] - pd.Timedelta(days=1))
    prices, run, kwargs = _fixture_run(module, index, monkeypatch, tmp_path)
    before = prices.copy(deep=True)
    before_bytes = prices.index.asi8.tobytes()
    backtest = module.run_long_only_backtest
    supplied = []

    def capture(prices, *args, **kwargs):
        supplied.append(prices.copy(deep=True))
        return backtest(prices, *args, **kwargs)

    monkeypatch.setattr(module, "run_long_only_backtest", capture)
    if count == 0:
        kwargs["observed_index"] = prices.index.copy()
    run(**kwargs)

    assert len(supplied) == 1
    assert_frame_equal(supplied[0], before)
    assert_frame_equal(prices, before)
    assert prices.index.asi8.tobytes() == before_bytes
    report = kwargs["report_path"].read_text()
    assert f"Adjacent timestamp pairs with calendar-day span > 1: `{count}`" in report
    assert f"Max adjacent calendar-day span: `{maximum}` days" in report
    assert "Session and holiday status remains unverified" in report
    assert "declared source index" in report
    assert "Detecting invented sessions remains later" not in report


@pytest.mark.parametrize("module", [demo_v0, multifactor], ids=["demo_v0", "m3_01"])
def test_demo_refuses_invented_session_and_preserves_input(
    module, monkeypatch, tmp_path: Path,
) -> None:
    observed = pd.DatetimeIndex(["2021-01-04", "2021-01-06", "2021-01-08"])
    planted = observed.insert(1, pd.Timestamp("2021-01-05"))
    prices, run, kwargs = _fixture_run(module, planted, monkeypatch, tmp_path)
    before = prices.copy(deep=True)
    source_bytes = observed.asi8.tobytes()
    panel_bytes = prices.index.asi8.tobytes()
    kwargs["report_path"].write_text("previous report\n")

    with pytest.raises(ValueError, match="silently inserted 1 source rows"):
        run(**kwargs, observed_index=observed)

    assert_frame_equal(prices, before)
    assert prices.index.asi8.tobytes() == panel_bytes
    assert observed.asi8.tobytes() == source_bytes
    assert kwargs["report_path"].read_text() == "previous report\n"
    records = module.load_attempt_records(kwargs["attempt_log_path"])
    assert [record["status"] for record in records] == ["started", "failure"]
    assert "silently inserted 1 source rows" in str(records[-1])
