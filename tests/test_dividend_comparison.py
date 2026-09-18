"""Independent literal oracles for the accepted synthetic dividend comparison."""

from copy import deepcopy
from dataclasses import asdict, replace
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal
import pytest

import research.dividend_comparison as comparison
import research.demo_v0 as demo_v0
import research.synthetic_multifactor_backtest_demo as multifactor


P = "2026-04-01"
E = "2026-04-02"
EARLY = "2026-03-30T12:00:00Z"
C = "2026-04-02T21:00:01Z"
LATER = "2026-04-03T12:00:00Z"


def availability(when=EARLY):
    return dict.fromkeys(comparison.AVAILABILITY_FIELDS, when)


def fixture(asset="T000", security="SYNTH:ORD_A", listing="SYNTH:LIST_A", event_id="SYNTH:DIV_A_01"):
    identity = dict(security_id=security, listing_id=listing)
    evidence = {
        "vintage_id": "synthetic_fixture_r1", "provenance": "independent_literal_fixture",
        "as_of_cutoff": C,
        "raw_field": dict(field_id="raw_close", basis="raw", share_basis="unchanged_ordinary_share", currency="USD", units="USD/share", provenance="independent_raw_literals", availability=availability()),
        "adjusted_field": dict(field_id="supplied_total_return", basis="gross_total_return", currency="USD", units="index_points", provenance="supplied_level_literals", adjustment_set_id="synthetic_gross_v1", version="r1", scale_id="common_scale", availability=availability()),
        "policy": dict(entitlement="pre_ex_holder", dividend="gross", withholding="zero", reinvestment="ex_close", availability=availability()),
        "identity": dict(mappings=[dict(asset=asset, **identity)], effective_from=EARLY, effective_to=None, effective_to_state="OPEN_IN_VINTAGE", availability=availability()),
        "source_times": dict(rows=[dict(label=P, close=P+"T21:00:00Z"), dict(label=E, close=E+"T21:00:00Z")], availability=availability()),
        "coverage": {role: dict(verified=True, complete=True, **{"from": EARLY, "through": C}) for role in comparison.ROLES},
        "events": [dict(event_id=event_id, revision_id="r1", supersedes=None, event_type="ordinary_cash_dividend", ex_date=E, amount=2, status="OBSERVED", currency="USD", units="USD/share", provenance="independent_dividend_literal", availability=availability(), **identity)],
    }
    for role, value in zip(comparison.ANCHORS, (100, 98, 100, 100), strict=True):
        label = P if role.endswith("prior") else E
        evidence[role] = dict(value=value, status="OBSERVED", label=label, field_id="raw_close" if role.startswith("raw") else "supplied_total_return", provenance="literal_"+role, availability=availability(label+"T21:00:01Z"), **identity)
    evidence["coverage"]["availability"] = availability()
    prices = pd.DataFrame({asset: [100.0, 100.0]}, index=pd.DatetimeIndex([P, E]))
    window = comparison.DividendWindow(asset, security, listing, asset, P, E, C, evidence)
    return window, prices


def seal(window):
    if window.evidence:
        window.evidence["sha256"] = comparison.evidence_sha256(window.evidence)
    return window


def evaluate(window, prices):
    retained = []
    result = comparison.retain_comparisons(comparison.DividendComparisonRequest((seal(window),)), prices, retained.append)
    assert result == retained
    return result[0]


def fraction(value):
    return Fraction(int(value["numerator"]), int(value["denominator"]))


def set_values(window, prices, pp=100, pe=98, dividend=2, ap=100, ae=100):
    for role, value in zip(comparison.ANCHORS, (pp, pe, ap, ae), strict=True):
        window.evidence[role]["value"] = value
    window.evidence["events"][0]["amount"] = dividend
    prices.loc[:, window.asset] = [ap, ae]


@pytest.mark.parametrize("case, values, expected, delta, status", [
    ("D01", {}, Fraction(0), Fraction(0), "MATCHED"),
    ("D02", dict(pe=101, ae=103), Fraction(3, 100), Fraction(0), "MATCHED"),
    ("D03", dict(pe=101, ap=50, ae=51.5), Fraction(3, 100), Fraction(0), "MATCHED"),
    ("D06", dict(dividend=3), Fraction(1, 100), Fraction(-1, 100), "MISMATCHED"),
    ("D07", dict(pe=97), Fraction(-1, 100), Fraction(1, 100), "MISMATCHED"),
    ("D08", dict(ae=98), Fraction(0), Fraction(-1, 50), "MISMATCHED"),
    ("D09", dict(ae=102), Fraction(0), Fraction(1, 50), "MISMATCHED"),
    ("D41", dict(pp=1, pe=1e16, dividend=1, ap=1, ae=1e16), Fraction(10**16), Fraction(-1), "MISMATCHED"),
    ("D42", dict(ae=float.fromhex("0x1.9000000000dbfp+6")), Fraction(0), Fraction(3519, 7036874417766400), "MATCHED"),
    ("D43", dict(ae=float.fromhex("0x1.90000000036f9p+6")), Fraction(0), Fraction(14073, 7036874417766400), "MISMATCHED"),
    ("D45", dict(ae=float.fromhex("0x1.9000000001b7ep+6")), Fraction(0), Fraction(3519, 3518437208883200), "MISMATCHED"),
    ("D46", dict(pp=2.0**-1074, pe=1, dividend=1, ap=1, ae=1), Fraction(2**1075-1), Fraction(1-2**1075), "MISMATCHED"),
], ids=lambda value: value if isinstance(value, str) else None)
def test_exact_matrix(case, values, expected, delta, status):
    window, prices = fixture()
    set_values(window, prices, **values)
    original, panel = deepcopy(window), prices.copy(deep=True)
    result = evaluate(window, prices)
    assert result["comparison_status"] == status
    assert result["compared"] == result["requested"] == 1
    assert result["reasons"] == ["within_tolerance" if status == "MATCHED" else "return_difference"]
    assert fraction(result["reference"]) == expected
    assert fraction(result["supplied"]) == expected + delta
    assert fraction(result["delta"]) == delta
    if case == "D41":
        assert fraction(result["binary64_diagnostic"]["delta"]["ratio"]) == 0
    if case == "D46":
        assert result["binary64_diagnostic"]["reference"] == {"type": "nonfinite", "value": "+inf"}
    assert_frame_equal(prices, panel, check_exact=True)
    assert seal(original) == window
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("case, supplied, status", [
    ("D04", Fraction(5, 10**13), "MATCHED"),
    ("D05", Fraction(2, 10**12), "MISMATCHED"),
    ("D44", Fraction(1, 10**12), "MATCHED"),
])
def test_injected_exact_return_boundary(case, supplied, status):
    result = comparison._classify(Fraction(0), supplied, {})
    assert result["comparison_status"] == status
    assert fraction(result["delta"]) == supplied
    assert result["compared"] == 1


