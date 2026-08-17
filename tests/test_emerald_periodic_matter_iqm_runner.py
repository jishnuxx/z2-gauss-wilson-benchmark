from pathlib import Path

import pytest
from qiskit import QuantumCircuit
from qiskit.qpy import dump as qpy_dump

from z2lgt.emerald_periodic_matter_iqm_runner import (
    EXPECTED_BATCH,
    EXPECTED_CIRCUIT_ORDER,
    EXPECTED_LAYOUT,
    EXPECTED_POINTS,
    require_explicit_emerald_scan_hardware_consent,
    validate_emerald_scan_submission_manifest,
)
from z2lgt.iqm_candidate import candidate_id, sha256_file


def emerald_manifest(tmp_path: Path) -> dict:
    circuit_records = []
    paths = []
    for index, (time, dt, case, sector) in enumerate(EXPECTED_CIRCUIT_ORDER):
        circuit = QuantumCircuit(8, 4)
        circuit.measure(range(4), range(4))
        path = tmp_path / f"circuit_{index}.qpy"
        with path.open("wb") as handle:
            qpy_dump(circuit, handle)
        paths.append(path)
        circuit_records.append(
            {
                "time": time,
                "dt": dt,
                "trotter_steps": 2,
                "case": case,
                "wilson_sector": sector,
                "logical_to_physical_indices": list(EXPECTED_LAYOUT),
                "measurement_count": 4,
                "measurement_classical_bits": [0, 1, 2, 3],
                "move_count": 0,
                "qpy": str(path),
                "qpy_sha256": sha256_file(path),
            }
        )
    identity = {
        "batch": EXPECTED_BATCH,
        "server_url": "https://example.invalid",
        "quantum_computer": "emerald",
        "calibration_set_id": "00000000-0000-0000-0000-000000000001",
        "shots": 5000,
        "optimization_level": 3,
        "seed_transpiler": 7,
        "qpy_sha256": [sha256_file(path) for path in paths],
    }
    return {
        "schema_version": 1,
        "candidate_id": candidate_id(identity),
        **identity,
        "benchmark_type": "two_step_fixed_product_formula_scan",
        "points": [
            {"time": time, "dt": dt, "trotter_steps": 2}
            for time, dt in EXPECTED_POINTS
        ],
        "readout_mode": "matter_only",
        "wilson_sectors": {"Wplus": 1, "Wminus": -1},
        "fixed_initial_layout_indices": list(EXPECTED_LAYOUT),
        "hardware_checks": {"six_circuit_scan": True},
        "all_tests_passed": True,
        "request_validated": True,
        "circuits_frozen": True,
        "human_review_approved": True,
        "submission_started": False,
        "hardware_submitted": False,
        "circuits": circuit_records,
    }


def mark_repeat2(manifest: dict) -> None:
    manifest["batch"] = f"{EXPECTED_BATCH}-repeat2"
    manifest["replicate_label"] = "repeat2"
    manifest["candidate_id"] = candidate_id(
        {
            "batch": manifest["batch"],
            "server_url": manifest["server_url"],
            "quantum_computer": manifest["quantum_computer"],
            "calibration_set_id": manifest["calibration_set_id"],
            "shots": manifest["shots"],
            "optimization_level": manifest["optimization_level"],
            "seed_transpiler": manifest["seed_transpiler"],
            "qpy_sha256": [
                record["qpy_sha256"] for record in manifest["circuits"]
            ],
        }
    )


def test_emerald_manifest_accepts_reviewed_six_circuit_scan(tmp_path):
    manifest = emerald_manifest(tmp_path)
    paths = validate_emerald_scan_submission_manifest(
        manifest,
        root=tmp_path,
        expected_quantum_computer="emerald",
        expected_shots=5000,
    )
    assert len(paths) == 6


def test_emerald_manifest_accepts_explicit_repeat2_batch(tmp_path):
    manifest = emerald_manifest(tmp_path)
    mark_repeat2(manifest)
    paths = validate_emerald_scan_submission_manifest(
        manifest,
        root=tmp_path,
        expected_replicate_label="repeat2",
    )
    assert len(paths) == 6


def test_emerald_manifest_rejects_move_operation(tmp_path):
    manifest = emerald_manifest(tmp_path)
    manifest["circuits"][0]["move_count"] = 1
    with pytest.raises(PermissionError, match="MOVE"):
        validate_emerald_scan_submission_manifest(manifest, root=tmp_path)


def test_emerald_manifest_rejects_wrong_classical_readout(tmp_path):
    manifest = emerald_manifest(tmp_path)
    manifest["circuits"][0]["measurement_classical_bits"] = [0, 1, 2, 2]
    with pytest.raises(PermissionError, match="classical"):
        validate_emerald_scan_submission_manifest(manifest, root=tmp_path)


def test_emerald_scan_submission_requires_two_consent_signals(tmp_path):
    candidate = emerald_manifest(tmp_path)["candidate_id"]
    require_explicit_emerald_scan_hardware_consent(
        submit=False,
        environment={},
        candidate_id=candidate,
        confirmation=None,
    )
    with pytest.raises(PermissionError, match="confirm-candidate"):
        require_explicit_emerald_scan_hardware_consent(
            submit=True,
            environment={"Z2LGT_ALLOW_EMERALD_SCAN_HARDWARE": "YES"},
            candidate_id=candidate,
            confirmation="wrong",
        )
    require_explicit_emerald_scan_hardware_consent(
        submit=True,
        environment={"Z2LGT_ALLOW_EMERALD_SCAN_HARDWARE": "YES"},
        candidate_id=candidate,
        confirmation=candidate[:12],
    )
