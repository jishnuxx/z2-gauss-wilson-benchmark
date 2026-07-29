import numpy as np

from z2lgt.gauss import commutator_norms, gauss_terms
from z2lgt.model import Z2Model


def test_hamiltonian_is_hermitian():
    model = Z2Model(3)
    hamiltonian = model.hamiltonian_matrix()
    assert np.allclose(hamiltonian, hamiltonian.conj().T, atol=1e-12)


def test_hamiltonian_commutes_with_all_gauss_generators():
    assert max(commutator_norms(Z2Model(3))) < 1e-12
    assert max(commutator_norms(Z2Model(4))) < 1e-12


def test_gauss_operator_eigenvalues_are_plus_or_minus_one():
    for term in gauss_terms(Z2Model(3)):
        assert set(np.round(np.linalg.eigvalsh(term.matrix()), 12)) == {-1.0, 1.0}

