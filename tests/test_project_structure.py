from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
from importlib import resources
import json
import math
from numbers import Real
from pathlib import Path
import re
import runpy
import tomllib
import unicodedata

import numpy as np

from campaign.classifier import DiagnosticInputs, classify_diagnostic
from campaign.deciles import top_decile_count
from campaign.inference import FactorVector
from campaign.listing_key import (
    encode_listing_lineage_key_v1 as _listing_lineage_key_bytes_v1,
)
from campaign.turnover import factor_target_turnover as _factor_target_turnover


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _markdown_section(text: str, heading: str) -> str:
    """Return one level-two Markdown section without matching later sections."""
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^##\s|\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one level-two section {heading!r}, found {len(matches)}"
        )
    return matches[0]


def _factor_anchor_lineage_v1_is_valid(
    anchors: list[dict[str, object]],
    target_identity: dict[str, str],
    alias_chain: list[dict[str, object]],
) -> bool:
    identity_fields = (
        "resolved_permanent_security_id",
        "resolved_listing_id",
        "resolved_listing_episode_id",
    )
    accepted_rename = (
        "ACCEPTED_SYMBOL_RENAME_SAME_PERMANENT_SECURITY_"
        "SAME_LISTING_AND_LISTING_EPISODE"
    )
    if not anchors or not alias_chain or any(
        not target_identity.get(field) for field in identity_fields
    ):
        return False

    parsed_chain: list[tuple[date, date | None, dict[str, object]]] = []
    for alias in alias_chain:
        try:
            effective_from = date.fromisoformat(str(alias["alias_effective_from"]))
            effective_to_raw = alias.get("alias_effective_to")
            effective_to = (
                None
                if effective_to_raw is None
                else date.fromisoformat(str(effective_to_raw))
            )
        except (KeyError, TypeError, ValueError):
            return False
        if effective_to is not None and effective_to <= effective_from:
            return False
        if any(
            alias.get(field) != target_identity[field]
            for field in identity_fields
        ):
            return False
        for required_text in (
            "source_exchange",
            "source_ticker",
            "lineage_resolution_evidence_id",
        ):
            if (
                not isinstance(alias.get(required_text), str)
                or not alias[required_text]
            ):
                return False
        parsed_chain.append((effective_from, effective_to, alias))

    for index, (effective_from, effective_to, alias) in enumerate(parsed_chain):
        if index == len(parsed_chain) - 1:
            if alias.get("transition_to_next") != "TARGET_ALIAS":
                return False
            continue
        next_effective_from = parsed_chain[index + 1][0]
        if (
            effective_to != next_effective_from
            or alias.get("transition_to_next") != accepted_rename
            or next_effective_from <= effective_from
        ):
            return False

    for anchor in anchors:
        if any(
            anchor.get(field) != target_identity[field]
            for field in identity_fields
        ):
            return False
        try:
            session = date.fromisoformat(str(anchor["session_date"]))
        except (KeyError, TypeError, ValueError):
            return False
        matching_aliases = [
            alias
            for effective_from, effective_to, alias in parsed_chain
            if anchor.get("source_exchange") == alias["source_exchange"]
            and anchor.get("source_ticker") == alias["source_ticker"]
            and anchor.get("alias_effective_from") == alias["alias_effective_from"]
            and anchor.get("alias_effective_to") == alias["alias_effective_to"]
            and anchor.get("lineage_resolution_evidence_id")
            == alias["lineage_resolution_evidence_id"]
            and session >= effective_from
            and (effective_to is None or session < effective_to)
        ]
        if len(matching_aliases) != 1:
            return False
    return True


def _decision_time_objects(
    records: list[dict[str, object]],
) -> tuple[
    tuple[tuple[bytes, float], ...],
    tuple[tuple[bytes, float], ...],
    float,
]:
    eligible = [
        record
        for record in records
        if record["membership_known_at_t"]
        and record["lineage_resolved_through_t"]
        and record[
            "factor_specific_lookback_position_span_addressable_at_t"
        ]
        and record["factor_specific_required_price_anchors_valid_at_t"]
        and record["factor_anchor_lineage_v1_valid_at_t"]
        and record["corporate_action_policy_known_at_t"]
        and math.isfinite(float(record["factor_value_at_t"]))
    ]
    ordered = sorted(
        eligible,
        key=lambda record: (
            -float(record["factor_value_at_t"]),
            bytes(record["listing_key_bytes"]),
        ),
    )
    listing_keys = [
        bytes(record["listing_key_bytes"]) for record in ordered
    ]
    distinct_factor_values = {
        float(record["factor_value_at_t"]) for record in ordered
    }
    invalid_rebalance = (
        len(ordered) < 100
        or len(distinct_factor_values) < 10
        or len(set(listing_keys)) != len(listing_keys)
    )
    if invalid_rebalance:
        target: tuple[tuple[bytes, float], ...] = ()
    else:
        base, remainder = divmod(len(ordered), 10)
        top_count = base + (1 if remainder else 0)
        target = tuple(
            (bytes(record["listing_key_bytes"]), 1.0 / top_count)
            for record in ordered[:top_count]
        )
    benchmark = tuple(
        sorted(
            (
                (bytes(record["listing_key_bytes"]), 1.0 / len(ordered))
                for record in ordered
            ),
            key=lambda item: item[0],
        )
    ) if ordered else ()
    cash_weight = 1.0 if invalid_rebalance else 0.0
    return target, benchmark, cash_weight


def _classify_diagnostic(
    *,
    hard_valid: bool,
    prefrozen_coverage_met: bool,
    common_months: int,
    bootstrap_support_all_three_factors: bool,
    primary_matched_benchmark_comparisons_valid: bool,
    secondary_spy_comparisons_valid: bool,
    mean_rank_ics: tuple[float, float, float],
    holm_rejections: tuple[bool, bool, bool],
    active_return_10bps: tuple[float, float, float],
    active_return_25bps: tuple[float, float, float],
    common_case_positive_year_fractions: tuple[float, float, float],
    common_case_all_loyo_means_positive: tuple[bool, bool, bool],
) -> str:
    return classify_diagnostic(
        DiagnosticInputs(
            hard_valid=hard_valid,
            prefrozen_coverage_met=prefrozen_coverage_met,
            common_months=common_months,
            bootstrap_support_all_three_factors=(
                bootstrap_support_all_three_factors
            ),
            primary_matched_benchmark_comparisons_valid=(
                primary_matched_benchmark_comparisons_valid
            ),
            secondary_spy_comparisons_valid=secondary_spy_comparisons_valid,
            mean_rank_ics=FactorVector(*mean_rank_ics),
            holm_rejections=FactorVector(*holm_rejections),
            active_return_10bps=FactorVector(*active_return_10bps),
            active_return_25bps=FactorVector(*active_return_25bps),
            common_case_positive_year_fractions=FactorVector(
                *common_case_positive_year_fractions
            ),
            common_case_all_loyo_means_positive=FactorVector(
                *common_case_all_loyo_means_positive
            ),
        )
    )


def test_required_directories_exist() -> None:
    required_directories = [
        "src/data",
        "src/features",
        "src/strategies",
        "src/backtest",
        "src/risk",
        "src/reporting",
        "src/ledger",
        "src/utils",
        "tests",
        "research",
        "reports",
    ]

    for directory in required_directories:
        assert (PROJECT_ROOT / directory).is_dir(), f"Missing directory: {directory}"


def test_required_governance_files_exist() -> None:
    required_files = [
        "README.md",
        "PROJECT_SPEC.md",
        "AGENTS.md",
        "EXPERIMENT_LOG.md",
        "pyproject.toml",
        "docs/research_program_charter.md",
        "docs/purged_bounded_split_contract.md",
        "docs/signal_execution_timing_contract.md",
        "docs/point_in_time_data_methodology_contract.md",
        "docs/experiment_trial_ledger_contract.md",
        "docs/experiment_trial_ledger_schema_registry_contract.md",
        "docs/experiment_trial_ledger_allocation_registration_schema_contract.md",
        "docs/experiment_trial_ledger_trial_family_registration_schema_contract.md",
        "docs/experiment_trial_ledger_sample_registration_schema_contract.md",
        "docs/experiment_trial_ledger_binding_schema_contract.md",
        "docs/experiment_trial_ledger_trial_allocation_schema_contract.md",
        "docs/experiment_trial_ledger_campaign_inventory_seal_schema_contract.md",
        "docs/experiment_trial_ledger_attempt_allocation_schema_contract.md",
        "docs/experiment_trial_ledger_attempt_start_schema_contract.md",
        "docs/eodhd_sp500_diagnostic_campaign_contract.md",
        "docs/preregistrations/eodhd_sp500_three_factor_diagnostic_v1.yaml",
        "docs/preregistrations/eodhd_sp500_three_factor_trial_inventory_v1.json",
        "docs/current_roadmap.md",
        "docs/current_handoff.md",
    ]

    for file_name in required_files:
        assert (PROJECT_ROOT / file_name).is_file(), f"Missing file: {file_name}"


