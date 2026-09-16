"""Synthetic three-factor backtest demo.

This command is the M3-01 exploratory slice. It reuses Demo v0 synthetic
price dates and assets, the existing factor generator and 0.50 / 0.30 / 0.20
weights, existing winsorize/z-score/combine helpers, and the existing
long-only backtester. ``python -m research.demo_v0`` remains the official
Demo v0 command. ``python -m research.synthetic_multifactor_workflow_demo``
remains the feature-only workflow.

The three synthetic panels are artificial quality, reversal, and momentum
fixtures. They are distinct from Demo v0 12-1 momentum and from fundamentals.

Results are synthetic diagnostics only. They are not a profitability claim,
private-data run, or brokerage/order capability.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest.portfolio import (
    BacktestResult,
    capture_backtest_source_provenance,
    run_long_only_backtest,
)
from features.combine import combine_factors
from features.normalize import (
    cross_sectional_winsorize_factor,
    cross_sectional_zscore_factor,
)
from features.operators import validate_panel_data
from research.bar_integrity import (
    require_complete_price_bars,
    require_positive_volume_bars,
)
from research.dividend_policy import refuse_cash_dividend_overlay
from research.source_row_lag import (
    DEMO_SIGNAL_LAG_PERIODS,
    require_observed_source_index,
)
from research.synthetic_momentum_demo import (
    SyntheticDemoConfig,
    build_equal_weight_benchmark,
    generate_synthetic_prices,
)
from research.synthetic_multifactor_workflow_demo import (
    FACTOR_NAMES,
    SyntheticMultifactorWorkflowConfig,
    generate_synthetic_factor_panels,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = (
    PROJECT_ROOT / "reports" / "synthetic_multifactor_backtest_demo.md"
)
DEFAULT_ATTEMPT_LOG_PATH = (
    PROJECT_ROOT / "reports" / "synthetic_multifactor_backtest_demo_attempts.jsonl"
)
TIMING_CONTRACT = "after_close_signal_next_observed_close_v1"
COMMAND_NAME = "python -m research.synthetic_multifactor_backtest_demo"
ATTEMPT_LOG_KIND = "all_attempt_case_logging"
ATTEMPT_LOG_CEILING = "lightweight_demo_diagnostic"
ATTEMPT_STATUS_STARTED = "started"
ATTEMPT_STATUS_SUCCESS = "success"
ATTEMPT_STATUS_FAILURE = "failure"
ATTEMPT_STATUS_INTERRUPTED = "interrupted"
_CATCHABLE_INTERRUPTIONS = (KeyboardInterrupt, SystemExit)
_CATCHABLE_ATTEMPT_OUTCOMES = (Exception, KeyboardInterrupt, SystemExit)
DEFAULT_WEIGHTS = {
    "synthetic_momentum": 0.50,
    "synthetic_quality": 0.30,
    "synthetic_reversal": 0.20,
}
SYNTHETIC_ONLY_CAVEATS = (
    "synthetic data only",
    "not financial advice",
    "not a profitability claim",
    "no real data fetching",
    "no live trading or brokerage integration",
    "artificial quality, reversal, and momentum panels",
    "distinct from Demo v0 12-1 momentum and from fundamentals",
)


@dataclass(frozen=True)
class SyntheticMultifactorBacktestConfig:
    """Frozen configuration for the synthetic three-factor backtest demo."""

    price_seed: int = 20260521
    factor_seed: int = 20260528
    asset_count: int = 20
    periods: int = 756
    start_date: str = "2021-01-01"
    starting_price: float = 100.0
    weights: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_WEIGHTS)
    )
    winsor_lower_quantile: float = 0.05
    winsor_upper_quantile: float = 0.95
    rebalance_frequency: str = "ME"
    top_n: int = 5
    transaction_cost_bps: float = 10.0
    slippage_bps: float = 0.0
    signal_lag_periods: int = DEMO_SIGNAL_LAG_PERIODS
    periods_per_year: int = 252


FROZEN_CONFIG = SyntheticMultifactorBacktestConfig()


@dataclass(frozen=True)
class SyntheticMultifactorBacktestDemoResult:
    """Outputs from one synthetic three-factor backtest demo run."""

    prices: pd.DataFrame
    raw_factors: dict[str, pd.DataFrame]
    winsorized_factors: dict[str, pd.DataFrame]
    zscore_factors: dict[str, pd.DataFrame]
    combined_score: pd.DataFrame
    backtest_result: BacktestResult
    report_path: Path


def load_attempt_records(log_path: Path) -> list[dict[str, Any]]:
    """Load All-Attempt Case Logging records in append order."""

    log_path = Path(log_path)
    if not log_path.is_file():
        return []

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        log_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "synthetic multifactor backtest attempt log is unreadable "
                f"at line {line_number}"
            ) from exc
        if not isinstance(payload, dict):
            raise ValueError(
                "synthetic multifactor backtest attempt log line "
                f"{line_number} must be a JSON object"
            )
        records.append(payload)
    return records


def append_attempt_record(
    log_path: Path,
    record: dict[str, Any],
    *,
    attempt_id: int | None = None,
) -> dict[str, Any]:
    """Append one All-Attempt record and return the stored payload."""

    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_attempt_records(log_path)
    if attempt_id is None:
        attempt_id = _next_attempt_id(existing)
    payload = {
        "schema_version": 1,
        "logging_kind": ATTEMPT_LOG_KIND,
        "logging_ceiling": ATTEMPT_LOG_CEILING,
        "command": COMMAND_NAME,
        **record,
        "attempt_id": attempt_id,
    }
    serialized = json.dumps(
        _json_ready(payload),
        sort_keys=True,
        allow_nan=False,
    )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(serialized + "\n")
        handle.flush()
    return json.loads(serialized)


def run_synthetic_multifactor_backtest_demo(
    *,
    config: SyntheticMultifactorBacktestConfig = FROZEN_CONFIG,
    report_path: Path = DEFAULT_REPORT_PATH,
    attempt_log_path: Path = DEFAULT_ATTEMPT_LOG_PATH,
    volume: pd.DataFrame | None = None,
    cash_dividends: object = None,
) -> SyntheticMultifactorBacktestDemoResult:
    """Run the synthetic three-factor backtest demo and record the attempt."""

    start_record = _begin_attempt(
        attempt_log_path=attempt_log_path,
        config=config,
        report_path=report_path,
    )
    attempt_id = start_record["attempt_id"]
    try:
        pipeline = _run_pipeline(
            config=config,
            volume=volume,
            cash_dividends=cash_dividends,
        )
        result = SyntheticMultifactorBacktestDemoResult(
            **pipeline,
            report_path=Path(report_path),
        )
        write_comparison_report(
            report_path=report_path,
            attempt_log_path=attempt_log_path,
            config=config,
            result=result,
        )
    except _CATCHABLE_ATTEMPT_OUTCOMES as exc:
        _record_attempt_outcome(
            attempt_log_path,
            attempt_id=attempt_id,
            record=_error_record(
                config=config,
                report_path=report_path,
                status=(
                    ATTEMPT_STATUS_INTERRUPTED
                    if isinstance(exc, _CATCHABLE_INTERRUPTIONS)
                    else ATTEMPT_STATUS_FAILURE
                ),
                error=exc,
            ),
        )
        raise

    append_attempt_record(
        attempt_log_path,
        _success_record(
            config=config,
            report_path=report_path,
            result=result,
        ),
        attempt_id=attempt_id,
    )
    return result


def write_comparison_report(
    *,
    report_path: Path,
    attempt_log_path: Path,
    config: SyntheticMultifactorBacktestConfig,
    result: SyntheticMultifactorBacktestDemoResult,
) -> None:
    """Write the human-readable synthetic three-factor comparison report."""

    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    metrics = result.backtest_result.metrics
    content = f"""# Synthetic Multifactor Backtest Comparison Report

