#!/usr/bin/env python3
"""Freeze the static IQM blind-spot batch with 16 response calibration circuits.

This script performs tests, target transpilation, calibration-metric checks,
artifact export, hashing, and client-side request validation.  It never calls
``backend.run``.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import _bootstrap
from qiskit import qasm2, transpile
from qiskit.qpy import dump as qpy_dump

from z2lgt.blindspot_response_iqm import RESPONSE_BATCH, response_mitigation_circuit_specs
from z2lgt.iqm_candidate import candidate_id, sha256_file
from z2lgt.periodic_iqm_audit import physical_operation_qubits


def provider_class():
    try:
        from iqm.qiskit_iqm import IQMProvider
    except ImportError as exc:
        raise RuntimeError('install the IQM adapter with: pip install "iqm-client[qiskit]"') from exc
    return IQMProvider


def instruction_properties(properties) -> dict[str, float | None]:
    return {
        "duration_seconds": None if properties is None or properties.duration is None else float(properties.duration),
        "error": None if properties is None or properties.error is None else float(properties.error),
    }


def resolve_symmetric_key(target, operation: str, qubits: tuple[int, ...]):
    for key in target[operation]:
        if set(key) == set(qubits):
            return key
    raise RuntimeError(f"mapped {operation} qubits are absent from target: {qubits}")


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(_bootstrap.ROOT))
    except ValueError:
        return str(path.resolve())


def finite_errors(items: list[dict[str, object]]) -> list[float]:
    return [float(item["error"]) for item in items if item["error"] is not None]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("IQM_SERVER_URL"))
    parser.add_argument(
        "--quantum-computer",
        default=os.environ.get("IQM_QUANTUM_COMPUTER", "emerald"),
    )
    parser.add_argument("--shots", type=int, default=5000)
    parser.add_argument("--optimization-level", type=int, default=3, choices=range(4))
    parser.add_argument("--seed-transpiler", type=int, default=7)
    parser.add_argument("--max-native-depth", type=int, default=30)
    parser.add_argument("--max-native-cz", type=int, default=12)
    parser.add_argument("--max-cz-error", type=float, default=0.015)
    parser.add_argument("--max-readout-error", type=float, default=0.025)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/iqm/emerald_blindspot_response_candidate_5000"),
    )
    parser.add_argument("--force", action="store_true", help="replace an unsubmitted candidate")
    args = parser.parse_args()

    if not args.url:
        raise SystemExit("IQM server URL missing; set IQM_SERVER_URL")
    if not os.environ.get("IQM_TOKEN"):
        raise SystemExit("IQM_TOKEN is missing; source scripts/activate_iqm_emerald.zsh")
    if args.shots <= 0:
        raise SystemExit("shots must be positive")

    outdir = args.outdir.resolve()
    manifest_path = outdir / "readiness_manifest.json"
    if manifest_path.exists() and not args.force:
        raise SystemExit(f"candidate already exists: {manifest_path}; inspect it or pass --force")
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        if old.get("hardware_submitted") is True:
            raise SystemExit("refusing to overwrite a candidate already marked as submitted")

    tests = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=_bootstrap.ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if tests.returncode != 0:
        print(tests.stdout + tests.stderr)
        raise SystemExit("test gate failed; candidate was not frozen")

    provider = provider_class()(args.url, quantum_computer=args.quantum_computer)
    backend = provider.get_backend(use_metrics=True)
    specs = response_mitigation_circuit_specs()
    sources = [spec["circuit"] for spec in specs]
    compiled = transpile(
        sources,
        backend=backend,
        optimization_level=args.optimization_level,
        seed_transpiler=args.seed_transpiler,
    )
    request = backend.create_run_request(compiled, shots=args.shots)

    circuit_dir = outdir / "circuits"
    circuit_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for spec, source, circuit in zip(specs, sources, compiled, strict=True):
        mapping = [
            int(circuit.layout.initial_layout[source.qubits[index]])
            for index in range(source.num_qubits)
        ]
        cz_keys = sorted(
            {
                resolve_symmetric_key(backend.target, "cz", pair)
                for pair in physical_operation_qubits(circuit, mapping, "cz")
            }
        )
        measured = sorted(
            qubits[0]
            for qubits in physical_operation_qubits(circuit, mapping, "measure")
        )
        qpy_path = circuit_dir / f"{spec['label']}.qpy"
        qasm_path = circuit_dir / f"{spec['label']}.qasm"
        with qpy_path.open("wb") as handle:
            qpy_dump(circuit, handle)
        qasm_path.write_text(qasm2.dumps(circuit), encoding="utf-8")
        record = {
            "kind": spec["kind"],
            "case": spec["case"],
            "logical_to_physical": mapping,
            "depth": int(circuit.depth()),
            "cz_count": int(circuit.count_ops().get("cz", 0)),
            "two_qubit_gate_count": int(circuit.num_nonlocal_gates()),
            "operations": {
                str(name): int(count)
                for name, count in circuit.count_ops().items()
            },
            "cz_pairs": [
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
            "qpy": relative(qpy_path),
            "qpy_sha256": sha256_file(qpy_path),
            "qasm": relative(qasm_path),
            "qasm_sha256": sha256_file(qasm_path),
        }
        if "true_syndrome" in spec:
            record["true_syndrome"] = int(spec["true_syndrome"])
        records.append(record)

    mappings = {tuple(record["logical_to_physical"]) for record in records}
    max_depth = max(int(record["depth"]) for record in records)
    max_cz = max(int(record["cz_count"]) for record in records)
    cz_errors = finite_errors([item for record in records for item in record["cz_pairs"]])
    readout_errors = finite_errors(
        [item for record in records for item in record["measurements"]]
    )
    maximum_cz_error = max(cz_errors) if cz_errors else None
    maximum_readout_error = max(readout_errors) if readout_errors else None
    hardware_checks = {
        "same_mapping_for_all_circuits": len(mappings) == 1,
        "maximum_native_depth": max_depth <= args.max_native_depth,
        "maximum_native_cz_count": max_cz <= args.max_native_cz,
        "maximum_cz_error": maximum_cz_error is not None and maximum_cz_error <= args.max_cz_error,
        "maximum_readout_error": (
            maximum_readout_error is not None
            and maximum_readout_error <= args.max_readout_error
        ),
    }
    if not all(hardware_checks.values()):
        failed = [name for name, passed in hardware_checks.items() if not passed]
        raise SystemExit("hardware freeze gate failed: " + ", ".join(failed))

    calibration_set_id = str(backend.architecture.calibration_set_id)
    identity = {
        "batch": RESPONSE_BATCH,
        "server_url": args.url,
        "quantum_computer": args.quantum_computer,
        "calibration_set_id": calibration_set_id,
        "shots": args.shots,
        "optimization_level": args.optimization_level,
        "seed_transpiler": args.seed_transpiler,
        "qpy_sha256": [record["qpy_sha256"] for record in records],
    }
    manifest = {
        "schema_version": 1,
        "candidate_id": candidate_id(identity),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        **identity,
        "backend_name": str(backend.name),
        "backend_qubit_count": int(backend.num_qubits),
        "native_operations": list(backend.operation_names),
        "use_metrics": True,
        "request_type": type(request).__name__,
        "response_syndromes": list(range(16)),
        "hardware_thresholds": {
            "maximum_native_depth": args.max_native_depth,
            "maximum_native_cz_count": args.max_native_cz,
            "maximum_cz_error": args.max_cz_error,
            "maximum_readout_error": args.max_readout_error,
        },
        "hardware_checks": hardware_checks,
        "maximum_native_depth": max_depth,
        "maximum_native_cz_count": max_cz,
        "maximum_cz_error": maximum_cz_error,
        "maximum_readout_error": maximum_readout_error,
        "all_tests_passed": True,
        "test_output": (tests.stdout + tests.stderr).strip(),
        "request_validated": True,
        "circuits_frozen": True,
        "human_review_approved": False,
        "submission_started": False,
        "hardware_submitted": False,
        "hardware_credits_consumed": False,
        "backend_run_called": False,
        "circuits": records,
        "review_note": (
            "Review the 19-circuit static response-mitigation batch.  The first "
            "three circuits are data circuits; the next 16 calibrate the "
            "(W,G0,G1,G2) diagnostic response matrix."
        ),
    }
    outdir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Frozen response-mitigation candidate: {manifest_path}")
    print(f"Candidate ID: {manifest['candidate_id']}")
    print(f"Calibration set: {calibration_set_id}")
    print(f"Circuits: {len(records)}")
    print(f"Shared mapping: {next(iter(mappings))}")
    print(f"Maximum depth: {max_depth}")
    print(f"Maximum CZ count: {max_cz}")
    print(
        f"Maximum calibrated errors: CZ={maximum_cz_error:.6f}, "
        f"readout={maximum_readout_error:.6f}"
    )
    print("Human review approved: false")
    print("backend.run called: false")
    print("Hardware submitted: false")


if __name__ == "__main__":
    main()