def test_governance_documents_define_unique_policy_owners() -> None:
    documents = {
        "agents": (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
        "controller": (
            PROJECT_ROOT / "docs/codex_long_running_controller.md"
        ).read_text(encoding="utf-8"),
        "roadmap": (PROJECT_ROOT / "docs/current_roadmap.md").read_text(
            encoding="utf-8"
        ),
        "handoff": (PROJECT_ROOT / "docs/current_handoff.md").read_text(
            encoding="utf-8"
        ),
        "charter": (
            PROJECT_ROOT / "docs/research_program_charter.md"
        ).read_text(encoding="utf-8"),
    }

    owners = {
        "agents": (
            "Canonical responsibility: repository invariants, authority boundaries, "
            "research-safety review standards, writing-style rules, and ablation after "
            "completed design or implementation."
        ),
        "controller": (
            "Canonical responsibility: staged workflow state transitions, external "
            "gates, GitHub review lifecycle, waiting, stop conditions, and "
            "completion reporting."
        ),
        "handoff": (
            "Canonical responsibility: the latest recorded operational checkpoint, "
            "exact last-verified repository and PR facts, immediate blockers or "
            "owner decisions, and the next safe action."
        ),
        "roadmap": (
            "Canonical responsibility: program stage sequence, dependency order, "
            "gate and completion criteria, and coarse stage status."
        ),
    }
    normalized = {name: " ".join(text.split()) for name, text in documents.items()}

    for owner, marker in owners.items():
        assert marker in normalized[owner]
        for other_name, other_text in normalized.items():
            if other_name != owner:
                assert marker not in other_text

    exclusive_sections = {
        "agents": [
            "Authority And Scope",
            "Writing Style And Syntax",
            "Ablation",
        ],
        "controller": [
            "External Authorization Gate",
            "Predecessor PR Gate",
            "GitHub Review Lifecycle",
            "Waiting And Follow-Up",
            "Protected Merge Eligibility",
        ],
        "roadmap": [
            "Program Position",
            "Active Dependency Chain",
            "Gate Completion Criteria",
            "Deferred And Out Of Scope",
        ],
        "handoff": [
            "Resume Order",
            "Latest Recorded Operational Checkpoint",
            "Immediate Blockers Or Owner Decisions",
            "Next Safe Action",
            "Source Routing",
        ],
    }
    for owner, headings in exclusive_sections.items():
        for heading in headings:
            marker = f"## {heading}"
            assert marker in documents[owner]
            for other_name, other_text in documents.items():
                if other_name != owner:
                    assert marker not in other_text

    for controller_only_token in [
        "explicit merged/resume/inspect request",
        "report one gate summary",
        "re-query an unchanged gate",
        "final stable current head",
        "technically merge-eligible",
        "perform the normal protected PR merge without another prompt",
    ]:
        assert controller_only_token in normalized["controller"]
        assert all(
            controller_only_token not in text
            for name, text in normalized.items()
            if name != "controller"
        )

    assert "docs/codex_long_running_controller.md" in documents["agents"]
    assert "../AGENTS.md#authority-and-scope" in documents["controller"]
    assert "codex_long_running_controller.md" in documents["roadmap"]
    assert "../AGENTS.md" in documents["roadmap"]
    authority = " ".join(
        _markdown_section(documents["agents"], "Authority And Scope").split()
    )
    controller_scope = " ".join(
        _markdown_section(documents["controller"], "Scope And Authority").split()
    )
    authorization_gate = " ".join(
        _markdown_section(
            documents["controller"], "External Authorization Gate"
        ).split()
    )

    assert "No repository file grants authority to" in authority
    assert "explicit user or higher-level authorization" in authority
    assert "create or publish a PR" in authority
    assert "normal protected lifecycle for that same PR" in authority
    assert "The user may revoke that lifecycle authorization" in authority
    assert "Lifecycle authorization never covers another PR" in authority

    for authorized_lifecycle_action in [
        "readiness transition",
        "required review request",
        "in-scope remediation publication",
        "verified review-thread reply and resolution",
        "eligible normal merge",
    ]:
        assert authorized_lifecycle_action in authority

    for excluded_lifecycle_scope in [
        "another PR",
        "scope expansion",
        "auto-merge",
        "administrative or protection bypass",
        "deployment",
        "private data",
        "credentials",
        "brokerage",
        "destructive action",
    ]:
        assert excluded_lifecycle_scope in authority

    assert "../AGENTS.md#authority-and-scope" in controller_scope
    assert "Authority remains in" in controller_scope
    assert "Eligibility is not authorization" in controller_scope

    assert "../AGENTS.md#authority-and-scope" in authorization_gate
    assert "explicit action-and-scope authorization" in authorization_gate
    assert "successful checks do not grant authority" in authorization_gate
    assert "stop after local validation" in authorization_gate
    assert "same-PR lifecycle authorization defined in `AGENTS.md`" in (
        authorization_gate
    )
    assert "apply the lifecycle below to that PR" in authorization_gate
    assert "re-enter this gate" in authorization_gate

    for duplicated_lifecycle_action in [
        "publish it",
        "transition it to Ready",
        "request required review",
        "perform the normal protected merge",
    ]:
        assert duplicated_lifecycle_action not in authorization_gate

    for duplicated_inventory in [
        "pushes, PR writes, comments",
        "Before any push, PR create/update",
    ]:
        assert duplicated_inventory not in documents["controller"]

    assert "## Current Authorization" not in documents["charter"]
    assert "## Current Research Scope Boundary" in documents["charter"]
    assert "../AGENTS.md#authority-and-scope" in documents["charter"]
    assert "defines staged execution and gates" in documents["charter"]
    assert "current_handoff.md` is the operational entry point" not in documents[
        "charter"
    ]
    assert (
        "codex_long_running_controller.md#github-review-lifecycle"
        in documents["charter"]
    )

    for stale_grant in [
        "may enable github auto-merge",
        "may automatically push",
        "thread-scoped monitor at five-minute",
        "thirty-minute intervals",
    ]:
        assert all(stale_grant not in text.lower() for text in documents.values())

    for misplaced_policy in [
        "@codex review",
        "five-minute",
        "thirty-minute",
        "auto-merge",
        "## Review and Change Policy",
    ]:
        assert misplaced_policy not in documents["roadmap"]


def test_active_handoff_is_bounded_and_rejects_obsolete_narratives() -> None:
    handoff = (PROJECT_ROOT / "docs/current_handoff.md").read_text(encoding="utf-8")
    handoff_lines = handoff.splitlines()
    normalized_handoff = " ".join(handoff.lower().split())

    assert 60 <= len(handoff_lines) <= 120
    assert len(handoff.encode("utf-8")) <= 12_000
    assert max(map(len, handoff_lines)) <= 120
    assert re.search(r"^Updated: \d{4}-\d{2}-\d{2}\b", handoff, re.MULTILINE)

    for section in [
        "Resume Order",
        "Latest Recorded Operational Checkpoint",
        "Recorded Delivery Scope",
        "Current Research Gate Summary",
        "Immediate Blockers Or Owner Decisions",
        "Next Safe Action",
        "Source Routing",
    ]:
        assert _markdown_section(handoff, section).strip()

    checkpoint = _markdown_section(handoff, "Latest Recorded Operational Checkpoint")
    checkpoint_bullets = re.findall(r"(?ms)^- (.*?)(?=^- |\Z)", checkpoint)
    baseline_bullets = [
        bullet
        for bullet in checkpoint_bullets
        if bullet.startswith("Last externally verified protected baseline")
    ]
    assert len(baseline_bullets) == 1
    assert re.search(r"`[0-9a-f]{40}`", baseline_bullets[0])
    assert "cached evidence" in handoff
    assert "must be checked separately" in checkpoint
    pr_148_bullets = [
        bullet for bullet in checkpoint_bullets if "pr #148" in bullet.lower()
    ]
    if pr_148_bullets:
        assert all("closed without merge" in bullet.lower() for bullet in pr_148_bullets)

    for obsolete_active_narrative in [
        "current protected `origin/main`: `6386c59`",
        "pr #177 is the current open scope-reset gate",
        "complete pr 1 scope and campaign reset",
        "codex/eodhd-diagnostic-scope-reset",
        "pr #148 remains open",
        "pr #148 is open",
        "pr #148 is not closed",
        "independent draft governance pr",
        "is still neither a predecessor",
        "authorized for merge/close",
        "until compaction",
        "supersession notice",
        "historical body",
    ]:
        assert obsolete_active_narrative not in normalized_handoff

    paragraphs = [
        " ".join(paragraph.lower().split())
        for paragraph in re.split(r"\n\s*\n", handoff)
    ]
    stale_pr_state = re.compile(
        r"\b(?:remains|is|currently|still)\s+(?:the\s+)?(?:current\s+)?open\b"
        r"|\bnot merged\b"
        r"|\bunmerged\b(?!\s+closure\b)"
        r"|\bis next\b"
        r"|\b(?:is|remains)\s+(?:the\s+)?current\b.{0,40}\bgate\b"
    )
    pr_reference = re.compile(r"\bpr #\d+\b")

    def has_stale_pr_state(paragraph: str) -> bool:
        normalized = " ".join(paragraph.lower().split())
        return bool(pr_reference.search(normalized) and stale_pr_state.search(normalized))

    for paragraph in paragraphs:
        assert not has_stale_pr_state(paragraph)

    assert has_stale_pr_state("PR #987654 remains the current open gate.")


def test_cca1_correction_checkpoint_is_consistent_across_active_sources() -> None:
    baseline = "c178d16d84a455774bcde73f21a9e3ff39ea7b2c"
    active_sources = [
        (PROJECT_ROOT / "docs/current_roadmap.md").read_text(encoding="utf-8"),
        (PROJECT_ROOT / "docs/current_handoff.md").read_text(encoding="utf-8"),
    ]

    for source in active_sources:
        normalized = " ".join(source.lower().split())
        assert baseline in source
        assert re.search(r"pr #180.{0,80}\b(?:is|are) merged\b", normalized)
        assert re.search(r"pr #181.{0,80}\b(?:is|are) merged\b", normalized)
        assert "no pull request was open at the verified start" in normalized


def test_historical_eodhd_checkpoints_declare_status_and_provenance() -> None:
    historical_paths = [
        "docs/eodhd_local_csv_validation_handoff.md",
        "docs/eodhd_data_quality_diagnostics_checkpoint.md",
        "docs/eodhd_factor_diagnostics_dry_run_checkpoint.md",
    ]

    for relative_path in historical_paths:
        document = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
        assert document.count("## Status: Historical") == 1
        status = " ".join(
            _markdown_section(document, "Status: Historical").lower().split()
        )
        for provenance_phrase in [
            "referenced private summaries",
            "without a tracked producer",
            "private-side tooling",
            "not retained in the public repository",
        ]:
            assert provenance_phrase in status


def test_roadmap_bounds_parallel_protocol_core_and_records_pr3_acceptance() -> None:
    roadmap = (PROJECT_ROOT / "docs/current_roadmap.md").read_text(encoding="utf-8")
    parallel_lane_source = _markdown_section(
        roadmap, "Parallel Dataset-Independent Protocol-Core Lane"
    )
    parallel_lane = " ".join(parallel_lane_source.lower().split())

    assert "only when all three conditions hold" in parallel_lane
    for eligibility_phrase in [
        "exact computation is already frozen",
        "committed golden fixture exists",
        "no dataset-specific input or result access",
    ]:
        assert eligibility_phrase in parallel_lane

    later_marker = "Later stages own:"
    assert parallel_lane_source.count(later_marker) == 1
    later_source = parallel_lane_source.split(later_marker, maxsplit=1)[1]
    later_source = later_source.split("## ", maxsplit=1)[0]
    later_scopes = [
        " ".join(bullet.lower().split()).rstrip(";.")
        for bullet in re.findall(r"(?ms)^- (.*?)(?=^- |\Z)", later_source)
    ]
    assert later_scopes == [
        "ingestion",
        "security-master construction",
        "historical membership",
        "alias lineage",
        "terminal/delisting-return semantics",
        "decision-time eligibility",
        "benchmark-membership construction",
        "runner orchestration",
        "private-data access",
        "result-bearing execution",
    ]

    assert "neither track a pr 2 nor track a pr 3" in parallel_lane
    assert "exclusive ownership of starting, satisfying, and unblocking" in (
        parallel_lane
    )
    assert "frozen golden-backed protocol-core modules" in parallel_lane

    acceptance = _markdown_section(
        roadmap, "Binding Track A PR 3 Acceptance Criteria"
    )
    acceptance_bullets = [
        " ".join(bullet.lower().split())
        for bullet in re.findall(r"(?ms)^- (.*?)(?=^- |\Z)", acceptance)
    ]
    assert len(acceptance_bullets) == 4

    def one_bullet_contains(*phrases: str) -> bool:
        return any(
            all(phrase.lower() in bullet for phrase in phrases)
            for bullet in acceptance_bullets
        )

    assert one_bullet_contains(
        "committed golden fixtures execute against shippable runner code",
        "rather than test-local closures",
    )
    assert one_bullet_contains(
        "each frozen factor id maps to exactly one explicit implementation",
        "validated by its golden and anchor-mutation fixtures",
    )
    assert one_bullet_contains(
        "generic helper defaults never define campaign semantics"
    )
    assert one_bullet_contains(
        "factor-matched equal-weight benchmark is canonical and strict",
        "uses no fill, interpolation, or survivor renormalization",
        "invalid comparisons are retained and routed under the frozen contract",
    )


def test_active_governance_sources_define_permanent_resume_routing() -> None:
    agents = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    workflow_skill = (
        PROJECT_ROOT / ".agents/skills/staged-quant-workflow/SKILL.md"
    ).read_text(encoding="utf-8")
    roadmap = (PROJECT_ROOT / "docs/current_roadmap.md").read_text(
        encoding="utf-8"
    )
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs/current_handoff.md").read_text(encoding="utf-8")
    historical_roadmap = (
        PROJECT_ROOT / "docs/current_roadmap_gap_refresh.md"
    ).read_text(encoding="utf-8")
    controller = (
        PROJECT_ROOT / "docs/codex_long_running_controller.md"
    ).read_text(encoding="utf-8")
    charter = (PROJECT_ROOT / "docs/research_program_charter.md").read_text(
        encoding="utf-8"
    )

    handoff_responsibility = (
        "Canonical responsibility: the latest recorded operational checkpoint, "
        "exact last-verified repository and PR facts, immediate blockers or owner "
        "decisions, and the next safe action."
    )
    roadmap_responsibility = (
        "Canonical responsibility: program stage sequence, dependency order, "
        "gate and completion criteria, and coarse stage status."
    )
    assert "This is the canonical roadmap" in roadmap
    assert roadmap_responsibility in " ".join(roadmap.split())
    assert handoff_responsibility in " ".join(handoff.split())
    for roadmap_section in [
        "Program Position",
        "Active Dependency Chain",
        "Gate Completion Criteria",
    ]:
        assert _markdown_section(roadmap, roadmap_section).strip()

    gate_summary = _markdown_section(handoff, "Current Research Gate Summary")
    assert "docs/current_roadmap.md" in gate_summary
    assert "- " not in gate_summary
    handoff_blockers = set(
        re.findall(
            r"^- (.+)$",
            _markdown_section(handoff, "Immediate Blockers Or Owner Decisions"),
            re.MULTILINE,
        )
    )
    roadmap_gate = _markdown_section(roadmap, "Gate Completion Criteria")
    roadmap_gate_bullets = set(
        re.findall(
            r"^- (.+)$",
            roadmap_gate,
            re.MULTILINE,
        )
    )
    assert handoff_blockers
    assert not roadmap_gate_bullets
    normalized_handoff_blockers = {
        " ".join(blocker.lower().split()) for blocker in handoff_blockers
    }

    def has_copied_blocker(text: str) -> bool:
        normalized = " ".join(text.lower().split())
        return any(blocker in normalized for blocker in normalized_handoff_blockers)

    assert not has_copied_blocker(roadmap_gate)
    copied_blocker_mutation = roadmap_gate + "\n" + next(
        iter(normalized_handoff_blockers)
    )
    assert has_copied_blocker(copied_blocker_mutation)

    source_routing = _markdown_section(handoff, "Source Routing")
    for evidence_reference in [
        "AGENTS.md",
        "docs/codex_long_running_controller.md",
        "docs/current_roadmap.md",
        "docs/research_program_charter.md",
        "docs/eodhd_sp500_diagnostic_campaign_contract.md",
        "docs/decision_log.md",
        "docs/engineering_log.md",
        "docs/troubleshooting_log.md",
    ]:
        assert evidence_reference in source_routing

    expected_resume_order = [
        "AGENTS.md",
        "docs/current_handoff.md",
        "docs/codex_long_running_controller.md",
        "docs/current_roadmap.md",
    ]
    for startup in [
        _markdown_section(agents, "Startup And Sources"),
        _markdown_section(controller, "Startup And Freshness"),
        _markdown_section(handoff, "Resume Order"),
        workflow_skill,
    ]:
        positions = [startup.index(path) for path in expected_resume_order]
        assert positions == sorted(positions)

    normalized_repo_map = " ".join(repo_map.split())
    assert "timestamped checkpoint, blockers, and next safe action" in normalized_repo_map
    assert (
        "Read `docs/current_handoff.md` for the recorded checkpoint, then the "
        "controller and `docs/current_roadmap.md`; verify remote facts live"
        in normalized_repo_map
    )
    assert "owns the latest recorded operational checkpoint" in controller
    assert "owns program stage sequence" in controller
    completion_report = " ".join(
        _markdown_section(controller, "Completion Report").split()
    )
    assert "owners named in" in completion_report
    assert "Select And Bound The Stage" in completion_report
    assert "This Skill routes to the canonical documents above" in workflow_skill
    assert "through a thin routing Skill" in agents

    next_action = " ".join(_markdown_section(handoff, "Next Safe Action").split())
    for duplicated_workflow_inventory in [
        "@codex review",
        "exact-head CI",
        "review, and separately authorized protected-merge gate",
        "Do not purchase access",
    ]:
        assert duplicated_workflow_inventory not in next_action

    normalized_roadmap = " ".join(roadmap.lower().split())
    for forbidden_roadmap_snapshot in [
        "origin/main",
        "branch head",
        "ci run",
        "latest verified snapshot",
    ]:
        assert forbidden_roadmap_snapshot not in normalized_roadmap

    active_sources = [agents, controller, roadmap, handoff, charter, repo_map]
    for transitional_wording in [
        "until compaction",
        "historical body",
        "supersession notice",
        "sole latest verified snapshot",
    ]:
        assert all(
            transitional_wording not in source.lower() for source in active_sources
        )

    assert "## Status: Historical" in historical_roadmap
    assert "must not be used as the current task queue" in historical_roadmap


def test_controller_predecessor_gate_is_single_check_and_single_report() -> None:
    controller = (
        PROJECT_ROOT / "docs/codex_long_running_controller.md"
    ).read_text(encoding="utf-8")
    predecessor_gate = " ".join(
        _markdown_section(controller, "Predecessor PR Gate").split()
    )

    for phrase in [
        "check once",
        "report one gate summary",
        "re-query an unchanged gate",
        "explicit merged/resume/inspect request",
    ]:
        assert phrase in predecessor_gate


def test_risk_evaluation_design_defines_staged_metrics() -> None:
    design = (
        PROJECT_ROOT / "docs/risk_evaluation_metrics_design.md"
    ).read_text(encoding="utf-8")
    for phrase in [
        "## Stage 1: Holdings-State Metrics",
        "average_holding_count",
        "average_position_concentration_hhi",
        "max_position_concentration_hhi",
        "## Stage 2: Tracking Error",
        "## Formerly Deferred Metrics",
        "## PR Sequence",
    ]:
        assert phrase in design


def test_eodhd_diagnostic_campaign_freezes_protocol_and_trial_inventory() -> None:
    contract_path = PROJECT_ROOT / "docs/eodhd_sp500_diagnostic_campaign_contract.md"
    preregistration_path = (
        PROJECT_ROOT
        / "docs/preregistrations/eodhd_sp500_three_factor_diagnostic_v1.yaml"
    )
    inventory_path = (
        PROJECT_ROOT
        / "docs/preregistrations/"
        "eodhd_sp500_three_factor_trial_inventory_v1.json"
    )
    controller = (
        PROJECT_ROOT / "docs/codex_long_running_controller.md"
    ).read_text(encoding="utf-8")
    contract = contract_path.read_text(encoding="utf-8")
    preregistration = preregistration_path.read_text(encoding="utf-8")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    assert "docs/eodhd_sp500_diagnostic_campaign_contract.md" in controller

    for phrase in [
        "Track A - diagnostic research now",
        "Track B - formal evidence infrastructure",
        "`full_ledger_profile_v1`",
        "`MOM_12_1`",
        "`REV_1M`",
        "`LOW_VOL_3M`",
        "The immutable semantic-trial count is 14",
        "`DIAGNOSTIC_ONLY`",
        "must not embed a hash of itself",
        "written permission",
        "no more than 14 exact wire event types",
        "Mutating any post-`t` availability",
        "`listing_lineage_key_bytes_v1`",
        "all-in fixed-bps diagnostic execution-cost",
        "ordered, mutually exclusive, exhaustive decision",
        "exact byte-for-byte copy",
        "No other condition produces a zero target",
        "Every yearly and leave-one-year-out Rank IC value",
        "required `trial_inventory.json` child",
        "For every later scheduled month",
        "scheduled frozen decision-time target",
        "make turnover skip back to the last outcome-valid month",
        "required factor-matched primary-",
        "benchmark comparison is a hard-validity failure",
        "SPY is descriptive",
        "gross_multiplier * turnover * bps / 10000",
        "random-rank baseline's continuous path is net",
        "beginning-period cost impact",
        "strict signal date `t`, not the later execution date",
        "Select exactly the first such number of",
        "The golden test freezes the complete 103-index permutation",
        "mathematical index `k` is explicitly one-based",
        "adjusted values mapped back to factor order",
        "one-day **simple** adjusted-close returns",
        "a log return is forbidden",
        "value for that listing/signal date is retained as invalid/missing",
        "diagnostic forward return is the **simple** adjusted-close return",
        "reuse that exact row-index vector jointly",
        "There is one RNG pass per",
        "Every adjusted-close anchor referenced by `MOM_12_1` or `REV_1M`",
        "to both numerator and denominator anchors",
        "not enter ranks merely because the formula",
        "lookback count describes common-",
        "positions**, not a contiguous-observed-price requirement",
        "Each formula consumes exactly its two referenced",
        "Interior-missing fixtures for both factors retain momentum",
        "Every factor input price anchor is governed by",
        "All anchors must match that target's permanent security, listing,",
        "Traversal across different ticker text is allowed only through a",
        "Ticker-text-only joins,",
        "A reused-ticker fixture deliberately",
        "The continuous held-return policy is",
        "adjusted_close[d] / adjusted_close[d-1] - 1",
        "A log return, raw close, or alternate price field is forbidden",
        "The corporate-action fixture holds a split security",
        "10-bps post-return-equity cost impact",
        "factor-specific common-calendar lookback position span addressable",
        "no extra observed-price completeness gate",
        "Prospective collection compares only canonical UTC instants",
        "Each signal instant is the official",
        "XNYS session close from the frozen calendar",
        "shared XNYS month-end date",
        "strictly before the official",
        "threshold-output-maturity instant",
        "Opening at counter increment",
        "Runner-",
        "code freeze alone is insufficient",
        "staggered binding fixture freezes runner code",
        "detached binding does not pretend to hash future provider bytes",
        "valid append never",
        "append fixture binds a seed cutoff",
        "only a subset of factors is valid",
        "The equal-weight eligible-universe baseline is the same frozen target",
        "The random-rank baseline alone inherits all three factor decision-time invalid-",
        "`episode_21_row_return` is a separate overlapping diagnostic",
        "hold those exact initial weights statically",
        "sum(weight_i_at_e * constituent_return_i)",
        "Survivor renormalization, zero/fill, cash substitution,",
        "the next execution precedes `e+21`",
        "primary benchmark are -0.0110 and -0.0125",
        "calendar-only strategy schedule includes a signal only when",
        "being excluded from",
        "continuous strategy schedule because its next monthly execution",
        "Removing the month",
        "A valid/tied/valid three-month fixture",
        "The random baseline does not derive a",
        "seed or consume a permutation for that factor/month",
        "freezes once, campaign-wide, at the earliest signal cutoff",
        "per-factor freeze or re-encoding is forbidden",
        "For `2<=n<=6`, set `L=1`",
        "overlapping circular moving-block bootstrap within each segment",
        "expected inclusion weight",
        "nonmultiple-segment null-mean golden fixture uses 63 records",
        "short-segment golden fixture uses 60 records",
        "resampling support is degenerate",
    ]:
        assert phrase in contract

    for phrase in [
        "semantic_trial_count: 14",
        "status: PROTOCOL_FROZEN_PENDING_BLINDED_DATA_ACCEPTANCE",
        "label_kind: execution_anchored_forward_return_v1",
        "label_end: SIGNAL_CLOSE_PLUS_22_COMMON_CALENDAR_ROWS",
        "horizon_purge_signal_axis_rows: 22",
        "embargo_rows: 0",
        "random_rank_seed: 20260729",
        "bootstrap_seed: 20260730",
        "long_segment_block_length_monthly_records: 6",
        "bootstrap_replicates: 20000",
        "minimum_valid_monthly_records_for_primary_inference: 60",
        "percentile_quantile_method: linear",
        "multiplicity_method: HOLM",
        "holm_stop_rule: STOP_AT_FIRST_NON_REJECTION",
        "complete_case_rule: ALL_THREE_PRIMARY_FACTOR_RANK_ICS_VALID",
        "rng_consumption_order: REPLICATE_MAJOR_THEN_CHRONOLOGICAL_SEGMENT",
        "dependence_aware_method: OVERLAPPING_CIRCULAR_MOVING_BLOCK_BOOTSTRAP_WITHIN_SEGMENT",
        "circular_index_rule: (START_PLUS_OFFSET)_MOD_SEGMENT_LENGTH",
        "uniform_marginal_row_weight: REQUIRED_EACH_RETAINED_ROW_EXPECTED_INCLUSION_ONE_PER_SEGMENT_REPLICATE",
        "record_count: 63",
        "forbidden_noncircular_action: REJECT_AS_TRUNCATION_BIASED_NOT_NULL_CENTERED",
        "return_object: CONTINUOUS_DAILY_NEXT_MONTHLY_EXECUTION_TO_EXECUTION_PATH",
        "minimum_distinct_factor_values: 10",
        "minimum_distinct_forward_returns: 2",
        "complete_full_37_event_profile_first: false",
        "version: listing_lineage_key_bytes_v1",
        "version: factor_anchor_lineage_v1",
        "anchor_to_target_identity_match: EXACT_PERMANENT_SECURITY_LISTING_AND_LISTING_EPISODE",
        "allowed_alias_traversal: ACCEPTED_SYMBOL_RENAME_SAME_PERMANENT_SECURITY_SAME_LISTING_AND_LISTING_EPISODE_ONLY",
        "price_stitch_or_ticker_fallback: FORBIDDEN",
        "version: adjusted_close_simple_held_return_v1",
        "strategy_held_return_field: adjusted_close",
        "primary_benchmark_held_return_field: adjusted_close",
        "selected_target_execution_anchor_field: adjusted_close",
        "primary_benchmark_execution_anchor_field: adjusted_close",
        "return_formula: adjusted_close[d] / adjusted_close[d-1] - 1",
        "raw_close_return_fallback: FORBIDDEN",
        "separate_split_or_dividend_cash_flow_addition: FORBIDDEN_TO_PREVENT_DOUBLE_COUNTING",
        "forbidden_raw_close_gross_return: -0.25",
        "post_t_mutation_effect_on_frozen_objects: NONE_BYTE_IDENTICAL",
        "fixed_bps_interpretation: ALL_IN_DIAGNOSTIC_EXECUTION_COST_PROXY",
        "evaluation: ORDERED_FIRST_MATCH_WINS_MUTUALLY_EXCLUSIVE_EXHAUSTIVE",
        "formula: \"-std([adjusted_close[d] / adjusted_close[d-1] - 1 for d=t-62..t], ddof=1)\"",
        "one_day_return_kind: SIMPLE_NOT_LOG",
        "price_anchor_validation: REAL_NUMERIC_NON_BOOLEAN_PRESENT_FINITE_STRICTLY_POSITIVE",
        "invalid_anchor_action: INVALID_MISSING_FACTOR_VALUE_EXCLUDE_LISTING_FROM_FACTOR_DECISION_TIME_ELIGIBILITY_AND_COUNT_REASON",
        "forward_return_kind: SIMPLE_NOT_LOG",
        "forward_return_formula: adjusted_close[label_end] / adjusted_close[label_start] - 1",
        "invalid_forward_anchor_action: INVALIDATE_AND_RETAIN_FACTOR_MONTH_OUTCOME_WITH_REASON_COUNT",
        "draw_reuse_across_distributions: SAME_ROW_INDEX_VECTOR_FOR_UNCENTERED_AND_NULL_CENTERED_TABLES",
        "rng_passes_per_replicate: ONE_NO_SECOND_CENTERED_OR_UNCENTERED_PASS",
        "price_anchor_validation: ALL_REAL_NUMERIC_NON_BOOLEAN_PRESENT_FINITE_STRICTLY_POSITIVE",
        "lookback_common_calendar_positions: 253",
        "lookback_common_calendar_positions: 22",
        "required_observed_price_anchors: 2",
        "intermediate_adjusted_close_values_required: false",
        "interior_missing_price_action: NO_FACTOR_VALUE_EFFECT_IF_REFERENCED_ANCHORS_VALID",
        "FACTOR_SPECIFIC_LOOKBACK_COMMON_CALENDAR_POSITION_SPAN_ADDRESSABLE_AT_T",
        "FACTOR_SPECIFIC_REFERENCED_PRICE_ANCHORS_VALID_AT_T",
        "FACTOR_SPECIFIC_FACTOR_ANCHOR_LINEAGE_V1_IDENTITY_AND_PATH_VALID_AT_T",
        "canonical_instant_standard: UTC_RFC3339_TIMEZONE_AWARE_EXACT_INSTANT",
        "freeze_timestamp_normalization: REQUIRE_TIMEZONE_AWARE_CONVERT_TO_UTC_REJECT_NAIVE_OR_DATE_ONLY",
        "detached_run_binding_completion_predicate: EXACT_PROTOCOL_INVENTORY_DATA_CODE_CONFIG_AND_ENVIRONMENT_IDENTITY_BOUND_BEFORE_RESULT_BEARING_JOB",
        "detached_run_binding_incomplete: PROSPECTIVE_COUNT_FORBIDDEN",
        "historical_seed: EXACT_IMMUTABLE_ACCEPTED_DATA_RECORD_AND_CUTOFF_BOUND_AT_DETACHED_RUN_BINDING",
        "append_record_chain: SEQUENCE_PREVIOUS_RECORD_SHA256_BATCH_MANIFEST_SHA256_SESSION_BOUNDS_INGESTED_AT_UTC",
        "original_start_anchor_reset_on_append: FORBIDDEN",
        "correction_policy: APPEND_CORRECTION_RECORD_NO_OVERWRITE_NO_RETROACTIVE_SIGNAL_RECOMPUTE_AND_RETAIN_AFFECTED_VALIDITY",
        "signal_instant: OFFICIAL_XNYS_SESSION_CLOSE_FROM_FROZEN_CALENDAR_CONVERTED_TO_UTC",
        "start_anchor_timestamp: MAXIMUM_OF_ALL_NORMALIZED_REQUIRED_FREEZE_INSTANTS_UTC",
        "start_rule: FIRST_SIGNAL_WITH_SIGNAL_INSTANT_UTC_STRICTLY_GT_START_ANCHOR_UTC_SATISFYING_SIGNAL_ELIGIBILITY_PREDICATE",
        "freeze_at_or_after_official_close: SAME_DAY_SIGNAL_NOT_PROSPECTIVE",
        "signal_at_exact_start_anchor_instant: NOT_PROSPECTIVE",
        "signal_eligibility_predicate: ALL_THREE_FACTOR_REBALANCES_DECISION_TIME_VALID",
        "subset_factor_eligible_signal_action: RETAIN_OPERATIONAL_RECORD_DO_NOT_START_OR_INCREMENT",
        "rebalance_count_increment: ONE_ONLY_WHEN_SIGNAL_ELIGIBILITY_PREDICATE_TRUE",
        "threshold_output_maturity_instant: MAXIMUM_OF_LABEL_AND_STRATEGY_MATURITY_INSTANTS",
        "protected_opening_timing: STRICTLY_AFTER_THRESHOLD_OUTPUT_MATURITY_INSTANT",
        "opening_at_counter_increment_or_label_only: FORBIDDEN",
        "random_seed_or_permutation_consumption: NONE",
        "version: frozen_target_execution_to_e_plus_21_v1",
        "intervening_monthly_execution_before_endpoint: IGNORE_FOR_THIS_EPISODE_NO_TARGET_RESET_OR_CONTINUOUS_PATH_SLICE",
        "aggregation_formula: sum(weight_i_at_e * constituent_return_i)",
        "invalid_target_constituent_action: INVALID_MISSING_RETAIN_EPISODE_AND_EXACT_REASON",
        "forbidden_continuous_path_slice_return: 0.10",
        "episodic_return: INVALID_MISSING_NOT_ZERO",
        "required_output_reconciliation: INVALID_OUTPUT_PRESENT_NOT_MISSING_TRIAL_OUTPUT",
        "key_freeze: FIRST_ANY_FACTOR_DECISION_TIME_ELIGIBILITY_CAMPAIGN_WIDE",
        "per_factor_key_freeze_or_reencoding: FORBIDDEN",
        "segment_block_length: 6_IF_SEGMENT_LENGTH_GT_6_ELSE_1",
        "short_segment_rule: LENGTH_2_THROUGH_6_DRAW_N_SINGLE_ROW_BLOCKS_UNIFORMLY_WITH_REPLACEMENT",
        "degenerate_resampling_action: PRIMARY_INFERENCE_INVALID_NO_HOLM_SUPPORT_RETAIN_COUNTS",
        "nondegenerate_bootstrap_support_all_three_factors: REQUIRED",
        "relation_to_primary_benchmark: SAME_FROZEN_TARGET_AND_GROSS_COST_FREE_CONTINUOUS_RETURN_OBJECT",
        "primary_benchmark_reuse_of_factor_or_random_zero_target: FORBIDDEN",
        "boundary_signal_with_complete_label_but_next_execution_after_cutoff: EXCLUDE_BEFORE_CONTINUOUS_TARGET_FREEZE_NOT_INVALID",
        "boundary_exclusion_strategy_artifacts: NO_TARGET_NO_TURNOVER_NO_COST_NO_HARD_VALIDITY_FAILURE",
        "invalid_factor_month_continuous_path: INCLUDE_UNFILTERED_IN_FULL_STRATEGY_AND_PRIMARY_BENCHMARK_DAILY_PATH",
        "invalid_factor_month_filtering: FORBIDDEN",
        "invalid_factor_month_segmentation_or_cash_restart: FORBIDDEN",
        "matched_factor_invalid_continuous_economic_path: INCLUDED_AS_PRIMARY_BENCHMARK_RETURN_SUBJECT_TO_EARLIER_COVERAGE_GATES",
        "adjusted_close_t_minus_252: 80.0",
        "adjusted_close_t: 90.0",
        "all_other_zero_target_triggers: FORBIDDEN",
        "byte_relation: EXACT_BYTE_FOR_BYTE_COPY",
        "rank_ic_input_table: PRIMARY_COMMON_COMPLETE_CASE_MONTHLY_RANK_IC_TABLE",
        "positive_year_fraction_denominator: ALL_REQUIRED_YEARS",
        "semantic_relation: EXACT_FROZEN_14_TRIAL_INVENTORY",
        "factor_turnover_predecessor: IMMEDIATELY_PRECEDING_SCHEDULED_FROZEN_DECISION_TIME_TARGET",
        "outcome_invalid_middle_target_retention: RETAIN_AS_NEXT_TURNOVER_PREDECESSOR",
        "primary_benchmark_comparison_gap_final_state: INVALID_DIAGNOSTIC_HARD_VALIDITY_FAILURE",
        "secondary_spy_comparison_final_state_role: DESCRIPTIVE_ONLY_NO_EFFECT",
        "cost_formula: gross_multiplier * turnover * bps / 10000",
        "cost_return_basis: BEGINNING_PERIOD_RETURN_IMPACT_OF_POST_RETURN_EQUITY_CHARGE",
        "strategy_security_cost_at_execution: -gross_multiplier * (bps / 10000) * abs(delta_weight)",
        "date_token: SIGNAL_DATE_T_STRICT_YYYY_MM_DD_NOT_EXECUTION_DATE",
        "selection: FIRST_TOP_DECILE_SIZE_PERMUTED_INDICES",
        "top_decile_size: 11",
        "holm_index_origin: ONE_BASED_K_1_THROUGH_3",
        "holm_python_sorted_access: sorted_raw_p[k-1]",
        "holm_map_back: ORIGINAL_FACTOR_ORDER_AFTER_SORTED_RUNNING_MAX",
    ]:
        assert phrase in preregistration

    assert "TO_BE_FROZEN" not in preregistration
    assert "COMPLETE_FACTOR_HISTORY_THROUGH_T" not in preregistration
    assert "preregistration_sha256:" not in preregistration
    assert inventory["semantic_trial_count"] == 14
    assert len(inventory["trials"]) == 14
    trial_ids = [trial["trial_id"] for trial in inventory["trials"]]
    assert len(set(trial_ids)) == 14
    assert trial_ids[:5] == [
        "BASELINE_EQUAL_WEIGHT_UNIVERSE",
        "BASELINE_RANDOM_RANK_TOP_DECILE",
        "DIAG_MOM_12_1",
        "DIAG_REV_1M",
        "DIAG_LOW_VOL_3M",
    ]
    strategy_trials = inventory["trials"][5:]
    assert {
        (trial["factor_id"], trial["cost_bps"]) for trial in strategy_trials
    } == {
        (factor_id, cost_bps)
        for factor_id in ["MOM_12_1", "REV_1M", "LOW_VOL_3M"]
        for cost_bps in [0, 10, 25]
    }
    assert inventory["trials"][1]["seed"] == 20260729
    expected_factor_ids = ["MOM_12_1", "REV_1M", "LOW_VOL_3M"]
    expected_baseline_outputs = [
        "episode_21_row_return",
        "continuous_daily_return",
    ]
    episode_common_contract = {
        "aggregation": (
            "SUM_FROZEN_EXECUTION_WEIGHT_TIMES_CONSTITUENT_"
            "SIMPLE_ADJUSTED_CLOSE_RETURN"
        ),
        "anchor_field": "adjusted_close",
        "anchor_lineage_policy": "factor_anchor_lineage_v1",
        "anchor_validation": (
            "BOTH_REAL_NUMERIC_NON_BOOLEAN_PRESENT_FINITE_STRICTLY_POSITIVE"
        ),
        "cost_bps": 0,
        "constituent_return_kind": "SIMPLE_NOT_LOG",
        "endpoint": "EXECUTION_E_PLUS_21_COMMON_CALENDAR_ROWS",
        "holding_rule": (
            "STATIC_SIGNAL_TIME_TARGET_FROM_EXECUTION_E_THROUGH_E_PLUS_21_"
            "IGNORE_INTERVENING_MONTHLY_EXECUTIONS"
        ),
        "invalid_constituent_action": (
            "INVALID_MISSING_RETAIN_EPISODE_NO_SURVIVOR_RENORMALIZATION_"
            "FILL_CASH_OR_ZERO"
        ),
        "return_formula": (
            "sum(weight_i_at_e * (adjusted_close_i[e+21] / "
            "adjusted_close_i[e] - 1))"
        ),
        "return_basis": "GROSS_COST_FREE_FACTOR_DIAGNOSTIC",
    }
    episode_target_rules = (
        "EQUAL_WEIGHT_ALL_FACTOR_SPECIFIC_DECISION_TIME_ELIGIBLE_KEYS_"
        "FROZEN_AT_SIGNAL_T",
        "EQUAL_WEIGHT_FROZEN_RANDOM_RANK_TOP_DECILE_KEYS_"
        "SELECTED_AT_SIGNAL_T",
    )
    for baseline, target_rule in zip(
        inventory["trials"][:2],
        episode_target_rules,
        strict=True,
    ):
        assert baseline["output_factor_ids"] == expected_factor_ids
        assert baseline["output_series_per_factor"] == expected_baseline_outputs
        assert baseline["output_contract_per_series"][
            "episode_21_row_return"
        ] == {**episode_common_contract, "target_rule": target_rule}
    assert inventory["trials"][0]["output_contract_per_series"][
        "continuous_daily_return"
    ] == {
        "cost_bps": 0,
        "return_basis": "GROSS_COST_FREE",
    }
    assert inventory["trials"][1]["output_contract_per_series"][
        "continuous_daily_return"
    ] == {
        "accounting": (
            "POST_RETURN_EQUITY_CHARGE_AS_BEGINNING_PERIOD_RETURN_IMPACT"
        ),
        "cost_bps": 10,
        "return_basis": "NET_PRIMARY",
    }
    assert inventory["trials"][1]["return_contract"] == (
        "CONTINUOUS_DAILY_NEXT_MONTHLY_EXECUTION_TO_EXECUTION_PATH"
    )
    assert inventory["trials"][1]["turnover_convention"] == (
        "UNDIVIDED_SUM_ABSOLUTE_WEIGHT_CHANGES_FROM_DRIFTED_WEIGHTS"
    )
    assert inventory["trials"][1]["rng_seed_date_token"] == (
        "SIGNAL_DATE_T_STRICT_YYYY-MM-DD_NOT_EXECUTION_DATE"
    )
    assert inventory["trials"][1]["permutation_rank_order"] == (
        "HIGH_TO_LOW_FIRST_CHUNK_SELECTED"
    )
    assert inventory["trials"][1]["random_top_decile_size_rule"] == (
        "N//10_PLUS_ONE_IFF_N_MOD_10_NONZERO"
    )
    assert inventory["trials"][1]["selected_target_rule"] == (
        "EQUAL_WEIGHT_SELECTED_KEYS_SERIALIZED_IN_ASCENDING_CANONICAL_KEY_BYTES"
    )
    assert inventory["trials"][1]["rng_seed_derivation"] == (
        "first_16_hex_sha256("
        "random_rank_v1|20260729|factor_id|signal_date_t_YYYY-MM-DD)"
    )
    assert all(trial["type"].startswith("STRATEGY_") for trial in strategy_trials)
    assert {
        trial["return_contract"] for trial in strategy_trials
    } == {"CONTINUOUS_DAILY_NEXT_MONTHLY_EXECUTION_TO_EXECUTION_PATH"}


def test_factor_price_anchors_bind_to_resolved_listing_lineage() -> None:
    target_identity = {
        "resolved_permanent_security_id": "SECURITY-001",
        "resolved_listing_id": "LISTING-001",
        "resolved_listing_episode_id": "EPISODE-001",
    }
    accepted_rename_chain = [
        {
            **target_identity,
            "source_exchange": "XNYS",
            "source_ticker": "OLD",
            "alias_effective_from": "2020-01-01",
            "alias_effective_to": "2025-06-01",
            "lineage_resolution_evidence_id": "rename-evidence-001",
            "transition_to_next": (
                "ACCEPTED_SYMBOL_RENAME_SAME_PERMANENT_SECURITY_"
                "SAME_LISTING_AND_LISTING_EPISODE"
            ),
        },
        {
            **target_identity,
            "source_exchange": "XNYS",
            "source_ticker": "NEW",
            "alias_effective_from": "2025-06-01",
            "alias_effective_to": None,
            "lineage_resolution_evidence_id": "rename-evidence-001",
            "transition_to_next": "TARGET_ALIAS",
        },
    ]
    accepted_rename_anchors = [
        {
            **accepted_rename_chain[0],
            "session_date": "2025-01-02",
            "adjusted_close": 80.0,
        },
        {
            **accepted_rename_chain[1],
            "session_date": "2025-12-01",
            "adjusted_close": 100.0,
        },
    ]

    assert _factor_anchor_lineage_v1_is_valid(
        accepted_rename_anchors,
        target_identity,
        accepted_rename_chain,
    )
    assert (
        float(accepted_rename_anchors[1]["adjusted_close"])
        / float(accepted_rename_anchors[0]["adjusted_close"])
        - 1.0
    ) == 0.25

    reused_ticker_anchors = deepcopy(accepted_rename_anchors)
    reused_ticker_chain = deepcopy(accepted_rename_chain)
    reused_ticker_anchors[0].update(
        {
            "source_ticker": "REUSED",
            "resolved_permanent_security_id": "SECURITY-OLD-ISSUER",
            "resolved_listing_id": "LISTING-OLD-ISSUER",
            "resolved_listing_episode_id": "EPISODE-OLD-ISSUER",
        }
    )
    reused_ticker_anchors[1].update(
        {
            "source_ticker": "REUSED",
            "resolved_permanent_security_id": "SECURITY-NEW-ISSUER",
            "resolved_listing_id": "LISTING-NEW-ISSUER",
            "resolved_listing_episode_id": "EPISODE-NEW-ISSUER",
        }
    )
    for anchor_index, alias in enumerate(reused_ticker_chain):
        alias.update(
            {
                "source_ticker": "REUSED",
                "resolved_permanent_security_id": (
                    "SECURITY-OLD-ISSUER"
                    if anchor_index == 0
                    else "SECURITY-NEW-ISSUER"
                ),
                "resolved_listing_id": (
                    "LISTING-OLD-ISSUER"
                    if anchor_index == 0
                    else "LISTING-NEW-ISSUER"
                ),
                "resolved_listing_episode_id": (
                    "EPISODE-OLD-ISSUER"
                    if anchor_index == 0
                    else "EPISODE-NEW-ISSUER"
                ),
            }
        )
    reused_ticker_target = {
        field: str(reused_ticker_anchors[1][field])
        for field in target_identity
    }
    forbidden_ticker_only_join = (
        reused_ticker_anchors[0]["source_ticker"]
        == reused_ticker_anchors[1]["source_ticker"]
    )
    forbidden_ticker_only_momentum = (
        float(reused_ticker_anchors[1]["adjusted_close"])
        / float(reused_ticker_anchors[0]["adjusted_close"])
        - 1.0
    )

    assert forbidden_ticker_only_join
    assert forbidden_ticker_only_momentum == 0.25
    assert not _factor_anchor_lineage_v1_is_valid(
        reused_ticker_anchors,
        reused_ticker_target,
        reused_ticker_chain,
    )

    gapped_rename_chain = deepcopy(accepted_rename_chain)
    gapped_rename_chain[1]["alias_effective_from"] = "2025-06-02"
    assert not _factor_anchor_lineage_v1_is_valid(
        accepted_rename_anchors,
        target_identity,
        gapped_rename_chain,
    )


def test_listing_key_freezes_at_campaign_first_any_factor_eligibility() -> None:
    first_eligibility = {
        "REV_1M": datetime(2026, 7, 31, 20, tzinfo=timezone.utc),
        "LOW_VOL_3M": datetime(2026, 8, 31, 20, tzinfo=timezone.utc),
        "MOM_12_1": datetime(2026, 9, 30, 20, tzinfo=timezone.utc),
    }
    campaign_freeze = min(first_eligibility.values())
    endpoint_known_at = datetime(2026, 8, 15, 20, tzinfo=timezone.utc)
    campaign_effective_to = (
        "2026-10-15" if endpoint_known_at <= campaign_freeze else None
    )
    campaign_key = _listing_lineage_key_bytes_v1(
        "XNYS", "STAG", "2026-07-01", campaign_effective_to
    )
    keys_by_factor = {
        factor_id: bytes(campaign_key) for factor_id in first_eligibility
    }
    forbidden_momentum_specific_key = _listing_lineage_key_bytes_v1(
        "XNYS", "STAG", "2026-07-01", "2026-10-15"
    )

    assert campaign_freeze == first_eligibility["REV_1M"]
    assert campaign_effective_to is None
    assert len(set(keys_by_factor.values())) == 1
    assert keys_by_factor["MOM_12_1"] == keys_by_factor["REV_1M"]
    assert campaign_key != forbidden_momentum_specific_key


def test_random_rank_top_decile_nondivisible_golden_fixture() -> None:
    seed_preimage = "random_rank_v1|20260729|MOM_12_1|2026-07-29"
    seed_digest = hashlib.sha256(seed_preimage.encode("ascii")).hexdigest()
    seed = int(seed_digest[:16], 16)
    ordered_keys = tuple(
        sorted(
            _listing_lineage_key_bytes_v1(
                "XNYS", f"T{index:03d}", "2014-01-01", None
            )
            for index in range(103)
        )
    )
    permutation = tuple(
        int(index)
        for index in np.random.Generator(
            np.random.PCG64DXSM(seed)
        ).permutation(len(ordered_keys))
    )
    expected_permutation = (
        63, 102, 92, 77, 18, 42, 25, 36, 66, 1, 94, 26, 61, 10, 35, 52,
        57, 82, 6, 87, 56, 27, 99, 44, 33, 28, 11, 100, 9, 64, 62, 90,
        78, 93, 16, 81, 8, 79, 38, 85, 67, 58, 15, 74, 0, 22, 37, 21,
        24, 72, 53, 76, 41, 73, 80, 40, 17, 13, 12, 71, 14, 101, 30, 50,
        60, 59, 69, 47, 3, 19, 83, 54, 91, 4, 84, 68, 43, 39, 29, 97, 23,
        20, 45, 75, 5, 86, 48, 31, 34, 89, 98, 55, 2, 7, 32, 95, 70, 51,
        65, 46, 49, 96, 88,
    )
    top_decile_size = top_decile_count(len(ordered_keys))
    selected_keys_in_permutation_order = tuple(
        ordered_keys[index] for index in permutation[:top_decile_size]
    )
    forbidden_last_chunk = tuple(
        ordered_keys[index] for index in permutation[-top_decile_size:]
    )
    forbidden_floor_only_first_chunk = tuple(
        ordered_keys[index]
        for index in permutation[: len(ordered_keys) // 10]
    )
    expected_selected_keys = tuple(
        _listing_lineage_key_bytes_v1(
            "XNYS", ticker, "2014-01-01", None
        )
        for ticker in (
            "T063", "T102", "T092", "T077", "T018", "T042",
            "T025", "T036", "T066", "T001", "T094",
        )
    )
    serialized_equal_weight_target = tuple(
        sorted(
            (key, 1.0 / top_decile_size)
            for key in selected_keys_in_permutation_order
        )
    )

    assert seed_digest == (
        "4f3c72a41c74ed307cc6a86e734268f"
        "2266be31b4977ed99336462b234251e97"
    )
    assert seed == 5709564476776574256
    assert permutation == expected_permutation
    assert top_decile_size == 11
    assert selected_keys_in_permutation_order == expected_selected_keys
    assert tuple(key for key, _ in serialized_equal_weight_target) == tuple(
        sorted(expected_selected_keys)
    )
    assert all(
        math.isclose(weight, 1.0 / 11.0, abs_tol=1e-15)
        for _, weight in serialized_equal_weight_target
    )
    assert forbidden_last_chunk != expected_selected_keys
    assert forbidden_floor_only_first_chunk == expected_selected_keys[:-1]
    assert forbidden_floor_only_first_chunk != expected_selected_keys


def test_baseline_episode_ignores_intervening_monthly_reset() -> None:
    def episode_return(
        weights_at_execution: tuple[float, ...],
        execution_adjusted_close: tuple[object, ...],
        endpoint_adjusted_close: tuple[object, ...],
    ) -> float | None:
        if not (
            weights_at_execution
            and len(weights_at_execution) == len(execution_adjusted_close)
            and len(weights_at_execution) == len(endpoint_adjusted_close)
            and math.isclose(sum(weights_at_execution), 1.0, abs_tol=1e-15)
        ):
            return None
        constituent_returns: list[float] = []
        for before, after in zip(
            execution_adjusted_close,
            endpoint_adjusted_close,
            strict=True,
        ):
            if not all(
                not isinstance(anchor, bool)
                and isinstance(anchor, Real)
                and math.isfinite(float(anchor))
                and float(anchor) > 0.0
                for anchor in (before, after)
            ):
                return None
            constituent_returns.append(float(after) / float(before) - 1.0)
        return sum(
            weight * constituent_return
            for weight, constituent_return in zip(
                weights_at_execution,
                constituent_returns,
                strict=True,
            )
        )

    execution_row = 0
    next_monthly_execution_row = 20
    endpoint_row = 21
    frozen_weights = (0.5, 0.5)
    execution_prices = (100.0, 100.0)
    next_execution_prices = (110.0, 90.0)
    endpoint_prices = (121.0, 81.0)

    frozen_episode_return = episode_return(
        frozen_weights,
        execution_prices,
        endpoint_prices,
    )
    first_continuous_multiplier = sum(
        weight * next_price / execution_price
        for weight, next_price, execution_price in zip(
            frozen_weights,
            next_execution_prices,
            execution_prices,
            strict=True,
        )
    )
    forbidden_reset_weights = (1.0, 0.0)
    second_continuous_multiplier = sum(
        weight * endpoint_price / next_price
        for weight, endpoint_price, next_price in zip(
            forbidden_reset_weights,
            endpoint_prices,
            next_execution_prices,
            strict=True,
        )
    )
    forbidden_continuous_slice_return = (
        first_continuous_multiplier * second_continuous_multiplier - 1.0
    )

    assert execution_row < next_monthly_execution_row < endpoint_row
    assert frozen_episode_return is not None
    assert math.isclose(frozen_episode_return, 0.01, abs_tol=1e-15)
    assert math.isclose(
        forbidden_continuous_slice_return,
        0.10,
        abs_tol=1e-15,
    )
    assert not math.isclose(
        frozen_episode_return,
        forbidden_continuous_slice_return,
        abs_tol=1e-15,
    )

    invalid_endpoint_prices: tuple[object, ...] = (121.0, None)
    assert episode_return(
        frozen_weights,
        execution_prices,
        invalid_endpoint_prices,
    ) is None
    forbidden_survivor_renormalized_return = 121.0 / 100.0 - 1.0
    assert math.isclose(
        forbidden_survivor_renormalized_return,
        0.21,
        abs_tol=1e-15,
    )


def test_decision_time_targets_ignore_future_availability_mutations() -> None:
    records = []
    for index in range(100):
        records.append(
            {
                "listing_key_bytes": _listing_lineage_key_bytes_v1(
                    "XNYS", f"T{index:03d}", "2018-01-01", None
                ),
                "membership_known_at_t": True,
                "lineage_resolved_through_t": True,
                "factor_specific_lookback_position_span_addressable_at_t": True,
                "factor_specific_required_price_anchors_valid_at_t": True,
                "factor_anchor_lineage_v1_valid_at_t": True,
                "corporate_action_policy_known_at_t": True,
                "factor_value_at_t": float(100 - index),
                "execution_available_after_t": True,
                "endpoint_available_after_t": True,
                "endpoint_return": index / 100,
                "actual_effective_to_observed_after_t": None,
            }
        )

    frozen_target, frozen_benchmark, frozen_cash = _decision_time_objects(records)
    selected_keys = {key for key, _ in frozen_target}
    mutated = deepcopy(records)
    for record in mutated:
        if bytes(record["listing_key_bytes"]) in selected_keys:
            continue
        record["execution_available_after_t"] = False
        record["endpoint_available_after_t"] = False
        record["endpoint_return"] = None
        record["actual_effective_to_observed_after_t"] = "2026-07-30"

    assert _decision_time_objects(mutated) == (
        frozen_target,
        frozen_benchmark,
        frozen_cash,
    )
    assert frozen_cash == 0.0

    lineage_invalid = deepcopy(records)
    lineage_invalid[0]["factor_anchor_lineage_v1_valid_at_t"] = False
    invalid_target, invalid_benchmark, invalid_cash = _decision_time_objects(
        lineage_invalid
    )
    assert invalid_target == ()
    assert len(invalid_benchmark) == 99
    assert invalid_cash == 1.0


def test_zero_target_has_only_the_three_frozen_decision_time_triggers() -> None:
    records = []
    for index in range(100):
        records.append(
            {
                "listing_key_bytes": _listing_lineage_key_bytes_v1(
                    "XNYS", f"Z{index:03d}", "2018-01-01", None
                ),
                "membership_known_at_t": True,
                "lineage_resolved_through_t": True,
                "factor_specific_lookback_position_span_addressable_at_t": True,
                "factor_specific_required_price_anchors_valid_at_t": True,
                "factor_anchor_lineage_v1_valid_at_t": True,
                "corporate_action_policy_known_at_t": True,
                "factor_value_at_t": float(100 - index),
            }
        )

    valid_target, _, valid_cash = _decision_time_objects(records)
    assert len(valid_target) == 10
    assert valid_cash == 0.0

    sparse_target, _, sparse_cash = _decision_time_objects(records[:-1])
    assert sparse_target == ()
    assert sparse_cash == 1.0

    tied = deepcopy(records)
    for record in tied:
        record["factor_value_at_t"] = 1.0
    tied_target, _, tied_cash = _decision_time_objects(tied)
    assert tied_target == ()
    assert tied_cash == 1.0

    duplicate_key = deepcopy(records)
    duplicate_key[-1]["listing_key_bytes"] = duplicate_key[0]["listing_key_bytes"]
    duplicate_target, _, duplicate_cash = _decision_time_objects(duplicate_key)
    assert duplicate_target == ()
    assert duplicate_cash == 1.0


def test_endpoint_only_factor_windows_flow_into_decision_time_targets() -> None:
    for factor_id, key_prefix in (("MOM_12_1", "M"), ("REV_1M", "R")):
        records: list[dict[str, object]] = []
        for index in range(100):
            records.append(
                {
                    "factor_id": factor_id,
                    "listing_key_bytes": _listing_lineage_key_bytes_v1(
                        "XNYS",
                        f"{key_prefix}{index:03d}",
                        "2018-01-01",
                        None,
                    ),
                    "membership_known_at_t": True,
                    "lineage_resolved_through_t": True,
                    "factor_specific_lookback_position_span_addressable_at_t": True,
                    "factor_specific_required_price_anchors_valid_at_t": True,
                    "factor_anchor_lineage_v1_valid_at_t": True,
                    "unreferenced_interior_adjusted_close_missing": index == 0,
                    "corporate_action_policy_known_at_t": True,
                    "factor_value_at_t": float(100 - index),
                }
            )

        missing_interior_key = bytes(records[0]["listing_key_bytes"])
        target, benchmark, cash_weight = _decision_time_objects(records)
        forbidden_full_window_records = [
            record
            for record in records
            if not record["unreferenced_interior_adjusted_close_missing"]
        ]

        assert len(target) == 10
        assert missing_interior_key in {key for key, _ in target}
        assert len(benchmark) == 100
        assert cash_weight == 0.0
        assert _decision_time_objects(forbidden_full_window_records) == (
            (),
            tuple(
                sorted(
                    (
                        (bytes(record["listing_key_bytes"]), 1.0 / 99.0)
                        for record in forbidden_full_window_records
                    ),
                    key=lambda item: item[0],
                )
            ),
            1.0,
        )


def test_prospective_start_uses_latest_required_freeze_boundary() -> None:
    freeze_timestamps = {
        "protocol": datetime(2026, 7, 29, 20, tzinfo=timezone.utc),
        "dataset_policy": datetime(2026, 8, 10, 20, tzinfo=timezone.utc),
        "runner_code": datetime(2026, 8, 31, 20, tzinfo=timezone.utc),
    }
    eligible_signal_timestamps = (
        datetime(2026, 7, 31, 20, tzinfo=timezone.utc),
        datetime(2026, 8, 31, 20, tzinfo=timezone.utc),
        datetime(2026, 9, 30, 20, tzinfo=timezone.utc),
        datetime(2026, 10, 30, 20, tzinfo=timezone.utc),
    )
    factor_order = ("MOM_12_1", "REV_1M", "LOW_VOL_3M")
    factor_validity_by_signal = {
        eligible_signal_timestamps[0]: (True, True, True),
        eligible_signal_timestamps[1]: (True, True, True),
        eligible_signal_timestamps[2]: (True, True, False),
        eligible_signal_timestamps[3]: (True, True, True),
    }
    start_anchor = max(freeze_timestamps.values())
    prospective_start = min(
        signal
        for signal in eligible_signal_timestamps
        if signal > start_anchor
        and all(factor_validity_by_signal[signal])
    )
    forbidden_protocol_only_start = min(
        signal
        for signal in eligible_signal_timestamps
        if signal > freeze_timestamps["protocol"]
        and all(factor_validity_by_signal[signal])
    )
    forbidden_any_factor_start = min(
        signal
        for signal in eligible_signal_timestamps
        if signal > start_anchor
        and any(factor_validity_by_signal[signal])
    )

    assert start_anchor == eligible_signal_timestamps[1]
    assert len(factor_order) == 3
    assert prospective_start == eligible_signal_timestamps[3]
    assert forbidden_protocol_only_start == eligible_signal_timestamps[0]
    assert forbidden_any_factor_start == eligible_signal_timestamps[2]
    assert prospective_start != forbidden_protocol_only_start
    assert prospective_start != forbidden_any_factor_start


def test_prospective_same_day_freeze_uses_canonical_close_instant() -> None:
    signal_close = datetime(2026, 7, 31, 20, tzinfo=timezone.utc)
    next_signal_close = datetime(2026, 8, 31, 20, tzinfo=timezone.utc)
    freezes = {
        "before_close": datetime(2026, 7, 31, 19, 59, 59, tzinfo=timezone.utc),
        "at_close": signal_close,
        "after_close": datetime(2026, 7, 31, 20, 0, 1, tzinfo=timezone.utc),
    }

    def first_prospective_signal(freeze_instant: datetime) -> datetime:
        if freeze_instant.tzinfo is None:
            raise ValueError("freeze instant must be timezone-aware")
        normalized_freeze = freeze_instant.astimezone(timezone.utc)
        return min(
            instant
            for instant in (signal_close, next_signal_close)
            if instant > normalized_freeze
        )

    assert first_prospective_signal(freezes["before_close"]) == signal_close
    assert first_prospective_signal(freezes["at_close"]) == next_signal_close
    assert first_prospective_signal(freezes["after_close"]) == next_signal_close
    try:
        first_prospective_signal(datetime(2026, 7, 31, 19, 59, 59))
    except ValueError as error:
        assert str(error) == "freeze instant must be timezone-aware"
    else:
        raise AssertionError("naive freeze instant must fail closed")


def test_prospective_start_waits_for_complete_detached_run_binding() -> None:
    runner_code_freeze = datetime(2026, 8, 15, 20, tzinfo=timezone.utc)
    august_signal = datetime(2026, 8, 31, 20, tzinfo=timezone.utc)
    detached_binding_completion = datetime(
        2026, 9, 5, 20, tzinfo=timezone.utc
    )
    september_signal = datetime(2026, 9, 30, 20, tzinfo=timezone.utc)
    qualifying_signals = (august_signal, september_signal)

    required_anchor = max(runner_code_freeze, detached_binding_completion)
    prospective_start = min(
        signal for signal in qualifying_signals if signal > required_anchor
    )
    forbidden_code_only_start = min(
        signal for signal in qualifying_signals if signal > runner_code_freeze
    )

    assert runner_code_freeze < august_signal < detached_binding_completion
    assert prospective_start == september_signal
    assert forbidden_code_only_start == august_signal
    assert prospective_start != forbidden_code_only_start


def test_prospective_data_appends_without_resetting_original_anchor() -> None:
    detached_binding_completion = datetime(
        2026, 2, 5, 20, tzinfo=timezone.utc
    )
    seed_cutoff = date(2026, 1, 30)
    seed_manifest_sha256 = hashlib.sha256(
        b"historical-seed-cutoff-2026-01-30"
    ).hexdigest()

    def append_record(
        *,
        sequence: int,
        previous_record_sha256: str,
        session_start: date,
        session_end: date,
        signal_instant: datetime,
        output_maturity: datetime,
        ingested_at: datetime,
    ) -> dict[str, object]:
        payload = {
            "sequence": sequence,
            "seed_manifest_sha256": seed_manifest_sha256,
            "previous_record_sha256": previous_record_sha256,
            "batch_manifest_sha256": hashlib.sha256(
                f"batch-{sequence}-{session_start}-{session_end}".encode()
            ).hexdigest(),
            "session_start": session_start.isoformat(),
            "session_end": session_end.isoformat(),
            "signal_instant": signal_instant.isoformat(),
            "output_maturity": output_maturity.isoformat(),
            "ingested_at": ingested_at.isoformat(),
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":")
        ).encode()
        return payload | {"record_sha256": hashlib.sha256(canonical).hexdigest()}

    seed_record_sha256 = hashlib.sha256(
        f"0|{seed_manifest_sha256}|{seed_cutoff}".encode()
    ).hexdigest()
    february = append_record(
        sequence=1,
        previous_record_sha256=seed_record_sha256,
        session_start=date(2026, 2, 2),
        session_end=date(2026, 2, 27),
        signal_instant=datetime(2026, 2, 27, 21, tzinfo=timezone.utc),
        output_maturity=datetime(2026, 4, 1, 20, tzinfo=timezone.utc),
        ingested_at=datetime(2026, 2, 27, 21, 5, tzinfo=timezone.utc),
    )
    march = append_record(
        sequence=2,
        previous_record_sha256=str(february["record_sha256"]),
        session_start=date(2026, 3, 2),
        session_end=date(2026, 3, 31),
        signal_instant=datetime(2026, 3, 31, 20, tzinfo=timezone.utc),
        output_maturity=datetime(2026, 5, 1, 20, tzinfo=timezone.utc),
        ingested_at=datetime(2026, 3, 31, 20, 5, tzinfo=timezone.utc),
    )
    records = (february, march)
    as_of = datetime(2026, 5, 1, 20, 0, 1, tzinfo=timezone.utc)

    previous_hash = seed_record_sha256
    previous_cutoff = seed_cutoff
    for expected_sequence, record in enumerate(records, start=1):
        assert record["sequence"] == expected_sequence
        assert record["previous_record_sha256"] == previous_hash
        assert date.fromisoformat(str(record["session_start"])) > previous_cutoff
        assert record["seed_manifest_sha256"] == seed_manifest_sha256
        previous_hash = str(record["record_sha256"])
        previous_cutoff = date.fromisoformat(str(record["session_end"]))

    matured_count = sum(
        datetime.fromisoformat(str(record["signal_instant"]))
        > detached_binding_completion
        and datetime.fromisoformat(str(record["output_maturity"])) < as_of
        for record in records
    )
    forbidden_reanchored_count = sum(
        datetime.fromisoformat(str(record["signal_instant"]))
        > datetime.fromisoformat(str(record["ingested_at"]))
        for record in records
    )

    assert matured_count == 2
    assert forbidden_reanchored_count == 0
    assert detached_binding_completion < datetime.fromisoformat(
        str(february["signal_instant"])
    )


def test_prospective_threshold_waits_for_label_and_strategy_maturity() -> None:
    threshold_signal = datetime(2024, 6, 28, 20, tzinfo=timezone.utc)
    threshold_execution = datetime(2024, 7, 1, 20, tzinfo=timezone.utc)
    label_maturity = datetime(2024, 7, 31, 20, tzinfo=timezone.utc)
    next_monthly_execution = datetime(2024, 8, 1, 20, tzinfo=timezone.utc)
    output_maturity = max(label_maturity, next_monthly_execution)

    def timing_gate_open(
        qualifying_count: int,
        threshold: int,
        access_instant: datetime,
    ) -> bool:
        return qualifying_count >= threshold and access_instant > output_maturity

    for threshold in (12, 24):
        assert not timing_gate_open(threshold, threshold, threshold_signal)
        assert not timing_gate_open(threshold, threshold, threshold_execution)
        assert not timing_gate_open(threshold, threshold, label_maturity)
        assert not timing_gate_open(
            threshold,
            threshold,
            next_monthly_execution,
        )
        assert timing_gate_open(
            threshold,
            threshold,
            datetime(2024, 8, 1, 20, 0, 1, tzinfo=timezone.utc),
        )
        assert not timing_gate_open(
            threshold - 1,
            threshold,
            datetime(2024, 8, 1, 20, 0, 1, tzinfo=timezone.utc),
        )


def test_invalid_factor_month_separates_invested_benchmark_from_random_cash() -> None:
    valid_records = []
    for index in range(100):
        valid_records.append(
            {
                "listing_key_bytes": _listing_lineage_key_bytes_v1(
                    "XNYS", f"B{index:03d}", "2018-01-01", None
                ),
                "membership_known_at_t": True,
                "lineage_resolved_through_t": True,
                "factor_specific_lookback_position_span_addressable_at_t": True,
                "factor_specific_required_price_anchors_valid_at_t": True,
                "factor_anchor_lineage_v1_valid_at_t": True,
                "corporate_action_policy_known_at_t": True,
                "factor_value_at_t": float(100 - index),
            }
        )

    def baseline_outputs(
        records: list[dict[str, object]],
        baseline_id: str,
    ) -> dict[str, object]:
        factor_target, eligible_benchmark, cash_weight = (
            _decision_time_objects(records)
        )
        unique_keys = len(
            {record["listing_key_bytes"] for record in records}
        ) == len(records)
        if baseline_id == "EQUAL_WEIGHT":
            if not records or not unique_keys:
                return {
                    "validity": "INVALID_UNFORMABLE_BENCHMARK",
                    "target": (),
                    "cash_weight": None,
                    "episodic_return": None,
                    "random_draw_consumed": False,
                    "output_record_retained": True,
                }
            return {
                "validity": (
                    "MATCHED_FACTOR_MONTH_INVALID"
                    if cash_weight == 1.0
                    else "VALID"
                ),
                "target": eligible_benchmark,
                "cash_weight": 0.0,
                "episodic_return": "MEASURE_AFTER_OUTCOME_GATE",
                "random_draw_consumed": False,
                "output_record_retained": True,
            }
        if cash_weight == 1.0:
            return {
                "validity": "INVALID_DECISION_TIME_FACTOR_MONTH",
                "target": (),
                "cash_weight": 1.0,
                "episodic_return": None,
                "random_draw_consumed": False,
                "output_record_retained": True,
            }
        return {
            "validity": "VALID",
            "target": factor_target,
            "cash_weight": 0.0,
            "episodic_return": "MEASURE_AFTER_OUTCOME_GATE",
            "random_draw_consumed": baseline_id == "RANDOM_RANK",
            "output_record_retained": True,
        }

    invalid_cases = {
        "sparse": valid_records[:-1],
        "tied": [
            {**record, "factor_value_at_t": 1.0}
            for record in valid_records
        ],
        "duplicate_key": [
            *valid_records[:-1],
            {
                **valid_records[-1],
                "listing_key_bytes": valid_records[0]["listing_key_bytes"],
            },
        ],
    }
    expected_invalid_output = {
        "validity": "INVALID_DECISION_TIME_FACTOR_MONTH",
        "target": (),
        "cash_weight": 1.0,
        "episodic_return": None,
        "random_draw_consumed": False,
        "output_record_retained": True,
    }

    assert len(baseline_outputs(valid_records, "EQUAL_WEIGHT")["target"]) == 100
    assert len(baseline_outputs(valid_records, "RANDOM_RANK")["target"]) == 10
    assert baseline_outputs(valid_records, "RANDOM_RANK")[
        "random_draw_consumed"
    ] is True
    for case_name in ("sparse", "tied"):
        records = invalid_cases[case_name]
        equal_weight_output = baseline_outputs(records, "EQUAL_WEIGHT")
        assert equal_weight_output["validity"] == (
            "MATCHED_FACTOR_MONTH_INVALID"
        )
        assert len(equal_weight_output["target"]) == len(records)
        assert equal_weight_output["cash_weight"] == 0.0
        assert baseline_outputs(records, "RANDOM_RANK") == (
            expected_invalid_output
        )

    duplicate_equal_weight = baseline_outputs(
        invalid_cases["duplicate_key"], "EQUAL_WEIGHT"
    )
    assert duplicate_equal_weight == {
        "validity": "INVALID_UNFORMABLE_BENCHMARK",
        "target": (),
        "cash_weight": None,
        "episodic_return": None,
        "random_draw_consumed": False,
        "output_record_retained": True,
    }
    assert baseline_outputs(
        invalid_cases["duplicate_key"], "RANDOM_RANK"
    ) == expected_invalid_output

    tied_factor_gross_return = 0.0
    invested_benchmark_return = 0.01
    liquidation_turnover = 1.0
    active_returns = {}
    forbidden_cash_benchmark_active_returns = {}
    for bps in (10, 25):
        factor_net_return = tied_factor_gross_return - (
            (1.0 + tied_factor_gross_return)
            * liquidation_turnover
            * bps
            / 10000
        )
        active_returns[bps] = factor_net_return - invested_benchmark_return
        forbidden_cash_benchmark_active_returns[bps] = factor_net_return

    assert active_returns == {10: -0.011, 25: -0.0125}
    assert forbidden_cash_benchmark_active_returns == {
        10: -0.001,
        25: -0.0025,
    }
    assert active_returns != forbidden_cash_benchmark_active_returns


def test_cutoff_excludes_unexecutable_boundary_target_before_strategy_freeze() -> None:
    july_2024_xnys_sessions = tuple(
        date(2024, 7, day)
        for day in range(1, 32)
        if date(2024, 7, day).weekday() < 5 and day != 4
    )
    accepted_cutoff = date(2024, 7, 31)
    signal_date = date(2024, 6, 28)
    execution_date = july_2024_xnys_sessions[0]
    label_endpoint = july_2024_xnys_sessions[21]
    next_monthly_signal = july_2024_xnys_sessions[-1]
    next_monthly_execution = date(2024, 8, 1)

    factor_diagnostic_included = label_endpoint <= accepted_cutoff
    continuous_target_included = next_monthly_execution <= accepted_cutoff
    boundary_disposition = {
        "factor_diagnostic_included": factor_diagnostic_included,
        "continuous_target_frozen": continuous_target_included,
        "strategy_invalid": False,
        "hard_validity_failure": False,
    }

    assert len(july_2024_xnys_sessions) == 22
    assert signal_date == date(2024, 6, 28)
    assert execution_date == date(2024, 7, 1)
    assert label_endpoint == accepted_cutoff
    assert next_monthly_signal == accepted_cutoff
    assert next_monthly_execution > accepted_cutoff
    assert boundary_disposition == {
        "factor_diagnostic_included": True,
        "continuous_target_frozen": False,
        "strategy_invalid": False,
        "hard_validity_failure": False,
    }


def test_invalid_month_stays_in_continuous_economic_support_path() -> None:
    key_a = b"a"
    key_c = b"c"
    targets = ({key_a: 1.0}, {}, {key_c: 1.0})
    turnovers = (
        1.0,
        _factor_target_turnover(targets[0], targets[1]),
        _factor_target_turnover(targets[1], targets[2]),
    )
    strategy_gross_returns = (0.02, 0.0, 0.02)
    benchmark_returns = (0.0, 0.05, 0.0)

    def annualized_active_return(
        gross_returns: tuple[float, ...],
        matched_benchmark_returns: tuple[float, ...],
        path_turnovers: tuple[float, ...],
        bps: int,
    ) -> float:
        net_returns = tuple(
            gross_return
            - (1.0 + gross_return) * turnover * bps / 10000
            for gross_return, turnover in zip(
                gross_returns, path_turnovers, strict=True
            )
        )
        strategy_annualized = (
            math.prod(1.0 + value for value in net_returns)
            ** (252 / len(net_returns))
            - 1.0
        )
        benchmark_annualized = (
            math.prod(1.0 + value for value in matched_benchmark_returns)
            ** (252 / len(matched_benchmark_returns))
            - 1.0
        )
        return strategy_annualized - benchmark_annualized

    full_path_active = tuple(
        annualized_active_return(
            strategy_gross_returns,
            benchmark_returns,
            turnovers,
            bps,
        )
        for bps in (10, 25)
    )
    forbidden_filtered_active = tuple(
        annualized_active_return(
            (strategy_gross_returns[0], strategy_gross_returns[2]),
            (benchmark_returns[0], benchmark_returns[2]),
            (
                turnovers[0],
                _factor_target_turnover(targets[0], targets[2]),
            ),
            bps,
        )
        for bps in (10, 25)
    )
    forbidden_segment_restart_active = tuple(
        annualized_active_return(
            (strategy_gross_returns[0], strategy_gross_returns[2]),
            (benchmark_returns[0], benchmark_returns[2]),
            (1.0, 1.0),
            bps,
        )
        for bps in (10, 25)
    )
    base = {
        "hard_valid": True,
        "prefrozen_coverage_met": True,
        "common_months": 60,
        "bootstrap_support_all_three_factors": True,
        "primary_matched_benchmark_comparisons_valid": True,
        "secondary_spy_comparisons_valid": True,
        "mean_rank_ics": (0.02, -0.01, -0.02),
        "holm_rejections": (True, False, False),
        "common_case_positive_year_fractions": (0.6, 0.4, 0.4),
        "common_case_all_loyo_means_positive": (True, False, False),
    }
    full_path_state = _classify_diagnostic(
        **base,
        active_return_10bps=(full_path_active[0], -0.01, -0.01),
        active_return_25bps=(full_path_active[1], -0.01, -0.01),
    )
    forbidden_filtered_state = _classify_diagnostic(
        **base,
        active_return_10bps=(
            forbidden_filtered_active[0],
            -0.01,
            -0.01,
        ),
        active_return_25bps=(
            forbidden_filtered_active[1],
            -0.01,
            -0.01,
        ),
    )
    forbidden_segment_restart_state = _classify_diagnostic(
        **base,
        active_return_10bps=(
            forbidden_segment_restart_active[0],
            -0.01,
            -0.01,
        ),
        active_return_25bps=(
            forbidden_segment_restart_active[1],
            -0.01,
            -0.01,
        ),
    )

    assert turnovers == (1.0, 1.0, 1.0)
    assert _factor_target_turnover(targets[0], targets[2]) == 2.0
    assert all(value < 0 for value in full_path_active)
    assert all(value > 0 for value in forbidden_filtered_active)
    assert all(value > 0 for value in forbidden_segment_restart_active)
    assert forbidden_segment_restart_active != forbidden_filtered_active
    assert full_path_state == "MIXED_DIAGNOSTIC"
    assert forbidden_filtered_state == "POSITIVE_DIAGNOSTIC"
    assert forbidden_segment_restart_state == "POSITIVE_DIAGNOSTIC"


def test_continuous_held_returns_use_adjusted_close_across_split() -> None:
    def simple_held_return(before: object, after: object) -> float | None:
        anchors = (before, after)
        if not all(
            not isinstance(anchor, bool)
            and isinstance(anchor, Real)
            and math.isfinite(float(anchor))
            and float(anchor) > 0.0
            for anchor in anchors
        ):
            return None
        return float(after) / float(before) - 1.0

    target_weights = (0.5, 0.5)
    adjusted_returns = (
        simple_held_return(50.0, 50.0),
        simple_held_return(100.0, 100.0),
    )
    forbidden_raw_returns = (
        simple_held_return(100.0, 50.0),
        simple_held_return(100.0, 100.0),
    )
    assert all(value is not None for value in adjusted_returns)
    assert all(value is not None for value in forbidden_raw_returns)
    adjusted_numeric = tuple(float(value) for value in adjusted_returns)
    forbidden_raw_numeric = tuple(
        float(value) for value in forbidden_raw_returns
    )

    def path_values(
        returns: tuple[float, float],
    ) -> tuple[float, tuple[float, float]]:
        ending_values = tuple(
            weight * (1.0 + held_return)
            for weight, held_return in zip(
                target_weights,
                returns,
                strict=True,
            )
        )
        ending_total = sum(ending_values)
        gross_return = ending_total - 1.0
        drifted_weights = tuple(
            value / ending_total for value in ending_values
        )
        return gross_return, drifted_weights

    adjusted_gross, adjusted_drifted = path_values(adjusted_numeric)
    forbidden_raw_gross, forbidden_raw_drifted = path_values(
        forbidden_raw_numeric
    )
    adjusted_turnover = sum(
        abs(target - drifted)
        for target, drifted in zip(
            target_weights,
            adjusted_drifted,
            strict=True,
        )
    )
    forbidden_raw_turnover = sum(
        abs(target - drifted)
        for target, drifted in zip(
            target_weights,
            forbidden_raw_drifted,
            strict=True,
        )
    )
    adjusted_cost = (
        (1.0 + adjusted_gross) * adjusted_turnover * 10 / 10000
    )
    forbidden_raw_cost = (
        (1.0 + forbidden_raw_gross)
        * forbidden_raw_turnover
        * 10
        / 10000
    )
    adjusted_primary_benchmark_return = adjusted_gross
    forbidden_raw_primary_benchmark_return = forbidden_raw_gross
    adjusted_active_return = (
        adjusted_gross
        - adjusted_cost
        - adjusted_primary_benchmark_return
    )
    forbidden_raw_active_return = (
        forbidden_raw_gross
        - forbidden_raw_cost
        - forbidden_raw_primary_benchmark_return
    )

    assert adjusted_numeric == (0.0, 0.0)
    assert adjusted_gross == 0.0
    assert adjusted_drifted == (0.5, 0.5)
    assert adjusted_turnover == 0.0
    assert adjusted_cost == 0.0
    assert adjusted_active_return == 0.0
    assert forbidden_raw_numeric == (-0.5, 0.0)
    assert forbidden_raw_gross == -0.25
    assert forbidden_raw_drifted == (
        0.3333333333333333,
        0.6666666666666666,
    )
    assert math.isclose(forbidden_raw_turnover, 1.0 / 3.0, abs_tol=1e-15)
    assert math.isclose(forbidden_raw_cost, 0.00025, abs_tol=1e-15)
    assert math.isclose(forbidden_raw_active_return, -0.00025, abs_tol=1e-15)

    invalid_anchors: tuple[object, ...] = (
        None,
        True,
        float("nan"),
        float("inf"),
        0.0,
        -1.0,
    )
    for invalid_anchor in invalid_anchors:
        assert simple_held_return(invalid_anchor, 100.0) is None
        assert simple_held_return(100.0, invalid_anchor) is None


def test_diagnostic_forward_return_is_simple_and_fail_closed() -> None:
    def diagnostic_forward_return(
        execution_anchor: object,
        endpoint_anchor: object,
    ) -> float | None:
        anchors = (execution_anchor, endpoint_anchor)
        if any(
            isinstance(anchor, bool)
            or not isinstance(anchor, Real)
            or not math.isfinite(float(anchor))
            or float(anchor) <= 0.0
            for anchor in anchors
        ):
            return None
        return float(endpoint_anchor) / float(execution_anchor) - 1.0

    simple_return = diagnostic_forward_return(100.0, 121.0)
    forbidden_log_return = math.log(121.0 / 100.0)
    assert math.isclose(simple_return, 0.21, abs_tol=1e-15)
    assert math.isclose(
        forbidden_log_return,
        0.1906203596086497,
        abs_tol=1e-15,
    )
    assert not math.isclose(
        simple_return,
        forbidden_log_return,
        rel_tol=1e-12,
        abs_tol=1e-15,
    )

    invalid_anchors: tuple[object, ...] = (
        None,
        True,
        float("nan"),
        float("inf"),
        0.0,
        -1.0,
    )
    for invalid_anchor in invalid_anchors:
        assert diagnostic_forward_return(invalid_anchor, 121.0) is None
        assert diagnostic_forward_return(100.0, invalid_anchor) is None


def test_preregistration_bundle_child_binds_exact_frozen_yaml_bytes() -> None:
    preregistration_path = (
        PROJECT_ROOT
        / "docs/preregistrations/eodhd_sp500_three_factor_diagnostic_v1.yaml"
    )
    frozen_bytes = preregistration_path.read_bytes()
    bundle_child_bytes = bytes(frozen_bytes)
    frozen_hash = hashlib.sha256(frozen_bytes).hexdigest()

    assert bundle_child_bytes == frozen_bytes
    assert hashlib.sha256(bundle_child_bytes).hexdigest() == frozen_hash
    tampered_bytes = frozen_bytes.replace(
        b"semantic_trial_count: 14",
        b"semantic_trial_count: 15",
        1,
    )
    assert tampered_bytes != frozen_bytes
    assert hashlib.sha256(tampered_bytes).hexdigest() != frozen_hash
    preregistration_text = frozen_bytes.decode("utf-8")
    assert "    - eodhd_sp500_three_factor_diagnostic_v1.yaml" in (
        preregistration_text
    )
    assert "    - preregistration.json" not in preregistration_text


def test_trial_inventory_bundle_child_binds_exact_frozen_json_bytes() -> None:
    inventory_path = (
        PROJECT_ROOT
        / "docs/preregistrations/"
        "eodhd_sp500_three_factor_trial_inventory_v1.json"
    )
    preregistration_path = (
        PROJECT_ROOT
        / "docs/preregistrations/eodhd_sp500_three_factor_diagnostic_v1.yaml"
    )
    frozen_bytes = inventory_path.read_bytes()
    bundle_child_bytes = bytes(frozen_bytes)
    frozen_hash = hashlib.sha256(frozen_bytes).hexdigest()

    assert bundle_child_bytes == frozen_bytes
    assert hashlib.sha256(bundle_child_bytes).hexdigest() == frozen_hash
    tampered_bytes = frozen_bytes.replace(
        b'"cost_bps": 10',
        b'"cost_bps": 11',
        1,
    )
    assert tampered_bytes != frozen_bytes
    assert hashlib.sha256(tampered_bytes).hexdigest() != frozen_hash
    preregistration = preregistration_path.read_text(encoding="utf-8")
    assert (
        "source_path: docs/preregistrations/"
        "eodhd_sp500_three_factor_trial_inventory_v1.json"
    ) in preregistration
    assert (
        "hash_relation: "
        "CHILD_SHA256_EQUALS_DETACHED_TRIAL_INVENTORY_FREEZE_SHA256"
    ) in preregistration


def test_research_program_charter_defines_evidence_and_scope_gates() -> None:
    charter = (PROJECT_ROOT / "docs/research_program_charter.md").read_text(
        encoding="utf-8"
    )
    normalized_charter = " ".join(charter.split())
    specification = " ".join(
        (PROJECT_ROOT / "PROJECT_SPEC.md").read_text(encoding="utf-8").split()
    )

    for phrase in [
        "## Current Research Scope Boundary",
        "This section records the current research-only evidence scope",
        "../AGENTS.md#authority-and-scope",
        "## Evidence Layers",
        "Factor | A date-by-asset score",
        "Strategy | A frozen signal policy",
        "Portfolio | One or more strategies",
        "Execution | The translation from frozen targets",
        "### Complete trial accounting",
        "## Sample Classification and Holdout Access",
        "historical evaluation or pseudo-holdout",
        "## Candidate States",
        "`PAPER_CANDIDATE`",
        "Controlled live execution is outside this charter and project scope",
    ]:
        assert phrase in normalized_charter

    assert "## Current Authorization" not in normalized_charter

    for phrase in [
        "The current phase is research-only",
        "Passing deterministic tests proves implementation behavior",
        "not historical validity",
        "Every protected-sample access",
        "holdout exposure ledger",
        "A candidate label is not",
        "authorization to paper trade or trade live",
    ]:
        assert phrase in specification


def test_purged_bounded_split_contract_freezes_stage_one_design() -> None:
    contract = (
        PROJECT_ROOT / "docs/purged_bounded_split_contract.md"
    ).read_text(encoding="utf-8")
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")

    for phrase in [
        "train_start",
        "validation_start",
        "test_start",
        "`test_end` is always explicit",
        "label_start = source_index[i]",
        "label_end = source_index[i + h]",
        "`price_forward_return` requires `label_horizon_rows >= 1`",
        "`synthetic_same_row_response` requires",
        "`label_derivation`",
        "`label_crosses_window_end`",
        "masks every purged or embargoed target value to `NaN`",
        "`embargo_rows`",
        "An explicit gap can therefore satisfy all or part of an embargo",
        "`feature_warm_up_rows`",
        "The purged tail is the label warm-down set",
        "`no_eligible_labels`",
        "`SPLIT-005`",
        "`SPLIT-006`",
        "`SPLIT-017`",
        "`SPLIT-021`",
        "`SPLIT-022`",
        "`no_usable_label_pairs`",
        "gap_dates_consuming_embargo",
        "No post-test value may complete a test label",
        "supersede that earlier wording for Stage 1b",
        "Stage 2",
    ]:
        assert phrase in contract

    assert "docs/purged_bounded_split_contract.md" in repo_map

    for case_number in range(1, 23):
        assert contract.count(f"`SPLIT-{case_number:03d}`") == 1

def test_signal_execution_timing_contract_freezes_stage_two_design() -> None:
    contract = (
        PROJECT_ROOT / "docs/signal_execution_timing_contract.md"
    ).read_text(encoding="utf-8")
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")

    for phrase in [
        "Status: accepted Stage 2 design; Stage 2b runtime implementation complete on",
        "This is the normative documentation and methodology target for the current",
        "after_close_signal_next_observed_close_v1",
        "A close-derived signal stamped at row `t` becomes available only after",
        "The earliest supported execution is `close[t+1]`, the next observed source",
        "It does not constrain source rows after execution",
        "execution_time < holding_effective_start",
        "first_return_end    = missing",
        "It must not construct or infer `a[N+1]`",
        "`signal_lag_periods=0` is invalid for close-derived signals.",
        "Row lag counts observed source rows within the exact bounded accounting slice",
        "Rows in the full source index before `a[0]` never satisfy lag",
        "A target executed at close `t` does not earn the return stamped `t`",
        "Both bounds must be exact scalar timestamp labels in the validated price index",
        "price_index.get_loc(evaluation_start)",
        "partial-date strings such as `2024-01`",
        "measured_return_dates = accounting_dates[1:]",
        "timing_ledger_dates =",
        "`is_scheduled_rebalance` is false",
        "`incoming_return_start = a[j-1]`",
        "`first_holding_return_start = a[N]`",
        "net_return.loc[measured_return_dates]",
        "`initial_capital_invalid`",
        "`signal_value_invalid`",
        "`source_provenance_invalid`",
        "`source_provenance` with no default or",
        "`tracked_pre_mutation_source_snapshot_v1`",
        "pre-start `1+0j` write",
        "controlled API",
        "enforcement begins at capture",
        "cannot infer or",
        "latest tracked assignment",
        "latest controlled bounded assignment determines recovery",
        "changes the promoted column",
        "container from complex to object",
        "wider NumPy scalar such as x86 `longdouble`",
        "raises `source_provenance_invalid` at capture before any Python",
        "Direct and nested provenance objects are rejected",
        "extracted primitives",
        "bounded_final_signals = final_signals.iloc",
        "Only after that exact bounded slice exists",
        "Signal values strictly before `evaluation_start` or after `evaluation_end`",
        "`incoming_price_invalid`",
        "`execution_price_invalid`",
        "`returns_invalid`",
        "`portfolio_insolvent_or_non_finite_before_trade`",
        "`portfolio_insolvent_or_non_finite_after_costs`",
        "`equity_curve_invalid`",
        "calculate_max_drawdown(equity_curve, *, initial_capital)",
        "It has no external index-equality requirement",
        "`DatetimeIndex` values, timezone, and order",
        "raise_before_successful_result_on_invalid_or_insolvent_capital",
        "validate_bounded_scores_after_exact_slice_raise_on_invalid_available_score",
        "decision_information_only_no_execution_close_rerank",
        "execution_price_failure_policy",
        "include_return_trade_cost_open_holdings_no_future_return",
        "Same-row synthetic response diagnostics are not executable strategy returns",
        "The model is an idealized full target reset at an observed close.",
        "## Required Metadata",
        "## Hand-Calculated Reference Case",
        "## Deterministic Stage 2b Test Matrix",
        "## Stage 2b Implementation Boundary",
        "## Accepted Decisions and Deferred Choices",
    ]:
        assert phrase in contract

    for field in [
        "`timing_contract`",
        "`feature_time`",
        "`signal_availability_time`",
        "`decision_time`",
        "`execution_time`",
        "`signal_lag_rows`",
        "`return_frequency`",
        "`periods_per_year`",
        "`return_interval`",
        "`holding_effective_interval`",
        "`cost_application_time`",
        "`metric_anchor_policy`",
        "`terminal_row_policy`",
        "`signal_value_failure_policy`",
        "`incoming_price_failure_policy`",
        "`returns_failure_policy`",
        "`gross_insolvency_failure_policy`",
        "`insolvency_failure_policy`",
        "`equity_curve_failure_policy`",
        "`benchmark_return_window`",
        "`backtest_source_provenance_policy`",
        "`backtest_source_provenance_status`",
    ]:
        assert field in contract

    for case_number in range(1, 15):
        assert contract.count(f"`TIMING-{case_number:03d}`") == 1

    assert "docs/signal_execution_timing_contract.md" in repo_map


def test_point_in_time_data_methodology_contract_freezes_stage_three_design() -> None:
    contract = (
        PROJECT_ROOT / "docs/point_in_time_data_methodology_contract.md"
    ).read_text(encoding="utf-8")
    readiness_audit = (
        PROJECT_ROOT / "docs/real_data_readiness_audit.md"
    ).read_text(encoding="utf-8")
    readiness_skill = (
        PROJECT_ROOT / ".agents/skills/real-data-readiness-audit/SKILL.md"
    ).read_text(encoding="utf-8")
    study_checklist = (
        PROJECT_ROOT / "docs/local_csv_study_checklist.md"
    ).read_text(encoding="utf-8")
    audit_template = (
        PROJECT_ROOT / "docs/local_csv_readiness_audit_report_template.md"
    ).read_text(encoding="utf-8")
    experiment_log = (PROJECT_ROOT / "EXPERIMENT_LOG.md").read_text(
        encoding="utf-8"
    )
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")

    for phrase in [
        "Status: accepted Stage 3 methodology contract",
        "Contract ID: `point_in_time_data_methodology_contract_v1`",
        "Contract version: `1.0.0`",
        "`methodology_contract_accepted`",
        "`dataset_manifest_reviewed`",
        "`formal_interpretation_eligible`",
        "Contract acceptance does not verify any dataset",
        "`UNKNOWN`",
        "`NOT_APPLICABLE`",
        "`asserted`",
        "`owner_accepted`",
        "`canonical_manifest_sha256`",
        "`raw_byte_sha256`",
        "`ordered_manifest_sha256`",
        "`ordered_component_inventory_v1`",
        "`physical_components`",
        "all-and-only, one-to-one flattening",
        "`canonicalization_id`",
        "`environment_id`",
        "`environment_lock_sha256`",
        "`review_decision_id`",
        "`public_projection_sha256`",
        "`public_redacted_projection_v1`",
        "`safe_public_id`",
        "`contract_content_sha256`",
        "`contract_protected_merge_sha`",
        "`decision_canonicalization_id`",
        "`decision_record_sha256`",
        "`pit_canonical_json_v1`",
        "RFC 8785 JCS",
        "an absent required property is rejected and is never synthesized",
        "The public projection cannot contain its dataset-review decision",
        "tests/fixtures/pit_canonical_json_v1_golden.json",
        "`permanent_security_id`",
        "`listing_id`",
        "`ticker_alias`",
        "`effective_from`",
        "`effective_to`",
        "`effective_to_state`",
        "`FINITE`",
        "`OPEN_IN_VINTAGE`",
        "`known_at`",
        "`public_available_at`",
        "`provider_available_at`",
        "`revision_published_at`",
        "`supersedes`",
        "`delisting_terminal_value_policy`",
        "`adjustment_set_id`",
        "`volume_basis`",
        "`NOT_YET_LISTED`",
        "`PROVIDER_GAP`",
        "`calendar_id`",
        "`calendar_version`",
        "`source_timezone`",
        "`session_date`",
        "`available_at`",
        "`benchmark_purpose`",
        "`risk_free_policy`",
        "`private_full_manifest`",
        "`public_redacted_projection`",
        "`sealed_at`",
        "`accessed_at`",
        "`recorded_at`",
        "`backfilled`",
        "`classification_before`",
        "`classification_after`",
        "`design_impact`",
        "`historical_evaluation`",
        "2025-05-01 through 2026-05-31",
        "Stage 4 owns append-only enforcement",
        "and known_at <= t",
        "and t <= as_of_cutoff",
        "inside every required role/input coverage range",
        "A later-known closure never",
        "Neither a manifest author nor a checklist can self-certify",
        "No provider selection, download, credentials, or remote data access",
        "## Deterministic Stage 3 Test Matrix",
        "## Accepted Decisions and Deferred Implementation",
    ]:
        assert phrase in contract

    for case_number in range(1, 16):
        assert contract.count(f"`PIT-{case_number:03d}`") == 1

    for case_id, decision_fragment in {
        "PIT-003": "requires digest recomputation",
        "PIT-004": "It is unavailable to that signal",
        "PIT-011": "Serialization fails closed through the allowlist",
        "PIT-012": "cannot retain or establish holdout status and is downgraded",
        "PIT-013": "uncertain overlap downgrades the nominal window",
        "PIT-014": "dataset verification and formal interpretation blocked",
        "PIT-015": "`t_after` is unsupported",
    }.items():
        case_row = next(
            line for line in contract.splitlines() if f"`{case_id}`" in line
        )
        assert decision_fragment in case_row

    pit_015_row = next(
        line for line in contract.splitlines() if "`PIT-015`" in line
    )
    for boundary_token in [
        "`effective_to_state = OPEN_IN_VINTAGE`",
        "`effective_to = null`",
        "`C = 2024-06-28T21:00:00Z`",
        "`t_in = 2024-06-28T20:00:00Z`",
        "`t_after = 2024-07-01T14:30:00Z`",
    ]:
        assert boundary_token in pit_015_row

    for canonical_doc in [
        readiness_audit,
        readiness_skill,
        study_checklist,
        audit_template,
        experiment_log,
        readme,
        repo_map,
    ]:
        assert "docs/point_in_time_data_methodology_contract.md" in canonical_doc

    normalized_contract = " ".join(contract.split())
    assert "no envelope, delimiter, byte-order mark, or trailing newline" in (
        normalized_contract
    )
    assert "Classification moves only toward greater exposure" in normalized_contract
    assert "An existing window is never upgraded" in normalized_contract
    assert (
        "methodology_contract_accepted does not imply "
        "dataset_manifest_reviewed"
    ) in normalized_contract
    assert (
        "dataset_manifest_reviewed does not imply "
        "formal_interpretation_eligible"
    ) in normalized_contract
    assert (
        "does not establish `formal_ready`, point-in-time status, license "
        "entitlement, or historical validity"
    ) in normalized_contract
    assert (
        "Tracked records must not contain private absolute paths"
        in normalized_contract
    )
    assert "Static or survivor-selected cohorts remain `DIAGNOSTIC_ONLY`" in contract

    for intake_doc in [study_checklist, audit_template]:
        normalized_intake = " ".join(intake_doc.split())
        assert "dataset-manifest review candidate (not formal evidence)" in normalized_intake
        assert "methodology_contract_accepted" in normalized_intake
        assert "dataset_manifest_reviewed" in normalized_intake
        assert "formal_interpretation_eligible" in normalized_intake
        assert "private absolute paths" in normalized_intake
        assert "hash plan is not evidence" in normalized_intake
        assert "this form cannot grant any gate" in normalized_intake
        assert "Dataset review decision ID:" in normalized_intake
        assert "Reviewer authority reference:" in normalized_intake
        assert "Finding IDs and dispositions:" in normalized_intake
        assert "cannot self-certify" in normalized_intake
        assert "outcome-reconstructible" in normalized_intake
        assert "2025-05-01 through 2026-05-31" in normalized_intake
        assert "`historical_evaluation`, never a pristine holdout" in normalized_intake
        assert "must not be upgraded" in normalized_intake
        assert "canonicalization_id" in normalized_intake
        assert "environment_id" in normalized_intake
        assert "environment_lock_sha256" in normalized_intake
        assert "known_at <= decision_time" in normalized_intake
        assert "non-self-issued exact-version dataset-review decision" in normalized_intake
        assert (
            "methodology_contract_accepted` does not imply "
            "`dataset_manifest_reviewed"
        ) in normalized_intake
        assert (
            "dataset_manifest_reviewed` does not imply "
            "`formal_interpretation_eligible"
        ) in normalized_intake


def test_experiment_trial_ledger_contract_freezes_stage_four_a_design() -> None:
    contract = (
        PROJECT_ROOT / "docs/experiment_trial_ledger_contract.md"
    ).read_text(encoding="utf-8")
    point_in_time_contract = (
        PROJECT_ROOT / "docs/point_in_time_data_methodology_contract.md"
    ).read_text(encoding="utf-8")
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")
    registry_contract = (
        PROJECT_ROOT
        / "docs/experiment_trial_ledger_schema_registry_contract.md"
    ).read_text(encoding="utf-8")
    normalized_contract = " ".join(contract.split())
    normalized_registry_contract = " ".join(registry_contract.split())

    for phrase in [
        "Status: accepted Stage 4a design contract on protected main via PR #164",
        "Contract ID: `experiment_trial_ledger_contract_v1`",
        "Contract version: `1.0.0`",
        "Stage 4b runtime enforcement is not implemented",
        "diagnostic/legacy sidecars",
        "`trial_id` identifies exactly one semantic configuration",
        "`attempt_id` identifies one invocation",
        "Each ledger-owned logical entity ID is allocated exactly once across the ledger",
        "`actor_id` is an externally assigned, opaque claimed-attribution reference",
        "does not prove the actor's authenticity, control, authorization",
        "grants no append, access, review, promotion",
        "must fail closed until Stage 4b accepts an owner-approved external authority mechanism",
        "Stage 4a does not choose that mechanism",
        "reuse that already allocated ID as a typed subject or reference",
        "Entity-ID conflict therefore means a second allocation attempt",
        "Campaign reports disclose both semantic trial count and execution-attempt count",
        "No validator, executor, protected-data accessor, or result-producing process",
        "LEDGER_EPOCH_CREATED",
        "Parent precedence is an exact partial order",
        "Direct campaign-scoped registration",
        "Ledger-global registration plus campaign binding",
        "Accepted external Stage 3 registration",
        "may list multiple affected campaigns",
        "registration and `CAMPAIGN_ALLOCATED` are independent siblings",
        "`STAGE3_SAMPLE_REFERENCE_BOUND` allocates the ledger-local typed `sample_id`",
        "exact external registry authority, external sample-record ID, schema/contract version",
        "A direct registration cannot also have `CAMPAIGN_ENTITY_BOUND`",
        "`CAMPAIGN_INVENTORY_SEALED`",
        "included and bound inside the inventory-seal request/event preimage",
        "referenced predecessor event bytes are external to and excluded from that seal preimage",
        "sequence/event hash are never named by the anchor, so the anchor is nonrecursive",
        "stored `event_sha256` remains outside its event preimage",
        "same serialized atomic commit boundary",
        "assigns the seal sequence/envelope `previous_event_sha256`",
        "seal fails/conflicts; it must not silently rebase",
        "epoch-empty `(null, null)` is not legal",
        "`ledger_operation_request_v1`",
        "result-informed amendment",
        "cannot support `RESEARCH_PASS` or higher",
        "Trial disposition and attempt execution state are separate",
        "It never means `RESEARCH_PASS`",
        "`ACCESS_INTENT` must be durable before the accessor",
        "validates and consumes that exact capability",
        "`protected_material_observed = NONE | SOME | UNKNOWN`",
        "No canonical access event, including the private full ledger",
        "a complete `SOME` observation with frozen `purpose = design` is `development`",
        "even without separately confirmed downstream design/tuning influence",
        "complete design-purpose `SOME` classification",
        "The explicit allowed-transition graph",
        "validation -> validation | historical_evaluation | pseudo_holdout | development",
        "irrevocable floor of `historical_evaluation`",
        "`ledger_event_identity_v1`",
        "`pit_canonical_json_v1`",
        "The stored `event_sha256`",
        "The common identity-envelope schema rejects missing or unknown envelope fields",
        "`ledger_v1_utc_timestamp` subset",
        "including year `0000`",
        "A fractional second may have arbitrary precision but must be nonzero",
        "Ledger event schema v1 rejects every `second = 60`",
        "this contract pins no leap-second table",
        "deliberate application-level subset of RFC 3339 timestamp syntax",
        "It does not change `pit_canonical_json_v1`",
        "The v1 event-type vocabulary is closed at exactly these 37 values",
        "Stage 4a freezes an exact unknown-field-rejecting payload schema only for one golden event type",
        "`TRIAL_ALLOCATED` bindings are normative semantic requirements",
        "must reject `TRIAL_ALLOCATED` as `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "`incomplete_trial_allocation_stub` is rejection evidence only",
        "separately reviewed machine-readable per-event payload schema registry",
        "`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "must not claim a contract-wide fail-closed ledger, Stage 4b conformance",
        "tamper-evident, not WORM",
        "`CAMPAIGN_EVIDENCE_FROZEN`",
        "`campaign_evidence_prefix_v1`",
        "The freeze event is necessarily excluded",
        "`campaign_evidence_checkpoint_v1`",
        "`freeze_event_sequence = evidence_sequence + 1`",
        "entire target-campaign projection is all-and-only exactly one",
        "`sealed_semantic_trial_count` is the cardinality",
        "equal counts never substitute for exact set equality",
        "A same-cardinality ID substitution fails",
        "one fixed all-excluded trial set and zero allocated/terminal",
        "depends on the complete Stage 4b per-event payload schema registry",
        "runtime remains fail closed until that registry is accepted and enforced",
        "`freeze_event_sequence`",
        "independently retained immutable checkpoint",
        "A producer cannot self-certify",
        "does not self-stale the decision",
        "`CAMPAIGN_ADJUDICATED`",
        "`campaign_adjudication_checkpoint_v1` anchors the complete verified chain",
        "checkpoint_generation",
        "Generation 1 has both",
        "Every successor is exactly the preceding generation plus one",
        "every retained generation, not only the head",
        "correspond one-to-one in that order",
        "The provider-neutral currentness authority key is exactly",
        "exactly `current_checkpoint_generation + 1` becomes pending",
        "Before any post-adjudication action scoped to that campaign",
        "A pending generation is not fully adjudicated",
        "No campaign-scoped `CHECKPOINT_REFERENCE_RECORDED` is appended",
        "General machine proof of which payloads are genuinely global remains deferred",
        "A local old ledger plus its old checkpoint cannot detect",
        "the full runtime must remain fail closed",
        "independent append-only and anti-rollback latestness",
        "Stage 4a chooses no provider, physical backend, signature scheme",
        "externally unverified adjudication checkpoint",
        "The full canonical ledger is private, repository-external evidence",
        "No runtime may create a default ledger database or event stream inside the repository",
        "`ledger_public_projection_v1` has all-and-only these top-level keys",
        "`schema_version` is exactly `ledger_public_projection_v1`",
        "`canonicalization_id` is exactly `pit_canonical_json_v1`",
        "Unknown-field, path, file-URI, query, username, raw-value",
        "`backfilled = true`, `DIAGNOSTIC_ONLY`",
        "Documentation-token tests for this matrix are not runtime append-only evidence",
        "physical storage backend",
        "Later implementation must not retrofit the legacy reporter in place",
    ]:
        assert phrase in normalized_contract

    for rejected_identity_architecture in [
        "genesis_principal_binding",
        "trusted_authority_manifest_v1",
        "owner_pinned_manifest_sha256",
        "authenticated_producer_context_v1",
    ]:
        assert rejected_identity_architecture not in contract

    vocabulary_block = (
        contract.split(
            "The v1 event-type vocabulary is closed at exactly these 37 values:", 1
        )[1]
        .split("```text", 1)[1]
        .split("```", 1)[0]
        .split()
    )
    assert len(vocabulary_block) == len(set(vocabulary_block))
    assert len(vocabulary_block) == 37
    assert set(vocabulary_block) == _LEDGER_EVENT_TYPES
    assert {
        "LEDGER_EPOCH_CREATED", "CAMPAIGN_ENTITY_BOUND",
        "STAGE3_SAMPLE_REFERENCE_BOUND", "TRIAL_ALLOCATED",
        "CAMPAIGN_ACCOUNTING_CLOSED", "EVENT_SUPERSEDED",
    } <= set(vocabulary_block)

    for case_number in range(1, 16):
        assert contract.count(f"`LEDGER-{case_number:03d}`") == 1

    assert "docs/experiment_trial_ledger_contract.md" in repo_map

    assert "accepted Stage 3 methodology contract" in point_in_time_contract
    assert "acceptance pending protected merge" not in point_in_time_contract
    for phrase in [
        "Contract ID: `experiment_trial_ledger_schema_registry_r0`",
        "`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "`LEDGER_EPOCH_CREATED` is the sole `FROZEN_SUPPORTED` event",
        "does not accept a complete payload-schema registry",
        "does not implement a ledger runtime",
        "Trial count, execution-attempt count, and protected-sample access remain zero",
        "No other event becomes append-valid in R0",
    ]:
        assert phrase in normalized_registry_contract
    assert "docs/experiment_trial_ledger_schema_registry_contract.md" in repo_map


def test_allocation_registration_r1b_freezes_e1_and_versioned_release() -> None:
    contract_path = (
        PROJECT_ROOT
        / "docs/experiment_trial_ledger_allocation_registration_schema_contract.md"
    )
    contract = contract_path.read_text(encoding="utf-8")
    normalized_contract = " ".join(contract.split())
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")
    r0_registry_path = (
        PROJECT_ROOT
        / "src/ledger/schemas/"
        "experiment_trial_ledger_payload_schema_registry_v1.json"
    )
    r0_sidecar_path = r0_registry_path.with_suffix(".sha256")
    r0_registry_bytes = r0_registry_path.read_bytes()
    r0_sidecar_bytes = r0_sidecar_path.read_bytes()
    r0_registry = json.loads(r0_registry_path.read_text(encoding="ascii"))
    r1_registry_path = (
        PROJECT_ROOT
        / "src/ledger/schemas/"
        "experiment_trial_ledger_payload_schema_registry_v2.json"
    )
    r1_sidecar_path = r1_registry_path.with_suffix(".sha256")
    r1_registry_bytes = r1_registry_path.read_bytes()
    r1_sidecar_bytes = r1_sidecar_path.read_bytes()
    r1_registry = json.loads(r1_registry_path.read_text(encoding="ascii"))

    for phrase in [
        "Contract ID: `experiment_trial_ledger_allocation_registration_schema_r1a`",
        "R1B amendment ID: `experiment_trial_ledger_allocation_registration_schema_r1b`",
        "Contract version: `0.2.0`",
        "Owner decision: architecture `A`",
        "Owner namespace decision: option `E1`, exact experiment namespace `exp_<32 lowercase hex>`",
        "No event becomes append-valid in R1A",
        "`LEDGER_EPOCH_CREATED` remains the sole `FROZEN_SUPPORTED` event",
        "other 36 known event types remain `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "only additional supported events are reservation-only `CAMPAIGN_ALLOCATED` and `EXPERIMENT_ALLOCATED`",
        "other 34 events remain incomplete",
        "Trial count, execution-attempt count, and protected-sample access remain zero",
        "preserve both R0 artifact files byte-for-byte",
        "preserve every accepted R0 validator behavior and literal test oracle",
        "registry version `0.2.0` and schema-language version `0.2.0`",
        "Every protected-merged registry release is immutable",
        "retains the accepted 37-event vocabulary unchanged",
        "reservation-only",
        "The allocated, registered, or bound logical entity is the event subject",
        "sole authority for `exp_`",
        "`campaign_scope_ids` directly in its top-level payload",
        "every campaign listed in `campaign_scope_ids` must already be allocated",
        "### `tagged_union`",
        "### `array_contains_path`",
        "### `safe_public_id`",
        "Its exact machine node is `{\"kind\":\"safe_public_id\"}`",
        "experiment_trial_ledger_payload_schema_registry_v2.json",
        "registry schema ID `experiment_trial_ledger_payload_schema_registry_v2`",
        "R1B authority must be selected explicitly as packaged registry version `0.2.0`",
        "R1B must implement and meta-test all three closed schema-language `0.2.0` capabilities",
        "Whether the family authority requires a separate acceptance decision",
        "remain human methodology decisions for R1C",
        "Before every new trial allocation, at each attempt execution boundary, and at each protected-access boundary",
        "superseded after trial allocation but before attempt execution",
        "Returning schema `ACCEPT` must never be described as satisfying a stateful rule",
        "An ID plus digest without retrievable, schema-valid semantic content is a forbidden hash-only stand-in",
        "A digest is not automatically publication-safe",
        "R1B must not promote the four registration/binding events",
        "Stage 5 remains blocked",
    ]:
        assert phrase in normalized_contract

    def text_block_after(lead_in: str) -> list[str]:
        return (
            contract.split(lead_in, 1)[1]
            .split("```text", 1)[1]
            .split("```", 1)[0]
            .split()
        )

    family_block = text_block_after(
        "The allocation/registration family remains exactly:"
    )
    assert family_block == [
        "CAMPAIGN_ALLOCATED",
        "EXPERIMENT_ALLOCATED",
        "TRIAL_FAMILY_REGISTERED",
        "SAMPLE_REGISTERED",
        "CAMPAIGN_ENTITY_BOUND",
        "STAGE3_SAMPLE_REFERENCE_BOUND",
    ]

    assert text_block_after("Their exact reservation payload field set is:") == [
        "campaign_scope_ids"
    ]
    assert text_block_after(
        "The forbidden definition-bearing or open-ended field categories are exactly:"
    ) == [
        "objective",
        "hypothesis",
        "estimand",
        "protocol",
        "budget",
        "sample_policy",
        "threshold",
        "inventory",
        "status",
        "reason",
        "metadata",
        "free_text",
        ]
    assert text_block_after(
        "versioned amendment. It adds only these capabilities:"
    ) == [
        "tagged_union",
        "array_contains_path",
        "safe_public_id",
    ]

    subject_section = (
        contract.split(
            "following subject and namespace decisions are frozen for later exact schemas.",
            1,
        )[1]
        .split("Subject IDs must not be duplicated", 1)[0]
    )
    assert [
        line for line in subject_section.splitlines() if line.startswith("| `")
    ] == [
        "| `CAMPAIGN_ALLOCATED` | `campaign` | newly reserved `campaign_id` | accepted `cmp_<32 lowercase hex>` |",
        "| `EXPERIMENT_ALLOCATED` | `experiment` | newly reserved `experiment_id` | owner-ratified `exp_<32 lowercase hex>` |",
        "| `TRIAL_FAMILY_REGISTERED` | `trial_family` | newly registered `trial_family_id` | exact prefix deferred to the R1C owner gate |",
        "| `SAMPLE_REGISTERED` | `sample` | newly registered local `sample_id` | exact prefix deferred to the R1D owner gate |",
        "| `CAMPAIGN_ENTITY_BOUND` | `trial_family` or `sample` | existing global entity identity | must match the later accepted family or sample namespace |",
        "| `STAGE3_SAMPLE_REFERENCE_BOUND` | `sample` | newly allocated ledger-local `sample_id` | exact prefix deferred to the R1D owner gate |",
    ]

    scope_section = contract.split("The scope formulas are:", 1)[1].split(
        "The experiment parent campaign", 1
    )[0]
    assert [
        line
        for line in scope_section.splitlines()
        if line.startswith("| `")
        or line.startswith("| direct")
        or line.startswith("| global")
    ] == [
        "| `CAMPAIGN_ALLOCATED` | one-item array containing `subject_id` |",
        "| `EXPERIMENT_ALLOCATED` | one-item array containing the sole parent campaign ID |",
        "| direct `TRIAL_FAMILY_REGISTERED` | nonempty sorted-unique array of all directly covered campaigns |",
        "| global `TRIAL_FAMILY_REGISTERED` | empty array |",
        "| direct `SAMPLE_REGISTERED` | nonempty sorted-unique array of all directly covered campaigns |",
        "| global `SAMPLE_REGISTERED` | empty array |",
        "| `CAMPAIGN_ENTITY_BOUND` | one-item array containing the binding campaign ID |",
        "| `STAGE3_SAMPLE_REFERENCE_BOUND` | one-item array containing the binding campaign ID |",
    ]

    assert r0_registry["registry_version"] == "0.1.0"
    assert r0_registry["schema_language_version"] == "0.1.0"
    assert [
        schema["event_type"] for schema in r0_registry["event_schemas"]
    ] == ["LEDGER_EPOCH_CREATED"]
    assert len(r0_registry["incomplete_event_types"]) == 36
    assert set(r0_registry["incomplete_event_types"]) == (
        set(r0_registry["closed_event_vocabulary"]) - {"LEDGER_EPOCH_CREATED"}
    )
    assert (
        r0_sidecar_path.read_text(encoding="ascii").strip()
        == "92ab88b0bac4c683c25aab25dd31f6a48f44250afbef7d4995de26b68451e2cf"
    )
    assert (
        hashlib.sha256(r0_registry_bytes).hexdigest()
        == "4b78c36647621deaec15114558d827c17dae2bfa29918f4cbf2ceb2aa6b6e6d9"
    )
    assert (
        hashlib.sha256(r0_sidecar_bytes).hexdigest()
        == "dc870da2958a107998d3939350edb20d3a9185e13a4edb48664befcb89e79d51"
    )
    assert r0_sidecar_bytes == (
        b"92ab88b0bac4c683c25aab25dd31f6a48f44250afbef7d4995de26b68451e2cf\n"
    )
    assert r1_registry["registry_version"] == "0.2.0"
    assert r1_registry["schema_language_version"] == "0.2.0"
    assert [
        schema["event_type"] for schema in r1_registry["event_schemas"]
    ] == [
        "LEDGER_EPOCH_CREATED",
        "CAMPAIGN_ALLOCATED",
        "EXPERIMENT_ALLOCATED",
    ]
    assert len(r1_registry["incomplete_event_types"]) == 34
    assert set(r1_registry["incomplete_event_types"]) == (
        set(r1_registry["closed_event_vocabulary"])
        - {
            "LEDGER_EPOCH_CREATED",
            "CAMPAIGN_ALLOCATED",
            "EXPERIMENT_ALLOCATED",
        }
    )
    assert (
        r1_sidecar_path.read_text(encoding="ascii").strip()
        == "6c1044a1a5d770b8d841164d0232134e975c8c372e7d62333eac3a8ae2eacab4"
    )
    assert (
        hashlib.sha256(r1_registry_bytes).hexdigest()
        == "d31b7a812a79618f097a50db0177e63f5246522b3b63590968172e31b71cd499"
    )
    assert (
        hashlib.sha256(r1_sidecar_bytes).hexdigest()
        == "ba6b1682d1a22004618c274b362359123ce7abbcb7b211335dcd4c74b1159ac8"
    )
    packaged_schema_root = resources.files("ledger").joinpath("schemas")
    assert (
        packaged_schema_root.joinpath(r0_registry_path.name).read_bytes()
        == r0_registry_bytes
    )
    assert (
        packaged_schema_root.joinpath(r0_sidecar_path.name).read_bytes()
        == r0_sidecar_bytes
    )
    assert (
        packaged_schema_root.joinpath(r1_registry_path.name).read_bytes()
        == r1_registry_bytes
    )
    assert (
        packaged_schema_root.joinpath(r1_sidecar_path.name).read_bytes()
        == r1_sidecar_bytes
    )

    assert (
        "docs/experiment_trial_ledger_allocation_registration_schema_contract.md"
        in repo_map
    )


def test_trial_family_registration_r1c_freezes_owner_bundle_and_release() -> None:
    contract_path = (
        PROJECT_ROOT
        / "docs/experiment_trial_ledger_trial_family_registration_schema_contract.md"
    )
    contract = contract_path.read_text(encoding="utf-8")
    normalized_contract = " ".join(contract.split())
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")
    registry_path = (
        PROJECT_ROOT
        / "src/ledger/schemas/"
        "experiment_trial_ledger_payload_schema_registry_v3.json"
    )
    sidecar_path = registry_path.with_suffix(".sha256")
    fixture_path = (
        PROJECT_ROOT
        / "tests/fixtures/"
        "experiment_trial_ledger_trial_family_registration_v1_golden.json"
    )
    registry = json.loads(registry_path.read_text(encoding="ascii"))
    fixture = json.loads(fixture_path.read_text(encoding="ascii"))

    for phrase in [
        "Contract ID: `experiment_trial_ledger_trial_family_registration_schema_r1c`",
        "Contract version: `0.3.0`",
        "Owner decision: option `R1C-A`",
        "Exact trial-family namespace: `fam_<32 lowercase hex>`",
        "registry schema ID `experiment_trial_ledger_payload_schema_registry_v3`",
        "registry version `0.3.0`",
        "unchanged schema-language version `0.2.0`",
        "The other 33 events remain `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "`subject_type` exactly `trial_family`",
        "empty means a ledger-global registration",
        "one through 32 entries means a direct registration",
        "complete repository-external canonical records",
        "The accepted resolver key is the exact tuple",
        "A retrieval miss, ambiguous record, digest mismatch, schema mismatch, noncanonical record, or hash-only stand-in fails closed",
        "The registration pins a separate complete acceptance record",
        "the reviewer must be distinct from both the definition issuer and the `TRIAL_FAMILY_REGISTERED.actor_id`",
        "The provider-neutral currentness key is exactly",
        "Acceptance generations are positive safe integers and strictly increase",
        "exactly one accepted generation is current",
        "Aliases, clones, reruns, new campaign IDs, result exposure, and post-result reclassification must reuse the same `trial_family_id`",
        "Definition revisions keep the same `trial_family_id` and advance through `supersedes`",
        "Genuinely distinct but dependent families use explicit `depends_on`",
        "No record may self-certify independence",
        "a shape-valid event whose resolver record is missing",
        "Trial count, execution-attempt count, and protected-sample access remain zero",
        "four reminders at 30-minute intervals",
    ]:
        assert phrase in normalized_contract

    expected_supported = [
        "LEDGER_EPOCH_CREATED",
        "CAMPAIGN_ALLOCATED",
        "EXPERIMENT_ALLOCATED",
        "TRIAL_FAMILY_REGISTERED",
    ]
    expected_payload_fields = [
        "campaign_scope_ids",
        "family_acceptance_decision_id",
        "family_acceptance_generation",
        "family_acceptance_record_sha256",
        "family_acceptance_schema_version",
        "family_authority_id",
        "family_authority_registry_sha256",
        "family_authority_version",
        "family_definition_canonicalization_id",
        "family_definition_record_id",
        "family_definition_record_sha256",
        "family_definition_record_version",
        "family_definition_schema_version",
    ]
    assert registry["registry_schema_id"] == (
        "experiment_trial_ledger_payload_schema_registry_v3"
    )
    assert registry["registry_version"] == "0.3.0"
    assert registry["registry_status"] == "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    assert registry["schema_language_id"] == "ledger_closed_schema_dsl_v1"
    assert registry["schema_language_version"] == "0.2.0"
    assert [item["event_type"] for item in registry["event_schemas"]] == (
        expected_supported
    )
    assert len(registry["incomplete_event_types"]) == 33
    assert set(registry["incomplete_event_types"]) == (
        set(registry["closed_event_vocabulary"]) - set(expected_supported)
    )
    assert registry["type_definitions"]["trial_family_id"] == {
        "kind": "typed_id",
        "prefix": "fam",
    }
    family_schema = next(
        item
        for item in registry["event_schemas"]
        if item["event_type"] == "TRIAL_FAMILY_REGISTERED"
    )
    assert family_schema["schema_status"] == "FROZEN_SUPPORTED"
    family_schema = family_schema["event_schema"]
    assert family_schema["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "trial_family",
    }
    assert family_schema["properties"]["subject_id"] == {
        "kind": "named",
        "name": "trial_family_id",
    }
    payload_schema = family_schema["properties"]["payload"]
    assert payload_schema["required"] == expected_payload_fields
    assert list(payload_schema["properties"]) == expected_payload_fields
    assert payload_schema["properties"]["campaign_scope_ids"] == {
        "kind": "array",
        "items": {"kind": "named", "name": "campaign_id"},
        "min_items": 0,
        "max_items": 32,
        "collection_semantics": "sorted_unique",
    }
    assert sidecar_path.read_text(encoding="ascii").strip() == (
        "d0e3c08ed5699c8fd6078afb6d7c0a513bbc20b306bad630b175abd09e695f85"
    )
    assert hashlib.sha256(registry_path.read_bytes()).hexdigest() == (
        "1d36c3cc5d608209cb431a9a768a1f95e24cb73f64745199670b175ffa6758dd"
    )
    assert hashlib.sha256(sidecar_path.read_bytes()).hexdigest() == (
        "d9491f211a4e7d84777c82cdb6af716f4e4422ed57624a0cbff1f713bc8f8fce"
    )

    assert fixture["fixture_id"] == (
        "experiment_trial_ledger_trial_family_registration_v1_golden"
    )
    assert set(fixture) == {
        "fixture_id",
        "global_trial_family_registered",
        "direct_trial_family_registered",
    }
    assert fixture["global_trial_family_registered"]["payload"][
        "campaign_scope_ids"
    ] == []
    assert len(
        fixture["direct_trial_family_registered"]["payload"][
            "campaign_scope_ids"
        ]
    ) == 2
    for key in (
        "global_trial_family_registered",
        "direct_trial_family_registered",
    ):
        event = fixture[key]
        assert event["event_type"] == "TRIAL_FAMILY_REGISTERED"
        assert event["subject_type"] == "trial_family"
        assert re.fullmatch(r"fam_[0-9a-f]{32}", event["subject_id"])
        assert list(event["payload"]) == expected_payload_fields

    r0_bytes = (
        PROJECT_ROOT
        / "src/ledger/schemas/"
        "experiment_trial_ledger_payload_schema_registry_v1.json"
    ).read_bytes()
    r1_bytes = (
        PROJECT_ROOT
        / "src/ledger/schemas/"
        "experiment_trial_ledger_payload_schema_registry_v2.json"
    ).read_bytes()
    assert hashlib.sha256(r0_bytes).hexdigest() == (
        "4b78c36647621deaec15114558d827c17dae2bfa29918f4cbf2ceb2aa6b6e6d9"
    )
    assert hashlib.sha256(r1_bytes).hexdigest() == (
        "d31b7a812a79618f097a50db0177e63f5246522b3b63590968172e31b71cd499"
    )

    assert (
        "docs/experiment_trial_ledger_trial_family_registration_schema_contract.md"
        in repo_map
    )


def test_sample_registration_r1d_freezes_owner_bundle_and_release() -> None:
    contract_path = (
        PROJECT_ROOT
        / "docs/experiment_trial_ledger_sample_registration_schema_contract.md"
    )
    contract = contract_path.read_text(encoding="utf-8")
    normalized_contract = " ".join(contract.split())
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")
    registry_path = (
        PROJECT_ROOT
        / "src/ledger/schemas/"
        "experiment_trial_ledger_payload_schema_registry_v4.json"
    )
    sidecar_path = registry_path.with_suffix(".sha256")
    fixture_path = (
        PROJECT_ROOT
        / "tests/fixtures/"
        "experiment_trial_ledger_sample_registration_v1_golden.json"
    )
    registry = json.loads(registry_path.read_text(encoding="ascii"))
    fixture = json.loads(fixture_path.read_text(encoding="ascii"))

    for phrase in [
        "Contract ID: `experiment_trial_ledger_sample_registration_schema_r1d`",
        "Contract version: `0.4.0`",
        "Owner decision: option `R1D-A`",
        "Exact ledger-local sample namespace: `smp_<32 lowercase hex>`",
        "registry schema ID `experiment_trial_ledger_payload_schema_registry_v4`",
        "registry version `0.4.0`",
        "unchanged schema-language version `0.2.0`",
        "The other 32 events remain `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "`CAMPAIGN_ENTITY_BOUND` and `STAGE3_SAMPLE_REFERENCE_BOUND` remain incomplete for R1E",
        "`subject_type` exactly `sample`",
        "empty means a ledger-global local registration",
        "one through 32 entries means a direct local registration",
        "complete repository-external canonical sample records",
        "The accepted resolver key is the exact tuple",
        "A retrieval miss, ambiguous record, digest mismatch, schema mismatch, noncanonical record, or hash-only stand-in fails closed",
        "the reviewer must be distinct from both the sample-record producer and the `SAMPLE_REGISTERED.actor_id`",
        "A digest is not publication safe merely because it is non-reversible",
        "direct local `SAMPLE_REGISTERED`",
        "ledger-global local `SAMPLE_REGISTERED`",
        "later campaign-scoped `STAGE3_SAMPLE_REFERENCE_BOUND`",
        "without backfilling a synthetic `SAMPLE_REGISTERED`",
        "one canonical sample lineage and representation path has exactly one ledger-local `sample_id`",
        "Acceptance generations are positive safe integers and strictly increase",
        "exactly one accepted generation is current",
        "Aliases, clones, new campaign IDs, reruns, result access, or reclassification must not allocate a new sample identity or reset exposure history",
        "an overlapping window cannot manufacture pristine holdout status",
        "Trial count, execution-attempt count, and protected-sample access remain zero",
        "four reminders at 30-minute intervals",
    ]:
        assert phrase in normalized_contract

    expected_supported = [
        "LEDGER_EPOCH_CREATED",
        "CAMPAIGN_ALLOCATED",
        "EXPERIMENT_ALLOCATED",
        "TRIAL_FAMILY_REGISTERED",
        "SAMPLE_REGISTERED",
    ]
    expected_payload_fields = [
        "campaign_scope_ids",
        "sample_acceptance_decision_id",
        "sample_acceptance_generation",
        "sample_acceptance_record_sha256",
        "sample_acceptance_schema_version",
        "sample_authority_id",
        "sample_authority_registry_sha256",
        "sample_authority_version",
        "sample_public_projection_id",
        "sample_public_projection_schema_version",
        "sample_public_projection_sha256",
        "sample_publication_approval_generation",
        "sample_publication_approval_id",
        "sample_publication_approval_record_sha256",
        "sample_publication_approval_schema_version",
        "sample_record_canonicalization_id",
        "sample_record_id",
        "sample_record_schema_version",
        "sample_record_sha256",
        "sample_record_version",
    ]
    assert registry["registry_schema_id"] == (
        "experiment_trial_ledger_payload_schema_registry_v4"
    )
    assert registry["registry_version"] == "0.4.0"
    assert registry["registry_status"] == "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    assert registry["schema_language_version"] == "0.2.0"
    assert [item["event_type"] for item in registry["event_schemas"]] == (
        expected_supported
    )
    assert len(registry["incomplete_event_types"]) == 32
    assert set(registry["incomplete_event_types"]) == (
        set(registry["closed_event_vocabulary"]) - set(expected_supported)
    )
    assert registry["type_definitions"]["sample_id"] == {
        "kind": "typed_id",
        "prefix": "smp",
    }
    sample_schema = next(
        item
        for item in registry["event_schemas"]
        if item["event_type"] == "SAMPLE_REGISTERED"
    )
    assert sample_schema["schema_status"] == "FROZEN_SUPPORTED"
    sample_schema = sample_schema["event_schema"]
    assert sample_schema["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "sample",
    }
    assert sample_schema["properties"]["subject_id"] == {
        "kind": "named",
        "name": "sample_id",
    }
    payload_schema = sample_schema["properties"]["payload"]
    assert payload_schema["required"] == expected_payload_fields
    assert list(payload_schema["properties"]) == expected_payload_fields
    assert payload_schema["properties"]["campaign_scope_ids"] == {
        "kind": "array",
        "collection_semantics": "sorted_unique",
        "items": {"kind": "named", "name": "campaign_id"},
        "min_items": 0,
        "max_items": 32,
    }
    assert sidecar_path.read_text(encoding="ascii").strip() == (
        "3a1c17be6dc6d20f512429b4ff2457be4f28472050a99a5f97eee16a9dd57ab4"
    )
    assert hashlib.sha256(registry_path.read_bytes()).hexdigest() == (
        "1562852a4b95f867f7843818f31a0672949afb187ef84291ccac030e105ef46d"
    )
    assert hashlib.sha256(sidecar_path.read_bytes()).hexdigest() == (
        "fc34bc6d5183fc977e863fda183b40fd4252bed073cfa04e567cb784aa0b7845"
    )

    assert fixture["fixture_id"] == (
        "experiment_trial_ledger_sample_registration_v1_golden"
    )
    assert set(fixture) == {
        "fixture_id",
        "global_sample_registered",
        "direct_sample_registered",
    }
    for key in ("global_sample_registered", "direct_sample_registered"):
        event = fixture[key]
        assert event["event_type"] == "SAMPLE_REGISTERED"
        assert event["subject_type"] == "sample"
        assert re.fullmatch(r"smp_[0-9a-f]{32}", event["subject_id"])
        assert list(event["payload"]) == expected_payload_fields

    assert (
        "docs/experiment_trial_ledger_sample_registration_schema_contract.md"
        in repo_map
    )


def test_binding_r1e_freezes_owner_bundle_and_release() -> None:
    contract_path = (
        PROJECT_ROOT
        / "docs/experiment_trial_ledger_binding_schema_contract.md"
    )
    contract = contract_path.read_text(encoding="utf-8")
    normalized_contract = " ".join(contract.split())
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")
    registry_path = (
        PROJECT_ROOT
        / "src/ledger/schemas/"
        "experiment_trial_ledger_payload_schema_registry_v5.json"
    )
    sidecar_path = registry_path.with_suffix(".sha256")
    fixture_path = (
        PROJECT_ROOT
        / "tests/fixtures/"
        "experiment_trial_ledger_binding_events_v1_golden.json"
    )
    registry = json.loads(registry_path.read_text(encoding="ascii"))
    fixture = json.loads(fixture_path.read_text(encoding="ascii"))

    for phrase in [
        "Contract ID: `experiment_trial_ledger_binding_schema_r1e`",
        "Contract version: `0.5.0`",
        "Owner decision: option `R1E-A`",
        "registry schema ID `experiment_trial_ledger_payload_schema_registry_v5`",
        "registry version `0.5.0`",
        "unchanged schema-language version `0.2.0`",
        "The other 30 events remain `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "`CAMPAIGN_ENTITY_BOUND` binds one existing ledger-local trial family or sample identity to one already allocated campaign",
        "top-level `tagged_union` discriminated by `subject_type`",
        "`trial_family`",
        "`sample`",
        "`local_registration`",
        "`external_reference`",
        "one-item `payload.campaign_scope_ids`",
        "source_registration_event_id",
        "source_registration_event_sha256",
        "source_reference_event_id",
        "source_reference_event_sha256",
        "the source exists earlier in the same ledger epoch",
        "recomputing the event digest from the exact retained canonical bytes",
        "R1E-A makes one explicit bounded amendment to the R1A binding architecture",
        "referencing the exact earlier `STAGE3_SAMPLE_REFERENCE_BOUND` event ID and hash",
        "The first external-reference event remains the sole allocation",
        "`STAGE3_SAMPLE_REFERENCE_BOUND` introduces one external-origin ledger-local sample identity",
        "A digest is not publication safe merely because it is non-reversible",
        "one `(ledger_id, campaign_id, subject_type, subject_id)` binding exists at most once",
        "a directly campaign-scoped registration cannot also have a binding for that campaign",
        "Aliases, clones, reruns, new campaigns, window overlap, result access, and post-result reclassification do not allocate a new identity",
        "local schema `ACCEPT` must not be represented as proof",
        "Trial count, execution-attempt count, and protected-sample access remain zero",
        "four reminders at 30-minute intervals",
    ]:
        assert phrase in normalized_contract

    expected_supported = [
        "LEDGER_EPOCH_CREATED",
        "CAMPAIGN_ALLOCATED",
        "EXPERIMENT_ALLOCATED",
        "TRIAL_FAMILY_REGISTERED",
        "SAMPLE_REGISTERED",
        "CAMPAIGN_ENTITY_BOUND",
        "STAGE3_SAMPLE_REFERENCE_BOUND",
    ]
    assert registry["registry_schema_id"] == (
        "experiment_trial_ledger_payload_schema_registry_v5"
    )
    assert registry["registry_version"] == "0.5.0"
    assert registry["registry_status"] == "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    assert registry["schema_language_version"] == "0.2.0"
    assert [item["event_type"] for item in registry["event_schemas"]] == (
        expected_supported
    )
    assert len(registry["incomplete_event_types"]) == 30
    assert set(registry["incomplete_event_types"]) == (
        set(registry["closed_event_vocabulary"]) - set(expected_supported)
    )

    binding_schema = next(
        item
        for item in registry["event_schemas"]
        if item["event_type"] == "CAMPAIGN_ENTITY_BOUND"
    )
    assert binding_schema["schema_status"] == "FROZEN_SUPPORTED"
    binding_schema = binding_schema["event_schema"]
    assert binding_schema["kind"] == "tagged_union"
    assert binding_schema["discriminator"] == "subject_type"
    assert list(binding_schema["variants"]) == ["trial_family", "sample"]
    sample_payload = binding_schema["variants"]["sample"]["properties"][
        "payload"
    ]
    assert sample_payload["kind"] == "tagged_union"
    assert sample_payload["discriminator"] == "source_kind"
    assert list(sample_payload["variants"]) == [
        "local_registration",
        "external_reference",
    ]

    stage3_schema = next(
        item
        for item in registry["event_schemas"]
        if item["event_type"] == "STAGE3_SAMPLE_REFERENCE_BOUND"
    )["event_schema"]
    assert stage3_schema["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "sample",
    }
    assert stage3_schema["properties"]["subject_id"] == {
        "kind": "named",
        "name": "sample_id",
    }
    assert stage3_schema["properties"]["payload"]["properties"][
        "campaign_scope_ids"
    ] == {
        "kind": "array",
        "collection_semantics": "sorted_unique",
        "items": {"kind": "named", "name": "campaign_id"},
        "min_items": 1,
        "max_items": 1,
    }

    assert sidecar_path.read_text(encoding="ascii").strip() == (
        "c6fed9409f596cae5cdba1bce3ad8c5b088d2931361aeda7c06dfd2453805a52"
    )
    assert hashlib.sha256(registry_path.read_bytes()).hexdigest() == (
        "223a2b7e2ff8ffdb4977c878186236cd747428838bade571e43e513e71ee52b2"
    )
    assert hashlib.sha256(sidecar_path.read_bytes()).hexdigest() == (
        "dceb0f334fe2056ae0d3a673e499caa899d69d67b60a21b2380d0ea947427483"
    )

    assert fixture["fixture_id"] == (
        "experiment_trial_ledger_binding_events_v1_golden"
    )
    assert set(fixture) == {
        "fixture_id",
        "trial_family_global_bound",
        "sample_global_local_bound",
        "stage3_sample_reference_bound",
        "sample_external_origin_reused",
    }
    assert fixture["trial_family_global_bound"]["subject_type"] == (
        "trial_family"
    )
    assert fixture["sample_global_local_bound"]["payload"]["source_kind"] == (
        "local_registration"
    )
    assert fixture["stage3_sample_reference_bound"]["event_type"] == (
        "STAGE3_SAMPLE_REFERENCE_BOUND"
    )
    assert fixture["sample_external_origin_reused"]["payload"][
        "source_kind"
    ] == "external_reference"
    assert fixture["sample_external_origin_reused"]["subject_id"] == (
        fixture["stage3_sample_reference_bound"]["subject_id"]
    )

    assert "docs/experiment_trial_ledger_binding_schema_contract.md" in repo_map


def test_trial_allocation_r1f_freezes_owner_bundle_and_release() -> None:
    contract_path = (
        PROJECT_ROOT
        / "docs/experiment_trial_ledger_trial_allocation_schema_contract.md"
    )
    contract = contract_path.read_text(encoding="utf-8")
    normalized_contract = " ".join(contract.split())
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")
    registry_path = (
        PROJECT_ROOT
        / "src/ledger/schemas/"
        "experiment_trial_ledger_payload_schema_registry_v6.json"
    )
    sidecar_path = registry_path.with_suffix(".sha256")
    fixture_path = (
        PROJECT_ROOT
        / "tests/fixtures/"
        "experiment_trial_ledger_trial_allocation_events_v1_golden.json"
    )
    registry = json.loads(registry_path.read_text(encoding="ascii"))
    fixture = json.loads(fixture_path.read_text(encoding="ascii"))

    for phrase in [
        "Contract ID: `experiment_trial_ledger_trial_allocation_schema_r1f`",
        "Contract version: `0.6.0`",
        "Owner decision: option `R1F-A`",
        "registry schema ID `experiment_trial_ledger_payload_schema_registry_v6`",
        "registry version `0.6.0`",
        "unchanged schema-language version `0.2.0`",
        "The other 29 events remain `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "`TRIAL_ALLOCATED` allocates one new semantic trial identity",
        "trl_<32 lowercase hexadecimal digits>",
        "`payload.initial_disposition` exactly `PLANNED`",
        "Complete trial-definition records are repository-external",
        "R1F fixes a finite maximum of 32 sample bindings per semantic trial",
        "reviewer must be distinct",
        "`payload.relation` is a closed `tagged_union`",
        "`original`",
        "`child`, `clone`, and `rerun`",
        "`payload.code_identity` is a closed `tagged_union`",
        "`clean_commit`",
        "`dirty_tree`",
        "The event pins the actor's allocation authority",
        "A digest is not public merely because it is non-reversible",
        "the allocation occurs before any validation, execution, attempt allocation, protected access, artifact production, or result inspection",
        "local schema `ACCEPT` must not be represented as proof",
        "Trial execution count, attempt count, and protected-sample access remain zero",
        "perform a read-only dependency/risk analysis over the remaining 29 incomplete events",
    ]:
        assert phrase in normalized_contract

    expected_supported = [
        "LEDGER_EPOCH_CREATED",
        "CAMPAIGN_ALLOCATED",
        "EXPERIMENT_ALLOCATED",
        "TRIAL_FAMILY_REGISTERED",
        "SAMPLE_REGISTERED",
        "CAMPAIGN_ENTITY_BOUND",
        "STAGE3_SAMPLE_REFERENCE_BOUND",
        "TRIAL_ALLOCATED",
    ]
    expected_payload_fields = [
        "allocation_authority_generation",
        "allocation_authority_id",
        "allocation_authority_record_sha256",
        "allocation_authority_schema_version",
        "campaign_allocation_event_id",
        "campaign_allocation_event_sha256",
        "campaign_scope_ids",
        "code_identity",
        "experiment_allocation_event_id",
        "experiment_allocation_event_sha256",
        "experiment_id",
        "initial_disposition",
        "relation",
        "trial_definition_acceptance_decision_id",
        "trial_definition_acceptance_generation",
        "trial_definition_acceptance_record_sha256",
        "trial_definition_acceptance_schema_version",
        "trial_definition_authority_id",
        "trial_definition_authority_registry_sha256",
        "trial_definition_authority_version",
        "trial_definition_public_projection_id",
        "trial_definition_public_projection_schema_version",
        "trial_definition_public_projection_sha256",
        "trial_definition_publication_approval_generation",
        "trial_definition_publication_approval_id",
        "trial_definition_publication_approval_record_sha256",
        "trial_definition_publication_approval_schema_version",
        "trial_definition_record_canonicalization_id",
        "trial_definition_record_id",
        "trial_definition_record_schema_version",
        "trial_definition_record_sha256",
        "trial_definition_record_version",
        "trial_family_id",
        "trial_family_source_event_id",
        "trial_family_source_event_sha256",
    ]
    assert registry["registry_schema_id"] == (
        "experiment_trial_ledger_payload_schema_registry_v6"
    )
    assert registry["registry_version"] == "0.6.0"
    assert registry["registry_status"] == "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    assert registry["schema_language_version"] == "0.2.0"
    assert [item["event_type"] for item in registry["event_schemas"]] == (
        expected_supported
    )
    assert len(registry["incomplete_event_types"]) == 29
    assert set(registry["incomplete_event_types"]) == (
        set(registry["closed_event_vocabulary"]) - set(expected_supported)
    )
    assert registry["type_definitions"]["trial_id"] == {
        "kind": "typed_id",
        "prefix": "trl",
    }

    trial_schema = next(
        item
        for item in registry["event_schemas"]
        if item["event_type"] == "TRIAL_ALLOCATED"
    )
    assert trial_schema["schema_status"] == "FROZEN_SUPPORTED"
    trial_schema = trial_schema["event_schema"]
    assert trial_schema["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "trial",
    }
    assert trial_schema["properties"]["subject_id"] == {
        "kind": "named",
        "name": "trial_id",
    }
    payload_schema = trial_schema["properties"]["payload"]
    assert payload_schema["required"] == expected_payload_fields
    assert list(payload_schema["properties"]) == expected_payload_fields
    assert payload_schema["properties"]["campaign_scope_ids"] == {
        "kind": "array",
        "collection_semantics": "sorted_unique",
        "items": {"kind": "named", "name": "campaign_id"},
        "min_items": 1,
        "max_items": 1,
    }
    relation_schema = payload_schema["properties"]["relation"]
    assert relation_schema["kind"] == "tagged_union"
    assert relation_schema["discriminator"] == "relation_kind"
    assert list(relation_schema["variants"]) == [
        "original",
        "child",
        "clone",
        "rerun",
    ]
    code_schema = payload_schema["properties"]["code_identity"]
    assert code_schema["kind"] == "tagged_union"
    assert code_schema["discriminator"] == "code_identity_kind"
    assert list(code_schema["variants"]) == ["clean_commit", "dirty_tree"]

    assert sidecar_path.read_text(encoding="ascii").strip() == (
        "acada613202d7ab3a96380ea70ba9bbfeffe7c401bf998828a39528db3ad8691"
    )
    assert hashlib.sha256(registry_path.read_bytes()).hexdigest() == (
        "162e20df0b7cfb4e07abb818ccf87160d007eced7f90faeefe0d20831fd7229c"
    )
    assert hashlib.sha256(sidecar_path.read_bytes()).hexdigest() == (
        "8322d6c509797710e5f8d7c85d5406202535b878c88ddf05f83525bbaa83db46"
    )

    assert fixture["fixture_id"] == (
        "experiment_trial_ledger_trial_allocation_events_v1_golden"
    )
    assert set(fixture) == {
        "fixture_id",
        "original_clean_trial_allocated",
        "rerun_dirty_trial_allocated",
    }
    assert (
        fixture["original_clean_trial_allocated"]["payload"]["relation"][
            "relation_kind"
        ]
        == "original"
    )
    assert (
        fixture["original_clean_trial_allocated"]["payload"]["code_identity"][
            "code_identity_kind"
        ]
        == "clean_commit"
    )
    assert (
        fixture["rerun_dirty_trial_allocated"]["payload"]["relation"][
            "relation_kind"
        ]
        == "rerun"
    )
    assert (
        fixture["rerun_dirty_trial_allocated"]["payload"]["code_identity"][
            "code_identity_kind"
        ]
        == "dirty_tree"
    )
    for event in fixture.values():
        if not isinstance(event, dict):
            continue
        assert event["event_type"] == "TRIAL_ALLOCATED"
        assert event["subject_type"] == "trial"
        assert re.fullmatch(r"trl_[0-9a-f]{32}", event["subject_id"])
        assert list(event["payload"]) == expected_payload_fields

    assert (
        "docs/experiment_trial_ledger_trial_allocation_schema_contract.md"
        in repo_map
    )


def test_campaign_inventory_seal_r1g_freezes_owner_bundle_and_release() -> None:
    contract_path = (
        PROJECT_ROOT
        / "docs/experiment_trial_ledger_campaign_inventory_seal_schema_contract.md"
    )
    contract = contract_path.read_text(encoding="utf-8")
    normalized_contract = " ".join(contract.split())
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")
    registry_path = (
        PROJECT_ROOT
        / "src/ledger/schemas/"
        "experiment_trial_ledger_payload_schema_registry_v7.json"
    )
    sidecar_path = registry_path.with_suffix(".sha256")
    fixture_path = (
        PROJECT_ROOT
        / "tests/fixtures/"
        "experiment_trial_ledger_campaign_inventory_seal_v1_golden.json"
    )
    registry = json.loads(registry_path.read_text(encoding="ascii"))
    fixture = json.loads(fixture_path.read_text(encoding="ascii"))

    for phrase in [
        "Contract ID: `experiment_trial_ledger_campaign_inventory_seal_schema_r1g`",
        "Contract version: `0.7.0`",
        "Owner decision: option `R1G-A`",
        "registry schema ID `experiment_trial_ledger_payload_schema_registry_v7`",
        "registry version `0.7.0`",
        "unchanged schema-language version `0.2.0`",
        "The other 28 events remain `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "`CAMPAIGN_INVENTORY_SEALED` creates no new campaign or trial identity",
        "`subject_type` exactly `campaign`",
        "one-item sorted-unique `payload.campaign_scope_ids`",
        "The complete `campaign_inventory_record_v1` is repository-external",
        "ordered all-and-only set of 1 through 4096 semantic trial entries",
        "Its reviewer must be distinct from:",
        "The maximum of 4096 semantic trials is a schema/review bound",
        "`campaign_inventory_preseal_head_v1`",
        "require the seal sequence to equal `predecessor_sequence + 1`",
        "Exactly one initial `CAMPAIGN_INVENTORY_SEALED` is legal",
        "`CAMPAIGN_AMENDMENT_PROPOSED`",
        "`CAMPAIGN_INVENTORY_AMENDED`",
        "local schema `ACCEPT`",
        "Trial execution count, attempt count, and protected-sample access remain zero",
    ]:
        assert phrase in normalized_contract

    expected_supported = [
        "LEDGER_EPOCH_CREATED",
        "CAMPAIGN_ALLOCATED",
        "EXPERIMENT_ALLOCATED",
        "TRIAL_FAMILY_REGISTERED",
        "SAMPLE_REGISTERED",
        "CAMPAIGN_ENTITY_BOUND",
        "STAGE3_SAMPLE_REFERENCE_BOUND",
        "TRIAL_ALLOCATED",
        "CAMPAIGN_INVENTORY_SEALED",
    ]
    expected_payload_fields = [
        "campaign_allocation_event_id",
        "campaign_allocation_event_sha256",
        "campaign_scope_ids",
        "inventory_acceptance_decision_id",
        "inventory_acceptance_generation",
        "inventory_acceptance_record_sha256",
        "inventory_acceptance_schema_version",
        "inventory_authority_id",
        "inventory_authority_registry_sha256",
        "inventory_authority_version",
        "inventory_record_canonicalization_id",
        "inventory_record_id",
        "inventory_record_schema_version",
        "inventory_record_version",
        "preseal_head",
        "seal_authority_generation",
        "seal_authority_id",
        "seal_authority_record_sha256",
        "seal_authority_schema_version",
        "sealed_semantic_trial_count",
        "sealed_trial_inventory_sha256",
    ]
    assert registry["registry_schema_id"] == (
        "experiment_trial_ledger_payload_schema_registry_v7"
    )
    assert registry["registry_version"] == "0.7.0"
    assert registry["registry_status"] == "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    assert registry["schema_language_version"] == "0.2.0"
    assert [item["event_type"] for item in registry["event_schemas"]] == (
        expected_supported
    )
    assert len(registry["incomplete_event_types"]) == 28
    assert set(registry["incomplete_event_types"]) == (
        set(registry["closed_event_vocabulary"]) - set(expected_supported)
    )

    seal = next(
        item
        for item in registry["event_schemas"]
        if item["event_type"] == "CAMPAIGN_INVENTORY_SEALED"
    )
    assert seal["schema_status"] == "FROZEN_SUPPORTED"
    schema = seal["event_schema"]
    payload = schema["properties"]["payload"]
    assert schema["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "campaign",
    }
    assert schema["properties"]["subject_id"] == {
        "kind": "named",
        "name": "campaign_id",
    }
    assert list(payload["properties"]) == expected_payload_fields
    assert payload["required"] == expected_payload_fields
    assert payload["properties"]["campaign_scope_ids"] == {
        "kind": "array",
        "collection_semantics": "sorted_unique",
        "items": {"kind": "named", "name": "campaign_id"},
        "min_items": 1,
        "max_items": 1,
    }
    count = payload["properties"]["sealed_semantic_trial_count"]
    assert count["kind"] == "enum"
    assert len(count["values"]) == 4096
    assert set(count["values"]) == set(range(1, 4097))
    preseal = payload["properties"]["preseal_head"]
    assert list(preseal["properties"]) == [
        "anchor_schema_version",
        "ledger_id",
        "predecessor_event_sha256",
        "predecessor_sequence",
    ]
    assert seal["local_constraints"] == [
        {
            "constraint_id": "inventory_campaign_subject_in_scope",
            "predicate": "array_contains_path",
            "left_path": ["payload", "campaign_scope_ids"],
            "right_path": ["subject_id"],
        },
        {
            "constraint_id": "inventory_preseal_ledger_matches_envelope",
            "predicate": "path_equals_path",
            "left_path": ["payload", "preseal_head", "ledger_id"],
            "right_path": ["ledger_id"],
        },
        {
            "constraint_id": "inventory_preseal_hash_matches_previous",
            "predicate": "path_equals_path",
            "left_path": [
                "payload",
                "preseal_head",
                "predecessor_event_sha256",
            ],
            "right_path": ["previous_event_sha256"],
        },
    ]

    assert sidecar_path.read_text(encoding="ascii").strip() == (
        "1d85424d1ee60dcc9523a52c56b22080b47aebb4275551a7ea9ee38e8e28d710"
    )
    assert fixture["fixture_id"] == (
        "experiment_trial_ledger_campaign_inventory_seal_v1_golden"
    )
    assert set(fixture) == {
        "fixture_id",
        "standard_inventory_sealed",
        "maximum_inventory_sealed",
    }
    assert (
        fixture["standard_inventory_sealed"]["payload"][
            "sealed_semantic_trial_count"
        ]
        == 2
    )
    assert (
        fixture["maximum_inventory_sealed"]["payload"][
            "sealed_semantic_trial_count"
        ]
        == 4096
    )
    for event in fixture.values():
        if not isinstance(event, dict):
            continue
        assert event["event_type"] == "CAMPAIGN_INVENTORY_SEALED"
        assert event["subject_type"] == "campaign"
        assert re.fullmatch(r"cmp_[0-9a-f]{32}", event["subject_id"])
        assert list(event["payload"]) == expected_payload_fields
        assert (
            event["payload"]["campaign_scope_ids"][0] == event["subject_id"]
        )
        assert (
            event["payload"]["preseal_head"]["ledger_id"]
            == event["ledger_id"]
        )
        assert (
            event["payload"]["preseal_head"]["predecessor_event_sha256"]
            == event["previous_event_sha256"]
        )

    assert (
        "docs/experiment_trial_ledger_campaign_inventory_seal_schema_contract.md"
        in repo_map
    )


def test_attempt_allocation_r1h_freezes_owner_bundle_and_release() -> None:
    contract_path = (
        PROJECT_ROOT
        / "docs/experiment_trial_ledger_attempt_allocation_schema_contract.md"
    )
    contract = contract_path.read_text(encoding="utf-8")
    normalized_contract = " ".join(contract.split())
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")
    registry_path = (
        PROJECT_ROOT
        / "src/ledger/schemas/"
        "experiment_trial_ledger_payload_schema_registry_v8.json"
    )
    sidecar_path = registry_path.with_suffix(".sha256")
    fixture_path = (
        PROJECT_ROOT
        / "tests/fixtures/"
        "experiment_trial_ledger_attempt_allocation_v1_golden.json"
    )
    registry = json.loads(registry_path.read_text(encoding="ascii"))
    fixture = json.loads(fixture_path.read_text(encoding="ascii"))

    for phrase in [
        "Contract ID: `experiment_trial_ledger_attempt_allocation_schema_r1h`",
        "Contract version: `0.8.0`",
        "Owner decision: option `R1H-A`",
        "registry schema ID `experiment_trial_ledger_payload_schema_registry_v8`",
        "registry version `0.8.0`",
        "unchanged schema-language version `0.2.0`",
        "The other 27 events remain `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "`subject_type` exactly `attempt`",
        "one-item sorted-unique `payload.campaign_scope_ids`",
        "The complete `attempt_plan_record_v1` is repository-external",
        "Its reviewer must be distinct from:",
        "`first_attempt` branch",
        "`retry` branch",
        "Every operational retry uses a new attempt ID",
        "`ATTEMPT_STARTED` remains the separate immediate pre-execution boundary",
        "statefully fail closed rather than local `ACCEPT` evidence",
    ]:
        assert phrase in normalized_contract

    expected_supported = [
        "LEDGER_EPOCH_CREATED",
        "CAMPAIGN_ALLOCATED",
        "EXPERIMENT_ALLOCATED",
        "TRIAL_FAMILY_REGISTERED",
        "SAMPLE_REGISTERED",
        "CAMPAIGN_ENTITY_BOUND",
        "STAGE3_SAMPLE_REFERENCE_BOUND",
        "TRIAL_ALLOCATED",
        "CAMPAIGN_INVENTORY_SEALED",
        "ATTEMPT_ALLOCATED",
    ]
    expected_payload_fields = [
        "allocation_authority_generation",
        "allocation_authority_id",
        "allocation_authority_record_sha256",
        "allocation_authority_schema_version",
        "attempt_plan_acceptance_decision_id",
        "attempt_plan_acceptance_generation",
        "attempt_plan_acceptance_record_sha256",
        "attempt_plan_acceptance_schema_version",
        "attempt_plan_authority_id",
        "attempt_plan_authority_registry_sha256",
        "attempt_plan_authority_version",
        "attempt_plan_record_canonicalization_id",
        "attempt_plan_record_id",
        "attempt_plan_record_schema_version",
        "attempt_plan_record_sha256",
        "attempt_plan_record_version",
        "campaign_inventory_seal_event_id",
        "campaign_inventory_seal_event_sha256",
        "campaign_scope_ids",
        "expected_output_inventory_sha256",
        "relation",
        "trial_allocation_event_id",
        "trial_allocation_event_sha256",
        "trial_id",
    ]
    assert registry["registry_schema_id"] == (
        "experiment_trial_ledger_payload_schema_registry_v8"
    )
    assert registry["registry_version"] == "0.8.0"
    assert registry["registry_status"] == "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    assert registry["schema_language_version"] == "0.2.0"
    assert registry["type_definitions"]["attempt_id"] == {
        "kind": "typed_id",
        "prefix": "att",
    }
    assert [item["event_type"] for item in registry["event_schemas"]] == (
        expected_supported
    )
    assert len(registry["incomplete_event_types"]) == 27
    assert set(registry["incomplete_event_types"]) == (
        set(registry["closed_event_vocabulary"]) - set(expected_supported)
    )

    attempt = next(
        item
        for item in registry["event_schemas"]
        if item["event_type"] == "ATTEMPT_ALLOCATED"
    )
    assert attempt["schema_status"] == "FROZEN_SUPPORTED"
    schema = attempt["event_schema"]
    payload = schema["properties"]["payload"]
    assert schema["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "attempt",
    }
    assert schema["properties"]["subject_id"] == {
        "kind": "named",
        "name": "attempt_id",
    }
    assert list(payload["properties"]) == expected_payload_fields
    assert payload["required"] == expected_payload_fields
    assert payload["properties"]["campaign_scope_ids"] == {
        "kind": "array",
        "collection_semantics": "sorted_unique",
        "items": {"kind": "named", "name": "campaign_id"},
        "min_items": 1,
        "max_items": 1,
    }
    relation = payload["properties"]["relation"]
    assert relation["kind"] == "tagged_union"
    assert relation["discriminator"] == "attempt_kind"
    assert set(relation["variants"]) == {"first_attempt", "retry"}
    assert relation["variants"]["first_attempt"]["properties"][
        "attempt_ordinal"
    ] == {"kind": "literal", "value": 1}
    assert relation["variants"]["retry"]["properties"]["attempt_ordinal"] == {
        "kind": "safe_integer",
        "minimum": 2,
    }
    assert attempt["local_constraints"] == []

    assert sidecar_path.read_text(encoding="ascii").strip() == (
        "3c71399f9ee8de51b6bd401dc409865c672d12a97cc00057c6de26445c0c538f"
    )
    assert fixture["fixture_id"] == (
        "experiment_trial_ledger_attempt_allocation_v1_golden"
    )
    assert set(fixture) == {
        "fixture_id",
        "first_attempt_allocated",
        "retry_attempt_allocated",
    }
    first = fixture["first_attempt_allocated"]
    retry = fixture["retry_attempt_allocated"]
    for event in [first, retry]:
        assert event["event_type"] == "ATTEMPT_ALLOCATED"
        assert event["subject_type"] == "attempt"
        assert re.fullmatch(r"att_[0-9a-f]{32}", event["subject_id"])
        assert list(event["payload"]) == expected_payload_fields
        assert len(event["payload"]["campaign_scope_ids"]) == 1
    assert first["payload"]["relation"] == {
        "attempt_kind": "first_attempt",
        "attempt_ordinal": 1,
    }
    assert retry["payload"]["relation"]["attempt_kind"] == "retry"
    assert retry["payload"]["relation"]["attempt_ordinal"] == 2
    assert re.fullmatch(
        r"att_[0-9a-f]{32}",
        retry["payload"]["relation"]["prior_attempt_id"],
    )

    assert (
        "docs/experiment_trial_ledger_attempt_allocation_schema_contract.md"
        in repo_map
    )


def test_attempt_start_r1i_freezes_owner_bundle_and_release() -> None:
    contract_path = (
        PROJECT_ROOT
        / "docs/experiment_trial_ledger_attempt_start_schema_contract.md"
    )
    contract = contract_path.read_text(encoding="utf-8")
    normalized_contract = " ".join(contract.split())
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")
    registry_path = (
        PROJECT_ROOT
        / "src/ledger/schemas/"
        "experiment_trial_ledger_payload_schema_registry_v9.json"
    )
    sidecar_path = registry_path.with_suffix(".sha256")
    fixture_path = (
        PROJECT_ROOT
        / "tests/fixtures/"
        "experiment_trial_ledger_attempt_start_v1_golden.json"
    )
    registry = json.loads(registry_path.read_text(encoding="ascii"))
    fixture = json.loads(fixture_path.read_text(encoding="ascii"))

    for phrase in [
        "Contract ID: `experiment_trial_ledger_attempt_start_schema_r1i`",
        "Contract version: `0.9.0`",
        "Owner decision: option `R1I-A`",
        "registry schema ID `experiment_trial_ledger_payload_schema_registry_v9`",
        "registry version `0.9.0`",
        "unchanged schema-language version `0.2.0`",
        "The other 26 events remain `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`",
        "`event_type` exactly `ATTEMPT_STARTED`",
        "`subject_type` exactly `attempt`",
        "one-item sorted-unique `payload.campaign_scope_ids`",
        "The complete `attempt_start_readiness_record_v1` is repository-external",
        "The reviewer must be distinct from:",
        "The exact capability namespace is:",
        "Exact lost-ack replay",
        "Exactly one start is permitted per attempt",
        "stateful checks are outside schema-language `0.2.0`",
    ]:
        assert phrase in normalized_contract

    expected_supported = [
        "LEDGER_EPOCH_CREATED",
        "CAMPAIGN_ALLOCATED",
        "EXPERIMENT_ALLOCATED",
        "TRIAL_FAMILY_REGISTERED",
        "SAMPLE_REGISTERED",
        "CAMPAIGN_ENTITY_BOUND",
        "STAGE3_SAMPLE_REFERENCE_BOUND",
        "TRIAL_ALLOCATED",
        "CAMPAIGN_INVENTORY_SEALED",
        "ATTEMPT_ALLOCATED",
        "ATTEMPT_STARTED",
    ]
    expected_payload_fields = [
        "attempt_allocation_event_id",
        "attempt_allocation_event_sha256",
        "campaign_scope_ids",
        "execution_capability_id",
        "execution_capability_record_canonicalization_id",
        "execution_capability_record_schema_version",
        "execution_capability_record_sha256",
        "execution_capability_record_version",
        "readiness_authority_id",
        "readiness_authority_registry_sha256",
        "readiness_authority_version",
        "readiness_record_canonicalization_id",
        "readiness_record_id",
        "readiness_record_schema_version",
        "readiness_record_sha256",
        "readiness_record_version",
        "start_authority_generation",
        "start_authority_id",
        "start_authority_record_sha256",
        "start_authority_schema_version",
        "trial_id",
    ]
    assert registry["registry_schema_id"] == (
        "experiment_trial_ledger_payload_schema_registry_v9"
    )
    assert registry["registry_version"] == "0.9.0"
    assert registry["registry_status"] == "SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY"
    assert registry["schema_language_version"] == "0.2.0"
    assert registry["type_definitions"]["attempt_id"] == {
        "kind": "typed_id",
        "prefix": "att",
    }
    assert registry["type_definitions"]["execution_capability_id"] == {
        "kind": "typed_id",
        "prefix": "cap",
    }
    assert [item["event_type"] for item in registry["event_schemas"]] == (
        expected_supported
    )
    assert len(registry["incomplete_event_types"]) == 26
    assert set(registry["incomplete_event_types"]) == (
        set(registry["closed_event_vocabulary"]) - set(expected_supported)
    )

    start = next(
        item
        for item in registry["event_schemas"]
        if item["event_type"] == "ATTEMPT_STARTED"
    )
    assert start["schema_status"] == "FROZEN_SUPPORTED"
    schema = start["event_schema"]
    payload = schema["properties"]["payload"]
    assert schema["properties"]["subject_type"] == {
        "kind": "literal",
        "value": "attempt",
    }
    assert schema["properties"]["subject_id"] == {
        "kind": "named",
        "name": "attempt_id",
    }
    assert list(payload["properties"]) == expected_payload_fields
    assert payload["required"] == expected_payload_fields
    assert payload["properties"]["campaign_scope_ids"] == {
        "kind": "array",
        "collection_semantics": "sorted_unique",
        "items": {"kind": "named", "name": "campaign_id"},
        "min_items": 1,
        "max_items": 1,
    }
    assert payload["properties"]["execution_capability_id"] == {
        "kind": "named",
        "name": "execution_capability_id",
    }
    assert start["local_constraints"] == []

    assert sidecar_path.read_text(encoding="ascii").strip() == (
        "1a58c069098921a8446fd2e0452fe544e7c56e8f9e5ff392ff201cb5c177503a"
    )
    assert fixture["fixture_id"] == (
        "experiment_trial_ledger_attempt_start_v1_golden"
    )
    assert set(fixture) == {"fixture_id", "attempt_started"}
    event = fixture["attempt_started"]
    assert event["event_type"] == "ATTEMPT_STARTED"
    assert event["subject_type"] == "attempt"
    assert re.fullmatch(r"att_[0-9a-f]{32}", event["subject_id"])
    assert re.fullmatch(
        r"cap_[0-9a-f]{32}",
        event["payload"]["execution_capability_id"],
    )
    assert list(event["payload"]) == expected_payload_fields
    assert len(event["payload"]["campaign_scope_ids"]) == 1

    assert (
        "docs/experiment_trial_ledger_attempt_start_schema_contract.md"
        in repo_map
    )


def _ascii_jcs_golden_bytes(value: object) -> bytes:
    """Serialize a preprocessed ASCII-only golden vector under the JCS subset."""

    def validate(item: object) -> None:
        if item is None or isinstance(item, bool):
            return
        if isinstance(item, int):
            if not (-(2**53) + 1 <= item <= (2**53) - 1):
                raise ValueError("integer is outside the I-JSON safe range")
            return
        if isinstance(item, float):
            raise ValueError("raw floats are outside the frozen preprocessing profile")
        if isinstance(item, str):
            item.encode("ascii")
            if unicodedata.normalize("NFC", item) != item:
                raise ValueError("golden string is not NFC-normalized")
            return
        if isinstance(item, list):
            for member in item:
                validate(member)
            return
        if isinstance(item, dict):
            for key, member in item.items():
                if not isinstance(key, str):
                    raise ValueError("JSON object keys must be strings")
                validate(key)
                validate(member)
            return
        raise ValueError(f"unsupported golden value type: {type(item).__name__}")

    validate(value)
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _require_exact_keys(
    value: object,
    expected_keys: set[str],
    *,
    context: str,
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise ValueError(f"{context} must contain exactly {sorted(expected_keys)}")
    return value


def _require_stable_id(value: object, *, context: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or unicodedata.normalize("NFC", value) != value
    ):
        raise ValueError(f"{context} must be a nonempty NFC-normalized string")
    return value


def _require_safe_public_id(value: object, *, context: str) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(
            r"[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?",
            value,
        )
        is None
    ):
        raise ValueError(f"{context} must be an opaque safe_public_id")
    return value


def _require_ledger_typed_id(
    value: object,
    *,
    prefix: str,
    context: str,
) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(rf"{re.escape(prefix)}_[0-9a-f]{{32}}", value) is None
    ):
        raise ValueError(f"{context} must be a typed opaque ledger ID")
    return value


