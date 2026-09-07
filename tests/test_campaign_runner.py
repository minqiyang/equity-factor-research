"""Authorized runner orchestration and byte-identical repeat runs."""

from __future__ import annotations

import dataclasses
from datetime import date, timedelta
from functools import partial
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from collections.abc import Mapping
from types import MappingProxyType

from campaign.bundle import invalid_and_missing_bytes, required_bundle_children
from campaign.classifier import classify_diagnostic
from campaign.diagnostics import descriptive_rank_ic
from campaign.inference import (
    FACTOR_ORDER,
    FactorVector,
    bootstrap_mean_rank_ic,
    holm_adjust,
)
from campaign.precondition import authorize, result_bearing_refusal_reason
from campaign.reconciliation import assemble_diagnostic_inputs
from campaign import runner as runner_module
from campaign.runner import (
    CampaignRun,
    RunConfig,
    attempt_ledger_path,
    campaign_identity,
    configuration_projection,
    run_campaign,
)
from campaign.schedule import CampaignSchedule, EvaluationFold, SignalRow
from pit_manifest_validator_v1.canonical import sha256_hex
from campaign_runner_v1_support import (
    encode_runner_listing_key,
    fixture_file,
    fixture_ticker,
    load_runner_fixture,
    make_run_config,
)


def _authorized_config(**overrides: object) -> RunConfig:
    golden = load_runner_fixture("acceptance_record_identity_golden.json")
    protocol = load_runner_fixture("run_config_protocol.json")["inputs"]
    expected = golden["expected"]
    inputs = golden["inputs"]
    locators = {
        "acceptance_record_file": str(fixture_file(inputs["record_file"])),
        "stage2_grant_file": str(fixture_file(inputs["grant_file"])),
        "protocol_file": str(fixture_file(inputs["protocol_file"])),
        "trial_inventory_file": str(fixture_file(inputs["inventory_file"])),
        "detached_binding_file": str(fixture_file(inputs["binding_file"])),
        "prepared_campaign_file": str(fixture_file(inputs["prepared_file"])),
        "attempt_state_file": str(fixture_file(inputs["attempt_state_file"])),
    }
    digests = {
        "acceptance_record_file_sha256": expected["file_bytes"],
        "acceptance_identity_sha256": expected["canonical_identity"],
        "decision_file_sha256": expected["decision_file_sha256"],
        "decision_identity_sha256": expected["decision_identity_sha256"],
        "stage2_grant_file_sha256": expected["grant_file_bytes"],
        "protocol_file_sha256": expected["protocol_file_bytes"],
        "trial_inventory_file_sha256": expected["inventory_file_bytes"],
        "prepared_campaign_file_sha256": expected["prepared_file_bytes"],
        "owner_authorization_file_sha256": expected[
            "owner_authorization_file_sha256"
        ],
    }
    return make_run_config(locators, digests, protocol, **overrides)


def test_run_campaign_refuses_without_bundle_when_unauthorized() -> None:
    fixture = load_runner_fixture("acceptance_record_role_swap.json")
    result = run_campaign(
        _authorized_config(
            acceptance_identity_sha256=fixture["expected"]["file_bytes"]
        )
    )
    assert isinstance(result, CampaignRun)
    assert result.status == "REFUSED"
    assert result.reason == fixture["expected"]["reason"]
    assert result.bundle is None
    assert result.reconciliation is None
    assert result.run_record is None


def test_run_campaign_planning_grant_refuses_result_bearing() -> None:
    fixture = load_runner_fixture("grant_result_bearing_refusal.json")
    expected = fixture["expected"]
    result = run_campaign(_authorized_config())
    assert isinstance(result, CampaignRun)
    assert result.status == expected["status"]
    assert result.reason == expected["reason"]
    assert result.authorization.status == expected["authorization_status"]
    assert result.bundle is None
    assert result.reconciliation is None
    assert result.run_record is None
    assert fixture["forbidden"]["emit_result_bearing_bundle"]


def test_two_runs_over_same_inputs_are_identical() -> None:
    fixture = load_runner_fixture("grant_result_bearing_refusal.json")
    first = run_campaign(_authorized_config())
    second = run_campaign(_authorized_config())
    assert first.status == fixture["expected"]["status"]
    assert second.status == fixture["expected"]["status"]
    assert first.reason == second.reason
    assert first.bundle is None
    assert second.bundle is None
    assert first.authorization.status == second.authorization.status
    assert first.run_record == second.run_record


def test_run_campaign_ignores_unbound_prepared_file(tmp_path: Path) -> None:
    fixture = load_runner_fixture("prepared_file_unbound_mutation.json")
    prepared = json.loads(
        fixture_file(fixture["inputs"]["prepared_file"]).read_text(encoding="utf-8")
    )
    cursor = prepared
    path = fixture["inputs"]["mutation"]["path"]
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = fixture["inputs"]["mutation"]["value"]
    target = tmp_path / "mutated_prepared.json"
    target.write_text(json.dumps(prepared), encoding="utf-8")
    original = run_campaign(_authorized_config())
    mutated = run_campaign(_authorized_config(prepared_campaign_file=str(target)))
    expected = fixture["expected"]
    assert original.status == expected["status"]
    assert mutated.status == expected["status"]
    assert original.reason == expected["reason"]
    assert mutated.reason == expected["reason"]
    assert original.bundle is None
    assert mutated.bundle is None
    assert fixture["forbidden"]["trust_unbound_prepared_file"]


def test_run_campaign_missing_output_does_not_emit_valid_null_bundle(
    tmp_path: Path,
) -> None:
    fixture = load_runner_fixture("reconciliation_missing_output.json")
    prepared = json.loads(
        fixture_file("precondition/prepared_campaign.json").read_text(encoding="utf-8")
    )
    prepared["prices"] = {}
    target = tmp_path / "missing_output.json"
    target.write_text(json.dumps(prepared), encoding="utf-8")
    result = run_campaign(_authorized_config(prepared_campaign_file=str(target)))
    expected = fixture["expected"]
    assert result.status == expected["run_campaign_status"]
    assert result.reason == expected["run_campaign_reason"]
    assert result.bundle is None
    assert result.run_record is None
    assert result.reconciliation is None


def test_configuration_projection_labels_digest_roles() -> None:
    config = _authorized_config()
    projection = configuration_projection(config)
    roles = projection["roles"]
    assert roles["acceptance_record_file_sha256"] == "FILE_BYTES"
    assert roles["acceptance_identity_sha256"] == "CANONICAL_IDENTITY"
    assert roles["prepared_campaign_file_sha256"] == "FILE_BYTES"
    assert roles["owner_authorization_file_sha256"] == "FILE_BYTES"
    assert (
        projection["acceptance_record_file_sha256"]
        == config.acceptance_record_file_sha256
    )
    assert projection["acceptance_identity_sha256"] == config.acceptance_identity_sha256
    assert (
        projection["prepared_campaign_file_sha256"]
        == config.prepared_campaign_file_sha256
    )
    assert (
        projection["owner_authorization_file_sha256"]
        == config.owner_authorization_file_sha256
    )


def test_run_config_fields_have_no_defaults() -> None:
    for field in dataclasses.fields(RunConfig):
        assert field.default is dataclasses.MISSING
        assert field.default_factory is dataclasses.MISSING


def test_runner_functions_have_no_defaults() -> None:
    for function in (configuration_projection, run_campaign):
        for parameter in inspect.signature(function).parameters.values():
            assert parameter.default is inspect.Parameter.empty


def _write_binding(
    tmp_path: Path,
    name: str,
    prepared_digest: str | None = None,
) -> str:
    binding = json.loads(
        fixture_file("precondition/binding_valid.json").read_text(encoding="utf-8")
    )
    if prepared_digest is not None:
        binding["prepared_campaign_file_sha256"] = prepared_digest
    path = tmp_path / name
    path.write_text(json.dumps(binding), encoding="utf-8")
    return str(path)


def _config_with_grant(
    grant_file: str,
    tmp_path: Path,
    **overrides: object,
) -> RunConfig:
    del tmp_path
    grant_path = fixture_file(grant_file)
    payload = {
        "stage2_grant_file": str(grant_path),
        "stage2_grant_file_sha256": sha256_hex(grant_path.read_bytes()),
    }
    payload.update(overrides)
    return _authorized_config(**payload)


def _copy_attempt_state(
    tmp_path: Path,
    identity: str,
    name: str,
) -> str:
    payload = json.loads(
        fixture_file("precondition/attempt_state.json").read_text(encoding="utf-8")
    )
    payload["campaign_identity_sha256"] = identity
    target = tmp_path / name
    target.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return str(target)


_ISOLATED_LEDGER_HOME = "isolated_home"


def _isolated_ledger_home(tmp_path: Path) -> Path:
    home = tmp_path / _ISOLATED_LEDGER_HOME
    home.mkdir(parents=True, exist_ok=True)
    return home


def _redirect_attempt_ledger_path(identity: str, isolated_home: Path) -> Path:
    produced = attempt_ledger_path(identity)
    return isolated_home.joinpath(*produced.relative_to(Path.home()).parts)


