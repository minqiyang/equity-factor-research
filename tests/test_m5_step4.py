"""Milestone 5 step 4 (amendment 4 revision 2): the required tests on synthetic fixtures.

Every fixture is synthetic (``tests/m5_step4_support.py`` and the rule v2
snapshot harness of ``tests/m4_8_integration_support.py``). No test reads a
private snapshot row or opens a network connection.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import shutil
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import m4_8_integration_support as it
import m5_step4_support as fx
import research.m4_7_sp500_pit_rerun as runner
import research.m5_factor_baseline as base
import research.m5_step3 as step3
import research.m5_step4 as s4
from data.public_factors import PublicDataRefusal
from features.multiple_testing import adjust_pvalues
from research.m4_7_universe_build import BUILD_MANIFEST, Snapshot, discovery_inputs_sha256


pytestmark = pytest.mark.xdist_group("m5_step4")
REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def chain():
    segments = fx.prepared()
    public = fx.public()
    result = s4.evaluate(segments, public, {fx.STOP_ASSET}, None)
    return {"segments": segments, "public": public, "result": result, "doc": s4.summarize(result)}


@pytest.fixture(scope="module")
def snapshot(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("step4_snapshot")
    with pytest.MonkeyPatch.context() as patch:
        snap = it.retrieve(base_dir, patch)
    return snap


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): _sha(p) for p in sorted(root.rglob("*")) if p.is_file()}


def _bind_args(snap: Path) -> dict:
    snapshot = Snapshot.open(snap)
    build = json.loads((snap / BUILD_MANIFEST).read_bytes())
    return {"pins": {rel: _sha(snap / rel) for rel in s4.SNAPSHOT_PINS},
            "snapshot_id": snapshot.manifest["snapshot"]["id"],
            "discovery_inputs": discovery_inputs_sha256(snapshot),
            "declared": {**s4.DECLARED, "d0_pre": build["d0_pre"], "calendar_source": snapshot.calendar_source}}


def _registered(bound: dict, segment) -> dict[str, str]:
    calendar = bound["calendar"]
    return {"side": segment.side, "anchor_row": calendar[segment.anchor_row].date().isoformat(),
            "first_reset": calendar[segment.first_reset_row].date().isoformat(),
            "last_ic_reset": calendar[segment.last_ic_reset_row].date().isoformat(),
            "last_book_row": calendar[segment.last_book_row].date().isoformat()}


def _metric(sharpe, drawdown):
    return {"sharpe": sharpe, "max_drawdown": drawdown}


def _grid(sharpe=1.0, drawdown=0.1, override=None):
    """Metrics per cost case and segment; ``override`` maps (case, segment) to a metric dict."""
    grid = {case: {seg: _metric(sharpe, drawdown) for seg in s4.SEGMENTS} for case in s4.CASES}
    for (case, seg), value in (override or {}).items():
        grid[case][seg] = value
    return grid


# ---------------------------------------------------------------- future perturbation (required test 1)

def _perturb(paths: dict[str, pd.DataFrame], rows: slice, seed: int = 1) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    out = {k: v.copy() for k, v in paths.items()}
    shock = np.exp(rng.normal(0.0, 0.05, out["close"].iloc[rows].shape))
    for field in ("open", "high", "low", "close", "adjusted_close"):
        out[field].iloc[rows] = out[field].iloc[rows].to_numpy() * shock
    out["volume"].iloc[rows] = out["volume"].iloc[rows].to_numpy() * rng.uniform(0.2, 5.0, shock.shape)
    return out


def test_future_perturbation_signals_leave_each_sleeve_target_unchanged():
    """For all six signals: prices, volume, or membership changed after row r - 1 leave the target at r unchanged."""
    paths = fx.vendor_paths()
    base_seg = fx.prepared(paths)["pre"]
    r = int(base_seg.schedule.evaluation_resets[6])                    # pre rows equal full-calendar rows
    member = fx.intervals()
    member.loc[5, ["end_date", "end_known_at"]] = fx.CAL[r + 3]
    perturbed_seg = fx.prepared(_perturb(paths, slice(r, None)), member)["pre"]
    events = s4.empty_events()
    for signal_id in s4.FAMILY_A_IDS:
        before, after = s4.book_signal(base_seg, signal_id), s4.book_signal(perturbed_seg, signal_id)
        np.testing.assert_array_equal(before.iloc[r - 1].to_numpy(), after.iloc[r - 1].to_numpy())
        assert not before.iloc[r:].equals(after.iloc[r:]), signal_id          # the perturbation reaches the signal
        held = []
        for seg, signal in ((base_seg, before), (perturbed_seg, after)):
            result = runner.run_book("long_only", seg.prices, signal, seg.calendar, (seg.schedule.d0 - 1, r + 1),
                                     intervals=seg.intervals, events=events, cost=dict(s4.STOCK_COSTS["primary"]),
                                     top_pct=s4.TOP_PCT, missing_price_policy=s4.HALT_POLICY)
            held.append(result.holdings.loc[seg.calendar[r]])
        pd.testing.assert_series_equal(held[0], held[1])
        assert (held[0] > 0).sum() == int(np.ceil(s4.TOP_PCT * np.isfinite(before.iloc[r - 1]).sum()))


def _layer_weights(paths):
    seg = fx.prepared(paths)["pre"]
    series = s4.segment_series(seg, s4.run_books(seg, -1.0), fx.public())
    return {case: series["layer"][case]["weights"] for case in s4.CASES}, series


def test_future_perturbation_whole_chain_class_weights_use_data_through_t_minus_2():
    """Prices after the last trading day of t-2 leave month t's sigma and R0, rule R1, R2 weights unchanged."""
    paths = fx.vendor_paths()
    t = pd.Period("2012-03", freq="M")
    last_t2 = fx.CAL[fx.CAL.to_period("M") == t - 2][-1]
    row = int(fx.CAL.get_loc(last_t2))
    original, series = _layer_weights(paths)
    later, later_series = _layer_weights(_perturb(paths, slice(row + 1, None)))
    on_boundary, _ = _layer_weights(_perturb(paths, slice(row, row + 1), seed=7))
    for case in s4.CASES:
        pd.testing.assert_series_equal(series["sigma"][case].loc[t], later_series["sigma"][case].loc[t])
        for rule in s4.RULES:
            pd.testing.assert_frame_equal(original[case][rule].loc[:t], later[case][rule].loc[:t])
        assert not original[case]["R1"].loc[t + 1:].equals(later[case]["R1"].loc[t + 1:])
        assert not np.allclose(original[case]["R1"].loc[t], on_boundary[case]["R1"].loc[t], rtol=0, atol=1e-12)


