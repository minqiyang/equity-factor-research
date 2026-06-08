"""Dry-run validation for declared local CSV research inventories.

This module validates metadata that a user declares before a local CSV research
run. It does not read files, check path existence, hash data, download data,
call vendor APIs, store credentials, connect to brokers, place orders, or make
profitability claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


SUPPORTED_LOCAL_CSV_SCHEMAS = frozenset(
    {
        "wide_price",
        "long_price",
        "ohlcv_long",
        "benchmark_price",
        "benchmark_return",
        "universe_membership",
        "factor_panel",
        "metadata",
    }
)

REMOTE_PATH_PREFIXES = (
    "http://",
    "https://",
    "ftp://",
    "s3://",
    "gs://",
)

CREDENTIAL_LIKE_PATH_MARKERS = (
    ".env",
    "api_key",
    "apikey",
    "credential",
    "id_rsa",
    "password",
    "private_key",
    "secret",
    "token",
)


@dataclass(frozen=True)
class LocalCSVInventoryIssue:
    """A validation issue that avoids storing source file paths."""

    severity: str
    input_name: str
    field: str
    message: str


@dataclass(frozen=True)
class LocalCSVInventorySummary:
    """Redacted per-input summary for a declared local CSV file."""

    input_name: str
    schema: str
    path_declared: bool
    source_declared: bool
    version_declared: bool
    file_hash_declared: bool
    hash_plan_declared: bool
    known_manual_edits_declared: bool
    mutable: bool


@dataclass(frozen=True)
class LocalCSVInventoryReview:
    """Dry-run inventory review result with no raw file paths."""

    summaries: tuple[LocalCSVInventorySummary, ...]
    issues: tuple[LocalCSVInventoryIssue, ...]
    issue_count_by_severity: Mapping[str, int]
    caveats: tuple[str, ...]

    @property
    def has_high_or_medium_issues(self) -> bool:
        """Return whether interpretation should stop under the workflow gate."""

        return any(issue.severity in {"high", "medium"} for issue in self.issues)


def validate_local_csv_inventory(
    inventory: Sequence[Mapping[str, object]],
) -> LocalCSVInventoryReview:
    """Validate declared local CSV inventory metadata without reading files.

    Each inventory item should include at least:

    - ``input_name``: stable label such as ``adjusted_close_prices``.
    - ``schema``: one of ``SUPPORTED_LOCAL_CSV_SCHEMAS``.
    - ``local_path``: a local CSV path or redacted local CSV placeholder.
    - ``source_name``: user-supplied source label.
    - ``timestamp_or_version`` or ``file_hash`` or ``hash_plan`` for mutable
      files.

    The returned review intentionally records only redacted metadata flags, not
    the raw local path.
    """

    if isinstance(inventory, (str, bytes)) or not isinstance(inventory, Sequence):
        raise TypeError("inventory must be a sequence of mappings")
    if not inventory:
        raise ValueError("inventory must contain at least one declared input")

    issues: list[LocalCSVInventoryIssue] = []
    summaries: list[LocalCSVInventorySummary] = []
    seen_names: set[str] = set()

    for position, item in enumerate(inventory):
        if not isinstance(item, Mapping):
            raise TypeError("each inventory item must be a mapping")

        fallback_name = f"input_{position + 1}"
        input_name = _text_value(item, "input_name") or fallback_name
        schema = _text_value(item, "schema")
        local_path = _text_value(item, "local_path")
        source_name = _text_value(item, "source_name")
        timestamp_or_version = _text_value(item, "timestamp_or_version")
        file_hash = _text_value(item, "file_hash")
        hash_plan = _text_value(item, "hash_plan")
        known_manual_edits = _text_value(item, "known_manual_edits")
        mutable = _bool_value(item.get("mutable", True), field_name="mutable")

        if not _text_value(item, "input_name"):
            issues.append(
                _issue(
                    "high",
                    fallback_name,
                    "input_name",
                    "input_name is required so issues can be traced without exposing a path",
                )
            )
        elif input_name in seen_names:
            issues.append(
                _issue(
                    "high",
                    input_name,
                    "input_name",
                    "input_name must be unique within the declared inventory",
                )
            )
        seen_names.add(input_name)

        if not schema:
            issues.append(_issue("high", input_name, "schema", "schema is required"))
            summary_schema = "missing"
        elif schema not in SUPPORTED_LOCAL_CSV_SCHEMAS:
            issues.append(
                _issue(
                    "high",
                    input_name,
                    "schema",
                    "schema is not one of the supported local CSV schema labels",
                )
            )
            summary_schema = schema
        else:
            summary_schema = schema

        if not local_path:
            issues.append(
                _issue("high", input_name, "local_path", "local_path or a redacted placeholder is required")
            )
        else:
            _validate_declared_path(local_path, input_name=input_name, issues=issues)

        if not source_name:
            issues.append(
                _issue("high", input_name, "source_name", "source_name supplied by the user is required")
            )

        has_version_evidence = bool(timestamp_or_version or file_hash or hash_plan)
        if mutable and not has_version_evidence:
            issues.append(
                _issue(
                    "high",
                    input_name,
                    "timestamp_or_version",
                    "mutable files require timestamp_or_version, file_hash, or hash_plan before loading",
                )
            )
        elif not mutable and not has_version_evidence:
            issues.append(
                _issue(
                    "medium",
                    input_name,
                    "timestamp_or_version",
                    "immutable files should still declare timestamp_or_version, file_hash, or hash_plan",
                )
            )

        if not known_manual_edits:
            issues.append(
                _issue(
                    "medium",
                    input_name,
                    "known_manual_edits",
                    "known manual edits must be declared, even when the answer is none known",
                )
            )

        summaries.append(
            LocalCSVInventorySummary(
                input_name=input_name,
                schema=summary_schema,
                path_declared=bool(local_path),
                source_declared=bool(source_name),
                version_declared=bool(timestamp_or_version),
                file_hash_declared=bool(file_hash),
                hash_plan_declared=bool(hash_plan),
                known_manual_edits_declared=bool(known_manual_edits),
                mutable=mutable,
            )
        )

    return LocalCSVInventoryReview(
        summaries=tuple(summaries),
        issues=tuple(issues),
        issue_count_by_severity=_issue_counts(issues),
        caveats=(
            "dry-run inventory review only",
            "does not read local files or validate file contents",
            "does not store raw local paths in the review result",
            "not real-data evidence, trading readiness, or a profitability claim",
        ),
    )


def _validate_declared_path(
    local_path: str,
    *,
    input_name: str,
    issues: list[LocalCSVInventoryIssue],
) -> None:
    lowered = local_path.lower()
    if lowered.startswith(REMOTE_PATH_PREFIXES):
        issues.append(
            _issue(
                "high",
                input_name,
                "local_path",
                "remote paths are not allowed for local CSV inventory review",
            )
        )

    if any(marker in lowered for marker in CREDENTIAL_LIKE_PATH_MARKERS):
        issues.append(
            _issue(
                "high",
                input_name,
                "local_path",
                "credential-like path markers must be removed or replaced with a neutral placeholder",
            )
        )

    if not (_looks_like_csv_path(local_path) or _looks_like_redacted_placeholder(local_path)):
        issues.append(
            _issue(
                "medium",
                input_name,
                "local_path",
                "local_path should point to a CSV file or use a redacted CSV placeholder",
            )
        )


def _looks_like_csv_path(value: str) -> bool:
    return value.strip().lower().endswith(".csv")


def _looks_like_redacted_placeholder(value: str) -> bool:
    text = value.strip().lower()
    return (
        "redacted" in text
        or "placeholder" in text
        or (text.startswith("<") and text.endswith(">") and "csv" in text)
        or (text.startswith("[") and text.endswith("]") and "csv" in text)
    )


def _text_value(item: Mapping[str, object], field_name: str) -> str:
    value = item.get(field_name, "")
    if value is None:
        return ""
    return str(value).strip()


def _bool_value(value: object, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise TypeError(f"{field_name} must be a bool")


def _issue(
    severity: str,
    input_name: str,
    field: str,
    message: str,
) -> LocalCSVInventoryIssue:
    if severity not in {"high", "medium", "low"}:
        raise ValueError("severity must be high, medium, or low")
    return LocalCSVInventoryIssue(
        severity=severity,
        input_name=input_name,
        field=field,
        message=message,
    )


def _issue_counts(issues: Sequence[LocalCSVInventoryIssue]) -> Mapping[str, int]:
    return {
        "high": sum(issue.severity == "high" for issue in issues),
        "medium": sum(issue.severity == "medium" for issue in issues),
        "low": sum(issue.severity == "low" for issue in issues),
    }


__all__ = [
    "LocalCSVInventoryIssue",
    "LocalCSVInventoryReview",
    "LocalCSVInventorySummary",
    "SUPPORTED_LOCAL_CSV_SCHEMAS",
    "validate_local_csv_inventory",
]
