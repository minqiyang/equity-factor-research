"""Official Demo v0 synthetic vertical slice.

This command is the Demo v0 entry point. It reuses existing 12-1 momentum,
the existing long-only backtester, and frozen SyntheticDemoConfig values.
``python -m research.synthetic_momentum_demo`` remains a legacy diagnostic.

Results are synthetic diagnostics only. They are not a profitability claim,
private-data run, or brokerage/order capability.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.portfolio import (
    BacktestResult,
    capture_backtest_source_provenance,
    run_long_only_backtest,
)
from features.momentum import calculate_12_1_momentum
from research.bar_integrity import (
    require_complete_price_bars,
    require_positive_volume_bars,
)
from research.dividend_policy import refuse_cash_dividend_overlay
from research.source_row_lag import (
    DEMO_SIGNAL_LAG_PERIODS,
    refuse_inserted_source_rows,
    report_calendar_day_spans,
)
from research.unchanging_price import report_unchanging_price_segments
from research.synthetic_momentum_demo import (
    SyntheticDemoConfig,
    build_equal_weight_benchmark,
    generate_synthetic_prices,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "demo_v0.md"
DEFAULT_ATTEMPT_LOG_PATH = PROJECT_ROOT / "reports" / "demo_v0_attempts.jsonl"
TIMING_CONTRACT = "after_close_signal_next_observed_close_v1"
COMMAND_NAME = "python -m research.demo_v0"
ATTEMPT_LOG_KIND = "all_attempt_case_logging"
ATTEMPT_LOG_CEILING = "lightweight_demo_diagnostic"
ATTEMPT_STATUS_STARTED = "started"
ATTEMPT_STATUS_SUCCESS = "success"
ATTEMPT_STATUS_FAILURE = "failure"
ATTEMPT_STATUS_INTERRUPTED = "interrupted"
_CATCHABLE_INTERRUPTIONS = (KeyboardInterrupt, SystemExit)
_CATCHABLE_ATTEMPT_OUTCOMES = (Exception, KeyboardInterrupt, SystemExit)

DEMO_V0_CONFIG = SyntheticDemoConfig(
    seed=20260521,
    asset_count=20,
    periods=756,
    start_date="2021-01-01",
    starting_price=100.0,
    lookback_periods=252,
    skip_periods=21,
    rebalance_frequency="ME",
    top_n=5,
    transaction_cost_bps=10.0,
    slippage_bps=0.0,
    periods_per_year=252,
)

SYNTHETIC_ONLY_CAVEATS = (
    "synthetic data only",
    "not financial advice",
    "not a profitability claim",
    "no real data fetching",
    "no live trading or brokerage integration",
)


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
                f"demo v0 attempt log is unreadable at line {line_number}"
            ) from exc
        if not isinstance(payload, dict):
            raise ValueError(
                f"demo v0 attempt log line {line_number} must be a JSON object"
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


def run_demo_v0(
    *,
    config: SyntheticDemoConfig = DEMO_V0_CONFIG,
    report_path: Path = DEFAULT_REPORT_PATH,
    attempt_log_path: Path = DEFAULT_ATTEMPT_LOG_PATH,
    volume: pd.DataFrame | None = None,
    cash_dividends: object = None,
    observed_index: pd.DatetimeIndex | None = None,
) -> BacktestResult:
    """Run the official Demo v0 slice and record the attempt."""

    start_record = _begin_attempt(
        attempt_log_path=attempt_log_path,
        config=config,
        report_path=report_path,
    )
    attempt_id = start_record["attempt_id"]
    try:
        prices, result = _run_demo_v0_pipeline(
            config=config,
            volume=volume,
            cash_dividends=cash_dividends,
            observed_index=observed_index,
        )
        write_comparison_report(
            report_path=report_path,
            attempt_log_path=attempt_log_path,
            config=config,
            prices=prices,
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
            prices=prices,
            result=result,
        ),
        attempt_id=attempt_id,
    )
    return result


def write_comparison_report(
    *,
    report_path: Path,
    attempt_log_path: Path,
    config: SyntheticDemoConfig,
    prices: pd.DataFrame,
    result: BacktestResult,
) -> None:
    """Write the human-readable Demo v0 comparison report."""

    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    metrics = result.metrics
    unchanging = report_unchanging_price_segments(prices)
    calendar_spans = report_calendar_day_spans(prices.index)
    content = f"""# Demo v0 Comparison Report

This report is the official Demo v0 synthetic vertical slice. It uses existing 12-1 momentum, frozen `SyntheticDemoConfig` values, and the existing long-only backtester. `python -m research.synthetic_momentum_demo` remains a legacy diagnostic.

This report was generated from synthetic data only. It does not use private data, does not support live trading, and is not a profitability claim.

## Purpose

