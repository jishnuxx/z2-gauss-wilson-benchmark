#!/usr/bin/env python3
"""Validate periodic Qiskit Trotter statevectors against exact dynamics."""

import argparse
from pathlib import Path

import numpy as np

import _bootstrap  # noqa: F401
from z2lgt.circuits import compiled_circuit, export_circuit, resource_metrics
from z2lgt.periodic_circuits import (
    periodic_circuit_validation,
    periodic_trotter_circuit,
    write_periodic_circuit_validation_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tmax", type=float, default=2.0)
    parser.add_argument("--dt", type=float, default=0.1)
    parser.add_argument("--output-step", type=float, default=0.2)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/processed/periodic_trotter_validation.csv"),
    )
    args = parser.parse_args()
    if args.tmax <= 0 or args.dt <= 0 or args.output_step <= 0:
        raise SystemExit("tmax, dt, and output-step must be positive")
    n_outputs = int(round(args.tmax / args.output_step))
    if not np.isclose(n_outputs * args.output_step, args.tmax):
        raise SystemExit("tmax must be an integer multiple of output-step")
    if not np.isclose(round(args.output_step / args.dt) * args.dt, args.output_step):
        raise SystemExit("output-step must be an integer multiple of dt")

    times = np.linspace(0.0, args.tmax, n_outputs + 1)
    rows = periodic_circuit_validation(times, dt=args.dt)
    output = write_periodic_circuit_validation_csv(rows, args.output)
    largest = periodic_trotter_circuit(args.tmax, args.dt)
    compiled = compiled_circuit(largest)
    exports = export_circuit(
        compiled,
        Path("circuits/periodic/qasm/periodic_tmax"),
        qpy_stem=Path("circuits/periodic/qiskit/periodic_tmax"),
    )
    resources = resource_metrics(largest)

    print("Periodic Qiskit circuit validation")
    print("  simulator: ideal Qiskit Statevector")
    print(f"  Trotter dt: {args.dt:.6f}")
    print(f"  validation times: {len(rows)} over [0, {args.tmax:g}]")
    print(f"  minimum state fidelity: {min(row['state_fidelity'] for row in rows):.9f}")
    print(
        "  maximum |Delta O_LR|: "
        f"{max(row['absolute_imbalance_error'] for row in rows):.9f}"
    )
    print(
        "  minimum Gauss expectation: "
        f"{min(row['trotter_min_gauss'] for row in rows):.9f}"
    )
    print(
        "  Wilson expectation range: "
        f"[{min(row['trotter_wilson'] for row in rows):.9f}, "
        f"{max(row['trotter_wilson'] for row in rows):.9f}]"
    )
    print(f"  compiled tmax resources: {resources}")
    print(f"  output: {output}")
    print(f"  circuits: {exports}")


if __name__ == "__main__":
    main()
