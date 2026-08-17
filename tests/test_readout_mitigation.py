import json

import numpy as np
from qiskit import QuantumCircuit
from qiskit.qpy import dump as qpy_dump

from z2lgt.readout_mitigation import (
    counts_to_probability_vector,
    independent_assignment_matrix,
    index_to_qiskit_key,
    measured_physical_qubits_by_clbit,
    mitigate_counts_independent,
    qiskit_key_to_index,
    readout_probabilities_from_manifest,
)


def test_qiskit_key_little_endian_index_roundtrip():
    assert qiskit_key_to_index("0010", 4) == 2
    for index in range(16):
        assert qiskit_key_to_index(index_to_qiskit_key(index, 4), 4) == index


def test_independent_readout_mitigation_recovers_distribution():
    true = np.zeros(4)
    true[0b10] = 1.0
    matrix = independent_assignment_matrix([0.05, 0.10])
    observed = matrix @ true
    counts = {
        index_to_qiskit_key(index, 2): probability * 10_000
        for index, probability in enumerate(observed)
    }
    result = mitigate_counts_independent(counts, [0.05, 0.10])
    mitigated, _ = counts_to_probability_vector(result["mitigated_counts"], 2)
    assert np.allclose(mitigated, true, atol=1e-12)
    assert result["negative_probability_mass"] < 1e-12


def test_measured_physical_qubits_by_clbit_uses_measurement_order(tmp_path):
    circuit = QuantumCircuit(5, 3)
    circuit.measure(4, 0)
    circuit.measure(2, 1)
    circuit.measure(0, 2)
    qpy_path = tmp_path / "mapped.qpy"
    with qpy_path.open("wb") as handle:
        qpy_dump(circuit, handle)

    assert measured_physical_qubits_by_clbit(qpy_path) == [4, 2, 0]


def test_readout_probabilities_from_manifest_follow_qpy_classical_bits(tmp_path):
    circuit = QuantumCircuit(6, 3)
    circuit.measure(4, 0)
    circuit.measure(2, 1)
    circuit.measure(5, 2)
    qpy_path = tmp_path / "mapped.qpy"
    with qpy_path.open("wb") as handle:
        qpy_dump(circuit, handle)

    manifest_path = tmp_path / "readiness_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "calibration_set_id": "calibration",
                "quantum_computer": "emerald",
                "circuits": [
                    {
                        "case": "Wplus",
                        "qpy": str(qpy_path),
                        "measurements": [
                            {"physical_qubit": 5, "error": 0.05},
                            {"physical_qubit": 4, "error": 0.04},
                            {"physical_qubit": 2, "error": 0.02},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    calibration = readout_probabilities_from_manifest(manifest_path, case="Wplus")

    assert calibration["physical_qubits_by_classical_bit"] == [4, 2, 5]
    assert calibration["readout_error_probabilities"] == [0.04, 0.02, 0.05]
