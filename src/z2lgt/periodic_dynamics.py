"""Exact dynamics for the conserved-sector periodic Z2 benchmark."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .gauss import basis_state
from .periodic_model import PeriodicZ2Model


def target_state(model: PeriodicZ2Model | None = None) -> np.ndarray:
    """Return a physical localized-pair state in the ``W=+1`` sector.

    Matter occupations are ``(1,1,0,0)``.  The two link configurations are
    complementary solutions of all four Gauss constraints; their symmetric
    superposition is the ``+1`` eigenstate of the global Wilson loop.
    """
    model = model or PeriodicZ2Model()
    if model.n_sites != 4:
        raise ValueError("the target state is defined for the four-site benchmark")
    branch_a = basis_state((1, 1, 0, 0, 0, 1, 1, 1))
    branch_b = basis_state((1, 1, 0, 0, 1, 0, 0, 0))
    return (branch_a + branch_b) / np.sqrt(2.0)


def operator_expectation(state: np.ndarray, operator) -> float:
    state = np.asarray(state, dtype=complex)
    return float(np.real(np.vdot(state, operator.matrix() @ state)))


def matter_occupation(
    state: np.ndarray,
    site: int,
    model: PeriodicZ2Model | None = None,
) -> float:
    """Return the probability that matter site ``site`` is occupied."""
    model = model or PeriodicZ2Model()
    qubit = model.matter_qubit(site)
    probabilities = np.abs(np.asarray(state, dtype=complex)) ** 2
    indices = np.arange(probabilities.size)
    return float(probabilities[((indices >> qubit) & 1) == 1].sum())


def left_right_imbalance(
    state: np.ndarray,
    model: PeriodicZ2Model | None = None,
) -> float:
    """Return ``(n0+n1-n2-n3)/2`` for the four-site ring."""
    model = model or PeriodicZ2Model()
    occupations = [matter_occupation(state, site, model) for site in range(4)]
    return float((occupations[0] + occupations[1] - occupations[2] - occupations[3]) / 2)


def _evolve_from_eigendecomposition(
    eigenvalues: np.ndarray,
    eigenvectors: np.ndarray,
    coefficients: np.ndarray,
    time: float,
) -> np.ndarray:
    return eigenvectors @ (np.exp(-1j * eigenvalues * time) * coefficients)


def exact_trajectories(
    times: np.ndarray | list[float] | tuple[float, ...],
    model: PeriodicZ2Model | None = None,
) -> list[dict[str, float]]:
    """Compare correct- and wrong-Wilson-sector matter dynamics."""
    model = model or PeriodicZ2Model()
    times_array = np.asarray(times, dtype=float)
    if times_array.ndim != 1 or times_array.size == 0:
        raise ValueError("times must be a nonempty one-dimensional sequence")
    if not np.all(np.isfinite(times_array)) or np.any(times_array < 0):
        raise ValueError("times must be finite and nonnegative")

    correct = target_state(model)
    wrong = model.errors["gauge_preserving_string"].matrix() @ correct
    eigenvalues, eigenvectors = np.linalg.eigh(model.hamiltonian_matrix())
    correct_coefficients = eigenvectors.conj().T @ correct
    wrong_coefficients = eigenvectors.conj().T @ wrong

    rows = []
    for time in times_array:
        correct_state = _evolve_from_eigendecomposition(
            eigenvalues, eigenvectors, correct_coefficients, float(time)
        )
        wrong_state = _evolve_from_eigendecomposition(
            eigenvalues, eigenvectors, wrong_coefficients, float(time)
        )
        correct_imbalance = left_right_imbalance(correct_state, model)
        wrong_imbalance = left_right_imbalance(wrong_state, model)
        correct_gauss = [
            operator_expectation(correct_state, check) for check in model.gauss_checks
        ]
        wrong_gauss = [
            operator_expectation(wrong_state, check) for check in model.gauss_checks
        ]
        rows.append(
            {
                "time": float(time),
                "ideal_imbalance": correct_imbalance,
                "wrong_sector_imbalance": wrong_imbalance,
                "absolute_difference": abs(correct_imbalance - wrong_imbalance),
                "ideal_min_gauss": min(correct_gauss),
                "wrong_sector_min_gauss": min(wrong_gauss),
                "ideal_wilson": operator_expectation(correct_state, model.wilson),
                "wrong_sector_wilson": operator_expectation(wrong_state, model.wilson),
                "ideal_norm_error": abs(float(np.vdot(correct_state, correct_state).real) - 1.0),
                "wrong_sector_norm_error": abs(float(np.vdot(wrong_state, wrong_state).real) - 1.0),
            }
        )
    return rows


def write_periodic_dynamics_csv(
    rows: list[dict[str, float]],
    path: Path = Path("results/processed/periodic_dynamics_ideal.csv"),
) -> Path:
    if not rows:
        raise ValueError("cannot write an empty trajectory")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path
