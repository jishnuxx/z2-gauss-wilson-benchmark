from z2lgt.bitstrings import canonical_counts, postselect_counts, qiskit_key_to_bits
from z2lgt.gauss import is_physical, localized_imbalance_bits
from z2lgt.model import Z2Model


def test_qiskit_endianness_conversion():
    assert qiskit_key_to_bits("00101", 5) == (1, 0, 1, 0, 0)


def test_classifier_known_physical_and_unphysical():
    model = Z2Model(3)
    physical = tuple(localized_imbalance_bits(model))
    unphysical = tuple([1 - physical[0], *physical[1:]])
    assert is_physical(physical, model)
    assert not is_physical(unphysical, model)


def test_postselection_accepts_no_unphysical_counts():
    model = Z2Model(3)
    counts = canonical_counts({"01011": 20, "01010": 7}, model.n_qubits)
    selected = postselect_counts(counts, model)
    assert sum(selected.values()) <= sum(counts.values())
    assert all(is_physical(bits, model) for bits in selected)