@pytest.mark.parametrize("case, diagnostic, reason", [
    ("D32", {"delta": float("inf")}, "arithmetic_nonfinite"),
    ("D47", {"delta": 1e-12}, "comparison_precision_insufficient"),
])
def test_missing_classification_is_insufficient(case, diagnostic, reason):
    # Conditional contract alternatives: production always calculates the rational.
    if case == "D47":
        # The hypothetical bound crosses the exact tolerance and supplies no
        # rational verdict; production has no public bound/precision switch.
        center, error = Fraction(1, 10**12), Fraction(1, 10**13)
        assert center - error <= Fraction(1, 10**12) < center + error
    result = comparison._classify(None, None, diagnostic)
    assert result == dict(comparison_status="INSUFFICIENT_EVIDENCE", compared=0, reasons=[reason])


def mutate(window, case):
    e = window.evidence
    if case == "D10":
        e["raw_field"]["basis"] = "UNKNOWN"
    elif case == "D11":
        e["adjusted_field"]["basis"] = "split_only"
    elif case == "D12":
        e["events"][0]["units"] = "cents/lot"
    elif case == "D13":
        del e["raw_prior"]["value"]
        e["raw_prior"]["status"] = "PROVIDER_GAP"
    elif case == "D14":
        e["raw_ex"]["label"] = "2026-04-03"
    elif case == "D15":
        e["identity"]["mappings"] = [{"ticker": "T000"}]
    elif case == "D17":
        e["events"][0]["availability"] = availability(LATER)
    elif case == "D19":
        e["events"][0]["availability"]["provider_available_at"] = C
    elif case == "D20":
        e["events"][0]["availability"]["known_at"] = "2026-03-30"
    elif case == "D21":
        e["events"].append(deepcopy(e["events"][0]))
    elif case == "D22":
        e["events"][0]["supersedes"] = "missing"
    elif case == "D24":
        e["events"].append(dict(deepcopy(e["events"][0]), event_id="SYNTH:DIV_A_02"))
    elif case == "D25":
        del e["events"]
    elif case == "D26":
        e["events"] = []
    elif case == "D28":
        e["events"][0]["event_type"] = "split"
    elif case == "D29":
        e["events"].append(dict(deepcopy(e["events"][0]), event_id="SYNTH:TERMINAL", event_type="terminal"))
    elif case == "D30":
        e["events"][0]["amount"] = True
    elif case == "D31":
        e["events"][0]["amount"] = 0
    elif case == "D33":
        e["raw_ex"]["status"] = "HALTED"
    elif case == "D34":
        e["coverage"]["events"]["through"] = EARLY
    elif case == "D35":
        del e["policy"]["entitlement"]
    elif case == "D40":
        del e["raw_field"]["provenance"]
    else:
        raise AssertionError(case)


@pytest.mark.parametrize("case, reason", [
    ("D10", "basis_unknown"), ("D11", "basis_incompatible"),
    ("D12", "currency_or_unit_incompatible"), ("D13", "anchor_missing"),
    ("D14", "window_invalid"), ("D15", "identity_unresolved"),
    ("D17", "event_unavailable_at_cutoff"), ("D19", "availability_inconsistent"),
    ("D20", "availability_unproven"), ("D21", "duplicate_event_revision"),
    ("D22", "revision_lineage_unresolved"), ("D24", "multiple_events_in_window"),
    ("D25", "event_evidence_absent"), ("D26", "event_evidence_empty"),
    ("D28", "event_type_unsupported"), ("D29", "event_type_unsupported"),
    ("D30", "numeric_invalid"), ("D31", "numeric_domain_invalid"),
    ("D33", "observation_unusable"), ("D34", "coverage_unproven"),
    ("D35", "policy_unresolved"), ("D40", "evidence_identity_unproven"),
])
def test_insufficient_matrix(case, reason):
    window, prices = fixture()
    mutate(window, case)
    result = evaluate(window, prices)
    assert result["comparison_status"] == "INSUFFICIENT_EVIDENCE"
    assert result["compared"] == 0 and result["requested"] == 1
    assert reason in result["reasons"]
    assert "delta" not in result and result["economic_acceptance"] is False
    assert result["evidence"] == comparison.json_evidence(window.evidence)