@pytest.fixture(autouse=True)
def isolate_campaign_attempt_ledger(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    isolated_home = _isolated_ledger_home(tmp_path)
    monkeypatch.setattr(
        runner_module,
        "attempt_ledger_path",
        partial(_redirect_attempt_ledger_path, isolated_home=isolated_home),
    )
    return isolated_home


def _seed_identity_ledger(identity: str, tmp_path: Path) -> str:
    payload = json.loads(
        fixture_file("precondition/attempt_state.json").read_text(encoding="utf-8")
    )
    payload["campaign_identity_sha256"] = identity
    target = runner_module.attempt_ledger_path(identity)
    assert target.resolve().is_relative_to(tmp_path.resolve())
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return str(target)


def test_seed_identity_ledger_targets_isolated_tmp_via_real_helper(
    tmp_path: Path,
) -> None:
    identity = str(
        load_runner_fixture("common_sample_primary_ic.json")["inputs"][
            "synthetic_identity"
        ]
    )
    seeded = Path(_seed_identity_ledger(identity, tmp_path))
    isolated_home = _isolated_ledger_home(tmp_path)
    production_default = attempt_ledger_path(identity)
    assert seeded == runner_module.attempt_ledger_path(identity)
    assert seeded.is_file()
    assert seeded.resolve().is_relative_to(isolated_home.resolve())
    assert production_default == Path.home().joinpath(
        *seeded.relative_to(isolated_home).parts
    )
    assert seeded.resolve() != production_default.resolve()
    redirected = runner_module.attempt_ledger_path(identity)
    assert redirected.resolve().is_relative_to(isolated_home.resolve())
    worker_home = _isolated_ledger_home(tmp_path)
    repo = Path(__file__).resolve().parents[1]
    worker_env = os.environ.copy()
    worker_env["HOME"] = str(worker_home)
    existing = worker_env.get("PYTHONPATH", "")
    worker_env["PYTHONPATH"] = (
        str(repo / "src") if not existing else str(repo / "src") + os.pathsep + existing
    )
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                "from campaign.runner import attempt_ledger_path; "
                f"p = attempt_ledger_path({identity!r}); "
                "print(p)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=worker_env,
        cwd=repo,
    )
    subprocess_path = Path(probe.stdout.strip())
    assert subprocess_path.resolve().is_relative_to(worker_home.resolve())


def _run_config_payload(config: RunConfig) -> dict[str, object]:
    payload = dataclasses.asdict(config)
    payload["cost_bps"] = list(config.cost_bps)
    return payload


def _binding_identity(path: str) -> str:
    return campaign_identity(
        json.loads(Path(path).read_text(encoding="utf-8"))
    )


def test_exact_grant_v2_lists_reach_diagnostic_execution(
    tmp_path: Path,
) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    locators = (
        fixture_file(inputs["grant_file"]),
        fixture_file(inputs["prepared_file"]),
        fixture_file("precondition/acceptance_valid.json"),
        fixture_file("precondition/binding_valid.json"),
        fixture_file("precondition/protocol.yaml"),
        fixture_file("precondition/trial_inventory.json"),
    )
    before = {path: sha256_hex(path.read_bytes()) for path in locators}
    prepared = json.loads(
        fixture_file(inputs["prepared_file"]).read_text(encoding="utf-8")
    )
    prepared_path = tmp_path / "conflicting_prepared.json"
    prepared_path.write_text(json.dumps(prepared), encoding="utf-8")
    prepared_digest = sha256_hex(prepared_path.read_bytes())
    binding_path = _write_binding(
        tmp_path, "authorized_binding.json", prepared_digest
    )
    identity = _binding_identity(binding_path)
    _seed_identity_ledger(identity, tmp_path)
    config = _config_with_grant(
        inputs["grant_file"],
        tmp_path,
        prepared_campaign_file=str(prepared_path),
        prepared_campaign_file_sha256=prepared_digest,
        detached_binding_file=binding_path,
        attempt_state_file=_copy_attempt_state(
            tmp_path, identity, "attempt_state.json"
        ),
    )
    grant = json.loads(fixture_file(inputs["grant_file"]).read_text(encoding="utf-8"))
    assert grant["now_eligible"] == expected["now_eligible"]
    assert grant["does_not_authorize"] == expected["does_not_authorize"]
    assert result_bearing_refusal_reason(grant) == expected["refusal_reason"]
    authorization = authorize(config)
    assert authorization.status == expected["authorization_status"]
    assert authorization.reason == expected["authorization_reason"]
    result = run_campaign(config)
    assert isinstance(result, CampaignRun)
    assert result.status == expected["status"]
    assert result.reason is None
    assert result.reconciliation is not None
    assert result.bundle is not None
    assert result.run_record is not None
    assert list(result.run_record) == expected["run_record_keys"]
    assert expected["reconciled_claim_key"] not in result.run_record
    assert result.run_record["evidence_ceiling"] == expected["evidence_ceiling"]
    assert result.run_record["trials_executed"] == expected["trials_executed"]
    assert result.run_record["trial_ids"] == expected["trial_ids"]
    assert result.reconciliation.trial_count == expected["trials_executed"]
    assert result.bundle.detached_root is not None
    assert (
        result.bundle.detached_root["attempt_count"]
        == expected["ledger_attempt_count"]
    )
    for name in expected["runner_owned_children"]:
        assert name in result.bundle.child_digests
    invalid_name = expected["invalid_child"]
    assert result.bundle.child_digests[invalid_name] == sha256_hex(
        invalid_and_missing_bytes(result.reconciliation)
    )
    replay = run_campaign(config)
    assert replay.status == "REFUSED"
    assert replay.reason == expected["attempt_consumed_reason"]
    alternate = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(prepared_path),
            prepared_campaign_file_sha256=prepared_digest,
            detached_binding_file=binding_path,
            attempt_state_file=_copy_attempt_state(
                tmp_path, identity, "attempt_alt.json"
            ),
        )
    )
    assert alternate.status == "REFUSED"
    assert alternate.reason == expected["alternate_locator_reason"]
    mutated_grant = json.loads(
        fixture_file(inputs["grant_file"]).read_text(encoding="utf-8")
    )
    mutated_grant["artifact_id"] = inputs["mutated_artifact_id"]
    mutated_path = tmp_path / "mutated_grant.json"
    mutated_path.write_text(json.dumps(mutated_grant), encoding="utf-8")
    mutated_run = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            stage2_grant_file=str(mutated_path),
            stage2_grant_file_sha256=sha256_hex(mutated_path.read_bytes()),
            prepared_campaign_file=str(prepared_path),
            prepared_campaign_file_sha256=prepared_digest,
            detached_binding_file=binding_path,
            attempt_state_file=_copy_attempt_state(
                tmp_path, identity, "attempt_mutated.json"
            ),
        )
    )
    assert mutated_run.status == "REFUSED"
    assert mutated_run.reason == expected["mutated_grant_reason"]
    after = {path: sha256_hex(path.read_bytes()) for path in locators}
    assert before == after
    assert fixture["forbidden"]["campaign_artifact_write"]
    assert fixture["forbidden"]["result_access_executable"]
    assert fixture["forbidden"]["performance_access_executable"]
    assert fixture["forbidden"]["reconcile_precomputed_payload"]


def test_run_campaign_refuses_sentinel_and_prepared_byte_mismatch(
    tmp_path: Path,
) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    sentinel = fixture_file(inputs["sentinel_file"])
    sentinel_digest = sha256_hex(sentinel.read_bytes())
    sentinel_run = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(sentinel),
            prepared_campaign_file_sha256=sentinel_digest,
            detached_binding_file=_write_binding(
                tmp_path,
                "sentinel_binding.json",
                sentinel_digest,
            ),
        )
    )
    assert sentinel_run.status == "REFUSED"
    assert sentinel_run.reason == expected["sentinel_reason"]
    mutated = json.loads(
        fixture_file(inputs["prepared_file"]).read_text(encoding="utf-8")
    )
    mutated["prices"] = {}
    mutated_path = tmp_path / "mutated_prepared.json"
    mutated_path.write_text(json.dumps(mutated), encoding="utf-8")
    mismatched = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(mutated_path),
        )
    )
    assert mismatched.status == "REFUSED"
    assert mismatched.reason == expected["prepared_bytes_reason"]


def test_forged_owner_authorization_digest_is_refused(tmp_path: Path) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    grant = json.loads(
        fixture_file(fixture["inputs"]["grant_file"]).read_text(encoding="utf-8")
    )
    grant["fourteen_trial_run_authorization"]["owner_authorization_file_sha256"] = (
        expected["wrong_owner_digest"]
    )
    grant_path = tmp_path / "forged_grant.json"
    grant_path.write_text(json.dumps(grant), encoding="utf-8")
    result = authorize(
        _authorized_config(
            stage2_grant_file=str(grant_path),
            stage2_grant_file_sha256=sha256_hex(grant_path.read_bytes()),
        )
    )
    assert result.status == "REFUSED"
    assert result.reason == expected["owner_mismatch_reason"]


def test_malformed_prepared_campaign_is_named_refusal(tmp_path: Path) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    malformed_path = tmp_path / "malformed.json"
    malformed_path.write_bytes(inputs["malformed_prepared"].encode("utf-8"))
    malformed_digest = sha256_hex(malformed_path.read_bytes())
    malformed_binding = _write_binding(
        tmp_path, "binding_malformed.json", malformed_digest
    )
    malformed = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(malformed_path),
            prepared_campaign_file_sha256=malformed_digest,
            detached_binding_file=malformed_binding,
            attempt_state_file=_copy_attempt_state(
                tmp_path,
                _binding_identity(malformed_binding),
                "attempt_malformed.json",
            ),
        )
    )
    assert malformed.status == "REFUSED"
    assert malformed.reason == expected["malformed_reason"]
    missing_path = tmp_path / "missing.json"
    missing_path.write_text(json.dumps(inputs["missing_key_prepared"]), encoding="utf-8")
    missing_digest = sha256_hex(missing_path.read_bytes())
    missing_binding = _write_binding(
        tmp_path, "binding_missing.json", missing_digest
    )
    missing = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(missing_path),
            prepared_campaign_file_sha256=missing_digest,
            detached_binding_file=missing_binding,
            attempt_state_file=_copy_attempt_state(
                tmp_path,
                _binding_identity(missing_binding),
                "attempt_missing.json",
            ),
        )
    )
    assert missing.status == "REFUSED"
    assert missing.reason == expected["schema_reason"]
    wrong_path = tmp_path / "wrong_type.json"
    wrong_path.write_text(json.dumps(inputs["wrong_type_prepared"]), encoding="utf-8")
    wrong_digest = sha256_hex(wrong_path.read_bytes())
    wrong_binding = _write_binding(tmp_path, "binding_wrong.json", wrong_digest)
    wrong = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(wrong_path),
            prepared_campaign_file_sha256=wrong_digest,
            detached_binding_file=wrong_binding,
            attempt_state_file=_copy_attempt_state(
                tmp_path,
                _binding_identity(wrong_binding),
                "attempt_wrong.json",
            ),
        )
    )
    assert wrong.status == "REFUSED"
    assert wrong.reason == expected["schema_reason"]
    nested = json.loads(
        fixture_file(inputs["prepared_file"]).read_text(encoding="utf-8")
    )
    nested["listings"][inputs["nested_wrong_signal_date"]] = ["not-a-listing"]
    nested_path = tmp_path / "nested.json"
    nested_path.write_text(json.dumps(nested), encoding="utf-8")
    nested_digest = sha256_hex(nested_path.read_bytes())
    nested_binding = _write_binding(tmp_path, "binding_nested.json", nested_digest)
    nested_identity = _binding_identity(nested_binding)
    nested_state = _copy_attempt_state(
        tmp_path, nested_identity, "attempt_nested.json"
    )
    nested_ledger = _seed_identity_ledger(nested_identity, tmp_path)
    nested_run = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(nested_path),
            prepared_campaign_file_sha256=nested_digest,
            detached_binding_file=nested_binding,
            attempt_state_file=nested_state,
        )
    )
    assert nested_run.status == "REFUSED"
    assert nested_run.reason == expected["schema_reason"]
    leftover = json.loads(Path(nested_ledger).read_text(encoding="utf-8"))
    assert leftover["consumed"] is False