def test_future_perturbation_public_multipliers_after_month_t_leave_weights_unchanged():
    rng = np.random.default_rng(4)
    months = pd.period_range("2015-01", "2015-12", freq="M")
    sigma = pd.DataFrame(rng.uniform(0.005, 0.02, (12, 6)), index=months, columns=list(s4.FAMILY_A_IDS))
    multipliers = fx.public().multipliers
    changed = multipliers.copy()
    changed.loc[months[6]:] = changed.loc[months[6]:] * 1.7
    before = s4.rule_weights(sigma, s4.theme_multipliers(multipliers, months))
    after = s4.rule_weights(sigma, s4.theme_multipliers(changed, months))
    for rule in s4.RULES:
        pd.testing.assert_frame_equal(before[rule].loc[:months[5]], after[rule].loc[:months[5]])
    assert not before["R2"].loc[months[6]:].equals(after["R2"].loc[months[6]:])


# ---------------------------------------------------------------- R4 events and affected weights (2, 3)

def test_r4_events_settle_held_stops_at_minus_one_and_last_close_at_zero(chain):
    pre = chain["segments"]["pre"]
    assert pre.residual == ((fx.STOP_ASSET, fx.STOP_LAST + 1, pre.residual[0][2]),)
    assert chain["segments"]["post"].residual == ()
    stop_day = fx.CAL[fx.STOP_LAST + 1]
    runs = chain["result"]["runs"]
    primary, last_close = runs["primary"]["seg"]["pre"]["books"], runs["last_close"]["seg"]["pre"]["books"]
    holders, others = [], []
    for key in [*primary["sleeves"], "ew"]:
        book = primary["ew"] if key == "ew" else primary["sleeves"][key]
        other = last_close["ew"] if key == "ew" else last_close["sleeves"][key]
        held = s4.held_events(book)
        if held:
            holders.append(key)
            log = [r for r in book.terminal_event_log if r["permanent_id"] == fx.STOP_ASSET][0]
            assert log["terminal_return"] == -1.0 and log["cashflow"] == 0.0
            assert pd.Timestamp(log["effective_date"]) == stop_day
            log0 = [r for r in other.terminal_event_log if r["permanent_id"] == fx.STOP_ASSET][0]
            assert log0["terminal_return"] == 0.0 and log0["cashflow"] > 0.0
            assert book.returns.loc[stop_day] < other.returns.loc[stop_day]
        else:
            others.append(key)
            pd.testing.assert_series_equal(book.returns, other.returns)
    assert "ew" in holders and len(others) >= 1 and len(holders) >= 2
    events = runs["primary"]["tables"]["events"]["pre"]
    for key, table in events.items():
        if "all" in table:
            assert table["seal_gap"]["count"] == table["all"]["count"] and table["other"]["count"] == 0
    assert runs["primary"]["tables"]["residual_stops"]["pre"] == {"count": 1, "seal_gap": 1}


def test_affected_event_weights_use_drifted_sleeve_shares():
    calendar = pd.bdate_range("2020-01-01", "2020-03-31")
    month = pd.Period("2020-02", freq="M")
    flat = pd.Series(1.0, index=calendar)
    grown = flat.where(calendar <= pd.Timestamp("2020-01-31"), 1.2)          # +20 percent after the t-1 close
    equity = {"A": grown, "B": flat, "C": flat}
    weights = pd.DataFrame({"A": [0.5], "B": [0.25], "C": [0.25]}, index=pd.PeriodIndex([month]))
    x_day, y_day, z_day = pd.Timestamp("2020-02-14"), pd.Timestamp("2020-02-20"), pd.Timestamp("2020-03-10")
    sleeve_events = {"A": [{"pid": "X", "date": x_day, "weight": 0.1}, {"pid": "Z", "date": z_day, "weight": 0.5}],
                     "B": [{"pid": "X", "date": x_day, "weight": 0.2}],
                     "C": [{"pid": "Y", "date": y_day, "weight": 0.3}]}
    out = s4.rule_event_summary(sleeve_events, equity, weights, calendar, {"Y"})
    x_weight = 0.6 / 1.1 * 0.1 + 0.25 / 1.1 * 0.2
    y_weight = 0.25 / 1.1 * 0.3
    assert out["unique_events"] == 2 and out["incidences"] == 3          # Z lies outside the class-layer months
    assert out["weight_sum"] == pytest.approx(x_weight + y_weight, abs=1e-15)
    assert out["weight_max"] == pytest.approx(x_weight, abs=1e-15) and x_weight == pytest.approx(0.1)
    assert out["seal_gap_events"] == 1 and out["seal_gap_weight_sum"] == pytest.approx(y_weight)
    fake = SimpleNamespace(terminal_event_log=(
        {"permanent_id": "X", "effective_date": "2020-02-14", "incoming_weight": 0.1},
        {"permanent_id": "Q", "effective_date": "2020-02-14", "incoming_weight": 0.0},
        {"permanent_id": "Z", "effective_date": "2020-03-10", "incoming_weight": 0.5}))
    held = s4.held_events(fake)
    assert [r["pid"] for r in held] == ["X", "Z"]
    table = s4.book_event_summary(held, {"Z"}, {month})
    assert table["all"] == {"count": 2, "weight_sum": pytest.approx(0.6), "weight_max": 0.5}
    assert table["seal_gap"]["count"] == 1 and table["outside_comparison_months"]["count"] == 1


