#!/usr/bin/env python3
"""Run only a reviewed, frozen IQM blind-spot candidate; dry-run by default."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import _bootstrap
from qiskit.qpy import load as qpy_load

from z2lgt.blindspot_analysis import analyze_joint_counts
from z2lgt.blindspot_circuits import CASES, joint_diagnostic_circuit
from z2lgt.blindspot_model import BlindSpotModel
from z2lgt.blindspot_workflow import EXPECTED
from z2lgt.circuits import resource_metrics
from z2lgt.iqm_candidate import load_manifest, validate_submission_manifest


def provider_class():
    try:
        from iqm.qiskit_iqm import IQMProvider
    except ImportError as exc:
        raise RuntimeError('install the IQM adapter with: pip install "iqm-client[qiskit]"') from exc
    return IQMProvider


def load_qpy_circuit(path: Path):
    with path.open("rb") as handle:
        circuits = qpy_load(handle)
    if len(circuits) != 1:
        raise PermissionError(f"expected exactly one circuit in {path}, found {len(circuits)}")
    return circuits[0]


def write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("IQM_SERVER_URL"))
    parser.add_argument(
        "--quantum-computer", default=os.environ.get("IQM_QUANTUM_COMPUTER", "emerald")
    )
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--batch", default="blindspot-minimal")
    parser.add_argument("--submit", action="store_true", help="submit the approved frozen candidate")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("results/iqm/emerald_blindspot_candidate/readiness_manifest.json"),
    )
    parser.add_argument("--outdir", type=Path, default=Path("results/iqm"))
    args = parser.parse_args()

    output = args.outdir / "blindspot_minimal.json"
    report = {
        "mode": "iqm",
        "batch": args.batch,
        "shots": args.shots,
        "submitted": False,
        "quantum_computer": args.quantum_computer,
        "records": [],
    }
    if not args.submit:
        circuits = [joint_diagnostic_circuit(case) for case in CASES]
        report.update(
            {
                "status": "dry-run only; no provider connection and no submission",
                "circuits": [
                    {"error_type": case, **resource_metrics(circuit)}
                    for case, circuit in zip(CASES, circuits, strict=True)
                ],
                "next_step": "freeze and review a target-specific manifest before using --submit",
            }
        )
        write_report(output, report)
        return

    manifest_path = args.manifest.resolve()
    try:
        if os.environ.get("Z2LGT_ALLOW_IQM_HARDWARE") != "YES":
            raise PermissionError("set Z2LGT_ALLOW_IQM_HARDWARE=YES for explicit submission consent")
        if not args.url:
            raise PermissionError("IQM server URL missing; set IQM_SERVER_URL")
        if not os.environ.get("IQM_TOKEN"):
            raise PermissionError("IQM_TOKEN is missing; load it from the system keychain")
        manifest = load_manifest(manifest_path)
        qpy_paths = validate_submission_manifest(
            manifest,
            root=_bootstrap.ROOT,
            expected_quantum_computer=args.quantum_computer,
            expected_shots=args.shots,
        )
        if manifest.get("server_url") != args.url:
            raise PermissionError("configured IQM server URL differs from the frozen manifest")
        if manifest.get("batch") != args.batch:
            raise PermissionError("requested batch differs from the frozen manifest")

        provider = provider_class()(args.url, quantum_computer=args.quantum_computer)
        backend = provider.get_backend(
            calibration_set_id=UUID(manifest["calibration_set_id"]),
            use_metrics=True,
        )
        circuits = [load_qpy_circuit(path) for path in qpy_paths]
        backend.create_run_request(circuits, shots=args.shots)
        manifest["submission_started"] = True
        manifest["submission_started_at_utc"] = datetime.now(timezone.utc).isoformat()
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        job = backend.run(circuits, shots=args.shots)
        job_id = job.job_id()
        manifest["hardware_submitted"] = True
        manifest["submitted_at_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["job_id"] = job_id
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        report.update(
            {
                "submitted": True,
                "status": "submitted; waiting for result",
                "job_id": job_id,
                "candidate_id": manifest["candidate_id"],
                "calibration_set_id": manifest["calibration_set_id"],
            }
        )
        write_report(output, report)
        result = job.result()
        records = []
        for index, (case, circuit) in enumerate(zip(CASES, circuits, strict=True)):
            counts = dict(result.get_counts(index))
            records.append(
                {
                    "mode": "iqm",
                    "backend_name": str(backend.name),
                    "quantum_computer": args.quantum_computer,
                    "calibration_set_id": manifest["calibration_set_id"],
                    "shots": args.shots,
                    "circuit_label": circuit.name,
                    "error_type": case,
                    "expected": EXPECTED[case],
                    "raw_counts": counts,
                    "analysis": analyze_joint_counts(counts),
                }
            )
        report.update(
            {
                "submitted": True,
                "status": "completed",
                "job_id": job_id,
                "backend_name": str(backend.name),
                "candidate_id": manifest["candidate_id"],
                "calibration_set_id": manifest["calibration_set_id"],
                "model_metadata": BlindSpotModel().metadata(),
                "records": records,
            }
        )
    except Exception as exc:
        report["status"] = f"submission blocked or failed: {exc}"
        write_report(output, report)
        raise SystemExit(str(exc)) from exc
    write_report(output, report)


if __name__ == "__main__":
    main()
