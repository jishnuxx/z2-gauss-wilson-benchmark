import numpy as np

from z2lgt.gauss import basis_state, localized_imbalance_bits
from z2lgt.model import Z2Model
from z2lgt.observables import (
    gauss_violation_rate,
    right_occupation,
    state_expectation,
)


def test_basis_observables():
    model = Z2Model(3)
    bits = tuple(localized_imbalance_bits(model))
    assert right_occupation(bits, model) == 0.0
    assert gauss_violation_rate(bits, model) == 0.0
    assert state_expectation(basis_state(bits), model, right_occupation) == 0.0

