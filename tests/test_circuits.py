import numpy as np

from z2lgt.circuits import ideal_statevector, trotter_circuit
from z2lgt.ed import evolve
from z2lgt.gauss import localized_imbalance_bits
from z2lgt.model import Z2Model


def test_small_step_trotter_agrees_with_exact_state():
    model = Z2Model(3)
    bits = localized_imbalance_bits(model)
    exact = evolve(model, bits, np.array([0.1]))[0]
    circuit = trotter_circuit(model, bits, time=0.1, dt=0.01)
    trotter = ideal_statevector(circuit)
    fidelity = abs(np.vdot(exact, trotter)) ** 2
    assert fidelity > 0.9999

