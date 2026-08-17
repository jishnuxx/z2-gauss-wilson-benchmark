"""Offline aggregation of matched Emerald and Sirius periodic-matter scans."""

from __future__ import annotations

import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any


CASES = ("Wplus", "Wminus")


def inverse_variance_mean(
    values: Sequence[float], standard_errors: Sequence[float]
) -> tuple[float, float]:
    """Return the inverse-variance weighted mean and its standard error."""
    if len(values) != len(standard_errors) or not values:
        raise ValueError("values and standard_errors must have equal nonzero length")
    if any(error <= 0.0 or not math.isfinite(error) for error in standard_errors):
        raise ValueError("standard errors must be positive and finite")
    weights = [1.0 / error**2 for error in standard_errors]
    weight_sum = sum(weights)
    mean = sum(weight * value for weight, value in zip(weights, values, strict=True)) / weight_sum
    return mean, math.sqrt(1.0 / weight_sum)


def consistency_z(value_a: float, se_a: float, value_b: float, se_b: float) -> float:
    """Absolute difference between independent estimates in standard deviations."""
    return abs(value_a - value_b) / math.hypot(se_a, se_b)


def _records_by_key(report: dict[str, Any]) -> dict[tuple[float, str], dict[str, Any]]:
    records = report.get("records", [])
    keyed = {(float(record["time"]), str(record["case"])): record for record in records}
    if len(keyed) != len(records):
        raise ValueError("duplicate (time, case) record in hardware report")
    return keyed


def _summaries_by_time(report: dict[str, Any]) -> dict[float, dict[str, Any]]:
    summaries = report.get("point_summaries", [])
    keyed = {float(summary["time"]): summary for summary in summaries}
    if len(keyed) != len(summaries):
        raise ValueError("duplicate time in point_summaries")
    return keyed


def validate_matched_repeats(
    reports: Sequence[dict[str, Any]], manifests: Sequence[dict[str, Any]]
) -> None:
    """Validate that two reports are a same-device, same-calibration matched repeat."""
    if len(reports) != 2 or len(manifests) != 2:
        raise ValueError("exactly two reports and two manifests are required")
    device = reports[0].get("quantum_computer")
    if not device or any(report.get("quantum_computer") != device for report in reports):
        raise ValueError("reports must target the same device")
    if any(report.get("status") != "completed" for report in reports):
        raise ValueError("all hardware reports must be completed")
    calibrations = {report.get("calibration_set_id") for report in reports}
    if len(calibrations) != 1:
        raise ValueError("matched repeats must use one calibration set")
    shots = {int(report.get("shots_per_circuit", 0)) for report in reports}
    if len(shots) != 1 or next(iter(shots)) <= 0:
        raise ValueError("matched repeats must use the same positive shot count")

    record_keys = [_records_by_key(report).keys() for report in reports]
    if record_keys[0] != record_keys[1]:
        raise ValueError("matched repeats must contain identical physics points and sectors")
    expected_cases = {case for _, case in record_keys[0]}
    if expected_cases != set(CASES):
        raise ValueError(f"expected sectors {CASES}, found {sorted(expected_cases)}")

    reference_layout = manifests[0].get("fixed_initial_layout_indices")
    reference_calibration = reports[0]["calibration_set_id"]
    for report, manifest in zip(reports, manifests, strict=True):
        if manifest.get("quantum_computer") != device:
            raise ValueError("report and manifest device mismatch")
        if manifest.get("candidate_id") != report.get("candidate_id"):
            raise ValueError("report and manifest candidate mismatch")
        if manifest.get("calibration_set_id") != reference_calibration:
            raise ValueError("report and manifest calibration mismatch")
        if manifest.get("fixed_initial_layout_indices") != reference_layout:
            raise ValueError("matched repeats must reuse the same physical layout")
        if int(manifest.get("shots", 0)) != next(iter(shots)):
            raise ValueError("report and manifest shot mismatch")


