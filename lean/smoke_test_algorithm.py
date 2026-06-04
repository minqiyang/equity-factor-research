"""Non-executing LEAN smoke-test scaffold.

This module is deliberately metadata-only. It is not a runnable QuantConnect
algorithm, does not import the LEAN runtime, does not read credentials, does
not fetch data, and does not submit simulated portfolio targets. A later PR
may translate this reviewed scaffold into a runnable LEAN backtest after the
static guardrails and timing contract are accepted.
"""

from dataclasses import dataclass
from typing import Final


IS_EXECUTABLE_LEAN_ALGORITHM: Final[bool] = False
SCAFFOLD_STATUS: Final[str] = "non_executing_design_review_only"


@dataclass(frozen=True)
class LeanSmokeTestConfig:
    """Configuration fields a future LEAN smoke test must record."""

    start_year: int = 2018
    start_month: int = 1
    start_day: int = 1
    end_year: int = 2020
    end_month: int = 12
    end_day: int = 31
    benchmark_symbol: str = "SPY"
    resolution: str = "Daily"
    cash_buffer: float = 0.02
    lookback_days: int = 252
    skip_days: int = 21
    max_selected_symbols: int = 20
    universe_note: str = "small platform-defined US equity universe"
    fee_model_note: str = "explicit simulated fee model required before run"
    slippage_model_note: str = "explicit simulated slippage model required before run"


TIMING_CONTRACT_FIELDS: Final[tuple[str, ...]] = (
    "algorithm_time",
    "latest_completed_data_date",
    "feature_date",
    "simulated_order_date",
    "evaluation_date",
)


DIAGNOSTIC_FIELDS: Final[tuple[str, ...]] = (
    "eligible_count",
    "skipped_count",
    "selected_symbols",
    "target_weights",
    "latest_completed_data_date",
    "benchmark_symbol",
    "fee_model",
    "slippage_model",
    "cash_buffer",
    "caveats",
)


GUARDRAILS: Final[tuple[str, ...]] = (
    "metadata_only_scaffold",
    "no_runtime_lean_dependency",
    "no_external_data_download",
    "no_credential_loading",
    "no_live_or_paper_mode",
    "no_brokerage_connection",
    "no_order_submission",
    "no_performance_interpretation",
)


def describe_smoke_test_scope(
    config: LeanSmokeTestConfig = LeanSmokeTestConfig(),
) -> dict[str, object]:
    """Return review metadata without running LEAN or calculating a signal."""

    return {
        "status": SCAFFOLD_STATUS,
        "is_executable_lean_algorithm": IS_EXECUTABLE_LEAN_ALGORITHM,
        "benchmark_symbol": config.benchmark_symbol,
        "resolution": config.resolution,
        "cash_buffer": config.cash_buffer,
        "lookback_days": config.lookback_days,
        "skip_days": config.skip_days,
        "max_selected_symbols": config.max_selected_symbols,
        "universe_note": config.universe_note,
        "fee_model_note": config.fee_model_note,
        "slippage_model_note": config.slippage_model_note,
        "timing_contract_fields": TIMING_CONTRACT_FIELDS,
        "diagnostic_fields": DIAGNOSTIC_FIELDS,
        "guardrails": GUARDRAILS,
    }
