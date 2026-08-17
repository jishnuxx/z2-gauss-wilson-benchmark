#!/usr/bin/env python3
"""Run the frozen static IQM response-mitigation candidate; dry-run by default."""

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

from z2lgt.blindspot_analysis import analyze_joint_counts
from z2lgt.blindspot_circuits import CASES
from z2lgt.blindspot_model import BlindSpotModel
from z2lgt.blindspot_response_iqm import (
    require_explicit_response_hardware_consent,
    validate_blindspot_response_manifest,
)
from z2lgt.blindspot_workflow import EXPECTED
from z2lgt.iqm_candidate import load_manifest
from z2lgt.readout_mitigation import (
    mitigate_counts_with_response_matrix,
    response_matrix_from_calibration_records,
)


FIELDNAMES = [
    "case",
    "method",
    "shots",
    "P_Gauss",
    "wilson_expectation",
    "gauss_plus_string_acceptance",
    "negative_probability_mass",
    "condition_number",
    "expected_P_Gauss",
    "expected_wilson_expectation",
]


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


def write_json(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def analysis_row(
    *,
    case: str,
    method: str,
    analysis: dict[str, object],
    mitigation: dict[str, object] | None = None,
) -> dict[str, object]:
    expected = EXPECTED[case]
    return {
        "case": case,
        "method": method,
        "shots": analysis["shots"],
        "P_Gauss": analysis["P_Gauss"],
        "wilson_expectation": analysis["wilson_expectation"],
        "gauss_plus_string_acceptance": analysis["gauss_plus_string_acceptance"],
        "negative_probability_mass": "" if mitigation is None else mitigation["negative_probability_mass"],
        "condition_number": "" if mitigation is None else mitigation["condition_number"],
        "expected_P_Gauss": expected["P_Gauss"],
        "expected_wilson_expectation": expected["wilson_expectation"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("IQM_SERVER_URL"))
    parser.add_argument(
        "--quantum-computer",
        default=os.environ.get("IQM_QUANTUM_COMPUTER", "emerald"),
    )
    parser.add_argument("--shots", type=int, default=5000)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("results/iqm/emerald_blindspot_response_candidate_5000/readiness_manifest.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("results/iqm/static_blindspot_response_mitigated/blindspot_response_mitigated.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("results/processed/static_iqm_response_mitigation.csv"),
    )
    parser.add_argument("--submit", action="store_true", help="submit the approved frozen candidate")
    parser.add_argument(
        "--confirm-candidate",
        help="first 12 characters of the approved candidate ID",
    )
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = load_manifest(manifest_path)
    qpy_paths = validate_blindspot_response_manifest(
        manifest,
        root=_bootstrap.ROOT,
        expected_quantum_computer=args.quantum_computer,
        expected_shots=args.shots,
    )
    require_explicit_response_hardware_consent(
        submit=args.submit,
        environment=os.environ,
        candidate_id=manifest["candidate_id"],
        confirmation=args.confirm_candidate,
    )
    circuits = [load_qpy_circuit(path) for path in qpy_paths]
    report: dict[str, object] = {
        "schema_version": 1,
        "mode": "iqm-static-response-mitigation",
        "candidate_id": manifest["candidate_id"],
        "calibration_set_id": manifest["calibration_set_id"],
        "quantum_computer": args.quantum_computer,
        "shots_per_circuit": args.shots,
        "submitted": False,
        "records": [],
        "response_records": [],
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
                        "kind": record["kind"],
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
        print("Static IQM response-mitigation runner dry-run")
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
        raise SystemExit("IQM_TOKEN is missing; source scripts/activate_iqm_emerald.zsh")
    if manifest.get("server_url") != args.url:
        raise SystemExit("configured IQM server URL differs from frozen manifest")

    try:
        provider = provider_class()(args.url, quantum_computer=args.quantum_computer)
        backend = provider.get_backend(
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
        report.update({"submitted": True, "status": "submitted; waiting for result", "job_id": job_id})
        write_json(args.output_json, report)
        print(f"Submitted IQM static response-mitigation job: {job_id}")

        result = job.result()
        data_records = []
        response_records = []
        for index, (manifest_record, circuit) in enumerate(
            zip(manifest["circuits"], circuits, strict=True)
        ):
            counts = dict(result.get_counts(index))
            if manifest_record["kind"] == "data":
                case = str(manifest_record["case"])
                data_records.append(
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
            else:
                response_records.append(
                    {
                        "true_syndrome": int(manifest_record["true_syndrome"]),
                        "raw_counts": counts,
                    }
                )

        response_matrix = response_matrix_from_calibration_records(
            response_records,
            n_bits=4,
        )
        table_rows: list[dict[str, object]] = []
        mitigated_records = []
        for record in data_records:
            case = str(record["error_type"])
            table_rows.append(
                analysis_row(case=case, method="raw", analysis=record["analysis"])
            )
            mitigation = mitigate_counts_with_response_matrix(
                record["raw_counts"],
                response_matrix,
            )
            mitigated_analysis = analyze_joint_counts(mitigation["mitigated_counts"])
            mitigation_summary = {
                "method": "hardware_response_matrix_16x16",
                "negative_probability_mass": mitigation["negative_probability_mass"],
                "condition_number": mitigation["condition_number"],
                "solver": mitigation["solver"],
            }
            table_rows.append(
                analysis_row(
                    case=case,
                    method="hardware_response_matrix_16x16",
                    analysis=mitigated_analysis,
                    mitigation=mitigation_summary,
                )
            )
            mitigated_records.append(
                {
                    **record,
                    "response_mitigated_counts": mitigation["mitigated_counts"],
                    "response_mitigated_analysis": mitigated_analysis,
                    "mitigation": mitigation_summary,
                }
            )

        report.update(
            {
                "submitted": True,
                "status": "completed",
                "job_id": job_id,
                "backend_name": str(backend.name),
                "model_metadata": BlindSpotModel().metadata(),
                "records": mitigated_records,
                "response_records": response_records,
                "response_matrix_measured_given_true": response_matrix.tolist(),
                "table": table_rows,
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
        write_csv(args.output_csv, table_rows)
        print("Static IQM response-mitigation result completed")
        for row in table_rows:
            print(
                f"  {row['case']} {row['method']}: "
                f"P_Gauss={float(row['P_Gauss']):.6f}, "
                f"<W>={float(row['wilson_expectation']):+.6f}"
            )
        print(f"  JSON: {args.output_json}")
        print(f"  CSV: {args.output_csv}")
    except Exception as exc:
        report["status"] = f"submission blocked or failed: {exc}"
        write_json(args.output_json, report)
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