# ---------------------------------------------------------------- snapshot binding (4, 14, 15)

def test_terminal_free_loader_reads_nothing_under_terminal(snapshot, monkeypatch):
    assert not (snapshot / "terminal").exists()
    before = _tree(snapshot)

    def forbidden(path) -> None:
        if "terminal" in Path(str(path)).parts:
            raise AssertionError("read under terminal/")

    def reject(*_args, **_kwargs):
        raise AssertionError("read_engine_events called")

    originals = {name: getattr(Path, name) for name in ("read_bytes", "read_text", "open")}
    for name, original in originals.items():
        monkeypatch.setattr(Path, name, lambda self, *a, _o=original, **k: (forbidden(self), _o(self, *a, **k))[1])
    import builtins
    real_open = builtins.open
    monkeypatch.setattr(builtins, "open", lambda file, *a, **k: (forbidden(file), real_open(file, *a, **k))[1])
    monkeypatch.setattr(runner, "read_engine_events", reject)
    bound = s4.bind_step4(snapshot, **_bind_args(snapshot))
    runs, access = s4.load_segment_runs_step4(bound)
    assert access == {"pre": ["discovery_pre"], "post": ["discovery_post"]}
    for run in runs:
        assert len(run.events) == 0 and list(run.events.columns) == list(s4.empty_events().columns)
    monkeypatch.undo()
    assert _tree(snapshot) == before and not (snapshot / "terminal").exists()


@pytest.mark.parametrize("relative", sorted(s4.SNAPSHOT_PINS))
def test_seal_and_pins_changed_pinned_file_refuses_before_any_load(snapshot, tmp_path, monkeypatch, relative):
    args = _bind_args(snapshot)
    copy = tmp_path / "snap"
    shutil.copytree(snapshot, copy)
    with (copy / relative).open("ab") as handle:
        handle.write(b"\n")
    monkeypatch.setattr(runner, "load_eod_cohort_panels", lambda *a, **k: pytest.fail("panel load"))
    with pytest.raises(runner.RunnerStop) as stop:
        s4.bind_step4(copy, **args)
    assert stop.value.reason == "derived_artifact_stale" and stop.value.detail == relative


def test_seal_and_pins_panel_hash_discovery_inputs_and_seal_window(snapshot, tmp_path):
    args = _bind_args(snapshot)
    copy = tmp_path / "snap"
    shutil.copytree(snapshot, copy)
    panel = sorted((copy / "panel").rglob("*.parquet"))[0]
    with panel.open("ab") as handle:
        handle.write(b"\0")
    with pytest.raises(runner.RunnerStop) as stop:
        s4.bind_step4(copy, **args)
    assert stop.value.reason == "derived_artifact_stale" and stop.value.detail == "panel file"
    with pytest.raises(runner.RunnerStop) as stop:
        s4.bind_step4(snapshot, **{**args, "discovery_inputs": "0" * 64})
    assert stop.value.reason == "derived_artifact_stale" and stop.value.detail == "discovery_inputs"
    assert s4.SEAL_WINDOW == ("2019-07-31", "2020-07-31")
    s4.bind_step4(snapshot, **args)                                   # the carried window equals the declared one
    with pytest.raises(runner.RunnerStop) as stop:
        s4.bind_step4(snapshot, **args, seal_window=("2019-08-01", "2020-07-31"))
    assert stop.value.reason == "holdout_overlap_refused"


def test_seal_and_pins_seal_window_row_refuses():
    run = fx.runs()[0]
    seal_day = fx.CAL[fx.ROW_START]
    fields = dict(run.fields)
    close = fields["adjusted_close"]
    fields["adjusted_close"] = pd.concat([close, close.iloc[-1:].set_axis([seal_day])])
    with pytest.raises(runner.RunnerStop) as stop:
        s4.prepare(dataclasses.replace(run, fields=fields), fx.registered(run.segment), fx.SEAL)
    assert stop.value.reason == "seal_bracket_computation_forbidden"


def test_no_snapshot_write(snapshot):
    before = _tree(snapshot)
    bound = s4.bind_step4(snapshot, **_bind_args(snapshot))
    runs, _ = s4.load_segment_runs_step4(bound)
    for run in runs:
        seg = s4.prepare(run, _registered(bound, run.segment))
        assert len(seg.calendar) == run.segment.last_book_row - run.segment.feature_floor_row + 1
    shares, lookup, _ = s4.snapshot_accounting(bound)
    assert set(shares) == {"pre", "post"} and lookup
    s4.verify_pins_unchanged(snapshot, _bind_args(snapshot)["pins"])
    assert _tree(snapshot) == before


# ---------------------------------------------------------------- fragility (5)

def _rows(margins, key_segment="pre"):
    return [{"segment": key_segment, "cost_case": "primary", "metric": f"m{i}", "margin": m} for i, m in enumerate(margins)]


def _run(means, r1, r2, r20, baseline="R1", r2_outcome="closed"):
    return {"s4_means": means, "conditions": {"R1_vs_R0": _rows(r1), "R2_vs_R1": _rows(r2), "R2_vs_R0": _rows(r20)},
            "decision": {"baseline": baseline, "r2": r2_outcome}}


