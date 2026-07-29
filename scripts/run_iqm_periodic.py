#!/usr/bin/env python3
"""Run the approved frozen periodic IQM candidate; dry-run by default."""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import _bootstrap
from qiskit.qpy import load as qpy_load

from z2lgt.iqm_candidate import load_manifest
from z2lgt.periodic_iqm_runner import (
    require_explicit_periodic_hardware_consent,
    validate_periodic_hardware_manifest,
)
from z2lgt.periodic_readout import analyze_periodic_joint_counts


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


def processed_rows(records: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for record in records:
        analysis = record["analysis"]
        rows.append(
            {
                "case": record["case"],
                "wilson_sector": record["wilson_sector"],
                "shots": record["shots"],
                "P_Gauss": analysis["P_Gauss"],
                "P_Gauss_se": analysis["P_Gauss_se"],
                "wilson_expectation": analysis["wilson_expectation"],
                "wilson_target_probability": analysis[
                    "wilson_target_probability"
                ],
                "imbalance": analysis["imbalance"],
                "imbalance_se": analysis["imbalance_se"],
                "gauss_only_imbalance": analysis["gauss_only_imbalance"],
                "gauss_plus_wilson_imbalance": analysis[
                    "gauss_plus_wilson_imbalance"
                ],
                "gauss_only_acceptance": analysis["gauss_only_acceptance"],
                "gauss_plus_wilson_acceptance": analysis[
                    "gauss_plus_wilson_acceptance"
                ],
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("IQM_SERVER_URL"))
    parser.add_argument(
        "--quantum-computer",
        default=os.environ.get("IQM_QUANTUM_COMPUTER", "emerald"),
    )
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "results/iqm/emerald_periodic_candidate/readiness_manifest.json"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("results/iqm/periodic_hardware/periodic_joint_readout.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("results/processed/periodic_iqm_joint_readout.csv"),
    )
    parser.add_argument(
        "--submit", action="store_true", help="execute the approved frozen hardware run"
    )
    parser.add_argument(
        "--confirm-candidate",
        help="first 12 characters of the approved candidate ID",
    )
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = load_manifest(manifest_path)
    qpy_paths = validate_periodic_hardware_manifest(
        manifest,
        root=_bootstrap.ROOT,
        expected_quantum_computer=args.quantum_computer,
        expected_shots=args.shots,
    )
    require_explicit_periodic_hardware_consent(
        submit=args.submit,
        environment=os.environ,
        candidate_id=manifest["candidate_id"],
        confirmation=args.confirm_candidate,
    )
    circuits = [load_qpy_circuit(path) for path in qpy_paths]
    report: dict[str, object] = {
        "schema_version": 1,
        "mode": "iqm-periodic",
        "candidate_id": manifest["candidate_id"],
        "calibration_set_id": manifest["calibration_set_id"],
        "quantum_computer": args.quantum_computer,
        "shots_per_circuit": args.shots,
        "time": manifest["time"],
        "dt": manifest["dt"],
        "submitted": False,
        "records": [],
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
                        "case": record["case"],
                        "qpy": record["qpy"],
                        "qpy_sha256": record["qpy_sha256"],
                        "mapping": record["logical_to_physical"],
                        "depth": record["depth"],
                        "cz_count": record["cz_count"],
                    }
                    for record in manifest["circuits"]
                ],
            }
        )
        write_json(args.output_json, report)
        print("Periodic IQM runner dry-run")
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
        raise SystemExit(
            "IQM_TOKEN is missing; source scripts/activate_iqm_emerald.zsh"
        )
    if manifest.get("server_url") != args.url:
        raise SystemExit("configured IQM server URL differs from frozen manifest")

    try:
        provider = provider_class()(args.url, quantum_computer=args.quantum_computer)
        backend = provider.get_backend(
            calibration_set_id=UUID(manifest["calibration_set_id"]),
            use_metrics=True,
        )
        backend.create_run_request(circuits, shots=args.shots)
        manifest["hardware_execution_started"] = True
        manifest["hardware_execution_started_at_utc"] = datetime.now(
            timezone.utc
        ).isoformat()
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
        print(f"Submitted IQM periodic job: {job_id}")
        print(f"Job identity recorded in: {manifest_path}")

        result = job.result()
        records = []
        for index, (manifest_record, circuit) in enumerate(
            zip(manifest["circuits"], circuits, strict=True)
        ):
            counts = dict(result.get_counts(index))
            records.append(
                {
                    "case": manifest_record["case"],
                    "wilson_sector": manifest_record["wilson_sector"],
                    "backend_name": str(backend.name),
                    "circuit_name": circuit.name,
                    "shots": args.shots,
                    "raw_counts": counts,
                    "analysis": analyze_periodic_joint_counts(counts),
                }
            )
        plus, minus = records
        report.update(
            {
                "status": "completed",
                "records": records,
                "measured_wilson_contrast": (
                    plus["analysis"]["wilson_expectation"]
                    - minus["analysis"]["wilson_expectation"]
                ),
                "measured_raw_imbalance_separation": abs(
                    plus["analysis"]["imbalance"]
                    - minus["analysis"]["imbalance"]
                ),
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
        write_csv(args.output_csv, processed_rows(records))
        print("Periodic IQM result completed")
        for record in records:
            analysis = record["analysis"]
            print(
                f"  {record['case']}: P_Gauss={analysis['P_Gauss']:.6f} "
                f"<W>={analysis['wilson_expectation']:.6f} "
                f"O_LR={analysis['imbalance']:.6f} +/- "
                f"{analysis['imbalance_se']:.6f}"
            )
        print(
            "  raw imbalance separation: "
            f"{report['measured_raw_imbalance_separation']:.6f}"
        )
        print(f"  JSON: {args.output_json}")
        print(f"  CSV: {args.output_csv}")
    except Exception as exc:
        report["status"] = f"hardware execution blocked or failed: {exc}"
        write_json(args.output_json, report)
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
