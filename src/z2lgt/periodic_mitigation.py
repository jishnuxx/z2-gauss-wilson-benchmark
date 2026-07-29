"""Exact single-fault ensemble for Gauss- versus Wilson-aware mitigation."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .periodic_dynamics import left_right_imbalance, target_state
from .periodic_error_sweep import single_qubit_pauli_errors
from .periodic_model import PeriodicZ2Model, pauli_commutes


def exact_single_fault_mitigation(
    observation_times: np.ndarray | list[float] | tuple[float, ...],
    *,
    total_error_probability: float = 0.2,
    n_injection_times: int = 8,
    model: PeriodicZ2Model | None = None,
) -> list[dict[str, float]]:
    """Return exact raw and post-selected trajectories for one-fault noise.

    The total probability that one Pauli fault has occurred by the final time
    is ``total_error_probability``.  Fault opportunities are the midpoints of
    ``n_injection_times`` equal time intervals.  Each of the 24 single-qubit
    Pauli errors has equal conditional weight.  Multiple faults, readout error,
    and finite-shot noise are intentionally excluded.
    """
    model = model or PeriodicZ2Model()
    times = np.asarray(observation_times, dtype=float)
    if times.ndim != 1 or times.size < 2 or np.any(np.diff(times) <= 0):
        raise ValueError("observation_times must be strictly increasing")
    if times[0] != 0.0 or times[-1] <= 0 or np.any(~np.isfinite(times)):
        raise ValueError("observation_times must run from zero to a finite positive time")
    if not 0.0 <= total_error_probability <= 1.0:
        raise ValueError("total_error_probability must lie in [0, 1]")
    if n_injection_times < 1:
        raise ValueError("n_injection_times must be positive")

    final_time = float(times[-1])
    interval = final_time / n_injection_times
    injection_times = (np.arange(n_injection_times, dtype=float) + 0.5) * interval
    per_fault_weight = total_error_probability / (n_injection_times * 24)

    initial = target_state(model)
    eigenvalues, eigenvectors = np.linalg.eigh(model.hamiltonian_matrix())

    def evolve(state: np.ndarray, duration: float) -> np.ndarray:
        coefficients = eigenvectors.conj().T @ state
        return eigenvectors @ (np.exp(-1j * eigenvalues * duration) * coefficients)

    errors = []
    for _, subsystem, local_index, pauli, error in single_qubit_pauli_errors(model):
        gauss_detected = any(
            not pauli_commutes(error, check) for check in model.gauss_checks
        )
        wilson_detected = not pauli_commutes(error, model.wilson)
        errors.append(
            {
                "name": f"{pauli}_{subsystem[0]}{local_index}",
                "operator": error,
                "gauss_detected": gauss_detected,
                "wilson_detected": wilson_detected,
            }
        )

    ideal_states = [evolve(initial, float(time)) for time in times]
    ideal_values = [left_right_imbalance(state, model) for state in ideal_states]
    states_before_fault = {
        float(injection_time): evolve(initial, float(injection_time))
        for injection_time in injection_times
    }

    rows: list[dict[str, float]] = []
    tolerance = 1e-12
    for time, ideal_value in zip(times, ideal_values, strict=True):
        eligible_times = [
            float(injection_time)
            for injection_time in injection_times
            if injection_time <= time + tolerance
        ]
        accumulated_fault_probability = (
            len(eligible_times) * 24 * per_fault_weight
        )
        no_fault_probability = 1.0 - accumulated_fault_probability

        raw_numerator = no_fault_probability * ideal_value
        gauss_numerator = no_fault_probability * ideal_value
        joint_numerator = no_fault_probability * ideal_value
        gauss_acceptance = no_fault_probability
        joint_acceptance = no_fault_probability

        for injection_time in eligible_times:
            state_before_fault = states_before_fault[injection_time]
            for error in errors:
                state_after_fault = error["operator"].matrix() @ state_before_fault
                state_at_observation = evolve(
                    state_after_fault,
                    float(time - injection_time),
                )
                value = left_right_imbalance(state_at_observation, model)
                raw_numerator += per_fault_weight * value
                if not error["gauss_detected"]:
                    gauss_acceptance += per_fault_weight
                    gauss_numerator += per_fault_weight * value
                    if not error["wilson_detected"]:
                        joint_acceptance += per_fault_weight
                        joint_numerator += per_fault_weight * value

        raw_value = raw_numerator
        gauss_value = gauss_numerator / gauss_acceptance
        joint_value = joint_numerator / joint_acceptance
        rows.append(
            {
                "time": float(time),
                "ideal_imbalance": float(ideal_value),
                "raw_imbalance": float(raw_value),
                "gauss_only_imbalance": float(gauss_value),
                "gauss_plus_wilson_imbalance": float(joint_value),
                "raw_abs_error": abs(float(raw_value - ideal_value)),
                "gauss_only_abs_error": abs(float(gauss_value - ideal_value)),
                "gauss_plus_wilson_abs_error": abs(float(joint_value - ideal_value)),
                "raw_acceptance": 1.0,
                "gauss_only_acceptance": float(gauss_acceptance),
                "gauss_plus_wilson_acceptance": float(joint_acceptance),
                "cumulative_fault_probability": float(accumulated_fault_probability),
            }
        )
    return rows


def write_periodic_mitigation_csv(
    rows: list[dict[str, float]],
    path: Path = Path("results/processed/periodic_exact_mitigation.csv"),
) -> Path:
    if not rows:
        raise ValueError("cannot write an empty mitigation result")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path
