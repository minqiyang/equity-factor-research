import ast
import inspect

import pytest

import data.local_csv_inventory as local_csv_inventory
from data.local_csv_inventory import (
    SUPPORTED_LOCAL_CSV_SCHEMAS,
    LocalCSVInventoryReview,
    validate_local_csv_inventory,
)


def _valid_inventory() -> list[dict[str, object]]:
    return [
        {
            "input_name": "adjusted_close_prices",
            "schema": "wide_price",
            "local_path": r"D:\private\data\prices.csv",
            "source_name": "user supplied export",
            "timestamp_or_version": "2026-06-08 export",
            "known_manual_edits": "none known",
            "mutable": True,
        },
        {
            "input_name": "benchmark",
            "schema": "benchmark_price",
            "local_path": "<redacted benchmark csv>",
            "source_name": "user supplied benchmark export",
            "hash_plan": "hash before loading",
            "known_manual_edits": "none known",
            "mutable": True,
        },
    ]


def test_validate_local_csv_inventory_returns_redacted_summary() -> None:
    review = validate_local_csv_inventory(_valid_inventory())

    assert isinstance(review, LocalCSVInventoryReview)
    assert review.issues == ()
    assert review.issue_count_by_severity == {"high": 0, "medium": 0, "low": 0}
    assert not review.has_high_or_medium_issues
    assert [summary.input_name for summary in review.summaries] == [
        "adjusted_close_prices",
        "benchmark",
    ]
    assert review.summaries[0].schema == "wide_price"
    assert review.summaries[0].path_declared is True
    assert review.summaries[0].source_declared is True
    assert review.summaries[0].version_declared is True
    assert review.summaries[1].hash_plan_declared is True


def test_validate_local_csv_inventory_does_not_store_raw_paths_in_result() -> None:
    raw_path = r"D:\private\research\prices.csv"
    inventory = _valid_inventory()
    inventory[0]["local_path"] = raw_path

    review = validate_local_csv_inventory(inventory)

    assert raw_path not in repr(review)
    assert "prices.csv" not in repr(review)
    assert all(not hasattr(summary, "local_path") for summary in review.summaries)
    assert all(raw_path not in issue.message for issue in review.issues)


@pytest.mark.parametrize(
    ("field_name", "expected_severity"),
    [
        ("input_name", "high"),
        ("schema", "high"),
        ("local_path", "high"),
        ("source_name", "high"),
        ("timestamp_or_version", "high"),
        ("known_manual_edits", "medium"),
    ],
)
def test_validate_local_csv_inventory_flags_missing_required_metadata(
    field_name: str,
    expected_severity: str,
) -> None:
    inventory = _valid_inventory()
    inventory[0][field_name] = ""
    if field_name == "timestamp_or_version":
        inventory[0]["file_hash"] = ""
        inventory[0]["hash_plan"] = ""

    review = validate_local_csv_inventory(inventory)

    assert any(
        issue.field == field_name and issue.severity == expected_severity
        for issue in review.issues
    )
    assert review.has_high_or_medium_issues


def test_validate_local_csv_inventory_accepts_hash_or_hash_plan_as_version_evidence() -> None:
    hash_inventory = _valid_inventory()
    hash_inventory[0]["timestamp_or_version"] = ""
    hash_inventory[0]["file_hash"] = "sha256:abc123"

    plan_inventory = _valid_inventory()
    plan_inventory[0]["timestamp_or_version"] = ""
    plan_inventory[0]["hash_plan"] = "hash before loading"

    assert validate_local_csv_inventory(hash_inventory).issues == ()
    assert validate_local_csv_inventory(plan_inventory).issues == ()


def test_validate_local_csv_inventory_flags_unknown_schema() -> None:
    inventory = _valid_inventory()
    inventory[0]["schema"] = "guessed_vendor_export"

    review = validate_local_csv_inventory(inventory)

    assert "wide_price" in SUPPORTED_LOCAL_CSV_SCHEMAS
    assert any(issue.field == "schema" and issue.severity == "high" for issue in review.issues)


@pytest.mark.parametrize(
    "bad_path",
    [
        "https://example.com/prices.csv",
        "s3://bucket/prices.csv",
        r"D:\private\.env\prices.csv",
        r"D:\private\api_key_exports\prices.csv",
        r"D:\private\secret_exports\prices.csv",
    ],
)
def test_validate_local_csv_inventory_flags_remote_or_credential_like_paths(
    bad_path: str,
) -> None:
    inventory = _valid_inventory()
    inventory[0]["local_path"] = bad_path

    review = validate_local_csv_inventory(inventory)

    assert any(issue.field == "local_path" and issue.severity == "high" for issue in review.issues)
    assert bad_path not in repr(review)


def test_validate_local_csv_inventory_flags_unclear_non_csv_path_but_accepts_placeholder() -> None:
    unclear_inventory = _valid_inventory()
    unclear_inventory[0]["local_path"] = r"D:\private\prices.xlsx"

    unclear_review = validate_local_csv_inventory(unclear_inventory)

    assert any(
        issue.field == "local_path" and issue.severity == "medium"
        for issue in unclear_review.issues
    )

    placeholder_inventory = _valid_inventory()
    placeholder_inventory[0]["local_path"] = "[redacted adjusted close csv]"

    placeholder_review = validate_local_csv_inventory(placeholder_inventory)

    assert placeholder_review.issues == ()


def test_validate_local_csv_inventory_flags_duplicate_input_names() -> None:
    inventory = _valid_inventory()
    inventory[1]["input_name"] = "adjusted_close_prices"

    review = validate_local_csv_inventory(inventory)

    assert any(
        issue.field == "input_name" and issue.severity == "high"
        for issue in review.issues
    )


def test_validate_local_csv_inventory_rejects_invalid_inventory_shape() -> None:
    with pytest.raises(ValueError, match="at least one"):
        validate_local_csv_inventory([])

    with pytest.raises(TypeError, match="sequence"):
        validate_local_csv_inventory("not a sequence")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="mapping"):
        validate_local_csv_inventory([object()])  # type: ignore[list-item]

    inventory = _valid_inventory()
    inventory[0]["mutable"] = "yes"
    with pytest.raises(TypeError, match="mutable"):
        validate_local_csv_inventory(inventory)


def test_local_csv_inventory_module_has_no_file_io_or_remote_data_or_trading_imports() -> None:
    source = inspect.getsource(local_csv_inventory)
    tree = ast.parse(source)
    forbidden_import_terms = [
        "pathlib",
        "requests",
        "urllib",
        "yfinance",
        "alpaca",
        "ccxt",
        "broker",
        "brokerage",
        "order",
        "execution",
        "live_trading",
    ]

    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    for module_name in imported_modules:
        assert not any(term in module_name for term in forbidden_import_terms)

    forbidden_calls = {"open", "read_csv"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"open", "exists", "is_file", "read_text"}
