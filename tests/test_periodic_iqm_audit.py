import csv
import json

import numpy as np
import pytest
from qiskit import QuantumCircuit, QuantumRegister

from z2lgt.periodic_iqm_audit import (
    algorithmic_candidate_metrics,
    apply_algorithmic_gate,
    parse_candidate,
    physical_operation_qubits,
    recommended_candidate,
    write_audit,
)


def test_parse_periodic_candidate_requires_integral_trotter_steps():
    assert parse_candidate("0.8:0.4") == (0.8, 0.4)
    with pytest.raises(ValueError):
        parse_candidate("0.8")
    with pytest.raises(ValueError):
        parse_candidate("0.8:0.3")


def test_physical_operation_qubits_supports_packed_transpiler_output():
    compiled = QuantumCircuit(2)
    compiled.cz(0, 1)
    compiled.measure_all()
    mapping = [10, 11]
    assert physical_operation_qubits(compiled, mapping, "cz") == [(10, 11)]
    assert physical_operation_qubits(compiled, mapping, "measure") == [
        (10,),
        (11,),
    ]


def test_physical_operation_qubits_supports_full_device_output():
    compiled = QuantumCircuit(53, 1)
    compiled.cz(30, 0)
    compiled.measure(30, 0)
    mapping = list(range(12))
    assert physical_operation_qubits(compiled, mapping, "cz") == [(30, 0)]
    assert physical_operation_qubits(compiled, mapping, "measure") == [(30,)]


def test_physical_operation_qubits_uses_global_position_across_registers():
    ancilla = QuantumRegister(3, "ancilla")
    data = QuantumRegister(2, "q")
    compiled = QuantumCircuit(ancilla, data)
    compiled.cz(data[0], ancilla[2])
    assert physical_operation_qubits(compiled, [10, 11], "cz") == [(3, 2)]


def test_periodic_iqm_candidate_reproduces_validated_signal_and_resources():
    row = algorithmic_candidate_metrics(0.8, 0.4)
    assert np.isclose(row["exact_sector_separation"], 0.205847, atol=1e-6)
    assert np.isclose(row["trotter_sector_separation"], 0.148869, atol=1e-6)
    assert row["separation_retained"] > 0.70
    assert row["minimum_state_fidelity"] > 0.91
    assert row["source_qubit_count"] == 12
    assert row["source_max_two_qubit_gate_count"] == 80
    assert row["source_measurement_count"] == 8


def test_recommendation_uses_explicit_gate_then_shallower_candidate():
    shallow = algorithmic_candidate_metrics(0.8, 0.4)
    accurate = algorithmic_candidate_metrics(0.8, 0.2)
    for row in (shallow, accurate):
        apply_algorithmic_gate(
            row,
            min_fidelity=0.85,
            min_separation_retained=0.60,
            min_trotter_separation=0.10,
        )
    assert recommended_candidate([shallow, accurate]) == "t=0.8,dt=0.4"


def test_audit_outputs_preserve_no_hardware_execution_status(tmp_path):
    row = algorithmic_candidate_metrics(0.8, 0.4)
    apply_algorithmic_gate(
        row,
        min_fidelity=0.85,
        min_separation_retained=0.60,
        min_trotter_separation=0.10,
    )
    row["recommended"] = True
    report = {
        "safety": {"backend_run_called": False, "job_submitted": False},
        "candidates": [row],
    }
    json_path, csv_path = write_audit(
        report,
        tmp_path / "audit.json",
        tmp_path / "audit.csv",
    )
    persisted = json.loads(json_path.read_text(encoding="utf-8"))
    assert persisted["safety"]["backend_run_called"] is False
    assert persisted["safety"]["job_submitted"] is False
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["recommended"] == "True"