def test_fragility_labels_sign_and_outcome_changes(chain):
    same = _run({"S4.R1": 0.01, "S4.R2": -0.02}, [0.1] * 8, [-0.1] * 8, [0.2] * 8)
    assert s4.fragility(same, same) == {"fragile": False, "sign_changes": [], "outcome_changes": []}
    flipped_mean = _run({"S4.R1": -0.01, "S4.R2": -0.02}, [0.1] * 8, [-0.1] * 8, [0.2] * 8)
    assert s4.fragility(same, flipped_mean)["sign_changes"] == ["S4.R1"]
    flipped_margin = _run({"S4.R1": 0.01, "S4.R2": -0.02}, [0.1] * 7 + [-0.1], [-0.1] * 8, [0.2] * 8)
    assert s4.fragility(same, flipped_margin)["fragile"]
    tiny = _run({"S4.R1": 0.01, "S4.R2": -0.02}, [0.1] * 7 + [5e-13], [-0.1] * 8, [0.2] * 8)
    tiny_other = _run({"S4.R1": 0.01, "S4.R2": -0.02}, [0.1] * 7 + [-5e-13], [-0.1] * 8, [0.2] * 8)
    assert not s4.fragility(tiny, tiny_other)["fragile"]
    r20_flip = _run({"S4.R1": 0.01, "S4.R2": -0.02}, [0.1] * 8, [-0.1] * 8, [-0.2] * 8)
    assert not s4.fragility(same, r20_flip)["fragile"]                   # R2 against R0 counts only under R0
    same_r0 = _run({"S4.R1": 0.01, "S4.R2": -0.02}, [0.1] * 8, [-0.1] * 8, [0.2] * 8, baseline="R0")
    r20_flip_r0 = _run({"S4.R1": 0.01, "S4.R2": -0.02}, [0.1] * 8, [-0.1] * 8, [-0.2] * 8, baseline="R0")
    assert s4.fragility(same_r0, r20_flip_r0)["fragile"]
    outcome = _run({"S4.R1": 0.01, "S4.R2": -0.02}, [0.1] * 8, [-0.1] * 8, [0.2] * 8, r2_outcome="continues")
    assert s4.fragility(same, outcome)["outcome_changes"] == ["r2"]
    rerun = json.dumps(chain["doc"]["runs"]["last_close"])
    assert not re.search(r"pvalue|qvalue|ci95|hac_statistic", rerun)
    assert set(chain["doc"]["s4_tests"]) == {"S4.R1", "S4.R2"}


# ---------------------------------------------------------------- long-only Sharpe (6)

def _exact(mean: float, sd: float, n: int = 24, seed: int = 0) -> pd.Series:
    z = np.random.default_rng(seed).standard_normal(n)
    z = (z - z.mean()) / z.std(ddof=1)
    return pd.Series(mean + sd * z, index=pd.period_range("2015-01", periods=n, freq="M"))


def test_long_only_sharpe_subtracts_rf_and_can_fail_the_condition():
    low_vol, high_vol = _exact(0.004, 0.01), _exact(0.012, 0.04, seed=1)
    zero, rf = pd.Series(0.0, index=low_vol.index), pd.Series(0.003, index=low_vol.index)
    assert s4.sharpe_long_only(low_vol, zero) == pytest.approx(0.4 * np.sqrt(12))
    assert s4.sharpe_long_only(low_vol, zero) > s4.sharpe_long_only(high_vol, zero)
    assert s4.sharpe_long_only(low_vol, rf) == pytest.approx(0.1 * np.sqrt(12))
    assert s4.sharpe_long_only(low_vol, rf) < s4.sharpe_long_only(high_vol, rf)
    for free, holds in ((zero, True), (rf, False)):
        candidate = {c: {s: s4.metrics(low_vol, free) for s in s4.SEGMENTS} for c in s4.CASES}
        comparator = {c: {s: s4.metrics(high_vol, free) for s in s4.SEGMENTS} for c in s4.CASES}
        sharpe_rows = [r for r in s4.conditions(candidate, comparator) if r["metric"] == "sharpe"]
        assert len(sharpe_rows) == 4 and all(r["holds"] is holds for r in sharpe_rows)
    assert s4.sharpe_long_only(high_vol, zero) == pytest.approx(base.performance(high_vol)["sharpe"])
    with pytest.raises(runner.RunnerStop) as stop:
        s4.sharpe_long_only(low_vol, rf.iloc[1:])
    assert stop.value.reason == "risk_free_missing"


def test_long_only_sharpe_public_counterpart_keeps_v1_sharpe(chain):
    public = chain["public"]
    primary = chain["result"]["runs"]["primary"]
    months = primary["seg"]["post"]["layer"]["primary"]["months"]
    expected = base.performance(public.nets["R1"]["primary"].loc[months[0]:months[-1]])
    assert primary["public_grid"]["R1"]["primary"]["post"]["sharpe"] == pytest.approx(expected["sharpe"])
    net = primary["seg"]["post"]["layer"]["primary"]["books"]["R1"]["net"]
    assert primary["grid"]["R1"]["primary"]["post"]["sharpe"] == pytest.approx(
        s4.sharpe_long_only(net, public.rf))


# ---------------------------------------------------------------- class layer (7, 8, 9, 10)

def test_drift_turnover_matches_hand_calculation(chain):
    months = pd.period_range("2015-01", periods=2, freq="M")
    weights = pd.DataFrame({"A": [0.5, 0.6], "B": [0.5, 0.4]}, index=months)
    returns = pd.DataFrame({"A": [0.1, 0.0], "B": [-0.1, 0.0]}, index=months)
    book = s4.drift_portfolio(weights, returns, 20)
    np.testing.assert_allclose(book["turnover"].to_numpy(), [1.0, 0.1], atol=1e-15)
    np.testing.assert_allclose(book["net"].to_numpy(), [-0.002, -0.0002], atol=1e-15)
    for run in chain["result"]["runs"].values():
        for seg in run["seg"].values():
            for case in s4.CASES:
                for rule in s4.RULES:
                    assert seg["layer"][case]["books"][rule]["turnover"].iloc[0] == pytest.approx(1.0)


def _fake_segment(calendar, full_calendar, first_reset):
    d0 = int(calendar.get_loc(pd.Timestamp(first_reset)))
    return SimpleNamespace(calendar=calendar, full_calendar=full_calendar,
                           schedule=SimpleNamespace(d0=d0, d_last=len(calendar) - 1))