This report is the M3-01 exploratory synthetic three-factor backtest. It reuses Demo v0 synthetic price dates and assets, the existing factor generator and `{_format_weights(config.weights)}` weights, existing winsorize/z-score/`combine_factors` helpers, and the existing long-only backtester. `python -m research.demo_v0` remains the official Demo v0 command. `python -m research.synthetic_multifactor_workflow_demo` remains the feature-only workflow.

The three synthetic panels are artificial quality, reversal, and momentum fixtures. They are distinct from Demo v0 12-1 momentum and from fundamentals.

This report was generated from synthetic data only. It does not use private data, does not support live trading, and is not a profitability claim.

## Purpose

1. Run one local command: `{COMMAND_NAME}`.
2. Generate Demo v0-aligned synthetic prices for `{config.asset_count}` assets.
3. Generate three aligned artificial factor panels from the existing factor generator.
4. Winsorize and z-score each panel, then combine with explicit weights through `combine_factors`.
5. Form simulated long-only top-`{config.top_n}` equal-weight selection with drift-aware holdings.
6. Compare the strategy with a synthetic equal-weight universe benchmark.
7. Record explicit fixed-bps cost, explicit slippage, the accepted timing contract, risk metrics, and limitations.
8. Persist an All-Attempt start record before computation, then append the success, failure, or catchable interruption outcome. Incomplete attempts remain visible.

