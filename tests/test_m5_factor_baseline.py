"""Milestone 5 step 2 baseline: loaders, weights, costs, metrics, and decision.

Synthetic fixtures only; no network access and no provider file.
"""

from __future__ import annotations

import json
import math
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data.public_factors import (
    MISSING_ABSENT,
    MISSING_BLANK,
    MISSING_CODE,
    PRESENT,
    MonthlyPanel,
    PublicDataRefusal,
    fetch,
    manifest_entry,
    publication_year,
    read_fred_csv,
    read_french_monthly_zip,
    read_jkp_zip,
    read_publication_years,
    write_manifest,
)
from features.multiple_testing import adjust_pvalues, return_test_statistics
from research import m5_factor_baseline as m5


def months(start: str, end: str) -> pd.PeriodIndex:
    return pd.period_range(start, end, freq="M")


def random_panel(seed: int = 7, start: str = "1990-01", end: str = "1996-12") -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    index = months(start, end)
    frame = pd.DataFrame(rng.normal(0.004, [0.01, 0.02, 0.03, 0.015], size=(len(index), 4)),
                         index=index, columns=["A", "B", "C", "D"])
    frame.iloc[rng.choice(len(index), 20, replace=False), 2] = np.nan
    frame.loc["1990-01":"1991-06", "D"] = np.nan
    return frame


def trial_like(first: str = "1993-01", first_half_end: str = "1994-12") -> dict:
    second = (pd.Period(first_half_end, freq="M") + 1).strftime("%Y-%m")
    return {"evaluation_window": {"first_evaluated_month": first,
                                  "halves": {"first": [first, first_half_end],
                                             "second": [second, "last_evaluated_month"]}},
            "traits": {"years_since_publication": {"missing_publication_year": ["D"]}}}


# Timing ----------------------------------------------------------------------

@pytest.mark.parametrize("rule", ["R0", "R1"])
def test_future_perturbation_leaves_month_t_set_sigma_and_weights_unchanged(rule: str) -> None:
    returns = random_panel()
    evaluated = months("1993-01", "1996-12")
    base = m5.membership(returns, evaluated)
    base_weights = m5.rule_weights(rule, base.in_set, base.sigma)
    rng = np.random.default_rng(11)
    for month in (pd.Period("1993-01", freq="M"), pd.Period("1994-07", freq="M"),
                  pd.Period("1996-12", freq="M")):
        perturbed = returns.copy()
        future = perturbed.index >= month
        noise = rng.normal(0.0, 0.5, size=perturbed.loc[future].shape)
        perturbed.loc[future] = perturbed.loc[future] + noise  # NaN stays NaN: availability is unchanged
        assert perturbed.loc[future].notna().equals(returns.loc[future].notna())
        after = m5.membership(perturbed, evaluated)
        after_weights = m5.rule_weights(rule, after.in_set, after.sigma)
        pd.testing.assert_series_equal(after.in_set.loc[month], base.in_set.loc[month])
        pd.testing.assert_series_equal(after.sigma.loc[month], base.sigma.loc[month])
        pd.testing.assert_series_equal(after_weights.loc[month], base_weights.loc[month])
        earlier = evaluated[evaluated < month]
        pd.testing.assert_frame_equal(after_weights.loc[earlier], base_weights.loc[earlier])


def test_past_perturbation_changes_inverse_volatility_weights() -> None:
    returns = random_panel()
    evaluated = months("1993-01", "1993-01")
    changed = returns.copy()
    changed.loc["1992-12", "A"] += 0.2
    before = m5.membership(returns, evaluated)
    after = m5.membership(changed, evaluated)
    assert m5.rule_weights("R1", after.in_set, after.sigma).loc["1993-01", "A"] != pytest.approx(
        m5.rule_weights("R1", before.in_set, before.sigma).loc["1993-01", "A"])


# Weights and membership --------------------------------------------------------

