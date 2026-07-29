from z2lgt.noise import NoiseConfig
from z2lgt.periodic_noisy_readout import run_periodic_noisy_readout


def test_zero_noise_periodic_readout_keeps_exact_sectors():
    payload = run_periodic_noisy_readout(
        shots=1000,
        noise_config=NoiseConfig(0.0, 0.0, 0.0),
    )
    plus, minus = payload["records"]
    assert plus["analysis"]["P_Gauss"] == 1.0
    assert minus["analysis"]["P_Gauss"] == 1.0
    assert plus["analysis"]["wilson_expectation"] == 1.0
    assert minus["analysis"]["wilson_expectation"] == -1.0


def test_synthetic_noise_degrades_but_does_not_erase_wilson_contrast():
    payload = run_periodic_noisy_readout(
        shots=4000,
        seed=9182,
        noise_config=NoiseConfig(0.001, 0.01, 0.02),
    )
    plus, minus = payload["records"]
    assert 0.0 < plus["analysis"]["P_Gauss"] < 1.0
    assert 0.0 < minus["analysis"]["P_Gauss"] < 1.0
    assert plus["analysis"]["wilson_expectation"] > 0.2
    assert minus["analysis"]["wilson_expectation"] < -0.2
    assert (
        plus["analysis"]["wilson_expectation"]
        - minus["analysis"]["wilson_expectation"]
        > 0.5
    )