@pytest.mark.parametrize("payload", [True, False, np.bool_(True), 1j, "2", None, float("nan"), float("inf"), float("-inf"), 2**53+1, np.int64(2**53+1), np.uint64(2**53+1), Decimal("0.1"), Fraction(1, 10), Decimal("NaN"), Decimal("Infinity")])
@pytest.mark.parametrize("role", [*comparison.ANCHORS, "dividend"])
def test_admission_before_conversion_D30(payload, role):
    window, prices = fixture()
    set_values(window, prices, pp=2, pe=2, ap=1, ae=2**52+1)
    if role == "dividend":
        window.evidence["events"][0]["amount"] = payload
    else:
        window.evidence[role]["value"] = payload
    result = evaluate(window, prices)
    assert result["comparison_status"] == "INSUFFICIENT_EVIDENCE"
    assert "numeric_invalid" in result["reasons"]
    assert result["compared"] == 0 and "delta" not in result
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("payload", [2, 2**53, np.int64(2), np.uint64(2**53), Decimal("2"), Fraction(2), np.float32(2), np.float64(2)])
def test_representable_numeric_controls(payload):
    window, prices = fixture()
    set_values(window, prices, pp=2, pe=2, dividend=payload, ap=1, ae=2 if int(payload) == 2 else 2**52+1)
    result = evaluate(window, prices)
    assert result["comparison_status"] == "MATCHED"
    assert fraction(result["reference"]) == Fraction(int(payload), 2)


@pytest.mark.parametrize("role", [*comparison.ANCHORS, "dividend"])
@pytest.mark.parametrize("value", [0, -1])
def test_nonpositive_domain_D31(role, value):
    window, prices = fixture()
    if role == "dividend":
        window.evidence["events"][0]["amount"] = value
    else:
        window.evidence[role]["value"] = value
    assert "numeric_domain_invalid" in evaluate(window, prices)["reasons"]


def later_window(window):
    new = deepcopy(window)
    new = replace(new, cutoff=LATER)
    new.evidence["as_of_cutoff"] = LATER
    new.evidence["vintage_id"] = "synthetic_fixture_r2"
    for role in comparison.ROLES:
        new.evidence["coverage"][role]["through"] = LATER
    return new


def test_revision_history_D16_D18_D39():
    window, prices = fixture()
    window.evidence["events"].append(dict(deepcopy(window.evidence["events"][0]), revision_id="r2", supersedes="r1", amount=3, availability=availability(LATER)))
    old = evaluate(window, prices)
    new = evaluate(later_window(window), prices)
    assert old["comparison_status"] == "MATCHED" and fraction(old["reference"]) == 0
    assert old["selected_revision"]["revision_id"] == "r1"
    assert old["excluded_revisions"][0]["revision_id"] == "r2"
    assert new["comparison_status"] == "MISMATCHED"
    assert new["selected_revision"]["revision_id"] == "r2"
    assert fraction(new["delta"]) == Fraction(-1, 100)
    assert old["evidence_sha256"] != new["evidence_sha256"]


@pytest.mark.parametrize("kind", ["heads", "cycle", "missing", "identity", "latest_only"])
def test_revision_defects_D22(kind):
    window, prices = fixture()
    event = window.evidence["events"][0]
    if kind == "heads":
        window.evidence["events"].append(dict(deepcopy(event), revision_id="r2"))
    elif kind == "cycle":
        event["supersedes"] = "r2"
        window.evidence["events"].append(dict(deepcopy(event), revision_id="r2", supersedes="r1"))
    elif kind in ("missing", "latest_only"):
        event["supersedes"] = "unretained_predecessor"
    else:
        window.evidence["events"].append(dict(deepcopy(event), revision_id="r2", supersedes="r1", listing_id="SYNTH:OTHER"))
    assert "revision_lineage_unresolved" in evaluate(window, prices)["reasons"]


@pytest.mark.parametrize("partial", [False, True], ids=["D23", "D36"])
def test_two_windows_same_date(partial):
    first, prices = fixture()
    second, panel = fixture("T001", "SYNTH:ORD_B", "SYNTH:LIST_B", "SYNTH:DIV_B_01")
    if partial:
        second.evidence["events"][0]["event_type"] = "spin_off"
    records = []
    items = comparison.retain_comparisons(comparison.DividendComparisonRequest((seal(first), seal(second))), pd.concat([prices, panel], axis=1), records.append)
    assert items == records
    assert [item["comparison_status"] for item in items] == ["MATCHED", "INSUFFICIENT_EVIDENCE" if partial else "MATCHED"]
    assert sum(item["compared"] for item in items) == (1 if partial else 2)
    assert sum(item["requested"] for item in items) == 2


@pytest.mark.parametrize("state", ["PROVIDER_GAP", "STALE", "HALTED", "SUSPENDED", "DELISTED", "INVALID"])
def test_typed_status_D33(state):
    window, prices = fixture()
    window.evidence["raw_ex"]["status"] = state
    result = evaluate(window, prices)
    assert result["observations"]["raw_ex"] == state
    assert result["reasons"] == ["observation_unusable"]


@pytest.mark.parametrize("role", comparison.ROLES)
def test_each_role_coverage_D34(role):
    window, prices = fixture()
    window.evidence["coverage"][role]["complete"] = False
    assert evaluate(window, prices)["reasons"] == ["coverage_unproven"]


@pytest.mark.parametrize("role", [*comparison.ANCHORS, "identity", "raw_field", "adjusted_field", "policy", "source_times", "event"])
@pytest.mark.parametrize("field", comparison.AVAILABILITY_FIELDS)
def test_each_availability_field_D19_D20(role, field):
    window, prices = fixture()
    record = window.evidence["events"][0] if role == "event" else window.evidence[role]
    record["availability"][field] = None
    assert "availability_unproven" in evaluate(window, prices)["reasons"]


