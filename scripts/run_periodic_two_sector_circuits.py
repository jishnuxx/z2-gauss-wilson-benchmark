#!/usr/bin/env python3
"""Validate and export the two-sector periodic benchmark circuits."""

import argparse
import csv
from pathlib import Path

import _bootstrap  # noqa: F401
from z2lgt.circuits import compiled_circuit, export_circuit
from z2lgt.periodic_circuits import (
    periodic_trotter_circuit,
    periodic_two_sector_circuit_comparison,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--time", type=float, default=0.8)
    parser.add_argument("--dt", type=float, default=0.4)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "results/processed/periodic_two_sector_circuit_comparison.csv"
        ),
    )
    args = parser.parse_args()
    rows = periodic_two_sector_circuit_comparison(args.time, args.dt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    exports = {}
    for sector, label in ((1, "Wplus"), (-1, "Wminus")):
        circuit = compiled_circuit(
            periodic_trotter_circuit(
                args.time,
                args.dt,
                wilson_sector=sector,
            )
        )
        stem = f"periodic_{label}_t{args.time:g}_dt{args.dt:g}".replace(".", "p")
        exports[label] = export_circuit(
            circuit,
            Path("circuits/periodic/qasm") / stem,
            qpy_stem=Path("circuits/periodic/qiskit") / stem,
        )

    exact_separation = abs(rows[0]["exact_imbalance"] - rows[1]["exact_imbalance"])
    trotter_separation = abs(
        rows[0]["trotter_imbalance"] - rows[1]["trotter_imbalance"]
    )
    print("Periodic two-sector circuit comparison")
    print(f"  candidate: t={args.time:.6f}, dt={args.dt:.6f}")
    for row in rows:
        print(
            f"  {row['case']}: exact O_LR={row['exact_imbalance']:.6f}, "
            f"Trotter O_LR={row['trotter_imbalance']:.6f}, "
            f"fidelity={row['state_fidelity']:.6f}, "
            f"W={row['trotter_wilson']:.6f}"
        )
    print(f"  exact sector separation: {exact_separation:.6f}")
    print(f"  Trotter sector separation: {trotter_separation:.6f}")
    print(
        "  separation retained: "
        f"{trotter_separation / exact_separation:.6f}"
    )
    print(
        "  compiled resources: "
        f"depth={max(row['depth'] for row in rows)}, "
        f"two_qubit={max(row['two_qubit_gate_count'] for row in rows)}"
    )
    print(f"  output: {args.output}")
    print(f"  circuits: {exports}")


if __name__ == "__main__":
    main()
