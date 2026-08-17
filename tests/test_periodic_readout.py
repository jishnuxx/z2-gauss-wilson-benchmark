import numpy as np

from z2lgt.circuits import ideal_counts
from z2lgt.periodic_readout import (
    analyze_matter_counts,
    analyze_periodic_joint_counts,
    analyze_wilson_matter_counts,
    canonical_matter_readout_bits,
    canonical_periodic_readout_bits,
    canonical_wilson_matter_readout_bits,
    periodic_joint_readout_circuit,
    periodic_matter_readout_circuit,
    periodic_wilson_matter_readout_circuit,
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


def test_reduced_readout_bit_orders_and_observables():
    assert canonical_matter_readout_bits("0011") == (1, 1, 0, 0)
    assert canonical_wilson_matter_readout_bits("10011") == (1, 1, 0, 0, 1)
    assert analyze_matter_counts({"0011": 100})["imbalance"] == 1.0
    analysis = analyze_wilson_matter_counts({"00011": 30, "10011": 70})
    assert analysis["imbalance"] == 1.0
    assert np.isclose(analysis["wilson_expectation"], -0.4)


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


def test_t0_reduced_readouts_resolve_expected_values():
    matter = ideal_counts(periodic_matter_readout_circuit(0.0, 0.4), 1000, 113)
    wilson_matter = ideal_counts(
        periodic_wilson_matter_readout_circuit(0.0, 0.4, wilson_sector=-1),
        1000,
        114,
    )
    assert matter == {"0011": 1000}
    assert wilson_matter == {"10011": 1000}


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
