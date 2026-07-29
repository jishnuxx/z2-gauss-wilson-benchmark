#!/usr/bin/env python3
"""Run exact periodic-sector dynamics and persist the comparison table."""

import argparse
from pathlib import Path

import numpy as np

import _bootstrap  # noqa: F401
from z2lgt.periodic_dynamics import exact_trajectories, write_periodic_dynamics_csv
from z2lgt.periodic_model import PeriodicZ2Model


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exact correct- versus wrong-Wilson-sector dynamics"
    )
    parser.add_argument("--tmax", type=float, default=2.0)
    parser.add_argument("--steps", type=int, default=17)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/processed/periodic_dynamics_ideal.csv"),
    )
    args = parser.parse_args()
    if args.tmax <= 0:
        raise SystemExit("--tmax must be positive")
    if args.steps < 2:
        raise SystemExit("--steps must be at least 2")

    model = PeriodicZ2Model()
    rows = exact_trajectories(np.linspace(0.0, args.tmax, args.steps), model)
    output = write_periodic_dynamics_csv(rows, args.output)
    largest = max(rows, key=lambda row: row["absolute_difference"])

    print("Exact periodic Z2 dynamics")
    print(f"  data qubits: {model.n_qubits}")
    print("  electric-link term: omitted (coefficient fixed to zero)")
    print("  observable: O_LR = (n0+n1-n2-n3)/2")
    print(f"  time points: {len(rows)} over [0, {args.tmax:g}]")
    print(
        "  maximum sector-induced difference: "
        f"{largest['absolute_difference']:.6f} at t={largest['time']:.6f}"
    )
    print(
        "  final sectors: "
        f"W_ideal={rows[-1]['ideal_wilson']:.6f}, "
        f"W_wrong={rows[-1]['wrong_sector_wilson']:.6f}"
    )
    print(
        "  minimum Gauss expectation: "
        f"ideal={min(row['ideal_min_gauss'] for row in rows):.6f}, "
        f"wrong={min(row['wrong_sector_min_gauss'] for row in rows):.6f}"
    )
    print(f"  output: {output}")


if __name__ == "__main__":
    main()
