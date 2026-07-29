"""Hamiltonian and qubit layout for the open-boundary Z2 model."""

from __future__ import annotations

from dataclasses import dataclass

from .pauli import PauliTerm, sum_matrix, word


@dataclass(frozen=True)
class Z2Model:
    """Open chain with matter qubits followed by link qubits.

    The link basis is Hadamard-rotated relative to the common electric-X
    convention.  Consequently Gauss operators and all measured observables are
    diagonal in the computational basis.
    """

    n_sites: int
    mass: float = 0.5
    electric: float = 0.35
    hopping: float = 1.0

    def __post_init__(self) -> None:
        if self.n_sites < 2:
            raise ValueError("n_sites must be at least 2")

    @property
    def n_links(self) -> int:
        return self.n_sites - 1

    @property
    def n_qubits(self) -> int:
        return 2 * self.n_sites - 1

    def matter_qubit(self, site: int) -> int:
        if not 0 <= site < self.n_sites:
            raise IndexError(site)
        return site

    def link_qubit(self, link: int) -> int:
        if not 0 <= link < self.n_links:
            raise IndexError(link)
        return self.n_sites + link

    def hamiltonian_terms(self) -> list[PauliTerm]:
        """Return H as mass, electric, and gauge-matter Pauli terms.

        H = -(m/2) sum_i (-1)^i Z_i - g sum_l Z_l
            -(J/2) sum_i (X_i X_l X_{i+1} + Y_i X_l Y_{i+1}).

        An omitted scalar mass offset has no effect on dynamics.
        """
        terms: list[PauliTerm] = []
        for site in range(self.n_sites):
            coefficient = -0.5 * self.mass * ((-1) ** site)
            terms.append(
                PauliTerm(coefficient, word(self.n_qubits, {site: "Z"}), f"mass_{site}")
            )
        for link in range(self.n_links):
            q_link = self.link_qubit(link)
            terms.append(
                PauliTerm(-self.electric, word(self.n_qubits, {q_link: "Z"}), f"electric_{link}")
            )
            left, right = link, link + 1
            terms.append(
                PauliTerm(
                    -0.5 * self.hopping,
                    word(self.n_qubits, {left: "X", q_link: "X", right: "X"}),
                    f"hop_x_{link}",
                )
            )
            terms.append(
                PauliTerm(
                    -0.5 * self.hopping,
                    word(self.n_qubits, {left: "Y", q_link: "X", right: "Y"}),
                    f"hop_y_{link}",
                )
            )
        return terms

    def hamiltonian_matrix(self):
        return sum_matrix(self.hamiltonian_terms(), self.n_qubits)