def test_inverse_volatility_weights_on_known_example() -> None:
    index = months("1990-01", "1993-01")
    sign = np.where(np.arange(len(index)) % 2 == 0, 1.0, -1.0)
    returns = pd.DataFrame({"A": 0.01 * sign, "B": 0.02 * sign}, index=index)
    member = m5.membership(returns, months("1993-01", "1993-01"))
    assert member.sigma.loc["1993-01", "A"] == pytest.approx(0.01 * math.sqrt(36 / 35), rel=1e-12)
    assert member.sigma.loc["1993-01", "B"] == pytest.approx(0.02 * math.sqrt(36 / 35), rel=1e-12)
    r1 = m5.rule_weights("R1", member.in_set, member.sigma).loc["1993-01"]
    r0 = m5.rule_weights("R0", member.in_set, member.sigma).loc["1993-01"]
    assert r1.to_dict() == pytest.approx({"A": 2 / 3, "B": 1 / 3}, rel=1e-12)
    assert r0.to_dict() == pytest.approx({"A": 0.5, "B": 0.5})


def test_minimum_observations_and_typed_missing_are_counted_never_filled() -> None:
    index = months("1990-01", "1993-02")
    rng = np.random.default_rng(3)
    returns = pd.DataFrame(rng.normal(0, 0.01, size=(len(index), 4)), index=index,
                           columns=["full", "has24", "has23", "no_t"])
    returns.loc["1990-01":"1990-12", "has24"] = np.nan   # 24 of 36 prior months remain for 1993-01
    returns.loc["1990-01":"1991-01", "has23"] = np.nan   # 23 remain
    returns.loc["1993-01", "no_t"] = np.nan
    missing = pd.DataFrame(PRESENT, index=index, columns=returns.columns, dtype=object)
    missing[returns.isna()] = MISSING_ABSENT
    missing.loc["1993-01", "no_t"] = MISSING_CODE
    snapshot = returns.copy()
    member = m5.membership(returns, months("1993-01", "1993-02"))
    assert member.in_set.loc["1993-01"].to_dict() == {"full": True, "has24": True, "has23": False, "no_t": False}
    assert math.isnan(member.sigma.loc["1993-01", "has23"])
    assert member.in_set.loc["1993-02", "has23"]
    bounds = {"full": (pd.Period("1993-01", freq="M"), pd.Period("1993-02", freq="M"))}
    counts = m5.membership_counts(member, missing, bounds)["full"]
    assert counts["factor_months_declared"] == 8
    assert counts["factor_months_in_set"] == 6
    assert counts["excluded_no_return_in_month"] == 1
    assert counts["excluded_fewer_than_24_prior_returns"] == 1
    assert counts["excluded_both_conditions"] == 0
    assert counts["typed_missing_by_reason"] == {MISSING_CODE: 1}
    weights = m5.rule_weights("R1", member.in_set, member.sigma)
    m5.portfolio(weights, returns, 20)
    pd.testing.assert_frame_equal(returns, snapshot)
    assert m5.missing_by_month(missing.loc["1993-01":"1993-02"]) == {"1993-01": {MISSING_CODE: 1}}
    assert m5.typed_missing_counts(missing.loc[:"1992-12"]) == {MISSING_ABSENT: 12 + 13}


def test_empty_set_and_degenerate_sigma_refuse() -> None:
    index = months("1993-01", "1993-02")
    in_set = pd.DataFrame({"A": [True, False], "B": [True, False]}, index=index)
    sigma = pd.DataFrame({"A": [0.01, 0.01], "B": [0.02, 0.02]}, index=index)
    with pytest.raises(PublicDataRefusal, match="empty set"):
        m5.rule_weights("R0", in_set, sigma)
    in_set.loc["1993-02"] = True
    sigma.loc["1993-02", "B"] = 0.0
    with pytest.raises(PublicDataRefusal, match="zero or non-finite sigma"):
        m5.rule_weights("R1", in_set, sigma)
    assert m5.rule_weights("R0", in_set, sigma).loc["1993-02"].tolist() == [0.5, 0.5]


# Costs ------------------------------------------------------------------------

