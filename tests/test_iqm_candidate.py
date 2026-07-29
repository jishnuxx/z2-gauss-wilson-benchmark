import json
from pathlib import Path

import pytest

from z2lgt.iqm_candidate import candidate_id, sha256_file, validate_hardware_manifest


def approved_manifest(tmp_path: Path) -> dict:
    qpy = tmp_path / "candidate.qpy"
    qpy.write_bytes(b"frozen-circuit")
    identity = {
        "batch": "blindspot-minimal",
        "server_url": "https://resonance.meetiqm.com",
        "quantum_computer": "emerald",
        "calibration_set_id": "00000000-0000-0000-0000-000000000001",
        "shots": 1000,
        "optimization_level": 3,
        "seed_transpiler": 7,
        "qpy_sha256": [sha256_file(qpy)],
    }
    return {
        "schema_version": 1,
        "candidate_id": candidate_id(identity),
        **identity,
        "all_tests_passed": True,
        "request_validated": True,
        "circuits_frozen": True,
        "human_review_approved": True,
        "hardware_execution_started": False,
        "hardware_submitted": False,
        "circuits": [{"qpy": str(qpy), "qpy_sha256": sha256_file(qpy)}],
    }


def test_approved_manifest_returns_verified_qpy(tmp_path):
    manifest = approved_manifest(tmp_path)
    paths = validate_hardware_manifest(
        manifest,
        root=tmp_path,
        expected_quantum_computer="emerald",
        expected_shots=1000,
    )
    assert paths == [tmp_path / "candidate.qpy"]


@pytest.mark.parametrize(
    "gate",
    ["all_tests_passed", "request_validated", "circuits_frozen", "human_review_approved"],
)
def test_manifest_requires_every_readiness_gate(tmp_path, gate):
    manifest = approved_manifest(tmp_path)
    manifest[gate] = False
    with pytest.raises(PermissionError, match=gate):
        validate_hardware_manifest(manifest, root=tmp_path)


def test_manifest_rejects_modified_frozen_circuit(tmp_path):
    manifest = approved_manifest(tmp_path)
    Path(manifest["circuits"][0]["qpy"]).write_bytes(b"modified")
    with pytest.raises(PermissionError, match="hash mismatch"):
        validate_hardware_manifest(manifest, root=tmp_path)


def test_manifest_rejects_prior_hardware_attempt(tmp_path):
    manifest = approved_manifest(tmp_path)
    manifest["hardware_execution_started"] = True
    with pytest.raises(PermissionError, match="prior hardware execution attempt"):
        validate_hardware_manifest(manifest, root=tmp_path)


def test_manifest_rejects_target_or_shot_change(tmp_path):
    manifest = approved_manifest(tmp_path)
    with pytest.raises(PermissionError, match="quantum computer"):
        validate_hardware_manifest(
            manifest, root=tmp_path, expected_quantum_computer="garnet", expected_shots=1000
        )
    with pytest.raises(PermissionError, match="shots"):
        validate_hardware_manifest(
            manifest, root=tmp_path, expected_quantum_computer="emerald", expected_shots=2000
        )


def test_manifest_rejects_identity_tampering(tmp_path):
    manifest = approved_manifest(tmp_path)
    manifest["calibration_set_id"] = "00000000-0000-0000-0000-000000000002"
    with pytest.raises(PermissionError, match="identity hash"):
        validate_hardware_manifest(manifest, root=tmp_path)


def test_manifest_is_json_serializable(tmp_path):
    json.dumps(approved_manifest(tmp_path))
