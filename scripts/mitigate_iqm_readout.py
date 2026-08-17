#!/usr/bin/env python3
"""Apply archived IQM readout-assignment mitigation to saved hardware counts.

This script does not contact IQM and does not submit hardware jobs.  It uses the
per-measured-qubit readout errors archived in the frozen readiness manifests as
a symmetric independent assignment-error model.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401
from z2lgt.blindspot_analysis import analyze_joint_counts
from z2lgt.periodic_readout import analyze_periodic_joint_counts
from z2lgt.readout_mitigation import (
    mitigate_counts_independent,
    readout_probabilities_from_manifest,
)


STATIC_METHOD = "raw"
MITIGATED_METHOD = "readout_mitigated_manifest_symmetric"


FIELDNAMES = [
    "dataset",
    "case",
    "method",
    "shots",
    "P_Gauss",
    "P_Gauss_se",
    "wilson_expectation",
    "wilson_expectation_se",
    "gauss_plus_string_acceptance",
    "gauss_plus_wilson_acceptance",
    "imbalance",
    "imbalance_se",
    "gauss_plus_wilson_imbalance",
    "negative_probability_mass",
    "condition_number",
    "max_readout_error",
    "mean_readout_error",
    "physical_qubits_by_classical_bit",
    "expected_P_Gauss",
    "expected_wilson_expectation",
]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def static_row(
    *,
    case: str,
    method: str,
    analysis: dict[str, Any],
    expected: dict[str, Any],
    mitigation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "dataset": "static_blindspot",
        "case": case,
        "method": method,
        "shots": analysis["shots"],
        "P_Gauss": analysis["P_Gauss"],
        "P_Gauss_se": analysis["P_Gauss_se"],
        "wilson_expectation": analysis["wilson_expectation"],
        "wilson_expectation_se": analysis["wilson_expectation_se"],
        "gauss_plus_string_acceptance": analysis["gauss_plus_string_acceptance"],
        "negative_probability_mass": "" if mitigation is None else mitigation["negative_probability_mass"],
        "condition_number": "" if mitigation is None else mitigation["condition_number"],
        "max_readout_error": "" if mitigation is None else mitigation["max_readout_error"],
        "mean_readout_error": "" if mitigation is None else mitigation["mean_readout_error"],
        "physical_qubits_by_classical_bit": ""
        if mitigation is None
        else " ".join(str(qubit) for qubit in mitigation["physical_qubits_by_classical_bit"]),
        "expected_P_Gauss": expected.get("P_Gauss", ""),
        "expected_wilson_expectation": expected.get("wilson_expectation", ""),
    }


def periodic_row(
    *,
    case: str,
    method: str,
    analysis: dict[str, Any],
    mitigation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "dataset": "periodic_readout",
        "case": case,
        "method": method,
        "shots": analysis["shots"],
        "P_Gauss": analysis["P_Gauss"],
        "P_Gauss_se": analysis["P_Gauss_se"],
        "wilson_expectation": analysis["wilson_expectation"],
        "gauss_plus_wilson_acceptance": analysis["gauss_plus_wilson_acceptance"],
        "imbalance": analysis["imbalance"],
        "imbalance_se": analysis["imbalance_se"],
        "gauss_plus_wilson_imbalance": analysis["gauss_plus_wilson_imbalance"],
        "negative_probability_mass": "" if mitigation is None else mitigation["negative_probability_mass"],
        "condition_number": "" if mitigation is None else mitigation["condition_number"],
        "max_readout_error": "" if mitigation is None else mitigation["max_readout_error"],
        "mean_readout_error": "" if mitigation is None else mitigation["mean_readout_error"],
        "physical_qubits_by_classical_bit": ""
        if mitigation is None
        else " ".join(str(qubit) for qubit in mitigation["physical_qubits_by_classical_bit"]),
    }


def mitigate_static(
    result_path: Path,
    manifest_path: Path,
    *,
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    output_records: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for record in payload["records"]:
        case = str(record["error_type"])
        raw_analysis = analyze_joint_counts(record["raw_counts"])
        rows.append(
            static_row(
                case=case,
                method=STATIC_METHOD,
                analysis=raw_analysis,
                expected=record.get("expected", {}),
            )
        )
        calibration = readout_probabilities_from_manifest(
            manifest_path,
            case=case,
            root=root,
        )
        mitigated = mitigate_counts_independent(
            record["raw_counts"],
            calibration["readout_error_probabilities"],
        )
        mitigated_analysis = analyze_joint_counts(mitigated["mitigated_counts"])
        mitigation_summary = {
            **calibration,
            "negative_probability_mass": mitigated["negative_probability_mass"],
            "condition_number": mitigated["condition_number"],
            "solver": mitigated["solver"],
            "response_model": mitigated["response_model"],
        }
        rows.append(
            static_row(
                case=case,
                method=MITIGATED_METHOD,
                analysis=mitigated_analysis,
                expected=record.get("expected", {}),
                mitigation=mitigation_summary,
            )
        )
        output_records.append(
            {
                "dataset": "static_blindspot",
                "case": case,
                "raw_counts": record["raw_counts"],
                "raw_analysis": raw_analysis,
                "mitigated_counts": mitigated["mitigated_counts"],
                "mitigated_analysis": mitigated_analysis,
                "mitigation": mitigation_summary,
                "expected": record.get("expected", {}),
            }
        )
    return output_records, rows


def mitigate_periodic(
    result_path: Path,
    manifest_path: Path,
    *,
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    output_records: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for record in payload["records"]:
        case = str(record["case"])
        raw_analysis = analyze_periodic_joint_counts(record["raw_counts"])
        rows.append(periodic_row(case=case, method=STATIC_METHOD, analysis=raw_analysis))
        calibration = readout_probabilities_from_manifest(
            manifest_path,
            case=case,
            root=root,
        )
        mitigated = mitigate_counts_independent(
            record["raw_counts"],
            calibration["readout_error_probabilities"],
        )
        mitigated_analysis = analyze_periodic_joint_counts(mitigated["mitigated_counts"])
        mitigation_summary = {
            **calibration,
            "negative_probability_mass": mitigated["negative_probability_mass"],
            "condition_number": mitigated["condition_number"],
            "solver": mitigated["solver"],
            "response_model": mitigated["response_model"],
        }
        rows.append(
            periodic_row(
                case=case,
                method=MITIGATED_METHOD,
                analysis=mitigated_analysis,
                mitigation=mitigation_summary,
            )
        )
        output_records.append(
            {
                "dataset": "periodic_readout",
                "case": case,
                "raw_counts": record["raw_counts"],
                "raw_analysis": raw_analysis,
                "mitigated_counts": mitigated["mitigated_counts"],
                "mitigated_analysis": mitigated_analysis,
                "mitigation": mitigation_summary,
            }
        )
    return output_records, rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--static-results",
        type=Path,
        default=Path("results/iqm/static_blindspot_5000/blindspot_minimal.json"),
    )
    parser.add_argument(
        "--static-manifest",
        type=Path,
        default=Path("results/iqm/emerald_blindspot_candidate_5000/readiness_manifest.json"),
    )
    parser.add_argument(
        "--periodic-results",
        type=Path,
        default=Path("results/iqm/periodic_hardware/periodic_joint_readout_5000_seed1.json"),
    )
    parser.add_argument(
        "--periodic-manifest",
        type=Path,
        default=Path("results/iqm/emerald_periodic_candidate_5000_seed1/readiness_manifest.json"),
    )
    parser.add_argument("--output-json", type=Path, default=Path("results/processed/iqm_readout_mitigation.json"))
    parser.add_argument("--output-csv", type=Path, default=Path("results/processed/iqm_readout_mitigation.csv"))
    args = parser.parse_args()

    root = _bootstrap.ROOT
    records: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []

    static_records, static_rows = mitigate_static(args.static_results, args.static_manifest, root=root)
    periodic_records, periodic_rows = mitigate_periodic(
        args.periodic_results,
        args.periodic_manifest,
        root=root,
    )
    records.extend(static_records)
    records.extend(periodic_records)
    rows.extend(static_rows)
    rows.extend(periodic_rows)

    summary = {
        "schema_version": 1,
        "method": MITIGATED_METHOD,
        "scope": (
            "offline readout-assignment mitigation from archived IQM readiness "
            "manifest readout errors; no hardware submission"
        ),
        "limitations": [
            "uses one scalar readout error per measured physical qubit as a symmetric assignment channel",
            "does not correct gate errors, decoherence, leakage, or crosstalk",
            "periodic 100-CZ circuit therefore remains a hardware readout check, not a fully corrected dynamics result",
        ],
        "records": records,
        "table": rows,
    }
    write_json(args.output_json, summary)
    write_csv(args.output_csv, rows)

    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_csv}")
    for row in rows:
        if row["method"] != MITIGATED_METHOD:
            continue
        print(
            f"{row['dataset']} {row['case']}: "
            f"P_Gauss={float(row['P_Gauss']):.6f}, "
            f"<W>={float(row['wilson_expectation']):+.6f}"
        )


if __name__ == "__main__":
    main()