def test_switch_cost_arithmetic_with_entering_and_leaving_factors() -> None:
    index = months("2000-01", "2000-03")
    in_set = pd.DataFrame({"A": [True, True, True], "B": [True, True, False], "C": [False, True, True]},
                          index=index)
    sigma = pd.DataFrame(0.01, index=index, columns=in_set.columns)
    returns = pd.DataFrame({"A": [0.01, 0.02, 0.03], "B": [0.02, -0.01, np.nan], "C": [np.nan, 0.04, -0.02]},
                           index=index)
    weights = m5.rule_weights("R0", in_set, sigma)
    book = m5.portfolio(weights, returns, 20)
    assert book["turnover"].tolist() == pytest.approx([1.0, 2 / 3, 2 / 3])
    gross = [0.015, (0.02 - 0.01 + 0.04) / 3, (0.03 - 0.02) / 2]
    assert book["gross"].tolist() == pytest.approx(gross)
    assert book["net"].tolist() == pytest.approx([g - 0.002 * t for g, t in zip(gross, [1.0, 2 / 3, 2 / 3])])
    high = m5.portfolio(weights, returns, 50)
    assert (book["net"] - high["net"]).tolist() == pytest.approx([0.003, 0.002, 0.002])


def test_missing_return_for_a_held_factor_refuses() -> None:
    index = months("2000-01", "2000-01")
    weights = pd.DataFrame({"A": [1.0]}, index=index)
    with pytest.raises(PublicDataRefusal, match="missing return"):
        m5.portfolio(weights, pd.DataFrame({"A": [np.nan]}, index=index), 20)


# Metrics --------------------------------------------------------------------

def test_max_drawdown_worst_12_month_and_moments_on_known_path() -> None:
    values = [0.10, -0.20, 0.05] + [0.0] * 21
    net = pd.Series(values, index=months("2000-01", "2001-12"))
    result = m5.performance(net, pd.Series(0.5, index=net.index))
    assert result["max_drawdown"] == pytest.approx(0.88 / 1.1 - 1)
    assert result["worst_12_month_return"] == pytest.approx(0.8 * 1.05 - 1)
    assert result["annualized_mean"] == pytest.approx(12 * np.mean(values))
    assert result["volatility"] == pytest.approx(math.sqrt(12) * np.std(values, ddof=1))
    assert result["sharpe"] == pytest.approx(result["annualized_mean"] / result["volatility"])
    assert result["average_monthly_turnover"] == 0.5
    first_loss = m5.performance(pd.Series([-0.10, 0.05, 0.05], index=months("2000-01", "2000-03")))
    assert first_loss["max_drawdown"] == pytest.approx(-0.10)
    assert first_loss["worst_12_month_return"] is None


def test_halves_split_is_rebased_and_uses_the_continuous_run() -> None:
    net = pd.Series([-0.3] * 3 + [0.0] * 21 + [0.02, -0.01, -0.01] + [0.0] * 21,
                    index=months("1998-01", "2001-12"))
    bounds = m5.period_bounds(trial_like("1998-01", "1999-12"), net.index[-1])
    assert bounds == {"full": (pd.Period("1998-01", "M"), pd.Period("2001-12", "M")),
                      "first_half": (pd.Period("1998-01", "M"), pd.Period("1999-12", "M")),
                      "second_half": (pd.Period("2000-01", "M"), pd.Period("2001-12", "M"))}
    second = m5.performance(net.loc[bounds["second_half"][0]:bounds["second_half"][1]])
    assert second["months"] == 24
    assert second["max_drawdown"] == pytest.approx(0.99 * 0.99 - 1)
    full = m5.performance(net.loc[bounds["full"][0]:bounds["full"][1]])
    assert full["max_drawdown"] == pytest.approx(0.7 ** 3 * 1.02 * 0.99 ** 2 - 1)