def combine_device(
    reports: Sequence[dict[str, Any]], manifests: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    """Combine two validated same-device reports and retain full provenance."""
    validate_matched_repeats(reports, manifests)
    device = str(reports[0]["quantum_computer"])
    record_maps = [_records_by_key(report) for report in reports]
    summary_maps = [_summaries_by_time(report) for report in reports]
    times = sorted(summary_maps[0])
    if any(sorted(summary_map) != times for summary_map in summary_maps[1:]):
        raise ValueError("point summaries do not have matching times")

    points: list[dict[str, Any]] = []
    for time in times:
        summaries = [summary_map[time] for summary_map in summary_maps]
        separations = [float(summary["hardware_sector_separation"]) for summary in summaries]
        separation_ses = [float(summary["hardware_sector_separation_se"]) for summary in summaries]
        separation, separation_se = inverse_variance_mean(separations, separation_ses)

        point: dict[str, Any] = {
            "time": time,
            "dt": float(summaries[0]["dt"]),
            "trotter_steps": int(summaries[0]["trotter_steps"]),
            "exact_sector_separation": float(summaries[0]["exact_sector_separation"]),
            "trotter_sector_separation": float(summaries[0]["trotter_sector_separation"]),
            "hardware_sector_separation": separation,
            "hardware_sector_separation_se": separation_se,
            "hardware_sector_separation_z": abs(separation) / separation_se,
            "separation_retained": separation
            / float(summaries[0]["trotter_sector_separation"]),
            "repeat_consistency_z": consistency_z(
                separations[0], separation_ses[0], separations[1], separation_ses[1]
            ),
            "replicate_separations": separations,
            "replicate_separation_ses": separation_ses,
            "sectors": {},
        }
        for case in CASES:
            records = [record_map[(time, case)] for record_map in record_maps]
            values = [float(record["analysis"]["imbalance"]) for record in records]
            errors = [float(record["analysis"]["imbalance_se"]) for record in records]
            combined, combined_se = inverse_variance_mean(values, errors)
            point["sectors"][case] = {
                "exact_O_LR": float(records[0]["exact_O_LR"]),
                "trotter_O_LR": float(records[0]["trotter_O_LR"]),
                "hardware_O_LR": combined,
                "hardware_O_LR_se": combined_se,
                "replicate_values": values,
                "replicate_ses": errors,
            }
        points.append(point)

    manifest = manifests[0]
    return {
        "quantum_computer": device,
        "calibration_set_id": reports[0]["calibration_set_id"],
        "shots_per_circuit_per_job": reports[0]["shots_per_circuit"],
        "number_of_jobs": len(reports),
        "job_ids": [report["job_id"] for report in reports],
        "candidate_ids": [report["candidate_id"] for report in reports],
        "fixed_initial_layout_indices": manifest["fixed_initial_layout_indices"],
        "fixed_initial_layout_components": manifest["fixed_initial_layout_components"],
        "resources": {
            "maximum_native_depth": manifest["maximum_native_depth"],
            "maximum_native_cz_count": manifest["maximum_native_cz_count"],
            "maximum_native_move_count": manifest["maximum_native_move_count"],
            "maximum_r_error": manifest["maximum_r_error"],
            "maximum_cz_error": manifest["maximum_cz_error"],
            "maximum_move_error": manifest["maximum_move_error"],
            "maximum_readout_error": manifest["maximum_readout_error"],
        },
        "points": points,
    }


def compare_devices(emerald: dict[str, Any], sirius: dict[str, Any]) -> list[dict[str, float]]:
    """Return pointwise Emerald-minus-Sirius separation contrasts."""
    emerald_points = {float(point["time"]): point for point in emerald["points"]}
    sirius_points = {float(point["time"]): point for point in sirius["points"]}
    if emerald_points.keys() != sirius_points.keys():
        raise ValueError("device summaries must contain the same times")
    comparisons = []
    for time in sorted(emerald_points):
        e_point = emerald_points[time]
        s_point = sirius_points[time]
        difference = (
            e_point["hardware_sector_separation"]
            - s_point["hardware_sector_separation"]
        )
        difference_se = math.hypot(
            e_point["hardware_sector_separation_se"],
            s_point["hardware_sector_separation_se"],
        )
        comparisons.append(
            {
                "time": time,
                "emerald_minus_sirius": difference,
                "emerald_minus_sirius_se": difference_se,
                "emerald_minus_sirius_z": abs(difference) / difference_se,
            }
        )
    return comparisons


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from ``path``."""
    import json

    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {path}")
    return value