def test_ordered_multiple_reasons_and_hash_tampering():
    window, prices = fixture()
    for case in ["D15", "D21", "D10", "D14", "D19", "D33", "D30"]:
        mutate(window, case)
    seal(window)
    window.evidence["sha256"] = "bad"
    item = comparison.retain_comparisons(comparison.DividendComparisonRequest((window,)), prices, lambda item: None)[0]
    assert item["reasons"] == ["evidence_identity_unproven", "identity_unresolved", "duplicate_event_revision", "revision_lineage_unresolved", "basis_unknown", "window_invalid", "availability_inconsistent", "observation_unusable", "numeric_invalid"]


@pytest.fixture(params=[demo_v0, multifactor], ids=["demo_v0", "m3_01"])
def consumer(request, monkeypatch, tmp_path):
    module = request.param
    dates = pd.bdate_range("2026-03-26", "2026-04-06")
    prices = pd.DataFrame({"T000": 100.0, "T001": 100.0}, index=dates)
    frozen = deepcopy(asdict(module.DEMO_V0_CONFIG if module is demo_v0 else module.FROZEN_CONFIG))
    overrides = dict(periods=len(dates), asset_count=2, top_n=2, start_date=str(dates[0].date()), rebalance_frequency="D", transaction_cost_bps=10, slippage_bps=5)
    if module is demo_v0:
        config = replace(module.DEMO_V0_CONFIG, lookback_periods=2, skip_periods=0, **overrides)
        run = module.run_demo_v0
    else:
        config = replace(module.FROZEN_CONFIG, **overrides)
        run = module.run_synthetic_multifactor_backtest_demo
        factors = {name: pd.DataFrame({"T000": 2.0, "T001": 1.0}, index=dates) for name in module.FACTOR_NAMES}
        monkeypatch.setattr(module, "generate_synthetic_factor_panels", lambda config: factors)
    monkeypatch.setattr(module, "generate_synthetic_prices", lambda config: prices)
    captured = []
    original_backtest = module.run_long_only_backtest

    def capture(*args, **kwargs):
        captured.append((deepcopy(args), deepcopy(kwargs)))
        return original_backtest(*args, **kwargs)

    monkeypatch.setattr(module, "run_long_only_backtest", capture)
    yield module, run, prices, captured, dict(config=config, report_path=tmp_path / "report.md", attempt_log_path=tmp_path / "attempts.jsonl")
    assert asdict(module.DEMO_V0_CONFIG if module is demo_v0 else module.FROZEN_CONFIG) == frozen


def backtest(result):
    return result.backtest_result if hasattr(result, "backtest_result") else result


def request_for(*windows):
    return comparison.DividendComparisonRequest(tuple(seal(window) for window in windows))


def records(consumer):
    module, _, _, _, kwargs = consumer
    return module.load_attempt_records(kwargs["attempt_log_path"])


def test_both_consumers_accounting_inputs_default_D27(consumer):
    module, run, prices, captured, kwargs = consumer
    window, _ = fixture()
    window = seal(window)
    snapshot = deepcopy(window)
    original_prices = prices.copy(deep=True)
    baseline = backtest(run(**kwargs))
    original_report = kwargs["report_path"].read_bytes()
    prefix = kwargs["attempt_log_path"].read_bytes()
    events = pd.DataFrame({"amount": [2, 3]}, index=pd.DatetimeIndex([E, E]))
    original_events = events.copy(deep=True)
    result = backtest(run(**kwargs, event_table=events, comparison_request=request_for(window)))
    assert_frame_equal(prices, original_prices, check_exact=True)
    assert_frame_equal(events, original_events, check_exact=True)
    assert window == snapshot
    for field in ("holdings", "signed_trade_weights", "trade_weights"):
        assert_frame_equal(getattr(result, field), getattr(baseline, field), check_exact=True)
    for field in ("gross_returns", "returns", "turnover", "transaction_costs", "slippage_costs", "volume_aware_slippage_costs", "total_trading_costs", "equity_curve", "benchmark_returns", "benchmark_equity_curve"):
        assert_series_equal(getattr(result, field), getattr(baseline, field), check_exact=True)
    assert result.timing_ledger == baseline.timing_ledger
    assert result.timing_metadata == baseline.timing_metadata
    for (args, call) in captured:
        assert_frame_equal(args[0], original_prices, check_exact=True)
        assert_frame_equal(args[1], captured[0][0][1], check_exact=True)
    assert kwargs["attempt_log_path"].read_bytes().startswith(prefix)
    rows = records(consumer)
    assert [row.get("status", "item") for row in rows] == ["started", "success", "started", "item", "success"]
    assert [row["attempt_id"] for row in rows] == [1, 1, 2, 2, 2]
    assert rows[3]["record_type"] == "dividend_comparison_item"
    assert "Attempt `2`" in kwargs["report_path"].read_text()
    assert "MATCHED" in kwargs["report_path"].read_text()
    assert "dividend_comparison_item" not in original_report.decode()
    run(**kwargs)
    assert kwargs["report_path"].read_bytes() == original_report


@pytest.mark.parametrize("kind", ["match", "mismatch", "insufficient", "partial", "mixed", "absent", "empty"])
def test_runner_completion_is_separate_from_economics(consumer, kind):
    _, run, _, _, kwargs = consumer
    window, _ = fixture()
    windows = [window]
    if kind in ("mismatch", "mixed"):
        window.evidence["events"][0]["amount"] = 3
    if kind == "insufficient":
        window.evidence["raw_field"]["basis"] = "UNKNOWN"
    if kind == "absent":
        windows = [replace(window, evidence=None)]
    if kind == "empty":
        windows = [replace(window, evidence={})]
    if kind in ("partial", "mixed"):
        second, _ = fixture("T001", "SYNTH:ORD_B", "SYNTH:LIST_B", "SYNTH:DIV_B_01")
        second.evidence["events"][0]["event_type"] = "split"
        windows.append(second)
    run(**kwargs, comparison_request=request_for(*windows))
    rows = records(consumer)
    assert rows[0]["status"] == "started" and rows[-1]["status"] == "success"
    items = rows[1:-1]
    assert len(items) == len(windows)
    assert all(item["attempt_id"] == rows[0]["attempt_id"] for item in items)
    assert all(item["economic_acceptance"] for item in items) == (kind == "match")
    report = kwargs["report_path"].read_text()
    assert "terminal execution status" in report
    assert f"All requested windows matched: {'true' if kind == 'match' else 'false'}" in report
    for item in items:
        assert item["comparison_status"] in report