def test_monthly_compounding_windows_first_reset_cost_and_partial_month():
    calendar = pd.bdate_range("2020-01-01", "2020-04-08")
    seg = _fake_segment(calendar, calendar, "2020-01-31")
    daily = pd.Series(np.random.default_rng(2).normal(0, 0.01, len(calendar)), index=calendar)
    monthly = s4.compound_monthly(daily, s4.month_labels(seg))
    assert list(monthly.index.astype(str)) == ["2020-02", "2020-03"]              # April is partial
    feb = daily.loc["2020-01-31":"2020-02-28"]
    mar = daily.loc["2020-03-02":"2020-03-31"]
    assert monthly.iloc[0] == pytest.approx((1 + feb).prod() - 1)
    assert monthly.iloc[1] == pytest.approx((1 + mar).prod() - 1)
    longer = pd.bdate_range("2020-01-01", "2020-05-29")
    kept = s4.month_labels(_fake_segment(calendar[:calendar.get_loc(pd.Timestamp("2020-03-31")) + 1], longer,
                                         "2020-01-31"))
    assert sorted(set(kept.astype(str))) == ["2020-02", "2020-03"]              # March complete: a later row exists


def test_monthly_compounding_benchmarks_use_the_sleeve_rows(chain):
    seg = chain["segments"]["post"]
    out = chain["result"]["runs"]["primary"]["seg"]["post"]
    first, cut = seg.schedule.d0, seg.calendar[seg.calendar.to_period("M") == pd.Period("2015-01", freq="M")][-1]
    spy_daily = seg.spy.pct_change(fill_method=None)
    assert out["spy"].iloc[0] == pytest.approx((1 + spy_daily.loc[seg.calendar[first]:cut]).prod() - 1)
    sleeve = out["books"]["sleeves"][("MOM_12_1", "primary")]
    assert out["monthly"]["primary"]["MOM_12_1"].iloc[0] == pytest.approx(
        (1 + sleeve.returns.loc[seg.calendar[first]:cut]).prod() - 1)
    assert sleeve.returns.loc[seg.calendar[first]] < 0                    # the initial purchase cost
    assert str(out["sleeve_months"][-1]) == "2016-11"                     # December 2016 is partial


def test_own_sigma_window_undefined_start_and_zero_refusal(chain):
    calendar = pd.bdate_range("2020-01-01", "2020-12-31")
    daily = pd.Series(np.random.default_rng(8).normal(0, 0.01, len(calendar)), index=calendar)
    months = pd.period_range("2020-02", "2020-12", freq="M")
    first_row = pd.Timestamp("2020-01-31")
    sigma = s4.own_sigma(daily, months, first_row)
    for month in months:
        window = daily[(daily.index > first_row) & (daily.index.to_period("M") <= month - 2)]
        if len(window) >= 126:
            assert sigma[month] == pytest.approx(np.std(window.to_numpy()[-126:], ddof=1), abs=0)
        else:
            assert np.isnan(sigma[month])
    t = pd.Period("2020-09", freq="M")
    through = daily[daily.index.to_period("M") <= t - 2]
    exact_126 = s4.own_sigma(daily, pd.PeriodIndex([t]), through.index[-127])
    exact_125 = s4.own_sigma(daily, pd.PeriodIndex([t]), through.index[-126])
    assert np.isfinite(exact_126[t]) and np.isnan(exact_125[t])
    # The equal-weight benchmark is no sigma input.
    seg = chain["segments"]["pre"]
    run = chain["result"]["runs"]["primary"]["seg"]["pre"]
    books = dict(run["books"])
    books["ew"] = dataclasses.replace(books["ew"], returns=books["ew"].returns * 3.0)
    changed = s4.segment_series(seg, books, chain["public"])
    for case in s4.CASES:
        pd.testing.assert_frame_equal(changed["sigma"][case], run["sigma"][case])
        for rule in s4.RULES:
            pd.testing.assert_frame_equal(changed["layer"][case]["weights"][rule], run["layer"][case]["weights"][rule])
    assert not changed["ew"].equals(run["ew"])
    # The class layer starts at the first month with a full window for every sleeve; a zero sigma refuses.
    sleeve_months = pd.period_range("2015-01", "2015-12", freq="M")
    sig = pd.DataFrame(0.01, index=sleeve_months, columns=list(s4.FAMILY_A_IDS))
    sig.loc[:"2015-04"] = np.nan
    sig.loc[:"2015-06", "REV_1M"] = np.nan
    monthly = pd.DataFrame(0.01, index=sleeve_months, columns=list(s4.FAMILY_A_IDS))
    layer = s4.class_layer({c: monthly for c in s4.CASES}, {c: sig for c in s4.CASES}, fx.public().multipliers,
                           pd.Period("2015-12", freq="M"))
    assert str(layer["primary"]["months"][0]) == "2015-07"
    zero = sig.copy()
    zero.loc["2015-09", "LOW_VOL_252"] = 0.0
    with pytest.raises(runner.RunnerStop) as stop:
        s4.class_layer({c: monthly for c in s4.CASES}, {c: zero for c in s4.CASES}, fx.public().multipliers,
                       pd.Period("2015-12", freq="M"))
    assert stop.value.reason == "sigma_degenerate"


