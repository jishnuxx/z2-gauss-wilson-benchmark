#!/usr/bin/env python3
"""Compile and freeze the three-circuit blind-spot batch for an IQM target."""

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

from z2lgt.blindspot_circuits import CASES, joint_diagnostic_circuit
from z2lgt.iqm_candidate import candidate_id, sha256_file


def provider_class():
    try:
        from iqm.qiskit_iqm import IQMProvider
    except ImportError as exc:
        raise RuntimeError('install the IQM adapter with: pip install "iqm-client[qiskit]"') from exc
    return IQMProvider


def instruction_properties(properties) -> dict[str, float | None]:
    return {
        "duration_seconds": None if properties is None else properties.duration,
        "error": None if properties is None else properties.error,
    }


def physical_cz_pairs(compiled, mapping: list[int]) -> list[tuple[int, int]]:
    local_pairs = {
        tuple(compiled.find_bit(qubit).index for qubit in instruction.qubits)
        for instruction in compiled.data
        if instruction.operation.name == "cz"
    }
    pairs: list[tuple[int, int]] = []
    for pair in sorted(local_pairs):
        if max(pair) >= len(mapping):
            raise RuntimeError(f"cannot translate packed CZ pair {pair} through mapping {mapping}")
        pairs.append(tuple(mapping[index] for index in pair))
    return pairs


def resolve_cz_key(target, pair: tuple[int, int]) -> tuple[int, int]:
    for key in target["cz"]:
        if set(key) == set(pair):
            return key
    raise RuntimeError(f"mapped CZ pair is absent from target: {pair}")


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(_bootstrap.ROOT))
    except ValueError:
        return str(path.resolve())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("IQM_SERVER_URL"))
    parser.add_argument(
        "--quantum-computer", default=os.environ.get("IQM_QUANTUM_COMPUTER", "emerald")
    )
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--optimization-level", type=int, default=3, choices=range(4))
    parser.add_argument("--seed-transpiler", type=int, default=7)
    parser.add_argument(
        "--outdir", type=Path, default=Path("results/iqm/emerald_blindspot_candidate")
    )
    parser.add_argument("--force", action="store_true", help="replace an unsubmitted candidate")
    args = parser.parse_args()
    if not args.url:
        raise SystemExit("IQM server URL missing; set IQM_SERVER_URL")
    if not os.environ.get("IQM_TOKEN"):
        raise SystemExit("IQM_TOKEN is missing; load it from the system keychain")
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
    sources = [joint_diagnostic_circuit(case) for case in CASES]
    compiled = transpile(
        sources,
        backend=backend,
        optimization_level=args.optimization_level,
        seed_transpiler=args.seed_transpiler,
    )
    request = backend.create_run_request(compiled, shots=args.shots)

    circuit_dir = outdir / "circuits"
    circuit_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for case, source, circuit in zip(CASES, sources, compiled, strict=True):
        mapping = [circuit.layout.initial_layout[source.qubits[index]] for index in range(4)]
        cz_pairs = [resolve_cz_key(backend.target, pair) for pair in physical_cz_pairs(circuit, mapping)]
        qpy_path = circuit_dir / f"{case}.qpy"
        qasm_path = circuit_dir / f"{case}.qasm"
        with qpy_path.open("wb") as handle:
            qpy_dump(circuit, handle)
        qasm_path.write_text(qasm2.dumps(circuit), encoding="utf-8")
        records.append(
            {
                "case": case,
                "logical_to_physical": mapping,
                "depth": int(circuit.depth()),
                "two_qubit_gate_count": int(circuit.num_nonlocal_gates()),
                "operations": {str(name): int(count) for name, count in circuit.count_ops().items()},
                "cz_pairs": [
                    {"physical_qubits": list(pair), **instruction_properties(backend.target["cz"][pair])}
                    for pair in sorted(set(cz_pairs))
                ],
                "measurements": [
                    {
                        "physical_qubit": qubit,
                        **instruction_properties(backend.target["measure"][(qubit,)]),
                    }
                    for qubit in sorted(mapping)
                ],
                "qpy": relative(qpy_path),
                "qpy_sha256": sha256_file(qpy_path),
                "qasm": relative(qasm_path),
                "qasm_sha256": sha256_file(qasm_path),
            }
        )

    calibration_set_id = str(backend.architecture.calibration_set_id)
    identity = {
        "batch": "blindspot-minimal",
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
        "all_tests_passed": True,
        "test_output": (tests.stdout + tests.stderr).strip(),
        "request_validated": True,
        "circuits_frozen": True,
        "human_review_approved": False,
        "submission_started": False,
        "hardware_submitted": False,
        "circuits": records,
        "review_note": (
            "Review target, calibration, mappings, gate/readout errors, hashes, shots, and credit "
            "budget. Approval must be recorded with scripts/approve_iqm_candidate.py."
        ),
    }
    outdir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Frozen candidate: {manifest_path}")
    print(f"Candidate ID: {manifest['candidate_id']}")
    print(f"Calibration set: {calibration_set_id}")
    for record in records:
        print(
            f"  {record['case']}: mapping={record['logical_to_physical']} "
            f"depth={record['depth']} two_qubit={record['two_qubit_gate_count']}"
        )
    print("Human review approved: false")
    print("Hardware submitted: false")


if __name__ == "__main__":
    main()
