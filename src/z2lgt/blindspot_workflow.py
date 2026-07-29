"""Reproducible ideal/noisy workflow for the four-link blind-spot benchmark."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .blindspot_analysis import analyze_joint_counts, diagnostic_rows, response_matrix
from .blindspot_circuits import CASES, joint_diagnostic_circuit, syndrome_response_circuit
from .blindspot_model import BlindSpotModel, algebra_report
from .circuits import export_circuit, ideal_counts, resource_metrics
from .noise import NoiseConfig, noisy_counts


EXPECTED = {
    "no_error": {"P_Gauss": 1.0, "wilson_expectation": 1.0},
    "gauge_violating": {"P_Gauss": 0.0, "wilson_expectation": 1.0},
    "gauge_preserving_string": {"P_Gauss": 1.0, "wilson_expectation": -1.0},
}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ideal_processed_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    """Return the compact, presentation-facing rows for the ideal benchmark."""
    interpretations = {
        "no_error": "target state: Gauss checks pass and Wilson sector is correct",
        "gauge_violating": "detected by at least one local Gauss check",
        "gauge_preserving_string": "Gauss-only blind spot: physical local sector, wrong Wilson sector",
    }
    rows = []
    for record in payload["records"]:
        analysis = record["analysis"]
        rows.append(
            {
                "case": record["error_type"],
                "backend": record["backend_name"],
                "p_gauss": analysis["P_Gauss"],
                "p_gauss_err": analysis["P_Gauss_se"],
                "wilson": analysis["wilson_expectation"],
                "wilson_err": analysis["wilson_expectation_se"],
                "interpretation": interpretations[record["error_type"]],
            }
        )
    return rows


def write_ideal_processed_csv(
    payload: dict[str, object],
    path: Path = Path("results/processed/blindspot_ideal.csv"),
) -> Path:
    """Persist the required seven-column ideal result table."""
    rows = ideal_processed_rows(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def _execute(circuit, mode: str, shots: int, seed: int, config: NoiseConfig | None):
    if mode == "ideal":
        return ideal_counts(circuit, shots, seed)
    if mode == "noisy" and config is not None:
        return noisy_counts(circuit, shots, config, seed, optimization_level=0)
    raise ValueError(f"unsupported execution mode: {mode}")


def run_dataset(
    mode: str,
    *,
    shots: int = 20_000,
    seed: int = 12345,
    output_dir: Path = Path("results"),
    noise_config: NoiseConfig | None = None,
) -> dict[str, object]:
    """Run the three cases, response calibration, and depth scan."""
    if shots <= 0:
        raise ValueError("shots must be positive")
    if mode == "noisy" and noise_config is None:
        noise_config = NoiseConfig(single_qubit=0.001, two_qubit=0.01, readout=0.02)
    model = BlindSpotModel()
    records = []
    for offset, error_type in enumerate(CASES):
        circuit = joint_diagnostic_circuit(error_type)
        counts = _execute(circuit, mode, shots, seed + offset, noise_config)
        records.append(
            {
                "mode": mode,
                "backend_name": "AerSimulator" if mode == "ideal" else "AerSimulator-noisy",
                "shots": shots,
                "circuit_label": circuit.name,
                "error_type": error_type,
                "expected_gauss_sector": "+1 all checks" if EXPECTED[error_type]["P_Gauss"] else "violated",
                "expected_string_sector": "+1" if EXPECTED[error_type]["wilson_expectation"] > 0 else "-1",
                "expected": EXPECTED[error_type],
                "resource_metrics": resource_metrics(circuit),
                "raw_counts": counts,
                "analysis": analyze_joint_counts(counts),
            }
        )

    response_shots = max(1000, min(5000, shots // 4))
    response_records = []
    for true in range(16):
        circuit = syndrome_response_circuit(true)
        counts = _execute(circuit, mode, response_shots, seed + 100 + true, noise_config)
        response_records.append({"true_syndrome": true, "counts": counts})
    matrix = response_matrix(response_records)

    scan_shots = max(1000, min(5000, shots // 4))
    depth_scan = []
    for offset, layers in enumerate((0, 2, 4, 8, 16, 32)):
        circuit = joint_diagnostic_circuit("no_error", idle_layers=layers)
        counts = _execute(circuit, mode, scan_shots, seed + 300 + offset, noise_config)
        depth_scan.append(
            {
                "idle_layers": layers,
                "compiled_depth": resource_metrics(circuit)["depth"],
                "counts": counts,
                "analysis": analyze_joint_counts(counts),
            }
        )

    payload: dict[str, object] = {
        "schema_version": 1,
        "mode": mode,
        "backend_name": "AerSimulator" if mode == "ideal" else "AerSimulator-noisy",
        "shots": shots,
        "seed": seed,
        "model_metadata": model.metadata(),
        "noise_config": asdict(noise_config) if noise_config is not None else None,
        "records": records,
        "response": {
            "bit_order": "integer index of (W,G0,G1,G2), W least significant",
            "shots_per_column": response_shots,
            "raw_records": response_records,
            "matrix_measured_given_true": matrix.tolist(),
        },
        "depth_scan": depth_scan,
    }
    _write_json(output_dir / mode / "blindspot_minimal.json", payload)
    if mode == "ideal":
        write_ideal_processed_csv(
            payload,
            output_dir / "processed" / "blindspot_ideal.csv",
        )
    if mode == "noisy":
        _write_json(output_dir / "noisy" / "noise_config.json", asdict(noise_config))
    return payload


def export_minimal_circuits(output_dir: Path = Path("circuits/blindspot")) -> list[dict[str, object]]:
    exported = []
    for error_type in CASES:
        circuit = joint_diagnostic_circuit(error_type)
        paths = export_circuit(
            circuit,
            output_dir / "qasm" / error_type,
            qpy_stem=output_dir / "qiskit" / error_type,
        )
        exported.append({"error_type": error_type, **resource_metrics(circuit), **paths})
    return exported


def combine_results(
    ideal_path: Path = Path("results/ideal/blindspot_minimal.json"),
    noisy_path: Path = Path("results/noisy/blindspot_minimal.json"),
    output_dir: Path = Path("results/processed"),
    iqm_path: Path | None = None,
) -> dict[str, object]:
    datasets = {
        "ideal": json.loads(ideal_path.read_text(encoding="utf-8")),
        "noisy": json.loads(noisy_path.read_text(encoding="utf-8")),
    }
    if iqm_path is not None and iqm_path.exists():
        iqm = json.loads(iqm_path.read_text(encoding="utf-8"))
        if iqm.get("records"):
            datasets["iqm"] = iqm
    all_records = [record for dataset in datasets.values() for record in dataset["records"]]
    summary = {
        "schema_version": 1,
        "model_metadata": datasets["ideal"]["model_metadata"],
        "algebra": algebra_report(),
        "datasets": datasets,
        "diagnostic_table": diagnostic_rows(all_records),
    }
    _write_json(output_dir / "blindspot_summary.json", summary)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "diagnostic_table.csv").open("w", newline="", encoding="utf-8") as handle:
        rows = summary["diagnostic_table"]
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return summary