def test_negative_ledger_execution_count_is_refused(tmp_path: Path) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    binding_path = str(fixture_file("precondition/binding_valid.json"))
    identity = _binding_identity(binding_path)
    state = _copy_attempt_state(tmp_path, identity, "attempt_negative.json")
    ledger = _seed_identity_ledger(identity, tmp_path)
    payload = json.loads(Path(ledger).read_text(encoding="utf-8"))
    payload["execution_count"] = inputs["negative_execution_count"]
    Path(ledger).write_text(json.dumps(payload), encoding="utf-8")
    result = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            attempt_state_file=state,
        )
    )
    assert result.status == "REFUSED"
    assert result.reason == expected["negative_count_reason"]
    leftover = json.loads(Path(ledger).read_text(encoding="utf-8"))
    assert leftover["consumed"] is False
    assert leftover["execution_count"] == inputs["negative_execution_count"]


def test_two_process_replay_consumes_the_identity_ledger(
    tmp_path: Path,
) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    prepared = json.loads(
        fixture_file(inputs["prepared_file"]).read_text(encoding="utf-8")
    )
    prepared_path = tmp_path / "two_process_prepared.json"
    prepared_path.write_text(json.dumps(prepared), encoding="utf-8")
    prepared_digest = sha256_hex(prepared_path.read_bytes())
    binding_path = _write_binding(
        tmp_path, "two_process_binding.json", prepared_digest
    )
    identity = _binding_identity(binding_path)
    _seed_identity_ledger(identity, tmp_path)
    first_config = _config_with_grant(
        inputs["grant_file"],
        tmp_path,
        prepared_campaign_file=str(prepared_path),
        prepared_campaign_file_sha256=prepared_digest,
        detached_binding_file=binding_path,
        attempt_state_file=_copy_attempt_state(
            tmp_path, identity, "attempt_process_one.json"
        ),
    )
    first_payload = tmp_path / "first_config.json"
    first_payload.write_text(
        json.dumps(_run_config_payload(first_config)), encoding="utf-8"
    )
    worker = Path(__file__).resolve().parent / expected["two_process_worker"]
    worker_env = os.environ.copy()
    worker_env["HOME"] = str(_isolated_ledger_home(tmp_path))
    first = subprocess.run(
        [sys.executable, str(worker), str(first_payload)],
        check=True,
        capture_output=True,
        text=True,
        env=worker_env,
    )
    first_result = json.loads(first.stdout)
    assert first_result["status"] == expected["status"]
    assert first_result["reason"] is None
    second_config = _config_with_grant(
        inputs["grant_file"],
        tmp_path,
        prepared_campaign_file=str(prepared_path),
        prepared_campaign_file_sha256=prepared_digest,
        detached_binding_file=binding_path,
        attempt_state_file=_copy_attempt_state(
            tmp_path, identity, "attempt_process_two.json"
        ),
    )
    second_payload = tmp_path / "second_config.json"
    second_payload.write_text(
        json.dumps(_run_config_payload(second_config)), encoding="utf-8"
    )
    second = subprocess.run(
        [sys.executable, str(worker), str(second_payload)],
        check=True,
        capture_output=True,
        text=True,
        env=worker_env,
    )
    second_result = json.loads(second.stdout)
    assert second_result["status"] == "REFUSED"
    assert second_result["reason"] == expected["attempt_consumed_reason"]


def test_result_bearing_prepared_campaign_is_refused(
    tmp_path: Path,
) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    prepared_path = tmp_path / "result_bearing.json"
    prepared_path.write_text(
        json.dumps(inputs["result_bearing_prepared"]), encoding="utf-8"
    )
    prepared_digest = sha256_hex(prepared_path.read_bytes())
    binding_path = _write_binding(
        tmp_path, "result_bearing_binding.json", prepared_digest
    )
    identity = _binding_identity(binding_path)
    ledger = _seed_identity_ledger(identity, tmp_path)
    result = run_campaign(
        _config_with_grant(
            inputs["grant_file"],
            tmp_path,
            prepared_campaign_file=str(prepared_path),
            prepared_campaign_file_sha256=prepared_digest,
            detached_binding_file=binding_path,
            attempt_state_file=_copy_attempt_state(
                tmp_path, identity, "attempt_result_bearing.json"
            ),
        )
    )
    assert result.status == "REFUSED"
    assert result.reason == expected["result_bearing_reason"]
    leftover = json.loads(Path(ledger).read_text(encoding="utf-8"))
    assert leftover["consumed"] is False


def _reconcile_ready_config(
    tmp_path: Path,
    prepared: dict[str, object],
    name: str,
) -> tuple[RunConfig, str]:
    fixture = load_runner_fixture("grant_run_execution.json")
    inputs = fixture["inputs"]
    prepared_path = tmp_path / f"{name}_prepared.json"
    prepared_path.write_text(json.dumps(prepared), encoding="utf-8")
    prepared_digest = sha256_hex(prepared_path.read_bytes())
    binding_path = _write_binding(
        tmp_path, f"{name}_binding.json", prepared_digest
    )
    identity = _binding_identity(binding_path)
    ledger = _seed_identity_ledger(identity, tmp_path)
    config = _config_with_grant(
        inputs["grant_file"],
        tmp_path,
        prepared_campaign_file=str(prepared_path),
        prepared_campaign_file_sha256=prepared_digest,
        detached_binding_file=binding_path,
        attempt_state_file=_copy_attempt_state(
            tmp_path, identity, f"{name}_attempt.json"
        ),
    )
    return config, ledger


def test_tmp_environment_wipe_cannot_replay(tmp_path: Path) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    prepared = json.loads(
        fixture_file(inputs["prepared_file"]).read_text(encoding="utf-8")
    )
    config, ledger = _reconcile_ready_config(tmp_path, prepared, "tmp_wipe")
    first = run_campaign(config)
    assert first.status == expected["status"]
    identity = json.loads(Path(ledger).read_text(encoding="utf-8"))[
        "campaign_identity_sha256"
    ]
    durable = Path(ledger)
    assert durable.resolve().is_relative_to(tmp_path.resolve())
    ephemeral = tmp_path / expected["tmp_ledger_dirname"]
    ephemeral.mkdir(parents=True)
    fake = json.loads(
        fixture_file("precondition/attempt_state.json").read_text(encoding="utf-8")
    )
    fake["campaign_identity_sha256"] = identity
    fake_ledger = ephemeral / f"{identity}.json"
    fake_ledger.write_text(
        json.dumps(fake, sort_keys=True), encoding="utf-8"
    )
    assert fake_ledger.resolve().is_relative_to(tmp_path.resolve())
    second = run_campaign(config)
    assert second.status == "REFUSED"
    assert second.reason == expected["attempt_consumed_reason"]
    leftover = json.loads(durable.read_text(encoding="utf-8"))
    assert leftover["consumed"] is True


def test_executed_bundle_contains_required_children(tmp_path: Path) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    prepared = json.loads(
        fixture_file(fixture["inputs"]["prepared_file"]).read_text(encoding="utf-8")
    )
    config, ledger = _reconcile_ready_config(tmp_path, prepared, "required_children")
    result = run_campaign(config)
    assert result.status == expected["status"]
    assert result.bundle is not None
    for name in expected["runner_owned_children"]:
        assert name in result.bundle.child_digests
    leftover = json.loads(Path(ledger).read_text(encoding="utf-8"))
    assert leftover["consumed"] is True


def test_protocol_and_inventory_file_swap_is_refused(tmp_path: Path) -> None:
    fixture = load_runner_fixture("grant_run_execution.json")
    expected = fixture["expected"]
    inputs = fixture["inputs"]
    prepared = json.loads(
        fixture_file(inputs["prepared_file"]).read_text(encoding="utf-8")
    )
    for case in expected["file_swap_cases"]:
        config, ledger = _reconcile_ready_config(
            tmp_path, prepared, str(case["config_field"])
        )
        source = fixture_file(case["source"])
        swapped = tmp_path / source.name
        swapped.write_bytes(source.read_bytes() + b"\n")
        result = run_campaign(
            _config_with_grant(
                inputs["grant_file"],
                tmp_path,
                prepared_campaign_file=config.prepared_campaign_file,
                prepared_campaign_file_sha256=config.prepared_campaign_file_sha256,
                detached_binding_file=config.detached_binding_file,
                attempt_state_file=config.attempt_state_file,
                **{case["config_field"]: str(swapped)},
            )
        )
        assert result.status == "REFUSED", case
        assert result.reason == case["reason"], case
        leftover = json.loads(Path(ledger).read_text(encoding="utf-8"))
        assert leftover["consumed"] is False, case


def _p1_cases() -> dict[str, object]:
    return load_runner_fixture("execution_p1_cases.json")


def _session_range(start: date, count: int) -> tuple[str, ...]:
    return tuple((start + timedelta(days=index)).isoformat() for index in range(count))