def _require_actor_attribution_reference(value: object, *, context: str) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"act_[0-9a-f]{32}", value) is None
    ):
        raise ValueError(f"{context} must be an opaque actor attribution reference")
    return value


def _require_normalized_utc_timestamp(value: object, *, context: str) -> str:
    """Validate the ledger v1 UTC subset without a mutable leap-second table."""
    if not isinstance(value, str):
        raise ValueError(f"{context} must be a normalized UTC timestamp")
    match = re.fullmatch(
        r"([0-9]{4})-([0-9]{2})-([0-9]{2})"
        r"T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]+))?Z",
        value,
    )
    if match is None:
        raise ValueError(f"{context} must be a normalized UTC timestamp")
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
        raise ValueError(f"{context} must be a valid Gregorian date")
    if not (
        0 <= hour <= 23
        and 0 <= minute <= 59
        and 0 <= second <= 59
    ):
        raise ValueError(f"{context} must be a valid ledger v1 UTC time")
    fraction = match.group(7)
    if fraction is not None and fraction.endswith("0"):
        raise ValueError(f"{context} has a noncanonical fractional second")
    return value


def _ledger_event_identity_projection(source: object) -> dict[str, object]:
    """Validate the exact envelope and sole Stage 4a golden epoch payload."""
    projection = _require_exact_keys(
        source,
        {
            "ledger_schema_version",
            "event_schema_version",
            "canonicalization_id",
            "identity_projection_id",
            "ledger_id",
            "sequence",
            "event_id",
            "operation_id",
            "operation_request_projection_id",
            "operation_request_sha256",
            "event_type",
            "subject_type",
            "subject_id",
            "occurred_at",
            "recorded_at",
            "actor_id",
            "previous_event_sha256",
            "payload",
        },
        context="ledger event identity projection",
    )
    if projection["ledger_schema_version"] != "experiment_trial_ledger_v1":
        raise ValueError("unexpected ledger schema version")
    if projection["event_schema_version"] != "ledger_event_v1":
        raise ValueError("unexpected event schema version")
    if projection["canonicalization_id"] != "pit_canonical_json_v1":
        raise ValueError("unexpected canonicalization ID")
    if projection["identity_projection_id"] != "ledger_event_identity_v1":
        raise ValueError("unexpected identity projection ID")
    _require_ledger_typed_id(
        projection["ledger_id"],
        prefix="ldg",
        context="ledger_id",
    )
    _require_ledger_typed_id(
        projection["event_id"],
        prefix="evt",
        context="event_id",
    )
    _require_ledger_typed_id(
        projection["operation_id"],
        prefix="opn",
        context="operation_id",
    )
    if (
        projection["operation_request_projection_id"]
        != "ledger_operation_request_v1"
    ):
        raise ValueError("unexpected operation request projection ID")
    _require_actor_attribution_reference(
        projection["actor_id"],
        context="actor_id",
    )
    sequence = projection["sequence"]
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise ValueError("sequence must be a nonnegative non-Boolean integer")
    if (
        not isinstance(projection["operation_request_sha256"], str)
        or re.fullmatch(
            r"[0-9a-f]{64}",
            projection["operation_request_sha256"],
        )
        is None
    ):
        raise ValueError("operation request hash must be lowercase SHA-256")
    if projection["event_type"] != "LEDGER_EPOCH_CREATED":
        raise ValueError("event type has no exact Stage 4a payload schema")
    for field in ["occurred_at", "recorded_at"]:
        _require_normalized_utc_timestamp(projection[field], context=field)
    previous_hash = projection["previous_event_sha256"]
    if previous_hash is not None and (
        not isinstance(previous_hash, str)
        or re.fullmatch(r"[0-9a-f]{64}", previous_hash) is None
    ):
        raise ValueError("previous event hash must be null or lowercase SHA-256")

    if sequence != 0 or previous_hash is not None:
        raise ValueError("LEDGER_EPOCH_CREATED must reserve sequence zero")
    if projection["subject_type"] != "ledger":
        raise ValueError("golden epoch subject must be ledger")
    if projection["subject_id"] != projection["ledger_id"]:
        raise ValueError("golden epoch subject must equal its ledger")
    _require_exact_keys(
        projection["payload"],
        {"campaign_scope_ids"},
        context="LEDGER_EPOCH_CREATED payload",
    )
    if projection["payload"]["campaign_scope_ids"] != []:
        raise ValueError("golden epoch must be ledger-global")
    return projection


