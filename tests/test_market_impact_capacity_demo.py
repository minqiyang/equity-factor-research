"""Capacity evidence parity, declared-grid retention, and interruption durability."""

import json

import numpy as np
import pytest

from backtest.market_impact import MarketImpactValidationError
from research import market_impact_capacity_demo as demo


def evaluate(**kwargs):
    prices, signals, volumes = demo.synthetic_inputs("hand_panel")
    settings = dict(
        scope="hand_panel",
        evaluation_start=prices.index[3],
        evaluation_end=prices.index[-1],
        price_basis="raw",
        volume_basis="raw",
        lookback=2,
        aum_tiers=(1e6, 1e7),
    )
    settings.update(kwargs)
    return demo.evaluate_capacity(prices, signals, volumes, **settings)


def test_small_grid_retains_refusals_negative_results_and_path_totals(tmp_path):
    attempts = tmp_path / "attempts.jsonl"
    cases = evaluate(attempt_path=attempts)
    assert len(cases) == 16
    assert {c["status"] for c in cases} == {"success", "refused"}
    assert any(c.get("net_return", 0) < 0 for c in cases)
    for case in cases:
        if case["status"] == "success":
            assert case["slippage_dollars"] == pytest.approx(
                sum(row["slippage_dollars"] for row in case["path"])
            )
            assert case["traded_notional"] == pytest.approx(
                sum(row["absolute_traded_dollars"] for row in case["path"])
            )
            assert case["summed_turnover"] == pytest.approx(
                sum(row["turnover"] for row in case["path"])
            )
            assert case["net_return"] == pytest.approx(
                case["path"][-1]["equity"] / case["aum"] - 1
            )
            assert case["benchmark_excess_return"] == pytest.approx(
                case["net_return"] - case["benchmark_return"]
            )
    records = [json.loads(line) for line in attempts.read_text().splitlines()]
    assert len(records) == 32
    assert all(
        records[i]["status"] == "started"
        and records[i]["attempt_id"] == records[i + 1]["attempt_id"]
        for i in range(0, 32, 2)
    )
    evaluate(attempt_path=attempts)
    assert len(attempts.read_text().splitlines()) == 64


def test_complete_demo_markdown_json_parity(tmp_path):
    path = tmp_path / "capacity.md"
    result = demo.run_market_impact_capacity_demo(report_path=path, aum_tiers=(1e6,))
    assert path.read_text() == demo.render_report(result)
    payload = json.loads(path.with_suffix(".json").read_text())
    assert payload["metrics"]["cases"] == result["cases"]
    assert payload["diagnostics"]["capacity_brackets"] == result["capacity_brackets"]
    assert len(result["cases"]) == 16
    assert "empirical strategy capacity remains unmeasured" in path.read_text()
    assert "zero positive-to-nonpositive brackets" in path.read_text()


def test_short_books_report_sharpe_as_unavailable():
    """Annualizing ten daily returns produced Sharpe values near 25 (OPUS-16)."""
    hand = [c for c in evaluate(modes=("fixed_control",)) if c["status"] == "success"]
    assert hand
    for case in hand:
        assert case["measured_returns"] < demo.MIN_SHARPE_OBSERVATIONS
        assert case["net_sharpe"] is None

    prices, signals, volumes = demo.synthetic_inputs("synthetic_cohort")
    cohort = demo.evaluate_capacity(
        prices,
        signals,
        volumes,
        scope="synthetic_cohort",
        evaluation_start=prices.index[21],
        evaluation_end=prices.index[-1],
        price_basis="raw",
        volume_basis="raw",
        aum_tiers=(1e6,),
        modes=("fixed_control",),
    )
    assert cohort and all(
        c["measured_returns"] >= demo.MIN_SHARPE_OBSERVATIONS
        and np.isfinite(c["net_sharpe"])
        for c in cohort
    )


def test_changing_price_cohort_throttle_remains_long_only():
    prices, signals, volumes = demo.synthetic_inputs("synthetic_cohort")
    cases = demo.evaluate_capacity(
        prices,
        signals,
        volumes,
        scope="synthetic_cohort",
        evaluation_start=prices.index[21],
        evaluation_end=prices.index[-1],
        price_basis="raw",
        volume_basis="raw",
        lookback=20,
        aum_tiers=(1e6, 1e7),
        engines=("long_only",),
        modes=("throttle",),
    )
    assert all(case["status"] == "success" for case in cases)
    assert all(case["final_net_exposure"] >= 0 for case in cases)


def test_brackets_preserve_multiple_crossings_and_refused_adjacency():
    common = dict(scope="fixture", engine="long_only", mode="penalize")
    cases = [
        {**common, "aum": float(i + 1), "benchmark_excess_return": value}
        for i, value in enumerate([0.1, -0.1, 0.2, None, -0.3, 0.1, 0.0])
    ]
    brackets = demo.capacity_brackets(cases)
    assert [c["status"] for c in brackets] == [
        "positive_to_nonpositive",
        "nonpositive_to_positive",
        "unavailable",
        "unavailable",
        "nonpositive_to_positive",
        "positive_to_nonpositive",
    ]


@pytest.mark.parametrize(
    "failure,status",
    [
        (RuntimeError("simulated"), "failure"),
        (MarketImpactValidationError("impact_adv_invalid", "simulated"), "refused"),
        (KeyboardInterrupt(), "interrupted"),
    ],
)
def test_attempt_outcomes_are_durable_including_interruption(
    tmp_path, monkeypatch, failure, status
):
    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(demo, "run_long_only_backtest", fail)
    attempts = tmp_path / "attempts.jsonl"
    if status == "interrupted":
        with pytest.raises(KeyboardInterrupt):
            evaluate(attempt_path=attempts, engines=("long_only",), modes=("throttle",))
    else:
        cases = evaluate(
            attempt_path=attempts, engines=("long_only",), modes=("throttle",)
        )
        assert len(cases) == 2
        assert all(case["status"] == status for case in cases)
    records = [json.loads(line) for line in attempts.read_text().splitlines()]
    assert records[0]["status"] == "started"
    assert records[1]["status"] == status
    assert records[0]["attempt_id"] == records[1]["attempt_id"]


def test_unexpected_failure_writes_report_before_raising(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("simulated")

    monkeypatch.setattr(demo, "run_long_only_backtest", fail)
    path = tmp_path / "capacity.md"
    with pytest.raises(RuntimeError, match="retained"):
        demo.run_market_impact_capacity_demo(report_path=path, aum_tiers=(1e6,))
    assert "failure" in path.read_text()
    assert any(
        c["status"] == "failure"
        for c in json.loads(path.with_suffix(".json").read_text())["metrics"]["cases"]
    )


@pytest.mark.parametrize(
    "tiers", [(), (0,), (-1,), (np.nan,), (np.inf,), (True,), (1, 1)]
)
def test_invalid_aum_grid_refused(tiers):
    with pytest.raises(ValueError, match="AUM tiers"):
        evaluate(aum_tiers=tiers)
