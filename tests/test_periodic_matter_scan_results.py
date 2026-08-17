import math

from z2lgt.periodic_matter_scan_results import point_summaries


def test_point_summary_uses_independent_sector_uncertainties():
    records = [
        {
            "time": 0.8,
            "dt": 0.4,
            "analysis": {"imbalance": 0.12, "imbalance_se": 0.008},
        },
        {
            "time": 0.8,
            "dt": 0.4,
            "analysis": {"imbalance": 0.07, "imbalance_se": 0.009},
        },
    ]
    physics = {
        (0.8, 0.4): {
            "exact_sector_separation": 0.20,
            "trotter_sector_separation": 0.15,
        }
    }
    summary = point_summaries(records, physics)[0]
    expected_se = math.sqrt(0.008**2 + 0.009**2)
    assert math.isclose(summary["hardware_sector_separation"], 0.05)
    assert math.isclose(summary["hardware_sector_separation_se"], expected_se)
    assert math.isclose(summary["hardware_sector_separation_z"], 0.05 / expected_se)
