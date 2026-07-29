import numpy as np
from qiskit.quantum_info import Statevector

from z2lgt.blindspot_circuits import gauss_check_circuit, joint_diagnostic_circuit, target_preparation_circuit
from z2lgt.blindspot_model import BlindSpotModel
from z2lgt.circuits import ideal_counts


def test_qiskit_target_preparation_matches_exact_model():
    exact = BlindSpotModel().target_statevector()
    circuit_state = np.asarray(Statevector.from_instruction(target_preparation_circuit()).data)
    assert abs(np.vdot(exact, circuit_state)) ** 2 > 1 - 1e-12


def test_ideal_joint_syndromes_separate_all_three_cases():
    expected = {
        "no_error": {"0000": 256},
        "gauge_violating": {"0010": 256},
        "gauge_preserving_string": {"0001": 256},
    }
    for case, counts in expected.items():
        assert ideal_counts(joint_diagnostic_circuit(case), 256, seed=91) == counts


def test_ancilla_checks_detect_only_gauge_violation():
    gv = [ideal_counts(gauss_check_circuit(index, "gauge_violating"), 64, seed=12) for index in range(4)]
    string = [ideal_counts(gauss_check_circuit(index, "gauge_preserving_string"), 64, seed=12) for index in range(4)]
    assert gv == [{"1": 64}, {"0": 64}, {"0": 64}, {"1": 64}]
    assert string == [{"0": 64}] * 4
