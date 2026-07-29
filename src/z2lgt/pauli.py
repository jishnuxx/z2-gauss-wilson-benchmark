"""Minimal Pauli-string utilities shared by ED and Qiskit circuits."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_MATRICES = {
    "I": np.eye(2, dtype=complex),
    "X": np.array([[0, 1], [1, 0]], dtype=complex),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "Z": np.diag([1, -1]).astype(complex),
}


@dataclass(frozen=True)
class PauliTerm:
    """Coefficient times a Pauli word, with ``word[q]`` acting on qubit q."""

    coefficient: float
    word: tuple[str, ...]
    name: str = ""

    def matrix(self) -> np.ndarray:
        """Return a little-endian matrix compatible with Qiskit's state order."""
        result = np.array([[1.0 + 0.0j]])
        for symbol in reversed(self.word):
            result = np.kron(result, _MATRICES[symbol])
        return self.coefficient * result

    @property
    def qiskit_label(self) -> str:
        """Return Qiskit's big-endian Pauli label."""
        return "".join(reversed(self.word))


def word(n_qubits: int, operators: dict[int, str]) -> tuple[str, ...]:
    """Construct a Pauli word from a qubit-to-symbol mapping."""
    symbols = ["I"] * n_qubits
    for qubit, symbol in operators.items():
        if symbol not in _MATRICES:
            raise ValueError(f"unsupported Pauli symbol: {symbol}")
        symbols[qubit] = symbol
    return tuple(symbols)


def sum_matrix(terms: list[PauliTerm], n_qubits: int) -> np.ndarray:
    """Build a dense matrix for a list of Pauli terms."""
    matrix = np.zeros((2**n_qubits, 2**n_qubits), dtype=complex)
    for term in terms:
        matrix += term.matrix()
    return matrix