1. Run one local command: `{COMMAND_NAME}`.
2. Generate synthetic prices for `{config.asset_count}` assets.
3. Compute existing 12-1 momentum.
4. Form simulated long-only top-`{config.top_n}` equal-weight selection with drift-aware holdings.
5. Compare the strategy with a synthetic equal-weight universe benchmark.
6. Record explicit fixed-bps cost, explicit slippage, the accepted timing contract, risk metrics, and limitations.
7. Persist an All-Attempt start record before computation, then append the success, failure, or catchable interruption outcome. Incomplete attempts remain visible.

## Configuration

- Command: `{COMMAND_NAME}`
- Data scope: synthetic only
- Random seed: `{config.seed}`
- Asset count: `{config.asset_count}`
- Price rows: `{len(prices)}`
- Unchanging-price segments: `{unchanging.segment_count}`
- Assets with unchanging-price segments: `{unchanging.assets_affected}`
- Max unchanging-price run length: `{unchanging.max_run_length}`
- Adjacent timestamp pairs with calendar-day span > 1: `{calendar_spans.pairs_over_one_day}`
- Max adjacent calendar-day span: `{calendar_spans.max_span_days}` days
- Source date range: `{prices.index.min().date()}` to `{prices.index.max().date()}`
- Evaluation date range: `{result.timing_metadata["evaluation_start"].date()}` to `{result.timing_metadata["evaluation_end"].date()}`
- Momentum lookback periods: `{config.lookback_periods}`
- Momentum skipped recent periods: `{config.skip_periods}`
- Rebalance frequency: `{config.rebalance_frequency}`
- Selected assets per rebalance: `{config.top_n}`
- Timing contract: `{result.assumptions["execution_timing"]}`
- Signal lag: `{DEMO_SIGNAL_LAG_PERIODS}` observed source rows (`{result.assumptions["signal_lag_unit"]}`)
- Turnover model: `{result.assumptions["turnover_model"]}` under the existing undivided absolute-trade convention (`{result.assumptions["trade_weight_model"]}`)
- Transaction cost: `{config.transaction_cost_bps:.2f}` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value
- Slippage: `{config.slippage_bps:.2f}` bps per unit of drift-adjusted target-weight turnover on post-return portfolio value
- Zero cost or slippage diagnostic: `{result.assumptions["zero_cost_or_slippage_is_diagnostic"]}`
- Benchmark: synthetic equal-weight universe benchmark
- Holdings model: `{result.assumptions["holdings_model"]}`
- Holdings shape: `{result.holdings.shape[0]}` rows by `{result.holdings.shape[1]}` assets
- Tracking-error contract: `{result.assumptions["tracking_error_contract"]}`
- Tracking-error return basis: `{result.assumptions["tracking_error_return_basis"]}`
- Sharpe convention: `{result.assumptions["sharpe_return_basis"]}`, risk-free `{result.assumptions["sharpe_risk_free_policy"]}`, `ddof={result.assumptions["sharpe_ddof"]}`, `{result.assumptions["sharpe_periods_per_year"]}` periods/year, `{result.assumptions["sharpe_measured_row_policy"]}`
- Holding-episode contract: `{result.assumptions["holding_episode_contract"]}`
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
- Zero slippage is labeled diagnostic: `{result.assumptions["zero_cost_or_slippage_is_diagnostic"]}`.
- Holdings drift with asset returns between scheduled rebalances; turnover is the undivided sum of absolute signed trades against drifted pre-trade weights. Fixed-bps costs are charged on post-return portfolio value and expressed as beginning-period return impacts. This is weight-level accounting, not an order-fill model.
- There is no survivorship-bias, delisting, borrow, tax, liquidity, or market-impact model in this slice.
- Price bars must be complete, finite, and strictly positive. A supplied volume panel must be complete, finite, and strictly positive; zero volume is refused. Silent fill, clip, drop, or repair is not applied.
- Consecutive equal prices stay in the panel. Unchanging-price segment count, assets affected, and max run length are recorded. The backtest uses every supplied bar.
- Held returns use the supplied price series only (`current / previous - 1`). A separate cash-dividend overlay on that series is refused. Event-level dividend and split reconciliation remains later Milestone 3/4 work.
- Signal lag counts observed source rows in the bounded accounting slice. A missing source row remains an omitted observation. These demos keep the supplied observed index. M3-07 calendar-alignment checks refuse invented sessions: panel timestamps absent from the declared source index. Official demos declare the generated price index as source. Adjacent calendar-day spans measure `(next.normalize() - current.normalize()).days` and disclose omitted-observation gaps in wall time. Session and holiday status remains unverified. Every supplied observed bar stays in the panel, including Friday-Monday bars.
- All-Attempt Case Logging records every Demo v0 invocation, including failures and catchable interruptions. A start record is written before computation so incomplete attempts stay visible. This is lightweight demo logging, not charter Stage 4 experiment/trial-ledger accounting.
- Results depend on the frozen synthetic seed and remain workflow diagnostics only.
- No claim of strategy profitability is made.

