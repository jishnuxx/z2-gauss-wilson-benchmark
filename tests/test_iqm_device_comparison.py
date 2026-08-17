import math
from pathlib import Path

import pytest

from z2lgt.iqm_device_comparison import (
    combine_device,
    compare_devices,
    consistency_z,
    inverse_variance_mean,
    load_json,
)


ROOT = Path(__file__).resolve().parents[1]


def test_inverse_variance_mean_equal_errors() -> None:
    mean, standard_error = inverse_variance_mean([0.04, 0.06], [0.01, 0.01])
    assert math.isclose(mean, 0.05)
    assert math.isclose(standard_error, 0.01 / math.sqrt(2.0))


def test_inverse_variance_mean_rejects_nonpositive_error() -> None:
    with pytest.raises(ValueError, match="positive and finite"):
        inverse_variance_mean([1.0], [0.0])


def test_consistency_z_uses_independent_error_sum() -> None:
    assert math.isclose(consistency_z(0.1, 0.03, 0.0, 0.04), 2.0)


def test_archived_matched_device_comparison() -> None:
    devices = {}
    for device in ("emerald", "sirius"):
        base = ROOT / f"results/iqm/{device}_periodic_matter_hardware"
        report_paths = [
            base / f"{device}_periodic_matter_scan_5000.json",
            base / f"{device}_periodic_matter_scan_repeat2_5000.json",
        ]
        manifest_paths = [
            ROOT
            / f"results/iqm/{device}_periodic_matter_scan_candidate_5000/readiness_manifest.json",
            ROOT
            / f"results/iqm/{device}_periodic_matter_scan_repeat2_5000/readiness_manifest.json",
        ]
        devices[device] = combine_device(
            [load_json(path) for path in report_paths],
            [load_json(path) for path in manifest_paths],
        )

    emerald_t1 = devices["emerald"]["points"][2]
    sirius_t1 = devices["sirius"]["points"][2]
    comparison_t1 = compare_devices(devices["emerald"], devices["sirius"])[2]
    assert emerald_t1["hardware_sector_separation"] == pytest.approx(0.1040803515)
    assert emerald_t1["hardware_sector_separation_z"] == pytest.approx(13.0128823)
    assert sirius_t1["hardware_sector_separation"] == pytest.approx(-0.0049803089)
    assert comparison_t1["emerald_minus_sirius_z"] == pytest.approx(10.2757911)
