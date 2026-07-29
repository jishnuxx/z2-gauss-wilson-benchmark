import json

import numpy as np

from z2lgt.periodic_model import (
    PeriodicZ2Model,
    pauli_commutes,
    periodic_algebra_report,
)


def test_periodic_layout_and_operator_weights():
    model = PeriodicZ2Model()
    assert model.n_qubits == 8
    assert len(model.gauss_checks) == 4
    assert all(check.word.count("Z") == 3 for check in model.gauss_checks)
    assert model.wilson.qiskit_label == "XXXXIIII"
    assert model.wilson.word.count("X") == 4


def test_periodic_hamiltonian_preserves_gauss_and_wilson_sectors():
    report = periodic_algebra_report()
    assert all(report["claims_verified"].values())
    json.dumps(report)
    assert all(
        np.isclose(norm, 0.0)
        for norm in report["hamiltonian_gauss_commutator_norms"].values()
    )
    assert np.isclose(report["hamiltonian_wilson_commutator_norm"], 0.0)


def test_periodic_error_relations_define_independent_blind_spot():
    model = PeriodicZ2Model()
    gauge_error = model.errors["gauge_violating"]
    string_error = model.errors["gauge_preserving_string"]
    assert any(not pauli_commutes(gauge_error, check) for check in model.gauss_checks)
    assert all(pauli_commutes(string_error, check) for check in model.gauss_checks)
    assert not pauli_commutes(string_error, model.wilson)


def test_periodic_model_rejects_other_sizes_for_this_milestone():
    try:
        PeriodicZ2Model(n_sites=3)
    except ValueError as error:
        assert "exactly four sites" in str(error)
    else:
        raise AssertionError("odd or alternative sizes must not silently change the benchmark")