def _ledger_operation_request_projection(source: object) -> dict[str, object]:
    event = _ledger_event_identity_projection(source)
    request_keys = [
        "operation_request_projection_id",
        "ledger_schema_version",
        "event_schema_version",
        "canonicalization_id",
        "identity_projection_id",
        "ledger_id",
        "event_id",
        "operation_id",
        "event_type",
        "subject_type",
        "subject_id",
        "occurred_at",
        "actor_id",
        "payload",
    ]
    return {key: event[key] for key in request_keys}


def _require_trial_parent_semantic_order_facts(
    parent_facts: object,
) -> None:
    """Check non-append semantic trial-parent ordering facts."""
    facts = _require_exact_keys(
        parent_facts,
        {
            "epoch_sequence",
            "campaign_sequence",
            "experiment_sequence",
            "trial_sequence",
            "campaign_id",
            "experiment_id",
            "family_id",
            "trial_id",
            "sample_ids",
            "family_path",
            "sample_paths",
        },
        context="trial parent facts",
    )
    epoch_sequence = facts["epoch_sequence"]
    campaign_sequence = facts["campaign_sequence"]
    experiment_sequence = facts["experiment_sequence"]
    trial_sequence = facts["trial_sequence"]
    for field, prefix in {
        "campaign_id": "cmp",
        "experiment_id": "exp",
        "family_id": "tfm",
        "trial_id": "trl",
    }.items():
        _require_ledger_typed_id(facts[field], prefix=prefix, context=field)
    sample_ids = facts["sample_ids"]
    if (
        any(
            isinstance(sequence, bool) or not isinstance(sequence, int)
            for sequence in [
                epoch_sequence,
                campaign_sequence,
                experiment_sequence,
                trial_sequence,
            ]
        )
        or not (epoch_sequence == 0 < campaign_sequence < experiment_sequence)
        or experiment_sequence >= trial_sequence
        or not isinstance(sample_ids, list)
        or sample_ids != sorted(set(sample_ids))
        or set(facts["sample_paths"]) != set(sample_ids)
    ):
        raise ValueError("base semantic parent bindings or order are invalid")
    for sample_id in sample_ids:
        _require_ledger_typed_id(sample_id, prefix="smp", context="sample_id")

    def require_path(
        path: object,
        *,
        expected_entity_id: object,
        allow_external: bool,
    ) -> None:
        if not isinstance(path, dict):
            raise ValueError("parent path must be an object")
        kind = path.get("kind")
        if kind == "direct":
            direct_path = _require_exact_keys(
                path,
                {
                    "kind",
                    "entity_id",
                    "campaign_scope_ids",
                    "registration_sequence",
                },
                context="direct parent path facts",
            )
            campaign_scope_ids = direct_path["campaign_scope_ids"]
            if not (
                direct_path["entity_id"] == expected_entity_id
                and isinstance(campaign_scope_ids, list)
                and campaign_scope_ids == sorted(set(campaign_scope_ids))
                and facts["campaign_id"] in campaign_scope_ids
                and campaign_sequence
                < direct_path["registration_sequence"]
                < trial_sequence
            ):
                raise ValueError("direct parent path is invalid")
        elif kind == "ledger_global":
            global_path = _require_exact_keys(
                path,
                {
                    "kind",
                    "entity_id",
                    "registration_scope_ids",
                    "registration_sequence",
                    "registration_event_id",
                    "registration_event_sha256",
                    "binding_entity_id",
                    "binding_campaign_id",
                    "binding_sequence",
                    "binding_source_event_id",
                    "binding_source_event_sha256",
                },
                context="ledger-global parent path facts",
            )
            if not (
                global_path["entity_id"] == expected_entity_id
                and global_path["binding_entity_id"] == expected_entity_id
                and global_path["registration_scope_ids"] == []
                and global_path["registration_event_id"]
                == global_path["binding_source_event_id"]
                and global_path["registration_event_sha256"]
                == global_path["binding_source_event_sha256"]
                and re.fullmatch(
                    r"evt_[0-9a-f]{32}",
                    global_path["registration_event_id"],
                )
                is not None
                and re.fullmatch(
                    r"[0-9a-f]{64}",
                    global_path["registration_event_sha256"],
                )
                is not None
                and global_path["binding_campaign_id"] == facts["campaign_id"]
                and epoch_sequence < global_path["registration_sequence"]
                < global_path["binding_sequence"]
                < trial_sequence
                and epoch_sequence < campaign_sequence
                < global_path["binding_sequence"]
                < trial_sequence
            ):
                raise ValueError("ledger-global parent path is invalid")
        elif kind == "stage3_external" and allow_external:
            external_path = _require_exact_keys(
                path,
                {
                    "kind",
                    "entity_id",
                    "binding_entity_id",
                    "binding_campaign_id",
                    "binding_sequence",
                    "external_reference",
                },
                context="external Stage 3 sample path facts",
            )
            external_reference = _require_exact_keys(
                external_path["external_reference"],
                {
                    "registry_authority_id",
                    "external_sample_record_id",
                    "schema_contract_version",
                    "record_sha256",
                    "review_decision_ref_id",
                },
                context="external Stage 3 sample reference",
            )
            if not (
                all(
                    isinstance(value, str) and value
                    for value in external_reference.values()
                )
                and re.fullmatch(
                    r"[0-9a-f]{64}",
                    external_reference["record_sha256"],
                )
                is not None
                and external_path["entity_id"] == expected_entity_id
                and external_path["binding_entity_id"] == expected_entity_id
                and external_path["binding_campaign_id"] == facts["campaign_id"]
                and campaign_sequence
                < external_path["binding_sequence"]
                < trial_sequence
            ):
                raise ValueError("external Stage 3 sample path is invalid")
        else:
            raise ValueError("ambiguous or illegal parent path")

    require_path(
        facts["family_path"],
        expected_entity_id=facts["family_id"],
        allow_external=False,
    )
    for sample_id, sample_path in facts["sample_paths"].items():
        require_path(
            sample_path,
            expected_entity_id=sample_id,
            allow_external=True,
        )


