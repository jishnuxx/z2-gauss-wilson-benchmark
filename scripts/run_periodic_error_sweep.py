#!/usr/bin/env python3
"""Run and persist the 24-error periodic-model audit."""

import argparse
from pathlib import Path

import numpy as np

import _bootstrap  # noqa: F401
from z2lgt.periodic_error_sweep import (
    CLASS_ORDER,
    diagnostic_class_counts,
    single_qubit_pauli_error_sweep,
    write_periodic_error_sweep_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tmax", type=float, default=2.0)
    parser.add_argument("--steps", type=int, default=17)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "results/processed/periodic_single_qubit_error_sweep.csv"
        ),
    )
    args = parser.parse_args()
    if args.tmax <= 0:
        raise SystemExit("--tmax must be positive")
    if args.steps < 2:
        raise SystemExit("--steps must be at least 2")

    rows = single_qubit_pauli_error_sweep(
        np.linspace(0.0, args.tmax, args.steps)
    )
    output = write_periodic_error_sweep_csv(rows, args.output)
    counts = diagnostic_class_counts(rows)

    print("Periodic single-qubit Pauli error sweep")
    print(f"  errors audited: {len(rows)}")
    print("  diagnostic classes:")
    for name in CLASS_ORDER:
        print(f"    {name}: {counts[name]}")
    print("  worst observable corruption in each class:")
    for name in CLASS_ORDER:
        members = [row for row in rows if row["diagnostic_class"] == name]
        if not members:
            continue
        worst = max(members, key=lambda row: row["max_abs_imbalance_error"])
        print(
            f"    {name}: {worst['pauli']}_{worst['subsystem'][0]}"
            f"{worst['local_index']} -> "
            f"max |Delta O_LR|={worst['max_abs_imbalance_error']:.6f} "
            f"at t={worst['time_of_max_error']:.6f}"
        )
    print(f"  output: {output}")


if __name__ == "__main__":
    main()