## Next Action

Use `{COMMAND_NAME}` as the official synthetic Demo v0 command. Keep `python -m research.synthetic_momentum_demo` as a legacy diagnostic. Formal promotion, private data, and execution remain outside this slice.
"""
    report_path.write_text(content, encoding="utf-8")


def main() -> None:
    """Run Demo v0 with the frozen configuration."""

    run_demo_v0()


def _run_demo_v0_pipeline(
    *,
    config: SyntheticDemoConfig,
    volume: pd.DataFrame | None = None,
    cash_dividends: object = None,
    observed_index: pd.DatetimeIndex | None = None,
) -> tuple[pd.DataFrame, BacktestResult]:
    if (
        isinstance(config.periods_per_year, bool)
        or not isinstance(config.periods_per_year, int)
        or config.periods_per_year != 252
    ):
        raise ValueError("demo v0 requires integer periods_per_year=252")
    if (
        isinstance(config.lookback_periods, bool)
        or not isinstance(config.lookback_periods, int)
        or config.lookback_periods < 1
    ):
        raise ValueError("lookback_periods must be a positive non-boolean integer")

    prices = generate_synthetic_prices(config)
    if observed_index is None:
        observed_index = prices.index.copy()
    require_complete_price_bars(
        prices,
        expected_rows=config.periods,
        expected_assets=config.asset_count,
    )
    prices = refuse_inserted_source_rows(prices, observed_index=observed_index)
    refuse_cash_dividend_overlay(cash_dividends)
    if volume is not None:
        require_positive_volume_bars(volume, prices=prices)
    momentum = calculate_12_1_momentum(
        prices,
        lookback_periods=config.lookback_periods,
        skip_periods=config.skip_periods,
    )
    source_provenance = capture_backtest_source_provenance(prices, momentum)
    benchmark = build_equal_weight_benchmark(
        prices,
        starting_price=config.starting_price,
    )
    evaluation_start_position = config.lookback_periods
    if evaluation_start_position >= len(prices) - 1:
        raise ValueError(
            "demo v0 evaluation requires the configured feature "
            "warm-up anchor plus at least one measured row"
        )
    evaluation_start = prices.index[evaluation_start_position]
    evaluation_end = prices.index[-1]
    accounting_benchmark = benchmark.iloc[evaluation_start_position:]

    result = run_long_only_backtest(
        prices,
        momentum,
        source_provenance=source_provenance,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
        rebalance_frequency=config.rebalance_frequency,
        top_n=config.top_n,
        transaction_cost_bps=config.transaction_cost_bps,
        slippage_bps=config.slippage_bps,
        benchmark_prices=accounting_benchmark,
        signal_lag_periods=DEMO_SIGNAL_LAG_PERIODS,
        periods_per_year=config.periods_per_year,
    )
    return prices, result


def _base_attempt_record(
    *,
    config: SyntheticDemoConfig,
    report_path: Path,
) -> dict[str, Any]:
    return {
        "config": asdict(config),
        "data_scope": "synthetic only",
        "factor": "calculate_12_1_momentum",
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
    config: SyntheticDemoConfig,
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
            "demo v0 attempt log cannot begin; comparison report was not replaced"
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
    config: SyntheticDemoConfig,
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
    config: SyntheticDemoConfig,
    report_path: Path,
    prices: pd.DataFrame,
    result: BacktestResult,
) -> dict[str, Any]:
    return {
        **_base_attempt_record(config=config, report_path=report_path),
        "status": ATTEMPT_STATUS_SUCCESS,
        "error_type": None,
        "error_message": None,
        "zero_cost_or_slippage_is_diagnostic": result.assumptions[
            "zero_cost_or_slippage_is_diagnostic"
        ],
        "holdings_rows": result.holdings.shape[0],
        "holdings_assets": result.holdings.shape[1],
        "source_price_rows": len(prices),
        "metrics": {
            "total_return": result.metrics["total_return"],
            "annualized_return": result.metrics["annualized_return"],
            "annualized_volatility": result.metrics["annualized_volatility"],
            "tracking_error": result.metrics["tracking_error"],
            "sharpe_ratio": result.metrics["sharpe_ratio"],
            "max_drawdown": result.metrics["max_drawdown"],
            "benchmark_total_return": result.metrics["benchmark_total_return"],
            "excess_total_return": result.metrics["excess_total_return"],
            "total_turnover": result.metrics["total_turnover"],
            "total_transaction_cost_impact": result.metrics[
                "total_transaction_cost_impact"
            ],
            "total_slippage_cost_impact": result.metrics["total_slippage_cost_impact"],
        },
    }


def _error_record(
    *,
    config: SyntheticDemoConfig,
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
    raise TypeError(f"unsupported demo v0 log value type: {type(value).__name__}")


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
