#!/usr/bin/env python3
"""Mitigate the reduced periodic matter-only IQM readout.

This script is offline-only.  It uses the readout errors archived in the frozen
IQM readiness manifest as an independent symmetric assignment model for the four
measured matter bits.  It does not contact IQM and cannot correct algorithmic
gate errors, decoherence, leakage, or crosstalk.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401
from z2lgt.periodic_readout import analyze_matter_counts
from z2lgt.readout_mitigation import (
    mitigate_counts_independent,
    readout_probabilities_from_manifest,
)


RAW_METHOD = "raw"
MITIGATED_METHOD = "readout_mitigated_manifest_symmetric"

FIELDNAMES = [
    "dataset",
    "case",
    "wilson_sector",
    "method",
    "shots",
    "imbalance",
    "imbalance_se",
    "ideal_trotter_imbalance",
    "ideal_exact_imbalance",
    "negative_probability_mass",
    "condition_number",
    "max_readout_error",
    "mean_readout_error",
    "physical_qubits_by_classical_bit",
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


def _case_label(case: str) -> str:
    if case not in {"Wplus", "Wminus"}:
        raise ValueError(f"unexpected periodic matter case {case!r}")
    return case


def _ideal_from_metrics(metrics: dict[str, Any], case: str, prefix: str) -> float | str:
    key = f"{prefix}_{_case_label(case)}_imbalance"
    value = metrics.get(key, "")
    return float(value) if value != "" else ""


def matter_row(
    *,
    record: dict[str, Any],
    method: str,
    analysis: dict[str, Any],
    physics_metrics: dict[str, Any],
    mitigation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return one CSV-ready row for a raw or mitigated matter observable."""
    case = _case_label(str(record["case"]))
    return {
        "dataset": "periodic_matter_readout",
        "case": case,
        "wilson_sector": record["wilson_sector"],
        "method": method,
        "shots": analysis["shots"],
        "imbalance": analysis["imbalance"],
        "imbalance_se": analysis["imbalance_se"],
        "ideal_trotter_imbalance": _ideal_from_metrics(physics_metrics, case, "trotter"),
        "ideal_exact_imbalance": _ideal_from_metrics(physics_metrics, case, "exact"),
        "negative_probability_mass": ""
        if mitigation is None
        else mitigation["negative_probability_mass"],
        "condition_number": "" if mitigation is None else mitigation["condition_number"],
        "max_readout_error": "" if mitigation is None else mitigation["max_readout_error"],
        "mean_readout_error": "" if mitigation is None else mitigation["mean_readout_error"],
        "physical_qubits_by_classical_bit": ""
        if mitigation is None
        else " ".join(str(qubit) for qubit in mitigation["physical_qubits_by_classical_bit"]),
    }


def separation_summary(rows: list[dict[str, Any]], *, method: str) -> dict[str, float]:
    """Compute Wplus-Wminus imbalance separation and independent-shot error."""
    selected = {row["case"]: row for row in rows if row["method"] == method}
    if set(selected) != {"Wplus", "Wminus"}:
        raise ValueError(f"method {method!r} does not contain exactly Wplus and Wminus")
    plus = selected["Wplus"]
    minus = selected["Wminus"]
    separation = float(plus["imbalance"]) - float(minus["imbalance"])
    separation_se = math.sqrt(float(plus["imbalance_se"]) ** 2 + float(minus["imbalance_se"]) ** 2)
    return {
        "Wplus_minus_Wminus": separation,
        "combined_standard_error": separation_se,
        "z_score": separation / separation_se if separation_se > 0 else math.inf,
    }