def test_volatility_forecast_accuracy_counts_pairs_and_exclusions() -> None:
    returns = random_panel(seed=5)
    evaluated = months("1993-01", "1996-12")
    member = m5.membership(returns, evaluated)
    realized = m5.realized_volatility(returns.loc[:"1996-12"], evaluated)
    bounds = m5.period_bounds(trial_like(), evaluated[-1])
    result = m5.volatility_accuracy(member.sigma, realized, member.in_set, bounds)
    full = result["full"]
    assert full["excluded_window_past_last_month"] == int(member.in_set.loc["1996-02":].to_numpy().sum())
    assert (full["pairs"] + full["excluded_window_past_last_month"]
            + full["excluded_incomplete_realized_window"]) == int(member.in_set.to_numpy().sum())
    assert full["excluded_incomplete_realized_window"] > 0
    assert -1.0 <= full["spearman"] <= 1.0
    assert result["first_half"]["pairs"] + result["second_half"]["pairs"] == full["pairs"]
    assert math.isnan(realized.loc["1996-02", "A"])
    assert realized.loc["1993-01", "A"] == pytest.approx(returns.loc["1993-01":"1993-12", "A"].std(ddof=1))


# Tests and decision -------------------------------------------------------------

def grid_with(sharpe: dict, drawdown: dict) -> dict:
    grid = {}
    for rule in ("R0", "R1"):
        grid[rule] = {}
        for cost in (20, 50):
            grid[rule][f"{cost}bp"] = {period: {"sharpe": sharpe[rule], "max_drawdown": drawdown[rule]}
                                       for period in ("full", "first_half", "second_half")}
    return grid


def test_decision_rule_on_constructed_inputs() -> None:
    better = grid_with({"R0": 0.7, "R1": 0.9}, {"R0": -0.14, "R1": -0.08})
    decision = m5.decide(better, [20, 50])
    assert decision["outcome"] == "R1" and decision["conditions_held"] == 8
    assert len(decision["conditions"]) == 8
    ties = grid_with({"R0": 0.8, "R1": 0.8}, {"R0": -0.1, "R1": -0.1})
    assert m5.decide(ties, [20, 50])["outcome"] == "R1"
    one_fails = grid_with({"R0": 0.7, "R1": 0.9}, {"R0": -0.14, "R1": -0.08})
    one_fails["R1"]["50bp"]["second_half"]["sharpe"] = 0.69
    decided = m5.decide(one_fails, [20, 50])
    assert decided["outcome"] == "R0" and decided["conditions_held"] == 7
    deeper = grid_with({"R0": 0.7, "R1": 0.9}, {"R0": -0.14, "R1": -0.08})
    deeper["R1"]["20bp"]["first_half"]["max_drawdown"] = -0.15
    assert m5.decide(deeper, [20, 50])["outcome"] == "R0"
    full_only = grid_with({"R0": 0.7, "R1": 0.9}, {"R0": -0.14, "R1": -0.08})
    full_only["R1"]["20bp"]["full"]["sharpe"] = 0.1
    assert m5.decide(full_only, [20, 50])["outcome"] == "R1"
    assert m5.decide(None, [20, 50])["outcome"] == "refused"


def test_s2_tests_use_hac_pvalues_and_by_adjustment_over_three() -> None:
    rng = np.random.default_rng(2)
    index = months("1972-01", "2001-12")
    series = {"S2.a": pd.Series(rng.normal(0.002, 0.01, len(index)), index=index),
              "S2.b": pd.Series(rng.normal(0.0, 0.01, len(index)), index=index), "S2.c": None}
    result = m5.s2_tests(series, 3)
    expected_p = {k: return_test_statistics(v, periods_per_year=12)["hac_pvalue"] for k, v in series.items() if v is not None}
    expected_q = adjust_pvalues(pd.Series({**expected_p, "S2.c": np.nan}), method="by", family_size=3)
    for key in ("S2.a", "S2.b"):
        assert result[key]["hac_pvalue"] == expected_p[key]
        assert result[key]["by_qvalue"] == pytest.approx(expected_q[key])
        assert result[key]["by_qvalue"] >= result[key]["hac_pvalue"]
    assert result["S2.c"]["status"] == "universe_refused" and result["S2.c"]["by_qvalue"] is None