def test_negative_then_match_history(consumer):
    _, run, _, _, kwargs = consumer
    window, _ = fixture()
    window.evidence["events"][0]["amount"] = 3
    run(**kwargs, comparison_request=request_for(window))
    prefix = kwargs["attempt_log_path"].read_bytes()
    window.evidence["events"][0]["amount"] = 2
    run(**kwargs, comparison_request=request_for(window))
    assert kwargs["attempt_log_path"].read_bytes().startswith(prefix)
    items = [row for row in records(consumer) if row.get("record_type") == "dividend_comparison_item"]
    assert [row["comparison_status"] for row in items] == ["MISMATCHED", "MATCHED"]
    assert [row["attempt_id"] for row in items] == [1, 2]
    assert items[0]["evidence_sha256"] != items[1]["evidence_sha256"]


@pytest.mark.parametrize("kind", ["container", "empty", "window", "cutoff", "scope", "duplicate", "convention", "evidence_container"])
def test_malformed_request_preserves_report(consumer, kind):
    _, run, _, _, kwargs = consumer
    run(**kwargs)
    previous, prefix = kwargs["report_path"].read_bytes(), kwargs["attempt_log_path"].read_bytes()
    window, _ = fixture()
    request = request_for(window)
    if kind == "container":
        request = {}
    elif kind == "empty":
        request = replace(request, windows=())
    elif kind == "window":
        request = replace(request, windows=("invalid",))
    elif kind == "cutoff":
        request = request_for(replace(window, cutoff="2026-04-02"))
    elif kind == "scope":
        request = request_for(replace(window, prior="2026-04", security_id=""))
    elif kind == "duplicate":
        request = request_for(window, window)
    elif kind == "convention":
        request = replace(request, convention="unknown")
    else:
        request = replace(request, windows=(replace(window, evidence=[]),))
    with pytest.raises((TypeError, ValueError)):
        run(**kwargs, comparison_request=request)
    assert kwargs["report_path"].read_bytes() == previous
    assert kwargs["attempt_log_path"].read_bytes().startswith(prefix)
    assert records(consumer)[-1]["status"] == "failure"
    assert not any(row.get("record_type") for row in records(consumer))


@pytest.mark.parametrize("kind", ["zero_overlay", "empty_overlay", "off_source", "missing", "malformed"])
def test_guard_precedence_D37_D38(consumer, kind):
    _, run, _, _, kwargs = consumer
    run(**kwargs)
    previous, prefix = kwargs["report_path"].read_bytes(), kwargs["attempt_log_path"].read_bytes()
    if kind.endswith("overlay"):
        extra = dict(cash_dividends=0 if kind == "zero_overlay" else {})
        error, match = ValueError, "cash_dividends overlay"
    else:
        index = {"off_source": pd.DatetimeIndex(["2026-04-02 12:00"]), "missing": pd.DatetimeIndex([pd.NaT]), "malformed": pd.Index([E])}[kind]
        extra = dict(event_table=pd.DataFrame({"amount": [2]}, index=index))
        error = TypeError if kind == "malformed" else ValueError
        match = {"off_source": "event date absent", "missing": "missing event dates", "malformed": "DatetimeIndex"}[kind]
    with pytest.raises(error, match=match):
        run(**kwargs, comparison_request={}, **extra)
    assert kwargs["report_path"].read_bytes() == previous
    assert kwargs["attempt_log_path"].read_bytes().startswith(prefix)
    assert records(consumer)[-1]["status"] == "failure"


