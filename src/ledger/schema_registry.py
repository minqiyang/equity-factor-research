"""Versioned fail-closed ledger event-schema registry support.

This module validates only the registry meta-contract and event schemas that
the registry marks ``FROZEN_SUPPORTED``. It does not append events, implement
ledger storage, enforce lifecycle state, or establish campaign completeness.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from functools import lru_cache
import hashlib
from importlib import resources
import json
import re


_PACKAGED_REGISTRY_RESOURCES = {
    "0.1.0": (
        "schemas/experiment_trial_ledger_payload_schema_registry_v1.json",
        "schemas/experiment_trial_ledger_payload_schema_registry_v1.sha256",
    ),
    "0.2.0": (
        "schemas/experiment_trial_ledger_payload_schema_registry_v2.json",
        "schemas/experiment_trial_ledger_payload_schema_registry_v2.sha256",
    ),
    "0.3.0": (
        "schemas/experiment_trial_ledger_payload_schema_registry_v3.json",
        "schemas/experiment_trial_ledger_payload_schema_registry_v3.sha256",
    ),
    "0.4.0": (
        "schemas/experiment_trial_ledger_payload_schema_registry_v4.json",
        "schemas/experiment_trial_ledger_payload_schema_registry_v4.sha256",
    ),
    "0.5.0": (
        "schemas/experiment_trial_ledger_payload_schema_registry_v5.json",
        "schemas/experiment_trial_ledger_payload_schema_registry_v5.sha256",
    ),
    "0.6.0": (
        "schemas/experiment_trial_ledger_payload_schema_registry_v6.json",
        "schemas/experiment_trial_ledger_payload_schema_registry_v6.sha256",
    ),
    "0.7.0": (
        "schemas/experiment_trial_ledger_payload_schema_registry_v7.json",
        "schemas/experiment_trial_ledger_payload_schema_registry_v7.sha256",
    ),
    "0.8.0": (
        "schemas/experiment_trial_ledger_payload_schema_registry_v8.json",
        "schemas/experiment_trial_ledger_payload_schema_registry_v8.sha256",
    ),
    "0.9.0": (
        "schemas/experiment_trial_ledger_payload_schema_registry_v9.json",
        "schemas/experiment_trial_ledger_payload_schema_registry_v9.sha256",
    ),
    "0.10.0": (
        "schemas/experiment_trial_ledger_payload_schema_registry_v10.json",
        "schemas/experiment_trial_ledger_payload_schema_registry_v10.sha256",
    ),
}
_REGISTRY_PROFILES = {
    version: {
        "registry_schema_id": (
            f"experiment_trial_ledger_payload_schema_registry_v{release}"
        ),
        "schema_language_id": "ledger_closed_schema_dsl_v1",
        "schema_language_version": "0.1.0" if release == 1 else "0.2.0",
        "local_constraint_predicates": (
            ["path_equals_path"]
            if release == 1
            else ["array_contains_path", "path_equals_path"]
        ),
    }
    for version, release in (
        ("0.1.0", 1),
        ("0.2.0", 2),
        ("0.3.0", 3),
        ("0.4.0", 4),
        ("0.5.0", 5),
        ("0.6.0", 6),
        ("0.7.0", 7),
        ("0.8.0", 8),
        ("0.9.0", 9),
        ("0.10.0", 10),
    )
}
_SAFE_INTEGER_MIN = -(2**53) + 1
_SAFE_INTEGER_MAX = (2**53) - 1
_TOP_LEVEL_KEYS = {
    "canonicalization_id",
    "closed_event_vocabulary",
    "conformance_vectors",
    "event_identity_projection_id",
    "event_schemas",
    "incomplete_event_types",
    "ledger_schema_version",
    "local_constraint_predicates",
    "operation_request_projection_id",
    "registry_schema_id",
    "registry_status",
    "registry_version",
    "schema_language_id",
    "schema_language_version",
    "type_definitions",
}
_EVENT_SCHEMA_KEYS = {
    "event_schema",
    "event_schema_version",
    "event_type",
    "ledger_schema_version",
    "local_constraints",
    "schema_status",
}
_EVENT_TYPE_PATTERN = re.compile(r"[A-Z][A-Z0-9_]*\Z")
_TYPE_NAME_PATTERN = re.compile(r"[a-z][a-z0-9_]*\Z")
_VECTOR_ID_PATTERN = re.compile(r"[a-z][a-z0-9_]*\Z")
_LOWER_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_TYPED_ID_PREFIX_PATTERN = re.compile(r"[a-z][a-z0-9]{2,7}\Z")
_TYPED_ID_BODY_PATTERN = re.compile(r"[0-9a-f]{32}\Z")
_SAFE_PUBLIC_ID_PATTERN = re.compile(
    r"[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?\Z"
)
_TIMESTAMP_PATTERN = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})"
    r"T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]+))?Z\Z"
)


class LedgerSchemaError(ValueError):
    """A stable fail-closed schema-registry or event-validation error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _fail(code: str, message: str) -> None:
    raise LedgerSchemaError(code, message)