def test_r2_multipliers_equal_step3_output_and_missing_refuses():
    rng = np.random.default_rng(6)
    all_months = pd.period_range("2000-01", "2010-12", freq="M")
    class_values = pd.DataFrame(rng.normal(0.003, 0.02, (len(all_months), 5)), index=all_months,
                                columns=["Low Risk", "Momentum", "Short-Term Reversal", "Size", "Value"])
    labels = pd.DataFrame(rng.integers(0, 2, (len(all_months), 3)).astype(float), index=all_months,
                          columns=list(step3.STATES))
    months = pd.period_range("2005-01", "2010-12", freq="M")
    multipliers = step3.r2_on_months(class_values, labels, all_months[0], all_months[-1], months)["multipliers"]
    themed = s4.theme_multipliers(multipliers, months)
    for signal_id, (_, theme) in s4.SLEEVES.items():
        pd.testing.assert_series_equal(themed[signal_id], multipliers[theme], check_names=False)
    assert not np.allclose(themed.to_numpy(), 1.0)
    sigma = pd.DataFrame(rng.uniform(0.005, 0.02, themed.shape), index=months, columns=list(s4.FAMILY_A_IDS))
    w2 = s4.rule_weights(sigma, themed)["R2"]
    assert (w2 > 0).to_numpy().all() and np.allclose(w2.sum(axis=1), 1.0)
    with pytest.raises(runner.RunnerStop) as stop:
        s4.theme_multipliers(multipliers.drop(months[3]), months)
    assert stop.value.reason == "r2_multiplier_missing"


def test_empty_sleeve_refuses(chain):
    seg = chain["segments"]["pre"]
    r = int(seg.schedule.evaluation_resets[4])
    signal = seg.signals["MOM_12_1"].copy()
    signal.iloc[r - 1] = np.nan
    empty = dataclasses.replace(seg, signals={**seg.signals, "MOM_12_1": signal})
    with pytest.raises(runner.RunnerStop) as stop:
        s4.run_books(empty, -1.0)
    assert stop.value.reason == "empty_sleeve_target"


# ---------------------------------------------------------------- halts and missingness (11, 12)

def _tiny_book(close: pd.DataFrame):
    calendar = close.index
    signal = pd.DataFrame(np.tile(np.arange(close.shape[1], 0, -1, dtype=float), (len(calendar), 1)),
                          index=calendar, columns=close.columns)
    member = pd.DataFrame({"symbol": close.columns, "permanent_id": close.columns, "start_date": calendar[0],
                           "start_known_at": calendar[0], "end_date": pd.NaT, "end_known_at": pd.NaT})
    return runner.run_book("long_only", close, signal, calendar, (0, len(calendar) - 1), intervals=member,
                           events=s4.empty_events(), cost=dict(s4.STOCK_COSTS["primary"]), top_pct=s4.TOP_PCT,
                           missing_price_policy=s4.HALT_POLICY)


def test_halt_versus_bad_data():
    calendar = pd.bdate_range("2020-01-01", "2020-04-30")
    rng = np.random.default_rng(9)
    close = pd.DataFrame(20 * np.exp(np.cumsum(rng.normal(0, 0.01, (len(calendar), 5)), axis=0)), index=calendar,
                         columns=[f"H{k}" for k in range(5)])
    halted = close.copy()
    halted.loc["2020-02-12":"2020-02-13", "H0"] = np.nan
    result = _tiny_book(halted)
    assert result.halt_ledger["unmarked_halt_rows"] == [(pd.Timestamp("2020-02-12"), "H0"),
                                                        (pd.Timestamp("2020-02-13"), "H0")]
    assert result.returns.loc["2020-02-12"] == 0.0
    for bad in (0.0, -1.0, np.inf):
        broken = close.copy()
        broken.loc["2020-02-12", "H0"] = bad
        with pytest.raises(runner.RunnerStop) as stop:
            _tiny_book(broken)
        assert stop.value.reason == "incoming_price_invalid"


def _accounting_fixture():
    calendar = pd.bdate_range("2020-01-01", "2020-03-31")
    day = lambda row: calendar[row].date().isoformat()                 # noqa: E731
    rows = [
        ("I1", "A", "P1", "resolved", "index_removal_still_trading", day(0), ""),
        ("I2", "B", "P2", "resolved", "delisting_candidate", day(20), day(30)),
        ("I3", "C", "", "no_containing_episode:no_vendor_bars:C", "", day(0), day(15)),
        ("I4", "D", "P3", "resolved", "", day(40), ""),
        ("E/1", "E", "P4", "resolved", "index_removal_still_trading", day(5), day(30)),
        ("E/2", "E", "P5", "resolved", "index_removal_still_trading", day(25), day(45)),
        ("I7", "G", "", "entry_missing_field", "", "", ""),
    ]
    intervals = pd.DataFrame(rows, columns=["interval_id", "vendor_code", "permanent_id", "resolution", "exit_class",
                                            "m_in", "m_out"])
    return calendar, intervals


def test_unpriced_accounting_matches_hand_count():
    calendar, intervals = _accounting_fixture()
    shares = s4.unpriced_share(intervals, calendar, {"pre": (10, 49, "discovery_pre")},
                               panels={"discovery_pre": {"P1", "P4"}}, quarantined={"discovery_pre": {"B"}},
                               refusals={"discovery_pre": {"P3"}})["pre"]
    assert (shares["priced"], shares["unpriced"], shares["denominator"]) == (60, 40, 100)
    assert shares["unpriced_share"] == pytest.approx(0.4)
    assert shares["by_exit_class"] == {"index_removal_still_trading": 15, "delisting_candidate": 10,
                                       "disappearance_outside_membership": 0, "seal_gap_identity_split": 0,
                                       "unresolved_no_permanent_id": 5, "unknown": 10}
    assert shares["by_reason"] == {"episode_panel_refusal": 10, "eod_quarantine": 10, "no_vendor_bars": 5,
                                   "other": 15}
    assert shares["undated_intervals"] == 1
    assert shares["unpriced_share_upper_bound"] == pytest.approx((40 + 40) / (100 + 40))
    with pytest.raises(runner.RunnerStop) as stop:
        s4.reconcile("pre", 100, 60, 41, {"unknown": 41}, {"other": 41})
    assert stop.value.reason == "unpriced_accounting_unreconciled"
    with pytest.raises(runner.RunnerStop):
        s4.reconcile("pre", 100, 60, 40, {"unknown": 39}, {"other": 40})


