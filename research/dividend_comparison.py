"""Read-only ordinary synthetic dividend evidence under the accepted Step 3 contract.

The callable/evidence fields are documented in docs/dividend_comparison_api.md.
Exact classification operates on admitted binary64 values in the rational field.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import math
from numbers import Integral, Real
from pathlib import Path
import re
import tempfile
from typing import Callable

import numpy as np
import pandas as pd


CONVENTION = "synthetic_ordinary_cash_dividend_gross_ex_close_v1"
TOLERANCE = Fraction(1, 10**12)
ANCHORS = ("raw_prior", "raw_ex", "adjusted_prior", "adjusted_ex")
ROLES = (*ANCHORS, "events", "identity", "raw_field", "adjusted_field", "policy", "source_times")
AVAILABILITY_FIELDS = (
    "source_published_at", "public_available_at", "provider_available_at",
    "revision_published_at", "parent_available_at", "known_at", "retrieved_at_utc",
)
REASONS = (
    "evidence_identity_unproven", "identity_unresolved", "duplicate_event_revision",
    "revision_lineage_unresolved", "event_evidence_absent", "event_evidence_empty",
    "event_type_unsupported", "multiple_events_in_window", "policy_unresolved",
    "basis_unknown", "basis_incompatible", "currency_or_unit_incompatible",
    "anchor_missing", "window_invalid", "coverage_unproven",
    "event_unavailable_at_cutoff", "availability_inconsistent", "availability_unproven",
    "observation_unusable", "numeric_invalid", "numeric_domain_invalid",
    "arithmetic_nonfinite", "comparison_precision_insufficient",
)


@dataclass(frozen=True)
class DividendWindow:
    """One explicit security/listing/window scope and its independent evidence."""

    item_id: str
    security_id: str
    listing_id: str
    asset: str
    prior: str
    ex: str
    cutoff: str
    evidence: dict | None


@dataclass(frozen=True)
class DividendComparisonRequest:
    windows: tuple[DividendWindow, ...]
    convention: str = CONVENTION


def _timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z", value
    ):
        return None
    try:
        return pd.Timestamp(value)
    except ValueError:
        return None


def _label(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return pd.Timestamp(value)
    except ValueError:
        return None


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _rational(value):
    """Admit the original mathematical value before any lossy conversion."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (Real, Decimal)):
        return None
    try:
        original = Fraction(int(value)) if isinstance(value, Integral) else Fraction(
            *value.as_integer_ratio()
        ) if hasattr(value, "as_integer_ratio") else Fraction(value)
        encoded = float(value)
        if not math.isfinite(encoded) or Fraction(*encoded.as_integer_ratio()) != original:
            return None
        return original
    except (ValueError, OverflowError):
        return None


def json_evidence(value):
    """Retain exact scalars and typed invalid/nonfinite observations in JSON."""
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            return {
                "json_evidence": "dict_items",
                "items": [
                    {
                        "json_evidence": "pair",
                        "key": json_evidence(key),
                        "value": json_evidence(nested),
                    }
                    for key, nested in value.items()
                ],
            }
        return {
            "json_evidence": "object",
            "items": {key: json_evidence(nested) for key, nested in value.items()},
        }
    if isinstance(value, tuple):
        return {"json_evidence": "tuple", "items": [json_evidence(nested) for nested in value]}
    if isinstance(value, list):
        return [json_evidence(nested) for nested in value]
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, np.bool_):
        return {"type": "bool", "value": bool(value)}
    if isinstance(value, Integral):
        return {"type": type(value).__name__, "value": str(int(value))}
    if isinstance(value, Fraction):
        return {"numerator": str(value.numerator), "denominator": str(value.denominator)}
    if isinstance(value, Decimal):
        return {"type": "Decimal", "value": str(value)}
    if isinstance(value, Real):
        if np.isnan(value):
            return {"type": "nonfinite", "value": "nan"}
        if np.isinf(value):
            return {"type": "nonfinite", "value": "+inf" if value > 0 else "-inf"}
        return {"type": type(value).__name__, "ratio": json_evidence(Fraction(*value.as_integer_ratio()))}
    if isinstance(value, (complex, np.complexfloating)):
        return {"type": "complex", "real": json_evidence(value.real), "imag": json_evidence(value.imag)}
    return {"type": type(value).__name__, "state": "unsupported"}