def _count_entity_identity_fact_appends(source: object) -> int:
    """Evaluate allocation/reference/idempotency documentation facts."""
    if not isinstance(source, list):
        raise ValueError("entity identity facts must be a list")
    allocations: dict[str, tuple[str, int]] = {}
    committed_operations: dict[str, tuple[object, ...]] = {}
    event_ids: set[str] = set()
    sequences: set[int] = set()
    append_count = 0
    entity_prefixes = {"trial": "trl", "attempt": "att"}

    for raw_fact in source:
        fact = _require_exact_keys(
            raw_fact,
            {
                "kind",
                "entity_type",
                "entity_id",
                "event_id",
                "operation_id",
                "sequence",
                "operation_request_sha256",
            },
            context="entity identity fact",
        )
        entity_type = fact["entity_type"]
        if entity_type not in entity_prefixes:
            raise ValueError("unknown entity type")
        entity_id = _require_ledger_typed_id(
            fact["entity_id"],
            prefix=entity_prefixes[entity_type],
            context="entity identity fact",
        )
        event_id = _require_ledger_typed_id(
            fact["event_id"],
            prefix="evt",
            context="entity fact event_id",
        )
        operation_id = _require_ledger_typed_id(
            fact["operation_id"],
            prefix="opn",
            context="entity fact operation_id",
        )
        sequence = fact["sequence"]
        request_sha256 = fact["operation_request_sha256"]
        if (
            isinstance(sequence, bool)
            or not isinstance(sequence, int)
            or sequence < 0
            or not isinstance(request_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", request_sha256) is None
        ):
            raise ValueError("invalid entity identity commit fact")
        request_identity = (
            event_id,
            operation_id,
            sequence,
            request_sha256,
            entity_type,
            entity_id,
        )

        if fact["kind"] == "exact_replay":
            if committed_operations.get(operation_id) != request_identity:
                raise ValueError("replay does not match the committed request")
            continue
        if (
            operation_id in committed_operations
            or event_id in event_ids
            or sequence in sequences
        ):
            raise ValueError("conflicting operation, event, or sequence reuse")
        if fact["kind"] == "allocate":
            if entity_id in allocations:
                raise ValueError("logical entity has already been allocated")
            allocations[entity_id] = (entity_type, sequence)
        elif fact["kind"] == "reference":
            allocation = allocations.get(entity_id)
            if (
                allocation is None
                or allocation[0] != entity_type
                or sequence <= allocation[1]
            ):
                raise ValueError("reference precedes allocation or has wrong type")
        else:
            raise ValueError("unknown entity identity fact kind")

        committed_operations[operation_id] = request_identity
        event_ids.add(event_id)
        sequences.add(sequence)
        append_count += 1

    return append_count


def _utf16_sort_key(value: str) -> bytes:
    return value.encode("utf-16-be")


def _require_inventory_preseal_head_facts(
    source: object,
    *,
    retained_ledger_id: object,
    retained_predecessor_sequence: object,
    retained_predecessor_event_sha256: object,
) -> None:
    """Conformance-only facts for the nonrecursive pre-attempt seal anchor."""
    facts = _require_exact_keys(
        source,
        {
            "anchor_schema_version",
            "ledger_id",
            "predecessor_sequence",
            "predecessor_event_sha256",
            "inventory_seal_previous_event_sha256",
            "inventory_seal_sequence",
            "first_attempt_or_access_sequence",
            "anchor_fields_in_seal_preimage",
            "predecessor_event_bytes_excluded_from_seal_preimage",
            "atomic_head_compare_and_assign",
        },
        context="inventory preseal head facts",
    )
    if facts["anchor_schema_version"] != "campaign_inventory_preseal_head_v1":
        raise ValueError("unexpected inventory preseal anchor schema")
    _require_ledger_typed_id(facts["ledger_id"], prefix="ldg", context="ledger_id")
    _require_ledger_typed_id(
        retained_ledger_id, prefix="ldg", context="retained ledger_id"
    )
    if retained_ledger_id != facts["ledger_id"]:
        raise ValueError("retained ledger does not match inventory anchor")
    for field in ["predecessor_sequence", "inventory_seal_sequence", "first_attempt_or_access_sequence"]:
        value = facts[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{field} must be a nonnegative integer")
    predecessor_hash = facts["predecessor_event_sha256"]
    if not isinstance(predecessor_hash, str) or re.fullmatch(r"[0-9a-f]{64}", predecessor_hash) is None:
        raise ValueError("predecessor event hash must be lowercase SHA-256")
    if (
        isinstance(retained_predecessor_sequence, bool)
        or not isinstance(retained_predecessor_sequence, int)
        or retained_predecessor_sequence < 0
    ):
        raise ValueError("retained predecessor sequence must be a nonnegative integer")
    if (
        not isinstance(retained_predecessor_event_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", retained_predecessor_event_sha256) is None
    ):
        raise ValueError("retained predecessor hash must be lowercase SHA-256")
    if (
        retained_predecessor_sequence != facts["predecessor_sequence"]
        or retained_predecessor_event_sha256 != predecessor_hash
    ):
        raise ValueError("retained predecessor mutation invalidates inventory seal")
    if not (
        facts["predecessor_sequence"] + 1 == facts["inventory_seal_sequence"]
        and facts["inventory_seal_sequence"] < facts["first_attempt_or_access_sequence"]
        and facts["inventory_seal_previous_event_sha256"] == predecessor_hash
        and facts["anchor_fields_in_seal_preimage"] is True
        and facts["predecessor_event_bytes_excluded_from_seal_preimage"] is True
        and facts["atomic_head_compare_and_assign"] is True
    ):
        raise ValueError("inventory seal must anchor its immediate predecessor before action")


def _ordered_component_inventory_projection(source: object) -> dict[str, object]:
    projection = _require_exact_keys(
        source,
        {"schema_version", "canonicalization_id", "components"},
        context="ordered component inventory",
    )
    if projection["schema_version"] != "ordered_component_inventory_v1":
        raise ValueError("unexpected ordered inventory schema")
    if projection["canonicalization_id"] != "pit_canonical_json_v1":
        raise ValueError("unexpected ordered inventory canonicalization")
    if not isinstance(projection["components"], list):
        raise ValueError("ordered inventory components must be a list")

    normalized_components: list[dict[str, object]] = []
    seen_keys: set[tuple[str, int]] = set()
    ordinals_by_input: dict[str, set[int]] = {}
    for raw_component in projection["components"]:
        component = _require_exact_keys(
            raw_component,
            {"input_id", "component_ordinal", "raw_byte_sha256", "byte_size"},
            context="ordered component",
        )
        input_id = _require_stable_id(
            component["input_id"],
            context="component input_id",
        )
        component_ordinal = component["component_ordinal"]
        byte_size = component["byte_size"]
        if (
            not isinstance(component_ordinal, int)
            or isinstance(component_ordinal, bool)
            or not 0 <= component_ordinal <= (2**53) - 1
        ):
            raise ValueError("component ordinal must be a nonnegative safe integer")
        if (
            not isinstance(byte_size, int)
            or isinstance(byte_size, bool)
            or not 0 <= byte_size <= (2**53) - 1
        ):
            raise ValueError("byte size must be a nonnegative safe integer")
        raw_digest = component["raw_byte_sha256"]
        if (
            not isinstance(raw_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", raw_digest) is None
        ):
            raise ValueError("raw component digest must be lowercase SHA-256")
        component_key = (input_id, component_ordinal)
        if component_key in seen_keys:
            raise ValueError("duplicate component identity")
        seen_keys.add(component_key)
        ordinals_by_input.setdefault(input_id, set()).add(component_ordinal)
        normalized_components.append(dict(component))

    for input_id, ordinals in ordinals_by_input.items():
        if ordinals != set(range(len(ordinals))):
            raise ValueError(f"noncontiguous component ordinals for {input_id}")

    normalized_components.sort(
        key=lambda component: (
            _utf16_sort_key(str(component["input_id"])),
            int(component["component_ordinal"]),
        )
    )
    return {
        "schema_version": projection["schema_version"],
        "canonicalization_id": projection["canonicalization_id"],
        "components": normalized_components,
    }


def _public_redacted_projection(source: object) -> dict[str, object]:
    projection = _require_exact_keys(
        source,
        {
            "schema_version",
            "public_projection_id",
            "canonicalization_id",
            "manifest_id",
            "dataset_roles",
            "policy_states",
            "redacted_evidence_refs",
            "published_hashes",
        },
        context="public redacted projection",
    )
    if projection["schema_version"] != "public_redacted_projection_v1":
        raise ValueError("unexpected public projection schema")
    if projection["canonicalization_id"] != "pit_canonical_json_v1":
        raise ValueError("unexpected public projection canonicalization")
    public_projection_id = _require_safe_public_id(
        projection["public_projection_id"],
        context="public projection ID",
    )
    manifest_id = _require_safe_public_id(
        projection["manifest_id"],
        context="public manifest ID",
    )

    raw_roles = projection["dataset_roles"]
    if not isinstance(raw_roles, list):
        raise ValueError("dataset roles must be a list")
    roles = [
        _require_safe_public_id(role, context="dataset role")
        for role in raw_roles
    ]
    if len(roles) != len(set(roles)):
        raise ValueError("duplicate dataset role")
    roles.sort(key=_utf16_sort_key)

    raw_policy_states = projection["policy_states"]
    if not isinstance(raw_policy_states, list):
        raise ValueError("policy states must be a list")
    policy_states: list[dict[str, object]] = []
    policy_ids: set[str] = set()
    for raw_policy in raw_policy_states:
        policy = _require_exact_keys(
            raw_policy,
            {"policy_id", "state"},
            context="public policy state",
        )
        policy_id = _require_safe_public_id(
            policy["policy_id"],
            context="public policy ID",
        )
        if policy_id in policy_ids:
            raise ValueError("duplicate public policy ID")
        policy_ids.add(policy_id)
        if policy["state"] not in {"accepted", "diagnostic_only", "blocked"}:
            raise ValueError("invalid public policy state")
        policy_states.append(dict(policy))
    policy_states.sort(key=lambda item: _utf16_sort_key(str(item["policy_id"])))

    raw_evidence_refs = projection["redacted_evidence_refs"]
    if not isinstance(raw_evidence_refs, list):
        raise ValueError("redacted evidence references must be a list")
    evidence_refs: list[dict[str, object]] = []
    evidence_ids: set[str] = set()
    for raw_evidence in raw_evidence_refs:
        evidence = _require_exact_keys(
            raw_evidence,
            {"evidence_ref_id"},
            context="redacted evidence reference",
        )
        evidence_id = _require_safe_public_id(
            evidence["evidence_ref_id"],
            context="redacted evidence ID",
        )
        if evidence_id in evidence_ids:
            raise ValueError("duplicate redacted evidence ID")
        evidence_ids.add(evidence_id)
        evidence_refs.append(dict(evidence))
    evidence_refs.sort(
        key=lambda item: _utf16_sort_key(str(item["evidence_ref_id"]))
    )

    raw_hashes = projection["published_hashes"]
    if not isinstance(raw_hashes, list):
        raise ValueError("published hashes must be a list")
    published_hashes: list[dict[str, object]] = []
    hash_ids: set[str] = set()
    for raw_hash in raw_hashes:
        published_hash = _require_exact_keys(
            raw_hash,
            {"hash_id", "sha256", "publication_approval_ref_id"},
            context="publication-approved hash",
        )
        hash_id = _require_safe_public_id(
            published_hash["hash_id"],
            context="published hash ID",
        )
        if hash_id in hash_ids:
            raise ValueError("duplicate published hash ID")
        hash_ids.add(hash_id)
        digest = published_hash["sha256"]
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("published digest must be lowercase SHA-256")
        _require_safe_public_id(
            published_hash["publication_approval_ref_id"],
            context="hash publication approval reference",
        )
        published_hashes.append(dict(published_hash))
    published_hashes.sort(
        key=lambda item: _utf16_sort_key(str(item["hash_id"]))
    )

    return {
        "schema_version": projection["schema_version"],
        "public_projection_id": public_projection_id,
        "canonicalization_id": projection["canonicalization_id"],
        "manifest_id": manifest_id,
        "dataset_roles": roles,
        "policy_states": policy_states,
        "redacted_evidence_refs": evidence_refs,
        "published_hashes": published_hashes,
    }


def _assert_value_error(operation: object) -> str:
    if not callable(operation):
        raise AssertionError("operation must be callable")
    try:
        operation()
    except ValueError as error:
        return str(error)
    raise AssertionError("operation did not fail closed")


_LEDGER_EVENT_TYPES = frozenset(
    """
    LEDGER_EPOCH_CREATED CAMPAIGN_ALLOCATED EXPERIMENT_ALLOCATED
    TRIAL_FAMILY_REGISTERED SAMPLE_REGISTERED CAMPAIGN_ENTITY_BOUND
    STAGE3_SAMPLE_REFERENCE_BOUND TRIAL_ALLOCATED CAMPAIGN_INVENTORY_SEALED
    CAMPAIGN_AMENDMENT_PROPOSED CAMPAIGN_INVENTORY_AMENDED ATTEMPT_ALLOCATED
    ATTEMPT_STARTED ATTEMPT_COMPLETED ATTEMPT_FAILED ATTEMPT_INVALID
    ATTEMPT_ABORTED TRIAL_COMPLETED TRIAL_FAILED TRIAL_INVALID TRIAL_ABORTED
    TRIAL_EXCLUDED ARTIFACT_DISPOSITION_RECORDED ACCESS_INTENT ACCESS_STARTED
    ACCESS_COMPLETED ACCESS_FAILED ACCESS_ABORTED ACCESS_CANCELLED
    EXPOSURE_DECISION CAMPAIGN_EVIDENCE_FROZEN CHECKPOINT_REFERENCE_RECORDED
    CAMPAIGN_ACCOUNTING_CLOSED REVIEW_DECIDED PROMOTION_DECIDED
    CAMPAIGN_ADJUDICATED EVENT_SUPERSEDED
    """.split()
)
_EVENT_KEYS = set("ledger_id sequence event_id event_type campaign_scope_ids previous_event_sha256 facts event_sha256".split())
_CHECKPOINT_KEYS = set(
    "schema_version canonicalization_id checkpoint_id ledger_id campaign_id checkpoint_generation "
    "previous_checkpoint_id previous_checkpoint_sha256 campaign_evidence_version_id "
    "campaign_evidence_sha256 campaign_evidence_checkpoint_id campaign_evidence_checkpoint_sha256 "
    "adjudication_event_sequence adjudication_event_id adjudication_event_sha256 created_at "
    "issuer_authority_reference".split()
)
_EVIDENCE_KEYS = set("schema_version canonicalization_id checkpoint_id ledger_id campaign_id evidence_sequence evidence_event_sha256 freeze_event_sequence freeze_event_id freeze_event_sha256 campaign_evidence_version_id campaign_evidence_sha256 sealed_trial_inventory_sha256 sealed_semantic_trial_count terminal_semantic_trial_count allocated_attempt_count terminal_attempt_count created_at issuer_authority_reference".split())
_FREEZE_KEYS = set("evidence_sequence evidence_event_sha256 campaign_evidence_version_id campaign_evidence_sha256 sealed_trial_inventory_sha256 sealed_trial_ids terminal_trial_ids terminal_trial_disposition_event_type allocated_attempt_bindings terminal_attempt_ids".split())
_REFERENCE_KEYS = {"checkpoint_id", "checkpoint_sha256"}
_SYNTHETIC_UNSUPPORTED = set("TRIAL_COMPLETED TRIAL_FAILED TRIAL_INVALID TRIAL_ABORTED ATTEMPT_ALLOCATED ATTEMPT_STARTED ATTEMPT_COMPLETED ATTEMPT_FAILED ATTEMPT_INVALID ATTEMPT_ABORTED".split())
_ADJUDICATION_KEYS = set(
    "checkpoint_id campaign_evidence_version_id campaign_evidence_sha256 campaign_evidence_checkpoint_id "
    "campaign_evidence_checkpoint_sha256 sealed_trial_inventory_sha256 closure_event_sequence "
    "closure_event_id closure_event_sha256 review_event_sequence review_event_id review_event_sha256 "
    "decision_event_sequence decision_event_id decision_event_sha256 decision_outcome".split()
)
_CLOSURE_KEYS = set(
    "freeze_event_id freeze_event_sha256 campaign_evidence_version_id campaign_evidence_sha256 "
    "campaign_evidence_checkpoint_id campaign_evidence_checkpoint_sha256 sealed_trial_inventory_sha256".split()
)
_REVIEW_KEYS = set(
    "closure_event_id closure_event_sha256 campaign_evidence_checkpoint_id "
    "campaign_evidence_checkpoint_sha256 review_outcome".split()
)
_DECISION_KEYS = set(
    "review_event_id review_event_sha256 campaign_evidence_checkpoint_id "
    "campaign_evidence_checkpoint_sha256 decision_outcome".split()
)
_CURRENTNESS_KEYS = set(
    "ledger_id campaign_id current_checkpoint_generation current_checkpoint_id current_checkpoint_sha256 "
    "pending_checkpoint_generation external_currentness_proof_verified".split()
)
_LEDGER_ID = "ldg_00000000000000000000000000000001"
_CAMPAIGN_ID = "cmp_00000000000000000000000000000002"
_OTHER_CAMPAIGN_ID = "cmp_00000000000000000000000000000003"


def _safe_int(value: object, minimum: int, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= (2**53) - 1:
        raise ValueError(f"{context} must be an I-JSON-safe integer")
    return value


def _lower_sha(value: object, context: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{context} must be lowercase SHA-256")
    return value


def _campaign_tail_test_event_projection(source: object) -> dict[str, object]:
    event = _require_exact_keys(source, _EVENT_KEYS, context="test event")
    _require_ledger_typed_id(event["ledger_id"], prefix="ldg", context="ledger_id")
    _safe_int(event["sequence"], 0, "sequence")
    _require_ledger_typed_id(event["event_id"], prefix="evt", context="event_id")
    event_type = _require_stable_id(event["event_type"], context="event type")
    if event_type not in _LEDGER_EVENT_TYPES:
        raise ValueError("unknown ledger event type")
    scopes = event["campaign_scope_ids"]
    if not isinstance(scopes, list):
        raise ValueError("campaign scopes must be a list")
    for scope in scopes:
        _require_ledger_typed_id(scope, prefix="cmp", context="campaign scope")
    if scopes != sorted(set(scopes)) or not isinstance(event["facts"], dict):
        raise ValueError("campaign scopes or facts are invalid")
    if event["previous_event_sha256"] is not None:
        _lower_sha(event["previous_event_sha256"], "previous digest")
    _lower_sha(event["event_sha256"], "event digest")
    return {key: event[key] for key in _EVENT_KEYS - {"event_sha256"}}


def _verified_campaign_chain(source: object) -> list[dict[str, object]]:
    if not isinstance(source, list) or not source:
        raise ValueError("retained ledger must be nonempty")
    verified: list[dict[str, object]] = []
    seen, previous, ledger_id = set(), None, None
    for sequence, raw in enumerate(source):
        event = _campaign_tail_test_event_projection(raw)
        digest = hashlib.sha256(_ascii_jcs_golden_bytes(event)).hexdigest()
        if (event["sequence"], event["previous_event_sha256"], raw["event_sha256"]) != (sequence, previous, digest):
            raise ValueError("event sequence, chain, or digest mismatch")
        ledger_id = event["ledger_id"] if ledger_id is None else ledger_id
        if event["ledger_id"] != ledger_id or event["event_id"] in seen:
            raise ValueError("ledger ID changed or event ID duplicated")
        seen.add(event["event_id"])
        verified.append({**event, "event_sha256": digest})
        previous = digest
    epochs = [event for event in verified if event["event_type"] == "LEDGER_EPOCH_CREATED"]
    if len(epochs) != 1 or verified[0]["event_type"] != "LEDGER_EPOCH_CREATED" or epochs[0]["campaign_scope_ids"] != []:
        raise ValueError("synthetic retained chain requires one empty-scope genesis epoch")
    return verified


def _campaign_adjudication_checkpoint_projection(source: object) -> dict[str, object]:
    item = _require_exact_keys(source, _CHECKPOINT_KEYS, context="checkpoint")
    if (item["schema_version"], item["canonicalization_id"]) != (
        "campaign_adjudication_checkpoint_v1", "pit_canonical_json_v1"
    ):
        raise ValueError("checkpoint schema/canonicalization mismatch")
    for field in ("checkpoint_id", "campaign_evidence_version_id", "campaign_evidence_checkpoint_id", "issuer_authority_reference"):
        _require_stable_id(item[field], context=field)
    _require_ledger_typed_id(item["ledger_id"], prefix="ldg", context="ledger_id")
    _require_ledger_typed_id(item["campaign_id"], prefix="cmp", context="campaign_id")
    _require_ledger_typed_id(item["adjudication_event_id"], prefix="evt", context="adjudication ID")
    generation = _safe_int(item["checkpoint_generation"], 1, "generation")
    _safe_int(item["adjudication_event_sequence"], 0, "adjudication sequence")
    for field in ("campaign_evidence_sha256", "campaign_evidence_checkpoint_sha256", "adjudication_event_sha256"):
        _lower_sha(item[field], field)
    prior = item["previous_checkpoint_id"], item["previous_checkpoint_sha256"]
    if (prior[0] is None) != (prior[1] is None) or (generation == 1) != (prior == (None, None)):
        raise ValueError("checkpoint predecessor nullability mismatch")
    if prior[0] is not None:
        _require_stable_id(prior[0], context="previous checkpoint ID")
        _lower_sha(prior[1], "previous checkpoint digest")
    _require_normalized_utc_timestamp(item["created_at"], context="created_at")
    return dict(item)


def _evidence_projection(source: object) -> dict[str, object]:
    item = _require_exact_keys(source, _EVIDENCE_KEYS, context="evidence checkpoint")
    if (item["schema_version"], item["canonicalization_id"]) != ("campaign_evidence_checkpoint_v1", "pit_canonical_json_v1"):
        raise ValueError("evidence checkpoint schema/canonicalization mismatch")
    for field in ("checkpoint_id", "campaign_evidence_version_id", "issuer_authority_reference"):
        _require_stable_id(item[field], context=field)
    for field, prefix in (("ledger_id", "ldg"), ("campaign_id", "cmp"), ("freeze_event_id", "evt")):
        _require_ledger_typed_id(item[field], prefix=prefix, context=field)
    for field in ("evidence_event_sha256", "freeze_event_sha256", "campaign_evidence_sha256", "sealed_trial_inventory_sha256"):
        _lower_sha(item[field], field)
    for field in "evidence_sequence freeze_event_sequence sealed_semantic_trial_count terminal_semantic_trial_count allocated_attempt_count terminal_attempt_count".split():
        _safe_int(item[field], 0, field)
    if item["freeze_event_sequence"] != item["evidence_sequence"] + 1:
        raise ValueError("freeze sequence must equal evidence sequence plus one")
    _require_normalized_utc_timestamp(item["created_at"], context="evidence created_at")
    return dict(item)


def _evidence_record(source: object) -> dict:
    record = _require_exact_keys(source, {"checkpoint", "checkpoint_sha256"}, context="evidence record")
    item = _evidence_projection(record["checkpoint"])
    digest = _lower_sha(record["checkpoint_sha256"], "evidence checkpoint digest")
    if digest != hashlib.sha256(_ascii_jcs_golden_bytes(item)).hexdigest():
        raise ValueError("evidence checkpoint digest mismatch")
    return {**item, "checkpoint_sha256": digest}


def _campaign_prefix_object(events: list[dict], evidence: dict) -> dict:
    sequence = evidence["evidence_sequence"]
    if sequence >= len(events):
        raise ValueError("ledger is truncated below evidence cutoff")
    cutoff = events[sequence]
    if cutoff["event_sha256"] != evidence["evidence_event_sha256"]:
        raise ValueError("evidence cutoff event digest mismatch")
    campaign_id = evidence["campaign_id"]
    return {
        "schema_version": "campaign_evidence_prefix_v1",
        "canonicalization_id": "pit_canonical_json_v1",
        "ledger_id": evidence["ledger_id"], "campaign_id": campaign_id,
        "evidence_sequence": sequence, "evidence_event_sha256": evidence["evidence_event_sha256"],
        "campaign_events": [
            {"sequence": event["sequence"], "event_id": event["event_id"], "event_sha256": event["event_sha256"]}
            for event in events[: sequence + 1] if campaign_id in event["campaign_scope_ids"]
        ],
    }


def _campaign_evidence_prefix(events: list[dict], evidence: dict, candidate: object | None = None) -> dict:
    expected = _campaign_prefix_object(events, evidence)
    if candidate is not None and (not isinstance(candidate, dict) or candidate != expected):
        raise ValueError("campaign evidence prefix is not all-and-only")
    digest = hashlib.sha256(_ascii_jcs_golden_bytes(expected)).hexdigest()
    if digest != evidence["campaign_evidence_sha256"]:
        raise ValueError("campaign evidence prefix digest mismatch")
    return expected


def _typed_id_set(source: object, prefix: str, context: str) -> set[str]:
    if not isinstance(source, list):
        raise ValueError(f"{context} must be a list")
    values = {_require_ledger_typed_id(item, prefix=prefix, context=context) for item in source}
    if len(values) != len(source):
        raise ValueError(f"{context} must be unique")
    return values


def _synthetic_count_semantics(events: list[dict], facts: dict, evidence: dict) -> None:
    sealed = _typed_id_set(facts["sealed_trial_ids"], "trl", "sealed trial ID")
    terminal = _typed_id_set(facts["terminal_trial_ids"], "trl", "terminal trial ID")
    if facts["terminal_trial_disposition_event_type"] != "TRIAL_EXCLUDED":
        raise ValueError("synthetic terminal trial disposition is not fixed")
    campaign_events = [event for event in events[: evidence["evidence_sequence"] + 1] if evidence["campaign_id"] in event["campaign_scope_ids"]]
    inventories = [event for event in campaign_events if event["event_type"] == "CAMPAIGN_INVENTORY_SEALED"]
    if len(inventories) != 1:
        raise ValueError("synthetic inventory is not unique")
    inventory = _require_exact_keys(inventories[0]["facts"], {"sealed_trial_inventory_sha256", "sealed_trial_ids"}, context="synthetic inventory facts")
    inventory_trials = _typed_id_set(inventory["sealed_trial_ids"], "trl", "inventory trial ID")
    excluded_trials = _typed_id_set(
        [_require_exact_keys(event["facts"], {"trial_id"}, context="synthetic exclusion facts")["trial_id"]
         for event in campaign_events if event["event_type"] == "TRIAL_EXCLUDED"],
        "trl", "excluded trial ID",
    )
    if any(event["event_type"] in _SYNTHETIC_UNSUPPORTED for event in campaign_events):
        raise ValueError("event is outside the fixed all-excluded synthetic vector")
    attempts = facts["allocated_attempt_bindings"], facts["terminal_attempt_ids"]
    if attempts != ([], []):
        raise ValueError("synthetic vector requires exact empty attempt sets")
    counts = len(sealed), len(terminal), 0, 0
    recorded = tuple(evidence[field] for field in "sealed_semantic_trial_count terminal_semantic_trial_count allocated_attempt_count terminal_attempt_count".split())
    if (
        inventory["sealed_trial_inventory_sha256"] != evidence["sealed_trial_inventory_sha256"]
        or sealed != inventory_trials or terminal != excluded_trials or sealed != terminal or counts != recorded
    ):
        raise ValueError("synthetic trial/attempt set or count mismatch")


def _evidence_checkpoint_semantics(events: list[dict], evidence: dict, closure_sequence: int) -> None:
    _campaign_evidence_prefix(events, evidence)
    freeze_sequence = evidence["freeze_event_sequence"]
    if freeze_sequence >= len(events):
        raise ValueError("ledger is truncated below evidence freeze")
    freeze = events[freeze_sequence]
    if (
        (freeze["event_id"], freeze["event_sha256"], freeze["event_type"]) !=
        (evidence["freeze_event_id"], evidence["freeze_event_sha256"], "CAMPAIGN_EVIDENCE_FROZEN")
        or freeze["campaign_scope_ids"] != [evidence["campaign_id"]]
        or freeze["previous_event_sha256"] != evidence["evidence_event_sha256"]
    ):
        raise ValueError("evidence freeze identity/scope/predecessor mismatch")
    facts = _require_exact_keys(freeze["facts"], _FREEZE_KEYS, context="freeze facts")
    for field in "evidence_sequence evidence_event_sha256 campaign_evidence_version_id campaign_evidence_sha256 sealed_trial_inventory_sha256".split():
        if facts[field] != evidence[field]:
            raise ValueError("freeze evidence facts mismatch")
    _synthetic_count_semantics(events, facts, evidence)
    target_interval = [event for event in events[freeze_sequence + 1 : closure_sequence]
                       if evidence["campaign_id"] in event["campaign_scope_ids"]]
    if len(target_interval) != 1 or target_interval[0]["event_type"] != "CHECKPOINT_REFERENCE_RECORDED":
        raise ValueError("target campaign interval must contain only its checkpoint reference")
    reference = _require_exact_keys(target_interval[0]["facts"], _REFERENCE_KEYS, context="checkpoint reference")
    if (reference["checkpoint_id"], reference["checkpoint_sha256"]) != (evidence["checkpoint_id"], evidence["checkpoint_sha256"]):
        raise ValueError("evidence checkpoint reference mismatch")


def _checkpoint_lineage(source: object, ledger_id: str) -> tuple[str, list[tuple[dict[str, object], str]]]:
    if not isinstance(source, list) or not source:
        raise ValueError("checkpoint history must be nonempty")
    lineage: list[tuple[dict[str, object], str]] = []
    seen, campaign_id = set(), None
    for generation, raw in enumerate(source, start=1):
        record = _require_exact_keys(raw, {"checkpoint", "checkpoint_sha256"}, context="checkpoint record")
        item = _campaign_adjudication_checkpoint_projection(record["checkpoint"])
        digest = _lower_sha(record["checkpoint_sha256"], "checkpoint digest")
        prior = (None, None) if not lineage else (lineage[-1][0]["checkpoint_id"], lineage[-1][1])
        if digest != hashlib.sha256(_ascii_jcs_golden_bytes(item)).hexdigest():
            raise ValueError("checkpoint digest mismatch")
        if (item["checkpoint_generation"], item["previous_checkpoint_id"], item["previous_checkpoint_sha256"]) != (generation, *prior):
            raise ValueError("checkpoint generation/predecessor mismatch")
        campaign_id = item["campaign_id"] if campaign_id is None else campaign_id
        if item["ledger_id"] != ledger_id or item["campaign_id"] != campaign_id or item["checkpoint_id"] in seen:
            raise ValueError("checkpoint authority changed or ID duplicated")
        seen.add(item["checkpoint_id"])
        lineage.append((item, digest))
    assert isinstance(campaign_id, str)
    return campaign_id, lineage


def _evidence_binding(left: dict, right: dict, pairs: tuple[tuple[str, str], ...], context: str) -> None:
    if any(left[a] != right[b] for a, b in pairs):
        raise ValueError(f"{context} evidence binding mismatch")


def _event_ref(events: list[dict], facts: dict, prefix: str, event_type: str, campaign_id: str, anchor: int) -> dict:
    sequence = _safe_int(facts[f"{prefix}_event_sequence"], 0, f"{prefix} sequence")
    if sequence >= anchor:
        raise ValueError(f"{prefix} must precede adjudication")
    event = events[sequence]
    if (
        (event["event_id"], event["event_sha256"], event["event_type"])
        != (facts[f"{prefix}_event_id"], facts[f"{prefix}_event_sha256"], event_type)
        or campaign_id not in event["campaign_scope_ids"]
    ):
        raise ValueError(f"{prefix} reference mismatch")
    matching = [item for item in events[:anchor] if item["event_type"] == event_type and campaign_id in item["campaign_scope_ids"]]
    if not matching or matching[-1]["sequence"] != sequence:
        raise ValueError(f"{prefix} is not current")
    return event


_CHECKPOINT_EVIDENCE_BINDING = (
    ("ledger_id", "ledger_id"), ("campaign_id", "campaign_id"),
    ("campaign_evidence_version_id", "campaign_evidence_version_id"),
    ("campaign_evidence_sha256", "campaign_evidence_sha256"),
    ("campaign_evidence_checkpoint_id", "checkpoint_id"),
    ("campaign_evidence_checkpoint_sha256", "checkpoint_sha256"),
)
_ADJUDICATION_EVIDENCE_BINDING = _CHECKPOINT_EVIDENCE_BINDING[2:] + (
    ("sealed_trial_inventory_sha256", "sealed_trial_inventory_sha256"),
)
_EVIDENCE_CHECKPOINT_BINDING = (
    ("campaign_evidence_checkpoint_id", "checkpoint_id"),
    ("campaign_evidence_checkpoint_sha256", "checkpoint_sha256"),
)


def _generation_terminal_binding(events: list[dict], checkpoint: dict, evidence: dict) -> int:
    campaign_id = checkpoint["campaign_id"]
    _evidence_binding(checkpoint, evidence, _CHECKPOINT_EVIDENCE_BINDING, "checkpoint")
    anchor = checkpoint["adjudication_event_sequence"]
    if anchor >= len(events):
        raise ValueError("ledger is truncated below adjudication")
    event = events[anchor]
    if (
        (event["event_id"], event["event_sha256"], event["event_type"])
        != (checkpoint["adjudication_event_id"], checkpoint["adjudication_event_sha256"], "CAMPAIGN_ADJUDICATED")
        or campaign_id not in event["campaign_scope_ids"]
    ):
        raise ValueError("checkpoint anchor mismatch")
    facts = _require_exact_keys(event["facts"], _ADJUDICATION_KEYS, context="adjudication facts")
    if facts["checkpoint_id"] != checkpoint["checkpoint_id"]:
        raise ValueError("checkpoint preallocation mismatch")
    _evidence_binding(facts, evidence, _ADJUDICATION_EVIDENCE_BINDING, "adjudication")
    closure = _event_ref(events, facts, "closure", "CAMPAIGN_ACCOUNTING_CLOSED", campaign_id, anchor)
    review = _event_ref(events, facts, "review", "REVIEW_DECIDED", campaign_id, anchor)
    decision = _event_ref(events, facts, "decision", "PROMOTION_DECIDED", campaign_id, anchor)
    terminal_projection = [item for item in events[closure["sequence"] : anchor + 1] if campaign_id in item["campaign_scope_ids"]]
    if terminal_projection != [closure, review, decision, event]:
        raise ValueError("target campaign terminal projection mismatch")
    closure_facts = _require_exact_keys(closure["facts"], _CLOSURE_KEYS, context="closure facts")
    review_facts = _require_exact_keys(review["facts"], _REVIEW_KEYS, context="review facts")
    decision_facts = _require_exact_keys(decision["facts"], _DECISION_KEYS, context="decision facts")
    _evidence_checkpoint_semantics(events, evidence, closure["sequence"])
    _evidence_binding(
        closure_facts, evidence,
        (("freeze_event_id", "freeze_event_id"), ("freeze_event_sha256", "freeze_event_sha256"))
        + _ADJUDICATION_EVIDENCE_BINDING,
        "closure",
    )
    if (
        (review_facts["closure_event_id"], review_facts["closure_event_sha256"], review_facts["review_outcome"])
        != (closure["event_id"], closure["event_sha256"], "ACCEPTED")
        or (decision_facts["review_event_id"], decision_facts["review_event_sha256"])
        != (review["event_id"], review["event_sha256"])
    ):
        raise ValueError("review or decision predecessor mismatch")
    for item in (review_facts, decision_facts):
        _evidence_binding(item, evidence, _EVIDENCE_CHECKPOINT_BINDING, "review/decision")
    outcome = facts["decision_outcome"]
    if not isinstance(outcome, str) or outcome not in {"PROMOTED", "REJECTED", "INCONCLUSIVE", "INVALIDATED"} or decision_facts["decision_outcome"] != outcome:
        raise ValueError("terminal outcome mismatch")
    return anchor


def _current_checkpoint(source: object, ledger_id: str, campaign_id: str, lineage: list[tuple[dict, str]]) -> None:
    item = _require_exact_keys(source, _CURRENTNESS_KEYS, context="currentness")
    _require_ledger_typed_id(item["ledger_id"], prefix="ldg", context="current ledger")
    _require_ledger_typed_id(item["campaign_id"], prefix="cmp", context="current campaign")
    generation = _safe_int(item["current_checkpoint_generation"], 1, "current generation")
    _require_stable_id(item["current_checkpoint_id"], context="current checkpoint ID")
    _lower_sha(item["current_checkpoint_sha256"], "current checkpoint digest")
    pending = item["pending_checkpoint_generation"]
    if pending is not None and _safe_int(pending, 1, "pending generation") != generation + 1:
        raise ValueError("pending generation must equal current plus one")
    head, digest = lineage[-1]
    if (
        (item["ledger_id"], item["campaign_id"]) != (ledger_id, campaign_id)
        or item["external_currentness_proof_verified"] is not True or pending is not None
        or (generation, item["current_checkpoint_id"], item["current_checkpoint_sha256"])
        != (head["checkpoint_generation"], head["checkpoint_id"], digest)
    ):
        raise ValueError("checkpoint is pending, old, or externally unverified")


def _require_campaign_adjudication_checkpoint_facts(
    *, retained_events: object, retained_checkpoints: object,
    retained_evidence_checkpoints: object, currentness: object,
) -> str:
    events = _verified_campaign_chain(retained_events)
    ledger_id = events[0]["ledger_id"]
    campaign_id, lineage = _checkpoint_lineage(retained_checkpoints, ledger_id)
    if not isinstance(retained_evidence_checkpoints, list) or len(retained_evidence_checkpoints) != len(lineage):
        raise ValueError("every generation needs one evidence checkpoint")
    evidences = [_evidence_record(item) for item in retained_evidence_checkpoints]
    if len({item["checkpoint_id"] for item in evidences}) != len(evidences):
        raise ValueError("duplicate evidence checkpoint")
    anchors = []
    for (checkpoint, _), evidence in zip(lineage, evidences, strict=True):
        if (
            (evidence["ledger_id"], evidence["campaign_id"]) != (ledger_id, campaign_id)
            or checkpoint["campaign_evidence_checkpoint_id"] != evidence["checkpoint_id"]
        ):
            raise ValueError("generation/evidence correspondence mismatch")
        anchors.append(_generation_terminal_binding(events, checkpoint, evidence))
    adjudications = [
        event["sequence"] for event in events
        if event["event_type"] == "CAMPAIGN_ADJUDICATED" and campaign_id in event["campaign_scope_ids"]
    ]
    if anchors != sorted(set(anchors)) or anchors != adjudications:
        raise ValueError("generation/adjudication correspondence mismatch")
    if any(campaign_id in event["campaign_scope_ids"] for event in events[anchors[-1] + 1 :]):
        raise ValueError("post-adjudication campaign suffix is stale")
    _current_checkpoint(currentness, ledger_id, campaign_id, lineage)
    return lineage[-1][1]


def _append_tail_event(events: list[dict], event_type: str, scopes: list[str], facts: dict, nonce: int | None = None) -> dict:
    sequence = len(events)
    event = {
        "ledger_id": _LEDGER_ID, "sequence": sequence,
        "event_id": f"evt_{(nonce or sequence + 1):032x}", "event_type": event_type,
        "campaign_scope_ids": scopes,
        "previous_event_sha256": events[-1]["event_sha256"] if events else None,
        "facts": facts, "event_sha256": "0" * 64,
    }
    projection = _campaign_tail_test_event_projection(event)
    event["event_sha256"] = hashlib.sha256(_ascii_jcs_golden_bytes(projection)).hexdigest()
    events.append(event)
    return event


def _rechain_tail(
    source: list[dict], *, refresh_terminal_refs: bool = False
) -> list[dict]:
    events, previous = deepcopy(source), None
    latest = {}
    for sequence, event in enumerate(events):
        if refresh_terminal_refs:
            references = {
                "REVIEW_DECIDED": (("closure", "CAMPAIGN_ACCOUNTING_CLOSED"),),
                "PROMOTION_DECIDED": (("review", "REVIEW_DECIDED"),),
                "CAMPAIGN_ADJUDICATED": (
                    ("closure", "CAMPAIGN_ACCOUNTING_CLOSED"),
                    ("review", "REVIEW_DECIDED"),
                    ("decision", "PROMOTION_DECIDED"),
                ),
            }
            for prefix, event_type in references.get(event["event_type"], ()):
                reference = _event_reference(prefix, latest[event_type])
                if event["event_type"] != "CAMPAIGN_ADJUDICATED":
                    del reference[f"{prefix}_event_sequence"]
                event["facts"].update(reference)
        event.update(sequence=sequence, previous_event_sha256=previous, event_sha256="0" * 64)
        projection = _campaign_tail_test_event_projection(event)
        event["event_sha256"] = hashlib.sha256(_ascii_jcs_golden_bytes(projection)).hexdigest()
        previous = event["event_sha256"]
        latest[event["event_type"]] = event
    return events


def _pack_checkpoint(item: dict) -> dict:
    projection = _campaign_adjudication_checkpoint_projection(item)
    return {"checkpoint": item, "checkpoint_sha256": hashlib.sha256(_ascii_jcs_golden_bytes(projection)).hexdigest()}


def _pack_evidence_checkpoint(item: dict) -> dict:
    projection = _evidence_projection(item)
    return {
        "checkpoint": item,
        "checkpoint_sha256": hashlib.sha256(
            _ascii_jcs_golden_bytes(projection)
        ).hexdigest(),
    }


def _currentness(record: dict, pending: int | None = None) -> dict:
    item = record["checkpoint"]
    return {
        "ledger_id": item["ledger_id"], "campaign_id": item["campaign_id"],
        "current_checkpoint_generation": item["checkpoint_generation"],
        "current_checkpoint_id": item["checkpoint_id"],
        "current_checkpoint_sha256": record["checkpoint_sha256"],
        "pending_checkpoint_generation": pending,
        "external_currentness_proof_verified": True,
    }


def _event_reference(prefix: str, event: dict) -> dict:
    return {
        f"{prefix}_event_sequence": event["sequence"],
        f"{prefix}_event_id": event["event_id"],
        f"{prefix}_event_sha256": event["event_sha256"],
    }


def _build_generation(generation: int, outcome: str, events: list[dict] | None = None, previous: dict | None = None) -> tuple[list, dict, dict]:
    events = deepcopy(events) if events is not None else []
    inventory = hashlib.sha256(b"sealed-inventory").hexdigest()
    trial_id = "trl_00000000000000000000000000000001"
    if not events:
        _append_tail_event(events, "LEDGER_EPOCH_CREATED", [], {"epoch": 1})
        _append_tail_event(events, "CAMPAIGN_INVENTORY_SEALED", [_CAMPAIGN_ID], {"sealed_trial_inventory_sha256": inventory, "sealed_trial_ids": [trial_id]})
        _append_tail_event(events, "TRIAL_EXCLUDED", [_CAMPAIGN_ID], {"trial_id": trial_id})
        _append_tail_event(events, "CAMPAIGN_ACCOUNTING_CLOSED", [_OTHER_CAMPAIGN_ID], {"other_campaign_interleave": True})
        _append_tail_event(events, "TRIAL_FAMILY_REGISTERED", [], {"unbound_global_family_interleave": True})
    version, evidence_id = f"campaign-evidence-version-{generation}", f"campaign-evidence-checkpoint-{generation}"
    cutoff = events[-1]
    evidence_basis = {"ledger_id": _LEDGER_ID, "campaign_id": _CAMPAIGN_ID, "evidence_sequence": cutoff["sequence"], "evidence_event_sha256": cutoff["event_sha256"]}
    evidence_sha = hashlib.sha256(_ascii_jcs_golden_bytes(_campaign_prefix_object(events, evidence_basis))).hexdigest()
    freeze_facts = {
        "evidence_sequence": evidence_basis["evidence_sequence"], "evidence_event_sha256": evidence_basis["evidence_event_sha256"],
        "campaign_evidence_version_id": version, "campaign_evidence_sha256": evidence_sha, "sealed_trial_inventory_sha256": inventory,
        "sealed_trial_ids": [trial_id], "terminal_trial_ids": [trial_id], "terminal_trial_disposition_event_type": "TRIAL_EXCLUDED",
        "allocated_attempt_bindings": [], "terminal_attempt_ids": []}
    freeze = _append_tail_event(events, "CAMPAIGN_EVIDENCE_FROZEN", [_CAMPAIGN_ID], freeze_facts)
    evidence_item = {
        "schema_version": "campaign_evidence_checkpoint_v1", "canonicalization_id": "pit_canonical_json_v1",
        "checkpoint_id": evidence_id, "ledger_id": _LEDGER_ID, "campaign_id": _CAMPAIGN_ID, **evidence_basis,
        "freeze_event_sequence": freeze["sequence"], "freeze_event_id": freeze["event_id"], "freeze_event_sha256": freeze["event_sha256"],
        "campaign_evidence_version_id": version, "campaign_evidence_sha256": evidence_sha, "sealed_trial_inventory_sha256": inventory,
        "sealed_semantic_trial_count": 1, "terminal_semantic_trial_count": 1,
        "allocated_attempt_count": 0, "terminal_attempt_count": 0,
        "created_at": f"2026-07-27T00:00:0{generation}Z", "issuer_authority_reference": "owner-approved-authority-reference",
    }
    evidence = _pack_evidence_checkpoint(evidence_item)
    evidence_checkpoint_sha = evidence["checkpoint_sha256"]
    common = {"campaign_evidence_version_id": version, "campaign_evidence_sha256": evidence_sha, "campaign_evidence_checkpoint_id": evidence_id, "campaign_evidence_checkpoint_sha256": evidence_checkpoint_sha}
    _append_tail_event(events, "CHECKPOINT_REFERENCE_RECORDED", [_CAMPAIGN_ID], {"checkpoint_id": evidence_id, "checkpoint_sha256": evidence_checkpoint_sha})
    _append_tail_event(events, "EVENT_SUPERSEDED", [_OTHER_CAMPAIGN_ID], {"other_campaign_interval": True})
    _append_tail_event(events, "TRIAL_FAMILY_REGISTERED", [], {"global_interval": True})
    closure = _append_tail_event(events, "CAMPAIGN_ACCOUNTING_CLOSED", [_CAMPAIGN_ID], {
        **common, "freeze_event_id": freeze["event_id"], "freeze_event_sha256": freeze["event_sha256"], "sealed_trial_inventory_sha256": inventory,
    })
    _append_tail_event(events, "EVENT_SUPERSEDED", [_OTHER_CAMPAIGN_ID], {"other_campaign_terminal_interval": True})
    _append_tail_event(events, "TRIAL_FAMILY_REGISTERED", [], {"global_terminal_interval": True})
    review = _append_tail_event(
        events, "REVIEW_DECIDED", [_CAMPAIGN_ID], {"closure_event_id": closure["event_id"], "closure_event_sha256": closure["event_sha256"],
        "campaign_evidence_checkpoint_id": evidence_id, "campaign_evidence_checkpoint_sha256": evidence_checkpoint_sha, "review_outcome": "ACCEPTED"},
    )
    decision = _append_tail_event(events, "PROMOTION_DECIDED", [_CAMPAIGN_ID], {
        "review_event_id": review["event_id"], "review_event_sha256": review["event_sha256"], "campaign_evidence_checkpoint_id": evidence_id,
        "campaign_evidence_checkpoint_sha256": evidence_checkpoint_sha, "decision_outcome": outcome,
    })
    checkpoint_id = f"campaign-adjudication-checkpoint-{generation}"
    adjudication = _append_tail_event(events, "CAMPAIGN_ADJUDICATED", [_CAMPAIGN_ID], {
        **common, "checkpoint_id": checkpoint_id, "sealed_trial_inventory_sha256": inventory,
        **_event_reference("closure", closure), **_event_reference("review", review), **_event_reference("decision", decision), "decision_outcome": outcome,
    })
    prior = previous["checkpoint"] if previous else None
    item = {
        "schema_version": "campaign_adjudication_checkpoint_v1", "canonicalization_id": "pit_canonical_json_v1",
        "checkpoint_id": checkpoint_id, "ledger_id": _LEDGER_ID, "campaign_id": _CAMPAIGN_ID,
        "checkpoint_generation": generation, "previous_checkpoint_id": prior["checkpoint_id"] if prior else None,
        "previous_checkpoint_sha256": previous["checkpoint_sha256"] if previous else None,
        **common, "adjudication_event_sequence": adjudication["sequence"], "adjudication_event_id": adjudication["event_id"],
        "adjudication_event_sha256": adjudication["event_sha256"], "created_at": f"2026-07-27T00:00:0{generation}Z",
        "issuer_authority_reference": "owner-approved-authority-reference",
    }
    return events, evidence, _pack_checkpoint(item)


def _campaign_case(outcome: str = "PROMOTED", renewed: bool = False) -> dict:
    events, evidence, record = _build_generation(1, outcome)
    evidences, records = [evidence], [record]
    if renewed:
        _append_tail_event(events, "EVENT_SUPERSEDED", [_CAMPAIGN_ID], {"correction": True})
        events, evidence, record = _build_generation(2, outcome, events, record)
        evidences.append(evidence)
        records.append(record)
    return {"events": events, "evidences": evidences, "records": records, "currentness": _currentness(records[-1])}


def _verify_case(case: dict) -> str:
    return _require_campaign_adjudication_checkpoint_facts(
        retained_events=case["events"], retained_checkpoints=case["records"],
        retained_evidence_checkpoints=case["evidences"], currentness=case["currentness"],
    )


def _refresh_records(case: dict) -> None:
    refreshed = []
    for generation, record in enumerate(case["records"], start=1):
        item = deepcopy(record["checkpoint"])
        anchor = next(event for event in case["events"] if event["event_id"] == item["adjudication_event_id"])
        item.update(
            checkpoint_generation=generation, adjudication_event_sequence=anchor["sequence"],
            adjudication_event_sha256=anchor["event_sha256"],
            previous_checkpoint_id=refreshed[-1]["checkpoint"]["checkpoint_id"] if refreshed else None,
            previous_checkpoint_sha256=refreshed[-1]["checkpoint_sha256"] if refreshed else None,
        )
        refreshed.append(_pack_checkpoint(item))
    case["records"], case["currentness"] = refreshed, _currentness(refreshed[-1])


def _coherent_fact_mutation(case: dict, event_type: str, field: str, value: object) -> dict:
    case = deepcopy(case)
    next(
        item for item in reversed(case["events"])
        if item["event_type"] == event_type and _CAMPAIGN_ID in item["campaign_scope_ids"]
    )["facts"][field] = value
    case["events"] = _rechain_tail(case["events"], refresh_terminal_refs=True)
    _refresh_records(case)
    return case


def _propagated_evidence_case(*, campaign_evidence_sha256: str | None = None, forced_checkpoint_sha256: str | None = None) -> dict:
    case = _campaign_case()
    item = deepcopy(case["evidences"][0]["checkpoint"])
    if campaign_evidence_sha256 is not None:
        item["campaign_evidence_sha256"] = campaign_evidence_sha256
    evidence = _pack_evidence_checkpoint(item)
    if forced_checkpoint_sha256 is not None:
        evidence["checkpoint_sha256"] = forced_checkpoint_sha256
    case["evidences"][0] = evidence
    digest = evidence["checkpoint_sha256"]
    for event in case["events"]:
        if _CAMPAIGN_ID in event["campaign_scope_ids"]:
            facts = event["facts"]
            if event["event_type"] == "CHECKPOINT_REFERENCE_RECORDED":
                facts["checkpoint_sha256"] = digest
            if "campaign_evidence_checkpoint_sha256" in facts:
                facts["campaign_evidence_checkpoint_sha256"] = digest
            if campaign_evidence_sha256 is not None and "campaign_evidence_sha256" in facts:
                facts["campaign_evidence_sha256"] = campaign_evidence_sha256
    checkpoint = case["records"][0]["checkpoint"]
    checkpoint["campaign_evidence_checkpoint_sha256"] = digest
    if campaign_evidence_sha256 is not None:
        checkpoint["campaign_evidence_sha256"] = campaign_evidence_sha256
    case["events"] = _rechain_tail(case["events"], refresh_terminal_refs=True)
    _refresh_records(case)
    return case


def test_campaign_adjudication_checkpoint_golden_bytes_and_vocabulary() -> None:
    assert len(_LEDGER_EVENT_TYPES) == 37
    checkpoint = {
        "issuer_authority_reference": "authority-ref", "created_at": "2026-07-27T00:00:01Z",
        "adjudication_event_sha256": "d" * 64, "adjudication_event_id": "evt_00000000000000000000000000000004",
        "adjudication_event_sequence": 7, "campaign_evidence_checkpoint_sha256": "c" * 64,
        "campaign_evidence_checkpoint_id": "evidence-checkpoint-1", "campaign_evidence_sha256": "b" * 64,
        "campaign_evidence_version_id": "evidence-version-1", "previous_checkpoint_sha256": None,
        "previous_checkpoint_id": None, "checkpoint_generation": 1, "campaign_id": _CAMPAIGN_ID,
        "ledger_id": _LEDGER_ID, "checkpoint_id": "adjudication-checkpoint-1",
        "canonicalization_id": "pit_canonical_json_v1", "schema_version": "campaign_adjudication_checkpoint_v1",
    }
    expected_bytes = (
        b'{"adjudication_event_id":"evt_00000000000000000000000000000004","adjudication_event_sequence":7,'
        b'"adjudication_event_sha256":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",'
        b'"campaign_evidence_checkpoint_id":"evidence-checkpoint-1","campaign_evidence_checkpoint_sha256":'
        b'"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","campaign_evidence_sha256":'
        b'"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","campaign_evidence_version_id":'
        b'"evidence-version-1","campaign_id":"cmp_00000000000000000000000000000002","canonicalization_id":'
        b'"pit_canonical_json_v1","checkpoint_generation":1,"checkpoint_id":"adjudication-checkpoint-1",'
        b'"created_at":"2026-07-27T00:00:01Z","issuer_authority_reference":"authority-ref","ledger_id":'
        b'"ldg_00000000000000000000000000000001","previous_checkpoint_id":null,'
        b'"previous_checkpoint_sha256":null,"schema_version":"campaign_adjudication_checkpoint_v1"}'
    )
    expected_sha256 = "b5931c6c4379f2ce4dd46c69d9ecc24906a6ed2b420e1d0ae4c479cf7f83d71e"
    assert _ascii_jcs_golden_bytes(checkpoint) == expected_bytes
    assert hashlib.sha256(expected_bytes).hexdigest() == expected_sha256
    assert _pack_checkpoint(checkpoint)["checkpoint_sha256"] == expected_sha256
    assert _ascii_jcs_golden_bytes(dict(reversed(checkpoint.items()))) == expected_bytes
    assert _pack_checkpoint(dict(reversed(checkpoint.items())))["checkpoint_sha256"] == expected_sha256
    evidence_checkpoint = {
        "schema_version": "campaign_evidence_checkpoint_v1", "canonicalization_id": "pit_canonical_json_v1",
        "checkpoint_id": "evidence-checkpoint-1", "ledger_id": _LEDGER_ID, "campaign_id": _CAMPAIGN_ID,
        "evidence_sequence": 4, "evidence_event_sha256": "a" * 64, "freeze_event_sequence": 5,
        "freeze_event_id": "evt_00000000000000000000000000000006", "freeze_event_sha256": "b" * 64,
        "campaign_evidence_version_id": "evidence-version-1", "campaign_evidence_sha256": "c" * 64,
        "sealed_trial_inventory_sha256": "d" * 64, "sealed_semantic_trial_count": 1,
        "terminal_semantic_trial_count": 1, "allocated_attempt_count": 0, "terminal_attempt_count": 0,
        "created_at": "2026-07-27T00:00:01Z", "issuer_authority_reference": "authority-ref",
    }
    evidence_bytes = (
        b'{"allocated_attempt_count":0,"campaign_evidence_sha256":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",'
        b'"campaign_evidence_version_id":"evidence-version-1","campaign_id":"cmp_00000000000000000000000000000002",'
        b'"canonicalization_id":"pit_canonical_json_v1","checkpoint_id":"evidence-checkpoint-1","created_at":"2026-07-27T00:00:01Z",'
        b'"evidence_event_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","evidence_sequence":4,'
        b'"freeze_event_id":"evt_00000000000000000000000000000006","freeze_event_sequence":5,'
        b'"freeze_event_sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",'
        b'"issuer_authority_reference":"authority-ref","ledger_id":"ldg_00000000000000000000000000000001",'
        b'"schema_version":"campaign_evidence_checkpoint_v1","sealed_semantic_trial_count":1,'
        b'"sealed_trial_inventory_sha256":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",'
        b'"terminal_attempt_count":0,"terminal_semantic_trial_count":1}'
    )
    evidence_sha256 = "047f025978c986d0515a16e3bc9c3a659796eed0bcf3990cd88007ea7bdc0df7"
    assert _ascii_jcs_golden_bytes(evidence_checkpoint) == evidence_bytes
    assert hashlib.sha256(evidence_bytes).hexdigest() == evidence_sha256
    assert _pack_evidence_checkpoint(evidence_checkpoint)["checkpoint_sha256"] == evidence_sha256
    assert _pack_evidence_checkpoint(dict(reversed(evidence_checkpoint.items())))["checkpoint_sha256"] == evidence_sha256
    unknown = {
        "ledger_id": _LEDGER_ID, "sequence": 0, "event_id": "evt_00000000000000000000000000000001",
        "event_type": "LEDGER_MAINTENANCE_RECORDED", "campaign_scope_ids": [],
        "previous_event_sha256": None, "facts": {}, "event_sha256": "0" * 64,
    }
    _assert_value_error(lambda: _campaign_tail_test_event_projection(unknown))


def test_campaign_adjudication_outcomes_and_suffix_scope() -> None:
    for outcome in ("PROMOTED", "REJECTED", "INCONCLUSIVE", "INVALIDATED"):
        case = _campaign_case(outcome)
        assert _verify_case(case) == case["records"][-1]["checkpoint_sha256"]
    prefix_case = _campaign_case()
    verified = _verified_campaign_chain(prefix_case["events"])
    evidence = _evidence_record(prefix_case["evidences"][0])
    prefix = _campaign_evidence_prefix(verified, evidence)
    assert tuple(evidence[field] for field in (
        "sealed_semantic_trial_count", "terminal_semantic_trial_count", "allocated_attempt_count", "terminal_attempt_count"
    )) == (1, 1, 0, 0)
    prefix_ids = {event["event_id"] for event in prefix["campaign_events"]}
    excluded_ids = {
        event["event_id"] for event in verified[: evidence["evidence_sequence"] + 1]
        if _CAMPAIGN_ID not in event["campaign_scope_ids"]
    }
    assert prefix_ids.isdisjoint(excluded_ids)
    other = [
        {key: verified[index][key] for key in ("sequence", "event_id", "event_sha256")}
        for index in (3, 4)
    ]
    for campaign_events in (
        prefix["campaign_events"][:-1],
        prefix["campaign_events"] + [deepcopy(prefix["campaign_events"][-1])],
        list(reversed(prefix["campaign_events"])),
        [prefix["campaign_events"][0], other[0]],
        prefix["campaign_events"] + [other[1]],
    ):
        candidate = {**prefix, "campaign_events": campaign_events}
        _assert_value_error(lambda candidate=candidate: _campaign_evidence_prefix(verified, evidence, candidate))
    unrelated = _campaign_case()
    _append_tail_event(unrelated["events"], "CAMPAIGN_ACCOUNTING_CLOSED", [_OTHER_CAMPAIGN_ID], {"other_campaign": True}, 900)
    _append_tail_event(unrelated["events"], "TRIAL_FAMILY_REGISTERED", [], {"unbound_global_family": True}, 901)
    assert _verify_case(unrelated)
    for event_type in ("EVENT_SUPERSEDED", "CHECKPOINT_REFERENCE_RECORDED"):
        stale = _campaign_case()
        _append_tail_event(stale["events"], event_type, [_CAMPAIGN_ID], {"post_adjudication": True})
        _assert_value_error(lambda stale=stale: _verify_case(stale))


def test_campaign_evidence_checkpoint_semantics_fail_closed() -> None:
    case = _campaign_case()
    events = _verified_campaign_chain(case["events"])
    evidence = _evidence_record(case["evidences"][0])
    closure_sequence = next(event["sequence"] for event in events if event["event_type"] == "CAMPAIGN_ACCOUNTING_CLOSED" and event["campaign_scope_ids"] == [_CAMPAIGN_ID])
    freeze_sequence = evidence["freeze_event_sequence"]
    reference_sequence = next(event["sequence"] for event in events if event["event_type"] == "CHECKPOINT_REFERENCE_RECORDED" and _CAMPAIGN_ID in event["campaign_scope_ids"])

    def repacked(**changes: object) -> dict:
        item = deepcopy(case["evidences"][0]["checkpoint"])
        item.update(changes)
        return _evidence_record(_pack_evidence_checkpoint(item))

    def changed(sequence: int, field: str, value: object, *, facts: bool = False) -> list[dict]:
        mutated = deepcopy(events)
        target = mutated[sequence]["facts"] if facts else mutated[sequence]
        target[field] = value
        return mutated

    def rejects(mutated_events: list[dict] = events, mutated_evidence: dict = evidence, boundary: int = closure_sequence, expected: str | None = None) -> None:
        error = _assert_value_error(lambda: _evidence_checkpoint_semantics(mutated_events, mutated_evidence, boundary))
        if expected is not None:
            assert error == expected

    _evidence_checkpoint_semantics(events, evidence, closure_sequence)
    interval = events[freeze_sequence + 1 : closure_sequence]
    assert [event["event_type"] for event in interval if _CAMPAIGN_ID in event["campaign_scope_ids"]] == ["CHECKPOINT_REFERENCE_RECORDED"]
    assert any(_OTHER_CAMPAIGN_ID in event["campaign_scope_ids"] for event in interval)
    assert any(not event["campaign_scope_ids"] for event in interval)
    for mutated_events, mutated_evidence in (
        (events, repacked(evidence_sequence=3, freeze_event_sequence=4)),
        (events, repacked(evidence_event_sha256="f" * 64)),
        (events, repacked(evidence_sequence=len(events), freeze_event_sequence=len(events) + 1)),
        (events[: evidence["evidence_sequence"]], evidence),
    ):
        rejects(mutated_events, mutated_evidence)
    for field, value in (
        ("freeze_event_id", "evt_ffffffffffffffffffffffffffffffff"),
        ("freeze_event_sha256", "f" * 64),
    ):
        rejects(mutated_evidence=repacked(**{field: value}))
    for field, value in (
        ("event_type", "EVENT_SUPERSEDED"),
        ("campaign_scope_ids", [_CAMPAIGN_ID, _OTHER_CAMPAIGN_ID]),
        ("previous_event_sha256", "f" * 64),
    ):
        rejects(changed(freeze_sequence, field, value))
    rejects(changed(freeze_sequence, "unexpected", True, facts=True))
    count_error = "synthetic trial/attempt set or count mismatch"
    rejects(mutated_evidence=repacked(terminal_semantic_trial_count=0), expected=count_error)
    same_count_different_set = deepcopy(events)
    alternate_trial = "trl_ffffffffffffffffffffffffffffffff"
    same_count_different_set[freeze_sequence]["facts"].update(sealed_trial_ids=[alternate_trial], terminal_trial_ids=[alternate_trial])
    rejects(same_count_different_set, expected=count_error)
    rejects(changed(2, "event_type", "ATTEMPT_ALLOCATED"), expected="event is outside the fixed all-excluded synthetic vector")

    reference_mutations = [
        (changed(reference_sequence, "event_type", "EVENT_SUPERSEDED"), closure_sequence),
        (changed(reference_sequence, "campaign_scope_ids", [_OTHER_CAMPAIGN_ID]), closure_sequence),
        (changed(reference_sequence, "checkpoint_id", "wrong-evidence-checkpoint", facts=True), closure_sequence),
        (changed(reference_sequence, "checkpoint_sha256", "f" * 64, facts=True), closure_sequence),
    ]
    duplicate = deepcopy(events)
    duplicate.insert(closure_sequence, deepcopy(duplicate[reference_sequence]))
    reference_mutations.extend(((duplicate, closure_sequence + 1), (events, reference_sequence)))
    for mutated, boundary in reference_mutations:
        rejects(mutated, boundary=boundary)
    for nonce, (offset, event_type) in enumerate((
        (0, "EVENT_SUPERSEDED"), (1, "EVENT_SUPERSEDED"),
        (0, "CAMPAIGN_INVENTORY_AMENDED"), (0, "ACCESS_COMPLETED"), (0, "TRIAL_EXCLUDED"),
    ), start=1000):
        invalid = deepcopy(case)
        intruder = deepcopy(invalid["events"][reference_sequence])
        intruder.update(event_id=f"evt_{nonce:032x}", event_type=event_type, facts={"interval_intrusion": True})
        invalid["events"].insert(reference_sequence + offset, intruder)
        invalid["events"] = _rechain_tail(invalid["events"], refresh_terminal_refs=True)
        _refresh_records(invalid)
        assert _assert_value_error(lambda invalid=invalid: _verify_case(invalid)) == "target campaign interval must contain only its checkpoint reference"

    for invalid, expected in (
        (_propagated_evidence_case(forced_checkpoint_sha256="f" * 64), "evidence checkpoint digest mismatch"),
        (_propagated_evidence_case(campaign_evidence_sha256="f" * 64), "campaign evidence prefix digest mismatch"),
        (_coherent_fact_mutation(case, "CAMPAIGN_EVIDENCE_FROZEN", "sealed_trial_inventory_sha256", "f" * 64), "evidence freeze identity/scope/predecessor mismatch"),
    ):
        assert _assert_value_error(lambda invalid=invalid: _verify_case(invalid)) == expected


def test_campaign_adjudication_tail_mutations_fail_closed() -> None:
    base = _campaign_case()
    positions = {
        event["event_type"]: event["sequence"] for event in base["events"]
        if event["event_type"] in {"CAMPAIGN_ACCOUNTING_CLOSED", "REVIEW_DECIDED", "PROMOTION_DECIDED", "CAMPAIGN_ADJUDICATED"}
    }
    review, decision = positions["REVIEW_DECIDED"], positions["PROMOTION_DECIDED"]
    mutations = {
        "delete": [event for event in deepcopy(base["events"]) if event["sequence"] != positions["CAMPAIGN_ACCOUNTING_CLOSED"]],
        "modify": deepcopy(base["events"]), "insert": deepcopy(base["events"]),
        "duplicate": deepcopy(base["events"]), "reorder": deepcopy(base["events"]),
        "replace": deepcopy(base["events"]),
        "truncate": deepcopy(base["events"])[: positions["CAMPAIGN_ADJUDICATED"]],
    }
    mutations["modify"][review]["facts"]["review_outcome"] = "REJECTED"
    mutations["insert"].insert(review, {
        "ledger_id": _LEDGER_ID, "sequence": 0, "event_id": "evt_00000000000000000000000000000384",
        "event_type": "EVENT_SUPERSEDED", "campaign_scope_ids": [_CAMPAIGN_ID],
        "previous_event_sha256": None, "facts": {"inserted": True}, "event_sha256": "0" * 64,
    })
    mutations["duplicate"].insert(review, deepcopy(mutations["duplicate"][review]))
    mutations["reorder"][review], mutations["reorder"][decision] = mutations["reorder"][decision], mutations["reorder"][review]
    mutations["replace"][decision]["event_type"] = "EVENT_SUPERSEDED"
    for events in mutations.values():
        invalid = deepcopy(base)
        invalid["events"] = _rechain_tail(events)
        _assert_value_error(lambda invalid=invalid: _verify_case(invalid))
    coherent = {
        "closure": ("CAMPAIGN_ACCOUNTING_CLOSED", "campaign_evidence_sha256", "f" * 64, "closure evidence binding mismatch"),
        "review": ("REVIEW_DECIDED", "review_outcome", "REJECTED", "review or decision predecessor mismatch"),
        "decision": ("PROMOTION_DECIDED", "decision_outcome", "REJECTED", "terminal outcome mismatch"),
        "adjudication": ("CAMPAIGN_ADJUDICATED", "checkpoint_id", "wrong-preallocation", "checkpoint preallocation mismatch"),
    }
    for event_type, field, value, expected_error in coherent.values():
        invalid = _coherent_fact_mutation(base, event_type, field, value)
        assert _assert_value_error(
            lambda invalid=invalid: _verify_case(invalid)
        ) == expected_error
    for mode in ("missing", "replaced", "moved later", "duplicate later", "wrong scope"):
        invalid = deepcopy(base)
        if mode == "missing":
            invalid["events"].pop(0)
        elif mode == "replaced":
            invalid["events"][0]["event_type"] = "TRIAL_FAMILY_REGISTERED"
        elif mode == "moved later":
            invalid["events"].insert(1, invalid["events"].pop(0))
        elif mode == "duplicate later":
            duplicate = deepcopy(invalid["events"][0])
            duplicate["event_id"] = "evt_000000000000000000000000000004b0"
            invalid["events"].insert(2, duplicate)
        else:
            invalid["events"][0]["campaign_scope_ids"] = [_CAMPAIGN_ID]
        invalid["events"] = _rechain_tail(invalid["events"], refresh_terminal_refs=True)
        _refresh_records(invalid)
        assert _assert_value_error(lambda invalid=invalid: _verify_case(invalid)) == "synthetic retained chain requires one empty-scope genesis epoch"
    for nonce, event_type in ((1201, "REVIEW_DECIDED"), (1202, "PROMOTION_DECIDED")):
        invalid = deepcopy(base)
        position = next(event["sequence"] for event in invalid["events"] if event["event_type"] == event_type and _CAMPAIGN_ID in event["campaign_scope_ids"])
        duplicate = deepcopy(invalid["events"][position])
        duplicate["event_id"] = f"evt_{nonce:032x}"
        invalid["events"].insert(position, duplicate)
        invalid["events"] = _rechain_tail(invalid["events"], refresh_terminal_refs=True)
        _refresh_records(invalid)
        assert _assert_value_error(lambda invalid=invalid: _verify_case(invalid)) == "target campaign terminal projection mismatch"


def test_campaign_adjudication_lineage_and_currentness_fail_closed() -> None:
    renewed = _campaign_case(renewed=True)
    assert _verify_case(renewed)
    rehashed = deepcopy(renewed)
    first = deepcopy(rehashed["records"][0]["checkpoint"])
    first["campaign_evidence_sha256"] = "f" * 64
    rehashed["records"][0] = _pack_checkpoint(first)
    second = deepcopy(rehashed["records"][1]["checkpoint"])
    second["previous_checkpoint_sha256"] = rehashed["records"][0]["checkpoint_sha256"]
    rehashed["records"][1] = _pack_checkpoint(second)
    rehashed["currentness"] = _currentness(rehashed["records"][1])
    assert _assert_value_error(
        lambda: _verify_case(rehashed)
    ) == "checkpoint evidence binding mismatch"
    lineage_mutations = {}
    for name, generation, prior_id, prior_sha in (
        ("reset", 1, None, None),
        ("skip", 3, renewed["records"][0]["checkpoint"]["checkpoint_id"], renewed["records"][0]["checkpoint_sha256"]),
        ("fork", 2, "wrong-predecessor", "f" * 64),
    ):
        invalid = deepcopy(renewed)
        item = invalid["records"][1]["checkpoint"]
        item.update(checkpoint_generation=generation, previous_checkpoint_id=prior_id, previous_checkpoint_sha256=prior_sha)
        invalid["records"][1] = _pack_checkpoint(item)
        invalid["currentness"] = _currentness(invalid["records"][1])
        lineage_mutations[name] = invalid
    missing = deepcopy(renewed)
    missing["records"], missing["evidences"] = missing["records"][:1], missing["evidences"][:1]
    missing["currentness"] = _currentness(missing["records"][0])
    lineage_mutations["missing"] = missing
    sibling = deepcopy(renewed)
    sibling_item = deepcopy(sibling["records"][1]["checkpoint"])
    sibling_item["checkpoint_id"] = "campaign-adjudication-sibling-2"
    sibling["records"].append(_pack_checkpoint(sibling_item))
    sibling["evidences"].append(deepcopy(sibling["evidences"][1]))
    sibling["currentness"] = _currentness(sibling["records"][-1])
    lineage_mutations["sibling"] = sibling
    for invalid in lineage_mutations.values():
        _assert_value_error(lambda invalid=invalid: _verify_case(invalid))
    for pending in (2, 3, 1):
        invalid = _campaign_case()
        invalid["currentness"] = _currentness(invalid["records"][0], pending)
        _assert_value_error(lambda invalid=invalid: _verify_case(invalid))
    old = deepcopy(renewed)
    old["currentness"] = _currentness(old["records"][0])
    _assert_value_error(lambda: _verify_case(old))
    unverified = _campaign_case()
    unverified["currentness"]["external_currentness_proof_verified"] = False
    _assert_value_error(lambda: _verify_case(unverified))


def test_campaign_adjudication_exact_correspondence_and_schema() -> None:
    base = _campaign_case()
    original = next(event for event in base["events"] if event["event_type"] == "CAMPAIGN_ADJUDICATED")
    for nonce, checkpoint_id in ((901, "unaccounted-checkpoint"), (902, original["facts"]["checkpoint_id"])):
        invalid, extra = deepcopy(base), deepcopy(original)
        extra["event_id"], extra["facts"]["checkpoint_id"] = f"evt_{nonce:032x}", checkpoint_id
        invalid["events"].insert(original["sequence"] + 1, extra)
        invalid["events"] = _rechain_tail(invalid["events"])
        _refresh_records(invalid)
        assert _assert_value_error(
            lambda invalid=invalid: _verify_case(invalid)
        ) == "generation/adjudication correspondence mismatch"
    checkpoint_mutations = {
        "missing": ("delete", "created_at", None), "unknown": ("set", "unknown_field", "rejected"),
        "type": ("set", "checkpoint_generation", True), "ledger": ("set", "ledger_id", "ldg_" + "f" * 32),
        "evidence": ("set", "campaign_evidence_sha256", "f" * 64),
        "anchor sequence": ("set", "adjudication_event_sequence", 0),
        "anchor ID": ("set", "adjudication_event_id", "evt_ffffffffffffffffffffffffffffffff"),
        "anchor digest": ("set", "adjudication_event_sha256", "f" * 64),
    }
    for operation, field, value in checkpoint_mutations.values():
        invalid = deepcopy(base)
        item = invalid["records"][0]["checkpoint"]
        if operation == "delete" or field in {"unknown_field", "checkpoint_generation"}:
            if operation == "delete":
                del item[field]
            else:
                item[field] = value
            invalid["records"][0]["checkpoint_sha256"] = "f" * 64
        else:
            item[field] = value
            invalid["records"][0] = _pack_checkpoint(item)
            invalid["currentness"] = _currentness(invalid["records"][0])
        _assert_value_error(lambda invalid=invalid: _verify_case(invalid))
    bad_digest = deepcopy(base)
    bad_digest["records"][0]["checkpoint_sha256"] = "f" * 64
    _assert_value_error(lambda: _verify_case(bad_digest))
    evidence_mutations = {
        "missing": ("delete", "checkpoint_id", None), "unknown": ("set", "unknown_field", "rejected"),
        "schema": ("set", "schema_version", "campaign_evidence_checkpoint_v2"),
        "type": ("set", "checkpoint_id", 1),
        "Boolean": ("set", "evidence_sequence", True),
        "negative": ("set", "freeze_event_sequence", -1),
        "unsafe": ("set", "terminal_attempt_count", 2**53),
        "uppercase hash": ("set", "evidence_event_sha256", "A" * 64),
        "ID": ("set", "checkpoint_id", "wrong-evidence-checkpoint"),
        "freeze": ("set", "freeze_event_sha256", "f" * 64),
    }
    for operation, field, value in evidence_mutations.values():
        invalid = deepcopy(base)
        evidence = invalid["evidences"][0]["checkpoint"]
        if operation == "delete":
            del evidence[field]
        else:
            evidence[field] = value
        _assert_value_error(lambda invalid=invalid: _verify_case(invalid))
    for operation in ("missing digest", "unknown outer field"):
        invalid = deepcopy(base)
        if operation == "missing digest":
            del invalid["evidences"][0]["checkpoint_sha256"]
        else:
            invalid["evidences"][0]["unknown"] = True
        _assert_value_error(lambda invalid=invalid: _verify_case(invalid))
    missing_fact = deepcopy(base)
    adjudication = next(event for event in missing_fact["events"] if event["event_type"] == "CAMPAIGN_ADJUDICATED")
    del adjudication["facts"]["decision_event_sha256"]
    missing_fact["events"] = _rechain_tail(missing_fact["events"])
    _refresh_records(missing_fact)
    _assert_value_error(lambda: _verify_case(missing_fact))


def test_inventory_preseal_head_anchor_precedes_attempt_and_detects_mutation() -> None:
    facts = {
        "anchor_schema_version": "campaign_inventory_preseal_head_v1",
        "ledger_id": "ldg_00000000000000000000000000000001",
        "predecessor_sequence": 5,
        "predecessor_event_sha256": "a" * 64,
        "inventory_seal_previous_event_sha256": "a" * 64,
        "inventory_seal_sequence": 6,
        "first_attempt_or_access_sequence": 7,
        "anchor_fields_in_seal_preimage": True,
        "predecessor_event_bytes_excluded_from_seal_preimage": True,
        "atomic_head_compare_and_assign": True,
    }
    _require_inventory_preseal_head_facts(
        facts,
        retained_ledger_id="ldg_00000000000000000000000000000001",
        retained_predecessor_sequence=5,
        retained_predecessor_event_sha256="a" * 64,
    )

    mutated_predecessor = dict(facts)
    mutated_predecessor["predecessor_event_sha256"] = "b" * 64
    assert mutated_predecessor["predecessor_event_sha256"] != facts[
        "predecessor_event_sha256"
    ]
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            mutated_predecessor,
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=5,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            facts,
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=4,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            {**facts, "inventory_seal_sequence": 7},
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=5,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            {**facts, "first_attempt_or_access_sequence": 6},
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=5,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            {**facts, "atomic_head_compare_and_assign": False},
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=5,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            facts,
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=6,
            retained_predecessor_event_sha256="c" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            {**facts, "inventory_seal_previous_event_sha256": "b" * 64},
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=5,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            facts,
            retained_ledger_id="ldg_00000000000000000000000000000002",
            retained_predecessor_sequence=5,
            retained_predecessor_event_sha256="a" * 64,
        )
    )
    _assert_value_error(
        lambda: _require_inventory_preseal_head_facts(
            {
                **facts,
                "predecessor_sequence": None,
                "predecessor_event_sha256": None,
            },
            retained_ledger_id="ldg_00000000000000000000000000000001",
            retained_predecessor_sequence=0,
            retained_predecessor_event_sha256="a" * 64,
        )
    )


def test_pit_canonical_json_v1_golden_bytes_and_digest() -> None:
    fixture = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/pit_canonical_json_v1_golden.json"
        ).read_text(encoding="utf-8")
    )
    canonical_text = _ascii_jcs_golden_bytes(fixture["semantic_input"]).decode()

    assert fixture["schema_version"] == "pit_canonical_json_v1_golden_v2"
    assert canonical_text == fixture["canonical_utf8"]
    assert " " not in canonical_text
    assert (
        hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
        == fixture["sha256"]
    )


def test_ordered_manifest_sha256_golden_reorder_and_mutation_vectors() -> None:
    fixture = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/pit_canonical_json_v1_golden.json"
        ).read_text(encoding="utf-8")
    )["ordered_manifest_sha256_vectors"]

    base_bytes = _ascii_jcs_golden_bytes(
        _ordered_component_inventory_projection(fixture["semantic_input"])
    )
    reordered_bytes = _ascii_jcs_golden_bytes(
        _ordered_component_inventory_projection(
            fixture["reordered_semantic_input"]
        )
    )
    mutated_bytes = _ascii_jcs_golden_bytes(
        _ordered_component_inventory_projection(
            fixture["mutated_semantic_input"]
        )
    )

    assert base_bytes.decode() == fixture["canonical_utf8"]
    assert reordered_bytes == base_bytes
    assert hashlib.sha256(base_bytes).hexdigest() == fixture["sha256"]
    assert hashlib.sha256(reordered_bytes).hexdigest() == fixture["sha256"]
    assert mutated_bytes.decode() == fixture["mutated_canonical_utf8"]
    assert hashlib.sha256(mutated_bytes).hexdigest() == fixture["mutated_sha256"]
    assert fixture["mutated_sha256"] != fixture["sha256"]

    duplicate_component = json.loads(json.dumps(fixture["semantic_input"]))
    duplicate_component["components"].append(
        dict(duplicate_component["components"][0])
    )
    _assert_value_error(
        lambda: _ordered_component_inventory_projection(duplicate_component)
    )
    unknown_component_key = json.loads(json.dumps(fixture["semantic_input"]))
    unknown_component_key["components"][0]["path"] = "private.csv"
    _assert_value_error(
        lambda: _ordered_component_inventory_projection(unknown_component_key)
    )


