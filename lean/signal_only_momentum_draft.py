"""Signal-only LEAN-adjacent momentum draft.

This module is deliberately metadata-only. It is not a runnable QuantConnect
algorithm, does not import the LEAN runtime, does not read credentials, does
not fetch data, and does not define portfolio or order behavior.

The purpose is to make the 12-1 momentum signal boundary reviewable before any
future runnable LEAN translation is considered.
"""

from dataclasses import dataclass
from typing import Final


IS_EXECUTABLE_LEAN_ALGORITHM: Final[bool] = False
SIGNAL_DRAFT_STATUS: Final[str] = "signal_only_metadata_review_only"
SIGNAL_NAME: Final[str] = "momentum_12_1_signal_only_draft"


@dataclass(frozen=True)
class SignalOnlyMomentumDraftConfig:
    """Review metadata for a future 12-1 momentum signal translation."""

    benchmark_symbol: str = "SPY"
    lookback_months: int = 12
    skip_months: int = 1
    required_history_note: str = "completed adjusted-close history only"
    ranking_direction: str = "higher_trailing_return_ranks_higher"
    universe_note: str = "future reviewed universe only; no data access here"


REQUIRED_INPUT_FIELDS: Final[tuple[str, ...]] = (
    "symbol",
    "adjusted_close",
    "latest_completed_data_date",
)


TIMING_CONTRACT_FIELDS: Final[tuple[str, ...]] = (
    "algorithm_time",
    "latest_completed_data_date",
    "feature_date",
    "signal_review_date",
)


DIAGNOSTIC_FIELDS: Final[tuple[str, ...]] = (
    "eligible_symbols",
    "skipped_symbols",
    "ranked_symbols_preview",
    "missing_input_reasons",
    "benchmark_symbol",
    "caveats",
)


GUARDRAILS: Final[tuple[str, ...]] = (
    "signal_metadata_only",
    "no_runtime_lean_dependency",
    "no_external_data_download",
    "no_credential_loading",
    "no_live_or_paper_mode",
    "no_brokerage_or_order_semantics",
    "no_portfolio_construction",
    "no_profitability_claim",
)


CAVEATS: Final[tuple[str, ...]] = (
    "research_boundary_only",
    "no_signal_calculation_performed",
    "no_backtest_results_produced",
    "not_investment_advice",
)


def describe_signal_only_momentum_draft(
    config: SignalOnlyMomentumDraftConfig = SignalOnlyMomentumDraftConfig(),
) -> dict[str, object]:
    """Return review metadata without calculating a signal or running LEAN."""

    return {
        "status": SIGNAL_DRAFT_STATUS,
        "is_executable_lean_algorithm": IS_EXECUTABLE_LEAN_ALGORITHM,
        "signal_name": SIGNAL_NAME,
        "represented_feature": "12-1 momentum",
        "lookback_months": config.lookback_months,
        "skip_months": config.skip_months,
        "required_history_note": config.required_history_note,
        "required_input_fields": REQUIRED_INPUT_FIELDS,
        "timing_contract_fields": TIMING_CONTRACT_FIELDS,
        "diagnostic_fields": DIAGNOSTIC_FIELDS,
        "benchmark_symbol": config.benchmark_symbol,
        "ranking_direction": config.ranking_direction,
        "universe_note": config.universe_note,
        "formula_boundary": (
            "trailing return over the lookback window excluding the most "
            "recent skip window; calculation remains outside this draft"
        ),
        "guardrails": GUARDRAILS,
        "caveats": CAVEATS,
    }
