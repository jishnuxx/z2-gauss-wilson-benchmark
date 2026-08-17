from qiskit import QuantumCircuit

from z2lgt.iqm_freeze_audit import (
    has_four_bit_matter_readout,
    measurement_classical_bits,
    parse_fixed_layout,
)


def test_matter_readout_allows_logical_states_to_move_before_measurement():
    circuit = QuantumCircuit(8, 4)
    circuit.measure([7, 5, 2, 0], [0, 1, 2, 3])
    assert measurement_classical_bits(circuit) == [0, 1, 2, 3]
    assert has_four_bit_matter_readout(circuit)


def test_matter_readout_rejects_missing_or_reused_classical_outputs():
    missing = QuantumCircuit(8, 4)
    missing.measure([7, 5, 2], [0, 1, 2])
    assert not has_four_bit_matter_readout(missing)

    reused = QuantumCircuit(8, 4)
    reused.measure([7, 5, 2, 0], [0, 1, 2, 2])
    assert not has_four_bit_matter_readout(reused)


def test_fixed_layout_parser_requires_eight_distinct_indices():
    assert parse_fixed_layout("17,24,16,10,8,7,9,3") == (
        17,
        24,
        16,
        10,
        8,
        7,
        9,
        3,
    )