def test_public_projection_sha256_golden_reorder_and_mutation_vectors() -> None:
    fixture = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/pit_canonical_json_v1_golden.json"
        ).read_text(encoding="utf-8")
    )["public_projection_sha256_vectors"]

    base_bytes = _ascii_jcs_golden_bytes(
        _public_redacted_projection(fixture["semantic_input"])
    )
    reordered_bytes = _ascii_jcs_golden_bytes(
        _public_redacted_projection(fixture["reordered_semantic_input"])
    )
    mutated_bytes = _ascii_jcs_golden_bytes(
        _public_redacted_projection(fixture["mutated_semantic_input"])
    )

    assert base_bytes.decode() == fixture["canonical_utf8"]
    assert reordered_bytes == base_bytes
    assert hashlib.sha256(base_bytes).hexdigest() == fixture["sha256"]
    assert hashlib.sha256(reordered_bytes).hexdigest() == fixture["sha256"]
    assert mutated_bytes.decode() == fixture["mutated_canonical_utf8"]
    assert hashlib.sha256(mutated_bytes).hexdigest() == fixture["mutated_sha256"]
    assert fixture["mutated_sha256"] != fixture["sha256"]

    duplicate_policy = json.loads(json.dumps(fixture["semantic_input"]))
    duplicate_policy["policy_states"].append(
        dict(duplicate_policy["policy_states"][0])
    )
    _assert_value_error(lambda: _public_redacted_projection(duplicate_policy))
    unknown_public_key = dict(fixture["semantic_input"])
    unknown_public_key["private_path"] = "/private/data.csv"
    _assert_value_error(lambda: _public_redacted_projection(unknown_public_key))
    private_manifest_locator = json.loads(json.dumps(fixture["semantic_input"]))
    private_manifest_locator["manifest_id"] = "/private/data.csv"
    _assert_value_error(
        lambda: _public_redacted_projection(private_manifest_locator)
    )
    private_evidence_uri = json.loads(json.dumps(fixture["semantic_input"]))
    private_evidence_uri["redacted_evidence_refs"][0]["evidence_ref_id"] = (
        "file://private/data.csv"
    )
    _assert_value_error(lambda: _public_redacted_projection(private_evidence_uri))
    private_approval_identity = json.loads(json.dumps(fixture["semantic_input"]))
    private_approval_identity["published_hashes"][0][
        "publication_approval_ref_id"
    ] = "owner@example.com"
    _assert_value_error(
        lambda: _public_redacted_projection(private_approval_identity)
    )