@pytest.mark.parametrize("boundary", ["start", "pipeline", "compare_second", "append_first", "append_second", "prepare", "replace", "success", "after_replace"])
@pytest.mark.parametrize("error_class", [OSError, KeyboardInterrupt, SystemExit])
def test_fault_boundaries(consumer, monkeypatch, boundary, error_class):
    module, run, _, _, kwargs = consumer
    run(**kwargs)
    previous, prefix = kwargs["report_path"].read_bytes(), kwargs["attempt_log_path"].read_bytes()
    first, _ = fixture()
    second, _ = fixture("T001", "SYNTH:ORD_B", "SYNTH:LIST_B", "SYNTH:DIV_B_01")
    fault = error_class("injected_"+boundary)

    def fail(*args, **kwargs):
        raise fault

    original_append = module.append_attempt_record
    item_count = 0

    def append(path, record, **kwargs):
        nonlocal item_count
        if record.get("record_type") == "dividend_comparison_item":
            item_count += 1
        if ((boundary == "start" and record.get("status") == "started")
                or (boundary == "success" and record.get("status") == "success")
                or (boundary == "append_first" and item_count == 1 and record.get("record_type"))
                or (boundary == "append_second" and item_count == 2 and record.get("record_type"))):
            raise fault
        return original_append(path, record, **kwargs)

    monkeypatch.setattr(module, "append_attempt_record", append)
    if boundary == "pipeline":
        monkeypatch.setattr(module, "_run_demo_v0_pipeline" if module is demo_v0 else "_run_pipeline", fail)
    elif boundary == "compare_second":
        original = comparison._compare_window

        def compare(window, prices, *source):
            if window.item_id == "T001":
                raise fault
            return original(window, prices, *source)

        monkeypatch.setattr(comparison, "_compare_window", compare)
    elif boundary == "prepare":
        def prepare(**kw):
            kw["report_path"].write_text("partial temporary report")
            raise fault
        monkeypatch.setattr(module, "write_comparison_report", prepare)
    elif boundary in ("replace", "after_replace"):
        original_replace = Path.replace

        def replace_path(source, target):
            assert source.parent == target.parent
            if boundary == "after_replace":
                original_replace(source, target)
            raise fault

        monkeypatch.setattr(Path, "replace", replace_path)
    expected = RuntimeError if boundary == "start" and error_class is OSError else error_class
    with pytest.raises(expected) as caught:
        run(**kwargs, comparison_request=request_for(first, second))
    if expected is error_class:
        assert caught.value is fault
    assert kwargs["attempt_log_path"].read_bytes().startswith(prefix)
    rows = records(consumer)[2:]
    if boundary == "start":
        assert rows == []
    else:
        assert rows[0]["status"] == "started"
        assert rows[-1]["status"] == ("failure" if error_class is OSError else "interrupted")
        assert not any(row.get("status") == "success" for row in rows)
        items = [row for row in rows if row.get("record_type")]
        count = 0 if boundary in ("pipeline", "append_first") else 1 if boundary in ("compare_second", "append_second") else 2
        assert len(items) == count
        assert all(row["attempt_id"] == 2 for row in rows)
    if boundary in ("success", "after_replace"):
        assert kwargs["report_path"].read_bytes() != previous
        assert "Attempt `2`" in kwargs["report_path"].read_text()
    else:
        assert kwargs["report_path"].read_bytes() == previous
    assert list(kwargs["report_path"].parent.glob(".dividend-*")) == []


def test_terminal_append_and_failure_append_both_unavailable(consumer, monkeypatch):
    module, run, _, _, kwargs = consumer
    window, _ = fixture()
    original = module.append_attempt_record

    def append(path, record, **kw):
        if record.get("status") in ("success", "failure"):
            raise OSError("terminal log unavailable")
        return original(path, record, **kw)

    monkeypatch.setattr(module, "append_attempt_record", append)
    with pytest.raises(OSError, match="terminal log unavailable"):
        run(**kwargs, comparison_request=request_for(window))
    rows = records(consumer)
    assert [row.get("status", "item") for row in rows] == ["started", "item"]
    assert kwargs["report_path"].exists()


@pytest.mark.parametrize("role", comparison.ANCHORS)
def test_each_missing_anchor_D13(role):
    window, prices = fixture()
    del window.evidence[role]
    result = evaluate(window, prices)
    assert "anchor_missing" in result["reasons"]
    assert result["observations"][role] == "MISSING"
    assert result["compared"] == 0


@pytest.mark.parametrize("kind", ["skipped", "off_source", "mapping_duplicate", "mapping_alias", "cutoff_at_close", "ex_role"])
def test_window_boundary_D14(kind):
    window, prices = fixture()
    if kind == "skipped":
        prices.loc[pd.Timestamp(P+" 12:00")] = 100
        prices = prices.sort_index()
    elif kind == "off_source":
        prices = prices.iloc[1:]
    elif kind == "mapping_duplicate":
        window.evidence["source_times"]["rows"].append(deepcopy(window.evidence["source_times"]["rows"][0]))
    elif kind == "mapping_alias":
        window.evidence["source_times"]["rows"].append(dict(label="2026-03-31", close=P+"T21:00:00Z"))
    elif kind == "cutoff_at_close":
        window = replace(window, cutoff=E+"T21:00:00Z")
    else:
        window.evidence["events"][0]["ex_date"] = P
    assert "window_invalid" in evaluate(window, prices)["reasons"]


def test_declared_source_adjacency_both_runners(consumer):
    _, run, prices, _, kwargs = consumer
    window, _ = fixture()
    source = prices.index.union(pd.DatetimeIndex([P+" 12:00"]))
    run(**kwargs)
    previous = kwargs["report_path"].read_bytes()
    with pytest.raises(ValueError, match="dropped 1 observed source rows"):
        run(**kwargs, observed_index=source, comparison_request=request_for(window))
    assert records(consumer)[-1]["status"] == "failure"
    assert kwargs["report_path"].read_bytes() == previous


@pytest.mark.parametrize("kind", ["finite_equal_ex", "finite_before_ex", "missing_end", "untyped_end", "start_late", "two_mappings", "changed_anchor"])
def test_identity_episode_boundary_D15(kind):
    window, prices = fixture()
    identity = window.evidence["identity"]
    if kind.startswith("finite"):
        identity.update(effective_to_state="FINITE", effective_to=(E if kind == "finite_equal_ex" else P)+"T21:00:00Z")
    elif kind == "missing_end":
        del identity["effective_to"]
    elif kind == "untyped_end":
        del identity["effective_to_state"]
    elif kind == "start_late":
        identity["effective_from"] = E+"T20:00:00Z"
    elif kind == "two_mappings":
        identity["mappings"].append(dict(identity["mappings"][0], asset="T001"))
    else:
        window.evidence["raw_ex"]["security_id"] = "SYNTH:REUSED"
    assert "identity_unresolved" in evaluate(window, prices)["reasons"]


def test_inclusive_availability_and_exclusive_identity_end():
    window, prices = fixture()
    window.evidence["identity"].update(effective_to_state="FINITE", effective_to=C)
    window.evidence["events"][0]["availability"] = availability(C)
    assert evaluate(window, prices)["comparison_status"] == "MATCHED"
    window.evidence["events"][0]["availability"] = availability("2026-04-02T21:00:01.000000001Z")
    assert "event_unavailable_at_cutoff" in evaluate(window, prices)["reasons"]


