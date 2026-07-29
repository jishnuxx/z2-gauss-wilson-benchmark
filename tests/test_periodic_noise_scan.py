from z2lgt.noise import NoiseConfig
from z2lgt.periodic_noise_scan import run_periodic_noise_scale_scan


def test_periodic_noise_scan_has_both_sectors_at_each_scale():
    payload = run_periodic_noise_scale_scan(
        (0.0, 1.0),
        shots=1500,
        seed=7712,
        baseline=NoiseConfig(0.001, 0.01, 0.02),
    )
    rows = payload["summary_rows"]
    assert len(rows) == 4
    assert {(row["noise_scale"], row["case"]) for row in rows} == {
        (0.0, "Wplus"),
        (0.0, "Wminus"),
        (1.0, "Wplus"),
        (1.0, "Wminus"),
    }


def test_noise_scan_degrades_target_acceptance_and_wilson_contrast():
    payload = run_periodic_noise_scale_scan(
        (0.0, 1.0),
        shots=2000,
        seed=8821,
    )
    plus = [row for row in payload["summary_rows"] if row["case"] == "Wplus"]
    ideal, noisy = plus
    assert ideal["target_joint_acceptance"] == 1.0
    assert ideal["wrong_sector_false_acceptance"] == 0.0
    assert ideal["wilson_contrast"] == 2.0
    assert noisy["target_joint_acceptance"] < ideal["target_joint_acceptance"]
    assert noisy["wrong_sector_false_acceptance"] > 0.0
    assert noisy["wilson_contrast"] < ideal["wilson_contrast"]
