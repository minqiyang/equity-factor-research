"""Shared run-family summaries for the synthetic and local-data diagnostics."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
from scipy.stats import t

from features.multiple_testing import METHODS, P_VALUE_FLOOR, adjust_pvalues, sharpe_haircut


def summarize_multiple_testing(
    inventory: list[dict[str, Any]], *, family_size: int | None = None,
) -> dict[str, Any]:
    """Retain every semantic trial and withhold conflicting repetitions."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in inventory:
        grouped.setdefault(record["trial_id"], []).append(record)
    rows = []
    for trial_id, attempts in sorted(grouped.items()):
        first = attempts[0]
        same = all(
            all(record.get(key) == first.get(key) for key in ("status", "specification", "sharpe", "return_test"))
            for record in attempts[1:]
        )
        statistics = first.get("return_test") or {"status": "unavailable_return_test"}
        if not same:
            statistics = {"status": "conflicting_attempts"}
        elif first["status"] != "completed":
            statistics = {"status": "failed_or_incomplete_attempt"}
        rows.append({
            "trial_id": trial_id, "specification": first["specification"],
            "attempt_count": len(attempts), "return_test": dict(statistics),
            "positive_mean": statistics.get("status") == "ok" and statistics["mean_return"] > 0,
            "adjusted_pvalues": {}, "rejections": {}, "iid_haircuts": {},
            "iid_bonferroni_t_hurdle": None, "iid_bonferroni_sharpe_hurdle": None,
        })
    size = len(rows) if family_size is None else family_size
    for basis in ("hac", "iid"):
        pvalues = pd.Series([
            row["return_test"].get(f"{basis}_pvalue")
            if row["return_test"]["status"] == "ok" else None for row in rows
        ], dtype=float)
        adjusted = {
            method: adjust_pvalues(pvalues, method=method, family_size=size)
            for method in METHODS
        }
        for index, row in enumerate(rows):
            row["adjusted_pvalues"][basis] = {
                method: float(values.iloc[index]) if pd.notna(values.iloc[index]) else None
                for method, values in adjusted.items()
            }
            row["rejections"][basis] = {
                method: value is not None and value <= 0.05
                for method, value in row["adjusted_pvalues"][basis].items()
            }
    for row in rows:
        statistics = row["return_test"]
        if statistics["status"] != "ok":
            continue
        count = statistics["n_observations"]
        annualization = statistics["periods_per_year"]
        row["iid_haircuts"] = {
            method: sharpe_haircut(
                statistics["observed_sharpe"], n_observations=count,
                adjusted_pvalue=value, periods_per_year=annualization,
            ) for method, value in row["adjusted_pvalues"]["iid"].items()
        }
        hurdle = float(t.isf(0.05 / (2 * size), count - 1))
        row["iid_bonferroni_t_hurdle"] = hurdle
        row["iid_bonferroni_sharpe_hurdle"] = hurdle * math.sqrt(annualization / count)
    return {
        "alpha": 0.05, "primary_basis": "hac", "primary_method": "by",
        "attempt_count": len(inventory), "distinct_trial_count": len(rows),
        "family_size": int(size), "additional_unavailable_hypotheses": int(size) - len(rows),
        "valid_trial_count": sum(row["return_test"]["status"] == "ok" for row in rows),
        "hac_by_rejections": sum(row["rejections"]["hac"]["by"] for row in rows),
        "positive_hac_by_rejections": sum(row["rejections"]["hac"]["by"] and row["positive_mean"] for row in rows),
        "null_hypothesis": "mean daily net book return equals zero; two-sided; zero risk-free rate",
        "family_scope": "all distinct factor, direction, weighting, and penalty trials in this run",
        "history_scope": "run-local observed family; total adaptive historical search remains unestablished",
        "unavailable_policy": "retain slots at p=1 internally; expose undefined inference as null",
        "dependence_assumptions": "HAC uses Bartlett truncation and asymptotic normal inference; BY accommodates arbitrary cross-trial dependence of valid marginal p-values; BH requires independence or PRDS",
        "haircut_assumptions": "observed-family IID Gaussian Student-t sensitivity; empirical-population Harvey-Liu calibration remains deferred",
        "pvalue_floor": P_VALUE_FLOOR, "rows": rows,
    }


def render_multiple_testing(summary: dict[str, Any]) -> str:
    """Render all trials with conditional inference and explicit unfavorable signs."""
    def number(value: float | None) -> str:
        return "undefined" if value is None else f"{value:.5g}"

    lines = [
        "## Multiple-testing diagnostics",
        "",
        f"Family: {summary['distinct_trial_count']} distinct trials from {summary['attempt_count']} attempts; "
        f"declared size {summary['family_size']}, including {summary['additional_unavailable_hypotheses']} "
        "additional unavailable hypotheses. Both directions and every evaluated weighting/penalty variant are included.",
        "",
        f"Primary diagnostic: two-sided HAC BY at 5%; {summary['hac_by_rejections']} rejections, "
        f"of which {summary['positive_hac_by_rejections']} have positive mean net return. "
        "A negative rejection identifies unfavorable performance. The null is zero mean net book return "
        "at a zero risk-free rate. Benchmark-relative alpha remains a separate question.",
        "",
        "HAC uses the existing automatic-lag Newey-West statistic and asymptotic normal p-values. "
        "BY accommodates arbitrary cross-trial dependence conditional on valid marginal p-values. "
        "Finite-sample calibration, temporal stationarity, lag truncation, and adaptive strategy construction "
        "limit that interpretation. BH assumes independence or PRDS. Bonferroni and Holm target FWER.",
        "",
        "IID Bonferroni Sharpe haircuts and t hurdles use a separate two-sided Gaussian Student-t sensitivity. "
        "Annualization uses sqrt(periods_per_year); negative Sharpe signs are retained. "
        "The empirical-population Harvey-Liu simulation and correlation calibration remain deferred. "
        "Machine-readable experiment metrics retain IID corrections and haircuts for all four methods.",
        "",
        f"Unavailable or conflicting trials retain their family slots and expose undefined inference. "
        f"The raw p-value resolution floor is {summary['pvalue_floor']:.6g}. "
        "This family covers the current run; total historical search remains unestablished. "
        "DSR remains the separately reported existing estimator. Evidence ceiling: DIAGNOSTIC_ONLY.",
        "",
        "| trial ID | factor | direction | weighting | penalty | T | status | HAC p | Bonferroni q | Holm q | BH q | BY q | BY reject | positive mean | IID observed SR | IID Bonferroni SR | haircut fraction | IID t hurdle |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in summary["rows"]:
        spec = row["specification"]
        parameters = spec.get("parameters", {})
        stats = row["return_test"]
        q = row["adjusted_pvalues"]["hac"]
        haircut = row["iid_haircuts"].get("bonferroni", {})
        cells = [
            row["trial_id"], spec.get("factor_id", "undefined"), spec.get("direction", "undefined"),
            parameters.get("weighting_scheme", "undefined"), str(parameters.get("turnover_penalty_lambda", "undefined")),
            str(stats.get("n_observations", "undefined")), stats["status"], number(stats.get("hac_pvalue")),
            *(number(q[method]) for method in METHODS), str(row["rejections"]["hac"]["by"]), str(row["positive_mean"]),
            number(stats.get("observed_sharpe")), number(haircut.get("adjusted_sharpe")),
            number(haircut.get("haircut_fraction")), number(row["iid_bonferroni_t_hurdle"]),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"
