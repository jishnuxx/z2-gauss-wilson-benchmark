import csv

import numpy as np
from qiskit.quantum_info import Statevector

from z2lgt.periodic_circuits import (
    periodic_circuit_validation,
    periodic_target_preparation_circuit,
    periodic_trotter_circuit,
    periodic_two_sector_circuit_comparison,
    write_periodic_circuit_validation_csv,
)
from z2lgt.periodic_dynamics import operator_expectation, target_state
from z2lgt.periodic_model import PeriodicZ2Model


def test_periodic_target_preparation_matches_exact_state():
    model = PeriodicZ2Model()
    prepared = np.asarray(
        Statevector.from_instruction(periodic_target_preparation_circuit(model)).data
    )
    assert np.isclose(abs(np.vdot(target_state(model), prepared)) ** 2, 1.0)
    assert all(
        np.isclose(operator_expectation(prepared, check), 1.0)
        for check in model.gauss_checks
    )
    assert np.isclose(operator_expectation(prepared, model.wilson), 1.0)


def test_periodic_trotter_preserves_gauss_and_wilson_exactly():
    model = PeriodicZ2Model()
    state = np.asarray(
        Statevector.from_instruction(periodic_trotter_circuit(0.4, 0.1, model)).data
    )
    assert all(
        np.isclose(operator_expectation(state, check), 1.0)
        for check in model.gauss_checks
    )
    assert np.isclose(operator_expectation(state, model.wilson), 1.0)

    wrong = np.asarray(
        Statevector.from_instruction(
            periodic_trotter_circuit(0.4, 0.1, model, wilson_sector=-1)
        ).data
    )
    assert all(
        np.isclose(operator_expectation(wrong, check), 1.0)
        for check in model.gauss_checks
    )
    assert np.isclose(operator_expectation(wrong, model.wilson), -1.0)


def test_periodic_trotter_converges_toward_exact_dynamics():
    coarse = periodic_circuit_validation([0.0, 0.4], dt=0.2)[-1]
    fine = periodic_circuit_validation([0.0, 0.4], dt=0.05)[-1]
    assert fine["state_fidelity"] > coarse["state_fidelity"]
    assert fine["state_fidelity"] > 0.999


def test_two_sector_candidate_retains_nonzero_observable_separation():
    rows = periodic_two_sector_circuit_comparison(
        time=0.8,
        dt=0.4,
        include_resources=False,
    )
    exact = abs(rows[0]["exact_imbalance"] - rows[1]["exact_imbalance"])
    trotter = abs(rows[0]["trotter_imbalance"] - rows[1]["trotter_imbalance"])
    assert exact > 0.2
    assert trotter > 0.14
    assert trotter / exact > 0.70


def test_periodic_circuit_validation_csv_schema(tmp_path):
    rows = periodic_circuit_validation([0.0, 0.2], dt=0.1)
    path = write_periodic_circuit_validation_csv(rows, tmp_path / "validation.csv")
    with path.open(newline="", encoding="utf-8") as handle:
        persisted = list(csv.DictReader(handle))
    assert len(persisted) == 2
    assert list(persisted[0]) == list(rows[0])
