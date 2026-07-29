#!/usr/bin/env python3
"""Compile and freeze the reviewed periodic two-sector IQM candidate.

This script performs tests, transpilation, calibration-metric checks, artifact
export, hashing, and client-side request validation.  It never calls
``backend.run`` and therefore cannot submit a hardware job.
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

from z2lgt.iqm_candidate import candidate_id, sha256_file
from z2lgt.periodic_iqm_audit import (
    algorithmic_candidate_metrics,
    apply_algorithmic_gate,
    physical_operation_qubits,
)
from z2lgt.periodic_readout import periodic_joint_readout_circuit


SECTORS: tuple[tuple[str, int], ...] = (("Wplus", 1), ("Wminus", -1))


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


def resolve_symmetric_key(target, operation: str, pair: tuple[int, int]):
    for key in target[operation]:
        if set(key) == set(pair):
            return key
    raise RuntimeError(f"mapped {operation} pair is absent from target: {pair}")


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
    parser.add_argument("--time", type=float, default=0.8)
    parser.add_argument("--dt", type=float, default=0.4)
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--optimization-level", type=int, default=3, choices=range(4))
    parser.add_argument("--seed-transpiler", type=int, default=7)
    parser.add_argument("--max-native-cz", type=int, default=100)
    parser.add_argument("--max-native-depth", type=int, default=140)
    parser.add_argument("--max-cz-error", type=float, default=0.015)
    parser.add_argument("--max-readout-error", type=float, default=0.025)
    parser.add_argument("--min-fidelity", type=float, default=0.85)
    parser.add_argument("--min-separation-retained", type=float, default=0.60)
    parser.add_argument("--min-trotter-separation", type=float, default=0.10)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/iqm/emerald_periodic_candidate"),
    )
    parser.add_argument(
        "--force", action="store_true", help="replace an unsubmitted candidate"
    )
    args = parser.parse_args()

    if not args.url:
        raise SystemExit("IQM server URL missing; set IQM_SERVER_URL")
    if not os.environ.get("IQM_TOKEN"):
        raise SystemExit(
            "IQM_TOKEN is missing; source scripts/activate_iqm_emerald.zsh"
        )
    if args.shots <= 0:
        raise SystemExit("shots must be positive")

    outdir = args.outdir.resolve()
    manifest_path = outdir / "readiness_manifest.json"
    if manifest_path.exists() and not args.force:
        raise SystemExit(
            f"candidate already exists: {manifest_path}; inspect it or pass --force"
        )
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        if old.get("hardware_submitted") is True:
            raise SystemExit(
                "refusing to overwrite a candidate already marked as submitted"
            )

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

    physics = algorithmic_candidate_metrics(args.time, args.dt)
    apply_algorithmic_gate(
        physics,
        min_fidelity=args.min_fidelity,
        min_separation_retained=args.min_separation_retained,
        min_trotter_separation=args.min_trotter_separation,
    )
    if physics["algorithmic_gate_passed"] is not True:
        raise SystemExit("algorithmic gate failed; candidate was not frozen")

    provider = provider_class()(args.url, quantum_computer=args.quantum_computer)
    backend = provider.get_backend(use_metrics=True)
    sources = [
        periodic_joint_readout_circuit(
            args.time,
            args.dt,
            wilson_sector=sign,
        )
        for _, sign in SECTORS
    ]
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
    for (sector, sign), source, circuit in zip(
        SECTORS, sources, compiled, strict=True
    ):
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
        qpy_path = circuit_dir / f"periodic_{sector}.qpy"
        qasm_path = circuit_dir / f"periodic_{sector}.qasm"
        with qpy_path.open("wb") as handle:
            qpy_dump(circuit, handle)
        qasm_path.write_text(qasm2.dumps(circuit), encoding="utf-8")
        cz_metrics = [
            {
                "physical_qubits": list(pair),
                **instruction_properties(backend.target["cz"][pair]),
            }
            for pair in cz_keys
        ]
        measurement_metrics = [
            {
                "physical_qubit": qubit,
                **instruction_properties(backend.target["measure"][(qubit,)]),
            }
            for qubit in measured
        ]
        records.append(
            {
                "case": sector,
                "wilson_sector": sign,
                "logical_to_physical": mapping,
                "depth": int(circuit.depth()),
                "cz_count": int(circuit.count_ops().get("cz", 0)),
                "two_qubit_gate_count": int(circuit.num_nonlocal_gates()),
                "operations": {
                    str(name): int(count)
                    for name, count in circuit.count_ops().items()
                },
                "cz_pairs": cz_metrics,
                "measurements": measurement_metrics,
                "qpy": relative(qpy_path),
                "qpy_sha256": sha256_file(qpy_path),
                "qasm": relative(qasm_path),
                "qasm_sha256": sha256_file(qasm_path),
            }
        )

    mappings = {tuple(record["logical_to_physical"]) for record in records}
    max_cz_count = max(int(record["cz_count"]) for record in records)
    max_depth = max(int(record["depth"]) for record in records)
    cz_errors = finite_errors(
        [item for record in records for item in record["cz_pairs"]]
    )
    readout_errors = finite_errors(
        [item for record in records for item in record["measurements"]]
    )
    maximum_cz_error = max(cz_errors) if cz_errors else None
    maximum_readout_error = max(readout_errors) if readout_errors else None
    hardware_checks = {
        "same_mapping_for_both_sectors": len(mappings) == 1,
        "maximum_native_cz_count": max_cz_count <= args.max_native_cz,
        "maximum_native_depth": max_depth <= args.max_native_depth,
        "maximum_cz_error": (
            maximum_cz_error is not None
            and maximum_cz_error <= args.max_cz_error
        ),
        "maximum_readout_error": (
            maximum_readout_error is not None
            and maximum_readout_error <= args.max_readout_error
        ),
    }
    if not all(hardware_checks.values()):
        failed = [name for name, passed in hardware_checks.items() if not passed]
        raise SystemExit(
            "hardware freeze gate failed: "
            + ", ".join(failed)
            + "; rerun the live candidate audit"
        )

    calibration_set_id = str(backend.architecture.calibration_set_id)
    batch = f"periodic-two-sector-t{args.time:g}-dt{args.dt:g}"
    identity = {
        "batch": batch,
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
        "time": args.time,
        "dt": args.dt,
        "trotter_steps": int(round(args.time / args.dt)),
        "wilson_sectors": {sector: sign for sector, sign in SECTORS},
        "backend_name": str(backend.name),
        "backend_qubit_count": int(backend.num_qubits),
        "native_operations": list(backend.operation_names),
        "use_metrics": True,
        "request_type": type(request).__name__,
        "physics_metrics": physics,
        "hardware_thresholds": {
            "maximum_native_cz_count": args.max_native_cz,
            "maximum_native_depth": args.max_native_depth,
            "maximum_cz_error": args.max_cz_error,
            "maximum_readout_error": args.max_readout_error,
        },
        "hardware_checks": hardware_checks,
        "maximum_native_cz_count": max_cz_count,
        "maximum_native_depth": max_depth,
        "maximum_cz_error": maximum_cz_error,
        "maximum_readout_error": maximum_readout_error,
        "all_tests_passed": True,
        "test_output": (tests.stdout + tests.stderr).strip(),
        "request_validated": True,
        "circuits_frozen": True,
        "human_review_approved": False,
        "hardware_execution_started": False,
        "hardware_submitted": False,
        "hardware_credits_consumed": False,
        "backend_run_called": False,
        "circuits": records,
        "review_note": (
            "Review calibration, mappings, errors, hashes, shots, and credit budget. "
            "Approval records review only; this repository currently provides no "
            "periodic hardware execution entrypoint."
        ),
    }
    outdir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"Frozen periodic candidate: {manifest_path}")
    print(f"Candidate ID: {manifest['candidate_id']}")
    print(f"Calibration set: {calibration_set_id}")
    print(
        f"Physics: t={args.time:g} dt={args.dt:g} "
        f"Trotter separation={float(physics['trotter_sector_separation']):.6f} "
        f"min fidelity={float(physics['minimum_state_fidelity']):.6f}"
    )
    for record in records:
        print(
            f"  {record['case']}: mapping={record['logical_to_physical']} "
            f"depth={record['depth']} CZ={record['cz_count']}"
        )
    print(
        f"Maximum calibrated errors: CZ={maximum_cz_error:.6f} "
        f"readout={maximum_readout_error:.6f}"
    )
    print("Human review approved: false")
    print("backend.run called: false")
    print("Hardware submitted: false")


if __name__ == "__main__":
    main()