def _listing_index(spec: dict[str, object]) -> int:
    identity = spec["identity"]
    assert isinstance(identity, dict)
    return int(str(identity["resolved_listing_id"]).split("-")[-1])


def _synthetic_listing(index: int, cases: dict[str, object]) -> dict[str, object]:
    inputs = cases["inputs"]
    ticker = fixture_ticker(
        str(inputs["ticker_prefix"]),
        int(inputs["ticker_width"]),
        index,
    )
    listing_key = encode_runner_listing_key(
        str(inputs["exchange"]),
        ticker,
        str(inputs["alias_effective_from"]),
        None,
    )
    identity = {
        "resolved_listing_episode_id": f"EP-{index}",
        "resolved_listing_id": f"LST-{index}",
        "resolved_permanent_security_id": f"SEC-{index}",
    }
    alias = {
        **identity,
        "alias_effective_from": inputs["alias_effective_from"],
        "alias_effective_to": None,
        "lineage_resolution_evidence_id": f"EV-{index}",
        "source_exchange": inputs["exchange"],
        "source_ticker": ticker,
        "transition_to_next": "TARGET_ALIAS",
    }
    return {
        "alias": alias,
        "hex_key": listing_key.hex(),
        "identity": identity,
        "listing_key": listing_key,
    }


def _price_for_case(
    case_name: str,
    cases: dict[str, object],
    spec: dict[str, object],
    session: str,
    sessions: tuple[str, ...],
) -> float:
    inputs = cases["inputs"]
    if case_name == "execution_anchor":
        cfg = inputs["execution_anchor"]
        if session == sessions[0]:
            return float(cfg["start_price"])
        if session == sessions[-1]:
            return float(cfg["end_price"])
        return float(cfg["execution_price"])
    index = _listing_index(spec)
    day = sessions.index(session)
    if case_name == "monthly_ic":
        cfg = inputs["monthly_ic"]
        one = int(inputs["one"])
        price = float(cfg["start_price"]) + index + float(cfg["slope"]) * (index + one) * day
        if session >= str(cfg["first_signal"]) and session < str(cfg["second_signal"]):
            if index >= int(cfg["split_index"]):
                return price * float(cfg["early_high_mult"])
            return price * float(cfg["early_low_mult"])
        if session >= str(cfg["second_signal"]):
            if index >= int(cfg["split_index"]):
                return price * float(cfg["late_high_mult"])
            return price * float(cfg["late_low_mult"])
        return price
    if case_name == "rebalance":
        cfg = inputs["rebalance"]
        return float(cfg["start_price"]) + index + day * float(cfg["day_weight"])
    cfg = inputs["derived_large"]
    remainder = index % int(cfg["parity_mod"])
    parity = float(cfg["parity_boost"]) if remainder else float(cfg["zero"])
    return float(cfg["start_price"]) + index + float(cfg["day_weight"]) * day + parity


def _synthetic_panel(
    sessions: tuple[str, ...],
    listing_count: int,
    signal_flags: dict[str, bool],
    case_name: str,
    cases: dict[str, object],
) -> dict[str, object]:
    listings_out: dict[str, list[dict[str, object]]] = {}
    prices: dict[str, dict[str, float]] = {}
    anchors: dict[str, list[dict[str, object]]] = {}
    specs = [_synthetic_listing(index, cases) for index in range(listing_count)]
    for spec in specs:
        hex_key = str(spec["hex_key"])
        alias = spec["alias"]
        assert isinstance(alias, dict)
        prices[hex_key] = {
            session: _price_for_case(case_name, cases, spec, session, sessions)
            for session in sessions
        }
        anchors[hex_key] = [
            {
                **alias,
                "adjusted_close": prices[hex_key][session],
                "session_date": session,
            }
            for session in sessions
        ]
    for signal_date, in_universe in signal_flags.items():
        rows = []
        for spec in specs:
            rows.append(
                {
                    "alias_chain": [spec["alias"]],
                    "in_universe_at_t": in_universe,
                    "listing_key": spec["hex_key"],
                    "lookback_addressable_at_t": True,
                    "target_identity": spec["identity"],
                    "terminal_blocked_at_t": False,
                }
            )
        listings_out[signal_date] = rows
    return {"anchors": anchors, "listings": listings_out, "prices": prices}


def _run_prepared(tmp_path: Path, prepared: dict[str, object], name: str):
    config, _ledger = _reconcile_ready_config(tmp_path, prepared, name)
    return run_campaign(config)


def _independent_common_means(
    monthly_rank_ics: object,
) -> FactorVector[float] | tuple[()]:
    assert isinstance(monthly_rank_ics, list)
    valid_by_factor: dict[str, dict[str, float]] = {
        factor_id: {} for factor_id in FACTOR_ORDER
    }
    for row in monthly_rank_ics:
        assert isinstance(row, dict)
        if row.get("valid") is not True or row.get("value") is None:
            continue
        factor_id = row["factor_id"]
        signal_date = row["signal_date"]
        if not isinstance(factor_id, str) or not isinstance(signal_date, str):
            continue
        if factor_id in valid_by_factor:
            valid_by_factor[factor_id][signal_date] = float(row["value"])
    common = [
        signal_date
        for signal_date in valid_by_factor[FACTOR_ORDER[0]]
        if all(
            signal_date in valid_by_factor[factor_id] for factor_id in FACTOR_ORDER
        )
    ]
    if not common:
        return ()
    return FactorVector(
        *(
            sum(valid_by_factor[factor_id][signal_date] for signal_date in common)
            / len(common)
            for factor_id in FACTOR_ORDER
        )
    )


def _all_valid_descriptive_means(
    monthly_rank_ics: object,
    sample_std_ddof: int,
    empty_mean: float,
) -> FactorVector[float]:
    assert isinstance(monthly_rank_ics, list)
    values_by_factor: dict[str, list[float]] = {
        factor_id: [] for factor_id in FACTOR_ORDER
    }
    for row in monthly_rank_ics:
        assert isinstance(row, dict)
        if row.get("valid") is not True or row.get("value") is None:
            continue
        factor_id = row["factor_id"]
        if factor_id in values_by_factor:
            values_by_factor[factor_id].append(float(row["value"]))
    means: list[float] = []
    for factor_id in FACTOR_ORDER:
        descriptive = descriptive_rank_ic(
            values_by_factor[factor_id], sample_std_ddof
        )
        means.append(empty_mean if descriptive.mean is None else descriptive.mean)
    return FactorVector(*means)


def _parse_child(result: CampaignRun, name: str) -> dict[str, object]:
    assert result.artifacts is not None
    payload = json.loads(result.artifacts[name].decode("utf-8"))
    assert isinstance(payload, dict)
    return payload


def _month_end_flags(sessions: tuple[str, ...], one: int) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for index, session in enumerate(sessions):
        nxt_index = index + one
        if nxt_index >= len(sessions):
            continue
        if session[5:7] != sessions[nxt_index][5:7]:
            flags[session] = True
    return flags


