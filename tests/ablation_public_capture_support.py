"""Committed synthetic public corpus promoted from the accepted A2 probe."""

from dataclasses import asdict
from decimal import Decimal
from fractions import Fraction
import json

import numpy as np
import pandas as pd

from backtest.portfolio import (
    apply_tracked_backtest_source_mutation,
    capture_backtest_source_provenance,
)


def cases():
    result = {}
    for rows, columns in [(0, 0), (1, 0), (2, 0), (5, 0), (0, 1), (0, 2), (0, 5), (1, 1), (2, 2), (5, 3)]:
        result[f"shape_{rows}x{columns}"] = pd.DataFrame(
            1.0, index=pd.date_range("2020-01-01", periods=rows),
            columns=list(range(columns)),
        )
    dates = pd.date_range("2020-01-01", periods=2)
    result["named_duplicate_axes"] = pd.DataFrame(
        [[1.0, -0.0], [2.0, np.nan]],
        index=pd.DatetimeIndex([dates[0], dates[0]], name="observed"),
        columns=pd.Index(["asset", "asset"], name="listing"),
    )
    result["duplicate_index_zero_columns"] = pd.DataFrame(
        index=pd.Index(["same", "same"], name="observation"),
        columns=pd.Index([], name="listing"),
    )
    result["zero_rows_duplicate_columns"] = pd.DataFrame(
        index=pd.DatetimeIndex([], name="observed", tz="UTC"),
        columns=pd.Index(["same", "same"], name="listing"), dtype="float64",
    )
    result["named_zero_axes"] = pd.DataFrame(
        index=pd.Index([], name="observed"), columns=pd.Index([], name="listing"),
    )
    result["multiindex_axes"] = pd.DataFrame(
        [[1, 2], [3, 4]],
        index=pd.MultiIndex.from_tuples([("a", 1), ("a", 1)], names=["group", "row"]),
        columns=pd.MultiIndex.from_tuples([("x", 1), ("x", 1)], names=["group", "col"]),
    )
    result["multiindex_zero_columns"] = pd.DataFrame(
        index=pd.MultiIndex.from_tuples([("a", 1), ("a", 1)], names=["group", "row"]),
        columns=pd.MultiIndex.from_tuples([], names=["group", "col"]),
    )
    result["unsorted_timezone_dates"] = pd.DataFrame(
        {"asset": [1.0, 2.0]},
        index=pd.DatetimeIndex(["2020-01-02", "2020-01-01"], tz="UTC", name="observed"),
    )
    result["mixed_uint64_float"] = pd.DataFrame(
        {"large": np.array([2**63 + 1, 2**63 + 3], dtype=np.uint64), "real": [1.5, -0.0]}, index=dates,
    )
    result["mixed_real_complex"] = pd.DataFrame(
        {"real": [1.0, -0.0], "complex": [1 + 2j, complex(-0.0, -0.0)]}, index=dates,
    )
    result["nullable_fraction"] = pd.DataFrame(
        {"integer": pd.array([1, None], dtype="Int64"), "fraction": [Fraction(1, 3), None]}, index=dates,
    )
    result["nullable_unsigned_boolean_float"] = pd.DataFrame({
        "unsigned": pd.array([2**63 + 1, None], dtype="UInt64"),
        "boolean": pd.array([True, None], dtype="boolean"),
        "float": pd.array([-0.0, None], dtype="Float64"),
    }, index=dates)
    result["heterogeneous_object"] = pd.DataFrame({
        "integer": pd.Series([2**100, np.uint64(2**63 + 1)], dtype=object).array,
        "fraction": pd.Series([Fraction(1, 3), Decimal("1.20")], dtype=object).array,
        "missing": pd.Series([None, pd.NA], dtype=object).array,
        "boolean": pd.Series([True, np.bool_(False)], dtype=object).array,
        "numeric": pd.Series([complex(1, -0.0), -0.0], dtype=object).array,
    }, index=dates)
    result["float_widths_nonfinite"] = pd.DataFrame({
        "float16": np.array([-0.0, np.inf], dtype=np.float16),
        "float32": np.array([np.nan, -np.inf], dtype=np.float32),
        "float64": np.array([np.nextafter(0.0, 1.0), np.finfo(np.float64).max]),
    }, index=dates)
    result["native_integer_widths"] = pd.DataFrame({
        "int8": np.array([-128, 127], dtype=np.int8),
        "int64": np.array([-(2**63), 2**63 - 1], dtype=np.int64),
        "uint64": np.array([0, 2**64 - 1], dtype=np.uint64),
        "bool": [True, False],
    }, index=dates)
    result["string_and_categorical"] = pd.DataFrame({
        "string": pd.array(["text", None], dtype="string"),
        "category": pd.Categorical(["x", None], categories=["y", "x"], ordered=True),
    }, index=dates)
    result["numeric_categorical"] = pd.DataFrame({
        "integer": pd.Categorical([1, 2]),
        "mixed": pd.Categorical([Fraction(1, 3), None]),
    }, index=dates)
    result["date_time_extension"] = pd.DataFrame({
        "naive": pd.to_datetime(["2020-01-01", None]),
        "aware": pd.to_datetime(["2020-01-01", None], utc=True),
        "delta": pd.to_timedelta([1, None], unit="D"),
        "period": pd.arrays.PeriodArray(pd.period_range("2020-01", periods=2, freq="M")),
        "interval": pd.arrays.IntervalArray.from_tuples([(0, 1), (1, 2)]),
    }, index=dates)
    result["sparse_numeric"] = pd.DataFrame({
        "sparse": pd.arrays.SparseArray([0.0, 1.0], fill_value=0.0),
        "real": [np.nan, -0.0],
    }, index=dates)
    result["empty_extension_columns"] = pd.DataFrame({
        "int": pd.array([], dtype="Int64"), "float": pd.array([], dtype="Float64"),
        "bool": pd.array([], dtype="boolean"), "string": pd.array([], dtype="string"),
    })
    result["noncontiguous_selection"] = result["native_integer_widths"].iloc[::-1, ::-1]
    # Baseline must reject this exact custom numeric type, rather than coerce it.
    class CustomFloat(float):
        pass
    result["unsupported_custom_real"] = pd.DataFrame({"value": [CustomFloat(1.0)]}, dtype=object)
    return result


