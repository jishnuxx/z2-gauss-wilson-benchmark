"""Qiskit preparation and Trotter circuits for the periodic Z2 benchmark."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import Pauli, Statevector

from .circuits import resource_metrics
from .periodic_dynamics import left_right_imbalance, operator_expectation, target_state
from .periodic_model import PeriodicZ2Model


def periodic_target_preparation_circuit(
    model: PeriodicZ2Model | None = None,
) -> QuantumCircuit:
    """Prepare the localized matter pair in the physical ``W=+1`` sector."""
    model = model or PeriodicZ2Model()
    circuit = QuantumCircuit(model.n_qubits, name="periodic_target_Wplus")
    circuit.x(model.matter_qubit(0))
    circuit.x(model.matter_qubit(1))
    control = model.link_qubit(0)
    circuit.h(control)
    for link in range(1, model.n_links):
        circuit.cx(control, model.link_qubit(link))
    for link in range(1, model.n_links):
        circuit.x(model.link_qubit(link))
    return circuit


def periodic_trotter_circuit(
    time: float,
    dt: float,
    model: PeriodicZ2Model | None = None,
    *,
    wilson_sector: int = 1,
) -> QuantumCircuit:
    """Prepare and evolve with a first-order product formula."""
    model = model or PeriodicZ2Model()
    if time < -1e-12 or dt <= 0:
        raise ValueError("time must be nonnegative and dt must be positive")
    n_steps = int(round(time / dt))
    if not np.isclose(n_steps * dt, time, atol=1e-10):
        raise ValueError("time must be an integer multiple of dt")
    if wilson_sector not in (-1, 1):
        raise ValueError("wilson_sector must be +1 or -1")
    circuit = periodic_target_preparation_circuit(model)
    if wilson_sector == -1:
        circuit.z(model.link_qubit(0))
    for _ in range(n_steps):
        for term in model.hamiltonian_terms():
            circuit.append(
                PauliEvolutionGate(
                    Pauli(term.qiskit_label),
                    time=term.coefficient * dt,
                ),
                range(model.n_qubits),
            )
    return circuit


def periodic_two_sector_circuit_comparison(
    time: float = 0.8,
    dt: float = 0.4,
    model: PeriodicZ2Model | None = None,
    *,
    include_resources: bool = True,
) -> list[dict[str, float | int | str]]:
    """Compare exact and Trotter dynamics in the two conserved W sectors."""
    model = model or PeriodicZ2Model()
    correct = target_state(model)
    wrong = model.errors["gauge_preserving_string"].matrix() @ correct
    eigenvalues, eigenvectors = np.linalg.eigh(model.hamiltonian_matrix())
    rows: list[dict[str, float | int | str]] = []
    for sector, initial in ((1, correct), (-1, wrong)):
        coefficients = eigenvectors.conj().T @ initial
        exact = eigenvectors @ (np.exp(-1j * eigenvalues * time) * coefficients)
        circuit = periodic_trotter_circuit(
            time,
            dt,
            model,
            wilson_sector=sector,
        )
        trotter = np.asarray(Statevector.from_instruction(circuit).data)
        gauss = [
            operator_expectation(trotter, check) for check in model.gauss_checks
        ]
        row: dict[str, float | int | str] = {
            "sector": sector,
            "case": "target_W_plus" if sector == 1 else "wrong_W_minus",
            "time": float(time),
            "dt": float(dt),
            "trotter_steps": int(round(time / dt)),
            "exact_imbalance": left_right_imbalance(exact, model),
            "trotter_imbalance": left_right_imbalance(trotter, model),
            "absolute_imbalance_error": abs(
                left_right_imbalance(trotter, model)
                - left_right_imbalance(exact, model)
            ),
            "state_fidelity": float(abs(np.vdot(exact, trotter)) ** 2),
            "trotter_min_gauss": min(gauss),
            "trotter_wilson": operator_expectation(trotter, model.wilson),
        }
        if include_resources:
            row.update(resource_metrics(circuit))
        rows.append(row)
    return rows


def periodic_circuit_validation(
    times: np.ndarray | list[float] | tuple[float, ...],
    *,
    dt: float = 0.1,
    model: PeriodicZ2Model | None = None,
    include_resources: bool = False,
) -> list[dict[str, float | int]]:
    """Compare ideal Qiskit Trotter statevectors with dense exact evolution."""
    model = model or PeriodicZ2Model()
    times_array = np.asarray(times, dtype=float)
    if times_array.ndim != 1 or times_array.size == 0:
        raise ValueError("times must be a nonempty one-dimensional sequence")
    if dt <= 0 or np.any(times_array < 0) or np.any(~np.isfinite(times_array)):
        raise ValueError("dt must be positive and times finite and nonnegative")

    initial = target_state(model)
    eigenvalues, eigenvectors = np.linalg.eigh(model.hamiltonian_matrix())
    coefficients = eigenvectors.conj().T @ initial
    rows: list[dict[str, float | int]] = []
    for time in times_array:
        exact = eigenvectors @ (np.exp(-1j * eigenvalues * time) * coefficients)
        circuit = periodic_trotter_circuit(float(time), dt, model)
        trotter = np.asarray(Statevector.from_instruction(circuit).data)
        exact_observable = left_right_imbalance(exact, model)
        trotter_observable = left_right_imbalance(trotter, model)
        gauss = [
            operator_expectation(trotter, check) for check in model.gauss_checks
        ]
        row: dict[str, float | int] = {
            "time": float(time),
            "dt": float(dt),
            "trotter_steps": int(round(float(time) / dt)),
            "state_fidelity": float(abs(np.vdot(exact, trotter)) ** 2),
            "exact_imbalance": exact_observable,
            "trotter_imbalance": trotter_observable,
            "absolute_imbalance_error": abs(trotter_observable - exact_observable),
            "trotter_min_gauss": min(gauss),
            "trotter_wilson": operator_expectation(trotter, model.wilson),
            "trotter_norm_error": abs(float(np.vdot(trotter, trotter).real) - 1.0),
        }
        if include_resources:
            row.update(resource_metrics(circuit))
        rows.append(row)
    return rows


def write_periodic_circuit_validation_csv(
    rows: list[dict[str, float | int]],
    path: Path = Path("results/processed/periodic_trotter_validation.csv"),
) -> Path:
    if not rows:
        raise ValueError("cannot write an empty circuit validation")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path