def test_post_publication_split_starts_at_first_non_empty_month_and_refuses_later_gaps() -> None:
    returns = random_panel()
    evaluated = months("1993-01", "1996-12")
    member = m5.membership(returns, evaluated)
    universe = {"_member": member, "_returns": returns.loc[:"1996-12"]}
    years = {"A": 1990, "B": 1993, "C": 1995, "D": None}
    result = m5.post_publication(universe, years, trial_like(), [20, 50])
    assert result["status"] == "completed"
    assert result["counts"]["full"]["excluded_missing_publication_year"] == int(member.in_set["D"].sum())
    late = {"A": 1993, "B": 1994, "C": 1995, "D": None}
    started = m5.post_publication(universe, late, trial_like(), [20, 50])
    assert started["status"] == "completed" and started["start_month"] == "1994-01"
    assert started["empty_subset_months"] == {"count": 12, "first": "1993-01", "last": "1993-12"}
    assert started["rules"]["R0"]["20bp"]["first_half"]["months"] == 12
    assert started["rules"]["R1"]["50bp"]["full"]["months"] == 36
    assert started["rules"]["R0"]["20bp"]["second_half"]["months"] == 24
    # Entry turnover is charged in the start month, not in the leading empty months.
    assert started["rules"]["R0"]["20bp"]["first_half"]["average_monthly_turnover"] >= 1 / 12
    gap = returns.copy()
    gap.loc["1995-03", "A"] = np.nan
    gapped = {"_member": m5.membership(gap, evaluated), "_returns": gap.loc[:"1996-12"]}
    refused = m5.post_publication(gapped, {"A": 1992, "B": 2000, "C": 2000, "D": None}, trial_like(), [20])
    assert refused["status"] == "refused" and "empty set" in refused["reason"]
    assert refused["start_month"] == "1993-01"
    never = m5.post_publication(universe, {"A": 2000, "B": 2000, "C": 2000, "D": None}, trial_like(), [20])
    assert never["status"] == "refused" and never["empty_subset_months"]["count"] == 48
    wrong = m5.post_publication(universe, {"A": 1990, "B": None, "C": 1990, "D": None}, trial_like(), [20])
    assert wrong["status"] == "refused" and "differ from the declared list" in wrong["reason"]


def test_run_universe_and_report_on_a_synthetic_panel() -> None:
    returns = random_panel()
    missing = pd.DataFrame(PRESENT, index=returns.index, columns=returns.columns, dtype=object)
    missing[returns.isna()] = MISSING_ABSENT
    panel = MonthlyPanel(returns, missing, 0)
    market = pd.Series(0.005, index=months("1985-01", "1996-12"))
    market.iloc[::2] = -0.003
    first, last = pd.Period("1993-01", "M"), pd.Period("1996-12", "M")
    universe = m5.run_universe(panel, first, last, trial_like(), market, [20, 50])
    assert universe["status"] == "completed"
    assert universe["rules"]["R1"]["20bp"]["full"]["months"] == 48
    assert universe["rules"]["R0"]["20bp"]["first_half"]["months"] == 24
    assert universe["lookback_typed_missing"] == {
        "months": "1990-01 to 1992-12",
        "by_reason": {MISSING_ABSENT: int(returns.loc[:"1992-12"].isna().to_numpy().sum())},
    }
    diff = universe["_series"][("R1", 20)] - universe["_series"][("R0", 20)]
    post = m5.post_publication(universe, {"A": 1980, "B": 1980, "C": 1980, "D": None}, trial_like(), [20, 50])
    for key in ("_series", "_member", "_returns"):
        universe.pop(key)
    result = {
        "run_utc": "2026-01-01T00:00:00Z", "git": {"commit": "abc", "tracked_changes": False},
        "evidence_ceiling": "DIAGNOSTIC_ONLY", "trial_file": "trial.json", "trial_file_sha256": "0" * 64,
        "timing": "after_month_end_signal_next_month_return", "switch_cost_bps": [20, 50],
        "manifest": [{"id": "x", "rows": 1, "first_date": None, "last_date": None, "sha256": "f" * 64,
                      "retrieved_utc": "2026-01-01T00:00:00Z"}],
        "universes": {m5.PRIMARY_UNIVERSE: universe},
        "s2_tests": m5.s2_tests({f"S2.{m5.PRIMARY_UNIVERSE}": diff}, 3),
        "decision": m5.decide(universe["rules"], [20, 50]), "post_publication": post,
    }
    text = m5.render_report(result)
    json.dumps(result)
    assert "Evidence ceiling: DIAGNOSTIC_ONLY" in text
    assert "## Limitations" in text and "## Data Manifest" in text
    assert text.isascii()


