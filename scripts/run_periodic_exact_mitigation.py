#!/usr/bin/env python3
"""Run the exact single-fault mitigation comparison."""

import argparse
from pathlib import Path

import numpy as np

import _bootstrap  # noqa: F401
from z2lgt.periodic_mitigation import (
    exact_single_fault_mitigation,
    write_periodic_mitigation_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tmax", type=float, default=2.0)
    parser.add_argument("--steps", type=int, default=17)
    parser.add_argument("--total-error-probability", type=float, default=0.2)
    parser.add_argument("--injection-times", type=int, default=8)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/processed/periodic_exact_mitigation.csv"),
    )
    args = parser.parse_args()
    if args.tmax <= 0 or args.steps < 2:
        raise SystemExit("require tmax > 0 and steps >= 2")

    rows = exact_single_fault_mitigation(
        np.linspace(0.0, args.tmax, args.steps),
        total_error_probability=args.total_error_probability,
        n_injection_times=args.injection_times,
    )
    output = write_periodic_mitigation_csv(rows, args.output)
    metrics = (
        ("raw", "raw_abs_error"),
        ("Gauss only", "gauss_only_abs_error"),
        ("Gauss + Wilson", "gauss_plus_wilson_abs_error"),
    )

    print("Exact periodic single-fault mitigation")
    print("  model: at most one uniformly distributed Pauli fault")
    print(
        "  total fault probability by final time: "
        f"{args.total_error_probability:.6f}"
    )
    print(f"  injection opportunities: {args.injection_times}")
    print("  mean absolute trajectory errors:")
    for label, key in metrics:
        print(f"    {label}: {np.mean([row[key] for row in rows]):.6f}")
    print("  final acceptance:")
    print(f"    raw: {rows[-1]['raw_acceptance']:.6f}")
    print(f"    Gauss only: {rows[-1]['gauss_only_acceptance']:.6f}")
    print(
        "    Gauss + Wilson: "
        f"{rows[-1]['gauss_plus_wilson_acceptance']:.6f}"
    )
    print(
        "  residual Gauss+Wilson error at final time: "
        f"{rows[-1]['gauss_plus_wilson_abs_error']:.6f}"
    )
    print(f"  output: {output}")


if __name__ == "__main__":
    main()
