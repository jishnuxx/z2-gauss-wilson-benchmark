"""Four-site periodic Z2 matter-gauge model with a conserved Wilson sector.

Qubits ``q0..q3`` encode staggered matter and ``q4..q7`` encode the four
periodic links.  Link Pauli operators use the same Hadamard-rotated convention
as :mod:`z2lgt.model`.

The electric-link term is deliberately omitted.  In this special limit the
noncontractible Wilson operator ``W = prod_l X_l`` commutes with the
Hamiltonian and can be used as an independently known sector check.  Adding a
term proportional to ``Z_l`` would destroy that conservation law.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .pauli import PauliTerm, sum_matrix, word


@dataclass(frozen=True)
class PeriodicZ2Model:
    """Minimal even periodic ring for observable-aware sector verification."""

    n_sites: int = 4
    mass: float = 0.5
    hopping: float = 1.0

    def __post_init__(self) -> None:
        if self.n_sites != 4:
            raise ValueError("the minimal periodic benchmark has exactly four sites")

    @property
    def n_links(self) -> int:
        return self.n_sites

    @property
    def n_qubits(self) -> int:
        return self.n_sites + self.n_links

    def matter_qubit(self, site: int) -> int:
        if not 0 <= site < self.n_sites:
            raise IndexError(site)
        return site

    def link_qubit(self, link: int) -> int:
        if not 0 <= link < self.n_links:
            raise IndexError(link)
        return self.n_sites + link

    @property
    def gauss_checks(self) -> tuple[PauliTerm, ...]:
        checks = []
        for site in range(self.n_sites):
            checks.append(
                PauliTerm(
                    1.0,
                    word(
                        self.n_qubits,
                        {
                            self.matter_qubit(site): "Z",
                            self.link_qubit((site - 1) % self.n_links): "Z",
                            self.link_qubit(site): "Z",
                        },
                    ),
                    f"G{site}",
                )
            )
        return tuple(checks)

    @property
    def wilson(self) -> PauliTerm:
        return PauliTerm(
            1.0,
            word(
                self.n_qubits,
                {self.link_qubit(link): "X" for link in range(self.n_links)},
            ),
            "W",
        )

    @property
    def errors(self) -> dict[str, PauliTerm]:
        return {
            "no_error": PauliTerm(1.0, word(self.n_qubits, {}), "I"),
            "gauge_violating": PauliTerm(
                1.0,
                word(self.n_qubits, {self.matter_qubit(0): "X"}),
                "X_m0",
            ),
            "gauge_preserving_string": PauliTerm(
                1.0,
                word(self.n_qubits, {self.link_qubit(0): "Z"}),
                "Z_l0",
            ),
        }

    def hamiltonian_terms(self) -> list[PauliTerm]:
        """Return periodic mass and gauge-matter hopping terms.

        The usual rotated-basis electric term ``-g sum_l Z_l`` is absent so
        that the global Wilson loop is an exact conserved quantity.
        """
        terms: list[PauliTerm] = []
        for site in range(self.n_sites):
            terms.append(
                PauliTerm(
                    -0.5 * self.mass * ((-1) ** site),
                    word(self.n_qubits, {self.matter_qubit(site): "Z"}),
                    f"mass_{site}",
                )
            )
        for link in range(self.n_links):
            left = link
            right = (link + 1) % self.n_sites
            gauge = self.link_qubit(link)
            terms.extend(
                [
                    PauliTerm(
                        -0.5 * self.hopping,
                        word(
                            self.n_qubits,
                            {
                                self.matter_qubit(left): "X",
                                gauge: "X",
                                self.matter_qubit(right): "X",
                            },
                        ),
                        f"hop_x_{link}",
                    ),
                    PauliTerm(
                        -0.5 * self.hopping,
                        word(
                            self.n_qubits,
                            {
                                self.matter_qubit(left): "Y",
                                gauge: "X",
                                self.matter_qubit(right): "Y",
                            },
                        ),
                        f"hop_y_{link}",
                    ),
                ]
            )
        return terms

    def hamiltonian_matrix(self) -> np.ndarray:
        return sum_matrix(self.hamiltonian_terms(), self.n_qubits)

    def metadata(self) -> dict[str, object]:
        return {
            "name": "four_site_periodic_z2_matter_ring",
            "n_qubits": self.n_qubits,
            "qubit_order": "matter q0..q3, periodic links q4..q7",
            "gauss_checks": [check.qiskit_label for check in self.gauss_checks],
            "wilson": self.wilson.qiskit_label,
            "electric_link_term": "omitted; coefficient fixed to zero",
            "separate_scientific_observable": "time-dependent charge imbalance",
        }


def pauli_commutes(left: PauliTerm, right: PauliTerm) -> bool:
    """Return whether two Pauli words commute."""
    anticommuting_sites = sum(
        a != "I" and b != "I" and a != b
        for a, b in zip(left.word, right.word, strict=True)
    )
    return anticommuting_sites % 2 == 0


def matrix_commutator_norm(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.linalg.norm(left @ right - right @ left))


def periodic_algebra_report(model: PeriodicZ2Model | None = None) -> dict[str, object]:
    """Return a dense-matrix verification of the proposed conserved sector."""
    model = model or PeriodicZ2Model()
    hamiltonian = model.hamiltonian_matrix()
    gauss_norms = {
        check.name: matrix_commutator_norm(hamiltonian, check.matrix())
        for check in model.gauss_checks
    }
    wilson_norm = matrix_commutator_norm(hamiltonian, model.wilson.matrix())
    gauge_error = model.errors["gauge_violating"]
    string_error = model.errors["gauge_preserving_string"]
    gauge_error_relations = {
        check.name: "commutes" if pauli_commutes(gauge_error, check) else "anticommutes"
        for check in model.gauss_checks
    }
    string_error_relations = {
        check.name: "commutes" if pauli_commutes(string_error, check) else "anticommutes"
        for check in model.gauss_checks
    }
    report = {
        "model": model.metadata(),
        "hamiltonian_gauss_commutator_norms": gauss_norms,
        "hamiltonian_wilson_commutator_norm": wilson_norm,
        "errors": {
            "gauge_violating": {
                "operator": gauge_error.qiskit_label,
                "gauss_relations": gauge_error_relations,
            },
            "gauge_preserving_string": {
                "operator": string_error.qiskit_label,
                "gauss_relations": string_error_relations,
                "wilson_relation": (
                    "commutes"
                    if pauli_commutes(string_error, model.wilson)
                    else "anticommutes"
                ),
            },
        },
    }
    report["claims_verified"] = {
        "hamiltonian_preserves_all_gauss_checks": all(
            np.isclose(value, 0.0) for value in gauss_norms.values()
        ),
        "hamiltonian_preserves_wilson_sector": bool(np.isclose(wilson_norm, 0.0)),
        "gauge_error_flips_at_least_one_gauss_check": any(
            relation == "anticommutes" for relation in gauge_error_relations.values()
        ),
        "string_error_preserves_all_gauss_checks": all(
            relation == "commutes" for relation in string_error_relations.values()
        ),
        "string_error_flips_wilson_sector": not pauli_commutes(
            string_error, model.wilson
        ),
    }
    return report
