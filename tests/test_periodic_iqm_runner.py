import json
from pathlib import Path

import pytest

from z2lgt.iqm_candidate import candidate_id, sha256_file
from z2lgt.periodic_iqm_runner import (
    require_explicit_periodic_hardware_consent,
    validate_periodic_hardware_manifest,
)


def periodic_manifest(tmp_path: Path) -> dict:
    qpy_paths = [tmp_path / "Wplus.qpy", tmp_path / "Wminus.qpy"]
    for index, path in enumerate(qpy_paths):
        path.write_bytes(f"frozen-{index}".encode())
    hashes = [sha256_file(path) for path in qpy_paths]
    identity = {
        "batch": "periodic-two-sector-t0.8-dt0.4",
        "server_url": "https://resonance.meetiqm.com",
        "quantum_computer": "emerald",
        "calibration_set_id": "00000000-0000-0000-0000-000000000001",
        "shots": 1000,
        "optimization_level": 3,
        "seed_transpiler": 7,
        "qpy_sha256": hashes,
    }
    circuits = []
    for case, sign, path, digest in zip(
        ("Wplus", "Wminus"), (1, -1), qpy_paths, hashes, strict=True
    ):
        circuits.append(
            {
                "case": case,
                "wilson_sector": sign,
                "logical_to_physical": list(range(12)),
                "qpy": str(path),
                "qpy_sha256": digest,
            }
        )
    return {
        "schema_version": 1,
        "candidate_id": candidate_id(identity),
        **identity,
        "time": 0.8,
        "dt": 0.4,
        "trotter_steps": 2,
        "wilson_sectors": {"Wplus": 1, "Wminus": -1},
        "hardware_checks": {
            "same_mapping_for_both_sectors": True,
            "maximum_native_cz_count": True,
        },
        "all_tests_passed": True,
        "request_validated": True,
        "circuits_frozen": True,
        "human_review_approved": True,
        "hardware_execution_started": False,
        "hardware_submitted": False,
        "circuits": circuits,
    }


def test_periodic_manifest_accepts_only_reviewed_two_sector_candidate(tmp_path):
    manifest = periodic_manifest(tmp_path)
    paths = validate_periodic_hardware_manifest(
        manifest,
        root=tmp_path,
        expected_quantum_computer="emerald",
        expected_shots=1000,
    )
    assert paths == [tmp_path / "Wplus.qpy", tmp_path / "Wminus.qpy"]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("wilson_sectors", {"Wplus": 1}, "sector labels"),
        ("time", 1.0, "t=0.8"),
        ("dt", 0.2, "dt=0.4"),
        ("trotter_steps", 4, "two Trotter"),
    ],
)
def test_periodic_manifest_rejects_changed_physics_point(
    tmp_path, field, value, message
):
    manifest = periodic_manifest(tmp_path)
    manifest[field] = value
    with pytest.raises(PermissionError, match=message):
        validate_periodic_hardware_manifest(
            manifest,
            root=tmp_path,
            expected_quantum_computer="emerald",
            expected_shots=1000,
        )


def test_periodic_manifest_rejects_failed_hardware_freeze_check(tmp_path):
    manifest = periodic_manifest(tmp_path)
    manifest["hardware_checks"]["maximum_native_cz_count"] = False
    with pytest.raises(PermissionError, match="freeze checks"):
        validate_periodic_hardware_manifest(
            manifest,
            root=tmp_path,
            expected_quantum_computer="emerald",
            expected_shots=1000,
        )


def test_periodic_hardware_requires_environment_and_candidate_confirmation(tmp_path):
    candidate = periodic_manifest(tmp_path)["candidate_id"]
    with pytest.raises(PermissionError, match="ALLOW_PERIODIC"):
        require_explicit_periodic_hardware_consent(
            submit=True,
            environment={},
            candidate_id=candidate,
            confirmation=candidate[:12],
        )
    with pytest.raises(PermissionError, match="confirm-candidate"):
        require_explicit_periodic_hardware_consent(
            submit=True,
            environment={"Z2LGT_ALLOW_PERIODIC_IQM_HARDWARE": "YES"},
            candidate_id=candidate,
            confirmation="wrong",
        )
    require_explicit_periodic_hardware_consent(
        submit=True,
        environment={"Z2LGT_ALLOW_PERIODIC_IQM_HARDWARE": "YES"},
        candidate_id=candidate,
        confirmation=candidate[:12],
    )


def test_dry_run_needs_no_hardware_consent(tmp_path):
    candidate = periodic_manifest(tmp_path)["candidate_id"]
    require_explicit_periodic_hardware_consent(
        submit=False,
        environment={},
        candidate_id=candidate,
        confirmation=None,
    )


def test_periodic_manifest_fixture_is_json_serializable(tmp_path):
    json.dumps(periodic_manifest(tmp_path))
