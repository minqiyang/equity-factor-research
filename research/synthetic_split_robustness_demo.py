"""Synthetic split-aware robustness diagnostic demo.

This module reports every configured synthetic signal case across
train/validation/test windows. It does not fetch data, use real market data,
select factors, choose parameters, run a backtest, write generated reports,
place orders, support live trading, or make profitability claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from features.diagnostics import (
    factor_information_coefficient,
    factor_rank_information_coefficient,
)
from features.validation import (
    TrainValidationTestSplit,
    make_train_validation_test_split,
    split_panel_by_train_validation_test,
)
from research.synthetic_split_ic_rank_ic_demo import (
    SyntheticSplitICRankICConfig,
    generate_synthetic_factor_panel,
    generate_synthetic_forward_returns,
)

SPLIT_NAMES = ("train", "validation", "test")
SUPPORTED_TRANSFORMS = {"identity", "inverse", "constant"}
SyntheticTransform = Literal["identity", "inverse", "constant"]


@dataclass(frozen=True)
class SyntheticRobustnessCase:
    """One deterministic synthetic signal case."""

    case_id: str
    transform: SyntheticTransform


@dataclass(frozen=True)
class SyntheticSplitRobustnessConfig:
    """Configuration for the split-aware robustness diagnostic demo."""

    base_config: SyntheticSplitICRankICConfig = SyntheticSplitICRankICConfig()
    cases: tuple[SyntheticRobustnessCase, ...] = (
        SyntheticRobustnessCase("base_signal", "identity"),
        SyntheticRobustnessCase("inverse_signal", "inverse"),
        SyntheticRobustnessCase("constant_signal", "constant"),
    )


@dataclass(frozen=True)
class SyntheticSplitRobustnessResult:
    """Container for synthetic split-aware robustness outputs."""

    config: SyntheticSplitRobustnessConfig
    base_factor: pd.DataFrame
    forward_returns: pd.DataFrame
    split: TrainValidationTestSplit
    factor_cases: dict[str, pd.DataFrame]
    summary: pd.DataFrame
    assumptions: dict[str, object]

    @property
    def reported_case_count(self) -> int:
        """Return the number of configured cases included in the summary."""

        return len(self.factor_cases)

    @property
    def invalid_case_count(self) -> int:
        """Return the number of case/split rows without valid diagnostics."""

        return int(self.summary["invalid_reason"].notna().sum())


def run_synthetic_split_robustness_demo(
    config: SyntheticSplitRobustnessConfig = SyntheticSplitRobustnessConfig(),
) -> SyntheticSplitRobustnessResult:
    """Run a deterministic all-case split-aware robustness diagnostic."""

    _validate_config(config)
    base_factor = generate_synthetic_factor_panel(config.base_config)
    split = make_train_validation_test_split(
        base_factor.index,
        train_end=config.base_config.train_end,
        validation_end=config.base_config.validation_end,
        test_end=config.base_config.test_end,
    )
    forward_returns = generate_synthetic_forward_returns(base_factor, split)
    factor_cases = build_synthetic_robustness_cases(
        base_factor=base_factor,
        cases=config.cases,
    )
    summary = summarize_synthetic_split_robustness(
        factor_cases=factor_cases,
        forward_returns=forward_returns,
        split=split,
        min_periods=config.base_config.ic_min_periods,
    )

    return SyntheticSplitRobustnessResult(
        config=config,
        base_factor=base_factor,
        forward_returns=forward_returns,
        split=split,
        factor_cases=factor_cases,
        summary=summary,
        assumptions=build_synthetic_robustness_assumptions(config),
    )


def build_synthetic_robustness_cases(
    *,
    base_factor: pd.DataFrame,
    cases: tuple[SyntheticRobustnessCase, ...],
) -> dict[str, pd.DataFrame]:
    """Build deterministic synthetic signal panels for every configured case."""

    _validate_cases(cases)
    factor_cases: dict[str, pd.DataFrame] = {}
    for case in cases:
        if case.transform == "identity":
            factor_cases[case.case_id] = base_factor.copy()
        elif case.transform == "inverse":
            factor_cases[case.case_id] = -base_factor
        elif case.transform == "constant":
            constant_factor = pd.DataFrame(
                1.0,
                index=base_factor.index,
                columns=base_factor.columns,
            )
            factor_cases[case.case_id] = constant_factor.where(base_factor.notna())
        else:  # pragma: no cover - guarded by _validate_cases.
            raise ValueError(f"unsupported transform: {case.transform}")

    return factor_cases


def summarize_synthetic_split_robustness(
    *,
    factor_cases: dict[str, pd.DataFrame],
    forward_returns: pd.DataFrame,
    split: TrainValidationTestSplit,
    min_periods: int,
) -> pd.DataFrame:
    """Summarize every configured case across every split."""

    if not factor_cases:
        raise ValueError("factor_cases must not be empty")

    forward_returns_by_split = split_panel_by_train_validation_test(
        forward_returns,
        split,
        name="forward_returns",
    )
    records: list[dict[str, object]] = []
    for case_order, (case_id, factor) in enumerate(factor_cases.items()):
        factor_by_split = split_panel_by_train_validation_test(
            factor,
            split,
            name=f"factor_cases[{case_id!r}]",
        )
        for split_order, split_name in enumerate(SPLIT_NAMES):
            split_factor = factor_by_split[split_name]
            split_returns = forward_returns_by_split[split_name]
            if _has_any_valid_cross_sectional_variation(
                split_factor,
                split_returns,
                min_periods=min_periods,
            ):
                information_coefficient = factor_information_coefficient(
                    split_factor,
                    split_returns,
                    min_periods=min_periods,
                )
                rank_information_coefficient = factor_rank_information_coefficient(
                    split_factor,
                    split_returns,
                    min_periods=min_periods,
                )
            else:
                information_coefficient = _empty_diagnostic_series(
                    split_factor.index,
                    name="information_coefficient",
                )
                rank_information_coefficient = _empty_diagnostic_series(
                    split_factor.index,
                    name="rank_information_coefficient",
                )
            ic_valid_dates = int(information_coefficient.notna().sum())
            rank_ic_valid_dates = int(rank_information_coefficient.notna().sum())
            records.append(
                {
                    "case_id": case_id,
                    "split": split_name,
                    "case_order": case_order,
                    "split_order": split_order,
                    "split_start": split_factor.index.min().date().isoformat(),
                    "split_end": split_factor.index.max().date().isoformat(),
                    "date_count": int(len(split_factor.index)),
                    "asset_count": int(split_factor.shape[1]),
                    "factor_valid_observations": int(
                        split_factor.notna().sum().sum()
                    ),
                    "forward_return_valid_observations": int(
                        split_returns.notna().sum().sum()
                    ),
                    "ic_valid_dates": ic_valid_dates,
                    "rank_ic_valid_dates": rank_ic_valid_dates,
                    "mean_ic": _mean_or_nan(information_coefficient),
                    "mean_rank_ic": _mean_or_nan(rank_information_coefficient),
                    "invalid_reason": _invalid_reason(
                        ic_valid_dates,
                        rank_ic_valid_dates,
                    ),
                }
            )

    summary = pd.DataFrame.from_records(records)
    return summary.set_index(["case_id", "split"]).sort_values(
        ["case_order", "split_order"],
    )


def build_synthetic_robustness_assumptions(
    config: SyntheticSplitRobustnessConfig,
) -> dict[str, object]:
    """Return separately inspectable assumptions for the synthetic demo."""

    return {
        "data_scope": "synthetic only",
        "source_artifacts": ["research/synthetic_split_robustness_demo.py"],
        "synthetic_seed": "deterministic formula; no random seed",
        "split_policy": "chronological train/validation/test windows",
        "parameter_grid": [
            {"case_id": case.case_id, "transform": case.transform}
            for case in config.cases
        ],
        "target_return_definition": "synthetic forward-return evaluation target",
        "signal_lag": "not applicable; deterministic aligned diagnostic inputs",
        "benchmark_assumption": "not included",
        "rebalance_frequency": "not included",
        "execution_timing": "not included",
        "transaction_cost_bps": 0.0,
        "slippage_bps": 0.0,
        "volume_aware_slippage_mode": "absent",
        "portfolio_construction": "not included",
        "backtest_integration": "not included",
        "live_trading": False,
        "paper_trading": False,
        "brokerage_integration": False,
        "order_execution": False,
        "profitability_claim": False,
    }


def _validate_config(config: SyntheticSplitRobustnessConfig) -> None:
    if not isinstance(config, SyntheticSplitRobustnessConfig):
        raise TypeError("config must be a SyntheticSplitRobustnessConfig")

    if not isinstance(config.base_config, SyntheticSplitICRankICConfig):
        raise TypeError("base_config must be a SyntheticSplitICRankICConfig")

    _validate_cases(config.cases)


def _validate_cases(cases: tuple[SyntheticRobustnessCase, ...]) -> None:
    if not isinstance(cases, tuple):
        raise TypeError("cases must be a tuple")

    if not cases:
        raise ValueError("cases must not be empty")

    seen_case_ids: set[str] = set()
    for case in cases:
        if not isinstance(case, SyntheticRobustnessCase):
            raise TypeError("cases must contain SyntheticRobustnessCase values")

        if not case.case_id:
            raise ValueError("case_id must not be empty")

        if case.case_id in seen_case_ids:
            raise ValueError(f"duplicate case_id: {case.case_id}")
        seen_case_ids.add(case.case_id)

        if case.transform not in SUPPORTED_TRANSFORMS:
            raise ValueError(f"unsupported transform: {case.transform}")


def _mean_or_nan(series: pd.Series) -> float:
    value = series.mean()
    return float(value) if not pd.isna(value) else np.nan


def _has_any_valid_cross_sectional_variation(
    factor: pd.DataFrame,
    forward_returns: pd.DataFrame,
    *,
    min_periods: int,
) -> bool:
    for date in factor.index:
        factor_row = factor.loc[date]
        returns_row = forward_returns.loc[date]
        valid_pair = factor_row.notna() & returns_row.notna()
        if int(valid_pair.sum()) < min_periods:
            continue
        if (
            factor_row[valid_pair].nunique(dropna=True) >= 2
            and returns_row[valid_pair].nunique(dropna=True) >= 2
        ):
            return True
    return False


def _empty_diagnostic_series(index: pd.DatetimeIndex, *, name: str) -> pd.Series:
    return pd.Series(np.nan, index=index, name=name)


def _invalid_reason(ic_valid_dates: int, rank_ic_valid_dates: int) -> str | None:
    if ic_valid_dates == 0 and rank_ic_valid_dates == 0:
        return "no_valid_ic_or_rank_ic_dates"
    if ic_valid_dates == 0:
        return "no_valid_ic_dates"
    if rank_ic_valid_dates == 0:
        return "no_valid_rank_ic_dates"
    return None


def main() -> None:
    """Run the synthetic split-aware robustness demo without writing outputs."""

    run_synthetic_split_robustness_demo()


if __name__ == "__main__":
    main()