## Configuration

- Command: `{COMMAND_NAME}`
- Data scope: synthetic only
- Price random seed: `{config.price_seed}`
- Factor random seed: `{config.factor_seed}`
- Asset count: `{config.asset_count}`
- Price rows: `{len(result.prices)}`
- Source date range: `{result.prices.index.min().date()}` to `{result.prices.index.max().date()}`
- Evaluation date range: `{result.backtest_result.timing_metadata["evaluation_start"].date()}` to `{result.backtest_result.timing_metadata["evaluation_end"].date()}`
- Factor names: `{", ".join(FACTOR_NAMES)}`
- Combination weights: `{_format_weights(config.weights)}`
- Winsorization quantiles: `{config.winsor_lower_quantile:.2f}` / `{config.winsor_upper_quantile:.2f}`
- Rebalance frequency: `{config.rebalance_frequency}`
- Selected assets per rebalance: `{config.top_n}`
- Timing contract: `{result.backtest_result.assumptions["execution_timing"]}`
- Signal lag: `{config.signal_lag_periods}` observed source rows (`{result.backtest_result.assumptions["signal_lag_unit"]}`)
- Turnover model: `{result.backtest_result.assumptions["turnover_model"]}` under the existing undivided absolute-trade convention (`{result.backtest_result.assumptions["trade_weight_model"]}`)
- Transaction cost: `{config.transaction_cost_bps:.2f}` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value
- Slippage: `{config.slippage_bps:.2f}` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value
- Zero cost or slippage diagnostic: `{result.backtest_result.assumptions["zero_cost_or_slippage_is_diagnostic"]}`
- Benchmark: synthetic equal-weight universe benchmark
- Holdings model: `{result.backtest_result.assumptions["holdings_model"]}`
- Holdings shape: `{result.backtest_result.holdings.shape[0]}` rows by `{result.backtest_result.holdings.shape[1]}` assets
- Tracking-error contract: `{result.backtest_result.assumptions["tracking_error_contract"]}`
- Tracking-error return basis: `{result.backtest_result.assumptions["tracking_error_return_basis"]}`
- Sharpe convention: `{result.backtest_result.assumptions["sharpe_return_basis"]}`, risk-free `{result.backtest_result.assumptions["sharpe_risk_free_policy"]}`, `ddof={result.backtest_result.assumptions["sharpe_ddof"]}`, `{result.backtest_result.assumptions["sharpe_periods_per_year"]}` periods/year, `{result.backtest_result.assumptions["sharpe_measured_row_policy"]}`
- Holding-episode contract: `{result.backtest_result.assumptions["holding_episode_contract"]}`
- All-Attempt Case Logging: `{_project_relative_path(attempt_log_path)}` (lightweight demo logging; not charter Stage 4 ledger accounting)