# Trial file ---------------------------------------------------------------------

def test_trial_file_must_equal_its_committed_head_version(tmp_path: Path) -> None:
    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@example.com",
                        *args], check=True, capture_output=True)
    git("init", "-q")
    trial = tmp_path / "docs" / "trial.json"
    trial.parent.mkdir()
    trial.write_text('{"a": 1}\n', encoding="utf-8")
    with pytest.raises(PublicDataRefusal, match="not committed"):
        m5.verify_trial_file(tmp_path, "docs/trial.json")
    git("add", "docs/trial.json")
    git("commit", "-q", "-m", "trial")
    content, digest = m5.verify_trial_file(tmp_path, "docs/trial.json")
    assert content == b'{"a": 1}\n' and len(digest) == 64
    trial.write_text('{"a": 2}\n', encoding="utf-8")
    with pytest.raises(PublicDataRefusal, match="differs from its committed HEAD"):
        m5.verify_trial_file(tmp_path, "docs/trial.json")


def test_committed_trial_file_matches_the_pinned_sha256() -> None:
    _, digest = m5.verify_trial_file(m5.REPO_ROOT, m5.TRIAL_PATH)
    assert digest == m5.TRIAL_SHA256
    _, amendment = m5.verify_trial_file(m5.REPO_ROOT, m5.AMENDMENT_PATH)
    assert amendment == m5.AMENDMENT_SHA256


# Parsers --------------------------------------------------------------------

def write_zip(path: Path, member: str, text: str) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(member, text)
    return path


FRENCH_TEXT = """This file was created using the 202608 CRSP database.
It contains a factor, constructed from portfolios, as a test.
Missing data are indicated by -99.99 or -999.

,Mkt-RF,SMB,RF
196307,   -0.39,   -0.48,    0.27
196308,    5.07,  -99.99,    0.25
196309,   -1.57,   -0.30,  -999
196311,    1.00,    2.00,    0.30

 Annual Factors: January-December
,Mkt-RF,SMB,RF
  1964,   12.00,    1.00,    3.50
196401,    9.00,    9.00,    9.00

Copyright 2026 Eugene F. Fama and Kenneth R. French
"""


def test_french_parser_reads_the_monthly_block_only_with_typed_missing(tmp_path: Path) -> None:
    path = write_zip(tmp_path / "f.zip", "F.csv", FRENCH_TEXT)
    panel = read_french_monthly_zip(path, "F.csv", columns=["Mkt-RF", "SMB", "RF"])
    assert panel.n_rows == 4
    assert list(panel.values.index.astype(str)) == ["1963-07", "1963-08", "1963-09", "1963-10", "1963-11"]
    assert panel.values.loc["1963-07", "Mkt-RF"] == pytest.approx(-0.0039)
    assert panel.values.loc["1963-11", "SMB"] == pytest.approx(0.02)
    assert math.isnan(panel.values.loc["1963-08", "SMB"]) and panel.missing.loc["1963-08", "SMB"] == MISSING_CODE
    assert panel.missing.loc["1963-09", "RF"] == MISSING_CODE
    assert panel.missing.loc["1963-10"].tolist() == [MISSING_ABSENT] * 3
    assert panel.missing.loc["1963-07"].tolist() == [PRESENT] * 3
    assert "1964-01" not in panel.values.index.astype(str)


