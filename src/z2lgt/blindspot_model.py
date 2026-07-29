"""Exact four-link Z2 model for the Gauss-law diagnostic blind spot.

The data qubits are links of a periodic square, ordered around the loop.  The
four vertex generators are ``G_s = X_s X_(s+1 mod 4)`` and the Wilson loop is
``W = Z_0 Z_1 Z_2 Z_3``.  One Gauss generator is redundant, as expected on a
closed connected graph.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .pauli import PauliTerm, word


@dataclass(frozen=True)
class BlindSpotModel:
    """Minimal four-data-qubit Z2 stabilizer benchmark."""

    n_data_qubits: int = 4

    def __post_init__(self) -> None:
        if self.n_data_qubits != 4:
            raise ValueError("the minimal blind-spot model has exactly four data qubits")

    @property
    def gauss_checks(self) -> tuple[PauliTerm, ...]:
        return tuple(
            PauliTerm(
                1.0,
                word(4, {site: "X", (site + 1) % 4: "X"}),
                f"G{site}",
            )
            for site in range(4)
        )

    @property
    def independent_gauss_checks(self) -> tuple[PauliTerm, ...]:
        return self.gauss_checks[:3]

    @property
    def wilson(self) -> PauliTerm:
        return PauliTerm(1.0, word(4, {q: "Z" for q in range(4)}), "W")

    @property
    def errors(self) -> dict[str, PauliTerm]:
        return {
            "no_error": PauliTerm(1.0, word(4, {}), "I"),
            "gauge_violating": PauliTerm(1.0, word(4, {0: "Z"}), "Z0"),
            "gauge_preserving_string": PauliTerm(1.0, word(4, {0: "X"}), "X0"),
        }

    def target_statevector(self) -> np.ndarray:
        """Return the unique simultaneous +1 state of G0,G1,G2,W.

        It is the equal superposition of the eight even-parity computational
        basis states.  Qubit zero is the least-significant statevector bit.
        """
        state = np.zeros(16, dtype=complex)
        for basis in range(16):
            if basis.bit_count() % 2 == 0:
                state[basis] = 1 / np.sqrt(8)
        return state

    def apply_error(self, error_type: str, state: np.ndarray | None = None) -> np.ndarray:
        if error_type not in self.errors:
            raise ValueError(f"unknown error type: {error_type}")
        source = self.target_statevector() if state is None else np.asarray(state)
        return self.errors[error_type].matrix() @ source

    def expectations(self, state: np.ndarray) -> dict[str, float]:
        state = np.asarray(state)
        operators = (*self.gauss_checks, self.wilson)
        return {
            operator.name: float(np.real(np.vdot(state, operator.matrix() @ state)))
            for operator in operators
        }

    def metadata(self) -> dict[str, object]:
        return {
            "name": "four_link_periodic_square",
            "n_data_qubits": 4,
            "n_ancilla_qubits": 1,
            "qubit_order": "q0,q1,q2,q3 around the square",
            "gauss_checks": [term.qiskit_label for term in self.gauss_checks],
            "independent_gauss_checks": [term.name for term in self.independent_gauss_checks],
            "redundancy": "G3 = G0 G1 G2",
            "wilson": self.wilson.qiskit_label,
            "errors": {name: term.qiskit_label for name, term in self.errors.items()},
            "target_sector": {"G0": 1, "G1": 1, "G2": 1, "G3": 1, "W": 1},
        }


def pauli_commutes(left: PauliTerm, right: PauliTerm) -> bool:
    """Return whether two Pauli words commute using their symplectic parity."""
    anticommuting_sites = 0
    for a, b in zip(left.word, right.word, strict=True):
        if a != "I" and b != "I" and a != b:
            anticommuting_sites += 1
    return anticommuting_sites % 2 == 0


def commutator_norm(left: PauliTerm, right: PauliTerm) -> float:
    commutator = left.matrix() @ right.matrix() - right.matrix() @ left.matrix()
    return float(np.linalg.norm(commutator))


def anticommutator_norm(left: PauliTerm, right: PauliTerm) -> float:
    anticommutator = left.matrix() @ right.matrix() + right.matrix() @ left.matrix()
    return float(np.linalg.norm(anticommutator))


def algebra_report(model: BlindSpotModel | None = None) -> dict[str, object]:
    """Build a machine-readable, matrix-verified algebra report."""
    model = model or BlindSpotModel()
    errors: dict[str, object] = {}
    for name, error in model.errors.items():
        gauss = {
            check.name: {
                "relation": "commutes" if pauli_commutes(error, check) else "anticommutes",
                "commutator_frobenius_norm": commutator_norm(error, check),
                "anticommutator_frobenius_norm": anticommutator_norm(error, check),
            }
            for check in model.gauss_checks
        }
        errors[name] = {
            "operator": error.qiskit_label,
            "gauss_relations": gauss,
            "wilson_relation": (
                "commutes" if pauli_commutes(error, model.wilson) else "anticommutes"
            ),
            "expectations_after_error": model.expectations(model.apply_error(name)),
        }
    target = model.target_statevector()
    report = {
        "model": model.metadata(),
        "target_norm": float(np.vdot(target, target).real),
        "target_expectations": model.expectations(target),
        "errors": errors,
    }
    gauge_violating = errors["gauge_violating"]
    string_error = errors["gauge_preserving_string"]
    report["claims_verified"] = {
        "target_is_physical_and_W_plus": all(
            np.isclose(value, 1.0) for value in report["target_expectations"].values()
        ),
        "gauge_violating_flips_a_check": any(
            item["relation"] == "anticommutes"
            for item in gauge_violating["gauss_relations"].values()
        ),
        "string_error_preserves_all_checks": all(
            item["relation"] == "commutes"
            for item in string_error["gauss_relations"].values()
        ),
        "string_error_flips_W": string_error["wilson_relation"] == "anticommutes",
    }
    return report