def test_executed_children_parse_with_required_schemas(tmp_path: Path) -> None:
    cases = _p1_cases()
    inputs = cases["inputs"]
    prepared = json.loads(
        fixture_file("precondition/prepared_campaign.json").read_text(encoding="utf-8")
    )
    result = _run_prepared(tmp_path, prepared, "artifact_schema")
    assert result.status == inputs["executed_status"]
    assert result.artifacts is not None
    placeholder = json.dumps(
        {
            "name": inputs["placeholder_child"],
            "schema_version": inputs["placeholder_schema"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert result.artifacts[str(inputs["placeholder_child"])] != placeholder
    schema = inputs["artifact_schema"]
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    assert diagnostics["schema_version"] == schema["diagnostics"]
    assert "monthly_rank_ics" in diagnostics
    strategy = _parse_child(result, "strategy_returns.parquet")
    assert strategy["schema_version"] == schema["strategy"]
    assert "trials" in strategy
    review = _parse_child(result, "review_record.json")
    assert review["schema_version"] == schema["review"]
    assert review["evidence_ceiling"] == cases["expected"]["evidence_ceiling"]
    for name in required_bundle_children():
        assert name in result.artifacts


def test_forward_returns_anchor_at_execution_close(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["execution_anchor"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    prepared = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        {str(cfg["signal_date"]): True},
        "execution_anchor",
        cases,
    )
    result = _run_prepared(tmp_path, prepared, "execution_anchor")
    assert result.status == cases["inputs"]["executed_status"]
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    months = diagnostics["monthly_rank_ics"]
    assert months
    forwards = months[0]["forward_returns"]
    assert months[0]["execution_date"] == sessions[1]
    assert months[0]["label_end_date"] == sessions[-1]
    values = [row["value"] for row in forwards if row["valid"]]
    assert values
    expected = float(cfg["expected_return"])
    rel_tol = float(cfg["rel_tol"])
    for value in values:
        assert abs(float(value) - expected) < rel_tol


def test_rank_ic_is_computed_per_signal_month(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["monthly_ic"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    first = str(cfg["first_signal"])
    second = str(cfg["second_signal"])
    prepared = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        {first: True, second: True},
        "monthly_ic",
        cases,
    )
    result = _run_prepared(tmp_path, prepared, "monthly_ic")
    assert result.status == cases["inputs"]["executed_status"]
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    by_signal: dict[str, list[object]] = {}
    for month in diagnostics["monthly_rank_ics"]:
        by_signal.setdefault(month["signal_date"], []).append(month["value"])
    assert first in by_signal
    assert second in by_signal
    assert by_signal[first] != by_signal[second]


def test_continuous_paths_charge_initial_turnover_and_keep_factor_benchmarks(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["rebalance"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    flags = {
        str(row["signal_date"]): bool(row["in_universe"])
        for row in cfg["signals"]
    }
    result = _run_prepared(
        tmp_path,
        _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            flags,
            "rebalance",
            cases,
        ),
        "rebalance",
    )
    assert result.status == cases["inputs"]["executed_status"]
    costs = _parse_child(result, "cost_sensitivity.json")
    rev = str(cases["inputs"]["rev_factor_id"])
    zero = next(
        row["cost_impact_sum"]
        for row in costs["trials"]
        if row["trial_id"] == cases["inputs"]["rev_zero_trial_id"]
        and row["factor_id"] == rev
    )
    ten = next(
        row["cost_impact_sum"]
        for row in costs["trials"]
        if row["trial_id"] == cases["inputs"]["rev_ten_trial_id"]
        and row["factor_id"] == rev
    )
    assert zero == 0.0
    assert ten > zero
    strategy = _parse_child(result, "strategy_returns.parquet")
    baseline = [
        row
        for row in strategy["trials"]
        if row["trial_id"] == cases["inputs"]["equal_weight_trial_id"]
    ]
    factor_ids = {row["factor_id"] for row in baseline}
    assert factor_ids == set(cases["inputs"]["universe_factor_ids"])
    by_factor = {row["factor_id"]: row["valid"] for row in baseline}
    assert by_factor[rev] is True
    ten_path = next(
        row
        for row in strategy["trials"]
        if row["trial_id"] == cases["inputs"]["rev_ten_trial_id"]
        and row["factor_id"] == rev
    )
    first = ten_path["points"][0]
    expected = float(cases["inputs"]["initial_turnover"])
    rel_tol = float(cases["inputs"]["execution_anchor"]["rel_tol"])
    assert abs(float(first["turnover"]) - expected) < rel_tol
    assert first["cost_impact"] > 0.0


def test_diagnostic_payload_is_derived_from_execution(tmp_path: Path) -> None:
    cases = _p1_cases()
    prepared = json.loads(
        fixture_file("precondition/prepared_campaign.json").read_text(encoding="utf-8")
    )
    small = _run_prepared(tmp_path, prepared, "derived_small")
    assert small.status == cases["inputs"]["executed_status"]
    assert small.reconciliation is not None
    assert small.reconciliation.diagnostic_inputs is not None
    small_inputs = small.reconciliation.diagnostic_inputs
    cfg = cases["inputs"]["derived_large"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    large = _run_prepared(
        tmp_path,
        _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            _month_end_flags(sessions, int(cases["inputs"]["one"])),
            "derived_large",
            cases,
        ),
        "derived_large",
    )
    assert large.status == cases["inputs"]["executed_status"]
    assert large.reconciliation is not None
    assert large.reconciliation.diagnostic_inputs is not None
    large_inputs = large.reconciliation.diagnostic_inputs
    small_months = _parse_child(small, "factor_diagnostics.parquet")["monthly_rank_ics"]
    large_months = _parse_child(large, "factor_diagnostics.parquet")["monthly_rank_ics"]
    assert small_months != large_months
    small_common = _independent_common_means(small_months)
    large_common = _independent_common_means(large_months)
    if small_common:
        assert small_inputs.mean_rank_ics == small_common
    else:
        assert small_inputs.common_months == 0
        assert all(
            getattr(small_inputs.mean_rank_ics, factor_id) == 0.0
            for factor_id in FACTOR_ORDER
        )
    if large_common:
        assert large_inputs.mean_rank_ics == large_common
    else:
        assert large_inputs.common_months == 0
        assert all(
            getattr(large_inputs.mean_rank_ics, factor_id) == 0.0
            for factor_id in FACTOR_ORDER
        )
    assert large.reconciliation.final_state != cases["expected"]["invalid_state"]


def test_attempt_is_reserved_before_execution(tmp_path: Path) -> None:
    cases = _p1_cases()
    prepared = json.loads(
        fixture_file("precondition/prepared_campaign.json").read_text(encoding="utf-8")
    )
    config, _ledger = _reconcile_ready_config(tmp_path, prepared, "reserve_once")
    first = run_campaign(config)
    assert first.status == cases["inputs"]["executed_status"]
    second = run_campaign(config)
    assert second.status == "REFUSED"
    assert second.reason == "CAMPAIGN_ATTEMPT_ALREADY_CONSUMED"
    assert second.reconciliation is None


def test_boundary_signals_are_excluded_from_continuous_paths(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cutoff = load_runner_fixture("session_month_cutoff.json")
    bound = str(cutoff["inputs"]["accepted_cutoff"])
    sessions = tuple(
        session
        for session in cutoff["inputs"]["session_dates"]
        if session <= bound
    )
    flags = {
        cutoff["expected"]["june_signal"]["signal_date"]: True,
        cutoff["expected"]["july_signal"]["signal_date"]: True,
    }
    result = _run_prepared(
        tmp_path,
        _synthetic_panel(sessions, int(cases["inputs"]["one"]), flags, "rebalance", cases),
        "cutoff_boundary",
    )
    assert result.status == cases["inputs"]["executed_status"]
    strategy = _parse_child(result, "strategy_returns.parquet")
    sessions_seen = {
        point["session_date"]
        for row in strategy["trials"]
        for point in row["points"]
    }
    assert cutoff["expected"]["july_signal"]["execution_date"] not in sessions_seen


def test_held_returns_require_exact_boundary_anchors(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["execution_anchor"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    missing_sessions = (sessions[1], sessions[-1])
    for missing in missing_sessions:
        prepared = _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            {str(cfg["signal_date"]): True},
            "execution_anchor",
            cases,
        )
        hex_key = next(iter(prepared["prices"]))
        del prepared["prices"][hex_key][missing]
        prepared["anchors"][hex_key] = [
            record
            for record in prepared["anchors"][hex_key]
            if record["session_date"] != missing
        ]
        result = _run_prepared(
            tmp_path, prepared, f"missing-{missing}"
        )
        assert result.status == cases["inputs"]["executed_status"]
        diagnostics = _parse_child(result, "factor_diagnostics.parquet")
        forwards = diagnostics["monthly_rank_ics"][0]["forward_returns"]
        dropped = [row for row in forwards if row["listing_key"] == hex_key]
        assert dropped
        assert dropped[0]["valid"] is False


def test_invalid_stress_paths_fail_hard_validity(tmp_path: Path) -> None:
    cases = _p1_cases()
    prepared = json.loads(
        fixture_file("precondition/prepared_campaign.json").read_text(encoding="utf-8")
    )
    result = _run_prepared(tmp_path, prepared, "stress_hard")
    assert result.status == cases["inputs"]["executed_status"]
    assert result.reconciliation is not None
    assert result.reconciliation.diagnostic_inputs is not None
    assert result.reconciliation.diagnostic_inputs.hard_valid is False
    assert result.reconciliation.final_state == cases["expected"]["invalid_state"]


def test_robustness_keeps_missing_scheduled_years(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["robustness_years"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    flags = _month_end_flags(sessions, int(cases["inputs"]["one"]))
    for signal_date in list(flags):
        if signal_date.startswith(str(cases["inputs"]["gap_year_prefix"])):
            flags[signal_date] = False
    result = _run_prepared(
        tmp_path,
        _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            flags,
            "monthly_ic",
            cases,
        ),
        "missing_year",
    )
    assert result.status == cases["inputs"]["executed_status"]
    yearly = _parse_child(result, "yearly_robustness.json")
    assert cases["inputs"]["missing_year"] in yearly["required_years"]


def test_decile_artifact_contains_executed_fields(tmp_path: Path) -> None:
    cases = _p1_cases()
    prepared = json.loads(
        fixture_file("precondition/prepared_campaign.json").read_text(encoding="utf-8")
    )
    result = _run_prepared(tmp_path, prepared, "decile_rows")
    assert result.status == cases["inputs"]["executed_status"]
    deciles = _parse_child(result, "decile_returns.parquet")
    assert deciles["schema_version"] == cases["inputs"]["artifact_schema"]["decile"]
    assert deciles["rows"]
    required = cases["inputs"]["decile_fields"]
    for row in deciles["rows"]:
        for field in required:
            assert field in row


def test_accepted_cutoff_is_last_session_not_latest_signal(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["mid_month_cutoff"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    result = _run_prepared(
        tmp_path,
        _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            {str(cfg["signal_date"]): True},
            "execution_anchor",
            cases,
        ),
        "mid_month_cutoff",
    )
    assert result.status == cases["inputs"]["executed_status"]
    manifest = _parse_child(result, "dataset_full_manifest.json")
    assert manifest["accepted_cutoff"] == sessions[-1]
    assert manifest["accepted_cutoff"] != cfg["signal_date"]


def test_primary_folds_start_in_evaluation_year(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["warmup_folds"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    result = _run_prepared(
        tmp_path,
        _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            _month_end_flags(sessions, int(cases["inputs"]["one"])),
            "monthly_ic",
            cases,
        ),
        "warmup_folds",
    )
    assert result.status == cases["inputs"]["executed_status"]
    manifest = _parse_child(result, "dataset_full_manifest.json")
    yearly = _parse_child(result, "yearly_robustness.json")
    assert manifest["first_fold_year"] == cases["expected"]["first_fold_year"]
    assert cfg["warmup_year"] not in yearly["required_years"]


def test_rank_ic_omits_ineligible_listings(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["mixed_eligible"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    flags = _month_end_flags(sessions, int(cases["inputs"]["one"]))
    listing_count = int(cfg["eligible_count"]) + int(cfg["ineligible_count"])
    mixed = _synthetic_panel(
        sessions,
        listing_count,
        flags,
        "derived_large",
        cases,
    )
    ineligible_hex = None
    for rows in mixed["listings"].values():
        rows[-1]["in_universe_at_t"] = False
        ineligible_hex = rows[-1]["listing_key"]
    eligible = _synthetic_panel(
        sessions,
        int(cfg["eligible_count"]),
        flags,
        "derived_large",
        cases,
    )
    mixed_result = _run_prepared(tmp_path, mixed, "mixed_eligible")
    eligible_result = _run_prepared(tmp_path, eligible, "eligible_cross_section")
    assert mixed_result.status == cases["inputs"]["executed_status"]
    assert eligible_result.status == cases["inputs"]["executed_status"]
    mixed_diagnostics = _parse_child(mixed_result, "factor_diagnostics.parquet")
    eligible_diagnostics = _parse_child(
        eligible_result, "factor_diagnostics.parquet"
    )
    valid_months = [
        month
        for month in mixed_diagnostics["monthly_rank_ics"]
        if month["valid"] is True
    ]
    assert valid_months
    assert ineligible_hex is not None
    mixed_listing_keys = {
        row["listing_key"]
        for rows in mixed["listings"].values()
        for row in rows
    }
    eligible_listing_keys = {
        row["listing_key"]
        for rows in eligible["listings"].values()
        for row in rows
    }
    assert ineligible_hex in mixed_listing_keys
    assert ineligible_hex not in eligible_listing_keys
    mixed_ics = [
        (month["factor_id"], month["signal_date"], month["value"], month["valid"])
        for month in mixed_diagnostics["monthly_rank_ics"]
    ]
    eligible_ics = [
        (month["factor_id"], month["signal_date"], month["value"], month["valid"])
        for month in eligible_diagnostics["monthly_rank_ics"]
    ]
    assert mixed_ics == eligible_ics
    for month in valid_months:
        assert month["value"] is not None
        assert month["reason"] is None


def test_below_floor_rank_ic_months_remain_invalid(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["below_floor_eligible"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    listing_count = int(cfg["eligible_count"]) + int(cfg["ineligible_count"])
    prepared = _synthetic_panel(
        sessions,
        listing_count,
        _month_end_flags(sessions, int(cases["inputs"]["one"])),
        "derived_large",
        cases,
    )
    ineligible = int(cfg["ineligible_count"])
    for rows in prepared["listings"].values():
        for row in rows[-ineligible:]:
            row["in_universe_at_t"] = False
    result = _run_prepared(tmp_path, prepared, "below_floor_eligible")
    assert result.status == cases["inputs"]["executed_status"]
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    scored = [
        month
        for month in diagnostics["monthly_rank_ics"]
        if month["reason"] != "EVALUATION_FOLD_LABEL_PURGED"
    ]
    assert scored
    assert all(month["valid"] is False for month in scored)
    assert any(
        month["reason"] == cfg["invalid_reason"] for month in scored
    )


def test_unscheduled_listing_dates_do_not_enter_resets_outputs_or_lineage(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["mid_month_injection"]
    rebalance = cases["inputs"]["rebalance"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    flags = {
        str(row["signal_date"]): bool(row["in_universe"])
        for row in rebalance["signals"]
    }
    control = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        flags,
        "rebalance",
        cases,
    )
    template = next(iter(control["listings"].values()))
    injected_date = str(cfg["injected_date"])
    ineligible = json.loads(json.dumps(control))
    ineligible["listings"][injected_date] = [
        {**row, "in_universe_at_t": False} for row in template
    ]
    eligible = json.loads(json.dumps(control))
    eligible["listings"][injected_date] = [
        {**row, "in_universe_at_t": True} for row in template
    ]
    lineage = json.loads(json.dumps(control))
    mutated = []
    for row in template:
        identity = dict(row["target_identity"])
        identity["resolved_permanent_security_id"] = (
            f"OTHER-{identity['resolved_permanent_security_id']}"
        )
        alias = dict(row["alias_chain"][0])
        alias["resolved_permanent_security_id"] = identity[
            "resolved_permanent_security_id"
        ]
        mutated.append(
            {
                **row,
                "alias_chain": [alias],
                "in_universe_at_t": True,
                "target_identity": identity,
            }
        )
    lineage["listings"][injected_date] = mutated
    control_result = _run_prepared(tmp_path, control, "mid_month_control")
    ineligible_result = _run_prepared(tmp_path, ineligible, "mid_month_injected")
    eligible_result = _run_prepared(tmp_path, eligible, "eligible_mid_injected")
    lineage_result = _run_prepared(tmp_path, lineage, "lineage_mid_injected")
    executed = cases["inputs"]["executed_status"]
    assert control_result.status == executed
    assert ineligible_result.status == executed
    assert eligible_result.status == executed
    assert lineage_result.status == executed
    session = str(cfg["injected_execution"])
    assert _turnover_on(cases, control_result, session) == _turnover_on(
        cases, ineligible_result, session
    )
    assert control_result.reconciliation is not None
    assert eligible_result.reconciliation is not None
    assert lineage_result.reconciliation is not None
    assert (
        control_result.reconciliation.invalid_and_missing["invalid_required_outputs"]
        == eligible_result.reconciliation.invalid_and_missing["invalid_required_outputs"]
    )
    assert _parse_child(control_result, "factor_diagnostics.parquet") == _parse_child(
        eligible_result, "factor_diagnostics.parquet"
    )
    assert _parse_child(control_result, "decile_returns.parquet")["rows"] == _parse_child(
        eligible_result, "decile_returns.parquet"
    )["rows"]
    assert control_result.reconciliation.final_state == cases["expected"][
        "inconclusive_state"
    ]
    assert (
        lineage_result.reconciliation.final_state
        == control_result.reconciliation.final_state
    )
    assert lineage_result.reconciliation.final_state != cases["expected"][
        "invalid_state"
    ]


def test_warmup_missing_labels_do_not_invalidate_primary(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["warmup_missing_label"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    flags = _month_end_flags(sessions, int(cases["inputs"]["one"]))
    control = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        flags,
        "derived_large",
        cases,
    )
    prepared = json.loads(json.dumps(control))
    warmup = next(
        signal_date
        for signal_date in flags
        if signal_date.startswith(str(cfg["warmup_prefix"]))
    )
    label_end = sessions[
        sessions.index(warmup) + int(cases["inputs"]["one"]) + int(cfg["horizon_rows"])
    ]
    hex_key = next(iter(prepared["prices"]))
    del prepared["prices"][hex_key][label_end]
    prepared["anchors"][hex_key] = [
        record
        for record in prepared["anchors"][hex_key]
        if record["session_date"] != label_end
    ]
    control_result = _run_prepared(tmp_path, control, "warmup_control")
    result = _run_prepared(tmp_path, prepared, "warmup_missing_label")
    assert result.status == cases["inputs"]["executed_status"]
    assert control_result.status == cases["inputs"]["executed_status"]
    assert result.reconciliation is not None
    assert control_result.reconciliation is not None
    assert result.reconciliation.diagnostic_inputs is not None
    assert result.reconciliation.diagnostic_inputs.prefrozen_coverage_met is True
    assert result.reconciliation.final_state != cases["expected"]["invalid_state"]
    assert (
        result.reconciliation.invalid_and_missing["invalid_required_outputs"]
        == control_result.reconciliation.invalid_and_missing["invalid_required_outputs"]
    )


def test_empty_primary_calendar_does_not_use_warmup_coverage(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["empty_primary_calendar"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    flags = _month_end_flags(sessions, int(cases["inputs"]["one"]))
    prepared = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        flags,
        "derived_large",
        cases,
    )
    warmup = max(
        signal_date
        for signal_date in flags
        if signal_date.startswith(str(cfg["warmup_prefix"]))
    )
    for signal_date, rows in prepared["listings"].items():
        if signal_date != warmup:
            rows[0]["in_universe_at_t"] = False
    label_end = sessions[
        sessions.index(warmup) + int(cases["inputs"]["one"]) + int(cfg["horizon_rows"])
    ]
    hex_key = next(iter(prepared["prices"]))
    del prepared["prices"][hex_key][label_end]
    prepared["anchors"][hex_key] = [
        record
        for record in prepared["anchors"][hex_key]
        if record["session_date"] != label_end
    ]
    result = _run_prepared(tmp_path, prepared, "empty_primary_calendar")
    assert result.status == cases["inputs"]["executed_status"]
    assert result.reconciliation is not None
    assert result.reconciliation.diagnostic_inputs is not None
    assert result.reconciliation.diagnostic_inputs.prefrozen_coverage_met is True
    yearly = _parse_child(result, "yearly_robustness.json")
    assert cases["expected"]["first_fold_year"] not in yearly["required_years"]
    assert result.reconciliation.invalid_and_missing["invalid_required_outputs"] > 0
    assert result.reconciliation.final_state == cases["expected"]["invalid_state"]


def test_continuous_resets_across_year_boundary(tmp_path: Path) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["year_boundary"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    result = _run_prepared(
        tmp_path,
        _synthetic_panel(
            sessions,
            int(cfg["listing_count"]),
            _month_end_flags(sessions, int(cases["inputs"]["one"])),
            "rebalance",
            cases,
        ),
        "year_boundary",
    )
    assert result.status == cases["inputs"]["executed_status"]
    execution = str(cfg["january_execution"])
    turnover = _turnover_on(cases, result, execution)
    expected = float(cases["inputs"]["initial_turnover"])
    rel_tol = float(cases["inputs"]["execution_anchor"]["rel_tol"])
    assert abs(turnover - expected) < rel_tol
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    december = str(cfg["december_signal"])
    purged = [
        month
        for month in diagnostics["monthly_rank_ics"]
        if month["signal_date"] == december
    ]
    assert purged
    assert all(month["valid"] is False for month in purged)
    assert all(month["reason"] == cfg["purged_reason"] for month in purged)
    assert len(purged) == int(cfg["december_purged_factor_month_count"])
    summary = _parse_child(result, "invalid_and_missing_summary.json")
    assert summary["summary"]["purged_factor_month_count"] == int(
        cfg["purged_factor_month_count"]
    )


def test_omitted_scheduled_month_is_still_purged_and_counted(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["year_boundary"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    prepared = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        _month_end_flags(sessions, int(cases["inputs"]["one"])),
        "rebalance",
        cases,
    )
    del prepared["listings"][str(cfg["december_signal"])]
    result = _run_prepared(tmp_path, prepared, "omitted_december")
    assert result.status == cases["inputs"]["executed_status"]
    summary = _parse_child(result, "invalid_and_missing_summary.json")
    assert summary["summary"]["purged_factor_month_count"] == int(
        cfg["purged_factor_month_count"]
    )
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    december = str(cfg["december_signal"])
    purged = [
        month
        for month in diagnostics["monthly_rank_ics"]
        if month["signal_date"] == december
    ]
    assert purged
    assert all(month["valid"] is False for month in purged)
    assert all(month["reason"] == cfg["purged_reason"] for month in purged)
    execution = str(cfg["january_execution"])
    strategy = _parse_child(result, "strategy_returns.parquet")
    rev = str(cases["inputs"]["rev_factor_id"])
    ten = next(
        row
        for row in strategy["trials"]
        if row["trial_id"] == cases["inputs"]["rev_ten_trial_id"]
        and row["factor_id"] == rev
    )
    sessions_seen = {point["session_date"] for point in ten["points"]}
    assert execution in sessions_seen


def test_omitted_incomplete_cutoff_month_is_still_purged_and_counted(
    tmp_path: Path,
) -> None:
    cases = _p1_cases()
    cfg = cases["inputs"]["year_boundary"]
    sessions = _session_range(
        date.fromisoformat(str(cfg["start"])),
        int(cfg["session_count"]),
    )
    prepared = _synthetic_panel(
        sessions,
        int(cfg["listing_count"]),
        _month_end_flags(sessions, int(cases["inputs"]["one"])),
        "rebalance",
        cases,
    )
    cutoff = str(cfg["final_cutoff_signal"])
    prepared["listings"].pop(cutoff, None)
    result = _run_prepared(tmp_path, prepared, "omitted_incomplete_cutoff")
    assert result.status == cases["inputs"]["executed_status"]
    summary = _parse_child(result, "invalid_and_missing_summary.json")
    assert summary["summary"]["purged_factor_month_count"] == int(
        cfg["purged_factor_month_count"]
    )
    diagnostics = _parse_child(result, "factor_diagnostics.parquet")
    purged = [
        month
        for month in diagnostics["monthly_rank_ics"]
        if month["signal_date"] == cutoff
    ]
    assert purged
    assert all(month["valid"] is False for month in purged)
    assert all(month["reason"] == cfg["purged_reason"] for month in purged)
    assert len(purged) == int(cfg["december_purged_factor_month_count"])


def _turnover_on(
    cases: dict[str, object],
    result: CampaignRun,
    session: str,
) -> float:
    strategy = _parse_child(result, "strategy_returns.parquet")
    rev = str(cases["inputs"]["rev_factor_id"])
    ten = next(
        row
        for row in strategy["trials"]
        if row["trial_id"] == cases["inputs"]["rev_ten_trial_id"]
        and row["factor_id"] == rev
    )
    point = next(row for row in ten["points"] if row["session_date"] == session)
    return float(point["turnover"])


def _month_end_dates(
    start_year: int,
    end_year: int,
    day: int,
    one: int,
    first_month: int,
    month_count: int,
) -> tuple[str, ...]:
    return tuple(
        f"{year}-{month:02d}-{day:02d}"
        for year in range(start_year, end_year + one)
        for month in range(first_month, first_month + month_count)
    )


def _month_result(signal_date: str, value: float | None, valid: bool) -> object:
    return runner_module._MonthResult(
        signal_date,
        None,
        None,
        value,
        valid,
        None,
        (),
    )


def _trace_from_monthly(
    monthly: dict[str, tuple[object, ...]],
    dates: tuple[str, ...],
    required_years: tuple[int, ...],
    schedule: CampaignSchedule | None = None,
) -> object:
    return runner_module._ExecutionTrace(
        schedule,
        MappingProxyType(monthly),
        MappingProxyType({}),
        runner_module._PreparedPanel(
            MappingProxyType({}),
            MappingProxyType({}),
            MappingProxyType({}),
            dates,
        ),
        MappingProxyType({}),
        required_years,
    )


def _payload_from_trace(trace: object) -> dict[str, object]:
    return runner_module._diagnostic_payload_from_execution(
        _authorized_config(),
        (),
        {},
        {},
        trace,
    )


def _classify_with_unrelated_gates_pinned(
    payload: Mapping[str, object],
    fixture: dict[str, object],
) -> str:
    controls = fixture["inputs"]
    pinned = dict(payload)
    pinned.update(
        {
            "hard_valid": True,
            "prefrozen_coverage_met": True,
            "primary_matched_benchmark_comparisons_valid": True,
            "invalid_primary_comparison_count": controls[
                "control_invalid_primary_comparison_count"
            ],
            "active_return_10bps": list(controls["control_active_return_10bps"]),
            "active_return_25bps": list(controls["control_active_return_25bps"]),
        }
    )
    return classify_diagnostic(assemble_diagnostic_inputs(pinned, True))


def _independent_common_oracle(
    common_values: list[float],
    config: RunConfig,
) -> tuple[list[float], bool, list[bool]]:
    rows = [tuple(value for _factor_id in FACTOR_ORDER) for value in common_values]
    boot = bootstrap_mean_rank_ic(
        [rows],
        bootstrap_seed=config.bootstrap_seed,
        replicates=config.bootstrap_replicates,
    )
    holm = holm_adjust(boot.one_sided_p_values)
    return (
        [float(getattr(boot.observed_means, factor_id)) for factor_id in FACTOR_ORDER],
        bool(boot.bootstrap_support_all_three_factors),
        [bool(getattr(holm.rejections, factor_id)) for factor_id in FACTOR_ORDER],
    )


def _common_sample_fixture() -> dict[str, object]:
    return load_runner_fixture("common_sample_primary_ic.json")


def _fixture_month_dates(
    inputs: Mapping[str, object],
    start_key: str,
    end_key: str,
) -> tuple[str, ...]:
    return _month_end_dates(
        int(inputs[start_key]),
        int(inputs[end_key]),
        int(inputs["day"]),
        int(inputs["one"]),
        int(inputs["first_month"]),
        int(inputs["month_count"]),
    )


def _inclusive_years(inputs: Mapping[str, object]) -> tuple[int, ...]:
    return tuple(
        range(
            int(inputs["common_start_year"]),
            int(inputs["common_end_year"]) + int(inputs["one"]),
        )
    )


def test_extra_noncommon_months_change_descriptive_not_primary_inputs() -> None:
    fixture = _common_sample_fixture()
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    common_dates = _fixture_month_dates(
        inputs, "common_start_year", "common_end_year"
    )
    extra_dates = _fixture_month_dates(inputs, "extra_year", "extra_year")
    common_values = [
        float(inputs["common_base"]) + float(inputs["common_step"]) * index
        for index, _date in enumerate(common_dates)
    ]
    expected_common = sum(common_values) / len(common_values)
    mom_all_valid = descriptive_rank_ic(
        common_values + [float(inputs["mom_extra_value"])] * len(extra_dates),
        int(inputs["sample_std_ddof"]),
    )
    assert mom_all_valid.mean is not None
    assert expected_common == expected["common_mean"]
    assert mom_all_valid.mean == expected["mom_all_valid_mean"]

    monthly_base = {
        factor_id: tuple(
            _month_result(signal_date, value, True)
            for signal_date, value in zip(common_dates, common_values, strict=True)
        )
        for factor_id in FACTOR_ORDER
    }
    required_years = _inclusive_years(inputs)
    base_payload = _payload_from_trace(
        _trace_from_monthly(
            monthly_base,
            common_dates,
            required_years,
        )
    )
    extra_monthly = {
        FACTOR_ORDER[0]: monthly_base[FACTOR_ORDER[0]]
        + tuple(
            _month_result(signal_date, float(inputs["mom_extra_value"]), True)
            for signal_date in extra_dates
        ),
        FACTOR_ORDER[1]: monthly_base[FACTOR_ORDER[1]]
        + tuple(_month_result(signal_date, None, False) for signal_date in extra_dates),
        FACTOR_ORDER[2]: monthly_base[FACTOR_ORDER[2]]
        + tuple(_month_result(signal_date, None, False) for signal_date in extra_dates),
    }
    extra_payload = _payload_from_trace(
        _trace_from_monthly(
            extra_monthly,
            common_dates + extra_dates,
            required_years,
        )
    )
    config = _authorized_config()
    independent_means, independent_support, independent_rejections = (
        _independent_common_oracle(common_values, config)
    )
    assert extra_payload["common_months"] == expected["common_month_count"]
    assert extra_payload["mean_rank_ics"] == independent_means
    assert extra_payload["mean_rank_ics"] == base_payload["mean_rank_ics"]
    assert extra_payload["holm_rejections"] == independent_rejections
    assert extra_payload["holm_rejections"] == base_payload["holm_rejections"]
    assert extra_payload["bootstrap_support_all_three_factors"] is independent_support
    assert (
        extra_payload["bootstrap_support_all_three_factors"]
        == base_payload["bootstrap_support_all_three_factors"]
    )
    assert extra_payload["descriptive_mean_rank_ics_all_valid_factor_months"][0] == (
        mom_all_valid.mean
    )
    assert extra_payload["descriptive_mean_rank_ics_all_valid_factor_months"][0] != (
        extra_payload["mean_rank_ics"][0]
    )
    assert extra_payload["descriptive_mean_rank_ics_all_valid_factor_months"][1:] == (
        base_payload["descriptive_mean_rank_ics_all_valid_factor_months"][1:]
    )
    assert extra_payload["common_case_positive_year_fractions"] == (
        base_payload["common_case_positive_year_fractions"]
    )
    assert extra_payload["common_case_all_loyo_means_positive"] == (
        base_payload["common_case_all_loyo_means_positive"]
    )
    assert _classify_with_unrelated_gates_pinned(extra_payload, fixture) == (
        expected["state_with_common_means"]
    )
    assert _classify_with_unrelated_gates_pinned(base_payload, fixture) == (
        expected["state_with_common_means"]
    )


def test_common_positive_all_valid_negative_is_not_invalid() -> None:
    fixture = _common_sample_fixture()
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    common_dates = _fixture_month_dates(
        inputs, "common_start_year", "common_end_year"
    )
    extra_dates = _fixture_month_dates(inputs, "extra_year", "extra_year")
    common_values = [
        float(inputs["common_base"]) + float(inputs["common_step"]) * index
        for index, _date in enumerate(common_dates)
    ]
    monthly = {
        FACTOR_ORDER[0]: tuple(
            _month_result(signal_date, value, True)
            for signal_date, value in zip(common_dates, common_values, strict=True)
        )
        + tuple(
            _month_result(signal_date, float(inputs["mom_extra_value"]), True)
            for signal_date in extra_dates
        ),
        FACTOR_ORDER[1]: tuple(
            _month_result(signal_date, value, True)
            for signal_date, value in zip(common_dates, common_values, strict=True)
        ),
        FACTOR_ORDER[2]: tuple(
            _month_result(signal_date, value, True)
            for signal_date, value in zip(common_dates, common_values, strict=True)
        ),
    }
    payload = _payload_from_trace(
        _trace_from_monthly(
            monthly,
            common_dates + extra_dates,
            _inclusive_years(inputs),
        )
    )
    mismatched = dict(payload)
    mismatched["mean_rank_ics"] = list(
        payload["descriptive_mean_rank_ics_all_valid_factor_months"]
    )
    assert payload["mean_rank_ics"][0] == expected["common_mean"]
    assert payload["descriptive_mean_rank_ics_all_valid_factor_months"][0] == (
        expected["mom_all_valid_mean"]
    )
    assert _classify_with_unrelated_gates_pinned(payload, fixture) == (
        expected["state_with_common_means"]
    )
    assert _classify_with_unrelated_gates_pinned(mismatched, fixture) == (
        expected["mismatch_state_if_all_valid_means_used"]
    )


def test_common_sample_all_consistent_matches_descriptive() -> None:
    fixture = _common_sample_fixture()
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    common_dates = _fixture_month_dates(
        inputs, "common_start_year", "common_end_year"
    )
    common_values = [
        float(inputs["common_base"]) + float(inputs["common_step"]) * index
        for index, _date in enumerate(common_dates)
    ]
    monthly = {
        factor_id: tuple(
            _month_result(signal_date, value, True)
            for signal_date, value in zip(common_dates, common_values, strict=True)
        )
        for factor_id in FACTOR_ORDER
    }
    payload = _payload_from_trace(
        _trace_from_monthly(
            monthly,
            common_dates,
            _inclusive_years(inputs),
        )
    )
    assert payload["mean_rank_ics"] == (
        payload["descriptive_mean_rank_ics_all_valid_factor_months"]
    )
    assert payload["mean_rank_ics"] == [expected["common_mean"]] * len(FACTOR_ORDER)
    assert _classify_with_unrelated_gates_pinned(payload, fixture) == (
        expected["all_consistent_state"]
    )


def test_missing_and_insufficient_common_sample_boundaries() -> None:
    fixture = _common_sample_fixture()
    expected = fixture["expected"]
    empty_payload = _payload_from_trace(
        _trace_from_monthly({factor_id: () for factor_id in FACTOR_ORDER}, (), ())
    )
    assert empty_payload["common_months"] == expected["insufficient_common_months"]
    assert empty_payload["mean_rank_ics"] == expected["insufficient_means"]
    assert empty_payload["descriptive_mean_rank_ics_all_valid_factor_months"] == (
        expected["insufficient_means"]
    )
    assert empty_payload["bootstrap_support_all_three_factors"] is (
        expected["insufficient_bootstrap_support"]
    )
    assert empty_payload["holm_rejections"] == expected["insufficient_holm_rejections"]

    inputs = fixture["inputs"]
    missing_date = str(inputs["missing_signal_date"])
    present = float(inputs["missing_present_value"])
    one_missing = {
        FACTOR_ORDER[0]: (_month_result(missing_date, present, True),),
        FACTOR_ORDER[1]: (_month_result(missing_date, present, True),),
        FACTOR_ORDER[2]: (),
    }
    missing_payload = _payload_from_trace(
        _trace_from_monthly(
            one_missing,
            (missing_date,),
            (int(inputs["missing_required_year"]),),
        )
    )
    assert missing_payload["common_months"] == expected["insufficient_common_months"]
    assert missing_payload["mean_rank_ics"] == expected["insufficient_means"]
    assert missing_payload["descriptive_mean_rank_ics_all_valid_factor_months"] == [
        present,
        present,
        expected["insufficient_means"][-1],
    ]
    assert missing_payload["bootstrap_support_all_three_factors"] is (
        expected["insufficient_bootstrap_support"]
    )


def test_eval_date_restriction_keeps_non_eval_months_descriptive_only() -> None:
    """Helper-only defensive intersection, not production monthly builder behavior.

    This injects valid=True months outside EvaluationFold.signal_dates into
    `_diagnostic_payload_from_execution`. Production `_monthly_rank_ics` marks
    those dates invalid with EVALUATION_FOLD_LABEL_PURGED and never scores them,
    so they do not enter run_campaign descriptive means.
    """
    fixture = _common_sample_fixture()
    inputs = fixture["inputs"]
    expected = fixture["expected"]
    common_dates = _fixture_month_dates(
        inputs, "common_start_year", "common_end_year"
    )
    excluded_dates = _fixture_month_dates(
        inputs, "eval_excluded_year", "eval_excluded_year"
    )
    common_values = [
        float(inputs["common_base"]) + float(inputs["common_step"]) * index
        for index, _date in enumerate(common_dates)
    ]
    excluded_value = float(inputs["eval_excluded_value"])
    monthly = {
        factor_id: tuple(
            _month_result(signal_date, value, True)
            for signal_date, value in zip(common_dates, common_values, strict=True)
        )
        + tuple(
            _month_result(signal_date, excluded_value, True)
            for signal_date in excluded_dates
        )
        for factor_id in FACTOR_ORDER
    }
    signals = tuple(
        SignalRow(
            signal_date=signal_date,
            execution_date=signal_date,
            label_start_date=signal_date,
            label_end_date=signal_date,
            signal_index=index,
            execution_index=index,
            label_end_index=index,
            factor_label_complete=True,
            continuous_included=True,
        )
        for index, signal_date in enumerate(common_dates + excluded_dates)
    )
    folds = tuple(
        EvaluationFold(
            fold_year=year,
            bound_end=f"{year}-12-{int(inputs['day']):02d}",
            partial=False,
            signal_dates=tuple(
                signal_date
                for signal_date in common_dates
                if int(signal_date[:4]) == year
            ),
        )
        for year in _inclusive_years(inputs)
    )
    schedule = CampaignSchedule(
        session_dates=common_dates + excluded_dates,
        accepted_cutoff=excluded_dates[-1],
        horizon_return_rows=int(inputs["horizon_return_rows"]),
        horizon_purge_signal_axis_rows=int(inputs["horizon_purge_signal_axis_rows"]),
        embargo_rows=int(inputs["embargo_rows"]),
        first_fold_year=int(inputs["common_start_year"]),
        signals=signals,
        folds=folds,
        campaign_invalid=False,
    )
    payload = _payload_from_trace(
        _trace_from_monthly(
            monthly,
            common_dates + excluded_dates,
            _inclusive_years(inputs),
            schedule,
        )
    )
    descriptive = descriptive_rank_ic(
        common_values + [excluded_value] * len(excluded_dates),
        int(inputs["sample_std_ddof"]),
    )
    assert descriptive.mean is not None
    assert payload["common_months"] == expected["common_month_count"]
    assert payload["mean_rank_ics"] == [expected["common_mean"]] * len(FACTOR_ORDER)
    assert payload["descriptive_mean_rank_ics_all_valid_factor_months"] == [
        descriptive.mean
    ] * len(FACTOR_ORDER)
    assert payload["descriptive_mean_rank_ics_all_valid_factor_months"][0] != (
        payload["mean_rank_ics"][0]
    )


def test_run_campaign_entry_uses_common_means_not_all_valid_descriptive(
    tmp_path: Path,
) -> None:
    fixture = _common_sample_fixture()
    entry = fixture["inputs"]["entry_run_campaign"]
    expected = fixture["expected"]["entry_run_campaign"]
    assert isinstance(entry, dict)
    assert isinstance(expected, dict)
    cases = _p1_cases()
    monthly = cases["inputs"]["monthly_ic"]
    assert isinstance(monthly, dict)
    monthly["first_signal"] = entry["first_signal"]
    monthly["second_signal"] = entry["second_signal"]
    sessions = _session_range(
        date.fromisoformat(str(entry["start"])),
        int(entry["session_count"]),
    )
    result = _run_prepared(
        tmp_path,
        _synthetic_panel(
            sessions,
            int(entry["listing_count"]),
            _month_end_flags(sessions, int(cases["inputs"]["one"])),
            str(entry["price_case"]),
            cases,
        ),
        "entry_common_mismatch",
    )
    assert result.status == expected["executed_status"]
    assert result.reconciliation is not None
    assert result.reconciliation.diagnostic_inputs is not None
    diagnostic_inputs = result.reconciliation.diagnostic_inputs
    months = _parse_child(result, "factor_diagnostics.parquet")["monthly_rank_ics"]
    common_means = _independent_common_means(months)
    descriptive_means = _all_valid_descriptive_means(
        months,
        int(fixture["inputs"]["sample_std_ddof"]),
        float(fixture["expected"]["insufficient_means"][0]),
    )
    assert common_means
    assert diagnostic_inputs.common_months > 0
    assert diagnostic_inputs.mean_rank_ics == common_means
    assert diagnostic_inputs.mean_rank_ics != descriptive_means
    valid_by_factor: dict[str, dict[str, float]] = {
        factor_id: {} for factor_id in FACTOR_ORDER
    }
    for row in months:
        assert isinstance(row, dict)
        if row.get("valid") is not True or row.get("value") is None:
            continue
        factor_id = row["factor_id"]
        signal_date = row["signal_date"]
        if factor_id in valid_by_factor and isinstance(signal_date, str):
            valid_by_factor[factor_id][signal_date] = float(row["value"])
    common_dates = set(valid_by_factor[FACTOR_ORDER[0]]).intersection(
        *(valid_by_factor[factor_id] for factor_id in FACTOR_ORDER[1:])
    )
    extra_noncommon = False
    for factor_id in FACTOR_ORDER:
        extra_values = [
            value
            for signal_date, value in valid_by_factor[factor_id].items()
            if signal_date not in common_dates
        ]
        if not extra_values:
            continue
        extra_noncommon = True
        assert getattr(descriptive_means, factor_id) != getattr(
            common_means, factor_id
        )
    assert extra_noncommon
    assert result.reconciliation.final_state == expected["unpinned_final_state"]
