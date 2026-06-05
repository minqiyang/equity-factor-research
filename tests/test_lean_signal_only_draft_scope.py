import ast
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LEAN_DIR = REPO_ROOT / "lean"
SIGNAL_DRAFT_PATH = LEAN_DIR / "signal_only_momentum_draft.py"
README_PATH = LEAN_DIR / "README.md"


BANNED_IMPORT_ROOTS = {"requests", "yfinance", "alpaca", "ccxt", "os"}
BANNED_CALL_NAMES = {
    "AddEquity",
    "History",
    "SetHoldings",
    "MarketOrder",
    "LimitOrder",
    "StopMarketOrder",
    "Liquidate",
    "SetBenchmark",
    "SetBrokerageModel",
}
BANNED_TEXT_SNIPPETS = {
    "AlgorithmImports",
    "QCAlgorithm",
    "config.json",
    "api_key",
    "access_token",
    "secret_key",
    "os.environ",
    "getenv(",
    "simulated_order_date",
    "target_weights",
    "submitted_order",
    "filled_order",
}


def _source() -> str:
    return SIGNAL_DRAFT_PATH.read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_source(), filename=str(SIGNAL_DRAFT_PATH))


def _module():
    spec = importlib.util.spec_from_file_location(
        "lean_signal_only_momentum_draft",
        SIGNAL_DRAFT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_signal_only_draft_expected_files_exist() -> None:
    assert README_PATH.is_file()
    assert SIGNAL_DRAFT_PATH.is_file()
    assert not (LEAN_DIR / "config.json").exists()


def test_signal_only_draft_is_metadata_only_and_not_runtime_dependent() -> None:
    source = _source()

    assert "IS_EXECUTABLE_LEAN_ALGORITHM: Final[bool] = False" in source
    assert "SIGNAL_DRAFT_STATUS: Final[str]" in source
    assert "SIGNAL_NAME: Final[str]" in source

    for snippet in BANNED_TEXT_SNIPPETS:
        assert snippet not in source


def test_signal_only_draft_has_no_external_download_or_credential_imports() -> None:
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".")[0].lower() for alias in node.names}
            assert imported_roots.isdisjoint(BANNED_IMPORT_ROOTS)
        elif isinstance(node, ast.ImportFrom):
            module_root = (node.module or "").split(".")[0].lower()
            assert module_root not in BANNED_IMPORT_ROOTS


def test_signal_only_draft_has_no_lean_runtime_order_or_brokerage_calls() -> None:
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in BANNED_CALL_NAMES
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in BANNED_CALL_NAMES


def test_signal_only_draft_declares_signal_timing_and_diagnostics() -> None:
    source = _source()

    for expected in (
        "algorithm_time",
        "latest_completed_data_date",
        "feature_date",
        "signal_review_date",
        "eligible_symbols",
        "skipped_symbols",
        "ranked_symbols_preview",
        "missing_input_reasons",
        "benchmark_symbol",
        "caveats",
    ):
        assert expected in source


def test_signal_only_draft_metadata_has_expected_boundary() -> None:
    module = _module()
    metadata = module.describe_signal_only_momentum_draft()

    assert metadata["status"] == "signal_only_metadata_review_only"
    assert metadata["is_executable_lean_algorithm"] is False
    assert metadata["signal_name"] == "momentum_12_1_signal_only_draft"
    assert metadata["represented_feature"] == "12-1 momentum"
    assert metadata["lookback_months"] == 12
    assert metadata["skip_months"] == 1
    assert "adjusted_close" in metadata["required_input_fields"]
    assert "no_runtime_lean_dependency" in metadata["guardrails"]
    assert "no_brokerage_or_order_semantics" in metadata["guardrails"]


def test_signal_only_draft_metadata_does_not_return_results_or_orders() -> None:
    metadata = _module().describe_signal_only_momentum_draft()
    returned_keys = {str(key).lower() for key in metadata}

    assert "returns" not in returned_keys
    assert "sharpe" not in returned_keys
    assert "drawdown" not in returned_keys
    assert "orders" not in returned_keys
    assert "target_weights" not in returned_keys


def test_signal_only_draft_readme_preserves_guardrails() -> None:
    readme = README_PATH.read_text(encoding="utf-8").lower()

    for expected in (
        "signal-only",
        "non-executing",
        "not a runnable lean project",
        "no real market data",
        "no live trading",
        "no brokerage",
        "no profitability claims",
        "do not run lean",
    ):
        assert expected in readme
