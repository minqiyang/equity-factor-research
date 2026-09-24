"""Static design evidence only: no ledger runtime or external catalog execution."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/experiment_trial_ledger_track_b_v7_design.json"
DESIGN = ROOT / "docs/experiment_trial_ledger_track_b_v7_design.md"
ARTIFACTS = ROOT / "docs/experiment_trial_ledger_track_b_v7_design.artifacts.sha256"
MARKER = b"\n## Track B v7 Design Candidate Extension\n"
PLAN_MANIFEST = "4b721dd2f4eb05702a91226697a1684cbbad033476793dec2d4b37b7d778b1b7"
DESIGN_DELIVERABLES = (
    "docs/experiment_trial_ledger_track_b_v7_design.md",
    "tests/fixtures/experiment_trial_ledger_track_b_v7_design.json",
)
DESIGN_ARTIFACTS_MANIFEST_SHA256 = (
    "c5222438065aa73c20629adc053edd40ef60d6ad731daa8296022db1d67f33cd"
)


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        assert key not in result, f"Duplicate fixture property: {key}"
        result[key] = value
    return result


def read_fixture():
    return json.loads(FIXTURE.read_text(), object_pairs_hook=reject_duplicates)


def canonical_digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def test_plan_manifest_and_all_baseline_owner_bytes_remain_pinned():
    fixture = read_fixture()
    assert fixture["accepted_plan_manifest_sha256"] == PLAN_MANIFEST
    manifest = "".join(
        f"{fixture['source_artifact_sha256'][name]}  {name}\n"
        for name in ("track_b_plan_v7.md", "track_b_plan_v7.json")
    )
    assert hashlib.sha256(manifest.encode()).hexdigest() == PLAN_MANIFEST
    assert len(fixture["baseline_inputs"]) == 14
    for pin in fixture["baseline_inputs"]:
        raw = (ROOT / pin["path"]).read_bytes()
        assert hashlib.sha256(raw.split(MARKER)[0]).hexdigest() == pin["sha256"]
    design_manifest = "".join(
        f"{hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}  {name}\n"
        for name in DESIGN_DELIVERABLES
    )
    assert ARTIFACTS.read_text() == design_manifest
    assert hashlib.sha256(ARTIFACTS.read_bytes()).hexdigest() == (
        DESIGN_ARTIFACTS_MANIFEST_SHA256
    )


def test_exact_v7_required_test_content_and_bidirectional_markdown_mirror():
    tests = read_fixture()["append_boundary_checks"]["killing_tests_v7"]
    assert canonical_digest(tests) == (
        "2b9a68ff97ade180d4bee62dda44f7f8d1697e5e10ac4d3a5859f25288b04f53"
    )
    rows = []
    for line in DESIGN.read_text().splitlines():
        if line.startswith("| T-"):
            rows.append([cell.strip() for cell in line.strip("|").split("|")])
    expected = []
    for case in tests:
        fault = case["fault"]
        if "required_independent_variants" in case:
            fault += " Independent variants: " + "; ".join(
                case["required_independent_variants"]
            ) + "."
        expected.append([case["id"], case["boundary"], fault, case["refusal"]])
    assert len(rows) == len(tests) == len({case["id"] for case in tests}) == 73
    assert rows == expected


def test_all_variants_are_separate_scenarios_with_concrete_refusal_codes():
    fixture = read_fixture()
    cases = fixture["append_boundary_checks"]["killing_tests_v7"]
    required = Counter(
        (case["id"], variant)
        for case in cases
        for variant in case.get("required_independent_variants", ["single fault"])
    )
    scenarios = fixture["required_scenarios"]
    actual = Counter((s["test_id"], s["variant"]) for s in scenarios)
    assert actual == required
    assert len(scenarios) == len(required) == 111
    for scenario in scenarios:
        assert re.fullmatch(r"[A-Z][A-Z0-9_]+", scenario["expected_refusal"])
        assert scenario["runtime_status"] == "NOT_EXECUTED"
        assert scenario["expected_committed_changes"] == (
            "winner only" if "CONCURRENT" in scenario["test_id"] else "none"
        )
    coverage = fixture["finding_test_coverage"]
    case_ids = [c["id"] for c in cases]
    assert len(coverage) == 9
    assert all(ids for ids in coverage.values())
    assert all(set(ids) <= set(case_ids) for ids in coverage.values())
    for key in (
        "TB-AUDIT-V6-M4",
        "TB-GROK-V6-M2-SELF-CONTAINED",
        "TB-V6-M1",
    ):
        assert coverage[key] == case_ids
    path_a = fixture["positive_controls"][0]
    assert "ACCESS_STARTED" in path_a
    assert "stop before ACCESS_COMPLETED" in path_a


def test_wire_partition_and_revalidation_boundaries_are_v7_exact():
    fixture = read_fixture()
    families = fixture["families"]
    vocabulary = [wire for family in families for wire in family["wire_types"]]
    selected = fixture["wire_budget"]["selected_14"]
    assert len(families) == 12
    assert len(vocabulary) == len(set(vocabulary)) == 37
    assert len(selected) == len(set(selected)) == 14
    assert set(selected) <= set(vocabulary)
    assert len(set(vocabulary) - set(selected)) == 23
    registry = json.loads((ROOT / "src/ledger/schemas/"
        "experiment_trial_ledger_payload_schema_registry_v9.json").read_text())
    assert set(vocabulary) == set(registry["closed_event_vocabulary"])
    supported = {s["event_type"] for s in registry["event_schemas"]}
    assert len(supported) == 11
    assert set(selected) - supported == {
        "ACCESS_INTENT", "ACCESS_STARTED", "ACCESS_COMPLETED"
    }
    assert "ACCESS_COMPLETED" in selected
    assert "EXPOSURE_DECISION" not in selected
    boundaries = {
        k: v for k, v in fixture["append_boundary_checks"].items()
        if k != "killing_tests_v7"
    }
    assert canonical_digest(boundaries) == (
        "42ac1af7f79db4db464834be4e85e3e85edb0a8a87b69701b0882c4e273cfe58"
    )


def test_native_tuples_cover_every_owner_field_without_aliases():
    fixture = read_fixture()
    registry = json.loads((ROOT / "src/ledger/schemas/"
        "experiment_trial_ledger_payload_schema_registry_v9.json").read_text())
    schemas = {s["event_type"]: s["event_schema"] for s in registry["event_schemas"]}
    groups = fixture["tuple_groups"]
    assert len(groups) == 19
    for name, mapping in groups.items():
        fields = mapping["fields"]
        assert len(fields) == len(set(fields))
        assert len(fields) == (
            8 if name.endswith("catalog_key") else
            3 if name.endswith("projection") else 4
        )
        props = schemas[mapping["source_event"]]["properties"]["payload"]["properties"]
        assert set(fields) <= set(props)
        specimen = fixture["native_tuple_specimens"][name]
        assert set(specimen) == set(fields)
        owner = (ROOT / mapping["owner"]).read_text().split(MARKER.decode())[1]
        for field in fields:
            assert f"{mapping['source_event']}.payload.{field}" in owner
            assert specimen[field] is not None
            if props[field]["kind"] == "literal":
                assert specimen[field] == props[field]["value"]
        # Every owner field in the tuple's semantic namespace must be retained.
        if name.endswith("catalog_key"):
            expected = {f for f in props if f in fields or (
                f.startswith(fields[0].removesuffix("_id"))
            )}
            assert expected == set(fields)
    assert "sealed_trial_inventory_sha256" in groups["inventory_catalog_key"]["fields"]
    assert "inventory_record_sha256" not in groups["inventory_catalog_key"]["fields"]
    assert groups["trial_authority"]["fields"] == groups["plan_authority"]["fields"]
    assert fixture["native_tuple_specimens"]["trial_authority"][
        "allocation_authority_schema_version"
    ] != fixture["native_tuple_specimens"]["plan_authority"][
        "allocation_authority_schema_version"
    ]


def resolve_specimen_path(value, path):
    values = [value]
    for part in path.split("."):
        expanded = part.endswith("[]")
        key = part.removesuffix("[]")
        values = [child for item in values for child in (
            item[key] if expanded else [item[key]]
        )]
    return values


def test_readiness_specimen_has_all_eleven_operands_and_complete_nested_keys():
    fixture = read_fixture()
    specimen = fixture["readiness_operand_specimen"]
    ready = specimen["readiness_operands"]
    assert ready == specimen["same_transaction_expected"]
    operands = fixture["append_boundary_checks"]["readiness_equality_operands"]
    assert set(ready) == {v["operand"] for v in operands}
    assert len(ready) == 11
    assert set(fixture["readiness_paths"]) == set(ready)
    for paths in fixture["readiness_paths"].values():
        for mapping in paths:
            group = mapping["tuple_group"]
            fields = fixture["tuple_groups"][group]["fields"] if group else [
                "event_id", "event_sha256"
            ]
            for nested in resolve_specimen_path(ready, mapping["path"]):
                assert set(nested) == set(fields)
    for family in ready["family_definition_and_acceptance"]:
        assert "trial_family_id" in family
        assert "fam_id" not in family
    for sample in ready["sample_record_acceptance_projection_publication_approval"]:
        assert "sample_id" in sample
        assert "smp_id" not in sample
    trial = ready["trial_definition_acceptance_projection_allocation_authority"]
    assert "trial_id" in trial
    assert "trl_id" not in trial
    for operand in operands:
        text = operand["complete_fields"]
        assert "fam_id" not in text
        assert "smp_id" not in text
        assert "trl_id" not in text
    source_text = next(
        item["complete_fields"] for item in operands
        if item["operand"] == "retained_source_event_id_hash"
    )
    assert "campaign binding" in source_text
    assert "attempt allocation" in source_text
    local_types = {
        row["event_type"]
        for row in ready["retained_source_event_id_hash"]
    }
    assert "ATTEMPT_ALLOCATED" in local_types
    assert "start_authority" not in ready
    assert "NOT_COMPLETE" in specimen["kind"]


def test_seal_role_and_both_origin_specimens_use_the_frozen_paths():
    fixture = read_fixture()
    role = fixture["inventory_role_specimen"]
    principals = {
        "inventory_issuer": role["campaign_inventory_record_v1"]["issuer_actor_id"],
        "inventory_reviewer": role["campaign_inventory_acceptance_v1"]["reviewer_actor_id"],
        "seal_authority_issuer": role["campaign_inventory_seal_authority_v1"]["issuer_actor_id"],
        "seal_actor": role["request"]["actor_id"],
        "authorized_seal_actor": role["campaign_inventory_seal_authority_v1"]["authorized_actor_id"],
        "included_trial_definition_issuer": role["included_trial_definition"]["issuer_actor_id"],
    }
    rules = fixture["inventory_seal_roles"]
    for left, right in rules["required_equalities"]:
        assert principals[left] == principals[right]
    for left, right in rules["prohibited_equalities"]:
        assert principals[left] != principals[right]
    assert principals["inventory_reviewer"] not in role[
        "campaign_inventory_record_v1"
    ]["private_input_producer_actor_ids"]
    local, external = fixture["sample_origin_specimens"]
    assert [local["representation_path"], external["representation_path"]] == [
        "SAMPLE_REGISTERED", "STAGE3_SAMPLE_REFERENCE_BOUND"
    ]
    assert local["sample_id"] != external["sample_id"]
    assert local["ledger_id"] == external["ledger_id"]
    assert local["canonical_sample_lineage_id"] == external["canonical_sample_lineage_id"]
    assert local["native_record_identity"] == external["native_record_identity"]
    assert len(local["native_record_identity"]) == 8


SAFE_PUBLIC_ID = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")


def test_external_reference_readiness_retains_binding_and_attempt_sources():
    fixture = read_fixture()
    rows = fixture["external_reference_readiness_specimen"]["retained_source_event_id_hash"]
    types = [row["event_type"] for row in rows]
    assert "CAMPAIGN_ENTITY_BOUND" in types
    assert "ATTEMPT_ALLOCATED" in types
    assert "STAGE3_SAMPLE_REFERENCE_BOUND" in types
    assert "SAMPLE_REGISTERED" not in types
    for row in rows:
        assert set(row["source"]) == {"event_id", "event_sha256"}
        assert row["source"]["event_id"]
        assert row["source"]["event_sha256"]


def test_access_intent_and_start_bind_resolvable_evidence_refs():
    fixture = read_fixture()
    specimen = fixture["access_evidence_ref_specimen"]
    for event in ("ACCESS_INTENT", "ACCESS_STARTED", "ACCESS_COMPLETED"):
        fields = fixture["access_pack"][event + "_payload_all_and_only"]
        types = fixture["access_field_types"][event]
        assert "evidence_ref_ids" in fields
        assert types["evidence_ref_ids"] == (
            "sorted-unique safe_public_id array; 1..4096"
        )
        assert "unknown_field" not in fields
        refs = specimen[event]["evidence_ref_ids"]
        assert refs
        assert refs == sorted(set(refs))
        for ref in refs:
            assert SAFE_PUBLIC_ID.fullmatch(ref)
    started = specimen["ACCESS_STARTED"]["evidence_ref_ids"]
    intended = specimen["ACCESS_INTENT"]["evidence_ref_ids"]
    completed = specimen["ACCESS_COMPLETED"]["evidence_ref_ids"]
    assert set(intended) <= set(started) <= set(completed)


@pytest.mark.parametrize("event", ["ACCESS_INTENT", "ACCESS_STARTED", "ACCESS_COMPLETED"])
def test_access_pack_exact_fields_and_types_are_frozen_in_existing_owner(event):
    fixture = read_fixture()
    assert canonical_digest(fixture["access_pack"]) == (
        "e7389ccf4008ea02815933d5037848ca6ef8d36e1813d96cb02b03777a66900c"
    )
    fields = fixture["access_pack"][event + "_payload_all_and_only"]
    types = fixture["access_field_types"][event]
    assert set(fields) == set(types)
    owner = (ROOT / "docs/experiment_trial_ledger_schema_registry_contract.md").read_text()
    table = owner.split("#### " + event + "\n")[1].split("#### ")[0]
    rows = [line for line in table.splitlines() if line.startswith("| `")]
    assert rows == [f"| `{field}` | {types[field]} |" for field in fields]


def test_owner_extensions_do_not_embed_literal_hashes():
    fixture = read_fixture()
    hex64 = re.compile(r"[0-9a-f]{64}")
    for pin in fixture["baseline_inputs"]:
        path = ROOT / pin["path"]
        raw = path.read_bytes()
        if MARKER not in raw:
            continue
        extension = raw.split(MARKER, 1)[1].decode()
        match = hex64.search(extension)
        assert match is None, f"{pin['path']} embeds forbidden hash {match.group(0)}"


def test_public_design_has_no_private_locations_or_runtime_delivery_claim():
    fixture = read_fixture()
    assert fixture["status"] == "DESIGN_SPECIFICATION_ONLY_RUNTIME_NOT_EXECUTED"
    for path in [FIXTURE, DESIGN]:
        text = path.read_text()
        assert not re.search(r"/Users/|/home/|private_data/|program_control_v1/|https?://", text)
        assert not any(ord(char) < 32 and char not in "\n\r\t" for char in text)
    assert "DESIGN_CANDIDATE_RUNTIME_NOT_IMPLEMENTED" in DESIGN.read_text()
