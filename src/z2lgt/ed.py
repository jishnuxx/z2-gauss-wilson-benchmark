"""Exact diagonalization and real-time evolution."""

from __future__ import annotations

import numpy as np

from .gauss import basis_state
from .model import Z2Model
from .observables import all_state_expectations


def evolve(model: Z2Model, initial_bits: list[int], times: np.ndarray) -> list[np.ndarray]:
    """Evolve by diagonalizing the dense Hermitian Hamiltonian once."""
    hamiltonian = model.hamiltonian_matrix()
    eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian)
    initial = basis_state(initial_bits)
    coefficients = eigenvectors.conj().T @ initial
    states = []
    for time in times:
        state = eigenvectors @ (np.exp(-1j * eigenvalues * time) * coefficients)
        states.append(state)
    return states


def benchmark(model: Z2Model, initial_bits: list[int], times: np.ndarray) -> list[dict[str, float]]:
    rows = []
    for time, state in zip(times, evolve(model, initial_bits, times), strict=True):
        row = {"time": float(time), "norm": float(np.vdot(state, state).real)}
        row.update(all_state_expectations(state, model))
        rows.append(row)
    return rows