def test_ledger_epoch_golden_semantic_facts_and_fail_closed_vectors() -> None:
    fixture = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/experiment_trial_ledger_event_v1_golden.json"
        ).read_text(encoding="utf-8")
    )
    base_bytes = _ascii_jcs_golden_bytes(
        _ledger_event_identity_projection(fixture["semantic_input"])
    )
    reordered_bytes = _ascii_jcs_golden_bytes(
        _ledger_event_identity_projection(fixture["reordered_semantic_input"])
    )
    mutated_bytes = _ascii_jcs_golden_bytes(
        _ledger_event_identity_projection(fixture["mutated_semantic_input"])
    )
    base_request_bytes = _ascii_jcs_golden_bytes(
        _ledger_operation_request_projection(fixture["semantic_input"])
    )
    reordered_request_bytes = _ascii_jcs_golden_bytes(
        _ledger_operation_request_projection(fixture["reordered_semantic_input"])
    )
    mutated_request_bytes = _ascii_jcs_golden_bytes(
        _ledger_operation_request_projection(fixture["mutated_semantic_input"])
    )

    assert (
        fixture["schema_version"]
        == "experiment_trial_ledger_event_v1_golden_v2"
    )
    assert fixture["semantic_input"]["event_type"] == "LEDGER_EPOCH_CREATED"
    assert fixture["semantic_input"]["sequence"] == 0
    assert fixture["semantic_input"]["previous_event_sha256"] is None
    fractional_timestamp_event = json.loads(json.dumps(fixture["semantic_input"]))
    fractional_timestamp_event["occurred_at"] = "2024-02-29T23:59:59.123456789Z"
    fractional_timestamp_event["recorded_at"] = "2024-03-01T00:00:00.000001Z"
    assert _ledger_event_identity_projection(fractional_timestamp_event)[
        "occurred_at"
    ].endswith(".123456789Z")
    arbitrary_precision_timestamp_event = json.loads(
        json.dumps(fixture["semantic_input"])
    )
    arbitrary_precision_timestamp_event["occurred_at"] = (
        "2024-02-29T23:59:59.1234567890123456789Z"
    )
    arbitrary_precision_timestamp_event["recorded_at"] = (
        "2024-03-01T00:00:00.0000000000000000001Z"
    )
    arbitrary_precision_projection = _ledger_event_identity_projection(
        arbitrary_precision_timestamp_event
    )
    assert arbitrary_precision_projection["occurred_at"] == (
        "2024-02-29T23:59:59.1234567890123456789Z"
    )
    assert arbitrary_precision_projection["recorded_at"] == (
        "2024-03-01T00:00:00.0000000000000000001Z"
    )
    year_zero_event = json.loads(json.dumps(fixture["semantic_input"]))
    year_zero_event["occurred_at"] = "0000-02-29T00:00:00Z"
    assert (
        _ledger_event_identity_projection(year_zero_event)["occurred_at"]
        == "0000-02-29T00:00:00Z"
    )
    for invalid_timestamp in [
        "2026-02-29T00:00:00Z",
        "0001-02-29T00:00:00Z",
        "0001-00-01T00:00:00Z",
        "2026-13-01T00:00:00Z",
        "0001-04-31T00:00:00Z",
        "0001-01-00T00:00:00Z",
        "2026-01-01T24:00:00Z",
        "2026-01-01T23:60:00Z",
        "2026-01-01T23:59:60Z",
        "2026-01-01T23:59:61Z",
        "1990-12-31T23:59:60Z",
        "1990-12-31T23:59:60.1234567890123456789Z",
        "1990-12-31T23:59:60.120Z",
        "2015-06-30T23:59:60Z",
        "2015-06-30T23:59:60.1Z",
        "2016-12-31T23:59:60Z",
        "2016-12-31T23:59:60.1Z",
        "2024-06-30T23:59:60Z",
        "2024-06-30T23:59:60.1Z",
        "2026-12-31T23:59:60Z",
        "2026-12-31T23:59:60.1Z",
        "2024-06-30T22:59:60Z",
        "2024-06-29T23:59:60Z",
        "2026-01-01T00:00:00.000Z",
        "2026-01-01T00:00:00.120Z",
        "2026-01-01T00:00:00.Z",
        "2026-01-01T00:00:00+00:00",
    ]:
        for timestamp_field in ["occurred_at", "recorded_at"]:
            invalid_timestamp_event = json.loads(
                json.dumps(fixture["semantic_input"])
            )
            invalid_timestamp_event[timestamp_field] = invalid_timestamp
            _assert_value_error(
                lambda event=invalid_timestamp_event: (
                    _ledger_event_identity_projection(event)
                )
            )

    assert (
        base_request_bytes.decode()
        == fixture["operation_request_canonical_utf8"]
    )
    assert reordered_request_bytes == base_request_bytes
    assert (
        hashlib.sha256(base_request_bytes).hexdigest()
        == fixture["operation_request_sha256"]
        == fixture["semantic_input"]["operation_request_sha256"]
    )
    assert (
        hashlib.sha256(reordered_request_bytes).hexdigest()
        == fixture["operation_request_sha256"]
        == fixture["reordered_semantic_input"]["operation_request_sha256"]
    )
    assert (
        mutated_request_bytes.decode()
        == fixture["mutated_operation_request_canonical_utf8"]
    )
    assert (
        hashlib.sha256(mutated_request_bytes).hexdigest()
        == fixture["mutated_operation_request_sha256"]
        == fixture["mutated_semantic_input"]["operation_request_sha256"]
    )
    assert (
        fixture["mutated_operation_request_sha256"]
        != fixture["operation_request_sha256"]
    )
    assert (
        fixture["mutated_semantic_input"]["operation_id"]
        == fixture["semantic_input"]["operation_id"]
    )
    assert base_bytes.decode() == fixture["canonical_utf8"]
    assert reordered_bytes == base_bytes
    assert hashlib.sha256(base_bytes).hexdigest() == fixture["sha256"]
    assert hashlib.sha256(reordered_bytes).hexdigest() == fixture["sha256"]
    assert mutated_bytes.decode() == fixture["mutated_canonical_utf8"]
    assert hashlib.sha256(mutated_bytes).hexdigest() == fixture["mutated_sha256"]
    assert fixture["mutated_sha256"] != fixture["sha256"]

    unknown_event_key = dict(fixture["semantic_input"])
    unknown_event_key["event_sha256"] = fixture["sha256"]
    _assert_value_error(
        lambda: _ledger_event_identity_projection(unknown_event_key)
    )
    unauthorized_actor_binding = json.loads(json.dumps(fixture["semantic_input"]))
    unauthorized_actor_binding["payload"]["genesis_principal_binding"] = {}
    _assert_value_error(
        lambda: _ledger_event_identity_projection(unauthorized_actor_binding)
    )
    missing_event_key = dict(fixture["semantic_input"])
    del missing_event_key["operation_request_sha256"]
    _assert_value_error(
        lambda: _ledger_event_identity_projection(missing_event_key)
    )
    invalid_typed_id = json.loads(json.dumps(fixture["semantic_input"]))
    invalid_typed_id["subject_id"] = "ledger-readable-name"
    _assert_value_error(
        lambda: _ledger_event_identity_projection(invalid_typed_id)
    )
    for invalid_actor_id in [
        "usr_00000000000000000000000000000004",
        "act_0000000000000000000000000000004",
        "act_0000000000000000000000000000000A",
        "act_0000000000000000000000000000000é",
    ]:
        invalid_actor = json.loads(json.dumps(fixture["semantic_input"]))
        invalid_actor["actor_id"] = invalid_actor_id
        _assert_value_error(
            lambda event=invalid_actor: _ledger_event_identity_projection(event)
        )
    incomplete_trial_stub = fixture["incomplete_trial_allocation_stub"]
    _assert_value_error(
        lambda: _ledger_event_identity_projection(incomplete_trial_stub)
    )
    sequence_repaired_stub = json.loads(json.dumps(incomplete_trial_stub))
    sequence_repaired_stub["sequence"] = 1
    sequence_repaired_stub["previous_event_sha256"] = fixture["sha256"]
    _assert_value_error(
        lambda: _ledger_event_identity_projection(sequence_repaired_stub)
    )

    # Independent semantic facts; these do not project the rejected stub payload.
    campaign_id = "cmp_00000000000000000000000000000005"
    experiment_id = "exp_00000000000000000000000000000006"
    family_id = "tfm_00000000000000000000000000000007"
    trial_id = "trl_00000000000000000000000000000008"
    sample_id = "smp_0000000000000000000000000000000b"

    def facts(
        campaign_sequence: int,
        experiment_sequence: int,
        trial_sequence: int,
        family_path: dict[str, object],
        sample_path: dict[str, object],
    ) -> dict[str, object]:
        return {
            "epoch_sequence": 0,
            "campaign_sequence": campaign_sequence,
            "experiment_sequence": experiment_sequence,
            "trial_sequence": trial_sequence,
            "campaign_id": campaign_id,
            "experiment_id": experiment_id,
            "family_id": family_id,
            "trial_id": trial_id,
            "sample_ids": [sample_id],
            "family_path": family_path,
            "sample_paths": {sample_id: sample_path},
        }

    def direct(
        sequence: int,
        entity_id: str,
        campaign_scope_ids: list[str] | None = None,
    ) -> dict[str, object]:
        return {
            "kind": "direct",
            "entity_id": entity_id,
            "campaign_scope_ids": campaign_scope_ids or [campaign_id],
            "registration_sequence": sequence,
        }

    def ledger_global(
        registration_sequence: int,
        binding_sequence: int,
        entity_id: str,
    ) -> dict[str, object]:
        registration_event_id = f"evt_{registration_sequence:032x}"
        registration_event_sha256 = f"{registration_sequence:064x}"
        return {
            "kind": "ledger_global",
            "entity_id": entity_id,
            "registration_scope_ids": [],
            "registration_sequence": registration_sequence,
            "registration_event_id": registration_event_id,
            "registration_event_sha256": registration_event_sha256,
            "binding_entity_id": entity_id,
            "binding_campaign_id": campaign_id,
            "binding_sequence": binding_sequence,
            "binding_source_event_id": registration_event_id,
            "binding_source_event_sha256": registration_event_sha256,
        }

    def stage3_external(
        binding_sequence: int,
        entity_id: str,
    ) -> dict[str, object]:
        return {
            "kind": "stage3_external",
            "entity_id": entity_id,
            "binding_entity_id": entity_id,
            "binding_campaign_id": campaign_id,
            "binding_sequence": binding_sequence,
            "external_reference": {
                "registry_authority_id": "registry-authority",
                "external_sample_record_id": "sample-record",
                "schema_contract_version": "schema-version",
                "record_sha256": "b" * 64,
                "review_decision_ref_id": "review-reference",
            },
        }

    direct_facts = facts(1, 4, 5, direct(3, family_id), direct(2, sample_id))
    other_campaign_id = "cmp_00000000000000000000000000000004"
    shared_direct_facts = facts(
        1,
        4,
        5,
        direct(3, family_id, [other_campaign_id, campaign_id]),
        direct(2, sample_id),
    )
    global_facts = facts(
        3,
        4,
        7,
        ledger_global(1, 5, family_id),
        ledger_global(2, 6, sample_id),
    )
    late_global_facts = facts(
        1,
        2,
        7,
        ledger_global(3, 5, family_id),
        ledger_global(4, 6, sample_id),
    )
    external_facts = facts(
        1,
        3,
        5,
        direct(4, family_id),
        stage3_external(2, sample_id),
    )
    for valid_facts in [
        direct_facts,
        shared_direct_facts,
        global_facts,
        late_global_facts,
        external_facts,
    ]:
        _require_trial_parent_semantic_order_facts(valid_facts)

    invalid_cases: list[dict[str, object]] = []

    def invalid_path(
        base: dict[str, object],
        *,
        sample: bool = False,
    ) -> dict[str, object]:
        invalid = json.loads(json.dumps(base))
        invalid_cases.append(invalid)
        return (
            invalid["sample_paths"][sample_id]
            if sample
            else invalid["family_path"]
        )

    invalid_path(direct_facts)["registration_sequence"] = 0
    invalid_path(direct_facts)["binding_source_event_id"] = "extra-global-field"
    invalid_path(direct_facts)["external_reference"] = {"extra": "external-field"}
    invalid_path(global_facts, sample=True)["binding_entity_id"] = family_id
    invalid_path(global_facts)["binding_campaign_id"] = other_campaign_id
    invalid_path(global_facts)["binding_source_event_id"] = f"evt_{99:032x}"
    invalid_path(global_facts)["binding_source_event_sha256"] = "f" * 64
    invalid_path(direct_facts)["campaign_scope_ids"] = [other_campaign_id]
    invalid_path(direct_facts)["campaign_scope_ids"] = [campaign_id, campaign_id]
    invalid_path(direct_facts)["campaign_scope_ids"] = [
        campaign_id,
        other_campaign_id,
    ]
    missing_external = invalid_path(external_facts, sample=True)
    del missing_external["external_reference"]["record_sha256"]
    unknown_external = invalid_path(external_facts, sample=True)
    unknown_external["external_reference"]["unknown_field"] = "rejected"

    for invalid_facts in invalid_cases:
        _assert_value_error(
            lambda invalid_facts=invalid_facts: _require_trial_parent_semantic_order_facts(
                invalid_facts,
            )
        )

    def entity_fact(
        kind: str,
        sequence: int,
        *,
        event_suffix: int,
        operation_suffix: int,
        request_digit: str,
    ) -> dict[str, object]:
        return {
            "kind": kind,
            "entity_type": "trial",
            "entity_id": trial_id,
            "event_id": f"evt_{event_suffix:032x}",
            "operation_id": f"opn_{operation_suffix:032x}",
            "sequence": sequence,
            "operation_request_sha256": request_digit * 64,
        }

    allocation_fact = entity_fact(
        "allocate",
        1,
        event_suffix=21,
        operation_suffix=31,
        request_digit="1",
    )
    lifecycle_reference_fact = entity_fact(
        "reference",
        2,
        event_suffix=22,
        operation_suffix=32,
        request_digit="2",
    )
    assert (
        _count_entity_identity_fact_appends(
            [allocation_fact, lifecycle_reference_fact]
        )
        == 2
    )
    exact_replay_fact = dict(allocation_fact)
    exact_replay_fact["kind"] = "exact_replay"
    assert (
        _count_entity_identity_fact_appends([allocation_fact, exact_replay_fact])
        == 1
    )

    duplicate_allocation = entity_fact(
        "allocate",
        3,
        event_suffix=23,
        operation_suffix=33,
        request_digit="3",
    )
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends(
            [allocation_fact, duplicate_allocation]
        )
    )
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends([lifecycle_reference_fact])
    )
    allocation_at_two = dict(allocation_fact)
    allocation_at_two["sequence"] = 2
    reference_at_one = dict(lifecycle_reference_fact)
    reference_at_one["sequence"] = 1
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends(
            [allocation_at_two, reference_at_one]
        )
    )
    wrong_type_reference = dict(lifecycle_reference_fact)
    wrong_type_reference["entity_type"] = "attempt"
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends(
            [allocation_fact, wrong_type_reference]
        )
    )
    conflicting_replay = dict(exact_replay_fact)
    conflicting_replay["operation_request_sha256"] = "f" * 64
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends(
            [allocation_fact, conflicting_replay]
        )
    )
    duplicate_event_reference = dict(lifecycle_reference_fact)
    duplicate_event_reference["event_id"] = allocation_fact["event_id"]
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends(
            [allocation_fact, duplicate_event_reference]
        )
    )
    duplicate_sequence_reference = dict(lifecycle_reference_fact)
    duplicate_sequence_reference["sequence"] = allocation_fact["sequence"]
    _assert_value_error(
        lambda: _count_entity_identity_fact_appends(
            [allocation_fact, duplicate_sequence_reference]
        )
    )

    _assert_value_error(
        lambda: _ascii_jcs_golden_bytes({"allowed_key": 1.5})
    )


