import pytest

from z2lgt.gauss import (
    gauss_eigenvalues,
    is_physical,
    localized_imbalance_bits,
    physical_bits_from_matter,
)
from z2lgt.model import Z2Model


@pytest.mark.parametrize("n_sites", [3, 4])
def test_initial_state_is_physical(n_sites):
    model = Z2Model(n_sites)
    bits = localized_imbalance_bits(model)
    assert gauss_eigenvalues(bits, model) == (1,) * n_sites
    assert is_physical(bits, model)


def test_odd_matter_parity_is_rejected():
    with pytest.raises(ValueError, match="even matter parity"):
        physical_bits_from_matter(Z2Model(3), [1, 0, 0])

