import numpy as np

from z2lgt.blindspot_model import BlindSpotModel, algebra_report, pauli_commutes


def test_square_pauli_construction_and_redundancy():
    model = BlindSpotModel()
    assert [check.qiskit_label for check in model.gauss_checks] == ["IIXX", "IXXI", "XXII", "XIIX"]
    assert model.wilson.qiskit_label == "ZZZZ"
    product = np.eye(16, dtype=complex)
    for check in model.gauss_checks:
        product = product @ check.matrix()
    assert np.allclose(product, np.eye(16))


def test_error_commutation_relations_are_the_claimed_blind_spot():
    model = BlindSpotModel()
    gauge_violating = model.errors["gauge_violating"]
    string_error = model.errors["gauge_preserving_string"]
    assert any(not pauli_commutes(gauge_violating, check) for check in model.gauss_checks)
    assert all(pauli_commutes(string_error, check) for check in model.gauss_checks)
    assert not pauli_commutes(string_error, model.wilson)
    assert all(algebra_report(model)["claims_verified"].values())


def test_target_and_error_expectations():
    model = BlindSpotModel()
    assert all(np.isclose(value, 1) for value in model.expectations(model.target_statevector()).values())
    gv = model.expectations(model.apply_error("gauge_violating"))
    string = model.expectations(model.apply_error("gauge_preserving_string"))
    assert np.isclose(min(gv[f"G{i}"] for i in range(4)), -1)
    assert all(np.isclose(string[f"G{i}"], 1) for i in range(4))
    assert np.isclose(string["W"], -1)
