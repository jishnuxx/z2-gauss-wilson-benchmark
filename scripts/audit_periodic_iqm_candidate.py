#!/usr/bin/env python3
"""Audit periodic joint-readout candidates against IQM without hardware execution."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

import _bootstrap
from qiskit import transpile

from z2lgt.periodic_iqm_audit import (
    DEFAULT_CANDIDATES,
    algorithmic_candidate_metrics,
    apply_algorithmic_gate,
    parse_candidate,
    physical_operation_qubits,
    recommended_candidate,
    write_audit,
)
from z2lgt.periodic_readout import periodic_joint_readout_circuit


def provider_class():
    try:
        from iqm.qiskit_iqm import IQMProvider
    except ImportError as exc:
        raise RuntimeError(
            'install the IQM adapter with: pip install "iqm-client[qiskit]"'
        ) from exc
    return IQMProvider


def instruction_properties(properties) -> dict[str, float | None]:
    return {
        "duration_seconds": (
            None
            if properties is None or properties.duration is None
            else float(properties.duration)
        ),
        "error": (
            None
            if properties is None or properties.error is None
            else float(properties.error)
        ),
    }


def logical_to_physical(source, compiled) -> list[int]:
    if compiled.layout is None or compiled.layout.initial_layout is None:
        raise RuntimeError("transpiled circuit has no initial layout")
    return [
        int(compiled.layout.initial_layout[source.qubits[index]])
        for index in range(source.num_qubits)
    ]


def physical_pairs(compiled, mapping: list[int], operation: str) -> list[tuple[int, int]]:
    pairs = physical_operation_qubits(compiled, mapping, operation)
    if any(len(pair) != 2 for pair in pairs):
        raise RuntimeError(f"expected two-qubit operation for {operation}")
    return [(pair[0], pair[1]) for pair in pairs]


def physical_measurements(compiled, mapping: list[int]) -> list[int]:
    measured = physical_operation_qubits(compiled, mapping, "measure")
    if any(len(qubits) != 1 for qubits in measured):
        raise RuntimeError("expected one-qubit measurement operations")
    return sorted(qubits[0] for qubits in measured)


def resolve_symmetric_key(target, operation: str, pair: tuple[int, int]):
    for key in target[operation]:
        if set(key) == set(pair):
            return key
    raise RuntimeError(f"mapped {operation} pair is absent from target: {pair}")


def calibrated_circuit_record(source, compiled, backend, sector: str) -> dict[str, object]:
    mapping = logical_to_physical(source, compiled)
    cz_keys = sorted(
        {
            resolve_symmetric_key(backend.target, "cz", pair)
            for pair in physical_pairs(compiled, mapping, "cz")
        }
    )
    measured = physical_measurements(compiled, mapping)
    return {
        "sector": sector,
        "logical_to_physical": mapping,
        "depth": int(compiled.depth()),
        "cz_count": int(compiled.count_ops().get("cz", 0)),
        "two_qubit_gate_count": int(compiled.num_nonlocal_gates()),
        "operations": {
            str(name): int(count) for name, count in compiled.count_ops().items()
        },
        "unique_cz_pairs": [
            {
                "physical_qubits": list(pair),
                **instruction_properties(backend.target["cz"][pair]),
            }
            for pair in cz_keys
        ],
        "measurements": [
            {
                "physical_qubit": qubit,
                **instruction_properties(backend.target["measure"][(qubit,)]),
            }
            for qubit in measured
        ],
    }


def finite_errors(records: list[dict[str, object]], key: str) -> list[float]:
    values: list[float] = []
    for record in records:
        for item in record[key]:
            if item["error"] is not None:
                values.append(float(item["error"]))
    return values


def attach_backend_metrics(
    candidates: list[dict[str, object]],
    *,
    backend,
    optimization_level: int,
    seed_transpiler: int,
    shots: int,
) -> object:
    sources = []
    labels: list[tuple[int, str]] = []
    for index, row in enumerate(candidates):
        for sector, sign in (("Wplus", 1), ("Wminus", -1)):
            sources.append(
                periodic_joint_readout_circuit(
                    float(row["time"]),
                    float(row["dt"]),
                    wilson_sector=sign,
                )
            )
            labels.append((index, sector))
    compiled = transpile(
        sources,
        backend=backend,
        optimization_level=optimization_level,
        seed_transpiler=seed_transpiler,
    )
    # This performs client-side request validation only.  It does not enqueue a
    # job and is intentionally the closest this script gets to execution.
    request = backend.create_run_request(compiled, shots=shots)
    grouped: list[list[dict[str, object]]] = [[] for _ in candidates]
    for source, circuit, (index, sector) in zip(
        sources, compiled, labels, strict=True
    ):
        grouped[index].append(
            calibrated_circuit_record(source, circuit, backend, sector)
        )
    for row, records in zip(candidates, grouped, strict=True):
        cz_errors = finite_errors(records, "unique_cz_pairs")
        readout_errors = finite_errors(records, "measurements")
        row["iqm_circuits"] = records
        row["native_max_depth"] = max(int(item["depth"]) for item in records)
        row["native_max_cz_count"] = max(int(item["cz_count"]) for item in records)
        row["maximum_cz_error"] = max(cz_errors) if cz_errors else None
        row["maximum_readout_error"] = (
            max(readout_errors) if readout_errors else None
        )
        row["request_validated"] = True
    return request


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        action="append",
        metavar="TIME:DT",
        help="candidate to audit; repeat for multiple candidates",
    )
    parser.add_argument("--url", default=os.environ.get("IQM_SERVER_URL"))
    parser.add_argument(
        "--quantum-computer",
        default=os.environ.get("IQM_QUANTUM_COMPUTER", "emerald"),
    )
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--optimization-level", type=int, default=3, choices=range(4))
    parser.add_argument("--seed-transpiler", type=int, default=7)
    parser.add_argument("--min-fidelity", type=float, default=0.85)
    parser.add_argument("--min-separation-retained", type=float, default=0.60)
    parser.add_argument("--min-trotter-separation", type=float, default=0.10)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="compute physics and source resources without connecting to IQM",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("results/iqm/periodic_candidate_audit.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("results/processed/periodic_candidate_audit.csv"),
    )
    args = parser.parse_args()
    if args.shots <= 0:
        raise SystemExit("shots must be positive")
    for name in (
        "min_fidelity",
        "min_separation_retained",
        "min_trotter_separation",
    ):
        value = getattr(args, name)
        if not 0 <= value <= 1:
            raise SystemExit(f"--{name.replace('_', '-')} must lie in [0, 1]")

    try:
        specifications = (
            [parse_candidate(value) for value in args.candidate]
            if args.candidate
            else list(DEFAULT_CANDIDATES)
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    candidates = [algorithmic_candidate_metrics(*spec) for spec in specifications]
    thresholds = {
        "minimum_state_fidelity": args.min_fidelity,
        "minimum_separation_retained": args.min_separation_retained,
        "minimum_trotter_sector_separation": args.min_trotter_separation,
    }
    for row in candidates:
        apply_algorithmic_gate(
            row,
            min_fidelity=args.min_fidelity,
            min_separation_retained=args.min_separation_retained,
            min_trotter_separation=args.min_trotter_separation,
        )

    backend_summary: dict[str, object]
    request_type = None
    if args.offline:
        backend_summary = {
            "status": "offline_not_connected",
            "quantum_computer_requested": args.quantum_computer,
        }
    else:
        if not args.url:
            raise SystemExit("IQM server URL missing; set IQM_SERVER_URL")
        if not os.environ.get("IQM_TOKEN"):
            raise SystemExit("IQM_TOKEN is missing; source scripts/activate_iqm_emerald.zsh")
        provider = provider_class()(args.url, quantum_computer=args.quantum_computer)
        backend = provider.get_backend(use_metrics=True)
        request = attach_backend_metrics(
            candidates,
            backend=backend,
            optimization_level=args.optimization_level,
            seed_transpiler=args.seed_transpiler,
            shots=args.shots,
        )
        request_type = type(request).__name__
        backend_summary = {
            "status": "connected_request_validated",
            "backend_name": str(backend.name),
            "quantum_computer": args.quantum_computer,
            "backend_qubit_count": int(backend.num_qubits),
            "native_operations": list(backend.operation_names),
            "calibration_set_id": str(backend.architecture.calibration_set_id),
            "use_metrics": True,
        }

    choice = recommended_candidate(candidates)
    for row in candidates:
        row["recommended"] = row["candidate"] == choice
    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "No-credit feasibility audit for periodic observable-aware certification"
        ),
        "safety": {
            "backend_run_called": False,
            "job_submitted": False,
            "hardware_credits_consumed": False,
            "request_validation_only": not args.offline,
        },
        "configuration": {
            "shots_for_request_validation": args.shots,
            "optimization_level": args.optimization_level,
            "seed_transpiler": args.seed_transpiler,
            "algorithmic_thresholds": thresholds,
            "selection_rule": (
                "among threshold-passing candidates, minimize native CZ count and "
                "native depth, then maximize Trotter sector separation"
            ),
        },
        "backend": backend_summary,
        "request_type": request_type,
        "recommended_candidate": choice,
        "audit_outcome": (
            "candidate_ready_for_human_review"
            if choice is not None and not args.offline
            else "offline_physics_screen_complete"
            if choice is not None
            else "no_candidate_passed_algorithmic_gate"
        ),
        "hardware_go_no_go": "human_review_required" if not args.offline else "not_assessed",
        "candidates": candidates,
    }
    json_path, csv_path = write_audit(report, args.output_json, args.output_csv)

    print("Periodic IQM candidate audit")
    print(f"  mode: {'offline' if args.offline else 'IQM request validation'}")
    print(f"  candidates: {len(candidates)}")
    print("  candidate | steps | Trotter separation | min fidelity | native CZ | gate")
    for row in candidates:
        native = row.get("native_max_cz_count")
        print(
            f"  {row['candidate']:>13} | {int(row['trotter_steps']):5d} | "
            f"{float(row['trotter_sector_separation']):18.6f} | "
            f"{float(row['minimum_state_fidelity']):12.6f} | "
            f"{str(native) if native is not None else 'offline':>9} | "
            f"{'PASS' if row['algorithmic_gate_passed'] else 'FAIL'}"
        )
    print(f"  recommended: {choice}")
    print(f"  JSON: {json_path}")
    print(f"  CSV: {csv_path}")
    print("  backend.run called: false")
    print("  hardware submitted: false")


if __name__ == "__main__":
    main()
