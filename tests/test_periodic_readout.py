import numpy as np

from z2lgt.circuits import ideal_counts
from z2lgt.periodic_readout import (
    analyze_periodic_joint_counts,
    canonical_periodic_readout_bits,
    periodic_joint_readout_circuit,
)


def test_periodic_readout_bit_order_and_inferred_g3():
    assert canonical_periodic_readout_bits("00000011") == (
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    analysis = analyze_periodic_joint_counts({"00000011": 100})
    assert analysis["P_Gauss"] == 1.0
    assert analysis["wilson_expectation"] == 1.0
    assert analysis["imbalance"] == 1.0


def test_t0_joint_readout_deterministically_resolves_both_wilson_sectors():
    plus = ideal_counts(
        periodic_joint_readout_circuit(0.0, 0.4, wilson_sector=1),
        1000,
        111,
    )
    minus = ideal_counts(
        periodic_joint_readout_circuit(0.0, 0.4, wilson_sector=-1),
        1000,
        112,
    )
    assert plus == {"00000011": 1000}
    assert minus == {"10000011": 1000}


def test_evolved_joint_readout_matches_statevector_sector_expectations():
    plus = analyze_periodic_joint_counts(
        ideal_counts(
            periodic_joint_readout_circuit(0.8, 0.4, wilson_sector=1),
            10_000,
            211,
        )
    )
    minus = analyze_periodic_joint_counts(
        ideal_counts(
            periodic_joint_readout_circuit(0.8, 0.4, wilson_sector=-1),
            10_000,
            212,
        )
    )
    assert np.isclose(plus["P_Gauss"], 1.0)
    assert np.isclose(minus["P_Gauss"], 1.0)
    assert np.isclose(plus["wilson_expectation"], 1.0)
    assert np.isclose(minus["wilson_expectation"], -1.0)
    assert abs(plus["imbalance"] - 0.189405) < 0.02
    assert abs(minus["imbalance"] - 0.040536) < 0.02
    assert plus["gauss_plus_wilson_acceptance"] == 1.0
    assert minus["gauss_plus_wilson_acceptance"] == 0.0
