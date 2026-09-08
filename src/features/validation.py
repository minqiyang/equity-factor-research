"""Purged and bounded train/validation/test helpers for research panels.

The split object records the complete source index, explicit sample bounds,
label intervals, purge decisions, embargo decisions, and feature-history
requirements. It does not fetch data, choose parameters, run a backtest, or
make performance claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from features.operators import validate_panel_data


SPLIT_NAMES = ("train", "validation", "test")
LabelKind = Literal["price_forward_return", "synthetic_same_row_response"]
PanelOrSeries = pd.DataFrame | pd.Series


@dataclass(frozen=True)
class SplitTransitionMetadata:
    """Exact gap and embargo dates for one chronological transition."""

    transition_name: str
    upstream_split: str
    downstream_split: str
    inter_window_gap_dates: pd.DatetimeIndex
    gap_dates_consuming_embargo: pd.DatetimeIndex
    downstream_embargoed_dates: pd.DatetimeIndex

    def as_dict(self) -> dict[str, object]:
        """Return deterministic JSON-ready transition metadata."""

        return {
            "transition_name": self.transition_name,
            "upstream_split": self.upstream_split,
            "downstream_split": self.downstream_split,
            "inter_window_gap_dates": _serialize_dates(
                self.inter_window_gap_dates
            ),
            "inter_window_gap_date_count": len(self.inter_window_gap_dates),
            "gap_dates_consuming_embargo": _serialize_dates(
                self.gap_dates_consuming_embargo
            ),
            "gap_dates_consuming_embargo_count": len(
                self.gap_dates_consuming_embargo
            ),
            "downstream_embargoed_dates": _serialize_dates(
                self.downstream_embargoed_dates
            ),
            "downstream_embargoed_date_count": len(
                self.downstream_embargoed_dates
            ),
        }


@dataclass(frozen=True)
class SplitWindowMetadata:
    """Auditable date ownership and exclusion metadata for one window."""

    split_name: str
    configured_start: pd.Timestamp
    configured_end: pd.Timestamp
    realized_start: pd.Timestamp
    realized_end: pd.Timestamp
    candidate_dates: pd.DatetimeIndex
    eligible_dates: pd.DatetimeIndex
    purged_dates: pd.DatetimeIndex
    embargoed_dates: pd.DatetimeIndex
    excluded_dates: pd.DatetimeIndex
    feature_warm_up_dates: pd.DatetimeIndex
    label_warm_down_dates: pd.DatetimeIndex
    inter_window_gap_dates: pd.DatetimeIndex
    gap_dates_consuming_embargo: pd.DatetimeIndex
    invalid_reason: str | None
    feature_warm_up_rows: int
    label_horizon_rows: int
    embargo_rows: int

    @property
    def candidate_date_count(self) -> int:
        return len(self.candidate_dates)

    @property
    def eligible_date_count(self) -> int:
        return len(self.eligible_dates)

    @property
    def purged_date_count(self) -> int:
        return len(self.purged_dates)

    @property
    def embargoed_date_count(self) -> int:
        return len(self.embargoed_dates)

    @property
    def excluded_date_count(self) -> int:
        return len(self.excluded_dates)

    @property
    def has_eligible_labels(self) -> bool:
        return bool(self.eligible_date_count)

    @property
    def status(self) -> str:
        return "DIAGNOSTIC_ONLY" if self.has_eligible_labels else "INVALID"

    def as_dict(self) -> dict[str, object]:
        """Return deterministic JSON-ready window metadata."""

        return {
            "split_name": self.split_name,
            "configured_start": self.configured_start.isoformat(),
            "configured_end": self.configured_end.isoformat(),
            "realized_start": self.realized_start.isoformat(),
            "realized_end": self.realized_end.isoformat(),
            "candidate_signal_dates": _serialize_dates(self.candidate_dates),
            "candidate_signal_date_count": self.candidate_date_count,
            "eligible_signal_dates": _serialize_dates(self.eligible_dates),
            "eligible_signal_date_count": self.eligible_date_count,
            "purged_signal_dates": _serialize_dates(self.purged_dates),
            "purged_signal_date_count": self.purged_date_count,
            "embargoed_signal_dates": _serialize_dates(self.embargoed_dates),
            "embargoed_signal_date_count": self.embargoed_date_count,
            "excluded_signal_dates": _serialize_dates(self.excluded_dates),
            "excluded_signal_date_count": self.excluded_date_count,
            "has_eligible_labels": self.has_eligible_labels,
            "invalid_reason": self.invalid_reason,
            "status": self.status,
            "feature_warm_up_dates": _serialize_dates(
                self.feature_warm_up_dates
            ),
            "feature_warm_up_rows_requested": self.feature_warm_up_rows,
            "feature_warm_up_rows_available": len(self.feature_warm_up_dates),
            "label_warm_down_dates": _serialize_dates(
                self.label_warm_down_dates
            ),
            "label_warm_down_date_count": len(self.label_warm_down_dates),
            "label_horizon_rows": self.label_horizon_rows,
            "embargo_rows_requested": self.embargo_rows,
            "embargo_rows_satisfied_by_gap": len(
                self.gap_dates_consuming_embargo
            ),
            "inter_window_gap_dates": _serialize_dates(
                self.inter_window_gap_dates
            ),
            "inter_window_gap_date_count": len(self.inter_window_gap_dates),
            "gap_dates_consuming_embargo": _serialize_dates(
                self.gap_dates_consuming_embargo
            ),
        }


@dataclass(frozen=True)
class TrainValidationTestSplit:
    """Fully specified chronological split and label-eligibility schedule."""

    source_dates: pd.DatetimeIndex
    train: pd.DatetimeIndex
    validation: pd.DatetimeIndex
    test: pd.DatetimeIndex
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    validation_start: pd.Timestamp
    validation_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    label_kind: LabelKind
    label_derivation: str
    label_horizon_rows: int
    embargo_rows: int
    feature_warm_up_rows: int
    label_ledger: pd.DataFrame
    window_metadata: dict[str, SplitWindowMetadata]
    transition_metadata: dict[str, SplitTransitionMetadata]
    ignored_pre_sample_dates: pd.DatetimeIndex
    ignored_post_test_dates: pd.DatetimeIndex

    @property
    def all_dates(self) -> pd.DatetimeIndex:
        """Return all raw candidate dates in chronological order."""

        return self.train.append([self.validation, self.test])

    def as_dict(self) -> dict[str, pd.DatetimeIndex]:
        """Return raw candidate dates keyed by window name."""

        return {
            "train": self.train,
            "validation": self.validation,
            "test": self.test,
        }

    def eligible_as_dict(self) -> dict[str, pd.DatetimeIndex]:
        """Return structurally eligible label dates keyed by window name."""

        _validate_split(self)
        return {
            name: self.window_metadata[name].eligible_dates
            for name in SPLIT_NAMES
        }

    def window_summary(self) -> pd.DataFrame:
        """Return deterministic per-window audit metadata."""

        _validate_split(self)
        source_timezone = (
            None if self.source_dates.tz is None else str(self.source_dates.tz)
        )
        records: list[dict[str, object]] = []
        for name in SPLIT_NAMES:
            metadata = self.window_metadata[name]
            records.append(
                {
                    "split": name,
                    "configured_start": metadata.configured_start,
                    "configured_end": metadata.configured_end,
                    "realized_start": metadata.realized_start,
                    "realized_end": metadata.realized_end,
                    "candidate_dates": tuple(metadata.candidate_dates),
                    "candidate_date_count": metadata.candidate_date_count,
                    "eligible_dates": tuple(metadata.eligible_dates),
                    "eligible_date_count": metadata.eligible_date_count,
                    "purged_dates": tuple(metadata.purged_dates),
                    "purged_date_count": metadata.purged_date_count,
                    "embargoed_dates": tuple(metadata.embargoed_dates),
                    "embargoed_date_count": metadata.embargoed_date_count,
                    "excluded_dates": tuple(metadata.excluded_dates),
                    "excluded_date_count": metadata.excluded_date_count,
                    "has_eligible_labels": metadata.has_eligible_labels,
                    "invalid_reason": metadata.invalid_reason,
                    "status": metadata.status,
                    "feature_warm_up_dates": tuple(
                        metadata.feature_warm_up_dates
                    ),
                    "feature_warm_up_rows_requested": (
                        metadata.feature_warm_up_rows
                    ),
                    "feature_warm_up_rows_available": len(
                        metadata.feature_warm_up_dates
                    ),
                    "label_warm_down_dates": tuple(
                        metadata.label_warm_down_dates
                    ),
                    "label_warm_down_date_count": len(
                        metadata.label_warm_down_dates
                    ),
                    "label_horizon_rows": metadata.label_horizon_rows,
                    "embargo_rows_requested": metadata.embargo_rows,
                    "embargo_rows_satisfied_by_gap": len(
                        metadata.gap_dates_consuming_embargo
                    ),
                    "inter_window_gap_dates": tuple(
                        metadata.inter_window_gap_dates
                    ),
                    "inter_window_gap_date_count": len(
                        metadata.inter_window_gap_dates
                    ),
                    "ignored_pre_sample_dates": tuple(
                        self.ignored_pre_sample_dates
                    ),
                    "ignored_pre_sample_date_count": len(
                        self.ignored_pre_sample_dates
                    ),
                    "ignored_post_test_dates": tuple(
                        self.ignored_post_test_dates
                    ),
                    "ignored_post_test_date_count": len(
                        self.ignored_post_test_dates
                    ),
                    "source_index_start": self.source_dates[0],
                    "source_index_end": self.source_dates[-1],
                    "source_index_row_count": len(self.source_dates),
                    "source_index_timezone": source_timezone,
                }
            )
        return pd.DataFrame.from_records(records).set_index("split")

    def metadata_as_dict(self) -> dict[str, object]:
        """Return the complete deterministic split audit payload."""

        _validate_split(self)
        ledger_records: list[dict[str, object]] = []
        for row in self.label_ledger.itertuples(index=False):
            ledger_records.append(
                {
                    "split_name": row.split_name,
                    "label_kind": row.label_kind,
                    "label_derivation": row.label_derivation,
                    "signal_date": row.signal_date.isoformat(),
                    "label_start": row.label_start.isoformat(),
                    "label_end": (
                        None
                        if pd.isna(row.label_end)
                        else row.label_end.isoformat()
                    ),
                    "is_purged": bool(row.is_purged),
                    "is_embargoed": bool(row.is_embargoed),
                    "is_eligible": bool(row.is_eligible),
                    "exclusion_reasons": list(row.exclusion_reasons),
                }
            )

        return {
            "schema_version": 1,
            "label_kind": self.label_kind,
            "label_derivation": self.label_derivation,
            "label_horizon_rows": self.label_horizon_rows,
            "embargo_rows": self.embargo_rows,
            "feature_warm_up_rows": self.feature_warm_up_rows,
            "source_index": {
                "start": self.source_dates[0].isoformat(),
                "end": self.source_dates[-1].isoformat(),
                "row_count": len(self.source_dates),
                "timezone": (
                    None
                    if self.source_dates.tz is None
                    else str(self.source_dates.tz)
                ),
            },
            "ignored_pre_sample_dates": _serialize_dates(
                self.ignored_pre_sample_dates
            ),
            "ignored_post_test_dates": _serialize_dates(
                self.ignored_post_test_dates
            ),
            "windows": {
                name: self.window_metadata[name].as_dict()
                for name in SPLIT_NAMES
            },
            "transitions": {
                name: metadata.as_dict()
                for name, metadata in self.transition_metadata.items()
            },
            "label_ledger": ledger_records,
        }


def make_train_validation_test_split(
    index: pd.DatetimeIndex,
    *,
    train_start: str | pd.Timestamp,
    train_end: str | pd.Timestamp,
    validation_start: str | pd.Timestamp,
    validation_end: str | pd.Timestamp,
    test_start: str | pd.Timestamp,
    test_end: str | pd.Timestamp,
    label_kind: LabelKind,
    label_derivation: str,
    label_horizon_rows: int,
    embargo_rows: int = 0,
    feature_warm_up_rows: int = 0,
) -> TrainValidationTestSplit:
    """Build explicit raw windows and a label-eligibility schedule.

    All configured bounds are inclusive. Bounds may fall between observed
    source timestamps, but each window must realize at least one candidate.
    Label intervals are derived from source-index row positions; excluded
    targets are masked by the label helpers rather than removed from raw axes.
    """

    source_dates = _validate_date_index(index, name="index")
    boundaries = {
        "train_start": _coerce_boundary(
            train_start, "train_start", source_dates
        ),
        "train_end": _coerce_boundary(train_end, "train_end", source_dates),
        "validation_start": _coerce_boundary(
            validation_start, "validation_start", source_dates
        ),
        "validation_end": _coerce_boundary(
            validation_end, "validation_end", source_dates
        ),
        "test_start": _coerce_boundary(
            test_start, "test_start", source_dates
        ),
        "test_end": _coerce_boundary(test_end, "test_end", source_dates),
    }
    _validate_boundary_order(boundaries)
    _validate_label_contract(
        label_kind=label_kind,
        label_derivation=label_derivation,
        label_horizon_rows=label_horizon_rows,
    )
    _validate_non_negative_integer(embargo_rows, "embargo_rows")
    _validate_non_negative_integer(
        feature_warm_up_rows, "feature_warm_up_rows"
    )

    configured = {
        "train": (boundaries["train_start"], boundaries["train_end"]),
        "validation": (
            boundaries["validation_start"],
            boundaries["validation_end"],
        ),
        "test": (boundaries["test_start"], boundaries["test_end"]),
    }
    candidates = {
        name: source_dates[
            (source_dates >= start) & (source_dates <= end)
        ]
        for name, (start, end) in configured.items()
    }
    for name in SPLIT_NAMES:
        _validate_non_empty_window(candidates[name], name)

    transitions = {
        "train_to_validation": _build_transition_metadata(
            source_dates=source_dates,
            transition_name="train_to_validation",
            upstream_split="train",
            downstream_split="validation",
            upstream_end=boundaries["train_end"],
            downstream_start=boundaries["validation_start"],
            downstream_candidates=candidates["validation"],
            embargo_rows=embargo_rows,
        ),
        "validation_to_test": _build_transition_metadata(
            source_dates=source_dates,
            transition_name="validation_to_test",
            upstream_split="validation",
            downstream_split="test",
            upstream_end=boundaries["validation_end"],
            downstream_start=boundaries["test_start"],
            downstream_candidates=candidates["test"],
            embargo_rows=embargo_rows,
        ),
    }
    embargoed_by_window = {
        "train": pd.DatetimeIndex([], tz=source_dates.tz),
        "validation": transitions[
            "train_to_validation"
        ].downstream_embargoed_dates,
        "test": transitions[
            "validation_to_test"
        ].downstream_embargoed_dates,
    }

    warm_up_by_window = {
        name: _feature_warm_up_dates(
            source_dates,
            candidates[name][0],
            feature_warm_up_rows,
            split_name=name,
        )
        for name in SPLIT_NAMES
    }
    ledger = _build_label_ledger(
        source_dates=source_dates,
        candidates=candidates,
        configured=configured,
        embargoed_by_window=embargoed_by_window,
        label_kind=label_kind,
        label_derivation=label_derivation,
        label_horizon_rows=label_horizon_rows,
    )

    window_metadata: dict[str, SplitWindowMetadata] = {}
    for name in SPLIT_NAMES:
        rows = ledger.loc[ledger["split_name"].eq(name)]
        eligible_dates = pd.DatetimeIndex(
            rows.loc[rows["is_eligible"], "signal_date"].array
        )
        purged_dates = pd.DatetimeIndex(
            rows.loc[rows["is_purged"], "signal_date"].array
        )
        embargoed_dates = pd.DatetimeIndex(
            rows.loc[rows["is_embargoed"], "signal_date"].array
        )
        excluded_dates = pd.DatetimeIndex(
            rows.loc[~rows["is_eligible"], "signal_date"].array
        )
        transition = (
            None
            if name == "train"
            else transitions[
                "train_to_validation"
                if name == "validation"
                else "validation_to_test"
            ]
        )
        gap_dates = (
            pd.DatetimeIndex([], tz=source_dates.tz)
            if transition is None
            else transition.inter_window_gap_dates
        )
        gap_consumed = (
            pd.DatetimeIndex([], tz=source_dates.tz)
            if transition is None
            else transition.gap_dates_consuming_embargo
        )
        window_metadata[name] = SplitWindowMetadata(
            split_name=name,
            configured_start=configured[name][0],
            configured_end=configured[name][1],
            realized_start=candidates[name][0],
            realized_end=candidates[name][-1],
            candidate_dates=candidates[name],
            eligible_dates=eligible_dates,
            purged_dates=purged_dates,
            embargoed_dates=embargoed_dates,
            excluded_dates=excluded_dates,
            feature_warm_up_dates=warm_up_by_window[name],
            label_warm_down_dates=purged_dates,
            inter_window_gap_dates=gap_dates,
            gap_dates_consuming_embargo=gap_consumed,
            invalid_reason=(
                None if len(eligible_dates) else "no_eligible_labels"
            ),
            feature_warm_up_rows=feature_warm_up_rows,
            label_horizon_rows=label_horizon_rows,
            embargo_rows=embargo_rows,
        )

    train_warm_up = warm_up_by_window["train"]
    ignored_pre_sample = source_dates[
        source_dates < boundaries["train_start"]
    ].difference(train_warm_up, sort=False)
    ignored_post_test = source_dates[source_dates > boundaries["test_end"]]

    return TrainValidationTestSplit(
        source_dates=source_dates,
        train=candidates["train"],
        validation=candidates["validation"],
        test=candidates["test"],
        train_start=boundaries["train_start"],
        train_end=boundaries["train_end"],
        validation_start=boundaries["validation_start"],
        validation_end=boundaries["validation_end"],
        test_start=boundaries["test_start"],
        test_end=boundaries["test_end"],
        label_kind=label_kind,
        label_derivation=label_derivation,
        label_horizon_rows=label_horizon_rows,
        embargo_rows=embargo_rows,
        feature_warm_up_rows=feature_warm_up_rows,
        label_ledger=ledger,
        window_metadata=window_metadata,
        transition_metadata=transitions,
        ignored_pre_sample_dates=ignored_pre_sample,
        ignored_post_test_dates=ignored_post_test,
    )


def split_panel_by_train_validation_test(
    panel: pd.DataFrame,
    split: TrainValidationTestSplit,
    *,
    panel_role: Literal["feature"],
    name: str = "panel",
) -> dict[str, pd.DataFrame]:
    """Slice an explicitly identified feature panel on raw candidate axes."""

    _validate_split(split)
    if panel_role != "feature":
        raise ValueError(
            "panel_role must be feature; label targets require the "
            "label-aware slicer"
        )
    validated = validate_panel_data(panel, name=name)
    _validate_source_alignment(validated.index, split, name=name)
    return {
        split_name: validated.loc[dates].copy()
        for split_name, dates in split.as_dict().items()
    }


def make_price_forward_return_labels(
    values: PanelOrSeries,
    split: TrainValidationTestSplit,
    *,
    name: str = "values",
) -> PanelOrSeries:
    """Calculate only structurally eligible row-horizon price labels."""

    _validate_split(split)
    if split.label_kind != "price_forward_return":
        raise ValueError(
            "split label_kind must be price_forward_return for price labels"
        )
    validated = _validate_panel_or_series(values, name=name)
    _validate_source_alignment(validated.index, split, name=name)
    labels = _all_nan_like(validated)

    eligible_rows = split.label_ledger.loc[
        split.label_ledger["is_eligible"]
    ]
    if not eligible_rows.empty:
        start_values = validated.loc[eligible_rows["label_start"]].to_numpy()
        end_values = validated.loc[eligible_rows["label_end"]].to_numpy()
        labels.loc[eligible_rows["signal_date"]] = end_values / start_values - 1.0
    return labels


def mask_label_panel_by_train_validation_test(
    labels: PanelOrSeries,
    split: TrainValidationTestSplit,
    *,
    name: str = "labels",
) -> PanelOrSeries:
    """Mask all non-eligible label rows while preserving the source axis."""

    _validate_split(split)
    validated = _validate_panel_or_series(labels, name=name)
    _validate_source_alignment(validated.index, split, name=name)
    masked = _all_nan_like(validated)
    eligible_dates = _append_indexes(
        [
            split.window_metadata[split_name].eligible_dates
            for split_name in SPLIT_NAMES
        ],
        tz=split.source_dates.tz,
    )
    masked.loc[eligible_dates] = validated.loc[eligible_dates]
    return masked


def split_label_panel_by_train_validation_test(
    labels: PanelOrSeries,
    split: TrainValidationTestSplit,
    *,
    name: str = "labels",
) -> dict[str, PanelOrSeries]:
    """Slice an already structurally masked target on every raw window axis."""

    _validate_split(split)
    validated = _validate_panel_or_series(labels, name=name)
    _validate_source_alignment(validated.index, split, name=name)
    _validate_structural_mask(validated, split, name=name)
    return {
        split_name: validated.loc[dates].copy()
        for split_name, dates in split.as_dict().items()
    }


def summarize_label_availability(
    labels: pd.DataFrame,
    split: TrainValidationTestSplit,
    *,
    factors: Mapping[str, pd.DataFrame],
    name: str = "labels",
) -> pd.DataFrame:
    """Audit structural target cells and usable factor-label pairs."""

    _validate_split(split)
    validated_labels = validate_panel_data(labels, name=name)
    _validate_source_alignment(validated_labels.index, split, name=name)
    _validate_structural_mask(validated_labels, split, name=name)
    if not isinstance(factors, Mapping) or not factors:
        raise ValueError("factors must contain at least one named factor panel")

    validated_factors: dict[str, pd.DataFrame] = {}
    for factor_name, factor in factors.items():
        if not isinstance(factor_name, str) or not factor_name.strip():
            raise ValueError("factor names must be non-empty strings")
        validated_factor = validate_panel_data(
            factor,
            name=f"factors[{factor_name!r}]",
        )
        _validate_source_alignment(
            validated_factor.index,
            split,
            name=f"factors[{factor_name!r}]",
        )
        if not validated_factor.columns.equals(validated_labels.columns):
            raise ValueError(
                f"factors[{factor_name!r}] columns must exactly match "
                f"{name} columns"
            )
        validated_factors[factor_name] = validated_factor

    records: list[dict[str, object]] = []
    for split_name in SPLIT_NAMES:
        metadata = split.window_metadata[split_name]
        eligible_labels = validated_labels.loc[metadata.eligible_dates]
        total_target_cells = int(eligible_labels.size)
        valid_target_cells = int(eligible_labels.notna().sum().sum())
        for factor_name, factor in validated_factors.items():
            eligible_factor = factor.loc[metadata.eligible_dates]
            usable_pairs = int(
                (eligible_factor.notna() & eligible_labels.notna())
                .sum()
                .sum()
            )
            if not metadata.has_eligible_labels:
                invalid_reason = "no_eligible_labels"
            elif usable_pairs == 0:
                invalid_reason = "no_usable_label_pairs"
            else:
                invalid_reason = None
            records.append(
                {
                    "split": split_name,
                    "factor": factor_name,
                    "candidate_date_count": metadata.candidate_date_count,
                    "eligible_date_count": metadata.eligible_date_count,
                    "total_eligible_target_cells": total_target_cells,
                    "valid_eligible_target_cells": valid_target_cells,
                    "missing_eligible_target_cells": (
                        total_target_cells - valid_target_cells
                    ),
                    "usable_factor_label_pairs": usable_pairs,
                    "has_usable_label_pairs": bool(usable_pairs),
                    "invalid_reason": invalid_reason,
                    "status": (
                        "INVALID"
                        if invalid_reason is not None
                        else "DIAGNOSTIC_ONLY"
                    ),
                }
            )

    return pd.DataFrame.from_records(records).set_index("split")


def resolve_diagnostic_classification(
    *,
    availability_invalid_reason: object,
    metric_valid_date_counts: Mapping[str, int],
    all_metrics_empty_invalid_reason: str = (
        "no_valid_factor_diagnostic_dates"
    ),
) -> tuple[str | None, str]:
    """Combine label availability with realized diagnostic coverage."""

    if not isinstance(metric_valid_date_counts, Mapping):
        raise TypeError("metric_valid_date_counts must be a mapping")
    if not metric_valid_date_counts:
        raise ValueError("metric_valid_date_counts must not be empty")
    for metric_name, valid_date_count in metric_valid_date_counts.items():
        if not isinstance(metric_name, str) or not metric_name.strip():
            raise ValueError("metric names must be non-empty strings")
        _validate_non_negative_integer(
            valid_date_count,
            f"metric_valid_date_counts[{metric_name!r}]",
        )
    if (
        not isinstance(all_metrics_empty_invalid_reason, str)
        or not all_metrics_empty_invalid_reason.strip()
    ):
        raise ValueError(
            "all_metrics_empty_invalid_reason must be a non-empty string"
        )

    if not pd.isna(availability_invalid_reason):
        return str(availability_invalid_reason), "INVALID"
    if all(count == 0 for count in metric_valid_date_counts.values()):
        return all_metrics_empty_invalid_reason, "INVALID"
    return None, "DIAGNOSTIC_ONLY"


def _build_transition_metadata(
    *,
    source_dates: pd.DatetimeIndex,
    transition_name: str,
    upstream_split: str,
    downstream_split: str,
    upstream_end: pd.Timestamp,
    downstream_start: pd.Timestamp,
    downstream_candidates: pd.DatetimeIndex,
    embargo_rows: int,
) -> SplitTransitionMetadata:
    gap_dates = source_dates[
        (source_dates > upstream_end) & (source_dates < downstream_start)
    ]
    protected_dates = source_dates[source_dates > upstream_end][:embargo_rows]
    gap_consumed = protected_dates[
        protected_dates.isin(gap_dates)
    ]
    downstream_embargoed = protected_dates[
        protected_dates.isin(downstream_candidates)
    ]
    return SplitTransitionMetadata(
        transition_name=transition_name,
        upstream_split=upstream_split,
        downstream_split=downstream_split,
        inter_window_gap_dates=gap_dates,
        gap_dates_consuming_embargo=gap_consumed,
        downstream_embargoed_dates=downstream_embargoed,
    )


def _feature_warm_up_dates(
    source_dates: pd.DatetimeIndex,
    first_candidate: pd.Timestamp,
    feature_warm_up_rows: int,
    *,
    split_name: str,
) -> pd.DatetimeIndex:
    available = source_dates[source_dates < first_candidate]
    if len(available) < feature_warm_up_rows:
        raise ValueError(
            f"{split_name} feature warm-up requires "
            f"{feature_warm_up_rows} rows but only {len(available)} are available"
        )
    return available[-feature_warm_up_rows:] if feature_warm_up_rows else available[:0]


def _build_label_ledger(
    *,
    source_dates: pd.DatetimeIndex,
    candidates: dict[str, pd.DatetimeIndex],
    configured: dict[str, tuple[pd.Timestamp, pd.Timestamp]],
    embargoed_by_window: dict[str, pd.DatetimeIndex],
    label_kind: LabelKind,
    label_derivation: str,
    label_horizon_rows: int,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    source_positions = {
        timestamp: position
        for position, timestamp in enumerate(source_dates)
    }
    for split_name in SPLIT_NAMES:
        configured_end = configured[split_name][1]
        embargoed = embargoed_by_window[split_name]
        for signal_date in candidates[split_name]:
            position = source_positions[signal_date]
            end_position = position + label_horizon_rows
            label_end = (
                source_dates[end_position]
                if end_position < len(source_dates)
                else pd.NaT
            )
            reasons: list[str] = []
            if pd.isna(label_end):
                reasons.append("label_end_unavailable")
            elif label_end > configured_end:
                reasons.append("label_crosses_window_end")
            is_purged = bool(reasons)
            is_embargoed = bool(signal_date in embargoed)
            if is_embargoed:
                reasons.append("embargo")
            records.append(
                {
                    "split_name": split_name,
                    "label_kind": label_kind,
                    "label_derivation": label_derivation,
                    "signal_date": signal_date,
                    "label_start": signal_date,
                    "label_end": label_end,
                    "is_purged": is_purged,
                    "is_embargoed": is_embargoed,
                    "is_eligible": not is_purged and not is_embargoed,
                    "exclusion_reasons": tuple(reasons),
                }
            )
    return pd.DataFrame.from_records(
        records,
        columns=[
            "split_name",
            "label_kind",
            "label_derivation",
            "signal_date",
            "label_start",
            "label_end",
            "is_purged",
            "is_embargoed",
            "is_eligible",
            "exclusion_reasons",
        ],
    )


def _validate_panel_or_series(
    values: PanelOrSeries,
    *,
    name: str,
) -> PanelOrSeries:
    if isinstance(values, pd.DataFrame):
        return validate_panel_data(values, name=name)
    if not isinstance(values, pd.Series):
        raise TypeError(f"{name} must be a pandas DataFrame or Series")
    _validate_date_index(values.index, name=f"{name} index")
    if is_bool_dtype(values.dtype) or not is_numeric_dtype(values.dtype):
        raise TypeError(f"{name} must have a numeric non-boolean dtype")
    validated = values.astype(float)
    if np.isinf(validated.to_numpy()).any():
        raise ValueError(f"{name} must contain finite numeric values or NaN")
    return validated


def _validate_source_alignment(
    index: pd.DatetimeIndex,
    split: TrainValidationTestSplit,
    *,
    name: str,
) -> None:
    if not index.equals(split.source_dates):
        raise ValueError(f"{name} index must exactly match split source index")


def _validate_structural_mask(
    labels: PanelOrSeries,
    split: TrainValidationTestSplit,
    *,
    name: str,
) -> None:
    eligible_dates = _append_indexes(
        [
            split.window_metadata[split_name].eligible_dates
            for split_name in SPLIT_NAMES
        ],
        tz=split.source_dates.tz,
    )
    excluded_dates = split.source_dates[~split.source_dates.isin(eligible_dates)]
    excluded_values = labels.loc[excluded_dates]
    if isinstance(excluded_values, pd.DataFrame):
        has_value = bool(excluded_values.notna().any().any())
    else:
        has_value = bool(excluded_values.notna().any())
    if has_value:
        raise ValueError(
            f"{name} contains values on structurally excluded label dates"
        )


def _all_nan_like(values: PanelOrSeries) -> PanelOrSeries:
    result = values.copy()
    if isinstance(result, pd.DataFrame):
        result.loc[:, :] = np.nan
    else:
        result.loc[:] = np.nan
    return result


def _append_indexes(
    indexes: list[pd.DatetimeIndex],
    *,
    tz: object,
) -> pd.DatetimeIndex:
    if not indexes:
        return pd.DatetimeIndex([], tz=tz)
    result = indexes[0]
    for index in indexes[1:]:
        result = result.append(index)
    return result


def _validate_split(split: TrainValidationTestSplit) -> None:
    if not isinstance(split, TrainValidationTestSplit):
        raise TypeError("split must be a TrainValidationTestSplit")

    try:
        canonical = make_train_validation_test_split(
            split.source_dates,
            train_start=split.train_start,
            train_end=split.train_end,
            validation_start=split.validation_start,
            validation_end=split.validation_end,
            test_start=split.test_start,
            test_end=split.test_end,
            label_kind=split.label_kind,
            label_derivation=split.label_derivation,
            label_horizon_rows=split.label_horizon_rows,
            embargo_rows=split.embargo_rows,
            feature_warm_up_rows=split.feature_warm_up_rows,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("split contract fields are invalid") from exc

    index_fields = (
        "source_dates",
        "train",
        "validation",
        "test",
        "ignored_pre_sample_dates",
        "ignored_post_test_dates",
    )
    for field in index_fields:
        actual_index = getattr(split, field)
        expected_index = getattr(canonical, field)
        if not isinstance(actual_index, pd.DatetimeIndex) or not actual_index.equals(
            expected_index
        ):
            raise ValueError(
                f"split {field} does not match the canonical contract"
            )

    try:
        pd.testing.assert_frame_equal(
            split.label_ledger,
            canonical.label_ledger,
            check_dtype=True,
            check_exact=True,
            check_like=False,
        )
    except (AssertionError, TypeError) as exc:
        raise ValueError(
            "split label_ledger does not match the canonical contract"
        ) from exc

    if tuple(split.window_metadata) != tuple(canonical.window_metadata):
        raise ValueError(
            "split window_metadata keys do not match the canonical contract"
        )
    for name in SPLIT_NAMES:
        actual = split.window_metadata.get(name)
        if (
            not isinstance(actual, SplitWindowMetadata)
            or actual.as_dict() != canonical.window_metadata[name].as_dict()
        ):
            raise ValueError(
                "split window_metadata does not match the canonical contract"
            )

    if tuple(split.transition_metadata) != tuple(
        canonical.transition_metadata
    ):
        raise ValueError(
            "split transition_metadata keys do not match the canonical contract"
        )
    for name, expected in canonical.transition_metadata.items():
        actual = split.transition_metadata.get(name)
        if (
            not isinstance(actual, SplitTransitionMetadata)
            or actual.as_dict() != expected.as_dict()
        ):
            raise ValueError(
                "split transition_metadata does not match the canonical contract"
            )


def _validate_date_index(
    index: pd.DatetimeIndex,
    *,
    name: str,
) -> pd.DatetimeIndex:
    if not isinstance(index, pd.DatetimeIndex):
        raise TypeError(f"{name} must be a pandas DatetimeIndex")
    if index.empty:
        raise ValueError(f"{name} must not be empty")
    if index.has_duplicates:
        raise ValueError(f"{name} must not contain duplicate dates")
    if not index.is_monotonic_increasing:
        raise ValueError(f"{name} must be sorted in increasing date order")
    return index


def _coerce_boundary(
    value: str | pd.Timestamp,
    name: str,
    source_dates: pd.DatetimeIndex,
) -> pd.Timestamp:
    if not isinstance(value, (str, pd.Timestamp)):
        raise TypeError(f"{name} must be a date string or pandas Timestamp")
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        raise ValueError(f"{name} must be a valid timestamp")
    source_is_aware = source_dates.tz is not None
    boundary_is_aware = timestamp.tzinfo is not None
    if source_is_aware != boundary_is_aware:
        raise ValueError(
            f"{name} timezone must be compatible with the source index timezone"
        )
    return timestamp


def _validate_boundary_order(
    boundaries: dict[str, pd.Timestamp],
) -> None:
    if not (
        boundaries["train_start"] <= boundaries["train_end"]
        < boundaries["validation_start"]
        <= boundaries["validation_end"]
        < boundaries["test_start"]
        <= boundaries["test_end"]
    ):
        raise ValueError(
            "split boundaries must satisfy train_start <= train_end < "
            "validation_start <= validation_end < test_start <= test_end"
        )


def _validate_label_contract(
    *,
    label_kind: str,
    label_derivation: str,
    label_horizon_rows: object,
) -> None:
    if label_kind not in {
        "price_forward_return",
        "synthetic_same_row_response",
    }:
        raise ValueError(
            "label_kind must be price_forward_return or "
            "synthetic_same_row_response"
        )
    if not isinstance(label_derivation, str) or not label_derivation.strip():
        raise ValueError("label_derivation must be a non-empty string")
    if isinstance(label_horizon_rows, bool) or not isinstance(
        label_horizon_rows, int
    ):
        raise TypeError("label_horizon_rows must be an integer")
    if label_kind == "price_forward_return" and label_horizon_rows < 1:
        raise ValueError(
            "price_forward_return label_horizon_rows must be at least 1"
        )
    if (
        label_kind == "synthetic_same_row_response"
        and label_horizon_rows != 0
    ):
        raise ValueError(
            "synthetic_same_row_response label_horizon_rows must equal 0"
        )


def _validate_non_negative_integer(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be at least 0")


def _validate_non_empty_window(index: pd.DatetimeIndex, name: str) -> None:
    if index.empty:
        raise ValueError(f"{name} split must contain at least one candidate date")


def _serialize_dates(index: pd.DatetimeIndex) -> list[str]:
    return [timestamp.isoformat() for timestamp in index]


__all__ = [
    "LabelKind",
    "SplitTransitionMetadata",
    "SplitWindowMetadata",
    "TrainValidationTestSplit",
    "make_price_forward_return_labels",
    "make_train_validation_test_split",
    "mask_label_panel_by_train_validation_test",
    "resolve_diagnostic_classification",
    "split_label_panel_by_train_validation_test",
    "split_panel_by_train_validation_test",
    "summarize_label_availability",
]
