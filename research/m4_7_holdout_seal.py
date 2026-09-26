"""Holdout seal script and confirmation tooling for M4.7 (plan sections 1.4 and 5.4).

``seal`` derives the prospective seal from the two recorded inputs (the raw
membership file and ``snapshot.components_retrieved_utc_date``) through
``data.holdout_partition.write_prospective_seal``, verifies the written record
against those inputs, and returns ``seal_prospective_sha256``. The script reads
exactly ``manifest.json`` and ``membership/historical_components_raw.parquet``
(S5). ``confirmed_seal_bytes`` adds the census confirmation block without
changing any prospective field, so the three digests stay acyclic (C33).

Run as ``python -m research.m4_7_holdout_seal --snapshot-id <ID> --sealing-actor <role>
--authorization-reference <engineering-log entry>``.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from data.holdout_partition import (
    MEMBERSHIP_FILE,
    SnapshotRefusal,
    read_manifest,
    seal_bytes,
    sha256_bytes,
    write_prospective_seal,
)
from research.m4_7_universe_build import snapshot_dir_from_args


REPOSITORY_SEAL = Path(__file__).resolve().parents[1] / "docs/preregistrations/m4_7_holdout_seal_v1.json"


def seal_snapshot(
    snapshot_dir: Path | str,
    *,
    sealing_actor: str,
    authorization_reference: str,
    clock: Callable[[], datetime] | None = None,
) -> tuple[dict[str, Any], str]:
    """Write the prospective seal and verify its inputs and bytes; return the record and its SHA-256."""
    now = (clock or (lambda: datetime.now(timezone.utc)))().astimezone(timezone.utc)
    record, prospective = write_prospective_seal(
        Path(snapshot_dir),
        sealed_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        sealing_actor=sealing_actor,
        authorization_reference=authorization_reference,
    )
    manifest = read_manifest(Path(snapshot_dir))
    expected = {
        "components_raw_sha256": manifest["files"]["membership"]["sha256"],
        "components_retrieved_utc_date": manifest["snapshot"]["components_retrieved_utc_date"],
    }
    if record["inputs"] != expected or sha256_bytes(seal_bytes(record)) != prospective:
        raise SnapshotRefusal("seal_verification_failed", MEMBERSHIP_FILE)
    if record["confirmation"]["status"] != "pending":
        raise SnapshotRefusal("seal_verification_failed", "prospective confirmation must be pending")
    return record, prospective


def confirmed_seal_bytes(
    prospective_bytes: bytes,
    *,
    census_json_sha256: str,
    status: str,
    identity_adjusted_min_month_end_count: int | None,
    integrity: dict[str, Any],
) -> bytes:
    """The committed seal record: the prospective fields plus the census confirmation block (plan 5.4 step 6)."""
    if status not in ("confirmed", "caveat"):
        raise ValueError("confirmation status must be confirmed or caveat")
    record = json.loads(prospective_bytes)
    if record["confirmation"]["status"] != "pending":
        raise SnapshotRefusal("seal_not_prospective", "the snapshot seal must carry confirmation.status = pending")
    record["automated_integrity_checks_over_holdout_rows"].update(integrity)
    record["confirmation"] = {
        "status": status,
        "identity_adjusted_min_month_end_count": identity_adjusted_min_month_end_count,
        "census_json_sha256": census_json_sha256,
        "seal_prospective_sha256": sha256_bytes(prospective_bytes),
    }
    return seal_bytes(record)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m research.m4_7_holdout_seal")
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--sealing-actor", required=True)
    parser.add_argument("--authorization-reference", required=True)
    args = parser.parse_args(argv)
    try:
        record, prospective = seal_snapshot(snapshot_dir_from_args(args), sealing_actor=args.sealing_actor,
                                            authorization_reference=args.authorization_reference)
    except SnapshotRefusal as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"holdout_start": record["holdout_start"], "holdout_end_exclusive": record["holdout_end_exclusive"],
                      "seal_prospective_sha256": prospective}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
