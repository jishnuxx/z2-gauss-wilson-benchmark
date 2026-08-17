"""Gauss-law operators, physical states, and bitstring classification."""

from __future__ import annotations

import numpy as np

from .model import Z2Model
from .pauli import PauliTerm, word


def gauss_terms(model: Z2Model) -> list[PauliTerm]:
    """Return local G_i with fixed +1 boundary electric fields."""
    result = []
    for site in range(model.n_sites):
        operators = {model.matter_qubit(site): "Z"}
        if site > 0:
            operators[model.link_qubit(site - 1)] = "Z"
        if site < model.n_sites - 1:
            operators[model.link_qubit(site)] = "Z"
        result.append(PauliTerm(1.0, word(model.n_qubits, operators), f"G_{site}"))
    return result


def physical_bits_from_matter(model: Z2Model, matter_bits: list[int]) -> list[int]:
    """Solve G_i=+1 for links given an even-parity matter configuration."""
    if len(matter_bits) != model.n_sites or any(bit not in (0, 1) for bit in matter_bits):
        raise ValueError("matter_bits must contain one binary value per site")
    if sum(matter_bits) % 2:
        raise ValueError("fixed +1 boundaries require even matter parity")
    link_bits: list[int] = []
    running_z = 1
    for site in range(model.n_links):
        running_z *= 1 if matter_bits[site] == 0 else -1
        link_bits.append(0 if running_z == 1 else 1)
    bits = list(matter_bits) + link_bits
    if not is_physical(bits, model):
        raise RuntimeError("internal Gauss-law state construction failure")
    return bits


def localized_imbalance_bits(model: Z2Model) -> list[int]:
    """Return a physical state with two adjacent occupied matter sites."""
    matter = [0] * model.n_sites
    matter[0] = matter[1] = 1
    return physical_bits_from_matter(model, matter)


def gauss_eigenvalues(bits: list[int] | tuple[int, ...], model: Z2Model) -> tuple[int, ...]:
    """Classify a canonical q0..qN-1 computational-basis bitstring."""
    if len(bits) != model.n_qubits or any(bit not in (0, 1) for bit in bits):
        raise ValueError("bits must contain one binary value per qubit")
    z = [1 if bit == 0 else -1 for bit in bits]
    values = []
    for site in range(model.n_sites):
        value = z[model.matter_qubit(site)]
        if site > 0:
            value *= z[model.link_qubit(site - 1)]
        if site < model.n_sites - 1:
            value *= z[model.link_qubit(site)]
        values.append(value)
    return tuple(values)


def violation_pattern(bits: list[int] | tuple[int, ...], model: Z2Model) -> str:
    """Return a 0/1 string over sites, where 1 denotes G_i=-1."""
    return "".join("0" if value == 1 else "1" for value in gauss_eigenvalues(bits, model))


def n_violations(bits: list[int] | tuple[int, ...], model: Z2Model) -> int:
    return sum(value == -1 for value in gauss_eigenvalues(bits, model))


def is_physical(bits: list[int] | tuple[int, ...], model: Z2Model) -> bool:
    return n_violations(bits, model) == 0


def basis_state(bits: list[int] | tuple[int, ...]) -> np.ndarray:
    """Return a Qiskit-compatible little-endian basis statevector."""
    index = sum(int(bit) << qubit for qubit, bit in enumerate(bits))
    state = np.zeros(2 ** len(bits), dtype=complex)
    state[index] = 1.0
    return state


def commutator_norms(model: Z2Model) -> list[float]:
    """Return Frobenius norms of [H,G_i]."""
    hamiltonian = model.hamiltonian_matrix()
    return [
        float(np.linalg.norm(hamiltonian @ term.matrix() - term.matrix() @ hamiltonian))
        for term in gauss_terms(model)
    ]

