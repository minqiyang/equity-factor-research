"""Frozen RunConfig and authorized campaign orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from bisect import bisect_left, bisect_right
from datetime import date, datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
from types import MappingProxyType

from campaign.baselines import (
    episode_gross_return,
    equal_weight_universe_target,
    random_rank_target,
)
from campaign.bundle import (
    BundleAssembly,
    assemble_evidence_bundle,
    invalid_and_missing_bytes,
    required_bundle_children,
)
from campaign.diagnostics import (
    CommonCaseMonth,
    common_case_robustness,
    decile_return_curve,
    descriptive_rank_ic,
    label_coverage,
    spearman_rank_ic,
    yearly_rank_ic_contributions,
)
from campaign.eligibility import (
    DecisionTimeListing,
    FrozenDecisionTime,
    build_frozen_decision_time,
)
from campaign.inference import (
    FACTOR_ORDER,
    FactorVector,
    HOLM_ALPHA,
    LONG_SEGMENT_BLOCK_LENGTH,
    bootstrap_mean_rank_ic,
    holm_adjust,
)
from campaign.paths import ContinuousHoldings, advance_holdings, holding_interval
from campaign.precondition import (
    Authorization,
    authorize,
    result_bearing_refusal_reason,
)
from campaign.reconciliation import (
    ReconciliationResult,
    parse_trial_inventory,
    reconcile_semantic_trials,
    required_output_names,
)
from campaign.registry import factor_spec
from campaign.returns import SimpleReturn, simple_adjusted_close_return
from campaign.schedule import CampaignSchedule, build_campaign_schedule


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_FAMILYWISE_ALPHA = "0.05"
_COST_BPS = (0, 10, 25)
_BIT_GENERATOR = "PCG64DXSM"
_QUANTILE_METHOD = "linear"
_HORIZON_RETURN_ROWS = 21
_HORIZON_PURGE_ROWS = 22
_EMBARGO_ROWS = 0
_DECILE_COUNT = 10
_MIN_ELIGIBLE = 100
_MIN_DISTINCT = 10
_COMMON_MONTHS = 60
_BOOTSTRAP_REPLICATES = 20000
_RANDOM_RANK_SEED = 20260729
_BOOTSTRAP_SEED = 20260730
_STATUS_REFUSED = "REFUSED"
_STATUS_AUTHORIZED = "AUTHORIZED"
_STATUS_EXECUTED = "EXECUTED_DIAGNOSTIC_ONLY"
_EVIDENCE_CEILING = "DIAGNOSTIC_ONLY"
_RUN_RECORD_SCHEMA = "campaign_run_record_v1"
_PROTOCOL_CHILD = "eodhd_sp500_three_factor_diagnostic_v1.yaml"
_INVENTORY_CHILD = "trial_inventory.json"
_RUN_MANIFEST_CHILD = "run_manifest.json"
_INVALID_CHILD = "invalid_and_missing_summary.json"
_SENTINEL_BODY = b"STAGE4_G2_PREPARED_CAMPAIGN_NOT_BOUND_NO_PANEL_ACCESS"
_REASON_PREPARED_BYTES = "PREPARED_CAMPAIGN_BYTES_MISMATCH"
_REASON_PREPARED_SENTINEL = "PREPARED_CAMPAIGN_IS_SENTINEL"
_REASON_PREPARED_UNPARSEABLE = "PREPARED_CAMPAIGN_UNPARSEABLE"
_REASON_PREPARED_SCHEMA = "PREPARED_CAMPAIGN_SCHEMA_INVALID"
_REASON_ATTEMPT_ABSENT = "CAMPAIGN_ATTEMPT_STATE_ABSENT"
_REASON_ATTEMPT_INVALID = "CAMPAIGN_ATTEMPT_STATE_INVALID"
_REASON_ATTEMPT_CONSUMED = "CAMPAIGN_ATTEMPT_ALREADY_CONSUMED"
_REASON_ATTEMPT_LEDGER = "CAMPAIGN_ATTEMPT_LEDGER_MISMATCH"
_REASON_BUNDLE_MISSING = "BUNDLE_CHILD_MISSING"
_REASON_PROTOCOL = "PROTOCOL_FREEZE_BYTES_MISMATCH"
_REASON_INVENTORY = "TRIAL_INVENTORY_BYTES_MISMATCH"
_REASON_ZERO_TARGET = "ZERO_TARGET"
_REASON_HELD_MISSING = "HELD_RETURN_MISSING"
_REASON_OUTPUT_INVALID = "TRIAL_OUTPUT_INVALID"
_REASON_LABEL_PURGED = "EVALUATION_FOLD_LABEL_PURGED"
_CONTINUOUS = "continuous_daily_return"
_MONTHLY_RANK_IC = "monthly_rank_ic"
_EPISODE = "episode_21_row_return"
_BASELINE_TYPE = "BASELINE"
_EQUAL_WEIGHT_TRIAL = "BASELINE_EQUAL_WEIGHT_UNIVERSE"
_RANDOM_RANK_TRIAL = "BASELINE_RANDOM_RANK_TOP_DECILE"
_EQUAL_WEIGHT_ROLE = "equal_weight_universe"
_RANDOM_RANK_SCHEME = "random_rank_v1"
_INITIAL_EQUITY = 1.0
_FIRST_FOLD_YEAR = 2018
_STRATEGY_PRIMARY = "STRATEGY_PRIMARY"
_STRATEGY_STRESS = "STRATEGY_STRESS"
_STRATEGY_PREFIX = "STRATEGY_"
_ATTEMPT_SCHEMA = "campaign_attempt_state_v1"
_ATTEMPT_LEDGER_DIRNAME = "campaign_attempt_ledger_v1"
_ATTEMPT_LEDGER_ROOT = (".local", "share", "equity-factor-research")
_ATTEMPT_KEYS = frozenset(
    {
        "schema_version",
        "consumed",
        "execution_count",
        "campaign_identity_sha256",
    }
)
_PREPARED_REQUIRED = frozenset({"prices", "anchors", "listings"})
_PREPARED_FORBIDDEN = frozenset(
    {
        "trial_outputs",
        "diagnostic_payload",
        "returns",
        "factors",
        "factor",
        "portfolio",
        "cumulative",
        "bundle_children",
    }
)
_RUNNER_OWNED_CHILDREN = frozenset(
    {
        _PROTOCOL_CHILD,
        _INVENTORY_CHILD,
        _INVALID_CHILD,
        _RUN_MANIFEST_CHILD,
    }
)
_LISTING_ROW_KEYS = frozenset(
    {
        "listing_key",
        "in_universe_at_t",
        "terminal_blocked_at_t",
        "lookback_addressable_at_t",
        "target_identity",
        "alias_chain",
    }
)
_BOUND_FIELDS = (
    "runner_code_sha",
    "environment_id",
    "environment_lock_sha256",
    "calendar_id",
    "calendar_version",
    "protocol_file_sha256",
    "trial_inventory_file_sha256",
    "acceptance_record_file_sha256",
    "acceptance_identity_sha256",
    "prepared_campaign_file_sha256",
    "owner_authorization_file_sha256",
)


@dataclass(frozen=True)
class RunConfig:
    """Explicit frozen protocol and same-role digest bindings."""

    acceptance_record_file: str
    acceptance_record_file_sha256: str
    acceptance_identity_sha256: str
    decision_file_sha256: str
    decision_identity_sha256: str
    stage2_grant_file: str
    stage2_grant_file_sha256: str
    protocol_file: str
    protocol_file_sha256: str
    trial_inventory_file: str
    trial_inventory_file_sha256: str
    detached_binding_file: str
    runner_code_sha: str
    environment_id: str
    environment_lock_sha256: str
    calendar_id: str
    calendar_version: str
    prepared_campaign_file: str
    prepared_campaign_file_sha256: str
    owner_authorization_file_sha256: str
    attempt_state_file: str
    horizon_return_rows: int
    horizon_purge_signal_axis_rows: int
    embargo_rows: int
    decile_count: int
    min_eligible_count: int
    min_distinct_values: int
    common_complete_case_month_floor: int
    long_segment_block_length: int
    bootstrap_replicates: int
    random_rank_seed: int
    bootstrap_seed: int
    familywise_alpha: str
    cost_bps: tuple[int, int, int]
    bit_generator: str
    quantile_method: str

    def __post_init__(self) -> None:
        for name in (
            "acceptance_record_file",
            "stage2_grant_file",
            "protocol_file",
            "trial_inventory_file",
            "runner_code_sha",
            "environment_id",
            "calendar_id",
            "calendar_version",
            "prepared_campaign_file",
            "attempt_state_file",
            "familywise_alpha",
            "bit_generator",
            "quantile_method",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a nonempty string")
        if not isinstance(self.detached_binding_file, str):
            raise TypeError("detached_binding_file must be a string")
        for name in (
            "acceptance_record_file_sha256",
            "acceptance_identity_sha256",
            "decision_file_sha256",
            "decision_identity_sha256",
            "stage2_grant_file_sha256",
            "protocol_file_sha256",
            "trial_inventory_file_sha256",
            "environment_lock_sha256",
            "prepared_campaign_file_sha256",
            "owner_authorization_file_sha256",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
                raise ValueError(f"{name} must be a 64-hex digest")
        if _GIT_SHA_RE.fullmatch(self.runner_code_sha) is None:
            raise ValueError("runner_code_sha must be a 40-hex git object name")
        _require_int(self.horizon_return_rows, "horizon_return_rows", _HORIZON_RETURN_ROWS)
        _require_int(
            self.horizon_purge_signal_axis_rows,
            "horizon_purge_signal_axis_rows",
            _HORIZON_PURGE_ROWS,
        )
        _require_int(self.embargo_rows, "embargo_rows", _EMBARGO_ROWS)
        _require_int(self.decile_count, "decile_count", _DECILE_COUNT)
        _require_int(self.min_eligible_count, "min_eligible_count", _MIN_ELIGIBLE)
        _require_int(self.min_distinct_values, "min_distinct_values", _MIN_DISTINCT)
        _require_int(
            self.common_complete_case_month_floor,
            "common_complete_case_month_floor",
            _COMMON_MONTHS,
        )
        _require_int(
            self.long_segment_block_length,
            "long_segment_block_length",
            LONG_SEGMENT_BLOCK_LENGTH,
        )
        _require_int(
            self.bootstrap_replicates,
            "bootstrap_replicates",
            _BOOTSTRAP_REPLICATES,
        )
        _require_int(self.random_rank_seed, "random_rank_seed", _RANDOM_RANK_SEED)
        _require_int(self.bootstrap_seed, "bootstrap_seed", _BOOTSTRAP_SEED)
        if self.familywise_alpha != _FAMILYWISE_ALPHA:
            raise ValueError("familywise_alpha must equal the frozen protocol value")
        if abs(float(self.familywise_alpha) - HOLM_ALPHA) > 0.0:
            raise ValueError("familywise_alpha must equal HOLM_ALPHA")
        if tuple(self.cost_bps) != _COST_BPS:
            raise ValueError("cost_bps must equal the frozen protocol tuple")
        object.__setattr__(self, "cost_bps", tuple(self.cost_bps))
        if self.bit_generator != _BIT_GENERATOR:
            raise ValueError("bit_generator must equal the frozen protocol value")
        if self.quantile_method != _QUANTILE_METHOD:
            raise ValueError("quantile_method must equal the frozen protocol value")


@dataclass(frozen=True)
class CampaignRun:
    """Authorized diagnostic execution, or a named refusal with no outputs."""

    status: str
    reason: str | None
    authorization: Authorization
    reconciliation: ReconciliationResult | None
    bundle: BundleAssembly | None
    run_record: MappingProxyType[str, object] | None
    artifacts: MappingProxyType[str, bytes] | None


@dataclass(frozen=True)
class _ListingRow:
    listing_key: bytes
    in_universe_at_t: bool
    terminal_blocked_at_t: bool
    lookback_addressable_at_t: bool
    target_identity: MappingProxyType[str, str]
    alias_chain: tuple[MappingProxyType[str, object], ...]


@dataclass(frozen=True)
class _PreparedPanel:
    prices: MappingProxyType[bytes, MappingProxyType[str, float]]
    anchors: MappingProxyType[bytes, tuple[MappingProxyType[str, object], ...]]
    listings: MappingProxyType[str, tuple[_ListingRow, ...]]
    session_dates: tuple[str, ...]


@dataclass(frozen=True)
class _IndexedPreparedPanel(_PreparedPanel):
    anchors_by_date: Mapping[bytes, Mapping[str, Mapping[str, object]]]


@dataclass(frozen=True)
class _MonthResult:
    signal_date: str
    execution_date: str | None
    label_end_date: str | None
    value: float | None
    valid: bool
    reason: str | None
    forward_returns: tuple[tuple[str, float | None, bool], ...]


@dataclass(frozen=True)
class _ExecutionTrace:
    schedule: CampaignSchedule | None
    monthly_ics: MappingProxyType[str, tuple[_MonthResult, ...]]
    holdings: MappingProxyType[str, MappingProxyType[str, ContinuousHoldings | None]]
    panel: _PreparedPanel
    frozen: MappingProxyType[tuple[str, str], object]
    required_years: tuple[int, ...]


def configuration_projection(config: RunConfig) -> dict[str, object]:
    """Return the I-JSON configuration projection with digest roles labelled."""

    if not isinstance(config, RunConfig):
        raise TypeError("config must be RunConfig")
    return {
        "horizon_return_rows": config.horizon_return_rows,
        "horizon_purge_signal_axis_rows": config.horizon_purge_signal_axis_rows,
        "embargo_rows": config.embargo_rows,
        "decile_count": config.decile_count,
        "min_eligible_count": config.min_eligible_count,
        "min_distinct_values": config.min_distinct_values,
        "common_complete_case_month_floor": config.common_complete_case_month_floor,
        "long_segment_block_length": config.long_segment_block_length,
        "bootstrap_replicates": config.bootstrap_replicates,
        "random_rank_seed": config.random_rank_seed,
        "bootstrap_seed": config.bootstrap_seed,
        "familywise_alpha": config.familywise_alpha,
        "cost_bps": list(config.cost_bps),
        "bit_generator": config.bit_generator,
        "quantile_method": config.quantile_method,
        "calendar_id": config.calendar_id,
        "calendar_version": config.calendar_version,
        "acceptance_record_file_sha256": config.acceptance_record_file_sha256,
        "acceptance_identity_sha256": config.acceptance_identity_sha256,
        "decision_file_sha256": config.decision_file_sha256,
        "decision_identity_sha256": config.decision_identity_sha256,
        "roles": {
            "acceptance_record_file_sha256": "FILE_BYTES",
            "acceptance_identity_sha256": "CANONICAL_IDENTITY",
            "decision_file_sha256": "FILE_BYTES",
            "decision_identity_sha256": "CANONICAL_IDENTITY",
            "protocol_file_sha256": "FILE_BYTES",
            "trial_inventory_file_sha256": "FILE_BYTES",
            "environment_lock_sha256": "ENV_LOCK",
            "runner_code_sha": "GIT_COMMIT",
            "prepared_campaign_file_sha256": "FILE_BYTES",
            "owner_authorization_file_sha256": "FILE_BYTES",
        },
        "protocol_file_sha256": config.protocol_file_sha256,
        "trial_inventory_file_sha256": config.trial_inventory_file_sha256,
        "environment_lock_sha256": config.environment_lock_sha256,
        "runner_code_sha": config.runner_code_sha,
        "environment_id": config.environment_id,
        "prepared_campaign_file_sha256": config.prepared_campaign_file_sha256,
        "owner_authorization_file_sha256": config.owner_authorization_file_sha256,
    }


def run_campaign(config: RunConfig) -> CampaignRun:
    """Authorize, then execute 14 inventory trials from an input-bearing panel."""

    if not isinstance(config, RunConfig):
        raise TypeError("config must be RunConfig")
    authorization = authorize(config)
    if authorization.status != _STATUS_AUTHORIZED:
        return _refused(authorization, authorization.reason)
    grant = authorization.grant
    if grant is None:
        return _refused(authorization, "STAGE2_GRANT_ABSENT")
    reason = result_bearing_refusal_reason(grant)
    if reason is not None:
        return _refused(authorization, reason)
    prepared_raw = _read_prepared_octets(config.prepared_campaign_file)
    if prepared_raw is None:
        return _refused(authorization, _REASON_PREPARED_BYTES)
    if hashlib.sha256(prepared_raw).hexdigest() != config.prepared_campaign_file_sha256:
        return _refused(authorization, _REASON_PREPARED_BYTES)
    if _is_sentinel(prepared_raw):
        return _refused(authorization, _REASON_PREPARED_SENTINEL)
    panel = _parse_prepared_campaign(prepared_raw)
    if isinstance(panel, str):
        return _refused(authorization, panel)
    protocol_raw = _bound_file_bytes(
        config.protocol_file,
        config.protocol_file_sha256,
        _REASON_PROTOCOL,
    )
    if isinstance(protocol_raw, str):
        return _refused(authorization, protocol_raw)
    inventory_raw = _bound_file_bytes(
        config.trial_inventory_file,
        config.trial_inventory_file_sha256,
        _REASON_INVENTORY,
    )
    if isinstance(inventory_raw, str):
        return _refused(authorization, inventory_raw)
    binding = authorization.binding
    if binding is None:
        return _refused(authorization, "DETACHED_BINDING_ABSENT")
    block = grant["fourteen_trial_run_authorization"]
    assert isinstance(block, dict)
    limit = block["execution_count_limit"]
    assert isinstance(limit, int)
    consumed = _consume_attempt(limit, campaign_identity(binding))
    if isinstance(consumed, str):
        return _refused(authorization, consumed)
    executed = _execute_prepared(config, inventory_raw, panel)
    if isinstance(executed, str):
        return _refused(authorization, executed)
    inventory, reconciliation, trace = executed
    started_at = _utc_now()
    trial_ids = tuple(str(trial["trial_id"]) for trial in inventory)
    bound_fields = {name: binding[name] for name in _BOUND_FIELDS}
    projection_digest = hashlib.sha256(
        json.dumps(
            configuration_projection(config),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    finished_at = _utc_now()
    run_record = {
        "schema_version": _RUN_RECORD_SCHEMA,
        "evidence_ceiling": _EVIDENCE_CEILING,
        "trials_executed": len(trial_ids),
        "trial_ids": list(trial_ids),
        "bound_fields": bound_fields,
        "configuration_projection_sha256": projection_digest,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
    }
    children = _bundle_children(
        protocol_raw, inventory_raw, reconciliation, trace
    )
    children[_RUN_MANIFEST_CHILD] = json.dumps(
        dict(run_record),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    missing = _missing_required_children(children)
    if missing is not None:
        return _refused(authorization, missing)
    bundle = assemble_evidence_bundle(
        children,
        _root_fields(config, inventory, reconciliation, consumed),
    )
    if not bundle.valid:
        reason = bundle.reason
        if reason is None:
            reason = _REASON_BUNDLE_MISSING
        return _refused(authorization, reason)
    return CampaignRun(
        _STATUS_EXECUTED,
        None,
        authorization,
        reconciliation,
        bundle,
        MappingProxyType(run_record),
        MappingProxyType(children),
    )


def _refused(authorization: Authorization, reason: str | None) -> CampaignRun:
    return CampaignRun(
        _STATUS_REFUSED,
        reason,
        authorization,
        None,
        None,
        None,
        None,
    )


def _read_prepared_octets(locator: str) -> bytes | None:
    path = Path(locator)
    try:
        if not path.is_file():
            return None
        return path.read_bytes()
    except OSError:
        return None


def _is_sentinel(raw: bytes) -> bool:
    return raw == _SENTINEL_BODY or raw == _SENTINEL_BODY + b"\n"


def _parse_prepared_campaign(raw: bytes) -> _PreparedPanel | str:
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _REASON_PREPARED_UNPARSEABLE
    if not isinstance(parsed, dict):
        return _REASON_PREPARED_SCHEMA
    if any(key in parsed for key in _PREPARED_FORBIDDEN):
        return _REASON_PREPARED_SCHEMA
    if set(parsed) != _PREPARED_REQUIRED:
        return _REASON_PREPARED_SCHEMA
    prices = _parse_prices(parsed["prices"])
    if isinstance(prices, str):
        return prices
    anchors = _parse_anchors(parsed["anchors"], set(prices))
    if isinstance(anchors, str):
        return anchors
    listings = _parse_listings(parsed["listings"], set(prices))
    if isinstance(listings, str):
        return listings
    sessions = _session_dates(prices)
    if isinstance(sessions, str):
        return sessions
    return _PreparedPanel(prices, anchors, listings, sessions)


def _execute_prepared(
    config: RunConfig,
    inventory_raw: bytes,
    panel: _PreparedPanel,
) -> tuple[tuple[object, ...], ReconciliationResult, _ExecutionTrace] | str:
    try:
        by_listing = MappingProxyType({
            key: MappingProxyType({
                str(record.get("session_date")): record
                for record in records
                if isinstance(record.get("session_date"), str)
            })
            for key, records in panel.anchors.items()
        })
        panel = _IndexedPreparedPanel(
            panel.prices, panel.anchors, panel.listings, panel.session_dates, by_listing
        )
        inventory = parse_trial_inventory(inventory_raw)
        schedule = _campaign_schedule(config, panel)
        frozen = _freeze_panel(config, panel, schedule)
        monthly_ics = {
            factor_id: _monthly_rank_ics(config, factor_id, panel, frozen, schedule)
            for factor_id in FACTOR_ORDER
        }
        held_cache: dict[tuple[str, str], dict[bytes, object]] = {}
        trial_outputs: dict[str, dict[str, dict[str, object]]] = {}
        holdings: dict[str, MappingProxyType[str, ContinuousHoldings | None]] = {}
        for trial in inventory:
            trial_id = trial.get("trial_id")
            if not isinstance(trial_id, str) or not trial_id:
                return _REASON_PREPARED_SCHEMA
            outputs, paths = _execute_trial(
                config,
                trial,
                panel,
                frozen,
                schedule,
                monthly_ics,
                held_cache,
            )
            trial_outputs[trial_id] = outputs
            holdings[trial_id] = MappingProxyType(paths)
        trace = _ExecutionTrace(
            schedule=schedule,
            monthly_ics=MappingProxyType(monthly_ics),
            holdings=MappingProxyType(holdings),
            panel=panel,
            frozen=MappingProxyType(frozen),
            required_years=_required_years(schedule),
        )
        reconciliation = reconcile_semantic_trials(
            inventory,
            trial_outputs,
            _diagnostic_payload_from_execution(
                config, inventory, trial_outputs, frozen, trace
            ),
        )
    except (TypeError, ValueError, KeyError):
        return _REASON_PREPARED_SCHEMA
    return inventory, reconciliation, trace


def _parse_prices(
    raw: object,
) -> MappingProxyType[bytes, MappingProxyType[str, float]] | str:
    if not isinstance(raw, dict):
        return _REASON_PREPARED_SCHEMA
    prices: dict[bytes, MappingProxyType[str, float]] = {}
    for key, series in raw.items():
        listing_key = _parse_listing_key(key)
        if listing_key is None or not isinstance(series, dict):
            return _REASON_PREPARED_SCHEMA
        parsed_series: dict[str, float] = {}
        for session, price in series.items():
            if _invalid_session(session) or not _finite_price(price):
                return _REASON_PREPARED_SCHEMA
            parsed_series[str(session)] = float(price)
        prices[listing_key] = MappingProxyType(parsed_series)
    return MappingProxyType(prices)


def _parse_anchors(
    raw: object,
    known_keys: set[bytes],
) -> MappingProxyType[bytes, tuple[MappingProxyType[str, object], ...]] | str:
    if not isinstance(raw, dict):
        return _REASON_PREPARED_SCHEMA
    anchors: dict[bytes, tuple[MappingProxyType[str, object], ...]] = {}
    for key, records in raw.items():
        listing_key = _parse_listing_key(key)
        if listing_key is None or listing_key not in known_keys:
            return _REASON_PREPARED_SCHEMA
        if not isinstance(records, list):
            return _REASON_PREPARED_SCHEMA
        parsed_records: list[MappingProxyType[str, object]] = []
        for record in records:
            if not isinstance(record, dict):
                return _REASON_PREPARED_SCHEMA
            session = record.get("session_date")
            if _invalid_session(session):
                return _REASON_PREPARED_SCHEMA
            parsed_records.append(MappingProxyType(dict(record)))
        anchors[listing_key] = tuple(parsed_records)
    if set(anchors) != known_keys:
        return _REASON_PREPARED_SCHEMA
    return MappingProxyType(anchors)


def _parse_listings(
    raw: object,
    known_keys: set[bytes],
) -> MappingProxyType[str, tuple[_ListingRow, ...]] | str:
    if not isinstance(raw, dict):
        return _REASON_PREPARED_SCHEMA
    listings: dict[str, tuple[_ListingRow, ...]] = {}
    for signal_date, rows in raw.items():
        if _invalid_session(signal_date) or not isinstance(rows, list):
            return _REASON_PREPARED_SCHEMA
        parsed_rows: list[_ListingRow] = []
        seen: set[bytes] = set()
        for row in rows:
            parsed = _parse_listing_row(row, known_keys)
            if isinstance(parsed, str):
                return parsed
            if parsed.listing_key in seen:
                return _REASON_PREPARED_SCHEMA
            seen.add(parsed.listing_key)
            parsed_rows.append(parsed)
        listings[str(signal_date)] = tuple(parsed_rows)
    return MappingProxyType(listings)


def _parse_listing_row(raw: object, known_keys: set[bytes]) -> _ListingRow | str:
    if not isinstance(raw, dict) or set(raw) != _LISTING_ROW_KEYS:
        return _REASON_PREPARED_SCHEMA
    listing_key = _parse_listing_key(raw.get("listing_key"))
    if listing_key is None or listing_key not in known_keys:
        return _REASON_PREPARED_SCHEMA
    identity = raw.get("target_identity")
    alias_chain = raw.get("alias_chain")
    if not isinstance(identity, dict) or not isinstance(alias_chain, list):
        return _REASON_PREPARED_SCHEMA
    if any(not isinstance(item, dict) for item in alias_chain):
        return _REASON_PREPARED_SCHEMA
    in_universe = raw.get("in_universe_at_t")
    terminal = raw.get("terminal_blocked_at_t")
    lookback = raw.get("lookback_addressable_at_t")
    if not isinstance(in_universe, bool):
        return _REASON_PREPARED_SCHEMA
    if not isinstance(terminal, bool) or not isinstance(lookback, bool):
        return _REASON_PREPARED_SCHEMA
    parsed_identity = {
        str(key): str(value) for key, value in identity.items() if isinstance(value, str)
    }
    if len(parsed_identity) != len(identity):
        return _REASON_PREPARED_SCHEMA
    return _ListingRow(
        listing_key=listing_key,
        in_universe_at_t=in_universe,
        terminal_blocked_at_t=terminal,
        lookback_addressable_at_t=lookback,
        target_identity=MappingProxyType(parsed_identity),
        alias_chain=tuple(MappingProxyType(dict(item)) for item in alias_chain),
    )


def _session_dates(
    prices: Mapping[bytes, Mapping[str, float]],
) -> tuple[str, ...] | str:
    sessions: set[str] = set()
    for series in prices.values():
        sessions.update(series)
    if not sessions:
        return _REASON_PREPARED_SCHEMA
    ordered = tuple(sorted(sessions))
    if any(_invalid_session(session) for session in ordered):
        return _REASON_PREPARED_SCHEMA
    return ordered


def _freeze_panel(
    config: RunConfig,
    panel: _PreparedPanel,
    schedule: CampaignSchedule | None,
) -> dict[tuple[str, str], object]:
    frozen: dict[tuple[str, str], object] = {}
    for signal_date, rows in _scheduled_listing_items(panel, schedule):
        for factor_id in FACTOR_ORDER:
            listings = tuple(
                _decision_listing(panel, row, signal_date, factor_id) for row in rows
            )
            frozen[(factor_id, signal_date)] = build_frozen_decision_time(
                listings,
                factor_id,
                signal_date,
                config.min_eligible_count,
                config.min_distinct_values,
            )
    return frozen


def _decision_listing(
    panel: _PreparedPanel,
    row: _ListingRow,
    signal_date: str,
    factor_id: str,
) -> DecisionTimeListing:
    selected = _select_factor_anchors(panel, row.listing_key, signal_date, factor_id)
    referenced, lineage = ((), ()) if selected is None else selected
    return DecisionTimeListing(
        listing_key=row.listing_key,
        in_universe_at_t=row.in_universe_at_t,
        terminal_blocked_at_t=row.terminal_blocked_at_t,
        lookback_addressable_at_t=row.lookback_addressable_at_t,
        referenced_anchors=referenced,
        lineage_anchors=lineage,
        target_identity=row.target_identity,
        alias_chain=row.alias_chain,
    )


def _anchor_index(panel: _PreparedPanel, listing_key: bytes):
    if isinstance(panel, _IndexedPreparedPanel):
        return panel.anchors_by_date.get(listing_key, {})
    return {
        str(record.get("session_date")): record
        for record in panel.anchors.get(listing_key, ())
        if isinstance(record.get("session_date"), str)
    }


def _select_factor_anchors(
    panel: _PreparedPanel,
    listing_key: bytes,
    signal_date: str,
    factor_id: str,
) -> tuple[tuple[float, ...], tuple[MappingProxyType[str, object], ...]] | None:
    spec = factor_spec(factor_id)
    try:
        signal_index = panel.session_dates.index(signal_date)
    except ValueError:
        return None
    if spec.referenced_anchor_offsets is not None:
        indexes = tuple(signal_index + offset for offset in spec.referenced_anchor_offsets)
    elif spec.required_history_price_anchor_span is not None:
        start, end = spec.required_history_price_anchor_span
        indexes = tuple(range(signal_index + start, signal_index + end + 1))
    else:
        return None
    if any(index < 0 or index >= len(panel.session_dates) for index in indexes):
        return None
    dates = tuple(panel.session_dates[index] for index in indexes)
    series = panel.prices.get(listing_key)
    records = panel.anchors.get(listing_key)
    if series is None or records is None:
        return None
    by_date = _anchor_index(panel, listing_key)
    scalars: list[float] = []
    lineage: list[MappingProxyType[str, object]] = []
    for session in dates:
        if session not in series or session not in by_date:
            return None
        scalars.append(float(series[session]))
        lineage.append(by_date[session])
    return tuple(scalars), tuple(lineage)


def _execute_trial(
    config: RunConfig,
    trial: Mapping[str, object],
    panel: _PreparedPanel,
    frozen: Mapping[tuple[str, str], object],
    schedule: CampaignSchedule | None,
    monthly_ics: Mapping[str, tuple[_MonthResult, ...]],
    held_cache: dict[tuple[str, str], dict[bytes, object]],
) -> tuple[dict[str, dict[str, object]], dict[str, ContinuousHoldings | None]]:
    outputs: dict[str, dict[str, object]] = {}
    paths: dict[str, ContinuousHoldings | None] = {}
    for name in required_output_names(trial):
        record, holdings = _execute_named_output(
            config,
            trial,
            name,
            panel,
            frozen,
            schedule,
            monthly_ics,
            held_cache,
        )
        outputs[name] = record
        factor_id, _, series = name.partition(":")
        if holdings is not None and factor_id:
            paths[factor_id] = holdings
        del series
    return outputs, paths


def _execute_named_output(
    config: RunConfig,
    trial: Mapping[str, object],
    name: str,
    panel: _PreparedPanel,
    frozen: Mapping[tuple[str, str], object],
    schedule: CampaignSchedule | None,
    monthly_ics: Mapping[str, tuple[_MonthResult, ...]],
    held_cache: dict[tuple[str, str], dict[bytes, object]],
) -> tuple[dict[str, object], ContinuousHoldings | None]:
    factor_id, _, series = name.partition(":")
    if not factor_id or not series:
        return _invalid_output(_REASON_OUTPUT_INVALID), None
    try:
        if series == _MONTHLY_RANK_IC:
            return _rank_ic_from_months(monthly_ics.get(factor_id, ())), None
        if series == _EPISODE:
            return (
                _episode_output(
                    config, trial, factor_id, panel, frozen, schedule
                ),
                None,
            )
        if series == _CONTINUOUS:
            return _continuous_output(
                config, trial, factor_id, panel, frozen, schedule, held_cache
            )
    except (TypeError, ValueError, KeyError):
        return _invalid_output(_REASON_OUTPUT_INVALID), None
    return _invalid_output(_REASON_OUTPUT_INVALID), None


def _monthly_rank_ics(
    config: RunConfig,
    factor_id: str,
    panel: _PreparedPanel,
    frozen: Mapping[tuple[str, str], object],
    schedule: CampaignSchedule | None,
) -> tuple[_MonthResult, ...]:
    months: list[_MonthResult] = []
    eval_dates = _evaluation_signal_dates(schedule)
    restrict = schedule is not None
    for signal_date in _primary_era_signal_dates(panel, schedule):
        rows = panel.listings.get(signal_date, ())
        window = _execution_window(
            schedule, panel.session_dates, signal_date, config.horizon_return_rows
        )
        execution_date = None if window is None else window[0]
        label_end = None if window is None else window[1]
        if restrict and signal_date not in eval_dates:
            months.append(
                _MonthResult(
                    signal_date=signal_date,
                    execution_date=execution_date,
                    label_end_date=label_end,
                    value=None,
                    valid=False,
                    reason=_REASON_LABEL_PURGED,
                    forward_returns=(),
                )
            )
            continue
        frozen_dt = frozen.get((factor_id, signal_date))
        values = _eligible_values(frozen_dt)
        pairs: list[tuple[object, object]] = []
        forwards: list[tuple[str, float | None, bool]] = []
        for row in rows:
            factor_value = values.get(row.listing_key)
            held = (
                None
                if window is None
                else _held_return(panel, row, window[0], window[1])
            )
            ret_value = None if held is None or not held.valid else held.value
            forwards.append((row.listing_key.hex(), ret_value, held is not None and held.valid))
            if factor_value is None:
                continue
            if ret_value is None:
                pairs.append((None, None))
            else:
                pairs.append((factor_value, ret_value))
        if (
            isinstance(frozen_dt, FrozenDecisionTime)
            and frozen_dt.invalid_factor_month
        ):
            trigger = next(
                iter(frozen_dt.zero_target_triggers), _REASON_OUTPUT_INVALID
            )
            months.append(
                _MonthResult(
                    signal_date=signal_date,
                    execution_date=execution_date,
                    label_end_date=label_end,
                    value=None,
                    valid=False,
                    reason=trigger,
                    forward_returns=tuple(forwards),
                )
            )
            continue
        result = spearman_rank_ic(
            pairs,
            config.min_distinct_values,
            2,
        )
        months.append(
            _MonthResult(
                signal_date=signal_date,
                execution_date=execution_date,
                label_end_date=label_end,
                value=result.value,
                valid=result.valid,
                reason=result.reason,
                forward_returns=tuple(forwards),
            )
        )
    return tuple(months)


def _rank_ic_from_months(months: tuple[_MonthResult, ...]) -> dict[str, object]:
    scored = tuple(
        month for month in months if month.reason != _REASON_LABEL_PURGED
    )
    if not scored:
        return _invalid_output(_REASON_OUTPUT_INVALID)
    invalid = next((month for month in scored if not month.valid), None)
    if invalid is not None:
        return _from_valid(False, invalid.reason)
    return _from_valid(True, None)


def _episode_output(
    config: RunConfig,
    trial: Mapping[str, object],
    factor_id: str,
    panel: _PreparedPanel,
    frozen: Mapping[tuple[str, str], object],
    schedule: CampaignSchedule | None,
) -> dict[str, object]:
    last: dict[str, object] | None = None
    for signal_date, rows in _required_listing_items(panel, schedule):
        frozen_dt = frozen.get((factor_id, signal_date))
        weights = _trial_weights(config, trial, factor_id, frozen_dt, signal_date)
        window = _execution_window(
            schedule, panel.session_dates, signal_date, config.horizon_return_rows
        )
        constituent: dict[bytes, object] = {}
        if window is not None:
            for row in rows:
                held = _held_return(panel, row, window[0], window[1])
                constituent[row.listing_key] = (
                    None if held is None or not held.valid else held.value
                )
        result = episode_gross_return(weights, constituent)
        last = _from_valid(result.valid, result.reason)
        if not result.valid:
            return last
    if last is None:
        return _invalid_output(_REASON_ZERO_TARGET)
    return last


def _continuous_output(
    config: RunConfig,
    trial: Mapping[str, object],
    factor_id: str,
    panel: _PreparedPanel,
    frozen: Mapping[tuple[str, str], object],
    schedule: CampaignSchedule | None,
    held_cache: dict[tuple[str, str], dict[bytes, object]],
) -> tuple[dict[str, object], ContinuousHoldings | None]:
    cost = trial.get("cost_bps", 0)
    if isinstance(cost, bool) or not isinstance(cost, int):
        cost = 0
    resets: dict[str, Mapping[bytes, float]] = {}
    ordered_exec: list[str] = []
    for signal_date, _rows in _continuous_listing_items(panel, schedule):
        row = _schedule_signal(schedule, signal_date)
        if row is not None and not row.continuous_included:
            continue
        window = _execution_window(
            schedule, panel.session_dates, signal_date, config.horizon_return_rows
        )
        if window is None:
            continue
        execution_date = window[0]
        frozen_dt = frozen.get((factor_id, signal_date))
        resets[execution_date] = _trial_weights(
            config, trial, factor_id, frozen_dt, signal_date
        )
        ordered_exec.append(execution_date)
    if not ordered_exec:
        return _invalid_output(_REASON_ZERO_TARGET), None
    first_exec = ordered_exec[0]
    try:
        start = panel.session_dates.index(first_exec)
    except ValueError:
        return _invalid_output(_REASON_HELD_MISSING), None
    intervals = [
        holding_interval(first_exec, {}, resets[first_exec]),
    ]
    for index in range(start, len(panel.session_dates) - 1):
        begin = panel.session_dates[index]
        end = panel.session_dates[index + 1]
        key = (begin, end)
        if key not in held_cache:
            held_cache[key] = _held_map(panel, begin, end, schedule)
        held = held_cache[key]
        reset = resets.get(end)
        intervals.append(holding_interval(end, held, reset))
    holdings = advance_holdings(
        {},
        tuple(intervals),
        float(cost),
        _INITIAL_EQUITY,
    )
    return _from_valid(holdings.valid, holdings.reason), holdings


def _trial_weights(
    config: RunConfig,
    trial: Mapping[str, object],
    factor_id: str,
    frozen_dt: object,
    signal_date: str | None,
) -> Mapping[bytes, float]:
    if not isinstance(frozen_dt, FrozenDecisionTime) or signal_date is None:
        return {}
    trial_type = trial.get("type")
    trial_id = trial.get("trial_id")
    if trial_type == _BASELINE_TYPE and trial_id == _EQUAL_WEIGHT_TRIAL:
        return equal_weight_universe_target(frozen_dt, _EQUAL_WEIGHT_ROLE).weights
    if trial_type == _BASELINE_TYPE and trial_id == _RANDOM_RANK_TRIAL:
        return random_rank_target(
            frozen_dt,
            factor_id,
            signal_date,
            _RANDOM_RANK_SCHEME,
            str(config.random_rank_seed),
            config.bit_generator,
        ).weights
    return frozen_dt.long_only_target


def _held_map(
    panel: _PreparedPanel,
    start_date: str,
    end_date: str,
    schedule: CampaignSchedule | None,
) -> dict[bytes, object]:
    held: dict[bytes, object] = {}
    for row in _all_listing_rows(panel, schedule):
        result = _held_return(panel, row, start_date, end_date)
        held[row.listing_key] = None if not result.valid else result.value
    return held


def _all_listing_rows(
    panel: _PreparedPanel,
    schedule: CampaignSchedule | None,
) -> tuple[_ListingRow, ...]:
    seen: dict[bytes, _ListingRow] = {}
    for _signal_date, rows in _scheduled_listing_items(panel, schedule):
        for row in rows:
            seen[row.listing_key] = row
    return tuple(seen.values())


def _held_return(
    panel: _PreparedPanel,
    row: _ListingRow,
    start_date: str,
    end_date: str,
) -> SimpleReturn:
    by_date = _anchor_index(panel, row.listing_key)
    if start_date not in by_date or end_date not in by_date:
        return SimpleReturn(None, False, _REASON_HELD_MISSING)
    sessions = panel.session_dates
    if isinstance(panel, _IndexedPreparedPanel):
        sessions = sessions[bisect_left(sessions, start_date):bisect_right(sessions, end_date)]
    ordered = tuple(
        by_date[session]
        for session in sessions
        if start_date <= session <= end_date and session in by_date
    )
    start = by_date[start_date]
    end = by_date[end_date]
    return simple_adjusted_close_return(
        start.get("adjusted_close"),
        end.get("adjusted_close"),
        ordered,
        row.target_identity,
        row.alias_chain,
    )


def _campaign_schedule(
    config: RunConfig,
    panel: _PreparedPanel,
) -> CampaignSchedule | None:
    if not panel.session_dates:
        return None
    cutoff = panel.session_dates[-1]
    try:
        return build_campaign_schedule(
            panel.session_dates,
            cutoff,
            config.horizon_return_rows,
            config.horizon_purge_signal_axis_rows,
            config.embargo_rows,
            _FIRST_FOLD_YEAR,
        )
    except (TypeError, ValueError):
        return None


def _scheduled_listing_items(
    panel: _PreparedPanel,
    schedule: CampaignSchedule | None,
) -> tuple[tuple[str, tuple[_ListingRow, ...]], ...]:
    if schedule is None:
        return tuple(panel.listings.items())
    return tuple(
        (row.signal_date, panel.listings.get(row.signal_date, ()))
        for row in schedule.signals
    )


def _required_listing_items(
    panel: _PreparedPanel,
    schedule: CampaignSchedule | None,
) -> tuple[tuple[str, tuple[_ListingRow, ...]], ...]:
    items = _scheduled_listing_items(panel, schedule)
    if schedule is None:
        return items
    eval_dates = _evaluation_signal_dates(schedule)
    return tuple(
        (signal_date, rows)
        for signal_date, rows in items
        if signal_date in eval_dates
    )


def _continuous_listing_items(
    panel: _PreparedPanel,
    schedule: CampaignSchedule | None,
) -> tuple[tuple[str, tuple[_ListingRow, ...]], ...]:
    items = _scheduled_listing_items(panel, schedule)
    if schedule is None:
        return items
    floor = schedule.first_fold_year
    return tuple(
        (signal_date, rows)
        for signal_date, rows in items
        if int(signal_date[:4]) >= floor
    )


def _primary_era_signal_dates(
    panel: _PreparedPanel,
    schedule: CampaignSchedule | None,
) -> tuple[str, ...]:
    if schedule is None:
        return tuple(panel.listings)
    floor = schedule.first_fold_year
    return tuple(
        row.signal_date
        for row in schedule.signals
        if int(row.signal_date[:4]) >= floor
    )


def _schedule_signal(
    schedule: CampaignSchedule | None,
    signal_date: str,
):
    if schedule is None:
        return None
    for row in schedule.signals:
        if row.signal_date == signal_date:
            return row
    return None


def _required_years(schedule: CampaignSchedule | None) -> tuple[int, ...]:
    if schedule is None:
        return ()
    years = []
    seen: set[int] = set()
    for fold in schedule.folds:
        if not fold.signal_dates:
            continue
        year = fold.fold_year
        if year in seen:
            continue
        seen.add(year)
        years.append(year)
    return tuple(years)


def _execution_window(
    schedule: CampaignSchedule | None,
    session_dates: tuple[str, ...],
    signal_date: str,
    horizon_return_rows: int,
) -> tuple[str, str] | None:
    if schedule is not None:
        for row in schedule.signals:
            if row.signal_date != signal_date:
                continue
            if row.execution_date is None or row.label_end_date is None:
                return None
            return row.execution_date, row.label_end_date
        return None
    try:
        index = session_dates.index(signal_date)
    except ValueError:
        return None
    start = index + 1
    end = start + horizon_return_rows
    if end >= len(session_dates):
        return None
    return session_dates[start], session_dates[end]


def _eligible_values(frozen_dt: object) -> dict[bytes, float]:
    if not isinstance(frozen_dt, FrozenDecisionTime):
        return {}
    values: dict[bytes, float] = {}
    for decision in frozen_dt.retained_decisions:
        if decision.eligible and decision.factor_value is not None:
            values[decision.listing_key] = float(decision.factor_value)
    return values


def _diagnostic_payload_from_execution(
    config: RunConfig,
    inventory: tuple[object, ...],
    trial_outputs: Mapping[str, Mapping[str, Mapping[str, object]]],
    frozen: Mapping[tuple[str, str], object],
    trace: _ExecutionTrace,
) -> dict[str, object]:
    all_valid_by_factor: dict[str, dict[str, float]] = {}
    descriptive_means: list[float] = []
    for factor_id in FACTOR_ORDER:
        valid_by_date = {
            month.signal_date: float(month.value)
            for month in trace.monthly_ics.get(factor_id, ())
            if month.valid and month.value is not None
        }
        all_valid_by_factor[factor_id] = valid_by_date
        descriptive = descriptive_rank_ic(tuple(valid_by_date.values()), 1)
        descriptive_means.append(
            0.0 if descriptive.mean is None else float(descriptive.mean)
        )
    common_dates = _common_valid_months(trace.monthly_ics)
    eval_dates = _evaluation_signal_dates(trace.schedule)
    if eval_dates:
        common_dates = tuple(
            signal_date for signal_date in common_dates if signal_date in eval_dates
        )
    common_months = len(common_dates)
    means: list[float] = []
    for factor_id in FACTOR_ORDER:
        values = [
            all_valid_by_factor[factor_id][signal_date]
            for signal_date in common_dates
        ]
        means.append(sum(values) / len(values) if values else 0.0)
    p_values, bootstrap_support = _bootstrap_from_months(
        config, trace.monthly_ics, common_dates, trace.schedule
    )
    holm = holm_adjust(_as_factor_vector(p_values))
    rejections = [
        bool(getattr(holm.rejections, factor_id))
        for factor_id in FACTOR_ORDER
    ]
    active_10, invalid_primary = _active_returns(inventory, trace, 10)
    active_25, invalid_stress = _active_returns(inventory, trace, 25)
    coverage = _prefrozen_coverage(frozen, trace)
    year_frac, loyo = _robustness_from_months(
        trace.monthly_ics, common_dates, trace.required_years
    )
    strategy_valid = _required_strategy_paths_valid(inventory, trial_outputs)
    purged_months = sum(
        1
        for months in trace.monthly_ics.values()
        for month in months
        if month.reason == _REASON_LABEL_PURGED
    )
    hard_valid = (
        strategy_valid
        and invalid_primary == 0
        and invalid_stress == 0
        and coverage
    )
    return {
        "hard_valid": hard_valid,
        "prefrozen_coverage_met": coverage,
        "common_months": common_months,
        "bootstrap_support_all_three_factors": bootstrap_support,
        "primary_matched_benchmark_comparisons_valid": invalid_primary == 0,
        "secondary_spy_comparisons_valid": False,
        "mean_rank_ics": means,
        "descriptive_mean_rank_ics_all_valid_factor_months": descriptive_means,
        "holm_rejections": rejections,
        "active_return_10bps": active_10,
        "active_return_25bps": active_25,
        "common_case_positive_year_fractions": year_frac,
        "common_case_all_loyo_means_positive": loyo,
        "invalid_primary_comparison_count": invalid_primary,
        "invalid_secondary_comparison_count": 1,
        "purged_factor_month_count": purged_months,
    }


def _as_factor_vector(values: Sequence[object]) -> FactorVector[object]:
    return FactorVector(**dict(zip(FACTOR_ORDER, values, strict=True)))


def _evaluation_signal_dates(
    schedule: CampaignSchedule | None,
) -> frozenset[str]:
    if schedule is None:
        return frozenset()
    dates: list[str] = []
    for fold in schedule.folds:
        dates.extend(fold.signal_dates)
    return frozenset(dates)


def _common_valid_months(
    monthly_ics: Mapping[str, tuple[_MonthResult, ...]],
) -> tuple[str, ...]:
    dates: dict[str, int] = {}
    for factor_id in FACTOR_ORDER:
        for month in monthly_ics.get(factor_id, ()):
            if month.valid:
                dates[month.signal_date] = dates.get(month.signal_date, 0) + 1
    return tuple(
        date for date, count in dates.items() if count == len(FACTOR_ORDER)
    )


def _required_strategy_paths_valid(
    inventory: tuple[object, ...],
    trial_outputs: Mapping[str, Mapping[str, Mapping[str, object]]],
) -> bool:
    for trial in inventory:
        if not isinstance(trial, Mapping):
            continue
        trial_type = trial.get("type")
        if not isinstance(trial_type, str) or not trial_type.startswith(_STRATEGY_PREFIX):
            continue
        trial_id = trial.get("trial_id")
        if not isinstance(trial_id, str):
            return False
        outputs = trial_outputs.get(trial_id, {})
        if not outputs:
            return False
        for record in outputs.values():
            if record.get("present") is not True or record.get("valid") is not True:
                return False
    return True


def _bootstrap_from_months(
    config: RunConfig,
    monthly_ics: Mapping[str, tuple[_MonthResult, ...]],
    common_dates: tuple[str, ...],
    schedule: CampaignSchedule | None,
) -> tuple[tuple[float, float, float], bool]:
    if not common_dates:
        return (1.0, 1.0, 1.0), False
    by_factor = {
        factor_id: {
            month.signal_date: month.value
            for month in monthly_ics.get(factor_id, ())
            if month.valid and month.value is not None
        }
        for factor_id in FACTOR_ORDER
    }
    common_set = set(common_dates)
    segments: list[tuple[tuple[float, float, float], ...]] = []
    current: list[tuple[float, float, float]] = []
    prev_fold: int | None = None
    ordered = (
        tuple(row.signal_date for row in schedule.signals)
        if schedule is not None
        else common_dates
    )
    fold_of = {}
    if schedule is not None:
        for fold in schedule.folds:
            for signal_date in fold.signal_dates:
                fold_of[signal_date] = fold.fold_year
    for signal_date in ordered:
        if signal_date not in common_set:
            if current:
                segments.append(tuple(current))
                current = []
            prev_fold = None
            continue
        fold_year = fold_of.get(signal_date)
        if current and fold_year != prev_fold:
            segments.append(tuple(current))
            current = []
        current.append(
            tuple(by_factor[factor_id][signal_date] for factor_id in FACTOR_ORDER)
        )
        prev_fold = fold_year
    if current:
        segments.append(tuple(current))
    if not segments:
        return (1.0, 1.0, 1.0), False
    try:
        boot = bootstrap_mean_rank_ic(
            segments,
            bootstrap_seed=config.bootstrap_seed,
            replicates=config.bootstrap_replicates,
        )
    except (TypeError, ValueError):
        return (1.0, 1.0, 1.0), False
    p_values = tuple(
        float(getattr(boot.one_sided_p_values, factor_id))
        for factor_id in FACTOR_ORDER
    )
    return p_values, bool(boot.bootstrap_support_all_three_factors)


def _active_returns(
    inventory: tuple[object, ...],
    trace: _ExecutionTrace,
    cost_bps: int,
) -> tuple[list[float], int]:
    baseline_trial = ""
    for trial in inventory:
        if not isinstance(trial, Mapping):
            continue
        if trial.get("type") == _BASELINE_TYPE and trial.get("trial_id") == _EQUAL_WEIGHT_TRIAL:
            baseline_trial = str(trial.get("trial_id"))
    values: list[float] = []
    invalid = 0
    baseline_paths = trace.holdings.get(baseline_trial, MappingProxyType({}))
    for factor_id in FACTOR_ORDER:
        path = None
        for trial in inventory:
            if not isinstance(trial, Mapping):
                continue
            if trial.get("factor_id") != factor_id:
                continue
            if trial.get("cost_bps") != cost_bps:
                continue
            path = trace.holdings.get(str(trial.get("trial_id")), MappingProxyType({})).get(
                factor_id
            )
            break
        baseline = baseline_paths.get(factor_id)
        if path is None:
            values.append(0.0)
            continue
        if (
            not isinstance(path, ContinuousHoldings)
            or not path.valid
            or not path.points
            or path.points[-1].equity is None
        ):
            values.append(0.0)
            invalid += 1
            continue
        if (
            not isinstance(baseline, ContinuousHoldings)
            or not baseline.valid
            or not baseline.points
            or baseline.points[-1].equity is None
        ):
            values.append(0.0)
            invalid += 1
            continue
        values.append(float(path.points[-1].equity) - float(baseline.points[-1].equity))
    return values, invalid


def _prefrozen_coverage(
    frozen: Mapping[tuple[str, str], object],
    trace: _ExecutionTrace,
) -> bool:
    if not frozen:
        return False
    eval_dates = _evaluation_signal_dates(trace.schedule)
    restrict_to_primary = trace.schedule is not None
    for (factor_id, signal_date), frozen_dt in frozen.items():
        if restrict_to_primary and signal_date not in eval_dates:
            continue
        if not isinstance(frozen_dt, FrozenDecisionTime):
            return False
        horizon = (
            trace.schedule.horizon_return_rows
            if trace.schedule is not None
            else 21
        )
        window = _execution_window(
            trace.schedule,
            trace.panel.session_dates,
            signal_date,
            horizon,
        )
        if window is None:
            continue
        forwards: dict[bytes, object] = {}
        for row in trace.panel.listings.get(signal_date, ()):
            held = _held_return(trace.panel, row, window[0], window[1])
            forwards[row.listing_key] = (
                None if held is None or not held.valid else held.value
            )
        coverage = label_coverage(
            tuple(item.listing_key for item in frozen_dt.ordered_eligible),
            forwards,
        )
        if not coverage.all_eligible_labels_valid:
            return False
        del factor_id
    return True


def _robustness_from_months(
    monthly_ics: Mapping[str, tuple[_MonthResult, ...]],
    common_dates: tuple[str, ...],
    required_years: tuple[int, ...],
) -> tuple[list[float], list[bool]]:
    if not required_years:
        return [0.0, 0.0, 0.0], [False, False, False]
    records: list[CommonCaseMonth] = []
    by_date = {
        factor_id: {
            month.signal_date: month.value
            for month in monthly_ics.get(factor_id, ())
            if month.valid and month.value is not None
        }
        for factor_id in FACTOR_ORDER
    }
    for signal_date in common_dates:
        year = int(signal_date[:4])
        records.append(
            CommonCaseMonth(
                signal_year=year,
                label_intersection_years=(year,),
                rank_ics=tuple(
                    float(by_date[factor_id][signal_date]) for factor_id in FACTOR_ORDER
                ),
            )
        )
    try:
        robustness = common_case_robustness(records, required_years)
    except (TypeError, ValueError):
        return [0.0, 0.0, 0.0], [False, False, False]
    fractions = [
        float(getattr(robustness, factor_id).positive_year_fraction)
        for factor_id in FACTOR_ORDER
    ]
    loyo = [
        bool(getattr(robustness, factor_id).all_leave_one_year_out_means_positive)
        for factor_id in FACTOR_ORDER
    ]
    return fractions, loyo


def _from_valid(valid: bool, reason: str | None) -> dict[str, object]:
    if valid:
        return {"present": True, "valid": True, "reason": None}
    return {
        "present": True,
        "valid": False,
        "reason": reason or _REASON_OUTPUT_INVALID,
    }


def _invalid_output(reason: str) -> dict[str, object]:
    return {"present": True, "valid": False, "reason": reason}


def _parse_listing_key(value: object) -> bytes | None:
    if not isinstance(value, str) or len(value) < 2 or len(value) % 2:
        return None
    try:
        listing_key = bytes.fromhex(value)
    except ValueError:
        return None
    if not listing_key:
        return None
    return listing_key


def _invalid_session(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 10:
        return True
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return True
    return parsed.isoformat() != value


def _finite_price(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    numeric = float(value)
    return numeric == numeric and numeric not in {float("inf"), float("-inf")}


def campaign_identity(binding: object) -> str:
    """Return the FILE_BYTES digest of the trusted detached bound fields."""

    if not isinstance(binding, Mapping):
        raise TypeError("binding must be a mapping")
    payload = {name: binding[name] for name in _BOUND_FIELDS}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def attempt_ledger_path(identity: str) -> Path:
    """Return the durable ledger path uniquely keyed by campaign identity."""

    if not isinstance(identity, str) or _SHA256_RE.fullmatch(identity) is None:
        raise ValueError("identity must be a 64-hex digest")
    return Path.home().joinpath(
        *_ATTEMPT_LEDGER_ROOT,
        _ATTEMPT_LEDGER_DIRNAME,
        f"{identity}.json",
    )


def _bound_file_bytes(locator: str, expected: str, reason: str) -> bytes | str:
    try:
        raw = Path(locator).read_bytes()
    except OSError:
        return reason
    if hashlib.sha256(raw).hexdigest() != expected:
        return reason
    return raw


def _missing_required_children(children: Mapping[str, bytes]) -> str | None:
    names = set(children)
    for name in required_bundle_children():
        if name not in names:
            return _REASON_BUNDLE_MISSING
    return None


def _consume_attempt(limit: int, identity: str) -> str | int:
    path = attempt_ledger_path(identity)
    try:
        if not path.is_file():
            return _REASON_ATTEMPT_ABSENT
        fd = os.open(path, os.O_RDWR)
    except OSError:
        return _REASON_ATTEMPT_ABSENT
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        size = os.fstat(fd).st_size
        raw = os.read(fd, size) if size else b""
        try:
            loaded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _REASON_ATTEMPT_INVALID
        if not isinstance(loaded, dict):
            return _REASON_ATTEMPT_INVALID
        parsed = loaded
        if set(parsed) != _ATTEMPT_KEYS:
            return _REASON_ATTEMPT_INVALID
        if parsed.get("schema_version") != _ATTEMPT_SCHEMA:
            return _REASON_ATTEMPT_INVALID
        ledger_identity = parsed.get("campaign_identity_sha256")
        if not isinstance(ledger_identity, str) or ledger_identity != identity:
            return _REASON_ATTEMPT_LEDGER
        consumed = parsed.get("consumed")
        execution_count = parsed.get("execution_count")
        if not isinstance(consumed, bool):
            return _REASON_ATTEMPT_INVALID
        if isinstance(execution_count, bool) or not isinstance(execution_count, int):
            return _REASON_ATTEMPT_INVALID
        if execution_count < 0:
            return _REASON_ATTEMPT_INVALID
        if consumed == (execution_count == 0):
            return _REASON_ATTEMPT_INVALID
        if consumed or execution_count >= limit:
            return _REASON_ATTEMPT_CONSUMED
        new_count = execution_count + 1
        payload = json.dumps(
            {
                "schema_version": _ATTEMPT_SCHEMA,
                "consumed": True,
                "execution_count": new_count,
                "campaign_identity_sha256": identity,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, payload)
        os.ftruncate(fd, len(payload))
        os.fsync(fd)
    finally:
        os.close(fd)
    return new_count


def _utc_now() -> str:
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def _decile_rows(trace: _ExecutionTrace) -> list[dict[str, object]]:
    horizon = (
        trace.schedule.horizon_return_rows
        if trace.schedule is not None
        else _HORIZON_RETURN_ROWS
    )
    rows_by_key = {
        row.listing_key: row for row in _all_listing_rows(trace.panel, trace.schedule)
    }
    rows: list[dict[str, object]] = []
    for (factor_id, signal_date), frozen_dt in trace.frozen.items():
        if not isinstance(frozen_dt, FrozenDecisionTime):
            continue
        window = _execution_window(
            trace.schedule,
            trace.panel.session_dates,
            signal_date,
            horizon,
        )
        forwards: dict[bytes, object] = {}
        if window is not None:
            for ranked in frozen_dt.ordered_eligible:
                listing = rows_by_key.get(ranked.listing_key)
                if listing is None:
                    continue
                held = _held_return(trace.panel, listing, window[0], window[1])
                forwards[ranked.listing_key] = (
                    None if not held.valid else held.value
                )
        curve = decile_return_curve(
            frozen_dt.deciles,
            forwards,
            _DECILE_COUNT,
        )
        rows.append(
            {
                "factor_id": factor_id,
                "fully_monotone": curve.fully_monotone,
                "means": dict(curve.means),
                "monotonicity_share": curve.monotonicity_share,
                "reason": curve.reason,
                "signal_date": signal_date,
                "spread": curve.spread,
                "valid": curve.valid,
            }
        )
    return rows


def _bundle_children(
    protocol_raw: bytes,
    inventory_raw: bytes,
    reconciliation: ReconciliationResult,
    trace: _ExecutionTrace,
) -> dict[str, bytes]:
    monthly = []
    for factor_id, months in trace.monthly_ics.items():
        for month in months:
            monthly.append(
                {
                    "execution_date": month.execution_date,
                    "factor_id": factor_id,
                    "forward_returns": [
                        {
                            "listing_key": key,
                            "valid": valid,
                            "value": value,
                        }
                        for key, value, valid in month.forward_returns
                    ],
                    "label_end_date": month.label_end_date,
                    "reason": month.reason,
                    "signal_date": month.signal_date,
                    "valid": month.valid,
                    "value": month.value,
                }
            )
    yearly = yearly_rank_ic_contributions(
        [
            (int(month.signal_date[:4]), month.value)
            for months in trace.monthly_ics.values()
            for month in months
            if month.valid and month.value is not None
        ]
    )
    strategy_points = []
    cost_rows = []
    for trial_id, factor_paths in trace.holdings.items():
        for factor_id, holdings in factor_paths.items():
            if not isinstance(holdings, ContinuousHoldings):
                continue
            points = [
                {
                    "cost_impact": point.cost_impact,
                    "net_return": point.net_return,
                    "session_date": point.session_date,
                    "turnover": point.turnover,
                    "valid": point.valid,
                }
                for point in holdings.points
            ]
            strategy_points.append(
                {
                    "factor_id": factor_id,
                    "reason": holdings.reason,
                    "trial_id": trial_id,
                    "valid": holdings.valid,
                    "points": points,
                }
            )
            cost_rows.append(
                {
                    "cost_impact_sum": sum(
                        point.cost_impact or 0.0 for point in holdings.points
                    ),
                    "factor_id": factor_id,
                    "trial_id": trial_id,
                    "valid": holdings.valid,
                }
            )
    listing_count = len(_all_listing_rows(trace.panel, None))
    artifacts = {
        "dataset_full_manifest.json": {
            "accepted_cutoff": (
                trace.schedule.accepted_cutoff
                if trace.schedule is not None
                else trace.panel.session_dates[-1]
            ),
            "first_fold_year": (
                trace.schedule.first_fold_year
                if trace.schedule is not None
                else _FIRST_FOLD_YEAR
            ),
            "listing_count": listing_count,
            "schema_version": "campaign_dataset_full_manifest_v1",
            "session_count": len(trace.panel.session_dates),
            "signal_count": len(trace.panel.listings),
        },
        "dataset_public_projection.json": {
            "evidence_ceiling": _EVIDENCE_CEILING,
            "schema_version": "campaign_dataset_public_projection_v1",
            "signal_count": len(trace.panel.listings),
            "trial_count": 14,
        },
        "factor_diagnostics.parquet": {
            "monthly_rank_ics": monthly,
            "schema_version": "campaign_factor_diagnostics_v1",
        },
        "decile_returns.parquet": {
            "rows": _decile_rows(trace),
            "schema_version": "campaign_decile_returns_v1",
            "signal_count": len(trace.panel.listings),
        },
        "strategy_returns.parquet": {
            "schema_version": "campaign_strategy_returns_v1",
            "trials": strategy_points,
        },
        "baseline_comparison.json": {
            "invalid_primary_comparison_count": reconciliation.invalid_and_missing.get(
                "invalid_primary_comparisons", 0
            ),
            "schema_version": "campaign_baseline_comparison_v1",
        },
        "cost_sensitivity.json": {
            "schema_version": "campaign_cost_sensitivity_v1",
            "trials": cost_rows,
        },
        "yearly_robustness.json": {
            "required_years": list(trace.required_years),
            "schema_version": "campaign_yearly_robustness_v1",
            "years": [
                {
                    "contribution": row.contribution,
                    "count": row.count,
                    "mean": row.mean,
                    "year": row.year,
                }
                for row in yearly
            ],
        },
        "review_record.json": {
            "evidence_ceiling": _EVIDENCE_CEILING,
            "final_state": reconciliation.final_state,
            "schema_version": "campaign_review_record_v1",
        },
    }
    children: dict[str, bytes] = {
        name: json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        for name, payload in artifacts.items()
    }
    children[_PROTOCOL_CHILD] = protocol_raw
    children[_INVENTORY_CHILD] = inventory_raw
    children[_INVALID_CHILD] = invalid_and_missing_bytes(reconciliation)
    return children


def _root_fields(
    config: RunConfig,
    inventory: tuple[object, ...],
    reconciliation: ReconciliationResult,
    attempt_count: int,
) -> dict[str, object]:
    if reconciliation.trials:
        statuses: list[dict[str, str]] = [
            {
                "trial_id": trial.trial_id,
                "status": "EXECUTED" if trial.complete else "FAIL_CLOSED",
            }
            for trial in reconciliation.trials
        ]
    else:
        statuses = [
            {
                "trial_id": str(trial["trial_id"]),
                "status": "UNRECONCILED",
            }
            for trial in inventory
            if isinstance(trial, dict)
        ]
    final_state = reconciliation.final_state
    return {
        "runner_code_sha": config.runner_code_sha,
        "environment_id": config.environment_id,
        "environment_lock_sha256": config.environment_lock_sha256,
        "protocol_file_sha256": config.protocol_file_sha256,
        "trial_inventory_file_sha256": config.trial_inventory_file_sha256,
        "acceptance_record_file_sha256": config.acceptance_record_file_sha256,
        "acceptance_identity_sha256": config.acceptance_identity_sha256,
        "semantic_trial_count": len(inventory),
        "attempt_count": attempt_count,
        "per_trial_status": statuses,
        "final_state": "" if final_state is None else str(final_state),
    }


def _require_int(value: object, name: str, expected: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value != expected:
        raise ValueError(f"{name} must equal the frozen protocol value")


__all__ = [
    "CampaignRun",
    "RunConfig",
    "attempt_ledger_path",
    "campaign_identity",
    "configuration_projection",
    "run_campaign",
]