def evidence_sha256(evidence: dict) -> str:
    """Hash the retained fixture contents, excluding their declared digest."""
    contents = {key: value for key, value in evidence.items() if key != "sha256"}
    return hashlib.sha256(json.dumps(
        json_evidence(contents), sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def _validate_request(request):
    if not isinstance(request, DividendComparisonRequest):
        raise TypeError("comparison_request must be a DividendComparisonRequest")
    if request.convention != CONVENTION:
        raise ValueError("unsupported comparison convention")
    if not isinstance(request.windows, tuple) or not request.windows:
        raise ValueError("comparison request requires a nonempty tuple of windows")
    ids, scopes = set(), set()
    for window in request.windows:
        if not isinstance(window, DividendWindow):
            raise TypeError("requested window must be a DividendWindow")
        if not all(_text(getattr(window, key)) for key in ("item_id", "security_id", "listing_id", "asset")):
            raise ValueError("requested window requires explicit item/security/listing/asset scope")
        if not window.security_id.startswith("SYNTH:") or not window.listing_id.startswith("SYNTH:"):
            raise ValueError("comparison scope requires synthetic security/listing identifiers")
        prior, ex, cutoff = _label(window.prior), _label(window.ex), _timestamp(window.cutoff)
        if prior is None or ex is None or prior >= ex or cutoff is None:
            raise ValueError("invalid requested window/cutoff encoding")
        scope = (window.security_id, window.listing_id, window.prior, window.ex)
        if window.item_id in ids or scope in scopes:
            raise ValueError("duplicate requested item or security/window scope")
        ids.add(window.item_id)
        scopes.add(scope)
        if window.evidence is not None and not isinstance(window.evidence, dict):
            raise TypeError("window evidence must be a dict or None")


def _overlapping_identity_conflicts(windows):
    """Return item IDs whose overlapping scopes assign contradictory identities."""
    affected = set()
    ordered = tuple(windows)
    for index, left in enumerate(ordered):
        left_labels = {left.prior, left.ex}
        left_identity = (left.security_id, left.listing_id)
        for right in ordered[index + 1:]:
            if not left_labels.intersection((right.prior, right.ex)):
                continue
            right_identity = (right.security_id, right.listing_id)
            same_asset = left.asset == right.asset
            same_identity = left_identity == right_identity
            if same_asset != same_identity:
                affected.add(left.item_id)
                affected.add(right.item_id)
    return affected


def _contains_non_string_keys(value):
    if isinstance(value, dict):
        return any(not isinstance(key, str) for key in value) or any(
            _contains_non_string_keys(nested) for nested in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_non_string_keys(nested) for nested in value)
    return False


def _availability(record, cutoff, reasons, *, event=False):
    availability = _mapping(_mapping(record).get("availability"))
    times = {key: _timestamp(availability.get(key)) for key in AVAILABILITY_FIELDS}
    if any(value is None for value in times.values()):
        reasons.add("availability_unproven")
        return False
    known = times["known_at"]
    if any(known < times[key] for key in AVAILABILITY_FIELDS[:-2]):
        reasons.add("availability_inconsistent")
    if times["retrieved_at_utc"] < known:
        reasons.add("availability_inconsistent")
    available = all(value <= cutoff for value in times.values())
    if not available and not event:
        reasons.add("availability_unproven")
    return available


def _classify(reference, supplied, diagnostic):
    """Exact classification; explicit missing-classification diagnostics for D32/D47."""
    if reference is None or supplied is None:
        reason = "arithmetic_nonfinite" if any(
            not math.isfinite(value) for value in diagnostic.values()
        ) else "comparison_precision_insufficient"
        return {"comparison_status": "INSUFFICIENT_EVIDENCE", "compared": 0, "reasons": [reason]}
    delta = supplied - reference
    matched = abs(delta) <= TOLERANCE
    return {
        "comparison_status": "MATCHED" if matched else "MISMATCHED", "compared": 1,
        "reasons": ["within_tolerance" if matched else "return_difference"],
        "reference": json_evidence(reference), "supplied": json_evidence(supplied),
        "delta": json_evidence(delta), "tolerance": json_evidence(TOLERANCE),
    }


def _compare_window(window: DividendWindow, prices: pd.DataFrame, conflicting_items=frozenset()) -> dict:
    """Diagnose one structurally validated requested window without mutating inputs."""
    evidence = window.evidence
    record = {
        "record_type": "dividend_comparison_item", "item_id": window.item_id,
        "scope": {key: value for key, value in asdict(window).items() if key != "evidence"},
        "convention": CONVENTION, "requested": 1, "compared": 0,
        "comparison_status": "INSUFFICIENT_EVIDENCE", "economic_acceptance": False,
        "evidence": json_evidence(evidence), "selected_revision": None,
        "excluded_revisions": [],
    }
    if evidence is None or evidence == {}:
        record["reasons"] = ["event_evidence_absent" if evidence is None else "event_evidence_empty"]
        return record
    reasons = set()
    cutoff = _timestamp(window.cutoff)
    prior, ex = _label(window.prior), _label(window.ex)
    if (not _text(evidence.get("vintage_id")) or not _text(evidence.get("provenance"))
            or evidence.get("sha256") != evidence_sha256(evidence)
            or _contains_non_string_keys(evidence)):
        reasons.add("evidence_identity_unproven")
    record["evidence_sha256"] = evidence_sha256(evidence)
    record["vintage_id"] = json_evidence(evidence.get("vintage_id"))
    raw = _mapping(evidence.get("raw_field"))
    adjusted = _mapping(evidence.get("adjusted_field"))
    for field in (raw, adjusted):
        if not _text(field.get("provenance")) or not _text(field.get("field_id")):
            reasons.add("evidence_identity_unproven")
    if raw.get("provenance") == adjusted.get("provenance"):
        reasons.add("evidence_identity_unproven")
    if any(not _text(adjusted.get(key)) for key in ("adjustment_set_id", "version", "scale_id")):
        reasons.add("evidence_identity_unproven")
    if raw.get("basis") in (None, "UNKNOWN") or raw.get("share_basis") in (None, "UNKNOWN") or adjusted.get("basis") in (None, "UNKNOWN", "vendor_adjusted", "adjusted_close"):
        reasons.add("basis_unknown")
    if (raw.get("basis") not in (None, "UNKNOWN", "raw")
            or raw.get("share_basis") not in (None, "UNKNOWN", "unchanged_ordinary_share")
            or adjusted.get("basis") not in (None, "UNKNOWN", "vendor_adjusted", "adjusted_close", "gross_total_return")):
        reasons.add("basis_incompatible")
    if raw.get("currency") != "USD" or raw.get("units") != "USD/share" or adjusted.get("currency") != "USD" or adjusted.get("units") != "index_points":
        reasons.add("currency_or_unit_incompatible")
    policy = _mapping(evidence.get("policy"))
    expected_policy = {"entitlement": "pre_ex_holder", "dividend": "gross", "withholding": "zero", "reinvestment": "ex_close"}
    if any(policy.get(key) is None for key in expected_policy):
        reasons.add("policy_unresolved")
    if any(policy.get(key) is not None and policy.get(key) != value for key, value in expected_policy.items()):
        reasons.add("basis_incompatible")

    source_times = _mapping(evidence.get("source_times"))
    mapping = source_times.get("rows", [])
    closes = []
    for label in (window.prior, window.ex):
        matches = [row for row in mapping if isinstance(row, dict) and row.get("label") == label] if isinstance(mapping, list) else []
        closes.append(_timestamp(matches[0].get("close")) if len(matches) == 1 else None)
    close_p, close_e = closes
    if isinstance(mapping, list):
        for close in closes:
            if close is not None and sum(
                _timestamp(_mapping(row).get("close")) == close for row in mapping
            ) != 1:
                reasons.add("window_invalid")
    if close_p is None or close_e is None or close_p >= close_e or cutoff <= close_e:
        reasons.add("window_invalid")
    if prior not in prices.index or ex not in prices.index:
        reasons.add("anchor_missing")
    if (not isinstance(prices.index, pd.DatetimeIndex) or not prices.index.is_unique
            or not prices.index.is_monotonic_increasing or prices.index.tz is not None
            or prior not in prices.index or ex not in prices.index):
        reasons.add("window_invalid")
    elif prices.index.get_loc(ex) != prices.index.get_loc(prior) + 1:
        reasons.add("window_invalid")
    if not prices.columns.is_unique or window.asset not in prices.columns:
        reasons.add("identity_unresolved")
    identity = _mapping(evidence.get("identity"))
    mappings = identity.get("mappings")
    target = {"asset": window.asset, "security_id": window.security_id, "listing_id": window.listing_id}
    if (not isinstance(mappings, list) or mappings.count(target) != 1
            or any(not isinstance(row, dict) or (row != target and (
                row.get("asset") == window.asset or (row.get("security_id"), row.get("listing_id")) == (window.security_id, window.listing_id)
            )) for row in mappings)):
        reasons.add("identity_unresolved")
    start, end = _timestamp(identity.get("effective_from")), _timestamp(identity.get("effective_to"))
    state = identity.get("effective_to_state")
    if (start is None or close_p is None or start > close_p or "effective_to" not in identity
            or state not in ("FINITE", "OPEN_IN_VINTAGE")
            or (state == "OPEN_IN_VINTAGE" and identity.get("effective_to") is not None)
            or (state == "FINITE" and (end is None or close_e is None or close_e >= end))):
        reasons.add("identity_unresolved")
    if window.item_id in conflicting_items:
        reasons.add("identity_unresolved")
    coverage = _mapping(evidence.get("coverage"))
    vintage_cutoff = _timestamp(evidence.get("as_of_cutoff"))
    if vintage_cutoff is None or vintage_cutoff < cutoff:
        reasons.add("coverage_unproven")
    for role in ROLES:
        covered = _mapping(coverage.get(role))
        first, last = _timestamp(covered.get("from")), _timestamp(covered.get("through"))
        if (covered.get("verified") is not True or covered.get("complete") is not True
                or first is None or last is None or close_p is None or first > close_p or last < cutoff):
            reasons.add("coverage_unproven")
    _availability(coverage, cutoff, reasons)
    for role in ("identity", "raw_field", "adjusted_field", "policy", "source_times"):
        _availability(evidence.get(role), cutoff, reasons)

    numbers = {}
    observations = {}
    bindable = (
        isinstance(prices.index, pd.DatetimeIndex)
        and prices.index.tz is None
        and prices.index.is_unique
        and prior in prices.index
        and ex in prices.index
        and prices.columns.is_unique
        and window.asset in prices.columns
    )
    for role in ANCHORS:
        anchor = _mapping(evidence.get(role))
        observations[role] = json_evidence(anchor.get("status", "MISSING"))
        missing_value = "value" not in anchor or (
            anchor.get("value") is None and _text(anchor.get("status"))
            and anchor.get("status") != "OBSERVED"
        )
        if missing_value:
            reasons.add("anchor_missing")
        if anchor.get("status") != "OBSERVED":
            reasons.add("observation_unusable")
        expected_label = window.prior if role.endswith("prior") else window.ex
        if anchor.get("label") != expected_label:
            reasons.add("window_invalid")
        if any(anchor.get(key) != value for key, value in target.items() if key != "asset"):
            reasons.add("identity_unresolved")
        field = raw if role.startswith("raw") else adjusted
        if anchor.get("field_id") != field.get("field_id") or not _text(anchor.get("provenance")):
            reasons.add("evidence_identity_unproven")
        _availability(anchor, cutoff, reasons)
        close = close_p if role.endswith("prior") else close_e
        known = _timestamp(_mapping(anchor.get("availability")).get("known_at"))
        for parent in (field, identity, source_times):
            parent_known = _timestamp(_mapping(parent.get("availability")).get("known_at"))
            if known is not None and parent_known is not None and known < parent_known:
                reasons.add("availability_inconsistent")
        if close is not None and known is not None and known <= close:
            reasons.add("availability_inconsistent")
        value = _rational(anchor.get("value"))
        if value is None and not missing_value:
            reasons.add("numeric_invalid")
        elif value is not None and value <= 0:
            reasons.add("numeric_domain_invalid")
        numbers[role] = value
        if role.startswith("adjusted") and value is not None and bindable:
            supplied = _rational(prices.at[_label(expected_label), window.asset])
            if supplied != value:
                reasons.add("evidence_identity_unproven")

    events = evidence.get("events")
    if events is None:
        reasons.add("event_evidence_absent")
        events = []
    elif not isinstance(events, list):
        reasons.add("event_evidence_absent")
        events = []
    elif not events:
        reasons.add("event_evidence_empty")
    eligible = []
    keys = []
    for event in events:
        event = _mapping(event)
        key = (event.get("event_id"), event.get("revision_id"))
        if not all(_text(part) for part in key):
            reasons.add("revision_lineage_unresolved")
        if key in keys:
            reasons.add("duplicate_event_revision")
        keys.append(key)
        available = _availability(event, cutoff, reasons, event=True)
        if not available:
            record["excluded_revisions"].append(json_evidence(event))
            continue
        event_known = _timestamp(_mapping(event.get("availability")).get("known_at"))
        identity_known = _timestamp(_mapping(identity.get("availability")).get("known_at"))
        if event_known is not None and identity_known is not None and event_known < identity_known:
            reasons.add("availability_inconsistent")
        if event.get("security_id") != window.security_id or event.get("listing_id") != window.listing_id:
            reasons.add("identity_unresolved")
        if event.get("ex_date") != window.ex:
            reasons.add("window_invalid")
        if event.get("event_type") != "ordinary_cash_dividend":
            reasons.add("event_type_unsupported")
        if not _text(event.get("provenance")):
            reasons.add("evidence_identity_unproven")
        eligible.append(event)
    if events and not eligible:
        reasons.add("event_unavailable_at_cutoff")
    event_ids = {row.get("event_id") for row in eligible if _text(row.get("event_id"))}
    if len(event_ids) > 1:
        reasons.add("multiple_events_in_window")
    selected = None
    candidates = []
    for event_id in sorted(event_ids):
        history = [row for row in eligible if row.get("event_id") == event_id]
        by_revision = {row.get("revision_id"): row for row in history if _text(row.get("revision_id"))}
        parents = [row.get("supersedes") for row in history]
        heads = [row for row in history if row.get("revision_id") not in parents]
        candidates.extend(heads or history)
        if len(heads) != 1:
            reasons.add("revision_lineage_unresolved")
        for row in history:
            seen = set()
            current = row
            while current is not None:
                revision = current.get("revision_id")
                if not _text(revision) or revision in seen or "supersedes" not in current:
                    reasons.add("revision_lineage_unresolved")
                    break
                seen.add(revision)
                parent = current.get("supersedes")
                if parent is None:
                    break
                if not _text(parent) or parent not in by_revision:
                    reasons.add("revision_lineage_unresolved")
                    break
                predecessor = by_revision[parent]
                if any(current.get(key) != predecessor.get(key) for key in ("security_id", "listing_id", "ex_date", "event_type")):
                    reasons.add("revision_lineage_unresolved")
                if _timestamp(current["availability"]["known_at"]) < _timestamp(predecessor["availability"]["known_at"]):
                    reasons.add("availability_inconsistent")
                current = predecessor
        if len(heads) == 1 and len(event_ids) == 1:
            selected = heads[0]
    for candidate in candidates:
        if candidate.get("status") != "OBSERVED":
            reasons.add("observation_unusable")
        if candidate.get("currency") != "USD" or candidate.get("units") != "USD/share":
            reasons.add("currency_or_unit_incompatible")
        amount = _rational(candidate.get("amount"))
        if amount is None:
            reasons.add("numeric_invalid")
        elif amount <= 0:
            reasons.add("numeric_domain_invalid")
    if selected is not None:
        record["selected_revision"] = {
            key: json_evidence(selected.get(key)) for key in ("event_id", "revision_id")
        }
        observations["dividend"] = json_evidence(selected.get("status", "MISSING"))
        numbers["dividend"] = _rational(selected.get("amount"))
    record["observations"] = observations
    if reasons:
        record["reasons"] = [reason for reason in REASONS if reason in reasons]
        return record
    pp, pe, ap, ae = (numbers[key] for key in ANCHORS)
    dividend = numbers["dividend"]
    reference, supplied = (pe + dividend) / pp - 1, ae / ap - 1
    binary_reference = (float(pe) + float(dividend)) / float(pp) - 1
    binary_supplied = float(ae) / float(ap) - 1
    diagnostic = {"reference": binary_reference, "supplied": binary_supplied, "delta": binary_supplied - binary_reference}
    record.update(_classify(reference, supplied, diagnostic))
    record["binary64_diagnostic"] = json_evidence(diagnostic)
    record["economic_acceptance"] = record["comparison_status"] == "MATCHED"
    return record


def retain_comparisons(request, prices, append_item: Callable[[dict], object]) -> list[dict]:
    """Validate scope, then retain each item before evaluating its successor."""
    _validate_request(request)
    conflicting_items = _overlapping_identity_conflicts(request.windows)
    items = []
    for window in request.windows:
        item = _compare_window(window, prices, conflicting_items)
        append_item(item)
        items.append(item)
    return items


def require_distinct_outputs(report_path, attempt_log_path):
    """Keep the append-only log and replaceable report on separate file identities."""
    report, log = Path(report_path), Path(attempt_log_path)
    if report.resolve() == log.resolve() or (
        report.exists() and log.exists() and report.samefile(log)
    ):
        raise RuntimeError("comparison attempt cannot begin: report and log paths must be distinct")


def write_diagnostic_report(report_path, writer, items, attempt_id):
    """Prepare beside the destination; preserve prior bytes until replace succeeds."""
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=report_path.parent, prefix=".dividend-", suffix=".md", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        writer(temporary)
        base_content = temporary.read_text(encoding="utf-8").replace(
            "Event-level reconciliation was not performed because no independent event table was supplied.",
            "M3-08 event_table metadata is absent. The explicit synthetic dividend request is diagnosed below.",
        )
        compared = sum(item["compared"] for item in items)
        accepted = bool(items) and all(item["economic_acceptance"] for item in items)
        content = (
            "\n## Synthetic dividend comparison\n\n"
            f"Attempt `{attempt_id}`: diagnostic computation completed; terminal execution status is recorded in the attempt log after report replacement.\n\n"
            f"Coverage: {compared}/{len(items)}. All requested windows matched: {str(accepted).lower()}. "
            "Economic acceptance is limited to each matched synthetic window. Supplied-series metrics retain their existing diagnostic scope.\n\n"
            "| Item | Comparison status | Coverage | Reasons |\n| --- | --- | --- | --- |\n"
        )
        for item in items:
            content += f"| {item['item_id']} | {item['comparison_status']} | {item['compared']}/1 | {', '.join(item['reasons'])} |\n"
        content += "\nExact evidence, scope, cutoff, revisions and typed observations:\n\n```json\n"
        payload = [{**item, "attempt_id": attempt_id} for item in items]
        content += json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n```\n"
        temporary.write_text(base_content + content, encoding="utf-8")
        temporary.replace(report_path)
    except (Exception, KeyboardInterrupt, SystemExit):
        try:
            temporary.unlink(missing_ok=True)
        except (Exception, KeyboardInterrupt, SystemExit):
            pass
        raise
    else:
        temporary.unlink(missing_ok=True)