def frame_record(provenance):
    return {
        "schema_version": provenance.schema_version,
        "role": provenance.role,
        "axis_fingerprint": provenance.axis_fingerprint,
        "original_dtype_names": provenance.original_dtype_names,
        "original_dtype_families": provenance.original_dtype_families,
        "original_cells": [[asdict(cell) for cell in row] for row in provenance.original_cells],
        "original_state_digest": provenance.original_state_digest,
        "current_state_digest": provenance.current_state_digest,
        "mutations": [asdict(record) for record in provenance.mutations],
    }


def public_record(provenance):
    return {
        "schema_version": provenance.schema_version,
        "prices": frame_record(provenance.prices),
        "signals": frame_record(provenance.signals),
    }


def error_record(error):
    return {"status": "rejected", "type": f"{type(error).__module__}.{type(error).__qualname__}",
            "reason": getattr(error, "reason", None), "message": str(error),
            "date": getattr(error, "date", None), "asset": getattr(error, "asset", None)}


def collect():
    records = {}
    for name, source in cases().items():
        try:
            captured = capture_backtest_source_provenance(source, source.copy(deep=True))
            records[name] = {"status": "accepted", "shape": list(source.shape), "capture": public_record(captured)}
        except Exception as error:
            records[name] = error_record(error)
    for role in ("prices", "signals"):
        prices = pd.DataFrame({"asset": [100.0, 101.0, 102.0]}, index=pd.date_range("2020-01-01", periods=3))
        signals = prices / 100.0
        captured = capture_backtest_source_provenance(prices, signals)
        events = [{"capture": public_record(captured)}]
        for row, value in [(0, -0.0), (1, complex(2.0, 0.0)), (2, np.nan)]:
            try:
                prices, signals, captured = apply_tracked_backtest_source_mutation(
                    prices, signals, captured, source_role=role,
                    row_position=row, column_position=0, value=value,
                )
                recaptured = capture_backtest_source_provenance(prices, signals)
                events.append({"status": "accepted", "capture": public_record(captured),
                               "recapture": public_record(recaptured)})
            except Exception as error:
                events.append(error_record(error))
        records[f"tracked_chain_{role}"] = events
    for argument in (None, [], 1):
        for role in ("prices", "signals"):
            frame = pd.DataFrame([[1.0]])
            try:
                captured = capture_backtest_source_provenance(
                    argument if role == "prices" else frame,
                    argument if role == "signals" else frame,
                )
                value = {"status": "accepted", "capture": public_record(captured)}
            except Exception as error:
                value = error_record(error)
            records[f"invalid_{role}_{type(argument).__name__}"] = value
    # JSON round trip ensures identical tuple/list representation in test oracles.
    return json.loads(json.dumps(records, sort_keys=True))