def _object_without_duplicate_keys(
    pairs: Sequence[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail("DUPLICATE_PROPERTY", f"duplicate JSON property: {key}")
        result[key] = value
    return result


def _parse_safe_integer(value: str) -> int:
    digits = value[1:] if value.startswith("-") else value
    if len(digits) > len(str(_SAFE_INTEGER_MAX)):
        _fail("NON_IJSON_NUMBER", "integer is outside the I-JSON safe range")
    try:
        parsed = int(value)
    except ValueError as exc:
        raise LedgerSchemaError(
            "NON_IJSON_NUMBER",
            "integer is not an accepted I-JSON safe integer",
        ) from exc
    if not (_SAFE_INTEGER_MIN <= parsed <= _SAFE_INTEGER_MAX):
        _fail("NON_IJSON_NUMBER", "integer is outside the I-JSON safe range")
    return parsed


def _reject_float(_: str) -> float:
    _fail("NON_IJSON_NUMBER", "floating-point JSON numbers are not accepted")


def _reject_constant(_: str) -> float:
    _fail("NON_IJSON_NUMBER", "non-finite JSON numbers are not accepted")


def parse_json_bytes(raw: bytes) -> object:
    """Decode JSON bytes while rejecting duplicate properties and unsafe numbers."""
    if not isinstance(raw, bytes):
        _fail("INVALID_JSON", "JSON input must be bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LedgerSchemaError("INVALID_JSON", "JSON input must be UTF-8") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_int=_parse_safe_integer,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except LedgerSchemaError:
        raise
    except json.JSONDecodeError as exc:
        raise LedgerSchemaError("INVALID_JSON", "invalid JSON document") from exc


def _require_mapping(value: object, *, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        _fail("INVALID_REGISTRY", f"{context} must be an object")
    if any(not isinstance(key, str) for key in value):
        _fail("INVALID_REGISTRY", f"{context} keys must be strings")
    return value


def _require_list(value: object, *, context: str) -> list[object]:
    if not isinstance(value, list):
        _fail("INVALID_REGISTRY", f"{context} must be an array")
    return value


def _require_string(value: object, *, context: str) -> str:
    if not isinstance(value, str):
        _fail("INVALID_REGISTRY", f"{context} must be a string")
    return value


def _require_exact_keys(
    value: object,
    expected: set[str],
    *,
    context: str,
    code: str = "INVALID_REGISTRY",
) -> dict[str, object]:
    mapping = _require_mapping(value, context=context)
    actual = set(mapping)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        _fail(
            code,
            f"{context} has missing={missing} unknown={unknown}",
        )
    return mapping


def _require_nonnegative_integer(value: object, *, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail("INVALID_REGISTRY", f"{context} must be a nonnegative integer")
    if value > _SAFE_INTEGER_MAX:
        _fail("INVALID_REGISTRY", f"{context} exceeds the I-JSON safe range")
    return value


def _require_ascii_tree(value: object, *, context: str = "registry") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if not (_SAFE_INTEGER_MIN <= value <= _SAFE_INTEGER_MAX):
            _fail("INVALID_REGISTRY", f"{context} has an unsafe integer")
        return
    if isinstance(value, float):
        _fail("INVALID_REGISTRY", f"{context} contains a floating-point value")
    if isinstance(value, str):
        try:
            value.encode("ascii")
        except UnicodeEncodeError as exc:
            raise LedgerSchemaError(
                "INVALID_REGISTRY",
                f"{context} must remain ASCII-only in R0",
            ) from exc
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_ascii_tree(item, context=f"{context}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                _fail(
                    "INVALID_REGISTRY",
                    f"{context} object keys must be strings",
                )
            _require_ascii_tree(key, context=f"{context} key")
            _require_ascii_tree(item, context=f"{context}.{key}")
        return
    _fail("INVALID_REGISTRY", f"{context} contains an unsupported JSON value")


def _canonical_ascii_json_bytes(value: object) -> bytes:
    _require_ascii_tree(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _same_json_value(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _same_json_value(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    if isinstance(left, dict):
        return set(left) == set(right) and all(
            _same_json_value(left[key], right[key]) for key in left
        )
    return left == right


def _require_unique_strings(
    value: object,
    *,
    context: str,
    pattern: re.Pattern[str] | None = None,
) -> list[str]:
    items = _require_list(value, context=context)
    result: list[str] = []
    for index, item in enumerate(items):
        text = _require_string(item, context=f"{context}[{index}]")
        if pattern is not None and pattern.fullmatch(text) is None:
            _fail("INVALID_REGISTRY", f"{context}[{index}] has invalid syntax")
        result.append(text)
    if len(set(result)) != len(result):
        _fail("INVALID_REGISTRY", f"{context} contains duplicates")
    return result


def _validate_schema_node(
    node: object,
    *,
    context: str,
    referenced_types: set[str],
    schema_language_version: str,
) -> None:
    mapping = _require_mapping(node, context=context)
    kind = _require_string(mapping.get("kind"), context=f"{context}.kind")

    if kind == "named":
        exact = _require_exact_keys(
            mapping, {"kind", "name"}, context=context
        )
        name = _require_string(exact["name"], context=f"{context}.name")
        if _TYPE_NAME_PATTERN.fullmatch(name) is None:
            _fail("INVALID_REGISTRY", f"{context}.name has invalid syntax")
        referenced_types.add(name)
        return

    if kind == "literal":
        exact = _require_exact_keys(
            mapping, {"kind", "value"}, context=context
        )
        if isinstance(exact["value"], (list, dict, float)):
            _fail(
                "INVALID_REGISTRY",
                f"{context}.value must be a scalar JSON literal",
            )
        return

    if kind == "typed_id":
        exact = _require_exact_keys(
            mapping, {"kind", "prefix"}, context=context
        )
        prefix = _require_string(exact["prefix"], context=f"{context}.prefix")
        if _TYPED_ID_PREFIX_PATTERN.fullmatch(prefix) is None:
            _fail("INVALID_REGISTRY", f"{context}.prefix has invalid syntax")
        return

    if kind in {"sha256", "ledger_v1_utc_timestamp"}:
        _require_exact_keys(mapping, {"kind"}, context=context)
        return

    if kind == "safe_public_id":
        if schema_language_version != "0.2.0":
            _fail("INVALID_REGISTRY", f"{context} uses unknown schema kind {kind!r}")
        _require_exact_keys(mapping, {"kind"}, context=context)
        return

    if kind == "safe_integer":
        exact = _require_exact_keys(
            mapping, {"kind", "minimum"}, context=context
        )
        _require_nonnegative_integer(
            exact["minimum"], context=f"{context}.minimum"
        )
        return

    if kind == "closed_object":
        exact = _require_exact_keys(
            mapping,
            {"kind", "properties", "required"},
            context=context,
        )
        properties = _require_mapping(
            exact["properties"], context=f"{context}.properties"
        )
        required = _require_unique_strings(
            exact["required"], context=f"{context}.required"
        )
        if required != sorted(required):
            _fail("INVALID_REGISTRY", f"{context}.required must be sorted")
        if not set(required) <= set(properties):
            _fail(
                "INVALID_REGISTRY",
                f"{context}.required names unknown properties",
            )
        for name, child in properties.items():
            if _TYPE_NAME_PATTERN.fullmatch(name) is None:
                _fail(
                    "INVALID_REGISTRY",
                    f"{context}.properties has an invalid property name",
                )
            _validate_schema_node(
                child,
                context=f"{context}.properties.{name}",
                referenced_types=referenced_types,
                schema_language_version=schema_language_version,
            )
        return

    if kind == "array":
        exact = _require_exact_keys(
            mapping,
            {
                "collection_semantics",
                "items",
                "kind",
                "max_items",
                "min_items",
            },
            context=context,
        )
        semantics = _require_string(
            exact["collection_semantics"],
            context=f"{context}.collection_semantics",
        )
        if semantics not in {"ordered", "sorted_unique"}:
            _fail(
                "INVALID_REGISTRY",
                f"{context}.collection_semantics is not closed",
            )
        minimum = _require_nonnegative_integer(
            exact["min_items"], context=f"{context}.min_items"
        )
        maximum = _require_nonnegative_integer(
            exact["max_items"], context=f"{context}.max_items"
        )
        if maximum < minimum:
            _fail("INVALID_REGISTRY", f"{context} has max_items < min_items")
        _validate_schema_node(
            exact["items"],
            context=f"{context}.items",
            referenced_types=referenced_types,
            schema_language_version=schema_language_version,
        )
        return

    if kind == "enum":
        exact = _require_exact_keys(
            mapping, {"kind", "values"}, context=context
        )
        values = _require_list(exact["values"], context=f"{context}.values")
        if not values:
            _fail("INVALID_REGISTRY", f"{context}.values must not be empty")
        canonical = [_canonical_ascii_json_bytes(value) for value in values]
        if canonical != sorted(set(canonical)):
            _fail(
                "INVALID_REGISTRY",
                f"{context}.values must be sorted and unique",
            )
        return

    if kind == "nullable":
        exact = _require_exact_keys(
            mapping, {"kind", "schema"}, context=context
        )
        _validate_schema_node(
            exact["schema"],
            context=f"{context}.schema",
            referenced_types=referenced_types,
            schema_language_version=schema_language_version,
        )
        return

    if kind == "tagged_union":
        if schema_language_version != "0.2.0":
            _fail("INVALID_REGISTRY", f"{context} uses unknown schema kind {kind!r}")
        exact = _require_exact_keys(
            mapping,
            {"discriminator", "kind", "variants"},
            context=context,
        )
        discriminator = _require_string(
            exact["discriminator"],
            context=f"{context}.discriminator",
        )
        if _TYPE_NAME_PATTERN.fullmatch(discriminator) is None:
            _fail(
                "INVALID_REGISTRY",
                f"{context}.discriminator has invalid syntax",
            )
        variants = _require_mapping(
            exact["variants"], context=f"{context}.variants"
        )
        if len(variants) < 2:
            _fail(
                "INVALID_REGISTRY",
                f"{context}.variants must contain at least two branches",
            )
        for tag, branch in variants.items():
            if _TYPE_NAME_PATTERN.fullmatch(tag) is None:
                _fail("INVALID_REGISTRY", f"{context} has invalid variant tag")
            _validate_schema_node(
                branch,
                context=f"{context}.variants.{tag}",
                referenced_types=referenced_types,
                schema_language_version=schema_language_version,
            )
            branch_mapping = _require_mapping(
                branch, context=f"{context}.variants.{tag}"
            )
            if branch_mapping.get("kind") != "closed_object":
                _fail(
                    "INVALID_REGISTRY",
                    f"{context}.variants.{tag} must be a closed_object",
                )
            properties = _require_mapping(
                branch_mapping["properties"],
                context=f"{context}.variants.{tag}.properties",
            )
            required = _require_list(
                branch_mapping["required"],
                context=f"{context}.variants.{tag}.required",
            )
            if discriminator not in required:
                _fail(
                    "INVALID_REGISTRY",
                    f"{context}.variants.{tag} must require the discriminator",
                )
            expected_discriminator = {"kind": "literal", "value": tag}
            if not _same_json_value(
                properties.get(discriminator), expected_discriminator
            ):
                _fail(
                    "INVALID_REGISTRY",
                    f"{context}.variants.{tag} has a mismatched discriminator",
                )
        return

    _fail("INVALID_REGISTRY", f"{context} uses unknown schema kind {kind!r}")


def _named_type_references(
    node: object,
    *,
    definitions: Mapping[str, object],
    seen: frozenset[str] = frozenset(),
) -> None:
    mapping = _require_mapping(node, context="schema node")
    kind = mapping["kind"]
    if kind == "named":
        name = mapping["name"]
        if name not in definitions:
            _fail("INVALID_REGISTRY", f"schema references unknown type {name}")
        if name in seen:
            _fail("INVALID_REGISTRY", f"schema type cycle at {name}")
        _named_type_references(
            definitions[name],
            definitions=definitions,
            seen=seen | {name},
        )
    elif kind == "closed_object":
        for child in mapping["properties"].values():
            _named_type_references(
                child, definitions=definitions, seen=seen
            )
    elif kind == "array":
        _named_type_references(
            mapping["items"], definitions=definitions, seen=seen
        )
    elif kind == "nullable":
        _named_type_references(
            mapping["schema"], definitions=definitions, seen=seen
        )
    elif kind == "tagged_union":
        for branch in mapping["variants"].values():
            _named_type_references(
                branch, definitions=definitions, seen=seen
            )


def _schemas_at_path(
    schema: object,
    path: Sequence[str],
    *,
    definitions: Mapping[str, object],
    _seen_names: frozenset[str] = frozenset(),
) -> list[dict[str, object]] | None:
    node = _require_mapping(schema, context="event schema")
    seen_names = set(_seen_names)
    while node["kind"] == "named":
        name = node["name"]
        if name not in definitions or name in seen_names:
            return None
        seen_names.add(name)
        node = _require_mapping(definitions[name], context="named type")
    if not path:
        return [node]
    if node["kind"] == "nullable":
        return _schemas_at_path(
            node["schema"],
            path,
            definitions=definitions,
            _seen_names=frozenset(seen_names),
        )
    if node["kind"] == "tagged_union":
        resolved: list[dict[str, object]] = []
        for branch in node["variants"].values():
            branch_schemas = _schemas_at_path(
                branch,
                path,
                definitions=definitions,
                _seen_names=frozenset(seen_names),
            )
            if branch_schemas is None:
                return None
            resolved.extend(branch_schemas)
        return resolved
    if node["kind"] != "closed_object":
        return None
    child = node["properties"].get(path[0])
    if child is None:
        return None
    return _schemas_at_path(
        child,
        path[1:],
        definitions=definitions,
        _seen_names=frozenset(seen_names),
    )


def _schema_path_exists(
    schema: object,
    path: Sequence[str],
    *,
    definitions: Mapping[str, object],
) -> bool:
    return _schemas_at_path(
        schema,
        path,
        definitions=definitions,
    ) is not None


def _expanded_schema(
    schema: object,
    *,
    definitions: Mapping[str, object],
    seen: frozenset[str] = frozenset(),
) -> dict[str, object]:
    node = _require_mapping(schema, context="schema")
    kind = node["kind"]
    if kind == "named":
        name = node["name"]
        if name in seen or name not in definitions:
            _fail("INVALID_REGISTRY", f"schema type cycle or unknown type at {name}")
        return _expanded_schema(
            definitions[name],
            definitions=definitions,
            seen=seen | {name},
        )
    if kind == "closed_object":
        return {
            "kind": kind,
            "properties": {
                name: _expanded_schema(child, definitions=definitions, seen=seen)
                for name, child in node["properties"].items()
            },
            "required": list(node["required"]),
        }
    if kind == "array":
        return {
            "kind": kind,
            "collection_semantics": node["collection_semantics"],
            "items": _expanded_schema(
                node["items"], definitions=definitions, seen=seen
            ),
            "min_items": node["min_items"],
            "max_items": node["max_items"],
        }
    if kind == "nullable":
        return {
            "kind": kind,
            "schema": _expanded_schema(
                node["schema"], definitions=definitions, seen=seen
            ),
        }
    if kind == "tagged_union":
        return {
            "kind": kind,
            "discriminator": node["discriminator"],
            "variants": {
                tag: _expanded_schema(branch, definitions=definitions, seen=seen)
                for tag, branch in node["variants"].items()
            },
        }
    return dict(node)


def _schemas_are_compatible(
    left: object,
    right: object,
    *,
    definitions: Mapping[str, object],
) -> bool:
    return _same_json_value(
        _expanded_schema(left, definitions=definitions),
        _expanded_schema(right, definitions=definitions),
    )


def _schema_is_scalar(
    schema: object,
    *,
    definitions: Mapping[str, object],
) -> bool:
    expanded = _expanded_schema(schema, definitions=definitions)
    kind = expanded["kind"]
    if kind == "nullable":
        return _schema_is_scalar(
            expanded["schema"],
            definitions={},
        )
    if kind == "enum":
        return all(
            not isinstance(value, (dict, list))
            for value in expanded["values"]
        )
    return kind in {
        "ledger_v1_utc_timestamp",
        "literal",
        "safe_integer",
        "safe_public_id",
        "sha256",
        "typed_id",
    }


def _validate_constraint(
    value: object,
    *,
    context: str,
    allowed_predicates: set[str],
    event_schema: object,
    definitions: Mapping[str, object],
    schema_language_version: str,
) -> str:
    constraint = _require_exact_keys(
        value,
        {
            "constraint_id",
            "left_path",
            "predicate",
            "right_path",
        },
        context=context,
    )
    constraint_id = _require_string(
        constraint["constraint_id"], context=f"{context}.constraint_id"
    )
    if _VECTOR_ID_PATTERN.fullmatch(constraint_id) is None:
        _fail("INVALID_REGISTRY", f"{context}.constraint_id has invalid syntax")
    predicate = _require_string(
        constraint["predicate"], context=f"{context}.predicate"
    )
    if predicate not in allowed_predicates:
        _fail("INVALID_REGISTRY", f"{context} uses an unknown predicate")
    if schema_language_version == "0.1.0":
        left_path = _require_unique_strings(
            constraint["left_path"], context=f"{context}.left_path"
        )
        right_path = _require_unique_strings(
            constraint["right_path"], context=f"{context}.right_path"
        )
    else:
        left_path = [
            _require_string(item, context=f"{context}.left_path[{index}]")
            for index, item in enumerate(
                _require_list(
                    constraint["left_path"],
                    context=f"{context}.left_path",
                )
            )
        ]
        right_path = [
            _require_string(item, context=f"{context}.right_path[{index}]")
            for index, item in enumerate(
                _require_list(
                    constraint["right_path"],
                    context=f"{context}.right_path",
                )
            )
        ]
    if not left_path or not right_path:
        _fail("INVALID_REGISTRY", f"{context} paths must not be empty")
    if not _schema_path_exists(
        event_schema, left_path, definitions=definitions
    ):
        _fail("INVALID_REGISTRY", f"{context}.left_path does not resolve")
    if not _schema_path_exists(
        event_schema, right_path, definitions=definitions
    ):
        _fail("INVALID_REGISTRY", f"{context}.right_path does not resolve")
    if predicate == "array_contains_path":
        left_schemas = _schemas_at_path(
            event_schema,
            left_path,
            definitions=definitions,
        )
        right_schemas = _schemas_at_path(
            event_schema,
            right_path,
            definitions=definitions,
        )
        if left_schemas is None or right_schemas is None:
            _fail("INVALID_REGISTRY", f"{context} paths do not resolve")
        if any(schema["kind"] != "array" for schema in left_schemas):
            _fail(
                "INVALID_REGISTRY",
                f"{context}.left_path must resolve to a non-null array",
            )
        if any(
            not _schema_is_scalar(schema, definitions=definitions)
            for schema in right_schemas
        ):
            _fail(
                "INVALID_REGISTRY",
                f"{context}.right_path must resolve to a scalar",
            )
        for left_schema in left_schemas:
            for right_schema in right_schemas:
                if not _schemas_are_compatible(
                    left_schema["items"],
                    right_schema,
                    definitions=definitions,
                ):
                    _fail(
                        "INVALID_REGISTRY",
                        f"{context} has incompatible array/scalar schemas",
                    )
    return constraint_id


def _validate_conformance_vectors(
    value: object,
    *,
    vocabulary: set[str],
    supported: set[str],
    incomplete: set[str],
) -> None:
    vectors = _require_list(value, context="conformance_vectors")
    vector_ids: set[str] = set()
    outcomes: set[str] = set()
    accepted_event_types: set[str] = set()
    for index, raw_vector in enumerate(vectors):
        context = f"conformance_vectors[{index}]"
        vector = _require_mapping(raw_vector, context=context)
        input_kind = _require_string(
            vector.get("input_kind"), context=f"{context}.input_kind"
        )
        if input_kind == "event_object":
            exact = _require_exact_keys(
                vector,
                {"expected_code", "input_kind", "value", "vector_id"},
                context=context,
            )
            event = _require_mapping(exact["value"], context=f"{context}.value")
            if exact["expected_code"] == "ACCEPT":
                event_type = event.get("event_type")
                if event_type not in supported:
                    _fail(
                        "INVALID_REGISTRY",
                        f"{context} accepts an unsupported event",
                    )
                accepted_event_types.add(event_type)
        elif input_kind == "raw_event_json":
            exact = _require_exact_keys(
                vector,
                {"expected_code", "input_kind", "raw_json", "vector_id"},
                context=context,
            )
            _require_string(
                exact["raw_json"], context=f"{context}.raw_json"
            )
        else:
            _fail("INVALID_REGISTRY", f"{context} has unknown input_kind")

        vector_id = _require_string(
            exact["vector_id"], context=f"{context}.vector_id"
        )
        if _VECTOR_ID_PATTERN.fullmatch(vector_id) is None:
            _fail("INVALID_REGISTRY", f"{context}.vector_id has invalid syntax")
        if vector_id in vector_ids:
            _fail("INVALID_REGISTRY", "duplicate conformance vector ID")
        vector_ids.add(vector_id)

        outcome = _require_string(
            exact["expected_code"], context=f"{context}.expected_code"
        )
        if outcome not in {
            "ACCEPT",
            "DUPLICATE_PROPERTY",
            "INVALID_EVENT",
            "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
            "UNKNOWN_EVENT_TYPE",
        }:
            _fail("INVALID_REGISTRY", f"{context} has an unknown outcome")
        outcomes.add(outcome)

    if accepted_event_types != supported:
        _fail(
            "INVALID_REGISTRY",
            "every supported event must have an accepted conformance vector",
        )
    if incomplete and "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY" not in outcomes:
        _fail(
            "INVALID_REGISTRY",
            "incomplete support requires a fail-closed conformance vector",
        )
    if vocabulary - incomplete - supported:
        _fail("INVALID_REGISTRY", "event coverage sets do not reconcile")
    for required in {
        "DUPLICATE_PROPERTY",
        "INVALID_EVENT",
        "UNKNOWN_EVENT_TYPE",
    }:
        if required not in outcomes:
            _fail(
                "INVALID_REGISTRY",
                f"conformance vectors do not cover {required}",
            )


def validate_registry(value: object) -> dict[str, object]:
    """Validate one exact supported registry-release meta-contract."""
    candidate = _require_mapping(value, context="schema registry")
    registry_version = _require_string(
        candidate.get("registry_version"),
        context="schema registry.registry_version",
    )
    profile = _REGISTRY_PROFILES.get(registry_version)
    if profile is None:
        _fail("INVALID_REGISTRY", "unsupported registry version")
    registry = _require_exact_keys(
        candidate, _TOP_LEVEL_KEYS, context="schema registry"
    )
    _require_ascii_tree(registry)
    expected_literals = {
        "registry_schema_id": profile["registry_schema_id"],
        "registry_version": registry_version,
        "schema_language_id": profile["schema_language_id"],
        "schema_language_version": profile["schema_language_version"],
        "canonicalization_id": "pit_canonical_json_v1",
        "ledger_schema_version": "experiment_trial_ledger_v1",
        "event_identity_projection_id": "ledger_event_identity_v1",
        "operation_request_projection_id": "ledger_operation_request_v1",
    }
    for field, expected in expected_literals.items():
        if registry[field] != expected:
            _fail("INVALID_REGISTRY", f"unexpected {field}")

    vocabulary = _require_unique_strings(
        registry["closed_event_vocabulary"],
        context="closed_event_vocabulary",
        pattern=_EVENT_TYPE_PATTERN,
    )
    if not vocabulary:
        _fail("INVALID_REGISTRY", "closed_event_vocabulary must not be empty")

    predicates = _require_unique_strings(
        registry["local_constraint_predicates"],
        context="local_constraint_predicates",
        pattern=_TYPE_NAME_PATTERN,
    )
    if predicates != profile["local_constraint_predicates"]:
        _fail("INVALID_REGISTRY", "unexpected local constraint predicate set")

    definitions = _require_mapping(
        registry["type_definitions"], context="type_definitions"
    )
    if not definitions:
        _fail("INVALID_REGISTRY", "type_definitions must not be empty")
    referenced_types: set[str] = set()
    for name, schema in definitions.items():
        if _TYPE_NAME_PATTERN.fullmatch(name) is None:
            _fail("INVALID_REGISTRY", "invalid type definition name")
        _validate_schema_node(
            schema,
            context=f"type_definitions.{name}",
            referenced_types=referenced_types,
            schema_language_version=profile["schema_language_version"],
        )

    supported_types: list[str] = []
    event_schema_keys: set[tuple[str, str, str]] = set()
    event_schemas = _require_list(
        registry["event_schemas"], context="event_schemas"
    )
    if not event_schemas:
        _fail("INVALID_REGISTRY", "event_schemas must not be empty")
    for index, raw_entry in enumerate(event_schemas):
        context = f"event_schemas[{index}]"
        entry = _require_exact_keys(
            raw_entry, _EVENT_SCHEMA_KEYS, context=context
        )
        ledger_version = _require_string(
            entry["ledger_schema_version"],
            context=f"{context}.ledger_schema_version",
        )
        event_version = _require_string(
            entry["event_schema_version"],
            context=f"{context}.event_schema_version",
        )
        event_type = _require_string(
            entry["event_type"], context=f"{context}.event_type"
        )
        if ledger_version != registry["ledger_schema_version"]:
            _fail("INVALID_REGISTRY", f"{context} has wrong ledger version")
        if event_version != "ledger_event_v1":
            _fail("INVALID_REGISTRY", f"{context} has wrong event version")
        if event_type not in vocabulary:
            _fail("INVALID_REGISTRY", f"{context} has unknown event type")
        if entry["schema_status"] != "FROZEN_SUPPORTED":
            _fail("INVALID_REGISTRY", f"{context} is not frozen supported")
        composite_key = (ledger_version, event_version, event_type)
        if composite_key in event_schema_keys:
            _fail("INVALID_REGISTRY", "duplicate event schema key")
        event_schema_keys.add(composite_key)
        supported_types.append(event_type)
        _validate_schema_node(
            entry["event_schema"],
            context=f"{context}.event_schema",
            referenced_types=referenced_types,
            schema_language_version=profile["schema_language_version"],
        )
        constraints = _require_list(
            entry["local_constraints"],
            context=f"{context}.local_constraints",
        )
        constraint_ids: set[str] = set()
        for constraint_index, constraint in enumerate(constraints):
            constraint_id = _validate_constraint(
                constraint,
                context=f"{context}.local_constraints[{constraint_index}]",
                allowed_predicates=set(predicates),
                event_schema=entry["event_schema"],
                definitions=definitions,
                schema_language_version=profile["schema_language_version"],
            )
            if constraint_id in constraint_ids:
                _fail("INVALID_REGISTRY", "duplicate local constraint ID")
            constraint_ids.add(constraint_id)

    if len(set(supported_types)) != len(supported_types):
        _fail("INVALID_REGISTRY", "event type has multiple supported schemas")
    expected_supported_order = [
        event_type for event_type in vocabulary if event_type in supported_types
    ]
    if supported_types != expected_supported_order:
        _fail("INVALID_REGISTRY", "event_schemas are not in vocabulary order")

    incomplete = _require_unique_strings(
        registry["incomplete_event_types"],
        context="incomplete_event_types",
        pattern=_EVENT_TYPE_PATTERN,
    )
    expected_incomplete = [
        event_type
        for event_type in vocabulary
        if event_type not in set(supported_types)
    ]
    if incomplete != expected_incomplete:
        _fail(
            "INVALID_REGISTRY",
            "supported and incomplete events must partition the vocabulary",
        )
    expected_status = (
        "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
        if incomplete
        else "PAYLOAD_SCHEMA_REGISTRY_ACCEPTED"
    )
    if registry["registry_status"] != expected_status:
        _fail("INVALID_REGISTRY", "registry status overstates schema coverage")

    unknown_references = referenced_types - set(definitions)
    if unknown_references:
        _fail(
            "INVALID_REGISTRY",
            f"unknown named type references: {sorted(unknown_references)}",
        )
    if set(definitions) != referenced_types:
        _fail("INVALID_REGISTRY", "registry contains orphan type definitions")
    for schema in definitions.values():
        _named_type_references(schema, definitions=definitions)
    for entry in event_schemas:
        _named_type_references(
            entry["event_schema"], definitions=definitions
        )

    _validate_conformance_vectors(
        registry["conformance_vectors"],
        vocabulary=set(vocabulary),
        supported=set(supported_types),
        incomplete=set(incomplete),
    )
    return registry


def canonical_registry_bytes(registry: object) -> bytes:
    """Return the exact ASCII canonical digest preimage for a valid registry."""
    validated = validate_registry(registry)
    return _canonical_ascii_json_bytes(validated)


def registry_digest(registry: object) -> str:
    """Return the lowercase SHA-256 of the exact registry canonical preimage."""
    return hashlib.sha256(canonical_registry_bytes(registry)).hexdigest()


def _packaged_registry_resources(registry_version: str) -> tuple[str, str]:
    resources_for_version = _PACKAGED_REGISTRY_RESOURCES.get(registry_version)
    if resources_for_version is None:
        _fail("INVALID_REGISTRY", "unsupported packaged registry version")
    return resources_for_version


def _packaged_registry_digest(registry_version: str) -> str:
    _, digest_resource = _packaged_registry_resources(registry_version)
    digest_text = (
        resources.files("ledger")
        .joinpath(digest_resource)
        .read_text(encoding="ascii")
        .strip()
    )
    if _LOWER_SHA256_PATTERN.fullmatch(digest_text) is None:
        _fail("INVALID_REGISTRY", "packaged registry digest is invalid")
    return digest_text


def _require_packaged_registry_authority(registry: object) -> None:
    validated = validate_registry(registry)
    registry_version = validated["registry_version"]
    if registry_digest(validated) != _packaged_registry_digest(registry_version):
        _fail(
            "REGISTRY_DIGEST_MISMATCH",
            "registry is not the packaged digest-bound release authority",
        )


def load_registry_bytes(
    raw: bytes,
    *,
    expected_digest: str,
) -> dict[str, object]:
    """Parse and validate registry bytes against an explicit external digest."""
    registry = validate_registry(parse_json_bytes(raw))
    actual_digest = registry_digest(registry)
    if _LOWER_SHA256_PATTERN.fullmatch(expected_digest) is None:
        _fail("INVALID_REGISTRY", "expected registry digest is invalid")
    if actual_digest != expected_digest:
        _fail("REGISTRY_DIGEST_MISMATCH", "registry digest mismatch")
    return registry


def load_default_registry() -> dict[str, object]:
    """Load the packaged R0 registry and verify its external digest sidecar."""
    return load_registry_release("0.1.0")


@lru_cache(maxsize=None)
def _cached_packaged_registry_release(registry_version: str) -> dict[str, object]:
    registry_resource, _ = _packaged_registry_resources(registry_version)
    raw = resources.files("ledger").joinpath(registry_resource).read_bytes()
    return load_registry_bytes(
        raw,
        expected_digest=_packaged_registry_digest(registry_version),
    )


def load_registry_release(registry_version: str) -> dict[str, object]:
    """Load one explicitly selected packaged registry release and digest."""
    return deepcopy(_cached_packaged_registry_release(registry_version))


def _validate_timestamp(value: object, *, context: str) -> None:
    if not isinstance(value, str):
        _fail("INVALID_EVENT", f"{context} must be a timestamp string")
    match = _TIMESTAMP_PATTERN.fullmatch(value)
    if match is None:
        _fail("INVALID_EVENT", f"{context} is not normalized ledger UTC")
    year, month, day, hour, minute, second = map(int, match.groups()[:6])
    leap_year = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days_in_month = (
        31,
        29 if leap_year else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    )
    if not (1 <= month <= 12 and 1 <= day <= days_in_month[month - 1]):
        _fail("INVALID_EVENT", f"{context} is not a Gregorian date")
    if not (
        0 <= hour <= 23
        and 0 <= minute <= 59
        and 0 <= second <= 59
    ):
        _fail("INVALID_EVENT", f"{context} is not a valid UTC time")
    fraction = match.group(7)
    if fraction is not None and fraction.endswith("0"):
        _fail("INVALID_EVENT", f"{context} has a noncanonical fraction")


def _validate_value(
    schema: object,
    value: object,
    *,
    definitions: Mapping[str, object],
    context: str,
) -> None:
    node = _require_mapping(schema, context=f"{context} schema")
    kind = node["kind"]
    if kind == "named":
        _validate_value(
            definitions[node["name"]],
            value,
            definitions=definitions,
            context=context,
        )
        return
    if kind == "literal":
        if not _same_json_value(value, node["value"]):
            _fail("INVALID_EVENT", f"{context} does not match its literal")
        return
    if kind == "typed_id":
        if not isinstance(value, str):
            _fail("INVALID_EVENT", f"{context} must be a typed ID")
        prefix, separator, body = value.partition("_")
        if (
            separator != "_"
            or prefix != node["prefix"]
            or _TYPED_ID_BODY_PATTERN.fullmatch(body) is None
        ):
            _fail("INVALID_EVENT", f"{context} has the wrong typed-ID syntax")
        return
    if kind == "safe_public_id":
        if (
            not isinstance(value, str)
            or _SAFE_PUBLIC_ID_PATTERN.fullmatch(value) is None
        ):
            _fail("INVALID_EVENT", f"{context} is not a safe public ID")
        return
    if kind == "sha256":
        if (
            not isinstance(value, str)
            or _LOWER_SHA256_PATTERN.fullmatch(value) is None
        ):
            _fail("INVALID_EVENT", f"{context} must be lowercase SHA-256")
        return
    if kind == "ledger_v1_utc_timestamp":
        _validate_timestamp(value, context=context)
        return
    if kind == "safe_integer":
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not (_SAFE_INTEGER_MIN <= value <= _SAFE_INTEGER_MAX)
            or value < node["minimum"]
        ):
            _fail("INVALID_EVENT", f"{context} is not a valid safe integer")
        return
    if kind == "closed_object":
        if not isinstance(value, dict):
            _fail("INVALID_EVENT", f"{context} must be an object")
        if any(not isinstance(key, str) for key in value):
            _fail("INVALID_EVENT", f"{context} keys must be strings")
        properties = node["properties"]
        missing = set(node["required"]) - set(value)
        unknown = set(value) - set(properties)
        if missing or unknown:
            _fail(
                "INVALID_EVENT",
                f"{context} has missing={sorted(missing)} "
                f"unknown={sorted(unknown)}",
            )
        for name, child in properties.items():
            if name in value:
                _validate_value(
                    child,
                    value[name],
                    definitions=definitions,
                    context=f"{context}.{name}",
                )
        return
    if kind == "tagged_union":
        if not isinstance(value, dict):
            _fail("INVALID_EVENT", f"{context} must be a tagged object")
        discriminator = node["discriminator"]
        tag = value.get(discriminator)
        if not isinstance(tag, str) or tag not in node["variants"]:
            _fail("INVALID_EVENT", f"{context} has an unknown discriminator")
        _validate_value(
            node["variants"][tag],
            value,
            definitions=definitions,
            context=context,
        )
        return
    if kind == "array":
        if not isinstance(value, list):
            _fail("INVALID_EVENT", f"{context} must be an array")
        if not (node["min_items"] <= len(value) <= node["max_items"]):
            _fail("INVALID_EVENT", f"{context} has invalid cardinality")
        for index, item in enumerate(value):
            _validate_value(
                node["items"],
                item,
                definitions=definitions,
                context=f"{context}[{index}]",
            )
        if node["collection_semantics"] == "sorted_unique":
            canonical_items = [_canonical_ascii_json_bytes(item) for item in value]
            if canonical_items != sorted(set(canonical_items)):
                _fail("INVALID_EVENT", f"{context} must be sorted and unique")
        return
    if kind == "enum":
        if not any(_same_json_value(value, item) for item in node["values"]):
            _fail("INVALID_EVENT", f"{context} is outside the closed enum")
        return
    if kind == "nullable":
        if value is None:
            return
        _validate_value(
            node["schema"],
            value,
            definitions=definitions,
            context=context,
        )
        return
    _fail("INVALID_EVENT", f"{context} uses an unsupported schema kind")


def _read_path(value: object, path: Sequence[str]) -> object:
    current = value
    for component in path:
        if not isinstance(current, dict) or component not in current:
            _fail("INVALID_EVENT", "constraint path does not resolve")
        current = current[component]
    return current


def validate_event(
    value: object,
    *,
    registry: object | None = None,
) -> dict[str, object]:
    """Validate one event against an exact supported schema or fail closed."""
    if registry is None:
        active_registry = load_default_registry()
    else:
        active_registry = validate_registry(registry)
        _require_packaged_registry_authority(active_registry)
    if not isinstance(value, dict):
        _fail("INVALID_EVENT", "ledger event must be an object")
    event_type = value.get("event_type")
    if not isinstance(event_type, str):
        _fail("INVALID_EVENT", "ledger event_type must be a string")
    vocabulary = set(active_registry["closed_event_vocabulary"])
    if event_type not in vocabulary:
        _fail("UNKNOWN_EVENT_TYPE", f"unknown ledger event type: {event_type}")
    if event_type in set(active_registry["incomplete_event_types"]):
        _fail(
            "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY",
            f"event schema is intentionally incomplete: {event_type}",
        )
    matches = [
        entry
        for entry in active_registry["event_schemas"]
        if entry["event_type"] == event_type
    ]
    if len(matches) != 1:
        _fail("INVALID_REGISTRY", "supported event schema lookup is ambiguous")
    entry = matches[0]
    definitions = active_registry["type_definitions"]
    _validate_value(
        entry["event_schema"],
        value,
        definitions=definitions,
        context=event_type,
    )
    for constraint in entry["local_constraints"]:
        predicate = constraint["predicate"]
        if predicate == "path_equals_path":
            left = _read_path(value, constraint["left_path"])
            right = _read_path(value, constraint["right_path"])
            if not _same_json_value(left, right):
                _fail(
                    "INVALID_EVENT",
                    f"constraint failed: {constraint['constraint_id']}",
                )
        elif predicate == "array_contains_path":
            items = _read_path(value, constraint["left_path"])
            scalar = _read_path(value, constraint["right_path"])
            if not isinstance(items, list) or not any(
                _same_json_value(item, scalar) for item in items
            ):
                _fail(
                    "INVALID_EVENT",
                    f"constraint failed: {constraint['constraint_id']}",
                )
        else:
            _fail("INVALID_REGISTRY", "unknown local constraint predicate")
    return value


def validate_raw_event_bytes(
    raw: bytes,
    *,
    registry: object | None = None,
) -> dict[str, object]:
    """Parse raw event bytes without lossy key collapse, then validate."""
    return validate_event(parse_json_bytes(raw), registry=registry)


def run_conformance_vectors(registry: object) -> dict[str, str]:
    """Execute one registry release's bound synthetic vectors."""
    validated = validate_registry(registry)
    _require_packaged_registry_authority(validated)
    outcomes: dict[str, str] = {}
    for vector in validated["conformance_vectors"]:
        try:
            if vector["input_kind"] == "raw_event_json":
                validate_raw_event_bytes(
                    vector["raw_json"].encode("ascii"),
                    registry=validated,
                )
            else:
                validate_event(vector["value"], registry=validated)
        except LedgerSchemaError as exc:
            outcome = exc.code
        else:
            outcome = "ACCEPT"
        if outcome != vector["expected_code"]:
            _fail(
                "INVALID_REGISTRY",
                f"conformance vector {vector['vector_id']} expected "
                f"{vector['expected_code']} but observed {outcome}",
            )
        outcomes[vector["vector_id"]] = outcome
    return outcomes
