#!/usr/bin/env python3
"""Combine the archived matched Emerald/Sirius scan repeats offline."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import _bootstrap  # noqa: F401

from z2lgt.iqm_device_comparison import combine_device, compare_devices, load_json


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORTS = {
    "emerald": [
        ROOT / "results/iqm/emerald_periodic_matter_hardware/emerald_periodic_matter_scan_5000.json",
        ROOT / "results/iqm/emerald_periodic_matter_hardware/emerald_periodic_matter_scan_repeat2_5000.json",
    ],
    "sirius": [
        ROOT / "results/iqm/sirius_periodic_matter_hardware/sirius_periodic_matter_scan_5000.json",
        ROOT / "results/iqm/sirius_periodic_matter_hardware/sirius_periodic_matter_scan_repeat2_5000.json",
    ],
}
DEFAULT_MANIFESTS = {
    "emerald": [
        ROOT / "results/iqm/emerald_periodic_matter_scan_candidate_5000/readiness_manifest.json",
        ROOT / "results/iqm/emerald_periodic_matter_scan_repeat2_5000/readiness_manifest.json",
    ],
    "sirius": [
        ROOT / "results/iqm/sirius_periodic_matter_scan_candidate_5000/readiness_manifest.json",
        ROOT / "results/iqm/sirius_periodic_matter_scan_repeat2_5000/readiness_manifest.json",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / "results/processed/iqm_emerald_sirius_comparison.json",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=ROOT / "results/processed/iqm_emerald_sirius_comparison.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    devices = {
        device: combine_device(
            [load_json(path) for path in DEFAULT_REPORTS[device]],
            [load_json(path) for path in DEFAULT_MANIFESTS[device]],
        )
        for device in ("emerald", "sirius")
    }
    comparison = compare_devices(devices["emerald"], devices["sirius"])
    payload = {
        "schema_version": 1,
        "analysis": "inverse-variance combination of two independent same-calibration jobs per device",
        "claim_boundary": (
            "The reduced circuits prepare nominal W sectors and measure matter only; "
            "they do not hardware-certify Gauss or Wilson sectors."
        ),
        "devices": devices,
        "device_comparison": comparison,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    comparison_by_time = {row["time"]: row for row in comparison}
    rows = []
    for device, summary in devices.items():
        for point in summary["points"]:
            contrast = comparison_by_time[point["time"]]
            rows.append(
                {
                    "device": device,
                    "time": point["time"],
                    "dt": point["dt"],
                    "trotter_steps": point["trotter_steps"],
                    "exact_separation": point["exact_sector_separation"],
                    "trotter_separation": point["trotter_sector_separation"],
                    "hardware_separation": point["hardware_sector_separation"],
                    "hardware_separation_se": point["hardware_sector_separation_se"],
                    "hardware_separation_z": point["hardware_sector_separation_z"],
                    "separation_retained": point["separation_retained"],
                    "repeat_consistency_z": point["repeat_consistency_z"],
                    "Wplus_hardware": point["sectors"]["Wplus"]["hardware_O_LR"],
                    "Wplus_hardware_se": point["sectors"]["Wplus"]["hardware_O_LR_se"],
                    "Wminus_hardware": point["sectors"]["Wminus"]["hardware_O_LR"],
                    "Wminus_hardware_se": point["sectors"]["Wminus"]["hardware_O_LR_se"],
                    "emerald_minus_sirius": contrast["emerald_minus_sirius"],
                    "emerald_minus_sirius_se": contrast["emerald_minus_sirius_se"],
                    "emerald_minus_sirius_z": contrast["emerald_minus_sirius_z"],
                }
            )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("Matched IQM device comparison (two 5000-shot jobs per device)")
    for time in sorted(comparison_by_time):
        e_point = next(point for point in devices["emerald"]["points"] if point["time"] == time)
        s_point = next(point for point in devices["sirius"]["points"] if point["time"] == time)
        contrast = comparison_by_time[time]
        print(
            f"  t={time:g}: Emerald={e_point['hardware_sector_separation']:+.6f} "
            f"+/- {e_point['hardware_sector_separation_se']:.6f} "
            f"({e_point['hardware_sector_separation_z']:.2f} sigma); "
            f"Sirius={s_point['hardware_sector_separation']:+.6f} "
            f"+/- {s_point['hardware_sector_separation_se']:.6f} "
            f"({s_point['hardware_sector_separation_z']:.2f} sigma); "
            f"device contrast={contrast['emerald_minus_sirius_z']:.2f} sigma"
        )
    print(f"  JSON: {args.output_json}")
    print(f"  CSV: {args.output_csv}")


if __name__ == "__main__":
    main()