def mitigate_periodic_matter(
    result_path: Path,
    manifest_path: Path,
    *,
    root: Path,
) -> dict[str, Any]:
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    physics_metrics = dict(manifest.get("physics_metrics", {}))
    output_records: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []

    if payload.get("candidate_id") != manifest.get("candidate_id"):
        raise ValueError("result candidate_id does not match manifest candidate_id")
    if payload.get("readout_mode") != "matter_only":
        raise ValueError("expected a matter_only periodic result")

    for record in payload["records"]:
        case = _case_label(str(record["case"]))
        raw_analysis = analyze_matter_counts(record["raw_counts"])
        rows.append(
            matter_row(
                record=record,
                method=RAW_METHOD,
                analysis=raw_analysis,
                physics_metrics=physics_metrics,
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
        mitigated_analysis = analyze_matter_counts(mitigated["mitigated_counts"])
        mitigation_summary = {
            **calibration,
            "negative_probability_mass": mitigated["negative_probability_mass"],
            "condition_number": mitigated["condition_number"],
            "solver": mitigated["solver"],
            "response_model": mitigated["response_model"],
        }
        rows.append(
            matter_row(
                record=record,
                method=MITIGATED_METHOD,
                analysis=mitigated_analysis,
                physics_metrics=physics_metrics,
                mitigation=mitigation_summary,
            )
        )
        output_records.append(
            {
                "dataset": "periodic_matter_readout",
                "case": case,
                "wilson_sector": record["wilson_sector"],
                "raw_counts": record["raw_counts"],
                "raw_analysis": raw_analysis,
                "mitigated_counts": mitigated["mitigated_counts"],
                "mitigated_analysis": mitigated_analysis,
                "mitigation": mitigation_summary,
            }
        )

    raw_separation = separation_summary(rows, method=RAW_METHOD)
    mitigated_separation = separation_summary(rows, method=MITIGATED_METHOD)
    trotter_separation = float(physics_metrics.get("trotter_sector_separation", math.nan))
    exact_separation = float(physics_metrics.get("exact_sector_separation", math.nan))

    return {
        "schema_version": 1,
        "method": MITIGATED_METHOD,
        "scope": (
            "offline readout-assignment mitigation of the reduced periodic "
            "matter-only IQM hardware result; no hardware submission"
        ),
        "source_result": str(result_path),
        "source_manifest": str(manifest_path),
        "candidate_id": manifest.get("candidate_id"),
        "job_id": payload.get("job_id"),
        "calibration_set_id": manifest.get("calibration_set_id"),
        "quantum_computer": manifest.get("quantum_computer"),
        "shots_per_circuit": payload.get("shots_per_circuit"),
        "readout_mode": payload.get("readout_mode"),
        "resources": {
            "native_cz_count": manifest.get("maximum_native_cz_count"),
            "native_depth": manifest.get("maximum_native_depth"),
            "max_readout_error": manifest.get("maximum_readout_error"),
        },
        "ideal_reference": {
            "trotter_Wplus_imbalance": physics_metrics.get("trotter_Wplus_imbalance"),
            "trotter_Wminus_imbalance": physics_metrics.get("trotter_Wminus_imbalance"),
            "trotter_sector_separation": physics_metrics.get("trotter_sector_separation"),
            "exact_Wplus_imbalance": physics_metrics.get("exact_Wplus_imbalance"),
            "exact_Wminus_imbalance": physics_metrics.get("exact_Wminus_imbalance"),
            "exact_sector_separation": physics_metrics.get("exact_sector_separation"),
            "minimum_state_fidelity": physics_metrics.get("minimum_state_fidelity"),
        },
        "separations": {
            RAW_METHOD: {
                **raw_separation,
                "fraction_of_trotter_separation": raw_separation["Wplus_minus_Wminus"]
                / trotter_separation,
                "fraction_of_exact_separation": raw_separation["Wplus_minus_Wminus"]
                / exact_separation,
            },
            MITIGATED_METHOD: {
                **mitigated_separation,
                "fraction_of_trotter_separation": mitigated_separation["Wplus_minus_Wminus"]
                / trotter_separation,
                "fraction_of_exact_separation": mitigated_separation["Wplus_minus_Wminus"]
                / exact_separation,
            },
        },
        "limitations": [
            "readout mitigation uses one scalar readout error per measured physical qubit as a symmetric assignment channel",
            "mitigated standard errors are approximate because the inverted distribution is represented as weighted counts",
            "matter-only readout cannot perform shot-level Gauss or Wilson postselection",
            "readout mitigation does not correct algorithmic gate errors, decoherence, leakage, or crosstalk",
        ],
        "records": output_records,
        "table": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--result",
        type=Path,
        default=Path("results/iqm/periodic_matter_hardware/periodic_matter_readout_5000.json"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("results/iqm/emerald_periodic_matter_candidate_5000/readiness_manifest.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("results/processed/periodic_iqm_matter_readout_mitigation_5000.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("results/processed/periodic_iqm_matter_readout_mitigation_5000.csv"),
    )
    args = parser.parse_args()

    summary = mitigate_periodic_matter(args.result, args.manifest, root=_bootstrap.ROOT)
    write_json(args.output_json, summary)
    write_csv(args.output_csv, summary["table"])

    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_csv}")
    for method, separation in summary["separations"].items():
        print(
            f"{method}: ΔO_LR={separation['Wplus_minus_Wminus']:.6f} +/- "
            f"{separation['combined_standard_error']:.6f}, "
            f"z={separation['z_score']:.2f}, "
            f"{100 * separation['fraction_of_trotter_separation']:.1f}% of Trotter"
        )


if __name__ == "__main__":
    main()