## Metrics

| Metric | Value |
| --- | ---: |
| Total return | {_format_percent(metrics["total_return"])} |
| Annualized return | {_format_percent(metrics["annualized_return"])} |
| Annualized volatility | {_format_percent(metrics["annualized_volatility"])} |
| Tracking error vs synthetic benchmark | {_format_percent(metrics["tracking_error"])} |
| Episode hit rate | {_format_percent(metrics["episode_hit_rate"])} |
| Average holding-period return | {_format_percent(metrics["average_holding_period_return"])} |
| Sharpe ratio | {_format_number(metrics["sharpe_ratio"])} |
| Max drawdown | {_format_percent(metrics["max_drawdown"])} |
| Average holding count | {_format_number(metrics["average_holding_count"])} |
| Average position concentration HHI | {_format_number(metrics["average_position_concentration_hhi"])} |
| Max position concentration HHI | {_format_number(metrics["max_position_concentration_hhi"])} |
| Average turnover | {_format_percent(metrics["average_turnover"])} |
| Total turnover | {_format_number(metrics["total_turnover"])} |
| Total transaction cost impact | {_format_percent(metrics["total_transaction_cost_impact"])} |
| Total slippage cost impact | {_format_percent(metrics["total_slippage_cost_impact"])} |
| Total trading cost impact | {_format_percent(metrics["total_trading_cost_impact"])} |
| Benchmark total return | {_format_percent(metrics["benchmark_total_return"])} |
| Excess total return vs synthetic benchmark | {_format_percent(metrics["excess_total_return"])} |

## Limitations

- Synthetic prices are workflow fixtures. They are not calibrated to actual equities.
- The three synthetic panels are artificial quality, reversal, and momentum fixtures. They are distinct from Demo v0 12-1 momentum and from fundamentals.
- Zero slippage is labeled diagnostic: `{result.backtest_result.assumptions["zero_cost_or_slippage_is_diagnostic"]}`.
- Holdings drift with asset returns between scheduled rebalances; turnover is the undivided sum of absolute signed trades against drifted pre-trade weights. Fixed-bps costs are charged on post-return portfolio value and expressed as beginning-period return impacts. This is weight-level accounting, not an order-fill model.
- There is no survivorship-bias, delisting, borrow, tax, liquidity, or market-impact model in this slice.
- Price bars must be complete, finite, and strictly positive. A supplied volume panel must be complete, finite, and strictly positive; zero volume is refused. Mismatched price/factor axes and nonfinite factor values are refused. Silent fill, reindex, clip, drop, or repair is not applied.
- Held returns use the supplied price series only (`current / previous - 1`). A separate cash-dividend overlay on that series is refused. Event-level dividend and split reconciliation remains later Milestone 3/4 work.
- Signal lag counts observed source rows in the bounded accounting slice. A missing source row remains an omitted observation. These demos keep the supplied observed index. Detecting invented sessions remains later calendar-alignment work.
- All-Attempt Case Logging records every invocation, including failures and catchable interruptions. A start record is written before computation so incomplete attempts stay visible. This is lightweight demo logging, not charter Stage 4 experiment/trial-ledger accounting.
- Results depend on the frozen synthetic seeds and remain workflow diagnostics only.
- No claim of strategy profitability is made.

## Next Action