@pytest.mark.parametrize("kind", ["date_only", "later_anchor", "early_anchor", "late_parent", "vintage_cutoff", "coverage_availability"])
def test_temporal_boundaries_D19_D20_D34(kind):
    window, prices = fixture()
    if kind == "date_only":
        window.evidence["identity"]["availability"]["known_at"] = P
        reason = "availability_unproven"
    elif kind == "later_anchor":
        window.evidence["adjusted_ex"]["availability"] = availability(LATER)
        reason = "availability_unproven"
    elif kind == "early_anchor":
        window.evidence["raw_ex"]["availability"] = availability(E+"T21:00:00Z")
        reason = "availability_inconsistent"
    elif kind == "late_parent":
        window.evidence["raw_field"]["availability"] = availability(C)
        reason = "availability_inconsistent"
    elif kind == "vintage_cutoff":
        window.evidence["as_of_cutoff"] = E+"T21:00:00Z"
        reason = "coverage_unproven"
    else:
        del window.evidence["coverage"]["availability"]
        reason = "availability_unproven"
    assert reason in evaluate(window, prices)["reasons"]


@pytest.mark.parametrize("basis", ["raw", "split_only", "net_dividend", "price_return"])
def test_incompatible_basis_equal_ratio_D11(basis):
    window, prices = fixture()
    window.evidence["adjusted_field"]["basis"] = basis
    assert evaluate(window, prices)["reasons"] == ["basis_incompatible"]


@pytest.mark.parametrize("policy", ["entitlement", "dividend", "withholding", "reinvestment"])
def test_policy_absence_and_incompatibility_D11_D35(policy):
    window, prices = fixture()
    del window.evidence["policy"][policy]
    assert evaluate(window, prices)["reasons"] == ["policy_unresolved"]
    window.evidence["policy"][policy] = "other"
    assert evaluate(window, prices)["reasons"] == ["basis_incompatible"]


@pytest.mark.parametrize("event_type", ["split", "special_dividend", "stock_dividend", "spin_off", "terminal"])
def test_all_unsupported_families_D28_D29(event_type):
    window, prices = fixture()
    window.evidence["events"].append(dict(deepcopy(window.evidence["events"][0]), event_id="SYNTH:OTHER", event_type=event_type))
    result = evaluate(window, prices)
    assert "event_type_unsupported" in result["reasons"]
    assert len(result["evidence"]["events"]) == 2


@pytest.mark.parametrize("kind", ["missing_hash", "bad_hash", "panel_mismatch", "provenance_shared", "version_missing"])
def test_evidence_binding_D40(kind):
    window, prices = fixture()
    if kind == "panel_mismatch":
        prices.loc[pd.Timestamp(E), "T000"] = 101
    elif kind == "provenance_shared":
        window.evidence["raw_field"]["provenance"] = window.evidence["adjusted_field"]["provenance"]
    elif kind == "version_missing":
        del window.evidence["adjusted_field"]["version"]
    seal(window)
    if kind == "missing_hash":
        del window.evidence["sha256"]
    elif kind == "bad_hash":
        window.evidence["sha256"] = "0"*64
    item = comparison.retain_comparisons(comparison.DividendComparisonRequest((window,)), prices, lambda item: None)[0]
    assert item["reasons"] == ["evidence_identity_unproven"]


@pytest.mark.parametrize("kind", ["absent", "empty", "repeated"])
def test_default_metadata_has_no_comparison_records_D27(consumer, kind):
    _, run, _, _, kwargs = consumer
    events = None if kind == "absent" else pd.DataFrame({"gross_dividend": [] if kind == "empty" else [2, 2]}, index=pd.DatetimeIndex([] if kind == "empty" else [E, E]))
    run(**kwargs, event_table=events)
    assert [row["status"] for row in records(consumer)] == ["started", "success"]
    assert all("record_type" not in row and "comparison_status" not in row for row in records(consumer))
    report = kwargs["report_path"].read_text()
    assert "Synthetic dividend comparison" not in report
    assert ("no independent event table was supplied" if kind == "absent" else "Supplied event dates passed membership") in report


def test_later_revision_attempt_preserves_earlier_cutoff_history(consumer):
    _, run, _, _, kwargs = consumer
    window, _ = fixture()
    window.evidence["events"].append(dict(deepcopy(window.evidence["events"][0]), revision_id="r2", supersedes="r1", amount=3, availability=availability(LATER)))
    run(**kwargs, comparison_request=request_for(window))
    prefix = kwargs["attempt_log_path"].read_bytes()
    run(**kwargs, comparison_request=request_for(later_window(window)))
    assert kwargs["attempt_log_path"].read_bytes().startswith(prefix)
    items = [row for row in records(consumer) if row.get("record_type")]
    assert [item["selected_revision"]["revision_id"] for item in items] == ["r1", "r2"]
    assert [item["comparison_status"] for item in items] == ["MATCHED", "MISMATCHED"]


@pytest.mark.parametrize("secondary", [OSError, KeyboardInterrupt, SystemExit])
def test_original_exception_survives_terminal_logging_interruption(consumer, monkeypatch, secondary):
    module, run, _, _, kwargs = consumer
    run(**kwargs)
    previous = kwargs["report_path"].read_bytes()
    original_append = module.append_attempt_record
    original_error = ValueError("original pipeline failure")

    def pipeline(**kwargs):
        raise original_error

    def append(path, record, **kw):
        if record.get("status") == "failure":
            raise secondary("secondary logging failure")
        return original_append(path, record, **kw)

    monkeypatch.setattr(module, "append_attempt_record", append)
    monkeypatch.setattr(module, "_run_demo_v0_pipeline" if module is demo_v0 else "_run_pipeline", pipeline)
    window, _ = fixture()
    with pytest.raises(ValueError) as caught:
        run(**kwargs, comparison_request=request_for(window))
    assert caught.value is original_error
    assert kwargs["report_path"].read_bytes() == previous
    assert records(consumer)[-1]["status"] == "started"