def test_french_parser_refuses_repeats_and_non_numeric_fields(tmp_path: Path) -> None:
    repeated = FRENCH_TEXT.replace("196311,", "196309,")
    with pytest.raises(PublicDataRefusal, match="repeats"):
        read_french_monthly_zip(write_zip(tmp_path / "a.zip", "F.csv", repeated), "F.csv", columns=["SMB"])
    garbled = FRENCH_TEXT.replace("   -0.30,", "   abc,")
    with pytest.raises(PublicDataRefusal, match="non-numeric"):
        read_french_monthly_zip(write_zip(tmp_path / "b.zip", "F.csv", garbled), "F.csv", columns=["SMB"])
    with pytest.raises(PublicDataRefusal, match="lacks"):
        read_french_monthly_zip(write_zip(tmp_path / "c.zip", "F.csv", FRENCH_TEXT), "F.csv", columns=["HML"])


JKP_COLUMNS = ["location", "name", "freq", "weighting", "direction", "n_stocks", "n_stocks_min", "date", "ret"]


def jkp_text(rows: list[tuple[str, str, str]], weighting: str = "vw_cap") -> str:
    body = [",".join(JKP_COLUMNS)]
    body += [f"usa,{name},monthly,{weighting},1,100,20,{date},{ret}" for name, date, ret in rows]
    return "\n".join(body) + "\n"


JKP_ROWS = [("a", "2000-01-31", "0.01"), ("a", "2000-02-29", ""), ("a", "2000-03-31", "-0.02"),
            ("b", "2000-01-31", "0.03"), ("b", "2000-03-31", "0.04")]


def test_jkp_parser_pivots_long_rows_with_typed_missing(tmp_path: Path) -> None:
    path = write_zip(tmp_path / "j.zip", "j.csv", jkp_text(JKP_ROWS))
    panel = read_jkp_zip(path, "j.csv", columns=JKP_COLUMNS, expected_names={"a", "b"})
    assert panel.n_rows == 5
    assert panel.values.loc["2000-03", "a"] == pytest.approx(-0.02)
    assert panel.missing.loc["2000-02", "a"] == MISSING_BLANK
    assert panel.missing.loc["2000-02", "b"] == MISSING_ABSENT
    assert panel.values.loc["2000-02"].isna().all()


@pytest.mark.parametrize("text, names, message", [
    (jkp_text(JKP_ROWS + [("b", "2000-03-15", "0.05")]), {"a", "b"}, "duplicate"),
    (jkp_text(JKP_ROWS), {"a", "b", "c"}, "name set differs"),
    (jkp_text(JKP_ROWS, weighting="ew"), {"a", "b"}, "weighting"),
    (jkp_text(JKP_ROWS).replace(",ret\n", ",return\n", 1), {"a", "b"}, "header"),
    (jkp_text(JKP_ROWS).replace("0.03", "x"), {"a", "b"}, "non-numeric"),
])
def test_jkp_parser_fail_closed_checks(tmp_path: Path, text: str, names: set[str], message: str) -> None:
    path = write_zip(tmp_path / "j.zip", "j.csv", text)
    with pytest.raises(PublicDataRefusal, match=message):
        read_jkp_zip(path, "j.csv", columns=JKP_COLUMNS, expected_names=names)


def test_fred_loader_types_blank_values(tmp_path: Path) -> None:
    path = tmp_path / "fred.csv"
    path.write_text("observation_date,BAA,AAA\n1990-01-01,9.50,8.90\n1990-02-01,.,9.00\n", encoding="utf-8")
    panel = read_fred_csv(path, series=["BAA", "AAA"])
    assert panel.values.loc["1990-01", "BAA"] == 9.5
    assert panel.missing.loc["1990-02", "BAA"] == MISSING_BLANK
    path.write_text("observation_date,BAA,AAA\n1990-01-15,9.50,8.90\n", encoding="utf-8")
    with pytest.raises(PublicDataRefusal, match="first day"):
        read_fred_csv(path, series=["BAA", "AAA"])


