#!/usr/bin/env python3
r"""Freeze the six-circuit Emerald periodic-matter benchmark candidate.

The physics points and shot count match the Sirius scan exactly.  A single
mapping is selected from the current Emerald calibration at the central
``t=0.8, dt=0.4`` point and then locked across all six circuits.

This script runs tests, transpiles, validates a run request, audits current
calibration data, and writes immutable QPY artifacts plus a readiness
manifest.  It never calls ``backend.run`` and consumes no hardware credits.
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
from z2lgt.iqm_freeze_audit import (
    calibrated_loci,
    component_name,
    has_four_bit_matter_readout,
    maximum_error,
    measurement_classical_bits,
    parse_fixed_layout,
)
from z2lgt.periodic_iqm_audit import algorithmic_candidate_metrics
from z2lgt.periodic_readout import periodic_matter_readout_circuit


POINTS: tuple[tuple[float, float], ...] = (
    (0.6, 0.3),
    (0.8, 0.4),
    (1.0, 0.5),
)
SECTORS: tuple[tuple[str, int], ...] = (("Wplus", 1), ("Wminus", -1))


def provider_class():
    try:
        from iqm.qiskit_iqm import IQMProvider
    except ImportError as exc:
        raise RuntimeError(
            'install the IQM adapter with: pip install "iqm-client[qiskit]"'
        ) from exc
    return IQMProvider


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(_bootstrap.ROOT))
    except ValueError:
        return str(path.resolve())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("IQM_SERVER_URL"))
    parser.add_argument("--quantum-computer", default="emerald")
    parser.add_argument("--shots", type=int, default=5000)
    parser.add_argument("--optimization-level", type=int, default=3, choices=range(4))
    parser.add_argument("--seed-transpiler", type=int, default=7)
    parser.add_argument("--max-native-depth", type=int, default=140)
    parser.add_argument("--max-native-cz", type=int, default=90)
    parser.add_argument("--max-r-error", type=float, default=0.003)
    parser.add_argument("--max-cz-error", type=float, default=0.015)
    parser.add_argument("--max-readout-error", type=float, default=0.025)
    parser.add_argument(
        "--fixed-layout",
        help="optional comma-separated logical-to-physical layout to lock",
    )
    parser.add_argument(
        "--replicate-label",
        help="optional label that creates a distinct matched-repeat candidate",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/iqm/emerald_periodic_matter_scan_candidate_5000"),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an unsubmitted candidate",
    )
    args = parser.parse_args()

    if not args.url:
        raise SystemExit("IQM server URL missing; set IQM_SERVER_URL")
    if not os.environ.get("IQM_TOKEN"):
        raise SystemExit("IQM_TOKEN is missing; load a valid raw token first")
    if args.quantum_computer != "emerald":
        raise SystemExit(
            "this target-specific freezer only accepts --quantum-computer emerald"
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
        raise SystemExit("test gate failed; Emerald candidate was not frozen")

    physics_by_point = []
    for time, dt in POINTS:
        physics = algorithmic_candidate_metrics(time, dt)
        physics_by_point.append(physics)
        if int(physics["trotter_steps"]) != 2:
            raise SystemExit("scan definition error: every point must use two Trotter steps")
        if float(physics["trotter_sector_separation"]) <= 0:
            raise SystemExit("scan definition error: every point must have positive separation")

    backend = provider_class()(
        args.url,
        quantum_computer=args.quantum_computer,
    ).get_backend(use_metrics=True)

    if args.fixed_layout is None:
        # Select one calibration-aware placement at the central point, then
        # lock it for every time and sector in the comparison.
        probe_source = periodic_matter_readout_circuit(
            time=0.8,
            dt=0.4,
            wilson_sector=1,
        )
        probe = transpile(
            probe_source,
            backend=backend,
            optimization_level=args.optimization_level,
            seed_transpiler=args.seed_transpiler,
        )
        fixed_layout = tuple(
            int(probe.layout.initial_layout[probe_source.qubits[index]])
            for index in range(probe_source.num_qubits)
        )
        mapping_selection = (
            "calibration-aware Emerald transpilation at t=0.8, dt=0.4, "
            "Wplus; then fixed for all six circuits"
        )
    else:
        try:
            fixed_layout = parse_fixed_layout(args.fixed_layout)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        if max(fixed_layout) >= int(backend.num_qubits):
            raise SystemExit("fixed layout contains an index outside the Emerald backend")
        mapping_selection = (
            "explicit physical layout reused from the reviewed primary "
            "Emerald scan for matched replication"
        )

    sources = []
    labels = []
    for time, dt in POINTS:
        for case, sector in SECTORS:
            labels.append((time, dt, case, sector))
            sources.append(
                periodic_matter_readout_circuit(
                    time=time,
                    dt=dt,
                    wilson_sector=sector,
                )
            )

    compiled = [
        transpile(
            source,
            backend=backend,
            initial_layout=list(fixed_layout),
            optimization_level=args.optimization_level,
            seed_transpiler=args.seed_transpiler,
        )
        for source in sources
    ]
    request = backend.create_run_request(compiled, shots=args.shots)

    circuit_dir = outdir / "circuits"
    circuit_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for label, source, circuit in zip(labels, sources, compiled, strict=True):
        time, dt, case, sector = label
        mapping = [
            int(circuit.layout.initial_layout[source.qubits[index]])
            for index in range(source.num_qubits)
        ]
        operations = {
            str(name): int(count) for name, count in circuit.count_ops().items()
        }
        r_loci = calibrated_loci(
            backend, circuit, mapping, "r", backend.target
        )
        cz_loci = calibrated_loci(
            backend, circuit, mapping, "cz", backend.target
        )
        measurement_loci = calibrated_loci(
            backend, circuit, mapping, "measure", backend.target
        )

        stem = f"periodic_matter_{case}_t{time:g}_dt{dt:g}".replace(".", "p")
        qpy_path = circuit_dir / f"{stem}.qpy"
        source_qasm_path = circuit_dir / f"{stem}_source.qasm"
        with qpy_path.open("wb") as handle:
            qpy_dump(circuit, handle)
        source_qasm_path.write_text(qasm2.dumps(source), encoding="utf-8")

        records.append(
            {
                "case": case,
                "wilson_sector": sector,
                "time": time,
                "dt": dt,
                "trotter_steps": int(round(time / dt)),
                "logical_to_physical_indices": mapping,
                "logical_to_physical_components": [
                    component_name(backend, index) for index in mapping
                ],
                "matter_components": [
                    component_name(backend, index) for index in mapping[:4]
                ],
                "link_components": [
                    component_name(backend, index) for index in mapping[4:]
                ],
                "depth": int(circuit.depth()),
                "r_count": int(operations.get("r", 0)),
                "cz_count": int(operations.get("cz", 0)),
                "move_count": int(operations.get("move", 0)),
                "measurement_count": int(operations.get("measure", 0)),
                "measurement_classical_bits": measurement_classical_bits(circuit),
                "operations": operations,
                "r_loci": r_loci,
                "cz_loci": cz_loci,
                "move_loci": [],
                "measurement_loci": measurement_loci,
                "qpy": relative(qpy_path),
                "qpy_sha256": sha256_file(qpy_path),
                "source_qasm": relative(source_qasm_path),
                "source_qasm_sha256": sha256_file(source_qasm_path),
            }
        )

    mappings = {tuple(record["logical_to_physical_indices"]) for record in records}
    measured_matter_only = all(has_four_bit_matter_readout(circuit) for circuit in compiled)
    maximum_depth = max(int(record["depth"]) for record in records)
    maximum_cz_count = max(int(record["cz_count"]) for record in records)
    maximum_move_count = max(int(record["move_count"]) for record in records)
    maximum_r_error = maximum_error(records, "r_loci")
    maximum_cz_error = maximum_error(records, "cz_loci")
    maximum_readout_error = maximum_error(records, "measurement_loci")

    hardware_checks = {
        "six_circuit_scan": len(records) == 6,
        "same_fixed_mapping_for_all_circuits": mappings == {fixed_layout},
        "two_trotter_steps_for_every_point": all(
            int(record["trotter_steps"]) == 2 for record in records
        ),
        "matter_only_measurements": measured_matter_only,
        "no_move_operations": maximum_move_count == 0,
        "maximum_native_depth": maximum_depth <= args.max_native_depth,
        "maximum_native_cz_count": maximum_cz_count <= args.max_native_cz,
        "maximum_r_error": (
            maximum_r_error is not None and maximum_r_error <= args.max_r_error
        ),
        "maximum_cz_error": (
            maximum_cz_error is not None and maximum_cz_error <= args.max_cz_error
        ),
        "maximum_readout_error": (
            maximum_readout_error is not None
            and maximum_readout_error <= args.max_readout_error
        ),
    }
    if not all(hardware_checks.values()):
        failed = [name for name, passed in hardware_checks.items() if not passed]
        raise SystemExit("Emerald freeze gate failed: " + ", ".join(failed))

    calibration_set_id = str(backend.architecture.calibration_set_id)
    base_batch = "periodic-matter-emerald-two-step-scan-t0.6-0.8-1.0"
    batch = (
        base_batch
        if args.replicate_label is None
        else f"{base_batch}-{args.replicate_label}"
    )
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
        "benchmark_type": "two_step_fixed_product_formula_scan",
        "replicate_label": args.replicate_label or "primary",
        "replicate_protocol": (
            "same logical points, shots, transpiler settings, and physical "
            "mapping; calibration fetched at freeze time"
        ),
        "points": [
            {"time": time, "dt": dt, "trotter_steps": 2}
            for time, dt in POINTS
        ],
        "readout_mode": "matter_only",
        "wilson_sectors": {case: sector for case, sector in SECTORS},
        "mapping_selection": mapping_selection,
        "fixed_initial_layout_indices": list(fixed_layout),
        "fixed_initial_layout_components": [
            component_name(backend, index) for index in fixed_layout
        ],
        "backend_name": str(backend.name),
        "backend_qubit_count": int(backend.num_qubits),
        "native_operations": list(backend.operation_names),
        "use_metrics": True,
        "request_type": type(request).__name__,
        "physics_metrics_by_point": physics_by_point,
        "physics_interpretation": (
            "Each hardware target is the corresponding two-step Trotter result, "
            "not the exact continuous-time value. Exact-state fidelity is "
            "reported descriptively and is not used as a freeze gate."
        ),
        "hardware_thresholds": {
            "maximum_native_depth": args.max_native_depth,
            "maximum_native_cz_count": args.max_native_cz,
            "maximum_r_error": args.max_r_error,
            "maximum_cz_error": args.max_cz_error,
            "maximum_readout_error": args.max_readout_error,
            "threshold_role": "operational acceptance gates, not physics claims",
        },
        "hardware_checks": hardware_checks,
        "maximum_native_depth": maximum_depth,
        "maximum_native_cz_count": maximum_cz_count,
        "maximum_native_move_count": maximum_move_count,
        "maximum_r_error": maximum_r_error,
        "maximum_cz_error": maximum_cz_error,
        "maximum_move_error": None,
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
            "Six reduced Emerald matter-readout circuits matching the Sirius "
            "two-step scan. They do not directly measure Wilson or Gauss operators."
        ),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"Frozen Emerald periodic-matter scan: {manifest_path}")
    print(f"Candidate ID: {manifest['candidate_id']}")
    print(f"Calibration set: {calibration_set_id}")
    print(
        "Fixed mapping:",
        list(zip(range(len(fixed_layout)), manifest["fixed_initial_layout_components"])),
    )
    for record in records:
        print(
            f"  t={record['time']:g} dt={record['dt']:g} {record['case']}: "
            f"depth={record['depth']} R={record['r_count']} "
            f"CZ={record['cz_count']} MOVE={record['move_count']}"
        )
    print(
        "Maximum calibrated errors: "
        f"R={maximum_r_error:.6f} CZ={maximum_cz_error:.6f} "
        f"readout={maximum_readout_error:.6f}"
    )
    print("Human review approved: false")
    print("backend.run called: false")
    print("Hardware submitted: false")
    print("Hardware credits consumed: false")


if __name__ == "__main__":
    main()