def test_partial_item_append_retains_prefix_and_raises(consumer, monkeypatch):
    module, run, _, _, kwargs = consumer
    run(**kwargs)
    previous, prefix = kwargs["report_path"].read_bytes(), kwargs["attempt_log_path"].read_bytes()
    original = module.append_attempt_record

    def append(path, record, **kw):
        if record.get("record_type"):
            with path.open("a") as handle:
                handle.write('{"record_type":"dividend_comparison_item",')
            raise OSError("partial item write")
        return original(path, record, **kw)

    monkeypatch.setattr(module, "append_attempt_record", append)
    window, _ = fixture()
    with pytest.raises(OSError, match="partial item write"):
        run(**kwargs, comparison_request=request_for(window))
    assert kwargs["report_path"].read_bytes() == previous
    assert kwargs["attempt_log_path"].read_bytes().startswith(prefix)
    assert kwargs["attempt_log_path"].read_text().endswith('{"record_type":"dividend_comparison_item",')


@pytest.mark.parametrize("kind", ["temporary_creation", "full_report_write"])
def test_report_preparation_boundaries(consumer, monkeypatch, kind):
    module, run, _, _, kwargs = consumer
    run(**kwargs)
    previous = kwargs["report_path"].read_bytes()
    if kind == "temporary_creation":
        def create(**kw):
            raise OSError("temporary creation failed")
        monkeypatch.setattr(comparison.tempfile, "NamedTemporaryFile", create)
    else:
        original = Path.write_text
        def write(path, data, **kw):
            if "## Synthetic dividend comparison" in data:
                raise OSError("full report write failed")
            return original(path, data, **kw)
        monkeypatch.setattr(Path, "write_text", write)
    window, _ = fixture()
    with pytest.raises(OSError):
        run(**kwargs, comparison_request=request_for(window))
    assert kwargs["report_path"].read_bytes() == previous
    assert [row.get("status", "item") for row in records(consumer)] == ["started", "success", "started", "item", "failure"]


@pytest.mark.parametrize("role", comparison.ANCHORS)
def test_typed_missing_anchor_preserves_gap_without_invalid_relabel(role):
    window, prices = fixture()
    window.evidence[role].update(value=None, status="PROVIDER_GAP")
    result = evaluate(window, prices)
    assert result["reasons"] == ["anchor_missing", "observation_unusable"]
    assert result["observations"][role] == "PROVIDER_GAP"
    assert result["evidence"][role]["value"] is None


@pytest.mark.parametrize("kind", ["same_path", "symlink", "hardlink"])
def test_output_identity_collision_refuses_before_append(consumer, kind):
    _, run, _, captured, kwargs = consumer
    run(**kwargs)
    log = kwargs["attempt_log_path"]
    if kind == "same_path":
        report = log
    else:
        report = log.with_name("alias_report.md")
        if kind == "symlink":
            report.symlink_to(log)
        else:
            report.hardlink_to(log)
    original = log.read_bytes()
    window, _ = fixture()
    with pytest.raises(RuntimeError, match="report and log paths must be distinct"):
        run(**dict(kwargs, report_path=report), comparison_request=request_for(window))
    assert log.read_bytes() == original and report.read_bytes() == original
    assert len(captured) == 1


@pytest.mark.parametrize("role, key, value, reason", [
    ("raw_field", "share_basis", "UNKNOWN", "basis_unknown"),
    ("adjusted_field", "basis", "vendor_adjusted", "basis_unknown"),
    ("adjusted_field", "basis", "adjusted_close", "basis_unknown"),
    ("raw_field", "currency", "EUR", "currency_or_unit_incompatible"),
    ("adjusted_field", "currency", "EUR", "currency_or_unit_incompatible"),
    ("raw_field", "units", "cents/share", "currency_or_unit_incompatible"),
    ("adjusted_field", "units", "USD/share", "currency_or_unit_incompatible"),
])
def test_field_basis_and_currency_variants_D10_D12(role, key, value, reason):
    window, prices = fixture()
    window.evidence[role][key] = value
    assert evaluate(window, prices)["reasons"] == [reason]


def test_missing_prior_source_anchor_D13():
    window, prices = fixture()
    result = evaluate(window, prices.iloc[1:])
    assert result["reasons"] == ["anchor_missing", "window_invalid"]
    assert result["compared"] == 0


@pytest.mark.parametrize("field", comparison.AVAILABILITY_FIELDS[:-2])
def test_every_applicable_availability_clock_D19(field):
    window, prices = fixture()
    window.evidence["events"][0]["availability"][field] = C
    assert evaluate(window, prices)["reasons"] == ["availability_inconsistent"]


@pytest.mark.parametrize("role", [*comparison.ANCHORS, "raw_field", "adjusted_field", "event"])
def test_each_required_provenance_D40(role):
    window, prices = fixture()
    record = window.evidence["events"][0] if role == "event" else window.evidence[role]
    del record["provenance"]
    assert evaluate(window, prices)["reasons"] == ["evidence_identity_unproven"]


@pytest.mark.parametrize("kind", ["unverified", "late_start", "early_end"])
def test_coverage_declaration_variants_D34(kind):
    window, prices = fixture()
    row = window.evidence["coverage"]["events"]
    if kind == "unverified":
        row["verified"] = False
    elif kind == "late_start":
        row["from"] = C
    else:
        row["through"] = E+"T21:00:00Z"
    assert evaluate(window, prices)["reasons"] == ["coverage_unproven"]