def test_publication_years_from_a_minimal_xlsx(tmp_path: Path) -> None:
    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    shared = ["abr_jkp", "cite", "beta_60m", "Fama and MacBeth (1973)", "op_at", "Ball et al. (forthcoming)"]
    cells = [("A1", 0, "B1", 1), ("A2", 2, "B2", 3), ("A3", 4, "B3", 5)]
    rows = "".join(f'<row><c r="{a}" t="s"><v>{i}</v></c><c r="{b}" t="s"><v>{j}</v></c></row>'
                   for a, i, b, j in cells)
    rows += '<row><c r="A4" t="inlineStr"><is><t>be_me</t></is></c><c r="B4" t="inlineStr"><is><t>R (1985)</t></is></c></row>'
    path = tmp_path / "details.xlsx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", f'<workbook xmlns="{main}" xmlns:r="{rel}"><sheets>'
                         '<sheet name="other" sheetId="1" r:id="rId1"/><sheet name="details" sheetId="2" r:id="rId2"/>'
                         '</sheets></workbook>')
        archive.writestr("xl/_rels/workbook.xml.rels",
                         '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                         '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/>'
                         '<Relationship Id="rId2" Target="worksheets/sheet2.xml"/></Relationships>')
        archive.writestr("xl/sharedStrings.xml", f'<sst xmlns="{main}">'
                         + "".join(f"<si><t>{s}</t></si>" for s in shared) + "</sst>")
        archive.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="{main}"><sheetData/></worksheet>')
        archive.writestr("xl/worksheets/sheet2.xml",
                         f'<worksheet xmlns="{main}"><sheetData>{rows}</sheetData></worksheet>')
    assert read_publication_years(path) == {"beta_60m": 1973, "op_at": None, "be_me": 1985}
    assert publication_year("Novy-Marx (2013) and Fama (2015)") == 2013
    assert publication_year(None) is None


# Download cache and manifest ----------------------------------------------------

def test_fetch_downloads_once_and_refuses_a_tampered_cache(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    source.write_bytes(b"x,y\n1,2\n")
    url = source.as_uri()
    target = tmp_path / "cache" / "file.csv"
    first = fetch(url, target)
    assert target.read_bytes() == b"x,y\n1,2\n" and first.n_bytes == 8
    source.unlink()
    second = fetch(url, target)
    assert second.sha256 == first.sha256 and second.retrieved_utc == first.retrieved_utc
    with pytest.raises(PublicDataRefusal, match="another URL"):
        fetch(url + "?v=2", target)
    target.write_bytes(b"tampered")
    with pytest.raises(PublicDataRefusal, match="SHA-256"):
        fetch(url, target)


def test_manifest_records_provenance_without_rows(tmp_path: Path) -> None:
    source = tmp_path / "s.csv"
    source.write_bytes(b"a\n")
    cached = fetch(source.as_uri(), tmp_path / "cache" / "s.csv")
    entry = manifest_entry("s", cached, rows=1, first="2000-01", last="2000-02")
    assert set(entry) == {"id", "url", "retrieved_utc", "sha256", "bytes", "rows", "first_date", "last_date"}
    out = tmp_path / "manifest.json"
    write_manifest(out, [entry], notes={"trial_file_sha256": "0" * 64})
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["sources"] == [entry] and payload["trial_file_sha256"] == "0" * 64


def test_public_cache_is_gitignored() -> None:
    result = subprocess.run(["git", "-C", str(m5.REPO_ROOT), "check-ignore", "-q", "data/public_cache/x.zip"],
                            check=False)
    assert result.returncode == 0


def test_universe_panel_types_added_months_absent() -> None:
    index = months("1970-01", "1972-03")
    values = pd.DataFrame({"A": np.arange(len(index), dtype=float)}, index=index)
    missing = pd.DataFrame(PRESENT, index=index, columns=["A"], dtype=object)
    frame, reasons = m5.universe_panel(values, missing, pd.Period("1972-01", "M"), pd.Period("1972-02", "M"))
    assert frame.index[0] == pd.Period("1969-01", "M") and frame.index[-1] == pd.Period("1972-02", "M")
    assert reasons.loc["1969-01", "A"] == MISSING_ABSENT and reasons.loc["1970-01", "A"] == PRESENT
