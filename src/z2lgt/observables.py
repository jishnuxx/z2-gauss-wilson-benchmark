"""Diagonal benchmark observables usable from states or bitstrings."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from .gauss import n_violations
from .model import Z2Model

Observable = Callable[[tuple[int, ...], Z2Model], float]


def occupation(site: int) -> Observable:
    return lambda bits, model: float(bits[model.matter_qubit(site)])


def charge_imbalance(bits: tuple[int, ...], model: Z2Model) -> float:
    return float(
        sum(((-1) ** site) * bits[model.matter_qubit(site)] for site in range(model.n_sites))
        / model.n_sites
    )


def mean_link_z(bits: tuple[int, ...], model: Z2Model) -> float:
    return float(
        np.mean([1 - 2 * bits[model.link_qubit(link)] for link in range(model.n_links)])
    )


def right_occupation(bits: tuple[int, ...], model: Z2Model) -> float:
    """Finite-size early-time transport diagnostic."""
    return float(bits[model.matter_qubit(model.n_sites - 1)])


def gauss_violation_rate(bits: tuple[int, ...], model: Z2Model) -> float:
    return n_violations(bits, model) / model.n_sites


OBSERVABLES: dict[str, Observable] = {
    "charge_imbalance": charge_imbalance,
    "mean_link_z": mean_link_z,
    "right_occupation": right_occupation,
    "gauss_violation_rate": gauss_violation_rate,
}


def basis_values(model: Z2Model, observable: Observable) -> np.ndarray:
    values = np.empty(2**model.n_qubits, dtype=float)
    for index in range(len(values)):
        bits = tuple((index >> qubit) & 1 for qubit in range(model.n_qubits))
        values[index] = observable(bits, model)
    return values


def state_expectation(state: np.ndarray, model: Z2Model, observable: Observable) -> float:
    probabilities = np.abs(state) ** 2
    return float(np.dot(probabilities, basis_values(model, observable)))


def all_state_expectations(state: np.ndarray, model: Z2Model) -> dict[str, float]:
    return {name: state_expectation(state, model, obs) for name, obs in OBSERVABLES.items()}