def test_unpriced_accounting_signal_exclusions_and_halts_split_by_exit_class():
    calendar, intervals = _accounting_fixture()
    lookup = s4.exit_class_lookup(intervals, calendar)
    columns = pd.Index(["P1", "P2", "P9"])
    mask = pd.DataFrame(True, index=calendar, columns=columns)
    signal = pd.DataFrame(1.0, index=calendar, columns=columns)
    signal.iloc[24, :] = np.nan                                  # signal row of the reset at row 25
    seg = SimpleNamespace(schedule=SimpleNamespace(evaluation_resets=np.array([25, 40]), evaluation_mask=mask),
                          signals={"MOM_12_1": signal}, prices=pd.DataFrame(columns=columns), offset=0,
                          calendar=calendar)
    out = s4.signal_exclusions(seg, lookup)["MOM_12_1"]
    assert out["total"] == 3 and out["per_rebalance"] == [3, 0]
    assert out["by_exit_class"] == {"delisting_candidate": 1, "index_removal_still_trading": 1, "unknown": 1}
    fake = SimpleNamespace(halt_ledger={"unmarked_halt_rows": [(calendar[22], "P2"), (calendar[35], "P2")],
                                        "locked_execution_rows": []})
    halts = s4.halt_counts(fake, seg, lookup)
    assert halts["unmarked_halt_rows"] == 2
    assert halts["by_exit_class"] == {"delisting_candidate": 1, "unknown": 1}


# ---------------------------------------------------------------- windows, decisions, survival (16-19)

def test_comparison_window_ends_at_public_last_month(chain):
    tables = chain["result"]["runs"]["primary"]["tables"]
    assert tables["comparison_months"]["post"]["primary"][1] == str(fx.PUBLIC_LAST)
    assert tables["comparison_months"]["pre"]["primary"][1] == "2012-12"
    sleeve_months = tables["benchmarks"]["post"]["sleeve_months"]
    assert sleeve_months[1] == "2016-11" and pd.Period(sleeve_months[1], freq="M") > fx.PUBLIC_LAST
    grid = chain["result"]["runs"]["primary"]["grid"]
    assert grid["R0"]["primary"]["post"]["months"] == tables["comparison_months"]["post"]["primary"][2]
    assert tables["sleeves"]["post"]["MOM_12_1|primary"]["months"] == sleeve_months[2]


def test_decision_outcomes_through_the_closure_adapter():
    good, worse_sharpe = _grid(), _grid(override={("sensitivity", "post"): _metric(0.5, 0.1)})
    r1_vs_r0_fail = s4.conditions(worse_sharpe, good)
    assert sum(not r["holds"] for r in r1_vs_r0_fail) == 1
    assert {(r["segment"], r["cost_case"], r["metric"]) for r in r1_vs_r0_fail if not r["holds"]} == {
        ("post", "sensitivity", "sharpe")}
    passing = s4.conditions(good, good)
    assert s4.decide({"R1_vs_R0": passing, "R2_vs_R1": passing, "R2_vs_R0": passing}) == {
        "baseline": "R1", "r2": "continues", "r2_label": "no evidence of state timing",
        "counts": {"R1_vs_R0": 8, "R2_vs_R1": 8, "R2_vs_R0": 8}}
    assert s4.decide({"R1_vs_R0": r1_vs_r0_fail, "R2_vs_R1": passing, "R2_vs_R0": passing})["baseline"] == "R0"
    deeper = s4.conditions(_grid(override={("primary", "pre"): _metric(1.0, 0.2)}), good)
    assert s4.decide({"R1_vs_R0": passing, "R2_vs_R1": deeper, "R2_vs_R0": passing})["r2"] == "closed"
    under_r0 = s4.decide({"R1_vs_R0": r1_vs_r0_fail, "R2_vs_R1": passing, "R2_vs_R0": deeper})
    assert under_r0["baseline"] == "R0" and under_r0["r2"] == "closed"
    assert s4.decide({"R1_vs_R0": r1_vs_r0_fail, "R2_vs_R1": passing, "R2_vs_R0": passing})["r2"] == "continues"
    undefined = s4.conditions(_grid(override={("primary", "pre"): _metric(None, 0.1)}), good)
    assert sum(not r["holds"] for r in undefined) == 1
    tiny = s4.conditions(_grid(sharpe=1.0 - 5e-13, drawdown=0.1 + 5e-13), good)
    assert all(r["holds"] for r in tiny)


def test_survival_tables_use_the_same_months_and_undefined_ratio(chain):
    primary = chain["result"]["runs"]["primary"]
    public = chain["public"]
    for sid in s4.SEGMENTS:
        for case in s4.CASES:
            months = primary["seg"][sid]["layer"][case]["months"]
            for rule in s4.RULES:
                expected = base.performance(public.nets[rule][case].loc[months[0]:months[-1]])
                got = primary["public_grid"][rule][case][sid]
                assert got["months"] == len(months) and got["max_drawdown"] == pytest.approx(expected["max_drawdown"])
    for rows in primary["survival"].values():
        assert len(rows) == 8
        for row in rows:
            if row["public_margin"] is None or row["public_margin"] <= 0:
                assert row["margin_ratio"] is None
            else:
                assert row["margin_ratio"] == pytest.approx(row["margin"] / row["public_margin"])
    assert s4.ratio(1.0, 2.0) == 0.5 and s4.ratio(1.0, 0.0) is None and s4.ratio(1.0, -1.0) is None


def test_transmission_ratio_and_correlation():
    months = pd.period_range("2015-01", periods=3, freq="M")
    active = pd.Series([0.01, 0.03, 0.02], index=months)
    jkp = pd.Series([0.02, 0.06, 0.04], index=months)
    out = s4._transmission(active, jkp)
    assert out["ratio"] == pytest.approx(0.5) and out["correlation"] == pytest.approx(1.0)
    assert out["pit_mean_active"] == pytest.approx(0.02) and out["public_mean"] == pytest.approx(0.04)
    assert s4._transmission(active, pd.Series([0.01, -0.02, 0.01], index=months))["ratio"] is None
    with pytest.raises(runner.RunnerStop):
        s4._transmission(active, jkp.iloc[:2].reindex(months))