Use `{COMMAND_NAME}` as the M3-01 exploratory synthetic three-factor backtest. Keep `python -m research.demo_v0` as the official Demo v0 command. Keep `python -m research.synthetic_multifactor_workflow_demo` as the feature-only workflow. Formal promotion, private data, and execution remain outside this slice.
"""
    report_path.write_text(content, encoding="utf-8")


def main() -> None:
    """Run the frozen synthetic three-factor backtest demo."""

    run_synthetic_multifactor_backtest_demo()


def _run_pipeline(
    *,
    config: SyntheticMultifactorBacktestConfig,
    volume: pd.DataFrame | None = None,
    cash_dividends: object = None,
) -> dict[str, Any]:
    _validate_config(config)

    prices = generate_synthetic_prices(_price_config(config))
    require_complete_price_bars(
        prices,
        expected_rows=config.periods,
        expected_assets=config.asset_count,
    )
    prices = require_observed_source_index(prices)
    refuse_cash_dividend_overlay(cash_dividends)
    if volume is not None:
        require_positive_volume_bars(volume, prices=prices)
    raw_factors = generate_synthetic_factor_panels(_factor_config(config))
    _require_aligned_finite_factor_panels(prices, raw_factors)

    winsorized_factors = {
        name: cross_sectional_winsorize_factor(
            factor,
            lower_quantile=config.winsor_lower_quantile,
            upper_quantile=config.winsor_upper_quantile,
        )
        for name, factor in raw_factors.items()
    }
    zscore_factors = {
        name: cross_sectional_zscore_factor(factor)
        for name, factor in winsorized_factors.items()
    }
    _require_aligned_finite_factor_panels(prices, zscore_factors)
    combined_score = combine_factors(zscore_factors, config.weights)
    _require_aligned_finite_panel(
        prices,
        combined_score,
        name="combined_score",
    )
    source_provenance = capture_backtest_source_provenance(
        prices,
        combined_score,
    )
    benchmark = build_equal_weight_benchmark(
        prices,
        starting_price=config.starting_price,
    )
    evaluation_start = prices.index[0]
    evaluation_end = prices.index[-1]

    backtest_result = run_long_only_backtest(
        prices,
        combined_score,
        source_provenance=source_provenance,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
        rebalance_frequency=config.rebalance_frequency,
        top_n=config.top_n,
        transaction_cost_bps=config.transaction_cost_bps,
        slippage_bps=config.slippage_bps,
        benchmark_prices=benchmark,
        signal_lag_periods=config.signal_lag_periods,
        periods_per_year=config.periods_per_year,
    )
    return {
        "prices": prices,
        "raw_factors": raw_factors,
        "winsorized_factors": winsorized_factors,
        "zscore_factors": zscore_factors,
        "combined_score": combined_score,
        "backtest_result": backtest_result,
    }


def _price_config(
    config: SyntheticMultifactorBacktestConfig,
) -> SyntheticDemoConfig:
    return SyntheticDemoConfig(
        seed=config.price_seed,
        asset_count=config.asset_count,
        periods=config.periods,
        start_date=config.start_date,
        starting_price=config.starting_price,
        rebalance_frequency=config.rebalance_frequency,
        top_n=config.top_n,
        transaction_cost_bps=config.transaction_cost_bps,
        slippage_bps=config.slippage_bps,
        periods_per_year=config.periods_per_year,
    )


def _factor_config(
    config: SyntheticMultifactorBacktestConfig,
) -> SyntheticMultifactorWorkflowConfig:
    return SyntheticMultifactorWorkflowConfig(
        seed=config.factor_seed,
        asset_count=config.asset_count,
        periods=config.periods,
        start_date=config.start_date,
        weights=dict(config.weights),
        winsor_lower_quantile=config.winsor_lower_quantile,
        winsor_upper_quantile=config.winsor_upper_quantile,
    )


def _validate_config(config: SyntheticMultifactorBacktestConfig) -> None:
    if isinstance(config.asset_count, bool) or not isinstance(config.asset_count, int):
        raise TypeError("asset_count must be a non-boolean integer")
    if config.asset_count < 2:
        raise ValueError("asset_count must be at least 2")
    if isinstance(config.periods, bool) or not isinstance(config.periods, int):
        raise TypeError("periods must be a non-boolean integer")
    if config.periods < 2:
        raise ValueError("periods must be at least 2")
    if config.starting_price <= 0:
        raise ValueError("starting_price must be positive")
    if set(config.weights) != set(FACTOR_NAMES):
        raise ValueError("weights must exactly match synthetic factor names")
    if (
        isinstance(config.top_n, bool)
        or not isinstance(config.top_n, int)
        or config.top_n < 1
    ):
        raise ValueError("top_n must be a positive non-boolean integer")
    if config.top_n > config.asset_count:
        raise ValueError("top_n must not exceed asset_count")
    if (
        isinstance(config.signal_lag_periods, bool)
        or not isinstance(config.signal_lag_periods, int)
        or config.signal_lag_periods < 1
    ):
        raise ValueError(
            "signal_lag_periods must be a non-boolean integer of at least one"
        )
    if (
        isinstance(config.periods_per_year, bool)
        or not isinstance(config.periods_per_year, int)
        or config.periods_per_year != 252
    ):
        raise ValueError(
            "synthetic multifactor backtest requires integer periods_per_year=252"
        )


def _require_aligned_finite_factor_panels(
    prices: pd.DataFrame,
    factors: dict[str, pd.DataFrame],
) -> None:
    if set(factors) != set(FACTOR_NAMES):
        raise ValueError("factor panels must exactly match synthetic factor names")
    for name, panel in factors.items():
        _require_aligned_finite_panel(prices, panel, name=f"factors[{name!r}]")


def _require_aligned_finite_panel(
    prices: pd.DataFrame,
    panel: pd.DataFrame,
    *,
    name: str,
) -> None:
    validated = validate_panel_data(panel, name=name)
    if not validated.index.equals(prices.index):
        raise ValueError(
            f"{name} index must match synthetic price dates; "
            "silent reindex or repair is refused"
        )
    if not validated.columns.equals(prices.columns):
        raise ValueError(
            f"{name} columns must match synthetic price assets; "
            "silent reindex or repair is refused"
        )
    if not np.isfinite(validated.to_numpy()).all():
        raise ValueError(
            f"{name} must be finite; silent fill, clip, drop, or repair is refused"
        )


def _base_attempt_record(
    *,
    config: SyntheticMultifactorBacktestConfig,
    report_path: Path,
) -> dict[str, Any]:
    return {
        "config": asdict(config),
        "data_scope": "synthetic only",
        "factor": "combine_factors(winsorize/z-score artificial quality, reversal, momentum)",
        "factor_names": list(FACTOR_NAMES),
        "weights": dict(config.weights),
        "timing_contract": TIMING_CONTRACT,
        "rebalance_frequency": config.rebalance_frequency,
        "transaction_cost_bps": config.transaction_cost_bps,
        "slippage_bps": config.slippage_bps,
        "turnover_convention": "undivided_absolute_signed_trades",
        "benchmark": "synthetic equal-weight universe benchmark",
        "report_path": _project_relative_path(report_path),
        "live_trading": False,
        "brokerage_integration": False,
        "not_a_profitability_claim": True,
        "caveats": list(SYNTHETIC_ONLY_CAVEATS),
    }


def _begin_attempt(
    *,
    attempt_log_path: Path,
    config: SyntheticMultifactorBacktestConfig,
    report_path: Path,
) -> dict[str, Any]:
    """Persist the attempt-start record before computation or report replacement."""

    try:
        return append_attempt_record(
            attempt_log_path,
            _start_record(config=config, report_path=report_path),
        )
    except Exception as exc:
        raise RuntimeError(
            "synthetic multifactor backtest attempt log cannot begin; "
            "comparison report was not replaced"
        ) from exc


def _record_attempt_outcome(
    log_path: Path,
    *,
    attempt_id: int,
    record: dict[str, Any],
) -> None:
    """Append a terminal outcome. Preserve the original exception if logging fails."""

    try:
        append_attempt_record(log_path, record, attempt_id=attempt_id)
    except Exception:
        return


def _next_attempt_id(records: list[dict[str, Any]]) -> int:
    used_ids = [
        record["attempt_id"]
        for record in records
        if isinstance(record.get("attempt_id"), int)
        and not isinstance(record.get("attempt_id"), bool)
    ]
    return (max(used_ids) if used_ids else 0) + 1


def _start_record(
    *,
    config: SyntheticMultifactorBacktestConfig,
    report_path: Path,
) -> dict[str, Any]:
    return {
        **_base_attempt_record(config=config, report_path=report_path),
        "status": ATTEMPT_STATUS_STARTED,
        "error_type": None,
        "error_message": None,
        "zero_cost_or_slippage_is_diagnostic": config.slippage_bps == 0.0
        or config.transaction_cost_bps == 0.0,
        "holdings_rows": None,
        "holdings_assets": None,
        "source_price_rows": None,
        "metrics": {},
    }


def _success_record(
    *,
    config: SyntheticMultifactorBacktestConfig,
    report_path: Path,
    result: SyntheticMultifactorBacktestDemoResult,
) -> dict[str, Any]:
    backtest = result.backtest_result
    return {
        **_base_attempt_record(config=config, report_path=report_path),
        "status": ATTEMPT_STATUS_SUCCESS,
        "error_type": None,
        "error_message": None,
        "zero_cost_or_slippage_is_diagnostic": backtest.assumptions[
            "zero_cost_or_slippage_is_diagnostic"
        ],
        "holdings_rows": backtest.holdings.shape[0],
        "holdings_assets": backtest.holdings.shape[1],
        "source_price_rows": len(result.prices),
        "metrics": {
            "total_return": backtest.metrics["total_return"],
            "annualized_return": backtest.metrics["annualized_return"],
            "annualized_volatility": backtest.metrics["annualized_volatility"],
            "tracking_error": backtest.metrics["tracking_error"],
            "sharpe_ratio": backtest.metrics["sharpe_ratio"],
            "max_drawdown": backtest.metrics["max_drawdown"],
            "benchmark_total_return": backtest.metrics["benchmark_total_return"],
            "excess_total_return": backtest.metrics["excess_total_return"],
            "total_turnover": backtest.metrics["total_turnover"],
            "total_transaction_cost_impact": backtest.metrics[
                "total_transaction_cost_impact"
            ],
            "total_slippage_cost_impact": backtest.metrics["total_slippage_cost_impact"],
        },
    }


def _error_record(
    *,
    config: SyntheticMultifactorBacktestConfig,
    report_path: Path,
    status: str,
    error: BaseException,
) -> dict[str, Any]:
    return {
        **_base_attempt_record(config=config, report_path=report_path),
        "status": status,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "zero_cost_or_slippage_is_diagnostic": config.slippage_bps == 0.0
        or config.transaction_cost_bps == 0.0,
        "holdings_rows": None,
        "holdings_assets": None,
        "source_price_rows": None,
        "metrics": {},
    }


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field_name: _json_ready(field_value)
            for field_name, field_value in asdict(value).items()
        }
    if isinstance(value, dict):
        return {str(key): _json_ready(nested) for key, nested in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(nested) for nested in value]
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, datetime | date):
        return value.isoformat()
    if hasattr(value, "item") and callable(value.item):
        return _json_ready(value.item())
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return value
    if isinstance(value, int | str | bool) or value is None:
        return value
    raise TypeError(
        "unsupported synthetic multifactor backtest log value type: "
        f"{type(value).__name__}"
    )


def _format_weights(weights: dict[str, float]) -> str:
    return ", ".join(f"{name}={weight:.2f}" for name, weight in weights.items())


def _format_percent(value: float) -> str:
    if pd.isna(value):
        return "NaN"
    return f"{value:.2%}"


def _format_number(value: float) -> str:
    if pd.isna(value):
        return "NaN"
    return f"{value:.4f}"


def _project_relative_path(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


if __name__ == "__main__":
    main()
