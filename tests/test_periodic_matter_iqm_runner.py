from pathlib import Path

import pytest
from qiskit import QuantumCircuit
from qiskit.qpy import dump as qpy_dump

from z2lgt.iqm_candidate import candidate_id, sha256_file
from z2lgt.periodic_matter_iqm_runner import (
    require_explicit_periodic_matter_hardware_consent,
    validate_periodic_matter_submission_manifest,
)


def periodic_matter_manifest(tmp_path: Path) -> dict:
    paths = []
    for name in ("Wplus", "Wminus"):
        circuit = QuantumCircuit(8, 4)
        circuit.measure(range(4), range(4))
        qpy_path = tmp_path / f"{name}.qpy"
        with qpy_path.open("wb") as handle:
            qpy_dump(circuit, handle)
        paths.append(qpy_path)
    identity = {
        "batch": "periodic-matter-two-sector-t0.8-dt0.4",
        "server_url": "https://example.invalid",
        "quantum_computer": "emerald",
        "calibration_set_id": "calibration",
        "shots": 5000,
        "optimization_level": 3,
        "seed_transpiler": 7,
        "qpy_sha256": [sha256_file(path) for path in paths],
    }
    return {
        "schema_version": 1,
        "candidate_id": candidate_id(identity),
        **identity,
        "all_tests_passed": True,
        "request_validated": True,
        "circuits_frozen": True,
        "human_review_approved": True,
        "hardware_submitted": False,
        "submission_started": False,
        "time": 0.8,
        "dt": 0.4,
        "trotter_steps": 2,
        "readout_mode": "matter_only",
        "wilson_sectors": {"Wplus": 1, "Wminus": -1},
        "hardware_checks": {
            "same_mapping_for_both_sectors": True,
            "maximum_native_cz_count": True,
            "maximum_native_depth": True,
            "maximum_cz_error": True,
            "maximum_readout_error": True,
            "matter_only_measurements": True,
        },
        "circuits": [
            {
                "case": "Wplus",
                "wilson_sector": 1,
                "logical_to_physical": list(range(8)),
                "measurement_count": 4,
                "qpy": str(paths[0]),
                "qpy_sha256": sha256_file(paths[0]),
            },
            {
                "case": "Wminus",
                "wilson_sector": -1,
                "logical_to_physical": list(range(8)),
                "measurement_count": 4,
                "qpy": str(paths[1]),
                "qpy_sha256": sha256_file(paths[1]),
            },
        ],
    }


def test_periodic_matter_manifest_accepts_reduced_candidate(tmp_path):
    manifest = periodic_matter_manifest(tmp_path)
    paths = validate_periodic_matter_submission_manifest(
        manifest,
        root=tmp_path,
        expected_quantum_computer="emerald",
        expected_shots=5000,
    )
    assert len(paths) == 2


def test_periodic_matter_manifest_rejects_wrong_mode(tmp_path):
    manifest = periodic_matter_manifest(tmp_path)
    manifest["readout_mode"] = "joint"
    with pytest.raises(PermissionError, match="matter_only"):
        validate_periodic_matter_submission_manifest(
            manifest,
            root=tmp_path,
            expected_quantum_computer="emerald",
            expected_shots=5000,
        )


def test_periodic_matter_hardware_requires_environment_and_candidate_confirmation(tmp_path):
    candidate = periodic_matter_manifest(tmp_path)["candidate_id"]
    require_explicit_periodic_matter_hardware_consent(
        submit=False,
        environment={},
        candidate_id=candidate,
        confirmation=None,
    )
    with pytest.raises(PermissionError, match="confirm-candidate"):
        require_explicit_periodic_matter_hardware_consent(
            submit=True,
            environment={"Z2LGT_ALLOW_PERIODIC_IQM_HARDWARE": "YES"},
            candidate_id=candidate,
            confirmation="wrong",
        )
    require_explicit_periodic_matter_hardware_consent(
        submit=True,
        environment={"Z2LGT_ALLOW_PERIODIC_IQM_HARDWARE": "YES"},
        candidate_id=candidate,
        confirmation=candidate[:12],
    )