def test_stage_three_tracked_policy_files_fail_closed_on_private_identifiers() -> None:
    tracked_policy_paths = [
        ".agents/skills/real-data-readiness-audit/SKILL.md",
        "EXPERIMENT_LOG.md",
        "docs/local_csv_study_checklist.md",
        "docs/local_csv_readiness_audit_report_template.md",
        "docs/point_in_time_data_methodology_contract.md",
        "docs/experiment_trial_ledger_contract.md",
        "docs/experiment_trial_ledger_allocation_registration_schema_contract.md",
        "docs/real_data_readiness_audit.md",
    ]

    for relative_path in tracked_policy_paths:
        text = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
        assert "/Users/" not in text
        assert "/home/" not in text
        assert "/private/tmp/" not in text
        assert "file://" not in text
        assert re.search(r"(?i)\b[a-z]:[\\/]", text) is None
        assert re.search(r"\b[0-9a-fA-F]{64}\b", text) is None

    for relative_path in tracked_policy_paths[:4] + [tracked_policy_paths[-1]]:
        normalized_text = " ".join(
            (PROJECT_ROOT / relative_path)
            .read_text(encoding="utf-8")
            .split()
        )
        assert (
            "publication-approved hash or redacted private-evidence reference"
            in normalized_text
        )

    checklist = (
        PROJECT_ROOT / "docs/local_csv_study_checklist.md"
    ).read_text(encoding="utf-8")
    audit_template = (
        PROJECT_ROOT / "docs/local_csv_readiness_audit_report_template.md"
    ).read_text(encoding="utf-8")
    experiment_log = (PROJECT_ROOT / "EXPERIMENT_LOG.md").read_text(
        encoding="utf-8"
    )
    assert "| Actual hash |" not in checklist
    assert "| Actual hash |" not in audit_template
    assert "License documents, contract/account IDs" in experiment_log
    assert (
        "Private performance values remain outside tracked records"
        in " ".join(experiment_log.split())
    )


def test_readiness_and_experiment_records_do_not_bypass_program_gates() -> None:
    readiness_skill = (
        PROJECT_ROOT / ".agents/skills/real-data-readiness-audit/SKILL.md"
    ).read_text(encoding="utf-8")
    readiness_audit = (
        PROJECT_ROOT / "docs/real_data_readiness_audit.md"
    ).read_text(encoding="utf-8")
    experiment_log = (PROJECT_ROOT / "EXPERIMENT_LOG.md").read_text(
        encoding="utf-8"
    )
    study_checklist = (
        PROJECT_ROOT / "docs/local_csv_study_checklist.md"
    ).read_text(encoding="utf-8")
    audit_template = (
        PROJECT_ROOT / "docs/local_csv_readiness_audit_report_template.md"
    ).read_text(encoding="utf-8")
    controller = (
        PROJECT_ROOT / "docs/codex_long_running_controller.md"
    ).read_text(encoding="utf-8")
    methodology_contract = (
        PROJECT_ROOT / "docs/point_in_time_data_methodology_contract.md"
    ).read_text(encoding="utf-8")

    for text in [readiness_skill, readiness_audit, methodology_contract]:
        normalized_text = " ".join(text.split())
        assert "docs/research_program_charter.md" in normalized_text
        assert "docs/current_roadmap.md" in normalized_text
        assert "`diagnostic_ready`" in normalized_text
        assert "`formal_ready`" in normalized_text
        assert "static current" in normalized_text
        assert "blocks formal interpretation" in normalized_text
        assert "immutable all-trial ledger" in normalized_text

    for text in [readiness_skill, readiness_audit, experiment_log]:
        normalized_text = " ".join(text.split())
        assert "canonicalization_id" in normalized_text
        assert "environment_id" in normalized_text
        assert "environment_lock_sha256" in normalized_text
        assert "known_at <= decision_time" in normalized_text
        assert "non-self-issued exact-version dataset-review decision" in normalized_text

    for text in [readiness_skill, readiness_audit]:
        normalized_text = " ".join(text.split())
        assert "unlocked/incomplete environment" in normalized_text
        assert (
            "A diagnostic-scope audit may return `diagnostic_ready` without a "
            "dataset-review decision"
        ) in normalized_text
        assert "`dataset_manifest_reviewed = false`" in normalized_text
        assert "`formal_interpretation_eligible = false`" in normalized_text
        assert "formal readiness remains blocked" in normalized_text
        assert "the outcome is not `formal_ready`" in normalized_text
        assert (
            "when formal interpretation is proposed, the dataset-review "
            "decision is absent"
        ) in normalized_text.lower()
        assert (
            "when formal interpretation is proposed, the immutable "
            "dataset-review decision id"
        ) in normalized_text.lower()
        assert (
            "for diagnostic scope without a dataset-review decision, do not "
            "fabricate a decision id"
        ) in normalized_text.lower()
        assert (
            "access-record and exposure-decision ids"
        ) in normalized_text.lower()
        assert "remain scope-applicable for diagnostics" in normalized_text.lower()

    normalized_readiness_skill = " ".join(readiness_skill.split()).lower()
    assert (
        "when formal interpretation is proposed, `dataset_manifest_reviewed` "
        "or `formal_interpretation_eligible` is absent"
    ) in normalized_readiness_skill
    assert (
        "- `dataset_manifest_reviewed` or "
        "`formal_interpretation_eligible` is absent"
    ) not in readiness_skill
    assert "- the dataset-review decision is absent" not in readiness_skill.lower()
    assert "- the dataset-review decision is absent" not in readiness_audit.lower()
    assert "finding dispositions, and exposure-decision id" not in (
        normalized_readiness_skill
    )

    for text in [experiment_log, study_checklist, audit_template]:
        normalized_text = " ".join(text.split()).lower()
        assert (
            "when formal interpretation is proposed, the immutable "
            "dataset-review decision"
        ) in normalized_text
        assert (
            "for diagnostic scope without a dataset-review decision, do not "
            "fabricate a decision id"
        ) in normalized_text
        assert "`dataset_manifest_reviewed = false`" in normalized_text
        assert "`formal_interpretation_eligible = false`" in normalized_text
        assert "protected-sample access-record" in normalized_text
        assert "exposure-decision id" in normalized_text
        assert "stop if the immutable decision is absent" not in normalized_text
        assert (
            "- immutable dataset-review decision id and exposure-decision id"
            not in normalized_text
        )

    for text in [study_checklist, audit_template]:
        normalized_text = " ".join(text.split()).lower()
        assert "every scope-applicable statement" in normalized_text
        assert "[formal interpretation only] dataset review" in normalized_text
        assert "the formal-only dataset-review box is outside scope" in normalized_text

    for phrase in [
        "diagnostic/legacy experiment record",
        "not the immutable all-trial ledger",
        "must not support formal historical interpretation",
        "Every configured case",
        "Tracked records must not contain private absolute paths",
    ]:
        assert phrase in " ".join(experiment_log.split())

    for text in [
        methodology_contract,
        readiness_skill,
        readiness_audit,
        experiment_log,
    ]:
        normalized_text = " ".join(text.split())
        assert "2025-05-01 through 2026-05-31" in normalized_text
        assert "`historical_evaluation`" in normalized_text

    assert "## Predecessor PR Gate" in controller
    assert "## Stop Conditions" in controller
    assert "Eligibility is not authorization" in controller
    assert "docs/eodhd_sp500_diagnostic_campaign_contract.md" in controller


def test_controller_applies_same_pr_lifecycle_authorization() -> None:
    controller = (
        PROJECT_ROOT / "docs/codex_long_running_controller.md"
    ).read_text(encoding="utf-8")
    review_lifecycle = " ".join(
        _markdown_section(controller, "GitHub Review Lifecycle").split()
    )

    for phrase in [
        "Automatic Review disabled",
        "Drafts get no request",
        "Mark it Ready",
        "`@codex review`",
        "required CI stabilize",
        "final stable current head",
        "unchanged head",
        "actionable fix changes the head",
        "reply with its evidence",
        "resolve only the addressed thread",
        "leave an unverified or disputed thread open and stop",
        "thread-write",
        "metadata-only edits may omit it",
        "the review seats in `routing_table.json` supply the formal reviews",
        "`@codex review` is a retired channel",
        "no actionable findings",
        "no review thread remains unresolved",
        "all required checks and formal reviews pass",
        "No PR is technically merge-eligible while its current head has any "
        "unresolved actionable finding from any review channel",
        "PR-level comments or independent audits",
        "do not create a resolvable thread",
        "Pending, missing, or head-mismatched independent review evidence is "
        "ineligible",
        "Technical eligibility alone never grants merge authority",
        "full-lifecycle",
        "External Authorization Gate",
    ]:
        assert phrase in review_lifecycle

    for required_scope in [
        "research semantics",
        "returns",
        "costs",
        "benchmarks",
        "implementation",
        "CI",
        "security",
        "data handling",
        "execution scope",
    ]:
        assert required_scope in review_lifecycle

    assert review_lifecycle.index("final stable current head") < review_lifecycle.index(
        "technically merge-eligible"
    )
    assert review_lifecycle.index("actionable fix changes the head") < (
        review_lifecycle.index("head-mismatched independent review evidence")
    )
    assert "may enable GitHub auto-merge" not in review_lifecycle
    assert "compatibility note" not in review_lifecycle
    assert "Codex review has completed" not in review_lifecycle

    protected_merge = " ".join(
        _markdown_section(controller, "Protected Merge Eligibility").split()
    )
    assert "full-lifecycle authorization is current" in protected_merge
    assert "perform the normal protected PR merge without another prompt" in (
        protected_merge
    )
    assert "Auto-merge remains a separate action" in protected_merge
    assert "administrative override or protection bypass" in protected_merge


def test_controller_does_not_assign_reviewer_seats() -> None:
    controller = (
        PROJECT_ROOT / "docs/codex_long_running_controller.md"
    ).read_text(encoding="utf-8")
    review_lifecycle = " ".join(
        _markdown_section(controller, "GitHub Review Lifecycle").split()
    )

    for assigned_seat in [
        "fresh Grok latest XHigh",
        "GPT Astra latest High",
        "Grok Extra High",
        "GPT Astra xhigh",
        "no-GPT / lsgz:1",
        "--dangerously-skip-permissions",
    ]:
        assert assigned_seat not in controller

    assert "live Herdr+Pi coordination standard" in review_lifecycle
    assert "routing_table.json" in review_lifecycle
    assert "## Predecessor PR Gate" in controller
    assert "## Protected Merge Eligibility" in controller


def test_agents_ablation_section_runs_after_each_completed_delivery() -> None:
    agents = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    ablation = " ".join(_markdown_section(agents, "Ablation").split())

    assert "After every completed design or implementation" in ablation
    assert "run an ablation experiment" in ablation
    assert "simplest implementation that still meets current requirements" in (
        ablation
    )
    assert "Preserve the baseline" in ablation
    assert "A supported no-change outcome is valid" in ablation


def test_staged_quant_workflow_skill_is_a_thin_router() -> None:
    skill_path = PROJECT_ROOT / ".agents/skills/staged-quant-workflow/SKILL.md"
    workflow_skill = skill_path.read_text(encoding="utf-8")
    normalized_skill = " ".join(workflow_skill.split())

    assert len(workflow_skill.splitlines()) <= 40
    for path in [
        "AGENTS.md",
        "docs/current_handoff.md",
        "docs/codex_long_running_controller.md",
        "docs/current_roadmap.md",
    ]:
        assert f"`{path}`" in normalized_skill

    assert "Continue from the handoff" in normalized_skill
    assert "This Skill routes to the canonical documents above" in normalized_skill
    assert "user's explicit authorization" in normalized_skill
    assert "Keep workflow policy" in normalized_skill
    assert "gh pr " not in normalized_skill
    assert "git " not in normalized_skill
    assert "auto-merge" not in normalized_skill


def test_tracking_error_design_freezes_stage_two_contract() -> None:
    design = (
        PROJECT_ROOT / "docs/risk_evaluation_metrics_design.md"
    ).read_text(encoding="utf-8")
    stage_two = design.split("## Stage 2: Tracking Error", maxsplit=1)[1]
    stage_two = stage_two.split("## Deferred Metrics", maxsplit=1)[0]

    for phrase in [
        "tracking_error = std(measured_active_return, ddof=0) * sqrt(252)",
        "strategy_net_after_applied_costs_vs_cost_free_benchmark",
        "cost-free close-to-close price return",
        "daily_close_to_close",
        "exclude_synthetic_anchor",
        "tracking_error_missing_policy = \"raise\"",
        "tracking error requires at least 2 measured return periods",
        "It is never the difference between strategy and",
        "benchmark annualized returns",
        "refreshes affected reports, JSON experiment logs, and the",
        "experiment registry",
        "Generated evidence",
        "remains explicitly synthetic",
    ]:
        assert phrase in stage_two


def test_placeholder_modules_are_importable() -> None:
    import backtest.metrics
    import backtest.portfolio
    import data.csv_loader
    import features.momentum
    import features.reversal
    import features.volatility
    import reporting.plots
    import risk.constraints

    assert features.momentum.__doc__
    assert features.reversal.__doc__
    assert features.volatility.__doc__
    assert backtest.portfolio.__doc__
    assert backtest.metrics.__doc__
    assert data.csv_loader.__doc__
    assert risk.constraints.__doc__
    assert reporting.plots.__doc__


def test_position_constraint_design_matches_implementation_scope() -> None:
    design = (PROJECT_ROOT / "docs/risk_evaluation_metrics_design.md").read_text(
        encoding="utf-8"
    )
    constraints = (PROJECT_ROOT / "src/risk/constraints.py").read_text(
        encoding="utf-8"
    )

    for phrase in [
        "after signal lag, ranking, eligibility, and equal-weight target",
        "constrained_weight[i, t] = min(target_weight[i, t], max_position_weight)",
        "not redistributed or renormalized",
        "non-interest-bearing cash",
        "clip_and_hold_cash",
        "after_selection_before_trade_calculation",
        "calculated from constrained targets versus drifted pre-trade holdings",
    ]:
        assert phrase in design
    assert "apply_long_only_position_cap" in constraints


def test_holding_episode_design_matches_implementation_contract() -> None:
    design = (PROJECT_ROOT / "docs/risk_evaluation_metrics_design.md").read_text(
        encoding="utf-8"
    )

    for phrase in [
        "continuous_positive_weight_v1",
        "net_contribution_over_cumulative_deployed_weight",
        "pro_rata_absolute_signed_trade_weight",
        "abs(signed_trade_weights) == trade_weights",
        "terminal-open episode",
        "Zero-return episodes are not hits",
        "episode_hit_rate = mean(episode_return > 0)",
        "average_holding_period_return = mean(episode_return)",
    ]:
        assert phrase in design


def test_public_metadata_and_readme_match_implemented_scope() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    configuration = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    metadata = configuration["project"]

    assert "docs/current_roadmap.md" in readme
    assert "docs/research_program_charter.md" in readme
    assert "docs/point_in_time_data_methodology_contract.md" in readme
    assert "local files and committed fixtures" in readme
    assert "Plotting is a placeholder module" in readme
    assert "Stage 3 contract acceptance is" in readme
    specification = (PROJECT_ROOT / "PROJECT_SPEC.md").read_text(encoding="utf-8")
    assert "Stage 3 contract acceptance is methodology-process evidence" in (
        specification
    )
    assert "POINT-IN-TIME FEATURES" not in readme
    assert "private_data" not in readme
    assert metadata["license"] == "Apache-2.0"
    assert metadata["urls"]["Repository"].endswith("equity-factor-research")
    assert metadata["dependencies"] == [
        "numpy>=1.26",
        "pandas>=2.1",
        "scipy>=1.11",
        "pyarrow>=14.0",
        "scikit-learn>=1.4",
    ]
    assert configuration["tool"]["ruff"]["lint"]["select"] == [
        "E4",
        "E7",
        "E9",
        "F",
    ]


def test_generated_repo_map_references_canonical_ci_commands() -> None:
    repo_map = (PROJECT_ROOT / "docs/repo_map.md").read_text(encoding="utf-8")
    assert ".github/workflows/ci.yml" in repo_map
    assert "scripts/repo_map.py" in repo_map
    assert (
        "CI validation commands are defined only in `.github/workflows/ci.yml`"
        in repo_map
    )

    repo_map_module = runpy.run_path(str(PROJECT_ROOT / "scripts/repo_map.py"))
    assert repo_map_module["build_repo_map"]() == repo_map
