#!/usr/bin/env python3
"""Run the approved six-circuit Sirius scan; dry-run by default."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import _bootstrap
from qiskit.qpy import load as qpy_load

from z2lgt.iqm_candidate import load_manifest
from z2lgt.periodic_readout import analyze_matter_counts
from z2lgt.sirius_periodic_matter_iqm_runner import (
    require_explicit_sirius_scan_hardware_consent,
    validate_sirius_scan_submission_manifest,
)


def provider_class():
    try:
        from iqm.qiskit_iqm import IQMProvider
    except ImportError as exc:
        raise RuntimeError(
            'install the IQM adapter with: pip install "iqm-client[qiskit]"'
        ) from exc
    return IQMProvider


def load_qpy_circuit(path: Path):
    with path.open("rb") as handle:
        circuits = qpy_load(handle)
    if len(circuits) != 1:
        raise PermissionError(
            f"expected exactly one circuit in {path}, found {len(circuits)}"
        )
    return circuits[0]


def write_json(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def point_summaries(
    records: list[dict[str, object]],
    physics_by_point: dict[tuple[float, float], dict[str, object]],
) -> list[dict[str, object]]:
    summaries = []
    for index in range(0, len(records), 2):
        plus, minus = records[index : index + 2]
        point = (float(plus["time"]), float(plus["dt"]))
        if point != (float(minus["time"]), float(minus["dt"])):
            raise RuntimeError("hardware results are not paired by time point")
        separation = float(plus["analysis"]["imbalance"]) - float(
            minus["analysis"]["imbalance"]
        )
        separation_se = math.sqrt(
            float(plus["analysis"]["imbalance_se"]) ** 2
            + float(minus["analysis"]["imbalance_se"]) ** 2
        )
        physics = physics_by_point[point]
        summaries.append(
            {
                "time": point[0],
                "dt": point[1],
                "trotter_steps": 2,
                "exact_sector_separation": physics["exact_sector_separation"],
                "trotter_sector_separation": physics[
                    "trotter_sector_separation"
                ],
                "hardware_sector_separation": separation,
                "hardware_sector_separation_absolute": abs(separation),
                "hardware_sector_separation_se": separation_se,
                "hardware_sector_separation_z": (
                    abs(separation) / separation_se if separation_se else None
                ),
            }
        )
    return summaries


def processed_rows(
    records: list[dict[str, object]],
    summaries: list[dict[str, object]],
    *,
    calibration_set_id: str,
    job_id: str,
) -> list[dict[str, object]]:
    summary_by_point = {
        (float(item["time"]), float(item["dt"])): item for item in summaries
    }
    rows = []
    for record in records:
        point = (float(record["time"]), float(record["dt"]))
        summary = summary_by_point[point]
        analysis = record["analysis"]
        rows.append(
            {
                "time": record["time"],
                "dt": record["dt"],
                "trotter_steps": record["trotter_steps"],
                "case": record["case"],
                "wilson_sector": record["wilson_sector"],
                "exact_O_LR": record["exact_O_LR"],
                "trotter_O_LR": record["trotter_O_LR"],
                "hardware_O_LR": analysis["imbalance"],
                "hardware_O_LR_se": analysis["imbalance_se"],
                "exact_sector_separation": summary["exact_sector_separation"],
                "trotter_sector_separation": summary[
                    "trotter_sector_separation"
                ],
                "hardware_sector_separation": summary[
                    "hardware_sector_separation"
                ],
                "hardware_sector_separation_se": summary[
                    "hardware_sector_separation_se"
                ],
                "hardware_sector_separation_z": summary[
                    "hardware_sector_separation_z"
                ],
                "shots": record["shots"],
                "depth": record["depth"],
                "r_count": record["r_count"],
                "cz_count": record["cz_count"],
                "move_count": record["move_count"],
                "calibration_set_id": calibration_set_id,
                "job_id": job_id,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("IQM_SERVER_URL"))
    parser.add_argument("--quantum-computer", default="sirius")
    parser.add_argument("--shots", type=int, default=5000)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "results/iqm/sirius_periodic_matter_scan_candidate_5000/"
            "readiness_manifest.json"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path(
            "results/iqm/sirius_periodic_matter_hardware/"
            "sirius_periodic_matter_scan_5000.json"
        ),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path(
            "results/processed/sirius_periodic_matter_hardware_scan_5000.csv"
        ),
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="submit the approved frozen candidate",
    )
    parser.add_argument(
        "--confirm-candidate",
        help="first 12 characters of the approved candidate ID",
    )
    parser.add_argument("--replicate-label")
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = load_manifest(manifest_path)
    qpy_paths = validate_sirius_scan_submission_manifest(
        manifest,
        root=_bootstrap.ROOT,
        expected_quantum_computer=args.quantum_computer,
        expected_shots=args.shots,
        expected_replicate_label=args.replicate_label,
    )
    require_explicit_sirius_scan_hardware_consent(
        submit=args.submit,
        environment=os.environ,
        candidate_id=manifest["candidate_id"],
        confirmation=args.confirm_candidate,
    )
    circuits = [load_qpy_circuit(path) for path in qpy_paths]
    report: dict[str, object] = {
        "schema_version": 1,
        "mode": "iqm-sirius-periodic-matter-three-point-scan",
        "candidate_id": manifest["candidate_id"],
        "calibration_set_id": manifest["calibration_set_id"],
        "quantum_computer": args.quantum_computer,
        "shots_per_circuit": args.shots,
        "points": manifest["points"],
        "replicate_label": manifest.get("replicate_label", "primary"),
        "readout_mode": "matter_only",
        "hypothesis": (
            "Larger ideal Trotter sector separation should improve hardware "
            "resolvability, subject to noise attenuation and statistical uncertainty."
        ),
        "submitted": False,
        "records": [],
        "point_summaries": [],
    }

    if not args.submit:
        report.update(
            {
                "status": "dry-run passed; frozen artifacts and approval verified",
                "request_sent": False,
                "backend_run_called": False,
                "hardware_credits_consumed": False,
                "circuits": [
                    {
                        "time": record["time"],
                        "dt": record["dt"],
                        "case": record["case"],
                        "qpy": record["qpy"],
                        "qpy_sha256": record["qpy_sha256"],
                        "mapping": record["logical_to_physical_components"],
                        "depth": record["depth"],
                        "r_count": record["r_count"],
                        "cz_count": record["cz_count"],
                        "move_count": record["move_count"],
                    }
                    for record in manifest["circuits"]
                ],
            }
        )
        write_json(args.output_json, report)
        print("Sirius periodic-matter scan dry-run")
        print(f"  candidate: {manifest['candidate_id']}")
        print(f"  calibration: {manifest['calibration_set_id']}")
        print(f"  circuits verified: {len(circuits)}")
        print(f"  shots per circuit: {args.shots}")
        print("  backend.run called: false")
        print("  hardware submitted: false")
        print(f"  report: {args.output_json}")
        return

    if not args.url:
        raise SystemExit("IQM server URL missing; set IQM_SERVER_URL")
    if not os.environ.get("IQM_TOKEN"):
        raise SystemExit("IQM_TOKEN is missing; load a valid raw token first")
    if manifest.get("server_url") != args.url:
        raise SystemExit("configured IQM server URL differs from frozen manifest")

    try:
        backend = provider_class()(
            args.url,
            quantum_computer=args.quantum_computer,
        ).get_backend(
            calibration_set_id=UUID(manifest["calibration_set_id"]),
            use_metrics=True,
        )
        backend.create_run_request(circuits, shots=args.shots)
        manifest["submission_started"] = True
        manifest["submission_started_at_utc"] = datetime.now(timezone.utc).isoformat()
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        job = backend.run(circuits, shots=args.shots)
        job_id = job.job_id()
        manifest.update(
            {
                "backend_run_called": True,
                "hardware_submitted": True,
                "hardware_credits_consumed": True,
                "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
                "job_id": job_id,
            }
        )
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        report.update(
            {
                "submitted": True,
                "status": "submitted; waiting for result",
                "job_id": job_id,
            }
        )
        write_json(args.output_json, report)
        print(f"Submitted Sirius periodic-matter scan: {job_id}")

        result = job.result()
        physics_by_point = {
            (float(item["time"]), float(item["dt"])): item
            for item in manifest["physics_metrics_by_point"]
        }
        records = []
        for index, (manifest_record, circuit) in enumerate(
            zip(manifest["circuits"], circuits, strict=True)
        ):
            counts = dict(result.get_counts(index))
            point = (
                float(manifest_record["time"]),
                float(manifest_record["dt"]),
            )
            physics = physics_by_point[point]
            prefix = "Wplus" if int(manifest_record["wilson_sector"]) == 1 else "Wminus"
            records.append(
                {
                    "time": point[0],
                    "dt": point[1],
                    "trotter_steps": int(manifest_record["trotter_steps"]),
                    "case": manifest_record["case"],
                    "wilson_sector": manifest_record["wilson_sector"],
                    "backend_name": str(backend.name),
                    "circuit_name": circuit.name,
                    "shots": args.shots,
                    "depth": manifest_record["depth"],
                    "r_count": manifest_record["r_count"],
                    "cz_count": manifest_record["cz_count"],
                    "move_count": manifest_record["move_count"],
                    "exact_O_LR": physics[f"exact_{prefix}_imbalance"],
                    "trotter_O_LR": physics[f"trotter_{prefix}_imbalance"],
                    "raw_counts": counts,
                    "analysis": analyze_matter_counts(counts),
                }
            )

        summaries = point_summaries(records, physics_by_point)
        report.update(
            {
                "status": "completed",
                "records": records,
                "point_summaries": summaries,
                "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
        manifest["result_completed"] = True
        manifest["result_completed_at_utc"] = report["completed_at_utc"]
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        write_json(args.output_json, report)
        write_csv(
            args.output_csv,
            processed_rows(
                records,
                summaries,
                calibration_set_id=str(manifest["calibration_set_id"]),
                job_id=str(job_id),
            ),
        )

        print("Sirius periodic-matter scan completed")
        for record in records:
            analysis = record["analysis"]
            print(
                f"  t={record['time']:g} {record['case']}: "
                f"O_LR={analysis['imbalance']:.6f} +/- "
                f"{analysis['imbalance_se']:.6f}"
            )
        for summary in summaries:
            print(
                f"  t={summary['time']:g} separation="
                f"{summary['hardware_sector_separation']:.6f} +/- "
                f"{summary['hardware_sector_separation_se']:.6f} "
                f"({summary['hardware_sector_separation_z']:.2f} sigma)"
            )
        print(f"  JSON: {args.output_json}")
        print(f"  CSV: {args.output_csv}")
    except Exception as exc:
        report["status"] = f"submission blocked or failed: {exc}"
        write_json(args.output_json, report)
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
