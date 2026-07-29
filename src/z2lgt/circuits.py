"""Trotter circuits, ideal simulation, resource reports, and export."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, qasm2, transpile
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import Pauli, Statevector
from qiskit.qpy import dump as qpy_dump
from qiskit_aer import AerSimulator

from .model import Z2Model


def trotter_circuit(
    model: Z2Model,
    initial_bits: list[int],
    time: float,
    dt: float,
    *,
    measure: bool = False,
) -> QuantumCircuit:
    """Build a first-order product-formula circuit from the model Pauli terms."""
    if time < -1e-12 or dt <= 0:
        raise ValueError("time must be nonnegative and dt must be positive")
    n_steps = int(round(time / dt))
    if not np.isclose(n_steps * dt, time, atol=1e-10):
        raise ValueError("time must be an integer multiple of dt")
    circuit = QuantumCircuit(model.n_qubits)
    for qubit, bit in enumerate(initial_bits):
        if bit:
            circuit.x(qubit)
    for _ in range(n_steps):
        for term in model.hamiltonian_terms():
            gate = PauliEvolutionGate(Pauli(term.qiskit_label), time=term.coefficient * dt)
            circuit.append(gate, range(model.n_qubits))
    if measure:
        circuit.measure_all()
    return circuit


def compiled_circuit(circuit: QuantumCircuit, *, optimization_level: int = 1) -> QuantumCircuit:
    """Compile to a hardware-generic CX/SX/RZ basis."""
    return transpile(
        circuit,
        basis_gates=["rz", "sx", "x", "cx"],
        optimization_level=optimization_level,
        seed_transpiler=1729,
    )


def ideal_statevector(circuit: QuantumCircuit) -> np.ndarray:
    if circuit.num_clbits:
        raise ValueError("statevector circuit must not contain measurements")
    return np.asarray(Statevector.from_instruction(circuit).data)


def ideal_counts(circuit: QuantumCircuit, shots: int, seed: int = 12345) -> dict[str, int]:
    """Run an ideal Aer shot simulation and return Qiskit's raw counts."""
    backend = AerSimulator()
    compiled = transpile(circuit, backend, seed_transpiler=seed)
    return dict(backend.run(compiled, shots=shots, seed_simulator=seed).result().get_counts())


def resource_metrics(circuit: QuantumCircuit) -> dict[str, int]:
    compiled = compiled_circuit(circuit)
    operations = compiled.count_ops()
    two_qubit = sum(
        count for instruction, count in operations.items()
        if instruction in {"cx", "cz", "ecr", "rxx", "ryy", "rzz", "iswap", "swap"}
    )
    measurement_count = int(operations.get("measure", 0))
    return {
        "qubit_count": compiled.num_qubits,
        "depth": int(compiled.depth()),
        "two_qubit_gate_count": int(two_qubit),
        "measurement_count": measurement_count,
    }


def export_circuit(
    circuit: QuantumCircuit, stem: Path, *, qpy_stem: Path | None = None
) -> dict[str, str]:
    """Export QASM2 and QPY without invoking any backend."""
    stem.parent.mkdir(parents=True, exist_ok=True)
    qasm_path = stem.with_suffix(".qasm")
    qpy_path = (qpy_stem or stem).with_suffix(".qpy")
    qpy_path.parent.mkdir(parents=True, exist_ok=True)
    qasm_path.write_text(qasm2.dumps(circuit), encoding="utf-8")
    with qpy_path.open("wb") as handle:
        qpy_dump(circuit, handle)
    return {"qasm": str(qasm_path), "qpy": str(qpy_path)}
