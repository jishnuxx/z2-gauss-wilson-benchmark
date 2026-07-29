import numpy as np

from z2lgt.ed import evolve
from z2lgt.gauss import localized_imbalance_bits
from z2lgt.model import Z2Model


def test_exact_evolution_conserves_norm():
    model = Z2Model(3)
    states = evolve(model, localized_imbalance_bits(model), np.linspace(0, 1, 6))
    assert max(abs(np.vdot(state, state).real - 1) for state in states) < 1e-12