# ---------------------------------------------------------------- family, costs, pins (20-22)

def test_s4_family_is_by_with_480_slots(chain):
    pvalues = pd.Series({"S4.R1": 0.001, "S4.R2": 0.2})
    pd.testing.assert_series_equal(s4.s4_family(pvalues), adjust_pvalues(pvalues, method="by", family_size=480))
    with pytest.raises(runner.RunnerStop):
        s4.s4_family(pd.Series({"a": 0.1, "b": 0.2, "c": 0.3}))
    with pytest.raises(runner.RunnerStop):
        s4.s4_family(pvalues, family_size=479)
    tests = chain["result"]["s4_tests"]
    observed = pd.Series({k: v["family_p"] for k, v in tests.items()})
    expected = adjust_pvalues(observed, method="by", family_size=480)
    assert {k: v["by_qvalue"] for k, v in tests.items()} == pytest.approx(expected.to_dict())


def test_costs_pair_stock_and_switch_cases(chain, monkeypatch):
    assert s4.STOCK_COSTS == {"primary": {"transaction_cost_bps": 1.0, "slippage_bps": 4.0},
                              "sensitivity": {"transaction_cost_bps": 2.0, "slippage_bps": 8.0}}
    assert s4.SWITCH_BPS == {"primary": 20, "sensitivity": 50}
    calls = []
    original = runner.run_book

    def record(*args, **kwargs):
        calls.append((kwargs["cost"], kwargs["top_pct"], kwargs["missing_price_policy"]))
        return original(*args, **kwargs)

    monkeypatch.setattr(runner, "run_book", record)
    s4.run_books(chain["segments"]["post"], -1.0)
    sleeve_calls = [c for c in calls if c[1] == s4.TOP_PCT]
    assert len(sleeve_calls) == 12 and len(calls) == 13
    assert sum(c[0] == s4.STOCK_COSTS["primary"] for c in sleeve_calls) == 6
    assert sum(c[0] == s4.STOCK_COSTS["sensitivity"] for c in sleeve_calls) == 6
    assert [c for c in calls if c[1] == 1.0][0][0] == {"transaction_cost_bps": 0.0, "slippage_bps": 0.0}
    assert all(c[2] == s4.HALT_POLICY for c in calls)
    seg = chain["result"]["runs"]["primary"]["seg"]["pre"]
    for case, bps in s4.SWITCH_BPS.items():
        book = seg["layer"][case]["books"]["R1"]
        pd.testing.assert_series_equal(book["net"], book["gross"] - bps / 10_000 * book["turnover"], check_names=False)
    sens = chain["result"]["runs"]["primary"]["tables"]["sleeves"]["pre"]
    assert sens["MOM_12_1|sensitivity"]["stock_cost_monthly_mean"] == pytest.approx(
        2 * sens["MOM_12_1|primary"]["stock_cost_monthly_mean"], rel=0.05)


def test_trial_file_pins_refuse_a_changed_pin(tmp_path, monkeypatch):
    assert set(s4.TRIAL_PINS) == {base.TRIAL_PATH, *base.AMENDMENTS, step3.AMENDMENT_3_PATH, s4.AMENDMENT_4_PATH}
    assert s4.TRIAL_PINS[s4.AMENDMENT_4_PATH] == s4.AMENDMENT_4_SHA256
    step3.verify_trial_files(REPO_ROOT, s4.TRIAL_PINS)
    for path in s4.TRIAL_PINS:
        monkeypatch.setattr(s4, "TRIAL_PINS", {**s4.TRIAL_PINS, path: "0" * 64})
        with pytest.raises(PublicDataRefusal):
            s4.run(REPO_ROOT, tmp_path / "absent", {"commit": "x", "tracked_changes": False})
        monkeypatch.undo()


# ---------------------------------------------------------------- R11: aggregates only

FORBIDDEN = (re.compile(r"\b[A-Z][A-Z0-9-]*\.US\b"), re.compile(r"/Users/|/private/|/home/|private_data|/tmp/"))


def _scan(text: str, extra: tuple[str, ...] = ()) -> None:
    for pattern in FORBIDDEN:
        assert not pattern.search(text), pattern.pattern
    for token in extra:
        assert token not in text, token


def test_report_leads_with_decisions_and_every_table_row_fits_its_header(chain):
    report = s4.render_report({**chain["doc"], "unpriced": {}})
    sections = [line for line in report.splitlines() if line.startswith("## ")]
    assert sections[:2] == ["## Decision Outcomes (primary run)",
                            "## Survival: Point-in-Time Conditions Beside the Public Margins"]
    decision = report.split("## Decision Outcomes")[1].split("## Survival")[0]
    assert "of 8 on public books" in decision and "Fragility: **" in decision
    assert report.index("DIAGNOSTIC_ONLY") < report.index("VP-2") < report.index("## Decision Outcomes")
    width = None
    for line in report.splitlines():
        if line.startswith("|"):
            cells = line.count("|") - 1
            width = cells if width is None else width
            assert cells == width, line
        else:
            width = None


def test_outputs_hold_no_identifier_or_path(chain):
    doc = {**chain["doc"], "unpriced": {}}
    text = json.dumps(s4._clean(doc)) + s4.render_report(doc)
    _scan(text, tuple(fx.ASSETS) + tuple(a.split(".")[0] for a in fx.ASSETS))
    committed = [REPO_ROOT / s4.REPORT_MD, REPO_ROOT / s4.REPORT_JSON, REPO_ROOT / s4.ATTEMPTS_JSONL]
    for path in committed:
        if path.is_file():
            _scan(path.read_text(encoding="utf-8"))
