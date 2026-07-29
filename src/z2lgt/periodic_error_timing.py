"""Mid-evolution Pauli-error timing audit for the periodic benchmark."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .periodic_dynamics import left_right_imbalance, target_state
from .periodic_error_sweep import _diagnostic_class, single_qubit_pauli_errors
from .periodic_model import PeriodicZ2Model, pauli_commutes


def timed_single_qubit_error_sweep(
    observation_times: np.ndarray | list[float] | tuple[float, ...],
    injection_times: np.ndarray | list[float] | tuple[float, ...],
    model: PeriodicZ2Model | None = None,
) -> list[dict[str, object]]:
    """Apply every weight-one Pauli at each requested evolution time."""
    model = model or PeriodicZ2Model()
    observation = np.asarray(observation_times, dtype=float)
    injection = np.asarray(injection_times, dtype=float)
    for name, values in (("observation_times", observation), ("injection_times", injection)):
        if values.ndim != 1 or values.size == 0:
            raise ValueError(f"{name} must be a nonempty one-dimensional sequence")
        if not np.all(np.isfinite(values)) or np.any(values < 0):
            raise ValueError(f"{name} must be finite and nonnegative")
    if np.any(np.diff(observation) <= 0) or np.any(np.diff(injection) <= 0):
        raise ValueError("observation and injection times must be strictly increasing")
    if injection[-1] > observation[-1]:
        raise ValueError("injection times cannot exceed the last observation time")

    initial = target_state(model)
    eigenvalues, eigenvectors = np.linalg.eigh(model.hamiltonian_matrix())

    def evolve(state: np.ndarray, duration: float) -> np.ndarray:
        coefficients = eigenvectors.conj().T @ state
        return eigenvectors @ (np.exp(-1j * eigenvalues * duration) * coefficients)

    ideal_states = [evolve(initial, float(time)) for time in observation]
    ideal_observable = np.asarray(
        [left_right_imbalance(state, model) for state in ideal_states]
    )

    rows: list[dict[str, object]] = []
    tolerance = 1e-12
    for injection_time in injection:
        state_before_error = evolve(initial, float(injection_time))
        observed_indices = np.flatnonzero(observation >= injection_time - tolerance)
        if observed_indices.size == 0:
            raise ValueError("each injection must have a subsequent observation")
        for qubit, subsystem, local_index, pauli, error in single_qubit_pauli_errors(model):
            state_after_error = error.matrix() @ state_before_error
            gauss_bits = tuple(
                int(not pauli_commutes(error, check)) for check in model.gauss_checks
            )
            gauss_detected = any(gauss_bits)
            wilson_flipped = not pauli_commutes(error, model.wilson)

            absolute_errors = []
            for index in observed_indices:
                errored_state = evolve(
                    state_after_error,
                    float(observation[index] - injection_time),
                )
                errored_observable = left_right_imbalance(errored_state, model)
                absolute_errors.append(abs(errored_observable - ideal_observable[index]))
            absolute_errors_array = np.asarray(absolute_errors)
            maximum = int(np.argmax(absolute_errors_array))
            rows.append(
                {
                    "injection_time": float(injection_time),
                    "qubit": qubit,
                    "subsystem": subsystem,
                    "local_index": local_index,
                    "pauli": pauli,
                    "operator": error.qiskit_label,
                    "gauss_syndrome": "".join(str(bit) for bit in gauss_bits),
                    "gauss_detected": gauss_detected,
                    "wilson_flipped": wilson_flipped,
                    "diagnostic_class": _diagnostic_class(
                        gauss_detected, wilson_flipped
                    ),
                    "state_fidelity_immediately_after_error": float(
                        abs(np.vdot(state_before_error, state_after_error)) ** 2
                    ),
                    "max_abs_imbalance_error_after_injection": float(
                        absolute_errors_array[maximum]
                    ),
                    "time_of_max_error": float(observation[observed_indices[maximum]]),
                    "final_abs_imbalance_error": float(absolute_errors_array[-1]),
                }
            )
    return rows


def write_periodic_error_timing_csv(
    rows: list[dict[str, object]],
    path: Path = Path("results/processed/periodic_error_timing_sweep.csv"),
) -> Path:
    if not rows:
        raise ValueError("cannot write an empty timing sweep")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path
