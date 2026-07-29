"""Exhaustive single-qubit Pauli-error audit for the periodic benchmark."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import numpy as np

from .pauli import PauliTerm, word
from .periodic_dynamics import left_right_imbalance, target_state
from .periodic_model import PeriodicZ2Model, pauli_commutes


CLASS_ORDER = (
    "gauss_only",
    "wilson_only",
    "gauss_and_wilson",
    "undetected_by_gauss_and_wilson",
)


def single_qubit_pauli_errors(model: PeriodicZ2Model):
    """Yield metadata and operators for all 24 weight-one Pauli errors."""
    for qubit in range(model.n_qubits):
        subsystem = "matter" if qubit < model.n_sites else "link"
        local_index = qubit if subsystem == "matter" else qubit - model.n_sites
        for pauli in ("X", "Y", "Z"):
            yield (
                qubit,
                subsystem,
                local_index,
                pauli,
                PauliTerm(
                    1.0,
                    word(model.n_qubits, {qubit: pauli}),
                    f"{pauli}_{subsystem[0]}{local_index}",
                ),
            )


def _diagnostic_class(gauss_detected: bool, wilson_detected: bool) -> str:
    if gauss_detected and wilson_detected:
        return "gauss_and_wilson"
    if gauss_detected:
        return "gauss_only"
    if wilson_detected:
        return "wilson_only"
    return "undetected_by_gauss_and_wilson"


def single_qubit_pauli_error_sweep(
    times: np.ndarray | list[float] | tuple[float, ...],
    model: PeriodicZ2Model | None = None,
) -> list[dict[str, object]]:
    """Classify and evolve all 24 weight-one Pauli errors applied at ``t=0``."""
    model = model or PeriodicZ2Model()
    times_array = np.asarray(times, dtype=float)
    if times_array.ndim != 1 or times_array.size == 0:
        raise ValueError("times must be a nonempty one-dimensional sequence")
    if not np.all(np.isfinite(times_array)) or np.any(times_array < 0):
        raise ValueError("times must be finite and nonnegative")

    initial = target_state(model)
    eigenvalues, eigenvectors = np.linalg.eigh(model.hamiltonian_matrix())

    def trajectory(state: np.ndarray) -> np.ndarray:
        coefficients = eigenvectors.conj().T @ state
        return np.asarray(
            [
                left_right_imbalance(
                    eigenvectors @ (np.exp(-1j * eigenvalues * time) * coefficients),
                    model,
                )
                for time in times_array
            ]
        )

    ideal = trajectory(initial)
    rows: list[dict[str, object]] = []
    for qubit, subsystem, local_index, pauli, error in single_qubit_pauli_errors(model):
            gauss_bits = tuple(
                int(not pauli_commutes(error, check)) for check in model.gauss_checks
            )
            gauss_detected = any(gauss_bits)
            wilson_detected = not pauli_commutes(error, model.wilson)
            errored_state = error.matrix() @ initial
            errored = trajectory(errored_state)
            absolute_error = np.abs(errored - ideal)
            maximum = int(np.argmax(absolute_error))
            rows.append(
                {
                    "qubit": qubit,
                    "subsystem": subsystem,
                    "local_index": local_index,
                    "pauli": pauli,
                    "operator": error.qiskit_label,
                    "gauss_syndrome": "".join(str(bit) for bit in gauss_bits),
                    "gauss_detected": gauss_detected,
                    "wilson_flipped": wilson_detected,
                    "wilson_sector_after_error": -1 if wilson_detected else 1,
                    "diagnostic_class": _diagnostic_class(
                        gauss_detected, wilson_detected
                    ),
                    "initial_state_fidelity_after_error": float(
                        abs(np.vdot(initial, errored_state)) ** 2
                    ),
                    "max_abs_imbalance_error": float(absolute_error[maximum]),
                    "time_of_max_error": float(times_array[maximum]),
                    "mean_abs_imbalance_error": float(absolute_error.mean()),
                }
            )
    return rows


def diagnostic_class_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts = Counter(str(row["diagnostic_class"]) for row in rows)
    return {name: counts.get(name, 0) for name in CLASS_ORDER}


def write_periodic_error_sweep_csv(
    rows: list[dict[str, object]],
    path: Path = Path("results/processed/periodic_single_qubit_error_sweep.csv"),
) -> Path:
    if not rows:
        raise ValueError("cannot write an empty error sweep")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path
