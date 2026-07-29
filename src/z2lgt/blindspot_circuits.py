"""Qiskit circuits for local and joint blind-spot diagnostics."""

from __future__ import annotations

from qiskit import QuantumCircuit

from .blindspot_model import BlindSpotModel


CASES = ("no_error", "gauge_violating", "gauge_preserving_string")


def target_preparation_circuit() -> QuantumCircuit:
    """Prepare the +1 sector of all Gauss checks and W on four links."""
    circuit = QuantumCircuit(4, name="prepare_physical_Wplus")
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.cx(2, 3)
    circuit.h(range(4))
    return circuit


def _append_target_preparation(circuit: QuantumCircuit) -> None:
    circuit.compose(target_preparation_circuit(), qubits=range(4), inplace=True)


def inject_error(
    circuit: QuantumCircuit,
    error_type: str,
    *,
    coherent_angle: float | None = None,
) -> None:
    if error_type not in CASES:
        raise ValueError(f"unknown error type: {error_type}")
    if error_type == "gauge_violating":
        circuit.z(0) if coherent_angle is None else circuit.rz(coherent_angle, 0)
    elif error_type == "gauge_preserving_string":
        circuit.x(0) if coherent_angle is None else circuit.rx(coherent_angle, 0)


def gauss_check_circuit(check_index: int, error_type: str = "no_error") -> QuantumCircuit:
    """Measure one X-type Gauss check with a fifth-qubit ancilla."""
    model = BlindSpotModel()
    if not 0 <= check_index < len(model.gauss_checks):
        raise IndexError(check_index)
    circuit = QuantumCircuit(5, 1, name=f"{error_type}_G{check_index}")
    _append_target_preparation(circuit)
    circuit.barrier()
    inject_error(circuit, error_type)
    circuit.barrier()
    ancilla = 4
    circuit.h(ancilla)
    for qubit, symbol in enumerate(model.gauss_checks[check_index].word):
        if symbol == "X":
            circuit.cx(ancilla, qubit)
    circuit.h(ancilla)
    circuit.measure(ancilla, 0)
    return circuit


def wilson_circuit(error_type: str = "no_error") -> QuantumCircuit:
    """Measure W=ZZZZ directly; bitstring parity is its eigenvalue."""
    circuit = QuantumCircuit(4, 4, name=f"{error_type}_W")
    _append_target_preparation(circuit)
    circuit.barrier()
    inject_error(circuit, error_type)
    circuit.barrier()
    circuit.measure(range(4), range(4))
    return circuit


def joint_diagnostic_circuit(
    error_type: str = "no_error",
    *,
    idle_layers: int = 0,
    coherent_angle: float | None = None,
) -> QuantumCircuit:
    """Measure W and all local Gauss syndromes with a static Clifford decode.

    After inverse state preparation, measured qubits ``(q0,q1,q2,q3)`` encode
    violations of ``(W,G0,G1,G2)``.  The redundant local syndrome is
    ``G3_violation = q1 xor q2 xor q3``.  This supports joint shot-level
    Gauss and string-aware postselection without dynamic circuits.
    """
    if idle_layers < 0:
        raise ValueError("idle_layers must be nonnegative")
    circuit = QuantumCircuit(4, 4, name=f"{error_type}_joint")
    _append_target_preparation(circuit)
    circuit.barrier()
    inject_error(circuit, error_type, coherent_angle=coherent_angle)
    for _ in range(idle_layers):
        circuit.barrier()
        for qubit in range(4):
            circuit.id(qubit)
    circuit.barrier()
    circuit.compose(target_preparation_circuit().inverse(), qubits=range(4), inplace=True)
    circuit.measure(range(4), range(4))
    return circuit


def syndrome_response_circuit(true_syndrome: int) -> QuantumCircuit:
    """Prepare one of the 16 joint (W,G0,G1,G2) syndrome eigenstates."""
    if not 0 <= true_syndrome < 16:
        raise ValueError("true_syndrome must lie in [0, 15]")
    circuit = QuantumCircuit(4, 4, name=f"response_{true_syndrome:04b}")
    for qubit in range(4):
        if (true_syndrome >> qubit) & 1:
            circuit.x(qubit)
    _append_target_preparation(circuit)
    circuit.barrier()
    circuit.compose(target_preparation_circuit().inverse(), qubits=range(4), inplace=True)
    circuit.measure(range(4), range(4))
    return circuit


def coherent_error_circuit(axis: str, theta: float) -> QuantumCircuit:
    if axis.upper() not in {"X", "Z"}:
        raise ValueError("axis must be X or Z")
    error_type = "gauge_preserving_string" if axis.upper() == "X" else "gauge_violating"
    return joint_diagnostic_circuit(error_type, coherent_angle=float(theta))
