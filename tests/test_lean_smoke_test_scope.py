import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LEAN_DIR = REPO_ROOT / "lean"
SCAFFOLD_PATH = LEAN_DIR / "smoke_test_algorithm.py"
README_PATH = LEAN_DIR / "README.md"


BANNED_IMPORT_ROOTS = {"requests", "yfinance", "alpaca", "ccxt", "os"}
BANNED_CALL_NAMES = {
    "SetHoldings",
    "MarketOrder",
    "LimitOrder",
    "StopMarketOrder",
    "Liquidate",
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
}


def _source() -> str:
    return SCAFFOLD_PATH.read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_source(), filename=str(SCAFFOLD_PATH))


def test_lean_scaffold_expected_files_exist() -> None:
    assert README_PATH.is_file()
    assert SCAFFOLD_PATH.is_file()
    assert not (LEAN_DIR / "config.json").exists()


def test_lean_scaffold_is_metadata_only_and_not_runtime_dependent() -> None:
    source = _source()

    assert "IS_EXECUTABLE_LEAN_ALGORITHM: Final[bool] = False" in source
    assert "SCAFFOLD_STATUS: Final[str]" in source

    for snippet in BANNED_TEXT_SNIPPETS:
        assert snippet not in source


def test_lean_scaffold_has_no_external_download_or_credential_imports() -> None:
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".")[0].lower() for alias in node.names}
            assert imported_roots.isdisjoint(BANNED_IMPORT_ROOTS)
        elif isinstance(node, ast.ImportFrom):
            module_root = (node.module or "").split(".")[0].lower()
            assert module_root not in BANNED_IMPORT_ROOTS


def test_lean_scaffold_has_no_order_or_brokerage_calls() -> None:
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in BANNED_CALL_NAMES
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in BANNED_CALL_NAMES


def test_lean_scaffold_declares_timing_contract_and_diagnostics() -> None:
    source = _source()

    for expected in (
        "algorithm_time",
        "latest_completed_data_date",
        "feature_date",
        "simulated_order_date",
        "evaluation_date",
        "eligible_count",
        "skipped_count",
        "selected_symbols",
        "target_weights",
        "benchmark_symbol",
        "fee_model",
        "slippage_model",
        "caveats",
    ):
        assert expected in source


def test_lean_scaffold_readme_preserves_guardrails() -> None:
    readme = README_PATH.read_text(encoding="utf-8").lower()

    for expected in (
        "non-executing",
        "not a runnable lean project",
        "no real market data",
        "no live trading",
        "no brokerage",
        "no profitability claims",
        "do not run lean",
    ):
        assert expected in readme
